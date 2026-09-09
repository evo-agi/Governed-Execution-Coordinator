from __future__ import annotations

import ast
import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = ROOT / ".docs" / "c2b-durable-development-state.md"
README_PATH = ROOT / "README.md"
AGENTS_PATH = ROOT / "AGENTS.md"
READER_STATUS_PATH = ROOT / ".docs" / "c2b2-private-readers.md"
INITIALIZATION_STATUS_PATH = ROOT / ".docs" / "c2b3-program-initialization.md"

SECTION_HEADING = "## 39. Coordinator C2B3C Author-Effect Contract Freeze"
BEGIN_MARKER = "<!-- COORDINATOR_C2B3C_AUTHOR_EFFECT_CONTRACT_BEGIN -->"
END_MARKER = "<!-- COORDINATOR_C2B3C_AUTHOR_EFFECT_CONTRACT_END -->"
INITIALIZATION_STATUS_BEGIN = (
    "<!-- COORDINATOR_VS1B_IMPLEMENTED_CURRENT_STATUS_BEGIN -->"
)
INITIALIZATION_STATUS_END = "<!-- COORDINATOR_VS1B_IMPLEMENTED_CURRENT_STATUS_END -->"
EXPECTED_SECTION_39_PROLOGUE = """## 39. Coordinator C2B3C Author-Effect Contract Freeze

Classification: `ACCEPTED TARGET CONTRACT`; documentation and finite direct
contract test only. This section is the sole semantic owner of the C2B3C
author-effect establishment contract. It finitely supersedes stale current-
status projections in earlier sections without changing their tranche-time
evidence or any byte in Sections 1 through 38.

VS1B is the current committed private implementation at
`327aa4ef6f043a94f700374546fedc456027ae83` and is pushed to the directly
verified `origin/trunk_dev` ref. The exact VS1B pre-commit candidate received
externally classified, provenance-bound independent acceptance and its
post-acceptance commit gate passed. Git owns the commit/ref fact; the audit and
validation reports remain external evidence rather than Coordinator durable
authority. C2B3C is currently an uncommitted contract-freeze candidate awaiting
fresh independent re-audit. C2B3D source, worker execution, and production or
external effects remain unauthorized.

<!-- COORDINATOR_C2B3C_AUTHOR_EFFECT_CONTRACT_BEGIN -->

```python
"""
EXPECTED_TRAILING_PROSE = """

The pending authority evaluation, AttemptFence, EffectFence, WorkerCommand,
and planned delivery are durable intent and bounds only. They are not execution
permission. No C2B3D source may begin until this exact contract receives fresh
independent acceptance and a separately authorized source-implementation
prompt.
"""
EXPECTED_SECTION_39_PAYLOAD_UTF8_LENGTH = 332446
EXPECTED_SECTION_39_PAYLOAD_SHA256 = (
    "a0689ec37b3e764e463cedbb5d38ece0c57f6ed2fba1db570c667a55c52b571d"
)

