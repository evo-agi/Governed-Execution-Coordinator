import ast
from collections.abc import Mapping
from copy import deepcopy
from functools import partial
import hashlib
import json
import re
from pathlib import Path
import shutil
import stat
from types import MappingProxyType

import pytest

import ge_nwp_coordinator._finite_backlog_risk_source_adapter as production_risk_adapter
import ge_nwp_coordinator._post_execution_evidence_values as production_evidence
import ge_nwp_coordinator._post_execution_policy_values as production_policy
import ge_nwp_coordinator._rw0_c_decision_input_values as production_decision
from test_post_execution_pure_owner_relations import (
    _active_stop_snapshot,
    _qualified_result_set,
    _section41_owner_inputs,
)
from c2a_contract_support import _reseal_single_digest_record
from ge_nwp_coordinator.global_stop import GlobalStopState
from ge_nwp_coordinator._rw0_phase_entry_semantic_values import (
    RW0AuthorityVerificationObservationV1,
)
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1,
    EffectFenceV1,
)
from test_post_execution_pure_owner_values import (
    CLASS_BY_V,
    _TEST_RECORDS,
    _ordered_fixture,
    _sample,
    _seal,
)
from test_rw0_b1_vectors import mapping_for


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / ".docs" / "rw0-c2-durable-progression-decision-semantic-contract.md"
EVIDENCE_SOURCE = ROOT / "src" / "ge_nwp_coordinator" / "_post_execution_evidence_values.py"
POLICY_SOURCE = ROOT / "src" / "ge_nwp_coordinator" / "_post_execution_policy_values.py"
DECISION_INPUT_SOURCE = ROOT / "src" / "ge_nwp_coordinator" / "_rw0_c_decision_input_values.py"

HUMAN_BEGIN = "<!-- RW0_C2_DURABLE_DECISION_HUMAN_CONTRACT_BEGIN -->"
HUMAN_END = "<!-- RW0_C2_DURABLE_DECISION_HUMAN_CONTRACT_END -->"
ORACLE_BEGIN = "<!-- RW0_C2_DURABLE_DECISION_FINITE_ORACLE_BEGIN -->"
ORACLE_END = "<!-- RW0_C2_DURABLE_DECISION_FINITE_ORACLE_END -->"
VALIDATION_BEGIN = "<!-- RW0_C2_VALIDATION_PROJECTION_BEGIN -->"
VALIDATION_END = "<!-- RW0_C2_VALIDATION_PROJECTION_END -->"
VALIDATION_CONFLICT_BEGIN = "<!-- RW0_C2_VALIDATION_CONFLICT_BEGIN -->"
VALIDATION_CONFLICT_END = "<!-- RW0_C2_VALIDATION_CONFLICT_END -->"
REVIEW_BEGIN = "<!-- RW0_C2_REVIEW_PROJECTION_BEGIN -->"
REVIEW_END = "<!-- RW0_C2_REVIEW_PROJECTION_END -->"
REVIEW_OVERRIDE_BEGIN = "<!-- RW0_C2_REVIEW_OVERRIDE_BEGIN -->"
REVIEW_OVERRIDE_END = "<!-- RW0_C2_REVIEW_OVERRIDE_END -->"
MATRIX_BEGIN = "<!-- RW0_C2_MATRIX_OWNER_PROFILES_BEGIN -->"
MATRIX_END = "<!-- RW0_C2_MATRIX_OWNER_PROFILES_END -->"
MATRIX_PAIR_BEGIN = "<!-- RW0_C2_MATRIX_OWNER_RESULT_REASON_PAIRS_BEGIN -->"
MATRIX_PAIR_END = "<!-- RW0_C2_MATRIX_OWNER_RESULT_REASON_PAIRS_END -->"
MATRIX_UNREACHABLE_BEGIN = "<!-- RW0_C2_MATRIX_METADATA_UNREACHABLE_PAIRS_BEGIN -->"
MATRIX_UNREACHABLE_END = "<!-- RW0_C2_MATRIX_METADATA_UNREACHABLE_PAIRS_END -->"
BRANCH_BEGIN = "<!-- RW0_C2_BRANCH_MAPPING_BEGIN -->"
BRANCH_END = "<!-- RW0_C2_BRANCH_MAPPING_END -->"


class _DuplicateJSONKeyError(ValueError):
    reason = "duplicate_json_key"

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"duplicate_json_key:{key}")


def _strict_json_loads(raw: str) -> object:
    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise _DuplicateJSONKeyError(key)
            value[key] = item
        return value

    return json.loads(raw, object_pairs_hook=reject_duplicate_keys)


EXPECTED_CONTRACT = _strict_json_loads(r"""{
  "contract_id": "rw0-c2-durable-progression-decision-semantic-contract-v2",
  "status": "accepted_strategic_target_not_implemented",
  "outcome_classes": [
    "no_write",
    "durable_decision",
    "recovery_unresolved"
  ],
  "rejection_classes": [
    "required_fact_invalid",
    "basis_identity_lineage_profile_provenance_conflict",
    "stale_caller_expectation",
    "mutation_ref_reuse_conflict",
    "preassigned_identity_or_family_route_collision",
    "matrix_conflict",
    "expected_branch_mismatch",
    "halt_only_matrix_contract_conflict",
    "bootstrap_acceptance_guard_conflict"
  ],
  "admission_fault_to_rejection": {
    "malformed_required_fact": "required_fact_invalid",
    "missing_required_fact": "required_fact_invalid",
    "duplicate_required_fact": "required_fact_invalid",
    "partial_required_fact": "required_fact_invalid",
    "foreign_required_fact": "required_fact_invalid",
    "contradictory_required_fact": "required_fact_invalid",
    "owner_conflict": "basis_identity_lineage_profile_provenance_conflict",
    "identity_conflict": "basis_identity_lineage_profile_provenance_conflict",
    "lineage_conflict": "basis_identity_lineage_profile_provenance_conflict",
    "profile_conflict": "basis_identity_lineage_profile_provenance_conflict",
    "provenance_conflict": "basis_identity_lineage_profile_provenance_conflict",
    "stale_caller_head": "stale_caller_expectation",
    "stale_caller_expectation": "stale_caller_expectation",
    "mutation_ref_reused_with_different_digest": "mutation_ref_reuse_conflict",
    "preassigned_identity_collision": "preassigned_identity_or_family_route_collision",
    "family_route_collision": "preassigned_identity_or_family_route_collision"
  },
  "validation_projection": [
    {
      "source_outcome": "passed",
      "result": "passed",
      "repairability": "not_applicable",
      "reason": "validation_passed",
      "normalized_class": "accept"
    },
    {
      "source_outcome": "failed",
      "result": "repairable_failure",
      "repairability": "repairable",
      "reason": "validation_failed_repairable",
      "normalized_class": "repair"
    },
    {
      "source_outcome": "failed",
      "result": "replan_required",
      "repairability": "same_attempt_insufficient",
      "reason": "validation_failed_replan_required",
      "normalized_class": "replan"
    },
    {
      "source_outcome": "failed",
      "result": "terminal_failure",
      "repairability": "nonrepairable",
      "reason": "validation_failed_terminal",
      "normalized_class": "terminal"
    },
    {
      "source_outcome": "failed",
      "result": "unknown",
      "repairability": "unknown",
      "reason": "validation_failed_unclassified",
      "normalized_class": "nonconclusive"
    },
    {
      "source_outcome": "inconclusive",
      "result": "unknown",
      "repairability": "unknown",
      "reason": "validation_inconclusive",
      "normalized_class": "nonconclusive"
    },
    {
      "source_outcome": "not_run",
      "result": "not_run",
      "repairability": "not_applicable",
      "reason": "validation_not_run",
      "normalized_class": "nonconclusive"
    }
  ],
  "validation_conflict_projection": {
    "source_outcome": "any_v14_allowed_source_outcome",
    "result": "basis_conflict",
    "repairability": "conflict",
    "reason": "source_observation_mismatch",
    "normalized_class": "conflict"
  },
  "review_projection": [
    {
      "separation_status": "separate",
      "source_outcome": "passed",
      "result": "passed",
      "reason": "review_passed",
      "normalized_class": "accept"
    },
    {
      "separation_status": "separate",
      "source_outcome": "failed",
      "result": "repair_required",
      "reason": "review_failed_repair_required",
      "normalized_class": "repair"
    },
    {
      "separation_status": "separate",
      "source_outcome": "failed",
      "result": "replan_required",
      "reason": "review_failed_replan_required",
      "normalized_class": "replan"
    },
    {
      "separation_status": "separate",
      "source_outcome": "failed",
      "result": "terminal_reject",
      "reason": "review_failed_terminal_reject",
      "normalized_class": "terminal"
    },
    {
      "separation_status": "separate",
      "source_outcome": "failed",
      "result": "unknown",
      "reason": "review_failed_unclassified",
      "normalized_class": "nonconclusive"
    },
    {
      "separation_status": "separate",
      "source_outcome": "inconclusive",
      "result": "unknown",
      "reason": "review_inconclusive",
      "normalized_class": "nonconclusive"
    }
  ],
  "review_override_projection": [
    {
      "separation_status": "not_separate",
      "source_outcome": "any_v15_allowed_source_outcome",
      "result": "basis_conflict",
      "reason": "review_not_operationally_separate",
      "normalized_class": "conflict"
    },
    {
      "separation_status": "unknown",
      "source_outcome": "any_v15_allowed_source_outcome",
      "result": "unknown",
      "reason": "reviewer_separation_unknown",
      "normalized_class": "nonconclusive"
    },
    {
      "separation_status": "conflict",
      "source_outcome": "any_v15_allowed_source_outcome",
      "result": "basis_conflict",
      "reason": "reviewer_separation_conflict",
      "normalized_class": "conflict"
    }
  ],
  "invalid_projection_rejection": "required_fact_invalid",
  "normalized_classes": [
    "accept",
    "repair",
    "replan",
    "terminal",
    "nonconclusive",
    "conflict"
  ],
  "conclusive_severity_low_to_high": [
    "accept",
    "repair",
    "replan",
    "terminal"
  ],
  "normalized_candidate_branch": {
    "accept": "candidate_acceptance",
    "repair": "candidate_repair",
    "replan": "attempt_selecting_replan",
    "terminal": "program_terminal_reject",
    "nonconclusive": "post_execution_program_block"
  },
  "candidate_reason_by_normalized_class": {
    "accept": "candidate_evidence_conclusively_accepted",
    "repair": "candidate_evidence_requires_repair",
    "replan": "candidate_evidence_requires_replan",
    "terminal": "candidate_evidence_terminally_rejected",
    "nonconclusive": "candidate_evidence_nonconclusive"
  },
  "currentness": {
    "conflict": "no_write",
    "stale": "decision_basis_not_current",
    "unknown": "decision_basis_not_current",
    "current": "continue"
  },
  "matrix": {
    "owners": [
      "standing_policy",
      "risk_lane",
      "decision_time_authority",
      "global_stop",
      "source_effect_ceiling"
    ],
    "results": [
      "permit",
      "deny",
      "unknown",
      "conflict"
    ],
    "productive_branches": [
      "candidate_acceptance",
      "candidate_repair",
      "attempt_selecting_replan"
    ],
    "halt_only_branches": [
      "program_terminal_reject",
      "post_execution_program_block"
    ],
    "branch_profiles": {
      "candidate_acceptance": {
        "applicability": "governed",
        "governed_effect_class": "author_candidate"
      },
      "candidate_repair": {
        "applicability": "governed",
        "governed_effect_class": "author_candidate"
      },
      "attempt_selecting_replan": {
        "applicability": "governed",
        "governed_effect_class": "author_candidate"
      },
      "program_terminal_reject": {
        "applicability": "halt_only",
        "governed_effect_class": null
      },
      "post_execution_program_block": {
        "applicability": "halt_only",
        "governed_effect_class": null
      }
    },
    "permit_reasons": {
      "standing_policy": {
        "productive": "policy_permits",
        "halt_only": "halt_only_policy_not_applicable"
      },
      "risk_lane": {
        "productive": "risk_lane_permits",
        "halt_only": "halt_only_risk_not_applicable"
      },
      "decision_time_authority": {
        "productive": "authority_verified_current",
        "halt_only": "halt_only_authority_not_applicable"
      },
      "global_stop": {
        "productive": "global_stop_clear",
        "halt_only": "halt_only_stop_checked"
      },
      "source_effect_ceiling": {
        "productive": "source_effect_within_current_ceilings",
        "halt_only": "halt_only_ceiling_not_applicable"
      }
    },
    "productive_all_permit": "retain_candidate",
    "productive_deny_or_unknown": "convert_to_post_execution_program_block",
    "productive_conflict": "matrix_conflict",
    "halt_only_required_branches": [
      "program_terminal_reject",
      "post_execution_program_block"
    ],
    "halt_only_required_result": "permit",
    "productive_profile_or_pair_rejection": "matrix_conflict",
    "halt_only_profile_or_pair_rejection": "halt_only_matrix_contract_conflict",
    "exact_conflict_pair_rejection": "matrix_conflict",
    "metadata_unreachable_rejection": "matrix_conflict",
    "malformed_inventory_rejection": "required_fact_invalid"
  },
  "accepted_emittable_pairs": {
    "standing_policy": [
      {
        "result": "permit",
        "reason": "halt_only_policy_not_applicable"
      },
      {
        "result": "deny",
        "reason": "policy_revoked"
      },
      {
        "result": "deny",
        "reason": "branch_not_allowed"
      },
      {
        "result": "deny",
        "reason": "risk_lane_not_allowed"
      },
      {
        "result": "deny",
        "reason": "effect_class_not_allowed"
      },
      {
        "result": "unknown",
        "reason": "policy_status_unknown"
      },
      {
        "result": "unknown",
        "reason": "policy_currentness_unknown"
      },
      {
        "result": "permit",
        "reason": "policy_permits"
      }
    ],
    "risk_lane": [
      {
        "result": "permit",
        "reason": "halt_only_risk_not_applicable"
      },
      {
        "result": "deny",
        "reason": "policy_revoked"
      },
      {
        "result": "deny",
        "reason": "required_lane_mismatch"
      },
      {
        "result": "unknown",
        "reason": "policy_status_unknown"
      },
      {
        "result": "permit",
        "reason": "risk_lane_permits"
      }
    ],
    "decision_time_authority": [
      {
        "result": "conflict",
        "reason": "snapshot_or_phase_mismatch"
      },
      {
        "result": "conflict",
        "reason": "parent_or_fence_identity_mismatch"
      },
      {
        "result": "conflict",
        "reason": "support_conflict"
      },
      {
        "result": "permit",
        "reason": "halt_only_authority_not_applicable"
      },
      {
        "result": "deny",
        "reason": "authority_denied"
      },
      {
        "result": "deny",
        "reason": "authority_revoked"
      },
      {
        "result": "deny",
        "reason": "attempt_fence_expired"
      },
      {
        "result": "deny",
        "reason": "effect_fence_expired"
      },
      {
        "result": "deny",
        "reason": "authority_grant_expired"
      },
      {
        "result": "deny",
        "reason": "authority_observation_expired"
      },
      {
        "result": "deny",
        "reason": "effect_class_not_allowed"
      },
      {
        "result": "unknown",
        "reason": "authority_status_unknown"
      },
      {
        "result": "unknown",
        "reason": "family_status_unknown"
      },
      {
        "result": "unknown",
        "reason": "revocation_status_unknown"
      },
      {
        "result": "permit",
        "reason": "authority_verified_current"
      }
    ],
    "global_stop": [
      {
        "result": "permit",
        "reason": "halt_only_stop_checked"
      },
      {
        "result": "deny",
        "reason": "global_stop_active"
      },
      {
        "result": "permit",
        "reason": "global_stop_clear"
      }
    ],
    "source_effect_ceiling": [
      {
        "result": "conflict",
        "reason": "snapshot_lineage_or_fence_mismatch"
      },
      {
        "result": "conflict",
        "reason": "proposal_evidence_conflict"
      },
      {
        "result": "permit",
        "reason": "halt_only_ceiling_not_applicable"
      },
      {
        "result": "deny",
        "reason": "proposal_evidence_noncompliant"
      },
      {
        "result": "deny",
        "reason": "attempt_fence_expired"
      },
      {
        "result": "deny",
        "reason": "effect_fence_expired"
      },
      {
        "result": "deny",
        "reason": "authority_grant_expired"
      },
      {
        "result": "deny",
        "reason": "authority_observation_expired"
      },
      {
        "result": "deny",
        "reason": "effect_class_not_allowed"
      },
      {
        "result": "deny",
        "reason": "source_effect_exceeds_current_attempt"
      },
      {
        "result": "deny",
        "reason": "source_effect_exceeds_current_authority"
      },
      {
        "result": "unknown",
        "reason": "current_authority_unknown"
      },
      {
        "result": "permit",
        "reason": "source_effect_within_current_ceilings"
      }
    ]
  },
  "metadata_only_unreachable_pairs": {
    "standing_policy": [
      {
        "result": "conflict",
        "reason": "policy_identity_conflict",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "conflict",
        "reason": "evaluator_profile_mismatch",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "conflict",
        "reason": "support_conflict",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "deny",
        "reason": "policy_not_yet_valid",
        "classification": "accepted_relation_precludes"
      },
      {
        "result": "deny",
        "reason": "policy_expired",
        "classification": "valid_construction_precludes"
      },
      {
        "result": "deny",
        "reason": "audience_mismatch",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "deny",
        "reason": "repository_mismatch",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "deny",
        "reason": "path_scope_mismatch",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "deny",
        "reason": "ceilings_exceeded",
        "classification": "no_evaluator_branch"
      }
    ],
    "risk_lane": [
      {
        "result": "conflict",
        "reason": "risk_source_conflict",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "conflict",
        "reason": "policy_identity_conflict",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "conflict",
        "reason": "evaluator_profile_mismatch",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "conflict",
        "reason": "support_conflict",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "deny",
        "reason": "policy_not_yet_valid",
        "classification": "accepted_relation_precludes"
      },
      {
        "result": "deny",
        "reason": "policy_expired",
        "classification": "valid_construction_precludes"
      },
      {
        "result": "deny",
        "reason": "risk_lane_not_allowed",
        "classification": "accepted_relation_precludes"
      }
    ],
    "decision_time_authority": [
      {
        "result": "conflict",
        "reason": "profile_mismatch",
        "classification": "no_evaluator_branch"
      }
    ],
    "global_stop": [
      {
        "result": "conflict",
        "reason": "snapshot_or_stop_identity_mismatch",
        "classification": "valid_construction_precludes"
      },
      {
        "result": "conflict",
        "reason": "profile_mismatch",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "unknown",
        "reason": "global_stop_unknown",
        "classification": "valid_construction_precludes"
      }
    ],
    "source_effect_ceiling": [
      {
        "result": "conflict",
        "reason": "profile_mismatch",
        "classification": "no_evaluator_branch"
      },
      {
        "result": "conflict",
        "reason": "support_conflict",
        "classification": "valid_construction_precludes"
      },
      {
        "result": "unknown",
        "reason": "proposal_evidence_unknown",
        "classification": "valid_construction_precludes"
      },
      {
        "result": "deny",
        "reason": "source_effect_exceeds_current_effect",
        "classification": "accepted_relation_precludes"
      }
    ]
  },
  "block_reason_precedence": [
    "decision_basis_not_current",
    "candidate_evidence_nonconclusive",
    "productive_branch_not_permitted"
  ],
  "branch_mapping": {
    "candidate_acceptance": {
      "decision_kind": "accept",
      "decision_variant": "candidate_acceptance",
      "version_advancing": true
    },
    "candidate_repair": {
      "decision_kind": "repair",
      "decision_variant": "candidate_repair",
      "version_advancing": true
    },
    "attempt_selecting_replan": {
      "decision_kind": "replan",
      "decision_variant": "attempt_selecting_replan",
      "version_advancing": true
    },
    "program_terminal_reject": {
      "decision_kind": "terminal_reject",
      "decision_variant": "program_terminal_reject",
      "version_advancing": true
    },
    "post_execution_program_block": {
      "decision_kind": "block",
      "decision_variant": "program_block",
      "version_advancing": true
    }
  },
  "excluded_reducer_decision_kinds": [
    "cancel",
    "redeliver"
  ],
  "expected_branch": {
    "role": "conflict_assertion_only",
    "mismatch": "expected_branch_mismatch"
  },
  "model": {
    "recommendation_to_branch": {
      "accept_candidate": "candidate_acceptance",
      "repair_candidate": "candidate_repair",
      "replan": "attempt_selecting_replan",
      "terminal_reject": "program_terminal_reject",
      "block": "post_execution_program_block"
    },
    "evaluation_order": "after_bootstrap_guard_gate",
    "may_change_branch": false,
    "retention": "non_authoritative_evidence",
    "recognized_equal": {
      "status": "consistent",
      "reason": "mapped_branch_equals_authoritative_branch"
    },
    "recognized_unequal": {
      "status": "inconsistent",
      "reason": "mapped_branch_differs_from_authoritative_branch"
    },
    "unrecognized": {
      "status": "inconsistent",
      "reason": "model_recommendation_unrecognized"
    }
  },
  "evaluation_trace": {
    "ordered_stages": [
      "basis_validated",
      "matrix_grammar_validated",
      "currentness_reduced",
      "validation_review_reduced",
      "productive_matrix_evaluated",
      "branch_selected",
      "halt_only_matrix_evaluated",
      "bootstrap_acceptance_guard_checked",
      "model_consistency_evaluated"
    ],
    "productive_matrix_evidence_fields": [
      "provisional_productive_branch",
      "owner_entries"
    ],
    "model_last": true
  },
  "guard": {
    "owner": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
    "relation_in_command_digest": true,
    "relation_in_recovery_selector": true,
    "relation_grants_authority": false,
    "relation_requests_acceptance": false,
    "relation_required_every_applicable_command": true,
    "universal_exact_roles": [
      "lineage",
      "scope",
      "admission",
      "continuity",
      "sole_active",
      "no_foreign_claim"
    ],
    "accept_required_evidence": "exhaustively_unclaimed",
    "accept_invalid_states": [
      "mismatch",
      "missing",
      "duplicate",
      "malformed",
      "ambiguous",
      "claimed"
    ],
    "accept_invalid_result": "bootstrap_acceptance_guard_conflict",
    "accept_effect": "create_one_immutable_acceptance_fact",
    "nonaccept_effect": "none",
    "replay_mutates": false,
    "recovery_family": "complete_decision_family_including_acceptance_fact",
    "accept_writer_callable_before_physical_freeze": false
  },
  "recovery": {
    "requires_commit_attempt_uncertainty": true,
    "readback": {
      "exact_family": "committed_exact",
      "provably_absent": "definitely_not_committed",
      "ambiguous": "unresolved"
    },
    "unresolved_creates_decision": false,
    "unresolved_is_branch": false,
    "automatic_retry_after_unresolved": false
  },
  "terminal": {
    "later_immutable_fact": true,
    "binds_committed_decision_result_receipt": true,
    "acceptance_binds_immutable_bootstrap_acceptance_fact": true,
    "mutates_guard": false,
    "is_development_decision": false,
    "is_effect_basis": false
  },
  "physical": {
    "application_generation": 2,
    "current_terminal_migration": "0004_rw0_c1_durable_evidence",
    "canonical_decision_representation_migration": "0002_development_program_and_effect_state",
    "migration_0005_exists": false,
    "migration_0005_selected": false,
    "later_freeze": "bounded_hybrid_physical_contract"
  },
  "excluded_effect_domains": [
    "worker",
    "process",
    "transport",
    "cancellation",
    "git",
    "execution_substrate",
    "publication",
    "rw0_d",
    "rw0_e"
  ],
  "implementation": {
    "durable_decision_writer": false,
    "bootstrap_acceptance_guard": false,
    "terminal_outcome_owner": false,
    "production_caller": false,
    "public_export": false,
    "runtime_active": false,
    "rw0_d": false,
    "rw0_e": false,
    "execution_substrate_change": false
  },
  "temporary_source_nonimplementation_guard": {
    "source_root": "src/ge_nwp_coordinator",
    "manifest_count": 66,
    "manifest_payload_bytes": 10877,
    "manifest_sha256": "f069130c33d68ebf4d83a2d4d3a3f6aca7d1f1b583decc6138c772bd4ddd721d",
    "supersession": "future_authorized_source_tranche"
  }
}""")
CLASS_ORDER = ("accept", "repair", "replan", "terminal", "nonconclusive", "conflict")
EXPECTED_CLASS_MATRIX = {
    "accept": ("accept", "repair", "replan", "terminal", "nonconclusive", "conflict"),
    "repair": ("repair", "repair", "replan", "terminal", "nonconclusive", "conflict"),
    "replan": ("replan", "replan", "replan", "terminal", "nonconclusive", "conflict"),
    "terminal": ("terminal", "terminal", "terminal", "terminal", "nonconclusive", "conflict"),
    "nonconclusive": (
        "nonconclusive", "nonconclusive", "nonconclusive",
        "nonconclusive", "nonconclusive", "conflict",
    ),
    "conflict": ("conflict", "conflict", "conflict", "conflict", "conflict", "conflict"),
}
FIXED_EXPECTED_ACCEPTED_PAIRS = {
    "standing_policy": (
        ("permit", "halt_only_policy_not_applicable"),
        ("deny", "policy_revoked"),
        ("deny", "branch_not_allowed"),
        ("deny", "risk_lane_not_allowed"),
        ("deny", "effect_class_not_allowed"),
        ("unknown", "policy_status_unknown"),
        ("unknown", "policy_currentness_unknown"),
        ("permit", "policy_permits"),
    ),
    "risk_lane": (
        ("permit", "halt_only_risk_not_applicable"),
        ("deny", "policy_revoked"),
        ("deny", "required_lane_mismatch"),
        ("unknown", "policy_status_unknown"),
        ("permit", "risk_lane_permits"),
    ),
    "decision_time_authority": (
        ("conflict", "snapshot_or_phase_mismatch"),
        ("conflict", "parent_or_fence_identity_mismatch"),
        ("conflict", "support_conflict"),
        ("permit", "halt_only_authority_not_applicable"),
        ("deny", "authority_denied"),
        ("deny", "authority_revoked"),
        ("deny", "attempt_fence_expired"),
        ("deny", "effect_fence_expired"),
        ("deny", "authority_grant_expired"),
        ("deny", "authority_observation_expired"),
        ("deny", "effect_class_not_allowed"),
        ("unknown", "authority_status_unknown"),
        ("unknown", "family_status_unknown"),
        ("unknown", "revocation_status_unknown"),
        ("permit", "authority_verified_current"),
    ),
    "global_stop": (
        ("permit", "halt_only_stop_checked"),
        ("deny", "global_stop_active"),
        ("permit", "global_stop_clear"),
    ),
    "source_effect_ceiling": (
        ("conflict", "snapshot_lineage_or_fence_mismatch"),
        ("conflict", "proposal_evidence_conflict"),
        ("permit", "halt_only_ceiling_not_applicable"),
        ("deny", "proposal_evidence_noncompliant"),
        ("deny", "attempt_fence_expired"),
        ("deny", "effect_fence_expired"),
        ("deny", "authority_grant_expired"),
        ("deny", "authority_observation_expired"),
        ("deny", "effect_class_not_allowed"),
        ("deny", "source_effect_exceeds_current_attempt"),
        ("deny", "source_effect_exceeds_current_authority"),
        ("unknown", "current_authority_unknown"),
        ("permit", "source_effect_within_current_ceilings"),
    ),
}
FIXED_EXPECTED_EXCLUDED_PAIRS = {
    "standing_policy": (
        ("conflict", "policy_identity_conflict", "no_evaluator_branch"),
        ("conflict", "evaluator_profile_mismatch", "no_evaluator_branch"),
        ("conflict", "support_conflict", "no_evaluator_branch"),
        ("deny", "policy_not_yet_valid", "accepted_relation_precludes"),
        ("deny", "policy_expired", "valid_construction_precludes"),
        ("deny", "audience_mismatch", "no_evaluator_branch"),
        ("deny", "repository_mismatch", "no_evaluator_branch"),
        ("deny", "path_scope_mismatch", "no_evaluator_branch"),
        ("deny", "ceilings_exceeded", "no_evaluator_branch"),
    ),
    "risk_lane": (
        ("conflict", "risk_source_conflict", "no_evaluator_branch"),
        ("conflict", "policy_identity_conflict", "no_evaluator_branch"),
        ("conflict", "evaluator_profile_mismatch", "no_evaluator_branch"),
        ("conflict", "support_conflict", "no_evaluator_branch"),
        ("deny", "policy_not_yet_valid", "accepted_relation_precludes"),
        ("deny", "policy_expired", "valid_construction_precludes"),
        ("deny", "risk_lane_not_allowed", "accepted_relation_precludes"),
    ),
    "decision_time_authority": (
        ("conflict", "profile_mismatch", "no_evaluator_branch"),
    ),
    "global_stop": (
        (
            "conflict",
            "snapshot_or_stop_identity_mismatch",
            "valid_construction_precludes",
        ),
        ("conflict", "profile_mismatch", "no_evaluator_branch"),
        ("unknown", "global_stop_unknown", "valid_construction_precludes"),
    ),
    "source_effect_ceiling": (
        ("conflict", "profile_mismatch", "no_evaluator_branch"),
        ("conflict", "support_conflict", "valid_construction_precludes"),
        ("unknown", "proposal_evidence_unknown", "valid_construction_precludes"),
        (
            "deny",
            "source_effect_exceeds_current_effect",
            "accepted_relation_precludes",
        ),
    ),
}
OWNER_PAIR_CASES = tuple(
    (owner, result, reason)
    for owner, pairs in FIXED_EXPECTED_ACCEPTED_PAIRS.items()
    for result, reason in pairs
)
UNREACHABLE_PAIR_CASES = tuple(
    (owner, result, reason, classification)
    for owner, pairs in FIXED_EXPECTED_EXCLUDED_PAIRS.items()
    for result, reason, classification in pairs
)
MIGRATION_SHA256 = {
    "0001_initial.sql": "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148",
    "0002_development_program_and_effect_state.sql": "5859f49994b1467db71911fb60db4f1cfc562af7517dc6e4d81b5b29ca44d56c",
    "0003_cognitive_proposal_and_selection_state.sql": "b5c7cac8e074b77ab369579f1f8015f547f1a2776b4b09d612e56280f16c1579",
    "0004_rw0_c1_durable_evidence.sql": "967b9c2deb43da625f9ce82d43c9538bfd2fa27c02f3abdfcb12eb3a2aef8cec",
}


