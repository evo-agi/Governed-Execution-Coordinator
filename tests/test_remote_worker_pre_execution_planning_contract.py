from __future__ import annotations

import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import sqlite3
import tokenize
from typing import NamedTuple
import unicodedata

import pytest


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = ROOT / ".docs" / "c2b-durable-development-state.md"

SECTION_HEADING = (
    "## 41. Coordinator Cognitive Proposal And Pre-Execution Selection Contract Freeze"
)
BEGIN_MARKER = "<!-- COORDINATOR_COGNITIVE_PROPOSAL_SELECTION_CONTRACT_BEGIN -->"
END_MARKER = "<!-- COORDINATOR_COGNITIVE_PROPOSAL_SELECTION_CONTRACT_END -->"
REPAIRED_BEGIN_MARKER = "<!-- COORDINATOR_SECTION41_REPAIRED_SEMANTIC_OWNER_BEGIN -->"
REPAIRED_END_MARKER = "<!-- COORDINATOR_SECTION41_REPAIRED_SEMANTIC_OWNER_END -->"
REAUDIT_REPAIR_BEGIN_MARKER = (
    "<!-- COORDINATOR_SECTION41_REAUDIT_REPAIR_CLOSURE_BEGIN -->"
)
REAUDIT_REPAIR_END_MARKER = (
    "<!-- COORDINATOR_SECTION41_REAUDIT_REPAIR_CLOSURE_END -->"
)
A2_REVISED_REPAIR_BEGIN_MARKER = (
    "<!-- COORDINATOR_SECTION41_A2_REVISED_REPAIR_CLOSURE_BEGIN -->"
)
A2_REVISED_REPAIR_END_MARKER = (
    "<!-- COORDINATOR_SECTION41_A2_REVISED_REPAIR_CLOSURE_END -->"
)
C2B3D_SECTION_HEADING = "## 39. Coordinator C2B3C Author-Effect Contract Freeze"
C2B3D_BEGIN_MARKER = "<!-- COORDINATOR_C2B3C_AUTHOR_EFFECT_CONTRACT_BEGIN -->"
C2B3D_END_MARKER = "<!-- COORDINATOR_C2B3C_AUTHOR_EFFECT_CONTRACT_END -->"
OPENING = (
    SECTION_HEADING
    + "\n\n"
    + BEGIN_MARKER
    + "\n\n"
    + "This uncommitted contract candidate is pending fresh independent audit. "
    + "It freezes only future\n"
    + "proposal admission and Coordinator selection or non-selection. C2B3D "
    + "remains the unchanged\n"
    + "current implementation. Migration 0003, production source, model "
    + "invocation, dispatch, worker\n"
    + "contact, post-execution review, semantic decision, Git, publication, and "
    + "every external effect\n"
    + "remain absent and unauthorized. The structured literal below is the byte-retained opening audit\n"
    + "snapshot. It is non-authoritative after the repaired semantic owner following the existing end marker.\n\n"
    + "```python\n"
)
CLOSING = (
    "\n```\n\n"
    + "The selection `selected_for_dispatch_gates` is durable planning state only. "
    + "A later dispatch\n"
    + "contract must re-read the exact selected disposition and CAS head revision, "
    + "then obtain fresh\n"
    + "externally authored authority verification and qualified-remote-host "
    + "readiness before any private\n"
    + "retrieval, transport, process, worker, validation, review, or Git activity.\n\n"
    + END_MARKER
    + "\n"
)

# Sections 1-40 are the exact HEAD bytes before the single blank line that
# introduces Section 41. These values are intentionally independent of Git.
EXPECTED_SECTIONS_1_40_UTF8_LENGTH = 1_332_141
EXPECTED_SECTIONS_1_40_SHA256 = (
    "ae12ce9c6a8c47f31eb16a3f2dceb1eb997e9facfe68b8d1caf619132ddd761e"
)

PHASES = ("pre_execution_plan", "post_execution_semantic_review")
PRE_EXECUTION_RECOMMENDATIONS = (
    "select_for_dispatch_gates",
    "defer",
    "block",
    "replan",
    "terminal_reject",
)
POST_EXECUTION_RECOMMENDATIONS = (
    "accept_candidate",
    "repair_candidate",
    "replan",
    "terminal_reject",
    "block",
)
DISPOSITIONS = ("selected_for_dispatch_gates", "deferred", "blocked")
AUTHORITY_STATES = ("pending", "verified", "blocked", "stale", "revoked", "expired")
C2A_EFFECT_CLASSES = (
    "author_candidate",
    "cancel_effect",
    "local_git_commit",
    "review_candidate",
    "validate_candidate",
)
AUTHORITY_SUBJECT_KINDS = ("effect_intent",)

PRE_EXECUTION_EVIDENCE_ROLES = (
    ("standing_policy", 5, True),
    ("risk_lane", 6, True),
    ("repository_binding", 7, True),
    ("base_binding", 8, True),
    ("authorized_path_scope", 9, True),
    ("cost_ceiling", 10, True),
    ("token_ceiling", 11, True),
    ("time_ceiling", 12, True),
    ("delivery_ceiling", 13, True),
    ("effect_ceiling", 14, True),
    ("authority_currentness_attestation", 15, True),
    ("global_stop", 16, True),
    ("validation_requirement", 17, True),
    ("review_requirement", 18, True),
    ("qualified_remote_host_readiness", 19, False),
)
POST_EXECUTION_EVIDENCE_ROLES = (
    ("candidate_capsule", 5, True),
    ("worker_result", 6, True),
    ("validation_result", 7, True),
    ("independent_review", 8, True),
    ("standing_policy", 9, True),
    ("risk_lane", 10, True),
    ("authority_currentness_attestation", 11, True),
    ("global_stop", 12, True),
    ("effect_ceiling", 13, True),
    ("qualified_remote_host_readiness", 14, False),
)

SCHEMA_IDS = {
    "safe_model_configuration": "governed-execution.nwp-model-configuration-safe.v1",
    "source_invocation": "governed-execution.nwp-model-source-invocation.v1",
    "pre_execution_context": "governed-execution.nwp-pre-execution-planning-context.v1",
    "post_execution_context": "governed-execution.nwp-post-execution-semantic-review-context.v1",
    "pre_execution_artifact": "governed-execution.nwp-pre-execution-plan-artifact.v1",
    "post_execution_artifact": "governed-execution.nwp-post-execution-semantic-review-artifact.v1",
    "artifact_binding": "governed-execution.nwp-private-proposal-artifact-binding.v1",
    "proposal": "governed-execution.nwp-model-proposal-envelope.v1",
    "pre_execution_projection": "governed-execution.nwp-pre-execution-plan-safe-projection.v1",
    "post_execution_projection": "governed-execution.nwp-post-execution-semantic-review-safe-projection.v1",
    "evidence_binding": "governed-execution.nwp-model-proposal-evidence-binding.v1",
    "disposition": "governed-execution.nwp-pre-execution-coordinator-disposition.v1",
    "selection_head": "governed-execution.nwp-pre-execution-selection-head.v1",
    "safe_command": "governed-execution.nwp-record-pre-execution-plan-disposition-command.v1",
    "result": "governed-execution.nwp-pre-execution-plan-disposition-result.v1",
    "receipt": "governed-execution.nwp-cognitive-mutation-receipt.v1",
    "authority_attestation": "governed-execution.nwp-authority-currentness-attestation-safe.v1",
}

DIGEST_DOMAINS = {
    "safe_model_configuration": SCHEMA_IDS["safe_model_configuration"] + ".identity",
    "source_invocation": SCHEMA_IDS["source_invocation"] + ".identity",
    "pre_execution_context": SCHEMA_IDS["pre_execution_context"] + ".identity",
    "pre_execution_artifact": SCHEMA_IDS["pre_execution_artifact"] + ".identity",
    "artifact_binding": SCHEMA_IDS["artifact_binding"] + ".identity",
    "proposal": SCHEMA_IDS["proposal"] + ".identity",
    "pre_execution_projection": SCHEMA_IDS["pre_execution_projection"] + ".identity",
    "evidence_binding": SCHEMA_IDS["evidence_binding"] + ".identity",
    "evidence_set": "governed-execution.nwp-model-proposal-evidence-set.v1.identity",
    "disposition": SCHEMA_IDS["disposition"] + ".identity",
    "selection_head": SCHEMA_IDS["selection_head"] + ".identity",
    "selection_preimage": "governed-execution.nwp-pre-execution-selection-preimage.v1.identity",
    "safe_command": SCHEMA_IDS["safe_command"] + ".identity",
    "result": SCHEMA_IDS["result"] + ".identity",
    "mutation_graph": "governed-execution.nwp-cognitive-mutation-graph.v1.identity",
    "receipt": SCHEMA_IDS["receipt"] + ".identity",
    "affected_path_set": "governed-execution.nwp-pre-execution-affected-path-set.v1.identity",
    "expected_output_set": "governed-execution.nwp-pre-execution-expected-output-set.v1.identity",
    "validation_strategy": "governed-execution.nwp-pre-execution-validation-strategy.v1.identity",
    "assumption_set": "governed-execution.nwp-pre-execution-assumption-set.v1.identity",
    "risk_set": "governed-execution.nwp-pre-execution-risk-set.v1.identity",
    "prerequisite_set": "governed-execution.nwp-pre-execution-prerequisite-set.v1.identity",
    "stop_condition_set": "governed-execution.nwp-pre-execution-stop-condition-set.v1.identity",
    "resource_effect_use": "governed-execution.nwp-pre-execution-resource-effect-use.v1.identity",
    "authority_attestation": SCHEMA_IDS["authority_attestation"] + ".identity",
}

AUTHORITY_ATTESTATION_FIELD_ORDER = (
    "schema_id",
    "authority_attestation_ref",
    "authoritative_subject_kind",
    "authoritative_subject_ref",
    "authority_evaluation_ref",
    "authority_evaluation_digest",
    "authority_state",
    "authority_version",
    "issued_at",
    "expires_at",
    "source_authority_ref",
    "authority_attestation_digest",
)

# Independently encoded from the committed Section-39/C2B3D family. The direct
# cross-contract test also parses Section 39 itself and proves this copy has not
# drifted. Section 41 never imports another test module or production code.
C2B3D_BASIS = {
    "committed_at": "2026-08-22T12:34:56Z",
    "program_ref": "program-c2b3a-1",
    "program_version_ref": "program-version-c2b3a-1",
    "program_version_number": 1,
    "accepted_intent_revision_ref": "accepted-intent-c2b3a-1",
    "work_item_ref": "work-item-c2b3a-1",
    "work_item_revision_ref": "work-item-revision-c2b3a-1",
    "basis_decision_ref": "decision-c2b3a-1",
    "basis_decision_digest": "e743c359aea93d7931250552b62bc741d84c490f9ebb68e071c8616cc5fb4b96",
    "semantic_attempt_ref": "semantic-attempt-c2b3a-1",
    "semantic_attempt_digest": "7018934d8724dcbc8cd3f93f603fca1682bf3d4b762293c4191e28e001cdd263",
    "attempt_number": 1,
    "candidate_ref": "candidate-c2b3a-1",
    "repository_ref": "repository-c2b3a-1",
    "base_git_object_format": "sha1",
    "base_git_oid": "2222222222222222222222222222222222222222",
    "authorized_paths": (
        ".docs/system_overview/hybrid_integration_architecture_adr.md",
        "PLANS.md",
        "docs_contract_test.go",
    ),
    "work_spec_ref": "work-spec-c2b3a-1",
    "work_spec_digest": "2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c",
    "work_spec_safe_projection_digest": "1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab",
    "validation_requirement_ref": "validation-c2b3a-1",
    "validation_requirement_digest": "6666666666666666666666666666666666666666666666666666666666666666",
    "validation_safe_evidence_digest": "bfd4be05ab68440c4402fdaa770fdbdbbec72f73962be77b8ef9d342ece9a5ea",
    "review_requirement_ref": "review-c2b3a-1",
    "review_requirement_digest": "7777777777777777777777777777777777777777777777777777777777777777",
    "review_safe_evidence_digest": "3a6ffa9bdb8b5e71d0deeb0d90e8d087aeb66ae92849690cae779efbdd6eb9f7",
    "standing_grant_ref": "standing-grant-c2b3c-1",
    "standing_grant_digest": "3333333333333333333333333333333333333333333333333333333333333333",
    "attempt_authorization_ref": "attempt-authorization-c2b3c-1",
    "attempt_authorization_digest": "4444444444444444444444444444444444444444444444444444444444444444",
    "effect_authorization_ref": "effect-authorization-c2b3c-1",
    "effect_authorization_digest": "5555555555555555555555555555555555555555555555555555555555555555",
    "attempt_fence_ref": "attempt-fence-c2b3c-1",
    "attempt_fence_digest": "6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed",
    "attempt_fence_allowed_effect_classes": C2A_EFFECT_CLASSES,
    "attempt_fence_expires_at": "2026-08-22T13:34:56Z",
    "effect_intent_ref": "effect-intent-c2b3c-1",
    "effect_intent_digest": "2597aeafff2e78212f12423f933f23c6e0a4107d80fc33cbf6d103f225bf938d",
    "effect_class": "author_candidate",
    "effect_fence_ref": "effect-fence-c2b3c-1",
    "effect_fence_digest": "8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd",
    "effect_fence_allowed_effect_classes": ("author_candidate",),
    "effect_fence_expires_at": "2026-08-22T13:34:56Z",
    "author_command_ref": "command-c2b3c-1",
    "author_command_digest": "545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484",
    "authority_evaluation_ref": "authority-evaluation-c2b3c-1",
    "authority_evaluation_digest": "e484b72ed81cffbd5dfe80be4263c9c0bc66739a9a45d96d6dffcf748208164d",
    "authority_evaluation_state": "pending",
    "coding_global_stop_ref": "coding-global-stop-c2b3a-1",
    "coding_global_stop_version": 0,
    "delivery_attempt_ref": "delivery-attempt-c2b3c-1",
    "delivery_envelope_digest": "e60ea42c5cc195a5a55aebb7b9c00d760b7337e5232be82729df67b7e317f35a",
    "delivery_attempt_digest": "715b1baa3a9a6e0142f46433a0222a47ea42773b62b6c2e9a0dde2ab070f134e",
    "effect_head_revision": 0,
    "effect_head_digest": "b302769593fd214cec86ada39e685cb97e46880e78973738c33e858e39a4e964",
    "delivery_head_revision": 0,
    "delivery_head_digest": "cc09294e960a7812807f2037c5066c6af263659f3409c2f4dcf75429e473bddf",
    "attempt_aggregate_ceilings": {
        "max_active_invocations": 1,
        "max_candidate_bytes": 1_048_576,
        "max_changed_files": 3,
        "max_cost_microusd": 100_000,
        "max_cpu_seconds": 600,
        "max_deliveries": 3,
        "max_deployments": 0,
        "max_local_commits": 1,
        "max_memory_bytes": 2_147_483_648,
        "max_merges": 0,
        "max_model_input_tokens": 200_000,
        "max_model_output_tokens": 50_000,
        "max_pull_requests": 0,
        "max_pushes": 0,
        "max_wall_seconds": 1_800,
    },
    "effect_ceilings": {
        "max_active_invocations": 1,
        "max_candidate_bytes": 1_048_576,
        "max_changed_files": 3,
        "max_cost_microusd": 100_000,
        "max_cpu_seconds": 600,
        "max_deliveries": 1,
        "max_deployments": 0,
        "max_local_commits": 0,
        "max_memory_bytes": 2_147_483_648,
        "max_merges": 0,
        "max_model_input_tokens": 200_000,
        "max_model_output_tokens": 50_000,
        "max_pull_requests": 0,
        "max_pushes": 0,
        "max_wall_seconds": 1_800,
    },
}


def _columns(*pairs: tuple[str, str]) -> tuple[tuple[str, str], ...]:
    return pairs


TABLE_CONTRACTS = {
    "development_model_source_invocations": {
        "columns": _columns(
            ("schema_id", f"literal:{SCHEMA_IDS['source_invocation']}"),
            ("source_invocation_ref", "safe_ref"),
            ("proposal_phase", "proposal_phase"),
            ("model_contract_ref", "safe_ref"),
            ("model_contract_digest", "sha256"),
            ("model_configuration_ref", "safe_ref"),
            ("model_configuration_digest", "sha256"),
            ("context_schema_id", "phase_context_schema"),
            ("context_ref", "safe_ref"),
            ("context_digest", "sha256"),
            ("artifact_schema_id", "phase_artifact_schema"),
            ("artifact_ref", "safe_ref"),
            ("artifact_digest", "sha256"),
            ("invocation_status", "literal:normalized_typed_proposal_supplied"),
            ("source_invocation_started_at", "utc_second"),
            ("source_invocation_completed_at", "utc_second"),
            ("source_invocation_digest", "sha256"),
        ),
        "primary_key": ("source_invocation_ref",),
        "unique": (("proposal_phase", "source_invocation_ref"),),
        "foreign_keys": (),
        "relational_checks": ("phase_context_and_artifact_schema_algebra",),
        "mutable": False,
        "author": "model_adapter_safe_reducer",
        "writer": "Coordinator_cognitive_mutation_family_only",
    },
    "development_pre_execution_planning_contexts": {
        "columns": _columns(
            ("schema_id", f"literal:{SCHEMA_IDS['pre_execution_context']}"),
            ("planning_context_ref", "safe_ref"),
            ("program_ref", "safe_ref"),
            ("program_version_ref", "safe_ref"),
            ("program_version_number", "positive_int"),
            ("accepted_intent_revision_ref", "safe_ref"),
            ("work_item_ref", "safe_ref"),
            ("work_item_revision_ref", "safe_ref"),
            ("semantic_attempt_ref", "safe_ref"),
            ("semantic_attempt_digest", "sha256"),
            ("attempt_number", "positive_int"),
            ("candidate_ref", "safe_ref"),
            ("basis_decision_ref", "safe_ref"),
            ("basis_decision_digest", "sha256"),
            ("work_spec_ref", "safe_ref"),
            ("work_spec_digest", "sha256"),
            ("work_spec_safe_projection_digest", "sha256"),
            ("effect_intent_ref", "safe_ref"),
            ("effect_intent_digest", "sha256"),
            ("author_command_ref", "safe_ref"),
            ("author_command_digest", "sha256"),
            ("standing_grant_ref", "safe_ref"),
            ("standing_grant_digest", "sha256"),
            ("attempt_authorization_ref", "safe_ref"),
            ("attempt_authorization_digest", "sha256"),
            ("effect_authorization_ref", "safe_ref"),
            ("effect_authorization_digest", "sha256"),
            ("attempt_fence_ref", "safe_ref"),
            ("attempt_fence_digest", "sha256"),
            ("attempt_fence_allowed_effect_classes_json", "canonical_effect_class_json"),
            ("attempt_fence_expires_at", "utc_second"),
            ("effect_fence_ref", "safe_ref"),
            ("effect_fence_digest", "sha256"),
            ("effect_fence_allowed_effect_classes_json", "canonical_effect_class_json"),
            ("effect_fence_expires_at", "utc_second"),
            ("delivery_attempt_ref", "safe_ref"),
            ("delivery_envelope_digest", "sha256"),
            ("delivery_attempt_digest", "sha256"),
            ("expected_program_head_revision", "nonnegative_int"),
            ("expected_work_item_head_revision", "nonnegative_int"),
            ("expected_effect_head_fence_ref", "safe_ref"),
            ("expected_effect_head_revision", "nonnegative_int"),
            ("expected_effect_head_digest", "sha256"),
            ("expected_delivery_head_attempt_ref", "safe_ref"),
            ("expected_delivery_head_revision", "nonnegative_int"),
            ("expected_delivery_head_digest", "sha256"),
            ("global_stop_ref", "safe_ref"),
            ("global_stop_version", "nonnegative_int"),
            ("global_stop_state", "enum:clear|active"),
            ("authority_evaluation_ref", "safe_ref"),
            ("authority_evaluation_digest", "sha256"),
            ("authority_attestation_schema_id", f"literal:{SCHEMA_IDS['authority_attestation']}"),
            ("authority_attestation_ref", "safe_ref"),
            ("authoritative_subject_kind", "literal:effect_intent"),
            ("authoritative_subject_ref", "safe_ref"),
            ("authority_state", "authority_state"),
            ("authority_version", "positive_int"),
            ("authority_issued_at", "utc_second"),
            ("authority_expires_at", "utc_second"),
            ("authority_source_ref", "safe_ref"),
            ("authority_attestation_digest", "sha256"),
            ("standing_policy_ref", "safe_ref"),
            ("standing_policy_digest", "sha256"),
            ("risk_lane_ref", "safe_ref"),
            ("risk_lane_digest", "sha256"),
            ("repository_ref", "safe_ref"),
            ("base_git_object_format", "literal:sha1"),
            ("base_git_oid", "sha1"),
            ("authorized_path_scope_digest", "sha256"),
            ("cost_ceiling_ref", "safe_ref"),
            ("cost_ceiling_digest", "sha256"),
            ("token_ceiling_ref", "safe_ref"),
            ("token_ceiling_digest", "sha256"),
            ("time_ceiling_ref", "safe_ref"),
            ("time_ceiling_digest", "sha256"),
            ("delivery_ceiling_ref", "safe_ref"),
            ("delivery_ceiling_digest", "sha256"),
            ("effect_ceiling_ref", "safe_ref"),
            ("effect_ceiling_digest", "sha256"),
            ("validation_requirement_ref", "safe_ref"),
            ("validation_requirement_digest", "sha256"),
            ("validation_safe_evidence_digest", "sha256"),
            ("review_requirement_ref", "safe_ref"),
            ("review_requirement_digest", "sha256"),
            ("review_safe_evidence_digest", "sha256"),
            ("qualified_remote_host_readiness_ref", "nullable_safe_ref"),
            ("qualified_remote_host_readiness_digest", "nullable_sha256"),
            ("planning_context_captured_at", "utc_second"),
            ("planning_context_digest", "sha256"),
        ),
        "primary_key": ("planning_context_ref",),
        "unique": (("program_ref", "planning_context_ref"),),
        "foreign_keys": (
            (("program_ref", "program_version_ref"), "development_program_versions", ("program_ref", "program_version_ref"), "IMMEDIATE"),
            (("program_ref", "accepted_intent_revision_ref"), "development_accepted_intent_revisions", ("program_ref", "accepted_intent_revision_ref"), "IMMEDIATE"),
            (("program_ref", "work_item_ref", "work_item_revision_ref"), "development_work_item_revisions", ("program_ref", "work_item_ref", "work_item_revision_ref"), "IMMEDIATE"),
            (("program_ref", "semantic_attempt_ref"), "development_semantic_attempts", ("program_ref", "semantic_attempt_ref"), "IMMEDIATE"),
            (("program_ref", "basis_decision_ref"), "development_decisions", ("program_ref", "decision_ref"), "IMMEDIATE"),
            (("program_ref", "effect_intent_ref"), "development_effect_intents", ("program_ref", "effect_intent_ref"), "IMMEDIATE"),
            (("program_ref", "author_command_ref"), "development_author_commands", ("program_ref", "command_ref"), "IMMEDIATE"),
            (("program_ref", "attempt_fence_ref"), "development_attempt_fences", ("program_ref", "attempt_fence_ref"), "IMMEDIATE"),
            (("program_ref", "effect_fence_ref"), "development_effect_fences", ("program_ref", "effect_fence_ref"), "IMMEDIATE"),
            (("program_ref", "delivery_attempt_ref"), "development_delivery_attempts", ("program_ref", "delivery_attempt_ref"), "IMMEDIATE"),
            (("program_ref", "authority_evaluation_ref"), "development_authority_evaluations", ("program_ref", "authority_evaluation_ref"), "IMMEDIATE"),
        ),
        "relational_checks": (
            "exact_C2B3D_program_attempt_candidate_effect_command_fence_delivery_lineage",
            "exact_current_program_work_effect_delivery_heads",
            "exact_global_stop_and_authority_evaluation",
            "closed_policy_risk_repository_base_path_cost_token_time_delivery_effect_evidence",
        ),
        "mutable": False,
        "author": "Coordinator_preselection_context_capture",
        "writer": "Coordinator_cognitive_mutation_family_only",
    },
    "development_private_proposal_artifact_bindings": {
        "columns": _columns(
            ("schema_id", f"literal:{SCHEMA_IDS['artifact_binding']}"),
            ("artifact_ref", "safe_ref"),
            ("proposal_phase", "proposal_phase"),
            ("artifact_schema_id", "phase_artifact_schema"),
            ("artifact_digest", "sha256"),
            ("artifact_canonical_byte_length", "int:1..65536"),
            ("safe_projection_schema_id", "phase_projection_schema"),
            ("safe_projection_digest", "sha256"),
            ("privacy_classification", "literal:private_normalized_model_proposal"),
            ("artifact_validated_at", "utc_second"),
            ("artifact_binding_digest", "sha256"),
        ),
        "primary_key": ("artifact_ref",),
        "unique": (("proposal_phase", "artifact_ref"),),
        "foreign_keys": (),
        "relational_checks": ("phase_artifact_and_projection_schema_algebra",),
        "mutable": False,
        "author": "Coordinator_private_artifact_validator",
        "writer": "Coordinator_cognitive_mutation_family_only",
    },
    "development_model_proposals": {
        "columns": _columns(
            ("schema_id", f"literal:{SCHEMA_IDS['proposal']}"),
            ("proposal_ref", "safe_ref"),
            ("proposal_phase", "proposal_phase"),
            ("source_invocation_ref", "safe_ref"),
            ("source_invocation_digest", "sha256"),
            ("model_contract_ref", "safe_ref"),
            ("model_contract_digest", "sha256"),
            ("model_configuration_ref", "safe_ref"),
            ("model_configuration_digest", "sha256"),
            ("context_schema_id", "phase_context_schema"),
            ("context_ref", "safe_ref"),
            ("context_digest", "sha256"),
            ("artifact_schema_id", "phase_artifact_schema"),
            ("artifact_ref", "safe_ref"),
            ("artifact_digest", "sha256"),
            ("safe_projection_schema_id", "phase_projection_schema"),
            ("safe_projection_digest", "sha256"),
            ("recommendation", "phase_recommendation"),
            ("reason_code", "reason_code"),
            ("evidence_set_ref", "safe_ref"),
            ("evidence_set_digest", "sha256"),
            ("proposal_created_at", "utc_second"),
            ("proposal_digest", "sha256"),
        ),
        "primary_key": ("proposal_ref",),
        "unique": (("source_invocation_ref",), ("artifact_ref",)),
        "foreign_keys": (
            (("source_invocation_ref",), "development_model_source_invocations", ("source_invocation_ref",), "IMMEDIATE"),
            (("artifact_ref",), "development_private_proposal_artifact_bindings", ("artifact_ref",), "IMMEDIATE"),
        ),
        "relational_checks": (
            "phase_schema_and_recommendation_algebra",
            "exact_source_invocation_and_artifact_binding_equality",
        ),
        "mutable": False,
        "author": "configured_model_normalized_typed_output",
        "writer": "Coordinator_cognitive_mutation_family_only",
    },
    "development_pre_execution_plan_projections": {
        "columns": _columns(
            ("schema_id", f"literal:{SCHEMA_IDS['pre_execution_projection']}"),
            ("proposal_ref", "safe_ref"),
            ("artifact_ref", "safe_ref"),
            ("planning_context_ref", "safe_ref"),
            ("strategy_item_count", "int:1..8"),
            ("work_unit_count", "int:1..32"),
            ("affected_path_count", "int:1..64"),
            ("affected_path_set_digest", "sha256"),
            ("expected_output_count", "int:1..32"),
            ("expected_output_set_digest", "sha256"),
            ("validation_step_count", "int:1..32"),
            ("validation_strategy_digest", "sha256"),
            ("assumption_count", "int:1..16"),
            ("assumption_set_digest", "sha256"),
            ("risk_count", "int:1..16"),
            ("risk_set_digest", "sha256"),
            ("prerequisite_count", "int:1..32"),
            ("prerequisite_set_digest", "sha256"),
            ("stop_condition_count", "int:1..16"),
            ("stop_condition_set_digest", "sha256"),
            ("proposed_resource_effect_use_digest", "sha256"),
            ("recommendation", "pre_execution_recommendation"),
            ("reason_code", "reason_code"),
            ("safe_projection_digest", "sha256"),
        ),
        "primary_key": ("proposal_ref",),
        "unique": (("artifact_ref",),),
        "foreign_keys": (
            (("proposal_ref",), "development_model_proposals", ("proposal_ref",), "IMMEDIATE"),
            (("artifact_ref",), "development_private_proposal_artifact_bindings", ("artifact_ref",), "IMMEDIATE"),
            (("planning_context_ref",), "development_pre_execution_planning_contexts", ("planning_context_ref",), "IMMEDIATE"),
        ),
        "relational_checks": (
            "proposal_is_pre_execution_and_all_refs_digests_recommendation_reason_equal",
            "all_substantive_counts_are_nonzero_and_bounded",
        ),
        "mutable": False,
        "author": "Coordinator_private_artifact_validator",
        "writer": "Coordinator_cognitive_mutation_family_only",
    },
    "development_model_proposal_evidence_bindings": {
        "columns": _columns(
            ("schema_id", f"literal:{SCHEMA_IDS['evidence_binding']}"),
            ("proposal_ref", "safe_ref"),
            ("proposal_phase", "proposal_phase"),
            ("evidence_set_ref", "safe_ref"),
            ("evidence_role", "phase_evidence_role"),
            ("role_rank", "phase_evidence_rank"),
            ("ordinal", "literal_int:0"),
            ("evidence_ref", "safe_ref"),
            ("evidence_digest", "sha256"),
            ("required_for_selection", "bool_int"),
            ("evidence_bound_at", "utc_second"),
            ("evidence_binding_digest", "sha256"),
        ),
        "primary_key": ("proposal_ref", "evidence_role", "ordinal"),
        "unique": (("proposal_ref", "role_rank", "ordinal"),),
        "foreign_keys": (
            (("proposal_ref",), "development_model_proposals", ("proposal_ref",), "IMMEDIATE"),
        ),
        "relational_checks": (
            "closed_phase_role_rank_required_algebra",
            "all_required_phase_roles_exactly_once",
            "qualified_remote_host_readiness_zero_or_one_and_never_required_for_selection",
        ),
        "mutable": False,
        "author": "evidence_owner_safe_bindings",
        "writer": "Coordinator_cognitive_mutation_family_only",
    },
    "development_pre_execution_dispositions": {
        "columns": _columns(
            ("schema_id", f"literal:{SCHEMA_IDS['disposition']}"),
            ("disposition_ref", "safe_ref"),
            ("program_ref", "safe_ref"),
            ("program_version_ref", "safe_ref"),
            ("accepted_intent_revision_ref", "safe_ref"),
            ("work_item_ref", "safe_ref"),
            ("work_item_revision_ref", "safe_ref"),
            ("proposal_ref", "safe_ref"),
            ("proposal_digest", "sha256"),
            ("planning_context_ref", "safe_ref"),
            ("planning_context_digest", "sha256"),
            ("evidence_set_ref", "safe_ref"),
            ("evidence_set_digest", "sha256"),
            ("semantic_attempt_ref", "safe_ref"),
            ("candidate_ref", "safe_ref"),
            ("effect_intent_ref", "safe_ref"),
            ("author_command_ref", "safe_ref"),
            ("author_command_digest", "sha256"),
            ("attempt_fence_ref", "safe_ref"),
            ("attempt_fence_digest", "sha256"),
            ("effect_fence_ref", "safe_ref"),
            ("effect_fence_digest", "sha256"),
            ("delivery_attempt_ref", "safe_ref"),
            ("delivery_envelope_digest", "sha256"),
            ("disposition", "pre_execution_disposition"),
            ("reason_code", "reason_code"),
            ("supersedes_disposition_ref", "nullable_safe_ref"),
            ("expected_selection_head_revision", "nullable_nonnegative_int"),
            ("expected_selection_head_digest", "nullable_sha256"),
            ("resulting_selection_head_revision", "nonnegative_int"),
            ("selection_head_postimage_digest", "sha256"),
            ("coordinator_disposition_decided_at", "utc_second"),
            ("disposition_digest", "sha256"),
        ),
        "primary_key": ("disposition_ref",),
        "unique": (("program_ref", "disposition_ref"), ("proposal_ref",)),
        "foreign_keys": (
            (("proposal_ref",), "development_model_proposals", ("proposal_ref",), "IMMEDIATE"),
            (("planning_context_ref",), "development_pre_execution_planning_contexts", ("planning_context_ref",), "IMMEDIATE"),
            (("program_ref", "program_version_ref"), "development_program_versions", ("program_ref", "program_version_ref"), "IMMEDIATE"),
            (("program_ref", "accepted_intent_revision_ref"), "development_accepted_intent_revisions", ("program_ref", "accepted_intent_revision_ref"), "IMMEDIATE"),
            (("program_ref", "work_item_ref", "work_item_revision_ref"), "development_work_item_revisions", ("program_ref", "work_item_ref", "work_item_revision_ref"), "IMMEDIATE"),
            (("program_ref", "semantic_attempt_ref"), "development_semantic_attempts", ("program_ref", "semantic_attempt_ref"), "IMMEDIATE"),
            (("program_ref", "effect_intent_ref"), "development_effect_intents", ("program_ref", "effect_intent_ref"), "IMMEDIATE"),
            (("program_ref", "author_command_ref"), "development_author_commands", ("program_ref", "command_ref"), "IMMEDIATE"),
            (("program_ref", "attempt_fence_ref"), "development_attempt_fences", ("program_ref", "attempt_fence_ref"), "IMMEDIATE"),
            (("program_ref", "effect_fence_ref"), "development_effect_fences", ("program_ref", "effect_fence_ref"), "IMMEDIATE"),
            (("program_ref", "delivery_attempt_ref"), "development_delivery_attempts", ("program_ref", "delivery_attempt_ref"), "IMMEDIATE"),
            (("program_ref", "supersedes_disposition_ref"), "development_pre_execution_dispositions", ("program_ref", "disposition_ref"), "IMMEDIATE"),
        ),
        "relational_checks": (
            "initial_head_requires_null_preimage_null_supersedes_and_result_revision_zero",
            "supersession_requires_exact_preimage_supersedes_and_result_revision_plus_one",
            "selected_requires_current_clear_stop_and_authority_pending_or_verified",
            "deferred_or_blocked_changes_no_other_progression_fact",
        ),
        "mutable": False,
        "author": "Coordinator",
        "writer": "Coordinator_cognitive_mutation_family_only",
    },
    "development_pre_execution_selection_heads": {
        "columns": _columns(
            ("schema_id", f"literal:{SCHEMA_IDS['selection_head']}"),
            ("program_ref", "safe_ref"),
            ("program_version_ref", "safe_ref"),
            ("accepted_intent_revision_ref", "safe_ref"),
            ("work_item_ref", "safe_ref"),
            ("work_item_revision_ref", "safe_ref"),
            ("semantic_attempt_ref", "safe_ref"),
            ("candidate_ref", "safe_ref"),
            ("effect_intent_ref", "safe_ref"),
            ("author_command_ref", "safe_ref"),
            ("author_command_digest", "sha256"),
            ("attempt_fence_ref", "safe_ref"),
            ("attempt_fence_digest", "sha256"),
            ("effect_fence_ref", "safe_ref"),
            ("effect_fence_digest", "sha256"),
            ("delivery_attempt_ref", "safe_ref"),
            ("delivery_envelope_digest", "sha256"),
            ("current_proposal_ref", "safe_ref"),
            ("current_disposition_ref", "safe_ref"),
            ("current_disposition", "pre_execution_disposition"),
            ("head_revision", "nonnegative_int"),
            ("updated_at", "utc_second"),
            ("head_digest", "sha256"),
        ),
        "primary_key": (
            "program_ref", "semantic_attempt_ref", "candidate_ref", "effect_intent_ref",
            "author_command_ref", "attempt_fence_ref", "effect_fence_ref", "delivery_attempt_ref",
        ),
        "unique": (("effect_intent_ref",), ("program_ref", "effect_intent_ref")),
        "foreign_keys": (
            (("program_ref", "program_version_ref"), "development_program_versions", ("program_ref", "program_version_ref"), "IMMEDIATE"),
            (("program_ref", "accepted_intent_revision_ref"), "development_accepted_intent_revisions", ("program_ref", "accepted_intent_revision_ref"), "IMMEDIATE"),
            (("program_ref", "work_item_ref", "work_item_revision_ref"), "development_work_item_revisions", ("program_ref", "work_item_ref", "work_item_revision_ref"), "IMMEDIATE"),
            (("program_ref", "semantic_attempt_ref"), "development_semantic_attempts", ("program_ref", "semantic_attempt_ref"), "IMMEDIATE"),
            (("program_ref", "effect_intent_ref"), "development_effect_intents", ("program_ref", "effect_intent_ref"), "IMMEDIATE"),
            (("program_ref", "author_command_ref"), "development_author_commands", ("program_ref", "command_ref"), "IMMEDIATE"),
            (("program_ref", "attempt_fence_ref"), "development_attempt_fences", ("program_ref", "attempt_fence_ref"), "IMMEDIATE"),
            (("program_ref", "effect_fence_ref"), "development_effect_fences", ("program_ref", "effect_fence_ref"), "IMMEDIATE"),
            (("program_ref", "delivery_attempt_ref"), "development_delivery_attempts", ("program_ref", "delivery_attempt_ref"), "IMMEDIATE"),
            (("current_proposal_ref",), "development_model_proposals", ("proposal_ref",), "IMMEDIATE"),
            (("program_ref", "current_disposition_ref"), "development_pre_execution_dispositions", ("program_ref", "disposition_ref"), "IMMEDIATE"),
        ),
        "relational_checks": (
            "current_proposal_disposition_and_lineage_exactly_equal",
            "only_current_fields_revision_timestamp_and_digest_may_change",
            "CAS_update_matches_complete_key_prior_revision_and_prior_disposition",
        ),
        "mutable": True,
        "author": "Coordinator",
        "writer": "Coordinator_cognitive_mutation_family_only",
    },
    "development_cognitive_mutation_receipts": {
        "columns": _columns(
            ("schema_id", f"literal:{SCHEMA_IDS['receipt']}"),
            ("mutation_ref", "safe_ref"),
            ("mutation_family", "literal:record_pre_execution_plan_disposition"),
            ("command_schema_id", f"literal:{SCHEMA_IDS['safe_command']}"),
            ("command_digest", "sha256"),
            ("program_ref", "safe_ref"),
            ("proposal_ref", "safe_ref"),
            ("disposition_ref", "safe_ref"),
            ("effect_intent_ref", "safe_ref"),
            ("selection_head_revision", "nonnegative_int"),
            ("selection_head_digest", "sha256"),
            ("result_class", "literal:pre_execution_plan_disposition_recorded"),
            ("result_projection_digest", "sha256"),
            ("mutation_graph_digest", "sha256"),
            ("outcome", "literal:committed"),
            ("committed_at", "utc_second"),
            ("receipt_digest", "sha256"),
        ),
        "primary_key": ("mutation_ref",),
        "unique": (("program_ref", "mutation_ref"), ("disposition_ref",)),
        "foreign_keys": (
            (("proposal_ref",), "development_model_proposals", ("proposal_ref",), "IMMEDIATE"),
            (("program_ref", "disposition_ref"), "development_pre_execution_dispositions", ("program_ref", "disposition_ref"), "IMMEDIATE"),
            (("program_ref", "effect_intent_ref"), "development_pre_execution_selection_heads", ("program_ref", "effect_intent_ref"), "IMMEDIATE"),
        ),
        "relational_checks": (
            "closed_pre_execution_family_result_algebra",
            "exact_result_graph_and_selection_postimage_binding",
        ),
        "mutable": False,
        "author": "Coordinator",
        "writer": "Coordinator_cognitive_mutation_family_only",
    },
}

IMMUTABLE_TABLES = tuple(
    name for name, value in TABLE_CONTRACTS.items() if value["mutable"] is False
)
TRIGGERS = tuple(
    trigger
    for table in IMMUTABLE_TABLES
    for trigger in (f"{table}_no_update", f"{table}_no_delete")
) + (
    "development_pre_execution_selection_heads_no_delete",
    "development_pre_execution_selection_heads_lineage_immutable",
)

PRIVATE_PLAN_FIELD_ORDER = (
    "schema_id",
    "artifact_ref",
    "proposal_ref",
    "proposal_phase",
    "planning_context_ref",
    "implementation_strategy",
    "proposed_work_units",
    "affected_authorized_paths",
    "expected_outputs",
    "validation_strategy",
    "material_assumptions",
    "risks_and_uncertainties",
    "required_evidence_and_prerequisites",
    "stop_or_replan_conditions",
    "proposed_resource_and_effect_use",
    "recommendation",
    "reason_code",
    "artifact_digest",
)

NARRATIVE_BYTE_LIMITS = {
    "implementation_strategy_item": 768,
    "work_unit_summary": 512,
    "output_description": 512,
    "validation_target": 512,
    "validation_success_criterion": 512,
    "assumption_statement": 512,
    "risk_description": 512,
    "risk_mitigation": 512,
    "prerequisite_requirement": 512,
    "stop_condition_statement": 512,
}

SAFE_COMMAND_FIELD_ORDER = (
    "schema_id",
    "mutation_ref",
    "proposal_ref",
    "proposal_digest",
    "source_invocation_ref",
    "source_invocation_digest",
    "artifact_ref",
    "artifact_digest",
    "artifact_binding_digest",
    "planning_context_ref",
    "planning_context_digest",
    "safe_projection_digest",
    "evidence_set_ref",
    "evidence_set_digest",
    "preassigned_disposition_ref",
    "expected_current_selection_revision",
    "expected_current_selection_head_digest",
    "disposition",
    "disposition_reason_code",
    "supersedes_disposition_ref",
    "program_ref",
    "semantic_attempt_ref",
    "candidate_ref",
    "effect_intent_ref",
    "author_command_ref",
    "author_command_digest",
    "attempt_fence_ref",
    "attempt_fence_digest",
    "effect_fence_ref",
    "effect_fence_digest",
    "delivery_attempt_ref",
    "delivery_envelope_digest",
    "mutation_command_digest",
)

GRAPH_ROLES = (
    ("source_invocation", 0, 0),
    ("planning_context", 1, 0),
    ("private_artifact_binding", 2, 0),
    ("model_proposal", 3, 0),
    ("pre_execution_plan_projection", 4, 0),
    *((f"evidence.{role}", rank, 0) for role, rank, _required in PRE_EXECUTION_EVIDENCE_ROLES),
    ("coordinator_disposition", 20, 0),
    ("selection_head_postimage", 21, 0),
)

FRESH_APPLY_PRECEDENCE = (
    {"rank": 1, "condition": "writer_session_schema_fencing_qualification", "outcome": ("writer_session_closed", "writer_session_process_mismatch", "database_schema_incompatible", "stale_writer_token")},
    {"rank": 2, "condition": "receipt_lookup_failure", "outcome": "mutation_failed"},
    {"rank": 3, "condition": "exact_replay", "outcome": "exact_replay"},
    {"rank": 4, "condition": "mutation_ref_reuse", "outcome": "mutation_ref_reuse_conflict"},
    {"rank": 5, "condition": "coding_global_stop_ref_or_version_conflict", "outcome": "global_stop_version_conflict"},
    {"rank": 6, "condition": "active_coding_global_stop", "outcome": "planning_selection_not_permitted"},
    {"rank": 7, "condition": "current_selection_head_conflict", "outcome": "selection_head_version_conflict"},
    {"rank": 8, "condition": "authority_attestation_invalid", "outcome": "planning_selection_not_permitted"},
    {"rank": 9, "condition": "attempt_or_effect_fence_expired", "outcome": "planning_selection_not_permitted"},
    {"rank": 10, "condition": "planning_context_or_C2B3D_relation_conflict", "outcome": "planning_relation_conflict"},
    {"rank": 11, "condition": "policy_risk_resource_path_cost_token_time_delivery_or_effect_bounds", "outcome": "planning_selection_not_permitted"},
    {"rank": 12, "condition": "proposal_or_disposition_semantic_identity_collision", "outcome": "semantic_identity_conflict"},
    {"rank": 13, "condition": "database_integrity_failure", "outcome": "database_integrity_failure"},
    {"rank": 14, "condition": "write_or_mutation_failure", "outcome": "mutation_failed"},
    {"rank": 15, "condition": "commit_outcome_unknown", "outcome": "commit_outcome_unknown"},
)

EXPECTED_CONTRACT = {
    "contract_identity": {
        "workstream": "COORDINATOR_REMOTE_WORKER_COGNITIVE_PROPOSAL_AND_SELECTION_CONTRACT_FREEZE",
        "status": "uncommitted contract candidate pending independent audit",
        "sole_detailed_semantic_owner": "Section 41",
        "sections_1_40_protected_utf8_length": EXPECTED_SECTIONS_1_40_UTF8_LENGTH,
        "sections_1_40_protected_sha256": EXPECTED_SECTIONS_1_40_SHA256,
        "C2B3D_current_and_unchanged": True,
        "production_or_SQL_implemented_or_authorized": False,
    },
    "audit_repair_scope": {
        "classification": "repair to implementation-defining detail without reopening the accepted operating model",
        "findings_closed": ("S41-001", "S41-002", "S41-003", "S41-004", "S41-005", "S41-006", "S41-007"),
        "preselection_bundle": "planning context, source invocation, private artifact, safe projection, evidence bindings, authority attestation, and model proposal are complete, immutable, and digestible before database access",
        "fresh_transaction": "validates current rows and immutable inputs, mutates no proposal-bundle field, then captures one Coordinator decision timestamp",
        "replay_and_recovery": "reuse persisted timestamps and never call a clock",
        "migration_0003_SQL_or_runtime_added": False,
    },
    "canonicalization_and_scalar_grammar": {
        "profile": "canonical-json.sorted-keys.utf8.v1",
        "recursive_runtime_types": ("dict", "tuple", "str", "int", "bool", "NoneType"),
        "serialized_container_mapping": (("dict", "JSON_object"), ("tuple", "JSON_array")),
        "dict_keys": "exact built-in str, unique, NFC, schema-ordered before canonical serialization",
        "strings": "exact built-in str, NFC, UTF-8, no C0 controls or DEL",
        "integers": "exact built-in int and not bool",
        "canonical_bytes": "UTF-8, sorted object keys, compact separators, ensure_ascii false, allow_nan false, no BOM or final newline",
        "domain_digest": "SHA-256(domain UTF-8 || 0x00 || canonical bytes)",
        "row_self_digest": "domain digest of exact ordered row mapping excluding only its named self-digest field",
        "safe_ref": "SQLite text, 1..96 ASCII [0-9A-Za-z.-], first ASCII alnum, excluded case-insensitive prefixes connector-, tunnel-, workspace-, org-, organization-, user-",
        "sha256": "SQLite text, exactly 64 lowercase hexadecimal characters",
        "sha1": "SQLite text, exactly 40 lowercase hexadecimal characters",
        "reason_code": "SQLite text, 1..96 ASCII [a-z0-9_.-], first lowercase ASCII letter",
        "utc_second": "SQLite text, exact valid YYYY-MM-DDTHH:MM:SSZ with year 0001..9999 and no fractional second",
        "sqlite_declaration": "every migration-0003 column is ANY in a STRICT table and every scalar predicate includes exact typeof checks",
        "foreign_key_action": "ON UPDATE RESTRICT ON DELETE RESTRICT",
        "unknown_fields_or_subclassed_values": "invalid before canonicalization or digest comparison",
    },
    "safe_model_configuration": {
        "schema_id": SCHEMA_IDS["safe_model_configuration"],
        "digest_domain": DIGEST_DOMAINS["safe_model_configuration"],
        "field_order": (
            "schema_id",
            "model_configuration_ref",
            "model_contract_ref",
            "model_contract_digest",
            "implementation_family",
            "capability_profile_ref",
            "capability_profile_digest",
            "input_policy_ref",
            "input_policy_digest",
            "output_policy_ref",
            "output_policy_digest",
            "model_configuration_digest",
        ),
        "implementation_family": ("configured_reasoning_model",),
        "refs": "safe_ref",
        "digests": "sha256",
        "identity_excludes": ("model_configuration_digest",),
        "forbids": (
            "provider endpoint",
            "credential",
            "header",
            "account ID",
            "organization ID",
            "session ID",
            "bearer material",
        ),
        "one_currently_configured_identity_is_sufficient_for_both_phases": True,
    },
    "common_model_proposal_envelope": {
        "schema_id": SCHEMA_IDS["proposal"],
        "digest_domain": DIGEST_DOMAINS["proposal"],
        "field_order": tuple(name for name, _predicate in TABLE_CONTRACTS["development_model_proposals"]["columns"]),
        "proposal_phases": PHASES,
        "phase_contracts": {
            "pre_execution_plan": {
                "context_schema_id": SCHEMA_IDS["pre_execution_context"],
                "artifact_schema_id": SCHEMA_IDS["pre_execution_artifact"],
                "safe_projection_schema_id": SCHEMA_IDS["pre_execution_projection"],
                "recommendations": PRE_EXECUTION_RECOMMENDATIONS,
            },
            "post_execution_semantic_review": {
                "context_schema_id": SCHEMA_IDS["post_execution_context"],
                "artifact_schema_id": SCHEMA_IDS["post_execution_artifact"],
                "safe_projection_schema_id": SCHEMA_IDS["post_execution_projection"],
                "recommendations": POST_EXECUTION_RECOMMENDATIONS,
            },
        },
        "binds": (
            "proposal identity and phase",
            "source invocation ref and digest",
            "model contract ref and digest",
            "redacted model configuration ref and digest",
            "context schema ref and digest",
            "private artifact schema ref and digest",
            "safe projection schema and digest",
            "phase-closed recommendation and bounded reason code",
            "closed evidence-set ref and digest",
            "proposal-author pre-selection creation time",
            "proposal digest",
        ),
        "proposal_is_program_truth_or_effect_authority": False,
        "source_invocation_or_provider_session_is_program_truth": False,
        "first_source_tranche_admits_phase": "pre_execution_plan",
        "post_execution_rows_or_decision_family_in_first_source_tranche": False,
    },
    "timestamp_and_authorship_split": {
        "planning_context_captured_at": "Coordinator-authored before model invocation, included in planning-context identity, immutable before selection admission",
        "source_invocation_started_at": "already-typed model-adapter source evidence, included in source-invocation identity, never created inside selection transaction",
        "source_invocation_completed_at": "already-typed model-adapter source evidence at or after start and no later than proposal creation, included in source-invocation identity",
        "proposal_created_at": "proposal-author evidence included in proposal identity and immutable before selection admission",
        "coordinator_disposition_decided_at": "captured exactly once inside the fresh transaction only after all current checks; shared by disposition, selection postimage, receipt, and committed result",
        "required_order": "C2B3D committed <= context capture <= source start <= source completion <= proposal creation < Coordinator decision < every applicable expiry",
        "fresh_transaction_populates_or_mutates_preselection_bundle": False,
        "replay_calls_clock": False,
        "recovery_calls_clock": False,
    },
    "pre_execution_private_plan_artifact": {
        "schema_id": SCHEMA_IDS["pre_execution_artifact"],
        "digest_domain": DIGEST_DOMAINS["pre_execution_artifact"],
        "field_order": PRIVATE_PLAN_FIELD_ORDER,
        "storage": "private immutable artifact outside Coordinator SQLite",
        "authorship": "normalized typed model-authored content, never raw provider response",
        "canonical_byte_length": (1, 65_536),
        "bounded_statement": "exact built-in NFC str, 1..field-specific named maximum UTF-8 bytes, no leading/trailing whitespace, at least one Unicode letter or digit, no C0 controls or DEL, and entire case-folded value not tbd, todo, n/a, none, unknown, placeholder, or ...",
        "narrative_byte_limits": NARRATIVE_BYTE_LIMITS,
        "implementation_strategy": {"cardinality": (1, 8), "item": "bounded_statement"},
        "proposed_work_units": {
            "cardinality": (1, 32),
            "field_order": ("ordinal", "work_unit_ref", "action_kind", "summary", "depends_on_work_unit_refs", "authorized_path_ordinals", "expected_output_refs", "validation_refs", "required_evidence_roles", "prerequisite_refs", "stop_condition_refs"),
            "ordinal": "contiguous zero-based",
            "references": "work-unit refs are unique and stable; dependencies resolve, forbid self-dependency, and form an acyclic graph; every output, validation, prerequisite, and stop-condition ref resolves",
            "action_kinds": ("analyze", "modify_authorized_path", "create_authorized_path", "delete_authorized_path", "run_validation", "review_evidence", "prepare_candidate"),
        },
        "affected_authorized_paths": {
            "cardinality": (1, 64),
            "item": "normalized repository-relative path, 1..512 UTF-8 bytes, no absolute path, dot segment, NUL, or duplicate",
            "relation": "ordered strict subset-or-equal of transient WorkSpec authorized_paths and within both AttemptFence and EffectFence path ceilings",
            "durable_content": False,
        },
        "expected_outputs": {
            "cardinality": (1, 32),
            "field_order": ("output_ref", "owner_work_unit_ref", "output_kind", "description"),
            "ownership": "every output has exactly one existing work-unit owner and every work-unit output ref resolves to an output it owns",
            "output_kinds": ("source_change", "test_change", "documentation_change", "candidate_manifest", "validation_evidence"),
        },
        "validation_strategy": {
            "cardinality": (1, 32),
            "field_order": ("ordinal", "validation_ref", "work_unit_refs", "validation_kind", "target", "success_criterion"),
            "coverage": "every validation ref and work-unit ref resolves and every work unit has one or more validation references",
            "validation_kinds": ("focused_test", "contract_test", "static_check", "build", "manual_review"),
        },
        "material_assumptions": {"cardinality": (1, 16), "field_order": ("assumption_ref", "statement")},
        "risks_and_uncertainties": {
            "cardinality": (1, 16),
            "field_order": ("risk_ref", "risk_kind", "description", "mitigation", "materiality", "affected_work_unit_refs"),
            "risk_kinds": ("correctness", "authority", "privacy", "compatibility", "operational", "unknown"),
            "materiality": ("material", "blocking"),
            "numeric_risk_score": False,
        },
        "required_evidence_and_prerequisites": {
            "cardinality": (1, 32),
            "field_order": ("prerequisite_ref", "evidence_role", "requirement"),
            "roles": tuple(role for role, _rank, required in PRE_EXECUTION_EVIDENCE_ROLES if required),
        },
        "stop_or_replan_conditions": {"cardinality": (1, 16), "field_order": ("stop_condition_ref", "statement")},
        "proposed_resource_and_effect_use": {
            "field_order": (
                "allowed_effect_classes", "max_active_invocations", "max_candidate_bytes", "max_changed_files",
                "max_cost_microusd", "max_cpu_seconds", "max_deliveries", "max_deployments",
                "max_local_commits", "max_memory_bytes", "max_merges", "max_model_input_tokens",
                "max_model_output_tokens", "max_pull_requests", "max_pushes", "max_wall_seconds",
            ),
            "allowed_effect_classes_exact_type": "tuple",
            "allowed_effect_classes_vocabulary_and_order": C2A_EFFECT_CLASSES,
            "allowed_effect_classes_relation": "non-empty duplicate-free canonical C2A-ordered exact built-in strings and subset of both AttemptFence and EffectFence allowed-effect sets",
            "relation": "componentwise nonnegative and no greater than current standing-policy, AttemptFence, and author EffectFence ceilings; validation synthesizes no effect",
        },
        "substance_rule": "every listed cardinality minimum, narrative rule, nested type/order rule, ownership rule, and closed cross-reference rule is enforced; empty, placeholder, content-free, recommendation-only, unowned, unresolved, cyclic, or validator-synthesized engineering judgment is invalid",
        "structural_validation_manufactures_engineering_judgment": False,
    },
    "pre_execution_safe_projection": {
        "schema_id": SCHEMA_IDS["pre_execution_projection"],
        "digest_domain": DIGEST_DOMAINS["pre_execution_projection"],
        "field_order": tuple(name for name, _predicate in TABLE_CONTRACTS["development_pre_execution_plan_projections"]["columns"]),
        "contains": (
            "safe refs and digests",
            "bounded nonzero counts",
            "component semantic digests",
            "finite recommendation",
            "bounded reason code",
        ),
        "forbids": (
            "strategy text", "work-unit text", "path strings", "output descriptions", "validation commands or targets",
            "assumption text", "risk text", "prerequisite text", "stop-condition text", "private WorkSpec content",
        ),
        "safe_ref_or_digest_is_retrieval_authority": False,
    },
    "planning_context": {
        "schema_id": SCHEMA_IDS["pre_execution_context"],
        "digest_domain": DIGEST_DOMAINS["pre_execution_context"],
        "field_order": tuple(name for name, _predicate in TABLE_CONTRACTS["development_pre_execution_planning_contexts"]["columns"]),
        "authorship": "Coordinator-authored complete immutable pre-guard input before model invocation and before database access",
        "freshness": "captured before model invocation; the same fenced BEGIN IMMEDIATE transaction later compares it to current rows without populating or mutating it",
        "timestamp_ownership": "planning_context_captured_at is Coordinator-authored pre-selection evidence included in context identity",
        "lineage": "exact existing program, accepted intent, work revision, semantic attempt, candidate, basis decision, author effect, command, fences, and planned delivery",
        "heads": "program, work, effect, and delivery head revisions and effect/delivery head digests are context evidence only and retain their existing meanings",
        "policy_binding": "standing policy, risk lane, repository, base, authorized-path scope, cost, token, time, delivery, effect, validation, and review refs and digests",
        "private_WorkSpec_content": False,
    },
    "c2b3d_prerequisite_crosswalk": {
        "semantic_owner": "Section 39 family_golden_vector",
        "exact_basis": C2B3D_BASIS,
        "comparison": "byte- and relation-exact independent extraction from the current Section-39/C2B3D owner",
        "reused_unique_ref_with_different_payload_or_relation": False,
        "dependent_digests_recomputed_for_each_readiness_variant": True,
    },
    "authority_readiness_policy_and_risk": {
        "planning_authority_states": AUTHORITY_STATES,
        "selected_for_dispatch_gates_permitted_authority_states": ("pending", "verified"),
        "selected_for_dispatch_gates_forbidden_authority_states": ("blocked", "stale", "revoked", "expired"),
        "selected_for_dispatch_gates_requires_global_stop": "clear",
        "pending_authority_permits_planning_and_nonexecuting_selection": True,
        "qualified_remote_host_readiness_required_for_planning": False,
        "qualified_remote_host_readiness_if_present": "optional supporting operational evidence only",
        "fresh_external_verification_immediately_before_dispatch_activity": True,
        "dispatch_activity": (
            "private retrieval", "transport", "process launch", "worker invocation", "validation", "review", "Git execution",
        ),
        "Coordinator_authors_or_infers_verified_authority": False,
        "currentness_attestation": {
            "schema_id": SCHEMA_IDS["authority_attestation"],
            "digest_domain": DIGEST_DOMAINS["authority_attestation"],
            "field_order": AUTHORITY_ATTESTATION_FIELD_ORDER,
            "author": "external_authority_owner_only",
            "subject_kinds": AUTHORITY_SUBJECT_KINDS,
            "monotonic_version_owner": "external_authority_owner_only",
            "selection_window": "issued_at <= coordinator_disposition_decided_at < expires_at",
            "must_bind": "exact C2B3D authority-evaluation ref/digest and exact effect-intent subject ref",
            "invalid": "absent, mixed, malformed, contradictory, wrong-subject, wrong-version, wrong-digest, stale, blocked, revoked, expired, or exact expiry boundary",
            "historical_rule": "later revocation never rewrites an already committed historical selection; every later dispatch-capable tranche binds fresh external verification",
            "immutable_C2B3D_evaluation_is_currentness": False,
        },
        "fence_window": "coordinator_disposition_decided_at is strictly before both AttemptFence and EffectFence expiry",
        "risk_treatment": "private bounded engineering judgment plus exact closed safe policy/effect evidence; no numeric score or general evaluator",
        "host_fallback": "no Mac execution and no Coordinator-host fallback",
    },
    "coordinator_disposition_and_currentness": {
        "dispositions": DISPOSITIONS,
        "authorship": "Coordinator only",
        "proposal_and_disposition_are_distinct_types_and_identities": True,
        "selected_meaning": "eligible only for a later independent dispatch-gate evaluation",
        "initial": "absent head plus null expected revision/digest and null supersedes creates revision zero",
        "supersession": "exact CAS over complete lineage key, prior head revision, prior head digest, and prior disposition; new revision is prior plus one",
        "currentness_source": "development_pre_execution_selection_heads only",
        "currentness_not_inferred_from": (
            "timestamps", "row insertion order", "maximum row ID", "report order", "adapter memory", "model session", "filesystem state",
            "program head", "program-version kind", "work head", "effect head", "delivery head",
        ),
        "later_dispatch_binds": ("current_disposition_ref", "current_proposal_ref", "head_revision", "head_digest", "complete lineage key"),
        "selected_changes": (),
        "selected_does_not_change": (
            "program version", "accepted intent", "work-item revision", "semantic attempt", "effect", "effect head",
            "delivery head", "planned delivery state", "dispatch state", "submission state", "acknowledgement", "completion",
            "acceptance", "verified authority", "credentials", "retrieval authority",
        ),
        "model_replan_or_terminal_reject_executes_progression_family": False,
        "timestamp_ownership": "coordinator_disposition_decided_at is captured exactly once inside the fresh transaction after every ordered check and is shared by disposition, head postimage, receipt, and result",
    },
    "migration_0003": {
        "migration_id": "0003_cognitive_proposal_and_selection_state",
        "sequence": 3,
        "application_generation_min": 2,
        "application_generation_max": 2,
        "application_generation_after_migration": 2,
        "posture": "additive non-destructive",
        "rebuilds_migration_0002_table": False,
        "tables": TABLE_CONTRACTS,
        "table_order": tuple(TABLE_CONTRACTS),
        "exact_named_check_algebra": {
            "phase_context_and_artifact_schema_algebra": (
                "pre_execution_plan iff context_schema_id is the pre-execution context schema and artifact_schema_id is the pre-execution artifact schema",
                "post_execution_semantic_review iff context_schema_id is the post-execution context schema and artifact_schema_id is the post-execution artifact schema",
            ),
            "phase_artifact_and_projection_schema_algebra": (
                "pre_execution_plan iff artifact_schema_id is the pre-execution artifact schema and safe_projection_schema_id is the pre-execution projection schema",
                "post_execution_semantic_review iff artifact_schema_id is the post-execution artifact schema and safe_projection_schema_id is the post-execution projection schema",
            ),
            "phase_schema_and_recommendation_algebra": (
                ("pre_execution_plan", SCHEMA_IDS["pre_execution_context"], SCHEMA_IDS["pre_execution_artifact"], SCHEMA_IDS["pre_execution_projection"], PRE_EXECUTION_RECOMMENDATIONS),
                ("post_execution_semantic_review", SCHEMA_IDS["post_execution_context"], SCHEMA_IDS["post_execution_artifact"], SCHEMA_IDS["post_execution_projection"], POST_EXECUTION_RECOMMENDATIONS),
            ),
            "closed_phase_role_rank_required_algebra": {
                "pre_execution_plan": PRE_EXECUTION_EVIDENCE_ROLES,
                "post_execution_semantic_review": POST_EXECUTION_EVIDENCE_ROLES,
                "ordinal": 0,
                "no_other_role_rank_required_tuple": True,
            },
            "initial_or_superseding_disposition_revision_algebra": (
                "null expected revision, expected digest, and supersedes together require resulting revision zero",
                "non-null expected revision, expected digest, and supersedes together require expected revision at most 9223372036854775806 and resulting revision exactly expected plus one",
                "mixed nullability is forbidden",
            ),
            "selection_head_current_relation": "current proposal and disposition identify one exact same-lineage immutable disposition whose disposition equals current_disposition and whose resulting revision and postimage digest equal the head",
            "receipt_closed_family_algebra": (
                "mutation_family is record_pre_execution_plan_disposition",
                "command_schema_id is the exact pre-execution safe command schema",
                "result_class is pre_execution_plan_disposition_recorded",
                "outcome is committed",
                "proposal, disposition, effect, head revision, head digest, result digest, graph digest, timestamp, and receipt digest are all non-null and exact",
            ),
            "exact_C2B3D_program_attempt_candidate_effect_command_fence_delivery_lineage": "every repeated program/version/intent/work/attempt/candidate/effect/command/fence/delivery ref and digest equals the corresponding already-validated migration-0002 row and every row belongs to the same author-effect family",
            "exact_current_program_work_effect_delivery_heads": "each current head exists exactly once; program and work heads still name the context version/revision; effect head still names the author fence; delivery head still names the planned delivery; all four exact revisions and the two persisted head digests equal the context",
            "exact_global_stop_and_authority_evaluation": "global-stop ref/version/state and immutable C2B3D effect-authority evaluation ref/digest equal fresh observations while separately supplied external attestation state/version/window/subject/source/digest satisfy selection currentness; Coordinator does not synthesize verified",
            "closed_policy_risk_repository_base_path_cost_token_time_delivery_effect_evidence": "the fourteen required pre-execution evidence roles exist exactly once at ordinal zero, equal their context or safe-binding facts, and bind standing policy, risk lane, repository, exact base OID, authorized path, cost, token, time, delivery, effect, external authority currentness, global stop, validation, and review evidence",
            "exact_source_invocation_and_artifact_binding_equality": "proposal phase, model contract/configuration, context, artifact, projection, source digest, artifact digest, and immutable pre-selection times exactly equal their source-invocation and artifact-binding rows",
            "proposal_is_pre_execution_and_all_refs_digests_recommendation_reason_equal": "projection proposal/artifact/context refs, safe projection digest, recommendation, and reason code exactly equal the pre-execution proposal, binding, context, and validated private artifact",
            "all_substantive_counts_are_nonzero_and_bounded": "strategy 1..8, work units 1..32, affected paths 1..64, outputs 1..32, validation steps 1..32, assumptions 1..16, risks 1..16, prerequisites 1..32, and stop conditions 1..16; all narratives and nested references satisfy the frozen finite grammar",
            "all_required_phase_roles_exactly_once": "the evidence-set digest covers every required role for its phase exactly once in ascending fixed rank with ordinal zero and covers no foreign or duplicate role",
            "qualified_remote_host_readiness_zero_or_one_and_never_required_for_selection": "context readiness ref/digest are both null iff no readiness evidence row and no rank 19; both valid and concrete iff exactly one non-required readiness row and one rank-19 graph member; every mixed, duplicate, wrong-role, wrong-locator, wrong-digest, unowned, or receipt-member shape is invalid; presence never changes selection eligibility",
            "initial_head_requires_null_preimage_null_supersedes_and_result_revision_zero": "expected selection revision, expected selection digest, and supersedes disposition are all null, the exact complete lineage key is absent, and resulting revision is zero",
            "supersession_requires_exact_preimage_supersedes_and_result_revision_plus_one": "expected selection revision/digest and supersedes disposition are all non-null, equal the freshly read complete-key head, expected revision is at most 9223372036854775806, and resulting revision is exactly expected plus one",
            "selected_requires_current_clear_stop_and_authority_pending_or_verified": "selected_for_dispatch_gates requires clear coding global stop, externally attested pending or verified authority with exact subject/evaluation/version/digest and issued <= decision < attestation/fence expiries, all required evidence, and all proposed path/resource/effect use inside current ceilings; it still grants no executable authority",
            "deferred_or_blocked_changes_no_other_progression_fact": "deferred and blocked are durable non-selections in this family and may change only the dedicated selection head; neither invokes any existing replan, reject, cancel, accept, effect, or delivery transition",
            "current_proposal_disposition_and_lineage_exactly_equal": "head current proposal and disposition resolve exactly once; proposal is pre_execution_plan; disposition names that proposal and has the exact head lineage, disposition value, resulting revision, and postimage digest",
            "only_current_fields_revision_timestamp_and_digest_may_change": "schema and all program/version/intent/work/attempt/candidate/effect/command/fence/delivery lineage columns are immutable; only current_proposal_ref, current_disposition_ref, current_disposition, head_revision, updated_at, and head_digest may change",
            "CAS_update_matches_complete_key_prior_revision_and_prior_disposition": "UPDATE predicate contains the complete eight-column primary key plus prior head_revision, head_digest, and current_disposition_ref and exactly one affected row is required",
            "closed_pre_execution_family_result_algebra": "receipt admits only record_pre_execution_plan_disposition with the exact safe command schema, pre_execution_plan_disposition_recorded result class, committed outcome, and non-null exact proposal/disposition/effect/head/result/graph bindings",
            "exact_result_graph_and_selection_postimage_binding": "receipt result digest equals the canonical original result, graph digest equals the exact ordered supplied graph, and head revision/digest equal the immutable disposition-owned reconstructed original selection-head postimage",
        },
        "transaction_only_relations_not_claimed_as_SQL_CHECKs": (
            "required evidence-set completeness",
            "cross-row digest equality beyond foreign keys",
            "C2B3D lineage and current-head equality",
            "standing-policy and resource/effect ceiling comparison",
            "selected authority-state and global-stop policy",
            "CAS success and affected-row cardinality",
        ),
        "new_table_count": 9,
        "immutable_tables": IMMUTABLE_TABLES,
        "explicit_indexes": (),
        "triggers": TRIGGERS,
        "trigger_count": 18,
        "trigger_program": tuple(
            trigger
            for table in IMMUTABLE_TABLES
            for trigger in (
                (
                    f"{table}_no_update",
                    "BEFORE UPDATE",
                    None,
                    f"RAISE(ABORT,'append_only_{table}')",
                ),
                (
                    f"{table}_no_delete",
                    "BEFORE DELETE",
                    None,
                    f"RAISE(ABORT,'append_only_{table}')",
                ),
            )
        )
        + (
            (
                "development_pre_execution_selection_heads_no_delete",
                "BEFORE DELETE",
                None,
                "RAISE(ABORT,'no_delete_development_pre_execution_selection_heads')",
            ),
            (
                "development_pre_execution_selection_heads_lineage_immutable",
                "BEFORE UPDATE",
                (
                    "schema_id", "program_ref", "program_version_ref", "accepted_intent_revision_ref",
                    "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref", "candidate_ref",
                    "effect_intent_ref", "author_command_ref", "author_command_digest", "attempt_fence_ref",
                    "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest", "delivery_attempt_ref",
                    "delivery_envelope_digest",
                ),
                "RAISE(ABORT,'immutable_development_pre_execution_selection_lineage') when any named OLD value IS NOT the corresponding NEW value",
            ),
        ),
        "head_write_contract": {
            "initial_insert": "INSERT one exact revision-zero row only after proving the complete lineage key absent",
            "superseding_update_set_order": ("current_proposal_ref", "current_disposition_ref", "current_disposition", "head_revision", "updated_at", "head_digest"),
            "superseding_update_where_order": (
                "program_ref", "semantic_attempt_ref", "candidate_ref", "effect_intent_ref", "author_command_ref",
                "attempt_fence_ref", "effect_fence_ref", "delivery_attempt_ref", "head_revision",
                "head_digest", "current_disposition_ref",
            ),
            "required_affected_row_count": 1,
            "zero_rows": "selection_head_version_conflict",
            "more_than_one_row": "database_integrity_failure",
        },
        "seed_rows": (),
        "bootstrap_latch": False,
        "cumulative_after_0003": {"user_tables": 39, "explicit_indexes": 1, "triggers": 64},
        "historical_0003_inventory_restored": False,
        "generic_metadata_or_event_bag": False,
        "one_authoritative_writer_per_mutable_fact": {"development_pre_execution_selection_heads": "Coordinator_cognitive_mutation_family_only"},
    },
    "safe_mutation_command": {
        "schema_id": SCHEMA_IDS["safe_command"],
        "digest_domain": DIGEST_DOMAINS["safe_command"],
        "field_order": SAFE_COMMAND_FIELD_ORDER,
        "identity_excludes": ("mutation_command_digest",),
        "caller_supplies_proposed_SQL_rows_receipt_or_current_head": False,
        "raw_artifact_crosses_SQLite_transaction_boundary": False,
    },
    "mutation_family": {
        "name": "record_pre_execution_plan_disposition",
        "first_source_runtime_accepted_phase": "pre_execution_plan",
        "preflight_before_writer_or_SQLite": (
            "exact built-in closed-world private artifact, safe configuration, source invocation, proposal, command, and evidence shapes",
            "canonical and domain digest equality",
            "substantive engineering-judgment minima",
            "private affected paths are normalized and within transient WorkSpec and fence ceilings",
            "proposed resource/effect use is componentwise within current ceilings",
            "configured model contract/configuration identity is admitted",
            "no prohibited raw provider/session/WorkSpec material",
            "complete immutable planning context, source invocation, artifact, proposal, safe projection, evidence, attestation, and command are digestible before database access",
        ),
        "fresh_read_and_validation_order": (
            "writer fencing",
            "receipt lookup",
            "same mutation key command-digest replay or reuse conflict",
            "coding-global-stop ref and version then active-state check",
            "current pre-execution selection head or proved absence",
            "external authority-attestation currentness, subject, evaluation binding, version, state, and expiry",
            "AttemptFence and EffectFence expiry",
            "program/version/intent/work/attempt/candidate/decision/effect/command/fence/delivery lineage and all current heads",
            "policy, risk, resource, path, cost, token, time, delivery, and effect bounds",
            "all preassigned identity collision probes",
            "closed evidence-set completeness and exact relation validation",
            "safe projection equality to preflight-validated private artifact",
            "disposition policy and supersession validation",
            "capture coordinator_disposition_decided_at exactly once",
        ),
        "fresh_apply_total_precedence": FRESH_APPLY_PRECEDENCE,
        "qualified_remote_host_readiness_read_or_required": False,
        "timestamp_algebra": {
            "preselection": "C2B3D committed <= planning_context_captured_at <= source_invocation_started_at <= source_invocation_completed_at <= proposal_created_at",
            "selection": "proposal_created_at < coordinator_disposition_decided_at < authority-attestation, AttemptFence, and EffectFence expiry",
            "immutable_input_mutation_inside_transaction": False,
            "Coordinator_decision_time_capture_count": 1,
            "decision_time_consumers": ("Coordinator disposition", "selection-head postimage", "receipt", "committed result"),
            "replay_or_recovery_calls_clock": False,
        },
        "physical_write_order": (
            "development_model_source_invocations",
            "development_pre_execution_planning_contexts",
            "development_private_proposal_artifact_bindings",
            "development_model_proposals",
            "development_pre_execution_plan_projections",
            "development_model_proposal_evidence_bindings in ascending role_rank",
            "development_pre_execution_dispositions",
            "development_pre_execution_selection_heads INSERT revision zero or exact CAS UPDATE",
            "development_cognitive_mutation_receipts",
        ),
        "graph_roles_rank_ordinal": GRAPH_ROLES,
        "receipt_is_graph_member": False,
        "commit_attempts": 1,
        "no_external_IO": True,
    },
    "replay_conflict_and_recovery": {
        "result_projection_field_order": (
            "schema_id", "mutation_ref", "proposal_ref", "disposition_ref", "disposition", "program_ref",
            "semantic_attempt_ref", "candidate_ref", "effect_intent_ref", "selection_head_revision",
            "selection_head_digest", "recorded_at", "result_projection_digest",
        ),
        "receipt_namespace": "development_cognitive_mutation_receipts/record_pre_execution_plan_disposition",
        "receipt_first_exact_replay": True,
        "same_key_same_digest": "return original receipt-owned result without clock, write, policy reinterpretation, host readiness, external I/O, or COMMIT",
        "same_key_different_digest": "mutation_ref_reuse_conflict",
        "stale_writer_precedes_idempotency_disclosure": True,
        "stale_current": "selection_head_version_conflict",
        "relation_conflict": "planning_relation_conflict",
        "semantic_identity_collision": "semantic_identity_conflict",
        "malformed_persisted_family": "database_integrity_failure",
        "commit_exception_after_attempt": "commit_outcome_unknown",
        "automatic_semantic_retry": False,
        "recovery_authority": "fresh acquired and fenced WriterSession only",
        "recovery_transaction": "read-only",
        "recovery_dispositions": ("committed_exact", "definitely_not_committed", "unresolved"),
        "committed_exact": "receipt, all immutable rows, exact supplied graph, result, and reconstructed original selection-head postimage verify, and current head either equals that postimage or reaches it through the exact bounded predecessor proof",
        "definitely_not_committed": "receipt and every preassigned immutable identity absent and selection head exactly equals the command preimage or remains absent",
        "unresolved": "partial, malformed, contradictory, colliding, foreign, missing, duplicate, cyclic, over-limit, wrong-lineage, revision-jumping, branched, disconnected, or otherwise unverifiable evidence, or a current head older than or contradictory to the original postimage",
        "later_head_ancestry": {
            "line_fields": ("lineage_key", "disposition_ref", "prior_disposition_ref", "prior_head_revision", "prior_head_digest", "resulting_head_revision", "resulting_head_digest"),
            "exact_successor": "each current disposition row matches the cursor lineage/ref/resulting revision/digest and names the unique prior disposition at revision minus one with its exact head digest",
            "maximum_predecessor_transitions": 256,
            "overflow_sentinel_read": 257,
            "terminal": "the exact receipt-owned disposition ref, head revision, and head digest",
            "current_later_head_replaces_historical_graph_member": False,
        },
        "recovery_writes_clock_COMMIT_or_external_IO": False,
        "later_dispatch_revalidates_every_current_gate": True,
    },
    "privacy_and_model_replacement": {
        "private_outside_SQLite": (
            "normalized typed proposal artifact", "raw prompts", "hidden reasoning", "provider session or conversation history",
            "raw model responses", "provider request or response payloads", "unrestricted transcripts or logs", "private WorkSpec contents",
            "arbitrary model-generated text", "credentials", "headers", "endpoints", "account IDs", "organization IDs", "bearer material",
        ),
        "SQLite_safe_only": (
            "closed schema IDs", "safe refs", "digests", "bounded counts", "finite phase/recommendation/status/reason",
            "closed role-specific evidence bindings", "Coordinator disposition", "current selection", "receipt",
        ),
        "safe_ref_or_digest_grants_retrieval": False,
        "one_configured_model_for_both_phases_is_sufficient": True,
        "replacement_changes": ("model_configuration_ref", "model_configuration_digest", "source_invocation_ref", "proposal_ref", "proposal_digest"),
        "replacement_does_not_change": (
            "program", "attempt", "candidate", "effect", "author command", "planned delivery",
        ),
        "tournament_router_governor_qualification_promotion_or_evaluator_platform": False,
    },
    "c2a_placement_amendment": {
        "scope": "finite candidate supersession of only the prior model-proposal placement clause; no existing C2A schema, vector, field order, or digest identity changes",
        "Coordinator_SQLite_may_contain_only": (
            "model contract and redacted configuration refs and digests",
            "source invocation ref, digest, phase, and normalized-proposal status",
            "proposal, context, private-artifact, and safe-projection schema IDs, refs, and digests",
            "bounded substantive-field counts and component digests",
            "closed proposal phase, recommendation, status, and reason code",
            "closed role-specific evidence refs and digests",
            "Coordinator disposition and dedicated current-selection facts",
            "closed mutation receipt, graph digest, and safe result projection",
        ),
        "SQLite_reports_logs_errors_and_unrestricted_diagnostics_continue_to_forbid": (
            "raw prompts", "hidden reasoning", "provider sessions", "conversation history", "raw model responses",
            "provider request or response payloads", "unrestricted transcripts", "arbitrary model-generated text",
            "private WorkSpec objective, requirements, exclusions, or authorized path strings", "private plan text",
            "credentials", "headers", "endpoints", "account IDs", "organization IDs", "bearer material",
            "database rows or canonical private artifacts as public reports", "unrestricted logs",
        ),
        "private_artifact_location": "outside SQLite under separately governed custody not selected or implemented here",
        "safe_ref_or_digest_is_retrieval_authority": False,
    },
    "post_execution_compatibility": {
        "common_tables": (
            "development_model_source_invocations",
            "development_private_proposal_artifact_bindings",
            "development_model_proposals",
            "development_model_proposal_evidence_bindings",
        ),
        "closed_phase": "post_execution_semantic_review",
        "closed_recommendations": POST_EXECUTION_RECOMMENDATIONS,
        "closed_evidence_roles": POST_EXECUTION_EVIDENCE_ROLES,
        "future_transport_interface": "transport and worker results are source evidence only; progression cannot reach semantic acceptance, repair, replan, terminal rejection, Git, or publication without a typed post-execution proposal and a later distinct Coordinator decision family",
        "post_execution_context_projection_or_disposition_tables_in_0003": False,
        "post_execution_Coordinator_decision_family_implemented_or_frozen": False,
    },
    "later_source_boundary_and_absent_effects": {
        "first_later_source_tranche_ends_at": "typed pre-execution proposal admission plus one Coordinator selection or non-selection with durable receipt",
        "first_later_source_tranche_invokes_model": False,
        "full_remote_worker_phase_reduced_to_first_source_tranche": False,
        "absent_and_blocked": (
            "migration 0003 SQL or catalog entry", "production model/provider client", "model invocation", "raw provider custody",
            "worker", "dispatcher", "supervisor", "transport", "remote-host contact", "private retrieval", "process launch",
            "capsule custody", "observation ingest", "post-execution review runtime", "semantic-decision runtime", "Git handler",
            "Execution Substrate adapter", "Bridge widening", "service", "API", "IPC", "queue", "scheduler", "autonomous loop",
            "public StateStore or WriterSession surface", "package export", "network", "external verification", "publication",
        ),
        "selected_for_dispatch_gates_is_executable": False,
        "independent_audit_performed": False,
    },
}


def _assert_closed_value(value: object) -> None:
    if value is None or type(value) in (str, int, bool):
        if type(value) is str:
            assert unicodedata.normalize("NFC", value) == value
            assert all(ord(character) >= 32 and ord(character) != 127 for character in value)
        return
    if type(value) is tuple:
        for item in value:
            _assert_closed_value(item)
        return
    if type(value) is dict:
        for key, item in value.items():
            assert type(key) is str
            _assert_closed_value(key)
            _assert_closed_value(item)
        return
    raise AssertionError("COGNITIVE_CONTRACT_VALUE_TYPE_INVALID")


def _json_value(value: object) -> object:
    _assert_closed_value(value)
    if type(value) is tuple:
        return [_json_value(item) for item in value]
    if type(value) is dict:
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        _json_value(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8", errors="strict")


def _domain_digest(domain: str, identity: object) -> str:
    assert type(domain) is str
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + _canonical_bytes(identity)).hexdigest()


def _independent_canonical_bytes(value: object) -> bytes:
    def audit_types(item: object) -> None:
        if item is None or type(item) in (str, int, bool):
            if type(item) is str:
                assert item == unicodedata.normalize("NFC", item)
                assert "\x00" not in item
            return
        if type(item) is tuple:
            for child in item:
                audit_types(child)
            return
        if type(item) is dict:
            assert all(type(key) is str for key in item)
            for key, child in item.items():
                audit_types(key)
                audit_types(child)
            return
        raise AssertionError("COGNITIVE_AUDIT_TYPE_INVALID")

    audit_types(value)
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return serialized.encode("utf-8", errors="strict")


def _independent_domain_digest(domain: str, identity: object) -> str:
    assert type(domain) is str
    payload = domain.encode("utf-8", errors="strict") + b"\x00"
    return hashlib.sha256(payload + _independent_canonical_bytes(identity)).hexdigest()


def _sealed(
    identity: dict[str, object], *, domain: str, digest_field: str
) -> dict[str, object]:
    assert digest_field not in identity
    return {**identity, digest_field: _domain_digest(domain, identity)}


def _without(mapping: dict[str, object], field: str) -> dict[str, object]:
    assert field in mapping
    return {key: value for key, value in mapping.items() if key != field}


def _record(
    name: str,
    value: object,
    *,
    domain: str,
    semantic_digest: str,
) -> dict[str, object]:
    canonical = _canonical_bytes(value)
    return {
        "name": name,
        "canonical_json": canonical.decode("utf-8", errors="strict"),
        "canonical_utf8_length": len(canonical),
        "raw_sha256": hashlib.sha256(canonical).hexdigest(),
        "digest_domain": domain,
        "semantic_digest": semantic_digest,
    }


def _build_golden_vector(readiness_present: bool) -> dict[str, object]:
    variant = "present" if readiness_present else "absent"
    planning_context_captured_at = "2026-08-22T12:35:00Z"
    source_invocation_started_at = "2026-08-22T12:35:01Z"
    source_invocation_completed_at = "2026-08-22T12:35:02Z"
    proposal_created_at = "2026-08-22T12:35:03Z"
    coordinator_disposition_decided_at = "2026-08-22T12:35:04Z"
    proposal_ref = f"model-proposal.pre.{variant}.0001"
    artifact_ref = f"plan-artifact.private.{variant}.0001"
    planning_context_ref = f"planning-context.pre.{variant}.0001"
    evidence_set_ref = f"proposal-evidence.pre.{variant}.0001"
    disposition_ref = f"planning-disposition.{variant}.0001"

    safe_model_configuration = _sealed(
        {
            "schema_id": SCHEMA_IDS["safe_model_configuration"],
            "model_configuration_ref": "model-config.safe.0001",
            "model_contract_ref": "model-contract.reasoning.0001",
            "model_contract_digest": "1010101010101010101010101010101010101010101010101010101010101010",
            "implementation_family": "configured_reasoning_model",
            "capability_profile_ref": "model-capability.planning-review.0001",
            "capability_profile_digest": "1111111111111111111111111111111111111111111111111111111111111111",
            "input_policy_ref": "model-input-policy.private.0001",
            "input_policy_digest": "1212121212121212121212121212121212121212121212121212121212121212",
            "output_policy_ref": "model-output-policy.typed.0001",
            "output_policy_digest": "1313131313131313131313131313131313131313131313131313131313131313",
        },
        domain=DIGEST_DOMAINS["safe_model_configuration"],
        digest_field="model_configuration_digest",
    )

    resource_effect_use = {
        "allowed_effect_classes": ("author_candidate",),
        "max_active_invocations": 1,
        "max_candidate_bytes": 262_144,
        "max_changed_files": 2,
        "max_cost_microusd": 100_000,
        "max_cpu_seconds": 600,
        "max_deliveries": 1,
        "max_deployments": 0,
        "max_local_commits": 0,
        "max_memory_bytes": 1_073_741_824,
        "max_merges": 0,
        "max_model_input_tokens": 16_000,
        "max_model_output_tokens": 8_000,
        "max_pull_requests": 0,
        "max_pushes": 0,
        "max_wall_seconds": 1_200,
    }
    private_plan_artifact = _sealed(
        {
            "schema_id": SCHEMA_IDS["pre_execution_artifact"],
            "artifact_ref": artifact_ref,
            "proposal_ref": proposal_ref,
            "proposal_phase": "pre_execution_plan",
            "planning_context_ref": planning_context_ref,
            "implementation_strategy": (
                "Extend the semantic owner with one additive closed contract and qualify it with a direct independent oracle.",
                "Preserve the current author-effect family and constrain the later source tranche to non-executing proposal admission and selection.",
            ),
            "proposed_work_units": (
                {
                    "ordinal": 0,
                    "work_unit_ref": "work-unit.analyze.0001",
                    "action_kind": "analyze",
                    "summary": "Confirm the current semantic and privacy boundaries before any bounded edit.",
                    "depends_on_work_unit_refs": (),
                    "authorized_path_ordinals": (0, 1),
                    "expected_output_refs": ("output.analysis.0001",),
                    "validation_refs": ("validation.contract.0001",),
                    "required_evidence_roles": ("standing_policy", "authorized_path_scope", "effect_ceiling"),
                    "prerequisite_refs": ("prerequisite.authority.0001",),
                    "stop_condition_refs": ("stop.boundary.0001", "stop.currentness.0001"),
                },
                {
                    "ordinal": 1,
                    "work_unit_ref": "work-unit.modify.0001",
                    "action_kind": "modify_authorized_path",
                    "summary": "Apply the closed contract and direct-test changes only inside the authorized path subset.",
                    "depends_on_work_unit_refs": ("work-unit.analyze.0001",),
                    "authorized_path_ordinals": (0, 1),
                    "expected_output_refs": ("output.contract.0001", "output.test.0001"),
                    "validation_refs": ("validation.contract.0001",),
                    "required_evidence_roles": ("repository_binding", "base_binding", "risk_lane"),
                    "prerequisite_refs": ("prerequisite.scope.0001",),
                    "stop_condition_refs": ("stop.boundary.0001",),
                },
                {
                    "ordinal": 2,
                    "work_unit_ref": "work-unit.validate.0001",
                    "action_kind": "run_validation",
                    "summary": "Run the focused contract oracle and stop on any authority, privacy, or prefix-integrity failure.",
                    "depends_on_work_unit_refs": ("work-unit.modify.0001",),
                    "authorized_path_ordinals": (1,),
                    "expected_output_refs": ("output.validation.0001",),
                    "validation_refs": ("validation.contract.0001", "validation.boundary.0001"),
                    "required_evidence_roles": ("validation_requirement", "review_requirement"),
                    "prerequisite_refs": ("prerequisite.authority.0001", "prerequisite.scope.0001"),
                    "stop_condition_refs": ("stop.boundary.0001",),
                },
            ),
            "affected_authorized_paths": (
                ".docs/system_overview/hybrid_integration_architecture_adr.md",
                "docs_contract_test.go",
            ),
            "expected_outputs": (
                {
                    "output_ref": "output.analysis.0001",
                    "owner_work_unit_ref": "work-unit.analyze.0001",
                    "output_kind": "candidate_manifest",
                    "description": "A bounded analysis manifest for the current semantic and privacy constraints.",
                },
                {
                    "output_ref": "output.contract.0001",
                    "owner_work_unit_ref": "work-unit.modify.0001",
                    "output_kind": "documentation_change",
                    "description": "One bounded semantic-owner amendment with an exact additive schema contract.",
                },
                {
                    "output_ref": "output.test.0001",
                    "owner_work_unit_ref": "work-unit.modify.0001",
                    "output_kind": "test_change",
                    "description": "One direct finite oracle that recomputes the safe contract vector independently.",
                },
                {
                    "output_ref": "output.validation.0001",
                    "owner_work_unit_ref": "work-unit.validate.0001",
                    "output_kind": "validation_evidence",
                    "description": "Focused pass evidence with no production import or external effect.",
                },
            ),
            "validation_strategy": (
                {
                    "ordinal": 0,
                    "validation_ref": "validation.contract.0001",
                    "work_unit_refs": ("work-unit.analyze.0001", "work-unit.modify.0001", "work-unit.validate.0001"),
                    "validation_kind": "contract_test",
                    "target": "Section 41 owner literal, vector, placement, and prefix integrity.",
                    "success_criterion": "Every direct oracle and bounded causal mutant passes under warnings-as-errors.",
                },
                {
                    "ordinal": 1,
                    "validation_ref": "validation.boundary.0001",
                    "work_unit_refs": ("work-unit.validate.0001",),
                    "validation_kind": "focused_test",
                    "target": "Current C2A, authority, architecture, and C2B3D status boundaries.",
                    "success_criterion": "No current implementation, schema, runtime, or authority claim is widened.",
                },
            ),
            "material_assumptions": (
                {"assumption_ref": "assumption.lineage.0001", "statement": "Migration 0002 and the current C2B3D lineage remain byte-exact and semantically authoritative."},
                {"assumption_ref": "assumption.privacy.0001", "statement": "The supplied normalized typed artifact was produced outside SQLite without retaining raw provider material."},
            ),
            "risks_and_uncertainties": (
                {
                    "risk_ref": "risk.authority.0001",
                    "risk_kind": "authority",
                    "description": "A planning selection could be mistaken for executable permission.",
                    "mitigation": "Use a dedicated disposition and require fresh external verification at the later dispatch gate.",
                    "materiality": "blocking",
                    "affected_work_unit_refs": ("work-unit.modify.0001", "work-unit.validate.0001"),
                },
                {
                    "risk_ref": "risk.privacy.0001",
                    "risk_kind": "privacy",
                    "description": "Private engineering text could leak into durable SQLite projection.",
                    "mitigation": "Persist only counts, closed codes, safe references, and semantic digests.",
                    "materiality": "material",
                    "affected_work_unit_refs": ("work-unit.modify.0001",),
                },
            ),
            "required_evidence_and_prerequisites": (
                {"prerequisite_ref": "prerequisite.authority.0001", "evidence_role": "authority_currentness_attestation", "requirement": "Bind externally authored currentness and reject blocked, stale, revoked, expired, or out-of-window authority."},
                {"prerequisite_ref": "prerequisite.scope.0001", "evidence_role": "authorized_path_scope", "requirement": "Prove every proposed path is inside the current path ceiling."},
            ),
            "stop_or_replan_conditions": (
                {"stop_condition_ref": "stop.boundary.0001", "statement": "Stop if any production, SQL, migration-0002, or C2B3D byte would need to change."},
                {"stop_condition_ref": "stop.currentness.0001", "statement": "Replan if the dedicated selection head cannot remain independent of program, work, effect, and delivery heads."},
            ),
            "proposed_resource_and_effect_use": resource_effect_use,
            "recommendation": "select_for_dispatch_gates",
            "reason_code": "plan.bounded_contract_change",
        },
        domain=DIGEST_DOMAINS["pre_execution_artifact"],
        digest_field="artifact_digest",
    )

    component_values = {
        "affected_path_set": private_plan_artifact["affected_authorized_paths"],
        "expected_output_set": private_plan_artifact["expected_outputs"],
        "validation_strategy": private_plan_artifact["validation_strategy"],
        "assumption_set": private_plan_artifact["material_assumptions"],
        "risk_set": private_plan_artifact["risks_and_uncertainties"],
        "prerequisite_set": private_plan_artifact["required_evidence_and_prerequisites"],
        "stop_condition_set": private_plan_artifact["stop_or_replan_conditions"],
        "resource_effect_use": resource_effect_use,
    }
    component_digests = {
        name: _domain_digest(DIGEST_DOMAINS[name], value)
        for name, value in component_values.items()
    }
    safe_projection = _sealed(
        {
            "schema_id": SCHEMA_IDS["pre_execution_projection"],
            "proposal_ref": proposal_ref,
            "artifact_ref": artifact_ref,
            "planning_context_ref": planning_context_ref,
            "strategy_item_count": len(private_plan_artifact["implementation_strategy"]),
            "work_unit_count": len(private_plan_artifact["proposed_work_units"]),
            "affected_path_count": len(private_plan_artifact["affected_authorized_paths"]),
            "affected_path_set_digest": component_digests["affected_path_set"],
            "expected_output_count": len(private_plan_artifact["expected_outputs"]),
            "expected_output_set_digest": component_digests["expected_output_set"],
            "validation_step_count": len(private_plan_artifact["validation_strategy"]),
            "validation_strategy_digest": component_digests["validation_strategy"],
            "assumption_count": len(private_plan_artifact["material_assumptions"]),
            "assumption_set_digest": component_digests["assumption_set"],
            "risk_count": len(private_plan_artifact["risks_and_uncertainties"]),
            "risk_set_digest": component_digests["risk_set"],
            "prerequisite_count": len(private_plan_artifact["required_evidence_and_prerequisites"]),
            "prerequisite_set_digest": component_digests["prerequisite_set"],
            "stop_condition_count": len(private_plan_artifact["stop_or_replan_conditions"]),
            "stop_condition_set_digest": component_digests["stop_condition_set"],
            "proposed_resource_effect_use_digest": component_digests["resource_effect_use"],
            "recommendation": private_plan_artifact["recommendation"],
            "reason_code": private_plan_artifact["reason_code"],
        },
        domain=DIGEST_DOMAINS["pre_execution_projection"],
        digest_field="safe_projection_digest",
    )

    authority_attestation = _sealed(
        {
            "schema_id": SCHEMA_IDS["authority_attestation"],
            "authority_attestation_ref": "authority-attestation.current.0001",
            "authoritative_subject_kind": "effect_intent",
            "authoritative_subject_ref": C2B3D_BASIS["effect_intent_ref"],
            "authority_evaluation_ref": C2B3D_BASIS["authority_evaluation_ref"],
            "authority_evaluation_digest": C2B3D_BASIS["authority_evaluation_digest"],
            "authority_state": "pending",
            "authority_version": 1,
            "issued_at": "2026-08-22T12:34:57Z",
            "expires_at": "2026-08-22T13:34:55Z",
            "source_authority_ref": "repo-policy.authority.0001",
        },
        domain=DIGEST_DOMAINS["authority_attestation"],
        digest_field="authority_attestation_digest",
    )
    readiness_ref = "remote-readiness.qualified.0001" if readiness_present else None
    readiness_digest = (
        "8989898989898989898989898989898989898989898989898989898989898989"
        if readiness_present
        else None
    )

    planning_context = _sealed(
        {
            "schema_id": SCHEMA_IDS["pre_execution_context"],
            "planning_context_ref": planning_context_ref,
            "program_ref": C2B3D_BASIS["program_ref"],
            "program_version_ref": C2B3D_BASIS["program_version_ref"],
            "program_version_number": C2B3D_BASIS["program_version_number"],
            "accepted_intent_revision_ref": C2B3D_BASIS["accepted_intent_revision_ref"],
            "work_item_ref": C2B3D_BASIS["work_item_ref"],
            "work_item_revision_ref": C2B3D_BASIS["work_item_revision_ref"],
            "semantic_attempt_ref": C2B3D_BASIS["semantic_attempt_ref"],
            "semantic_attempt_digest": C2B3D_BASIS["semantic_attempt_digest"],
            "attempt_number": 1,
            "candidate_ref": C2B3D_BASIS["candidate_ref"],
            "basis_decision_ref": C2B3D_BASIS["basis_decision_ref"],
            "basis_decision_digest": C2B3D_BASIS["basis_decision_digest"],
            "work_spec_ref": C2B3D_BASIS["work_spec_ref"],
            "work_spec_digest": C2B3D_BASIS["work_spec_digest"],
            "work_spec_safe_projection_digest": C2B3D_BASIS["work_spec_safe_projection_digest"],
            "effect_intent_ref": C2B3D_BASIS["effect_intent_ref"],
            "effect_intent_digest": C2B3D_BASIS["effect_intent_digest"],
            "author_command_ref": C2B3D_BASIS["author_command_ref"],
            "author_command_digest": C2B3D_BASIS["author_command_digest"],
            "standing_grant_ref": C2B3D_BASIS["standing_grant_ref"],
            "standing_grant_digest": C2B3D_BASIS["standing_grant_digest"],
            "attempt_authorization_ref": C2B3D_BASIS["attempt_authorization_ref"],
            "attempt_authorization_digest": C2B3D_BASIS["attempt_authorization_digest"],
            "effect_authorization_ref": C2B3D_BASIS["effect_authorization_ref"],
            "effect_authorization_digest": C2B3D_BASIS["effect_authorization_digest"],
            "attempt_fence_ref": C2B3D_BASIS["attempt_fence_ref"],
            "attempt_fence_digest": C2B3D_BASIS["attempt_fence_digest"],
            "attempt_fence_allowed_effect_classes_json": _canonical_bytes(C2B3D_BASIS["attempt_fence_allowed_effect_classes"]).decode("utf-8"),
            "attempt_fence_expires_at": C2B3D_BASIS["attempt_fence_expires_at"],
            "effect_fence_ref": C2B3D_BASIS["effect_fence_ref"],
            "effect_fence_digest": C2B3D_BASIS["effect_fence_digest"],
            "effect_fence_allowed_effect_classes_json": _canonical_bytes(C2B3D_BASIS["effect_fence_allowed_effect_classes"]).decode("utf-8"),
            "effect_fence_expires_at": C2B3D_BASIS["effect_fence_expires_at"],
            "delivery_attempt_ref": C2B3D_BASIS["delivery_attempt_ref"],
            "delivery_envelope_digest": C2B3D_BASIS["delivery_envelope_digest"],
            "delivery_attempt_digest": C2B3D_BASIS["delivery_attempt_digest"],
            "expected_program_head_revision": 0,
            "expected_work_item_head_revision": 0,
            "expected_effect_head_fence_ref": C2B3D_BASIS["effect_fence_ref"],
            "expected_effect_head_revision": C2B3D_BASIS["effect_head_revision"],
            "expected_effect_head_digest": C2B3D_BASIS["effect_head_digest"],
            "expected_delivery_head_attempt_ref": C2B3D_BASIS["delivery_attempt_ref"],
            "expected_delivery_head_revision": C2B3D_BASIS["delivery_head_revision"],
            "expected_delivery_head_digest": C2B3D_BASIS["delivery_head_digest"],
            "global_stop_ref": C2B3D_BASIS["coding_global_stop_ref"],
            "global_stop_version": C2B3D_BASIS["coding_global_stop_version"],
            "global_stop_state": "clear",
            "authority_evaluation_ref": C2B3D_BASIS["authority_evaluation_ref"],
            "authority_evaluation_digest": C2B3D_BASIS["authority_evaluation_digest"],
            "authority_attestation_schema_id": authority_attestation["schema_id"],
            "authority_attestation_ref": authority_attestation["authority_attestation_ref"],
            "authoritative_subject_kind": authority_attestation["authoritative_subject_kind"],
            "authoritative_subject_ref": authority_attestation["authoritative_subject_ref"],
            "authority_state": authority_attestation["authority_state"],
            "authority_version": authority_attestation["authority_version"],
            "authority_issued_at": authority_attestation["issued_at"],
            "authority_expires_at": authority_attestation["expires_at"],
            "authority_source_ref": authority_attestation["source_authority_ref"],
            "authority_attestation_digest": authority_attestation["authority_attestation_digest"],
            "standing_policy_ref": "standing-policy.0001",
            "standing_policy_digest": "2121212121212121212121212121212121212121212121212121212121212121",
            "risk_lane_ref": "risk-lane.bounded.0001",
            "risk_lane_digest": "2222222222222222222222222222222222222222222222222222222222222222",
            "repository_ref": C2B3D_BASIS["repository_ref"],
            "base_git_object_format": C2B3D_BASIS["base_git_object_format"],
            "base_git_oid": C2B3D_BASIS["base_git_oid"],
            "authorized_path_scope_digest": "2323232323232323232323232323232323232323232323232323232323232323",
            "cost_ceiling_ref": "ceiling.cost.0001",
            "cost_ceiling_digest": "2424242424242424242424242424242424242424242424242424242424242424",
            "token_ceiling_ref": "ceiling.token.0001",
            "token_ceiling_digest": "2525252525252525252525252525252525252525252525252525252525252525",
            "time_ceiling_ref": "ceiling.time.0001",
            "time_ceiling_digest": "2626262626262626262626262626262626262626262626262626262626262626",
            "delivery_ceiling_ref": "ceiling.delivery.0001",
            "delivery_ceiling_digest": "2727272727272727272727272727272727272727272727272727272727272727",
            "effect_ceiling_ref": "ceiling.effect.0001",
            "effect_ceiling_digest": "2828282828282828282828282828282828282828282828282828282828282828",
            "validation_requirement_ref": C2B3D_BASIS["validation_requirement_ref"],
            "validation_requirement_digest": C2B3D_BASIS["validation_requirement_digest"],
            "validation_safe_evidence_digest": C2B3D_BASIS["validation_safe_evidence_digest"],
            "review_requirement_ref": C2B3D_BASIS["review_requirement_ref"],
            "review_requirement_digest": C2B3D_BASIS["review_requirement_digest"],
            "review_safe_evidence_digest": C2B3D_BASIS["review_safe_evidence_digest"],
            "qualified_remote_host_readiness_ref": readiness_ref,
            "qualified_remote_host_readiness_digest": readiness_digest,
            "planning_context_captured_at": planning_context_captured_at,
        },
        domain=DIGEST_DOMAINS["pre_execution_context"],
        digest_field="planning_context_digest",
    )

    artifact_binding = _sealed(
        {
            "schema_id": SCHEMA_IDS["artifact_binding"],
            "artifact_ref": artifact_ref,
            "proposal_phase": "pre_execution_plan",
            "artifact_schema_id": SCHEMA_IDS["pre_execution_artifact"],
            "artifact_digest": private_plan_artifact["artifact_digest"],
            "artifact_canonical_byte_length": len(_canonical_bytes(private_plan_artifact)),
            "safe_projection_schema_id": SCHEMA_IDS["pre_execution_projection"],
            "safe_projection_digest": safe_projection["safe_projection_digest"],
            "privacy_classification": "private_normalized_model_proposal",
            "artifact_validated_at": source_invocation_completed_at,
        },
        domain=DIGEST_DOMAINS["artifact_binding"],
        digest_field="artifact_binding_digest",
    )

    source_invocation = _sealed(
        {
            "schema_id": SCHEMA_IDS["source_invocation"],
            "source_invocation_ref": f"source-invocation.model.{variant}.0001",
            "proposal_phase": "pre_execution_plan",
            "model_contract_ref": safe_model_configuration["model_contract_ref"],
            "model_contract_digest": safe_model_configuration["model_contract_digest"],
            "model_configuration_ref": safe_model_configuration["model_configuration_ref"],
            "model_configuration_digest": safe_model_configuration["model_configuration_digest"],
            "context_schema_id": SCHEMA_IDS["pre_execution_context"],
            "context_ref": planning_context_ref,
            "context_digest": planning_context["planning_context_digest"],
            "artifact_schema_id": SCHEMA_IDS["pre_execution_artifact"],
            "artifact_ref": artifact_ref,
            "artifact_digest": private_plan_artifact["artifact_digest"],
            "invocation_status": "normalized_typed_proposal_supplied",
            "source_invocation_started_at": source_invocation_started_at,
            "source_invocation_completed_at": source_invocation_completed_at,
        },
        domain=DIGEST_DOMAINS["source_invocation"],
        digest_field="source_invocation_digest",
    )

    evidence_sources = {
        "standing_policy": (planning_context["standing_policy_ref"], planning_context["standing_policy_digest"]),
        "risk_lane": (planning_context["risk_lane_ref"], planning_context["risk_lane_digest"]),
        "repository_binding": ("repository-binding.safe.0001", "3131313131313131313131313131313131313131313131313131313131313131"),
        "base_binding": ("base-git-object.0001", "3232323232323232323232323232323232323232323232323232323232323232"),
        "authorized_path_scope": ("path-scope.0001", planning_context["authorized_path_scope_digest"]),
        "cost_ceiling": (planning_context["cost_ceiling_ref"], planning_context["cost_ceiling_digest"]),
        "token_ceiling": (planning_context["token_ceiling_ref"], planning_context["token_ceiling_digest"]),
        "time_ceiling": (planning_context["time_ceiling_ref"], planning_context["time_ceiling_digest"]),
        "delivery_ceiling": (planning_context["delivery_ceiling_ref"], planning_context["delivery_ceiling_digest"]),
        "effect_ceiling": (planning_context["effect_ceiling_ref"], planning_context["effect_ceiling_digest"]),
        "authority_currentness_attestation": (authority_attestation["authority_attestation_ref"], authority_attestation["authority_attestation_digest"]),
        "global_stop": ("coding-global-stop-binding.0001", "3434343434343434343434343434343434343434343434343434343434343434"),
        "validation_requirement": (planning_context["validation_requirement_ref"], planning_context["validation_requirement_digest"]),
        "review_requirement": (planning_context["review_requirement_ref"], planning_context["review_requirement_digest"]),
        "qualified_remote_host_readiness": (readiness_ref, readiness_digest),
    }
    evidence_rows = tuple(
        _sealed(
            {
                "schema_id": SCHEMA_IDS["evidence_binding"],
                "proposal_ref": proposal_ref,
                "proposal_phase": "pre_execution_plan",
                "evidence_set_ref": evidence_set_ref,
                "evidence_role": role,
                "role_rank": rank,
                "ordinal": 0,
                "evidence_ref": evidence_sources[role][0],
                "evidence_digest": evidence_sources[role][1],
                "required_for_selection": 1 if required else 0,
                "evidence_bound_at": proposal_created_at,
            },
            domain=DIGEST_DOMAINS["evidence_binding"],
            digest_field="evidence_binding_digest",
        )
        for role, rank, required in PRE_EXECUTION_EVIDENCE_ROLES
        if required or readiness_present
    )
    if readiness_present:
        mutable_rows = list(evidence_rows)
        readiness_index = next(
            index
            for index, row in enumerate(mutable_rows)
            if row["evidence_role"] == "qualified_remote_host_readiness"
        )
        readiness_identity = _without(
            mutable_rows[readiness_index], "evidence_binding_digest"
        )
        readiness_identity["evidence_ref"] = readiness_ref
        readiness_identity["evidence_digest"] = readiness_digest
        mutable_rows[readiness_index] = _sealed(
            readiness_identity,
            domain=DIGEST_DOMAINS["evidence_binding"],
            digest_field="evidence_binding_digest",
        )
        evidence_rows = tuple(mutable_rows)
    evidence_set_identity = {
        "evidence_set_ref": evidence_set_ref,
        "proposal_ref": proposal_ref,
        "proposal_phase": "pre_execution_plan",
        "entries": tuple(
            {
                "evidence_role": row["evidence_role"],
                "role_rank": row["role_rank"],
                "ordinal": row["ordinal"],
                "evidence_ref": row["evidence_ref"],
                "evidence_digest": row["evidence_digest"],
                "evidence_binding_digest": row["evidence_binding_digest"],
            }
            for row in evidence_rows
        ),
    }
    evidence_set = {
        **evidence_set_identity,
        "evidence_set_digest": _domain_digest(DIGEST_DOMAINS["evidence_set"], evidence_set_identity),
    }

    proposal = _sealed(
        {
            "schema_id": SCHEMA_IDS["proposal"],
            "proposal_ref": proposal_ref,
            "proposal_phase": "pre_execution_plan",
            "source_invocation_ref": source_invocation["source_invocation_ref"],
            "source_invocation_digest": source_invocation["source_invocation_digest"],
            "model_contract_ref": safe_model_configuration["model_contract_ref"],
            "model_contract_digest": safe_model_configuration["model_contract_digest"],
            "model_configuration_ref": safe_model_configuration["model_configuration_ref"],
            "model_configuration_digest": safe_model_configuration["model_configuration_digest"],
            "context_schema_id": SCHEMA_IDS["pre_execution_context"],
            "context_ref": planning_context_ref,
            "context_digest": planning_context["planning_context_digest"],
            "artifact_schema_id": SCHEMA_IDS["pre_execution_artifact"],
            "artifact_ref": artifact_ref,
            "artifact_digest": private_plan_artifact["artifact_digest"],
            "safe_projection_schema_id": SCHEMA_IDS["pre_execution_projection"],
            "safe_projection_digest": safe_projection["safe_projection_digest"],
            "recommendation": "select_for_dispatch_gates",
            "reason_code": "plan.bounded_contract_change",
            "evidence_set_ref": evidence_set_ref,
            "evidence_set_digest": evidence_set["evidence_set_digest"],
            "proposal_created_at": proposal_created_at,
        },
        domain=DIGEST_DOMAINS["proposal"],
        digest_field="proposal_digest",
    )

    selection_key = {
        "program_ref": planning_context["program_ref"],
        "semantic_attempt_ref": planning_context["semantic_attempt_ref"],
        "candidate_ref": planning_context["candidate_ref"],
        "effect_intent_ref": planning_context["effect_intent_ref"],
        "author_command_ref": planning_context["author_command_ref"],
        "attempt_fence_ref": planning_context["attempt_fence_ref"],
        "effect_fence_ref": planning_context["effect_fence_ref"],
        "delivery_attempt_ref": planning_context["delivery_attempt_ref"],
    }
    selection_preimage = {
        "state": "absent",
        "selection_key": selection_key,
        "expected_current_selection_revision": None,
        "expected_current_selection_head_digest": None,
    }
    selection_preimage_digest = _domain_digest(
        DIGEST_DOMAINS["selection_preimage"], selection_preimage
    )
    selection_head = _sealed(
        {
            "schema_id": SCHEMA_IDS["selection_head"],
            "program_ref": planning_context["program_ref"],
            "program_version_ref": planning_context["program_version_ref"],
            "accepted_intent_revision_ref": planning_context["accepted_intent_revision_ref"],
            "work_item_ref": planning_context["work_item_ref"],
            "work_item_revision_ref": planning_context["work_item_revision_ref"],
            "semantic_attempt_ref": planning_context["semantic_attempt_ref"],
            "candidate_ref": planning_context["candidate_ref"],
            "effect_intent_ref": planning_context["effect_intent_ref"],
            "author_command_ref": planning_context["author_command_ref"],
            "author_command_digest": planning_context["author_command_digest"],
            "attempt_fence_ref": planning_context["attempt_fence_ref"],
            "attempt_fence_digest": planning_context["attempt_fence_digest"],
            "effect_fence_ref": planning_context["effect_fence_ref"],
            "effect_fence_digest": planning_context["effect_fence_digest"],
            "delivery_attempt_ref": planning_context["delivery_attempt_ref"],
            "delivery_envelope_digest": planning_context["delivery_envelope_digest"],
            "current_proposal_ref": proposal_ref,
            "current_disposition_ref": disposition_ref,
            "current_disposition": "selected_for_dispatch_gates",
            "head_revision": 0,
            "updated_at": coordinator_disposition_decided_at,
        },
        domain=DIGEST_DOMAINS["selection_head"],
        digest_field="head_digest",
    )
    disposition = _sealed(
        {
            "schema_id": SCHEMA_IDS["disposition"],
            "disposition_ref": disposition_ref,
            "program_ref": planning_context["program_ref"],
            "program_version_ref": planning_context["program_version_ref"],
            "accepted_intent_revision_ref": planning_context["accepted_intent_revision_ref"],
            "work_item_ref": planning_context["work_item_ref"],
            "work_item_revision_ref": planning_context["work_item_revision_ref"],
            "proposal_ref": proposal_ref,
            "proposal_digest": proposal["proposal_digest"],
            "planning_context_ref": planning_context_ref,
            "planning_context_digest": planning_context["planning_context_digest"],
            "evidence_set_ref": evidence_set_ref,
            "evidence_set_digest": evidence_set["evidence_set_digest"],
            "semantic_attempt_ref": planning_context["semantic_attempt_ref"],
            "candidate_ref": planning_context["candidate_ref"],
            "effect_intent_ref": planning_context["effect_intent_ref"],
            "author_command_ref": planning_context["author_command_ref"],
            "author_command_digest": planning_context["author_command_digest"],
            "attempt_fence_ref": planning_context["attempt_fence_ref"],
            "attempt_fence_digest": planning_context["attempt_fence_digest"],
            "effect_fence_ref": planning_context["effect_fence_ref"],
            "effect_fence_digest": planning_context["effect_fence_digest"],
            "delivery_attempt_ref": planning_context["delivery_attempt_ref"],
            "delivery_envelope_digest": planning_context["delivery_envelope_digest"],
            "disposition": "selected_for_dispatch_gates",
            "reason_code": "selection.policy_bounds_satisfied",
            "supersedes_disposition_ref": None,
            "expected_selection_head_revision": None,
            "expected_selection_head_digest": None,
            "resulting_selection_head_revision": 0,
            "selection_head_postimage_digest": selection_head["head_digest"],
            "coordinator_disposition_decided_at": coordinator_disposition_decided_at,
        },
        domain=DIGEST_DOMAINS["disposition"],
        digest_field="disposition_digest",
    )

    safe_command = _sealed(
        {
            "schema_id": SCHEMA_IDS["safe_command"],
            "mutation_ref": f"cognitive-mutation.{variant}.0001",
            "proposal_ref": proposal_ref,
            "proposal_digest": proposal["proposal_digest"],
            "source_invocation_ref": source_invocation["source_invocation_ref"],
            "source_invocation_digest": source_invocation["source_invocation_digest"],
            "artifact_ref": artifact_ref,
            "artifact_digest": private_plan_artifact["artifact_digest"],
            "artifact_binding_digest": artifact_binding["artifact_binding_digest"],
            "planning_context_ref": planning_context_ref,
            "planning_context_digest": planning_context["planning_context_digest"],
            "safe_projection_digest": safe_projection["safe_projection_digest"],
            "evidence_set_ref": evidence_set_ref,
            "evidence_set_digest": evidence_set["evidence_set_digest"],
            "preassigned_disposition_ref": disposition_ref,
            "expected_current_selection_revision": None,
            "expected_current_selection_head_digest": None,
            "disposition": "selected_for_dispatch_gates",
            "disposition_reason_code": "selection.policy_bounds_satisfied",
            "supersedes_disposition_ref": None,
            "program_ref": planning_context["program_ref"],
            "semantic_attempt_ref": planning_context["semantic_attempt_ref"],
            "candidate_ref": planning_context["candidate_ref"],
            "effect_intent_ref": planning_context["effect_intent_ref"],
            "author_command_ref": planning_context["author_command_ref"],
            "author_command_digest": planning_context["author_command_digest"],
            "attempt_fence_ref": planning_context["attempt_fence_ref"],
            "attempt_fence_digest": planning_context["attempt_fence_digest"],
            "effect_fence_ref": planning_context["effect_fence_ref"],
            "effect_fence_digest": planning_context["effect_fence_digest"],
            "delivery_attempt_ref": planning_context["delivery_attempt_ref"],
            "delivery_envelope_digest": planning_context["delivery_envelope_digest"],
        },
        domain=DIGEST_DOMAINS["safe_command"],
        digest_field="mutation_command_digest",
    )

    graph_entries = (
        {"role": "source_invocation", "rank": 0, "ordinal": 0, "record_ref": source_invocation["source_invocation_ref"], "record_digest": source_invocation["source_invocation_digest"]},
        {"role": "planning_context", "rank": 1, "ordinal": 0, "record_ref": planning_context_ref, "record_digest": planning_context["planning_context_digest"]},
        {"role": "private_artifact_binding", "rank": 2, "ordinal": 0, "record_ref": artifact_ref, "record_digest": artifact_binding["artifact_binding_digest"]},
        {"role": "model_proposal", "rank": 3, "ordinal": 0, "record_ref": proposal_ref, "record_digest": proposal["proposal_digest"]},
        {"role": "pre_execution_plan_projection", "rank": 4, "ordinal": 0, "record_ref": proposal_ref, "record_digest": safe_projection["safe_projection_digest"]},
        *(
            {"role": f"evidence.{row['evidence_role']}", "rank": row["role_rank"], "ordinal": 0, "record_ref": row["evidence_ref"], "record_digest": row["evidence_binding_digest"]}
            for row in evidence_rows
        ),
        {"role": "coordinator_disposition", "rank": 20, "ordinal": 0, "record_ref": disposition_ref, "record_digest": disposition["disposition_digest"]},
        {"role": "selection_head_postimage", "rank": 21, "ordinal": 0, "record_ref": planning_context["effect_intent_ref"], "record_digest": selection_head["head_digest"]},
    )
    graph_identity = {
        "mutation_ref": safe_command["mutation_ref"],
        "mutation_family": "record_pre_execution_plan_disposition",
        "command_digest": safe_command["mutation_command_digest"],
        "entries": graph_entries,
    }
    mutation_graph = {
        **graph_identity,
        "mutation_graph_digest": _domain_digest(DIGEST_DOMAINS["mutation_graph"], graph_identity),
    }
    result = _sealed(
        {
            "schema_id": SCHEMA_IDS["result"],
            "mutation_ref": safe_command["mutation_ref"],
            "proposal_ref": proposal_ref,
            "disposition_ref": disposition_ref,
            "disposition": "selected_for_dispatch_gates",
            "program_ref": planning_context["program_ref"],
            "semantic_attempt_ref": planning_context["semantic_attempt_ref"],
            "candidate_ref": planning_context["candidate_ref"],
            "effect_intent_ref": planning_context["effect_intent_ref"],
            "selection_head_revision": 0,
            "selection_head_digest": selection_head["head_digest"],
            "recorded_at": coordinator_disposition_decided_at,
        },
        domain=DIGEST_DOMAINS["result"],
        digest_field="result_projection_digest",
    )
    receipt = _sealed(
        {
            "schema_id": SCHEMA_IDS["receipt"],
            "mutation_ref": safe_command["mutation_ref"],
            "mutation_family": "record_pre_execution_plan_disposition",
            "command_schema_id": SCHEMA_IDS["safe_command"],
            "command_digest": safe_command["mutation_command_digest"],
            "program_ref": planning_context["program_ref"],
            "proposal_ref": proposal_ref,
            "disposition_ref": disposition_ref,
            "effect_intent_ref": planning_context["effect_intent_ref"],
            "selection_head_revision": 0,
            "selection_head_digest": selection_head["head_digest"],
            "result_class": "pre_execution_plan_disposition_recorded",
            "result_projection_digest": result["result_projection_digest"],
            "mutation_graph_digest": mutation_graph["mutation_graph_digest"],
            "outcome": "committed",
            "committed_at": coordinator_disposition_decided_at,
        },
        domain=DIGEST_DOMAINS["receipt"],
        digest_field="receipt_digest",
    )

    rows_by_table = {
        "development_model_source_invocations": (source_invocation,),
        "development_pre_execution_planning_contexts": (planning_context,),
        "development_private_proposal_artifact_bindings": (artifact_binding,),
        "development_model_proposals": (proposal,),
        "development_pre_execution_plan_projections": (safe_projection,),
        "development_model_proposal_evidence_bindings": evidence_rows,
        "development_pre_execution_dispositions": (disposition,),
        "development_pre_execution_selection_heads": (selection_head,),
        "development_cognitive_mutation_receipts": (receipt,),
    }
    row_write_order = (
        ("development_model_source_invocations", source_invocation),
        ("development_pre_execution_planning_contexts", planning_context),
        ("development_private_proposal_artifact_bindings", artifact_binding),
        ("development_model_proposals", proposal),
        ("development_pre_execution_plan_projections", safe_projection),
        *(("development_model_proposal_evidence_bindings", row) for row in evidence_rows),
        ("development_pre_execution_dispositions", disposition),
        ("development_pre_execution_selection_heads", selection_head),
        ("development_cognitive_mutation_receipts", receipt),
    )
    row_digest_contracts = {
        "development_model_source_invocations": (DIGEST_DOMAINS["source_invocation"], "source_invocation_digest"),
        "development_pre_execution_planning_contexts": (DIGEST_DOMAINS["pre_execution_context"], "planning_context_digest"),
        "development_private_proposal_artifact_bindings": (DIGEST_DOMAINS["artifact_binding"], "artifact_binding_digest"),
        "development_model_proposals": (DIGEST_DOMAINS["proposal"], "proposal_digest"),
        "development_pre_execution_plan_projections": (DIGEST_DOMAINS["pre_execution_projection"], "safe_projection_digest"),
        "development_model_proposal_evidence_bindings": (DIGEST_DOMAINS["evidence_binding"], "evidence_binding_digest"),
        "development_pre_execution_dispositions": (DIGEST_DOMAINS["disposition"], "disposition_digest"),
        "development_pre_execution_selection_heads": (DIGEST_DOMAINS["selection_head"], "head_digest"),
        "development_cognitive_mutation_receipts": (DIGEST_DOMAINS["receipt"], "receipt_digest"),
    }
    table_ordinals: dict[str, int] = {}
    row_canonical_records = []
    for table, row in row_write_order:
        ordinal = table_ordinals.get(table, 0)
        table_ordinals[table] = ordinal + 1
        domain, digest_field = row_digest_contracts[table]
        row_canonical_records.append(
            _record(
                f"{table}[{ordinal}]",
                row,
                domain=domain,
                semantic_digest=row[digest_field],
            )
        )

    canonical_records = (
        _record("safe_model_configuration", safe_model_configuration, domain=DIGEST_DOMAINS["safe_model_configuration"], semantic_digest=safe_model_configuration["model_configuration_digest"]),
        _record("authority_currentness_attestation", authority_attestation, domain=DIGEST_DOMAINS["authority_attestation"], semantic_digest=authority_attestation["authority_attestation_digest"]),
        _record("private_plan_artifact", private_plan_artifact, domain=DIGEST_DOMAINS["pre_execution_artifact"], semantic_digest=private_plan_artifact["artifact_digest"]),
        _record("safe_projection", safe_projection, domain=DIGEST_DOMAINS["pre_execution_projection"], semantic_digest=safe_projection["safe_projection_digest"]),
        _record("planning_context", planning_context, domain=DIGEST_DOMAINS["pre_execution_context"], semantic_digest=planning_context["planning_context_digest"]),
        _record("private_artifact_binding", artifact_binding, domain=DIGEST_DOMAINS["artifact_binding"], semantic_digest=artifact_binding["artifact_binding_digest"]),
        _record("source_invocation", source_invocation, domain=DIGEST_DOMAINS["source_invocation"], semantic_digest=source_invocation["source_invocation_digest"]),
        _record("evidence_set", evidence_set, domain=DIGEST_DOMAINS["evidence_set"], semantic_digest=evidence_set["evidence_set_digest"]),
        _record("model_proposal", proposal, domain=DIGEST_DOMAINS["proposal"], semantic_digest=proposal["proposal_digest"]),
        _record("selection_preimage", selection_preimage, domain=DIGEST_DOMAINS["selection_preimage"], semantic_digest=selection_preimage_digest),
        _record("selection_postimage", selection_head, domain=DIGEST_DOMAINS["selection_head"], semantic_digest=selection_head["head_digest"]),
        _record("coordinator_disposition", disposition, domain=DIGEST_DOMAINS["disposition"], semantic_digest=disposition["disposition_digest"]),
        _record("safe_command", safe_command, domain=DIGEST_DOMAINS["safe_command"], semantic_digest=safe_command["mutation_command_digest"]),
        _record("mutation_graph", mutation_graph, domain=DIGEST_DOMAINS["mutation_graph"], semantic_digest=mutation_graph["mutation_graph_digest"]),
        _record("fresh_result", result, domain=DIGEST_DOMAINS["result"], semantic_digest=result["result_projection_digest"]),
        _record("receipt", receipt, domain=DIGEST_DOMAINS["receipt"], semantic_digest=receipt["receipt_digest"]),
    )
    return {
        "vector_id": f"coordinator-cognitive-proposal-selection-{variant}-golden-v2",
        "canonicalization_profile": "canonical-json.sorted-keys.utf8.v1",
        "planning_context_captured_at": planning_context_captured_at,
        "source_invocation_started_at": source_invocation_started_at,
        "source_invocation_completed_at": source_invocation_completed_at,
        "proposal_created_at": proposal_created_at,
        "coordinator_disposition_decided_at": coordinator_disposition_decided_at,
        "c2b3d_committed_at": C2B3D_BASIS["committed_at"],
        "attempt_fence_expires_at": C2B3D_BASIS["attempt_fence_expires_at"],
        "effect_fence_expires_at": C2B3D_BASIS["effect_fence_expires_at"],
        "authority_attestation": authority_attestation,
        "readiness_present": readiness_present,
        "physical_row_count": len(row_write_order),
        "supplied_graph_member_count": len(graph_entries),
        "safe_model_configuration": safe_model_configuration,
        "private_plan_artifact": private_plan_artifact,
        "component_digests": component_digests,
        "source_invocation": source_invocation,
        "private_artifact_binding": artifact_binding,
        "planning_context": planning_context,
        "evidence_set": evidence_set,
        "pre_execution_proposal": proposal,
        "safe_projection": safe_projection,
        "coordinator_disposition": disposition,
        "current_selection_preimage": selection_preimage,
        "current_selection_preimage_digest": selection_preimage_digest,
        "current_selection_postimage": selection_head,
        "safe_mutation_command": safe_command,
        "migration_0003_rows_by_table": rows_by_table,
        "physical_row_write_order": row_write_order,
        "row_canonical_records": tuple(row_canonical_records),
        "supplied_graph": mutation_graph,
        "receipt": receipt,
        "fresh_result": result,
        "exact_replay_result": deepcopy(result),
        "conflict_examples": (
            {"case": "same_mutation_ref_different_command_digest", "classification": "mutation_ref_reuse_conflict", "new_disposition": False, "writes": 0},
            {"case": "stale_current_selection_revision_or_digest", "classification": "selection_head_version_conflict", "new_disposition": False, "writes": 0},
            {"case": "foreign_or_changed_C2B3D_lineage", "classification": "planning_relation_conflict", "new_disposition": False, "writes": 0},
            {"case": "selected_with_expired_authority", "classification": "planning_selection_not_permitted", "new_disposition": False, "writes": 0},
            {"case": "malformed_or_raw_provider_material", "classification": "preflight_rejected", "new_disposition": False, "writes": 0},
            {"case": "commit_attempt_exception", "classification": "commit_outcome_unknown", "automatic_semantic_retry": False},
        ),
        "compound_conflict_examples": (
            {"case": "stale_selection_plus_active_stop", "true_conditions": ("current_selection_head_conflict", "active_coding_global_stop"), "classification": "planning_selection_not_permitted"},
            {"case": "stale_selection_plus_expired_authority", "true_conditions": ("current_selection_head_conflict", "authority_attestation_invalid"), "classification": "selection_head_version_conflict"},
            {"case": "active_stop_plus_expired_authority", "true_conditions": ("active_coding_global_stop", "authority_attestation_invalid"), "classification": "planning_selection_not_permitted"},
            {"case": "stale_context_plus_semantic_collision", "true_conditions": ("planning_context_or_C2B3D_relation_conflict", "proposal_or_disposition_semantic_identity_collision"), "classification": "planning_relation_conflict"},
            {"case": "receipt_replay_plus_later_invalid_current_policy", "true_conditions": ("exact_replay", "policy_risk_resource_path_cost_token_time_delivery_or_effect_bounds"), "classification": "exact_replay"},
            {"case": "mutation_ref_reuse_plus_active_stop", "true_conditions": ("mutation_ref_reuse", "active_coding_global_stop"), "classification": "mutation_ref_reuse_conflict"},
        ),
        "recovery_classifications": (
            {"case": "current_head_exactly_receipt_postimage", "classification": "committed_exact"},
            {"case": "one_exact_later_successor_reaches_receipt_postimage", "classification": "committed_exact"},
            {"case": "all_preassigned_identities_absent_and_preimage_unchanged", "classification": "definitely_not_committed"},
            {"case": "missing_malformed_duplicate_cyclic_overlimit_wrong_lineage_or_disconnected", "classification": "unresolved"},
        ),
        "canonical_records": canonical_records,
        "privacy": {
            "host_readiness_evidence_present": readiness_present,
            "authority_state": "pending",
            "raw_prompt_present": False,
            "raw_response_present": False,
            "provider_session_present": False,
            "credential_or_endpoint_present": False,
            "private_plan_text_in_SQLite_rows": False,
            "absolute_path_present": False,
            "retrieval_authority_present": False,
        },
    }


EXPECTED_GOLDEN_VECTORS = {
    "readiness_absent": _build_golden_vector(False),
    "readiness_present": _build_golden_vector(True),
}

# Measured from the separately written Section-41 owner bytes. These values are
# not derived at test runtime.
EXPECTED_SECTION_41_UTF8_LENGTH = 522_877
EXPECTED_SECTION_41_SHA256 = (
    "1198a3f56554cc6659572686669a95a62c04cd5789a149b4655d68fbf870c350"
)


def _assert_exact(actual: object, expected: object, message: str) -> None:
    assert type(actual) is type(expected), message
    if type(expected) is dict:
        assert tuple(actual) == tuple(expected), message
        for key in expected:
            _assert_exact(actual[key], expected[key], message)
        return
    if type(expected) is tuple:
        assert len(actual) == len(expected), message
        for actual_item, expected_item in zip(actual, expected, strict=True):
            _assert_exact(actual_item, expected_item, message)
        return
    assert actual == expected, message


def _read_owner_bytes() -> bytes:
    assert not OWNER_PATH.is_symlink()
    assert OWNER_PATH.resolve(strict=True) == OWNER_PATH
    return OWNER_PATH.read_bytes()


def _section_41_bytes(
    source: bytes | None = None, *, enforce_frozen_bytes: bool = True
) -> tuple[bytes, bytes]:
    owner = _read_owner_bytes() if source is None else source
    assert type(owner) is bytes
    boundary = ("\n" + SECTION_HEADING).encode("utf-8")
    assert owner.count(boundary) == 1, "COGNITIVE_SECTION_BOUNDARY_INVALID"
    prefix, section_without_leading_newline = owner.split(boundary, 1)
    section = SECTION_HEADING.encode("utf-8") + section_without_leading_newline
    assert len(prefix) == EXPECTED_SECTIONS_1_40_UTF8_LENGTH
    assert hashlib.sha256(prefix).hexdigest() == EXPECTED_SECTIONS_1_40_SHA256
    if enforce_frozen_bytes:
        assert len(section) == EXPECTED_SECTION_41_UTF8_LENGTH
        assert hashlib.sha256(section).hexdigest() == EXPECTED_SECTION_41_SHA256
    assert section.startswith(OPENING.encode("utf-8"))
    assert section.count(CLOSING.encode("utf-8")) == 1
    assert section.count(BEGIN_MARKER.encode("utf-8")) == 1
    assert section.count(END_MARKER.encode("utf-8")) == 1
    assert section.count(REPAIRED_BEGIN_MARKER.encode("utf-8")) == 1
    assert section.count(REPAIRED_END_MARKER.encode("utf-8")) == 1
    assert section.count(REAUDIT_REPAIR_BEGIN_MARKER.encode("utf-8")) == 1
    assert section.count(REAUDIT_REPAIR_END_MARKER.encode("utf-8")) == 1
    assert section.count(A2_REVISED_REPAIR_BEGIN_MARKER.encode("utf-8")) == 1
    assert section.count(A2_REVISED_REPAIR_END_MARKER.encode("utf-8")) == 1
    return prefix, section


def _assert_literal_ast_is_closed(expression: ast.Expression) -> None:
    for node in ast.walk(expression):
        if type(node) is ast.Dict:
            keys = []
            for key_node in node.keys:
                assert type(key_node) is ast.Constant
                assert type(key_node.value) is str
                keys.append(key_node.value)
            assert len(keys) == len(set(keys)), "COGNITIVE_OWNER_DUPLICATE_FIELD"


def _parse_owner_literal(
    source: bytes | None = None,
    *,
    enforce_frozen_bytes: bool = True,
    compare_expected: bool = True,
) -> dict[str, object]:
    _prefix, section = _section_41_bytes(
        source, enforce_frozen_bytes=enforce_frozen_bytes
    )
    opening = OPENING.encode("utf-8")
    closing = CLOSING.encode("utf-8")
    legacy_end = section.index(closing) + len(closing)
    legacy_section = section[:legacy_end]
    payload = legacy_section[len(opening) : -len(closing)]
    assert b"\r" not in payload, "COGNITIVE_OWNER_LITERAL_INVALID"
    try:
        decoded_payload = payload.decode("utf-8", errors="strict")
        tokens = tokenize.generate_tokens(io.StringIO(decoded_payload).readline)
        assert all(token.type != tokenize.COMMENT for token in tokens)
        expression = ast.parse(decoded_payload, mode="eval")
        assert type(expression) is ast.Expression
        _assert_literal_ast_is_closed(expression)
        value = ast.literal_eval(expression)
    except (AssertionError, IndentationError, SyntaxError, tokenize.TokenError, UnicodeDecodeError, TypeError, ValueError):
        raise AssertionError("COGNITIVE_OWNER_LITERAL_INVALID") from None
    assert type(value) is dict, "COGNITIVE_OWNER_LITERAL_INVALID"
    assert tuple(value) == (
        "coordinator_cognitive_proposal_selection_contract",
        "golden_vectors",
    ), "COGNITIVE_OWNER_LITERAL_INVALID"
    _assert_closed_value(value)
    if compare_expected:
        _assert_exact(
            value["coordinator_cognitive_proposal_selection_contract"],
            EXPECTED_CONTRACT,
            "COGNITIVE_CONTRACT_INVALID",
        )
        _assert_exact(
            value["golden_vectors"],
            EXPECTED_GOLDEN_VECTORS,
            "COGNITIVE_VECTOR_INVALID",
        )
    return value


def _assert_self_digest(row: dict[str, object], domain: str, field: str) -> None:
    assert tuple(row)[-1] == field
    assert row[field] == _independent_domain_digest(domain, _without(row, field))


def _assert_narrative(value: object, maximum_utf8_bytes: int = 512) -> None:
    assert type(value) is str, "PRIVATE_PLAN_NARRATIVE_INVALID"
    encoded = value.encode("utf-8", errors="strict")
    assert 1 <= len(encoded) <= maximum_utf8_bytes, "PRIVATE_PLAN_NARRATIVE_INVALID"
    assert value == value.strip(), "PRIVATE_PLAN_NARRATIVE_INVALID"
    assert unicodedata.normalize("NFC", value) == value, "PRIVATE_PLAN_NARRATIVE_INVALID"
    assert any(unicodedata.category(character)[0] in ("L", "N") for character in value), "PRIVATE_PLAN_NARRATIVE_INVALID"
    assert all(unicodedata.category(character) != "Cc" for character in value), "PRIVATE_PLAN_NARRATIVE_INVALID"
    assert value.casefold() not in {"tbd", "todo", "n/a", "none", "unknown", "placeholder", "..."}, "PRIVATE_PLAN_NARRATIVE_INVALID"


def _assert_safe_ref(value: object) -> None:
    assert type(value) is str and re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z.-]{0,95}", value)
    assert not value.casefold().startswith(("connector-", "tunnel-", "workspace-", "org-", "organization-", "user-"))


def _assert_exact_tuple(value: object) -> tuple[object, ...]:
    assert type(value) is tuple, "PRIVATE_PLAN_SEQUENCE_INVALID"
    return value


def _assert_private_plan_semantics(artifact: dict[str, object]) -> None:
    assert type(artifact) is dict and tuple(artifact) == PRIVATE_PLAN_FIELD_ORDER, "PRIVATE_PLAN_SHAPE_INVALID"
    assert artifact["schema_id"] == SCHEMA_IDS["pre_execution_artifact"]
    assert artifact["proposal_phase"] == "pre_execution_plan"
    strategies = _assert_exact_tuple(artifact["implementation_strategy"])
    assert 1 <= len(strategies) <= 8
    for statement in strategies:
        _assert_narrative(statement, NARRATIVE_BYTE_LIMITS["implementation_strategy_item"])

    paths = _assert_exact_tuple(artifact["affected_authorized_paths"])
    assert 1 <= len(paths) <= 64 and len(paths) == len(set(paths))
    authorized_order = C2B3D_BASIS["authorized_paths"]
    assert tuple(path for path in authorized_order if path in paths) == paths
    for path in paths:
        assert type(path) is str and path in authorized_order
        assert not path.startswith(("/", "\\")) and "\\" not in path and "\x00" not in path
        assert all(part not in ("", ".", "..") for part in path.split("/"))

    work_units = _assert_exact_tuple(artifact["proposed_work_units"])
    work_fields = (
        "ordinal", "work_unit_ref", "action_kind", "summary", "depends_on_work_unit_refs",
        "authorized_path_ordinals", "expected_output_refs", "validation_refs",
        "required_evidence_roles", "prerequisite_refs", "stop_condition_refs",
    )
    assert 1 <= len(work_units) <= 32
    work_refs = tuple(unit["work_unit_ref"] for unit in work_units)
    assert len(work_refs) == len(set(work_refs))
    for index, unit in enumerate(work_units):
        assert type(unit) is dict and tuple(unit) == work_fields
        assert type(unit["ordinal"]) is int and unit["ordinal"] == index
        _assert_safe_ref(unit["work_unit_ref"])
        assert unit["action_kind"] in (
            "analyze", "modify_authorized_path", "create_authorized_path", "delete_authorized_path",
            "run_validation", "review_evidence", "prepare_candidate",
        )
        _assert_narrative(unit["summary"], NARRATIVE_BYTE_LIMITS["work_unit_summary"])
        dependencies = _assert_exact_tuple(unit["depends_on_work_unit_refs"])
        assert len(dependencies) == len(set(dependencies)) and unit["work_unit_ref"] not in dependencies
        assert all(dependency in work_refs[:index] for dependency in dependencies)
        path_ordinals = _assert_exact_tuple(unit["authorized_path_ordinals"])
        assert path_ordinals and all(type(item) is int and 0 <= item < len(paths) for item in path_ordinals)
        assert tuple(sorted(set(path_ordinals))) == path_ordinals
        for field in ("expected_output_refs", "validation_refs", "required_evidence_roles", "prerequisite_refs", "stop_condition_refs"):
            values = _assert_exact_tuple(unit[field])
            assert values and len(values) == len(set(values))

    outputs = _assert_exact_tuple(artifact["expected_outputs"])
    assert 1 <= len(outputs) <= 32
    output_fields = ("output_ref", "owner_work_unit_ref", "output_kind", "description")
    output_by_ref = {}
    for output in outputs:
        assert type(output) is dict and tuple(output) == output_fields
        _assert_safe_ref(output["output_ref"])
        assert output["output_ref"] not in output_by_ref
        assert output["owner_work_unit_ref"] in work_refs
        assert output["output_kind"] in ("source_change", "test_change", "documentation_change", "candidate_manifest", "validation_evidence")
        _assert_narrative(output["description"], NARRATIVE_BYTE_LIMITS["output_description"])
        output_by_ref[output["output_ref"]] = output

    validations = _assert_exact_tuple(artifact["validation_strategy"])
    assert 1 <= len(validations) <= 32
    validation_fields = ("ordinal", "validation_ref", "work_unit_refs", "validation_kind", "target", "success_criterion")
    validation_by_ref = {}
    for index, validation in enumerate(validations):
        assert type(validation) is dict and tuple(validation) == validation_fields
        assert type(validation["ordinal"]) is int and validation["ordinal"] == index
        _assert_safe_ref(validation["validation_ref"])
        assert validation["validation_ref"] not in validation_by_ref
        covered = _assert_exact_tuple(validation["work_unit_refs"])
        assert covered and len(covered) == len(set(covered)) and all(ref in work_refs for ref in covered)
        assert validation["validation_kind"] in ("focused_test", "contract_test", "static_check", "build", "manual_review")
        _assert_narrative(validation["target"], NARRATIVE_BYTE_LIMITS["validation_target"])
        _assert_narrative(validation["success_criterion"], NARRATIVE_BYTE_LIMITS["validation_success_criterion"])
        validation_by_ref[validation["validation_ref"]] = validation

    assumptions = _assert_exact_tuple(artifact["material_assumptions"])
    assert 1 <= len(assumptions) <= 16
    seen_assumptions = set()
    for assumption in assumptions:
        assert type(assumption) is dict and tuple(assumption) == ("assumption_ref", "statement")
        _assert_safe_ref(assumption["assumption_ref"])
        assert assumption["assumption_ref"] not in seen_assumptions
        seen_assumptions.add(assumption["assumption_ref"])
        _assert_narrative(assumption["statement"], NARRATIVE_BYTE_LIMITS["assumption_statement"])

    risks = _assert_exact_tuple(artifact["risks_and_uncertainties"])
    assert 1 <= len(risks) <= 16
    risk_fields = ("risk_ref", "risk_kind", "description", "mitigation", "materiality", "affected_work_unit_refs")
    seen_risks = set()
    for risk in risks:
        assert type(risk) is dict and tuple(risk) == risk_fields
        _assert_safe_ref(risk["risk_ref"])
        assert risk["risk_ref"] not in seen_risks
        seen_risks.add(risk["risk_ref"])
        assert risk["risk_kind"] in ("correctness", "authority", "privacy", "compatibility", "operational", "unknown")
        assert risk["materiality"] in ("material", "blocking")
        _assert_narrative(risk["description"], NARRATIVE_BYTE_LIMITS["risk_description"])
        _assert_narrative(risk["mitigation"], NARRATIVE_BYTE_LIMITS["risk_mitigation"])
        affected = _assert_exact_tuple(risk["affected_work_unit_refs"])
        assert affected and len(affected) == len(set(affected)) and all(ref in work_refs for ref in affected)

    prerequisites = _assert_exact_tuple(artifact["required_evidence_and_prerequisites"])
    assert 1 <= len(prerequisites) <= 32
    prerequisite_by_ref = {}
    required_roles = {role for role, _rank, required in PRE_EXECUTION_EVIDENCE_ROLES if required}
    for prerequisite in prerequisites:
        assert type(prerequisite) is dict and tuple(prerequisite) == ("prerequisite_ref", "evidence_role", "requirement")
        _assert_safe_ref(prerequisite["prerequisite_ref"])
        assert prerequisite["prerequisite_ref"] not in prerequisite_by_ref
        assert prerequisite["evidence_role"] in required_roles
        _assert_narrative(prerequisite["requirement"], NARRATIVE_BYTE_LIMITS["prerequisite_requirement"])
        prerequisite_by_ref[prerequisite["prerequisite_ref"]] = prerequisite

    stops = _assert_exact_tuple(artifact["stop_or_replan_conditions"])
    assert 1 <= len(stops) <= 16
    stop_by_ref = {}
    for stop in stops:
        assert type(stop) is dict and tuple(stop) == ("stop_condition_ref", "statement")
        _assert_safe_ref(stop["stop_condition_ref"])
        assert stop["stop_condition_ref"] not in stop_by_ref
        _assert_narrative(stop["statement"], NARRATIVE_BYTE_LIMITS["stop_condition_statement"])
        stop_by_ref[stop["stop_condition_ref"]] = stop

    referenced_outputs = set()
    referenced_validations = set()
    referenced_prerequisites = set()
    referenced_stops = set()
    for unit in work_units:
        for ref in unit["expected_output_refs"]:
            assert ref in output_by_ref and output_by_ref[ref]["owner_work_unit_ref"] == unit["work_unit_ref"]
            referenced_outputs.add(ref)
        for ref in unit["validation_refs"]:
            assert ref in validation_by_ref and unit["work_unit_ref"] in validation_by_ref[ref]["work_unit_refs"]
            referenced_validations.add(ref)
        for ref in unit["prerequisite_refs"]:
            assert ref in prerequisite_by_ref
            referenced_prerequisites.add(ref)
        for ref in unit["stop_condition_refs"]:
            assert ref in stop_by_ref
            referenced_stops.add(ref)
        assert all(role in required_roles for role in unit["required_evidence_roles"])
    assert referenced_outputs == set(output_by_ref)
    assert referenced_validations == set(validation_by_ref)
    assert referenced_prerequisites == set(prerequisite_by_ref)
    assert referenced_stops == set(stop_by_ref)

    use = artifact["proposed_resource_and_effect_use"]
    expected_use_fields = EXPECTED_CONTRACT["pre_execution_private_plan_artifact"]["proposed_resource_and_effect_use"]["field_order"]
    assert type(use) is dict and tuple(use) == expected_use_fields
    effects = _assert_exact_tuple(use["allowed_effect_classes"])
    assert effects and all(type(effect) is str and effect in C2A_EFFECT_CLASSES for effect in effects)
    assert len(effects) == len(set(effects))
    assert tuple(effect for effect in C2A_EFFECT_CLASSES if effect in effects) == effects
    assert set(effects) <= set(C2B3D_BASIS["attempt_fence_allowed_effect_classes"])
    assert set(effects) <= set(C2B3D_BASIS["effect_fence_allowed_effect_classes"])
    for name, ceiling in C2B3D_BASIS["effect_ceilings"].items():
        assert type(use[name]) is int and 0 <= use[name] <= ceiling
    assert artifact["recommendation"] in PRE_EXECUTION_RECOMMENDATIONS
    assert type(artifact["reason_code"]) is str


def _assert_authority_selection_eligible(
    attestation: dict[str, object], decision_time: str
) -> None:
    assert type(attestation) is dict and tuple(attestation) == AUTHORITY_ATTESTATION_FIELD_ORDER
    _assert_self_digest(attestation, DIGEST_DOMAINS["authority_attestation"], "authority_attestation_digest")
    assert attestation["schema_id"] == SCHEMA_IDS["authority_attestation"]
    _assert_safe_ref(attestation["authority_attestation_ref"])
    _assert_safe_ref(attestation["source_authority_ref"])
    assert all(type(attestation[field]) is str and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", attestation[field]) for field in ("issued_at", "expires_at"))
    assert attestation["issued_at"] < attestation["expires_at"]
    assert attestation["authoritative_subject_kind"] == "effect_intent"
    assert attestation["authoritative_subject_ref"] == C2B3D_BASIS["effect_intent_ref"]
    assert attestation["authority_evaluation_ref"] == C2B3D_BASIS["authority_evaluation_ref"]
    assert attestation["authority_evaluation_digest"] == C2B3D_BASIS["authority_evaluation_digest"]
    assert type(attestation["authority_version"]) is int and attestation["authority_version"] == 1
    assert attestation["authority_state"] in ("pending", "verified")
    assert attestation["issued_at"] <= decision_time < attestation["expires_at"]
    assert decision_time < C2B3D_BASIS["attempt_fence_expires_at"]
    assert decision_time < C2B3D_BASIS["effect_fence_expires_at"]


def _assert_readiness_and_graph_semantics(vector: dict[str, object]) -> None:
    context = vector["planning_context"]
    readiness_values = (
        context["qualified_remote_host_readiness_ref"],
        context["qualified_remote_host_readiness_digest"],
    )
    assert all(value is None for value in readiness_values) or all(value is not None for value in readiness_values)
    present = all(value is not None for value in readiness_values)
    assert vector["readiness_present"] is present
    evidence_rows = vector["migration_0003_rows_by_table"]["development_model_proposal_evidence_bindings"]
    readiness_rows = tuple(row for row in evidence_rows if row["evidence_role"] == "qualified_remote_host_readiness")
    graph = vector["supplied_graph"]
    rank_19 = tuple(entry for entry in graph["entries"] if entry["rank"] == 19)
    assert len(readiness_rows) == (1 if present else 0)
    assert len(rank_19) == (1 if present else 0)
    if present:
        row = readiness_rows[0]
        member = rank_19[0]
        assert row["required_for_selection"] == 0 and row["ordinal"] == 0
        assert row["evidence_ref"] == readiness_values[0] and row["evidence_digest"] == readiness_values[1]
        assert (member["role"], member["rank"], member["ordinal"]) == ("evidence.qualified_remote_host_readiness", 19, 0)
        assert member["record_ref"] == row["evidence_ref"]
        assert member["record_digest"] == row["evidence_binding_digest"]
    assert tuple(entry["rank"] for entry in graph["entries"]) == ((*range(19), 19, 20, 21) if present else (*range(19), 20, 21))
    assert len(vector["physical_row_write_order"]) == (23 if present else 22)
    assert len(graph["entries"]) == (22 if present else 21)
    assert vector["physical_row_count"] == len(vector["physical_row_write_order"])
    assert vector["supplied_graph_member_count"] == len(graph["entries"])
    assert all(entry["role"] != "receipt" for entry in graph["entries"])

    owned = {
        ("source_invocation", 0): (vector["source_invocation"]["source_invocation_ref"], vector["source_invocation"]["source_invocation_digest"]),
        ("planning_context", 1): (vector["planning_context"]["planning_context_ref"], vector["planning_context"]["planning_context_digest"]),
        ("private_artifact_binding", 2): (vector["private_artifact_binding"]["artifact_ref"], vector["private_artifact_binding"]["artifact_binding_digest"]),
        ("model_proposal", 3): (vector["pre_execution_proposal"]["proposal_ref"], vector["pre_execution_proposal"]["proposal_digest"]),
        ("pre_execution_plan_projection", 4): (vector["safe_projection"]["proposal_ref"], vector["safe_projection"]["safe_projection_digest"]),
        ("coordinator_disposition", 20): (vector["coordinator_disposition"]["disposition_ref"], vector["coordinator_disposition"]["disposition_digest"]),
        ("selection_head_postimage", 21): (vector["current_selection_postimage"]["effect_intent_ref"], vector["current_selection_postimage"]["head_digest"]),
    }
    for row in evidence_rows:
        owned[(f"evidence.{row['evidence_role']}", row["role_rank"])] = (row["evidence_ref"], row["evidence_binding_digest"])
    assert len(owned) == len(graph["entries"])
    for member in graph["entries"]:
        assert member["ordinal"] == 0
        assert (member["record_ref"], member["record_digest"]) == owned[(member["role"], member["rank"])]
    assert graph["mutation_graph_digest"] == _independent_domain_digest(DIGEST_DOMAINS["mutation_graph"], _without(graph, "mutation_graph_digest"))


def _resolve_fresh_outcome(true_conditions: tuple[str, ...]) -> object | None:
    assert type(true_conditions) is tuple and len(true_conditions) == len(set(true_conditions))
    known = {entry["condition"] for entry in FRESH_APPLY_PRECEDENCE}
    assert all(type(condition) is str and condition in known for condition in true_conditions)
    for entry in FRESH_APPLY_PRECEDENCE:
        if entry["condition"] in true_conditions:
            return entry["outcome"]
    return None


def _classify_recovery_ancestry(
    *,
    lineage_key: dict[str, object],
    receipt_disposition_ref: str,
    receipt_head_revision: int,
    receipt_head_digest: str,
    current_disposition_ref: str,
    current_head_revision: int,
    current_head_digest: str,
    predecessor_rows: tuple[dict[str, object], ...],
) -> str:
    if (current_disposition_ref, current_head_revision, current_head_digest) == (
        receipt_disposition_ref, receipt_head_revision, receipt_head_digest
    ):
        return "committed_exact" if not predecessor_rows else "unresolved"
    by_ref: dict[str, dict[str, object]] = {}
    for row in predecessor_rows:
        if type(row) is not dict or tuple(row) != (
            "lineage_key", "disposition_ref", "prior_disposition_ref", "prior_head_revision",
            "prior_head_digest", "resulting_head_revision", "resulting_head_digest",
        ):
            return "unresolved"
        if row["disposition_ref"] in by_ref:
            return "unresolved"
        by_ref[row["disposition_ref"]] = row
    cursor = (current_disposition_ref, current_head_revision, current_head_digest)
    visited: set[str] = set()
    for read_number in range(1, 258):
        if cursor == (receipt_disposition_ref, receipt_head_revision, receipt_head_digest):
            return "committed_exact" if len(visited) == len(predecessor_rows) else "unresolved"
        row = by_ref.get(cursor[0])
        if row is None or read_number == 257 or cursor[0] in visited:
            return "unresolved"
        visited.add(cursor[0])
        if row["lineage_key"] != lineage_key:
            return "unresolved"
        if (row["resulting_head_revision"], row["resulting_head_digest"]) != cursor[1:]:
            return "unresolved"
        if type(row["prior_head_revision"]) is not int or row["prior_head_revision"] != row["resulting_head_revision"] - 1:
            return "unresolved"
        cursor = (row["prior_disposition_ref"], row["prior_head_revision"], row["prior_head_digest"])
    raise AssertionError("RECOVERY_WALK_UNREACHABLE")


def _section_39_vector() -> dict[str, object]:
    source = _read_owner_bytes()
    heading = C2B3D_SECTION_HEADING.encode("utf-8")
    begin = C2B3D_BEGIN_MARKER.encode("utf-8")
    end = C2B3D_END_MARKER.encode("utf-8")
    assert source.count(heading) == source.count(begin) == source.count(end) == 1
    section = source[source.index(heading) : source.index(end) + len(end)]
    opening_index = section.index(b"```python\n") + len(b"```python\n")
    closing_index = section.index(b"\n```\n", opening_index)
    expression = ast.parse(section[opening_index:closing_index].decode("utf-8", errors="strict"), mode="eval")
    assert type(expression) is ast.Expression
    _assert_literal_ast_is_closed(expression)
    owner = ast.literal_eval(expression)
    assert type(owner) is dict and tuple(owner) == ("coordinator_c2b3c_author_effect_contract",)
    contract = owner["coordinator_c2b3c_author_effect_contract"]
    assert type(contract) is dict
    vector = contract["family_golden_vector"]
    assert type(vector) is dict
    return vector


def _extract_c2b3d_basis(vector: dict[str, object]) -> dict[str, object]:
    inputs = vector["inputs"]
    genesis = inputs["committed_vs1b_genesis_basis"]
    refs = inputs["preassigned_author_effect_refs"]
    authority = inputs["standing_and_subordinate_authority"]
    requirements = inputs["requirement_evidence"]
    rows = vector["persisted_postimages"]
    return {
        "committed_at": vector["transaction_timestamp"],
        "program_ref": genesis["program_ref"],
        "program_version_ref": genesis["program_version_ref"],
        "program_version_number": genesis["program_version_number"],
        "accepted_intent_revision_ref": genesis["accepted_intent_revision_ref"],
        "work_item_ref": genesis["work_item_ref"],
        "work_item_revision_ref": genesis["work_item_revision_ref"],
        "basis_decision_ref": genesis["basis_decision_ref"],
        "basis_decision_digest": genesis["basis_decision_digest"],
        "semantic_attempt_ref": genesis["semantic_attempt_ref"],
        "semantic_attempt_digest": rows["semantic_attempt"]["semantic_attempt_digest"],
        "attempt_number": genesis["attempt_number"],
        "candidate_ref": genesis["candidate_ref"],
        "repository_ref": genesis["repository_ref"],
        "base_git_object_format": genesis["base_git_object_format"],
        "base_git_oid": genesis["base_git_oid"],
        "authorized_paths": genesis["authorized_paths"],
        "work_spec_ref": genesis["work_spec_ref"],
        "work_spec_digest": genesis["work_spec_digest"],
        "work_spec_safe_projection_digest": genesis["work_spec_safe_projection_digest"],
        "validation_requirement_ref": genesis["validation_requirement_ref"],
        "validation_requirement_digest": requirements["validation"]["requirement_digest"],
        "validation_safe_evidence_digest": requirements["validation"]["safe_evidence_digest"],
        "review_requirement_ref": genesis["review_requirement_ref"],
        "review_requirement_digest": requirements["review"]["requirement_digest"],
        "review_safe_evidence_digest": requirements["review"]["safe_evidence_digest"],
        "standing_grant_ref": authority["standing_grant_ref"],
        "standing_grant_digest": authority["standing_grant_digest"],
        "attempt_authorization_ref": authority["attempt_authorization_ref"],
        "attempt_authorization_digest": authority["attempt_authorization_digest"],
        "effect_authorization_ref": authority["effect_authorization_ref"],
        "effect_authorization_digest": authority["effect_authorization_digest"],
        "attempt_fence_ref": refs["attempt_fence_ref"],
        "attempt_fence_digest": rows["attempt_fence"]["attempt_fence_digest"],
        "attempt_fence_allowed_effect_classes": inputs["allowed_effect_classes"],
        "attempt_fence_expires_at": rows["attempt_fence"]["expires_at"],
        "effect_intent_ref": refs["effect_intent_ref"],
        "effect_intent_digest": rows["author_effect_intent"]["effect_intent_digest"],
        "effect_class": rows["author_effect_intent"]["effect_class"],
        "effect_fence_ref": refs["effect_fence_ref"],
        "effect_fence_digest": rows["author_effect_fence"]["effect_fence_digest"],
        "effect_fence_allowed_effect_classes": (rows["author_effect_fence"]["effect_class"],),
        "effect_fence_expires_at": rows["author_effect_fence"]["expires_at"],
        "author_command_ref": refs["command_ref"],
        "author_command_digest": rows["author_command"]["command_digest"],
        "authority_evaluation_ref": refs["authority_evaluation_ref"],
        "authority_evaluation_digest": rows["authority_evaluation"]["authority_evaluation_digest"],
        "authority_evaluation_state": rows["authority_evaluation"]["authority_state"],
        "coding_global_stop_ref": inputs["coding_global_stop"]["global_stop_ref"],
        "coding_global_stop_version": inputs["coding_global_stop"]["global_stop_version"],
        "delivery_attempt_ref": refs["delivery_attempt_ref"],
        "delivery_envelope_digest": rows["initial_delivery_attempt"]["delivery_envelope_digest"],
        "delivery_attempt_digest": rows["initial_delivery_attempt"]["delivery_attempt_digest"],
        "effect_head_revision": rows["effect_head_postimage"]["head_revision"],
        "effect_head_digest": rows["effect_head_postimage"]["head_digest"],
        "delivery_head_revision": rows["delivery_head_postimage"]["head_revision"],
        "delivery_head_digest": rows["delivery_head_postimage"]["head_digest"],
        "attempt_aggregate_ceilings": inputs["attempt_aggregate_ceilings"],
        "effect_ceilings": inputs["author_effect_ceilings"],
    }


def _assert_vector_semantics(vector: dict[str, object]) -> None:
    assert (
        vector["c2b3d_committed_at"]
        <= vector["planning_context_captured_at"]
        <= vector["source_invocation_started_at"]
        <= vector["source_invocation_completed_at"]
        <= vector["proposal_created_at"]
        < vector["coordinator_disposition_decided_at"]
        < vector["authority_attestation"]["expires_at"]
        < vector["attempt_fence_expires_at"]
    )
    assert vector["coordinator_disposition_decided_at"] < vector["effect_fence_expires_at"]
    context = vector["planning_context"]
    assert context["planning_context_captured_at"] == vector["planning_context_captured_at"]
    source = vector["source_invocation"]
    assert source["source_invocation_started_at"] == vector["source_invocation_started_at"]
    assert source["source_invocation_completed_at"] == vector["source_invocation_completed_at"]
    proposal = vector["pre_execution_proposal"]
    assert proposal["proposal_created_at"] == vector["proposal_created_at"]
    assert tuple(proposal) == tuple(name for name, _predicate in TABLE_CONTRACTS["development_model_proposals"]["columns"])
    assert proposal["schema_id"] == SCHEMA_IDS["proposal"]
    artifact_phase = vector["private_plan_artifact"]["proposal_phase"]
    assert proposal["proposal_phase"] == artifact_phase == "pre_execution_plan"
    assert proposal["recommendation"] == vector["private_plan_artifact"]["recommendation"] == vector["safe_projection"]["recommendation"]
    decision_time = vector["coordinator_disposition_decided_at"]
    assert vector["coordinator_disposition"]["coordinator_disposition_decided_at"] == decision_time
    assert vector["current_selection_postimage"]["updated_at"] == decision_time
    assert vector["fresh_result"]["recorded_at"] == decision_time
    assert vector["receipt"]["committed_at"] == decision_time
    assert "coordinator_disposition_decided_at" not in proposal
    assert "proposal_created_at" not in vector["coordinator_disposition"]
    assert vector["coordinator_disposition"]["schema_id"] == SCHEMA_IDS["disposition"]
    assert vector["coordinator_disposition"]["disposition_ref"] != proposal["proposal_ref"]
    _assert_authority_selection_eligible(vector["authority_attestation"], decision_time)
    attestation_context_fields = {
        "authority_attestation_schema_id": "schema_id",
        "authority_attestation_ref": "authority_attestation_ref",
        "authoritative_subject_kind": "authoritative_subject_kind",
        "authoritative_subject_ref": "authoritative_subject_ref",
        "authority_evaluation_ref": "authority_evaluation_ref",
        "authority_evaluation_digest": "authority_evaluation_digest",
        "authority_state": "authority_state",
        "authority_version": "authority_version",
        "authority_issued_at": "issued_at",
        "authority_expires_at": "expires_at",
        "authority_source_ref": "source_authority_ref",
        "authority_attestation_digest": "authority_attestation_digest",
    }
    for context_field, attestation_field in attestation_context_fields.items():
        assert context[context_field] == vector["authority_attestation"][attestation_field]
    _assert_private_plan_semantics(vector["private_plan_artifact"])
    artifact_bytes = _independent_canonical_bytes(vector["private_plan_artifact"])
    assert vector["private_artifact_binding"]["artifact_canonical_byte_length"] == len(artifact_bytes)
    assert vector["private_artifact_binding"]["artifact_digest"] == vector["private_plan_artifact"]["artifact_digest"]

    artifact = vector["private_plan_artifact"]
    component_values = {
        "affected_path_set": artifact["affected_authorized_paths"],
        "expected_output_set": artifact["expected_outputs"],
        "validation_strategy": artifact["validation_strategy"],
        "assumption_set": artifact["material_assumptions"],
        "risk_set": artifact["risks_and_uncertainties"],
        "prerequisite_set": artifact["required_evidence_and_prerequisites"],
        "stop_condition_set": artifact["stop_or_replan_conditions"],
        "resource_effect_use": artifact["proposed_resource_and_effect_use"],
    }
    recomputed_components = {
        name: _independent_domain_digest(DIGEST_DOMAINS[name], value)
        for name, value in component_values.items()
    }
    assert vector["component_digests"] == recomputed_components
    projection = vector["safe_projection"]
    assert projection["strategy_item_count"] == len(artifact["implementation_strategy"])
    assert projection["work_unit_count"] == len(artifact["proposed_work_units"])
    assert projection["affected_path_count"] == len(artifact["affected_authorized_paths"])
    assert projection["expected_output_count"] == len(artifact["expected_outputs"])
    assert projection["validation_step_count"] == len(artifact["validation_strategy"])
    assert projection["assumption_count"] == len(artifact["material_assumptions"])
    assert projection["risk_count"] == len(artifact["risks_and_uncertainties"])
    assert projection["prerequisite_count"] == len(artifact["required_evidence_and_prerequisites"])
    assert projection["stop_condition_count"] == len(artifact["stop_or_replan_conditions"])
    for name, digest in recomputed_components.items():
        field = {
            "affected_path_set": "affected_path_set_digest",
            "expected_output_set": "expected_output_set_digest",
            "validation_strategy": "validation_strategy_digest",
            "assumption_set": "assumption_set_digest",
            "risk_set": "risk_set_digest",
            "prerequisite_set": "prerequisite_set_digest",
            "stop_condition_set": "stop_condition_set_digest",
            "resource_effect_use": "proposed_resource_effect_use_digest",
        }[name]
        assert projection[field] == digest

    _assert_readiness_and_graph_semantics(vector)
    assert vector["fresh_result"] == vector["exact_replay_result"]
    assert vector["fresh_result"] is not vector["exact_replay_result"]
    assert vector["receipt"]["result_projection_digest"] == vector["fresh_result"]["result_projection_digest"]
    assert vector["receipt"]["mutation_graph_digest"] == vector["supplied_graph"]["mutation_graph_digest"]
    assert vector["receipt"]["selection_head_digest"] == vector["current_selection_postimage"]["head_digest"]

    row_digest_contracts = {
        "development_model_source_invocations": (DIGEST_DOMAINS["source_invocation"], "source_invocation_digest"),
        "development_pre_execution_planning_contexts": (DIGEST_DOMAINS["pre_execution_context"], "planning_context_digest"),
        "development_private_proposal_artifact_bindings": (DIGEST_DOMAINS["artifact_binding"], "artifact_binding_digest"),
        "development_model_proposals": (DIGEST_DOMAINS["proposal"], "proposal_digest"),
        "development_pre_execution_plan_projections": (DIGEST_DOMAINS["pre_execution_projection"], "safe_projection_digest"),
        "development_model_proposal_evidence_bindings": (DIGEST_DOMAINS["evidence_binding"], "evidence_binding_digest"),
        "development_pre_execution_dispositions": (DIGEST_DOMAINS["disposition"], "disposition_digest"),
        "development_pre_execution_selection_heads": (DIGEST_DOMAINS["selection_head"], "head_digest"),
        "development_cognitive_mutation_receipts": (DIGEST_DOMAINS["receipt"], "receipt_digest"),
    }
    for table, rows in vector["migration_0003_rows_by_table"].items():
        expected_columns = tuple(name for name, _predicate in TABLE_CONTRACTS[table]["columns"])
        domain, digest_field = row_digest_contracts[table]
        for row in rows:
            assert tuple(row) == expected_columns
            _assert_self_digest(row, domain, digest_field)

    basis_relation = {
        "program_ref": "program_ref",
        "program_version_ref": "program_version_ref",
        "program_version_number": "program_version_number",
        "accepted_intent_revision_ref": "accepted_intent_revision_ref",
        "work_item_ref": "work_item_ref",
        "work_item_revision_ref": "work_item_revision_ref",
        "semantic_attempt_ref": "semantic_attempt_ref",
        "semantic_attempt_digest": "semantic_attempt_digest",
        "attempt_number": "attempt_number",
        "candidate_ref": "candidate_ref",
        "basis_decision_ref": "basis_decision_ref",
        "basis_decision_digest": "basis_decision_digest",
        "work_spec_ref": "work_spec_ref",
        "work_spec_digest": "work_spec_digest",
        "work_spec_safe_projection_digest": "work_spec_safe_projection_digest",
        "effect_intent_ref": "effect_intent_ref",
        "effect_intent_digest": "effect_intent_digest",
        "author_command_ref": "author_command_ref",
        "author_command_digest": "author_command_digest",
        "standing_grant_ref": "standing_grant_ref",
        "standing_grant_digest": "standing_grant_digest",
        "attempt_authorization_ref": "attempt_authorization_ref",
        "attempt_authorization_digest": "attempt_authorization_digest",
        "effect_authorization_ref": "effect_authorization_ref",
        "effect_authorization_digest": "effect_authorization_digest",
        "attempt_fence_ref": "attempt_fence_ref",
        "attempt_fence_digest": "attempt_fence_digest",
        "attempt_fence_expires_at": "attempt_fence_expires_at",
        "effect_fence_ref": "effect_fence_ref",
        "effect_fence_digest": "effect_fence_digest",
        "effect_fence_expires_at": "effect_fence_expires_at",
        "delivery_attempt_ref": "delivery_attempt_ref",
        "delivery_envelope_digest": "delivery_envelope_digest",
        "delivery_attempt_digest": "delivery_attempt_digest",
        "expected_effect_head_fence_ref": "effect_fence_ref",
        "expected_effect_head_digest": "effect_head_digest",
        "expected_delivery_head_attempt_ref": "delivery_attempt_ref",
        "expected_delivery_head_digest": "delivery_head_digest",
        "global_stop_ref": "coding_global_stop_ref",
        "global_stop_version": "coding_global_stop_version",
        "authority_evaluation_ref": "authority_evaluation_ref",
        "authority_evaluation_digest": "authority_evaluation_digest",
        "repository_ref": "repository_ref",
        "base_git_object_format": "base_git_object_format",
        "base_git_oid": "base_git_oid",
        "validation_requirement_ref": "validation_requirement_ref",
        "validation_requirement_digest": "validation_requirement_digest",
        "validation_safe_evidence_digest": "validation_safe_evidence_digest",
        "review_requirement_ref": "review_requirement_ref",
        "review_requirement_digest": "review_requirement_digest",
        "review_safe_evidence_digest": "review_safe_evidence_digest",
    }
    for context_field, basis_field in basis_relation.items():
        assert context[context_field] == C2B3D_BASIS[basis_field]
    assert context["attempt_fence_allowed_effect_classes_json"] == _canonical_bytes(C2B3D_BASIS["attempt_fence_allowed_effect_classes"]).decode("utf-8")
    assert context["effect_fence_allowed_effect_classes_json"] == _canonical_bytes(C2B3D_BASIS["effect_fence_allowed_effect_classes"]).decode("utf-8")


def test_section_41_is_exact_and_sections_1_40_are_byte_identical() -> None:
    prefix, section = _section_41_bytes()
    assert prefix.endswith(b"-->\n")
    assert section.count(BEGIN_MARKER.encode()) == 1
    assert section.count(END_MARKER.encode()) == 1
    assert _read_owner_bytes() == prefix + b"\n" + section
    _parse_owner_literal()


def test_recursive_types_mapping_order_and_canonical_ledger_are_independent() -> None:
    owner = _parse_owner_literal()
    _assert_closed_value(owner)
    for vector in owner["golden_vectors"].values():
        expected_names = tuple(record["name"] for record in vector["canonical_records"])
        assert expected_names == (
            "safe_model_configuration",
            "authority_currentness_attestation",
            "private_plan_artifact",
            "safe_projection",
            "planning_context",
            "private_artifact_binding",
            "source_invocation",
            "evidence_set",
            "model_proposal",
            "selection_preimage",
            "selection_postimage",
            "coordinator_disposition",
            "safe_command",
            "mutation_graph",
            "fresh_result",
            "receipt",
        )
        for record in vector["canonical_records"]:
            canonical = record["canonical_json"].encode("utf-8")
            assert len(canonical) == record["canonical_utf8_length"]
            assert hashlib.sha256(canonical).hexdigest() == record["raw_sha256"]
            decoded = json.loads(canonical)
            assert json.dumps(decoded, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8") == canonical


def test_private_plan_contains_substantive_engineering_judgment_but_rows_do_not() -> None:
    vector = _parse_owner_literal()["golden_vectors"]["readiness_absent"]
    artifact = vector["private_plan_artifact"]
    assert tuple(artifact) == PRIVATE_PLAN_FIELD_ORDER
    for field, lower, upper in (
        ("implementation_strategy", 1, 8),
        ("proposed_work_units", 1, 32),
        ("affected_authorized_paths", 1, 64),
        ("expected_outputs", 1, 32),
        ("validation_strategy", 1, 32),
        ("material_assumptions", 1, 16),
        ("risks_and_uncertainties", 1, 16),
        ("required_evidence_and_prerequisites", 1, 32),
        ("stop_or_replan_conditions", 1, 16),
    ):
        assert lower <= len(artifact[field]) <= upper
    projection = vector["safe_projection"]
    assert tuple(projection) == tuple(
        name for name, _predicate in TABLE_CONTRACTS["development_pre_execution_plan_projections"]["columns"]
    )
    durable_json = _canonical_bytes(vector["migration_0003_rows_by_table"]).decode("utf-8")
    for private_value in (
        artifact["implementation_strategy"][0],
        artifact["proposed_work_units"][0]["summary"],
        artifact["affected_authorized_paths"][0],
        artifact["expected_outputs"][0]["description"],
        artifact["validation_strategy"][0]["target"],
        artifact["material_assumptions"][0]["statement"],
        artifact["risks_and_uncertainties"][0]["description"],
        artifact["required_evidence_and_prerequisites"][0]["requirement"],
        artifact["stop_or_replan_conditions"][0]["statement"],
    ):
        assert private_value not in durable_json


def test_migration_0003_tables_rows_graph_and_receipt_algebra_are_exact() -> None:
    owner = _parse_owner_literal()
    contract = owner["coordinator_cognitive_proposal_selection_contract"]
    migration = contract["migration_0003"]
    vectors = owner["golden_vectors"]
    assert migration["table_order"] == tuple(TABLE_CONTRACTS)
    assert migration["new_table_count"] == 9
    assert len(migration["triggers"]) == 18
    assert tuple(item[0] for item in migration["trigger_program"]) == migration["triggers"]
    assert migration["explicit_indexes"] == ()
    assert migration["seed_rows"] == ()
    assert migration["rebuilds_migration_0002_table"] is False
    referenced_checks = {
        check
        for table in migration["tables"].values()
        for check in table["relational_checks"]
    }
    assert referenced_checks <= set(migration["exact_named_check_algebra"])
    for table in migration["tables"].values():
        column_names = tuple(name for name, _predicate in table["columns"])
        assert len(column_names) == len(set(column_names))
        assert set(table["primary_key"]) <= set(column_names)
        assert all(set(unique) <= set(column_names) for unique in table["unique"])
        assert all(set(local) <= set(column_names) for local, _foreign, _remote, _timing in table["foreign_keys"])
    for name, vector in vectors.items():
        assert tuple(vector["migration_0003_rows_by_table"]) == migration["table_order"]
        expected_rows = 23 if name == "readiness_present" else 22
        assert len(vector["physical_row_write_order"]) == expected_rows
        assert len(vector["row_canonical_records"]) == expected_rows
        _assert_readiness_and_graph_semantics(vector)
        for (table, row), record in zip(vector["physical_row_write_order"], vector["row_canonical_records"], strict=True):
            assert record["name"].startswith(table + "[")
            canonical = _independent_canonical_bytes(row)
            assert record["canonical_json"] == canonical.decode("utf-8")
            assert record["canonical_utf8_length"] == len(canonical)
            assert record["raw_sha256"] == hashlib.sha256(canonical).hexdigest()


def test_all_golden_row_and_aggregate_digests_recompute_independently() -> None:
    for vector in _parse_owner_literal()["golden_vectors"].values():
        row_specs = (
        (vector["safe_model_configuration"], DIGEST_DOMAINS["safe_model_configuration"], "model_configuration_digest"),
        (vector["authority_attestation"], DIGEST_DOMAINS["authority_attestation"], "authority_attestation_digest"),
        (vector["private_plan_artifact"], DIGEST_DOMAINS["pre_execution_artifact"], "artifact_digest"),
        (vector["safe_projection"], DIGEST_DOMAINS["pre_execution_projection"], "safe_projection_digest"),
        (vector["planning_context"], DIGEST_DOMAINS["pre_execution_context"], "planning_context_digest"),
        (vector["private_artifact_binding"], DIGEST_DOMAINS["artifact_binding"], "artifact_binding_digest"),
        (vector["source_invocation"], DIGEST_DOMAINS["source_invocation"], "source_invocation_digest"),
        (vector["pre_execution_proposal"], DIGEST_DOMAINS["proposal"], "proposal_digest"),
        (vector["coordinator_disposition"], DIGEST_DOMAINS["disposition"], "disposition_digest"),
        (vector["current_selection_postimage"], DIGEST_DOMAINS["selection_head"], "head_digest"),
        (vector["safe_mutation_command"], DIGEST_DOMAINS["safe_command"], "mutation_command_digest"),
        (vector["fresh_result"], DIGEST_DOMAINS["result"], "result_projection_digest"),
        (vector["receipt"], DIGEST_DOMAINS["receipt"], "receipt_digest"),
        )
        for row, domain, field in row_specs:
            _assert_self_digest(row, domain, field)
        for row in vector["migration_0003_rows_by_table"]["development_model_proposal_evidence_bindings"]:
            _assert_self_digest(row, DIGEST_DOMAINS["evidence_binding"], "evidence_binding_digest")
        evidence_set = vector["evidence_set"]
        assert evidence_set["evidence_set_digest"] == _independent_domain_digest(DIGEST_DOMAINS["evidence_set"], _without(evidence_set, "evidence_set_digest"))
        graph = vector["supplied_graph"]
        assert graph["mutation_graph_digest"] == _independent_domain_digest(DIGEST_DOMAINS["mutation_graph"], _without(graph, "mutation_graph_digest"))
        assert vector["current_selection_preimage_digest"] == _independent_domain_digest(DIGEST_DOMAINS["selection_preimage"], vector["current_selection_preimage"])
        _assert_vector_semantics(vector)


def test_common_envelope_supports_both_phases_but_first_family_is_pre_execution_only() -> None:
    contract = _parse_owner_literal()["coordinator_cognitive_proposal_selection_contract"]
    common = contract["common_model_proposal_envelope"]
    assert common["proposal_phases"] == PHASES
    assert tuple(common["phase_contracts"]) == PHASES
    assert common["phase_contracts"]["pre_execution_plan"]["recommendations"] == PRE_EXECUTION_RECOMMENDATIONS
    assert common["phase_contracts"]["post_execution_semantic_review"]["recommendations"] == POST_EXECUTION_RECOMMENDATIONS
    assert common["first_source_tranche_admits_phase"] == "pre_execution_plan"
    assert common["post_execution_rows_or_decision_family_in_first_source_tranche"] is False
    compatibility = contract["post_execution_compatibility"]
    assert compatibility["post_execution_context_projection_or_disposition_tables_in_0003"] is False
    assert compatibility["post_execution_Coordinator_decision_family_implemented_or_frozen"] is False


def test_pending_authority_permits_planning_without_dispatch_or_host_readiness() -> None:
    owner = _parse_owner_literal()
    contract = owner["coordinator_cognitive_proposal_selection_contract"]
    boundary = contract["authority_readiness_policy_and_risk"]
    vector = owner["golden_vectors"]["readiness_absent"]
    assert vector["planning_context"]["authority_state"] == "pending"
    assert vector["coordinator_disposition"]["disposition"] == "selected_for_dispatch_gates"
    assert boundary["pending_authority_permits_planning_and_nonexecuting_selection"] is True
    assert boundary["qualified_remote_host_readiness_required_for_planning"] is False
    assert vector["privacy"]["host_readiness_evidence_present"] is False
    assert boundary["fresh_external_verification_immediately_before_dispatch_activity"] is True
    assert boundary["Coordinator_authors_or_infers_verified_authority"] is False
    assert contract["coordinator_disposition_and_currentness"]["selected_meaning"].startswith("eligible only")


def test_current_selection_does_not_overload_existing_heads_or_progression() -> None:
    contract = _parse_owner_literal()["coordinator_cognitive_proposal_selection_contract"]
    currentness = contract["coordinator_disposition_and_currentness"]
    assert currentness["currentness_source"] == "development_pre_execution_selection_heads only"
    assert {"program head", "work head", "effect head", "delivery head"}.issubset(
        currentness["currentness_not_inferred_from"]
    )
    assert currentness["selected_changes"] == ()
    assert {"program version", "semantic attempt", "effect head", "delivery head", "verified authority"}.issubset(
        currentness["selected_does_not_change"]
    )
    head = TABLE_CONTRACTS["development_pre_execution_selection_heads"]
    assert head["writer"] == "Coordinator_cognitive_mutation_family_only"
    assert head["mutable"] is True


def test_privacy_placement_and_all_non_goals_are_closed() -> None:
    owner = _parse_owner_literal()
    contract = owner["coordinator_cognitive_proposal_selection_contract"]
    privacy = contract["privacy_and_model_replacement"]
    durable = _canonical_bytes(tuple(vector["migration_0003_rows_by_table"] for vector in owner["golden_vectors"].values())).decode("utf-8")
    for prohibited_name in (
        "raw_prompt", "hidden_reasoning", "provider_session", "raw_model_response",
        "provider_request_payload", "provider_response_payload", "credential", "endpoint",
        "account_id", "organization_id", "bearer",
    ):
        assert prohibited_name not in durable
    assert privacy["safe_ref_or_digest_grants_retrieval"] is False
    assert privacy["one_configured_model_for_both_phases_is_sufficient"] is True
    absent = contract["later_source_boundary_and_absent_effects"]
    assert absent["first_later_source_tranche_invokes_model"] is False
    assert absent["selected_for_dispatch_gates_is_executable"] is False
    assert absent["independent_audit_performed"] is False
    assert {"migration 0003 SQL or catalog entry", "worker", "transport", "Git handler", "publication"}.issubset(
        absent["absent_and_blocked"]
    )


CAUSAL_MUTANTS = (
    "collapse_proposal_into_disposition",
    "permit_recommendation_only_plan",
    "put_private_plan_text_in_SQLite",
    "make_pending_authority_block_planning",
    "require_host_readiness_for_planning",
    "make_selection_executable",
    "overload_effect_head",
    "remove_selection_CAS",
    "allow_expired_authority_selection",
    "add_generic_metadata_table",
    "restore_bootstrap_latch",
    "rebuild_migration_0002",
    "remove_post_execution_phase",
    "implement_post_execution_decision",
    "allow_automatic_semantic_retry",
    "make_receipt_replay_reinterpret_policy",
    "change_sections_1_40_prefix",
)


def _apply_causal_mutant(contract: dict[str, object], name: str) -> None:
    if name == "collapse_proposal_into_disposition":
        contract["coordinator_disposition_and_currentness"]["proposal_and_disposition_are_distinct_types_and_identities"] = False
    elif name == "permit_recommendation_only_plan":
        contract["pre_execution_private_plan_artifact"]["substance_rule"] = "recommendation is sufficient"
    elif name == "put_private_plan_text_in_SQLite":
        contract["pre_execution_safe_projection"]["forbids"] = ()
    elif name == "make_pending_authority_block_planning":
        contract["authority_readiness_policy_and_risk"]["pending_authority_permits_planning_and_nonexecuting_selection"] = False
    elif name == "require_host_readiness_for_planning":
        contract["authority_readiness_policy_and_risk"]["qualified_remote_host_readiness_required_for_planning"] = True
    elif name == "make_selection_executable":
        contract["later_source_boundary_and_absent_effects"]["selected_for_dispatch_gates_is_executable"] = True
    elif name == "overload_effect_head":
        contract["coordinator_disposition_and_currentness"]["currentness_source"] = "development_effect_heads"
    elif name == "remove_selection_CAS":
        contract["coordinator_disposition_and_currentness"]["supersession"] = "latest timestamp wins"
    elif name == "allow_expired_authority_selection":
        contract["authority_readiness_policy_and_risk"]["selected_for_dispatch_gates_permitted_authority_states"] += ("expired",)
    elif name == "add_generic_metadata_table":
        contract["migration_0003"]["tables"]["development_generic_metadata"] = {}
    elif name == "restore_bootstrap_latch":
        contract["migration_0003"]["bootstrap_latch"] = True
    elif name == "rebuild_migration_0002":
        contract["migration_0003"]["rebuilds_migration_0002_table"] = True
    elif name == "remove_post_execution_phase":
        contract["common_model_proposal_envelope"]["proposal_phases"] = ("pre_execution_plan",)
    elif name == "implement_post_execution_decision":
        contract["post_execution_compatibility"]["post_execution_Coordinator_decision_family_implemented_or_frozen"] = True
    elif name == "allow_automatic_semantic_retry":
        contract["replay_conflict_and_recovery"]["automatic_semantic_retry"] = True
    elif name == "make_receipt_replay_reinterpret_policy":
        contract["replay_conflict_and_recovery"]["same_key_same_digest"] = "re-evaluate current policy"
    elif name == "change_sections_1_40_prefix":
        contract["contract_identity"]["sections_1_40_protected_utf8_length"] += 1
    else:
        raise AssertionError(name)


def _assert_named_contract_predicate(contract: dict[str, object], name: str) -> None:
    if name == "collapse_proposal_into_disposition":
        assert contract["coordinator_disposition_and_currentness"]["proposal_and_disposition_are_distinct_types_and_identities"] is True
    elif name == "permit_recommendation_only_plan":
        rule = contract["pre_execution_private_plan_artifact"]["substance_rule"]
        assert all(word in rule for word in ("cardinality", "narrative", "ownership", "cross-reference", "placeholder"))
        assert contract["pre_execution_private_plan_artifact"]["structural_validation_manufactures_engineering_judgment"] is False
    elif name == "put_private_plan_text_in_SQLite":
        forbidden = contract["pre_execution_safe_projection"]["forbids"]
        assert {"strategy text", "work-unit text", "path strings", "private WorkSpec content"} <= set(forbidden)
    elif name == "make_pending_authority_block_planning":
        assert contract["authority_readiness_policy_and_risk"]["pending_authority_permits_planning_and_nonexecuting_selection"] is True
    elif name == "require_host_readiness_for_planning":
        assert contract["authority_readiness_policy_and_risk"]["qualified_remote_host_readiness_required_for_planning"] is False
    elif name == "make_selection_executable":
        assert contract["later_source_boundary_and_absent_effects"]["selected_for_dispatch_gates_is_executable"] is False
    elif name == "overload_effect_head":
        assert contract["coordinator_disposition_and_currentness"]["currentness_source"] == "development_pre_execution_selection_heads only"
    elif name == "remove_selection_CAS":
        currentness = contract["coordinator_disposition_and_currentness"]
        assert "exact CAS" in currentness["supersession"] and "prior head digest" in currentness["supersession"]
    elif name == "allow_expired_authority_selection":
        boundary = contract["authority_readiness_policy_and_risk"]
        assert boundary["selected_for_dispatch_gates_permitted_authority_states"] == ("pending", "verified")
        assert "expired" in boundary["selected_for_dispatch_gates_forbidden_authority_states"]
    elif name == "add_generic_metadata_table":
        migration = contract["migration_0003"]
        assert migration["new_table_count"] == len(migration["tables"]) == 9
        assert tuple(migration["tables"]) == tuple(TABLE_CONTRACTS)
    elif name == "restore_bootstrap_latch":
        assert contract["migration_0003"]["bootstrap_latch"] is False
    elif name == "rebuild_migration_0002":
        assert contract["migration_0003"]["rebuilds_migration_0002_table"] is False
    elif name == "remove_post_execution_phase":
        assert contract["common_model_proposal_envelope"]["proposal_phases"] == PHASES
    elif name == "implement_post_execution_decision":
        assert contract["post_execution_compatibility"]["post_execution_Coordinator_decision_family_implemented_or_frozen"] is False
    elif name == "allow_automatic_semantic_retry":
        assert contract["replay_conflict_and_recovery"]["automatic_semantic_retry"] is False
    elif name == "make_receipt_replay_reinterpret_policy":
        replay = contract["replay_conflict_and_recovery"]["same_key_same_digest"]
        assert all(term in replay for term in ("original receipt-owned result", "without clock", "policy reinterpretation"))
    elif name == "change_sections_1_40_prefix":
        identity = contract["contract_identity"]
        assert identity["sections_1_40_protected_utf8_length"] == EXPECTED_SECTIONS_1_40_UTF8_LENGTH
        assert identity["sections_1_40_protected_sha256"] == EXPECTED_SECTIONS_1_40_SHA256
    else:
        raise AssertionError(name)


@pytest.mark.parametrize("case_name", CAUSAL_MUTANTS, ids=CAUSAL_MUTANTS)
def test_bounded_causal_contract_mutants_fail(case_name: str) -> None:
    owner = _parse_owner_literal()
    candidate = deepcopy(owner["coordinator_cognitive_proposal_selection_contract"])
    _apply_causal_mutant(candidate, case_name)
    currentness = candidate["coordinator_disposition_and_currentness"]
    plan = candidate["pre_execution_private_plan_artifact"]
    projection = candidate["pre_execution_safe_projection"]
    authority = candidate["authority_readiness_policy_and_risk"]
    later = candidate["later_source_boundary_and_absent_effects"]
    migration = candidate["migration_0003"]
    post = candidate["post_execution_compatibility"]
    replay = candidate["replay_conflict_and_recovery"]
    checks = {
        "collapse_proposal_into_disposition": currentness["proposal_and_disposition_are_distinct_types_and_identities"] is True,
        "permit_recommendation_only_plan": all(word in plan["substance_rule"] for word in ("cardinality", "narrative", "ownership", "cross-reference", "placeholder")) and plan["structural_validation_manufactures_engineering_judgment"] is False,
        "put_private_plan_text_in_SQLite": {"strategy text", "work-unit text", "path strings", "private WorkSpec content"} <= set(projection["forbids"]),
        "make_pending_authority_block_planning": authority["pending_authority_permits_planning_and_nonexecuting_selection"] is True,
        "require_host_readiness_for_planning": authority["qualified_remote_host_readiness_required_for_planning"] is False,
        "make_selection_executable": later["selected_for_dispatch_gates_is_executable"] is False,
        "overload_effect_head": currentness["currentness_source"] == "development_pre_execution_selection_heads only",
        "remove_selection_CAS": "exact CAS" in currentness["supersession"] and "prior head digest" in currentness["supersession"],
        "allow_expired_authority_selection": authority["selected_for_dispatch_gates_permitted_authority_states"] == ("pending", "verified") and "expired" in authority["selected_for_dispatch_gates_forbidden_authority_states"],
        "add_generic_metadata_table": migration["new_table_count"] == len(migration["tables"]) == 9 and tuple(migration["tables"]) == tuple(TABLE_CONTRACTS),
        "restore_bootstrap_latch": migration["bootstrap_latch"] is False,
        "rebuild_migration_0002": migration["rebuilds_migration_0002_table"] is False,
        "remove_post_execution_phase": candidate["common_model_proposal_envelope"]["proposal_phases"] == PHASES,
        "implement_post_execution_decision": post["post_execution_Coordinator_decision_family_implemented_or_frozen"] is False,
        "allow_automatic_semantic_retry": replay["automatic_semantic_retry"] is False,
        "make_receipt_replay_reinterpret_policy": all(term in replay["same_key_same_digest"] for term in ("original receipt-owned result", "without clock", "policy reinterpretation")),
        "change_sections_1_40_prefix": candidate["contract_identity"]["sections_1_40_protected_utf8_length"] == EXPECTED_SECTIONS_1_40_UTF8_LENGTH and candidate["contract_identity"]["sections_1_40_protected_sha256"] == EXPECTED_SECTIONS_1_40_SHA256,
    }
    classification = (
        "historical_contract_boundary_accepted"
        if checks[case_name]
        else f"historical_contract_boundary_rejected:{case_name}"
    )
    assert classification == f"historical_contract_boundary_rejected:{case_name}"


def test_c2b3d_prerequisite_basis_is_byte_and_relation_exact() -> None:
    independently_parsed = _extract_c2b3d_basis(_section_39_vector())
    _assert_exact(independently_parsed, C2B3D_BASIS, "C2B3D_PREREQUISITE_BASIS_INVALID")
    owner = _parse_owner_literal()
    contract_basis = owner["coordinator_cognitive_proposal_selection_contract"]["c2b3d_prerequisite_crosswalk"]["exact_basis"]
    _assert_exact(contract_basis, independently_parsed, "C2B3D_PREREQUISITE_BASIS_INVALID")
    for vector in owner["golden_vectors"].values():
        _assert_vector_semantics(vector)


def test_preselection_and_transaction_owned_timestamps_are_acyclic() -> None:
    for vector in _parse_owner_literal()["golden_vectors"].values():
        _assert_vector_semantics(vector)
        proposal_bundle = (
            vector["planning_context"], vector["source_invocation"], vector["private_plan_artifact"],
            vector["private_artifact_binding"], vector["safe_projection"], vector["evidence_set"],
            vector["pre_execution_proposal"], vector["safe_mutation_command"],
        )
        assert all("coordinator_disposition_decided_at" not in value for value in proposal_bundle)
        assert vector["fresh_result"] == vector["exact_replay_result"]


AUTHORITY_CASES = (
    "eligible_pending",
    "eligible_verified",
    "expired_verified",
    "exact_expiry_boundary",
    "selection_time_revoked",
    "later_revocation_does_not_rewrite_history",
    "stale_authority_version",
    "wrong_subject",
    "wrong_evaluation_binding",
    "absent_required_attestation",
    "malformed_attestation",
    "contradictory_context_binding",
    "wrong_attestation_digest",
    "attempt_fence_expiry",
    "effect_fence_expiry",
    "pending_selection_non_executable",
)


@pytest.mark.parametrize("case_name", AUTHORITY_CASES, ids=AUTHORITY_CASES)
def test_opening_snapshot_historical_authority_attestation_vectors(
    case_name: str,
) -> None:
    decision = "2026-08-22T12:35:04Z"
    bundle = _sample_temporal_bundle()
    observation = bundle["authority_observation"]

    def reseal_observation() -> None:
        observation["authority_observation_digest"] = _s41_digest(
            REPAIRED_AUTHORITY_DOMAIN,
            _s41_without(observation, "authority_observation_digest"),
        )
        bundle["preselection_records"] = _sample_preselection_records(observation)

    if case_name in ("eligible_pending", "eligible_verified"):
        observation["observation_state"] = (
            "pending" if case_name == "eligible_pending" else "verified"
        )
        reseal_observation()
        result = _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: decision,
            trace=[],
        )
        assert result["authority_selection_observation_digest"] == observation["authority_observation_digest"]
        return
    if case_name == "pending_selection_non_executable":
        observation["observation_state"] = "pending"
        reseal_observation()
        result = _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: decision,
            trace=[],
        )
        assert result["grants_dispatch"] is False
        return
    if case_name == "later_revocation_does_not_rewrite_history":
        persisted = _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: decision,
            trace=[],
        )
        later = _build_authority_observation(
            state="revoked",
            version=23,
            issued_at="2026-08-22T12:35:05Z",
            expires_at="2026-08-22T13:35:05Z",
        )
        with pytest.raises(_ContractViolation) as caught:
            _validate_authority_observation_non_temporal(
                later, _authority_expected_binding()
            )
        assert caught.value.reason == "authority_observation_state_ineligible"
        persisted_family = _build_repaired_physical_family(False)
        persisted_receipt = persisted_family["receipt"]["values"]
        assert _apply_repaired_selection(
            mutation_ref=persisted_receipt["mutation_ref"],
            command_digest=persisted_receipt["command_digest"],
            receipt=persisted_family,
            bundle=bundle,
            clock=lambda: (_ for _ in ()).throw(RuntimeError("clock called")),
            trace=[],
        ) is persisted_family["replay_result"]
        assert persisted["grants_dispatch"] is False
        return
    expected_reason = "authority_observation_shape_invalid"
    if case_name == "absent_required_attestation":
        bundle["authority_observation"] = {}
    elif case_name == "contradictory_context_binding":
        context = bundle["preselection_records"]["planning_context"]
        context["authority_observation_state"] = "pending"
        context["planning_context_digest"] = _s41_digest(
            DIGEST_DOMAINS["pre_execution_context"],
            _s41_without(context, "planning_context_digest"),
        )
        expected_reason = "authority_observation_binding_mismatch"
    elif case_name == "wrong_attestation_digest":
        observation["authority_observation_digest"] = "f" * 64
    elif case_name in ("expired_verified", "exact_expiry_boundary"):
        observation["observation_state"] = "verified"
        observation["authority_observation_expires_at"] = (
            "2026-08-22T12:35:03Z"
            if case_name == "expired_verified"
            else decision
        )
        reseal_observation()
        expected_reason = "authority_observation_expired"
    elif case_name == "selection_time_revoked":
        observation["observation_state"] = "revoked"
        reseal_observation()
        expected_reason = "authority_observation_state_ineligible"
    elif case_name == "stale_authority_version":
        observation["observation_version"] = 0
        reseal_observation()
        expected_reason = "authority_observation_version_invalid"
    elif case_name == "wrong_subject":
        observation["authoritative_subject_ref"] = "effect-intent-foreign.0001"
        reseal_observation()
        expected_reason = "authority_observation_binding_mismatch"
    elif case_name == "wrong_evaluation_binding":
        observation["authority_evaluation_digest"] = "f" * 64
        reseal_observation()
        expected_reason = "authority_observation_binding_mismatch"
    elif case_name == "malformed_attestation":
        observation["source_authority_ref"] = "connector-secret"
        reseal_observation()
    elif case_name in ("attempt_fence_expiry", "effect_fence_expiry"):
        fence_role = (
            "attempt_fence" if case_name == "attempt_fence_expiry" else "effect_fence"
        )
        bundle[fence_role]["expires_at"] = decision
        _redigest_fence_and_context(bundle, fence_role)
        expected_reason = (
            "attempt_fence_expired"
            if fence_role == "attempt_fence"
            else "effect_fence_expired"
        )
    else:
        raise AssertionError(case_name)
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: decision,
            trace=[],
        )
    assert caught.value.reason == expected_reason


PRIVATE_PLAN_MUTANTS = (
    "whitespace_only_text",
    "closed_placeholder_text",
    "missing_work_units",
    "unresolved_dependency",
    "unauthorized_path",
    "output_without_owner",
    "validation_less_work_unit",
    "scalar_allowed_effect_classes",
    "wrong_effect_sequence_type",
    "empty_effect_sequence",
    "unknown_effect_class",
    "duplicate_effect_class",
    "noncanonical_effect_order",
    "effect_absent_from_effect_fence",
)


@pytest.mark.parametrize("case_name", PRIVATE_PLAN_MUTANTS, ids=PRIVATE_PLAN_MUTANTS)
def test_private_plan_causal_semantic_mutants_fail(case_name: str) -> None:
    artifact = deepcopy(_sample_private_plan())
    if case_name == "whitespace_only_text":
        artifact["implementation_strategy"] = ("   ",)
    elif case_name == "closed_placeholder_text":
        artifact["implementation_strategy"] = ("TBD",)
    elif case_name == "missing_work_units":
        artifact["proposed_work_units"] = ()
    elif case_name == "unresolved_dependency":
        artifact["proposed_work_units"][1]["depends_on_work_unit_refs"] = ("work-unit.missing.0001",)
    elif case_name == "unauthorized_path":
        artifact["affected_authorized_paths"] = ("unauthorized/file.py",)
    elif case_name == "output_without_owner":
        artifact["expected_outputs"][0]["owner_work_unit_ref"] = "work-unit.missing.0001"
    elif case_name == "validation_less_work_unit":
        artifact["proposed_work_units"][0]["validation_refs"] = ()
    elif case_name == "scalar_allowed_effect_classes":
        artifact["proposed_resource_and_effect_use"]["allowed_effect_classes"] = "author_candidate"
    elif case_name == "wrong_effect_sequence_type":
        artifact["proposed_resource_and_effect_use"]["allowed_effect_classes"] = ["author_candidate"]
    elif case_name == "empty_effect_sequence":
        artifact["proposed_resource_and_effect_use"]["allowed_effect_classes"] = ()
    elif case_name == "unknown_effect_class":
        artifact["proposed_resource_and_effect_use"]["allowed_effect_classes"] = ("unknown_effect",)
    elif case_name == "duplicate_effect_class":
        artifact["proposed_resource_and_effect_use"]["allowed_effect_classes"] = ("author_candidate", "author_candidate")
    elif case_name == "noncanonical_effect_order":
        artifact["proposed_resource_and_effect_use"]["allowed_effect_classes"] = ("validate_candidate", "author_candidate")
    elif case_name == "effect_absent_from_effect_fence":
        artifact["proposed_resource_and_effect_use"]["allowed_effect_classes"] = ("cancel_effect",)
    else:
        raise AssertionError(case_name)
    artifact["artifact_digest"] = _s41_digest(
        REPAIRED_ARTIFACT_DOMAIN,
        _s41_without(artifact, "artifact_digest"),
    )
    expected_reason = (
        "private_plan_narrative_invalid"
        if case_name in ("whitespace_only_text", "closed_placeholder_text")
        else "private_plan_nested_collection_invalid"
    )
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_private_plan(artifact)
    assert caught.value.reason == expected_reason


READINESS_CASES = (
    "valid_absence",
    "valid_presence",
    "mixed_context_nullability",
    "row_missing",
    "graph_member_missing",
    "wrong_rank_19_role",
    "wrong_locator",
    "wrong_digest",
    "duplicate_row",
    "duplicate_graph_member",
    "extra_unowned_graph_member",
    "receipt_inserted_as_graph_member",
)


@pytest.mark.parametrize("case_name", READINESS_CASES, ids=READINESS_CASES)
def test_optional_readiness_rank_19_causal_vectors(case_name: str) -> None:
    if case_name == "valid_absence":
        _validate_repaired_physical_family(_build_repaired_physical_family(False))
        return
    vector = _build_repaired_physical_family(True)
    if case_name == "valid_presence":
        _validate_repaired_physical_family(vector)
        absent = _build_repaired_physical_family(False)
        assert next(row for row in vector["physical_rows"] if row["role"] == "coordinator_disposition")["values"]["disposition"] == next(row for row in absent["physical_rows"] if row["role"] == "coordinator_disposition")["values"]["disposition"]
        return
    physical_rows = list(vector["physical_rows"])
    graph_entries = list(vector["graph"]["entries"])
    readiness_index = next(index for index, row in enumerate(physical_rows) if row["role"] == "evidence.qualified_remote_host_readiness")
    member_index = next(index for index, entry in enumerate(graph_entries) if entry["rank"] == 19)
    expected_reason = "physical_family_graph_digest_mismatch"
    if case_name == "mixed_context_nullability":
        context = next(row for row in physical_rows if row["role"] == "planning_context")
        context["values"]["qualified_remote_host_readiness_digest"] = None
        context["values"]["planning_context_digest"] = _repaired_row_digest(
            context["table"], context["values"]
        )
        expected_reason = "physical_family_readiness_mismatch"
    elif case_name == "row_missing":
        del physical_rows[readiness_index]
        expected_reason = "physical_family_missing_row"
    elif case_name == "graph_member_missing":
        del graph_entries[member_index]
        expected_reason = "physical_family_row_without_graph"
    elif case_name == "wrong_rank_19_role":
        graph_entries[member_index]["role"] = "evidence.review_requirement"
        expected_reason = "physical_family_row_without_graph"
    elif case_name == "wrong_locator":
        graph_entries[member_index]["locator"] = (
            ("proposal_ref", "proposal.foreign.0001"),
            ("evidence_role", "qualified_remote_host_readiness"),
            ("ordinal", 0),
        )
    elif case_name == "wrong_digest":
        graph_entries[member_index]["member_digest"] = "f" * 64
    elif case_name == "duplicate_row":
        physical_rows.append(deepcopy(physical_rows[readiness_index]))
        expected_reason = "physical_family_extra_row"
    elif case_name == "duplicate_graph_member":
        graph_entries.insert(member_index, deepcopy(graph_entries[member_index]))
    elif case_name == "extra_unowned_graph_member":
        graph_entries.append({"role": "evidence.unowned", "rank": 22, "ordinal": 0, "table": REPAIRED_TABLE_ORDER[5], "locator": (("proposal_ref", "unowned.0001"), ("evidence_role", "unowned"), ("ordinal", 0)), "member_digest": "e" * 64})
        expected_reason = "physical_family_graph_without_row"
    elif case_name == "receipt_inserted_as_graph_member":
        receipt = vector["receipt"]
        graph_entries.append({"role": "receipt", "rank": 22, "ordinal": 0, "table": receipt["table"], "locator": _member_locator(receipt), "member_digest": _member_digest(receipt)})
        expected_reason = "physical_family_receipt_in_graph"
    else:
        raise AssertionError(case_name)
    vector["physical_rows"] = tuple(physical_rows)
    vector["graph"]["entries"] = tuple(graph_entries)
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(vector)
    assert caught.value.reason == expected_reason


def _recovery_chain(vector: dict[str, object], length: int) -> tuple[tuple[str, int, str], tuple[dict[str, object], ...]]:
    lineage = vector["current_selection_preimage"]["selection_key"]
    prior_ref = vector["coordinator_disposition"]["disposition_ref"]
    prior_revision = vector["current_selection_postimage"]["head_revision"]
    prior_digest = vector["current_selection_postimage"]["head_digest"]
    rows = []
    for revision in range(1, length + 1):
        disposition_ref = f"planning-disposition.recovery.{revision:04d}"
        resulting_digest = hashlib.sha256(f"recovery-head-{revision}".encode("ascii")).hexdigest()
        rows.append({
            "lineage_key": deepcopy(lineage),
            "disposition_ref": disposition_ref,
            "prior_disposition_ref": prior_ref,
            "prior_head_revision": prior_revision,
            "prior_head_digest": prior_digest,
            "resulting_head_revision": revision,
            "resulting_head_digest": resulting_digest,
        })
        prior_ref, prior_revision, prior_digest = disposition_ref, revision, resulting_digest
    return (prior_ref, prior_revision, prior_digest), tuple(rows)


RECOVERY_CASES = (
    "exact_postimage",
    "one_successor",
    "maximum_256",
    "missing_link",
    "cycle",
    "wrong_lineage",
    "overflow_257",
    "duplicate_row",
    "revision_jump",
    "disconnected_successor",
    "branching_successor",
)


@pytest.mark.parametrize("case_name", RECOVERY_CASES, ids=RECOVERY_CASES)
def test_bounded_recovery_ancestry_causal_vectors(case_name: str) -> None:
    vector = _parse_owner_literal()["golden_vectors"]["readiness_absent"]
    lineage = vector["current_selection_preimage"]["selection_key"]
    receipt = vector["receipt"]
    original = vector["coordinator_disposition"]["disposition_ref"]
    if case_name == "exact_postimage":
        current = (original, receipt["selection_head_revision"], receipt["selection_head_digest"])
        rows = ()
        expected = "committed_exact"
    else:
        length = 256 if case_name == "maximum_256" else 257 if case_name == "overflow_257" else 2 if case_name in ("missing_link", "cycle", "wrong_lineage", "duplicate_row", "revision_jump", "disconnected_successor", "branching_successor") else 1
        current, rows = _recovery_chain(vector, length)
        mutable = list(deepcopy(rows))
        expected = "committed_exact" if case_name in ("one_successor", "maximum_256") else "unresolved"
        if case_name == "missing_link":
            del mutable[0]
        elif case_name == "cycle":
            mutable[-1]["prior_disposition_ref"] = mutable[-1]["disposition_ref"]
        elif case_name == "wrong_lineage":
            mutable[-1]["lineage_key"]["program_ref"] = "program-foreign.0001"
        elif case_name == "duplicate_row":
            mutable.append(deepcopy(mutable[-1]))
        elif case_name == "revision_jump":
            mutable[-1]["prior_head_revision"] -= 1
        elif case_name == "disconnected_successor":
            extra = deepcopy(mutable[-1])
            extra["disposition_ref"] = "planning-disposition.disconnected.0001"
            mutable.append(extra)
        elif case_name == "branching_successor":
            extra = deepcopy(mutable[-1])
            extra["disposition_ref"] = "planning-disposition.branch.0001"
            extra["resulting_head_digest"] = "d" * 64
            mutable.append(extra)
        rows = tuple(mutable)
    actual = _classify_recovery_ancestry(
        lineage_key=lineage,
        receipt_disposition_ref=original,
        receipt_head_revision=receipt["selection_head_revision"],
        receipt_head_digest=receipt["selection_head_digest"],
        current_disposition_ref=current[0],
        current_head_revision=current[1],
        current_head_digest=current[2],
        predecessor_rows=rows,
    )
    assert actual == expected
    assert vector["exact_replay_result"] == vector["fresh_result"]


def test_compound_conflict_precedence_is_total_and_exact() -> None:
    owner = _parse_owner_literal()
    vector = owner["golden_vectors"]["readiness_absent"]
    assert tuple(entry["rank"] for entry in FRESH_APPLY_PRECEDENCE) == tuple(range(1, 16))
    assert len({entry["condition"] for entry in FRESH_APPLY_PRECEDENCE}) == 15
    assert owner["coordinator_cognitive_proposal_selection_contract"]["mutation_family"]["fresh_apply_total_precedence"] == FRESH_APPLY_PRECEDENCE
    for case in vector["compound_conflict_examples"]:
        assert _resolve_fresh_outcome(case["true_conditions"]) == case["classification"]
    stale = next(case for case in vector["conflict_examples"] if case["case"] == "stale_current_selection_revision_or_digest")
    assert stale == {"case": "stale_current_selection_revision_or_digest", "classification": "selection_head_version_conflict", "new_disposition": False, "writes": 0}


VECTOR_MUTANTS = (
    "c2b3d_prerequisite_ref_mismatch",
    "c2b3d_prerequisite_digest_mismatch",
    "out_of_window_selection_timestamp",
    "transaction_timestamp_in_proposal_identity",
    "phase_mismatch",
    "schema_mismatch",
    "recommendation_mismatch",
    "proposal_used_as_coordinator_disposition",
    "raw_provider_material_in_durable_row",
    "bool_for_integer",
    "nested_mapping_reorder",
)


@pytest.mark.parametrize("case_name", VECTOR_MUTANTS, ids=VECTOR_MUTANTS)
def test_direct_vector_semantic_mutants_fail(case_name: str) -> None:
    expected_reason: str
    if case_name == "c2b3d_prerequisite_ref_mismatch":
        bundle = _sample_temporal_bundle()
        bundle["preselection_records"]["planning_context"]["work_item_revision_ref"] = "work-item-revision-foreign.0001"
        validator = lambda: _apply_repaired_selection(mutation_ref=REPAIRED_FRESH_MUTATION_REF, command_digest=REPAIRED_FRESH_COMMAND_DIGEST, receipt=None, bundle=bundle, clock=lambda: "2026-08-22T12:35:04Z", trace=[])
        expected_reason = "preselection_timestamp_digest_mismatch"
    elif case_name == "c2b3d_prerequisite_digest_mismatch":
        bundle = _sample_temporal_bundle()
        bundle["preselection_records"]["planning_context"]["attempt_fence_digest"] = "f" * 64
        validator = lambda: _apply_repaired_selection(mutation_ref=REPAIRED_FRESH_MUTATION_REF, command_digest=REPAIRED_FRESH_COMMAND_DIGEST, receipt=None, bundle=bundle, clock=lambda: "2026-08-22T12:35:04Z", trace=[])
        expected_reason = "preselection_timestamp_digest_mismatch"
    elif case_name == "out_of_window_selection_timestamp":
        bundle = _sample_temporal_bundle()
        bundle["attempt_fence"]["expires_at"] = "2026-08-22T12:35:04Z"
        _redigest_fence_and_context(bundle, "attempt_fence")
        validator = lambda: _apply_repaired_selection(mutation_ref=REPAIRED_FRESH_MUTATION_REF, command_digest=REPAIRED_FRESH_COMMAND_DIGEST, receipt=None, bundle=bundle, clock=lambda: "2026-08-22T12:35:04Z", trace=[])
        expected_reason = "attempt_fence_expired"
    elif case_name == "transaction_timestamp_in_proposal_identity":
        bundle = _sample_temporal_bundle()
        bundle["preselection_records"]["model_proposal"]["coordinator_disposition_decided_at"] = "2026-08-22T12:35:04Z"
        validator = lambda: _apply_repaired_selection(mutation_ref=REPAIRED_FRESH_MUTATION_REF, command_digest=REPAIRED_FRESH_COMMAND_DIGEST, receipt=None, bundle=bundle, clock=lambda: "2026-08-22T12:35:04Z", trace=[])
        expected_reason = "preselection_timestamp_record_invalid"
    elif case_name == "phase_mismatch":
        artifact = _sample_private_plan()
        artifact["proposal_phase"] = "post_execution_semantic_review"
        artifact["artifact_digest"] = _s41_digest(REPAIRED_ARTIFACT_DOMAIN, _s41_without(artifact, "artifact_digest"))
        validator = lambda: _validate_repaired_private_plan(artifact)
        expected_reason = "private_plan_closed_vocabulary_invalid"
    elif case_name == "schema_mismatch":
        artifact = _sample_private_plan()
        artifact["schema_id"] = "governed-execution.foreign.v1"
        artifact["artifact_digest"] = _s41_digest(REPAIRED_ARTIFACT_DOMAIN, _s41_without(artifact, "artifact_digest"))
        validator = lambda: _validate_repaired_private_plan(artifact)
        expected_reason = "private_plan_nested_collection_invalid"
    elif case_name == "recommendation_mismatch":
        artifact = _sample_private_plan()
        artifact["recommendation"] = "foreign_recommendation"
        artifact["artifact_digest"] = _s41_digest(REPAIRED_ARTIFACT_DOMAIN, _s41_without(artifact, "artifact_digest"))
        validator = lambda: _validate_repaired_private_plan(artifact)
        expected_reason = "private_plan_closed_vocabulary_invalid"
    elif case_name == "proposal_used_as_coordinator_disposition":
        family = _build_repaired_physical_family(False)
        disposition = next(row for row in family["physical_rows"] if row["role"] == "coordinator_disposition")
        proposal = next(row for row in family["physical_rows"] if row["role"] == "model_proposal")
        disposition["values"]["disposition_ref"] = proposal["values"]["proposal_ref"]
        validator = lambda: _validate_repaired_physical_family(family)
        expected_reason = "physical_family_row_digest_mismatch"
    elif case_name == "raw_provider_material_in_durable_row":
        family = _build_repaired_physical_family(False)
        source = next(row for row in family["physical_rows"] if row["role"] == "source_invocation")
        source["values"]["raw_provider_response"] = "private response"
        validator = lambda: _validate_repaired_physical_family(family)
        expected_reason = "physical_family_row_digest_mismatch"
    elif case_name == "bool_for_integer":
        artifact = _sample_private_plan()
        artifact["proposed_work_units"][0]["ordinal"] = True
        artifact["artifact_digest"] = _s41_digest(REPAIRED_ARTIFACT_DOMAIN, _s41_without(artifact, "artifact_digest"))
        validator = lambda: _validate_repaired_private_plan(artifact)
        expected_reason = "private_plan_nested_collection_invalid"
    elif case_name == "nested_mapping_reorder":
        observation = _build_authority_observation()
        observation = dict(reversed(tuple(observation.items())))
        validator = lambda: _validate_authority_observation_non_temporal(observation, _authority_expected_binding())
        expected_reason = "authority_observation_shape_invalid"
    else:
        raise AssertionError(case_name)
    with pytest.raises(_ContractViolation) as caught:
        validator()
    assert caught.value.reason == expected_reason


RAW_OWNER_MUTANTS = ("raw_comment", "crlf_payload", "duplicate_field")


@pytest.mark.parametrize("case_name", RAW_OWNER_MUTANTS, ids=RAW_OWNER_MUTANTS)
def test_raw_owner_parser_causal_mutants_fail(case_name: str) -> None:
    source = _read_owner_bytes()
    opening = OPENING.encode("utf-8")
    if case_name == "raw_comment":
        mutated = source.replace(opening, opening + b"# forbidden owner comment\n", 1)
    elif case_name == "crlf_payload":
        mutated = source.replace(opening, opening + b"\r\n", 1)
    elif case_name == "duplicate_field":
        mutated = source.replace(opening + b"{", opening + b"{'golden_vectors': {}, ", 1)
    else:
        raise AssertionError(case_name)
    with pytest.raises(AssertionError, match="COGNITIVE_OWNER_LITERAL_INVALID"):
        _parse_owner_literal(mutated, enforce_frozen_bytes=False, compare_expected=False)


def test_supporting_documents_are_bounded_cross_references_not_second_owners() -> None:
    paths = (
        ".docs/c2a-first-slice-semantic-protocol-contract.md",
        ".docs/authority-boundaries.md",
        ".docs/autonomous-software-development-operating-model.md",
        ".docs/software-development-progression-boundary.md",
        ".docs/worker-execution-boundary.md",
        ".docs/durable-state-model.md",
        ".docs/sqlite-bootstrap-and-migrations.md",
        ".docs/sqlite-operations-and-recovery.md",
        ".docs/sqlite-threat-model.md",
        "AGENTS.md",
        "README.md",
    )
    owner_claim = "Section 41 of `.docs/c2b-durable-development-state.md` is the sole detailed semantic owner"
    for relative in paths:
        path = ROOT / relative
        assert not path.is_symlink() and path.resolve(strict=True) == path
        text = path.read_text(encoding="utf-8")
        assert text.count(owner_claim) == 1
        bounded = text.split(owner_claim, 1)[1]
        for phrase in (
            "C2B3D remains current and unchanged",
            "uncommitted contract candidate pending independent audit",
            "Migration 0003 and all source/runtime remain absent",
            "proposal admission plus Coordinator selection or non-selection",
            "model invocation, dispatch, worker contact, post-execution review, semantic decision, Git, and publication remain blocked",
            "full remote-worker phase is not reduced to that first source tranche",
        ):
            assert phrase in bounded


# The tests above retain the exact opening audit snapshot as historical
# evidence.  Everything below validates only the repaired semantic owner and
# uses finite reasons instead of accepting an arbitrary AssertionError.


class _ContractViolation(Exception):
    def __init__(self, reason: str) -> None:
        assert type(reason) is str and reason in REPAIRED_VIOLATION_REASONS
        super().__init__(reason)
        self.reason = reason


INCORPORATED_NINE_FINDING_VIOLATION_REASONS = (
    "cognitive_mutation_identity_invalid",
    "authority_observation_shape_invalid",
    "authority_observation_binding_mismatch",
    "authority_observation_version_invalid",
    "authority_observation_state_ineligible",
    "authority_observation_window_invalid",
    "preselection_timestamp_record_invalid",
    "preselection_timestamp_digest_mismatch",
    "preselection_chronology_invalid",
    "authority_observation_expired",
    "attempt_fence_expired",
    "effect_fence_expired",
    "private_plan_narrative_invalid",
    "private_plan_nested_collection_invalid",
    "private_plan_closed_vocabulary_invalid",
    "private_plan_artifact_size_invalid",
    "private_plan_prerequisite_order_invalid",
    "private_plan_prerequisite_unreferenced",
    "private_plan_stop_unreferenced",
    "private_plan_validation_link_asymmetric",
    "private_plan_forward_dependency",
    "safe_projection_derivation_mismatch",
    "phase_algebra_mismatch",
    "canonical_value_invalid",
    "physical_family_missing_row",
    "physical_family_extra_row",
    "physical_family_row_digest_mismatch",
    "physical_family_graph_without_row",
    "physical_family_row_without_graph",
    "physical_family_receipt_in_graph",
    "physical_family_graph_digest_mismatch",
    "physical_family_order_mismatch",
    "physical_family_receipt_binding_mismatch",
    "physical_family_readiness_mismatch",
    "recovery_unresolved",
)
REPAIRED_VIOLATION_REASONS = (
    *INCORPORATED_NINE_FINDING_VIOLATION_REASONS[:9],
    "proposal_disposition_identity_collapse",
    "post_common_mapping_invalid",
    *INCORPORATED_NINE_FINDING_VIOLATION_REASONS[9:],
)

REPAIRED_AUTHORITY_SCHEMA = (
    "governed-execution.nwp-authority-observation-attestation-safe.v1"
)
REPAIRED_AUTHORITY_DOMAIN = REPAIRED_AUTHORITY_SCHEMA + ".identity"
REPAIRED_AUTHORITY_LINEAGE_FIELDS = (
    "program_ref",
    "semantic_attempt_ref",
    "candidate_ref",
    "effect_intent_ref",
    "author_command_ref",
    "attempt_fence_ref",
    "effect_fence_ref",
    "delivery_attempt_ref",
)
REPAIRED_C2B3D_LINEAGE_FIELDS = (
    "program_ref",
    "program_version_ref",
    "program_version_number",
    "accepted_intent_revision_ref",
    "work_item_ref",
    "work_item_revision_ref",
    "semantic_attempt_ref",
    "semantic_attempt_digest",
    "attempt_number",
    "candidate_ref",
    "basis_decision_ref",
    "basis_decision_digest",
    "work_spec_ref",
    "work_spec_digest",
    "work_spec_safe_projection_digest",
    "effect_intent_ref",
    "effect_intent_digest",
    "author_command_ref",
    "author_command_digest",
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
    "delivery_attempt_ref",
    "delivery_envelope_digest",
    "delivery_attempt_digest",
    "authority_evaluation_ref",
    "authority_evaluation_digest",
)
REPAIRED_C2B3D_LINEAGE_FIELD_SPECS = (
    ("program_ref", "safe_ref"),
    ("program_version_ref", "safe_ref"),
    ("program_version_number", "positive_int"),
    ("accepted_intent_revision_ref", "safe_ref"),
    ("work_item_ref", "safe_ref"),
    ("work_item_revision_ref", "safe_ref"),
    ("semantic_attempt_ref", "safe_ref"),
    ("semantic_attempt_digest", "sha256"),
    ("attempt_number", "positive_int"),
    ("candidate_ref", "safe_ref"),
    ("basis_decision_ref", "safe_ref"),
    ("basis_decision_digest", "sha256"),
    ("work_spec_ref", "safe_ref"),
    ("work_spec_digest", "sha256"),
    ("work_spec_safe_projection_digest", "sha256"),
    ("effect_intent_ref", "safe_ref"),
    ("effect_intent_digest", "sha256"),
    ("author_command_ref", "safe_ref"),
    ("author_command_digest", "sha256"),
    ("standing_grant_ref", "safe_ref"),
    ("standing_grant_digest", "sha256"),
    ("attempt_authorization_ref", "safe_ref"),
    ("attempt_authorization_digest", "sha256"),
    ("effect_authorization_ref", "safe_ref"),
    ("effect_authorization_digest", "sha256"),
    ("attempt_fence_ref", "safe_ref"),
    ("attempt_fence_digest", "sha256"),
    ("effect_fence_ref", "safe_ref"),
    ("effect_fence_digest", "sha256"),
    ("delivery_attempt_ref", "safe_ref"),
    ("delivery_envelope_digest", "sha256"),
    ("delivery_attempt_digest", "sha256"),
    ("authority_evaluation_ref", "safe_ref"),
    ("authority_evaluation_digest", "sha256"),
)
assert tuple(
    field for field, _kind in REPAIRED_C2B3D_LINEAGE_FIELD_SPECS
) == REPAIRED_C2B3D_LINEAGE_FIELDS
REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS = REPAIRED_AUTHORITY_LINEAGE_FIELDS
REPAIRED_SELECTION_HEAD_REPEATED_LINEAGE_FIELDS = (
    "program_ref",
    "program_version_ref",
    "accepted_intent_revision_ref",
    "work_item_ref",
    "work_item_revision_ref",
    "semantic_attempt_ref",
    "candidate_ref",
    "effect_intent_ref",
    "author_command_ref",
    "author_command_digest",
    "attempt_fence_ref",
    "attempt_fence_digest",
    "effect_fence_ref",
    "effect_fence_digest",
    "delivery_attempt_ref",
    "delivery_envelope_digest",
)
REPAIRED_SELECTION_HEAD_IMMUTABLE_FIELDS = (
    "schema_id",
    "program_ref",
    "program_version_ref",
    "accepted_intent_revision_ref",
    "work_item_ref",
    "work_item_revision_ref",
    "semantic_attempt_ref",
    "candidate_ref",
    "effect_intent_ref",
    "author_command_ref",
    "author_command_digest",
    "attempt_fence_ref",
    "attempt_fence_digest",
    "effect_fence_ref",
    "effect_fence_digest",
    "delivery_attempt_ref",
    "delivery_envelope_digest",
)
REPAIRED_SELECTION_HEAD_MUTABLE_CAS_FIELDS = (
    "current_proposal_ref",
    "current_disposition_ref",
    "current_disposition",
    "head_revision",
    "updated_at",
    "head_digest",
)
REPAIRED_AUTHORITY_FIELDS = (
    "schema_id",
    "authority_observation_ref",
    "authoritative_subject_kind",
    "authoritative_subject_ref",
    *REPAIRED_AUTHORITY_LINEAGE_FIELDS,
    "authority_evaluation_ref",
    "authority_evaluation_digest",
    "observation_state",
    "observation_version",
    "authority_observation_issued_at",
    "authority_observation_expires_at",
    "source_authority_ref",
    "verification_evidence_ref",
    "verification_evidence_digest",
    "authority_observation_digest",
)
REPAIRED_AUTHORITY_EXPECTED_BINDING_FIELDS = (
    "authoritative_subject_kind",
    "authoritative_subject_ref",
    *REPAIRED_AUTHORITY_LINEAGE_FIELDS,
    "authority_evaluation_ref",
    "authority_evaluation_digest",
    "source_authority_ref",
    "verification_evidence_ref",
    "verification_evidence_digest",
)
REPAIRED_EFFECT_CLASSES = C2A_EFFECT_CLASSES
REPAIRED_EVIDENCE_ROLES = (
    "standing_policy",
    "risk_lane",
    "repository_binding",
    "base_binding",
    "authorized_path_scope",
    "cost_ceiling",
    "token_ceiling",
    "time_ceiling",
    "delivery_ceiling",
    "effect_ceiling",
    "authority_selection_observation",
    "global_stop",
    "validation_requirement",
    "review_requirement",
)
REPAIRED_READINESS_EVIDENCE_ROLE = "qualified_remote_host_readiness"
REPAIRED_PRE_EXECUTION_EVIDENCE_SPECS = tuple(
    (role, rank, True)
    for rank, role in enumerate(REPAIRED_EVIDENCE_ROLES, start=5)
) + ((REPAIRED_READINESS_EVIDENCE_ROLE, 19, False),)
REPAIRED_POST_EXECUTION_EVIDENCE_SPECS = POST_EXECUTION_EVIDENCE_ROLES[:-1]
REPAIRED_PHASE_ALGEBRA = {
    "pre_execution_plan": {
        "source_invocation_proposal_phase": "pre_execution_plan",
        "context_schema_id": SCHEMA_IDS["pre_execution_context"],
        "private_artifact_schema_id": SCHEMA_IDS["pre_execution_artifact"],
        "proposal_schema_id": SCHEMA_IDS["proposal"],
        "safe_projection_schema_id": SCHEMA_IDS["pre_execution_projection"],
        "safe_projection_schema_field_present": True,
        "recommendations": PRE_EXECUTION_RECOMMENDATIONS,
        "evidence_roles": REPAIRED_PRE_EXECUTION_EVIDENCE_SPECS,
        "row_presence": (
            ("development_model_source_invocations", "required"),
            ("development_pre_execution_planning_contexts", "required"),
            ("development_private_proposal_artifact_bindings", "required"),
            ("development_model_proposals", "required"),
            ("development_pre_execution_plan_projections", "required"),
            ("development_model_proposal_evidence_bindings", "required"),
            ("development_pre_execution_dispositions", "required"),
            ("development_pre_execution_selection_heads", "required"),
            ("development_cognitive_mutation_receipts", "required"),
        ),
    },
    "post_execution_semantic_review": {
        "source_invocation_proposal_phase": "post_execution_semantic_review",
        "context_schema_id": SCHEMA_IDS["post_execution_context"],
        "private_artifact_schema_id": SCHEMA_IDS["post_execution_artifact"],
        "proposal_schema_id": SCHEMA_IDS["proposal"],
        "safe_projection_schema_id": SCHEMA_IDS["post_execution_projection"],
        "safe_projection_schema_field_present": True,
        "recommendations": POST_EXECUTION_RECOMMENDATIONS,
        "evidence_roles": REPAIRED_POST_EXECUTION_EVIDENCE_SPECS,
        "evidence_set_rule": "zero_or_complete",
        "row_presence": (
            ("development_model_source_invocations", "required"),
            ("development_pre_execution_planning_contexts", "forbidden"),
            ("development_private_proposal_artifact_bindings", "required"),
            ("development_model_proposals", "required"),
            ("development_pre_execution_plan_projections", "forbidden"),
            ("development_model_proposal_evidence_bindings", "optional"),
            ("development_pre_execution_dispositions", "forbidden"),
            ("development_pre_execution_selection_heads", "forbidden"),
            ("development_cognitive_mutation_receipts", "forbidden"),
        ),
    },
}
SQLITE_INTEGER_MIN = -(2**63)
SQLITE_INTEGER_MAX = 2**63 - 1


def _s41_violate(reason: str) -> None:
    raise _ContractViolation(reason)


def _s41_require_exact_mapping(
    value: object,
    fields: tuple[str, ...],
    reason: str,
) -> dict[str, object] | str:
    if (
        type(value) is not dict
        or any(type(key) is not str for key in value)
        or tuple(value) != fields
    ):
        _s41_violate(reason)
    return value


def _s41_canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8", errors="strict")
    except (
        AssertionError,
        TypeError,
        ValueError,
        UnicodeEncodeError,
        OverflowError,
        KeyError,
        AttributeError,
        IndexError,
        RecursionError,
    ):
        _s41_violate("canonical_value_invalid")


def _s41_digest(domain: str, value: object) -> str:
    assert type(domain) is str and domain
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + _s41_canonical_bytes(value)).hexdigest()


def _s41_string_is_canonical(value: object) -> bool:
    if type(value) is not str or unicodedata.normalize("NFC", value) != value:
        return False
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return False
    return not any(ord(character) < 32 or ord(character) == 127 for character in value)


def _s41_integer_fits_sqlite(value: object) -> bool:
    return (
        type(value) is int
        and SQLITE_INTEGER_MIN <= value <= SQLITE_INTEGER_MAX
    )


def _s41_without(mapping: dict[str, object], field: str) -> dict[str, object]:
    return {key: value for key, value in mapping.items() if key != field}


def _s41_parse_literal(payload: bytes) -> dict[str, object]:
    assert b"\r" not in payload, "REPAIRED_OWNER_LITERAL_INVALID"
    try:
        decoded = payload.decode("utf-8", errors="strict")
        tokens = tokenize.generate_tokens(io.StringIO(decoded).readline)
        assert all(token.type != tokenize.COMMENT for token in tokens)
        expression = ast.parse(decoded, mode="eval")
        assert type(expression) is ast.Expression
        _assert_literal_ast_is_closed(expression)
        value = ast.literal_eval(expression)
    except (
        AssertionError,
        IndentationError,
        SyntaxError,
        tokenize.TokenError,
        UnicodeDecodeError,
        TypeError,
        ValueError,
    ):
        raise AssertionError("REPAIRED_OWNER_LITERAL_INVALID") from None
    assert type(value) is dict, "REPAIRED_OWNER_LITERAL_INVALID"
    _assert_closed_value(value)
    return value


def _parse_repaired_owner(
    source: bytes | None = None,
    *,
    enforce_frozen_bytes: bool = True,
) -> dict[str, object]:
    _prefix, section = _section_41_bytes(
        source,
        enforce_frozen_bytes=enforce_frozen_bytes,
    )
    opening = (REPAIRED_BEGIN_MARKER + "\n\n```python\n").encode("utf-8")
    closing = ("\n```\n\n" + REPAIRED_END_MARKER).encode("utf-8")
    assert section.count(opening) == 1, "REPAIRED_OWNER_BOUNDARY_INVALID"
    assert section.count(closing) == 1, "REPAIRED_OWNER_BOUNDARY_INVALID"
    payload = section.split(opening, 1)[1].split(closing, 1)[0]
    value = _s41_parse_literal(payload)
    assert tuple(value) == ("coordinator_section41_repaired_contract",)
    return value["coordinator_section41_repaired_contract"]


def _parse_reaudit_repair_owner(
    source: bytes | None = None,
    *,
    enforce_frozen_bytes: bool = True,
) -> dict[str, object]:
    _prefix, section = _section_41_bytes(
        source,
        enforce_frozen_bytes=enforce_frozen_bytes,
    )
    opening = (REAUDIT_REPAIR_BEGIN_MARKER + "\n\n```python\n").encode("utf-8")
    closing = ("\n```\n\n" + REAUDIT_REPAIR_END_MARKER).encode("utf-8")
    assert section.count(opening) == 1, "REAUDIT_REPAIR_OWNER_BOUNDARY_INVALID"
    assert section.count(closing) == 1, "REAUDIT_REPAIR_OWNER_BOUNDARY_INVALID"
    payload = section.split(opening, 1)[1].split(closing, 1)[0]
    value = _s41_parse_literal(payload)
    assert tuple(value) == ("coordinator_section41_reaudit_repair",)
    return value["coordinator_section41_reaudit_repair"]


def _parse_a2_revised_repair_owner(
    source: bytes | None = None,
    *,
    enforce_frozen_bytes: bool = True,
) -> dict[str, object]:
    _prefix, section = _section_41_bytes(
        source,
        enforce_frozen_bytes=enforce_frozen_bytes,
    )
    opening = (A2_REVISED_REPAIR_BEGIN_MARKER + "\n\n```python\n").encode(
        "utf-8"
    )
    closing = ("\n```\n\n" + A2_REVISED_REPAIR_END_MARKER).encode("utf-8")
    assert section.count(opening) == 1, "A2_REVISED_REPAIR_OWNER_BOUNDARY_INVALID"
    assert section.count(closing) == 1, "A2_REVISED_REPAIR_OWNER_BOUNDARY_INVALID"
    payload = section.split(opening, 1)[1].split(closing, 1)[0]
    value = _s41_parse_literal(payload)
    assert tuple(value) == ("coordinator_section41_a2_revised_repair",)
    return value["coordinator_section41_a2_revised_repair"]


def test_a2_revised_repair_owner_is_exact_and_finitely_scoped() -> None:
    owner = _parse_a2_revised_repair_owner()
    assert tuple(owner) == (
        "contract_identity",
        "database_owned_evidence_inventory",
        "selection_head_graph_locator",
        "regenerated_identity_ledger",
        "predecessor_relation_two_layer_proof",
        "recovery_readback",
        "recovery_identity_inventory",
        "preserved_boundaries",
    )
    identity = owner["contract_identity"]
    assert identity["superseded_relations"] == (
        "S41-REAUDIT-A2-001",
        "S41-REAUDIT-A2-002",
        "S41-REAUDIT-A2-003",
    )
    assert identity["all_other_section41_relations_preserved"] is True
    assert identity["sections_1_40_preserved"] is True
    assert identity["c2b3d_current_and_unchanged"] is True
    assert identity["production_source_schema_migration_or_public_API_changed"] is False

    evidence = owner["database_owned_evidence_inventory"]
    assert evidence["lookup_authority"] == "exact receipt-owned proposal_ref"
    assert evidence["where_predicate"] == "proposal_ref=?"
    assert evidence["other_prefilters"] == ()
    assert evidence["complete_field_order"] == _EVIDENCE_RECOVERY_FIELDS
    assert evidence["canonical_order"] == _EVIDENCE_INVENTORY_ORDER_FIELDS
    assert evidence["read_limit"] == _EVIDENCE_INVENTORY_LIMIT == 16
    assert evidence["overflow_sentinel_row"] == 16
    assert (evidence["readiness_absent_count"], evidence["readiness_present_count"]) == (
        14,
        15,
    )
    assert evidence["position"].endswith("exact-postimage depth zero")
    assert evidence["clock_write_COMMIT_retry_or_external_effect"] is False

    locator = owner["selection_head_graph_locator"]
    assert locator["field_order"] == REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS
    assert locator["field_count"] == 8
    assert locator["equals_unchanged_currentness_primary_key"] is True
    assert locator["uses_full_34_lineage"] is False
    assert locator["full_34_lineage_remains_complete_immutable_row_and_self_digest_input"] is True
    assert locator["readiness_absent_row_and_graph_counts"] == (22, 21)
    assert locator["readiness_present_row_and_graph_counts"] == (23, 22)

    ledger = owner["regenerated_identity_ledger"]
    for variant in ("readiness_absent", "readiness_present"):
        expected = INDEPENDENT_REPAIRED_DIGEST_LEDGER[variant]
        assert ledger[variant] == {
            "graph_digest": expected["graph_digest"],
            "result_projection_digest": expected["result_digest"],
            "receipt_digest": expected["receipt_digest"],
            "canonical_object_ledger": expected["canonical_object_ledger"],
        }
    assert ledger["non_graph_row_digests_unchanged_except_receipt"] is True
    assert ledger["command_and_evidence_set_digests_unchanged"] is True
    assert ledger["independent_oracle_recomputed_every_entry"] is True

    proof = owner["predecessor_relation_two_layer_proof"]
    assert proof["relation_width"] == 37
    assert proof["lineage_prefix_count"] == 34
    assert proof["layer_A"] == {
        "schema_source": "mechanically extracted relation columns and installed column types",
        "unrelated_constraints": (),
        "matching_control_inserts": True,
        "all_34_single_local_coordinate_mutants_rejected": True,
        "same_34_mutants_with_extracted_relation_absent_insert": True,
        "rollback_and_foreign_key_check_clean": True,
    }
    layer_b = proof["layer_B"]
    assert layer_b["target_exclusive_coordinate_order"] == (
        REVISED_LAYER_B_TARGET_EXCLUSIVE_FIELDS
    )
    assert layer_b["overlapping_coordinate_order"] == (
        REVISED_LAYER_B_OVERLAPPING_FIELDS
    )
    assert (layer_b["target_exclusive_count"], layer_b["overlapping_count"]) == (
        23,
        11,
    )
    assert layer_b["bounded_alternate_parent_isolatable"] == tuple(
        REVISED_LAYER_B_ALTERNATE_PARENT_ISOLATABLE.items()
    )
    assert layer_b["generic_FK_message_is_all_34_coverage_proof"] is False
    assert layer_b["inherited_constraint_removed_relaxed_or_rewritten"] is False

    readback = owner["recovery_readback"]
    assert readback["value_fields"] == _RecoveryReadback._fields
    assert readback["classification_vocabulary"] == (
        "committed_exact",
        "definitely_not_committed",
        "unresolved",
    )
    assert readback["exact_depths"] == (0, 1, 256)
    assert readback["overflow_depth_and_classification"] == (257, "unresolved")
    assert (readback["clock_calls"], readback["writes"], readback["COMMIT_attempts"]) == (
        0,
        0,
        0,
    )

    identity_inventory = owner["recovery_identity_inventory"]
    assert identity_inventory["historical_29_probe_statement"] == (
        "explicitly superseded"
    )
    derived_count = sum(
        len(identities) for identities in REPAIRED_RECOVERY_IDENTITY_FIELDS.values()
    )
    assert identity_inventory["active_probe_count"] == derived_count == 30
    assert identity_inventory["count_is_derived_not_independently_hard_coded"] is True


def test_reaudit_repair_owner_is_exact_and_finitely_scoped() -> None:
    owner = _parse_reaudit_repair_owner()
    assert tuple(owner) == (
        "contract_identity",
        "finite_reasons",
        "strict_fresh_and_persisted_chronology",
        "canonical_c2b3d_lineage",
        "physical_lineage_contract",
        "recovery_lineage_contract",
        "proposal_disposition_identity_noncollapse",
        "independent_post_common_mapping_safety",
        "preserved_boundaries",
    )
    identity = owner["contract_identity"]
    assert identity["superseded_relations"] == (
        "S41-REAUDIT-001",
        "S41-REAUDIT-002",
        "S41-REAUDIT-003",
        "S41-REAUDIT-004",
    )
    assert identity["all_other_section41_relations_preserved"] is True
    assert identity["sections_1_40_preserved"] is True
    assert identity["c2b3d_current_and_unchanged"] is True
    assert identity["selection_head_currentness_key_redefined"] is False
    assert (
        identity["production_source_schema_migration_or_public_API_changed"]
        is False
    )
    assert owner["finite_reasons"] == {
        "chronology": "preselection_chronology_invalid",
        "identity_noncollapse": "proposal_disposition_identity_collapse",
        "post_common_mapping": "post_common_mapping_invalid",
        "physical_lineage": "physical_family_row_digest_mismatch",
        "recovery": "recovery_unresolved",
    }
    chronology = owner["strict_fresh_and_persisted_chronology"]
    assert chronology["ordered_relations"][6] == (
        "proposal_created_at < coordinator_disposition_decided_at"
    )
    assert chronology["proposal_decision_equality_accepted"] is False
    assert chronology["fresh_clock_calls"] == 1
    assert chronology["replay_clock_calls"] == 0
    assert chronology["recovery_clock_calls"] == 0
    lineage = owner["canonical_c2b3d_lineage"]
    assert lineage["field_kind_order"] == REPAIRED_C2B3D_LINEAGE_FIELD_SPECS
    assert lineage["field_count"] == 34
    assert (
        lineage["selection_head_currentness_key_field_order"]
        == REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS
    )
    assert lineage["selection_head_currentness_key_field_count"] == 8
    assert lineage["currentness_key_is_not_full_lineage"] is True
    assert lineage["disposition_stores_and_self_digests_all_34"] is True
    assert lineage["successor_stores_and_self_digests_all_34"] is True
    assert lineage["selection_head_stores_and_self_digests_all_34"] is True
    physical = owner["physical_lineage_contract"]
    assert "unchanged ordered eight-field" in physical["selection_head_primary_key"]
    assert physical["selection_head_full_lineage_unique"] is True
    assert physical["digest_only_lineage_substitute"] is False
    assert physical["every_added_full_lineage_coordinate_immutable_on_selection_head_update"] is True
    recovery = owner["recovery_lineage_contract"]
    assert "eight-field currentness key" in recovery["head_lookup"]
    assert "all 34 coordinates" in recovery["head_post_fetch"]
    assert recovery["exact_postimage_may_return_before_collision_and_successor_probes"] is False
    assert recovery["maximum_predecessor_transitions"] == 256
    assert recovery["overflow_sentinel_transition"] == 257
    noncollapse = owner["proposal_disposition_identity_noncollapse"]
    assert noncollapse["typed_identities_distinct"] is True
    assert noncollapse["persisted_scalar_refs_must_be_unequal"] is True
    assert noncollapse["type_qualified_equal_scalar_exception"] is False
    assert noncollapse["DDL_constraint"] == "CHECK(disposition_ref != proposal_ref)"
    mapping = owner["independent_post_common_mapping_safety"]
    assert mapping["validation_order"] == (
        "exact built-in dict",
        "exact key count",
        "every key type is exactly built-in str",
        "exact ordered key inventory",
        "exact declared value types",
        "recursive value validation and canonicalization",
    )
    assert mapping["malformed_reason"] == "post_common_mapping_invalid"
    assert mapping["raw_exception_escapes"] is False


def test_repaired_owner_is_the_only_current_closed_semantic_owner() -> None:
    owner = _parse_repaired_owner()
    assert tuple(owner) == (
        "contract_identity",
        "authority_selection_observation",
        "timestamp_ownership",
        "transaction_clock_order",
        "phase_algebra",
        "private_plan_grammar",
        "safe_projection_derivation",
        "canonical_physical_family",
        "migration_0003_contract",
        "recovery_query_and_proof",
        "causal_oracle",
        "nine_finding_repair",
        "preserved_boundaries",
    )
    identity = owner["contract_identity"]
    assert identity["workstream"] == "COORDINATOR_SECTION41_NINE_FINDING_REPAIR"
    assert identity["status"] == (
        "uncommitted repaired contract candidate pending fresh independent re-audit"
    )
    assert identity["opening_snapshot_is_current_authority"] is False
    assert identity["opening_snapshot_is_immutable_incorporated_basis"] is True
    assert identity["all_non_superseded_opening_semantics_remain_operative"] is True
    assert identity["repair_precedence"] == (
        "every relation selected by this repaired literal finitely supersedes the "
        "corresponding opening-snapshot relation"
    )
    assert identity["c2b3d_current_and_unchanged"] is True
    assert identity["findings_repaired"] == (
        "IA-S41-002-01",
        "IA-S41-002-02",
        "IA-S41-003-01",
        "IA-S41-004-01",
        "IA-S41-004-02",
        "IA-S41-005-01",
        "IA-S41-006-01",
        "IA-S41-007-01",
    )
    assert identity["latest_audit_findings_repaired"] == (
        "A1-S41-001_SELECTION_HEAD_TRIGGER_UNDERCOVERAGE",
        "A1-S41-002_POST_EVIDENCE_GATE_UNBOUND",
        "A1-S41-003_POST_COMMON_CROSSROW_UNDERBINDING",
        "A2-S41-003-01",
        "IA3-S41-006-01",
        "IA3-S41-006-02",
        "IA3-S41-006-03",
        "IA3-S41-006-04",
        "IA-S41-ORACLE-001",
    )
    assert identity["F3_private_artifact_canonical_byte_ceiling_preserved"] is True
    assert owner["causal_oracle"]["exact_violation_reasons"] == (
        INCORPORATED_NINE_FINDING_VIOLATION_REASONS
    )
    assert owner["preserved_boundaries"] == {
        "one_configured_replaceable_reasoning_model_sufficient": True,
        "model_proposal_and_coordinator_disposition_distinct": True,
        "provider_session_or_raw_response_is_durable_truth": False,
        "private_normalized_plan_stored_in_coordinator_sqlite": False,
        "model_adapter_has_coordinator_sqlite_authority": False,
        "worker_has_coordinator_writer_session_authority": False,
        "host_readiness_required_for_nonexecuting_planning": False,
        "host_readiness_required_before_later_effects": True,
        "direct_local_bootstrap_route": "one qualified remote Linux host; never Mac or Coordinator host",
        "transport_checkpoint_is_phase_completion": False,
        "post_execution_coordinator_decision_family_selected_now": False,
        "production_source_or_sql_added": False,
        "model_provider_worker_transport_or_external_effect_invoked": False,
    }


def _s41_require_safe_ref(value: object, reason: str) -> None:
    if not _s41_string_is_canonical(value) or re.fullmatch(
        r"[0-9A-Za-z][0-9A-Za-z.-]{0,95}", value
    ) is None:
        _s41_violate(reason)
    if value.casefold().startswith(("connector-", "tunnel-", "workspace-", "org-", "organization-", "user-")):
        _s41_violate(reason)


def _s41_require_sha256(value: object, reason: str) -> None:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        _s41_violate(reason)


def _s41_require_utc_second(value: object, reason: str) -> None:
    if type(value) is not str or re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z",
        value,
    ) is None:
        _s41_violate(reason)
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        _s41_violate(reason)
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        _s41_violate(reason)


def _build_authority_observation(
    *,
    state: str = "verified",
    version: int = 7,
    issued_at: str = "2026-08-22T12:34:57Z",
    expires_at: str = "2026-08-22T13:34:55Z",
) -> dict[str, object]:
    observation: dict[str, object] = {
        "schema_id": REPAIRED_AUTHORITY_SCHEMA,
        "authority_observation_ref": "authority-observation.supplied.0007",
        "authoritative_subject_kind": "effect_intent",
        "authoritative_subject_ref": C2B3D_BASIS["effect_intent_ref"],
        **{field: C2B3D_BASIS[field] for field in REPAIRED_AUTHORITY_LINEAGE_FIELDS},
        "authority_evaluation_ref": C2B3D_BASIS["authority_evaluation_ref"],
        "authority_evaluation_digest": C2B3D_BASIS["authority_evaluation_digest"],
        "observation_state": state,
        "observation_version": version,
        "authority_observation_issued_at": issued_at,
        "authority_observation_expires_at": expires_at,
        "source_authority_ref": "external-authority.policy.0001",
        "verification_evidence_ref": "authority-verification.safe.0007",
        "verification_evidence_digest": "a" * 64,
    }
    observation["authority_observation_digest"] = _s41_digest(
        REPAIRED_AUTHORITY_DOMAIN,
        observation,
    )
    return observation


def _authority_expected_binding() -> dict[str, object]:
    return {
        "authoritative_subject_kind": "effect_intent",
        "authoritative_subject_ref": C2B3D_BASIS["effect_intent_ref"],
        **{field: C2B3D_BASIS[field] for field in REPAIRED_AUTHORITY_LINEAGE_FIELDS},
        "authority_evaluation_ref": C2B3D_BASIS["authority_evaluation_ref"],
        "authority_evaluation_digest": C2B3D_BASIS["authority_evaluation_digest"],
        "source_authority_ref": "external-authority.policy.0001",
        "verification_evidence_ref": "authority-verification.safe.0007",
        "verification_evidence_digest": "a" * 64,
    }


def _validate_authority_observation_non_temporal(
    observation: object,
    expected_binding: object,
) -> dict[str, object]:
    reason = "authority_observation_shape_invalid"
    observation = _s41_require_exact_mapping(
        observation,
        REPAIRED_AUTHORITY_FIELDS,
        reason,
    )
    if type(observation["schema_id"]) is not str or observation["schema_id"] != REPAIRED_AUTHORITY_SCHEMA:
        _s41_violate(reason)
    for field in (
        "authority_observation_ref",
        "source_authority_ref",
        "verification_evidence_ref",
    ):
        _s41_require_safe_ref(observation[field], reason)
    for field in (
        "authority_evaluation_digest",
        "verification_evidence_digest",
        "authority_observation_digest",
    ):
        _s41_require_sha256(observation[field], reason)
    if observation["authority_observation_digest"] != _s41_digest(
        REPAIRED_AUTHORITY_DOMAIN,
        _s41_without(observation, "authority_observation_digest"),
    ):
        _s41_violate(reason)
    expected_binding = _s41_require_exact_mapping(
        expected_binding,
        REPAIRED_AUTHORITY_EXPECTED_BINDING_FIELDS,
        "authority_observation_binding_mismatch",
    )
    supplied_binding = {
        field: observation[field]
        for field in REPAIRED_AUTHORITY_EXPECTED_BINDING_FIELDS
    }
    if not _s41_exact_equal(supplied_binding, expected_binding):
        _s41_violate("authority_observation_binding_mismatch")
    if (
        not _s41_integer_fits_sqlite(observation["observation_version"])
        or observation["observation_version"] <= 0
    ):
        _s41_violate("authority_observation_version_invalid")
    if (
        not _s41_string_is_canonical(observation["observation_state"])
        or observation["observation_state"] not in ("pending", "verified")
    ):
        _s41_violate("authority_observation_state_ineligible")
    if type(observation["authoritative_subject_kind"]) is not str:
        _s41_violate(reason)
    for field in (
        "authority_observation_issued_at",
        "authority_observation_expires_at",
    ):
        _s41_require_utc_second(observation[field], "authority_observation_window_invalid")
    return observation


REPAIRED_PRESELECTION_RECORD_SPECS = {
    "planning_context": (
        "development_pre_execution_planning_contexts",
        "pre_execution_context",
        "planning_context_digest",
        "pre_execution_context",
    ),
    "source_invocation": (
        "development_model_source_invocations",
        "source_invocation",
        "source_invocation_digest",
        "source_invocation",
    ),
    "artifact_binding": (
        "development_private_proposal_artifact_bindings",
        "artifact_binding",
        "artifact_binding_digest",
        "artifact_binding",
    ),
    "evidence_bindings": (
        "development_model_proposal_evidence_bindings",
        "evidence_binding",
        "evidence_binding_digest",
        "evidence_binding",
    ),
    "model_proposal": (
        "development_model_proposals",
        "proposal",
        "proposal_digest",
        "proposal",
    ),
}
REPAIRED_EVIDENCE_SET_FIELDS = (
    "evidence_set_ref",
    "proposal_ref",
    "proposal_phase",
    "entries",
    "evidence_set_digest",
)
REPAIRED_EVIDENCE_SET_ENTRY_FIELDS = (
    "evidence_role",
    "role_rank",
    "ordinal",
    "evidence_ref",
    "evidence_digest",
    "evidence_binding_digest",
)


_HISTORICAL_CURRENTNESS_FIELDS = (
    "authority_attestation_schema_id",
    "authority_attestation_ref",
    "authoritative_subject_kind",
    "authoritative_subject_ref",
    "authority_state",
    "authority_version",
    "authority_issued_at",
    "authority_expires_at",
    "authority_source_ref",
    "authority_attestation_digest",
)
REPAIRED_PLANNING_CONTEXT_OBSERVATION_FIELDS = (
    "authority_selection_observation_schema_id",
    "authority_selection_observation_ref",
    "authoritative_subject_kind",
    "authoritative_subject_ref",
    "authority_observation_state",
    "authority_observation_version",
    "authority_observation_issued_at",
    "authority_observation_expires_at",
    "source_authority_ref",
    "verification_evidence_ref",
    "verification_evidence_digest",
    "authority_selection_observation_digest",
)
_OPENING_PLANNING_CONTEXT_COLUMNS = TABLE_CONTRACTS[
    "development_pre_execution_planning_contexts"
]["columns"]
REPAIRED_PLANNING_CONTEXT_COLUMNS = tuple(
    (
        (
            ("authority_selection_observation_schema_id", f"literal:{REPAIRED_AUTHORITY_SCHEMA}"),
            ("authority_selection_observation_ref", "safe_ref"),
            ("authoritative_subject_kind", "literal:effect_intent"),
            ("authoritative_subject_ref", "safe_ref"),
            ("authority_observation_state", "authority_observation_state"),
            ("authority_observation_version", "positive_int"),
            ("authority_observation_issued_at", "utc_second"),
            ("authority_observation_expires_at", "utc_second"),
            ("source_authority_ref", "safe_ref"),
            ("verification_evidence_ref", "safe_ref"),
            ("verification_evidence_digest", "sha256"),
            ("authority_selection_observation_digest", "sha256"),
        )
        if name == "authority_attestation_schema_id"
        else ((name, kind),)
    )
    for name, kind in _OPENING_PLANNING_CONTEXT_COLUMNS
    if name == "authority_attestation_schema_id" or name not in _HISTORICAL_CURRENTNESS_FIELDS
)
REPAIRED_PLANNING_CONTEXT_COLUMNS = tuple(
    item for group in REPAIRED_PLANNING_CONTEXT_COLUMNS for item in group
)
REPAIRED_PLANNING_CONTEXT_FIELDS = tuple(
    name for name, _kind in REPAIRED_PLANNING_CONTEXT_COLUMNS
)


def _sample_preselection_records(
    observation: dict[str, object] | None = None,
    readiness_present: bool = False,
) -> dict[str, object]:
    selected_observation = (
        _build_authority_observation() if observation is None else observation
    )
    assert type(readiness_present) is bool
    vector = _build_golden_vector(readiness_present)
    historical_context = deepcopy(vector["planning_context"])
    replacement = {
        "authority_selection_observation_schema_id": selected_observation["schema_id"],
        "authority_selection_observation_ref": selected_observation["authority_observation_ref"],
        "authoritative_subject_kind": selected_observation["authoritative_subject_kind"],
        "authoritative_subject_ref": selected_observation["authoritative_subject_ref"],
        "authority_observation_state": selected_observation["observation_state"],
        "authority_observation_version": selected_observation["observation_version"],
        "authority_observation_issued_at": selected_observation["authority_observation_issued_at"],
        "authority_observation_expires_at": selected_observation["authority_observation_expires_at"],
        "source_authority_ref": selected_observation["source_authority_ref"],
        "verification_evidence_ref": selected_observation["verification_evidence_ref"],
        "verification_evidence_digest": selected_observation["verification_evidence_digest"],
        "authority_selection_observation_digest": selected_observation["authority_observation_digest"],
    }
    planning_context = {
        field: (
            replacement[field]
            if field in replacement
            else historical_context[field]
        )
        for field in REPAIRED_PLANNING_CONTEXT_FIELDS
    }
    planning_context["planning_context_digest"] = _s41_digest(
        DIGEST_DOMAINS["pre_execution_context"],
        _s41_without(planning_context, "planning_context_digest"),
    )
    source_invocation = deepcopy(vector["source_invocation"])
    source_invocation["context_digest"] = planning_context["planning_context_digest"]
    source_invocation["source_invocation_digest"] = _s41_digest(
        DIGEST_DOMAINS["source_invocation"],
        _s41_without(source_invocation, "source_invocation_digest"),
    )
    evidence_bindings = list(
        deepcopy(
            vector["migration_0003_rows_by_table"][
                "development_model_proposal_evidence_bindings"
            ]
        )
    )
    authority_row = next(row for row in evidence_bindings if row["role_rank"] == 15)
    authority_row["evidence_role"] = "authority_selection_observation"
    authority_row["evidence_ref"] = selected_observation["authority_observation_ref"]
    authority_row["evidence_digest"] = selected_observation["authority_observation_digest"]
    authority_row["evidence_binding_digest"] = _s41_digest(
        DIGEST_DOMAINS["evidence_binding"],
        _s41_without(authority_row, "evidence_binding_digest"),
    )
    evidence_bindings_tuple = tuple(evidence_bindings)
    evidence_set = deepcopy(vector["evidence_set"])
    evidence_set["entries"] = tuple(
        {
            "evidence_role": row["evidence_role"],
            "role_rank": row["role_rank"],
            "ordinal": row["ordinal"],
            "evidence_ref": row["evidence_ref"],
            "evidence_digest": row["evidence_digest"],
            "evidence_binding_digest": row["evidence_binding_digest"],
        }
        for row in evidence_bindings_tuple
    )
    evidence_set["evidence_set_digest"] = _s41_digest(
        DIGEST_DOMAINS["evidence_set"],
        _s41_without(evidence_set, "evidence_set_digest"),
    )
    model_proposal = deepcopy(vector["pre_execution_proposal"])
    model_proposal["source_invocation_digest"] = source_invocation["source_invocation_digest"]
    model_proposal["context_digest"] = planning_context["planning_context_digest"]
    model_proposal["evidence_set_digest"] = evidence_set["evidence_set_digest"]
    model_proposal["proposal_digest"] = _s41_digest(
        DIGEST_DOMAINS["proposal"],
        _s41_without(model_proposal, "proposal_digest"),
    )
    return {
        "planning_context": planning_context,
        "source_invocation": source_invocation,
        "artifact_binding": deepcopy(vector["private_artifact_binding"]),
        "evidence_bindings": evidence_bindings_tuple,
        "model_proposal": model_proposal,
        "evidence_set": evidence_set,
    }


def _validate_one_timestamp_record(
    role: str,
    record: object,
) -> None:
    reason = "preselection_timestamp_record_invalid"
    table, schema_key, digest_field, domain_key = REPAIRED_PRESELECTION_RECORD_SPECS[role]
    columns = (
        REPAIRED_PLANNING_CONTEXT_COLUMNS
        if role == "planning_context"
        else TABLE_CONTRACTS[table]["columns"]
    )
    field_order = tuple(name for name, _kind in columns)
    record = _s41_require_exact_mapping(record, field_order, reason)
    if record["schema_id"] != SCHEMA_IDS[schema_key]:
        _s41_violate(reason)
    column_kinds = dict(columns)
    for field, value in record.items():
        if column_kinds[field] == "sha256":
            _s41_require_sha256(value, reason)
        elif column_kinds[field] == "utc_second":
            _s41_require_utc_second(value, reason)
    if record[digest_field] != _s41_digest(
        DIGEST_DOMAINS[domain_key],
        _s41_without(record, digest_field),
    ):
        _s41_violate("preselection_timestamp_digest_mismatch")


def _validate_preselection_timestamp_records(records: object) -> None:
    reason = "preselection_timestamp_record_invalid"
    records = _s41_require_exact_mapping(
        records,
        (*REPAIRED_PRESELECTION_RECORD_SPECS, "evidence_set"),
        reason,
    )
    for role in ("planning_context", "source_invocation", "artifact_binding", "model_proposal"):
        _validate_one_timestamp_record(role, records[role])
    expected_evidence_specs = _expected_active_preselection_evidence_specs(
        records,
        reason,
    )
    evidence_rows = records["evidence_bindings"]
    if (
        type(evidence_rows) is not tuple
        or len(evidence_rows) != len(expected_evidence_specs)
    ):
        _s41_violate(reason)
    for row in evidence_rows:
        _validate_one_timestamp_record("evidence_bindings", row)
    evidence_set = records["evidence_set"]
    evidence_set = _s41_require_exact_mapping(
        evidence_set,
        REPAIRED_EVIDENCE_SET_FIELDS,
        reason,
    )
    evidence_set_entries = evidence_set["entries"]
    if (
        type(evidence_set_entries) is not tuple
        or len(evidence_set_entries) != len(expected_evidence_specs)
    ):
        _s41_violate(reason)
    for entry in evidence_set_entries:
        _s41_require_exact_mapping(entry, REPAIRED_EVIDENCE_SET_ENTRY_FIELDS, reason)
    expected_entries = tuple(
        {
            "evidence_role": row["evidence_role"],
            "role_rank": row["role_rank"],
            "ordinal": row["ordinal"],
            "evidence_ref": row["evidence_ref"],
            "evidence_digest": row["evidence_digest"],
            "evidence_binding_digest": row["evidence_binding_digest"],
        }
        for row in evidence_rows
    )
    if not _s41_exact_equal(evidence_set["entries"], expected_entries):
        _s41_violate("preselection_timestamp_digest_mismatch")
    _s41_require_sha256(evidence_set["evidence_set_digest"], reason)
    if evidence_set["evidence_set_digest"] != _s41_digest(
        DIGEST_DOMAINS["evidence_set"],
        _s41_without(evidence_set, "evidence_set_digest"),
    ):
        _s41_violate("preselection_timestamp_digest_mismatch")
    planning_context = records["planning_context"]
    source_invocation = records["source_invocation"]
    artifact_binding = records["artifact_binding"]
    proposal = records["model_proposal"]
    cross_bindings = (
        (source_invocation["context_ref"], planning_context["planning_context_ref"]),
        (source_invocation["context_digest"], planning_context["planning_context_digest"]),
        (proposal["context_ref"], planning_context["planning_context_ref"]),
        (proposal["context_digest"], planning_context["planning_context_digest"]),
        (source_invocation["artifact_ref"], artifact_binding["artifact_ref"]),
        (source_invocation["artifact_digest"], artifact_binding["artifact_digest"]),
        (proposal["artifact_ref"], artifact_binding["artifact_ref"]),
        (proposal["artifact_digest"], artifact_binding["artifact_digest"]),
        (proposal["source_invocation_ref"], source_invocation["source_invocation_ref"]),
        (proposal["source_invocation_digest"], source_invocation["source_invocation_digest"]),
        (proposal["evidence_set_ref"], evidence_set["evidence_set_ref"]),
        (proposal["evidence_set_digest"], evidence_set["evidence_set_digest"]),
    )
    if any(not _s41_exact_equal(left, right) for left, right in cross_bindings):
        _s41_violate("preselection_timestamp_digest_mismatch")


def _validate_observation_context_binding(
    observation: dict[str, object],
    records: dict[str, object],
) -> None:
    context = records["planning_context"]
    expected = {
        "authority_selection_observation_schema_id": observation["schema_id"],
        "authority_selection_observation_ref": observation["authority_observation_ref"],
        "authoritative_subject_kind": observation["authoritative_subject_kind"],
        "authoritative_subject_ref": observation["authoritative_subject_ref"],
        "authority_observation_state": observation["observation_state"],
        "authority_observation_version": observation["observation_version"],
        "authority_observation_issued_at": observation["authority_observation_issued_at"],
        "authority_observation_expires_at": observation["authority_observation_expires_at"],
        "source_authority_ref": observation["source_authority_ref"],
        "verification_evidence_ref": observation["verification_evidence_ref"],
        "verification_evidence_digest": observation["verification_evidence_digest"],
        "authority_selection_observation_digest": observation["authority_observation_digest"],
    }
    actual = {field: context[field] for field in expected}
    if not _s41_exact_equal(actual, expected):
        _s41_violate("authority_observation_binding_mismatch")
    rank_15 = tuple(
        row for row in records["evidence_bindings"] if row["role_rank"] == 15
    )
    if len(rank_15) != 1 or not _s41_exact_equal(
        {
            "evidence_role": rank_15[0]["evidence_role"],
            "evidence_ref": rank_15[0]["evidence_ref"],
            "evidence_digest": rank_15[0]["evidence_digest"],
        },
        {
            "evidence_role": "authority_selection_observation",
            "evidence_ref": observation["authority_observation_ref"],
            "evidence_digest": observation["authority_observation_digest"],
        },
    ):
        _s41_violate("authority_observation_binding_mismatch")


def _redigest_preselection_record(records: dict[str, object], role: str) -> None:
    if role == "evidence_bindings":
        for row in records[role]:
            row["evidence_binding_digest"] = _s41_digest(
                DIGEST_DOMAINS["evidence_binding"],
                _s41_without(row, "evidence_binding_digest"),
            )
        evidence_set = records["evidence_set"]
        evidence_set["entries"] = tuple(
            {
                "evidence_role": row["evidence_role"],
                "role_rank": row["role_rank"],
                "ordinal": row["ordinal"],
                "evidence_ref": row["evidence_ref"],
                "evidence_digest": row["evidence_digest"],
                "evidence_binding_digest": row["evidence_binding_digest"],
            }
            for row in records[role]
        )
        evidence_set["evidence_set_digest"] = _s41_digest(
            DIGEST_DOMAINS["evidence_set"],
            _s41_without(evidence_set, "evidence_set_digest"),
        )
        proposal = records["model_proposal"]
        proposal["evidence_set_digest"] = evidence_set["evidence_set_digest"]
        proposal["proposal_digest"] = _s41_digest(
            DIGEST_DOMAINS["proposal"],
            _s41_without(proposal, "proposal_digest"),
        )
        return
    _table, _schema_key, digest_field, domain_key = REPAIRED_PRESELECTION_RECORD_SPECS[role]
    record = records[role]
    record[digest_field] = _s41_digest(
        DIGEST_DOMAINS[domain_key],
        _s41_without(record, digest_field),
    )


def _sample_temporal_bundle(
    readiness_present: bool = False,
) -> dict[str, object]:
    assert type(readiness_present) is bool
    observation = _build_authority_observation()
    c2b3d = _section_39_vector()["canonical_values"]
    return {
        "authority_observation": observation,
        "authority_expected_binding": _authority_expected_binding(),
        "attempt_fence": deepcopy(c2b3d["attempt_fence"]["complete_mapping"]),
        "effect_fence": deepcopy(c2b3d["effect_fence"]["complete_mapping"]),
        "preselection_records": _sample_preselection_records(
            observation,
            readiness_present,
        ),
    }


REPAIRED_TEMPORAL_BUNDLE_FIELDS = (
    "authority_observation",
    "authority_expected_binding",
    "attempt_fence",
    "effect_fence",
    "preselection_records",
)
REPAIRED_ATTEMPT_FENCE_FIELDS = (
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
    "path_ceiling",
    "allowed_effect_classes",
    "aggregate_ceilings",
    "expires_at",
    "global_stop_ref",
    "global_stop_version",
    "attempt_fence_digest",
)
REPAIRED_EFFECT_FENCE_FIELDS = (
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
    "path_ceiling",
    "effect_ceilings",
    "expires_at",
    "global_stop_ref",
    "global_stop_version",
    "portable_capsule_digest",
    "cancellation_target_effect_intent_ref",
    "cancellation_target_effect_fence_ref",
    "cancellation_target_effect_fence_digest",
    "effect_fence_digest",
)


REPAIRED_FENCE_CEILING_FIELDS = (
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
REPAIRED_ACTIVE_RECORD_SHAPE_INVENTORY = (
    ("selection_bundle", "mapping"),
    ("authority_observation", "mapping"),
    ("authority_expected_binding", "mapping"),
    ("attempt_fence", "mapping"),
    ("attempt_fence.path_ceiling", "list"),
    ("attempt_fence.allowed_effect_classes", "list"),
    ("attempt_fence.aggregate_ceilings", "mapping"),
    ("effect_fence", "mapping"),
    ("effect_fence.path_ceiling", "list"),
    ("effect_fence.effect_ceilings", "mapping"),
    ("preselection_records", "mapping"),
    ("planning_context", "mapping"),
    ("source_invocation", "mapping"),
    ("private_artifact_binding", "mapping"),
    ("evidence_bindings", "tuple"),
    ("evidence_binding", "mapping"),
    ("model_proposal", "mapping"),
    ("evidence_set", "mapping"),
    ("evidence_set.entries", "tuple"),
    ("evidence_set.entry", "mapping"),
)
REPAIRED_ACTIVE_SCALAR_KIND_INVENTORY = (
    "literal_string",
    "exact_string_for_later_semantics",
    "safe_ref",
    "nullable_safe_ref",
    "sha256",
    "nullable_sha256",
    "sha1",
    "utc_second",
    "exact_integer_for_later_semantics",
    "positive_integer",
    "nonnegative_integer",
    "bounded_integer",
    "integer_encoded_boolean",
    "canonical_effect_class_json",
    "reason_code",
    "closed_vocabulary_string",
    "required_null",
)

REPAIRED_AUTHORITY_VALUE_KINDS = (
    ("schema_id", f"literal:{REPAIRED_AUTHORITY_SCHEMA}"),
    ("authority_observation_ref", "safe_ref"),
    ("authoritative_subject_kind", "literal:effect_intent"),
    ("authoritative_subject_ref", "safe_ref"),
    ("program_ref", "safe_ref"),
    ("semantic_attempt_ref", "safe_ref"),
    ("candidate_ref", "safe_ref"),
    ("effect_intent_ref", "safe_ref"),
    ("author_command_ref", "safe_ref"),
    ("attempt_fence_ref", "safe_ref"),
    ("effect_fence_ref", "safe_ref"),
    ("delivery_attempt_ref", "safe_ref"),
    ("authority_evaluation_ref", "safe_ref"),
    ("authority_evaluation_digest", "sha256"),
    ("observation_state", "exact_str"),
    ("observation_version", "exact_int"),
    ("authority_observation_issued_at", "utc_second"),
    ("authority_observation_expires_at", "utc_second"),
    ("source_authority_ref", "safe_ref"),
    ("verification_evidence_ref", "safe_ref"),
    ("verification_evidence_digest", "sha256"),
    ("authority_observation_digest", "sha256"),
)
_REPAIRED_AUTHORITY_KIND_BY_FIELD = dict(REPAIRED_AUTHORITY_VALUE_KINDS)
REPAIRED_AUTHORITY_EXPECTED_VALUE_KINDS = tuple(
    (field, _REPAIRED_AUTHORITY_KIND_BY_FIELD[field])
    for field in REPAIRED_AUTHORITY_EXPECTED_BINDING_FIELDS
)
REPAIRED_ATTEMPT_FENCE_VALUE_KINDS = (
    ("schema_id", "literal:governed-execution.nwp-attempt-fence.v1"),
    ("attempt_fence_ref", "safe_ref"),
    ("parent_standing_grant_ref", "safe_ref"),
    ("parent_standing_grant_digest", "sha256"),
    ("attempt_authorization_ref", "safe_ref"),
    ("attempt_authorization_digest", "sha256"),
    ("program_ref", "safe_ref"),
    ("program_version_ref", "safe_ref"),
    ("accepted_intent_revision_ref", "safe_ref"),
    ("work_item_ref", "safe_ref"),
    ("work_item_revision_ref", "safe_ref"),
    ("semantic_attempt_ref", "safe_ref"),
    ("repository_ref", "safe_ref"),
    ("base_git_object_format", "literal:sha1"),
    ("base_git_oid", "sha1"),
    ("path_ceiling", "safe_path_list"),
    ("allowed_effect_classes", "effect_class_list"),
    ("aggregate_ceilings", "ceiling_mapping"),
    ("expires_at", "utc_second"),
    ("global_stop_ref", "safe_ref"),
    ("global_stop_version", "nonnegative_int"),
    ("attempt_fence_digest", "sha256"),
)
REPAIRED_EFFECT_FENCE_VALUE_KINDS = (
    ("schema_id", "literal:governed-execution.nwp-effect-fence.v1"),
    ("effect_fence_ref", "safe_ref"),
    ("parent_standing_grant_ref", "safe_ref"),
    ("parent_standing_grant_digest", "sha256"),
    ("effect_authorization_ref", "safe_ref"),
    ("effect_authorization_digest", "sha256"),
    ("attempt_fence_ref", "safe_ref"),
    ("attempt_fence_digest", "sha256"),
    ("program_ref", "safe_ref"),
    ("program_version_ref", "safe_ref"),
    ("accepted_intent_revision_ref", "safe_ref"),
    ("work_item_ref", "safe_ref"),
    ("work_item_revision_ref", "safe_ref"),
    ("semantic_attempt_ref", "safe_ref"),
    ("effect_intent_ref", "safe_ref"),
    ("effect_class", "literal:author_candidate"),
    ("command_ref", "safe_ref"),
    ("command_digest", "sha256"),
    ("candidate_ref", "safe_ref"),
    ("repository_ref", "safe_ref"),
    ("base_git_object_format", "literal:sha1"),
    ("base_git_oid", "sha1"),
    ("path_ceiling", "safe_path_list"),
    ("effect_ceilings", "ceiling_mapping"),
    ("expires_at", "utc_second"),
    ("global_stop_ref", "safe_ref"),
    ("global_stop_version", "nonnegative_int"),
    ("portable_capsule_digest", "literal_none"),
    ("cancellation_target_effect_intent_ref", "literal_none"),
    ("cancellation_target_effect_fence_ref", "literal_none"),
    ("cancellation_target_effect_fence_digest", "literal_none"),
    ("effect_fence_digest", "sha256"),
)

_REPAIRED_ACTIVE_COLUMN_OVERRIDES = {
    "source_invocation": {
        "proposal_phase": "literal:pre_execution_plan",
        "context_schema_id": f"literal:{SCHEMA_IDS['pre_execution_context']}",
        "artifact_schema_id": f"literal:{SCHEMA_IDS['pre_execution_artifact']}",
    },
    "artifact_binding": {
        "proposal_phase": "literal:pre_execution_plan",
        "artifact_schema_id": f"literal:{SCHEMA_IDS['pre_execution_artifact']}",
        "safe_projection_schema_id": f"literal:{SCHEMA_IDS['pre_execution_projection']}",
    },
    "model_proposal": {
        "proposal_phase": "literal:pre_execution_plan",
        "context_schema_id": f"literal:{SCHEMA_IDS['pre_execution_context']}",
        "artifact_schema_id": f"literal:{SCHEMA_IDS['pre_execution_artifact']}",
        "safe_projection_schema_id": f"literal:{SCHEMA_IDS['pre_execution_projection']}",
        "recommendation": "pre_execution_recommendation",
    },
    "evidence_binding": {
        "proposal_phase": "literal:pre_execution_plan",
    },
}


def _s41_active_columns(
    role: str,
    columns: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    overrides = _REPAIRED_ACTIVE_COLUMN_OVERRIDES.get(role, {})
    return tuple((field, overrides.get(field, kind)) for field, kind in columns)


def _s41_safe_path_list_is_exact(value: object) -> bool:
    if type(value) is not list or not 1 <= len(value) <= len(C2B3D_BASIS["authorized_paths"]):
        return False
    for path in value:
        if not _s41_string_is_canonical(path):
            return False
        try:
            encoded = path.encode("utf-8", errors="strict")
        except UnicodeEncodeError:
            return False
        if not 1 <= len(path) <= 160 or not encoded:
            return False
        if (
            path.startswith(("/", "\\", "~"))
            or "\\" in path
            or ":" in path
            or "//" in path
            or any(part in ("", ".", "..") for part in path.split("/"))
            or any(ord(character) < 32 or ord(character) == 127 for character in path)
            or path not in C2B3D_BASIS["authorized_paths"]
        ):
            return False
    return value == sorted(set(value))


def _s41_effect_class_list_is_exact(value: object) -> bool:
    return (
        type(value) is list
        and 1 <= len(value) <= len(REPAIRED_EFFECT_CLASSES)
        and all(type(item) is str and item in REPAIRED_EFFECT_CLASSES for item in value)
        and len(value) == len(set(value))
        and value == [item for item in REPAIRED_EFFECT_CLASSES if item in value]
    )


def _s41_ceiling_mapping_is_exact(value: object) -> bool:
    return (
        type(value) is dict
        and all(type(key) is str for key in value)
        and tuple(value) == REPAIRED_FENCE_CEILING_FIELDS
        and all(
            _s41_integer_fits_sqlite(item) and item >= 0
            for item in value.values()
        )
    )


def _s41_active_value_matches_kind(value: object, kind: str) -> bool:
    if kind == "exact_str":
        return _s41_string_is_canonical(value)
    if kind == "exact_int":
        return _s41_integer_fits_sqlite(value)
    if kind == "literal_none":
        return value is None
    if kind == "exact_tuple":
        return type(value) is tuple
    if kind == "safe_path_list":
        return _s41_safe_path_list_is_exact(value)
    if kind == "effect_class_list":
        return _s41_effect_class_list_is_exact(value)
    if kind == "ceiling_mapping":
        return _s41_ceiling_mapping_is_exact(value)
    return _repaired_value_matches_kind(value, kind)


def _s41_require_active_record(
    value: object,
    columns: tuple[tuple[str, str], ...],
    reason: str,
) -> dict[str, object]:
    record = _s41_require_exact_mapping(
        value,
        tuple(field for field, _kind in columns),
        reason,
    )
    if any(
        not _s41_active_value_matches_kind(record[field], kind)
        for field, kind in columns
    ):
        _s41_violate(reason)
    return record


def _expected_active_preselection_evidence_specs(
    records: dict[str, object],
    reason: str,
) -> tuple[tuple[str, int, bool], ...]:
    context = records["planning_context"]
    readiness_ref = context["qualified_remote_host_readiness_ref"]
    readiness_digest = context["qualified_remote_host_readiness_digest"]
    if readiness_ref is None and readiness_digest is None:
        return REPAIRED_PRE_EXECUTION_EVIDENCE_SPECS[:-1]
    if (
        _repaired_value_matches_kind(readiness_ref, "safe_ref")
        and _repaired_value_matches_kind(readiness_digest, "sha256")
    ):
        return REPAIRED_PRE_EXECUTION_EVIDENCE_SPECS
    _s41_violate(reason)


def _preflight_selection_bundle_shapes(bundle: object) -> None:
    reason = "preselection_timestamp_record_invalid"
    bundle = _s41_require_exact_mapping(
        bundle,
        REPAIRED_TEMPORAL_BUNDLE_FIELDS,
        reason,
    )
    observation = _s41_require_exact_mapping(
        bundle["authority_observation"],
        tuple(field for field, _kind in REPAIRED_AUTHORITY_VALUE_KINDS),
        "authority_observation_shape_invalid",
    )
    if not _s41_string_is_canonical(observation["observation_state"]):
        _s41_violate("authority_observation_shape_invalid")
    if not _s41_integer_fits_sqlite(observation["observation_version"]):
        _s41_violate("authority_observation_version_invalid")
    _s41_require_active_record(
        observation,
        REPAIRED_AUTHORITY_VALUE_KINDS,
        "authority_observation_shape_invalid",
    )
    _s41_require_active_record(
        bundle["authority_expected_binding"],
        REPAIRED_AUTHORITY_EXPECTED_VALUE_KINDS,
        "authority_observation_binding_mismatch",
    )
    _s41_require_active_record(
        bundle["attempt_fence"],
        REPAIRED_ATTEMPT_FENCE_VALUE_KINDS,
        reason,
    )
    _s41_require_active_record(
        bundle["effect_fence"],
        REPAIRED_EFFECT_FENCE_VALUE_KINDS,
        reason,
    )
    records = _s41_require_exact_mapping(
        bundle["preselection_records"],
        (*REPAIRED_PRESELECTION_RECORD_SPECS, "evidence_set"),
        reason,
    )
    for role in (
        "planning_context",
        "source_invocation",
        "artifact_binding",
        "model_proposal",
    ):
        table = REPAIRED_PRESELECTION_RECORD_SPECS[role][0]
        columns = (
            REPAIRED_PLANNING_CONTEXT_COLUMNS
            if role == "planning_context"
            else TABLE_CONTRACTS[table]["columns"]
        )
        active_columns = _s41_active_columns(role, columns)
        if role == "planning_context":
            active_columns = tuple(
                (
                    field,
                    "exact_str"
                    if field == "authority_observation_state"
                    else "exact_int"
                    if field == "authority_observation_version"
                    else kind,
                )
                for field, kind in active_columns
            )
        _s41_require_active_record(
            records[role],
            active_columns,
            reason,
        )
    expected_evidence_specs = _expected_active_preselection_evidence_specs(
        records,
        reason,
    )
    evidence_rows = records["evidence_bindings"]
    if (
        type(evidence_rows) is not tuple
        or len(evidence_rows) != len(expected_evidence_specs)
    ):
        _s41_violate(reason)
    evidence_columns = _s41_active_columns(
        "evidence_binding",
        TABLE_CONTRACTS["development_model_proposal_evidence_bindings"]["columns"],
    )
    for row, (expected_role, expected_rank, required) in zip(
        evidence_rows,
        expected_evidence_specs,
        strict=True,
    ):
        row = _s41_require_active_record(row, evidence_columns, reason)
        if not (
            row["evidence_role"] == expected_role
            and row["role_rank"] == expected_rank
            and row["ordinal"] == 0
            and row["required_for_selection"] == int(required)
        ):
            _s41_violate(reason)
        if expected_role == REPAIRED_READINESS_EVIDENCE_ROLE and not (
            row["evidence_ref"]
            == records["planning_context"]["qualified_remote_host_readiness_ref"]
            and row["evidence_digest"]
            == records["planning_context"]["qualified_remote_host_readiness_digest"]
        ):
            _s41_violate(reason)
    evidence_set = _s41_require_active_record(
        records["evidence_set"],
        (
            ("evidence_set_ref", "safe_ref"),
            ("proposal_ref", "safe_ref"),
            ("proposal_phase", "literal:pre_execution_plan"),
            ("entries", "exact_tuple"),
            ("evidence_set_digest", "sha256"),
        ),
        reason,
    )
    entries = evidence_set["entries"]
    if type(entries) is not tuple or len(entries) != len(expected_evidence_specs):
        _s41_violate(reason)
    entry_columns = (
        ("evidence_role", "phase_evidence_role"),
        ("role_rank", "phase_evidence_rank"),
        ("ordinal", "literal_int:0"),
        ("evidence_ref", "safe_ref"),
        ("evidence_digest", "sha256"),
        ("evidence_binding_digest", "sha256"),
    )
    for entry, (expected_role, expected_rank, _required) in zip(
        entries,
        expected_evidence_specs,
        strict=True,
    ):
        entry = _s41_require_active_record(entry, entry_columns, reason)
        if not (
            entry["evidence_role"] == expected_role
            and entry["role_rank"] == expected_rank
            and entry["ordinal"] == 0
        ):
            _s41_violate(reason)


def _validate_fence_records_non_temporal(bundle: dict[str, object]) -> None:
    records = bundle["preselection_records"]
    context = records["planning_context"]
    specifications = (
        (
            "attempt_fence",
            "attempt_fence_ref",
            "attempt_fence_digest",
            "governed-execution.nwp-attempt-fence.v1.identity",
            "allowed_effect_classes",
            "attempt_fence_allowed_effect_classes_json",
            "attempt_fence_expires_at",
        ),
        (
            "effect_fence",
            "effect_fence_ref",
            "effect_fence_digest",
            "governed-execution.nwp-effect-fence.v1.identity",
            "effect_class",
            "effect_fence_allowed_effect_classes_json",
            "effect_fence_expires_at",
        ),
    )
    for (
        bundle_field,
        ref_field,
        digest_field,
        domain,
        effects_field,
        context_effects_field,
        context_expiry_field,
    ) in specifications:
        fence = _s41_require_exact_mapping(
            bundle[bundle_field],
            (
                REPAIRED_ATTEMPT_FENCE_FIELDS
                if bundle_field == "attempt_fence"
                else REPAIRED_EFFECT_FENCE_FIELDS
            ),
            "preselection_timestamp_record_invalid",
        )
        _s41_require_safe_ref(fence.get(ref_field), "preselection_timestamp_record_invalid")
        _s41_require_sha256(fence.get(digest_field), "preselection_timestamp_record_invalid")
        _s41_require_utc_second(fence.get("expires_at"), "preselection_timestamp_record_invalid")
        if fence[digest_field] != _s41_digest(
            domain,
            _s41_without(fence, digest_field),
        ):
            _s41_violate("preselection_timestamp_digest_mismatch")
        effects = (
            fence[effects_field]
            if bundle_field == "attempt_fence"
            else [fence[effects_field]]
        )
        if type(effects) is not list or not all(type(item) is str for item in effects):
            _s41_violate("preselection_timestamp_record_invalid")
        expected_context = (
            (context[ref_field], fence[ref_field]),
            (context[digest_field], fence[digest_field]),
            (context[context_effects_field], _s41_canonical_bytes(tuple(effects)).decode("utf-8")),
            (context[context_expiry_field], fence["expires_at"]),
        )
        if any(not _s41_exact_equal(left, right) for left, right in expected_context):
            _s41_violate("preselection_timestamp_digest_mismatch")


def _redigest_fence_and_context(
    bundle: dict[str, object],
    fence_role: str,
) -> None:
    assert fence_role in ("attempt_fence", "effect_fence")
    digest_field = f"{fence_role}_digest"
    domain = f"governed-execution.nwp-{fence_role.replace('_', '-')}.v1.identity"
    fence = bundle[fence_role]
    fence[digest_field] = _s41_digest(domain, _s41_without(fence, digest_field))
    records = bundle["preselection_records"]
    context = records["planning_context"]
    context[digest_field] = fence[digest_field]
    context[f"{fence_role}_expires_at"] = fence["expires_at"]
    context["planning_context_digest"] = _s41_digest(
        DIGEST_DOMAINS["pre_execution_context"],
        _s41_without(context, "planning_context_digest"),
    )
    source = records["source_invocation"]
    source["context_digest"] = context["planning_context_digest"]
    source["source_invocation_digest"] = _s41_digest(
        DIGEST_DOMAINS["source_invocation"],
        _s41_without(source, "source_invocation_digest"),
    )
    proposal = records["model_proposal"]
    proposal["source_invocation_digest"] = source["source_invocation_digest"]
    proposal["context_digest"] = context["planning_context_digest"]
    proposal["proposal_digest"] = _s41_digest(
        DIGEST_DOMAINS["proposal"],
        _s41_without(proposal, "proposal_digest"),
    )


def _validate_temporal_bundle(
    bundle: dict[str, object],
    decision_time: str,
) -> None:
    _s41_require_utc_second(decision_time, "preselection_chronology_invalid")
    observation = bundle["authority_observation"]
    records = bundle["preselection_records"]
    evidence_times = tuple(
        row["evidence_bound_at"] for row in records["evidence_bindings"]
    )
    if not evidence_times or any(value != evidence_times[0] for value in evidence_times):
        _s41_violate("preselection_chronology_invalid")
    if not (
        observation["authority_observation_issued_at"]
        < observation["authority_observation_expires_at"]
    ):
        _s41_violate("authority_observation_window_invalid")
    chronology = (
        observation["authority_observation_issued_at"],
        records["planning_context"]["planning_context_captured_at"],
        records["source_invocation"]["source_invocation_started_at"],
        records["source_invocation"]["source_invocation_completed_at"],
        records["artifact_binding"]["artifact_validated_at"],
        evidence_times[0],
        records["model_proposal"]["proposal_created_at"],
        decision_time,
    )
    for value in chronology:
        _s41_require_utc_second(value, "preselection_chronology_invalid")
    if (
        tuple(sorted(chronology)) != chronology
        or not records["model_proposal"]["proposal_created_at"] < decision_time
    ):
        _s41_violate("preselection_chronology_invalid")
    if not decision_time < observation["authority_observation_expires_at"]:
        _s41_violate("authority_observation_expired")
    if not decision_time < bundle["attempt_fence"]["expires_at"]:
        _s41_violate("attempt_fence_expired")
    if not decision_time < bundle["effect_fence"]["expires_at"]:
        _s41_violate("effect_fence_expired")


REPAIRED_FRESH_MUTATION_REF = "cognitive-mutation.oracle.0001"
REPAIRED_FRESH_COMMAND_DIGEST = "9" * 64


def _validate_cognitive_mutation_identity(
    mutation_ref: object,
    command_digest: object,
) -> None:
    _s41_require_safe_ref(mutation_ref, "cognitive_mutation_identity_invalid")
    _s41_require_sha256(command_digest, "cognitive_mutation_identity_invalid")


def _apply_repaired_selection(
    *,
    mutation_ref: object,
    command_digest: object,
    receipt: object | None,
    bundle: object,
    clock: object,
    trace: list[str],
) -> dict[str, object]:
    trace.append("receipt_lookup")
    _validate_cognitive_mutation_identity(mutation_ref, command_digest)
    if receipt is not None:
        trace.append("persisted_receipt_validation")
        _validate_repaired_physical_family(receipt)
        receipt_values = receipt["receipt"]["values"]
        if receipt_values["mutation_ref"] != mutation_ref:
            _s41_violate("physical_family_receipt_binding_mismatch")
        if receipt_values["command_digest"] != command_digest:
            trace.append("mutation_ref_reuse_conflict")
            return "mutation_ref_reuse_conflict"
        trace.append("exact_replay")
        return receipt["replay_result"]
    trace.append("fresh_shape_preflight")
    _preflight_selection_bundle_shapes(bundle)
    trace.append("non_temporal_checks")
    _validate_authority_observation_non_temporal(
        bundle["authority_observation"],
        bundle["authority_expected_binding"],
    )
    _validate_observation_context_binding(
        bundle["authority_observation"],
        bundle["preselection_records"],
    )
    _validate_fence_records_non_temporal(bundle)
    _validate_preselection_timestamp_records(bundle["preselection_records"])
    trace.append("clock")
    decision_time = clock()
    trace.append("temporal_checks")
    _validate_temporal_bundle(bundle, decision_time)
    trace.append("construct")
    return {
        "mutation_ref": mutation_ref,
        "command_digest": command_digest,
        "disposition": "selected_for_dispatch_gates",
        "coordinator_decision_at": decision_time,
        "selection_head_updated_at": decision_time,
        "receipt_committed_at": decision_time,
        "result_recorded_at": decision_time,
        "authority_selection_observation_ref": bundle["authority_observation"]["authority_observation_ref"],
        "authority_selection_observation_digest": bundle["authority_observation"]["authority_observation_digest"],
        "grants_dispatch": False,
    }


def test_transaction_clock_is_captured_once_before_every_temporal_check() -> None:
    owner = _parse_repaired_owner()["transaction_clock_order"]
    assert owner["fresh_receipt_miss_steps"][1] == (
        "perform bounded shape-only preflight over every active preselection, "
        "authority, AttemptFence, and EffectFence record before cross-record indexing"
    )
    assert owner["shape_preflight_calls_clock_writes_or_constructs_result"] is False
    assert owner["incoming_identity"] == (
        "exact built-in safe mutation_ref and exact built-in SHA-256 canonical "
        "command/proposal-selection digest are explicit oracle inputs"
    )
    assert owner["receipt_hit_order"] == (
        "lookup by incoming mutation_ref",
        "validate the complete exact persisted physical family and receipt schema",
        "require persisted mutation_ref equality",
        "return exact replay when persisted command digest equals the incoming digest",
        "otherwise return exact mutation_ref_reuse_conflict",
    )
    assert owner["arbitrary_non_none_receipt_gets_replay_credit"] is False
    assert owner["receipt_hit_runs_fresh_shape_preflight"] is False
    assert owner["receipt_hit_calls_clock_writes_or_commit"] is False
    assert owner["attempt_fence_field_order"] == REPAIRED_ATTEMPT_FENCE_FIELDS
    assert owner["effect_fence_field_order"] == REPAIRED_EFFECT_FENCE_FIELDS
    assert owner["fence_nested_shape"] == {
        "path_ceiling": (
            "exact built-in list; 1..3 unique exact built-in C2A safe paths in "
            "exact code-point order"
        ),
        "attempt_allowed_effect_classes": (
            "exact built-in nonempty list; unique exact built-in strings in "
            "canonical C2A effect-class order"
        ),
        "attempt_aggregate_ceilings": (
            "exact built-in dict with all fifteen ceiling fields in normative order "
            "and nonnegative exact built-in int values; bool invalid"
        ),
        "effect_ceilings": (
            "exact built-in dict with all fifteen ceiling fields in normative order "
            "and nonnegative exact built-in int values; bool invalid"
        ),
        "author_effect_nullable_fields": (
            "portable capsule digest and all three cancellation-target fields are "
            "exactly null"
        ),
    }
    calls: list[str] = []

    def clock() -> str:
        calls.append("called")
        return "2026-08-22T12:35:04Z"

    trace: list[str] = []
    result = _apply_repaired_selection(
        mutation_ref=REPAIRED_FRESH_MUTATION_REF,
        command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
        receipt=None,
        bundle=_sample_temporal_bundle(),
        clock=clock,
        trace=trace,
    )
    assert calls == ["called"]
    assert trace == (
        [
            "receipt_lookup",
            "fresh_shape_preflight",
            "non_temporal_checks",
            "clock",
            "temporal_checks",
            "construct",
        ]
    )
    assert result == {
        "mutation_ref": REPAIRED_FRESH_MUTATION_REF,
        "command_digest": REPAIRED_FRESH_COMMAND_DIGEST,
        "disposition": "selected_for_dispatch_gates",
        "coordinator_decision_at": "2026-08-22T12:35:04Z",
        "selection_head_updated_at": "2026-08-22T12:35:04Z",
        "receipt_committed_at": "2026-08-22T12:35:04Z",
        "result_recorded_at": "2026-08-22T12:35:04Z",
        "authority_selection_observation_ref": "authority-observation.supplied.0007",
        "authority_selection_observation_digest": _build_authority_observation()["authority_observation_digest"],
        "grants_dispatch": False,
    }


@pytest.mark.parametrize(
    "readiness_present,expected_count",
    ((False, 14), (True, 15)),
    ids=("readiness-absent", "readiness-present"),
)
def test_s41_corr_004_both_readiness_variants_pass_fresh_preflight(
    readiness_present: bool,
    expected_count: int,
) -> None:
    bundle = _sample_temporal_bundle(readiness_present)
    evidence = bundle["preselection_records"]["evidence_bindings"]
    assert len(evidence) == expected_count
    assert tuple(
        (
            row["evidence_role"],
            row["role_rank"],
            bool(row["required_for_selection"]),
        )
        for row in evidence
    ) == (
        REPAIRED_PRE_EXECUTION_EVIDENCE_SPECS
        if readiness_present
        else REPAIRED_PRE_EXECUTION_EVIDENCE_SPECS[:-1]
    )
    clock_calls: list[str] = []
    trace: list[str] = []

    def clock() -> str:
        clock_calls.append("called")
        return "2026-08-22T12:35:04Z"

    result = _apply_repaired_selection(
        mutation_ref=REPAIRED_FRESH_MUTATION_REF,
        command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
        receipt=None,
        bundle=bundle,
        clock=clock,
        trace=trace,
    )
    assert result["disposition"] == "selected_for_dispatch_gates"
    assert result["grants_dispatch"] is False
    assert clock_calls == ["called"]
    assert trace[-1] == "construct"


@pytest.mark.parametrize(
    "case_name",
    (
        "readiness_row_without_rank_19",
        "rank_19_without_readiness_row",
        "duplicate_rank_19",
        "wrong_role",
        "wrong_rank",
        "wrong_ref",
        "wrong_digest",
        "extra_non_readiness_evidence",
        "mandatory_missing_readiness_absent",
        "mandatory_missing_readiness_present",
    ),
)
def test_s41_corr_004_malformed_readiness_inventory_fails_before_clock(
    case_name: str,
) -> None:
    readiness_present = case_name not in (
        "extra_non_readiness_evidence",
        "mandatory_missing_readiness_absent",
    )
    bundle = _sample_temporal_bundle(readiness_present)
    records = bundle["preselection_records"]
    evidence = list(records["evidence_bindings"])
    if case_name == "readiness_row_without_rank_19":
        evidence[-1]["role_rank"] = 18
    elif case_name == "rank_19_without_readiness_row":
        context = records["planning_context"]
        context["qualified_remote_host_readiness_ref"] = None
        context["qualified_remote_host_readiness_digest"] = None
    elif case_name == "duplicate_rank_19":
        evidence.append(deepcopy(evidence[-1]))
    elif case_name == "wrong_role":
        evidence[-1]["evidence_role"] = "review_requirement"
    elif case_name == "wrong_rank":
        evidence[-1]["role_rank"] = 18
    elif case_name == "wrong_ref":
        evidence[-1]["evidence_ref"] = "qualified-readiness.changed.0001"
    elif case_name == "wrong_digest":
        evidence[-1]["evidence_digest"] = "f" * 64
    elif case_name == "extra_non_readiness_evidence":
        extra = deepcopy(evidence[-1])
        extra["evidence_role"] = "review_requirement"
        extra["role_rank"] = 19
        evidence.append(extra)
    elif case_name in (
        "mandatory_missing_readiness_absent",
        "mandatory_missing_readiness_present",
    ):
        del evidence[0]
    else:
        raise AssertionError(case_name)
    records["evidence_bindings"] = tuple(evidence)
    clock_calls: list[str] = []
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: clock_calls.append("called"),
            trace=trace,
        )
    assert caught.value.reason == "preselection_timestamp_record_invalid"
    assert clock_calls == []
    assert trace == ["receipt_lookup", "fresh_shape_preflight"]


def test_exact_replay_calls_no_clock_and_reuses_persisted_time() -> None:
    persisted = _build_repaired_physical_family(False)
    receipt_values = persisted["receipt"]["values"]

    def forbidden_clock() -> str:
        raise AssertionError("REPLAY_CLOCK_CALLED")

    trace: list[str] = []
    assert _apply_repaired_selection(
        mutation_ref=receipt_values["mutation_ref"],
        command_digest=receipt_values["command_digest"],
        receipt=persisted,
        bundle=_sample_temporal_bundle(),
        clock=forbidden_clock,
        trace=trace,
    ) is persisted["replay_result"]
    assert trace == [
        "receipt_lookup",
        "persisted_receipt_validation",
        "exact_replay",
    ]


def test_invalid_observation_window_is_decided_only_after_clock_capture() -> None:
    bundle = _sample_temporal_bundle()
    observation = bundle["authority_observation"]
    observation["authority_observation_expires_at"] = observation[
        "authority_observation_issued_at"
    ]
    observation["authority_observation_digest"] = _s41_digest(
        REPAIRED_AUTHORITY_DOMAIN,
        _s41_without(observation, "authority_observation_digest"),
    )
    bundle["preselection_records"] = _sample_preselection_records(observation)
    calls: list[str] = []
    trace: list[str] = []

    def clock() -> str:
        calls.append("called")
        return "2026-08-22T12:35:04Z"

    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=clock,
            trace=trace,
        )
    assert caught.value.reason == "authority_observation_window_invalid"
    assert calls == ["called"]
    assert trace == [
        "receipt_lookup",
        "fresh_shape_preflight",
        "non_temporal_checks",
        "clock",
        "temporal_checks",
    ]


def test_historical_currentness_record_is_inactive_for_current_selection() -> None:
    historical = deepcopy(_build_golden_vector(False)["authority_attestation"])
    historical["authority_state"] = "revoked"
    bundle = _sample_temporal_bundle()
    result = _apply_repaired_selection(
        mutation_ref=REPAIRED_FRESH_MUTATION_REF,
        command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
        receipt=None,
        bundle=bundle,
        clock=lambda: "2026-08-22T12:35:04Z",
        trace=[],
    )
    context = bundle["preselection_records"]["planning_context"]
    shared_observation_fields = (
        "authoritative_subject_kind",
        "authoritative_subject_ref",
    )
    assert all(
        field not in context
        for field in _HISTORICAL_CURRENTNESS_FIELDS
        if field not in shared_observation_fields
    )
    assert all(field in context for field in shared_observation_fields)
    assert historical["authority_state"] == "revoked"
    assert result["authority_selection_observation_ref"] == context[
        "authority_selection_observation_ref"
    ]


@pytest.mark.parametrize(
    "role,field",
    (
        ("artifact_binding", "artifact_validated_at"),
        ("evidence_bindings", "evidence_bound_at"),
    ),
)
def test_future_dated_preselection_inputs_fail_exact_chronology_reason(
    role: str,
    field: str,
) -> None:
    bundle = _sample_temporal_bundle()
    records = bundle["preselection_records"]
    if role == "evidence_bindings":
        for record in records[role]:
            record[field] = "2026-08-22T12:35:05Z"
    else:
        records[role][field] = "2026-08-22T12:35:05Z"
    _redigest_preselection_record(records, role)
    calls: list[str] = []

    def clock() -> str:
        calls.append("called")
        return "2026-08-22T12:35:04Z"

    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=clock,
            trace=[],
        )
    assert caught.value.reason == "preselection_chronology_invalid"
    assert calls == ["called"]


def test_reaudit_fully_redigested_fresh_proposal_decision_equality_is_rejected() -> None:
    bundle = _sample_temporal_bundle()
    proposal = bundle["preselection_records"]["model_proposal"]
    proposal["proposal_created_at"] = "2026-08-22T12:35:04Z"
    proposal["proposal_digest"] = _s41_digest(
        DIGEST_DOMAINS["proposal"],
        _s41_without(proposal, "proposal_digest"),
    )
    clock_calls = 0

    def clock() -> str:
        nonlocal clock_calls
        clock_calls += 1
        return "2026-08-22T12:35:04Z"

    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=clock,
            trace=trace,
        )
    assert caught.value.reason == "preselection_chronology_invalid"
    assert clock_calls == 1
    assert trace == [
        "receipt_lookup",
        "fresh_shape_preflight",
        "non_temporal_checks",
        "clock",
        "temporal_checks",
    ]


def test_reaudit_fully_redigested_persisted_proposal_decision_equality_is_rejected() -> None:
    family = _build_repaired_physical_family(False)
    by_role = {row["role"]: row for row in family["physical_rows"]}
    proposal = by_role["model_proposal"]["values"]
    disposition = by_role["coordinator_disposition"]["values"]
    proposal["proposal_created_at"] = disposition[
        "coordinator_disposition_decided_at"
    ]
    _redigest_repaired_physical_family(family)
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(family)
    assert caught.value.reason == "preselection_chronology_invalid"


@pytest.mark.parametrize(
    "expiry_field,reason",
    (
        ("authority_observation_expires_at", "authority_observation_expired"),
        ("attempt_fence_expires_at", "attempt_fence_expired"),
        ("effect_fence_expires_at", "effect_fence_expired"),
    ),
)
def test_each_exact_expiry_boundary_fails_its_own_reason(
    expiry_field: str,
    reason: str,
) -> None:
    bundle = _sample_temporal_bundle()
    if expiry_field.startswith("authority_"):
        observation = dict(bundle["authority_observation"])
        observation[expiry_field] = "2026-08-22T12:35:04Z"
        observation["authority_observation_digest"] = _s41_digest(
            REPAIRED_AUTHORITY_DOMAIN,
            _s41_without(observation, "authority_observation_digest"),
        )
        bundle["authority_observation"] = observation
        bundle["preselection_records"] = _sample_preselection_records(observation)
    else:
        fence_role = expiry_field.removesuffix("_expires_at")
        bundle[fence_role]["expires_at"] = "2026-08-22T12:35:04Z"
        _redigest_fence_and_context(bundle, fence_role)
    if expiry_field == "effect_fence_expires_at":
        bundle["attempt_fence"]["expires_at"] = "2026-08-22T12:35:06Z"
        _redigest_fence_and_context(bundle, "attempt_fence")
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: "2026-08-22T12:35:04Z",
            trace=[],
        )
    assert caught.value.reason == reason


@pytest.mark.parametrize("state", ("pending", "verified"))
def test_authority_observation_is_opaque_versioned_and_not_global_currentness(
    state: str,
) -> None:
    owner = _parse_repaired_owner()["authority_selection_observation"]
    observation = _build_authority_observation(state=state, version=23)
    assert _validate_authority_observation_non_temporal(
        observation,
        _authority_expected_binding(),
    ) is observation
    assert owner["field_order"] == REPAIRED_AUTHORITY_FIELDS
    assert owner["coordinator_expected_binding_inputs"] == tuple(
        _authority_expected_binding()
    )
    assert owner["self_digest_without_exact_supplied_binding_match_is_sufficient"] is False
    assert owner["globally_latest_external_state_proven"] is False
    assert owner["absence_of_later_or_omitted_revocation_proven"] is False
    assert owner["grants_execution_or_dispatch"] is False
    assert owner["fresh_external_verification_before_any_later_effect"] is True
    assert owner["live_currentness_service_added"] is False
    assert owner["active_authority_source_count"] == 1
    assert owner["planning_context_observation_field_order"] == REPAIRED_PLANNING_CONTEXT_OBSERVATION_FIELDS
    assert owner["planning_context_preserves_full_observation_lineage_state_version_time_source_and_verification_relations"] is True
    assert owner["historical_currentness_record_active"] is False
    assert "authority_currentness_attestation" not in REPAIRED_EVIDENCE_ROLES


@pytest.mark.parametrize("state", ("blocked", "stale", "revoked", "expired"))
def test_ineligible_authority_observation_state_has_exact_reason(state: str) -> None:
    observation = _build_authority_observation(state=state)
    with pytest.raises(_ContractViolation) as caught:
        _validate_authority_observation_non_temporal(
            observation,
            _authority_expected_binding(),
        )
    assert caught.value.reason == "authority_observation_state_ineligible"


@pytest.mark.parametrize(
    "field,bad_value",
    (
        ("program_ref", "program.changed.0001"),
        ("authority_evaluation_digest", "b" * 64),
        ("source_authority_ref", "external-authority.changed.0001"),
        ("verification_evidence_ref", "authority-verification.changed.0001"),
        ("verification_evidence_digest", "b" * 64),
    ),
)
def test_redigested_authority_binding_mutants_reach_exact_binding_reason(
    field: str,
    bad_value: str,
) -> None:
    observation = _build_authority_observation()
    observation[field] = bad_value
    observation["authority_observation_digest"] = _s41_digest(
        REPAIRED_AUTHORITY_DOMAIN,
        _s41_without(observation, "authority_observation_digest"),
    )
    with pytest.raises(_ContractViolation) as caught:
        _validate_authority_observation_non_temporal(
            observation,
            _authority_expected_binding(),
        )
    assert caught.value.reason == "authority_observation_binding_mismatch"


@pytest.mark.parametrize("version", (0, -1, True))
def test_nonpositive_or_nonexact_authority_version_has_exact_reason(
    version: object,
) -> None:
    observation = _build_authority_observation(version=version)
    with pytest.raises(_ContractViolation) as caught:
        _validate_authority_observation_non_temporal(
            observation,
            _authority_expected_binding(),
        )
    assert caught.value.reason == "authority_observation_version_invalid"


def test_preselection_timestamp_owner_and_digest_table_is_exact() -> None:
    owner = _parse_repaired_owner()["timestamp_ownership"]
    assert owner["preselection_timestamp_table"] == (
        ("authority_observation_issued_at", "external_authority_evidence_source", "authority observation identity"),
        ("authority_observation_expires_at", "external_authority_evidence_source", "authority observation identity"),
        ("planning_context_captured_at", "Coordinator_context_projection_producer", "planning context identity"),
        ("source_invocation_started_at", "model_adapter", "source invocation identity"),
        ("source_invocation_completed_at", "model_adapter", "source invocation identity"),
        ("artifact_validated_at", "private_artifact_validator_or_custodian", "private artifact binding identity"),
        ("evidence_bound_at", "proposal_assembler_model_adapter_boundary", "proposal evidence-set identity"),
        ("proposal_created_at", "model_adapter", "model proposal identity"),
    )
    assert owner["preselection_digest_bindings"] == (
        ("authority_observation_issued_at", "authority_observation_digest"),
        ("authority_observation_expires_at", "authority_observation_digest"),
        ("planning_context_captured_at", "planning_context_digest"),
        ("source_invocation_started_at", "source_invocation_digest"),
        ("source_invocation_completed_at", "source_invocation_digest"),
        ("artifact_validated_at", "artifact_binding_digest"),
        ("evidence_bound_at", "evidence_binding_digest"),
        ("proposal_created_at", "proposal_digest"),
    )
    assert owner["all_preselection_values_digest_bound"] is True
    assert owner["duplicate_active_fence_time_source"] is False
    assert owner["all_active_ordering_window_expiry_chronology_and_eligibility_comparisons_after_clock_capture"] is True


@pytest.mark.parametrize(
    "role,field",
    (
        ("planning_context", "planning_context_captured_at"),
        ("source_invocation", "source_invocation_started_at"),
        ("source_invocation", "source_invocation_completed_at"),
        ("artifact_binding", "artifact_validated_at"),
        ("evidence_bindings", "evidence_bound_at"),
        ("model_proposal", "proposal_created_at"),
    ),
)
def test_each_preselection_timestamp_is_mechanically_digest_bound(
    role: str,
    field: str,
) -> None:
    records = _sample_preselection_records()
    if role == "evidence_bindings":
        records[role][0][field] = "2026-08-22T12:35:04Z"
    else:
        records[role][field] = "2026-08-22T12:35:04Z"
    with pytest.raises(_ContractViolation) as caught:
        _validate_preselection_timestamp_records(records)
    assert caught.value.reason == "preselection_timestamp_digest_mismatch"


@pytest.mark.parametrize(
    "mutation",
    (
        "missing_context_observation_ref",
        "missing_rank15_role_rank",
        "missing_context_attempt_expiry",
    ),
)
def test_f5_audit_shape_mutants_reach_finite_reason_before_clock(
    mutation: str,
) -> None:
    bundle = _sample_temporal_bundle()
    records = bundle["preselection_records"]
    if mutation == "missing_context_observation_ref":
        del records["planning_context"]["authority_selection_observation_ref"]
    elif mutation == "missing_rank15_role_rank":
        rank_15 = next(
            row for row in records["evidence_bindings"] if row["role_rank"] == 15
        )
        del rank_15["role_rank"]
    else:
        del records["planning_context"]["attempt_fence_expires_at"]
    clock_calls: list[str] = []
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: clock_calls.append("called"),
            trace=trace,
        )
    assert type(caught.value) is _ContractViolation
    assert caught.value.reason == "preselection_timestamp_record_invalid"
    assert clock_calls == []
    assert trace == ["receipt_lookup", "fresh_shape_preflight"]
    assert "construct" not in trace


@pytest.mark.parametrize(
    "record_role,expected_reason",
    (
        ("bundle", "preselection_timestamp_record_invalid"),
        ("authority_observation", "authority_observation_shape_invalid"),
        ("authority_expected_binding", "authority_observation_binding_mismatch"),
        ("attempt_fence", "preselection_timestamp_record_invalid"),
        ("attempt_path_ceiling", "preselection_timestamp_record_invalid"),
        ("attempt_effect_classes", "preselection_timestamp_record_invalid"),
        ("attempt_ceilings", "preselection_timestamp_record_invalid"),
        ("effect_fence", "preselection_timestamp_record_invalid"),
        ("effect_path_ceiling", "preselection_timestamp_record_invalid"),
        ("effect_ceilings", "preselection_timestamp_record_invalid"),
        ("preselection_records", "preselection_timestamp_record_invalid"),
        ("planning_context", "preselection_timestamp_record_invalid"),
        ("source_invocation", "preselection_timestamp_record_invalid"),
        ("artifact_binding", "preselection_timestamp_record_invalid"),
        ("evidence_bindings", "preselection_timestamp_record_invalid"),
        ("evidence_binding", "preselection_timestamp_record_invalid"),
        ("model_proposal", "preselection_timestamp_record_invalid"),
        ("evidence_set", "preselection_timestamp_record_invalid"),
        ("evidence_set_entries", "preselection_timestamp_record_invalid"),
        ("evidence_set_entry", "preselection_timestamp_record_invalid"),
    ),
)
def test_f5_every_preclock_active_record_wrong_container_is_finite(
    record_role: str,
    expected_reason: str,
) -> None:
    bundle: object = _sample_temporal_bundle()
    if record_role == "bundle":
        bundle = []
    else:
        records = bundle["preselection_records"]
        if record_role in (
            "authority_observation",
            "authority_expected_binding",
            "attempt_fence",
            "effect_fence",
            "preselection_records",
        ):
            bundle[record_role] = []
        elif record_role == "evidence_binding":
            rows = list(records["evidence_bindings"])
            rows[0] = []
            records["evidence_bindings"] = tuple(rows)
        elif record_role == "evidence_set_entries":
            records["evidence_set"]["entries"] = []
        elif record_role == "evidence_set_entry":
            entries = list(records["evidence_set"]["entries"])
            entries[0] = []
            records["evidence_set"]["entries"] = tuple(entries)
        elif record_role == "attempt_path_ceiling":
            bundle["attempt_fence"]["path_ceiling"] = {}
        elif record_role == "attempt_effect_classes":
            bundle["attempt_fence"]["allowed_effect_classes"] = {}
        elif record_role == "attempt_ceilings":
            bundle["attempt_fence"]["aggregate_ceilings"] = []
        elif record_role == "effect_path_ceiling":
            bundle["effect_fence"]["path_ceiling"] = {}
        elif record_role == "effect_ceilings":
            bundle["effect_fence"]["effect_ceilings"] = []
        else:
            records[record_role] = []
    clock_calls: list[str] = []
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: clock_calls.append("called"),
            trace=trace,
        )
    assert type(caught.value) is _ContractViolation
    assert caught.value.reason == expected_reason
    assert clock_calls == []
    assert trace == ["receipt_lookup", "fresh_shape_preflight"]


def test_f4_active_record_shape_inventory_is_finite_complete_and_owned() -> None:
    owner = _parse_repaired_owner()["transaction_clock_order"]
    assert owner["active_record_shape_count"] == 20
    assert owner["active_record_shape_inventory"] == (
        REPAIRED_ACTIVE_RECORD_SHAPE_INVENTORY
    )
    assert owner["active_scalar_kind_inventory"] == (
        REPAIRED_ACTIVE_SCALAR_KIND_INVENTORY
    )
    assert owner["finite_section41_registry_not_general_schema_engine"] is True
    assert owner["all_active_scalar_values_exact_builtins_before_digest_or_index"] is True
    assert owner["bool_accepted_as_integer"] is False
    assert owner["container_subclass_accepted"] is False
    assert owner["timestamp_record_inventories_exact"] is True
    assert owner["every_attempt_fence_missing_or_extra_field_invalid_before_digest"] is True
    assert owner["every_effect_fence_missing_or_extra_field_invalid_before_digest"] is True
    assert owner["shape_preflight_manufactures_engineering_judgment"] is False
    assert owner["semantic_reason_precedence_after_shape_success_preserved"] is True
    assert "strict UTF-8 encodable" in owner["active_string_grammar"]
    assert "-9223372036854775808..9223372036854775807" in owner[
        "persisted_integer_grammar"
    ]
    assert owner["residual_canonicalization_failure"].startswith(
        "canonical_value_invalid"
    )
    assert owner["readiness_absent_evidence_inventory"] == (
        REPAIRED_PRE_EXECUTION_EVIDENCE_SPECS[:-1]
    )
    assert owner["readiness_present_evidence_inventory"] == (
        REPAIRED_PRE_EXECUTION_EVIDENCE_SPECS
    )
    assert owner["readiness_inventory_derived_from_context_binding"] is True
    assert owner["readiness_grants_selection_authority"] is False
    assert owner["readiness_grants_dispatch_or_effect"] is False


@pytest.mark.parametrize(
    "case_name,expected_reason",
    (
        ("authority_matching_list_ref", "authority_observation_shape_invalid"),
        ("authority_expected_digest_subclass", "authority_observation_binding_mismatch"),
        ("planning_positive_int_bool", "preselection_timestamp_record_invalid"),
        ("planning_attempt_number_object", "preselection_timestamp_record_invalid"),
        ("planning_safe_ref_subclass", "preselection_timestamp_record_invalid"),
        ("planning_effect_json_subclass", "preselection_timestamp_record_invalid"),
        ("planning_timestamp_subclass", "preselection_timestamp_record_invalid"),
        ("source_phase_subclass", "preselection_timestamp_record_invalid"),
        ("artifact_bounded_int_float", "preselection_timestamp_record_invalid"),
        ("proposal_recommendation_subclass", "preselection_timestamp_record_invalid"),
        ("proposal_reason_subclass", "preselection_timestamp_record_invalid"),
        ("evidence_rank_bool", "preselection_timestamp_record_invalid"),
        ("evidence_bool_int_bool", "preselection_timestamp_record_invalid"),
        ("evidence_set_ref_subclass", "preselection_timestamp_record_invalid"),
        ("evidence_entry_ordinal_bool", "preselection_timestamp_record_invalid"),
        ("attempt_global_stop_bool", "preselection_timestamp_record_invalid"),
        ("attempt_oid_subclass", "preselection_timestamp_record_invalid"),
        ("attempt_effect_entry_subclass", "preselection_timestamp_record_invalid"),
        ("attempt_path_entry_subclass", "preselection_timestamp_record_invalid"),
        ("effect_global_stop_bool", "preselection_timestamp_record_invalid"),
        ("effect_class_subclass", "preselection_timestamp_record_invalid"),
        ("effect_nullable_nonnull", "preselection_timestamp_record_invalid"),
        ("effect_ceiling_bool", "preselection_timestamp_record_invalid"),
    ),
)
def test_f4_every_active_scalar_kind_rejects_aliases_before_clock(
    case_name: str,
    expected_reason: str,
) -> None:
    bundle = _sample_temporal_bundle()
    records = bundle["preselection_records"]
    if case_name == "authority_matching_list_ref":
        bundle["authority_observation"]["program_ref"] = ["program-c2b3a-1"]
        bundle["authority_expected_binding"]["program_ref"] = ["program-c2b3a-1"]
    elif case_name == "authority_expected_digest_subclass":
        bundle["authority_expected_binding"]["authority_evaluation_digest"] = (
            _S41StringSubclass(
                bundle["authority_expected_binding"]["authority_evaluation_digest"]
            )
        )
    elif case_name == "planning_positive_int_bool":
        records["planning_context"]["program_version_number"] = True
    elif case_name == "planning_attempt_number_object":
        records["planning_context"]["attempt_number"] = object()
    elif case_name == "planning_safe_ref_subclass":
        records["planning_context"]["work_spec_ref"] = _S41StringSubclass(
            records["planning_context"]["work_spec_ref"]
        )
    elif case_name == "planning_effect_json_subclass":
        records["planning_context"]["attempt_fence_allowed_effect_classes_json"] = (
            _S41StringSubclass(
                records["planning_context"][
                    "attempt_fence_allowed_effect_classes_json"
                ]
            )
        )
    elif case_name == "planning_timestamp_subclass":
        records["planning_context"]["planning_context_captured_at"] = (
            _S41StringSubclass(
                records["planning_context"]["planning_context_captured_at"]
            )
        )
    elif case_name == "source_phase_subclass":
        records["source_invocation"]["proposal_phase"] = _S41StringSubclass(
            records["source_invocation"]["proposal_phase"]
        )
    elif case_name == "artifact_bounded_int_float":
        records["artifact_binding"]["artifact_canonical_byte_length"] = 1.5
    elif case_name == "proposal_recommendation_subclass":
        records["model_proposal"]["recommendation"] = _S41StringSubclass(
            records["model_proposal"]["recommendation"]
        )
    elif case_name == "proposal_reason_subclass":
        records["model_proposal"]["reason_code"] = _S41StringSubclass(
            records["model_proposal"]["reason_code"]
        )
    elif case_name == "evidence_rank_bool":
        records["evidence_bindings"][0]["role_rank"] = True
    elif case_name == "evidence_bool_int_bool":
        records["evidence_bindings"][0]["required_for_selection"] = True
    elif case_name == "evidence_set_ref_subclass":
        records["evidence_set"]["evidence_set_ref"] = _S41StringSubclass(
            records["evidence_set"]["evidence_set_ref"]
        )
    elif case_name == "evidence_entry_ordinal_bool":
        records["evidence_set"]["entries"][0]["ordinal"] = True
    elif case_name == "attempt_global_stop_bool":
        bundle["attempt_fence"]["global_stop_version"] = True
    elif case_name == "attempt_oid_subclass":
        bundle["attempt_fence"]["base_git_oid"] = _S41StringSubclass(
            bundle["attempt_fence"]["base_git_oid"]
        )
    elif case_name == "attempt_effect_entry_subclass":
        effects = list(bundle["attempt_fence"]["allowed_effect_classes"])
        effects[0] = _S41StringSubclass(effects[0])
        bundle["attempt_fence"]["allowed_effect_classes"] = effects
    elif case_name == "attempt_path_entry_subclass":
        paths = list(bundle["attempt_fence"]["path_ceiling"])
        paths[0] = _S41StringSubclass(paths[0])
        bundle["attempt_fence"]["path_ceiling"] = paths
    elif case_name == "effect_global_stop_bool":
        bundle["effect_fence"]["global_stop_version"] = True
    elif case_name == "effect_class_subclass":
        bundle["effect_fence"]["effect_class"] = _S41StringSubclass(
            bundle["effect_fence"]["effect_class"]
        )
    elif case_name == "effect_nullable_nonnull":
        bundle["effect_fence"]["portable_capsule_digest"] = "a" * 64
    elif case_name == "effect_ceiling_bool":
        bundle["effect_fence"]["effect_ceilings"]["max_active_invocations"] = True
    else:
        raise AssertionError(case_name)
    clock_calls: list[str] = []
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: clock_calls.append("called"),
            trace=trace,
        )
    assert type(caught.value) is _ContractViolation
    assert caught.value.reason == expected_reason
    assert clock_calls == []
    assert trace == ["receipt_lookup", "fresh_shape_preflight"]


@pytest.mark.parametrize(
    "case_name,expected_reason",
    (
        ("surrogate_observation_state", "authority_observation_shape_invalid"),
        ("huge_authority_version", "authority_observation_version_invalid"),
    ),
)
def test_s41_corr_005_audit_scalars_are_finite_before_clock(
    case_name: str,
    expected_reason: str,
) -> None:
    bundle = _sample_temporal_bundle()
    if case_name == "surrogate_observation_state":
        bundle["authority_observation"]["observation_state"] = "\ud800"
    elif case_name == "huge_authority_version":
        bundle["authority_observation"]["observation_version"] = 10**5000
    else:
        raise AssertionError(case_name)
    clock_calls: list[str] = []
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: clock_calls.append("called"),
            trace=trace,
        )
    assert type(caught.value) is _ContractViolation
    assert caught.value.reason == expected_reason
    assert clock_calls == []
    assert trace == ["receipt_lookup", "fresh_shape_preflight"]


@pytest.mark.parametrize(
    "value",
    (
        {"unsupported": object()},
        {"not_finite": float("nan")},
        "\ud800",
    ),
    ids=("unsupported-object", "nan", "surrogate"),
)
def test_s41_corr_005_residual_canonicalization_errors_are_finite(
    value: object,
) -> None:
    with pytest.raises(_ContractViolation) as caught:
        _s41_canonical_bytes(value)
    assert type(caught.value) is _ContractViolation
    assert caught.value.reason == "canonical_value_invalid"


def test_s41_corr_005_recursive_canonical_value_is_finite() -> None:
    recursive: list[object] = []
    recursive.append(recursive)
    assert _s41_exact_equal(recursive, recursive) is False
    with pytest.raises(_ContractViolation) as caught:
        _s41_canonical_bytes(recursive)
    assert type(caught.value) is _ContractViolation
    assert caught.value.reason == "canonical_value_invalid"


def test_s41_corr_005_persisted_integer_grammar_is_sqlite_bounded() -> None:
    for kind in (
        "positive_int",
        "nonnegative_int",
        "selection_prior_revision",
        "nullable_nonnegative_int",
    ):
        assert str(SQLITE_INTEGER_MAX) in _sqlite_kind_check("value", kind)
    assert _repaired_value_matches_kind(SQLITE_INTEGER_MAX, "nonnegative_int")
    assert not _repaired_value_matches_kind(
        SQLITE_INTEGER_MAX + 1,
        "nonnegative_int",
    )
    assert not _repaired_value_matches_kind(
        SQLITE_INTEGER_MIN - 1,
        "selection_prior_revision",
    )
    assert not _s41_active_value_matches_kind(10**5000, "exact_int")


@pytest.mark.parametrize(
    "fence_role,field",
    tuple(("attempt_fence", field) for field in REPAIRED_ATTEMPT_FENCE_FIELDS)
    + tuple(("effect_fence", field) for field in REPAIRED_EFFECT_FENCE_FIELDS),
)
def test_f4_every_fence_missing_field_is_rejected_before_index_or_digest(
    fence_role: str,
    field: str,
) -> None:
    bundle = _sample_temporal_bundle()
    del bundle[fence_role][field]
    clock_calls: list[str] = []
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: clock_calls.append("called"),
            trace=trace,
        )
    assert type(caught.value) is _ContractViolation
    assert caught.value.reason == "preselection_timestamp_record_invalid"
    assert clock_calls == []
    assert trace == ["receipt_lookup", "fresh_shape_preflight"]


def test_f5_receipt_first_replay_bypasses_shape_preflight_and_clock() -> None:
    receipt = _build_repaired_physical_family(False)
    receipt_values = receipt["receipt"]["values"]
    trace: list[str] = []
    assert _apply_repaired_selection(
        mutation_ref=receipt_values["mutation_ref"],
        command_digest=receipt_values["command_digest"],
        receipt=receipt,
        bundle={},
        clock=lambda: (_ for _ in ()).throw(AssertionError("REPLAY_CLOCK_CALLED")),
        trace=trace,
    ) is receipt["replay_result"]
    assert trace == [
        "receipt_lookup",
        "persisted_receipt_validation",
        "exact_replay",
    ]


def test_f5_same_mutation_ref_with_different_digest_is_exact_conflict() -> None:
    receipt = _build_repaired_physical_family(False)
    receipt_values = receipt["receipt"]["values"]
    different_digest = (
        "a" * 64 if receipt_values["command_digest"] != "a" * 64 else "b" * 64
    )
    trace: list[str] = []
    assert _apply_repaired_selection(
        mutation_ref=receipt_values["mutation_ref"],
        command_digest=different_digest,
        receipt=receipt,
        bundle=object(),
        clock=lambda: (_ for _ in ()).throw(AssertionError("CONFLICT_CLOCK_CALLED")),
        trace=trace,
    ) == "mutation_ref_reuse_conflict"
    assert trace == [
        "receipt_lookup",
        "persisted_receipt_validation",
        "mutation_ref_reuse_conflict",
    ]


@pytest.mark.parametrize(
    "receipt,expected_reason",
    (
        ({"not": "a persisted family"}, "physical_family_extra_row"),
        (object(), "physical_family_extra_row"),
    ),
)
def test_f5_arbitrary_nonreceipt_objects_never_receive_replay_credit(
    receipt: object,
    expected_reason: str,
) -> None:
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=receipt,
            bundle=object(),
            clock=lambda: (_ for _ in ()).throw(AssertionError("RECEIPT_CLOCK_CALLED")),
            trace=trace,
        )
    assert type(caught.value) is _ContractViolation
    assert caught.value.reason == expected_reason
    assert trace == ["receipt_lookup", "persisted_receipt_validation"]


def test_f5_malformed_persisted_receipt_family_fails_closed_before_replay() -> None:
    receipt = _build_repaired_physical_family(False)
    receipt_values = receipt["receipt"]["values"]
    malformed = deepcopy(receipt)
    malformed_receipt = deepcopy(malformed["receipt"])
    del malformed_receipt["values"]["command_digest"]
    malformed_rows = list(malformed["physical_rows"])
    malformed_rows[-1] = malformed_receipt
    malformed["receipt"] = malformed_receipt
    malformed["physical_rows"] = tuple(malformed_rows)
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=receipt_values["mutation_ref"],
            command_digest=receipt_values["command_digest"],
            receipt=malformed,
            bundle=object(),
            clock=lambda: (_ for _ in ()).throw(AssertionError("RECEIPT_CLOCK_CALLED")),
            trace=trace,
        )
    assert type(caught.value) is _ContractViolation
    assert caught.value.reason == "physical_family_row_digest_mismatch"
    assert trace == ["receipt_lookup", "persisted_receipt_validation"]


def test_f5_receipt_lookup_identity_and_fresh_identity_shapes_are_finite() -> None:
    receipt = _build_repaired_physical_family(False)
    receipt_values = receipt["receipt"]["values"]
    wrong_lookup = deepcopy(receipt)
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as wrong_lookup_caught:
        _apply_repaired_selection(
            mutation_ref="cognitive-mutation.different.0001",
            command_digest=receipt_values["command_digest"],
            receipt=wrong_lookup,
            bundle=object(),
            clock=lambda: (_ for _ in ()).throw(AssertionError("RECEIPT_CLOCK_CALLED")),
            trace=trace,
        )
    assert (
        wrong_lookup_caught.value.reason
        == "physical_family_receipt_binding_mismatch"
    )
    assert trace == ["receipt_lookup", "persisted_receipt_validation"]

    for mutation_ref, command_digest in (
        (object(), REPAIRED_FRESH_COMMAND_DIGEST),
        (REPAIRED_FRESH_MUTATION_REF, _S41StringSubclass("a" * 64)),
    ):
        trace = []
        with pytest.raises(_ContractViolation) as malformed_identity:
            _apply_repaired_selection(
                mutation_ref=mutation_ref,
                command_digest=command_digest,
                receipt=None,
                bundle=object(),
                clock=lambda: (_ for _ in ()).throw(AssertionError("IDENTITY_CLOCK_CALLED")),
                trace=trace,
            )
        assert malformed_identity.value.reason == "cognitive_mutation_identity_invalid"
        assert trace == ["receipt_lookup"]


def test_f5_valid_shaped_authority_stop_and_head_precedence_remains_exact() -> None:
    bundle = _sample_temporal_bundle()
    observation = bundle["authority_observation"]
    observation["observation_state"] = "revoked"
    observation["authority_observation_digest"] = _s41_digest(
        REPAIRED_AUTHORITY_DOMAIN,
        _s41_without(observation, "authority_observation_digest"),
    )
    bundle["preselection_records"] = _sample_preselection_records(observation)
    with pytest.raises(_ContractViolation) as authority_caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: (_ for _ in ()).throw(AssertionError("AUTHORITY_CLOCK_CALLED")),
            trace=[],
        )
    assert authority_caught.value.reason == "authority_observation_state_ineligible"
    assert _resolve_fresh_outcome(
        ("active_coding_global_stop", "current_selection_head_conflict")
    ) == "planning_selection_not_permitted"
    assert _resolve_fresh_outcome(
        ("current_selection_head_conflict", "authority_attestation_invalid")
    ) == "selection_head_version_conflict"
    assert _resolve_fresh_outcome(
        ("mutation_ref_reuse", "active_coding_global_stop")
    ) == "mutation_ref_reuse_conflict"


REPAIRED_ARTIFACT_SCHEMA = "governed-execution.nwp-pre-execution-plan-artifact.v1"
REPAIRED_ARTIFACT_DOMAIN = REPAIRED_ARTIFACT_SCHEMA + ".identity"
REPAIRED_PROJECTION_SCHEMA = "governed-execution.nwp-pre-execution-plan-safe-projection.v1"
REPAIRED_PROJECTION_DOMAIN = REPAIRED_PROJECTION_SCHEMA + ".identity"
REPAIRED_ARTIFACT_FIELDS = (
    "schema_id",
    "artifact_ref",
    "proposal_ref",
    "proposal_phase",
    "planning_context_ref",
    "implementation_strategy",
    "proposed_work_units",
    "affected_authorized_paths",
    "expected_outputs",
    "validation_strategy",
    "material_assumptions",
    "risks_and_uncertainties",
    "required_evidence_and_prerequisites",
    "stop_or_replan_conditions",
    "proposed_resource_and_effect_use",
    "recommendation",
    "reason_code",
    "artifact_digest",
)
REPAIRED_WORK_UNIT_FIELDS = (
    "ordinal",
    "work_unit_ref",
    "action_kind",
    "summary",
    "depends_on_work_unit_refs",
    "authorized_path_ordinals",
    "expected_output_refs",
    "validation_refs",
    "required_evidence_roles",
    "prerequisite_refs",
    "stop_condition_refs",
)
REPAIRED_RESOURCE_FIELDS = (
    "allowed_effect_classes",
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
REPAIRED_STANDING_CEILINGS = dict(C2B3D_BASIS["attempt_aggregate_ceilings"])
REPAIRED_PROJECTION_FIELDS = (
    "schema_id",
    "proposal_ref",
    "proposal_phase",
    "artifact_schema_id",
    "artifact_ref",
    "artifact_digest",
    "planning_context_schema_id",
    "planning_context_ref",
    "planning_context_digest",
    "strategy_item_count",
    "work_unit_count",
    "affected_path_count",
    "affected_path_set_digest",
    "expected_output_count",
    "expected_output_set_digest",
    "validation_step_count",
    "validation_strategy_digest",
    "assumption_count",
    "assumption_set_digest",
    "risk_count",
    "risk_set_digest",
    "prerequisite_count",
    "prerequisite_set_digest",
    "stop_condition_count",
    "stop_condition_set_digest",
    "proposed_resource_effect_use_digest",
    "allowed_effect_classes",
    "recommendation",
    "reason_code",
    "safe_projection_digest",
)
REPAIRED_COMPONENT_DOMAINS = {
    "affected_path_set_digest": "governed-execution.nwp-pre-execution-affected-path-set.v1.identity",
    "expected_output_set_digest": "governed-execution.nwp-pre-execution-expected-output-set.v1.identity",
    "validation_strategy_digest": "governed-execution.nwp-pre-execution-validation-strategy.v1.identity",
    "assumption_set_digest": "governed-execution.nwp-pre-execution-assumption-set.v1.identity",
    "risk_set_digest": "governed-execution.nwp-pre-execution-risk-set.v1.identity",
    "prerequisite_set_digest": "governed-execution.nwp-pre-execution-prerequisite-set.v1.identity",
    "stop_condition_set_digest": "governed-execution.nwp-pre-execution-stop-condition-set.v1.identity",
    "proposed_resource_effect_use_digest": "governed-execution.nwp-pre-execution-resource-effect-use.v1.identity",
}


def _s41_exact_equal(actual: object, expected: object) -> bool:
    def compare(
        left: object,
        right: object,
        active_pairs: set[tuple[int, int]],
    ) -> bool:
        if type(left) is not type(right):
            return False
        if type(right) in (dict, tuple, list):
            pair = (id(left), id(right))
            if pair in active_pairs:
                return False
            active_pairs.add(pair)
            try:
                if type(right) is dict:
                    return (
                        all(type(key) is str for key in left)
                        and all(type(key) is str for key in right)
                        and tuple(left) == tuple(right)
                        and all(
                            compare(left[key], right[key], active_pairs)
                            for key in right
                        )
                    )
                return len(left) == len(right) and all(
                    compare(left_item, right_item, active_pairs)
                    for left_item, right_item in zip(left, right, strict=True)
                )
            finally:
                active_pairs.remove(pair)
        if type(right) not in (str, int, bool, type(None)):
            return False
        return left == right

    return compare(actual, expected, set())


def _s41_require_tuple(
    value: object,
    minimum: int,
    maximum: int,
    *,
    duplicate_free: bool,
) -> tuple[object, ...]:
    if type(value) is not tuple or not minimum <= len(value) <= maximum:
        _s41_violate("private_plan_nested_collection_invalid")
    if duplicate_free and any(
        _s41_exact_equal(value[left], value[right])
        for left in range(len(value))
        for right in range(left + 1, len(value))
    ):
        _s41_violate("private_plan_nested_collection_invalid")
    return value


def _s41_validate_narrative(value: object, maximum: int) -> None:
    if type(value) is not str:
        _s41_violate("private_plan_narrative_invalid")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        _s41_violate("private_plan_narrative_invalid")
    if not 1 <= len(encoded) <= maximum:
        _s41_violate("private_plan_narrative_invalid")
    if value != value.strip() or unicodedata.normalize("NFC", value) != value:
        _s41_violate("private_plan_narrative_invalid")
    if not any(unicodedata.category(character)[0] in ("L", "N") for character in value):
        _s41_violate("private_plan_narrative_invalid")
    if any(unicodedata.category(character) == "Cc" for character in value):
        _s41_violate("private_plan_narrative_invalid")
    if value.casefold() in {"...", "n/a", "none", "placeholder", "tbd", "todo", "unknown"}:
        _s41_violate("private_plan_narrative_invalid")


def _s41_assert_ref_tuple_in_order(
    values: object,
    allowed_order: tuple[str, ...],
    minimum: int,
    maximum: int,
) -> tuple[str, ...]:
    result = _s41_require_tuple(
        values,
        minimum,
        maximum,
        duplicate_free=True,
    )
    if not all(type(item) is str and item in allowed_order for item in result):
        _s41_violate("private_plan_nested_collection_invalid")
    if tuple(item for item in allowed_order if item in result) != result:
        _s41_violate("private_plan_nested_collection_invalid")
    return result


def _validate_repaired_private_plan(
    artifact: object,
    *,
    attempt_effects: tuple[str, ...] = REPAIRED_EFFECT_CLASSES,
    effect_effects: tuple[str, ...] = ("author_candidate",),
    attempt_paths: tuple[str, ...] | None = None,
    effect_paths: tuple[str, ...] | None = None,
    standing_ceilings: dict[str, object] | None = None,
    attempt_ceilings: dict[str, object] | None = None,
    effect_ceilings: dict[str, object] | None = None,
) -> dict[str, object]:
    artifact = _s41_require_exact_mapping(
        artifact,
        REPAIRED_ARTIFACT_FIELDS,
        "private_plan_nested_collection_invalid",
    )
    if type(artifact["schema_id"]) is not str or artifact["schema_id"] != REPAIRED_ARTIFACT_SCHEMA:
        _s41_violate("private_plan_nested_collection_invalid")
    for field in ("artifact_ref", "proposal_ref", "planning_context_ref"):
        _s41_require_safe_ref(artifact[field], "private_plan_nested_collection_invalid")
    if type(artifact["proposal_phase"]) is not str or artifact["proposal_phase"] != "pre_execution_plan":
        _s41_violate("private_plan_closed_vocabulary_invalid")

    strategies = _s41_require_tuple(
        artifact["implementation_strategy"],
        1,
        8,
        duplicate_free=True,
    )
    for statement in strategies:
        _s41_validate_narrative(statement, 768)

    paths = _s41_require_tuple(
        artifact["affected_authorized_paths"],
        1,
        64,
        duplicate_free=True,
    )
    authorized_order = C2B3D_BASIS["authorized_paths"]
    attempt_path_ceiling = authorized_order if attempt_paths is None else attempt_paths
    effect_path_ceiling = authorized_order if effect_paths is None else effect_paths
    if not all(type(path) is str and path in authorized_order for path in paths):
        _s41_violate("private_plan_nested_collection_invalid")
    if tuple(path for path in authorized_order if path in paths) != paths:
        _s41_violate("private_plan_nested_collection_invalid")
    for ceiling in (attempt_path_ceiling, effect_path_ceiling):
        ceiling = _s41_require_tuple(
            ceiling,
            0,
            len(authorized_order),
            duplicate_free=True,
        )
        if not all(type(path) is str and path in authorized_order for path in ceiling):
            _s41_violate("private_plan_nested_collection_invalid")
        if tuple(path for path in authorized_order if path in ceiling) != ceiling:
            _s41_violate("private_plan_nested_collection_invalid")
        if any(not any(_s41_exact_equal(path, item) for item in ceiling) for path in paths):
            _s41_violate("private_plan_nested_collection_invalid")

    work_units = _s41_require_tuple(
        artifact["proposed_work_units"],
        1,
        32,
        duplicate_free=False,
    )
    for unit in work_units:
        _s41_require_exact_mapping(
            unit,
            REPAIRED_WORK_UNIT_FIELDS,
            "private_plan_nested_collection_invalid",
        )
    work_refs = tuple(unit["work_unit_ref"] for unit in work_units)
    if not all(type(ref) is str for ref in work_refs) or len(work_refs) != len(set(work_refs)):
        _s41_violate("private_plan_nested_collection_invalid")

    action_kinds = (
        "analyze",
        "modify_authorized_path",
        "create_authorized_path",
        "delete_authorized_path",
        "run_validation",
        "review_evidence",
        "prepare_candidate",
    )
    for index, unit in enumerate(work_units):
        if type(unit["ordinal"]) is not int or unit["ordinal"] != index:
            _s41_violate("private_plan_nested_collection_invalid")
        _s41_require_safe_ref(unit["work_unit_ref"], "private_plan_nested_collection_invalid")
        if type(unit["action_kind"]) is not str or unit["action_kind"] not in action_kinds:
            _s41_violate("private_plan_closed_vocabulary_invalid")
        _s41_validate_narrative(unit["summary"], 512)
        dependencies = _s41_require_tuple(
            unit["depends_on_work_unit_refs"],
            0,
            31,
            duplicate_free=True,
        )
        if any(type(ref) is not str or ref not in work_refs for ref in dependencies):
            _s41_violate("private_plan_nested_collection_invalid")
        if any(ref not in work_refs[:index] for ref in dependencies):
            _s41_violate("private_plan_forward_dependency")
        if tuple(ref for ref in work_refs[:index] if ref in dependencies) != dependencies:
            _s41_violate("private_plan_nested_collection_invalid")
        path_ordinals = _s41_require_tuple(
            unit["authorized_path_ordinals"],
            1,
            64,
            duplicate_free=True,
        )
        if not all(type(item) is int and 0 <= item < len(paths) for item in path_ordinals):
            _s41_violate("private_plan_nested_collection_invalid")
        if tuple(sorted(path_ordinals)) != path_ordinals:
            _s41_violate("private_plan_nested_collection_invalid")

    outputs = _s41_require_tuple(
        artifact["expected_outputs"],
        1,
        32,
        duplicate_free=False,
    )
    output_fields = ("output_ref", "owner_work_unit_ref", "output_kind", "description")
    output_kinds = (
        "source_change",
        "test_change",
        "documentation_change",
        "candidate_manifest",
        "validation_evidence",
    )
    output_refs: list[str] = []
    output_owners: dict[str, str] = {}
    for output in outputs:
        output = _s41_require_exact_mapping(
            output,
            output_fields,
            "private_plan_nested_collection_invalid",
        )
        _s41_require_safe_ref(output["output_ref"], "private_plan_nested_collection_invalid")
        if type(output["owner_work_unit_ref"]) is not str:
            _s41_violate("private_plan_nested_collection_invalid")
        if output["output_ref"] in output_refs or output["owner_work_unit_ref"] not in work_refs:
            _s41_violate("private_plan_nested_collection_invalid")
        if type(output["output_kind"]) is not str or output["output_kind"] not in output_kinds:
            _s41_violate("private_plan_closed_vocabulary_invalid")
        _s41_validate_narrative(output["description"], 512)
        output_refs.append(output["output_ref"])
        output_owners[output["output_ref"]] = output["owner_work_unit_ref"]

    validations = _s41_require_tuple(
        artifact["validation_strategy"],
        1,
        32,
        duplicate_free=False,
    )
    validation_fields = (
        "ordinal",
        "validation_ref",
        "work_unit_refs",
        "validation_kind",
        "target",
        "success_criterion",
    )
    validation_kinds = ("focused_test", "contract_test", "static_check", "build", "manual_review")
    validation_refs: list[str] = []
    for index, validation in enumerate(validations):
        validation = _s41_require_exact_mapping(
            validation,
            validation_fields,
            "private_plan_nested_collection_invalid",
        )
        if type(validation["ordinal"]) is not int or validation["ordinal"] != index:
            _s41_violate("private_plan_nested_collection_invalid")
        _s41_require_safe_ref(validation["validation_ref"], "private_plan_nested_collection_invalid")
        if validation["validation_ref"] in validation_refs:
            _s41_violate("private_plan_nested_collection_invalid")
        _s41_assert_ref_tuple_in_order(validation["work_unit_refs"], work_refs, 1, 32)
        if type(validation["validation_kind"]) is not str or validation["validation_kind"] not in validation_kinds:
            _s41_violate("private_plan_closed_vocabulary_invalid")
        _s41_validate_narrative(validation["target"], 512)
        _s41_validate_narrative(validation["success_criterion"], 512)
        validation_refs.append(validation["validation_ref"])

    assumptions = _s41_require_tuple(
        artifact["material_assumptions"],
        1,
        16,
        duplicate_free=False,
    )
    assumption_refs: set[str] = set()
    for assumption in assumptions:
        assumption = _s41_require_exact_mapping(
            assumption,
            ("assumption_ref", "statement"),
            "private_plan_nested_collection_invalid",
        )
        _s41_require_safe_ref(assumption["assumption_ref"], "private_plan_nested_collection_invalid")
        if assumption["assumption_ref"] in assumption_refs:
            _s41_violate("private_plan_nested_collection_invalid")
        assumption_refs.add(assumption["assumption_ref"])
        _s41_validate_narrative(assumption["statement"], 512)

    risks = _s41_require_tuple(
        artifact["risks_and_uncertainties"],
        1,
        16,
        duplicate_free=False,
    )
    risk_fields = (
        "risk_ref",
        "risk_kind",
        "description",
        "mitigation",
        "materiality",
        "affected_work_unit_refs",
    )
    risk_refs: set[str] = set()
    for risk in risks:
        risk = _s41_require_exact_mapping(
            risk,
            risk_fields,
            "private_plan_nested_collection_invalid",
        )
        _s41_require_safe_ref(risk["risk_ref"], "private_plan_nested_collection_invalid")
        if risk["risk_ref"] in risk_refs:
            _s41_violate("private_plan_nested_collection_invalid")
        risk_refs.add(risk["risk_ref"])
        if type(risk["risk_kind"]) is not str or risk["risk_kind"] not in ("correctness", "authority", "privacy", "compatibility", "operational", "unknown"):
            _s41_violate("private_plan_closed_vocabulary_invalid")
        if type(risk["materiality"]) is not str or risk["materiality"] not in ("material", "blocking"):
            _s41_violate("private_plan_closed_vocabulary_invalid")
        _s41_validate_narrative(risk["description"], 512)
        _s41_validate_narrative(risk["mitigation"], 512)
        _s41_assert_ref_tuple_in_order(risk["affected_work_unit_refs"], work_refs, 1, 32)

    prerequisites = _s41_require_tuple(
        artifact["required_evidence_and_prerequisites"],
        1,
        32,
        duplicate_free=False,
    )
    prerequisite_refs: list[str] = []
    prerequisite_roles: list[str] = []
    for prerequisite in prerequisites:
        prerequisite = _s41_require_exact_mapping(
            prerequisite,
            ("prerequisite_ref", "evidence_role", "requirement"),
            "private_plan_nested_collection_invalid",
        )
        _s41_require_safe_ref(prerequisite["prerequisite_ref"], "private_plan_nested_collection_invalid")
        if prerequisite["prerequisite_ref"] in prerequisite_refs:
            _s41_violate("private_plan_nested_collection_invalid")
        if type(prerequisite["evidence_role"]) is not str or prerequisite["evidence_role"] not in REPAIRED_EVIDENCE_ROLES:
            _s41_violate("private_plan_closed_vocabulary_invalid")
        prerequisite_refs.append(prerequisite["prerequisite_ref"])
        prerequisite_roles.append(prerequisite["evidence_role"])
        _s41_validate_narrative(prerequisite["requirement"], 512)
    prerequisite_role_ranks = tuple(
        REPAIRED_EVIDENCE_ROLES.index(role) for role in prerequisite_roles
    )
    if prerequisite_role_ranks != tuple(sorted(prerequisite_role_ranks)):
        _s41_violate("private_plan_prerequisite_order_invalid")

    stops = _s41_require_tuple(
        artifact["stop_or_replan_conditions"],
        1,
        16,
        duplicate_free=False,
    )
    stop_refs: list[str] = []
    for stop in stops:
        stop = _s41_require_exact_mapping(
            stop,
            ("stop_condition_ref", "statement"),
            "private_plan_nested_collection_invalid",
        )
        _s41_require_safe_ref(stop["stop_condition_ref"], "private_plan_nested_collection_invalid")
        if stop["stop_condition_ref"] in stop_refs:
            _s41_violate("private_plan_nested_collection_invalid")
        stop_refs.append(stop["stop_condition_ref"])
        _s41_validate_narrative(stop["statement"], 512)
    if tuple(stop_refs) != tuple(sorted(stop_refs)):
        _s41_violate("private_plan_nested_collection_invalid")

    for unit in work_units:
        _s41_assert_ref_tuple_in_order(unit["expected_output_refs"], tuple(output_refs), 1, 32)
        if any(output_owners[ref] != unit["work_unit_ref"] for ref in unit["expected_output_refs"]):
            _s41_violate("private_plan_nested_collection_invalid")
        _s41_assert_ref_tuple_in_order(unit["validation_refs"], tuple(validation_refs), 1, 32)
        _s41_assert_ref_tuple_in_order(unit["required_evidence_roles"], REPAIRED_EVIDENCE_ROLES, 1, 14)
        _s41_assert_ref_tuple_in_order(unit["prerequisite_refs"], tuple(prerequisite_refs), 1, 32)
        _s41_assert_ref_tuple_in_order(unit["stop_condition_refs"], tuple(stop_refs), 1, 16)
    if set(output_refs) != {ref for unit in work_units for ref in unit["expected_output_refs"]}:
        _s41_violate("private_plan_nested_collection_invalid")
    if set(validation_refs) != {ref for unit in work_units for ref in unit["validation_refs"]}:
        _s41_violate("private_plan_nested_collection_invalid")
    referenced_prerequisites = {
        ref for unit in work_units for ref in unit["prerequisite_refs"]
    }
    if referenced_prerequisites != set(prerequisite_refs):
        _s41_violate("private_plan_prerequisite_unreferenced")
    referenced_stops = {
        ref for unit in work_units for ref in unit["stop_condition_refs"]
    }
    if referenced_stops != set(stop_refs):
        _s41_violate("private_plan_stop_unreferenced")
    validations_by_ref = {
        validation["validation_ref"]: validation for validation in validations
    }
    units_by_ref = {unit["work_unit_ref"]: unit for unit in work_units}
    for unit in work_units:
        for validation_ref in unit["validation_refs"]:
            if unit["work_unit_ref"] not in validations_by_ref[validation_ref]["work_unit_refs"]:
                _s41_violate("private_plan_validation_link_asymmetric")
    for validation in validations:
        for work_unit_ref in validation["work_unit_refs"]:
            if validation["validation_ref"] not in units_by_ref[work_unit_ref]["validation_refs"]:
                _s41_violate("private_plan_validation_link_asymmetric")

    use = _s41_require_exact_mapping(
        artifact["proposed_resource_and_effect_use"],
        REPAIRED_RESOURCE_FIELDS,
        "private_plan_nested_collection_invalid",
    )
    effects = _s41_require_tuple(use["allowed_effect_classes"], 1, 5, duplicate_free=True)
    if not all(type(effect) is str and effect in REPAIRED_EFFECT_CLASSES for effect in effects):
        _s41_violate("private_plan_nested_collection_invalid")
    if tuple(effect for effect in REPAIRED_EFFECT_CLASSES if effect in effects) != effects:
        _s41_violate("private_plan_nested_collection_invalid")
    for ceiling in (attempt_effects, effect_effects):
        ceiling = _s41_require_tuple(
            ceiling,
            0,
            len(REPAIRED_EFFECT_CLASSES),
            duplicate_free=True,
        )
        if not all(
            type(effect) is str and effect in REPAIRED_EFFECT_CLASSES
            for effect in ceiling
        ):
            _s41_violate("private_plan_nested_collection_invalid")
        if tuple(
            effect for effect in REPAIRED_EFFECT_CLASSES if effect in ceiling
        ) != ceiling:
            _s41_violate("private_plan_nested_collection_invalid")
        if any(
            not any(_s41_exact_equal(effect, item) for item in ceiling)
            for effect in effects
        ):
            _s41_violate("private_plan_nested_collection_invalid")
    ceiling_sources = (
        REPAIRED_STANDING_CEILINGS if standing_ceilings is None else standing_ceilings,
        C2B3D_BASIS["attempt_aggregate_ceilings"] if attempt_ceilings is None else attempt_ceilings,
        C2B3D_BASIS["effect_ceilings"] if effect_ceilings is None else effect_ceilings,
    )
    for ceilings in ceiling_sources:
        ceilings = _s41_require_exact_mapping(
            ceilings,
            REPAIRED_RESOURCE_FIELDS[1:],
            "private_plan_nested_collection_invalid",
        )
        if any(
            not _s41_integer_fits_sqlite(ceilings[field])
            or ceilings[field] < 0
            for field in ceilings
        ):
            _s41_violate("private_plan_nested_collection_invalid")
    for field in REPAIRED_RESOURCE_FIELDS[1:]:
        if (
            not _s41_integer_fits_sqlite(use[field])
            or use[field] < 0
            or any(use[field] > ceilings[field] for ceilings in ceiling_sources)
        ):
            _s41_violate("private_plan_nested_collection_invalid")
    if type(artifact["recommendation"]) is not str or artifact["recommendation"] not in PRE_EXECUTION_RECOMMENDATIONS:
        _s41_violate("private_plan_closed_vocabulary_invalid")
    if type(artifact["reason_code"]) is not str or re.fullmatch(
        r"[a-z][a-z0-9_.-]{0,95}", artifact["reason_code"]
    ) is None:
        _s41_violate("private_plan_nested_collection_invalid")
    _s41_require_sha256(
        artifact["artifact_digest"],
        "private_plan_nested_collection_invalid",
    )
    artifact_size = len(_s41_canonical_bytes(artifact))
    if not 1 <= artifact_size <= 65_536:
        _s41_violate("private_plan_artifact_size_invalid")
    if artifact["artifact_digest"] != _s41_digest(
        REPAIRED_ARTIFACT_DOMAIN,
        _s41_without(artifact, "artifact_digest"),
    ):
        _s41_violate("private_plan_nested_collection_invalid")
    return artifact


def _sample_private_plan() -> dict[str, object]:
    prerequisites = tuple(
        {
            "prerequisite_ref": f"prerequisite.{ordinal:02d}",
            "evidence_role": role,
            "requirement": f"Verify required {role.replace('_', ' ')} evidence.",
        }
        for ordinal, role in enumerate(REPAIRED_EVIDENCE_ROLES)
    )
    prerequisite_refs = tuple(row["prerequisite_ref"] for row in prerequisites)
    shared_roles = REPAIRED_EVIDENCE_ROLES
    artifact: dict[str, object] = {
        "schema_id": REPAIRED_ARTIFACT_SCHEMA,
        "artifact_ref": "plan-artifact.private.repaired.0001",
        "proposal_ref": "model-proposal.pre.repaired.0001",
        "proposal_phase": "pre_execution_plan",
        "planning_context_ref": "planning-context.pre.absent.0001",
        "implementation_strategy": (
            "Update the bounded Section 41 contract and prove each relation causally.",
        ),
        "proposed_work_units": (
            {
                "ordinal": 0,
                "work_unit_ref": "work-unit.plan.0001",
                "action_kind": "analyze",
                "summary": "Reconcile the frozen semantic relations.",
                "depends_on_work_unit_refs": (),
                "authorized_path_ordinals": (0,),
                "expected_output_refs": ("output.contract.0001",),
                "validation_refs": ("validation.contract.0001",),
                "required_evidence_roles": shared_roles,
                "prerequisite_refs": prerequisite_refs,
                "stop_condition_refs": ("stop.scope.0001",),
            },
            {
                "ordinal": 1,
                "work_unit_ref": "work-unit.verify.0001",
                "action_kind": "run_validation",
                "summary": "Run the focused direct contract validations.",
                "depends_on_work_unit_refs": ("work-unit.plan.0001",),
                "authorized_path_ordinals": (0,),
                "expected_output_refs": ("output.evidence.0001",),
                "validation_refs": ("validation.focused.0001",),
                "required_evidence_roles": shared_roles,
                "prerequisite_refs": prerequisite_refs,
                "stop_condition_refs": ("stop.scope.0001",),
            },
        ),
        "affected_authorized_paths": (C2B3D_BASIS["authorized_paths"][0],),
        "expected_outputs": (
            {
                "output_ref": "output.contract.0001",
                "owner_work_unit_ref": "work-unit.plan.0001",
                "output_kind": "documentation_change",
                "description": "A closed repaired Section 41 contract.",
            },
            {
                "output_ref": "output.evidence.0001",
                "owner_work_unit_ref": "work-unit.verify.0001",
                "output_kind": "validation_evidence",
                "description": "Focused causal validation evidence.",
            },
        ),
        "validation_strategy": (
            {
                "ordinal": 0,
                "validation_ref": "validation.contract.0001",
                "work_unit_refs": ("work-unit.plan.0001",),
                "validation_kind": "contract_test",
                "target": "The repaired semantic owner.",
                "success_criterion": "Every owner relation matches the direct oracle.",
            },
            {
                "ordinal": 1,
                "validation_ref": "validation.focused.0001",
                "work_unit_refs": ("work-unit.verify.0001",),
                "validation_kind": "focused_test",
                "target": "The bounded causal mutants.",
                "success_criterion": "Each mutant reaches its exact named predicate.",
            },
        ),
        "material_assumptions": (
            {
                "assumption_ref": "assumption.scope.0001",
                "statement": "The repair remains contract and direct test work only.",
            },
        ),
        "risks_and_uncertainties": (
            {
                "risk_ref": "risk.drift.0001",
                "risk_kind": "correctness",
                "description": "A disconnected projection could drift from its private artifact.",
                "mitigation": "Derive and compare every projection field from one artifact.",
                "materiality": "blocking",
                "affected_work_unit_refs": (
                    "work-unit.plan.0001",
                    "work-unit.verify.0001",
                ),
            },
        ),
        "required_evidence_and_prerequisites": prerequisites,
        "stop_or_replan_conditions": (
            {
                "stop_condition_ref": "stop.scope.0001",
                "statement": "Stop if production or migration source would need to change.",
            },
        ),
        "proposed_resource_and_effect_use": {
            "allowed_effect_classes": ("author_candidate",),
            "max_active_invocations": 1,
            "max_candidate_bytes": 1_048_576,
            "max_changed_files": 2,
            "max_cost_microusd": 100_000,
            "max_cpu_seconds": 600,
            "max_deliveries": 0,
            "max_deployments": 0,
            "max_local_commits": 0,
            "max_memory_bytes": 2_147_483_648,
            "max_merges": 0,
            "max_model_input_tokens": 200_000,
            "max_model_output_tokens": 50_000,
            "max_pull_requests": 0,
            "max_pushes": 0,
            "max_wall_seconds": 1_800,
        },
        "recommendation": "select_for_dispatch_gates",
        "reason_code": "plan.bounded_contract_repair",
    }
    artifact["artifact_digest"] = _s41_digest(REPAIRED_ARTIFACT_DOMAIN, artifact)
    return artifact


def _s41_padded_narrative(prefix: str, length: int) -> str:
    assert type(prefix) is str and len(prefix.encode("utf-8")) <= length
    return prefix + "A" * (length - len(prefix.encode("utf-8")))


def _maximal_private_plan() -> dict[str, object]:
    artifact = deepcopy(_sample_private_plan())
    work_refs = tuple(f"work-unit.max.{index:02d}" for index in range(32))
    output_refs = tuple(f"output.max.{index:02d}" for index in range(32))
    validation_refs = tuple(f"validation.max.{index:02d}" for index in range(32))
    prerequisites = tuple(
        {
            "prerequisite_ref": f"prerequisite.max.{index:02d}",
            "evidence_role": (
                REPAIRED_EVIDENCE_ROLES[index]
                if index < len(REPAIRED_EVIDENCE_ROLES)
                else REPAIRED_EVIDENCE_ROLES[-1]
            ),
            "requirement": _s41_padded_narrative(f"Requirement {index:02d} ", 512),
        }
        for index in range(32)
    )
    prerequisite_refs = tuple(row["prerequisite_ref"] for row in prerequisites)
    stops = tuple(
        {
            "stop_condition_ref": f"stop.max.{index:02d}",
            "statement": _s41_padded_narrative(f"Stop {index:02d} ", 512),
        }
        for index in range(16)
    )
    stop_refs = tuple(row["stop_condition_ref"] for row in stops)
    artifact["implementation_strategy"] = tuple(
        _s41_padded_narrative(f"Strategy {index:02d} ", 768)
        for index in range(8)
    )
    artifact["proposed_work_units"] = tuple(
        {
            "ordinal": index,
            "work_unit_ref": work_refs[index],
            "action_kind": "analyze",
            "summary": _s41_padded_narrative(f"Work {index:02d} ", 512),
            "depends_on_work_unit_refs": (),
            "authorized_path_ordinals": (0,),
            "expected_output_refs": (output_refs[index],),
            "validation_refs": (validation_refs[index],),
            "required_evidence_roles": REPAIRED_EVIDENCE_ROLES,
            "prerequisite_refs": prerequisite_refs,
            "stop_condition_refs": stop_refs,
        }
        for index in range(32)
    )
    artifact["expected_outputs"] = tuple(
        {
            "output_ref": output_refs[index],
            "owner_work_unit_ref": work_refs[index],
            "output_kind": "documentation_change",
            "description": _s41_padded_narrative(f"Output {index:02d} ", 512),
        }
        for index in range(32)
    )
    artifact["validation_strategy"] = tuple(
        {
            "ordinal": index,
            "validation_ref": validation_refs[index],
            "work_unit_refs": (work_refs[index],),
            "validation_kind": "contract_test",
            "target": _s41_padded_narrative(f"Target {index:02d} ", 512),
            "success_criterion": _s41_padded_narrative(
                f"Criterion {index:02d} ",
                512,
            ),
        }
        for index in range(32)
    )
    artifact["material_assumptions"] = tuple(
        {
            "assumption_ref": f"assumption.max.{index:02d}",
            "statement": _s41_padded_narrative(f"Assumption {index:02d} ", 512),
        }
        for index in range(16)
    )
    artifact["risks_and_uncertainties"] = tuple(
        {
            "risk_ref": f"risk.max.{index:02d}",
            "risk_kind": "correctness",
            "description": _s41_padded_narrative(f"Risk {index:02d} ", 512),
            "mitigation": _s41_padded_narrative(f"Mitigation {index:02d} ", 512),
            "materiality": "blocking",
            "affected_work_unit_refs": (work_refs[index],),
        }
        for index in range(16)
    )
    artifact["required_evidence_and_prerequisites"] = prerequisites
    artifact["stop_or_replan_conditions"] = stops
    artifact["artifact_digest"] = _s41_digest(
        REPAIRED_ARTIFACT_DOMAIN,
        _s41_without(artifact, "artifact_digest"),
    )
    return artifact


def _private_plan_with_exact_canonical_size(target: int) -> dict[str, object]:
    assert type(target) is int and target > 0
    artifact = _maximal_private_plan()
    prerequisite_rows = artifact["required_evidence_and_prerequisites"]
    stop_rows = artifact["stop_or_replan_conditions"]
    for index, unit in enumerate(artifact["proposed_work_units"]):
        unit["required_evidence_roles"] = (
            prerequisite_rows[index]["evidence_role"],
        )
        unit["prerequisite_refs"] = (
            prerequisite_rows[index]["prerequisite_ref"],
        )
        unit["stop_condition_refs"] = (
            stop_rows[index % len(stop_rows)]["stop_condition_ref"],
        )
    slots = [
        *((unit, "summary") for unit in artifact["proposed_work_units"]),
        *((output, "description") for output in artifact["expected_outputs"]),
        *(
            (validation, field)
            for validation in artifact["validation_strategy"]
            for field in ("target", "success_criterion")
        ),
        *((assumption, "statement") for assumption in artifact["material_assumptions"]),
        *(
            (risk, field)
            for risk in artifact["risks_and_uncertainties"]
            for field in ("description", "mitigation")
        ),
        *(
            (prerequisite, "requirement")
            for prerequisite in artifact["required_evidence_and_prerequisites"]
        ),
        *((stop, "statement") for stop in artifact["stop_or_replan_conditions"]),
    ]

    def refresh() -> int:
        artifact["artifact_digest"] = _s41_digest(
            REPAIRED_ARTIFACT_DOMAIN,
            _s41_without(artifact, "artifact_digest"),
        )
        return len(_s41_canonical_bytes(artifact))

    size = refresh()
    assert size >= target
    for mapping, field in slots:
        original = mapping[field]
        mapping[field] = "A"
        reduced_size = refresh()
        if reduced_size <= target:
            delta = target - reduced_size
            assert 1 + delta <= len(original.encode("utf-8"))
            mapping[field] = "A" * (1 + delta)
            assert refresh() == target
            return artifact
        size = reduced_size
    raise AssertionError(("EXACT_PRIVATE_PLAN_SIZE_UNREACHABLE", target, size))


def _derive_safe_projection(
    artifact: dict[str, object],
    artifact_binding: dict[str, object],
    context: dict[str, object],
    proposal: dict[str, object],
) -> dict[str, object]:
    _validate_repaired_private_plan(artifact)
    artifact_binding = _s41_require_exact_mapping(
        artifact_binding,
        ("artifact_schema_id", "artifact_ref", "artifact_digest"),
        "safe_projection_derivation_mismatch",
    )
    if (
        type(artifact_binding["artifact_schema_id"]) is not str
        or type(artifact_binding["artifact_ref"]) is not str
        or type(artifact_binding["artifact_digest"]) is not str
    ):
        _s41_violate("safe_projection_derivation_mismatch")
    _s41_require_safe_ref(
        artifact_binding["artifact_ref"],
        "safe_projection_derivation_mismatch",
    )
    _s41_require_sha256(
        artifact_binding["artifact_digest"],
        "safe_projection_derivation_mismatch",
    )
    expected_artifact_binding = {
        "artifact_schema_id": artifact["schema_id"],
        "artifact_ref": artifact["artifact_ref"],
        "artifact_digest": artifact["artifact_digest"],
    }
    if not _s41_exact_equal(artifact_binding, expected_artifact_binding):
        _s41_violate("safe_projection_derivation_mismatch")
    expected_context_fields = (
        "planning_context_schema_id",
        "planning_context_ref",
        "planning_context_digest",
    )
    context = _s41_require_exact_mapping(
        context,
        expected_context_fields,
        "safe_projection_derivation_mismatch",
    )
    if any(type(context[field]) is not str for field in expected_context_fields):
        _s41_violate("safe_projection_derivation_mismatch")
    _s41_require_safe_ref(
        context["planning_context_ref"],
        "safe_projection_derivation_mismatch",
    )
    _s41_require_sha256(
        context["planning_context_digest"],
        "safe_projection_derivation_mismatch",
    )
    expected_context = {
        "planning_context_schema_id": "governed-execution.nwp-pre-execution-planning-context.v1",
        "planning_context_ref": artifact["planning_context_ref"],
        "planning_context_digest": context["planning_context_digest"],
    }
    if not _s41_exact_equal(context, expected_context):
        _s41_violate("safe_projection_derivation_mismatch")
    proposal = _s41_require_exact_mapping(
        proposal,
        ("proposal_ref", "proposal_phase", "recommendation", "reason_code"),
        "safe_projection_derivation_mismatch",
    )
    if any(type(value) is not str for value in proposal.values()):
        _s41_violate("safe_projection_derivation_mismatch")
    _s41_require_safe_ref(
        proposal["proposal_ref"],
        "safe_projection_derivation_mismatch",
    )
    expected_proposal = {
        "proposal_ref": artifact["proposal_ref"],
        "proposal_phase": artifact["proposal_phase"],
        "recommendation": artifact["recommendation"],
        "reason_code": artifact["reason_code"],
    }
    if not _s41_exact_equal(proposal, expected_proposal):
        _s41_violate("safe_projection_derivation_mismatch")
    component_values = {
        "affected_path_set_digest": artifact["affected_authorized_paths"],
        "expected_output_set_digest": artifact["expected_outputs"],
        "validation_strategy_digest": artifact["validation_strategy"],
        "assumption_set_digest": artifact["material_assumptions"],
        "risk_set_digest": artifact["risks_and_uncertainties"],
        "prerequisite_set_digest": artifact["required_evidence_and_prerequisites"],
        "stop_condition_set_digest": artifact["stop_or_replan_conditions"],
        "proposed_resource_effect_use_digest": artifact["proposed_resource_and_effect_use"],
    }
    projection: dict[str, object] = {
        "schema_id": REPAIRED_PROJECTION_SCHEMA,
        "proposal_ref": proposal["proposal_ref"],
        "proposal_phase": proposal["proposal_phase"],
        "artifact_schema_id": artifact_binding["artifact_schema_id"],
        "artifact_ref": artifact_binding["artifact_ref"],
        "artifact_digest": artifact_binding["artifact_digest"],
        "planning_context_schema_id": context["planning_context_schema_id"],
        "planning_context_ref": context["planning_context_ref"],
        "planning_context_digest": context["planning_context_digest"],
        "strategy_item_count": len(artifact["implementation_strategy"]),
        "work_unit_count": len(artifact["proposed_work_units"]),
        "affected_path_count": len(artifact["affected_authorized_paths"]),
        "affected_path_set_digest": _s41_digest(
            REPAIRED_COMPONENT_DOMAINS["affected_path_set_digest"],
            component_values["affected_path_set_digest"],
        ),
        "expected_output_count": len(artifact["expected_outputs"]),
        "expected_output_set_digest": _s41_digest(
            REPAIRED_COMPONENT_DOMAINS["expected_output_set_digest"],
            component_values["expected_output_set_digest"],
        ),
        "validation_step_count": len(artifact["validation_strategy"]),
        "validation_strategy_digest": _s41_digest(
            REPAIRED_COMPONENT_DOMAINS["validation_strategy_digest"],
            component_values["validation_strategy_digest"],
        ),
        "assumption_count": len(artifact["material_assumptions"]),
        "assumption_set_digest": _s41_digest(
            REPAIRED_COMPONENT_DOMAINS["assumption_set_digest"],
            component_values["assumption_set_digest"],
        ),
        "risk_count": len(artifact["risks_and_uncertainties"]),
        "risk_set_digest": _s41_digest(
            REPAIRED_COMPONENT_DOMAINS["risk_set_digest"],
            component_values["risk_set_digest"],
        ),
        "prerequisite_count": len(artifact["required_evidence_and_prerequisites"]),
        "prerequisite_set_digest": _s41_digest(
            REPAIRED_COMPONENT_DOMAINS["prerequisite_set_digest"],
            component_values["prerequisite_set_digest"],
        ),
        "stop_condition_count": len(artifact["stop_or_replan_conditions"]),
        "stop_condition_set_digest": _s41_digest(
            REPAIRED_COMPONENT_DOMAINS["stop_condition_set_digest"],
            component_values["stop_condition_set_digest"],
        ),
        "proposed_resource_effect_use_digest": _s41_digest(
            REPAIRED_COMPONENT_DOMAINS["proposed_resource_effect_use_digest"],
            component_values["proposed_resource_effect_use_digest"],
        ),
        "allowed_effect_classes": artifact["proposed_resource_and_effect_use"]["allowed_effect_classes"],
        "recommendation": proposal["recommendation"],
        "reason_code": proposal["reason_code"],
    }
    projection["safe_projection_digest"] = _s41_digest(
        REPAIRED_PROJECTION_DOMAIN,
        projection,
    )
    assert tuple(projection) == REPAIRED_PROJECTION_FIELDS
    return projection


def _sample_projection_inputs() -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    artifact = _sample_private_plan()
    planning_context = _sample_preselection_records()["planning_context"]
    binding = {
        "artifact_schema_id": artifact["schema_id"],
        "artifact_ref": artifact["artifact_ref"],
        "artifact_digest": artifact["artifact_digest"],
    }
    context = {
        "planning_context_schema_id": planning_context["schema_id"],
        "planning_context_ref": planning_context["planning_context_ref"],
        "planning_context_digest": planning_context["planning_context_digest"],
    }
    proposal = {
        "proposal_ref": artifact["proposal_ref"],
        "proposal_phase": artifact["proposal_phase"],
        "recommendation": artifact["recommendation"],
        "reason_code": artifact["reason_code"],
    }
    return artifact, binding, context, proposal


def _validate_safe_projection(
    supplied: object,
    artifact: dict[str, object],
    binding: dict[str, object],
    context: dict[str, object],
    proposal: dict[str, object],
) -> None:
    expected = _derive_safe_projection(artifact, binding, context, proposal)
    if not _s41_exact_equal(supplied, expected):
        _s41_violate("safe_projection_derivation_mismatch")


def test_private_plan_owner_and_oracle_select_identical_nested_grammar() -> None:
    owner = _parse_repaired_owner()["private_plan_grammar"]
    assert owner["every_closed_vocabulary_string_exact_type"] == "built-in str; subclasses invalid"
    assert owner["every_integer_exact_type"] == "built-in int; bool invalid"
    assert owner["every_mapping"].startswith("exact built-in dict")
    assert owner["complete_artifact_canonical_utf8_byte_length"] == (1, 65_536)
    assert owner["artifact_size_failure_reason"] == "private_plan_artifact_size_invalid"
    assert owner["artifact_size_check_precedes_safe_projection_and_physical_family_success"] is True
    assert owner["artifact_field_order"] == REPAIRED_ARTIFACT_FIELDS
    assert owner["resource_and_effect_use_field_order"] == REPAIRED_RESOURCE_FIELDS
    assert owner["narrative"] == {
        "exact_type": "built-in str",
        "normalization": "NFC",
        "trimmed": True,
        "nonempty": True,
        "requires_unicode_letter_or_number": True,
        "forbidden_unicode_categories": ("Cc",),
        "closed_placeholders_casefolded": (
            "...",
            "n/a",
            "none",
            "placeholder",
            "tbd",
            "todo",
            "unknown",
        ),
        "utf8_byte_limits": (
            ("implementation_strategy_item", 1, 768),
            ("work_unit_summary", 1, 512),
            ("output_description", 1, 512),
            ("validation_target", 1, 512),
            ("validation_success_criterion", 1, 512),
            ("assumption_statement", 1, 512),
            ("risk_description", 1, 512),
            ("risk_mitigation", 1, 512),
            ("prerequisite_requirement", 1, 512),
            ("stop_condition_statement", 1, 512),
        ),
    }
    assert owner["nested_collections"] == {
        "implementation_strategy": ("tuple", 1, 8, "duplicate-free", "author order", "bounded narrative items"),
        "proposed_work_units": ("tuple", 1, 32, "unique work_unit_ref", "canonical topological tuple order", "contiguous zero-based ordinal"),
        "depends_on_work_unit_refs": ("tuple", 0, 31, "duplicate-free", "canonical earlier-work-unit order", "every ref names an earlier tuple member; forward refs invalid"),
        "authorized_path_ordinals": ("tuple", 1, 64, "duplicate-free", "strict numeric order", "every ordinal resolves"),
        "expected_output_refs": ("tuple", 1, 32, "duplicate-free", "expected-output declaration order", "every ref resolves to an output owned by this work unit"),
        "validation_refs": ("tuple", 1, 32, "duplicate-free", "validation declaration order", "every ref resolves and is reciprocally covered by that validation"),
        "required_evidence_roles": ("tuple", 1, 14, "duplicate-free", "closed evidence-role order", "every role resolves"),
        "prerequisite_refs": ("tuple", 1, 32, "duplicate-free", "prerequisite declaration order", "every ref resolves"),
        "stop_condition_refs": ("tuple", 1, 16, "duplicate-free", "stop-condition declaration order", "every ref resolves"),
        "affected_authorized_paths": ("tuple", 1, 64, "duplicate-free", "transient WorkSpec authorized-path order", "every path is within WorkSpec and both fences"),
        "expected_outputs": ("tuple", 1, 32, "unique output_ref", "declaration order", "exactly one existing work-unit owner"),
        "validation_strategy": ("tuple", 1, 32, "unique validation_ref and contiguous ordinal", "declaration order", "work_unit_refs follow work-unit order"),
        "validation_work_unit_refs": ("tuple", 1, 32, "duplicate-free", "work-unit order", "every ref resolves"),
        "material_assumptions": ("tuple", 1, 16, "unique assumption_ref", "declaration order", "bounded narrative"),
        "risks_and_uncertainties": ("tuple", 1, 16, "unique risk_ref", "declaration order", "affected_work_unit_refs follow work-unit order"),
        "risk_affected_work_unit_refs": ("tuple", 1, 32, "duplicate-free", "work-unit order", "every ref resolves"),
        "required_evidence_and_prerequisites": ("tuple", 1, 32, "unique prerequisite_ref", "nondecreasing closed evidence-role rank then declaration order within equal role", "repeated roles permitted and every declaration referenced by at least one work unit"),
        "stop_or_replan_conditions": ("tuple", 1, 16, "unique stop_condition_ref", "safe-ref lexical order", "bounded narrative and every declaration referenced by at least one work unit"),
        "allowed_effect_classes": ("tuple", 1, 5, "duplicate-free", "canonical C2A effect-class order", "subset of AttemptFence and EffectFence"),
    }
    assert owner["closed_vocabularies"]["evidence_roles"] == REPAIRED_EVIDENCE_ROLES
    assert owner["closed_vocabularies"]["effect_classes"] == REPAIRED_EFFECT_CLASSES
    assert owner["validation_coverage"] == "bidirectional: every work-unit validation ref includes that work unit and every validation-covered work unit lists that validation"
    assert owner["work_unit_forward_dependency_valid"] is False
    artifact = _sample_private_plan()
    assert _validate_repaired_private_plan(artifact) is artifact


def test_f3_private_artifact_exact_canonical_byte_ceiling_is_enforced() -> None:
    below = _sample_private_plan()
    assert len(_s41_canonical_bytes(below)) < 65_536
    assert _validate_repaired_private_plan(below) is below

    boundary = _private_plan_with_exact_canonical_size(65_536)
    assert len(_s41_canonical_bytes(boundary)) == 65_536
    assert _validate_repaired_private_plan(boundary) is boundary
    records = _sample_preselection_records()
    projection = _derive_safe_projection(
        boundary,
        {
            "artifact_schema_id": boundary["schema_id"],
            "artifact_ref": boundary["artifact_ref"],
            "artifact_digest": boundary["artifact_digest"],
        },
        {
            "planning_context_schema_id": records["planning_context"]["schema_id"],
            "planning_context_ref": records["planning_context"]["planning_context_ref"],
            "planning_context_digest": records["planning_context"]["planning_context_digest"],
        },
        {
            "proposal_ref": boundary["proposal_ref"],
            "proposal_phase": boundary["proposal_phase"],
            "recommendation": boundary["recommendation"],
            "reason_code": boundary["reason_code"],
        },
    )
    assert projection["artifact_digest"] == boundary["artifact_digest"]

    minimally_oversized = _private_plan_with_exact_canonical_size(65_537)
    assert len(_s41_canonical_bytes(minimally_oversized)) == 65_537
    with pytest.raises(_ContractViolation) as minimal_caught:
        _validate_repaired_private_plan(minimally_oversized)
    assert minimal_caught.value.reason == "private_plan_artifact_size_invalid"

    reproduced_oversized = _maximal_private_plan()
    assert len(_s41_canonical_bytes(reproduced_oversized)) == 186_390
    with pytest.raises(_ContractViolation) as reproduced_caught:
        _validate_repaired_private_plan(reproduced_oversized)
    assert reproduced_caught.value.reason == "private_plan_artifact_size_invalid"


def test_forward_dependency_reaches_exact_forward_dependency_reason() -> None:
    artifact = deepcopy(_sample_private_plan())
    artifact["proposed_work_units"][0]["depends_on_work_unit_refs"] = (
        "work-unit.verify.0001",
    )
    artifact["artifact_digest"] = _s41_digest(
        REPAIRED_ARTIFACT_DOMAIN,
        _s41_without(artifact, "artifact_digest"),
    )
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_private_plan(artifact)
    assert caught.value.reason == "private_plan_forward_dependency"


@pytest.mark.parametrize("bad_text", ("placeholder", "Valid\u0080text"))
def test_placeholder_and_unicode_cc_reach_exact_narrative_reason(bad_text: str) -> None:
    artifact = deepcopy(_sample_private_plan())
    artifact["implementation_strategy"] = (bad_text,)
    artifact["artifact_digest"] = _s41_digest(
        REPAIRED_ARTIFACT_DOMAIN,
        _s41_without(artifact, "artifact_digest"),
    )
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_private_plan(artifact)
    assert caught.value.reason == "private_plan_narrative_invalid"


def test_scalar_resource_use_above_effect_fence_reaches_exact_nested_reason() -> None:
    artifact = deepcopy(_sample_private_plan())
    artifact["proposed_resource_and_effect_use"]["max_deliveries"] = 2
    artifact["artifact_digest"] = _s41_digest(
        REPAIRED_ARTIFACT_DOMAIN,
        _s41_without(artifact, "artifact_digest"),
    )
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_private_plan(artifact)
    assert caught.value.reason == "private_plan_nested_collection_invalid"


def test_affected_path_outside_effect_fence_reaches_exact_nested_reason() -> None:
    artifact = _sample_private_plan()
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_private_plan(
            artifact,
            effect_paths=(C2B3D_BASIS["authorized_paths"][1],),
        )
    assert caught.value.reason == "private_plan_nested_collection_invalid"


def test_closed_vocabulary_exact_string_subclass_reaches_exact_reason() -> None:
    class _StringSubclass(str):
        pass

    artifact = deepcopy(_sample_private_plan())
    artifact["recommendation"] = _StringSubclass("select_for_dispatch_gates")
    artifact["artifact_digest"] = _s41_digest(
        REPAIRED_ARTIFACT_DOMAIN,
        _s41_without(artifact, "artifact_digest"),
    )
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_private_plan(artifact)
    assert caught.value.reason == "private_plan_closed_vocabulary_invalid"


class _S41StringSubclass(str):
    pass


class _S41TupleSubclass(tuple):
    pass


class _S41DictSubclass(dict):
    pass


class _S41ListSubclass(list):
    pass


class _S41HostileHash:
    def __hash__(self) -> int:
        raise ValueError("HOSTILE_HASH_CALLED")


class _S41HostileEquality:
    def __eq__(self, other: object) -> bool:
        raise TypeError("HOSTILE_EQUALITY_CALLED")


def _s41_replace_key_with_subclass(
    mapping: dict[str, object],
    selected_key: str,
) -> dict[str, object]:
    return {
        (_S41StringSubclass(key) if key == selected_key else key): value
        for key, value in mapping.items()
    }


def test_f4_private_artifact_keys_digests_and_containers_are_exact_builtins() -> None:
    subclassed_key = _s41_replace_key_with_subclass(
        _sample_private_plan(),
        "artifact_digest",
    )
    with pytest.raises(_ContractViolation) as key_caught:
        _validate_repaired_private_plan(subclassed_key)
    assert key_caught.value.reason == "private_plan_nested_collection_invalid"

    subclassed_digest = deepcopy(_sample_private_plan())
    subclassed_digest["artifact_digest"] = _S41StringSubclass(
        subclassed_digest["artifact_digest"]
    )
    with pytest.raises(_ContractViolation) as digest_caught:
        _validate_repaired_private_plan(subclassed_digest)
    assert digest_caught.value.reason == "private_plan_nested_collection_invalid"

    subclassed_container = deepcopy(_sample_private_plan())
    subclassed_container["implementation_strategy"] = _S41TupleSubclass(
        subclassed_container["implementation_strategy"]
    )
    with pytest.raises(_ContractViolation) as container_caught:
        _validate_repaired_private_plan(subclassed_container)
    assert container_caught.value.reason == "private_plan_nested_collection_invalid"

    subclassed_mapping = _S41DictSubclass(_sample_private_plan())
    with pytest.raises(_ContractViolation) as mapping_caught:
        _validate_repaired_private_plan(subclassed_mapping)
    assert mapping_caught.value.reason == "private_plan_nested_collection_invalid"

    for mutation in ("missing", "extra"):
        malformed = deepcopy(_sample_private_plan())
        if mutation == "missing":
            del malformed["reason_code"]
        else:
            malformed["shadow_reason"] = "plan.shadow"
        with pytest.raises(_ContractViolation) as shape_caught:
            _validate_repaired_private_plan(malformed)
        assert shape_caught.value.reason == "private_plan_nested_collection_invalid"


@pytest.mark.parametrize(
    "case_name,expected_reason",
    (
        ("attempt_path_list", "private_plan_nested_collection_invalid"),
        ("effect_path_list", "private_plan_nested_collection_invalid"),
        ("attempt_effect_list", "private_plan_nested_collection_invalid"),
        ("effect_effect_list", "private_plan_nested_collection_invalid"),
        ("attempt_path_string_subclass", "private_plan_nested_collection_invalid"),
        ("effect_class_string_subclass", "private_plan_nested_collection_invalid"),
        ("standing_ceiling_mapping_subclass", "private_plan_nested_collection_invalid"),
        ("effect_ceiling_key_subclass", "private_plan_nested_collection_invalid"),
        ("attempt_ceiling_boolean", "private_plan_nested_collection_invalid"),
        ("effect_ceiling_huge_integer", "private_plan_nested_collection_invalid"),
        ("unhashable_attempt_path", "private_plan_nested_collection_invalid"),
        ("hostile_hash_effect", "private_plan_nested_collection_invalid"),
        ("hostile_output_owner_equality", "private_plan_nested_collection_invalid"),
        ("hostile_recommendation_equality", "private_plan_closed_vocabulary_invalid"),
        ("cyclic_path_container", "private_plan_nested_collection_invalid"),
    ),
)
def test_s41_audit_003_004_relation_inputs_are_exact_before_operations(
    case_name: str,
    expected_reason: str,
) -> None:
    artifact = _sample_private_plan()
    keyword_arguments: dict[str, object] = {}
    if case_name == "attempt_path_list":
        keyword_arguments["attempt_paths"] = list(C2B3D_BASIS["authorized_paths"])
    elif case_name == "effect_path_list":
        keyword_arguments["effect_paths"] = list(C2B3D_BASIS["authorized_paths"])
    elif case_name == "attempt_effect_list":
        keyword_arguments["attempt_effects"] = list(REPAIRED_EFFECT_CLASSES)
    elif case_name == "effect_effect_list":
        keyword_arguments["effect_effects"] = ["author_candidate"]
    elif case_name == "attempt_path_string_subclass":
        keyword_arguments["attempt_paths"] = (
            _S41StringSubclass(C2B3D_BASIS["authorized_paths"][0]),
        )
    elif case_name == "effect_class_string_subclass":
        keyword_arguments["effect_effects"] = (
            _S41StringSubclass("author_candidate"),
        )
    elif case_name == "standing_ceiling_mapping_subclass":
        keyword_arguments["standing_ceilings"] = _S41DictSubclass(
            REPAIRED_STANDING_CEILINGS
        )
    elif case_name == "effect_ceiling_key_subclass":
        keyword_arguments["effect_ceilings"] = _s41_replace_key_with_subclass(
            dict(C2B3D_BASIS["effect_ceilings"]),
            "max_active_invocations",
        )
    elif case_name == "attempt_ceiling_boolean":
        ceilings = dict(C2B3D_BASIS["attempt_aggregate_ceilings"])
        ceilings["max_active_invocations"] = True
        keyword_arguments["attempt_ceilings"] = ceilings
    elif case_name == "effect_ceiling_huge_integer":
        ceilings = dict(C2B3D_BASIS["effect_ceilings"])
        ceilings["max_active_invocations"] = SQLITE_INTEGER_MAX + 1
        keyword_arguments["effect_ceilings"] = ceilings
    elif case_name == "unhashable_attempt_path":
        keyword_arguments["attempt_paths"] = ([],)
    elif case_name == "hostile_hash_effect":
        keyword_arguments["effect_effects"] = (_S41HostileHash(),)
    elif case_name == "hostile_output_owner_equality":
        artifact["expected_outputs"][0]["owner_work_unit_ref"] = (
            _S41HostileEquality()
        )
    elif case_name == "hostile_recommendation_equality":
        artifact["recommendation"] = _S41HostileEquality()
    elif case_name == "cyclic_path_container":
        cyclic: list[object] = []
        cyclic.append(cyclic)
        keyword_arguments["attempt_paths"] = cyclic
    else:
        raise AssertionError(case_name)
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_private_plan(artifact, **keyword_arguments)
    assert type(caught.value) is _ContractViolation
    assert caught.value.reason == expected_reason


@pytest.mark.parametrize(
    "record_role,selected_key,expected_reason",
    (
        (
            "authority_observation",
            "authority_observation_digest",
            "authority_observation_shape_invalid",
        ),
        ("planning_context", "planning_context_digest", "preselection_timestamp_record_invalid"),
        ("source_invocation", "source_invocation_digest", "preselection_timestamp_record_invalid"),
        ("artifact_binding", "artifact_binding_digest", "preselection_timestamp_record_invalid"),
        ("evidence_binding", "evidence_binding_digest", "preselection_timestamp_record_invalid"),
        ("model_proposal", "proposal_digest", "preselection_timestamp_record_invalid"),
        ("evidence_set", "evidence_set_digest", "preselection_timestamp_record_invalid"),
    ),
)
def test_f4_active_timestamp_and_authority_mapping_keys_are_exact_builtins(
    record_role: str,
    selected_key: str,
    expected_reason: str,
) -> None:
    bundle = _sample_temporal_bundle()
    records = bundle["preselection_records"]
    if record_role == "authority_observation":
        bundle[record_role] = _s41_replace_key_with_subclass(
            bundle[record_role],
            selected_key,
        )
    elif record_role == "evidence_binding":
        rows = list(records["evidence_bindings"])
        rows[0] = _s41_replace_key_with_subclass(rows[0], selected_key)
        records["evidence_bindings"] = tuple(rows)
    else:
        records[record_role] = _s41_replace_key_with_subclass(
            records[record_role],
            selected_key,
        )
    clock_calls: list[str] = []
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: clock_calls.append("called"),
            trace=trace,
        )
    assert caught.value.reason == expected_reason
    assert clock_calls == []
    assert trace == ["receipt_lookup", "fresh_shape_preflight"]


@pytest.mark.parametrize("fence_role", ("attempt_fence", "effect_fence"))
@pytest.mark.parametrize("mutation", ("extra", "missing"))
def test_f4_attempt_and_effect_fence_inventories_are_exact_before_digest(
    fence_role: str,
    mutation: str,
) -> None:
    bundle = _sample_temporal_bundle()
    if mutation == "extra":
        bundle[fence_role]["shadow_expiry"] = "2026-08-22T12:36:04Z"
    else:
        del bundle[fence_role][
            "aggregate_ceilings" if fence_role == "attempt_fence" else "effect_ceilings"
        ]
    _redigest_fence_and_context(bundle, fence_role)
    clock_calls: list[str] = []
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: clock_calls.append("called"),
            trace=trace,
        )
    assert caught.value.reason == "preselection_timestamp_record_invalid"
    assert clock_calls == []
    assert trace == ["receipt_lookup", "fresh_shape_preflight"]


@pytest.mark.parametrize(
    "fence_role,mutation",
    (
        ("attempt_fence", "ceiling_mapping_subclass"),
        ("attempt_fence", "ceiling_key_subclass"),
        ("attempt_fence", "boolean_ceiling"),
        ("effect_fence", "ceiling_mapping_subclass"),
        ("effect_fence", "ceiling_key_subclass"),
        ("effect_fence", "boolean_ceiling"),
        ("attempt_fence", "path_list_subclass"),
        ("effect_fence", "path_list_subclass"),
        ("attempt_fence", "effect_list_subclass"),
    ),
)
def test_f4_nested_fence_mappings_scalars_and_containers_are_exact_before_digest(
    fence_role: str,
    mutation: str,
) -> None:
    bundle = _sample_temporal_bundle()
    fence = bundle[fence_role]
    ceilings_field = (
        "aggregate_ceilings" if fence_role == "attempt_fence" else "effect_ceilings"
    )
    if mutation == "ceiling_mapping_subclass":
        fence[ceilings_field] = _S41DictSubclass(fence[ceilings_field])
    elif mutation == "ceiling_key_subclass":
        fence[ceilings_field] = _s41_replace_key_with_subclass(
            fence[ceilings_field],
            "max_active_invocations",
        )
    elif mutation == "boolean_ceiling":
        fence[ceilings_field]["max_active_invocations"] = True
    elif mutation == "path_list_subclass":
        fence["path_ceiling"] = _S41ListSubclass(fence["path_ceiling"])
    else:
        assert fence_role == "attempt_fence" and mutation == "effect_list_subclass"
        fence["allowed_effect_classes"] = _S41ListSubclass(
            fence["allowed_effect_classes"]
        )
    clock_calls: list[str] = []
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=REPAIRED_FRESH_MUTATION_REF,
            command_digest=REPAIRED_FRESH_COMMAND_DIGEST,
            receipt=None,
            bundle=bundle,
            clock=lambda: clock_calls.append("called"),
            trace=trace,
        )
    assert caught.value.reason == "preselection_timestamp_record_invalid"
    assert clock_calls == []
    assert trace == ["receipt_lookup", "fresh_shape_preflight"]


def test_multiple_same_role_prerequisites_follow_declaration_order() -> None:
    artifact = deepcopy(_sample_private_plan())
    duplicate_role = {
        "prerequisite_ref": "prerequisite.00b",
        "evidence_role": "standing_policy",
        "requirement": "Verify the second standing policy declaration.",
    }
    artifact["required_evidence_and_prerequisites"] = (
        artifact["required_evidence_and_prerequisites"][0],
        duplicate_role,
        *artifact["required_evidence_and_prerequisites"][1:],
    )
    for unit in artifact["proposed_work_units"]:
        unit["prerequisite_refs"] = (
            unit["prerequisite_refs"][0],
            duplicate_role["prerequisite_ref"],
            *unit["prerequisite_refs"][1:],
        )
    artifact["artifact_digest"] = _s41_digest(
        REPAIRED_ARTIFACT_DOMAIN,
        _s41_without(artifact, "artifact_digest"),
    )
    assert _validate_repaired_private_plan(artifact) is artifact


def test_unreferenced_prerequisite_reaches_exact_reason() -> None:
    artifact = deepcopy(_sample_private_plan())
    artifact["required_evidence_and_prerequisites"] += (
        {
            "prerequisite_ref": "prerequisite.14",
            "evidence_role": "review_requirement",
            "requirement": "Verify the additional review prerequisite.",
        },
    )
    artifact["artifact_digest"] = _s41_digest(
        REPAIRED_ARTIFACT_DOMAIN,
        _s41_without(artifact, "artifact_digest"),
    )
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_private_plan(artifact)
    assert caught.value.reason == "private_plan_prerequisite_unreferenced"


def test_unreferenced_stop_condition_reaches_exact_reason() -> None:
    artifact = deepcopy(_sample_private_plan())
    artifact["stop_or_replan_conditions"] += (
        {
            "stop_condition_ref": "stop.unused.0001",
            "statement": "Stop if the bounded evidence becomes unavailable.",
        },
    )
    artifact["artifact_digest"] = _s41_digest(
        REPAIRED_ARTIFACT_DOMAIN,
        _s41_without(artifact, "artifact_digest"),
    )
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_private_plan(artifact)
    assert caught.value.reason == "private_plan_stop_unreferenced"


def test_validation_linked_to_wrong_work_unit_reaches_exact_reason() -> None:
    artifact = deepcopy(_sample_private_plan())
    artifact["validation_strategy"][0]["work_unit_refs"] = (
        "work-unit.verify.0001",
    )
    artifact["artifact_digest"] = _s41_digest(
        REPAIRED_ARTIFACT_DOMAIN,
        _s41_without(artifact, "artifact_digest"),
    )
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_private_plan(artifact)
    assert caught.value.reason == "private_plan_validation_link_asymmetric"


def test_reverse_asymmetric_validation_link_reaches_exact_reason() -> None:
    artifact = deepcopy(_sample_private_plan())
    artifact["proposed_work_units"][1]["validation_refs"] = (
        "validation.contract.0001",
        "validation.focused.0001",
    )
    artifact["artifact_digest"] = _s41_digest(
        REPAIRED_ARTIFACT_DOMAIN,
        _s41_without(artifact, "artifact_digest"),
    )
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_private_plan(artifact)
    assert caught.value.reason == "private_plan_validation_link_asymmetric"


@pytest.mark.parametrize(
    "field,bad_value",
    (
        ("reason_code", "different.reason"),
        ("artifact_ref", "different-artifact.0001"),
        ("planning_context_ref", "different-context.0001"),
        ("work_unit_count", 3),
        ("allowed_effect_classes", ("validate_candidate",)),
        ("safe_projection_digest", "c" * 64),
    ),
)
def test_every_independent_projection_mutation_reaches_derivation_reason(
    field: str,
    bad_value: object,
) -> None:
    artifact, binding, context, proposal = _sample_projection_inputs()
    projection = _derive_safe_projection(artifact, binding, context, proposal)
    projection[field] = bad_value
    with pytest.raises(_ContractViolation) as caught:
        _validate_safe_projection(projection, artifact, binding, context, proposal)
    assert caught.value.reason == "safe_projection_derivation_mismatch"


def test_safe_projection_is_fully_derived_and_self_digested() -> None:
    owner = _parse_repaired_owner()["safe_projection_derivation"]
    assert owner["field_order"] == REPAIRED_PROJECTION_FIELDS
    assert owner["component_digest_sources"] == tuple(
        (projection_field, artifact_field)
        for projection_field, artifact_field in (
            ("affected_path_set_digest", "affected_authorized_paths"),
            ("expected_output_set_digest", "expected_outputs"),
            ("validation_strategy_digest", "validation_strategy"),
            ("assumption_set_digest", "material_assumptions"),
            ("risk_set_digest", "risks_and_uncertainties"),
            ("prerequisite_set_digest", "required_evidence_and_prerequisites"),
            ("stop_condition_set_digest", "stop_or_replan_conditions"),
            ("proposed_resource_effect_use_digest", "proposed_resource_and_effect_use"),
        )
    )
    artifact, binding, context, proposal = _sample_projection_inputs()
    projection = _derive_safe_projection(artifact, binding, context, proposal)
    _validate_safe_projection(projection, artifact, binding, context, proposal)
    assert projection["safe_projection_digest"] == _s41_digest(
        REPAIRED_PROJECTION_DOMAIN,
        _s41_without(projection, "safe_projection_digest"),
    )


def test_every_safe_projection_field_is_checked_against_its_derivation() -> None:
    artifact, binding, context, proposal = _sample_projection_inputs()
    projection = _derive_safe_projection(artifact, binding, context, proposal)
    for field, value in projection.items():
        mutant = deepcopy(projection)
        if type(value) is int:
            replacement: object = value + 1
        elif type(value) is tuple:
            replacement = value + ("mutant",)
        elif type(value) is str and len(value) == 64:
            replacement = "f" * 64 if value != "f" * 64 else "e" * 64
        else:
            replacement = value + ".mutant"
        mutant[field] = replacement
        with pytest.raises(_ContractViolation) as caught:
            _validate_safe_projection(mutant, artifact, binding, context, proposal)
        assert caught.value.reason == "safe_projection_derivation_mismatch", field


def test_safe_projection_input_bindings_fail_with_one_exact_reason() -> None:
    artifact, binding, context, proposal = _sample_projection_inputs()
    mutations = []
    bad_binding = dict(binding)
    bad_binding["artifact_ref"] = "artifact.changed.0001"
    mutations.append((bad_binding, context, proposal))
    bad_context = dict(context)
    del bad_context["planning_context_digest"]
    mutations.append((binding, bad_context, proposal))
    bad_proposal = dict(proposal)
    bad_proposal["reason_code"] = "plan.changed"
    mutations.append((binding, context, bad_proposal))
    for mutated_binding, mutated_context, mutated_proposal in mutations:
        with pytest.raises(_ContractViolation) as caught:
            _derive_safe_projection(
                artifact,
                mutated_binding,
                mutated_context,
                mutated_proposal,
            )
        assert caught.value.reason == "safe_projection_derivation_mismatch"


REPAIRED_TABLE_ORDER = (
    "development_model_source_invocations",
    "development_pre_execution_planning_contexts",
    "development_private_proposal_artifact_bindings",
    "development_model_proposals",
    "development_pre_execution_plan_projections",
    "development_model_proposal_evidence_bindings",
    "development_pre_execution_dispositions",
    "development_pre_execution_selection_heads",
    "development_cognitive_mutation_receipts",
)
REPAIRED_GRAPH_ROLE_INVENTORY = (
    ("source_invocation", 0, REPAIRED_TABLE_ORDER[0]),
    ("planning_context", 1, REPAIRED_TABLE_ORDER[1]),
    ("private_artifact_binding", 2, REPAIRED_TABLE_ORDER[2]),
    ("model_proposal", 3, REPAIRED_TABLE_ORDER[3]),
    ("pre_execution_plan_projection", 4, REPAIRED_TABLE_ORDER[4]),
    ("evidence.standing_policy", 5, REPAIRED_TABLE_ORDER[5]),
    ("evidence.risk_lane", 6, REPAIRED_TABLE_ORDER[5]),
    ("evidence.repository_binding", 7, REPAIRED_TABLE_ORDER[5]),
    ("evidence.base_binding", 8, REPAIRED_TABLE_ORDER[5]),
    ("evidence.authorized_path_scope", 9, REPAIRED_TABLE_ORDER[5]),
    ("evidence.cost_ceiling", 10, REPAIRED_TABLE_ORDER[5]),
    ("evidence.token_ceiling", 11, REPAIRED_TABLE_ORDER[5]),
    ("evidence.time_ceiling", 12, REPAIRED_TABLE_ORDER[5]),
    ("evidence.delivery_ceiling", 13, REPAIRED_TABLE_ORDER[5]),
    ("evidence.effect_ceiling", 14, REPAIRED_TABLE_ORDER[5]),
    ("evidence.authority_selection_observation", 15, REPAIRED_TABLE_ORDER[5]),
    ("evidence.global_stop", 16, REPAIRED_TABLE_ORDER[5]),
    ("evidence.validation_requirement", 17, REPAIRED_TABLE_ORDER[5]),
    ("evidence.review_requirement", 18, REPAIRED_TABLE_ORDER[5]),
    ("evidence.qualified_remote_host_readiness", 19, REPAIRED_TABLE_ORDER[5]),
    ("coordinator_disposition", 20, REPAIRED_TABLE_ORDER[6]),
    ("selection_head_postimage", 21, REPAIRED_TABLE_ORDER[7]),
)
REPAIRED_ROW_FIELDS = ("table", "role", "rank", "ordinal", "values")
REPAIRED_GRAPH_FIELDS = (
    "mutation_ref",
    "command_digest",
    "entries",
    "mutation_graph_digest",
)
REPAIRED_RESULT_PROJECTION_FIELDS = (
    "schema_id",
    "mutation_ref",
    "command_digest",
    "proposal_ref",
    "disposition_ref",
    "disposition_digest",
    "disposition",
    "program_ref",
    "semantic_attempt_ref",
    "candidate_ref",
    "effect_intent_ref",
    "selection_head_revision",
    "selection_head_digest",
    "authority_selection_observation_ref",
    "authority_selection_observation_digest",
    "mutation_graph_digest",
    "recorded_at",
    "result_projection_digest",
)
REPAIRED_FRESH_RESULT_FIELDS = REPAIRED_RESULT_PROJECTION_FIELDS + (
    "receipt_digest",
)
REPAIRED_COMMAND_DOMAIN = (
    "governed-execution.nwp-record-pre-execution-plan-disposition-command.v1.identity"
)
REPAIRED_COMMAND_FIELD_SPECS = (
    ("schema_id", f"literal:{SCHEMA_IDS['safe_command']}", "contract constant"),
    ("mutation_ref", "safe_ref", "Coordinator preassignment"),
    ("proposal_ref", "safe_ref", "model proposal"),
    ("proposal_digest", "sha256", "model proposal"),
    ("source_invocation_ref", "safe_ref", "source invocation"),
    ("source_invocation_digest", "sha256", "source invocation"),
    ("artifact_ref", "safe_ref", "private artifact binding"),
    ("artifact_digest", "sha256", "private artifact binding"),
    ("artifact_binding_digest", "sha256", "private artifact binding"),
    ("planning_context_ref", "safe_ref", "planning context"),
    ("planning_context_digest", "sha256", "planning context"),
    ("safe_projection_digest", "sha256", "safe projection"),
    ("evidence_set_ref", "safe_ref", "model proposal"),
    ("evidence_set_digest", "sha256", "model proposal"),
    ("preassigned_disposition_ref", "safe_ref", "Coordinator preassignment"),
    ("expected_current_selection_revision", "nullable_nonnegative_int", "disposition CAS preimage"),
    ("expected_current_selection_head_digest", "nullable_sha256", "disposition CAS preimage"),
    ("disposition", "pre_execution_disposition", "Coordinator decision"),
    ("disposition_reason_code", "reason_code", "Coordinator decision"),
    ("supersedes_disposition_ref", "nullable_safe_ref", "disposition CAS preimage"),
    ("program_ref", "safe_ref", "canonical C2B3D lineage"),
    ("semantic_attempt_ref", "safe_ref", "canonical C2B3D lineage"),
    ("candidate_ref", "safe_ref", "canonical C2B3D lineage"),
    ("effect_intent_ref", "safe_ref", "canonical C2B3D lineage"),
    ("author_command_ref", "safe_ref", "canonical C2B3D lineage"),
    ("author_command_digest", "sha256", "canonical C2B3D lineage"),
    ("attempt_fence_ref", "safe_ref", "canonical C2B3D lineage"),
    ("attempt_fence_digest", "sha256", "canonical C2B3D lineage"),
    ("effect_fence_ref", "safe_ref", "canonical C2B3D lineage"),
    ("effect_fence_digest", "sha256", "canonical C2B3D lineage"),
    ("delivery_attempt_ref", "safe_ref", "canonical C2B3D lineage"),
    ("delivery_envelope_digest", "sha256", "canonical C2B3D lineage"),
    ("mutation_command_digest", "sha256", "command self-digest"),
)
assert tuple(field for field, _kind, _source in REPAIRED_COMMAND_FIELD_SPECS) == SAFE_COMMAND_FIELD_ORDER
REPAIRED_DISPOSITION_COLUMNS = tuple(
    (
        (
            ("proposal_phase", "literal:pre_execution_plan"),
        )
        if name == "proposal_digest"
        else ()
    )
    + (
        (
            ("prior_selection_head_revision", "selection_prior_revision"),
            ("prior_selection_head_digest", "nullable_sha256"),
        )
        if name == "resulting_selection_head_revision"
        else ()
    )
    + (
        (
            ("authority_selection_observation_ref", "safe_ref"),
            ("authority_selection_observation_digest", "sha256"),
        )
        if name == "coordinator_disposition_decided_at"
        else ()
    )
    + ((name, kind),)
    for name, kind in TABLE_CONTRACTS["development_pre_execution_dispositions"]["columns"]
)
REPAIRED_DISPOSITION_COLUMNS = tuple(
    item for group in REPAIRED_DISPOSITION_COLUMNS for item in group
)


def _columns_with_complete_c2b3d_lineage(
    columns: tuple[tuple[str, str], ...],
    *,
    digest_field: str,
) -> tuple[tuple[str, str], ...]:
    existing_fields = tuple(field for field, _kind in columns)
    missing_lineage = tuple(
        (field, kind)
        for field, kind in REPAIRED_C2B3D_LINEAGE_FIELD_SPECS
        if field not in existing_fields
    )
    completed: list[tuple[str, str]] = []
    for specification in columns:
        if specification[0] == digest_field:
            completed.extend(missing_lineage)
        completed.append(specification)
    result = tuple(completed)
    result_fields = tuple(field for field, _kind in result)
    assert len(result_fields) == len(set(result_fields))
    assert all(field in result_fields for field in REPAIRED_C2B3D_LINEAGE_FIELDS)
    assert result_fields[-1] == digest_field
    return result


REPAIRED_DISPOSITION_COLUMNS = _columns_with_complete_c2b3d_lineage(
    REPAIRED_DISPOSITION_COLUMNS,
    digest_field="disposition_digest",
)
REPAIRED_SELECTION_HEAD_COLUMNS = _columns_with_complete_c2b3d_lineage(
    TABLE_CONTRACTS["development_pre_execution_selection_heads"]["columns"],
    digest_field="head_digest",
)
REPAIRED_SELECTION_HEAD_ALL_IMMUTABLE_FIELDS = tuple(
    field
    for field, _kind in REPAIRED_SELECTION_HEAD_COLUMNS
    if field not in REPAIRED_SELECTION_HEAD_MUTABLE_CAS_FIELDS
)
assert set(REPAIRED_SELECTION_HEAD_IMMUTABLE_FIELDS).issubset(
    REPAIRED_SELECTION_HEAD_ALL_IMMUTABLE_FIELDS
)
REPAIRED_RECEIPT_COLUMNS = tuple(
    (
        (
            ("disposition_digest", "sha256"),
            ("authority_selection_observation_ref", "safe_ref"),
            ("authority_selection_observation_digest", "sha256"),
        )
        if name == "effect_intent_ref"
        else ()
    )
    + ((name, kind),)
    for name, kind in TABLE_CONTRACTS["development_cognitive_mutation_receipts"]["columns"]
)
REPAIRED_RECEIPT_COLUMNS = tuple(
    item for group in REPAIRED_RECEIPT_COLUMNS for item in group
)
REPAIRED_PROJECTION_COLUMNS = (
    ("schema_id", f"literal:{REPAIRED_PROJECTION_SCHEMA}"),
    ("proposal_ref", "safe_ref"),
    ("proposal_phase", "literal:pre_execution_plan"),
    ("artifact_schema_id", f"literal:{REPAIRED_ARTIFACT_SCHEMA}"),
    ("artifact_ref", "safe_ref"),
    ("artifact_digest", "sha256"),
    ("planning_context_schema_id", f"literal:{SCHEMA_IDS['pre_execution_context']}"),
    ("planning_context_ref", "safe_ref"),
    ("planning_context_digest", "sha256"),
    ("strategy_item_count", "int:1..8"),
    ("work_unit_count", "int:1..32"),
    ("affected_path_count", "int:1..64"),
    ("affected_path_set_digest", "sha256"),
    ("expected_output_count", "int:1..32"),
    ("expected_output_set_digest", "sha256"),
    ("validation_step_count", "int:1..32"),
    ("validation_strategy_digest", "sha256"),
    ("assumption_count", "int:1..16"),
    ("assumption_set_digest", "sha256"),
    ("risk_count", "int:1..16"),
    ("risk_set_digest", "sha256"),
    ("prerequisite_count", "int:1..32"),
    ("prerequisite_set_digest", "sha256"),
    ("stop_condition_count", "int:1..16"),
    ("stop_condition_set_digest", "sha256"),
    ("proposed_resource_effect_use_digest", "sha256"),
    ("allowed_effect_classes", "canonical_effect_class_json"),
    ("recommendation", "pre_execution_recommendation"),
    ("reason_code", "reason_code"),
    ("safe_projection_digest", "sha256"),
)
REPAIRED_TABLE_COLUMNS = {
    REPAIRED_TABLE_ORDER[0]: TABLE_CONTRACTS[REPAIRED_TABLE_ORDER[0]]["columns"],
    REPAIRED_TABLE_ORDER[1]: REPAIRED_PLANNING_CONTEXT_COLUMNS,
    REPAIRED_TABLE_ORDER[2]: TABLE_CONTRACTS[REPAIRED_TABLE_ORDER[2]]["columns"],
    REPAIRED_TABLE_ORDER[3]: TABLE_CONTRACTS[REPAIRED_TABLE_ORDER[3]]["columns"],
    REPAIRED_TABLE_ORDER[4]: REPAIRED_PROJECTION_COLUMNS,
    REPAIRED_TABLE_ORDER[5]: TABLE_CONTRACTS[REPAIRED_TABLE_ORDER[5]]["columns"],
    REPAIRED_TABLE_ORDER[6]: REPAIRED_DISPOSITION_COLUMNS,
    REPAIRED_TABLE_ORDER[7]: REPAIRED_SELECTION_HEAD_COLUMNS,
    REPAIRED_TABLE_ORDER[8]: REPAIRED_RECEIPT_COLUMNS,
}
REPAIRED_TABLE_DIGESTS = {
    REPAIRED_TABLE_ORDER[0]: ("source_invocation_digest", DIGEST_DOMAINS["source_invocation"]),
    REPAIRED_TABLE_ORDER[1]: ("planning_context_digest", DIGEST_DOMAINS["pre_execution_context"]),
    REPAIRED_TABLE_ORDER[2]: ("artifact_binding_digest", DIGEST_DOMAINS["artifact_binding"]),
    REPAIRED_TABLE_ORDER[3]: ("proposal_digest", DIGEST_DOMAINS["proposal"]),
    REPAIRED_TABLE_ORDER[4]: ("safe_projection_digest", REPAIRED_PROJECTION_DOMAIN),
    REPAIRED_TABLE_ORDER[5]: ("evidence_binding_digest", DIGEST_DOMAINS["evidence_binding"]),
    REPAIRED_TABLE_ORDER[6]: ("disposition_digest", DIGEST_DOMAINS["disposition"]),
    REPAIRED_TABLE_ORDER[7]: ("head_digest", DIGEST_DOMAINS["selection_head"]),
    REPAIRED_TABLE_ORDER[8]: ("receipt_digest", DIGEST_DOMAINS["receipt"]),
}


def _persisted_projection(projection: dict[str, object]) -> dict[str, object]:
    persisted = deepcopy(projection)
    persisted["allowed_effect_classes"] = _s41_canonical_bytes(
        projection["allowed_effect_classes"]
    ).decode("utf-8")
    return persisted


def _member_digest(member: dict[str, object]) -> str:
    digest_field, _domain = REPAIRED_TABLE_DIGESTS[member["table"]]
    return member["values"][digest_field]


def _member_locator(member: dict[str, object]) -> tuple[tuple[str, object], ...]:
    values = member["values"]
    if member["table"] == REPAIRED_TABLE_ORDER[5]:
        fields = ("proposal_ref", "evidence_role", "ordinal")
    elif member["table"] == REPAIRED_TABLE_ORDER[7]:
        fields = REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS
    else:
        fields = {
            REPAIRED_TABLE_ORDER[0]: ("source_invocation_ref",),
            REPAIRED_TABLE_ORDER[1]: ("planning_context_ref",),
            REPAIRED_TABLE_ORDER[2]: ("artifact_ref",),
            REPAIRED_TABLE_ORDER[3]: ("proposal_ref",),
            REPAIRED_TABLE_ORDER[4]: ("proposal_ref",),
            REPAIRED_TABLE_ORDER[6]: ("disposition_ref",),
            REPAIRED_TABLE_ORDER[8]: ("mutation_ref",),
        }[member["table"]]
    return tuple((field, values[field]) for field in fields)


def _derive_physical_write_order(
    physical_rows: tuple[dict[str, object], ...],
) -> tuple[tuple[str, tuple[tuple[str, object], ...]], ...]:
    assert type(physical_rows) is tuple
    return tuple(
        (member["table"], _member_locator(member))
        for member in physical_rows
    )


def _derive_repaired_graph(
    rows: tuple[dict[str, object], ...],
    *,
    mutation_ref: str,
    command_digest: str,
) -> dict[str, object]:
    entries = tuple(
        {
            "role": row["role"],
            "rank": row["rank"],
            "ordinal": row["ordinal"],
            "table": row["table"],
            "locator": _member_locator(row),
            "member_digest": _member_digest(row),
        }
        for row in rows
        if row["rank"] is not None
    )
    graph: dict[str, object] = {
        "mutation_ref": mutation_ref,
        "command_digest": command_digest,
        "entries": entries,
    }
    graph["mutation_graph_digest"] = _s41_digest(
        "governed-execution.nwp-cognitive-mutation-graph.v1.identity",
        graph,
    )
    return graph


def _derive_repaired_command(
    rows_by_role: dict[str, dict[str, object]],
    *,
    mutation_ref: str,
) -> dict[str, object]:
    source = rows_by_role["source_invocation"]["values"]
    context = rows_by_role["planning_context"]["values"]
    artifact = rows_by_role["private_artifact_binding"]["values"]
    proposal = rows_by_role["model_proposal"]["values"]
    projection = rows_by_role["pre_execution_plan_projection"]["values"]
    disposition = rows_by_role["coordinator_disposition"]["values"]
    command: dict[str, object] = {
        "schema_id": SCHEMA_IDS["safe_command"],
        "mutation_ref": mutation_ref,
        "proposal_ref": proposal["proposal_ref"],
        "proposal_digest": proposal["proposal_digest"],
        "source_invocation_ref": source["source_invocation_ref"],
        "source_invocation_digest": source["source_invocation_digest"],
        "artifact_ref": artifact["artifact_ref"],
        "artifact_digest": artifact["artifact_digest"],
        "artifact_binding_digest": artifact["artifact_binding_digest"],
        "planning_context_ref": context["planning_context_ref"],
        "planning_context_digest": context["planning_context_digest"],
        "safe_projection_digest": projection["safe_projection_digest"],
        "evidence_set_ref": proposal["evidence_set_ref"],
        "evidence_set_digest": proposal["evidence_set_digest"],
        "preassigned_disposition_ref": disposition["disposition_ref"],
        "expected_current_selection_revision": disposition[
            "expected_selection_head_revision"
        ],
        "expected_current_selection_head_digest": disposition[
            "expected_selection_head_digest"
        ],
        "disposition": disposition["disposition"],
        "disposition_reason_code": disposition["reason_code"],
        "supersedes_disposition_ref": disposition["supersedes_disposition_ref"],
        "program_ref": context["program_ref"],
        "semantic_attempt_ref": context["semantic_attempt_ref"],
        "candidate_ref": context["candidate_ref"],
        "effect_intent_ref": context["effect_intent_ref"],
        "author_command_ref": context["author_command_ref"],
        "author_command_digest": context["author_command_digest"],
        "attempt_fence_ref": context["attempt_fence_ref"],
        "attempt_fence_digest": context["attempt_fence_digest"],
        "effect_fence_ref": context["effect_fence_ref"],
        "effect_fence_digest": context["effect_fence_digest"],
        "delivery_attempt_ref": context["delivery_attempt_ref"],
        "delivery_envelope_digest": context["delivery_envelope_digest"],
    }
    command["mutation_command_digest"] = _s41_digest(
        REPAIRED_COMMAND_DOMAIN,
        command,
    )
    assert tuple(command) == SAFE_COMMAND_FIELD_ORDER
    return command


def _validate_repaired_command(
    supplied: object,
    rows_by_role: dict[str, dict[str, object]],
    *,
    mutation_ref: str,
) -> dict[str, object]:
    command = _s41_require_exact_mapping(
        supplied,
        SAFE_COMMAND_FIELD_ORDER,
        "physical_family_receipt_binding_mismatch",
    )
    if any(
        not _repaired_value_matches_kind(command[field], kind)
        for field, kind, _source in REPAIRED_COMMAND_FIELD_SPECS
    ):
        _s41_violate("physical_family_receipt_binding_mismatch")
    if command["mutation_command_digest"] != _s41_digest(
        REPAIRED_COMMAND_DOMAIN,
        {
            field: command[field]
            for field in SAFE_COMMAND_FIELD_ORDER
            if field != "mutation_command_digest"
        },
    ):
        _s41_violate("physical_family_receipt_binding_mismatch")
    if command["preassigned_disposition_ref"] == command["proposal_ref"]:
        _s41_violate("proposal_disposition_identity_collapse")
    expected = _derive_repaired_command(
        rows_by_role,
        mutation_ref=mutation_ref,
    )
    if not _s41_exact_equal(command, expected):
        _s41_violate("physical_family_receipt_binding_mismatch")
    return command


def _build_repaired_physical_family(
    readiness_present: bool,
    observation: dict[str, object] | None = None,
    expected_binding: dict[str, object] | None = None,
) -> dict[str, object]:
    assert type(readiness_present) is bool
    selected_observation = (
        _build_authority_observation() if observation is None else deepcopy(observation)
    )
    _validate_authority_observation_non_temporal(
        selected_observation,
        _authority_expected_binding() if expected_binding is None else expected_binding,
    )
    variant = "present" if readiness_present else "absent"
    opening = _build_golden_vector(readiness_present)
    preselection = _sample_preselection_records(
        selected_observation,
        readiness_present,
    )
    planning_context = preselection["planning_context"]
    source = preselection["source_invocation"]
    evidence_rows = preselection["evidence_bindings"]
    evidence_set = preselection["evidence_set"]
    proposal = preselection["model_proposal"]

    artifact = _sample_private_plan()
    artifact["artifact_ref"] = opening["private_plan_artifact"]["artifact_ref"]
    artifact["proposal_ref"] = proposal["proposal_ref"]
    artifact["planning_context_ref"] = planning_context["planning_context_ref"]
    artifact["artifact_digest"] = _s41_digest(
        REPAIRED_ARTIFACT_DOMAIN,
        _s41_without(artifact, "artifact_digest"),
    )
    projection = _derive_safe_projection(
        artifact,
        {
            "artifact_schema_id": artifact["schema_id"],
            "artifact_ref": artifact["artifact_ref"],
            "artifact_digest": artifact["artifact_digest"],
        },
        {
            "planning_context_schema_id": planning_context["schema_id"],
            "planning_context_ref": planning_context["planning_context_ref"],
            "planning_context_digest": planning_context["planning_context_digest"],
        },
        {
            "proposal_ref": proposal["proposal_ref"],
            "proposal_phase": artifact["proposal_phase"],
            "recommendation": artifact["recommendation"],
            "reason_code": artifact["reason_code"],
        },
    )
    projection_row = _persisted_projection(projection)

    artifact_binding = preselection["artifact_binding"]
    artifact_binding.update(
        {
            "artifact_ref": artifact["artifact_ref"],
            "artifact_schema_id": artifact["schema_id"],
            "artifact_digest": artifact["artifact_digest"],
            "artifact_canonical_byte_length": len(_s41_canonical_bytes(artifact)),
            "safe_projection_schema_id": projection["schema_id"],
            "safe_projection_digest": projection["safe_projection_digest"],
        }
    )
    artifact_binding["artifact_binding_digest"] = _s41_digest(
        DIGEST_DOMAINS["artifact_binding"],
        _s41_without(artifact_binding, "artifact_binding_digest"),
    )
    source.update(
        {
            "artifact_schema_id": artifact["schema_id"],
            "artifact_ref": artifact["artifact_ref"],
            "artifact_digest": artifact["artifact_digest"],
        }
    )
    source["source_invocation_digest"] = _s41_digest(
        DIGEST_DOMAINS["source_invocation"],
        _s41_without(source, "source_invocation_digest"),
    )
    proposal.update(
        {
            "source_invocation_digest": source["source_invocation_digest"],
            "artifact_schema_id": artifact["schema_id"],
            "artifact_ref": artifact["artifact_ref"],
            "artifact_digest": artifact["artifact_digest"],
            "safe_projection_schema_id": projection["schema_id"],
            "safe_projection_digest": projection["safe_projection_digest"],
            "recommendation": artifact["recommendation"],
            "reason_code": artifact["reason_code"],
            "evidence_set_digest": evidence_set["evidence_set_digest"],
        }
    )
    proposal["proposal_digest"] = _s41_digest(
        DIGEST_DOMAINS["proposal"],
        _s41_without(proposal, "proposal_digest"),
    )

    observation_suffix = selected_observation["authority_observation_digest"][:16]
    disposition = deepcopy(opening["coordinator_disposition"])
    disposition_ref = f"planning-disposition.{variant}.{observation_suffix}"
    disposition.update(
        {
            **{
                field: planning_context[field]
                for field in REPAIRED_C2B3D_LINEAGE_FIELDS
            },
            "disposition_ref": disposition_ref,
            "proposal_ref": proposal["proposal_ref"],
            "proposal_phase": "pre_execution_plan",
            "proposal_digest": proposal["proposal_digest"],
            "planning_context_ref": planning_context["planning_context_ref"],
            "planning_context_digest": planning_context["planning_context_digest"],
            "evidence_set_ref": evidence_set["evidence_set_ref"],
            "evidence_set_digest": evidence_set["evidence_set_digest"],
            "prior_selection_head_revision": -1,
            "prior_selection_head_digest": None,
            "authority_selection_observation_ref": selected_observation["authority_observation_ref"],
            "authority_selection_observation_digest": selected_observation["authority_observation_digest"],
        }
    )
    disposition = {
        field: disposition[field]
        for field, _kind in REPAIRED_DISPOSITION_COLUMNS
    }

    head = deepcopy(opening["current_selection_postimage"])
    head.update(
        {
            **{
                field: planning_context[field]
                for field in REPAIRED_C2B3D_LINEAGE_FIELDS
            },
            "current_proposal_ref": proposal["proposal_ref"],
            "current_disposition_ref": disposition_ref,
        }
    )
    head = {
        field: head[field]
        for field, _kind in REPAIRED_SELECTION_HEAD_COLUMNS
    }
    head["head_digest"] = _s41_digest(
        DIGEST_DOMAINS["selection_head"],
        _s41_without(head, "head_digest"),
    )
    disposition["selection_head_postimage_digest"] = head["head_digest"]
    disposition["disposition_digest"] = _s41_digest(
        DIGEST_DOMAINS["disposition"],
        _s41_without(disposition, "disposition_digest"),
    )

    role_values = (
        ("source_invocation", 0, REPAIRED_TABLE_ORDER[0], source),
        ("planning_context", 1, REPAIRED_TABLE_ORDER[1], planning_context),
        ("private_artifact_binding", 2, REPAIRED_TABLE_ORDER[2], artifact_binding),
        ("model_proposal", 3, REPAIRED_TABLE_ORDER[3], proposal),
        ("pre_execution_plan_projection", 4, REPAIRED_TABLE_ORDER[4], projection_row),
        *tuple(
            (
                f"evidence.{row['evidence_role']}",
                row["role_rank"],
                REPAIRED_TABLE_ORDER[5],
                row,
            )
            for row in evidence_rows
        ),
        ("coordinator_disposition", 20, REPAIRED_TABLE_ORDER[6], disposition),
        ("selection_head_postimage", 21, REPAIRED_TABLE_ORDER[7], head),
    )
    non_receipt_rows = tuple(
        {
            "table": table,
            "role": role,
            "rank": rank,
            "ordinal": values.get("ordinal", 0),
            "values": values,
        }
        for role, rank, table, values in role_values
    )
    mutation_ref = f"cognitive-mutation.{variant}.{observation_suffix}"
    rows_by_role = {row["role"]: row for row in non_receipt_rows}
    command = _derive_repaired_command(
        rows_by_role,
        mutation_ref=mutation_ref,
    )
    command_digest = command["mutation_command_digest"]
    graph = _derive_repaired_graph(
        non_receipt_rows,
        mutation_ref=mutation_ref,
        command_digest=command_digest,
    )
    result_projection: dict[str, object] = {
        "schema_id": "governed-execution.nwp-pre-execution-plan-disposition-result.v1",
        "mutation_ref": mutation_ref,
        "command_digest": command_digest,
        "proposal_ref": proposal["proposal_ref"],
        "disposition_ref": disposition_ref,
        "disposition_digest": disposition["disposition_digest"],
        "disposition": disposition["disposition"],
        "program_ref": disposition["program_ref"],
        "semantic_attempt_ref": disposition["semantic_attempt_ref"],
        "candidate_ref": disposition["candidate_ref"],
        "effect_intent_ref": disposition["effect_intent_ref"],
        "selection_head_revision": head["head_revision"],
        "selection_head_digest": head["head_digest"],
        "authority_selection_observation_ref": selected_observation["authority_observation_ref"],
        "authority_selection_observation_digest": selected_observation["authority_observation_digest"],
        "mutation_graph_digest": graph["mutation_graph_digest"],
        "recorded_at": disposition["coordinator_disposition_decided_at"],
    }
    result_projection["result_projection_digest"] = _s41_digest(
        "governed-execution.nwp-pre-execution-plan-disposition-result.v1.identity",
        result_projection,
    )
    assert tuple(result_projection) == REPAIRED_RESULT_PROJECTION_FIELDS
    receipt_values = deepcopy(opening["receipt"])
    receipt_values.update(
        {
            "mutation_ref": mutation_ref,
            "command_digest": command_digest,
            "proposal_ref": proposal["proposal_ref"],
            "disposition_ref": disposition_ref,
            "disposition_digest": disposition["disposition_digest"],
            "authority_selection_observation_ref": selected_observation["authority_observation_ref"],
            "authority_selection_observation_digest": selected_observation["authority_observation_digest"],
            "selection_head_revision": head["head_revision"],
            "selection_head_digest": head["head_digest"],
            "result_projection_digest": result_projection["result_projection_digest"],
            "mutation_graph_digest": graph["mutation_graph_digest"],
        }
    )
    receipt_values = {
        field: receipt_values[field] for field, _kind in REPAIRED_RECEIPT_COLUMNS
    }
    receipt_values["receipt_digest"] = _s41_digest(
        DIGEST_DOMAINS["receipt"],
        _s41_without(receipt_values, "receipt_digest"),
    )
    receipt_row = {
        "table": REPAIRED_TABLE_ORDER[8],
        "role": "receipt",
        "rank": None,
        "ordinal": 0,
        "values": receipt_values,
    }
    physical_rows = non_receipt_rows + (receipt_row,)
    fresh_result = {
        **result_projection,
        "receipt_digest": receipt_values["receipt_digest"],
    }
    assert tuple(fresh_result) == REPAIRED_FRESH_RESULT_FIELDS
    return {
        "readiness_present": readiness_present,
        "command": command,
        "physical_rows": physical_rows,
        "physical_row_count": len(physical_rows),
        "graph": graph,
        "receipt": receipt_row,
        "result_projection": result_projection,
        "fresh_result": fresh_result,
        "replay_result": deepcopy(fresh_result),
    }


def _redigest_repaired_physical_family(
    family: dict[str, object],
) -> dict[str, object]:
    rows = family["physical_rows"]
    assert type(rows) is tuple
    by_role = {row["role"]: row for row in rows}
    context = by_role["planning_context"]["values"]
    source = by_role["source_invocation"]["values"]
    artifact = by_role["private_artifact_binding"]["values"]
    proposal = by_role["model_proposal"]["values"]
    projection = by_role["pre_execution_plan_projection"]["values"]
    evidence_rows = tuple(
        row["values"]
        for row in rows
        if row["table"] == REPAIRED_TABLE_ORDER[5]
    )
    disposition = by_role["coordinator_disposition"]["values"]
    head = by_role["selection_head_postimage"]["values"]
    receipt_row = by_role["receipt"]
    receipt = receipt_row["values"]

    context["planning_context_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[1], context
    )
    projection["planning_context_digest"] = context["planning_context_digest"]
    projection["safe_projection_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[4], projection
    )
    artifact["safe_projection_digest"] = projection["safe_projection_digest"]
    artifact["artifact_binding_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[2], artifact
    )
    source["context_digest"] = context["planning_context_digest"]
    source["artifact_digest"] = artifact["artifact_digest"]
    source["source_invocation_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[0], source
    )
    for evidence in evidence_rows:
        evidence["evidence_binding_digest"] = _repaired_row_digest(
            REPAIRED_TABLE_ORDER[5], evidence
        )
    evidence_set_identity = {
        "evidence_set_ref": proposal["evidence_set_ref"],
        "proposal_ref": proposal["proposal_ref"],
        "proposal_phase": proposal["proposal_phase"],
        "entries": tuple(
            {
                "evidence_role": evidence["evidence_role"],
                "role_rank": evidence["role_rank"],
                "ordinal": evidence["ordinal"],
                "evidence_ref": evidence["evidence_ref"],
                "evidence_digest": evidence["evidence_digest"],
                "evidence_binding_digest": evidence["evidence_binding_digest"],
            }
            for evidence in evidence_rows
        ),
    }
    evidence_set_digest = _s41_digest(
        DIGEST_DOMAINS["evidence_set"], evidence_set_identity
    )
    proposal.update(
        {
            "source_invocation_digest": source["source_invocation_digest"],
            "context_digest": context["planning_context_digest"],
            "artifact_digest": artifact["artifact_digest"],
            "safe_projection_digest": projection["safe_projection_digest"],
            "evidence_set_digest": evidence_set_digest,
        }
    )
    proposal["proposal_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[3], proposal
    )
    disposition.update(
        {
            "proposal_digest": proposal["proposal_digest"],
            "planning_context_digest": context["planning_context_digest"],
            "evidence_set_ref": proposal["evidence_set_ref"],
            "evidence_set_digest": evidence_set_digest,
        }
    )
    head.update(
        {
            "current_proposal_ref": proposal["proposal_ref"],
            "current_disposition_ref": disposition["disposition_ref"],
            "current_disposition": disposition["disposition"],
        }
    )
    head["head_digest"] = _repaired_row_digest(REPAIRED_TABLE_ORDER[7], head)
    disposition["selection_head_postimage_digest"] = head["head_digest"]
    disposition["disposition_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[6], disposition
    )

    non_receipt_rows = tuple(row for row in rows if row["role"] != "receipt")
    command = _derive_repaired_command(
        {row["role"]: row for row in non_receipt_rows},
        mutation_ref=receipt["mutation_ref"],
    )
    receipt["command_digest"] = command["mutation_command_digest"]
    graph = _derive_repaired_graph(
        non_receipt_rows,
        mutation_ref=receipt["mutation_ref"],
        command_digest=receipt["command_digest"],
    )
    result_projection: dict[str, object] = {
        "schema_id": "governed-execution.nwp-pre-execution-plan-disposition-result.v1",
        "mutation_ref": receipt["mutation_ref"],
        "command_digest": receipt["command_digest"],
        "proposal_ref": proposal["proposal_ref"],
        "disposition_ref": disposition["disposition_ref"],
        "disposition_digest": disposition["disposition_digest"],
        "disposition": disposition["disposition"],
        "program_ref": disposition["program_ref"],
        "semantic_attempt_ref": disposition["semantic_attempt_ref"],
        "candidate_ref": disposition["candidate_ref"],
        "effect_intent_ref": disposition["effect_intent_ref"],
        "selection_head_revision": head["head_revision"],
        "selection_head_digest": head["head_digest"],
        "authority_selection_observation_ref": disposition[
            "authority_selection_observation_ref"
        ],
        "authority_selection_observation_digest": disposition[
            "authority_selection_observation_digest"
        ],
        "mutation_graph_digest": graph["mutation_graph_digest"],
        "recorded_at": disposition["coordinator_disposition_decided_at"],
    }
    result_projection["result_projection_digest"] = _s41_digest(
        "governed-execution.nwp-pre-execution-plan-disposition-result.v1.identity",
        result_projection,
    )
    receipt.update(
        {
            "proposal_ref": proposal["proposal_ref"],
            "disposition_ref": disposition["disposition_ref"],
            "disposition_digest": disposition["disposition_digest"],
            "authority_selection_observation_ref": disposition[
                "authority_selection_observation_ref"
            ],
            "authority_selection_observation_digest": disposition[
                "authority_selection_observation_digest"
            ],
            "selection_head_revision": head["head_revision"],
            "selection_head_digest": head["head_digest"],
            "result_projection_digest": result_projection[
                "result_projection_digest"
            ],
            "mutation_graph_digest": graph["mutation_graph_digest"],
            "committed_at": disposition["coordinator_disposition_decided_at"],
        }
    )
    receipt["receipt_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[8], receipt
    )
    fresh_result = {
        **result_projection,
        "receipt_digest": receipt["receipt_digest"],
    }
    family.update(
        {
            "physical_row_count": len(rows),
            "command": command,
            "graph": graph,
            "receipt": receipt_row,
            "result_projection": result_projection,
            "fresh_result": fresh_result,
            "replay_result": deepcopy(fresh_result),
        }
    )
    return family


def _build_repaired_successor_family(
    predecessor: dict[str, object],
    *,
    suffix: str,
    readiness_present: bool = False,
) -> dict[str, object]:
    _validate_repaired_physical_family(predecessor)
    _s41_require_safe_ref(suffix, "physical_family_row_digest_mismatch")
    family = deepcopy(_build_repaired_physical_family(readiness_present))
    predecessor_by_role = {
        row["role"]: row for row in predecessor["physical_rows"]
    }
    by_role = {row["role"]: row for row in family["physical_rows"]}
    old_identifiers = {
        by_role["source_invocation"]["values"]["source_invocation_ref"]:
            f"source.{suffix}",
        by_role["planning_context"]["values"]["planning_context_ref"]:
            f"context.{suffix}",
        by_role["private_artifact_binding"]["values"]["artifact_ref"]:
            f"artifact.{suffix}",
        by_role["model_proposal"]["values"]["proposal_ref"]:
            f"proposal.{suffix}",
        by_role["model_proposal"]["values"]["evidence_set_ref"]:
            f"evidence-set.{suffix}",
        by_role["coordinator_disposition"]["values"]["disposition_ref"]:
            f"disposition.{suffix}",
        by_role["receipt"]["values"]["mutation_ref"]:
            f"cognitive-mutation.{suffix}",
    }
    for row in family["physical_rows"]:
        for field, value in row["values"].items():
            if type(value) is str and value in old_identifiers:
                row["values"][field] = old_identifiers[value]

    predecessor_disposition = predecessor_by_role["coordinator_disposition"][
        "values"
    ]
    predecessor_head = predecessor_by_role["selection_head_postimage"]["values"]
    disposition = by_role["coordinator_disposition"]["values"]
    head = by_role["selection_head_postimage"]["values"]
    next_revision = predecessor_head["head_revision"] + 1
    decided_at = "2026-08-22T12:35:05Z"
    disposition.update(
        {
            "supersedes_disposition_ref": predecessor_disposition[
                "disposition_ref"
            ],
            "expected_selection_head_revision": predecessor_head["head_revision"],
            "expected_selection_head_digest": predecessor_head["head_digest"],
            "prior_selection_head_revision": predecessor_head["head_revision"],
            "prior_selection_head_digest": predecessor_head["head_digest"],
            "resulting_selection_head_revision": next_revision,
            "coordinator_disposition_decided_at": decided_at,
        }
    )
    head.update(
        {
            "head_revision": next_revision,
            "updated_at": decided_at,
        }
    )
    _redigest_repaired_physical_family(family)
    _validate_repaired_physical_family(family)
    return family


def _expected_repaired_role_specs(
    readiness_present: bool,
) -> tuple[tuple[str, int | None, int, str], ...]:
    graph_specs = tuple(
        spec
        for spec in REPAIRED_GRAPH_ROLE_INVENTORY
        if readiness_present or spec[1] != 19
    )
    return tuple(
        (role, rank, 0, table)
        for role, rank, table in graph_specs
    ) + (("receipt", None, 0, REPAIRED_TABLE_ORDER[8]),)


REPAIRED_KIND_VOCABULARIES = {
    "proposal_phase": PHASES,
    "phase_context_schema": (
        SCHEMA_IDS["pre_execution_context"],
        SCHEMA_IDS["post_execution_context"],
    ),
    "phase_artifact_schema": (
        SCHEMA_IDS["pre_execution_artifact"],
        SCHEMA_IDS["post_execution_artifact"],
    ),
    "phase_projection_schema": (
        SCHEMA_IDS["pre_execution_projection"],
        SCHEMA_IDS["post_execution_projection"],
    ),
    "phase_recommendation": (
        "select_for_dispatch_gates",
        "defer",
        "block",
        "replan",
        "terminal_reject",
        "accept_candidate",
        "repair_candidate",
    ),
    "pre_execution_recommendation": PRE_EXECUTION_RECOMMENDATIONS,
    "pre_execution_disposition": DISPOSITIONS,
    "authority_state": AUTHORITY_STATES,
    "authority_observation_state": ("pending", "verified"),
    "phase_evidence_role": (
        "standing_policy",
        "risk_lane",
        "repository_binding",
        "base_binding",
        "authorized_path_scope",
        "cost_ceiling",
        "token_ceiling",
        "time_ceiling",
        "delivery_ceiling",
        "effect_ceiling",
        "authority_currentness_attestation",
        "authority_selection_observation",
        "global_stop",
        "validation_requirement",
        "review_requirement",
        "qualified_remote_host_readiness",
        "candidate_capsule",
        "worker_result",
        "validation_result",
        "independent_review",
    ),
}


def _repaired_kind_vocabulary(kind: str) -> tuple[str, ...] | None:
    if kind.startswith("enum:"):
        values = tuple(kind.split(":", 1)[1].split("|"))
        return values if values and all(values) else None
    return REPAIRED_KIND_VOCABULARIES.get(kind)


def _repaired_value_matches_kind(value: object, kind: str) -> bool:
    if kind.startswith("literal_int:"):
        return (
            _s41_integer_fits_sqlite(value)
            and value == int(kind.split(":", 1)[1])
        )
    if kind.startswith("literal:"):
        return (
            _s41_string_is_canonical(value)
            and value == kind.split(":", 1)[1]
        )
    if kind == "safe_ref":
        return _s41_string_is_canonical(value) and re.fullmatch(
            r"[0-9A-Za-z][0-9A-Za-z.-]{0,95}", value
        ) is not None and not value.casefold().startswith(
            ("connector-", "tunnel-", "workspace-", "org-", "organization-", "user-")
        )
    if kind == "nullable_safe_ref":
        return value is None or _repaired_value_matches_kind(value, "safe_ref")
    if kind == "sha256":
        return _s41_string_is_canonical(value) and re.fullmatch(r"[0-9a-f]{64}", value) is not None
    if kind == "nullable_sha256":
        return value is None or _repaired_value_matches_kind(value, "sha256")
    if kind == "sha1":
        return _s41_string_is_canonical(value) and re.fullmatch(r"[0-9a-f]{40}", value) is not None
    if kind == "utc_second":
        try:
            _s41_require_utc_second(value, "physical_family_row_digest_mismatch")
        except _ContractViolation:
            return False
        return True
    if kind in ("positive_int", "nonnegative_int"):
        return _s41_integer_fits_sqlite(value) and value >= (
            1 if kind == "positive_int" else 0
        )
    if kind == "nullable_nonnegative_int":
        return value is None or _repaired_value_matches_kind(value, "nonnegative_int")
    if kind == "selection_prior_revision":
        return _s41_integer_fits_sqlite(value) and value >= -1
    if kind.startswith("int:"):
        match = re.fullmatch(r"int:([0-9]+)\.\.([0-9]+)", kind)
        return (
            match is not None
            and _s41_integer_fits_sqlite(value)
            and int(match.group(1)) <= value <= int(match.group(2))
        )
    if kind == "bool_int":
        return _s41_integer_fits_sqlite(value) and value in (0, 1)
    if kind == "canonical_effect_class_json":
        if not _s41_string_is_canonical(value):
            return False
        try:
            decoded = json.loads(value)
        except (TypeError, ValueError, RecursionError):
            return False
        return (
            type(decoded) is list
            and decoded
            and all(type(item) is str and item in REPAIRED_EFFECT_CLASSES for item in decoded)
            and len(decoded) == len(set(decoded))
            and tuple(item for item in REPAIRED_EFFECT_CLASSES if item in decoded) == tuple(decoded)
            and _s41_canonical_bytes(tuple(decoded)).decode("utf-8") == value
        )
    if kind == "reason_code":
        return _s41_string_is_canonical(value) and re.fullmatch(r"[a-z][a-z0-9_.-]{0,95}", value) is not None
    if kind == "phase_evidence_rank":
        return _s41_integer_fits_sqlite(value) and 5 <= value <= 19
    vocabulary = _repaired_kind_vocabulary(kind)
    if vocabulary is not None:
        return _s41_string_is_canonical(value) and value in vocabulary
    return False


def _repaired_value_has_safe_scalar_shape(value: object, kind: str) -> bool:
    if kind.startswith("nullable_") and value is None:
        return True
    if (
        kind.startswith("literal_int:")
        or kind.startswith("int:")
        or kind
        in (
            "positive_int",
            "nonnegative_int",
            "selection_prior_revision",
            "nullable_nonnegative_int",
            "bool_int",
            "phase_evidence_rank",
        )
    ):
        return _s41_integer_fits_sqlite(value)
    return _s41_string_is_canonical(value)


def _repaired_disposition_shape_is_exact(values: dict[str, object]) -> bool:
    if values["disposition_ref"] == values["proposal_ref"]:
        return False
    resulting_revision = values["resulting_selection_head_revision"]
    if resulting_revision == 0:
        return (
            values["supersedes_disposition_ref"] is None
            and values["expected_selection_head_revision"] is None
            and values["expected_selection_head_digest"] is None
            and values["prior_selection_head_revision"] == -1
            and values["prior_selection_head_digest"] is None
        )
    return (
        resulting_revision > 0
        and values["prior_selection_head_revision"] == resulting_revision - 1
        and type(values["supersedes_disposition_ref"]) is str
        and type(values["prior_selection_head_digest"]) is str
        and values["expected_selection_head_revision"]
        == values["prior_selection_head_revision"]
        and values["expected_selection_head_digest"]
        == values["prior_selection_head_digest"]
    )


def _repaired_row_digest(table: str, values: dict[str, object]) -> str:
    digest_field, domain = REPAIRED_TABLE_DIGESTS[table]
    identity = _s41_without(values, digest_field)
    if table == REPAIRED_TABLE_ORDER[4]:
        decoded = json.loads(identity["allowed_effect_classes"])
        identity["allowed_effect_classes"] = tuple(decoded)
    return _s41_digest(domain, identity)


def _validate_repaired_common_phase_algebra(
    source: dict[str, object],
    artifact: dict[str, object],
    proposal: dict[str, object],
) -> dict[str, object]:
    for values, table in (
        (source, REPAIRED_TABLE_ORDER[0]),
        (artifact, REPAIRED_TABLE_ORDER[2]),
        (proposal, REPAIRED_TABLE_ORDER[3]),
    ):
        columns = REPAIRED_TABLE_COLUMNS[table]
        values = _s41_require_exact_mapping(
            values,
            tuple(name for name, _kind in columns),
            "phase_algebra_mismatch",
        )
        if any(
            not _repaired_value_has_safe_scalar_shape(values[field], kind)
            for field, kind in columns
        ):
            _s41_violate("phase_algebra_mismatch")
    phase = source["proposal_phase"]
    if type(phase) is not str or not any(
        _s41_exact_equal(phase, candidate)
        for candidate in REPAIRED_PHASE_ALGEBRA
    ):
        _s41_violate("phase_algebra_mismatch")
    contract = REPAIRED_PHASE_ALGEBRA[phase]
    if not all(
        _s41_exact_equal(left, right)
        for left, right in (
            (source["schema_id"], SCHEMA_IDS["source_invocation"]),
            (source["proposal_phase"], contract["source_invocation_proposal_phase"]),
            (source["context_schema_id"], contract["context_schema_id"]),
            (source["artifact_schema_id"], contract["private_artifact_schema_id"]),
            (artifact["schema_id"], SCHEMA_IDS["artifact_binding"]),
            (artifact["proposal_phase"], phase),
            (artifact["artifact_schema_id"], contract["private_artifact_schema_id"]),
            (artifact["safe_projection_schema_id"], contract["safe_projection_schema_id"]),
            (proposal["schema_id"], contract["proposal_schema_id"]),
            (proposal["proposal_phase"], phase),
            (proposal["context_schema_id"], contract["context_schema_id"]),
            (proposal["artifact_schema_id"], contract["private_artifact_schema_id"]),
            (proposal["safe_projection_schema_id"], contract["safe_projection_schema_id"]),
        )
    ) or not any(
        _s41_exact_equal(proposal["recommendation"], recommendation)
        for recommendation in contract["recommendations"]
    ):
        _s41_violate("phase_algebra_mismatch")
    return contract


def _validate_repaired_phase_algebra(
    rows_by_role: dict[str, dict[str, object]],
    *,
    readiness_present: bool,
) -> None:
    source = rows_by_role["source_invocation"]["values"]
    artifact = rows_by_role["private_artifact_binding"]["values"]
    proposal = rows_by_role["model_proposal"]["values"]
    phase = source["proposal_phase"]
    contract = _validate_repaired_common_phase_algebra(
        source,
        artifact,
        proposal,
    )
    table_presence = {
        table: any(row["table"] == table for row in rows_by_role.values())
        for table in REPAIRED_TABLE_ORDER
    }
    for table, policy in contract["row_presence"]:
        if (policy == "required" and not table_presence[table]) or (
            policy == "forbidden" and table_presence[table]
        ):
            _s41_violate("phase_algebra_mismatch")
    evidence_rows = tuple(
        row["values"]
        for row in rows_by_role.values()
        if row["table"] == REPAIRED_TABLE_ORDER[5]
    )
    allowed_evidence = contract["evidence_roles"]
    if any(
        not _s41_exact_equal(row["proposal_phase"], phase)
        or type(row["evidence_role"]) is not str
        or type(row["role_rank"]) is not int
        or type(row["required_for_selection"]) is not int
        or not any(
            _s41_exact_equal(
                (
                    row["evidence_role"],
                    row["role_rank"],
                    row["required_for_selection"],
                ),
                (role, rank, int(required)),
            )
            for role, rank, required in allowed_evidence
        )
        for row in evidence_rows
    ):
        _s41_violate("phase_algebra_mismatch")
    if phase == "pre_execution_plan":
        expected_evidence = (
            REPAIRED_PRE_EXECUTION_EVIDENCE_SPECS
            if readiness_present
            else REPAIRED_PRE_EXECUTION_EVIDENCE_SPECS[:-1]
        )
        if tuple(
            (
                row["evidence_role"],
                row["role_rank"],
                row["required_for_selection"],
            )
            for row in evidence_rows
        ) != tuple(
            (role, rank, int(required))
            for role, rank, required in expected_evidence
        ):
            _s41_violate("phase_algebra_mismatch")
        projection = rows_by_role["pre_execution_plan_projection"]["values"]
        context = rows_by_role["planning_context"]["values"]
        if not all(
            _s41_exact_equal(left, right)
            for left, right in (
                (projection["schema_id"], contract["safe_projection_schema_id"]),
                (projection["proposal_phase"], phase),
                (projection["artifact_schema_id"], contract["private_artifact_schema_id"]),
                (projection["planning_context_schema_id"], contract["context_schema_id"]),
                (projection["recommendation"], proposal["recommendation"]),
                (context["schema_id"], contract["context_schema_id"]),
            )
        ):
            _s41_violate("phase_algebra_mismatch")
    else:
        observed_evidence = tuple(
            (
                row["evidence_role"],
                row["role_rank"],
                row["required_for_selection"],
            )
            for row in evidence_rows
        )
        complete_evidence = tuple(
            (role, rank, int(required))
            for role, rank, required in REPAIRED_POST_EXECUTION_EVIDENCE_SPECS
        )
        if evidence_rows and not _s41_exact_equal(
            observed_evidence,
            complete_evidence,
        ):
            _s41_violate("phase_algebra_mismatch")


def _reconstruct_repaired_authority_observation(
    context: dict[str, object],
) -> dict[str, object]:
    observation = {
        "schema_id": context["authority_selection_observation_schema_id"],
        "authority_observation_ref": context[
            "authority_selection_observation_ref"
        ],
        "authoritative_subject_kind": context["authoritative_subject_kind"],
        "authoritative_subject_ref": context["authoritative_subject_ref"],
        **{field: context[field] for field in REPAIRED_AUTHORITY_LINEAGE_FIELDS},
        "authority_evaluation_ref": context["authority_evaluation_ref"],
        "authority_evaluation_digest": context["authority_evaluation_digest"],
        "observation_state": context["authority_observation_state"],
        "observation_version": context["authority_observation_version"],
        "authority_observation_issued_at": context[
            "authority_observation_issued_at"
        ],
        "authority_observation_expires_at": context[
            "authority_observation_expires_at"
        ],
        "source_authority_ref": context["source_authority_ref"],
        "verification_evidence_ref": context["verification_evidence_ref"],
        "verification_evidence_digest": context[
            "verification_evidence_digest"
        ],
        "authority_observation_digest": context[
            "authority_selection_observation_digest"
        ],
    }
    expected_binding = {
        "authoritative_subject_kind": "effect_intent",
        "authoritative_subject_ref": context["effect_intent_ref"],
        **{field: context[field] for field in REPAIRED_AUTHORITY_LINEAGE_FIELDS},
        "authority_evaluation_ref": context["authority_evaluation_ref"],
        "authority_evaluation_digest": context["authority_evaluation_digest"],
        "source_authority_ref": context["source_authority_ref"],
        "verification_evidence_ref": context["verification_evidence_ref"],
        "verification_evidence_digest": context[
            "verification_evidence_digest"
        ],
    }
    _validate_authority_observation_non_temporal(observation, expected_binding)
    return observation


def _validate_repaired_c2b3d_lineage(
    family: dict[str, object],
    rows_by_role: dict[str, dict[str, object]],
) -> None:
    context = rows_by_role["planning_context"]["values"]
    disposition = rows_by_role["coordinator_disposition"]["values"]
    head = rows_by_role["selection_head_postimage"]["values"]
    canonical_lineage = tuple(
        context[field] for field in REPAIRED_C2B3D_LINEAGE_FIELDS
    )
    expected_lineage = tuple(
        C2B3D_BASIS[field] for field in REPAIRED_C2B3D_LINEAGE_FIELDS
    )
    disposition_lineage = tuple(
        disposition[field] for field in REPAIRED_C2B3D_LINEAGE_FIELDS
    )
    head_lineage = tuple(
        head[field] for field in REPAIRED_C2B3D_LINEAGE_FIELDS
    )
    if not (
        _s41_exact_equal(canonical_lineage, expected_lineage)
        and _s41_exact_equal(disposition_lineage, canonical_lineage)
        and _s41_exact_equal(head_lineage, canonical_lineage)
    ):
        _s41_violate("physical_family_row_digest_mismatch")
    receipt = rows_by_role["receipt"]["values"]
    result = family["result_projection"]
    for field in ("program_ref", "effect_intent_ref"):
        if not _s41_exact_equal(context[field], receipt[field]):
            _s41_violate("physical_family_receipt_binding_mismatch")
    for field in (
        "program_ref",
        "semantic_attempt_ref",
        "candidate_ref",
        "effect_intent_ref",
    ):
        if not _s41_exact_equal(context[field], result[field]):
            _s41_violate("physical_family_graph_digest_mismatch")


def _validate_repaired_persisted_observation_and_chronology(
    family: dict[str, object],
    rows_by_role: dict[str, dict[str, object]],
) -> None:
    context = rows_by_role["planning_context"]["values"]
    observation = _reconstruct_repaired_authority_observation(context)
    source = rows_by_role["source_invocation"]["values"]
    artifact = rows_by_role["private_artifact_binding"]["values"]
    proposal = rows_by_role["model_proposal"]["values"]
    disposition = rows_by_role["coordinator_disposition"]["values"]
    head = rows_by_role["selection_head_postimage"]["values"]
    receipt = rows_by_role["receipt"]["values"]
    evidence_times = tuple(
        row["values"]["evidence_bound_at"]
        for row in rows_by_role.values()
        if row["table"] == REPAIRED_TABLE_ORDER[5]
    )
    if not evidence_times or any(value != evidence_times[0] for value in evidence_times):
        _s41_violate("preselection_chronology_invalid")
    decision_time = disposition["coordinator_disposition_decided_at"]
    chronology = (
        observation["authority_observation_issued_at"],
        context["planning_context_captured_at"],
        source["source_invocation_started_at"],
        source["source_invocation_completed_at"],
        artifact["artifact_validated_at"],
        evidence_times[0],
        proposal["proposal_created_at"],
    )
    for value in (*chronology, decision_time):
        _s41_require_utc_second(value, "preselection_chronology_invalid")
    if tuple(sorted(chronology)) != chronology or not chronology[-1] < decision_time:
        _s41_violate("preselection_chronology_invalid")
    if not (
        decision_time < observation["authority_observation_expires_at"]
        and decision_time < context["attempt_fence_expires_at"]
        and decision_time < context["effect_fence_expires_at"]
    ):
        _s41_violate("preselection_chronology_invalid")
    shared_times = (
        head["updated_at"],
        receipt["committed_at"],
        family["result_projection"]["recorded_at"],
        family["fresh_result"]["recorded_at"],
        family["replay_result"]["recorded_at"],
    )
    if any(not _s41_exact_equal(value, decision_time) for value in shared_times):
        _s41_violate("preselection_chronology_invalid")


def _validate_repaired_physical_family(family: object) -> None:
    family = _s41_require_exact_mapping(
        family,
        (
            "readiness_present",
            "command",
            "physical_rows",
            "physical_row_count",
            "graph",
            "receipt",
            "result_projection",
            "fresh_result",
            "replay_result",
        ),
        "physical_family_extra_row",
    )
    readiness_present = family["readiness_present"]
    if type(readiness_present) is not bool or type(family["physical_rows"]) is not tuple:
        _s41_violate("physical_family_extra_row")
    rows = family["physical_rows"]
    graph = family["graph"]
    graph = _s41_require_exact_mapping(
        graph,
        REPAIRED_GRAPH_FIELDS,
        "physical_family_graph_digest_mismatch",
    )
    entries = graph["entries"]
    if type(entries) is not tuple:
        _s41_violate("physical_family_graph_digest_mismatch")

    # Receipt exclusion is deliberately first so the named mutant is causal.
    graph_entry_fields = (
        "role",
        "rank",
        "ordinal",
        "table",
        "locator",
        "member_digest",
    )
    if any(
        type(entry) is dict
        and all(type(key) is str for key in entry)
        and tuple(entry) == graph_entry_fields
        and type(entry["role"]) is str
        and entry["role"] == "receipt"
        for entry in entries
    ):
        _s41_violate("physical_family_receipt_in_graph")

    expected_specs = _expected_repaired_role_specs(readiness_present)
    expected_count = 23 if readiness_present else 22
    if len(rows) < expected_count:
        _s41_violate("physical_family_missing_row")
    if len(rows) > expected_count:
        _s41_violate("physical_family_extra_row")
    actual_specs: list[tuple[str, int | None, int, str]] = []
    for row in rows:
        row = _s41_require_exact_mapping(
            row,
            REPAIRED_ROW_FIELDS,
            "physical_family_extra_row",
        )
        if (
            type(row["table"]) is not str
            or row["table"] not in REPAIRED_TABLE_COLUMNS
            or type(row["role"]) is not str
            or (row["rank"] is not None and type(row["rank"]) is not int)
        ):
            _s41_violate("physical_family_row_digest_mismatch")
        if type(row["ordinal"]) is not int:
            _s41_violate("physical_family_order_mismatch")
        _s41_require_exact_mapping(
            row["values"],
            tuple(name for name, _kind in REPAIRED_TABLE_COLUMNS[row["table"]]),
            "physical_family_row_digest_mismatch",
        )
        actual_specs.append(
            (row["role"], row["rank"], row["ordinal"], row["table"])
        )
    if not _s41_exact_equal(tuple(actual_specs), expected_specs):
        _s41_violate("physical_family_order_mismatch")

    for row in rows:
        columns = REPAIRED_TABLE_COLUMNS[row["table"]]
        values = row["values"]
        if any(
            not _repaired_value_has_safe_scalar_shape(values[field], kind)
            for field, kind in columns
        ):
            _s41_violate("physical_family_row_digest_mismatch")

    rows_by_role = {row["role"]: row for row in rows}
    _validate_repaired_phase_algebra(
        rows_by_role,
        readiness_present=readiness_present,
    )

    for row in rows:
        columns = REPAIRED_TABLE_COLUMNS[row["table"]]
        values = row["values"]
        for field, kind in columns:
            if not _repaired_value_matches_kind(values[field], kind):
                _s41_violate("physical_family_row_digest_mismatch")
        digest_field, _domain = REPAIRED_TABLE_DIGESTS[row["table"]]
        if values[digest_field] != _repaired_row_digest(row["table"], values):
            _s41_violate("physical_family_row_digest_mismatch")

    context_values = rows_by_role["planning_context"]["values"]
    observation_row = rows_by_role[
        "evidence.authority_selection_observation"
    ]["values"]
    disposition_values = rows_by_role["coordinator_disposition"]["values"]
    head_values = rows_by_role["selection_head_postimage"]["values"]
    observation_ref = context_values["authority_selection_observation_ref"]
    observation_digest = context_values["authority_selection_observation_digest"]
    readiness_rows = tuple(
        row for row in rows if row["role"] == "evidence.qualified_remote_host_readiness"
    )
    readiness_ref = context_values["qualified_remote_host_readiness_ref"]
    readiness_digest = context_values["qualified_remote_host_readiness_digest"]
    if readiness_present:
        if not (
            len(readiness_rows) == 1
            and type(readiness_ref) is str
            and type(readiness_digest) is str
            and readiness_rows[0]["values"]["evidence_ref"] == readiness_ref
            and readiness_rows[0]["values"]["evidence_digest"] == readiness_digest
        ):
            _s41_violate("physical_family_readiness_mismatch")
    elif not (
        not readiness_rows and readiness_ref is None and readiness_digest is None
    ):
        _s41_violate("physical_family_readiness_mismatch")
    if not (
        observation_row["role_rank"] == 15
        and observation_row["evidence_role"] == "authority_selection_observation"
        and observation_row["evidence_ref"] == observation_ref
        and observation_row["evidence_digest"] == observation_digest
        and disposition_values["authority_selection_observation_ref"] == observation_ref
        and disposition_values["authority_selection_observation_digest"] == observation_digest
    ):
        _s41_violate("authority_observation_binding_mismatch")
    if disposition_values["disposition_ref"] == disposition_values["proposal_ref"]:
        _s41_violate("proposal_disposition_identity_collapse")
    if not (
        head_values["current_disposition_ref"] == disposition_values["disposition_ref"]
        and head_values["current_proposal_ref"] == disposition_values["proposal_ref"]
        and head_values["current_disposition"] == disposition_values["disposition"]
        and head_values["head_revision"] == disposition_values["resulting_selection_head_revision"]
        and head_values["head_digest"] == disposition_values["selection_head_postimage_digest"]
        and disposition_values["disposition_digest"] != disposition_values["selection_head_postimage_digest"]
    ):
        _s41_violate("physical_family_row_digest_mismatch")
    if not _repaired_disposition_shape_is_exact(disposition_values):
        _s41_violate("physical_family_row_digest_mismatch")

    source_values = rows_by_role["source_invocation"]["values"]
    artifact_values = rows_by_role["private_artifact_binding"]["values"]
    proposal_values = rows_by_role["model_proposal"]["values"]
    projection_values = rows_by_role["pre_execution_plan_projection"]["values"]
    evidence_members = tuple(
        row for row in rows if row["table"] == REPAIRED_TABLE_ORDER[5]
    )
    if any(
        not _s41_exact_equal(left, right)
        for left, right in (
            (source_values["context_ref"], context_values["planning_context_ref"]),
            (source_values["context_digest"], context_values["planning_context_digest"]),
            (source_values["artifact_ref"], artifact_values["artifact_ref"]),
            (source_values["artifact_digest"], artifact_values["artifact_digest"]),
            (proposal_values["source_invocation_ref"], source_values["source_invocation_ref"]),
            (proposal_values["source_invocation_digest"], source_values["source_invocation_digest"]),
            (proposal_values["context_ref"], context_values["planning_context_ref"]),
            (proposal_values["context_digest"], context_values["planning_context_digest"]),
            (proposal_values["artifact_ref"], artifact_values["artifact_ref"]),
            (proposal_values["artifact_digest"], artifact_values["artifact_digest"]),
            (proposal_values["safe_projection_digest"], projection_values["safe_projection_digest"]),
            (artifact_values["safe_projection_digest"], projection_values["safe_projection_digest"]),
            (projection_values["proposal_ref"], proposal_values["proposal_ref"]),
            (projection_values["artifact_ref"], artifact_values["artifact_ref"]),
            (projection_values["planning_context_ref"], context_values["planning_context_ref"]),
            (projection_values["planning_context_digest"], context_values["planning_context_digest"]),
            (projection_values["recommendation"], proposal_values["recommendation"]),
            (projection_values["reason_code"], proposal_values["reason_code"]),
            (disposition_values["proposal_ref"], proposal_values["proposal_ref"]),
            (disposition_values["proposal_phase"], proposal_values["proposal_phase"]),
            (disposition_values["proposal_digest"], proposal_values["proposal_digest"]),
            (disposition_values["planning_context_ref"], context_values["planning_context_ref"]),
            (disposition_values["planning_context_digest"], context_values["planning_context_digest"]),
            (head_values["current_proposal_ref"], proposal_values["proposal_ref"]),
        )
    ):
        _s41_violate("physical_family_row_digest_mismatch")
    if tuple(
        (
            member["values"]["evidence_role"],
            member["values"]["role_rank"],
            member["values"]["ordinal"],
        )
        for member in evidence_members
    ) != tuple(
        (role.removeprefix("evidence."), rank, 0)
        for role, rank, _ordinal, table in expected_specs
        if table == REPAIRED_TABLE_ORDER[5]
    ):
        _s41_violate("physical_family_order_mismatch")
    if any(
        member["values"]["proposal_ref"] != proposal_values["proposal_ref"]
        or member["values"]["proposal_phase"] != "pre_execution_plan"
        or member["values"]["evidence_set_ref"] != proposal_values["evidence_set_ref"]
        for member in evidence_members
    ):
        _s41_violate("physical_family_row_digest_mismatch")
    evidence_set_identity = {
        "evidence_set_ref": proposal_values["evidence_set_ref"],
        "proposal_ref": proposal_values["proposal_ref"],
        "proposal_phase": proposal_values["proposal_phase"],
        "entries": tuple(
            {
                "evidence_role": member["values"]["evidence_role"],
                "role_rank": member["values"]["role_rank"],
                "ordinal": member["values"]["ordinal"],
                "evidence_ref": member["values"]["evidence_ref"],
                "evidence_digest": member["values"]["evidence_digest"],
                "evidence_binding_digest": member["values"]["evidence_binding_digest"],
            }
            for member in evidence_members
        ),
    }
    evidence_set_digest = _s41_digest(
        DIGEST_DOMAINS["evidence_set"], evidence_set_identity
    )
    if not (
        proposal_values["evidence_set_digest"] == evidence_set_digest
        and disposition_values["evidence_set_ref"] == proposal_values["evidence_set_ref"]
        and disposition_values["evidence_set_digest"] == evidence_set_digest
    ):
        _s41_violate("physical_family_row_digest_mismatch")
    for field in REPAIRED_SELECTION_HEAD_REPEATED_LINEAGE_FIELDS:
        if not _s41_exact_equal(head_values[field], disposition_values[field]):
            _s41_violate("physical_family_row_digest_mismatch")

    for entry in entries:
        entry = _s41_require_exact_mapping(
            entry,
            graph_entry_fields,
            "physical_family_graph_digest_mismatch",
        )
        if not (
            type(entry["role"]) is str
            and type(entry["rank"]) is int
            and type(entry["ordinal"]) is int
            and type(entry["table"]) is str
            and type(entry["locator"]) is tuple
            and all(
                type(pair) is tuple
                and len(pair) == 2
                and type(pair[0]) is str
                for pair in entry["locator"]
            )
            and _repaired_value_matches_kind(entry["member_digest"], "sha256")
        ):
            _s41_violate("physical_family_graph_digest_mismatch")
        if entry["role"] not in rows_by_role:
            _s41_violate("physical_family_graph_without_row")
    entry_roles = tuple(entry["role"] for entry in entries)
    required_graph_roles = tuple(row["role"] for row in rows if row["rank"] is not None)
    if any(role not in entry_roles for role in required_graph_roles):
        _s41_violate("physical_family_row_without_graph")

    receipt_values = rows_by_role["receipt"]["values"]
    command = _validate_repaired_command(
        family["command"],
        rows_by_role,
        mutation_ref=receipt_values["mutation_ref"],
    )
    expected_command_digest = command["mutation_command_digest"]
    expected_graph = _derive_repaired_graph(
        tuple(row for row in rows if row["rank"] is not None),
        mutation_ref=receipt_values["mutation_ref"],
        command_digest=expected_command_digest,
    )
    if not _s41_exact_equal(graph, expected_graph):
        _s41_violate("physical_family_graph_digest_mismatch")
    expected_receipt = rows_by_role["receipt"]
    if not _s41_exact_equal(family["receipt"], expected_receipt):
        _s41_violate("physical_family_missing_row")
    disposition_row = rows_by_role["coordinator_disposition"]
    head_row = rows_by_role["selection_head_postimage"]
    disposition_values = disposition_row["values"]
    head_values = head_row["values"]
    expected_projection: dict[str, object] = {
        "schema_id": "governed-execution.nwp-pre-execution-plan-disposition-result.v1",
        "mutation_ref": receipt_values["mutation_ref"],
        "command_digest": expected_command_digest,
        "proposal_ref": disposition_values["proposal_ref"],
        "disposition_ref": disposition_values["disposition_ref"],
        "disposition_digest": disposition_values["disposition_digest"],
        "disposition": disposition_values["disposition"],
        "program_ref": disposition_values["program_ref"],
        "semantic_attempt_ref": disposition_values["semantic_attempt_ref"],
        "candidate_ref": disposition_values["candidate_ref"],
        "effect_intent_ref": disposition_values["effect_intent_ref"],
        "selection_head_revision": head_values["head_revision"],
        "selection_head_digest": head_values["head_digest"],
        "authority_selection_observation_ref": disposition_values["authority_selection_observation_ref"],
        "authority_selection_observation_digest": disposition_values["authority_selection_observation_digest"],
        "mutation_graph_digest": graph["mutation_graph_digest"],
        "recorded_at": disposition_values["coordinator_disposition_decided_at"],
    }
    expected_projection["result_projection_digest"] = _s41_digest(
        "governed-execution.nwp-pre-execution-plan-disposition-result.v1.identity",
        expected_projection,
    )
    if not _s41_exact_equal(family["result_projection"], expected_projection):
        _s41_violate("physical_family_graph_digest_mismatch")
    receipt_expectations = {
        "command_digest": expected_command_digest,
        "program_ref": disposition_values["program_ref"],
        "proposal_ref": disposition_values["proposal_ref"],
        "effect_intent_ref": disposition_values["effect_intent_ref"],
        "mutation_graph_digest": graph["mutation_graph_digest"],
        "result_projection_digest": expected_projection["result_projection_digest"],
        "disposition_ref": disposition_values["disposition_ref"],
        "disposition_digest": disposition_values["disposition_digest"],
        "selection_head_digest": head_values["head_digest"],
        "selection_head_revision": head_values["head_revision"],
        "authority_selection_observation_ref": disposition_values["authority_selection_observation_ref"],
        "authority_selection_observation_digest": disposition_values["authority_selection_observation_digest"],
        "committed_at": disposition_values["coordinator_disposition_decided_at"],
    }
    if any(
        not _s41_exact_equal(receipt_values[field], value)
        for field, value in receipt_expectations.items()
    ):
        _s41_violate("physical_family_receipt_binding_mismatch")
    expected_result = {
        **expected_projection,
        "receipt_digest": receipt_values["receipt_digest"],
    }
    if not _s41_exact_equal(family["fresh_result"], expected_result):
        _s41_violate("physical_family_graph_digest_mismatch")
    if not _s41_exact_equal(family["replay_result"], expected_result):
        _s41_violate("physical_family_graph_digest_mismatch")
    _validate_repaired_c2b3d_lineage(family, rows_by_role)
    _validate_repaired_persisted_observation_and_chronology(
        family,
        rows_by_role,
    )
    if type(family["physical_row_count"]) is not int or family["physical_row_count"] != len(rows):
        _s41_violate("physical_family_missing_row")


@pytest.mark.parametrize("readiness_present", (False, True), ids=("absent", "present"))
def test_one_canonical_physical_collection_derives_entire_family(
    readiness_present: bool,
) -> None:
    owner = _parse_repaired_owner()["canonical_physical_family"]
    assert owner["member_field_order"] == REPAIRED_ROW_FIELDS
    incorporated_orders = dict(owner["complete_table_column_orders"])
    for table in REPAIRED_TABLE_ORDER:
        current_fields = tuple(
            name for name, _kind in REPAIRED_TABLE_COLUMNS[table]
        )
        incorporated_fields = incorporated_orders[table]
        if table in (REPAIRED_TABLE_ORDER[6], REPAIRED_TABLE_ORDER[7]):
            assert tuple(
                field for field in current_fields if field in incorporated_fields
            ) == incorporated_fields
            assert tuple(
                field for field in current_fields if field not in incorporated_fields
            ) == tuple(
                field
                for field in REPAIRED_C2B3D_LINEAGE_FIELDS
                if field not in incorporated_fields
            )
        else:
            assert current_fields == incorporated_fields
    assert owner["graph_entry_field_order"] == (
        "role", "rank", "ordinal", "table", "locator", "member_digest"
    )
    assert owner["result_projection_field_order"] == REPAIRED_RESULT_PROJECTION_FIELDS
    assert owner["fresh_and_replay_result_field_order"] == REPAIRED_FRESH_RESULT_FIELDS
    assert owner["physical_write_order_compared_as_set"] is False
    assert owner["physical_write_order_is_derived_projection"] is True
    assert owner["caller_supplies_physical_write_order"] is False
    assert "bool never aliases integer" in owner["exact_recursive_comparison"]
    assert owner["bool_or_container_subclass_order_alias_accepted"] is False
    assert owner["independently_supplied_graph_or_locator_ordinal_accepted"] is False
    assert "same row" in owner["canonical_ordinal_authority"]
    assert owner["receipt_independent_binding_checks"] == (
        "command_digest",
        "program_ref",
        "proposal_ref",
        "effect_intent_ref",
        "mutation_graph_digest",
        "result_projection_digest",
        "disposition_ref",
        "disposition_digest",
        "selection_head_revision",
        "selection_head_digest",
        "authority_selection_observation_ref",
        "authority_selection_observation_digest",
        "committed_at",
    )
    assert owner["distinct_valid_observations_produce_distinct_physical_families"] is True
    family = _build_repaired_physical_family(readiness_present)
    _validate_repaired_physical_family(family)
    assert family["physical_row_count"] == (23 if readiness_present else 22)
    assert len(family["graph"]["entries"]) == (22 if readiness_present else 21)
    assert tuple(entry["rank"] for entry in family["graph"]["entries"]) == (
        tuple(range(22)) if readiness_present else (*range(19), 20, 21)
    )
    assert family["receipt"]["role"] == "receipt"
    assert all(entry["role"] != "receipt" for entry in family["graph"]["entries"])
    assert family["fresh_result"] == family["replay_result"]
    assert family["fresh_result"] is not family["replay_result"]


def test_reaudit_fully_redigested_proposal_disposition_identity_collapse_is_causal() -> None:
    family = _build_repaired_physical_family(False)
    by_role = {row["role"]: row for row in family["physical_rows"]}
    proposal_ref = by_role["model_proposal"]["values"]["proposal_ref"]
    by_role["coordinator_disposition"]["values"]["disposition_ref"] = proposal_ref
    _redigest_repaired_physical_family(family)

    receipt = family["receipt"]["values"]
    with pytest.raises(_ContractViolation) as fresh_semantic_caught:
        _validate_repaired_command(
            family["command"],
            by_role,
            mutation_ref=receipt["mutation_ref"],
        )
    assert (
        fresh_semantic_caught.value.reason
        == "proposal_disposition_identity_collapse"
    )

    with pytest.raises(_ContractViolation) as principal_caught:
        _validate_repaired_physical_family(family)
    assert (
        principal_caught.value.reason
        == "proposal_disposition_identity_collapse"
    )
    with pytest.raises(_ContractViolation) as independent_caught:
        _independent_repaired_family_digest_ledger(family)
    assert (
        independent_caught.value.reason
        == "proposal_disposition_identity_collapse"
    )

    connection, _inventory = _install_repaired_temporary_schema()
    try:
        with pytest.raises(sqlite3.IntegrityError) as sqlite_caught:
            for member in family["physical_rows"]:
                _insert_exact_repaired_values(
                    connection,
                    member["table"],
                    member["values"],
                )
        assert sqlite_caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_CHECK"
        assert str(sqlite_caught.value) == (
            "CHECK constraint failed: proposal_disposition_identity_noncollapse"
        )
        connection.rollback()
        assert _recover_repaired_family(
            connection,
            expected_family=family,
            expected_head_preimage=None,
            fresh_writer_verified=True,
        ) == _RecoveryReadback("unresolved", 0, None)
    finally:
        connection.close()

    clock_calls = 0

    def forbidden_clock() -> str:
        nonlocal clock_calls
        clock_calls += 1
        raise AssertionError("replay clock called")

    with pytest.raises(_ContractViolation) as replay_caught:
        _apply_repaired_selection(
            mutation_ref=receipt["mutation_ref"],
            command_digest=receipt["command_digest"],
            receipt=family,
            bundle=object(),
            clock=forbidden_clock,
            trace=[],
        )
    assert (
        replay_caught.value.reason
        == "proposal_disposition_identity_collapse"
    )
    assert clock_calls == 0


@pytest.mark.parametrize(
    "role,field,bad_value",
    (
        ("source_invocation", "schema_id", "schema.cross-phase.invalid"),
        ("source_invocation", "proposal_phase", "post_execution_semantic_review"),
        ("source_invocation", "context_schema_id", SCHEMA_IDS["post_execution_context"]),
        ("source_invocation", "artifact_schema_id", SCHEMA_IDS["post_execution_artifact"]),
        ("private_artifact_binding", "schema_id", "schema.cross-phase.invalid"),
        ("private_artifact_binding", "proposal_phase", "post_execution_semantic_review"),
        ("private_artifact_binding", "artifact_schema_id", SCHEMA_IDS["post_execution_artifact"]),
        ("private_artifact_binding", "safe_projection_schema_id", SCHEMA_IDS["post_execution_projection"]),
        ("model_proposal", "schema_id", "schema.cross-phase.invalid"),
        ("model_proposal", "proposal_phase", "post_execution_semantic_review"),
        ("model_proposal", "context_schema_id", SCHEMA_IDS["post_execution_context"]),
        ("model_proposal", "artifact_schema_id", SCHEMA_IDS["post_execution_artifact"]),
        ("model_proposal", "safe_projection_schema_id", SCHEMA_IDS["post_execution_projection"]),
        ("model_proposal", "recommendation", "accept_candidate"),
        ("pre_execution_plan_projection", "schema_id", SCHEMA_IDS["post_execution_projection"]),
        ("pre_execution_plan_projection", "proposal_phase", "post_execution_semantic_review"),
        ("pre_execution_plan_projection", "artifact_schema_id", SCHEMA_IDS["post_execution_artifact"]),
        ("pre_execution_plan_projection", "planning_context_schema_id", SCHEMA_IDS["post_execution_context"]),
        ("pre_execution_plan_projection", "recommendation", "accept_candidate"),
        ("planning_context", "schema_id", SCHEMA_IDS["post_execution_context"]),
        ("evidence.standing_policy", "proposal_phase", "post_execution_semantic_review"),
        ("evidence.standing_policy", "evidence_role", "candidate_capsule"),
        ("evidence.standing_policy", "role_rank", 6),
        ("evidence.standing_policy", "required_for_selection", 0),
    ),
    ids=(
        "source-schema",
        "source-phase",
        "source-context-schema",
        "source-artifact-schema",
        "artifact-binding-schema",
        "artifact-phase",
        "artifact-schema",
        "artifact-projection-schema",
        "proposal-schema",
        "proposal-phase",
        "proposal-context-schema",
        "proposal-artifact-schema",
        "proposal-projection-schema",
        "proposal-recommendation",
        "projection-schema",
        "projection-phase",
        "projection-artifact-schema",
        "projection-context-schema",
        "projection-recommendation",
        "context-schema",
        "evidence-phase",
        "evidence-role",
        "evidence-rank",
        "evidence-required",
    ),
)
def test_s41_corr_001_redigested_phase_algebra_mutants_reach_exact_reason(
    role: str,
    field: str,
    bad_value: object,
) -> None:
    family = _build_repaired_physical_family(False)
    row = next(member for member in family["physical_rows"] if member["role"] == role)
    row["values"][field] = bad_value
    _redigest_repaired_physical_family(family)
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(family)
    assert caught.value.reason == "phase_algebra_mismatch"


def _malformed_supplied_physical_order(
    case_name: str,
    canonical: tuple[tuple[str, tuple[tuple[str, object], ...]], ...],
) -> object:
    if case_name == "false_zero_alias":
        changed = list(canonical)
        table, locator = changed[5]
        locator_parts = list(locator)
        field, value = locator_parts[-1]
        assert field == "ordinal" and value == 0
        locator_parts[-1] = (field, False)
        changed[5] = (table, tuple(locator_parts))
        return tuple(changed)
    if case_name == "tuple_subclass":
        return _S41TupleSubclass(canonical)
    if case_name == "row_swap":
        return (canonical[1], canonical[0], *canonical[2:])
    if case_name == "missing_entry":
        return canonical[:-1]
    if case_name == "extra_entry":
        return (*canonical, canonical[0])
    if case_name == "locator_mutation":
        table, locator = canonical[0]
        field, _value = locator[0]
        return ((table, ((field, "source.changed.0001"),)), *canonical[1:])
    if case_name == "inconsistent_value":
        return (("development_model_proposals", canonical[0][1]), *canonical[1:])
    raise AssertionError(case_name)


@pytest.mark.parametrize(
    "case_name",
    (
        "false_zero_alias",
        "tuple_subclass",
        "row_swap",
        "missing_entry",
        "extra_entry",
        "locator_mutation",
        "inconsistent_value",
    ),
)
def test_s41_corr_006_supplied_order_metadata_never_receives_replay(
    case_name: str,
) -> None:
    family = _build_repaired_physical_family(False)
    canonical = _derive_physical_write_order(family["physical_rows"])
    assert "physical_write_order" not in family
    family["physical_write_order"] = _malformed_supplied_physical_order(
        case_name,
        canonical,
    )
    receipt_values = family["receipt"]["values"]
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=receipt_values["mutation_ref"],
            command_digest=receipt_values["command_digest"],
            receipt=family,
            bundle=object(),
            clock=lambda: (_ for _ in ()).throw(
                AssertionError("MALFORMED_ORDER_CLOCK_CALLED")
            ),
            trace=trace,
        )
    assert caught.value.reason == "physical_family_extra_row"
    assert trace == ["receipt_lookup", "persisted_receipt_validation"]


def test_s41_corr_006_physical_write_order_is_only_an_exact_projection() -> None:
    family = _build_repaired_physical_family(True)
    order = _derive_physical_write_order(family["physical_rows"])
    assert type(order) is tuple
    assert len(order) == family["physical_row_count"]
    assert all(
        type(entry) is tuple
        and type(entry[0]) is str
        and type(entry[1]) is tuple
        and all(
            type(pair) is tuple
            and type(pair[0]) is str
            and type(pair[1]) in (str, int)
            and type(pair[1]) is not bool
            for pair in entry[1]
        )
        for entry in order
    )
    assert _s41_exact_equal(
        order,
        tuple(
            (row["table"], _member_locator(row))
            for row in family["physical_rows"]
        ),
    )


@pytest.mark.parametrize(
    "role",
    ("source_invocation", "receipt", "evidence.review_requirement"),
)
def test_missing_arbitrary_physical_row_reaches_exact_missing_reason(role: str) -> None:
    family = _build_repaired_physical_family(False)
    family["physical_rows"] = tuple(
        row for row in family["physical_rows"] if row["role"] != role
    )
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(family)
    assert caught.value.reason == "physical_family_missing_row"


def test_extra_arbitrary_physical_row_reaches_exact_extra_reason() -> None:
    family = _build_repaired_physical_family(False)
    extra = deepcopy(family["physical_rows"][5])
    extra["role"] = "evidence.unrecognized"
    family["physical_rows"] += (extra,)
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(family)
    assert caught.value.reason == "physical_family_extra_row"


def test_readiness_row_rank_mismatch_reaches_exact_missing_reason() -> None:
    family = _build_repaired_physical_family(False)
    family["readiness_present"] = True
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(family)
    assert caught.value.reason == "physical_family_missing_row"


def test_redigested_physical_source_with_stale_graph_reaches_graph_digest_reason() -> None:
    family = _build_repaired_physical_family(False)
    rows_by_role = {row["role"]: row for row in family["physical_rows"]}
    source = rows_by_role["source_invocation"]["values"]
    proposal = rows_by_role["model_proposal"]["values"]
    original_source_digest = source["source_invocation_digest"]
    source["model_contract_ref"] = "model-contract.changed.0001"
    proposal["model_contract_ref"] = source["model_contract_ref"]
    _redigest_repaired_physical_family(family)
    graph = deepcopy(family["graph"])
    source_entry = next(
        entry for entry in graph["entries"] if entry["role"] == "source_invocation"
    )
    source_entry["member_digest"] = original_source_digest
    graph["mutation_graph_digest"] = _s41_digest(
        "governed-execution.nwp-cognitive-mutation-graph.v1.identity",
        _s41_without(graph, "mutation_graph_digest"),
    )
    result_projection = deepcopy(family["result_projection"])
    result_projection["mutation_graph_digest"] = graph["mutation_graph_digest"]
    result_projection["result_projection_digest"] = _s41_digest(
        "governed-execution.nwp-pre-execution-plan-disposition-result.v1.identity",
        _s41_without(result_projection, "result_projection_digest"),
    )
    receipt = family["receipt"]
    receipt["values"]["mutation_graph_digest"] = graph["mutation_graph_digest"]
    receipt["values"]["result_projection_digest"] = result_projection[
        "result_projection_digest"
    ]
    receipt["values"]["receipt_digest"] = _repaired_row_digest(
        receipt["table"], receipt["values"]
    )
    family["graph"] = graph
    family["result_projection"] = result_projection
    family["fresh_result"] = {
        **result_projection,
        "receipt_digest": receipt["values"]["receipt_digest"],
    }
    family["replay_result"] = deepcopy(family["fresh_result"])
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(family)
    assert caught.value.reason == "physical_family_graph_digest_mismatch"


def test_receipt_graph_member_reaches_explicit_receipt_exclusion_first() -> None:
    family = _build_repaired_physical_family(False)
    receipt = family["receipt"]
    graph = deepcopy(family["graph"])
    graph["entries"] += (
        {
            "role": "receipt",
            "rank": 22,
            "ordinal": 0,
            "table": receipt["table"],
            "locator": _member_locator(receipt),
            "member_digest": _member_digest(receipt),
        },
    )
    graph["mutation_graph_digest"] = _s41_digest(
        "governed-execution.nwp-cognitive-mutation-graph.v1.identity",
        _s41_without(graph, "mutation_graph_digest"),
    )
    family["graph"] = graph
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(family)
    assert caught.value.reason == "physical_family_receipt_in_graph"


def test_graph_without_row_and_row_without_graph_have_distinct_exact_reasons() -> None:
    graph_without = _build_repaired_physical_family(False)
    graph = deepcopy(graph_without["graph"])
    graph["entries"] += (
        {
            "role": "evidence.ghost",
            "rank": 19,
            "ordinal": 0,
            "table": REPAIRED_TABLE_ORDER[5],
            "locator": (("proposal_ref", "ghost.0001"), ("evidence_role", "ghost"), ("ordinal", 0)),
            "member_digest": "d" * 64,
        },
    )
    graph_without["graph"] = graph
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(graph_without)
    assert caught.value.reason == "physical_family_graph_without_row"

    row_without = _build_repaired_physical_family(False)
    graph = deepcopy(row_without["graph"])
    graph["entries"] = tuple(
        entry for entry in graph["entries"] if entry["role"] != "source_invocation"
    )
    row_without["graph"] = graph
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(row_without)
    assert caught.value.reason == "physical_family_row_without_graph"


def test_reordered_physical_rows_reach_exact_order_reason() -> None:
    family = _build_repaired_physical_family(False)
    rows = list(family["physical_rows"])
    rows[0], rows[1] = rows[1], rows[0]
    family["physical_rows"] = tuple(rows)
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(family)
    assert caught.value.reason == "physical_family_order_mismatch"


def test_redigested_contradictory_receipt_reaches_exact_binding_reason() -> None:
    family = _build_repaired_physical_family(False)
    rows = list(family["physical_rows"])
    receipt = deepcopy(rows[-1])
    receipt["values"]["mutation_graph_digest"] = "f" * 64
    receipt["values"]["receipt_digest"] = _repaired_row_digest(
        receipt["table"], receipt["values"]
    )
    rows[-1] = receipt
    family["physical_rows"] = tuple(rows)
    family["receipt"] = receipt
    family["fresh_result"]["receipt_digest"] = receipt["values"]["receipt_digest"]
    family["replay_result"]["receipt_digest"] = receipt["values"]["receipt_digest"]
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(family)
    assert caught.value.reason == "physical_family_receipt_binding_mismatch"


@pytest.mark.parametrize(
    "bad_ordinal",
    (False, 1, -1),
    ids=("bool-false", "positive", "negative"),
)
def test_s41_audit_005_envelope_ordinal_is_bound_before_replay(
    bad_ordinal: object,
) -> None:
    family = _build_repaired_physical_family(False)
    evidence = next(
        row
        for row in family["physical_rows"]
        if row["role"] == "evidence.standing_policy"
    )
    evidence["ordinal"] = bad_ordinal
    receipt_values = family["receipt"]["values"]
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=receipt_values["mutation_ref"],
            command_digest=receipt_values["command_digest"],
            receipt=family,
            bundle=object(),
            clock=lambda: (_ for _ in ()).throw(
                AssertionError("ORDINAL_REPLAY_CLOCK_CALLED")
            ),
            trace=trace,
        )
    assert caught.value.reason == "physical_family_order_mismatch"
    assert trace == ["receipt_lookup", "persisted_receipt_validation"]


@pytest.mark.parametrize(
    "case_name",
    (
        "physical_rows_tuple_subclass",
        "physical_rows_list_subclass",
        "locator_tuple_subclass",
        "stale_locator_ordinal",
        "stale_graph_ordinal",
    ),
)
def test_s41_audit_005_container_and_graph_ordinals_fail_before_replay(
    case_name: str,
) -> None:
    family = _build_repaired_physical_family(False)
    expected_reason = "physical_family_graph_digest_mismatch"
    if case_name == "physical_rows_tuple_subclass":
        family["physical_rows"] = _S41TupleSubclass(family["physical_rows"])
        expected_reason = "physical_family_extra_row"
    elif case_name == "physical_rows_list_subclass":
        family["physical_rows"] = _S41ListSubclass(family["physical_rows"])
        expected_reason = "physical_family_extra_row"
    else:
        graph = deepcopy(family["graph"])
        entry = next(
            item for item in graph["entries"] if item["role"] == "evidence.standing_policy"
        )
        if case_name == "locator_tuple_subclass":
            entry["locator"] = _S41TupleSubclass(entry["locator"])
        elif case_name == "stale_locator_ordinal":
            locator = list(entry["locator"])
            locator[-1] = ("ordinal", 1)
            entry["locator"] = tuple(locator)
        elif case_name == "stale_graph_ordinal":
            entry["ordinal"] = 1
        else:
            raise AssertionError(case_name)
        graph["mutation_graph_digest"] = _s41_digest(
            "governed-execution.nwp-cognitive-mutation-graph.v1.identity",
            _s41_without(graph, "mutation_graph_digest"),
        )
        family["graph"] = graph
    receipt_values = family["receipt"]["values"]
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=receipt_values["mutation_ref"],
            command_digest=receipt_values["command_digest"],
            receipt=family,
            bundle=object(),
            clock=lambda: (_ for _ in ()).throw(
                AssertionError("ORDINAL_REPLAY_CLOCK_CALLED")
            ),
            trace=trace,
        )
    assert caught.value.reason == expected_reason
    assert trace == ["receipt_lookup", "persisted_receipt_validation"]


@pytest.mark.parametrize(
    "case_name,expected_reason",
    (
        ("proposal_recommendation", "physical_family_row_digest_mismatch"),
        ("receipt_program", "physical_family_row_digest_mismatch"),
        ("graph_role", "physical_family_graph_digest_mismatch"),
    ),
)
def test_s41_audit_003_hostile_equality_never_escapes_persisted_preflight(
    case_name: str,
    expected_reason: str,
) -> None:
    family = _build_repaired_physical_family(False)
    if case_name == "proposal_recommendation":
        next(
            row
            for row in family["physical_rows"]
            if row["role"] == "model_proposal"
        )["values"]["recommendation"] = _S41HostileEquality()
    elif case_name == "receipt_program":
        family["receipt"]["values"]["program_ref"] = _S41HostileEquality()
    elif case_name == "graph_role":
        family["graph"]["entries"][0]["role"] = _S41HostileEquality()
    else:
        raise AssertionError(case_name)
    receipt_values = family["receipt"]["values"]
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=receipt_values["mutation_ref"],
            command_digest=receipt_values["command_digest"],
            receipt=family,
            bundle=object(),
            clock=lambda: (_ for _ in ()).throw(
                AssertionError("HOSTILE_REPLAY_CLOCK_CALLED")
            ),
            trace=trace,
        )
    assert type(caught.value) is _ContractViolation
    assert caught.value.reason == expected_reason
    assert trace == ["receipt_lookup", "persisted_receipt_validation"]


@pytest.mark.parametrize(
    "field",
    (
        "command_digest",
        "program_ref",
        "proposal_ref",
        "disposition_ref",
        "effect_intent_ref",
        "selection_head_revision",
        "selection_head_digest",
        "result_projection_digest",
        "mutation_graph_digest",
        "committed_at",
    ),
)
def test_s41_audit_006_every_foreign_receipt_binding_fails_before_replay(
    field: str,
) -> None:
    family = _build_repaired_physical_family(False)
    foreign = _build_repaired_successor_family(
        family,
        suffix="foreign-existing.0001",
    )
    _validate_repaired_physical_family(foreign)
    receipt_values = family["receipt"]["values"]
    foreign_receipt_values = foreign["receipt"]["values"]
    original_mutation_ref = receipt_values["mutation_ref"]
    original_command_digest = receipt_values["command_digest"]
    foreign_value = {
        "program_ref": "program.foreign.existing",
        "effect_intent_ref": "effect.foreign.existing",
    }.get(field, foreign_receipt_values[field])
    assert not _s41_exact_equal(receipt_values[field], foreign_value)
    receipt_values[field] = foreign_value
    receipt_values["receipt_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[8],
        receipt_values,
    )
    family["fresh_result"]["receipt_digest"] = receipt_values["receipt_digest"]
    family["replay_result"]["receipt_digest"] = receipt_values["receipt_digest"]
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=original_mutation_ref,
            command_digest=original_command_digest,
            receipt=family,
            bundle=object(),
            clock=lambda: (_ for _ in ()).throw(
                AssertionError("FOREIGN_RECEIPT_REPLAY_CLOCK_CALLED")
            ),
            trace=trace,
        )
    assert caught.value.reason == "physical_family_receipt_binding_mismatch"
    assert trace == ["receipt_lookup", "persisted_receipt_validation"]


@pytest.mark.parametrize("case_name", ("envelope-ordinal", "foreign-receipt"))
def test_s41_audit_005_006_recovery_refuses_invalid_replay_family(
    case_name: str,
) -> None:
    persisted = _build_repaired_physical_family(False)
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        for member in persisted["physical_rows"]:
            _insert_exact_repaired_values(
                connection,
                member["table"],
                member["values"],
            )
        connection.commit()
        expected = deepcopy(persisted)
        if case_name == "envelope-ordinal":
            next(
                row
                for row in expected["physical_rows"]
                if row["role"] == "evidence.standing_policy"
            )["ordinal"] = 1
        else:
            expected["receipt"]["values"]["proposal_ref"] = (
                "proposal.foreign.existing"
            )
            expected["receipt"]["values"]["receipt_digest"] = (
                _repaired_row_digest(
                    REPAIRED_TABLE_ORDER[8],
                    expected["receipt"]["values"],
                )
            )
        assert _recover_repaired_family(
            connection,
            expected_family=expected,
            expected_head_preimage=None,
            fresh_writer_verified=True,
        ) == _RecoveryReadback("unresolved", 0, None)
    finally:
        connection.close()


def test_distinct_valid_observations_produce_distinct_complete_families() -> None:
    first_observation = _build_authority_observation()
    second_observation = _build_authority_observation(version=23)
    second_observation["authority_observation_ref"] = "authority-observation.supplied.0023"
    second_observation["verification_evidence_ref"] = "authority-verification.safe.0023"
    second_observation["verification_evidence_digest"] = "b" * 64
    second_observation["authority_observation_digest"] = _s41_digest(
        REPAIRED_AUTHORITY_DOMAIN,
        _s41_without(second_observation, "authority_observation_digest"),
    )
    second_binding = _authority_expected_binding()
    second_binding["verification_evidence_ref"] = second_observation["verification_evidence_ref"]
    second_binding["verification_evidence_digest"] = second_observation["verification_evidence_digest"]
    first = _build_repaired_physical_family(False, first_observation)
    with pytest.raises(_ContractViolation) as mismatch:
        _validate_authority_observation_non_temporal(second_observation, _authority_expected_binding())
    assert mismatch.value.reason == "authority_observation_binding_mismatch"
    second = _build_repaired_physical_family(
        False,
        second_observation,
        second_binding,
    )
    _validate_repaired_physical_family(first)
    _validate_repaired_physical_family(second)
    assert first["physical_rows"] != second["physical_rows"]
    assert first["receipt"] != second["receipt"]
    assert first["fresh_result"] != second["fresh_result"]
    assert first["replay_result"] != second["replay_result"]


REPAIRED_LINEAGE_COLUMNS = REPAIRED_C2B3D_LINEAGE_FIELDS
REPAIRED_IMMUTABLE_TABLES = (
    "development_model_source_invocations",
    "development_pre_execution_planning_contexts",
    "development_private_proposal_artifact_bindings",
    "development_model_proposals",
    "development_pre_execution_plan_projections",
    "development_model_proposal_evidence_bindings",
    "development_pre_execution_dispositions",
    "development_cognitive_mutation_receipts",
)
REPAIRED_RECOVERY_IDENTITY_FIELDS = {
    REPAIRED_TABLE_ORDER[0]: (
        ("source_invocation_ref",),
        ("proposal_phase", "source_invocation_ref"),
    ),
    REPAIRED_TABLE_ORDER[1]: (
        ("planning_context_ref",),
        ("program_ref", "planning_context_ref"),
    ),
    REPAIRED_TABLE_ORDER[2]: (
        ("artifact_ref",),
        ("proposal_phase", "artifact_ref"),
    ),
    REPAIRED_TABLE_ORDER[3]: (
        ("proposal_ref",),
        ("source_invocation_ref",),
        ("artifact_ref",),
        ("proposal_phase", "proposal_ref"),
    ),
    REPAIRED_TABLE_ORDER[4]: (
        ("proposal_ref",),
        ("artifact_ref",),
    ),
    REPAIRED_TABLE_ORDER[5]: (
        ("proposal_ref", "evidence_role", "ordinal"),
        ("proposal_ref", "role_rank", "ordinal"),
    ),
    REPAIRED_TABLE_ORDER[6]: (
        ("disposition_ref",),
        ("program_ref", "disposition_ref"),
        ("proposal_ref",),
        (*REPAIRED_LINEAGE_COLUMNS, "resulting_selection_head_revision"),
        (*REPAIRED_LINEAGE_COLUMNS, "prior_selection_head_revision"),
        (
            *REPAIRED_LINEAGE_COLUMNS,
            "disposition_ref",
            "resulting_selection_head_revision",
            "selection_head_postimage_digest",
        ),
        (
            *REPAIRED_LINEAGE_COLUMNS,
            "disposition_ref",
            "proposal_ref",
            "disposition",
            "resulting_selection_head_revision",
            "selection_head_postimage_digest",
        ),
        (
            "program_ref",
            "disposition_ref",
            "proposal_ref",
            "effect_intent_ref",
            "resulting_selection_head_revision",
            "selection_head_postimage_digest",
        ),
    ),
    REPAIRED_TABLE_ORDER[7]: (
        REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS,
        REPAIRED_LINEAGE_COLUMNS,
        ("effect_intent_ref",),
        ("program_ref", "effect_intent_ref"),
        (
            "program_ref",
            "effect_intent_ref",
            "current_proposal_ref",
            "current_disposition_ref",
            "head_revision",
            "head_digest",
        ),
    ),
    REPAIRED_TABLE_ORDER[8]: (
        ("mutation_ref",),
        ("program_ref", "mutation_ref"),
        ("disposition_ref",),
    ),
}
INCORPORATED_NINE_FINDING_RECOVERY_IDENTITY_FIELDS = {
    **REPAIRED_RECOVERY_IDENTITY_FIELDS,
    REPAIRED_TABLE_ORDER[6]: (
        ("disposition_ref",),
        ("program_ref", "disposition_ref"),
        ("proposal_ref",),
        (
            *REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS,
            "resulting_selection_head_revision",
        ),
        (
            *REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS,
            "prior_selection_head_revision",
        ),
        (
            *REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS,
            "disposition_ref",
            "resulting_selection_head_revision",
            "selection_head_postimage_digest",
        ),
        (
            *REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS,
            "disposition_ref",
            "proposal_ref",
            "disposition",
            "resulting_selection_head_revision",
            "selection_head_postimage_digest",
        ),
        (
            "program_ref",
            "disposition_ref",
            "proposal_ref",
            "effect_intent_ref",
            "resulting_selection_head_revision",
            "selection_head_postimage_digest",
        ),
    ),
    REPAIRED_TABLE_ORDER[7]: (
        REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS,
        ("effect_intent_ref",),
        ("program_ref", "effect_intent_ref"),
        (
            "program_ref",
            "effect_intent_ref",
            "current_proposal_ref",
            "current_disposition_ref",
            "head_revision",
            "head_digest",
        ),
    ),
}
_HISTORICAL_SYNTHETIC_REPAIRED_TABLE_DDL = """
CREATE TABLE development_model_source_invocations (
  source_invocation_ref ANY PRIMARY KEY CHECK(typeof(source_invocation_ref)='text'),
  source_invocation_digest ANY NOT NULL CHECK(typeof(source_invocation_digest)='text' AND length(source_invocation_digest)=64)
) STRICT;

CREATE TABLE development_pre_execution_planning_contexts (
  planning_context_ref ANY PRIMARY KEY CHECK(typeof(planning_context_ref)='text'),
  planning_context_digest ANY NOT NULL CHECK(typeof(planning_context_digest)='text' AND length(planning_context_digest)=64)
) STRICT;

CREATE TABLE development_private_proposal_artifact_bindings (
  artifact_ref ANY PRIMARY KEY CHECK(typeof(artifact_ref)='text'),
  artifact_digest ANY NOT NULL CHECK(typeof(artifact_digest)='text' AND length(artifact_digest)=64)
) STRICT;

CREATE TABLE development_model_proposals (
  proposal_ref ANY PRIMARY KEY CHECK(typeof(proposal_ref)='text'),
  source_invocation_ref ANY NOT NULL UNIQUE CHECK(typeof(source_invocation_ref)='text'),
  planning_context_ref ANY NOT NULL CHECK(typeof(planning_context_ref)='text'),
  artifact_ref ANY NOT NULL UNIQUE CHECK(typeof(artifact_ref)='text'),
  proposal_digest ANY NOT NULL CHECK(typeof(proposal_digest)='text' AND length(proposal_digest)=64),
  FOREIGN KEY(source_invocation_ref) REFERENCES development_model_source_invocations(source_invocation_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY(planning_context_ref) REFERENCES development_pre_execution_planning_contexts(planning_context_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY(artifact_ref) REFERENCES development_private_proposal_artifact_bindings(artifact_ref) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;

CREATE TABLE development_pre_execution_plan_projections (
  proposal_ref ANY PRIMARY KEY CHECK(typeof(proposal_ref)='text'),
  safe_projection_digest ANY NOT NULL CHECK(typeof(safe_projection_digest)='text' AND length(safe_projection_digest)=64),
  FOREIGN KEY(proposal_ref) REFERENCES development_model_proposals(proposal_ref) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;

CREATE TABLE development_model_proposal_evidence_bindings (
  proposal_ref ANY NOT NULL CHECK(typeof(proposal_ref)='text'),
  evidence_role ANY NOT NULL CHECK(typeof(evidence_role)='text'),
  role_rank ANY NOT NULL CHECK(typeof(role_rank)='integer' AND role_rank BETWEEN 5 AND 19),
  evidence_binding_digest ANY NOT NULL CHECK(typeof(evidence_binding_digest)='text' AND length(evidence_binding_digest)=64),
  PRIMARY KEY(proposal_ref,evidence_role),
  UNIQUE(proposal_ref,role_rank),
  FOREIGN KEY(proposal_ref) REFERENCES development_model_proposals(proposal_ref) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;

CREATE TABLE development_pre_execution_dispositions (
  program_ref ANY NOT NULL CHECK(typeof(program_ref)='text'),
  semantic_attempt_ref ANY NOT NULL CHECK(typeof(semantic_attempt_ref)='text'),
  candidate_ref ANY NOT NULL CHECK(typeof(candidate_ref)='text'),
  effect_intent_ref ANY NOT NULL CHECK(typeof(effect_intent_ref)='text'),
  author_command_ref ANY NOT NULL CHECK(typeof(author_command_ref)='text'),
  attempt_fence_ref ANY NOT NULL CHECK(typeof(attempt_fence_ref)='text'),
  effect_fence_ref ANY NOT NULL CHECK(typeof(effect_fence_ref)='text'),
  delivery_attempt_ref ANY NOT NULL CHECK(typeof(delivery_attempt_ref)='text'),
  proposal_ref ANY NOT NULL UNIQUE CHECK(typeof(proposal_ref)='text'),
  disposition_ref ANY PRIMARY KEY CHECK(typeof(disposition_ref)='text'),
  supersedes_disposition_ref ANY CHECK(supersedes_disposition_ref IS NULL OR typeof(supersedes_disposition_ref)='text'),
  prior_selection_head_revision ANY NOT NULL CHECK(typeof(prior_selection_head_revision)='integer' AND prior_selection_head_revision>=-1),
  prior_selection_head_digest ANY CHECK(prior_selection_head_digest IS NULL OR (typeof(prior_selection_head_digest)='text' AND length(prior_selection_head_digest)=64)),
  resulting_selection_head_revision ANY NOT NULL CHECK(typeof(resulting_selection_head_revision)='integer' AND resulting_selection_head_revision>=0),
  disposition_digest ANY NOT NULL CHECK(typeof(disposition_digest)='text' AND length(disposition_digest)=64),
  UNIQUE(program_ref,semantic_attempt_ref,candidate_ref,effect_intent_ref,author_command_ref,attempt_fence_ref,effect_fence_ref,delivery_attempt_ref,resulting_selection_head_revision),
  UNIQUE(program_ref,semantic_attempt_ref,candidate_ref,effect_intent_ref,author_command_ref,attempt_fence_ref,effect_fence_ref,delivery_attempt_ref,prior_selection_head_revision),
  UNIQUE(program_ref,semantic_attempt_ref,candidate_ref,effect_intent_ref,author_command_ref,attempt_fence_ref,effect_fence_ref,delivery_attempt_ref,disposition_ref,resulting_selection_head_revision,disposition_digest),
  CONSTRAINT disposition_root_or_successor_shape CHECK(
    (resulting_selection_head_revision=0 AND prior_selection_head_revision=-1 AND supersedes_disposition_ref IS NULL AND prior_selection_head_digest IS NULL)
    OR
    (resulting_selection_head_revision>0 AND prior_selection_head_revision=resulting_selection_head_revision-1 AND supersedes_disposition_ref IS NOT NULL AND prior_selection_head_digest IS NOT NULL)
  ),
  FOREIGN KEY(proposal_ref) REFERENCES development_model_proposals(proposal_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY(program_ref,semantic_attempt_ref,candidate_ref,effect_intent_ref,author_command_ref,attempt_fence_ref,effect_fence_ref,delivery_attempt_ref,supersedes_disposition_ref,prior_selection_head_revision,prior_selection_head_digest)
    REFERENCES development_pre_execution_dispositions(program_ref,semantic_attempt_ref,candidate_ref,effect_intent_ref,author_command_ref,attempt_fence_ref,effect_fence_ref,delivery_attempt_ref,disposition_ref,resulting_selection_head_revision,disposition_digest)
    ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;

CREATE TABLE development_pre_execution_selection_heads (
  program_ref ANY NOT NULL CHECK(typeof(program_ref)='text'),
  semantic_attempt_ref ANY NOT NULL CHECK(typeof(semantic_attempt_ref)='text'),
  candidate_ref ANY NOT NULL CHECK(typeof(candidate_ref)='text'),
  effect_intent_ref ANY NOT NULL CHECK(typeof(effect_intent_ref)='text'),
  author_command_ref ANY NOT NULL CHECK(typeof(author_command_ref)='text'),
  attempt_fence_ref ANY NOT NULL CHECK(typeof(attempt_fence_ref)='text'),
  effect_fence_ref ANY NOT NULL CHECK(typeof(effect_fence_ref)='text'),
  delivery_attempt_ref ANY NOT NULL CHECK(typeof(delivery_attempt_ref)='text'),
  current_disposition_ref ANY NOT NULL CHECK(typeof(current_disposition_ref)='text'),
  head_revision ANY NOT NULL CHECK(typeof(head_revision)='integer' AND head_revision>=0),
  head_digest ANY NOT NULL CHECK(typeof(head_digest)='text' AND length(head_digest)=64),
  updated_at ANY NOT NULL CHECK(typeof(updated_at)='text'),
  PRIMARY KEY(program_ref,semantic_attempt_ref,candidate_ref,effect_intent_ref,author_command_ref,attempt_fence_ref,effect_fence_ref,delivery_attempt_ref),
  FOREIGN KEY(program_ref,semantic_attempt_ref,candidate_ref,effect_intent_ref,author_command_ref,attempt_fence_ref,effect_fence_ref,delivery_attempt_ref,current_disposition_ref,head_revision,head_digest)
    REFERENCES development_pre_execution_dispositions(program_ref,semantic_attempt_ref,candidate_ref,effect_intent_ref,author_command_ref,attempt_fence_ref,effect_fence_ref,delivery_attempt_ref,disposition_ref,resulting_selection_head_revision,disposition_digest)
    ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;

CREATE TABLE development_cognitive_mutation_receipts (
  mutation_ref ANY PRIMARY KEY CHECK(typeof(mutation_ref)='text'),
  proposal_ref ANY NOT NULL CHECK(typeof(proposal_ref)='text'),
  disposition_ref ANY NOT NULL UNIQUE CHECK(typeof(disposition_ref)='text'),
  mutation_graph_digest ANY NOT NULL CHECK(typeof(mutation_graph_digest)='text' AND length(mutation_graph_digest)=64),
  receipt_digest ANY NOT NULL CHECK(typeof(receipt_digest)='text' AND length(receipt_digest)=64),
  FOREIGN KEY(proposal_ref) REFERENCES development_model_proposals(proposal_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY(disposition_ref) REFERENCES development_pre_execution_dispositions(disposition_ref) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;
"""


def _sqlite_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _sqlite_ascii_text_is_byte_complete(quoted: str) -> str:
    return (
        f"typeof({quoted})='text' "
        f"AND length(CAST({quoted} AS BLOB))=length({quoted})"
    )


def _sqlite_kind_check(field: str, kind: str) -> str:
    quoted = f'"{field}"'
    byte_complete = _sqlite_ascii_text_is_byte_complete(quoted)
    if kind.startswith("literal_int:"):
        return f"typeof({quoted})='integer' AND {quoted}={int(kind.split(':', 1)[1])}"
    if kind.startswith("literal:"):
        literal = _sqlite_literal(kind.split(":", 1)[1])
        return f"{byte_complete} AND {quoted}={literal}"
    if kind in ("safe_ref", "nullable_safe_ref"):
        core = (
            f"{byte_complete} AND length(CAST({quoted} AS BLOB)) BETWEEN 1 AND 96 "
            f"AND {quoted} NOT GLOB '*[^0-9A-Za-z.-]*' "
            f"AND substr({quoted},1,1) GLOB '[0-9A-Za-z]' "
            f"AND lower({quoted}) NOT GLOB 'connector-*' "
            f"AND lower({quoted}) NOT GLOB 'tunnel-*' "
            f"AND lower({quoted}) NOT GLOB 'workspace-*' "
            f"AND lower({quoted}) NOT GLOB 'org-*' "
            f"AND lower({quoted}) NOT GLOB 'organization-*' "
            f"AND lower({quoted}) NOT GLOB 'user-*'"
        )
        return f"{quoted} IS NULL OR ({core})" if kind.startswith("nullable_") else core
    if kind in ("sha256", "nullable_sha256"):
        core = (
            f"{byte_complete} AND length(CAST({quoted} AS BLOB))=64 "
            f"AND {quoted} NOT GLOB '*[^0-9a-f]*'"
        )
        return f"{quoted} IS NULL OR ({core})" if kind.startswith("nullable_") else core
    if kind == "sha1":
        return (
            f"{byte_complete} AND length(CAST({quoted} AS BLOB))=40 "
            f"AND {quoted} NOT GLOB '*[^0-9a-f]*'"
        )
    if kind == "utc_second":
        return (
            f"{byte_complete} AND length(CAST({quoted} AS BLOB))=20 "
            f"AND {quoted} GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' "
            f"AND substr({quoted},1,4) BETWEEN '0001' AND '9999' "
            f"AND substr({quoted},6,2) BETWEEN '01' AND '12' "
            f"AND substr({quoted},9,2) BETWEEN '01' AND '31' "
            f"AND substr({quoted},12,2) BETWEEN '00' AND '23' "
            f"AND substr({quoted},15,2) BETWEEN '00' AND '59' "
            f"AND substr({quoted},18,2) BETWEEN '00' AND '59' "
            f"AND strftime('%Y-%m-%dT%H:%M:%SZ',{quoted}) IS NOT NULL "
            f"AND strftime('%Y-%m-%dT%H:%M:%SZ',{quoted})={quoted}"
        )
    if kind == "positive_int":
        return (
            f"typeof({quoted})='integer' AND {quoted} BETWEEN 1 AND "
            f"{SQLITE_INTEGER_MAX}"
        )
    if kind == "nonnegative_int":
        return (
            f"typeof({quoted})='integer' AND {quoted} BETWEEN 0 AND "
            f"{SQLITE_INTEGER_MAX}"
        )
    if kind == "selection_prior_revision":
        return (
            f"typeof({quoted})='integer' AND {quoted} BETWEEN -1 AND "
            f"{SQLITE_INTEGER_MAX}"
        )
    if kind == "nullable_nonnegative_int":
        return (
            f"{quoted} IS NULL OR (typeof({quoted})='integer' AND "
            f"{quoted} BETWEEN 0 AND {SQLITE_INTEGER_MAX})"
        )
    if kind.startswith("int:"):
        match = re.fullmatch(r"int:([0-9]+)\.\.([0-9]+)", kind)
        assert match is not None
        return (
            f"typeof({quoted})='integer' AND {quoted} BETWEEN "
            f"{int(match.group(1))} AND {int(match.group(2))}"
        )
    if kind == "bool_int":
        return f"typeof({quoted})='integer' AND {quoted} IN (0,1)"
    if kind == "phase_evidence_rank":
        return f"typeof({quoted})='integer' AND {quoted} BETWEEN 5 AND 19"
    if kind == "canonical_effect_class_json":
        canonical_values = tuple(
            _s41_canonical_bytes(
                tuple(
                    effect
                    for ordinal, effect in enumerate(REPAIRED_EFFECT_CLASSES)
                    if mask & (1 << ordinal)
                )
            ).decode("utf-8")
            for mask in range(1, 1 << len(REPAIRED_EFFECT_CLASSES))
        )
        return (
            f"{byte_complete} AND {quoted} IN ("
            + ",".join(_sqlite_literal(value) for value in canonical_values)
            + ")"
        )
    if kind == "reason_code":
        return (
            f"{byte_complete} AND length(CAST({quoted} AS BLOB)) BETWEEN 1 AND 96 "
            f"AND {quoted} NOT GLOB '*[^a-z0-9_.-]*' "
            f"AND substr({quoted},1,1) GLOB '[a-z]'"
        )
    vocabulary = _repaired_kind_vocabulary(kind)
    if vocabulary is not None:
        return (
            f"{byte_complete} AND {quoted} IN ("
            + ",".join(_sqlite_literal(value) for value in vocabulary)
            + ")"
        )
    return byte_complete


REPAIRED_SUPPLEMENTAL_FOREIGN_KEYS = {
    REPAIRED_TABLE_ORDER[6]: (
        (
            (
                *REPAIRED_LINEAGE_COLUMNS,
                "supersedes_disposition_ref",
                "prior_selection_head_revision",
                "prior_selection_head_digest",
            ),
            REPAIRED_TABLE_ORDER[6],
            (
                *REPAIRED_LINEAGE_COLUMNS,
                "disposition_ref",
                "resulting_selection_head_revision",
                "selection_head_postimage_digest",
            ),
            "IMMEDIATE",
        ),
    ),
    REPAIRED_TABLE_ORDER[7]: (
        (
            (
                *REPAIRED_LINEAGE_COLUMNS,
                "current_disposition_ref",
                "current_proposal_ref",
                "current_disposition",
                "head_revision",
                "head_digest",
            ),
            REPAIRED_TABLE_ORDER[6],
            (
                *REPAIRED_LINEAGE_COLUMNS,
                "disposition_ref",
                "proposal_ref",
                "disposition",
                "resulting_selection_head_revision",
                "selection_head_postimage_digest",
            ),
            "IMMEDIATE",
        ),
    ),
}
INCORPORATED_NINE_FINDING_SUPPLEMENTAL_FOREIGN_KEYS = {
    REPAIRED_TABLE_ORDER[6]: (
        (
            (
                *REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS,
                "supersedes_disposition_ref",
                "prior_selection_head_revision",
                "prior_selection_head_digest",
            ),
            REPAIRED_TABLE_ORDER[6],
            (
                *REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS,
                "disposition_ref",
                "resulting_selection_head_revision",
                "selection_head_postimage_digest",
            ),
            "IMMEDIATE",
        ),
    ),
    REPAIRED_TABLE_ORDER[7]: (
        (
            (
                *REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS,
                "current_disposition_ref",
                "current_proposal_ref",
                "current_disposition",
                "head_revision",
                "head_digest",
            ),
            REPAIRED_TABLE_ORDER[6],
            (
                *REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS,
                "disposition_ref",
                "proposal_ref",
                "disposition",
                "resulting_selection_head_revision",
                "selection_head_postimage_digest",
            ),
            "IMMEDIATE",
        ),
    ),
}
REPAIRED_BASE_FOREIGN_KEYS = {
    table: TABLE_CONTRACTS[table]["foreign_keys"]
    for table in REPAIRED_TABLE_ORDER
}
REPAIRED_BASE_FOREIGN_KEYS.update(
    {
        REPAIRED_TABLE_ORDER[3]: (
            (
                ("proposal_phase", "source_invocation_ref"),
                REPAIRED_TABLE_ORDER[0],
                ("proposal_phase", "source_invocation_ref"),
                "IMMEDIATE",
            ),
            (
                ("proposal_phase", "artifact_ref"),
                REPAIRED_TABLE_ORDER[2],
                ("proposal_phase", "artifact_ref"),
                "IMMEDIATE",
            ),
        ),
        REPAIRED_TABLE_ORDER[4]: (
            (
                ("proposal_phase", "proposal_ref"),
                REPAIRED_TABLE_ORDER[3],
                ("proposal_phase", "proposal_ref"),
                "IMMEDIATE",
            ),
            (
                ("proposal_phase", "artifact_ref"),
                REPAIRED_TABLE_ORDER[2],
                ("proposal_phase", "artifact_ref"),
                "IMMEDIATE",
            ),
            TABLE_CONTRACTS[REPAIRED_TABLE_ORDER[4]]["foreign_keys"][2],
        ),
        REPAIRED_TABLE_ORDER[5]: (
            (
                ("proposal_phase", "proposal_ref"),
                REPAIRED_TABLE_ORDER[3],
                ("proposal_phase", "proposal_ref"),
                "IMMEDIATE",
            ),
        ),
        REPAIRED_TABLE_ORDER[6]: (
            (
                ("proposal_phase", "proposal_ref"),
                REPAIRED_TABLE_ORDER[3],
                ("proposal_phase", "proposal_ref"),
                "IMMEDIATE",
            ),
            *TABLE_CONTRACTS[REPAIRED_TABLE_ORDER[6]]["foreign_keys"][1:],
        ),
        REPAIRED_TABLE_ORDER[8]: (
            TABLE_CONTRACTS[REPAIRED_TABLE_ORDER[8]]["foreign_keys"][0],
            (
                (
                    "program_ref",
                    "disposition_ref",
                    "proposal_ref",
                    "effect_intent_ref",
                    "selection_head_revision",
                    "selection_head_digest",
                ),
                REPAIRED_TABLE_ORDER[6],
                (
                    "program_ref",
                    "disposition_ref",
                    "proposal_ref",
                    "effect_intent_ref",
                    "resulting_selection_head_revision",
                    "selection_head_postimage_digest",
                ),
                "IMMEDIATE",
            ),
            TABLE_CONTRACTS[REPAIRED_TABLE_ORDER[8]]["foreign_keys"][2],
        ),
    }
)
REPAIRED_TABLE_FOREIGN_KEYS = {
    table: (
        *REPAIRED_BASE_FOREIGN_KEYS[table],
        *REPAIRED_SUPPLEMENTAL_FOREIGN_KEYS.get(table, ()),
    )
    for table in REPAIRED_TABLE_ORDER
}


def _render_repaired_foreign_key(
    specification: tuple[tuple[str, ...], str, tuple[str, ...], str],
) -> str:
    child_columns, parent_table, parent_columns, timing = specification
    assert timing == "IMMEDIATE"
    assert len(child_columns) == len(parent_columns) and child_columns
    return (
        f"FOREIGN KEY({','.join(child_columns)}) "
        f"REFERENCES {parent_table}({','.join(parent_columns)}) "
        "ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE"
    )


def _sqlite_phase_algebra_constraint(table: str) -> str | None:
    clauses: list[str] = []
    for phase, contract in REPAIRED_PHASE_ALGEBRA.items():
        phase_literal = _sqlite_literal(phase)
        if table == REPAIRED_TABLE_ORDER[0]:
            clauses.append(
                "("
                f"proposal_phase={phase_literal} "
                f"AND context_schema_id={_sqlite_literal(contract['context_schema_id'])} "
                f"AND artifact_schema_id={_sqlite_literal(contract['private_artifact_schema_id'])}"
                ")"
            )
        elif table == REPAIRED_TABLE_ORDER[2]:
            clauses.append(
                "("
                f"proposal_phase={phase_literal} "
                f"AND artifact_schema_id={_sqlite_literal(contract['private_artifact_schema_id'])} "
                f"AND safe_projection_schema_id={_sqlite_literal(contract['safe_projection_schema_id'])}"
                ")"
            )
        elif table == REPAIRED_TABLE_ORDER[3]:
            recommendations = ",".join(
                _sqlite_literal(value) for value in contract["recommendations"]
            )
            clauses.append(
                "("
                f"proposal_phase={phase_literal} "
                f"AND context_schema_id={_sqlite_literal(contract['context_schema_id'])} "
                f"AND artifact_schema_id={_sqlite_literal(contract['private_artifact_schema_id'])} "
                f"AND safe_projection_schema_id={_sqlite_literal(contract['safe_projection_schema_id'])} "
                f"AND recommendation IN ({recommendations})"
                ")"
            )
        elif table == REPAIRED_TABLE_ORDER[5]:
            evidence_clauses = " OR ".join(
                "("
                f"evidence_role={_sqlite_literal(role)} "
                f"AND role_rank={rank} "
                "AND ordinal=0 "
                f"AND required_for_selection={int(required)}"
                ")"
                for role, rank, required in contract["evidence_roles"]
            )
            clauses.append(
                f"(proposal_phase={phase_literal} AND ({evidence_clauses}))"
            )
    if not clauses:
        return None
    return (
        f"CONSTRAINT {table}_phase_algebra CHECK("
        + " OR ".join(clauses)
        + ")"
    )


def _build_repaired_table_ddl(
    foreign_keys: dict[
        str,
        tuple[tuple[tuple[str, ...], str, tuple[str, ...], str], ...],
    ]
    | None = None,
) -> str:
    selected_foreign_keys = (
        REPAIRED_TABLE_FOREIGN_KEYS if foreign_keys is None else foreign_keys
    )
    constraints: dict[str, tuple[str, ...]] = {
        REPAIRED_TABLE_ORDER[0]: (
            "PRIMARY KEY(source_invocation_ref)",
            "UNIQUE(proposal_phase,source_invocation_ref)",
        ),
        REPAIRED_TABLE_ORDER[1]: (
            "PRIMARY KEY(planning_context_ref)",
            "UNIQUE(program_ref,planning_context_ref)",
        ),
        REPAIRED_TABLE_ORDER[2]: (
            "PRIMARY KEY(artifact_ref)",
            "UNIQUE(proposal_phase,artifact_ref)",
        ),
        REPAIRED_TABLE_ORDER[3]: (
            "PRIMARY KEY(proposal_ref)",
            "UNIQUE(source_invocation_ref)",
            "UNIQUE(artifact_ref)",
            "UNIQUE(proposal_phase,proposal_ref)",
        ),
        REPAIRED_TABLE_ORDER[4]: (
            "PRIMARY KEY(proposal_ref)",
            "UNIQUE(artifact_ref)",
        ),
        REPAIRED_TABLE_ORDER[5]: (
            "PRIMARY KEY(proposal_ref,evidence_role,ordinal)",
            "UNIQUE(proposal_ref,role_rank,ordinal)",
        ),
        REPAIRED_TABLE_ORDER[6]: (
            "PRIMARY KEY(disposition_ref)",
            "UNIQUE(program_ref,disposition_ref)",
            "UNIQUE(proposal_ref)",
            f"UNIQUE({','.join(REPAIRED_LINEAGE_COLUMNS)},resulting_selection_head_revision)",
            f"UNIQUE({','.join(REPAIRED_LINEAGE_COLUMNS)},prior_selection_head_revision)",
            f"UNIQUE({','.join(REPAIRED_LINEAGE_COLUMNS)},disposition_ref,resulting_selection_head_revision,selection_head_postimage_digest)",
            f"UNIQUE({','.join(REPAIRED_LINEAGE_COLUMNS)},disposition_ref,proposal_ref,disposition,resulting_selection_head_revision,selection_head_postimage_digest)",
            "UNIQUE(program_ref,disposition_ref,proposal_ref,effect_intent_ref,resulting_selection_head_revision,selection_head_postimage_digest)",
            "CONSTRAINT proposal_disposition_identity_noncollapse CHECK(disposition_ref != proposal_ref)",
            "CONSTRAINT disposition_root_or_successor_shape CHECK((resulting_selection_head_revision=0 AND prior_selection_head_revision=-1 AND supersedes_disposition_ref IS NULL AND prior_selection_head_digest IS NULL AND expected_selection_head_revision IS NULL AND expected_selection_head_digest IS NULL) OR (resulting_selection_head_revision>0 AND prior_selection_head_revision=resulting_selection_head_revision-1 AND supersedes_disposition_ref IS NOT NULL AND prior_selection_head_digest IS NOT NULL AND expected_selection_head_revision IS NOT NULL AND expected_selection_head_digest IS NOT NULL AND expected_selection_head_revision=prior_selection_head_revision AND expected_selection_head_digest=prior_selection_head_digest))",
        ),
        REPAIRED_TABLE_ORDER[7]: (
            f"PRIMARY KEY({','.join(REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS)})",
            f"UNIQUE({','.join(REPAIRED_LINEAGE_COLUMNS)})",
            "UNIQUE(effect_intent_ref)",
            "UNIQUE(program_ref,effect_intent_ref)",
            "UNIQUE(program_ref,effect_intent_ref,current_proposal_ref,current_disposition_ref,head_revision,head_digest)",
        ),
        REPAIRED_TABLE_ORDER[8]: (
            "PRIMARY KEY(mutation_ref)",
            "UNIQUE(program_ref,mutation_ref)",
            "UNIQUE(disposition_ref)",
        ),
    }
    statements: list[str] = []
    for table in REPAIRED_TABLE_ORDER:
        definitions: list[str] = []
        for field, kind in REPAIRED_TABLE_COLUMNS[table]:
            nullable = kind.startswith("nullable_") or field == "supersedes_disposition_ref"
            definitions.append(
                f'  "{field}" ANY' + ("" if nullable else " NOT NULL")
                + f" CHECK({_sqlite_kind_check(field, kind)})"
            )
        phase_constraint = _sqlite_phase_algebra_constraint(table)
        if phase_constraint is not None:
            definitions.append(f"  {phase_constraint}")
        definitions.extend(f"  {constraint}" for constraint in constraints[table])
        definitions.extend(
            f"  {_render_repaired_foreign_key(specification)}"
            for specification in selected_foreign_keys[table]
        )
        statements.append(
            f'CREATE TABLE "{table}" (\n' + ",\n".join(definitions) + "\n) STRICT;"
        )
    return "\n\n".join(statements)


REPAIRED_TABLE_DDL = _build_repaired_table_ddl()


def _install_repaired_temporary_schema(
    *,
    seed_c2b3d_parents: bool = True,
    repaired_table_ddl: str = REPAIRED_TABLE_DDL,
) -> tuple[sqlite3.Connection, dict[str, int]]:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    migration_root = ROOT / "src" / "ge_nwp_coordinator" / "sqlite_migrations"
    connection.executescript((migration_root / "0001_initial.sql").read_text(encoding="utf-8"))
    connection.executescript(
        (migration_root / "0002_development_program_and_effect_state.sql").read_text(encoding="utf-8")
    )
    baseline_tables = connection.execute(
        "SELECT count(*) FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()[0]
    baseline_triggers = connection.execute(
        "SELECT count(*) FROM sqlite_schema WHERE type='trigger'"
    ).fetchone()[0]
    baseline_explicit_indexes = connection.execute(
        "SELECT count(*) FROM sqlite_schema WHERE type='index' AND sql IS NOT NULL"
    ).fetchone()[0]
    connection.executescript(repaired_table_ddl)
    for table in REPAIRED_IMMUTABLE_TABLES:
        connection.executescript(
            f"""
            CREATE TRIGGER {table}_no_update BEFORE UPDATE ON {table}
            BEGIN SELECT RAISE(ABORT,'immutable_{table}'); END;
            CREATE TRIGGER {table}_no_delete BEFORE DELETE ON {table}
            BEGIN SELECT RAISE(ABORT,'immutable_{table}'); END;
            """
        )
    immutable_head_change = " OR ".join(
        f'OLD."{field}" IS NOT NEW."{field}"'
        for field in REPAIRED_SELECTION_HEAD_ALL_IMMUTABLE_FIELDS
    )
    connection.executescript(
        f"""
        CREATE TRIGGER development_pre_execution_selection_heads_no_delete
        BEFORE DELETE ON development_pre_execution_selection_heads
        BEGIN SELECT RAISE(ABORT,'append_only_selection_head'); END;
        CREATE TRIGGER development_pre_execution_selection_heads_lineage_immutable
        BEFORE UPDATE
        ON development_pre_execution_selection_heads
        WHEN {immutable_head_change}
        BEGIN SELECT RAISE(ABORT,'immutable_selection_head_lineage'); END;
        """
    )
    if seed_c2b3d_parents:
        _insert_exact_c2b3d_parent_rows(connection)
    return connection, {
        "baseline_tables": baseline_tables,
        "added_tables": connection.execute(
            "SELECT count(*) FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchone()[0] - baseline_tables,
        "added_triggers": connection.execute(
            "SELECT count(*) FROM sqlite_schema WHERE type='trigger'"
        ).fetchone()[0] - baseline_triggers,
        "added_explicit_indexes": connection.execute(
            "SELECT count(*) FROM sqlite_schema WHERE type='index' AND sql IS NOT NULL"
        ).fetchone()[0] - baseline_explicit_indexes,
    }


def _sqlite_lineage(suffix: str) -> tuple[object, ...]:
    assert type(suffix) is str and suffix
    values: list[object] = []
    for field, kind in REPAIRED_C2B3D_LINEAGE_FIELD_SPECS:
        basis_value = C2B3D_BASIS[field]
        if kind == "safe_ref":
            values.append(f"{basis_value}.{suffix}")
        elif kind == "sha256":
            values.append(
                hashlib.sha256(f"{field}:{suffix}".encode("utf-8")).hexdigest()
            )
        elif kind == "positive_int":
            assert type(basis_value) is int
            values.append(basis_value + 1)
        else:
            raise AssertionError(kind)
    return tuple(values)


_SQLITE_PREREQUISITE_TEMPLATES: dict[str, dict[str, object]] | None = None
_SQLITE_DISPOSITION_TEMPLATE: dict[str, object] | None = None

_EXACT_C2B3A_PARENT_ROWS = (
    (
        "development_program_heads",
        {
            "schema_id": "governed-execution.nwp-development-program-head.v1",
            "program_ref": "program-c2b3a-1",
            "current_program_version_ref": "program-version-c2b3a-1",
            "current_program_version_number": 1,
            "head_revision": 0,
            "program_state": "active",
            "updated_at": "2026-08-21T12:34:56Z",
            "head_digest": "79b933902d113c5dda9c054b56cb105a8f9ed25513eaf91656c72efe53ee7058",
        },
    ),
    (
        "development_accepted_intent_revisions",
        {
            "schema_id": "governed-execution.nwp-development-accepted-intent-revision.v1",
            "accepted_intent_revision_ref": "accepted-intent-c2b3a-1",
            "program_ref": "program-c2b3a-1",
            "accepted_intent_revision_number": 1,
            "prior_accepted_intent_revision_ref": None,
            "source_intent_ref": "source-intent-c2b3a-1",
            "source_intent_digest": "1" * 64,
            "safe_projection_digest": "8e76f55695e0f3bda1af480bb00fbd4bcff4c6c0270d80c65ffbe61f67c92ce1",
            "created_at": "2026-08-21T12:34:56Z",
            "accepted_intent_revision_digest": "4f903ee159a9ee9ac8bb1ce0803ed4d899e73a16da6a8dd84621ccd30bfd60ab",
        },
    ),
    (
        "development_work_item_heads",
        {
            "schema_id": "governed-execution.nwp-development-work-item-head.v1",
            "work_item_ref": "work-item-c2b3a-1",
            "program_ref": "program-c2b3a-1",
            "current_work_item_revision_ref": "work-item-revision-c2b3a-1",
            "current_work_item_revision_number": 1,
            "head_revision": 0,
            "work_state": "planned",
            "updated_at": "2026-08-21T12:34:56Z",
            "head_digest": "67acca455028e770d816c509ac1c6936cf69a7ec582da412941df2b7f0986405",
        },
    ),
    (
        "development_work_item_revisions",
        {
            "schema_id": "governed-execution.nwp-development-work-item-revision.v1",
            "work_item_revision_ref": "work-item-revision-c2b3a-1",
            "program_ref": "program-c2b3a-1",
            "work_item_ref": "work-item-c2b3a-1",
            "work_item_revision_number": 1,
            "work_item_revision_kind": "initial",
            "prior_work_item_revision_ref": None,
            "accepted_intent_revision_ref": "accepted-intent-c2b3a-1",
            "created_at": "2026-08-21T12:34:56Z",
            "work_item_revision_digest": "23d7354b797a03faf0bdaee2bce03752258443cc9e232a26c47a0e8a7069a215",
        },
    ),
    (
        "development_decisions",
        {
            "schema_id": "governed-execution.nwp-development-decision.v1",
            "mutation_ref": "mutation-c2b3a-1",
            "decision_ref": "decision-c2b3a-1",
            "program_ref": "program-c2b3a-1",
            "decision_kind": "initialize",
            "decision_variant": "program_genesis",
            "basis_decision_ref": None,
            "basis_program_version_ref": None,
            "basis_program_version_number": None,
            "expected_program_head_revision": 0,
            "resulting_program_version_ref": "program-version-c2b3a-1",
            "resulting_program_version_number": 1,
            "selected_semantic_attempt_ref": None,
            "selected_candidate_ref": None,
            "selected_attempt_fence_ref": None,
            "selected_attempt_fence_digest": None,
            "target_effect_intent_ref": None,
            "target_effect_class": None,
            "target_effect_fence_ref": None,
            "target_effect_fence_digest": None,
            "expected_target_effect_head_revision": None,
            "target_delivery_attempt_ref": None,
            "originating_command_ref": None,
            "originating_command_digest": None,
            "target_capsule_manifest_ref": None,
            "target_portable_capsule_digest": None,
            "coding_global_stop_ref": "coding-global-stop-c2b3a-1",
            "coding_global_stop_version": 0,
            "source_directive_ref": None,
            "source_directive_digest": None,
            "source_evidence_ref": None,
            "source_evidence_digest": None,
            "preassigned_semantic_attempt_ref": "semantic-attempt-c2b3a-1",
            "preassigned_candidate_ref": "candidate-c2b3a-1",
            "preassigned_effect_intent_ref": None,
            "preassigned_effect_fence_ref": None,
            "preassigned_delivery_attempt_ref": None,
            "resulting_accepted_intent_revision_ref": None,
            "resulting_work_item_ref": None,
            "resulting_work_item_revision_ref": None,
            "reason_code": "program_genesis",
            "decided_at": "2026-08-21T12:34:56Z",
            "decision_digest": "e743c359aea93d7931250552b62bc741d84c490f9ebb68e071c8616cc5fb4b96",
        },
    ),
    (
        "development_program_versions",
        {
            "schema_id": "governed-execution.nwp-development-program-version.v1",
            "program_version_ref": "program-version-c2b3a-1",
            "program_ref": "program-c2b3a-1",
            "program_version_number": 1,
            "program_version_kind": "initial",
            "creating_decision_ref": "decision-c2b3a-1",
            "accepted_intent_revision_ref": "accepted-intent-c2b3a-1",
            "created_at": "2026-08-21T12:34:56Z",
            "program_version_digest": "f06037aaa718343f8676ec00d5b26b2be6fd7ab58683292f6fbe4b461b8374b9",
        },
    ),
    (
        "development_work_spec_bindings",
        {
            "schema_id": "governed-execution.nwp-development-work-spec-binding.v1",
            "work_spec_ref": "work-spec-c2b3a-1",
            "program_ref": "program-c2b3a-1",
            "program_version_ref": "program-version-c2b3a-1",
            "accepted_intent_revision_ref": "accepted-intent-c2b3a-1",
            "work_item_ref": "work-item-c2b3a-1",
            "work_item_revision_ref": "work-item-revision-c2b3a-1",
            "repository_ref": "repository-c2b3a-1",
            "base_git_object_format": "sha1",
            "base_git_oid": "2" * 40,
            "authorized_paths_json": '[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"]',
            "validation_requirement_ref": "validation-c2b3a-1",
            "review_requirement_ref": "review-c2b3a-1",
            "privacy_classification": "private_work_spec",
            "work_spec_digest": "2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c",
            "safe_projection_digest": "1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab",
            "recorded_at": "2026-08-21T12:34:56Z",
            "work_spec_binding_digest": "ada4d473f82b01649e66c82a13e7732a257247d032cd9d7ca8d5be03a7cb3afa",
        },
    ),
)


def _insert_existing_exact_values(
    connection: sqlite3.Connection,
    table: str,
    values: dict[str, object],
) -> None:
    observed_fields = tuple(
        row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')
    )
    assert tuple(values) == observed_fields
    connection.execute(
        f'INSERT INTO "{table}" ({",".join(values)}) VALUES ({",".join("?" for _ in values)})',
        tuple(values.values()),
    )


def _insert_exact_c2b3d_parent_rows(
    connection: sqlite3.Connection,
    *,
    omit_table: str | None = None,
) -> None:
    postimages = _section_39_vector()["persisted_postimages"]
    c2b3d_rows = (
        ("development_semantic_attempts", postimages["semantic_attempt"]),
        ("development_attempt_fences", postimages["attempt_fence"]),
        ("development_effect_intents", postimages["author_effect_intent"]),
        ("development_effect_fences", postimages["author_effect_fence"]),
        ("development_author_commands", postimages["author_command"]),
        ("development_authority_evaluations", postimages["authority_evaluation"]),
        ("development_delivery_attempts", postimages["initial_delivery_attempt"]),
    )
    connection.execute("BEGIN")
    try:
        for table, values in (*_EXACT_C2B3A_PARENT_ROWS, *c2b3d_rows):
            if table != omit_table:
                _insert_existing_exact_values(connection, table, values)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise


def _insert_sqlite_proposal_prerequisites(
    connection: sqlite3.Connection,
    suffix: str,
) -> str:
    global _SQLITE_PREREQUISITE_TEMPLATES
    if _SQLITE_PREREQUISITE_TEMPLATES is None:
        family = _build_repaired_physical_family(False)
        _SQLITE_PREREQUISITE_TEMPLATES = {
            member["role"]: deepcopy(member)
            for member in family["physical_rows"]
            if member["role"] in (
                "source_invocation",
                "planning_context",
                "private_artifact_binding",
                "model_proposal",
                "pre_execution_plan_projection",
            )
        }
    members = deepcopy(_SQLITE_PREREQUISITE_TEMPLATES)
    source = members["source_invocation"]["values"]
    context = members["planning_context"]["values"]
    artifact = members["private_artifact_binding"]["values"]
    proposal = members["model_proposal"]["values"]
    projection = members["pre_execution_plan_projection"]["values"]
    source_ref = f"source.{suffix}"
    context_ref = f"context.{suffix}"
    artifact_ref = f"artifact.{suffix}"
    proposal_ref = f"proposal.{suffix}"
    context["planning_context_ref"] = context_ref
    context["planning_context_digest"] = _repaired_row_digest(REPAIRED_TABLE_ORDER[1], context)
    artifact["artifact_ref"] = artifact_ref
    artifact["artifact_binding_digest"] = _repaired_row_digest(REPAIRED_TABLE_ORDER[2], artifact)
    source.update(
        {
            "source_invocation_ref": source_ref,
            "context_ref": context_ref,
            "context_digest": context["planning_context_digest"],
            "artifact_ref": artifact_ref,
        }
    )
    source["source_invocation_digest"] = _repaired_row_digest(REPAIRED_TABLE_ORDER[0], source)
    proposal.update(
        {
            "proposal_ref": proposal_ref,
            "source_invocation_ref": source_ref,
            "source_invocation_digest": source["source_invocation_digest"],
            "context_ref": context_ref,
            "context_digest": context["planning_context_digest"],
            "artifact_ref": artifact_ref,
            "artifact_digest": artifact["artifact_digest"],
        }
    )
    proposal["proposal_digest"] = _repaired_row_digest(REPAIRED_TABLE_ORDER[3], proposal)
    projection.update(
        {
            "proposal_ref": proposal_ref,
            "artifact_ref": artifact_ref,
            "planning_context_ref": context_ref,
            "planning_context_digest": context["planning_context_digest"],
        }
    )
    projection["safe_projection_digest"] = _repaired_row_digest(REPAIRED_TABLE_ORDER[4], projection)
    for table, values in (
        (REPAIRED_TABLE_ORDER[0], source),
        (REPAIRED_TABLE_ORDER[1], context),
        (REPAIRED_TABLE_ORDER[2], artifact),
        (REPAIRED_TABLE_ORDER[3], proposal),
        (REPAIRED_TABLE_ORDER[4], projection),
    ):
        _insert_exact_repaired_values(connection, table, values)
    return proposal_ref


def _insert_sqlite_disposition(
    connection: sqlite3.Connection,
    *,
    lineage: tuple[object, ...],
    proposal_ref: str,
    disposition_ref: str,
    supersedes_ref: str | None,
    prior_revision: int,
    prior_digest: str | None,
    resulting_revision: int,
    selection_head_postimage_digest: str,
) -> dict[str, str]:
    global _SQLITE_DISPOSITION_TEMPLATE
    if _SQLITE_DISPOSITION_TEMPLATE is None:
        _SQLITE_DISPOSITION_TEMPLATE = deepcopy(
            next(
                member["values"]
                for member in _build_repaired_physical_family(False)["physical_rows"]
                if member["role"] == "coordinator_disposition"
            )
        )
    values = deepcopy(_SQLITE_DISPOSITION_TEMPLATE)
    values.update(dict(zip(REPAIRED_LINEAGE_COLUMNS, lineage, strict=True)))
    values.update(
        {
            "proposal_ref": proposal_ref,
            "disposition_ref": disposition_ref,
            "supersedes_disposition_ref": supersedes_ref,
            "expected_selection_head_revision": None if resulting_revision == 0 else prior_revision,
            "expected_selection_head_digest": None if resulting_revision == 0 else prior_digest,
            "prior_selection_head_revision": prior_revision,
            "prior_selection_head_digest": prior_digest,
            "resulting_selection_head_revision": resulting_revision,
            "selection_head_postimage_digest": selection_head_postimage_digest,
        }
    )
    values["disposition_digest"] = _repaired_row_digest(REPAIRED_TABLE_ORDER[6], values)
    _insert_exact_repaired_values(connection, REPAIRED_TABLE_ORDER[6], values)
    return {
        "disposition_digest": values["disposition_digest"],
        "selection_head_postimage_digest": values["selection_head_postimage_digest"],
    }


def _insert_exact_repaired_values(
    connection: sqlite3.Connection,
    table: str,
    values: dict[str, object],
) -> None:
    assert tuple(values) == tuple(name for name, _kind in REPAIRED_TABLE_COLUMNS[table])
    columns = tuple(values)
    connection.execute(
        f'INSERT INTO "{table}" ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})',
        tuple(values.values()),
    )


def _insert_sqlite_golden_family(
    connection: sqlite3.Connection,
    readiness_present: bool,
) -> dict[str, object]:
    family = _build_repaired_physical_family(readiness_present)
    _validate_repaired_physical_family(family)
    for member in family["physical_rows"]:
        _insert_exact_repaired_values(connection, member["table"], member["values"])
    rows_by_role = {row["role"]: row for row in family["physical_rows"]}
    proposal_values = rows_by_role["model_proposal"]["values"]
    disposition_values = rows_by_role["coordinator_disposition"]["values"]
    lineage = tuple(disposition_values[field] for field in REPAIRED_LINEAGE_COLUMNS)
    return {
        "lineage": lineage,
        "proposal_ref": proposal_values["proposal_ref"],
        "disposition_ref": disposition_values["disposition_ref"],
        "disposition_digest": disposition_values["disposition_digest"],
        "selection_head_postimage_digest": disposition_values["selection_head_postimage_digest"],
    }


def _build_repaired_common_phase_rows(
    source_phase: str,
    artifact_phase: str,
    proposal_phase: str,
    *,
    post_evidence_count: int = 0,
) -> tuple[dict[str, object], ...]:
    phases = (source_phase, artifact_phase, proposal_phase)
    assert all(phase in REPAIRED_PHASE_ALGEBRA for phase in phases)
    assert 0 <= post_evidence_count <= len(REPAIRED_POST_EXECUTION_EVIDENCE_SPECS)
    family = _build_repaired_physical_family(False)
    by_role = {member["role"]: member for member in family["physical_rows"]}
    source = deepcopy(by_role["source_invocation"]["values"])
    artifact = deepcopy(by_role["private_artifact_binding"]["values"])
    proposal = deepcopy(by_role["model_proposal"]["values"])
    suffix = ".".join(phase.split("_")[0] for phase in phases)
    source_contract = REPAIRED_PHASE_ALGEBRA[source_phase]
    artifact_contract = REPAIRED_PHASE_ALGEBRA[artifact_phase]
    proposal_contract = REPAIRED_PHASE_ALGEBRA[proposal_phase]
    source.update(
        {
            "source_invocation_ref": f"source.common.{suffix}",
            "proposal_phase": source_phase,
            "context_schema_id": source_contract["context_schema_id"],
            "context_ref": f"context.common.{suffix}",
            "context_digest": "a" * 64,
            "artifact_schema_id": source_contract["private_artifact_schema_id"],
            "artifact_ref": f"artifact.common.{suffix}",
            "artifact_digest": "b" * 64,
        }
    )
    source["source_invocation_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[0], source
    )
    artifact.update(
        {
            "artifact_ref": source["artifact_ref"],
            "proposal_phase": artifact_phase,
            "artifact_schema_id": artifact_contract["private_artifact_schema_id"],
            "artifact_digest": source["artifact_digest"],
            "safe_projection_schema_id": artifact_contract["safe_projection_schema_id"],
            "safe_projection_digest": "c" * 64,
        }
    )
    artifact["artifact_binding_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[2], artifact
    )
    evidence_set_ref = f"evidence-set.common.{suffix}"
    evidence_rows: list[dict[str, object]] = []
    if proposal_phase == "post_execution_semantic_review":
        evidence_specs = REPAIRED_POST_EXECUTION_EVIDENCE_SPECS[:post_evidence_count]
    else:
        evidence_specs = ()
    evidence_template = deepcopy(by_role["evidence.standing_policy"]["values"])
    for role, rank, required in evidence_specs:
        values = deepcopy(evidence_template)
        values.update(
            {
                "proposal_ref": f"proposal.common.{suffix}",
                "proposal_phase": proposal_phase,
                "evidence_set_ref": evidence_set_ref,
                "evidence_role": role,
                "role_rank": rank,
                "ordinal": 0,
                "evidence_ref": f"evidence.{role.replace('_', '.')}.{suffix}",
                "evidence_digest": f"{rank:064x}",
                "required_for_selection": int(required),
            }
        )
        values["evidence_binding_digest"] = _repaired_row_digest(
            REPAIRED_TABLE_ORDER[5], values
        )
        evidence_rows.append(
            {
                "table": REPAIRED_TABLE_ORDER[5],
                "role": f"evidence.{role}",
                "rank": rank,
                "ordinal": 0,
                "values": values,
            }
        )
    evidence_set_digest = _s41_digest(
        DIGEST_DOMAINS["evidence_set"],
        {
            "evidence_set_ref": evidence_set_ref,
            "proposal_ref": f"proposal.common.{suffix}",
            "proposal_phase": proposal_phase,
            "entries": tuple(
                {
                    "evidence_role": row["values"]["evidence_role"],
                    "role_rank": row["values"]["role_rank"],
                    "ordinal": row["values"]["ordinal"],
                    "evidence_ref": row["values"]["evidence_ref"],
                    "evidence_digest": row["values"]["evidence_digest"],
                    "evidence_binding_digest": row["values"]["evidence_binding_digest"],
                }
                for row in evidence_rows
            ),
        },
    )
    proposal.update(
        {
            "proposal_ref": f"proposal.common.{suffix}",
            "proposal_phase": proposal_phase,
            "source_invocation_ref": source["source_invocation_ref"],
            "source_invocation_digest": source["source_invocation_digest"],
            "context_schema_id": proposal_contract["context_schema_id"],
            "context_ref": source["context_ref"],
            "context_digest": source["context_digest"],
            "artifact_schema_id": proposal_contract["private_artifact_schema_id"],
            "artifact_ref": artifact["artifact_ref"],
            "artifact_digest": artifact["artifact_digest"],
            "safe_projection_schema_id": proposal_contract["safe_projection_schema_id"],
            "safe_projection_digest": artifact["safe_projection_digest"],
            "recommendation": proposal_contract["recommendations"][0],
            "evidence_set_ref": evidence_set_ref,
            "evidence_set_digest": evidence_set_digest,
        }
    )
    proposal["proposal_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[3], proposal
    )
    return (
        {
            "table": REPAIRED_TABLE_ORDER[0],
            "role": "source_invocation",
            "rank": 0,
            "ordinal": 0,
            "values": source,
        },
        {
            "table": REPAIRED_TABLE_ORDER[2],
            "role": "private_artifact_binding",
            "rank": 2,
            "ordinal": 0,
            "values": artifact,
        },
        {
            "table": REPAIRED_TABLE_ORDER[3],
            "role": "model_proposal",
            "rank": 3,
            "ordinal": 0,
            "values": proposal,
        },
        *evidence_rows,
    )


def _validate_repaired_common_physical_rows(
    rows: object,
) -> dict[str, object]:
    if type(rows) is not tuple or len(rows) < 3:
        _s41_violate("phase_algebra_mismatch")
    checked: list[dict[str, object]] = []
    for row in rows:
        row = _s41_require_exact_mapping(
            row,
            REPAIRED_ROW_FIELDS,
            "phase_algebra_mismatch",
        )
        if (
            type(row["table"]) is not str
            or row["table"] not in REPAIRED_TABLE_COLUMNS
            or type(row["role"]) is not str
            or type(row["ordinal"]) is not int
            or row["ordinal"] != 0
            or (row["rank"] is not None and type(row["rank"]) is not int)
        ):
            _s41_violate("phase_algebra_mismatch")
        columns = REPAIRED_TABLE_COLUMNS[row["table"]]
        values = _s41_require_exact_mapping(
            row["values"],
            tuple(name for name, _kind in columns),
            "phase_algebra_mismatch",
        )
        if any(
            not _repaired_value_matches_kind(values[field], kind)
            for field, kind in columns
        ):
            _s41_violate("phase_algebra_mismatch")
        digest_field, _domain = REPAIRED_TABLE_DIGESTS[row["table"]]
        if not _s41_exact_equal(
            values[digest_field],
            _repaired_row_digest(row["table"], values),
        ):
            _s41_violate("phase_algebra_mismatch")
        checked.append(row)
    expected_prefix = (
        "source_invocation",
        "private_artifact_binding",
        "model_proposal",
    )
    if not _s41_exact_equal(
        tuple(row["role"] for row in checked[:3]),
        expected_prefix,
    ) or any(not row["role"].startswith("evidence.") for row in checked[3:]):
        _s41_violate("phase_algebra_mismatch")
    by_role = {row["role"]: row for row in checked}
    if len(by_role) != len(checked):
        _s41_violate("phase_algebra_mismatch")
    contract = _validate_repaired_common_phase_algebra(
        by_role["source_invocation"]["values"],
        by_role["private_artifact_binding"]["values"],
        by_role["model_proposal"]["values"],
    )
    source = by_role["source_invocation"]["values"]
    artifact = by_role["private_artifact_binding"]["values"]
    proposal = by_role["model_proposal"]["values"]
    common_relations = (
        (source["proposal_phase"], artifact["proposal_phase"]),
        (source["proposal_phase"], proposal["proposal_phase"]),
        (source["model_contract_ref"], proposal["model_contract_ref"]),
        (source["model_contract_digest"], proposal["model_contract_digest"]),
        (source["model_configuration_ref"], proposal["model_configuration_ref"]),
        (source["model_configuration_digest"], proposal["model_configuration_digest"]),
        (source["context_schema_id"], proposal["context_schema_id"]),
        (source["context_ref"], proposal["context_ref"]),
        (source["context_digest"], proposal["context_digest"]),
        (source["artifact_schema_id"], artifact["artifact_schema_id"]),
        (source["artifact_schema_id"], proposal["artifact_schema_id"]),
        (source["artifact_ref"], artifact["artifact_ref"]),
        (source["artifact_ref"], proposal["artifact_ref"]),
        (source["artifact_digest"], artifact["artifact_digest"]),
        (source["artifact_digest"], proposal["artifact_digest"]),
        (artifact["safe_projection_schema_id"], proposal["safe_projection_schema_id"]),
        (artifact["safe_projection_digest"], proposal["safe_projection_digest"]),
        (source["source_invocation_ref"], proposal["source_invocation_ref"]),
        (source["source_invocation_digest"], proposal["source_invocation_digest"]),
    )
    if any(not _s41_exact_equal(left, right) for left, right in common_relations):
        _s41_violate("phase_algebra_mismatch")
    evidence_rows = tuple(row["values"] for row in checked[3:])
    if any(
        not (
            _s41_exact_equal(row["proposal_ref"], proposal["proposal_ref"])
            and _s41_exact_equal(row["proposal_phase"], proposal["proposal_phase"])
            and _s41_exact_equal(row["evidence_set_ref"], proposal["evidence_set_ref"])
        )
        for row in evidence_rows
    ):
        _s41_violate("phase_algebra_mismatch")
    evidence_set_identity = {
        "evidence_set_ref": proposal["evidence_set_ref"],
        "proposal_ref": proposal["proposal_ref"],
        "proposal_phase": proposal["proposal_phase"],
        "entries": tuple(
            {
                "evidence_role": row["evidence_role"],
                "role_rank": row["role_rank"],
                "ordinal": row["ordinal"],
                "evidence_ref": row["evidence_ref"],
                "evidence_digest": row["evidence_digest"],
                "evidence_binding_digest": row["evidence_binding_digest"],
            }
            for row in evidence_rows
        ),
    }
    if proposal["evidence_set_digest"] != _s41_digest(
        DIGEST_DOMAINS["evidence_set"],
        evidence_set_identity,
    ):
        _s41_violate("phase_algebra_mismatch")
    if by_role["source_invocation"]["values"]["proposal_phase"] == (
        "post_execution_semantic_review"
    ):
        _validate_repaired_phase_algebra(
            by_role,
            readiness_present=False,
        )
    return contract


REPAIRED_POST_EVIDENCE_PROPOSAL_QUERY = (
    "SELECT proposal_phase,evidence_set_ref,evidence_set_digest "
    "FROM development_model_proposals WHERE proposal_ref=? LIMIT 2"
)
REPAIRED_POST_EVIDENCE_ROWS_QUERY = (
    "SELECT schema_id,proposal_ref,proposal_phase,evidence_set_ref,evidence_role,"
    "role_rank,ordinal,evidence_ref,evidence_digest,required_for_selection,"
    "evidence_bound_at,evidence_binding_digest "
    "FROM development_model_proposal_evidence_bindings WHERE proposal_ref=? "
    "ORDER BY role_rank,ordinal,evidence_role,evidence_ref LIMIT 10"
)
REPAIRED_POST_EVIDENCE_TRANSACTION_QUERIES = (
    REPAIRED_POST_EVIDENCE_PROPOSAL_QUERY,
    REPAIRED_POST_EVIDENCE_ROWS_QUERY,
)


def _validate_post_evidence_transaction_gate(
    connection: sqlite3.Connection,
    proposal_ref: object,
    *,
    expected_written_evidence_count: object | None,
) -> None:
    _s41_require_safe_ref(proposal_ref, "phase_algebra_mismatch")
    if expected_written_evidence_count is not None and not (
        type(expected_written_evidence_count) is int
        and 0 <= expected_written_evidence_count <= 9
    ):
        _s41_violate("phase_algebra_mismatch")
    try:
        proposal_rows = connection.execute(
            REPAIRED_POST_EVIDENCE_PROPOSAL_QUERY,
            (proposal_ref,),
        ).fetchmany(2)
        evidence_tuples = connection.execute(
            REPAIRED_POST_EVIDENCE_ROWS_QUERY,
            (proposal_ref,),
        ).fetchmany(10)
    except sqlite3.Error:
        _s41_violate("phase_algebra_mismatch")
    if (
        len(proposal_rows) != 1
        or type(proposal_rows[0]) is not tuple
        or len(proposal_rows[0]) != 3
    ):
        _s41_violate("phase_algebra_mismatch")
    proposal_phase, evidence_set_ref, evidence_set_digest = proposal_rows[0]
    if not (
        type(proposal_phase) is str
        and type(evidence_set_ref) is str
        and type(evidence_set_digest) is str
        and proposal_phase == "post_execution_semantic_review"
        and _repaired_value_matches_kind(evidence_set_ref, "safe_ref")
        and _repaired_value_matches_kind(evidence_set_digest, "sha256")
    ):
        _s41_violate("phase_algebra_mismatch")
    if len(evidence_tuples) > 9 or (
        expected_written_evidence_count is not None
        and len(evidence_tuples) != expected_written_evidence_count
    ):
        _s41_violate("phase_algebra_mismatch")
    evidence_fields = tuple(
        name for name, _kind in REPAIRED_TABLE_COLUMNS[REPAIRED_TABLE_ORDER[5]]
    )
    evidence_rows: list[dict[str, object]] = []
    for row in evidence_tuples:
        if type(row) is not tuple or len(row) != len(evidence_fields):
            _s41_violate("phase_algebra_mismatch")
        values = dict(zip(evidence_fields, row, strict=True))
        if any(
            not _repaired_value_matches_kind(values[field], kind)
            for field, kind in REPAIRED_TABLE_COLUMNS[REPAIRED_TABLE_ORDER[5]]
        ) or values["evidence_binding_digest"] != _repaired_row_digest(
            REPAIRED_TABLE_ORDER[5],
            values,
        ):
            _s41_violate("phase_algebra_mismatch")
        evidence_rows.append(values)
    observed_specs = tuple(
        (
            row["evidence_role"],
            row["role_rank"],
            row["ordinal"],
            row["required_for_selection"],
        )
        for row in evidence_rows
    )
    complete_specs = tuple(
        (role, rank, 0, int(required))
        for role, rank, required in REPAIRED_POST_EXECUTION_EVIDENCE_SPECS
    )
    if evidence_rows and not _s41_exact_equal(observed_specs, complete_specs):
        _s41_violate("phase_algebra_mismatch")
    if any(
        not (
            row["proposal_ref"] == proposal_ref
            and row["proposal_phase"] == proposal_phase
            and row["evidence_set_ref"] == evidence_set_ref
        )
        for row in evidence_rows
    ):
        _s41_violate("phase_algebra_mismatch")
    evidence_set_identity = {
        "evidence_set_ref": evidence_set_ref,
        "proposal_ref": proposal_ref,
        "proposal_phase": proposal_phase,
        "entries": tuple(
            {
                "evidence_role": row["evidence_role"],
                "role_rank": row["role_rank"],
                "ordinal": row["ordinal"],
                "evidence_ref": row["evidence_ref"],
                "evidence_digest": row["evidence_digest"],
                "evidence_binding_digest": row["evidence_binding_digest"],
            }
            for row in evidence_rows
        ),
    }
    if evidence_set_digest != _s41_digest(
        DIGEST_DOMAINS["evidence_set"],
        evidence_set_identity,
    ):
        _s41_violate("phase_algebra_mismatch")


def _sqlite_post_evidence_set_is_zero_or_complete(
    connection: sqlite3.Connection,
    proposal_ref: str,
) -> bool:
    try:
        _validate_post_evidence_transaction_gate(
            connection,
            proposal_ref,
            expected_written_evidence_count=None,
        )
    except _ContractViolation:
        return False
    return True


def _commit_post_common_rows_with_transaction_gate(
    connection: sqlite3.Connection,
    rows: tuple[dict[str, object], ...],
    trace: list[str],
) -> None:
    if (
        type(rows) is not tuple
        or len(rows) < 3
        or type(trace) is not list
        or connection.in_transaction
    ):
        _s41_violate("phase_algebra_mismatch")
    proposal = rows[2]
    if (
        type(proposal) is not dict
        or any(type(key) is not str for key in proposal)
        or tuple(proposal) != REPAIRED_ROW_FIELDS
        or type(proposal["values"]) is not dict
        or any(type(key) is not str for key in proposal["values"])
        or "proposal_ref" not in proposal["values"]
    ):
        _s41_violate("phase_algebra_mismatch")
    proposal_ref = proposal["values"]["proposal_ref"]
    evidence_count = len(rows) - 3
    connection.execute("BEGIN IMMEDIATE")
    trace.append("begin_immediate")
    try:
        for row in rows:
            _insert_exact_repaired_values(
                connection,
                row["table"],
                row["values"],
            )
        trace.append("proposal_and_evidence_writes")
        _validate_post_evidence_transaction_gate(
            connection,
            proposal_ref,
            expected_written_evidence_count=evidence_count,
        )
        trace.append("post_evidence_gate")
        connection.commit()
        trace.append("commit")
    except (
        AssertionError,
        KeyError,
        TypeError,
        ValueError,
        sqlite3.Error,
        _ContractViolation,
    ):
        connection.rollback()
        trace.append("rollback")
        _s41_violate("phase_algebra_mismatch")


def _new_table_row_count(connection: sqlite3.Connection) -> int:
    return sum(
        connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        for table in REPAIRED_TABLE_ORDER
    )


def _observed_sqlite_foreign_keys(
    connection: sqlite3.Connection,
    table: str,
) -> tuple[tuple[tuple[str, ...], str, tuple[str, ...], str, str, str], ...]:
    grouped: dict[int, list[tuple[object, ...]]] = {}
    for row in connection.execute(f'PRAGMA foreign_key_list("{table}")'):
        grouped.setdefault(row[0], []).append(row)
    return tuple(
        (
            tuple(item[3] for item in sorted(rows, key=lambda item: item[1])),
            rows[0][2],
            tuple(item[4] for item in sorted(rows, key=lambda item: item[1])),
            rows[0][5],
            rows[0][6],
            rows[0][7],
        )
        for _foreign_key_id, rows in sorted(grouped.items())
    )


def _declared_unique_column_sets(
    connection: sqlite3.Connection,
    table: str,
) -> set[tuple[str, ...]]:
    table_info = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
    primary_key = tuple(
        row[1] for row in sorted(table_info, key=lambda row: row[5]) if row[5] > 0
    )
    result = {primary_key} if primary_key else set()
    for index in connection.execute(f'PRAGMA index_list("{table}")'):
        if index[2] == 1 and index[4] == 0:
            result.add(
                tuple(
                    row[2]
                    for row in connection.execute(
                        f'PRAGMA index_info({json.dumps(index[1])})'
                    )
                )
            )
    return result


def test_f1_generated_foreign_keys_exactly_equal_the_complete_contract_inventory() -> None:
    owner = _parse_repaired_owner()["migration_0003_contract"]
    assert owner["inherited_foreign_key_inventory_source"] == (
        "the exact ordered repaired base foreign-key inventory derived from the "
        "opening contracts with phase-bearing replacements and a strengthened "
        "receipt-disposition relation; 43 base relation slots remain"
    )
    assert owner["common_model_proposal_context_binding"] == (
        "context_ref is a phase-specific safe identity binding; the common proposal "
        "supports pre_execution_plan and post_execution_semantic_review and is not "
        "globally constrained to the pre-execution context table"
    )
    assert (
        owner["unconditional_common_proposal_preexecution_context_foreign_key_present"]
        is False
    )
    assert owner["phase_and_receipt_binding_foreign_keys"] == (
        (
            REPAIRED_TABLE_ORDER[3],
            *REPAIRED_BASE_FOREIGN_KEYS[REPAIRED_TABLE_ORDER[3]][0][:3],
        ),
        (
            REPAIRED_TABLE_ORDER[3],
            *REPAIRED_BASE_FOREIGN_KEYS[REPAIRED_TABLE_ORDER[3]][1][:3],
        ),
        (
            REPAIRED_TABLE_ORDER[4],
            *REPAIRED_BASE_FOREIGN_KEYS[REPAIRED_TABLE_ORDER[4]][0][:3],
        ),
        (
            REPAIRED_TABLE_ORDER[4],
            *REPAIRED_BASE_FOREIGN_KEYS[REPAIRED_TABLE_ORDER[4]][1][:3],
        ),
        (
            REPAIRED_TABLE_ORDER[5],
            *REPAIRED_BASE_FOREIGN_KEYS[REPAIRED_TABLE_ORDER[5]][0][:3],
        ),
        (
            REPAIRED_TABLE_ORDER[6],
            *REPAIRED_BASE_FOREIGN_KEYS[REPAIRED_TABLE_ORDER[6]][0][:3],
        ),
        (
            REPAIRED_TABLE_ORDER[8],
            *REPAIRED_BASE_FOREIGN_KEYS[REPAIRED_TABLE_ORDER[8]][1][:3],
        ),
        (
            REPAIRED_TABLE_ORDER[8],
            *REPAIRED_BASE_FOREIGN_KEYS[REPAIRED_TABLE_ORDER[8]][2][:3],
        ),
    )
    assert owner["supplemental_strengthening_foreign_keys"] == tuple(
        (table, *specification)
        for table in REPAIRED_TABLE_ORDER
        for specification in INCORPORATED_NINE_FINDING_SUPPLEMENTAL_FOREIGN_KEYS.get(
            table,
            (),
        )
    )
    assert owner["foreign_key_count_by_table"] == tuple(
        (table, len(REPAIRED_TABLE_FOREIGN_KEYS[table]))
        for table in REPAIRED_TABLE_ORDER
    )
    assert owner["foreign_key_total"] == 45
    assert owner["generated_foreign_keys_equal_complete_contract_inventory"] is True
    assert owner["every_foreign_key_parent_columns_are_declared_primary_or_unique"] is True
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        observed_total = 0
        expected_total = 0
        for table in REPAIRED_TABLE_ORDER:
            expected = tuple(
                (
                    child_columns,
                    parent_table,
                    parent_columns,
                    "RESTRICT",
                    "RESTRICT",
                    "NONE",
                )
                for child_columns, parent_table, parent_columns, timing
                in REPAIRED_TABLE_FOREIGN_KEYS[table]
                if timing == "IMMEDIATE"
            )
            observed = _observed_sqlite_foreign_keys(connection, table)
            assert len(observed) == len(set(observed))
            assert set(observed) == set(expected)
            assert len(observed) == len(expected)
            observed_total += len(observed)
            expected_total += len(expected)
            for _child, parent_table, parent_columns, _update, _delete, _match in observed:
                assert parent_columns in _declared_unique_column_sets(
                    connection,
                    parent_table,
                )
            schema_sql = connection.execute(
                "SELECT sql FROM sqlite_schema WHERE type='table' AND name=?",
                (table,),
            ).fetchone()[0]
            assert schema_sql.count("NOT DEFERRABLE INITIALLY IMMEDIATE") == len(expected)
        assert expected_total == observed_total == 45
        assert tuple(
            (table, len(REPAIRED_TABLE_FOREIGN_KEYS[table]))
            for table in REPAIRED_TABLE_ORDER
        ) == (
            (REPAIRED_TABLE_ORDER[0], 0),
            (REPAIRED_TABLE_ORDER[1], 11),
            (REPAIRED_TABLE_ORDER[2], 0),
            (REPAIRED_TABLE_ORDER[3], 2),
            (REPAIRED_TABLE_ORDER[4], 3),
            (REPAIRED_TABLE_ORDER[5], 1),
            (REPAIRED_TABLE_ORDER[6], 13),
            (REPAIRED_TABLE_ORDER[7], 12),
            (REPAIRED_TABLE_ORDER[8], 3),
        )
    finally:
        connection.close()


def test_f1_canonical_family_fails_when_migration_0002_parents_are_empty() -> None:
    connection, _inventory = _install_repaired_temporary_schema(
        seed_c2b3d_parents=False
    )
    try:
        parent_tables = {
            parent_table
            for table in REPAIRED_TABLE_ORDER
            for _child, parent_table, _columns, _timing
            in REPAIRED_TABLE_FOREIGN_KEYS[table]
            if parent_table not in REPAIRED_TABLE_ORDER
        }
        assert parent_tables
        assert all(
            connection.execute(f'SELECT count(*) FROM "{table}"').fetchone() == (0,)
            for table in parent_tables
        )
        with pytest.raises(sqlite3.IntegrityError) as caught:
            _insert_sqlite_golden_family(connection, False)
        assert caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_FOREIGNKEY"
    finally:
        connection.rollback()
        connection.close()


def _insert_two_repaired_generations_without_receipts(
    connection: sqlite3.Connection,
) -> tuple[dict[str, object], dict[str, object]]:
    root = _build_repaired_physical_family(False)
    successor = _build_repaired_successor_family(
        root,
        suffix="sqlite-foreign-existing.0001",
    )
    for member in root["physical_rows"]:
        if member["role"] != "receipt":
            _insert_exact_repaired_values(
                connection,
                member["table"],
                member["values"],
            )
    successor_head = next(
        member
        for member in successor["physical_rows"]
        if member["role"] == "selection_head_postimage"
    )
    for member in successor["physical_rows"]:
        if member["role"] not in ("selection_head_postimage", "receipt"):
            _insert_exact_repaired_values(
                connection,
                member["table"],
                member["values"],
            )
    assignments = tuple(
        field
        for field in successor_head["values"]
        if field not in REPAIRED_LINEAGE_COLUMNS
    )
    cursor = connection.execute(
        f'UPDATE "{REPAIRED_TABLE_ORDER[7]}" SET '
        + ",".join(f'"{field}"=?' for field in assignments)
        + " WHERE "
        + _LINEAGE_WHERE,
        (
            *(successor_head["values"][field] for field in assignments),
            *(
                successor_head["values"][field]
                for field in REPAIRED_LINEAGE_COLUMNS
            ),
        ),
    )
    assert cursor.rowcount == 1
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    return root, successor


@pytest.mark.parametrize(
    "field",
    (
        "proposal_ref",
        "disposition_ref",
        "selection_head_revision",
        "selection_head_digest",
    ),
)
def test_s41_audit_006_sqlite_receipt_rejects_foreign_existing_family_member(
    field: str,
) -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        root, successor = _insert_two_repaired_generations_without_receipts(connection)
        receipt = deepcopy(successor["receipt"]["values"])
        receipt[field] = root["receipt"]["values"][field]
        receipt["receipt_digest"] = _repaired_row_digest(
            REPAIRED_TABLE_ORDER[8],
            receipt,
        )
        with pytest.raises(sqlite3.IntegrityError) as caught:
            _insert_exact_repaired_values(
                connection,
                REPAIRED_TABLE_ORDER[8],
                receipt,
            )
        assert caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_FOREIGNKEY"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.rollback()
        connection.close()


def test_s41_audit_006_sqlite_receipt_composites_bind_program_effect_and_head() -> None:
    owner = _parse_repaired_owner()["migration_0003_contract"]
    receipt_foreign_keys = REPAIRED_BASE_FOREIGN_KEYS[REPAIRED_TABLE_ORDER[8]]
    assert receipt_foreign_keys[1][0] == (
        "program_ref",
        "disposition_ref",
        "proposal_ref",
        "effect_intent_ref",
        "selection_head_revision",
        "selection_head_digest",
    )
    assert receipt_foreign_keys[1][2] == owner["receipt_disposition_parent_key"]
    assert receipt_foreign_keys[2][0] == (
        "program_ref",
        "effect_intent_ref",
    )
    assert receipt_foreign_keys[2][2] == owner[
        "receipt_selection_head_lineage_parent_key"
    ]
    assert owner["receipt_historical_head_binding"] == (
        "receipt proposal, disposition, revision, and postimage digest bind through "
        "the immutable disposition; program and effect bind to the mutable selection-"
        "head lineage, so a later valid head CAS neither rewrites nor invalidates an "
        "immutable historical receipt"
    )
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        _root, successor = _insert_two_repaired_generations_without_receipts(connection)
        _insert_exact_repaired_values(
            connection,
            REPAIRED_TABLE_ORDER[8],
            successor["receipt"]["values"],
        )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.rollback()
        connection.close()


def test_f1_one_missing_exact_authority_parent_fails_its_inherited_foreign_key() -> None:
    connection, _inventory = _install_repaired_temporary_schema(
        seed_c2b3d_parents=False
    )
    try:
        omitted = "development_authority_evaluations"
        _insert_exact_c2b3d_parent_rows(connection, omit_table=omitted)
        assert connection.execute(f'SELECT count(*) FROM "{omitted}"').fetchone() == (0,)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        with pytest.raises(sqlite3.IntegrityError) as caught:
            _insert_sqlite_golden_family(connection, False)
        assert caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_FOREIGNKEY"
    finally:
        connection.rollback()
        connection.close()


def test_f1_post_execution_common_proposal_needs_no_preexecution_context_row() -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        family = _build_repaired_physical_family(False)
        by_role = {
            member["role"]: deepcopy(member["values"])
            for member in family["physical_rows"]
        }
        source = by_role["source_invocation"]
        artifact = by_role["private_artifact_binding"]
        proposal = by_role["model_proposal"]
        source.update(
            {
                "source_invocation_ref": "source.post-execution.0001",
                "proposal_phase": "post_execution_semantic_review",
                "context_schema_id": SCHEMA_IDS["post_execution_context"],
                "context_ref": "context.post-execution.0001",
                "context_digest": "a" * 64,
                "artifact_schema_id": SCHEMA_IDS["post_execution_artifact"],
                "artifact_ref": "artifact.post-execution.0001",
                "artifact_digest": "b" * 64,
            }
        )
        source["source_invocation_digest"] = _repaired_row_digest(
            REPAIRED_TABLE_ORDER[0], source
        )
        artifact.update(
            {
                "artifact_ref": source["artifact_ref"],
                "proposal_phase": "post_execution_semantic_review",
                "artifact_schema_id": SCHEMA_IDS["post_execution_artifact"],
                "artifact_digest": source["artifact_digest"],
                "safe_projection_schema_id": SCHEMA_IDS["post_execution_projection"],
                "safe_projection_digest": "c" * 64,
            }
        )
        artifact["artifact_binding_digest"] = _repaired_row_digest(
            REPAIRED_TABLE_ORDER[2], artifact
        )
        proposal.update(
            {
                "proposal_ref": "proposal.post-execution.0001",
                "proposal_phase": "post_execution_semantic_review",
                "source_invocation_ref": source["source_invocation_ref"],
                "source_invocation_digest": source["source_invocation_digest"],
                "context_schema_id": source["context_schema_id"],
                "context_ref": source["context_ref"],
                "context_digest": source["context_digest"],
                "artifact_schema_id": artifact["artifact_schema_id"],
                "artifact_ref": artifact["artifact_ref"],
                "artifact_digest": artifact["artifact_digest"],
                "safe_projection_schema_id": artifact["safe_projection_schema_id"],
                "safe_projection_digest": artifact["safe_projection_digest"],
                "recommendation": "accept_candidate",
                "evidence_set_ref": "evidence-set.post-execution.0001",
                "evidence_set_digest": "d" * 64,
            }
        )
        proposal["proposal_digest"] = _repaired_row_digest(
            REPAIRED_TABLE_ORDER[3], proposal
        )
        assert _validate_repaired_common_phase_algebra(
            source,
            artifact,
            proposal,
        ) is REPAIRED_PHASE_ALGEBRA["post_execution_semantic_review"]
        assert connection.execute(
            "SELECT count(*) FROM development_pre_execution_planning_contexts"
        ).fetchone() == (0,)
        for table, values in (
            (REPAIRED_TABLE_ORDER[0], source),
            (REPAIRED_TABLE_ORDER[2], artifact),
            (REPAIRED_TABLE_ORDER[3], proposal),
        ):
            _insert_exact_repaired_values(connection, table, values)
        assert connection.execute(
            "SELECT count(*) FROM development_model_proposals WHERE proposal_ref=?",
            (proposal["proposal_ref"],),
        ).fetchone() == (1,)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.rollback()
        connection.close()


def test_s41_corr_001_phase_algebra_owner_and_generated_checks_are_exact() -> None:
    owner = _parse_repaired_owner()["phase_algebra"]
    assert owner == REPAIRED_PHASE_ALGEBRA
    assert tuple(owner) == PHASES
    assert owner["pre_execution_plan"]["row_presence"] == tuple(
        (table, "required") for table in REPAIRED_TABLE_ORDER
    )
    assert owner["post_execution_semantic_review"]["row_presence"] == (
        (REPAIRED_TABLE_ORDER[0], "required"),
        (REPAIRED_TABLE_ORDER[1], "forbidden"),
        (REPAIRED_TABLE_ORDER[2], "required"),
        (REPAIRED_TABLE_ORDER[3], "required"),
        (REPAIRED_TABLE_ORDER[4], "forbidden"),
        (REPAIRED_TABLE_ORDER[5], "optional"),
        (REPAIRED_TABLE_ORDER[6], "forbidden"),
        (REPAIRED_TABLE_ORDER[7], "forbidden"),
        (REPAIRED_TABLE_ORDER[8], "forbidden"),
    )
    assert owner["post_execution_semantic_review"]["evidence_roles"] == (
        REPAIRED_POST_EXECUTION_EVIDENCE_SPECS
    )
    assert (
        owner["post_execution_semantic_review"]["evidence_set_rule"]
        == "zero_or_complete"
    )
    constrained_tables = tuple(
        table
        for table in REPAIRED_TABLE_ORDER
        if _sqlite_phase_algebra_constraint(table) is not None
    )
    assert constrained_tables == (
        REPAIRED_TABLE_ORDER[0],
        REPAIRED_TABLE_ORDER[2],
        REPAIRED_TABLE_ORDER[3],
        REPAIRED_TABLE_ORDER[5],
    )
    for table in constrained_tables:
        assert (
            f"CONSTRAINT {table}_phase_algebra CHECK("
            in REPAIRED_TABLE_DDL
        )


def test_s41_corr_001_generated_ddl_rejects_cross_phase_common_row() -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        family = _build_repaired_physical_family(False)
        source = deepcopy(family["physical_rows"][0]["values"])
        source["context_schema_id"] = SCHEMA_IDS["post_execution_context"]
        source["source_invocation_digest"] = _repaired_row_digest(
            REPAIRED_TABLE_ORDER[0], source
        )
        with pytest.raises(sqlite3.IntegrityError) as caught:
            _insert_exact_repaired_values(
                connection,
                REPAIRED_TABLE_ORDER[0],
                source,
            )
        assert caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_CHECK"
        assert str(caught.value) == (
            "CHECK constraint failed: "
            "development_model_source_invocations_phase_algebra"
        )
    finally:
        connection.rollback()
        connection.close()


@pytest.mark.parametrize(
    "source_phase,artifact_phase,proposal_phase",
    tuple(
        (source_phase, artifact_phase, proposal_phase)
        for source_phase in PHASES
        for artifact_phase in PHASES
        for proposal_phase in PHASES
    ),
)
def test_s41_audit_001_all_phase_triples_have_pure_physical_and_sqlite_parity(
    source_phase: str,
    artifact_phase: str,
    proposal_phase: str,
) -> None:
    rows = _build_repaired_common_phase_rows(
        source_phase,
        artifact_phase,
        proposal_phase,
    )
    source, artifact, proposal = (row["values"] for row in rows[:3])
    coherent = source_phase == artifact_phase == proposal_phase
    if coherent:
        assert _validate_repaired_common_phase_algebra(
            source,
            artifact,
            proposal,
        ) is REPAIRED_PHASE_ALGEBRA[source_phase]
        assert _validate_repaired_common_physical_rows(rows) is (
            REPAIRED_PHASE_ALGEBRA[source_phase]
        )
    else:
        with pytest.raises(_ContractViolation) as pure_caught:
            _validate_repaired_common_phase_algebra(source, artifact, proposal)
        assert pure_caught.value.reason == "phase_algebra_mismatch"
        with pytest.raises(_ContractViolation) as physical_caught:
            _validate_repaired_common_physical_rows(rows)
        assert physical_caught.value.reason == "phase_algebra_mismatch"

    connection, _inventory = _install_repaired_temporary_schema()
    try:
        if coherent:
            for row in rows:
                _insert_exact_repaired_values(
                    connection,
                    row["table"],
                    row["values"],
                )
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        else:
            for row in rows[:2]:
                _insert_exact_repaired_values(
                    connection,
                    row["table"],
                    row["values"],
                )
            with pytest.raises(sqlite3.IntegrityError) as sqlite_caught:
                _insert_exact_repaired_values(
                    connection,
                    rows[2]["table"],
                    rows[2]["values"],
                )
            assert sqlite_caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_FOREIGNKEY"
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.rollback()
        connection.close()


@pytest.mark.parametrize(
    "evidence_count,accepted",
    tuple((count, count in (0, 9)) for count in range(10)),
    ids=tuple(f"count-{count}" for count in range(10)),
)
def test_s41_post_execution_evidence_is_exactly_zero_or_complete(
    evidence_count: int,
    accepted: bool,
) -> None:
    rows = _build_repaired_common_phase_rows(
        "post_execution_semantic_review",
        "post_execution_semantic_review",
        "post_execution_semantic_review",
        post_evidence_count=evidence_count,
    )
    if accepted:
        assert _validate_repaired_common_physical_rows(rows) is (
            REPAIRED_PHASE_ALGEBRA["post_execution_semantic_review"]
        )
    else:
        with pytest.raises(_ContractViolation) as caught:
            _validate_repaired_common_physical_rows(rows)
        assert caught.value.reason == "phase_algebra_mismatch"

    connection, _inventory = _install_repaired_temporary_schema()
    try:
        for row in rows:
            _insert_exact_repaired_values(
                connection,
                row["table"],
                row["values"],
            )
        proposal_ref = rows[2]["values"]["proposal_ref"]
        assert _sqlite_post_evidence_set_is_zero_or_complete(
            connection,
            proposal_ref,
        ) is accepted
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.rollback()
        connection.close()

    transaction_connection, _inventory = _install_repaired_temporary_schema()
    transaction_connection.commit()
    trace: list[str] = []
    try:
        if accepted:
            _commit_post_common_rows_with_transaction_gate(
                transaction_connection,
                rows,
                trace,
            )
            assert trace == [
                "begin_immediate",
                "proposal_and_evidence_writes",
                "post_evidence_gate",
                "commit",
            ]
            assert transaction_connection.execute(
                "SELECT count(*) FROM development_model_proposals WHERE proposal_ref=?",
                (rows[2]["values"]["proposal_ref"],),
            ).fetchone() == (1,)
        else:
            with pytest.raises(_ContractViolation) as transaction_caught:
                _commit_post_common_rows_with_transaction_gate(
                    transaction_connection,
                    rows,
                    trace,
                )
            assert transaction_caught.value.reason == "phase_algebra_mismatch"
            assert trace == [
                "begin_immediate",
                "proposal_and_evidence_writes",
                "rollback",
            ]
            assert transaction_connection.execute(
                "SELECT count(*) FROM development_model_proposals WHERE proposal_ref=?",
                (rows[2]["values"]["proposal_ref"],),
            ).fetchone() == (0,)
    finally:
        transaction_connection.close()


@pytest.mark.parametrize(
    "case_name",
    (
        "duplicate",
        "unknown-role",
        "wrong-rank",
        "wrong-ordinal",
        "wrong-required",
        "cross-phase",
        "wrong-proposal",
        "foreign-evidence-set",
        "wrong-row-digest",
    ),
)
def test_s41_post_execution_evidence_rejects_every_noncanonical_member(
    case_name: str,
) -> None:
    rows = list(
        _build_repaired_common_phase_rows(
            "post_execution_semantic_review",
            "post_execution_semantic_review",
            "post_execution_semantic_review",
            post_evidence_count=9,
        )
    )
    selected = deepcopy(rows[3])
    if case_name == "duplicate":
        rows.append(selected)
    elif case_name == "unknown-role":
        selected["role"] = "evidence.unknown"
        selected["values"]["evidence_role"] = "unknown"
        rows[3] = selected
    elif case_name == "wrong-rank":
        selected["rank"] = 14
        selected["values"]["role_rank"] = 14
        rows[3] = selected
    elif case_name == "wrong-ordinal":
        selected["ordinal"] = 1
        selected["values"]["ordinal"] = 1
        rows[3] = selected
    elif case_name == "wrong-required":
        selected["values"]["required_for_selection"] = 0
        rows[3] = selected
    elif case_name == "cross-phase":
        selected["values"]["proposal_phase"] = "pre_execution_plan"
        rows[3] = selected
    elif case_name == "wrong-proposal":
        selected["values"]["proposal_ref"] = "proposal.foreign.valid.0001"
        rows[3] = selected
    elif case_name == "foreign-evidence-set":
        selected["values"]["evidence_set_ref"] = "evidence-set.foreign.valid.0001"
        rows[3] = selected
    elif case_name == "wrong-row-digest":
        selected["values"]["evidence_binding_digest"] = "f" * 64
        rows[3] = selected
    else:
        raise AssertionError(case_name)
    if case_name != "wrong-row-digest":
        selected["values"]["evidence_binding_digest"] = _repaired_row_digest(
            REPAIRED_TABLE_ORDER[5],
            selected["values"],
        )
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_common_physical_rows(tuple(rows))
    assert caught.value.reason == "phase_algebra_mismatch"

    connection, _inventory = _install_repaired_temporary_schema()
    connection.commit()
    trace: list[str] = []
    try:
        with pytest.raises(_ContractViolation) as transaction_caught:
            _commit_post_common_rows_with_transaction_gate(
                connection,
                tuple(rows),
                trace,
            )
        assert transaction_caught.value.reason == "phase_algebra_mismatch"
        assert trace[-1] == "rollback"
        assert "commit" not in trace
        assert connection.execute(
            "SELECT count(*) FROM development_model_proposals WHERE proposal_ref=?",
            (rows[2]["values"]["proposal_ref"],),
        ).fetchone() == (0,)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()


@pytest.mark.parametrize(
    "value,accepted",
    (
        ("connector-secret", False),
        ("TUNNEL-secret", False),
        ("WoRkSpAcE-secret", False),
        ("org-secret", False),
        ("ORGANIZATION-secret", False),
        ("UsEr-secret", False),
        ("CoNnEcToR-secret", False),
        ("\x00safe-ref", False),
        ("safe\x00-ref", False),
        ("safe-ref\x00", False),
        ("safe-ref\x00hidden", False),
        ("safe-réf", False),
        ("ordinary-safe-ref.0001", True),
    ),
    ids=(
        "connector-lower",
        "tunnel-upper",
        "workspace-mixed",
        "org-lower",
        "organization-upper",
        "user-mixed",
        "connector-mixed-audit",
        "nul-beginning",
        "nul-middle",
        "nul-end",
        "nul-hidden-suffix",
        "non-ascii",
        "valid",
    ),
)
def test_s41_corr_002_safe_ref_pure_physical_ddl_and_recovery_parity(
    value: str,
    accepted: bool,
) -> None:
    family = _build_repaired_physical_family(False)
    by_role = {row["role"]: row for row in family["physical_rows"]}
    source = by_role["source_invocation"]["values"]
    proposal = by_role["model_proposal"]["values"]
    source["source_invocation_ref"] = value
    proposal["source_invocation_ref"] = value
    _redigest_repaired_physical_family(family)
    assert _repaired_value_matches_kind(value, "safe_ref") is accepted
    recovered = _recovery_exact_row(
        tuple(source.values()),
        REPAIRED_TABLE_ORDER[0],
    )
    assert (recovered is not None) is accepted
    if accepted:
        _validate_repaired_physical_family(family)
    else:
        with pytest.raises(_ContractViolation) as physical_caught:
            _validate_repaired_physical_family(family)
        assert physical_caught.value.reason == "physical_family_row_digest_mismatch"

    connection, _inventory = _install_repaired_temporary_schema()
    try:
        if accepted:
            _insert_exact_repaired_values(
                connection,
                REPAIRED_TABLE_ORDER[0],
                source,
            )
            assert connection.execute(
                f'SELECT count(*) FROM "{REPAIRED_TABLE_ORDER[0]}"'
            ).fetchone() == (1,)
        else:
            with pytest.raises(sqlite3.IntegrityError) as ddl_caught:
                _insert_exact_repaired_values(
                    connection,
                    REPAIRED_TABLE_ORDER[0],
                    source,
                )
            assert ddl_caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_CHECK"
    finally:
        connection.rollback()
        connection.close()


@pytest.mark.parametrize(
    "kind,value,accepted",
    (
        ("sha256", "a" * 64, True),
        ("sha256", "a" * 63, False),
        ("sha256", "a" * 64 + "\x00hidden", False),
        ("sha256", "a" * 63 + "g", False),
        ("sha1", "b" * 40, True),
        ("sha1", "b" * 40 + "\x00hidden", False),
        ("reason_code", "plan.valid_reason-1", True),
        ("reason_code", "1plan.invalid", False),
        ("reason_code", "plan.valid\x00hidden", False),
        ("proposal_phase", "pre_execution_plan", True),
        ("proposal_phase", "pre_execution_plan\x00hidden", False),
        ("phase_recommendation", "accept_candidate", True),
        ("phase_recommendation", "accept_candidate\x00hidden", False),
        ("literal:committed", "committed", True),
        ("literal:committed", "committed\x00hidden", False),
    ),
)
def test_s41_audit_002_byte_complete_ascii_scalar_parity(
    kind: str,
    value: str,
    accepted: bool,
) -> None:
    assert _repaired_value_matches_kind(value, kind) is accepted
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute(
            "CREATE TABLE scalar_probe (value ANY NOT NULL CHECK("
            + _sqlite_kind_check("value", kind)
            + ")) STRICT"
        )
        if accepted:
            connection.execute("INSERT INTO scalar_probe(value) VALUES (?)", (value,))
            assert connection.execute("SELECT value FROM scalar_probe").fetchone() == (
                value,
            )
        else:
            with pytest.raises(sqlite3.IntegrityError) as caught:
                connection.execute("INSERT INTO scalar_probe(value) VALUES (?)", (value,))
            assert caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_CHECK"
    finally:
        connection.close()


@pytest.mark.parametrize("blob_hex", ("80", "c328", "c080", "e228a1"))
def test_s41_audit_002_malformed_utf8_text_fails_generated_ascii_predicates(
    blob_hex: str,
) -> None:
    for kind in (
        "safe_ref",
        "sha256",
        "reason_code",
        "proposal_phase",
        "phase_recommendation",
        "literal:committed",
    ):
        connection = sqlite3.connect(":memory:")
        try:
            connection.execute(
                "CREATE TABLE scalar_probe (value ANY NOT NULL CHECK("
                + _sqlite_kind_check("value", kind)
                + ")) STRICT"
            )
            with pytest.raises(sqlite3.IntegrityError) as caught:
                connection.execute(
                    f"INSERT INTO scalar_probe(value) SELECT CAST(X'{blob_hex}' AS TEXT)"
                )
            assert caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_CHECK"
        finally:
            connection.close()


def test_s41_audit_002_every_selected_ascii_kind_uses_complete_stored_bytes() -> None:
    for kind in (
        "safe_ref",
        "nullable_safe_ref",
        "sha256",
        "nullable_sha256",
        "sha1",
        "utc_second",
        "canonical_effect_class_json",
        "reason_code",
        "proposal_phase",
        "phase_recommendation",
        "literal:committed",
    ):
        predicate = _sqlite_kind_check("value", kind)
        assert 'length(CAST("value" AS BLOB))=length("value")' in predicate


@pytest.mark.parametrize(
    "value,accepted",
    (
        ("2026-02-30T12:35:01Z", False),
        ("2023-02-29T12:35:01Z", False),
        ("2024-02-29T12:35:01Z", True),
        ("0001-01-01T00:00:00Z", True),
        ("9999-12-31T23:59:59Z", True),
        ("2026-02-28T12:35:60Z", False),
        ("2026-02-28T12:35:01+00:00", False),
        ("2026-02-28T12:35:01.000Z", False),
    ),
    ids=(
        "february-30",
        "invalid-nonleap-day",
        "valid-leap-day",
        "minimum-year",
        "maximum-year",
        "second-60",
        "timezone-offset",
        "fractional-second",
    ),
)
def test_s41_corr_002_utc_second_pure_physical_ddl_and_recovery_parity(
    value: str,
    accepted: bool,
) -> None:
    family = _build_repaired_physical_family(False)
    source = next(
        row["values"]
        for row in family["physical_rows"]
        if row["role"] == "source_invocation"
    )
    source["source_invocation_started_at"] = value
    _redigest_repaired_physical_family(family)
    assert _repaired_value_matches_kind(value, "utc_second") is accepted
    recovered = _recovery_exact_row(
        tuple(source.values()),
        REPAIRED_TABLE_ORDER[0],
    )
    assert (recovered is not None) is accepted
    if accepted:
        with pytest.raises(_ContractViolation) as chronology_caught:
            _validate_repaired_physical_family(family)
        assert chronology_caught.value.reason == "preselection_chronology_invalid"
    else:
        with pytest.raises(_ContractViolation) as physical_caught:
            _validate_repaired_physical_family(family)
        assert physical_caught.value.reason == "physical_family_row_digest_mismatch"

    connection, _inventory = _install_repaired_temporary_schema()
    try:
        if accepted:
            _insert_exact_repaired_values(
                connection,
                REPAIRED_TABLE_ORDER[0],
                source,
            )
            assert connection.execute(
                f'SELECT count(*) FROM "{REPAIRED_TABLE_ORDER[0]}"'
            ).fetchone() == (1,)
        else:
            with pytest.raises(sqlite3.IntegrityError) as ddl_caught:
                _insert_exact_repaired_values(
                    connection,
                    REPAIRED_TABLE_ORDER[0],
                    source,
                )
            assert ddl_caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_CHECK"
    finally:
        connection.rollback()
        connection.close()


def test_f1_preexecution_projection_still_requires_its_exact_context_parent() -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        family = _build_repaired_physical_family(False)
        by_role = {member["role"]: member for member in family["physical_rows"]}
        for role in (
            "source_invocation",
            "private_artifact_binding",
            "model_proposal",
        ):
            member = by_role[role]
            _insert_exact_repaired_values(connection, member["table"], member["values"])
        projection = by_role["pre_execution_plan_projection"]
        with pytest.raises(sqlite3.IntegrityError) as caught:
            _insert_exact_repaired_values(
                connection,
                projection["table"],
                projection["values"],
            )
        assert caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_FOREIGNKEY"
    finally:
        connection.rollback()
        connection.close()


@pytest.mark.parametrize("readiness_present", (False, True), ids=("absent", "present"))
def test_repaired_nine_table_ddl_and_both_golden_families_are_representable(
    readiness_present: bool,
) -> None:
    connection, inventory = _install_repaired_temporary_schema()
    try:
        assert sqlite3.sqlite_version_info >= (3, 37, 0)
        assert inventory == {
            "baseline_tables": 30,
            "added_tables": 9,
            "added_triggers": 18,
            "added_explicit_indexes": 0,
        }
        actual_tables = tuple(
            row[0]
            for row in connection.execute(
                f"SELECT name FROM sqlite_schema WHERE type='table' AND name IN ({','.join('?' for _ in REPAIRED_TABLE_ORDER)}) ORDER BY rowid",
                REPAIRED_TABLE_ORDER,
            )
        )
        assert actual_tables == REPAIRED_TABLE_ORDER
        for table in REPAIRED_TABLE_ORDER:
            table_info = connection.execute(
                f'PRAGMA table_info("{table}")'
            ).fetchall()
            assert tuple(row[1] for row in table_info) == tuple(
                name for name, _kind in REPAIRED_TABLE_COLUMNS[table]
            )
            assert all(row[2] == "ANY" for row in table_info)
        assert _new_table_row_count(connection) == 0
        family = _build_repaired_physical_family(readiness_present)
        _insert_sqlite_golden_family(connection, readiness_present)
        connection.commit()
        assert _new_table_row_count(connection) == (23 if readiness_present else 22)
        for member in family["physical_rows"]:
            predicate = " AND ".join(
                f'"{field}"=?' for field, _value in _member_locator(member)
            )
            fetched = connection.execute(
                f'SELECT {",".join(member["values"])} FROM "{member["table"]}" WHERE {predicate} LIMIT 2',
                tuple(value for _field, value in _member_locator(member)),
            ).fetchall()
            assert fetched == [tuple(member["values"].values())]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()


def test_migration_0003_owner_freezes_exact_representability_without_0002_rebuild() -> None:
    contract = _parse_repaired_owner()["migration_0003_contract"]
    assert contract["implemented"] is False
    assert (
        contract["table_count"],
        contract["trigger_count"],
        contract["explicit_index_count"],
        contract["seed_row_count"],
        contract["application_generation"],
    ) == (9, 18, 0, 0, 2)
    assert contract["migration_0002_rebuild_required"] is False
    assert contract["phase_algebra_source"].startswith(
        "the exact Section 41 phase_algebra table"
    )
    assert contract["phase_algebra_generated_check_table_count"] == 4
    assert contract["cross_phase_common_row_accepted"] is False
    assert contract[
        "post_execution_common_envelope_representable_without_preexecution_context"
    ] is True
    assert "case-insensitive rejection" in contract["safe_ref_check_parity"]
    assert "full CAST-AS-BLOB byte sequence" in contract["safe_ref_check_parity"]
    assert "no runtime UDF" in contract["byte_complete_ASCII_scalar_check"]
    assert "strftime round-trip" in contract["utc_second_check_parity"]
    assert "signed 64-bit bounds" in contract["persisted_integer_check_parity"]
    assert contract["finite_value_vocabularies"] == {
        **REPAIRED_KIND_VOCABULARIES,
        "global_stop_state": ("clear", "active"),
    }
    assert contract["finite_value_checks_are_exact_SQLite_text_membership_checks"] is True
    assert (
        contract["disposition_lineage_key"]
        == REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS
    )
    assert (
        _parse_reaudit_repair_owner()["canonical_c2b3d_lineage"][
            "field_kind_order"
        ]
        == REPAIRED_C2B3D_LINEAGE_FIELD_SPECS
    )
    assert contract["disposition_root_sentinel"] == -1
    assert contract["disposition_unique_constraints"] == (
        ("proposal_ref",),
        ("full_lineage_key", "resulting_selection_head_revision"),
        ("full_lineage_key", "prior_selection_head_revision"),
        (
            "full_lineage_key",
            "disposition_ref",
            "resulting_selection_head_revision",
            "selection_head_postimage_digest",
        ),
        (
            "full_lineage_key",
            "disposition_ref",
            "proposal_ref",
            "disposition",
            "resulting_selection_head_revision",
            "selection_head_postimage_digest",
        ),
        (
            "program_ref",
            "disposition_ref",
            "proposal_ref",
            "effect_intent_ref",
            "resulting_selection_head_revision",
            "selection_head_postimage_digest",
        ),
    )
    assert contract["automatic_constraint_indexes_only"] is True
    assert contract["selection_head_lineage_key_changed"] is False
    assert contract["selection_head_current_disposition_equals_referenced_disposition"] is True
    assert (
        contract[
            "selection_head_current_proposal_equals_referenced_disposition_proposal"
        ]
        is True
    )
    assert contract["selection_head_parent_key"] == (
        "full_lineage_key",
        "current_disposition_ref",
        "current_proposal_ref",
        "current_disposition",
        "head_revision",
        "head_digest",
        (
            "references disposition disposition_ref, proposal_ref, disposition, "
            "resulting revision, and selection-head-postimage digest"
        ),
    )


def _disposition_unique_column_sets(connection: sqlite3.Connection) -> set[tuple[str, ...]]:
    result: set[tuple[str, ...]] = set()
    for row in connection.execute("PRAGMA index_list(development_pre_execution_dispositions)"):
        if row[2] != 1:
            continue
        result.add(
            tuple(
                item[2]
                for item in connection.execute(
                    f"PRAGMA index_info({json.dumps(row[1])})"
                )
            )
        )
    return result


def test_disposition_constraints_create_linear_history_with_automatic_indexes() -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        root = _insert_sqlite_golden_family(connection, False)
        lineage = root["lineage"]
        unique_sets = _disposition_unique_column_sets(connection)
        assert REPAIRED_LINEAGE_COLUMNS + ("resulting_selection_head_revision",) in unique_sets
        assert REPAIRED_LINEAGE_COLUMNS + ("prior_selection_head_revision",) in unique_sets
        assert REPAIRED_LINEAGE_COLUMNS + (
            "disposition_ref",
            "resulting_selection_head_revision",
            "selection_head_postimage_digest",
        ) in unique_sets
        assert REPAIRED_LINEAGE_COLUMNS + (
            "disposition_ref",
            "proposal_ref",
            "disposition",
            "resulting_selection_head_revision",
            "selection_head_postimage_digest",
        ) in unique_sets
        assert ("proposal_ref",) in unique_sets
        assert connection.execute(
            "SELECT count(*) FROM sqlite_schema WHERE type='index' AND tbl_name='development_pre_execution_dispositions' AND sql IS NOT NULL"
        ).fetchone() == (0,)

        second_proposal = _insert_sqlite_proposal_prerequisites(connection, "second-root")
        with pytest.raises(sqlite3.IntegrityError) as duplicate_root:
            _insert_sqlite_disposition(
                connection,
                lineage=lineage,
                proposal_ref=second_proposal,
                disposition_ref="disposition.second-root.0",
                supersedes_ref=None,
                prior_revision=-1,
                prior_digest=None,
                resulting_revision=0,
                selection_head_postimage_digest="d" * 64,
            )
        assert duplicate_root.value.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE"

        successor_proposal = _insert_sqlite_proposal_prerequisites(connection, "successor-one")
        _insert_sqlite_disposition(
            connection,
            lineage=lineage,
            proposal_ref=successor_proposal,
            disposition_ref="disposition.absent.1",
            supersedes_ref=root["disposition_ref"],
            prior_revision=0,
            prior_digest=root["selection_head_postimage_digest"],
            resulting_revision=1,
            selection_head_postimage_digest="e" * 64,
        )
        wrong_digest_proposal = _insert_sqlite_proposal_prerequisites(connection, "wrong-predecessor-digest")
        with pytest.raises(sqlite3.IntegrityError) as wrong_predecessor_digest:
            _insert_sqlite_disposition(
                connection,
                lineage=_sqlite_lineage("wrong-predecessor-digest"),
                proposal_ref=wrong_digest_proposal,
                disposition_ref="disposition.wrong-predecessor-digest.1",
                supersedes_ref=root["disposition_ref"],
                prior_revision=0,
                prior_digest=root["disposition_digest"],
                resulting_revision=1,
                selection_head_postimage_digest="7" * 64,
            )
        assert wrong_predecessor_digest.value.sqlite_errorname == "SQLITE_CONSTRAINT_FOREIGNKEY"
        branching_proposal = _insert_sqlite_proposal_prerequisites(connection, "branching-successor")
        with pytest.raises(sqlite3.IntegrityError) as duplicate_successor:
            _insert_sqlite_disposition(
                connection,
                lineage=lineage,
                proposal_ref=branching_proposal,
                disposition_ref="disposition.absent.branch",
                supersedes_ref=root["disposition_ref"],
                prior_revision=0,
                prior_digest=root["selection_head_postimage_digest"],
                resulting_revision=1,
                selection_head_postimage_digest="f" * 64,
            )
        assert duplicate_successor.value.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE"

        bad_arithmetic_proposal = _insert_sqlite_proposal_prerequisites(connection, "bad-arithmetic")
        with pytest.raises(sqlite3.IntegrityError) as bad_arithmetic:
            _insert_sqlite_disposition(
                connection,
                lineage=_sqlite_lineage("bad-arithmetic"),
                proposal_ref=bad_arithmetic_proposal,
                disposition_ref="disposition.bad-arithmetic.2",
                supersedes_ref="disposition.missing.0",
                prior_revision=0,
                prior_digest="1" * 64,
                resulting_revision=2,
                selection_head_postimage_digest="2" * 64,
            )
        assert bad_arithmetic.value.sqlite_errorname == "SQLITE_CONSTRAINT_CHECK"
        assert str(bad_arithmetic.value) == (
            "CHECK constraint failed: disposition_root_or_successor_shape"
        )
    finally:
        connection.close()


def test_predecessor_foreign_key_uses_only_head_postimage_digest() -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        root = _insert_sqlite_golden_family(connection, False)
        wrong_proposal = _insert_sqlite_proposal_prerequisites(connection, "wrong-self-substitution")
        with pytest.raises(sqlite3.IntegrityError) as caught:
            _insert_sqlite_disposition(
                connection,
                lineage=root["lineage"],
                proposal_ref=wrong_proposal,
                disposition_ref="disposition.wrong-self-substitution.1",
                supersedes_ref=root["disposition_ref"],
                prior_revision=0,
                prior_digest=root["disposition_digest"],
                resulting_revision=1,
                selection_head_postimage_digest="7" * 64,
            )
        assert caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_FOREIGNKEY"

        correct_proposal = _insert_sqlite_proposal_prerequisites(connection, "correct-head-digest")
        inserted = _insert_sqlite_disposition(
            connection,
            lineage=root["lineage"],
            proposal_ref=correct_proposal,
            disposition_ref="disposition.correct-head-digest.1",
            supersedes_ref=root["disposition_ref"],
            prior_revision=0,
            prior_digest=root["selection_head_postimage_digest"],
            resulting_revision=1,
            selection_head_postimage_digest="8" * 64,
        )
        assert inserted["selection_head_postimage_digest"] == "8" * 64
        assert inserted["disposition_digest"] != inserted["selection_head_postimage_digest"]
    finally:
        connection.close()


@pytest.mark.parametrize(
    "nullable_field",
    ("expected_selection_head_revision", "expected_selection_head_digest"),
)
def test_f2_successor_expected_head_fields_are_independently_nonnull_in_ddl(
    nullable_field: str,
) -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        root = _insert_sqlite_golden_family(connection, False)
        proposal_ref = _insert_sqlite_proposal_prerequisites(
            connection,
            (
                "nullable-revision"
                if nullable_field == "expected_selection_head_revision"
                else "nullable-digest"
            ),
        )
        template = deepcopy(
            next(
                member["values"]
                for member in _build_repaired_physical_family(False)["physical_rows"]
                if member["role"] == "coordinator_disposition"
            )
        )
        template.update(
            dict(zip(REPAIRED_LINEAGE_COLUMNS, root["lineage"], strict=True))
        )
        template.update(
            {
                "disposition_ref": (
                    "disposition.nullable-revision.1"
                    if nullable_field == "expected_selection_head_revision"
                    else "disposition.nullable-digest.1"
                ),
                "proposal_ref": proposal_ref,
                "supersedes_disposition_ref": root["disposition_ref"],
                "expected_selection_head_revision": 0,
                "expected_selection_head_digest": root[
                    "selection_head_postimage_digest"
                ],
                "prior_selection_head_revision": 0,
                "prior_selection_head_digest": root[
                    "selection_head_postimage_digest"
                ],
                "resulting_selection_head_revision": 1,
                "selection_head_postimage_digest": "7" * 64,
            }
        )
        template[nullable_field] = None
        template["disposition_digest"] = _repaired_row_digest(
            REPAIRED_TABLE_ORDER[6], template
        )
        with pytest.raises(sqlite3.IntegrityError) as caught:
            _insert_exact_repaired_values(
                connection,
                REPAIRED_TABLE_ORDER[6],
                template,
            )
        assert caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_CHECK"
        assert str(caught.value) == (
            "CHECK constraint failed: disposition_root_or_successor_shape"
        )
    finally:
        connection.rollback()
        connection.close()


@pytest.mark.parametrize(
    "head_field,bad_value",
    (
        ("current_disposition", "deferred"),
        ("current_proposal_ref", "replacement_proposal"),
    ),
)
def test_f2_selection_head_composite_rejects_disposition_or_proposal_mismatch(
    head_field: str,
    bad_value: str,
) -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        root = _insert_sqlite_golden_family(connection, False)
        if head_field == "current_proposal_ref":
            bad_value = _insert_sqlite_proposal_prerequisites(
                connection,
                "head-proposal-mismatch",
            )
        with pytest.raises(sqlite3.IntegrityError) as caught:
            connection.execute(
                f"UPDATE development_pre_execution_selection_heads SET {head_field}=? WHERE "
                + _LINEAGE_WHERE,
                (bad_value, *root["lineage"]),
            )
        assert caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_FOREIGNKEY"
    finally:
        connection.rollback()
        connection.close()


@pytest.mark.parametrize(
    "role,field",
    (
        ("coordinator_disposition", "disposition"),
        ("selection_head_postimage", "current_disposition"),
    ),
)
def test_f2_generated_ddl_rejects_unknown_disposition_values(
    role: str,
    field: str,
) -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        family = _build_repaired_physical_family(False)
        rows = deepcopy(family["physical_rows"])
        by_role = {row["role"]: row["values"] for row in rows}
        disposition = by_role["coordinator_disposition"]
        head = by_role["selection_head_postimage"]
        target = disposition if role == "coordinator_disposition" else head
        target[field] = "semantically_invalid"
        head["head_digest"] = _repaired_row_digest(REPAIRED_TABLE_ORDER[7], head)
        disposition["selection_head_postimage_digest"] = head["head_digest"]
        disposition["disposition_digest"] = _repaired_row_digest(
            REPAIRED_TABLE_ORDER[6], disposition
        )
        with pytest.raises(sqlite3.IntegrityError) as caught:
            for member in rows:
                _insert_exact_repaired_values(
                    connection,
                    member["table"],
                    member["values"],
                )
        assert caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_CHECK"
    finally:
        connection.rollback()
        connection.close()


def test_f2_physical_validator_rejects_unknown_and_mismatched_dispositions() -> None:
    unknown = _build_repaired_physical_family(False)
    unknown_rows = {row["role"]: row["values"] for row in unknown["physical_rows"]}
    unknown_disposition = unknown_rows["coordinator_disposition"]
    unknown_head = unknown_rows["selection_head_postimage"]
    unknown_disposition["disposition"] = "semantically_invalid"
    unknown_head["current_disposition"] = "semantically_invalid"
    unknown_head["head_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[7], unknown_head
    )
    unknown_disposition["selection_head_postimage_digest"] = unknown_head["head_digest"]
    unknown_disposition["disposition_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[6], unknown_disposition
    )
    with pytest.raises(_ContractViolation) as unknown_caught:
        _validate_repaired_physical_family(unknown)
    assert unknown_caught.value.reason == "physical_family_row_digest_mismatch"

    mismatched = _build_repaired_physical_family(False)
    mismatch_rows = {
        row["role"]: row["values"] for row in mismatched["physical_rows"]
    }
    mismatch_disposition = mismatch_rows["coordinator_disposition"]
    mismatch_head = mismatch_rows["selection_head_postimage"]
    mismatch_head["current_disposition"] = "deferred"
    mismatch_head["head_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[7], mismatch_head
    )
    mismatch_disposition["selection_head_postimage_digest"] = mismatch_head["head_digest"]
    mismatch_disposition["disposition_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[6], mismatch_disposition
    )
    with pytest.raises(_ContractViolation) as mismatch_caught:
        _validate_repaired_physical_family(mismatched)
    assert mismatch_caught.value.reason == "physical_family_row_digest_mismatch"

    proposal_mismatched = _build_repaired_physical_family(False)
    proposal_mismatch_rows = {
        row["role"]: row["values"] for row in proposal_mismatched["physical_rows"]
    }
    proposal_mismatch_disposition = proposal_mismatch_rows["coordinator_disposition"]
    proposal_mismatch_head = proposal_mismatch_rows["selection_head_postimage"]
    proposal_mismatch_head["current_proposal_ref"] = "proposal.mismatched.0001"
    proposal_mismatch_head["head_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[7], proposal_mismatch_head
    )
    proposal_mismatch_disposition["selection_head_postimage_digest"] = (
        proposal_mismatch_head["head_digest"]
    )
    proposal_mismatch_disposition["disposition_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[6], proposal_mismatch_disposition
    )
    with pytest.raises(_ContractViolation) as proposal_mismatch_caught:
        _validate_repaired_physical_family(proposal_mismatched)
    assert (
        proposal_mismatch_caught.value.reason
        == "physical_family_row_digest_mismatch"
    )


@pytest.mark.parametrize(
    "field,bad_value",
    (
        ("supersedes_disposition_ref", "disposition.forbidden.root-parent"),
        ("expected_selection_head_revision", 0),
        ("expected_selection_head_digest", "a" * 64),
        ("prior_selection_head_revision", 0),
        ("prior_selection_head_digest", "b" * 64),
    ),
)
def test_f2_physical_validator_rejects_every_invalid_root_shape(
    field: str,
    bad_value: object,
) -> None:
    family = _build_repaired_physical_family(False)
    disposition = next(
        row["values"]
        for row in family["physical_rows"]
        if row["role"] == "coordinator_disposition"
    )
    disposition[field] = bad_value
    disposition["disposition_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[6], disposition
    )
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(family)
    assert caught.value.reason == "physical_family_row_digest_mismatch"
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        with pytest.raises(sqlite3.IntegrityError) as sqlite_caught:
            for member in family["physical_rows"]:
                _insert_exact_repaired_values(
                    connection,
                    member["table"],
                    member["values"],
                )
        assert sqlite_caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_CHECK"
        assert str(sqlite_caught.value) == (
            "CHECK constraint failed: disposition_root_or_successor_shape"
        )
    finally:
        connection.rollback()
        connection.close()


_LINEAGE_WHERE = " AND ".join(f"{column}=?" for column in REPAIRED_LINEAGE_COLUMNS)
_CURRENTNESS_WHERE = " AND ".join(
    f"{column}=?" for column in REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS
)
_LINEAGE_FIELD_INDEX = {
    field: index for index, field in enumerate(REPAIRED_LINEAGE_COLUMNS)
}


def _currentness_key_from_lineage(
    lineage: tuple[object, ...],
) -> tuple[object, ...]:
    return tuple(
        lineage[_LINEAGE_FIELD_INDEX[field]]
        for field in REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS
    )


_HEAD_RECOVERY_FIELDS = tuple(
    name for name, _kind in REPAIRED_TABLE_COLUMNS[REPAIRED_TABLE_ORDER[7]]
)
_RECOVERY_ROW_FIELDS = tuple(
    name for name, _kind in REPAIRED_TABLE_COLUMNS[REPAIRED_TABLE_ORDER[6]]
)
_HEAD_QUERY = (
    "SELECT " + ",".join(_HEAD_RECOVERY_FIELDS) + " "
    "FROM development_pre_execution_selection_heads WHERE "
    + _CURRENTNESS_WHERE
    + " LIMIT 2"
)
_INVENTORY_QUERY = (
    "SELECT " + ",".join(_RECOVERY_ROW_FIELDS) + " "
    "FROM development_pre_execution_dispositions WHERE "
    + _CURRENTNESS_WHERE
    + " ORDER BY rowid LIMIT 258"
)
_DISPOSITION_QUERY = (
    "SELECT " + ",".join(_RECOVERY_ROW_FIELDS) + " "
    "FROM development_pre_execution_dispositions WHERE "
    + _LINEAGE_WHERE
    + " AND disposition_ref=? LIMIT 2"
)
_SUCCESSOR_QUERY = (
    "SELECT " + ",".join(_RECOVERY_ROW_FIELDS) + " "
    "FROM development_pre_execution_dispositions WHERE "
    + _LINEAGE_WHERE
    + " AND prior_selection_head_revision=? AND supersedes_disposition_ref=? LIMIT 2"
)
_EVIDENCE_RECOVERY_FIELDS = tuple(
    name for name, _kind in REPAIRED_TABLE_COLUMNS[REPAIRED_TABLE_ORDER[5]]
)
_EVIDENCE_INVENTORY_LIMIT = 16
_EVIDENCE_INVENTORY_ORDER_FIELDS = (
    "role_rank",
    "ordinal",
    "evidence_role",
    "evidence_set_ref",
    "evidence_ref",
    "evidence_digest",
    "evidence_binding_digest",
    "proposal_phase",
    "schema_id",
    "required_for_selection",
    "evidence_bound_at",
)
_EVIDENCE_INVENTORY_QUERY = (
    "SELECT "
    + ",".join(_EVIDENCE_RECOVERY_FIELDS)
    + f' FROM "{REPAIRED_TABLE_ORDER[5]}" WHERE proposal_ref=? ORDER BY '
    + ",".join(f'"{field}"' for field in _EVIDENCE_INVENTORY_ORDER_FIELDS)
    + f" LIMIT {_EVIDENCE_INVENTORY_LIMIT}"
)
_RECEIPT_RECOVERY_FIELDS = tuple(
    name for name, _kind in REPAIRED_TABLE_COLUMNS[REPAIRED_TABLE_ORDER[8]]
)
_RECEIPT_BY_MUTATION_QUERY = (
    "SELECT "
    + ",".join(_RECEIPT_RECOVERY_FIELDS)
    + f' FROM "{REPAIRED_TABLE_ORDER[8]}" WHERE mutation_ref=? LIMIT 2'
)
_DISPOSITION_BY_REF_QUERY = (
    "SELECT "
    + ",".join(_RECOVERY_ROW_FIELDS)
    + f' FROM "{REPAIRED_TABLE_ORDER[6]}" WHERE disposition_ref=? LIMIT 2'
)
_PLANNING_CONTEXT_RECOVERY_FIELDS = tuple(
    name for name, _kind in REPAIRED_TABLE_COLUMNS[REPAIRED_TABLE_ORDER[1]]
)
_PLANNING_CONTEXT_BY_REF_QUERY = (
    "SELECT "
    + ",".join(_PLANNING_CONTEXT_RECOVERY_FIELDS)
    + f' FROM "{REPAIRED_TABLE_ORDER[1]}" WHERE planning_context_ref=? LIMIT 2'
)


class _RecoveryReadback(NamedTuple):
    classification: str
    depth: int
    result: dict[str, object] | None


def _query_at_most_one(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple[object, ...],
) -> tuple[object, ...] | None:
    cursor = connection.execute(sql, parameters)
    rows = cursor.fetchmany(2)
    if len(rows) != 1 or type(rows[0]) is not tuple:
        return None
    return rows[0]


def _recovery_exact_row(
    row: object,
    table: str,
) -> dict[str, object] | None:
    fields = tuple(name for name, _kind in REPAIRED_TABLE_COLUMNS[table])
    if type(row) is not tuple or len(row) != len(fields):
        return None
    values = dict(zip(fields, row, strict=True))
    if tuple(values) != fields:
        return None
    if any(
        not _repaired_value_matches_kind(values[field], kind)
        for field, kind in REPAIRED_TABLE_COLUMNS[table]
    ):
        return None
    digest_field, _domain = REPAIRED_TABLE_DIGESTS[table]
    if values[digest_field] != _repaired_row_digest(table, values):
        return None
    if (
        table == REPAIRED_TABLE_ORDER[6]
        and not _repaired_disposition_shape_is_exact(values)
    ):
        return None
    return values


def _recovery_schema_is_exact(connection: sqlite3.Connection) -> bool:
    for table in REPAIRED_TABLE_ORDER:
        expected_fields = tuple(
            name for name, _kind in REPAIRED_TABLE_COLUMNS[table]
        )
        observed_fields = tuple(
            row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')
        )
        if observed_fields != expected_fields:
            return False
    return True


def _recovery_probe_expected_row(
    connection: sqlite3.Connection,
    *,
    table: str,
    expected_values: dict[str, object],
) -> str:
    expected_fields = tuple(
        name for name, _kind in REPAIRED_TABLE_COLUMNS[table]
    )
    observed_states: list[str] = []
    for identity_fields in REPAIRED_RECOVERY_IDENTITY_FIELDS[table]:
        where = " AND ".join(f'"{field}"=?' for field in identity_fields)
        rows = connection.execute(
            f'SELECT {",".join(expected_fields)} FROM "{table}" '
            f"WHERE {where} LIMIT 2",
            tuple(expected_values[field] for field in identity_fields),
        ).fetchmany(2)
        if not rows:
            observed_states.append("absent")
            continue
        if len(rows) != 1:
            return "unresolved"
        recovered = _recovery_exact_row(rows[0], table)
        if recovered is None or not _s41_exact_equal(recovered, expected_values):
            return "unresolved"
        observed_states.append("exact")
    if all(state == "absent" for state in observed_states):
        return "absent"
    if all(state == "exact" for state in observed_states):
        return "exact"
    return "unresolved"


def _recover_complete_evidence_inventory(
    connection: sqlite3.Connection,
    expected_family: dict[str, object],
) -> tuple[str, tuple[dict[str, object], ...]]:
    rows_by_role = {
        row["role"]: row for row in expected_family["physical_rows"]
    }
    expected_receipt = rows_by_role["receipt"]["values"]
    expected_members = tuple(
        row
        for row in expected_family["physical_rows"]
        if row["table"] == REPAIRED_TABLE_ORDER[5]
    )
    receipt_tuple = _query_at_most_one(
        connection,
        _RECEIPT_BY_MUTATION_QUERY,
        (expected_receipt["mutation_ref"],),
    )
    receipt = (
        None
        if receipt_tuple is None
        else _recovery_exact_row(receipt_tuple, REPAIRED_TABLE_ORDER[8])
    )
    proposal_ref = (
        expected_receipt["proposal_ref"]
        if receipt is None
        else receipt["proposal_ref"]
    )
    cursor = connection.execute(
        _EVIDENCE_INVENTORY_QUERY,
        (proposal_ref,),
    )
    observed_rows = cursor.fetchmany(_EVIDENCE_INVENTORY_LIMIT)
    if receipt_tuple is None and not observed_rows:
        return "absent", ()
    if receipt is None or not _s41_exact_equal(receipt, expected_receipt):
        return "unresolved", ()
    if not observed_rows:
        return "unresolved", ()
    disposition_tuple = _query_at_most_one(
        connection,
        _DISPOSITION_BY_REF_QUERY,
        (receipt["disposition_ref"],),
    )
    if disposition_tuple is None:
        return "unresolved", ()
    disposition = _recovery_exact_row(
        disposition_tuple,
        REPAIRED_TABLE_ORDER[6],
    )
    if disposition is None or not (
        disposition["proposal_ref"] == receipt["proposal_ref"]
        and disposition["disposition_digest"] == receipt["disposition_digest"]
    ):
        return "unresolved", ()
    context_tuple = _query_at_most_one(
        connection,
        _PLANNING_CONTEXT_BY_REF_QUERY,
        (disposition["planning_context_ref"],),
    )
    if context_tuple is None:
        return "unresolved", ()
    context = _recovery_exact_row(context_tuple, REPAIRED_TABLE_ORDER[1])
    if context is None or not (
        context["planning_context_digest"] == disposition["planning_context_digest"]
        and context["program_ref"] == receipt["program_ref"]
    ):
        return "unresolved", ()
    readiness_binding = (
        context["qualified_remote_host_readiness_ref"],
        context["qualified_remote_host_readiness_digest"],
    )
    if readiness_binding == (None, None):
        expected_count = 14
    elif all(type(value) is str for value in readiness_binding):
        expected_count = 15
    else:
        return "unresolved", ()
    if len(expected_members) != expected_count:
        return "unresolved", ()
    if len(observed_rows) == _EVIDENCE_INVENTORY_LIMIT:
        return "unresolved", ()
    recovered_rows: list[dict[str, object]] = []
    for observed_row in observed_rows:
        recovered = _recovery_exact_row(
            observed_row,
            REPAIRED_TABLE_ORDER[5],
        )
        if recovered is None:
            return "unresolved", ()
        recovered_rows.append(recovered)
    ordered_expected = tuple(
        sorted(
            (member["values"] for member in expected_members),
            key=lambda values: tuple(
                values[field] for field in _EVIDENCE_INVENTORY_ORDER_FIELDS
            ),
        )
    )
    if len(recovered_rows) != expected_count or not _s41_exact_equal(
        tuple(recovered_rows),
        ordered_expected,
    ):
        return "unresolved", ()
    actual_graph_entries = tuple(
        {
            "role": f'evidence.{values["evidence_role"]}',
            "rank": values["role_rank"],
            "ordinal": values["ordinal"],
            "table": REPAIRED_TABLE_ORDER[5],
            "locator": _member_locator(
                {
                    "table": REPAIRED_TABLE_ORDER[5],
                    "values": values,
                }
            ),
            "member_digest": values["evidence_binding_digest"],
        }
        for values in recovered_rows
    )
    expected_graph_entries = tuple(
        entry
        for entry in expected_family["graph"]["entries"]
        if entry["table"] == REPAIRED_TABLE_ORDER[5]
    )
    if not _s41_exact_equal(actual_graph_entries, expected_graph_entries):
        return "unresolved", ()
    return "exact", tuple(recovered_rows)


def _reconstruct_receipt_owned_recovery_result(
    connection: sqlite3.Connection,
    expected_family: dict[str, object],
) -> dict[str, object] | None:
    expected_receipt = expected_family["receipt"]["values"]
    receipt_tuple = _query_at_most_one(
        connection,
        _RECEIPT_BY_MUTATION_QUERY,
        (expected_receipt["mutation_ref"],),
    )
    if receipt_tuple is None:
        return None
    receipt = _recovery_exact_row(receipt_tuple, REPAIRED_TABLE_ORDER[8])
    if receipt is None:
        return None
    disposition_tuple = _query_at_most_one(
        connection,
        _DISPOSITION_BY_REF_QUERY,
        (receipt["disposition_ref"],),
    )
    if disposition_tuple is None:
        return None
    disposition = _recovery_exact_row(
        disposition_tuple,
        REPAIRED_TABLE_ORDER[6],
    )
    if disposition is None:
        return None
    if any(
        not _s41_exact_equal(receipt[field], disposition[source])
        for field, source in (
            ("program_ref", "program_ref"),
            ("proposal_ref", "proposal_ref"),
            ("effect_intent_ref", "effect_intent_ref"),
            ("disposition_ref", "disposition_ref"),
            ("disposition_digest", "disposition_digest"),
            (
                "authority_selection_observation_ref",
                "authority_selection_observation_ref",
            ),
            (
                "authority_selection_observation_digest",
                "authority_selection_observation_digest",
            ),
            ("selection_head_revision", "resulting_selection_head_revision"),
            ("selection_head_digest", "selection_head_postimage_digest"),
            ("committed_at", "coordinator_disposition_decided_at"),
        )
    ):
        return None
    projection: dict[str, object] = {
        "schema_id": SCHEMA_IDS["result"],
        "mutation_ref": receipt["mutation_ref"],
        "command_digest": receipt["command_digest"],
        "proposal_ref": disposition["proposal_ref"],
        "disposition_ref": disposition["disposition_ref"],
        "disposition_digest": disposition["disposition_digest"],
        "disposition": disposition["disposition"],
        "program_ref": disposition["program_ref"],
        "semantic_attempt_ref": disposition["semantic_attempt_ref"],
        "candidate_ref": disposition["candidate_ref"],
        "effect_intent_ref": disposition["effect_intent_ref"],
        "selection_head_revision": receipt["selection_head_revision"],
        "selection_head_digest": receipt["selection_head_digest"],
        "authority_selection_observation_ref": receipt[
            "authority_selection_observation_ref"
        ],
        "authority_selection_observation_digest": receipt[
            "authority_selection_observation_digest"
        ],
        "mutation_graph_digest": receipt["mutation_graph_digest"],
        "recorded_at": receipt["committed_at"],
    }
    projection["result_projection_digest"] = _s41_digest(
        DIGEST_DOMAINS["result"],
        projection,
    )
    if receipt["result_projection_digest"] != projection[
        "result_projection_digest"
    ]:
        return None
    result = {**projection, "receipt_digest": receipt["receipt_digest"]}
    if tuple(result) != REPAIRED_FRESH_RESULT_FIELDS or not _s41_exact_equal(
        result,
        expected_family["replay_result"],
    ):
        return None
    return result


def _recover_repaired_family(
    connection: sqlite3.Connection,
    *,
    expected_family: object,
    expected_head_preimage: object | None,
    fresh_writer_verified: object,
) -> _RecoveryReadback:
    if fresh_writer_verified is not True:
        return _RecoveryReadback("unresolved", 0, None)
    try:
        _validate_repaired_physical_family(expected_family)
        if not _recovery_schema_is_exact(connection):
            return _RecoveryReadback("unresolved", 0, None)
        expected_rows = expected_family["physical_rows"]
        rows_by_role = {row["role"]: row for row in expected_rows}
        target_disposition = rows_by_role["coordinator_disposition"]["values"]
        target_head = rows_by_role["selection_head_postimage"]["values"]
        target_receipt = rows_by_role["receipt"]["values"]

        validated_preimage: dict[str, object] | None = None
        if expected_head_preimage is None:
            if target_disposition["resulting_selection_head_revision"] != 0:
                return _RecoveryReadback("unresolved", 0, None)
        else:
            if (
                type(expected_head_preimage) is not dict
                or any(type(key) is not str for key in expected_head_preimage)
                or tuple(expected_head_preimage) != _HEAD_RECOVERY_FIELDS
            ):
                return _RecoveryReadback("unresolved", 0, None)
            validated_preimage = _recovery_exact_row(
                tuple(expected_head_preimage.values()),
                REPAIRED_TABLE_ORDER[7],
            )
            if validated_preimage is None:
                return _RecoveryReadback("unresolved", 0, None)
            preimage_lineage = tuple(
                validated_preimage[field] for field in REPAIRED_LINEAGE_COLUMNS
            )
            target_lineage = tuple(
                target_head[field] for field in REPAIRED_LINEAGE_COLUMNS
            )
            if not all(
                _s41_exact_equal(left, right)
                for left, right in (
                    (preimage_lineage, target_lineage),
                    (
                        target_disposition["supersedes_disposition_ref"],
                        validated_preimage["current_disposition_ref"],
                    ),
                    (
                        target_disposition["expected_selection_head_revision"],
                        validated_preimage["head_revision"],
                    ),
                    (
                        target_disposition["expected_selection_head_digest"],
                        validated_preimage["head_digest"],
                    ),
                    (
                        target_disposition["prior_selection_head_revision"],
                        validated_preimage["head_revision"],
                    ),
                    (
                        target_disposition["prior_selection_head_digest"],
                        validated_preimage["head_digest"],
                    ),
                    (
                        target_disposition["resulting_selection_head_revision"],
                        validated_preimage["head_revision"] + 1,
                    ),
                )
            ):
                return _RecoveryReadback("unresolved", 0, None)

        evidence_state, _actual_evidence = _recover_complete_evidence_inventory(
            connection,
            expected_family,
        )
        if evidence_state == "unresolved":
            return _RecoveryReadback("unresolved", 0, None)

        immutable_states = tuple(
            _recovery_probe_expected_row(
                connection,
                table=row["table"],
                expected_values=row["values"],
            )
            for row in expected_rows
            if row["table"] != REPAIRED_TABLE_ORDER[7]
        )
        if any(state == "unresolved" for state in immutable_states):
            return _RecoveryReadback("unresolved", 0, None)
        if all(state == "exact" for state in immutable_states):
            if evidence_state != "exact":
                return _RecoveryReadback("unresolved", 0, None)
            lineage = tuple(
                target_disposition[field] for field in REPAIRED_LINEAGE_COLUMNS
            )
            ancestry = _recover_repaired_disposition(
                connection,
                lineage=lineage,
                receipt_disposition_ref=target_receipt["disposition_ref"],
                receipt_revision=target_receipt["selection_head_revision"],
                receipt_digest=target_receipt["disposition_digest"],
            )
            if ancestry[0] != "committed_exact":
                return _RecoveryReadback("unresolved", ancestry[1], None)
            result = _reconstruct_receipt_owned_recovery_result(
                connection,
                expected_family,
            )
            if result is None:
                return _RecoveryReadback("unresolved", ancestry[1], None)
            return _RecoveryReadback("committed_exact", ancestry[1], result)
        if not all(state == "absent" for state in immutable_states):
            return _RecoveryReadback("unresolved", 0, None)
        if evidence_state != "absent":
            return _RecoveryReadback("unresolved", 0, None)

        preimage_state = _recovery_probe_expected_row(
            connection,
            table=REPAIRED_TABLE_ORDER[7],
            expected_values=(
                target_head if validated_preimage is None else validated_preimage
            ),
        )
        if (
            validated_preimage is None
            and preimage_state == "absent"
        ) or (
            validated_preimage is not None
            and preimage_state == "exact"
        ):
            return _RecoveryReadback("definitely_not_committed", 0, None)
        return _RecoveryReadback("unresolved", 0, None)
    except (sqlite3.Error, _ContractViolation):
        return _RecoveryReadback("unresolved", 0, None)


def _recover_repaired_disposition(
    connection: sqlite3.Connection,
    *,
    lineage: tuple[object, ...],
    receipt_disposition_ref: str,
    receipt_revision: int,
    receipt_digest: str,
) -> tuple[str, int]:
    if (
        type(lineage) is not tuple
        or len(lineage) != len(REPAIRED_LINEAGE_COLUMNS)
        or any(
            not _repaired_value_matches_kind(value, kind)
            for value, (_field, kind) in zip(
                lineage,
                REPAIRED_C2B3D_LINEAGE_FIELD_SPECS,
                strict=True,
            )
        )
        or not _repaired_value_matches_kind(receipt_disposition_ref, "safe_ref")
        or not _repaired_value_matches_kind(receipt_revision, "nonnegative_int")
        or not _repaired_value_matches_kind(receipt_digest, "sha256")
    ):
        return "unresolved", 0
    for table in (REPAIRED_TABLE_ORDER[6], REPAIRED_TABLE_ORDER[7]):
        expected_fields = tuple(
            name for name, _kind in REPAIRED_TABLE_COLUMNS[table]
        )
        observed_fields = tuple(
            row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')
        )
        if observed_fields != expected_fields:
            return "unresolved", 0
    currentness_key = _currentness_key_from_lineage(lineage)
    head_tuples = connection.execute(_HEAD_QUERY, currentness_key).fetchmany(2)
    validated_heads = tuple(
        _recovery_exact_row(row, REPAIRED_TABLE_ORDER[7]) for row in head_tuples
    )
    if len(validated_heads) != 1 or validated_heads[0] is None:
        return "unresolved", 0
    head = validated_heads[0]
    if tuple(head[field] for field in REPAIRED_LINEAGE_COLUMNS) != lineage:
        return "unresolved", 0
    inventory_cursor = connection.execute(_INVENTORY_QUERY, currentness_key)
    inventory_tuples = inventory_cursor.fetchmany(258)
    if not inventory_tuples:
        return "unresolved", 0
    inventory_rows: list[dict[str, object]] = []
    for row_tuple in inventory_tuples:
        row = _recovery_exact_row(row_tuple, REPAIRED_TABLE_ORDER[6])
        if row is None:
            return "unresolved", 0
        if tuple(row[field] for field in REPAIRED_LINEAGE_COLUMNS) != lineage:
            return "unresolved", 0
        inventory_rows.append(row)
    inventory_overflow = len(inventory_rows) == 258
    inventory_rows.sort(key=lambda row: row["resulting_selection_head_revision"])
    inventory_refs = {row["disposition_ref"] for row in inventory_rows}
    if len(inventory_refs) != len(inventory_rows) or tuple(
        row["resulting_selection_head_revision"] for row in inventory_rows
    ) != tuple(sorted(row["resulting_selection_head_revision"] for row in inventory_rows)):
        return "unresolved", 0

    current_ref = head["current_disposition_ref"]
    current_revision = head["head_revision"]
    current_digest = head["head_digest"]
    dangling_tuples = connection.execute(
        _SUCCESSOR_QUERY,
        (*lineage, current_revision, current_ref),
    ).fetchmany(2)
    if any(
        _recovery_exact_row(row, REPAIRED_TABLE_ORDER[6]) is None
        for row in dangling_tuples
    ):
        return "unresolved", 0
    if dangling_tuples:
        return "unresolved", 0

    cursor_ref = current_ref
    cursor_revision = current_revision
    cursor_digest = current_digest
    visited: set[str] = set()
    receipt_seen = False
    predecessor_transitions = 0
    while True:
        selected_tuples = connection.execute(
            _DISPOSITION_QUERY, (*lineage, cursor_ref)
        ).fetchmany(2)
        validated_selected = tuple(
            _recovery_exact_row(item, REPAIRED_TABLE_ORDER[6])
            for item in selected_tuples
        )
        if len(validated_selected) != 1 or validated_selected[0] is None:
            return "unresolved", predecessor_transitions
        row = validated_selected[0]
        if row["disposition_ref"] in visited:
            return "unresolved", predecessor_transitions
        if not visited and not (
            row["disposition_ref"] == head["current_disposition_ref"]
            and row["proposal_ref"] == head["current_proposal_ref"]
            and row["disposition"] == head["current_disposition"]
        ):
            return "unresolved", predecessor_transitions
        visited.add(row["disposition_ref"])
        if (
            row["resulting_selection_head_revision"],
            row["selection_head_postimage_digest"],
        ) != (cursor_revision, cursor_digest):
            return "unresolved", predecessor_transitions
        if (
            row["disposition_ref"],
            row["resulting_selection_head_revision"],
            row["disposition_digest"],
        ) == (
            receipt_disposition_ref,
            receipt_revision,
            receipt_digest,
        ):
            receipt_seen = True

        if row["resulting_selection_head_revision"] == 0:
            break

        predecessor_transitions += 1
        if predecessor_transitions == 257:
            return "unresolved", predecessor_transitions
        if not (
            type(row["prior_selection_head_revision"]) is int
            and row["prior_selection_head_revision"]
            == row["resulting_selection_head_revision"] - 1
            and type(row["supersedes_disposition_ref"]) is str
            and type(row["prior_selection_head_digest"]) is str
        ):
            return "unresolved", predecessor_transitions
        successor_tuples = connection.execute(
            _SUCCESSOR_QUERY,
            (
                *lineage,
                row["prior_selection_head_revision"],
                row["supersedes_disposition_ref"],
            ),
        ).fetchmany(2)
        successors = tuple(
            _recovery_exact_row(item, REPAIRED_TABLE_ORDER[6])
            for item in successor_tuples
        )
        if (
            len(successors) != 1
            or successors[0] is None
            or successors[0]["disposition_ref"] != row["disposition_ref"]
        ):
            return "unresolved", predecessor_transitions
        cursor_ref = row["supersedes_disposition_ref"]
        cursor_revision = row["prior_selection_head_revision"]
        cursor_digest = row["prior_selection_head_digest"]

    if inventory_overflow or not receipt_seen or visited != inventory_refs:
        return "unresolved", predecessor_transitions
    return "committed_exact", predecessor_transitions


def _insert_sqlite_successor(
    connection: sqlite3.Connection,
    *,
    lineage: tuple[object, ...],
    predecessor_ref: str,
    predecessor_revision: int,
    predecessor_digest: str,
    revision: int,
    suffix: str,
) -> tuple[str, str]:
    proposal_ref = _insert_sqlite_proposal_prerequisites(connection, suffix)
    disposition_ref = f"disposition.{suffix}.{revision}"
    head_tuple = _query_at_most_one(
        connection,
        _HEAD_QUERY,
        _currentness_key_from_lineage(lineage),
    )
    assert head_tuple is not None
    head_values = dict(zip(_HEAD_RECOVERY_FIELDS, head_tuple, strict=True))
    head_values.update(
        {
            "current_proposal_ref": proposal_ref,
            "current_disposition_ref": disposition_ref,
            "current_disposition": "selected_for_dispatch_gates",
            "head_revision": revision,
            "updated_at": f"2026-08-22T12:{35 + min(revision, 24):02d}:04Z",
        }
    )
    head_values["head_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[7], head_values
    )
    selection_head_postimage_digest = head_values["head_digest"]
    _insert_sqlite_disposition(
        connection,
        lineage=lineage,
        proposal_ref=proposal_ref,
        disposition_ref=disposition_ref,
        supersedes_ref=predecessor_ref,
        prior_revision=predecessor_revision,
        prior_digest=predecessor_digest,
        resulting_revision=revision,
        selection_head_postimage_digest=selection_head_postimage_digest,
    )
    return disposition_ref, selection_head_postimage_digest


def _advance_sqlite_head(
    connection: sqlite3.Connection,
    lineage: tuple[object, ...],
    disposition_ref: str,
    revision: int,
    digest: str,
) -> None:
    disposition_tuple = _query_at_most_one(
        connection,
        _DISPOSITION_QUERY,
        (*lineage, disposition_ref),
    )
    assert disposition_tuple is not None
    disposition = dict(zip(_RECOVERY_ROW_FIELDS, disposition_tuple, strict=True))
    assert (
        disposition["resulting_selection_head_revision"] == revision
        and disposition["selection_head_postimage_digest"] == digest
    )
    connection.execute(
        "UPDATE development_pre_execution_selection_heads SET current_proposal_ref=?,current_disposition_ref=?,current_disposition=?,head_revision=?,head_digest=?,updated_at=? WHERE "
        + _CURRENTNESS_WHERE,
        (
            disposition["proposal_ref"],
            disposition_ref,
            disposition["disposition"],
            revision,
            digest,
            f"2026-08-22T12:{35 + min(revision, 24):02d}:04Z",
            *_currentness_key_from_lineage(lineage),
        ),
    )


def _insert_expected_recovery_family(
    connection: sqlite3.Connection,
    family: dict[str, object],
    *,
    replace_existing_head: bool,
) -> None:
    target_head = next(
        row
        for row in family["physical_rows"]
        if row["table"] == REPAIRED_TABLE_ORDER[7]
    )
    for member in family["physical_rows"]:
        if member["table"] not in (
            REPAIRED_TABLE_ORDER[7],
            REPAIRED_TABLE_ORDER[8],
        ):
            _insert_exact_repaired_values(
                connection,
                member["table"],
                member["values"],
            )
    if not replace_existing_head:
        _insert_exact_repaired_values(
            connection,
            REPAIRED_TABLE_ORDER[7],
            target_head["values"],
        )
    else:
        assignments = tuple(
            field
            for field in target_head["values"]
            if field not in REPAIRED_LINEAGE_COLUMNS
        )
        cursor = connection.execute(
            f'UPDATE "{REPAIRED_TABLE_ORDER[7]}" SET '
            + ",".join(f'"{field}"=?' for field in assignments)
            + " WHERE "
            + _LINEAGE_WHERE,
            (
                *(target_head["values"][field] for field in assignments),
                *(target_head["values"][field] for field in REPAIRED_LINEAGE_COLUMNS),
            ),
        )
        assert cursor.rowcount == 1
    receipt = next(
        member
        for member in family["physical_rows"]
        if member["table"] == REPAIRED_TABLE_ORDER[8]
    )
    _insert_exact_repaired_values(
        connection,
        receipt["table"],
        receipt["values"],
    )


def _classify_expected_recovery_family(
    connection: sqlite3.Connection,
    family: dict[str, object],
    expected_head_preimage: dict[str, object] | None,
) -> _RecoveryReadback:
    changes_before = connection.total_changes
    result = _recover_repaired_family(
        connection,
        expected_family=family,
        expected_head_preimage=expected_head_preimage,
        fresh_writer_verified=True,
    )
    assert connection.total_changes == changes_before
    return result


@pytest.mark.parametrize(
    "case_name,expected_result",
    (
        ("complete_exact_root", ("committed_exact", 0)),
        ("complete_exact_successor", ("committed_exact", 1)),
        ("total_initial_family_absence", ("definitely_not_committed", 0)),
        ("total_successor_family_absence", ("definitely_not_committed", 0)),
        ("one_partial_row", ("unresolved", 0)),
        ("one_colliding_identity", ("unresolved", 0)),
        ("changed_selection_head_preimage", ("unresolved", 0)),
        ("malformed_receipt", ("unresolved", 0)),
        ("contradictory_complete_immutable_family", ("unresolved", 0)),
        ("absent_receipt_present_family", ("unresolved", 0)),
    ),
    ids=(
        "complete-root",
        "complete-successor",
        "initial-absence",
        "successor-absence",
        "partial-row",
        "colliding-identity",
        "changed-head-preimage",
        "malformed-receipt",
        "contradictory-family",
        "absent-receipt-present-family",
    ),
)
def test_s41_corr_003_outer_recovery_trichotomy_is_causal(
    case_name: str,
    expected_result: tuple[str, int],
) -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        root = _build_repaired_physical_family(False)
        root_head = next(
            row["values"]
            for row in root["physical_rows"]
            if row["role"] == "selection_head_postimage"
        )
        successor = _build_repaired_successor_family(
            root,
            suffix="recovery-target.0001",
            readiness_present=True,
        )
        expected_head_preimage: dict[str, object] | None = None
        target = root

        if case_name == "complete_exact_root":
            _insert_expected_recovery_family(
                connection, root, replace_existing_head=False
            )
        elif case_name == "complete_exact_successor":
            _insert_expected_recovery_family(
                connection, root, replace_existing_head=False
            )
            _insert_expected_recovery_family(
                connection, successor, replace_existing_head=True
            )
            target = successor
            expected_head_preimage = root_head
        elif case_name == "total_initial_family_absence":
            pass
        elif case_name == "total_successor_family_absence":
            _insert_expected_recovery_family(
                connection, root, replace_existing_head=False
            )
            target = successor
            expected_head_preimage = root_head
        elif case_name == "one_partial_row":
            member = root["physical_rows"][0]
            _insert_exact_repaired_values(
                connection, member["table"], member["values"]
            )
        elif case_name == "one_colliding_identity":
            member = deepcopy(root["physical_rows"][0])
            member["values"]["model_contract_ref"] = "model-contract.collision.0001"
            member["values"]["source_invocation_digest"] = _repaired_row_digest(
                member["table"], member["values"]
            )
            _insert_exact_repaired_values(
                connection, member["table"], member["values"]
            )
        elif case_name == "changed_selection_head_preimage":
            _insert_expected_recovery_family(
                connection, root, replace_existing_head=False
            )
            changed_head = deepcopy(root_head)
            changed_head.update(
                {
                    "current_proposal_ref": "proposal.changed-head.0001",
                    "current_disposition_ref": "disposition.changed-head.0001",
                    "head_revision": 1,
                    "updated_at": "2026-08-22T12:35:06Z",
                }
            )
            changed_head["head_digest"] = _repaired_row_digest(
                REPAIRED_TABLE_ORDER[7], changed_head
            )
            connection.commit()
            connection.execute("PRAGMA foreign_keys=OFF")
            assignments = tuple(
                field
                for field in changed_head
                if field not in REPAIRED_LINEAGE_COLUMNS
            )
            connection.execute(
                f'UPDATE "{REPAIRED_TABLE_ORDER[7]}" SET '
                + ",".join(f'"{field}"=?' for field in assignments)
                + " WHERE "
                + _LINEAGE_WHERE,
                (
                    *(changed_head[field] for field in assignments),
                    *(changed_head[field] for field in REPAIRED_LINEAGE_COLUMNS),
                ),
            )
            target = successor
            expected_head_preimage = root_head
        elif case_name == "malformed_receipt":
            receipt = deepcopy(root["receipt"])
            receipt["values"]["receipt_digest"] = "A" * 64
            connection.execute("PRAGMA foreign_keys=OFF")
            connection.execute("PRAGMA ignore_check_constraints=ON")
            _insert_exact_repaired_values(
                connection, receipt["table"], receipt["values"]
            )
        elif case_name == "contradictory_complete_immutable_family":
            connection.commit()
            connection.execute("PRAGMA foreign_keys=OFF")
            for member in root["physical_rows"]:
                if member["table"] != REPAIRED_TABLE_ORDER[7]:
                    _insert_exact_repaired_values(
                        connection, member["table"], member["values"]
                    )
        elif case_name == "absent_receipt_present_family":
            for member in root["physical_rows"]:
                if member["table"] != REPAIRED_TABLE_ORDER[8]:
                    _insert_exact_repaired_values(
                        connection, member["table"], member["values"]
                    )
        else:
            raise AssertionError(case_name)
        connection.commit()
        observed = _classify_expected_recovery_family(
            connection,
            target,
            expected_head_preimage,
        )
        assert observed[:2] == expected_result
        if observed.classification == "committed_exact":
            assert observed.result == target["replay_result"]
            assert observed.result is not target["replay_result"]
        else:
            assert observed.result is None
    finally:
        connection.close()


def test_s41_corr_003_recovery_identity_inventory_is_complete_and_writer_gated() -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        owner = _parse_repaired_owner()["recovery_query_and_proof"]
        assert owner["outer_result_vocabulary"] == (
            "committed_exact",
            "definitely_not_committed",
            "unresolved",
        )
        assert owner["identity_inventory"] == (
            INCORPORATED_NINE_FINDING_RECOVERY_IDENTITY_FIELDS
        )
        assert owner["identity_probe_count"] == 29
        assert owner["immutable_identity_probe_count"] == 25
        assert owner[
            "identity_inventory_equals_all_declared_primary_and_unique_constraints"
        ] is True
        assert owner["fresh_writer_verification_required"] is True
        assert owner["automatic_semantic_retry_authorized"] is False
        assert owner["recovery_writes_or_commits"] is False
        assert tuple(INCORPORATED_NINE_FINDING_RECOVERY_IDENTITY_FIELDS) == (
            REPAIRED_TABLE_ORDER
        )
        assert sum(
            len(identities)
            for identities in INCORPORATED_NINE_FINDING_RECOVERY_IDENTITY_FIELDS.values()
        ) == 29
        assert sum(
            len(INCORPORATED_NINE_FINDING_RECOVERY_IDENTITY_FIELDS[table])
            for table in REPAIRED_IMMUTABLE_TABLES
        ) == 25
        assert tuple(REPAIRED_RECOVERY_IDENTITY_FIELDS) == REPAIRED_TABLE_ORDER
        assert sum(
            len(identities)
            for identities in REPAIRED_RECOVERY_IDENTITY_FIELDS.values()
        ) == 30
        for table in REPAIRED_TABLE_ORDER:
            assert set(REPAIRED_RECOVERY_IDENTITY_FIELDS[table]) == (
                _declared_unique_column_sets(connection, table)
            )
        family = _build_repaired_physical_family(False)
        assert _recover_repaired_family(
            connection,
            expected_family=family,
            expected_head_preimage=None,
            fresh_writer_verified=False,
        ) == _RecoveryReadback("unresolved", 0, None)
        assert _recover_repaired_family(
            connection,
            expected_family=family,
            expected_head_preimage=None,
            fresh_writer_verified=1,
        ) == _RecoveryReadback("unresolved", 0, None)
    finally:
        connection.close()


def test_recovery_uses_complete_database_results_and_probes_exact_postimage() -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        root = _insert_sqlite_golden_family(connection, False)
        connection.commit()
        assert _recover_repaired_disposition(
            connection,
            lineage=root["lineage"],
            receipt_disposition_ref=root["disposition_ref"],
            receipt_revision=0,
            receipt_digest=root["disposition_digest"],
        ) == ("committed_exact", 0)

        successor_ref, successor_digest = _insert_sqlite_successor(
            connection,
            lineage=root["lineage"],
            predecessor_ref=root["disposition_ref"],
            predecessor_revision=0,
            predecessor_digest=root["selection_head_postimage_digest"],
            revision=1,
            suffix="advanced",
        )
        connection.commit()
        # Even an exact receipt/head match probes and rejects the dangling,
        # unadvanced successor.
        assert _recover_repaired_disposition(
            connection,
            lineage=root["lineage"],
            receipt_disposition_ref=root["disposition_ref"],
            receipt_revision=0,
            receipt_digest=root["disposition_digest"],
        ) == ("unresolved", 0)

        _advance_sqlite_head(
            connection,
            root["lineage"],
            successor_ref,
            1,
            successor_digest,
        )
        connection.commit()
        assert _recover_repaired_disposition(
            connection,
            lineage=root["lineage"],
            receipt_disposition_ref=root["disposition_ref"],
            receipt_revision=0,
            receipt_digest=root["disposition_digest"],
        ) == ("committed_exact", 1)
    finally:
        connection.close()


def test_complete_lineage_inventory_rejects_disconnected_database_row() -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        root = _insert_sqlite_golden_family(connection, False)
        connection.commit()
        connection.execute("PRAGMA foreign_keys=OFF")
        proposal_ref = _insert_sqlite_proposal_prerequisites(connection, "disconnected")
        _insert_sqlite_disposition(
            connection,
            lineage=root["lineage"],
            proposal_ref=proposal_ref,
            disposition_ref="disposition.disconnected.2",
            supersedes_ref="disposition.missing.1",
            prior_revision=1,
            prior_digest="9" * 64,
            resulting_revision=2,
            selection_head_postimage_digest="8" * 64,
        )
        connection.commit()
        connection.execute("PRAGMA foreign_keys=ON")
        assert _recover_repaired_disposition(
            connection,
            lineage=root["lineage"],
            receipt_disposition_ref=root["disposition_ref"],
            receipt_revision=0,
            receipt_digest=root["disposition_digest"],
        )[0] == "unresolved"
    finally:
        connection.close()


def _install_malformed_recovery_fixture() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    disposition_columns = ",".join(
        f'"{field}"' for field, _kind in REPAIRED_TABLE_COLUMNS[REPAIRED_TABLE_ORDER[6]]
    )
    head_columns = ",".join(
        f'"{field}"' for field, _kind in REPAIRED_TABLE_COLUMNS[REPAIRED_TABLE_ORDER[7]]
    )
    connection.executescript(
        f"""
        CREATE TABLE development_pre_execution_dispositions ({disposition_columns});
        CREATE TABLE development_pre_execution_selection_heads ({head_columns});
        """
    )
    return connection


def _insert_unconstrained_recovery_values(
    connection: sqlite3.Connection,
    table: str,
    values: dict[str, object],
) -> None:
    columns = tuple(name for name, _kind in REPAIRED_TABLE_COLUMNS[table])
    assert tuple(values) == columns
    connection.execute(
        f'INSERT INTO "{table}" ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})',
        tuple(values.values()),
    )


def _f2_recovery_outcome_after_mutation(mutate: object) -> tuple[str, int]:
    family = _build_repaired_physical_family(False)
    by_role = {
        member["role"]: deepcopy(member["values"])
        for member in family["physical_rows"]
    }
    disposition = by_role["coordinator_disposition"]
    head = by_role["selection_head_postimage"]
    mutate(disposition, head)
    head["head_digest"] = _repaired_row_digest(REPAIRED_TABLE_ORDER[7], head)
    disposition["selection_head_postimage_digest"] = head["head_digest"]
    disposition["disposition_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[6], disposition
    )
    connection = _install_malformed_recovery_fixture()
    try:
        _insert_unconstrained_recovery_values(
            connection,
            REPAIRED_TABLE_ORDER[6],
            disposition,
        )
        _insert_unconstrained_recovery_values(
            connection,
            REPAIRED_TABLE_ORDER[7],
            head,
        )
        connection.commit()
        return _recover_repaired_disposition(
            connection,
            lineage=tuple(
                disposition[field] for field in REPAIRED_LINEAGE_COLUMNS
            ),
            receipt_disposition_ref=disposition["disposition_ref"],
            receipt_revision=disposition["resulting_selection_head_revision"],
            receipt_digest=disposition["disposition_digest"],
        )
    finally:
        connection.close()


def test_f2_unknown_disposition_and_head_mismatch_recover_unresolved() -> None:
    def unknown(disposition: dict[str, object], head: dict[str, object]) -> None:
        disposition["disposition"] = "semantically_invalid"
        head["current_disposition"] = "semantically_invalid"

    def mismatch(_disposition: dict[str, object], head: dict[str, object]) -> None:
        head["current_disposition"] = "deferred"

    assert _f2_recovery_outcome_after_mutation(unknown) == ("unresolved", 0)
    assert _f2_recovery_outcome_after_mutation(mismatch) == ("unresolved", 0)


def test_f2_head_proposal_mismatch_recovers_unresolved() -> None:
    def mismatch(_disposition: dict[str, object], head: dict[str, object]) -> None:
        head["current_proposal_ref"] = "proposal.recovery-mismatch.0001"

    assert _f2_recovery_outcome_after_mutation(mismatch) == ("unresolved", 0)


@pytest.mark.parametrize(
    "field,bad_value",
    (
        ("supersedes_disposition_ref", "disposition.forbidden.root-parent"),
        ("expected_selection_head_revision", 0),
        ("expected_selection_head_digest", "a" * 64),
        ("prior_selection_head_revision", 0),
        ("prior_selection_head_digest", "b" * 64),
    ),
)
def test_f2_each_invalid_root_shape_recovers_unresolved(
    field: str,
    bad_value: object,
) -> None:
    def mutate(disposition: dict[str, object], _head: dict[str, object]) -> None:
        disposition[field] = bad_value

    assert _f2_recovery_outcome_after_mutation(mutate) == ("unresolved", 0)


def test_branched_database_history_is_never_committed_exact() -> None:
    connection = _install_malformed_recovery_fixture()
    try:
        family = _build_repaired_physical_family(False)
        by_role = {member["role"]: member["values"] for member in family["physical_rows"]}
        lineage = _sqlite_lineage("malformed-branch")
        root_head = deepcopy(by_role["selection_head_postimage"])
        root_head.update(dict(zip(REPAIRED_LINEAGE_COLUMNS, lineage, strict=True)))
        root_head["current_disposition_ref"] = "root"
        root_head["head_revision"] = 0
        root_head["head_digest"] = _repaired_row_digest(REPAIRED_TABLE_ORDER[7], root_head)
        current_head = deepcopy(root_head)
        current_head["current_disposition_ref"] = "child.one"
        current_head["head_revision"] = 1
        current_head["head_digest"] = _repaired_row_digest(REPAIRED_TABLE_ORDER[7], current_head)

        def disposition(
            ref: str,
            supersedes: str | None,
            prior_revision: int,
            prior_digest: str | None,
            resulting_revision: int,
            head_digest: str,
        ) -> dict[str, object]:
            values = deepcopy(by_role["coordinator_disposition"])
            values.update(dict(zip(REPAIRED_LINEAGE_COLUMNS, lineage, strict=True)))
            values.update(
                {
                    "disposition_ref": ref,
                    "supersedes_disposition_ref": supersedes,
                    "expected_selection_head_revision": None if resulting_revision == 0 else prior_revision,
                    "expected_selection_head_digest": None if resulting_revision == 0 else prior_digest,
                    "prior_selection_head_revision": prior_revision,
                    "prior_selection_head_digest": prior_digest,
                    "resulting_selection_head_revision": resulting_revision,
                    "selection_head_postimage_digest": head_digest,
                }
            )
            values["disposition_digest"] = _repaired_row_digest(REPAIRED_TABLE_ORDER[6], values)
            return values

        root = disposition("root", None, -1, None, 0, root_head["head_digest"])
        first = disposition("child.one", "root", 0, root_head["head_digest"], 1, current_head["head_digest"])
        second = disposition("child.two", "root", 0, root_head["head_digest"], 1, "3" * 64)
        for values in (root, first, second):
            _insert_unconstrained_recovery_values(
                connection, REPAIRED_TABLE_ORDER[6], values
            )
        _insert_unconstrained_recovery_values(
            connection, REPAIRED_TABLE_ORDER[7], current_head
        )
        connection.commit()
        result = _recover_repaired_disposition(
            connection,
            lineage=lineage,
            receipt_disposition_ref="root",
            receipt_revision=0,
            receipt_digest=root["disposition_digest"],
        )
        assert result == ("unresolved", 1)
    finally:
        connection.close()


@pytest.mark.parametrize(
    "table_role,field,bad_value",
    (
        ("coordinator_disposition", "prior_selection_head_revision", -1.0),
        ("coordinator_disposition", "resulting_selection_head_revision", 0.0),
        ("selection_head_postimage", "head_revision", 0.0),
        ("selection_head_postimage", "head_revision", True),
    ),
    ids=("real-prior-minus-one", "real-result-zero", "real-head-zero", "bool-head"),
)
def test_malformed_numeric_revision_aliases_are_unresolved(
    table_role: str,
    field: str,
    bad_value: object,
) -> None:
    connection = _install_malformed_recovery_fixture()
    try:
        family = _build_repaired_physical_family(False)
        by_role = {
            member["role"]: deepcopy(member["values"])
            for member in family["physical_rows"]
        }
        disposition = by_role["coordinator_disposition"]
        head = by_role["selection_head_postimage"]
        target = disposition if table_role == "coordinator_disposition" else head
        target[field] = bad_value
        if target is head:
            head["head_digest"] = _repaired_row_digest(REPAIRED_TABLE_ORDER[7], head)
            disposition["selection_head_postimage_digest"] = head["head_digest"]
        disposition["disposition_digest"] = _repaired_row_digest(
            REPAIRED_TABLE_ORDER[6], disposition
        )
        _insert_unconstrained_recovery_values(
            connection, REPAIRED_TABLE_ORDER[6], disposition
        )
        _insert_unconstrained_recovery_values(
            connection, REPAIRED_TABLE_ORDER[7], head
        )
        lineage = tuple(disposition[field] for field in REPAIRED_LINEAGE_COLUMNS)
        assert _recover_repaired_disposition(
            connection,
            lineage=lineage,
            receipt_disposition_ref=disposition["disposition_ref"],
            receipt_revision=0,
            receipt_digest=disposition["disposition_digest"],
        ) == ("unresolved", 0)
    finally:
        connection.close()


@pytest.mark.parametrize(
    "table",
    (REPAIRED_TABLE_ORDER[6], REPAIRED_TABLE_ORDER[7]),
    ids=("disposition-extra-field", "head-extra-field"),
)
def test_unknown_recovery_table_field_is_unresolved(table: str) -> None:
    connection = _install_malformed_recovery_fixture()
    try:
        family = _build_repaired_physical_family(False)
        by_role = {
            member["role"]: member["values"] for member in family["physical_rows"]
        }
        disposition = by_role["coordinator_disposition"]
        head = by_role["selection_head_postimage"]
        _insert_unconstrained_recovery_values(
            connection, REPAIRED_TABLE_ORDER[6], disposition
        )
        _insert_unconstrained_recovery_values(
            connection, REPAIRED_TABLE_ORDER[7], head
        )
        connection.execute(f'ALTER TABLE "{table}" ADD COLUMN unexpected_field')
        lineage = tuple(disposition[field] for field in REPAIRED_LINEAGE_COLUMNS)
        assert _recover_repaired_disposition(
            connection,
            lineage=lineage,
            receipt_disposition_ref=disposition["disposition_ref"],
            receipt_revision=0,
            receipt_digest=disposition["disposition_digest"],
        ) == ("unresolved", 0)
    finally:
        connection.close()


def test_recovery_reads_transition_257_as_overflow_sentinel() -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        root = _insert_sqlite_golden_family(connection, False)
        predecessor_ref = root["disposition_ref"]
        predecessor_digest = root["selection_head_postimage_digest"]
        for revision in range(1, 258):
            predecessor_ref, predecessor_digest = _insert_sqlite_successor(
                connection,
                lineage=root["lineage"],
                predecessor_ref=predecessor_ref,
                predecessor_revision=revision - 1,
                predecessor_digest=predecessor_digest,
                revision=revision,
                suffix=f"overflow-{revision:03d}",
            )
        _advance_sqlite_head(
            connection,
            root["lineage"],
            predecessor_ref,
            257,
            predecessor_digest,
        )
        connection.commit()
        assert _recover_repaired_disposition(
            connection,
            lineage=root["lineage"],
            receipt_disposition_ref=root["disposition_ref"],
            receipt_revision=0,
            receipt_digest=root["disposition_digest"],
        ) == ("unresolved", 257)
    finally:
        connection.close()


def test_recovery_query_inventory_is_closed_bounded_and_database_owned() -> None:
    owner = _parse_repaired_owner()["recovery_query_and_proof"]
    assert owner["input_authority"] == (
        "complete database-query results inside one fenced read-only recovery transaction"
    )
    assert owner["caller_selected_predecessor_subset_permitted"] is False
    assert owner["maximum_predecessor_transitions"] == 256
    assert owner["overflow_sentinel_read_number"] == 257
    assert _HEAD_QUERY.endswith("LIMIT 2")
    assert _DISPOSITION_QUERY.endswith("LIMIT 2")
    assert _SUCCESSOR_QUERY.endswith("LIMIT 2")
    assert _INVENTORY_QUERY.endswith("LIMIT 258")
    assert owner["recovery_calls_clock"] is False
    assert "exact built-in scalars" in owner["exact_row_grammar_before_relations"]
    assert "exact finite enum membership" in owner["exact_row_grammar_before_relations"]
    assert "exact root-or-successor shape" in owner["exact_row_grammar_before_relations"]
    assert "REAL numeric aliases invalid" in owner["exact_row_grammar_before_relations"]
    assert "current head disposition value equals the exact referenced disposition row value" in owner[
        "verified_relations"
    ]
    assert "current head proposal ref equals the exact referenced disposition row proposal ref" in owner[
        "verified_relations"
    ]
    assert "head_proposal_mismatch" in owner["unresolved_conditions"]


def test_repaired_c2b3d_basis_hash_is_exact_and_production_independent() -> None:
    vector = _section_39_vector()
    digest = hashlib.sha256(_s41_canonical_bytes(vector)).hexdigest()
    assert digest == "fac7e895942089ee6fd6cb172f056b5f4b06e76cbb2dccee29192ffa7be63f1b"
    assert digest == _parse_repaired_owner()["contract_identity"][
        "c2b3d_family_golden_vector_canonical_sha256"
    ]


def test_repaired_owner_asserts_exact_causal_oracle_posture() -> None:
    causal = _parse_repaired_owner()["causal_oracle"]
    assert causal == {
        "validator_result": "exact finite success value or _ContractViolation with one exact reason",
        "generic_assertion_credit": False,
        "named_mutant_must_reach_intended_predicate": True,
        "effect_fence_expiry_keeps_attempt_fence_valid": True,
        "receipt_member_checked_before_rank_inventory": True,
        "raw_byte_failure_proves_only_byte_identity": True,
        "exact_violation_reasons": INCORPORATED_NINE_FINDING_VIOLATION_REASONS,
    }


def test_nine_finding_repair_owner_is_exactly_bound_to_the_direct_contract() -> None:
    repair = _parse_repaired_owner()["nine_finding_repair"]
    assert tuple(repair) == (
        "selection_head_update_trigger",
        "post_execution_evidence_transaction_gate",
        "common_envelope_cross_row_binding",
        "shape_before_relations",
        "canonical_C2B3D_lineage",
        "complete_cognitive_mutation_command",
        "persisted_observation_and_chronology",
        "historical_receipt_after_later_CAS",
        "independent_digest_oracle",
    )
    head = repair["selection_head_update_trigger"]
    assert head["immutable_field_order"] == REPAIRED_SELECTION_HEAD_IMMUTABLE_FIELDS
    assert head["comparison_template"] == 'OLD."{field}" IS NOT NEW."{field}"'
    assert head["predicate_join"] == " OR "
    assert head["timing"] == "BEFORE UPDATE"
    assert head["mutable_CAS_field_order"] == REPAIRED_SELECTION_HEAD_MUTABLE_CAS_FIELDS
    assert head["valid_CAS_recomputes_exact_head_digest"] is True

    post_gate = repair["post_execution_evidence_transaction_gate"]
    assert post_gate["query_order"] == REPAIRED_POST_EVIDENCE_TRANSACTION_QUERIES
    assert post_gate["complete_role_rank_ordinal_required_order"] == tuple(
        (role, rank, 0, int(required))
        for role, rank, required in REPAIRED_POST_EXECUTION_EVIDENCE_SPECS
    )
    assert post_gate["accepted_cardinalities"] == (0, 9)
    assert post_gate["rejected_cardinalities"] == tuple(range(1, 9))
    assert "before receipt disclosure or COMMIT" in post_gate["position"]
    assert "rollback" in post_gate["gate_false_or_unverifiable"]

    common = repair["common_envelope_cross_row_binding"]
    assert common["coherent_phase_triples"] == tuple(
        (phase, phase, phase) for phase in PHASES
    )
    assert common["all_other_phase_triples_accepted"] is False
    assert common["post_execution_common_envelope_without_preexecution_context_row"] is True
    assert common["unconditional_common_proposal_to_preexecution_context_foreign_key"] is False

    shape = repair["shape_before_relations"]
    assert shape["exact_recursive_comparison_after_shape_only"] is True
    assert shape["malformed_input_clock_result_family_write_or_commit_count"] == 0
    assert "every key type is exactly str" in shape["order"][1]

    lineage = repair["canonical_C2B3D_lineage"]
    assert lineage["field_order"] == REPAIRED_C2B3D_LINEAGE_FIELDS
    assert lineage["every_repeated_coordinate_and_digest_checked"] is True
    assert lineage["later_valid_CAS_preserves_lineage"] is True

    command = repair["complete_cognitive_mutation_command"]
    assert command["digest_domain"] == REPAIRED_COMMAND_DOMAIN
    assert command["field_kind_source_order"] == REPAIRED_COMMAND_FIELD_SPECS
    assert command["identity_excludes_only"] == ("mutation_command_digest",)
    assert command["digest_consumers"] == (
        "mutation-ref reuse comparison",
        "receipt binding",
        "result binding",
        "fresh and replay verification",
        "recovery verification",
    )

    chronology = repair["persisted_observation_and_chronology"]
    assert chronology["replay_or_recovery_clock_calls"] == 0
    assert chronology["distinct_valid_observations_produce_distinct_complete_families"] is True
    assert chronology["shared_decision_time_destinations"] == (
        "selection head updated_at",
        "receipt committed_at",
        "result projection recorded_at",
        "fresh result recorded_at",
        "replay result recorded_at",
    )

    recovery = repair["historical_receipt_after_later_CAS"]
    assert recovery["maximum_transitions"] == 256
    assert recovery["overflow_sentinel_transition"] == 257
    assert recovery["clock_write_COMMIT_or_semantic_retry"] is False
    assert "original receipt-owned result" in recovery["committed_result"]

    oracle = repair["independent_digest_oracle"]
    assert oracle["separate_implementation"] is True
    assert oracle["construction_helpers_called"] == ()
    assert oracle["forbidden_dependencies"][:2] == (
        "_s41_digest",
        "_repaired_row_digest",
    )
    assert oracle["ledger_variants"] == (
        "pre-execution readiness absent",
        "pre-execution readiness present",
        "post-execution coherent common envelope with zero evidence",
        "post-execution coherent common envelope with complete nine-role evidence",
        "private artifact canonical identity",
    )


def _repair_alternate_scalar(value: object, kind: str) -> object:
    if kind.startswith("literal:"):
        return f"{value}.foreign"
    if kind in ("nullable_nonnegative_int", "nonnegative_int", "positive_int"):
        return 1 if value is None else value + 1
    if kind == "nullable_sha256":
        return "f" * 64 if value != "f" * 64 else "e" * 64
    if kind == "nullable_safe_ref":
        return "disposition.foreign.valid.0001" if value is None else f"{value}.foreign"
    if kind == "sha256":
        return "f" * 64 if value != "f" * 64 else "e" * 64
    if kind == "pre_execution_disposition":
        return "deferred" if value != "deferred" else "blocked"
    if kind == "reason_code":
        return "selection.foreign_valid"
    if kind == "safe_ref":
        return f"{value}.foreign"
    raise AssertionError((value, kind))


REVISED_LAYER_B_TARGET_EXCLUSIVE_FIELDS = (
    "program_version_number",
    "semantic_attempt_digest",
    "attempt_number",
    "candidate_ref",
    "basis_decision_ref",
    "basis_decision_digest",
    "work_spec_ref",
    "work_spec_digest",
    "work_spec_safe_projection_digest",
    "effect_intent_digest",
    "author_command_digest",
    "standing_grant_ref",
    "standing_grant_digest",
    "attempt_authorization_ref",
    "attempt_authorization_digest",
    "effect_authorization_ref",
    "effect_authorization_digest",
    "attempt_fence_digest",
    "effect_fence_digest",
    "delivery_envelope_digest",
    "delivery_attempt_digest",
    "authority_evaluation_ref",
    "authority_evaluation_digest",
)
REVISED_LAYER_B_OVERLAPPING_FIELDS = (
    "program_ref",
    "program_version_ref",
    "accepted_intent_revision_ref",
    "work_item_ref",
    "work_item_revision_ref",
    "semantic_attempt_ref",
    "effect_intent_ref",
    "author_command_ref",
    "attempt_fence_ref",
    "effect_fence_ref",
    "delivery_attempt_ref",
)
REVISED_LAYER_B_ALTERNATE_PARENT_ISOLATABLE = {
    field: field not in ("program_ref", "work_item_ref")
    for field in REVISED_LAYER_B_OVERLAPPING_FIELDS
}
REVISED_LAYER_B_NONISOLATABLE_EXPLANATIONS = {
    "program_ref": (
        "the retained (program_ref,supersedes_disposition_ref) parent key "
        "requires the original disposition_ref under the alternate program_ref, "
        "but PRIMARY KEY(disposition_ref) globally reserves that ref for the "
        "original predecessor"
    ),
    "work_item_ref": (
        "the retained (program_ref,work_item_ref,work_item_revision_ref) parent "
        "key requires the unchanged work_item_revision_ref under the alternate "
        "work_item_ref, but PRIMARY KEY(work_item_revision_ref) globally reserves "
        "that ref for the original work-item revision"
    ),
}


def _extract_installed_predecessor_relation(
    connection: sqlite3.Connection,
) -> tuple[tuple[str, ...], str, tuple[str, ...], str, str, str]:
    disposition_table = REPAIRED_TABLE_ORDER[6]
    matches = tuple(
        relation
        for relation in _observed_sqlite_foreign_keys(
            connection,
            disposition_table,
        )
        if relation[1] == disposition_table
        and len(relation[0]) == len(REPAIRED_C2B3D_LINEAGE_FIELDS) + 3
        and len(relation[2]) == len(REPAIRED_C2B3D_LINEAGE_FIELDS) + 3
    )
    assert len(matches) == 1
    return matches[0]


def _foreign_key_specification_for_observed_relation(
    relation: tuple[tuple[str, ...], str, tuple[str, ...], str, str, str],
) -> tuple[tuple[str, ...], str, tuple[str, ...], str]:
    child, parent_table, parent, on_update, on_delete, match = relation
    assert (on_update, on_delete, match) == ("RESTRICT", "RESTRICT", "NONE")
    matches = tuple(
        specification
        for specification in REPAIRED_TABLE_FOREIGN_KEYS[REPAIRED_TABLE_ORDER[6]]
        if specification[:3] == (child, parent_table, parent)
    )
    assert len(matches) == 1
    return matches[0]


def _ablated_repaired_foreign_keys(
    relation: tuple[tuple[str, ...], str, tuple[str, ...], str, str, str],
) -> dict[
    str,
    tuple[tuple[tuple[str, ...], str, tuple[str, ...], str], ...],
]:
    target = _foreign_key_specification_for_observed_relation(relation)
    result = {
        table: tuple(
            specification
            for specification in specifications
            if not (table == REPAIRED_TABLE_ORDER[6] and specification == target)
        )
        for table, specifications in REPAIRED_TABLE_FOREIGN_KEYS.items()
    }
    assert sum(
        len(specifications) for specifications in REPAIRED_TABLE_FOREIGN_KEYS.values()
    ) - sum(len(specifications) for specifications in result.values()) == 1
    return result


def _retained_overlap_relations(
    field: str,
) -> tuple[tuple[tuple[str, ...], str, tuple[str, ...], str], ...]:
    return tuple(
        relation
        for relation in REPAIRED_BASE_FOREIGN_KEYS[REPAIRED_TABLE_ORDER[6]]
        if field in relation[0]
    )


def _layer_a_relation_schema(
    relation: tuple[tuple[str, ...], str, tuple[str, ...], str, str, str],
    column_types: dict[str, str],
    *,
    include_relation: bool,
) -> sqlite3.Connection:
    local_fields, _parent_table, referenced_fields, _update, _delete, _match = relation
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute(
        "CREATE TABLE extracted_parent ("
        + ",".join(
            f'"{field}" {column_types[field]}' for field in referenced_fields
        )
        + ",UNIQUE("
        + ",".join(f'"{field}"' for field in referenced_fields)
        + ")) STRICT"
    )
    definitions = [
        f'"{field}" {column_types[field]}' for field in local_fields
    ]
    if include_relation:
        definitions.append(
            "FOREIGN KEY("
            + ",".join(f'"{field}"' for field in local_fields)
            + ") REFERENCES extracted_parent("
            + ",".join(f'"{field}"' for field in referenced_fields)
            + ") ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE "
            "INITIALLY IMMEDIATE"
        )
    connection.execute(
        "CREATE TABLE extracted_child (" + ",".join(definitions) + ") STRICT"
    )
    return connection


def _insert_layer_a_parent_and_child(
    connection: sqlite3.Connection,
    relation: tuple[tuple[str, ...], str, tuple[str, ...], str, str, str],
    parent_values: dict[str, object],
    child_values: dict[str, object],
) -> None:
    local_fields, _parent_table, referenced_fields, _update, _delete, _match = relation
    connection.execute(
        "INSERT INTO extracted_parent VALUES ("
        + ",".join("?" for _field in referenced_fields)
        + ")",
        tuple(parent_values[field] for field in referenced_fields),
    )
    connection.execute(
        "INSERT INTO extracted_child VALUES ("
        + ",".join("?" for _field in local_fields)
        + ")",
        tuple(child_values[field] for field in local_fields),
    )


@pytest.fixture(scope="module")
def a2_revised_extracted_predecessor_relation() -> tuple[
    tuple[tuple[str, ...], str, tuple[str, ...], str, str, str],
    dict[str, str],
]:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        relation = _extract_installed_predecessor_relation(connection)
        column_types = {
            row[1]: row[2]
            for row in connection.execute(
                f'PRAGMA table_info("{REPAIRED_TABLE_ORDER[6]}")'
            )
        }
        yield relation, column_types
    finally:
        connection.close()


REPAIRED_LINEAGE_MUTATION_EXPECTATIONS = tuple(
    (
        field,
        "extracted_target_relation_plus_integrated_overlap",
        "SQLITE_CONSTRAINT_FOREIGNKEY",
        ("unresolved", 0),
    )
    for field in REPAIRED_C2B3D_LINEAGE_FIELDS
)


@pytest.mark.parametrize(
    "field,first_predicate,sqlite_result,recovery_result",
    REPAIRED_LINEAGE_MUTATION_EXPECTATIONS,
    ids=REPAIRED_C2B3D_LINEAGE_FIELDS,
)
def test_reaudit_each_full_lineage_coordinate_is_physically_and_recovery_bound(
    field: str,
    first_predicate: str,
    sqlite_result: str,
    recovery_result: tuple[str, int],
) -> None:
    assert first_predicate == "extracted_target_relation_plus_integrated_overlap"
    predecessor_spec = REPAIRED_SUPPLEMENTAL_FOREIGN_KEYS[
        REPAIRED_TABLE_ORDER[6]
    ][0]
    assert predecessor_spec[0] == (
        *REPAIRED_C2B3D_LINEAGE_FIELDS,
        "supersedes_disposition_ref",
        "prior_selection_head_revision",
        "prior_selection_head_digest",
    )
    assert predecessor_spec[2] == (
        *REPAIRED_C2B3D_LINEAGE_FIELDS,
        "disposition_ref",
        "resulting_selection_head_revision",
        "selection_head_postimage_digest",
    )

    root = _build_repaired_physical_family(False)
    successor = _build_repaired_successor_family(
        root,
        suffix=f"lineage-{field.replace('_', '-')}",
    )
    root_by_role = {row["role"]: row for row in root["physical_rows"]}
    successor_by_role = {
        row["role"]: row for row in successor["physical_rows"]
    }
    mutated_disposition = deepcopy(
        successor_by_role["coordinator_disposition"]["values"]
    )
    kind = dict(REPAIRED_C2B3D_LINEAGE_FIELD_SPECS)[field]
    mutated_disposition[field] = _repair_alternate_scalar(
        mutated_disposition[field],
        kind,
    )
    mutated_disposition["disposition_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[6],
        mutated_disposition,
    )

    connection, _inventory = _install_repaired_temporary_schema()
    extracted_relation = _extract_installed_predecessor_relation(connection)
    try:
        for member in root["physical_rows"]:
            _insert_exact_repaired_values(
                connection,
                member["table"],
                member["values"],
            )
        for member in successor["physical_rows"]:
            if member["role"] == "coordinator_disposition":
                break
            _insert_exact_repaired_values(
                connection,
                member["table"],
                member["values"],
            )
        with pytest.raises(sqlite3.IntegrityError) as sqlite_caught:
            _insert_exact_repaired_values(
                connection,
                REPAIRED_TABLE_ORDER[6],
                mutated_disposition,
            )
        assert sqlite_caught.value.sqlite_errorname == sqlite_result
        assert str(sqlite_caught.value) == "FOREIGN KEY constraint failed"
        assert connection.in_transaction is True
        assert connection.execute(
            f'SELECT count(*) FROM "{REPAIRED_TABLE_ORDER[6]}" '
            "WHERE disposition_ref=?",
            (mutated_disposition["disposition_ref"],),
        ).fetchone() == (0,)
        connection.rollback()
        assert connection.in_transaction is False
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()

    ablated_foreign_keys = _ablated_repaired_foreign_keys(extracted_relation)
    ablated_ddl = _build_repaired_table_ddl(ablated_foreign_keys)
    ablated, _inventory = _install_repaired_temporary_schema(
        repaired_table_ddl=ablated_ddl,
    )
    try:
        for member in root["physical_rows"]:
            _insert_exact_repaired_values(
                ablated,
                member["table"],
                member["values"],
            )
        for member in successor["physical_rows"]:
            if member["role"] == "coordinator_disposition":
                break
            _insert_exact_repaired_values(
                ablated,
                member["table"],
                member["values"],
            )
        if field in REVISED_LAYER_B_TARGET_EXCLUSIVE_FIELDS:
            _insert_exact_repaired_values(
                ablated,
                REPAIRED_TABLE_ORDER[6],
                mutated_disposition,
            )
            ablated.commit()
            assert ablated.execute(
                f'SELECT count(*) FROM "{REPAIRED_TABLE_ORDER[6]}" '
                "WHERE disposition_ref=?",
                (mutated_disposition["disposition_ref"],),
            ).fetchone() == (1,)
            assert ablated.execute("PRAGMA foreign_key_check").fetchall() == []
        else:
            assert field in REVISED_LAYER_B_OVERLAPPING_FIELDS
            with pytest.raises(sqlite3.IntegrityError) as ablated_caught:
                _insert_exact_repaired_values(
                    ablated,
                    REPAIRED_TABLE_ORDER[6],
                    mutated_disposition,
                )
            assert ablated_caught.value.sqlite_errorname == (
                "SQLITE_CONSTRAINT_FOREIGNKEY"
            )
            assert _retained_overlap_relations(field)
            ablated.rollback()
            assert ablated.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        if ablated.in_transaction:
            ablated.rollback()
        ablated.close()

    malformed = _install_malformed_recovery_fixture()
    try:
        root_disposition = root_by_role["coordinator_disposition"]["values"]
        successor_head = successor_by_role["selection_head_postimage"]["values"]
        for table, values in (
            (REPAIRED_TABLE_ORDER[6], root_disposition),
            (REPAIRED_TABLE_ORDER[6], mutated_disposition),
            (REPAIRED_TABLE_ORDER[7], successor_head),
        ):
            _insert_unconstrained_recovery_values(
                malformed,
                table,
                values,
            )
        malformed.commit()
        root_lineage = tuple(
            root_disposition[name]
            for name in REPAIRED_C2B3D_LINEAGE_FIELDS
        )
        assert _recover_repaired_disposition(
            malformed,
            lineage=root_lineage,
            receipt_disposition_ref=root_disposition["disposition_ref"],
            receipt_revision=root_disposition[
                "resulting_selection_head_revision"
            ],
            receipt_digest=root_disposition["disposition_digest"],
        ) == recovery_result
    finally:
        malformed.close()


@pytest.mark.parametrize(
    "field",
    REPAIRED_SELECTION_HEAD_ALL_IMMUTABLE_FIELDS,
)
def test_nine_repair_selection_head_trigger_rejects_each_immutable_field(
    field: str,
) -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        inserted = _insert_sqlite_golden_family(connection, False)
        connection.commit()
        head_fields = tuple(
            name for name, _kind in REPAIRED_TABLE_COLUMNS[REPAIRED_TABLE_ORDER[7]]
        )
        before = connection.execute(
            f'SELECT {",".join(head_fields)} FROM "{REPAIRED_TABLE_ORDER[7]}" '
            f"WHERE {_LINEAGE_WHERE}",
            inserted["lineage"],
        ).fetchone()
        assert before is not None
        current = dict(zip(head_fields, before, strict=True))[field]
        replacement = _repair_alternate_scalar(
            current,
            dict(REPAIRED_SELECTION_HEAD_COLUMNS)[field],
        )
        with pytest.raises(sqlite3.IntegrityError) as caught:
            connection.execute(
                f'UPDATE "{REPAIRED_TABLE_ORDER[7]}" SET "{field}"=? '
                f"WHERE {_LINEAGE_WHERE}",
                (replacement, *inserted["lineage"]),
            )
        assert caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_TRIGGER"
        assert str(caught.value) == "immutable_selection_head_lineage"
        after = connection.execute(
            f'SELECT {",".join(head_fields)} FROM "{REPAIRED_TABLE_ORDER[7]}" '
            f"WHERE {_LINEAGE_WHERE}",
            inserted["lineage"],
        ).fetchone()
        assert after == before
    finally:
        connection.rollback()
        connection.close()


def test_nine_repair_selection_head_positive_cas_changes_only_mutable_fields() -> None:
    root = _build_repaired_physical_family(False)
    successor = _build_repaired_successor_family(
        root,
        suffix="trigger-positive-cas.0001",
        readiness_present=True,
    )
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        _insert_expected_recovery_family(
            connection,
            root,
            replace_existing_head=False,
        )
        connection.commit()
        _insert_expected_recovery_family(
            connection,
            successor,
            replace_existing_head=True,
        )
        connection.commit()
        root_head = next(
            row["values"]
            for row in root["physical_rows"]
            if row["role"] == "selection_head_postimage"
        )
        successor_head = next(
            row["values"]
            for row in successor["physical_rows"]
            if row["role"] == "selection_head_postimage"
        )
        selected = connection.execute(
            f'SELECT {",".join(successor_head)} FROM "{REPAIRED_TABLE_ORDER[7]}" '
            f"WHERE {_LINEAGE_WHERE}",
            tuple(successor_head[field] for field in REPAIRED_LINEAGE_COLUMNS),
        ).fetchone()
        assert selected == tuple(successor_head.values())
        assert all(
            root_head[field] == successor_head[field]
            for field in REPAIRED_SELECTION_HEAD_IMMUTABLE_FIELDS
        )
        assert all(
            root_head[field] == successor_head[field]
            for field in REPAIRED_C2B3D_LINEAGE_FIELDS
        )
        assert any(
            root_head[field] != successor_head[field]
            for field in REPAIRED_SELECTION_HEAD_MUTABLE_CAS_FIELDS
        )
        assert successor_head["head_digest"] == _repaired_row_digest(
            REPAIRED_TABLE_ORDER[7],
            successor_head,
        )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()


def test_nine_repair_post_evidence_insertion_order_is_canonicalized_by_gate() -> None:
    rows = _build_repaired_common_phase_rows(
        "post_execution_semantic_review",
        "post_execution_semantic_review",
        "post_execution_semantic_review",
        post_evidence_count=9,
    )
    reordered = (*rows[:3], *reversed(rows[3:]))
    connection, _inventory = _install_repaired_temporary_schema()
    connection.commit()
    trace: list[str] = []
    try:
        _commit_post_common_rows_with_transaction_gate(
            connection,
            reordered,
            trace,
        )
        assert trace[-2:] == ["post_evidence_gate", "commit"]
        observed = connection.execute(
            REPAIRED_POST_EVIDENCE_ROWS_QUERY,
            (rows[2]["values"]["proposal_ref"],),
        ).fetchall()
        assert tuple(row[5] for row in observed) == tuple(
            rank for _role, rank, _required in REPAIRED_POST_EXECUTION_EVIDENCE_SPECS
        )
    finally:
        connection.close()


REPAIRED_COMMON_RELATION_MUTATIONS = (
    ("source_invocation", "model_contract_ref"),
    ("source_invocation", "model_contract_digest"),
    ("source_invocation", "model_configuration_ref"),
    ("source_invocation", "model_configuration_digest"),
    ("source_invocation", "context_ref"),
    ("source_invocation", "context_digest"),
    ("private_artifact_binding", "artifact_ref"),
    ("private_artifact_binding", "artifact_digest"),
    ("private_artifact_binding", "safe_projection_digest"),
    ("model_proposal", "source_invocation_ref"),
    ("model_proposal", "source_invocation_digest"),
)


@pytest.mark.parametrize("phase", PHASES)
@pytest.mark.parametrize("role,field", REPAIRED_COMMON_RELATION_MUTATIONS)
def test_nine_repair_common_envelope_rejects_every_repeated_field_divergence(
    phase: str,
    role: str,
    field: str,
) -> None:
    rows = list(
        _build_repaired_common_phase_rows(
            phase,
            phase,
            phase,
            post_evidence_count=(9 if phase == "post_execution_semantic_review" else 0),
        )
    )
    selected = next(row for row in rows if row["role"] == role)
    old = selected["values"][field]
    selected["values"][field] = (
        "f" * 64
        if field.endswith("digest") and old != "f" * 64
        else "e" * 64
        if field.endswith("digest")
        else f"{old}.foreign"
    )
    selected["values"][REPAIRED_TABLE_DIGESTS[selected["table"]][0]] = (
        _repaired_row_digest(selected["table"], selected["values"])
    )
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_common_physical_rows(tuple(rows))
    assert caught.value.reason == "phase_algebra_mismatch"


class _RepairHostileKeyEquality:
    def __hash__(self) -> int:
        return 41

    def __eq__(self, other: object) -> bool:
        raise RuntimeError("HOSTILE_KEY_EQUALITY_REACHED")


class _RepairHostileKeyHash:
    def __init__(self) -> None:
        self.calls = 0

    def __hash__(self) -> int:
        self.calls += 1
        if self.calls > 1:
            raise RuntimeError("HOSTILE_KEY_HASH_REACHED")
        return 43


@pytest.mark.parametrize(
    "case_name",
    (
        "hostile-equality-key",
        "hostile-hash-key",
        "unhashable-pair-container",
        "cyclic-value",
        "mapping-subclass",
        "key-subclass",
        "missing-key",
        "extra-key",
    ),
)
def test_nine_repair_projection_mapping_shape_precedes_every_operation(
    case_name: str,
) -> None:
    artifact, binding, context, proposal = _sample_projection_inputs()
    malformed: object
    hostile_hash: _RepairHostileKeyHash | None = None
    if case_name == "hostile-equality-key":
        malformed = {
            _RepairHostileKeyEquality(): context["planning_context_schema_id"],
            "planning_context_ref": context["planning_context_ref"],
            "planning_context_digest": context["planning_context_digest"],
        }
    elif case_name == "hostile-hash-key":
        hostile_hash = _RepairHostileKeyHash()
        malformed = {
            hostile_hash: context["planning_context_schema_id"],
            "planning_context_ref": context["planning_context_ref"],
            "planning_context_digest": context["planning_context_digest"],
        }
    elif case_name == "unhashable-pair-container":
        malformed = [([], context["planning_context_schema_id"])]
    elif case_name == "cyclic-value":
        cyclic = dict(context)
        cyclic["planning_context_digest"] = cyclic
        malformed = cyclic
    elif case_name == "mapping-subclass":
        malformed = _S41DictSubclass(context)
    elif case_name == "key-subclass":
        malformed = _s41_replace_key_with_subclass(
            context,
            "planning_context_ref",
        )
    elif case_name == "missing-key":
        malformed = dict(context)
        del malformed["planning_context_ref"]
    elif case_name == "extra-key":
        malformed = {**context, "shadow": "shadow.safe.0001"}
    else:
        raise AssertionError(case_name)
    with pytest.raises(_ContractViolation) as caught:
        _derive_safe_projection(artifact, binding, malformed, proposal)
    assert type(caught.value) is _ContractViolation
    assert caught.value.reason == "safe_projection_derivation_mismatch"
    if hostile_hash is not None:
        assert hostile_hash.calls == 1


@pytest.mark.parametrize("field", REPAIRED_C2B3D_LINEAGE_FIELDS)
def test_nine_repair_every_c2b3d_lineage_substitution_fails_before_replay(
    field: str,
) -> None:
    family = _build_repaired_physical_family(False)
    original_receipt = deepcopy(family["receipt"]["values"])
    context = next(
        row["values"]
        for row in family["physical_rows"]
        if row["role"] == "planning_context"
    )
    value = context[field]
    context_kind = dict(REPAIRED_PLANNING_CONTEXT_COLUMNS)[field]
    context[field] = _repair_alternate_scalar(value, context_kind)
    _redigest_repaired_physical_family(family)
    trace: list[str] = []
    clock_calls = 0

    def forbidden_clock() -> str:
        nonlocal clock_calls
        clock_calls += 1
        raise AssertionError("LINEAGE_REPLAY_CLOCK_CALLED")

    with pytest.raises(_ContractViolation):
        _apply_repaired_selection(
            mutation_ref=original_receipt["mutation_ref"],
            command_digest=original_receipt["command_digest"],
            receipt=family,
            bundle=object(),
            clock=forbidden_clock,
            trace=trace,
        )
    assert trace == ["receipt_lookup", "persisted_receipt_validation"]
    assert clock_calls == 0


@pytest.mark.parametrize(
    "field,kind,_source",
    REPAIRED_COMMAND_FIELD_SPECS,
    ids=tuple(field for field, _kind, _source in REPAIRED_COMMAND_FIELD_SPECS),
)
def test_nine_repair_every_complete_command_field_is_causal(
    field: str,
    kind: str,
    _source: str,
) -> None:
    family = _build_repaired_physical_family(False)
    original = family["command"]
    mutant = deepcopy(original)
    mutant[field] = _repair_alternate_scalar(mutant[field], kind)
    if field != "mutation_command_digest":
        mutant["mutation_command_digest"] = _independent_repaired_digest(
            REPAIRED_COMMAND_DOMAIN,
            {
                name: mutant[name]
                for name in SAFE_COMMAND_FIELD_ORDER
                if name != "mutation_command_digest"
            },
        )
        assert mutant["mutation_command_digest"] != original["mutation_command_digest"]
    family["command"] = mutant
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(family)
    assert caught.value.reason == "physical_family_receipt_binding_mismatch"


def test_nine_repair_omitted_artifact_binding_change_causes_reuse_conflict() -> None:
    family = _build_repaired_physical_family(False)
    original_receipt = deepcopy(family["receipt"]["values"])
    artifact = next(
        row["values"]
        for row in family["physical_rows"]
        if row["role"] == "private_artifact_binding"
    )
    artifact["artifact_canonical_byte_length"] += 7
    _redigest_repaired_physical_family(family)
    _validate_repaired_physical_family(family)
    assert family["command"]["mutation_command_digest"] != original_receipt[
        "command_digest"
    ]
    clock_calls = 0

    def forbidden_clock() -> str:
        nonlocal clock_calls
        clock_calls += 1
        raise AssertionError("COMMAND_REUSE_CLOCK_CALLED")

    trace: list[str] = []
    assert _apply_repaired_selection(
        mutation_ref=original_receipt["mutation_ref"],
        command_digest=original_receipt["command_digest"],
        receipt=family,
        bundle=object(),
        clock=forbidden_clock,
        trace=trace,
    ) == "mutation_ref_reuse_conflict"
    assert trace == [
        "receipt_lookup",
        "persisted_receipt_validation",
        "mutation_ref_reuse_conflict",
    ]
    assert clock_calls == 0


def test_nine_repair_stale_persisted_observation_digest_fails_before_replay() -> None:
    family = _build_repaired_physical_family(False)
    context = next(
        row["values"]
        for row in family["physical_rows"]
        if row["role"] == "planning_context"
    )
    context["authority_observation_state"] = "pending"
    _redigest_repaired_physical_family(family)
    trace: list[str] = []
    with pytest.raises(_ContractViolation) as caught:
        _apply_repaired_selection(
            mutation_ref=family["receipt"]["values"]["mutation_ref"],
            command_digest=family["receipt"]["values"]["command_digest"],
            receipt=family,
            bundle=object(),
            clock=lambda: (_ for _ in ()).throw(
                AssertionError("OBSERVATION_REPLAY_CLOCK_CALLED")
            ),
            trace=trace,
        )
    assert caught.value.reason == "authority_observation_shape_invalid"
    assert trace == ["receipt_lookup", "persisted_receipt_validation"]


def test_nine_repair_historical_receipt_survives_one_exact_later_cas() -> None:
    root = _build_repaired_physical_family(False)
    original_result = deepcopy(root["replay_result"])
    successor = _build_repaired_successor_family(
        root,
        suffix="historical-receipt.0001",
        readiness_present=True,
    )
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        _insert_expected_recovery_family(
            connection,
            root,
            replace_existing_head=False,
        )
        _insert_expected_recovery_family(
            connection,
            successor,
            replace_existing_head=True,
        )
        connection.commit()
        changes_before = connection.total_changes
        recovered = _recover_repaired_family(
            connection,
            expected_family=root,
            expected_head_preimage=None,
            fresh_writer_verified=True,
        )
        assert recovered == _RecoveryReadback(
            "committed_exact",
            1,
            original_result,
        )
        assert recovered.result is not root["replay_result"]
        assert connection.total_changes == changes_before
        assert root["replay_result"] == original_result
        assert root["replay_result"] != successor["replay_result"]
    finally:
        connection.close()


def _replace_repaired_observation_window(
    family: dict[str, object],
    *,
    issued_at: str = "2026-08-22T12:34:57Z",
    expires_at: str = "2026-08-22T13:34:55Z",
) -> None:
    observation = _build_authority_observation(
        issued_at=issued_at,
        expires_at=expires_at,
    )
    by_role = {row["role"]: row for row in family["physical_rows"]}
    context = by_role["planning_context"]["values"]
    context.update(
        {
            "authority_observation_issued_at": observation[
                "authority_observation_issued_at"
            ],
            "authority_observation_expires_at": observation[
                "authority_observation_expires_at"
            ],
            "authority_selection_observation_digest": observation[
                "authority_observation_digest"
            ],
        }
    )
    by_role["evidence.authority_selection_observation"]["values"][
        "evidence_digest"
    ] = observation["authority_observation_digest"]
    by_role["coordinator_disposition"]["values"][
        "authority_selection_observation_digest"
    ] = observation["authority_observation_digest"]


@pytest.mark.parametrize(
    "case_name",
    (
        "observation-issued-after-context",
        "observation-expiry-at-decision",
        "context-after-source-start",
        "source-start-after-completion",
        "source-completion-after-artifact",
        "artifact-after-evidence",
        "evidence-after-proposal",
        "proposal-equals-decision",
        "decision-head-time-mismatch",
        "head-decision-time-mismatch",
        "receipt-decision-time-mismatch",
        "result-decision-time-mismatch",
        "fresh-result-time-mismatch",
        "replay-result-time-mismatch",
    ),
)
def test_nine_repair_every_persisted_historical_time_relation_precedes_replay(
    case_name: str,
) -> None:
    family = _build_repaired_physical_family(False)
    by_role = {row["role"]: row for row in family["physical_rows"]}
    context = by_role["planning_context"]["values"]
    source = by_role["source_invocation"]["values"]
    artifact = by_role["private_artifact_binding"]["values"]
    proposal = by_role["model_proposal"]["values"]
    disposition = by_role["coordinator_disposition"]["values"]
    head = by_role["selection_head_postimage"]["values"]
    receipt = by_role["receipt"]["values"]
    if case_name == "observation-issued-after-context":
        _replace_repaired_observation_window(
            family,
            issued_at="2026-08-22T12:35:01Z",
        )
    elif case_name == "observation-expiry-at-decision":
        _replace_repaired_observation_window(
            family,
            expires_at="2026-08-22T12:35:04Z",
        )
    elif case_name == "context-after-source-start":
        context["planning_context_captured_at"] = "2026-08-22T12:35:02Z"
    elif case_name == "source-start-after-completion":
        source["source_invocation_started_at"] = "2026-08-22T12:35:03Z"
    elif case_name == "source-completion-after-artifact":
        source["source_invocation_completed_at"] = "2026-08-22T12:35:03Z"
    elif case_name == "artifact-after-evidence":
        artifact["artifact_validated_at"] = "2026-08-22T12:35:04Z"
    elif case_name == "evidence-after-proposal":
        for row in family["physical_rows"]:
            if row["table"] == REPAIRED_TABLE_ORDER[5]:
                row["values"]["evidence_bound_at"] = "2026-08-22T12:35:04Z"
    elif case_name == "proposal-equals-decision":
        proposal["proposal_created_at"] = "2026-08-22T12:35:04Z"
    elif case_name == "decision-head-time-mismatch":
        disposition["coordinator_disposition_decided_at"] = (
            "2026-08-22T12:35:05Z"
        )
    elif case_name == "head-decision-time-mismatch":
        head["updated_at"] = "2026-08-22T12:35:05Z"
    elif case_name in (
        "receipt-decision-time-mismatch",
        "result-decision-time-mismatch",
        "fresh-result-time-mismatch",
        "replay-result-time-mismatch",
    ):
        pass
    else:
        raise AssertionError(case_name)
    _redigest_repaired_physical_family(family)
    if case_name == "receipt-decision-time-mismatch":
        receipt["committed_at"] = "2026-08-22T12:35:05Z"
        receipt["receipt_digest"] = _repaired_row_digest(
            REPAIRED_TABLE_ORDER[8],
            receipt,
        )
        family["fresh_result"]["receipt_digest"] = receipt["receipt_digest"]
        family["replay_result"]["receipt_digest"] = receipt["receipt_digest"]
    elif case_name == "result-decision-time-mismatch":
        projection = family["result_projection"]
        projection["recorded_at"] = "2026-08-22T12:35:05Z"
        projection["result_projection_digest"] = _s41_digest(
            "governed-execution.nwp-pre-execution-plan-disposition-result.v1.identity",
            _s41_without(projection, "result_projection_digest"),
        )
        receipt["result_projection_digest"] = projection[
            "result_projection_digest"
        ]
        receipt["receipt_digest"] = _repaired_row_digest(
            REPAIRED_TABLE_ORDER[8],
            receipt,
        )
        family["fresh_result"] = {
            **projection,
            "receipt_digest": receipt["receipt_digest"],
        }
        family["replay_result"] = deepcopy(family["fresh_result"])
    elif case_name == "fresh-result-time-mismatch":
        family["fresh_result"]["recorded_at"] = "2026-08-22T12:35:05Z"
    elif case_name == "replay-result-time-mismatch":
        family["replay_result"]["recorded_at"] = "2026-08-22T12:35:05Z"
    clock_calls = 0

    def forbidden_clock() -> str:
        nonlocal clock_calls
        clock_calls += 1
        raise AssertionError("HISTORICAL_TIME_REPLAY_CLOCK_CALLED")

    trace: list[str] = []
    with pytest.raises(_ContractViolation):
        _apply_repaired_selection(
            mutation_ref=receipt["mutation_ref"],
            command_digest=receipt["command_digest"],
            receipt=family,
            bundle=object(),
            clock=forbidden_clock,
            trace=trace,
        )
    assert trace == ["receipt_lookup", "persisted_receipt_validation"]
    assert clock_calls == 0


def _independent_repaired_canonical_bytes(value: object) -> bytes:
    active: set[int] = set()

    def encode(item: object) -> str:
        if item is None:
            return "null"
        if type(item) is bool:
            return "true" if item else "false"
        if type(item) is int:
            return str(item)
        if type(item) is str:
            if unicodedata.normalize("NFC", item) != item:
                raise ValueError("noncanonical string")
            return json.dumps(item, ensure_ascii=False, allow_nan=False)
        if type(item) in (tuple, list):
            marker = id(item)
            if marker in active:
                raise ValueError("cycle")
            active.add(marker)
            try:
                return "[" + ",".join(encode(member) for member in item) + "]"
            finally:
                active.remove(marker)
        if type(item) is dict:
            marker = id(item)
            if marker in active or any(type(key) is not str for key in item):
                raise ValueError("invalid mapping")
            active.add(marker)
            try:
                return "{" + ",".join(
                    f"{encode(key)}:{encode(item[key])}" for key in sorted(item)
                ) + "}"
            finally:
                active.remove(marker)
        raise ValueError("unsupported canonical value")

    return encode(value).encode("utf-8", errors="strict")


def _independent_repaired_digest(domain: str, identity: object) -> str:
    if type(domain) is not str or not domain:
        raise ValueError("invalid domain")
    return hashlib.sha256(
        domain.encode("utf-8", errors="strict")
        + b"\x00"
        + _independent_repaired_canonical_bytes(identity)
    ).hexdigest()


def _independent_repaired_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        if any(type(key) is not str for key in left) or any(
            type(key) is not str for key in right
        ):
            return False
        if tuple(left) != tuple(right):
            return False
        return all(_independent_repaired_equal(left[key], right[key]) for key in left)
    if type(left) in (tuple, list):
        return len(left) == len(right) and all(
            _independent_repaired_equal(one, two)
            for one, two in zip(left, right, strict=True)
        )
    if type(left) not in (str, int, bool, type(None)):
        return False
    return left == right


INDEPENDENT_REPAIRED_ROW_LEDGER = {
    "development_model_source_invocations": (
        tuple("schema_id source_invocation_ref proposal_phase model_contract_ref model_contract_digest model_configuration_ref model_configuration_digest context_schema_id context_ref context_digest artifact_schema_id artifact_ref artifact_digest invocation_status source_invocation_started_at source_invocation_completed_at source_invocation_digest".split()),
        "source_invocation_digest",
        "governed-execution.nwp-model-source-invocation.v1.identity",
    ),
    "development_pre_execution_planning_contexts": (
        tuple("schema_id planning_context_ref program_ref program_version_ref program_version_number accepted_intent_revision_ref work_item_ref work_item_revision_ref semantic_attempt_ref semantic_attempt_digest attempt_number candidate_ref basis_decision_ref basis_decision_digest work_spec_ref work_spec_digest work_spec_safe_projection_digest effect_intent_ref effect_intent_digest author_command_ref author_command_digest standing_grant_ref standing_grant_digest attempt_authorization_ref attempt_authorization_digest effect_authorization_ref effect_authorization_digest attempt_fence_ref attempt_fence_digest attempt_fence_allowed_effect_classes_json attempt_fence_expires_at effect_fence_ref effect_fence_digest effect_fence_allowed_effect_classes_json effect_fence_expires_at delivery_attempt_ref delivery_envelope_digest delivery_attempt_digest expected_program_head_revision expected_work_item_head_revision expected_effect_head_fence_ref expected_effect_head_revision expected_effect_head_digest expected_delivery_head_attempt_ref expected_delivery_head_revision expected_delivery_head_digest global_stop_ref global_stop_version global_stop_state authority_evaluation_ref authority_evaluation_digest authority_selection_observation_schema_id authority_selection_observation_ref authoritative_subject_kind authoritative_subject_ref authority_observation_state authority_observation_version authority_observation_issued_at authority_observation_expires_at source_authority_ref verification_evidence_ref verification_evidence_digest authority_selection_observation_digest standing_policy_ref standing_policy_digest risk_lane_ref risk_lane_digest repository_ref base_git_object_format base_git_oid authorized_path_scope_digest cost_ceiling_ref cost_ceiling_digest token_ceiling_ref token_ceiling_digest time_ceiling_ref time_ceiling_digest delivery_ceiling_ref delivery_ceiling_digest effect_ceiling_ref effect_ceiling_digest validation_requirement_ref validation_requirement_digest validation_safe_evidence_digest review_requirement_ref review_requirement_digest review_safe_evidence_digest qualified_remote_host_readiness_ref qualified_remote_host_readiness_digest planning_context_captured_at planning_context_digest".split()),
        "planning_context_digest",
        "governed-execution.nwp-pre-execution-planning-context.v1.identity",
    ),
    "development_private_proposal_artifact_bindings": (
        tuple("schema_id artifact_ref proposal_phase artifact_schema_id artifact_digest artifact_canonical_byte_length safe_projection_schema_id safe_projection_digest privacy_classification artifact_validated_at artifact_binding_digest".split()),
        "artifact_binding_digest",
        "governed-execution.nwp-private-proposal-artifact-binding.v1.identity",
    ),
    "development_model_proposals": (
        tuple("schema_id proposal_ref proposal_phase source_invocation_ref source_invocation_digest model_contract_ref model_contract_digest model_configuration_ref model_configuration_digest context_schema_id context_ref context_digest artifact_schema_id artifact_ref artifact_digest safe_projection_schema_id safe_projection_digest recommendation reason_code evidence_set_ref evidence_set_digest proposal_created_at proposal_digest".split()),
        "proposal_digest",
        "governed-execution.nwp-model-proposal-envelope.v1.identity",
    ),
    "development_pre_execution_plan_projections": (
        tuple("schema_id proposal_ref proposal_phase artifact_schema_id artifact_ref artifact_digest planning_context_schema_id planning_context_ref planning_context_digest strategy_item_count work_unit_count affected_path_count affected_path_set_digest expected_output_count expected_output_set_digest validation_step_count validation_strategy_digest assumption_count assumption_set_digest risk_count risk_set_digest prerequisite_count prerequisite_set_digest stop_condition_count stop_condition_set_digest proposed_resource_effect_use_digest allowed_effect_classes recommendation reason_code safe_projection_digest".split()),
        "safe_projection_digest",
        "governed-execution.nwp-pre-execution-plan-safe-projection.v1.identity",
    ),
    "development_model_proposal_evidence_bindings": (
        tuple("schema_id proposal_ref proposal_phase evidence_set_ref evidence_role role_rank ordinal evidence_ref evidence_digest required_for_selection evidence_bound_at evidence_binding_digest".split()),
        "evidence_binding_digest",
        "governed-execution.nwp-model-proposal-evidence-binding.v1.identity",
    ),
    "development_pre_execution_dispositions": (
        tuple("schema_id disposition_ref program_ref program_version_ref accepted_intent_revision_ref work_item_ref work_item_revision_ref proposal_ref proposal_phase proposal_digest planning_context_ref planning_context_digest evidence_set_ref evidence_set_digest semantic_attempt_ref candidate_ref effect_intent_ref author_command_ref author_command_digest attempt_fence_ref attempt_fence_digest effect_fence_ref effect_fence_digest delivery_attempt_ref delivery_envelope_digest disposition reason_code supersedes_disposition_ref expected_selection_head_revision expected_selection_head_digest prior_selection_head_revision prior_selection_head_digest resulting_selection_head_revision selection_head_postimage_digest authority_selection_observation_ref authority_selection_observation_digest coordinator_disposition_decided_at program_version_number semantic_attempt_digest attempt_number basis_decision_ref basis_decision_digest work_spec_ref work_spec_digest work_spec_safe_projection_digest effect_intent_digest standing_grant_ref standing_grant_digest attempt_authorization_ref attempt_authorization_digest effect_authorization_ref effect_authorization_digest delivery_attempt_digest authority_evaluation_ref authority_evaluation_digest disposition_digest".split()),
        "disposition_digest",
        "governed-execution.nwp-pre-execution-coordinator-disposition.v1.identity",
    ),
    "development_pre_execution_selection_heads": (
        tuple("schema_id program_ref program_version_ref accepted_intent_revision_ref work_item_ref work_item_revision_ref semantic_attempt_ref candidate_ref effect_intent_ref author_command_ref author_command_digest attempt_fence_ref attempt_fence_digest effect_fence_ref effect_fence_digest delivery_attempt_ref delivery_envelope_digest current_proposal_ref current_disposition_ref current_disposition head_revision updated_at program_version_number semantic_attempt_digest attempt_number basis_decision_ref basis_decision_digest work_spec_ref work_spec_digest work_spec_safe_projection_digest effect_intent_digest standing_grant_ref standing_grant_digest attempt_authorization_ref attempt_authorization_digest effect_authorization_ref effect_authorization_digest delivery_attempt_digest authority_evaluation_ref authority_evaluation_digest head_digest".split()),
        "head_digest",
        "governed-execution.nwp-pre-execution-selection-head.v1.identity",
    ),
    "development_cognitive_mutation_receipts": (
        tuple("schema_id mutation_ref mutation_family command_schema_id command_digest program_ref proposal_ref disposition_ref disposition_digest authority_selection_observation_ref authority_selection_observation_digest effect_intent_ref selection_head_revision selection_head_digest result_class result_projection_digest mutation_graph_digest outcome committed_at receipt_digest".split()),
        "receipt_digest",
        "governed-execution.nwp-cognitive-mutation-receipt.v1.identity",
    ),
}
INDEPENDENT_REPAIRED_C2B3D_LINEAGE_FIELDS = tuple(
    "program_ref program_version_ref program_version_number "
    "accepted_intent_revision_ref work_item_ref work_item_revision_ref "
    "semantic_attempt_ref semantic_attempt_digest attempt_number candidate_ref "
    "basis_decision_ref basis_decision_digest work_spec_ref work_spec_digest "
    "work_spec_safe_projection_digest effect_intent_ref effect_intent_digest "
    "author_command_ref author_command_digest standing_grant_ref "
    "standing_grant_digest attempt_authorization_ref "
    "attempt_authorization_digest effect_authorization_ref "
    "effect_authorization_digest attempt_fence_ref attempt_fence_digest "
    "effect_fence_ref effect_fence_digest delivery_attempt_ref "
    "delivery_envelope_digest delivery_attempt_digest authority_evaluation_ref "
    "authority_evaluation_digest".split()
)
assert (
    INDEPENDENT_REPAIRED_C2B3D_LINEAGE_FIELDS
    == REPAIRED_C2B3D_LINEAGE_FIELDS
)
INDEPENDENT_REPAIRED_COMMAND_FIELDS = tuple(
    "schema_id mutation_ref proposal_ref proposal_digest source_invocation_ref source_invocation_digest artifact_ref artifact_digest artifact_binding_digest planning_context_ref planning_context_digest safe_projection_digest evidence_set_ref evidence_set_digest preassigned_disposition_ref expected_current_selection_revision expected_current_selection_head_digest disposition disposition_reason_code supersedes_disposition_ref program_ref semantic_attempt_ref candidate_ref effect_intent_ref author_command_ref author_command_digest attempt_fence_ref attempt_fence_digest effect_fence_ref effect_fence_digest delivery_attempt_ref delivery_envelope_digest mutation_command_digest".split()
)
INDEPENDENT_REPAIRED_RESULT_FIELDS = tuple(
    "schema_id mutation_ref command_digest proposal_ref disposition_ref disposition_digest disposition program_ref semantic_attempt_ref candidate_ref effect_intent_ref selection_head_revision selection_head_digest authority_selection_observation_ref authority_selection_observation_digest mutation_graph_digest recorded_at result_projection_digest".split()
)
INDEPENDENT_REPAIRED_FRESH_FIELDS = (
    *INDEPENDENT_REPAIRED_RESULT_FIELDS,
    "receipt_digest",
)
INDEPENDENT_REPAIRED_COMMAND_DOMAIN = (
    "governed-execution.nwp-record-pre-execution-plan-disposition-command.v1.identity"
)
INDEPENDENT_REPAIRED_GRAPH_DOMAIN = (
    "governed-execution.nwp-cognitive-mutation-graph.v1.identity"
)
INDEPENDENT_REPAIRED_RESULT_DOMAIN = (
    "governed-execution.nwp-pre-execution-plan-disposition-result.v1.identity"
)
INDEPENDENT_REPAIRED_EVIDENCE_SET_DOMAIN = (
    "governed-execution.nwp-model-proposal-evidence-set.v1.identity"
)
INDEPENDENT_REPAIRED_ARTIFACT_FIELDS = tuple(
    "schema_id artifact_ref proposal_ref proposal_phase planning_context_ref implementation_strategy proposed_work_units affected_authorized_paths expected_outputs validation_strategy material_assumptions risks_and_uncertainties required_evidence_and_prerequisites stop_or_replan_conditions proposed_resource_and_effect_use recommendation reason_code artifact_digest".split()
)
INDEPENDENT_REPAIRED_SELECTION_HEAD_PRIMARY_KEY_FIELDS = (
    "program_ref",
    "semantic_attempt_ref",
    "candidate_ref",
    "effect_intent_ref",
    "author_command_ref",
    "attempt_fence_ref",
    "effect_fence_ref",
    "delivery_attempt_ref",
)


def _independent_repaired_row_digest(
    table: str,
    values: dict[str, object],
) -> str:
    fields, digest_field, domain = INDEPENDENT_REPAIRED_ROW_LEDGER[table]
    if type(values) is not dict or any(type(key) is not str for key in values):
        raise ValueError("row shape")
    if tuple(values) != fields:
        raise ValueError("row order")
    identity = {field: values[field] for field in fields if field != digest_field}
    if table == "development_pre_execution_plan_projections":
        decoded = json.loads(identity["allowed_effect_classes"])
        if type(decoded) is not list:
            raise ValueError("projection effect classes")
        identity["allowed_effect_classes"] = tuple(decoded)
    return _independent_repaired_digest(domain, identity)


def _independent_repaired_locator(
    table: str,
    values: dict[str, object],
) -> tuple[tuple[str, object], ...]:
    if table == "development_model_proposal_evidence_bindings":
        fields = ("proposal_ref", "evidence_role", "ordinal")
    elif table == "development_pre_execution_selection_heads":
        fields = INDEPENDENT_REPAIRED_SELECTION_HEAD_PRIMARY_KEY_FIELDS
    else:
        fields = {
            "development_model_source_invocations": ("source_invocation_ref",),
            "development_pre_execution_planning_contexts": ("planning_context_ref",),
            "development_private_proposal_artifact_bindings": ("artifact_ref",),
            "development_model_proposals": ("proposal_ref",),
            "development_pre_execution_plan_projections": ("proposal_ref",),
            "development_pre_execution_dispositions": ("disposition_ref",),
            "development_cognitive_mutation_receipts": ("mutation_ref",),
        }[table]
    return tuple((field, values[field]) for field in fields)


def _independent_repaired_command_from_rows(
    rows: dict[str, dict[str, object]],
    mutation_ref: object,
) -> dict[str, object]:
    source = rows["source_invocation"]["values"]
    context = rows["planning_context"]["values"]
    artifact = rows["private_artifact_binding"]["values"]
    proposal = rows["model_proposal"]["values"]
    projection = rows["pre_execution_plan_projection"]["values"]
    disposition = rows["coordinator_disposition"]["values"]
    command = {
        "schema_id": "governed-execution.nwp-record-pre-execution-plan-disposition-command.v1",
        "mutation_ref": mutation_ref,
        "proposal_ref": proposal["proposal_ref"],
        "proposal_digest": proposal["proposal_digest"],
        "source_invocation_ref": source["source_invocation_ref"],
        "source_invocation_digest": source["source_invocation_digest"],
        "artifact_ref": artifact["artifact_ref"],
        "artifact_digest": artifact["artifact_digest"],
        "artifact_binding_digest": artifact["artifact_binding_digest"],
        "planning_context_ref": context["planning_context_ref"],
        "planning_context_digest": context["planning_context_digest"],
        "safe_projection_digest": projection["safe_projection_digest"],
        "evidence_set_ref": proposal["evidence_set_ref"],
        "evidence_set_digest": proposal["evidence_set_digest"],
        "preassigned_disposition_ref": disposition["disposition_ref"],
        "expected_current_selection_revision": disposition[
            "expected_selection_head_revision"
        ],
        "expected_current_selection_head_digest": disposition[
            "expected_selection_head_digest"
        ],
        "disposition": disposition["disposition"],
        "disposition_reason_code": disposition["reason_code"],
        "supersedes_disposition_ref": disposition["supersedes_disposition_ref"],
        "program_ref": context["program_ref"],
        "semantic_attempt_ref": context["semantic_attempt_ref"],
        "candidate_ref": context["candidate_ref"],
        "effect_intent_ref": context["effect_intent_ref"],
        "author_command_ref": context["author_command_ref"],
        "author_command_digest": context["author_command_digest"],
        "attempt_fence_ref": context["attempt_fence_ref"],
        "attempt_fence_digest": context["attempt_fence_digest"],
        "effect_fence_ref": context["effect_fence_ref"],
        "effect_fence_digest": context["effect_fence_digest"],
        "delivery_attempt_ref": context["delivery_attempt_ref"],
        "delivery_envelope_digest": context["delivery_envelope_digest"],
    }
    command["mutation_command_digest"] = _independent_repaired_digest(
        INDEPENDENT_REPAIRED_COMMAND_DOMAIN,
        command,
    )
    return command


def _independent_repaired_family_digest_ledger(
    family: object,
) -> dict[str, object]:
    outer_fields = (
        "readiness_present",
        "command",
        "physical_rows",
        "physical_row_count",
        "graph",
        "receipt",
        "result_projection",
        "fresh_result",
        "replay_result",
    )
    if (
        type(family) is not dict
        or any(type(key) is not str for key in family)
        or tuple(family) != outer_fields
        or type(family["readiness_present"]) is not bool
        or type(family["physical_rows"]) is not tuple
    ):
        raise ValueError("family shape")
    rows: dict[str, dict[str, object]] = {}
    row_ledger: list[tuple[str, str]] = []
    for member in family["physical_rows"]:
        if (
            type(member) is not dict
            or any(type(key) is not str for key in member)
            or tuple(member) != ("table", "role", "rank", "ordinal", "values")
            or type(member["table"]) is not str
            or member["table"] not in INDEPENDENT_REPAIRED_ROW_LEDGER
            or type(member["role"]) is not str
            or member["role"] in rows
            or type(member["ordinal"]) is not int
            or (member["rank"] is not None and type(member["rank"]) is not int)
        ):
            raise ValueError("member shape")
        values = member["values"]
        digest_field = INDEPENDENT_REPAIRED_ROW_LEDGER[member["table"]][1]
        expected_digest = _independent_repaired_row_digest(
            member["table"],
            values,
        )
        if values[digest_field] != expected_digest:
            raise ValueError("row digest")
        rows[member["role"]] = member
        row_ledger.append((member["role"], expected_digest))
    expected_count = 23 if family["readiness_present"] else 22
    if family["physical_row_count"] != expected_count or len(rows) != expected_count:
        raise ValueError("row count")
    evidence_members = tuple(
        member
        for member in family["physical_rows"]
        if member["table"]
        == "development_model_proposal_evidence_bindings"
    )
    proposal = rows["model_proposal"]["values"]
    disposition = rows["coordinator_disposition"]["values"]
    if disposition["disposition_ref"] == proposal["proposal_ref"]:
        raise _ContractViolation("proposal_disposition_identity_collapse")
    context = rows["planning_context"]["values"]
    head = rows["selection_head_postimage"]["values"]
    for field in INDEPENDENT_REPAIRED_C2B3D_LINEAGE_FIELDS:
        if not (
            context[field] == disposition[field]
            and disposition[field] == head[field]
        ):
            raise ValueError("complete C2B3D lineage")
    evidence_identity = {
        "evidence_set_ref": proposal["evidence_set_ref"],
        "proposal_ref": proposal["proposal_ref"],
        "proposal_phase": proposal["proposal_phase"],
        "entries": tuple(
            {
                "evidence_role": member["values"]["evidence_role"],
                "role_rank": member["values"]["role_rank"],
                "ordinal": member["values"]["ordinal"],
                "evidence_ref": member["values"]["evidence_ref"],
                "evidence_digest": member["values"]["evidence_digest"],
                "evidence_binding_digest": member["values"][
                    "evidence_binding_digest"
                ],
            }
            for member in evidence_members
        ),
    }
    evidence_set_digest = _independent_repaired_digest(
        INDEPENDENT_REPAIRED_EVIDENCE_SET_DOMAIN,
        evidence_identity,
    )
    if proposal["evidence_set_digest"] != evidence_set_digest or any(
        member["values"]["proposal_ref"] != proposal["proposal_ref"]
        or member["values"]["proposal_phase"] != proposal["proposal_phase"]
        or member["values"]["evidence_set_ref"] != proposal["evidence_set_ref"]
        for member in evidence_members
    ):
        raise ValueError("evidence set")
    receipt = rows["receipt"]["values"]
    command = _independent_repaired_command_from_rows(
        rows,
        receipt["mutation_ref"],
    )
    if tuple(command) != INDEPENDENT_REPAIRED_COMMAND_FIELDS or not (
        _independent_repaired_equal(family["command"], command)
        and receipt["command_digest"] == command["mutation_command_digest"]
    ):
        raise ValueError("command")
    graph_entries = tuple(
        {
            "role": member["role"],
            "rank": member["rank"],
            "ordinal": member["ordinal"],
            "table": member["table"],
            "locator": _independent_repaired_locator(
                member["table"],
                member["values"],
            ),
            "member_digest": member["values"][
                INDEPENDENT_REPAIRED_ROW_LEDGER[member["table"]][1]
            ],
        }
        for member in family["physical_rows"]
        if member["rank"] is not None
    )
    graph = {
        "mutation_ref": receipt["mutation_ref"],
        "command_digest": command["mutation_command_digest"],
        "entries": graph_entries,
    }
    graph["mutation_graph_digest"] = _independent_repaired_digest(
        INDEPENDENT_REPAIRED_GRAPH_DOMAIN,
        graph,
    )
    if not _independent_repaired_equal(family["graph"], graph):
        raise ValueError("graph")
    result = {
        "schema_id": "governed-execution.nwp-pre-execution-plan-disposition-result.v1",
        "mutation_ref": receipt["mutation_ref"],
        "command_digest": command["mutation_command_digest"],
        "proposal_ref": disposition["proposal_ref"],
        "disposition_ref": disposition["disposition_ref"],
        "disposition_digest": disposition["disposition_digest"],
        "disposition": disposition["disposition"],
        "program_ref": disposition["program_ref"],
        "semantic_attempt_ref": disposition["semantic_attempt_ref"],
        "candidate_ref": disposition["candidate_ref"],
        "effect_intent_ref": disposition["effect_intent_ref"],
        "selection_head_revision": head["head_revision"],
        "selection_head_digest": head["head_digest"],
        "authority_selection_observation_ref": disposition[
            "authority_selection_observation_ref"
        ],
        "authority_selection_observation_digest": disposition[
            "authority_selection_observation_digest"
        ],
        "mutation_graph_digest": graph["mutation_graph_digest"],
        "recorded_at": disposition["coordinator_disposition_decided_at"],
    }
    result["result_projection_digest"] = _independent_repaired_digest(
        INDEPENDENT_REPAIRED_RESULT_DOMAIN,
        result,
    )
    if tuple(result) != INDEPENDENT_REPAIRED_RESULT_FIELDS or not (
        _independent_repaired_equal(family["result_projection"], result)
        and receipt["result_projection_digest"]
        == result["result_projection_digest"]
    ):
        raise ValueError("result")
    receipt_expectations = {
        "command_digest": command["mutation_command_digest"],
        "program_ref": disposition["program_ref"],
        "proposal_ref": disposition["proposal_ref"],
        "disposition_ref": disposition["disposition_ref"],
        "disposition_digest": disposition["disposition_digest"],
        "authority_selection_observation_ref": disposition[
            "authority_selection_observation_ref"
        ],
        "authority_selection_observation_digest": disposition[
            "authority_selection_observation_digest"
        ],
        "effect_intent_ref": disposition["effect_intent_ref"],
        "selection_head_revision": head["head_revision"],
        "selection_head_digest": head["head_digest"],
        "result_projection_digest": result["result_projection_digest"],
        "mutation_graph_digest": graph["mutation_graph_digest"],
        "committed_at": disposition["coordinator_disposition_decided_at"],
    }
    if any(receipt[field] != value for field, value in receipt_expectations.items()):
        raise ValueError("receipt bindings")
    fresh = {**result, "receipt_digest": receipt["receipt_digest"]}
    if tuple(fresh) != INDEPENDENT_REPAIRED_FRESH_FIELDS or not (
        _independent_repaired_equal(family["fresh_result"], fresh)
        and _independent_repaired_equal(family["replay_result"], fresh)
        and _independent_repaired_equal(family["receipt"], rows["receipt"])
    ):
        raise ValueError("fresh or replay")
    return {
        "row_digests": tuple(row_ledger),
        "evidence_set_digest": evidence_set_digest,
        "command_digest": command["mutation_command_digest"],
        "graph_digest": graph["mutation_graph_digest"],
        "result_digest": result["result_projection_digest"],
        "receipt_digest": receipt["receipt_digest"],
        "canonical_object_ledger": tuple(
            (
                role,
                len(encoded),
                hashlib.sha256(encoded).hexdigest(),
            )
            for role, encoded in (
                ("graph", _independent_repaired_canonical_bytes(graph)),
                ("result_projection", _independent_repaired_canonical_bytes(result)),
                ("receipt", _independent_repaired_canonical_bytes(receipt)),
                ("fresh_result", _independent_repaired_canonical_bytes(fresh)),
                (
                    "replay_result",
                    _independent_repaired_canonical_bytes(family["replay_result"]),
                ),
            )
        ),
        "fresh_canonical_sha256": hashlib.sha256(
            _independent_repaired_canonical_bytes(fresh)
        ).hexdigest(),
        "replay_canonical_sha256": hashlib.sha256(
            _independent_repaired_canonical_bytes(family["replay_result"])
        ).hexdigest(),
    }


def _independent_repaired_family_is_valid(family: object) -> bool:
    try:
        _independent_repaired_family_digest_ledger(family)
    except (
        _ContractViolation,
        AttributeError,
        IndexError,
        KeyError,
        TypeError,
        ValueError,
        UnicodeEncodeError,
        RecursionError,
    ):
        return False
    return True


def _independent_repaired_private_artifact_digest(artifact: object) -> str:
    if (
        type(artifact) is not dict
        or any(type(key) is not str for key in artifact)
        or tuple(artifact) != INDEPENDENT_REPAIRED_ARTIFACT_FIELDS
    ):
        raise ValueError("artifact shape")
    identity = {
        field: artifact[field]
        for field in INDEPENDENT_REPAIRED_ARTIFACT_FIELDS
        if field != "artifact_digest"
    }
    return _independent_repaired_digest(
        "governed-execution.nwp-pre-execution-plan-artifact.v1.identity",
        identity,
    )


def _independent_post_common_exact_mapping(
    value: object,
    fields: tuple[str, ...],
) -> dict[str, object]:
    if type(value) is not dict or len(value) != len(fields):
        raise _ContractViolation("post_common_mapping_invalid")
    for key in value:
        if type(key) is not str:
            raise _ContractViolation("post_common_mapping_invalid")
    if tuple(value) != fields:
        raise _ContractViolation("post_common_mapping_invalid")
    return value


def _independent_repaired_post_common_digest_ledger(
    rows: tuple[dict[str, object], ...],
) -> dict[str, object]:
    try:
        if type(rows) is not tuple or len(rows) not in (3, 12):
            raise _ContractViolation("post_common_mapping_invalid")
        for raw_member in rows:
            member = _independent_post_common_exact_mapping(
                raw_member,
                ("table", "role", "rank", "ordinal", "values"),
            )
            if not (
                type(member["table"]) is str
                and type(member["role"]) is str
                and type(member["rank"]) is int
                and type(member["ordinal"]) is int
                and member["table"] in INDEPENDENT_REPAIRED_ROW_LEDGER
            ):
                raise _ContractViolation("post_common_mapping_invalid")
            table = member["table"]
            value_fields = INDEPENDENT_REPAIRED_ROW_LEDGER[table][0]
            values = _independent_post_common_exact_mapping(
                member["values"],
                value_fields,
            )
            integer_fields = (
                ("artifact_canonical_byte_length",)
                if table == "development_private_proposal_artifact_bindings"
                else (
                    "role_rank",
                    "ordinal",
                    "required_for_selection",
                )
                if table == "development_model_proposal_evidence_bindings"
                else ()
            )
            for field in value_fields:
                expected_type = int if field in integer_fields else str
                if type(values[field]) is not expected_type:
                    raise _ContractViolation("post_common_mapping_invalid")
        return _independent_repaired_post_common_digest_ledger_validated(rows)
    except _ContractViolation:
        raise
    except Exception:
        raise _ContractViolation("post_common_mapping_invalid") from None


def _independent_repaired_post_common_digest_ledger_validated(
    rows: tuple[dict[str, object], ...],
) -> dict[str, object]:
    row_digests: list[tuple[str, str]] = []
    by_role: dict[str, dict[str, object]] = {}
    for member in rows:
        if (
            type(member) is not dict
            or tuple(member) != ("table", "role", "rank", "ordinal", "values")
            or member["table"] not in INDEPENDENT_REPAIRED_ROW_LEDGER
        ):
            raise ValueError("post member shape")
        digest_field = INDEPENDENT_REPAIRED_ROW_LEDGER[member["table"]][1]
        digest = _independent_repaired_row_digest(
            member["table"],
            member["values"],
        )
        if member["values"][digest_field] != digest:
            raise ValueError("post row digest")
        by_role[member["role"]] = member
        row_digests.append((member["role"], digest))
    source = by_role["source_invocation"]["values"]
    artifact = by_role["private_artifact_binding"]["values"]
    proposal = by_role["model_proposal"]["values"]
    if not all(
        left == right
        for left, right in (
            (source["proposal_phase"], "post_execution_semantic_review"),
            (artifact["proposal_phase"], source["proposal_phase"]),
            (proposal["proposal_phase"], source["proposal_phase"]),
            (source["model_contract_ref"], proposal["model_contract_ref"]),
            (source["model_contract_digest"], proposal["model_contract_digest"]),
            (source["model_configuration_ref"], proposal["model_configuration_ref"]),
            (source["model_configuration_digest"], proposal["model_configuration_digest"]),
            (source["context_schema_id"], proposal["context_schema_id"]),
            (source["context_ref"], proposal["context_ref"]),
            (source["context_digest"], proposal["context_digest"]),
            (source["artifact_schema_id"], artifact["artifact_schema_id"]),
            (source["artifact_ref"], artifact["artifact_ref"]),
            (source["artifact_digest"], artifact["artifact_digest"]),
            (artifact["artifact_schema_id"], proposal["artifact_schema_id"]),
            (artifact["artifact_ref"], proposal["artifact_ref"]),
            (artifact["artifact_digest"], proposal["artifact_digest"]),
            (artifact["safe_projection_schema_id"], proposal["safe_projection_schema_id"]),
            (artifact["safe_projection_digest"], proposal["safe_projection_digest"]),
            (source["source_invocation_ref"], proposal["source_invocation_ref"]),
            (source["source_invocation_digest"], proposal["source_invocation_digest"]),
        )
    ):
        raise ValueError("post relations")
    evidence = tuple(member["values"] for member in rows[3:])
    expected_roles = (
        ("candidate_capsule", 5, 0, 1),
        ("worker_result", 6, 0, 1),
        ("validation_result", 7, 0, 1),
        ("independent_review", 8, 0, 1),
        ("standing_policy", 9, 0, 1),
        ("risk_lane", 10, 0, 1),
        ("authority_currentness_attestation", 11, 0, 1),
        ("global_stop", 12, 0, 1),
        ("effect_ceiling", 13, 0, 1),
    )
    observed_roles = tuple(
        (
            row["evidence_role"],
            row["role_rank"],
            row["ordinal"],
            row["required_for_selection"],
        )
        for row in evidence
    )
    if evidence and observed_roles != expected_roles:
        raise ValueError("post evidence roles")
    if any(
        row["proposal_ref"] != proposal["proposal_ref"]
        or row["proposal_phase"] != proposal["proposal_phase"]
        or row["evidence_set_ref"] != proposal["evidence_set_ref"]
        for row in evidence
    ):
        raise ValueError("post evidence binding")
    evidence_identity = {
        "evidence_set_ref": proposal["evidence_set_ref"],
        "proposal_ref": proposal["proposal_ref"],
        "proposal_phase": proposal["proposal_phase"],
        "entries": tuple(
            {
                "evidence_role": row["evidence_role"],
                "role_rank": row["role_rank"],
                "ordinal": row["ordinal"],
                "evidence_ref": row["evidence_ref"],
                "evidence_digest": row["evidence_digest"],
                "evidence_binding_digest": row["evidence_binding_digest"],
            }
            for row in evidence
        ),
    }
    evidence_digest = _independent_repaired_digest(
        INDEPENDENT_REPAIRED_EVIDENCE_SET_DOMAIN,
        evidence_identity,
    )
    if proposal["evidence_set_digest"] != evidence_digest:
        raise ValueError("post evidence digest")
    return {
        "row_digests": tuple(row_digests),
        "evidence_set_digest": evidence_digest,
        "canonical_sha256": hashlib.sha256(
            _independent_repaired_canonical_bytes(rows)
        ).hexdigest(),
    }


class _PostCommonEqualityBomb(str):
    __hash__ = str.__hash__

    def __eq__(self, other: object) -> bool:
        raise RuntimeError("POST_COMMON_EQUALITY_BOMB")


class _PostCommonHashBomb(str):
    def __new__(cls, value: str) -> _PostCommonHashBomb:
        instance = str.__new__(cls, value)
        instance.armed = False
        instance.calls = 0
        return instance

    def __hash__(self) -> int:
        self.calls += 1
        if self.armed:
            raise RuntimeError("POST_COMMON_HASH_BOMB")
        return str.__hash__(self)


@pytest.mark.parametrize(
    "case_name",
    (
        "hostile-equality-str-key",
        "hostile-hash-str-key",
        "ordinary-str-subclass-key",
        "missing-key",
        "extra-key",
        "dict-subclass",
        "unhashable-nested-container",
    ),
)
def test_reaudit_independent_post_common_mapping_failures_are_finite(
    case_name: str,
) -> None:
    rows = list(
        _build_repaired_common_phase_rows(
            "post_execution_semantic_review",
            "post_execution_semantic_review",
            "post_execution_semantic_review",
            post_evidence_count=9,
        )
    )
    member = rows[0]
    hash_bomb: _PostCommonHashBomb | None = None
    if case_name == "hostile-equality-str-key":
        member = {
            (
                _PostCommonEqualityBomb(key)
                if key == "table"
                else key
            ): value
            for key, value in member.items()
        }
    elif case_name == "hostile-hash-str-key":
        hash_bomb = _PostCommonHashBomb("table")
        member = {
            (hash_bomb if key == "table" else key): value
            for key, value in member.items()
        }
        hash_bomb.armed = True
    elif case_name == "ordinary-str-subclass-key":
        member = {
            (_S41StringSubclass(key) if key == "table" else key): value
            for key, value in member.items()
        }
    elif case_name == "missing-key":
        member = dict(member)
        del member["role"]
    elif case_name == "extra-key":
        member = {**member, "extra": "forbidden"}
    elif case_name == "dict-subclass":
        member = _S41DictSubclass(member)
    elif case_name == "unhashable-nested-container":
        member = dict(member)
        values = dict(member["values"])
        values["source_invocation_ref"] = []
        member["values"] = values
    else:
        raise AssertionError(case_name)
    rows[0] = member
    with pytest.raises(_ContractViolation) as caught:
        _independent_repaired_post_common_digest_ledger(tuple(rows))
    assert caught.value.reason == "post_common_mapping_invalid"
    if hash_bomb is not None:
        assert hash_bomb.calls == 1


INDEPENDENT_REPAIRED_DIGEST_LEDGER: dict[str, object] = {
    "readiness_absent": {
        "row_digests": (
            ("source_invocation", "f0adc78a49ca5496407ff3cb73ad5cae70ca2ffb4294d174b7c94e4fef162c40"),
            ("planning_context", "ca067ba5a286bcfdf1d39a993b41ddcc57f75584e80c605a8621a85ae9f77b52"),
            ("private_artifact_binding", "64faa102c45794e963391609fc1019b19c79ea2710a03600ddb32551d5971b64"),
            ("model_proposal", "05b58c9fb58bec0b8171d64f1bbfd5ebc5523735c2dd91ff4f46229b4208e2dd"),
            ("pre_execution_plan_projection", "d8aed7b3d4b8a49159ec826f117d1ec0026299ef684e272e6737c72b463d2081"),
            ("evidence.standing_policy", "667db0a7b0ec8820d0f61a80b2a5d1bb409d1d99d60875ad7fc5dfb18bea5452"),
            ("evidence.risk_lane", "a8e2b390d18e841197bd2ef151e3b48accec940ca53636ee9faad595566b0202"),
            ("evidence.repository_binding", "a3fd87010bbba701e3d38096a1676c18e1cf4c371e73e76ea8623a2fffdee4bd"),
            ("evidence.base_binding", "fcfacd91b01e2ca3206b9f3d4992bf8e5c24900a3ee9d443552615cb2dcc9334"),
            ("evidence.authorized_path_scope", "b5cdf79beffd72cc6f9cb4c7fd59ab86d924b56239e1fed7f8f306fc49fca861"),
            ("evidence.cost_ceiling", "beee51b6a6e0508f954e7559d1717e6cc289841194ef512718883a1cfc2ab52a"),
            ("evidence.token_ceiling", "8140fe9a84315a5d5e2ea1530ea23c02245a2dd67228c7d22fdea8fc02318b83"),
            ("evidence.time_ceiling", "7865a3176ebc08ec83c49a9aefde1e42a513d447459457357e86922f7824dcff"),
            ("evidence.delivery_ceiling", "af7fc9db9e8e4f7161cd0a6ce27ff08a3181543d2baf240d575d24773df7aae7"),
            ("evidence.effect_ceiling", "1d898d2253b44a31c99e8f8024dfbb9cf1eda702f4b9ed1e3b6323afe6ab4a4d"),
            ("evidence.authority_selection_observation", "c6969b1556a937db9e787f18a2b1e2637914049b92d56ca5878ff53399e7377e"),
            ("evidence.global_stop", "17e3e48e3cdf5fd080671309294eab3a39f9553c407929df3f89ebeb6e615c0f"),
            ("evidence.validation_requirement", "cc723c675161cda5410d48492ab4505c58e3e31554029edf9c7f711669592158"),
            ("evidence.review_requirement", "74b297a9191539ca20a1919770df734587a803f866b208bea3026114f1cad9dd"),
            ("coordinator_disposition", "05357fc7a58c5391c997aa430542de7cbb35ba4878982b85b2319918df3d7ff3"),
            ("selection_head_postimage", "7a0e83d5b5a34d97494b4689f4f18ac121e3c8e2f1f1da670793e6e834a0cf3c"),
            ("receipt", "845b69e511a793141da55fba95901787f48777645de91ae7e4338ec7ac51f076"),
        ),
        "evidence_set_digest": "013b0c647bdc0275db1074e7f351c1cf1028ba5d373c4b0d814c373b2bb649e2",
        "command_digest": "a6722c5d14bc1d558fb462ffa4e9ed5705085c89360fb72050d19ce51670b04b",
        "graph_digest": "7f9df837cf186a488f6a46c408c6e27a67bd22f18ed4e7e5cde18f038bc64c27",
        "result_digest": "9ba1300aecc520c644cad9b1e36d4be664ebf9ea5174b71ce87df9646357f390",
        "receipt_digest": "845b69e511a793141da55fba95901787f48777645de91ae7e4338ec7ac51f076",
        "canonical_object_ledger": (
            ("graph", 6675, "22ae712c6d715339ce3f011de5533efefa0cff9512f543093d642a5665db4cbf"),
            ("result_projection", 1155, "0f334b2f85489e3d19c985175aedc12d798379f6afe025dce23dedd524566ea5"),
            ("receipt", 1330, "fffd1d0ecaeda6c471f547397e1bc87d4f52e2f893f1fd85220e6f20e06d2b43"),
            ("fresh_result", 1239, "5dc675bbd6434dd3cbbbef7f530c128ced900ff8df549ba2251a04d239a7598c"),
            ("replay_result", 1239, "5dc675bbd6434dd3cbbbef7f530c128ced900ff8df549ba2251a04d239a7598c"),
        ),
        "fresh_canonical_sha256": "5dc675bbd6434dd3cbbbef7f530c128ced900ff8df549ba2251a04d239a7598c",
        "replay_canonical_sha256": "5dc675bbd6434dd3cbbbef7f530c128ced900ff8df549ba2251a04d239a7598c",
    },
    "readiness_present": {
        "row_digests": (
            ("source_invocation", "b1acdb4edb116661e0f0f7b3fb82d25c590ac3da874f4daa1e47d748bc4ceac6"),
            ("planning_context", "7f618c45531808c2b356d10ff0b8b612e002a9625b35579d4aeef3ede90be697"),
            ("private_artifact_binding", "f7b630dc613b80c40cd61dd07c49e5d6799e21bbbdd1886f5e220ecfe648a702"),
            ("model_proposal", "0d70f582ddbb3f9ace0b555afe4c88c8a1b6266c27e94eb9481f9b575b779149"),
            ("pre_execution_plan_projection", "d958ca3a596f9e2db772f0cdee193fbb5022b1edce67e18c0ef73e1a04bced5d"),
            ("evidence.standing_policy", "68579a8ff6e4034a0249e84fefe49caf3193a36934d44bb53bbf81e3bd8af414"),
            ("evidence.risk_lane", "6fa73c9b81fa66afe7a556f1bf79e83b889733a86905f58df9c64a0aade1fc7a"),
            ("evidence.repository_binding", "6fb254c865c3675d54fa918effc6171750dd781d888dc955ec64167438ea5507"),
            ("evidence.base_binding", "4161be3a216264ef9ef12d0baec7176d931093faf50589e0b66606c222b22d3f"),
            ("evidence.authorized_path_scope", "f628f04370853cbef63157a54fae05b5b689c9ebb4547580aa4c0840149f57dd"),
            ("evidence.cost_ceiling", "f3aea247fc2c3e185063cd77ce353353917c6c184472306a1c92ff5539b4db43"),
            ("evidence.token_ceiling", "e1b504b239ecb0eafb4f0fab6ceadda01679a1e9dfb175544c8ce5fb64e4f9fd"),
            ("evidence.time_ceiling", "4ba3e69877f0021bd4d106fd353ee40e2489b366a90b4f090f19ccbe20fe10a9"),
            ("evidence.delivery_ceiling", "a8777e422455ffcfeb8ab9b8c69266572ce36fc70324f1a7d0ecc28aaaeda24c"),
            ("evidence.effect_ceiling", "beb27e95c55a5d058024aa3ccde4175ea457526eb9591e9f9f7b21145a155889"),
            ("evidence.authority_selection_observation", "1c22e67bfd0e640ded2d1fa88fff23f1fc023353c37472b9515502dc0213b581"),
            ("evidence.global_stop", "2f34143e90cffeed9455c232b6e71294304f9266141081ce1209248ae29d4987"),
            ("evidence.validation_requirement", "79f75b6bedb9c7a5d801cf875ab9fa3e2f8279210621857738b6d3fc39050094"),
            ("evidence.review_requirement", "0fb169b4015938fefd4a284866abc31c0834e7a3bc73a205fb1973dd5d9c4ff4"),
            ("evidence.qualified_remote_host_readiness", "4cd9cde82d5afc20eea15720c4b0569b108015e1682ec5349f80fed1a2e999b7"),
            ("coordinator_disposition", "fe39767c456f3b6019eeccda8c58bda515f74ac0dcd43980f3f4debbfde939f6"),
            ("selection_head_postimage", "5d873b7eac41a64672234ce9c8736193d7e14f745396b0d5b926ca13e3a0dd9c"),
            ("receipt", "557299087883ef6163e145fd69b2ff233610d6b6c1c15b7010ffee31cef17e99"),
        ),
        "evidence_set_digest": "bb2684269e497e051a48f379864526465dc27f1cde8cd30f0d1e7fc2cfc62b8c",
        "command_digest": "cc7e662b4794dbebcd48f17fec9cebef19b2277b280909e1190a112c198f120c",
        "graph_digest": "50126ce9b02c8c2153c4bce594c53ba1b3ef7c5f39cdc01f7612e566fa4a7dcd",
        "result_digest": "75c6c60b6ac0dd367937aeb7ec50646bd8d0bf9d75e9c11724f60734e25f8cd5",
        "receipt_digest": "557299087883ef6163e145fd69b2ff233610d6b6c1c15b7010ffee31cef17e99",
        "canonical_object_ledger": (
            ("graph", 7037, "31bbe7c4e9987c56b25c8dfe96bae1ceb39f0d1e8fed1a38f4f488cccbaa596f"),
            ("result_projection", 1158, "fed300b4bc6285e7fe740ab5e96910482e5195fb2206b47df2e55e51d74a5a6f"),
            ("receipt", 1333, "a988ea1c6bbcb4de3706ccd61d4cc15da1993d1b66b005171c7dd0ffff65d3d1"),
            ("fresh_result", 1242, "41f0b226bdae3e2bf320e254bb84e9b222069495da0fe30a89f0d0d2b721a091"),
            ("replay_result", 1242, "41f0b226bdae3e2bf320e254bb84e9b222069495da0fe30a89f0d0d2b721a091"),
        ),
        "fresh_canonical_sha256": "41f0b226bdae3e2bf320e254bb84e9b222069495da0fe30a89f0d0d2b721a091",
        "replay_canonical_sha256": "41f0b226bdae3e2bf320e254bb84e9b222069495da0fe30a89f0d0d2b721a091",
    },
    "post_zero": {
        "row_digests": (
            ("source_invocation", "6ed3ee2c567a19edc8b933970cd81cbcb8122cbf6579ffa795a124065abc8c78"),
            ("private_artifact_binding", "160847ae8d4096f54515acc807aabd7bfd0e380ec4e938aeb8ca6ef0105c5071"),
            ("model_proposal", "2592f0d0b3cc1bce716d00872428b7077d392ce9954bc7515587c3c2d9eafef0"),
        ),
        "evidence_set_digest": "176ffbb365adfd959fcc8ce7fe9c834e869397f7e9ed2ed37b2f240444cde067",
        "canonical_sha256": "25fdc607bfdcb1ff3ae6ea300732f3d722dc15ddb0bfbe2fa345abd9fd2cf366",
    },
    "post_complete": {
        "row_digests": (
            ("source_invocation", "6ed3ee2c567a19edc8b933970cd81cbcb8122cbf6579ffa795a124065abc8c78"),
            ("private_artifact_binding", "160847ae8d4096f54515acc807aabd7bfd0e380ec4e938aeb8ca6ef0105c5071"),
            ("model_proposal", "f65a2adb242be2ef124aada3bbe95b9b683a4cc723d972c49a8c39f2c0c3e288"),
            ("evidence.candidate_capsule", "d45c9cd4961307429c2ce6f9e5abf134adc3ea3972dabddc4adef54ef89e25ed"),
            ("evidence.worker_result", "365ad01d5d6126c15e83d031351c7c6af21d3a5b47e5a15ccfe91db4e2cf50b9"),
            ("evidence.validation_result", "bb2525849e83262dd1fec724c0919127e6901ce1cd772893698f60ca26ed582b"),
            ("evidence.independent_review", "de116b78e9381261aa392ca32df546e56afed2141ab0ada3431524d5a01628fc"),
            ("evidence.standing_policy", "47aed6da8d37aaf1838492168f4cd5473d66d11da2b75367991a642e0b741445"),
            ("evidence.risk_lane", "e9995eb4c05ac0423002d7f989b6c9debd45a14e2e98d499261b7785061b2a34"),
            ("evidence.authority_currentness_attestation", "f498b98bd0537e532e4be35ea1f3bc865b5124263e345ab69cbbfb27e4a1ee9f"),
            ("evidence.global_stop", "82ad509440374b0edb232e42bed0e6eb58d4d2045e82a2cdba36510784cf6dbc"),
            ("evidence.effect_ceiling", "7c9d0d94b0c03edf2e4ad4675e6836970fed10b6fffb5e11874ab9ddac5232dd"),
        ),
        "evidence_set_digest": "222b202216e0a62b928aa563c74a056d157ba85b67c59a7a8bb5ed6b5ee3f909",
        "canonical_sha256": "cfaa848ac3abf42cab7114e96a5438b97a6f1e264aa35c71ae9f540c8886aacb",
    },
    "private_artifact_digest": "2bd77bd31dcfc57a345670fc0238b7421b6ccbe86294b8b633268bc1b2bc8e5c",
}


def test_nine_repair_independent_digest_ledger_is_exact_for_every_variant() -> None:
    observed = {
        "readiness_absent": _independent_repaired_family_digest_ledger(
            _build_repaired_physical_family(False)
        ),
        "readiness_present": _independent_repaired_family_digest_ledger(
            _build_repaired_physical_family(True)
        ),
        "post_zero": _independent_repaired_post_common_digest_ledger(
            _build_repaired_common_phase_rows(
                "post_execution_semantic_review",
                "post_execution_semantic_review",
                "post_execution_semantic_review",
                post_evidence_count=0,
            )
        ),
        "post_complete": _independent_repaired_post_common_digest_ledger(
            _build_repaired_common_phase_rows(
                "post_execution_semantic_review",
                "post_execution_semantic_review",
                "post_execution_semantic_review",
                post_evidence_count=9,
            )
        ),
        "private_artifact_digest": _independent_repaired_private_artifact_digest(
            _sample_private_plan()
        ),
    }
    assert _independent_repaired_equal(
        observed,
        INDEPENDENT_REPAIRED_DIGEST_LEDGER,
    )


@pytest.mark.parametrize(
    "mutant",
    (
        "receipt-domain",
        "receipt-exclusion",
        "receipt-canonicalization",
        "graph-member-binding",
    ),
)
def test_nine_repair_independent_oracle_rejects_shared_construction_mutants(
    mutant: str,
) -> None:
    global _member_digest, _s41_canonical_bytes, _s41_digest, _s41_without
    original_digest = _s41_digest
    original_without = _s41_without
    original_canonical = _s41_canonical_bytes
    original_member_digest = _member_digest

    def domain_poison(domain: str, identity: object) -> str:
        if domain == "governed-execution.nwp-cognitive-mutation-receipt.v1.identity":
            return hashlib.sha256(
                b"WRONG-RECEIPT-DOMAIN\x00" + original_canonical(identity)
            ).hexdigest()
        return original_digest(domain, identity)

    def exclusion_poison(
        mapping: dict[str, object],
        field: str,
    ) -> dict[str, object]:
        excluded = original_without(mapping, field)
        if (
            field == "receipt_digest"
            and mapping.get("schema_id")
            == "governed-execution.nwp-cognitive-mutation-receipt.v1"
        ):
            excluded.pop("committed_at", None)
        return excluded

    def canonical_poison(value: object) -> bytes:
        encoded = original_canonical(value)
        if type(value) is dict and value.get("mutation_family") == (
            "record_pre_execution_plan_disposition"
        ):
            return encoded + b" "
        return encoded

    def graph_poison(member: dict[str, object]) -> str:
        digest = original_member_digest(member)
        if member["role"] == "source_invocation":
            return "f" * 64 if digest != "f" * 64 else "e" * 64
        return digest

    try:
        if mutant == "receipt-domain":
            _s41_digest = domain_poison
        elif mutant == "receipt-exclusion":
            _s41_without = exclusion_poison
        elif mutant == "receipt-canonicalization":
            _s41_canonical_bytes = canonical_poison
        elif mutant == "graph-member-binding":
            _member_digest = graph_poison
        else:
            raise AssertionError(mutant)
        family = _build_repaired_physical_family(False)
        _validate_repaired_physical_family(family)
        assert _independent_repaired_family_is_valid(family) is False
    finally:
        _s41_digest = original_digest
        _s41_without = original_without
        _s41_canonical_bytes = original_canonical
        _member_digest = original_member_digest


def test_nine_repair_independent_oracle_rejects_row_field_order_mutant() -> None:
    family = _build_repaired_physical_family(False)
    receipt = family["receipt"]["values"]
    reordered = {
        **{key: value for key, value in receipt.items() if key != "schema_id"},
        "schema_id": receipt["schema_id"],
    }
    family["receipt"]["values"] = reordered
    assert _independent_repaired_family_is_valid(family) is False


def _extra_recovery_readiness_member(
    family: dict[str, object],
    *,
    foreign_evidence_set: bool = False,
) -> dict[str, object]:
    member = deepcopy(
        next(
            row
            for row in _build_repaired_physical_family(True)["physical_rows"]
            if row["role"] == "evidence.qualified_remote_host_readiness"
        )
    )
    rows_by_role = {row["role"]: row for row in family["physical_rows"]}
    proposal = rows_by_role["model_proposal"]["values"]
    values = member["values"]
    values.update(
        {
            "proposal_ref": proposal["proposal_ref"],
            "evidence_set_ref": (
                "proposal-evidence.foreign.valid.0001"
                if foreign_evidence_set
                else proposal["evidence_set_ref"]
            ),
        }
    )
    values["evidence_binding_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[5],
        values,
    )
    return member


def _insert_complete_family_except_roles(
    connection: sqlite3.Connection,
    family: dict[str, object],
    omitted_roles: tuple[str, ...] = (),
) -> None:
    for member in family["physical_rows"]:
        if member["role"] not in omitted_roles:
            _insert_exact_repaired_values(
                connection,
                member["table"],
                member["values"],
            )


def _replace_evidence_table_with_permissive_diagnostic(
    connection: sqlite3.Connection,
    members: tuple[dict[str, object], ...],
) -> None:
    table = REPAIRED_TABLE_ORDER[5]
    connection.commit()
    connection.execute("PRAGMA foreign_keys=OFF")
    connection.execute(f'DROP TRIGGER "{table}_no_update"')
    connection.execute(f'DROP TRIGGER "{table}_no_delete"')
    connection.execute(f'DROP TABLE "{table}"')
    connection.execute(
        f'CREATE TABLE "{table}" ('
        + ",".join(
            f'"{field}" ANY' for field, _kind in REPAIRED_TABLE_COLUMNS[table]
        )
        + ") STRICT"
    )
    for member in members:
        _insert_exact_repaired_values(connection, table, member["values"])
    connection.commit()
    connection.execute("PRAGMA foreign_keys=ON")


@pytest.mark.parametrize("readiness_present", (False, True), ids=("absent", "present"))
def test_a2_revised_exact_evidence_inventory_recovers_receipt_result(
    readiness_present: bool,
) -> None:
    family = _build_repaired_physical_family(readiness_present)
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        _insert_complete_family_except_roles(connection, family)
        connection.commit()
        changes_before = connection.total_changes
        recovered = _recover_repaired_family(
            connection,
            expected_family=family,
            expected_head_preimage=None,
            fresh_writer_verified=True,
        )
        assert recovered == _RecoveryReadback(
            "committed_exact",
            0,
            family["replay_result"],
        )
        assert recovered.result is not family["replay_result"]
        assert connection.total_changes == changes_before
    finally:
        connection.close()


@pytest.mark.parametrize(
    "case_name",
    (
        "extra-rank-19",
        "missing-rank-19",
        "foreign-evidence-set",
        "unknown-role",
        "wrong-rank",
        "wrong-ordinal",
        "wrong-required",
        "wrong-evidence-digest",
        "wrong-row-digest",
        "malformed-row",
        "duplicate-row",
        "overflow-row-16",
    ),
)
def test_a2_revised_evidence_inventory_rejects_every_nonexact_inventory(
    case_name: str,
) -> None:
    readiness_present = case_name == "missing-rank-19"
    family = _build_repaired_physical_family(readiness_present)
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        if case_name == "missing-rank-19":
            _insert_complete_family_except_roles(
                connection,
                family,
                ("evidence.qualified_remote_host_readiness",),
            )
        else:
            _insert_complete_family_except_roles(connection, family)
            extra = _extra_recovery_readiness_member(
                family,
                foreign_evidence_set=case_name == "foreign-evidence-set",
            )
            if case_name in ("extra-rank-19", "foreign-evidence-set"):
                _insert_exact_repaired_values(
                    connection,
                    extra["table"],
                    extra["values"],
                )
            else:
                evidence_members = tuple(
                    deepcopy(member)
                    for member in family["physical_rows"]
                    if member["table"] == REPAIRED_TABLE_ORDER[5]
                )
                extras = [extra]
                if case_name == "unknown-role":
                    extra["values"]["evidence_role"] = "unknown_role"
                    extra["values"]["evidence_binding_digest"] = (
                        _repaired_row_digest(extra["table"], extra["values"])
                    )
                elif case_name == "wrong-rank":
                    extra["values"]["role_rank"] = 20
                    extra["values"]["evidence_binding_digest"] = (
                        _repaired_row_digest(extra["table"], extra["values"])
                    )
                elif case_name == "wrong-ordinal":
                    extra["values"]["ordinal"] = 1
                    extra["values"]["evidence_binding_digest"] = (
                        _repaired_row_digest(extra["table"], extra["values"])
                    )
                elif case_name == "wrong-required":
                    extra["values"]["required_for_selection"] = 1
                    extra["values"]["evidence_binding_digest"] = (
                        _repaired_row_digest(extra["table"], extra["values"])
                    )
                elif case_name == "wrong-evidence-digest":
                    extra["values"]["evidence_digest"] = "f" * 64
                    extra["values"]["evidence_binding_digest"] = (
                        _repaired_row_digest(extra["table"], extra["values"])
                    )
                elif case_name == "wrong-row-digest":
                    extra["values"]["evidence_binding_digest"] = "f" * 64
                elif case_name == "malformed-row":
                    extra["values"]["schema_id"] = 1
                elif case_name == "duplicate-row":
                    extras = [deepcopy(evidence_members[0])]
                elif case_name == "overflow-row-16":
                    second = deepcopy(extra)
                    second["values"].update(
                        {
                            "evidence_role": "overflow_unknown_role",
                            "role_rank": 20,
                            "ordinal": 1,
                        }
                    )
                    second["values"]["evidence_binding_digest"] = (
                        _repaired_row_digest(second["table"], second["values"])
                    )
                    extras.append(second)
                else:
                    raise AssertionError(case_name)
                _replace_evidence_table_with_permissive_diagnostic(
                    connection,
                    (*evidence_members, *extras),
                )
        connection.commit()
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        changes_before = connection.total_changes
        trace: list[str] = []
        connection.set_trace_callback(trace.append)
        recovered = _recover_repaired_family(
            connection,
            expected_family=family,
            expected_head_preimage=None,
            fresh_writer_verified=True,
        )
        connection.set_trace_callback(None)
        assert recovered == _RecoveryReadback("unresolved", 0, None)
        assert connection.total_changes == changes_before
        assert not any(
            statement.lstrip().upper().startswith(
                ("INSERT", "UPDATE", "DELETE", "REPLACE", "COMMIT")
            )
            for statement in trace
        )
    finally:
        connection.close()


def test_a2_revised_evidence_inventory_query_is_complete_bounded_and_unfiltered() -> None:
    assert _EVIDENCE_INVENTORY_LIMIT == 16
    assert _EVIDENCE_INVENTORY_QUERY == (
        "SELECT "
        + ",".join(_EVIDENCE_RECOVERY_FIELDS)
        + f' FROM "{REPAIRED_TABLE_ORDER[5]}" WHERE proposal_ref=? ORDER BY '
        + ",".join(
            f'"{field}"' for field in _EVIDENCE_INVENTORY_ORDER_FIELDS
        )
        + " LIMIT 16"
    )
    where_clause = _EVIDENCE_INVENTORY_QUERY.split(" WHERE ", 1)[1].split(
        " ORDER BY ", 1
    )[0]
    assert where_clause == "proposal_ref=?"
    assert tuple(_EVIDENCE_RECOVERY_FIELDS) == tuple(
        field for field, _kind in REPAIRED_TABLE_COLUMNS[REPAIRED_TABLE_ORDER[5]]
    )


def _layer_a_control_values() -> tuple[dict[str, object], dict[str, object]]:
    root = _build_repaired_physical_family(False)
    successor = _build_repaired_successor_family(
        root,
        suffix="a2-layer-a-control.0001",
    )
    root_disposition = next(
        row["values"]
        for row in root["physical_rows"]
        if row["role"] == "coordinator_disposition"
    )
    successor_disposition = next(
        row["values"]
        for row in successor["physical_rows"]
        if row["role"] == "coordinator_disposition"
    )
    return root_disposition, successor_disposition


def test_a2_revised_target_relation_is_mechanically_extracted_from_installed_ddl(
    a2_revised_extracted_predecessor_relation: tuple[
        tuple[tuple[str, ...], str, tuple[str, ...], str, str, str],
        dict[str, str],
    ],
) -> None:
    relation, column_types = a2_revised_extracted_predecessor_relation
    local, parent_table, referenced, on_update, on_delete, match = relation
    assert local == (
        *REPAIRED_C2B3D_LINEAGE_FIELDS,
        "supersedes_disposition_ref",
        "prior_selection_head_revision",
        "prior_selection_head_digest",
    )
    assert parent_table == REPAIRED_TABLE_ORDER[6]
    assert referenced == (
        *REPAIRED_C2B3D_LINEAGE_FIELDS,
        "disposition_ref",
        "resulting_selection_head_revision",
        "selection_head_postimage_digest",
    )
    assert len(local) == len(referenced) == 37
    assert len(local[:34]) == 34
    assert len(set(local)) == len(local)
    assert len(set(referenced)) == len(referenced)
    assert (on_update, on_delete, match) == ("RESTRICT", "RESTRICT", "NONE")
    assert set(local) | set(referenced) <= set(column_types)
    assert all(column_types[field] == "ANY" for field in set(local) | set(referenced))


def test_a2_revised_layer_a_exact_control_inserts(
    a2_revised_extracted_predecessor_relation: tuple[
        tuple[tuple[str, ...], str, tuple[str, ...], str, str, str],
        dict[str, str],
    ],
) -> None:
    relation, column_types = a2_revised_extracted_predecessor_relation
    parent, child = _layer_a_control_values()
    connection = _layer_a_relation_schema(
        relation,
        column_types,
        include_relation=True,
    )
    try:
        _insert_layer_a_parent_and_child(connection, relation, parent, child)
        connection.commit()
        assert connection.execute("SELECT count(*) FROM extracted_parent").fetchone() == (1,)
        assert connection.execute("SELECT count(*) FROM extracted_child").fetchone() == (1,)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()


@pytest.mark.parametrize("field", REPAIRED_C2B3D_LINEAGE_FIELDS)
def test_a2_revised_layer_a_isolates_each_extracted_lineage_coordinate(
    field: str,
    a2_revised_extracted_predecessor_relation: tuple[
        tuple[tuple[str, ...], str, tuple[str, ...], str, str, str],
        dict[str, str],
    ],
) -> None:
    relation, column_types = a2_revised_extracted_predecessor_relation
    parent, child = _layer_a_control_values()
    mutated = deepcopy(child)
    kind = dict(REPAIRED_C2B3D_LINEAGE_FIELD_SPECS)[field]
    mutated[field] = _repair_alternate_scalar(mutated[field], kind)
    assert sum(
        not _s41_exact_equal(mutated[name], child[name])
        for name in REPAIRED_C2B3D_LINEAGE_FIELDS
    ) == 1

    complete = _layer_a_relation_schema(
        relation,
        column_types,
        include_relation=True,
    )
    try:
        with pytest.raises(sqlite3.IntegrityError) as caught:
            _insert_layer_a_parent_and_child(complete, relation, parent, mutated)
        assert caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_FOREIGNKEY"
        assert complete.in_transaction is True
        assert complete.execute("SELECT count(*) FROM extracted_child").fetchone() == (0,)
        complete.rollback()
        assert complete.in_transaction is False
        assert complete.execute("SELECT count(*) FROM extracted_child").fetchone() == (0,)
        assert complete.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        complete.close()

    absent = _layer_a_relation_schema(
        relation,
        column_types,
        include_relation=False,
    )
    try:
        _insert_layer_a_parent_and_child(absent, relation, parent, mutated)
        absent.commit()
        assert absent.execute("SELECT count(*) FROM extracted_child").fetchone() == (1,)
        assert absent.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        absent.close()


def test_a2_revised_layer_b_classification_and_single_relation_ablation_are_exact() -> None:
    assert len(REVISED_LAYER_B_TARGET_EXCLUSIVE_FIELDS) == 23
    assert len(REVISED_LAYER_B_OVERLAPPING_FIELDS) == 11
    assert set(REVISED_LAYER_B_TARGET_EXCLUSIVE_FIELDS).isdisjoint(
        REVISED_LAYER_B_OVERLAPPING_FIELDS
    )
    assert set(REVISED_LAYER_B_TARGET_EXCLUSIVE_FIELDS) | set(
        REVISED_LAYER_B_OVERLAPPING_FIELDS
    ) == set(REPAIRED_C2B3D_LINEAGE_FIELDS)
    complete, _inventory = _install_repaired_temporary_schema()
    try:
        relation = _extract_installed_predecessor_relation(complete)
        complete_set = set(
            _observed_sqlite_foreign_keys(complete, REPAIRED_TABLE_ORDER[6])
        )
    finally:
        complete.close()
    ablated_keys = _ablated_repaired_foreign_keys(relation)
    ablated, _inventory = _install_repaired_temporary_schema(
        repaired_table_ddl=_build_repaired_table_ddl(ablated_keys),
    )
    try:
        ablated_set = set(
            _observed_sqlite_foreign_keys(ablated, REPAIRED_TABLE_ORDER[6])
        )
        assert complete_set - ablated_set == {relation}
        assert not ablated_set - complete_set
        assert len(complete_set) - len(ablated_set) == 1
    finally:
        ablated.close()
    for field in REVISED_LAYER_B_OVERLAPPING_FIELDS:
        relations = _retained_overlap_relations(field)
        assert relations
        assert all(field in child for child, _table, _parent, _timing in relations)
    assert REVISED_LAYER_B_ALTERNATE_PARENT_ISOLATABLE == {
        "program_ref": False,
        "program_version_ref": True,
        "accepted_intent_revision_ref": True,
        "work_item_ref": False,
        "work_item_revision_ref": True,
        "semantic_attempt_ref": True,
        "effect_intent_ref": True,
        "author_command_ref": True,
        "attempt_fence_ref": True,
        "effect_fence_ref": True,
        "delivery_attempt_ref": True,
    }
    assert tuple(REVISED_LAYER_B_NONISOLATABLE_EXPLANATIONS) == (
        "program_ref",
        "work_item_ref",
    )
    key_connection, _inventory = _install_repaired_temporary_schema()
    try:
        disposition_primary_key = next(
            key
            for key in _declared_unique_column_sets(
                key_connection,
                REPAIRED_TABLE_ORDER[6],
            )
            if key == ("disposition_ref",)
        )
        assert disposition_primary_key == ("disposition_ref",)
    finally:
        key_connection.close()


def test_a2_revised_selection_head_graph_locator_is_exact_primary_key() -> None:
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        table = REPAIRED_TABLE_ORDER[7]
        table_info = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
        primary_key = tuple(
            row[1] for row in sorted(table_info, key=lambda row: row[5]) if row[5]
        )
        assert primary_key == REPAIRED_SELECTION_HEAD_CURRENTNESS_KEY_FIELDS
        assert primary_key == INDEPENDENT_REPAIRED_SELECTION_HEAD_PRIMARY_KEY_FIELDS
        assert len(primary_key) == 8
        for readiness_present in (False, True):
            family = _build_repaired_physical_family(readiness_present)
            head_member = next(
                row
                for row in family["physical_rows"]
                if row["role"] == "selection_head_postimage"
            )
            direct = _member_locator(head_member)
            independent = _independent_repaired_locator(
                head_member["table"],
                head_member["values"],
            )
            assert tuple(field for field, _value in direct) == primary_key
            assert direct == independent
            assert len(direct) == 8
            assert len(family["physical_rows"]) == (23 if readiness_present else 22)
            assert len(family["graph"]["entries"]) == (
                22 if readiness_present else 21
            )
            assert family["receipt"] in family["physical_rows"]
            assert all(
                entry["role"] != "receipt" for entry in family["graph"]["entries"]
            )
    finally:
        connection.close()


def test_a2_revised_full_lineage_locator_mutant_fails_after_complete_redigest() -> None:
    family = _build_repaired_physical_family(False)
    graph = family["graph"]
    head = next(
        row
        for row in family["physical_rows"]
        if row["role"] == "selection_head_postimage"
    )
    head_entry = next(
        entry for entry in graph["entries"] if entry["role"] == head["role"]
    )
    head_entry["locator"] = tuple(
        (field, head["values"][field]) for field in REPAIRED_LINEAGE_COLUMNS
    )
    assert len(head_entry["locator"]) == 34
    graph["mutation_graph_digest"] = _s41_digest(
        DIGEST_DOMAINS["mutation_graph"],
        _s41_without(graph, "mutation_graph_digest"),
    )
    projection = family["result_projection"]
    projection["mutation_graph_digest"] = graph["mutation_graph_digest"]
    projection["result_projection_digest"] = _s41_digest(
        DIGEST_DOMAINS["result"],
        _s41_without(projection, "result_projection_digest"),
    )
    receipt = family["receipt"]["values"]
    receipt["mutation_graph_digest"] = graph["mutation_graph_digest"]
    receipt["result_projection_digest"] = projection["result_projection_digest"]
    receipt["receipt_digest"] = _repaired_row_digest(
        REPAIRED_TABLE_ORDER[8],
        receipt,
    )
    family["fresh_result"] = {**projection, "receipt_digest": receipt["receipt_digest"]}
    family["replay_result"] = deepcopy(family["fresh_result"])
    with pytest.raises(_ContractViolation) as caught:
        _validate_repaired_physical_family(family)
    assert caught.value.reason == "physical_family_graph_digest_mismatch"


def test_a2_revised_selection_head_row_digest_still_binds_all_34_lineage_fields() -> None:
    family = _build_repaired_physical_family(False)
    head = next(
        row["values"]
        for row in family["physical_rows"]
        if row["role"] == "selection_head_postimage"
    )
    original = head["head_digest"]
    for field, kind in REPAIRED_C2B3D_LINEAGE_FIELD_SPECS:
        mutated = deepcopy(head)
        mutated[field] = _repair_alternate_scalar(mutated[field], kind)
        assert _repaired_row_digest(REPAIRED_TABLE_ORDER[7], mutated) != original
        assert (
            _independent_repaired_row_digest(REPAIRED_TABLE_ORDER[7], mutated)
            != original
        )


def test_a2_revised_outer_recovery_returns_actual_result_at_0_1_and_256() -> None:
    family = _build_repaired_physical_family(False)
    original_result = deepcopy(family["replay_result"])
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        _insert_expected_recovery_family(
            connection,
            family,
            replace_existing_head=False,
        )
        connection.commit()
        trace: list[str] = []
        connection.set_trace_callback(trace.append)

        changes_before = connection.total_changes
        root = _recover_repaired_family(
            connection,
            expected_family=family,
            expected_head_preimage=None,
            fresh_writer_verified=True,
        )
        assert root == _RecoveryReadback("committed_exact", 0, original_result)
        assert root.result is not family["replay_result"]
        assert connection.total_changes == changes_before

        lineage = tuple(
            next(
                row["values"]
                for row in family["physical_rows"]
                if row["role"] == "coordinator_disposition"
            )[field]
            for field in REPAIRED_LINEAGE_COLUMNS
        )
        predecessor_ref = family["receipt"]["values"]["disposition_ref"]
        predecessor_digest = family["receipt"]["values"]["selection_head_digest"]
        for revision in range(1, 258):
            successor_ref, successor_digest = _insert_sqlite_successor(
                connection,
                lineage=lineage,
                predecessor_ref=predecessor_ref,
                predecessor_revision=revision - 1,
                predecessor_digest=predecessor_digest,
                revision=revision,
                suffix=f"a2-recovery-depth-{revision:04d}",
            )
            _advance_sqlite_head(
                connection,
                lineage,
                successor_ref,
                revision,
                successor_digest,
            )
            predecessor_ref = successor_ref
            predecessor_digest = successor_digest
            if revision in (1, 256, 257):
                connection.commit()
                checkpoint_changes = connection.total_changes
                recovered = _recover_repaired_family(
                    connection,
                    expected_family=family,
                    expected_head_preimage=None,
                    fresh_writer_verified=True,
                )
                assert connection.total_changes == checkpoint_changes
                if revision in (1, 256):
                    assert recovered == _RecoveryReadback(
                        "committed_exact",
                        revision,
                        original_result,
                    )
                    assert recovered.result is not family["replay_result"]
                else:
                    assert recovered == _RecoveryReadback("unresolved", 257, None)

        connection.set_trace_callback(None)
        recovery_statements = tuple(
            statement
            for statement in trace
            if statement.lstrip().upper().startswith("SELECT")
        )
        assert recovery_statements
        assert not any(
            statement.lstrip().upper().startswith(
                ("INSERT", "UPDATE", "DELETE", "REPLACE")
            )
            for statement in trace
            if "a2-recovery-depth" not in statement
        )
    finally:
        connection.close()


def test_a2_revised_noncommitted_recovery_readbacks_never_expose_results() -> None:
    family = _build_repaired_physical_family(False)
    connection, _inventory = _install_repaired_temporary_schema()
    try:
        absent = _recover_repaired_family(
            connection,
            expected_family=family,
            expected_head_preimage=None,
            fresh_writer_verified=True,
        )
        assert absent == _RecoveryReadback("definitely_not_committed", 0, None)
        member = family["physical_rows"][0]
        _insert_exact_repaired_values(connection, member["table"], member["values"])
        connection.commit()
        incomplete = _recover_repaired_family(
            connection,
            expected_family=family,
            expected_head_preimage=None,
            fresh_writer_verified=True,
        )
        assert incomplete == _RecoveryReadback("unresolved", 0, None)
    finally:
        connection.close()
