from __future__ import annotations

import ast
import copy
import inspect
import json
from pathlib import Path
import pickle

import pytest

import ge_nwp_coordinator
from ge_nwp_coordinator import _sqlite_development_reader_contracts as contracts
from ge_nwp_coordinator import _sqlite_development_readers as readers
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _MutationReadCapabilityError,
    _MutationReadCapabilityFailureReason,
    _execute_select_fetch_bounded,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_PATH = ROOT / "src/ge_nwp_coordinator/_sqlite_development_reader_contracts.py"
READERS_PATH = ROOT / "src/ge_nwp_coordinator/_sqlite_development_readers.py"
SELECT_SUPPORT_PATH = ROOT / "src/ge_nwp_coordinator/sqlite_transition_select_support.py"
OWNER_PATH = ROOT / ".docs/c2b-durable-development-state.md"
EXPECTED_PRODUCTION_READER_IMPORTERS = (
    "_sqlite_development_author_effect_establishment.py",
    "_sqlite_development_pre_execution_plan_disposition.py",
    "_sqlite_development_program_initialization.py",
    "_sqlite_rw0_c1.py",
)
EXPECTED_SECTION41_READER_CALLS = (
    "_read_development_attempt_fence_command_effect_aggregate",
    "_read_development_authority_evaluation_by_exact_ref",
    "_read_development_delivery_head",
    "_read_development_effect_head",
    "_read_development_program_head_and_current_version",
    "_read_development_work_item_head_and_revision_by_exact_ref",
    "_read_development_work_spec_safe_binding",
)

EXPECTED_QUERY_SPECIFICATION_NAMES = (
    "_MUTATION_RECEIPT_SELECT",
    "_DECISION_SELECT",
    "_PROGRAM_HEAD_SELECT",
    "_CURRENT_PROGRAM_VERSION_SELECT",
    "_INITIALIZE_DECISION_SELECT",
    "_RESULTING_PROGRAM_VERSION_SELECT",
    "_ACCEPTED_INTENT_REVISION_SELECT",
    "_WORK_ITEM_HEAD_SELECT",
    "_WORK_ITEM_REVISION_SELECT",
    "_PROGRAM_VERSION_ROOT_SELECT",
    "_MEMBERSHIP_FIRST_PAGE_SELECT",
    "_MEMBERSHIP_CONTINUATION_PAGE_SELECT",
    "_MEMBERSHIP_WORK_ITEM_REVISION_SELECT",
    "_WORK_SPEC_SAFE_BINDING_SELECT",
    "_EFFECT_INTENT_ROOT_SELECT",
    "_SEMANTIC_ATTEMPT_SELECT",
    "_AUTHOR_COMMAND_SELECT",
    "_ATTEMPT_FENCE_SELECT",
    "_CURRENT_EFFECT_FENCE_SELECT",
    "_AUTHOR_EFFECT_FENCE_SELECT",
    "_AUTHORITY_EVALUATION_SELECT",
    "_EFFECT_HEAD_SELECT",
    "_DELIVERY_HEAD_SELECT",
    "_CURRENT_DELIVERY_ATTEMPT_SELECT",
)

EXPECTED_AGGREGATE_TYPE_NAMES = (
    "DevelopmentProgramHeadAndCurrentVersionRead",
    "DevelopmentInitializeDecisionAndResultingVersionRead",
    "DevelopmentWorkItemHeadAndRevisionRead",
    "DevelopmentProgramVersionMembershipEntry",
    "DevelopmentProgramVersionMembershipRead",
    "DevelopmentAttemptFenceCommandEffectRead",
    "DevelopmentDeliveryHeadAndCurrentAttemptRead",
)

EXPECTED_IMPLEMENTATION_PATHS = (
    "src/ge_nwp_coordinator/_sqlite_development_reader_contracts.py",
    "src/ge_nwp_coordinator/_sqlite_development_readers.py",
    "src/ge_nwp_coordinator/sqlite_transition_select_support.py",
    ".docs/c2b2-private-readers.md",
    ".docs/c2b-durable-development-state.md",
    ".docs/c2b2-migration-0002.md",
    ".docs/c2b2-pure-durable-row-values.md",
    ".docs/architecture.md",
    ".docs/autonomous-software-development-operating-model.md",
    ".docs/durable-state-model.md",
    ".docs/software-development-progression-boundary.md",
    ".docs/sqlite-threat-model.md",
    "README.md",
    "AGENTS.md",
    "tests/test_c2b2_development_reader_contracts.py",
    "tests/test_c2b2_private_development_readers.py",
    "tests/test_c2b2_field_level_contract.py",
    "tests/test_c2b0_durable_state_contract.py",
    "tests/test_architecture_contracts.py",
    "tests/test_autonomous_software_development_operating_model.py",
    "tests/test_software_development_progression_boundary.py",
    "tests/test_runtime_non_authority.py",
    "tests/test_c2a_nonimplementation.py",
)

EXPECTED_AGGREGATE_FIELDS = {
    "DevelopmentProgramHeadAndCurrentVersionRead": (
        "program_head",
        "current_program_version",
    ),
    "DevelopmentInitializeDecisionAndResultingVersionRead": (
        "initialize_decision",
        "resulting_program_version",
    ),
    "DevelopmentWorkItemHeadAndRevisionRead": (
        "work_item_head",
        "work_item_revision",
        "is_current",
    ),
    "DevelopmentProgramVersionMembershipEntry": (
        "membership",
        "work_item_revision",
    ),
    "DevelopmentProgramVersionMembershipRead": ("program_version", "entries"),
    "DevelopmentAttemptFenceCommandEffectRead": (
        "semantic_attempt",
        "effect_intent",
        "author_command",
        "attempt_fence",
        "current_effect_fence",
        "author_effect_fence",
    ),
    "DevelopmentDeliveryHeadAndCurrentAttemptRead": (
        "delivery_head",
        "current_delivery_attempt",
    ),
}

EXPECTED_READER_SIGNATURES = {
    "_read_development_mutation_receipt_by_mutation_ref": (
        ("capability", "mutation_ref"),
        "DevelopmentMutationReceiptRowValue | None",
    ),
    "_read_development_decision_by_decision_ref": (
        ("capability", "decision_ref"),
        "DevelopmentDecisionRowValue | None",
    ),
    "_read_development_program_head_and_current_version": (
        ("capability", "program_ref"),
        "DevelopmentProgramHeadAndCurrentVersionRead | None",
    ),
    "_read_development_initialize_decision_and_resulting_version": (
        ("capability", "program_ref", "decision_ref"),
        "DevelopmentInitializeDecisionAndResultingVersionRead | None",
    ),
    "_read_development_accepted_intent_revision_by_exact_ref": (
        ("capability", "program_ref", "accepted_intent_revision_ref"),
        "DevelopmentAcceptedIntentRevisionRowValue | None",
    ),
    "_read_development_work_item_head_and_revision_by_exact_ref": (
        ("capability", "program_ref", "work_item_ref", "work_item_revision_ref"),
        "DevelopmentWorkItemHeadAndRevisionRead | None",
    ),
    "_read_development_paged_program_version_membership": (
        ("capability", "program_ref", "program_version_ref", "maximum_members"),
        "DevelopmentProgramVersionMembershipRead | None",
    ),
    "_read_development_work_spec_safe_binding": (
        (
            "capability",
            "program_ref",
            "program_version_ref",
            "work_item_ref",
            "work_item_revision_ref",
        ),
        "DevelopmentWorkSpecBindingRowValue | None",
    ),
    "_read_development_attempt_fence_command_effect_aggregate": (
        ("capability", "program_ref", "semantic_attempt_ref", "effect_intent_ref"),
        "DevelopmentAttemptFenceCommandEffectRead | None",
    ),
    "_read_development_authority_evaluation_by_exact_ref": (
        ("capability", "program_ref", "authority_evaluation_ref"),
        "DevelopmentAuthorityEvaluationRowValue | None",
    ),
    "_read_development_effect_head": (
        ("capability", "program_ref", "effect_intent_ref"),
        "DevelopmentEffectHeadRowValue | None",
    ),
    "_read_development_delivery_head": (
        ("capability", "program_ref", "effect_intent_ref"),
        "DevelopmentDeliveryHeadAndCurrentAttemptRead | None",
    ),
}