EXPECTED_FAMILY_GOLDEN_VECTOR = {'vector_id': 'c2b3c-author-effect-family-v1',
 'vector_version': 1,
 'transaction_timestamp': '2026-08-22T12:34:56Z',
 'expires_at': '2026-08-22T13:34:56Z',
 'inputs': {'committed_vs1b_genesis_basis': {'program_ref': 'program-c2b3a-1',
                                             'program_version_ref': 'program-version-c2b3a-1',
                                             'program_version_number': 1,
                                             'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                             'work_item_ref': 'work-item-c2b3a-1',
                                             'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                             'basis_decision_ref': 'decision-c2b3a-1',
                                             'basis_decision_digest': 'e743c359aea93d7931250552b62bc741d84c490f9ebb68e071c8616cc5fb4b96',
                                             'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                             'candidate_ref': 'candidate-c2b3a-1',
                                             'attempt_number': 1,
                                             'repository_ref': 'repository-c2b3a-1',
                                             'base_git_object_format': 'sha1',
                                             'base_git_oid': '2222222222222222222222222222222222222222',
                                             'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                  'PLANS.md',
                                                                  'docs_contract_test.go'),
                                             'work_spec_ref': 'work-spec-c2b3a-1',
                                             'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                             'work_spec_safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab',
                                             'validation_requirement_ref': 'validation-c2b3a-1',
                                             'review_requirement_ref': 'review-c2b3a-1'},
            'preassigned_author_effect_refs': {'mutation_ref': 'mutation-c2b3c-1',
                                               'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                               'effect_intent_ref': 'effect-intent-c2b3c-1',
                                               'effect_fence_ref': 'effect-fence-c2b3c-1',
                                               'command_ref': 'command-c2b3c-1',
                                               'authority_evaluation_ref': 'authority-evaluation-c2b3c-1',
                                               'delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                               'adapter_safe_correlation_ref': 'adapter-correlation-c2b3c-1'},
            'standing_and_subordinate_authority': {'standing_grant_ref': 'standing-grant-c2b3c-1',
                                                   'standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                   'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                                   'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                                   'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                   'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555'},
            'requirement_evidence': {'validation': {'schema_id': 'governed-execution.nwp-development-validation-requirement-evidence.v1',
                                                    'requirement_ref': 'validation-c2b3a-1',
                                                    'requirement_digest': '6666666666666666666666666666666666666666666666666666666666666666',
                                                    'work_spec_ref': 'work-spec-c2b3a-1',
                                                    'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                    'safe_evidence_digest': 'bfd4be05ab68440c4402fdaa770fdbdbbec72f73962be77b8ef9d342ece9a5ea'},
                                     'review': {'schema_id': 'governed-execution.nwp-development-review-requirement-evidence.v1',
                                                'requirement_ref': 'review-c2b3a-1',
                                                'requirement_digest': '7777777777777777777777777777777777777777777777777777777777777777',
                                                'work_spec_ref': 'work-spec-c2b3a-1',
                                                'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                'safe_evidence_digest': '3a6ffa9bdb8b5e71d0deeb0d90e8d087aeb66ae92849690cae779efbdd6eb9f7'}},
            'coding_global_stop': {'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                   'global_stop_version': 0},
            'profile_references': {'capsule_profile_ref': 'capsule-profile.regular-replace-v1',
                                   'redaction_profile_ref': 'redaction.source-private-v1'},
            'allowed_effect_classes': ('author_candidate',
                                       'cancel_effect',
                                       'local_git_commit',
                                       'review_candidate',
                                       'validate_candidate'),
            'attempt_aggregate_ceilings': {'max_active_invocations': 1,
                                           'max_candidate_bytes': 1048576,
                                           'max_changed_files': 3,
                                           'max_cost_microusd': 100000,
                                           'max_cpu_seconds': 600,
                                           'max_deliveries': 3,
                                           'max_deployments': 0,
                                           'max_local_commits': 1,
                                           'max_memory_bytes': 2147483648,
                                           'max_merges': 0,
                                           'max_model_input_tokens': 200000,
                                           'max_model_output_tokens': 50000,
                                           'max_pull_requests': 0,
                                           'max_pushes': 0,
                                           'max_wall_seconds': 1800},
            'author_effect_ceilings': {'max_active_invocations': 1,
                                       'max_candidate_bytes': 1048576,
                                       'max_changed_files': 3,
                                       'max_cost_microusd': 100000,
                                       'max_cpu_seconds': 600,
                                       'max_deliveries': 1,
                                       'max_deployments': 0,
                                       'max_local_commits': 0,
                                       'max_memory_bytes': 2147483648,
                                       'max_merges': 0,
                                       'max_model_input_tokens': 200000,
                                       'max_model_output_tokens': 50000,
                                       'max_pull_requests': 0,
                                       'max_pushes': 0,
                                       'max_wall_seconds': 1800},
            'nullable_values': {'portable_capsule_digest': None,
                                'cancellation_target_effect_intent_ref': None,
                                'expected_target_effect_head_revision': None,
                                'cancellation_target_effect_fence_ref': None,
                                'cancellation_target_effect_fence_digest': None,
                                'predecessor_delivery_attempt_ref': None,
                                'authority_evaluation_expires_at': None}},
 'canonical_values': {'work_spec_safe_projection': {'complete_mapping': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                                         'work_spec_ref': 'work-spec-c2b3a-1',
                                                                         'program_ref': 'program-c2b3a-1',
                                                                         'program_version_ref': 'program-version-c2b3a-1',
                                                                         'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                         'work_item_ref': 'work-item-c2b3a-1',
                                                                         'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                         'repository_ref': 'repository-c2b3a-1',
                                                                         'base_git_object_format': 'sha1',
                                                                         'base_git_oid': '2222222222222222222222222222222222222222',
                                                                         'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                              'PLANS.md',
                                                                                              'docs_contract_test.go'),
                                                                         'validation_requirement_ref': 'validation-c2b3a-1',
                                                                         'review_requirement_ref': 'review-c2b3a-1',
                                                                         'privacy_classification': 'private_work_spec',
                                                                         'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                         'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
                                                    'identity_excludes': ('safe_projection_digest',),
                                                    'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                                                   'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                   'program_ref': 'program-c2b3a-1',
                                                                                   'program_version_ref': 'program-version-c2b3a-1',
                                                                                   'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                   'work_item_ref': 'work-item-c2b3a-1',
                                                                                   'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                   'repository_ref': 'repository-c2b3a-1',
                                                                                   'base_git_object_format': 'sha1',
                                                                                   'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                   'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                        'PLANS.md',
                                                                                                        'docs_contract_test.go'),
                                                                                   'validation_requirement_ref': 'validation-c2b3a-1',
                                                                                   'review_requirement_ref': 'review-c2b3a-1',
                                                                                   'privacy_classification': 'private_work_spec',
                                                                                   'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c'},
                                                    'canonical_json': '{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","authorized_paths":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"base_git_object_format":"sha1","base_git_oid":"2222222222222222222222222222222222222222","privacy_classification":"private_work_spec","program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","repository_ref":"repository-c2b3a-1","review_requirement_ref":"review-c2b3a-1","schema_id":"governed-execution.nwp-development-work-spec-safe-projection.v1","validation_requirement_ref":"validation-c2b3a-1","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1","work_spec_digest":"2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c","work_spec_ref":"work-spec-c2b3a-1"}',
                                                    'utf8_length': 812,
                                                    'digest_domain': 'governed-execution.nwp-development-work-spec-safe-projection.v1.identity',
                                                    'digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
                      'validation_requirement_evidence': {'complete_mapping': {'schema_id': 'governed-execution.nwp-development-validation-requirement-evidence.v1',
                                                                               'requirement_ref': 'validation-c2b3a-1',
                                                                               'requirement_digest': '6666666666666666666666666666666666666666666666666666666666666666',
                                                                               'work_spec_ref': 'work-spec-c2b3a-1',
                                                                               'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                               'safe_evidence_digest': 'bfd4be05ab68440c4402fdaa770fdbdbbec72f73962be77b8ef9d342ece9a5ea'},
                                                          'identity_excludes': ('safe_evidence_digest',),
                                                          'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-development-validation-requirement-evidence.v1',
                                                                                         'requirement_ref': 'validation-c2b3a-1',
                                                                                         'requirement_digest': '6666666666666666666666666666666666666666666666666666666666666666',
                                                                                         'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                         'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c'},
                                                          'canonical_json': '{"requirement_digest":"6666666666666666666666666666666666666666666666666666666666666666","requirement_ref":"validation-c2b3a-1","schema_id":"governed-execution.nwp-development-validation-requirement-evidence.v1","work_spec_digest":"2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c","work_spec_ref":"work-spec-c2b3a-1"}',
                                                          'utf8_length': 334,
                                                          'digest_domain': 'governed-execution.nwp-development-validation-requirement-evidence.v1.identity',
                                                          'digest': 'bfd4be05ab68440c4402fdaa770fdbdbbec72f73962be77b8ef9d342ece9a5ea'},
                      'review_requirement_evidence': {'complete_mapping': {'schema_id': 'governed-execution.nwp-development-review-requirement-evidence.v1',
                                                                           'requirement_ref': 'review-c2b3a-1',
                                                                           'requirement_digest': '7777777777777777777777777777777777777777777777777777777777777777',
                                                                           'work_spec_ref': 'work-spec-c2b3a-1',
                                                                           'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                           'safe_evidence_digest': '3a6ffa9bdb8b5e71d0deeb0d90e8d087aeb66ae92849690cae779efbdd6eb9f7'},
                                                      'identity_excludes': ('safe_evidence_digest',),
                                                      'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-development-review-requirement-evidence.v1',
                                                                                     'requirement_ref': 'review-c2b3a-1',
                                                                                     'requirement_digest': '7777777777777777777777777777777777777777777777777777777777777777',
                                                                                     'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                     'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c'},
                                                      'canonical_json': '{"requirement_digest":"7777777777777777777777777777777777777777777777777777777777777777","requirement_ref":"review-c2b3a-1","schema_id":"governed-execution.nwp-development-review-requirement-evidence.v1","work_spec_digest":"2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c","work_spec_ref":"work-spec-c2b3a-1"}',
                                                      'utf8_length': 326,
                                                      'digest_domain': 'governed-execution.nwp-development-review-requirement-evidence.v1.identity',
                                                      'digest': '3a6ffa9bdb8b5e71d0deeb0d90e8d087aeb66ae92849690cae779efbdd6eb9f7'},
                      'attempt_fence': {'complete_mapping': {'schema_id': 'governed-execution.nwp-attempt-fence.v1',
                                                             'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                             'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                             'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                             'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                                             'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                                             'program_ref': 'program-c2b3a-1',
                                                             'program_version_ref': 'program-version-c2b3a-1',
                                                             'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                             'work_item_ref': 'work-item-c2b3a-1',
                                                             'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                             'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                             'repository_ref': 'repository-c2b3a-1',
                                                             'base_git_object_format': 'sha1',
                                                             'base_git_oid': '2222222222222222222222222222222222222222',
                                                             'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                              'PLANS.md',
                                                                              'docs_contract_test.go'],
                                                             'allowed_effect_classes': ['author_candidate',
                                                                                        'cancel_effect',
                                                                                        'local_git_commit',
                                                                                        'review_candidate',
                                                                                        'validate_candidate'],
                                                             'aggregate_ceilings': {'max_active_invocations': 1,
                                                                                    'max_candidate_bytes': 1048576,
                                                                                    'max_changed_files': 3,
                                                                                    'max_cost_microusd': 100000,
                                                                                    'max_cpu_seconds': 600,
                                                                                    'max_deliveries': 3,
                                                                                    'max_deployments': 0,
                                                                                    'max_local_commits': 1,
                                                                                    'max_memory_bytes': 2147483648,
                                                                                    'max_merges': 0,
                                                                                    'max_model_input_tokens': 200000,
                                                                                    'max_model_output_tokens': 50000,
                                                                                    'max_pull_requests': 0,
                                                                                    'max_pushes': 0,
                                                                                    'max_wall_seconds': 1800},
                                                             'expires_at': '2026-08-22T13:34:56Z',
                                                             'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                             'global_stop_version': 0,
                                                             'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed'},
                                        'identity_excludes': ('attempt_fence_digest',),
                                        'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-attempt-fence.v1',
                                                                       'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                       'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                       'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                       'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                                                       'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                                                       'program_ref': 'program-c2b3a-1',
                                                                       'program_version_ref': 'program-version-c2b3a-1',
                                                                       'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                       'work_item_ref': 'work-item-c2b3a-1',
                                                                       'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                       'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                       'repository_ref': 'repository-c2b3a-1',
                                                                       'base_git_object_format': 'sha1',
                                                                       'base_git_oid': '2222222222222222222222222222222222222222',
                                                                       'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                        'PLANS.md',
                                                                                        'docs_contract_test.go'],
                                                                       'allowed_effect_classes': ['author_candidate',
                                                                                                  'cancel_effect',
                                                                                                  'local_git_commit',
                                                                                                  'review_candidate',
                                                                                                  'validate_candidate'],
                                                                       'aggregate_ceilings': {'max_active_invocations': 1,
                                                                                              'max_candidate_bytes': 1048576,
                                                                                              'max_changed_files': 3,
                                                                                              'max_cost_microusd': 100000,
                                                                                              'max_cpu_seconds': 600,
                                                                                              'max_deliveries': 3,
                                                                                              'max_deployments': 0,
                                                                                              'max_local_commits': 1,
                                                                                              'max_memory_bytes': 2147483648,
                                                                                              'max_merges': 0,
                                                                                              'max_model_input_tokens': 200000,
                                                                                              'max_model_output_tokens': 50000,
                                                                                              'max_pull_requests': 0,
                                                                                              'max_pushes': 0,
                                                                                              'max_wall_seconds': 1800},
                                                                       'expires_at': '2026-08-22T13:34:56Z',
                                                                       'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                       'global_stop_version': 0},
                                        'canonical_json': '{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","aggregate_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":100000,"max_cpu_seconds":600,"max_deliveries":3,"max_deployments":0,"max_local_commits":1,"max_memory_bytes":2147483648,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":1800},"allowed_effect_classes":["author_candidate","cancel_effect","local_git_commit","review_candidate","validate_candidate"],"attempt_authorization_digest":"4444444444444444444444444444444444444444444444444444444444444444","attempt_authorization_ref":"attempt-authorization-c2b3c-1","attempt_fence_ref":"attempt-fence-c2b3c-1","base_git_object_format":"sha1","base_git_oid":"2222222222222222222222222222222222222222","expires_at":"2026-08-22T13:34:56Z","global_stop_ref":"coding-global-stop-c2b3a-1","global_stop_version":0,"parent_standing_grant_digest":"3333333333333333333333333333333333333333333333333333333333333333","parent_standing_grant_ref":"standing-grant-c2b3c-1","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","repository_ref":"repository-c2b3a-1","schema_id":"governed-execution.nwp-attempt-fence.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1"}',
                                        'utf8_length': 1538,
                                        'digest_domain': 'governed-execution.nwp-attempt-fence.v1.identity',
                                        'digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed'},
                      'effect_authorization_safe_binding': {'complete_mapping': {'schema_id': 'governed-execution.nwp-development-effect-authorization-safe-binding.v1',
                                                                                 'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                                 'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                                 'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                                 'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                                 'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                 'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                                 'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                 'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                 'effect_class': 'author_candidate',
                                                                                 'path_ceiling': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                  'PLANS.md',
                                                                                                  'docs_contract_test.go'),
                                                                                 'effect_ceilings': {'max_active_invocations': 1,
                                                                                                     'max_candidate_bytes': 1048576,
                                                                                                     'max_changed_files': 3,
                                                                                                     'max_cost_microusd': 100000,
                                                                                                     'max_cpu_seconds': 600,
                                                                                                     'max_deliveries': 1,
                                                                                                     'max_deployments': 0,
                                                                                                     'max_local_commits': 0,
                                                                                                     'max_memory_bytes': 2147483648,
                                                                                                     'max_merges': 0,
                                                                                                     'max_model_input_tokens': 200000,
                                                                                                     'max_model_output_tokens': 50000,
                                                                                                     'max_pull_requests': 0,
                                                                                                     'max_pushes': 0,
                                                                                                     'max_wall_seconds': 1800},
                                                                                 'expires_at': '2026-08-22T13:34:56Z',
                                                                                 'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                                 'global_stop_version': 0,
                                                                                 'safe_binding_digest': 'afa53c667dc36b2d797ab2a9ed94c46e1012a19352120b892e631a5e43e03868'},
                                                            'identity_excludes': ('safe_binding_digest',),
                                                            'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-development-effect-authorization-safe-binding.v1',
                                                                                           'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                                           'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                                           'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                                           'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                                           'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                           'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                                           'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                           'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                           'effect_class': 'author_candidate',
                                                                                           'path_ceiling': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                            'PLANS.md',
                                                                                                            'docs_contract_test.go'),
                                                                                           'effect_ceilings': {'max_active_invocations': 1,
                                                                                                               'max_candidate_bytes': 1048576,
                                                                                                               'max_changed_files': 3,
                                                                                                               'max_cost_microusd': 100000,
                                                                                                               'max_cpu_seconds': 600,
                                                                                                               'max_deliveries': 1,
                                                                                                               'max_deployments': 0,
                                                                                                               'max_local_commits': 0,
                                                                                                               'max_memory_bytes': 2147483648,
                                                                                                               'max_merges': 0,
                                                                                                               'max_model_input_tokens': 200000,
                                                                                                               'max_model_output_tokens': 50000,
                                                                                                               'max_pull_requests': 0,
                                                                                                               'max_pushes': 0,
                                                                                                               'max_wall_seconds': 1800},
                                                                                           'expires_at': '2026-08-22T13:34:56Z',
                                                                                           'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                                           'global_stop_version': 0},
                                                            'canonical_json': '{"attempt_fence_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","attempt_fence_ref":"attempt-fence-c2b3c-1","effect_authorization_digest":"5555555555555555555555555555555555555555555555555555555555555555","effect_authorization_ref":"effect-authorization-c2b3c-1","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":100000,"max_cpu_seconds":600,"max_deliveries":1,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":2147483648,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":1800},"effect_class":"author_candidate","effect_intent_ref":"effect-intent-c2b3c-1","expires_at":"2026-08-22T13:34:56Z","global_stop_ref":"coding-global-stop-c2b3a-1","global_stop_version":0,"parent_standing_grant_digest":"3333333333333333333333333333333333333333333333333333333333333333","parent_standing_grant_ref":"standing-grant-c2b3c-1","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"schema_id":"governed-execution.nwp-development-effect-authorization-safe-binding.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1"}',
                                                            'utf8_length': 1256,
                                                            'digest_domain': 'governed-execution.nwp-development-effect-authorization-safe-binding.v1.identity',
                                                            'digest': 'afa53c667dc36b2d797ab2a9ed94c46e1012a19352120b892e631a5e43e03868'},
                      'worker_command_identity_without_effect_fence_digest': {'complete_mapping': {'schema_id': 'governed-execution.nwp-worker-command.v1',
                                                                                                   'command_ref': 'command-c2b3c-1',
                                                                                                   'program_ref': 'program-c2b3a-1',
                                                                                                   'program_version_ref': 'program-version-c2b3a-1',
                                                                                                   'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                                   'work_item_ref': 'work-item-c2b3a-1',
                                                                                                   'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                                   'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                                   'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                                   'effect_class': 'author_candidate',
                                                                                                   'candidate_ref': 'candidate-c2b3a-1',
                                                                                                   'repository_ref': 'repository-c2b3a-1',
                                                                                                   'base_git_object_format': 'sha1',
                                                                                                   'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                                   'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                                    'PLANS.md',
                                                                                                                    'docs_contract_test.go'],
                                                                                                   'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                                   'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                                   'standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                                                   'standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                                                   'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                                                                                   'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                                                                                   'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                                                   'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                                                   'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                                   'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                                                   'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                                                   'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                                                   'global_stop_version': 0,
                                                                                                   'validation_requirement_ref': 'validation-c2b3a-1',
                                                                                                   'validation_requirement_digest': '6666666666666666666666666666666666666666666666666666666666666666',
                                                                                                   'review_requirement_ref': 'review-c2b3a-1',
                                                                                                   'review_requirement_digest': '7777777777777777777777777777777777777777777777777777777777777777',
                                                                                                   'capsule_schema_id': 'governed-execution.nwp-candidate-capsule-manifest.v1',
                                                                                                   'capsule_profile_ref': 'capsule-profile.regular-replace-v1',
                                                                                                   'effect_ceilings': {'max_active_invocations': 1,
                                                                                                                       'max_candidate_bytes': 1048576,
                                                                                                                       'max_changed_files': 3,
                                                                                                                       'max_cost_microusd': 100000,
                                                                                                                       'max_cpu_seconds': 600,
                                                                                                                       'max_deliveries': 1,
                                                                                                                       'max_deployments': 0,
                                                                                                                       'max_local_commits': 0,
                                                                                                                       'max_memory_bytes': 2147483648,
                                                                                                                       'max_merges': 0,
                                                                                                                       'max_model_input_tokens': 200000,
                                                                                                                       'max_model_output_tokens': 50000,
                                                                                                                       'max_pull_requests': 0,
                                                                                                                       'max_pushes': 0,
                                                                                                                       'max_wall_seconds': 1800},
                                                                                                   'privacy_classification': 'private_source_change',
                                                                                                   'redaction_profile_ref': 'redaction.source-private-v1'},
                                                                              'identity_excludes': ('effect_fence_digest',
                                                                                                    'command_digest'),
                                                                              'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-worker-command.v1',
                                                                                                             'command_ref': 'command-c2b3c-1',
                                                                                                             'program_ref': 'program-c2b3a-1',
                                                                                                             'program_version_ref': 'program-version-c2b3a-1',
                                                                                                             'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                                             'work_item_ref': 'work-item-c2b3a-1',
                                                                                                             'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                                             'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                                             'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                                             'effect_class': 'author_candidate',
                                                                                                             'candidate_ref': 'candidate-c2b3a-1',
                                                                                                             'repository_ref': 'repository-c2b3a-1',
                                                                                                             'base_git_object_format': 'sha1',
                                                                                                             'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                                             'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                                              'PLANS.md',
                                                                                                                              'docs_contract_test.go'],
                                                                                                             'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                                             'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                                             'standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                                                             'standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                                                             'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                                                                                             'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                                                                                             'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                                                             'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                                                             'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                                             'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                                                             'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                                                             'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                                                             'global_stop_version': 0,
                                                                                                             'validation_requirement_ref': 'validation-c2b3a-1',
                                                                                                             'validation_requirement_digest': '6666666666666666666666666666666666666666666666666666666666666666',
                                                                                                             'review_requirement_ref': 'review-c2b3a-1',
                                                                                                             'review_requirement_digest': '7777777777777777777777777777777777777777777777777777777777777777',
                                                                                                             'capsule_schema_id': 'governed-execution.nwp-candidate-capsule-manifest.v1',
                                                                                                             'capsule_profile_ref': 'capsule-profile.regular-replace-v1',
                                                                                                             'effect_ceilings': {'max_active_invocations': 1,
                                                                                                                                 'max_candidate_bytes': 1048576,
                                                                                                                                 'max_changed_files': 3,
                                                                                                                                 'max_cost_microusd': 100000,
                                                                                                                                 'max_cpu_seconds': 600,
                                                                                                                                 'max_deliveries': 1,
                                                                                                                                 'max_deployments': 0,
                                                                                                                                 'max_local_commits': 0,
                                                                                                                                 'max_memory_bytes': 2147483648,
                                                                                                                                 'max_merges': 0,
                                                                                                                                 'max_model_input_tokens': 200000,
                                                                                                                                 'max_model_output_tokens': 50000,
                                                                                                                                 'max_pull_requests': 0,
                                                                                                                                 'max_pushes': 0,
                                                                                                                                 'max_wall_seconds': 1800},
                                                                                                             'privacy_classification': 'private_source_change',
                                                                                                             'redaction_profile_ref': 'redaction.source-private-v1'},
                                                                              'canonical_json': '{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","attempt_authorization_digest":"4444444444444444444444444444444444444444444444444444444444444444","attempt_authorization_ref":"attempt-authorization-c2b3c-1","attempt_fence_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","attempt_fence_ref":"attempt-fence-c2b3c-1","base_git_object_format":"sha1","base_git_oid":"2222222222222222222222222222222222222222","candidate_ref":"candidate-c2b3a-1","capsule_profile_ref":"capsule-profile.regular-replace-v1","capsule_schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1","command_ref":"command-c2b3c-1","effect_authorization_digest":"5555555555555555555555555555555555555555555555555555555555555555","effect_authorization_ref":"effect-authorization-c2b3c-1","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":100000,"max_cpu_seconds":600,"max_deliveries":1,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":2147483648,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":1800},"effect_class":"author_candidate","effect_fence_ref":"effect-fence-c2b3c-1","effect_intent_ref":"effect-intent-c2b3c-1","global_stop_ref":"coding-global-stop-c2b3a-1","global_stop_version":0,"path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"privacy_classification":"private_source_change","program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","redaction_profile_ref":"redaction.source-private-v1","repository_ref":"repository-c2b3a-1","review_requirement_digest":"7777777777777777777777777777777777777777777777777777777777777777","review_requirement_ref":"review-c2b3a-1","schema_id":"governed-execution.nwp-worker-command.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","standing_grant_digest":"3333333333333333333333333333333333333333333333333333333333333333","standing_grant_ref":"standing-grant-c2b3c-1","validation_requirement_digest":"6666666666666666666666666666666666666666666666666666666666666666","validation_requirement_ref":"validation-c2b3a-1","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1","work_spec_digest":"2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c","work_spec_ref":"work-spec-c2b3a-1"}',
                                                                              'utf8_length': 2443,
                                                                              'digest_domain': 'governed-execution.nwp-worker-command.v1.identity',
                                                                              'digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484'},
                      'effect_fence': {'complete_mapping': {'schema_id': 'governed-execution.nwp-effect-fence.v1',
                                                            'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                            'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                            'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                            'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                            'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                            'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                            'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                            'program_ref': 'program-c2b3a-1',
                                                            'program_version_ref': 'program-version-c2b3a-1',
                                                            'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                            'work_item_ref': 'work-item-c2b3a-1',
                                                            'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                            'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                            'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                            'effect_class': 'author_candidate',
                                                            'command_ref': 'command-c2b3c-1',
                                                            'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484',
                                                            'candidate_ref': 'candidate-c2b3a-1',
                                                            'repository_ref': 'repository-c2b3a-1',
                                                            'base_git_object_format': 'sha1',
                                                            'base_git_oid': '2222222222222222222222222222222222222222',
                                                            'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                             'PLANS.md',
                                                                             'docs_contract_test.go'],
                                                            'effect_ceilings': {'max_active_invocations': 1,
                                                                                'max_candidate_bytes': 1048576,
                                                                                'max_changed_files': 3,
                                                                                'max_cost_microusd': 100000,
                                                                                'max_cpu_seconds': 600,
                                                                                'max_deliveries': 1,
                                                                                'max_deployments': 0,
                                                                                'max_local_commits': 0,
                                                                                'max_memory_bytes': 2147483648,
                                                                                'max_merges': 0,
                                                                                'max_model_input_tokens': 200000,
                                                                                'max_model_output_tokens': 50000,
                                                                                'max_pull_requests': 0,
                                                                                'max_pushes': 0,
                                                                                'max_wall_seconds': 1800},
                                                            'expires_at': '2026-08-22T13:34:56Z',
                                                            'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                            'global_stop_version': 0,
                                                            'portable_capsule_digest': None,
                                                            'cancellation_target_effect_intent_ref': None,
                                                            'cancellation_target_effect_fence_ref': None,
                                                            'cancellation_target_effect_fence_digest': None,
                                                            'effect_fence_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd'},
                                       'identity_excludes': ('effect_fence_digest',),
                                       'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-effect-fence.v1',
                                                                      'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                      'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                      'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                      'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                      'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                      'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                      'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                      'program_ref': 'program-c2b3a-1',
                                                                      'program_version_ref': 'program-version-c2b3a-1',
                                                                      'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                      'work_item_ref': 'work-item-c2b3a-1',
                                                                      'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                      'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                      'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                      'effect_class': 'author_candidate',
                                                                      'command_ref': 'command-c2b3c-1',
                                                                      'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484',
                                                                      'candidate_ref': 'candidate-c2b3a-1',
                                                                      'repository_ref': 'repository-c2b3a-1',
                                                                      'base_git_object_format': 'sha1',
                                                                      'base_git_oid': '2222222222222222222222222222222222222222',
                                                                      'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                       'PLANS.md',
                                                                                       'docs_contract_test.go'],
                                                                      'effect_ceilings': {'max_active_invocations': 1,
                                                                                          'max_candidate_bytes': 1048576,
                                                                                          'max_changed_files': 3,
                                                                                          'max_cost_microusd': 100000,
                                                                                          'max_cpu_seconds': 600,
                                                                                          'max_deliveries': 1,
                                                                                          'max_deployments': 0,
                                                                                          'max_local_commits': 0,
                                                                                          'max_memory_bytes': 2147483648,
                                                                                          'max_merges': 0,
                                                                                          'max_model_input_tokens': 200000,
                                                                                          'max_model_output_tokens': 50000,
                                                                                          'max_pull_requests': 0,
                                                                                          'max_pushes': 0,
                                                                                          'max_wall_seconds': 1800},
                                                                      'expires_at': '2026-08-22T13:34:56Z',
                                                                      'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                      'global_stop_version': 0,
                                                                      'portable_capsule_digest': None,
                                                                      'cancellation_target_effect_intent_ref': None,
                                                                      'cancellation_target_effect_fence_ref': None,
                                                                      'cancellation_target_effect_fence_digest': None},
                                       'canonical_json': '{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","attempt_fence_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","attempt_fence_ref":"attempt-fence-c2b3c-1","base_git_object_format":"sha1","base_git_oid":"2222222222222222222222222222222222222222","cancellation_target_effect_fence_digest":null,"cancellation_target_effect_fence_ref":null,"cancellation_target_effect_intent_ref":null,"candidate_ref":"candidate-c2b3a-1","command_digest":"545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484","command_ref":"command-c2b3c-1","effect_authorization_digest":"5555555555555555555555555555555555555555555555555555555555555555","effect_authorization_ref":"effect-authorization-c2b3c-1","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":100000,"max_cpu_seconds":600,"max_deliveries":1,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":2147483648,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":1800},"effect_class":"author_candidate","effect_fence_ref":"effect-fence-c2b3c-1","effect_intent_ref":"effect-intent-c2b3c-1","expires_at":"2026-08-22T13:34:56Z","global_stop_ref":"coding-global-stop-c2b3a-1","global_stop_version":0,"parent_standing_grant_digest":"3333333333333333333333333333333333333333333333333333333333333333","parent_standing_grant_ref":"standing-grant-c2b3c-1","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"portable_capsule_digest":null,"program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","repository_ref":"repository-c2b3a-1","schema_id":"governed-execution.nwp-effect-fence.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1"}',
                                       'utf8_length': 1939,
                                       'digest_domain': 'governed-execution.nwp-effect-fence.v1.identity',
                                       'digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd'},
                      'complete_worker_command': {'complete_mapping': {'schema_id': 'governed-execution.nwp-worker-command.v1',
                                                                       'command_ref': 'command-c2b3c-1',
                                                                       'program_ref': 'program-c2b3a-1',
                                                                       'program_version_ref': 'program-version-c2b3a-1',
                                                                       'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                       'work_item_ref': 'work-item-c2b3a-1',
                                                                       'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                       'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                       'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                       'effect_class': 'author_candidate',
                                                                       'candidate_ref': 'candidate-c2b3a-1',
                                                                       'repository_ref': 'repository-c2b3a-1',
                                                                       'base_git_object_format': 'sha1',
                                                                       'base_git_oid': '2222222222222222222222222222222222222222',
                                                                       'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                        'PLANS.md',
                                                                                        'docs_contract_test.go'],
                                                                       'work_spec_ref': 'work-spec-c2b3a-1',
                                                                       'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                       'standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                       'standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                       'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                                                       'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                                                       'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                       'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                       'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                       'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                       'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                       'effect_fence_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd',
                                                                       'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                       'global_stop_version': 0,
                                                                       'validation_requirement_ref': 'validation-c2b3a-1',
                                                                       'validation_requirement_digest': '6666666666666666666666666666666666666666666666666666666666666666',
                                                                       'review_requirement_ref': 'review-c2b3a-1',
                                                                       'review_requirement_digest': '7777777777777777777777777777777777777777777777777777777777777777',
                                                                       'capsule_schema_id': 'governed-execution.nwp-candidate-capsule-manifest.v1',
                                                                       'capsule_profile_ref': 'capsule-profile.regular-replace-v1',
                                                                       'effect_ceilings': {'max_active_invocations': 1,
                                                                                           'max_candidate_bytes': 1048576,
                                                                                           'max_changed_files': 3,
                                                                                           'max_cost_microusd': 100000,
                                                                                           'max_cpu_seconds': 600,
                                                                                           'max_deliveries': 1,
                                                                                           'max_deployments': 0,
                                                                                           'max_local_commits': 0,
                                                                                           'max_memory_bytes': 2147483648,
                                                                                           'max_merges': 0,
                                                                                           'max_model_input_tokens': 200000,
                                                                                           'max_model_output_tokens': 50000,
                                                                                           'max_pull_requests': 0,
                                                                                           'max_pushes': 0,
                                                                                           'max_wall_seconds': 1800},
                                                                       'privacy_classification': 'private_source_change',
                                                                       'redaction_profile_ref': 'redaction.source-private-v1',
                                                                       'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484'},
                                                  'identity_excludes': ('effect_fence_digest',
                                                                        'command_digest'),
                                                  'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-worker-command.v1',
                                                                                 'command_ref': 'command-c2b3c-1',
                                                                                 'program_ref': 'program-c2b3a-1',
                                                                                 'program_version_ref': 'program-version-c2b3a-1',
                                                                                 'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                 'work_item_ref': 'work-item-c2b3a-1',
                                                                                 'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                 'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                 'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                 'effect_class': 'author_candidate',
                                                                                 'candidate_ref': 'candidate-c2b3a-1',
                                                                                 'repository_ref': 'repository-c2b3a-1',
                                                                                 'base_git_object_format': 'sha1',
                                                                                 'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                 'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                  'PLANS.md',
                                                                                                  'docs_contract_test.go'],
                                                                                 'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                 'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                 'standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                                 'standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                                 'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                                                                 'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                                                                 'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                                 'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                                 'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                 'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                                 'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                                 'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                                 'global_stop_version': 0,
                                                                                 'validation_requirement_ref': 'validation-c2b3a-1',
                                                                                 'validation_requirement_digest': '6666666666666666666666666666666666666666666666666666666666666666',
                                                                                 'review_requirement_ref': 'review-c2b3a-1',
                                                                                 'review_requirement_digest': '7777777777777777777777777777777777777777777777777777777777777777',
                                                                                 'capsule_schema_id': 'governed-execution.nwp-candidate-capsule-manifest.v1',
                                                                                 'capsule_profile_ref': 'capsule-profile.regular-replace-v1',
                                                                                 'effect_ceilings': {'max_active_invocations': 1,
                                                                                                     'max_candidate_bytes': 1048576,
                                                                                                     'max_changed_files': 3,
                                                                                                     'max_cost_microusd': 100000,
                                                                                                     'max_cpu_seconds': 600,
                                                                                                     'max_deliveries': 1,
                                                                                                     'max_deployments': 0,
                                                                                                     'max_local_commits': 0,
                                                                                                     'max_memory_bytes': 2147483648,
                                                                                                     'max_merges': 0,
                                                                                                     'max_model_input_tokens': 200000,
                                                                                                     'max_model_output_tokens': 50000,
                                                                                                     'max_pull_requests': 0,
                                                                                                     'max_pushes': 0,
                                                                                                     'max_wall_seconds': 1800},
                                                                                 'privacy_classification': 'private_source_change',
                                                                                 'redaction_profile_ref': 'redaction.source-private-v1'},
                                                  'identity_canonical_json': '{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","attempt_authorization_digest":"4444444444444444444444444444444444444444444444444444444444444444","attempt_authorization_ref":"attempt-authorization-c2b3c-1","attempt_fence_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","attempt_fence_ref":"attempt-fence-c2b3c-1","base_git_object_format":"sha1","base_git_oid":"2222222222222222222222222222222222222222","candidate_ref":"candidate-c2b3a-1","capsule_profile_ref":"capsule-profile.regular-replace-v1","capsule_schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1","command_ref":"command-c2b3c-1","effect_authorization_digest":"5555555555555555555555555555555555555555555555555555555555555555","effect_authorization_ref":"effect-authorization-c2b3c-1","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":100000,"max_cpu_seconds":600,"max_deliveries":1,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":2147483648,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":1800},"effect_class":"author_candidate","effect_fence_ref":"effect-fence-c2b3c-1","effect_intent_ref":"effect-intent-c2b3c-1","global_stop_ref":"coding-global-stop-c2b3a-1","global_stop_version":0,"path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"privacy_classification":"private_source_change","program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","redaction_profile_ref":"redaction.source-private-v1","repository_ref":"repository-c2b3a-1","review_requirement_digest":"7777777777777777777777777777777777777777777777777777777777777777","review_requirement_ref":"review-c2b3a-1","schema_id":"governed-execution.nwp-worker-command.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","standing_grant_digest":"3333333333333333333333333333333333333333333333333333333333333333","standing_grant_ref":"standing-grant-c2b3c-1","validation_requirement_digest":"6666666666666666666666666666666666666666666666666666666666666666","validation_requirement_ref":"validation-c2b3a-1","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1","work_spec_digest":"2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c","work_spec_ref":"work-spec-c2b3a-1"}',
                                                  'identity_utf8_length': 2443,
                                                  'identity_raw_sha256': '24f7b3b96ca6e82e2e83f0283564cf3335b6beef80d410a4921548899f1a05c7',
                                                  'complete_record_canonical_json': '{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","attempt_authorization_digest":"4444444444444444444444444444444444444444444444444444444444444444","attempt_authorization_ref":"attempt-authorization-c2b3c-1","attempt_fence_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","attempt_fence_ref":"attempt-fence-c2b3c-1","base_git_object_format":"sha1","base_git_oid":"2222222222222222222222222222222222222222","candidate_ref":"candidate-c2b3a-1","capsule_profile_ref":"capsule-profile.regular-replace-v1","capsule_schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1","command_digest":"545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484","command_ref":"command-c2b3c-1","effect_authorization_digest":"5555555555555555555555555555555555555555555555555555555555555555","effect_authorization_ref":"effect-authorization-c2b3c-1","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":100000,"max_cpu_seconds":600,"max_deliveries":1,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":2147483648,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":1800},"effect_class":"author_candidate","effect_fence_digest":"8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd","effect_fence_ref":"effect-fence-c2b3c-1","effect_intent_ref":"effect-intent-c2b3c-1","global_stop_ref":"coding-global-stop-c2b3a-1","global_stop_version":0,"path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"privacy_classification":"private_source_change","program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","redaction_profile_ref":"redaction.source-private-v1","repository_ref":"repository-c2b3a-1","review_requirement_digest":"7777777777777777777777777777777777777777777777777777777777777777","review_requirement_ref":"review-c2b3a-1","schema_id":"governed-execution.nwp-worker-command.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","standing_grant_digest":"3333333333333333333333333333333333333333333333333333333333333333","standing_grant_ref":"standing-grant-c2b3c-1","validation_requirement_digest":"6666666666666666666666666666666666666666666666666666666666666666","validation_requirement_ref":"validation-c2b3a-1","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1","work_spec_digest":"2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c","work_spec_ref":"work-spec-c2b3a-1"}',
                                                  'complete_record_utf8_length': 2616,
                                                  'complete_record_raw_sha256': '15a343f1a3606bae1774ed42297cf7ea567f11d3fddcfc47d164becdd8353260',
                                                  'digest_domain': 'governed-execution.nwp-worker-command.v1.identity',
                                                  'digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484'},
                      'delivery_envelope': {'complete_mapping': {'schema_id': 'governed-execution.nwp-delivery-envelope.v1',
                                                                 'delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                                                 'program_ref': 'program-c2b3a-1',
                                                                 'program_version_ref': 'program-version-c2b3a-1',
                                                                 'command_ref': 'command-c2b3c-1',
                                                                 'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484',
                                                                 'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                 'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                 'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                 'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                 'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                 'effect_fence_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd',
                                                                 'adapter_kind': 'direct_local_bootstrap',
                                                                 'adapter_safe_correlation_ref': 'adapter-correlation-c2b3c-1',
                                                                 'delivery_envelope_digest': 'e60ea42c5cc195a5a55aebb7b9c00d760b7337e5232be82729df67b7e317f35a'},
                                            'identity_excludes': ('delivery_envelope_digest',),
                                            'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-delivery-envelope.v1',
                                                                           'delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                                                           'program_ref': 'program-c2b3a-1',
                                                                           'program_version_ref': 'program-version-c2b3a-1',
                                                                           'command_ref': 'command-c2b3c-1',
                                                                           'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484',
                                                                           'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                           'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                           'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                           'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                           'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                           'effect_fence_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd',
                                                                           'adapter_kind': 'direct_local_bootstrap',
                                                                           'adapter_safe_correlation_ref': 'adapter-correlation-c2b3c-1'},
                                            'canonical_json': '{"adapter_kind":"direct_local_bootstrap","adapter_safe_correlation_ref":"adapter-correlation-c2b3c-1","attempt_fence_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","attempt_fence_ref":"attempt-fence-c2b3c-1","command_digest":"545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484","command_ref":"command-c2b3c-1","delivery_attempt_ref":"delivery-attempt-c2b3c-1","effect_fence_digest":"8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd","effect_fence_ref":"effect-fence-c2b3c-1","effect_intent_ref":"effect-intent-c2b3c-1","program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","schema_id":"governed-execution.nwp-delivery-envelope.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1"}',
                                            'utf8_length': 765,
                                            'digest_domain': 'governed-execution.nwp-delivery-envelope.v1.identity',
                                            'digest': 'e60ea42c5cc195a5a55aebb7b9c00d760b7337e5232be82729df67b7e317f35a'},
                      'safe_mutation_command': {'complete_mapping': {'schema_id': 'governed-execution.nwp-establish-development-author-effect-intent-command.v1',
                                                                     'mutation_ref': 'mutation-c2b3c-1',
                                                                     'program_ref': 'program-c2b3a-1',
                                                                     'program_version_ref': 'program-version-c2b3a-1',
                                                                     'program_version_number': 1,
                                                                     'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                     'work_item_ref': 'work-item-c2b3a-1',
                                                                     'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                     'basis_decision_ref': 'decision-c2b3a-1',
                                                                     'basis_decision_digest': 'e743c359aea93d7931250552b62bc741d84c490f9ebb68e071c8616cc5fb4b96',
                                                                     'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                     'candidate_ref': 'candidate-c2b3a-1',
                                                                     'attempt_number': 1,
                                                                     'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                     'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                     'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                     'command_ref': 'command-c2b3c-1',
                                                                     'authority_evaluation_ref': 'authority-evaluation-c2b3c-1',
                                                                     'delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                                                     'adapter_safe_correlation_ref': 'adapter-correlation-c2b3c-1',
                                                                     'coding_global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                     'coding_global_stop_version': 0,
                                                                     'capsule_schema_id': 'governed-execution.nwp-candidate-capsule-manifest.v1',
                                                                     'capsule_profile_ref': 'capsule-profile.regular-replace-v1',
                                                                     'privacy_classification': 'private_source_change',
                                                                     'redaction_profile_ref': 'redaction.source-private-v1',
                                                                     'work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                                                                   'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                                   'program_ref': 'program-c2b3a-1',
                                                                                                   'program_version_ref': 'program-version-c2b3a-1',
                                                                                                   'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                                   'work_item_ref': 'work-item-c2b3a-1',
                                                                                                   'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                                   'repository_ref': 'repository-c2b3a-1',
                                                                                                   'base_git_object_format': 'sha1',
                                                                                                   'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                                   'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                                        'PLANS.md',
                                                                                                                        'docs_contract_test.go'),
                                                                                                   'validation_requirement_ref': 'validation-c2b3a-1',
                                                                                                   'review_requirement_ref': 'review-c2b3a-1',
                                                                                                   'privacy_classification': 'private_work_spec',
                                                                                                   'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                                   'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
                                                                     'validation_requirement_evidence': {'schema_id': 'governed-execution.nwp-development-validation-requirement-evidence.v1',
                                                                                                         'requirement_ref': 'validation-c2b3a-1',
                                                                                                         'requirement_digest': '6666666666666666666666666666666666666666666666666666666666666666',
                                                                                                         'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                                         'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                                         'safe_evidence_digest': 'bfd4be05ab68440c4402fdaa770fdbdbbec72f73962be77b8ef9d342ece9a5ea'},
                                                                     'review_requirement_evidence': {'schema_id': 'governed-execution.nwp-development-review-requirement-evidence.v1',
                                                                                                     'requirement_ref': 'review-c2b3a-1',
                                                                                                     'requirement_digest': '7777777777777777777777777777777777777777777777777777777777777777',
                                                                                                     'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                                     'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                                     'safe_evidence_digest': '3a6ffa9bdb8b5e71d0deeb0d90e8d087aeb66ae92849690cae779efbdd6eb9f7'},
                                                                     'attempt_fence': {'schema_id': 'governed-execution.nwp-attempt-fence.v1',
                                                                                       'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                       'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                                       'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                                       'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                                                                       'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                                                                       'program_ref': 'program-c2b3a-1',
                                                                                       'program_version_ref': 'program-version-c2b3a-1',
                                                                                       'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                       'work_item_ref': 'work-item-c2b3a-1',
                                                                                       'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                       'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                       'repository_ref': 'repository-c2b3a-1',
                                                                                       'base_git_object_format': 'sha1',
                                                                                       'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                       'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                        'PLANS.md',
                                                                                                        'docs_contract_test.go'],
                                                                                       'allowed_effect_classes': ['author_candidate',
                                                                                                                  'cancel_effect',
                                                                                                                  'local_git_commit',
                                                                                                                  'review_candidate',
                                                                                                                  'validate_candidate'],
                                                                                       'aggregate_ceilings': {'max_active_invocations': 1,
                                                                                                              'max_candidate_bytes': 1048576,
                                                                                                              'max_changed_files': 3,
                                                                                                              'max_cost_microusd': 100000,
                                                                                                              'max_cpu_seconds': 600,
                                                                                                              'max_deliveries': 3,
                                                                                                              'max_deployments': 0,
                                                                                                              'max_local_commits': 1,
                                                                                                              'max_memory_bytes': 2147483648,
                                                                                                              'max_merges': 0,
                                                                                                              'max_model_input_tokens': 200000,
                                                                                                              'max_model_output_tokens': 50000,
                                                                                                              'max_pull_requests': 0,
                                                                                                              'max_pushes': 0,
                                                                                                              'max_wall_seconds': 1800},
                                                                                       'expires_at': '2026-08-22T13:34:56Z',
                                                                                       'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                                       'global_stop_version': 0,
                                                                                       'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed'},
                                                                     'effect_authorization_safe_binding': {'schema_id': 'governed-execution.nwp-development-effect-authorization-safe-binding.v1',
                                                                                                           'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                                                           'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                                                           'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                                                           'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                                                           'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                                           'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                                                           'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                                           'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                                           'effect_class': 'author_candidate',
                                                                                                           'path_ceiling': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                                            'PLANS.md',
                                                                                                                            'docs_contract_test.go'),
                                                                                                           'effect_ceilings': {'max_active_invocations': 1,
                                                                                                                               'max_candidate_bytes': 1048576,
                                                                                                                               'max_changed_files': 3,
                                                                                                                               'max_cost_microusd': 100000,
                                                                                                                               'max_cpu_seconds': 600,
                                                                                                                               'max_deliveries': 1,
                                                                                                                               'max_deployments': 0,
                                                                                                                               'max_local_commits': 0,
                                                                                                                               'max_memory_bytes': 2147483648,
                                                                                                                               'max_merges': 0,
                                                                                                                               'max_model_input_tokens': 200000,
                                                                                                                               'max_model_output_tokens': 50000,
                                                                                                                               'max_pull_requests': 0,
                                                                                                                               'max_pushes': 0,
                                                                                                                               'max_wall_seconds': 1800},
                                                                                                           'expires_at': '2026-08-22T13:34:56Z',
                                                                                                           'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                                                           'global_stop_version': 0,
                                                                                                           'safe_binding_digest': 'afa53c667dc36b2d797ab2a9ed94c46e1012a19352120b892e631a5e43e03868'},
                                                                     'worker_command': {'schema_id': 'governed-execution.nwp-worker-command.v1',
                                                                                        'command_ref': 'command-c2b3c-1',
                                                                                        'program_ref': 'program-c2b3a-1',
                                                                                        'program_version_ref': 'program-version-c2b3a-1',
                                                                                        'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                        'work_item_ref': 'work-item-c2b3a-1',
                                                                                        'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                        'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                        'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                        'effect_class': 'author_candidate',
                                                                                        'candidate_ref': 'candidate-c2b3a-1',
                                                                                        'repository_ref': 'repository-c2b3a-1',
                                                                                        'base_git_object_format': 'sha1',
                                                                                        'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                        'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                         'PLANS.md',
                                                                                                         'docs_contract_test.go'],
                                                                                        'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                        'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                        'standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                                        'standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                                        'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                                                                        'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                                                                        'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                                        'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                                        'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                        'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                                        'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                                        'effect_fence_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd',
                                                                                        'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                                        'global_stop_version': 0,
                                                                                        'validation_requirement_ref': 'validation-c2b3a-1',
                                                                                        'validation_requirement_digest': '6666666666666666666666666666666666666666666666666666666666666666',
                                                                                        'review_requirement_ref': 'review-c2b3a-1',
                                                                                        'review_requirement_digest': '7777777777777777777777777777777777777777777777777777777777777777',
                                                                                        'capsule_schema_id': 'governed-execution.nwp-candidate-capsule-manifest.v1',
                                                                                        'capsule_profile_ref': 'capsule-profile.regular-replace-v1',
                                                                                        'effect_ceilings': {'max_active_invocations': 1,
                                                                                                            'max_candidate_bytes': 1048576,
                                                                                                            'max_changed_files': 3,
                                                                                                            'max_cost_microusd': 100000,
                                                                                                            'max_cpu_seconds': 600,
                                                                                                            'max_deliveries': 1,
                                                                                                            'max_deployments': 0,
                                                                                                            'max_local_commits': 0,
                                                                                                            'max_memory_bytes': 2147483648,
                                                                                                            'max_merges': 0,
                                                                                                            'max_model_input_tokens': 200000,
                                                                                                            'max_model_output_tokens': 50000,
                                                                                                            'max_pull_requests': 0,
                                                                                                            'max_pushes': 0,
                                                                                                            'max_wall_seconds': 1800},
                                                                                        'privacy_classification': 'private_source_change',
                                                                                        'redaction_profile_ref': 'redaction.source-private-v1',
                                                                                        'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484'},
                                                                     'effect_fence': {'schema_id': 'governed-execution.nwp-effect-fence.v1',
                                                                                      'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                                      'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                                      'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                                      'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                                      'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                                      'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                      'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                                      'program_ref': 'program-c2b3a-1',
                                                                                      'program_version_ref': 'program-version-c2b3a-1',
                                                                                      'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                      'work_item_ref': 'work-item-c2b3a-1',
                                                                                      'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                      'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                      'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                      'effect_class': 'author_candidate',
                                                                                      'command_ref': 'command-c2b3c-1',
                                                                                      'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484',
                                                                                      'candidate_ref': 'candidate-c2b3a-1',
                                                                                      'repository_ref': 'repository-c2b3a-1',
                                                                                      'base_git_object_format': 'sha1',
                                                                                      'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                      'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                       'PLANS.md',
                                                                                                       'docs_contract_test.go'],
                                                                                      'effect_ceilings': {'max_active_invocations': 1,
                                                                                                          'max_candidate_bytes': 1048576,
                                                                                                          'max_changed_files': 3,
                                                                                                          'max_cost_microusd': 100000,
                                                                                                          'max_cpu_seconds': 600,
                                                                                                          'max_deliveries': 1,
                                                                                                          'max_deployments': 0,
                                                                                                          'max_local_commits': 0,
                                                                                                          'max_memory_bytes': 2147483648,
                                                                                                          'max_merges': 0,
                                                                                                          'max_model_input_tokens': 200000,
                                                                                                          'max_model_output_tokens': 50000,
                                                                                                          'max_pull_requests': 0,
                                                                                                          'max_pushes': 0,
                                                                                                          'max_wall_seconds': 1800},
                                                                                      'expires_at': '2026-08-22T13:34:56Z',
                                                                                      'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                                      'global_stop_version': 0,
                                                                                      'portable_capsule_digest': None,
                                                                                      'cancellation_target_effect_intent_ref': None,
                                                                                      'cancellation_target_effect_fence_ref': None,
                                                                                      'cancellation_target_effect_fence_digest': None,
                                                                                      'effect_fence_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd'},
                                                                     'delivery_envelope': {'schema_id': 'governed-execution.nwp-delivery-envelope.v1',
                                                                                           'delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                                                                           'program_ref': 'program-c2b3a-1',
                                                                                           'program_version_ref': 'program-version-c2b3a-1',
                                                                                           'command_ref': 'command-c2b3c-1',
                                                                                           'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484',
                                                                                           'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                           'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                           'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                           'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                                           'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                                           'effect_fence_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd',
                                                                                           'adapter_kind': 'direct_local_bootstrap',
                                                                                           'adapter_safe_correlation_ref': 'adapter-correlation-c2b3c-1',
                                                                                           'delivery_envelope_digest': 'e60ea42c5cc195a5a55aebb7b9c00d760b7337e5232be82729df67b7e317f35a'},
                                                                     'command_digest': '1d3473cc6cfebb93d75b09de1c7f1822cc8ee9e1800b026208116b1d8b1199a7'},
                                                'identity_excludes': ('command_digest',),
                                                'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-establish-development-author-effect-intent-command.v1',
                                                                               'mutation_ref': 'mutation-c2b3c-1',
                                                                               'program_ref': 'program-c2b3a-1',
                                                                               'program_version_ref': 'program-version-c2b3a-1',
                                                                               'program_version_number': 1,
                                                                               'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                               'work_item_ref': 'work-item-c2b3a-1',
                                                                               'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                               'basis_decision_ref': 'decision-c2b3a-1',
                                                                               'basis_decision_digest': 'e743c359aea93d7931250552b62bc741d84c490f9ebb68e071c8616cc5fb4b96',
                                                                               'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                               'candidate_ref': 'candidate-c2b3a-1',
                                                                               'attempt_number': 1,
                                                                               'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                               'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                               'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                               'command_ref': 'command-c2b3c-1',
                                                                               'authority_evaluation_ref': 'authority-evaluation-c2b3c-1',
                                                                               'delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                                                               'adapter_safe_correlation_ref': 'adapter-correlation-c2b3c-1',
                                                                               'coding_global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                               'coding_global_stop_version': 0,
                                                                               'capsule_schema_id': 'governed-execution.nwp-candidate-capsule-manifest.v1',
                                                                               'capsule_profile_ref': 'capsule-profile.regular-replace-v1',
                                                                               'privacy_classification': 'private_source_change',
                                                                               'redaction_profile_ref': 'redaction.source-private-v1',
                                                                               'work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                                                                             'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                                             'program_ref': 'program-c2b3a-1',
                                                                                                             'program_version_ref': 'program-version-c2b3a-1',
                                                                                                             'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                                             'work_item_ref': 'work-item-c2b3a-1',
                                                                                                             'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                                             'repository_ref': 'repository-c2b3a-1',
                                                                                                             'base_git_object_format': 'sha1',
                                                                                                             'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                                             'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                                                  'PLANS.md',
                                                                                                                                  'docs_contract_test.go'),
                                                                                                             'validation_requirement_ref': 'validation-c2b3a-1',
                                                                                                             'review_requirement_ref': 'review-c2b3a-1',
                                                                                                             'privacy_classification': 'private_work_spec',
                                                                                                             'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                                             'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
                                                                               'validation_requirement_evidence': {'schema_id': 'governed-execution.nwp-development-validation-requirement-evidence.v1',
                                                                                                                   'requirement_ref': 'validation-c2b3a-1',
                                                                                                                   'requirement_digest': '6666666666666666666666666666666666666666666666666666666666666666',
                                                                                                                   'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                                                   'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                                                   'safe_evidence_digest': 'bfd4be05ab68440c4402fdaa770fdbdbbec72f73962be77b8ef9d342ece9a5ea'},
                                                                               'review_requirement_evidence': {'schema_id': 'governed-execution.nwp-development-review-requirement-evidence.v1',
                                                                                                               'requirement_ref': 'review-c2b3a-1',
                                                                                                               'requirement_digest': '7777777777777777777777777777777777777777777777777777777777777777',
                                                                                                               'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                                               'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                                               'safe_evidence_digest': '3a6ffa9bdb8b5e71d0deeb0d90e8d087aeb66ae92849690cae779efbdd6eb9f7'},
                                                                               'attempt_fence': {'schema_id': 'governed-execution.nwp-attempt-fence.v1',
                                                                                                 'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                                 'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                                                 'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                                                 'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                                                                                 'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                                                                                 'program_ref': 'program-c2b3a-1',
                                                                                                 'program_version_ref': 'program-version-c2b3a-1',
                                                                                                 'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                                 'work_item_ref': 'work-item-c2b3a-1',
                                                                                                 'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                                 'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                                 'repository_ref': 'repository-c2b3a-1',
                                                                                                 'base_git_object_format': 'sha1',
                                                                                                 'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                                 'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                                  'PLANS.md',
                                                                                                                  'docs_contract_test.go'],
                                                                                                 'allowed_effect_classes': ['author_candidate',
                                                                                                                            'cancel_effect',
                                                                                                                            'local_git_commit',
                                                                                                                            'review_candidate',
                                                                                                                            'validate_candidate'],
                                                                                                 'aggregate_ceilings': {'max_active_invocations': 1,
                                                                                                                        'max_candidate_bytes': 1048576,
                                                                                                                        'max_changed_files': 3,
                                                                                                                        'max_cost_microusd': 100000,
                                                                                                                        'max_cpu_seconds': 600,
                                                                                                                        'max_deliveries': 3,
                                                                                                                        'max_deployments': 0,
                                                                                                                        'max_local_commits': 1,
                                                                                                                        'max_memory_bytes': 2147483648,
                                                                                                                        'max_merges': 0,
                                                                                                                        'max_model_input_tokens': 200000,
                                                                                                                        'max_model_output_tokens': 50000,
                                                                                                                        'max_pull_requests': 0,
                                                                                                                        'max_pushes': 0,
                                                                                                                        'max_wall_seconds': 1800},
                                                                                                 'expires_at': '2026-08-22T13:34:56Z',
                                                                                                 'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                                                 'global_stop_version': 0,
                                                                                                 'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed'},
                                                                               'effect_authorization_safe_binding': {'schema_id': 'governed-execution.nwp-development-effect-authorization-safe-binding.v1',
                                                                                                                     'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                                                                     'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                                                                     'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                                                                     'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                                                                     'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                                                     'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                                                                     'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                                                     'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                                                     'effect_class': 'author_candidate',
                                                                                                                     'path_ceiling': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                                                      'PLANS.md',
                                                                                                                                      'docs_contract_test.go'),
                                                                                                                     'effect_ceilings': {'max_active_invocations': 1,
                                                                                                                                         'max_candidate_bytes': 1048576,
                                                                                                                                         'max_changed_files': 3,
                                                                                                                                         'max_cost_microusd': 100000,
                                                                                                                                         'max_cpu_seconds': 600,
                                                                                                                                         'max_deliveries': 1,
                                                                                                                                         'max_deployments': 0,
                                                                                                                                         'max_local_commits': 0,
                                                                                                                                         'max_memory_bytes': 2147483648,
                                                                                                                                         'max_merges': 0,
                                                                                                                                         'max_model_input_tokens': 200000,
                                                                                                                                         'max_model_output_tokens': 50000,
                                                                                                                                         'max_pull_requests': 0,
                                                                                                                                         'max_pushes': 0,
                                                                                                                                         'max_wall_seconds': 1800},
                                                                                                                     'expires_at': '2026-08-22T13:34:56Z',
                                                                                                                     'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                                                                     'global_stop_version': 0,
                                                                                                                     'safe_binding_digest': 'afa53c667dc36b2d797ab2a9ed94c46e1012a19352120b892e631a5e43e03868'},
                                                                               'worker_command': {'schema_id': 'governed-execution.nwp-worker-command.v1',
                                                                                                  'command_ref': 'command-c2b3c-1',
                                                                                                  'program_ref': 'program-c2b3a-1',
                                                                                                  'program_version_ref': 'program-version-c2b3a-1',
                                                                                                  'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                                  'work_item_ref': 'work-item-c2b3a-1',
                                                                                                  'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                                  'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                                  'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                                  'effect_class': 'author_candidate',
                                                                                                  'candidate_ref': 'candidate-c2b3a-1',
                                                                                                  'repository_ref': 'repository-c2b3a-1',
                                                                                                  'base_git_object_format': 'sha1',
                                                                                                  'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                                  'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                                   'PLANS.md',
                                                                                                                   'docs_contract_test.go'],
                                                                                                  'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                                  'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                                  'standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                                                  'standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                                                  'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                                                                                  'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                                                                                  'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                                                  'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                                                  'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                                  'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                                                  'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                                                  'effect_fence_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd',
                                                                                                  'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                                                  'global_stop_version': 0,
                                                                                                  'validation_requirement_ref': 'validation-c2b3a-1',
                                                                                                  'validation_requirement_digest': '6666666666666666666666666666666666666666666666666666666666666666',
                                                                                                  'review_requirement_ref': 'review-c2b3a-1',
                                                                                                  'review_requirement_digest': '7777777777777777777777777777777777777777777777777777777777777777',
                                                                                                  'capsule_schema_id': 'governed-execution.nwp-candidate-capsule-manifest.v1',
                                                                                                  'capsule_profile_ref': 'capsule-profile.regular-replace-v1',
                                                                                                  'effect_ceilings': {'max_active_invocations': 1,
                                                                                                                      'max_candidate_bytes': 1048576,
                                                                                                                      'max_changed_files': 3,
                                                                                                                      'max_cost_microusd': 100000,
                                                                                                                      'max_cpu_seconds': 600,
                                                                                                                      'max_deliveries': 1,
                                                                                                                      'max_deployments': 0,
                                                                                                                      'max_local_commits': 0,
                                                                                                                      'max_memory_bytes': 2147483648,
                                                                                                                      'max_merges': 0,
                                                                                                                      'max_model_input_tokens': 200000,
                                                                                                                      'max_model_output_tokens': 50000,
                                                                                                                      'max_pull_requests': 0,
                                                                                                                      'max_pushes': 0,
                                                                                                                      'max_wall_seconds': 1800},
                                                                                                  'privacy_classification': 'private_source_change',
                                                                                                  'redaction_profile_ref': 'redaction.source-private-v1',
                                                                                                  'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484'},
                                                                               'effect_fence': {'schema_id': 'governed-execution.nwp-effect-fence.v1',
                                                                                                'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                                                'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                                                'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                                                'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                                                'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                                                'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                                'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                                                'program_ref': 'program-c2b3a-1',
                                                                                                'program_version_ref': 'program-version-c2b3a-1',
                                                                                                'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                                'work_item_ref': 'work-item-c2b3a-1',
                                                                                                'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                                'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                                'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                                'effect_class': 'author_candidate',
                                                                                                'command_ref': 'command-c2b3c-1',
                                                                                                'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484',
                                                                                                'candidate_ref': 'candidate-c2b3a-1',
                                                                                                'repository_ref': 'repository-c2b3a-1',
                                                                                                'base_git_object_format': 'sha1',
                                                                                                'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                                'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                                 'PLANS.md',
                                                                                                                 'docs_contract_test.go'],
                                                                                                'effect_ceilings': {'max_active_invocations': 1,
                                                                                                                    'max_candidate_bytes': 1048576,
                                                                                                                    'max_changed_files': 3,
                                                                                                                    'max_cost_microusd': 100000,
                                                                                                                    'max_cpu_seconds': 600,
                                                                                                                    'max_deliveries': 1,
                                                                                                                    'max_deployments': 0,
                                                                                                                    'max_local_commits': 0,
                                                                                                                    'max_memory_bytes': 2147483648,
                                                                                                                    'max_merges': 0,
                                                                                                                    'max_model_input_tokens': 200000,
                                                                                                                    'max_model_output_tokens': 50000,
                                                                                                                    'max_pull_requests': 0,
                                                                                                                    'max_pushes': 0,
                                                                                                                    'max_wall_seconds': 1800},
                                                                                                'expires_at': '2026-08-22T13:34:56Z',
                                                                                                'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                                                'global_stop_version': 0,
                                                                                                'portable_capsule_digest': None,
                                                                                                'cancellation_target_effect_intent_ref': None,
                                                                                                'cancellation_target_effect_fence_ref': None,
                                                                                                'cancellation_target_effect_fence_digest': None,
                                                                                                'effect_fence_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd'},
                                                                               'delivery_envelope': {'schema_id': 'governed-execution.nwp-delivery-envelope.v1',
                                                                                                     'delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                                                                                     'program_ref': 'program-c2b3a-1',
                                                                                                     'program_version_ref': 'program-version-c2b3a-1',
                                                                                                     'command_ref': 'command-c2b3c-1',
                                                                                                     'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484',
                                                                                                     'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                                     'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                                     'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                                     'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                                                     'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                                                     'effect_fence_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd',
                                                                                                     'adapter_kind': 'direct_local_bootstrap',
                                                                                                     'adapter_safe_correlation_ref': 'adapter-correlation-c2b3c-1',
                                                                                                     'delivery_envelope_digest': 'e60ea42c5cc195a5a55aebb7b9c00d760b7337e5232be82729df67b7e317f35a'}},
                                                'canonical_json': '{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","adapter_safe_correlation_ref":"adapter-correlation-c2b3c-1","attempt_fence":{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","aggregate_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":100000,"max_cpu_seconds":600,"max_deliveries":3,"max_deployments":0,"max_local_commits":1,"max_memory_bytes":2147483648,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":1800},"allowed_effect_classes":["author_candidate","cancel_effect","local_git_commit","review_candidate","validate_candidate"],"attempt_authorization_digest":"4444444444444444444444444444444444444444444444444444444444444444","attempt_authorization_ref":"attempt-authorization-c2b3c-1","attempt_fence_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","attempt_fence_ref":"attempt-fence-c2b3c-1","base_git_object_format":"sha1","base_git_oid":"2222222222222222222222222222222222222222","expires_at":"2026-08-22T13:34:56Z","global_stop_ref":"coding-global-stop-c2b3a-1","global_stop_version":0,"parent_standing_grant_digest":"3333333333333333333333333333333333333333333333333333333333333333","parent_standing_grant_ref":"standing-grant-c2b3c-1","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","repository_ref":"repository-c2b3a-1","schema_id":"governed-execution.nwp-attempt-fence.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1"},"attempt_fence_ref":"attempt-fence-c2b3c-1","attempt_number":1,"authority_evaluation_ref":"authority-evaluation-c2b3c-1","basis_decision_digest":"e743c359aea93d7931250552b62bc741d84c490f9ebb68e071c8616cc5fb4b96","basis_decision_ref":"decision-c2b3a-1","candidate_ref":"candidate-c2b3a-1","capsule_profile_ref":"capsule-profile.regular-replace-v1","capsule_schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1","coding_global_stop_ref":"coding-global-stop-c2b3a-1","coding_global_stop_version":0,"command_ref":"command-c2b3c-1","delivery_attempt_ref":"delivery-attempt-c2b3c-1","delivery_envelope":{"adapter_kind":"direct_local_bootstrap","adapter_safe_correlation_ref":"adapter-correlation-c2b3c-1","attempt_fence_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","attempt_fence_ref":"attempt-fence-c2b3c-1","command_digest":"545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484","command_ref":"command-c2b3c-1","delivery_attempt_ref":"delivery-attempt-c2b3c-1","delivery_envelope_digest":"e60ea42c5cc195a5a55aebb7b9c00d760b7337e5232be82729df67b7e317f35a","effect_fence_digest":"8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd","effect_fence_ref":"effect-fence-c2b3c-1","effect_intent_ref":"effect-intent-c2b3c-1","program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","schema_id":"governed-execution.nwp-delivery-envelope.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1"},"effect_authorization_safe_binding":{"attempt_fence_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","attempt_fence_ref":"attempt-fence-c2b3c-1","effect_authorization_digest":"5555555555555555555555555555555555555555555555555555555555555555","effect_authorization_ref":"effect-authorization-c2b3c-1","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":100000,"max_cpu_seconds":600,"max_deliveries":1,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":2147483648,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":1800},"effect_class":"author_candidate","effect_intent_ref":"effect-intent-c2b3c-1","expires_at":"2026-08-22T13:34:56Z","global_stop_ref":"coding-global-stop-c2b3a-1","global_stop_version":0,"parent_standing_grant_digest":"3333333333333333333333333333333333333333333333333333333333333333","parent_standing_grant_ref":"standing-grant-c2b3c-1","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"safe_binding_digest":"afa53c667dc36b2d797ab2a9ed94c46e1012a19352120b892e631a5e43e03868","schema_id":"governed-execution.nwp-development-effect-authorization-safe-binding.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1"},"effect_fence":{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","attempt_fence_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","attempt_fence_ref":"attempt-fence-c2b3c-1","base_git_object_format":"sha1","base_git_oid":"2222222222222222222222222222222222222222","cancellation_target_effect_fence_digest":null,"cancellation_target_effect_fence_ref":null,"cancellation_target_effect_intent_ref":null,"candidate_ref":"candidate-c2b3a-1","command_digest":"545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484","command_ref":"command-c2b3c-1","effect_authorization_digest":"5555555555555555555555555555555555555555555555555555555555555555","effect_authorization_ref":"effect-authorization-c2b3c-1","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":100000,"max_cpu_seconds":600,"max_deliveries":1,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":2147483648,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":1800},"effect_class":"author_candidate","effect_fence_digest":"8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd","effect_fence_ref":"effect-fence-c2b3c-1","effect_intent_ref":"effect-intent-c2b3c-1","expires_at":"2026-08-22T13:34:56Z","global_stop_ref":"coding-global-stop-c2b3a-1","global_stop_version":0,"parent_standing_grant_digest":"3333333333333333333333333333333333333333333333333333333333333333","parent_standing_grant_ref":"standing-grant-c2b3c-1","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"portable_capsule_digest":null,"program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","repository_ref":"repository-c2b3a-1","schema_id":"governed-execution.nwp-effect-fence.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1"},"effect_fence_ref":"effect-fence-c2b3c-1","effect_intent_ref":"effect-intent-c2b3c-1","mutation_ref":"mutation-c2b3c-1","privacy_classification":"private_source_change","program_ref":"program-c2b3a-1","program_version_number":1,"program_version_ref":"program-version-c2b3a-1","redaction_profile_ref":"redaction.source-private-v1","review_requirement_evidence":{"requirement_digest":"7777777777777777777777777777777777777777777777777777777777777777","requirement_ref":"review-c2b3a-1","safe_evidence_digest":"3a6ffa9bdb8b5e71d0deeb0d90e8d087aeb66ae92849690cae779efbdd6eb9f7","schema_id":"governed-execution.nwp-development-review-requirement-evidence.v1","work_spec_digest":"2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c","work_spec_ref":"work-spec-c2b3a-1"},"schema_id":"governed-execution.nwp-establish-development-author-effect-intent-command.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","validation_requirement_evidence":{"requirement_digest":"6666666666666666666666666666666666666666666666666666666666666666","requirement_ref":"validation-c2b3a-1","safe_evidence_digest":"bfd4be05ab68440c4402fdaa770fdbdbbec72f73962be77b8ef9d342ece9a5ea","schema_id":"governed-execution.nwp-development-validation-requirement-evidence.v1","work_spec_digest":"2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c","work_spec_ref":"work-spec-c2b3a-1"},"work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1","work_spec_safe_projection":{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","authorized_paths":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"base_git_object_format":"sha1","base_git_oid":"2222222222222222222222222222222222222222","privacy_classification":"private_work_spec","program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","repository_ref":"repository-c2b3a-1","review_requirement_ref":"review-c2b3a-1","safe_projection_digest":"1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab","schema_id":"governed-execution.nwp-development-work-spec-safe-projection.v1","validation_requirement_ref":"validation-c2b3a-1","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1","work_spec_digest":"2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c","work_spec_ref":"work-spec-c2b3a-1"},"worker_command":{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","attempt_authorization_digest":"4444444444444444444444444444444444444444444444444444444444444444","attempt_authorization_ref":"attempt-authorization-c2b3c-1","attempt_fence_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","attempt_fence_ref":"attempt-fence-c2b3c-1","base_git_object_format":"sha1","base_git_oid":"2222222222222222222222222222222222222222","candidate_ref":"candidate-c2b3a-1","capsule_profile_ref":"capsule-profile.regular-replace-v1","capsule_schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1","command_digest":"545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484","command_ref":"command-c2b3c-1","effect_authorization_digest":"5555555555555555555555555555555555555555555555555555555555555555","effect_authorization_ref":"effect-authorization-c2b3c-1","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":100000,"max_cpu_seconds":600,"max_deliveries":1,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":2147483648,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":1800},"effect_class":"author_candidate","effect_fence_digest":"8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd","effect_fence_ref":"effect-fence-c2b3c-1","effect_intent_ref":"effect-intent-c2b3c-1","global_stop_ref":"coding-global-stop-c2b3a-1","global_stop_version":0,"path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"privacy_classification":"private_source_change","program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","redaction_profile_ref":"redaction.source-private-v1","repository_ref":"repository-c2b3a-1","review_requirement_digest":"7777777777777777777777777777777777777777777777777777777777777777","review_requirement_ref":"review-c2b3a-1","schema_id":"governed-execution.nwp-worker-command.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","standing_grant_digest":"3333333333333333333333333333333333333333333333333333333333333333","standing_grant_ref":"standing-grant-c2b3c-1","validation_requirement_digest":"6666666666666666666666666666666666666666666666666666666666666666","validation_requirement_ref":"validation-c2b3a-1","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1","work_spec_digest":"2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c","work_spec_ref":"work-spec-c2b3a-1"}}',
                                                'utf8_length': 11693,
                                                'digest_domain': 'governed-execution.nwp-establish-development-author-effect-intent-command.v1.identity',
                                                'digest': '1d3473cc6cfebb93d75b09de1c7f1822cc8ee9e1800b026208116b1d8b1199a7'},
                      'result_projection': {'complete_mapping': {'schema_id': 'governed-execution.nwp-establish-development-author-effect-intent-result.v1',
                                                                 'program_ref': 'program-c2b3a-1',
                                                                 'decision_ref': 'decision-c2b3a-1',
                                                                 'result_program_version_ref': 'program-version-c2b3a-1',
                                                                 'result_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                 'result_effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                 'result_effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                 'result_delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                                                 'result_projection_digest': '470d1ccf62ce6934320d3258385c5b8c38d066f7b8ac3a233f366f6c3c42bc39'},
                                            'identity_excludes': ('result_projection_digest',),
                                            'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-establish-development-author-effect-intent-result.v1',
                                                                           'program_ref': 'program-c2b3a-1',
                                                                           'decision_ref': 'decision-c2b3a-1',
                                                                           'result_program_version_ref': 'program-version-c2b3a-1',
                                                                           'result_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                           'result_effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                           'result_effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                           'result_delivery_attempt_ref': 'delivery-attempt-c2b3c-1'},
                                            'canonical_json': '{"decision_ref":"decision-c2b3a-1","program_ref":"program-c2b3a-1","result_delivery_attempt_ref":"delivery-attempt-c2b3c-1","result_effect_fence_ref":"effect-fence-c2b3c-1","result_effect_intent_ref":"effect-intent-c2b3c-1","result_program_version_ref":"program-version-c2b3a-1","result_semantic_attempt_ref":"semantic-attempt-c2b3a-1","schema_id":"governed-execution.nwp-establish-development-author-effect-intent-result.v1"}',
                                            'utf8_length': 426,
                                            'digest_domain': 'governed-execution.nwp-establish-development-author-effect-intent-result.v1.identity',
                                            'digest': '470d1ccf62ce6934320d3258385c5b8c38d066f7b8ac3a233f366f6c3c42bc39'}},
 'persisted_postimages': {'semantic_attempt': {'schema_id': 'governed-execution.nwp-development-semantic-attempt.v1',
                                               'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                               'program_ref': 'program-c2b3a-1',
                                               'program_version_ref': 'program-version-c2b3a-1',
                                               'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                               'work_item_ref': 'work-item-c2b3a-1',
                                               'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                               'attempt_number': 1,
                                               'candidate_ref': 'candidate-c2b3a-1',
                                               'attempt_phase': 'established',
                                               'selection_decision_ref': 'decision-c2b3a-1',
                                               'created_at': '2026-08-22T12:34:56Z',
                                               'semantic_attempt_digest': '7018934d8724dcbc8cd3f93f603fca1682bf3d4b762293c4191e28e001cdd263'},
                          'attempt_fence': {'schema_id': 'governed-execution.nwp-attempt-fence.v1',
                                            'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                            'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                            'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                            'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                            'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                            'program_ref': 'program-c2b3a-1',
                                            'program_version_ref': 'program-version-c2b3a-1',
                                            'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                            'work_item_ref': 'work-item-c2b3a-1',
                                            'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                            'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                            'repository_ref': 'repository-c2b3a-1',
                                            'base_git_object_format': 'sha1',
                                            'base_git_oid': '2222222222222222222222222222222222222222',
                                            'path_ceiling_json': '[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"]',
                                            'allowed_effect_class_mask': 31,
                                            'aggregate_max_active_invocations': 1,
                                            'aggregate_max_candidate_bytes': 1048576,
                                            'aggregate_max_changed_files': 3,
                                            'aggregate_max_cost_microusd': 100000,
                                            'aggregate_max_cpu_seconds': 600,
                                            'aggregate_max_deliveries': 3,
                                            'aggregate_max_deployments': 0,
                                            'aggregate_max_local_commits': 1,
                                            'aggregate_max_memory_bytes': 2147483648,
                                            'aggregate_max_merges': 0,
                                            'aggregate_max_model_input_tokens': 200000,
                                            'aggregate_max_model_output_tokens': 50000,
                                            'aggregate_max_pull_requests': 0,
                                            'aggregate_max_pushes': 0,
                                            'aggregate_max_wall_seconds': 1800,
                                            'expires_at': '2026-08-22T13:34:56Z',
                                            'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                            'global_stop_version': 0,
                                            'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                            'recorded_at': '2026-08-22T12:34:56Z'},
                          'author_effect_intent': {'schema_id': 'governed-execution.nwp-development-effect-intent.v1',
                                                   'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                   'program_ref': 'program-c2b3a-1',
                                                   'program_version_ref': 'program-version-c2b3a-1',
                                                   'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                   'effect_class': 'author_candidate',
                                                   'candidate_ref': 'candidate-c2b3a-1',
                                                   'command_ref': 'command-c2b3c-1',
                                                   'basis_decision_ref': 'decision-c2b3a-1',
                                                   'cancellation_target_effect_intent_ref': None,
                                                   'expected_target_effect_head_revision': None,
                                                   'portable_capsule_digest': None,
                                                   'created_at': '2026-08-22T12:34:56Z',
                                                   'effect_intent_digest': '2597aeafff2e78212f12423f933f23c6e0a4107d80fc33cbf6d103f225bf938d'},
                          'author_effect_fence': {'schema_id': 'governed-execution.nwp-effect-fence.v1',
                                                  'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                  'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                  'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                  'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                  'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                  'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                  'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                  'program_ref': 'program-c2b3a-1',
                                                  'program_version_ref': 'program-version-c2b3a-1',
                                                  'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                  'work_item_ref': 'work-item-c2b3a-1',
                                                  'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                  'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                  'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                  'effect_class': 'author_candidate',
                                                  'command_ref': 'command-c2b3c-1',
                                                  'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484',
                                                  'candidate_ref': 'candidate-c2b3a-1',
                                                  'repository_ref': 'repository-c2b3a-1',
                                                  'base_git_object_format': 'sha1',
                                                  'base_git_oid': '2222222222222222222222222222222222222222',
                                                  'path_ceiling_json': '[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"]',
                                                  'effect_max_active_invocations': 1,
                                                  'effect_max_candidate_bytes': 1048576,
                                                  'effect_max_changed_files': 3,
                                                  'effect_max_cost_microusd': 100000,
                                                  'effect_max_cpu_seconds': 600,
                                                  'effect_max_deliveries': 1,
                                                  'effect_max_deployments': 0,
                                                  'effect_max_local_commits': 0,
                                                  'effect_max_memory_bytes': 2147483648,
                                                  'effect_max_merges': 0,
                                                  'effect_max_model_input_tokens': 200000,
                                                  'effect_max_model_output_tokens': 50000,
                                                  'effect_max_pull_requests': 0,
                                                  'effect_max_pushes': 0,
                                                  'effect_max_wall_seconds': 1800,
                                                  'expires_at': '2026-08-22T13:34:56Z',
                                                  'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                  'global_stop_version': 0,
                                                  'portable_capsule_digest': None,
                                                  'cancellation_target_effect_intent_ref': None,
                                                  'cancellation_target_effect_fence_ref': None,
                                                  'cancellation_target_effect_fence_digest': None,
                                                  'effect_fence_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd',
                                                  'recorded_at': '2026-08-22T12:34:56Z'},
                          'author_command': {'schema_id': 'governed-execution.nwp-worker-command.v1',
                                             'command_ref': 'command-c2b3c-1',
                                             'program_ref': 'program-c2b3a-1',
                                             'program_version_ref': 'program-version-c2b3a-1',
                                             'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                             'work_item_ref': 'work-item-c2b3a-1',
                                             'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                             'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                             'effect_intent_ref': 'effect-intent-c2b3c-1',
                                             'effect_class': 'author_candidate',
                                             'candidate_ref': 'candidate-c2b3a-1',
                                             'repository_ref': 'repository-c2b3a-1',
                                             'base_git_object_format': 'sha1',
                                             'base_git_oid': '2222222222222222222222222222222222222222',
                                             'path_ceiling_json': '[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"]',
                                             'work_spec_ref': 'work-spec-c2b3a-1',
                                             'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                             'standing_grant_ref': 'standing-grant-c2b3c-1',
                                             'standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                             'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                             'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                             'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                             'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                             'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                             'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                             'effect_fence_ref': 'effect-fence-c2b3c-1',
                                             'effect_fence_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd',
                                             'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                             'global_stop_version': 0,
                                             'validation_requirement_ref': 'validation-c2b3a-1',
                                             'validation_requirement_digest': '6666666666666666666666666666666666666666666666666666666666666666',
                                             'review_requirement_ref': 'review-c2b3a-1',
                                             'review_requirement_digest': '7777777777777777777777777777777777777777777777777777777777777777',
                                             'capsule_schema_id': 'governed-execution.nwp-candidate-capsule-manifest.v1',
                                             'capsule_profile_ref': 'capsule-profile.regular-replace-v1',
                                             'effect_max_active_invocations': 1,
                                             'effect_max_candidate_bytes': 1048576,
                                             'effect_max_changed_files': 3,
                                             'effect_max_cost_microusd': 100000,
                                             'effect_max_cpu_seconds': 600,
                                             'effect_max_deliveries': 1,
                                             'effect_max_deployments': 0,
                                             'effect_max_local_commits': 0,
                                             'effect_max_memory_bytes': 2147483648,
                                             'effect_max_merges': 0,
                                             'effect_max_model_input_tokens': 200000,
                                             'effect_max_model_output_tokens': 50000,
                                             'effect_max_pull_requests': 0,
                                             'effect_max_pushes': 0,
                                             'effect_max_wall_seconds': 1800,
                                             'privacy_classification': 'private_source_change',
                                             'redaction_profile_ref': 'redaction.source-private-v1',
                                             'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484',
                                             'recorded_at': '2026-08-22T12:34:56Z'},
                          'authority_evaluation': {'schema_id': 'governed-execution.nwp-development-authority-evaluation.v1',
                                                   'authority_evaluation_ref': 'authority-evaluation-c2b3c-1',
                                                   'program_ref': 'program-c2b3a-1',
                                                   'evaluation_scope': 'effect',
                                                   'evaluation_subject_ref': 'effect-intent-c2b3c-1',
                                                   'semantic_attempt_ref': None,
                                                   'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                   'authority_ref': 'effect-authorization-c2b3c-1',
                                                   'authority_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                   'authority_state': 'pending',
                                                   'reason_code': 'external_verification_pending',
                                                   'expires_at': None,
                                                   'evaluated_at': '2026-08-22T12:34:56Z',
                                                   'authority_evaluation_digest': 'e484b72ed81cffbd5dfe80be4263c9c0bc66739a9a45d96d6dffcf748208164d'},
                          'effect_head_postimage': {'schema_id': 'governed-execution.nwp-development-effect-head.v1',
                                                    'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                    'program_ref': 'program-c2b3a-1',
                                                    'current_effect_fence_ref': 'effect-fence-c2b3c-1',
                                                    'head_revision': 0,
                                                    'effect_state': 'ready_for_delivery',
                                                    'cancellation_effect_intent_ref': None,
                                                    'updated_at': '2026-08-22T12:34:56Z',
                                                    'head_digest': 'b302769593fd214cec86ada39e685cb97e46880e78973738c33e858e39a4e964'},
                          'initial_delivery_attempt': {'schema_id': 'governed-execution.nwp-delivery-envelope.v1',
                                                       'delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                                       'program_ref': 'program-c2b3a-1',
                                                       'program_version_ref': 'program-version-c2b3a-1',
                                                       'command_ref': 'command-c2b3c-1',
                                                       'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484',
                                                       'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                       'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                       'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                       'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                       'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                       'effect_fence_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd',
                                                       'adapter_kind': 'direct_local_bootstrap',
                                                       'adapter_safe_correlation_ref': 'adapter-correlation-c2b3c-1',
                                                       'delivery_envelope_digest': 'e60ea42c5cc195a5a55aebb7b9c00d760b7337e5232be82729df67b7e317f35a',
                                                       'delivery_kind': 'initial',
                                                       'delivery_number': 1,
                                                       'predecessor_delivery_attempt_ref': None,
                                                       'basis_decision_ref': 'decision-c2b3a-1',
                                                       'recorded_at': '2026-08-22T12:34:56Z',
                                                       'delivery_attempt_digest': '715b1baa3a9a6e0142f46433a0222a47ea42773b62b6c2e9a0dde2ab070f134e'},
                          'delivery_head_postimage': {'schema_id': 'governed-execution.nwp-development-delivery-head.v1',
                                                      'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                      'program_ref': 'program-c2b3a-1',
                                                      'current_delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                                      'head_revision': 0,
                                                      'delivery_state': 'planned',
                                                      'updated_at': '2026-08-22T12:34:56Z',
                                                      'head_digest': 'cc09294e960a7812807f2037c5066c6af263659f3409c2f4dcf75429e473bddf'},
                          'mutation_receipt': {'schema_id': 'governed-execution.nwp-development-mutation-receipt.v1',
                                               'mutation_ref': 'mutation-c2b3c-1',
                                               'mutation_family': 'establish_development_author_effect_intent',
                                               'command_schema_id': 'governed-execution.nwp-establish-development-author-effect-intent-command.v1',
                                               'command_digest': '1d3473cc6cfebb93d75b09de1c7f1822cc8ee9e1800b026208116b1d8b1199a7',
                                               'program_ref': 'program-c2b3a-1',
                                               'decision_ref': 'decision-c2b3a-1',
                                               'result_program_version_ref': 'program-version-c2b3a-1',
                                               'result_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                               'result_effect_intent_ref': 'effect-intent-c2b3c-1',
                                               'result_effect_fence_ref': 'effect-fence-c2b3c-1',
                                               'result_delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                               'result_observation_ref': None,
                                               'result_decision_ref': None,
                                               'result_class': 'development_author_effect_intent_established',
                                               'result_projection_digest': '470d1ccf62ce6934320d3258385c5b8c38d066f7b8ac3a233f366f6c3c42bc39',
                                               'mutation_graph_digest': 'bd7d6a8b10a01e779495d8bc140eed9937d71e511d7686dbdb368cdb29bbb41d',
                                               'outcome': 'committed',
                                               'committed_at': '2026-08-22T12:34:56Z'}},
 'postimage_digest_specs': {'semantic_attempt': {'self_digest_field': 'semantic_attempt_digest',
                                                 'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-development-semantic-attempt.v1',
                                                                                'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                'program_ref': 'program-c2b3a-1',
                                                                                'program_version_ref': 'program-version-c2b3a-1',
                                                                                'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                'work_item_ref': 'work-item-c2b3a-1',
                                                                                'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                'attempt_number': 1,
                                                                                'candidate_ref': 'candidate-c2b3a-1',
                                                                                'attempt_phase': 'established',
                                                                                'selection_decision_ref': 'decision-c2b3a-1',
                                                                                'created_at': '2026-08-22T12:34:56Z'},
                                                 'canonical_json': '{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","attempt_number":1,"attempt_phase":"established","candidate_ref":"candidate-c2b3a-1","created_at":"2026-08-22T12:34:56Z","program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","schema_id":"governed-execution.nwp-development-semantic-attempt.v1","selection_decision_ref":"decision-c2b3a-1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1"}',
                                                 'utf8_length': 512,
                                                 'digest_domain': 'governed-execution.nwp-development-semantic-attempt.v1.identity',
                                                 'self_digest': '7018934d8724dcbc8cd3f93f603fca1682bf3d4b762293c4191e28e001cdd263'},
                            'attempt_fence': {'self_digest_field': 'attempt_fence_digest',
                                              'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-attempt-fence.v1',
                                                                             'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                             'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                             'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                             'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                                                             'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                                                             'program_ref': 'program-c2b3a-1',
                                                                             'program_version_ref': 'program-version-c2b3a-1',
                                                                             'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                             'work_item_ref': 'work-item-c2b3a-1',
                                                                             'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                             'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                             'repository_ref': 'repository-c2b3a-1',
                                                                             'base_git_object_format': 'sha1',
                                                                             'base_git_oid': '2222222222222222222222222222222222222222',
                                                                             'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                              'PLANS.md',
                                                                                              'docs_contract_test.go'],
                                                                             'allowed_effect_classes': ['author_candidate',
                                                                                                        'cancel_effect',
                                                                                                        'local_git_commit',
                                                                                                        'review_candidate',
                                                                                                        'validate_candidate'],
                                                                             'aggregate_ceilings': {'max_active_invocations': 1,
                                                                                                    'max_candidate_bytes': 1048576,
                                                                                                    'max_changed_files': 3,
                                                                                                    'max_cost_microusd': 100000,
                                                                                                    'max_cpu_seconds': 600,
                                                                                                    'max_deliveries': 3,
                                                                                                    'max_deployments': 0,
                                                                                                    'max_local_commits': 1,
                                                                                                    'max_memory_bytes': 2147483648,
                                                                                                    'max_merges': 0,
                                                                                                    'max_model_input_tokens': 200000,
                                                                                                    'max_model_output_tokens': 50000,
                                                                                                    'max_pull_requests': 0,
                                                                                                    'max_pushes': 0,
                                                                                                    'max_wall_seconds': 1800},
                                                                             'expires_at': '2026-08-22T13:34:56Z',
                                                                             'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                             'global_stop_version': 0},
                                              'canonical_json': '{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","aggregate_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":100000,"max_cpu_seconds":600,"max_deliveries":3,"max_deployments":0,"max_local_commits":1,"max_memory_bytes":2147483648,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":1800},"allowed_effect_classes":["author_candidate","cancel_effect","local_git_commit","review_candidate","validate_candidate"],"attempt_authorization_digest":"4444444444444444444444444444444444444444444444444444444444444444","attempt_authorization_ref":"attempt-authorization-c2b3c-1","attempt_fence_ref":"attempt-fence-c2b3c-1","base_git_object_format":"sha1","base_git_oid":"2222222222222222222222222222222222222222","expires_at":"2026-08-22T13:34:56Z","global_stop_ref":"coding-global-stop-c2b3a-1","global_stop_version":0,"parent_standing_grant_digest":"3333333333333333333333333333333333333333333333333333333333333333","parent_standing_grant_ref":"standing-grant-c2b3c-1","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","repository_ref":"repository-c2b3a-1","schema_id":"governed-execution.nwp-attempt-fence.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1"}',
                                              'utf8_length': 1538,
                                              'digest_domain': 'governed-execution.nwp-attempt-fence.v1.identity',
                                              'self_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed'},
                            'author_effect_intent': {'self_digest_field': 'effect_intent_digest',
                                                     'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-development-effect-intent.v1',
                                                                                    'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                    'program_ref': 'program-c2b3a-1',
                                                                                    'program_version_ref': 'program-version-c2b3a-1',
                                                                                    'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                    'effect_class': 'author_candidate',
                                                                                    'candidate_ref': 'candidate-c2b3a-1',
                                                                                    'command_ref': 'command-c2b3c-1',
                                                                                    'basis_decision_ref': 'decision-c2b3a-1',
                                                                                    'cancellation_target_effect_intent_ref': None,
                                                                                    'expected_target_effect_head_revision': None,
                                                                                    'portable_capsule_digest': None,
                                                                                    'created_at': '2026-08-22T12:34:56Z'},
                                                     'canonical_json': '{"basis_decision_ref":"decision-c2b3a-1","cancellation_target_effect_intent_ref":null,"candidate_ref":"candidate-c2b3a-1","command_ref":"command-c2b3c-1","created_at":"2026-08-22T12:34:56Z","effect_class":"author_candidate","effect_intent_ref":"effect-intent-c2b3c-1","expected_target_effect_head_revision":null,"portable_capsule_digest":null,"program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","schema_id":"governed-execution.nwp-development-effect-intent.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1"}',
                                                     'utf8_length': 539,
                                                     'digest_domain': 'governed-execution.nwp-development-effect-intent.v1.identity',
                                                     'self_digest': '2597aeafff2e78212f12423f933f23c6e0a4107d80fc33cbf6d103f225bf938d'},
                            'author_effect_fence': {'self_digest_field': 'effect_fence_digest',
                                                    'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-effect-fence.v1',
                                                                                   'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                                   'parent_standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                                   'parent_standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                                   'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                                   'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                                   'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                                   'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                                   'program_ref': 'program-c2b3a-1',
                                                                                   'program_version_ref': 'program-version-c2b3a-1',
                                                                                   'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                   'work_item_ref': 'work-item-c2b3a-1',
                                                                                   'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                   'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                   'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                   'effect_class': 'author_candidate',
                                                                                   'command_ref': 'command-c2b3c-1',
                                                                                   'command_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484',
                                                                                   'candidate_ref': 'candidate-c2b3a-1',
                                                                                   'repository_ref': 'repository-c2b3a-1',
                                                                                   'base_git_object_format': 'sha1',
                                                                                   'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                   'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                    'PLANS.md',
                                                                                                    'docs_contract_test.go'],
                                                                                   'effect_ceilings': {'max_active_invocations': 1,
                                                                                                       'max_candidate_bytes': 1048576,
                                                                                                       'max_changed_files': 3,
                                                                                                       'max_cost_microusd': 100000,
                                                                                                       'max_cpu_seconds': 600,
                                                                                                       'max_deliveries': 1,
                                                                                                       'max_deployments': 0,
                                                                                                       'max_local_commits': 0,
                                                                                                       'max_memory_bytes': 2147483648,
                                                                                                       'max_merges': 0,
                                                                                                       'max_model_input_tokens': 200000,
                                                                                                       'max_model_output_tokens': 50000,
                                                                                                       'max_pull_requests': 0,
                                                                                                       'max_pushes': 0,
                                                                                                       'max_wall_seconds': 1800},
                                                                                   'expires_at': '2026-08-22T13:34:56Z',
                                                                                   'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                                   'global_stop_version': 0,
                                                                                   'portable_capsule_digest': None,
                                                                                   'cancellation_target_effect_intent_ref': None,
                                                                                   'cancellation_target_effect_fence_ref': None,
                                                                                   'cancellation_target_effect_fence_digest': None},
                                                    'canonical_json': '{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","attempt_fence_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","attempt_fence_ref":"attempt-fence-c2b3c-1","base_git_object_format":"sha1","base_git_oid":"2222222222222222222222222222222222222222","cancellation_target_effect_fence_digest":null,"cancellation_target_effect_fence_ref":null,"cancellation_target_effect_intent_ref":null,"candidate_ref":"candidate-c2b3a-1","command_digest":"545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484","command_ref":"command-c2b3c-1","effect_authorization_digest":"5555555555555555555555555555555555555555555555555555555555555555","effect_authorization_ref":"effect-authorization-c2b3c-1","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":100000,"max_cpu_seconds":600,"max_deliveries":1,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":2147483648,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":1800},"effect_class":"author_candidate","effect_fence_ref":"effect-fence-c2b3c-1","effect_intent_ref":"effect-intent-c2b3c-1","expires_at":"2026-08-22T13:34:56Z","global_stop_ref":"coding-global-stop-c2b3a-1","global_stop_version":0,"parent_standing_grant_digest":"3333333333333333333333333333333333333333333333333333333333333333","parent_standing_grant_ref":"standing-grant-c2b3c-1","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"portable_capsule_digest":null,"program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","repository_ref":"repository-c2b3a-1","schema_id":"governed-execution.nwp-effect-fence.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1"}',
                                                    'utf8_length': 1939,
                                                    'digest_domain': 'governed-execution.nwp-effect-fence.v1.identity',
                                                    'self_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd'},
                            'author_command': {'self_digest_field': 'command_digest',
                                               'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-worker-command.v1',
                                                                              'command_ref': 'command-c2b3c-1',
                                                                              'program_ref': 'program-c2b3a-1',
                                                                              'program_version_ref': 'program-version-c2b3a-1',
                                                                              'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                              'work_item_ref': 'work-item-c2b3a-1',
                                                                              'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                              'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                              'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                              'effect_class': 'author_candidate',
                                                                              'candidate_ref': 'candidate-c2b3a-1',
                                                                              'repository_ref': 'repository-c2b3a-1',
                                                                              'base_git_object_format': 'sha1',
                                                                              'base_git_oid': '2222222222222222222222222222222222222222',
                                                                              'path_ceiling': ['.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                               'PLANS.md',
                                                                                               'docs_contract_test.go'],
                                                                              'work_spec_ref': 'work-spec-c2b3a-1',
                                                                              'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                              'standing_grant_ref': 'standing-grant-c2b3c-1',
                                                                              'standing_grant_digest': '3333333333333333333333333333333333333333333333333333333333333333',
                                                                              'attempt_authorization_ref': 'attempt-authorization-c2b3c-1',
                                                                              'attempt_authorization_digest': '4444444444444444444444444444444444444444444444444444444444444444',
                                                                              'effect_authorization_ref': 'effect-authorization-c2b3c-1',
                                                                              'effect_authorization_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                              'attempt_fence_ref': 'attempt-fence-c2b3c-1',
                                                                              'attempt_fence_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed',
                                                                              'effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                              'global_stop_ref': 'coding-global-stop-c2b3a-1',
                                                                              'global_stop_version': 0,
                                                                              'validation_requirement_ref': 'validation-c2b3a-1',
                                                                              'validation_requirement_digest': '6666666666666666666666666666666666666666666666666666666666666666',
                                                                              'review_requirement_ref': 'review-c2b3a-1',
                                                                              'review_requirement_digest': '7777777777777777777777777777777777777777777777777777777777777777',
                                                                              'capsule_schema_id': 'governed-execution.nwp-candidate-capsule-manifest.v1',
                                                                              'capsule_profile_ref': 'capsule-profile.regular-replace-v1',
                                                                              'effect_ceilings': {'max_active_invocations': 1,
                                                                                                  'max_candidate_bytes': 1048576,
                                                                                                  'max_changed_files': 3,
                                                                                                  'max_cost_microusd': 100000,
                                                                                                  'max_cpu_seconds': 600,
                                                                                                  'max_deliveries': 1,
                                                                                                  'max_deployments': 0,
                                                                                                  'max_local_commits': 0,
                                                                                                  'max_memory_bytes': 2147483648,
                                                                                                  'max_merges': 0,
                                                                                                  'max_model_input_tokens': 200000,
                                                                                                  'max_model_output_tokens': 50000,
                                                                                                  'max_pull_requests': 0,
                                                                                                  'max_pushes': 0,
                                                                                                  'max_wall_seconds': 1800},
                                                                              'privacy_classification': 'private_source_change',
                                                                              'redaction_profile_ref': 'redaction.source-private-v1'},
                                               'canonical_json': '{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","attempt_authorization_digest":"4444444444444444444444444444444444444444444444444444444444444444","attempt_authorization_ref":"attempt-authorization-c2b3c-1","attempt_fence_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","attempt_fence_ref":"attempt-fence-c2b3c-1","base_git_object_format":"sha1","base_git_oid":"2222222222222222222222222222222222222222","candidate_ref":"candidate-c2b3a-1","capsule_profile_ref":"capsule-profile.regular-replace-v1","capsule_schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1","command_ref":"command-c2b3c-1","effect_authorization_digest":"5555555555555555555555555555555555555555555555555555555555555555","effect_authorization_ref":"effect-authorization-c2b3c-1","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":100000,"max_cpu_seconds":600,"max_deliveries":1,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":2147483648,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":1800},"effect_class":"author_candidate","effect_fence_ref":"effect-fence-c2b3c-1","effect_intent_ref":"effect-intent-c2b3c-1","global_stop_ref":"coding-global-stop-c2b3a-1","global_stop_version":0,"path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"privacy_classification":"private_source_change","program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","redaction_profile_ref":"redaction.source-private-v1","repository_ref":"repository-c2b3a-1","review_requirement_digest":"7777777777777777777777777777777777777777777777777777777777777777","review_requirement_ref":"review-c2b3a-1","schema_id":"governed-execution.nwp-worker-command.v1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","standing_grant_digest":"3333333333333333333333333333333333333333333333333333333333333333","standing_grant_ref":"standing-grant-c2b3c-1","validation_requirement_digest":"6666666666666666666666666666666666666666666666666666666666666666","validation_requirement_ref":"validation-c2b3a-1","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1","work_spec_digest":"2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c","work_spec_ref":"work-spec-c2b3a-1"}',
                                               'utf8_length': 2443,
                                               'digest_domain': 'governed-execution.nwp-worker-command.v1.identity',
                                               'self_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484'},
                            'authority_evaluation': {'self_digest_field': 'authority_evaluation_digest',
                                                     'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-development-authority-evaluation.v1',
                                                                                    'authority_evaluation_ref': 'authority-evaluation-c2b3c-1',
                                                                                    'program_ref': 'program-c2b3a-1',
                                                                                    'evaluation_scope': 'effect',
                                                                                    'evaluation_subject_ref': 'effect-intent-c2b3c-1',
                                                                                    'semantic_attempt_ref': None,
                                                                                    'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                    'authority_ref': 'effect-authorization-c2b3c-1',
                                                                                    'authority_digest': '5555555555555555555555555555555555555555555555555555555555555555',
                                                                                    'authority_state': 'pending',
                                                                                    'reason_code': 'external_verification_pending',
                                                                                    'expires_at': None,
                                                                                    'evaluated_at': '2026-08-22T12:34:56Z'},
                                                     'canonical_json': '{"authority_digest":"5555555555555555555555555555555555555555555555555555555555555555","authority_evaluation_ref":"authority-evaluation-c2b3c-1","authority_ref":"effect-authorization-c2b3c-1","authority_state":"pending","effect_intent_ref":"effect-intent-c2b3c-1","evaluated_at":"2026-08-22T12:34:56Z","evaluation_scope":"effect","evaluation_subject_ref":"effect-intent-c2b3c-1","expires_at":null,"program_ref":"program-c2b3a-1","reason_code":"external_verification_pending","schema_id":"governed-execution.nwp-development-authority-evaluation.v1","semantic_attempt_ref":null}',
                                                     'utf8_length': 576,
                                                     'digest_domain': 'governed-execution.nwp-development-authority-evaluation.v1.identity',
                                                     'self_digest': 'e484b72ed81cffbd5dfe80be4263c9c0bc66739a9a45d96d6dffcf748208164d'},
                            'effect_head_postimage': {'self_digest_field': 'head_digest',
                                                      'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-development-effect-head.v1',
                                                                                     'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                     'program_ref': 'program-c2b3a-1',
                                                                                     'current_effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                                     'head_revision': 0,
                                                                                     'effect_state': 'ready_for_delivery',
                                                                                     'cancellation_effect_intent_ref': None,
                                                                                     'updated_at': '2026-08-22T12:34:56Z'},
                                                      'canonical_json': '{"cancellation_effect_intent_ref":null,"current_effect_fence_ref":"effect-fence-c2b3c-1","effect_intent_ref":"effect-intent-c2b3c-1","effect_state":"ready_for_delivery","head_revision":0,"program_ref":"program-c2b3a-1","schema_id":"governed-execution.nwp-development-effect-head.v1","updated_at":"2026-08-22T12:34:56Z"}',
                                                      'utf8_length': 319,
                                                      'digest_domain': 'governed-execution.nwp-development-effect-head.v1.identity',
                                                      'self_digest': 'b302769593fd214cec86ada39e685cb97e46880e78973738c33e858e39a4e964'},
                            'initial_delivery_attempt': {'self_digest_field': 'delivery_attempt_digest',
                                                         'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-development-delivery-attempt.v1',
                                                                                        'delivery_envelope_digest': 'e60ea42c5cc195a5a55aebb7b9c00d760b7337e5232be82729df67b7e317f35a',
                                                                                        'delivery_kind': 'initial',
                                                                                        'delivery_number': 1,
                                                                                        'predecessor_delivery_attempt_ref': None,
                                                                                        'basis_decision_ref': 'decision-c2b3a-1',
                                                                                        'recorded_at': '2026-08-22T12:34:56Z'},
                                                         'canonical_json': '{"basis_decision_ref":"decision-c2b3a-1","delivery_envelope_digest":"e60ea42c5cc195a5a55aebb7b9c00d760b7337e5232be82729df67b7e317f35a","delivery_kind":"initial","delivery_number":1,"predecessor_delivery_attempt_ref":null,"recorded_at":"2026-08-22T12:34:56Z","schema_id":"governed-execution.nwp-development-delivery-attempt.v1"}',
                                                         'utf8_length': 327,
                                                         'digest_domain': 'governed-execution.nwp-development-delivery-attempt.v1.identity',
                                                         'self_digest': '715b1baa3a9a6e0142f46433a0222a47ea42773b62b6c2e9a0dde2ab070f134e'},
                            'delivery_head_postimage': {'self_digest_field': 'head_digest',
                                                        'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-development-delivery-head.v1',
                                                                                       'effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                       'program_ref': 'program-c2b3a-1',
                                                                                       'current_delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                                                                       'head_revision': 0,
                                                                                       'delivery_state': 'planned',
                                                                                       'updated_at': '2026-08-22T12:34:56Z'},
                                                        'canonical_json': '{"current_delivery_attempt_ref":"delivery-attempt-c2b3c-1","delivery_state":"planned","effect_intent_ref":"effect-intent-c2b3c-1","head_revision":0,"program_ref":"program-c2b3a-1","schema_id":"governed-execution.nwp-development-delivery-head.v1","updated_at":"2026-08-22T12:34:56Z"}',
                                                        'utf8_length': 282,
                                                        'digest_domain': 'governed-execution.nwp-development-delivery-head.v1.identity',
                                                        'self_digest': 'cc09294e960a7812807f2037c5066c6af263659f3409c2f4dcf75429e473bddf'},
                            'mutation_receipt': {'self_digest_field': 'mutation_graph_digest',
                                                 'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-development-mutation-receipt.v1',
                                                                                'mutation_ref': 'mutation-c2b3c-1',
                                                                                'mutation_family': 'establish_development_author_effect_intent',
                                                                                'command_schema_id': 'governed-execution.nwp-establish-development-author-effect-intent-command.v1',
                                                                                'command_digest': '1d3473cc6cfebb93d75b09de1c7f1822cc8ee9e1800b026208116b1d8b1199a7',
                                                                                'program_ref': 'program-c2b3a-1',
                                                                                'decision_ref': 'decision-c2b3a-1',
                                                                                'result_program_version_ref': 'program-version-c2b3a-1',
                                                                                'result_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                                                'result_effect_intent_ref': 'effect-intent-c2b3c-1',
                                                                                'result_effect_fence_ref': 'effect-fence-c2b3c-1',
                                                                                'result_delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                                                                'result_observation_ref': None,
                                                                                'result_decision_ref': None,
                                                                                'result_class': 'development_author_effect_intent_established',
                                                                                'result_projection_digest': '470d1ccf62ce6934320d3258385c5b8c38d066f7b8ac3a233f366f6c3c42bc39',
                                                                                'outcome': 'committed',
                                                                                'committed_at': '2026-08-22T12:34:56Z',
                                                                                'graph_entries': ({'role': 'semantic_attempt',
                                                                                                   'ordinal': 0,
                                                                                                   'record_ref': 'semantic-attempt-c2b3a-1',
                                                                                                   'record_digest': '7018934d8724dcbc8cd3f93f603fca1682bf3d4b762293c4191e28e001cdd263'},
                                                                                                  {'role': 'attempt_fence',
                                                                                                   'ordinal': 0,
                                                                                                   'record_ref': 'attempt-fence-c2b3c-1',
                                                                                                   'record_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed'},
                                                                                                  {'role': 'author_effect_intent',
                                                                                                   'ordinal': 0,
                                                                                                   'record_ref': 'effect-intent-c2b3c-1',
                                                                                                   'record_digest': '2597aeafff2e78212f12423f933f23c6e0a4107d80fc33cbf6d103f225bf938d'},
                                                                                                  {'role': 'author_effect_fence',
                                                                                                   'ordinal': 0,
                                                                                                   'record_ref': 'effect-fence-c2b3c-1',
                                                                                                   'record_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd'},
                                                                                                  {'role': 'author_command',
                                                                                                   'ordinal': 0,
                                                                                                   'record_ref': 'command-c2b3c-1',
                                                                                                   'record_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484'},
                                                                                                  {'role': 'authority_evaluation',
                                                                                                   'ordinal': 0,
                                                                                                   'record_ref': 'authority-evaluation-c2b3c-1',
                                                                                                   'record_digest': 'e484b72ed81cffbd5dfe80be4263c9c0bc66739a9a45d96d6dffcf748208164d'},
                                                                                                  {'role': 'initial_delivery_attempt',
                                                                                                   'ordinal': 0,
                                                                                                   'record_ref': 'delivery-attempt-c2b3c-1',
                                                                                                   'record_digest': '715b1baa3a9a6e0142f46433a0222a47ea42773b62b6c2e9a0dde2ab070f134e'},
                                                                                                  {'role': 'effect_head_postimage',
                                                                                                   'ordinal': 0,
                                                                                                   'record_ref': 'effect-intent-c2b3c-1',
                                                                                                   'record_digest': 'b302769593fd214cec86ada39e685cb97e46880e78973738c33e858e39a4e964'},
                                                                                                  {'role': 'delivery_head_postimage',
                                                                                                   'ordinal': 0,
                                                                                                   'record_ref': 'effect-intent-c2b3c-1',
                                                                                                   'record_digest': 'cc09294e960a7812807f2037c5066c6af263659f3409c2f4dcf75429e473bddf'})},
                                                 'canonical_json': '{"command_digest":"1d3473cc6cfebb93d75b09de1c7f1822cc8ee9e1800b026208116b1d8b1199a7","command_schema_id":"governed-execution.nwp-establish-development-author-effect-intent-command.v1","committed_at":"2026-08-22T12:34:56Z","decision_ref":"decision-c2b3a-1","graph_entries":[{"ordinal":0,"record_digest":"7018934d8724dcbc8cd3f93f603fca1682bf3d4b762293c4191e28e001cdd263","record_ref":"semantic-attempt-c2b3a-1","role":"semantic_attempt"},{"ordinal":0,"record_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","record_ref":"attempt-fence-c2b3c-1","role":"attempt_fence"},{"ordinal":0,"record_digest":"2597aeafff2e78212f12423f933f23c6e0a4107d80fc33cbf6d103f225bf938d","record_ref":"effect-intent-c2b3c-1","role":"author_effect_intent"},{"ordinal":0,"record_digest":"8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd","record_ref":"effect-fence-c2b3c-1","role":"author_effect_fence"},{"ordinal":0,"record_digest":"545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484","record_ref":"command-c2b3c-1","role":"author_command"},{"ordinal":0,"record_digest":"e484b72ed81cffbd5dfe80be4263c9c0bc66739a9a45d96d6dffcf748208164d","record_ref":"authority-evaluation-c2b3c-1","role":"authority_evaluation"},{"ordinal":0,"record_digest":"715b1baa3a9a6e0142f46433a0222a47ea42773b62b6c2e9a0dde2ab070f134e","record_ref":"delivery-attempt-c2b3c-1","role":"initial_delivery_attempt"},{"ordinal":0,"record_digest":"b302769593fd214cec86ada39e685cb97e46880e78973738c33e858e39a4e964","record_ref":"effect-intent-c2b3c-1","role":"effect_head_postimage"},{"ordinal":0,"record_digest":"cc09294e960a7812807f2037c5066c6af263659f3409c2f4dcf75429e473bddf","record_ref":"effect-intent-c2b3c-1","role":"delivery_head_postimage"}],"mutation_family":"establish_development_author_effect_intent","mutation_ref":"mutation-c2b3c-1","outcome":"committed","program_ref":"program-c2b3a-1","result_class":"development_author_effect_intent_established","result_decision_ref":null,"result_delivery_attempt_ref":"delivery-attempt-c2b3c-1","result_effect_fence_ref":"effect-fence-c2b3c-1","result_effect_intent_ref":"effect-intent-c2b3c-1","result_observation_ref":null,"result_program_version_ref":"program-version-c2b3a-1","result_projection_digest":"470d1ccf62ce6934320d3258385c5b8c38d066f7b8ac3a233f366f6c3c42bc39","result_semantic_attempt_ref":"semantic-attempt-c2b3a-1","schema_id":"governed-execution.nwp-development-mutation-receipt.v1"}',
                                                 'utf8_length': 2448,
                                                 'digest_domain': 'governed-execution.nwp-development-mutation-receipt.v1.identity',
                                                 'self_digest': 'bd7d6a8b10a01e779495d8bc140eed9937d71e511d7686dbdb368cdb29bbb41d'}},
 'graph_entries': ({'rank': 0,
                    'role': 'semantic_attempt',
                    'ordinal': 0,
                    'locator': {'program_ref': 'program-c2b3a-1',
                                'semantic_attempt_ref': 'semantic-attempt-c2b3a-1'},
                    'record_ref': 'semantic-attempt-c2b3a-1',
                    'record_digest': '7018934d8724dcbc8cd3f93f603fca1682bf3d4b762293c4191e28e001cdd263'},
                   {'rank': 1,
                    'role': 'attempt_fence',
                    'ordinal': 0,
                    'locator': {'program_ref': 'program-c2b3a-1',
                                'attempt_fence_ref': 'attempt-fence-c2b3c-1'},
                    'record_ref': 'attempt-fence-c2b3c-1',
                    'record_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed'},
                   {'rank': 2,
                    'role': 'author_effect_intent',
                    'ordinal': 0,
                    'locator': {'program_ref': 'program-c2b3a-1',
                                'effect_intent_ref': 'effect-intent-c2b3c-1'},
                    'record_ref': 'effect-intent-c2b3c-1',
                    'record_digest': '2597aeafff2e78212f12423f933f23c6e0a4107d80fc33cbf6d103f225bf938d'},
                   {'rank': 3,
                    'role': 'author_effect_fence',
                    'ordinal': 0,
                    'locator': {'program_ref': 'program-c2b3a-1',
                                'effect_fence_ref': 'effect-fence-c2b3c-1'},
                    'record_ref': 'effect-fence-c2b3c-1',
                    'record_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd'},
                   {'rank': 4,
                    'role': 'author_command',
                    'ordinal': 0,
                    'locator': {'program_ref': 'program-c2b3a-1', 'command_ref': 'command-c2b3c-1'},
                    'record_ref': 'command-c2b3c-1',
                    'record_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484'},
                   {'rank': 5,
                    'role': 'authority_evaluation',
                    'ordinal': 0,
                    'locator': {'program_ref': 'program-c2b3a-1',
                                'authority_evaluation_ref': 'authority-evaluation-c2b3c-1'},
                    'record_ref': 'authority-evaluation-c2b3c-1',
                    'record_digest': 'e484b72ed81cffbd5dfe80be4263c9c0bc66739a9a45d96d6dffcf748208164d'},
                   {'rank': 6,
                    'role': 'initial_delivery_attempt',
                    'ordinal': 0,
                    'locator': {'program_ref': 'program-c2b3a-1',
                                'delivery_attempt_ref': 'delivery-attempt-c2b3c-1'},
                    'record_ref': 'delivery-attempt-c2b3c-1',
                    'record_digest': '715b1baa3a9a6e0142f46433a0222a47ea42773b62b6c2e9a0dde2ab070f134e'},
                   {'rank': 7,
                    'role': 'effect_head_postimage',
                    'ordinal': 0,
                    'locator': {'program_ref': 'program-c2b3a-1',
                                'effect_intent_ref': 'effect-intent-c2b3c-1'},
                    'record_ref': 'effect-intent-c2b3c-1',
                    'record_digest': 'b302769593fd214cec86ada39e685cb97e46880e78973738c33e858e39a4e964'},
                   {'rank': 8,
                    'role': 'delivery_head_postimage',
                    'ordinal': 0,
                    'locator': {'program_ref': 'program-c2b3a-1',
                                'effect_intent_ref': 'effect-intent-c2b3c-1'},
                    'record_ref': 'effect-intent-c2b3c-1',
                    'record_digest': 'cc09294e960a7812807f2037c5066c6af263659f3409c2f4dcf75429e473bddf'}),
 'receipt_envelope': {'complete_mapping': {'schema_id': 'governed-execution.nwp-development-mutation-receipt.v1',
                                           'mutation_ref': 'mutation-c2b3c-1',
                                           'mutation_family': 'establish_development_author_effect_intent',
                                           'command_schema_id': 'governed-execution.nwp-establish-development-author-effect-intent-command.v1',
                                           'command_digest': '1d3473cc6cfebb93d75b09de1c7f1822cc8ee9e1800b026208116b1d8b1199a7',
                                           'program_ref': 'program-c2b3a-1',
                                           'decision_ref': 'decision-c2b3a-1',
                                           'result_program_version_ref': 'program-version-c2b3a-1',
                                           'result_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                           'result_effect_intent_ref': 'effect-intent-c2b3c-1',
                                           'result_effect_fence_ref': 'effect-fence-c2b3c-1',
                                           'result_delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                           'result_observation_ref': None,
                                           'result_decision_ref': None,
                                           'result_class': 'development_author_effect_intent_established',
                                           'result_projection_digest': '470d1ccf62ce6934320d3258385c5b8c38d066f7b8ac3a233f366f6c3c42bc39',
                                           'mutation_graph_digest': 'bd7d6a8b10a01e779495d8bc140eed9937d71e511d7686dbdb368cdb29bbb41d',
                                           'outcome': 'committed',
                                           'committed_at': '2026-08-22T12:34:56Z'},
                      'identity_excludes': ('mutation_graph_digest',),
                      'canonical_identity_mapping': {'schema_id': 'governed-execution.nwp-development-mutation-receipt.v1',
                                                     'mutation_ref': 'mutation-c2b3c-1',
                                                     'mutation_family': 'establish_development_author_effect_intent',
                                                     'command_schema_id': 'governed-execution.nwp-establish-development-author-effect-intent-command.v1',
                                                     'command_digest': '1d3473cc6cfebb93d75b09de1c7f1822cc8ee9e1800b026208116b1d8b1199a7',
                                                     'program_ref': 'program-c2b3a-1',
                                                     'decision_ref': 'decision-c2b3a-1',
                                                     'result_program_version_ref': 'program-version-c2b3a-1',
                                                     'result_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                                     'result_effect_intent_ref': 'effect-intent-c2b3c-1',
                                                     'result_effect_fence_ref': 'effect-fence-c2b3c-1',
                                                     'result_delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                                     'result_observation_ref': None,
                                                     'result_decision_ref': None,
                                                     'result_class': 'development_author_effect_intent_established',
                                                     'result_projection_digest': '470d1ccf62ce6934320d3258385c5b8c38d066f7b8ac3a233f366f6c3c42bc39',
                                                     'outcome': 'committed',
                                                     'committed_at': '2026-08-22T12:34:56Z',
                                                     'graph_entries': ({'role': 'semantic_attempt',
                                                                        'ordinal': 0,
                                                                        'record_ref': 'semantic-attempt-c2b3a-1',
                                                                        'record_digest': '7018934d8724dcbc8cd3f93f603fca1682bf3d4b762293c4191e28e001cdd263'},
                                                                       {'role': 'attempt_fence',
                                                                        'ordinal': 0,
                                                                        'record_ref': 'attempt-fence-c2b3c-1',
                                                                        'record_digest': '6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed'},
                                                                       {'role': 'author_effect_intent',
                                                                        'ordinal': 0,
                                                                        'record_ref': 'effect-intent-c2b3c-1',
                                                                        'record_digest': '2597aeafff2e78212f12423f933f23c6e0a4107d80fc33cbf6d103f225bf938d'},
                                                                       {'role': 'author_effect_fence',
                                                                        'ordinal': 0,
                                                                        'record_ref': 'effect-fence-c2b3c-1',
                                                                        'record_digest': '8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd'},
                                                                       {'role': 'author_command',
                                                                        'ordinal': 0,
                                                                        'record_ref': 'command-c2b3c-1',
                                                                        'record_digest': '545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484'},
                                                                       {'role': 'authority_evaluation',
                                                                        'ordinal': 0,
                                                                        'record_ref': 'authority-evaluation-c2b3c-1',
                                                                        'record_digest': 'e484b72ed81cffbd5dfe80be4263c9c0bc66739a9a45d96d6dffcf748208164d'},
                                                                       {'role': 'initial_delivery_attempt',
                                                                        'ordinal': 0,
                                                                        'record_ref': 'delivery-attempt-c2b3c-1',
                                                                        'record_digest': '715b1baa3a9a6e0142f46433a0222a47ea42773b62b6c2e9a0dde2ab070f134e'},
                                                                       {'role': 'effect_head_postimage',
                                                                        'ordinal': 0,
                                                                        'record_ref': 'effect-intent-c2b3c-1',
                                                                        'record_digest': 'b302769593fd214cec86ada39e685cb97e46880e78973738c33e858e39a4e964'},
                                                                       {'role': 'delivery_head_postimage',
                                                                        'ordinal': 0,
                                                                        'record_ref': 'effect-intent-c2b3c-1',
                                                                        'record_digest': 'cc09294e960a7812807f2037c5066c6af263659f3409c2f4dcf75429e473bddf'})},
                      'canonical_json': '{"command_digest":"1d3473cc6cfebb93d75b09de1c7f1822cc8ee9e1800b026208116b1d8b1199a7","command_schema_id":"governed-execution.nwp-establish-development-author-effect-intent-command.v1","committed_at":"2026-08-22T12:34:56Z","decision_ref":"decision-c2b3a-1","graph_entries":[{"ordinal":0,"record_digest":"7018934d8724dcbc8cd3f93f603fca1682bf3d4b762293c4191e28e001cdd263","record_ref":"semantic-attempt-c2b3a-1","role":"semantic_attempt"},{"ordinal":0,"record_digest":"6256370d14021a726185587d59f49b95a459a6da0d3b0cb55ecf054b37e10fed","record_ref":"attempt-fence-c2b3c-1","role":"attempt_fence"},{"ordinal":0,"record_digest":"2597aeafff2e78212f12423f933f23c6e0a4107d80fc33cbf6d103f225bf938d","record_ref":"effect-intent-c2b3c-1","role":"author_effect_intent"},{"ordinal":0,"record_digest":"8b952238c6278b9b19b327a70672a058033465aa9b43d862e09a10dbf2406bfd","record_ref":"effect-fence-c2b3c-1","role":"author_effect_fence"},{"ordinal":0,"record_digest":"545ceb0ad2ab8268d4bfc79a537d54c2ba7b2342313a90fac6f929a638dcb484","record_ref":"command-c2b3c-1","role":"author_command"},{"ordinal":0,"record_digest":"e484b72ed81cffbd5dfe80be4263c9c0bc66739a9a45d96d6dffcf748208164d","record_ref":"authority-evaluation-c2b3c-1","role":"authority_evaluation"},{"ordinal":0,"record_digest":"715b1baa3a9a6e0142f46433a0222a47ea42773b62b6c2e9a0dde2ab070f134e","record_ref":"delivery-attempt-c2b3c-1","role":"initial_delivery_attempt"},{"ordinal":0,"record_digest":"b302769593fd214cec86ada39e685cb97e46880e78973738c33e858e39a4e964","record_ref":"effect-intent-c2b3c-1","role":"effect_head_postimage"},{"ordinal":0,"record_digest":"cc09294e960a7812807f2037c5066c6af263659f3409c2f4dcf75429e473bddf","record_ref":"effect-intent-c2b3c-1","role":"delivery_head_postimage"}],"mutation_family":"establish_development_author_effect_intent","mutation_ref":"mutation-c2b3c-1","outcome":"committed","program_ref":"program-c2b3a-1","result_class":"development_author_effect_intent_established","result_decision_ref":null,"result_delivery_attempt_ref":"delivery-attempt-c2b3c-1","result_effect_fence_ref":"effect-fence-c2b3c-1","result_effect_intent_ref":"effect-intent-c2b3c-1","result_observation_ref":null,"result_program_version_ref":"program-version-c2b3a-1","result_projection_digest":"470d1ccf62ce6934320d3258385c5b8c38d066f7b8ac3a233f366f6c3c42bc39","result_semantic_attempt_ref":"semantic-attempt-c2b3a-1","schema_id":"governed-execution.nwp-development-mutation-receipt.v1"}',
                      'utf8_length': 2448,
                      'digest_domain': 'governed-execution.nwp-development-mutation-receipt.v1.identity',
                      'digest': 'bd7d6a8b10a01e779495d8bc140eed9937d71e511d7686dbdb368cdb29bbb41d'},
 'fresh_committed_result': {'mapping': {'disposition': 'committed',
                                        'mutation_ref': 'mutation-c2b3c-1',
                                        'command_digest': '1d3473cc6cfebb93d75b09de1c7f1822cc8ee9e1800b026208116b1d8b1199a7',
                                        'program_ref': 'program-c2b3a-1',
                                        'program_version_ref': 'program-version-c2b3a-1',
                                        'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                        'decision_ref': 'decision-c2b3a-1',
                                        'work_item_ref': 'work-item-c2b3a-1',
                                        'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                        'work_spec_ref': 'work-spec-c2b3a-1',
                                        'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                        'candidate_ref': 'candidate-c2b3a-1',
                                        'effect_intent_ref': 'effect-intent-c2b3c-1',
                                        'effect_fence_ref': 'effect-fence-c2b3c-1',
                                        'delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                        'transaction_timestamp': '2026-08-22T12:34:56Z'},
                            'canonical_json': '{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","candidate_ref":"candidate-c2b3a-1","command_digest":"1d3473cc6cfebb93d75b09de1c7f1822cc8ee9e1800b026208116b1d8b1199a7","decision_ref":"decision-c2b3a-1","delivery_attempt_ref":"delivery-attempt-c2b3c-1","disposition":"committed","effect_fence_ref":"effect-fence-c2b3c-1","effect_intent_ref":"effect-intent-c2b3c-1","mutation_ref":"mutation-c2b3c-1","program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","transaction_timestamp":"2026-08-22T12:34:56Z","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1","work_spec_ref":"work-spec-c2b3a-1"}',
                            'utf8_length': 711,
                            'digest_domain': 'governed-execution.nwp-development-author-effect-establishment-result.v1.identity',
                            'digest': '316bbbe2e5d5fe0b6d44f3adb99c5e2c36676fcdf183e1bbf0aba2f3eb51e14c'},
 'exact_replay_result': {'mapping': {'disposition': 'exact_replay',
                                     'mutation_ref': 'mutation-c2b3c-1',
                                     'command_digest': '1d3473cc6cfebb93d75b09de1c7f1822cc8ee9e1800b026208116b1d8b1199a7',
                                     'program_ref': 'program-c2b3a-1',
                                     'program_version_ref': 'program-version-c2b3a-1',
                                     'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                     'decision_ref': 'decision-c2b3a-1',
                                     'work_item_ref': 'work-item-c2b3a-1',
                                     'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                     'work_spec_ref': 'work-spec-c2b3a-1',
                                     'semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                     'candidate_ref': 'candidate-c2b3a-1',
                                     'effect_intent_ref': 'effect-intent-c2b3c-1',
                                     'effect_fence_ref': 'effect-fence-c2b3c-1',
                                     'delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                     'transaction_timestamp': '2026-08-22T12:34:56Z'},
                         'canonical_json': '{"accepted_intent_revision_ref":"accepted-intent-c2b3a-1","candidate_ref":"candidate-c2b3a-1","command_digest":"1d3473cc6cfebb93d75b09de1c7f1822cc8ee9e1800b026208116b1d8b1199a7","decision_ref":"decision-c2b3a-1","delivery_attempt_ref":"delivery-attempt-c2b3c-1","disposition":"exact_replay","effect_fence_ref":"effect-fence-c2b3c-1","effect_intent_ref":"effect-intent-c2b3c-1","mutation_ref":"mutation-c2b3c-1","program_ref":"program-c2b3a-1","program_version_ref":"program-version-c2b3a-1","semantic_attempt_ref":"semantic-attempt-c2b3a-1","transaction_timestamp":"2026-08-22T12:34:56Z","work_item_ref":"work-item-c2b3a-1","work_item_revision_ref":"work-item-revision-c2b3a-1","work_spec_ref":"work-spec-c2b3a-1"}',
                         'utf8_length': 714,
                         'digest_domain': 'governed-execution.nwp-development-author-effect-establishment-result.v1.identity',
                         'digest': 'cdcfff349dd542318f3b072e32e897fbc0b48206073002fed52cbd06778c8d87'},
 'result_semantic_equality': {'comparison_excludes': ('disposition',),
                              'fresh_disposition': 'committed',
                              'replay_disposition': 'exact_replay',
                              'all_other_ordered_fields_exactly_equal': True},
 'historical_postimages': {'effect_head': {'schema_id': 'governed-execution.nwp-development-effect-head.v1',
                                           'effect_intent_ref': 'effect-intent-c2b3c-1',
                                           'program_ref': 'program-c2b3a-1',
                                           'current_effect_fence_ref': 'effect-fence-c2b3c-1',
                                           'head_revision': 0,
                                           'effect_state': 'ready_for_delivery',
                                           'cancellation_effect_intent_ref': None,
                                           'updated_at': '2026-08-22T12:34:56Z',
                                           'head_digest': 'b302769593fd214cec86ada39e685cb97e46880e78973738c33e858e39a4e964'},
                           'delivery_head': {'schema_id': 'governed-execution.nwp-development-delivery-head.v1',
                                             'effect_intent_ref': 'effect-intent-c2b3c-1',
                                             'program_ref': 'program-c2b3a-1',
                                             'current_delivery_attempt_ref': 'delivery-attempt-c2b3c-1',
                                             'head_revision': 0,
                                             'delivery_state': 'planned',
                                             'updated_at': '2026-08-22T12:34:56Z',
                                             'head_digest': 'cc09294e960a7812807f2037c5066c6af263659f3409c2f4dcf75429e473bddf'},
                           'later_coherent_head_advancement_rewrites_vector': False},
 'privacy': {'contains_raw_objective_requirements_or_exclusions': False,
             'contains_prompt_transcript_credential_endpoint_or_workspace_content': False,
             'contains_retrieval_bearer': False,
             'safe_refs_and_digests_are_identity_and_correlation_only': True}}


EXPECTED_OWNER = {
    "coordinator_c2b3c_author_effect_contract": {
        "contract_identity": {
            "workstream": "COORDINATOR_C2B3C_AUTHOR_EFFECT_CONTRACT_FREEZE",
            "semantic_owner": ".docs/c2b-durable-development-state.md#39-coordinator-c2b3c-author-effect-contract-freeze",
            "classification": "ACCEPTED TARGET CONTRACT",
            "tranche_kind": "documentation and finite direct contract test only",
            "current_private_implementation": "VS1B route-neutral program genesis",
            "next_source_tranche": "C2B3D private atomic author-effect implementation",
            "C2B3D_source_status": "absent and unauthorized",
            "application_generation": 2,
            "terminal_migration": "0002_development_program_and_effect_state",
            "migration_0003_required": False,
            "production_source_changed_or_authorized": False,
            "public_surface_changed_or_authorized": False,
        },
        "status_reconciliation": {
            "vs1b_commit": "327aa4ef6f043a94f700374546fedc456027ae83",
            "branch": "trunk_dev",
            "upstream": "origin/trunk_dev",
            "remote_ref_directly_verified_at_commit": True,
            "independent_accept": "external provenance-bound report evidence for the exact pre-commit candidate",
            "post_acceptance_full_suite_commit_gate": "external validation report evidence: passed",
            "Git_owns": "commit object and remote-ref fact",
            "reports_are": "external evidence; not Git-intrinsic fact or Coordinator durable authority",
            "vs1b_current_status": "current committed private implementation",
            "vs1b_acceptance_subject": "exact VS1B pre-commit candidate",
            "c2b3c_current_status": "uncommitted contract-freeze candidate awaiting fresh independent re-audit",
            "c2b3c_independent_audit_accepted": False,
            "c2b3d_worker_and_external_effect_status": "absent and unauthorized",
            "sections_1_through_38": "byte-preserved tranche-time evidence",
            "supersedes_stale_current_status_only": (
                "C2B current implementation ending at C2B2",
                "all twelve private readers being production-unintegrated",
                "current mutation being transition and global-stop only",
                "migration-0003 inventory being selected",
                "program initialization source and private delegation being absent",
                "VS1B being pending fresh independent audit",
            ),
        },
        "basis_and_cardinality": {
            "basis_decision_kind": "initialize",
            "basis_decision_variant": "program_genesis",
            "program_version_number": 1,
            "initial_work_item_count": 1,
            "initial_work_item_revision_count": 1,
            "semantic_attempt_ref": "exact preassigned genesis value",
            "candidate_ref": "exact preassigned genesis value",
            "attempt_number": 1,
            "created_counts": {
                "program_version": 0,
                "work_item": 0,
                "work_item_revision": 0,
                "semantic_attempt": 1,
                "candidate_row": 0,
                "attempt_fence": 1,
                "author_effect_intent": 1,
                "author_effect_fence": 1,
                "author_command": 1,
                "authority_evaluation": 1,
                "initial_delivery_attempt": 1,
            },
            "candidate_identity_location": "development_semantic_attempts.candidate_ref",
            "second_work_attempt_candidate_command_or_effect_created": False,
        },
        "persisted_family": {
            "fresh_row_count": 10,
            "physical_write_order": (
                "development_semantic_attempts",
                "development_attempt_fences",
                "development_effect_intents",
                "development_effect_fences",
                "development_author_commands",
                "development_authority_evaluations",
                "development_effect_heads",
                "development_delivery_attempts",
                "development_delivery_heads",
                "development_mutation_receipts",
            ),
            "deferred_foreign_key_cycle": (
                "development_effect_intents.command_ref",
                "development_effect_fences.command_ref",
                "development_author_commands.effect_intent_ref",
                "development_author_commands.effect_fence_ref",
            ),
            "deferred_foreign_key_source": "existing migration 0002 only",
            "row_shape_and_digest_authority": "existing migration-0002 schema and C2B2 private row-value contracts",
            "one_whole_second_UTC_transaction_timestamp": True,
            "schema_or_migration_change": False,
        },
        "receipt_graph": {
            "entry_count": 9,
            "entries": (
                (0, "semantic_attempt", 0, "semantic_attempt_ref"),
                (1, "attempt_fence", 0, "attempt_fence_ref"),
                (2, "author_effect_intent", 0, "effect_intent_ref"),
                (3, "author_effect_fence", 0, "effect_fence_ref"),
                (4, "author_command", 0, "command_ref"),
                (5, "authority_evaluation", 0, "authority_evaluation_ref"),
                (6, "initial_delivery_attempt", 0, "delivery_attempt_ref"),
                (7, "effect_head_postimage", 0, "effect_intent_ref"),
                (8, "delivery_head_postimage", 0, "effect_intent_ref"),
            ),
            "same_effect_intent_ref_in_distinct_head_roles": True,
            "entry_digest_rule": "each entry binds its exact row ref and existing row self-digest; head roles bind the original postimage digest",
            "receipt_is_graph_envelope_not_entry": True,
            "receipt_rank_or_ordinal": None,
            "result_projection": {
                "schema_id": "governed-execution.nwp-establish-development-author-effect-intent-result.v1",
                "digest_domain": "governed-execution.nwp-establish-development-author-effect-intent-result.v1.identity",
                "ordered_fields": (
                    "schema_id",
                    "program_ref",
                    "decision_ref",
                    "result_program_version_ref",
                    "result_semantic_attempt_ref",
                    "result_effect_intent_ref",
                    "result_effect_fence_ref",
                    "result_delivery_attempt_ref",
                    "result_projection_digest",
                ),
                "identity_excludes": ("result_projection_digest",),
            },
            "receipt_scalar_envelope": {
                "mutation_family": "establish_development_author_effect_intent",
                "command_schema_id": "governed-execution.nwp-establish-development-author-effect-intent-command.v1",
                "decision_ref": "exact genesis decision_ref",
                "result_program_version_ref": "exact genesis program_version_ref",
                "result_semantic_attempt_ref": "exact created semantic_attempt_ref",
                "result_effect_intent_ref": "exact created effect_intent_ref",
                "result_effect_fence_ref": "exact created effect_fence_ref",
                "result_delivery_attempt_ref": "exact created delivery_attempt_ref",
                "result_observation_ref": None,
                "result_decision_ref": None,
                "result_class": "development_author_effect_intent_established",
                "outcome": "committed",
            },
        },
        "private_apply_result": {
            "semantic_name": "DevelopmentAuthorEffectEstablishmentResultV1",
            "digest_domain": "governed-execution.nwp-development-author-effect-establishment-result.v1.identity",
            "ordered_fields": (
                "disposition",
                "mutation_ref",
                "command_digest",
                "program_ref",
                "program_version_ref",
                "accepted_intent_revision_ref",
                "decision_ref",
                "work_item_ref",
                "work_item_revision_ref",
                "work_spec_ref",
                "semantic_attempt_ref",
                "candidate_ref",
                "effect_intent_ref",
                "effect_fence_ref",
                "delivery_attempt_ref",
                "transaction_timestamp",
            ),
            "dispositions": ("committed", "exact_replay"),
            "canonicalization": "existing canonical JSON sorted-keys compact UTF-8 rule",
            "fresh_and_replay_semantic_content_equal_except_disposition": True,
            "digest_is_persisted_receipt_authority_or_execution_permission": False,
        },
        "family_golden_vector": EXPECTED_FAMILY_GOLDEN_VECTOR,
        "locators_and_historical_postimages": {
            "bounded_LIMIT_2_locators": (
                ("semantic_attempt", "program_ref", "semantic_attempt_ref"),
                ("attempt_fence", "program_ref", "attempt_fence_ref"),
                ("author_effect_intent", "program_ref", "effect_intent_ref"),
                ("author_effect_fence", "program_ref", "effect_fence_ref"),
                ("author_command", "program_ref", "command_ref"),
                ("authority_evaluation", "program_ref", "authority_evaluation_ref"),
                ("initial_delivery_attempt", "program_ref", "delivery_attempt_ref"),
                ("effect_head_postimage", "program_ref", "effect_intent_ref"),
                ("delivery_head_postimage", "program_ref", "effect_intent_ref"),
                ("receipt", "program_ref", "mutation_ref"),
            ),
            "family_completeness": "all ten exact rows plus the exact nine-entry graph or fail closed",
            "original_head_postimages_remain_receipt_graph_members": True,
            "later_coherent_effect_or_delivery_head_advancement_invalidates_replay": False,
            "contradictory_historical_relation_apply": "database_integrity_failure",
            "contradictory_historical_relation_recovery": "unresolved",
        },
        "initial_postimages": {
            "semantic_attempt": {
                "attempt_number": 1,
                "attempt_phase": "established",
                "selection_decision_ref": "exact genesis decision_ref",
                "candidate_ref": "exact preassigned genesis candidate_ref",
            },
            "effect_intent": {
                "effect_class": "author_candidate",
                "basis_decision_ref": "exact genesis decision_ref",
                "command_ref": "exact sole originating command_ref",
                "cancellation_target_effect_intent_ref": None,
                "expected_target_effect_head_revision": None,
                "portable_capsule_digest": None,
            },
            "authority_evaluation": {
                "evaluation_scope": "effect",
                "evaluation_subject_ref": "exact effect_intent_ref",
                "semantic_attempt_ref": None,
                "effect_intent_ref": "exact effect_intent_ref",
                "authority_ref": "exact externally authored effect_authorization_ref",
                "authority_digest": "exact externally authored effect_authorization_digest",
                "authority_state": "pending",
                "reason_code": "external_verification_pending",
                "expires_at": None,
                "dispatch_eligibility": False,
                "dispatch_eligibility_is_semantic_conclusion_not_column": True,
            },
            "effect_head": {
                "head_revision": 0,
                "effect_state": "ready_for_delivery",
                "current_effect_fence_ref": "exact author effect_fence_ref",
                "cancellation_effect_intent_ref": None,
            },
            "delivery_attempt": {
                "delivery_kind": "initial",
                "delivery_number": 1,
                "predecessor_delivery_attempt_ref": None,
                "basis_decision_ref": "exact genesis decision_ref",
            },
            "delivery_head": {
                "head_revision": 0,
                "delivery_state": "planned",
                "current_delivery_attempt_ref": "exact initial delivery_attempt_ref",
            },
            "time_bearing_rows_use_one_transaction_timestamp": (
                "semantic_attempt.created_at",
                "attempt_fence.recorded_at",
                "effect_intent.created_at",
                "effect_fence.recorded_at",
                "author_command.recorded_at",
                "authority_evaluation.evaluated_at",
                "effect_head.updated_at",
                "delivery_attempt.recorded_at",
                "delivery_head.updated_at",
                "mutation_receipt.committed_at",
            ),
        },
        "route_boundary": {
            "route_neutral_values": (
                "AttemptFenceV1",
                "EffectFenceV1",
                "WorkerCommandV1",
            ),
            "route_specific_value": "DeliveryEnvelopeV1.adapter_kind",
            "initial_adapter_kind": "direct_local_bootstrap",
            "meaning": "persisted planned delivery selection only",
            "adapter_safe_correlation_ref": "safe correlation only",
            "not_selected_or_persisted": (
                "host",
                "endpoint",
                "transport",
                "process",
                "profile",
                "credential",
                "workspace",
                "invocation",
                "external request",
                "route-effect row",
                "dispatch eligibility",
                "ES compatibility",
                "ES admission",
            ),
            "third_adapter_kind_introduced": False,
            "safe_correlation_is_capability_credential_retrieval_or_dispatch_permission": False,
        },
        "authority_split": {
            "establishment_time": {
                "parent_standing_grant_owner": "external standing-policy authority",
                "attempt_and_effect_authorization_owner": "external authority",
                "typed_safe_attempt_binding": "exact AttemptFenceV1 carrying parent standing-grant and attempt-authorization bindings",
                "typed_safe_effect_binding": "exact DevelopmentEffectAuthorizationSafeBindingV1",
                "effect_binding_schema_id": "governed-execution.nwp-development-effect-authorization-safe-binding.v1",
                "effect_binding_digest_domain": "governed-execution.nwp-development-effect-authorization-safe-binding.v1.identity",
                "effect_binding_ordered_fields": (
                    "schema_id",
                    "parent_standing_grant_ref",
                    "parent_standing_grant_digest",
                    "effect_authorization_ref",
                    "effect_authorization_digest",
                    "attempt_fence_ref",
                    "attempt_fence_digest",
                    "semantic_attempt_ref",
                    "effect_intent_ref",
                    "effect_class",
                    "path_ceiling",
                    "effect_ceilings",
                    "expires_at",
                    "global_stop_ref",
                    "global_stop_version",
                    "safe_binding_digest",
                ),
                "effect_binding_identity_excludes": ("safe_binding_digest",),
                "effect_binding_is": "private transient prevalidated correlation evidence; not a new external authority protocol",
                "Coordinator_validates": (
                    "identity",
                    "correlation",
                    "expiry",
                    "global-stop ref and version",
                    "scope",
                    "paths",
                    "effect classes",
                    "ceilings",
                ),
                "Coordinator_mints_widens_renews_reinterprets_or_extends_authority": False,
            },
            "dispatch_time": {
                "current_verification_owner": "external verifier",
                "current_verification_state_at_establishment": "pending",
                "fresh_external_verification_immediately_before_launch": "mandatory",
                "Coordinator_authors_verified_blocked_stale_revoked_or_expired": False,
            },
            "fence_command_evaluation_or_planned_delivery_is_executable_permission": False,
        },
        "requirement_evidence": {
            "types": (
                (
                    "DevelopmentValidationRequirementEvidenceV1",
                    "governed-execution.nwp-development-validation-requirement-evidence.v1",
                    "governed-execution.nwp-development-validation-requirement-evidence.v1.identity",
                ),
                (
                    "DevelopmentReviewRequirementEvidenceV1",
                    "governed-execution.nwp-development-review-requirement-evidence.v1",
                    "governed-execution.nwp-development-review-requirement-evidence.v1.identity",
                ),
            ),
            "ordered_fields": (
                "schema_id",
                "requirement_ref",
                "requirement_digest",
                "work_spec_ref",
                "work_spec_digest",
                "safe_evidence_digest",
            ),
            "identity_excludes": ("safe_evidence_digest",),
            "rules": (
                "requirement_ref equals the corresponding exact WorkSpec requirement ref",
                "work_spec_ref and work_spec_digest equal the exact transient WorkSpec",
                "requirement_digest arrives only through the exact typed value",
                "bare digest or ref-digest tuple is invalid",
                "safe evidence is consistency and correlation evidence only",
                "only WorkerCommandV1 requirement refs and digests cross into durable rows",
            ),
            "new_requirement_evidence_row": False,
            "raw_requirement_content_crosses_durable_or_outward_boundary": False,
            "signature_PKI_or_external_authority_protocol_added": False,
        },
        "profile_references": {
            "capsule_profile_ref": "capsule-profile.regular-replace-v1",
            "redaction_profile_ref": "redaction.source-private-v1",
            "classification": "exact fixed C2B3C contract constants and opaque safe references",
            "validation_order": (
                "require exact built-in str",
                "require length from 1 through 96",
                "require full match of [A-Za-z0-9][A-Za-z0-9.-]*",
                "reject case-insensitive connector-, tunnel-, workspace-, org-, organization-, and user- prefixes",
                "require exact equality to the selected field constant",
            ),
            "provenance": (
                "not inferred from WorkSpec text",
                "not supplied by report text",
                "not minted by Coordinator",
                "not external-authority evidence",
                "not caller-selectable in C2B3C",
            ),
            "meaning": (
                "non-authoritative",
                "non-retrieval-bearing",
                "identity and correlation input only",
            ),
            "safe_command_positions": (
                "capsule_profile_ref immediately after capsule_schema_id",
                "redaction_profile_ref immediately after privacy_classification",
            ),
            "carried_through": (
                "fresh construction",
                "safe mutation-command canonical identity and digest",
                "WorkerCommandV1 construction",
                "persisted author-command row and row digest",
                "receipt-family verification",
                "exact replay reconstruction",
                "read-only recovery reconstruction",
                "family golden vector",
            ),
            "profile_refs_are_safe_command_identity_inputs": True,
            "profile_change_with_same_mutation_ref": "mutation_ref_reuse_conflict",
            "new_profile_evidence_registry_lookup_public_input_or_schema_field": False,
        },
        "safe_command": {
            "semantic_name": "DevelopmentAuthorEffectEstablishmentCommandV1",
            "mutation_family": "establish_development_author_effect_intent",
            "schema_id": "governed-execution.nwp-establish-development-author-effect-intent-command.v1",
            "digest_domain": "governed-execution.nwp-establish-development-author-effect-intent-command.v1.identity",
            "ordered_fields_with_exact_type_and_source": (
                ("schema_id", "exact str constant", "computed C2A semantic value or digest"),
                ("mutation_ref", "str", "exact preassigned identity"),
                ("program_ref", "str", "persisted genesis evidence"),
                ("program_version_ref", "str", "persisted genesis evidence"),
                ("program_version_number", "int excluding bool", "persisted genesis evidence"),
                ("accepted_intent_revision_ref", "str", "persisted genesis evidence"),
                ("work_item_ref", "str", "persisted genesis evidence"),
                ("work_item_revision_ref", "str", "persisted genesis evidence"),
                ("basis_decision_ref", "str", "persisted genesis evidence"),
                ("basis_decision_digest", "str", "persisted genesis evidence"),
                ("semantic_attempt_ref", "str", "exact preassigned identity"),
                ("candidate_ref", "str", "exact preassigned identity"),
                ("attempt_number", "int excluding bool", "persisted genesis evidence"),
                ("attempt_fence_ref", "str", "preassigned author-effect identity"),
                ("effect_intent_ref", "str", "preassigned author-effect identity"),
                ("effect_fence_ref", "str", "preassigned author-effect identity"),
                ("command_ref", "str", "preassigned author-effect identity"),
                ("authority_evaluation_ref", "str", "preassigned author-effect identity"),
                ("delivery_attempt_ref", "str", "preassigned author-effect identity"),
                ("adapter_safe_correlation_ref", "str", "preassigned author-effect identity"),
                ("coding_global_stop_ref", "str", "current coding-global-stop identity/version"),
                ("coding_global_stop_version", "int excluding bool", "current coding-global-stop identity/version"),
                ("capsule_schema_id", "exact str constant", "computed C2A semantic value or digest"),
                ("capsule_profile_ref", "exact str constant", "fixed C2B3C contract constant"),
                ("privacy_classification", "exact str constant", "computed C2A semantic value or digest"),
                ("redaction_profile_ref", "exact str constant", "fixed C2B3C contract constant"),
                ("work_spec_safe_projection", "exact DevelopmentWorkSpecSafeProjection", "transient WorkSpec reduction"),
                ("validation_requirement_evidence", "exact DevelopmentValidationRequirementEvidenceV1", "exact typed requirement evidence"),
                ("review_requirement_evidence", "exact DevelopmentReviewRequirementEvidenceV1", "exact typed requirement evidence"),
                ("attempt_fence", "exact AttemptFenceV1", "exact typed authority binding"),
                ("effect_authorization_safe_binding", "exact DevelopmentEffectAuthorizationSafeBindingV1", "exact typed authority binding"),
                ("worker_command", "exact WorkerCommandV1", "computed C2A semantic value or digest"),
                ("effect_fence", "exact EffectFenceV1", "computed C2A semantic value or digest"),
                ("delivery_envelope", "exact DeliveryEnvelopeV1", "computed C2A semantic value or digest"),
                ("command_digest", "str", "computed C2A semantic value or digest"),
            ),
            "identity_excludes": ("command_digest",),
            "profile_refs_are_identity_inputs": True,
            "unknown_optional_extension_or_metadata_fields": False,
            "digest_owner": "Coordinator sensitive reducer",
        },
        "command_and_fence_digest_closure": {
            "ordered_steps": (
                "construct WorkerCommandV1 identity with effect_fence_ref and without effect_fence_digest or command_digest",
                "compute WorkerCommandV1 command_digest",
                "construct EffectFenceV1 binding that exact WorkerCommandV1 command_digest",
                "compute EffectFenceV1 effect_fence_digest",
                "place the EffectFenceV1 effect_fence_digest into complete WorkerCommandV1",
                "construct the complete family safe command and compute its distinct command_digest",
            ),
            "exact_replay_requires": (
                "same family mutation_ref and family command_digest",
                "same WorkerCommandV1 command_ref and command_digest",
                "same postcomputed EffectFenceV1 effect_fence_digest",
            ),
            "recursive_digest_graph": False,
        },
        "effect_ceilings": {
            "attempt_fence": {
                "allowed_effect_classes_may_include": (
                    "author_candidate",
                    "validate_candidate",
                    "review_candidate",
                    "cancel_effect",
                    "local_git_commit",
                ),
                "aggregate_max_local_commits": 1,
                "aggregate_max_pushes": 0,
                "aggregate_max_pull_requests": 0,
                "aggregate_max_merges": 0,
                "aggregate_max_deployments": 0,
                "aggregate_max_publication_effects": 0,
            },
            "author_effect_fence_and_worker_command": {
                "effect_class": "author_candidate",
                "max_local_commits": 0,
                "max_pushes": 0,
                "max_remote_ref_mutations": 0,
                "max_pull_requests": 0,
                "max_merges": 0,
                "max_deployments": 0,
                "max_publication_effects": 0,
            },
            "later_local_Git_effect_requires": (
                "separate Coordinator decision",
                "separate command",
                "separate EffectFence",
                "separate transaction",
                "separate audit",
                "accepted ambiguity and reconciliation contract",
            ),
        },
        "fresh_construction_replay_and_recovery": {
            "fresh_private_call_requires": (
                "transient raw WorkSpecV1",
                "exact DevelopmentValidationRequirementEvidenceV1",
                "exact DevelopmentReviewRequirementEvidenceV1",
                "exact AttemptFenceV1",
                "exact DevelopmentEffectAuthorizationSafeBindingV1",
                "all exact preassigned refs",
                "exact current coding-global-stop ref and version",
                "fixed capsule-profile.regular-replace-v1 capsule profile ref",
                "fixed redaction.source-private-v1 redaction profile ref",
            ),
            "sensitive_reducer": (
                "constructs one complete safe command",
                "clears raw references before transaction-controller entry",
                "clears raw references before outward error",
            ),
            "apply_order_after_writer_fencing": (
                "receipt lookup",
                "exact replay or mutation-ref conflict",
                "current coding-global-stop read and version comparison",
                "active-stop rejection",
                "basis current-head identity and collision checks",
                "one immutable fresh plan and one COMMIT attempt",
            ),
            "exact_replay": (
                "verifies all ten exact rows and the exact nine-entry graph",
                "reconstructs original effect and delivery head postimages",
                "accepts later coherent head advancement",
                "calls no clock",
                "writes nothing",
                "consults no current route or external service",
                "reconstructs and verifies both fixed profile refs through the exact safe command and author-command row",
            ),
            "conflicts": (
                ("same mutation_ref different family command_digest", "mutation_ref_reuse_conflict"),
                ("coding-global-stop ref or version mismatch", "global_stop_version_conflict"),
                ("coding global stop active", "coding_global_stop_active"),
                ("preassigned identity occupied by non-exact family evidence", "semantic_identity_conflict"),
                ("persisted family contradiction", "database_integrity_failure"),
            ),
            "recovery": {
                "authority": "fresh fenced writer session",
                "transaction": "read-only",
                "complete_exact_family": "committed_exact",
                "all_selected_family_identities_absent": "definitely_not_committed",
                "partial_malformed_contradictory_colliding_or_unverifiable": "unresolved",
                "write_clock_external_IO_or_COMMIT": False,
                "reconstructs_and_verifies_both_fixed_profile_refs": True,
            },
            "automatic_semantic_retry_after_commit_outcome_unknown_or_unresolved": False,
            "separately_reconstructed_exact_safe_command_for_replay_or_recovery": True,
            "restart_safe_raw_input_or_command_custody_claimed": False,
        },
        "privacy": {
            "must_remain_outside_SQLite_transaction_receipt_result_report_log_and_error_graph": (
                "raw WorkSpecV1",
                "requirement contents",
                "objective",
                "requirements",
                "exclusions",
                "credentials",
                "endpoints",
                "paths outside the existing safe projection",
                "prompts",
                "transcripts",
                "workspace material",
                "retrieval bearer authority",
            ),
            "outward_error_forbids": (
                "raw exception args",
                "raw dictionaries",
                "raw cause",
                "raw context",
                "raw notes",
                "raw supported traceback containers",
            ),
            "ref_or_digest_is_retrieval_authority": False,
            "safe_values_are_identity_and_correlation_evidence_only": True,
        },
        "ownership": {
            "Coordinator": "durable progression decisions and exact private family persistence only",
            "external_standing_policy": "parent grant and subordinate authorization authorship",
            "external_verifier": "fresh dispatch-time verification",
            "worker": "process-separated implementation activity without Coordinator SQLite or writer access",
            "capsule_store": "private immutable candidate bytes and manifest custody",
            "validators_and_reviewers": "validation and review observations",
            "Git": "object and ref truth after a separately accepted Git effect",
            "Execution_Substrate": "later admission runtime lifecycle and reliable-submit authority",
            "adapter_or_transport": "no semantic acceptance or durable progression authority",
        },
        "explicit_nonimplementation": (
            "production source",
            "worker or supervisor",
            "subprocess or Codex invocation",
            "adapter or route implementation",
            "host endpoint transport profile credential or workspace selection",
            "external verification implementation",
            "capsule store",
            "validation or review execution",
            "Git operation",
            "Execution Substrate or Bridge call",
            "migration 0003 or schema change",
            "service API or IPC",
            "queue or scheduler",
            "public StateStore or WriterSession method",
            "package export",
            "acceptance repair replan observation cancellation or redelivery runtime",
        ),
        "c2b3d_gate": {
            "this_contract_requires_independent_acceptance": True,
            "separate_source_implementation_prompt_required": True,
            "C2B3D_currently_authorized": False,
            "worker_or_external_IO_currently_authorized": False,
        },
    }
}
EXPECTED_CONTRACT = EXPECTED_OWNER["coordinator_c2b3c_author_effect_contract"]
EXPECTED_TOP_LEVEL_KEYS = (
    "contract_identity",
    "status_reconciliation",
    "basis_and_cardinality",
    "persisted_family",
    "receipt_graph",
    "private_apply_result",
    "family_golden_vector",
    "locators_and_historical_postimages",
    "initial_postimages",
    "route_boundary",
    "authority_split",
    "requirement_evidence",
    "profile_references",
    "safe_command",
    "command_and_fence_digest_closure",
    "effect_ceilings",
    "fresh_construction_replay_and_recovery",
    "privacy",
    "ownership",
    "explicit_nonimplementation",
    "c2b3d_gate",
)
EXPECTED_ROWS = (
    "development_semantic_attempts",
    "development_attempt_fences",
    "development_effect_intents",
    "development_effect_fences",
    "development_author_commands",
    "development_authority_evaluations",
    "development_effect_heads",
    "development_delivery_attempts",
    "development_delivery_heads",
    "development_mutation_receipts",
)
EXPECTED_GRAPH = (
    (0, "semantic_attempt", 0, "semantic_attempt_ref"),
    (1, "attempt_fence", 0, "attempt_fence_ref"),
    (2, "author_effect_intent", 0, "effect_intent_ref"),
    (3, "author_effect_fence", 0, "effect_fence_ref"),
    (4, "author_command", 0, "command_ref"),
    (5, "authority_evaluation", 0, "authority_evaluation_ref"),
    (6, "initial_delivery_attempt", 0, "delivery_attempt_ref"),
    (7, "effect_head_postimage", 0, "effect_intent_ref"),
    (8, "delivery_head_postimage", 0, "effect_intent_ref"),
)
EXPECTED_REQUIREMENT_FIELDS = (
    "schema_id",
    "requirement_ref",
    "requirement_digest",
    "work_spec_ref",
    "work_spec_digest",
    "safe_evidence_digest",
)
EXPECTED_COMMAND_SOURCES = {
    "persisted genesis evidence",
    "exact preassigned identity",
    "transient WorkSpec reduction",
    "exact typed requirement evidence",
    "exact typed authority binding",
    "current coding-global-stop identity/version",
    "preassigned author-effect identity",
    "computed C2A semantic value or digest",
    "fixed C2B3C contract constant",
}
EXPECTED_STATUS_PHRASES = (
    "VS1B is the current committed private implementation at",
    "327aa4ef6f043a94f700374546fedc456027ae83",
    "is pushed to the directly verified `origin/trunk_dev` ref",
    "The exact VS1B pre-commit candidate received externally classified, provenance-bound independent acceptance",
    "its post-acceptance commit gate passed",
    "Git owns the commit/ref fact",
    "external evidence rather than Coordinator durable authority",
    "C2B3C is currently an uncommitted contract-freeze candidate awaiting fresh independent re-audit",
    "C2B3D source, worker execution, and production or external effects remain unauthorized",
)
CAPSULE_PROFILE_REF = "capsule-profile.regular-replace-v1"
REDACTION_PROFILE_REF = "redaction.source-private-v1"
SAFE_REF_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]*\Z")
SAFE_REF_RESERVED_PREFIXES = (
    "connector-",
    "tunnel-",
    "workspace-",
    "org-",
    "organization-",
    "user-",
)
EXPECTED_CANONICAL_VALUE_KEYS = (
    "work_spec_safe_projection",
    "validation_requirement_evidence",
    "review_requirement_evidence",
    "attempt_fence",
    "effect_authorization_safe_binding",
    "worker_command_identity_without_effect_fence_digest",
    "effect_fence",
    "complete_worker_command",
    "delivery_envelope",
    "safe_mutation_command",
    "result_projection",
)
EXPECTED_POSTIMAGE_COLUMNS = {
    "semantic_attempt": (
        "schema_id", "semantic_attempt_ref", "program_ref", "program_version_ref",
        "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref",
        "attempt_number", "candidate_ref", "attempt_phase", "selection_decision_ref",
        "created_at", "semantic_attempt_digest",
    ),
    "attempt_fence": (
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
    ),
    "author_effect_intent": (
        "schema_id", "effect_intent_ref", "program_ref", "program_version_ref",
        "semantic_attempt_ref", "effect_class", "candidate_ref", "command_ref",
        "basis_decision_ref", "cancellation_target_effect_intent_ref",
        "expected_target_effect_head_revision", "portable_capsule_digest",
        "created_at", "effect_intent_digest",
    ),
    "author_effect_fence": (
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
        "effect_max_deployments", "effect_max_local_commits",
        "effect_max_memory_bytes", "effect_max_merges",
        "effect_max_model_input_tokens", "effect_max_model_output_tokens",
        "effect_max_pull_requests", "effect_max_pushes", "effect_max_wall_seconds",
        "expires_at", "global_stop_ref", "global_stop_version",
        "portable_capsule_digest", "cancellation_target_effect_intent_ref",
        "cancellation_target_effect_fence_ref",
        "cancellation_target_effect_fence_digest", "effect_fence_digest",
        "recorded_at",
    ),
    "author_command": (
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
        "effect_max_changed_files", "effect_max_cost_microusd",
        "effect_max_cpu_seconds", "effect_max_deliveries", "effect_max_deployments",
        "effect_max_local_commits", "effect_max_memory_bytes", "effect_max_merges",
        "effect_max_model_input_tokens", "effect_max_model_output_tokens",
        "effect_max_pull_requests", "effect_max_pushes", "effect_max_wall_seconds",
        "privacy_classification", "redaction_profile_ref", "command_digest",
        "recorded_at",
    ),
    "authority_evaluation": (
        "schema_id", "authority_evaluation_ref", "program_ref", "evaluation_scope",
        "evaluation_subject_ref", "semantic_attempt_ref", "effect_intent_ref",
        "authority_ref", "authority_digest", "authority_state", "reason_code",
        "expires_at", "evaluated_at", "authority_evaluation_digest",
    ),
    "effect_head_postimage": (
        "schema_id", "effect_intent_ref", "program_ref", "current_effect_fence_ref",
        "head_revision", "effect_state", "cancellation_effect_intent_ref",
        "updated_at", "head_digest",
    ),
    "initial_delivery_attempt": (
        "schema_id", "delivery_attempt_ref", "program_ref", "program_version_ref",
        "command_ref", "command_digest", "semantic_attempt_ref", "effect_intent_ref",
        "attempt_fence_ref", "attempt_fence_digest", "effect_fence_ref",
        "effect_fence_digest", "adapter_kind", "adapter_safe_correlation_ref",
        "delivery_envelope_digest", "delivery_kind", "delivery_number",
        "predecessor_delivery_attempt_ref", "basis_decision_ref", "recorded_at",
        "delivery_attempt_digest",
    ),
    "delivery_head_postimage": (
        "schema_id", "effect_intent_ref", "program_ref",
        "current_delivery_attempt_ref", "head_revision", "delivery_state",
        "updated_at", "head_digest",
    ),
    "mutation_receipt": (
        "schema_id", "mutation_ref", "mutation_family", "command_schema_id",
        "command_digest", "program_ref", "decision_ref",
        "result_program_version_ref", "result_semantic_attempt_ref",
        "result_effect_intent_ref", "result_effect_fence_ref",
        "result_delivery_attempt_ref", "result_observation_ref",
        "result_decision_ref", "result_class", "result_projection_digest",
        "mutation_graph_digest", "outcome", "committed_at",
    ),
}