def _between(text: str, begin: str, end: str) -> str:
    assert text.count(begin) == 1, begin
    assert text.count(end) == 1, end
    return text.split(begin, 1)[1].split(end, 1)[0].strip()


def _code_cell(cell: str) -> str:
    cell = cell.strip()
    delimiter = chr(96)
    assert cell.startswith(delimiter) and cell.endswith(delimiter), cell
    return cell[1:-1]


def _table_rows(text: str, begin: str, end: str) -> tuple[tuple[str, ...], ...]:
    lines = [
        line for line in _between(text, begin, end).splitlines()
        if line.startswith("|")
    ]
    assert len(lines) >= 3
    width = len(lines[0].split("|")[1:-1])
    rows = tuple(
        tuple(cell.strip() for cell in line.split("|")[1:-1])
        for line in lines[2:]
    )
    assert all(len(row) == width for row in rows)
    return rows


def _parse_human_contract(text: str) -> dict[str, object]:
    parsed: dict[str, object] = {}
    for field_cell, value_cell in _table_rows(text, HUMAN_BEGIN, HUMAN_END):
        field = _code_cell(field_cell)
        assert field not in parsed
        parsed[field] = _strict_json_loads(_code_cell(value_cell))
    accepted: dict[str, list[dict[str, str]]] = {
        owner: [] for owner in EXPECTED_CONTRACT["matrix"]["owners"]
    }
    for owner_cell, result_cell, reason_cell in _table_rows(
        text, MATRIX_PAIR_BEGIN, MATRIX_PAIR_END
    ):
        accepted[_code_cell(owner_cell)].append(
            {"result": _code_cell(result_cell), "reason": _code_cell(reason_cell)}
        )
    unreachable: dict[str, list[dict[str, str]]] = {
        owner: [] for owner in EXPECTED_CONTRACT["matrix"]["owners"]
    }
    for owner_cell, result_cell, reason_cell, class_cell in _table_rows(
        text, MATRIX_UNREACHABLE_BEGIN, MATRIX_UNREACHABLE_END
    ):
        unreachable[_code_cell(owner_cell)].append(
            {
                "result": _code_cell(result_cell),
                "reason": _code_cell(reason_cell),
                "classification": _code_cell(class_cell),
            }
        )
    if "accepted_emittable_pairs" in parsed:
        _require_exact(
            parsed["accepted_emittable_pairs"] == accepted,
            "human_accepted_pair_table_mismatch",
        )
    else:
        parsed["accepted_emittable_pairs"] = accepted
    if "metadata_only_unreachable_pairs" in parsed:
        _require_exact(
            parsed["metadata_only_unreachable_pairs"] == unreachable,
            "human_excluded_pair_table_mismatch",
        )
    else:
        parsed["metadata_only_unreachable_pairs"] = unreachable
    return parsed


def _parse_machine_contract(text: str) -> dict[str, object]:
    body = _between(text, ORACLE_BEGIN, ORACLE_END)
    fence = chr(96) * 3
    prefix = fence + "json\n"
    suffix = "\n" + fence
    assert body.startswith(prefix) and body.endswith(suffix)
    parsed = _strict_json_loads(body.removeprefix(prefix).removesuffix(suffix))
    assert type(parsed) is dict
    return parsed


def _assert_duplicate_json_key(
    exception: pytest.ExceptionInfo[_DuplicateJSONKeyError],
    expected_key: str,
) -> None:
    assert exception.type is _DuplicateJSONKeyError
    assert exception.value.reason == "duplicate_json_key"
    assert exception.value.key == expected_key
    assert str(exception.value) == f"duplicate_json_key:{expected_key}"


def test_duplicate_key_contradictory_shadow_is_rejected_before_comparison() -> None:
    accepted = json.dumps(EXPECTED_CONTRACT, separators=(",", ":"))
    hostile = accepted.replace(
        '"status":"accepted_strategic_target_not_implemented"',
        '"status":"contradictory_shadow",'
        '"status":"accepted_strategic_target_not_implemented"',
        1,
    )
    assert json.loads(hostile) == EXPECTED_CONTRACT
    with pytest.raises(_DuplicateJSONKeyError) as exception:
        _strict_json_loads(hostile)
    _assert_duplicate_json_key(exception, "status")


def test_hostile_duplicate_key_nested_machine_contract_rejects_exact_boundary(
    owner_text: str,
) -> None:
    accepted = '"model_last": true'
    hostile = '"model_last": false, "model_last": true'
    assert owner_text.count(accepted) == 1
    changed = _replace_in_region(
        owner_text,
        ORACLE_BEGIN,
        ORACLE_END,
        accepted,
        hostile,
    )
    with pytest.raises(_DuplicateJSONKeyError) as exception:
        _parse_machine_contract(changed)
    _assert_duplicate_json_key(exception, "model_last")


def _first_difference(
    actual: object,
    expected: object,
    path: tuple[str, ...] = (),
) -> tuple[str, ...] | None:
    if type(actual) is not type(expected):
        return path
    if type(expected) is dict:
        assert isinstance(actual, dict) and isinstance(expected, dict)
        if set(actual) != set(expected):
            return path
        for key in expected:
            difference = _first_difference(actual[key], expected[key], (*path, str(key)))
            if difference is not None:
                return difference
        return None
    if type(expected) is list:
        assert isinstance(actual, list) and isinstance(expected, list)
        if len(actual) != len(expected):
            return path
        for index, (left, right) in enumerate(zip(actual, expected, strict=True)):
            difference = _first_difference(left, right, (*path, str(index)))
            if difference is not None:
                return difference
        return None
    return None if actual == expected else path


def _assert_fixed_contract(contract: dict[str, object]) -> None:
    difference = _first_difference(contract, EXPECTED_CONTRACT)
    pointer = "/" + "/".join(
        component.replace("~", "~0").replace("/", "~1")
        for component in (difference or ())
    )
    if difference is not None:
        raise AssertionError(f"contract drift at {pointer}")


def _dict_rows(
    rows: tuple[tuple[str, ...], ...],
    fields: tuple[str, ...],
) -> list[dict[str, object]]:
    values: list[dict[str, object]] = []
    for row in rows:
        assert len(row) == len(fields)
        values.append({field: _code_cell(cell) for field, cell in zip(fields, row, strict=True)})
    return values


def _require_exact(condition: bool, boundary: str) -> None:
    if not condition:
        raise AssertionError(boundary)


def _validate_expanded_tables(text: str, contract: dict[str, object]) -> None:
    _require_exact(
        _dict_rows(
            _table_rows(text, VALIDATION_BEGIN, VALIDATION_END),
            (
                "source_outcome",
                "result",
                "repairability",
                "reason",
                "normalized_class",
            ),
        ) == contract["validation_projection"],
        "human_expanded_validation_projection_mismatch",
    )
    assert _dict_rows(
        _table_rows(text, VALIDATION_CONFLICT_BEGIN, VALIDATION_CONFLICT_END),
        ("source_outcome", "result", "repairability", "reason", "normalized_class"),
    ) == [contract["validation_conflict_projection"]]
    assert _dict_rows(
        _table_rows(text, REVIEW_BEGIN, REVIEW_END),
        ("separation_status", "source_outcome", "result", "reason", "normalized_class"),
    ) == contract["review_projection"]
    assert _dict_rows(
        _table_rows(text, REVIEW_OVERRIDE_BEGIN, REVIEW_OVERRIDE_END),
        ("separation_status", "source_outcome", "result", "reason", "normalized_class"),
    ) == contract["review_override_projection"]

    matrix = contract["matrix"]
    assert isinstance(matrix, dict)
    owners: list[str] = []
    permit_reasons: dict[str, dict[str, str]] = {}
    for expected_order, row in enumerate(_table_rows(text, MATRIX_BEGIN, MATRIX_END), 1):
        order_cell, owner_cell, productive_cell, halt_cell = row
        assert order_cell == str(expected_order)
        owner = _code_cell(owner_cell)
        owners.append(owner)
        permit_reasons[owner] = {
            "productive": _code_cell(productive_cell),
            "halt_only": _code_cell(halt_cell),
        }
    assert owners == matrix["owners"]
    assert permit_reasons == matrix["permit_reasons"]

    pair_rows = tuple(
        (_code_cell(owner), _code_cell(result), _code_cell(reason))
        for owner, result, reason in _table_rows(
            text,
            MATRIX_PAIR_BEGIN,
            MATRIX_PAIR_END,
        )
    )
    expected_pair_rows = tuple(
        (owner, pair["result"], pair["reason"])
        for owner in matrix["owners"]
        for pair in contract["accepted_emittable_pairs"][owner]
    )
    _require_exact(
        pair_rows == expected_pair_rows,
        "human_accepted_pair_table_mismatch",
    )

    unreachable_rows = tuple(
        (
            _code_cell(owner),
            _code_cell(result),
            _code_cell(reason),
            _code_cell(classification),
        )
        for owner, result, reason, classification in _table_rows(
            text,
            MATRIX_UNREACHABLE_BEGIN,
            MATRIX_UNREACHABLE_END,
        )
    )
    expected_unreachable_rows = tuple(
        (owner, pair["result"], pair["reason"], pair["classification"])
        for owner in matrix["owners"]
        for pair in contract["metadata_only_unreachable_pairs"][owner]
    )
    _require_exact(
        unreachable_rows == expected_unreachable_rows,
        "human_excluded_pair_table_mismatch",
    )

    branch_mapping: dict[str, dict[str, object]] = {}
    for branch_cell, kind_cell, variant_cell, advancing_cell in _table_rows(
        text, BRANCH_BEGIN, BRANCH_END
    ):
        assert advancing_cell == "yes"
        branch_mapping[_code_cell(branch_cell)] = {
            "decision_kind": _code_cell(kind_cell),
            "decision_variant": _code_cell(variant_cell),
            "version_advancing": True,
        }
    assert branch_mapping == contract["branch_mapping"]



def _type_exact(observed, expected, path='', *, boundary='c2:human_machine_equivalence', ordered_keys=False):
    """Closed built-in values; no coercion or subclass equivalence."""
    location = path or '/'
    if type(expected) not in (dict, list, tuple, bool, int, str, type(None)) or type(observed) is not type(expected):
        raise AssertionError(boundary + ':' + location + ':type')
    if type(expected) is dict:
        if any(type(key) is not str for key in observed) or set(observed) != set(expected):
            raise AssertionError(boundary + ':' + location + ':keys')
        if ordered_keys and tuple(observed) != tuple(expected):
            raise AssertionError(boundary + ':' + location + ':order')
        for key, value in expected.items():
            escaped = key.replace('~', '~0').replace('/', '~1')
            _type_exact(observed[key], value, path + '/' + escaped, boundary=boundary, ordered_keys=ordered_keys)
    elif type(expected) in (list, tuple):
        if len(observed) != len(expected):
            raise AssertionError(boundary + ':' + location + ':length')
        for index, (actual, wanted) in enumerate(zip(observed, expected, strict=True)):
            _type_exact(actual, wanted, path + '/' + str(index), boundary=boundary, ordered_keys=ordered_keys)
    elif observed != expected:
        raise AssertionError(boundary + ':' + location + ':value')

def _validate_document_text(text: str) -> dict[str, object]:
    human = _parse_human_contract(text)
    machine = _parse_machine_contract(text)
    _type_exact(human, machine)
    _assert_fixed_contract(machine)
    _validate_expanded_tables(text, machine)
    compact = " ".join(text.split())
    _require_exact("## Bootstrap acceptance-guard dependency" in text and "Every applicable direct-local command binds canonical admitted lineage and scope expectations" in compact, "c2:guard_dependency_prose")
    _require_exact(not any(phrase in compact for phrase in ("verify the exact available preimage", "preassigned consumed postimage", "accept decision plus consumed postimage", "verify the future latch precondition")), "c2:mutable_latch_requirement")
    assert "single semantic owner for the future RW0-C2" in compact
    assert "The productive-to-block path is necessarily two-stage." in compact
    assert "Source and migrations implement current behavior" in compact
    assert "sole authority for current implemented behavior" not in compact
    assert "basis_owner_profile_conflict" not in text
    assert "basis_owner_separation_profile_conflict" not in text
    return machine


def _assignment(tree: ast.Module, name: str) -> object:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return ast.literal_eval(node.value)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == name:
                return ast.literal_eval(node.value)
    raise AssertionError(f"missing static assignment {name}")