PROGRAM_HEAD_COLUMNS = (
    "schema_id", "program_ref", "current_program_version_ref",
    "current_program_version_number", "head_revision", "program_state",
    "updated_at", "head_digest",
)
PROGRAM_VERSION_COLUMNS = (
    "schema_id", "program_version_ref", "program_ref", "program_version_number",
    "program_version_kind", "creating_decision_ref", "accepted_intent_revision_ref",
    "created_at", "program_version_digest",
)
ACCEPTED_INTENT_COLUMNS = (
    "schema_id", "accepted_intent_revision_ref", "program_ref",
    "accepted_intent_revision_number", "prior_accepted_intent_revision_ref",
    "source_intent_ref", "source_intent_digest", "safe_projection_digest",
    "created_at", "accepted_intent_revision_digest",
)
WORK_ITEM_HEAD_COLUMNS = (
    "schema_id", "work_item_ref", "program_ref", "current_work_item_revision_ref",
    "current_work_item_revision_number", "head_revision", "work_state",
    "updated_at", "head_digest",
)
WORK_ITEM_REVISION_COLUMNS = (
    "schema_id", "work_item_revision_ref", "program_ref", "work_item_ref",
    "work_item_revision_number", "work_item_revision_kind",
    "prior_work_item_revision_ref", "accepted_intent_revision_ref", "created_at",
    "work_item_revision_digest",
)
MEMBERSHIP_COLUMNS = (
    "schema_id", "program_ref", "program_version_ref", "work_item_ref",
    "work_item_revision_ref", "membership_ordinal", "created_at", "membership_digest",
)
WORK_SPEC_COLUMNS = (
    "schema_id", "work_spec_ref", "program_ref", "program_version_ref",
    "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref",
    "repository_ref", "base_git_object_format", "base_git_oid",
    "authorized_paths_json", "validation_requirement_ref", "review_requirement_ref",
    "privacy_classification", "work_spec_digest", "safe_projection_digest",
    "recorded_at", "work_spec_binding_digest",
)
SEMANTIC_ATTEMPT_COLUMNS = (
    "schema_id", "semantic_attempt_ref", "program_ref", "program_version_ref",
    "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref",
    "attempt_number", "candidate_ref", "attempt_phase", "selection_decision_ref",
    "created_at", "semantic_attempt_digest",
)
ATTEMPT_FENCE_COLUMNS = (
    "schema_id", "attempt_fence_ref", "parent_standing_grant_ref",
    "parent_standing_grant_digest", "attempt_authorization_ref",
    "attempt_authorization_digest", "program_ref", "program_version_ref",
    "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref",
    "semantic_attempt_ref", "repository_ref", "base_git_object_format",
    "base_git_oid", "path_ceiling_json", "allowed_effect_class_mask",
    "aggregate_max_active_invocations", "aggregate_max_candidate_bytes",
    "aggregate_max_changed_files", "aggregate_max_cost_microusd",
    "aggregate_max_cpu_seconds", "aggregate_max_deliveries",
    "aggregate_max_deployments", "aggregate_max_local_commits",
    "aggregate_max_memory_bytes", "aggregate_max_merges",
    "aggregate_max_model_input_tokens", "aggregate_max_model_output_tokens",
    "aggregate_max_pull_requests", "aggregate_max_pushes",
    "aggregate_max_wall_seconds", "expires_at", "global_stop_ref",
    "global_stop_version", "attempt_fence_digest", "recorded_at",
)
AUTHORITY_COLUMNS = (
    "schema_id", "authority_evaluation_ref", "program_ref", "evaluation_scope",
    "evaluation_subject_ref", "semantic_attempt_ref", "effect_intent_ref",
    "authority_ref", "authority_digest", "authority_state", "reason_code",
    "expires_at", "evaluated_at", "authority_evaluation_digest",
)
EFFECT_INTENT_COLUMNS = (
    "schema_id", "effect_intent_ref", "program_ref", "program_version_ref",
    "semantic_attempt_ref", "effect_class", "candidate_ref", "command_ref",
    "basis_decision_ref", "cancellation_target_effect_intent_ref",
    "expected_target_effect_head_revision", "portable_capsule_digest", "created_at",
    "effect_intent_digest",
)
EFFECT_FENCE_COLUMNS = (
    "schema_id", "effect_fence_ref", "parent_standing_grant_ref",
    "parent_standing_grant_digest", "effect_authorization_ref",
    "effect_authorization_digest", "attempt_fence_ref", "attempt_fence_digest",
    "program_ref", "program_version_ref", "accepted_intent_revision_ref",
    "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
    "effect_intent_ref", "effect_class", "command_ref", "command_digest",
    "candidate_ref", "repository_ref", "base_git_object_format", "base_git_oid",
    "path_ceiling_json", "effect_max_active_invocations",
    "effect_max_candidate_bytes", "effect_max_changed_files",
    "effect_max_cost_microusd", "effect_max_cpu_seconds", "effect_max_deliveries",
    "effect_max_deployments", "effect_max_local_commits", "effect_max_memory_bytes",
    "effect_max_merges", "effect_max_model_input_tokens",
    "effect_max_model_output_tokens", "effect_max_pull_requests",
    "effect_max_pushes", "effect_max_wall_seconds", "expires_at",
    "global_stop_ref", "global_stop_version", "portable_capsule_digest",
    "cancellation_target_effect_intent_ref", "cancellation_target_effect_fence_ref",
    "cancellation_target_effect_fence_digest", "effect_fence_digest", "recorded_at",
)
AUTHOR_COMMAND_COLUMNS = (
    "schema_id", "command_ref", "program_ref", "program_version_ref",
    "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref",
    "semantic_attempt_ref", "effect_intent_ref", "effect_class", "candidate_ref",
    "repository_ref", "base_git_object_format", "base_git_oid", "path_ceiling_json",
    "work_spec_ref", "work_spec_digest", "standing_grant_ref",
    "standing_grant_digest", "attempt_authorization_ref",
    "attempt_authorization_digest", "effect_authorization_ref",
    "effect_authorization_digest", "attempt_fence_ref", "attempt_fence_digest",
    "effect_fence_ref", "effect_fence_digest", "global_stop_ref",
    "global_stop_version", "validation_requirement_ref",
    "validation_requirement_digest", "review_requirement_ref",
    "review_requirement_digest", "capsule_schema_id", "capsule_profile_ref",
    "effect_max_active_invocations", "effect_max_candidate_bytes",
    "effect_max_changed_files", "effect_max_cost_microusd", "effect_max_cpu_seconds",
    "effect_max_deliveries", "effect_max_deployments", "effect_max_local_commits",
    "effect_max_memory_bytes", "effect_max_merges", "effect_max_model_input_tokens",
    "effect_max_model_output_tokens", "effect_max_pull_requests", "effect_max_pushes",
    "effect_max_wall_seconds", "privacy_classification", "redaction_profile_ref",
    "command_digest", "recorded_at",
)
EFFECT_HEAD_COLUMNS = (
    "schema_id", "effect_intent_ref", "program_ref", "current_effect_fence_ref",
    "head_revision", "effect_state", "cancellation_effect_intent_ref",
    "updated_at", "head_digest",
)
DELIVERY_ATTEMPT_COLUMNS = (
    "schema_id", "delivery_attempt_ref", "program_ref", "program_version_ref",
    "command_ref", "command_digest", "semantic_attempt_ref", "effect_intent_ref",
    "attempt_fence_ref", "attempt_fence_digest", "effect_fence_ref",
    "effect_fence_digest", "adapter_kind", "adapter_safe_correlation_ref",
    "delivery_envelope_digest", "delivery_kind", "delivery_number",
    "predecessor_delivery_attempt_ref", "basis_decision_ref", "recorded_at",
    "delivery_attempt_digest",
)
DELIVERY_HEAD_COLUMNS = (
    "schema_id", "effect_intent_ref", "program_ref", "current_delivery_attempt_ref",
    "head_revision", "delivery_state", "updated_at", "head_digest",
)
DECISION_COLUMNS = (
    "schema_id", "mutation_ref", "decision_ref", "program_ref", "decision_kind",
    "decision_variant", "basis_decision_ref", "basis_program_version_ref",
    "basis_program_version_number", "expected_program_head_revision",
    "resulting_program_version_ref", "resulting_program_version_number",
    "selected_semantic_attempt_ref", "selected_candidate_ref",
    "selected_attempt_fence_ref", "selected_attempt_fence_digest",
    "target_effect_intent_ref", "target_effect_class", "target_effect_fence_ref",
    "target_effect_fence_digest", "expected_target_effect_head_revision",
    "target_delivery_attempt_ref", "originating_command_ref",
    "originating_command_digest", "target_capsule_manifest_ref",
    "target_portable_capsule_digest", "coding_global_stop_ref",
    "coding_global_stop_version", "source_directive_ref", "source_directive_digest",
    "source_evidence_ref", "source_evidence_digest", "preassigned_semantic_attempt_ref",
    "preassigned_candidate_ref", "preassigned_effect_intent_ref",
    "preassigned_effect_fence_ref", "preassigned_delivery_attempt_ref",
    "resulting_accepted_intent_revision_ref", "resulting_work_item_ref",
    "resulting_work_item_revision_ref", "reason_code", "decided_at", "decision_digest",
)
RECEIPT_COLUMNS = (
    "schema_id", "mutation_ref", "mutation_family", "command_schema_id",
    "command_digest", "program_ref", "decision_ref", "result_program_version_ref",
    "result_semantic_attempt_ref", "result_effect_intent_ref",
    "result_effect_fence_ref", "result_delivery_attempt_ref", "result_observation_ref",
    "result_decision_ref", "result_class", "result_projection_digest",
    "mutation_graph_digest", "outcome", "committed_at",
)