def _assert_owned_path(path: Path) -> None:
    assert path in {
        OWNER_PATH,
        README_PATH,
        AGENTS_PATH,
        READER_STATUS_PATH,
        INITIALIZATION_STATUS_PATH,
    }
    assert not path.is_symlink()
    assert path.resolve(strict=True) == path


def _read_owned_bytes(path: Path) -> bytes:
    _assert_owned_path(path)
    return path.read_bytes()


def _read_owned_path(path: Path) -> str:
    _assert_owned_path(path)
    return path.read_text(encoding="utf-8")


def _assert_exact_value(actual: object, expected: object, failure: str) -> None:
    assert type(actual) is type(expected), failure
    if type(expected) is dict:
        actual_mapping = actual
        expected_mapping = expected
        assert type(actual_mapping) is dict, failure
        assert type(expected_mapping) is dict, failure
        actual_items = tuple(actual_mapping.items())
        expected_items = tuple(expected_mapping.items())
        assert len(actual_items) == len(expected_items), failure
        for actual_item, expected_item in zip(
            actual_items, expected_items, strict=True
        ):
            actual_key, actual_value = actual_item
            expected_key, expected_value = expected_item
            _assert_exact_value(actual_key, expected_key, failure)
            _assert_exact_value(actual_value, expected_value, failure)
        return
    if type(expected) in (tuple, list):
        actual_sequence = actual
        expected_sequence = expected
        assert type(actual_sequence) is type(expected_sequence), failure
        assert len(actual_sequence) == len(expected_sequence), failure
        for actual_item, expected_item in zip(
            actual_sequence, expected_sequence, strict=True
        ):
            _assert_exact_value(actual_item, expected_item, failure)
        return
    if type(expected) in (str, int, bool) or expected is None:
        assert actual == expected, failure
        return
    raise AssertionError(failure)


