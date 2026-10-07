"""Closed private value-shape, identity, and profile contracts."""

from copy import copy, deepcopy
import base64
import dataclasses
import hashlib
import json
import pickle
import re
import zlib

import pytest

import ge_nwp_coordinator._finite_backlog_risk_source_adapter as adapter
import ge_nwp_coordinator._post_execution_evidence_values as evidence
import ge_nwp_coordinator._post_execution_policy_values as policy
import ge_nwp_coordinator._rw0_c_decision_input_values as decision
import ge_nwp_coordinator._section41_post_execution_proposal_family_projection as projection
import ge_nwp_coordinator._section41_post_execution_role_resolution as resolution
from ge_nwp_coordinator._rw0_c1_semantic_values import _NWPF_DIGEST, _NWPF_REF


VALUE_INVENTORY = {'V01': ('_post_execution_evidence_values',
         'Section41PostExecutionSemanticReviewLineageContextV1',
         ('schema_id',
          'proposal_phase',
          'program_ref',
          'program_version_ref',
          'program_version_number',
          'accepted_intent_revision_ref',
          'work_item_ref',
          'work_item_revision_ref',
          'semantic_attempt_ref',
          'semantic_attempt_digest',
          'attempt_number',
          'candidate_ref',
          'basis_decision_ref',
          'basis_decision_digest',
          'work_spec_ref',
          'work_spec_digest',
          'work_spec_safe_projection_digest',
          'effect_intent_ref',
          'effect_intent_digest',
          'author_command_ref',
          'author_command_digest',
          'standing_grant_ref',
          'standing_grant_digest',
          'attempt_authorization_ref',
          'attempt_authorization_digest',
          'effect_authorization_ref',
          'effect_authorization_digest',
          'attempt_fence_ref',
          'attempt_fence_digest',
          'effect_fence_ref',
          'effect_fence_digest',
          'delivery_attempt_ref',
          'delivery_envelope_digest',
          'delivery_attempt_digest',
          'authority_evaluation_ref',
          'authority_evaluation_digest',
          'lineage_context_ref',
          'lineage_context_digest')),
 'V02': ('_post_execution_evidence_values',
         'PostExecutionSemanticReviewInputContextV1',
         ('schema_id',
          'input_context_ref',
          'profile_ref',
          'profile_digest',
          'proposal_phase',
          'lineage_context_schema_id',
          'lineage_context_ref',
          'lineage_context_digest',
          'phase_basis_ref',
          'phase_basis_digest',
          'preassigned_proposal_ref',
          'role_entry_count',
          'role_entries',
          'model_input_safe_projection_schema_id',
          'model_input_safe_projection_ref',
          'model_input_safe_projection_digest',
          'private_input_manifest_schema_id',
          'private_input_manifest_ref',
          'private_input_manifest_digest',
          'constructed_at',
          'input_context_digest')),
 'V03': ('_post_execution_evidence_values',
         'PostExecutionSemanticReviewRoleEntryV2',
         ('schema_id',
          'role',
          'role_rank',
          'ordinal',
          'typed_schema_id',
          'typed_value_ref',
          'typed_value_digest',
          'source_posture',
          'direct_c1_kind',
          'direct_c1_kind_rank',
          'direct_c1_membership_ref',
          'direct_c1_membership_digest',
          'source_profile_ref',
          'source_profile_digest',
          'source_binding_schema_id',
          'source_binding_ref',
          'source_binding_digest',
          'model_input_posture')),
 'V04': ('_post_execution_evidence_values',
         'CandidateCapsuleSafeProjectionV1',
         ('schema_id',
          'candidate_ref',
          'capsule_manifest_ref',
          'portable_capsule_digest',
          'program_ref',
          'program_version_ref',
          'accepted_intent_revision_ref',
          'work_item_ref',
          'work_item_revision_ref',
          'semantic_attempt_ref',
          'effect_intent_ref',
          'command_ref',
          'command_digest',
          'attempt_fence_ref',
          'attempt_fence_digest',
          'effect_fence_ref',
          'effect_fence_digest',
          'repository_ref',
          'base_git_object_format',
          'base_git_oid',
          'authorized_path_scope_digest',
          'projection_ref',
          'projection_digest')),
 'V05': ('_post_execution_evidence_values',
         'PostExecutionModelInputSafeProjectionV2',
         ('schema_id',
          'profile_ref',
          'profile_digest',
          'proposal_phase',
          'lineage_context_schema_id',
          'lineage_context_ref',
          'lineage_context_digest',
          'entry_count',
          'entries',
          'projection_ref',
          'projection_digest')),
 'V06': ('_post_execution_evidence_values',
         'PostExecutionModelInputProjectionEntryV2',
         ('schema_id',
          'role',
          'role_rank',
          'ordinal',
          'typed_schema_id',
          'typed_value_ref',
          'typed_value_digest',
          'model_value_schema_id',
          'model_value_ref',
          'model_value_digest',
          'model_input_posture')),
 'V07': ('_post_execution_evidence_values',
         'PostExecutionPrivateInputManifestV2',
         ('schema_id',
          'profile_ref',
          'profile_digest',
          'proposal_phase',
          'lineage_context_schema_id',
          'lineage_context_ref',
          'lineage_context_digest',
          'entry_count',
          'entries',
          'manifest_ref',
          'manifest_digest')),
 'V08': ('_post_execution_evidence_values',
         'PostExecutionPrivateInputManifestEntryV2',
         ('schema_id',
          'role',
          'role_rank',
          'ordinal',
          'typed_schema_id',
          'typed_value_ref',
          'typed_value_digest',
          'canonical_byte_length',
          'privacy_classification')),
 'V09': ('_post_execution_evidence_values',
         'PostExecutionModelInputBindingV2',
         ('schema_id',
          'profile_ref',
          'profile_digest',
          'input_context_schema_id',
          'input_context_ref',
          'input_context_digest',
          'lineage_context_schema_id',
          'lineage_context_ref',
          'lineage_context_digest',
          'model_input_safe_projection_schema_id',
          'model_input_safe_projection_ref',
          'model_input_safe_projection_digest',
          'private_input_manifest_schema_id',
          'private_input_manifest_ref',
          'private_input_manifest_digest',
          'source_invocation_ref',
          'source_invocation_digest',
          'model_contract_ref',
          'model_contract_digest',
          'model_configuration_ref',
          'model_configuration_digest',
          'artifact_schema_id',
          'artifact_ref',
          'artifact_digest',
          'artifact_binding_digest',
          'artifact_safe_projection_schema_id',
          'artifact_safe_projection_digest',
          'proposal_ref',
          'proposal_digest',
          'evidence_set_ref',
          'evidence_set_digest',
          'source_invocation_started_at',
          'source_invocation_completed_at',
          'artifact_validated_at',
          'result',
          'reason',
          'binding_ref',
          'binding_digest')),
 'V10': ('_post_execution_evidence_values',
         'PostExecutionEvidenceSupplyV2',
         ('schema_id',
          'profile_ref',
          'profile_digest',
          'input_context',
          'model_input_safe_projection',
          'private_input_manifest',
          'role_supply_count',
          'role_supplies',
          'supply_created_at',
          'supply_ref',
          'supply_digest')),
 'V11': ('_post_execution_evidence_values',
         'PostExecutionRoleSupplyV2',
         ('schema_id',
          'role',
          'role_rank',
          'ordinal',
          'typed_schema_id',
          'typed_value_ref',
          'typed_value_digest',
          'typed_canonical_value',
          'source_profile_ref',
          'source_profile_digest',
          'source_profile_canonical_value',
          'source_binding_schema_id',
          'source_binding_ref',
          'source_binding_digest',
          'source_binding_canonical_value',
          'support_set_ref',
          'support_set_digest',
          'support_set_canonical_value',
          'support_value_count',
          'support_canonical_values',
          'model_input_posture')),
 'V12': ('_post_execution_evidence_values',
         'PostExecutionSupportEntryV1',
         ('role', 'rank', 'ordinal', 'source_schema_id', 'source_ref', 'source_digest')),
 'V13': ('_post_execution_evidence_values',
         'PostExecutionSupportSetV1',
         ('schema_id', 'profile_ref', 'profile_digest', 'entries', 'support_set_ref', 'support_set_digest')),
 'V14': ('_post_execution_evidence_values',
         'ValidationDispositionV1',
         ('schema_id',
          'disposition_ref',
          'profile_ref',
          'profile_digest',
          'source_observation_schema_id',
          'source_observation_ref',
          'source_observation_digest',
          'delivery_attempt_ref',
          'source_kind',
          'source_ref',
          'source_invocation_ref',
          'observation_kind',
          'source_outcome',
          'source_reason_code',
          'source_evidence_refs',
          'source_observed_at',
          'author_role',
          'program_ref',
          'program_version_ref',
          'accepted_intent_revision_ref',
          'work_item_ref',
          'work_item_revision_ref',
          'semantic_attempt_ref',
          'semantic_attempt_digest',
          'attempt_number',
          'candidate_ref',
          'capsule_manifest_ref',
          'portable_capsule_digest',
          'command_ref',
          'command_digest',
          'attempt_fence_ref',
          'attempt_fence_digest',
          'effect_intent_ref',
          'effect_fence_ref',
          'effect_fence_digest',
          'effect_class',
          'validation_tool_profile_ref',
          'validation_tool_profile_digest',
          'validation_tool_qualification_schema_id',
          'validation_tool_qualification_ref',
          'validation_tool_qualification_digest',
          'validation_requirement_schema_id',
          'validation_requirement_ref',
          'validation_requirement_safe_evidence_digest',
          'validation_requirement_digest',
          'validation_requirement_work_spec_ref',
          'validation_requirement_work_spec_digest',
          'validation_result_set_schema_id',
          'validation_result_set_ref',
          'validation_result_set_digest',
          'result',
          'reason',
          'repairability',
          'evaluated_at',
          'expires_at',
          'support_set_ref',
          'support_set_digest',
          'disposition_digest')),
 'V15': ('_post_execution_evidence_values',
         'IndependentReviewDispositionV1',
         ('schema_id',
          'disposition_ref',
          'profile_ref',
          'profile_digest',
          'source_observation_schema_id',
          'source_observation_ref',
          'source_observation_digest',
          'delivery_attempt_ref',
          'source_kind',
          'source_ref',
          'source_invocation_ref',
          'observation_kind',
          'source_outcome',
          'source_reason_code',
          'source_evidence_refs',
          'source_observed_at',
          'author_role',
          'program_ref',
          'program_version_ref',
          'accepted_intent_revision_ref',
          'work_item_ref',
          'work_item_revision_ref',
          'semantic_attempt_ref',
          'semantic_attempt_digest',
          'attempt_number',
          'candidate_ref',
          'capsule_manifest_ref',
          'portable_capsule_digest',
          'command_ref',
          'command_digest',
          'attempt_fence_ref',
          'attempt_fence_digest',
          'effect_intent_ref',
          'effect_fence_ref',
          'effect_fence_digest',
          'effect_class',
          'review_tool_profile_ref',
          'review_tool_profile_digest',
          'review_tool_qualification_schema_id',
          'review_tool_qualification_ref',
          'review_tool_qualification_digest',
          'review_requirement_schema_id',
          'review_requirement_ref',
          'review_requirement_safe_evidence_digest',
          'review_requirement_digest',
          'review_requirement_work_spec_ref',
          'review_requirement_work_spec_digest',
          'review_result_set_schema_id',
          'review_result_set_ref',
          'review_result_set_digest',
          'reviewer_separation_schema_id',
          'reviewer_separation_ref',
          'reviewer_separation_digest',
          'separation_status',
          'result',
          'reason',
          'evaluated_at',
          'expires_at',
          'support_set_ref',
          'support_set_digest',
          'disposition_digest')),
 'V16': ('_post_execution_policy_values',
         'DecisionBranchEvaluationEntryV1',
         ('branch', 'applicability', 'governed_effect_class', 'result', 'reason')),
 'V17': ('_post_execution_policy_values',
         'PostExecutionStandingPolicyBranchMatrixV1',
         ('schema_id',
          'matrix_ref',
          'profile_ref',
          'profile_digest',
          'proposal_phase',
          'program_ref',
          'program_version_ref',
          'accepted_intent_revision_ref',
          'work_item_ref',
          'work_item_revision_ref',
          'semantic_attempt_ref',
          'candidate_ref',
          'effect_intent_ref',
          'author_command_ref',
          'matrix_author_ref',
          'matrix_author_invocation_ref',
          'policy_source_schema_id',
          'policy_source_ref',
          'policy_source_digest',
          'policy_status',
          'policy_revocation_status',
          'parent_grant_ref',
          'parent_grant_digest',
          'grant_family_ref',
          'grant_family_digest',
          'audience_ref',
          'repository_ref',
          'path_scope_digest',
          'risk_lane',
          'source_effect_fence_ref',
          'source_effect_fence_digest',
          'source_effect_class',
          'allowed_branches',
          'allowed_risk_lanes',
          'allowed_effect_classes',
          'policy_ceilings',
          'not_before',
          'expires_at',
          'evaluated_at',
          'entries',
          'support_set_ref',
          'support_set_digest',
          'matrix_digest')),
 'V18': ('_post_execution_policy_values',
         'PostExecutionRiskLaneBranchMatrixV1',
         ('schema_id',
          'matrix_ref',
          'profile_ref',
          'profile_digest',
          'proposal_phase',
          'program_ref',
          'program_version_ref',
          'accepted_intent_revision_ref',
          'development_work_item_ref',
          'work_item_revision_ref',
          'semantic_attempt_ref',
          'candidate_ref',
          'author_command_ref',
          'matrix_author_ref',
          'matrix_author_invocation_ref',
          'risk_lane',
          'source_profile_schema_id',
          'source_profile_ref',
          'source_profile_digest',
          'source_binding_schema_id',
          'source_binding_ref',
          'source_binding_digest',
          'risk_policy_schema_id',
          'risk_policy_ref',
          'risk_policy_digest',
          'policy_status',
          'policy_revocation_status',
          'allowed_risk_lanes',
          'required_risk_lane',
          'not_before',
          'expires_at',
          'evaluated_at',
          'entries',
          'support_set_ref',
          'support_set_digest',
          'matrix_digest')),
 'V19': ('_finite_backlog_risk_source_adapter',
         'FiniteBacklogRiskSourceBindingV1',
         ('schema_id',
          'development_work_item_ref',
          'backlog_ref',
          'backlog_digest',
          'backlog_lease_ref',
          'backlog_work_item_id',
          'risk_lane',
          'mapping_author_ref',
          'mapping_author_digest',
          'mapping_evidence_ref',
          'mapping_evidence_digest',
          'binding_ref',
          'binding_digest')),
 'V20': ('_post_execution_evidence_values',
         'PostExecutionGlobalStopSnapshotV1',
         ('schema_id',
          'profile_ref',
          'profile_digest',
          'global_stop_schema_id',
          'global_stop_ref',
          'global_stop_version',
          'global_stop_state',
          'global_stop_stop_id',
          'global_stop_reason_class',
          'global_stop_issuer_ref',
          'global_stop_issued_at',
          'global_stop_operator_decision_ref',
          'global_stop_digest',
          'global_stop_updated_at',
          'evaluated_at',
          'support_set_ref',
          'support_set_digest',
          'snapshot_ref',
          'snapshot_digest')),
 'V21': ('_post_execution_evidence_values',
         'PostExecutionSourceEffectCeilingEvidenceV1',
         ('schema_id',
          'profile_ref',
          'profile_digest',
          'proposal_phase',
          'program_ref',
          'program_version_ref',
          'accepted_intent_revision_ref',
          'work_item_ref',
          'work_item_revision_ref',
          'semantic_attempt_ref',
          'candidate_ref',
          'effect_intent_ref',
          'repository_ref',
          'base_git_object_format',
          'base_git_oid',
          'source_effect_class',
          'source_effect_ceilings',
          'path_scope_digest',
          'attempt_fence_schema_id',
          'attempt_fence_ref',
          'attempt_fence_digest',
          'attempt_allowed_effect_classes',
          'attempt_ceilings',
          'attempt_fence_expires_at',
          'effect_fence_schema_id',
          'effect_fence_ref',
          'effect_fence_digest',
          'effect_fence_class',
          'effect_ceilings',
          'effect_fence_expires_at',
          'authority_schema_id',
          'authority_observation_ref',
          'authority_observation_digest',
          'authority_status',
          'authority_family_status',
          'authority_revocation_status',
          'authority_allowed_effect_classes',
          'authority_ceilings',
          'authority_grant_expires_at',
          'authority_observation_expires_at',
          'evaluated_at',
          'result',
          'reason',
          'support_set_ref',
          'support_set_digest',
          'evidence_ref',
          'evidence_digest')),
 'V22': ('_section41_post_execution_proposal_family_projection',
         'Section41PostExecutionProposalFamilyProjectionV2',
         ('schema_id',
          'projection_ref',
          'profile_ref',
          'profile_digest',
          'proposal_phase',
          'source_invocation_ref',
          'source_invocation_digest',
          'artifact_ref',
          'artifact_digest',
          'artifact_binding_digest',
          'proposal_ref',
          'proposal_digest',
          'model_contract_ref',
          'model_contract_digest',
          'model_configuration_ref',
          'model_configuration_digest',
          'input_context_schema_id',
          'input_context_ref',
          'input_context_digest',
          'lineage_context_schema_id',
          'lineage_context_ref',
          'lineage_context_digest',
          'safe_projection_schema_id',
          'safe_projection_digest',
          'evidence_set_ref',
          'evidence_set_digest',
          'evidence_binding_count',
          'evidence_bindings',
          'owner_family_graph_digest',
          'recommendation',
          'reason_code',
          'source_invocation_started_at',
          'source_invocation_completed_at',
          'artifact_validated_at',
          'evidence_bound_at',
          'proposal_created_at',
          'projection_evaluated_at',
          'projection_digest')),
 'V23': ('_section41_post_execution_proposal_family_projection',
         'Section41PostExecutionProjectionEvidenceEntryV2',
         ('schema_id',
          'proposal_ref',
          'proposal_phase',
          'evidence_set_ref',
          'evidence_role',
          'role_rank',
          'ordinal',
          'evidence_ref',
          'evidence_digest',
          'required_for_selection',
          'evidence_bound_at',
          'source_binding_schema_id',
          'source_binding_digest',
          'projection_evidence_entry_digest')),
 'V24': ('_section41_post_execution_role_resolution',
         'Section41PostExecutionRoleResolutionV3',
         ('schema_id',
          'profile_ref',
          'profile_digest',
          'input_context_schema_id',
          'input_context_ref',
          'input_context_digest',
          'lineage_context_schema_id',
          'lineage_context_ref',
          'lineage_context_digest',
          'projection_schema_id',
          'projection_ref',
          'projection_digest',
          'source_invocation_ref',
          'source_invocation_digest',
          'proposal_ref',
          'proposal_digest',
          'evidence_set_ref',
          'evidence_set_digest',
          'section41_membership_ref',
          'section41_membership_digest',
          'section41_value_ref',
          'section41_value_digest',
          'context_role_entry_schema_id',
          'context_role',
          'context_role_rank',
          'context_role_ordinal',
          'evidence_locator_proposal_ref',
          'evidence_locator_role',
          'evidence_locator_ordinal',
          'evidence_binding_digest',
          'evidence_bound_at',
          'typed_schema_id',
          'typed_value_ref',
          'typed_value_digest',
          'source_posture',
          'direct_c1_kind',
          'direct_c1_kind_rank',
          'direct_c1_membership_ref',
          'direct_c1_membership_digest',
          'source_profile_ref',
          'source_profile_digest',
          'source_binding_schema_id',
          'source_binding_ref',
          'source_binding_digest',
          'model_input_posture',
          'decision_currentness_profile_ref',
          'decision_currentness_profile_digest',
          'resolution_posture',
          'result',
          'reason',
          'relation_ref',
          'relation_digest')),
 'V25': ('_rw0_c_decision_input_values',
         'RW0CDecisionMembershipClosureV1',
         ('schema_id',
          'profile_ref',
          'profile_digest',
          'phase_basis_ref',
          'phase_basis_digest',
          'entry_count',
          'entries',
          'captured_at',
          'closure_ref',
          'closure_digest')),
 'V26': ('_rw0_c_decision_input_values',
         'RW0CDecisionMembershipClosureEntryV1',
         ('schema_id',
          'kind_rank',
          'membership_ref',
          'membership_digest',
          'value_schema_id',
          'value_ref',
          'value_digest',
          'scope_binding_digest',
          'relation_set_digest',
          'admitted_at',
          'admission_graph_digest')),
 'V27': ('_rw0_c_decision_input_values',
         'RW0CDecisionCurrentSnapshotV1',
         ('schema_id',
          'profile_ref',
          'profile_digest',
          'program_ref',
          'program_version_ref',
          'accepted_intent_revision_ref',
          'work_item_ref',
          'work_item_revision_ref',
          'semantic_attempt_ref',
          'candidate_ref',
          'phase_basis_ref',
          'phase_basis_digest',
          'membership_closure_ref',
          'membership_closure_digest',
          'selected_authority_membership_ref',
          'selected_authority_membership_digest',
          'selected_section41_membership_ref',
          'selected_section41_membership_digest',
          'global_stop_ref',
          'global_stop_digest',
          'attempt_fence_ref',
          'attempt_fence_digest',
          'effect_fence_ref',
          'effect_fence_digest',
          'external_source_count',
          'external_sources',
          'captured_at',
          'snapshot_ref',
          'snapshot_digest')),
 'V28': ('_rw0_c_decision_input_values',
         'ExternalCurrentSourceCoordinateV1',
         ('schema_id',
          'role',
          'source_schema_id',
          'source_ref',
          'source_digest',
          'profile_ref',
          'profile_digest',
          'source_available')),
 'V29': ('_rw0_c_decision_input_values',
         'RW0CProposalEvidenceCurrentnessV1',
         ('schema_id',
          'profile_ref',
          'profile_digest',
          'proposal_ref',
          'proposal_digest',
          'snapshot_ref',
          'snapshot_digest',
          'component_count',
          'components',
          'result',
          'reason',
          'evaluated_at',
          'currentness_ref',
          'currentness_digest')),
 'V30': ('_rw0_c_decision_input_values',
         'RW0CProposalEvidenceCurrentnessComponentV1',
         ('schema_id',
          'component',
          'proposal_source_schema_id',
          'proposal_source_ref',
          'proposal_source_digest',
          'current_source_schema_id',
          'current_source_ref',
          'current_source_digest',
          'profile_ref',
          'profile_digest',
          'source_expires_at',
          'evaluated_at',
          'result',
          'reason')),
 'V31': ('_rw0_c_decision_input_values',
         'RW0CDecisionTimeAuthorityBranchMatrixV1',
         ('schema_id',
          'profile_ref',
          'profile_digest',
          'snapshot_ref',
          'snapshot_digest',
          'proposal_ref',
          'proposal_digest',
          'entry_count',
          'entries',
          'evaluated_at',
          'matrix_ref',
          'matrix_digest')),
 'V32': ('_rw0_c_decision_input_values',
         'RW0CDecisionTimeGlobalStopBranchMatrixV1',
         ('schema_id',
          'profile_ref',
          'profile_digest',
          'snapshot_ref',
          'snapshot_digest',
          'global_stop_ref',
          'global_stop_digest',
          'entry_count',
          'entries',
          'evaluated_at',
          'matrix_ref',
          'matrix_digest')),
 'V33': ('_rw0_c_decision_input_values',
         'RW0CDecisionTimeSourceEffectCeilingBranchMatrixV1',
         ('schema_id',
          'profile_ref',
          'profile_digest',
          'snapshot_ref',
          'snapshot_digest',
          'source_effect_ceiling_ref',
          'source_effect_ceiling_digest',
          'entry_count',
          'entries',
          'evaluated_at',
          'matrix_ref',
          'matrix_digest')),
 'V34': ('_rw0_c_decision_input_values',
         'RW0CRecommendationConsistencyEvaluationV1',
         ('schema_id',
          'profile_ref',
          'profile_digest',
          'proposal_ref',
          'proposal_digest',
          'snapshot_ref',
          'snapshot_digest',
          'proposal_currentness_ref',
          'proposal_currentness_digest',
          'model_recommendation',
          'mapped_branch',
          'authoritative_branch',
          'result',
          'reason',
          'evaluated_at',
          'evaluation_ref',
          'evaluation_digest')),
 'V38': ('_post_execution_evidence_values',
         'PostExecutionValidationResultSetV1',
         ('schema_id',
          'result_set_ref',
          'profile_ref',
          'profile_digest',
          'source_observation_schema_id',
          'source_observation_ref',
          'source_observation_digest',
          'source_kind',
          'source_ref',
          'source_invocation_ref',
          'delivery_attempt_ref',
          'observation_kind',
          'source_outcome',
          'source_reason_code',
          'source_evidence_refs',
          'source_observed_at',
          'program_ref',
          'program_version_ref',
          'accepted_intent_revision_ref',
          'work_item_ref',
          'work_item_revision_ref',
          'semantic_attempt_ref',
          'effect_intent_ref',
          'command_ref',
          'command_digest',
          'attempt_fence_ref',
          'attempt_fence_digest',
          'effect_fence_ref',
          'effect_fence_digest',
          'effect_class',
          'candidate_ref',
          'capsule_manifest_ref',
          'portable_capsule_digest',
          'tool_profile_ref',
          'tool_profile_digest',
          'tool_qualification_schema_id',
          'tool_qualification_ref',
          'tool_qualification_digest',
          'requirement_evidence_schema_id',
          'requirement_evidence_ref',
          'requirement_evidence_safe_digest',
          'requirement_digest',
          'requirement_work_spec_ref',
          'requirement_work_spec_digest',
          'result_author_ref',
          'result_author_invocation_ref',
          'result_set_evidence_refs',
          'result',
          'repairability',
          'reason',
          'evaluated_at',
          'expires_at',
          'result_set_digest')),
 'V39': ('_post_execution_evidence_values',
         'PostExecutionReviewResultSetV1',
         ('schema_id',
          'result_set_ref',
          'profile_ref',
          'profile_digest',
          'source_observation_schema_id',
          'source_observation_ref',
          'source_observation_digest',
          'source_kind',
          'source_ref',
          'source_invocation_ref',
          'delivery_attempt_ref',
          'observation_kind',
          'source_outcome',
          'source_reason_code',
          'source_evidence_refs',
          'source_observed_at',
          'program_ref',
          'program_version_ref',
          'accepted_intent_revision_ref',
          'work_item_ref',
          'work_item_revision_ref',
          'semantic_attempt_ref',
          'effect_intent_ref',
          'command_ref',
          'command_digest',
          'attempt_fence_ref',
          'attempt_fence_digest',
          'effect_fence_ref',
          'effect_fence_digest',
          'effect_class',
          'candidate_ref',
          'capsule_manifest_ref',
          'portable_capsule_digest',
          'tool_profile_ref',
          'tool_profile_digest',
          'tool_qualification_schema_id',
          'tool_qualification_ref',
          'tool_qualification_digest',
          'requirement_evidence_schema_id',
          'requirement_evidence_ref',
          'requirement_evidence_safe_digest',
          'requirement_digest',
          'requirement_work_spec_ref',
          'requirement_work_spec_digest',
          'result_author_ref',
          'result_author_invocation_ref',
          'result_set_evidence_refs',
          'result',
          'reason',
          'evaluated_at',
          'expires_at',
          'result_set_digest')),
 'V40': ('_post_execution_evidence_values',
         'PostExecutionReviewerSeparationEvaluationV1',
         ('schema_id',
          'evaluation_ref',
          'profile_ref',
          'profile_digest',
          'phase_basis_ref',
          'phase_basis_digest',
          'review_membership_schema_id',
          'review_membership_ref',
          'review_membership_digest',
          'review_value_schema_id',
          'review_value_ref',
          'review_value_digest',
          'review_relation_row_schema_id',
          'review_relation_ref',
          'review_relation_digest',
          'review_relation_row_digest',
          'review_relation_schema_id',
          'author_result_membership_schema_id',
          'author_result_membership_ref',
          'author_result_membership_digest',
          'author_result_value_schema_id',
          'author_result_value_ref',
          'author_result_value_digest',
          'author_result_relation_row_schema_id',
          'author_result_relation_ref',
          'author_result_relation_digest',
          'author_result_relation_row_digest',
          'author_result_relation_schema_id',
          'author_observation_locators',
          'review_source_kind',
          'review_source_ref',
          'review_source_invocation_ref',
          'author_source_kind',
          'author_source_ref',
          'author_source_invocation_ref',
          'review_effect_intent_ref',
          'review_effect_fence_ref',
          'review_effect_fence_digest',
          'review_delivery_attempt_ref',
          'author_effect_intent_ref',
          'author_effect_fence_ref',
          'author_effect_fence_digest',
          'author_delivery_attempt_ref',
          'author_command_ref',
          'author_command_digest',
          'attempt_fence_ref',
          'attempt_fence_digest',
          'program_ref',
          'program_version_ref',
          'accepted_intent_revision_ref',
          'work_item_ref',
          'work_item_revision_ref',
          'semantic_attempt_ref',
          'candidate_ref',
          'capsule_manifest_ref',
          'portable_capsule_digest',
          'support_set_ref',
          'support_set_digest',
          'status',
          'reason',
          'evaluated_at',
          'evaluation_digest')),
 'V40.n01': ('_post_execution_evidence_values',
             'PostExecutionReviewerSeparationAuthorObservationLocatorV1',
             ('schema_id',
              'ordinal',
              'membership_schema_id',
              'membership_ref',
              'membership_digest',
              'value_schema_id',
              'value_ref',
              'value_digest',
              'relation_row_schema_id',
              'relation_ref',
              'relation_digest',
              'relation_row_digest',
              'relation_schema_id',
              'source_kind',
              'source_ref',
              'source_invocation_ref',
              'observation_kind',
              'effect_intent_ref',
              'effect_fence_ref',
              'effect_fence_digest',
              'delivery_attempt_ref')),
 'V41': ('_post_execution_policy_values',
         'PostExecutionStandingPolicySourceAttestationV1',
         ('schema_id',
          'attestation_ref',
          'profile_ref',
          'profile_digest',
          'source_owner_kind',
          'source_owner_ref',
          'source_owner_invocation_ref',
          'source_evidence_ref',
          'source_evidence_digest',
          'policy_ref',
          'policy_digest',
          'parent_grant_ref',
          'parent_grant_digest',
          'grant_family_ref',
          'grant_family_digest',
          'audience_ref',
          'repository_ref',
          'path_scope_digest',
          'policy_status',
          'revocation_status',
          'allowed_branches',
          'allowed_risk_lanes',
          'allowed_effect_classes',
          'max_active_invocations',
          'max_candidate_bytes',
          'max_changed_files',
          'max_cost_microusd',
          'max_cpu_seconds',
          'max_deliveries',
          'max_deployments',
          'max_local_commits',
          'max_memory_bytes',
          'max_merges',
          'max_model_input_tokens',
          'max_model_output_tokens',
          'max_pull_requests',
          'max_pushes',
          'max_wall_seconds',
          'branch_assertions',
          'not_before',
          'expires_at',
          'evaluated_at',
          'attestation_digest')),
 'V41.n01': ('_post_execution_policy_values',
             'PostExecutionStandingPolicyBranchAssertionV1',
             ('schema_id', 'branch', 'applicability', 'governed_effect_class', 'result', 'reason')),
 'V42': ('_post_execution_policy_values',
         'PostExecutionRiskPolicyAttestationV1',
         ('schema_id',
          'attestation_ref',
          'profile_ref',
          'profile_digest',
          'source_owner_kind',
          'source_owner_ref',
          'source_owner_invocation_ref',
          'source_evidence_ref',
          'source_evidence_digest',
          'risk_policy_ref',
          'risk_policy_digest',
          'policy_status',
          'revocation_status',
          'allowed_risk_lanes',
          'required_risk_lane',
          'source_profile_schema_id',
          'source_profile_ref',
          'source_profile_digest',
          'branch_assertions',
          'not_before',
          'expires_at',
          'evaluated_at',
          'attestation_digest')),
 'V42.n01': ('_post_execution_policy_values',
             'PostExecutionRiskPolicyBranchAssertionV1',
             ('schema_id', 'branch', 'applicability', 'governed_effect_class', 'result', 'reason')),
 'V43': ('_post_execution_policy_values',
         'PostExecutionRiskSourceProfileV1',
         ('schema_id',
          'source_profile_ref',
          'source_family',
          'source_system_schema_id',
          'adapter_profile_ref',
          'adapter_profile_digest',
          'profile_version',
          'external_authority_claim',
          'source_profile_digest')),
 'V44': ('_post_execution_policy_values',
         'PostExecutionRiskSourceBindingV1',
         ('schema_id',
          'source_binding_ref',
          'source_profile_schema_id',
          'source_profile_ref',
          'source_profile_digest',
          'development_work_item_ref',
          'risk_lane',
          'source_value_schema_id',
          'source_value_ref',
          'source_value_digest',
          'mapping_evidence_ref',
          'mapping_evidence_digest',
          'evaluated_at',
          'expires_at',
          'source_binding_digest'))}
FIELD_SPECS = {'V01': [{'constant': 'governed-execution.nwp-section41-post-execution-semantic-review-lineage-context.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'proposal_phase', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'program_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'program_version_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'program_version_number',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'accepted_intent_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'semantic_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'semantic_attempt_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_number',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'candidate_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'basis_decision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'basis_decision_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'work_spec_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_spec_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'work_spec_safe_projection_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'effect_intent_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_intent_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'author_command_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'author_command_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'standing_grant_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'standing_grant_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_authorization_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_authorization_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'effect_authorization_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_authorization_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'delivery_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'delivery_envelope_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'delivery_attempt_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'authority_evaluation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'authority_evaluation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'lineage_context_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'lineage_context_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V02': [{'constant': 'governed-execution.nwp-post-execution-semantic-review-context.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'input_context_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_phase', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'lineage_context_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'lineage_context_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'lineage_context_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'phase_basis_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'phase_basis_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'preassigned_proposal_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'role_entry_count',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'cardinality': 9,
          'name': 'role_entries',
          'nullable': False,
          'ordering': 'literal_owner_order;duplicates_rejected_when_profile_requires',
          'type': 'exact_builtin_list'},
         {'name': 'model_input_safe_projection_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'model_input_safe_projection_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'model_input_safe_projection_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'private_input_manifest_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'private_input_manifest_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'private_input_manifest_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'constructed_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'input_context_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V03': [{'constant': 'governed-execution.nwp-post-execution-semantic-review-role-entry.v2',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'role',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'role_rank',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'ordinal',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'typed_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'typed_value_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'typed_value_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_posture', 'nullable': False, 'type': 'exact_builtin_str'},
         {'branch_rule': 'non_null_only_for_roles_with_direct_c1_in_governing_profile;otherwise_null',
          'name': 'direct_c1_kind',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_direct_c1_in_governing_profile;otherwise_null',
          'name': 'direct_c1_kind_rank',
          'nullable': True,
          'type': 'exact_builtin_int_bool_rejected_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_direct_c1_in_governing_profile;otherwise_null',
          'name': 'direct_c1_membership_ref',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_direct_c1_in_governing_profile;otherwise_null',
          'name': 'direct_c1_membership_digest',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_profile_in_governing_profile;otherwise_null',
          'name': 'source_profile_ref',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_profile_in_governing_profile;otherwise_null',
          'name': 'source_profile_digest',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
          'name': 'source_binding_schema_id',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
          'name': 'source_binding_ref',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
          'name': 'source_binding_digest',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'name': 'model_input_posture', 'nullable': False, 'type': 'exact_builtin_str'}],
 'V04': [{'constant': 'governed-execution.nwp-candidate-capsule-safe-projection.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'candidate_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'capsule_manifest_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'portable_capsule_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'program_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'program_version_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'accepted_intent_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'semantic_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_intent_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'command_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'command_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'repository_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'base_git_object_format', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'base_git_oid', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'authorized_path_scope_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'projection_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'projection_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V05': [{'constant': 'governed-execution.nwp-post-execution-model-input-safe-projection.v2',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_phase', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'lineage_context_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'lineage_context_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'lineage_context_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'entry_count',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'cardinality': 9,
          'name': 'entries',
          'nullable': False,
          'ordering': 'literal_owner_order;duplicates_rejected_when_profile_requires',
          'type': 'exact_builtin_list'},
         {'name': 'projection_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'projection_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V06': [{'constant': 'governed-execution.nwp-post-execution-model-input-projection-entry.v2',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'role',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'role_rank',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'ordinal',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'typed_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'typed_value_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'typed_value_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'model_value_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'model_value_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'model_value_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'model_input_posture', 'nullable': False, 'type': 'exact_builtin_str'}],
 'V07': [{'constant': 'governed-execution.nwp-post-execution-private-input-manifest.v2',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_phase', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'lineage_context_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'lineage_context_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'lineage_context_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'entry_count',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'cardinality': 1,
          'name': 'entries',
          'nullable': False,
          'ordering': 'literal_owner_order;duplicates_rejected_when_profile_requires',
          'type': 'exact_builtin_list'},
         {'name': 'manifest_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'manifest_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V08': [{'constant': 'governed-execution.nwp-post-execution-private-input-manifest-entry.v2',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'role',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'role_rank',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'ordinal',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'typed_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'typed_value_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'typed_value_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'canonical_byte_length',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'privacy_classification', 'nullable': False, 'type': 'exact_builtin_str'}],
 'V09': [{'constant': 'governed-execution.nwp-post-execution-model-input-binding.v2',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'input_context_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'input_context_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'input_context_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'lineage_context_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'lineage_context_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'lineage_context_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'model_input_safe_projection_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'model_input_safe_projection_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'model_input_safe_projection_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'private_input_manifest_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'private_input_manifest_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'private_input_manifest_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_invocation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'model_contract_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'model_contract_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'model_configuration_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'model_configuration_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'artifact_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'artifact_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'artifact_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'artifact_binding_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'artifact_safe_projection_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'artifact_safe_projection_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'evidence_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'evidence_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_invocation_started_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'source_invocation_completed_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'artifact_validated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'result',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'reason',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'binding_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'binding_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V10': [{'constant': 'governed-execution.nwp-post-execution-evidence-supply.v2',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'input_context',
          'nullable': False,
          'type': 'exact_builtin_dict',
          'unknown_nested_fields': 'reject'},
         {'name': 'model_input_safe_projection',
          'nullable': False,
          'type': 'exact_builtin_dict',
          'unknown_nested_fields': 'reject'},
         {'name': 'private_input_manifest',
          'nullable': False,
          'type': 'exact_builtin_dict',
          'unknown_nested_fields': 'reject'},
         {'name': 'role_supply_count',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'cardinality': 9,
          'name': 'role_supplies',
          'nullable': False,
          'ordering': 'literal_owner_order;duplicates_rejected_when_profile_requires',
          'type': 'exact_builtin_list'},
         {'name': 'supply_created_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'supply_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'supply_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V11': [{'constant': 'governed-execution.nwp-post-execution-role-supply.v2',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'role',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'role_rank',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'ordinal',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'typed_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'typed_value_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'typed_value_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'typed_canonical_value',
          'nullable': False,
          'type': 'exact_builtin_dict',
          'unknown_nested_fields': 'reject'},
         {'branch_rule': 'non_null_only_for_roles_with_source_profile_in_governing_profile;otherwise_null',
          'name': 'source_profile_ref',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_profile_in_governing_profile;otherwise_null',
          'name': 'source_profile_digest',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_profile_in_governing_profile;otherwise_null',
          'name': 'source_profile_canonical_value',
          'nullable': True,
          'type': 'exact_builtin_dict_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
          'name': 'source_binding_schema_id',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
          'name': 'source_binding_ref',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
          'name': 'source_binding_digest',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
          'name': 'source_binding_canonical_value',
          'nullable': True,
          'type': 'exact_builtin_dict_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_support_set_in_governing_profile;otherwise_null',
          'name': 'support_set_ref',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_support_set_in_governing_profile;otherwise_null',
          'name': 'support_set_digest',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_support_set_in_governing_profile;otherwise_null',
          'name': 'support_set_canonical_value',
          'nullable': True,
          'type': 'exact_builtin_dict_or_exact_null'},
         {'name': 'support_value_count',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'support_canonical_values',
          'nullable': False,
          'rule': {'branch_rule': 'support_set_is_null_iff_support_value_count_is_zero_and_values_are_empty',
                   'count_equality': 'length_equals_support_value_count',
                   'item_type': 'exact_builtin_dict',
                   'maximum': 16,
                   'minimum': 0,
                   'ordering': 'exact_support_set_entry_order',
                   'value_equality': 'non_null_support_set_length_and_each_value_match_entry_schema_ref_digest_in_order'},
          'type': 'exact_builtin_list'},
         {'name': 'model_input_posture', 'nullable': False, 'type': 'exact_builtin_str'}],
 'V12': [{'name': 'role',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'rank',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'ordinal',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'source_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V13': [{'constant': 'governed-execution.nwp-post-execution-support-set.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'entries',
          'nullable': False,
          'rule': {'count_equality': 'length_equals_owner_inventory_by_consumer_entry_count_for_profile_ref',
                   'duplicates': 'reject_repeated_role_rank_ordinal_or_unapproved_repeated_source_pair',
                   'item_type': 'PostExecutionSupportEntryV1',
                   'maximum': 16,
                   'minimum': 1,
                   'ordering': 'exact_owner_inventory_by_consumer_order',
                   'value_equality': 'equals_literal_owner_inventory_by_consumer_for_profile_ref'},
          'type': 'exact_builtin_list'},
         {'name': 'support_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'support_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V14': [{'constant': 'governed-execution.nwp-validation-disposition.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'disposition_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_observation_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_observation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_observation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'delivery_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_kind',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'observation_kind',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_outcome', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_reason_code', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_evidence_refs',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_safe_ref',
                   'maximum': 32,
                   'minimum': 0,
                   'ordering': 'strict_lexicographic',
                   'value_equality': 'equals_exact_current_source_observation_source_evidence_refs'},
          'type': 'exact_builtin_list'},
         {'name': 'source_observed_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'author_role', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'program_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'program_version_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'accepted_intent_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'semantic_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'semantic_attempt_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_number',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'candidate_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'capsule_manifest_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'portable_capsule_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'command_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'command_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'effect_intent_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'effect_class',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'validation_tool_profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'validation_tool_profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'validation_tool_qualification_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'validation_tool_qualification_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'validation_tool_qualification_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'validation_requirement_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'validation_requirement_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'validation_requirement_safe_evidence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'validation_requirement_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'validation_requirement_work_spec_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'validation_requirement_work_spec_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'validation_result_set_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'validation_result_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'validation_result_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'result',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'reason',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'repairability', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'expires_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'support_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'support_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'disposition_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V15': [{'constant': 'governed-execution.nwp-independent-review-disposition.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'disposition_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_observation_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_observation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_observation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'delivery_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_kind',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'observation_kind',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_outcome', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_reason_code', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_evidence_refs',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_safe_ref',
                   'maximum': 32,
                   'minimum': 0,
                   'ordering': 'strict_lexicographic',
                   'value_equality': 'equals_exact_current_source_observation_source_evidence_refs'},
          'type': 'exact_builtin_list'},
         {'name': 'source_observed_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'author_role', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'program_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'program_version_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'accepted_intent_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'semantic_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'semantic_attempt_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_number',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'candidate_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'capsule_manifest_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'portable_capsule_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'command_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'command_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'effect_intent_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'effect_class',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'review_tool_profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'review_tool_profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'review_tool_qualification_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'review_tool_qualification_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'review_tool_qualification_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'review_requirement_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'review_requirement_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'review_requirement_safe_evidence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'review_requirement_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'review_requirement_work_spec_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'review_requirement_work_spec_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'review_result_set_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'review_result_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'review_result_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'reviewer_separation_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'reviewer_separation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'reviewer_separation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'separation_status', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'result',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'reason',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'expires_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'support_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'support_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'disposition_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V16': [{'name': 'branch',
          'nullable': False,
          'rule': 'closed_by_dispatched_consuming_profile',
          'type': 'exact_builtin_str'},
         {'name': 'applicability',
          'nullable': False,
          'rule': 'governed_or_halt_only_closed_by_dispatched_consuming_profile',
          'type': 'exact_builtin_str'},
         {'branch_rule': 'exact_builtin_str_for_governed_applicability;exact_null_for_halt_only',
          'name': 'governed_effect_class',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'name': 'result',
          'nullable': False,
          'rule': 'closed_by_dispatched_consuming_profile',
          'type': 'exact_builtin_str'},
         {'name': 'reason',
          'nullable': False,
          'rule': 'closed_by_dispatched_consuming_profile',
          'type': 'exact_builtin_str'}],
 'V17': [{'constant': 'governed-execution.nwp-post-execution-standing-policy-branch-matrix.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'matrix_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_phase', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'program_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'program_version_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'accepted_intent_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'semantic_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'candidate_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_intent_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'author_command_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'matrix_author_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'matrix_author_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'policy_source_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'policy_source_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'policy_source_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'policy_status', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'policy_revocation_status', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'parent_grant_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'parent_grant_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'grant_family_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'grant_family_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'audience_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'repository_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'path_scope_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'risk_lane', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_effect_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_effect_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_effect_class', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'allowed_branches',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_enum',
                   'maximum': 5,
                   'minimum': 1,
                   'ordering': 'canonical_branch_order',
                   'subset_of': 'current_canonical_branches',
                   'value_equality': 'equals_exact_current_V41.allowed_branches'},
          'type': 'exact_builtin_list'},
         {'name': 'allowed_risk_lanes',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_safe_ref',
                   'maximum': 32,
                   'minimum': 1,
                   'ordering': 'strict_lexicographic',
                   'value_equality': 'equals_exact_current_V41.allowed_risk_lanes'},
          'type': 'exact_builtin_list'},
         {'name': 'allowed_effect_classes',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_enum',
                   'maximum': 5,
                   'minimum': 0,
                   'ordering': 'canonical_effect_class_order',
                   'subset_of': 'current_effect_classes',
                   'value_equality': 'equals_exact_current_V41.allowed_effect_classes'},
          'type': 'exact_builtin_list'},
         {'name': 'policy_ceilings',
          'nullable': False,
          'type': 'exact_builtin_dict',
          'unknown_nested_fields': 'reject'},
         {'name': 'not_before', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'expires_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'cardinality': 5,
          'name': 'entries',
          'nullable': False,
          'ordering': 'exact_consuming_profile_branch_order;duplicates_rejected',
          'rule': {'child_encoded_fields': ['branch',
                                            'applicability',
                                            'governed_effect_class',
                                            'result',
                                            'reason'],
                   'child_field_equality': 'exact',
                   'child_schema_id': 'governed-execution.nwp-decision-branch-evaluation-entry.v1',
                   'child_unknown_field_behavior': 'reject_before_parent_canonicalization_or_identity_acceptance',
                   'parent_identity_protection': 'the parent matrix ref/digest pair identifies the matrix '
                                                 'and matrix_digest binds exact child order and canonical '
                                                 'bytes',
                   'parent_profile_dispatch': {'profile_digest': 'd0c25cc85f015d222d1fa9ef14d375fe68f16f17283326a9df7d5605cdc9c539',
                                               'profile_ref': 'post-execution-standing-policy-matrix.v1'},
                   'parent_source_binding': {'direct_fields': ['policy_source_schema_id',
                                                               'policy_source_ref',
                                                               'policy_source_digest',
                                                               'parent_grant_ref',
                                                               'parent_grant_digest',
                                                               'grant_family_ref',
                                                               'grant_family_digest',
                                                               'audience_ref',
                                                               'repository_ref',
                                                               'path_scope_digest',
                                                               'risk_lane',
                                                               'source_effect_fence_ref',
                                                               'source_effect_fence_digest',
                                                               'source_effect_class'],
                                             'posture': 'parent_only',
                                             'proof': 'the V17 parent binds the policy source and related '
                                                      'grant, audience, repository, path, risk, and '
                                                      'effect-fence coordinates used by all five entries'},
                   'source_identity_posture': 'parent_only;forbidden_in_child'},
          'type': 'exact_builtin_list'},
         {'name': 'support_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'support_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'matrix_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V18': [{'constant': 'governed-execution.nwp-post-execution-risk-lane-branch-matrix.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'matrix_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_phase', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'program_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'program_version_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'accepted_intent_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'development_work_item_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'semantic_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'candidate_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'author_command_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'matrix_author_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'matrix_author_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'risk_lane', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_profile_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_binding_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_binding_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_binding_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'risk_policy_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'risk_policy_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'risk_policy_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'policy_status', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'policy_revocation_status', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'allowed_risk_lanes',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_safe_ref',
                   'maximum': 32,
                   'minimum': 1,
                   'ordering': 'strict_lexicographic',
                   'value_equality': 'equals_exact_current_V42.allowed_risk_lanes'},
          'type': 'exact_builtin_list'},
         {'name': 'required_risk_lane', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'not_before', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'expires_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'cardinality': 5,
          'name': 'entries',
          'nullable': False,
          'ordering': 'exact_consuming_profile_branch_order;duplicates_rejected',
          'rule': {'child_encoded_fields': ['branch',
                                            'applicability',
                                            'governed_effect_class',
                                            'result',
                                            'reason'],
                   'child_field_equality': 'exact',
                   'child_schema_id': 'governed-execution.nwp-decision-branch-evaluation-entry.v1',
                   'child_unknown_field_behavior': 'reject_before_parent_canonicalization_or_identity_acceptance',
                   'parent_identity_protection': 'the parent matrix ref/digest pair identifies the matrix '
                                                 'and matrix_digest binds exact child order and canonical '
                                                 'bytes',
                   'parent_profile_dispatch': {'profile_digest': '436ba40a1386d2843bc890767920a7c1cebae96e8c7fa0ed86ef16022c46e502',
                                               'profile_ref': 'post-execution-risk-lane-matrix.v1'},
                   'parent_source_binding': {'direct_fields': ['risk_policy_schema_id',
                                                               'risk_policy_ref',
                                                               'risk_policy_digest',
                                                               'source_profile_schema_id',
                                                               'source_profile_ref',
                                                               'source_profile_digest',
                                                               'source_binding_schema_id',
                                                               'source_binding_ref',
                                                               'source_binding_digest',
                                                               'risk_lane',
                                                               'required_risk_lane'],
                                             'posture': 'parent_only',
                                             'proof': 'the V18 parent binds the risk policy, generic source '
                                                      'profile, source binding, and risk-lane coordinates '
                                                      'used by all five entries'},
                   'source_identity_posture': 'parent_only;forbidden_in_child'},
          'type': 'exact_builtin_list'},
         {'name': 'support_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'support_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'matrix_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V19': [{'constant': 'governed-execution.nwp-finite-backlog-risk-source-binding.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'development_work_item_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'backlog_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'backlog_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'backlog_lease_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'backlog_work_item_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'risk_lane', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'mapping_author_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'mapping_author_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'mapping_evidence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'mapping_evidence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'binding_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'binding_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V20': [{'constant': 'governed-execution.nwp-post-execution-global-stop-snapshot.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'global_stop_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'global_stop_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'global_stop_version',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'global_stop_state', 'nullable': False, 'type': 'exact_builtin_str'},
         {'branch_rule': 'null_only_in_the_literal_profile_branch_exhibited_by_the_golden_value',
          'name': 'global_stop_stop_id',
          'nullable': True,
          'type': 'exact_null'},
         {'branch_rule': 'null_only_in_the_literal_profile_branch_exhibited_by_the_golden_value',
          'name': 'global_stop_reason_class',
          'nullable': True,
          'type': 'exact_null'},
         {'branch_rule': 'null_only_in_the_literal_profile_branch_exhibited_by_the_golden_value',
          'name': 'global_stop_issuer_ref',
          'nullable': True,
          'type': 'exact_null'},
         {'branch_rule': 'null_only_in_the_literal_profile_branch_exhibited_by_the_golden_value',
          'name': 'global_stop_issued_at',
          'nullable': True,
          'type': 'exact_null'},
         {'branch_rule': 'null_only_in_the_literal_profile_branch_exhibited_by_the_golden_value',
          'name': 'global_stop_operator_decision_ref',
          'nullable': True,
          'type': 'exact_null'},
         {'name': 'global_stop_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'global_stop_updated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'support_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'support_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'snapshot_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'snapshot_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V21': [{'constant': 'governed-execution.nwp-post-execution-source-effect-ceiling-evidence.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_phase', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'program_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'program_version_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'accepted_intent_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'semantic_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'candidate_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_intent_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'repository_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'base_git_object_format', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'base_git_oid', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_effect_class', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_effect_ceilings',
          'nullable': False,
          'type': 'exact_builtin_dict',
          'unknown_nested_fields': 'reject'},
         {'name': 'path_scope_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_allowed_effect_classes',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_enum',
                   'maximum': 5,
                   'minimum': 1,
                   'ordering': 'strict_lexicographic_current_effect_class_order',
                   'subset_of': 'current_effect_classes'},
          'type': 'exact_builtin_list'},
         {'name': 'attempt_ceilings',
          'nullable': False,
          'type': 'exact_builtin_dict',
          'unknown_nested_fields': 'reject'},
         {'name': 'attempt_fence_expires_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'effect_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_class', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'effect_ceilings',
          'nullable': False,
          'type': 'exact_builtin_dict',
          'unknown_nested_fields': 'reject'},
         {'name': 'effect_fence_expires_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'authority_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'authority_observation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'authority_observation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'authority_status', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'authority_family_status', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'authority_revocation_status', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'authority_allowed_effect_classes',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_enum',
                   'maximum': 5,
                   'minimum': 1,
                   'ordering': 'strict_lexicographic_current_effect_class_order',
                   'subset_of': 'current_effect_classes'},
          'type': 'exact_builtin_list'},
         {'name': 'authority_ceilings',
          'nullable': False,
          'type': 'exact_builtin_dict',
          'unknown_nested_fields': 'reject'},
         {'name': 'authority_grant_expires_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'authority_observation_expires_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'result',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'reason',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'support_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'support_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'evidence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'evidence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V22': [{'constant': 'governed-execution.nwp-section41-post-execution-proposal-family-projection.v2',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'projection_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_phase', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_invocation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'artifact_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'artifact_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'artifact_binding_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'model_contract_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'model_contract_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'model_configuration_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'model_configuration_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'input_context_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'input_context_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'input_context_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'lineage_context_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'lineage_context_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'lineage_context_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'safe_projection_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'safe_projection_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'evidence_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'evidence_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'evidence_binding_count',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'cardinality': 9,
          'name': 'evidence_bindings',
          'nullable': False,
          'ordering': 'literal_owner_order;duplicates_rejected_when_profile_requires',
          'type': 'exact_builtin_list'},
         {'name': 'owner_family_graph_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'recommendation', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'reason_code', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_invocation_started_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'source_invocation_completed_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'artifact_validated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'evidence_bound_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_created_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'projection_evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'projection_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V23': [{'constant': 'governed-execution.nwp-section41-post-execution-projection-evidence-entry.v2',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'proposal_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_phase', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'evidence_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'evidence_role', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'role_rank',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'ordinal',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'evidence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'evidence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'required_for_selection',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'evidence_bound_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'source_binding_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_binding_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'projection_evidence_entry_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V24': [{'constant': 'governed-execution.nwp-section41-post-execution-role-resolution.v3',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'input_context_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'input_context_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'input_context_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'lineage_context_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'lineage_context_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'lineage_context_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'projection_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'projection_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'projection_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_invocation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'evidence_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'evidence_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'section41_membership_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'section41_membership_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'section41_value_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'section41_value_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'context_role_entry_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'context_role', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'context_role_rank',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'context_role_ordinal',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'evidence_locator_proposal_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'evidence_locator_role', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'evidence_locator_ordinal',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'evidence_binding_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'evidence_bound_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'typed_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'typed_value_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'typed_value_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_posture', 'nullable': False, 'type': 'exact_builtin_str'},
         {'branch_rule': 'non_null_only_for_roles_with_direct_c1_in_governing_profile;otherwise_null',
          'name': 'direct_c1_kind',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_direct_c1_in_governing_profile;otherwise_null',
          'name': 'direct_c1_kind_rank',
          'nullable': True,
          'type': 'exact_builtin_int_bool_rejected_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_direct_c1_in_governing_profile;otherwise_null',
          'name': 'direct_c1_membership_ref',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_direct_c1_in_governing_profile;otherwise_null',
          'name': 'direct_c1_membership_digest',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_profile_in_governing_profile;otherwise_null',
          'name': 'source_profile_ref',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_profile_in_governing_profile;otherwise_null',
          'name': 'source_profile_digest',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
          'name': 'source_binding_schema_id',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
          'name': 'source_binding_ref',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
          'name': 'source_binding_digest',
          'nullable': True,
          'type': 'exact_builtin_str_or_exact_null'},
         {'name': 'model_input_posture', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'decision_currentness_profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'decision_currentness_profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'resolution_posture', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'result',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'reason',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'relation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'relation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V25': [{'constant': 'governed-execution.nwp-rw0-c-decision-membership-closure.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'phase_basis_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'phase_basis_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'entry_count',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'entries',
          'nullable': False,
          'rule': {'count_equality': 'length_equals_entry_count',
                   'duplicates': 'reject',
                   'item_type': 'RW0CDecisionMembershipClosureEntryV1',
                   'maximum': 65536,
                   'minimum': 0,
                   'ordering': 'strict_kind_rank_then_membership_ref',
                   'value_equality': 'complete_result_of_frozen_exhaustive_page_algorithm'},
          'type': 'exact_builtin_list'},
         {'name': 'captured_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'closure_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'closure_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V26': [{'constant': 'governed-execution.nwp-rw0-c-decision-membership-closure-entry.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'kind_rank',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'membership_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'membership_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'value_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'value_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'value_digest', 'nullable': False, 'rule': '64_lowercase_hex', 'type': 'exact_builtin_str'},
         {'name': 'scope_binding_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'relation_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'admitted_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'admission_graph_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V27': [{'constant': 'governed-execution.nwp-rw0-c-decision-current-snapshot.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'program_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'program_version_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'accepted_intent_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'semantic_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'candidate_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'phase_basis_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'phase_basis_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'membership_closure_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'membership_closure_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'selected_authority_membership_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'selected_authority_membership_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'selected_section41_membership_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'selected_section41_membership_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'global_stop_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'global_stop_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'external_source_count',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'cardinality': 5,
          'name': 'external_sources',
          'nullable': False,
          'ordering': 'literal_owner_order;duplicates_rejected_when_profile_requires',
          'type': 'exact_builtin_list'},
         {'name': 'captured_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'snapshot_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'snapshot_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V28': [{'constant': 'governed-execution.nwp-rw0-c-external-current-source-coordinate.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'role',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_available', 'nullable': False, 'type': 'exact_builtin_bool'}],
 'V29': [{'constant': 'governed-execution.nwp-rw0-c-proposal-evidence-currentness.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'snapshot_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'snapshot_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'component_count',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'cardinality': 5,
          'name': 'components',
          'nullable': False,
          'ordering': 'literal_owner_order;duplicates_rejected_when_profile_requires',
          'type': 'exact_builtin_list'},
         {'name': 'result',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'reason',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'currentness_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'currentness_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V30': [{'constant': 'governed-execution.nwp-rw0-c-proposal-evidence-currentness-component.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'enum': ['validation', 'review', 'policy', 'risk_profile', 'risk_binding'],
          'name': 'component',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'proposal_source_schema_id',
          'nullable': False,
          'rule': 'equals_governing_profile_component_owner_schema_map_for_component',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_source_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_source_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'current_source_schema_id',
          'nullable': False,
          'rule': 'equals_governing_profile_component_owner_schema_map_for_component',
          'type': 'exact_builtin_str'},
         {'name': 'current_source_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'current_source_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_expires_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'result',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'reason',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'}],
 'V31': [{'constant': 'governed-execution.nwp-rw0-c-decision-time-authority-branch-matrix.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'snapshot_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'snapshot_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'entry_count',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'cardinality': 5,
          'name': 'entries',
          'nullable': False,
          'ordering': 'exact_consuming_profile_branch_order;duplicates_rejected',
          'rule': {'child_encoded_fields': ['branch',
                                            'applicability',
                                            'governed_effect_class',
                                            'result',
                                            'reason'],
                   'child_field_equality': 'exact',
                   'child_schema_id': 'governed-execution.nwp-decision-branch-evaluation-entry.v1',
                   'child_unknown_field_behavior': 'reject_before_parent_canonicalization_or_identity_acceptance',
                   'parent_identity_protection': 'the parent matrix ref/digest pair identifies the matrix '
                                                 'and matrix_digest binds exact child order and canonical '
                                                 'bytes',
                   'parent_profile_dispatch': {'profile_digest': '07384a871dd87a8387c97bb1cd60e6cc8207333428e04e7766044ec8567677dc',
                                               'profile_ref': 'rw0-c-decision-time-authority-branch.v1'},
                   'parent_source_binding': {'direct_fields': ['snapshot_ref',
                                                               'snapshot_digest',
                                                               'proposal_ref',
                                                               'proposal_digest',
                                                               'profile_ref',
                                                               'profile_digest'],
                                             'posture': 'parent_only',
                                             'proof': 'the exact current snapshot binds closure and '
                                                      'selected-authority membership lineage; the proposal '
                                                      'pair and authority profile complete the unique '
                                                      'authority basis shared by all five entries',
                                             'snapshot_bound_components': ['membership_closure_ref',
                                                                           'membership_closure_digest',
                                                                           'selected_authority_membership_ref',
                                                                           'selected_authority_membership_digest']},
                   'source_identity_posture': 'parent_only;forbidden_in_child'},
          'type': 'exact_builtin_list'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'matrix_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'matrix_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V32': [{'constant': 'governed-execution.nwp-rw0-c-decision-time-global-stop-branch-matrix.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'snapshot_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'snapshot_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'global_stop_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'global_stop_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'entry_count',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'cardinality': 5,
          'name': 'entries',
          'nullable': False,
          'ordering': 'exact_consuming_profile_branch_order;duplicates_rejected',
          'rule': {'child_encoded_fields': ['branch',
                                            'applicability',
                                            'governed_effect_class',
                                            'result',
                                            'reason'],
                   'child_field_equality': 'exact',
                   'child_schema_id': 'governed-execution.nwp-decision-branch-evaluation-entry.v1',
                   'child_unknown_field_behavior': 'reject_before_parent_canonicalization_or_identity_acceptance',
                   'parent_identity_protection': 'the parent matrix ref/digest pair identifies the matrix '
                                                 'and matrix_digest binds exact child order and canonical '
                                                 'bytes',
                   'parent_profile_dispatch': {'profile_digest': '6139df3c64d3736e6938605bc6abef22c258e4841ffe8b641d7a70490f6a5e47',
                                               'profile_ref': 'rw0-c-decision-time-global-stop-branch.v1'},
                   'parent_source_binding': {'direct_fields': ['global_stop_ref',
                                                               'global_stop_digest',
                                                               'snapshot_ref',
                                                               'snapshot_digest',
                                                               'profile_ref',
                                                               'profile_digest'],
                                             'posture': 'parent_only',
                                             'proof': 'the V32 parent directly binds the exact global-stop '
                                                      'source plus snapshot and profile used by all five '
                                                      'entries'},
                   'source_identity_posture': 'parent_only;forbidden_in_child'},
          'type': 'exact_builtin_list'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'matrix_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'matrix_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V33': [{'constant': 'governed-execution.nwp-rw0-c-decision-time-source-effect-ceiling-branch-matrix.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'snapshot_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'snapshot_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_effect_ceiling_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_effect_ceiling_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'entry_count',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'cardinality': 5,
          'name': 'entries',
          'nullable': False,
          'ordering': 'exact_consuming_profile_branch_order;duplicates_rejected',
          'rule': {'child_encoded_fields': ['branch',
                                            'applicability',
                                            'governed_effect_class',
                                            'result',
                                            'reason'],
                   'child_field_equality': 'exact',
                   'child_schema_id': 'governed-execution.nwp-decision-branch-evaluation-entry.v1',
                   'child_unknown_field_behavior': 'reject_before_parent_canonicalization_or_identity_acceptance',
                   'parent_identity_protection': 'the parent matrix ref/digest pair identifies the matrix '
                                                 'and matrix_digest binds exact child order and canonical '
                                                 'bytes',
                   'parent_profile_dispatch': {'profile_digest': '41a6233d964b084cc582bfbaca6ef34e57601996a0d0fc59c77024427af700d2',
                                               'profile_ref': 'rw0-c-decision-time-source-effect-ceiling-branch.v1'},
                   'parent_source_binding': {'direct_fields': ['source_effect_ceiling_ref',
                                                               'source_effect_ceiling_digest',
                                                               'snapshot_ref',
                                                               'snapshot_digest',
                                                               'profile_ref',
                                                               'profile_digest'],
                                             'posture': 'parent_only',
                                             'proof': 'the V33 parent directly binds the exact '
                                                      'source-effect-ceiling source plus snapshot and '
                                                      'profile used by all five entries'},
                   'source_identity_posture': 'parent_only;forbidden_in_child'},
          'type': 'exact_builtin_list'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'matrix_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'matrix_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V34': [{'constant': 'governed-execution.nwp-rw0-c-recommendation-consistency-evaluation.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'snapshot_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'snapshot_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_currentness_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'proposal_currentness_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'model_recommendation', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'mapped_branch', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'authoritative_branch', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'result',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'reason',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'evaluation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'evaluation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V38': [{'constant': 'governed-execution.nwp-post-execution-validation-result-set.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'result_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_observation_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_observation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_observation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_kind',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'delivery_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'observation_kind',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_outcome', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_reason_code', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_evidence_refs',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_safe_ref',
                   'maximum': 32,
                   'minimum': 0,
                   'ordering': 'strict_lexicographic',
                   'value_equality': 'equals_exact_current_source_observation_source_evidence_refs'},
          'type': 'exact_builtin_list'},
         {'name': 'source_observed_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'program_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'program_version_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'accepted_intent_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'semantic_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_intent_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'command_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'command_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'effect_class',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'candidate_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'capsule_manifest_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'portable_capsule_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'tool_profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'tool_profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'tool_qualification_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'tool_qualification_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'tool_qualification_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'requirement_evidence_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'requirement_evidence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'requirement_evidence_safe_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'requirement_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'requirement_work_spec_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'requirement_work_spec_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'result_author_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'result_author_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'result_set_evidence_refs',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_safe_ref',
                   'maximum': 32,
                   'minimum': 0,
                   'ordering': 'strict_lexicographic',
                   'value_equality': 'independently_exact_under_governing_result_set_profile'},
          'type': 'exact_builtin_list'},
         {'name': 'result',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'repairability', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'reason',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'expires_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'result_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V39': [{'constant': 'governed-execution.nwp-post-execution-review-result-set.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'result_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_observation_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_observation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_observation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_kind',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'delivery_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'observation_kind',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_outcome', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_reason_code', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_evidence_refs',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_safe_ref',
                   'maximum': 32,
                   'minimum': 0,
                   'ordering': 'strict_lexicographic',
                   'value_equality': 'equals_exact_current_source_observation_source_evidence_refs'},
          'type': 'exact_builtin_list'},
         {'name': 'source_observed_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'program_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'program_version_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'accepted_intent_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'semantic_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_intent_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'command_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'command_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'effect_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'effect_class',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'candidate_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'capsule_manifest_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'portable_capsule_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'tool_profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'tool_profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'tool_qualification_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'tool_qualification_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'tool_qualification_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'requirement_evidence_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'requirement_evidence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'requirement_evidence_safe_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'requirement_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'requirement_work_spec_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'requirement_work_spec_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'result_author_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'result_author_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'result_set_evidence_refs',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_safe_ref',
                   'maximum': 32,
                   'minimum': 0,
                   'ordering': 'strict_lexicographic',
                   'value_equality': 'independently_exact_under_governing_result_set_profile'},
          'type': 'exact_builtin_list'},
         {'name': 'result',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'reason',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'expires_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'result_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V40': [{'constant': 'governed-execution.nwp-post-execution-reviewer-separation-evaluation.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'evaluation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'phase_basis_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'phase_basis_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'review_membership_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'review_membership_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'review_membership_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'review_value_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'review_value_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'review_value_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'review_relation_row_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'review_relation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'review_relation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'review_relation_row_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'review_relation_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'author_result_membership_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'author_result_membership_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'author_result_membership_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'author_result_value_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'author_result_value_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'author_result_value_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'author_result_relation_row_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'author_result_relation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'author_result_relation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'author_result_relation_row_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'author_result_relation_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'author_observation_locators',
          'nullable': False,
          'rule': {'count_equality': 'length_equals_exact_rank13_observation_membership_count',
                   'duplicates': 'reject',
                   'item_type': 'PostExecutionReviewerSeparationAuthorObservationLocatorV1',
                   'maximum': 3,
                   'minimum': 2,
                   'ordering': 'exact_rank13_worker_result_tuple_order'},
          'type': 'exact_builtin_list'},
         {'name': 'review_source_kind', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'review_source_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'review_source_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'author_source_kind', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'author_source_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'author_source_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'review_effect_intent_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'review_effect_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'review_effect_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'review_delivery_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'author_effect_intent_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'author_effect_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'author_effect_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'author_delivery_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'author_command_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'author_command_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'attempt_fence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'program_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'program_version_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'accepted_intent_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'work_item_revision_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'semantic_attempt_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'candidate_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'capsule_manifest_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'portable_capsule_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'support_set_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'support_set_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'status',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'reason',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'evaluation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V40.n01': [{'constant': 'governed-execution.nwp-post-execution-reviewer-separation-author-observation-locator.v1',
              'name': 'schema_id',
              'nullable': False,
              'rule': 'exact_builtin_str;displayed_literal',
              'type': 'exact_builtin_str'},
             {'name': 'ordinal',
              'nullable': False,
              'rule': '0..2;tuple_order;bool_rejected',
              'type': 'exact_builtin_int'},
             {'constant': 'governed-execution.nwp-rw0-c1-evidence-membership.v1',
              'name': 'membership_schema_id',
              'nullable': False,
              'rule': 'exact_builtin_str;displayed_literal',
              'type': 'exact_builtin_str'},
             {'name': 'membership_ref',
              'nullable': False,
              'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
              'type': 'exact_builtin_str'},
             {'name': 'membership_digest',
              'nullable': False,
              'rule': 'exact_builtin_str;64_lowercase_hex',
              'type': 'exact_builtin_str'},
             {'constant': 'governed-execution.nwp-worker-observation.v1',
              'name': 'value_schema_id',
              'nullable': False,
              'rule': 'exact_builtin_str;displayed_literal',
              'type': 'exact_builtin_str'},
             {'name': 'value_ref',
              'nullable': False,
              'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
              'type': 'exact_builtin_str'},
             {'name': 'value_digest',
              'nullable': False,
              'rule': 'exact_builtin_str;64_lowercase_hex',
              'type': 'exact_builtin_str'},
             {'constant': 'governed-execution.nwp-rw0-c1-relation-binding.v1',
              'name': 'relation_row_schema_id',
              'nullable': False,
              'rule': 'exact_builtin_str;displayed_literal',
              'type': 'exact_builtin_str'},
             {'name': 'relation_ref',
              'nullable': False,
              'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
              'type': 'exact_builtin_str'},
             {'name': 'relation_digest',
              'nullable': False,
              'rule': 'exact_builtin_str;64_lowercase_hex',
              'type': 'exact_builtin_str'},
             {'name': 'relation_row_digest',
              'nullable': False,
              'rule': 'exact_builtin_str;64_lowercase_hex',
              'type': 'exact_builtin_str'},
             {'constant': 'governed-execution.nwp-rw0-c1-c2a-worker-observation-relation.v1',
              'name': 'relation_schema_id',
              'nullable': False,
              'rule': 'exact_builtin_str;displayed_literal',
              'type': 'exact_builtin_str'},
             {'enum': ['worker'], 'name': 'source_kind', 'nullable': False, 'type': 'exact_builtin_str'},
             {'name': 'source_ref',
              'nullable': False,
              'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
              'type': 'exact_builtin_str'},
             {'name': 'source_invocation_ref',
              'nullable': False,
              'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
              'type': 'exact_builtin_str'},
             {'enum': ['worker_started', 'candidate_captured', 'worker_completed'],
              'name': 'observation_kind',
              'nullable': False,
              'type': 'exact_builtin_str'},
             {'name': 'effect_intent_ref',
              'nullable': False,
              'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
              'type': 'exact_builtin_str'},
             {'name': 'effect_fence_ref',
              'nullable': False,
              'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
              'type': 'exact_builtin_str'},
             {'name': 'effect_fence_digest',
              'nullable': False,
              'rule': 'exact_builtin_str;64_lowercase_hex',
              'type': 'exact_builtin_str'},
             {'name': 'delivery_attempt_ref',
              'nullable': False,
              'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
              'type': 'exact_builtin_str'}],
 'V41': [{'constant': 'governed-execution.nwp-post-execution-standing-policy-source-attestation.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'attestation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_owner_kind', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_owner_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_owner_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_evidence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_evidence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'policy_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'policy_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'parent_grant_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'parent_grant_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'grant_family_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'grant_family_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'audience_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'repository_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'path_scope_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'policy_status', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'revocation_status', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'allowed_branches',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_enum',
                   'maximum': 5,
                   'minimum': 1,
                   'ordering': 'canonical_branch_order',
                   'subset_of': 'current_canonical_branches'},
          'type': 'exact_builtin_list'},
         {'name': 'allowed_risk_lanes',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_safe_ref',
                   'maximum': 32,
                   'minimum': 1,
                   'ordering': 'strict_lexicographic'},
          'type': 'exact_builtin_list'},
         {'name': 'allowed_effect_classes',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_enum',
                   'maximum': 5,
                   'minimum': 0,
                   'ordering': 'canonical_effect_class_order',
                   'subset_of': 'current_effect_classes'},
          'type': 'exact_builtin_list'},
         {'name': 'max_active_invocations',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'max_candidate_bytes',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'max_changed_files',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'max_cost_microusd',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'max_cpu_seconds',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'max_deliveries',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'max_deployments',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'max_local_commits',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'max_memory_bytes',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'max_merges',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'max_model_input_tokens',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'max_model_output_tokens',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'max_pull_requests',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'max_pushes',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'max_wall_seconds',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'cardinality': 5,
          'name': 'branch_assertions',
          'nullable': False,
          'ordering': 'literal_owner_order;duplicates_rejected_when_profile_requires',
          'type': 'exact_builtin_list'},
         {'name': 'not_before', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'expires_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'attestation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V41.n01': [{'constant': 'governed-execution.nwp-post-execution-standing-policy-branch-assertion.v1',
              'name': 'schema_id',
              'nullable': False,
              'rule': 'exact_builtin_str;displayed_literal',
              'type': 'exact_builtin_str'},
             {'enum': ['candidate_acceptance',
                       'candidate_repair',
                       'attempt_selecting_replan',
                       'program_terminal_reject',
                       'post_execution_program_block'],
              'name': 'branch',
              'nullable': False,
              'type': 'exact_builtin_str'},
             {'enum': ['governed', 'halt_only'],
              'name': 'applicability',
              'nullable': False,
              'type': 'exact_builtin_str'},
             {'enum': ['author_candidate'],
              'name': 'governed_effect_class',
              'nullable': True,
              'type': 'exact_builtin_str'},
             {'enum': ['permit', 'deny', 'unknown', 'conflict'],
              'name': 'result',
              'nullable': False,
              'type': 'exact_builtin_str'},
             {'name': 'reason',
              'nullable': False,
              'rule': 'exact_builtin_str;closed_profile_reason',
              'type': 'exact_builtin_str'}],
 'V42': [{'constant': 'governed-execution.nwp-post-execution-risk-policy-attestation.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'attestation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'source_owner_kind', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_owner_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_owner_invocation_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_evidence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_evidence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'risk_policy_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'risk_policy_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'policy_status', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'revocation_status', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'allowed_risk_lanes',
          'nullable': False,
          'rule': {'duplicates': 'reject',
                   'item_type': 'exact_builtin_str_safe_ref',
                   'maximum': 32,
                   'minimum': 1,
                   'ordering': 'strict_lexicographic'},
          'type': 'exact_builtin_list'},
         {'name': 'required_risk_lane', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_profile_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'cardinality': 5,
          'name': 'branch_assertions',
          'nullable': False,
          'ordering': 'literal_owner_order;duplicates_rejected_when_profile_requires',
          'type': 'exact_builtin_list'},
         {'name': 'not_before', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'expires_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'attestation_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V42.n01': [{'constant': 'governed-execution.nwp-post-execution-risk-policy-branch-assertion.v1',
              'name': 'schema_id',
              'nullable': False,
              'rule': 'exact_builtin_str;displayed_literal',
              'type': 'exact_builtin_str'},
             {'enum': ['candidate_acceptance',
                       'candidate_repair',
                       'attempt_selecting_replan',
                       'program_terminal_reject',
                       'post_execution_program_block'],
              'name': 'branch',
              'nullable': False,
              'type': 'exact_builtin_str'},
             {'enum': ['governed', 'halt_only'],
              'name': 'applicability',
              'nullable': False,
              'type': 'exact_builtin_str'},
             {'enum': ['author_candidate'],
              'name': 'governed_effect_class',
              'nullable': True,
              'type': 'exact_builtin_str'},
             {'enum': ['permit', 'deny', 'unknown', 'conflict'],
              'name': 'result',
              'nullable': False,
              'type': 'exact_builtin_str'},
             {'name': 'reason',
              'nullable': False,
              'rule': 'exact_builtin_str;closed_profile_reason',
              'type': 'exact_builtin_str'}],
 'V43': [{'constant': 'governed-execution.nwp-post-execution-risk-source-profile.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'source_profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_family', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_system_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'adapter_profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'adapter_profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'profile_version',
          'nullable': False,
          'rule': 'bounded_by_governing_profile;bool_rejected',
          'type': 'exact_builtin_int_bool_rejected'},
         {'name': 'external_authority_claim', 'nullable': False, 'type': 'exact_builtin_bool'},
         {'name': 'source_profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}],
 'V44': [{'constant': 'governed-execution.nwp-post-execution-risk-source-binding.v1',
          'name': 'schema_id',
          'nullable': False,
          'type': 'exact_builtin_str'},
         {'name': 'source_binding_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_profile_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_profile_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_profile_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'development_work_item_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'risk_lane', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_value_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
         {'name': 'source_value_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'source_value_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'mapping_evidence_ref',
          'nullable': False,
          'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
          'type': 'exact_builtin_str'},
         {'name': 'mapping_evidence_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'},
         {'name': 'evaluated_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'expires_at',
          'nullable': False,
          'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
          'type': 'exact_builtin_str'},
         {'name': 'source_binding_digest',
          'nullable': False,
          'rule': '64_lowercase_hex',
          'type': 'exact_builtin_str'}]}
IDENTITY_SPECS = {'V01': {'reference': {'domain': 'governed-execution.nwp-section41-post-execution-semantic-review-lineage-context-reference.v1.identity',
                       'field': 'lineage_context_ref',
                       'posture': 'generated',
                       'prefix': 'section41-post-lineage.',
                       'preimage_fields': ['proposal_phase',
                                           'program_ref',
                                           'program_version_ref',
                                           'program_version_number',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'semantic_attempt_digest',
                                           'attempt_number',
                                           'candidate_ref',
                                           'basis_decision_ref',
                                           'basis_decision_digest',
                                           'work_spec_ref',
                                           'work_spec_digest',
                                           'work_spec_safe_projection_digest',
                                           'effect_intent_ref',
                                           'effect_intent_digest',
                                           'author_command_ref',
                                           'author_command_digest',
                                           'standing_grant_ref',
                                           'standing_grant_digest',
                                           'attempt_authorization_ref',
                                           'attempt_authorization_digest',
                                           'effect_authorization_ref',
                                           'effect_authorization_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'delivery_attempt_ref',
                                           'delivery_envelope_digest',
                                           'delivery_attempt_digest',
                                           'authority_evaluation_ref',
                                           'authority_evaluation_digest']},
         'digest': {'domain': 'governed-execution.nwp-section41-post-execution-semantic-review-lineage-context.v1.identity',
                    'field': 'lineage_context_digest',
                    'self_exclusion': ['lineage_context_digest']}},
 'V02': {'reference': {'domain': 'governed-execution.nwp-post-execution-semantic-review-input-context-reference.v1.identity',
                       'field': 'input_context_ref',
                       'posture': 'generated',
                       'prefix': 'post-semantic-input-context.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'proposal_phase',
                                           'lineage_context_schema_id',
                                           'lineage_context_ref',
                                           'lineage_context_digest',
                                           'phase_basis_ref',
                                           'phase_basis_digest',
                                           'preassigned_proposal_ref',
                                           'role_entry_count',
                                           'role_entries',
                                           'model_input_safe_projection_schema_id',
                                           'model_input_safe_projection_ref',
                                           'model_input_safe_projection_digest',
                                           'private_input_manifest_schema_id',
                                           'private_input_manifest_ref',
                                           'private_input_manifest_digest',
                                           'constructed_at']},
         'digest': {'domain': 'governed-execution.nwp-post-execution-semantic-review-context.v1.identity',
                    'field': 'input_context_digest',
                    'self_exclusion': ['input_context_digest']}},
 'V03': {'reference': {'posture': 'parent_bound_or_no_standalone_ref'},
         'digest': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
 'V04': {'reference': {'domain': 'governed-execution.nwp-candidate-capsule-safe-projection-reference.v1.identity',
                       'field': 'projection_ref',
                       'posture': 'generated',
                       'prefix': 'candidate-safe-projection.',
                       'preimage_fields': ['candidate_ref',
                                           'capsule_manifest_ref',
                                           'portable_capsule_digest',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'effect_intent_ref',
                                           'command_ref',
                                           'command_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'repository_ref',
                                           'base_git_object_format',
                                           'base_git_oid',
                                           'authorized_path_scope_digest']},
         'digest': {'domain': 'governed-execution.nwp-candidate-capsule-safe-projection.v1.identity',
                    'field': 'projection_digest',
                    'self_exclusion': ['projection_digest']}},
 'V05': {'reference': {'domain': 'governed-execution.nwp-post-execution-model-input-safe-projection-reference.v2.identity',
                       'field': 'projection_ref',
                       'posture': 'generated',
                       'prefix': 'post-model-input-projection-v2.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'proposal_phase',
                                           'lineage_context_schema_id',
                                           'lineage_context_ref',
                                           'lineage_context_digest',
                                           'entry_count',
                                           'entries']},
         'digest': {'domain': 'governed-execution.nwp-post-execution-model-input-safe-projection.v2.identity',
                    'field': 'projection_digest',
                    'self_exclusion': ['projection_digest']}},
 'V06': {'reference': {'posture': 'parent_bound_or_no_standalone_ref'},
         'digest': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
 'V07': {'reference': {'domain': 'governed-execution.nwp-post-execution-private-input-manifest-reference.v2.identity',
                       'field': 'manifest_ref',
                       'posture': 'generated',
                       'prefix': 'post-private-input-manifest-v2.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'proposal_phase',
                                           'lineage_context_schema_id',
                                           'lineage_context_ref',
                                           'lineage_context_digest',
                                           'entry_count',
                                           'entries']},
         'digest': {'domain': 'governed-execution.nwp-post-execution-private-input-manifest.v2.identity',
                    'field': 'manifest_digest',
                    'self_exclusion': ['manifest_digest']}},
 'V08': {'reference': {'posture': 'parent_bound_or_no_standalone_ref'},
         'digest': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
 'V09': {'reference': {'domain': 'governed-execution.nwp-post-execution-model-input-binding.v2.key',
                       'field': 'binding_ref',
                       'posture': 'generated',
                       'prefix': 'post-model-input-binding-v2.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'input_context_schema_id',
                                           'input_context_ref',
                                           'input_context_digest',
                                           'lineage_context_schema_id',
                                           'lineage_context_ref',
                                           'lineage_context_digest',
                                           'model_input_safe_projection_schema_id',
                                           'model_input_safe_projection_ref',
                                           'model_input_safe_projection_digest',
                                           'private_input_manifest_schema_id',
                                           'private_input_manifest_ref',
                                           'private_input_manifest_digest',
                                           'source_invocation_ref',
                                           'source_invocation_digest',
                                           'model_contract_ref',
                                           'model_contract_digest',
                                           'model_configuration_ref',
                                           'model_configuration_digest',
                                           'artifact_schema_id',
                                           'artifact_ref',
                                           'artifact_digest',
                                           'artifact_binding_digest',
                                           'artifact_safe_projection_schema_id',
                                           'artifact_safe_projection_digest',
                                           'proposal_ref',
                                           'proposal_digest',
                                           'evidence_set_ref',
                                           'evidence_set_digest',
                                           'source_invocation_started_at',
                                           'source_invocation_completed_at',
                                           'artifact_validated_at',
                                           'result',
                                           'reason']},
         'digest': {'domain': 'governed-execution.nwp-post-execution-model-input-binding.v2.identity',
                    'field': 'binding_digest',
                    'self_exclusion': ['binding_digest']}},
 'V10': {'reference': {'domain': 'governed-execution.nwp-post-execution-evidence-supply.v2.key',
                       'field': 'supply_ref',
                       'posture': 'generated',
                       'prefix': 'post-evidence-supply-v2.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'input_context',
                                           'model_input_safe_projection',
                                           'private_input_manifest',
                                           'role_supply_count',
                                           'role_supplies',
                                           'supply_created_at']},
         'digest': {'domain': 'governed-execution.nwp-post-execution-evidence-supply.v2.identity',
                    'field': 'supply_digest',
                    'self_exclusion': ['supply_digest']}},
 'V11': {'reference': {'posture': 'parent_bound_or_no_standalone_ref'},
         'digest': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
 'V12': {'reference': {'posture': 'parent_bound_or_no_standalone_ref'},
         'digest': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
 'V13': {'reference': {'domain': 'governed-execution.nwp-post-execution-support-set.v1.key',
                       'field': 'support_set_ref',
                       'posture': 'generated',
                       'prefix': 'post-support-set.',
                       'preimage_fields': ['profile_ref', 'profile_digest', 'entries']},
         'digest': {'domain': 'governed-execution.nwp-post-execution-support-set.v1.identity',
                    'field': 'support_set_digest',
                    'self_exclusion': ['support_set_digest']}},
 'V14': {'reference': {'domain': 'governed-execution.nwp-validation-disposition.v1.key',
                       'field': 'disposition_ref',
                       'posture': 'generated',
                       'prefix': 'validation-disposition.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'source_observation_schema_id',
                                           'source_observation_ref',
                                           'source_observation_digest',
                                           'delivery_attempt_ref',
                                           'source_kind',
                                           'source_ref',
                                           'source_invocation_ref',
                                           'observation_kind',
                                           'source_outcome',
                                           'source_reason_code',
                                           'source_evidence_refs',
                                           'source_observed_at',
                                           'author_role',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'semantic_attempt_digest',
                                           'attempt_number',
                                           'candidate_ref',
                                           'capsule_manifest_ref',
                                           'portable_capsule_digest',
                                           'command_ref',
                                           'command_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'effect_intent_ref',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'effect_class',
                                           'validation_tool_profile_ref',
                                           'validation_tool_profile_digest',
                                           'validation_tool_qualification_schema_id',
                                           'validation_tool_qualification_ref',
                                           'validation_tool_qualification_digest',
                                           'validation_requirement_schema_id',
                                           'validation_requirement_ref',
                                           'validation_requirement_safe_evidence_digest',
                                           'validation_requirement_digest',
                                           'validation_requirement_work_spec_ref',
                                           'validation_requirement_work_spec_digest',
                                           'validation_result_set_schema_id',
                                           'validation_result_set_ref',
                                           'validation_result_set_digest',
                                           'result',
                                           'reason',
                                           'repairability',
                                           'evaluated_at',
                                           'expires_at',
                                           'support_set_ref',
                                           'support_set_digest']},
         'digest': {'domain': 'governed-execution.nwp-validation-disposition.v1.identity',
                    'field': 'disposition_digest',
                    'self_exclusion': ['disposition_digest']}},
 'V15': {'reference': {'domain': 'governed-execution.nwp-independent-review-disposition.v1.key',
                       'field': 'disposition_ref',
                       'posture': 'generated',
                       'prefix': 'independent-review-disposition.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'source_observation_schema_id',
                                           'source_observation_ref',
                                           'source_observation_digest',
                                           'delivery_attempt_ref',
                                           'source_kind',
                                           'source_ref',
                                           'source_invocation_ref',
                                           'observation_kind',
                                           'source_outcome',
                                           'source_reason_code',
                                           'source_evidence_refs',
                                           'source_observed_at',
                                           'author_role',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'semantic_attempt_digest',
                                           'attempt_number',
                                           'candidate_ref',
                                           'capsule_manifest_ref',
                                           'portable_capsule_digest',
                                           'command_ref',
                                           'command_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'effect_intent_ref',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'effect_class',
                                           'review_tool_profile_ref',
                                           'review_tool_profile_digest',
                                           'review_tool_qualification_schema_id',
                                           'review_tool_qualification_ref',
                                           'review_tool_qualification_digest',
                                           'review_requirement_schema_id',
                                           'review_requirement_ref',
                                           'review_requirement_safe_evidence_digest',
                                           'review_requirement_digest',
                                           'review_requirement_work_spec_ref',
                                           'review_requirement_work_spec_digest',
                                           'review_result_set_schema_id',
                                           'review_result_set_ref',
                                           'review_result_set_digest',
                                           'reviewer_separation_schema_id',
                                           'reviewer_separation_ref',
                                           'reviewer_separation_digest',
                                           'separation_status',
                                           'result',
                                           'reason',
                                           'evaluated_at',
                                           'expires_at',
                                           'support_set_ref',
                                           'support_set_digest']},
         'digest': {'domain': 'governed-execution.nwp-independent-review-disposition.v1.identity',
                    'field': 'disposition_digest',
                    'self_exclusion': ['disposition_digest']}},
 'V16': {'reference': {'posture': 'parent_bound_no_standalone_ref'},
         'digest': {'posture': 'parent_bound_no_standalone_self_digest'}},
 'V17': {'reference': {'domain': None,
                       'field': 'matrix_ref',
                       'posture': 'supplied_not_generated',
                       'preimage_fields': None},
         'digest': {'domain': 'governed-execution.nwp-post-execution-standing-policy-branch-matrix.v1.identity',
                    'field': 'matrix_digest',
                    'self_exclusion': ['matrix_digest']}},
 'V18': {'reference': {'domain': None,
                       'field': 'matrix_ref',
                       'posture': 'supplied_not_generated',
                       'preimage_fields': None},
         'digest': {'domain': 'governed-execution.nwp-post-execution-risk-lane-branch-matrix.v1.identity',
                    'field': 'matrix_digest',
                    'self_exclusion': ['matrix_digest']}},
 'V19': {'reference': {'domain': 'governed-execution.nwp-finite-backlog-risk-source-binding.v1.key',
                       'field': 'binding_ref',
                       'posture': 'generated',
                       'prefix': 'finite-backlog-risk-binding.',
                       'preimage_fields': ['development_work_item_ref',
                                           'backlog_ref',
                                           'backlog_digest',
                                           'backlog_lease_ref',
                                           'backlog_work_item_id',
                                           'risk_lane',
                                           'mapping_author_ref',
                                           'mapping_author_digest',
                                           'mapping_evidence_ref',
                                           'mapping_evidence_digest']},
         'digest': {'domain': 'governed-execution.nwp-finite-backlog-risk-source-binding.v1.identity',
                    'field': 'binding_digest',
                    'self_exclusion': ['binding_digest']}},
 'V20': {'reference': {'domain': 'governed-execution.nwp-post-execution-global-stop-snapshot.v1.key',
                       'field': 'snapshot_ref',
                       'posture': 'generated',
                       'prefix': 'post-global-stop-snapshot.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'global_stop_schema_id',
                                           'global_stop_ref',
                                           'global_stop_version',
                                           'global_stop_state',
                                           'global_stop_stop_id',
                                           'global_stop_reason_class',
                                           'global_stop_issuer_ref',
                                           'global_stop_issued_at',
                                           'global_stop_operator_decision_ref',
                                           'global_stop_digest',
                                           'global_stop_updated_at',
                                           'evaluated_at',
                                           'support_set_ref',
                                           'support_set_digest']},
         'digest': {'domain': 'governed-execution.nwp-post-execution-global-stop-snapshot.v1.identity',
                    'field': 'snapshot_digest',
                    'self_exclusion': ['snapshot_digest']}},
 'V21': {'reference': {'domain': 'governed-execution.nwp-post-execution-source-effect-ceiling-evidence.v1.key',
                       'field': 'evidence_ref',
                       'posture': 'generated',
                       'prefix': 'post-source-effect-ceiling.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'proposal_phase',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'candidate_ref',
                                           'effect_intent_ref',
                                           'repository_ref',
                                           'base_git_object_format',
                                           'base_git_oid',
                                           'source_effect_class',
                                           'source_effect_ceilings',
                                           'path_scope_digest',
                                           'attempt_fence_schema_id',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'attempt_allowed_effect_classes',
                                           'attempt_ceilings',
                                           'attempt_fence_expires_at',
                                           'effect_fence_schema_id',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'effect_fence_class',
                                           'effect_ceilings',
                                           'effect_fence_expires_at',
                                           'authority_schema_id',
                                           'authority_observation_ref',
                                           'authority_observation_digest',
                                           'authority_status',
                                           'authority_family_status',
                                           'authority_revocation_status',
                                           'authority_allowed_effect_classes',
                                           'authority_ceilings',
                                           'authority_grant_expires_at',
                                           'authority_observation_expires_at',
                                           'evaluated_at',
                                           'result',
                                           'reason',
                                           'support_set_ref',
                                           'support_set_digest']},
         'digest': {'domain': 'governed-execution.nwp-post-execution-source-effect-ceiling-evidence.v1.identity',
                    'field': 'evidence_digest',
                    'self_exclusion': ['evidence_digest']}},
 'V22': {'reference': {'domain': 'governed-execution.nwp-section41-post-execution-proposal-family-projection-reference.v2.identity',
                       'field': 'projection_ref',
                       'posture': 'generated',
                       'prefix': 'section41-post-projection-v2.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'proposal_ref',
                                           'proposal_digest',
                                           'input_context_schema_id',
                                           'input_context_ref',
                                           'input_context_digest',
                                           'lineage_context_schema_id',
                                           'lineage_context_ref',
                                           'lineage_context_digest',
                                           'evidence_set_ref',
                                           'evidence_set_digest',
                                           'owner_family_graph_digest']},
         'digest': {'domain': 'governed-execution.nwp-section41-post-execution-proposal-family-projection.v2.identity',
                    'field': 'projection_digest',
                    'self_exclusion': ['projection_digest']}},
 'V23': {'reference': {'posture': 'parent_bound_or_no_standalone_ref'},
         'digest': {'domain': 'governed-execution.nwp-section41-post-execution-projection-evidence-entry.v2.identity',
                    'field': 'projection_evidence_entry_digest',
                    'self_exclusion': ['projection_evidence_entry_digest']}},
 'V24': {'reference': {'domain': 'governed-execution.nwp-section41-post-execution-role-resolution-reference.v3.identity',
                       'field': 'relation_ref',
                       'posture': 'generated',
                       'prefix': 'section41-role-relation-v3.',
                       'preimage_fields': ['context_role',
                                           'context_role_entry_schema_id',
                                           'context_role_ordinal',
                                           'context_role_rank',
                                           'decision_currentness_profile_digest',
                                           'decision_currentness_profile_ref',
                                           'direct_c1_kind',
                                           'direct_c1_kind_rank',
                                           'direct_c1_membership_digest',
                                           'direct_c1_membership_ref',
                                           'evidence_binding_digest',
                                           'evidence_bound_at',
                                           'evidence_locator_ordinal',
                                           'evidence_locator_proposal_ref',
                                           'evidence_locator_role',
                                           'evidence_set_digest',
                                           'evidence_set_ref',
                                           'input_context_digest',
                                           'input_context_ref',
                                           'input_context_schema_id',
                                           'lineage_context_digest',
                                           'lineage_context_ref',
                                           'lineage_context_schema_id',
                                           'model_input_posture',
                                           'profile_digest',
                                           'profile_ref',
                                           'projection_digest',
                                           'projection_ref',
                                           'projection_schema_id',
                                           'proposal_digest',
                                           'proposal_ref',
                                           'reason',
                                           'resolution_posture',
                                           'result',
                                           'section41_membership_digest',
                                           'section41_membership_ref',
                                           'section41_value_digest',
                                           'section41_value_ref',
                                           'source_binding_digest',
                                           'source_binding_ref',
                                           'source_binding_schema_id',
                                           'source_invocation_digest',
                                           'source_invocation_ref',
                                           'source_posture',
                                           'source_profile_digest',
                                           'source_profile_ref',
                                           'typed_schema_id',
                                           'typed_value_digest',
                                           'typed_value_ref']},
         'digest': {'domain': 'governed-execution.nwp-section41-post-execution-role-resolution.v3.identity',
                    'field': 'relation_digest',
                    'self_exclusion': ['relation_digest']}},
 'V25': {'reference': {'domain': 'governed-execution.nwp-rw0-c-decision-membership-closure.v1.key',
                       'field': 'closure_ref',
                       'posture': 'generated',
                       'prefix': 'rw0-c-membership-closure.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'phase_basis_ref',
                                           'phase_basis_digest',
                                           'entry_count',
                                           'entries',
                                           'captured_at']},
         'digest': {'domain': 'governed-execution.nwp-rw0-c-decision-membership-closure.v1.identity',
                    'field': 'closure_digest',
                    'self_exclusion': ['closure_digest']}},
 'V26': {'reference': {'posture': 'parent_bound_or_no_standalone_ref'},
         'digest': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
 'V27': {'reference': {'domain': 'governed-execution.nwp-rw0-c-decision-current-snapshot.v1.key',
                       'field': 'snapshot_ref',
                       'posture': 'generated',
                       'prefix': 'rw0-c-current-snapshot.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'candidate_ref',
                                           'phase_basis_ref',
                                           'phase_basis_digest',
                                           'membership_closure_ref',
                                           'membership_closure_digest',
                                           'selected_authority_membership_ref',
                                           'selected_authority_membership_digest',
                                           'selected_section41_membership_ref',
                                           'selected_section41_membership_digest',
                                           'global_stop_ref',
                                           'global_stop_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'external_source_count',
                                           'external_sources',
                                           'captured_at']},
         'digest': {'domain': 'governed-execution.nwp-rw0-c-decision-current-snapshot.v1.identity',
                    'field': 'snapshot_digest',
                    'self_exclusion': ['snapshot_digest']}},
 'V28': {'reference': {'posture': 'parent_bound_or_no_standalone_ref'},
         'digest': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
 'V29': {'reference': {'domain': 'governed-execution.nwp-rw0-c-proposal-evidence-currentness.v1.key',
                       'field': 'currentness_ref',
                       'posture': 'generated',
                       'prefix': 'rw0-c-proposal-currentness.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'proposal_ref',
                                           'proposal_digest',
                                           'snapshot_ref',
                                           'snapshot_digest',
                                           'component_count',
                                           'components',
                                           'result',
                                           'reason',
                                           'evaluated_at']},
         'digest': {'domain': 'governed-execution.nwp-rw0-c-proposal-evidence-currentness.v1.identity',
                    'field': 'currentness_digest',
                    'self_exclusion': ['currentness_digest']}},
 'V30': {'reference': {'posture': 'parent_bound_or_no_standalone_ref'},
         'digest': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
 'V31': {'reference': {'domain': 'governed-execution.nwp-rw0-c-decision-time-authority-branch-matrix.v1.key',
                       'field': 'matrix_ref',
                       'posture': 'generated',
                       'prefix': 'rw0-c-authority-matrix.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'snapshot_ref',
                                           'snapshot_digest',
                                           'proposal_ref',
                                           'proposal_digest',
                                           'entry_count',
                                           'entries',
                                           'evaluated_at']},
         'digest': {'domain': 'governed-execution.nwp-rw0-c-decision-time-authority-branch-matrix.v1.identity',
                    'field': 'matrix_digest',
                    'self_exclusion': ['matrix_digest']}},
 'V32': {'reference': {'domain': 'governed-execution.nwp-rw0-c-decision-time-global-stop-branch-matrix.v1.key',
                       'field': 'matrix_ref',
                       'posture': 'generated',
                       'prefix': 'rw0-c-global-stop-matrix.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'snapshot_ref',
                                           'snapshot_digest',
                                           'global_stop_ref',
                                           'global_stop_digest',
                                           'entry_count',
                                           'entries',
                                           'evaluated_at']},
         'digest': {'domain': 'governed-execution.nwp-rw0-c-decision-time-global-stop-branch-matrix.v1.identity',
                    'field': 'matrix_digest',
                    'self_exclusion': ['matrix_digest']}},
 'V33': {'reference': {'domain': 'governed-execution.nwp-rw0-c-decision-time-source-effect-ceiling-branch-matrix.v1.key',
                       'field': 'matrix_ref',
                       'posture': 'generated',
                       'prefix': 'rw0-c-ceiling-matrix.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'snapshot_ref',
                                           'snapshot_digest',
                                           'source_effect_ceiling_ref',
                                           'source_effect_ceiling_digest',
                                           'entry_count',
                                           'entries',
                                           'evaluated_at']},
         'digest': {'domain': 'governed-execution.nwp-rw0-c-decision-time-source-effect-ceiling-branch-matrix.v1.identity',
                    'field': 'matrix_digest',
                    'self_exclusion': ['matrix_digest']}},
 'V34': {'reference': {'domain': 'governed-execution.nwp-rw0-c-recommendation-consistency-evaluation.v1.key',
                       'field': 'evaluation_ref',
                       'posture': 'generated',
                       'prefix': 'rw0-c-recommendation-consistency.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'proposal_ref',
                                           'proposal_digest',
                                           'snapshot_ref',
                                           'snapshot_digest',
                                           'proposal_currentness_ref',
                                           'proposal_currentness_digest',
                                           'model_recommendation',
                                           'mapped_branch',
                                           'authoritative_branch',
                                           'result',
                                           'reason',
                                           'evaluated_at']},
         'digest': {'domain': 'governed-execution.nwp-rw0-c-recommendation-consistency-evaluation.v1.identity',
                    'field': 'evaluation_digest',
                    'self_exclusion': ['evaluation_digest']}},
 'V38': {'reference': {'domain': 'governed-execution.nwp-post-execution-validation-result-set.v1.key',
                       'field': 'result_set_ref',
                       'posture': 'generated_and_owner_supplied_for_revalidation',
                       'prefix': 'post-validation-result-set.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'source_observation_schema_id',
                                           'source_observation_ref',
                                           'source_observation_digest',
                                           'source_kind',
                                           'source_ref',
                                           'source_invocation_ref',
                                           'delivery_attempt_ref',
                                           'observation_kind',
                                           'source_outcome',
                                           'source_reason_code',
                                           'source_evidence_refs',
                                           'source_observed_at',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'effect_intent_ref',
                                           'command_ref',
                                           'command_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'effect_class',
                                           'candidate_ref',
                                           'capsule_manifest_ref',
                                           'portable_capsule_digest',
                                           'tool_profile_ref',
                                           'tool_profile_digest',
                                           'tool_qualification_schema_id',
                                           'tool_qualification_ref',
                                           'tool_qualification_digest',
                                           'requirement_evidence_schema_id',
                                           'requirement_evidence_ref',
                                           'requirement_evidence_safe_digest',
                                           'requirement_digest',
                                           'requirement_work_spec_ref',
                                           'requirement_work_spec_digest',
                                           'result_author_ref',
                                           'result_author_invocation_ref',
                                           'result_set_evidence_refs',
                                           'result',
                                           'repairability',
                                           'reason',
                                           'evaluated_at',
                                           'expires_at']},
         'digest': {'algorithm': 'sha256',
                    'domain': 'governed-execution.nwp-post-execution-validation-result-set.v1.identity',
                    'domain_separator': 'NUL',
                    'field': 'result_set_digest',
                    'self_exclusion': ['result_set_digest']}},
 'V39': {'reference': {'domain': 'governed-execution.nwp-post-execution-review-result-set.v1.key',
                       'field': 'result_set_ref',
                       'posture': 'generated_and_owner_supplied_for_revalidation',
                       'prefix': 'post-review-result-set.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'source_observation_schema_id',
                                           'source_observation_ref',
                                           'source_observation_digest',
                                           'source_kind',
                                           'source_ref',
                                           'source_invocation_ref',
                                           'delivery_attempt_ref',
                                           'observation_kind',
                                           'source_outcome',
                                           'source_reason_code',
                                           'source_evidence_refs',
                                           'source_observed_at',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'effect_intent_ref',
                                           'command_ref',
                                           'command_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'effect_class',
                                           'candidate_ref',
                                           'capsule_manifest_ref',
                                           'portable_capsule_digest',
                                           'tool_profile_ref',
                                           'tool_profile_digest',
                                           'tool_qualification_schema_id',
                                           'tool_qualification_ref',
                                           'tool_qualification_digest',
                                           'requirement_evidence_schema_id',
                                           'requirement_evidence_ref',
                                           'requirement_evidence_safe_digest',
                                           'requirement_digest',
                                           'requirement_work_spec_ref',
                                           'requirement_work_spec_digest',
                                           'result_author_ref',
                                           'result_author_invocation_ref',
                                           'result_set_evidence_refs',
                                           'result',
                                           'reason',
                                           'evaluated_at',
                                           'expires_at']},
         'digest': {'algorithm': 'sha256',
                    'domain': 'governed-execution.nwp-post-execution-review-result-set.v1.identity',
                    'domain_separator': 'NUL',
                    'field': 'result_set_digest',
                    'self_exclusion': ['result_set_digest']}},
 'V40': {'reference': {'domain': 'governed-execution.nwp-post-execution-reviewer-separation-evaluation.v1.key',
                       'field': 'evaluation_ref',
                       'posture': 'generated',
                       'prefix': 'post-reviewer-separation-evaluation.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'phase_basis_ref',
                                           'phase_basis_digest',
                                           'review_membership_schema_id',
                                           'review_membership_ref',
                                           'review_membership_digest',
                                           'review_value_schema_id',
                                           'review_value_ref',
                                           'review_value_digest',
                                           'review_relation_row_schema_id',
                                           'review_relation_ref',
                                           'review_relation_digest',
                                           'review_relation_row_digest',
                                           'review_relation_schema_id',
                                           'author_result_membership_schema_id',
                                           'author_result_membership_ref',
                                           'author_result_membership_digest',
                                           'author_result_value_schema_id',
                                           'author_result_value_ref',
                                           'author_result_value_digest',
                                           'author_result_relation_row_schema_id',
                                           'author_result_relation_ref',
                                           'author_result_relation_digest',
                                           'author_result_relation_row_digest',
                                           'author_result_relation_schema_id',
                                           'author_observation_locators',
                                           'review_source_kind',
                                           'review_source_ref',
                                           'review_source_invocation_ref',
                                           'author_source_kind',
                                           'author_source_ref',
                                           'author_source_invocation_ref',
                                           'review_effect_intent_ref',
                                           'review_effect_fence_ref',
                                           'review_effect_fence_digest',
                                           'review_delivery_attempt_ref',
                                           'author_effect_intent_ref',
                                           'author_effect_fence_ref',
                                           'author_effect_fence_digest',
                                           'author_delivery_attempt_ref',
                                           'author_command_ref',
                                           'author_command_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'candidate_ref',
                                           'capsule_manifest_ref',
                                           'portable_capsule_digest',
                                           'support_set_ref',
                                           'support_set_digest',
                                           'status',
                                           'reason',
                                           'evaluated_at']},
         'digest': {'algorithm': 'sha256',
                    'domain': 'governed-execution.nwp-post-execution-reviewer-separation-evaluation.v1.identity',
                    'domain_separator': 'NUL',
                    'field': 'evaluation_digest',
                    'self_exclusion': ['evaluation_digest']}},
 'V40.n01': {'reference': {'posture': 'parent_bound_no_standalone_ref'},
             'digest': {'posture': 'parent_bound_no_standalone_self_digest'}},
 'V41': {'reference': {'domain': None,
                       'field': 'attestation_ref',
                       'posture': 'supplied_not_generated',
                       'preimage_fields': None},
         'digest': {'algorithm': 'sha256',
                    'domain': 'governed-execution.nwp-post-execution-standing-policy-source-attestation.v1.identity',
                    'domain_separator': 'NUL',
                    'field': 'attestation_digest',
                    'self_exclusion': ['attestation_digest']}},
 'V41.n01': {'reference': {'posture': 'parent_bound_no_standalone_ref'},
             'digest': {'posture': 'parent_bound_no_standalone_self_digest'}},
 'V42': {'reference': {'domain': None,
                       'field': 'attestation_ref',
                       'posture': 'supplied_not_generated',
                       'preimage_fields': None},
         'digest': {'algorithm': 'sha256',
                    'domain': 'governed-execution.nwp-post-execution-risk-policy-attestation.v1.identity',
                    'domain_separator': 'NUL',
                    'field': 'attestation_digest',
                    'self_exclusion': ['attestation_digest']}},
 'V42.n01': {'reference': {'posture': 'parent_bound_no_standalone_ref'},
             'digest': {'posture': 'parent_bound_no_standalone_self_digest'}},
 'V43': {'reference': {'domain': 'governed-execution.nwp-post-execution-risk-source-profile.v1.key',
                       'field': 'source_profile_ref',
                       'posture': 'generated',
                       'prefix': 'post-risk-source-profile.',
                       'preimage_fields': ['source_family',
                                           'source_system_schema_id',
                                           'adapter_profile_ref',
                                           'adapter_profile_digest',
                                           'profile_version',
                                           'external_authority_claim']},
         'digest': {'algorithm': 'sha256',
                    'domain': 'governed-execution.nwp-post-execution-risk-source-profile.v1.identity',
                    'domain_separator': 'NUL',
                    'field': 'source_profile_digest',
                    'self_exclusion': ['source_profile_digest']}},
 'V44': {'reference': {'domain': 'governed-execution.nwp-post-execution-risk-source-binding.v1.key',
                       'field': 'source_binding_ref',
                       'posture': 'generated',
                       'prefix': 'post-risk-source-binding.',
                       'preimage_fields': ['source_profile_schema_id',
                                           'source_profile_ref',
                                           'source_profile_digest',
                                           'development_work_item_ref',
                                           'risk_lane',
                                           'source_value_schema_id',
                                           'source_value_ref',
                                           'source_value_digest',
                                           'mapping_evidence_ref',
                                           'mapping_evidence_digest',
                                           'evaluated_at',
                                           'expires_at']},
         'digest': {'algorithm': 'sha256',
                    'domain': 'governed-execution.nwp-post-execution-risk-source-binding.v1.identity',
                    'domain_separator': 'NUL',
                    'field': 'source_binding_digest',
                    'self_exclusion': ['source_binding_digest']}}}
PROFILE_PAIRS = {'finite_backlog_risk_source.v1': '2ea8aa75234deb0901d3ca0a32d19877da072378e1acd438c901ce5cf1e489bc',
 'independent-review-disposition.v1': 'c5a87ab332790e95f4cd0fb4790149115e8b15a5e4cd0786272cc535b1b23a78',
 'post-execution-evidence-supply.v2': '59a4a741fb394767f341dc57c514bb3e022737196905c7bed1f05295376d3a02',
 'post-execution-global-stop.v1': '5f2be30f5f081f5c159596375ba872bc08e012e389706b084a79b21baaab9142',
 'post-execution-model-input-binding.v2': '1bbc54604228066b13aa6cbed7cb98b1962a2a4f63920938cf9e824faf253bbb',
 'post-execution-review-result-set.v1': '2dd40a8e0c3628f9e0e3860acc29c0ee908111ce14c7e8dccf944e4b1e9d9730',
 'post-execution-reviewer-separation-evaluation.v1': '477867ca6eecb36bd77629452489637ef43af2d79c97ffb72b5cce0969d80a2f',
 'post-execution-risk-lane-matrix.v1': '436ba40a1386d2843bc890767920a7c1cebae96e8c7fa0ed86ef16022c46e502',
 'post-execution-risk-policy-attestation.v1': '861f58f9b8b747ca169c27cf86565e7e3e5a7eebdfd6113944f71ff9151b6174',
 'post-execution-risk-source-binding.v1': 'c4982a13fe91d7af98e87eab7b67d8f9c45b390c82e0232905a53d25dde48471',
 'post-execution-risk-source-profile.v1': '1c82ba782f69f24d0e4be84cab71db04f61bedd40f74a3f602c160a408bbca4a',
 'post-execution-semantic-review-input.v2': 'd4693a9cd9beb9d58edf2e492176182b69b5ed2fa8da34419709e2392333e54e',
 'post-execution-source-effect-ceiling.v1': '6aa721b81b9b341e0e5b3ce3bc10590641dd4d4f50c056ae65e8dc4b605eff1a',
 'post-execution-standing-policy-matrix.v1': 'd0c25cc85f015d222d1fa9ef14d375fe68f16f17283326a9df7d5605cdc9c539',
 'post-execution-standing-policy-source-attestation.v1': 'a68f350c418edfe7477cdd8b6b5a709974deff058f382919169154fcbaa7fd12',
 'post-execution-support-set.v1': 'dc2428d307d9ebb5bcff78fa494a70339a7a57a330a2a8c8fce284f971b8ab52',
 'post-execution-validation-result-set.v1': 'cff49323050cd70855d7fda9b8bcc2666da18a7a3f30f8d8e030a9d60b087d58',
 'rw0-c-decision-current-snapshot.v1': '8bc6f746c2b071f9295c171c9e0caacddda4f61f4d0dfde571bbebb46e0da7dc',
 'rw0-c-decision-membership-closure.v1': 'db06318a51022ccec345e29a66008e96dd8cf81231bdb8055167960efce07928',
 'rw0-c-decision-time-authority-branch.v1': '07384a871dd87a8387c97bb1cd60e6cc8207333428e04e7766044ec8567677dc',
 'rw0-c-decision-time-global-stop-branch.v1': '6139df3c64d3736e6938605bc6abef22c258e4841ffe8b641d7a70490f6a5e47',
 'rw0-c-decision-time-source-effect-ceiling-branch.v1': '41a6233d964b084cc582bfbaca6ef34e57601996a0d0fc59c77024427af700d2',
 'rw0-c-proposal-evidence-currentness.v1': '88b347a069c92a5804ba53dad4f39a9d7ba6a36413fa38812f81e964a8902e9b',
 'rw0-c-recommendation-consistency.v1': 'b85aba9ee6564d53dcb075c5bb60e33a3b923a504c9b38046f2f96aa28f05ebd',
 'rw0-wire-nwpf-v1': '470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454',
 'section41-post-execution-proposal-family-projection.v2': '76b0fdedd0fbbd3c6400be3f8e22eacdf585eb28280d12f38834d513b8cdb411',
 'section41-post-execution-role-resolution.v3': '008a8468c608d9db41fe28f19bc582cc9598f58c9b3009e2d79322fd6c22cebc',
 'validation-disposition.v1': '65a2af00efe0fd6d83cafe5c713536c12e71814544c342d907ef62a2f3cb4048'}
NESTED = {'V02': {'role_entries': 'V03'},
 'V05': {'entries': 'V06'},
 'V07': {'entries': 'V08'},
 'V10': {'input_context': 'V02',
         'model_input_safe_projection': 'V05',
         'private_input_manifest': 'V07',
         'role_supplies': 'V11'},
 'V13': {'entries': 'V12'},
 'V17': {'entries': 'V16'},
 'V18': {'entries': 'V16'},
 'V22': {'evidence_bindings': 'V23'},
 'V25': {'entries': 'V26'},
 'V27': {'external_sources': 'V28'},
 'V29': {'components': 'V30'},
 'V31': {'entries': 'V16'},
 'V32': {'entries': 'V16'},
 'V33': {'entries': 'V16'},
 'V40': {'author_observation_locators': 'V40.n01'},
 'V41': {'branch_assertions': 'V41.n01'},
 'V42': {'branch_assertions': 'V42.n01'}}

MODULES = {
    "_post_execution_evidence_values": evidence,
    "_post_execution_policy_values": policy,
    "_finite_backlog_risk_source_adapter": adapter,
    "_section41_post_execution_proposal_family_projection": projection,
    "_section41_post_execution_role_resolution": resolution,
    "_rw0_c_decision_input_values": decision,
}
CLASS_BY_V = {
    v_number: getattr(MODULES[module_name], symbol)
    for v_number, (module_name, symbol, _) in VALUE_INVENTORY.items()
}

# Fixed, test-owned V11 responsibility fixtures.  The compressed literal keeps
# the repository tests independent of the external audit package at runtime.
_TEST_RECORD_B85 = (
    b'c-'
    b'ri}`*Y(+av=P#F!a+of|T$gKx*tCX4h+<@78PIj@=ud#~lbf3KHBT!6itkwG;Edf0^|zpa6mt#TI&W8@_3Q^~}o5%FN2gFE>eDA9'
    b'l$mBey>~j(c<ei~16m`OW<e{XD(NlA6F@<caKFCfQ-PBb)u?ljF`l1;K=DvMML}WSwlc<>q0sBmYCPeLXpBzHF-'
    b'J&7>&FDz7KWCZDhYwh8v1ZAiU`ZcoYTKqh4k{b1y}d?KqC{8;7*{+yDc+7aGoQs(ggm;0AVl4WGO$A!Z3$k#2*NN~Yya`?6-'
    b'yLGaG)^VLxTU>osZT7n)+fSaLMYWq$o7Kw?lT9@tUt#8bS#2ipm3-Zk-6mO0lEeP7+QD2fm|R+%t&(zG-`xLv^T`b-'
    b'$!b+S*U$%sg;l2rxyR`Q0I@2wBrR9aeL8ulVA~s#$D}A=Y8<1kr?B7pu-'
    b'Z>4V0I*_s}0PAqY3~Dz}DF#StoEH0vK7csWvdds{C7m>+b4T9d>Y#J5rq2F)ttBh<f^34ziX<XPl>bint;GH6LF)%FolAJ$#A*ZO'
    b'E>EEVpoM)h;hL$?hdC%1yZ^aSgBl9LQpTTPzn9vqO!s`^~RY6SF-#W_t>=^8-'
    b'CGSoQz;>EHe|`9famNx7LMyM0+8%B;!_!6k2#msOSI*TA{A0EBM`gs%VrqsXDeZsY%9xH-'
    b'x#2lg!oYRi0=lk^3Se?>MA`^U+;tk=mtdmQVo=k{IC+q>Q+&y%12_m4Ag9*%z3p?%k(M(5Q!DL1p404Ji?3+F*&-+5%;d8F-}Y--'
    b'ArVK!iGIr%zyNVa3$@4~*{g^i>0J^#x;j&-'
    b'w3`(~GFvoK^?ARfbPWJhqbH7@ZnsUP7=9yxZqjuim#SponTjFLt2@USBfc<N){vt1f@HEBFsRW+#&`$<+EHv93PvRz7ZH7O0ohIM'
    b'SnGZn|SAV9-*#=2d*Eaqym*nj@VKg|}C-~HRaj(w|k8O+sWus<b#!W9)DlI$n@>I)gGyy@B{FISViV4R$3NcCgl-UZI=5iVn@Lz<'
    b'griqRN0Z5O=Uuw&CGYr^uLch%-'
    b'$@?7To(ef<2+~sO=*N*)4Q0~YYZ>Ksbh>$o(ecpEQ%hkj$vQ9~kwgi3ueCvlAz9+Rb=8X05?Q)r`$z|}v7dMa=vj+n6ml?ohMNKF'
    b'j5Eu;}cy__e(*(0}^91WhJm8=}+gDkXWT&98tDZ-S0-jw;^E4@KTY(z#GNJQMl0A;XcHPMU;^z_;eb~pKxa<ft-aN!&L-'
    b'Cq`sK0p_18nT_oTtfiyR!cBTZD{V^z$^)PjU)`P`Tb#I}q@bJlVnu8<5#$kFbnvf7p@usjODgIQ!nAV3!I#O)C7o_v78~+`Hd-cf'
    b'WTf6t=r+Tj33|uJXf*d@s<j%Z=V#mn5D_^309%lP~3l*>SdHgSSY`er}@2r@)DEr{(5A#sCJpB<X3ABwK+2hUaScW$YWbOOjsHI)'
    b'AuPtBf(qyetY>!=%_%Ygj+wi`1I5VIoYQV}OZW%=8w0FadEhS=B=zv8nc>f`(n(^mH@eVYM%}D+?Y7NwXxil}ri{QpO-'
    b'~`F4rZcUmaH-dZR4^twv65+T^<(IbOz7d(Bp1&5rhO8V;FgoOBE{IIYKn!eY9#jaYBJB}Ds5n(2XaZ`j{nDqVDjrm>f-'
    b'Y!J?`t$Ctde|lFI}{S`P|a9x_jg&fUZdYdeMoCyiwFA+F(yFR<wxIUcf8Ah4S?wU9qryOHu{>_xGw7&y^~Dw5%>aJj7=vZ+&%YR8'
    b'pG!8qNA^gj)%>T)Ya+<?QX{fqY-'
    b'W0E+P7wgjgqQGTT1FACom2CF$gM()MJ3G#eZG+eJfP6AkkcD18G9emubFcfb@8^LKYiMqdvn)UVBEg#&D;4_j2dNgj(<?;Rk4T}%'
    b'u#F|pp`<wtgt;(*2i&9hLmMD5Ya#EjLSXy-'
    b'O~xN{yzQuR124S`*B3^dUZ_Bs&);AFcxpl>D>ptjJBG`!zFx${_lfA^cW%Zh<#ZeDS~#zy%M(%2&8WZ1@t*k)jt83W&hLPHN|fFe'
    b'!mvX)$uLxk!Muw@34WVL!3lO_?^rO6;L;iBCPLttWJ$%w9%z%Ek;noJ2NJgLjC;*}2tYI;`y``Fi`e&Y=6B4rSoo8O=(3Tjq#=c|'
    b'&8eAjkaGSFnnq=2PN(L0(tn@uMY40Pj@ZB_4QYVktC##g?YULceGBau&{@D=F^ZsP+kN*ir|*sh4B$97jfQMW$m3D+}Q0;qDdO|^'
    b'zj@T2R^Rw&=1Pf4;aS1;`9GDo88o$=qP6o_M?XhbIe;ohyQoUHDC0${;D0{0I6_2GzLn2B+`ueO0*Xbu*-'
    b'&dgw}yf)G*N8C<Q^h06>XX?!W(E1++p|L{4E;|QHT~tgMeZ#Z_eHx^!SRM8?{4rUP{Gs^(F`7s0xm{SEYr^s;e?I%<M^tP4!sKB|'
    b'z@R;pYikrvj4>ZD!ahzx$H)_EYkc?6u#3lY{Yf9TQ0@U3u%hjba0P*_Hc6%VeY~D6bGwv0H(fDHWD805WmP>em!6coRKSS&GxbC}'
    b'^icxAE+o%2Az9Esy-Bw9W3`{GIRZSwy##Q0!j39xt6Brvn9$Hf#SEYZis%?1V;7U>nwZSZYlltpl$0w*6nnulHUzG8g5hEo1C-'
    b'FPHdUOHtQ?6_J-'
    b'3U>b4^r!SXC)3q~2HC39P#WAp_l6WON{p9yFl=7tJV`rd?Q`Yr=9tg+SOEstM!Vq+K?i8&C8|<OJAW`+Z)lE}=(nJM40Ul5kn?nX'
    b'C7^hlgE`oa<hoVkyWNaedVANH*C14xb-Iv}lVB=$<XfAunO^u-'
    b'P|<N^9EIrtRY5e0iMEACuL7hKsWvJ`*ZNaO|O7TnrtHV!SRNnAv0IIF8@18Y1m*J&?hRsgv@KC97h_9Ej_8p=$7j#jyBT(_kqenO'
    b'@opMZ1_8>hV1mWtMBBlfZ2Pvs=xT3Nu|4i^I2QzV8aCe9Z!o2vfS|n60@NvUcG$^mL!xx}<a|L)0f22G7IUsoaWT3R^;fm6!DvK?'
    b'KCStEl9nXF<TDKdkX(k#&bzM2DC;KUW|E-'
    b'~ar}jcggyNO@{9#JdAnVo|O{xINy7PUg+CY%wn!cb<Emm%Bx>B!wH~el#ygxG3DPa3gQw`(BtV^CHUUp)=3&Y?;mJtB)9SM+&xI4'
    b'OM2K&w^UNd6+TZ<QX8quKarY<N_$|%Usx&8TetE1Ww}mi!k>VfuClJr4xnG(sPn1b2E}AWEql078Qv@@<j++2p!MMf{@H<^nLF#('
    b'f4(>0^B>kK<f9>TA&m8iy&D<Zk{iqWZ^HOY#F7go8_THLIAJ_Eqp)l7Q_ii6osJ^1O(t7!X~0TYb|j1?98&65KCvM_s%4G&lp$lT'
    b'cu}PW$5~Ff_@g_>G~lFmjF*^o@QYJiUUB)n=eSP2wadQ7HJr`d6Yy>uyl$rnUf$Iv`Tg-&G1eduuk84+-'
    b'?$jzMn6{Aaxc&mdzJlT7UwWz`6PXnMa}HE|+2A<W7;zmsu1!UJ!UuQbdlEdxO@=^oAMpQki9>Tp^xnEB@TUr6}#iJaI)@Qv9xw5q'
    b'x4XIys1)$UbN;5=`I0a9{M0DK>B{;}=|O^BaeWoE9!Q>VR7`KgovdPtLqpL*tWdh(ZV6iM-'
    b'K{P+kQrL=L}yWSm&_K|+a<P~hKug*?+pp$%pGMGj&9NWFtF83$4%>ZJE#TS5riRTUl~UNZn-'
    b'k=Fy^&h8!_^}y9Ymf>VYpHk_zrxUSHOoJk}IGy0`rqt=3*>pJ`Fx?@m*lht!pW7Q=sI|C2{teUb(7Ex~DP>o-'
    b'6Q^Jj2dSO6{+&Zz`_crFz+rua#!m*k8+0VUa~!peBYrZ*5g)CmE}mav^>Og&E!w9?qYl{qr!r`XpC#YVRQ%1?#nadbmOcEim?vZF'
    b'u!KoP073kzNRNgAfT+spLj0*W&`zUq3<IIl5J82Rhd~PCuhDaW`jL?p<w@!~(7a7(_L$^>{J=<quN1&uGHFcp;j2{d7}(*kDgS!V'
    b'jEWQb%7_BWt^=+byr?h}<9HPcaTK;{Wij6a2a@Fng|>W$v0O*2HRq?)+eUz%p1Nl}b#_g~cuff|seMsv8GszGK6_ZBpbWN7RNN$q'
    b'FwD@dRY@P{E+H`mk5?ROKN<LTGBEivyAQ1lUHo=!Ao)juWWCd01Fl~$td$6LfX0jLDr6~`F$8!rL&|CeYU(ZAbGM+DteHhyeq2~S'
    b'`mXJxXaC4d1Qdt#AAH&Rv$jH(CoD$az4WlcUzLa>42d%6FlIId<OgVbVCQ$Q{w=OJ^w|(8%T`3YLbVa)#d35|+R`#4WAxgPib=pH'
    b'3<=GJ`qw$O>SCKfz_Kxq&O&&DuJLIbxRA3i(36jutw^%#8It`zd_=!7mPy8F`6xG159ZX;4Q)a8O?dojPg=(l@a=#czfzCDhlx<Z'
    b'sS2Duma81o#>kv@NXNyl`Wx9$Dx6W?Bs0Z*Aus6afwlvt6*shDV<<|+bO!hd9SBO{BO-~Ox)i`@be1XqasRRfdE-cOJ;`6XlIv-'
    b'v#z~bSXnM2KY33+yoJ_LE_Wp#fPjrqac0+IYRY|ksJ(8W0&(#YuT;$B&Kn;VK{Nj-'
    b')O9D_f6_69^TLV<7|K+>JU*3#jV&fY_cmW6b1GU9bmeP^1k6Pfg9d$FHDZL2xk2?a_!Sc_J<6<Zp;1{rCjx8HZ$wTMb5zN2E2W4v'
    b'l3V}1g<ZCmIC@|#T$gY}HFz{{yN0gR1z>5#YoR@LUGk&o2G<T>YhzSNI5>)i@<c2Z7<D~7T&%$JX84UeqrkYQ#OXJ>W?p%p<Nlsn'
    b'SLE{BgX!}T^pvj6ro51!T@H7C8a)o}>{3Yz@T!qfu84kCf)xt|<#xD?uCGMo_h~<<qol>(j6=V?=k(bW{FJESbOWeXsyu=MWXAx#'
    b'Wo-'
    b'd0u&%?aPydr`_m<Q=14SYW#%fwj*a)!2;cYoujeo@Sq9!ZL5o~49fuLX$~>3kk8LgGe|>x9eP4@eP&dFp3=lx8l;LlWc*Y8vC|tY'
    b'R&R1Z88CDYZb%GKorM6A7K)=!SJ!-'
    b'Le!rZfRzM`7JvQ<X0`ppPMCECR5~hbQ19wGoaU;5ZEv*&z#~V>?k>tP%G~^82bV>BsqDNg0EsHZJdG2Y@hD*CI#wL;KhGP!Upzn6'
    b'fw04ytyJ0u2P|>2ZJO#6!>5<RW0_aUI5exqPLz<LQ0_t_wzEgEjB@!E)2Aptdkdj#xtS_N!DT^Qz@EG^~Y<*PNn6l+-'
    b'whfEy5C!jo@7;aAT4I5|>P<ZV9g3lY+iBsV5PO_(}yYiY*<Itih(>+>jUF0&kniOG>cJ8Fgv0a53IXF*0Q3$$pkl^W21aLaE^<EP'
    b'E{F!pyOQF)Qp`Q=>QNs)WnaC^y-pX5nMxF4Pm5_81YXf$wkB)PiA)3rSw?F}u~p?^=o#e1<(Ls!ne(+bM{~)V&9q-'
    b'^tv((yy7m^ln!PKPQ#FS7{O`<;1(>IcDjO(0;mH<iRp`A}>n)-'
    b'19wukrzc;czNo0Y2p)Lz9a!YxCjc@@uPy|Y2;+fdG0ThoP^ZOgO{aR0=qgHdUH}>XTf-'
    b'2hN2NS$MFXbCf_wK+kK@4h{W`a;YwV@8lcz)(OzsnP($O9PGhc=&ffAod-aI7I?Oyt{2(lxW$42_7I;BUoGf34q#$XSL_wH(N$RA'
    b'_B43gqNs`=4qi9k1t{=hKF0Xu;z8lLV)MuaNm5H-c*L$-'
    b'=CAk|$!JL5L0^(1QCc!ds$=vtm@HKGABAADf<GN`v_nkD%qq!djZV`ff6a`rxUH?!|p-|6us@{Yu4OgL4o6`J7C%McBA<=T-'
    b'XW_z0iQ^NJF8pN_&gVsrl57^az+)GM6S|AQN%C~*ElKJSKXU!FD6V~y9s|fJMA|eQX-'
    b'9fxLN!brZ+4_f<Pow=!^jPsw8#S2_4AAX4Q5$ZI62&+Bv{UiC~+LnBqBe{!Zag}<B??+IZ=N7BRz#UeH(H5S0T%x_NO;vx_;uO^E'
    b'~sDFiVrUA0?4rWD7Xrpjgb8$<iebaYM&V=6RGZT_9^G$v}o8#d5ivU;AABQ;4+VSg%Z=9X7%@JJK{Dz;X*OS-'
    b'5WCI++juE#@E*IoV>FFBeH#_#vEo82CxzcuA2I#j;q2%iIML4;R-z(l)7Teg-'
    b'j~Tuj5HZ|)=8iN#F4zQ19Uw(X4r%U?A2%}kC7&D%~PpeyEmJ2f>y|DRD2d_?aWmNRW;Bz~}HfwTwWERFXDT!Ow68ue6^BB4-'
    b'CGxyOan)XwvmYWUDRu#S*pbm@)*`*N+XBM&ni8s%1i-=d_YIhs&o}HKm?#I*|pj;JMp%DxIQgcZx=eA%meZJ!BK<(D-'
    b'K+&UXDb4AB)i9w*$`!trR=ZfdL&YM~WhR!u8Ld8Ntfe1ld%VJVZ_y!`nYvByR7#7=VUoYGF?$g`Y4fzG2QsCPa<h>YUhcL@_62Q?'
    b'+>XOuqiKvArS>L3VHp6?m3SwUd+MC`Rv$p5<~r}JmEnXMc3ZHaU!VL3K-'
    b'?G?A|Py_dYdjhwrWx6WyVeS%+@@JPP~3PIn>l3#Qif^rn*>6M{Dyi7S_=~nyLm8Qr}EAis1%U_TqeZr1x=xIx+wyu+BF6gY?PNCE'
    b'`ZtPTngyodoSRwf*@o&L60l_P=3C|4(1hCs#1w70r#wtiCja_9WWz811x<gpPNNmV5>(=(De~YIO!J`Df6Qn68tSWP{hzl0MVvwA'
    b'AQ*IxRH@u+oxj^INB-2C%*bE%}U=T1PU7mV#T|WtRf)6yYt<2<e~cKtI7aKkf0ESC`x@cd=%sd6oQTj&m(h4KR9xaxu%aLGk-Ni)'
    b'y+9*;QmTeM0^&#)LEO$9WQl2eEF`GoW<@z2^pc^Qv5oKM%t1c@KW8C?>99VQtCeS$!Av&Q7=qq<R}yg%&2ox6BG(TCiMb<urhWt>'
    b'%vXCl=myLvX*<h3T;rYBIl0u517&<GVS*yG8Xu;A|6srQ5C9O{gYA&v`hB%ncIZN5&^VLL=d=cnzM_WPkb{5Nb5SO(VAGI~=^>?Z'
    b'gBv<((z8`ro@ESnMJSe*M=K^}_+(FLU4Oj*!+Kn(Q<dy9Tn^8yxE$UlKBk5`!pb#<^YP&gh<huzue>>fr<wb|2X>0*Y>x32vsj5S'
    b'>m+kw!|ISx>KRBRw}dXy+0HlanX1s<vx}QusV7%=VbEFkO}PBmGTDK3BAn>5Idd*mrLxvm?iKNXkBUgPgvy%ENS^lV~Q=-'
    b'wCwwPokd1ElXebI?7pSlq0fme^AYcsiut-'
    b'*P)p9yqBVug~(lbE~PA$paw@MV)X}+$5JB?85kysg6m`~KLSvQ%yEZLKcL93MZO_E<zPDbxfwnu?^sM_$Q*C+kqJE(hv+nXei67d'
    b'gg{zdkVJmg76R+~d@>mz35k)fDT|@U=>?UV7I50cVKx!6mwv2M<4~vkNLjez%LW#T?<)u}G@OEtT)+UQS-'
    b'6(5HiZIwKe@Qh?FPfW3D$E0g;03yQV&yL$m?wfv9Nl-;x3^+zux5c-j9<it;z05h-'
    b'7TEdXj)zr%yDPI5vmXs*UzMUlj&7?gt@wqXWGGJjV-'
    b'X&T{5E|KYm#^W}XI{nzQdUhMH=7;bo*vnz5&oz6XU*S?j0)n{UO0}^dq7Pq~AT(H0gP~CPfLSB$5!{|5@Jf%~R)y29dn^+7VOCTz'
    b'=Yon@r+eTBI_&BcWujdk1^vwx0MJIRt1zk3ts5u6UKkU|$L&W+JO@x+^;OB4=3`gL6dwezp2a3ouDL=dpmybcM8@V+sKv#MVz4wP'
    b'5AcFnWhU2$u!EHQ_UIh09c(SC<lALr02GG_P2CQNn9+M4RUK2hNMub&|hes4%rl7e`X@tvEi^6D>q#F1nhvLs+uYA1KX3;z#pZMC'
    b'YO}17;9^q{LY<@(xmM4<}2c9(LUW>(R$8siN*a6ih2az%S_pWe&S|u--Bu_>ksd9E%wcAnPNq%_}MR+mWVJx7^kh@I<{_RuX%r*o'
    b'AHD@d#$E?g}EZK1vG3amAp8^nS99O6x6E@U@%VvNis{>GkO!Waj>`r-'
    b'zmL2)qVNPJ;od8G^)!F1+lf3))s^0%W7=8cD6Vm@A^U?oEQQ_Z|1ocNI#C>w__{*x(qLX#?)Fcx}5CvNxhuq2N&zCM6TnhVB@|Zl'
    b'8fb#qe_O_X7io<2567|nig3{Y3_gt!YgR^Lpl!<Lr6QD~KSjo_5V!oK4L`i=9gmvNAW)wE6V{Q;spc52x|JV`kBx$Fnz(P&>zS!z'
    b'fO;IZT$<%|9ez8z(-<)tn%;f-Mk%-Q$WSH`bEmma*`k<vZI-'
    b'Y)d;&><GTDh7nF!U8973d_zxTYYHHa*RCdct%FGkKaF^fW(4PrCzFS3o8CWP)PN(nGld`6n)|adsCzEcXs~J&2fiLrP2LN&$gC$m'
    b'q>ZrcFmQZwIO%B3TFBJ*Iyno5Py<>Y?ctjaFp0m$g#_ot;EabDf@WW_40+dJ1n@22@ef<A|uIzod&gf=pYNH9=n3<!fdwA4X4r55'
    b'%Uhu#xZBATU79B3cLN<&7Rl3e>oFI`SLaxh%e`%m7WyuU2G6>lGdts{7~bBponp<7#8l$tQneq6p7FGuiXlnc<ij^3=6rq;9b(YN'
    b'90ub<{_BePlc$&^=Dl12d=D(bTL{bt>oQ+n|dRQ9o@2R^Bs>hQ|@Ovnyrl(!7kasAVZ9V|fc2m(a97xz25Yrb6W}!H(ceT<(O)a9'
    b'rk!0FXt&-KOs7Sb9OD;b<K-(VDHRhwCnGWj&!8Oi~u;?bpwF_2*+%j7W5*o_(V7ShAm-'
    b'%zAk<IdUvUW??86tmaARELyP*k)79=MK8#F1x`9Lh27b<d~N?0Tc=2JByx_+lhWQ+Pr|Z=?Ql97=+cH^G_GjKYplEM$F>ggxntF3'
    b'#ba%$SAZLYgn0kO^8Qn?PfP@~AfbHaqcab}#8wx|N}+`|G4$JP(82MYaM0IdYirkSlx<-'
    b'uPk5%E=}8#7v|%iZZR>v+^>j1rYzzCE<p&zAyYI5dd-'
    b'{{8X2TVElvspnJ(1&RDPo5qCzTs57??Z&T<+w!l3xyRW^VOCR74^88>3xILTw}{*A9on_Z3=LCji?RiV3pR0rJe+mNHsL5Yuz?EN'
    b'zHhu|lslGP*i4Vxl|%3`ijBYE$h|5b455w*w>T2+ZIB@GhyArv@8t%;SCI2U?ohmP3Stc0<1IV>ay|yfoWW_P8Q-'
    b'9q%8L4Xz1L<51uH265B`jP-'
    b'%D#)P|QyW$t%mlBJhB%3eOR*vZ5`0DET$|i{o3~VE<*W#euriPhT?fB~1@fABOn{zF+zJXYp)EN;sM+bUR0vv84Hk$L$zb9Ic^0$'
    b'bR1~e?bQT!Q>o!>=}(Q7eJg;{Mp^sUSjAp~rzuDfv2@8F%Vv2w!<f0Om0rU_=*K*KST7b8@J{B~@!PS!+x`rwzA=Y_9(ejmyTada'
    b'qlL?=BXc)pcM#u7o=xEbiUiFs3sRrTD3kwL$FDY6&y3`IjQF`Uo+uoL^3D<9wrO9R1@t_*rYvv)*%#2KUCARcyrq>Yg4<ZHP;tS9'
    b'tngoeN}^9%eyj+35b_VfZBGbNt2@o{e4*_gi>Bl2c@%yzm-den7qeoXn{euI3d)r73K`xld)vSJ38(T2p5DK!jusM4GNhIJqV4wh'
    b'FWg$U|MH`SzCmwSB9)Q|Hd1f3gKx<I^GN4z$+hQ`gVO+CcG<mnGdCK@K_I!8;onAw!@lE@x0rTK7k(hd$VW^RQ8E_{6*r(FE@e#{'
    b'A|+L7{M^Ba}{?7*=ZOf@7(3G}VekWG(pB93q(2N;grp&=LOt2ttXiVOr#w*2jOMz&S<IAczpUFfYpL<ufT1G~_fk6F|ZUTV|{9d$'
    b'TrW2)>D04Tb3p|qSpwjA>4)au0bEZUkz1+gD~i}>6IjwN0T<o*dwz>(0W-'
    b'Mi*N3!mWXaGK>RGLX5kl$hgW8<iKgB6~Y?b=4s=gj?&6PqIW2t8t~L-)ElCT7LQA_>5`tW&KEPb!M*oCYBE=#dRFthm4|g^A-'
    b'%*^4`f?f%odSf+6s*8D}F|{7qnjDAudx<Q$Ici&z!zLV)XwIKsM@4Sb)Uitx)*5Pp6x#w*8<(=lH5eHF&{jMB#V`ELN_djK*B<>#'
    b'-%`DFv==fjcScNEf#k{F_j>;RPa^#?RrQln8&MXzO<h%~e(pga#$X%>%dxfby0W3xkj=iD{B4#4$B4?`|DfBbIH`2+ykvATgk+QH'
    b'LuI_KcF?<m}s>k~zX`!U;9n9W=mzATQpg88nEgDc7V|1QLn_F0&WrJ>IMpG{t;&*BW9PC#yJHx^)<zUF`54=Gq7WJh|fsffs;Zw!'
    b'bibY?2nGaRC;d44QGl>fhr8OtI_lM_4>eAnfd!b$YuD*9k6`LgKoA@e;=#^Ih{H0c6&%k82I{gn?R(4^Oxh|Z+DK$1{Sq63Kn6Hd'
    b'+mvTN$H%?i8q3NzRt#tyOQFj#`=?0UA7*?UFc&YjwkSc?(IGL+&0P{!V3*rUeIPr^`7lTKuv?dmxeDAz_(Um>XwB`A(2E4YEzoo~'
    b'^;{{BaEze_PoLsRx1jo^m<D}WWv^)nn_oy-l1zf8h;?s!2O6326~Fkg{6gph^jczKuwQCcKL7^S(hNQs**vH-'
    b'L5dw$?sFgn>|=y9v4{BeBl=tx<)lfQDE-wiEvK&eZHp;-iIo+gSdqS7cYQ(nwe0qDUb;42c4Vb@3j5~15P5GWcrY-so{#@1qj&KZ'
    b'{P+?BNAK?fn|&yKS9Bv1AU7TTE5VJ3M+9|HE1XWS!&D}RiXRr_B1u)_|$D8J&%z@1!4OpBXR5S$X1(cl047a+E2bwq~^Gl}JIZE2'
    b'Kx5})}McE(d6-I-%yrbJ#|ftP%xq1Sm_i`2*T_Q%T}F^84&WvP(O`i{Z|G@W4L&MDUG5S7bi?v9g4DA3PG?2fJ~*65*4NAp__I-'
    b'q8%<8G_nenwHgN8Zt&Mz{E!%5FfG&#Iolv0`$Zi9Ym%4gLDJP&#CcL&kE*Ar4NqerFR!iH_)Kv**QfkVdffFQBu`B=9QQ;5qOBoh'
    b'n}I;#1(9Z)LY_-kv<cOpP~D3#ccSVNTEL<j-'
    b'TvII+aIHj0L~jIYxYHM2DV(#elvXfr$Qo`zRpd1M+!H`yLixP>P)rSng;`VSlU)%Z!r<&;NP9Ls?RU};b9_lv8nC^j6%tR~6&_9v'
    b'{-eJ-Z<0KmeRSq6O!L=*ThDKSaS{!ZcTL_p>wEDbGd=tI)z_IZcv0}#~wnQRcAM#J#*FLdyq*w_=1^Z&9q%Qg`64V;0tT?71<Ft-'
    b'Z^S4G~)zKlNnU8vN9v-+>Aqj<YGg12%s6m5R`e}BXnQ3}Y{BC8x2Q3qBUi-'
    b'BX9dZ266@iBfAD0>_X7H2+*CB=@wgi81mTRjO=(HJKdfh*|2(B&;l;6x|SfJA`V9>daQ2bN-idt|P1zzG}hju9Z)y;`#a3Vt4ljj'
    b'HYY#X1I;8Oa~Wt<Z+F<JcWGm<FzyWJ1O!vuqHv?fEte2_p+iwk1{Uj+miLTiR;*W+u3qlaO^8t3hIhFg*wxIJbF;`Nd`|JH6(LaR'
    b'hAx{nc<oo+*_{<qC!*CDX5fuVSKJ0L6yAuqws!wFu0XE)wgj8Df2gA*DqI4D%b&!Un;@5<!ZGkMploGDPM8HQ_a02V-'
    b'#H#O5NDFG>#{ySHU^0`j_j$O}tFlO7^38c^z&dQaAO8?r}(JjT;zAhF<ok#p=O|8n<lCpf0!L@G1=omq6`PGz^DaQgw*0OQkAsjv'
    b'ymbFCjllOX5`sNiXK0)tag+j{bZb^;1m8}^K7t2d_s%DZ{mLPUSc<Ry<6d4yCNAqD62&2?QM>!6N7hb{*hPA+a-R>Nq-yG8RMhC|'
    b'Gr{5kwzG-J0+7nSHQhM%CvCqLq%-9(H;p&~4dujS{$uFh6f-|;yIA+TzDHm5EQ)cKty5XM5$u-'
    b'LzmHxP!svlF0n0;r92D0JV^$p8wV^_7?#q#(N;&wtJmNJvwfCYhXseqJn40sfxD|3!Rt76kNf(fcM#YJ9jZaiN&&G#57XE;Q7i1m'
    b'yq}AOa}?(ECTUY*T}_%%lx_pw*%2&zC|@Ijq?4Fwg3q-'
    b'oF8awQbvyw1@1eLjo%zUr(wG`m>RM<<y5QvT$lFxWkpnA`vGctRD*;ighFuk9rog4Q{J#@>jTDcyT^nYyD*=QoU@t<5`2iNP>>TO'
    b'p=F(9eJS7cXU9^7rjBum9<zVGKmcQgU9%YSx?A>PN$3Ibo|-0j*}JkO?LR~QXdMysFGMS7-'
    b'~OfFY#_@;TLN+me`Xmi5GvP)#mAQGu!RWxfCE^1N)I<y&od5g2T$Ny@|E$aO4hR6T%WO2CAAU9{da36t@h<aD@8`Fk5EDn9*vr;s'
    b'KrIv9+N(9YlA$)6&mRw#mz?N^(}eg(kITW<^A95PBYV$$Fjam_l4p9<FkIsEU>H6`v>hP4*M4qqxHAK_>)(r?nl|jf%W>2aY7qTh'
    b'H07N-!2Sqzj3^5MISZW;Ib+%cztpD+-'
    b'$l)WaY~>%lHV|F1{#^=!{nqY9E*h0Lb@o(mdxoIythbt{U|XI+s(lh+DDBy*h^9F4%WA11b`pkImXnBO=xz--buy}{HNlt2)%K~>'
    b'sm(5lFdBWY8mCyR;G8sf)%xoMaF>fvj$Ptb)#IgZfAlVl=Fs80U$mw*2!={rENf0MtmZj8)}kA%U8zT^KLnz@U&W#MSg4rus0GTS'
    b'_Fi`kR=N+J<Osq6A#le}H=*UOQ~5qKV{BGz8Vt!=<tfdeR3!?8|M5SoyIb48XTvAH2-v!)okO-dw9pgF?q)x&AWla<5S*>wAfBij'
    b'3HSE@h_%s7Z%{DJg>1J-'
    b'6(GF39PN|<PDJuO8}4<v5}Qjt~^Vt64BNk<sC5>71pmMvdLS*jq$s7XtM+l6RLmf+#Z)cY}EIMw)U09E`3)6g8Do#6J#3uiPzhF1'
    b'8aqOQH&gcCGgtv-'
    b'37NUlzYlK#h%jj#$Jb+ZHrJpxtrQgq`58$`P7GfEwFWG>~`?ZBcQdfAbka?E{YaSy@OSk8NzL+S03s=sAubPJ%Cm#@}*$}^GnR`@'
    b'_|iQ0%}D)fm!Gb)I21UZR1f*3G8Zp<1>OgBkm{(Dr5s8=E|^%<z;dr*JAqPZ$z<tb1hQYM71TZWFKJGE2qd@=3>#}&v<y?JDH4~#'
    b'2(Ago5i-C<LLT8G-'
    b'(9Zg~*Y8N2H=zz@CdQt<X)kVqfs`UlbBD1{19p*VkSGa~)469N=IjS|WwZ=724iZO9!5W(*AelKQ)0Y5ij9}H;NilrzTSNEjg6lS'
    b'37pfIc|NO*F1fS+jLP6AJ6^nqj6ew);a%KD&Mm_TkwHXt-ty7B|#L%WE54|L5?A?sz@SJgcLVtKz1DYO=No{l--O|8Dn9yUG@-'
    b'P<$F!`q(eLDH%`Xas4l!6D&b0WrIxIBT~JZ#Y9$O8#@lD&a-Wq-'
    b'b5dy9oHk^6Znzey?G!;k9OMyub+1cij!O+j5ns`Rljm#lc*=7JeMgU^=ow1P+}NQQ;V@*WaUq8RN7o3Sj}x<6cWYdg4h>^A>=dco'
    b'V);!nIwPbo>##9x?ZSALZ@=&LCIdYC+%=)G9%I2MS|f_9I5iNxyPYGDPlU0HvjhVu&Nhkt?6w5>@Or5hFIyd_mIi;|jn_@kB_tDZ'
    b'cU`$uKSz?lS!vO+8PL8K_(qKk@nJs4UsT4{UGNv0-efWa@?jN(s`KHEa3YURVUHylp(iPdAaEF3*xd1us<)=p2G{>)-'
    b'P10+?Euv~d&X)Cx4rM(>{4W}$W)&bi%TuByfa?*mzC@pdQ^B5r+#pS%nvVC5}qLk7<R&6xh77(NE7(U(UK)Evja^ih?VX9Kw;6@0'
    b'(nc*}hQWKm-'
    b'V4}BB@$fR2t3CZ{6Y)}f)VHI$;{k22q`0e~+;H;KV$t+t>ms~AqB6+Tzje8paStY}B4DGpKXR213of8L@`mOXEiiQ(ljvvSASX<K'
    b'xS#y|%YU=Nq5pkz|KB%VYSw?>O#l04MK%xnM`-'
    b'83A0p*A?WSrIVP~vD%amQ(i1y`bFMDB!<<f4$^_%|&xEKrN0*JXT*S;=Bj!JGw@mZ1vAMQ?Ep>M8`Zy5Ib<hE8Q<V=2<U<my&FtP'
    b';u@rrycvx?SiF0;XF3vLzu<|W`?T{1tjZ@#kmt;Q-'
    b'CW%VzRJ2c0v?AOs#*2*){4ksRJ)HqZwcQV>%BQj#?St%vu6>xxKYkd_UFR@at_fU?1l&%$I^={uSd>0J{1e4;N$JWSG1Pp=jp!Lc'
    b')|MP+FHFzl_c{U!8r55CG+mTeCzn?u>FN`ieC(9PFO2B4fw!!P2qll9U0Y?qO&C%bUGy4sMR~HBhNUM&Ejs3=M`FFk0YeREs^ZtH'
    b'skUV*jj2Re)LY{E2u};q}ebKCfevB~;^ktTAd4Jfh$Z6z%nsfcPl_>(Z@6Ka*iPuKGKepVfTzr>X?$xD>u|e8vix_OF%|(8`Q93('
    b'5W@Q=K?s?fyuGq!asM0#Cwnib>nRra)dZ1JRp9s2#sem83Dh&IP2|0~mH0nKz>J-'
    b'g9EA`qHzS6LF8CYAaX{l{>))VS%@^yeZ>uKsNFO_j|b=D2vt3Df!OQH3>cdOA}cxe|_Y3CzSX)g@Px7KOrqtj_G4B)p{YUkgfQac'
    b'~7Qp>7*jZLw=EY`oJX8RsidUbfdk#75~S2<X@^+&AS&c~+QUKT5^qutKOsoh=})R$3jnWFcu)LT!ex5?Lj_13?|jIgxe;*1pv@A4'
    b'=7Blj|5+O6z$iheuHsQoRK#(vJ^j7aZs-ksWWot3`5{@{Fv`ooy^G(h}uM=bt0V-'
    b'tUz_bL5cXSwG}5bUmv<u&>qga%(NCswjRTV@DuMUCd;B151=23a8b@)q&vy;{Vhky*t3_iGXN-?K$L9Fs-dAC*Ns9G^wpADKiOeu'
    b'olmIBtu0G(L;CKN^d;KMISuKMISuKN5?0Fk+Q39GyknAD=}$9H~Xze^2_X(DB}bIvdE<^lGzk7ZM7;<I3z@DYLxK<#k!_ovO0lxH'
    b'Q@K>)Q3MJ-fUS>9ON-'
    b'?D9sZ#*WRe%li(sSZ};qtT#Fhb~G+sqwwe&g+rJ35v=s)+N(D<?RA9iT;4d9SMNRPu3V*i531{2ET&g;4R2Nc`J=jPsB~AAHU71}'
    b'TOUf{hf?^V6n-'
    b'd$A4=heQuv`1ekg?>O5ul6_@NYjD23mTQYdw$_n;PrT4|&%#W4IcreLHzU@ntX(&1*H{$)u{Fgf$engEsd)e@l6!YA%rR&imul?5'
    b'}JV4WK{%$EtKm!w%P>ETQ#&+s1r)>PC*ngFAl%3>+-uj=^@KHc%=>Y|?VYTxVvpOl;JfoA>fOOaaN-'
    b'2W`|^CK#(p_3|9$d%C|S(mGqn9iswX0@{T_q08p6}7LoS;dT=K+np6VtRJO!OQEUb#A8d^YQgJI@p$Mow|Ru90%y7+YNYIqX7`Nb'
    b'+dxH-LQYvvNTNRlG`nYR~G7DY_k=vw3!bVvHm8>c})%jd-SBYnjqc$@$*z{KXYd|(tcJmjuN;tRtDkLVf;YfI-'
    b'U5A|IVuUFlKX0*KkKi!iA<Ul0;F)f?=$^)C#-1ezw9^=4+>UcClOvDc8t@ll>%_?8|i%`aMgt9s^xq+}Z2b&!?s-'
    b'<|CS%iF4(X3)`?{zQ9%gdMI~<vfoXKV0e6~X(349vaGVjc2_<z8)1SyL_*(sDl5an$?tiU)#=3bW}L+{hCgE*N-'
    b'%eEDI8<+1(v&Do#-mmLCcfk3Hj+EidiTO$nFQ3I(ajpP-hh}yAH#0_><>H%tQVNIESf^S?MHpT9clVi7mkXFZb`T>N5kbxCsHa6P'
    b'YU-@4_t{^$(N(<!NmjV8<>J^rF50cdS@i`y62YEvvbU?E==W_h`%>bJnAAT3Q=cPzwG-'
    b'W0^?~eL~hpY|?fvFu?w>+tgSrn*2b=_+QcAX@@29UXw}vvQAOb>XHg(6k)2J#F>fAdOkEmb-'
    b'2S!UcF?+gdI~xivAg8q=!|Ng5*~3tL+R6%0H1AE*@xy%`&Uu4_0lP{wfA$sG_7!S*eFJHf`Kn))V%_hmgs%dq(-'
    b'>MZ6zdo50O!OJ1Y<!0*z0gt9KMA!O?3OQ1shOD42x>x3<4!uB=6HGzn>!Qwa%=wY{^S<P8F8)zo<J;r+A7?JWGlNGN;zQ-'
    b'>(BNJfnQb6c0veRj@9wpE`=CBouiD7XsT<`5DZU$?=bM9o50d>hy$)T0!7`Y_Oa=`nWw+9wi226y1H5bO9A^M$ue<0|Edd#e&*th'
    b'_c-JhP|9x0ulEXCWY_)FlZ{P4;5_@fZx*Oa(HyV~r5xY=e5(oN{8tdmty?bfL1X*e#w8sx|JG}ErYVe}t8ApNtEVhSA&a)Xd#M#x'
    b'x!0AE0!NH6vIo=$zVfB|rp8oRanZz(|YQk3ul)=x9{YXgYdGqQH!ga%n^H8K&rqH0D;u<APf5uiM402d3`5g1sgUXu(_bbqhtP)w'
    b'G<AiOhD11r=47g3FMq+8(nL8DL02n=nFF|a+WOHPLY(#^h*W^LXDRYlk310yaFCVf?`1g=B409J*l7T>9qE*eTHNwUX@9CU`GPR!'
    b'~<@;aq=?)m_iDPFh6-KI-'
    b'P`c1A2OcQD}oACRa9}T|_@!H~7tFnT<Qd3n%R$;Z1MoM15p+_45VehUrz+LwMgVe#n%dyGN!~6HEVme=AHpo-'
    b'q(jMVefH`SFHprYXKtE`jMW;@LOQZX%fHHh3Hi!)EeMD&&7R6HmAv?Yb1Vg5`Dw;?8^>15e=qGMm>-'
    b'ws#4_kt5^Fw;}Z(rE5*^A_<5HNec3J8N2VuQoL&Zi5F#{H{3dsWXd-oF;3(Evdb*1X%ZdPllmJZs*h;yb@Xg|10$6H}Y6NVQ}o7A'
    b'Vn2>h;`4T!AjL7k974@@!EnC!#iSTkD4n!jjQWK!pS*zq55JeOzvii4sB@q>boi0W()*&+ITL;M{5YI+q)`!D_ICyPz8Gz%#Vzx='
    b'SjAJ-OkG6`o{CtU*`;beYjdnSS4~WkdY><c3^zt0z<x1F0x2b1a$)YpQZtqY96J7i9fHUWE9>7BP_zC*|J~p^M_C_ON#f#{`(-'
    b'K!GZO$@3WIXjHZ490PucS=rtgzwo4OD5mqe(f}J4Qq`+0>Ld4;?d4$5N+%ySRFP)$3Hlc(Pv;jHsb)c*XY7o<tuu4wg}0^;J#cTb'
    b'%aP6TYNy&19UGI(@lEz-<>E)T$I0rH9iGjmjY(ogEpd}fPG-)?TbY(grE#jAGOC{-AyfDPL(Ox;lD<hmK}V{cN-'
    b'L;Tf+vz&G)Nk)ut3F}TPhl!GP@uv8&4T0vIANkl8>Ff?8%I+lJQ}&*EXM~e3#l6Ceo5HVOl(Wb4|)k&9!H0klYda77KbZGa%2B{V'
    b'bVL^Ki+WT40>*78rm1!$h(^G;UH|cTL9=M?KuOaT?bhdKWC|U4VGcagGie(?L1j7=xZ+?SQ+ZRrruSX~$`jeOXlxdKp02AYK_lL{'
    b'ZEO$7dD^rIp`qp0_hL){Kv3ROaNP;F!~!2eKhMATBYqq#I6O_cvLvTzHA=7i8(?QBo`yWD$`hjnXj67sWCQ=BdAQvV}(+&-'
    b'a$jJem8sHwVrWEP|+a5@b{NH;t0UN7pJ!S+>{e!Ya}vT6jgcEW99hNRX06kilx*JavL1bW@V&fm1|5;uoRgWp3ysfwM@{ED4gnNs'
    b'g{n9Ak5>98q}1dVJN($rD*s+ckY-u6AEyII1<j7Nm{>|8A7-'
    b')NjVdPpog_qvXZ>dmDXPKN;gRB;wC%SHSlk$UZ&+A5T4FK0|x!=geT742TK94q1VCWJK#NyBLaORTI3W6h!ZD`blys-'
    b'<j#LidI6tVpl1&l0V=vi;tQz%D?Dnv9IK$oNvaWN@=4dE$Av|uHy{>ZV4hg+a;db>)3?>JdPQ|P+3CF_)B7?_^={LO&X2VP!vmbq'
    b'7dNV-g~TH<D;BI!cKESw0%}6E)67XS=1y;pZ+C=DAas_`-'
    b'6G~s7D>v$j03@d1A(FQ8O)8fOGg{wTdgaR(H&gu+|bj9QJV4<4R>8U6s^7v(<2?rnU(TV?*cz8*7KYZ8Gx#EmKT=P8wsfTaU%<z_'
    b'IHrL~q8xYjUM7cBK1VT3C|)v%!}1ALN)hS;5`91Cr)G>qZy!dRBiKKY?^oW%?}o@Mb@L1o}W|qmNOPRUZw1*XFA65p6FY5@XB`!5'
    b'{=`=UTyw{sr5q)v|;}AEWHe&r<ujNqhR=MnmzQ)C5%XvxKbpusNVx0S#^vPjswnmTc<-'
    b'oG%Pe7EG$5+o*Q?B*hz)|1L)aAg+;X@$USu)`W#du;w?}l-qJ7NDB2$?`?c)cBTq~ET0XGmp(V?2yFXBj-vlauN9$c7&zVCsy&7I'
    b'dvhW#%deStWNQZfXJcriUs8}3@3Xe-`;DSl4XRi7M5;-9An71(-'
    b'G%(MF}D2P7!d2KOLu9@kmm3Dpyn@%Nok|)ll_6A2!DrWgpWAH&0?Ia;fjW>*X$2HlME*^?Tg}E8v9h&5L&ZV^wp3mt>R5nF=-'
    b'BpO$AzSx)bUxTy4ONR<Ypu8Iji(FFr4pKp})z_|F!;dNXyWU7`YWcb{pk@$ULO{n^+Fr<0qh*EvxCg{aFNICv+8+)Vw>DX^40BlF'
    b'oKiibwW#>g7p-'
    b'b{neAvJ+VtXk_SpIuvn3&g#d&Zk2~STQ{IMJFC}Py=yqrr~MB!V#+8GxfA8=1^Ro^Y5E!)H#D}JmZaL;xeGaeQt`?$7P}Ejm}4eM'
    b'2#X+n_jrR=>7y&*N|EIM&O1(De;=TrOj<E%(KZUEo{-'
    b'c&d<M^0}c@6Pe9M99;MT`*Y0mTRFjhhaWX&jK+Pu(@fV;gXPLLm972}P!gbw@xIq??MV@8FG6+E3cF8hdM!sVo-mXO3@Z9KrhWgh'
    b'vW}D@=wjM;$B8;*mBqU4yFwLVV^p?Tg3l_`Jk4O>tN#W(uGFwJPkw#uR2jR?FhRb~6Bwlf3o*o$V5#_O)?*3xrKS*O7&b>9^QYbZ'
    b'W>7b(s$<;+m<zVrRlOg{b*%6v{o6UCwt%QPDwSKH|-'
    b'2A;~9MCO$$1#5I8b^5CapPcXoaXOc<8TXgtN&pmjM;n<=l}=b4mERq>>I*pihU)lRnulC6Vt@6#;VWh+*tKFL&(LWokQDpn$%^jy'
    b'Xx`XV>9_6fsr(-'
    b'ld+x44A<D;Wd@a7)_QgfWx`GVZ0z(^qck>n{#c(aayE;&&;ZtepTZJtO+tp1PJ%#X>dJnl#`@W=+e_0hl}bdsm@?U*tq~RQ{R<6Y'
    b'V@8(rP_FhR?sdmx6Jd~|rLAb)ts7p(87pYW_&oaB)Q--Bt}H@Gm^5)B{AbOLI?{p3Vso+CD}FU?CU*Og-'
    b'4@f?Ar|lT`7z_q{b@=^(=tO3TM~-'
    b'I^#<=#)*BxE!(mr)%=@rTy#src&9ZZGyU}qQ(FHgMb!0i<>nb`i6Rwn7@l3PluF4Hb9*kfmZZqWlSRk6lX@z(xUmpxE+}5Sc-'
    b'=(N+`&mK3-nq@<ZS92V!S)+I6a)KTZ)1b0E7(!Vk%r=JUg8$U(~lN|P3t<Mj!CgLF1O@-R?BOt19|2J-'
    b'Xiy%C|{B^ou^q*M2jK`mO&CZzQ0VOWF95H53+x<$QDILyhTtfBR5?n>D<${PO|}b+g!ShD90=yopy{a8$`Dmp-cJ4%evRfd4IMQ#'
    b'`av&&{|aB7EPvn`{dE*lE%9WD)#Ku;6|>{sbH{L)Slp0S{=Chk9RQrQMVGV3b<+M<${K~pBpVugEz02|8OZ5@Z8ek=?`UuyqU0C{'
    b'wh$Csx#bAYZq@0t5y54*4{=lJksb~{x{2ut<6K-'
    b'@x|vIK{pRr7mYtC5g*y_Y>zaswfkA<$RiL9Ij15N`MQ^OOZJrtM(X8UTN(RZa9?CT2ulw0tU7GWZzT<M5<dg2OG_>PrtGrXnF(7d'
    b'ED2Hn{)R?-#S&N4CCUJGyM4K7TDXp*FEY-8?AUd133Np-uNI~X=#!%SDwk#Uok3qDK?*i;lt0g>7A^q1A!K*COn8FdqG>yZ0lzP%'
    b'7HJTFSWcU6?D*An^p{@z;OZfFT$J6Ax{kG+60{*&nU#Mt{p3#@e!^7U(D4Pc@kt@R#zW}J98aBZSUA{@p@dFRaK#{<#br^Ll*KR-'
    b'fBzfVRh05LX(c<LZV*gp6d-'
    b'M+3GggIN6h7T%ZR$d;D((FLvKQRtLBiv2H95@g{o#}J!Kvc=?M#5ferWTuY=4+{b;PrMxN62q#`HussY!99vaGhr$pc*^<>qf*0j'
    b'Z<$Uxh5L?YfO3%HTl1$`WubS8T-'
    b'_sf&!VfL!Gm_vxca9trwrH(#m(|YY(GCED4Oy~=3b6Ce*NIb(wH(9Zmj7GN}nd0+QOU%RZmy`1@d5-'
    b'JH#G8k4RcPeTF9PN+LKQi<h^R@hkemPmDoW6U3K0`YKoW`dsLO0c5<FK%L{w9tLZJAr9T^J&yfN5W%-'
    b'T`GjQ7w%BfF?rL3?KzBdyJcL5q#qcr&BN3G<2W@*3q($x)hEF%_GEOg^N_H~6xy4@CI%&_DQf%?xAc*~3%T$aEDfR2=sx4g`H@sQ'
    b'a=xv5<v$G8pT74p(ty7&*!YmtLzr3=;`u2ObB@L$ml_C=Bgi#Jwh-agTG_1`F(a05;Ht-'
    b'Liczz>Sd+QE1lzZ@%4Z+Ia8%EU+x5>Kn5j#cgT7SLSK~pib6AS}_y?=(}g9see%@p?^i$gS5U0Ofg3^utxvMz@XL-9Gmp-'
    b'cFZ!{NC8{_c-ZDb^!<F!HQjMeFqBBMz_bv|6eJuPV+&S+7(t&W$<4L(Z99rvP#1AeS-Ms{Y5+!{Zh&xeRy*aD-ZnAdh?sS4Xa9+!'
    b'AjWscXtH41lV;-'
    b'S>LC;~{DXddEFaKG@R=a56H7_*Clpe0pq~LE5>>cnRH0HXxR=(d?UUFv>sIVuTeWWbBe!&GL#Na<Va=Xq{js5Mnm-'
    b'EFQ=0sYU-7cRC^V+j<4;PRZn$GpM_o-zR}FRDmrj?-'
    b'1S7o7<y39Mm~H;TuQKDCmcYjZpgv6VH#Si7t8&WiR`rcx``Ynmlb#lGI=k&4HUVgDBH(HLvFXm*GS#=gHy~hy7PLOL8yDrn!Ej)+'
    b'{i4j_yM0+u1yI|l{K(DY;?H)k7Cox*dXB8Kk#-stpf=SC3jI%In-|6v<u_-1>VZ3r$C4JF*3a@8iu>S-'
    b'wF>7t{=MzxXGTY~!y+zjF6!XTuQM5S@M6<!WNy{88(9VrwxiQU3fo|p(*CW^KLD^+l%Jkh6hj+t>k1KQ1~92_H`VO<vD}k-'
    b'n`GqnurC%&=24envU<RK@)5%*nf8c3pLQy?wd(gH8%~($D~!7Q(|`U^J29J2Z2RtPx5DdFWjUpRow#ikanKzaNj8TyvzPTb_6+gn'
    b'd6f&#tNeCe<*akAht3hV96S=Km;7>*v82EI*E+pnlxZVm8+Bo3hTsw&*PUBV3P0d`)GB#_&G8^n{#s#cOl?Gbww4R`@G0Hf+hrL4'
    b'_|xzI<zHe9S*?Fy&vwab`<QI7xJjA)z+y&`RsHPDmOsw^E1CW6cJ>**^OtOKZ8IK5pELf4<s2Ti0aK_N>*^&-'
    b'7`}lph^YpHMQq|n^7Yt^$I-'
    b'OQdqW^*zsJSf<7%f*$JkE2&j;o05CE?OrhZvmg+4crnR~6YmUF`XMtwLfJz;G7=x}Bl%{IExRdZBRXlwDfIt_Qle8(Nr8dNOZTV6'
    b'*ix)<2+L&8!n6w2Zj<hsxaQ#XChIwt>i&Xd1(YzH5PJK3sG6NiKH`H?<4(+rmJfBwhs<Npu--'
    b'|S!ib@q?{_#cmt_v`h2UH{kcdtGzQ8=+KUaU~qvE{?c9j%_<lSIsf6f7A!j;R-'
    b'vpZP;9Q$F>L4)p)F{zk=*9Sfa)EdUR~v?koQ0u(LR$kCf!E200;83$a}~DJdbkk=@}e5xVL9KRP~Ok5(9+)YzFx<jrZ*k_}{R(6g'
    b's4`IhFuqwxS!W9{8pRo>n**qN|plvvP_S>{{f!b$lG<kNzRW>QbXSAN~FEMc6OVTUGKSFXoqtywd!I%_jU$Cyvil3wHru%yp@MpC'
    b'}<!BF4B=<W1fHJC?fiESCtZJq;7cYyXAze*xuLg{RyzUkX=%zfdQhr%%@gkFDxu3R5#r`&{pmM+xDboOnm-'
    b'$s75Z?goOyUiPM*LE5>{wM<seg*si-'
    b'9xpwJ06~Kjx!n$4Par@_uMHDSx`q`tw5iVIh1We<PSYB>C^cRZdO++)4i?bm7?nS(aggP!2wHDums&$K`%80?3Qm_dv4Z**2>g^4'
    b'ZcBY)HAY7bUg8XB%ioy@`;8C>(zNzEyfJHao~vB-KiA!r!PICwDqV|15}ibq@{h?N{^%|ZOgMq<ij3$>y*TyEa{(?R-'
    b'7@_zfd2le^V6r$yJ#&cw{ld4wE~q1i#YQfCw$_$nDc4^X}$GW*;40MVFR=wj-'
    b'4iZEmdmIIj?M=)Fu<VqiCKEh3T7^3+0NF3Zs%Tr1LvK}1NJs$x#Nve;=n4a{TJooCmEdRYZRG6;KnBEW%1{uBK4$!#H@hz;lbTe%'
    b'DCctul+aW7sgt2G+)hB_vm<JaA~2+e@84zKPWXJa1s&cl-'
    b'b9cKH3nC#DVu0PYMej<AcC)WHz2_pyln)jtseAkZWJqtg{3tjc>^FnX8x`Y>cBd-'
    b'z$%z>U=Bhpkg3dwpZqg@5uNefMq*@?K^Qmu^7X3`}|%g0-=l1i=LwOiw`0c5LIPrB-'
    b'66UYvRW+`M7!TOuOOVO>}LdM4PrYwb&mSymUX#hfaqd{scTaik?cXW`Sn+f}lZLPaY$6mWTbZ#EIDChhBBkOBxKRz0ne*~2pZI0n'
    b'pqj?9~HYe^u{R;&b^yiKJCXogjQ~8KA_^u-j#EcZfS*-L(VW#ci-8{)=u1d$VCRpqPOUN`{-'
    b'YA<@zh3>>tvUZ#P4mrtj3G|PP;$P>!LzAHedcTn?}_Mzjle9#X0BT1%B7WXzs1q36^!}x<u0!IGTT1E_k@0#msl8&#L8Z5yb>l}?'
    b'EaMIL~6_VX4h!vGDhmS+qIqdgyzrXjtD&GMkX7-HTUu@u3Fm)z6ZP**~M!v{u|!ET?_dRP~sch#y!XS&bgKKLhjhkH^ET-'
    b'9SHp<_SLS}*Xc;!T{h(|*?e(*GfTg^U_>_F<8D)ycMG!nNm|l=q+8Hl_x{K>K%X>}SC!^e<rz*@MoMOujYZ_;9qL(iBzoVp;=U$`'
    b'-yCVw;{51C`o-Zh{Lzlvv`@e0xXqD9eQkU%85|nVD`O7SG`CWW+7G|IldD?^#-7{5q}T5O!Og9VI=<GjldB8f-'
    b'xq?9J50T?iH~UYF+{6>B%t|7K=YA+<|6^kyH0!Xk+$Ktowh-'
    b'*c{Nf})OK*iges?&T^6eq1vk$NqCDbLdL8fB%lPr0?MB?~nB3>o`CSEfT3pEARb=G`)<klxB;ff*eHs%$!#()hgNJox{F}?W=rYV'
    b'RTr2qF$TxJ^Wsxqcp1GXcTki+$9pi@-V|k7-'
    b'QILl(>#*_7Tr@`Slrb{j#&6+iF=pS2(YY~xL;uB*J1%|$kHzo8Rq?vM5S=f%A8Gf$t2cU4<m#qTpBuAS<TtW7_nTz0|Be#;ek5Hz'
    b'mphO81r3NnMm68xfRcn5oK^?WUN;r3>J0y(amx~*nwJ$<TV!!`?i^-'
    b'uzB)4x&$(gir>J~bsQnw{2%<W*D4)%gZ>8|}Rww4B8@mf$U!CH99go(xW@Z`l0QJGWa|i!CDE(1?H0|qiA@xP~n~9NHL9~{{NF7O'
    b'!Iwv_R15!J<(;6(<ABor%C)g8r*BRVq2|criavckmvIjDC1_t%U?eqo03<@$i5(08Oq~chhLU$NJuUq~=xA$JB^kYumLwv9YI5zj'
    b'Y9b5fnZLY6JTuH5tm^PovBR+~fK7ZXlbiF=l{VroYE?C_zO}#Ec{T@74kC-kGlM}Lay@PaQuTK2ceh#xfFUeONdzPw>#8le*1eJ%'
    b'pxXon+`O9Qf_O5>1$#+^KVBu}viBHS>@=nl}>h-$=7Yfb0z9xS?(1V8AW2{-'
    b'PXo=<jQ=hs>X?Q}dHVumoTwCwq0(l9<0NW{c)tYZnHOG}&2@QW>h|I;^5>q;%1Xk7{4C|>xwK1BnW0p>W04NR%G!^t^D5Mkx#e0@'
    b'4iLT+D{AMPdk;!~w_9jE0BICyc%n-'
    b'AJ*RTeZx^^+p9gX40c7!e%WJ;RW3mRmkhI8FL0Ew`KL8vfnvT}=$KCoMCF3Li$l5*Y4&tolA<dndW&zF+ul~847(-'
    b'PopNKv4qWnSPda^H#aB}vnHniWN~D3V|qB$4C$%OpzXQR4ef;w6i0QDnqh1jRCP(?ycbJ<HfuF_t${`8!1~d;lFLz7LbbQJ{W<++'
    b'q52-'
    b'5(^7FOW#APqH79RjjPP%vQ+;^onG^E5GtQVkux9YM%6YFxk?eqqO8th+=tIqMWufTw&N9m7q4EC2=xROe&8|nXV7@{?q1RDUaV`4'
    b'#90eJ;$Q*v`9IoPk!xOj|m_ff8v#s2|m}(z}ztx+CPSmZtBcpvK08umm^br#>*2{wc(5m^T54u9wtmLvH_wI&{48s&_bi&VK4M=S'
    b'd!>alpByoK*!3ytf~jNL}IG+fh5B4UpADV**zty#h*bXh~R7#^TDPugVGzdN)d5WqN4jma#0=_f^AvS=b9R5<6|>zZhMQZpNw(DN'
    b'0HyIwWIdJ&ViY64PY#vw6xSLK_Hs;@>l|<ezWZE?(yvIf|+Wumd0HwvS@w^yj#o4(PGtb*Dx}lO6{!evcb3~Clq>>+%sg^Rse|?Z'
    b'lq#A!=y6bGx8dgOOD#6a4hp+`z%t!4is-hePE7Keb%U9)FlUIyT6(GCk@DY%{17UgNpqJCylDzat094g2oOBZd4%+Gg*;dfH&xO^'
    b';CTk?p^#}T84ikFQf@l-'
    b'SJ9KrpITL=+)JZU+8eR2y$MRH8l%2TMDe{8cDw&ws_fK3;B_e0lMOedu2uRg{pnSieKn2TpCijU&W6Sp7_%X*)wuscF;Y#A0-'
    b'7`8!Q3rORE#h3(J~|dIgj|^_|N_Na|&4XEd!h;G=TcUpW`5<NNuh0x^B}T-'
    b'HPfjT)JKst4FwEy9#YsLM=}VsO4?yRW0pH#8b(3*U>-E#`}2nJ&^Oh_b{Dmzfu3#Uh-Ca}p7s%#(<aG%xbdb^T=!6p>pLOLy+3p&'
    b'JD^$LH$ar=3X65zoAOdWUXYf70$Rp^^p5g_pQ~L6&YFCB<?<77<C(C=H_=pp^yl)L%N;!Xu97drN1Y%>CS(=Q#-$L3DJYZjji-'
    b'3=8A7tl5Rtq)D{!if~zYLGF+sC5r&aFmm(M35w87NuCEz5e11~gpQZFp_2s8B2BX-'
    b'NRCZ(bj_x=ciypeFjy(E?5mhxll*=z8Gp57jEPB__{G1pN*U0*6U{1W9wV!|(ayBBw7axyF$N#u7lCnCFjG-eq?jrm_7<`u6ZB&&'
    b'3bUi;GHgP1RoD?+ExVGg!QjzGZ4=Y*b{$1uQ`xOjO}ALmmMbhm0Zl+VNbj}tnfIDTyK}`S<<Hicd`|*xOS4O4(3XfApL{E7CW$U<'
    b'gT*+|qsw<|-o0A$=LRoeD?)|g3D*E4iGOMm;(3zgYZEE=-'
    b'KF2e9b3n$j}*$^bqZx!x2&lIw><{gjeG&WK`8=^*L%<=os4%kBd=K6+{G0=lUt(i=-'
    b'jz&qWasjn<MwIj2JbA`SYR)kJ^P)%A1y|a9)Nhn|^WK5}WP?N^F{yWKG3rG-!UFG-lJbO=e?L3Ey5Yvnrh<W!KlQ6VcMbUq_ba^D'
    b'&^!zf*SgJ37mcViGfB<6NWBxj~~+9gF!g2c~P}doxT2zu97}?;>v5s=ALUaJdJSq3xwqU54f}NsZq^-'
    b'xVUlH#Srl{OQ$M6ZH2YJ%gv=h;Z&CEe{Gcf!#|%pJ=~344r3~vFUX+yN{+y=tMM5Wa=K~BV07lge|A(0b@Wn#y0HHeDxAPKax#s9'
    b'CKXOvHqZVB+i4&+pmm3IYQ$D;!P~;cxAN7uy_4eyr$VgGw^Wi7Tsn@g<KC_<Bj+VGhTwZ6`6jwE&GhDw%Ri4$R`S;x+q6iRv=XKh'
    b'SWTRT5lVmQfyTf)z$^_6K(zPtT8WG+SDTuJDF2oTotiZYid872xKonX++1Q4!KExOkvw%kJ*hfyZr@E#oGY#_#Gf?#_seAe#Ig2I'
    b'8zYB9%JcX#eJ*J^z^i2*jpA%l~?_bYQEQbJ9bma(C41^^Xz+m>S?X^q-'
    b'P$xlbG$Lr^B7>{KuYG%W<}6^l$Q9VRgUzuuyzhC`M<Y=<{hErDb_+=0XzzzC{usW9m_p&(%@_i40Sq`rxic{+iX=#`PfhKGObudo'
    b'yB}RQ9fncvsh<rCu6u$N@gBgcI9P<=N_Y`I?*tcKO>(WMCBz2PHGGjBd|ha49dr6C+yMx0B`Wu=C;$R@u#ZntHRM(a#;$h_mek#)'
    b'{3}jCPVd*`h8_Tl9fVbQ2xK_Uc2*4YSG=(P*lJy9E_A1vfiz^YBrF!lsHl!?n&g8klJM#s&j+WWQr`z1~>R<_aeo3bfshz)+x8dy'
    b'b)?9hKH)C}^~N2ZjQxuKJ;zo}BlM=bFH$03)uG?XK;&S0w9l_3}!ez51m_u6kuZRKZ+FZB1zI;;OY-'
    b'=!_g=j!n6GiQRMaD)Zr_4Bv6Z4Mjp+#W%Fb{Kh15gEL=BBG)cDt3=+&`*os3E=KQ_$R+3NW@2_0(@C;zit3i;Is{|3C?P){VdkwF'
    b'ML)M^YJ69t<Y3telU+ro6+2k?@2?g|`J7h~M|BP265^<~<^kfUNYuoWeay<u_OQQw^0+|Cok(PUCiWJK`8$vqJ(Tc;Y9uj$V4dul'
    b'q=`FGzr(3)@jY#a#E2JFGAlm+5;(sOd!v_&nDI<JGqD)H!^?=x$e92uIlaUua*rky`DhJMS<InPyGG9x^08=R<`nG8Fi5#BGEdAr'
    b'Mbjt9q8oG+ef;KcY|Q4@Q?nOt(SxKeA2!UXge`|F{%F?15WyE&U0Qx(QG+ZA65BX+3|5zbvGl%nT>tNBp{<pPL#&y^X?>=SCIbG}'
    b'ALaO3mM*3;n@6hhXlO^kF09w$8=XjC-AoSKfq!b+;khh7Fzp><niZu?2}ELyfhxBeR-At8baOp@*p`}qj4IeA$i-'
    b'*l()@`}$TD923y$-'
    b'9)`{MpDr23Azcq9IG!g@G=>qH3kYtf0(cJTcoTSduadSUQoW%EXce#k7JaHn=j~2vDvOMq?8MMgAJS$uhES4$egn3w1DIjCLuP`g'
    b'iyzo-uJH@<k7H%=m-1&084E<=HCX2{RGiN~@*CYO7898C<EP^Cjrk<N7Ns=zzz>~4y_^j$=-'
    b'aN||FqS*dJrCAYBui4bK@I~JBwQ43Sh$h5@O>{#mU$87^U#@RdA7{v{!%8#!?6MqILjzZ5(4{kBFE2`kq?^*$ujrSDEIRq4PaZ28'
    b'!Qr%E(?;+7fv{baRQf!6aX+%;D>1vIEm{o!rWT~ewr<oP83E<&q<;Tz>_9q8Ina76^TRgMF=Yn9nZ^xkjx!V32?$Ckd!OtOb)Ay0'
    b'2T{3U8X+F>X3QrX9Q+&o%zxU12@luJSgT)=FG!{gmbdUvmk{%!&q*jqQEZ`Qm%9*T-'
    b'+Sm6^;Wm<`j9DF91;rK!wQl=YE*Mp+@e)4dy|R`GJ=MNJtTSiC6ep8aTlM#TCH@Ma;R-'
    b';yC%C@t4aWEFq9i>MK9!Wxbt*TQdd~xW`DCk8P6jI$5E3N4*cz8ZHx>d8-oYTwZ4TYKPd$IJTA_hDQ%Duf-SL<L!lpC%6EVc@$!3'
    b'0kC$O1A`^|XPl2l2gEtaSZYxOh!(gAYf8%;=>10Z=NSzNo6zjvVBQ+vW>-hs%a!J>>2h-'
    b'I9qV*vN{8dzSq(R%!=XIhIpOQ3!YfRhkIf{mAI*!L83tt5N-'
    b';UcnQP6O7b2dR7);(`i2340q(CoV@k{r`ch&**j&(ZJ_;4I<VmSSPj^6sOn@UX5m&CG5n`=pMt;~HgV=uoiEK=3|()f7dacDhXFK'
    b'XamI_T-(oXeb{KI3Stw;GPU8%XBEGrMgF)#ZVY(FeS8N3SnexJ(-~Dh)#dF?fzR$pytbpeQ1D@35(jG?ZNJ6`RCttuz9wk-OxcS`'
    b'@W6S~)wg=uKTRv52ih^2g?jt{Md`jCp(k{k#)|<$8UfS)NTe{&GX(^zUz;;hW5V%M+<mQ%YHge77=h3+=-'
    b'};|9NWoddxAjH57exthliT8<%eWy(pJ&QHGKSI_ZtxqlR|2`u++pl5?_9UqLB<m+<3C)~Ux*V;Ne0WxVXJLMpG83-'
    b'I>#=$;gd!CtKHy=DZ&sQ=WRU=gUeK75ucV?Q2+jee|?cBUXr0vx+{IYlae!3EAA-bsw-'
    b';t`iG%}x^dO&JVGi|u{d<yL(;^r|d#&`_cro?SDlH<S!FUp2Qax48TmX@<<bP(yX^mw4loC_cS+#_iU3w+s)ST2<^@x309?z^KMj'
    b'q6y>M&2=&OoEp=6x$3JIw6(K@07Dqk3~FSiuLM{A5?2tk&+oSrqYlbE-'
    b'W@^Pg`mijj%oaklhnRx)WrAQ{_1n1LV?YI_R1eXM0XcGl=z_)#WKjx5Sy?^=vexEfWugT!?b$fEOYaw#FF_Ijc7yVn0^LBx|c}?Y'
    b'igCu<Mye;aiTvD3o)VQxF@!)UCpvSJ^^md~jJcjULHa@6PtO9Qle%jithT$Ml7{UY{e`$9p)!8)*%T51ZsEDOX&z5_k4Sdo>Z3Lo'
    b'JJW+x*ygYG?4~2SzRGP224+Hzy>~=U^-'
    b'(>>5_|lLpghgpXyBJWm_4tH^e%@~BP9)oPYbjjFY_#w=Bey82IB=TL9;i|6Y9b=s0AU$ye4(8gzMN8+|syEi*oZL01Q<&7$OjHa#'
    b'Nw1xFn|8Awr4I(E?=V`GFlPve$(9cK`kkCmNMH&`)>MeqRq^Y~e(?#UwjvEkYLFPq1UxvXvXqggmdaC@xT8i1JNF#egpM8~8E7Nx'
    b'd{-'
    b'_FC^r(*07h%q!cP@2R2G~>ITv1l@d6#Ur6p*aa2WMvd5w8ID#_j`YVPSZ}yw_1Qs%zm%MurTnc|2XnRstwyR?}9s9k>S;NSwd2*Q'
    b'&FOma<-_Zn!+dN6BBrPeEXNGPRZi68q$JlJ0Lj%o?67h?DuDw<wmxA^swCk}UI<nM26ZS-7s75jV&pe5=cfC17Tdx@4K-'
    b'`y+RuJE`svqJOjqqbvyt$x=T|^C$|vWia=G1-'
    b'`YCBJh*K%cEtsjEW+SymX#r#94;ReBmTsVVSijVe=&t;SWq0aEa{l149ljkre(cE)L33xG4O&lLhXA<OKnkMp>RO(l7-'
    b'$I?H7g<RBq90CIofE!`!++nonRmL^G5<gVAAS+kBcF*GZRVCj3l0~6+vvzX6w7$m{N1SAc^Fi+e?62T6Ar&#2G%D$5<bKs@UBFg6'
    b'rn)v0YBb`k=<dGdBL5Pt6$5QHsXK1oDKfmk^b-wRN<aRvSqO53RtX*U(!S`SSvN+x!wuV^pW~ynz-'
    b'`CE5ZI;>`z{Gh6CHU&#;SRQX0&l#d0IS*cS8j|ywM3w53|)-'
    b'5sJgFDa&8?PHG<xa%_^#@l+8|;aW&=YFLyT=8NGy#s2t${n_`yORr58d8JcM?-'
    b'OPc3e|=0g4}jIk7UVa4U0s*it~%7Y__jUpFkjJ%m#Hj?`mkM9FBlLgzA$fotV>zSZ=n8FyBA{(YqEP#e`uQg9!_Cn{!ktEtzWkI5'
    b'RZwD=;bfI)sJ$_XDm}HR!_aP02AS6VGg(ON40@fV~rbOD_o(yYY(tNR}rde(wY$oW<}y;!zoHLl}Up^lSNn(xKZEV3^v5t-'
    b'iXi##03U0RU1_A#jgrt=7KXU5NBwxJht>j!zGhDm}N2a*^FNlFo01Z*RlVo)43kh3PSP$jU@uMG#wq2hDD@FcM&jS!F}bwT5OD#l'
    b'G66nSK_M)IaN2av9Z3gUc(s|tzFf4$q-hs!3DmKzA4}=4U5ywbUuBRaj98E%&Y=-'
    b'tX`MqCuXhJWmMJeE)b?p=4jJn6~fd|jL*lkbdI<uKsBLScA0E=a|`)c8(N6TKA@Gfjx=o(THhLYazj-'
    b'r4Aot}k(0ZLHS}~OUo%4TdcYK-rAej72ku)$^FHq=f7X(4jy2Qdi(^d%%^feirk37xKSh@eOvuNE8c>I=Q`k3(vFQ^UpzBHsdMTs'
    b'y)hjEjf=kUC#Bwk6vHM<LZD+BAsxdX$w^57uD#G(e!Q+pD$EOrL7RZ0R<Z*Y+T!nLQtzdWNGPUW^&Bj#67+P1?y>0F8*Xhmm3=2-'
    b'jzR$HHoU?O_iDjf!lHDs*Np9XJudS49I76LKBYBu@R4XYf?>O(=DJ;c^J7rt?Ld^WQsdRin<;xJZxEK%&R}VjnqPZ9z&f4OmjV78'
    b'3R`}X7%Z8iVTfJen6}k6Ts#&Y9{GN(63lpBb4s&wIOR4}`t2h(tpovy9+t1r%{|M(@ZO^O$-'
    b'KE9pZG?8gHLKH$Nb@$jH`xi*rUg$KT57smVm_nb^y^8fr|NHS1?vkuH1$j~2y$Iqz`_>KvpXKCe%!^?n*7czL(IOt!y3r?9VNQyp'
    b'X8F+pWNcW8XBKuL&-UKG`ZpxVtC0NRG+30+EJXjLu5l&24H(c8XdUR7-1ynTv#IpS63cbt@-Ljn41EVRm3?-'
    b'FzJ>m&awt{yi&i<lzf90|535|%7u`w{#-SZ64661!;fmwAJw9-'
    b'QNGn`4EU%R{ZTRcqhj<iVjXj_=<C&q78AC$l+nS=s#U!?<Sc62*dS+DGv6F?4Lx>rWp|o-'
    b'_xK2=Z729BNPm%n^qQIFqUGpc{lYo4%C*%vbkVI`;^FSp-L$M)S38^&o?(Y>s?+ngi-sNGI-'
    b'ckIk>~i~Vje`%eBnf=<ssMRZaWuWYvP9g^0lUIxJX}XTEh$bN|PFn-dCGb_a(p5q)m7AD^1(*h`-vb-'
    b'0A*W^V$6RuR3=#bl^&pH=`4-Hf{ZQ&GR*4EUq$Z>%r)Ccet6Ymz&yHndaZonSK-'
    b'#eR8{Q_W32nF5~6wH(M3(T~tT3zB0Y5DkvKkLC(sYAi|%7&NRpL<sM3SfQh8cZ}Chb)V^>0wr23EvvpU^FIl-'
    b'isnJd6-*YEvJ^HB$?4H5;L@Xq6&^*K5N2NB-Ga#O&f@9kK;}w_;MB~J!9;f&Sy#(7%C!1CWU^`v;WZ80>UgxF)h;3p~A?o>&Y+~b'
    b'>(VtLvg*&|r(#4X~8FY>guvah1G|VmbBA!pyLQO0QmCYxiS!YQu4R7~G(IvB<67%f07Bf;We4;Rs{b^9TG-Vaba|P>)1qSb#vmd|'
    b'=aW_kJ_k5c-jzGnN85!bEw|Rxm%xMSE^hr3pYK8)IjiCr^G-FsVoD4L-'
    b'Loqq?Ji;VpE37~&z@<AHv5hg$%ti&(V}(L_{wQGlJHTFE8KWZ1F%l0o1u5-'
    b'ORgK~y4wvy0Y@^&87I88~0#?rHM>X@SN;(bBhji50iTPv6bQtK>#1gh~&wS>R59oPV>*><U%@bf%wPTfI4jUs~n83Fc**xqY%__I'
    b'@y_j{!NJcg~<u<H5i*g#0r7rkE0NN0WT{2@_%=62kukc|5418CiwO%$9iQjk~Tbf~9#bDEfbie{I^_)sorz(iGix3-'
    b'*jH*0|sAVAB=<eN6YAxDFU3>YtJuP2O|LmX5oO(R~#p67lkQSZr1l!ZY?Ycu3>`AiF?aq=yw=Y1Ue{s#o1n&K`M@^O@n+Pj77L35'
    b'1VjmIpjgF0x(S`t=3XNiYAqZMwW|j6x_B4|I8H2N|R%Cxd<hM1ek{T3mbeRR|W*VM0Y+nu~>XY8iG9OLP%k)ki$~#k63M|w!ZgNN'
    b'VJ~V8Mz@kG{Zp{-SWArqd&9M5Dvrqjjk6iatRY@89w!~A1$?RRKml>WD8>!@s!M$?_|7=eUMHBIA5wSn>h=)c-'
    b'&Eb(w9SNsoC`BXt=kQbPNSY-F7KyF>lLoXW{ZfO9{Rh*N(;Hg?u-'
    b'b>vojU3xCC7VD$uT(0{3CGin*<Ja7ftwvLXmw@O=xQd$~O>*j5Mkz3q?k@y>7v%m8<nc;ixmIUx)A#o-'
    b'Mrmdd#$8YEfuYklR)!6=lN$ElY(0{G)>0C%L0Ps{#JN`%{HcYs~5#+8ch>{PGQZu)Z)6(4@Xd^BE#@TyIIn8>zol2nc$VG(Al}^U'
    b'x5ZP;RXoSYL%Udf>{dg>yBS7W2dxE^B(*HmOB1kwP|YLskLJ47qEx6#6j@EXCXCFVOEN==RBt`v%pzsvft;POi6$7PxbUO+pbtGs'
    b'g_C3#d$!(y}1Qs#2MRwKU^=|C%3JEUICM_kngY0d9RzCIUV#RlUXjMUAC~`aHyD(w$87ea3`!t@orbFvX$!qQKg%E)fJKtIzFWAQ'
    b'3i*{F9n>#XlMW=|(Pa-iRhPOW;TuD@3CZ%@rV0M(ZEV0a&kC`?)z5Nc1|o*2$X4OoqS%4+Y$@CA~!L;~M>q!R4EnS|-'
    b'5i$Vx>gbEtMmxUKJDBlA?VrC@5&4LxSVfwW^3qcwKNli3|M{EXDUx=u^9`uy7XvQA3<Mj>Syd3;2aeb*6X$5FMb(m*4;%9?ZR8n|'
    b'j%z_<g|w2fTR0bdn>XoV48Ab@bxCo=k=LGHIJQ+SST8x0&aE14*CZPh+G*Z)O|YEm9)2p00<Z?VC{9#%$PO)cnZ0(;EK8+)wu29{'
    b'nwxWl<zaEHN7zpc-pa0MH!FhW<)3%-'
    b'nW7tG}k1}ZmuQMGEs+o7fqN^Ij_|ELc_s{A9pT7_>ldz_HOF~&V$xDHFKIp)=0G0@sbOg~b#ZtUTDurt!#jhf`I2Dye1Ppt0conG'
    b'Z92+_Jj|0p>Dd)kY|)81&4mF!r8Td|+(Q73(99=8e5*uuN810H>kpBig7e!j9v(6WFLV}ZGmcYzBhI#FmbJQjC@Yd>vRmN3>-'
    b'Gd5_Vjpcf**6NjU)mfX41Y<r$i~GtIU`gNljQq#rgQ32M(c9~_=hyMuV_Qb`E`NrGV}iw-'
    b'K)vF(4e)1%hl<s;p7{;8g+3>Vri+6uj}-'
    b'g)bwRmpFOegTA4B{%dOb3Zx?FU7Q`p@krpKdkN0SKP9VA4sxjMb8R0Kz&e<g3bVEnI)s%4v?BOeR+?eV^`#`wP0o$U*Gu{*3aLxg'
    b'2iF!fGXwS4FX3s!bgPQoIG;l2?Yw9jt~F#fsWFVoUHk2raBx?uFVG?>l>wy4F{J>Kz-ZF%=?J;z#KRy*E2txt#MBcA<H?8qZi^U<'
    b'dB5v1c$!Dgg4jovLIvdzZZVKcRuH0>tBhK;UiZtE~#b(@1M)*8F@<A`0MQ|s^3qK|5%J^JDR{mZHz^=U6hv;mv2enj}~5hkU~)Ra'
    b')<{oIV2*Ge=uGZHX{`xojh_HT+JKe@3{_Dq_8O>VIgJWOK?!UbBnCben3(Z+NQF>$rglo;g+Y^;En`!-'
    b'7F9%U6`7QL6rNetxXtwk+4w5&By)sXvWaJUuk#6W!Wazw2=^FYT#z^VyxN6dg71C6{96fDXyzlDP$6$NMG%6r?$x}c?LuyWiZDH_'
    b'g7v|zmx-!Qj=9w>v;{Y3V!%BRpNs@TE-XdLY<CmFq4W*j4C^#(ZbV<jU2T$YPZ75hc>Q8BkMN_tHHV)>9zjYu|MT&?=29@pDwHAi'
    b'6=7aX{Hv(NOR;Brp2ApqV7OzgH^lf0ztVMDJ9k>iGJD@-'
    b'i1AxzY(Rx6N&_T?I52iIH5nn3r+F_FR^DVk<?jd#^EOW46P4bXzrdg(E}^mDbv+zcYrQt>uaj#qH@YgXzz+f_9NZ9J<YYxg&4QkS'
    b'(XREN#rl#&!hYrL)>c<E_c!yX2&wm3A+9wp^D9#Dzd-ePfPS{I?R#r0p&;7M2F^6cCvEPxjsd?X2wRsMuIuqdSq>}C~QRGm)>O*J'
    b'lG1zI%3@$t-'
    b'8tfxLEIv$FIDLeAKEB9i2n(u;RVM{n4fVGU@aJVtCSQ`T*k1Zm$jNmytzYj)bwfkFh9ZXr2wFm~kzZn+uJvD=~d%GE2N|XDC>odP'
    b'v0LOVy6K0pKiz7jKqK|n4rmqUGZ-'
    b'M$%SpXU*aMHf4#~{)(VP+Z39@){NHcdeawxX6&bDs?$4!bpv&|o8Mjx!`yBL+AwE>U|SlBw{J>C{w>YyZX-spijJ8dbBMQl)H@v='
    b'y!PGKgke;CcVxU$)V>OlkW`DyZT|0A##<WL&tW83*yJHGhb?Z(T?0SOEX+^MI>gUA!}Xo2$!TT>0jGDD6l3&sxwTlL4i;z~#THh>'
    b'KnIHv)q4*T>{g(=_B;G&QLBz~OnAXbvQiYpIzLN!QV+BEXXrX@U#4Y^x7a#%+pU;tT7+{;doZv=#y<AYD%8^_va*TaxqpEfIg!RI'
    b'#V#axMCpZRd1SY@g(e4#h~Zz?^BkVuzlV01Kuvc#8at<)+-1c!GyrjZu_8JJTBn7Y3Wc1bTAeEPI-'
    b'i3wmyJB_}q=XbKnbS6b$v7N9srZR-'
    b'u`&ycxPROXJ**9e+3Z$mi;L&~ATPc!#bIG_8r^jG591M#c}w=lsKK)F~|&!*UBk)C7OQguS+mlAO<xR?mTM1flB@^5fMdGqjyaAc'
    b'?J>CImc$b?oU1-Cbks76mWBn3P1MwRJeIi*$c-m!;W*UaAAlEeiXT?B#6+k`zbsng~8MA@SRziv0=>z<=7%M-'
    b'}3w4m=rbPofVB5Ds>8V{Cuh4V$NCgU%Sq^kFN4pyGc^}Z{)tUX=oeLKS{n)OecM`o+N_#8dyZ(lW+o}^Sx)}2tdV=k5rbLi-'
    b'ONqPIHIH6v<SqNQ7NyvxT-QQK<oadW?c7>66qr1b~R!mpgu%&3a`Vm%HHmjD4-z+uNO?$H_h2E|^-'
    b'ub&4ot32OZDLsKI_K)GajqK$dMcUod$zYttAx-'
    b'g#m?0_*j<iyESDDBh0ljFx3{T#K4f;C&ktqKdcwO82K~XHk1%K|u%5!7sS5ULwyW!NcKSZTc$p^nNU|?Hk%c~@tcS*l)bd*=3o$g'
    b'!6-jmjIftF@uE#st^Pj^#?8)yw_{awz>Et8D0gc+C*>GM0m_<-'
    b'?ld@b7FM+jUjW_Y~)+MaHv9Ko|IxM1IdySxPQ(I4&Z1$s;?aXA1<ZDJquAX1{c7}J5`RRvFAQ4LI(gwHv5@`)`iZE%e>$%)NV&;B'
    b'6qR6g4@OC)HSEp)A4JVHKn=nZt&rKI@x=j7RB@UUVen$K>bDjCp2?ICJgFGnaPUg(RgoJal$g>~~ojJ_sCbq%txemMX(O&Ns>x0v'
    b'<`%G+AB}3L;FZmUgJUr~k1NS%9nUmoYVdoJ%0dyw|VwqSwdutC3{f&h6w5yS}RM3-'
    b'{&n^A0w#fDmsvK;yhrY0mpT&~eKWmHW)ar0S_8<A8I(q60>uDkucbvd=jSyLMwV@`3kGH*V_O_=^;p0(y*rT+9*q-'
    b'?=qhy69XapSn2T!w!zDoskf7B6wsx{8bf;#MKFER$7QNKSEd@5lt3|zie96)m(7J>#kAt{#!)s)|>hfVU7l&e+@z|W@h$n&n!(|B'
    b'u()5-S&kG$0Z4dQ@wTYB=psF|A2B^oF(3jt`tn}gb7(;Y?Z%>1t99hS<pj4|LAe4AKt^m;qt>g^qC*li2fXSH6F4aZY-'
    b'8Y=5OjP+t@ix#y&12j_$H4Uj#XJpFBQQd{<e;or#<&bM`y-'
    b'HnE_3Bp2er;(w@?0zGZ1Y4mNkh$Ppp_xnqNzowO4J`qzIszMqfTAq>z)(Lb}Ngei^pIA@`OGq%OZO6i1w|Ek;bFQA3w7VRRA~Xv1'
    b'%I=bOwAXLnHUDL{~(Vl!2Id<yaF#bXipQDpR{dCp1>+mcy?Ub+>LhB<+42G-Ow8e~s-'
    b'n!D>02;e^$_q9IiE3_M^4gB3GILc%Sal8T}uK{u2%BvlbC>J1ncZ^&VfF}{MAAiCBpnXgpLMZqVyA!vMz`T-'
    b'fj&Kv`89TCX1W7B`($S*PlKgnW-Ne+yk*IBE1Daj1(4_-MSLzcKA`2$rojo-AuzZ}pCtpqVy0U_{8Z&il)LcW$flbu*oru?c8wY*'
    b'g1Kg$ih9jGG#^o{F7MhBvC4fuRbtHASB7l3UrQoz27Ir&$QedSe&#aEYo-'
    b'B)`Wf5*P@Va<vz{71jdFW3?p_8YabunXM|^`O8=mc&p9kY$NaIxLwBg=9EP5a-'
    b't~ed^}gHaDTR;7xDq@&UOV_tW7Y&pFM;cLqHy5ykG`pXJ$dII#ewyv!8e;Kx8S4D!v;8ad42Q#n<u!&alJT>Ts2gF}Dk7=rAM`S6'
    b'=4)I5~d8MIF6#6y{O9*LCzTE}q&u+y{7>a?Sn9zBTZkz>I2Ajs83cbBCbk-P^ar-~+d-|ea$JtJ{6OmL%-cmSVAH1It#-'
    b'wkBqIf!%*Wk!#V+yAiEFLR!2eC44~Fx4tS0hW7LA*)A87UhB6VZ+KjZj+Z)mCz`fUBc{w=t85R3?_ZYB~<HJy6?c>G*LP&q^^NSV'
    b'G#>;6JzWu{_2t?u%xE1z2@vJ{^qre@dn!E+5~8hltm}i+NDdDhL6<uuf-m2_#N@f4F@i=EDl;{8c-'
    b'{M0BSIG@oxssIs1dp$zh5mJ3OR0enI>q0<kD3H5evvTsVH==muEBHM2vx*}EZVVGlFJbt<m0_1xe5=`a8OPv|xTq{ElZoo_^#m@3'
    b'%8?>w>gd-qp_{+>LrOAb#9C)*(5p=%Wg@Sva2vb698&t?Viz$5q@*;VMug(0G>hAlekKX3HokwN2@LheG|5)pEA2&E15ly&E;#F_'
    b'%=B(+J@B@fuA91|r1><9&<jDZmd!KV`GOlsNHz)$s=Y^bMJQfFl;KNc{Q)^!7_oL)2m*1#eocs&A2%TxH@J(aPLeAygqEtHBxBt4'
    b'a~*;-Ac`GsDzH2=WO{d}=pu$vbdR{{(aCz-QPIfzV;^!mlWFnWj?mP&fJ`%w_GUtkSX%Z0BIzuXxS;(0&eG?9b!gLFo>z~Z=m&sM'
    b'}Mx-j3?KWwNcDzDx`Nt*5OXSo3tsY$(48w6nN&J9B^YHx30Y%j2GFASr|X>TvGZqE&umi-xVYOU>PrX6&%{Z;aP8Vsygj_DVnsR+'
    b'!wHta>WMsO6`C8UhmeUVy(n4!{q&r;MIfvg0qvlJ~ZkNMvoKnQ;-YZjHa#W-'
    b'bZO??55z2?z@{LVWaSo%#q<Ky%|?v%|B82UAk(45Gzn#_);x7#PX2eP-npWZ0Kpwg6H8=CP)=>^WcQg3K|5#gt4kCqm9gw{g;j2q'
    b'u%yhaHpP~eg~CNc33dXjBRE2DH38piBhKbx`M_q++c{>#5gPiw^^*;g82DdZ*WBFj-xosCJOc)v=%Vg5xkkZ|8tZrNhr`I9JSW?@'
    b'dtRKk#vtT6u?7S49Vqyx&V=;(sc&_9F_fWJ}?>n(j$)_&Q_;#tV}V<z<(QWHA*+U_#rBLWjdI7a7!trd8?|Jn-HzrP70CrjsPu?&'
    b'+e_ubIXND`3HNf$*L7J2F|f`Fu{yU5c;<mQeWfZ~>rd6CbTVK5J@5m|;Be=@t-S6Q_>W-'
    b'X9$f=x5MwCpjDJN)~9SlintPed_1CYuM+77kuj-Y9$ARhw#6J-'
    b'jdp9ql;Wq(UPK0XZ|~>;L!v(56C8C@d17?`K<QNk3iP^#*_c4=_|&aGNzHNfCfx`~LU;AoUh1m5FfM#<#!!2W8ya5jCa)zfn}(+8'
    b'Rw7GG0<ed`Po7t-2`sF%z3i<sq!{eJzXf;qd>n_h!A3<XF1kUn%H06wQ5!dAgXH`*d-'
    b'qfo}8#IuQ`KMtG+rSIec!ib}+PpF`W6W=8W}3Q5WG?y8V2B#k`$&dPHhM~9<JkB?VwR=umyQ1T}_wWE*eD80~k)6egyzu{`>&GIY'
    b'FVeD*XyEliowhxxjzVKX=6e1me-DW0eGmK;>SkmqET>JIq(q>89N=ke4a1!wHQ}6@%d`&`io6~8ynG(h{6}mDzaF<tNI7Q#q5%0@'
    b'{ms&}Lv(;}hDxIFkDZY6CPBpYt@E(jDV%uPyyy`rtC?Gf_#|dgpy^a03=wa!t17GydthM2k$xs7sRAzlVPhY2GdP3>DPGjudg<VV'
    b'SH@1z>*okLCQ=^^NHdyVs3O<s+G{I6}MXb=42T!6=-'
    b'cZJ{mPiLeHE4u1a294Qm!mZ%BWqqs@D3_yw+)Z@>_t{G?WSvcJP~)RZylx}gy@vDw666o_`4I>j*@U4&c@fY)-'
    b'$%IwTW!o?V|P^ToNVdCrpko-'
    b'|y|Lk;B?=^n<+BoDORI)P0V)O)sXUQ#R?~S5x(_fsf`Gej8MFza9=24LH|`yKT;w{)E+3!Z?xjk9g66D{xv@`HGDAU!Q%WInH;1A'
    b'#^QoVW>OZci;%h=OZWZyN#bpr&DsA*(RZyLi9d>8oxA6CemiB8jjVLq>U|49RhRa8K!2Szi%x%FWbU18DD{hL$WeAIS;bRut3nmq'
    b'%E{^4j%1V@o}e%E89OXPTjST$ZNLrOR2Wz*XIIEmrknxbN)bSxr&51JTMUfyA!<Qi}QywDRA;ec4tA>%V%?Zr)_F{ZD?efDb4S-'
    b'4Nb3(3lz^qzn1PN_qIv6c5K<vf#jLMG#sd&+}K=|cw4@eC$8^eF15q;pNWREq`{Pc;wZhO#3d%MFl70A3GQ({w7!hu+W{P$l5g);'
    b'dTV5UFvTtt;nJ!Nc@HPclPv;F{dmgHMD0VRl6mRjeZ<&CopmWb|E(XwD67=JcK!d)ru%;#-'
    b'u(|U+oy$CrSSu8B+N8ssStHEgc!}^i26{b!^F~4_RwHDB3aV4wjy>PmozEZ{e+ilbtjQ^EKg+lA=~sNzilb0O*}e>ueSbmmX)LBI'
    b'kN{h%S@Iu5eegtX3}#H+q3?*Nv5Y(hYZliyt>q3JM5v6h0p5mZ)V8Tw3*VJID9i{x{$54%U89li<=T-'
    b'8uy7sGAbXNsO>15W1^iDsJgyw3HR@GtM1?Q&CH@BU&;_UW8%G5IARwEnpkFy9c*GbzzQ-'
    b'pbabbwvM6R~f23aXn>&+YMU!oQu)?=nG>JYf7$&!L_rdKs^(Nax=W`uS<PZ7yw!s)putD;}te&2eG>|Ra%tTXdE5F{ha-'
    b'db9usKI8bT-dYSQLHm9z|<Cb%G&e1C1&W5{&baD;_LSL?Mq!q)JidIi^-'
    b'QZyCnr=FhZUbm<WRGdjQ6B76>eyAz5!r`EKIRzLrOc@_zCu1R7()wu{ebaMd-deT!aHt*}RApdo(b$(uGVU)4y3@R_u-uCaCZT9X'
    b')&U)ywhQ!D9UFXg1GQ0igttvBHM4uKUL0uC=GdP;;kDI{|bF($Wq-*U7<{<-'
    b'77LL4)Qt_+D=71z_Prmkgat9&9z<bG}9q!f**(X!)J5G4tu$M1mS8y`*jZ8)<T4f?}eQ7e)Z)Kxx?@ijFRW9LV6V^XH98Kw3N#R8'
    b'PkaZmfdfg55x(`Th-I9w_xVr0dXO8Fb&#T_44cBg_k%psa-'
    b'b~uecPsn3v<^*@tD~1<9BngN22ofBz>X%({K{?FZ!Q?5`1iiVQk&7071A|t2Mz5FInc&A_-'
    b'AX^Pgw(|o%`<Kh3t&mqkxv~V9|Kmb4SjO^(~ys&h8()cTQWg?8ISd-DGLqi0MPI^JCFZkE<>;WO-k8nHqQOs#IKSy;+U8-'
    b'LVUl9r((cd&{ek+kl4ySJ^VC_qYt%NA-f)J6VqYNaW4-%-'
    b'eP?bYU$fFZ8;2rhQy!UAp#9U6MUVKfCkccLoOgkGH%)&6&enb3bAB>7dALZ3Z5b-'
    b'kErFF0&}59xk*(&4JhSp+~LFHcdl!w5)w=L4KGf`*L~dfS%jta>IqihHd|&{OFnHK3-'
    b'&egh+RUOmM6`m&AZ=qOpAH<|nfkS1Qkvv}3I<zk{-lC(}zxdng-bo0t7EJEv*zLR%$I+?1zm-'
    b'!c2+%p`qUnpa(iao>}rpoOIvrM0=tD)b+IDXvn?J(5>t{duOjeyXq!HhMa>(YL)cVe^xjPG_oT?*7H0bRQFkFBl~_JF>BiQoFVa^'
    b'51byE~UDd6{sr7nxnck<ACY;!{M<B93L3)apOER4aAT^<*X*hVZT$U?yQj?mNnz&r-'
    b'Fj@Vk^5)iD<l{+mc45^D##ZtW$#rOILCIUNtoQ2%^~;BHpyLj*WL{(^$T`LRM{km#x>~YB;L@m@)@E-'
    b'sFb2CeXi$SL@4&e%aaqTRLfTdkopi+X8uqH2w29li~pu3m~z+#s0K^*M4@Q@8@M)U(5P=d-SdiX1!^Snq*ycCG~D{-'
    b'84IHnO|<@vZmZmM)4g_Xm1Vz;c()m=hAsY&1Y_dW%D3}{IP=~pkAVs;X+-)6Dl0ON-4v>dR*%nd;^6IXP0O73-'
    b'6yhkH^{71}|PPaa4}+)FO%*(<qcfT)Larvlu<FTqJS#ljZIfN+*tZ>b7RwLT~vavu;N3m&?*EJiYJ!w7%lr$I1;3B@`FGZc@axd~'
    b'Z_6F|V{ZEy1{4dGXVb`E%P{eq{?w88&W1jV5(`hiZre0(axRUjxgukKM8lL6yBE>ZTF#!w`C5|F_=?pn3HPe>zUcYSVVj453$_$f'
    b'x5>&$)0hN%J=+^Q%wv(=JBdsUqn}^7ZJ&LhBi!rECIA&1NAn<7{ce+avXD)=5ugDM`V(<pjI5C{v%F_;i|IZJt(iS^5}PpxnAe|1'
    b'8k+O<zR$I4qe64f|SYw^%s<d;VMzou)8Uz?<S&`*YNDaQ$*2G8z?#ohb}1My4sDh$H7EQk;7kz0p=#=ZFx(8?1~pG*T3mR{>FEv<'
    b'Hm>De1W?H-CH;?gIXvT{80^>&Jd5$;6jlR{kv|2-$Qwp89`G@+^;7ME6izRbt3O(=vqHt?H6r95>Lub(7tmwsmXnw<-'
    b'C$bK$*Uv%23rM*y%@n>(!7?&$qd<3lv)c9@`k>=|kQ(zvO4y3^9T&-'
    b'a7A)DES|eb(pf+S|(L>GXP2&g%KTTchp2mR75ODm&ReB$i9lFaX7w!s^$Bvc&yKhz1k;R3=*$Ed_-o*}IrxW%KlS(;w-'
    b'|Gq_MP)WO=;zv|s;O+}{L@Q;;SH}Tj_0-'
    b'`QEW>&?mE8EtZUHkf>1$C>Ws{CBGkQ8;VgN!X@CGTh>&sYO%qb>VgJ&^8%1_v6+^tDcv@1|_kwp8`ex1fQRbh(Rbiu<*~3jjtFD)'
    b'#)?WJk{u@|EZ%Gu!lWpxLFqo_rr)pM}cKa=m8vO2XUt{=myix3@D;y4&j*rF%m$=y8_I?R>OJQ_^XN`yn=9OT~pF+rvNO>M@-'
    b'G*f!N^ZC|$|nuqo}!ie$|Nw0&o+=3`2RWwX9BN3$<q$Uo66Ua-%D5s(eM6swPw#ryevajvK`xf-6Wd-'
    b'RFEoY~$vP;KUQV|kY+-ZdPa<X2Pj?Q=d<}>1-$KjNp=YvV6^mJ;>JZ{g0WG=XI>BCN=*fO-%%{YE2X$#XQW-nd|9h8*DFu}ZXB6#'
    b'V9!j3yDj0)Ux@1r4JNMo6oMtZ`rSH^H^kRwiC4UzMYsq$(&_s?z2MH4Ciw-'
    b'g)tx5UT)wv8(Omu}(zrSk#&ZJToT|N2|!6#d&^8va|uzyAhH4ef3I25oj3+J;Amd0IHq1v5$nR#b6I2vJc49;DUMQVHJ}99JSnga'
    b'wm`kSLUjQE5hq(NQCWk%$Y2$YwFs-9w*+R3b#dnNb!y5*dpDnLq<GmT<~3N7^tcB=_19CYg-'
    b'UAwh!h7#2V#=xPe`WotDFwI2AxHsf}C6#j_#*fAE&=q1kzU${4k=V_A#cd3!auUyTQ?r-Z`c<nQS`5lKPkDEC-Xt&+8S(hiN{|o2'
    b'0XJ0>gsx(36Gvc$S8q&=_dIB9;@W5W&$eyjBQ9+}E#$OdQvhz9Hqdfc2<KGG|RT!x-'
    b'Qeot;3L{Urr?|b~@$Wb*;ZPx?LPmv*zaV6Ysik8cFnGF^<0=H8KN|$*u(v5UR0l+&R75H+wP4n9!wHWVd#jPqD7c`Fkdj5umDX3g'
    b'LFX!kytRh)?K6{wpAU)>uXUt|OH7QXmPbk?mNFvvX--7624G7f9*Lkz2csAU$nxGR$&{*)^rj){fGGV%RJw2wYu<7>n)L{T>j=H`'
    b'GarR+dyefMifktxi`@@+SDH#rVe1<pQf-}%jyi{lv`S;igkn)f94WQfGwcwv1S7-'
    b'<g>6e=s}^$j73Mw*Wd0l#CB{jkq<}76lt=|{w4mCNfTQG$Xyc(*VmXRNa}ZUqQbcG^BbN4RKlq*$Q@t0fbJNl;pgzj1R8hL3bVcc'
    b'k(iNpIgwjP@-Y&R4&5l=byW)1m?TXtKw=aa-nelWNS|4LLtr%S~x?*(2=!(%7!Du<PR+rD-'
    b'|BARg51U3)6|BdA0?2wP3DO#42AhZn#srI2Giy2H0x-'
    b'r|2Fo2n^vp$$SjE(ji>ZPeVj@BTh914}il(LKPGZWbfQ=p`Rv5sOIm&=HBMDzj42cw|1TnRYsk@H49S5!pEop>}6EKrJ!2?Dhu9%'
    b'q4Y-ua3hFi!okRE_29MPPE;9zhRhEM`jpvVExd_aD}L!o8YZ0yBgp_~-'
    b'dCv+o$0*8~HfNUg~2p$12TIzuNVWU7;v)FoK1i==>JI#fXT<*o-'
    b'Y;;+W^@NX|imHp}OZEY3Zc^TdrmqyOSfR8+X@$}XrSA<&i+10AnEKi=oE2OvxK?nj;QHRcH8alcgVfiFY^^|AfwTf?1=9Bgq-ttG'
    b'T}Vv(D@>>%P^~G|E+VfzP#kv5B1)VjT16GH!PHQWghN(D?YWi!GfH5|Eb-'
    b'V^ME$sk3NWOkvB~41QP4axmkMq%_zN>&x;((QaRYo8uEX~dNt}akgN;k5kvkA|e-'
    b'Vpgk#$dtjD^U#<4kdZjNl4e%ZNoD*oBwC764Z%@C~4PjEpqQO6{#9EMhN%lKT<%kYXc;;>;n_vma`a<w5{^kPN;Lc>)VVxQ`aT&w'
    b'2`UZzz_;%Se&Z+*k*5BZZEUMjv(D@84=i_J&|Kx2x{O*jF;FR)DPlTLHEL?1uo@qP2A|(!RF2wL)%%+zPoBaz6y*W;WQpK>IpI*b'
    b'1)|UMsv-c>MtIs;8FOQZ=hzVU{(BC!4ns!Uq-*4_JA}0*O&lYn8Q#^XQ~NL^{hQRTNVT02CC#4l`ac_Tyr#M~-'
    b'j@TMwp&dzd(nqtPK^=BeZ{2w=e?!ah|1!@_7Er3VP(&N~fQtCul$Pc^n}mDFRQw%pQj#|ie94?YwtjxE=F$XNowLhFH$Ok~s&C7n'
    b'Tt+CVh02g|f{K{F)<3&2PaVi;3qgLDiF;{$bjfpeiS-eth^q#}F=U~6uU-3_d-WQ(n+T2Zy4YDLv|jjBZ(>~45{Z3Aq@*^09jXDi'
    b'OWYn;stue;Ipb*!!xQ!A!cOs$yuelZoJskQZSwfX(#*4+QP%0AL5>|tM^K%9t<MdScpkw-rHCxSN-'
    b'd6||)S^$_Rd;%H74eT6ej6fAtKQ5|r!i`n}X3Yez6_-dOfnsv}NUS}O4$?4w&j~Za7^bb#LLrW|^-'
    b'fB(2UQdC_dBUCKdO|noET<3kt|TGO*+qD3=$Lx97%vRM1ni&h>XSooX9AM!bDQ3JPk*~a5IRs15X0r?fxA>FGi<h?{+|^pl+008K'
    b'fKzOa$QwtOLRt_+bc+8frM9oMS<_ZM@XTV;7up96O1PQDQIZ&Q`9^q~a_BiHwnycq%eWqBIf6oJAmVO^v09@E|}ua~e3WFf_p42!'
    b'sp66o_d2a$sE=-C^jQ+iRDg`IRiS6_+b6S6r^RTyYt2xoGiS0_fMa^;V>=NL`V-B6US-'
    b'K<dn9yoArMV=b<zTv55Aaz*8e${0_r&gS{)`}z^?-MHt+M*yh%u-V*X#_V$|uyN-'
    b'Y5}E+51w*0&!Y7_$sbPu?7aXvFrl4}_730ie3-iZ43d$QS3?>KUA0NKqs1)RiNXMNDT529qB-'
    b'(KRFRo$LFvU*8BKk<MWCVLyUt|SJ35zknsj(JUrto2z!lg??Zs{}IW4XiVI6&UNWye5`kIXN=9WFewO(;G;PVkoMNCL9u7TaTC?Y'
    b'Men71JuFRZOdx_VSokw00f~ZYNgvswh`cuA*E;xtB+|%u;wPwjEUqt0G!Ow2EjI(Ow$S$kfXA?RITpg*H#?hhG-'
    b'm$u)7BSgx@}*fAV=NQCZ`!4WwujZm5hB7$~IQyv(n7`A~_l)?^jwdUSO_JTxW14R*-j{?GQm}{;DmE0O7iFHT?gh`-EOC&5(%t-'
    b'haY>hEiV@3{+nQu43b=nB01j;w9Wo=w<?#;vI`x@j1SXZMl(5vtPxqzdkoQ8;qBE%7HndZ`=5K<Mvz>Q=Aduxqnkz38leyGd$@EF'
    b'v{>7J0{w;UK$?=<&;f`kxkgw5*|Q2_{8M-xDRAc7NP8KN}GG$S;5N@(;!Vn6|8>|QrWJ~nq7%;OpEi`lyGMbO-uw+x@J6oFZ>vtn'
    b'n(&WfGy1UrjX!(|YC?I_8LrWH*qnpQM@Cuo{kCzmnwbs`xna#rN5$XSu|T_7i&T0ujMArW<0!M^+U%M77WQH#88azF^Dg$k4t#01'
    b'Q`h5t5AYC#AKUWXu+@={0m2hqqF&akZE;2*heo-'
    b'q<IQDLhsWjG+1E9wHZ4kNCSVAy+>@CG@=g$aU(lzGMq#DTi8IXrnt8@t<XiR*4loD8Ss);z3#v^c_ND8XPMfD>>)Qje)*3Q^>gg8'
    b'v2LP=*2bV38`u6|zQh0AH~mPbWKi45{>tq$8#8x$fuVKya1TSp`IogQ6T73esTY8AnKa1~g{`GC-'
    b'O<P^Kd@K`D)x^)#_h%oN!RuHEor8q<YxjpR)p2(r1MbSJ{TlC8ADYlYVeuN7WD2)q_;sXKA@wauv&a4X<ez^#D$K>#;1x9)`5*Ri'
    b'-(aIN54!L@?xI|kRTv;RQ&Gtl~7gPwn08Rx>oQ}8#d`=`F<)}}$HX503+uiM*`5vKs(yN9QnE<E?2O(gCXOprS7x7b5Bw)S2V9K0'
    b'~FW=^sJIV=LzCPniT*nj~MY=Q=YM<E175b>f(|6!t#)+1#DcFHmBaUhh@S<B;rloqvr{{A^}9H8(|U9dFZ;~fB#-'
    b';Pc*&JD4|P#O_unjp%l3N8xFB}LRpAF*~)3aTaJfl-'
    b'B`OvoFM^Qal!xan?q&Bg2P;&gmN<aS6%H(9|8oJc5kkPqzeAarXstIdrMuBFiJvXb+D^QPPJ^?zPBcPE2!DgCcc9HV`B_<MTHBiy'
    b'cF+y1!eDPb74q8L^&a%}_k%xVo&76^7xM-@0QIZs>=GCHjV%&Fu}$_Xr$H-T8hN{#meZ!cf>l({gZaR2vkyMD-ah?ERb1LM%x8-'
    b'ZhxGEri5PDUD8a>#LKap26cw0*Qq;7CKNe5VypW9smI2@~{rzoib^5AUF`fC$}76F|5C+>aU_jiLkx-'
    b'P0Y|ZfAv`_nWmm8b}elKa>dgxc>HN?z(=uzb4<?KLdo{Z1D_`r?<w<bXVuiwE|ZoejXxqcKm$hmpS=lhBDcvYppM1+0ET`uOYQuz'
    b'wdH}G_Wpb{Ys7ZYuXL0j5I?wdYH)(z031{^QODu^hw#9i<7~mdYCsW7-siy`ujTlz2mu&FtmN4zfpQ~^AOzjOFf6-'
    b'Vj`N{O+p4hbC8m)3@m_{?TJnb0o(?lr6L*=k>gf7_+JW2g|wqqvtgva7kf`?WM*~D=AE7QyUOKA^7-'
    b'HKb>m0s=`abD@XrlMoG!_fCiMvnR$L=}P0_z&{Dtc;T>dAFws~=mK9&fW6c1vMU_v8oq_7tBXe>a%0?k89F1&)F;Gn5il)<!mFBK'
    b'(TGHmFq<!&=K8c$EGqd|YR%tjV0h3-'
    b'I=(a^C$pxSVRwLm)65K#nJ9W0{*1t>5pF|chIkMRVSk$*5So%Z+QxRp61mnm0A$DE5?I0C8x$f3b_A)F6Q1sJV?4!qP<7>uzY$Y8'
    b'>p1d*A8EQ74Kd-}<!q<O3(k?j-Le<z=VNTq(Ac0vRPYOyy6_Hzo$34wE*B;F(oX$cbvWC9|EQQlG`EM*`w_&sAdV4^3}n-'
    b'4X$mW}uG-'
    b'^pMb>4e*UDv3GoH)*$>x^zmjxjN&M!E83GZ}2TQ1JBH6yT3Mjt+mFqGX+Gnib+!+zJXcJ8EhHunra~+t~!IGqM+bW9~mfc9Hh30f'
    b'-<n3B47{$u)qMdAw8v*yBLkFd7_)({)t2h0L=;;AUMpU@(N@{<sG2}q(bQtW6VUOfCjYiHdvu7h>|c`7;Mx4Fk-'
    b'p;<B6a=%5MEfMyte*SjteR9qj&KwdX2;`Uc|!Rs%pqtk5uRp1|n6p^RZIkp|UQ6G~GSyD+v@6--o<4d2Ei^kX?vVrmRSAh|xS!sh'
    b'DBZ+~9-'
    b')nj8i!Z*LK?)}zUn_ulLNz+?1v+&MGns00G=R0<5Fx+P?Tt9*sVs5X#puz67RT!Ol*d*KU$n?bzk`VVycWUoC&Df82&WrZ0<zvvh'
    b'Pd~5x<o<R#p5PlctE71J6O%>o^-oV|aoki+RPCLo9}j>T2h7P<^X?`#+XM+q+J>5y*=_`(gObu1CYV=F1TP)%KL^UKFra-'
    b'~?tL`G3u!F#pnQA6u~)`$YLFvNPuiW@0Q!;SsP^;IoPw|ZfD7sCT{<wIChZpP-X_TGPr3KYaJ4|`nC+qSs}N*LRVgrsF9D`RHHb4'
    b'&Dk2q^S}^Ol;e<zwz10ZBAW($05mK@U2%+`Wu3eI{U38V^7gJr7_s{`G_rf-'
    b'6`|74@yoJOoZlNnpC8sb`2BbP|9mprtIZUKg8cW~@EXs%@r6A-'
    b'p>=3gABg6nliKNyDe^uUq4I_mqeGIp4UISoPB$?Ed6ws545&>o#EvR-'
    b'R;3$C&YU80Z0>Vc$8f1=ul_ElW8e0Woc{}gQxsVNFl3R4T`++Kqzgs;ek-uHZe*G4<{uKzk&T<<;`*EHE&jxXh1%Ye|>5kqK#Xus'
    b'r7{n(fu}7EzNt(cc9)VsPGgApTn#oH$>KZ;GUT3@i@NaHj?>6LhOJ&#N4LP2TBD#P!qIIN*gX(8IwLHSIV<{topXNkFAORgD;*ki'
    b'dbTEoxKp*eDl1!;0x^%m&8`C~y`E|VUw0#Y?5_Go0_<V26*WBAeIho{0*ghmsphJLvSVhoCgGaFQEOkJm7*v3WEw-'
    b'K*L9h);6A?;sxwN;p-<YQ^ImivP>#IA$SjvV{V$<tC?mH0O&7`jc2Z=wX%+vuz52`l>#0%U>OgR+*ctL_F3|o>p%7E&T1oacNgh-'
    b'tQEnO|`)NCsJY6C-'
    b'DZO47^mfhdTWM6s!9ZglR$&3zg<E11>Ym6Cy5DyHbfoL@YJ&tks3Ju?oJ~u?qK=*7+?(==QFp6Zna00Yyp5PiIV6vcy048WFtcF`'
    b'CIZp`@pr>oj0TDoh5eBpf1TT?~v8!Qt;UV1n-nF=u>)S!ASKZdgav@-'
    b'D0b(&jo=|QH_t7FFtq1+aCjFjx3CNus8rCT;q|h<a=%bE{EV~`Xd)d-'
    b'Jhzi8oB#D5ir+H+~qi7lYg&FJx9+br(5r%Xfwh58MISzA$Euls(Zs}~T`;|F;Yaia&WQ&JDwWc5)MdY=I-'
    b'G&{rh!Q7>R#7#%;6VsR!XXefKn2#)=%@q;ZI*cKi(7opXh2wroIB1^);J@$!qzfkkq6lHQl%;aoC1Er5HQf1VODBy9bplB33|wf*'
    b'y;yXo_!6`{3Ytlo>yM>n6Eyxu<Qk(-'
    b'~vUGi%@VxiR6P3;rN2YMSQqG&G0!s98kIWBW&^gH9%frcfUy8k6%*m<A}*xF7$B$6u3a~n`IPuq0%>}!p6>;Gey9-K-'
    b's7{VC<~LQ#2HA<EZi!m^Yb(xM(2UXCJ&kKHS~*!2`14UJ|BG&qn$VP47n=-!5i%KPEA2*-'
    b'CbPbm4qw9T!yi5xDXp*(_c|>VAnN7Dwf-'
    b'*!7X~tQD7Foag6SIYfM(jr~;Sx16G+xIZtDW@x@YUoh{>N7&2<o{o5h{rn<FAx=2~vFlq4XCE$M^gjPY&p~SO@_C+<wc-'
    b'N~!4&uU1rE3^?DZEqXY})H79awW-un6e=|Xm<EIKWZcch=Qt%LaIc|gaP8lqA|RNi-'
    b'p$`ZMY&*Q+0FEy5>#<J8{mKw`)`B;`E2$G-'
    b'YF(O}T;7bjBsevyaE%0Rt0@UY1K*^UHCR4*?YM9JlB1~op81(09_{o<VQBxyoYDCS4j;L8c1B^azBUQfCu$vloQ^Rg**v$c9H%oY'
    b'e535IAV|HrHPL0`lg_xbCeM+X4nQCZH4ehC+Js%>pXKByVLVDmD1XP27Y7o$0AqXgg1$ObYwr?PNY?tFQB~LO>-'
    b'+>lJ**X=dND4RBY51ZTtqW;e(uCd^NkoBZ1rChb1t4S4_KaebGT5O4v@0yy#HZor+Y0uD{jVmE<@)iiN!zyhZt&=SLx4%sKje2rg'
    b'48Y!WtxF$cc2Qq_5$g1kI0+*Ci98z&-'
    b'(eWeta_ab_npgXtdEOX*dtewK>ZNCp~vTI3GddNFHf`5d&JVW*GJYbxjT~t(62d1qeP$?R-jthgovhgn-'
    b'7)PDyT>Obry~<Q7RfHb#a>$vFs!Fj27aK@BoO!cuxIy#sMdz?y<!h)HzBMk0iuO;+^A53+vzF}TC}3sVMoN<7&t{oCnDJ6}3aW)9'
    b'js2kku7*J&}0?ORhz()py4xBCjTl6QAGYIvo9&xQPnnXvgGGkcvZ{}*ZY0zp@Enq3aMI-2B83^03z7|08f-'
    b'#gC;by<qMKm^g8B3~+k=xBQ06;Sm`F?$yz+>f6Z>9Vwafnb<9ZNGFd%+WM{NUYFn#im`5*#CN&f-'
    b'Xz^7YN^&6aN9>8%NXc@!=}35>s_SQvLubZZ1ok7YG8F)8@_~fODyGXQ0DN$M(D&DZZDqDHqnl&Ubdt$?w>zS0`v@hkE#bRUF2Jb+'
    b'nI=gygb>dja?EoN!;zy?ZX|E_=UUKB(g5K=&_@uH&*~e*ypH0@=S<vD7nV-'
    b'~&9puM%JIf<o|LDx<|TnMExubw**SH&*@TC2Cszf)Z9QQu*+>!dAHlQGA}^4G2}qomgFn)rI&jGp`g$8ZVP{buv~b<F8KDQKVUNd'
    b'77<m$m)iCds!-q)K4!@{nb%f9hL7eS3_}ou*+|c>dLIH%**E%C{i!KJoQ#*XLWX-bXdJepyCDe#p({N?$Fmg-'
    b'(4had3n;V4%6x|eOHH|iyK2-'
    b'eq&UZYIUi8jPt>A>8ROuC)gjbJ#NGOx2Nw{UkIgqywuGGaz7?H%`>0U%oj2oYQ1_<e@WMWM=X7xAKPCtb(Z7mEI-RxJ{-'
    b'T^CN{U6Gnf$Wn!JudV+V{;QHN8CXci5yB@XN>C<Buf2_j5`{vF^u(o-'
    b'sLG~4P6#QJygSrV+U0o1@eDz7{fpzIS$005+Ke5}zZ8JHH{1}l{H*ueN;cu@nR7H`kx|Kg7F@?=hZ<mz+(+{i&*f$yC=iuLDQNa$'
    b';8r1Te$Ppg=uyjen*#3Q|;BBfGPUQ-)E&~y@WB@rNFa7w0~O<~&@Vghy+HaLkAG(Qe|GR2$>jSr1tblxv-'
    b'G}~qUwP{j}{?Qboa8nAb!Q{N(u1?O+y;F>=*!FjJ`+ZZBhC4qP5L=Vq1K?U*BYjQLzhnG`YxuwaO!+>h1VbV*GDs060JDpdps1`$'
    b'X-%-'
    b'!+A5+_l1~=BFhufb0z(E{A2o0V$|TL&T!>KWZa3jcz%?V%#G_Q=MFtF;3jjVk8I45TIjIOm!FWqj3V!N5*9N$SM3`c$n~WHp7z^;'
    b'4Q7Cboz=)^?`VXG6Ab_Zqa~Nb*r*!0?+W`;rHqwv`AHalhO8reGH4OH`wBei=bk|`Wrj*($VKZ?A2JeaX1pXJAM%YMUEl9~&ScO5'
    b'L)shRZ7-'
    b'BeR3M`cgqPz#SlX%Inp|h5ALAob~c5ZtXZ<&oOSPI>Ngbd7*83YnDM_3D_lNDW&fCz$p4svy177zi}!Ybo|TLwPs@}gC?s_1r}=+'
    b'-E_a4D|7JwKWW7P9kx3+=a)*ly$YPSH-'
    b'A#`!qr74*E{yy?kMnu|L!l`e9P3xs3t>gToMGk1;Q;*pr21`)9B@I|zUg)UxCrzm!RNn!nsDlXg9XVy3(0?b%QDbAP${_Ge9HU=E'
    b'Tg$U~iJj6z9L8=8#1tjYj_QEpb9B)#e4ULYLt-Utct&hQM8ucP4<sMBN>t*v$TL9{+zi=LH55aX=%EHzC-'
    b'`8ErX1Bh3xDES+r}=wZ*y9`l?{X1Xz5!Js1@;1OQ32$a-~>VmSX=-'
    b'Bh)ZN7P3hKyqZ)Jv0EAE;RmaI%+u8Pd`<=zCirLGXClC#nKS=#&u4-WPIX>UsX2MRJJ`r?{(egBE<@$c}^!V&{G%o-1qe(|qfH_-'
    b'$sqFbB*mJTy-'
    b'B`0(Z8B}hocEiwyRBE)T%Bd_3(0Eq?LH;3Je&zsx#Hu>6$cwchXT*Nucnq)uH}{Acb>pnHMv$zu2qw3)#S_Pd#r_!Ya!%X2>GLBx'
    b'~!#*YiZ+J+W0S#*R$3uuJwv*z2Xm@9<`PtuBC`;DdJj+_<&TlwVH6PCS0otze@7mS|+%b39e;=KS)a9TKu;b|E<M;|04O4hX9d0Y'
    b'4SzSCj8tPvQ^7g)||7oY-P<TTQkbmvXwPoY|R&2%U0HGu+_a?%U0H0ueEGt&E#4$xz@6kHBW0TTUoQP)-0^GY-'
    b'P={T63({vXwO(LM>bQ*DYIFKJ#BQ64#8x6$fiZ;t!vZ_$^IF1943t(0RcduN0rq1Z}l(OU0<I>A=d-'
    b'#Fq|2?&f}X=f}n$r>|T;&gMET(%0?Xl!kSw-'
    b'|Ue|r`erCk1g7F_>FoVFze;dE8|>vNCDR?0Ibf#wAqR?{q5`a_B4U<(^I&6c)Dp~*0Lmf0Aqn_lOpR01LYGDY=Q>q9JJA(0L{E;?'
    b'2aZ1X+2UlV3!i{dJJ2lNwPO?xf@G+tr%|C8GQbkQZt#S@37A6hipVj0aL`y5mES}7_AE_@{cB!93zP+$a{eUKXO4~YY;MuQOXbu-'
    b'YHPAQ|{lCChFVj>1J({By<zkk9SQ{xXpKiNB5h(kdE&h@`E?Gn{3LR$KN=t-'
    b's+#N>${`4_LcV5^?z+(*KO7*A>Q@x;m79l^HWqU8=4AE2MGi4+WHRO@R``mI5)%+15zvE0C6yVR0S6W=8_^1kbT73Nhzq7j0Z*)i'
    b'ZU_$fSgA(YcsdjU3V8J-M8J|`1PGx-Jd92eNM{i)9NX?n>yWlLb4Z#5FItVH$Jp`df0W@<HfC(OVuVmg~uCvyS6t#e1waX35|H>Q'
    b'yhB0R=^T87Sxn!g(%IPilA5|rz(=t!j}kcSs)BE&@CbdF)b+;U9-8ME+i0k08$T=?hKcfD?$al3K9tjcn%~yiX;JPhG-'
    b'962<XD7WO52Pa0CKIkW?99hQcJ}zHfKbpK2{KO)7RISPE=_jr`ba1CQb1)-==m?fKR`-'
    b'ZbP7oYSP2uRi;=+x*Ms#|CiXCXq?vl>hSmhkabN`1Y;K`D-5C_tg{3H892-'
    b';~ziY`NkSnnpmkhaWH#PL=eDy<WvL@&?xsJa!g6EhA5$=S0J4Mq#&IRmKz}*Mn*Tzyu!p{zA&*|C4&VBw%U3lv5YXE0op_q!*1fB'
    b'uTq3fgr!zO5R{Jo+ZaJe43UB;Y!)UKi*qLSU;o$t_}~AwYm!uos1(%dWO_jXbY)OSK%N8;2nJ+UYLikcYye1r!ApeTg3&lKVL_eN'
    b'<w+uHVUk1)9>M=>8ZfBpnxp8s#|i}ySd~D*3)rPV+zLc3!WnXg0uN#eAYKV67bc15b0#Sf-!_+X@-%$@wr-TE#F34?-Kwsa)b4-'
    b'@09oJlQe*qqECpfv3~Y&vxA)I>S7*6vo1lp`sDXWIi2lMf)ct(bcaYb6zTfMBozUB}{&B}C{O)FzHv2Xl?>hax<GGP^vwfkzF|AN'
    b'hLuFq%huP8E!Jk(l{cETP(aOQiwgmyBlYrUw%BY$`v^rp|WF*NH=bY38)N5<F6`TS~Lzr--95DOfEdVgbl1U~&Q3k-'
    b'l7{8Icq?b=gwl^0UJg|;89a{PTgah;c$D?_8Xs98jnSO3SuYr==NfPM`WSkosZHW!#S6(Xn+_s1HADOxX;xDi{gq5bw3&9M*1SAD'
    b'%fr6;Q(nR>IpqK{%67!h+Zvn()5cYuBn9Cc!OjL9elYE<b-'
    b'iP)(tZ!_3XD82lZZ)Av0>}RH3#D%?G=FgN#{S&|nrSqBA(ZV4*+Z8PARo89|4hL6`Iicq|5+15E+>XuG7J5AmAgEKaFeY?#Q<Ghe'
    b'Tn9F6F{g8?mIlbxx2X!&mbQH2Yq^ch8qBucdJdiBfDq&E?4(A5u~$_-$?ZOIBo-'
    b'0Z@cT;?th0_Zs;cb!`(h_0Ga#lj5iNS%1%2rsgg-naN)MY26*#+{l{(a--2(=4cmKdi_LW(j8A6n8<@C<P3T-'
    b'wP14u!k5zi+>vl{nxix(~Z#s7Hd_Vkib>9T3r#I5OH=AeIG~^n-'
    b'f|8Z{A2<D|Q}L%w!^_jvzR&I|X|Fzp|9(#9g6=AAuRg7xVCnj6U9%&}rN2p=G~X^XxB#R6tsi15E~U?Zez;Aa6`EI?&uK^q*k5-'
    b'cRgr;5o)R7Qm-4v;q5I+c4Xpc}d2-+3+kZ<nAX<XEUEQskg$pnQ-'
    b'`tzcce<F;kf*v9;TD$nvAcN6YEG`VvzG#>Q(!`Bbehn&QE>dqb+KsMWdNe}{l}yy8^Ug*8`=xo#oo3$K=A6muT0V0?<nN!*S?6xn'
    b'1rT_GFyY$Djm5fpB9&-xB+I%v1ejGowQcREybt33-M{sGNk7pVCq9Neqbt_{zC@r@gZ&1$D8o@xPENbs9&1(bK0{Fr-'
    b'k|Xo{ZApVdBDLV=MJHcjnv5HA~motdknkNhjm0&FS~1D^R-'
    b'O?^a!J3_MArPD;?@^Sx`9|H1sYU7O};z@us6LT*46G8xGvduSTM`YxGp?aIT4!{5nn3OMn5xX-'
    b'3%OGUqjA6Xk9`##;QAA!r5+a`&_^L<)CK<rhxZBC=KQ$GBC4|5iLBNspVtOMXGTh_82`yj4m^w=n|GkCb_c*LJq-'
    b'Q*_7>ZTTbVreT4lgd8f^mjX*y#1r=vp0c!5}!!ga~*^Dvp3W>NIF*az7SacZYh9t)@{YctLN4I6BfWszg;I<H}{RJGL7fU)&KrK|'
    b'N1|Z771IY8+OZ<2JL?^)Al@XE3W=bv;P#nwM_26+Oj%8C2ctdppDfXOyT|dCS6Hua|`p4mf)Y^ah;sL>pzlt3Dm(P62MyJ%LD9Sb'
    b'@zOC^+gj9UL-'
    b'+OD9)th3dxostnYi<Nz(+(eK+=Alx#F+`@FgZgh{r>Bv!Sf1eSaYz2DrMEt3c88~(i|fXC2GBmm2QKf}F&AiA!aax^eeo8i?FeQq'
    b'xY*gVOwxpAx2a4|wt*{k=-ebIXoTJ68tsNumpnx}3re}dnaL}kgL(Dl)drP)R4P{Jd?Pva16$2umOKO07yY;15H<agC_-UM6*05o'
    b';N+e;oqrtb~=O@Dn~Z=RA2^nAZ+csm7Qv%LdjfN5E!H)Y4%+fA6(`|qh6*=T}kpEaNGe;T6wzuOW0M-'
    b'uJ+pBAKl{J*fIx9f)h7n}3<>;4OW8$KX`PW$lH*PpWuF#0+y1d;R4Q=`vg#m^I<-'
    b'=O*D$>Qf>p$p&l|7}C93!jq(VsGF>eh#>wzTrUs%3uQM^@?$H_sGNY_vF$TWXxqoS`cCmRZ4dZWh=cWu{@2+<&e_d8-'
    b'@pbCOHa#!nfAmq(C%Ygl5?Xo_G9Y<(&MwYiGyI9rN)AG=0uYWU&;_7Ph%*C4wjO_$@pQKD%vL*458#C9^-'
    b'T8fhxwLmQRQr}JtYVVl;Fn1KB12>`5t9pDBx3uVDN9+5qfUrrz1G@2M+w?VstU{}MA9g3bcvgPclQItcnhL&IbI-'
    b'0UUcW>DL>c0nD!4@Oit1#NlATOm?8i*WpwpJQV{B^*M@n5iSHodtcnK_2*>-#42OI-aUx%O|@n?}O8?KLjw{|*M;eoZSKG+@=V-'
    b'UChZM=u04&X8okdoY{L=uWy2S`i$8|E87tMpD!2pW&*+%SIQ|WP%9S?(-hjV&d*Ue~}sUNVs`gyY=mm`*CDE`IUts-'
    b'b0*8r^JtVQ8T>LLOpJd2q8E)z+xJFnprA(L15yc>Mt*Ns9rWE;7zz58vSv;s)x8Ghw_*OMYYwJGsA30c!RlSb(>_|zKPMz#kbPou'
    b'jY^)4EO%&>KGIFu}Mfy^Jre)=6tBFxi8*yaSR(ZyntXoYf_lEQfKA_|LX?{Av`<`?_Gw`mHAhmBc^9%J6PB@a)B}xsrMA6{K;A?;'
    b'i6+q5k>_I01MK?%6RE8rQSND349Xw@Ci&H)p&*qyfGWik!*7Q=H#8;z}ZUUzl~n#O9AJv01L~Q+C}Rr<?VKwM7EQ+3di`#Bg!tdc'
    b'b1D5qg1qb{rm)7HF4odxNoe%?=wy*NdTS4D4)pTv(Bkea}pO{s&Cy54)$nP;=1_im@L*=p5SRquO1Qg7b!Hh?D#dew>Rsj@5#B5t'
    b'QVU`er^1%-'
    b'Ilt^5)S1S{QPo@)vbuSUCl17YkPCBnhZviUKGe1YE0NSojv8ZjMm4GrMVod!!w0@`1Txi^7ab1+lC4^hBk|QXH4fK+Fsf{1=!qn+'
    b'(B8^&=wPhi(?ir8FdSmgL2sjSYym8qtmC|($929F7CVqs3}|?X12d@|J+!HrUJ}@pt6keV{u|8u#^O<1@W!Kq6_@KEL#j$8)?4PV'
    b'0uV@TCZ<!#zeeycW7<;Kys~YYfj|!z5B^>cjISDop!F%yEG9Cz2%S0x*5Hna`p~%ysx)?_Zw2&JOsD9)9qvB23yTK?D)Fji9$cay'
    b'`k}~D%0xrO(?QiJsP{Z?HvqRz-Ka5KQzAS=8vhps%YC9V`F#mYjP4Mq&Hnc<bI%Gi@@D@@7Fic*vH;b)Mt_CGtXs_KP{jSLuh8Gw'
    b'N=kS^Xe1+bR4^C!b7qz=??^bBA<>+O_`fC8=vtmGQavnKkd@aI{`d-'
    b'xvobq7Fy2;Ejg%{n)RXa)uqSsFUZ~=Wu%yO(o<RTdmpF>kGg48d3e8Xyl^g3d^#;O{Oi}LnR-'
    b'|D(0pTVz2$!v=(%%le>oCMCPKr$R@yDrJhYk0AM@vm=ro0)0^StI+PmiF;QHl4WVE##hNnX9$rzcYDRC;O;}R*(y^P*ytE_V=lej'
    b'ln8EI&wD4n?uh$5rCKo%+KxhgkbJp8*zi=!rvH}>pk_v9?MIh17LOD`+`_FJZJ_W!tFKi!yzCYGVKw$IhLwCl3Krj{YxhTaf7x;S'
    b'p2ed{K>J#FjO3`FgFXJjwftnN3@5ddt}8jOqWj@}<N{*>Z7@0-}eewd(7>=|kQ(zvNE#Ax)d`Mb~egJ-cFN($(@@54a%wlaD;y`E'
    b'O)@%g@6qwT+zR;zz1bCyDjzM+gX4Fgb|DXe}ii}l0#s|FMM=$NgFmSVV)>|Ko7**rbAsMvNr1O?F)Te`Y$|3IDdx{Y>f<6mxW!#`'
    b'GT-8j9Qn6}m&+(hv-'
    b'_<Yp`^mMk}HYMFnN!==`DnAb}3mk4!+NtE7sxEgLShKRjt{zBtLW2X1Wcpec@77IOd(gG&qi;e3E$MO>*A(|_g%<#fr^n}X<Tr&{'
    b'<}uzSddbW-eY%+JQfDRT1+bewxHvPal<t*;xAFafmzQpDXP|Vq*D*@>o>q4$@#Wpa_TqRx+Bh7T3UmMCW=6%WCpaI;_MdU}xJi!H'
    b'p{Y)5%i<2^xl$ZqL?z#W*TGtDL6nlIVvA-'
    b'*B1$z#O&kO#ke7&2PDPhI3Q<dJm9b5_%D(MnsM(=UEh|WeXgND|m0dc<l8TVH;!Y#Pmy`9X9f2r<!!*WJmNcN~g;zAy4&Y8=%BgU'
    b'e1c?=9oH0ik@fyhx1u-'
    b'O2XBlFPMbdZaDLW!ks>85446DPiIt;7B@Gs#otPZp4Fslx;>M*Mgv+6Lb4zubos}8g3Fslx;>M*Mgv+6Lb4zubos}8g3Fslx;>M('
    b'nKhuNPW##NE$Kb@QJnf}i=aag!$`uTE|sM<McoQMSe6O|;|V5YIuGI{Y>lq99@4>;w_M8+Exj5bywBn<Oz*79uD<^(Wz3HVi0Xmf'
    b'k=Rh{=6wc008zFUJ%J6v8m4c(12WGbN_r!1cV1hwb=_V&~{46|Fk+A{l!u9;C1v-'
    b'!bda^7!mPlJzjn<QoLfLs2zd0H2bLZA7c{ay7#ZcQG|y}e_;4d(v&p>%Njyx*=)x^cEw_m1!}H2f79-'
    b'FE=^b&Q3<((`@?_ScPjc;LEwVBaTfQ{fDv!h8dU^L_{R*X4v5>=FF~`#xc{SugHHblz`wH|>Cj>-'
    b')y}0FR}@DuoF)=lyo}(%F!@%X<geCB2xBF`oC^)yd%5ZW12s8R3v}Yrfj}yx-'
    b'1VdN$Y9=iEEURGy>ggo1I3^M3m}>WA9Y(n@#sjdtV0y?I=%3#+cr`|a$d3m@n%?;GSE-yTdWKks))XEX8Zkm>ERZJEcXRmz8z&8|'
    b'D|x2uy;zK;Itfg|mcL1iQL=lyndG8*YL57lg>Z5FnX9C-'
    b'<isY%CK65!9T;67^j)DrFmX9)}rpZ6=cWk$rEyFw<BIVB&=mn$r>$3b!~JfT5*B4h}JStShvr3YK&EhfRhMX!Q~sg*Hc#)yfjZc{'
    b'jHF^_iK%$!JHt~{4WVi;c(M8PPd(>Mw%0}Ih&PqZ*Wq~S|RMKmTN$E|kozZ5jKCM)~cRn<icrN8GvLNzAz<Hv-'
    b'y5h_`nz&3s4r@x3Xrj4b{A~3pVFuF$g-x2zP_!rd1TORD8c<C_Ai@R}8_1(T~Na#W|=s1|>%iNpy8hj`BeH_YwitjgE>5|N-'
    b'+{=rE7VHSIx(K&gj`dpNT$!|$(Mx04?p+=y#Pp6^*d4$-4+#5mm5MEfh+#M4NDb^!FG&c-SOCVrkO~sM-'
    b'7rG{O*t&LG9J^Yl#AM=cgM}15(z&EVe9sId1q718Rgz0fxPjQMX6I>L5e*$@Dae(6o`o!7`8VAST#tJ2uK#`0PNj(eo}GgU4b0ug'
    b'm9lSSuYv={ZdB~7F@~4rE9vdOZ|{T3=>yfwrvZZ=Y`V&hs4#tnEHLPs=XY2dl47RLICh_ewY_>^}W(DhgwOyR?@DOv}+~pT1mTB('
    b'yo=XYbEVkNqZ|F?JGm^=LnWZxz5|dvP07IQrKF5@dY%T<F%TTHJJnn^DigEmlxym=AVACY!3%yc{uos_aA*Ie?2WFyD!Ba&gS6)I'
    b'?d8N?A2oqpO=He6z9{z$~6G8aLd_zT*B|PFdsX7U<Xgck><eiwD9H92yLM0Y*sE{DjUtp3){I4p3XzfUFCTc!#oy(a_5M1KI<LL;'
    b'XXC$@LAZ+EPsA2csDKppGRcLIeH;GCYo6*3zeI$FmVpX4&t>0&4daJMC^pY*jP|EC}u=)2BIbGbOd5Br9vyXq=@(M7xRT<!5wMm{'
    b'e!OJ1i%U`KPI65U<G;!z$uOvfrMz0cGST{aRmsc;J>i&Mlhn`Ny@ou&gs14;V)Fd61%EkeGnVbIFmw>&hk7EV@q^(i5Fesg#+~<;'
    b'#qDr4Ay!qLHn{^N`f?SXJ8Y+e;7b)w3=DV83)wSfH?`CLiEf<j#wdy$sz)2(0*Y92*th8%^ou*CbzD(!fLpMEQ^#7fgRDDM{5j@!'
    b'VpRjyhN&7|6{rJUzPE_RY(5RmwU2iv!IM`K^vd<tA5Jrr@Vxp@_ox+yYu*5BnW3m8jk~Y;A7H>TtrRZn@j0(F*%23K)OhH&Ouq3m'
    b'Lqj`W>LC`C15#+(@Pr$_T`tlKv>LcoGrM-'
    b'k%EH~j$On&xIg{baaO}a6R*APK#0RDx$csjisf1_pdHQ2wZ4>gbm?NRAUbu~(w@2#P2*~>s#bfgf%<!_65V;XqY^iBM}?0bG0zNW'
    b'?MVy+J_($ea}7gN4*nbVA@FzWsDb@yL3PK$ILr+O-LR~wcOyAcOCP_rCt-'
    b'8{@KMQ{k>x_b{*?@LT?8T+w}gA3Lj!b2LA5p%!^g@<k<#2)r?`+p$4H}(I+peO`PSW&w7DDl=?R<3$4%JWP2k&0*4z#(9IOS;sUp'
    b'nMHV<vSoieZI?~r1d*S#eFzDvB87P}^|uF0!w^6E+Q>ZQZ_<vUpp<n7Jngw@MW&AV7gRNXzYl%%?Fd(`v+31tgU?z%V42D|f-'
    b'c|*ly)bqQOwo6H<J5bw%2lKcz_2c__qvJbUkjh$nGEdK&V!rE|-'
    b'}?0Y)){BI?)8J^JlBgm<m?>RbGkh=zjZh2UAe7ignL9@>!JB+PU`~U?#gOiY!;Sq`}TE5$JwkD;&0@|@@DT|`jhi#9}aa(xw98h^'
    b'gZUy-'
    b'b0?db7m9o83F|iffi0w1YJ8&mC|Q8q8$oBBZV<`0W&9q^3FxgSYQ?h?X{%nh@9C)IzKaC_F|iJ$S<TYlS)XJqV}DoB3b(c(To$Ow'
    b'4gFXMok1oLpv>Fw31j3!Wq&+dxZ>%d-~Zi2fH@qK2G=LV%z^9)%I}o-jiCq8%D^pjE`0AQF86<@z$-'
    b'L=L7HF8|4vS$oD;NXOdTZ*3NR?@T{F7h4_%cdfd+R{!%;JeBa~u_hk&<)x<1a_%PR{JmV!w>+kMOb-wTA1M-'
    b'~jYhsj+KKtxh`rGd7(__Oa5YVxIY+o9E&Sjb_B+)*<(czP`Hy4^3&s&y9IQ!DGTA6&{>1};2$k|;&@$H07=5I?SqYTM4gZ;~7u-'
    b'|PgJl^K~tCQN-RQ5HM{ku+O-'
    b'@VrWz?(>CUxN5oPJ7>6EEsHN?C3q`z~5y7S+rv;*&vq92usTUuPGtzxKYwrN{MVzKSbs{ik87&DP{)qpe*Kwhjbm(HX@00oN|jTN'
    b'r$+XN=P4KfvBaVYcxWQMySyUH5%bB8;wvs^3@|>J@VBfUp?~GBVRr8)gxa$^3@|>J@VBfUp?~GBVRr8)gxa$^3@|>J@VBfUp?~GB'
    b'VRr8)g%9LJo10Odq3!&ylMDN*QN(r4VGyjYorOGiUn^p(?Nm)Y>Wv)at=%2gtL+(BdoMM1}1!38@^bZzMHXHm%i4euXX8bUHV#=z'
    b'SgC$b?Iwe`dXL1)}^m?>Hi{i>B)J&VqN-zWAm_@^eBRk<8`#yNlK&hjv3{d&`HPVF(u)Q&T))Wu1l{`aNNj9Owh<<cS242y)M{Vk'
    b'G=+$zi422pR~R=#qUj7|6xonWM8U!ww$Vdj}zl{Q`TP~6yucmix*E`KMg8>4F)nPFu#|R98z5Ve6Dhd;_?SX`+SJP^7|wHOLgTJV'
    b'){!NvK2CtL`p3%Ff2$=u)nku#4}D{KD=NN_B8A}$$bc(BBEe36Zi`?DXsUEmEUthrkqiGzC}|KXO0Q;CMw6d(t&7$f<e}C4?q!#q'
    b'!9xcIfE_mR_leLS`+K7mc-bT$}%k=#brx0?3tj~ISKMo2bC5JH5{54@^y<ekQ0hD%+3lOaJJ^ftPm$z9d;#DzksV`F^l@4{*qch{'
    b';kxHzj+DGVAAvf3PShBf}Sua2xT1ZUVgDM=cV@dRy!ZRba2u0?zJ2w(@Bb_^<#UE`m`B(rxoDuLOQXP&H-'
    b'jD%<~Y5r5XeSFInKyFzrBmHAV}N9t`zbkq`}tJUWOVQ~mXjOiPSmOeW2C+B3fHs59qY+sCe9JfGX4jbA?yw4nV#7}&nuB340n>x_'
    b'4sC-c}H_06jc^g&<4jKqjN2)4vyfi1{P9=0J!?STldkPslSlVH5^ks-$z;v61IVzR*oM8VM7WN$|>-'
    b'j2Dy`k8v+Spa@yjRGAI6aZwQAp-IkF$ysSsDzOOkf1?hzzoNA8WaE+h?AW&u<v30M<%I)GKd&4GAV}~T7XrhfNc_F_-'
    b'H`kP*MqOQm_iBq7-xIL<CjTDv7l7eA@8g>(Re<-'
    b'Q}t7HH_P%xDhnuh$+Y@+qpZjerPGky+ETKHjG4~nPAxs??AD#eR?YPbZyKEq2y&hfD1STng{0G^Js*i5;fwx0_|T?5cs2Guv49(!'
    b'dOfr;W7kgBnbAPkMW_!w#!`P>$>l@L~$5rmGl0~!zzjjYoq}&8N!qbWdv||h63h@I1gJimDn-CgDRjjESL=zG%+j~C0aFJ+*4o`z'
    b'ap%TV!~1c$_QF<5n3$*42mupzampH3M2wX$+#e5lteg(7|bd~-'
    b'bqA_#|nTk`XphyXz6}vWx&52@Ggd|aXff|0IV6a0q{_OejI>g95>tmbqIwq*PtYGY_zgY>n@I^1g(I@$`DDE6R`CVr8dH*<JdDC6'
    b'^YR|Dj)^z4!fW=RRTy*c@OsyDBP$*>sx|WMTD?6DF8O*^l?%L$}w{kSs`7@`r{PrNq8h!K@hT3cwo|+%7|!eOgc-'
    b'@I&vK}+oHnj<>6IO5``u>avzP?g4tA@)d>b#903K(fs6(E6EH)b0091lG){GQWuTth6XBJ-zSKHOQPYDfDS;~yplMnzEN=A1q)Sq'
    b'i6v<TH7Bd6?^3=Ih^DQ|U6sAEX;nsoViLod9!8IW#<IZsAB=Z#h#LyrO2>t@`6k$S%^4tUdQW~5f(g)Z|${Uz{Cc`qgf?$gf$SlH'
    b'weqoe_)#R-'
    b'yGv(M~k|V~2N>*|a1aJwQ6m<(b6h1&pQNi^sfh+J?SbyhX!6@?*o&nV|Dhhm_5Y830I#o~B$wnhNmBI<9fvb|lQaxq+<<?<STo_u'
    b'vZWFPzR`(M2IPMJr9azK1I7ESScrQ#~z(x>u%%&=_$P>vGk!cE~)Dpv|E7&bT8+Em#lPMB)hV=|C1^`-'
    b'Y;{tFrZhH<jpl@i{>L9@>P)&peVJ-=?#>4<SRDxcM9CiX^D-'
    b'3!ICPV>8F`fe$5Kv?3au;Rb(F~9*kxjskTL5&F0$h@%4A@rCTo@E3j)G7S@j$@Ck^-'
    b'+%siJ9ewe9$%5e!+DkkWxH&O{WThJ!$WosNcRs*$6~sRFAD;-oOiteYZgk`r7BErBn(-QAoEN()UN-'
    b's~T%$Iw%LM_6Nc8uu{S)mTIv1n|`;x%1p<>k$WL%Y|T!xCk0305)t2A&vGnfEo(IHHtt7#4*7Z+V5axKD448Z}jR}UtXHpQ-'
    b'O2*`V>FMcXz<(3&*S+7#}g5{Le(hq|7*s7_mZmz%b1z@N|$SGzLOQWqBC^{03TxSRjx9m^HyB7nn7K>2b3&FXm$EfdDcJ;t2FaLz'
    b'DZQbD{%ru<IS@hgM4<KMb-1D3zdi(MV_@Oi~WxlL{#DO`NcK-O!K=q^dYOEyat+iS(PjkHl$@K8_MNG}liGlj`1mu~?{5`-'
    b'g@^jo&>uGOBy6B+N(@9q?{YnTX+_KiQ-RY7e^?zKIg<K@9{>Z#78dE>IPb1d3t68I4UQlVa<G6jShFmqeL)3m1@KhC_~1;YEWY1d'
    b'@nlh%wKJlUM<RLa<ONV{c<##UPYQ7Oe&8#j1dq^B%({F^)u8XuB-6fOG`wuMiLj3WDR1=23BrtVorb8T^+-'
    b'P9l>$f|yb+Nve7df<z!dW46>$F0P0Oo7kGPrA4ygGY=vWlZ1mbWIPEffY{BUOQQf#6yq{VDzQ&tEE*KVh4#-'
    b'^p2lrnScmGGKRxPW+`#VOkMXm6B8Qqsr@GMj5hA084~z{Ny>m`f$jf9CIxRe?J;ePbPX$s)pa(qA3&xWJMEKww^N}Ug0uBqCj~LK'
    b'HlRFHPv@bv<rHsNlBrBg_uqznDg;aeVAM7qSfld)c5d4*mj2WU7=nO<)4*ZlV8dO?T7XUheYoiocz?=Nwf+Ol3k;u9lU2%ML#p<8'
    b'wB$jysX7APyxjk2bWQ3a(?eIk)*udO_#0bEsG)58tR`b9y5)Nca&`yz2j8fnLRyc*RXj21(n{TV9o3(B7>!y=uji9{wZt&=Svm1^'
    b'$=XSVU-'
    b'z9oq{d06^uYIMxb^Tu;0)5`B8@Ju>;m79l^HWsqwtA<r>}|?EzrHi8`(>EfnNjfbkPq<PTDjrM<El^YAD_bGjlEsl8z4T=s*=t^J'
    b'm8umK42?g37YdfMuBt>Y{Mx~zk$(5P>m$87ACl5pbLRUZfWF>t7Jazn*9NUcpL7&J$=9WA|w!Yi0RbxxH|(9ELVgIcooDL!K6ck0'
    b'CW;iEeHsRObF=0z`nDvy8}linjmS44k5xMcURx;s6W*vByFOk0dSL5V90URFt&$V(@gKT=Uel5(`LK4N?RW8e)em(`IpU)O@hKiC'
    b'W+Pj%l9Alan<76w=Unu=*YbBkDu>+3x<V>l^SF~n7t?>#Q_8+DgpzAlY0?4rX+w03pg*m3W5NnfIJLhq5&lfBcq!mc!i0@d|_g_a'
    b'vn4R61DY4Vi}XF25lmc0JY@IIf}4}u++dU2udP@jgb%&B4sg{g^9)DoQeI{|Mfrq_rL9$B&C!G{n2Wqk`tRC1M;(y0YD%a0z<Qi1'
    b'`XN+KmrV2A_NzV#*qmtK_4$q5>X421WJ_$_UbhaSaPj7ik^E6qO=oC2^2g?NFcpi1^k+DhMb|mgO~z{2lZDjOcK%OOj07gA;s5CI'
    b'`#${Ok*>Cr}_Mwv@&Z@k9(oAzc3ZN_6vc#^Sz!b@x8cw^mQ!hO)9OVG;TR8kHW^x{qJp%!@6P6rSv`h#TN({KQ2W4EMN2dtI6=y#'
    b'oR=*&%Rs{og<3p9Q@^n=PfPI1|4Q&M?R+6oLnGkyhI9nBgGG&mxGct&8LG+r(=|UYBmp-IDuQ3haD$@51xP{&Qg`9g3qU7n{aD36'
    b'BjsTG@6MQJSKGT6drO~s62OKGIx`tWV6}3fQw>j_FmFGapqL+GP9KDRSxr7Na;3bSm%o`qgmajiXJ{4y9JJ)Ukk303$URRintxUv'
    b'bl}v?|9M1rGtscQ;dxQ!~}@M#Dc60U*{FZ$kLSGK?qP19R>g~6jm@sCKU!`#r`lGmo%{ZK?|`KaF@dNf@#AV#C-'
    b'`p8mB4HF@jb>(l=6=;F$tF8w41PKmp}#X}xzm{B19-CDpB;fs3V0lydm`lEC;;>}}&BKS|QfOB5{{%xm6-'
    b'nfg?y=knz$z<O#*wS!%tL88+satKl4BuQqRhz+KOawHtGB5KdIG&(8)y8;Llm&$DI1ti8o<lJ#klLd&BDG&<;2#Y)lpt6HTLV#%o'
    b'm>!}r2qT7Bsl5d;EMhN#5!4(KA1H^!FX4v2AcMp_nZQy_s|%%;DAtQPD6zz0wQ4SuUt&k?uuEl^*kAqYLP;j}R3h7zYhs~_*oBfl'
    b'lxml~q-M6OmfA%M<-BBez;luU?kSdc5qrz-l6}V{H{M?$@SHRIJF3`SL{DC-pZ97?^E)bgv|#<-O7{4?-'
    b'|4{=v*h^WxQd#JrKV!(Kki*C@Gl=@)7b(pgcWULlPIzaXp4EfucIv{17ur#bansm{B)C6_xUkV;r;sl;c@l%WF_c|5>4zVlN1e|i'
    b'|xrYQHIda?aHN4k96avwQK5=V%63uuX`$>`s4H8GjnVg&R8_>+}^JLfQhuwE%Z03Ce>PZQjYtHDJ0dM%d9G!a0?tfb<viR%haBE&'
    b'A2q^EC+f2puJtY-xKKeL&|mYc3^$pm`pt{XzW8N+3m%w)yLK5_Zt{u+hY3bbF&cU(KnB6^S@@o7Qn0Z$b=M|YDtn<5uz64S)dk>!'
    b'lVnDDJfV0x<ZHnt7kSy$FMLyG&zFvb~}dFE&p}9{MTJl>uH#nUu6aYw{Gd^X*~tCcKvSBR6V9ny1<)<rf8R4b(OPvG8$eO+093*J'
    b';bC>OeDoM=(N@LOKu+0l0R)m>S}Z8H2d*np4x$54`15*29EpIfrLNgckbAi@BVwg8&Cz;_qRXt4_-!_h3~z8zP-)9aA>px<EB_)-'
    b'}7yFlb^f`M&IFge?7ojNq1T+$(LlXY^;?q6(DLybGL#|%Z_=T_nS7{f^u`|y1g_#>TmwhlsNx;u0w1Z??bw^g`*VK1=j`VRCM>go'
    b'BMAt6UjWVX`(Wkt7*~iR_<~Ayn*@0sQFKK@8KCXd@2x`TI#QMM*Jq`NA;H;Zr4AOVQJIIBk5XOjy-'
    b't^R@v3NaF^n#y3t`Isbp9Y*57^n7P5yk+30Egdq^Kj(~;r)HVF3leUP3>d;0+hv$1)>Qf=FOc;0-'
    b'^y7&XQ`1Tuh`o=`CZEW0_Vj5EDr~%Z#q<OV#x7AhUdB17H6Sm%x#l#j|2=x|}Nz4WIPFrIos0JD|Vdq3h&I7pSFbg07bFNahGKV8'
    b'KA|maS;xh8a7~byPtuhnN`)!*niz?Ftfz6|X+T9X-'
    b'$wqI4iXhd4T%>}JK{6?w_bMG9G7@PmnFq8&9G+4jg=;KQwy>BiS~7Y}_8sP15UDcRtG6f}8Y&3lWv}@U-'
    b'}ii<uKs>#*@F|uIJH=0r$Ns9m8~I#RW2Guwi@~$_o0xyc-'
    b'qK514-LVXC|3wMD5M#v*ms|H|Io?o#;Q86zC^SA0g9E-h6Qq>bFcu`|E399Bb-HX4`E6jl8<X-29WNman6cyoNULnv(d-'
    b'O2Mxna5l2tKVVd8Ok0|RCsub?U!u9)gzSNC^WOz?-_BQZDnBQwun|&VQ2i^nD;QB9!M-'
    b'V*Gft~q9qym+@~YK5D_V_5MXR^Fs#C$6dyP5JCQIPD(c8Ns)zgQ==HU9)|H1I*+1LGCww7G}yV1gT=RNQI`pFPa`SM8<Kg)KV7ph'
    b'i{FITNR|E6r@KjDK~NjwQrjfOUq=xalIx--aGZLDsa-WeFrKf2wOPK__|)9#UE;Z2spRikYUoFkbko2LeAcEb$Xn!dfH*YK6APx#'
    b'YC8CI&x+glojy1=J)(N0Gm?Vg%1^Sd;&xg>w}iGDht@umKHK`RUOx%$Kw8_xrOnkG`%XQOuCtTr9=HW4+$2nHw|<n@WX+L}3Yk#+'
    b'm8=lkF9VX?2iej2ar3yLJ83gN?Y7fW()%Vhu78wS>ogD{ho4Ie$(lkHMVIcFOz8vCpu8D(x~561kXxznA@$`sM=<}j`4){pSi?%I'
    b'|Rp+DG(%@MN3p7CS$QfuaDAMaR8GprUh@&OD+;%rieo0+atx}9mH#kYHGTIzcQ{tM5z0CL6sw?x4%!0L}~j<m;{o+NYP9G=PQv@J'
    b'Zie)=9B|5$B8zPc0Z<=3xAYLP9J^qOO`hBbR?Xun&w?TAJd-'
    b'p}4jb0ixi``oGU63X_DZqCxb3$S<y=1k#nXy|Eu)3Lvf@3tr07Ex`AcP-'
    b'N&U+d;^u6$;_Wd(S4>c#U{CVKPKh*B~<6s%2U%T~ciSvH7H+)FdNNXcIHX)a<HWw1rT^wU*b0qlkQn+_Ik;ws$wO`4;ApLck1HL~'
    b'uF48Idwal!wUD7DFZ0PXgN9<$?-'
    b'v+a^X4T<s;Nw0&o+`1T3UU{Y&Y!^zkk%mh{DKaEw(~T|=#iEwjDq}gx0sxX5wk$9eMVzAqlVz#m>(`$%m4Ewn$Pw<G;t^r)Nh$^q'
    b'jSdkrPbH55up;HdlSENUgwZ}q&jsSnJMB2tb8EuU&^d7Cu^FN>3sg6BbwgJ-bag{lH*|GFS2uKZLsvI+bwgJ-'
    b'bag|21UGc`vsOQA^|Mw#YxT2MKWp`~RzGX?vsOQA^|Mw#YxT2MKWp`~zDGanpD*Pd?6lZPeJ7;O`&~_29_LF-BYwk$5)O4ezFfV7'
    b'PMH|8rF{=3OW8)%dB3cOj+!Rz%kzHQv|&@S(&zoA4UdWf6o_iStM9GUI+$5IDL?O*H=5_=OUliHfwSWwgS|IdX8^8Rci6YvwFT{U'
    b'^R(`(Q?*yF)0Jy?8_eV6snkxBCbe*{OG4Hpf@~SsJ92Inv!{Tll`3kgprz&!MWP)?O^FE_aH@fcoc1xL^dQ(XDUbykazIy924n5C'
    b'-5m+?Fe)U-n=WxCQRh-'
    b'x@k<unjx2W~4ZQoypVhth((b*Ve*xd!FRv^4s@||;{3@fILS=_fYGk3fSKD^*AE|iNi<Xvh;kGlrJ{j2gPvy#$Z2-'
    b'yM$D422`)r<0b$Ix&w7<VLe{VPbzL?mA30_XV8+UN1oL5=YtFox~BVHd{N^DvBqJuDcv_PB-'
    b'y&V%C{5UVh<|jQI%I~|al*|if)eQTzt&H_)q5jjZ@=q-'
    b'`zKa4*1smo^FWEFPg3U|xTrBCq@yQNe%G0&4pwrX{IGdEq9gH~sK*Xh{X70JzSJ~-'
    b'MGw5u(E}&PBrt4T0`M7dVhe`PR>OK|C!1IDV=X24~%<SNwhfl&31&eiLF0choKNR#r<zzq=cHRbyBo9t9gc-'
    b'I%Xl+zr)<%v=%7pDaRUnruFC_&PN|N9#kqR{A!_v71YEscmZ&AuMZ7GiM|C%LD%s9&!u{=WaNT494jzn@UWJq~meR5{7#d0$5WcU'
    b'l^WY~+9lc}e~#;3#%^^NpnIb5?mQ~^G#EbtpU7WUSTZ@txHR&V$?)LTEc^g)jo?FhLzA{Kuh?Qu|m{qW*8BnNTHLERC;2Nn<ySb4'
    b'_+iBVE(m9>cT=s-FJVb*d<6~)v>rGp~a;id$3*JODRoxnXFL_GmCMAuZy-zz((7J^bIevx9})kW+A^DwUi%>%C%4}0+8uwSVSy_9'
    b'7Q?!qY2k&onen{&UxG}a2J$2sGA5j8zD5>PLAM0cbzo>m`bq{QzKgGw=zFQDWfXEA@@O5$58S#mtR6$_YLK*E?8FgZZXxO5GY?d}'
    b'~_AHnFA%8z6f_-+m*lQZRKymcDgfvlbe_9CZSXN`A23NwD)-CGL%x-6zPJ$8(-TZ)kZdX^nIO0En70WUBSgd^Tb1VRe&A-'
    b'LqH=Y;Z9Ly+61P)}2X(HY0Flh_y~ma-$a<<ttJaTdV_VuS;nMP^BqCQ^=BWKw8qEJcI|0lUd*V70=~zyVwd7ltX=QT%E-'
    b'@ewE7XeFrPCU^~kDhRa##Z>J_V(q0<NK5WLC(H<An6^p_g*et0K3k%liI4Jc>8<ZdDa(lg)F+Y!fJzXiLNo>miUf`XI0t|wchnIX'
    b'0YL+4N=0G<f~E2_%sV`9#Y^WIreMY*3P80%arj@%oK{rFpd3?*xZn*#$bl>*0)QO%!Ak~$pMsUbFhjWyBuBHjx`)ks4Qj*hx9e~1'
    b'nEC~`&_j$sVNNQ+Xe#<DB~u`NBB?k|?2HN}4X`if0{|xiW(Ttxu}W2SXP<Jw6qSZE-xNPT<gPe9)%ZT_*p*w{n}>AlYPKawFv=JS'
    b'^Oe>%DVd&v%3&xhtcLaV21x>&Az<S?qsqY(E^rrN=9RWh8mmd$ImO*{OWYby+i|vI-'
    b'g`8<Z*B+;z~|y^Y4^1@lr}Uhb(5@2{m8O0e@sy80vBFj!+wle+L<J;?x?z>USUU7vAl}qRV=S!`CAgp|2!*ms<aAQk<P^P=!BG!!'
    b')hb=3Ms5pDp;!-r-rEL5JNzb7+Z!pMm{pv+U@3<Q=73CQ<1%iEU4R*0+&sgnSb^hNP_y-Kl8%Q`M31BFYNQ5<ixmiHqgs`@nu5^e'
    b')VTxG(zDZr})9XIR%`Ws|dn?l}tK=g$8!*q7q#2AOi>>MuuR0^a5k58H*Cfr~%1ssvW-1H<!;%AzR~rKc_@7H@n2ZeJ<GM-'
    b'D#doj?Vi{+MRPJ9~w4W2&X-Ze2z#K8PEGICX396b5f$nyn&;VMCLQTBSGY7zDltxRYKk`AtxxV*)3~!%VV-zHv98{+?Ep)*XsV}T'
    b'Y&Amavk{&4-'
    b'S`K%%(o+q0QHml$>RA%%_nDcX9s}v0w>%cDN0S7K9~>#n;&vy@2YxoSO8#C8{K^kf?ITw9ZIUnHg5M=c^7*Rk^UBLoU2ANga`(a$'
    b'$E34YyyvEA`~z63@2L{`=Wct)?|DWzhV3exAv3{>OYumohfKxg3$rpx;`C$UzHeG_;daIUbUUv6x_SuKVxJu{b5O6SFJkxUn-'
    b'C;srFceSMvvxn(V0SmP;R)%HmBFe{E}MGU4fXzZnlS_PHPLrN>8huLzBTdI*$Bp^bGM%-'
    b'}f2}t*WDJJ)Jv^*sxF{1$7g)w6ojWtq{D0C#uqrhxX47Q=f-XazSw!wRbqGX0ffr!H?`VlE>ondBQM|;OSwveB;YzqLpH=$*jV&-'
    b'agQK5fJsVs{bBMX*{%gK%hC5SvY;pD4lk}OL#%VNn~t|$lvU%y`Pn16AEv*XB@GatO3Bm0u(f?Y`giYqyr!OOW@U(L;WF<o?D{(u'
    b'q17mmW8?QI*)+_IzXyzeeE^?m68#(R7A@r()!To5Qi2~U#m)G3XmkeVPP9T15%L5rXqYzO#wB|-'
    b'$oNr(e7<B04@C{Y&Z&YOn?E?G<#aDmS|L12BUGyzd+MhLJ3K^pl+YK<*X%EKoaiZQb>TFfK^-'
    b'U2)Y#8||X_r?%{l~m@iBNW<1;)xT4Veb^R0mLN>R4*71yoK%IU=YlJ=qIekj0Zztr(ll&3M>nFF-'
    b'^cb8UC+I6R`L6{7W5*KPi0b*By*M#HaiQz4~w11OKbM<!|<U{DGspsPB2tvGjvHf2AYodtG|d<LDr4gW69N3V@;@21VpRu}2<x=a'
    b'CHFMC4^UP%CZJC<+hFAjFOH&KV=n^f>yAX`gTq{kRju`(5+DMlN_u2WAh64%l~Z8X0f_NqTo=Kq0{OWejEKh^Ci51YD2y9CNg%Mk'
    b'JIilJ8m|{{=^_ckbunA?pk9&G{kgoy_yn$E&j_g{-F5*u$D1yT-'
    b'3_?7EfG7QnE0Gs}#<j60+Iiw6UXPZc{Kp+t9Q`FPYm1M9efeAmwJ6nY$Ku4tF$S_=c!!a%h!P%R8p3j@`{K(#PXEeuo(1J%MndkO'
    b';`u2UT|yrNEZ0sNcmRL9}jrIoCVVNKL2@=95(I<sgWDZbilo;$E^m5AoTW3E=fE`4lbD1C65`kmX)$2Ro?z9VDw9epMizSYdO%zQ'
    b'_d8|^grfdVlE5Y~lqil~5*(9r~-6(Tq>mLW=`^Z_}VtYtKMkij&u$k-)QSV;;w-'
    b'h?&(#Jy=~>ba46Zlv+tc7)MV`px5W8_Z$;xB)egaB;Ja8Tqs!d0jq;#-'
    b'j_k6dEUS|7y3pZdS3EvBGUqBnyO|e7iqxnwmOIkl7$=Z<lO{!_CF-_PM6Cd-ukkkm>TvgV!eOuM79hU+5kiy>Uc;{p(-'
    b'*Lj&Ec`0!*_w~Ym)2c!wajQ}!-'
    b'&n283x@f+!Uyvl6#nj`t<C{bS!%2qip_)9xv4_S_+b_TPSo3CDgV69o$GQe@Tk}^see%@(H8gSxMlK)W7?DfMxpy7mn6%u4_@`I5'
    b'CAJSe{g7{x>A{DF%5GMvG}Yb1ZAduWix;!BLPb~MoJp9wAp=oH08>@DtooLe<>|GaQpPQgs3yNPqM+H0j+*l8Wy%^qvn@)WU3`A<'
    b'c_i)8ve3dhK~wkUVe@_c)Mr-ua<#tig|-4!-GuulA|_99^*ZsqWfCutZlb-di?}^i)wFO2tCBe9I`M<sWISwnY@@l1&a))L?_>E^'
    b'LxO*-'
    b'KtnV4KUx~h505Op(M)JZ!R?Wm)wl0JI)8+Ob^TC`|9cWr{8cJVzwEw?#0H8YNc{@*JcmK;(}GHFjgrJVqyoYuP^Bdj7Acr?Z3(u<'
    b'nB+wwJKcA?cHhpFX75gNt`cRHD62$SCCVyMR*AAolvSeq@Dk<aPOcSaZeFJLViw4~mdE3<Z{N|fF$v61<y}k$KM<!*Jr}gFO^Zi@'
    b'F7Q!DqVEfx29lgaqJwcV1<wYiofm<~pbcS|5-'
    b'*r#jx&l=oNXXcVa&7uV&#knYQkaBd!EoBVQ)ETOkf{5wOSL!Q{K+xl;K{f7^6{?N|FEz27sdA0$ZPaGK;5y-'
    b'pTM6VyeiFn5w;J0@#0+dDlhIq|8q{)o_6e7w+y<To?I#@%}+!9Vf_jhlYhr)Z+#DpcJXV|9|%0t4EF`OB4Ms`Ao7+3%(8R-'
    b'F+I&9bkZ7U>ZciBpFkg8M!H{nq8>>evi2d7v>@&Jc5~|cc7~(U6`9Z=R5kpCp=8vBV}nXLk(eifaWk9O&shhuCYbfF&I%GL3pPOj'
    b'>usN+fx%kM9_|D$^+wYR<V$9lmur^wHs}XC))+1L^N>Dg%oLDhg7zS(-09+ggC-'
    b'2(_A_ff{Iq8q#O(mv$e*v$gS=`pLa?lPxVtCU(u{VeT79G8q_biu4`N0YwbwscGNS#)2kWa&j}ZOGcK(c^i)l7{;tXu_F|sChL?P'
    b'ayON^MKHg$o6VJA*LN^aDilD87au0l*ac+nuAgo2inI;Ify$UW0%q2zCNguIxQVOaikQzo6iZW`1;FNeoTWu}~^sV||sR{no^C4W'
    b'%J+}LSrEapDhu>8_{N9gu^0Bqp$DLQ3S{%m%&kmw1eHd%sxXXD-_P(&xU9#p{pZ{_5$?x6s->PCNiBF}-jK6*RZl87~TY*N3Q)-'
    b'^vx7`a&DsatP<DWj=CymK}{`<fE$A6XonHoCexk^58pT6#kq<jExlExnP&g1jzAnfH*!K};uCl~PQ_Vzm`6!Qu-LC0L&)+^%Lb#a'
    b'@j-+HvCTV|f;E3Rcik8U#wQmb_ui&Q!-'
    b'S!#HAy>BN<<wxa7z3m0MlzlH=DkKJ*goS;97%~s0M5!NI!FE5_$o}dB$pzb|gEGtgbC{k^07+>$>co)j9y))v(uyA1Xa_Z{?6-'
    b'XQ$f?;+4=uD`YaFf%Tjj3*(lOxs_AyQHQ_6Ai5A;!+kMYZ&4E=RTfA<hx;lP2Q^z!r?0D6{ure!J`0d9HNmIG`#xHg1o1Bf;RXgP'
    b'S60cRaVHj2l_kys9dbs$&<fPMK;Zp^1$nNKABv44PGr_88z2DiHuQu_jPlk6!)8pk5jph-yxt7Fqe+bJ5ikyaOlX_g{R)yz$ukvZ'
    b'*!a>9;@<m^DYlNdpnrM9(~y40bYOtJm7&Yi<#3<A5x&Uxz*7)X3A5K#4n!pQnu0>8?nI&LNIba=`>JRoC50^-'
    b'(~rYyw$nJe57as!)62ECkcl@`DXhE|66GQ|9dw9vEl$P3qvikdWbCce1&GLb<wGgUhSdwDl^^jwx_Xd;-'
    b'e<9Vgay*Hay`mi#ykIv<lJ~UO*`P(9OPt7L)HWhvVJJ|JA2I%4O$v&7lO!)@0M{DNM;X#|~Ly00<38sNc*W~W#*BWPt@fX8CT?qb'
    b'p!6)h`yQg%%;i*pa`T0oF>;b}=d#r^o<{quj+<dz3L)Q;QYs#@EYdv7fMt?J#y*qnc2PwSUAM8xsST^qy?5A^d<JwLbeGZc03sdB'
    b'Nl2+$Q?4)n4Fh&xbk~L{d84f6LOI@JWVZ=2O4Et1nG;-'
    b't+7bXavYBn+}5Qko4v(UG8Vn57y*`A{w|N8YQd@XRyrg*%n;_<SnM8=fc>!lRQX}8}+YLUy?VJ6BSqfO;{0hQ}}(5YsWHE&g^x|v'
    b'!xQ|o4G-'
    b'4M@aYTZn&o2hj(wKk|=%X+wFJ>0S$ZdnhvtcP3H!!7IKmi2JUdbnjhoXL8)QkADxI*zeS8=1ry6L~DgvrbHAjQDafh5gcURtu5g<'
    b'?3D?EfxQ`npc(4@68mvTCG1TSGzi?Ul%TQ)vD$FCW~Dy?%%5AuHFd#oT<9iXBbCS-pX^End(~xaS6QM2;l<@hzFcZ?}5Z9skI8w0'
    b'q4;H<^_msxdaguQyY~A`5gmL;Qi`b{Z5=-'
    b'gX?F<P~|b$p!t=d`EjM)`q?))$a@}SLlYUbL`i25qBam6C9zCP7c^5+uwVp7h+#}qog>GvFg{Q>XgPmqDo>W)KJ2`Bf|pYMBZFFG'
    b'%d6UX<Op|8fy|7#Cxmz$jSdkrPbH5*sE9?xk|;`vFd#!q&jsQRj*a6~&jq08Y02BGZMRqynJ92~{(7!m2W}n)bst<`50`6yKA0#M'
    b'mk)&6c^fQ}JUGb^X4nd$wNZgt8#yMz`{+DX0(0f1q=9Nlg0n;_px?{l@&g6BkBql)9DoVX6n&00OZso)EMvs-'
    b'2+bpbf|NQE$+?g~6<}VHGavhb)`%?-Y72zg0-'
    b'?4*s4Wm`3xwJNp|(J%Ef8u8gxUh3wm_&Y5bF3qsP$69_PRevn7V?8RYwms<yy5|?=;}Xb7^6FG@w7q^)v}fGm)HtxAJ48nOfJKEj'
    b'AeJ3ce`aB|XxuWcds%hdlYYVXd^l`6D)%oE3}}lX};zv0^oa>j0$X=Y==(GN3Ml30W_)^5}@llV@d)M`W`ouQ1S)V@EHPPuZ)$4W'
    b'ZOB*tOhAFT7-)Dk~@toN}Pz+&GIIQ^4+&({PDKC$yl}bB31bBwfT<N39XejHgixqJgFmWvNZ!C{jvdJunU+BEeZB6-'
    b'LI!pdy?xB1Ig{r~FR3Kax+GPt~YjBZlj;F5jEg@XE2qSMqRQ5&(O&PyDJ%;S25Sz5uoD>}&1pyt=>dLO!7e9Cf+LD=pSUy0iMnQU'
    b'B}wo2NnM2}4BBtDvQzxRfnq=t_FwXx?L7AGgE(Ljp!i%KyV7X_iEJo)l+#j*;Y8pWHcz#G-`5FeE4{0IXgY-'
    b'Y~*xp#tRuF(Guc@K2y?0Bs2iUWXu+@={0m52BGVoMDNEAweZn&WbHwV1OX72mvX<0u9zEPKfhBI+;Qg0Un2c6BU(VkysX~Vq77>&'
    b'mdAqaY3iIHze1+B@d#?Np@Nfd|cE+<xJaAGp{79*E?}VC!>uqT$M2_ckz1HqW=}rXrEd~Wy#6PR#aJmlZ;eUxezl+`n;m*Nm;a{*'
    b'1+gf=us2>+9`liwF_i)f-'
    b'%egK0JC5;4L$PI)hCFHbpsb9t7LjN@IcVD45U4e26gmNMw4}qZqXWHl%GJJ|3EEbDwS}KmJZWQJ5~qqj1qvU|~cms&t?VQ#dh_Yd'
    b'}u|5z7S#MFCn46l)Kh)p$5-I-'
    b'0c8s*U$|j6bz&z##tVKoYBb4h0#_R<Svugw3$^P8Az|l_EA(vFd!z`s~eCuAlMz@}2vmx#P1>Wk24*BGsMo)Pr+|!fpd?5<I+<`C'
    b'>=mi7u`1d<)4R${a?a@VgtpSEaBA)`@}!=Hz0uE+jdIrV>=Zr4a?>8aPJ61%RUl_=;kbG7xEmQy7akAxJl?SEp*KZ9|_Aw?6(4pv'
    b'h0qumxbvehc59KfS(0RkD;i;R|51T`cNy_dZuW@V2sGRW-!@{@&~!#)-'
    b'^u6!kD+@Skdbp?91nsT~j+U&2$0!LwC8^~CfD$V#b1W558#oGg@SMoB@G=1xUpEgV1v(8<C`1h*^@hMBiCa>rGnp(>jN?0S0_9=^'
    b'VO15_+wV;8|%z0VmC`?w;&(3A&MBA9fD5MZFhh(NT5PYC#gQK`gQz=0zZO^{R>fWyKhBvQBA`Ch`lz`T;%J^~4lHKo1_ufdxlV6&'
    b'LsudjFJ>9#VBrXvq`&&r-'
    b'uc*kcZR%%Wh%w80c;*bjNiNK<v+>6LD1(t1y5=sKI76eEN(iHHh5i*4X=)&%tnOMw6CYGy&t{jQldLyxnFrNY1L=?km;><aU0I|S'
    b'QD<J^;Ax~_KgqRR1i@}UcEEeZXY?D`NY?2g!&4loE!igvl0GyU78Gr}`L!fIG(V&G5KoX$y5+S%?G>#1L7B@OSNkolIl86Do7{FW'
    b'_Fd!(+QS{tng@O}I2^2gaVg{RAQN{>J9nMhTK}-'
    b'ROS3=5>Nh123Ny=y3`fDoX){W3XNonA;Ft3~lUOJ($<IV~Lf|ljpM+4jvFe&rWNKZI0GC=dxAV-|Oc_#_GCaLpVu9UP`#G4yoR-R'
    b'j7`G@k{G(VpZCd8*SA4QqoQh~H?Im~Y39XUc=sTgKggIglz;(!AbsjxCTT<PdNqSXOwB_mPX1BR5EDC(@?R&WZ;4`ITS#se^>w?L'
    b'{nmP|4sfme8rF@6)7QwAznCXut;MlFo<6a#PwhJiS0Q;pQ<Em4dGYq0`SDzQhH0W<<=0b|mFaW+uFrZ4}odkP<6!Q#hS*Se3l6<t'
    b'knP$_ZIA5Z4-vDghsN%{KH<N>(rSqe3koB~}3Q6XsSbad1?3<5a-cbH$r09oQlsl}dQ2bhci>1KpdBB=$Lz1?WJ*--'
    b'mR(`ko4)>l6PpdrcH2<QpE>Y_v{cmw=RI}&gNE=;uX@L`bJQ8XY^sDKsV8trMs(ssVN|Dz=s0Z;~ph_KSsc_Ek~m;k1b7IqL-Seg'
    b'jK3W|AvnwZB_nKl5R23QE2jk$Ki3$2JSu3|l46<ji9mdEd7q4rBQ!l%QqE2rVA{U+5HUYsYVHHROoQ&{^zl`_+ByM*~mM^|>Zd>`'
    b'&DeC^w=Rh>Kp$vxl&%z^MxZm0$+GD=0H;u7|rb=+{mBL;w}k$__dA|0SEna-Qi`X<|aMIm8M3S#u}aBC1rTE1IH{MGiC!wap4dQ_'
    b'bfuXUt|OH7QXmPgo(Sjvdt2WV16*qAy<#3K<&7X-p42CDD9SCT0;X!*dbisdR6FyGzs`E|C28!Y5R<-iq=X|{6U1&-'
    b'$N6$hvH_H6ON8VD5XmL`Uw(Y+L@dg_3v`;hDyyXX6Ucwi=Ys{Z8e;Wh$}3+)?ezdm)_fYm#k`ttL?Rhec|h{fIOa|-pZK4-'
    b'jnOn5w<*gAjIA;C7h`LO@vF8Hs7k3r{N*<uw!X?zO(xrK>)d@ge<lzR<6xJ%D`IrOQq_59=J_1V;6rOkit9t!WFB0LV>y?uUlMMJ'
    b'LOE0wvU?sY8Vm@BhO{mtrXWk0D*C-'
    b'v3J!t}C#fu*aj)mD@?a;b09K@?Qg#S$*1;n#u0#Vf^diY=6kRHhS>RK$H&m)dh##0MXus#4SebfSuB+}-'
    b'c$*qCA_|1q5JB8Fl2HKi1)%v#mOQ&zKgy_~(rP#lG#(R!Y%c`8LApN6-8Xf1s-'
    b'uxWignDk_^vC9hS<%PpyA6jila2a}h7YgsOX0xO~nbMZp-'
    b'9r6E8LYuzm5yAL52H(xJphB{n3>oQC#}_SOYvcLAwJA3Lwf!Zralz?FFZY}fi$$ohjdh*Zo|{l{;61_dTI8r>C6_K7Ut($QeUUMw'
    b'ngx}HU9SAeBHTX=_>7Z5_l?f(!H9fRWa>ARA6o^!M;!hCD}WPOHZ#4u2}v@^Zjmbd~wZ`zV;wAnbwv`n$y&U{e4pQ+MS1i!{156T'
    b'H0e<({tEGzlHCuHURs+q}ak|;0Q%F)hgVo49!ge&E=Fge?P#SrHpnkTTj0AffTjXu$DvL8@SfmkA=89AP+YckNESZn%qRPs;Na~L'
    b'{l@Vtc;c_r<0d|RNt(XB_G5GlFnSkApWdXx&<Ze$&mz>zgh~|I(uJcLU`RhykG&$^y|m8*NZ%CWq&^3{Kx<K&;OmINH{uGw@bFv='
    b'm{EyZq4%!aP_Y=`!C^Z$>jd0^sazi0tXK!7WT&O9;WbNf19qPwYh`&NK5dq@U$-'
    b'?xBp0rC=dq|B!IPQFHe)<K@$Kkk{~J+XHs&7WXTZr54D!1XaeTG>U%bM1oSk)s<M|=dXC!%b71nY`<nkgY=EawOk^m7*`J#YQRfn'
    b'XqX@Vnv8n3S&i*`H4sdvq3iR3ScFn~IO|@QqNQREu=1@xi#X${^<|*Y+EY9)=_<b${2h;H_zftz3I7M~di<=@rYSGv3rYT)ND!&Q'
    b'9@2Ym+cz7{DK+{Kf<BXBiZIyq=xBc@=!a%PNg&PK;05;1z(1+WUbr7z~in*7EFs=9R=`*sB1k*VyhVXxiP5b|pJ^FiscK>gc#`}N'
    b'4lHTnf!{2d1>e7)eNBECs0Ey_758tF}XhTKHVRTpsB8S6Mo#C<U@C3*=XgEBX9Uc}sGrs@t;69oePRqIU83yuKL-'
    b'&isD9bD{jS8TaE4m)59b3%r$@tM=%yCAV0WnL3(uuAd(0hXAsaLK|QmT7R_khnNlLGAUgI+iZ5QV*=SoVhJ9Y0xZPX4iKXJY1#8T'
    b'^8#&zXsqciXFlV_v!SmqmDTo<)BhT-'
    b'5%&DbQ4+4@r@i0`W`wSeVS7Z>rQeaQ_7eSV4Ax8`Nn%`Y9AE9?^QDeK`%hXf!dt>VN{3d@2!Bb)m*ICH5RV)$xZ&+R*%~UpiCP$n'
    b'FLE-~Hc4S8$+_<yGkIbAy-CD+P&cWVRBGCjQ#cjqYD%BBxSCQMmur*Q>0aare*U1aP;1E)d3DEpfs3@1f)6Xi9WY5UZl~n$Q$~)F'
    b'7ZRn<V|+W8pp4y7Sn?ge1a$TcW-WYTErP+~jy!=VF=DC6wp9CTlTq_rHFS8uLhU^RjpQyH051c#X^zx}U9)nH$AB@JOkI_zo{Bx_'
    b'6pW$R*M_ca;{!32G$HruawKmQ`OKv1MJ>d*Dr&9t!z!xT;GGn2ncoMo=x~<(6W$Nk3evYj$@D<JL`dZjQcH7r`*l-'
    b'KGB1C+SpAwSBIyb6%=zPUE`>4eK;KLcxwP$)30#SxfB-^E<TEj?eOhl~#VL!YE7Fa|uiB@B<xdt-O-8_9t;oT<+fYF5UC;-'
    b'0rZ2J~oVRg5kB}j8vpPr2>K_(pm`@9b<|xDp*STBR#B)mkv|vtuvaykhq5-'
    b'Fo9HIN6K*0R&S1Es>3%&3P6?E{U4nda^;%7jMO0#%E5y8WTPU10-'
    b'=<i0G$y`1dm{)EOkIcu~9r?i>)U{5NwnGI2THC*{ds5$sMhed=O7^6^L5hZrwbt><}-j8@;~3rwV`bBnp%Xwcn-xQ^E_CeW^W>&9'
    b'D{_!HU8Uh3#|VrUsP*s?Na~9jzJA6-S#F`Z-'
    b'_@EnVHyYRs~{!okQ|mKW{#<88&GD?V!`PN7;wlDOMK*Kx=`d|MqUn3Lzi1+S;?Z(lBHbqQz>t9e`I*(`51I+jM|QbU1uLxsY-'
    b'%0ZkoKF!FxkEOZn3eN-aycv5wA8__|*-'
    b'++2(`J_MboY5@Z;zdx4B0$<xFTh(h7L605J=Zy0li+A#Ig}Z3xL(7S$XR8VH*APPvq#y8zD8B%gxNz7am><JyIXQi~yB!D&K_@1H'
    b'h64R3q>$$D%X*K94PWRV6>PN&3rve|Ov6#AA1x*7^@5Lrf!4boTf3lljkepUHi+GPK?og@^NBYd<phOy_+QTl;wKYjgLDt@!*H-'
    b'1J8ekL4RI<?t{uy5@<@cba=m;|Ecu)C3eR&Sv*iS3v3o_;*SR4YgZYO<0#URu{k2$)Js^ltoP*oQ48d{e9TqMq{69wbF-'
    b'5s`DXv1BAAp(0JnHA<>-'
    b'5o}6b_g)>QOBux^!@l48Xz<+qNlQ;OoKc=_&T#n@mfG3;S$IgqH)>|8GDz&l?g=H^2)*eCY?M_(k;3M@eJ0ibw=QD-iU!{tx{Brv'
    b'7mg2){F6YC{vH2yc-98To^I%*5Gqay7Q~2j2X-N+>%(YS;u|xjyHVqg)m!(d9GL)e=*}m3>ydiP@ywWy0Xc<E$8Lo?wX-'
    b'a4j`!12<+{@^Vw#qt3gb?0fWu&2zqNuzIh$5rCKo%+Kxym=6&5$v=7duTHuk4v<cR^$Gq@)F3YOI{HkT>#X{U3umb3-'
    b'w%NI!mXgDM%qU8vQ@or~QD%C~M?xBG3~nPyY_+H_e1o880nYXkzeE7i-'
    b'{c02EP8gD8E9=Zwg#7s}?m%2?2vsLHbeSK)`kY!hr``1J5G&<W#=jrr%TA8QUhiZ)u|24K+^;0d=YD#KR?2I%G4WT#_tbWPE`X;X'
    b'H)B-UDr71t%xDZj&suF`{tHd-'
    b'a`oia@tl3z(|5Uo&syIwe+{%e6e=Sf8EY~Sb3VElB%asIHtZZ|to2}d1gUudk$!nE&Ts3870PQA^z6l95C(EraDb7oUD-'
    b'evAr`HrpoE$UT9^twD(o);hMKM~J>e8T@>K2W&f975eymjw4ygXYtqnUx+-CD-T-Fw;Hr@V;wkGGxL0f+f0y>?Q9(1)ga;b9k-'
    b'cH>-$js*Rlo|752X{wUizFfPEKvtd_7m$`nIg_%=l#DSZA|$Rjsf74^vRpOcwjwx8V?-'
    b'##fT9;(Q3qU(JBcZ$!eJ65R+w?d9A(67BtsO$kVu_nh^aBRl_@!8!hdBm7;Xl`&0x403^#+}FJUm;3}&0bY%`c`2D8mzwi(PegV|'
    b';<+YDx#!E7^_Z3eT=V73{|HiOw_Fxw1fo55@|m~95L>l@7e{Ao-'
    b'T)Ag>H{_i&tTAWq=e7;G$+Bs>Qhy?x@l_c6=rm@sAS@BquB$WgRIAz#G#v2ukHdY}d4D)W#@?h468(?S>@Vit&uoWk(&ii#*trIi'
    b'f??I+*E|0}dS3M0ak<fQjp$`ZIwdeh2zf>6vTeoVlWiX1WnNG^HVHh$w?>GCU#>RR`sWRK)lK(xw?6ZN>XZ~;gQ+1b1l}B-'
    b'Jw$FFLJiI>U!o1J>O?{;5XL)tDhfks4ufXWO0fFDgnCUD%@3-)KRll1DK2{IR4dIYDr-'
    b'2H?0~pTxE&N`UL88$|)DO%JVfVZrJ&EYN-'
    b'}Gn74ma25`uPZtrGhP)2{z~bCcjeYkgChGovc!14Eq?*`%QhMv1}LV5oUVWB<LEhHa_n+`IVZ@RYl5XJ6RN-'
    b'&KaSgpW?jV+=uF}raK?gow?pVyYOJ1cKgh#>+^n-U#Z*&s>^eooU!e}wDR+QOFlM$UrVO9%FSh-UUn&aR%>?MdB3TTbh3NYR~PoQ'
    b'P94?isXy;G^^s0b`&p~T%8Ise<QfvwhnseR>s5<{cN#vW!grG9GR6|<96s-tG0Su|ciR-'
    b'w^UTTFU_Reqi9HUIbKwaM+7lr|Aj~Rh7zjPsB5yGX1}=IPJWQ>O0W(HSO!c6`vc){wa5FF>eZKKrB8j1YQ4j^aj85YytPCtfi#^e'
    b'))^F;*lvG4xB68en2mhuZu@yPoyQZqjTPXcKbQ0QpLVtdr(7K3i<0mj*;QVJ(#+1I46J^#Buga`1w@_T#4Rduf?y0uh%esV)c!PG'
    b'GX+96FdDq}Oy~6T~7*O{8f-9}bjPhT(h-<-wi`6RJYTVarjB~ZnR%^c$itXCuae_~8w}oj3-l0R-=bKc-'
    b'F+>cf5l3p^jCx5zFvbF53=F9tVeEz(0@Relax3F8jY_$wO?tQ6>?xk`Jr}m>jOR}_#hg*@EfUBZPg#^YWg(>4a|43_uBHGcVqn<b'
    b'5Mb4SBoS;`qyw;b<N3`gY3`;RInHt6K4r2l>HU4Fkc1Ia@^R^!RyL_G31aA(>RQJ(V|gBl4p`z>e=+g<WKnzE`*sx*%!mW<adwys'
    b'nfk62=CD=h-YRr&6}q<y-'
    b'CKq3twQ%!p?j;)y;bNw;G?;s6@PZfawpe$S%$VrdY*Gzt1n(a!Z}{5Ia!iPBw;vm(u_Romp2^xYS|tZWO-OT;`z{r{OD;e*?rFUa'
    b'4-)m$TVZ~Fe}F_pO-'
    b'~$io<DP`5FK%cgw+itYLQ=nU4t@*y4#eQXQC|7Cv4Yp>#AI%*qO?vd*krSkJY1I+v=u^7AN~dCWNF4k^z0thY0Vb7Iu;S(s*)e|^'
    b'bVH&!5@M`X!4dLb(&+R|2L>O9?G;vDoH;I#zFgbECs*a?HNu^?_x%!uL)pe3Ai1TdIVp%q+G#C!OQ`Ak@FwYA&d2U*1lAS<x^n1J'
    b'|$704w(PI0sd5TZreQ3n&n6;L<@|G>f<!H9+@Dd(z)(|O0;AE}uorfO#WBs!vQCWVB~+Ib+ln&{0Wo;8VQ0_p+cS#C9S)_N>K`m$'
    b'b1f;4bvU=zT97?9X#HM5p84pc`2%}L}bM9*C0h-'
    b'H$Pj8Y&C(k~nUp}04?IAg}dWY*PISPi$3Wswphup^rDXpO;97(xkxm&j(;|GCWiS7m%})sWw}<(@3rj0ocgqK(h{ZFb7dPPvAi@_'
    b'pm4={!EGIN?mB@mMGWACpdG6)}A_m(qGZIZHDjt>T`uC@a&rr_N*+rByTm<2jrztr(cgFSUYO%r#;Q)(9zBlyGbn_27K^v*WaeOB'
    b'1iXZAXaZbzi5DQ?|J43ewTAxa*~)qlwb6>J#9gD)re*6`r(qZP?5gI>lktRvdQo>z`3#RN-'
    b'+)<$30g3LiaUo*5AG6KVst3XGg{4P8?X{t3qx;DB}1z;U)9>EmD=<_3c(nHTJ<o*XIEci)=H?_588RBmTvxe##NB?HkI0b=8pa1Z'
    b';?z`mm(i5rSxurgAlG&j~ME~L;g(&(d(d3C_>=+5MLuDX7DerNLY=69|p@a^SxE;|+$3(dn_5e8YFn>OE0RoL@SNVY2M?3RDu6=8'
    b'FWz2&;za$Rq^u6wzz$71{QcUmcv4>!m2TaQ0A{KQCJ>*|rQoYtA!ou(J$pUpfub+4a1cJh&7L)qNb!@Iq<b2+OkqV^mf&C}S_ckj'
    b'0w?cO;Msa9(*=H>M{n;v^hhkbfF>=tMGSjz|FX|YF7$k{2ehx>MEI_#>~Q>m~A8~2Db*iG~O6xf-'
    b'KJCy`G+bk^M;q8yrK5orQ#$89QmS%f;=}%6#y`0pIrP>~)qVF-y_RRL2PO(kAX9xr^1X4Ir5oGN^Rm!&Eh;}FhjTFY%1<afb$~zY'
    b'|V}V&5wAYfNBT{T<_xYLWwMW|=lKf1@GpU4h$;sbYDw1+g5Y0GYN((AOWYk0uG_=z)Mk|Ts0M3vW+ACy8ocYeg984X`IZpR^wd21'
    b'?v|UcUXEKpj-'
    b'3aZZ<Xus_lZ(6ccxi=irw^~*>!ckYNe|v_r<aC&(9U?8@m4!c#_=ZMb+?`V{jqiq>A}12&m|b2YGROGyqW7<TJqdZtMATcMxT3mL'
    b'0a^=COX;cTf-h?%dJMA9&3U|K*s)lc&Rg-'
    b'b(+iM+&;h2X2`8KN1E!+TPy8wYouqj(i`CEZGFk$>?;5GVZwUzci1JJgvwjO`^zM}pH>zguXFy<Iq<j4_gm)scb)mZdaob=ZzB7B'
    b'j>KO%OMY=Nqp%sUqxYOLe@X)~s>c}9L5!;r#)SVLQ*qjHqolEv5?N%5h|GBuErY+3iw)*MS<DR&={ksQL=xvX<rZ6#V!p>JPA}0w'
    b'Y?Y@sZ-mVoVe>}Vyb*p`Z-mVvzggrri~MGh-z@T*MSio$Zx;E@BEMPWH;epck>4!xn?-'
    b')J$Zr<;%_6^9<Ts1_W|7}4@|#6|v&e52`Jcxk|L426gU+N`!*9BjJ?zzBnTBnRG$B;6;EiTFNDzRHF+oVqVF{dYR&r#7m6pfAgim'
    b'Y3M@!jPGq#nn-'
    b'^$o;W$d>y_FEbIt&IIv#(pbfzm>7y%GhsZ?0=Cm_T;=@wv2tou(_;+J&GXXcpWWvlG5nBV@7!<bdvFTOgTHFa~$K88q;eO95*r&6'
    b'EyPJolwGl)&#qiuiqTYFX~uc=eVy`@v|B3e;Snwnaga?#xvW`7%{G!;eG{Ij8ptCE}rYY?^J#b2GXlXKg&s$)S^G1tE^Freu1~oP'
    b'f>?{-s3-'
    b'4hJM7SKbKHjAtOno)B*#;f&>NUOFKb4;{@iz3l`x_!?}~(hu|q93Jx=Yzfh3@d!`EgOoU860r&8Trku|l6Xs1+j&r30(FO&Btm7U'
    b'CMI@3&48+J8Y=O60FBH|9SZ}o?#-'
    b'3EgX@pX&ThU==g02$@a;ZS2(Yg*x6GL9NrUN;lro$jsXhCev#k3G7X&t8WudiS#8BMyr)Lyccn|~|i=5H?{8T6W7ARtt4jK~R%fR'
    b'Lxd)yo&Fik@qKwm5qCrNuSUtJm5@GDT9n?4Qaw>eFWEofeG04=G|R#R0ZhnCBr9OEmxkFInKyFzo=o8lwfE2SdG9Bt!#{M+XsPD%'
    b'T#8YKbw7Nw3*Tdd45C-'
    b'Pz_|hsQobe?FC6>%P8_XhHi87&yFLQml;ZRw?hEU(8b#>f5d|P&<7!GZG{A0BniJ0$adL9*!ZP_CSPJNC*JzBp9!JWXLgwIERN4O'
    b'g7j66bz+K_O3(5%RbjvKT$6{3&4-8Q6K|?0DvqsL;#NwqYzU-'
    b'l`xV(BxukWXollDbqWX=z{$!OSbt&vM+>QfFo+m2G6{zqT7XrhK-(l>_-H`jP*MqOlCuhkq7-'
    b'xIL<CXPDv7l7yx;Kh^{8L_Smmj%C5*eHxDhnuh{<4-!`z)%ZZzlQp4p=nZRkLv0kEvPw-'
    b'8pAPxoO@)yAN1O1nx3Z~=!v^1z&X9*q!Gq5{4vkp3kFz#kohlj;l=#$p-?mmxSK0oa2)#+w$)Pqran_4(>ZWV>-'
    b'z_3vMvtfHu}Mj9w4Lzq&bi~tVLP{14!=i!K^iaaKG5CxQm1+&3|B!&f}M61GzdkR^_S0t+)pRnYC(jl!lOIj@g8WdepenqBY6i5V'
    b'&l5#=BD2Z?mF_=|~ypxC;j};Kc=o7+r(b9R+%7A}4;9U$^<9P4_0kLMx2B3!m<l_Ka#&N?9><*zY<{E@#j*V8<X<hlT<VY*fVr7U'
    b'V$_Y4nh*BHj&~fY;j*7(S3lWflbcbEgnkoTXP<apc5eVF9Bdu?Vv??NmwMhW5DW{K<I#7<8qsR*BQq~`*;7r0J!3u(qrNRS~)>KA'
    b'BW1-R+Bds0NL2)cL^142G6_iAw369)H<F#Nm)pB)$ffPqTz;b}GKz;&d$P)p8|3Vt4GQBcT&+Uoim0TaSc2d;T#FgZTD-'
    b'j@RS}rUu<i;dRQj`SAR1Ft11OMfzbE!mJGBPMkgG%7m0rJGylX>ErC@162aONcQ6#m4}APorq0(gorp+tG^f&Nk&oFLK%I7-'
    b'SJn0+S0IB^AFix6NIVL`qy%ED^$Qk9u<Y%$3Z<3c4Zxd;Nd1Wtmwg%b(`&{Ax~^(_%s;Ipv)&clLH<|RA>qGePR_&gz;D{OTtwyc'
    b'wmMsg~J6HWtHC5fea%I0xvb0}6OtzQm_SW2yXj`le24FMTg!(beuz&X4ZCNN+l2s>s|QCZ}P<ci2N1yX8>Vdx4@OVCE$OnjtIi7L'
    b'f<i(E7WXta$L$WgcLA*lg*L&H%A1gAhW5gNc;0<*@%04G#}T#Fob0<aYZxdjuVfTI}Cffx`FW9j%O@`Oh-'
    b'pk!&=1njs4f{v1dOVX49+X|WsgQCPy5DE|v03MbUc$G>8P?M=`Vn`h_WLct=4zM^AQGgf@fB-uk4bfC1N0U(nRu|x;FiEYOJZh2='
    b'TnR0KFS_Z^oJ*8OnqJ=QAG@be@BC_Gb;(or3%yf~MZ`e>UyYJG&z-'
    b'g&abUJw2*!wuAb|qGhC?Bw(cT6SLjhc)2>XCICfG>(6<HZ}Evv`tyn5Eib5naN;q1QNr=Q)s6J+$lJ}V3TBbvzn7DP<KjKhc#E0h'
    b'Nsra1+k4roGS*a)eLFC##|VJ}215Fh|%O|Z!XW({Gw+w8!KIhuMP07gL^ft+Y)GM{r!bRZ5+y#x8sY6;s919kwR5(F<A2@Qlv%At'
    b'Q!!A^V=5jNL#4Ot;o#o1{oF778%ANJZ4rwo1UBycFMpX4T0y?ZfVs9gI?U81`0F7}M7Udw?QiJ}AE4I&dU9ONgP1VQcL^um}Z;U2'
    b'_5;Ph4lB6oqRh$QS72At8@q%z62-'
    b'k_L_4Lb*AhApgsVVWSvK6ud}2munY3^C?8aS|(FPzV+(W$Z1~s~AA3WYJncFIEM_oc9<GiE$*#Oxt<X0_X_VUm@5aC<u;2nn%Sgv'
    b'LY3BX7CS*oJ1yB1Tm#tl2jxefJ7j$$87FHZMY&L9AazIkrqjZ&pbdPCJ6^LWIPEf0PN=QNuz+ED8^-'
    b'!RAQgpSTqQTBki9rJayY#S%#{bKi%u2+rYH*NB7wo&!OVczASXUhe)U4g}x!3ch2z&xlA^p)7*o~AnwoYR3MoIdcXs{U_2Q>gb&U'
    b'!A6cSWz+vI=5d(5)GKXQ3&IO31lu=lRq~#L~P6cB)ld7-'
    b'cgVp82(J7(`z+c(Om?27m%s>R@z)z{7L8V1?0Z1osZIm1fc#$7ma74W$5?Qx-'
    b'R~+wMvHMqw#4<0y?A`vct<P0}jBt^n9YzGe2Id|RBM?TVF_J)FH4hvk;Q&*Dbc&2(lmZ8^!YPbJnHnJ6e%-'
    b'y??ro7@H$|QmK>7Kb!JYfXX*eRzZ8@&5620&K)d|`wUny^W{2zcopPu)H+3vUS{rS`DOH}2tdZ)hZWy(Ikzc;&waWXTRQSeif5Af'
    b'Y;x#7ywu1@YBU&7O^z1!Pc*nA*WC7FeIplgo!fUSTfDB^jH0(1{-'
    b'!zmEIfzd}0jU=!ZCb(rF3xPy#Y2=Qpq&}{i{SF)PE<AjF`F8VJNZ8mRrl{xc=L{fNt_T(ID!>@Qq(g)N=_DXp5CDiw2>677b7$dn'
    b'2aZfMLDJ+MLWD`?uDadM_f(mXwD6J!f}6AgO^&OAu|3|IVtT*6-kGP{GTX&XI`VM$li$1Nzde6{PNXnxlf-KN_U*fU+LiR}YnAV#'
    b'6Ebi7)2Dl162r{IN(~qgW-'
    b'p3JaR9(XMPMLsaxWsslmrlAfzC^>f*?Rr01pF9G$3SQWONaNmzh}1M<$jl=Rp!6QCn{$mNAKH&?W)|s3m94QG`u|r3P+6P=X9LMn'
    b'X)8l*M31CKiixCiXx7{onrMzosThDdj<av>K^o#3sl9epWI75eSAr*DRtzgY*C-'
    b'0Xi=cf(u6D$b^+3kLM?esF6tmp~?e$^_m7Oxz-#-&piex?F3T-1rG=b(7RQ@uL)<!845gzDIoD6{>qU_BKn+3N}I1q@pYTR-avvW'
    b'bjI&ApMQ~7W)I?V4Jzvkec&|@0;lu6o{IP`j*q@{kzTLTN=oC_Cd(bSG4t?S>Ey647<4XuPkr$M?&8O}h@WL^9*&wcqt50g8Vq~A'
    b'B05JD&sjY3<#|i<vq78Ln8?R8n3EN}#&cU?)>C}>yevx6G@K6BpN>xYslhy~5rLbThlxnw#S?HuELDCg_;4x?3AY9_u|kwlXC^Kf'
    b'CbW18mqZKY=T7wIu9uW-FncSQD8^>*lIDpsr*cZolAl-'
    b'E%xfm4+mK<M4_`X7Iwy)QpN?t3@z<A(X=DX9bV3ogqgS@AWBMJB>bP_;5qXNSQ9v<)L}FqAE5qo#!Wdba@;e9tLZZV!Kn#TyjFCx'
    b'&fwE%1Ovfb+oPLl(tOdGD;dsHcVGVF!!WWIx6!tNKRsrc7DNOK8ft(Eh1|twad0ATT9e4lml~R-'
    b'H_OHOj(jiJYe0>fu{w(^oZjqmablWA0Miu5;-i3kql&R<P`6j@6YD%?(Q=kFS>Et<tC~=Y`HBQ6^Q$slt4p|Yk=UN&am4H(L8x-'
    b'ftY|RoR#zN%WaS)RQK+5EZ1pvY#j{=D7AdwJYngOPVXbfP)Fe|mU0K+2o5*WdjL*ggOA@M`F;Sb0lF-'
    b'#^fR?}*w)DqcxF^dvQEUQ(sQhtev+F@&Dmzb~qwNjFanM!0+xh6)ch^>_LAy>QXl9Jg}Ewxn&<y<m5;5kVFXNu*mqHmcl*>_BG<M'
    b'{%C=fvz!RIyt{P9CeDcQv8;9hE&A(S9G0JwESux--QfIeyo#VoSxcrDCZE_pSx_%lp_=x`35vMcG)-i);mHvEA-'
    b'<q{Y8db;x3({*Ljdq&6tl_U`*9q(1@CDO?6`ANO}VSJZJV3zhC39$#N>(@uDON;~#p|M2*<`#otCssctmol7sBLuHQZHDBJiEp?#'
    b'!B)_&+|9@|(ZY$TvtSad4ZvO{Nx`ofe_j;A5N=;D8hu>41q#AWC4a{@618$!_QI?%+iAclxa;ej;eC73n_HOTfO9Z;^Qd^EMJ67k'
    b'IX^HX~>AopDd$`zY^=bF~+bwjlY%%>+uCsaa#bbwDu`OT*q}Y07Lh@s^B%xb`s0Hi`I|~q-bU`yE1q-'
    b'kT5n=!fm<`e~EQ}9DKH+w|74xf>|6{rQAFBk|eU~!7Ybg`lzT8JI`#u3I*Y7q>)l>RN<)rgi6!@~cs>)WqjhYuaI`+<LH~#BAbxL'
    b'*(D#^AS$?aoW@|Wk1Xj@!5P1oF;r?TT8n~~ObgyY8AY~i1BoD=8r-H-'
    b'R10kLuaaQD4E;Bjg*GTw*RySvs1n?@^QTog8}zkC<o<dCPx=sO(umj#+lI;q(tpObR4&}_m~04$H@eg{Kqg@m5>>o;5y<>J!E@=`'
    b'x7fca-'
    b'p4*mDGyzyLED$=b3IZ7^Ia9watMRo6+dH4!5kyHuKg$GA*H7)x6&OPm4pJDznD*jj9dwhihpNdJQmg=jO!oTnjQuU?ByZ!g1gnBO'
    b'UNV-;*Zci44UF+(7xKF-URqrs8R5GjxtM5L24XuY;*yv^dTSx<?DZIFS8-'
    b'#%NeL&izy!{9pv(S&hQXSfSe0~1b`otf=#SdfDX^d&ZmVR{I9aC(DYBzw$n549F?GAFSJnz?UxX0GZZPC*kXWYUCWfF6Nz0=lM31'
    b'Wl>so6OZlA!^vIm`l}WzJQ~Z02y}Mnt5YQd~w}D9+2Xdk}oWdA~!Gd8pD49xNVhMD%jQ=k)nTs0b1O;35@#43bIdyjLmI$VjBMWF'
    b'Dv$;_#FL#ICVOnZ;t#e#z)DnG5_IfmAK*RcoJ?x)lPvthEHq_+B5<)!&wuNI0>NeeFgoa^$>UUUQOJ<*WkbAkF{r5Hg95`;E*gQ_'
    b'5y4l}b+{DsT3m&3~sdiT0%4p8T^Wpzk$(1g7u3dGRe&ADNu=SJ%rpRxOlNyoX{N?MfU&RZ&Z{ypBY24Qb$-'
    b'Nc^%W_zHltz;^$HUZp-A_8dI1yTADy&E0coJy0F~`(Pf*`AP=p*MtfSkOG~mU%A^sk7{rC=e#=Ov?|x(;q|^<;hMJ!T;ooG>%*z4'
    b'MDXHXp*pllYq&4u_Nt(D|KaewxEA)`8U8dF-CyI{lJ&=pM#kO#^5p1yT|8yvy(a$3>vb+v*&MG|*}OfbR?q)}0hLHRfv7@4Ys&eR'
    b'?mtz$a;uJ3bxiLK^yi<|=}HmiWBjywBx!?_rf^qCTMg$(s><T2M)O@TgR=f_jr0n>a`ORySe0R=8osrrp{XH!>L<$SXnV$|=JWh6'
    b'&1@UV-+Z7S&S!k-do|E%xdq*PV55z<orH=el8a~|cHi!vE7Dtd-'
    b'!wgFNMVE5dw8`}bG9Mt;lExVetUq$zWMT@yRsLAB%NyF&2neUcOOb>|D#q6?4KGi(<(9Ed9vQNV=c8gTcgpK(}J{i=3(}r&)<tXR'
    b'TNiC5Up-D)0%F54=?4ZEjJ>34^CncZdT|sz7Jk1)g0yH6>BNFRZ@+12O1@DYf_q<Em<dbyCsok->zxX*ta{xf8-'
    b'e#09QPGO*_~HSpCk;j`Vn2Z^`!NY@TV=bQ^ha|MD$7{jqxv?bYpRFTZ>_Qi?1|Ni8`hZCG)pn)a(@JM^ei4gTz-'
    b'G^At=vTqv|E+K4BeC90qJ3|(i(40PbY#Msm-'
    b'&X9e;=5%u+$dG+)4P)Ccdu3RI21lxUuzZXnUsr%uk_^Rz7i#;c*tm*@|vxTk}|Il?U|PbdXb#I>cbFXXEE3)F#T{7cR=>S!)-'
    b'+tZsRW8`R6o8^*OKT#Z5=M*HQfTbj2C_SK6sXjs$484v=hxQVxzwa!Vx2QzX3()^h7&OgZS8W^i06)kYdF4W-'
    b'DClzBJ0KopBwVylehq~$D-'
    b'%&>XDl!Z7)0h4i5@#V{31CjqQI^+m<PVtB^_aqe#h(?EqnWvJ+0JI|I&XYt@N`%oqO3wx2&O7Zm)kAH<(WJBC%w07^r54!C(3=^0'
    b'Ged7?=*<khnV~l`^k#<M%+Q+|dNV_BX6T>6487S|H#_TQXWi_qo1JyDvu<|Q&Ca^nSvNcDW@p{(tec&6v$Jk?*7s;<{qs`R!Agql'
    b')q+Cmyx&c~<!)}Z)Z;f?RAH&<@p82hDq*6@toALKR(dz8&il2#Q0=B(`|`ZsA;nmKTj}$D{f0XQ1Tvdy-qiP2>LLuZos^&VYd6}?'
    b';g^J)5d~+(LmGW=(#`<6D$QYE@Aej?*XNggUCFAv@-'
    b'bcc=<b4f>OGa(DN?Ft?o|oPilmVx1A9ltt!$<hfLf{grV3hW9#JIPaa5F}paG|PnaF7$Q~D2rJ(B`i*h3EX6_vqQ+i!OwnI1-'
    b'&WP1H2ZXxP6O3RL9)a=OGMx=&!r=%2{dGE63y}y0|+uaYZL3vec*fDmMPX3|1!6!8`QV6VUJNTce(A7oDP`PkdDPLa<ocx!3mCMq'
    b'BWcKl5EVIwHQ?E7;FG~^pV{`ph{jUp;^_bv#_^$hbr8sY6QCDSA?+0EVTXt+5ebEMt9u0`wptoYejUDG=Y`*t}rTo4+N=dzNR(-'
    b'J#hbmehMruV(m5M59<GU#Kl+j`S?B$($O0Z!$pVg8c9G~pqQkJf{;!k}g;9yeL3ye5EAY!el8Covpsz5DOgAS%^1-'
    b'ZI2UB`;Z$CZX!hVbWVL}k^$!{R>YbJ5PsOz_X;lhCJv*_tye9D&n=f-'
    b'Y2g21H@!ZLmo4;3PwsVJn2zMg?YV<d~$a+0Ii1xLkQDDTq*#1ZRm<AR#YH{TirA1vb4!DKE99IKuxmOOlvzmN8;^gyxYzK}sEo<X'
    b'p&*a>V*%%wVIXXWmKoM@rAIi<O?)qQtsUVoPl!bzhcCmP-ZTvq}iRv9PeW7QXdX!>rzLIMiDYTlz`EizZwyj_}1FdV4H#uy0;Gxa'
    b'1%%Ify$#_`m|<0W0rVATdg6t+Ezz9vz@l0JD}$swk#5DjgKT4j1LJt0wcEr~r4j6I%pO<6X09{;q7C8gWYP*+sIBSF7j+hHhR9)d'
    b'N@ahg}>T_9LaCOKH~NF7zUWd?dTukoz^Nu@ayjXN;>MYI>*xP*)7m?TC!0)spE5@e?p8=QDW$A^$jy`TG_U-'
    b'%@##<M&&(*vSeAV_58D0n8Y$SAx-'
    b'})=^xyQpus=PK^?bu2iI?RnzZw>1H|;W#fZs=^hY$>exkMU<Zv?<Q8W9V|8!LL2O;hTYRx%pVd-'
    b'y)YO9<%29G<5Wv8|L=cX6ClNpy;zMxBn$HR4sVX72Md_cSs-rWGV<)jON{r=DE(^3}dgCmDW5x&vq8FJZQJP3OW|2vusj(Ch9t4~'
    b'@r-'
    b'300LjwmAOt>&i!MWo%<LQw&;YKS#6*s|afU^L71&XPDki^<cr;wK1drp`U#xQM_77B5!Eeu<t$@EC=vD7+xrIh8w0B<0Y1t6#Zxk'
    b'5As35o=c1o#V(RPLxFG6J0qq$oa#3BXU~X&8R+ycN$yJ@iQ)izvXZ4T{6RF>_i`9fNXADdK`R3?T=INdzE;+y^fiz(WNqg<*!;mX'
    b'bEji@OInydOch`0Z~0wd_;9;1<3RBkV9Im0&cLk(H7u0I5hSjuX?PLP-Nmj`;xO6#+|xS&dkwI=zFTESREPcZP@Jub=W%oSu+;j&'
    b'@9CAou1m1!oP8Bnd_tBVoSM+9pxdQxHrHg@x6yzTO~7;4lPioM%)yc)|tlBFwzfwn%o>YrDPUZmT6ORjg${%RbKrP}j{h4g~mIdY'
    b'e0arKY8HAWNS~x~RHmtv>&pM6GgfxWIw^Ic8}xmELxuwi9)Q6Scwe4VG`Pe1qk036}qPR(@4!6}BQp&hzMml##<~BN&Ag)+rUN)r'
    b'?a^RCI_T*pV1phB-'
    b'z)GFNK%hWS;CzGf4ay@_0@hr|Qxrqyf@`wgT@ee1(q*@XX=hI?VpfL`W|wR489H{x|24u15oSM_69WIA7L!BfDgxrzV=tYp#|EHt'
    b'od7nR_G2N?i>7#V`~(F=^JW-Lk^qXtTDQ#JBA3toF}GC3Xp?`ujYb2|kC=M1&QyZvmM9G&;;wL9caJ``*=<8*u0_BkS@WIXRTno_'
    b'deos-'
    b'f@wi`Gqm1KLyC(=lE<}2snvLWPogq%q6mIHIkfq6_0%;J15$bi{XaqS*%zXmwIJ6CPr=E3Ij#dPYuFO*q*l8`g5j``5B;EtZZEG-'
    b'zLJribwtOj9BWASA$q6>)5;|WaPTRKZ}g>;q!rgcUt%a&sG5QVikq2<VeHW~A}Tk423mLsRDX}BEyRD#Ooi09B~J$`mnt7(mMc{a'
    b'bCpN+DcC9*xGV|g9lTqen)({C-0WFrL>652@#AD857%%))+%Ko#N82j7o#2k!mx-pqDaRmu&?pr5FZmkwqmUuF>>JWI{%!*@L5rb'
    b'(A8hdG?RzanxNoj@jFk6msOEq$e1Vkv&h#O8l0dyajVsiFF<5QA@85zQz=`)7jSR)mQLPx?p3d{z@;228mEn-'
    b'n%8@y*IN@i#jh&Y^lB$2Y#8D{1_G~4H{hWxZ;8zHc>X)p6TW+-'
    b'N71^Ty?@G_fMGNZ{@4?8YOBe^&&<<;{|=26W!EE(d83@G^WWyNFw*&Yspme*4sT+fibrn+D%bwG9{2Q#>yx%Fyh*41Ruxhw;n9iI'
    b'u9Kik^YnYnR8+j-;8GxfQo0o}7b7(AoG0vCiGp@b*NcIuQyQb<jZkq$PAH9?D@92^H2yb>V-'
    b'<0QnvHsgrQq@BnEy7T5?giB^q3al`^69DU_k_kkq86m(D1S#;1)EZl&l!qZ1iZQb>TFfK^-U2)YU@T(Fdt(T}N-'
    b'DD~&_bI?JaK|B?46=E09>-'
    b'L>ji@iZ{c`2=mawW{e;z+@n8s?6zma@0?Ps(O(yV8y8ok+3CzaWUn+F|B=@Nw7e2qlru+u2`fu0*|D&wsZ#Ig4VeeM8J<kNMFS7j'
    b'Q0@r6vdi|hv0NWt;6NLg$QGh`aIS}lTN8WiPgEtX*nZj<RjT%Map&5j@ao#y&1nLK^5194|;p)f570;XIe+({oOJTK3yaVR$^*sY'
    b'tK+@Bm0T~C^%P7jufu?JR3U8r3$AtE59tnAk<hussKOi7`@;qllu~*=m!%*x=<~b3BjX$+q4q9cj+UC-'
    b'ggR|#9*bUmoR|(oKG2RF%&E9Nf-yWx0o%^F<h1sXFAMenZ>dts@)tq{^+d%uw5AS5Y*pYkDl-#=&AKHo!ZN-PS;zL{Up{@APR(xn'
    b'HKC~4d+KLa&6dzhHksZ^$tVFf~{ToVT$I-'
    b'J15siFmai6t?v3Ap4v5Q<OS5~Ebt^Lt=&(E(FQ7?s!;=)r~{D9N^RCsFo;95d{TT9>7+%FhM3lLQMII;SJ1b1Ni6S;J>)7%FNn<f'
    b'CL7s@H30!Bhd6JSpf!HKa9Q5vNW$kC*eqtOFa)5IcU#}sZkv~s+nY&gW(WH(!M$`+kc*oUi)QSS8Hr`OVD#Qbp!;v(VVb{|{Yr*!'
    b'<QvQ89sW1vf+Fh$p|R;TNB7i%mQ?vlWn+33lF{Qb75?^C$4HIV$UWR16P8>W}f6=mkDH)b5O^Dj5Hq1N{*r{eYt)nlDEj`&{v`j<'
    b'L1p_&yRUd-;U(3I2!sYl{E1hP#&$LM79iDHcPf+P?Z(-'
    b'*rRzD;|eiI+Hp?zH_VYts1PF!I&=+HR&)95pXgtgEr<6@R4|mzV0Vrjb)<<anS+XS<XfekxF;*K!d^kX}8M`(7Gj(LN;o@QPxW-'
    b'R@GEtoz5ikmzs?Lk7u<vIfZ^lQ8#9o}<<V=!?{O5jiJR_pjAErQ2d>*R*eScF^EPwVT@4^E<2iOylO;zWDm++y1&oW1*3Cf~FqK<'
    b'MX%uOP#;z^UeOD25p&LbsHWEzngX<t?PIV=eKxf>!!VTFht)~W&>#99#$oB&VAwscS*@u^4LPc=|s&W1@Tk<R<Q;D*nuQx9=?}*u'
    b'pOc@_C_(G)ebHLb9P_9!PfaBBwAN@#rWS7Nbzufrjo8jVgp4Hqyq)=pu-'
    b'>@YC$EpMoD5FQUPHSsL~P%ixf<{wgg*aOtMvxNh9IZ>6=WP_U@4LhA1~gxgp98QErHGLzEk$+z{nYk0{rRkIT;7uw?FP8pv7A<MF'
    b'g_E`Y7O1%|PIt6}hkbn4XTqmg5p4Ln+5P)AbV3&k8sP9o94IGJ2@1JllnKxEK{FieRT%reIr#mSpDkf<<bTEJ%Ij0bAMG9N)tXpn'
    b'HW95g1dkDOYqiQ*|cXfob#uT+fDC`u(s1PeNVqTm8spKLdyF-PyD`y;+rWWx7qHu8Y|cb<2xLQV4gv=R+RxNzp~q~JQr=d<@0xqq'
    b'C1>z2BY^u*&4e30{K;Qu}0iSiyPOM4k=2-5>Jhv8`AU{`UCEy9k$hyn@1J7sW04oldcng}9-'
    b'c1%+q7>Bcpg@mIdICHAqXlp##E*K@EfpadTNc%dZ5>lLoh=?M@5pJ30(xDJkv?8VcU~rhNHJ(LobqD&qQyO`yH}v?5W)1HvEb7qk'
    b'e!+E}u+q~{wW_1^HCo$H-'
    b')p^VtEX49)t?i;`ewXjFX;T5kpEqkyzIq1eGM=9%6uj9pMAW=<tCnO7qf02UKG+>M+qNTKI7aFOF*uRh%-'
    b'$PoDdaU6qrkjsFOZo?W7b`OQ1@ODimeZ2*H8!h_>2X5P4knztSlDtLK)up2uzX14}(`H>bg?It{)bhv#EU$dCKOHpM}X$EY3fSGq'
    b';k?sk`RyzG5psRw4m6aR7Z$?x6s->T{^iBF|qkH3BUZl87~TY*N3Q)-^vx7`a&DsatP<DWj=C*{h2{`<fE$A6XonHoAI-'
    b'b!wDpT6#kEP;T8l5!vR&g1jzAd==%(Y4E6G8gdb_Vzm`HuMUmOvk+8)~h|+^@f`&JA1TKTxOo<OTcBKnQk)~TdQ>%3w}B+duw=jy'
    b'>Dl3<wqrMz3s)$lzlH=DufH0<cfWP7%~s0%&i|<@q0hl$o}dB$pzb|gEGtgbC{k^OiF2E>V&229y))v@|+&pXvayc><WGO$f@aA4'
    b'=uD`Ykas1v*xb<(lOxs_AyQHQ%bt=5A;!+kMYZ&4E=S;$M+Ck;lP2Q^z!r?0D6{ure#$c0d9HNmIG`#xHg1o1Bf;RXgPS60cRaVH'
    b'j2l_kys9dbs$&<fPMK;Zp^1$ncyV-v44PGr&O(VO1ZlfrTYSNlT0r~UdbZ$p-EX0t7Fqe+bO`ekyaN)ewHFm)yz$uB0BAba>9-'
    b'Y4(&j?lNdpnHn+8xy40bY-Ld_(&Yi<#3}VH`&Uxz*7)X3A5K#4n!XEov0>8@oI&M(zba={?JRoC5M&#C*ri{t`nJYXNas!*nPQ9F'
    b'PmBzvfhE_KEGUok=Jk_&h)C(_<ikdVgDZaS*GP6Q8GgUhS(|R|V^<3I%Xd;-e<B6`zy*HcZ`mi#ykIp5!J~UO*`P(9wP|YU*HWe-'
    b'dJJ|JAO6uY9$v&7lO!)@0M{DNM;X#|~Ly00<8Lxp#*W~W#*BZZx@fX8CT?qbp!6)h`yQg%%;i*pa`T0l|?*YP@d#r^o<{quj+<gA'
    b'<L)Q;gbjq<N!#-'
    b'fjMt?J#PCR>D2RX&tAM8xsSbFgjOs#Wt<J$fjeGZc03sdBNl2+$Q?4%p6Fh&xbvPWr484f6LOI@JWVZ=2O4Et0NHFD$-'
    b'7bXavibygm5Qko4v(OE9Vn56{<esA*|N8YQd@XRyrg*%n;_<TCNye1h>t!j)X}8}+wvx-'
    b')VJ7M^qfO;{0hQ}}(5YsWHE&g^x|v!xQ|o4G-'
    b'4M@aYTZn&o2hj(wKk|=OQg6ZQrr?LZiy7PM2cG?#VwKImPm0+q_`zgoJpj(QrW3i=8mzX9GM&%6Dcpo6I4tlm-uoqh5gd{S__fk<'
    b'qB~fEfxQ`B3zZx@6A-'
    b';TCG1Tm)|<6Ul*>u)haIjCaZ5P?%%5Qx84Z;oGAm=XBbD70?TuonQ~wTaS6QM2;l<@hzFcZ?}5Z9skI8w0q4;H<^_msxdaguQyY~'
    b'A`5gmL;Qex7{Z5=-6zpfmP~|b$p!t=d`Ej-'
    b'8`iVL?$a@}SLlYUbL`i25qBam6C9zCP7c^5+uwVp7h+#}q;U&kgFg{Q>XgPmqDo>W)KJ2`Bf|pYMBZJ~-'
    b'%ggL}<Op|8fy|7#Cxmz$jSdkrPbH5*sE9?xk|;`vFd#!q&jsQRj*a6~&&8_eY029wwzpUmnW(sT{(7!mm~I{hbst<`50`6yKA0#M'
    b'!ViSnc^fQ}JUGb^X4nd$wNZgt8#yMz`{+DX0(0f1q=9Nlg0n;_px?_v_yYyHkBql)9DoVX6sV3hOZso)EMvs-'
    b'2+bpbf|NQE$+?g~6<}VHGavhb)`%?-Y72zg0-?4*s4Wm`3xwJNp|(J%Ef8u8gxUh3wm_&Y5bF3qsP(eP_PRgFt-'
    b'6ATRYwms<yy5|?=;}Xa~WiNG@w7q^)v}fGm)HtxAJ48ney44EjAeJ3ce`aB|XxuWcds%hdlYYVXX|p`6D)%oE3}}lX};zv0^oa>j'
    b'0$X=Y==(GN3Ml30W_)^5}@llV@d)M`RN&uQ1S)V@EHPdfBVM4WZOB*tOhAFT7-'
    b')Dk~@toN}Pz+&GIIQ^4+&({PDKC$yl}bB31bBwfT<N39XejHgixqJgFmWvNZ!C{jvdJunU+BEeZB6-'
    b'LI!pdy?xB1Ifcz5GtPKazTxPnEr2BZlj;F5jEg@XE2qSMqRQ5&(O&PyDJ%;S25Sz5uoD>}&1pyt=>dLO!7e9Cf+LD=pSUy0iMnQU'
    b'B}wo2NnM2}4BBtDvQzxRfnq=t_FwXx?L7AGgE(Ljp!i%KyV7X_iEJo)l+#j*;Y8pWHcz#G=~6FeE4{0IXgY-'
    b'Y~*xp#tRuF(Guc@K2y?0Bs2iUWXu+@={0m52BGVoMDNEAweZn&WbHwV1OX72mvX<0u9zEPKfhBI+;Qg0Un2c6BU(VkysX~Vq77>&'
    b'mdAqaY3iIHze1+B@d#?Np@Nfd|cE+<xJaAGp{79*E?}VC!>uqT$M2_ckz1HqW=}rXrEegWy#6P7GGI`lZ+H!xezmHS6?BYdaV~lU'
    b'DITylmAPYLKaL0&QHeAW-wVW6C^(qn^|S?4AT4zZpN2Iv&ZtY_sg4TI&;@9DYuxO{}hE$=VoD+kpJwpQ#&(Mp2X!_q!aLx+Z^Wy;'
    b'~XD_bK&rt$r+p7PIWly=!RM$VrP;VO$6+$HgOf7Sh~$lgAlhV_PZS^_)B7n-c-'
    b'(GiDAIb&jC+MRn2nJReg6Flfs7JLI~JJOksvRq1+PgL1Hl=p-{jHhQd+wGQ!Xkv4e9fB=EinEH3KUpNF!O?G-'
    b'(FHj>;Mo~AcPZ%$^3lixiT%Bm`ce1t+d4y?^sAU{&00OyK<tPhec{Dqmu7|@Z$-0+aDOC^XT4k#11*b-'
    b'`_>QBn<!H382kbH$dRuk0f$g!kpy0vkd)SIhWnp7E1U-'
    b'tXE+Z3wMoYx#1go6a!E=q+oAs~DQZ#2_ECas78Kq)x~fa!#@66lk#(!!}@Dd5c`?%l{X`j)70=i6tIpXz)KTb-'
    b'S(S*lY_R?>s*p2B?|Nn!*iMtU7Bb`tO+a5QEV&>Ni`PkD@p$_P6NV{JI{u=ijm%1BJm$m2F0>&#N?qbE;~55I@I{o{RWQ?;9I>x3'
    b'pJYF1cjCMxNMlj<!qPYQ?+iIiHvOjwWrv{z{-2+(H&TgM9)olqzQ3BWu6Q6?#Jk-'
    b'%RlCh(a>2+gR{hYRJNfy2x(VctaLI0q?_XoG@5*1?vfA`(d>FbKeO*gB@I7m8{C_1<bp+Q9yV3c7>d%*`y%&#dUpYzkuu02;<lDv'
    b'&GdLF{A13gv?~np1C_r%tDUQG!u`nWThpz+eJ-?wK{gCT3s_VR~Y2fmk0t{jsuArSS)aDdI@QXlUB)oD-'
    b'O9r;vmbAYn3<BRFV<038dMb3y}Ql5*&qR6tM8pXkx9&CR;V&$>Ja-;F7t%43>ivKls#G=>T0l@q~B*uEHGn-xX@i{(HD4e<ha4)f'
    b'ATPdN6<7)}jfWjC1fgN3{L=E=u?*wVdu*u|8kb!28bGr1g$RL8!JZtugr4NuSCc8|GjilSoy0~{d+4x_LMs%Z~9(ZRF;LII#gi7N'
    b'CN4usE$fTI94WzJY-GgF2?W}wNT3!ln?9?epq-'
    b'6k7itF@yhZx*#wHjxq#)ueNB`hb8Lf<Y>PbL<e+fqE}YV9dExEgguZ0tN#VQzbhOr&0n37a($ROo1k-'
    b'%=A^6Tq=rn#hFV<3YPD)l-{6Qs3oV<AV6D`po*K|wc-+KBoF|50@I-3cmj+8ZsIv%M!>n%R%u{390Lz<vanxdh#-'
    b'8rmZ)nGrj)X<gF$itfE_6Cb%a7R1__D;j=<WeLV`Q$h>XVB0RIw1VW7ZL0sKCT@@4unJ-'
    b'f3Tu|2z0rPR#qM%Y#cDTe{zg`^F05@Fbhz^h&I+2L@i6JO^xVh}_NXyXjP9w)IeO3cn~_32N}qJR|xYG6ZTmPBbH<(NefbTtJ4j|'
    b'd0oDL@A10tpa_If!z=*$h)b5x&;!*8Q2D-'
    b'Fd*BX15e~vl6SqRsh@y9MF%Hk;B$WR8k5M%2cpcGhi4*MTZ!IZH=*In1fUc;!8$iEe24jGgeYBwVRyODRt&$9$OdlGJ2R971l5WJ'
    b'4p#o6r(U58c88F0UYUIa{++SA}9w(3?@d2kdO@_4z?#pa|+60P$^-'
    b'`I+~<@bK^&|@=`sD%`TJqVI~Ci5lc$~wH5>50CXo{Iy?|2V5!bqf{o%4gGlR%5d;GR=5UIX<g!0uhmKxN?$6B4O0vJ;hM1VBbU@J'
    b'yuc$LIa3D>TQ{gZHAfhniz)C42Afw3u6x)Ef;w(c<O-#-iGJn36qxQ}$`8m9^Oy*BflFmuvKv07JMI}LeO8ODN63Oz-'
    b'q9hn(*nkmr5g89y*JyxefT|4}%KWV{{y4cmGjX%@sWovk^1s9$hm>*0gNUO&5i)?JW0f>4>6I+<7B-'
    b'lHi(UnQ3_!60W(+nY$PPSA%-GsGfRU!h^#GZPo7Dw$CT>C>z!4n5h#g3Yks2?Nmm~yZECTtTAr&NY+%Q7`({Y$kWjv-)DHoF-'
    b'#l$Ry?~JgK!YSsA0-gXk=#8hW&?f*-'
    b'!JZrF0pfrhjKv`+0NByQm;`3Ykq$0dbk2el`5rBq=~>;tuOg+=z7f6U%(VqQZ$Zyn(DUYZvjshGLC^0b=()w$+I})8GPR$=-'
    b'Ral%Wy+n<6$UkVLWiTe(7BYHzzGS!RFlFgFzw)c5E--'
    b'~3{yZ<%reIl76(}gc#py$Z2|%doB;$eVcEG%qL*~RgShSl_K{Po;aKv>EKaPSd!=HGMo}tB%Krl$Kv8g!G$FwGd*`xpPdV{O{+jM'
    b'(n*&)^`M0@<tp{v>A}6pfZ!GKirO5v~$&cM7|CPJIiRAxhb<x|L@Rrl{U(U^LbEKQpTy3s$%UtC)XSmBa!~MeUZaJj20vqZgtwnt'
    b'3LJ$jBg^9>hjEw?{2_zB|izSEAd61@&rAZ7B0%QY+fq)naD;Oh_3Ik=uei_7)22Q^q$XcMg2|2;EVF0I8!WWIx6!tNKR*l9+3KKk'
    b'20K@^nV8kusI1915u5%~itzXd#adRzfPe<;EGYRJwIF|?jqbP6$DFxBMK$%K<v=A9J5w@pxTE=K4hzQOFqycRJ`z3Ksn3|`$7d-'
    b'KR0C)u2DtvH``N+~91*)tS>}f@jlu=-!l>w1QQbs|buyA$-'
    b'(}*&Lm!0^CVo*Za$e1BYS>T!=qrp5;MM1U(>BI#%C_w2^GJ^7gQVNbJz%>aNqJQFxx>P3~@y!8r)&X>L@;ukc^H+A{+?+MX^>Ql='
    b'Z<>|l$9Ey-0TLo3Bx+!XAP52Y(Hc;#QpxMl0ElE3*db<;Sr-jpB_$A3-Wx*zAV_7FF%O-'
    b'XD*>66Veb^RfkxoL8jHlOEF2F9onQtLm|Kk*4+emR#U24Euz=2b%%kNVby2O{`*foHwOwR42iOxda=)y5>*l<=j`Qj-'
    b'?3$YOs5+l~b}_;v{k)X1jyMN>7Xi3G2GoOL6FXrrHr8-'
    b'Sanb@Xz&vo$k#m$%5IEtIBHqJaY@sHJisYjK5?KI=$Xkk)2@=RDjuv62EYcu2!9;Nd6b_&>U@30|2yyTvh##s04cMp0r`^4I`o3C'
    b'yg-d7RU!GV0;WcSF3J_Cibh=b(|8zv6>}n_9);oFOp-DMNlRLt}TE#eQbxRDT5oixUVA$X)xF|4e5#Wgu;FAV%8sL%yT*p8TiZW_'
    b'A8p%VBw%Tla9(=4W_C8<bOa0zU0oy(t)f4>}TcGD)V7J_A=&bcv0<29sA%Xz@!d}NfrWsJ82y&XWoN+juI(ZYpDGt#y7dc|Rb|(+'
    b'2Mi?*z7K(eLi<4vk5>v#r1;h)tP)cY?h`^3$&Z9L3M_~vh2woz%R~q#2p|BvqwxCQ!>Ql`#*tZ&(kONT^#7sEUELAs?9=0nGTuiC'
    b'A&S(Nl$2}|+69|Nye7@|~Nas^$cM@L@-#jw;b(z9@Jk2-aRhsX%7Wg+1?z=p_$XOg-irn>y9vOSraHv%o(~sp3mr6k0q?2w<>0>I'
    b'>Q5HgeG`lBbcXz3X;^&*9$m3&C?YgY=&}5EoUO8C+7|9QPAlmr6-'
    b'`UBhTN%~M($B2}P%E+9Z+>ZBJ!GctE;NwH!>#;RyZe3L^2yDX$yiU=9ag$HM({ndl6PJR?zJ{UN$O``Uw|Tn&X%kZW!mXLFMJr;?'
    b'm3|b)~GkacZ{+=jL3*BQ5m228~?-'
    b'+qT)yk&p=&oht(2RkY>j|xVo%5`l%wR`150MEo8$bk{Cvl><lob=ro`SD+3GBVo!7m;z)y)l8OjO1ooWOz=9B!1PH*AkF^q)r@yD'
    b'xp_ZIi6`1p1xQ6_k|MH6B^oN0(YN&+f=lv$WF*t4MZmnY*U*@4YZB;GW^p}oTu1&YMhR*FOWdRz=m;Z{AZ_Cf-wzk0kszPw>XLN)'
    b'B9AG^)r5cW$*B)fi<lBKLad13URE1I3P>zH{Rz&T&mPSVfID%Q?3s<3`06gRS#DE2H4p2jJfnYN!Y%L?eXh9b8QYGs=ryvwT7cer'
    b'whpp5glM)uOmmr7@1>sEbzq}aC9Tmw*mU(7CBu*Fym=Lf%&NVEAa_~<niBDCAsIi(_kc)9hZc;E2&gRA7YK%vUz}>fw6o1K__{+w'
    b'{-'
    b'{Fz@fnx9valE^@I9yF@OBC))x<d!(7Oy1d{qoH(^nuR2IR>52chAm!Y*pv$>?bY*mnT0o4V4Ej;H!Fm4_m*q6Zr6pEBS+e=)_SBA'
    b'+b2`H`0FR<V--}(HM_aLp#R5a$K~>csuJr-;8hmsxJAt_OI%npX<OSob?x}MHl&-'
    b'zd`kAYwGH9vemUPp*^j!(~+9fX08`1PDg}`Nge8HVSGa!>e7(D>*`O*3HsAMKFWk?g+;2<cM|GwT}6P%*1xGuFSR+Q-'
    b'VLcLbCEfx<E2q52uvAKT|c^@iem$T>-'
    b'hfgRFtf2W8mV_bdT}zJub~nKcu&0X>V)V_#Ez_XDRm(^!m;`{E%MLT(7?wKy3SmyYKC8*Rs${YW2aSLZGR-_js=#UhnQ&{cIYoGf'
    b'+*K0vB|gE$?`@9&SAjd$)JLU9I=S)Yex%iiNXwawlHAQ-'
    b'=AXuXq;E?Cy^`jAwTHN1Vo@%jfLoA9fOt@3~x0JAQY!{{!AF$5wcnkDb=ciI~`R;|n`EdtVM+YR_KTvFwf=XiGDmM6Fhvon2z@B5'
    b'W&V4lz%@c<j~hTG~*zFa1D=#_zf>%N5;A)%ZF6Y9*d#m#`fp@b+-gTSGo?72CXF^zz2>$(IEt20CeCAfJ<!p)fHN8L4igx!*w-'
    b'4oYls-ml+qm1Zzq`dD7-'
    b'o#`@E>bBZb1KGcy>u6L3&}}FGaz(VVFRqzQwQBN+Y^rJPZHW7)&|TDGwW<YcXA*1afaH0<e#5;^mn+w^v6z={x6f|>*!5JEm<#Nk'
    b'w#G`BC5<q0PK0EXgKID~!Na_AC4y8AN0{M=v{Q=9$O|J=c?_y7qtA)q-'
    b'y2v_ph~~DwL;H@JvrSv&{F&TCGiEpITh8tZ|31E9FwH*eJ%otimU15-tXMg{`J{IJE-'
    b'_yb?@;NsG!?F_|#H;wKB^VY)93X9`E+wld0gj2%1RO;OGO1O6+jgx_Te(_fOyJ-'
    b'eDxEWLOba-+lTTS`Y8xTQJVY*O%Lu{cj-+l%_EK_U--aOZ&dUnv}O6fw~k{3|Nmtn~$&0-&&ve1F*qij2fZ8nrR1kQJ=g<rT6-'
    b'fuKrfp7hA~?SIvRgZTW~)h}{=2l@amqoqAfz9eMM{GQVBQItq887qGb>znSMS<bI6?xdf=C2XRthr=4G`2I~ubV@3^8D?#i4P)`b'
    b'unaeDFt~c;349a9SyhK97j5EVjcEfj^&+ob#Shc#aIV*!*O0;Sj+i#an;SUtAmT6($pg!vj>#W|aUg}Njo>rByW`vt|CXb^8n@$R'
    b'lB|?pK3VVPZC=e&2V-dOJuI-'
    b'Ue{#n5%Yn)85Oxl<dYI|q~A#MPeI0KBSFVqZjZ=4{`9EUsS!Pk#T@9~ykSK-3cVmcXAHG8j`?==(RwA-D_iqn2})zmnr0LsIPuMH'
    b')ud_|YY*i<)twaiWR2UpAB)U-'
    b'UTrm$LOu*^xnY=*G<gR5l<d*5k+)&cCg4cM)5zuoOyXNuYLehG|JZQcQ%s5eV>?PGDRcf9N8yHDnyIZQyY8S007z&t7F2Gqg;0}s'
    b'rzpg8;+Gp7~R5jY!Dia22B3?auo5vkk{_rXhMd{C*12AqOI&(I|karXe<{aE***mCuWw9t5rK$@IXg3;tNE+tF+6-'
    b'mW$5+A8h(tx<ge6Ud=*b{JQBJ3wg{HfB&J>ay|!3y{sR@I&N8#dkIN$E~_8tKW<mzw$We!0eby-'
    b'E6vti#;d+LPRxPu5H(sD0dKQ8Fv646U+8YgRF8x4V0OeyzGuqW{6oYK@0?_psW@<az6ZYtf+LgS8`ETgd3%A1kNSe(Ly|O1<}Ak|'
    b'YQsZm#WOv_99l*GE6GP>lB%szRhiYU%e_(Wt!)&kyGD`P;rums9=K8jdCob`=LMnKI<Uhyn=$n3};LBw-'
    b'2LQxgG{R6C|A4*+(t$3iMf1!qpR8*Pmz+XcXB(EvaOSe5p5Na`?7LqtS@6av_eX)YZKK&b(8b0e9+-'
    b'dd9?xLM7~&r_R;;MJoZFXT*7wZ2)Uu4|RLRxInN76%_R6{kkOmd~G38uml0pwxx-b<_T~v#-'
    b'3fo0+d%BpTIL3g?6wFBOxA$4a~W5_My~3fY>q#`0g7h-k&reLJma*`cjD?cw3cRV$oz8m_-vzECRuleGAC_X1=6pTbhNf4VOw=lP'
    b'q#o%=<9l7eT+?|9d`?QmcBaCa=T6Q-'
    b'PtS%^CgPn=6ypUdNH$(^T9sF!zw&*z+&Sx7HK(L5?@k=KQ{g>YJ^KsiB7fRJh7pFr2NAcO_4Ly$^&sU!Rc(a0FiaG@&fiR2|9&Q?'
    b'VB0s{nrMF>a<7H9xjhy$eeKsuR16gj2f-'
    b'$X@a7|2g7QpLDJ)<_OgfViMj)f*}q{gzB6m3gr1Q1Qp^<=gJzKs1kXWvLB`MN)=cRqb=7I^f;d_*I-'
    b'(HpXyO#<1Ll=p7eDzpA$mAsrRM)5|WxCLUVW60!A)ie%kVUQ-'
    b'K1QaYfkN}`ym3Mt7zT%=5BLkx(EHljeH1U$@@S4r8}G~P<0ao(@pXlpg<Ykj<1KU&Ljqs&lum|;B^ZvP78=(8T)DxG}}SK+}-'
    b'+bt1e$Y@tcFVkbRb7`CokB=uQZ=UJx_ePZt*L%&j^PmGuNx;1jZt9kb=&6<sh9aREV;C_+q9!;-AZIA);k-'
    b'$Cky0h4pg0p$*x(TI(F50oU5K%580nFWt9hd}r25)`Ayw`GAbix0M~UZEr8I7vl=%yo)N}bV!+myjn5V<cmQiNElL>2gfF0mc1{x'
    b'ZikXT#904oWVjFub_2hf<nc`!I8w?o0L*05tdM=*7YAaj!OxghO_*=qXRs~vRKVW7lo9Vy}x6XU7n5qJxh5~OVuH76ok0|!PT9*L'
    b'j|_KIQ{4vY65$dFRQ!%&6!R|!?74??F<+*J-'
    b'i1YC#(Y;}ey3(O~<QVwg20jvTa2`Nps0|bkWBOKY3!W1MLZjx_~z?8m?Lm+<0ApptFI^%(@8%hM%I=N;=#jOx2!UUL948Wi$>=B7'
    b'00ojBBOo92fG*yLjZ}t$Zke<DF2rihLy?2BLDMGJujD&JQJI<v}kw*X!0KB1KoTG|(0C`rW48x3&kVvLxz;A$91eIz9N?+Kt-'
    b'@q}FKjavtOj;J`EpTF=Agi<ia}K<M>1ceU77J_<1?gX!n2cZ`kDH>@q4Ff!_-'
    b'2pM3P~P&$LI<f9(%`Wn2P5r=SfAW6jFe^cvRBCDe;IT?HVIOAc~Wv5>8yCLIK6~lo^gW94d@cK5s1F#(7dd<UHAsjJQSzI6)u`0d'
    b'o%s2MkapnY%rU63{zPDygVTSvGM>r^f-'
    b'&NU9vdZ}&W{5ZKu}Pm4l3`$wXF=}?36^5=mmA*mpoQw)5O{r~K}*>W38wk7y0GCikweIE2sW?l8r?_F*6aNE*oJ|5vFMKU>@b5w2'
    b'p@4a?J00;yEGeCk=9A-))5aAK-zK6B8yYJ0tJE_C;YM7S7XloucK?0BZSb#AyKnP{FH!>;iphDN75B^>B0oKmQ!U0Ycm<s;ZRsmO'
    b'Vk{wqJeXMLroR^xiWkLuE;87e1JJ@Z%px%|~!x_#5jBQ%md@5k53CsO!Z^GBPqh(BjpaFIuC92F&bJAS$f)1gJC6_GFeE}7)p(Lj'
    b'~P?><Mu&P{#4siB9PJz;wdSE7*ok>!eNO06hOKIP|jI2`i^=MrJy0Xq@${5Qns|tD}qQ73ke)^jDKnV_A%pPh*Z)e8x{@dRDZ$s>'
    b'*1Q06F0;UB;W;pjEL}DQ@eom7Ui4_pK00lH@wreHbp^Th?r+g*a!rw((jHiMu**5-'
    b'D!?`BFO&wJ*9CAe@#Yv?gS&sRTc~r&Ns_5Jd^G0QMwc2uq&5~n_s+Za<IaICQ9@n>lT~!vq1S_qv8n_yIQXKRL>?Bs|fvY7^7|a$'
    b'Q!P~UvRs<Lz0hAH-mB218-bIP1$X#U~3KEPE%vufrVsfNqb>$N9ND0Nm;4rCq0Z8?rr}VwEo|f~kR*62^&V-'
    b'>Bt*#)yi6Vhy%9=sobXLV$OmL{YDp(n%19XZz^ur4UM`dWq$wiU{OUJ^j5Jq2#BFT4Aq#UwWw9XP@g29aV1&lWY9-'
    b'V=qj524VQ&q6530kBnSvH)1EG&4drMZ|Q{qrA3DbmWyxBxzfG=RV>z;_8xO8eVW;!q!mMAdLXBGepViV5L44wx#XkQf1_j6Y6%+w'
    b'BAC;r^xk-FulROcp*1{Eem=WfhK)M8-{oh$@HSG#L&+@!}<603%$^@Qxx|#e-aHxv$>y-5t#p-'
    b'?}Sqq5=vlpzoeRZ{d7ZV9;aDxHrsGNW%#*d}cWz^P-~Vx>USR$fBsC*B*JqmX-ONbs@$1t2KL7U?NKRqpXir5wJ|sY1nfZA82i%^'
    b'z9L@5S}t=IRA=qQ$(n%p@RjE&NT*4#dkPsHX97vo^OL$QJ?Oj8-'
    b'Nglj%yWM<VjQoc>&PJkc22ST!;o1Q{<?#kAgUTt%(_eH?S&ANO1VPQ*?PaXkFW@gV%0G!AEuW$LlZ`KUb&yY-'
    b'qn7#8!RVZ-%Gg<~O}Ot!{}pv5eq)(}P!OJ{<ayzwXP^d?WQAPvP-Lzjhfc0fRzv3YEJQGcT|Tx&}IR=9B_dkj-'
    b'XGT46zh@Fx<W)dQEo*N*O<gF>^KOQvEsG0S8WV|4h{6(LGUxoW2i+7);(7x1M}@~pXxE@i-bzP5XAo3U?AXO}f^Y5ZGj-}9PF-oa'
    b't`B;=StkhV4048I-$qv+_bhEoTZ1B17@hD<e4Dr~(0@U+<!$Jp0_Gv2uKvS*fiH;neE=d}J5H&%HrL&-'
    b'In;F$I{VN|3^S!ld)07jNUSccb53Q#^+0rDit%M&JQ5&|vUa(XKJyj^?oa@9441cG8SD|AvsMa*AP5{4T#GXdME3ac3_j|nKrQd$'
    b'ELoov9~5}l#CJd{|^xPLQ00o8m@+uzE4yGXe>9ksfLj4J<(2?!Ub{fxAIy1$?nSHyeILw`rB&U&4RMIo)N`>NLOTMn$&3?2-'
    b'uL_x3<d<Fx&fLZW?19~y$C4hY?rE1Fp6whi`lJwbF$!!^bt4^O<T;IzN({kpq&7HlQpI^e$mJYf9T-'
    b'i$}Z$`l7Jn#9mJ#5+@Hf;|ZoQ2<{G5lnWnf8!Pd&oZi9<tq<B2LznX`|V+(QMjiwvVpKlXY#{jW+E@n|7leq;%?JrJJ^_O<UGJ)t'
    b'0s0N~2F!nrUC#w6E>s?`zwwDdzM@!?gKr+WhwWY<}CVQubt(ns&%dJLIMva=SInovdloHo9pW-'
    b'L#EvRom1JjT0^OJlwU7FnzPW{t4Av?3voUM%urmlcduZ`<wUcjrPhz`r^Fu#bPmXk*2v157&0-I2Wa|ff-'
    b'<X5uk=D1}!r=KIwzcHU<-'
    b'<QNV3MI>#v^ZUOiR&NBf=^L59AI#&1>`<6!LrgulXmmx!@Nz?i5zc6j{1kJ0Tc3m8P^|Snp<>~pyY?(cK%O$<s)oVFm&bhdHjNPW'
    b'xO_XT6KgVld9$+ih?%j8_f7&`aZ5{nxwvM**L-'
    b')TnrI;R{W`B}ul)q_zB~<0%enuJ9Xs6$3O(g)e;FNL6Fqb`TVXOsX&S^y+elB_KUDb|i`!VJVgwackdNv8*sKm7Ye#fEX`cuBiCd'
    b'W71vv|OMxl{IpUU0YLzIzu*LmT;OTzBVxns4t0yXGnvjw@1In4$y&9AI0$({RW+0?un#8;0QrdkF#mN+MRmUr|@@@oB%&;Y4=w)P'
    b'DQzPkF<nN(zv`QTfVPl!J+<t+`Us`hqvb7)uHCoewNk23i3sO*IUFi1CVDj>k?sdpgx@$b_0vLAl%d^zgIOE?U)pd~8bEEpkIP4g'
    b'6X1i5nb8b!Bn&7-;w^p&%7TzJzKux=(5Uy#q0dS`*rbdQbrla)VWYBSM00Bv)vP%B>9>eL%M*kM~}7`R#C%;-Z1Z-'
    b't_PqE5*RI!G>gEYJ%rc1_KYI?WM6*Q~}*nw7Z%CmLz-'
    b'}oN+ZoZnV#8r0t<Nv@f+^F|HOtjg`|H{iZjQE8k!7KGCK0z5sVV&uBq>?i+e?yP*u%N-'
    b'tN;d;87HuSamWJp_DxCnr4Htl}Z96Kfk92+J8Zl=j=*XHV%4ie+wAH_ffntKp`)tD{!tlTfR#f8hgaEK#HFc(>VB7rESf9%+<<ak'
    b'YbheJ#aO)jY#B<V)%xeWAK$PFSZc`U-3W45BONIeLr~D+&5-'
    b'tW|J0&ik+1=o{J6ZolS6L%NyVonb%VHIuuon^PxZHxawvmDqvEP26tcc2~shfapz%kpmr+LI#a#No&5G`^32x3Fux2Ba8##NP&CF'
    b'OklMHrWw@}J&4<JV}j=vU4@Z=6Lx{c#v4m5(c8>`R?zR7;gGX*p139^yHtS2F30!8?S2bx_ti_QB@kJFe}Sd*HA&bUVWWcp!5XRx'
    b'F{)BVo)u4kw}LaK0H}nOz_xi)q2&g$@`Y61RCsXOE90!elTx+J6*@d1eG-LZqLlC<<6$CdR)g0dFWfmn^HjNwM=ci(UShPU@`s?M'
    b'0LCHzoW0Nq##ZI#ZfsL&XrO`=VeLF#G)rz|Dgj!~B5i)CwCJsXi6VD7I$9{_3aC634M+~iuGOZ}&@`k(D!yTS>$e^)-'
    b'G4fo+dED&KZLc)NmeInl=hzCRM<N0-Fz@?2j#Ul>*rV2Y46w>m#d?`c3M?D!>ZyL4#!+G@!WY@Ya*W$`JBk-L_R0-'
    b'c@5+f4@=RR<UxF5iC#vqJO=k{M3NOVXd|Gm6;Pv`R4(4zsu*n))GnA<4kDkJe-=SxVdw$)YjRp(2!yd75P-'
    b'puHmQZ^O#mKZN>(Ndp9eQ-'
    b'15bWhSp0p+C+wXyG84ZO1rPz^CxGSQoJ(e)h8P_%6&{?1;!xRi2rQ3<&Hx&+Nt?)L@7Q{;QtkGa+Cxq{dazdf_G2z^wz<M~FK>P|'
    b'Isl<DR^X7~ak7(?H9#lJrG|OtqFC-YIHQ6!1}$S2eq01W0t77OHc`n9$psGMl)D=l=)f70B&-w1OXW$}K|9^e$Pw;!-'
    b'Z^^C`|60Nn~3Kbi02s&h+i}D+?}#uVxAN8oS5gtJSXOP4a_sctOo0ag~zd4L<m<<%zBa`p*@Ft%5c_9rve};RgiRy*jPGL?v*)g*'
    b'%Mj|i_c(1t!5T7$^pKV5`^_cBqBq30IaYoDBAZ500`MC8PHriStjQB8!=B7wK2fhR)M<Uoh00i&QO(LW0vqVurwCNu1e;-'
    b'#%nrltnszVnyarHmpxmXJ+aP{Stq!XgXyJ(X3q-'
    b'nnM#ypTH!Yia}BHlZ><9u8>KOEMp!s2c<acckil+bojcNO9mYQQZ)~6sXGkBm&O$GpL2L&b^*6)BNb6K|J$2I6@lZeU&@=GRGvr*'
    b'lW*)jD1=vJFClWf5(20ajB=j0csB=o>YGG^)7c5#Mf#QATMoKP$f;o&XZ5jhlg=q>9K?^^{nq!eL+3v7&l{!+2O2xFSF-IWlN=b%'
    b'*4ss-$4}K#E>%rJMpD`F5=AsZ61?M%>-'
    b'rL`4?=5&`%&_vIDoJK01xA~_g$D+Y3KpOM30b2G&^p75bEzU_YUCzRuC+}hbePn%<7}rA(V>eNe@ZVo-'
    b'EYBDGfP6J<TUVr&Oi&9*WgR#Dod+tf&B0$DU$=NGoS_4X7Deaa`ND-eiKjKG1_hB%>(J`jy5BDpMH!qJ<y{wq~TpBuX|+T-'
    b'OfKbyIE!$U1y&CETmV*IVs)eL^@Aj{5(B<={1wijfr$8x;fF!iEd7GbE2D9k;W&(nmGk8O}b>IG0C`+nXaDl+k$ymPdXgooC6)H('
    b'^P>*q=@-2N{NH$Cg!40zFeN+++DItgTH`R2B@?4Dw&vp3Z%u1YFK_~bbvvYBJr&7KsC|L--d1ydkV~<`^rFXL{1id5rn0HQw2#CC'
    b'A8*7km3Zqb%rXXkTg%02fW!Py4g%)Qxl*gUGvj>DKbz4B`7;cRZ&zMDqM@Ia4cR17+0Z-'
    b'0Z)Lz#lQqv;E#&X7!(JtpwGcl$KLCApru;CP&)%i0UPffUeq(gDlPI^4w?Y`1N@b<77BzRC>ReIC8ps6As3cyrKSBr?Y_QoU?#9I'
    b'DrR9-k=zH`F&w~DBs08<0(irWPBIC2H|Q$<0^sAq0*Pl?PT;Z2dKCLI*fZ3`SZA<X%VO-'
    b'{uKZ?qs{eIPyH9z5>*Koovm{qq4nM|lnNX>>Q)6RNrCm9dbZV0G35ZS!=ob`AWEd9@OBu8QapIDe@qq~8@gt8gqfG(T9JmQhW#a8'
    b'Qm6nw$j!3I?hMES~%(D-!x-s$ZiGNT0d*a^{|GozP4Sod%WqIYoNbnbBi_{F577ojTDOccKFpca5*p^Sg>^cj;QnJ8cU-cmVEkeN'
    b'Em@AV=Wxc7Od|pNlgJC@&qfO+RnV`cr9QMTu43sbURo5D)J;zfT-'
    b'A|ZC_uza*XUm~WXnu)p`?!342laSjq0@`Nty9Cp>cH*bisGhUmTH|9t`@DjKK>`BwazoFb)KQx)iralEtS_Mwl%S>iET}6Yhqj1z'
    b'_wzR!8?n0ql`kv!rf$FI0yku44t@ig4HZbYWBtjf$0SD&V}k|rTHWGXIsj`l(|w1_=W<LQ(#t>an1!MF>v&pk{YGT71cB`Tr1EKR'
    b';vw=G&`}a-'
    b')D0z>{>1opuNNzVEvqMg@&hw0!%NAhQuf)L58SWtfU1|3Awb~i^xLUwA$G(J)7=Icsgp8ve(M*u^d@NERt0)D#xo%T*K=aX>|+^w'
    b'l*<W7#Br4sxTA*XM%+%<}rj2Jy&ASU9xM#dhC+oXo2C)r11=8j@L=!1uGrzV3_h|P>pq+WUiHKy*{2PC!To*o_U5kuh+~ox0fBBs'
    b'OCg9C#pG7&53GW#loJgQh1_tffWu^Z!K6wkracMs#*m|Z@>;+jy7VjMbSXO+!|i0;4B|@juZXoTw1Skph6UiLqsGnRWJZt!N9l|2'
    b'Pv+(<`6POM}c70W~-'
    b'wr%1l)Ax1pNod310r90H*MCyEV_Hl<<WG6o020>T!eE>iibLUF*2Dngh*g}8EJ6V+_7$+y~|gHum$_8a>>($)r;R-'
    b'jZK;cWng7(BjAMM6wrl^NiC&WacjOH7+kj4pJHF&gx|Rvz{}nA!HH8{Q5_o_H>EtjPsV+(JXElaXcL95*$|8&{+jOc~>A#GfHqax'
    b'n^+wLq0=6{zALK#n13#Vy-RL&tlWfvswU5Etf*0>}ZI*R%iyyQzQ!S#p4*V5QXsphZe{3-svVWvm8iH7h(+-'
    b'vDm>3{P#^pzugDzmY5mA`9v6;Tae8+!v8+g|-`fOgtn*-<gTV6JSp@JC?xk$lc07)v?ea3Hz2|zkpVIZT2}^&q8%y-'
    b'$0GCgM!!UxzCBQ0E}%TxpGbwlkhx`x2_Cq+cEDg<+=eyaD=0cCOk~Ec2=Ihe*b^|-><Y-'
    b'{@n1#Kc2$lkA7f*bAW;%s|XxOLO|mpliKiz=L!j0Vr+yH<QQ`)jFCYz_&e>BfN;}u77OufL&?8u|6Ms6%GJH87uu0}<UZ7e&t73<'
    b'H2_-5>fvvLl2oBuCv;l@&u6?G20>D-'
    b'QP6pC`2+(MJq&LF95b=xEcf%NtpLo~{fH#YqZ5tQN)L}C?m>jpe$evy_b42{J7IqBSvO<+fB)E`1VK4j4An%JDG5500@h$*ZoKlT'
    b'dccnaswI6QR_Z*wJj75!IH}~7^JWhvutOyf<5~cN0xTK9sx9y@h^-Cu4i*s5n-W-'
    b'%*@Fq!KnIawbF2e+EHqC_L6iAbEm%n#*b_Aj`%OCoo3#Ox4#bB4dnS@Z*Ck$sY1n2Ns~4e4xI0IOpd$#5%&^pyC{H`8`L5#IX@ko'
    b'wunZvYSnyCpF0A7rR}W|bU@eUyQqF<p4bYS|6~Gcs3@<K&ir%ej1MF?0be~Our5X&K_oiGL+$q8)fh#)UVRH%qEs?{NYFi*h77wW'
    b'Kd;@LhOJ<jQ5o+)R;W<_f#xpo>6?scxCX*oXl1{RNj;Y{4w-WOXPA7OFC3Ku(l~y{qlt_CTfpH>-'
    b'leh91yT3u?S#{jQh2a$#d<<Z=u@?U>oOU&45iH<1C&CNw4$L8Ai7`V7704Q<;7F0@yF}gt>ID2(f)9cl+QG>&Gqeb3J!aiV6Co8='
    b'g5DR<Hw;Zx1%d@dh0OVnEb<PXK1Mp76e%$#ro7O>ItU8fZlctgKwePws7f?&*-'
    b'_F$LG;pACTkR1M1H08dxOE=Q0yyFdqb<YiBWY4tu+XL1=?^1<`WK%c({V46INNqUCtB&l~f&sj+X5q_I_WnH&RsK9bPp>hNzA?Rk'
    b'whTNe<2im_mZ=vIIM#1tm2m-Q*I;0-h=Bc%;~iU1CoWG)a}?QVp2)%u)kvz$R-f^hu(X3(2(rN|2lb?8s=c#Hbbms2^GEjfd-'
    b'!DI2Gy$`<knFAUPdj1@vtLQ_vwM||S&yjoh5hy}p{#A+}mYPY4Q*vwsdTU&2}sX#9gkPRxDERm#;1S5Ovyh}U_moh+3a2Y;3*92m'
    b'&Y6jL79)q@9=r!L{=q-b*EF9tumXrx8TV8w)1rG;%0iMV72-h%bP-'
    b'#~grYxzTQiv`lzd`6nvLY`p+a>TOyHFGzBW{y+d!regO#tHr!(mLT=0Gto;9p>%qQERdDOCit(Qu1zC-A_cL_4zv3BiOhOEp}8$B'
    b'QZ!QmCY45W-'
    b'xnjKXHPOz_f>1C(Af%xNAG_|wx=ubfcbm7V&MVh(IBvWQj@5zfMZvqZRTyk*Q3Y;ra*N>CgiYKEfFF)46(s5Dg;GJFp)XG1ZU<6@'
    b'q424nzzg4IY&!g<1vK*-'
    b'=pY56`X0dAj#)fjlPHI%)c!^SvZ<>G_eZri)^vHMFnt;tj56uw1Q7p<lY*IpT(bn&1wkgMVnsD{rJJ)tcGp+;CvNsE#?e`J$RxzP'
    b'#`Zl*YM*2$AFz`;W7l@f_!wkiYe3Par|4`;OZ41C9kq|DHyH?@T~m+?K2yUvRhuQu3ABd}HAnYWb(L18g3vn?h=-'
    b'7y$cav9DTzhE3a9S*W87+P9Q=%9$f`vh5Z$6$ChF7Q;z4{aN+vkekX)E5S5?3$wR1Z@Brwa}IG96g0iN`jmN=fllt=Qr8)Zd?wG+'
    b'`x7#C_P>WZcPc{0)U<3stBfh)C??wY-4i3tqB8|s{zPW9#jV!8p=l&_cN5O-mhTwk&?c5S?;ZppDUbkg<sNC4-'
    b'Rm?@Jf*^t^@;}RXLN<&jwHiQkZkm@YWIjF+l2=S6d~&4FInp8a*!gXIRKOa`|e5@E2ew(B#D6=M2+SCl9zBW{?;S=sX7kvk-OKO$'
    b'Oi&+LN*`+64y$(XL&+jqpoY2nR0+{>1}#DP~>@9C8h`q0%W8g_F&qS2Qv<MLiQ}3Hqm?F2Rqm*3;MR4p^-'
    b'_RQ~r~MsJ_iD8WD5F#fOG^zeHB($uhf{1Kipn&El&eAW<fzuo2HMDyvO<LfC(BgiawL31WVN??de7XkZj7y}40uq~-'
    b'Npne|VniwSkf>Qt(ONCi4+}f^;o#HhYtkVUxwKdCCB6G7U!RRxs7flN&(*nwGzJRh#NBCA9nbudP^_9=KzOqdt#8!=%mS3jjm(RN'
    b'VvP~=GR;`#;XQtJe&$&9YO()b=otPGHrp24jvUsyi3-neknAUctwVltmwzEwi%vODvmVTzCpHIB>vrRGVR>hcBhNhLF-'
    b'(qE`rz7?z;Ql{Lmowx6<NI*eXh}-'
    b'tktBI`|3XKb2;n_1PfE?d{?>jy=mbTVe?Gq4HV3+To`=|#gaHTK7b=1S3r=zk)LBY#P?v0)wDzGIpit&w;h@aQV-AIEPH?Wa+`UW'
    b't+2~ocMaW{V1d9;H@VY(D^mOO(2faGO3A>escb=~+f4@K=C;?r21gu-%(`(<f=Xcht*VhUpCt&RvmA7^p-'
    b'nRnl5YYnuHHHqA1~_CmgzB;@Ov2A(PzL5K{O;P4+d%Rl!ZgIq>CV<(!<Mv4+a)$wUU7(FnD=hJkTE~_l^)te3@@u^2g9FXc1I^!z'
    b'kYvtdM%63mmJ6?YXAVb1-Fwia+?K3Jd`P!8SrKa-'
    b'~$PD03eaaEP@dn#8rFPV5{x&QSC7F`n{P5b$6V!jcsj4MFw9Du1OUn98fz0g{D=ZBs`^B@sKr6&_E?i2MGb}=^St*3hu3ByJmEr@'
    b'nn29+i%}>CQoOxD>J#1&R%2|1DuA`bZFfbU=cW0Q1=W!6?L$5P7e&fR<M*R9sHZ;hR&PU6hnaia<OX`_brOrP3xk1{JTx-'
    b'`D)M}UVHXZHD^a>9$pUo3cRO6CWXojx>+2>zATszQ`Jx~7CK%*$z(N5z>~tOz(d9a=dx3OM{44%XfPFT?7n!<2|r(9pvxBoI$BOP'
    b'Ovb2S0Q)!)5Lt`opvV;*z|ktdjfPT%_@s1{Am~kk8!0HKJH@y#L=@Px{1CxdsX)~ijAh!3cN2{Bl?QvXvS4Q`2SyvYdKriN+ETpd'
    b'EK!|yuzLuBRG{XP0#!K$7ixCFB%m7D%Vc<FywKTqV_-ZZBY)9vcRht*M-5i(V~<x};*9%9^OryFeuewufW-'
    b'~0J!CyH%PIb^6Sq78+oceI3vwX0P~j|c%|%-'
    b'tX>lFu!E&%U?b;W&P|TGCg1F_6r|@&GCGBtPui9J#k?s+~`L*4rL#KK$`5%A3=W+*DL^N$t2I)fE*|tCFkR5J|mfj$%&9)~Umfog'
    b'K&2>BH+w<5(m$7S3xd(T3bJgR<oYvbl7rsQiKV+ElZh_5PhECEFWK1$EVO<rx8sIpmYIRLIHvu!>Z?rGQYtkVMC69yg5#Vu|Vd_K'
    b'j3KMN31#4;XH&fmia5)pJV5yb@lMo}5uGUDSM@ap4hJN*enBVC4K`;B)t;9r@H_X4-SUJJ=^NCEMmMPRSg<7Ui%M@yvLM>CMWeT-'
    b'Sp_VDsGKE^MD%5g@f(_e4E%Ry(Q*>pDu1wLDDY~*(bfwUSG(|hHw2Km`yaJ*{lR>A@L-'
    b'Ml<ZpuT<HT*en44|$^0_u~h2I<{9x`Oekl$X`mBH$SXAaI30PYE8urJ_=HA&LMG!4*&3X^bkRas@zy$!hYHzh!jA-'
    b'7KBr(hGK{aVL)cxj6dnY3HNUJ`wp3N91=;wHTf1iS7RuY=5_S$Wif_LIP7rU?1sG<M3gM8%%M7p7i*YQUMP?A0O^%QE$0&wD_!DG'
    b'g|yQ1cKeX++F~u4VpdxuMO@z+L=?yv2gbqUUsYlUK3hhR1dnqj11d8U`mF!o-'
    b'ilFqDQ56om`X|fhWGL7?>ZFMW$a4s1uAsEYQ|+gWnc<v0{eG-'
    b';XmqvnMm0ePjIpCV^2+ojwZg_H}B3v^VP0=|Ff?pLPP`ch{wNqClJV==7Nw*Q1?NG3n4&9a=D!O*(W2LNTgCdl8Gn_2@|ccBGnJ3'
    b';o=vcW0QralPAX`i{`OWBK=IbZ@KVag&0cf!mEL=p{Mc$$Gt!cps_A?-nT7sJUmD)^W|f<h-'
    b'7)@S7tlpH;(`1b>r;pMihxr{QPh;b+zGmEg#+?DD;WIU6<n4AZ)&hM#d>&#U39QLoRS;s0ESKDE<JvydzV$#YAYD7-'
    b'FFWgWF@T}l#|giOV&t;AHvVg&b?6&JlXpi8#d6wz<DzoxtBN$-'
    b'LiDTPwL1fim*q(25zo`Z!f=|m;Kg%(0o%0258%(wB3;laXCZDWU*J6_S?MWnLu8a{auC|6}9O$u36=>t4hgujwTK^22^a39rybyB'
    b'8F&qVQY!v>74^EJ@4_bx0Q?(S}vvB2A<bY4tgJ2Cyh`v`i0R>^M0b+KFLpW>=hTy=`8o)ebtqk4R(dQ<py3cpU_*Gs6H7^>P7rJb'
    b'U*Q<U}tX|P;#mQyfy3g%A1-'
    b'155_0ySy~rkL*(^POV8pU@ES{uV(>X*=ukM})^mK%)?6ce9sYz4yd};#0U!Kl*7kZrj8l_?YbQ{L<Sl!9|lIc~SoBc5&BA1afiss'
    b';%CIyGNpskLBs-'
    b'?4>QLdC>bkmB%o9x~6xVpSNm{a#7x3yyIQCf3J7^5$;}YAMWpd^<Q#+0`P_IyKiF3|AjZ&{EqjpcXz$FS~S`_TzCKQayx(cT{-'
    b'FPptH9NwYi<YY`l9&|GMxi4hvf9JxsnNlm9b7#s2Q4kx4EjA3&irkc<gF>5@zirfTm?$<{g$z#^UHbbi)k8K??^^d;)(npkJoWIx'
    b'*7JFM7zdBe1FRE8)N4_GHG0HpR&6qt0FPQl<(QqUGyQ^U(d!)$IiC%r`yMvOTtW~qh?UW^j22f#C%yp55kY-sfYP6}5@se~&`6>E'
    b')QN|iQHWA`|?`ZD`jdOc~U{W=y-'
    b'4nO5O+L`(6e5$n&(NE+3&R(T|(7k=DzB1!|f4#LYIpZ6h*@GPUW*7Dw&Feth(!ZL{UyHBU^;$>!hil5NIdE0kcq>%qcmY+o3~&%J'
    b'bC?24HU03hkERMLZ$NqMif7C)t>GJFc11K%iV;`Ue~r!@hRlMmOcv=YHwlJ_7m?9@Z<LZCMci<m0_=MV6c`W+6eI`?kcxQHsIxL$'
    b'`dno)Dogm;0xIF~dNG**njv5|wQFoG-rPl_h<;fH`&v!VMcKWaRlhHNcXgz@SZ{8J!}vHU4p$w<bx@GLip+DMyfgDS=PO;%T^#ai'
    b'lfSsUzj(V8K?4_|p!hN|X#vNnCY6N2E<8l-ZT8y00#P;Um=$-)BvveynHP$~d;{Ui{ar*#Oc{}a1ck{-'
    b'as}T5s+1@gOu1835Rx&k6wrS*HCRd26v>4KIEoy8TNm*$Ifc9u7cmd9wRikAd-'
    b'*ZDpT}8lQ^8x@|MC3(ZsXFgd1hB~&ey%Ld+FZhdV^T|zu?(IShXg~SVqMt1^5U+pmrf^E27~>G2=>hS}<-'
    b'wN?>_{j#(R{8JJ9^YUkrdzw5{%fE8^l!MkEI>@En7uhB`yjnzV!EVXCwUf#0;Oj|rau)&BW7;LJftlXHv2Zl8QNR_HPGN)3~PQ)6'
    b'itX!#56>SZk<4s_hp^u&xHiZIw4%Jctw!I8~w}{XscAod@45oiu!=J_p{9|Ao=Hk5+J|`o?3|4LhmC1HRLe`W4)`|EtB<qc!Ch-'
    b'>5xojbGfE}KNpcS{9pU?{ej*j$AHr!Q+FE7j)MI}rF#9XAziFz~1l5_Z5xaxwcAmUW=T00;kt1&EQ#lfkSB<x+7Fc2xf-'
    b'Q~yjQ`+t-'
    b'GBL}I?>;bPtI1AbcC;i&25hFYq}}#bM~V5DqVfpb1T+){2Ry{k;omIeyxMGE5S~hU`1!NkcN<&N!~OH@`K8>aUpE0*O)9}ml~iU}'
    b'2CF33RROHk>PgHDU|O-2XR3J0s64o~P*l80@u>}XKR%+ny9VaxLoQ_M`>(RdVZY*u)+|GGI>bPNtAPf!%qbFs)-'
    b'f6eTpeWeLI%xLqFR&?w<;>^M8IS-U1Hu~8MX||YFPVHCo)DK@D@iiuI8k}itOB$f4_#i=i5<*>#y9-'
    b'C+eWZ+s(86ZK*b&3#Yr^yOspRrQH4u_p?eH0*04&7YuKMjL?>WC3#m`2Z136J!e{Z!K9Y1q-'
    b'r><F_W+Yl@k^*(pv@M2?JDZh0=k_XC`}XcAaZWvUeX29uE@<nFk77&Hvdul`y|zSdL;9-*-2Z6}viKIl}-'
    b'2R++P8l#7+tBU4REIRWigML1<MW-r^sfz4tH9;TncDUqFptIgw;GkR~lt%yc@<3b|G?;PB-*}*m?#x-'
    b'jk?3Qg8y4iN|kFUKQ;<r?JdFA2F0j#_7(on6(ho=_;?zeNPT8^HF^|v7?I3|}&!8jQQtDK?<u0T6;t^rzL11zr%7WR}wg@cxX!IJ'
    b'vxJ8*N6Jj4rw-y7gZh-w#pBXYeYW+P<j-'
    b'>;a>pCly9yuJLipFz9xEj{Z}*t=@2S0nd7huYsuYB_A3)f%2u7N6mUOM$6$Ho%E<V7VN*C@|;(6Pblgz!O{%0)$NIvhgXq-Ciz#m'
    b'b-'
    b'_?=Djy`XWra=Gu84zO|sqR$C7%0M_Z6ObbvN`q8l}N;O1zHDgfSD0C554;0tS|sUcJbgys|emR4{ZH$I`4#g~3x8{|1tUdju7(!m'
    b'56k3Sz$AM<v7g^gW)HQMI9h2d?Z*RB*j*9?<fIkb^i8K9%t3c!E>hy+Z?T(RhTP(i?&YD_l>IG5GARDGa(SDWpN9>vjCOyGQ{S^u'
    b'T}xpI3?$Hz4rfL=+RBQq?AELF8YiNJ<D>wr$sW|R^lFO-HGz_C`r8AO(OfD99|-'
    b'VbH%Z)A>4a^3O5BL=Ix^%zO%Ze4W`4^PW)`cC8m36uNHAD%q9fA<L|r&e0q;dtlQzP`YLmcH69_M4I`fP2klgFhHMkh!LoFAooQx'
    b'9c$^ecI2k;k6;BZ|8f_$KHq-%&gARKp+6Fa!NKNP*Y-O&I(V|n_F)QG(#sr5CNJw5M>3M2Y3iRM8}v3s@a@1()`-'
    b'n{U9A&xn}n}?n$6JEVllHRz%(~iM#X@t@#|ZraS$)AEjw8-'
    b'h<HSBtgG3Q&|N=RU5d0vjz~+nu>ThD&=9V0Gx>+)zQlchQmupTn8>w949p0yB<hpR_{8H$cSA;Mr|fC__I6~{L!fdjoiBtn)f@-'
    b'd|5Kn4QvmXj`0+6+Rt{LvgrCL9EDY1ZT3L%$-*9_oK$dG8K09-'
    b'x)Ok|DQV6Ly=J&6fLmK>_i}T<<V+l8q${72pS1lf2hx+pUAx(dW5J3lWrPFcMidAA^2vy-w7_^|qbhV7dS}5_N|sDGD6_zCtf2-'
    b'w*vZ_c9mGu5Rg~b5=0fFAUDDe50!YM4U@_?oLs5m5l@~h9%p-'
    b'hj%*ILYMa<D#(d>#j;vmtur8qAm*)c$y*vM|VSS2ItCcf<CC1<PbvCd2Ot@81<oJ1VKNrq;9Bx6O{la83ve#YrYH_}H^5pQ{k3I^'
    b'XXFNAce<lvPrwot+Xm`JNNpi?p_TFn9sM%1+^lL=Gl?Np?Dv)_V-D0Xwt_)Uj<`(l4b+WYV{PdBvz{4P-'
    b'MxN*6bGS?%Zw!3_kQH@ntGg+4^qV%xk+0sUipnL-22*Dc|{2;S;qSOE{MfD1;3)}$}TA)DA#h}?i3AmM!@6}bq``omzwtD-'
    b'%>xF!2zn6EnLN)@oTPt<@{1Tp8fZbNgxcmB@kw?56=wPip1B-~v4Uceh8Jr40s|b@FGX@w-'
    b'l#pGniY29(*0_j}P2d6EyXddIMtjSN{M-'
    b'D~8<|a31tug02iOkG#v&RLaG@eNrW~j%XBLc47RpxQllJsdV7Wj5&F;zN6CVERr{@C+R3ccy^BOH+RwW3q1?;K;7|~g0c(ASpum{'
    b'O?N~VH6L}!^#Sq~fDe?I274Nm~y9b`bzP!eIptt`iG-'
    b')%sn*aD3{m&fqbwz<VR^u5>`7U*7YPbAP@J@iyv8>=@G=Uh2YUK0aY<XUH4gE7*w25~tMHY<VAYEsbD6r>4}%PO=jB?SvC1_-'
    b'SeEw+#Bd+F}+ol1<p#yJXp?PG@dWQHlKRUP-'
    b't!@?@Yr8F)WYw_>GH4`aAr78XxN(S1a^dXY!n&!xjlEOnCjx@vk4bAW}ik8CT%j?ssDdwZ5I5OBQ(A#K2RjyXU3~kN_e>AnyF1Ex'
    b'JMpZJ(wID<04u-U50#T_(x!V*g_`3vOr)ZCjF4-^`cco&1{WPFJCDXQ%paZ1CIL@^P57In%7nAo&Y&6BN-'
    b'7W|#TryBq2EtdNq?%{Ns}r^62IWftc#w2Y+vg#IE@ymCJA&9`im%BOJ7G+W6jcV^Rw-FuD9=WcEE=02ATBxRBrYk@2*#o`8BX0xT'
    b'bZm4Yu{vwSE9p>TD+?{7Lz$9b8I9fm=e5#fQM$+vs5A{qmoM?<}v}p6*?kgH5m;2i+N5Pb!?GY$0N<Lczaab4?Hi7u^2PP!YE)}Z'
    b'6a?L8ED}_GFo*Ip)#%l{*`4)w17r&XUAo61fCO+E$3P6HpXOWl}<scWL1{<m7_sf7=8o%Wn4(%vd*yAQkG<d%>}CGa=_>-'
    b'TQ(bG0B6R4i9ncL2rgnabsOD+NiPaqT501baB7NySK+i;6rs`RfVXBc#@A$w;g>Q0DPzK<$`;pvx>hHF3xv?x@#saRqYNB$RZD9U'
    b'?RK|PkPFUI?Z(9mrMRRi{(S4C^MgwlSkD|Zy~na<cgJzAth@PQ9&N1sosMnwroH`JcU#{Dbn4um3!Fk=QwVGdflVQ>DFk*#M?aa>'
    b'DWo-pw5E{O6w<m#NNX~$Q;2E`QB5JLDMWQ{)B4Xvz@XbJIA(j2&Ov|!dvqo-'
    b'3D1$U2}Qw;Fv?V*gwrewtDUek1lD@X(RBxHDL%NbTOKmBMBR44p1D{Upp9*u!5po&y>4nK|1eY?2+o0;7!NQ<U^awWprIDLmL;AH'
    b'uoVYy;X*igl#n%y0VRZ&n;$W5c)WroBe5ww=?H_)Y|@D$WpG=?YZF+tyc!_^@c{6+mGD)L&cM+I;VoTSF+)+2rA)x$%2Wdy4nV+@'
    b'uR(Z9rY~tLC}tOM(gfO!rhSmKb>A6p;TO~P$DC@EHZ;9|vwzK=%3Sh0!CEy>t4|ncH8+(P1HW3WPFW`(Gt+Rk+8Cuos$ifn*iZ^%'
    b'gU_*mh5}r($|>KEGHOHnomp9bwb3}<%B?5$d~9fsHJq!r5AEmbw_D8Ug-_b-'
    b'd8%V1|BEFulQ>f%8kb?iJe567Kog!r5a>{*qO>cJg~|;B0#GrONE>%!5Xz6`f9dVLUiEIhlotgUg=q$!7$j}_*IH2G7ifI~KaAc&'
    b'{5Y@!NF|7utU?x{tkifv>wKHv^+$Lvw=q1=dI?fQIPGW9?$Ty8pAOG)yy<}!WieTn5>u4~(h{?^MtA~K&KrQ=s${4lTc5n81gj$I'
    b'lnV34XUBr5`yFW6IAd>fx@D2;tlJNbdmew>c5l?8%;xi>4tI6;UhD+dSo`}P<XXLV@AF*UZDU}@vPwysL77C*;7^f=pwG}=^hpYx'
    b'K?C9GqX!~SMY_r?Bt`|QIYl9p(bg9zW@P967?fFW;S3n2YjhpFcn~2Vk*JtbS&L-'
    b'3gM(t2C>dZ;D7?x6O0BAqlA=bcN{}+8vo;}#YDd~0M=g$Wj#<YbAgmb83yq`Gkx_j<r4|0LELj$4MUYFWt)MgS01`z&#^Tt6`f$Z'
    b'ms-r-a^@5=ozRG|^$_foM6tXC;0CsCUGB_9%r?jnBTAu0fjR!&8(EjP<X|>HWbEvNQ<Ik$BHn9E3%IdW{&O0@i4!O|j=UP@8-'
    b't$Du$~~u?WjPCBUCUy1+@YqI@bdcHT(>av&##Z<Usq3=sce*{1rU=<N-'
    b'9@HRtp{$$|nMNC@qI^L3#m7DwV`MP?XOoXoXUI&~87$U;A-'
    b'$Jgc$_;O}BpDhTJm8HC{){!}_y98GE}FrDz)j5Zd)lEO0^&16o(vY6iZObBmwzjaw3>HN@BGaubakT*_`+g8)OZ8MCHWo$i0@`kl'
    b'K*ZTVBo+H8!ACZ%?@Lu<5h<!)n%*lSQdsO7us9ZRwa5o}5Gxomgz^MHP=DZ1wuWNMr``hmB9{yUSl5FykZ?dH$24#y@ZI-'
    b'O9LrX!<?v?sO+rHSSMy{o|7)j#SYqco^idSq~q~C6u0Sr&MxolZH`K*Pa`|Tc3Bs#q2S&xLJhjx`^J+Duf3Uo2)?~+*l9j)T;;uC'
    b'*2Z}%JevES4~{d12Xu-uy3r%e>zr1rs3fGgMVbB3<<R)$Xd88+ONl%bElwI8h&AN#wjLf4B0JU9D~=&PkUioagSAsMZu>Aw3B?*G'
    b'6@P_z@@$nH~`^q;fz^zizO@#n1hulw%t6$+mo?lZMC|FjDvHl;?~{G-'
    b'RahhLPf<+<5qN}tgh?On5pd)E8(XZiW?^lSchoLOlVcS6m-'
    b'efp#HE^acF&+Z>zUv6I>{#B@>l2#e}Uq8IQ^uKr9i}veB2<9y%lEG9h+kAX|{?U8HU-'
    b'06~K6>gS32ZF&;i;@jOd|@NG=Py)=%k&yUggizeufPX+<Ge(gTQil`EmQ49v)W{30tlW&&fxskxjYjsl<;d6sN^!iK~*e*V@qr=f'
    b'tZHrc(Vpr)||upuN@IWsISm_Oonq9I6c05SmLD5s*dM#kKf<Fs@2X8PHwHwOG|uXLS^D43>FsRfe@<8do{tx#xy97*|TLVQc1MSN'
    b'wkir0QX>d6W(}&R$5g=OL^42kW7#c?56Kzt?;Ev@L;kx-'
    b'H!Fj>9ZDy#Uf_KjRsAMrL_55zjI!%wP9qBumq<kzM;a+Ge^q=ltfmGitsZUOWDrZcD<Z0F$_;0MmkkoEcFy<=*!sf#O=?OIJM@?-'
    b'gFU>Opyr=+bgPE&@=`GA{2HT)L{k8Hp_&6LPW9@n}lPMb~63fR1#GmV>Q{Kt3f#ue796HMA+eWXcIo6&P8rDs?CM)<Q1*o?K!0<o'
    b'&e%H?jD?nJxeQtn}|`f6p2@*^5u_&G?)FU3Haeuz>BQ07jRDP1PA~bg@MiFuzh_uGw%dy;8JQwu1J-`g5yx?)d7B%?QnF($e-'
    b'EP^XSd_p_VfHTMn)wq~dO4BB1yPT;|_``H+6I!SyEV43x_pN%ZD|2ju8%zgt0vCIC5Z()`z<F(Ez7x%2mx)wTkXQa~sc*JSTJTt6'
    b'vCA{T6+vJ$HI%h3ZFd--'
    b'?g*T3A?qjB+oa;^ZH>1*9b+Ll(>l^1>)FP;ug;hmzPX*O#2+T+Zy%WU&GZ~#ERIY{;i)eB@b3yf`vn=ZmJW{#_?=`@LD`k&E4v%m'
    b'&>!T-'
    b'1aDfg)NtH_z1Isee34f8fch=^>tiXF09#U4)B~JzRbgH~4=bIfX!?xSuYZQrg!=``TJ^azyg7$@56)1n>9&&s0`gy;|;Lm=3{a(Y'
    b'}b6FaoZr^7Uy*=ANEvBH2A5&e5_A%ss=5N+}=g%pB&%d5&1JNF%+Ro;;ZZ=n5tGCauFMcaUNqdRYZ};8cbfRzN-'
    b'{stIQrSkrlNSl<tu@{=XWe(34DL4nc$%cI?7i$JyZfx4N<h27T!JQ>Vv?Za)!Yj@jFV)L0X9KXMs}*B8Mthc=ckY~PnL(^%zD!s1'
    b'b6;6DYC+y5;_Cvs3@upl}^}JuuCsPluYPitYOJ(!%P55QK1NJf^x+PJvo8HY};VlX;76FNNsT%e{+?*lfD)Q-'
    b'tI&yIVi@G&caYp3!O{0D&*oYQye2C{jlM_onN&K^9hf5LamUnWSvox4lr1&oRX1Qr+G<MN#ktDHIetJ4&EnWR4aG1VScSE7cf)}1'
    b'i1-'
    b'7^_Zo_382PhcAu>)4pn2$P8t$km%WS?Xc|hPon@5{SvadIL|YjjL?}E(3_PTrL#|zRw1<1qIJoP>{frg?X|?b6uH66e@`Kj=Xti%'
    b'~Rj>HPX+Ql(_auDL|G_qx`K3p!x6JqLcH5HYO?79h<_*s`4Q({?z9BwOvp+-'
    b'n)iT0G4)umZ<BJy}fKNZs(*H&~?Rw|Dl5fAzZ*vf5orW$p9=C5wGDr1Ba2wI_mFO53r~Qnyefr2!i{F+l?!QO79lK@G<Dn9aD$3e'
    b'1<HcgmC#h_8m8GXXXA*~DDUyG#<~%rO&ZE6DfUOk?**iPZj=CO7HFd8R1wEF}yzH^KWr+~_?FOEv>}MM`9{o6_^32=i9(cPm6kDt'
    b'!{~hc7P1f_>tmoo`UD<{<nb|YsKiWGZ*j7`!Gh5OwbE{X)ZSTR8z5TTIR!k^#vZH6UqgxXTZL*?gNOZJk;;((+>ZYVfyDX>~SkQh'
    b'k*2#o^9uxW$?*GNbO_O_>5@xh(ML%aRn?o|n{%5o3(_IvQ-Tr)C+3rJ`s_5IXoMbCWo@tbB=?%Vq=i=m)(eIztWtrWefAYNY<Yle'
    b'+zh@#z$%_m!GY#`5WA!3b$#ZtNAW|Sv<``fkgw!r;I?&c@xZNJLx-imik9c@2Ph{Lzo@{OOv?`q7lHdb;)x1eR#wb~bE&^Xmk$qt'
    b'd#9G2vRjOL5Be%*K)8+BFXeR7t?%CyYW7A%ZBhrVE7(chFM9MJ_t<gDxwV?1BB<-_RJKJPwmKr=aH_ae-DSLYB6;5K(V@;Hyl9rw'
    b'*bwa@uQ!;vQa!fo4>61}`VWK&tPs$7h3#vG8`c`T(WmjU#&XB}sQovIcu=5tJJDIzVWgI|qFo>#sEHbO;eF?D$4wb7gzRZX$QZX1'
    b'C?@hA7>SjroTbDx-ku?amYqMWeVgA`(Tw-'
    b'zY!yTbP4AUPZh}})S3l6N>K74GKX?M|B|A^SYv$p#{z$N~kJvZA^yWL9<v}Dx&yUVz`>~`10%9s1~e{f5S=*Am-evR!g^}p-'
    b'}uD|hO$m&Ry?!)8rkB8+NXA4~0hI&}GGi@uMk7N$p^nKIi_RANv^gN^28GGdN+w%0(biCd5N#D{o(=}N=120~aRX&u}tz3B^sjFp'
    b'q4inTRXQO-HO*FT6_X2{sHfA4QEYA=!S`$mLCYD<QNJFXY$Da-'
    b'p%9W?QpG<D+>m@{TFkl~EBF_+pTa!pRl*lbnxp6bukL(>Lmi<S)n^bP=?*)W%Fj|vLj>x1sUM4$`ImzVjB9s5zNtEU^nBo-'
    b'M!fxr|^&TJU%LU@DAZPVp&uu#bE8ArkA3fA&A6^s3Uqtq35#jY^aYE};1Qy?-=-%0L<#z2Jc(7t?eqWdi+JAUEh=a{PzEF|Lk>-'
    b'yHx6PY*`SsY?;rW7KFHX6<==?FF)s_#86|LTUv6vCxe|gBA6jSAAjj8hMkE!~|An_rT;Dg{s$RsGeQ~?yS9`a+PiI6WV1*b{|yhK'
    b'igRg{L32-'
    b'ub5mxlu7p|_Dk5_w_SLA!)t0iqfd3}c}5iyY9)c%69_3Z&JM>6Jpbf;awp@oIj1TJe+X`+dmep$}cIZkM&$bBV~Ris?=@N$CuF4p'
    b'$CGUa7E~W3>h^q)a|*xN^APN`5{RT^N)I<7MR@OGJ}7duwy{k(P))wGvLtMAI_Sv`jQD6HUuR(=yStOf)SMP0K`6NPb!-'
    b'nwE*CWugI5I@2=I83J;@!7|ZD3@~o2ai63M!U~s+m4Qh~hk&ByS@G&bt+}ZXD2+8d74Ie0+?6h8e9r=p>^E2@V%2faye~#EE~Rn7'
    b'fTk%{xMm_{5iGDWP;;(TQcfQkON<#x1hw!^u@jex_<5Fz&JZWswM?`#Ui3ywMPmP@B7ahBRh%`pDy~1as=*8;jD$`#K!7q!(F5%O'
    b'=~ODM?qN-'
    b'G$dYRzosgWzl4UemnpBI8;)Ih#A|w%+lQzI!86$JXUzx!TIpsC2%9fHe>}}#PQ~hcS${Mp$HB%K^J!;8?QCdfBB5z_W6nBw~f-'
    b'WLd##O+-GM)So)lrpe$7OM}D<Cl~IM3o3OHO85=@hg|R?*04jz`GC@EeE5aUq4vI>XpYS&|Vp7bvI8Au+FP`It*ZXE>9(V{v-'
    b'ZIn#^VnmreafD{6Q9>C<ni)g8-Y&@@Uvd(ZWv=2f-'
    b'mSwHND$6*0tWm~G9(klBZhI^gO~&l4joC+9DEh=II4u)R%S6*M(X>o7EfY=4MAI_Sv`jQD6HOucX_;tRCYqLs21Myh%S2}g#(n-'
    b'}q7NBd+_+5SVXIgT!9?pqa4|}yh03AQVpCC8Go_8wm}ygtNr@Bmi%v##$y@U~EE5?is_}wXoomS6D2$QF$tWOU0UDQN25?S^YTcB'
    b'eXr?`f?nql?*73w;B5|H&qBBH^_B>6rDO&Ufi$rqo1tQH3jH$MD-'
    b'^N3!a%(8Hy|W)5y#5Gk^t2WYL!xwb5k`P3@0H<67w;p5*osTq2H+n}8wI?C9{|>oT6m}P@ykIlIx>W83p7ddBo&L%!@zk_EQ2|Mk'
    b't&f6T?FQ#j8!NRwe>Kq%rX<*sKu5hc-TkfD&9>SALv{_C?V7Wvt~^UaA?VRA9xLh3*mt7Le{XLRI=u%g?+E!6iBH+m~}*Nn1$!0u'
    b'nu5k@!AANh4GA#UUOv<w-VUV!OBQ!YvOOQ9ON<!ELRK-'
    b'3%=ycg>@W*N&}G!m&RykFsoV^0AFjWv=IaCWt2fh@780{9G4dZgIKLjStlQX9$+Q4F-'
    b'nP4L*(!+UeMuMpD7w|wD+uH^hHu;7>oXE_EhF(pi`qGBhcM2jWoEsBt>Uh_FNBwWQr`JRSBY;h4GmFglYAa#-'
    b'dnf11lA>1#fPWFeN6HJv2^erIO*h*Mlb8bz$3exz(RZ;||fd?aM!x2&uCvq&|hzPYV`ZVpWo#wkp{T^0X>Btx8VIKhyHhwEQzI|4'
    b'gCw!$a-'
    b'z&@j8YT#)1X!t7s_Whv@dy$LBxZe*ft>4rtP6H{{(PN@<jcR4!CGiVvqI}}~B_TXyj>mW$qJh`C{P^9|p&+ehikbN#sGb%Ll7YO)'
    b'cQ|*06<o-j(fi^|%qoU=8Bx6yg8s&mYk|)TE@Y1s+wev;Mm`4+g)mr-?@kepSTbRvsT;zU)&b?FAUT%-'
    b'tC!K@fu7LUK#H0rp&n6V5Qo^XIh@sIe3&3wmm#3w*-g0B{DVN0uw_ntLOMK*%VEq|L{aCPmC%Hd3M1Ka7-'
    b'#n{{s2y0zYLz<fLtyu<HF$<1RcEgy)vw946rnaWvUywgIaA`Dm<q203SGIW-'
    b'W}hm%<q*{NFYqQ$7r76<k*QP#<q<nzoukD`;O@8i>xOuu5KGqaXq{4387vE_}f{j?Og8T*g|XX94My?ZZ83nR~p`cl!q>Nu}%RV('
    b'vX+?m#0~oug!MIWNo#g@a%vnVO>iymix$5%G@{$6QPYRg|VV_0a}(tdZVNF4!lM)&Z847^h+T26sOS6p@1Pp>!xIzi~}~NQ`fHOs'
    b'51<J$e4u)y$Y80&}1|V%EXdrG8XsiDz3P3SRl+q*;t0LRq>U&v2;DT*WL;MUDlZ^P3CL!0D&IF6ta*qNI~KvlBpmU(HN~OY*nhIn'
    b'j%ZUWL9B?SMX1U@hB_!MH(F-%Gd0xWZH58O96u|h2<8O7(ZSMQ)9p&TBfToa4%>aE*f|@XJ?gj>jSh+OoxNh*}wMM%>!e$4-'
    b'A~M0cGU?53uFJ+gKV$&QwEaWu#2ZbVN(oP_>fWF&PANNx3X)tfK>yp*UW;5-'
    b'C~^mC4o$IAP9lKcrDXqH6RiMy<3F!KbJas9mX9rK+3A`e0z7&?E@t7V_-'
    b'*@!@&aayG_8G7xld2yZxpe+*S%Mtn5U<0}>wCPf&YgvUh302MGnNWpNE7#r5*lXecR-'
    b'9EGtC=me17xaijX(+ijFC1c^;VUy?A{R8+jDvRy_y%JDS;GIM1N9jnT98}sr34~m*~2b+qDV}N1d#<>t~_vvxMn5+FjNm?1S46U;'
    b'Z{YFd0rn{ymomk_~ZViDH~b-S{Y(kxvF*2%4x%bA%6)<7FlMPF6+3$z{&z@EIbF^3o2R|<s?+)8T8eT3~}#?x9t-'
    b'*kFnc6#(1icg+p)@%pU&MR$<P0PO7+K=woF|;=EL#X(oh_5Q;)6w_%}_8y(|-DbPR-'
    b'2GB|srVETb+7q=}ATJjqBb#9j6BaH4vn8qY8T1<xmAKODV+;h_y!f}rhr3z&_3dYXRsVa3g3oWdZExB<Mt+AJGNKC5SeYq7sxnal'
    b'u@Ov{iORImVN1)S1+rw)I?6v%1-'
    b'Gm!46BHKbc}3rm|x*oAxjE?&k_a;Qjt?;wq%Ghrr$Pe67bC?qmPVf_);LlVA%Q?J<Xo~_3bX)m;FYEF2AMAH;)Tv+Xn{7P$``)e7'
    b'oY>M44PoI;vo}50b2*lL`RVJLW^?fZWDbg}*t2i_dJ_DL6rKBS(x(!w(3bGy^U`i-'
    b'l9%2km7VUnO{klYyGDkSx^JmH<4lJ}@mbp1u6~mR_Hppfva8`MH5o&o5*3XNM!Txc|0y|84L7EhEUckDwDuR#^6sgAsyR0z%9H9D'
    b'!RYmoV*sL_T}XKw^N6oQJib@16B7+i}s-'
    b'aL!&tn6^j(AP|irpvnnE7gEM;FlfdIQ#@@6fjiNX1MI+zN<)@)eFS05;7#uyVz>jDe0cmek96MzXKH|BGL~pmf+dNdFr_l#&<6ow'
    b'@Y*JDL_&Q<2dfOvF$P#~+P)%2hP!>vEj?$;z>4hyo58FUVYv_!o)2ePV0_@cqJv}8kz!;zRfX3~7*(wUtgtDuu;4*r%;>;^^uTU='
    b'z-'
    b'vm81GWolDVQ<_$Ps@+3L*1C6*#J59nBAXGAt|urc*Eo8wR$G@Xr@eQkmTmAIOGd%s8Mtb4CGK#o#o_1q5Be&@k{={4L<Lf~tc2w4'
    b'-f45xf!8U`9r^i^OzK*fO}1xYy$D)s6FsHV*~ZaY`F4q0+GHE+vj$C+7iiv=jmO9!QxK*m0OfDTT!71GlV5EH&I4hdy*)XJNPmQq'
    b'fSf?uOe1#kyVariD9P+|hf${Ijh^oqJ+_6Vl7<&o*S&{p;oFwfy7j?D_e1Y}1+mgZ|DqZCYzCnJ-JVzl<%wy)?TOQojiG{PS<~&o'
    b'|Wgz6;OK<mCYTV46C0*@KGqJJ^y={Hwd8r{ZmohfH%G>UP6nYySLJ!_V2>uWyUJ$<3$TuBNfoyOA|DTJpHNU8^15bbNKqZtmvCF7'
    b'2-'
    b'$0FTplL|9V=;+0GW&Qhwv!vHh_%`h*ay9MwW;4xSU+DyetJeZl}wur914vDnN+ACh(8pmODdAWYrtp4uV`NyZ(pG4Od(i@&$X24p'
    b'D^}Wr*Fm~nYDoO=@k*30vxD41*VU3gJ+5xGUQW7Xt4HfXl2N3|KV+A&;79Ll-'
    b'?BdEOG<}{w@m!s6XMW!G%{^VeuHR2eF9zRcfv;&t2f%$SfNlot8r~2l5Y&n3SUE5@AT1CJgOAJrbs+(z%k_SanvHG!WP5k=cId%2'
    b'_j-'
    b')WuO4tYJ%({$$4B1j^5Zb1?W>c2dYIzSF<5<{%lChbU$2b886pygj=}mnU49%!N${%0J3W4I=s=9T)a6HFo#(C$!x<?4p~EnIqsx'
    b'y$pUtic!Rh4v(B3cK<?{XBhnud9#~C>Lq2sap9WOsltE6(Z%-rc5{Lm5Uzs=?QzDE02x_<_yd}#LvFLc=XuV>tfj}-'
    b's5PC3T*U@UMVvA8)#UUCC=+7Io{m^Zo`8ZR#0qq{97o`3Xhu>{zKnCDHk6fQm7zm&gw{fYvB*Jpvh0q7YI*2F0A4-'
    b'*}C%3<nEb_$NMcu6X6gv&s~Qe>-'
    b'mki9nhk&5|C%<dmwU%qu$+(Z?tDpBG=PHB%v2Bs?EZEu*TXs;86LA5v;*`gv?2VhuqKx(C}IyryX=>s!=sXzJG>xyBt`is}Avp-'
    b'&+1{?OcI_+me`|X=G-+XJo+4NE`Ppf(%Py1PKdhjaEhnu22>8XU5%>kC?RN&&`b27gR#+jCZn|T@rYT*WtE|2JI^F3|m0($Ir-hO'
    b'SryIrs>GNPe2(SiSJtzd7$#A!bxZJ(}-)Z({gi}M46JDY8#WHF58zVU+Hw(_-'
    b'j&sifq>#gq{_u1rmmPP@N@`mY~b=v&>tu`mbhu8b<di7EEF&trm`!MUmn*Q(C*%J&{rNac}t`+}ggK&S##ZkI2@7|VeryB&%+^oh'
    b'bzQ5Imk7I=Hy7q>Ad|@+hENu2>Jt*}3tv1peBXFN>&&|gdS^LH!>uyHEci-P?hte@J`)M~beSG0{Z!En2W*Bt+{#N_Gj*;A}-'
    b'6Hn!CC|UD<Z*Vh40wNkt9^9G$lO(Jx%>EX#@QPS8o$}SlJNbl_A4I6X+GrE#!n!r{Ea15-'
    b'1Jv?zQ5HD&|_rsQ*9Rg1fnY5SXAZBU^VXhTWza7Mp{4J4%|;5vGP(9+Z>x$=SoFVqX#p0fRq$?p@YE!tULxCjh2vQ#)Wo(o}QH)I'
    b'pwGT15(BoO8Lz>pHh(=mx{zoC_XDGRQQmXd`&VXE^KrjBW#?iwo(d^NCjIHQ&9kPD<P!-'
    b'6AUIFlZpgpLJ)9r*5IkBTILD`+oVqdnrXEXaJYCd93QJx6WD=(I$?a4FfDOoDiTV(2rS09^K>HGs35o~XemO1q=UPJ)#JsfOciK#'
    b'CC62W-'
    b'joDkQ>UaN!7L;KcU}Ct+5SDNvnHbbE@?^B_Ov9hyE?~WH~@E$8u+>}Q7s^_)0R%XQ?Xy6D~F5s%s}l@@swSF^v!v{BP~f6&F`IYA'
    b'5ZXcOj43FtUZh-CAm~Sk`1Df)+Ta;g<U2l$>H&3H75XV-'
    b'v8%6t|(>6YVUC2>;3C<XML_Qoyk==4HA!$S=}eO!8~c$*H*f2n`F@4cC&xKqC0(+nr}R7FRfvA_xe;;@{TRO+;|r;&xV`gb?;veP'
    b'p`1IHk>Kl!Wpc^zE<L@GA%U5L+?|Epm!{4pIqL{9e%65?>iqoo&{xj>qf_Lt=YUY&=IB3Ni3vbm`1Zyq?MbdnyzD@<_R;cERl5?j'
    b'e!h-=4c0$BUM(%S0Vr=0%rlC$->qkSk#5k64Rh;G4T>=1w2Yz7sm~waxZvS!2`$@<0Xnw*q5{LR#wA2%b-'
    b'aSz*=#oM0B7>RAk4x;=NS(kC&t(uy>>lInEZL@kU40j;SDjw0`St%vn)d!7LdB(Q_^<lT@gND;q@(7)o!7$u{AYq`{BR=`AV|NPr'
    b';6G8IndfxCp)#b|q7Ly0v|5<Ae6CM#$(;JSdqK1rz|9OzF7ek9`&D^PaD(bEiLleBiqFylbcy)?kMRU{KsuArs>+6f;AXB?%0G1}'
    b'*0x|g8}otPDU+1y~S*n$dn8+hBN-'
    b'E1~AdsZdLwSeSVkpc3vPhju7l8SOAK;x6jnd%c{lWPJT&ADg=nN(5+z)$AY)~W=PC3_o7cDcF)ll~p6e+R~4xVW6V`KYDW){`7J@'
    b'ss=Km#5b>-'
    b'vs<AJn5zYiUst|L3_b8?N`Z^>DOsk0%?uo(WIcO64uyUnPNT%=uuWOumCjeWj!u{vbPevQz%7m52eT`YsHvBHLOmt6!KNBSQoW6&'
    b'J>Uh&M0=JN>wIDnWQC6%BHC7xZM#-'
    b'*~8VG5=}XSeH@FX?68x^22{>xFPBl3!O8ryp2>gjBTduEqa7!Y=9AvJML!)%`dEjOT36jF{g7*%0Zd*6l)08uSJN4)^PQnO-'
    b'k)9Z5vzA4Uu%B8ouFP=z0DNW3gdEx;Lm<`r}@|8iv_F8Ea$9Vbm#)k-'
    b'peuVfvj5y?X1#jz<wvZ<_kmTtZ{e1V$+6&qWO;Z`Fhcob)w}4ssvkCGgDawLkOIkTB-'
    b'+;(H^hn68^Lljshf?Ap+!CItma#a07=xjxRuUZ*t%|)aqTEw*Hk$0pi8Qb8yhV{GY37_?J5<!Pbp2PFMy02bGgL3Y{T`0dgmcjsa'
    b'Q@Bv&PKUPB9=HrDuBWzE&sL3;nTSk1^0fZIh%@WCA`{p=?@AFCm-xvr=nU-'
    b't0&g2yzwX2SDx^Qgy%r)DR^{G8!g4?*s;+BUzYW1NF)yHEG<iMNX`9bJC<*yXWJ=DmF}Jf~;iNAKJy73FDp(V)%2IvF~2JHyNM*3'
    b'`by?^~{0vC_*M=3ngN2^!)j_OHyncN}?L-'
    b'p5Pait$+Th`M~FI=7&Up(rXIsl0O*)K0SkZF5G!=rVW<Rh2bB**3}&LF`~^1CXf88U`sGzcQw{$(iL)m?~1n9B7kvj=*|00BV4+3'
    b'FoR{OnT1oze@X7m5zltTw1L>wDfdvTJUud6j)^~K=++Uioq+$U|m!9gG+0`{39GXxN4#E-'
    b'kJ8G2U@Z?CZ6YL<D>;x!n2FfKm{&(r-9WCoo7_|!?FaxMqZbLqFBKbqy2Cop_#?ESQ$Hmqzx-qobIjq;Bcqc**n%WZg96-'
    b'l|7fgOfXeQAAPPY0x!{?REQ0u`Yq18#ItaaCMbx@Jc?Wsu)M0-'
    b't15hzc8{Xmli7MJvvs*;uu0jrD%<vY+>*tjxO2u7t(Xy1PhA!vTvgzpjKV<1lIzf(LU_<Pttw%~!m}?;ZiL<SxVLkWLG{j;@bpJ{'
    b'`Al_>cXWR$d%RbX*-KQ8=TqhQsdD^OjeDxbJyqkLs&P-%xGyJ@XNWAX$)wr<GxrzG4r+dI(cGiklZ0-'
    b'q7r#oF4%{55FBfq8sCxr@5xiX|DnDWXanpuCQ<JwbR3(E+F*=o#lFAAlSfx!mAS;<p|GVH!a87Akt+YG?J95vYJ#Ir_5@94R@Lt>'
    b'h#P;ofmer&Rr!Yg%IT^~5Q#_O;!WBpX49&cx`G``bB3)%R>ZF27A-'
    b'b4$ouu3|%y!Baz%#^##<l?Nj1e8Y32?ty(b`6ZDYy7<xWlivz)43IU#S?^{lnAGa5wwk@O`8wd6};N`StPfZq}^GPJ8b5P6WPpT8'
    b'q6iP^{_hrX5d<9SED2LHvJS_fDzxn<1u8TRP<alPulrCvAfGR`MU^rb`M%d&Tl=YF#Ao+w5n#8EDF4{h=|n&)*)K{Da}{?%^-'
    b'U{P!B}o=fj6@%_V>uI(?&w!b7?-'
    b'&^A+_tai=yS(VOdjVY4G7(&LI}neBZ)#uW=JD6CV|8{vdnw;yNdLNf_~ToX$E_RG?hHJ7FzjQOSa7_DZDGJg2fJ3jv=4p$@<)N=n'
    b'58fDq%X8*=LrV3e0jLP`_=F7ZTn)k-HY8e8RNQ%?3$$BZ0URZlAC)@?T_^B@cDbhD~3NPi_pW%m-'
    b'06~VWlUx^rYL{9k084s&>BUO?vnPkD_9Qi#?5inETCBS8%VJr!Nl`U4cDXNN3~lzqC!Q&(`kF^t--z&!tx&D16?YFI?6~=>EcvpD'
    b'+gf)vGQv-?4hiVHfXa&p(>)=C0<{A?dOrQJY`puXCmm8VUM$5rdVkEL`bv1J+N?cG^(<pG`~u6Ak@O%GuCK%V~qqOXzk~?>h1|-'
    b';!{)X+NhX;2m!hUv8T?Z9W$py{}dAyY8Mt*_R;~yyVlbEAMn0GHTxREWPj8=?Fi$y6$%c6h<KXzWpDft^F|DR@AZr!hXI!zkIm|c'
    b'Ik%W<wyBKm>((`XLqxgUthXbw~fLY+Uk$Nepv3nQ8)~@4JDvy?aT5s$@3RFef;{fbfPeDXh(PbV3gMwv1P^UHU@B}US|mQ^9z3c`'
    b'Q`ETseD;|%9q{=Y$73Rg5Q|0Ws&aYruXUgAq3>zI=zd4?CA2|=arU1d^IDnc=xq2nFHSL7-'
    b'8=?*ZBsB)|)78)WhBD#~771iRj{mM~31!VK~u7E}EL##^=sBHl6&BZ6@+a0XWHo93T%DP_AYB!_itcvELAlNW=Mc>-'
    b'pbz4TgAlc!6+-'
    b'$I~Mr|3myA|MB1XfBbjxAOC}|VT$(MO8&C?j4wYQ^6TBI?6hxoyLhwH<zjbNxB8PS>F6$ZGS<!Q7W685xx;>rcd}!8S0l5xT`yaL'
    b'cP@$D*voej*Ms`Fr?4)2cm<NWy@N-'
    b'|X_LY8>P&0%R_7AZO<jCXle$j__mt2@_pZm3j`r>_@!TVRaxIp1pZLj1a(u*CypR1oaU^yL{66Dw4OaTlVc4x1Kf_&pc=}oL&Hv*'
    b'3|6+{a{K-'
    b'vI?JvBfA0>ZlJ3+Rftx%l8b7@aRMT%>tAG5pMbe?uLq|ipq@a!Mq?&Y>)jPWVlryt8B?6)uF=_hT@1k@*({`DV=<@)(rN0YF5nG?'
    b'Dj$VH=V91Wv*JAZDsO|C65`t^|>@IoDI-jayyQ@bmmSsedg+}%7r&3=aFlvHZB7vRG$^nh>OTbI8d3+3bMUb4+3vmBY*$MDpiN^c'
    b'I{_o{Ekf*~#Q?@0$=XiWa`^}n7QS!`B*(bj)-{lYBJA^@6v*U_Y!WP1(ie959=e$>{Nt@HBb+kgAA@1tHGp60`F`xO4Vef|-'
    b'IHnb<yyR3X>R@f-'
    b'BkV3j#YpfziCL)#2!cQ<cI#oH7ww4?%OI~N`LoVhkZLZ!fvGYOe5AiYqN}IAJw0m|pjPK%LQ!mfZax=i9$`<aWnhkkgZtD=im3%~'
    b'SCI8ZU`D>Ef3y<l1XUM|SwZr$kuiS2)6B63(t#2099D-'
    b'D)GH)ceRtZIQuCh0!mT0J+RTLqz=xg>xg%Glc*19S=6+yIq4^h3aIam(M@fLQIp#G*77X3;8>XMTkWKcKF#i~_ZX?~+*7CMrwbdg'
    b'aC=2Q%dcA?SkVSK7saY`G@IFD6J7EPvNU5Zze@lTbqeSag`+ZcfBOL#g+B*mCWiZ4w=lLbA>g04--35L_tK1l1GOvW*)m{dx1(p#'
    b'f-'
    b'&6K7+Sq|UsDl^<E7IO5$m&l5=R2R6uzu|0$VVkONl+2KtEnHm<!=7|b2J<k3*`I@BjAXE)6d#S{ip81~=Q5`PTbL46SO?%N%Ij(a'
    b'V^Jn6Q!+6X#zgVSGMnGuNOs!`x;y@wz5JNn&vDJX>frN1;wi@rr<_dYQ6_V*={doSmMjC0I;Z9^RnXGXzH+K^OdHR&51toRxM4i#'
    b'Y@_Eexl~~|%2K`e`u)vlHwdSo&kYhg8Pmgz>G(_>V^*Uo@aR<p$GPGxN&H<ks1QreXYWF+(m-^Lk|8h=YN*v$Zz$VC@y0dD#}-'
    b'qT8u4t8k=jd4Wp7ZZ-'
    b'@n@RZ2bLjPdmi!(^L8X*?aTeNRA|5@T(;1uU$Z7`F*H?1$s0+4+He<G+F~a;5CGVpH;a^X0kKMs;(LIcVDx(BQhd0c#4#wsDl-Uh'
    b'aYzP&&==As)&lMexhVm&D`C7^|AIX?^bSACn;b})FLgVin0wtZ~T8@<n1#C0L!r7)$!gRp)2=wVp&1vx9;0^?_xWtpnEjO<5a+`X'
    b'FM8A2;@<EoxG5e8cf3U!2jGv60tCmjRrHM1WP^>iYaw{{;8mJWrkbPpTFP3Y&8e%O-'
    b'ywq(#n+Qas+rp+zn2Dm;Bvszk{Z>>!vJzKJ0G_P~Lj?71Z{=%-'
    b'RMjy1oRS9O1X__v?)EhO%$Bt`PaRK%h7r6bXYD?)GQ8GW>j>bGqcwd;w`-'
    b'*r^UF6stZ$39Ov?CdIEx8otV#w2kkKGVXW3?BJbs(f3)T&>T2i1-pCMk0Wb-'
    b'h^aW97(a0Qc;W5KBypjEf<z{t>85wjrjG{=U_d@>gnW3pJkXcBeb{e*=j2mQ!{f+j@b<&WXVAbX`83bG0Qn5R-'
    b'zOhFLO!CG8&WLT!<3TA$|nW7J~Qtf5DewkGp{&kdmf$fNg853T=#)6m7~VePY#?dJgAL`^R(0H+-'
    b'qv1PMqTv6;D}<qn{q~Oo~U0EWPY4eca!;&F-p9WqmJeU-'
    b'q`x|HVURAGGYPy}I7#&U4j7f*n{Mc{^PF+H736g?m2s`!S0qPF^XfqFe>AKEOsT`rjC-bLn7K_XgA<N2o(x_l}Txgk*>;8|@9){>'
    b'eIr?kNQ))!MA0@r(zLN5Ojot^pI^q;jtr$8!R~XZ48%ex5pRHlNBFCLq{)$KAZD+1f)=y{3_RIkobcM28w74t?EvRac$t$j6Y0Al'
    b'_oNn!rL5gcz=q!!wQu(>7_NrPeNGuueD=;67?*C7y2#)Fq`<$($#X@qWH4i99&P^EJt++qpI~`I$&ZkC2XOsz^PJY^0W;b%M@R5+'
    b'#iaQX63v_dXKg9kD4JLM138M|t$tlI#Uhcyvr4GG5R<r+r*V=2b|>jF60NRS_onR~6W1(urf#IUy{wENV`K<38~eiS|C{>_FN`7N'
    b'f^dKgr5kPC(=+o`L|4WUPOb7Ah;$jnWIwSY1QzA$0P${*hVT!(H~}0#_CAex7Ht)O{#DiCF}4@(Pm3-'
    b'+HIaeE9h(cFO4o`ov*RiGz}Bn6N7>O}al|6^Ob57sld%S8i_4h!AV>z*$2W6)Fgdo8l5r&!kE@O`Rv;?b2vDkD03|GK(TotWs+Ul'
    b'l+u4dKIIp!UR>ZJfM%ZVBQpI)WydhLKkHec(~%ddVF)%cJM;M{3qpNg#JIX*?ibwZzU-iSxI_*x{5fuIZGKW9w<vCj}+`nm4y!Im'
    b'>8caOI{isjdHNaNkvJSBGh{AKyT3O4Y(`%f;K4D@TyS?FR+Z2^lcVu-'
    b'46P6b?bR5<^O*BEX!TiB%QaompU+5?UAr2){iV_HMnDNF}0Y}Nng`(=AtG#@IsVZJcZGFrX&1rKyXv)z2?yp@F)n4N(7RFWh5oy!'
    b'$X<1SL1GUovV&FF4_a#&#L5O3qo6uohdQ4%{2DZoLJS^dj+HOBrUg*D;W)*G|dxCAn_dWLqW>KS&G?eZ!;50J4@keVw%GITRd=Yw'
    b'osVpL!VkkqMVdpe-Y$r2M?xrRTlob+Qcj8k7$}r5)DQhzzp<wl&X&@Y05wlFrXPcW}4`v;3}6{2SFkX8qW$$PD{>-HsFk&5RFft-'
    b'IoneN)@~t;^mvesVWb?%qJ*#qp3SKN=)U@+KOopqNS!1TB$h^0=})jK0-'
    b'j%r%JQ!<6mF^f2#Zc*Q)zJHogC2!5IJ97DxPZsiS|QAFCK7IibFr{g)x}k($)X4p!?nmuz03#{-'
    b'%h35`<GrMWVken>?Cb|JWi;O;)BT~mDd#c8da{aMaT^<+VGRsYJ)wq*l<CGu;!)+fP{5G|f4-'
    b'jX0zm%M70>Gw{8#d59v{bqZ&!CaTSm#04Zu_%N)hy1Ds3+n6l^muppwFs~2|A6vF!oO5q7u~{Q0$9cL+eKB&gpiK95VVMyIh7PsS'
    b'OF7!h~zD$!g*$tS4jqH9sFXIM+_3UUQw9h=&K84H@E7+^%p)#ar-'
    b'7cY7UW=g%3^*uyRU1mJ16@b}ZvVGtBP68%Q5T`q+E}YU102B^?RcQaxN!{|(-'
    b'nAyGUmR%9l@zf9?1UCznFt>g$xCK8!5%_a#ODA<O~=U^;2UnChxBXRP>WL_4z&gkH^(fgufQ>#}NV#iXp+f4zCnkyyBX4l1d>tUU'
    b')Yun1;!OQD9`D!5mnm`qFb*w9M7k~OI{ly;%yHa!A9?x8#+kBCy6>*5dPT)+-WE4qSP|b^@-0|E%;9VN1Q8eL}p0W(|4NG`Lie-'
    b'{3uO}Ct=ni1-'
    b'IXJai=oa_coK0PziAGi%uW!<r`8u}1<PlDC_X~p+8i{gJJGMe);k$W}&R=o09>JLx%R3JjY)~M2&Z?cfQm`XD(M=ZKy4?<Udgm_d'
    b'X`}tM9SKshZaCrU7E9>H`vP8hcP8SIy#hgs#n2@Wj^HVgMEcBQAQ{inN|Xc;#gtP|2op(BCX5N52phHW;<82^Bsq8b7`FT4{UMz('
    b'-X6Z>Ri5<8y1Gv={U4hNX*hPq9{R~UxWK5jXD{Z|$NP)QM&gx>b{93=AC54yF!Y=KZhwa}@cUWW4`9@8aE8~P4#}1E6DO8=hgJE@'
    b'$(psq{pSn*-'
    b'KOIaTsenzpg>sc@8|D5jdo(N)FZ)4#!mRRiUg$iJ6dIT45>KQWO{jVZr1a?^xoqYS`JTMN%5ge+Ha}9q9XxC#z&d=ssQ09MA!d*R'
    b'yBUX^qAN(#LKbn(cPr_(sT0cNcfJ4?h0cDMc(ee{(ja~Nigar*RnkA22)B3uzi_ZF)OY%{vxg}eo;SgRi~QkFYicbjLDuzK7jd%*'
    b'tV-Gd*-'
    b'~Q{QI)3>M2QaUg)a(_#^G9ejEM89EmnD)sx11a0GT`^l+x@^P3aO;BOU&@c~WmW{BqQls!a5kH1%L)a(yw^J(`;X+6<!pAtrbR80'
    b'3M!QEC#b64qhA3k3Nu=+mzj$Eb>SWbKc*NfqwS^s9DnkVN3txjI5Ot9kV^7P8$#zPl>q~ZR`k3^`LxvtN~EVtpib2}62h36h-'
    b'Y6#_-C&gtBL^?_=qR_REf?MyYXFeyEHHl88D3e#wD4~-{lK~L+5&@7vubOHf-LdvhbQ&)BF>TAQx0ON$2mH-h`Z=w1rNGIGl--'
    b'+47qdRsr;w2d8M6Zlk-'
    b'q~HX*WF{P9kmn<fo9xnO06oL_VEH&V8>>BO{SEPFflPhanwyt~vkhH%TECbf`ihPlAT(xmfpKIDRA_hp)~cjlml|d!c`GcC37U|N'
    b'2D0M<R2awnR_{(0?&Awz=Nd%0KyV;}cWj^bqA)A)K+-'
    b'O8BUM%FleGW3&T(A{mM4an{i$RT^ahF9$+7VvOrILMNCRdbPPrH&^v}<`>ilzOcp@ngh^h>x{`)AG&om-'
    b'B5pBM<RQix9eJ;Wmzn1{nT$|VM#!b#yTY<xH29yE2&G?WKU8`h7lGKs_wJP3OY}WPc)byu*3%Af{!e{yF*}aby)pFguuj$g%}|5i'
    b'T#{QG*g}Elgvn{kc*aN?so-76;Y-'
    b'|J?zcyi#u$J`azR)W3x)yD@l2vNeLj9Z1BMAppA3EbIGU>I>2{C&e7pH_C!hUJdDvKA0O;>)^uI>`kc?Xzu!f)s;WoV_q)=Gj!y_'
    b'Ix%;?*dEWd3LvA0NDO-aUKe!?%=pmq(^Y1@20`-u-'
    b'4M<}o%*f?+_t4X;^3c<(uZUMUt0ZXBQri%vCtfClAqeT5a7qc`j3AVGDMaFe;Ff(tw7N-f!)v(g_$eH!N{+*-'
    b')72ryKM69m>Ki=A7#;Yk?hO(FNS`$jRg=5$_^4trA8VYCb#n;poV}j0_Z}W#9Brk)kRu^RuC7alE@~EmmjaGxoUx8sCLX2bSP6qE'
    b'Dtus3OO=EsL=s+T0Yah;gu+S+;+&*HNfCuiM5t3VB}S?@_)T!_+|Bimr4oMqRlN70Y03)w>tasU<($l0%QJ63cty{()nC_<fFak{'
    b'Uk{tR0)2X{LUPN};)IsdvaY7(5vx1Zz#|uUvbp{mkAw!fY4a?vj(^|&j@P!ChxPt|wFipRv#R4I<ID}7%WXV#g=e(bU*wVK9=F$>'
    b'Bj?Lw;b$zgW1I<VNm7{bEp6aLbH%~JlFq|2gT6I_Y3B)JOa@Ms6|m633l0j`pB9<u9u!gAS)GnmN72tXGvrsGj`~Q7Stfh)?1L?='
    b'_RapPj>O{xxsKpjhr6rll$kc<{d=~d$~mcvhk)C+D?i%?$Y<7&nbFKcmv>&Hy_FXuK{!FLH~R-'
    b'IH#kq+WiGICe)3dt!o3#3>Ih3uz)iF!CdsfQFMKgZ5YtKl<EI?8bDEqicd-^#wji!_!L$v})@dtk)=HbS^5tcP`-'
    b'kHA&9*ej$NtfqAKQ);r*QsZwcD@${o{YG_J>uxKNK}NyNfZTE~M^GH5gZ)$T%;<f9%aFb#I%F-'
    b';QNe#?41)O*Y!6p^+G!VAtrYAwcBn3zzV(zAEMO8E2eWNwV_b>6;?b;EeSugPx~3yJ!>_+FETq1G@lRbH=3+KyEHa<CF3;G(Vdnj'
    b'(lH~p(<0kv4|=x_kX9S2#Pu!UXJ?s@h6ytpSYg2nC-'
    b'I<6#>&<9jw_%{7vv{+zJTph;h{oriX*>gaxdRKlz=l+zzJ36?K|`g5lqJYj^JL$FAmRTmAJM362SIy}xyT2SHkuhQsOok`CXlFn@'
    b'iU?$YioUh)mBYTe`YW>@!lUP*>x+-vvg(;<CA@3fqO<JxUume&rN-'
    b't3O|Id8%yjV2&=ZijE{!`w<dqpy{jtYw#~f^J1Y<|1xfjcRuBmC+CMX<--*6aS7?i_2t9XbK$lZ*3OCRZ--'
    b'#u7pr#OTV*1#%&HjQ_x|49nvb3>XZU{{TL6agO79)5iRSW;@JjUthTiNB~^uTnobV-'
    b'()6`d)t+MMlL&mpNp>V>MOd~3T;h;P))bBDEIAm;foEnC(@|$Is<g+n&H20b6T|C}Qb9H&q{N!KwMDtwcU%FxuH$;#eA>AO*P$G*'
    b'-_sPzz(ub<@Ui;;+|;M)*%H(Bm4F3)NLRbBxB2P|eR#!=@s11@nvE=URiL;n>EmwR^>Vj0Odhq~A1bpyt?~Qo;rC||LZ<@J{JJj<'
    b'DY)G)S89b{U-iDeYMy)&adf}erw%?s9pd^6Q&$E0yHnR?Uu?p^U&L>fxL-?#vgk>Xo$|;!8xskv-'
    b'_{Q)!qP1hb7(hcA6Sg#<hz4a9@-7^hvJ-'
    b'3+(iY)^=i8TuFIQ$phw`!x*TXRw64N=k)UayprAl=Sr@4=!ddNX2mud}(m^;Solr4o!VFOo^&8lcMuS%4hN*lZNI>ZzNU+~l+45f'
    b'|t;~98YaCiz&7!rG=0*i3jfg?jZ|o5GWy6+^A3GCz(Z(pT3F{*a2qnO}Sdw+W1tbsh$kOC9JJ}(gf>1_?hvCj$k#|-'
    b'fM_jdyoAWSXXo$|!Cp<||6;cVS!6nJrazRtdSyD~0KwMBlXc-gBoNKPU<1~c;^d!KNib*`UG|I5!!1;&GKh6k_de)keJ*-CL-'
    b'#%1lA6JJ6e@B1*uDRA|ZH5<HDDJ*38Bz-'
    b'J@_3X_peTSCIX>J!#HavReE3fMJW^`19zel3^U#FDA=iZ^A267aE{~26JAE=7>^r_Df1X{uayZHX6|)g4=Jjp@y31F1E^gsKL)*J'
    b'M_-'
    b'(s&x5qOW6RCn_B6E?ganv$rqDamqtCLlTKhfMv@UFq$XND^sc<|gYr!5W4P&ZfK)!FUsjz*{3X9&0R)Vdkh<4XJd?L!+GEshzg3I'
    b'dcXk5}+e;noH%{^~bnX6gt@Hr<&=k41Cs5Zdr?Q}A>~_vY6@?e%UzM|^~iI#{KGh$@rzG6lV5lv0CEsyOpa&`nh*2agFZE&mFWJf'
    b'DiH(L9cX>bGkn5=C><+XvPQ8XLoa)=tc}Kcmb-'
    b'@K}*Jd(~O4{}~WMjgZ1Ep3=Un*YE1nJ!t#sLaF%sy7|V1MaEpHv~EwNuYyb;syZw1_BQQ4-F*g|<-4-}Te00#m4+#Y-'
    b'|AJ5*`~YW{S8)Kt@6ez1GyYnIX46IkoV2QN)H^<UExx<eX90I*X8MMXFAuZ=~F!VfWGKKUn*OpB%-'
    b'pl(%zWpTXQ!1bnnW#4(o0D$0p$Ebhn>3;obMm3`~6Z6n^PkuPS6|-'
    b'Mj8Nd=Knlli<*8WB#JEfqzo6bJ<pPdS9)$hhu2$q4z(Ep2=Dj4et(sj_`kxp2X{elFEY-'
    b'*LU}~+cdx558Oh2Wq}~*Ii@S;7%BO9cdmmk$a!zSgX~l^l${%N>*u}+(A8kQ?Q{$Xv^V=oyVPf>v#(m6-'
    b'8{Vdl5mS<mEFx|J9L!)JYpLD8BN2w%*6|8>!y;%<COJOSfI<jdW3!J_poqu8G)LwD9^=ox)gS5NQ`#nbuEe7SM40K(Cs1T&!ZGY='
    b'cF7wN_AfzME2`+MqY!Rn{Lw%H{wbmJKd)<l2yHFQ|q~A>#3cav;(H5?{P~1ZBOD08indNVHCdMQJl){q7>0shkpUVQka5eE%1{J^'
    b'UJ-I80H9dkfUv&+7$X#1STI)Z!5}6JNHzpRQ7M7P2XDIUTMzkm@WSX=IcTIn&%IRcjXVMx9<-<(^@}I4_`@tzk}&~r2E!!X-'
    b'>Si=H3kFt$y~B?=}`{1+`LE6n#P0tv<cv#XL9mW*j&6*8Mj2hTJyxw!Aj>roA@y#+^3y4xBdj=6yEyoABA#d-'
    b'B=XJMh=o+jZC2+w|7h+jQ30oAuS$yYki8+xOMjdvMj*dvVp+uj;9_9?XfOR^OW8r&W($a?|99o2IVYl&6<-'
    b')Y`*go(mDP_(O|7wD?1dKeYHmi$ApZLyJGO_(O|7wD?2s-XH2Z3MU>>dvk_Q)I5C2D;m~dRDZ?v&Z_u-'
    b'o$^t*7FXby1Q)U7rrV~0lY|aSKOMVjqCN1S^mD$u@Kh(=xGJ~Yeek+igo%5t^279xafhsUvat$Em#G@pNpeb+YKa?Et8PjLu11Re'
    b'%nY}}GIE_aD-W*B1jRYJxh)P1?ti*mm31+y>1zMyo}F>T*O|A=iq6?dsu@km05_^YoEFh~A#yZ2CKGiM+-'
    b'T{ep~h<>4Pi_x8NJ4`&!Ob5$&r4APeLcFx)zgz9NfM<uE7gs?z5qsyAUK}HpR>X41r|nd30XJ9IR%Mc^IvuEK%l+Fe-'
    b'`!FC@)^5*LP2bZQq1)jPdfV-'
    b'L+(rm@$`^|3A~ktL@*5)yRq(Px*ifH{*=c?p+c0GuWc|A{aT<1^fjkqZ(Hy)dXI>wj`Yr%%i;Q!p5d#Dj_{&59}w{R})LSPQ9>OM'
    b'>LArO?y?!NsUzuqvfMIpfTjWVO<^T%c3dF2s+ERhfYvmG{`XwXcUaL1J_c@`0A_Iznl>!hZ4LkCT$>W6=_J)qh*pqM@?wKc1Ii)3'
    b'5$KI{&N9ZZ$|8+uXQMed*Mz7&+ZFFu_1)v>zzS_^!Z3DZj9)A78=aD<IlcRg$TAq(1p&l`$=RRR&1DbUK8monKX5t?6Q9(hD_n-J'
    b'N<=mmT$0sH%bbGKKnT3YfxcyiI+@a|57vxh{P*smOXObDBa6?OYSx2~AZt>rgLEylJ|Dr1pU9Ij`C#cYfU@7tVN(lIzCWnfV60{<'
    b'PhDEcAD`zn%FGzpm}M(l;*DaAS2>_8rjE{_Co#kGL<0W(U-<`BDaRK@}g05{U%|eYdLg$9GsRv6d<=1#XV3>JtUUm31&ib$^d2I-'
    b'b-1>l%q-OkA9^0t(_;HO*A1oK-'
    b'7lOoGuPB_2U(m9!E$fCkW12pX+oR{KPyjFJeO9cVyL6~$t0l4+Nv;M5TA7%@SZ$g<C4l}N_NG*>D2d%B)(4e>u?uhcTZI}M5qtHL'
    b'DB169H>7p%xsc|tw)hHK$iBo0(a=7K4vh>zKes6h7zSLlj|Pxl0SR`czF#ItiY!3@*jRkVrFL~U|X1QSKp(KxBGQdfu$?gW>K1fx'
    b'lF6UrJ!&pF?xUA;Wvqr)p^+)|lIAS7E#bq4bAU~_0DtPfxcN**jzk|($g237DtTa17$C_K<ta6CP7#>b>uHQkz7#S_g@fMH<a|56'
    b'L$f!2daCMmouG#Cjq<q$O%h2}vKFl1d|Kr7~%r+d)P%X57?u+mNyK~RndqJWWRWp>&!?}^J!8L*55Ra^&w6>gN`nG)t1&B9S6C1+'
    b')L+(Zx5Kuyua*kC~*@Mu)vLSZd!1|1+^K3ncd_DNH(i&9(~JOT%#K{d(X9|-'
    b'2{Gf#2T!^@M~9ZWH;Q7N2JN0c>=&<KPn2#kj~^a)^q9tfBdXAO`qrNptEq;)i!Y_%|tlo%(vvYJ@K1kc1;7oB2^XidR<SJ5*TqA('
    b'$=2v)C+RuV30k|61rm3ZHPUlsLpPi&`;m#4NrpmK778iP;4B&^Y`gABofqyRe|#Ix4P8moy1ZcQ*U#SAbk2w^H=8oVsGUmr8MCq_'
    b'jxztKetzMIm{gHuF2{3UDd9B2mREjoQs$&dvzEWqSS37o@K@(Bn4gqeEg`R#Y}@)Vy8t2||mC4t9OW#BBSKz#%bv+HyK6%!NF!7!'
    b'i~m6KBxep5Lzs;m;gxSn|E6dK93&AlEo<l$qh<icmL!48MgQm>4bPTA_?Y6Jh4)_!Bbqv3|uK3e&8jndU_vny8WBV|`rytfTDRaV'
    b'`)wCdK`ZMOG^qSU#&a|JEn)PE|rd+M9t73H*>07?DE?dNaDB4$`cGSF^2HQ74uff;cRY~db!q3WtEF?3ZF{Jts<6Dq5mj=%s)nDb'
    b'b@woNKari~vH#@RI%$No|rQiE(%Hq;h@!$-'
    b'ku+NIdmn7ZD5y=`l*lyT;()`%`k>s6&!MojC3hcn|^{Y2HOsykW^tW%$S1x5@ybmbhZ%B{r0m&1zWB`x6kIuNkaRTS&0re!s}vdI'
    b'?Ku=(#^`Siy8El!ZY`lo|(cu)UCed;`}8=C9zNO@{;XP$AbiYYCl(6OxC2+ASd-'
    b'W7*}eb+qNi%qxN8_ipVo9vE7Kf9u}T=LS1Mq?IeJ?*}=QRAnsdq4OK(^=G%UxBFE!_2O_b9!1aZYU41s$jv+#j>nmS$gh#K{D%>3'
    b'Hq)(%JbfGmRn_I2;q0Ip6zh!Hws3-s+hhPxwx=s-'
    b'I@D!R;|%azng`tM*RH;$&$5{1aKfIBNj9)7se*8q_r_PgQd%z3OX{Ibx>f%(FCri0b|pH(q%JO_e`<q=Urel0LlV-b*-'
    b'spsETrnVR0oQRzyt7a-'
    b')d!K{;4dFie>Q^UeqgQ*OKhKMPC`BEZg5P9}jR<_Are<Uc4ChJlZ(E=!baU8=3BfoETZVau}^bJA8SETne&H^)`EEOFIwpSSh86a'
    b'ms>CqmlrMzJ=>)jprBTHjhJEEBkN^3<DTqJQ?xstR^=RTPrMGZi;eB|IA&=_k&oWKHot79K6n{Y<-'
    b'!+nxtb)?k~$zIffa>X)AUy1Dzj*)=;Wm1%$MP9O08&E~F@!Vl^yI2~?tc%$8{foEmxAHAKzN7}uC?tXUL@??c>e?fYEI=Gwl9lnR'
    b'>l$QiJ-QBXRd(*+D(Z=1wLq_UPZ_|_dhIPanyKr51)q`{O%ZqmK=h{OF;1t0P*|-?+HHS|!!qgQdSA_i+A>SAO{2ye^!hvW-Im<Z'
    b'<B3YJ<(Wtn~nMoByq7;O94vZ^mMaGaJ^_kirywOIBj75Aw5425owM#XSy6CRtS`mfEjS#~v5uA9Is8P<Ps4yt#T~3?^!7b$p)Eb7'
    b'=j4^~NN=OWacREmyf;z=GkKj*xVnhhiFrU2(PNmF6lJH4tt#Txi9Hb3e6DIIHx~!p1)@gHEFIM=6a`~E3bv5J+PvM~r_evEv<vE*'
    b'yCre$S_o+0VE2Xk98iU)O`;;6Z32Xpqg$fcTF;EqA0%L(W7P5rzbsO!i*|27)!dR|NN$JE~wk$`QePkg7?o3D`fRgvj;l8h+fg0('
    b'hWFp0+gXNNt)_fa;TbiL{!##l&%v3WKtTKs9Mubu}d-$&l+A4-'
    b'kLNBzzI9rBan8h<A1=Z7ED92S)gdUyg>!_&7o@SbeQ6h1mKqE2ON6}6poB;X3|C!0gi40at=0-'
    b'?Eyweh<MGfr8dd^mz<HKAAiM6Vv?W)wYJv-'
    b'vED(-3SM*3cT!oAn3w(N<rCgMV!U@S{Z*Kv<W`E>4|)!L=*g?nYe=Kj&}-#53f%G(30ZS-*PXE{W@-*VNL-mDIKQsR~W8_x%Dcc0'
    b'hC0QP;`BV%YZ)RJT+j3{Rxl8pjnqB3CZYQm+JNm8OhGSma7IU_h1MBsr4l&U(q1naZj`y!nr7Y9Efg_P^neWD-'
    b'&?&kf#n_c@NckPYAC<D;qJ&3g%x7*}&ygPZkdSLk4{^q7Q=cb+xE2MM`IGpoLq_7MofSVMuqEd6h!M;a@pta&w3yHuZl6AHqfk=p'
    b'iciOC$rkMV#>f+$@-'
    b'2&%rAG8nN$fRj9T*3p0Kp|0pbitL0paX~#&dbDw&B7&PK)v|Li2>dgh7B7oJ5mXQF%sz&ChtE!O5B)nQ=C9h&wA^>*<`eKMG1QoR'
    b'Eh|qp+N?(oJk-oW6Ta{Tstq&b&E^_`GI8Pj^Kt^sh|pbq7rB2--aEio&nX<;mG>g>gwq`729`aI?9k#K;RW<XX-'
    b'MZ17?^N6u5y0B7|_(8f~=&lFxWJC{Mysfr=m{(r<Q1az{|`SMB|4M;QZFcY;OS+R<7{nHfwJus-gwfzAPWZ*>eFi~v~E#0_O&j`&'
    b'>cvlTW`;SOT@RHeq63xna#(9x&NG3;@vjhmAcE6G!SxxRc=3!nb?5iGsll!rIs<M{V0{QH^bdh)e>p}uh@Vl^&;R>dKpgQH_dRmv'
    b'Hq^YyR?D+L4>X4fGE_YvAhkoD*E50rk3@_9w&Lr+zYd*Yu(B`qpxQAvwRdWcHe#2JccsAhT^smCbu;+KqGieL6QeMT7bS#;7wD$e'
    b'(R8xOb@h_UXa<~Y0d;?HgCP3#T2d*l95g@-'
    b'ZeygGsXSX67rTdf!`BH(2aPgULf>~^1uv!(F7o$q;dbzkh|hr|B<2y;wH@u#|Xd%r#+JOKf^s=gZ27Cv9beocMpcDw&}QyjqZef3'
    b'y*Vl~R+P3P)Ox+&A-i{61c1TUQ$ChEI~PpR|p9=-+RyuH6$-|c@%I8e^CGTqzz`@8Oa(7dd?eS5#f5aZwP@wnNh&D;Cq=gud-'
    b'!qT;41oiUI*RwQAnmrDpeDuEvZKHe-woQ7^&k#<%#!5kSF&X%&bltSSQ1&ZRb~E!8o(Hqy?r~$FK%U%f${=<7SaBHGG@-'
    b'H%p^hGf)-Vq@48d!dQ35KMWM+dT4sn1yQBJ`w2sR?ZQ7{^XR>Xtx6~G|lIyvv@<QFFUMqmxj_N{9-'
    b';^~Rqqs2NIgX6~k9U2BTmA2D(k14RQUa|M&%+PY%6(qv?MA55GpNIU}e7Afd#fSS2FA%oshj16>ekJDanLcMW{9eZyI^|1ZubAy^'
    b'VLi%wnyuNoO;y;v2l`)Q8*wlSPX3G1@1^}-'
    b'%3>5X=JYvtL%KBvUU&lpAsnYs4BX?RQqdT!cV2r>EJ2`%N)ku~t_ASUqO?*P1%n7QOQ$kINQ~53+OeHJ<(y{J8|tmcQ$q=Osyrm_'
    b'10~WDM7~53MV2HGsa#SrnHa#-'
    b'A`%8&oWI!L=^LIDIyymL=*xP$1%7&c``I1S=|*zn)HOLD7xvq``|NXl&}LJ)zz1)N^E>A_rgNsR0fs-'
    b'tNgdtWTNJ}9DTcx9Piuy5ndydUqe;>+&b=T~%Ali)T10NV;xb7tLHI})JPCL-IQ(Pb63;<d#eI~54BG9=v+4w5xO^Qlr8ZkjfcGQ'
    b'Mm{bQgA~PN&X^2E?&3pux3yi`PFh`9N=W{YysR%QeUp*31&gQDnF4dm!s)=3<f+80q9lf|nSz6)>B<wHS{iiDz-'
    b'R)gETndd)I~5wK8d!fyJD~DVsJ}yod7ODLXw{JpV8cJ{r!YdxHn*u9MJ{4X<$#N8gEgz4?>{;IOuN3t<kt@mC;?HGgCr5m5X&Ti2'
    b'1-'
    b'W4|EUPpaL~<|w`o{N(FsC=j7*_kk}&}%xClfjJk^?T+iA1x>0m93!)B`|u01rKGic7BL2+}8+iK9*0w`V^NmI~*E2CY^LB!;<A)t'
    b'&UbD0|8hKNIs=}X$~Z*Pi<4>QUC#@*gx2P^(>S2aBC=d|fcYvGu0ifrPEo}3y`B0lYBtnoo_x~grcPMZw3^7%4RvaC4yaIM-sV7N'
    b'Zy_avjB;>`-RysDn-3Y3-'
    b'qwyHR}N;l|<m^nhDCuL57!dHzr`2K%pC)bP~M2r~Ls#sG6DFc0!x0?d%_ckG==i#@%4t{hFB>2~XiaxSuFN_K;x&y2c%J|D$!Gd1'
    b'u)=UIw<#?7MH;#^HcNLx!(cf)%CZ2x?MvW?4FSGHK2$qBPF69ucBVa^k@b#$7nLFlqiiQ|ae?jvYl2U?E(5+$|jN0u+1+8=#m|#&'
    b'T>m-Z{fumXH3@#{q+Oy)vx$GHyC{kmI*E;!>UDg7VFGk(eXUNxhbfU&1VW?x`{4DrXL+_cEl-UGRLahwZ3rZ8yL`%#}r#|o~m^PW'
    b'wtddhkfVGlE@*HL$&IX?{m>|cw6wG^|Hp>XslaSy=c<}q3gnLm+B8|+-'
    b'XGTI!iDlwF;U;IV2bywB=CA6BT9wSTLJ73G`hQj>i>=VN?j~Gf`ba1Hwk*xmQ>W*&V^58i6$Wbke#u7HQ!2BnY*2Y>XqDVye0QFK'
    b'{<JO3VI9Wr|2CypN7ULGy)rG=&&t=Izx(h)yH2MS2%*KkeOGKw#ZAXv40~8R=>FaQFuD=2egF#Pf${VCVai|6Y^vzC<g+)Ba`SBc'
    b'd1iy@QT=*hbE)dno6Vt_-M^n_MCuEJY0f@ox#L-'
    b'FkG9*F>S;g2hAXoQFI|<F#to{9rrOYG9dE5F++0=qr+wgTJL4}`LhHOm=ZMtON~cszA`zJ=hUP(2XU)Agpsu9^Ll2BG9X!@u;*?_'
    b'@sbm-pRLG%4H|#`tbI=J~`!esjzo^|!q$>ZkoZc3!p`Z3MY<SS=a^(hF0WY+RQnJAkG=JToc{S~qHu?L8TT6aV{BzRsIMY;S=MXj'
    b'8een_7K;s|jKq9Iwwdy<dv^0T$6Nf4iaG62?3!hLK8Do)VXH%x=V9A`6$+XxkHJmf$!1>Zqg2xqrZGz<X;=bRgEO~nyf3x@Vo;3h'
    b'DoSiZE@Huw%&g?7o9(;b_!C3nj;RK_bT_C8z4^AF@V2r;LDyUb=S_cll_Zi$}6=M#O8%3pwTJyxMW+`}ZltF&a+w4jl<UVoH13Q2'
    b'c;55U(Rv@s@1uwu;mKmBSiX^Qqy6IBs#NnOjjq~EwH@iy8siV`C>pZpFb;c#`yUry`mnF*21fPGRa?)+Cq(WJh`Zc`ex08fYJ-'
    b'@rh+Qo(LuZ_H^f|Es^|KE0^M`f0L8wj#;{8#ne;Y;m-'
    b'Qk~>%SWnBj4Vgq6F=QEpC!7V1xdouG9OaHnq5|<MTd?7@vl+yK79R9l9JE{Zqq8Pgb)VXYu7yZh${>XS?FYnUsP`ZYNF*soZKz;Y'
    b'@&wbvEQk;7gx5Cuz(l4|C!;&qyGj_3L`TM@unb(q9Epg+fzg^!A*XDElhVRMm;nF9T}L!qx$~BLjfGZ0j!Bq^;K$Ki)fgX`64QU{'
    b'fsibA*3ko}K~#Q27Yd3e0*%*ott;-uS4hX{8%@t)LiUWN3&i)L)>7l%SJQfnA-'
    b'(=?NPDGt0&R9!!(wZ@b;H@ye#V>cQC;W8$rw)F#5|sn?Q2T11rye0PlE=z2X?G*1~(}pFssa&aGgVtlv*c2ypR+m)^`P!K_U%l;$'
    b'w44*)@28tC8{ap<E-'
    b'MD6EAeDB6zgF2NfHvqxve3|JvKSeljB31oz)ky*s)!ELZqxXR9D5~R0Sf0=7WwZHVCjx~aRpPKXL@TE4*5+oqYoO=+IRIvnRp|L?'
    b'RFdZ56FDfk3Z9xBO8B+p#k)i1Xwp7FfGtWj_?-'
    b'*>&{Nc^QY;#mtumDAL*#z*|ZDQ7u<cJS4g8T$Sjb|`pb#T;!a`#agP$JAn4>qFnqhEXkpx~rq-Q~R7@3*HV$UrbX>1U$-'
    b'9_Qel8sRX$jK#ZuzjxaP+}^Phzya`J;cG)IW88=oofS4|gnK!lF))HbIRzEGmY^KH1|vBMG{-'
    b'?Z7nNnEztZdHXPnO7{n@>pxj9#9uG0^7S1KLW?J-'
    b'#$cgQFo18$poWn!{eJ~uk>IDqfKSzweTAY#s#1dmyfD5LN$!E8j}1Saf6`zM5r;E?8ar{?8#GL#cZOwNv@$dZx)p$9`Wh%pV6Yyz'
    b'WT+Y(B-0)l5eF`+ru`PBxNZlVK^rSr*t&fP7YqxMex-&PCLr~N$Mx$aC|9bu`ibzSP-QFOSURoPBs$flp0*G}Te&0J3glB+i-'
    b'Ev51hvGSqO3?N0kR7x491z55qGA=!n5nLpP#0yrE;}k4Rox!!Y()j>ZuvRu_o+Ief@#cG+-MKN|`|g`FNT)m-'
    b'?=%6Y*V+YBw0`#f4ou0^HFTQD9-2mLtXer@AN9h2%__}^WPs=d9UM8O4jfGf<_2Y+YRNf^hEn1=CR-'
    b'^bE!yx*IS!_4&H~&Fuu=;DWkw`JJJ4~8;ck5j7@$a?A#KWB!xvq!97F<vR-'
    b'L6zgQXCK@d5lJO^NhEzJ3C8jjX#A!x)cE^x_vi%L<%uEL+(ea&w^$qnSRudSG3?Di+|)L^pnyQHr)!_*A4~;N6b^9j5$y@aav)b1'
    b'w*<A!n^oAqOGwv;-v*o*MvGtpdN5avptf7HkYKt6-'
    b'Qy5u@U`f8Xix1AY9{Hy`NdlS_WSoc8lOhu{2q{(S(kXu&BhG9ENBQiAFOo7aPc3|NOEI%=GD9Q0u}(IkRrXhcw>#ONr^rA?8}3=d'
    b's}7x(fz6WsCZ5!cZ|2uAkx$2@-'
    b'ew4Xt{12lMVj;8(ok@pMP{NlZQpvylooT1zQ^8Wr~9R1TcP~js_At0);?$4O4{T7C=jXv8mp}@_|DO2D^nz;iWjhdz8oCm>}1Tjg'
    b'&*qv|;q^Sfa$hb&(HYQ{Y>$u!+_QX{0iogkTeLONT&e@zw!DaLWoI)45D1sbDa2ln9L4Z~>$$30)G&+{CIxJXg;7Z#B>fJ^8sJ+E'
    b'ALgs0EijSDADc@!WrSzSf=7mchjR{~6fMK9LOWcEX9T|AxN`QhOU?_MVB33&xGULf<kvYYvPY9z?MoWFpqv?$Ijd?ZX5nj!hKInN'
    b'iQ*1dA&5}?188&<}<!3@!=VDl3T*VNy3o0}ClZ|E;gN9UFjYc!@B*VgRiQ*|=#6>V3oORw1qMRsVSd+o4PVX)TuwE>3^}4>=Saf|'
    b'=9Rn3hQ1^(<&~@WxyJ!Q)?j)K}N`|2y_rD8H`p@>cpXjBciCtc8@NmDU;)%=t^ORTjZg*rK7J_`K;NW~e?-'
    b'B9CS)slWZTK!LI9`ZIKEc9xib?pwG3&Dt*4Nd0m9AL*!2VcgE%lUDU&D>-sxgIDA+i=-'
    b'w&=1&m%TS#b^)8T=(OLZPAhx$ThU@&1$9P&H8i>CutkS0I&9HlvvnBmIUVkIixOKLv)5H=H3{~$TBkD9rOFZ0fDz0U`xWa(Tr8*X'
    b'QdJTjQ~T^!td!8q)7vSQ@SI(G=6VT_?b-'
    b'{MOenhbW(y|F?A^1LOSn*{pb&A7sZr2<aaMhTpfQo2MInUeQj=t&PfCDosiooyF*71jM3QTvf(=&d=+VZMU}-'
    b'BKPbyAf2ap1vP?_LiDdd;)s0CNv2?FM%Q4#m{!R)d`D~&~!bf6)5@D@}uL1#x&GzzU$!dMV0Ny08chK6H)dl}Tlc3wy6j3h{3yjR'
    b'V4Cjr?|aJ5oQG6$t~2AUxxgP)~feogWod=~DQ$$<!%RZFQCR8kVN2xS6tx7}0v9ZBx4*ZgtSBx}AHX5>GzxnjkiJ1hL8w(2wFvkj'
    b'W=<}`Fnsk**u0H>K60d5O0s_-mpm${@O!@^qd&^Tc-fzv{Qm5L|_UX5^xN#%qAUt6Aj@M*<A>wa~?7AGt&nRM1DZlnWBGa$$;Q6y'
    b'vPr=}Ks5ko*^MUZshg@Th}y|Ky=Nv)4~F!E{B6SGv8A~nW%$(-'
    b';Je7(e}#dC+Vb3}2XXlBU(Hz;s^0|TKFd}0MMj55u&0Z;JsgU?nXbpqL*wH1tIs}&<j_@u3+p5cjJM1xmKh0objp@k3GX_Ad1!o='
    b'ttW7KHl<{{gy%Pg{>n4mEj?i0_TB`gK65QqtcM1W2RM;ORtONC61fxMuR0G)ZzG|%RA;N+|-'
    b'+PMT<pY$kteh0`5JcH~W3<B^R(ZH|#h7rf3sNX$N<<;S0H?1_@#|5XO6<XbDJyH-K!Qu8m-'
    b'NJ*Y%{(U;Kr(};ZG4DaM9d~2gcBK<gr!v3PzBVVyshG1b-'
    b'O2SXzgEybRD>~M9Ao*XTe~t5#yjCiJ9C^=qw^h$*Vv!P!<hfPXJGVS_q&3L<r)v^4oKUwjS;-!Fp|u-'
    b'L#LV{WL8O=CG54Ros8BDB^R5T^<>te7=<OL6&nmv>tif05k3ir=z|3@W4s)?)ikE8DOt5<`}UkekTcCwe8&rMGeF-'
    b'e0>Gdu&TZN5xV)Y5yt3l4J7fjjO~fy`(34TI!_e-4*ptE0Jwddn+J*J``s_Q{ny<(Z_*a18U#t_JL|H&-'
    b'_Jq4Z$wbn_4dbiB$};=aih9=`Nb+IjkSNVf>Qsb+2u;B*Sf5WW#aDkhcYntxEXq<NBrI(EcI~wyy=wiR#B$RJhw)N2u8WoVCRRd!'
    b'Gr~C#}UWDGhkq(8yjrGx`B?GgeU6>K`9$FTPZ<Whf%sRwSDXg`g2`&t^fMmdepStU~1nkrR&H}P$`Hp=5eU@eu^r)+oB}jA#De$C'
    b'TALx!n$#adJXCW*igWFG8Mr&Q6yTHTr^;rlOXV%8h8kESR8dx!32KjG}<XvO|R;!*F35yk`l^0aQVSROau?SVTN1g3^))Vl_=35B'
    b'zUqEWJZt{I|TyFdREl@Zojbq+C2>%<c45QgB3$0v;eEhLAGgdqq36}T@po|HsD-=e55i21<r-'
    b'{23)@o<*?!T>rubfcRZWM<~J0W8_}HY+&wn-'
    b'Fk)Md&}bzadiKbP<y3X=NvMgcjsA;eWwDO$nFG-*gTD~*Bx%JpDe8R~0ag!pROBFlQ-kBmdCD`BI;G&WG8~+0*|b=GvTKM`pRZVA'
    b'v>T7Ma4;hMyBDhj+&oJxNK8Q}=gK$*8eWh@C1D`~i(+PmOA!oI461<7?|t;(@pEQPVQoD|tkPE$tF0RbuFl>4p)XqLsA%;BWKa(1'
    b'XJuh>RzxLAF!N94jOQ0()DzwA7&PH7QUii9N37NovgemYs{s8KKzD(M?}AKG5fIiw_yqD$SxFO+Ops1Gg8n?E(ppC(br#%yYXzGW'
    b'tsskyW14}x2&_jq_ZgTD+(JRKVL8XbG2!5I(2y)1;s7LQVubs|QBM}p`j$kiVM=+A4uF?ggrIH0Xl>xcD;<D9@N_xu;gRGOBgAtR'
    b'K}lP#GvT?Y=QJf+dl7(wEf(?m{Nhz{mX&2R%a~oXN_Z|<3`&3($H2h~91rjdpbRAn0QikqiX{nj;!*lXidXjfR%;KlR0~%&CR~{U'
    b'Pt!}~Y2i1bFUbiylFVg7g@fNB4*^pJF`i{8PX>+K0G21EkzE$9C^>};PKto1GQwXeG{_Tyzkzv5DC5jTiQ#X~Q&3FD1gvDDgV`54'
    b'O$%2rYzYCIMS1Wqobj-lvaEduB032ziIB=*-'
    b'8z*NXbFmrx(5!00a&dT;rf<@E9hBR{}5rpxQH5_0oO7c4tkz3iG@Zj%RE?&(P+uF3V3d@<_uM8<l?g3+Azg4i`EuHR3*cY$(|siW'
    b'8ec@7)&4>G)IieB>`%LVBJ>1j3kk1X|QlSj89ulVdw_9C0S=aocYL55><Kb9dXeJpvg9#K^*nlJ{2|KZ&+Y;u;2{1Cdz^_hsLaPI'
    b'RS@i@M}q+0ZUm^@LMQj1~iI`5`+N*H<nL-VqEZ80g?>KCea{02y~)@3>YZ`wUw+?j$}=<VjN67Fz~46psNg)Qo!PuXNJ@hLtdby3'
    b'}A~3l@++*U=Yw?vtyQ95;#_2gw+LeQaLOUD6QiN$TiAp(2L>xXPzpQCYqk#?AOg9)s$ZmR$n~zzcAoxESjGb=+&%ch*(NI5(&yyD'
    b'kTI989Y!B*uWG@I~#ohHx!I(l7S8o5+Wwruf)n}*GA)by;q+!^0BFXtl;dwK9ryRyJy7c3!~%fU7_{odw6r*3H*a`@%`Q5KF!{qY'
    b'6>GhYbnW2v#(k~vVa7w2YZ{$J?&@EZY$S{t0$*uyk;>dp<%Ifa4Mw$j*X96D`wH)GFE|soCQZbf=1jL9*W1j3?UJ#Y&68Nd=c3-'
    b'qn752SA}Zuj1_Vn-nsp}?i97Gu0JYiqk8wnayQ1>pPRzbe|L5!NA=p6!J`qMmcY1|%t`RE5UY@E1nz|~aV8_UieL?R3s!qb++?DG'
    b'VgzVUhxNtmXzPuoGqU?SX6~G}@C<fNQz3b1;8<{$z*_Nw2oWU<ni^1I1Qv=rkSG{}rC_*fk-Y~C$D2e%h>-'
    b'%5xWKX=X?xtV0SgM&-w+@Wl9Z$g=g~+{yz*E+2L7W-'
    b'(8S@cA>~|ZhUJyO*hma$%#VGjYtpC;Oza)9w8A*Qh+sAe%_LY%F0y12nC22b=?n-'
    b'IBc#rnYZ|f6wFM_~qWz~kSp7Di+0Uw)e|*kJzk&0qBmHO3VkN3ahyK#ju?@Y3XQCQ<?>q(1@G`}gABP7Wt6n@>u{J6pag#*F6avE'
    b'RP-=mO1?FQ8d{x{sqYU{1+*U3)tOG^@l>n{~g3iPBWs<=;Fg^?6m@(j2FhwQkQ*L-'
    b'NxTqn4=mf1z5PSfV6g0DvgvY=%@!{2zjylkdRbeK61a*tj^YGDy;>hS#f%8~7tZvi;q0C2@^gt<J1gV|fMoc>(F+805;V6`kePg>'
    b'xPpn#8a3~87<t^e+mblXrcUt03OWf%<8FyM@N=r;>i772Hr6s1c#FUnp(h^fzVoJZSn9}|>mFwZQoyD0hW^*PYG!;4O@LbsM@^%v'
    b'*7Cow8nhGB^jV=MCC4jUfGA)TrOCr;f$g}`Lmqex|k!eX}S`wKS(YhouE#h@aWLgrLmPDo{k!eX}S^y;rpkx7*yazzZbtkgDph*@'
    b'q$$}<X&?F0*WI>ZGXp#j@vY<&8G|6uYO)`cOIYE@P_UCr9OYT#89FQa&_Q&J8YGT2UEclTHKeFIQ7W~M9A6eq?3w~t5k1Y6+1wXQ'
    b'g)&)PZh}Q)_vfxJ+{K$eIS@0tZeq_OqEclV7AjugB$#wrM(gi}YKu8t{$pRr+AS4TfWPy+@5RwH#vOq{)2tslS3mHL<l*Z<Q8(DB'
    b'83vOh=jV!p41vj$9-xu7-vaz|~Mi$)2f*V<IBMWY1!Hq1qkp(xh2-'
    b'gKSvfxG*+{l6(S#TrEK{g9+<gvIB^29$2Ze+oYEVz*cH?rVH7Tm~!8(DB8FM=ECgF;SFBaIS0r2FH;KqI^TU8A!<4mEat1oOIRH!'
    b'cX01wpbPNEQUif*@HCBugZIL69s6k_ADsAV?O`x*$jv@wy;L76i$HAXyM33xZ@pkSqw21wpbPNEQUiQh8*lJo17Fk_&Fq0wGx-Bn'
    b'yOOfsiZ^k_AHYyN8er5F#fCl1kk?4}PRpYYTd0L60oxkp(@nphp(;$P$HL&?5_aWI>NC=#fRVF6fa(ye{aG1wFE$M;7$Rf*x7WBM'
    b'W+DL60oxkp(@nphp(;$a|<i@(j+>G<f83sF8E7(}EgVP$LU!WI>HAsF4LV@-'
    b'Wm$4;6BP8R@Xt^Wa9tn0i5uEXa`sIkF%}7Ual+99bgp3vy&Zjx5NL1v#>a)&)7Th}Q)<vLHtm<j8^?S&$<Oa%4e{EXa`sIkF%}7U'
    b'al+99d4TS;~$q0Fnhj@)!WgC0)J1M;7?V0w0+NA2|VtoIprQgQq^%<{|izu;1nFCft2Ix|_5v&8e{6AMX$F|LWd?8(DB83vOh=jV'
    b'!p41vj$9-xu7-'
    b'f*V<IBMWY15v>buWD&0mZe+oYEVz*cH?rVH7Tm~!8(DB83vOh=jl48&ggo)jf*V<IBMWY1!Hq1qk)`m+f*e_pBfnkbNFNt+0vq{y'
    b'*zZ2oQvR^tJ{CGsvDbdPU`7_q$buPJFe3|QWWkIqvG)ZtvS3CQ%*cWnSw!oC8Ck^Zf*DybBMW9^!Hg`Jkp(ldU`7_q$buPJFe6K?'
    b'kp(ldU`7_q$buPJFe9&y8ELfjf)ZI!BEM&p$SDk@j}&oRv@!9!U0N);Xowg2-'
    b'vy2RXZzewbP_*ue>k8r>juJZ+}&aGkIrMi2N=l<I{_~NPk8_?Wx^usP}PK0Hg1lA31%`zbqP3|(ORPdm^0w`3$6sHTLDTvE3m6Uy'
    b'GF2REO;qIMi_!n#HctPyYBSnfnn^^H-|1*X{_Mmh(GDQP#ZGcSAOn?hTDOg01E;uqdiO9dkR7aoGm55iy*L4o`>jxR*lTmQy-aAj'
    b'Dl?^tyD%!JsxsC1y1(E&z(0;#yhQ<$~)6;CqcJ!e}4y`N+@>Su{@sYr5&di^ig2iV(QJ$x*66}bo1l1=!B(Ib#6a9BHX+%3<|d`O'
    b'>422*LIZ(S^dENxGGi08BKRajZNvha>$FSTU6bm>fXJo>qzEB#VsoC{HEu-'
    b')^A<4bwRZ?6uM})MY}E9ZP9Lz(r(=^E(&h(;a*S2)il^sb7ep??18=iad)+IH|com!dP}2VN*)2TJHjYkkg^y{F}`YdKf;RS7z|t'
    b'<K5vtoY{8Q$Ud9h?fu=l>SYI!!c=57f>;NMU<q|vdC%Y%<qb8$SS?jFf(V){w}uPFOpMxa7PX*`pR`=9Nq0`_6|6D?PdkyAqJ|sk'
    b'8Dl1^Bopqvd#-^^Q;<gG3>^}hFqV}uIU6e&bGXk&C{cN&?V9L|2^O^6Qm7ufR@$hPl@!i+8dw%0C*l%M!g(gSq>@-'
    b'Cw9=p{FdatdoC8rTsfd_vJ@UO73_IvdyT8$}W)&2#+HR(=VCx$Y7Ta|>*GHGr8bnM*Ki!?jAVSDe1x5^EHY6973NcBP=hnjNMQyo'
    b'qlv2ltqf7)1id#CLh>!llcRJe^#bZ~+V^{4HS6|q5Qn>vTY)~o%P%F`q1hWT5LrPN8<h+-'
    b'JC#zv1lkkR1XQJm$c`iUb#|wRU`1Vn^tJqqnzt>;h2!sPQ!g2EnAqUVq7yz(%XSVBWC$DY3p#4|QRAb+@yH;LG0W2c}*f>rlOM|1'
    b'?aIjT5Zeh6$YA|Jzj01McAUOoEI88w5_>`IcM6Ykf6V(LQPaq{|Mh$g9a8za!O%%$+z&N8|j6@=YaM>B40jr`<UKt;OD6@jjW^0*'
    b'J)1QAh5sde;TK^%&1))IP*#O+1yp7VNm>KkwQ4NBMd1YbRB7@#Xhr4@L6AM<nWt{UQMY@D>88Up)sirUG>K9~Ey}E8*T{qgjd=-'
    b'reOoRrNcG#pU<8*UCb2HFNCGYOH+wTTf*9W)z<@DAFfaA;~#n{UGU5>>b-'
    b'ye#;SF4x);qc{w@*1Q`775|~oF6pk>JgS5mXFy#9!@v5cZD<dt(^19OsOyigOLwzcE&uo)9F|5emfm^Foxp>eSmsm5Gr_kyZzR7V'
    b'n~bqrn*E`-'
    b'nsjB3o>KIoSeFQEfb(DDH}QgT0hx_?zTI}@hq}W1{7SNH*xeK9gj6cGi*_0=1pa;R?F~Vg3_tDK<6J4_&gwoz?p@SfKuWXeE6&l('
    b'?)8{|G=y+23``4-V(5tQb-n)?nDL&VeN-'
    b'=T!L7o%3$y0dkoT0MtKN$<`HaE<#v=))n_5~iY)ZOaxFQ`6!_N3`T+I`4}mi6jinm&fyg=|hT3DATOa~FQ9=aBQE<P#E8Ole20TG'
    b'Rfx2QYXiz5#z7(=1AhVqX|2D8hvj#P2U4)M@Fg~)gU~?pD3{y68bd5ipW9LVKluo!GsKUjY%^e!*<x1A;H^KTJ5WMB3&j<^P9CS9'
    b'Ab0R6?P4+5-*KUMJ;L(HmWHgP03Lr_BB+w(!s}vu`1xGP?1z;Hlk*_-'
    b'3|3JKR#gH}NxzCXO*%*~B;6qrOIgy$&7rB=imYr&y3H(^eR0a~TNfViw;>IRt1O@36V>DVAGb&xCG2Ua6<=4}VkK^l3tYD0{^=tC'
    b'>Genj~d3#pK=;7Qt884Yu)BCTxN{F6U(jSy`m;(onP9iyi!^}bAB^fm3k}D8+NrNd2EGYtJ5n6)z$lxVp9uOsJrZ}}5?c5xpi<`F'
    b'Jvsw0XBLlvSAapD@3G8ujlnFw-'
    b'8L^g90YXS70oFkFR(Qmi!YC|^0f(D%6ySRjG0K+{y}*z|P~cTd6xWo1k_ATuWP<g|TewBM0I|Rn_~}+kkO<(xC<k5yftT2CgR4(r'
    b'F@3f+ugca>hnJ44>`MUCx5d(!q77y(S|VWTSxn-NBzpmWqrzg+sPPmm!i3j>O_*jONSG_?8N$4$Sh};;^~yY+wdXfBVDXf=wH&OY'
    b'OrnjzZJ1X`I18FtlTD_Maxj943It3IaDlCMHX8*-'
    b'n`e>6Q5L_@8!%R~ltBuh7vdDAX?npti6Azk23i9K=O90!3lwP039oJRfr(6`20!FC!Rp65SCaSbe!B_Z`h0F*)iejz^^v%Q_<pb@'
    b'b#R1mpO}Re@WN_vZv@!W7&($)lvBzDXzw7Xaxw8R#pm@1ugVeDq4THm`f$|aU%}0d<J~ihf(X8>3?Sw*0q2lm;U;h)Ql=t;dy|tg'
    b'n56?U(SWp2&Vrv2fy8Bq!GcJzQ=;I)kjm|e2TFtsZF(4e_&n0|Kt4E9M2wwMF^NPZI7=~z#Bv6|%p30s=wdMc2-'
    b'D!AXl^*=K7)x4Dmj3mGb$g(2l$(_(GQ#BFYB$_4MJCxye4;p%WE7lfhI7=RbW`|hFXTn(E%j8lc3fmRSeuql=URi0A6~K6l_-KjG'
    b'E%^GOH3sSaV$M<^@lHNCd+eN(Lp7waZxXBnyqfRL=>M3G4(C!2Bo5VW89{CY2Kgs75}AP#Ejivq=HTq_YP6Q0Y>%MrvY-'
    b'A{o_|rZ(zeh}GbmN+z6gPFRm+mx!d+!{lpnRtj``UfsSn#(2p<4Ms4<5~tRogW(+bRz%UvlHrCZ8F*kiy8x0~gHvHB(_9-'
    b'c)Se(VitZo@&lVUke9+R&ki>$*s$nF6<N)0s(L72KydzNJx`4n~l2yc=J0cy($l#nJqXMJt#!OLBK}t4v-'
    b'*7*^4GwlJ#K{2RrT8Fd06~;x@a+Vin}L-'
    b'9cb965)d8fEDpHP?4UYy>@2FRZG$F}E2O5*Ii}Asx@2?XgY^SQ)6W?KQwWB}>;)}lL(EEdfZ_gHY$ADS8vR$e?^;^cHWZ;Pf84Om'
    b'$1PdfHuqnW5!_p9mV)Y1+s4+9J%o&X!Y{6hB7z(9a<6bKr<*c?xoyG53Pro^>{As)Q@Wk<Me>)&-'
    b'_NrDls6VitVd)a){+eKz!2)$QgEF*%DUkSH;BL8&i3E<S8~o}7Dh6C7=cn{?IlL<z-'
    b'c{HpcX*UO?X>cYiZe5xILSb~hGrQkLJ<^L&K^8$<^wTU*eP*iHBp`z;k5OPdgq+CRIr)m^GV+ytNglCdEB|%<LCXkJu+!ofVBY^+'
    b'GBMd7-'
    b'2%7NHC6q5~Lay*)qjcvO!oblaQQ7sx&wYN{TQZ#V)!u+7YnL!1<ui02Yi3iDu8iZO()l#=uVj&rRw;Qo>DwB%KzDM(<q|n5iw<Z-'
    b'SXCL}f^uZMo;y<!Any{QL~X?MC_e44m}gY~5|_8H3)=X<$>Vw&l5?i6rTHNZbcXB-qA+#wd{NNFZP$B_$I&k)WO=bcnjSZgFW9S7'
    b'WG_{E1%iSd$H`_6)CMy#*3&;p}5cF_XAtL?{s79{vkz*DA&Y_y;LzW1_Yheqok4Ck54Hn%Boi85IRK21-'
    b'f9DDVLih)fA=4yL9ShHw&$f&Vj;jT0bdMdo098seP>mp!YZ;8+6?0ZVUxzq@;;I8z6m)`wW0-'
    b'~m^+@Sn{;R)=)Eb)mqwwjj$X^yCP{68W2ocE1&u>ke#~Q>112<fROPwtxgYG!t&wuW?jLwjv821ZFk6qP^0qA&|XI)Eb=`ZgyZvP'
    b'-b}WPI@Idh-'
    b'^@TSegR_M2enbp)oB$dh3J$14`)|L8?9fCiTVLX?S3t*Ec0xI)Vv}Sn;n1cY9k%D#U}|7bx%#V`VF!0fW$%FDX<Exmd{Z8Sn_>C0'
    b'Q`%0_=K1jl}|pN;n3#6SU-kg17;5Bg3$g5fN(#%Zyq-5gtIS0I`YixZ0DO-'
    b'4|dOxLfb>7d!0zqA69Q72>^csGp3XxcA7lLmW?i`GrtCBhAmo@YL_3l*iuGSsd*Porj(u4$*J<5+Gvu{7b<<`s$%x>Q(u<7Jfgf7'
    b'$#-@n0`Q;t)9+P@I9Z>2Ze$x-<zog7Kr5nv3w?o<ue>F`EZD3mmg1ib%`ZAY&OM(MK>PGg7DJ9e+&Qp1|ZHI2D-'
    b'#@=pW7CH*9x`*~+PTIKNd>y0F~Ba*t)XDFoKr$tF1EyJlE(_^#ru5!NfxPBC(Db?Y{V5$@w=iu;OG)*|SDug+w^rE0<NplU(kM71'
    b'xVysF0g8>(z@p-Om>?GJnd%Hh~~hLS5n|BI0CiTs|F6#-'
    b'_~C3xKu*&%0PIf9shf;2HwMxCRxSkE{xrBrm(IPEw%`<NJ+2q(@)MLaP&N^>cFurtGz?~TPnU#BwmSh0dbLNVt2W?KYfKkW8*YX='
    b'Gl<X0V&`};kt<_!`_8}6V_`x&&`Ett`#!p>7CqZ)a?NH}f}CD0UPot9EX#*>Xq>6AcJ8tnwafIW$xvgF_*EM#Ol=$xn!%w?b{nI^'
    b'w-'
    b'S+~aYC2jY&MZYJ8)8De_eyCM3&*^E7f1y)`q0ooJNiOnKIz_3f1itFng2$Ac=(ljbzC`tGFBC5cEOMs6jWlxyJQ_7i$vF>#F$rRl'
    b'#zX|+7)VnI%WYhwJR1|Tb@*<-'
    b'*~ips>Ac?I@o~=PR0=MmCyGQoz9!@TxDlL2=`t4d7A84Q6GDv`sOpU8C1^=(3W(K}k1D!+M#wy=!pLJL>m`emyj0Pgk>($s-'
    b'qd~j>G=?|%Iwt7p4O6Us<~V&UNfic%iVsz9Z7kVPx~1*d@|*Dw?<fw_2}>S@N9z{Y?T$!F$C>`%8cOwXPQ}uc_7+qG@5}Y8MS!gC'
    b'hoNm7r}UN)_FsSaw3ND=1+R}8F{ex%;i4LjM`VW*y$Ha5_#P!JRLo<!qRU)g4$Tk3O)|Ju74Im0(1l1c3Vk+>!09zSQ)3<=7rUc_'
    b'hs=AaHzHke6{Sh#{>ps0d*)FfG?~EwH6vtRrp}X>s$1w%XgZ>@wLxg)@=aZD(<6|<-#vmAm*^&W1DD!HsAfS-rZxoqlnS8$BN<RH'
    b'(dI$t`qYY=+2+&-uzfe*S{9ghCi1jVty#M&3~d(6T#lmM6lsRoEiVWV@&Ac==nPuJ%7OH|GM9%KVhWlCpI;7@s5TrhC~0Mc6xs(-'
    b'L)UVTKh{=v}by~<vSX*JiFfifsxOG$OmJeTyXV{#;#_Ly&d-jYS-'
    b'^*@cQiF|5CPJ4F5l>(AV_1%{v;mdGNR|EV_M1gSRs&{$I+l|Ky-'
    b'4c|U`u<m{mTRQ2J<Vy|L)#P7(Kqx9^EQEguu?K?8q=mmqVJlLpY;whC)-'
    b';s$%`JD0on5GR<`i`tJdSaFR)cC3Y+Gh1nkM$iHWAwxr`}ek#L1}W&8uIhlU}bjn%MSR&0{hn#3a9;FihR#MHK(gxU|;=iMtt7v`'
    b'mst)|4Y%6auWWd$T^)JyLmTbKW}>db#wgX&u*9Ijrx&RSKjP4cL*^LzijuP)<uqd6(@Aj-QK0c3yuB6^7^-'
    b';C;w7*1jqhk(T&>jni@EJN0t{mZ+ZQ%BCqVnyZ!BtRaV*bsNa$G#m-'
    b'w_<ud=N2!sAm=GW9F==AU(X^u6eo=>>FF7KM%&1U<pQ`q>0=7i0QF8-zJ*S{6rnh|ec{JqZ%pFJ~m45Ffz^KK~<&pa^|H1@dP-oM'
    b'~%h<UStF3ew>zWl_eCgG9B-'
    b'{C7+hjpxMkqY_uqB7&e^84%mCO_21(0??j#2>c%<Ne``piu8+!0JH*K5zap{a!|`&yD(rasZc=p?NREJu&$H^bfGGc5Yh_wa|q>>'
    b'`SQZ-5I*J?`6n#Y=vvJR*UW*+F}=zL+0e244IP$4*7@u&Fy{%f0-UTeJ^9D=NS6GHaF>yb%m2zZVhMeW#H`6z+3Bn-pKiT89Bc+@'
    b'(~Mv-V})UG6iC63jT@-&^KvU#^!$5?~a?}9kBklHi|Pn^mnv_#LtH@+VJFG3%uI7KrDYpdq@2I-cf}JxHx3-'
    b'j^Y=B%ouVy{FrXtp^Q>qrgTBBcdv*G0)2}RcjzE~%J1)Y@j(+%boODBP-?u+8Jd5_!S4^#Q$pWM1XIulL~lzq@W-'
    b'~6*_jD=Hk!CR2~VU5dXXZ=V%UE?0yUhU1NLr+fL#n@mqVYm^z8jCJ-aLnnz7GbcK&XbonIV!$?<<FQN7bc7Vl=rV&;&0n-'
    b'+(3<2F02WOYpL=K4oc(l`DETDaMKD%HeQKBTm|y+5R@qF<|Wq{kId=L+jE9bC9uRb5@}ciV4&SpCH1)lXa(j~r5oB42^DS-'
    b'~J+Ha2(LZ}4l_-p3LE4xcPRyFXTNcJM~9B2?Ve=Uu{u)&1^nvt1oa1(u+Rsw(AwL*pAv-a>qE(dR#`;(oQ;-'
    b'>s_kOihnAyVc!i=y!Fj=UqYmX?!{gNtf?2Z+5-'
    b'++s&s6j{HA09vM^oFq5sg`ZpNHw#eOFRk6^OpsO}4U5p>|hp(tyl|gGvhum&g@KKniGHbgIm9EMpieu-'
    b'9x2rqwSyq^Cv?_@S?)}8%s?CL7g)$0P+|bP+>so-tWxHzH>y+|bHK)UXtGsHeeO5=F7MIzoQ(v%qgRgqU$W~P`vhE{db?7-'
    b'ASih_GI@(XypM^)hq*Yl-'
    b'c$FGcZM8qFIu%D(Uq7eaDj)X$ov`%mF5SaoZdX6Be_0iUsfzh7veaOF?Tlh8(3!Nky&JT!zrRa|`l<SnV$q=Qn1Z<~7kGa-mKizK'
    b'(sy#J^Zj;PCWMtMga@>4Zf?qAQ|oPMUmcO!HoN0}&cF&d1?xj8I`+5j@4&<E6ZH8LN`w;Peq6ileh1eNnA6g{hf{{BbJYNl0L$cK'
    b'>{~9%2N&50wQwuyc6~b*S;A%YtDnECxxJ+F6}X32KdfpGbyel8ek|wYV>Krq@p4fb_o|thQZgXNHPhK+YBtH#KIJ`p+3miqs!sG-'
    b'c~z)C2j3{!zu?{~RkQjmtabI(Q8wlssfN_irHN*!UxDt@u-'
    b'AO7*Eq<gi@@wim5m%4?}6y_pqyf$v>PlsP|z1%`qz(t8h%|o)7NF^>y1uW{fKE3C`Uo^z?GsZX7BTI?DO})l5Y2@lIDekz3_F_`F'
    b'g6N%9X$<-'
    b'bEe?C~69J1v$3geS{T4mkCz3uHH20n;PpI4C4qdtiT)k!>XvLhc{fKF$xg^>S?^6y3@~6Wq(A_!K&%=O>(=DY0{%zLAtEUI47(df'
    b'Z44$X|4D=p6QF}^rdr13d|RL0qOTk+JSIP#hhXF-rYw`5?{5MLBn2}sb0pF|F$~$#vh8Mg()m67_2_0L!l$<W36#`*S)O$!c=<hA'
    b'_R>btW?Soo4j%VScAm@<LxB)9gF&Lc&n`!;J@AB38zX*uBv+_?XJ=6gFC#sx-aT@1>l2Y#B&#lKh?e4d)#S-'
    b'NyC=vt5r^Zae%6+FWqkU-'
    b';gPfMIjNqhVp*9E~RCA71Z_q@U8A0C7NqN4HNa<!>81FxKq*OZvRWdfpVsm>D~sy@7_1mvhwyVsw1>jP>D2c-'
    b'rgTScRumeq0XwuXbJgeVU_H^V(Ifvm4V{4*h)wD$_$kCOnR3_$`SnBmVT&3#vo^on5X@GnEFD$$OPVdv(+w&k|3WpcVKT8h4zsDi'
    b'tNkdXV<@9a5kRIG3V!8fdu+J)<`IFIXgAa&y)%8KGjrj)ab1gj#6`C5%>??{C%RI_VZ!t3xmUAii^V%2JY^2Q~epJ_&V;x@#FE^5'
    b'fc;9f<X%Y`1zYZY)Vm8`95HBh0kCZgu(}K@o;^E{>oqe{Kx<I$MRQfXkB|jYn1NSpY}-'
    b'XFIQQiz?Gs1sn1EPFAQ^nFDH8TNbxDj+OLof+Bo9vAq|y()3t{hYkO7qcvaVVs*Q<tx8BSDR8}(RgtUz<clKogt}`m>`7?RlF<r1'
    b'u-FWk*oepkAUKj50vGOEGJMr^B(ca&!8}F<#2V1MEVu99wE2~?jL!tAa1IN}&K)U#Dv^&#Wc7eyw$=?gozt1n@oblaxYhp-'
    b'*lf*Vb<0q^&DUAnWcpzRTwdbfo(-X|65_nwNPH3#3>&Q~U@_#HJ`L_zNcoL`jl-'
    b'5AFAiFA1$Nq4=u8x5oIX=FLIFzjvELKocr|QVM*Q?4&uFCu(&sAyk$aKxGW&N=Fu?|!J!2Y;uO22jt+kZYzunmpZ>DqrUV#&T41E'
    b'Y1<)&<ob19(bpkBp(w(Bc3~7*WnXBs`aZ<DnE_suC`(Op+26lA+!a;*8*25a@g`v`7<pITL1nDX?nwY9Z55TYKy3{{u(!`nW&fn*'
    b'EZ#9k1{2vME*IJ1r$v>ak0T>TJ==uGSi_9`+39SBz8-dtk}1>hV!l!-|T9WA-=T*$kR-'
    b'?LmUBf%uqIX!^1!BA$|ys8_HA#mPumcbyq4gUQZ&JkgYB?Fm+7@**)oMf5z&AWfk(%VxoWTW{0u)7@uq4Z;2`BUyvbIjOxgj4OCG'
    b'8?J;7gfUJub1E?#;S&lz;S3(Sl4!zeK`v=-9QcIF;l_5|Ztr`htagbNrwCES20#<?D2+lqIsxYE)BV;R3Xiu^RB-'
    b'o6<}aQHGd8i>N)}-'
    b'DvdWyMn8E8#B0Dal%93)HykkZg9ZgaUL<+HZ?5$HeP~vP+ie+SCshpTtY4B8wz_RtxX{s~KXM#2fr@&28gun@P8J5~8#Rwiu>~m('
    b'!rOZW6Zen7oddkE$j=|I<8DpYV+*>@KgCs_r^TOx^LLfN?UGsz|t9$~H0G-!_zy)V%7Rqbs?D!-'
    b'xGcidjr%2#m%M;boT1j%0ks6YM5=M~}6>upKx8XuCDM)Y}tJ4?|@kVJqF-gomWs=5SCOmoMrOWQUeTVE)N#b|zojuYgo1%-'
    b'$ZrN;Y*Y(jx_5YZgHr1~&Pp#VIT~+#NwJ*0&aOdKt+|+Bg3NN~ClNQd<3>X?s-'
    b'%Snf4Y*&Yn!a!UoLE@n?(2jDe`0lvTR2bf0?(S(tzj}P=KB8Iu&7N_-Q&f4xjFvY*l{}@@2wN~Jt4F0LmasCf^g`~b?wLBw*U5`-'
    b'c?B3YWeTn;S*M>9P<H6m;K`7o$}ykp6%N8&BOD&ykFPds`@{*mtmjwGxdR<|1+|a(Ld;L*)Myg{jxzd?vYKh_v%egm(}LWuF(tZ8'
    b'clgXrEGi`KFrAJp}+GzrEx>^lJ7E@$0=`R#IQZ}RK|KRy`O}=D8_q>Fr^YH<-'
    b'gShR|_!OMHgkHTTj?nnpB4874d^Sgg5E}^>oWck7(%bJ=dPr(6D&qzSXoRKhH*-X?M=IX2&&i-'
    b'xDh{1YdI_t=p$xbsudg%ZH9vN7GOGU1)kXuyv3o_r1e#iwlRY15id1!G3BoB|A6kYT~7(Rh>)pn1kw(F56R*T8m`1R*3h9LPnMt)'
    b'WiPkv^r>~r9L$>fv}3*{iy2B|Mh<thr*O6)*?_F(=t+F$2aK$l`)S7W@TG-Os{HOYlJq}W`EiuXP?+)|7?Oq?LZIiYZX0S?{nu=p'
    b'^D_)?QJOz%D?y3T(x@Dap1Xsxeab1>z7~qpAWST`-'
    b'ze3uE1zza=QfOTX<&J*Y(MS9unLHq8?FcWwyr0nyOZXbMS}N4=uZ{;yxV<#A88>s{)riA4AdEl`m<%rLF<J_Ncwf3sXejmqVR8On'
    b'0SMaaj^|W_3j7bmzRH@ux`}1n?rRKd$NlT{RHvmIVH=swuWWu$GivB#Ts}zv__wKOe*3LpgO?#(qLvjr(aba20bTA_}LtNSUgfvJ'
    b'Fm3n@BJL{;M^M5*#}2yyad;N0SRwI?96|_tUC_;2!9%_1}8nSxNN&yopo6Cr(YU;0Sy0bhROtF>VB&fh}y(DR}2xQd&w_f}n!ek~'
    b'rnH2d^0%Wn3FsoSHCpU_v!x7Y|DSUIn&E$Ih$>^R%B{t95T~_IH@-Q(c}qIjQPtbplS6Z`AWFPfo+&{%JoKzf{G=I=3dy#%P-'
    b'9*<q*0cd)1ZT>MfKLTqkb?r>?Cf+QK6V)4X3mp@f^xr}-j_b&DsQvmL7|Nr*hwaIN9NgMqu3V%8$qU0fXXLp<rGd;cUyC-IL`?Pm'
    b'^;@t^{0ssM*!YZjoQrYd@nE!qf7m^?ekko||tIYLAk1bJPA_3&($wa1w+T^l7T`$pes!w|<g#QTB2t@58i2NPr7Gi_T{tSGdrn`J'
    b'#sUPT@LS@UBR$lu6vdjJqe4obc%HB)G1AS9iA9l`@=w0@w`!$N-'
    b'^7B4ApW!j#ms%K%FZ<K^7LAnYk9&z!?d&Zy^2`2oy`%*5#HW1}irb{tcCPP2blIQIw-jnl8(_Ue%G)E3_D=C-'
    b'fBIfjvky92J(YtTDBI%wdS_Yn?6N<dZ_&P;{<x1wqsP{0U9);$c1kC$axe{>V6gnTK*lTX(#!sIy`%z*#hpF<=|D>1spF3BHU_2n'
    b'Wq-O}Qlqr^)JdssqiEWZ*XjKwLV1>!XQ`jih^8z{vWR=!&nVdFBD*qRC_psxXqIyyC83Y<Fo``9dzdERA0-'
    b'SE(i+%|!3y1G+*V&2_bAVU^nXH&qAJf|6yNH!^uzdl40Yl9ZBNDq>|2SlA^WAjQBGW4K<z^}Y-'
    b'BVYJ*!LEiDvhw;k5RGecv_xD~lJ`Cs+rF_dcs(fbBBGwHoN?^~kb*dD<gl`o-LEGxa0`y2tS8H@<p}&>_ZfpKUY1!W!b14s?=-'
    b'J2fY{TZ7!tp>FX&b6~iMGQeybW<vJ(ul+uBsYpv?rh&3Kz^poQ`|IC46-4^qpaK3r^ZB6xB~d$430aXx_-#NuN&G^KR-'
    b't$5T|mzaDwXMd?GXp!w7up<6S*zx5P^aZD)Wq}N=B}rQz7v5W0jRcLLTI45c42HX`TgyM>wGgiqgd6F=I4MLXLS5#u@f8LzHlj`8'
    b')ypB}(&DKxF0M)r;#_2t1LT)V5)fciA8F)kY8Kk|m9l#p2P^TRE3`8QL)_hEmpFIdHKVoM3Y%!Df;7OuwlJh=IPBRj;-'
    b'p0KJiEvnoBSs83{+K2lp>&)61KRg?+~Nfh5Pf=w0o{mcGX#=e}hV#KA<x!}vd6dTREWm(Fpc`o!xavQ@{c`tFUbPy9(6N`#6MHB`'
    b'ed43#zbJ}s}`c32^({Wy?uA4rVyVMS{x{~w@LKZUXaG@%+EQ$g%jcomcsFt!QXLQQ#>pJa?-'
    b'EKX@ZNbtjkh(Um^T0R{u1f$sxEWnjg+20okTRsZPusN&ZI>+D@4gO8t*95<gI_kuK2tST{W#Rybz2g7gbGgl^QwotLroSg-'
    b'cqC`I0BtTQQDS@WGGK*#t8}-jT4j+FQhq&#T7{}iX+B6k3|u~hzBgl;)rBfig6x!2$9tHWU-NQa8bOgtsnfV=1BSIHSc<rgATj7T'
    b'RpxjZVBhLYYgTy2Ub(RC9C1{#;|I~Ze-^0>6)zC+SSX-'
    b'E#W|=!0}wEB6V_8BKS&ngTdR+?|z5|?LMi4s~45iyQN}LyT)9^D%;Uq*@sr5rDId~tDydAn+ix*@-'
    b'xJGZMB*^s@e)4t;v}Vs>Q?Kw#P>%_XP+zxf5g})%|r>W5O-'
    b'n)jBV2rc`^gV$ef#g`4uhx!Y}0=b?+YPNh_no}(+Iy3xC85`1p@pXl9jSi^qMdv)=DnJf0Ns4d3BLi7Ls{&8XQUl-ux;=-'
    b'aRyeJu~lb`>2MR77jmBBu8sWRir|83OT#C4UacuWN#Zl${!<mDluIQN492Ywu7nNMTR(}=`z6mbe}GH2i-'
    b'2MnhP;(p?1VG^gYhe*I<<Wnny0zc0(9(YlLe4Ga);(?!_B;g+X$s#}I1OpQjFXDb2q!|nzB4A*i=irH_X`4Yh{Gni(9_DEHvV?FP'
    b'jETD$6LK08m_Qh!Jd6D-'
    b'Aq+(k?2ItuIOhRDF(O_NM1F#K6b2~u0_=M!4b$A`gj*St6WC!v%1Dk9U?Rzr#P_lcA^1J)#t?QCCs{~H6h^U+GfF}VvYYWdq&$+v'
    b'K^u%QVr_ZVefE9kAxvY~=uwWd7<n|pnES9I8Hq^-'
    b'UwHx(@%<Q4KZAuP7>+=U{lNF&N4|}%271@W+N7JcgmKO>&KS%H!J)}B<{^e)8$=;Z^N=TSTB0ON(twJLIs`m`y#)Usq|`%p)-'
    b'pK1SrBBDdwG__L=g>PeS8XAHsvWt7{L~gyqJ0<=2;$P3C?&Lqa-ALj`B8ZjRKj4>u$0*3>l9i8ii>TdpM3#L`dipFZW=%k`#r&*n'
    b'oK)-j6(-'
    b';E*I)PN*MplqVoSEG#zOSeb+l9;e+rhPTE6L$Gl|5PR^yQ4+$Mqnw5;WwH1;Oc+IoahfNd@B0C43YLP)0TL=qtvtrC1W^{@IL=wf'
    b'yojMxjOTNn1cao7ctU0*vF9h0h}8;EKscOl*ijV85ORaZ<y9<IeRZkINB11?^1g`rk()<Z&p!0hjAn3RgFKCC5XK}7LJ&xa7f_xB'
    b'#N&h|h$Jb6vz??#juR2e^mqtt^+{&sQ9@H#UqAJjkfb!^9tCE>uE=TbB`k-'
    b'n49lO$8^W2#;~eJbc@d^Lr5MLvn@6G|?Q(;+Y#4WB*Ie<qn=i=gW=xz#VHo8}9MBL&F$rkOX+%OCqYMW^8j8{(9`Me~aE?gG;)I9'
    b'rzsSo#Cwg|JaCxY>!I;y+#BENMzh4=@Um3se;2`SeVCshf2g#0e9Q(ePBnZ|y&WZ2SJWMGpJHsr?v&ah~#3DE&AT7lAX_BRRV&7U'
    b'3DCf*4Alirr(hc#5`EZnJ3bNayC=vC#{Me6KM#C%sbrJ;#j2#f8K`bO|n}gE7G%pDhRpZ~|H0Br-'
    b'Q=9;)9tBB40uX21^HZ3E51S#266!IK7$jy9PQq9eGr}OfLB&PBh24#;bO&SoZpP*~&q86#VM5{kpez{(AJAST1;rMTAkX87@({?R'
    b'z||<inW#xbn1{0j{$^z?PvNkGmggw(W17V&1GVmjaSWCt{1<j1?0G+Apr}}qiuD1V3=-A@n=S-_;9zX6LjF?UqI#dl2zZ7#Vxk-n'
    b'SXKn5k=Pfo(L)e49!*pDUmuhf4!JM%bQ(sfM{oiHm&X>)*6(R`FgFkdcWO>rl?qNHIMx{Cc*t2Ez>x;Io>Gcn)-'
    b'=t)#EAkQ^PGUCEDmsrKr{w{9{~5kZpqF=OGZRUIsuD1M87a8EbEWU769ABasMLwJLo17B8lX8fy*hZPc%FLhiI=#x|G9fG*6@@sC'
    b'z=-b1POa6)0gA^j@obDCIp<=@E(64#V%7T9)*D_yY#%x_a97@jK8BgP=QM?-'
    b'qJ{VT`hBi*+7DPz2$)4nh$Q|JaD0_p(hOx(jM>##tcW7QJ(MzjC1C>ckw>iIHci``i@$E95`rg`u*B{mHP5yn0lE8ln=DI>q{hL*'
    b'}(o&o=KU3AT2F8md2ldf`%mp>}9PoqvgJl!Cl=&rV7G_Ri3GDOJS}U8r51O1<#fhPFKlY^p-'
    b'1Q3M7)xc_k&<CMlZI5A<!!F&Uc3|s{-3qUb4@J+!p!%4uCC}lLr@;C`l!hAiRHuDu%s<){aX`{-(3sJ-'
    b'=Rt}$hZ*<4a2HTS+7p{;wP;sFva)0*ZTj6uZOxw?y^91XHg5j8e^D2rLf#*yZ_(gH<M__7#eGzhS?g&TVz=FRB?tljdXbv6|rr-h'
    b'x?Rh$)7Vdd^gD2S%eC}D>fU?@euK*C9IB^S2<MW}3iPabXat!cP9@Oa>fBrV`s>XvWz<sCkpiR^Ge6S)+b%}R5ICm-'
    b'|EJTgZi8hE-W5X5jvs2m7q-cB|m{3uD6I_mrojUu9mhtC31o)}(;|hS-sr=}taeO}25t|xEt^jbI$`O;A@#o&cRBF?|0t|KP^cw^'
    b'TBxhjiEk(=H6|;CD_edLbr%TnrhW2ys?w<vr{j)9{z~bu-'
    b'&iDowQ<NT4Wm9yyxMBGOEvN1v3(K682lvo%e7e8A79MfEq`Kjozr$@WU8bI_^S74rEw&!}-'
    b'Iy2g!5z$UAO08IT@T?TCd7xo#3V&&n1W!7^E3prk!68Uh_RpM;421xo`eVo#+W8ZUJxNm^epug?@35_$VdP$O2a6FS7I;Z!W+$EF'
    b'B5^r)Mp+j9wbZ<783Bu!AT)0_%SSGk@2$28B-AT1-'
    b'+XVe69{4kjK}bUiOW<nHOI74jtnw$`p32zHt$y3SCz81eg7358WU|e&`A?&^@zXTQJg6%ZIOti;SEEswz#Xz6@%F_eH%z`MueJxh'
    b'#2It5W-Y+@5F#JGN4d6}3v6iu0;CXnXX*sOYWjvgQdmJ&08C)fGT$L|-'
    b'f&78*o+oPOe~eTh3ZmQ|LyWT#sYcd7uJ3asnkmX`0kexeJawr-'
    b'=Gb=jmLoa)l7JDIo^=d{WAwlME9*9}<wris6Iw~#xeVz*V?l3lZTJe$XYFNUZqi<cU=J&)g>b&*qfZi*)9vn_jyEj#>T>`)2NI?g'
    b'V;NL(@4u)h1hleMR8KZb3(@0d{fUpKeHI;@6a=9q0cUFMk6bZOaTPO>Iopt)wzvee#`+0_=dJsZ6DNOzpwE(5A<4&2C+vOu1bFsZ'
    b'BpwP{j`tW4w=YP6!pad+1&^J`R1hbhwC%l0TQdlsM6z^M?$dG6(yc_9k|l4Fr>ofGiU6HKEh@-sh8xep7OAq4-'
    b'=MNV%R5hlPan$k&>4{jE;D@%-5mFLQjc6{|zKq8ys*ou9wT3i_I%Zxh2JOi@{6R^<2Jo0IRQlExi0^Gt$N-@}QC`jTY<b-'
    b'exrW6yYBDsk0Ve0e598{&-dgdqP+$btn`h6-'
    b'gkCW76@NO1Ii1{hW(ujB@7FU2m_)p?d(1W6@6$*kV@e%c+G^Nbvxkqa6tOYDN%@Trn7~q%^l7=}AgD~+U>~UcNf=bOrqIQZ?(86F'
    b'sCOioelw%+w^McxBh6C-?$4h-'
    b'vYex=j|3&G=a=Nv~aaBVgbPAYX{M@`uD8pp3vBl@L=#rr`$*Yf_*b`AHwMK;B<1}Q*4<a8&IgLd`n`LlF2*pw0N4YRX#Cnh*q%26'
    b'emyn2tIHZ`QMBd`F46pC=q2f@Re5f9KueP=^gs_Xv<l5?4;~^;vj79cH6vuJuCt-'
    b'?2uiGFZKsP5~H<3JG5rKoAfP29MFU??U(=>{cIO9CvInQ`&<XUA+lk!$f()iJUrEBkr-k76Vx9<}JVY#Lv^}1|o(b;-'
    b'o<ikDMQNHR4ww43b+&irr;K0g%H3qdMY-'
    b'6uGPfypWwH<WZCUzVd_ttI7ZmamS$gY~UscWN_#%k3Nt7~to?zYSKx+Qi6nSABQw0O3p+lVaJKG(B7(_XuH(*L|v>2w=&rP=m&yO'
    b'Iv>*=cJ&+<)i&&aFOm`^s;P_I1TYVEwJVb;ql1BvRdBQ|DMeTm+!a$At{4j@DI;5_4Q3=dCHCmD}3*#XuuQedC6Ge1T)_UXJh@3A'
    b'N$FLB8shwyST4iC5*6&bHvrZSv>>@DyS29s|O&{?fTC*uHwGG3G@3Od3V0hoOYmIb$PvM1u~W#WJlKq!I)yJ4o&JMn}s2+`NV)sB'
    b'f9t-f)A4R@pz<UXeY`Ax~(AIk--'
    b'DOF~zo(iz2-N~JD$+np<|wnA42NsA5|WF5N%+Bj_<rSa_J;-|)23$wUnQ#nTM)9ScR+g^5h`fXD=SZe!A7xlRu{tO-PCqkfNah@='
    b'r;Rw+n^a#mv=4C!hJQgNN3L-8_y%2lyvX3A7BuX+b^1Z~1NjgdR^PPYbNJO|mDDnWs0cAL3pc+I)1}-'
    b'w~!;lez(ww9sJ0FD%o?sErqbv@iu;H$%H-'
    b'BC4*%B6#FTbF74JftfQ27<K)U&+2)q|)8F&6qFOnDmRQJi58+66O=IZMC`i3!*}h{jol5yvs|{nP^sIR`60^>fC8a}d=m47>ypSX'
    b'!{W2rRfKijD|Z0CXA4q8NiufOzZ&S%kuvq9n+8nEHqZLBc6=BB~_B+=I<SSQzs-OhM}j6df$OEXX_>L}|uC!E><oM9Vr+*F@O&X`'
    b'Cf2P3d`vs$7qH@vA$bsX;fIN~0Y6C}o-'
    b'NN7M^4CT>7r7KW6HS|tQn6M><UL}0YUX%r+$mY_I+Pf@@!oc5rpby0C`AQk*E#9|ucJc(!?(F`2qD5X9aSz+i?jtL5L3{wN!J<AE'
    b'hiMS={aoD^*1#{m4q*@m5LLk+>D~49;yfUtO)gwOIfxhZFo^jO~R~;gmCy%Mx6#ig~v1j_@psP)ju@huH5zSO1uTDS+hvJ_OB(a1'
    b'L?HGv#@jDUf(~nzGWYcXjeG5@@q!B~4Y5O>j823q#r3uZGkVOd&Gs=@3<17Xdje|T(ea5l4M$BRc7B<)hqVii9A|%U8c4&Ef%v7X'
    b'TRqDQ8N5J^S5Ac|18&%iv98`gq_*~xU2TdfdG6U@*?kAGWFbYMfz9gp@G#Wtx_oIX{3W`1rIL1*qqN3IGZ}cJ1Nj43jV-Pnzo}$d'
    b'lfKj1`f*?*o@g(qfh9b|WxsSn15n46pJV-O3h=5(66BLJmpQW-5=Q-R&!?=ms+)VvACPYLNNW{UyOTgR%<x2yP#0jOK+-'
    b'V9_!Xu2tzUPrZ6p<qtC}c0-#P8r{Eh-'
    b'>;zn{g?IPiI#fe{ep;L(A<LxRxHX&h28>w+i%TQ6oFg$0hlqzK_}UWUMA4H7V1BXTB3{b3yS+Z>Iv2nPYpg=rk-'
    b'2}~6Z7Ec2YOk_V2wM8?Z2Q(8=o&>Dtn2I`eN#GM6<2(ra_h$*0*ZKKzBED@e?0qfk_*~5T`Yyvsu7Y@AH3kMy8`uE^j0$F7fs-RS'
    b'q=S}bOfcItyazf9b&T49A~#W28>(!vhwNCg1vGZx=dG<~-'
    b'_~yHq;U!_G}miFVYszE4DFQ@t5rE_8tqp`d?#bg_kt5`yFOeN&8_QwhepJNIms9T^OgIeM7l6x{4}5hM<fPWK;dNjA~!3|JO-AQz'
    b'!s7)3FCx?AUhF4GbVf<CJZ)U6nJ1+^O$9XW}F6;B0nK%1{{u4Fv7WjZV1XlM7@ys$n!!!2>c`<IL^<(gu#yTMJ4GpiQ%o_rg$k6W'
    b'$}ZI`V4{E3H=O%`T>t7@;C-lEM+JKBR9(fjuLm4tw=ygz}-'
    b'P<CTzDj1dZc^nVt~XK|zWV%wbwA1^q=L1g0{N2ooig7=_IiUV;f12S%T;;@rqHcNcs(?8b)~n603^V-'
    b')2H4#3#WnCJ5Zly4d(!afJDA@U=RP);&0hGR!T3xgjd&Rd%GW!q|bV_4&Mr1czh_zK-DtmyDqz_4R$P#eZ_y9C^8p8L^G`Be}13>'
    b'42m@u}kaI{=M`v0@wm*=cBYBFQ;^J~p#9e)#*xhY4ZKtwy^q+n0kj!lsBnPr`PV&E(swIs}c<ZNY!gjlx&bqu1pG|M4Ocmki6I%*'
    b'K(Aa=hMvs$CUB)V_57N?h-'
    b'hWg&rFDXYdZ3a*5YUBPG?YAn4uXlx|=`CcnD2q9B>ld>JgZhzJd@b48Ys|g63AaO~a2fJpoiZF+~Y$={nGF}SRoglA9f$oawYSz`'
    b'?KY1u`1RLvQ*RpMWMMfpg%aJ`1`?ErO;O=<@r(Tfz3CF%iA|@O`FUpdLP{c6j;Q3J$u@uD~^?jbR%ttuMxQCdGPQKRL?(FyV;V4R'
    b'o7xj?8u4;{2tdLxu`&kn3*vq^;O+k~SS%|{WCn>=RO2aHkS(XJM{2yX8BvG0YQI{o6m>&VN&w=E?MfZKt1v5)Xo`)j$HV-'
    b'@xoN<H#?gg+YDGC$fb4)|fZ!FFe3M2(F{K<0agya&?Q8|t>--'
    b'|>O$Xq1xf`)`&CUJ^LOfh)seiA1+_d+krah&2j46uhm?PUQ!50b0)b)!^LSy@ZhoV^n`7j=Vk0SPz<p25*bB1#ww#MMETq$G;sG-'
    b'hBGAWz^VA>(13lYj<^I7xZT!aPMu4>(tGXB2!c^%&T7A%gvrgVjQ#C=Fu|)|JpKh!gH}pT;=Md6asH2NXWWX`G6{VhlUPmA%=d`b'
    b'rSp;H{$GdTX5Ss={Ejqkq*CKjU;WPItZxe`{Cg&tk(kXq{;<b^>&bBKB8p-*xW-mUErSo-'
    b'*vkqHDJxn=7=xuBw*qdTU^qday)b)n!QZZ%-'
    b'+h4dBbc;$TKN7MC>qG!VCxQxXRR1`IPA1QE*!*cBLOQ*q^{Qi6UiD1W_z^5@(0ldg|?edlVhQ*|pW{R-'
    b'~xeYrGIIQ@(w_`MZQUACROB>&V4?4MOCe{d~)hgsBHY~Nl(zpG8x+4%lh67$+1e^u|bQAE3BMA5BU36M#YX&B!(I}e?zyKY4_+kd'
    b'>Q_fldz+&1G0Gb(x6A056b#;w((F}`SmdE(rat7v$7JmX0&+5^)h2sq7Yh|?ULft>nb#JMM~7}E%$3`brrg07M1gbC`z%fU7qW=I'
    b'%Cjh7Zm3$oNXkOgB7&x{(79T)-$@<Gjjrxz!TQ!tlfl7RmOgoE)MV-~~LEJ?r<#+Z9FBAIC08YI3-'
    b'e5*z^iW`Z457*DKl6R?yDjC*s1Ei;v`Eb6NrOm~@%yTA!u$Jv*`Ou)xt_hp_>A^lqorji{`dF{K-X7Lcaox5rKN_LxX5o0-'
    b'^A>}__S|B9SQMQ2anYWl_<p;Cg$61Y)m4p7BjQ@DdvJ2X&^mvv_RFtwyZl<c>u3GT-'
    b'v;Uuv(UH>?(5LKXunD}>%*h`ZfJkTYDSm!Mr6Ok%NBow(LTUn<|-'
    b'|o@p?Z{*q<PAn$o>$T79;JzYt}xN_ab21EqX|a>Np_{c}HHSuR8+^Fxv*;CN*S5l@s#XBa-'
    b'rQ<nP)O*j)V5zKKIM`uWR2eq@LAH<tk+RxIyChdPKx6CZ@uOoe$Qop)GF7n&PENiUy?SD5=F)zLBkMj-nq;2utWa}*x0l9oyA6Gj'
    b'Sn&qOamZ0VEi0j|Woe<z*f6l1nT+fLu$~Wsz!2$gAvcV$N?0JJ>7GKPt4%n;h!q7!E$fEPwT?<2Nso>hE*=2uRFQ}!|TefMvJN!X'
    b'HpZNC`$PUq6$83)ya*V`R)uPMJOz(b(qbP{=caM1cNy>RC*#iBkKuVt0biaE!!1^Ii{-'
    b'6Ht`9)wVI}w%sAuc}Exvgt4NLqaKyxDyd66YWj#l&Zuoe(5~-D~61C-$`4e=Dd%UJ@iBO8v0-cK?YP4@;Cz1}|5~-'
    b'Df5y8i<?y=GVKIqxpS`GGBfD3{rQc(_X7FpI;7-'
    b'#w)&Jc&MBs?4EyCY!``;<;JN6L+mBN6GBNE$;ed@!2>M8$jigX^RhgQbA)3LhnPex2s0jHmZq5(l05KI#8H^~qhHYYwAm5SpYOOU'
    b'61mhTOYzB)ZW!J-'
    b'o+@+Ll81NC`1n}tMWGnq=R11%!{OUORJs+XUich;c>G58Yo#u9FR2yY)5rA@s1kX~IN!g25{AVufBECTeNcZD16A<tQ3!=kyLa-'
    b'|#`+7U-&U=gFh$RMjY6xfJ!-'
    b'A(9Mb|yG_MX6pTF0tRTEa^_ky9lK8g)rJYIaz8edlL9uGZh4L=k_8(bb%3)YKDh##@Sw_znr4tU9Bf7(N9a`cBw`C&U|rY)+~ST3'
    b'*Q6(@MVV^=(%u*Yh~4vT%YP<HFkmW-{k+I>E4Ypc8ZFV-)Ow7o)m1?~ntwhoN?5#h;!dfl-'
    b'7LP`1u>DZl6hNe#8M600JG;#aZPD8#rt?7mt-'
    b'B4x2oY%JeaLKDKucXH(>aY{LZPalp!Z+;&yKT@Z$NJ=`Q#W<#M4RVfcVyZ&w9}|?Df#xXtU(rklOo|K^~i7IRhzd!8Je!E+&|K*#'
    b'ER_&o4Wk=pJ$o@4#2^<Y&Q2&ntLhDy_Du&N^>uzxtEg5wl~$qP{ZDG@CF<A^(Ax}_?DJLEhFF7#>N)Ok*guI_{6Iye7X=OzLD-HZ'
    b'TmftJ@-nQdnKLND@hrs|6V=z+kILhUDHUdZ}M}@)OIr?IjN-@;r(wOdS9l^3HekGQZPY@P4Fog{={@XC=6s8wAx1lTK@At{$-'
    b'gighCc^zr#)z75~h>E&ksR|Nd`3F4*=Uq0s|fum2y8HwX6P0-'
    b'XEZ*VPtpix0ND#ec%Eu&Lm$;MSJIKNQlhl%xH@d1p#sGm&0T(72{!O2k4M>Zexiyx5jdbUZ2qBip`!GyzFOM5sx|7yd_lEP|!Q<@'
    b'aV*B{(Vzy?x5-u?HzWP1j>lgliY;?c(^jJ}h7%K4S?Pm*bRPpA5lP+tL8O!Z-'
    b'_XM)Qm?lI2m#a_%!Qv{4eH)F*L9B9{9cr#TM75M_y%f%B00K>&7L$Xb;+dzddHAMd~TVtant?_QokYLGo>gvZtXMISlEonl!1t-'
    b'M#c-yIH0NtA4pr*N}|y>fg34ZD)6L_Lk=!QUvA1pmYKc(bUhnuUDn;u#im(c=D(3pwOr0q1HhHYaGbgWTT>yx-'
    b'$*2bssdz{f?A{k<T&mu-&sVk7An4v8dQuyw_YWK^ml{hH~*jfCL$&)>>lR%(eBp$Ir~iwflUgHfA7{8Qh0m35+vME-yM!@r9R{`_'
    b'SxBxfyue+xSe7!D^4v~OwbR2I@R76#H%vTpIR1%|_JU#MRx^ixU>s&6{~{=5+e1u*{b@(h26^;sWbDZXyuwD3Qa=XAS+nZejXxRz'
    b'T~j)AKLhL+*+KkwvJvB(u0XSudmIv1vaBWRID(0-'
    b'7D@!?%jUO*lM^0M9>*PyG8d)Ze&4^Sq6%R3GijAGb7ts(YmH_5dTYbb|;A>fq!NH@EKIKAIiZF%$c5!kvC(vOJ+5R*KGn!5cpHLB'
    b'qEL^>UPgxQGrk?eLNhAY5aHw9n}uIdjO^z_)H_hwhq9-'
    b'b0ClVX&^ADA3jl}L3^7Kbaa?AV@)ki;YVec+3V@$Y?}nhwjo7eHTE)4dp`Nz_<-q8YcEgz%`x%|@HC^H$xJ-'
    b')I9I?#<^qO`}O1Tm8d(PrX6ZSaY|Ad+)Am9O34XG>t6=efQ<>j-HQm_NT~*?qq<Gc7%zGPGu)FfZ1_&z?3F#2c)k&Z$|*&-'
    b'g7U>Vq2LFaYF`-t7QeqQz1o@(zOlJ#^OU07oG+SoWS-'
    b'~W?u$sM4jiCLy1$tBm}CcVahTwTG%~0WU9WYUDGSlnwsH7osqnF#@{wOEKpn~Vgn2P`H%V{*x?V=Xom&fvqnPUgAtE>Q1wTSz+=3'
    b'r!I!XVz-J+uZV-%EmTwyvmMCIr1(+&JYwF$b3}3E)uhnUh)aWtZt4G#PV!SHy+QJowgh-tb*~qa|H&)RC7n)wa)ysByxdYNE2l#O'
    b'v`Jhe5$6l%3;VFEVnVb%N-'
    b'l0$33a~?Cb!m)`Wjf$$$5&O>pS}w8u1Hr}9KLOjk4$89t9%h1)@VfTR2ZrZR0(<bhawQThS_XIS}>6Gvi-'
    b'b;Z*?Gyut)r5z1z#Y7nveV7~k#Lsui?-c=x3^4nMs6&8VWKHN%HOO#A{;;^#tSeb7ft)hhUlk{v%O@$;K4%<RAKh%U?c-'
    b'>Zu)4=(s<6WQvr*MK;(^}#ucJV%j-MUhXbN;=1kZyYl|WpS<*A+F1l$;48PYY0=JW-JfzIx+gD&42O6_#PcoV^LaFBJaKpZB;6-'
    b'z7?6c8}w<*@>QcG<-MoB-'
    b'))!{^+grPTStOxT0VPdQMQ)3p)IPUDv)=_OGT}8s{G=|{6**;;KZSPo8Xao8B1OSJGh7y7KzCzvwA>Rea^F_Lf7Ea*eG2Tj(2X<w'
    b'S4u~GKcvJ>08!ur=l0F#Er#cqw|wWA$N`c^-&y1Roi0qpa1dG>i@w1E&ux0<)8ojACHeeJU#tzIQ-'
    b'YUbF8Bo1swqe9pc3eMm}xUY!B|))iJ^ees=YHY1wmKrkUN!a#}fqdqFz&xJ8dP6xdMx(XR>yiQ)mWvr`QAiJ^wvc-?TE--P2jP`G'
    b'~;4C%t)f-'
    b'VeBYznzezW7rC;F_NON@_YG7==qNkZio!ZH4IHaHE3Y42;dd*u}t@I1WpB9t7jw3O1%sQ2qFb>z;6?%u{qn(5uP#YvEpE+^M*=y7'
    b'}ClGMm-'
    b'a$Ibl+5WmPTcb3#JW~+~TFRn?^Xc?QzmMKp5sk}4fK0LFPQTYuBHV`qQiqJ~z&%^5L`Y4)Z>}5q61gmM;2RpEq_FvaPycnT6snyT'
    b')h2e@o5N;jx2_d9Dlmp&_+V;upAi1^2?>vE4hs{^Qcv}O|+mK$IC4K5oqQCLmTXOu0WZ#G3MSGufC@+3%S0As0_&e;DYmj}7-'
    b'C{v)&(dYz37R(42NpZ(RU;k22}sAUu)BX2F2ZlV1?C9fmsx$fiip6Xsug-'
    b'Y8Ak2OXzhNFHdNFGyR|cm+E2}CMKgLb3_TgLGv|z=+h-'
    b'IFT$gKsDpR{8?Wihs_sFTUs@3&Vi{`=|eYbt)LK$<Rj9cAVpNLqT)YbN}@3haic)zz>ysi596R3+~ug`y$mDMQff7Teq9V`Klh^7'
    b'DsI_9n7$t4MnmJ>K9bq(`7dNa9NTc#(Ct9oP8!?7oEU0i^6E(%<AvN*FHNv9Bc-HBRZ6TbYZ*l$0njr0L_=`ZCbwdQ9<_53UekxT'
    b'TcfnWNs^oFFIkj}Vl!4m!qWX?e5-P6Fjx9E&$-u;eb?*d)1lJ0ybalVsy&pU~ey!|$zi*K`+`F&p<>d*zIyXjxU-IT93Uue7w-'
    b'Y~g~Lv`6v9NO3IV?~`QB7YT&Bk#a8TrFFUNbGX8s%4!o!^~dL>;;)}ZoUq4TmQz+`uRf4d?9AO5Yx;gR`0k{xr-'
    b'^W(4=Tw7S74ob27HJwBv!6c4cL|)3KAfsjXK_Znh%!_G%*<dNNvH7t?XLob6Ht?NCPZnK_U#oA76u@Xnn%$1v_5!{}O@IeamPFXr'
    b'&YwZj)^is6fiT~ZjSpxYd}7_I_(qZX}Xwf>le<4tqS;x?XC(&<V4q83N`Qh(J;V|Aj^ekW><SIo}N?Ch8_ZjM*n%a@ts6?42|j#o'
    b'JEOdA%=YQwglj*s_S%fh6l8&N@)uW6yuXZZiSh5yr&jaE1OpSdz^v^n-BZZqh)IJ~x2`J^`P-'
    b'+1Iz!2XC38ilbJ`hM!gF+l;wF(oWdD9KWSve?Hy4tWg5ua^ZW<rz!;kYnyg0U@N%61FpVwu4XIk~88zsap%Rg_+_0b4;ju)&Doy5'
    b'^Kyx6m!Jm26;4dC!V<z&l~B)qa7J=G_;1DN(G=6UE?0?(t(}QaVv=$eeQhy>1B^6CvWPMjaF1h8|s%!mU5(tR3<9O8J%+-'
    b'RfMm+MAufm&XGsYXPJyWugDoKRitn|4{S1Z+)R>gr&+<T+~2h0U7Lggo4g?r<pI-(!Y$vuXNQ-'
    b'~aSD+oh7We+{npjX998P?OU;~?blV%%2B!U)+2HK+?oI1opPhi@#(r!tjsr%yV$#wZ>z?TH^*Velt8?UXPTbx^r!{XizZ;fx+mdy'
    b'go`Y<~ezUJ(r?u@Qi(z9oEP5<~UM=m?prv-'
    b'x+U0d;(`5tiCH+aQw=E!vym~;gSPmH}`1Wd}k;OEYY95YAr24We5LtiXRm35q42L)g5hp<wCUL@p5al#VXoNyS0_ORC5+o>#GcTe'
    b'EVL9Sn<Y!Tk#Cd>ai`C9JWSg~f4DytXIL9CF9)Gkh${c&VIQBT0W%-&O4K=9uTd|~C3l5B>jQ3KzaX8-'
    b'lWG<!FI1?*#R*^Q5+d>7Kz>d2uKBV3|k%&*jewm?w(Vzf}L0N|ZY8zt+3eXtwItW0w-'
    b'|TdF1(Phor+MnzhwfGTPsr=^pMKU0^g+(r>O7&k^Ca6$PRwz7s~3-EH)l$2j%-u^_FS9^-'
    b'Y{x$dcIIJUnrU{6gA&bnIiISBRFkyWA({5R=)=2T^p%m3SuA4&Ee<f@UM{a`|WtJYQQ0qk-*a?VEpi=+vOSr-'
    b'+H55gXZgQk;V&@d2lZPv_VW`rUy4g%~hx|`k)qM&H2hQP4WGIv;9u`fa*OfEbObNXX&h{huA+}O3zT<l2)G_R(8h8MrvI)&J+H9{'
    b'q*wm?gtdZKh|6I53h#hYJ<?2it?D`BPDubP*(0e^EaAYF*}BVL+V#g_y~Vj<7o{gTq_M>0G;Y3{~TIBYOdNkU)wg(J=BTr{R$$n1'
    b'KIQI$e!NKs;Cf}vAvOt3Q<4w(>(B!JY$4JgmRvw9EVwm6E6rdoZu+ILEvE@r!?i1`Dw_r1d$Yzs2AJQtGNW(^!^K)aXmNMRB%ccu'
    b't77jHyGKQ7_9bvBWhZUT@0z|aVB-'
    b')Zw~*?R*>5Y@;j}d4@$nPdNr0NyeP2RL7+INV+EZU$*(JaS6XPxJGbYCHXi#pTUWDnm7lp4=fu#vCx*5bWKIe_x77K%8!PL9wA2w'
    b'O)uEWZSWGd`l~EU2f}3^TR+)yCs@$_@m9bO?msi>%6$<}li=SbPFXH>+!6FDGWM~~q>r$UCObuBuwXPXD(KXGTdWNNaj3#IPc|u~'
    b'P3roLWmSYE4KHIuiPIYV;NbNMo`t}%->u3&nR+8hJsD6%uA-4DjcC=dJ;rmLB=j#LTbuIq-dhGCu{G~y^!v;5==(52rkG%>TJdVJ'
    b'&=AH+~)#G`brvb&BMKnP{6vPzyEI}y>qcEgF=;xW2FfQsx@_>@i3)7Yj?qu$4e-GJ$v+aF*+q-'
    b'Kqu4Q+d@?l!G_xIrm6uO$g$^L?`Q+~)Y=A`ggld!S)Dyl{U)!$b5cobOz)8fEq(2>)jW~$Zsra_mvTc@>dyO$$auk7MbjVSc65;p'
    b'9GBbB-z7OoT9us{%<`8Xn{OWxGdl|Kp$A@H4fIfD6AB-Z>6*7>JBetulj4!}UYuW(*%LfJOO!H|JD-'
    b'c9RdN%Lss3b77UfWW?|>8N8#4Gedfj)+je0}Q&}iVT>QXvH)k^1kl&pI7p9O^=>QF{<)Vre!oV$r`O9rXF7-'
    b'GIvWxpx`viqC^u}0E(Xv@W#oNb>8id;{B_FzR_9`?Vg?ljxmwd(A1253V5ODr=VeKG>sOP;#`2Wr52k+T~$TXloq2#(#UHe+iXo>'
    b'&J`B5ItsBpEtJMZ-'
    b'B^p$e4q3uie6}!132BoPm|?!8gIaOT@dF<I&4?uxH<0RSY4a6@Q6!?^u`>&@$00^aCl~P+DlTAc@zGKQk^o;eBJ$D4m&|!m$Z$=;'
    b'JLhan-CGD#bmwFakg_dn2zP$68vJnKZ}BCw=I44y<`U2BZzbM(FoZ`?zE74=21J8+mm_Z82GIGqn<dXGbGs+5_H7y>M^uh49gWmv'
    b'czy&F%)Y!#1YxB0{V5Zy^fpPaqAx3xQW|3aZ?9w>BbFPKwlGab0A)B#HkJuwICWBrsBXfY#@XM1h6~d4X?S|Ywh(Khr4-'
    b'0Jhp)z(*PHz(_1;sTj(?I2ioJq?csg{w#ydnu?3se>mORiOT!MS*$8d@?YP16dJ`<eW`gB!B}4yQsQ_zwW%M2dCwpdFky#}K5c~Q'
    b'nvn-'
    b'8SEY&pTY)cy9G{GbY{3P>O7V(hg9w#CE3xyd%5lab*aKyytNgDf!PiYiH1Q9>LNjuxJm&tS1<tbZo&c3{T_T`X8nX@qGEX+9zbI!'
    b't?voPl@%sC5l&cd9tFy}1HISX^n!kn`(=Pb-'
    b'Q3v<rGoU<_JEX?bsVh9{+iW!(T%En94sor(v%uDys(_`~(GA{KSubORX8FNzXy?vIY<;6FA)zq>pJ4qa!FW1YeY!5jx{@x&)QoKo'
    b'|aH$~86@_$t&?zytPT6QN3xlI7KkjUH&Ka+Bvg(|yIwz}MAz8IQyXL~A)t(p3$*Xhn>KjR3bvyf=&h{|xxX;lY;Ar-EhE6AMxRcf'
    b'86%BA>hPe^lcE8Jn?=YeJY+kqd+G#%8?7eor>vx{t8a4A<|Fu#Vze?`*rMbrMb4I0nQi+FE8r<vXZPe4)NDQ8f+Q(#_15*qgY0-'
    b'E!y;N<)dh>_c2j=@eo|^ay11u^F$4D3Cph=gK(#8G-'
    b'l)@A2zDN8l5;Py#LREB@d7JV_VwWAt+*x59h(2mY>g>Wu@NHYK#Sf~o(PhG*e2ebrCw5!XHYUKL@u(kBnnv71QSSSGjyTR3M`0c$'
    b'5odAAQOr@|r$OMyILmpGN3j>toMto%vfl0ig4;mH@_Dye({IZs3>NwCDy7y=W@;ld3}S*q52GNBb3Y9OLetDk;w1AuoKQp=!7Phe'
    b'N)wJfmZvdHA@+QqhB1r!+r#hIhtJCm-m-oI17su6OM*1SX@c@RO>i2d3C$8h5Y1zc#lT=6o(O`_Pnj38B#C1$3>ok}hDjtjZ4tQt'
    b'>MiNAINeLJjh3aoyHuyWi%Q={WsCw?!GOkMb%U728SvAK2#qm_EZ~+Or7TQC1iC#XaftE+CtjF&JQnHH$sj5}ZFU52VC8qu1LzE_'
    b'%Z+gC2SJ|2A@S0X(kS%_CzxVb*C1q35_>4iV(jG}r%^_e#Ph?@PcTnBFZT!0sWa1+9kZlty%GD=p!lOZD_v#kI#R-'
    b'irFcuRVhW2V{QNBB0_Y@1`nUY26ugJ^@5jf57LW@N+&>oLq>v<1tSG|N@1#hPual}_VN!Ea{&&emHTtsBIVblOQ$k^Q{x^MGZ*n6'
    b'GT+XSU3BC~S|GrGguH@~q!JtBN7OCP7g}fD~Oh{a1K|U;s`Bv`c!$g{ufwYVlkN6;WL^;%=ut%z!0cxedk$#p*bn1T5!=l*w!i0Z'
    b'VDD&(=^Hf-'
    b'9i((lLm0~(R!lwTOdrxfN&9?>Ul?V7w3jYa^_>V8S0|(p5dSMH?JFF>MJAjS~%qfTx4dP4DqF*vJNN#eZ<E6z}5Nq^^!HAa4c&|f'
    b'Bz0qttjZyS|DBoWr_{XaCu6(MbtjhK;f9MPjpWL2!C=z?sh3bV{ukg0-'
    b'yII=FozjFkdjwa?5IsU5DF;hmQxeZ8P1hC_Ab1$wtG^04|Ai^xBV>oRsP&B-'
    b'<pX_zp~_Y?S8~DPrVI9GE$#m#59QCLZgclkOBy}Zw8g7*n>yRdsC>OW)*42<R{W)@Y`cS~zU;bwSbyU5n}=d+0rv~TN8Bw``%O_<'
    b's&lE%HUec>d;-FShI`4^OrD!PlUobirUw}32r5!|0%{v-'
    b'?I>X{SRB=22zLJB1q8x^d=qOR4XR>S{;2E|phg&1U}9;+v$%N&V@mQAy=waUv}@|sNl{i#WwfdDc3M-oJGyl)v-'
    b't1tw7FLrMj%P~Ms+VQ|N8Oa?*%Mmv^)Z#C;N*xpDg>jJ4P}UqLiKDiAsNKf<UsCdKFZJ_@Vx0&%W$FOGqDR{wBZCf<^pB{k8b=;h'
    b'izuHzpgngB>k?gQc>-{3!Ze36Ses>qiRvQjcrKNwUN_uM<%0UXv;1m(_;0el7Mm*!a6=$FE`YuY?=ydbeprxSr9Tl(-'
    b';48O!Tm>e(s<yV63u66fYKTDO7<a6Pz#<Fx;}J}`52^{>^x5AQy{y*7hA(s(TAYrcGYy#>0~Ra~t@=Uce9zlEz@12`_v;DOIqrRJ'
    b'+r^Hr(Wc~xp^H;1Npqe3TKOzTpQR(?e?$OLJc+{N_5{8p&W<$aKA!%cCDqiKKBkGYV2!pWr9$c@!-'
    b'o<upOvKl5yV=aano#UtV=G#Q(T_b6<TZaV_FqM4r5__1+<}1;T(XI>>h{>gOFs659(MH+GC5`$nFb+Bt3X#(2BfEN05y3~Zph)EG'
    b'3~xkC6rfi$f<L?vk;AqVz-kdeYCg;kgG-P67NYm9Sr4r<Qv9&o$hWV;g05GE#bkvsqf?n-'
    b'?!(*eAkVRbYQSsPK5CJEI^!Bc3}s#c+iLiC@cGRZZeIlSG&)!Sa0OG17uBHm^Xj|b`u@r-'
    b'@95Nk?Wn{WtI%od?Z%GNyP_F3uSu{Ut4(j#>?n?e3}3Cv<jpc=vrO!0=3KZ^6q@<MA0PDCD&}i$X+ib7;_IvBFsb1NMw+#y+YIlD'
    b'z)y*BS0Q^5s8Bzs0Py|p$fyzAtOp7!EPElsemX6b3%FZ6te+C`!dhUpGqP9`TgDhQQO)$y=>-'
    b'`zq1tfJg=M8ghLbJqmFhZ;)91ChuMYRo;#%2V8;dVu_XQfpd&_vX8Ly_b={6iY4L6&m_3@#d6H)|C_dBUxCKqfsl2hD?b}|}OrH_'
    b'M<lqX<#5w`F0+F>(wW4>{C`i(;sO>88?G_MTmcx5gl>5cn?^-'
    b'F<bxL1AEC28ha{Q_M0xe)aqw50z<3KNxj^;gL=YsOVt&$tp&L<q$<k!w}mM3_>RRoWK(f>15}9~N@+!j98wKyRcnrCO_Jom*VY@U'
    b'<mX-RBaDJDo~e16m}w5}+oRawUnLTEdmSbeXH%r?WDnh9ovw^OdTR-'
    b')_p1Td2*+N_S3H>Rg&RO=(V3n$witMw(L2zOc>ixhgC$r!37WOLKbAoE|hnG`k?<T5V~jrLr4DjT{r#zVp?1S&TO+UKT`+nx;{>X'
    b'ct#>GzOc{xz!YXR~c__EqlSgBzvJmF)kM4bA)}4u+I_p`$yRCgg6h6t-'
    b'JJUTSZz`REN1}wftO`SBI%&wR&7uhbcHM(sXc~{C?q*IV?Vh#pkg2s|kyzoni4`;pqPbPJVAdJbTZ<96f?Ipr1EjcEaxzPqZX?J<'
    b')JAkENc7Qc${3o1Tj!65f*K?NE5*kyp{{+-'
    b'Eq&IEnlq%o*`A59I;H9uE8*WoeS+*h~B%Ng2X44}+A#6O=`iBNnC^Y1b803|?sluZ$RSPoMMR7o}P$Ov3UD;YSr8R#DC36BB<v?n'
    b'(l5)w@*@8EZT#;Kb_9ht-'
    b'y8xgc%RH_%Oe(1v$LN!_ct!a05hD&|<}1+mhhi*vQk>JyI9lzVJa)Qn~972|K1_}#STT<wetG0aOKqC##@EWA=9YCKOs>nx*J!Gv'
    b'Z%djGF!g%HMx9n2k4PO!)8T~g}Xqo+fP?FGfi_Vy@UO0uq`T1vtu)g4mR6p&U~=aMxJ;ov%)ue*am*7RThMK0%`6i<c!`a#a^Pij'
    b'SN&a3a$v$<9Ia8W({u*J`Z$KCPO=5m{r(2L19+}GmkF8{Up%&Tx<BkmIxcs$}>ig-'
    b'j(ltoz_BoV=B;uGqn%tJm4(k$^}QS2Qj8SxRp7?TWzy%4s+;~ocA@uU%Mk<Q|NcR1*iQ1av5n@hrV?8c!PxTWBlb8xSngX><IYdM'
    b'zRSI(>A=SuMN@@x-tu!+=`F(}e0umh;FQSc)X9kYxGv-'
    b'S0BSt8tg(8X&ol}~pl>*eodEqi%W1Reo{XH^KihTvwuKd#C8s3s<!Q&y4gEb?F{5B}5G2$tgaWu5z*5mq$98&aD8_SAuo@xt03{&'
    b'Z+-rF=|+wB55f)WS2+nGh#&&@$jHq~*(Ve&bHEw{KqieMYZK=V2mKZuvViYI8l*W}qKhhiw`=qzAW=udoh$R#RJ-'
    b'$=0^M?ADLX46*C}4#n%#dM=eSMBZCPxKrjf<l)<Ig6VsmDG>ilGU@~H>4V;1RtyO>day`tsANZ7kE(EAUvCo@YrDE)S`JvL9SUf}'
    b'N;X7t@~~2japEJAB9f6HM9gCm2`CE)MP8J7qIF>&<{^(f>P0bTam3P`h9veP;2^@iwTEon?(J{Vb9ElZU_vUouFk7cJ-'
    b'v7JOZCwIXy0Z1YA6_Kt=gMaSMcGCNZGL#V1~L@Z}yQcZqQpEtkoXsc&>WCDv~tlQM1K(KMk#3CBlx;6FK>3CMf0jq3U{a81RbXNt'
    b'0Pa2JRxF;!<ZNg6c6{ma6YD<Hkncqx!H6sDV(C-mFXYbq%6nTh$VLgI!$u#QBWN-oKH{fHj&C+PNyhT$NyMo-'
    b'$V=n471(mb&;v2<uO4@Z^Z})Vc6gkLOC^YP5^*reCA}dt<24t5M&e$w1xhy4cjH4>u7tRikNaM&7^9d;hKRm93)tDW%^B7roa^8U'
    b'Lu*;DcLU5jR1Ji%-'
    b'!6J9gZpRY&b57fI@yiD(NNb;E6EKr$CgZYu^hr5aF8+Qw^rRL8k4=coq4t~K2CN}QBK&RWaLmK*3TD@uJA5z@xK4{thIqpVPJe<w'
    b'~>NSRi$$oG@JGO?>xBVDnY(^t-meAg3M8hd3(B8xrTdsZe(3)-%u)OM7(2c>PIq)wF5ff6=RIvYyXLaCf6Q3LR?V>eD1#)g-'
    b';0S+5h;lK)doqLO;+u@Nqy+w=TXLr1;o>H43ZtukIIdnMzJw~|2YIYmI-L~uiv(##$b=pz`?3{)T(yU<iU8GE*?q(`-'
    b'UO&s#_(?JTXDtz}xl{i8gOc(gswGhsf=um;N*R3dUrPp6Ij^QhDW<kmb6ZxEd;i6^<xy1+bY)VtpL!L!R7p%c4pvj{aYFKd#-'
    b'ZmC7Vwn$KEpKUQ5rGgr+(_?$mc<t24NndfTT1hAwsQOs`L0h-`%@-'
    b'>pF8r%HdjlH41A*OMhdyIg#Z2M3S?Y?~3Upg(#Z4ZoJm~mZFg3)XK!S=^72@)lzgS7<WO==<^-'
    b'BAbPn$CvzSZIir>A0gG}|Atw_l*i$EJ^tto(r<eVd1c{BZvAD3_KEKFBc<^wJmxto&!%c&ob(+Rvq;ZSkI;?CCI1OetsT%EKrf4u'
    b'=m}{5!`DhF{IwU`xNJNdK(dS+0XbQ7C-'
    b'k}0R&6~|0T=exdBq+R6<uf|_4~R9{8ui#^b@ao#f#F&;xOOsSta!X$FHH2IV%xj`j?OEPsIP{ChPs~l4qoH_ws+lIBoxTz4T&g?T'
    b'8$Unw!T1d7{npG-Fr)emcmB5>5L7@e}{PeXnJQ3jh+iEEz1}6gWH25rVSd5H^KOq#Z1fZ8{VMXc(>W%4m-HZaJAc@P8-l-'
    b'``B#{x88f*At=8Yg8EQwidrn{7rm1IA{p>Yxl?}gErF=O9f;CDD|jq{;<pipDvnMuwW2#x-'
    b'$^aEn*z;;MWyUNnuAnxkm~9|D(Aj_t1&9r<?I=}4%s<N96~K8M34zAfgEo@eieT5T>?*COLE1y(<E`_i{da-'
    b'MmqLjyPxgj?&QAPe!gG%NY&A7b3X#UkHk_-lTa}8gq$jUqI>iI#t!<(-IYg-+x1z1v%5Xq-EOr;RJ#zS(^lKB+FuI>`)iufMatmM'
    b'VslyDwb0?N39Yhchuud0>r3$Jy)-'
    b'eQWi_MsUjmzNRv7kOu2}P#SK)biUW(H&PHF6=c_y4G&is_4jL<0cDb1oR1@DVyB=Ee9`FWBBzR&ZR`aWfr7IY^tdUm(Y+n}dAS;`'
    b'iy#+Z<2C5y1>j@Ce=sF}GDJz%Qp%eQx@tSp~vLCuL7b7IC@NzAxrPR10|amUUNnX^~Fw<OE&H6y4ps-BqexDJo&=gE|fvye7EAC#'
    b'*(H5MqU#+rSpC50uejM<CzhB@Xn#<(-uTO(yU(678XwA-'
    b'&HCa+ucU9t;WgH4D1V`HZGf|$iK`Q<V|4KpQ)YEm?^^;n<)7d90GBd==p#Pv}+$TH(FgT1`BjzkZr_C_xYmaFDWrI%m*>@)1&zQ#'
    b'^wg(Y}>cT=j-scox)4w74k_|6mPu(2l1_-+GiOwx<9q)+`x^f!KcOO9WW?E5ghP;BQ=-'
    b'W`~HCB)xhw_JnlYwVWV4L61VovX_VNmBHc(vj9JI~-Qif{Hsy9517xK;bXt@LX)JO~__S&|N#mIww2a;BG-'
    b'9*kxWQ=njRSc%4AMNBwvSW7{tiG(eFa+{J-'
    b'8*ieyS;%k5$Zutgw^Sj$N?67#<uCvY8?Qs43AP^S>VTV;M_^%`K)qiWF>vD$kMu+{@hB=g7AKNaZ)bFdbf+g)sGxl&%8+325xRmu'
    b')JyxouZXmY<fp)^5cC^-'
    b'I3Rx|?4qLS&%Hj$PwOoFe5pVTL+GvXvrf8xmulpKKI4rH}S2(r5mfP#Mz>>`sz2ATJXd&CGT_m(Ptj6nUn+elc(q%D`Wi^wfo{FP'
    b'YrvA1oeXH@vtH|EUi5CYb#S!v+A1ntNgc0*I9LJuQvMkQ?l=2k$0U|j`y(mI)lEoh5lzB<!r>*R*A^e@wwocrT&U`KS@rqV0g_Yu'
    b'(JN;dp*fnrb=8Ueh@*c!xn-#%_^<gSAHYge`%p?!Ty^4VtM6A1;LP!c%>>n?s@MPOh$4B+aVO5_-'
    b'e+P+Q|K|PlXMK+TS{|dH)G1Qg<H+nM5l2xF8$BgFTThA7OIjU8)sdD_t85-)4uzSvQU<fI<@kR0-'
    b'%L~we#9?_<NAwGlHe8K%_kw%9-'
    b'jucnxObuh`Ad^4hutLB0c_^meCBlTn}^^WUkih+t+tT54xhpw+wq;p@x=Zw@TK!45?(2d6HhY;}ta>uTC*&t-'
    b'Bp}dt9o<!DQU7p*N+BtIzLd|7iA)uHYXP_tf8rm!wZl>w@7*UC8CDDY!o-'
    b'&#&bK*)vaWY93E6KlcV%xk^o4yn0hgKpQ#rOg5((J1emal8u>}j`OGW@wUbOa&0q@Qsr^Jmj1S`rN<|k(FK~&wxyGrEv?u5u*J`Z'
    b'$KCPO#xC?cmc>LIk&EK%uFysEnO70JNC}O362{agUV?b$XAwmSq8alj#x&1!9P$|PF!yqvvnWA?FhatZc{xsU+Gm?v_&ZzXCvC?$'
    b'ZgJnZg?&lpsKuGLHH|)v6PT@~PvqSjpmg`Cyf=BxKABUZXHtxE^a;Itq@mHLbV^~v?<bIHU=q^`L|F(M?<(^~-'
    b'F2#3l1}h$cNdMLb7s=F-n(cVi!+}#J0fgaQJ`oVd@v~*4Pvr%Xui9dV($=r?SzkZBj~$d8Mii~zV^H|j#XT_nneGb=)pnWB--EHK'
    b'82(Nd?q51TNu@h2alFSV#5vVDI|^EF(`+mHR`#oJ`6A0?&bD)nN2Ux>18>*oTisCFsa397I&GYL+r?bcH9udYoOuNwp6T^f=#tMR'
    b'I5c7+I5jjd03?O+sPJ6y22bksdM!~A1iBoBYj`+r-*GxUeKMo%5`LOqR<?S_#T20#WASZrB=E+33Hy%)x!-'
    b'#nSQOfgR9QfeF{Zht2Mx+s$Y&6MEQ<FMw*%U3tp>Xhwc#J%+A>?Z!Mc8ZJK#MYaSIQo}AfFrPQ>VdYMdRDK3c@SL%&g1FtQerR=9'
    b'x_MI{&<GPG%lve1vklTLjbtJZ=BnT7i#Tm_f9Hm}Ja1`V?4|$N`EKdlIaS(?n;5bNA<nt7<EDmv+c|OaC!<Ovh^lVR_ygBCtm%Aj'
    b'm3|N*q$z?7{KEvScV$V;{U`uU}Q;W)!giRtIGgo?R7fHT(uXxjXn@IkV&Fq{5Ro4zw^?C%2`_8R>GALeEzQr7Toc8n$Ez_3rZLwU'
    b'Fhov|w#X;>jzV6^hW($54jp2(ngFjVkWb=vxug@zk`S~UzA=P#f+qLo@<d*reW?$u@039h$=KAotkc7oQwco1T<Jk{(`@!Ymmfoz'
    b'E!A&Iiph}Ods$;E%yL#XWKi4TMYO7Swn_t4?@@;kYtk#F({Sy1o-'
    b'WI3`zFA8x2<Ko`oKX;Jl&Rv2vM#c*1?1TEP4GQ9@5_?eb42L2{&|!07klbLB3>%@+K$M@E$)ZJhqSGz&wpDqx+RD_$0o7o&^9qIf'
    b'8^kkOI%N2VH%`O%H3JbF~RG{1ljM;0+6_!H+=^OenwH|sswK^jvII<daOSc%E0QnqFQZ&<NAq}oL0`q6Ndfx`>U-'
    b'|AZD~Ir?gaaTB=Do!n^9ruE=iviPM9+u&EaEtA##livpC9uIpi;Gj)|`tFvaSSuCoo*@Z4A555hIS(q{l;nT_=SHCHCWVyM;4_>z'
    b'Gf4msR{z7IIFAk4zgz^RXCe~`f*I$5KRVMGp1$|s^a-'
    b'ewu{@DK8V)t@{5n16o!7C*p@(3;zpY+++Q`7SnqbTQ1{zx6YliYJJ2~zO26O`v^g3};PXqFIyXdZhkrZn~8i6995lzAabk~sFlkk'
    b'K@XlQ<cW@@U;T-Tt{z$wG81ka^l5*?<l7QFV2Y-Z9wwe=npIJg0JyOTWtb15K>!dl3_b<5&9N&F>$vs5}a*BqlB-'
    b'u6UyS&`9sDceIzkt-b^**HYoYU%oZI1E**Ax$$K!AzPUpwFhc>*p~0B(LVvNkKK>#2)OoNRN*4`yXXcV4r-'
    b'P{61fIb>axHvD)}uR<M?U4>3K%5L$?s<e6H;KWG+la2ONksh^7+ndH3<n)$ZsK(sP=_ed~DiFVCFrFo*x=^p0uOTz6eSb=P1w@*L'
    b'C)grs<RGFhz+9%tgiJEM}jF!5kjgk5jQAKf)ks5ot7tT#%G7Q$#{>S;^-5!9a=TRBojopnj|yW;BsdZ-j}TBcQk-'
    b'z+hzh8yU<X}hlJDhWfcR1KArD^$MvL8UkLyCb89r%*ShD;1!ueDymnw1jwAKP7DHnwQdPeV4?RcDN?0l7NS2X>(4^5Z83pTRllPQ'
    b'S~RQwq0)&yf=>C8HfM)&_*B%V|%~b@mKBjnfy|)ijg27{NcM^J~a{$+`%bn$H4(5>l~gD4OrzN7~E#z4gjV;zZ0o$(*Q;0yra=B$'
    b'oD~3_57pSE*X@1R1K}iJS*+!a(U|N!|-;pivrYjwfa9`o&Q*@#h>IV|5YxC6{z)FK&`qJFD}Ku9i&#xX(=W(A*>d-'
    b'Usz$vt^nU$sq9Lp8<gv0B(>K{9WNAfvDID<lZRJh6l6IMXdLE262vUdf;9FbLSqb@-'
    b'}k8>r7TQC1jc$w;t=HtPP{Plc#I<!CWEZH_Hv&Bu*!N67vrX8aS1y>*MpqOU&1k^0{d)^C?KaVtUwqaY~MLCK=WC;VR-'
    b'*mp}($EKZAc00RMUxXoml0_;0R2ID>#Q2>9KCfcG^Qhr@sai;E5MZZ8G{Z{}9Kn-'
    b'Q`ZA$w~GStnF*DMn@vJ}OE!P#%qil}Wc!#SEk~S_97xcSg_rKJ@H=NmhLTPW8fPK?^=poKj{6Wnh17KfN6sO<#vovs>!vO$t#9dR'
    b'3ow4sQZm3lWa}Ajq>gBwiX)8l^tr1XCO{9)v7PVh?3mjJ@3BG|Fg_czziA3Fe9C<^CXJscQ=iM%i?ru}V|yK-'
    b'm<$U);HJ<{^%p$EYW2%VKQP2!~q=#Why_<X>&tVsWoSJqpK_vAn#YSyUJv{sZ;#2`?}deEE|$yY295Ymig&B<pm2U4y#XmSpL@aC'
    b'ob@=`bljBd8NVPzNv7jHS+4>hODfS~X~$H>o174ccaWb;eg`eD!R6bt*2y2?>`SBC1D3+z5TWxeGeuurm((=5W}7P}8M|Y%%btXz'
    b'T?t>pRG14Epd`RYLq{$)TSVgL;A4Py(~UgM4~oTjfv+lL(|5?9OkMvGCde+4_{0#+(cb$N|Du4|D;s?WbNveQ}aTnBa`DIEuqO3U'
    b'W%kB%%=^vB!b{2PE?Y9C;zlNRWDA%zX}q4fa#+MU3PQQ^w8jKD4vc#XBje;oRT`)Tx?n*#S?Hh*$^`fzBCa(PR-cp%g#@%O5>~Ib'
    b'Knq%li~k8H)hSs<hn82^?GK*LrJy`Bt#4p$BHhv+jatov=JJhBaT0oiRHnL#J0-'
    b'+Dh7J9o)gn5}Vu<C+A9tnnFEy5QhRjuRGXWb?pA7-weZeBAu@-_WX=XTpO1d>~Ynxh}LcyghzC^8+R(>-l1Q*<-'
    b'0>5H)X3sOupsv@Ih#UJbtZl>ZfYue=c{D73xUei=9>O+{)olEIhCYm50ZhPhzbfpM+)fi2W!QkM$fw@%!qdWi`R2n&A?r*g!ngkc'
    b'H<WSLomV^DoBfRKJ7=j$Kel`zaR`QuW<d&aFfMp7G(J4tepHM*7f$QQmo_A5wL|VB^Vv920nlcy=W|6I?VutPh}mwKBeLj<vztqH'
    b'T=$<N%wm>=V9*#pWD*LWMF|$F2RoHuzD<W6{dGB6BNtU?-'
    b');kLp9U({yaVec8$wqpV>je=pGsxpwkmWX~wIr^V03%IsgZdX1{TxmK%q>f^M!3sBC(Ebs#_@@SrTX%yuN&v8alLa86eagI@n6CC'
    b'is<7u8UFYs`d#~$(0B#+V-'
    b'3O4ZY^|#sk+iw4v?f<<>O8X5NQB|<c^w6x9xK?tr6!)KjPX)%Me*)(l3>M>8mS@Drg;L0?PVFlFt^TN#-'
    b'?{vo0niuOX26!B6+$h;&iuamnR-O(tl}-^uZ*w7ArgrI1^bKk3EHrFgmqZSa5-'
    b'P=@_#kivEIugF3;wZOtvcsGWsxx$(JJ<KUca)EW*oy9aaa-jR}|X(H#9Ntmf+Q%;>6Wh+MEmtn>%?>NiyCac%e&v^1iX4dpJ+me!'
    b'<gHZ~vD4;r<nUq5m=^w7B=OY!?v`TJ@qXVmgy)N=UJT&**BWrR!%vHY%T+nZARTHVp>if%$lb|zsX^Hr$o=}df5s{oE?QR#OYbb&'
    b't)<}wKK!e^KUSxw7tLgz@`1-ej7C<J6BT<i-+Y8t5yHvP}LDm}EsHbj6JR(<7qow6Erfj<2E`bqRJ3Vis-daM57)zVZ2^I?Py`+Z'
    b'G!pZ56qaZO8D#7qoTCZo=3t#@y!31!<9hi11~&CFY1%COI1?oZRvrIH#L?l2v(qwrlAbiEa+38EnUdP3w$S4bX>>CrPOMpeGXq|}'
    b'E-0?N%bi7r*UrzhFMa8lHaWeV2sMNUNM)My&*nu&Sgb5h6QCi5<?iQIjI7kJ-P4jg_4pP#MZ)UCM)p-'
    b'jX)*zJ!p7E#bQ*7m3Yq0^XqjigcMT?ctD#u_YRPKcv*!p7pO6&Jq(FlQNc8oaenSU706VDT;9Q3W8T$MK4`@i<{dRi?rLlcvdmR|'
    b'bs!8exz%FzK0XMFeH@O*2a{Zf|hNm}1cqdME%gp#(#fGEm$sK2tJ($61QEZo+FzrJ1u3ua|{5H2tZbe%Oi{TG9_?R9v%Ig;R6c=z'
    b'Gs<UFXXbMM;VM{pVer><+CtqhwuCs(M(d7S?fvRUBarOIV==>st|e2iR`KnCtkj9e?e?Kb!cY6aRDIZ#Mj^jz6{V9~)rf08A_hha'
    b'F*PKmtvd+~E?tT~dn=Y4_oJoGz#T)aAeQIvgFo!vNdeYHW8|$351m&7ABp=Q_+OBXzf~%k8PW52ng`-FdxfGq3j-'
    b'keELgqWiZ}a{ekg^nux%XJ_?<UU7=q*EgEXt0wpQ5_uKf9XY#Zo~?ekmY?g$qirYYwthSy3Ac1r>OXFN??}6?|7dukt^Qp-wRT$R'
    b'v3{P19!{A@gV;}b#ylnpii3vrGwLyxc_~7OG8EE;r8%WM3quwX#Iig~0<SMU*0!DRlNxLIiz`JH>&lXCKi-'
    b'=yTRiqEa%Ic&dU~F${^^_}JLw!*>&ct*WAB|G>sXdKH+IgAopWR7+}JrccFv8Rb7SY+*f}?L&W)XOW9Qu1IX8CBjh%C2=iJyiH+I'
    b'gAopWR7+}JrccFv8Rb7SY+*f}?LPHUahTHkV7t2GhmMk%fBchBjpb2{ss&N`>F9{MZMzM=HhtTTP}S1BbsQ&&Up{nkUa^i_}mD&I'
    b't;n8-'
    b'CS<dMu@+3lT~t>VD$wnnQvkxpbyNo}<~lNQlRq`QC)%kgHn752e~7n|ke&NjNYTQg(v#7^BwlE#T>vd1V1Vv;9G>}O%*hiMiE3FB'
    b'daxt}K)%@WQ@;*$u3rkBN8o_g5l!_pAhepxZS(M_WxC$TX@)v``Kv^eUrvO|)`^f>bCE2MVSXQTGe(%3{xy^C&?_qEWy|Ar-'
    b'SS@$6<oow@CY{zRRU7g0TAsJcP+HKjiKZ+ic8~hE()~h@;J3;N2j(2(Q-}^rr`)qJmRn<pzSQ8qwEOx^3i3w?Vcw9f%*iwDGx-Ex'
    b'{7k5Ji?N_4r@3VOI#}7aK>%S`f^CMsH52DZe^COlX-<tlY+yWuA{_ZWaKQ8|ZFaP`f@*{k%%{uKctdzxEZx?&w1bW@5_8d-'
    b'yfch8wtIV}F&p~aWmHNBw8mo7{&gE6KPhw^DQ7$y{Qr{S;EpPGVYQOt><5jL+{VEr_B>x6$ZCk7<Z87R&iySF;o_)vNXtxP#R#<V'
    b'0K4Gd2%PGBDBIr~%@TrNTlbc6<WrZQRSHG&T1&W`A*_mtDM8b&0C7x<049N+-'
    b'c5={Ecf|=wCa+=&x0B8%COl7zdu<F}`*AgQO&T{HAp3UL4}%Z&1m6usj`ZCh4I8y@LtY09Qb^7KJc#W-'
    b'luqU!B{PhBjDJxcrUNSKfr+NrqxpJQo;$#qlkPuXyQi~=dr&5wVev!RA_&eShz1cy6znYf6@%v4?+ypBOtwq}N{lZGOJTREeXP;f'
    b'W<;U?2@HE`+y35A<}ae%)o$~}yfbZ6`7gEm+l2}%aGU1$rI2esQ7m?GKUBu2%Ug9q-'
    b'748qL{kJ9sBV*&&kPtuH6}8C(Kj{sPaJb~|G+tU@ssM>clVNYJ!@Y+@r%B#)Oe<EUo{?gY}@9GJGTDBuC-'
    b'4ZPu9r@6*uAg&&V&fya5muKu8Ix+kYBVksTSd=^6pVeeomxTK!x7qm^-eR~~Eqbzx+)f4s=81aDu-'
    b'*g@$6sYrA6ktL*Lp40(%^Xt3V{DF4nI!=GShSLqx;rrc_o?`X5ptQJLUbET77s_tbM|>^9SbMRv4qz*pB_xb7nsUMNqayMvgL8#}'
    b'Sj1gx{)&up7DrL8w>Ww)&mt14!g0lCb!l2^sg=raQJ0z@U*HWZ)p-(V5Q1R8!jyu|1@GT8NibMdvO)knKt;#O-'
    b'To8aYOOEq$t_(!!!u&G;&IJky20zGw|Z~B>uArH=%;aszI%<Xb)$ZAO^&~>8}&-f5qwxrrir^j(ReAlO;g|s3Fyrsr;=*hq-'
    b'$iR4v1)-'
    b'JldpKIWPou85f5Kj?Nl%O8gui>A50HZ}qN=m(J;Wj5qQ`E`7Sl8|~(6?S)qoW41x3$lq~=TK!$um2IxEC&=W{C0z%fZ~V$@Evp$j'
    b')cIqbw}h1EZQRw_u<fVg<EmD<L<2PD*oJ(OLkK9m_rlTn;R*9Tl5ri$uU$u~5vu_r&1VA+IN@4R6Cb+JoS0OdrVgBXLW1B5%&(6$'
    b'#o0~px?wFKF{R=nb<+5xt}VAI8`)}}XiYOKls!e#CRMY=LfObR$h5c5w8{uIh?=VjT^(4Ri^<K!<mO^>b0w*{l2o}(j41m=Hm*U@'
    b'XtP!spK~>jyH@kCWG&9cHAXJ3(Uo#que8xh0<cuta8%K7zT~Wu8trhnH5}a?KX!$JJ3_I}*r_E9Y7ay9#SQHtKxYW9GiKHm<Qf#O'
    b'>Ipsdhkp8EHSVxWXV_z4oT4-'
    b'2&<FVs!RQBo>fQLb73;OZwmq<^6}Ge?kUa=s2Lk6tz&a7AZpf$uvT;KuosdO0#$fgFT|V{+<zFUH-'
    b'{#^<GHtWZYIc=&lD+K7tFCksdMDm&`MK0%*1IgIUG_xY?g8WMdAC{9Zz?BRG>hAJUTAr9l}>P+@*whPh*FkwmV`+{^E@RniE!d&S'
    b'rX=OzP$*ZO8pFFD9%t6a!N2xc#izO%=CiIOU37<POcY6Mr`0$SnZ@aBSp)y+&d?v<f;+gT6L3Q47zPSlj3e}C7dhMz9F-'
    b'93%Ww61Al~vAS+ag){cf+X}5E1uCIQOz^Z;WF8C^roE*?BCQ&Q{4Dg7--jREu8XZ5&IQ*F%+KZPI%DC(vSiPXU6y>ahe%!wdeUEg'
    b'vWcmQxeyg>sH17TMSNgn)L*L$L+MBOLoE~Amxq7~CN4+;!KWGW^ixeP#lBea5h4^qN_zvZ+CU2;mw{>52kcvI&&Z_a#u1l+y$DFr'
    b'TOX;tjw8QYTucW222JS4sO@XHfYKcin3}qWF97~n{X{|0;tqo_){8iaPwkC14g`i}Kek06AHueS5i@z3(`zVJlTuJj+;{N8B-'
    b'RI)&to~d1yGh-aoV-'
    b'n1NK?rx^B!O^a$(uYC#pNLwKlU_b*N6U#$7gH)QBA;?K}PE^7QE6ZN7mJ{vvP#Q=Y453k$c>(qJ5lD}W%b*{Zo;rKK#bh}vU9Lsm'
    b'POGO#6JS&f(TBV*guareC1urILNwZZuC&ggq9Ck7AhSIvT)-Mw#1K?x^z54JN^5@rYAiXp`!5wQ3lR|OusdSX~?t+#jkZ`f8H-'
    b'QAe)|6OI3u5|~{RJ`*g!27k;E#?2Ey>zwGol+NFNz&vpQ!Ta5CrH(3IZ{f1PbCdP5;NLdl}`)y_hgbsYb1>|Z#6o{PwUN8R=P&gc'
    b'sZ&0dQ#ckpySsfs4<z%cYFi`a`!yCcyTA-'
    b'3`|Y0`=4hUIRaQIoiBFvUPlsuH0~8e#=Rm`yI16Nu?{apgyeR@$1KuRnh&$#jhu@a@7IUVs}0_=+xK@u{r#OzolOHXx#22$j#V@%'
    b'>RihP=|g7@#H<uFV;E3FGTLnNVsJtARsF#RJ(a_+VBh-'
    b'^^N6>fq|ddvJ1N3Nep=K0?&Xl*nUv=joxOKwp6Hy7HM=_<&zs#h(M0CXgea6mp|^J?<%vBBn`8oq7|fSXcc(!X5?gPdUyiHe?lap'
    b'?f}Y*WaVi8o3mjK;V-o4E_a^1=c<=r4Rg@dNpNy@+&`~2DzySGeq#2e>0VgYrMzvk3Y^U;-'
    b'!qeCqp=;Ta>+o)%5mVv#XICn_bw|iM<jGqjrE{YE>51|RjJE}#n+fh^+eooP8`<vl>~%5btImQvB}?LioaG-'
    b'Y##!?ud`tf~@HW5mB*-*IJW6>+Qj&xT#VF3GpHQC0Q5>;^1uVh|V<hK!j8Kq;Ax{wJ8Hx~zQ4;o+=LHrQv7uL-'
    b'`DjjK&U!qVIdjJ2obfnkJbsTEkA8oz4v-'
    b'$hvmJex27j|Tj&2P)CpKO~On;YohSN0roXLeUEOf2JLjA*n{^NcvOi2BvmS|GW#V_h%S&mP`2}ZDLwLa*pr$XpjV_6quGtOy+S8X'
    b'cb-kEbQ;hlR4bS=%CKsYB5&IyEb0^!+pBMlQ`B6(H@Mc-Fm)7!}MY1@Gpin3xqU9968<4x+IkEUPd2;&@KoFj~LgmEx3IS`fXiz^'
    b'0gL{c$D)BXn0NDWBo37(2Xx)ebhjI=-b@#IM99RM~&Q=i}@^?96eKg>NA5|)NQaDsB;g*--'
    b't<$37wB*X!aJ)ff3!=aZFLUD)(0c@>x7yz#6y9^rc(&eF~`q#*hv}V-91`$OaDg8SnJD}=clyXQlq7-'
    b'PD+@1ol&GGY53CxmTRohHO(c#-'
    b'c*mR}UqrZQf$WwdCX4Gi{sFQ73u7x;F*&0{U;KG?T5AfOUVMAC<r1E%!su8Qeo09f^*`hAFK6qKh$T#!+=Bm0Um}&J=x>mt7sGP2'
    b'4bbAfmrkHU{4Ey1C9=`Tzac<k!T@EtnbyJ!V%C?IVx?B`(>%LtVMNjZd7e)VifQ!<2@>RGfG|W;Tqkyvv<q76l%F={^gF@mYPkBb'
    b'ehy<Ajjtuksz|Xu0M?vmKdCtN#OwcJVO0^CHT$HmT^ZNJdxYU2G*j|W}A|opo1$=hT;-'
    b'1y2R{Xa3S@DA>{QNAKdUzokhpvMEjYmy1xcFHa-BA8d{RcX^r8k5R7O`8#y=7;~*gUhdG#zKDwk%h6mI`?~$<W0dpSi%zaf;ljL}'
    b'afJ$h%TQ=-'
    b'OzL+9cz)fNp8cY0SMv)>!kuN7I{IhZ9{E_KXSK1QRg)A}c0P*T1J?0>$W^n1D^2S{0*9F?DGYQ<6J{vPHhy<(oqwxdlQqJGVMruN'
    b'#aA2Z9lQQX4>k5&!)E0m(J3*Z'
)
_TEST_RECORDS = json.loads(
    zlib.decompress(base64.b85decode(_TEST_RECORD_B85)).decode("utf-8")
)

BRANCHES = (
    ("candidate_acceptance", "governed", "author_candidate"),
    ("candidate_repair", "governed", "author_candidate"),
    ("attempt_selecting_replan", "governed", "author_candidate"),
    ("program_terminal_reject", "halt_only", None),
    ("post_execution_program_block", "halt_only", None),
)
ROLES = (
    "candidate_capsule", "worker_result", "validation_result", "independent_review",
    "standing_policy", "risk_lane", "authority_currentness_attestation", "global_stop",
    "effect_ceiling",
)
CURRENTNESS_COMPONENTS = ("validation", "review", "policy", "risk_profile", "risk_binding")
CURRENTNESS_PROFILES = (
    "post-execution-validation-result-set.v1",
    "post-execution-review-result-set.v1",
    "post-execution-standing-policy-source-attestation.v1",
    "post-execution-risk-source-profile.v1",
    "post-execution-risk-source-binding.v1",
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _digest(domain: str, value: object) -> str:
    return hashlib.sha256(domain.encode("utf-8") + b"\0" + _canonical(value)).hexdigest()


def _safe_name(value: str) -> str:
    return re_sub("[^0-9A-Za-z.-]", "-", value).strip("-")[:48] or "value"


def re_sub(pattern: str, replacement: str, value: str) -> str:
    # Kept local so these tests do not borrow implementation canonical helpers.
    import re
    return re.sub(pattern, replacement, value)


def _profile_for(v_number: str, variation: int) -> tuple[str, str] | None:
    if v_number in {"V09", "V10"}:
        ref = "post-execution-semantic-review-input.v2"
    elif v_number == "V13":
        ref = "validation-disposition.v1"
    elif v_number in {"V28", "V30"}:
        ref = CURRENTNESS_PROFILES[variation % len(CURRENTNESS_PROFILES)]
    else:
        pair = CLASS_BY_V[v_number]._PROFILE_PAIR
        if pair is None:
            return None
        return pair
    return ref, PROFILE_PAIRS[ref]


def _string_value(v_number: str, name: str, spec: dict[str, object], variation: int) -> str:
    if "constant" in spec:
        return str(spec["constant"])
    pair = _profile_for(v_number, variation)
    if name == "profile_ref" and pair is not None:
        return pair[0]
    if name == "profile_digest" and pair is not None:
        return pair[1]
    if "enum" in spec:
        return str(spec["enum"][0])
    if name == "base_git_object_format":
        return "sha1"
    if name == "base_git_oid":
        return "a" * 40
    if name.endswith("_digest"):
        return hashlib.sha256((v_number + ":" + name + ":" + str(variation)).encode()).hexdigest()
    if name in {"not_before", "source_invocation_started_at"}:
        return "2030-01-01T00:00:00Z"
    if name.endswith("_at") or name == "expires_at":
        return "2030-01-03T00:00:00Z" if name == "expires_at" else "2030-01-02T00:00:00Z"
    if name.endswith("_ref"):
        return f"{_safe_name(v_number)}-{_safe_name(name)}.{variation + 1}"
    if name.endswith("_schema_id") or name == "schema_id":
        return f"governed-execution.test-{_safe_name(v_number.lower())}-{_safe_name(name)}.v1"
    special = {
        "proposal_phase": "post_execution_semantic_review",
        "source_family": "versioned_external_risk_source",
        "risk_lane": "risk.standard",
        "required_risk_lane": "risk.standard",
        "model_recommendation": "accept_candidate",
        "mapped_branch": "candidate_acceptance",
        "authoritative_branch": "candidate_acceptance",
    }
    return special.get(name, "value")


def _matrix_entries(v_number: str) -> list[dict[str, object]]:
    governed = {
        "V17": ("permit", "policy_permits"),
        "V18": ("permit", "risk_lane_permits"),
        "V31": ("permit", "authority_verified_current"),
        "V32": ("permit", "global_stop_clear"),
        "V33": ("permit", "source_effect_within_current_ceilings"),
    }[v_number]
    halt_reason = {
        "V17": "halt_only_policy_not_applicable",
        "V18": "halt_only_risk_not_applicable",
        "V31": "halt_only_authority_not_applicable",
        "V32": "halt_only_stop_checked",
        "V33": "halt_only_ceiling_not_applicable",
    }[v_number]
    return [
        {
            "branch": branch,
            "applicability": applicability,
            "governed_effect_class": effect,
            "result": governed[0] if applicability == "governed" else "permit",
            "reason": governed[1] if applicability == "governed" else halt_reason,
        }
        for branch, applicability, effect in BRANCHES
    ]


def _assertion_entries(v_number: str) -> list[dict[str, object]]:
    reason = "policy_permits" if v_number == "V41" else "risk_lane_permits"
    halt = "halt_only_policy_not_applicable" if v_number == "V41" else "halt_only_risk_lane_not_applicable"
    schema = (
        "governed-execution.nwp-post-execution-standing-policy-branch-assertion.v1"
        if v_number == "V41"
        else "governed-execution.nwp-post-execution-risk-policy-branch-assertion.v1"
    )
    return [
        {
            "schema_id": schema,
            "branch": branch,
            "applicability": applicability,
            "governed_effect_class": effect,
            "result": "permit",
            "reason": reason if applicability == "governed" else halt,
        }
        for branch, applicability, effect in BRANCHES
    ]


def _list_value(v_number: str, name: str, spec: dict[str, object], variation: int) -> list[object]:
    if name == "entries" and v_number in {"V17", "V18", "V31", "V32", "V33"}:
        return _matrix_entries(v_number)
    if name == "branch_assertions":
        return _assertion_entries(v_number)
    if name == "allowed_branches":
        return [branch for branch, _, _ in BRANCHES]
    if name == "allowed_effect_classes" or name in {"attempt_allowed_effect_classes", "authority_allowed_effect_classes"}:
        return ["author_candidate"]
    if name == "allowed_risk_lanes":
        return ["risk.standard"]
    if name in {"source_evidence_refs", "result_set_evidence_refs", "support_canonical_values"}:
        return []
    nested_v = NESTED.get(v_number, {}).get(name)
    cardinality = int(spec.get("cardinality", 0))
    rule = spec.get("rule")
    if isinstance(rule, dict):
        cardinality = int(rule.get("minimum", cardinality))
    if nested_v is None:
        item_type = rule.get("item_type") if isinstance(rule, dict) else None
        return [f"item.{index + 1}" for index in range(cardinality)] if item_type else [{} for _ in range(cardinality)]
    return [_sample(nested_v, index) for index in range(cardinality)]


def _apply_variation(v_number: str, mapping: dict[str, object], variation: int) -> None:
    if v_number in {"V03", "V06", "V11"}:
        mapping["role"] = ROLES[variation % 9]
        mapping["role_rank"] = 5 + variation % 9
        mapping["ordinal"] = 0
    elif v_number == "V12":
        mapping["role"] = f"support-{variation + 1}"
        mapping["rank"] = variation + 1
        mapping["ordinal"] = 0
    elif v_number == "V16":
        branch, applicability, effect = BRANCHES[variation % 5]
        mapping.update(branch=branch, applicability=applicability, governed_effect_class=effect,
                       result="permit", reason="policy_permits" if applicability == "governed" else "halt_only_policy_not_applicable")
    elif v_number == "V23":
        mapping["evidence_role"] = ROLES[variation % 9]
        mapping["role_rank"] = 5 + variation % 9
        mapping["ordinal"] = 0
    elif v_number == "V26":
        mapping["kind_rank"] = variation + 1
        mapping["membership_ref"] = f"membership.{variation + 1}"
    elif v_number == "V28":
        mapping["role"] = CURRENTNESS_COMPONENTS[variation % 5]
    elif v_number == "V30":
        mapping["component"] = CURRENTNESS_COMPONENTS[variation % 5]
        mapping["result"] = "current"
        mapping["reason"] = "exact_ref_digest_profile_and_freshness"
    elif v_number == "V40.n01":
        mapping["ordinal"] = variation
        mapping["observation_kind"] = ("worker_started", "candidate_captured", "worker_completed")[variation % 3]


def _seal(v_number: str, mapping: dict[str, object]) -> dict[str, object]:
    identity = IDENTITY_SPECS[v_number]
    reference = identity["reference"]
    if reference.get("posture") in {"generated", "generated_and_owner_supplied_for_revalidation"}:
        preimage = {name: mapping[name] for name in reference["preimage_fields"]}
        mapping[reference["field"]] = reference["prefix"] + _digest(reference["domain"], preimage)
    digest = identity["digest"]
    if isinstance(digest.get("field"), str):
        exclusions = set(digest["self_exclusion"])
        preimage = {name: value for name, value in mapping.items() if name not in exclusions}
        mapping[digest["field"]] = _digest(digest["domain"], preimage)
    return mapping


_PRIMARY_FIXTURE_IDS = {
    "V01": "golden.V01.primary",
    "V02": "golden.V02.T1-input-context",
    "V04": "golden.V04.primary",
    "V05": "golden.V05.primary",
    "V07": "golden.V07.primary",
    "V08": "golden.V08.private-entry.000",
    "V09": "golden.V09.model-input-binding",
    "V10": "golden.V10.full-evidence-supply",
    "V13": "golden.V13.validation.support-set",
    "V14": "golden.V14.primary",
    "V15": "golden.V15.primary",
    "V17": "golden.V17.primary",
    "V18": "golden.V18.primary",
    "V19": "golden.V19.primary",
    "V20": "golden.V20.primary",
    "V21": "golden.V21.primary",
    "V22": "golden.V22.primary",
    "V25": "golden.V25.primary",
    "V27": "golden.V27.primary",
    "V29": "golden.V29.primary",
    "V31": "golden.V31.primary",
    "V32": "golden.V32.primary",
    "V33": "golden.V33.primary",
    "V34": "golden.V34.primary",
    "V38": "golden.V38.primary",
    "V39": "golden.V39.primary",
    "V40": "golden.V40.primary",
    "V41": "golden.V41.primary",
    "V42": "golden.V42.primary",
    "V43": "golden.V43.primary",
    "V44": "golden.V44.primary",
}


def _fixture_id(v_number: str, variation: int) -> str:
    indexed = {
        "V03": f"golden.V03.role-entry.{5 + variation % 9:02d}.{ROLES[variation % 9]}",
        "V06": f"golden.V06.projection-entry.{variation % 9:03d}",
        "V11": f"golden.V11.role-supply.{5 + variation % 9:02d}.{ROLES[variation % 9]}",
        "V12": f"golden.V12.validation.entry.{variation % 6:03d}",
        "V16": f"golden.V16.policy.entry.{variation % 5:03d}",
        "V23": f"golden.V23.projection-evidence.{variation % 9:03d}",
        "V24": f"golden.V24.role-resolution.{5 + variation % 9:02d}.{ROLES[variation % 9]}",
        "V26": f"golden.V26.closure-entry.{variation % 8:03d}",
        "V28": f"golden.V28.external-coordinate.{variation % 5:03d}",
        "V30": f"golden.V30.currentness-component.{variation % 5:03d}",
        "V40.n01": f"golden.V40.n01.author-observation-locator.{variation % 3:03d}",
        "V41.n01": f"golden.V41.n01.branch-assertion.{variation % 5:03d}",
        "V42.n01": f"golden.V42.n01.branch-assertion.{variation % 5:03d}",
    }
    if v_number == "V27" and variation:
        return "golden.V27.active-stop-control"
    if v_number == "V32" and variation:
        return "golden.V32.active-stop"
    if v_number in indexed:
        return indexed[v_number]
    return _PRIMARY_FIXTURE_IDS[v_number]


def _ordered_fixture(v_number: str, value: object) -> dict[str, object]:
    assert type(value) is dict
    source = typing_cast_dict(value)
    result: dict[str, object] = {}
    for spec in FIELD_SPECS[v_number]:
        name = str(spec["name"])
        member = deepcopy(source[name])
        nested_v = NESTED.get(v_number, {}).get(name)
        if nested_v is not None:
            if type(member) is list:
                member = [_ordered_fixture(nested_v, item) for item in member]
            else:
                member = _ordered_fixture(nested_v, member)
        result[name] = member
    return result


def typing_cast_dict(value: object) -> dict[str, object]:
    # The assertion in _ordered_fixture is the test-local exact-type gate.
    return value  # type: ignore[return-value]


def _sample(v_number: str, variation: int = 0) -> dict[str, object]:
    """Return an independently fixed accepted canonical value in declared order."""

    return _ordered_fixture(v_number, _TEST_RECORDS[_fixture_id(v_number, variation)])


def _reason(cls: type, mapping: object) -> str:
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        cls.from_mapping(mapping)
    assert caught.value.__cause__ is None
    return caught.value.reason


def test_exact_value_and_module_inventory() -> None:
    assert len(VALUE_INVENTORY) == 44
    assert set(CLASS_BY_V) == set(VALUE_INVENTORY)
    assert {v for v in CLASS_BY_V if v in {"V35", "V36", "V37", "V45"}} == set()
    for v_number, (module_name, symbol, fields) in VALUE_INVENTORY.items():
        cls = CLASS_BY_V[v_number]
        assert cls.__name__ == symbol
        assert cls.__module__.endswith(module_name)
        assert cls._FIELDS == fields
        assert cls._V_NUMBER == v_number
        assert cls.__all__ if hasattr(cls, "__all__") else True
    assert all(module.__all__ == () for module in MODULES.values())


@pytest.mark.parametrize("v_number", tuple(VALUE_INVENTORY))
def test_all_values_are_frozen_slotted_closed_and_round_trip(v_number: str) -> None:
    cls = CLASS_BY_V[v_number]
    mapping = _sample(v_number)
    value = cls.from_mapping(mapping)
    assert value.to_mapping() == mapping
    assert not hasattr(value, "__dict__")
    assert repr(value) == f"{cls.__name__}()"
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        setattr(value, cls._FIELDS[0], object())
    with pytest.raises(TypeError):
        copy(value)
    with pytest.raises(TypeError):
        deepcopy(value)
    with pytest.raises(TypeError):
        pickle.dumps(value)
    with pytest.raises(TypeError):
        type("Forbidden", (cls,), {})
    assert _reason(cls, {**mapping, "unknown": "hostile"}) == "unknown_field"
    missing = dict(mapping)
    missing.pop(cls._FIELDS[0])
    assert _reason(cls, missing) == "missing_field"
    assert _reason(cls, []) == "invalid_mapping"


@pytest.mark.parametrize("v_number", tuple(VALUE_INVENTORY))
def test_all_declared_scalar_types_and_nullability_are_exact(v_number: str) -> None:
    cls = CLASS_BY_V[v_number]
    mapping = _sample(v_number)
    for spec in FIELD_SPECS[v_number]:
        name = spec["name"]
        if spec["type"] in {"exact_builtin_int", "exact_builtin_int_bool_rejected"}:
            mutated = dict(mapping)
            mutated[name] = True
            assert _reason(cls, mutated) == "invalid_field_type"
            break
    nonnullable = next(spec for spec in FIELD_SPECS[v_number] if not spec.get("nullable") and spec["type"] != "exact_null")
    mutated = dict(mapping)
    mutated[nonnullable["name"]] = None
    assert _reason(cls, mutated) in {"invalid_field_type", "invalid_schema_id"}


def test_all_generated_references_and_self_digests_use_independent_test_code() -> None:
    for v_number, cls in CLASS_BY_V.items():
        mapping = _sample(v_number)
        value = cls.from_mapping(mapping)
        reference = IDENTITY_SPECS[v_number]["reference"]
        if reference.get("posture") in {"generated", "generated_and_owner_supplied_for_revalidation"}:
            preimage = {name: mapping[name] for name in reference["preimage_fields"]}
            expected_ref = reference["prefix"] + _digest(reference["domain"], preimage)
            assert mapping[reference["field"]] == expected_ref == value.computed_ref()
        digest = IDENTITY_SPECS[v_number]["digest"]
        if isinstance(digest.get("field"), str):
            preimage = {name: member for name, member in mapping.items() if name not in set(digest["self_exclusion"])}
            expected_digest = _digest(digest["domain"], preimage)
            assert mapping[digest["field"]] == expected_digest == value.computed_digest()


def test_all_profile_pairs_and_nwpf_behavior_runtime_distinction() -> None:
    assert len(PROFILE_PAIRS) == 28
    assert PROFILE_PAIRS["rw0-wire-nwpf-v1"] == "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454"
    assert (_NWPF_REF, _NWPF_DIGEST) == ("rw0-wire-nwpf-v1", PROFILE_PAIRS["rw0-wire-nwpf-v1"])
    accepted_behavior_record_digest = "891c3ffa26b33262763571ff60fcb6288240052d7f87319ca6d11c79f085f280"
    assert accepted_behavior_record_digest != _NWPF_DIGEST


def test_canonical_bytes_do_not_normalize_unicode() -> None:
    composed = {"value": "é"}
    decomposed = {"value": "é"}
    assert _canonical(composed) != _canonical(decomposed)
    assert _digest("test.domain", composed) != _digest("test.domain", decomposed)
    assert evidence._canonical_bytes(composed) == _canonical(composed)
    assert evidence._canonical_bytes(decomposed) == _canonical(decomposed)


PROPOSED_GOLDEN_RECORD_IDS = tuple(
    record_id
    for record_id in _TEST_RECORDS
    if re.match(r"golden\.V(?:\d+|(?:40|41|42)\.n01)(?:\.|$)", record_id)
)


def _golden_v_number(record_id: str) -> str:
    match = re.match(r"golden\.(V(?:40|41|42)\.n01|V\d+)(?:\.|$)", record_id)
    assert match is not None
    return match.group(1)


@pytest.mark.parametrize("record_id", PROPOSED_GOLDEN_RECORD_IDS)
def test_each_of_155_proposed_goldens_executes_its_concrete_value_contract(record_id: str) -> None:
    v_number = _golden_v_number(record_id)
    mapping = _ordered_fixture(v_number, _TEST_RECORDS[record_id])
    value = CLASS_BY_V[v_number].from_mapping(mapping)
    assert value.to_mapping() == mapping
    if isinstance(IDENTITY_SPECS[v_number]["digest"].get("field"), str):
        assert value.computed_digest() == mapping[IDENTITY_SPECS[v_number]["digest"]["field"]]


@pytest.mark.parametrize("v_number", tuple(VALUE_INVENTORY))
def test_every_outer_mapping_requires_declared_iteration_order(v_number: str) -> None:
    mapping = _sample(v_number)
    names = list(mapping)
    reordered = {name: mapping[name] for name in (*names[1:], names[0])}
    assert _reason(CLASS_BY_V[v_number], reordered) == "invalid_mapping"


@pytest.mark.parametrize("v_number", tuple(VALUE_INVENTORY))
def test_every_declared_scalar_and_container_field_has_an_exact_builtin_gate(v_number: str) -> None:
    cls = CLASS_BY_V[v_number]
    mapping = _sample(v_number)
    exercised = 0
    for spec in FIELD_SPECS[v_number]:
        name = str(spec["name"])
        field_type = spec["type"]
        mutated = dict(mapping)
        if field_type in {"exact_builtin_int", "exact_builtin_int_bool_rejected", "exact_builtin_int_bool_rejected_or_exact_null"}:
            mutated[name] = True
        elif field_type == "exact_builtin_bool":
            mutated[name] = 1
        elif field_type in {"exact_builtin_str", "exact_builtin_str_or_exact_null"}:
            mutated[name] = 7
        elif field_type in {"exact_builtin_dict", "exact_builtin_dict_or_exact_null"}:
            mutated[name] = []
        elif field_type == "exact_builtin_list":
            mutated[name] = tuple(typing_cast_dict(mapping)[name])
        elif field_type == "exact_null":
            mutated[name] = object()
        else:
            raise AssertionError((v_number, name, field_type))
        assert _reason(cls, mutated) == "invalid_field_type", (v_number, name)
        exercised += 1
    assert exercised == len(FIELD_SPECS[v_number])


def test_required_exact_grammar_probes_fail_before_identity_acceptance() -> None:
    tuple_list = _sample("V41")
    tuple_list["allowed_branches"] = tuple(tuple_list["allowed_branches"])
    tuple_list["attestation_ref"] = "wrong-parent.1"
    tuple_list["attestation_digest"] = "0" * 64
    assert _reason(CLASS_BY_V["V41"], tuple_list) == "invalid_field_type"

    long_ref = _sample("V01")
    long_ref["program_ref"] = "r" * 97
    long_ref["lineage_context_ref"] = "wrong-parent.1"
    long_ref["lineage_context_digest"] = "0" * 64
    assert _reason(CLASS_BY_V["V01"], long_ref) == "invalid_reference"

    non_enum = _sample("V41")
    non_enum["allowed_branches"] = [*non_enum["allowed_branches"][:-1], "not_a_branch"]
    non_enum["attestation_ref"] = "wrong-parent.1"
    non_enum["attestation_digest"] = "0" * 64
    assert _reason(CLASS_BY_V["V41"], non_enum) == "invalid_field_value"


BEHAVIOR_PROFILE_RECORD_IDS = tuple(
    record_id for record_id in _TEST_RECORDS if record_id.startswith("behavior-profile.")
)


@pytest.mark.parametrize("record_id", BEHAVIOR_PROFILE_RECORD_IDS)
def test_each_of_28_behavior_profiles_is_bound_to_live_value_or_current_nwpf_contract(record_id: str) -> None:
    payload = typing_cast_dict(_TEST_RECORDS[record_id])
    profile_ref = str(payload.get("profile_ref", record_id.removeprefix("behavior-profile.")))
    assert record_id == f"behavior-profile.{profile_ref}"
    profile_digest = PROFILE_PAIRS[profile_ref]
    assert re.fullmatch(r"[0-9a-f]{64}", profile_digest)
    bound_values = tuple(
        v_number for v_number, cls in CLASS_BY_V.items()
        if cls._PROFILE_PAIR == (profile_ref, profile_digest)
    )
    if profile_ref == "rw0-wire-nwpf-v1":
        assert (_NWPF_REF, _NWPF_DIGEST) == (profile_ref, profile_digest)
        return
    assert bound_values, profile_ref
    for v_number in bound_values:
        value = CLASS_BY_V[v_number].from_mapping(_sample(v_number))
        assert value._PROFILE_PAIR == (profile_ref, profile_digest)
        if "profile_ref" in value._FIELDS and v_number not in {"V09", "V10", "V13", "V28", "V30"}:
            invalid = value.to_mapping()
            invalid["profile_digest"] = "0" * 64
            assert _reason(CLASS_BY_V[v_number], invalid) == "invalid_profile_pair"