EXPECTED_QUERY_LEDGER = (
    ("_MUTATION_RECEIPT_SELECT", "mutation_receipt", RECEIPT_COLUMNS, ("mutation_ref",), 2),
    ("_DECISION_SELECT", "decision", DECISION_COLUMNS, ("decision_ref",), 2),
    ("_PROGRAM_HEAD_SELECT", "program_head", PROGRAM_HEAD_COLUMNS, ("program_ref",), 2),
    ("_CURRENT_PROGRAM_VERSION_SELECT", "current_program_version", PROGRAM_VERSION_COLUMNS, ("program_ref", "program_head.current_program_version_ref", "program_head.current_program_version_number"), 2),
    ("_INITIALIZE_DECISION_SELECT", "initialize_decision", DECISION_COLUMNS, ("program_ref", "decision_ref"), 2),
    ("_RESULTING_PROGRAM_VERSION_SELECT", "resulting_program_version", PROGRAM_VERSION_COLUMNS, ("program_ref", "initialize_decision.resulting_program_version_ref", "initialize_decision.resulting_program_version_number"), 2),
    ("_ACCEPTED_INTENT_REVISION_SELECT", "accepted_intent_revision", ACCEPTED_INTENT_COLUMNS, ("program_ref", "accepted_intent_revision_ref"), 2),
    ("_WORK_ITEM_HEAD_SELECT", "work_item_head", WORK_ITEM_HEAD_COLUMNS, ("program_ref", "work_item_ref"), 2),
    ("_WORK_ITEM_REVISION_SELECT", "work_item_revision", WORK_ITEM_REVISION_COLUMNS, ("program_ref", "work_item_ref", "work_item_revision_ref"), 2),
    ("_PROGRAM_VERSION_ROOT_SELECT", "program_version_root", PROGRAM_VERSION_COLUMNS, ("program_ref", "program_version_ref"), 2),
    ("_MEMBERSHIP_FIRST_PAGE_SELECT", "membership_first_page", MEMBERSHIP_COLUMNS, ("program_ref", "program_version_ref"), 257),
    ("_MEMBERSHIP_CONTINUATION_PAGE_SELECT", "membership_continuation_page", MEMBERSHIP_COLUMNS, ("program_ref", "program_version_ref", "after_membership_ordinal", "after_membership_ordinal", "after_work_item_ref"), 257),
    ("_MEMBERSHIP_WORK_ITEM_REVISION_SELECT", "membership_work_item_revision", WORK_ITEM_REVISION_COLUMNS, ("program_ref", "membership.work_item_ref", "membership.work_item_revision_ref"), 2),
    ("_WORK_SPEC_SAFE_BINDING_SELECT", "work_spec_safe_binding", WORK_SPEC_COLUMNS, ("program_ref", "program_version_ref", "work_item_ref", "work_item_revision_ref"), 2),
    ("_EFFECT_INTENT_ROOT_SELECT", "effect_intent_root", EFFECT_INTENT_COLUMNS, ("program_ref", "effect_intent_ref"), 2),
    ("_SEMANTIC_ATTEMPT_SELECT", "semantic_attempt", SEMANTIC_ATTEMPT_COLUMNS, ("program_ref", "semantic_attempt_ref"), 2),
    ("_AUTHOR_COMMAND_SELECT", "author_command", AUTHOR_COMMAND_COLUMNS, ("program_ref", "effect_intent.command_ref"), 2),
    ("_ATTEMPT_FENCE_SELECT", "attempt_fence", ATTEMPT_FENCE_COLUMNS, ("program_ref", "author_command.attempt_fence_ref"), 2),
    ("_CURRENT_EFFECT_FENCE_SELECT", "current_effect_fence", EFFECT_FENCE_COLUMNS, ("program_ref", "effect_intent_ref"), 2),
    ("_AUTHOR_EFFECT_FENCE_SELECT", "author_effect_fence", EFFECT_FENCE_COLUMNS, ("program_ref", "author_command.effect_fence_ref"), 2),
    ("_AUTHORITY_EVALUATION_SELECT", "authority_evaluation", AUTHORITY_COLUMNS, ("program_ref", "authority_evaluation_ref"), 2),
    ("_EFFECT_HEAD_SELECT", "effect_head", EFFECT_HEAD_COLUMNS, ("program_ref", "effect_intent_ref"), 2),
    ("_DELIVERY_HEAD_SELECT", "delivery_head", DELIVERY_HEAD_COLUMNS, ("program_ref", "effect_intent_ref"), 2),
    ("_CURRENT_DELIVERY_ATTEMPT_SELECT", "current_delivery_attempt", DELIVERY_ATTEMPT_COLUMNS, ("program_ref", "effect_intent_ref", "delivery_head.current_delivery_attempt_ref"), 2),
)