def _mutable_container_ids(value: object) -> set[int]:
    if type(value) is dict:
        result = {id(value)}
        for key, item in value.items():
            result.update(_mutable_container_ids(key))
            result.update(_mutable_container_ids(item))
        return result
    if type(value) is list:
        result = {id(value)}
        for item in value:
            result.update(_mutable_container_ids(item))
        return result
    if type(value) is tuple:
        result: set[int] = set()
        for item in value:
            result.update(_mutable_container_ids(item))
        return result
    return set()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _domain_digest(domain: object, identity: object) -> str:
    assert type(domain) is str, "C2B3C_VECTOR_INVALID"
    canonical = _canonical_json(identity).encode("utf-8", errors="strict")
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + canonical).hexdigest()


def _parse_section_39_payload(payload_bytes: bytes) -> dict[str, object]:
    assert type(payload_bytes) is bytes, "C2B3C_OWNER_LITERAL_INVALID"
    try:
        payload = payload_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise AssertionError("C2B3C_OWNER_LITERAL_INVALID") from None
    try:
        expression = ast.parse(payload, mode="eval")
    except SyntaxError:
        raise AssertionError("C2B3C_OWNER_LITERAL_INVALID") from None
    assert type(expression) is ast.Expression, "C2B3C_OWNER_LITERAL_INVALID"
    assert type(expression.body) is ast.Dict, "C2B3C_OWNER_LITERAL_INVALID"
    try:
        parsed = ast.literal_eval(expression.body)
    except (TypeError, ValueError):
        raise AssertionError("C2B3C_OWNER_LITERAL_INVALID") from None
    assert type(parsed) is dict, "C2B3C_OWNER_LITERAL_INVALID"
    assert tuple(parsed) == (
        "coordinator_c2b3c_author_effect_contract",
    ), "C2B3C_OWNER_LITERAL_INVALID"
    value = parsed["coordinator_c2b3c_author_effect_contract"]
    assert type(value) is dict, "C2B3C_OWNER_LITERAL_INVALID"
    _assert_exact_value(value, EXPECTED_CONTRACT, "C2B3C_CONTRACT_INVALID")
    return value