def _literal_set_containing(tree: ast.Module, member: tuple[object, ...]) -> set[tuple[object, ...]]:
    matches: list[set[tuple[object, ...]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Set):
            continue
        try:
            value = ast.literal_eval(node)
        except (ValueError, TypeError):
            continue
        if type(value) is set and member in value:
            matches.append(value)
    assert len(matches) == 1
    return matches[0]


def _review_override_mapping(tree: ast.Module) -> dict[str, tuple[str, str]]:
    matches: list[dict[str, tuple[str, str]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        try:
            value = ast.literal_eval(node)
        except (ValueError, TypeError):
            continue
        if type(value) is dict and set(value) == {"not_separate", "unknown", "conflict"}:
            if all(type(item) is tuple and len(item) == 2 for item in value.values()):
                matches.append(value)
    assert len(matches) == 1
    return matches[0]


MATRIX_OWNER_CLASSES = {
    "standing_policy": "PostExecutionStandingPolicyBranchMatrixV1",
    "risk_lane": "PostExecutionRiskLaneBranchMatrixV1",
    "decision_time_authority": "RW0CDecisionTimeAuthorityBranchMatrixV1",
    "global_stop": "RW0CDecisionTimeGlobalStopBranchMatrixV1",
    "source_effect_ceiling": "RW0CDecisionTimeSourceEffectCeilingBranchMatrixV1",
}


def _matrix_class_metadata(
    tree: ast.Module,
) -> dict[str, dict[str, tuple[tuple[object, ...], ...]]]:
    metadata: dict[str, dict[str, tuple[tuple[object, ...], ...]]] = {}
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "_define"
            and node.args
        ):
            continue
        try:
            class_name = ast.literal_eval(node.args[0])
        except (ValueError, TypeError):
            continue
        if class_name not in MATRIX_OWNER_CLASSES.values():
            continue
        keywords = {keyword.arg: keyword.value for keyword in node.keywords}
        assert "meta" in keywords
        meta = ast.literal_eval(keywords["meta"])
        matrix = meta["matrix"]
        metadata[class_name] = {
            "branches": tuple(matrix["branches"]),
            "allowed_pairs": tuple(matrix["allowed_pairs"]),
        }
    return metadata


def _derive_source_contract(
    evidence_text: str,
    policy_text: str,
    decision_input_text: str,
) -> dict[str, object]:
    evidence_tree = ast.parse(evidence_text)
    policy_tree = ast.parse(policy_text)
    decision_tree = ast.parse(decision_input_text)
    matrix_metadata = {
        **_matrix_class_metadata(policy_tree),
        **_matrix_class_metadata(decision_tree),
    }
    assert set(matrix_metadata) == set(MATRIX_OWNER_CLASSES.values())
    return {
        "validation_tuples": _assignment(evidence_tree, "_VALIDATION_TUPLES"),
        "review_tuples": _assignment(evidence_tree, "_REVIEW_TUPLES"),
        "validation_allowed": _literal_set_containing(
            evidence_tree,
            ("basis_conflict", "conflict", "source_observation_mismatch"),
        ),
        "review_allowed": _literal_set_containing(
            evidence_tree,
            ("basis_conflict", "review_not_operationally_separate"),
        ),
        "review_overrides": _review_override_mapping(evidence_tree),
        "branches": _assignment(evidence_tree, "_BRANCHES"),
        "canonical_branches": _assignment(evidence_tree, "_CANONICAL_BRANCHES"),
        "decision_branches": _assignment(decision_tree, "_DECISION_BRANCHES"),
        "recommendation_branches": _assignment(evidence_tree, "_RECOMMENDATION_BRANCHES"),
        "matrix_owner_metadata": {
            owner: matrix_metadata[class_name]
            for owner, class_name in MATRIX_OWNER_CLASSES.items()
        },
    }


def _assert_source_binding(
    contract: dict[str, object],
    evidence_text: str,
    policy_text: str,
    decision_input_text: str,
) -> dict[str, object]:
    source = _derive_source_contract(evidence_text, policy_text, decision_input_text)
    validation = contract["validation_projection"]
    review = contract["review_projection"]
    validation_conflict = contract["validation_conflict_projection"]
    review_overrides = contract["review_override_projection"]
    matrix = contract["matrix"]
    model = contract["model"]
    assert isinstance(validation, list)
    assert isinstance(review, list)
    assert isinstance(validation_conflict, dict)
    assert isinstance(review_overrides, list)
    assert isinstance(matrix, dict)
    assert isinstance(model, dict)

    validation_tuples = tuple(
        (row["source_outcome"], row["result"], row["repairability"], row["reason"])
        for row in validation
    )
    _require_exact(
        source["validation_tuples"] == validation_tuples,
        "source_binding:validation_tuples",
    )
    assert source["validation_allowed"] == {
        (row["result"], row["repairability"], row["reason"]) for row in validation
    } | {
        (
            validation_conflict["result"],
            validation_conflict["repairability"],
            validation_conflict["reason"],
        )
    }

    review_tuples = tuple(
        (row["source_outcome"], row["result"], row["reason"]) for row in review
    )
    assert source["review_tuples"] == review_tuples
    expected_overrides = {
        row["separation_status"]: (row["result"], row["reason"])
        for row in review_overrides
    }
    _require_exact(
        source["review_overrides"] == expected_overrides,
        "source_binding:review_overrides",
    )
    assert source["review_allowed"] == {
        (row["result"], row["reason"]) for row in review
    } | set(expected_overrides.values())

    profiles = matrix["branch_profiles"]
    assert isinstance(profiles, dict)
    expected_canonical = tuple(
        (branch, profile["applicability"], profile["governed_effect_class"])
        for branch, profile in profiles.items()
    )
    assert source["branches"] == tuple(profiles)
    assert source["canonical_branches"] == expected_canonical
    assert source["decision_branches"] == expected_canonical
    assert source["recommendation_branches"] == model["recommendation_to_branch"]

    owner_metadata = source["matrix_owner_metadata"]
    for owner in matrix["owners"]:
        assert owner_metadata[owner]["branches"] == expected_canonical
        declared = [
            {"result": result, "reason": reason}
            for result, reason in owner_metadata[owner]["allowed_pairs"]
        ]
        accepted = contract["accepted_emittable_pairs"][owner]
        unreachable = [
            {"result": pair["result"], "reason": pair["reason"]}
            for pair in contract["metadata_only_unreachable_pairs"][owner]
        ]
        _require_exact(
            len(declared) == len(accepted) + len(unreachable),
            f"source_binding:owner_pair_cardinality:{owner}",
        )
        _require_exact(
            {tuple(pair.values()) for pair in declared}
            == {(pair["result"], pair["reason"]) for pair in accepted}
            | {tuple(pair.values()) for pair in unreachable},
            f"source_binding:owner_pair_partition:{owner}",
        )
        _require_exact(
            not (
                {(pair["result"], pair["reason"]) for pair in accepted}
                & {tuple(pair.values()) for pair in unreachable}
            ),
            f"source_binding:owner_pair_disjointness:{owner}",
        )
    return source


def _normal_class(
    contract: dict[str, object],
    row: dict[str, object],
    *,
    review: bool,
) -> str | None:
    projection_key = "review_projection" if review else "validation_projection"
    for candidate in contract[projection_key]:
        fields = set(candidate) - {"normalized_class"}
        if all(row.get(field) == candidate[field] for field in fields):
            return candidate["normalized_class"]

    source_outcomes = {
        candidate["source_outcome"] for candidate in contract[projection_key]
    }
    if row.get("source_outcome") not in source_outcomes:
        return None
    if review:
        for candidate in contract["review_override_projection"]:
            if (
                row.get("separation_status") == candidate["separation_status"]
                and row.get("result") == candidate["result"]
                and row.get("reason") == candidate["reason"]
            ):
                return candidate["normalized_class"]
        return None

    conflict = contract["validation_conflict_projection"]
    if (
        row.get("result") == conflict["result"]
        and row.get("repairability") == conflict["repairability"]
        and row.get("reason") == conflict["reason"]
    ):
        return conflict["normalized_class"]
    return None


def _no_write(
    rejection: str,
    audit_trace: tuple[str, ...] = (),
    **evidence: object,
) -> dict[str, object]:
    result: dict[str, object] = {
        "outcome": "no_write",
        "rejection": rejection,
        "decision_created": False,
        "version_advanced": False,
        "head_mutated": False,
        "receipt_created": False,
        "acceptance_fact_effect": "none",
        "terminal_fact_created": False,
        "audit_trace": audit_trace,
    }
    result.update(evidence)
    return result


def _assert_no_write(result: dict[str, object], rejection: str) -> None:
    _require_exact(
        result["outcome"] == "no_write",
        f"no_write:outcome:{result['outcome']}",
    )
    _require_exact(
        result["rejection"] == rejection,
        f"no_write:rejection:{result['rejection']}!=expected:{rejection}",
    )
    _require_exact(
        result["decision_created"] is False,
        "no_write:decision_created",
    )
    _require_exact(
        result["version_advanced"] is False,
        "no_write:version_advanced",
    )
    _require_exact(result["head_mutated"] is False, "no_write:head_mutated")
    _require_exact(
        result["receipt_created"] is False,
        "no_write:receipt_created",
    )
    _require_exact(result["acceptance_fact_effect"] == "none", "no_write:acceptance_fact_effect")
    _require_exact(
        result["terminal_fact_created"] is False,
        "no_write:terminal_fact_created",
    )
    _require_exact(type(result["audit_trace"]) is tuple, "no_write:audit_trace")


def _baseline(contract: dict[str, object]) -> dict[str, object]:
    matrix = contract["matrix"]
    matrices: list[dict[str, object]] = []
    for owner in matrix["owners"]:
        entries: dict[str, dict[str, object]] = {}
        for branch, profile in matrix["branch_profiles"].items():
            profile_kind = "productive" if branch in matrix["productive_branches"] else "halt_only"
            entries[branch] = {
                "branch": branch,
                "applicability": profile["applicability"],
                "governed_effect_class": profile["governed_effect_class"],
                "result": "permit",
                "reason": matrix["permit_reasons"][owner][profile_kind],
            }
        matrices.append({"owner": owner, "entries": entries})
    return {
        "admission_fault": None,
        "validation": deepcopy(contract["validation_projection"][0]),
        "review": deepcopy(contract["review_projection"][0]),
        "currentness": "current",
        "matrices": matrices,
        "expected_branch": None,
        "model_recommendation": "accept_candidate",
        "guard_state": "exhaustively_unclaimed",
        "guard_relation": {role: "exact" for role in contract["guard"]["universal_exact_roles"]},
    }


def _matrix_mapping(
    contract: dict[str, object],
    state: dict[str, object],
) -> tuple[dict[str, dict[str, object]] | None, str | None]:
    matrix = contract["matrix"]
    matrices = state.get("matrices")
    if type(matrices) is not list:
        return None, matrix["malformed_inventory_rejection"]
    owners = [item.get("owner") if type(item) is dict else None for item in matrices]
    if owners != matrix["owners"]:
        if len(owners) == len(matrix["owners"]) and any(
            owner not in matrix["owners"] for owner in owners
        ):
            return None, matrix["productive_profile_or_pair_rejection"]
        return None, matrix["malformed_inventory_rejection"]
    mapped: dict[str, dict[str, object]] = {}
    expected_branches = set(matrix["branch_profiles"])
    for item in matrices:
        if type(item) is not dict or set(item) != {"owner", "entries"}:
            return None, matrix["malformed_inventory_rejection"]
        owner = item["owner"]
        entries = item["entries"]
        if type(owner) is not str or type(entries) is not dict:
            return None, matrix["malformed_inventory_rejection"]
        if set(entries) != expected_branches:
            return None, matrix["malformed_inventory_rejection"]
        mapped[owner] = entries
    return mapped, None


def _entry_result(
    contract: dict[str, object],
    entries: dict[str, dict[str, object]],
    owner: str,
    branch: str,
    *,
    evaluate_semantics: bool = True,
) -> tuple[str | None, str | None]:
    matrix = contract["matrix"]
    entry = entries[owner][branch]
    profile_kind = (
        "productive" if branch in matrix["productive_branches"] else "halt_only"
    )
    profile_rejection = matrix[
        "productive_profile_or_pair_rejection"
        if profile_kind == "productive"
        else "halt_only_profile_or_pair_rejection"
    ]
    if type(entry) is not dict or set(entry) != {
        "branch", "applicability", "governed_effect_class", "result", "reason",
    }:
        return profile_rejection, None
    if entry["branch"] != branch:
        return profile_rejection, None
    profile = matrix["branch_profiles"][branch]
    if (
        entry["applicability"] != profile["applicability"]
        or entry["governed_effect_class"] != profile["governed_effect_class"]
    ):
        return profile_rejection, None
    result = entry["result"]
    reason = entry["reason"]
    if type(result) is not str or result not in matrix["results"]:
        return profile_rejection, None
    if type(reason) is not str:
        return profile_rejection, None
    pair = {"result": result, "reason": reason}
    unreachable_pair = any(
        pair == {"result": item["result"], "reason": item["reason"]}
        for item in contract["metadata_only_unreachable_pairs"][owner]
    )
    if unreachable_pair:
        return matrix["metadata_unreachable_rejection"], None
    if pair not in contract["accepted_emittable_pairs"][owner]:
        return profile_rejection, None
    if result == "conflict" and evaluate_semantics:
        return matrix["exact_conflict_pair_rejection"], None
    if result == "permit":
        if reason != matrix["permit_reasons"][owner][profile_kind]:
            return profile_rejection, None
    return None, result


def _interpret_pre_model(
    contract: dict[str, object],
    state: dict[str, object],
) -> dict[str, object]:
    trace: list[str] = []
    relation = state.get("guard_relation")
    if type(relation) is not dict or set(relation) != set(contract["guard"]["universal_exact_roles"]) or any(value != "exact" for value in relation.values()):
        return _no_write("bootstrap_acceptance_guard_conflict", tuple(trace))
    fault = state.get("admission_fault")
    if fault is not None:
        rejection = contract["admission_fault_to_rejection"].get(
            fault, contract["invalid_projection_rejection"]
        )
        return _no_write(rejection, tuple(trace))

    validation = state.get("validation")
    review = state.get("review")
    if type(validation) is not dict or type(review) is not dict:
        return _no_write(contract["invalid_projection_rejection"], tuple(trace))
    trace.append("basis_validated")

    matrices, matrix_rejection = _matrix_mapping(contract, state)
    if matrix_rejection is not None:
        return _no_write(matrix_rejection, tuple(trace))
    assert matrices is not None
    matrix = contract["matrix"]
    for owner in matrix["owners"]:
        for branch in matrix["branch_profiles"]:
            rejection, _ = _entry_result(
                contract,
                matrices,
                owner,
                branch,
                evaluate_semantics=False,
            )
            if rejection is not None:
                return _no_write(rejection, tuple(trace))
    trace.append("matrix_grammar_validated")

    currentness = state.get("currentness")
    if currentness not in contract["currentness"]:
        return _no_write(contract["invalid_projection_rejection"], tuple(trace))
    currentness_effect = contract["currentness"][currentness]
    trace.append("currentness_reduced")
    if currentness_effect == "no_write":
        return _no_write(
            "basis_identity_lineage_profile_provenance_conflict",
            tuple(trace),
        )

    validation_class = _normal_class(contract, validation, review=False)
    review_class = _normal_class(contract, review, review=True)
    if validation_class is None or review_class is None:
        return _no_write(contract["invalid_projection_rejection"], tuple(trace))
    if "conflict" in {validation_class, review_class}:
        return _no_write(
            "basis_identity_lineage_profile_provenance_conflict",
            tuple(trace),
        )

    if "nonconclusive" in {validation_class, review_class}:
        normalized = "nonconclusive"
    else:
        severity = contract["conclusive_severity_low_to_high"]
        normalized = max((validation_class, review_class), key=severity.index)
    trace.append("validation_review_reduced")

    candidate_branch = contract["normalized_candidate_branch"][normalized]
    candidate_reason = contract["candidate_reason_by_normalized_class"][normalized]
    block_reasons: list[str] = []
    if currentness_effect == "decision_basis_not_current":
        block_reasons.append("decision_basis_not_current")
    if normalized == "nonconclusive":
        block_reasons.append("candidate_evidence_nonconclusive")

    productive_evidence: dict[str, object] | None = None
    if candidate_branch in matrix["productive_branches"]:
        productive_results: list[str] = []
        owner_entries: list[dict[str, object]] = []
        productive_rejection: str | None = None
        trace.append("productive_matrix_evaluated")
        for owner in matrix["owners"]:
            rejection, result = _entry_result(
                contract, matrices, owner, candidate_branch
            )
            entry = matrices[owner][candidate_branch]
            owner_entries.append(
                {
                    "owner": owner,
                    "branch": entry["branch"],
                    "applicability": entry["applicability"],
                    "governed_effect_class": entry["governed_effect_class"],
                    "result": entry["result"],
                    "reason": entry["reason"],
                }
            )
            if rejection is not None:
                productive_rejection = rejection
            else:
                assert result is not None
                productive_results.append(result)
        productive_evidence = {
            "provisional_productive_branch": candidate_branch,
            "owner_entries": owner_entries,
        }
        if productive_rejection is not None:
            return _no_write(
                productive_rejection,
                tuple(trace),
                productive_matrix_evidence=productive_evidence,
            )
        if any(result in {"deny", "unknown"} for result in productive_results):
            block_reasons.append("productive_branch_not_permitted")

    if block_reasons:
        branch = "post_execution_program_block"
        reason = next(
            value for value in contract["block_reason_precedence"]
            if value in block_reasons
        )
    else:
        branch = candidate_branch
        reason = candidate_reason
    trace.append("branch_selected")

    if branch in matrix["halt_only_required_branches"]:
        trace.append("halt_only_matrix_evaluated")
        for owner in matrix["owners"]:
            rejection, result = _entry_result(
                contract, matrices, owner, branch
            )
            if rejection is not None:
                return _no_write(
                    rejection,
                    tuple(trace),
                    **(
                        {"productive_matrix_evidence": productive_evidence}
                        if productive_evidence is not None
                        else {}
                    ),
                )
            assert result is not None
            if result != matrix["halt_only_required_result"]:
                return _no_write(
                    matrix["halt_only_profile_or_pair_rejection"],
                    tuple(trace),
                    **(
                        {"productive_matrix_evidence": productive_evidence}
                        if productive_evidence is not None
                        else {}
                    ),
                )

    expected_branch = state.get("expected_branch")
    if expected_branch is not None:
        if expected_branch not in matrix["branch_profiles"]:
            return _no_write(contract["invalid_projection_rejection"], tuple(trace))
        if expected_branch != branch:
            return _no_write(contract["expected_branch"]["mismatch"], tuple(trace))

    return {
        'outcome': 'pre_model', 'branch': branch, 'reason': reason,
        'candidate_reason': candidate_reason, 'retained_basis': deepcopy(state),
        'deferred_model_inputs': state.get('model_recommendation'),
        'audit_trace': tuple(trace),
        **({'productive_matrix_evidence': productive_evidence} if productive_evidence is not None else {}),
    }


def _c2_guard_gate(contract, prepared):
    """The existing supplied guard-evidence gate, before any model projection."""
    if prepared['outcome'] == 'no_write':
        return prepared
    result = deepcopy(prepared)
    branch = result['branch']
    if branch == 'candidate_acceptance':
        result['audit_trace'] += ('bootstrap_acceptance_guard_checked',)
        if result['retained_basis'].get('guard_state') != contract['guard']['accept_required_evidence']:
            return _no_write(contract['guard']['accept_invalid_result'], result['audit_trace'])
        result['acceptance_fact_effect'] = contract['guard']['accept_effect']
    else:
        result['acceptance_fact_effect'] = contract['guard']['nonaccept_effect']
    result['_guard_gates_passed'] = True
    return result


def _model_consistency_phase(contract, prepared):
    """One final model phase; it cannot precede the authoritative guard gates."""
    if prepared['outcome'] == 'no_write':
        return prepared
    _require_exact(prepared.get('_guard_gates_passed') is True, 'c2:model_after_guard:guard_gate')
    branch = prepared['branch']
    trace = list(prepared['audit_trace'])
    recommendation = prepared['deferred_model_inputs']
    trace.append('model_consistency_evaluated')
    if type(recommendation) is not str:
        return _no_write(contract['invalid_projection_rejection'], tuple(trace))
    recommendation_map = contract['model']['recommendation_to_branch']
    if recommendation not in recommendation_map:
        model_evidence = contract['model']['unrecognized']
    elif recommendation_map[recommendation] == branch:
        model_evidence = contract['model']['recognized_equal']
    else:
        model_evidence = contract['model']['recognized_unequal']
    mapping = contract['branch_mapping'][branch]
    return {
        'outcome': 'durable_decision', 'branch': branch,
        'decision_kind': mapping['decision_kind'], 'decision_variant': mapping['decision_variant'],
        'reason': prepared['reason'], 'candidate_reason': prepared['candidate_reason'],
        'decision_created': True, 'version_advanced': mapping['version_advancing'],
        'head_mutated': True, 'receipt_created': True,
        'acceptance_fact_effect': prepared['acceptance_fact_effect'], 'terminal_fact_created': False,
        'model_consistent': model_evidence['status'] == 'consistent',
        'model_consistency': model_evidence['status'], 'model_consistency_reason': model_evidence['reason'],
        'retained_basis': prepared['retained_basis'], 'audit_trace': tuple(trace),
        **({'productive_matrix_evidence': prepared['productive_matrix_evidence']}
           if 'productive_matrix_evidence' in prepared else {}),
    }


def _interpret(contract: dict[str, object], state: dict[str, object]) -> dict[str, object]:
    """Standalone composition retains the original C2 output and trace semantics."""
    return _model_consistency_phase(contract, _c2_guard_gate(contract, _interpret_pre_model(contract, state)))


def _set_matrix_result(
    contract: dict[str, object],
    state: dict[str, object],
    owner: str,
    branch: str,
    result: str,
    reason: str | None = None,
) -> None:
    entry = _matrix_entry(state, owner, branch)
    if reason is None:
        if result == "permit":
            profile_kind = (
                "productive"
                if branch in contract["matrix"]["productive_branches"]
                else "halt_only"
            )
            reason = contract["matrix"]["permit_reasons"][owner][profile_kind]
        else:
            reason = _first_owner_pair(contract, owner, result)["reason"]
    entry["result"] = result
    entry["reason"] = reason


def _matrix_entry(
    state: dict[str, object],
    owner: str,
    branch: str,
) -> dict[str, object]:
    matrices = state["matrices"]
    assert isinstance(matrices, list)
    item = next(item for item in matrices if item["owner"] == owner)
    return item["entries"][branch]


def _expanded_validation_cases(
    contract: dict[str, object],
) -> tuple[dict[str, object], ...]:
    cases = [deepcopy(row) for row in contract["validation_projection"]]
    outcomes = {row["source_outcome"] for row in contract["validation_projection"]}
    for outcome in sorted(outcomes):
        row = deepcopy(contract["validation_conflict_projection"])
        row["source_outcome"] = outcome
        cases.append(row)
    return tuple(cases)


def _expanded_review_cases(
    contract: dict[str, object],
) -> tuple[dict[str, object], ...]:
    cases = [deepcopy(row) for row in contract["review_projection"]]
    outcomes = {row["source_outcome"] for row in contract["review_projection"]}
    for override in contract["review_override_projection"]:
        for outcome in sorted(outcomes):
            row = deepcopy(override)
            row["source_outcome"] = outcome
            cases.append(row)
    return tuple(cases)


def _replace_in_region(
    text: str,
    begin: str,
    end: str,
    old: str,
    new: str,
) -> str:
    prefix, tail = text.split(begin, 1)
    body, suffix = tail.split(end, 1)
    assert body.count(old) == 1
    return prefix + begin + body.replace(old, new, 1) + end + suffix


def _recover(
    contract: dict[str, object],
    *,
    commit_attempted: bool,
    readback: str | None = None,
    expected_family: dict[str, object] | None = None,
    observed_family: dict[str, object] | None = None,
    exhaustive: bool = True,
    collision_or_read_fault: bool = False,
) -> dict[str, object]:
    if not commit_attempted:
        raise ValueError("recovery classification requires commit-attempt uncertainty")
    if expected_family is not None:
        if exhaustive and not collision_or_read_fault and observed_family == expected_family:
            readback = "exact_family"
        elif exhaustive and not collision_or_read_fault and observed_family == {}:
            readback = "provably_absent"
        else:
            readback = "ambiguous"
    classification = contract["recovery"]["readback"][readback]
    return {
        "outcome": "recovery_unresolved" if classification == "unresolved" else classification,
        "classification": classification,
        "decision_created_by_recovery": False,
        "guard_mutated_by_recovery": False,
    }


def _replace_matrix_pairs(
    mapping: dict[str, object],
    governed: tuple[str, str],
    halt_only: tuple[str, str],
) -> None:
    for entry in mapping["entries"]:
        pair = halt_only if entry["applicability"] == "halt_only" else governed
        entry["result"], entry["reason"] = pair


def _observed_pairs(value: object) -> set[tuple[str, str]]:
    return {
        (entry["result"], entry["reason"])
        for entry in value.to_mapping()["entries"]
    }


def _standing_policy_witness(scenario: str) -> object:
    source_mapping = _sample("V41")
    candidate_mapping = _sample("V17")
    reason = scenario
    if reason == "policy_revoked":
        source_mapping["revocation_status"] = "revoked"
        candidate_mapping["policy_revocation_status"] = "revoked"
    elif reason == "branch_not_allowed":
        source_mapping["allowed_branches"] = source_mapping["allowed_branches"][1:]
        candidate_mapping["allowed_branches"] = candidate_mapping["allowed_branches"][1:]
    elif reason == "risk_lane_not_allowed":
        source_mapping["allowed_risk_lanes"] = ["risk.high"]
        candidate_mapping["allowed_risk_lanes"] = ["risk.high"]
    elif reason == "effect_class_not_allowed":
        source_mapping["allowed_effect_classes"] = [
            "review_candidate",
            "validate_candidate",
        ]
        candidate_mapping["allowed_effect_classes"] = [
            "review_candidate",
            "validate_candidate",
        ]
    elif reason == "policy_status_unknown":
        source_mapping["policy_status"] = "unknown"
        candidate_mapping["policy_status"] = "unknown"
    elif reason == "policy_currentness_unknown":
        source_mapping["policy_status"] = "inactive"
        candidate_mapping["policy_status"] = "inactive"

    source_governed = {
        "policy_revoked": ("deny", "policy_revoked"),
        "effect_class_not_allowed": ("deny", "effect_class_not_allowed"),
        "policy_status_unknown": ("unknown", "policy_status_unknown"),
        "policy_currentness_unknown": ("unknown", "policy_currentness_unknown"),
    }.get(reason, ("permit", "policy_permits"))
    _replace_matrix_pairs(
        {"entries": source_mapping["branch_assertions"]},
        source_governed,
        ("permit", "halt_only_policy_not_applicable"),
    )
    if reason == "branch_not_allowed":
        source_mapping["branch_assertions"][0].update(
            result="deny",
            reason="branch_not_allowed",
        )
    source = production_policy.validate_post_execution_standing_policy_attestation(
        _seal("V41", source_mapping)
    )
    source_values = source.to_mapping()
    field_pairs = (
        ("policy_source_schema_id", "schema_id"),
        ("policy_source_ref", "attestation_ref"),
        ("policy_source_digest", "attestation_digest"),
        ("matrix_author_ref", "source_owner_ref"),
        ("matrix_author_invocation_ref", "source_owner_invocation_ref"),
        ("policy_status", "policy_status"),
        ("policy_revocation_status", "revocation_status"),
        ("parent_grant_ref", "parent_grant_ref"),
        ("parent_grant_digest", "parent_grant_digest"),
        ("grant_family_ref", "grant_family_ref"),
        ("grant_family_digest", "grant_family_digest"),
        ("audience_ref", "audience_ref"),
        ("repository_ref", "repository_ref"),
        ("path_scope_digest", "path_scope_digest"),
        ("allowed_branches", "allowed_branches"),
        ("allowed_risk_lanes", "allowed_risk_lanes"),
        ("allowed_effect_classes", "allowed_effect_classes"),
        ("not_before", "not_before"),
        ("expires_at", "expires_at"),
        ("evaluated_at", "evaluated_at"),
    )
    for target, origin in field_pairs:
        candidate_mapping[target] = deepcopy(source_values[origin])
    candidate_mapping["policy_ceilings"] = {
        field: source_values[field]
        for field in candidate_mapping["policy_ceilings"]
    }
    candidate_governed = (
        ("deny", "risk_lane_not_allowed")
        if reason == "risk_lane_not_allowed"
        else source_governed
    )
    _replace_matrix_pairs(
        candidate_mapping,
        candidate_governed,
        ("permit", "halt_only_policy_not_applicable"),
    )
    if reason == "branch_not_allowed":
        candidate_mapping["entries"][0].update(
            result="deny",
            reason="branch_not_allowed",
        )
    candidate = _seal("V17", candidate_mapping)
    return production_policy.validate_post_execution_standing_policy_matrix_relation(
        candidate,
        policy_source=source,
    )


def _risk_lane_witness(scenario: str) -> object:
    policy_mapping = _sample("V42")
    source_mapping = _sample("V19")
    candidate_mapping = _sample("V18")
    reason = scenario
    if reason == "policy_revoked":
        policy_mapping["revocation_status"] = "revoked"
    elif reason == "required_lane_mismatch":
        source_mapping["risk_lane"] = "risk.high"
    elif reason == "policy_status_unknown":
        policy_mapping["policy_status"] = "unknown"
    policy_governed = {
        "policy_revoked": ("deny", "policy_revoked"),
        "policy_status_unknown": ("unknown", "policy_status_unknown"),
    }.get(reason, ("permit", "risk_lane_permits"))
    _replace_matrix_pairs(
        {"entries": policy_mapping["branch_assertions"]},
        policy_governed,
        ("permit", "halt_only_risk_lane_not_applicable"),
    )
    policy_value = production_policy.validate_post_execution_risk_policy_attestation(
        _seal("V42", policy_mapping)
    )
    profile, binding = production_risk_adapter.finite_backlog_risk_source_projection(
        _seal("V19", source_mapping),
        evaluated_at=_sample("V44")["evaluated_at"],
        expires_at=_sample("V44")["expires_at"],
    )
    policy_values = policy_value.to_mapping()
    profile_values = profile.to_mapping()
    binding_values = binding.to_mapping()
    for target, origin in (
        ("risk_policy_schema_id", "schema_id"),
        ("risk_policy_ref", "attestation_ref"),
        ("risk_policy_digest", "attestation_digest"),
        ("matrix_author_ref", "source_owner_ref"),
        ("matrix_author_invocation_ref", "source_owner_invocation_ref"),
        ("policy_status", "policy_status"),
        ("policy_revocation_status", "revocation_status"),
        ("allowed_risk_lanes", "allowed_risk_lanes"),
        ("required_risk_lane", "required_risk_lane"),
        ("not_before", "not_before"),
        ("expires_at", "expires_at"),
        ("evaluated_at", "evaluated_at"),
    ):
        candidate_mapping[target] = deepcopy(policy_values[origin])
    for target, origin in (
        ("source_profile_schema_id", "schema_id"),
        ("source_profile_ref", "source_profile_ref"),
        ("source_profile_digest", "source_profile_digest"),
    ):
        candidate_mapping[target] = profile_values[origin]
    for target, origin in (
        ("source_binding_schema_id", "schema_id"),
        ("source_binding_ref", "source_binding_ref"),
        ("source_binding_digest", "source_binding_digest"),
        ("development_work_item_ref", "development_work_item_ref"),
        ("risk_lane", "risk_lane"),
    ):
        candidate_mapping[target] = binding_values[origin]
    candidate_governed = (
        ("deny", "required_lane_mismatch")
        if reason == "required_lane_mismatch"
        else policy_governed
    )
    _replace_matrix_pairs(
        candidate_mapping,
        candidate_governed,
        ("permit", "halt_only_risk_not_applicable"),
    )
    return production_policy.validate_post_execution_risk_lane_matrix_relation(
        _seal("V18", candidate_mapping),
        risk_policy=policy_value,
        source_profile=profile,
        source_binding=binding,
    )


def _rebuild_worker_value(
    model: str,
    value_type: type,
    value: object,
    **changes: object,
) -> object:
    mapping = value.to_mapping()
    mapping.update(changes)
    return value_type.from_mapping(_reseal_single_digest_record(model, mapping))


def _rebuild_authority_observation(
    value: object,
    **changes: object,
) -> RW0AuthorityVerificationObservationV1:
    mapping = value.to_mapping()
    mapping.update(changes)
    supplied = {
        key: item
        for key, item in mapping.items()
        if key not in {"schema_id", "observation_digest"}
    }
    return RW0AuthorityVerificationObservationV1.from_mapping(
        mapping_for(RW0AuthorityVerificationObservationV1, **supplied)
    )


def _standing_policy_matrix_for_ceiling(
    attempt: AttemptFenceV1,
    effect: EffectFenceV1,
    authority: RW0AuthorityVerificationObservationV1,
) -> object:
    attempt_mapping = attempt.to_mapping()
    effect_mapping = effect.to_mapping()
    authority_mapping = authority.to_mapping()
    source_mapping = _sample("V41")
    source_mapping.update(
        parent_grant_ref=authority_mapping["parent_grant_ref"],
        parent_grant_digest=authority_mapping["parent_grant_digest"],
        grant_family_ref=authority_mapping["grant_family_ref"],
        grant_family_digest=authority_mapping["grant_family_digest"],
        audience_ref=authority_mapping["audience_ref"],
        repository_ref=authority_mapping["repository_ref"],
        path_scope_digest=authority_mapping["path_scope_digest"],
        allowed_effect_classes=authority_mapping["allowed_effect_classes"],
    )
    for field in tuple(source_mapping):
        if field.startswith("max_"):
            source_mapping[field] = authority_mapping["parent_ceilings"][field]
    governed = (
        ("permit", "policy_permits")
        if "author_candidate" in source_mapping["allowed_effect_classes"]
        else ("deny", "effect_class_not_allowed")
    )
    _replace_matrix_pairs(
        {"entries": source_mapping["branch_assertions"]},
        governed,
        ("permit", "halt_only_policy_not_applicable"),
    )
    source = production_policy.validate_post_execution_standing_policy_attestation(
        _seal("V41", source_mapping)
    )
    source_values = source.to_mapping()
    candidate_mapping = _sample("V17")
    for target, origin in (
        ("policy_source_schema_id", "schema_id"),
        ("policy_source_ref", "attestation_ref"),
        ("policy_source_digest", "attestation_digest"),
        ("matrix_author_ref", "source_owner_ref"),
        ("matrix_author_invocation_ref", "source_owner_invocation_ref"),
        ("policy_status", "policy_status"),
        ("policy_revocation_status", "revocation_status"),
        ("parent_grant_ref", "parent_grant_ref"),
        ("parent_grant_digest", "parent_grant_digest"),
        ("grant_family_ref", "grant_family_ref"),
        ("grant_family_digest", "grant_family_digest"),
        ("audience_ref", "audience_ref"),
        ("repository_ref", "repository_ref"),
        ("path_scope_digest", "path_scope_digest"),
        ("allowed_branches", "allowed_branches"),
        ("allowed_risk_lanes", "allowed_risk_lanes"),
        ("allowed_effect_classes", "allowed_effect_classes"),
        ("not_before", "not_before"),
        ("expires_at", "expires_at"),
        ("evaluated_at", "evaluated_at"),
    ):
        candidate_mapping[target] = deepcopy(source_values[origin])
    candidate_mapping.update(
        program_ref=attempt_mapping["program_ref"],
        program_version_ref=attempt_mapping["program_version_ref"],
        accepted_intent_revision_ref=attempt_mapping[
            "accepted_intent_revision_ref"
        ],
        work_item_ref=attempt_mapping["work_item_ref"],
        work_item_revision_ref=attempt_mapping["work_item_revision_ref"],
        semantic_attempt_ref=attempt_mapping["semantic_attempt_ref"],
        candidate_ref=effect_mapping["candidate_ref"],
        effect_intent_ref=effect_mapping["effect_intent_ref"],
        author_command_ref=effect_mapping["command_ref"],
        source_effect_fence_ref=effect_mapping["effect_fence_ref"],
        source_effect_fence_digest=effect_mapping["effect_fence_digest"],
        source_effect_class=effect_mapping["effect_class"],
        policy_ceilings={
            field: source_values[field]
            for field in candidate_mapping["policy_ceilings"]
        },
    )
    _replace_matrix_pairs(
        candidate_mapping,
        governed,
        ("permit", "halt_only_policy_not_applicable"),
    )
    return production_policy.validate_post_execution_standing_policy_matrix_relation(
        _seal("V17", candidate_mapping),
        policy_source=source,
    )


def _support_set_for_ceiling(
    attempt: AttemptFenceV1,
    effect: EffectFenceV1,
    authority: RW0AuthorityVerificationObservationV1,
    policy: object,
) -> object:
    attempt_mapping = attempt.to_mapping()
    effect_mapping = effect.to_mapping()
    authority_mapping = authority.to_mapping()
    support_mapping = _ordered_fixture(
        "V13",
        deepcopy(_TEST_RECORDS["golden.V13.effect-ceiling.support-set"]),
    )
    sources = (
        (
            attempt_mapping["schema_id"],
            attempt_mapping["attempt_fence_ref"],
            attempt_mapping["attempt_fence_digest"],
        ),
        (
            effect_mapping["schema_id"],
            effect_mapping["effect_fence_ref"],
            effect_mapping["effect_fence_digest"],
        ),
        (
            authority_mapping["schema_id"],
            authority_mapping["observation_ref"],
            authority_mapping["observation_digest"],
        ),
        (policy.schema_id, policy.matrix_ref, policy.matrix_digest),
    )
    for entry, (schema_id, source_ref, source_digest) in zip(
        support_mapping["entries"], sources, strict=False
    ):
        entry.update(
            source_schema_id=schema_id,
            source_ref=source_ref,
            source_digest=source_digest,
        )
    candidate = CLASS_BY_V["V13"].from_mapping(_seal("V13", support_mapping))
    return production_evidence.construct_post_execution_support_set(
        candidate,
        entries=tuple(candidate.entries),
    )


def _ceiling_relation_case(
    scenario: str,
) -> tuple[object, AttemptFenceV1, EffectFenceV1, object, object, object]:
    baseline = CLASS_BY_V["V21"].from_mapping(_sample("V21"))
    attempt = AttemptFenceV1.from_mapping(
        deepcopy(_TEST_RECORDS["source-owner.attempt-fence"]["canonical_value"])
    )
    effect = EffectFenceV1.from_mapping(
        deepcopy(_TEST_RECORDS["source-owner.effect-fence"]["canonical_value"])
    )
    authority = RW0AuthorityVerificationObservationV1.from_mapping(
        deepcopy(
            _TEST_RECORDS[
                "golden.V11.role-supply.11.authority_currentness_attestation"
            ]["typed_canonical_value"]
        )
    )
    decision_time = "2026-09-30T12:00:03Z"
    attempt_changes: dict[str, object] = {}
    effect_changes: dict[str, object] = {}
    authority_changes: dict[str, object] = {}
    if scenario == "authority_incompatible":
        authority_changes["family_status"] = "incompatible"
    elif scenario == "authority_denied":
        authority_changes["status"] = "denied"
    elif scenario == "authority_revoked":
        authority_changes["revocation_status"] = "revoked"
    elif scenario == "attempt_expired":
        attempt_changes["expires_at"] = decision_time
    elif scenario == "effect_expired":
        effect_changes["expires_at"] = decision_time
    elif scenario == "grant_expired":
        authority_changes["grant_expires_at"] = decision_time
    elif scenario == "observation_expired":
        authority_changes["observation_expires_at"] = decision_time
    elif scenario == "effect_class_attempt":
        attempt_changes["allowed_effect_classes"] = ["review_candidate"]
    elif scenario == "effect_class_authority":
        authority_changes["allowed_effect_classes"] = ["review_candidate"]
    elif scenario == "exceeds_attempt":
        ceilings = deepcopy(attempt.to_mapping()["aggregate_ceilings"])
        ceilings["max_candidate_bytes"] = 1
        attempt_changes["aggregate_ceilings"] = ceilings
    elif scenario == "exceeds_authority":
        ceilings = deepcopy(authority.to_mapping()["parent_ceilings"])
        ceilings["max_candidate_bytes"] = 1
        authority_changes["parent_ceilings"] = ceilings
    elif scenario == "authority_unknown":
        authority_changes["status"] = "unknown"
    elif scenario == "family_unknown":
        authority_changes["family_status"] = "unknown"
    elif scenario == "revocation_unknown":
        authority_changes["revocation_status"] = "unknown"
    elif scenario != "baseline":
        raise AssertionError(f"unknown ceiling witness scenario {scenario}")

    if attempt_changes:
        attempt = _rebuild_worker_value(
            "AttemptFenceV1", AttemptFenceV1, attempt, **attempt_changes
        )
        effect_changes["attempt_fence_digest"] = attempt.attempt_fence_digest
    if effect_changes:
        effect = _rebuild_worker_value(
            "EffectFenceV1", EffectFenceV1, effect, **effect_changes
        )
    if attempt_changes or effect_changes:
        authority_changes.update(
            attempt_fence_digest=attempt.attempt_fence_digest,
            effect_fence_digest=effect.effect_fence_digest,
        )
    if authority_changes:
        authority = _rebuild_authority_observation(authority, **authority_changes)

    policy = _standing_policy_matrix_for_ceiling(attempt, effect, authority)
    support = _support_set_for_ceiling(
        attempt,
        effect,
        authority,
        policy,
    )
    attempt_mapping = attempt.to_mapping()
    effect_mapping = effect.to_mapping()
    authority_mapping = authority.to_mapping()
    mapping = baseline.to_mapping()
    mapping.update(
        program_ref=attempt_mapping["program_ref"],
        program_version_ref=attempt_mapping["program_version_ref"],
        accepted_intent_revision_ref=attempt_mapping[
            "accepted_intent_revision_ref"
        ],
        work_item_ref=attempt_mapping["work_item_ref"],
        work_item_revision_ref=attempt_mapping["work_item_revision_ref"],
        semantic_attempt_ref=attempt_mapping["semantic_attempt_ref"],
        candidate_ref=effect_mapping["candidate_ref"],
        effect_intent_ref=effect_mapping["effect_intent_ref"],
        repository_ref=effect_mapping["repository_ref"],
        base_git_object_format=effect_mapping["base_git_object_format"],
        base_git_oid=effect_mapping["base_git_oid"],
        source_effect_class=effect_mapping["effect_class"],
        source_effect_ceilings=effect_mapping["effect_ceilings"],
        path_scope_digest=authority_mapping["path_scope_digest"],
        attempt_fence_schema_id=attempt_mapping["schema_id"],
        attempt_fence_ref=attempt_mapping["attempt_fence_ref"],
        attempt_fence_digest=attempt_mapping["attempt_fence_digest"],
        attempt_allowed_effect_classes=attempt_mapping[
            "allowed_effect_classes"
        ],
        attempt_ceilings=attempt_mapping["aggregate_ceilings"],
        attempt_fence_expires_at=attempt_mapping["expires_at"],
        effect_fence_schema_id=effect_mapping["schema_id"],
        effect_fence_ref=effect_mapping["effect_fence_ref"],
        effect_fence_digest=effect_mapping["effect_fence_digest"],
        effect_fence_class=effect_mapping["effect_class"],
        effect_ceilings=effect_mapping["effect_ceilings"],
        effect_fence_expires_at=effect_mapping["expires_at"],
        authority_schema_id=authority_mapping["schema_id"],
        authority_observation_ref=authority_mapping["observation_ref"],
        authority_observation_digest=authority_mapping["observation_digest"],
        authority_status=authority_mapping["status"],
        authority_family_status=authority_mapping["family_status"],
        authority_revocation_status=authority_mapping["revocation_status"],
        authority_allowed_effect_classes=authority_mapping[
            "allowed_effect_classes"
        ],
        authority_ceilings=authority_mapping["parent_ceilings"],
        authority_grant_expires_at=authority_mapping["grant_expires_at"],
        authority_observation_expires_at=authority_mapping[
            "observation_expires_at"
        ],
        evaluated_at="2026-09-30T12:00:02Z",
        support_set_ref=support.support_set_ref,
        support_set_digest=support.support_set_digest,
    )
    if scenario == "authority_incompatible":
        relation_pair = ("conflict", "authority_identity_conflict")
    elif scenario in {"authority_denied", "authority_revoked"}:
        relation_pair = ("noncompliant", "authority_denied_or_revoked")
    elif scenario == "effect_class_attempt":
        relation_pair = ("noncompliant", "effect_class_not_allowed_by_attempt")
    elif scenario == "effect_class_authority":
        relation_pair = (
            "noncompliant",
            "effect_class_not_allowed_by_authority",
        )
    elif scenario == "exceeds_attempt":
        relation_pair = ("noncompliant", "effect_exceeds_attempt")
    elif scenario == "exceeds_authority":
        relation_pair = ("noncompliant", "effect_exceeds_authority")
    elif scenario == "authority_unknown":
        relation_pair = ("unknown", "authority_status_unknown")
    elif scenario == "family_unknown":
        relation_pair = ("unknown", "authority_family_unknown")
    elif scenario == "revocation_unknown":
        relation_pair = ("unknown", "authority_revocation_unknown")
    else:
        relation_pair = ("compliant", "source_effect_within_ceilings")
    mapping["result"], mapping["reason"] = relation_pair
    candidate = CLASS_BY_V["V21"].from_mapping(_seal("V21", mapping))
    observed = production_evidence.evaluate_post_execution_source_effect_ceiling(
        candidate,
        attempt_fence=attempt,
        effect_fence=effect,
        authority_observation=authority,
        standing_policy_matrix=policy,
        support_set=support,
    )
    return observed, attempt, effect, authority, policy, support


def _relation_backed_ceiling(scenario: str) -> object:
    return _ceiling_relation_case(scenario)[0]


def _decision_matrix_candidate(
    v_number: str,
    chain: dict[str, object],
    governed: tuple[str, str],
    halt_only: tuple[str, str],
    *,
    snapshot: object | None = None,
    source_effect_ceiling: object | None = None,
    global_stop_snapshot: object | None = None,
    evaluated_at: str | None = None,
) -> dict[str, object]:
    active_snapshot = chain["snapshot"] if snapshot is None else snapshot
    mapping = _sample(v_number)
    mapping.update(
        snapshot_ref=active_snapshot.snapshot_ref,
        snapshot_digest=active_snapshot.snapshot_digest,
    )
    if v_number == "V31":
        mapping.update(
            proposal_ref=chain["projection"].proposal_ref,
            proposal_digest=chain["projection"].proposal_digest,
        )
    elif v_number == "V32":
        stop = chain["stop"] if global_stop_snapshot is None else global_stop_snapshot
        mapping.update(
            global_stop_ref=stop.global_stop_ref,
            global_stop_digest=stop.global_stop_digest,
        )
    else:
        ceiling = chain["ceiling"] if source_effect_ceiling is None else source_effect_ceiling
        mapping.update(
            source_effect_ceiling_ref=ceiling.evidence_ref,
            source_effect_ceiling_digest=ceiling.evidence_digest,
        )
    if evaluated_at is not None:
        mapping["evaluated_at"] = evaluated_at
    _replace_matrix_pairs(mapping, governed, halt_only)
    return _seal(v_number, mapping)


def _action_backed_current_sources() -> tuple[object, ...]:
    validation_inputs = _qualified_result_set("V38")
    validation = production_evidence.validate_post_execution_validation_result_set(
        validation_inputs[0],
        source_observation=validation_inputs[1],
        requirement_evidence=validation_inputs[2],
        tool_qualification=validation_inputs[3],
    )
    review_inputs = _qualified_result_set("V39")
    review = production_evidence.validate_post_execution_review_result_set(
        review_inputs[0],
        source_observation=review_inputs[1],
        requirement_evidence=review_inputs[2],
        tool_qualification=review_inputs[3],
    )
    policy = production_policy.validate_post_execution_standing_policy_attestation(
        _sample("V41")
    )
    risk_profile, risk_binding = (
        production_risk_adapter.finite_backlog_risk_source_projection(
            _sample("V19"),
            evaluated_at=_sample("V44")["evaluated_at"],
            expires_at=_sample("V44")["expires_at"],
        )
    )
    return validation, review, policy, risk_profile, risk_binding


def _clear_global_stop_snapshot() -> object:
    candidate = CLASS_BY_V["V13"].from_mapping(
        _ordered_fixture(
            "V13",
            deepcopy(_TEST_RECORDS["golden.V13.global-stop.support-set"]),
        )
    )
    support = production_evidence.construct_post_execution_support_set(
        candidate,
        entries=tuple(candidate.entries),
    )
    return production_evidence.post_execution_global_stop_snapshot(
        _sample("V20"),
        current_state=GlobalStopState(version=7),
        updated_at="2026-09-30T11:59:45Z",
        support_set=support,
    )


def _production_decision_chain(
    ceiling: object | None = None,
    *,
    active_stop: bool = False,
) -> dict[str, object]:
    current_ceiling = (
        _relation_backed_ceiling("baseline") if ceiling is None else ceiling
    )
    owners = _section41_owner_inputs()
    lineage_mapping = _sample("V01")
    for field in (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "candidate_ref",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
    ):
        lineage_mapping[field] = getattr(current_ceiling, field)
    lineage = CLASS_BY_V["V01"].from_mapping(_seal("V01", lineage_mapping))
    if (
        owners["context"].lineage_context_ref == lineage.lineage_context_ref
        and owners["context"].lineage_context_digest
        == lineage.lineage_context_digest
    ):
        context = owners["context"]
    else:
        context_mapping = _sample("V02")
        context_mapping.update(
            lineage_context_schema_id=lineage.schema_id,
            lineage_context_ref=lineage.lineage_context_ref,
            lineage_context_digest=lineage.lineage_context_digest,
        )
        context = production_evidence.construct_post_execution_semantic_review_input(
            _seal("V02", context_mapping),
            lineage_context=lineage,
            role_entries=tuple(
                CLASS_BY_V["V03"].from_mapping(entry)
                for entry in context_mapping["role_entries"]
            ),
            safe_projection=CLASS_BY_V["V05"].from_mapping(_sample("V05")),
            private_manifest=CLASS_BY_V["V07"].from_mapping(_sample("V07")),
        )
    authority_entry_mapping = _sample("V26", 0)
    authority_entry_mapping.update(
        value_ref=current_ceiling.authority_observation_ref,
        value_digest=current_ceiling.authority_observation_digest,
    )
    authority_entry = CLASS_BY_V["V26"].from_mapping(
        _seal("V26", authority_entry_mapping)
    )
    entries = (
        authority_entry,
        *tuple(
            CLASS_BY_V["V26"].from_mapping(_sample("V26", index))
            for index in range(1, 8)
        ),
    )
    pages = (production_decision._MembershipPage("epoch.1", (0, "0"), entries, None),)
    closure_mapping = _sample("V25")
    closure_mapping["entries"] = [entry.to_mapping() for entry in entries]
    closure = production_decision.rw0_c_decision_membership_closure(
        _seal("V25", closure_mapping),
        pages=pages,
    )
    stop = _active_stop_snapshot()[0] if active_stop else _clear_global_stop_snapshot()
    sources = _action_backed_current_sources()
    snapshot_mapping = _sample("V27")
    for field in (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "candidate_ref",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
    ):
        snapshot_mapping[field] = getattr(current_ceiling, field)
    snapshot_mapping.update(
        phase_basis_ref=closure.phase_basis_ref,
        phase_basis_digest=closure.phase_basis_digest,
        membership_closure_ref=closure.closure_ref,
        membership_closure_digest=closure.closure_digest,
        selected_authority_membership_ref=authority_entry.membership_ref,
        selected_authority_membership_digest=authority_entry.membership_digest,
        selected_section41_membership_ref=entries[7].membership_ref,
        selected_section41_membership_digest=entries[7].membership_digest,
        global_stop_ref=stop.global_stop_ref,
        global_stop_digest=stop.global_stop_digest,
        captured_at=closure.captured_at,
    )
    coordinate_fields = (
        "role",
        "source_schema_id",
        "source_ref",
        "source_digest",
        "profile_ref",
        "profile_digest",
        "source_available",
    )
    for index, (entry, source) in enumerate(
        zip(snapshot_mapping["external_sources"], sources, strict=True)
    ):
        entry.update(
            dict(
                zip(
                    coordinate_fields,
                    production_decision._source_coordinate(source, index),
                    strict=True,
                )
            )
        )
    snapshot = production_decision.rw0_c_decision_current_snapshot(
        _seal("V27", snapshot_mapping),
        lineage_context=lineage,
        input_context=context,
        membership_closure=closure,
        selected_authority_membership=authority_entry,
        selected_section41_membership=entries[7],
        global_stop_snapshot=stop,
        source_effect_ceiling=current_ceiling,
        external_sources=sources,
    )
    return {
        **owners,
        "lineage": lineage,
        "context": context,
        "entries": entries,
        "pages": pages,
        "closure": closure,
        "stop": stop,
        "ceiling": current_ceiling,
        "sources": sources,
        "snapshot": snapshot,
    }


def _authority_witness(scenario: str) -> object:
    ceiling_scenario = {
        "baseline": "baseline",
        "phase_mismatch": "baseline",
        "parent_mismatch": "baseline",
        "support_conflict": "authority_incompatible",
        "authority_denied": "authority_denied",
        "authority_revoked": "authority_revoked",
        "attempt_expired": "baseline",
        "effect_expired": "baseline",
        "grant_expired": "grant_expired",
        "observation_expired": "baseline",
        "effect_class": "effect_class_authority",
        "authority_unknown": "authority_unknown",
        "family_unknown": "family_unknown",
        "revocation_unknown": "revocation_unknown",
    }[scenario]
    ceiling = _relation_backed_ceiling(ceiling_scenario)
    chain = _production_decision_chain(ceiling)
    lineage = chain["lineage"]
    selected = chain["entries"][0]
    halt = ("permit", "halt_only_authority_not_applicable")
    if scenario == "phase_mismatch":
        selected = chain["entries"][1]
        governed = halt = ("conflict", "snapshot_or_phase_mismatch")
    elif scenario == "parent_mismatch":
        lineage_mapping = _sample("V01")
        lineage_mapping["candidate_ref"] = "candidate-hostile-lineage.0001"
        lineage = CLASS_BY_V["V01"].from_mapping(_seal("V01", lineage_mapping))
        governed = halt = ("conflict", "parent_or_fence_identity_mismatch")
    else:
        governed = {
            "baseline": ("permit", "authority_verified_current"),
            "support_conflict": ("conflict", "support_conflict"),
            "authority_denied": ("deny", "authority_denied"),
            "authority_revoked": ("deny", "authority_revoked"),
            "attempt_expired": ("deny", "attempt_fence_expired"),
            "effect_expired": ("deny", "effect_fence_expired"),
            "grant_expired": ("deny", "authority_grant_expired"),
            "observation_expired": ("deny", "authority_observation_expired"),
            "effect_class": ("deny", "effect_class_not_allowed"),
            "authority_unknown": ("unknown", "authority_status_unknown"),
            "family_unknown": ("unknown", "family_status_unknown"),
            "revocation_unknown": ("unknown", "revocation_status_unknown"),
        }[scenario]
        if governed[0] == "conflict":
            halt = governed
    candidate = _decision_matrix_candidate(
        "V31",
        chain,
        governed,
        halt,
        source_effect_ceiling=ceiling,
        evaluated_at={
            "attempt_expired": ceiling.attempt_fence_expires_at,
            "effect_expired": ceiling.effect_fence_expires_at,
            "grant_expired": ceiling.authority_grant_expires_at,
            "observation_expired": ceiling.authority_observation_expires_at,
        }.get(scenario),
    )
    return production_decision.evaluate_rw0_c_decision_time_authority_branches(
        candidate,
        snapshot=chain["snapshot"],
        projection=chain["projection"],
        lineage_context=lineage,
        input_context=chain["context"],
        membership_closure=chain["closure"],
        selected_authority_membership=selected,
        source_effect_ceiling=ceiling,
    )


def _global_stop_witness(scenario: str) -> object:
    chain = _production_decision_chain(active_stop=scenario == "active")
    snapshot = chain["snapshot"]
    stop = chain["stop"]
    governed = ("permit", "global_stop_clear")
    if scenario == "active":
        governed = ("deny", "global_stop_active")
    elif scenario != "baseline":
        raise AssertionError(f"unknown global-stop witness scenario {scenario}")
    candidate = _decision_matrix_candidate(
        "V32",
        chain,
        governed,
        ("permit", "halt_only_stop_checked"),
        snapshot=snapshot,
        global_stop_snapshot=stop,
    )
    return production_decision.evaluate_rw0_c_decision_time_global_stop_branches(
        candidate,
        snapshot=snapshot,
        global_stop_snapshot=stop,
    )


def _source_effect_ceiling_witness(
    scenario: str,
) -> object:
    ceiling_scenario = {
        "baseline": "baseline",
        "lineage_mismatch": "baseline",
        "proposal_conflict": "authority_incompatible",
        "proposal_noncompliant": "authority_denied",
        "attempt_expired": "baseline",
        "effect_expired": "baseline",
        "grant_expired": "grant_expired",
        "observation_expired": "baseline",
        "effect_class": "effect_class_authority",
        "exceeds_attempt": "exceeds_attempt",
        "exceeds_authority": "exceeds_authority",
        "authority_unknown": "authority_unknown",
    }[scenario]
    ceiling = _relation_backed_ceiling(ceiling_scenario)
    chain = _production_decision_chain(ceiling)
    lineage = chain["lineage"]
    halt = ("permit", "halt_only_ceiling_not_applicable")
    if scenario == "lineage_mismatch":
        lineage_mapping = _sample("V01")
        lineage_mapping["candidate_ref"] = "candidate-hostile-lineage.0001"
        lineage = CLASS_BY_V["V01"].from_mapping(_seal("V01", lineage_mapping))
        governed = halt = ("conflict", "snapshot_lineage_or_fence_mismatch")
    else:
        governed = {
            "baseline": ("permit", "source_effect_within_current_ceilings"),
            "proposal_conflict": ("conflict", "proposal_evidence_conflict"),
            "proposal_noncompliant": (
                "deny",
                "proposal_evidence_noncompliant",
            ),
            "attempt_expired": ("deny", "attempt_fence_expired"),
            "effect_expired": ("deny", "effect_fence_expired"),
            "grant_expired": ("deny", "authority_grant_expired"),
            "observation_expired": ("deny", "authority_observation_expired"),
            "effect_class": ("deny", "effect_class_not_allowed"),
            "exceeds_attempt": (
                "deny",
                "source_effect_exceeds_current_attempt",
            ),
            "exceeds_authority": (
                "deny",
                "source_effect_exceeds_current_authority",
            ),
            "authority_unknown": ("unknown", "current_authority_unknown"),
        }[scenario]
        if governed[0] == "conflict":
            halt = governed
    candidate = _decision_matrix_candidate(
        "V33",
        chain,
        governed,
        halt,
        source_effect_ceiling=ceiling,
        evaluated_at={
            "attempt_expired": ceiling.attempt_fence_expires_at,
            "effect_expired": ceiling.effect_fence_expires_at,
            "grant_expired": ceiling.authority_grant_expires_at,
            "observation_expired": ceiling.authority_observation_expires_at,
        }.get(scenario),
    )
    return production_decision.evaluate_rw0_c_decision_time_source_effect_ceiling_branches(
        candidate,
        snapshot=chain["snapshot"],
        lineage_context=lineage,
        source_effect_ceiling=ceiling,
    )


WITNESS_BUILDER_REGISTRY = {
    "standing.baseline": partial(_standing_policy_witness, "baseline"),
    "standing.revoked": partial(_standing_policy_witness, "policy_revoked"),
    "standing.branch": partial(_standing_policy_witness, "branch_not_allowed"),
    "standing.risk": partial(_standing_policy_witness, "risk_lane_not_allowed"),
    "standing.effect": partial(_standing_policy_witness, "effect_class_not_allowed"),
    "standing.status": partial(_standing_policy_witness, "policy_status_unknown"),
    "standing.currentness": partial(
        _standing_policy_witness, "policy_currentness_unknown"
    ),
    "risk.baseline": partial(_risk_lane_witness, "baseline"),
    "risk.revoked": partial(_risk_lane_witness, "policy_revoked"),
    "risk.required_lane": partial(_risk_lane_witness, "required_lane_mismatch"),
    "risk.status": partial(_risk_lane_witness, "policy_status_unknown"),
    "authority.baseline": partial(_authority_witness, "baseline"),
    "authority.phase": partial(_authority_witness, "phase_mismatch"),
    "authority.parent": partial(_authority_witness, "parent_mismatch"),
    "authority.support": partial(_authority_witness, "support_conflict"),
    "authority.denied": partial(_authority_witness, "authority_denied"),
    "authority.revoked": partial(_authority_witness, "authority_revoked"),
    "authority.attempt_expiry": partial(_authority_witness, "attempt_expired"),
    "authority.effect_expiry": partial(_authority_witness, "effect_expired"),
    "authority.grant_expiry": partial(_authority_witness, "grant_expired"),
    "authority.observation_expiry": partial(
        _authority_witness, "observation_expired"
    ),
    "authority.effect_class": partial(_authority_witness, "effect_class"),
    "authority.status_unknown": partial(_authority_witness, "authority_unknown"),
    "authority.family_unknown": partial(_authority_witness, "family_unknown"),
    "authority.revocation_unknown": partial(
        _authority_witness, "revocation_unknown"
    ),
    "stop.baseline": partial(_global_stop_witness, "baseline"),
    "stop.active": partial(_global_stop_witness, "active"),
    "ceiling.baseline": partial(_source_effect_ceiling_witness, "baseline"),
    "ceiling.lineage": partial(
        _source_effect_ceiling_witness, "lineage_mismatch"
    ),
    "ceiling.conflict": partial(
        _source_effect_ceiling_witness, "proposal_conflict"
    ),
    "ceiling.noncompliant": partial(
        _source_effect_ceiling_witness, "proposal_noncompliant"
    ),
    "ceiling.attempt_expiry": partial(
        _source_effect_ceiling_witness, "attempt_expired"
    ),
    "ceiling.effect_expiry": partial(
        _source_effect_ceiling_witness, "effect_expired"
    ),
    "ceiling.grant_expiry": partial(
        _source_effect_ceiling_witness, "grant_expired"
    ),
    "ceiling.observation_expiry": partial(
        _source_effect_ceiling_witness, "observation_expired"
    ),
    "ceiling.effect_class": partial(
        _source_effect_ceiling_witness, "effect_class"
    ),
    "ceiling.exceeds_attempt": partial(
        _source_effect_ceiling_witness, "exceeds_attempt"
    ),
    "ceiling.exceeds_authority": partial(
        _source_effect_ceiling_witness, "exceeds_authority"
    ),
    "ceiling.authority_unknown": partial(
        _source_effect_ceiling_witness, "authority_unknown"
    ),
}

WITNESS_PROVENANCE_BY_SCHEMA = {
    "governed-execution.nwp-post-execution-standing-policy-branch-matrix.v1": {
        "observed_owner": "standing_policy",
        "production_constructors": (
            "PostExecutionStandingPolicySourceAttestationV1",
            "PostExecutionStandingPolicyBranchMatrixV1",
        ),
        "production_evaluator": "_evaluate_parent_owned_branch_entries",
        "relation_action_boundary": (
            "validate_post_execution_standing_policy_attestation",
            "validate_post_execution_standing_policy_matrix_relation",
        ),
        "first_accepted_boundary": (
            "validate_post_execution_standing_policy_matrix_relation"
        ),
    },
    "governed-execution.nwp-post-execution-risk-lane-branch-matrix.v1": {
        "observed_owner": "risk_lane",
        "production_constructors": (
            "PostExecutionRiskPolicyAttestationV1",
            "PostExecutionRiskLaneBranchMatrixV1",
        ),
        "production_evaluator": "_evaluate_parent_owned_branch_entries",
        "relation_action_boundary": (
            "validate_post_execution_risk_policy_attestation",
            "finite_backlog_risk_source_projection",
            "validate_post_execution_risk_lane_matrix_relation",
        ),
        "first_accepted_boundary": (
            "validate_post_execution_risk_lane_matrix_relation"
        ),
    },
    "governed-execution.nwp-rw0-c-decision-time-authority-branch-matrix.v1": {
        "observed_owner": "decision_time_authority",
        "production_constructors": (
            "PostExecutionSourceEffectCeilingEvidenceV1",
            "RW0CDecisionCurrentSnapshotV1",
            "RW0CDecisionTimeAuthorityBranchMatrixV1",
        ),
        "production_evaluator": (
            "evaluate_rw0_c_decision_time_authority_branches"
        ),
        "relation_action_boundary": (
            "evaluate_post_execution_source_effect_ceiling",
            "rw0_c_decision_current_snapshot",
        ),
        "first_accepted_boundary": (
            "evaluate_rw0_c_decision_time_authority_branches"
        ),
    },
    "governed-execution.nwp-rw0-c-decision-time-global-stop-branch-matrix.v1": {
        "observed_owner": "global_stop",
        "production_constructors": (
            "PostExecutionGlobalStopSnapshotV1",
            "RW0CDecisionTimeGlobalStopBranchMatrixV1",
        ),
        "production_evaluator": (
            "evaluate_rw0_c_decision_time_global_stop_branches"
        ),
        "relation_action_boundary": (
            "post_execution_global_stop_snapshot",
            "rw0_c_decision_current_snapshot",
        ),
        "first_accepted_boundary": (
            "evaluate_rw0_c_decision_time_global_stop_branches"
        ),
    },
    "governed-execution.nwp-rw0-c-decision-time-source-effect-ceiling-branch-matrix.v1": {
        "observed_owner": "source_effect_ceiling",
        "production_constructors": (
            "PostExecutionSourceEffectCeilingEvidenceV1",
            "RW0CDecisionCurrentSnapshotV1",
            "RW0CDecisionTimeSourceEffectCeilingBranchMatrixV1",
        ),
        "production_evaluator": (
            "evaluate_rw0_c_decision_time_source_effect_ceiling_branches"
        ),
        "relation_action_boundary": (
            "evaluate_post_execution_source_effect_ceiling",
            "rw0_c_decision_current_snapshot",
        ),
        "first_accepted_boundary": (
            "evaluate_rw0_c_decision_time_source_effect_ceiling_branches"
        ),
    },
}


def _observed_production_entry_labels(
    entry: Mapping[str, object],
) -> tuple[str, str]:
    observed_result = entry["result"]
    observed_reason = entry["reason"]
    _require_exact(
        type(observed_result) is str,
        "production_witness:label_provenance:returned_result_type",
    )
    _require_exact(
        type(observed_reason) is str,
        "production_witness:label_provenance:returned_reason_type",
    )
    return observed_result, observed_reason


def _production_witness_ledger() -> tuple[dict[str, object], ...]:
    observed: list[dict[str, object]] = []
    accepted: set[tuple[str, str, str]] = set()
    for witness_id, builder in WITNESS_BUILDER_REGISTRY.items():
        value = builder()
        mapping = value.to_mapping()
        provenance = WITNESS_PROVENANCE_BY_SCHEMA[mapping["schema_id"]]
        owner = provenance["observed_owner"]
        for entry in mapping["entries"]:
            observed_result, observed_reason = _observed_production_entry_labels(
                entry
            )
            key = (owner, observed_result, observed_reason)
            if key in accepted:
                continue
            accepted.add(key)
            observed.append(
                {
                    "witness_id": witness_id,
                    "production_constructors": provenance[
                        "production_constructors"
                    ],
                    "production_evaluator": provenance["production_evaluator"],
                    "relation_action_boundary": provenance[
                        "relation_action_boundary"
                    ],
                    "observed_owner": owner,
                    "observed_result": observed_result,
                    "observed_reason": observed_reason,
                    "first_accepted_boundary": provenance[
                        "first_accepted_boundary"
                    ],
                }
            )
    return tuple(observed)


def _assert_observed_owner_pair_set_exact(
    owner: str,
    observed: set[tuple[str, str]],
) -> None:
    _require_exact(
        observed == set(FIXED_EXPECTED_ACCEPTED_PAIRS[owner]),
        f"production_witness:observed_pair_set:{owner}",
    )


SOURCE_REACHABILITY_SURFACES = {
    "standing_policy": (
        POLICY_SOURCE,
        ("_evaluate_parent_owned_branch_entries",),
    ),
    "risk_lane": (
        POLICY_SOURCE,
        ("_evaluate_parent_owned_branch_entries",),
    ),
    "decision_time_authority": (
        DECISION_INPUT_SOURCE,
        (
            "evaluate_rw0_c_decision_time_authority_branches",
            "_expected_matrix_pairs",
            "_matrix_pairs",
        ),
    ),
    "global_stop": (
        DECISION_INPUT_SOURCE,
        (
            "evaluate_rw0_c_decision_time_global_stop_branches",
            "_expected_matrix_pairs",
            "_matrix_pairs",
        ),
    ),
    "source_effect_ceiling": (
        DECISION_INPUT_SOURCE,
        (
            "evaluate_rw0_c_decision_time_source_effect_ceiling_branches",
            "_expected_matrix_pairs",
            "_matrix_pairs",
        ),
    ),
}


def _function_nodes(
    path: Path,
    function_names: tuple[str, ...],
) -> tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert set(function_names) <= set(definitions)
    return tuple(definitions[name] for name in function_names)


def _normalized_function_fingerprint(
    path: Path,
    function_name: str,
) -> str:
    node = _function_nodes(path, (function_name,))[0]
    normalized = ast.dump(node, annotate_fields=True, include_attributes=False)
    return hashlib.sha256(normalized.encode()).hexdigest()


def _resolved_constant_values(
    node: ast.AST,
    bindings: dict[str, ast.AST],
    resolving: frozenset[str] = frozenset(),
) -> set[object]:
    if isinstance(node, ast.Constant) and type(node.value) in {str, int, type(None)}:
        return {node.value}
    if isinstance(node, ast.Name):
        if node.id in resolving or node.id not in bindings:
            return set()
        return _resolved_constant_values(
            bindings[node.id], bindings, resolving | {node.id}
        )
    if isinstance(node, (ast.Tuple, ast.List)):
        products: set[tuple[object, ...]] = {()}
        for element in node.elts:
            values = _resolved_constant_values(element, bindings, resolving)
            if not values:
                return set()
            products = {
                (*prefix, value) for prefix in products for value in values
            }
        return set(products)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"tuple", "list"}
        and len(node.args) == 1
        and not node.keywords
    ):
        return _resolved_constant_values(node.args[0], bindings, resolving)
    if isinstance(node, ast.IfExp):
        return _resolved_constant_values(
            node.body, bindings, resolving
        ) | _resolved_constant_values(node.orelse, bindings, resolving)
    if isinstance(node, ast.Dict):
        return {
            value
            for expression in node.values
            for value in _resolved_constant_values(expression, bindings, resolving)
        }
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id in bindings
    ):
        mapping = bindings[node.value.id]
        if isinstance(mapping, ast.Dict):
            requested = _resolved_constant_values(node.slice, bindings, resolving)
            values: set[object] = set()
            for key, value in zip(mapping.keys, mapping.values, strict=True):
                if key is None:
                    continue
                if _resolved_constant_values(key, bindings, resolving) & requested:
                    values.update(
                        _resolved_constant_values(value, bindings, resolving)
                    )
            return values
    return set()