EXPECTED_SQL = {
    "_MUTATION_RECEIPT_SELECT": "SELECT schema_id, mutation_ref, mutation_family, command_schema_id, command_digest, program_ref, decision_ref, result_program_version_ref, result_semantic_attempt_ref, result_effect_intent_ref, result_effect_fence_ref, result_delivery_attempt_ref, result_observation_ref, result_decision_ref, result_class, result_projection_digest, mutation_graph_digest, outcome, committed_at FROM development_mutation_receipts WHERE mutation_ref = ? LIMIT 2",
    "_DECISION_SELECT": "SELECT schema_id, mutation_ref, decision_ref, program_ref, decision_kind, decision_variant, basis_decision_ref, basis_program_version_ref, basis_program_version_number, expected_program_head_revision, resulting_program_version_ref, resulting_program_version_number, selected_semantic_attempt_ref, selected_candidate_ref, selected_attempt_fence_ref, selected_attempt_fence_digest, target_effect_intent_ref, target_effect_class, target_effect_fence_ref, target_effect_fence_digest, expected_target_effect_head_revision, target_delivery_attempt_ref, originating_command_ref, originating_command_digest, target_capsule_manifest_ref, target_portable_capsule_digest, coding_global_stop_ref, coding_global_stop_version, source_directive_ref, source_directive_digest, source_evidence_ref, source_evidence_digest, preassigned_semantic_attempt_ref, preassigned_candidate_ref, preassigned_effect_intent_ref, preassigned_effect_fence_ref, preassigned_delivery_attempt_ref, resulting_accepted_intent_revision_ref, resulting_work_item_ref, resulting_work_item_revision_ref, reason_code, decided_at, decision_digest FROM development_decisions WHERE decision_ref = ? LIMIT 2",
    "_PROGRAM_HEAD_SELECT": "SELECT schema_id, program_ref, current_program_version_ref, current_program_version_number, head_revision, program_state, updated_at, head_digest FROM development_program_heads WHERE program_ref = ? LIMIT 2",
    "_CURRENT_PROGRAM_VERSION_SELECT": "SELECT schema_id, program_version_ref, program_ref, program_version_number, program_version_kind, creating_decision_ref, accepted_intent_revision_ref, created_at, program_version_digest FROM development_program_versions WHERE program_ref = ? AND program_version_ref = ? AND program_version_number = ? LIMIT 2",
    "_INITIALIZE_DECISION_SELECT": "SELECT schema_id, mutation_ref, decision_ref, program_ref, decision_kind, decision_variant, basis_decision_ref, basis_program_version_ref, basis_program_version_number, expected_program_head_revision, resulting_program_version_ref, resulting_program_version_number, selected_semantic_attempt_ref, selected_candidate_ref, selected_attempt_fence_ref, selected_attempt_fence_digest, target_effect_intent_ref, target_effect_class, target_effect_fence_ref, target_effect_fence_digest, expected_target_effect_head_revision, target_delivery_attempt_ref, originating_command_ref, originating_command_digest, target_capsule_manifest_ref, target_portable_capsule_digest, coding_global_stop_ref, coding_global_stop_version, source_directive_ref, source_directive_digest, source_evidence_ref, source_evidence_digest, preassigned_semantic_attempt_ref, preassigned_candidate_ref, preassigned_effect_intent_ref, preassigned_effect_fence_ref, preassigned_delivery_attempt_ref, resulting_accepted_intent_revision_ref, resulting_work_item_ref, resulting_work_item_revision_ref, reason_code, decided_at, decision_digest FROM development_decisions WHERE program_ref = ? AND decision_ref = ? LIMIT 2",
    "_RESULTING_PROGRAM_VERSION_SELECT": "SELECT schema_id, program_version_ref, program_ref, program_version_number, program_version_kind, creating_decision_ref, accepted_intent_revision_ref, created_at, program_version_digest FROM development_program_versions WHERE program_ref = ? AND program_version_ref = ? AND program_version_number = ? LIMIT 2",
    "_ACCEPTED_INTENT_REVISION_SELECT": "SELECT schema_id, accepted_intent_revision_ref, program_ref, accepted_intent_revision_number, prior_accepted_intent_revision_ref, source_intent_ref, source_intent_digest, safe_projection_digest, created_at, accepted_intent_revision_digest FROM development_accepted_intent_revisions WHERE program_ref = ? AND accepted_intent_revision_ref = ? LIMIT 2",
    "_WORK_ITEM_HEAD_SELECT": "SELECT schema_id, work_item_ref, program_ref, current_work_item_revision_ref, current_work_item_revision_number, head_revision, work_state, updated_at, head_digest FROM development_work_item_heads WHERE program_ref = ? AND work_item_ref = ? LIMIT 2",
    "_WORK_ITEM_REVISION_SELECT": "SELECT schema_id, work_item_revision_ref, program_ref, work_item_ref, work_item_revision_number, work_item_revision_kind, prior_work_item_revision_ref, accepted_intent_revision_ref, created_at, work_item_revision_digest FROM development_work_item_revisions WHERE program_ref = ? AND work_item_ref = ? AND work_item_revision_ref = ? LIMIT 2",
    "_PROGRAM_VERSION_ROOT_SELECT": "SELECT schema_id, program_version_ref, program_ref, program_version_number, program_version_kind, creating_decision_ref, accepted_intent_revision_ref, created_at, program_version_digest FROM development_program_versions WHERE program_ref = ? AND program_version_ref = ? LIMIT 2",
    "_MEMBERSHIP_FIRST_PAGE_SELECT": "SELECT schema_id, program_ref, program_version_ref, work_item_ref, work_item_revision_ref, membership_ordinal, created_at, membership_digest FROM development_program_version_work_items WHERE program_ref = ? AND program_version_ref = ? ORDER BY membership_ordinal ASC, work_item_ref ASC LIMIT 257",
    "_MEMBERSHIP_CONTINUATION_PAGE_SELECT": "SELECT schema_id, program_ref, program_version_ref, work_item_ref, work_item_revision_ref, membership_ordinal, created_at, membership_digest FROM development_program_version_work_items WHERE program_ref = ? AND program_version_ref = ? AND (membership_ordinal > ? OR (membership_ordinal = ? AND work_item_ref > ?)) ORDER BY membership_ordinal ASC, work_item_ref ASC LIMIT 257",
    "_MEMBERSHIP_WORK_ITEM_REVISION_SELECT": "SELECT schema_id, work_item_revision_ref, program_ref, work_item_ref, work_item_revision_number, work_item_revision_kind, prior_work_item_revision_ref, accepted_intent_revision_ref, created_at, work_item_revision_digest FROM development_work_item_revisions WHERE program_ref = ? AND work_item_ref = ? AND work_item_revision_ref = ? LIMIT 2",
    "_WORK_SPEC_SAFE_BINDING_SELECT": "SELECT schema_id, work_spec_ref, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, repository_ref, base_git_object_format, base_git_oid, authorized_paths_json, validation_requirement_ref, review_requirement_ref, privacy_classification, work_spec_digest, safe_projection_digest, recorded_at, work_spec_binding_digest FROM development_work_spec_bindings WHERE program_ref = ? AND program_version_ref = ? AND work_item_ref = ? AND work_item_revision_ref = ? LIMIT 2",
    "_EFFECT_INTENT_ROOT_SELECT": "SELECT schema_id, effect_intent_ref, program_ref, program_version_ref, semantic_attempt_ref, effect_class, candidate_ref, command_ref, basis_decision_ref, cancellation_target_effect_intent_ref, expected_target_effect_head_revision, portable_capsule_digest, created_at, effect_intent_digest FROM development_effect_intents WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2",
    "_SEMANTIC_ATTEMPT_SELECT": "SELECT schema_id, semantic_attempt_ref, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, attempt_number, candidate_ref, attempt_phase, selection_decision_ref, created_at, semantic_attempt_digest FROM development_semantic_attempts WHERE program_ref = ? AND semantic_attempt_ref = ? LIMIT 2",
    "_AUTHOR_COMMAND_SELECT": "SELECT schema_id, command_ref, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, semantic_attempt_ref, effect_intent_ref, effect_class, candidate_ref, repository_ref, base_git_object_format, base_git_oid, path_ceiling_json, work_spec_ref, work_spec_digest, standing_grant_ref, standing_grant_digest, attempt_authorization_ref, attempt_authorization_digest, effect_authorization_ref, effect_authorization_digest, attempt_fence_ref, attempt_fence_digest, effect_fence_ref, effect_fence_digest, global_stop_ref, global_stop_version, validation_requirement_ref, validation_requirement_digest, review_requirement_ref, review_requirement_digest, capsule_schema_id, capsule_profile_ref, effect_max_active_invocations, effect_max_candidate_bytes, effect_max_changed_files, effect_max_cost_microusd, effect_max_cpu_seconds, effect_max_deliveries, effect_max_deployments, effect_max_local_commits, effect_max_memory_bytes, effect_max_merges, effect_max_model_input_tokens, effect_max_model_output_tokens, effect_max_pull_requests, effect_max_pushes, effect_max_wall_seconds, privacy_classification, redaction_profile_ref, command_digest, recorded_at FROM development_author_commands WHERE program_ref = ? AND command_ref = ? LIMIT 2",
    "_ATTEMPT_FENCE_SELECT": "SELECT schema_id, attempt_fence_ref, parent_standing_grant_ref, parent_standing_grant_digest, attempt_authorization_ref, attempt_authorization_digest, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, semantic_attempt_ref, repository_ref, base_git_object_format, base_git_oid, path_ceiling_json, allowed_effect_class_mask, aggregate_max_active_invocations, aggregate_max_candidate_bytes, aggregate_max_changed_files, aggregate_max_cost_microusd, aggregate_max_cpu_seconds, aggregate_max_deliveries, aggregate_max_deployments, aggregate_max_local_commits, aggregate_max_memory_bytes, aggregate_max_merges, aggregate_max_model_input_tokens, aggregate_max_model_output_tokens, aggregate_max_pull_requests, aggregate_max_pushes, aggregate_max_wall_seconds, expires_at, global_stop_ref, global_stop_version, attempt_fence_digest, recorded_at FROM development_attempt_fences WHERE program_ref = ? AND attempt_fence_ref = ? LIMIT 2",
    "_CURRENT_EFFECT_FENCE_SELECT": "SELECT schema_id, effect_fence_ref, parent_standing_grant_ref, parent_standing_grant_digest, effect_authorization_ref, effect_authorization_digest, attempt_fence_ref, attempt_fence_digest, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, semantic_attempt_ref, effect_intent_ref, effect_class, command_ref, command_digest, candidate_ref, repository_ref, base_git_object_format, base_git_oid, path_ceiling_json, effect_max_active_invocations, effect_max_candidate_bytes, effect_max_changed_files, effect_max_cost_microusd, effect_max_cpu_seconds, effect_max_deliveries, effect_max_deployments, effect_max_local_commits, effect_max_memory_bytes, effect_max_merges, effect_max_model_input_tokens, effect_max_model_output_tokens, effect_max_pull_requests, effect_max_pushes, effect_max_wall_seconds, expires_at, global_stop_ref, global_stop_version, portable_capsule_digest, cancellation_target_effect_intent_ref, cancellation_target_effect_fence_ref, cancellation_target_effect_fence_digest, effect_fence_digest, recorded_at FROM development_effect_fences WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2",
    "_AUTHOR_EFFECT_FENCE_SELECT": "SELECT schema_id, effect_fence_ref, parent_standing_grant_ref, parent_standing_grant_digest, effect_authorization_ref, effect_authorization_digest, attempt_fence_ref, attempt_fence_digest, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, semantic_attempt_ref, effect_intent_ref, effect_class, command_ref, command_digest, candidate_ref, repository_ref, base_git_object_format, base_git_oid, path_ceiling_json, effect_max_active_invocations, effect_max_candidate_bytes, effect_max_changed_files, effect_max_cost_microusd, effect_max_cpu_seconds, effect_max_deliveries, effect_max_deployments, effect_max_local_commits, effect_max_memory_bytes, effect_max_merges, effect_max_model_input_tokens, effect_max_model_output_tokens, effect_max_pull_requests, effect_max_pushes, effect_max_wall_seconds, expires_at, global_stop_ref, global_stop_version, portable_capsule_digest, cancellation_target_effect_intent_ref, cancellation_target_effect_fence_ref, cancellation_target_effect_fence_digest, effect_fence_digest, recorded_at FROM development_effect_fences WHERE program_ref = ? AND effect_fence_ref = ? LIMIT 2",
    "_AUTHORITY_EVALUATION_SELECT": "SELECT schema_id, authority_evaluation_ref, program_ref, evaluation_scope, evaluation_subject_ref, semantic_attempt_ref, effect_intent_ref, authority_ref, authority_digest, authority_state, reason_code, expires_at, evaluated_at, authority_evaluation_digest FROM development_authority_evaluations WHERE program_ref = ? AND authority_evaluation_ref = ? LIMIT 2",
    "_EFFECT_HEAD_SELECT": "SELECT schema_id, effect_intent_ref, program_ref, current_effect_fence_ref, head_revision, effect_state, cancellation_effect_intent_ref, updated_at, head_digest FROM development_effect_heads WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2",
    "_DELIVERY_HEAD_SELECT": "SELECT schema_id, effect_intent_ref, program_ref, current_delivery_attempt_ref, head_revision, delivery_state, updated_at, head_digest FROM development_delivery_heads WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2",
    "_CURRENT_DELIVERY_ATTEMPT_SELECT": "SELECT schema_id, delivery_attempt_ref, program_ref, program_version_ref, command_ref, command_digest, semantic_attempt_ref, effect_intent_ref, attempt_fence_ref, attempt_fence_digest, effect_fence_ref, effect_fence_digest, adapter_kind, adapter_safe_correlation_ref, delivery_envelope_digest, delivery_kind, delivery_number, predecessor_delivery_attempt_ref, basis_decision_ref, recorded_at, delivery_attempt_digest FROM development_delivery_attempts WHERE program_ref = ? AND effect_intent_ref = ? AND delivery_attempt_ref = ? LIMIT 2",
}