def _section_39_contract(source_bytes: bytes | None = None) -> dict[str, object]:
    source = _read_owned_bytes(OWNER_PATH) if source_bytes is None else source_bytes
    assert type(source) is bytes, "C2B3C_PROLOGUE_INVALID"
    section_heading_bytes = SECTION_HEADING.encode("utf-8", errors="strict")
    begin_marker_bytes = BEGIN_MARKER.encode("utf-8", errors="strict")
    end_marker_bytes = END_MARKER.encode("utf-8", errors="strict")
    opening_fence_bytes = b"```python\n"
    closing_fence_bytes = b"\n```\n\n"
    expected_prologue_bytes = EXPECTED_SECTION_39_PROLOGUE.encode(
        "utf-8", errors="strict"
    )
    expected_trailing_prose_bytes = EXPECTED_TRAILING_PROSE.encode(
        "utf-8", errors="strict"
    )
    assert expected_prologue_bytes.endswith(opening_fence_bytes), (
        "C2B3C_PROLOGUE_INVALID"
    )
    assert source.count(section_heading_bytes) == 1, "C2B3C_PROLOGUE_INVALID"
    assert source.count(begin_marker_bytes) == 1, "C2B3C_PROLOGUE_INVALID"
    assert source.count(end_marker_bytes) == 1, "C2B3C_PROLOGUE_INVALID"
    section_start = source.index(section_heading_bytes)
    prologue_end = section_start + len(expected_prologue_bytes)
    assert (
        source[section_start:prologue_end] == expected_prologue_bytes
    ), "C2B3C_PROLOGUE_INVALID"
    remainder = source[prologue_end:]
    closing_boundary = closing_fence_bytes + end_marker_bytes
    assert remainder.count(closing_boundary) == 1, "C2B3C_BOUNDARY_INVALID"
    payload_bytes, after = remainder.split(closing_boundary, 1)
    assert after == expected_trailing_prose_bytes, "C2B3C_BOUNDARY_INVALID"
    assert source.endswith(b"\n"), "C2B3C_BOUNDARY_INVALID"
    assert len(payload_bytes) == EXPECTED_SECTION_39_PAYLOAD_UTF8_LENGTH, (
        "C2B3C_PAYLOAD_BYTES_INVALID"
    )
    assert hashlib.sha256(payload_bytes).hexdigest() == (
        EXPECTED_SECTION_39_PAYLOAD_SHA256
    ), "C2B3C_PAYLOAD_BYTES_INVALID"
    return _parse_section_39_payload(payload_bytes)