def _semantic_result_reason_pairs(
    path: Path,
    function_names: tuple[str, ...],
) -> set[tuple[str, str]]:
    functions = _function_nodes(path, function_names)
    bindings: dict[str, ast.AST] = {}
    for function in functions:
        for node in ast.walk(function):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        bindings[target.id] = value
    pairs: set[tuple[str, str]] = set()
    for function in functions:
        for node in ast.walk(function):
            for value in _resolved_constant_values(node, bindings):
                if (
                    type(value) is tuple
                    and len(value) == 2
                    and all(type(item) is str for item in value)
                    and value[0] in {"permit", "deny", "unknown", "conflict"}
                ):
                    pairs.add(value)
    return pairs


FIXED_REACHABILITY_AST_FINGERPRINTS = {
    "_post_execution_policy_values.py:_evaluate_parent_owned_branch_entries": (
        "7074b182b220656a69f1c323152a555134374d151a7e3f1c7d8141520027fcbb"
    ),
    "_rw0_c_decision_input_values.py:_expected_matrix_pairs": (
        "4a7f70d7450a585768218d6a6c5c42e7a175520d3a269c01eb38c327ae6de03d"
    ),
    "_rw0_c_decision_input_values.py:_matrix_pairs": (
        "85141fddc6bb0a1b07713e56ecd1a39cdae5960661d24cbba08dd4cdbac85cda"
    ),
    "_rw0_c_decision_input_values.py:evaluate_rw0_c_decision_time_authority_branches": (
        "e090d00ab527e0282e2775e70850c48d7cbed8a37a71b3bbe0c5e846fd287082"
    ),
    "_rw0_c_decision_input_values.py:evaluate_rw0_c_decision_time_global_stop_branches": (
        "5c4e4006f06fde20852cdfa65cb14195ecd83e112be0ac206fbf95956ab3d95d"
    ),
    "_rw0_c_decision_input_values.py:evaluate_rw0_c_decision_time_source_effect_ceiling_branches": (
        "3c9e32028e067110e9567d6656e17019698c62e2d988484fd2869e5fa42c5b39"
    ),
}
_FIXED_SHARED_POLICY_SOURCE_INVENTORY = frozenset(
    {
        ("deny", "branch_not_allowed"),
        ("deny", "effect_class_not_allowed"),
        ("deny", "policy_expired"),
        ("deny", "policy_not_yet_valid"),
        ("deny", "policy_revoked"),
        ("deny", "required_lane_mismatch"),
        ("deny", "risk_lane_not_allowed"),
        ("permit", "halt_only_policy_not_applicable"),
        ("permit", "halt_only_risk_not_applicable"),
        ("permit", "policy_permits"),
        ("permit", "risk_lane_permits"),
        ("unknown", "policy_currentness_unknown"),
        ("unknown", "policy_status_unknown"),
    }
)
FIXED_SOURCE_SEMANTIC_INVENTORY = {
    "standing_policy": _FIXED_SHARED_POLICY_SOURCE_INVENTORY,
    "risk_lane": _FIXED_SHARED_POLICY_SOURCE_INVENTORY,
    "decision_time_authority": frozenset(
        {
            ("conflict", "parent_or_fence_identity_mismatch"),
            ("conflict", "snapshot_or_phase_mismatch"),
            ("conflict", "support_conflict"),
            ("deny", "attempt_fence_expired"),
            ("deny", "authority_denied"),
            ("deny", "authority_grant_expired"),
            ("deny", "authority_observation_expired"),
            ("deny", "authority_revoked"),
            ("deny", "effect_class_not_allowed"),
            ("deny", "effect_fence_expired"),
            ("permit", "authority_verified_current"),
            ("permit", "halt_only_authority_not_applicable"),
            ("unknown", "authority_status_unknown"),
            ("unknown", "family_status_unknown"),
            ("unknown", "revocation_status_unknown"),
        }
    ),
    "global_stop": frozenset(
        {
            ("conflict", "snapshot_or_stop_identity_mismatch"),
            ("deny", "global_stop_active"),
            ("permit", "global_stop_clear"),
            ("permit", "halt_only_stop_checked"),
            ("unknown", "global_stop_unknown"),
        }
    ),
    "source_effect_ceiling": frozenset(
        {
            ("conflict", "proposal_evidence_conflict"),
            ("conflict", "snapshot_lineage_or_fence_mismatch"),
            ("conflict", "support_conflict"),
            ("deny", "attempt_fence_expired"),
            ("deny", "authority_grant_expired"),
            ("deny", "authority_observation_expired"),
            ("deny", "effect_class_not_allowed"),
            ("deny", "effect_fence_expired"),
            ("deny", "proposal_evidence_noncompliant"),
            ("deny", "source_effect_exceeds_current_attempt"),
            ("deny", "source_effect_exceeds_current_authority"),
            ("deny", "source_effect_exceeds_current_effect"),
            ("permit", "halt_only_ceiling_not_applicable"),
            ("permit", "source_effect_within_current_ceilings"),
            ("unknown", "current_authority_unknown"),
            ("unknown", "proposal_evidence_unknown"),
        }
    ),
}