class _IntSubclass(int):
    pass


class _BoundedLimitStandIn:
    def __init__(self) -> None:
        self.borrow_count = 0

    def _borrow_connection_for_select(self) -> object:
        self.borrow_count += 1
        return object()


def _properties(value_type: type[object]) -> tuple[str, ...]:
    return tuple(
        name
        for name, value in value_type.__dict__.items()
        if type(value) is property
    )


def _closed_literal_ast(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return type(node.value) in (str, int)
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(_closed_literal_ast(element) for element in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            key is not None
            and _closed_literal_ast(key)
            and _closed_literal_ast(value)
            for key, value in zip(node.keys, node.values, strict=True)
        )
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and type(node.operand.value) is int
    ):
        return True
    return False


def _module_assignment(tree: ast.Module, name: str) -> ast.AST:
    matches = tuple(
        node.value
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(
            isinstance(target, ast.Name) and target.id == name
            for target in (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
        )
    )
    if len(matches) != 1:
        raise AssertionError("C2B2_READER_LITERAL_ORACLE_CONTRACT")
    return matches[0]


def _source_contract(source: str, *, reader_module: bool) -> None:
    tree = ast.parse(source)
    imports = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )
    forbidden_imports = (
        "pathlib", "os", "sqlite3", "subprocess", "threading", "multiprocessing",
        "socket", "time", "datetime", "random", "uuid", "importlib",
    )
    for node in imports:
        module = node.module if isinstance(node, ast.ImportFrom) else node.names[0].name
        if module is not None and module.split(".", 1)[0] in forbidden_imports:
            raise AssertionError("C2B2_READER_SOURCE_CONTRACT")
    forbidden_calls = {"eval", "exec", "compile", "getattr", "setattr", "open"}
    if any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in forbidden_calls
        for node in ast.walk(tree)
    ):
        raise AssertionError("C2B2_READER_SOURCE_CONTRACT")
    if any(isinstance(node, ast.Match) for node in ast.walk(tree)):
        raise AssertionError("C2B2_READER_SOURCE_CONTRACT")
    if "_borrow_connection_for_select" in source:
        raise AssertionError("C2B2_READER_SOURCE_CONTRACT")
    if any(
        isinstance(node, (ast.FunctionDef, ast.ClassDef))
        and ("dispatch" in node.name.lower() or "registry" in node.name.lower())
        for node in tree.body
    ):
        raise AssertionError("C2B2_READER_SOURCE_CONTRACT")
    if any(
        isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(
            isinstance(target, ast.Name)
            and ("dispatch" in target.id.lower() or "registry" in target.id.lower())
            for target in (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
        )
        for node in tree.body
    ):
        raise AssertionError("C2B2_READER_SOURCE_CONTRACT")
    reader_functions = tuple(
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("_read_development_")
    )
    if reader_module and reader_functions != tuple(EXPECTED_READER_SIGNATURES):
        raise AssertionError("C2B2_READER_SOURCE_CONTRACT")
    if reader_module:
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name.startswith("_read_development_")
        }
        all_functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }
        for name, (parameters, result) in EXPECTED_READER_SIGNATURES.items():
            node = functions.get(name)
            if (
                node is None
                or tuple(argument.arg for argument in node.args.args) != parameters
                or node.returns is None
                or ast.unparse(node.returns) != result
            ):
                raise AssertionError("C2B2_READER_SOURCE_CONTRACT")
            suffix = name.removeprefix("_read_development_")
            load_name = f"_load_development_{suffix}"
            perform_name = f"_perform_development_{suffix}"
            load_node = all_functions.get(load_name)
            perform_node = all_functions.get(perform_name)
            if load_node is None or perform_node is None:
                raise AssertionError("C2B2_READER_SOURCE_CONTRACT")
            public_calls = tuple(
                child.func.id
                for child in ast.walk(node)
                if isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
            )
            deleted_names = {
                target.id
                for child in ast.walk(node)
                if isinstance(child, ast.Delete)
                for target in child.targets
                if isinstance(target, ast.Name)
            }
            if (
                public_calls.count(perform_name) != 1
                or load_name in public_calls
                or deleted_names != set(parameters)
            ):
                raise AssertionError("C2B2_READER_SOURCE_CONTRACT")
            if any(isinstance(child, ast.Raise) for child in ast.walk(perform_node)):
                raise AssertionError("C2B2_READER_SOURCE_CONTRACT")
            try_nodes = tuple(
                child for child in perform_node.body if isinstance(child, ast.Try)
            )
            if len(try_nodes) != 1 or len(try_nodes[0].handlers) != 2:
                raise AssertionError("C2B2_READER_SOURCE_CONTRACT")
    if not reader_module and reader_functions:
        raise AssertionError("C2B2_READER_SOURCE_CONTRACT")
    if reader_module and source.count("from .sqlite_transition_transaction import _SQLiteMutationReadCapability") != 1:
        raise AssertionError("C2B2_READER_SOURCE_CONTRACT")
    if "__all__: tuple[str, ...] = ()" not in source:
        raise AssertionError("C2B2_READER_SOURCE_CONTRACT")


def _query_candidate_contract(
    ledger: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...], int], ...],
    sql: dict[str, str],
) -> None:
    if ledger != EXPECTED_QUERY_LEDGER or sql != EXPECTED_SQL:
        raise AssertionError("C2B2_READER_QUERY_CONTRACT")


def _reader_inventory_candidate_contract(names: tuple[str, ...]) -> None:
    if names != tuple(EXPECTED_READER_SIGNATURES):
        raise AssertionError("C2B2_READER_INVENTORY_CONTRACT")


def _scope_candidate_contract(
    package_source: str,
    production_importers: tuple[str, ...],
    c2b3_paths: tuple[str, ...],
) -> None:
    if (
        "_sqlite_development_readers" in package_source
        or production_importers != EXPECTED_PRODUCTION_READER_IMPORTERS
        or c2b3_paths
    ):
        raise AssertionError("C2B2_READER_SCOPE_CONTRACT")


def test_exact_two_module_inventory_import_dag_and_private_exports() -> None:
    assert CONTRACTS_PATH.is_file() and not CONTRACTS_PATH.is_symlink()
    assert READERS_PATH.is_file() and not READERS_PATH.is_symlink()
    assert contracts.__all__ == readers.__all__ == ()
    contracts_source = CONTRACTS_PATH.read_text(encoding="utf-8")
    readers_source = READERS_PATH.read_text(encoding="utf-8")
    _source_contract(contracts_source, reader_module=False)
    _source_contract(readers_source, reader_module=True)
    assert "_sqlite_development_readers" not in contracts_source
    assert "sqlite_transition_transaction" not in contracts_source
    assert "sqlite_transition_transaction" not in "\n".join(
        line for line in readers_source.splitlines()[:120] if not line.startswith("    ")
    )
    assert not hasattr(ge_nwp_coordinator, "_read_development_effect_head")
    assert "_read_development_effect_head" not in ge_nwp_coordinator.__all__