def _assert_exact_contract(value: object) -> None:
    assert type(value) is dict, "C2B3C_CONTRACT_INVALID"
    assert tuple(value) == EXPECTED_TOP_LEVEL_KEYS, "C2B3C_CONTRACT_INVALID"
    _assert_exact_value(value, EXPECTED_CONTRACT, "C2B3C_CONTRACT_INVALID")


def _assert_safe_ref(value: object) -> None:
    assert type(value) is str, "C2B3C_PROFILE_REFS_INVALID"
    assert 1 <= len(value) <= 96, "C2B3C_PROFILE_REFS_INVALID"
    assert SAFE_REF_PATTERN.fullmatch(value) is not None, "C2B3C_PROFILE_REFS_INVALID"
    assert not value.lower().startswith(
        SAFE_REF_RESERVED_PREFIXES
    ), "C2B3C_PROFILE_REFS_INVALID"


def _assert_profile_contract(candidate: object) -> None:
    assert type(candidate) is dict, "C2B3C_PROFILE_REFS_INVALID"
    profile = candidate["profile_references"]
    _assert_exact_value(
        profile,
        EXPECTED_CONTRACT["profile_references"],
        "C2B3C_PROFILE_REFS_INVALID",
    )
    _assert_safe_ref(profile["capsule_profile_ref"])
    _assert_safe_ref(profile["redaction_profile_ref"])
    assert profile["capsule_profile_ref"] == CAPSULE_PROFILE_REF, (
        "C2B3C_PROFILE_REFS_INVALID"
    )
    assert profile["redaction_profile_ref"] == REDACTION_PROFILE_REF, (
        "C2B3C_PROFILE_REFS_INVALID"
    )
    fields = candidate["safe_command"]["ordered_fields_with_exact_type_and_source"]
    names = tuple(item[0] for item in fields)
    assert names[names.index("capsule_schema_id") + 1] == "capsule_profile_ref", (
        "C2B3C_PROFILE_REFS_INVALID"
    )
    assert (
        names[names.index("privacy_classification") + 1]
        == "redaction_profile_ref"
    ), "C2B3C_PROFILE_REFS_INVALID"
    vector = candidate["family_golden_vector"]
    safe_record = vector["canonical_values"]["safe_mutation_command"]
    safe_complete = safe_record["complete_mapping"]
    safe_identity = safe_record["canonical_identity_mapping"]
    assert tuple(safe_complete) == names, "C2B3C_PROFILE_REFS_INVALID"
    assert tuple(safe_identity) == tuple(
        field for field in names if field != "command_digest"
    ), "C2B3C_PROFILE_REFS_INVALID"
    worker_mapping = vector["canonical_values"]["complete_worker_command"][
        "complete_mapping"
    ]
    author_row = vector["persisted_postimages"]["author_command"]
    vector_profiles = vector["inputs"]["profile_references"]
    for field, expected in (
        ("capsule_profile_ref", CAPSULE_PROFILE_REF),
        ("redaction_profile_ref", REDACTION_PROFILE_REF),
    ):
        assert field in safe_identity, "C2B3C_PROFILE_REFS_INVALID"
        assert safe_complete[field] == expected, "C2B3C_PROFILE_REFS_INVALID"
        assert safe_identity[field] == expected, "C2B3C_PROFILE_REFS_INVALID"
        assert worker_mapping[field] == expected, "C2B3C_PROFILE_REFS_INVALID"
        assert author_row[field] == expected, "C2B3C_PROFILE_REFS_INVALID"
        assert vector_profiles[field] == expected, "C2B3C_PROFILE_REFS_INVALID"