def _capture_violation(call: object) -> str:
    with pytest.raises(production_evidence._PostExecutionContractViolation) as exc:
        call()
    return exc.value.reason


def _assert_source_reachability_surface(owner: str) -> None:
    path, function_names = SOURCE_REACHABILITY_SURFACES[owner]
    for function_name in function_names:
        key = f"{path.name}:{function_name}"
        _require_exact(
            _normalized_function_fingerprint(path, function_name)
            == FIXED_REACHABILITY_AST_FINGERPRINTS[key],
            f"source_reachability_ast_fingerprint:{key}",
        )
    _require_exact(
        frozenset(_semantic_result_reason_pairs(path, function_names))
        == FIXED_SOURCE_SEMANTIC_INVENTORY[owner],
        f"source_reachability_semantic_inventory:{owner}",
    )


def _prove_unreachable_boundary(
    owner: str,
    result: str,
    reason: str,
    classification: str,
    chain: dict[str, object],
) -> str:
    pair = (result, reason)
    if classification == "no_evaluator_branch":
        _assert_source_reachability_surface(owner)
        path, function_names = SOURCE_REACHABILITY_SURFACES[owner]
        assert pair not in _semantic_result_reason_pairs(path, function_names)
        return f"source_reachability:no_evaluator_branch:{owner}:{result}:{reason}"

    if classification == "accepted_relation_precludes":
        if owner == "source_effect_ceiling":
            ceiling, attempt, effect, authority, policy, support = (
                _ceiling_relation_case("baseline")
            )
            mapping = ceiling.to_mapping()
            source = deepcopy(mapping["source_effect_ceilings"])
            attempt_ceilings = deepcopy(mapping["attempt_ceilings"])
            authority_ceilings = deepcopy(mapping["authority_ceilings"])
            source["max_candidate_bytes"] += 1
            attempt_ceilings["max_candidate_bytes"] = source[
                "max_candidate_bytes"
            ]
            authority_ceilings["max_candidate_bytes"] = source[
                "max_candidate_bytes"
            ]
            mapping.update(
                source_effect_ceilings=source,
                attempt_ceilings=attempt_ceilings,
                authority_ceilings=authority_ceilings,
                result="noncompliant",
                reason="effect_exceeds_effect_fence",
            )
            candidate = CLASS_BY_V["V21"].from_mapping(_seal("V21", mapping))
            failure = _capture_violation(
                lambda: production_evidence.evaluate_post_execution_source_effect_ceiling(
                    candidate,
                    attempt_fence=attempt,
                    effect_fence=effect,
                    authority_observation=authority,
                    standing_policy_matrix=policy,
                    support_set=support,
                )
            )
            assert failure == "source_owner_mismatch"
            return (
                "evaluate_post_execution_source_effect_ceiling:"
                "source_owner_mismatch"
            )
        v_number = "V41" if owner == "standing_policy" else "V42"
        mapping = _sample(v_number)
        if reason == "policy_not_yet_valid":
            mapping["not_before"] = "2026-09-30T12:00:00Z"
        else:
            mapping["allowed_risk_lanes"] = ["risk.high"]
        relation = (
            production_policy.validate_post_execution_standing_policy_matrix_relation
            if owner == "standing_policy"
            else production_policy.validate_post_execution_risk_lane_matrix_relation
        )
        candidate_number = "V17" if owner == "standing_policy" else "V18"
        keyword = "policy_source" if owner == "standing_policy" else "risk_policy"
        relation_arguments: dict[str, object] = {keyword: _seal(v_number, mapping)}
        if owner == "risk_lane":
            profile, binding = (
                production_risk_adapter.finite_backlog_risk_source_projection(
                    _sample("V19"),
                    evaluated_at=_sample("V44")["evaluated_at"],
                    expires_at=_sample("V44")["expires_at"],
                )
            )
            relation_arguments.update(
                source_profile=profile,
                source_binding=binding,
            )
        failure = _capture_violation(
            lambda: relation(
                _sample(candidate_number),
                **relation_arguments,
            )
        )
        assert failure == "relation_mismatch"
        return f"{relation.__name__}:relation_mismatch"

    assert classification == "valid_construction_precludes"
    if owner in {"standing_policy", "risk_lane"}:
        v_number = "V17" if owner == "standing_policy" else "V18"
        mapping = _sample(v_number)
        mapping["evaluated_at"] = mapping["expires_at"]
        failure = _capture_violation(
            lambda: CLASS_BY_V[v_number].from_mapping(_seal(v_number, mapping))
        )
        assert failure == "relation_mismatch"
        return f"{v_number}.from_mapping:relation_mismatch"
    if owner == "global_stop" and reason == "snapshot_or_stop_identity_mismatch":
        mapping = _sample("V27")
        mapping["global_stop_ref"] = "global-stop-hostile-mismatch"
        failure = _capture_violation(
            lambda: production_decision.rw0_c_decision_current_snapshot(
                _seal("V27", mapping),
                lineage_context=chain["lineage"],
                input_context=chain["context"],
                membership_closure=chain["closure"],
                selected_authority_membership=chain["entries"][0],
                selected_section41_membership=chain["entries"][7],
                global_stop_snapshot=chain["stop"],
                source_effect_ceiling=chain["ceiling"],
                external_sources=chain["sources"],
            )
        )
        assert failure == "source_owner_mismatch"
        return "rw0_c_decision_current_snapshot:source_owner_mismatch"
    if owner == "global_stop":
        support = CLASS_BY_V["V13"].from_mapping(
            _ordered_fixture(
                "V13",
                deepcopy(_TEST_RECORDS["golden.V13.global-stop.support-set"]),
            )
        )
        mapping = _sample("V20")
        mapping["global_stop_state"] = "unknown"
        failure = _capture_violation(
            lambda: production_evidence.post_execution_global_stop_snapshot(
                _seal("V20", mapping),
                current_state=GlobalStopState(version=7),
                updated_at="2026-09-30T11:59:45Z",
                support_set=support,
            )
        )
        assert failure == "source_owner_mismatch"
        return "post_execution_global_stop_snapshot:source_owner_mismatch"
    mapping = _sample("V21")
    mapping.update(result=result, reason=reason)
    failure = _capture_violation(
        lambda: CLASS_BY_V["V21"].from_mapping(_seal("V21", mapping))
    )
    expected_failure = (
        "invalid_field_value"
        if reason == "proposal_evidence_unknown"
        else "evaluation_contract_mismatch"
    )
    assert failure == expected_failure
    return f"V21.from_mapping:{expected_failure}"


@pytest.fixture(scope="module")
def owner_text() -> str:
    return OWNER.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def contract(owner_text: str) -> dict[str, object]:
    return _validate_document_text(owner_text)


@pytest.fixture(scope="module")
def source_contract(contract: dict[str, object]) -> dict[str, object]:
    return _assert_source_binding(
        contract,
        EVIDENCE_SOURCE.read_text(encoding="utf-8"),
        POLICY_SOURCE.read_text(encoding="utf-8"),
        DECISION_INPUT_SOURCE.read_text(encoding="utf-8"),
    )


@pytest.fixture(scope="module")
def production_witness_ledger() -> tuple[dict[str, object], ...]:
    return _production_witness_ledger()


@pytest.fixture(scope="module")
def production_decision_chain() -> dict[str, object]:
    return _production_decision_chain()


def test_human_machine_expanded_and_fixed_contract_representations_are_identical(
    contract: dict[str, object],
) -> None:
    assert contract == EXPECTED_CONTRACT
    assert set(contract) == {
        "contract_id",
        "status",
        "outcome_classes",
        "rejection_classes",
        "admission_fault_to_rejection",
        "validation_projection",
        "validation_conflict_projection",
        "review_projection",
        "review_override_projection",
        "invalid_projection_rejection",
        "normalized_classes",
        "conclusive_severity_low_to_high",
        "normalized_candidate_branch",
        "candidate_reason_by_normalized_class",
        "currentness",
        "matrix",
        "accepted_emittable_pairs",
        "metadata_only_unreachable_pairs",
        "block_reason_precedence",
        "branch_mapping",
        "excluded_reducer_decision_kinds",
        "expected_branch",
        "model",
        "evaluation_trace",
        "guard",
        "recovery",
        "terminal",
        "physical",
        "excluded_effect_domains",
        "implementation",
        "temporary_source_nonimplementation_guard",
    }


def test_current_source_ast_is_the_exact_projection_and_branch_evidence(
    contract: dict[str, object],
    source_contract: dict[str, object],
) -> None:
    assert len(source_contract["validation_tuples"]) == 7
    assert len(source_contract["review_tuples"]) == 6
    assert contract["normalized_classes"] == list(CLASS_ORDER)
    assert tuple(source_contract["matrix_owner_metadata"]) == tuple(
        contract["matrix"]["owners"]
    )


def test_source_reachability_inventories_reconcile_exact_68_pair_metadata(
    contract: dict[str, object],
    source_contract: dict[str, object],
) -> None:
    accepted = {
        (owner, pair["result"], pair["reason"])
        for owner in contract["matrix"]["owners"]
        for pair in contract["accepted_emittable_pairs"][owner]
    }
    unreachable = {
        (owner, pair["result"], pair["reason"])
        for owner in contract["matrix"]["owners"]
        for pair in contract["metadata_only_unreachable_pairs"][owner]
    }
    declared = {
        (owner, result, reason)
        for owner, metadata in source_contract["matrix_owner_metadata"].items()
        for result, reason in metadata["allowed_pairs"]
    }
    assert {
        owner: tuple((pair["result"], pair["reason"]) for pair in pairs)
        for owner, pairs in contract["accepted_emittable_pairs"].items()
    } == FIXED_EXPECTED_ACCEPTED_PAIRS
    assert {
        owner: tuple(
            (pair["result"], pair["reason"], pair["classification"])
            for pair in pairs
        )
        for owner, pairs in contract["metadata_only_unreachable_pairs"].items()
    } == FIXED_EXPECTED_EXCLUDED_PAIRS
    assert len(accepted) == len(OWNER_PAIR_CASES) == 44
    assert len(unreachable) == len(UNREACHABLE_PAIR_CASES) == 24
    assert accepted.isdisjoint(unreachable)
    assert accepted | unreachable == declared
    assert len(declared) == 68
    assert {
        owner: sum(item[0] == owner for item in OWNER_PAIR_CASES)
        for owner in contract["matrix"]["owners"]
    } == {
        "standing_policy": 8,
        "risk_lane": 5,
        "decision_time_authority": 15,
        "global_stop": 3,
        "source_effect_ceiling": 13,
    }
    assert {
        owner: sum(item[0] == owner for item in UNREACHABLE_PAIR_CASES)
        for owner in contract["matrix"]["owners"]
    } == {
        "standing_policy": 9,
        "risk_lane": 7,
        "decision_time_authority": 1,
        "global_stop": 3,
        "source_effect_ceiling": 4,
    }


@pytest.mark.parametrize("owner", tuple(FIXED_EXPECTED_ACCEPTED_PAIRS))
def test_source_reachability_ast_fingerprint_inventory_and_runtime_witness_agree(
    production_witness_ledger: tuple[dict[str, object], ...],
    owner: str,
) -> None:
    _assert_source_reachability_surface(owner)
    observed = {
        (item["observed_result"], item["observed_reason"])
        for item in production_witness_ledger
        if item["observed_owner"] == owner
    }
    assert observed == set(FIXED_EXPECTED_ACCEPTED_PAIRS[owner])
    assert observed <= FIXED_SOURCE_SEMANTIC_INVENTORY[owner]


def test_hostile_source_reachability_dynamic_tuple_construction_is_resolved(
    tmp_path: Path,
) -> None:
    path = tmp_path / "dynamic_pair.py"
    path.write_text(
        "def evaluator():\n"
        "    emitted = tuple(['conflict', 'profile_mismatch'])\n"
        "    return emitted\n",
        encoding="utf-8",
    )
    observed = _semantic_result_reason_pairs(path, ("evaluator",))
    assert observed == {("conflict", "profile_mismatch")}
    assert ("conflict", "profile_mismatch") not in (
        FIXED_EXPECTED_ACCEPTED_PAIRS["decision_time_authority"]
    )


@pytest.mark.parametrize(
    ("owner", "pair_result", "pair_reason"),
    OWNER_PAIR_CASES,
    ids=lambda value: str(value),
)
def test_production_witness_observed_runtime_ledger_is_exact(
    production_witness_ledger: tuple[dict[str, object], ...],
    owner: str,
    pair_result: str,
    pair_reason: str,
) -> None:
    matching = [
        item
        for item in production_witness_ledger
        if (
            item["observed_owner"],
            item["observed_result"],
            item["observed_reason"],
        )
        == (owner, pair_result, pair_reason)
    ]
    assert len(matching) == 1
    assert {
        (
            item["observed_owner"],
            item["observed_result"],
            item["observed_reason"],
        )
        for item in production_witness_ledger
    } == set(OWNER_PAIR_CASES)
    assert len(production_witness_ledger) == len(OWNER_PAIR_CASES) == 44
    assert set(matching[0]) == {
        "witness_id",
        "production_constructors",
        "production_evaluator",
        "relation_action_boundary",
        "observed_owner",
        "observed_result",
        "observed_reason",
        "first_accepted_boundary",
    }


@pytest.mark.parametrize("owner", tuple(FIXED_EXPECTED_ACCEPTED_PAIRS))
def test_production_witness_observed_owner_pair_set_is_exact(
    production_witness_ledger: tuple[dict[str, object], ...],
    owner: str,
) -> None:
    observed = {
        (item["observed_result"], item["observed_reason"])
        for item in production_witness_ledger
        if item["observed_owner"] == owner
    }
    _assert_observed_owner_pair_set_exact(owner, observed)


def test_hostile_witness_label_provenance_runtime_extractor_uses_returned_entry(
) -> None:
    returned_entry = MappingProxyType(
        {
            "result": "sentinel_returned_result",
            "reason": "sentinel_returned_reason",
        }
    )
    observed = _observed_production_entry_labels(returned_entry)
    _require_exact(
        observed == ("sentinel_returned_result", "sentinel_returned_reason"),
        "production_witness:label_provenance:sentinel_extraction",
    )
    with pytest.raises(AssertionError) as exception:
        _assert_observed_owner_pair_set_exact("standing_policy", {observed})
    _require_exact(
        type(exception.value) is AssertionError,
        "production_witness:label_provenance:sentinel_rejection_class",
    )
    _require_exact(
        str(exception.value)
        == "production_witness:observed_pair_set:standing_policy",
        "production_witness:label_provenance:sentinel_rejection_boundary",
    )


def test_hostile_witness_label_provenance_structural_extractor_is_independent(
) -> None:
    extractor, ledger = _function_nodes(
        Path(__file__),
        (
            "_observed_production_entry_labels",
            "_production_witness_ledger",
        ),
    )
    forbidden_names = {
        "EXPECTED_CONTRACT",
        "FIXED_EXPECTED_ACCEPTED_PAIRS",
        "FIXED_SOURCE_SEMANTIC_INVENTORY",
        "MATRIX_PAIR_BEGIN",
        "MATRIX_PAIR_END",
        "OWNER_PAIR_CASES",
    }
    forbidden_strings = {
        "accepted_emittable_pairs",
        "RW0_C2_MATRIX_OWNER_RESULT_REASON_PAIRS_BEGIN",
        "RW0_C2_MATRIX_OWNER_RESULT_REASON_PAIRS_END",
    }
    forbidden_references = sorted(
        {
            node.id
            for function in (extractor, ledger)
            for node in ast.walk(function)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in forbidden_names
        }
        | {
            node.value
            for function in (extractor, ledger)
            for node in ast.walk(function)
            if isinstance(node, ast.Constant)
            and type(node.value) is str
            and node.value in forbidden_strings
        }
    )
    _require_exact(
        not forbidden_references,
        "production_witness:label_provenance:forbidden_reference:"
        + ",".join(forbidden_references),
    )

    direct_entry_fields = {
        node.slice.value
        for node in ast.walk(extractor)
        if isinstance(node, ast.Subscript)
        and isinstance(node.ctx, ast.Load)
        and isinstance(node.value, ast.Name)
        and node.value.id == "entry"
        and isinstance(node.slice, ast.Constant)
        and type(node.slice.value) is str
    }
    _require_exact(
        direct_entry_fields == {"result", "reason"},
        "production_witness:label_provenance:direct_returned_entry_fields",
    )
    exact_return = any(
        isinstance(node, ast.Return)
        and isinstance(node.value, ast.Tuple)
        and tuple(
            element.id if isinstance(element, ast.Name) else None
            for element in node.value.elts
        )
        == ("observed_result", "observed_reason")
        for node in ast.walk(extractor)
    )
    _require_exact(
        exact_return,
        "production_witness:label_provenance:extractor_return",
    )

    extraction_assignments = [
        node
        for node in ast.walk(ledger)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Tuple)
        and tuple(
            element.id if isinstance(element, ast.Name) else None
            for element in node.targets[0].elts
        )
        == ("observed_result", "observed_reason")
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "_observed_production_entry_labels"
        and len(node.value.args) == 1
        and isinstance(node.value.args[0], ast.Name)
        and node.value.args[0].id == "entry"
    ]
    _require_exact(
        len(extraction_assignments) == 1,
        "production_witness:label_provenance:shared_extractor_call",
    )
    stored_labels = {
        (key.value, value.id)
        for node in ast.walk(ledger)
        if isinstance(node, ast.Dict)
        for key, value in zip(node.keys, node.values, strict=True)
        if isinstance(key, ast.Constant)
        and type(key.value) is str
        and key.value in {"observed_result", "observed_reason"}
        and isinstance(value, ast.Name)
    }
    _require_exact(
        stored_labels
        == {
            ("observed_result", "observed_result"),
            ("observed_reason", "observed_reason"),
        },
        "production_witness:label_provenance:observed_labels_stored",
    )


def test_production_witness_registry_contains_only_ids_and_callable_builders() -> None:
    assert len(WITNESS_BUILDER_REGISTRY) == len(set(WITNESS_BUILDER_REGISTRY))
    assert all(type(witness_id) is str for witness_id in WITNESS_BUILDER_REGISTRY)
    assert all(callable(builder) for builder in WITNESS_BUILDER_REGISTRY.values())
    assert all(
        not any(
            type(argument) is tuple
            and len(argument) == 2
            and argument[0] in {"permit", "deny", "unknown", "conflict"}
            for argument in builder.args
        )
        for builder in WITNESS_BUILDER_REGISTRY.values()
    )


@pytest.mark.parametrize(
    ("witness_prefix", "module", "attribute"),
    (
        (
            "standing.",
            production_policy,
            "validate_post_execution_standing_policy_matrix_relation",
        ),
        (
            "risk.",
            production_policy,
            "validate_post_execution_risk_lane_matrix_relation",
        ),
        (
            "authority.",
            production_evidence,
            "evaluate_post_execution_source_effect_ceiling",
        ),
        (
            "stop.",
            production_evidence,
            "post_execution_global_stop_snapshot",
        ),
        (
            "ceiling.",
            production_evidence,
            "evaluate_post_execution_source_effect_ceiling",
        ),
    ),
    ids=("standing", "risk", "authority", "global_stop", "source_ceiling"),
)
def test_production_witness_relation_owned_builders_invoke_actual_action(
    monkeypatch: pytest.MonkeyPatch,
    witness_prefix: str,
    module: object,
    attribute: str,
) -> None:
    original = getattr(module, attribute)
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def observed(*args: object, **kwargs: object) -> object:
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(module, attribute, observed)
    builders = tuple(
        builder
        for witness_id, builder in WITNESS_BUILDER_REGISTRY.items()
        if witness_id.startswith(witness_prefix)
    )
    for builder in builders:
        builder()
    _require_exact(
        len(calls) == len(builders),
        f"production_witness:relation_action_count:{witness_prefix[:-1]}",
    )


def test_hostile_production_witness_v21_fence_class_bypass_is_not_credited(
    production_witness_ledger: tuple[dict[str, object], ...],
) -> None:
    ceiling, attempt, effect, authority, policy, support = _ceiling_relation_case(
        "baseline"
    )
    hostile_mapping = ceiling.to_mapping()
    hostile_mapping.update(
        effect_fence_class="review_candidate",
        result="conflict",
        reason="fence_identity_conflict",
    )
    hostile = CLASS_BY_V["V21"].from_mapping(_seal("V21", hostile_mapping))
    with pytest.raises(
        production_evidence._PostExecutionContractViolation
    ) as exception:
        production_evidence.evaluate_post_execution_source_effect_ceiling(
            hostile,
            attempt_fence=attempt,
            effect_fence=effect,
            authority_observation=authority,
            standing_policy_matrix=policy,
            support_set=support,
        )
    assert exception.value.reason == "source_owner_mismatch"
    assert str(exception.value) == "source_owner_mismatch"
    assert not any(
        item["observed_reason"] == "fence_identity_conflict"
        for item in production_witness_ledger
    )


@pytest.mark.parametrize(
    ("owner", "pair_result", "pair_reason", "classification"),
    UNREACHABLE_PAIR_CASES,
    ids=lambda value: str(value),
)
def test_source_reachability_metadata_only_pair_has_exact_proof_boundary(
    production_decision_chain: dict[str, object],
    owner: str,
    pair_result: str,
    pair_reason: str,
    classification: str,
) -> None:
    boundary = _prove_unreachable_boundary(
        owner,
        pair_result,
        pair_reason,
        classification,
        production_decision_chain,
    )
    assert type(boundary) is str and boundary


@pytest.mark.parametrize(
    ("owner", "pair_result", "pair_reason", "classification"),
    tuple(
        case
        for case in UNREACHABLE_PAIR_CASES
        if case[3] == "accepted_relation_precludes"
    ),
    ids=lambda value: str(value),
)
def test_source_reachability_accepted_relation_precludes_invokes_actual_relation(
    monkeypatch: pytest.MonkeyPatch,
    production_decision_chain: dict[str, object],
    owner: str,
    pair_result: str,
    pair_reason: str,
    classification: str,
) -> None:
    module, attribute = {
        "standing_policy": (
            production_policy,
            "validate_post_execution_standing_policy_matrix_relation",
        ),
        "risk_lane": (
            production_policy,
            "validate_post_execution_risk_lane_matrix_relation",
        ),
        "source_effect_ceiling": (
            production_evidence,
            "evaluate_post_execution_source_effect_ceiling",
        ),
    }[owner]
    original = getattr(module, attribute)
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def observed(*args: object, **kwargs: object) -> object:
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(module, attribute, observed)
    _prove_unreachable_boundary(
        owner,
        pair_result,
        pair_reason,
        classification,
        production_decision_chain,
    )
    expected_calls = 2 if owner == "source_effect_ceiling" else 1
    _require_exact(
        len(calls) == expected_calls,
        (
            "source_reachability:relation_action_count:"
            f"{owner}:{pair_result}:{pair_reason}"
        ),
    )


@pytest.mark.parametrize(
    ("owner", "pair_result", "pair_reason", "classification"),
    UNREACHABLE_PAIR_CASES,
    ids=lambda value: str(value),
)
def test_matrix_pair_forged_metadata_only_unreachable_input_is_matrix_conflict(
    contract: dict[str, object],
    owner: str,
    pair_result: str,
    pair_reason: str,
    classification: str,
) -> None:
    assert classification in {
        "no_evaluator_branch",
        "valid_construction_precludes",
        "accepted_relation_precludes",
    }
    state = _baseline(contract)
    _set_matrix_result(
        contract,
        state,
        owner,
        "candidate_acceptance",
        pair_result,
        pair_reason,
    )
    _assert_no_write(_interpret(contract, state), "matrix_conflict")


@pytest.mark.parametrize(
    ("owner", "pair_result", "pair_reason"),
    OWNER_PAIR_CASES,
    ids=lambda value: str(value),
)
def test_each_accepted_matrix_pair_is_source_declared_and_interpreter_consumed(
    contract: dict[str, object],
    source_contract: dict[str, object],
    owner: str,
    pair_result: str,
    pair_reason: str,
) -> None:
    source_pairs = source_contract["matrix_owner_metadata"][owner]["allowed_pairs"]
    assert (pair_result, pair_reason) in source_pairs
    assert {"result": pair_result, "reason": pair_reason} in contract[
        "accepted_emittable_pairs"
    ][owner]

    state = _baseline(contract)
    productive_reason = contract["matrix"]["permit_reasons"][owner]["productive"]
    halt_reason = contract["matrix"]["permit_reasons"][owner]["halt_only"]
    if pair_result == "permit" and pair_reason == halt_reason:
        state["validation"] = {
            "source_outcome": "failed",
            "result": "terminal_failure",
            "repairability": "nonrepairable",
            "reason": "validation_failed_terminal",
        }
        branch = "program_terminal_reject"
    else:
        branch = "candidate_acceptance"
    _set_matrix_result(
        contract,
        state,
        owner,
        branch,
        pair_result,
        pair_reason,
    )
    result = _interpret(contract, state)
    if pair_result == "conflict":
        _assert_no_write(result, "matrix_conflict")
    elif pair_result in {"deny", "unknown"}:
        assert result["branch"] == "post_execution_program_block"
        assert result["reason"] == "productive_branch_not_permitted"
    elif pair_reason == halt_reason:
        assert result["branch"] == "program_terminal_reject"
    else:
        assert pair_reason == productive_reason
        assert result["branch"] == "candidate_acceptance"


def test_every_current_v14_by_v15_case_has_one_fixed_first_semantic_outcome(
    contract: dict[str, object],
    source_contract: dict[str, object],
) -> None:
    observed = 0
    for validation in _expanded_validation_cases(contract):
        for review in _expanded_review_cases(contract):
            state = _baseline(contract)
            state["validation"] = {
                key: value for key, value in validation.items()
                if key != "normalized_class"
            }
            state["review"] = {
                key: value for key, value in review.items()
                if key != "normalized_class"
            }
            validation_class = validation["normalized_class"]
            review_class = review["normalized_class"]
            expected_class = EXPECTED_CLASS_MATRIX[validation_class][
                CLASS_ORDER.index(review_class)
            ]
            result = _interpret(contract, state)
            if expected_class == "conflict":
                _assert_no_write(
                    result,
                    "basis_identity_lineage_profile_provenance_conflict",
                )
            else:
                expected_branch = contract["normalized_candidate_branch"][expected_class]
                assert result["outcome"] == "durable_decision"
                assert result["branch"] == expected_branch
                assert result["reason"] == contract[
                    "candidate_reason_by_normalized_class"
                ][expected_class]
            observed += 1
    assert observed == 11 * 15 == 165