def test_seven_aggregate_types_have_exact_manual_immutable_posture() -> None:
    assert tuple(EXPECTED_AGGREGATE_FIELDS) == tuple(
        name
        for name in contracts.__dict__
        if name in EXPECTED_AGGREGATE_FIELDS
    )
    for type_name, fields in EXPECTED_AGGREGATE_FIELDS.items():
        value_type = getattr(contracts, type_name)
        assert value_type.__slots__ == ("_values",)
        assert _properties(value_type) == fields
        assert value_type.__hash__ is None
        assert "__dict__" not in value_type.__dict__
        assert "__weakref__" not in value_type.__dict__
        with pytest.raises(TypeError, match="^construction disabled$"):
            value_type()
        with pytest.raises(TypeError, match="^subclassing disabled$"):
            type("Forbidden", (value_type,), {})


def test_exact_production_query_and_aggregate_inventories_reject_additions() -> None:
    observed_queries = tuple(
        name
        for name, value in contracts.__dict__.items()
        if type(value) is contracts._DevelopmentSelectSpecification
    )
    assert observed_queries == EXPECTED_QUERY_SPECIFICATION_NAMES
    observed_aggregates = tuple(
        name
        for name, value in contracts.__dict__.items()
        if type(value) is type
        and value.__module__ == contracts.__name__
        and value.__base__.__name__ == "_ImmutableValue"
        and not name.startswith("_")
    )
    assert observed_aggregates == EXPECTED_AGGREGATE_TYPE_NAMES


@pytest.mark.parametrize("valid_limit", (2, 257))
def test_query_specification_factory_accepts_only_exact_valid_limits(
    valid_limit: int,
) -> None:
    specification = contracts._DevelopmentSelectSpecification._from_literal(
        "test_owned_literal_query",
        "SELECT schema_id FROM test_owned_table LIMIT 2",
        ("schema_id",),
        ("test_ref",),
        valid_limit,
    )
    assert specification.fetch_limit == valid_limit


@pytest.mark.parametrize(
    "invalid_limit",
    (True, False, _IntSubclass(2), _IntSubclass(257), 1, 3, 256, 258, 0, -1),
)
def test_query_specification_factory_rejects_invalid_limit_matrix(
    invalid_limit: object,
) -> None:
    with pytest.raises(TypeError, match="^invalid literal query specification$"):
        contracts._DevelopmentSelectSpecification._from_literal(
            "test_owned_literal_query",
            "SELECT schema_id FROM test_owned_table LIMIT 2",
            ("schema_id",),
            ("test_ref",),
            invalid_limit,
        )


@pytest.mark.parametrize(
    "invalid_limit",
    (True, False, _IntSubclass(2), _IntSubclass(257), 1, 3, 256, 259, 0, -1),
)
def test_shared_bounded_helper_rejects_invalid_limit_before_borrow_or_sql(
    invalid_limit: object,
) -> None:
    stand_in = _BoundedLimitStandIn()
    if type(invalid_limit) is int and invalid_limit == 3:
        with pytest.raises(_MutationReadCapabilityError) as capability_error:
            _execute_select_fetch_bounded(
                capability=stand_in,
                sql="SELECT schema_id FROM test_owned_table WHERE test_ref = ? LIMIT 3",
                parameters=("test-ref",),
                limit=invalid_limit,
            )
        assert (
            capability_error.value.reason
            is _MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE
        )
        assert stand_in.borrow_count == 1
        return
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        _execute_select_fetch_bounded(
            capability=stand_in,
            sql="SELECT schema_id FROM test_owned_table WHERE test_ref = ? LIMIT 2",
            parameters=("test-ref",),
            limit=invalid_limit,
        )
    assert exc_info.value.error_class == "database_integrity_failure"
    assert stand_in.borrow_count == 0


def test_expected_sql_and_inventory_oracles_are_closed_test_owned_literals() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for assignment_name in (
        "EXPECTED_QUERY_SPECIFICATION_NAMES",
        "EXPECTED_AGGREGATE_TYPE_NAMES",
        "EXPECTED_SQL",
    ):
        assert _closed_literal_ast(_module_assignment(tree, assignment_name))


def test_select_and_reader_failure_stages_exit_before_fresh_safe_raise() -> None:
    support_tree = ast.parse(SELECT_SUPPORT_PATH.read_text(encoding="utf-8"))
    support_functions = {
        node.name: node
        for node in support_tree.body
        if isinstance(node, ast.FunctionDef)
    }
    raw_select = support_functions["_perform_select_fetch_bounded"]
    assert not any(isinstance(node, ast.Raise) for node in ast.walk(raw_select))
    for function_name, deleted in (
        ("_execute_select_fetch_two", {"capability", "sql", "parameters"}),
        (
            "_execute_select_fetch_bounded",
            {"capability", "sql", "parameters", "limit"},
        ),
    ):
        node = support_functions[function_name]
        calls = tuple(
            child.func.id
            for child in ast.walk(node)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        )
        deleted_names = {
            target.id
            for child in ast.walk(node)
            if isinstance(child, ast.Delete)
            for target in child.targets
            if isinstance(target, ast.Name)
        }
        assert calls.count("_perform_select_fetch_bounded") == 1
        assert deleted_names == deleted


def test_aggregate_positive_mechanics_are_content_free_and_nonserializable() -> None:
    sentinel_type = contracts.DevelopmentWorkItemHeadAndRevisionRead
    value = object.__new__(sentinel_type)
    object.__setattr__(value, "_values", (object(), object(), True))
    assert repr(value) == str(value) == "<DevelopmentWorkItemHeadAndRevisionRead>"
    assert copy.copy(value) is value
    assert copy.deepcopy(value) is value
    assert value == value
    with pytest.raises(TypeError, match="^unhashable type"):
        hash(value)
    with pytest.raises(TypeError, match="^pickling disabled$"):
        pickle.dumps(value)
    with pytest.raises(AttributeError, match="^immutable$"):
        value.is_current = False
    with pytest.raises(AttributeError, match="^immutable$"):
        del value.is_current


def test_twelve_private_reader_names_parameters_and_result_annotations_are_exact() -> None:
    for function_name, (parameter_names, return_name) in EXPECTED_READER_SIGNATURES.items():
        function = getattr(readers, function_name)
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == parameter_names
        assert signature.return_annotation == return_name
    assert len(EXPECTED_READER_SIGNATURES) == 12


def test_twenty_four_literal_query_specs_columns_parameters_and_bounds_are_exact() -> None:
    _query_candidate_contract(EXPECTED_QUERY_LEDGER, EXPECTED_SQL)
    assert len(EXPECTED_QUERY_LEDGER) == 24
    assert len({name for name, _, _, _, _ in EXPECTED_QUERY_LEDGER}) == 24
    for name, query_id, columns, parameters, limit in EXPECTED_QUERY_LEDGER:
        specification = getattr(contracts, name)
        assert specification.query_id == query_id
        assert specification.sql == EXPECTED_SQL[name]
        assert specification.row_columns == columns
        assert specification.parameter_order == parameters
        assert specification.fetch_limit == limit
        assert specification.sql.startswith("SELECT ")
        assert specification.sql.endswith(f" LIMIT {limit}")
        assert repr(specification) == "<_DevelopmentSelectSpecification>"
    assert [item[-1] for item in EXPECTED_QUERY_LEDGER].count(257) == 2
    assert [item[-1] for item in EXPECTED_QUERY_LEDGER].count(2) == 22


def test_query_order_role_nine_authority_boundary_and_role_ten_exactness() -> None:
    source = READERS_PATH.read_text(encoding="utf-8")
    role_nine = inspect.getsource(
        readers._load_development_attempt_fence_command_effect_aggregate
    )
    ordered = (
        "_EFFECT_INTENT_ROOT_SELECT",
        "_SEMANTIC_ATTEMPT_SELECT",
        "_AUTHOR_COMMAND_SELECT",
        "_ATTEMPT_FENCE_SELECT",
        "_CURRENT_EFFECT_FENCE_SELECT",
        "_AUTHOR_EFFECT_FENCE_SELECT",
    )
    positions = tuple(role_nine.index(name) for name in ordered)
    assert positions == tuple(sorted(positions))
    assert "_AUTHORITY_EVALUATION_SELECT" not in role_nine
    role_ten = inspect.getsource(
        readers._load_development_authority_evaluation_by_exact_ref
    )
    assert "parameters=(program_ref, authority_evaluation_ref)" in role_ten
    for forbidden in ("MAX(", "rowid", "ORDER BY", "evaluated_at"):
        assert forbidden not in role_ten
    assert "authorized" not in source


@pytest.mark.parametrize("inventory_case", ("missing", "thirteenth", "reordered"))
def test_reader_inventory_counterfactuals_fail_one_fixed_diagnostic(
    inventory_case: str,
) -> None:
    names = list(EXPECTED_READER_SIGNATURES)
    if inventory_case == "missing":
        names.pop()
    elif inventory_case == "thirteenth":
        names.append("_read_development_thirteenth")
    else:
        names[0], names[1] = names[1], names[0]
    with pytest.raises(
        AssertionError,
        match="^C2B2_READER_INVENTORY_CONTRACT$",
    ):
        _reader_inventory_candidate_contract(tuple(names))