def _assert_frozen_bytes_and_digest(
    *,
    identity: object,
    canonical_text: object,
    utf8_length: object,
    domain: object,
    digest: object,
) -> None:
    assert type(canonical_text) is str, "C2B3C_VECTOR_INVALID"
    assert type(utf8_length) is int, "C2B3C_VECTOR_INVALID"
    assert type(domain) is str, "C2B3C_VECTOR_INVALID"
    assert type(digest) is str, "C2B3C_VECTOR_INVALID"
    observed_text = _canonical_json(identity)
    assert observed_text == canonical_text, "C2B3C_VECTOR_INVALID"
    assert len(observed_text.encode("utf-8")) == utf8_length, (
        "C2B3C_VECTOR_INVALID"
    )
    assert _domain_digest(domain, identity) == digest, "C2B3C_VECTOR_INVALID"


def _assert_canonical_record(record: object) -> None:
    assert type(record) is dict, "C2B3C_VECTOR_INVALID"
    assert tuple(record) == (
        "complete_mapping",
        "identity_excludes",
        "canonical_identity_mapping",
        "canonical_json",
        "utf8_length",
        "digest_domain",
        "digest",
    ), "C2B3C_VECTOR_INVALID"
    complete = record["complete_mapping"]
    exclusions = record["identity_excludes"]
    identity = record["canonical_identity_mapping"]
    assert type(complete) is dict, "C2B3C_VECTOR_INVALID"
    assert type(exclusions) is tuple, "C2B3C_VECTOR_INVALID"
    assert all(type(field) is str for field in exclusions), "C2B3C_VECTOR_INVALID"
    derived = {key: value for key, value in complete.items() if key not in exclusions}
    _assert_exact_value(derived, identity, "C2B3C_VECTOR_INVALID")
    _assert_frozen_bytes_and_digest(
        identity=identity,
        canonical_text=record["canonical_json"],
        utf8_length=record["utf8_length"],
        domain=record["digest_domain"],
        digest=record["digest"],
    )


def _assert_complete_worker_command_record(record: object) -> None:
    assert type(record) is dict, "C2B3C_VECTOR_INVALID"
    assert tuple(record) == (
        "complete_mapping",
        "identity_excludes",
        "canonical_identity_mapping",
        "identity_canonical_json",
        "identity_utf8_length",
        "identity_raw_sha256",
        "complete_record_canonical_json",
        "complete_record_utf8_length",
        "complete_record_raw_sha256",
        "digest_domain",
        "digest",
    ), "C2B3C_VECTOR_INVALID"
    complete = record["complete_mapping"]
    exclusions = record["identity_excludes"]
    identity = record["canonical_identity_mapping"]
    assert type(complete) is dict, "C2B3C_VECTOR_INVALID"
    assert type(exclusions) is tuple, "C2B3C_VECTOR_INVALID"
    assert exclusions == (
        "effect_fence_digest",
        "command_digest",
    ), "C2B3C_VECTOR_INVALID"
    derived = {key: value for key, value in complete.items() if key not in exclusions}
    _assert_exact_value(derived, identity, "C2B3C_VECTOR_INVALID")
    assert len(identity) == 37, "C2B3C_VECTOR_INVALID"
    assert len(complete) == 39, "C2B3C_VECTOR_INVALID"
    _assert_frozen_bytes_and_digest(
        identity=identity,
        canonical_text=record["identity_canonical_json"],
        utf8_length=record["identity_utf8_length"],
        domain=record["digest_domain"],
        digest=record["digest"],
    )
    identity_text = record["identity_canonical_json"]
    identity_raw_sha256 = record["identity_raw_sha256"]
    complete_text = record["complete_record_canonical_json"]
    complete_length = record["complete_record_utf8_length"]
    complete_raw_sha256 = record["complete_record_raw_sha256"]
    assert type(identity_raw_sha256) is str, "C2B3C_VECTOR_INVALID"
    assert type(complete_text) is str, "C2B3C_VECTOR_INVALID"
    assert type(complete_length) is int, "C2B3C_VECTOR_INVALID"
    assert type(complete_raw_sha256) is str, "C2B3C_VECTOR_INVALID"
    assert hashlib.sha256(identity_text.encode("utf-8")).hexdigest() == (
        identity_raw_sha256
    ), "C2B3C_VECTOR_INVALID"
    observed_complete_text = _canonical_json(complete)
    assert observed_complete_text == complete_text, "C2B3C_VECTOR_INVALID"
    assert len(observed_complete_text.encode("utf-8")) == complete_length, (
        "C2B3C_VECTOR_INVALID"
    )
    assert hashlib.sha256(observed_complete_text.encode("utf-8")).hexdigest() == (
        complete_raw_sha256
    ), "C2B3C_VECTOR_INVALID"
    assert complete_text != identity_text, "C2B3C_VECTOR_INVALID"
    assert complete["command_digest"] == record["digest"], "C2B3C_VECTOR_INVALID"