@pytest.mark.parametrize(
    ("currentness", "outcome", "branch", "reason"),
    (
        (
            "conflict",
            "no_write",
            None,
            "basis_identity_lineage_profile_provenance_conflict",
        ),
        (
            "stale",
            "durable_decision",
            "post_execution_program_block",
            "decision_basis_not_current",
        ),
        (
            "unknown",
            "durable_decision",
            "post_execution_program_block",
            "decision_basis_not_current",
        ),
        (
            "current",
            "durable_decision",
            "candidate_acceptance",
            "candidate_evidence_conclusively_accepted",
        ),
    ),
)
def test_currentness_is_exact_and_stale_caller_remains_a_separate_no_write(
    contract: dict[str, object],
    source_contract: dict[str, object],
    currentness: str,
    outcome: str,
    branch: str | None,
    reason: str,
) -> None:
    state = _baseline(contract)
    state["currentness"] = currentness
    result = _interpret(contract, state)
    assert result["outcome"] == outcome
    if branch is None:
        assert result["rejection"] == reason
    else:
        assert result["branch"] == branch
        assert result["reason"] == reason

    stale_caller = _baseline(contract)
    stale_caller["admission_fault"] = "stale_caller_expectation"
    _assert_no_write(
        _interpret(contract, stale_caller),
        "stale_caller_expectation",
    )


@pytest.mark.parametrize("owner", EXPECTED_CONTRACT["matrix"]["owners"])
@pytest.mark.parametrize(
    ("branch", "validation_result"),
    (
        ("candidate_acceptance", "passed"),
        ("candidate_repair", "repairable_failure"),
        ("attempt_selecting_replan", "replan_required"),
    ),
)
@pytest.mark.parametrize("matrix_result", ("permit", "deny", "unknown", "conflict"))
def test_each_productive_matrix_owner_and_result_is_causally_selected(
    contract: dict[str, object],
    source_contract: dict[str, object],
    owner: str,
    branch: str,
    validation_result: str,
    matrix_result: str,
) -> None:
    state = _baseline(contract)
    validation = next(
        row for row in contract["validation_projection"]
        if row["result"] == validation_result
    )
    state["validation"] = {
        key: value for key, value in validation.items()
        if key != "normalized_class"
    }
    if matrix_result != "permit":
        _set_matrix_result(contract, state, owner, branch, matrix_result)
    result = _interpret(contract, state)
    if matrix_result == "permit":
        assert result["branch"] == branch
    elif matrix_result in {"deny", "unknown"}:
        if any(
            pair["result"] == matrix_result
            for pair in contract["accepted_emittable_pairs"][owner]
        ):
            assert result["branch"] == "post_execution_program_block"
            assert result["reason"] == "productive_branch_not_permitted"
            assert _matrix_entry(
                result["retained_basis"],
                owner,
                branch,
            )["result"] == matrix_result
        else:
            _assert_no_write(result, "matrix_conflict")
    else:
        _assert_no_write(result, "matrix_conflict")


@pytest.mark.parametrize("owner", EXPECTED_CONTRACT["matrix"]["owners"])
@pytest.mark.parametrize(
    ("halt_result", "expected_rejection"),
    (
        ("deny", "halt_only_matrix_contract_conflict"),
        ("unknown", "halt_only_matrix_contract_conflict"),
        ("conflict", "matrix_conflict"),
    ),
)
def test_productive_to_block_always_executes_the_second_halt_only_stage(
    contract: dict[str, object],
    source_contract: dict[str, object],
    owner: str,
    halt_result: str,
    expected_rejection: str,
) -> None:
    state = _baseline(contract)
    _set_matrix_result(
        contract, state, "global_stop", "candidate_acceptance", "deny"
    )
    _set_matrix_result(
        contract, state, owner, "post_execution_program_block", halt_result
    )
    if not any(
        pair["result"] == halt_result
        for pair in contract["accepted_emittable_pairs"][owner]
    ):
        expected_rejection = "matrix_conflict"
    _assert_no_write(_interpret(contract, state), expected_rejection)


@pytest.mark.parametrize("owner", EXPECTED_CONTRACT["matrix"]["owners"])
def test_converted_block_rejects_malformed_reason_wrong_applicability_and_effect_class(
    contract: dict[str, object],
    source_contract: dict[str, object],
    owner: str,
) -> None:
    malformed = _baseline(contract)
    _set_matrix_result(
        contract, malformed, "global_stop", "candidate_acceptance", "deny"
    )
    _matrix_entry(
        malformed,
        owner,
        "post_execution_program_block",
    )["reason"] = "not-a-current-matrix-reason"
    _assert_no_write(
        _interpret(contract, malformed),
        "halt_only_matrix_contract_conflict",
    )

    wrong_applicability = _baseline(contract)
    _set_matrix_result(
        contract,
        wrong_applicability,
        "global_stop",
        "candidate_acceptance",
        "deny",
    )
    _matrix_entry(
        wrong_applicability,
        owner,
        "post_execution_program_block",
    )["applicability"] = "governed"
    _assert_no_write(
        _interpret(contract, wrong_applicability),
        "halt_only_matrix_contract_conflict",
    )

    wrong_effect = _baseline(contract)
    _set_matrix_result(
        contract, wrong_effect, "global_stop", "candidate_acceptance", "deny"
    )
    _matrix_entry(
        wrong_effect,
        owner,
        "post_execution_program_block",
    )["governed_effect_class"] = "author_candidate"
    _assert_no_write(
        _interpret(contract, wrong_effect),
        "halt_only_matrix_contract_conflict",
    )


NATIVE_BLOCK_PATHS = (
    "stale_currentness",
    "unknown_currentness",
    "validation_nonconclusive",
    "review_nonconclusive",
)
CONVERTED_BLOCK_PATHS = ("productive_deny", "productive_unknown")
HALT_ONLY_HOSTILES = (
    "same_owner_productive_permit",
    "exact_conflict_pair",
    "deny",
    "unknown",
    "foreign_owner_reason",
    "wrong_reason_for_result",
    "malformed_result",
    "wrong_applicability",
    "wrong_governed_effect_class",
)


def _halt_path_state(
    contract: dict[str, object],
    path: str,
) -> tuple[dict[str, object], str]:
    state = _baseline(contract)
    if path == "terminal":
        state["validation"] = {
            "source_outcome": "failed",
            "result": "terminal_failure",
            "repairability": "nonrepairable",
            "reason": "validation_failed_terminal",
        }
        return state, "program_terminal_reject"
    if path == "stale_currentness":
        state["currentness"] = "stale"
    elif path == "unknown_currentness":
        state["currentness"] = "unknown"
    elif path == "validation_nonconclusive":
        state["validation"] = {
            "source_outcome": "inconclusive",
            "result": "unknown",
            "repairability": "unknown",
            "reason": "validation_inconclusive",
        }
    elif path == "review_nonconclusive":
        state["review"] = {
            "separation_status": "separate",
            "source_outcome": "inconclusive",
            "result": "unknown",
            "reason": "review_inconclusive",
        }
    elif path in CONVERTED_BLOCK_PATHS:
        _set_matrix_result(
            contract,
            state,
            "standing_policy",
            "candidate_acceptance",
            "deny" if path == "productive_deny" else "unknown",
        )
    else:
        raise AssertionError(f"unknown halt path {path}")
    return state, "post_execution_program_block"


def _first_owner_pair(
    contract: dict[str, object],
    owner: str,
    result: str,
) -> dict[str, str]:
    accepted = contract["accepted_emittable_pairs"][owner]
    match = next((pair for pair in accepted if pair["result"] == result), None)
    if match is not None:
        return match
    unreachable = contract["metadata_only_unreachable_pairs"][owner]
    pair = next(pair for pair in unreachable if pair["result"] == result)
    return {"result": pair["result"], "reason": pair["reason"]}


def _foreign_owner_pair(
    contract: dict[str, object],
    owner: str,
) -> dict[str, str]:
    own_pairs = contract["accepted_emittable_pairs"][owner]
    return next(
        pair
        for other in contract["matrix"]["owners"]
        if other != owner
        for pair in contract["accepted_emittable_pairs"][other]
        if pair["result"] in {"deny", "unknown"} and pair not in own_pairs
    )


def _apply_halt_only_hostile(
    contract: dict[str, object],
    state: dict[str, object],
    owner: str,
    branch: str,
    hostile: str,
) -> str:
    entry = _matrix_entry(state, owner, branch)
    if hostile == "same_owner_productive_permit":
        entry.update(
            result="permit",
            reason=contract["matrix"]["permit_reasons"][owner]["productive"],
        )
    elif hostile == "exact_conflict_pair":
        pair = _first_owner_pair(contract, owner, "conflict")
        entry.update(pair)
        return "matrix_conflict"
    elif hostile in {"deny", "unknown"}:
        entry.update(_first_owner_pair(contract, owner, hostile))
        if not any(
            pair["result"] == hostile
            for pair in contract["accepted_emittable_pairs"][owner]
        ):
            return "matrix_conflict"
    elif hostile == "foreign_owner_reason":
        entry.update(_foreign_owner_pair(contract, owner))
    elif hostile == "wrong_reason_for_result":
        entry["result"] = "deny"
        entry["reason"] = _first_owner_pair(contract, owner, "unknown")["reason"]
    elif hostile == "malformed_result":
        entry["result"] = 7
    elif hostile == "wrong_applicability":
        entry["applicability"] = "governed"
    elif hostile == "wrong_governed_effect_class":
        entry["governed_effect_class"] = "author_candidate"
    else:
        raise AssertionError(f"unknown halt hostile {hostile}")
    return "halt_only_matrix_contract_conflict"


def _assert_halt_only_hostile(
    contract: dict[str, object],
    path: str,
    owner: str,
    hostile: str,
) -> None:
    state, branch = _halt_path_state(contract, path)
    rejection = _apply_halt_only_hostile(
        contract,
        state,
        owner,
        branch,
        hostile,
    )
    _assert_no_write(_interpret(contract, state), rejection)


@pytest.mark.parametrize("owner", EXPECTED_CONTRACT["matrix"]["owners"])
@pytest.mark.parametrize("hostile", HALT_ONLY_HOSTILES)
def test_terminal_halt_only_path_selection_requires_all_five_exact_permits(
    contract: dict[str, object],
    owner: str,
    hostile: str,
) -> None:
    _assert_halt_only_hostile(contract, "terminal", owner, hostile)


@pytest.mark.parametrize("path", NATIVE_BLOCK_PATHS)
@pytest.mark.parametrize("owner", EXPECTED_CONTRACT["matrix"]["owners"])
@pytest.mark.parametrize("hostile", HALT_ONLY_HOSTILES)
def test_native_block_halt_only_path_selection_requires_all_five_exact_permits(
    contract: dict[str, object],
    path: str,
    owner: str,
    hostile: str,
) -> None:
    _assert_halt_only_hostile(contract, path, owner, hostile)


@pytest.mark.parametrize("path", CONVERTED_BLOCK_PATHS)
@pytest.mark.parametrize("owner", EXPECTED_CONTRACT["matrix"]["owners"])
@pytest.mark.parametrize("hostile", HALT_ONLY_HOSTILES)
def test_converted_block_halt_only_path_selection_requires_all_five_exact_permits(
    contract: dict[str, object],
    path: str,
    owner: str,
    hostile: str,
) -> None:
    _assert_halt_only_hostile(contract, path, owner, hostile)


@pytest.mark.parametrize(
    ("path", "required_branch"),
    (
        ("terminal", "program_terminal_reject"),
        ("stale_currentness", "post_execution_program_block"),
        ("productive_deny", "post_execution_program_block"),
    ),
)
def test_hostile_terminal_native_and_converted_halt_bypasses_fail_causally(
    contract: dict[str, object],
    path: str,
    required_branch: str,
) -> None:
    hostile = deepcopy(contract)
    hostile["matrix"]["halt_only_required_branches"].remove(required_branch)
    with pytest.raises(
        AssertionError,
        match="^no_write:outcome:durable_decision$",
    ):
        _assert_halt_only_hostile(
            hostile,
            path,
            "risk_lane",
            "deny",
        )


@pytest.mark.parametrize("owner", EXPECTED_CONTRACT["matrix"]["owners"])
@pytest.mark.parametrize(
    ("mutation", "value"),
    (
        ("applicability", "halt_only"),
        ("governed_effect_class", None),
        ("halt_permit_reason", None),
        ("foreign_pair", None),
        ("malformed_result", None),
    ),
)
def test_productive_profile_and_pair_mismatches_are_matrix_conflict(
    contract: dict[str, object],
    owner: str,
    mutation: str,
    value: object,
) -> None:
    state = _baseline(contract)
    entry = _matrix_entry(state, owner, "candidate_acceptance")
    if mutation in {"applicability", "governed_effect_class"}:
        entry[mutation] = value
    elif mutation == "halt_permit_reason":
        entry["reason"] = contract["matrix"]["permit_reasons"][owner]["halt_only"]
    elif mutation == "foreign_pair":
        entry.update(_foreign_owner_pair(contract, owner))
    else:
        entry["result"] = 7
    _assert_no_write(_interpret(contract, state), "matrix_conflict")


@pytest.mark.parametrize(
    ("validation_result", "expected_branch"),
    (
        ("passed", "post_execution_program_block"),
        ("repairable_failure", "post_execution_program_block"),
        ("replan_required", "post_execution_program_block"),
        ("terminal_failure", "program_terminal_reject"),
    ),
)
def test_active_stop_preserves_terminal_and_two_stage_blocks_productive_branches(
    contract: dict[str, object],
    source_contract: dict[str, object],
    validation_result: str,
    expected_branch: str,
) -> None:
    state = _baseline(contract)
    validation = next(
        row for row in contract["validation_projection"]
        if row["result"] == validation_result
    )
    state["validation"] = {
        key: value for key, value in validation.items()
        if key != "normalized_class"
    }
    for branch in contract["matrix"]["productive_branches"]:
        _set_matrix_result(contract, state, "global_stop", branch, "deny")
    result = _interpret(contract, state)
    assert result["branch"] == expected_branch
    if expected_branch == "post_execution_program_block":
        assert result["reason"] == "productive_branch_not_permitted"


def test_matrix_owner_inventory_rejects_missing_additional_duplicate_and_reordered_state(
    contract: dict[str, object],
    source_contract: dict[str, object],
) -> None:
    mutations: list[list[dict[str, object]]] = []

    missing = deepcopy(_baseline(contract)["matrices"])
    missing.pop(1)
    mutations.append(missing)

    additional = deepcopy(_baseline(contract)["matrices"])
    additional.append(deepcopy(additional[0]))
    additional[-1]["owner"] = "additional_owner"
    mutations.append(additional)

    duplicate = deepcopy(_baseline(contract)["matrices"])
    duplicate[1]["owner"] = duplicate[0]["owner"]
    mutations.append(duplicate)

    reordered = deepcopy(_baseline(contract)["matrices"])
    reordered[0], reordered[1] = reordered[1], reordered[0]
    mutations.append(reordered)

    for matrices in mutations:
        state = _baseline(contract)
        state["matrices"] = matrices
        _assert_no_write(_interpret(contract, state), "required_fact_invalid")

    substituted = _baseline(contract)
    substituted["matrices"][1]["owner"] = "foreign_owner"
    _assert_no_write(_interpret(contract, substituted), "matrix_conflict")


def test_block_reason_precedence_is_fixed_and_lower_evidence_is_retained(
    contract: dict[str, object],
    source_contract: dict[str, object],
) -> None:
    policy_only = _baseline(contract)
    _set_matrix_result(
        contract,
        policy_only,
        "standing_policy",
        "candidate_acceptance",
        "deny",
    )
    result = _interpret(contract, policy_only)
    assert result["reason"] == "productive_branch_not_permitted"

    stale_policy = deepcopy(policy_only)
    stale_policy["currentness"] = "stale"
    result = _interpret(contract, stale_policy)
    assert result["reason"] == "decision_basis_not_current"
    assert _matrix_entry(
        result["retained_basis"],
        "standing_policy",
        "candidate_acceptance",
    )["result"] == "deny"

    nonconclusive = _baseline(contract)
    nonconclusive["review"] = {
        "separation_status": "separate",
        "source_outcome": "inconclusive",
        "result": "unknown",
        "reason": "review_inconclusive",
    }
    result = _interpret(contract, nonconclusive)
    assert result["reason"] == "candidate_evidence_nonconclusive"

    stale_nonconclusive = deepcopy(nonconclusive)
    stale_nonconclusive["currentness"] = "stale"
    result = _interpret(contract, stale_nonconclusive)
    assert result["reason"] == "decision_basis_not_current"
    assert result["candidate_reason"] == "candidate_evidence_nonconclusive"


def _v14_conflict_state(contract: dict[str, object]) -> dict[str, object]:
    state = _baseline(contract)
    conflict = contract["validation_conflict_projection"]
    state["validation"] = {
        "source_outcome": "passed",
        "result": conflict["result"],
        "repairability": conflict["repairability"],
        "reason": conflict["reason"],
    }
    return state


def test_pipeline_order_missing_matrix_owner_precedes_v14_conflict(
    contract: dict[str, object],
) -> None:
    state = _v14_conflict_state(contract)
    state["matrices"].pop()
    result = _interpret(contract, state)
    _assert_no_write(result, "required_fact_invalid")
    assert result["audit_trace"] == ("basis_validated",)


def test_pipeline_order_foreign_matrix_pair_precedes_v14_conflict(
    contract: dict[str, object],
) -> None:
    state = _v14_conflict_state(contract)
    _matrix_entry(state, "standing_policy", "candidate_acceptance").update(
        result="deny",
        reason="repository_mismatch",
    )
    result = _interpret(contract, state)
    _assert_no_write(result, "matrix_conflict")
    assert result["audit_trace"] == ("basis_validated",)


def test_pipeline_order_currentness_conflict_precedes_v14_conflict(
    contract: dict[str, object],
) -> None:
    state = _v14_conflict_state(contract)
    state["currentness"] = "conflict"
    result = _interpret(contract, state)
    _assert_no_write(
        result,
        "basis_identity_lineage_profile_provenance_conflict",
    )
    assert result["audit_trace"] == (
        "basis_validated",
        "matrix_grammar_validated",
        "currentness_reduced",
    )


def test_pipeline_order_v14_conflict_controls_after_every_earlier_stage(
    contract: dict[str, object],
) -> None:
    result = _interpret(contract, _v14_conflict_state(contract))
    _assert_no_write(
        result,
        "basis_identity_lineage_profile_provenance_conflict",
    )
    assert result["audit_trace"] == (
        "basis_validated",
        "matrix_grammar_validated",
        "currentness_reduced",
    )


def test_pipeline_order_v15_conflict_controls_after_every_earlier_stage(
    contract: dict[str, object],
) -> None:
    state = _baseline(contract)
    state["review"] = {
        "separation_status": "conflict",
        "source_outcome": "passed",
        "result": "basis_conflict",
        "reason": "reviewer_separation_conflict",
    }
    result = _interpret(contract, state)
    _assert_no_write(
        result,
        "basis_identity_lineage_profile_provenance_conflict",
    )
    assert result["audit_trace"] == (
        "basis_validated",
        "matrix_grammar_validated",
        "currentness_reduced",
    )


@pytest.mark.parametrize("owner", EXPECTED_CONTRACT["matrix"]["owners"])
@pytest.mark.parametrize("profile_kind", ("governed", "halt_only"))
def test_hostile_complete_matrix_stage_unselected_permit_reason_precedes_later_fault(
    contract: dict[str, object],
    owner: str,
    profile_kind: str,
) -> None:
    if profile_kind == "governed":
        state = _baseline(contract)
        state["currentness"] = "conflict"
        branch = "candidate_repair"
        wrong_reason = contract["matrix"]["permit_reasons"][owner]["halt_only"]
    else:
        state = _v14_conflict_state(contract)
        branch = "program_terminal_reject"
        wrong_reason = contract["matrix"]["permit_reasons"][owner]["productive"]
    entry = _matrix_entry(state, owner, branch)
    entry["result"] = "permit"
    entry["reason"] = wrong_reason

    result = _interpret(contract, state)
    boundary = f"complete_matrix_stage:{owner}:{profile_kind}"
    expected_rejection = (
        "matrix_conflict"
        if profile_kind == "governed"
        else "halt_only_matrix_contract_conflict"
    )
    _require_exact(
        result["outcome"] == "no_write",
        f"{boundary}:outcome",
    )
    _require_exact(
        result["rejection"] == expected_rejection,
        f"{boundary}:rejection",
    )
    _require_exact(
        result["audit_trace"] == ("basis_validated",),
        f"{boundary}:trace",
    )


@pytest.mark.parametrize("currentness", ("stale", "unknown"))
@pytest.mark.parametrize("owner", EXPECTED_CONTRACT["matrix"]["owners"])
def test_stale_unknown_plus_each_exact_matrix_conflict_is_no_write(
    contract: dict[str, object],
    currentness: str,
    owner: str,
) -> None:
    state = _baseline(contract)
    state["currentness"] = currentness
    conflict = _first_owner_pair(contract, owner, "conflict")
    _set_matrix_result(
        contract,
        state,
        owner,
        "candidate_acceptance",
        "conflict",
        conflict["reason"],
    )
    _assert_no_write(_interpret(contract, state), "matrix_conflict")


@pytest.mark.parametrize("nonconclusive_owner", ("validation", "review"))
@pytest.mark.parametrize("owner", EXPECTED_CONTRACT["matrix"]["owners"])
def test_nonconclusive_plus_exact_matrix_conflict_is_no_write(
    contract: dict[str, object],
    nonconclusive_owner: str,
    owner: str,
) -> None:
    state, branch = _halt_path_state(
        contract,
        f"{nonconclusive_owner}_nonconclusive",
    )
    conflict = _first_owner_pair(contract, owner, "conflict")
    _set_matrix_result(
        contract,
        state,
        owner,
        branch,
        "conflict",
        conflict["reason"],
    )
    _assert_no_write(_interpret(contract, state), "matrix_conflict")


EARLIER_BLOCK_PRODUCTIVE_CASES = tuple(
    (owner, result)
    for owner in EXPECTED_CONTRACT["matrix"]["owners"]
    for result in ("permit", "deny", "unknown")
    if result == "permit"
    or any(
        pair["result"] == result
        for pair in EXPECTED_CONTRACT["accepted_emittable_pairs"][owner]
    )
)


@pytest.mark.parametrize("currentness", ("stale", "unknown"))
@pytest.mark.parametrize(("owner", "matrix_result"), EARLIER_BLOCK_PRODUCTIVE_CASES)
def test_earlier_currentness_block_retains_productive_matrix_evidence_and_halt_gate(
    contract: dict[str, object],
    currentness: str,
    matrix_result: str,
    owner: str,
) -> None:
    state = _baseline(contract)
    state["currentness"] = currentness
    if matrix_result != "permit":
        _set_matrix_result(
            contract,
            state,
            owner,
            "candidate_acceptance",
            matrix_result,
        )
    result = _interpret(contract, state)
    assert result["branch"] == "post_execution_program_block"
    assert result["reason"] == "decision_basis_not_current"
    retained = _matrix_entry(result["retained_basis"], owner, "candidate_acceptance")
    assert retained["result"] == matrix_result
    assert result["audit_trace"] == (
        "basis_validated",
        "matrix_grammar_validated",
        "currentness_reduced",
        "validation_review_reduced",
        "productive_matrix_evaluated",
        "branch_selected",
        "halt_only_matrix_evaluated",
        "model_consistency_evaluated",
    )
    productive = result["productive_matrix_evidence"]
    assert productive["provisional_productive_branch"] == "candidate_acceptance"
    assert tuple(item["owner"] for item in productive["owner_entries"]) == tuple(
        contract["matrix"]["owners"]
    )
    assert len(productive["owner_entries"]) == 5
    observed = next(
        item for item in productive["owner_entries"] if item["owner"] == owner
    )
    assert observed["result"] == matrix_result

    blocked = deepcopy(state)
    _set_matrix_result(
        contract,
        blocked,
        "risk_lane",
        "post_execution_program_block",
        "deny",
    )
    _assert_no_write(
        _interpret(contract, blocked),
        "halt_only_matrix_contract_conflict",
    )


def test_hostile_earlier_block_reason_cannot_skip_productive_matrix_evaluation(
    contract: dict[str, object],
) -> None:
    state = _baseline(contract)
    state["currentness"] = "stale"
    conflict = _first_owner_pair(contract, "decision_time_authority", "conflict")
    _set_matrix_result(
        contract,
        state,
        "decision_time_authority",
        "candidate_acceptance",
        "conflict",
        conflict["reason"],
    )
    result = _interpret(contract, state)
    _assert_no_write(result, "matrix_conflict")
    assert result["audit_trace"] == (
        "basis_validated",
        "matrix_grammar_validated",
        "currentness_reduced",
        "validation_review_reduced",
        "productive_matrix_evaluated",
    )
    evidence = result["productive_matrix_evidence"]
    assert evidence["provisional_productive_branch"] == "candidate_acceptance"
    assert tuple(item["owner"] for item in evidence["owner_entries"]) == tuple(
        contract["matrix"]["owners"]
    )
    assert len(evidence["owner_entries"]) == 5


RETAINED_PRODUCTIVE_EVIDENCE_FIELDS = (
    "owner",
    "branch",
    "applicability",
    "governed_effect_class",
    "result",
    "reason",
)
RETAINED_PRODUCTIVE_EVIDENCE_CASES = (
    "stale_acceptance",
    "unknown_repair",
    "earlier_block_productive_deny",
    "earlier_block_productive_unknown",
    "earlier_block_productive_conflict",
    "current_all_permit_replan",
)


def _set_validation_projection_result(
    contract: dict[str, object],
    state: dict[str, object],
    validation_result: str,
) -> None:
    projection = next(
        row
        for row in contract["validation_projection"]
        if row["result"] == validation_result
    )
    state["validation"] = {
        key: value
        for key, value in projection.items()
        if key != "normalized_class"
    }


def _retained_productive_case_state(
    contract: dict[str, object],
    case: str,
) -> tuple[dict[str, object], str]:
    state = _baseline(contract)
    branch = "candidate_acceptance"
    if case == "stale_acceptance":
        state["currentness"] = "stale"
    elif case == "unknown_repair":
        state["currentness"] = "unknown"
        _set_validation_projection_result(contract, state, "repairable_failure")
        branch = "candidate_repair"
    elif case == "earlier_block_productive_deny":
        state["currentness"] = "stale"
        _set_matrix_result(
            contract,
            state,
            "standing_policy",
            branch,
            "deny",
            "policy_revoked",
        )
    elif case == "earlier_block_productive_unknown":
        state["currentness"] = "unknown"
        _set_validation_projection_result(contract, state, "repairable_failure")
        branch = "candidate_repair"
        _set_matrix_result(
            contract,
            state,
            "risk_lane",
            branch,
            "unknown",
            "policy_status_unknown",
        )
    elif case == "earlier_block_productive_conflict":
        state["currentness"] = "stale"
        _set_matrix_result(
            contract,
            state,
            "decision_time_authority",
            branch,
            "conflict",
            "support_conflict",
        )
    elif case == "current_all_permit_replan":
        _set_validation_projection_result(contract, state, "replan_required")
        branch = "attempt_selecting_replan"
    else:
        raise AssertionError(f"retained_productive_evidence:unknown_case:{case}")
    return state, branch


def _expected_retained_productive_sequence(
    contract: dict[str, object],
    state: dict[str, object],
    branch: str,
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "owner": owner,
            "branch": entry["branch"],
            "applicability": entry["applicability"],
            "governed_effect_class": entry["governed_effect_class"],
            "result": entry["result"],
            "reason": entry["reason"],
        }
        for owner in contract["matrix"]["owners"]
        for entry in (_matrix_entry(state, owner, branch),)
    )


def _assert_retained_productive_sequence_exact(
    result: dict[str, object],
    expected: tuple[dict[str, object], ...],
    case: str,
) -> None:
    evidence = result.get("productive_matrix_evidence")
    _require_exact(
        type(evidence) is dict,
        f"retained_productive_evidence:{case}:evidence_type",
    )
    observed = evidence.get("owner_entries")
    _require_exact(
        type(observed) is list,
        f"retained_productive_evidence:{case}:owner_entries_type",
    )
    _require_exact(
        len(observed) == len(expected) == 5,
        f"retained_productive_evidence:{case}:owner_entries_count",
    )
    for index, (observed_entry, expected_entry) in enumerate(
        zip(observed, expected, strict=True)
    ):
        owner = expected_entry["owner"]
        _require_exact(
            type(observed_entry) is dict,
            f"retained_productive_evidence:{case}:{index}:{owner}:entry_type",
        )
        _require_exact(
            tuple(observed_entry) == RETAINED_PRODUCTIVE_EVIDENCE_FIELDS,
            f"retained_productive_evidence:{case}:{index}:{owner}:fields",
        )
        for field in RETAINED_PRODUCTIVE_EVIDENCE_FIELDS:
            _require_exact(
                observed_entry[field] == expected_entry[field],
                (
                    f"retained_productive_evidence:{case}:{index}:"
                    f"{owner}:{field}"
                ),
            )