@pytest.mark.parametrize(
    "query_case",
    (
        "missing_sql",
        "extra_sql",
        "field_reorder",
        "wrong_where_key",
        "wrong_parameter_order",
        "limit_1",
        "limit_3",
        "membership_limit_256",
        "membership_limit_258",
        "missing_order_by",
    ),
)
def test_query_counterfactuals_fail_one_fixed_diagnostic(query_case: str) -> None:
    ledger = list(EXPECTED_QUERY_LEDGER)
    sql = dict(EXPECTED_SQL)
    if query_case == "missing_sql":
        del sql["_EFFECT_HEAD_SELECT"]
    elif query_case == "extra_sql":
        sql["_EXTRA_SELECT"] = "SELECT schema_id FROM extra_table LIMIT 2"
    elif query_case == "field_reorder":
        sql["_PROGRAM_HEAD_SELECT"] = sql["_PROGRAM_HEAD_SELECT"].replace(
            "SELECT schema_id, program_ref",
            "SELECT program_ref, schema_id",
            1,
        )
    elif query_case == "wrong_where_key":
        sql["_MUTATION_RECEIPT_SELECT"] = sql["_MUTATION_RECEIPT_SELECT"].replace(
            "WHERE mutation_ref = ?",
            "WHERE program_ref = ?",
            1,
        )
    elif query_case == "wrong_parameter_order":
        record = ledger[13]
        ledger[13] = (record[0], record[1], record[2], tuple(reversed(record[3])), record[4])
    elif query_case in ("limit_1", "limit_3"):
        replacement = "LIMIT 1" if query_case == "limit_1" else "LIMIT 3"
        sql["_DECISION_SELECT"] = sql["_DECISION_SELECT"].replace("LIMIT 2", replacement)
    elif query_case in ("membership_limit_256", "membership_limit_258"):
        replacement = "LIMIT 256" if query_case == "membership_limit_256" else "LIMIT 258"
        sql["_MEMBERSHIP_FIRST_PAGE_SELECT"] = sql["_MEMBERSHIP_FIRST_PAGE_SELECT"].replace(
            "LIMIT 257",
            replacement,
        )
    else:
        sql["_MEMBERSHIP_FIRST_PAGE_SELECT"] = sql["_MEMBERSHIP_FIRST_PAGE_SELECT"].replace(
            " ORDER BY membership_ordinal ASC, work_item_ref ASC",
            "",
        )
    with pytest.raises(AssertionError, match="^C2B2_READER_QUERY_CONTRACT$"):
        _query_candidate_contract(tuple(ledger), sql)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda source: source.replace(
            "def _read_development_effect_head(",
            "def removed_development_effect_head(",
            1,
        ),
        lambda source: source
        + "\ndef _read_development_thirteenth(capability: object) -> None:\n    return None\n",
        lambda source: source.replace(
            "def _read_development_mutation_receipt_by_mutation_ref(\n"
            "    capability: object,\n    mutation_ref: object,",
            "def _read_development_mutation_receipt_by_mutation_ref(\n"
            "    mutation_ref: object,\n    capability: object,",
            1,
        ),
        lambda source: source.replace(
            "def _read_development_effect_head(\n"
            "    capability: object,\n    program_ref: object,\n"
            "    effect_intent_ref: object,\n) -> DevelopmentEffectHeadRowValue | None:",
            "def _read_development_effect_head(\n"
            "    capability: object,\n    program_ref: object,\n"
            "    effect_intent_ref: object,\n) -> object:",
            1,
        ),
        lambda source: source + "\n_READER_REGISTRY = {}\n",
        lambda source: source + "\ndef _dispatch(role):\n    return getattr(readers, role)\n",
        lambda source: source.replace(
            "capability = _require_nominal_capability(capability)",
            "capability._borrow_connection_for_select()\n    capability = _require_nominal_capability(capability)",
            1,
        ),
    ),
)
def test_reader_source_counterfactuals_fail_one_fixed_diagnostic(mutation: object) -> None:
    source = READERS_PATH.read_text(encoding="utf-8")
    candidate = mutation(source)
    with pytest.raises(AssertionError, match="^C2B2_READER_SOURCE_CONTRACT$"):
        _source_contract(candidate, reader_module=True)


def test_no_production_caller_public_store_writer_or_c2b3_surface() -> None:
    production = tuple((ROOT / "src/ge_nwp_coordinator").glob("*.py"))
    importers = {
        path.name
        for path in production
        if "_sqlite_development_readers" in path.read_text(encoding="utf-8")
    }
    assert importers == set(EXPECTED_PRODUCTION_READER_IMPORTERS)
    for path in production:
        if path.name in {
            "_sqlite_development_author_effect_establishment.py",
            "_sqlite_development_pre_execution_plan_disposition.py",
            "_sqlite_development_readers.py",
            "_sqlite_rw0_c1.py",
        }:
            continue
        source = path.read_text(encoding="utf-8")
        assert "_read_development_program_head_and_current_version" not in source
    assert not (ROOT / "src/ge_nwp_coordinator/sqlite_development_state.py").exists()
    assert not (ROOT / "src/ge_nwp_coordinator/c2b3_development_mutation.py").exists()
    state_source = (ROOT / "src/ge_nwp_coordinator/state_store.py").read_text(encoding="utf-8")
    writer_source = (ROOT / "src/ge_nwp_coordinator/sqlite_writer_session.py").read_text(encoding="utf-8")
    for source in (state_source, writer_source):
        assert "read_development" not in source
        assert "DevelopmentProgramHeadAndCurrentVersionRead" not in source


@pytest.mark.parametrize("scope_case", ("package_export", "production_caller", "c2b3"))
def test_scope_counterfactuals_fail_one_fixed_diagnostic(scope_case: str) -> None:
    package_source = (ROOT / "src/ge_nwp_coordinator/__init__.py").read_text(encoding="utf-8")
    importers = EXPECTED_PRODUCTION_READER_IMPORTERS
    c2b3_paths: tuple[str, ...] = ()
    if scope_case == "package_export":
        package_source += "\nfrom . import _sqlite_development_readers\n"
    elif scope_case == "production_caller":
        importers = EXPECTED_PRODUCTION_READER_IMPORTERS + ("sqlite_writer_session.py",)
    else:
        c2b3_paths = ("src/ge_nwp_coordinator/c2b3_development_mutation.py",)
    with pytest.raises(AssertionError, match="^C2B2_READER_SCOPE_CONTRACT$"):
        _scope_candidate_contract(package_source, importers, c2b3_paths)


def _assert_current_migration_0003_documentation(source: object) -> None:
    if type(source) is not str:
        raise AssertionError("C2B2_CURRENT_MIGRATION_STATUS_CONTRACT")
    compacted = " ".join(source.split())
    required = (
        "Slice 3 itself added no schema or migration",
        "Migration 0004 now exists in the current repository and is the current "
        "packaged migration tip.",
        "The C2B2 private-reader Slice 3 itself did not implement or own migrations "
        "0003 or 0004",
        "neither migration retroactively widens this contract or its exact "
        "twenty-four-query inventory.",
        "Sections 41 and 42 own the cognitive proposal-selection runtime; RW0-C1 "
        "owns its separate durable-evidence runtime.",
        "Generated reports and reader projections remain non-authoritative; neither "
        "becomes durable program state or effect authority.",
    )
    forbidden = (
        "migration 0003 is still absent",
        "migration 0003 remains absent",
        "migration 0004 is still absent",
        "migration 0004 remains absent",
        "reader method, every later C2B mutation family, migration 0003,",
    )
    if any(phrase not in compacted for phrase in required) or any(
        phrase in compacted.lower() for phrase in forbidden
    ):
        raise AssertionError("C2B2_CURRENT_MIGRATION_STATUS_CONTRACT")


def test_current_migration_0003_status_preserves_historical_reader_ownership() -> None:
    path = ROOT / ".docs/c2b2-private-readers.md"
    source = path.read_text(encoding="utf-8")
    _assert_current_migration_0003_documentation(source)

    counterfactual = source.replace(
        "Migration 0004 now exists in the current repository and is the current "
        "packaged\nmigration tip.",
        "Migration 0004 is still absent from the current repository.",
        1,
    )
    assert counterfactual != source
    with pytest.raises(
        AssertionError,
        match="^C2B2_CURRENT_MIGRATION_STATUS_CONTRACT$",
    ):
        _assert_current_migration_0003_documentation(counterfactual)