def _assert_family_vector(candidate: object) -> None:
    assert type(candidate) is dict, "C2B3C_VECTOR_INVALID"
    assert tuple(candidate) == (
        "vector_id",
        "vector_version",
        "transaction_timestamp",
        "expires_at",
        "inputs",
        "canonical_values",
        "persisted_postimages",
        "postimage_digest_specs",
        "graph_entries",
        "receipt_envelope",
        "fresh_committed_result",
        "exact_replay_result",
        "result_semantic_equality",
        "historical_postimages",
        "privacy",
    ), "C2B3C_VECTOR_INVALID"
    assert candidate["vector_id"] == "c2b3c-author-effect-family-v1", (
        "C2B3C_VECTOR_INVALID"
    )
    assert type(candidate["vector_version"]) is int, "C2B3C_VECTOR_INVALID"
    assert candidate["vector_version"] == 1, "C2B3C_VECTOR_INVALID"

    canonical_values = candidate["canonical_values"]
    assert type(canonical_values) is dict, "C2B3C_VECTOR_INVALID"
    assert tuple(canonical_values) == EXPECTED_CANONICAL_VALUE_KEYS, (
        "C2B3C_VECTOR_INVALID"
    )
    digest_fields = {
        "work_spec_safe_projection": "safe_projection_digest",
        "validation_requirement_evidence": "safe_evidence_digest",
        "review_requirement_evidence": "safe_evidence_digest",
        "attempt_fence": "attempt_fence_digest",
        "effect_authorization_safe_binding": "safe_binding_digest",
        "effect_fence": "effect_fence_digest",
        "complete_worker_command": "command_digest",
        "delivery_envelope": "delivery_envelope_digest",
        "safe_mutation_command": "command_digest",
        "result_projection": "result_projection_digest",
    }
    for name, record in canonical_values.items():
        if name == "complete_worker_command":
            _assert_complete_worker_command_record(record)
        else:
            _assert_canonical_record(record)
        digest_field = digest_fields.get(name)
        if digest_field is not None:
            assert record["complete_mapping"][digest_field] == record["digest"], (
                "C2B3C_VECTOR_INVALID"
            )
    worker_identity = canonical_values[
        "worker_command_identity_without_effect_fence_digest"
    ]
    complete_worker = canonical_values["complete_worker_command"]
    _assert_exact_value(
        worker_identity["canonical_identity_mapping"],
        complete_worker["canonical_identity_mapping"],
        "C2B3C_VECTOR_INVALID",
    )
    assert worker_identity["canonical_json"] == complete_worker[
        "identity_canonical_json"
    ], (
        "C2B3C_VECTOR_INVALID"
    )
    assert worker_identity["utf8_length"] == complete_worker[
        "identity_utf8_length"
    ], "C2B3C_VECTOR_INVALID"
    assert worker_identity["digest"] == complete_worker["digest"], (
        "C2B3C_VECTOR_INVALID"
    )
    assert complete_worker["complete_record_canonical_json"] != complete_worker[
        "identity_canonical_json"
    ], "C2B3C_VECTOR_INVALID"
    assert complete_worker["complete_mapping"]["command_digest"] == worker_identity[
        "digest"
    ], "C2B3C_VECTOR_INVALID"
    assert complete_worker["complete_mapping"]["effect_fence_digest"] == (
        canonical_values["effect_fence"]["digest"]
    ), "C2B3C_VECTOR_INVALID"

    postimages = candidate["persisted_postimages"]
    specs = candidate["postimage_digest_specs"]
    assert type(postimages) is dict, "C2B3C_VECTOR_INVALID"
    assert type(specs) is dict, "C2B3C_VECTOR_INVALID"
    assert tuple(postimages) == tuple(EXPECTED_POSTIMAGE_COLUMNS), (
        "C2B3C_VECTOR_INVALID"
    )
    assert tuple(specs) == tuple(EXPECTED_POSTIMAGE_COLUMNS), (
        "C2B3C_VECTOR_INVALID"
    )
    assert len(postimages) == 10, "C2B3C_VECTOR_INVALID"
    for name, expected_columns in EXPECTED_POSTIMAGE_COLUMNS.items():
        row = postimages[name]
        spec = specs[name]
        assert type(row) is dict, "C2B3C_VECTOR_INVALID"
        assert tuple(row) == expected_columns, "C2B3C_VECTOR_INVALID"
        assert type(spec) is dict, "C2B3C_VECTOR_INVALID"
        assert tuple(spec) == (
            "self_digest_field",
            "canonical_identity_mapping",
            "canonical_json",
            "utf8_length",
            "digest_domain",
            "self_digest",
        ), "C2B3C_VECTOR_INVALID"
        digest_field = spec["self_digest_field"]
        assert type(digest_field) is str, "C2B3C_VECTOR_INVALID"
        assert row[digest_field] == spec["self_digest"], "C2B3C_VECTOR_INVALID"
        _assert_frozen_bytes_and_digest(
            identity=spec["canonical_identity_mapping"],
            canonical_text=spec["canonical_json"],
            utf8_length=spec["utf8_length"],
            domain=spec["digest_domain"],
            digest=spec["self_digest"],
        )

    entries = candidate["graph_entries"]
    assert type(entries) is tuple, "C2B3C_VECTOR_INVALID"
    assert len(entries) == 9, "C2B3C_VECTOR_INVALID"
    program_ref = candidate["inputs"]["committed_vs1b_genesis_basis"][
        "program_ref"
    ]
    graph_role_rows = (
        ("semantic_attempt", "semantic_attempt", "semantic_attempt_digest"),
        ("attempt_fence", "attempt_fence", "attempt_fence_digest"),
        ("author_effect_intent", "author_effect_intent", "effect_intent_digest"),
        ("author_effect_fence", "author_effect_fence", "effect_fence_digest"),
        ("author_command", "author_command", "command_digest"),
        (
            "authority_evaluation",
            "authority_evaluation",
            "authority_evaluation_digest",
        ),
        (
            "initial_delivery_attempt",
            "initial_delivery_attempt",
            "delivery_attempt_digest",
        ),
        ("effect_head_postimage", "effect_head_postimage", "head_digest"),
        ("delivery_head_postimage", "delivery_head_postimage", "head_digest"),
    )
    primitive_entries = []
    for entry, expected_graph, role_row in zip(
        entries, EXPECTED_GRAPH, graph_role_rows, strict=True
    ):
        assert type(entry) is dict, "C2B3C_VECTOR_INVALID"
        assert tuple(entry) == (
            "rank", "role", "ordinal", "locator", "record_ref", "record_digest"
        ), "C2B3C_VECTOR_INVALID"
        expected_rank, expected_role, expected_ordinal, locator_field = expected_graph
        assert entry["rank"] == expected_rank, "C2B3C_VECTOR_INVALID"
        assert entry["role"] == expected_role, "C2B3C_VECTOR_INVALID"
        assert entry["ordinal"] == expected_ordinal, "C2B3C_VECTOR_INVALID"
        expected_locator = {
            "program_ref": program_ref,
            locator_field: entry["record_ref"],
        }
        _assert_exact_value(
            entry["locator"], expected_locator, "C2B3C_VECTOR_INVALID"
        )
        expected_role_name, row_name, digest_field = role_row
        assert entry["role"] == expected_role_name, "C2B3C_VECTOR_INVALID"
        assert entry["record_digest"] == postimages[row_name][digest_field], (
            "C2B3C_VECTOR_INVALID"
        )
        primitive_entries.append(
            {
                "role": entry["role"],
                "ordinal": entry["ordinal"],
                "record_ref": entry["record_ref"],
                "record_digest": entry["record_digest"],
            }
        )
    assert tuple(entry["rank"] for entry in entries) == tuple(range(9)), (
        "C2B3C_VECTOR_INVALID"
    )
    assert "receipt" not in tuple(entry["role"] for entry in entries), (
        "C2B3C_VECTOR_INVALID"
    )

    receipt = candidate["receipt_envelope"]
    assert type(receipt) is dict, "C2B3C_VECTOR_INVALID"
    assert tuple(receipt) == (
        "complete_mapping",
        "identity_excludes",
        "canonical_identity_mapping",
        "canonical_json",
        "utf8_length",
        "digest_domain",
        "digest",
    ), "C2B3C_VECTOR_INVALID"
    _assert_exact_value(
        receipt["complete_mapping"],
        postimages["mutation_receipt"],
        "C2B3C_VECTOR_INVALID",
    )
    assert receipt["identity_excludes"] == ("mutation_graph_digest",), (
        "C2B3C_VECTOR_INVALID"
    )
    receipt_identity = {
        key: value
        for key, value in postimages["mutation_receipt"].items()
        if key != "mutation_graph_digest"
    }
    receipt_identity["graph_entries"] = tuple(primitive_entries)
    _assert_exact_value(
        receipt_identity,
        receipt["canonical_identity_mapping"],
        "C2B3C_VECTOR_INVALID",
    )
    _assert_frozen_bytes_and_digest(
        identity=receipt_identity,
        canonical_text=receipt["canonical_json"],
        utf8_length=receipt["utf8_length"],
        domain=receipt["digest_domain"],
        digest=receipt["digest"],
    )
    assert receipt["digest"] == postimages["mutation_receipt"][
        "mutation_graph_digest"
    ], "C2B3C_VECTOR_INVALID"

    result_fields = EXPECTED_CONTRACT["private_apply_result"]["ordered_fields"]
    results = (
        (candidate["fresh_committed_result"], "committed"),
        (candidate["exact_replay_result"], "exact_replay"),
    )
    for result, disposition in results:
        assert type(result) is dict, "C2B3C_VECTOR_INVALID"
        assert tuple(result) == (
            "mapping", "canonical_json", "utf8_length", "digest_domain", "digest"
        ), "C2B3C_VECTOR_INVALID"
        assert tuple(result["mapping"]) == result_fields, "C2B3C_VECTOR_INVALID"
        assert result["mapping"]["disposition"] == disposition, (
            "C2B3C_VECTOR_INVALID"
        )
        assert result["digest_domain"] == EXPECTED_CONTRACT[
            "private_apply_result"
        ]["digest_domain"], "C2B3C_VECTOR_INVALID"
        _assert_frozen_bytes_and_digest(
            identity=result["mapping"],
            canonical_text=result["canonical_json"],
            utf8_length=result["utf8_length"],
            domain=result["digest_domain"],
            digest=result["digest"],
        )
    fresh_semantic = {
        key: value
        for key, value in candidate["fresh_committed_result"]["mapping"].items()
        if key != "disposition"
    }
    replay_semantic = {
        key: value
        for key, value in candidate["exact_replay_result"]["mapping"].items()
        if key != "disposition"
    }
    _assert_exact_value(
        fresh_semantic, replay_semantic, "C2B3C_VECTOR_INVALID"
    )
    assert candidate["result_semantic_equality"][
        "all_other_ordered_fields_exactly_equal"
    ] is True, "C2B3C_VECTOR_INVALID"
    _assert_exact_value(
        candidate["historical_postimages"]["effect_head"],
        postimages["effect_head_postimage"],
        "C2B3C_VECTOR_INVALID",
    )
    _assert_exact_value(
        candidate["historical_postimages"]["delivery_head"],
        postimages["delivery_head_postimage"],
        "C2B3C_VECTOR_INVALID",
    )
    assert candidate["historical_postimages"][
        "later_coherent_head_advancement_rewrites_vector"
    ] is False, "C2B3C_VECTOR_INVALID"
    assert all(value is False for key, value in candidate["privacy"].items() if key.startswith("contains_")), "C2B3C_VECTOR_INVALID"
    assert candidate["privacy"][
        "safe_refs_and_digests_are_identity_and_correlation_only"
    ] is True, "C2B3C_VECTOR_INVALID"


def _assert_current_status(text: object) -> None:
    assert type(text) is str, "C2B3C_STATUS_INVALID"
    current = " ".join(text.split())
    assert "C2B3C independent audit accepted" not in current, (
        "C2B3C_STATUS_INVALID"
    )
    for phrase in EXPECTED_STATUS_PHRASES:
        assert phrase in current, "C2B3C_STATUS_INVALID"


def test_section_39_direct_literal_matches_independent_expected_contract() -> None:
    value = _section_39_contract()
    _assert_exact_contract(value)
    _assert_profile_contract(value)
    identity = value["contract_identity"]
    assert identity["classification"] == "ACCEPTED TARGET CONTRACT"
    assert identity["C2B3D_source_status"] == "absent and unauthorized"
    assert identity["terminal_migration"] == (
        "0002_development_program_and_effect_state"
    )
    assert identity["migration_0003_required"] is False
    status = value["status_reconciliation"]
    assert status["remote_ref_directly_verified_at_commit"] is True
    assert status["c2b3c_independent_audit_accepted"] is False
    assert status["sections_1_through_38"] == "byte-preserved tranche-time evidence"


def test_family_rows_graph_locators_and_initial_postimages_are_exact() -> None:
    value = _section_39_contract()
    family = value["persisted_family"]
    assert family["fresh_row_count"] == 10
    _assert_exact_value(
        family["physical_write_order"], EXPECTED_ROWS, "C2B3C_CONTRACT_INVALID"
    )
    assert family["schema_or_migration_change"] is False
    graph = value["receipt_graph"]
    assert graph["entry_count"] == 9
    _assert_exact_value(graph["entries"], EXPECTED_GRAPH, "C2B3C_CONTRACT_INVALID")
    assert graph["receipt_is_graph_envelope_not_entry"] is True
    assert graph["receipt_rank_or_ordinal"] is None
    assert len(value["locators_and_historical_postimages"]["bounded_LIMIT_2_locators"]) == 10
    postimages = value["initial_postimages"]
    _assert_exact_value(
        postimages["semantic_attempt"],
        {
            "attempt_number": 1,
            "attempt_phase": "established",
            "selection_decision_ref": "exact genesis decision_ref",
            "candidate_ref": "exact preassigned genesis candidate_ref",
        },
        "C2B3C_CONTRACT_INVALID",
    )
    assert postimages["effect_head"]["head_revision"] == 0
    assert postimages["effect_head"]["effect_state"] == "ready_for_delivery"
    assert postimages["delivery_attempt"]["delivery_number"] == 1
    assert postimages["delivery_head"]["head_revision"] == 0
    assert postimages["delivery_head"]["delivery_state"] == "planned"
    assert len(postimages["time_bearing_rows_use_one_transaction_timestamp"]) == 10


def test_route_authority_requirements_and_effect_ceilings_are_exact() -> None:
    value = _section_39_contract()
    route = value["route_boundary"]
    assert route["initial_adapter_kind"] == "direct_local_bootstrap"
    assert route["meaning"] == "persisted planned delivery selection only"
    assert route["third_adapter_kind_introduced"] is False
    assert (
        route[
            "safe_correlation_is_capability_credential_retrieval_or_dispatch_permission"
        ]
        is False
    )
    authority = value["authority_split"]
    assert authority["dispatch_time"]["current_verification_state_at_establishment"] == (
        "pending"
    )
    assert authority["dispatch_time"][
        "fresh_external_verification_immediately_before_launch"
    ] == "mandatory"
    assert (
        authority[
            "fence_command_evaluation_or_planned_delivery_is_executable_permission"
        ]
        is False
    )
    requirements = value["requirement_evidence"]
    assert tuple(item[0] for item in requirements["types"]) == (
        "DevelopmentValidationRequirementEvidenceV1",
        "DevelopmentReviewRequirementEvidenceV1",
    )
    _assert_exact_value(
        requirements["ordered_fields"],
        EXPECTED_REQUIREMENT_FIELDS,
        "C2B3C_CONTRACT_INVALID",
    )
    assert requirements["new_requirement_evidence_row"] is False
    author_ceiling = value["effect_ceilings"][
        "author_effect_fence_and_worker_command"
    ]
    _assert_exact_value(
        author_ceiling,
        {
            "effect_class": "author_candidate",
            "max_local_commits": 0,
            "max_pushes": 0,
            "max_remote_ref_mutations": 0,
            "max_pull_requests": 0,
            "max_merges": 0,
            "max_deployments": 0,
            "max_publication_effects": 0,
        },
        "C2B3C_CONTRACT_INVALID",
    )


def test_safe_command_digest_replay_recovery_privacy_and_gate_are_exact() -> None:
    value = _section_39_contract()
    safe_command = value["safe_command"]
    fields = safe_command["ordered_fields_with_exact_type_and_source"]
    assert len(fields) == 35
    assert len({item[0] for item in fields}) == 35
    assert {item[2] for item in fields} == EXPECTED_COMMAND_SOURCES
    assert safe_command["identity_excludes"] == ("command_digest",)
    assert safe_command["profile_refs_are_identity_inputs"] is True
    digest = value["command_and_fence_digest_closure"]
    assert len(digest["ordered_steps"]) == 6
    assert digest["recursive_digest_graph"] is False
    runtime = value["fresh_construction_replay_and_recovery"]
    assert runtime["apply_order_after_writer_fencing"][:2] == (
        "receipt lookup",
        "exact replay or mutation-ref conflict",
    )
    _assert_exact_value(
        runtime["recovery"],
        {
            "authority": "fresh fenced writer session",
            "transaction": "read-only",
            "complete_exact_family": "committed_exact",
            "all_selected_family_identities_absent": "definitely_not_committed",
            "partial_malformed_contradictory_colliding_or_unverifiable": "unresolved",
            "write_clock_external_IO_or_COMMIT": False,
            "reconstructs_and_verifies_both_fixed_profile_refs": True,
        },
        "C2B3C_CONTRACT_INVALID",
    )
    assert (
        runtime[
            "automatic_semantic_retry_after_commit_outcome_unknown_or_unresolved"
        ]
        is False
    )
    assert value["privacy"]["ref_or_digest_is_retrieval_authority"] is False
    _assert_exact_value(
        value["c2b3d_gate"],
        {
            "this_contract_requires_independent_acceptance": True,
            "separate_source_implementation_prompt_required": True,
            "C2B3D_currently_authorized": False,
            "worker_or_external_IO_currently_authorized": False,
        },
        "C2B3C_CONTRACT_INVALID",
    )


def test_current_status_regions_are_reconciled_without_historical_rewrite() -> None:
    for path in (README_PATH, AGENTS_PATH):
        _assert_current_status(_read_owned_path(path))

    reader_status = _read_owned_path(READER_STATUS_PATH).split(
        "## Status And Authority", 1
    )[1].split("## Exact Private Source", 1)[0]
    reader_status = " ".join(reader_status.split())
    assert "Only the mutation-receipt reader has the bounded private VS1B" in reader_status
    assert "the other eleven roles remain production-unintegrated" in reader_status

    initialization = _read_owned_path(INITIALIZATION_STATUS_PATH)
    _historical, current = initialization.split(INITIALIZATION_STATUS_BEGIN, 1)
    current, after = current.split(INITIALIZATION_STATUS_END, 1)
    assert after == "\n"
    _assert_current_status(current)
    normalized = " ".join(current.split())
    assert "VS1B being pending fresh independent audit" not in normalized
    assert "C2B3C independent audit accepted" not in normalized


def test_family_golden_vector_is_independent_exact_and_self_verifying() -> None:
    value = _section_39_contract()
    owner_vector = value["family_golden_vector"]
    independently_owned_expected = deepcopy(EXPECTED_FAMILY_GOLDEN_VECTOR)
    assert owner_vector is not EXPECTED_FAMILY_GOLDEN_VECTOR
    assert independently_owned_expected is not EXPECTED_FAMILY_GOLDEN_VECTOR
    assert not (
        _mutable_container_ids(owner_vector)
        & _mutable_container_ids(independently_owned_expected)
    ), "C2B3C_VECTOR_INVALID"
    _assert_exact_value(
        owner_vector,
        independently_owned_expected,
        "C2B3C_VECTOR_INVALID",
    )
    _assert_family_vector(owner_vector)


@pytest.mark.parametrize(
    "case_name",
    (
        "canonical_bytes",
        "complete_worker_bytes",
        "canonical_digest",
        "postimage_digest",
        "graph_order",
        "receipt_digest",
        "committed_result",
        "replay_result",
    ),
)
def test_family_golden_vector_mutants_fail_closed(case_name: str) -> None:
    candidate = deepcopy(EXPECTED_FAMILY_GOLDEN_VECTOR)
    if case_name == "canonical_bytes":
        candidate["canonical_values"]["validation_requirement_evidence"][
            "canonical_json"
        ] += " "
    elif case_name == "complete_worker_bytes":
        candidate["canonical_values"]["complete_worker_command"][
            "complete_record_canonical_json"
        ] += " "
    elif case_name == "canonical_digest":
        candidate["canonical_values"]["attempt_fence"]["digest"] = "0" * 64
    elif case_name == "postimage_digest":
        candidate["persisted_postimages"]["semantic_attempt"][
            "semantic_attempt_digest"
        ] = "0" * 64
    elif case_name == "graph_order":
        entries = list(candidate["graph_entries"])
        entries[0], entries[1] = entries[1], entries[0]
        candidate["graph_entries"] = tuple(entries)
    elif case_name == "receipt_digest":
        candidate["receipt_envelope"]["digest"] = "0" * 64
    elif case_name == "committed_result":
        candidate["fresh_committed_result"]["mapping"][
            "effect_intent_ref"
        ] = "effect-intent-c2b3c-mutant"
    else:
        candidate["exact_replay_result"]["digest"] = "0" * 64
    with pytest.raises(AssertionError, match="C2B3C_VECTOR_INVALID"):
        _assert_family_vector(candidate)


@pytest.mark.parametrize(
    "case_name",
    (
        "missing_capsule",
        "changed_capsule",
        "missing_redaction",
        "changed_redaction",
        "swapped_order",
        "capsule_excluded_from_identity",
        "redaction_excluded_from_identity",
    ),
)
def test_profile_reference_mutants_reach_exact_profile_assertion(
    case_name: str,
) -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    safe_record = candidate["family_golden_vector"]["canonical_values"][
        "safe_mutation_command"
    ]
    if case_name == "missing_capsule":
        safe_record["complete_mapping"].pop("capsule_profile_ref")
    elif case_name == "changed_capsule":
        safe_record["complete_mapping"][
            "capsule_profile_ref"
        ] = "capsule-profile.changed-v1"
    elif case_name == "missing_redaction":
        safe_record["complete_mapping"].pop("redaction_profile_ref")
    elif case_name == "changed_redaction":
        safe_record["complete_mapping"][
            "redaction_profile_ref"
        ] = "redaction.changed-v1"
    elif case_name == "swapped_order":
        items = list(safe_record["complete_mapping"].items())
        capsule_index = next(
            index for index, item in enumerate(items) if item[0] == "capsule_profile_ref"
        )
        redaction_index = next(
            index for index, item in enumerate(items) if item[0] == "redaction_profile_ref"
        )
        items[capsule_index], items[redaction_index] = (
            items[redaction_index],
            items[capsule_index],
        )
        safe_record["complete_mapping"] = dict(items)
    elif case_name == "capsule_excluded_from_identity":
        candidate["family_golden_vector"]["canonical_values"][
            "safe_mutation_command"
        ]["canonical_identity_mapping"].pop("capsule_profile_ref")
    else:
        candidate["family_golden_vector"]["canonical_values"][
            "safe_mutation_command"
        ]["canonical_identity_mapping"].pop("redaction_profile_ref")
    with pytest.raises(AssertionError, match="C2B3C_PROFILE_REFS_INVALID"):
        _assert_profile_contract(candidate)


@pytest.mark.parametrize(
    "case_name",
    (
        "false_to_zero",
        "true_to_one",
        "one_to_true",
        "nested_mapping_order",
        "nested_container_type",
        "nested_extra_key",
        "nested_missing_key",
        "string_subclass_key",
    ),
)
def test_recursive_exact_comparator_rejects_python_equality_bypasses(
    case_name: str,
) -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    if case_name == "false_to_zero":
        candidate["contract_identity"]["migration_0003_required"] = 0
    elif case_name == "true_to_one":
        candidate["status_reconciliation"][
            "remote_ref_directly_verified_at_commit"
        ] = 1
    elif case_name == "one_to_true":
        candidate["basis_and_cardinality"]["program_version_number"] = True
    elif case_name == "nested_mapping_order":
        counts = candidate["basis_and_cardinality"]["created_counts"]
        items = list(counts.items())
        items[0], items[1] = items[1], items[0]
        candidate["basis_and_cardinality"]["created_counts"] = dict(items)
    elif case_name == "nested_container_type":
        candidate["receipt_graph"]["entries"] = list(
            candidate["receipt_graph"]["entries"]
        )
    elif case_name == "nested_extra_key":
        candidate["basis_and_cardinality"]["created_counts"]["extra"] = 0
    elif case_name == "nested_missing_key":
        candidate["basis_and_cardinality"]["created_counts"].pop(
            "program_version"
        )
    else:
        class StringSubclass(str):
            pass

        counts = candidate["basis_and_cardinality"]["created_counts"]
        items = list(counts.items())
        first_key, first_value = items[0]
        items[0] = (StringSubclass(first_key), first_value)
        candidate["basis_and_cardinality"]["created_counts"] = dict(items)
    with pytest.raises(AssertionError, match="C2B3C_CONTRACT_INVALID"):
        _assert_exact_contract(candidate)


@pytest.mark.parametrize(
    "case_name",
    (
        "arbitrary_prose",
        "contradictory_authority",
        "changed_wording",
        "added_blank_material",
        "duplicated_heading",
        "duplicated_marker",
    ),
)
def test_section_39_prologue_and_boundary_mutants_fail_exactly(
    case_name: str,
) -> None:
    source = _read_owned_bytes(OWNER_PATH)
    section_heading_bytes = SECTION_HEADING.encode("utf-8", errors="strict")
    begin_marker_bytes = BEGIN_MARKER.encode("utf-8", errors="strict")
    section_start = source.index(section_heading_bytes)
    prefix = source[:section_start]
    section = source[section_start:]
    if case_name == "arbitrary_prose":
        mutated_section = section.replace(
            b"Classification: `ACCEPTED TARGET CONTRACT`",
            b"Arbitrary interstitial prose.\n\nClassification: `ACCEPTED TARGET CONTRACT`",
            1,
        )
    elif case_name == "contradictory_authority":
        mutated_section = section.replace(
            begin_marker_bytes,
            b"Coordinator may self-authorize this family.\n\n"
            + begin_marker_bytes,
            1,
        )
    elif case_name == "changed_wording":
        mutated_section = section.replace(
            b"sole semantic owner", b"shared semantic owner", 1
        )
    elif case_name == "added_blank_material":
        mutated_section = section.replace(
            b"\n" + begin_marker_bytes, b"\n\n" + begin_marker_bytes, 1
        )
    elif case_name == "duplicated_heading":
        mutated_section = section.replace(
            section_heading_bytes,
            section_heading_bytes + b"\n" + section_heading_bytes,
            1,
        )
    else:
        mutated_section = section.replace(
            begin_marker_bytes,
            begin_marker_bytes + b"\n" + begin_marker_bytes,
            1,
        )
    candidate = prefix + mutated_section
    assert candidate != source
    with pytest.raises(AssertionError, match="C2B3C_PROLOGUE_INVALID"):
        _section_39_contract(candidate)


@pytest.mark.parametrize(
    "case_name",
    (
        "contradictory_comment",
        "leading_payload_material",
        "trailing_payload_material",
        "raw_crlf",
    ),
)
def test_section_39_payload_bytes_reject_raw_mutants(
    case_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _read_owned_bytes(OWNER_PATH)
    live_owner_sha256 = hashlib.sha256(source).hexdigest()
    section_heading_bytes = SECTION_HEADING.encode("utf-8", errors="strict")
    end_marker_bytes = END_MARKER.encode("utf-8", errors="strict")
    opening_fence = b"```python\n"
    closing_boundary = b"\n```\n\n" + end_marker_bytes
    assert source.count(opening_fence) >= 1
    section_start = source.index(section_heading_bytes)
    payload_start = source.index(opening_fence, section_start) + len(opening_fence)
    payload_end = source.index(closing_boundary, payload_start)
    payload = source[payload_start:payload_end]
    if case_name == "contradictory_comment":
        candidate = (
            source[:payload_start]
            + b"# Coordinator may self-authorize this family.\n"
            + source[payload_start:]
        )
    elif case_name == "leading_payload_material":
        candidate = source[:payload_start] + b"\n" + source[payload_start:]
    elif case_name == "trailing_payload_material":
        candidate = (
            source[:payload_end]
            + b"\n# Trailing non-payload material."
            + source[payload_end:]
        )
    else:
        assert b"\r\n" not in payload
        lf_offset = payload.index(b"\n")
        assert 0 < lf_offset < len(payload) - 1
        mutated_payload = (
            payload[:lf_offset] + b"\r\n" + payload[lf_offset + 1 :]
        )
        assert len(mutated_payload) == 332447
        assert hashlib.sha256(mutated_payload).hexdigest() == (
            "66f017012bf390ca8f567ccc6cc3a266d77da9c9f4ed217f01bea46fc3e92ef1"
        )
        candidate = source[:payload_start] + mutated_payload + source[payload_end:]
    assert candidate != source
    semantic_parser_called = False

    def unexpected_semantic_parse(_payload_bytes: bytes) -> dict[str, object]:
        nonlocal semantic_parser_called
        semantic_parser_called = True
        raise AssertionError("C2B3C_SEMANTIC_PARSE_REACHED")

    monkeypatch.setitem(
        globals(), "_parse_section_39_payload", unexpected_semantic_parse
    )
    with pytest.raises(AssertionError, match="C2B3C_PAYLOAD_BYTES_INVALID"):
        _section_39_contract(candidate)
    assert semantic_parser_called is False
    live_owner_after = _read_owned_bytes(OWNER_PATH)
    assert live_owner_after == source
    assert hashlib.sha256(live_owner_after).hexdigest() == live_owner_sha256


def test_section_39_semantic_parser_rejects_non_dict_direct_expression() -> None:
    with pytest.raises(AssertionError, match="C2B3C_OWNER_LITERAL_INVALID"):
        _parse_section_39_payload(b"[]")


def test_current_status_rejects_c2b3c_audit_acceptance_preclaim() -> None:
    initialization = _read_owned_path(INITIALIZATION_STATUS_PATH)
    _historical, current = initialization.split(INITIALIZATION_STATUS_BEGIN, 1)
    current, _after = current.split(INITIALIZATION_STATUS_END, 1)
    mutated = current + "\nC2B3C independent audit accepted\n"
    with pytest.raises(AssertionError, match="C2B3C_STATUS_INVALID"):
        _assert_current_status(mutated)


@pytest.mark.parametrize(
    "case_name",
    ("missing", "extra", "reordered", "widened", "contradictory"),
)
def test_finite_direct_contract_counterexamples_are_rejected(case_name: str) -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    if case_name == "missing":
        candidate.pop("receipt_graph")
    elif case_name == "extra":
        candidate["contract_identity"]["extension"] = "not allowed"
    elif case_name == "reordered":
        entries = list(candidate["receipt_graph"]["entries"])
        entries[0], entries[1] = entries[1], entries[0]
        candidate["receipt_graph"]["entries"] = tuple(entries)
    elif case_name == "widened":
        candidate["contract_identity"]["production_source_changed_or_authorized"] = True
    else:
        candidate["authority_split"]["dispatch_time"][
            "current_verification_state_at_establishment"
        ] = "verified"
    with pytest.raises(AssertionError, match="C2B3C_CONTRACT_INVALID"):
        _assert_exact_contract(candidate)