@pytest.mark.parametrize("case", RETAINED_PRODUCTIVE_EVIDENCE_CASES)
def test_hostile_retained_productive_evidence_complete_sequence_is_exact(
    contract: dict[str, object],
    case: str,
) -> None:
    state, productive_branch = _retained_productive_case_state(contract, case)
    expected = _expected_retained_productive_sequence(
        contract,
        state,
        productive_branch,
    )
    _require_exact(
        len({entry["reason"] for entry in expected}) == 5,
        f"retained_productive_evidence:{case}:owner_distinct_reasons",
    )
    result = _interpret(contract, state)
    if case == "earlier_block_productive_conflict":
        _assert_no_write(result, "matrix_conflict")
        expected_trace = (
            "basis_validated",
            "matrix_grammar_validated",
            "currentness_reduced",
            "validation_review_reduced",
            "productive_matrix_evaluated",
        )
    elif case == "current_all_permit_replan":
        _require_exact(
            result["outcome"] == "durable_decision"
            and result["branch"] == "attempt_selecting_replan",
            f"retained_productive_evidence:{case}:selected_branch",
        )
        expected_trace = (
            "basis_validated",
            "matrix_grammar_validated",
            "currentness_reduced",
            "validation_review_reduced",
            "productive_matrix_evaluated",
            "branch_selected",
            "model_consistency_evaluated",
        )
    else:
        _require_exact(
            result["outcome"] == "durable_decision"
            and result["branch"] == "post_execution_program_block"
            and result["reason"] == "decision_basis_not_current",
            f"retained_productive_evidence:{case}:earlier_block_selection",
        )
        expected_trace = (
            "basis_validated",
            "matrix_grammar_validated",
            "currentness_reduced",
            "validation_review_reduced",
            "productive_matrix_evaluated",
            "branch_selected",
            "halt_only_matrix_evaluated",
            "model_consistency_evaluated",
        )
    _require_exact(
        result["audit_trace"] == expected_trace,
        f"retained_productive_evidence:{case}:trace",
    )
    evidence = result["productive_matrix_evidence"]
    _require_exact(
        evidence["provisional_productive_branch"] == productive_branch,
        f"retained_productive_evidence:{case}:provisional_branch",
    )
    _assert_retained_productive_sequence_exact(result, expected, case)


def _state_for_authoritative_branch(
    contract: dict[str, object],
    branch: str,
) -> dict[str, object]:
    state = _baseline(contract)
    validation_result = {
        "candidate_acceptance": "passed",
        "candidate_repair": "repairable_failure",
        "attempt_selecting_replan": "replan_required",
        "program_terminal_reject": "terminal_failure",
    }.get(branch)
    if validation_result is None:
        state["currentness"] = "stale"
        return state
    selected = next(
        row
        for row in contract["validation_projection"]
        if row["result"] == validation_result
    )
    state["validation"] = {
        key: value for key, value in selected.items() if key != "normalized_class"
    }
    return state


MODEL_RECOMMENDATION_CASES = tuple(
    EXPECTED_CONTRACT["model"]["recommendation_to_branch"]
) + ("out_of_vocabulary_recommendation",)


@pytest.mark.parametrize("branch", tuple(EXPECTED_CONTRACT["branch_mapping"]))
@pytest.mark.parametrize("recommendation", MODEL_RECOMMENDATION_CASES)
def test_model_authority_exhaustive_recommendation_evidence_never_changes_branch(
    contract: dict[str, object],
    branch: str,
    recommendation: str,
) -> None:
    state = _state_for_authoritative_branch(contract, branch)
    state["model_recommendation"] = recommendation
    result = _interpret(contract, state)
    assert result["branch"] == branch
    mapped = contract["model"]["recommendation_to_branch"].get(recommendation)
    expected = (
        contract["model"]["unrecognized"]
        if mapped is None
        else contract["model"][
            "recognized_equal" if mapped == branch else "recognized_unequal"
        ]
    )
    assert result["model_consistency"] == expected["status"]
    assert result["model_consistency_reason"] == expected["reason"]
    assert result["audit_trace"][-1] == "model_consistency_evaluated"
    assert result["audit_trace"].count("model_consistency_evaluated") == 1


@pytest.mark.parametrize("recommendation", MODEL_RECOMMENDATION_CASES)
def test_model_authority_bootstrap_guard_no_write_precedes_all_recommendations(
    contract: dict[str, object],
    recommendation: str,
) -> None:
    state = _baseline(contract)
    state["guard_state"] = "missing"
    state["model_recommendation"] = recommendation
    result = _interpret(contract, state)
    _assert_no_write(result, "bootstrap_acceptance_guard_conflict")
    _require_exact(
        result["audit_trace"][-1] == "bootstrap_acceptance_guard_checked",
        f"model_authority:guard_precedes_model:{recommendation}",
    )
    _require_exact(
        "model_consistency_evaluated" not in result["audit_trace"],
        f"model_authority:model_not_evaluated:{recommendation}",
    )


def test_model_recommendation_changes_only_consistency_evidence(
    contract: dict[str, object],
    source_contract: dict[str, object],
) -> None:
    baseline = _baseline(contract)
    changed = deepcopy(baseline)
    changed["model_recommendation"] = "terminal_reject"
    baseline_result = _interpret(contract, baseline)
    changed_result = _interpret(contract, changed)
    assert baseline_result["branch"] == changed_result["branch"] == (
        "candidate_acceptance"
    )
    assert baseline_result["model_consistent"] is True
    assert changed_result["model_consistent"] is False
    assert baseline_result["model_consistency"] == "consistent"
    assert baseline_result["model_consistency_reason"] == (
        "mapped_branch_equals_authoritative_branch"
    )
    assert changed_result["model_consistency"] == "inconsistent"
    assert changed_result["model_consistency_reason"] == (
        "mapped_branch_differs_from_authoritative_branch"
    )
    assert contract["model"]["evaluation_order"] == "after_bootstrap_guard_gate"
    assert contract["model"]["may_change_branch"] is False
    assert contract["model"]["retention"] == "non_authoritative_evidence"


def test_hostile_model_recommendation_unrecognized_string_is_non_authoritative_evidence(
    contract: dict[str, object],
) -> None:
    state = _baseline(contract)
    state["model_recommendation"] = "out_of_vocabulary_recommendation"
    result = _interpret(contract, state)
    assert result["outcome"] == "durable_decision"
    assert result["branch"] == "candidate_acceptance"
    assert result["model_consistent"] is False
    assert result["model_consistency"] == "inconsistent"
    assert result["model_consistency_reason"] == (
        "model_recommendation_unrecognized"
    )

    malformed = _baseline(contract)
    malformed["model_recommendation"] = None
    _assert_no_write(_interpret(contract, malformed), "required_fact_invalid")


def test_model_recommendation_cannot_override_authoritative_no_write(
    contract: dict[str, object],
) -> None:
    state = _baseline(contract)
    state["admission_fault"] = "owner_conflict"
    state["model_recommendation"] = "out_of_vocabulary_recommendation"
    _assert_no_write(
        _interpret(contract, state),
        "basis_identity_lineage_profile_provenance_conflict",
    )


def test_expected_branch_is_only_a_conflict_assertion(
    contract: dict[str, object],
    source_contract: dict[str, object],
) -> None:
    matching = _baseline(contract)
    matching["expected_branch"] = "candidate_acceptance"
    mismatching = _baseline(contract)
    mismatching["expected_branch"] = "candidate_repair"
    assert _interpret(contract, matching)["branch"] == (
        "candidate_acceptance"
    )
    _assert_no_write(_interpret(contract, mismatching), "expected_branch_mismatch")
    assert contract["expected_branch"] == {
        "role": "conflict_assertion_only",
        "mismatch": "expected_branch_mismatch",
    }


@pytest.mark.parametrize(
    "fault",
    tuple(EXPECTED_CONTRACT["admission_fault_to_rejection"]),
)
def test_each_admission_fault_is_independently_fixed_and_no_write(
    contract: dict[str, object],
    source_contract: dict[str, object],
    fault: str,
) -> None:
    state = _baseline(contract)
    state["admission_fault"] = fault
    _assert_no_write(
        _interpret(contract, state),
        contract["admission_fault_to_rejection"][fault],
    )


@pytest.mark.parametrize(
    "guard_state",
    tuple(EXPECTED_CONTRACT["guard"]["accept_invalid_states"]),
)
def test_bootstrap_guard_dependency_is_abstract_exact_and_nonaccept_does_not_mutate(
    contract: dict[str, object],
    source_contract: dict[str, object],
    guard_state: str,
) -> None:
    acceptance = _baseline(contract)
    acceptance["guard_state"] = guard_state
    _assert_no_write(
        _interpret(contract, acceptance),
        "bootstrap_acceptance_guard_conflict",
    )

    repair = _baseline(contract)
    repair["validation"] = {
        "source_outcome": "failed",
        "result": "repairable_failure",
        "repairability": "repairable",
        "reason": "validation_failed_repairable",
    }
    repair["guard_state"] = guard_state
    result = _interpret(contract, repair)
    assert result["branch"] == "candidate_repair"
    assert result["acceptance_fact_effect"] == "none"


def test_no_write_block_and_recovery_unresolved_remain_disjoint(
    contract: dict[str, object],
    source_contract: dict[str, object],
) -> None:
    rejected = _baseline(contract)
    rejected["admission_fault"] = "missing_required_fact"
    blocked = _baseline(contract)
    blocked["currentness"] = "unknown"
    assert _interpret(contract, rejected)["outcome"] == "no_write"
    blocked_result = _interpret(contract, blocked)
    assert blocked_result["outcome"] == "durable_decision"
    assert blocked_result["branch"] == "post_execution_program_block"

    unresolved = _recover(contract, commit_attempted=True, readback="ambiguous")
    assert unresolved == {
        "outcome": "recovery_unresolved",
        "classification": "unresolved",
        "decision_created_by_recovery": False,
        "guard_mutated_by_recovery": False,
    }
    with pytest.raises(ValueError, match="commit-attempt uncertainty"):
        _recover(contract, commit_attempted=False, readback="ambiguous")


def test_terminal_physical_and_implementation_nonclaims_are_exact(
    contract: dict[str, object],
) -> None:
    assert contract["terminal"] == {
        "later_immutable_fact": True,
        "binds_committed_decision_result_receipt": True,
        "acceptance_binds_immutable_bootstrap_acceptance_fact": True,
        "mutates_guard": False,
        "is_development_decision": False,
        "is_effect_basis": False,
    }
    assert contract["physical"]["application_generation"] == 2
    assert contract["physical"]["migration_0005_exists"] is False
    assert contract["physical"]["migration_0005_selected"] is False
    assert all(value is False for value in contract["implementation"].values())


def test_document_routes_and_current_status_prose_are_reconciled() -> None:
    owner_ref = ".docs/rw0-c2-durable-progression-decision-semantic-contract.md"
    for relative in (
        ".docs/autonomous-software-development-operating-model.md",
        ".docs/architecture.md",
        ".docs/rw0-remote-worker-contact-phase-entry.md",
        ".docs/rw0-c1-durable-evidence.md",
        ".docs/c2b-durable-development-state.md",
    ):
        assert owner_ref in (ROOT / relative).read_text(encoding="utf-8"), relative

    c1 = (ROOT / ".docs/rw0-c1-durable-evidence.md").read_text(encoding="utf-8")
    assert "implemented together in this candidate" not in c1
    assert "already implemented in the merged baseline" in c1

    remote = (
        ROOT / ".docs/rw0-remote-worker-contact-phase-entry.md"
    ).read_text(encoding="utf-8")
    assert (
        "RW0-C — durable phase-entry and observation state** — future RW0-C2"
        in remote
    )
    assert "separate from current RW0-C1 private durable" in remote

    operating = (
        ROOT / ".docs/autonomous-software-development-operating-model.md"
    ).read_text(encoding="utf-8")
    assert "RW0-C1 private durable phase/evidence mechanics are also current" in (
        operating
    )
    assert "RW0-C2 durable progression-decision" in operating

    c2b = (
        ROOT / ".docs/c2b-durable-development-state.md"
    ).read_text(encoding="utf-8")
    assert c2b.count("RW0_C2_DURABLE_DECISION_SEMANTIC_STATUS_BEGIN") == 1
    assert "does not revise Sections 1 through 42" in c2b


def _leaf_paths(
    value: object,
    path: tuple[str | int, ...] = (),
) -> tuple[tuple[str | int, ...], ...]:
    if type(value) is dict:
        return tuple(
            child
            for key, item in value.items()
            for child in _leaf_paths(item, (*path, key))
        )
    if type(value) is list:
        return tuple(
            child
            for index, item in enumerate(value)
            for child in _leaf_paths(item, (*path, index))
        )
    return (path,)


def _hostile_leaf_value(value: object) -> object:
    if type(value) is bool:
        return not value
    if type(value) is int:
        return value + 1
    if type(value) is str:
        return value + "_hostile"
    if value is None:
        return "hostile_non_null"
    raise AssertionError(f"unsupported normative leaf type {type(value)!r}")


def _mutate_leaf(
    contract: dict[str, object],
    path: tuple[str | int, ...],
) -> dict[str, object]:
    hostile = deepcopy(contract)
    cursor: object = hostile
    for component in path[:-1]:
        cursor = cursor[component]
    leaf = path[-1]
    cursor[leaf] = _hostile_leaf_value(cursor[leaf])
    return hostile


NORMATIVE_LEAF_PATHS = _leaf_paths(EXPECTED_CONTRACT)
FIXED_NORMATIVE_SCALAR_LEAF_COUNT = 460


def _json_pointer(path: tuple[str | int, ...]) -> str:
    return "/" + "/".join(
        str(component).replace("~", "~0").replace("/", "~1")
        for component in path
    )


def _value_at_path(value: object, path: tuple[str | int, ...]) -> object:
    cursor = value
    for component in path:
        cursor = cursor[component]
    return cursor


SCALAR_POINTER_POSITIVE_COVERAGE = tuple(
    (_json_pointer(path), "fixed_expected_contract_positive_value")
    for path in NORMATIVE_LEAF_PATHS
)
SCALAR_POINTER_HOSTILE_COVERAGE = tuple(
    (_json_pointer(path), f"single_leaf_mutation:{_json_pointer(path)}")
    for path in NORMATIVE_LEAF_PATHS
)


def assert_exact_contract_drift(
    exception: BaseException,
    expected_pointer: str,
) -> None:
    expected = f"contract drift at {expected_pointer}"
    observed = str(exception)
    if observed != expected:
        raise AssertionError(
            "exact contract-drift boundary mismatch: "
            f"expected {expected!r}; observed {observed!r}"
        )


@pytest.mark.parametrize(
    "path",
    NORMATIVE_LEAF_PATHS,
    ids=lambda path: "/".join(str(component) for component in path),
)
def test_hostile_scalar_pointer_every_normative_leaf_is_independently_fixed(
    contract: dict[str, object],
    path: tuple[str | int, ...],
) -> None:
    pointer = _json_pointer(path)
    assert _value_at_path(contract, path) == _value_at_path(EXPECTED_CONTRACT, path)
    hostile = _mutate_leaf(EXPECTED_CONTRACT, path)
    with pytest.raises(AssertionError) as exception:
        _assert_fixed_contract(hostile)
    assert_exact_contract_drift(exception.value, pointer)


def test_scalar_pointer_coverage_map_is_exact_one_to_one_and_complete() -> None:
    pointers = tuple(_json_pointer(path) for path in NORMATIVE_LEAF_PATHS)
    assert len(pointers) == FIXED_NORMATIVE_SCALAR_LEAF_COUNT
    assert len(pointers) == len(set(pointers))
    assert len(SCALAR_POINTER_POSITIVE_COVERAGE) == len(pointers)
    assert len(SCALAR_POINTER_HOSTILE_COVERAGE) == len(pointers)
    assert tuple(row[0] for row in SCALAR_POINTER_POSITIVE_COVERAGE) == pointers
    assert tuple(row[0] for row in SCALAR_POINTER_HOSTILE_COVERAGE) == pointers
    assert all(
        row[1] == "fixed_expected_contract_positive_value"
        for row in SCALAR_POINTER_POSITIVE_COVERAGE
    )
    assert len({row[1] for row in SCALAR_POINTER_HOSTILE_COVERAGE}) == len(
        pointers
    )


@pytest.mark.parametrize(
    ("case", "expected_pointer", "observed_pointer"),
    (
        ("expected_prefix_of_observed", "/some/path", "/some/path/suffix"),
        ("observed_prefix_of_expected", "/some/path/suffix", "/some/path"),
        ("sibling_pointer", "/some/path", "/some/other"),
    ),
)
def test_hostile_scalar_pointer_checker_integrity_rejects_nonexact_pointer(
    case: str,
    expected_pointer: str,
    observed_pointer: str,
) -> None:
    wrong = AssertionError(f"contract drift at {observed_pointer}")
    try:
        assert_exact_contract_drift(wrong, expected_pointer)
    except AssertionError as exception:
        expected_message = (
            "exact contract-drift boundary mismatch: "
            f"expected 'contract drift at {expected_pointer}'; "
            f"observed 'contract drift at {observed_pointer}'"
        )
        _require_exact(
            type(exception) is AssertionError,
            f"pointer_checker_integrity:{case}:exception_class",
        )
        _require_exact(
            str(exception) == expected_message,
            f"pointer_checker_integrity:{case}:failure_boundary",
        )
    else:
        raise AssertionError(
            f"pointer_checker_integrity:{case}:nonexact_pointer_accepted"
        )


def test_hostile_prose_reason_drift_fails_human_machine_boundary(
    owner_text: str,
) -> None:
    hostile = _replace_in_region(
        owner_text,
        VALIDATION_BEGIN,
        VALIDATION_END,
        "validation_passed",
        "validation_passed_hostile",
    )
    with pytest.raises(
        AssertionError,
        match="^human_expanded_validation_projection_mismatch$",
    ):
        _validate_document_text(hostile)


def test_hostile_machine_projection_drift_fails_human_machine_boundary(
    owner_text: str,
) -> None:
    hostile = _replace_in_region(
        owner_text,
        ORACLE_BEGIN,
        ORACLE_END,
        '"reason": "validation_passed",\n      "normalized_class": "accept"',
        '"reason": "validation_passed",\n      "normalized_class": "repair"',
    )
    with pytest.raises(
        AssertionError,
        match="^c2:human_machine_equivalence:/validation_projection/0/normalized_class:value$",
    ):
        _validate_document_text(hostile)


def test_hostile_admission_fault_remap_fails_fixed_contract_boundary() -> None:
    hostile = deepcopy(EXPECTED_CONTRACT)
    hostile["admission_fault_to_rejection"]["missing_required_fact"] = (
        "matrix_conflict"
    )
    with pytest.raises(
        AssertionError,
        match=(
            "^contract drift at "
            "/admission_fault_to_rejection/missing_required_fact$"
        ),
    ):
        _assert_fixed_contract(hostile)


@pytest.mark.parametrize(
    ("mutation", "expected_path"),
    (
        ("remove", "matrix/owners"),
        ("add", "matrix/owners"),
        ("duplicate", "matrix/owners/1"),
        ("reorder", "matrix/owners/0"),
        ("substitute", "matrix/owners/1"),
    ),
)
def test_hostile_matrix_owner_contract_mutations_fail_fixed_inventory(
    mutation: str,
    expected_path: str,
) -> None:
    hostile = deepcopy(EXPECTED_CONTRACT)
    owners = hostile["matrix"]["owners"]
    if mutation == "remove":
        owners.remove("risk_lane")
    elif mutation == "add":
        owners.append("additional_owner")
    elif mutation == "duplicate":
        owners[1] = owners[0]
    elif mutation == "reorder":
        owners[0], owners[1] = owners[1], owners[0]
    else:
        owners[1] = "foreign_owner"
    with pytest.raises(
        AssertionError,
        match=f"^contract drift at /{expected_path}$",
    ):
        _assert_fixed_contract(hostile)


def test_hostile_current_source_validation_tuple_drift_fails_source_binding(
    contract: dict[str, object],
) -> None:
    evidence = EVIDENCE_SOURCE.read_text(encoding="utf-8")
    original = '("passed", "passed", "not_applicable", "validation_passed"),'
    replacement = (
        '("passed", "passed", "not_applicable", "validation_passed_hostile"),'
    )
    assert evidence.count(original) == 1
    hostile = evidence.replace(original, replacement, 1)
    with pytest.raises(
        AssertionError,
        match="^source_binding:validation_tuples$",
    ):
        _assert_source_binding(
            contract,
            hostile,
            POLICY_SOURCE.read_text(encoding="utf-8"),
            DECISION_INPUT_SOURCE.read_text(encoding="utf-8"),
        )


def test_hostile_review_separation_override_drift_fails_source_binding(
    contract: dict[str, object],
) -> None:
    evidence = EVIDENCE_SOURCE.read_text(encoding="utf-8")
    original = (
        '"not_separate": ("basis_conflict", '
        '"review_not_operationally_separate"),'
    )
    replacement = (
        '"not_separate": ("basis_conflict", '
        '"review_not_operationally_separate_hostile"),'
    )
    assert evidence.count(original) == 1
    hostile = evidence.replace(original, replacement, 1)
    with pytest.raises(
        AssertionError,
        match="^source_binding:review_overrides$",
    ):
        _assert_source_binding(
            contract,
            hostile,
            POLICY_SOURCE.read_text(encoding="utf-8"),
            DECISION_INPUT_SOURCE.read_text(encoding="utf-8"),
        )


@pytest.mark.parametrize(
    ("owner", "pair_result", "pair_reason"),
    OWNER_PAIR_CASES,
    ids=lambda value: str(value),
)
def test_hostile_removing_each_owner_pair_fails_source_binding_without_count_drift(
    contract: dict[str, object],
    owner: str,
    pair_result: str,
    pair_reason: str,
) -> None:
    hostile = deepcopy(contract)
    hostile["accepted_emittable_pairs"][owner].remove(
        {"result": pair_result, "reason": pair_reason}
    )
    with pytest.raises(
        AssertionError,
        match=f"^source_binding:owner_pair_cardinality:{owner}$",
    ):
        _assert_source_binding(
            hostile,
            EVIDENCE_SOURCE.read_text(encoding="utf-8"),
            POLICY_SOURCE.read_text(encoding="utf-8"),
            DECISION_INPUT_SOURCE.read_text(encoding="utf-8"),
        )


def test_hostile_adding_or_swapping_owner_pair_fails_exact_source_binding(
    contract: dict[str, object],
) -> None:
    added = deepcopy(contract)
    added["accepted_emittable_pairs"]["risk_lane"].append(
        {"result": "unknown", "reason": "policy_currentness_unknown"}
    )
    swapped = deepcopy(contract)
    risk_unknown = next(
        pair
        for pair in swapped["accepted_emittable_pairs"]["risk_lane"]
        if pair["result"] == "unknown"
    )
    risk_unknown["reason"] = "global_stop_unknown"
    for hostile, boundary in (
        (added, "source_binding:owner_pair_cardinality:risk_lane"),
        (swapped, "source_binding:owner_pair_partition:risk_lane"),
    ):
        with pytest.raises(AssertionError, match=f"^{boundary}$"):
            _assert_source_binding(
                hostile,
                EVIDENCE_SOURCE.read_text(encoding="utf-8"),
                POLICY_SOURCE.read_text(encoding="utf-8"),
                DECISION_INPUT_SOURCE.read_text(encoding="utf-8"),
            )


def test_hostile_matrix_pair_moved_between_owners_fails_owner_provenance(
    contract: dict[str, object],
) -> None:
    hostile = deepcopy(contract)
    moved = {"result": "deny", "reason": "required_lane_mismatch"}
    hostile["accepted_emittable_pairs"]["risk_lane"].remove(moved)
    hostile["accepted_emittable_pairs"]["standing_policy"].append(moved)
    with pytest.raises(
        AssertionError,
        match="^source_binding:owner_pair_cardinality:standing_policy$",
    ):
        _assert_source_binding(
            hostile,
            EVIDENCE_SOURCE.read_text(encoding="utf-8"),
            POLICY_SOURCE.read_text(encoding="utf-8"),
            DECISION_INPUT_SOURCE.read_text(encoding="utf-8"),
        )


@pytest.mark.parametrize(
    "foreign_reason",
    ("policy_currentness_unknown", "global_stop_unknown"),
)
def test_hostile_risk_lane_unknown_foreign_reason_is_matrix_conflict(
    contract: dict[str, object],
    foreign_reason: str,
) -> None:
    state = _baseline(contract)
    _set_matrix_result(
        contract,
        state,
        "risk_lane",
        "candidate_acceptance",
        "unknown",
        foreign_reason,
    )
    _assert_no_write(_interpret(contract, state), "matrix_conflict")


def test_hostile_owner_pair_human_table_drift_fails_representation_binding(
    owner_text: str,
) -> None:
    hostile = _replace_in_region(
        owner_text,
        MATRIX_PAIR_BEGIN,
        MATRIX_PAIR_END,
        "| `risk_lane` | `unknown` | `policy_status_unknown` |",
        "| `risk_lane` | `unknown` | `policy_currentness_unknown` |",
    )
    with pytest.raises(
        AssertionError,
        match="^human_accepted_pair_table_mismatch$",
    ):
        _validate_document_text(hostile)


def test_hostile_source_reachability_human_unreachable_ledger_drift_fails(
    owner_text: str,
) -> None:
    hostile = _replace_in_region(
        owner_text,
        MATRIX_UNREACHABLE_BEGIN,
        MATRIX_UNREACHABLE_END,
        "| `decision_time_authority` | `conflict` | `profile_mismatch` | `no_evaluator_branch` |",
        "| `decision_time_authority` | `conflict` | `profile_mismatch` | `valid_construction_precludes` |",
    )
    with pytest.raises(
        AssertionError,
        match="^human_excluded_pair_table_mismatch$",
    ):
        _validate_document_text(hostile)


def _assert_converted_block_halt_failure_is_no_write(
    contract: dict[str, object],
) -> None:
    state = _baseline(contract)
    _set_matrix_result(
        contract, state, "global_stop", "candidate_acceptance", "deny"
    )
    _set_matrix_result(
        contract, state, "risk_lane", "post_execution_program_block", "deny"
    )
    _assert_no_write(
        _interpret(contract, state),
        "halt_only_matrix_contract_conflict",
    )


def test_hostile_removing_converted_block_halt_verification_fails_causally(
    contract: dict[str, object],
    source_contract: dict[str, object],
) -> None:
    hostile = deepcopy(contract)
    hostile["matrix"]["halt_only_required_branches"].remove(
        "post_execution_program_block"
    )
    with pytest.raises(
        AssertionError,
        match="^no_write:outcome:durable_decision$",
    ):
        _assert_converted_block_halt_failure_is_no_write(hostile)


@pytest.mark.parametrize(
    ("halt_result", "expected_rejection"),
    (
        ("deny", "halt_only_matrix_contract_conflict"),
        ("unknown", "halt_only_matrix_contract_conflict"),
        ("conflict", "matrix_conflict"),
    ),
)
def test_hostile_each_converted_block_nonpermit_fails_at_second_stage(
    contract: dict[str, object],
    source_contract: dict[str, object],
    halt_result: str,
    expected_rejection: str,
) -> None:
    state = _baseline(contract)
    _set_matrix_result(
        contract, state, "global_stop", "candidate_acceptance", "deny"
    )
    _set_matrix_result(
        contract,
        state,
        "risk_lane",
        "post_execution_program_block",
        halt_result,
    )
    _assert_no_write(_interpret(contract, state), expected_rejection)


def test_hostile_model_recommendation_cannot_change_authoritative_branch(
    contract: dict[str, object],
    source_contract: dict[str, object],
) -> None:
    expected = _interpret(contract, _baseline(contract))["branch"]
    for recommendation in contract["model"]["recommendation_to_branch"]:
        state = _baseline(contract)
        state["model_recommendation"] = recommendation
        assert _interpret(contract, state)["branch"] == expected


def test_hostile_branch_mapping_change_fails_behavioral_boundary(
    contract: dict[str, object],
    source_contract: dict[str, object],
) -> None:
    hostile = deepcopy(contract)
    hostile["branch_mapping"]["candidate_acceptance"]["decision_kind"] = (
        "repair"
    )
    result = _interpret(hostile, _baseline(hostile))
    with pytest.raises(
        AssertionError,
        match="^branch_mapping:decision_kind:repair$",
    ):
        _require_exact(
            result["decision_kind"] == "accept",
            f"branch_mapping:decision_kind:{result['decision_kind']}",
        )