def _assert_current_private_reader_composition_documentation(
    source: object,
    production_usage: dict[str, set[str]],
) -> None:
    diagnostic = "C2B2_CURRENT_READER_COMPOSITION_CONTRACT"
    if type(source) is not str:
        raise AssertionError(diagnostic)
    status_heading = "## Status And Authority"
    source_heading = "## Exact Private Source"
    integration_heading = "## Current Integration And Remaining Nonimplementation"
    composition_begin = "<!-- C2B2_CURRENT_PRODUCTION_READER_COMPOSITION_BEGIN -->"
    composition_end = "<!-- C2B2_CURRENT_PRODUCTION_READER_COMPOSITION_END -->"
    if any(source.count(marker) != 1 for marker in (composition_begin, composition_end)):
        raise AssertionError(diagnostic)
    try:
        status = source.split(status_heading, 1)[1].split(source_heading, 1)[0]
        integration = source.split(integration_heading, 1)[1]
        payload = integration.split(composition_begin, 1)[1].split(composition_end, 1)[0].strip()
    except (IndexError, ValueError):
        raise AssertionError(diagnostic) from None
    if not payload.startswith("```json\n") or not payload.endswith("\n```"):
        raise AssertionError(diagnostic)
    try:
        documented_usage = json.loads(payload.removeprefix("```json\n").removesuffix("\n```"))
    except (TypeError, ValueError):
        raise AssertionError(diagnostic) from None
    expected_usage = {
        module_name: sorted(calls)
        for module_name, calls in production_usage.items()
    }
    if (
        type(documented_usage) is not dict
        or any(type(key) is not str for key in documented_usage)
        or any(
            type(calls) is not list or any(type(call) is not str for call in calls)
            for calls in documented_usage.values()
        )
        or documented_usage != expected_usage
    ):
        raise AssertionError(diagnostic)

    compact_status = " ".join(status.split())
    compact_integration = " ".join(integration.split())
    required_status = (
        "bounded reader layer remains exactly twelve private roles and twenty-four "
        "bounded query contracts",
            "Present production composition is source-derived and has exactly four "
            "private importer modules",
        "_sqlite_development_author_effect_establishment.py",
        "_sqlite_development_program_initialization.py",
            "_sqlite_development_pre_execution_plan_disposition.py",
            "_sqlite_rw0_c1.py",
        "All twelve roles now have the bounded private C2B3D author-effect "
        "establishment, replay, and recovery caller",
        "the mutation-receipt reader also retains its bounded private VS1B",
            "the later Section 41 runtime and RW0-C1 durable-evidence runtime "
            "compose with the exact seven-role subset",
    )
    required_integration = (
            "Present production composition is source-derived and has exactly four "
            "private importer modules",
        "All twelve roles have the bounded private C2B3D author-effect caller",
        "mutation-receipt role also retains the private VS1B",
            "later Section 41 selection runtime and RW0-C1 durable-evidence runtime "
            "compose with the bounded seven-role subset",
            "C2B3D, VS1B, Section 41, and RW0-C1 are later consumers",
        "Their composition does not retroactively make C2B2 the owner of those runtimes",
        "C2B2 did not implement or acquire ownership of migrations 0003/0004, "
        "Section 41, or RW0-C1",
        "does not widen the twenty-four-query reader contract",
        "creates no public package or protocol surface",
        "grants no durable program truth, executable permission, effect authority, or "
        "other durable authority",
        "does not turn reports or reader projections into authoritative state",
        "reader reports and projections remain neither durable program truth nor effect "
        "authority",
    )
    forbidden = (
        "the only production importers are the bounded private vs1b and c2b3d family runtimes",
        "current integration consists only of c2b3d plus vs1b",
        "section 41 owns a later runtime but does not directly compose with these readers",
    )
    if (
        any(phrase not in compact_status for phrase in required_status)
        or any(phrase not in compact_integration for phrase in required_integration)
        or any(phrase in " ".join(source.lower().split()) for phrase in forbidden)
    ):
        raise AssertionError(diagnostic)


def test_current_living_documents_match_source_derived_private_reader_composition() -> None:
    reader_tree = ast.parse(READERS_PATH.read_text(encoding="utf-8"))
    reader_names = {
        node.name
        for node in reader_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("_read_development_")
    }
    contract_tree = ast.parse(CONTRACTS_PATH.read_text(encoding="utf-8"))
    query_names: set[str] = set()
    for node in contract_tree.body:
        targets: tuple[ast.expr, ...]
        if isinstance(node, ast.Assign):
            targets = tuple(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets = (node.target,)
        else:
            continue
        query_names.update(
            target.id
            for target in targets
            if isinstance(target, ast.Name) and target.id.endswith("_SELECT")
        )

    production_usage: dict[str, set[str]] = {}
    for path in sorted((ROOT / "src/ge_nwp_coordinator").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        aliases: dict[str, str] = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module != "_sqlite_development_readers":
                continue
            for alias in node.names:
                if alias.name in reader_names:
                    aliases[alias.asname or alias.name] = alias.name
        if not aliases:
            continue
        calls = {
            aliases[node.func.id]
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in aliases
        }
        assert calls == set(aliases.values())
        production_usage[path.name] = calls

    assert len(reader_names) == 12
    assert len(query_names) == 24
    assert tuple(sorted(production_usage)) == EXPECTED_PRODUCTION_READER_IMPORTERS
    expected_production_usage = {
        "_sqlite_development_author_effect_establishment.py": reader_names,
        "_sqlite_development_pre_execution_plan_disposition.py": set(
            EXPECTED_SECTION41_READER_CALLS
        ),
            "_sqlite_development_program_initialization.py": {
                "_read_development_mutation_receipt_by_mutation_ref"
            },
            "_sqlite_rw0_c1.py": {
                "_read_development_attempt_fence_command_effect_aggregate",
                "_read_development_authority_evaluation_by_exact_ref",
                "_read_development_delivery_head",
                "_read_development_effect_head",
                "_read_development_program_head_and_current_version",
                "_read_development_work_item_head_and_revision_by_exact_ref",
                "_read_development_work_spec_safe_binding",
            },
        }
    assert len(EXPECTED_SECTION41_READER_CALLS) == 7
    assert production_usage == expected_production_usage

    reader_status_path = ROOT / ".docs/c2b2-private-readers.md"
    reader_status_source = reader_status_path.read_text(encoding="utf-8")
    _assert_current_private_reader_composition_documentation(
        reader_status_source,
        production_usage,
    )
    stale_two_importer_source = reader_status_source.replace(
        "Present production composition is source-derived and has exactly four private\n"
        "importer modules with this exact role mapping:",
        "The only production importers are the bounded private VS1B and C2B3D family "
        "runtimes.",
        1,
    )
    assert stale_two_importer_source != reader_status_source
    with pytest.raises(
        AssertionError,
        match="^C2B2_CURRENT_READER_COMPOSITION_CONTRACT$",
    ):
        _assert_current_private_reader_composition_documentation(
            stale_two_importer_source,
            production_usage,
        )

    document_paths = (
        ROOT / ".docs/autonomous-software-development-operating-model.md",
        ROOT / ".docs/architecture.md",
        reader_status_path,
        ROOT / ".docs/durable-state-model.md",
    )
    for path in document_paths:
        current = " ".join(path.read_text(encoding="utf-8").split())
        for phrase in (
            "exactly twelve private roles and twenty-four bounded query contracts",
            "All twelve roles have the bounded private C2B3D author-effect caller",
            "mutation-receipt role also retains the private VS1B",
            "bounded seven-role subset",
            "C2B2 did not implement or acquire ownership of migrations 0003/0004, "
            "Section 41, or RW0-C1",
            "reader reports and projections remain neither durable program truth nor effect authority",
        ):
            assert phrase in current
        assert "only the mutation-receipt reader has the bounded private C2B3 caller" not in current
        assert "only the mutation-receipt role has the bounded private C2B3" not in current
        assert "no public" in current.lower()
        assert "durable authority" in current.lower()


def test_exact_twenty_three_path_implementation_record_is_independently_owned() -> None:
    owner = OWNER_PATH.read_text(encoding="utf-8")
    payload = owner.split("<!-- C2B2_FIELD_LEVEL_CONTRACT_JSON_BEGIN -->", 1)[1]
    payload = payload.split("<!-- C2B2_FIELD_LEVEL_CONTRACT_JSON_END -->", 1)[0].strip()
    candidate = json.loads(payload.removeprefix("```json\n").removesuffix("\n```"))
    scope = candidate["private_readers"]["future_implementation_allowlist"]
    observed = tuple(
        scope[key][index]
        for key in (
            "new_production_source",
            "existing_production_source_modifications",
            "new_documentation",
            "existing_documentation_modifications",
            "new_focused_tests",
            "existing_test_modifications",
        )
        for index in range(len(scope[key]))
    )
    assert scope["maximum_path_count"] == 23
    assert observed == EXPECTED_IMPLEMENTATION_PATHS
    assert len(set(observed)) == 23