@pytest.mark.parametrize("decision_kind", ("cancel", "redeliver"))
def test_hostile_adding_excluded_reducer_branch_fails_fixed_boundary(
    decision_kind: str,
) -> None:
    hostile = deepcopy(EXPECTED_CONTRACT)
    hostile["branch_mapping"][f"candidate_{decision_kind}"] = {
        "decision_kind": decision_kind,
        "decision_variant": f"candidate_{decision_kind}",
        "version_advancing": True,
    }
    with pytest.raises(
        AssertionError,
        match="^contract drift at /branch_mapping$",
    ):
        _assert_fixed_contract(hostile)


@pytest.mark.parametrize(
    "claim",
    (
        "durable_decision_writer",
        "bootstrap_acceptance_guard",
        "terminal_outcome_owner",
        "production_caller",
        "public_export",
        "runtime_active",
        "rw0_d",
        "rw0_e",
        "execution_substrate_change",
    ),
)
def test_hostile_current_implementation_claim_fails_nonimplementation_boundary(
    claim: str,
) -> None:
    hostile = deepcopy(EXPECTED_CONTRACT)
    hostile["implementation"][claim] = True
    with pytest.raises(
        AssertionError,
        match=f"^contract drift at /implementation/{claim}$",
    ):
        _assert_fixed_contract(hostile)


@pytest.mark.parametrize(
    "claim",
    ("migration_0005_exists", "migration_0005_selected"),
)
def test_hostile_migration_0005_claim_fails_physical_boundary(claim: str) -> None:
    hostile = deepcopy(EXPECTED_CONTRACT)
    hostile["physical"][claim] = True
    with pytest.raises(
        AssertionError,
        match=f"^contract drift at /physical/{claim}$",
    ):
        _assert_fixed_contract(hostile)


def _class_methods(tree: ast.Module, class_name: str) -> tuple[str, ...]:
    matches = [
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    ]
    assert len(matches) == 1
    return tuple(
        node.name for node in matches[0].body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )


def _imported_module_names(
    tree: ast.Module,
    *,
    importing_module: str,
    importing_is_package: bool = False,
) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                package = (
                    importing_module
                    if importing_is_package
                    else importing_module.rpartition(".")[0]
                )
                package_parts = package.split(".") if package else []
                ascend = node.level - 1
                assert ascend <= len(package_parts)
                base_parts = package_parts[: len(package_parts) - ascend]
                if node.module:
                    base_parts.extend(node.module.split("."))
                base = ".".join(base_parts)
            else:
                base = node.module or ""
            if base:
                modules.add(base)
            for alias in node.names:
                if alias.name == "*":
                    continue
                modules.add(f"{base}.{alias.name}" if base else alias.name)
    return modules


def _called_symbol_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            names.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            names.add(node.func.attr)
    return names


FORBIDDEN_RW0_C2_MODULES = {
    "ge_nwp_coordinator._rw0_c2_durable_progression_decision",
    "ge_nwp_coordinator._rw0_c2_durable_progression_decision_contracts",
    "ge_nwp_coordinator._sqlite_rw0_c2_durable_progression_decision",
    "ge_nwp_coordinator._sqlite_rw0_c2_decision",
    "ge_nwp_coordinator.sqlite_rw0_c2_decision",
    "ge_nwp_coordinator.rw0_c2_durable_progression_decision",
}
FORBIDDEN_RW0_C2_CALLS = {
    "apply_rw0_c2_durable_progression_decision",
    "persist_rw0_c2_durable_progression_decision",
    "write_rw0_c2_durable_progression_decision",
    "consume_rw0_c2_acceptance_latch",
    "record_rw0_c2_terminal_outcome",
    "resolve_rw0_c2_commit_outcome",
}
FORBIDDEN_RW0_C2_EXPORTS = FORBIDDEN_RW0_C2_CALLS | {
    "DurableProgressionDecisionWriter",
    "RW0C2DurableProgressionDecision",
    "RW0C2AcceptanceLatch",
    "RW0C2TerminalOutcome",
}
PURE_OWNER_MODULE_BASENAMES = {
    "_finite_backlog_risk_source_adapter",
    "_post_execution_evidence_values",
    "_post_execution_policy_values",
    "_rw0_c_decision_input_values",
    "_section41_post_execution_proposal_family_projection",
    "_section41_post_execution_role_resolution",
}
PURE_OWNER_MODULES = {
    f"ge_nwp_coordinator.{name}" for name in PURE_OWNER_MODULE_BASENAMES
}
EXPECTED_PURE_OWNER_IMPORT_GRAPH = {
    "ge_nwp_coordinator._finite_backlog_risk_source_adapter": (
        "ge_nwp_coordinator._post_execution_evidence_values",
        "ge_nwp_coordinator._post_execution_policy_values",
    ),
    "ge_nwp_coordinator._post_execution_evidence_values": (),
    "ge_nwp_coordinator._post_execution_policy_values": (
        "ge_nwp_coordinator._post_execution_evidence_values",
    ),
    "ge_nwp_coordinator._rw0_c_decision_input_values": (
        "ge_nwp_coordinator._post_execution_evidence_values",
        "ge_nwp_coordinator._post_execution_policy_values",
        "ge_nwp_coordinator._section41_post_execution_proposal_family_projection",
        "ge_nwp_coordinator._section41_post_execution_role_resolution",
    ),
    "ge_nwp_coordinator._section41_post_execution_proposal_family_projection": (
        "ge_nwp_coordinator._post_execution_evidence_values",
    ),
    "ge_nwp_coordinator._section41_post_execution_role_resolution": (
        "ge_nwp_coordinator._post_execution_evidence_values",
        "ge_nwp_coordinator._section41_post_execution_proposal_family_projection",
    ),
}
PURE_OWNER_ACTION_CALLS = {
    "validate_post_execution_standing_policy_matrix_relation",
    "validate_post_execution_risk_lane_matrix_relation",
    "rw0_c_decision_current_snapshot",
    "evaluate_rw0_c_decision_time_authority_branches",
    "evaluate_rw0_c_decision_time_global_stop_branches",
    "evaluate_rw0_c_decision_time_source_effect_ceiling_branches",
}


def _owner_module_for_target(target: str) -> str | None:
    matches = [
        module
        for module in PURE_OWNER_MODULES
        if target == module or target.startswith(module + ".")
    ]
    return max(matches, key=len) if matches else None


def _semantic_owner_boundary_violations(
    index: dict[str, object],
) -> tuple[tuple[str, str, str], ...]:
    violations: list[tuple[str, str, str]] = []
    for caller, target in index["calls"]:
        owner_module = _owner_module_for_target(target)
        if owner_module is None or caller in PURE_OWNER_MODULES:
            continue
        symbol = target.rsplit(".", 1)[-1]
        if (
            owner_module
            == "ge_nwp_coordinator._rw0_c_decision_input_values"
            or symbol in PURE_OWNER_ACTION_CALLS
        ):
            violations.append(("resolved_owner_call", caller, target))
    for module, local, target in index["reexports"]:
        owner_module = _owner_module_for_target(target)
        if owner_module is not None and module not in PURE_OWNER_MODULES:
            violations.append(
                ("resolved_owner_reexport", module, f"{local}->{target}")
            )
    return tuple(sorted(violations))


def _source_module_identity(
    source_root: Path,
    path: Path,
) -> tuple[str, bool]:
    relative = path.relative_to(source_root)
    parts = [source_root.name, *relative.with_suffix("").parts]
    is_package = parts[-1] == "__init__"
    if is_package:
        parts.pop()
    return ".".join(parts), is_package


def _import_from_base(
    node: ast.ImportFrom,
    *,
    importing_module: str,
    importing_is_package: bool,
) -> str:
    if not node.level:
        return node.module or ""
    package = (
        importing_module
        if importing_is_package
        else importing_module.rpartition(".")[0]
    )
    parts = package.split(".") if package else []
    ascend = node.level - 1
    assert ascend <= len(parts)
    base = parts[: len(parts) - ascend]
    if node.module:
        base.extend(node.module.split("."))
    return ".".join(base)


def _resolved_expression_name(
    node: ast.AST,
    bindings: dict[str, str],
) -> str | None:
    if isinstance(node, ast.Name):
        return bindings.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        base = _resolved_expression_name(node.value, bindings)
        return None if base is None else f"{base}.{node.attr}"
    return None


def _semantic_module_bindings(
    tree: ast.Module,
    *,
    importing_module: str,
    importing_is_package: bool,
) -> tuple[dict[str, str], set[str]]:
    bindings: dict[str, str] = {}
    imported_targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_targets.add(alias.name)
                local = alias.asname or alias.name.split(".", 1)[0]
                bindings[local] = alias.name if alias.asname else local
        elif isinstance(node, ast.ImportFrom):
            base = _import_from_base(
                node,
                importing_module=importing_module,
                importing_is_package=importing_is_package,
            )
            for alias in node.names:
                if alias.name == "*":
                    continue
                target = f"{base}.{alias.name}" if base else alias.name
                imported_targets.add(target)
                bindings[alias.asname or alias.name] = target
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        resolved = _resolved_expression_name(value, bindings)
        if resolved is None:
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                bindings[target.id] = resolved
    return bindings, imported_targets


def _dereference_reexport(
    target: str,
    module_bindings: dict[str, dict[str, str]],
) -> str:
    observed: set[str] = set()
    current = target
    while current not in observed:
        observed.add(current)
        parts = current.split(".")
        replacement: str | None = None
        for size in range(len(parts) - 1, 0, -1):
            module = ".".join(parts[:size])
            remainder = parts[size:]
            bindings = module_bindings.get(module)
            if bindings is None or not remainder:
                continue
            bound = bindings.get(remainder[0])
            if bound is None:
                continue
            replacement = ".".join((bound, *remainder[1:]))
            break
        if replacement is None or replacement == current:
            return current
        current = replacement
    return current


def _semantic_source_index(source_root: Path) -> dict[str, object]:
    modules: dict[str, tuple[Path, ast.Module, bool]] = {}
    for path in sorted(source_root.rglob("*.py")):
        module, is_package = _source_module_identity(source_root, path)
        modules[module] = (
            path,
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path)),
            is_package,
        )
    module_bindings: dict[str, dict[str, str]] = {}
    raw_imports: dict[str, set[str]] = {}
    for module, (_path, tree, is_package) in modules.items():
        bindings, imports = _semantic_module_bindings(
            tree,
            importing_module=module,
            importing_is_package=is_package,
        )
        module_bindings[module] = bindings
        raw_imports[module] = imports

    resolved_imports: set[tuple[str, str]] = set()
    resolved_calls: set[tuple[str, str]] = set()
    resolved_reexports: set[tuple[str, str, str]] = set()
    for module, (_path, tree, is_package) in modules.items():
        bindings = module_bindings[module]
        for target in raw_imports[module]:
            resolved_imports.add(
                (module, _dereference_reexport(target, module_bindings))
            )
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = _resolved_expression_name(node.func, bindings)
            if target is not None:
                resolved_calls.add(
                    (module, _dereference_reexport(target, module_bindings))
                )
        if is_package:
            for local, target in bindings.items():
                resolved = _dereference_reexport(target, module_bindings)
                if resolved != f"{module}.{local}" and resolved != local:
                    resolved_reexports.add((module, local, resolved))
    return {
        "modules": frozenset(modules),
        "bindings": module_bindings,
        "imports": frozenset(resolved_imports),
        "calls": frozenset(resolved_calls),
        "reexports": frozenset(resolved_reexports),
    }


def _is_forbidden_rw0_c2_module(module: str) -> bool:
    forbidden_basenames = {name.rsplit(".", 1)[-1] for name in FORBIDDEN_RW0_C2_MODULES}
    return module in FORBIDDEN_RW0_C2_MODULES or module.rsplit(".", 1)[-1] in (
        forbidden_basenames
    )


def _scan_production_source_tree(source_root: Path) -> dict[str, object]:
    source_paths = tuple(sorted(source_root.rglob("*.py")))
    assert source_paths
    semantic_index = _semantic_source_index(source_root)
    prohibited_inventory: list[str] = []
    all_imports: set[str] = set()
    all_calls: set[str] = set()
    all_definitions: set[str] = set()
    for path in source_paths:
        module, is_package = _source_module_identity(source_root, path)
        if (
            _is_forbidden_rw0_c2_module(module)
            or "durable_progression_decision" in module
            or "acceptance_latch" in module
        ):
            prohibited_inventory.append(path.relative_to(source_root).as_posix())
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        all_imports.update(
            _imported_module_names(
                tree,
                importing_module=module,
                importing_is_package=is_package,
            )
        )
        all_calls.update(_called_symbol_names(tree))
        all_definitions.update(
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        )
    return {
        "paths": source_paths,
        "prohibited_inventory": tuple(prohibited_inventory),
        "imports": all_imports,
        "calls": all_calls,
        "definitions": all_definitions,
        "resolved_imports": semantic_index["imports"],
        "resolved_calls": semantic_index["calls"],
        "resolved_reexports": semantic_index["reexports"],
        "owner_boundary_violations": _semantic_owner_boundary_violations(
            semantic_index
        ),
    }


def _complete_source_manifest(source_root: Path) -> dict[str, object]:
    records: list[dict[str, object]] = []
    paths = sorted(
        source_root.rglob("*"),
        key=lambda path: path.relative_to(source_root).as_posix().encode(),
    )
    for path in paths:
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        relative = path.relative_to(source_root).as_posix()
        metadata = path.lstat()
        if stat.S_ISDIR(metadata.st_mode):
            continue
        kind = (
            "regular"
            if stat.S_ISREG(metadata.st_mode)
            else "symlink"
            if stat.S_ISLNK(metadata.st_mode)
            else "unsupported"
        )
        records.append(
            {
                "path": relative,
                "type": kind,
                "mode": f"{stat.S_IMODE(metadata.st_mode):04o}",
                "bytes": metadata.st_size,
                "sha256": (
                    hashlib.sha256(path.read_bytes()).hexdigest()
                    if kind == "regular"
                    else None
                ),
            }
        )
    payload = (
        json.dumps(records, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    return {
        "records": tuple(records),
        "count": len(records),
        "payload_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _assert_fixed_source_nonimplementation_manifest(source_root: Path) -> None:
    manifest = _complete_source_manifest(source_root)
    expected = EXPECTED_CONTRACT["temporary_source_nonimplementation_guard"]
    _require_exact(
        all(record["type"] == "regular" for record in manifest["records"]),
        "source_manifest:regular_files_only",
    )
    _require_exact(
        manifest["count"] == expected["manifest_count"],
        "source_manifest:count",
    )
    _require_exact(
        manifest["payload_bytes"] == expected["manifest_payload_bytes"],
        "source_manifest:payload_bytes",
    )
    _require_exact(
        manifest["sha256"] == expected["manifest_sha256"],
        "source_manifest:sha256",
    )


def test_ast_import_guard_uses_importfrom_module_and_import_alias_targets() -> None:
    tree = ast.parse(
        "import ge_nwp_coordinator._sqlite_rw0_c2_decision as harmless_alias\n"
        "from ge_nwp_coordinator import _sqlite_rw0_c2_decision as package_alias\n"
        "from . import _sqlite_rw0_c2_decision as relative_alias\n"
        "from ge_nwp_coordinator._rw0_c2_durable_progression_decision "
        "import persist as another_alias\n"
    )
    modules = _imported_module_names(
        tree,
        importing_module="ge_nwp_coordinator.probe",
    )
    assert modules == {
        "ge_nwp_coordinator",
        "ge_nwp_coordinator._sqlite_rw0_c2_decision",
        "ge_nwp_coordinator._rw0_c2_durable_progression_decision",
        "ge_nwp_coordinator._rw0_c2_durable_progression_decision.persist",
    }
    assert "harmless_alias" not in modules
    assert "package_alias" not in modules
    assert "relative_alias" not in modules
    assert "another_alias" not in modules


def _synthetic_semantic_tree(
    tmp_path: Path,
    probe_source: str,
    *,
    package_source: str = "__all__ = ()\n",
    nested: bool = False,
) -> tuple[Path, str]:
    source_root = tmp_path / "src" / "ge_nwp_coordinator"
    source_root.mkdir(parents=True)
    (source_root / "__init__.py").write_text(package_source, encoding="utf-8")
    (source_root / "_rw0_c_decision_input_values.py").write_text(
        "def some_future_decision_call():\n    return None\n",
        encoding="utf-8",
    )
    if nested:
        target = source_root / "internal" / "probe.py"
        target.parent.mkdir()
        (target.parent / "__init__.py").write_text("__all__ = ()\n", encoding="utf-8")
        module = "ge_nwp_coordinator.internal.probe"
    else:
        target = source_root / "probe.py"
        module = "ge_nwp_coordinator.probe"
    target.write_text(probe_source, encoding="utf-8")
    return source_root, module


def test_hostile_structural_nonimplementation_resolves_absolute_module_alias_call(
    tmp_path: Path,
) -> None:
    source_root, module = _synthetic_semantic_tree(
        tmp_path,
        "from ge_nwp_coordinator import _rw0_c_decision_input_values as d\n"
        "d.some_future_decision_call()\n",
    )
    index = _semantic_source_index(source_root)
    target = (
        "ge_nwp_coordinator._rw0_c_decision_input_values."
        "some_future_decision_call"
    )
    assert (module, target) in index["calls"]
    assert (
        "resolved_owner_call",
        module,
        target,
    ) in _semantic_owner_boundary_violations(index)


def test_hostile_structural_nonimplementation_resolves_relative_nested_alias_call(
    tmp_path: Path,
) -> None:
    source_root, module = _synthetic_semantic_tree(
        tmp_path,
        "from .. import _rw0_c_decision_input_values as d\n"
        "d.some_future_decision_call()\n",
        nested=True,
    )
    index = _semantic_source_index(source_root)
    target = (
        "ge_nwp_coordinator._rw0_c_decision_input_values."
        "some_future_decision_call"
    )
    assert (module, target) in index["calls"]
    assert (
        "resolved_owner_call",
        module,
        target,
    ) in _semantic_owner_boundary_violations(index)


def test_hostile_structural_nonimplementation_resolves_package_reexport_symbol_alias(
    tmp_path: Path,
) -> None:
    source_root, module = _synthetic_semantic_tree(
        tmp_path,
        "from ge_nwp_coordinator import exposed_decision as alias\n"
        "alias()\n",
        package_source=(
            "from ._rw0_c_decision_input_values import "
            "some_future_decision_call as exposed_decision\n"
            "__all__ = ('exposed_decision',)\n"
        ),
    )
    index = _semantic_source_index(source_root)
    target = (
        "ge_nwp_coordinator._rw0_c_decision_input_values."
        "some_future_decision_call"
    )
    assert (module, target) in index["calls"]
    violations = _semantic_owner_boundary_violations(index)
    assert ("resolved_owner_call", module, target) in violations
    assert (
        "resolved_owner_reexport",
        "ge_nwp_coordinator",
        f"exposed_decision->{target}",
    ) in violations


def test_structural_nonimplementation_manifest_and_semantic_absence_are_exact() -> None:
    source_root = ROOT / "src" / "ge_nwp_coordinator"
    _assert_fixed_source_nonimplementation_manifest(source_root)
    scan = _scan_production_source_tree(source_root)
    assert scan["prohibited_inventory"] == ()
    assert not any(
        _is_forbidden_rw0_c2_module(module) for module in scan["imports"]
    )
    assert scan["calls"].isdisjoint(FORBIDDEN_RW0_C2_CALLS)
    assert scan["definitions"].isdisjoint(FORBIDDEN_RW0_C2_EXPORTS)
    assert scan["owner_boundary_violations"] == ()
    assert not any(
        _is_forbidden_rw0_c2_module(target)
        for _caller, target in scan["resolved_imports"]
    )
    assert not any(
        target.rsplit(".", 1)[-1] in FORBIDDEN_RW0_C2_CALLS
        for _caller, target in scan["resolved_calls"]
    )

    package_tree = ast.parse(
        (source_root / "__init__.py").read_text(encoding="utf-8")
    )
    package_exports = set(_assignment(package_tree, "__all__"))
    assert package_exports.isdisjoint(FORBIDDEN_RW0_C2_EXPORTS)


def test_structural_nonimplementation_pure_owner_importers_and_callers_are_exact() -> None:
    source_root = ROOT / "src" / "ge_nwp_coordinator"
    index = _semantic_source_index(source_root)
    import_graph = {
        module: tuple(
            sorted(
                {
                    owner
                    for caller, target in index["imports"]
                    if caller == module
                    for owner in (_owner_module_for_target(target),)
                    if owner is not None and owner != module
                }
            )
        )
        for module in sorted(PURE_OWNER_MODULES)
    }
    _require_exact(
        import_graph == EXPECTED_PURE_OWNER_IMPORT_GRAPH,
        "structural_nonimplementation:resolved_owner_import_graph",
    )
    violations = _semantic_owner_boundary_violations(index)
    for kind in ("resolved_owner_call", "resolved_owner_reexport"):
        _require_exact(
            not any(violation[0] == kind for violation in violations),
            f"structural_nonimplementation:{kind}",
        )
    _require_exact(
        violations == (),
        "structural_nonimplementation:unexpected_semantic_violation",
    )


@pytest.mark.parametrize(
    "source",
    (
        "from ge_nwp_coordinator import _sqlite_rw0_c2_decision as x\n",
        "from . import _sqlite_rw0_c2_decision as x\n",
    ),
)
def test_hostile_structural_nonimplementation_importfrom_aliases_are_detected(
    tmp_path: Path,
    source: str,
) -> None:
    source_root = tmp_path / "src" / "ge_nwp_coordinator"
    source_root.mkdir(parents=True)
    (source_root / "__init__.py").write_text("__all__ = ()\n", encoding="utf-8")
    (source_root / "probe.py").write_text(source, encoding="utf-8")
    scan = _scan_production_source_tree(source_root)
    assert any(
        _is_forbidden_rw0_c2_module(module) for module in scan["imports"]
    )


def test_hostile_structural_nonimplementation_named_nested_module_is_detected(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src" / "ge_nwp_coordinator"
    nested = source_root / "internal"
    nested.mkdir(parents=True)
    (source_root / "__init__.py").write_text("__all__ = ()\n", encoding="utf-8")
    (nested / "__init__.py").write_text("__all__ = ()\n", encoding="utf-8")
    (nested / "_sqlite_rw0_c2_decision.py").write_text(
        "def persist_rw0_c2_durable_progression_decision():\n    pass\n",
        encoding="utf-8",
    )
    scan = _scan_production_source_tree(source_root)
    assert scan["prohibited_inventory"] == (
        "internal/_sqlite_rw0_c2_decision.py",
    )
    assert "persist_rw0_c2_durable_progression_decision" in scan["definitions"]


@pytest.mark.parametrize(
    ("hostile", "expected_boundary"),
    (
        ("neutral_nested_module", "source_manifest:count"),
        ("differently_named_writer", "source_manifest:count"),
        (
            "modified_existing_neutral_module",
            "source_manifest:sha256",
        ),
        ("symlink", "source_manifest:regular_files_only"),
    ),
)
def test_hostile_structural_nonimplementation_complete_source_manifest_rejects_change(
    tmp_path: Path,
    hostile: str,
    expected_boundary: str,
) -> None:
    source_root = tmp_path / "src" / "ge_nwp_coordinator"
    shutil.copytree(ROOT / "src" / "ge_nwp_coordinator", source_root)
    if hostile == "neutral_nested_module":
        target = source_root / "internal" / "worker.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("WORKER_MARKER = 'neutral-name'\n", encoding="utf-8")
    elif hostile == "differently_named_writer":
        target = source_root / "internal" / "_sqlite_rw0_c2_writer.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("WRITER_MARKER = 'differently-named'\n", encoding="utf-8")
    elif hostile == "modified_existing_neutral_module":
        target = source_root / "__init__.py"
        target.write_text(
            target.read_text(encoding="utf-8") + "\nSOURCE_MANIFEST_HOSTILE = True\n",
            encoding="utf-8",
        )
    else:
        (source_root / "source-manifest-hostile-link.py").symlink_to(
            source_root / "__init__.py"
        )
    with pytest.raises(AssertionError, match=f"^{expected_boundary}$"):
        _assert_fixed_source_nonimplementation_manifest(source_root)


def test_state_store_and_writer_session_public_method_inventories_are_unchanged() -> None:
    source = ROOT / "src" / "ge_nwp_coordinator" / "state_store.py"
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    assert _class_methods(tree, "StateStore") == (
        "read_current",
        "read_global_stop",
    )
    assert _class_methods(tree, "WriterSession") == (
        "metadata",
        "active",
        "apply_transition",
        "apply_global_stop_update",
        "close",
        "__enter__",
        "__exit__",
    )


def test_current_pure_owner_modules_remain_present_without_public_exports() -> None:
    source_root = ROOT / "src" / "ge_nwp_coordinator"
    evidence_tree = ast.parse(
        (source_root / "_post_execution_evidence_values.py").read_text(
            encoding="utf-8"
        )
    )
    decision_tree = ast.parse(
        (source_root / "_rw0_c_decision_input_values.py").read_text(
            encoding="utf-8"
        )
    )
    evidence_definitions = {
        node.name for node in evidence_tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef))
    }
    decision_definitions = {
        node.name for node in decision_tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef))
    }
    assert {
        "validate_post_execution_validation_result_set",
        "validate_independent_review_disposition",
        "evaluate_post_execution_reviewer_separation",
    } <= evidence_definitions
    assert {
        "evaluate_rw0_c_decision_time_authority_branches",
        "evaluate_rw0_c_decision_time_global_stop_branches",
        "evaluate_rw0_c_decision_time_source_effect_ceiling_branches",
        "evaluate_rw0_c_recommendation_consistency",
    } <= decision_definitions
    assert _assignment(decision_tree, "__all__") == ()


def test_migration_inventory_and_bytes_are_exactly_0001_through_0004() -> None:
    migration_root = ROOT / "src" / "ge_nwp_coordinator" / "sqlite_migrations"
    sql_paths = tuple(sorted(migration_root.glob("*.sql")))
    assert tuple(path.name for path in sql_paths) == tuple(MIGRATION_SHA256)
    assert "0005" not in " ".join(path.name for path in migration_root.iterdir())
    assert {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sql_paths
    } == MIGRATION_SHA256


def _replay_family(original, mutation_ref, command_digest):
    """Receipt-first, branch-neutral conformance operation; never reevaluates a reducer."""
    if original["mutation_ref"] != mutation_ref:
        return None
    if original["command_digest"] != command_digest:
        return _no_write("mutation_ref_reuse_conflict")
    required = {"mutation_ref", "command_digest", "decision", "version", "head", "result", "receipt", "timestamp"}
    if not required.issubset(original) or (original.get("branch") == "candidate_acceptance" and "acceptance_fact" not in original):
        return _no_write("required_fact_invalid")
    return deepcopy(original)


@pytest.mark.parametrize("role", ("lineage", "scope", "admission", "continuity", "sole_active", "no_foreign_claim"))
@pytest.mark.parametrize("branch", ("candidate_acceptance", "candidate_repair", "attempt_selecting_replan", "program_terminal_reject", "post_execution_program_block"))
def test_admitted_lineage_relation_is_required_for_every_applicable_command(contract, role, branch):
    state = _baseline(contract)
    state["guard_relation"][role] = "unreadable"
    state["expected_branch"] = branch
    _assert_no_write(_interpret(contract, state), "bootstrap_acceptance_guard_conflict")


def test_one_classifier_includes_the_acceptance_fact(contract):
    family = {"decision": "d", "version": "v", "head": "h", "acceptance_fact": "f", "result": "r", "receipt": "q"}
    exact = _recover(contract, commit_attempted=True, expected_family=family, observed_family=family)
    assert exact["classification"] == "committed_exact", "c2:whole_family_exact"
    for missing in ("decision", "acceptance_fact"):
        partial = dict(family)
        del partial[missing]
        assert _recover(contract, commit_attempted=True, expected_family=family, observed_family=partial)["classification"] == "unresolved", "c2:partial_family_unresolved"


@pytest.mark.parametrize('human,machine,kind', [
    (True, 1, 'type'), (1, True, 'type'), (False, 0, 'type'), (0, False, 'type'),
    ('sibling', 'original', 'value'), (None, 'value', 'type'),
    ([True], [1], 'type'), ((1,), [1], 'type'),
])
def test_typed_human_machine_equivalence_c2_scalars(human, machine, kind):
    pointer = '/role/0' if type(human) is list and type(machine) is list else '/role'
    with pytest.raises(AssertionError, match='^' + re.escape('c2:human_machine_equivalence:' + pointer + ':' + kind) + '$'):
        _type_exact({'role': human}, {'role': machine})


def test_typed_human_machine_equivalence_c2_document(owner_text):
    changed = _replace_in_region(owner_text, HUMAN_BEGIN, HUMAN_END, '"mutates_guard":false', '"mutates_guard":0')
    with pytest.raises(AssertionError, match='^c2:human_machine_equivalence:/terminal/mutates_guard:type$'):
        _validate_document_text(changed)


def test_model_after_guard_c2_phase_cannot_be_called_early(contract):
    prepared = _interpret_pre_model(contract, _baseline(contract))
    with pytest.raises(AssertionError, match='^c2:model_after_guard:guard_gate$'):
        _model_consistency_phase(contract, prepared)
