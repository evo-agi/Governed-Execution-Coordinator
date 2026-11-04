"""Target-only RW0-C2 value/profile contract; no future runtime imports."""

import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / ".docs/rw0-c2-private-value-versioning.md"
BEGIN = "<!-- RW0_C2_PRIVATE_VALUES_MACHINE_BEGIN -->"
END = "<!-- RW0_C2_PRIVATE_VALUES_MACHINE_END -->"
PREFIX = "governed-execution.nwp-rw0-c2-"


class ContractViolation(AssertionError):
    def __init__(self, boundary):
        self.boundary = boundary
        super().__init__(boundary)


def _exact(actual, wanted, boundary):
    if type(actual) is not type(wanted):
        raise ContractViolation(boundary)
    if type(wanted) is dict:
        if set(actual) != set(wanted):
            raise ContractViolation(boundary)
        for key in wanted:
            _exact(actual[key], wanted[key], boundary)
    elif type(wanted) is list:
        if len(actual) != len(wanted):
            raise ContractViolation(boundary)
        for item, expected in zip(actual, wanted, strict=True):
            _exact(item, expected, boundary)
    elif actual != wanted:
        raise ContractViolation(boundary)


def _strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ContractViolation("duplicate_json_key")
            result[key] = value
        return result

    return json.loads(raw, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ContractViolation("nonfinite_json")))


def _document():
    text = OWNER.read_text(encoding="utf-8")
    assert text.count(BEGIN) == text.count(END) == 1
    region = text.split(BEGIN, 1)[1].split(END, 1)[0]
    assert region.count("```") == 2
    raw = region.split("```json\n", 1)[1].split("\n```", 1)[0]
    return text, _strict_json(raw)


# Fixed expectations are independently authored here; the observed registry is
# parsed only from the owner document. Slugs are fixed test literals, not read
# from that registry.
SCHEMAS = [
    ("admission_act", "verified-admission-act", "external_safe_evidence", "schema_id act_ref act_digest lineage_ref scope_ref guard_profile applicability provenance_ref provenance_digest projection_digest"),
    ("scope_admission_fact", "scope-admission-fact", "immutable_durable_fact", "schema_id admission_fact_ref act_ref act_digest lineage_ref scope_ref guard_profile applicability provenance_ref provenance_digest one_shot_ceiling admission_fact_digest"),
    ("command_relation", "admitted-command-relation", "transient_command_relation", "schema_id lineage_ref scope_ref admission_fact_ref admission_fact_digest guard_profile applicability admission_act_ref admission_act_digest continuity_basis_ref continuity_basis_digest continuity_source_ref continuity_source_digest sole_active_basis_ref sole_active_basis_digest sole_active_source_ref sole_active_source_digest mutation_ref program_ref decision_basis_ref decision_basis_digest expected_head_ref expected_head_revision expected_head_digest preassigned_decision_ref preassigned_version_ref preassigned_acceptance_fact_ref preassigned_relation_ref preassigned_guarded_result_ref family_route relation_digest"),
    ("continuity_basis", "verified-lineage-continuity", "external_current_safe_evidence", "schema_id basis_ref source_ref source_digest lineage_ref scope_ref authority_epoch_ref currentness_ref currentness_digest provenance_ref provenance_digest projection_digest"),
    ("sole_active_basis", "verified-sole-active", "external_current_safe_evidence", "schema_id basis_ref source_ref source_digest lineage_ref scope_ref authority_epoch_ref currentness_ref currentness_digest active_authority_ref sole_active_assertion_ref sole_active_assertion_digest provenance_ref provenance_digest projection_digest"),
    ("acceptance_fact", "bootstrap-acceptance-fact", "immutable_durable_fact", "schema_id acceptance_fact_ref lineage_ref scope_ref admission_fact_ref admission_fact_digest mutation_ref command_digest decision_ref decision_digest version_ref version_digest historical_head_ref historical_head_revision historical_head_digest selected_attempt_ref selected_candidate_ref basis_ref basis_digest family_route accepted_at acceptance_fact_digest"),
    ("family_relation", "guarded-family-relation", "immutable_supplemental_relation", "schema_id relation_ref branch lineage_ref scope_ref command_digest admission_act_ref admission_act_digest admission_fact_ref admission_fact_digest continuity_basis_ref continuity_basis_digest sole_active_basis_ref sole_active_basis_digest decision_ref decision_digest version_ref version_digest historical_head_ref historical_head_revision historical_head_digest historical_head_postimage acceptance_fact_ref acceptance_fact_digest generic_result_projection_digest family_route relation_digest"),
    ("guarded_result", "guarded-progression-result", "derived_result_composite", "schema_id guarded_result_ref branch generic_v1_result_schema_id generic_v1_result_digest family_relation_ref family_relation_digest receipt_graph_profile_id guarded_result_digest"),
    ("receipt_graph_profile", "receipt-graph-profile", "static_contract_metadata", "schema_id version authoritative_branches common_roles acceptance_only_role role_bindings ordinal_per_role role_entry_fields exact_member_verification extra_or_duplicate_roles supersession_rule"),
    ("recovery_selector", "complete-family-selector", "transient_query_value", "schema_id lineage_ref scope_ref admission_fact_ref admission_fact_digest mutation_ref command_digest decision_ref version_ref acceptance_fact_ref relation_ref guarded_result_ref family_route required_collision_routes selector_digest"),
    ("recovery_result", "complete-family-recovery-result", "transient_read_projection", "schema_id classification lineage_ref scope_ref current_continuity_posture_ref current_continuity_posture_digest current_sole_active_posture_ref current_sole_active_posture_digest"),
]
EXPECTED_SCHEMAS = [
    [key, PREFIX + slug + ".v1", None if key == "receipt_graph_profile" else PREFIX + slug + ".v1.identity", form, fields.split()]
    for key, slug, form, fields in SCHEMAS
]

# Columns: semantic owner, future writer, verifier, status, command coverage,
# graph coverage, selector coverage, replay owner, recovery owner, substitutes.
AUTHORITY = {
    "admission_act": ["external_standing_policy", "external_standing_policy", "external_current_verifier", "external_safe_evidence", "act_expectation", "verified_evidence_role", "act_via_admission", "decision_owner", "decision_owner", ["caller", "model", "local_digest"]],
    "scope_admission_fact": ["guard_owner", "future_separate_admission_provisioner", "guarded_decision_verifier", "immutable_durable", "ref_and_digest", "required_role", "ref_and_digest", "decision_owner", "decision_owner", ["decision_writer", "local_absence", "database"]],
    "command_relation": ["guard_and_decision_owners", "none", "guarded_decision_verifier", "transient", "all_expectations", "via_command_digest", "exact_expectations", "decision_owner", "decision_owner", ["caller_admission", "model_branch"]],
    "continuity_basis": ["guard_owner_external_currentness", "none", "external_current_verifier", "external_current_safe_evidence", "basis_and_source", "historical_evidence_role", "basis_and_source", "decision_owner", "decision_owner", ["stored_snapshot", "machine", "database", "process"]],
    "sole_active_basis": ["guard_owner_external_currentness", "none", "external_current_verifier", "external_current_safe_evidence", "basis_and_source", "historical_evidence_role", "basis_and_source", "decision_owner", "decision_owner", ["local_lock", "writer_row", "machine"]],
    "acceptance_fact": ["guard_owner", "future_guarded_decision_writer", "whole_family_verifier", "immutable_durable", "preassigned_ref_only", "acceptance_only_role", "preassigned_ref", "decision_owner", "decision_owner", ["terminal", "grant", "replay"]],
    "family_relation": ["decision_owner", "future_guarded_decision_writer", "whole_family_verifier", "immutable_supplemental", "preassigned_ref_only", "required_role", "preassigned_ref", "decision_owner", "decision_owner", ["receipt_digest_only", "mutable_head_currentness"]],
    "guarded_result": ["decision_owner", "none", "whole_family_verifier", "derived_composite", "preassigned_ref_only", "required_role", "preassigned_ref", "decision_owner", "decision_owner", ["generic_v1_reinterpretation"]],
    "receipt_graph_profile": ["decision_owner", "none", "whole_family_verifier", "static_contract_metadata", "excluded", "transitive_via_guarded_result", "excluded", "decision_owner", "decision_owner", ["graph_digest_only", "second_receipt", "durable_profile_row"]],
    "recovery_selector": ["decision_owner", "none", "whole_family_verifier", "transient", "excluded", "excluded", "self", "decision_owner", "decision_owner", ["local_absence", "timestamp", "postcommit_digest"]],
    "recovery_result": ["decision_owner", "none", "whole_family_verifier", "transient", "excluded", "excluded", "excluded", "decision_owner", "decision_owner", ["automatic_retry", "fragment_repair", "stale_posture"]],
}

CANONICALIZATION = {
    "json": "utf8_ensure_ascii_false_allow_nan_false_sort_keys_compact",
    "digest": "sha256(domain_utf8+nul+identity_json_utf8)",
    "self_digest": "excluded", "unknown_fields": "reject",
    "duplicate_keys_recursive": "reject", "types": "exact_builtin_no_bool_as_int",
    "array_order": "significant",
}
INCLUDES = "command_profile lineage_ref scope_ref admission_fact_ref admission_fact_digest admission_act_ref admission_act_digest guard_profile applicability continuity_basis_ref continuity_basis_digest continuity_source_ref continuity_source_digest sole_active_basis_ref sole_active_basis_digest sole_active_source_ref sole_active_source_digest mutation_ref program_ref decision_basis_ref decision_basis_digest expected_head_ref expected_head_revision expected_head_digest preassigned_decision_ref preassigned_version_ref preassigned_acceptance_fact_ref preassigned_relation_ref preassigned_guarded_result_ref family_route".split()
EXCLUDES = "caller_branch caller_acceptance_conclusion transaction_timestamp resulting_row_digests receipt_graph_digest terminal_outcome raw_credentials raw_external_attestations".split()
COMMAND_DOMAIN = "governed-execution.nwp-rw0-c2-guarded-command-digest.v1.identity"
COMMAND_DIGEST = {"includes": INCLUDES, "excludes": EXCLUDES,
                  "admitted_scope_match_required": True,
                  "caller_can_select_unadmitted_scope": False,
                  "derivation_order": "after_six_independent_siblings",
                  "name": "guarded_command_digest_v1", "domain": COMMAND_DOMAIN,
                  "ordered_preimage": [[name, "command_relation." + ("schema_id" if name == "command_profile" else name),
                                         "nonnegative_exact_int_not_bool" if name == "expected_head_revision" else
                                         "lowercase_sha256_hex_64" if name.endswith("_digest") or name.startswith("preassigned_") or name == "family_route" else
                                         "nonempty_exact_str"] for name in INCLUDES],
                  "serialization": "ordered_name_value_pairs_utf8_json_ensure_ascii_false_allow_nan_false_compact",
                  "digest": "sha256(domain_utf8+nul+preimage_json_utf8)",
                  "fixed_vector_digest": "a392abcc3f0981b4ac2aeab5d3869aea9f24ba7305b242563e3a41f402b716b1"}
COMMAND_DIGEST_V2 = {
    "name": "guarded_command_digest_v2",
    "domain": "governed-execution.nwp-rw0-c2-guarded-command-digest.v2.identity",
    "ordered_preimage_prefix_ref": "command_digest.ordered_preimage",
    "ordered_preimage_suffix": [["expected_branch", "command.expected_branch",
                                 "null_or_exact_finite_branch_str"]],
    "ordered_pair_count": 31,
    "serialization": "ordered_name_value_pairs_utf8_json_ensure_ascii_false_allow_nan_false_compact",
    "digest": "sha256(domain_utf8+nul+preimage_json_utf8)",
    "derivation_order": "after_six_independent_siblings",
    "preassignments_exclude_expected_branch": True,
    "replay_identity_includes_expected_branch": True,
    "finite_expected_branch_values": [None, "candidate_acceptance", "candidate_repair",
                                      "attempt_selecting_replan",
                                      "program_terminal_reject",
                                      "post_execution_program_block"],
    "fixed_vector_expected_branch": None,
    "fixed_vector_digest": "ed40b1bc67f9b4604075a31d1ce2e5a3ecf9247ff02152e4803be24e59d30976",
}
ACCEPTANCE_SCHEMA = "governed-execution.nwp-rw0-c2-bootstrap-acceptance-fact.v1"
PROSPECTIVE_DOMAIN = "governed-execution.nwp-rw0-c2-bootstrap-acceptance-fact.v1.prospective-ref"
PRIMITIVE_NAMES = "command_profile lineage_ref scope_ref admission_fact_ref admission_fact_digest admission_act_ref admission_act_digest guard_profile applicability continuity_basis_ref continuity_basis_digest continuity_source_ref continuity_source_digest sole_active_basis_ref sole_active_basis_digest sole_active_source_ref sole_active_source_digest mutation_ref program_ref decision_basis_ref decision_basis_digest expected_head_ref expected_head_revision expected_head_digest".split()
assert INCLUDES == PRIMITIVE_NAMES + ["preassigned_decision_ref", "preassigned_version_ref", "preassigned_acceptance_fact_ref", "preassigned_relation_ref", "preassigned_guarded_result_ref", "family_route"]

def _primitive_type(name):
    if name == "expected_head_revision":
        return "nonnegative_exact_int_not_bool"
    if name.endswith("_digest"):
        return "lowercase_sha256_hex_64"
    return "nonempty_exact_str"

PREIMAGE = [[name, "preassignment_basis." + name, _primitive_type(name)] for name in PRIMITIVE_NAMES]
PROSPECTIVE = {
    "command_field": "preassigned_acceptance_fact_ref",
    "required_all_branches": True, "nullable": False, "assertion_only": True,
    "coordinator_derived": True, "caller_selects_branch": False,
    "wrong_ref_invalid": True, "domain": PROSPECTIVE_DOMAIN,
    "ordered_preimage": PREIMAGE,
    "serialization": "ordered_name_value_pairs_utf8_json_ensure_ascii_false_allow_nan_false_compact",
    "digest": "sha256(domain_utf8+nul+preimage_json_utf8)",
    "ref_encoding": "lowercase_sha256_hex_64",
    "preimage_excludes": "authoritative_branch expected_branch result guarded_relation_digest guarded_result_digest receipt_ref receipt_digest transaction_timestamp terminal_outcome current_head_after_commit raw_external_attestations".split(),
    "command_digest_covered": True, "selector_covered": True,
    "collision_probe_all_branches": True, "acceptance_fact_count": 1,
    "nonaccept_fact_count": 0, "nonaccept_absence_proves_unclaimed": False,
    "derivation_basis": "guarded_family_preassignment_basis_v1",
    "sibling_independent": True,
}
COMMON_ROLES = "verified_admission_act scope_admission_fact historical_continuity_basis historical_sole_active_basis decision program_version historical_head_postimage generic_v1_result_projection guarded_family_relation guarded_result_composite".split()
GRAPH = {"root": "generic_v1_mutation_receipt", "common_roles": COMMON_ROLES,
         "root_fields": "mutation_ref command_digest result_projection_digest mutation_graph_digest committed_at".split(),
         "acceptance_only_role": "acceptance_fact",
         "historical_head_fields": "schema_id program_ref current_program_version_ref current_program_version_number head_revision program_state updated_at head_digest".split(),
         "historical_head_equalities": [
             "family_relation.historical_head_ref=historical_head_postimage.program_ref",
             "family_relation.historical_head_revision=historical_head_postimage.head_revision",
             "family_relation.historical_head_digest=historical_head_postimage.head_digest",
             "historical_head_postimage.current_program_version_ref=family_relation.version_ref",
             "acceptance_fact.historical_head_ref=family_relation.historical_head_ref",
             "acceptance_fact.historical_head_revision=family_relation.historical_head_revision",
             "acceptance_fact.historical_head_digest=family_relation.historical_head_digest",
         ],
         "role_bindings": {
             "verified_admission_act": ["admission_act.act_ref", "admission_act.act_digest", "authenticated_external_act"],
             "scope_admission_fact": ["scope_admission_fact.admission_fact_ref", "scope_admission_fact.admission_fact_digest", "verified_provisioner_fact"],
             "historical_continuity_basis": ["continuity_basis.basis_ref", "continuity_basis.projection_digest", "verified_historical_external_evidence"],
             "historical_sole_active_basis": ["sole_active_basis.basis_ref", "sole_active_basis.projection_digest", "verified_historical_external_evidence"],
             "decision": ["v1_decision.decision_ref", "v1_decision.decision_digest", "v1_decision_reconstruction"],
             "program_version": ["v1_program_version.program_version_ref", "v1_program_version.program_version_digest", "v1_version_reconstruction"],
             "historical_head_postimage": ["family_relation.historical_head_postimage.program_ref", "family_relation.historical_head_postimage.head_digest", "v1_head_reconstruction_from_complete_snapshot"],
             "generic_v1_result_projection": ["v1_decision.decision_ref", "generic_result_projection.result_projection_digest", "v1_result_reconstruction"],
             "guarded_family_relation": ["family_relation.relation_ref", "family_relation.relation_digest", "guarded_relation_reconstruction"],
             "guarded_result_composite": ["guarded_result.guarded_result_ref", "guarded_result.guarded_result_digest", "guarded_result_reconstruction"],
             "acceptance_fact": ["acceptance_fact.acceptance_fact_ref", "acceptance_fact.acceptance_fact_digest", "verified_acceptance_only_fact"],
         },
         "ordinal_per_role": 0,
         "exact_member_verification": True, "digest_alone_proves_members": False,
         "extra_or_duplicate_roles": "reject",
         "guarded_result_profile_selector": "receipt_graph_profile_id",
         "profile_graph_role": False,
         "profile_instance_digest": False,
         "generic_receipt_self_digest": False,
         "source_exact_digest": "current_v1_receipt_preimage_plus_exact_ordered_graph_entries",
         "source_exact_receipt_preimage_fields": "schema_id mutation_ref mutation_family command_schema_id command_digest program_ref decision_ref result_program_version_ref result_semantic_attempt_ref result_effect_intent_ref result_effect_fence_ref result_delivery_attempt_ref result_observation_ref result_decision_ref result_class result_projection_digest outcome committed_at".split(),
         "profile_completeness_rule": "reconstruct_graph_and_exact_members_then_validate_guarded_result_profile_and_branch"}
BRANCHES = {
    "candidate_acceptance": ["accept", "candidate_acceptance", 1, "required"],
    "candidate_repair": ["repair", "candidate_repair", 0, "forbidden"],
    "attempt_selecting_replan": ["replan", "attempt_selecting_replan", 0, "forbidden"],
    "program_terminal_reject": ["terminal_reject", "program_terminal_reject", 0, "forbidden"],
    "post_execution_program_block": ["block", "program_block", 0, "forbidden"],
}
PROFILE_ID = "governed-execution.nwp-rw0-c2-receipt-graph-profile.v1"
EXPECTED_STATIC_RECEIPT_PROFILE = {
    "schema_id": PROFILE_ID,
    "version": 1,
    "authoritative_branches": ["candidate_acceptance", "candidate_repair",
                               "attempt_selecting_replan", "program_terminal_reject",
                               "post_execution_program_block"],
    "common_roles": ['verified_admission_act', 'scope_admission_fact', 'historical_continuity_basis', 'historical_sole_active_basis', 'decision', 'program_version', 'historical_head_postimage', 'generic_v1_result_projection', 'guarded_family_relation', 'guarded_result_composite'],
    "acceptance_only_role": "acceptance_fact",
    "role_bindings": {'verified_admission_act': ['admission_act.act_ref',
                            'admission_act.act_digest',
                            'authenticated_external_act'],
 'scope_admission_fact': ['scope_admission_fact.admission_fact_ref',
                          'scope_admission_fact.admission_fact_digest',
                          'verified_provisioner_fact'],
 'historical_continuity_basis': ['continuity_basis.basis_ref',
                                 'continuity_basis.projection_digest',
                                 'verified_historical_external_evidence'],
 'historical_sole_active_basis': ['sole_active_basis.basis_ref',
                                  'sole_active_basis.projection_digest',
                                  'verified_historical_external_evidence'],
 'decision': ['v1_decision.decision_ref',
              'v1_decision.decision_digest',
              'v1_decision_reconstruction'],
 'program_version': ['v1_program_version.program_version_ref',
                     'v1_program_version.program_version_digest',
                     'v1_version_reconstruction'],
 'historical_head_postimage': ['family_relation.historical_head_postimage.program_ref',
                               'family_relation.historical_head_postimage.head_digest',
                               'v1_head_reconstruction_from_complete_snapshot'],
 'generic_v1_result_projection': ['v1_decision.decision_ref',
                                  'generic_result_projection.result_projection_digest',
                                  'v1_result_reconstruction'],
 'guarded_family_relation': ['family_relation.relation_ref',
                             'family_relation.relation_digest',
                             'guarded_relation_reconstruction'],
 'guarded_result_composite': ['guarded_result.guarded_result_ref',
                              'guarded_result.guarded_result_digest',
                              'guarded_result_reconstruction'],
 'acceptance_fact': ['acceptance_fact.acceptance_fact_ref',
                     'acceptance_fact.acceptance_fact_digest',
                     'verified_acceptance_only_fact']},
    "ordinal_per_role": 0,
    "role_entry_fields": ["role", "ordinal", "record_ref", "record_digest"],
    "exact_member_verification": True,
    "extra_or_duplicate_roles": "reject",
    "supersession_rule": "new_profile_id_version_and_successor_guarded_result_contract",
}
ROUTES = [
    {"role": "mutation_receipt_route", "kind": "receipt_replay", "key_sources": ["mutation_ref"], "expected_schema_id": "governed-execution.nwp-development-mutation-receipt.v1"},
    {"role": "decision_identity_route", "kind": "preassigned_identity", "key_sources": ["decision_ref"], "expected_schema_id": "governed-execution.nwp-development-decision.v1"},
    {"role": "resulting_version_identity_route", "kind": "preassigned_identity", "key_sources": ["version_ref"], "expected_schema_id": "governed-execution.nwp-development-program-version.v1"},
    {"role": "acceptance_fact_identity_route", "kind": "preassigned_identity", "key_sources": ["acceptance_fact_ref"], "expected_schema_id": ACCEPTANCE_SCHEMA},
    {"role": "guarded_family_relation_identity_route", "kind": "preassigned_identity", "key_sources": ["relation_ref"], "expected_schema_id": "governed-execution.nwp-rw0-c2-guarded-family-relation.v1"},
    {"role": "guarded_progression_result_identity_route", "kind": "preassigned_identity", "key_sources": ["guarded_result_ref"], "expected_schema_id": "governed-execution.nwp-rw0-c2-guarded-progression-result.v1"},
    {"role": "deterministic_family_route", "kind": "deterministic_family", "key_sources": ["family_route"], "expected_schema_id": None},
    {"role": "admitted_scope_winner_route", "kind": "scope_complete_winner", "key_sources": ["lineage_ref", "scope_ref", "admission_fact_ref", "admission_fact_digest"], "expected_schema_id": None},
]
EXPECTED_CONCRETE_ROUTES = [
    ("mutation_receipt_route", "receipt_replay", ["mutation-A"], "governed-execution.nwp-development-mutation-receipt.v1"),
    ("decision_identity_route", "preassigned_identity", ["400960b261c148544c0d0c29d2c65bf7b6b85b679d18c52d2ab4ec793198f208"], "governed-execution.nwp-development-decision.v1"),
    ("resulting_version_identity_route", "preassigned_identity", ["1d930498247537c7934366c77a35a3a7c0614402ceefa87b49d713143220f237"], "governed-execution.nwp-development-program-version.v1"),
    ("acceptance_fact_identity_route", "preassigned_identity", ["e45e55113d63769b1a4a157aa5a0d8a1621516ba5b81155535f1116af66e8f17"], "governed-execution.nwp-rw0-c2-bootstrap-acceptance-fact.v1"),
    ("guarded_family_relation_identity_route", "preassigned_identity", ["0fbf19ecc76ca0a2c6ffba5c8c4b07157cdb1645a722b0df130ed5c30b832f77"], "governed-execution.nwp-rw0-c2-guarded-family-relation.v1"),
    ("guarded_progression_result_identity_route", "preassigned_identity", ["28719afd5182e5a76ea2d17502d70b62cc2e1817f4b82e460d8a1f2225700254"], "governed-execution.nwp-rw0-c2-guarded-progression-result.v1"),
    ("deterministic_family_route", "deterministic_family", ["4f13fe4404b53c9d521eac90a64d87352d1077e307be5a33a8dd9c27c33079b9"], None),
    ("admitted_scope_winner_route", "scope_complete_winner", ["lineage-A", "scope-A", "admission-A", "68303f1a8c16309605c3701d88ad63858b40a6a4ae5b0ad8ee116a44b5d33ae1"], None),
]
EXPECTED_PROSE_ROUTE_ROWS = [
    ("mutation_receipt_route", "receipt_replay", ("mutation_ref",), "governed-execution.nwp-development-mutation-receipt.v1"),
    ("decision_identity_route", "preassigned_identity", ("decision_ref",), "governed-execution.nwp-development-decision.v1"),
    ("resulting_version_identity_route", "preassigned_identity", ("version_ref",), "governed-execution.nwp-development-program-version.v1"),
    ("acceptance_fact_identity_route", "preassigned_identity", ("acceptance_fact_ref",), "governed-execution.nwp-rw0-c2-bootstrap-acceptance-fact.v1"),
    ("guarded_family_relation_identity_route", "preassigned_identity", ("relation_ref",), "governed-execution.nwp-rw0-c2-guarded-family-relation.v1"),
    ("guarded_progression_result_identity_route", "preassigned_identity", ("guarded_result_ref",), "governed-execution.nwp-rw0-c2-guarded-progression-result.v1"),
    ("deterministic_family_route", "deterministic_family", ("family_route",), None),
    ("admitted_scope_winner_route", "scope_complete_winner", ("lineage_ref", "scope_ref", "admission_fact_ref", "admission_fact_digest"), None),
]
SELECTOR = {
    "includes": "lineage_ref scope_ref admission_fact_ref admission_fact_digest mutation_ref command_digest decision_ref version_ref acceptance_fact_ref relation_ref guarded_result_ref family_route required_collision_routes".split(),
    "excludes": "transaction_timestamp receipt_digest receipt_graph_digest resulting_row_digests".split(),
    "route_element_fields": ["role", "kind", "key", "expected_schema_id"],
    "route_element_types": {"role": "closed_enum_str", "kind": "closed_enum_str", "key": "ordered_nonnull_exact_string_array", "expected_schema_id": "exact_versioned_str_or_null"},
    "route_instantiation": "ordered_selector_top_level_values_for_template_key_sources",
    "concrete_route_element_fields": ["role", "kind", "key", "expected_schema_id"],
    "concrete_key_type": "ordered_nonnull_exact_string_array",
    "concrete_routes_all_branches": True,
    "exact_route_count": 8, "exact_order": True, "role_once": True,
    "no_extensions": True, "key_equals_selector_top_level": True,
    "all_branches": True, "no_timestamp_or_postcommit_digest_dependency": True,
    "local_absence_proves_unclaimed": False,
}
REPLAY = {
    "returns": "original_decision original_version historical_head_postimage original_optional_acceptance_fact original_guarded_relation original_guarded_result original_generic_v1_receipt original_transaction_timestamp".split(),
    "reevaluate_branch": False, "new_fact": False, "new_timestamp": False,
    "change_current_head": False, "renew_scope": False,
    "fresh_external_posture_required": True,
    "historical_basis_is_current_permission": False,
}
RECOVERY = {
    "classes": ["committed_exact", "definitely_not_committed", "unresolved"],
    "cases": "same_mutation_same_command_complete_exact same_mutation_different_command_conflict preassigned_identity_or_route_collision different_complete_winner_same_scope exact_total_original_family_absence partial_orphan_duplicate_malformed_foreign_unreadable restore_or_clone_continuity_unproved".split(),
    "exact_complete_original_class": "committed_exact",
    "same_mutation_different_digest_reason": "mutation_ref_reuse_conflict",
    "identity_or_family_route_collision_reason": "preassigned_identity_or_family_route_collision",
    "total_absence_class": "definitely_not_committed",
    "total_absence_requires_all_routes_checked": True,
    "total_absence_requires_positive_current_continuity": True,
    "total_absence_requires_positive_current_sole_active": True,
    "local_absence_without_current_posture_class": "unresolved",
    "missing_malformed_unreadable_foreign_duplicate_unchecked_route_class": "unresolved",
    "partial_or_orphan_fact_class": "unresolved",
    "different_complete_winner_can_prove_original_noncommit": True,
    "different_complete_winner_fresh_acceptance_eligible": False,
    "fresh_retry_eligibility_separate": True,
    "fresh_external_posture_required": True, "fragment_repair": False,
    "branch_reevaluation": False, "new_timestamp": False,
    "automatic_retry": False, "scope_renewal": False,
}
V1 = {
    "decision": ["governed-execution.nwp-development-decision.v1", "governed-execution.nwp-development-decision.v1.identity"],
    "program_version": ["governed-execution.nwp-development-program-version.v1", "governed-execution.nwp-development-program-version.v1.identity"],
    "program_head": ["governed-execution.nwp-development-program-head.v1", "governed-execution.nwp-development-program-head.v1.identity"],
    "generic_result": ["governed-execution.nwp-record-development-progression-decision-result.v1", "governed-execution.nwp-record-development-progression-decision-result.v1.identity", "schema_id program_ref decision_ref result_program_version_ref result_decision_ref".split()],
    "generic_receipt": ["governed-execution.nwp-development-mutation-receipt.v1", "governed-execution.nwp-development-mutation-receipt.v1.identity"],
    "graph_entry_fields": "role ordinal record_ref record_digest".split(),
    "migration_catalog": ["0001_initial.sql", "0002_development_program_and_effect_state.sql", "0003_cognitive_proposal_and_selection_state.sql", "0004_rw0_c1_durable_evidence.sql"],
    "preserve_bytes": True, "append_existing_v1_field": False, "new_v1_authority": False,
}
B1 = {"pair": ["latch_postimage_ref", "latch_postimage_digest"],
      "guarded_writer_consumes_pair": False,
      "pair_proves": "supplied_representation_and_pair_coherence_only",
      "durable_guard_authority": False,
      "terminal_consumer": "separately_accepted_safe_value_compatibility_versioning_contract",
      "successor_defined": False}
BOUNDARIES = {
    "admission_writer": "future_separate_admission_provisioner_only",
    "acceptance_writer": "future_guarded_decision_writer_acceptance_only",
    "receipts": 1, "replay_owners": 1, "recovery_classifiers": 1,
    "local_absence_admits_or_unclaims": False,
    "operational_identity_is_lineage": False,
    "external_currentness_is_local_durable_fact": False,
    "mutable_latch_state": False,
    "terminal_creates_or_replenishes_acceptance": False,
    "es_replenishes_direct_local": False,
    "migration_0005_implemented": False,
    "provisioner_implemented": False, "writer_implemented": False,
    "reader_implemented": False, "recovery_implemented": False,
    "production_caller_implemented": False, "public_export_implemented": False,
    "runtime_implemented": False,
}
OWNERS = {
    "guard": ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
    "decision": ".docs/rw0-c2-durable-progression-decision-semantic-contract.md",
    "values": ".docs/rw0-c2-private-value-versioning.md",
    "composition": ".docs/autonomous-software-development-operating-model.md",
    "implemented_v1": "current_source_and_migrations",
}

PRIMITIVE_SOURCES = {
    "command_profile": ("contract_literal", "contract_literal"),
    "lineage_ref": ("current_owner_durable_current_value", "verified_scope_admission_fact"),
    "scope_ref": ("current_owner_durable_current_value", "verified_scope_admission_fact"),
    "admission_fact_ref": ("current_owner_durable_current_value", "verified_scope_admission_fact"),
    "admission_fact_digest": ("current_owner_durable_current_value", "verified_scope_admission_fact"),
    "admission_act_ref": ("externally_verified", "verified_admission_act"),
    "admission_act_digest": ("externally_verified", "verified_admission_act"),
    "guard_profile": ("current_owner_durable_current_value", "verified_scope_admission_fact"),
    "applicability": ("current_owner_durable_current_value", "verified_scope_admission_fact"),
    "continuity_basis_ref": ("externally_verified", "verified_continuity_basis"),
    "continuity_basis_digest": ("externally_verified", "verified_continuity_basis"),
    "continuity_source_ref": ("externally_verified", "verified_continuity_basis"),
    "continuity_source_digest": ("externally_verified", "verified_continuity_basis"),
    "sole_active_basis_ref": ("externally_verified", "verified_sole_active_basis"),
    "sole_active_basis_digest": ("externally_verified", "verified_sole_active_basis"),
    "sole_active_source_ref": ("externally_verified", "verified_sole_active_basis"),
    "sole_active_source_digest": ("externally_verified", "verified_sole_active_basis"),
    "mutation_ref": ("caller_expectation_independently_verified", "verified_mutation_identity"),
    "program_ref": ("current_owner_durable_current_value", "current_program_identity"),
    "decision_basis_ref": ("caller_expectation_independently_verified", "current_decision_basis"),
    "decision_basis_digest": ("caller_expectation_independently_verified", "current_decision_basis"),
    "expected_head_ref": ("caller_expectation_independently_verified", "current_head"),
    "expected_head_revision": ("caller_expectation_independently_verified", "current_head"),
    "expected_head_digest": ("caller_expectation_independently_verified", "current_head"),
}
assert list(PRIMITIVE_SOURCES) == PRIMITIVE_NAMES

BASIS = {
    "name": "guarded_family_preassignment_basis_v1",
    "logical_schema": False, "durable_authority": False, "public_dto": False,
    "profile_source": "command_relation.schema_id",
    "ordered_primitive_fields": [
        {"name": name, "type": _primitive_type(name),
         "origin_class": PRIMITIVE_SOURCES[name][0],
         "source_node": PRIMITIVE_SOURCES[name][1]}
        for name in PRIMITIVE_NAMES
    ],
    "serialization": "ordered_name_value_pairs_utf8_json_ensure_ascii_false_allow_nan_false_compact",
    "excluded_sources": ["command_digest", "preassigned_sibling", "authoritative_branch",
                         "result", "receipt", "transaction_timestamp", "terminal_outcome",
                         "postcommit_head", "raw_external_credential", "raw_external_attestation"],
}
SIBLING_SPECS = [
    ("preassigned_decision_ref", "preassigned_decision_ref",
     "governed-execution.nwp-rw0-c2-preassigned-decision-ref.v1",
     "400960b261c148544c0d0c29d2c65bf7b6b85b679d18c52d2ab4ec793198f208"),
    ("preassigned_resulting_program_version_ref", "preassigned_version_ref",
     "governed-execution.nwp-rw0-c2-preassigned-resulting-version-ref.v1",
     "1d930498247537c7934366c77a35a3a7c0614402ceefa87b49d713143220f237"),
    ("preassigned_guarded_family_relation_ref", "preassigned_relation_ref",
     "governed-execution.nwp-rw0-c2-preassigned-guarded-relation-ref.v1",
     "0fbf19ecc76ca0a2c6ffba5c8c4b07157cdb1645a722b0df130ed5c30b832f77"),
    ("preassigned_guarded_progression_result_ref", "preassigned_guarded_result_ref",
     "governed-execution.nwp-rw0-c2-preassigned-guarded-result-ref.v1",
     "28719afd5182e5a76ea2d17502d70b62cc2e1817f4b82e460d8a1f2225700254"),
    ("deterministic_family_route", "family_route",
     "governed-execution.nwp-rw0-c2-deterministic-family-route.v1",
     "4f13fe4404b53c9d521eac90a64d87352d1077e307be5a33a8dd9c27c33079b9"),
    ("preassigned_acceptance_fact_ref", "preassigned_acceptance_fact_ref",
     PROSPECTIVE_DOMAIN,
     "e45e55113d63769b1a4a157aa5a0d8a1621516ba5b81155535f1116af66e8f17"),
]
SIBLINGS = [
    {"name": name, "command_field": field, "domain": domain,
     "input": "guarded_family_preassignment_basis_v1",
     "output_grammar": "lowercase_sha256_hex_64", "fixed_vector": vector}
    for name, field, domain, vector in SIBLING_SPECS
]
ADMISSION_BINDING = {
    "verified_act_fields": EXPECTED_SCHEMAS[0][4],
    "immutable_fact_fields": EXPECTED_SCHEMAS[1][4],
    "command_equalities": ["lineage_ref", "scope_ref", "admission_fact_ref",
                           "admission_fact_digest", "admission_act_ref",
                           "admission_act_digest", "guard_profile", "applicability"],
    "must_validate_before_branch": True, "command_may_admit_or_select_scope": False,
}
RELATION_FACT_FIELDS = {
    "fields": ["acceptance_fact_ref", "acceptance_fact_digest"],
    "acceptance": {"ref": "reserved_command_preassigned_acceptance_fact_ref",
                   "digest": "verified_actual_immutable_fact_digest",
                   "fact_count": 1, "receipt_role_count": 1},
    "nonaccept": {"ref": None, "digest": None, "fact_count": 0,
                  "receipt_role_count": 0, "reserved_ref_in_command_and_selector": True,
                  "reserved_route_required": True, "null_proves_unclaimed": False,
                  "occupied_reserved_identity": "collision_or_unresolved"},
}

ORIGIN_CLASSES = [
    "externally_verified", "current_owner_durable_current_value",
    "caller_expectation_independently_verified", "contract_literal",
    "primitive_derivation_transcript", "sibling_domain_separated_derivation",
    "post_preassignment_command_digest", "authoritative_branch_output",
    "post_branch_canonical_value_digest", "receipt_graph", "replay_recovery_projection",
    "future_transaction_owner_prerequisite", "validated_prebranch_admission_posture",
    "postread_verified_input",
]
FRESH_LIFECYCLE = "fresh_write_construction_v1"
REPLAY_LIFECYCLE = "exact_replay_readback_v1"
RECOVERY_LIFECYCLE = "uncertain_commit_recovery_v1"
LIFECYCLE_NAMES = (FRESH_LIFECYCLE, REPLAY_LIFECYCLE, RECOVERY_LIFECYCLE)
PRIVATE_VOCABULARY_ID = "rw0-c2-private-value-contract-v1"
OWNER_ASSERTION_PROFILE_ID = "rw0-c2-private-owner-assertions-v1"
OWNER_ASSERTION_DIGEST_DOMAIN = b"governed-execution.nwp-rw0-c2-private-owner-assertions.v1"
OWNER_ASSERTION_PROFILE_DIGEST = "93b76bb45f90e44c999366462adc466db21970bdfbeae51246cba616ba19edb0"
OWNER_FIRST_CLAUSE_DIGEST = "a1b7dc2ec2c5576f68d47a6da3046513410d8f95cc277bbb51920d1942e14d7a"


def _expected_dependency_registry():
    rows = []
    branches = list(BRANCHES)
    routes = ["recovery_route_observation:" + route["role"] for route in ROUTES]

    def add(node, stage, origin_class, dependencies, *, on="all_branches", conditional=None):
        rows.append({"node": node, "stage": stage, "origin_class": origin_class,
                     "materializes_on": on, "common_dependencies": dependencies,
                     "dependencies_by_branch": conditional or {},
                     "prohibited_dependencies": [], "lifecycle_memberships": []})

    for node, stage, origin, deps in (
        ("receipt_profile_id_literal", 0, "contract_literal", []),
        ("family_relation_schema_literal", 0, "contract_literal", []),
        ("verified_admission_act", 0, "externally_verified", []),
        ("verified_scope_admission_fact", 1, "current_owner_durable_current_value", ["verified_admission_act"]),
        ("verified_continuity_basis", 0, "externally_verified", []),
        ("verified_sole_active_basis", 0, "externally_verified", []),
        ("verified_mutation_identity", 0, "caller_expectation_independently_verified", []),
        ("current_program_identity", 0, "current_owner_durable_current_value", []),
        ("current_decision_basis", 0, "current_owner_durable_current_value", []),
        ("current_head", 0, "current_owner_durable_current_value", []),
        ("fresh_current_continuity_posture", 0, "externally_verified", []),
        ("fresh_current_sole_active_posture", 0, "externally_verified", []),
        ("local_writer_session_fence", 0, "future_transaction_owner_prerequisite", []),
        ("fresh_external_posture", 1, "externally_verified",
         ["fresh_current_continuity_posture", "fresh_current_sole_active_posture"]),
    ):
        add(node, stage, origin, deps)
    primitives = ["primitive:" + name for name in PRIMITIVE_NAMES]
    for name in PRIMITIVE_NAMES:
        origin, source = PRIMITIVE_SOURCES[name]
        add("primitive:" + name, 2, origin, [] if source == "contract_literal" else [source])
    add("closed_command_relation_value", 3, "primitive_derivation_transcript",
        primitives + ["verified_admission_act", "verified_scope_admission_fact"])
    add("guarded_family_preassignment_basis_v1", 4, "primitive_derivation_transcript",
        ["closed_command_relation_value"] + primitives)
    siblings = ["sibling:" + name for name, *_ in SIBLING_SPECS]
    for name in siblings:
        add(name, 5, "sibling_domain_separated_derivation", ["guarded_family_preassignment_basis_v1"])
    add("command_digest", 6, "post_preassignment_command_digest",
        ["closed_command_relation_value"] + primitives + siblings)
    add("guarded_result_identity_expectation", 6, "post_preassignment_command_digest", [siblings[3]])
    add("validated_admission_command_and_current_posture", 7,
        "validated_prebranch_admission_posture",
        ["verified_admission_act", "verified_scope_admission_fact", "closed_command_relation_value",
         "command_digest"] + siblings + ["fresh_current_continuity_posture",
         "fresh_current_sole_active_posture", "local_writer_session_fence"])
    add("authoritative_branch", 8, "authoritative_branch_output",
        ["validated_admission_command_and_current_posture", "current_decision_basis", "current_head"])
    add("recovery_selector_value", 6, "replay_recovery_projection",
        ["command_digest"] + siblings +
        ["primitive:lineage_ref", "primitive:scope_ref", "primitive:admission_fact_ref",
         "primitive:admission_fact_digest", "primitive:mutation_ref"])
    add("transaction_timestamp", 9, "post_branch_canonical_value_digest", ["authoritative_branch"])
    add("recovery_selector_digest", 7, "replay_recovery_projection", ["recovery_selector_value"])
    for node in routes:
        add(node, 8, "replay_recovery_projection", ["recovery_selector_value", "fresh_external_posture"])
    add("complete_family_recovery_observation_set_v1", 9, "replay_recovery_projection",
        ["recovery_selector_digest", "fresh_external_posture"] + routes)
    post = [
        ("canonical_decision_value", 10, ["authoritative_branch", "command_digest", siblings[0], "transaction_timestamp"]),
        ("canonical_decision_digest", 11, ["canonical_decision_value"]),
        ("canonical_version_value", 12, ["canonical_decision_digest", siblings[1], "transaction_timestamp"]),
        ("canonical_version_digest", 13, ["canonical_version_value"]),
        ("historical_head_postimage_value", 14, ["canonical_version_digest", "current_head", "transaction_timestamp"]),
        ("historical_head_postimage_digest", 15, ["historical_head_postimage_value"]),
        ("generic_result_projection_value", 16, ["canonical_decision_digest", "canonical_version_digest", "historical_head_postimage_digest"]),
        ("generic_result_projection_digest", 17, ["generic_result_projection_value"]),
        ("acceptance_fact_value", 18, ["authoritative_branch", "command_digest", "canonical_decision_value", "canonical_decision_digest", "canonical_version_value", "canonical_version_digest", "historical_head_postimage_value", "historical_head_postimage_digest", "transaction_timestamp", siblings[5], siblings[4]]),
        ("acceptance_fact_digest", 19, ["acceptance_fact_value"]),
    ]
    for node, stage, deps in post:
        add(node, stage, "post_branch_canonical_value_digest", deps,
            on=["candidate_acceptance"] if node.startswith("acceptance_fact_") else "all_branches")
    relation_deps = ["authoritative_branch", "command_digest", "historical_head_postimage_value",
        "historical_head_postimage_digest", "canonical_decision_value", "canonical_decision_digest",
        "canonical_version_value", "canonical_version_digest", "generic_result_projection_value",
        "generic_result_projection_digest", "guarded_result_identity_expectation", siblings[2], siblings[4],
        "verified_scope_admission_fact", "verified_admission_act", "verified_continuity_basis",
        "verified_sole_active_basis", "family_relation_schema_literal",
        "primitive:lineage_ref", "primitive:scope_ref"]
    add("family_relation_value", 20, "post_branch_canonical_value_digest", relation_deps,
        conditional={"candidate_acceptance": ["acceptance_fact_value", "acceptance_fact_digest"]})
    add("family_relation_digest", 21, "post_branch_canonical_value_digest", ["family_relation_value"])
    add("guarded_result_value", 22, "post_branch_canonical_value_digest",
        ["family_relation_digest", "generic_result_projection_digest", siblings[3],
         "authoritative_branch", "receipt_profile_id_literal"])
    add("guarded_result_digest", 23, "post_branch_canonical_value_digest", ["guarded_result_value"])
    add("generic_receipt_preimage_value", 24, "receipt_graph",
        ["command_digest", "canonical_decision_value", "canonical_decision_digest",
         "canonical_version_value", "canonical_version_digest", "generic_result_projection_value",
         "generic_result_projection_digest", "transaction_timestamp"])
    add("generic_receipt_graph_entries_value", 24, "receipt_graph",
        ["verified_admission_act", "verified_scope_admission_fact", "verified_continuity_basis",
         "verified_sole_active_basis", "canonical_decision_value", "canonical_decision_digest",
         "canonical_version_value", "canonical_version_digest", "historical_head_postimage_value",
         "historical_head_postimage_digest", "generic_result_projection_value",
         "generic_result_projection_digest", "family_relation_value", "family_relation_digest",
         "guarded_result_value", "guarded_result_digest"],
        conditional={"candidate_acceptance": ["acceptance_fact_value", "acceptance_fact_digest"]})
    add("generic_receipt_graph_identity_value", 25, "receipt_graph",
        ["generic_receipt_preimage_value", "generic_receipt_graph_entries_value"])
    add("generic_receipt_graph_digest", 26, "receipt_graph", ["generic_receipt_graph_identity_value"])
    add("generic_receipt_row_value", 27, "receipt_graph",
        ["generic_receipt_preimage_value", "generic_receipt_graph_digest"])
    add("replay_canonical_command_digest_observation", 0, "postread_verified_input", [])
    add("replay_receipt_first_mutation_lookup", 1, "postread_verified_input",
        ["replay_canonical_command_digest_observation"])
    add("replay_exact_persisted_family", 2, "postread_verified_input",
        ["replay_receipt_first_mutation_lookup"])
    add("replay_projection", 28, "replay_recovery_projection",
        ["replay_canonical_command_digest_observation", "replay_receipt_first_mutation_lookup",
         "replay_exact_persisted_family", "fresh_external_posture"])
    add("recovery_projection", 28, "replay_recovery_projection",
        ["recovery_selector_value", "recovery_selector_digest",
         "complete_family_recovery_observation_set_v1", "fresh_external_posture"])
    high_risk = ["command_digest", "authoritative_branch", "transaction_timestamp",
                 "acceptance_fact_digest", "family_relation_digest", "guarded_result_digest",
                 "generic_receipt_graph_digest", "generic_receipt_row_value", "recovery_projection",
                 "terminal_outcome", "postcommit_head"] + siblings
    added_nodes = {"fresh_current_continuity_posture", "fresh_current_sole_active_posture",
                   "local_writer_session_fence", "closed_command_relation_value",
                   "validated_admission_command_and_current_posture",
                   "replay_canonical_command_digest_observation",
                   "replay_receipt_first_mutation_lookup", "replay_exact_persisted_family"}
    for row in rows:
        if ((row["stage"] <= 5 and row["node"] not in added_nodes) or
                row["node"] in {"command_digest", "guarded_result_identity_expectation"}):
            row["prohibited_dependencies"] = [name for name in high_risk
                                              if name != row["node"] and
                                              name not in row["common_dependencies"]]
        if row["node"] in {"family_relation_value", "generic_receipt_graph_entries_value"}:
            row["prohibited_dependencies"] = ["acceptance_fact_value", "acceptance_fact_digest"]
    by_name = {row["node"]: row for row in rows}
    fresh_excluded = {"recovery_selector_value", "recovery_selector_digest",
                      "complete_family_recovery_observation_set_v1", "replay_projection",
                      "recovery_projection", "replay_canonical_command_digest_observation",
                      "replay_receipt_first_mutation_lookup", "replay_exact_persisted_family",
                      *routes}
    for row in rows:
        if row["node"] not in fresh_excluded:
            row["lifecycle_memberships"].append(FRESH_LIFECYCLE)

    def mark(name, lifecycle):
        row = by_name[name]
        if lifecycle in row["lifecycle_memberships"]:
            return
        row["lifecycle_memberships"].append(lifecycle)
        for dependency in row["common_dependencies"]:
            mark(dependency, lifecycle)
        for dependencies in row["dependencies_by_branch"].values():
            for dependency in dependencies:
                mark(dependency, lifecycle)

    mark("replay_projection", REPLAY_LIFECYCLE)
    mark("recovery_projection", RECOVERY_LIFECYCLE)
    for row in rows:
        row["lifecycle_memberships"].sort(key=LIFECYCLE_NAMES.index)

    def inventory(lifecycle, branch=None):
        active = [row for row in rows if lifecycle in row["lifecycle_memberships"] and
                  (branch is None or row["materializes_on"] == "all_branches" or
                   branch in row["materializes_on"])]
        names = {row["node"] for row in active}
        edges = [(dependency, row["node"]) for row in active for dependency in
                 row["common_dependencies"] + (row["dependencies_by_branch"].get(branch, [])
                 if branch else []) if dependency in names]
        return {"nodes": [row["node"] for row in active], "node_count": len(active),
                "edge_count": len(edges)}

    expanded = {}
    for branch in branches:
        branch_inventory = inventory(FRESH_LIFECYCLE, branch)
        expanded[branch] = {"nodes": branch_inventory["node_count"],
                            "edges": branch_inventory["edge_count"]}
    return {"private_contract_vocabulary_id": PRIVATE_VOCABULARY_ID,
            "origin_classes": ORIGIN_CLASSES, "nodes": rows,
            "conditional_nodes": ["acceptance_fact_value", "acceptance_fact_digest"],
            "dependency_rule": "exact_branch_expansion_no_implicit_aggregate_inputs",
            "stage_rule": "fresh_write_dependencies_strictly_increase_only",
            "topological_rule": "complete_unique_topological_sort_per_lifecycle_partition",
            "node_count": len(rows),
            "common_edge_count": sum(len(row["common_dependencies"]) for row in rows),
            "expanded_counts": expanded,
            "recovery_observation_nodes": routes,
            "relation_field_dependencies": RELATION_FIELD_DEPENDENCIES,
            "lifecycle_partitions": {
                FRESH_LIFECYCLE: {"phase": "fresh_write_construction",
                    "branch_dags": {branch: inventory(FRESH_LIFECYCLE, branch) for branch in branches}},
                REPLAY_LIFECYCLE: {"phase": "postread_exact_replay",
                    "dag": inventory(REPLAY_LIFECYCLE)},
                RECOVERY_LIFECYCLE: {"phase": "postread_uncertain_commit_recovery",
                    "dag": inventory(RECOVERY_LIFECYCLE)},
            }}


RELATION_FIELD_DEPENDENCIES = {
    "schema_id": "family_relation_schema_literal", "relation_ref": "sibling:preassigned_guarded_family_relation_ref",
    "branch": "authoritative_branch", "lineage_ref": "primitive:lineage_ref",
    "scope_ref": "primitive:scope_ref", "command_digest": "command_digest",
    "admission_act_ref": "verified_admission_act",
    "admission_act_digest": "verified_admission_act", "admission_fact_ref": "verified_scope_admission_fact",
    "admission_fact_digest": "verified_scope_admission_fact", "continuity_basis_ref": "verified_continuity_basis",
    "continuity_basis_digest": "verified_continuity_basis", "sole_active_basis_ref": "verified_sole_active_basis",
    "sole_active_basis_digest": "verified_sole_active_basis", "decision_ref": "canonical_decision_value",
    "decision_digest": "canonical_decision_digest", "version_ref": "canonical_version_value",
    "version_digest": "canonical_version_digest", "historical_head_ref": "historical_head_postimage_value",
    "historical_head_revision": "historical_head_postimage_value",
    "historical_head_digest": "historical_head_postimage_digest",
    "historical_head_postimage": "historical_head_postimage_value",
    "acceptance_fact_ref": "acceptance_fact_value", "acceptance_fact_digest": "acceptance_fact_digest",
    "generic_result_projection_digest": "generic_result_projection_digest",
    "family_route": "sibling:deterministic_family_route",
}


EXPECTED_DEPENDENCY_REGISTRY = _expected_dependency_registry()

RECOVERY_OBSERVATION_SET = {
    "private_contract_vocabulary_id": PRIVATE_VOCABULARY_ID,
    "name": "complete_family_recovery_observation_set_v1",
    "kind": "non_durable_postread_derivation_not_logical_schema",
    "owner": "decision_owner_existing_whole_family_recovery",
    "posture_fields": ["lineage_ref", "scope_ref", "fresh_current_continuity",
                       "fresh_current_sole_active"],
    "posture_value_fields": ["status", "posture_ref", "posture_digest"],
    "posture_statuses": ["positive", "missing", "stale", "unknown", "conflicting", "negative"],
    "route_observation_fields": ["route_role", "route_key", "status", "read_attempted",
                                 "readable", "evidence_ref", "evidence_digest",
                                 "total_absence_proved"],
    "route_statuses": ["unchecked", "exact_complete_family", "absent", "partial",
                       "duplicate", "foreign", "malformed", "unreadable",
                       "route_identity_conflict", "competing_complete_scope_winner"],
    "route_status_rules": {
        status: {"read_attempted": status != "unchecked",
                 "readable": status not in {"unchecked", "unreadable"},
                 "evidence_ref": ("null" if status in {"unchecked", "unreadable", "absent"}
                                  else "nonempty_string"),
                 "evidence_digest": ("null" if status in {"unchecked", "unreadable", "absent"}
                                     else "lowercase_sha256_hex"),
                 "total_absence_proved": status == "absent"}
        for status in ("unchecked", "exact_complete_family", "absent", "partial",
                       "duplicate", "foreign", "malformed", "unreadable",
                       "route_identity_conflict", "competing_complete_scope_winner")},
    "route_roles": ["mutation_receipt_route", "decision_identity_route",
                    "resulting_version_identity_route", "acceptance_fact_identity_route",
                    "guarded_family_relation_identity_route", "guarded_progression_result_identity_route",
                    "deterministic_family_route", "admitted_scope_winner_route"],
    "route_order_exact": True,
    "total_absence_rule": "all_eight_absent_and_proved_with_both_positive_fresh_postures",
    "complete_rule": "exact_original_family_every_required_route_and_member_command_binding_with_positive_fresh_posture",
    "unresolved_rule": "unchecked_partial_duplicate_foreign_malformed_unreadable_identity_conflict_mixed_missing_duplicate_or_insufficient_posture",
    "competing_winner_rule": "scope_winner_route_only_with_all_other_routes_absent_proves_original_noncommit_without_fresh_acceptance_eligibility",
    "no_local_absence_outside_observations": True,
    "selector_phase": "precommit_query_plan", "observation_phase": "postread_classification_basis",
    "new_receipt_or_recovery_owner": False,
    "result_fields": ["classification", "lineage_ref", "scope_ref",
                      "current_continuity_posture_ref", "current_continuity_posture_digest",
                      "current_sole_active_posture_ref", "current_sole_active_posture_digest"],
    "result_posture_binding": "exact_copy_of_validated_current_recovery_posture_pairs",
    "evidence_digest_domain": "governed-execution.nwp-rw0-c2-route-observation-evidence.v1",
    "evidence_digest_derivation": "sha256(domain_utf8+nul+evidence_ref_utf8)",
}
FIXED_RECOVERY_STATUSES = ("unchecked", "exact_complete_family", "absent", "partial",
                           "duplicate", "foreign", "malformed", "unreadable",
                           "route_identity_conflict", "competing_complete_scope_winner")
RECOVERY_RESULT_FIELDS = ("classification", "lineage_ref", "scope_ref",
                          "current_continuity_posture_ref", "current_continuity_posture_digest",
                          "current_sole_active_posture_ref", "current_sole_active_posture_digest")
CURRENT_RECOVERY_POSTURE_FIELDS = (
    "lineage_ref", "scope_ref", "current_continuity_posture_ref",
    "current_continuity_posture_digest", "continuity_state",
    "current_sole_active_posture_ref", "current_sole_active_posture_digest",
    "sole_active_state")
CONTINUITY_STATES = ("positively_established", "missing", "stale", "unknown",
                     "conflicting", "negative")
SOLE_ACTIVE_STATES = ("exactly_one_active_authority", "missing", "stale", "unknown",
                      "conflicting", "not_exactly_one")
CURRENT_RECOVERY_POSTURE = {
    "name": "validated_current_recovery_posture_v1",
    "kind": "transient_private_external_current_evidence_validation_not_logical_schema",
    "fields": list(CURRENT_RECOVERY_POSTURE_FIELDS),
    "continuity_states": list(CONTINUITY_STATES),
    "sole_active_states": list(SOLE_ACTIVE_STATES),
    "positive_continuity_state": "positively_established",
    "positive_sole_active_state": "exactly_one_active_authority",
    "binding": "exact_selector_lineage_scope_and_fresh_observation_coordinates_and_states",
    "historical_basis_allowed": False,
}
RECOVERY_PROJECTION_SIGNATURE = {
    "parameters": ["observed_set", "canonical_binding", "validated_current_posture"],
    "canonical_binding_fields": ["command", "branch", "family", "selector"],
    "unknown_keys": "reject", "classification_input": False,
    "classifier": "_classify_complete_family_recovery",
    "classification_source": "classifier_return",
}
PRIVATE_VOCABULARY = {
    "private_contract_vocabulary_id": PRIVATE_VOCABULARY_ID,
    "lifecycle_ids": list(LIFECYCLE_NAMES),
    "route_observation_statuses": list(FIXED_RECOVERY_STATUSES),
    "recovery_result_schema_id": PREFIX + "complete-family-recovery-result.v1",
    "recovery_result_payload_fields": list(RECOVERY_RESULT_FIELDS),
}


def _validate_preassignment_basis(value):
    _exact(value, BASIS, "preassignment_basis")


def _validate_siblings(value):
    _exact(value, SIBLINGS, "preassignment_siblings")


def _validate_dependency_registry(value):
    expected = EXPECTED_DEPENDENCY_REGISTRY
    if type(value) is not dict or set(value) != set(expected):
        raise ContractViolation("dependency_registry_shape")
    _exact(value["origin_classes"], ORIGIN_CLASSES, "dependency_origin_class_inventory")
    nodes = value["nodes"]
    if type(nodes) is not list or len(nodes) != len(expected["nodes"]):
        raise ContractViolation("dependency_inventory")
    names = [row.get("node") if type(row) is dict else None for row in nodes]
    if len(set(names)) != len(names) or set(names) != {row["node"] for row in expected["nodes"]}:
        raise ContractViolation("dependency_inventory")
    by_name = {row["node"]: row for row in nodes}
    expected_by_name = {row["node"]: row for row in expected["nodes"]}
    for name, row in by_name.items():
        if set(row) != {"node", "stage", "origin_class", "materializes_on",
                        "common_dependencies", "dependencies_by_branch",
                        "prohibited_dependencies", "lifecycle_memberships"}:
            raise ContractViolation("dependency_node_shape")
        if row["origin_class"] not in ORIGIN_CLASSES:
            raise ContractViolation("dependency_origin_class")
        if (type(row["stage"]) is not int or type(row["common_dependencies"]) is not list
                or type(row["dependencies_by_branch"]) is not dict
                or type(row["prohibited_dependencies"]) is not list
                or type(row["lifecycle_memberships"]) is not list
                or not row["lifecycle_memberships"]
                or len(set(row["lifecycle_memberships"])) != len(row["lifecycle_memberships"])
                or any(life not in LIFECYCLE_NAMES for life in row["lifecycle_memberships"])):
            raise ContractViolation("dependency_node_shape")
        if row["materializes_on"] != "all_branches" and (type(row["materializes_on"]) is not list
                or not row["materializes_on"] or any(b not in BRANCHES for b in row["materializes_on"])):
            raise ContractViolation("dependency_materialization")
        if any(b not in BRANCHES for b in row["dependencies_by_branch"]):
            raise ContractViolation("dependency_branch_inventory")
        if name in {"family_relation_value", "generic_receipt_graph_entries_value"} and any(
                dep.startswith("acceptance_fact_") for dep in row["common_dependencies"]):
            raise ContractViolation("dependency_hidden_optional")
        expected_row = expected_by_name[name]
        if row["lifecycle_memberships"] != expected_row["lifecycle_memberships"]:
            raise ContractViolation("dependency_lifecycle_membership")
    def sort_partition(lifecycle, branch=None):
        active = {name: row for name, row in by_name.items()
                  if lifecycle in row["lifecycle_memberships"] and
                  (branch is None or row["materializes_on"] == "all_branches"
                   or branch in row["materializes_on"])}
        indegree = {name: 0 for name in active}
        forward = {name: [] for name in active}
        edge_count = 0
        for name, row in active.items():
            dependencies = row["common_dependencies"] + (
                row["dependencies_by_branch"].get(branch, []) if branch else [])
            if len(dependencies) != len(set(dependencies)):
                raise ContractViolation("dependency_duplicate_edge")
            for dep in dependencies:
                if dep not in active:
                    raise ContractViolation("dependency_nonmaterialized_edge")
                if dep in row["prohibited_dependencies"] and dep in row["common_dependencies"]:
                    raise ContractViolation("dependency_forbidden_backedge")
                if (lifecycle == FRESH_LIFECYCLE and
                        by_name[dep]["stage"] >= row["stage"]):
                    raise ContractViolation("dependency_stage_or_cycle")
                indegree[name] += 1
                forward[dep].append(name)
                edge_count += 1
        ready = sorted(name for name, degree in indegree.items() if degree == 0)
        order = []
        while ready:
            name = ready.pop(0)
            order.append(name)
            for target in forward[name]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    ready.append(target)
            ready.sort()
        if len(order) != len(active):
            raise ContractViolation("dependency_stage_or_cycle")
        return order, edge_count
    fresh = {}
    fresh_counts = {}
    for branch in BRANCHES:
        order, edges = sort_partition(FRESH_LIFECYCLE, branch)
        fresh[branch] = order
        fresh_counts[branch] = {"nodes": len(order), "edges": edges}
    replay_order, replay_edges = sort_partition(REPLAY_LIFECYCLE)
    recovery_order, recovery_edges = sort_partition(RECOVERY_LIFECYCLE)
    for name, row in by_name.items():
        # A post-read-only stage is not an execution order against fresh write.
        comparable = dict(row)
        expected_row = expected_by_name[name]
        if FRESH_LIFECYCLE not in row["lifecycle_memberships"]:
            comparable["stage"] = expected_row["stage"]
        if comparable != expected_row:
            raise ContractViolation("dependency_exact_edges")
    for branch in BRANCHES:
        _exact(fresh_counts[branch], expected["expanded_counts"][branch],
               "dependency_fresh_counts")
        _exact(value["lifecycle_partitions"][FRESH_LIFECYCLE]["branch_dags"][branch],
               expected["lifecycle_partitions"][FRESH_LIFECYCLE]["branch_dags"][branch],
               "dependency_fresh_partition")
    for life, order, edges in ((REPLAY_LIFECYCLE, replay_order, replay_edges),
                               (RECOVERY_LIFECYCLE, recovery_order, recovery_edges)):
        _exact({"node_count": len(order), "edge_count": edges},
               {"node_count": expected["lifecycle_partitions"][life]["dag"]["node_count"],
                "edge_count": expected["lifecycle_partitions"][life]["dag"]["edge_count"]},
               "dependency_postread_counts")
    # Exact rows supply the fixed edge inventory; the partition lists fix
    # membership and prohibit presenting a combined execution sequence.
    remaining = dict(value)
    remaining.pop("nodes")
    _exact(remaining, {key: item for key, item in expected.items() if key != "nodes"},
           "dependency_exact_edges")
    if ("validated_admission_command_and_current_posture" not in
            set(fresh["candidate_acceptance"])):
        raise ContractViolation("dependency_prebranch_admission_posture")
    for branch, order in fresh.items():
        by_order = set()
        for name in order:
            if name == "authoritative_branch" and (
                    "validated_admission_command_and_current_posture" not in by_order):
                raise ContractViolation("dependency_prebranch_admission_posture")
            by_order.add(name)
        if any(name.startswith("recovery_route_observation:") or
               name in {"replay_projection", "recovery_projection"}
               for name in order):
            raise ContractViolation("dependency_cross_lifecycle")
    return fresh


def _validate(p):
    _exact(set(p), {"contract_id", "status", "owners", "canonicalization", "schemas", "authority", "preassignment_basis", "preassignment_siblings", "dependency_registry", "command_digest", "command_digest_v2", "prospective_fact_identity", "admission_binding", "family_relation_fact_fields", "graph", "receipt_graph_profile_definition", "branches", "collision_route_templates", "selector", "replay", "recovery", "recovery_observation_set", "validated_current_recovery_posture", "recovery_projection_signature", "owner_assertion_profile", "normative_clause_registry", "private_contract_vocabulary", "v1", "b1", "boundaries"}, "closed_inventory")
    _exact([p["contract_id"], p["status"], p["owners"]],
           ["rw0-c2-private-value-versioning-v1", "accepted_target_not_implemented", OWNERS], "owner_status")
    _exact(p["canonicalization"], CANONICALIZATION, "canonicalization")
    _exact(p["schemas"], EXPECTED_SCHEMAS, "logical_schemas")
    _exact(p["private_contract_vocabulary"], PRIVATE_VOCABULARY,
           "private_contract_vocabulary")
    _exact(p["authority"], AUTHORITY, "authority_matrix")
    _validate_preassignment_basis(p["preassignment_basis"])
    _validate_siblings(p["preassignment_siblings"])
    _validate_dependency_registry(p["dependency_registry"])
    _exact(p["command_digest"], COMMAND_DIGEST, "command_digest")
    _exact(p["command_digest_v2"], COMMAND_DIGEST_V2, "command_digest_v2")
    _exact(p["prospective_fact_identity"], PROSPECTIVE, "prospective_fact_identity")
    _exact(p["graph"], GRAPH, "receipt_graph")
    _exact(p["receipt_graph_profile_definition"], EXPECTED_STATIC_RECEIPT_PROFILE,
           "static_receipt_profile")
    _exact(p["branches"], BRANCHES, "branch_profile")
    _exact(p["collision_route_templates"], ROUTES, "collision_route_templates")
    _exact(p["selector"], SELECTOR, "recovery_selector")
    _exact(p["admission_binding"], ADMISSION_BINDING, "admission_binding")
    _exact(p["family_relation_fact_fields"], RELATION_FACT_FIELDS, "relation_fact_fields")
    _exact(p["recovery_observation_set"], RECOVERY_OBSERVATION_SET,
           "recovery_observation_set")
    _exact(p["validated_current_recovery_posture"], CURRENT_RECOVERY_POSTURE,
           "validated_current_recovery_posture")
    _exact(p["recovery_projection_signature"], RECOVERY_PROJECTION_SIGNATURE,
           "recovery_projection_signature")
    _validate_owner_assertion_profile(p)
    _exact(p["replay"], REPLAY, "replay_value")
    _exact(p["recovery"], RECOVERY, "recovery_value")
    _exact(p["v1"], V1, "v1_preservation")
    _exact(p["b1"], B1, "b1_compatibility")
    _exact(p["boundaries"], BOUNDARIES, "authority_boundaries")


def test_owner_prose_and_closed_private_profile():
    text, p = _document()
    _validate(p)
    assert text.startswith("# RW0-C2 Private Value Versioning and Receipt-Graph Profile\n")
    compact = " ".join(text.split())
    for sentence in (
        "none of the private values or profiles defined here is implemented",
        "The guarded decision writer reads a previously provisioned admission fact",
        "Positive lineage continuity and one active authority remain fresh external/current evidence",
        "The derived `candidate_acceptance` branch has one immutable acceptance fact",
        "The receipt is the root and is not an entry in its own graph.",
        "A matching graph digest alone proves none of those propositions.",
        "The guarded decision writer has no B1-pair read or consumption path.",
        "Later ES routing has no direct-local-allowance replenishment effect.",
    ):
        assert sentence in compact
    for key in ("guard", "decision", "composition"):
        assert p["owners"][key] in text


PROSE_CLAUSES = {
    "historical_basis_non_authority": "Retained historical continuity and sole-active bases never become current standing permission.",
    "current_external_posture": "Protected replay and recovery require positive current external continuity and sole-active posture.",
    "mandatory_prospective_fact_coordinate": "Every guarded command requires a non-null Coordinator-derived prospective acceptance-fact ref before branch reduction.",
    "branch_nonselection": "Supplying or withholding the prospective fact coordinate cannot force or veto the authoritative branch.",
    "nonaccept_fact_collision": "Every nonaccept branch forbids fact membership while retaining and collision-probing the reserved fact identity.",
    "closed_collision_routes": "Every branch requires the exact ordered eight-route collision inventory with no omissions or extensions.",
    "total_absence_currentness": "Local absence without positive current continuity and sole-active posture is unresolved, never definitely_not_committed.",
    "replay_original_fact_timestamp": "Exact replay returns the original fact if present and the original transaction timestamp; it creates neither a new fact nor a new timestamp.",
    "admitted_scope_only": "A command relation must match an already admitted lineage and scope and cannot select an unadmitted scope.",
    "separate_admission_decision_writers": "The guarded decision writer cannot provision or repair an admission fact; only the separate admission provisioner may record it.",
    "single_result_receipt_replay_recovery": "The guarded family retains one logical result, one receipt, one replay owner, and one recovery classifier under the decision owner.",
    "terminal_nonreplenishment": "A terminal outcome cannot replenish acceptance.",
    "es_nonreplenishment": "ES routing cannot replenish the direct-local allowance.",
}

# These references are fixed independently of the private machine block. The
# owner value is read from the unchanged owner document at verification time.
OWNER_DOCS = {
    "guard": (".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md",
              "RW0_C2_BOOTSTRAP_GUARD_MACHINE_BEGIN"),
    "decision": (".docs/rw0-c2-durable-progression-decision-semantic-contract.md",
                 "RW0_C2_DURABLE_DECISION_FINITE_ORACLE_BEGIN"),
}
# Fixed pointer assertions are authored in the verifier, separately from the
# private machine rows. No action or polarity is derived from a private map.
OWNER_REFERENCE_RULES = {
    "historical_basis_non_authority": ("guard", (
        ("/scope/continuity", "equals", "positively_established"),
        ("/family/replay_historical_head_freshness", "equals", False)),
        "historical_basis_not_current_permission"),
    "current_external_posture": ("guard", (
        ("/scope/continuity", "equals", "positively_established"),
        ("/scope/active_authorities", "equals", 1)),
        "fresh_posture_required_for_protected_disclosure"),
    "mandatory_prospective_fact_coordinate": ("guard", (
        ("/relation/every_applicable_command", "equals", True),
        ("/acceptance_roles", "contains", "acceptance_fact_identity")),
        "derived_nonnull_coordinate_required"),
    "branch_nonselection": ("decision", (
        ("/expected_branch/role", "equals", "conflict_assertion_only"),
        ("/model/may_change_branch", "equals", False),
        ("/guard/relation_grants_authority", "equals", False),
        ("/guard/relation_requests_acceptance", "equals", False)),
        "coordinate_cannot_force_or_veto_branch"),
    "nonaccept_fact_collision": ("guard", (
        ("/branch_effects/candidate_repair", "equals", 0),
        ("/taxonomy/fact_identity_collision", "equals",
         "preassigned_identity_or_family_route_collision")),
        "nonaccept_fact_absent_but_collision_probed"),
    "closed_collision_routes": ("guard", (
        ("/taxonomy/family_route_collision", "equals",
         "preassigned_identity_or_family_route_collision"),
        ("/eligibility/acceptance_only", "contains", "exact_command_family_route"),
        ("/relation/recovery_selector_covered", "equals", True)),
        "eight_exact_routes_required"),
    "total_absence_currentness": ("decision", (
        ("/recovery/unresolved_creates_decision", "equals", False),
        ("/recovery/automatic_retry_after_unresolved", "equals", False),
        ("/recovery/readback/ambiguous", "equals", "unresolved")),
        "local_absence_cannot_prove_noncommit"),
    "replay_original_fact_timestamp": ("guard", (
        ("/family/replay_new_fact", "equals", False),
        ("/family/replay_new_timestamp", "equals", False)),
        "replay_creates_no_fact_or_timestamp"),
    "admitted_scope_only": ("guard", (
        ("/relation/authority", "equals", False),
        ("/relation/requests_acceptance", "equals", False),
        ("/relation/roles", "contains", "canonical_scope_expectation"),
        ("/scope/local_absence_is_proof", "equals", False)),
        "command_relation_cannot_admit_scope"),
    "separate_admission_decision_writers": ("guard", (
        ("/authority/admission", "equals", "external_standing_policy"),
        ("/authority/writer", "equals", "future_guarded_decision_transaction"),
        ("/relation/prohibited", "contains", "caller_admission")),
        "decision_writer_cannot_provision_admission"),
    "single_result_receipt_replay_recovery": ("guard", (
        ("/family/separate_receipt", "equals", False),
        ("/family/separate_replay", "equals", False),
        ("/family/separate_recovery", "equals", False),
        ("/authority/replay", "equals", "decision_owner"),
        ("/authority/recovery", "equals", "decision_owner")),
        "one_decision_owned_result_receipt_replay_recovery"),
    "terminal_nonreplenishment": ("guard", (
        ("/terminal/mutates_guard", "equals", False),
        ("/scope/forbidden_changes", "contains", "replenish")),
        "terminal_cannot_replenish_acceptance"),
    "es_nonreplenishment": ("guard", (
        ("/es/replenishes", "equals", False),
        ("/es/new_grant_or_policy_epoch_replenishes", "equals", False),
        ("/es/separately_governed", "equals", True)),
        "es_cannot_replenish_direct_local_allowance"),
}
NORMATIVE_REGISTRY = [
    {"clause_id": clause_id,
     "owner_document": OWNER_DOCS[rule[0]][0],
     "owner_machine_marker": OWNER_DOCS[rule[0]][1],
     "owner_assertions": [
         {"json_pointer": pointer, "comparison": operation, "expected_value": expected}
         for pointer, operation, expected in rule[1]],
     "private_structural_consequence": rule[2]}
    for clause_id, rule in OWNER_REFERENCE_RULES.items()
]
OWNER_ASSERTION_PROFILE = {
    "profile_id": OWNER_ASSERTION_PROFILE_ID,
    "digest_domain": OWNER_ASSERTION_DIGEST_DOMAIN.decode("ascii"),
    "digest_preimage": "ordered_registry_compact_sorted_key_json_utf8_no_newline",
    "digest_rule": "sha256(domain_utf8+nul+preimage_utf8)",
    "registry_digest": OWNER_ASSERTION_PROFILE_DIGEST,
    "clause_count": 13,
    "assertion_count": 37,
    "first_clause_vector": {
        "clause_id": "historical_basis_non_authority",
        "preimage_bytes": 492,
        "digest": OWNER_FIRST_CLAUSE_DIGEST,
    },
}


def _owner_registry_preimage(rows):
    return json.dumps(rows, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _owner_registry_digest(rows):
    return hashlib.sha256(OWNER_ASSERTION_DIGEST_DOMAIN + b"\0" +
                          _owner_registry_preimage(rows)).hexdigest()


def _validate_owner_assertion_profile(profile):
    _exact(profile["owner_assertion_profile"], OWNER_ASSERTION_PROFILE,
           "owner_assertion_profile")
    rows = profile["normative_clause_registry"]
    _exact(rows, NORMATIVE_REGISTRY, "normative_clause_registry")
    if (_owner_registry_digest(rows) != OWNER_ASSERTION_PROFILE_DIGEST or
            len(rows) != 13 or sum(len(row["owner_assertions"]) for row in rows) != 37 or
            len(_owner_registry_preimage(rows[:1])) != 492 or
            _owner_registry_digest(rows[:1]) != OWNER_FIRST_CLAUSE_DIGEST):
        raise ContractViolation("owner_assertion_profile_digest")


# Independently fixed pointer purposes: enclosing object, terminal key,
# comparison, exact built-in value, and allowed private consequence IDs.
OWNER_POINTER_PURPOSES = {
    ("guard", "/scope/continuity"): ("scope", "continuity", "equals", "positively_established",
        ("historical_basis_not_current_permission", "fresh_posture_required_for_protected_disclosure")),
    ("guard", "/family/replay_historical_head_freshness"): ("family", "replay_historical_head_freshness", "equals", False,
        ("historical_basis_not_current_permission",)),
    ("guard", "/scope/active_authorities"): ("scope", "active_authorities", "equals", 1,
        ("fresh_posture_required_for_protected_disclosure",)),
    ("guard", "/relation/every_applicable_command"): ("relation", "every_applicable_command", "equals", True,
        ("derived_nonnull_coordinate_required",)),
    ("guard", "/acceptance_roles"): ("", "acceptance_roles", "contains", "acceptance_fact_identity",
        ("derived_nonnull_coordinate_required",)),
    ("decision", "/expected_branch/role"): ("expected_branch", "role", "equals", "conflict_assertion_only",
        ("coordinate_cannot_force_or_veto_branch",)),
    ("decision", "/model/may_change_branch"): ("model", "may_change_branch", "equals", False,
        ("coordinate_cannot_force_or_veto_branch",)),
    ("decision", "/guard/relation_grants_authority"): ("guard", "relation_grants_authority", "equals", False,
        ("coordinate_cannot_force_or_veto_branch",)),
    ("decision", "/guard/relation_requests_acceptance"): ("guard", "relation_requests_acceptance", "equals", False,
        ("coordinate_cannot_force_or_veto_branch",)),
    ("guard", "/branch_effects/candidate_repair"): ("branch_effects", "candidate_repair", "equals", 0,
        ("nonaccept_fact_absent_but_collision_probed",)),
    ("guard", "/taxonomy/fact_identity_collision"): ("taxonomy", "fact_identity_collision", "equals",
        "preassigned_identity_or_family_route_collision", ("nonaccept_fact_absent_but_collision_probed",)),
    ("guard", "/taxonomy/family_route_collision"): ("taxonomy", "family_route_collision", "equals",
        "preassigned_identity_or_family_route_collision", ("eight_exact_routes_required",)),
    ("guard", "/eligibility/acceptance_only"): ("eligibility", "acceptance_only", "contains",
        "exact_command_family_route", ("eight_exact_routes_required",)),
    ("guard", "/relation/recovery_selector_covered"): ("relation", "recovery_selector_covered", "equals", True,
        ("eight_exact_routes_required",)),
    ("decision", "/recovery/unresolved_creates_decision"): ("recovery", "unresolved_creates_decision", "equals", False,
        ("local_absence_cannot_prove_noncommit",)),
    ("decision", "/recovery/automatic_retry_after_unresolved"): ("recovery", "automatic_retry_after_unresolved", "equals", False,
        ("local_absence_cannot_prove_noncommit",)),
    ("decision", "/recovery/readback/ambiguous"): ("recovery/readback", "ambiguous", "equals", "unresolved",
        ("local_absence_cannot_prove_noncommit",)),
    ("guard", "/family/replay_new_fact"): ("family", "replay_new_fact", "equals", False,
        ("replay_creates_no_fact_or_timestamp",)),
    ("guard", "/family/replay_new_timestamp"): ("family", "replay_new_timestamp", "equals", False,
        ("replay_creates_no_fact_or_timestamp",)),
    ("guard", "/relation/authority"): ("relation", "authority", "equals", False,
        ("command_relation_cannot_admit_scope",)),
    ("guard", "/relation/requests_acceptance"): ("relation", "requests_acceptance", "equals", False,
        ("command_relation_cannot_admit_scope",)),
    ("guard", "/relation/roles"): ("relation", "roles", "contains", "canonical_scope_expectation",
        ("command_relation_cannot_admit_scope",)),
    ("guard", "/scope/local_absence_is_proof"): ("scope", "local_absence_is_proof", "equals", False,
        ("command_relation_cannot_admit_scope",)),
    ("guard", "/authority/admission"): ("authority", "admission", "equals", "external_standing_policy",
        ("decision_writer_cannot_provision_admission",)),
    ("guard", "/authority/writer"): ("authority", "writer", "equals", "future_guarded_decision_transaction",
        ("decision_writer_cannot_provision_admission",)),
    ("guard", "/relation/prohibited"): ("relation", "prohibited", "contains", "caller_admission",
        ("decision_writer_cannot_provision_admission",)),
    ("guard", "/family/separate_receipt"): ("family", "separate_receipt", "equals", False,
        ("one_decision_owned_result_receipt_replay_recovery",)),
    ("guard", "/family/separate_replay"): ("family", "separate_replay", "equals", False,
        ("one_decision_owned_result_receipt_replay_recovery",)),
    ("guard", "/family/separate_recovery"): ("family", "separate_recovery", "equals", False,
        ("one_decision_owned_result_receipt_replay_recovery",)),
    ("guard", "/authority/replay"): ("authority", "replay", "equals", "decision_owner",
        ("one_decision_owned_result_receipt_replay_recovery",)),
    ("guard", "/authority/recovery"): ("authority", "recovery", "equals", "decision_owner",
        ("one_decision_owned_result_receipt_replay_recovery",)),
    ("guard", "/terminal/mutates_guard"): ("terminal", "mutates_guard", "equals", False,
        ("terminal_cannot_replenish_acceptance",)),
    ("guard", "/scope/forbidden_changes"): ("scope", "forbidden_changes", "contains", "replenish",
        ("terminal_cannot_replenish_acceptance",)),
    ("guard", "/es/replenishes"): ("es", "replenishes", "equals", False,
        ("es_cannot_replenish_direct_local_allowance",)),
    ("guard", "/es/new_grant_or_policy_epoch_replenishes"): ("es", "new_grant_or_policy_epoch_replenishes", "equals", False,
        ("es_cannot_replenish_direct_local_allowance",)),
    ("guard", "/es/separately_governed"): ("es", "separately_governed", "equals", True,
        ("es_cannot_replenish_direct_local_allowance",)),
}


def _normative_prefix(clause_id):
    return "NORMATIVE " + clause_id + " [" + OWNER_REFERENCE_RULES[clause_id][2] + "]: "


def _normative_clauses(text):
    section = text.split("## Normative semantic boundaries\n", 1)
    if len(section) != 2:
        raise ContractViolation("normative_clause_section")
    section = section[1].split("\n## ", 1)[0]
    triples = re.findall(r"(?m)^NORMATIVE ([a-z_]+) \[([a-z_]+)\]: (.+)$", section)
    if len(triples) != len({clause_id for clause_id, _, _ in triples}):
        raise ContractViolation("normative_clause_inventory")
    for clause_id, consequence_id, _ in triples:
        if clause_id not in OWNER_REFERENCE_RULES:
            raise ContractViolation("normative_unknown_clause")
        if consequence_id != OWNER_REFERENCE_RULES[clause_id][2]:
            raise ContractViolation("normative_consequence_tag:" + clause_id)
    return {clause_id: statement for clause_id, _, statement in triples}


# Exact token-sequence subjects. A neutral compound following a short alias is
# not the protected subject. Longest phrases win.
PROTECTED_SUBJECT_PHRASES = (
    ("reserved acceptance fact coordinate", "branch_nonselection"),
    ("prospective acceptance coordinate", "branch_nonselection"),
    ("prospective acceptance coordinate", "mandatory_prospective_fact_coordinate"),
    ("prospective fact coordinate", "branch_nonselection"),
    ("prospective fact coordinate", "mandatory_prospective_fact_coordinate"),
    ("current continuity posture", "current_external_posture"),
    ("historical continuity basis", "historical_basis_non_authority"),
    ("historical continuity", "historical_basis_non_authority"),
    ("historical basis", "historical_basis_non_authority"),
    ("local row absence", "total_absence_currentness"),
    ("local absence", "total_absence_currentness"),
    ("replay adapter", "replay_original_fact_timestamp"),
    ("exact replay", "replay_original_fact_timestamp"),
    ("replay", "replay_original_fact_timestamp"),
    ("command relation", "admitted_scope_only"),
    ("nonaccept branch", "nonaccept_fact_collision"),
    ("nonaccept", "nonaccept_fact_collision"),
    ("candidate acceptance branch", "nonaccept_fact_collision"),
    ("terminal outcome", "terminal_nonreplenishment"),
    ("es routing", "es_nonreplenishment"),
    ("execution substrate routing", "es_nonreplenishment"),
    ("decision writer", "separate_admission_decision_writers"),
    ("guarded decision writer", "separate_admission_decision_writers"),
    ("complete family selector", "closed_collision_routes"),
    ("collision routes", "closed_collision_routes"),
    ("guarded command", "mandatory_prospective_fact_coordinate"),
    ("guarded family", "single_result_receipt_replay_recovery"),
    ("caller", "admitted_scope_only"),
)
NEUTRAL_SUBJECT_PHRASES = (
    "replay glossary", "replay diagram", "replay example", "replay documentation",
    "receipt documentation", "timestamp terminology",
)
AUTHORITY_MODAL_PHRASES = (
    "may not", "must not", "cannot", "is not permitted to", "is not allowed to",
    "is not authorized to", "is permitted to", "is allowed to",
    "is authorized to", "is sufficient to", "may", "might", "must", "shall",
    "can", "could",
)
MODAL_RE = re.compile(r"\b(?:" + "|".join(re.escape(x) for x in
    sorted(AUTHORITY_MODAL_PHRASES, key=len, reverse=True)) + r")\b", re.I)
PROTECTED_ACTION_PATTERNS = {
    "replay_original_fact_timestamp": (
        r"\b(?:create|creates|recreate|recreates|refresh|refreshes)\b.{0,70}\b(?:new|second|another|acceptance|transaction)\s+(?:fact|receipt|timestamp)\b",
        r"\b(?:create|creates|recreate|recreates|refresh|refreshes)\b.{0,70}\b(?:fact|receipt|timestamp)\b",
    ),
    "mandatory_prospective_fact_coordinate": (
        r"\b(?:is|be|becomes)\s+optional\b",
        r"\b(?:omit|omits)\b.{0,50}\b(?:coordinate|fact ref)\b",
    ),
    "branch_nonselection": (
        r"\b(?:force|forces|veto|vetoes|select|selects)\b.{0,60}\b(?:branch|acceptance)\b",
    ),
    "historical_basis_non_authority": (
        r"\b(?:sufficient to|becomes?|establishes?|grants?)\b.{0,80}\bcurrent\s+(?:standing\s+)?(?:permission|authorization)\b",
    ),
    "current_external_posture": (
        r"\b(?:use|uses|replace|replaces|skip|skips|omit|omits)\b.{0,80}\b(?:historical posture|fresh current posture|current external posture)\b",
    ),
    "total_absence_currentness": (
        r"\b(?:prove|proves|establish|establishes)\b.{0,60}\b(?:noncommit|definitely not committed|unclaimed scope)\b",
    ),
    "admitted_scope_only": (
        r"\b(?:admit|admits|select|selects)\b.{0,60}\b(?:unadmitted\s+)?scope\b",
    ),
    "nonaccept_fact_collision": (
        r"\b(?:skip|skips|omit|omits)\b.{0,50}\b(?:acceptance|collision)\s+route\b",
        r"\b(?:create|creates)\b.{0,40}\btwo\s+acceptance\s+facts\b",
    ),
    "closed_collision_routes": (
        r"\b(?:skip|skips|omit|omits|extend|extends|reorder|reorders)\b.{0,50}\bcollision\s+routes?\b",
    ),
    "separate_admission_decision_writers": (
        r"\b(?:provision|provisions|repair|repairs|create|creates)\b.{0,60}\badmission\s+fact\b",
    ),
    "single_result_receipt_replay_recovery": (
        r"\b(?:create|creates|recreate|recreates)\b.{0,40}\b(?:second|another)\s+receipt\b",
    ),
    "terminal_nonreplenishment": (
        r"\b(?:replenish|replenishes|renew|renews|reset|resets|recreate|recreates)\b.{0,60}\b(?:acceptance|allowance)\b",
    ),
    "es_nonreplenishment": (
        r"\b(?:replenish|replenishes|renew|renews|reset|resets|recreate|recreates)\b.{0,60}\b(?:direct local|allowance|acceptance)\b",
    ),
}


LIST_MARKER_RE = re.compile(r"^([ \t]*)(?:[-*+]\s+|\d+[.)]\s+)(.*)$")
QUOTE_PREFIX_RE = re.compile(r"(?:> ?)+")


def _visible_line(raw):
    """Retain quote structure before removing presentation markers."""
    list_match = LIST_MARKER_RE.match(raw)
    body = list_match.group(2) if list_match else raw.lstrip(" \t")
    quote = QUOTE_PREFIX_RE.match(body)
    if quote:
        visible = body[quote.end():].strip()
        inner_list = LIST_MARKER_RE.match(visible)
        if inner_list:
            visible = inner_list.group(2).strip()
        return {
            "original": raw, "visible": visible, "kind": "quote",
            "quote_depth": quote.group().count(">"), "blank": not visible,
            "list_item": bool(list_match or inner_list),
            "list_indent": len(raw) - len(body) if list_match else None,
            "indent": len(raw) - len(raw.lstrip(" \t")),
        }
    visible = body.strip()
    if not visible:
        kind = "blank"
    elif list_match:
        kind = "list"
    elif visible.startswith("<!--"):
        kind = "comment"
    elif visible.startswith("```"):
        kind = "fence"
    elif re.match(r"^#{1,6}\s", visible):
        kind = "heading"
    elif visible.startswith("|"):
        kind = "table"
    else:
        kind = "paragraph"
    return {
        "original": raw, "visible": visible, "kind": kind,
        "quote_depth": 0, "blank": not visible,
        "list_item": bool(list_match), "list_indent": None,
        "indent": len(raw) - len(raw.lstrip(" \t")),
    }


def _visible_blocks(text):
    blocks = []
    current = []
    current_kind = None
    quote_depth = 0
    list_quote_indent = None
    fenced = False
    comment = False

    def flush():
        nonlocal current_kind, quote_depth, list_quote_indent
        if current:
            blocks.append(" ".join(current))
            current.clear()
        current_kind = None
        quote_depth = 0
        list_quote_indent = None

    for raw in text.splitlines():
        line = _visible_line(raw)
        if line["kind"] == "comment":
            flush()
            comment = "-->" not in line["visible"]
            continue
        if comment:
            if "-->" in line["visible"]:
                comment = False
            continue
        if line["kind"] == "fence":
            flush()
            fenced = not fenced
            continue
        if fenced:
            continue
        if line["blank"]:
            flush()
            continue
        if line["kind"] in {"heading", "table"}:
            flush()
            blocks.append(line["visible"])
            continue
        if line["kind"] == "quote":
            same_quote = (current_kind == "quote" and
                          quote_depth == line["quote_depth"] and
                          not line["list_item"] and
                          (list_quote_indent is None or
                           line["indent"] >= list_quote_indent))
            if not same_quote:
                flush()
            current.append(line["visible"])
            current_kind = "quote"
            quote_depth = line["quote_depth"]
            if line["list_indent"] is not None:
                list_quote_indent = line["list_indent"]
            continue
        if current_kind == "quote" or line["kind"] == "list":
            flush()
        current.append(line["visible"])
        current_kind = line["kind"]
    flush()
    return blocks


def _normalize_visible(block):
    block = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", block)
    block = block.replace("`", "").replace("*", "").replace("_", " ").replace("-", " ")
    return " ".join(re.findall(r"[a-z0-9]+", block.lower()))


SUBJECT_PREDICATE_RE = re.compile(
    r"\b(?:is|are|was|were|may|might|must|shall|can|could|cannot|"
    r"create|creates|recreate|recreates|refresh|refreshes|"
    r"admit|admits|select|selects|prove|proves|establish|establishes|"
    r"skip|skips|omit|omits|force|forces|veto|vetoes|"
    r"replenish|replenishes|renew|renews|reset|resets|"
    r"provision|provisions|repair|repairs|use|uses|replace|replaces|"
    r"grant|grants|become|becomes)\b")


def _initial_subject_words(segment):
    normalized = _normalize_visible(segment)
    predicate = SUBJECT_PREDICATE_RE.search(normalized)
    words = (normalized[:predicate.start()] if predicate else normalized).split()
    if words and words[0] in {"the", "this", "a", "an"}:
        words = words[1:]
    return words


def _neutral_subject_present(segment):
    return " ".join(_initial_subject_words(segment)) in NEUTRAL_SUBJECT_PHRASES


def _sentence_subjects(sentence):
    words = _initial_subject_words(sentence)
    if " ".join(words) in NEUTRAL_SUBJECT_PHRASES:
        return []
    matches = [(phrase, topic) for phrase, topic in PROTECTED_SUBJECT_PHRASES
               if words[:len(phrase.split())] == phrase.split()]
    if not matches:
        return []
    longest = max(len(phrase.split()) for phrase, _ in matches)
    return list(dict.fromkeys(topic for phrase, topic in matches
                              if len(phrase.split()) == longest))


def _positive_authority(sentence):
    normalized = _normalize_visible(sentence)
    if "cannot not" in normalized:
        normalized = normalized.replace("cannot not", "may")
    action = re.search(r"\b(?:create|creates|recreate|recreates|refresh|refreshes|"
                       r"admit|admits|select|selects|prove|proves|establish|establishes|"
                       r"skip|skips|force|forces|veto|vetoes|replenish|replenishes|"
                       r"renew|renews|reset|resets|provision|provisions|repair|repairs)\b",
                       normalized)
    prefix = normalized[:action.start()] if action else normalized
    if re.search(r"\b(?:cannot|may not|must not|does not|do not|never|neither|forbids)\b",
                 prefix):
        return False
    if re.search(r"\b(?:create|creates|recreate|recreates|refresh|refreshes)\s+(?:no|neither)\b",
                 normalized):
        return False
    return True


SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")
CLAUSE_BOUNDARY_RE = re.compile(
    r"\s*;\s*|\s+\b(?:but|however|although|yet|while)\b\s+|"
    r",\s*(?=(?:may|might|must|shall|can|could|cannot|"
    r"is\s+(?:not\s+)?(?:permitted|allowed|authorized|sufficient)\s+to)\b)|"
    r"\s+\band\b\s+(?=(?:no\s+(?:new|second)|may|might|must|shall|can|could|"
    r"cannot|is\s+(?:not\s+)?(?:permitted|allowed|authorized|sufficient)\s+to)\b)", re.I)


def _immediate_modal_or_action(clause):
    prefix = " ".join(_normalize_visible(clause).split()[:4])
    return bool(MODAL_RE.search(prefix) or re.search(
        r"\b(?:create|creates|recreate|recreates|refresh|refreshes|admit|admits|"
        r"select|selects|prove|proves|skip|skips|force|forces|veto|vetoes|"
        r"replenish|replenishes|renew|renews|provision|provisions)\b", prefix))


def _authority_topics(block):
    topics = []
    preceding_sentence_subjects = []
    for sentence in SENTENCE_BOUNDARY_RE.split(block):
        if not sentence.strip():
            continue
        preceding_clause_subjects = []
        for index, clause in enumerate(CLAUSE_BOUNDARY_RE.split(sentence)):
            if not clause.strip():
                continue
            explicit = _sentence_subjects(clause)
            neutral = _neutral_subject_present(clause)
            pronoun = bool(re.match(r"^\s*it\b", clause, re.I))
            if explicit:
                subjects = explicit
            elif neutral:
                subjects = []
            elif index > 0 and preceding_clause_subjects and (
                    pronoun or _immediate_modal_or_action(clause)):
                subjects = preceding_clause_subjects
            elif index == 0 and pronoun:
                subjects = preceding_sentence_subjects
            else:
                subjects = []
            normalized = _normalize_visible(clause)
            if _positive_authority(clause):
                for topic in subjects:
                    target_topic = topic
                    if (topic == "replay_original_fact_timestamp" and
                            re.search(r"\b(?:second|another) receipt\b", normalized)):
                        target_topic = "single_result_receipt_replay_recovery"
                    patterns = PROTECTED_ACTION_PATTERNS[target_topic]
                    if any(re.search(pattern, normalized) for pattern in patterns):
                        if target_topic not in topics:
                            topics.append(target_topic)
                    if (topic == "replay_original_fact_timestamp" and
                            re.search(PROTECTED_ACTION_PATTERNS[
                                "total_absence_currentness"][0], normalized) and
                            "total_absence_currentness" not in topics):
                        topics.append("total_absence_currentness")
            preceding_clause_subjects = subjects
        preceding_sentence_subjects = preceding_clause_subjects
    return topics


def _scan_normative_prose(text):
    observed = {}
    profile = _document()[1]
    _validate_owner_assertion_profile(profile)
    machine_rows = {row["clause_id"]: row for row in profile["normative_clause_registry"]}
    for block in _visible_blocks(text):
        tag = re.match(r"^NORMATIVE\s+([a-z_]+)\s+\[([a-z_]+)\]\s*:\s*(.*)$",
                       block.strip(), re.I)
        if tag:
            clause_id, consequence_id, statement = tag.groups()
            if clause_id not in PROSE_CLAUSES or clause_id not in machine_rows:
                raise ContractViolation("normative_unknown_clause")
            if consequence_id != OWNER_REFERENCE_RULES[clause_id][2]:
                raise ContractViolation("normative_consequence_tag:" + clause_id)
            if _normalize_visible(statement) != _normalize_visible(PROSE_CLAUSES[clause_id]):
                raise ContractViolation("normative_clause_mismatch:" + clause_id)
            _resolve_owner_consequence(clause_id, machine_rows[clause_id], profile)
            if _authority_topics(statement):
                raise ContractViolation("normative_owner_prose_consequence:" + clause_id)
            observed[clause_id] = observed.get(clause_id, 0) + 1
            if observed[clause_id] > 1:
                raise ContractViolation("normative_duplicate:" + clause_id)
        else:
            topics = _authority_topics(block)
            if topics:
                raise ContractViolation("normative_untagged:" + topics[0])
    if set(observed) != set(PROSE_CLAUSES):
        raise ContractViolation("normative_clause_inventory")


def test_whole_document_normative_sentence_registry():
    text, profile = _document()
    _exact(profile["normative_clause_registry"], NORMATIVE_REGISTRY,
           "normative_clause_registry")
    clauses = _normative_clauses(text)
    _exact(clauses, PROSE_CLAUSES, "normative_clause_inventory")
    _scan_normative_prose(text)


PROSE_CHALLENGES = [
    ("replay_original_fact_timestamp", "Replay creates a new fact."),
    ("replay_original_fact_timestamp", "Replay refreshes the transaction timestamp."),
    ("mandatory_prospective_fact_coordinate", "The prospective fact coordinate is optional."),
    ("branch_nonselection", "The prospective fact coordinate may force acceptance."),
    ("branch_nonselection", "The prospective fact coordinate may veto acceptance."),
    ("historical_basis_non_authority", "Historical continuity is sufficient to grant current authorization."),
    ("total_absence_currentness", "Local absence proves noncommit."),
    ("admitted_scope_only", "A command relation may select an unadmitted scope."),
    ("admitted_scope_only", "A caller may select an unadmitted scope."),
    ("nonaccept_fact_collision", "Nonaccept may skip the acceptance route."),
    ("nonaccept_fact_collision", "The candidate_acceptance branch may create two acceptance facts."),
    ("terminal_nonreplenishment", "A terminal outcome may replenish acceptance."),
    ("es_nonreplenishment", "ES routing may replenish acceptance."),
]


@pytest.mark.parametrize("topic,assertion", PROSE_CHALLENGES)
@pytest.mark.parametrize("style", ["heading", "bullet", "table", "blockquote",
                                   "link_label", "modal_synonym", "split_continuation", "double_negation"])
def test_visible_markdown_authority_challenges(topic, assertion, style):
    text, _ = _document()
    if style == "heading":
        addition = "\n## " + assertion + "\n"
    elif style == "bullet":
        addition = "\n- " + assertion + "\n"
    elif style == "table":
        addition = "\n| " + assertion + " |\n"
    elif style == "blockquote":
        addition = "\n> " + assertion + "\n"
    elif style == "link_label":
        addition = "\n[" + assertion + "](https://example.invalid/contract)\n"
    elif style == "modal_synonym":
        addition = "\n" + assertion.replace(" may ", " is permitted to ") + "\n"
    elif style == "split_continuation":
        midpoint = max(1, len(assertion.split()) // 2)
        words = assertion.split()
        addition = "\n- " + " ".join(words[:midpoint]) + "\n  " + " ".join(words[midpoint:]) + "\n"
    else:
        addition = "\n" + assertion.replace(" may ", " cannot not ") + "\n"
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(text + addition)
    assert error.value.boundary == "normative_untagged:" + topic


def test_registry_and_tagged_prose_cannot_be_mutated_together():
    text, profile = _document()
    changed = deepcopy(profile["normative_clause_registry"])
    changed[0]["modality"] = "permitted"
    mutated = text.replace(_normative_prefix("historical_basis_non_authority"),
                           _normative_prefix("historical_basis_non_authority") +
                           "Retained bases may become permission. ")
    with pytest.raises(ContractViolation) as error:
        _exact(changed, NORMATIVE_REGISTRY, "normative_clause_registry")
        _scan_normative_prose(mutated)
    assert error.value.boundary == "normative_clause_registry"


def test_unknown_or_duplicate_normative_tags_are_rejected():
    text, _ = _document()
    for addition, boundary in (
        ("NORMATIVE invented_clause [invented_consequence]: Replay creates a new fact.", "normative_unknown_clause"),
        (_normative_prefix("terminal_nonreplenishment") +
         "A terminal outcome cannot replenish acceptance.",
         "normative_duplicate:terminal_nonreplenishment"),
    ):
        with pytest.raises(ContractViolation) as error:
            _scan_normative_prose(text + "\n\n" + addition + "\n")
        assert error.value.boundary == boundary


def test_existing_owners_route_without_transferring_authority():
    target = ".docs/rw0-c2-private-value-versioning.md"
    for path in (OWNERS["guard"], OWNERS["decision"],
                 ".docs/rw0-b1-pure-phase-values.md", OWNERS["composition"]):
        text = (ROOT / path).read_text(encoding="utf-8")
        assert target in text, path
    guard = (ROOT / OWNERS["guard"]).read_text(encoding="utf-8")
    decision = (ROOT / OWNERS["decision"]).read_text(encoding="utf-8")
    b1 = (ROOT / ".docs/rw0-b1-pure-phase-values.md").read_text(encoding="utf-8")
    assert "This is the sole guard semantic owner." in guard
    assert "There is one whole-family recovery classifier" in decision
    assert "must not read or consume either" in b1


def _assignment(tree, name):
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                return ast.literal_eval(node.value)
    raise AssertionError(name)


def _source_tree(name):
    return ast.parse((ROOT / "src/ge_nwp_coordinator" / name).read_text(encoding="utf-8"))


DECISION_COLUMNS = "schema_id mutation_ref decision_ref program_ref decision_kind decision_variant basis_decision_ref basis_program_version_ref basis_program_version_number expected_program_head_revision resulting_program_version_ref resulting_program_version_number selected_semantic_attempt_ref selected_candidate_ref selected_attempt_fence_ref selected_attempt_fence_digest target_effect_intent_ref target_effect_class target_effect_fence_ref target_effect_fence_digest expected_target_effect_head_revision target_delivery_attempt_ref originating_command_ref originating_command_digest target_capsule_manifest_ref target_portable_capsule_digest coding_global_stop_ref coding_global_stop_version source_directive_ref source_directive_digest source_evidence_ref source_evidence_digest preassigned_semantic_attempt_ref preassigned_candidate_ref preassigned_effect_intent_ref preassigned_effect_fence_ref preassigned_delivery_attempt_ref resulting_accepted_intent_revision_ref resulting_work_item_ref resulting_work_item_revision_ref reason_code decided_at decision_digest".split()
RECEIPT_COLUMNS = "schema_id mutation_ref mutation_family command_schema_id command_digest program_ref decision_ref result_program_version_ref result_semantic_attempt_ref result_effect_intent_ref result_effect_fence_ref result_delivery_attempt_ref result_observation_ref result_decision_ref result_class result_projection_digest mutation_graph_digest outcome committed_at".split()
HEAD_COLUMNS = "schema_id program_ref current_program_version_ref current_program_version_number head_revision program_state updated_at head_digest".split()
VERSION_COLUMNS = "schema_id program_version_ref program_ref program_version_number program_version_kind creating_decision_ref accepted_intent_revision_ref created_at program_version_digest".split()


def test_current_v1_inventory_is_source_derived_and_unchanged():
    _, p = _document()
    d = _source_tree("_development_decision_row_values.py")
    v = _source_tree("_development_program_row_values.py")
    _exact(list(_assignment(d, "_DEVELOPMENT_DECISION_COLUMNS")), DECISION_COLUMNS, "source_v1_decision_fields")
    _exact(list(_assignment(d, "_DEVELOPMENT_MUTATION_RECEIPT_COLUMNS")), RECEIPT_COLUMNS, "source_v1_receipt_fields")
    _exact(list(_assignment(v, "_DEVELOPMENT_PROGRAM_HEAD_COLUMNS")), HEAD_COLUMNS, "source_v1_head_fields")
    _exact(list(_assignment(v, "_DEVELOPMENT_PROGRAM_HEAD_COLUMNS")), GRAPH["historical_head_fields"], "source_historical_head_snapshot_fields")
    _exact(list(_assignment(v, "_DEVELOPMENT_PROGRAM_VERSION_COLUMNS")), VERSION_COLUMNS, "source_v1_version_fields")
    schemas = (
        (d, "_DEVELOPMENT_DECISION_SCHEMA", "decision"),
        (d, "_DEVELOPMENT_MUTATION_RECEIPT_SCHEMA", "generic_receipt"),
        (d, "_PROGRESSION_RESULT_SCHEMA", "generic_result"),
        (v, "_DEVELOPMENT_PROGRAM_HEAD_SCHEMA", "program_head"),
        (v, "_DEVELOPMENT_PROGRAM_VERSION_SCHEMA", "program_version"),
    )
    for tree, assignment, key in schemas:
        observed = _assignment(tree, assignment)
        _exact([observed, observed + ".identity"], p["v1"][key][:2], "source_v1_schema_domain")
        _exact([observed, observed + ".identity"], V1[key][:2], "fixed_v1_schema_domain")
    result_class = next(node for node in d.body if isinstance(node, ast.ClassDef)
                        and node.name == "_RecordDevelopmentProgressionDecisionResultProjection")
    identity = next(node for node in result_class.body if isinstance(node, ast.FunctionDef)
                    and node.name == "identity_mapping")
    result_keys = [key.value for node in ast.walk(identity) if isinstance(node, ast.Dict)
                   for key in node.keys if isinstance(key, ast.Constant)]
    _exact(result_keys, V1["generic_result"][2], "source_v1_result_fields")
    graph_class = next(node for node in d.body if isinstance(node, ast.ClassDef)
                       and node.name == "DevelopmentMutationGraphEntry")
    graph_fields = [node.name for node in graph_class.body
                    if isinstance(node, ast.FunctionDef) and any(
                        isinstance(dec, ast.Name) and dec.id == "property" for dec in node.decorator_list)]
    _exact(graph_fields, V1["graph_entry_fields"], "source_v1_graph_fields")


def test_source_exact_receipt_graph_and_static_profile_direction():
    _, p = _document()
    tree = _source_tree("_development_decision_row_values.py")
    graph_fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "_receipt_graph_identity")
    returned = next(node.value for node in ast.walk(graph_fn) if isinstance(node, ast.Return))
    assert isinstance(returned, ast.Dict)
    source_fields = [key.value for key in returned.keys]
    _exact(source_fields, GRAPH["source_exact_receipt_preimage_fields"] + ["graph_entries"],
           "source_exact_graph_preimage")
    assert "mutation_graph_digest" not in source_fields
    assert "receipt_graph_profile_id" not in source_fields
    assert "receipt_digest" not in RECEIPT_COLUMNS
    assert p["graph"]["profile_graph_role"] is False
    assert p["graph"]["profile_instance_digest"] is False
    assert len(p["graph"]["common_roles"]) == 10
    assert "receipt_graph_profile" not in p["graph"]["common_roles"]
    profile = next(row for row in p["schemas"] if row[0] == "receipt_graph_profile")
    assert profile[2] is None
    assert "receipt_graph_digest" not in profile[4]
    assert "profile_digest" not in profile[4]
    result = next(row for row in p["schemas"] if row[0] == "guarded_result")
    assert result[4][-2] == "receipt_graph_profile_id"
    assert p["receipt_graph_profile_definition"]["schema_id"] == PROFILE_ID


def test_transaction_timestamp_edges_and_source_v1_fields():
    _, p = _document()
    nodes = {row["node"]: row for row in p["dependency_registry"]["nodes"]}
    for node in ("canonical_decision_value", "canonical_version_value",
                 "historical_head_postimage_value", "generic_receipt_preimage_value"):
        assert "transaction_timestamp" in nodes[node]["common_dependencies"]
    for node in ("guarded_family_preassignment_basis_v1", "command_digest",
                 "authoritative_branch", "recovery_selector_value",
                 "generic_receipt_graph_entries_value"):
        assert "transaction_timestamp" not in nodes[node]["common_dependencies"]
    assert "generic_receipt_preimage_value" in nodes["generic_receipt_graph_identity_value"]["common_dependencies"]
    assert nodes["generic_receipt_graph_digest"]["common_dependencies"] == ["generic_receipt_graph_identity_value"]
    assert nodes["generic_receipt_row_value"]["common_dependencies"] == [
        "generic_receipt_preimage_value", "generic_receipt_graph_digest"]
    assert not any("receipt_graph_profile" in name for name in nodes)


def test_b1_pair_and_migration_catalog_remain_current():
    _, p = _document()
    b = _source_tree("_rw0_phase_entry_semantic_values.py")
    terminal = next(node for node in b.body if isinstance(node, ast.ClassDef)
                    and node.name == "RW0TerminalOutcomeV1")
    fields = _assignment(terminal, "_FIELDS")
    index = fields.index("latch_postimage_ref")
    _exact(list(fields[index:index + 2]), B1["pair"], "source_b1_pair_order")
    _exact([_assignment(terminal, name) for name in ("_LIMIT", "_STORED_LIMIT", "_RECONSTRUCTION_LIMIT", "_EQUALITY_LIMIT")],
           [64, 32, 96, 192], "source_b1_budgets")
    _exact(_assignment(terminal, "_SCHEMA"), "governed-execution.nwp-rw0-terminal-outcome-value.v1", "source_b1_schema")
    source = (ROOT / "src/ge_nwp_coordinator/_rw0_phase_entry_semantic_values.py").read_text(encoding="utf-8")
    assert '_pair(mapping, "latch_postimage")' in source
    assert '_domain_digest(expected._SCHEMA + ".identity", identity)' in source
    migration = _source_tree("sqlite_migration.py")
    catalog = next(node for node in migration.body if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "_PACKAGED_MIGRATION_SPECS" for t in node.targets))
    resources = [next(ast.literal_eval(kw.value) for kw in call.keywords if kw.arg == "resource_name")
                 for call in catalog.value.elts]
    _exact(resources[:4], V1["migration_catalog"], "source_migration_catalog")
    _exact(resources[:4], p["v1"]["migration_catalog"], "document_migration_catalog")
    _exact(resources[4:6], ["0005_section41_post_execution_proposal_family.sql",
                            "0006_rw0_c2_scope_admission.sql"],
           "p0_catalog_successor_prefix")
    _exact(resources[6:], ["0007_rw0_c2_progression_decision.sql",
                           "0008_rw0_terminal_outcome.sql",
                           "0009_rw0_terminal_anchor_registry.sql",
                           "0010_rw0_active_cancel_pre_effect_safety_closure.sql"],
           "p1_current_catalog_successor")
    assert not (ROOT / "src/ge_nwp_coordinator/sqlite_migrations/0005_rw0_c2_guard.sql").exists()
    assert {path.name for path in (ROOT / "src/ge_nwp_coordinator/sqlite_migrations").glob("0005*")} == {
        "0005_section41_post_execution_proposal_family.sql",
    }


def test_p0_writer_table_owner_excludes_p1_acceptance_even_when_schema_id_is_constructed():
    src = ROOT / "src/ge_nwp_coordinator"
    p0_contracts = _source_tree("_rw0_c2_scope_admission_contracts.py")
    p0_writer = _source_tree("_sqlite_rw0_c2_scope_admission.py")
    p1_rows = _source_tree("_rw0_c2_progression_rows.py")
    p0_tables = {
        "rw0_c2_verified_admission_acts", "rw0_c2_scope_admission_facts",
        "rw0_c2_scope_admission_recording_bases",
        "rw0_c2_scope_admission_recording_receipts",
    }
    table_fields = next(node.value for node in p0_contracts.body
                        if isinstance(node, ast.Assign)
                        and any(isinstance(target, ast.Name) and target.id == "_TABLE_FIELDS"
                                for target in node.targets))
    assert isinstance(table_fields, ast.Dict)
    assert {ast.literal_eval(key) for key in table_fields.keys} == p0_tables
    table_names = {name: _assignment(p0_writer, name) for name in (
        "_ACT_TABLE", "_FACT_TABLE", "_BASIS_TABLE", "_RECEIPT_TABLE")}
    tables = next(node.value for node in p0_writer.body
                  if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == "_TABLES"
                          for target in node.targets))
    assert isinstance(tables, ast.Tuple)
    assert {table_names[node.id] for node in tables.elts if isinstance(node, ast.Name)} == p0_tables
    assert len(tables.elts) == 4
    write = next(node for node in p0_writer.body
                 if isinstance(node, ast.FunctionDef)
                 and node.name == "write_fresh_after_fencing")
    loops = [node for node in ast.walk(write) if isinstance(node, ast.For)]
    assert len(loops) == 1
    assert isinstance(loops[0].iter, ast.Call)
    assert isinstance(loops[0].iter.func, ast.Name)
    assert loops[0].iter.func.id == "zip"
    assert isinstance(loops[0].iter.args[0], ast.Name)
    assert loops[0].iter.args[0].id == "_TABLES"
    assert sum(isinstance(node, ast.Call)
               and isinstance(node.func, ast.Attribute)
               and isinstance(node.func.value, ast.Name)
               and node.func.value.id == "connection"
               and node.func.attr == "execute"
               for node in ast.walk(write)) == 1

    # The P1 owner intentionally constructs this schema ID; checking for a
    # contiguous source literal would miss it and obscure the P0/P1 boundary.
    p1_contracts = _source_tree("_rw0_c2_progression_contracts.py")
    prefix = _assignment(p1_contracts, "_PREFIX")
    assert prefix == PREFIX
    assert any(isinstance(node, ast.ImportFrom)
               and node.module == "_rw0_c2_progression_contracts"
               and any(alias.name == "_PREFIX" for alias in node.names)
               for node in p1_rows.body)
    schemas = next(node.value for node in p1_rows.body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "_SCHEMAS"
                           for target in node.targets))
    assert isinstance(schemas, ast.Dict)
    acceptance_schema = next(value for key, value in zip(schemas.keys, schemas.values, strict=True)
                             if isinstance(key, ast.Name) and key.id == "_ACCEPTANCE")
    assert isinstance(acceptance_schema, ast.BinOp)
    assert isinstance(acceptance_schema.op, ast.Add)
    assert isinstance(acceptance_schema.left, ast.Name)
    assert acceptance_schema.left.id == "_PREFIX"
    assert prefix + ast.literal_eval(acceptance_schema.right) == (
        "governed-execution.nwp-rw0-c2-bootstrap-acceptance-fact.v1")
    assert "rw0_c2_bootstrap_acceptance_facts" not in p0_tables
    assert {p.name for p in src.glob("*_rw0_c2_*")} == {
        "_rw0_c2_scope_admission_contracts.py",
        "_sqlite_rw0_c2_scope_admission.py",
        "_rw0_c2_progression_contracts.py",
        "_rw0_c2_progression_rows.py",
        "_rw0_c2_progression_plan.py",
        "_sqlite_rw0_c2_progression.py",
    }
    assert not list(src.glob("rw0_c2_*"))


def _set(profile, path, value):
    target = profile
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


HOSTILE = [
    ("decision_writer_creates_admission", "authority_matrix", ("authority", "scope_admission_fact", 1), "future_guarded_decision_writer"),
    ("local_absence_admits_or_unclaims", "authority_boundaries", ("boundaries", "local_absence_admits_or_unclaims"), True),
    ("operational_identity_becomes_lineage", "authority_boundaries", ("boundaries", "operational_identity_is_lineage"), True),
    ("currentness_becomes_local_fact", "authority_boundaries", ("boundaries", "external_currentness_is_local_durable_fact"), True),
    ("mutable_available_consumed_revision", "authority_boundaries", ("boundaries", "mutable_latch_state"), True),
    ("second_guard_receipt", "authority_boundaries", ("boundaries", "receipts"), 2),
    ("second_guard_replay", "authority_boundaries", ("boundaries", "replay_owners"), 2),
    ("second_guard_recovery", "authority_boundaries", ("boundaries", "recovery_classifiers"), 2),
    ("fact_on_repair", "branch_profile", ("branches", "candidate_repair", 2), 1),
    ("fact_on_replan", "branch_profile", ("branches", "attempt_selecting_replan", 2), 1),
    ("fact_on_terminal_reject", "branch_profile", ("branches", "program_terminal_reject", 2), 1),
    ("fact_on_block", "branch_profile", ("branches", "post_execution_program_block", 2), 1),
    ("missing_acceptance_fact", "branch_profile", ("branches", "candidate_acceptance", 2), 0),
    ("timestamp_in_command", "command_digest", ("command_digest", "includes"), INCLUDES + ["transaction_timestamp"]),
    ("timestamp_in_selector", "recovery_selector", ("selector", "includes"), SELECTOR["includes"] + ["transaction_timestamp"]),
    ("admission_ref_missing_from_command", "command_digest", ("command_digest", "includes"), [x for x in INCLUDES if x != "admission_fact_ref"]),
    ("admission_digest_missing_from_command", "command_digest", ("command_digest", "includes"), [x for x in INCLUDES if x != "admission_fact_digest"]),
    ("admission_ref_missing_from_selector", "recovery_selector", ("selector", "includes"), [x for x in SELECTOR["includes"] if x != "admission_fact_ref"]),
    ("admission_digest_missing_from_selector", "recovery_selector", ("selector", "includes"), [x for x in SELECTOR["includes"] if x != "admission_fact_digest"]),
    ("graph_digest_claims_member_proof", "receipt_graph", ("graph", "digest_alone_proves_members"), True),
    ("head_snapshot_omitted", "receipt_graph", ("graph", "historical_head_fields"), HEAD_COLUMNS[:-1]),
    ("head_postimage_revision_unbound", "receipt_graph", ("graph", "historical_head_equalities", 1), "family_relation.historical_head_revision=caller_revision"),
    ("graph_member_ref_rebound", "receipt_graph", ("graph", "role_bindings", "decision", 0), "v1_receipt.decision_ref"),
    ("v1_result_field_appended", "v1_preservation", ("v1", "generic_result", 2), V1["generic_result"][2] + ["acceptance_fact_ref"]),
    ("v1_receipt_authority_repurposed", "v1_preservation", ("v1", "new_v1_authority"), True),
    ("b1_pair_as_guard_authority", "b1_compatibility", ("b1", "durable_guard_authority"), True),
    ("b1_pair_consumed_by_writer", "b1_compatibility", ("b1", "guarded_writer_consumes_pair"), True),
    ("migration_0005_claimed", "authority_boundaries", ("boundaries", "migration_0005_implemented"), True),
    ("writer_claimed", "authority_boundaries", ("boundaries", "writer_implemented"), True),
    ("reader_claimed", "authority_boundaries", ("boundaries", "reader_implemented"), True),
    ("provisioner_claimed", "authority_boundaries", ("boundaries", "provisioner_implemented"), True),
    ("caller_claimed", "authority_boundaries", ("boundaries", "production_caller_implemented"), True),
    ("export_claimed", "authority_boundaries", ("boundaries", "public_export_implemented"), True),
    ("runtime_claimed", "authority_boundaries", ("boundaries", "runtime_implemented"), True),
    ("terminal_replenishes_acceptance", "authority_boundaries", ("boundaries", "terminal_creates_or_replenishes_acceptance"), True),
    ("es_replenishes_allowance", "authority_boundaries", ("boundaries", "es_replenishes_direct_local"), True),
    ("bool_is_not_one_receipt", "authority_boundaries", ("boundaries", "receipts"), True),
    ("fact_ref_nullable", "prospective_fact_identity", ("prospective_fact_identity", "nullable"), True),
    ("fact_ref_optional", "prospective_fact_identity", ("prospective_fact_identity", "required_all_branches"), False),
    ("caller_fact_ref_selects_branch", "prospective_fact_identity", ("prospective_fact_identity", "caller_selects_branch"), True),
    ("fact_collision_skipped_nonaccept", "prospective_fact_identity", ("prospective_fact_identity", "collision_probe_all_branches"), False),
    ("wrong_fact_ref_allowed", "prospective_fact_identity", ("prospective_fact_identity", "wrong_ref_invalid"), False),
    ("fact_ref_derived_from_branch", "prospective_fact_identity", ("prospective_fact_identity", "ordered_preimage", 1, 1), "decision.branch"),
    ("fact_ref_derived_from_result", "prospective_fact_identity", ("prospective_fact_identity", "ordered_preimage", 1, 1), "result.digest"),
    ("fact_ref_derived_from_receipt", "prospective_fact_identity", ("prospective_fact_identity", "ordered_preimage", 1, 1), "receipt.digest"),
    ("route_missing", "collision_route_templates", ("collision_route_templates",), ROUTES[:-1]),
    ("route_duplicate", "collision_route_templates", ("collision_route_templates",), ROUTES[:-1] + ROUTES[:1]),
    ("route_unknown", "collision_route_templates", ("collision_route_templates", 1, "role"), "implementation_specific_route"),
    ("route_copies_other_coordinate", "collision_route_templates", ("collision_route_templates", 3, "key_sources"), ["version_ref"]),
    ("route_omits_scope_winner", "collision_route_templates", ("collision_route_templates",), ROUTES[:-1]),
    ("route_uses_timestamp", "collision_route_templates", ("collision_route_templates", 3, "key_sources"), ["transaction_timestamp"]),
    ("route_uses_final_receipt", "collision_route_templates", ("collision_route_templates", 3, "key_sources"), ["receipt_digest"]),
    ("absence_without_continuity", "recovery_value", ("recovery", "total_absence_requires_positive_current_continuity"), False),
    ("partial_routes_prove_noncommit", "recovery_value", ("recovery", "missing_malformed_unreadable_foreign_duplicate_unchecked_route_class"), "definitely_not_committed"),
    ("historical_basis_becomes_permission", "replay_value", ("replay", "historical_basis_is_current_permission"), True),
    ("replay_creates_fact", "replay_value", ("replay", "new_fact"), True),
    ("replay_refreshes_timestamp", "replay_value", ("replay", "new_timestamp"), True),
    ("command_selects_unadmitted_scope", "command_digest", ("command_digest", "caller_can_select_unadmitted_scope"), True),
]


@pytest.mark.parametrize("name,boundary,path,value", HOSTILE, ids=[item[0] for item in HOSTILE])
def test_hostile_semantic_mutation(name, boundary, path, value):
    del name
    _, observed = _document()
    changed = deepcopy(observed)
    _set(changed, path, value)
    with pytest.raises(ContractViolation) as error:
        _validate(changed)
    assert error.value.boundary == boundary


@pytest.mark.parametrize("source,target", [
    ("guarded_result_digest", "acceptance_fact_value"),
    ("generic_receipt_graph_digest", "guarded_family_preassignment_basis_v1"),
], ids=["acceptance_depends_on_result", "aggregate_digest_backedge"])
def test_hostile_digest_cycle(source, target):
    _, observed = _document()
    changed = deepcopy(observed)
    node = next(row for row in changed["dependency_registry"]["nodes"]
                if row["node"] == target)
    node["common_dependencies"].append(source)
    with pytest.raises(ContractViolation) as error:
        _validate(changed)
    assert error.value.boundary in {"dependency_stage_or_cycle",
                                    "dependency_forbidden_backedge"}


def test_recursive_duplicate_json_keys_are_rejected():
    with pytest.raises(ContractViolation) as error:
        _strict_json('{"outer":{"ref":"one","ref":"two"}}')
    assert error.value.boundary == "duplicate_json_key"


FIXED_RAW_ADMISSION_ACT = {
    "schema_id": "governed-execution.nwp-rw0-c2-verified-admission-act.v1",
    "act_ref": "act-A", "act_digest": "ac" * 32,
    "lineage_ref": "lineage-A", "scope_ref": "scope-A",
    "guard_profile": "rw0-c2-guard-v1",
    "applicability": "admitted_direct_local_bootstrap",
    "provenance_ref": "policy-proof-A", "provenance_digest": "b1" * 32,
}
FIXED_RAW_ADMISSION_FACT = {
    "schema_id": "governed-execution.nwp-rw0-c2-scope-admission-fact.v1",
    "admission_fact_ref": "admission-A", "act_ref": "act-A",
    "act_digest": "ac" * 32, "lineage_ref": "lineage-A",
    "scope_ref": "scope-A", "guard_profile": "rw0-c2-guard-v1",
    "applicability": "admitted_direct_local_bootstrap",
    "provenance_ref": "policy-proof-A", "provenance_digest": "b1" * 32,
    "one_shot_ceiling": 1,
}
# This oracle is authored independently from both raw input and builders.
EXPECTED_ADMISSION_ACT = {
    "schema_id": "governed-execution.nwp-rw0-c2-verified-admission-act.v1",
    "act_ref": "act-A", "act_digest": "ac" * 32,
    "lineage_ref": "lineage-A", "scope_ref": "scope-A",
    "guard_profile": "rw0-c2-guard-v1",
    "applicability": "admitted_direct_local_bootstrap",
    "provenance_ref": "policy-proof-A", "provenance_digest": "b1" * 32,
    "projection_digest": "cfcd726c87164e89779d0c1b13a080746e21cdf092be6ba11015e9c052634b1c",
}
EXPECTED_ADMISSION_FACT = {
    "schema_id": "governed-execution.nwp-rw0-c2-scope-admission-fact.v1",
    "admission_fact_ref": "admission-A", "act_ref": "act-A",
    "act_digest": "ac" * 32, "lineage_ref": "lineage-A",
    "scope_ref": "scope-A", "guard_profile": "rw0-c2-guard-v1",
    "applicability": "admitted_direct_local_bootstrap",
    "provenance_ref": "policy-proof-A", "provenance_digest": "b1" * 32,
    "one_shot_ceiling": 1,
    "admission_fact_digest": "68303f1a8c16309605c3701d88ad63858b40a6a4ae5b0ad8ee116a44b5d33ae1",
}
FIXED_CURRENT_BASES = {
    "continuity_basis_ref": "continuity-basis-A",
    "continuity_basis_digest": "e7e50ee17c285a0b54199891c5d2c5a324da0bee5a76fac2c6463145886a90f5",
    "continuity_source_ref": "continuity-source-A",
    "continuity_source_digest": "ce" * 32,
    "sole_active_basis_ref": "sole-basis-A",
    "sole_active_basis_digest": "29c2547e8aa3f8c2bea89ea149a33ab853a0c5c10fab9fc75b06561b1ae02383",
    "sole_active_source_ref": "sole-source-A",
    "sole_active_source_digest": "df" * 32,
}


def _private_identity_digest(schema_id, identity):
    raw = json.dumps(identity, ensure_ascii=False, allow_nan=False,
                     sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256((schema_id + ".identity").encode("utf-8") + b"\0" + raw).hexdigest()


def _verified_admission_fixture():
    act = deepcopy(FIXED_RAW_ADMISSION_ACT)
    act["projection_digest"] = _private_identity_digest(act["schema_id"], act)
    fact = deepcopy(FIXED_RAW_ADMISSION_FACT)
    fact["admission_fact_digest"] = _private_identity_digest(fact["schema_id"], fact)
    return act, fact


def _command_coordinates():
    act, fact = _verified_admission_fixture()
    command = {
        "schema_id": PREFIX + "admitted-command-relation.v1",
        "lineage_ref": fact["lineage_ref"], "scope_ref": fact["scope_ref"],
        "admission_fact_ref": fact["admission_fact_ref"],
        "admission_fact_digest": fact["admission_fact_digest"],
        "admission_act_ref": act["act_ref"], "admission_act_digest": act["act_digest"],
        "guard_profile": fact["guard_profile"],
        "applicability": fact["applicability"],
        **FIXED_CURRENT_BASES,
        "mutation_ref": "mutation-A", "program_ref": "program-A",
        "decision_basis_ref": "decision-basis-A",
        "decision_basis_digest": "ef" * 32,
        "expected_head_ref": "program-A", "expected_head_revision": 4,
        "expected_head_digest": "645f2b1fa3683fa8606df25fa844a6854345d85b32ee8c78b1d388202acaa42e",
    }
    command.update(_derive_siblings(command))
    command["relation_digest"] = _private_identity_digest(command["schema_id"], command)
    return command


def _fixed_preimage_bytes(command, schema_id=None):
    pairs = []
    for name in PRIMITIVE_NAMES:
        source = "schema_id" if name == "command_profile" else name
        if source not in command:
            raise ContractViolation("preassignment_basis_field")
        value = (schema_id if schema_id is not None else command[source]) if name == "command_profile" else command[source]
        wanted = _primitive_type(name)
        if (wanted == "nonnegative_exact_int_not_bool" and
                (type(value) is not int or value < 0)):
            raise ContractViolation("prospective_fact_preimage_type")
        if wanted == "lowercase_sha256_hex_64" and (
                type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None):
            raise ContractViolation("prospective_fact_preimage_type")
        if wanted == "nonempty_exact_str" and (type(value) is not str or not value):
            raise ContractViolation("prospective_fact_preimage_type")
        pairs.append([name, value])
    return json.dumps(pairs, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def _derive_siblings(command):
    preimage = _fixed_preimage_bytes(command)
    return {field: hashlib.sha256(domain.encode("utf-8") + b"\0" + preimage).hexdigest()
            for _, field, domain, _ in SIBLING_SPECS}


def _guarded_command_digest_v1(command):
    if type(command) is not dict:
        raise ContractViolation("guarded_command_shape")
    pairs = []
    for name, source, wanted in COMMAND_DIGEST["ordered_preimage"]:
        field = "schema_id" if name == "command_profile" else name
        if source != "command_relation." + field or field not in command:
            raise ContractViolation("guarded_command_field")
        value = command[field]
        if wanted == "nonnegative_exact_int_not_bool":
            valid = type(value) is int and value >= 0
        elif wanted == "lowercase_sha256_hex_64":
            valid = type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None
        else:
            valid = type(value) is str and bool(value)
        if not valid:
            raise ContractViolation("guarded_command_type:" + name)
        pairs.append([name, value])
    if [name for name, _, _ in COMMAND_DIGEST["ordered_preimage"]] != INCLUDES:
        raise ContractViolation("guarded_command_inventory")
    raw = json.dumps(pairs, ensure_ascii=False, allow_nan=False,
                     separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(COMMAND_DOMAIN.encode("utf-8") + b"\0" + raw).hexdigest()


def _fixed_fact_ref(command, schema_id=None):
    preimage = _fixed_preimage_bytes(command, schema_id)
    return hashlib.sha256(PROSPECTIVE_DOMAIN.encode("utf-8") + b"\0" + preimage).hexdigest()


def _validate_admission_binding(command, act, fact):
    if (type(act) is not dict or set(act) != set(ADMISSION_BINDING["verified_act_fields"]) or
            type(fact) is not dict or set(fact) != set(ADMISSION_BINDING["immutable_fact_fields"])):
        raise ContractViolation("verified_admission_shape")
    if act["schema_id"] != EXPECTED_SCHEMAS[0][1] or fact["schema_id"] != EXPECTED_SCHEMAS[1][1]:
        raise ContractViolation("verified_admission_schema")
    _exact(act, EXPECTED_ADMISSION_ACT, "fixed_admission_act_vector")
    _exact(fact, EXPECTED_ADMISSION_FACT, "fixed_admission_fact_vector")
    if (type(fact["one_shot_ceiling"]) is not int or fact["one_shot_ceiling"] != 1 or
            any(fact[name] != act[name] for name in
                ("act_ref", "act_digest", "lineage_ref", "scope_ref",
                 "guard_profile", "applicability", "provenance_ref", "provenance_digest"))):
        raise ContractViolation("verified_admission_act_fact_binding")
    names = {"admission_act_ref": "act_ref", "admission_act_digest": "act_digest"}
    for name in ADMISSION_BINDING["command_equalities"]:
        if type(command.get(name)) is not type(fact[names.get(name, name)]) or command[name] != fact[names.get(name, name)]:
            raise ContractViolation("admission_binding:" + name)


FRESH_POSTURE_VECTOR = {
    "fresh_current_continuity": {"status": "positive", "evidence_ref": "fresh-continuity-A",
                                 "evidence_digest": "91" * 32},
    "fresh_current_sole_active": {"status": "positive", "evidence_ref": "fresh-sole-active-A",
                                  "evidence_digest": "92" * 32},
}
ALTERNATE_POSTURE_VECTOR = {
    "fresh_current_continuity": {"status": "positive", "evidence_ref": "fresh-continuity-B",
                                 "evidence_digest": "93" * 32},
    "fresh_current_sole_active": {"status": "positive", "evidence_ref": "fresh-sole-active-B",
                                  "evidence_digest": "94" * 32},
}


def _validate_fresh_posture(posture):
    if type(posture) is not dict or set(posture) != set(FRESH_POSTURE_VECTOR):
        raise ContractViolation("current_external_posture")
    for field in FRESH_POSTURE_VECTOR:
        value = posture[field]
        if type(value) is not dict or set(value) != {"status", "evidence_ref", "evidence_digest"}:
            raise ContractViolation("current_external_posture")
        if (value["status"] != "positive" or type(value["evidence_ref"]) is not str
                or not value["evidence_ref"] or type(value["evidence_digest"]) is not str
                or re.fullmatch(r"[0-9a-f]{64}", value["evidence_digest"]) is None):
            raise ContractViolation("current_external_posture")
    return posture


def _validate_command_skeleton(command, act, fact):
    if type(command) is not dict or set(command) != set(EXPECTED_SCHEMAS[2][4]):
        raise ContractViolation("command_relation_closed")
    _validate_admission_binding(command, act, fact)
    if command.get("schema_id") != EXPECTED_SCHEMAS[2][1]:
        raise ContractViolation("command_profile")
    for name, wanted in FIXED_CURRENT_BASES.items():
        if type(command.get(name)) is not str or command[name] != wanted:
            raise ContractViolation("current_basis_binding:" + name)
    if type(command["expected_head_revision"]) is not int or command["expected_head_revision"] < 0:
        raise ContractViolation("expected_head_revision")


def _validate_prebranch_admission(command, act, fact, *, fresh_posture):
    _validate_command_skeleton(command, act, fact)
    _validate_fresh_posture(fresh_posture)


def _validate_command_relation(command, act, fact):
    _validate_command_skeleton(command, act, fact)
    expected = _derive_siblings(command)
    for name, value in expected.items():
        if type(command.get(name)) is not str or command[name] != value:
            raise ContractViolation("preassignment_sibling:" + name)
    if command["relation_digest"] != _private_identity_digest(
            command["schema_id"], {key: value for key, value in command.items()
                                   if key != "relation_digest"}):
        raise ContractViolation("command_relation_digest")
    return command


def _private_branch_path(c2, command, act, fact, state, *, fresh_posture):
    _validate_prebranch_admission(command, act, fact, fresh_posture=fresh_posture)
    _validate_command_relation(command, act, fact)
    observation = c2._interpret(c2.EXPECTED_CONTRACT, state)
    branch = observation["branch"]
    _validate_fact_assertion(command)
    if branch not in BRANCHES:
        raise ContractViolation("authoritative_branch")
    family = _family_fixture(branch, command)
    actual_fact = family["acceptance_fact"]
    roles = _receipt_roles_fixture(branch, actual_fact, command)
    return {"branch": branch, "family": family, "acceptance_fact": actual_fact,
            "receipt_roles": roles}


def _validate_fact_assertion(command):
    if "preassigned_acceptance_fact_ref" not in command:
        raise ContractViolation("fact_command_grammar")
    ref = command["preassigned_acceptance_fact_ref"]
    if type(ref) is not str or not re.fullmatch(r"[0-9a-f]{64}", ref):
        raise ContractViolation("fact_command_grammar")
    if ref != _fixed_fact_ref(command):
        raise ContractViolation("prospective_fact_identity")
    return ref


def _selector_instance(command):
    fact_ref = _validate_fact_assertion(command)
    selector = {
        "schema_id": "governed-execution.nwp-rw0-c2-complete-family-selector.v1",
        "lineage_ref": command["lineage_ref"], "scope_ref": command["scope_ref"],
        "admission_fact_ref": command["admission_fact_ref"],
        "admission_fact_digest": command["admission_fact_digest"],
        "mutation_ref": command["mutation_ref"],
        "command_digest": _guarded_command_digest_v1(command),
        "decision_ref": command["preassigned_decision_ref"],
        "version_ref": command["preassigned_version_ref"],
        "acceptance_fact_ref": fact_ref,
        "relation_ref": command["preassigned_relation_ref"],
        "guarded_result_ref": command["preassigned_guarded_result_ref"],
        "family_route": command["family_route"],
        "selector_digest": "",
    }
    templates = _document()[1]["collision_route_templates"]
    selector["required_collision_routes"] = [
        {"role": template["role"], "kind": template["kind"],
         "key": [selector[source] for source in template["key_sources"]],
         "expected_schema_id": template["expected_schema_id"]}
        for template in templates
    ]
    selector["selector_digest"] = _private_identity_digest(selector["schema_id"],
        {key: value for key, value in selector.items() if key != "selector_digest"})
    return selector


def _validate_selector_instance(selector, command=None):
    expected_top = set(SELECTOR["includes"]) | {"schema_id", "selector_digest"}
    if type(selector) is not dict or set(selector) != expected_top:
        raise ContractViolation("recovery_selector_closed")
    command = _command_coordinates() if command is None else command
    _validate_command_relation(command, *_verified_admission_fixture())
    expected = {
        "lineage_ref": command["lineage_ref"], "scope_ref": command["scope_ref"],
        "admission_fact_ref": command["admission_fact_ref"],
        "admission_fact_digest": command["admission_fact_digest"],
        "mutation_ref": command["mutation_ref"],
        "command_digest": _guarded_command_digest_v1(command),
        "decision_ref": command["preassigned_decision_ref"],
        "version_ref": command["preassigned_version_ref"],
        "acceptance_fact_ref": command["preassigned_acceptance_fact_ref"],
        "relation_ref": command["preassigned_relation_ref"],
        "guarded_result_ref": command["preassigned_guarded_result_ref"],
        "family_route": command["family_route"],
    }
    for name, wanted in expected.items():
        if type(selector[name]) is not type(wanted) or selector[name] != wanted:
            raise ContractViolation("selector_command_binding:" + name)
    routes = selector["required_collision_routes"]
    if type(routes) is not list or len(routes) != 8:
        raise ContractViolation("selector_route_inventory")
    roles = [route.get("role") if type(route) is dict else None for route in routes]
    if roles != [template["role"] for template in ROUTES]:
        raise ContractViolation("selector_route_inventory")
    for route, template in zip(routes, ROUTES, strict=True):
        if set(route) != {"role", "kind", "key", "expected_schema_id"}:
            raise ContractViolation("selector_route_element_grammar")
        if type(route["kind"]) is not str or route["kind"] != template["kind"]:
            raise ContractViolation("selector_route_element_grammar")
        if type(route["key"]) is not list or len(route["key"]) != len(template["key_sources"]):
            raise ContractViolation("selector_route_element_grammar")
        if any(type(value) is not str or not value for value in route["key"]):
            raise ContractViolation("selector_route_element_grammar")
        if type(route["expected_schema_id"]) is not type(template["expected_schema_id"]):
            raise ContractViolation("selector_route_schema")
        if route["expected_schema_id"] != template["expected_schema_id"]:
            raise ContractViolation("selector_route_schema")
        if list(route["key"]) != [selector[source] for source in template["key_sources"]]:
            raise ContractViolation("selector_route_coordinate_binding")

    if selector["selector_digest"] != _private_identity_digest(selector["schema_id"],
            {key: value for key, value in selector.items() if key != "selector_digest"}):
        raise ContractViolation("selector_digest")

def _require_total_absence(selector, observations, *, current_continuity, current_sole_active):
    _validate_selector_instance(selector)
    if type(observations) is not dict or set(observations) != {r["role"] for r in ROUTES}:
        raise ContractViolation("recovery_route_coverage")
    if observations["acceptance_fact_identity_route"] == "occupied":
        raise ContractViolation("reserved_fact_collision")
    if any(type(value) is not str or value != "absent" for value in observations.values()):
        raise ContractViolation("recovery_route_coverage")
    if current_continuity is not True or current_sole_active is not True:
        raise ContractViolation("recovery_current_posture")


def _validate_branch_members(branch, fact_refs, command, selector):
    ref = _validate_fact_assertion(command)
    _validate_selector_instance(selector, command)
    if type(fact_refs) is not list or any(type(item) is not str for item in fact_refs):
        raise ContractViolation("branch_fact_membership")
    required = [ref] if branch == "candidate_acceptance" else []
    if branch not in BRANCHES or fact_refs != required:
        raise ContractViolation("branch_fact_membership")


# The fixed input literals do not come from any family builder. The current
# head is a valid v1 row and the command's expected digest equals that row.
CURRENT_HEAD_IDENTITY = {
    "schema_id": "governed-execution.nwp-development-program-head.v1",
    "program_ref": "program-A", "current_program_version_ref": "version-1-A",
    "current_program_version_number": 1, "head_revision": 4,
    "program_state": "active", "updated_at": "2025-12-31T00:00:00Z",
}
CURRENT_HEAD_DIGEST = "645f2b1fa3683fa8606df25fa844a6854345d85b32ee8c78b1d388202acaa42e"
FIXED_FAMILY_INPUT = {
    "program_ref": "program-A", "mutation_ref": "mutation-A",
    "basis_decision_ref": "decision-basis-A",
    "basis_program_version_ref": "version-1-A", "basis_program_version_number": 1,
    "resulting_program_version_number": 2, "accepted_intent_revision_ref": "intent-A",
    "coding_global_stop_ref": "global-stop-A", "coding_global_stop_version": 0,
    "selected_semantic_attempt_ref": "attempt-A", "selected_candidate_ref": "candidate-A",
    "selected_attempt_fence_ref": "attempt-fence-A",
    "selected_attempt_fence_digest": "86" * 32,
    "next_semantic_attempt_ref": "attempt-next-A", "next_candidate_ref": "candidate-next-A",
    "next_accepted_intent_revision_ref": "intent-next-A",
    "next_work_item_ref": "work-next-A", "next_work_item_revision_ref": "work-revision-next-A",
    "timestamp": "2026-01-01T00:00:00Z",
}
V1_DECISION_COLUMNS = tuple("""schema_id mutation_ref decision_ref program_ref decision_kind
    decision_variant basis_decision_ref basis_program_version_ref basis_program_version_number
    expected_program_head_revision resulting_program_version_ref resulting_program_version_number
    selected_semantic_attempt_ref selected_candidate_ref selected_attempt_fence_ref
    selected_attempt_fence_digest target_effect_intent_ref target_effect_class
    target_effect_fence_ref target_effect_fence_digest expected_target_effect_head_revision
    target_delivery_attempt_ref originating_command_ref originating_command_digest
    target_capsule_manifest_ref target_portable_capsule_digest coding_global_stop_ref
    coding_global_stop_version source_directive_ref source_directive_digest source_evidence_ref
    source_evidence_digest preassigned_semantic_attempt_ref preassigned_candidate_ref
    preassigned_effect_intent_ref preassigned_effect_fence_ref preassigned_delivery_attempt_ref
    resulting_accepted_intent_revision_ref resulting_work_item_ref resulting_work_item_revision_ref
    reason_code decided_at decision_digest""".split())
V1_VERSION_COLUMNS = ("schema_id", "program_version_ref", "program_ref", "program_version_number",
                      "program_version_kind", "creating_decision_ref", "accepted_intent_revision_ref",
                      "created_at", "program_version_digest")
V1_HEAD_COLUMNS = ("schema_id", "program_ref", "current_program_version_ref",
                   "current_program_version_number", "head_revision", "program_state",
                   "updated_at", "head_digest")
V1_RECEIPT_COLUMNS = tuple("""schema_id mutation_ref mutation_family command_schema_id
    command_digest program_ref decision_ref result_program_version_ref
    result_semantic_attempt_ref result_effect_intent_ref result_effect_fence_ref
    result_delivery_attempt_ref result_observation_ref result_decision_ref result_class
    result_projection_digest mutation_graph_digest outcome committed_at""".split())
V1_VERSION_KIND = {"candidate_acceptance": "accepted", "candidate_repair": "repair",
                   "attempt_selecting_replan": "replan", "program_terminal_reject": "terminal_rejected",
                   "post_execution_program_block": "blocked"}
V1_HEAD_STATE = {"candidate_acceptance": "accepted", "candidate_repair": "active",
                 "attempt_selecting_replan": "active", "program_terminal_reject": "terminal_rejected",
                 "post_execution_program_block": "blocked"}


def _canonical_source_members(branch, command):
    from ge_nwp_coordinator import _development_decision_row_values as decisions
    from ge_nwp_coordinator import _development_program_row_values as programs

    if branch not in BRANCHES:
        raise ContractViolation("canonical_family_branch")
    basis = FIXED_FAMILY_INPUT
    assert _private_identity_digest(CURRENT_HEAD_IDENTITY["schema_id"], CURRENT_HEAD_IDENTITY) == CURRENT_HEAD_DIGEST
    assert command["program_ref"] == CURRENT_HEAD_IDENTITY["program_ref"]
    assert command["expected_head_ref"] == CURRENT_HEAD_IDENTITY["program_ref"]
    assert command["expected_head_revision"] == CURRENT_HEAD_IDENTITY["head_revision"]
    assert command["expected_head_digest"] == CURRENT_HEAD_DIGEST
    current_head_row = dict(CURRENT_HEAD_IDENTITY, head_digest=CURRENT_HEAD_DIGEST)
    current_head = programs.development_program_head_row_value_from_row_tuple(
        tuple(current_head_row[name] for name in V1_HEAD_COLUMNS))
    assert current_head.computed_digest() == CURRENT_HEAD_DIGEST
    assert decisions._DEVELOPMENT_DECISION_COLUMNS == V1_DECISION_COLUMNS
    assert programs._DEVELOPMENT_PROGRAM_VERSION_COLUMNS == V1_VERSION_COLUMNS
    assert programs._DEVELOPMENT_PROGRAM_HEAD_COLUMNS == V1_HEAD_COLUMNS
    assert decisions._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS == V1_RECEIPT_COLUMNS
    identity = {name: None for name in V1_DECISION_COLUMNS if name != "decision_digest"}
    identity.update({
        "schema_id": "governed-execution.nwp-development-decision.v1",
        "mutation_ref": command["mutation_ref"], "decision_ref": command["preassigned_decision_ref"],
        "program_ref": command["program_ref"], "decision_kind": BRANCHES[branch][0],
        "decision_variant": BRANCHES[branch][1],
        "basis_decision_ref": command["decision_basis_ref"],
        "basis_program_version_ref": basis["basis_program_version_ref"],
        "basis_program_version_number": basis["basis_program_version_number"],
        "expected_program_head_revision": CURRENT_HEAD_IDENTITY["head_revision"],
        "resulting_program_version_ref": command["preassigned_version_ref"],
        "resulting_program_version_number": basis["resulting_program_version_number"],
        "coding_global_stop_ref": basis["coding_global_stop_ref"],
        "coding_global_stop_version": basis["coding_global_stop_version"],
        "reason_code": "decision.recorded", "decided_at": basis["timestamp"],
    })
    if branch != "post_execution_program_block":
        identity.update({
            "selected_semantic_attempt_ref": basis["selected_semantic_attempt_ref"],
            "selected_candidate_ref": basis["selected_candidate_ref"],
            "selected_attempt_fence_ref": basis["selected_attempt_fence_ref"],
            "selected_attempt_fence_digest": basis["selected_attempt_fence_digest"],
        })
    if branch in {"candidate_repair", "attempt_selecting_replan"}:
        identity.update({
            "preassigned_semantic_attempt_ref": basis["next_semantic_attempt_ref"],
            "preassigned_candidate_ref": basis["next_candidate_ref"],
        })
    if branch == "attempt_selecting_replan":
        identity.update({
            "resulting_accepted_intent_revision_ref": basis["next_accepted_intent_revision_ref"],
            "resulting_work_item_ref": basis["next_work_item_ref"],
            "resulting_work_item_revision_ref": basis["next_work_item_revision_ref"],
        })
    decision_digest = _private_identity_digest(identity["schema_id"], identity)
    decision_row = dict(identity, decision_digest=decision_digest)
    decision = decisions.development_decision_row_value_from_row_tuple(
        tuple(decision_row[name] for name in V1_DECISION_COLUMNS))
    assert decision.computed_digest() == decision_digest
    assert decision.identity_mapping() == identity
    version_identity = {
        "schema_id": "governed-execution.nwp-development-program-version.v1",
        "program_version_ref": command["preassigned_version_ref"],
        "program_ref": command["program_ref"],
        "program_version_number": basis["resulting_program_version_number"],
        "program_version_kind": V1_VERSION_KIND[branch],
        "creating_decision_ref": command["preassigned_decision_ref"],
        "accepted_intent_revision_ref": basis["accepted_intent_revision_ref"],
        "created_at": basis["timestamp"],
    }
    version_digest = _private_identity_digest(version_identity["schema_id"], version_identity)
    version_row = dict(version_identity, program_version_digest=version_digest)
    version = programs.development_program_version_row_value_from_row_tuple(
        tuple(version_row[name] for name in V1_VERSION_COLUMNS))
    assert version.computed_digest() == version_digest
    head_identity = {
        "schema_id": "governed-execution.nwp-development-program-head.v1",
        "program_ref": command["program_ref"],
        "current_program_version_ref": command["preassigned_version_ref"],
        "current_program_version_number": basis["resulting_program_version_number"],
        "head_revision": CURRENT_HEAD_IDENTITY["head_revision"] + 1,
        "program_state": V1_HEAD_STATE[branch], "updated_at": basis["timestamp"],
    }
    head_digest = _private_identity_digest(head_identity["schema_id"], head_identity)
    head_row = dict(head_identity, head_digest=head_digest)
    head = programs.development_program_head_row_value_from_row_tuple(
        tuple(head_row[name] for name in V1_HEAD_COLUMNS))
    assert head.computed_digest() == head_digest
    result_identity = {
        "schema_id": "governed-execution.nwp-record-development-progression-decision-result.v1",
        "program_ref": command["program_ref"], "decision_ref": command["preassigned_decision_ref"],
        "result_program_version_ref": command["preassigned_version_ref"],
        "result_decision_ref": command["preassigned_decision_ref"],
    }
    result_digest = _private_identity_digest(result_identity["schema_id"], result_identity)
    return {"decision": decision, "decision_row": decision_row,
            "version": version, "version_row": version_row,
            "historical_head_postimage": head, "historical_head_postimage_row": head_row,
            "generic_result_projection": result_identity,
            "generic_result_projection_digest": result_digest}


EXPECTED_COMMON_RECEIPT_ROLES = (
    "verified_admission_act", "scope_admission_fact",
    "historical_continuity_basis", "historical_sole_active_basis",
    "decision", "program_version", "historical_head_postimage",
    "generic_v1_result_projection", "guarded_family_relation",
    "guarded_result_composite",
)
# Fixed expected outputs are filled from a separate literal vector below and
# compared after invoking the current v1 constructors. They are never read
# from the private machine block or generated by the builder under test.
FIXED_CANONICAL_OUTPUTS = {
    "candidate_acceptance": {
        "decision": "aefb1f727127ae37500426fcd2b4ed57d1465be50d4fea4a10e8122b0cf17008",
        "version": "185789b58cc95b8579bfe72fe1ee67f564ccc3e18090c1b7a25925258249f683",
        "head": "272c393bb53b4f45c353b6eaa0c877175bf976a25f1e0787c388de044d6376e3",
        "result": "64ed10e407546085d9102502c493623f014af59dd857e237912fa23916b92cf4",
        "acceptance": "02eb9ffbb1fbf9417d4ebb6bb5e5f2017cccdadd93fe55e59680c7f64ba48031",
        "relation": "c35d42f12fad729857afb9cd2b6f297830daa8630184ebbde5c266702e7e2c95",
        "guarded_result": "46521d87704984013dcea317b2f8dcaf9cc38f63d6fe3832e88ca3382886a5e4",
        "graph": "1e1535e588a941855f79d21c3150fd8239c2e94aa60d90a0a59bf15dc9fa124b",
    },
    "candidate_repair": {
        "decision": "48d6053219f9a09b06f662018b8d89552c4dd9dff8eb5ee431e96d6e553a0cd7",
        "version": "ed007177d92265dfc53db1c80bc78d0153d4650a1ee2c972a1e7901ac6cfbb61",
        "head": "754d00836e2fe9d8b45ae1d8622ff332c6d0e4fd86d6db6ad63f5f4f27078047",
        "result": "64ed10e407546085d9102502c493623f014af59dd857e237912fa23916b92cf4",
        "acceptance": None,
        "relation": "2f979d225d2fbbbefca2a713864031db955f2455e38d51fe2d484dc6c04c7a24",
        "guarded_result": "0ff8d035c537994012462bb551b2c330ccc67d85d150fe1d2e40ce4081153bb9",
        "graph": "f65f45487ffde890c44ceae2b21d2134c34c12d415e0b06b5e49cd38ff05d825",
    },
    "attempt_selecting_replan": {
        "decision": "6e0cda8ae736cc4e07a6c161be196ddd1d82d16d0032f6852a03c7e2a39e3380",
        "version": "f0346848aaca0ed6b03c7f2810516d8204a7327b75fd87561869fba67d9c8505",
        "head": "754d00836e2fe9d8b45ae1d8622ff332c6d0e4fd86d6db6ad63f5f4f27078047",
        "result": "64ed10e407546085d9102502c493623f014af59dd857e237912fa23916b92cf4",
        "acceptance": None,
        "relation": "acf2ebaab307a599d2b50ad17319fd9cd9a62a4d72c5251c139fdd315c214739",
        "guarded_result": "ee53f805e4458519b7e937f9e5a9f484e233afaf8900c49206935aaf844723ca",
        "graph": "eb8d9ef4139fc8bb9a9b59726087a580fdb93b241359d5d20dd3f010e98c77e0",
    },
    "program_terminal_reject": {
        "decision": "23cfe6b03870a9489dbfd0289a3b28e36c609b897b088d366d72913e98c73e85",
        "version": "a83d083b99989a73918fd01771d0b6bb5a1a3f6547a69ecd1f9fa1b5fe0653b4",
        "head": "4b8881a07b189251c3e1a2003d7b9c4d58ad4a256d5256082a234aeaa5dc5789",
        "result": "64ed10e407546085d9102502c493623f014af59dd857e237912fa23916b92cf4",
        "acceptance": None,
        "relation": "a68409aaa0d03ef59e7f18e758a7d790073948366f09ae2e85afebe34fc5e034",
        "guarded_result": "0a97de8ac3b6e9b156cb73a83e2404977102fb51cf9c2d950c2d69a8356cd2b3",
        "graph": "07196a218e47d55f973cc5142de0d279811b0cbd98c087b5b62087fb623a5d23",
    },
    "post_execution_program_block": {
        "decision": "e359ff1424a50a3b15cdac56d516d2601b712e4906bb756fdc66646ca5a95082",
        "version": "c7f0d4efa0b110391d7426cb1fc4ef0d775e516104e8732ecb359c2c26cc059e",
        "head": "89989e2e2906add5673894493462c1ded77a2f1f0a8513a8b5bfc8606536fc6f",
        "result": "64ed10e407546085d9102502c493623f014af59dd857e237912fa23916b92cf4",
        "acceptance": None,
        "relation": "e9667744297ca7375280e539ee2808f977d284ab0f44511c9e515a003b6fc624",
        "guarded_result": "6268e28e7c79b43951e8d6de66656defc834dabe9349e8082b1204dc79020a66",
        "graph": "d35f036a2bf04415011a77f011a86bf3503a850f90c07eb91aa4f190f0f692aa",
    },
}
EXPECTED_SOURCE_GRAPH_DIGESTS = {
    branch: values["graph"] for branch, values in FIXED_CANONICAL_OUTPUTS.items()
}


def _family_fixture(branch, command=None):
    command = _command_coordinates() if command is None else command
    source = _canonical_source_members(branch, command)
    act, admission = _verified_admission_fixture()
    basis = FIXED_FAMILY_INPUT
    head_row = source["historical_head_postimage_row"]
    family = {
        "decision_ref": command["preassigned_decision_ref"],
        "decision_digest": source["decision"].computed_digest(),
        "version_ref": command["preassigned_version_ref"],
        "version_digest": source["version"].computed_digest(),
        "historical_head_ref": head_row["program_ref"],
        "historical_head_revision": head_row["head_revision"],
        "historical_head_digest": source["historical_head_postimage"].computed_digest(),
        "generic_result_projection_digest": source["generic_result_projection_digest"],
        "relation_ref": command["preassigned_relation_ref"],
        "guarded_result_ref": command["preassigned_guarded_result_ref"],
        "mutation_ref": command["mutation_ref"], "program_ref": command["program_ref"],
        "command_digest": _guarded_command_digest_v1(command),
        "selected_attempt_ref": basis["selected_semantic_attempt_ref"],
        "selected_candidate_ref": basis["selected_candidate_ref"],
        "basis_ref": command["decision_basis_ref"],
        "basis_digest": command["decision_basis_digest"],
        "family_route": command["family_route"],
        "transaction_timestamp": basis["timestamp"],
        **source,
    }
    acceptance = None
    if branch == "candidate_acceptance":
        acceptance = {
            "schema_id": ACCEPTANCE_SCHEMA,
            "acceptance_fact_ref": command["preassigned_acceptance_fact_ref"],
            "lineage_ref": command["lineage_ref"], "scope_ref": command["scope_ref"],
            "admission_fact_ref": command["admission_fact_ref"],
            "admission_fact_digest": command["admission_fact_digest"],
            "mutation_ref": command["mutation_ref"],
            "command_digest": family["command_digest"],
            "decision_ref": family["decision_ref"],
            "decision_digest": family["decision_digest"],
            "version_ref": family["version_ref"],
            "version_digest": family["version_digest"],
            "historical_head_ref": family["historical_head_ref"],
            "historical_head_revision": family["historical_head_revision"],
            "historical_head_digest": family["historical_head_digest"],
            "selected_attempt_ref": family["selected_attempt_ref"],
            "selected_candidate_ref": family["selected_candidate_ref"],
            "basis_ref": family["basis_ref"], "basis_digest": family["basis_digest"],
            "family_route": family["family_route"],
            "accepted_at": family["transaction_timestamp"],
        }
        acceptance["acceptance_fact_digest"] = _private_identity_digest(
            ACCEPTANCE_SCHEMA, acceptance)
    family["acceptance_fact"] = acceptance
    relation = {
        "schema_id": EXPECTED_SCHEMAS[6][1],
        "relation_ref": family["relation_ref"], "branch": branch,
        "lineage_ref": command["lineage_ref"], "scope_ref": command["scope_ref"],
        "command_digest": family["command_digest"],
        "admission_act_ref": act["act_ref"], "admission_act_digest": act["act_digest"],
        "admission_fact_ref": admission["admission_fact_ref"],
        "admission_fact_digest": admission["admission_fact_digest"],
        "continuity_basis_ref": command["continuity_basis_ref"],
        "continuity_basis_digest": command["continuity_basis_digest"],
        "sole_active_basis_ref": command["sole_active_basis_ref"],
        "sole_active_basis_digest": command["sole_active_basis_digest"],
        "decision_ref": family["decision_ref"], "decision_digest": family["decision_digest"],
        "version_ref": family["version_ref"], "version_digest": family["version_digest"],
        "historical_head_ref": family["historical_head_ref"],
        "historical_head_revision": family["historical_head_revision"],
        "historical_head_digest": family["historical_head_digest"],
        "historical_head_postimage": head_row,
        "acceptance_fact_ref": acceptance["acceptance_fact_ref"] if acceptance else None,
        "acceptance_fact_digest": acceptance["acceptance_fact_digest"] if acceptance else None,
        "generic_result_projection_digest": family["generic_result_projection_digest"],
        "family_route": family["family_route"],
    }
    if list(relation) != EXPECTED_SCHEMAS[6][4][:-1]:
        raise ContractViolation("canonical_relation_field_order")
    relation["relation_digest"] = _private_identity_digest(relation["schema_id"], relation)
    family["family_relation"] = relation
    family["relation_digest"] = relation["relation_digest"]
    result = {
        "schema_id": EXPECTED_SCHEMAS[7][1],
        "guarded_result_ref": family["guarded_result_ref"],
        "branch": branch,
        "generic_v1_result_schema_id": V1["generic_result"][0],
        "generic_v1_result_digest": family["generic_result_projection_digest"],
        "family_relation_ref": family["relation_ref"],
        "family_relation_digest": family["relation_digest"],
        "receipt_graph_profile_id": PROFILE_ID,
    }
    result["guarded_result_digest"] = _private_identity_digest(result["schema_id"], result)
    family["guarded_result"] = result
    return family


def _acceptance_fact_fixture(command):
    return _family_fixture("candidate_acceptance", command)["acceptance_fact"]


def _receipt_roles_fixture(branch, fact, command=None):
    family = _family_fixture(branch, command)
    act, admission = _verified_admission_fixture()
    members = {
        "verified_admission_act": (act["act_ref"], act["act_digest"]),
        "scope_admission_fact": (admission["admission_fact_ref"], admission["admission_fact_digest"]),
        "historical_continuity_basis": (FIXED_CURRENT_BASES["continuity_basis_ref"], FIXED_CURRENT_BASES["continuity_basis_digest"]),
        "historical_sole_active_basis": (FIXED_CURRENT_BASES["sole_active_basis_ref"], FIXED_CURRENT_BASES["sole_active_basis_digest"]),
        "decision": (family["decision_ref"], family["decision_digest"]),
        "program_version": (family["version_ref"], family["version_digest"]),
        "historical_head_postimage": (family["historical_head_ref"], family["historical_head_digest"]),
        "generic_v1_result_projection": (family["decision_ref"], family["generic_result_projection_digest"]),
        "guarded_family_relation": (family["relation_ref"], family["relation_digest"]),
        "guarded_result_composite": (family["guarded_result_ref"], family["guarded_result"]["guarded_result_digest"]),
    }
    if fact is not None:
        members["acceptance_fact"] = (fact["acceptance_fact_ref"], fact["acceptance_fact_digest"])
    roles = EXPECTED_COMMON_RECEIPT_ROLES + (("acceptance_fact",) if fact is not None else ())
    return [{"role": role, "ordinal": 0, "record_ref": members[role][0],
             "record_digest": members[role][1]} for role in roles]


def _source_exact_receipt_preimage(command, family):
    value = {
        "schema_id": V1["generic_receipt"][0],
        "mutation_ref": family["mutation_ref"],
        "mutation_family": "record_development_progression_decision",
        "command_schema_id": "governed-execution.nwp-record-development-progression-decision-command.v1",
        "command_digest": family["command_digest"],
        "program_ref": family["program_ref"],
        "decision_ref": family["decision_ref"],
        "result_program_version_ref": family["version_ref"],
        "result_semantic_attempt_ref": None,
        "result_effect_intent_ref": None,
        "result_effect_fence_ref": None,
        "result_delivery_attempt_ref": None,
        "result_observation_ref": None,
        "result_decision_ref": family["decision_ref"],
        "result_class": "development_progression_decision_recorded",
        "result_projection_digest": family["generic_result_projection_digest"],
        "outcome": "committed",
        "committed_at": family["transaction_timestamp"],
    }
    assert list(value) == GRAPH["source_exact_receipt_preimage_fields"]
    return value


def _source_exact_graph_digest(command, family, roles):
    identity = _source_exact_receipt_preimage(command, family)
    identity["graph_entries"] = roles
    return _private_identity_digest(V1["generic_receipt"][0], identity)


def _validate_guarded_result_profile(guarded, branch, family):
    if type(guarded) is not dict or set(guarded) != set(EXPECTED_SCHEMAS[7][4]):
        raise ContractViolation("guarded_result_profile_binding")
    if (guarded["schema_id"] != EXPECTED_SCHEMAS[7][1] or
            guarded["generic_v1_result_schema_id"] != V1["generic_result"][0] or
            guarded["branch"] != branch or guarded["receipt_graph_profile_id"] != PROFILE_ID or
            guarded["guarded_result_ref"] != family["guarded_result_ref"] or
            guarded["family_relation_ref"] != family["relation_ref"] or
            guarded["family_relation_digest"] != family["relation_digest"] or
            guarded["generic_v1_result_digest"] != family["generic_result_projection_digest"]):
        raise ContractViolation("guarded_result_profile_binding")
    if guarded["guarded_result_digest"] != _private_identity_digest(
            guarded["schema_id"], {k: v for k, v in guarded.items()
                                   if k != "guarded_result_digest"}):
        raise ContractViolation("guarded_result_profile_binding")


def _validate_relation_family(branch, relation, fact, receipt_roles, command, selector):
    ref = _validate_fact_assertion(command)
    _validate_selector_instance(selector, command)
    if type(relation) is not dict or list(relation) != EXPECTED_SCHEMAS[6][4]:
        raise ContractViolation("relation_full_field_order")
    if branch not in BRANCHES:
        raise ContractViolation("branch_profile")
    family = _family_fixture(branch, command)
    guarded = family["guarded_result"]
    _validate_guarded_result_profile(guarded, branch, family)
    if family["command_digest"] != _guarded_command_digest_v1(command):
        raise ContractViolation("family_command_digest_binding")
    if family["family_relation"]["command_digest"] != family["command_digest"]:
        raise ContractViolation("relation_command_digest_binding")
    if type(receipt_roles) is not list:
        raise ContractViolation("receipt_role_family")
    if branch == "candidate_acceptance":
        if type(fact) is not dict or list(fact) != EXPECTED_SCHEMAS[5][4]:
            raise ContractViolation("acceptance_fact_membership")
        _, admission = _verified_admission_fixture()
        expected = {
            "schema_id": ACCEPTANCE_SCHEMA,
            "acceptance_fact_ref": ref,
            "lineage_ref": admission["lineage_ref"],
            "scope_ref": admission["scope_ref"],
            "admission_fact_ref": admission["admission_fact_ref"],
            "admission_fact_digest": admission["admission_fact_digest"],
            "mutation_ref": family["mutation_ref"],
            "command_digest": family["command_digest"],
            "decision_ref": family["decision_ref"],
            "decision_digest": family["decision_digest"],
            "version_ref": family["version_ref"],
            "version_digest": family["version_digest"],
            "historical_head_ref": family["historical_head_ref"],
            "historical_head_revision": family["historical_head_revision"],
            "historical_head_digest": family["historical_head_digest"],
            "selected_attempt_ref": family["selected_attempt_ref"],
            "selected_candidate_ref": family["selected_candidate_ref"],
            "basis_ref": family["basis_ref"], "basis_digest": family["basis_digest"],
            "family_route": family["family_route"],
            "accepted_at": family["transaction_timestamp"],
        }
        if type(fact["historical_head_revision"]) is not int or fact["historical_head_revision"] < 0:
            raise ContractViolation("acceptance_fact_head_revision")
        for name, wanted in expected.items():
            if type(fact[name]) is not type(wanted) or fact[name] != wanted:
                raise ContractViolation("acceptance_fact_binding:" + name)
        for name, source in (("lineage_ref", "lineage_ref"), ("scope_ref", "scope_ref"),
                             ("admission_fact_ref", "admission_fact_ref"),
                             ("admission_fact_digest", "admission_fact_digest"),
                             ("decision_ref", "preassigned_decision_ref"),
                             ("version_ref", "preassigned_version_ref"),
                             ("family_route", "family_route")):
            if fact[name] != command[source]:
                raise ContractViolation("acceptance_fact_command_binding:" + name)
        expected_digest = _private_identity_digest(ACCEPTANCE_SCHEMA, expected)
        if type(fact["acceptance_fact_digest"]) is not str or fact["acceptance_fact_digest"] != expected_digest:
            raise ContractViolation("acceptance_fact_digest")
        if relation["acceptance_fact_ref"] != ref:
            raise ContractViolation("relation_fact_ref")
        if relation["acceptance_fact_digest"] != fact["acceptance_fact_digest"]:
            raise ContractViolation("relation_fact_digest")
    else:
        if relation["acceptance_fact_ref"] is not None:
            raise ContractViolation("relation_nonaccept_ref_null")
        if relation["acceptance_fact_digest"] is not None:
            raise ContractViolation("relation_nonaccept_digest_null")
        if fact is not None:
            raise ContractViolation("nonaccept_fact_membership")
    canonical_relation = family["family_relation"]
    for name in EXPECTED_SCHEMAS[6][4][:-1]:
        wanted = canonical_relation[name]
        if type(relation[name]) is not type(wanted) or relation[name] != wanted:
            raise ContractViolation("relation_field_binding:" + name)
    if (type(relation["relation_digest"]) is not str or
            relation["relation_digest"] != _private_identity_digest(
                relation["schema_id"], {name: relation[name] for name in
                                        EXPECTED_SCHEMAS[6][4][:-1]})):
        raise ContractViolation("relation_self_digest")
    # The fixed ordered family is independent from the supplied role list.
    act, admission = _verified_admission_fixture()
    expected_members = (
        (act["act_ref"], act["act_digest"]),
        (admission["admission_fact_ref"], admission["admission_fact_digest"]),
        (FIXED_CURRENT_BASES["continuity_basis_ref"], FIXED_CURRENT_BASES["continuity_basis_digest"]),
        (FIXED_CURRENT_BASES["sole_active_basis_ref"], FIXED_CURRENT_BASES["sole_active_basis_digest"]),
        (family["decision_ref"], family["decision_digest"]),
        (family["version_ref"], family["version_digest"]),
        (family["historical_head_ref"], family["historical_head_digest"]),
        (family["decision_ref"], family["generic_result_projection_digest"]),
        (family["relation_ref"], family["relation_digest"]),
        (family["guarded_result_ref"], guarded["guarded_result_digest"]),
    )
    expected_roles = [
        {"role": role, "ordinal": 0, "record_ref": member[0], "record_digest": member[1]}
        for role, member in zip(EXPECTED_COMMON_RECEIPT_ROLES, expected_members, strict=True)
    ]
    if branch == "candidate_acceptance":
        expected_roles.append({"role": "acceptance_fact", "ordinal": 0,
                               "record_ref": fact["acceptance_fact_ref"],
                               "record_digest": fact["acceptance_fact_digest"]})
    _exact(receipt_roles, expected_roles, "receipt_role_family")
    if selector["acceptance_fact_ref"] != ref or selector["required_collision_routes"][3]["key"] != [ref]:
        raise ContractViolation("reserved_fact_route")
    return _source_exact_graph_digest(command, family, receipt_roles)


def test_fixed_prospective_fact_preimage_and_digest():
    command = _command_coordinates()
    preimage = _fixed_preimage_bytes(command)
    assert json.loads(preimage) == [[name, command["schema_id" if name == "command_profile" else name]]
                                    for name in PRIMITIVE_NAMES]
    assert len(json.loads(preimage)) == 24
    assert PROSPECTIVE_DOMAIN != ACCEPTANCE_SCHEMA + ".identity"
    assert _fixed_fact_ref(command) == "e45e55113d63769b1a4a157aa5a0d8a1621516ba5b81155535f1116af66e8f17"
    _, p = _document()
    _exact(p["prospective_fact_identity"], PROSPECTIVE, "prospective_fact_identity")
    _exact(p["prospective_fact_identity"]["ordered_preimage"], PREIMAGE, "prospective_fact_identity")


@pytest.mark.parametrize("coordinate", PRIMITIVE_NAMES)
def test_every_preimage_coordinate_changes_fact_ref(coordinate):
    command = _command_coordinates()
    original = _fixed_fact_ref(command)
    coordinate = "schema_id" if coordinate == "command_profile" else coordinate
    if coordinate == "expected_head_revision":
        command[coordinate] += 1
    elif coordinate.endswith("_digest"):
        command[coordinate] = "12" * 32
    else:
        command[coordinate] += "-changed"
    changed = _fixed_fact_ref(command)
    assert changed != original


@pytest.mark.parametrize("excluded", PROSPECTIVE["preimage_excludes"])
def test_postreduction_and_postcommit_values_do_not_enter_fact_preimage(excluded):
    command = _command_coordinates()
    original = _fixed_fact_ref(command)
    command[excluded] = "changed-but-prohibited"
    assert _fixed_fact_ref(command) == original


@pytest.mark.parametrize("bad", [None, True, 1, "", "wrong", "f" * 64])
def test_null_or_invalid_fact_coordinate_is_command_grammar_error(bad):
    command = _command_coordinates()
    command["preassigned_acceptance_fact_ref"] = bad
    boundary = "prospective_fact_identity" if bad == "f" * 64 else "fact_command_grammar"
    with pytest.raises(ContractViolation) as error:
        _validate_fact_assertion(command)
    assert error.value.boundary == boundary


def test_omitted_fact_coordinate_cannot_veto_acceptance():
    command = _command_coordinates()
    del command["preassigned_acceptance_fact_ref"]
    with pytest.raises(ContractViolation) as error:
        _validate_fact_assertion(command)
    assert error.value.boundary == "fact_command_grammar"


@pytest.mark.parametrize("coordinate,value", [("lineage_ref", None), ("scope_ref", 7),
                                            ("admission_fact_digest", "AB" * 32),
                                            ("guard_profile", ""),
                                            ("expected_head_revision", True)])
def test_fact_preimage_types_are_exact(coordinate, value):
    command = _command_coordinates()
    command[coordinate] = value
    with pytest.raises(ContractViolation) as error:
        _fixed_fact_ref(command)
    assert error.value.boundary == "prospective_fact_preimage_type"


@pytest.mark.parametrize("branch", list(BRANCHES))
def test_branch_neutral_fact_truth_table(branch):
    command = _command_coordinates()
    ref = _fixed_fact_ref(command)
    command["preassigned_acceptance_fact_ref"] = ref
    selector = _selector_instance(command)
    assert selector["acceptance_fact_ref"] == ref
    assert selector["required_collision_routes"][3]["key"] == [ref]
    fact_refs = [ref] if branch == "candidate_acceptance" else []
    _validate_branch_members(branch, fact_refs, command, selector)
    assert BRANCHES[branch][2] == len(fact_refs)


@pytest.mark.parametrize("branch,facts", [("candidate_acceptance", []),
                                         ("candidate_repair", ["reserved"]),
                                         ("attempt_selecting_replan", ["reserved"]),
                                         ("program_terminal_reject", ["reserved"]),
                                         ("post_execution_program_block", ["reserved"])])
def test_wrong_branch_fact_membership_is_rejected(branch, facts):
    command = _command_coordinates()
    command["preassigned_acceptance_fact_ref"] = _fixed_fact_ref(command)
    selector = _selector_instance(command)
    with pytest.raises(ContractViolation) as error:
        _validate_branch_members(branch, facts, command, selector)
    assert error.value.boundary == "branch_fact_membership"


def test_coordinate_cannot_force_another_branch():
    command = _command_coordinates()
    command["preassigned_acceptance_fact_ref"] = _fixed_fact_ref(command)
    selector = _selector_instance(command)
    for branch in BRANCHES:
        _validate_branch_members(branch, [command["preassigned_acceptance_fact_ref"]]
                                 if branch == "candidate_acceptance" else [], command, selector)
    assert PROSPECTIVE["caller_selects_branch"] is False


@pytest.mark.parametrize("role", [route["role"] for route in ROUTES])
def test_every_closed_route_blocks_total_absence_when_occupied(role):
    command = _command_coordinates()
    command["preassigned_acceptance_fact_ref"] = _fixed_fact_ref(command)
    selector = _selector_instance(command)
    observations = {route["role"]: "absent" for route in ROUTES}
    observations[role] = "occupied"
    with pytest.raises(ContractViolation) as error:
        _require_total_absence(selector, observations,
                               current_continuity=True, current_sole_active=True)
    assert error.value.boundary == ("reserved_fact_collision" if role == "acceptance_fact_identity_route"
                                    else "recovery_route_coverage")


@pytest.mark.parametrize("posture", [(True, True), (False, True), (True, False), (False, False)])
def test_total_absence_needs_both_current_postures(posture):
    command = _command_coordinates()
    command["preassigned_acceptance_fact_ref"] = _fixed_fact_ref(command)
    selector = _selector_instance(command)
    observations = {route["role"]: "absent" for route in ROUTES}
    if posture == (True, True):
        _require_total_absence(selector, observations,
                               current_continuity=posture[0], current_sole_active=posture[1])
    else:
        with pytest.raises(ContractViolation) as error:
            _require_total_absence(selector, observations,
                                   current_continuity=posture[0], current_sole_active=posture[1])
        assert error.value.boundary == "recovery_current_posture"


@pytest.mark.parametrize("fault", ["malformed", "foreign", "unreadable", "unchecked", "partial", "orphan"])
def test_route_fault_or_partial_member_cannot_prove_absence(fault):
    command = _command_coordinates()
    command["preassigned_acceptance_fact_ref"] = _fixed_fact_ref(command)
    selector = _selector_instance(command)
    observations = {route["role"]: "absent" for route in ROUTES}
    observations["decision_identity_route"] = fault
    with pytest.raises(ContractViolation) as error:
        _require_total_absence(selector, observations,
                               current_continuity=True, current_sole_active=True)
    assert error.value.boundary == "recovery_route_coverage"


SELECTOR_MUTANTS = [
    ("missing_route", "selector_route_inventory"),
    ("duplicate_route", "selector_route_inventory"),
    ("unknown_route", "selector_route_inventory"),
    ("reordered_route", "selector_route_inventory"),
    ("missing_acceptance_route", "selector_route_inventory"),
    ("missing_scope_winner_route", "selector_route_inventory"),
    ("additional_implementation_route", "selector_route_inventory"),
    ("null_coordinate", "selector_route_element_grammar"),
    ("wrong_key_type", "selector_route_element_grammar"),
    ("wrong_scope_key_order", "selector_route_coordinate_binding"),
    ("coordinate_from_other_role", "selector_route_coordinate_binding"),
    ("wrong_route_kind", "selector_route_element_grammar"),
    ("wrong_schema_version", "selector_route_schema"),
    ("extra_element_field", "selector_route_element_grammar"),
    ("template_field_in_concrete", "selector_route_element_grammar"),
    ("null_record_schema", "selector_route_schema"),
    ("missing_element_field", "selector_route_element_grammar"),
    ("timestamp_dependency", "recovery_selector_closed"),
    ("final_receipt_dependency", "recovery_selector_closed"),
]


@pytest.mark.parametrize("name,boundary", SELECTOR_MUTANTS,
                         ids=[name for name, _ in SELECTOR_MUTANTS])
def test_closed_route_instance_rejects_hostile_shape(name, boundary):
    command = _command_coordinates()
    command["preassigned_acceptance_fact_ref"] = _fixed_fact_ref(command)
    selector = _selector_instance(command)
    routes = selector["required_collision_routes"]
    if name in {"missing_route", "missing_acceptance_route", "missing_scope_winner_route"}:
        index = {"missing_route": 1, "missing_acceptance_route": 3,
                 "missing_scope_winner_route": 7}[name]
        routes.pop(index)
    elif name == "duplicate_route":
        routes[1] = deepcopy(routes[0])
    elif name == "unknown_route":
        routes[1]["role"] = "implementation_specific_route"
    elif name == "reordered_route":
        routes[0], routes[1] = routes[1], routes[0]
    elif name == "additional_implementation_route":
        routes.append({"role": "implementation_specific_route", "kind": "preassigned_identity",
                       "key": ["extra"], "expected_schema_id": None})
    elif name == "null_coordinate":
        routes[3]["key"] = [None]
    elif name == "wrong_key_type":
        routes[3]["key"] = selector["acceptance_fact_ref"]
    elif name == "wrong_scope_key_order":
        routes[7]["key"] = list(reversed(routes[7]["key"]))
    elif name == "coordinate_from_other_role":
        routes[3]["key"] = routes[2]["key"][:]
    elif name == "wrong_route_kind":
        routes[3]["kind"] = "receipt_replay"
    elif name == "wrong_schema_version":
        routes[3]["expected_schema_id"] = ACCEPTANCE_SCHEMA + ".other"
    elif name == "extra_element_field":
        routes[3]["hint"] = "caller supplied"
    elif name == "template_field_in_concrete":
        routes[3]["key_sources"] = ["acceptance_fact_ref"]
    elif name == "null_record_schema":
        routes[3]["expected_schema_id"] = None
    elif name == "missing_element_field":
        del routes[3]["kind"]
    elif name == "timestamp_dependency":
        selector["transaction_timestamp"] = "postcommit"
    elif name == "final_receipt_dependency":
        selector["receipt_digest"] = "ab" * 32
    with pytest.raises(ContractViolation) as error:
        _validate_selector_instance(selector)
    assert error.value.boundary == boundary


def test_closed_route_templates_have_exact_roles_kinds_sources_and_versions():
    _, observed = _document()
    _exact(observed["collision_route_templates"], ROUTES, "collision_route_templates")
    _exact(observed["selector"], SELECTOR, "recovery_selector")
    assert len(ROUTES) == 8
    assert len({route["role"] for route in ROUTES}) == 8
    assert [route["role"] for route in ROUTES][3] == "acceptance_fact_identity_route"
    assert [route["role"] for route in ROUTES][-1] == "admitted_scope_winner_route"
    assert [route["expected_schema_id"] is None for route in ROUTES] == [False] * 6 + [True, True]


@pytest.mark.parametrize("fault", ["concrete_key_in_template", "template_missing", "template_duplicate",
                                   "template_unknown", "template_reordered", "template_extension"])
def test_route_template_negative_controls(fault):
    _, profile = _document()
    changed = deepcopy(profile)
    routes = changed["collision_route_templates"]
    if fault == "concrete_key_in_template":
        routes[3]["key"] = ["invented"]
    elif fault == "template_missing":
        routes.pop(3)
    elif fault == "template_duplicate":
        routes[3] = deepcopy(routes[2])
    elif fault == "template_unknown":
        routes[3]["role"] = "implementation_route"
    elif fault == "template_reordered":
        routes[2], routes[3] = routes[3], routes[2]
    else:
        routes.append(deepcopy(routes[3]))
    with pytest.raises(ContractViolation) as error:
        _validate(changed)
    assert error.value.boundary == "collision_route_templates"


def test_concrete_selector_route_instantiation_is_exact_and_tuple_safe():
    selector = _selector_instance(_command_coordinates())
    _validate_selector_instance(selector)
    _exact([(row["role"], row["kind"], row["key"], row["expected_schema_id"])
            for row in selector["required_collision_routes"]],
           EXPECTED_CONCRETE_ROUTES, "fixed_concrete_routes")
    for concrete, template in zip(selector["required_collision_routes"], ROUTES, strict=True):
        assert set(concrete) == {"role", "kind", "key", "expected_schema_id"}
        assert concrete["key"] == [selector[field] for field in template["key_sources"]]
        assert all(type(value) is str for value in concrete["key"])
    assert [len(row["key"]) for row in selector["required_collision_routes"]] == [1] * 7 + [4]
    selector["required_collision_routes"][7]["key"] = tuple(selector["required_collision_routes"][7]["key"])
    with pytest.raises(ContractViolation) as error:
        _validate_selector_instance(selector)
    assert error.value.boundary == "selector_route_element_grammar"


def test_prose_route_table_is_independent_of_machine_and_concrete_routes():
    text, p = _document()
    section = text.split("| Role | Kind | Ordered source coordinates | Expected schema |\n", 1)[1]
    section = section.split("\n\n", 1)[0]
    lines = section.splitlines()
    assert lines.pop(0) == "|---|---|---|---|"
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip("| ").split("|")]
        if len(cells) != 4:
            raise ContractViolation("prose_route_table")
        values = [re.findall(r"\x60([^\x60]+)\x60", cell) for cell in cells]
        if len(values[0]) != 1 or len(values[1]) != 1 or len(values[3]) != 1:
            raise ContractViolation("prose_route_table")
        rows.append((values[0][0], values[1][0], tuple(values[2]),
                     None if values[3][0] == "null" else values[3][0]))
    _exact(rows, EXPECTED_PROSE_ROUTE_ROWS, "prose_route_table")
    _exact(p["collision_route_templates"], ROUTES, "collision_route_templates")


@pytest.mark.parametrize("field,wanted", [
    ("exact_complete_original_class", "committed_exact"),
    ("same_mutation_different_digest_reason", "mutation_ref_reuse_conflict"),
    ("identity_or_family_route_collision_reason", "preassigned_identity_or_family_route_collision"),
    ("total_absence_class", "definitely_not_committed"),
    ("total_absence_requires_all_routes_checked", True),
    ("total_absence_requires_positive_current_continuity", True),
    ("total_absence_requires_positive_current_sole_active", True),
    ("local_absence_without_current_posture_class", "unresolved"),
    ("missing_malformed_unreadable_foreign_duplicate_unchecked_route_class", "unresolved"),
    ("partial_or_orphan_fact_class", "unresolved"),
    ("different_complete_winner_can_prove_original_noncommit", True),
    ("different_complete_winner_fresh_acceptance_eligible", False),
    ("fresh_retry_eligibility_separate", True),
    ("fragment_repair", False), ("branch_reevaluation", False),
    ("automatic_retry", False), ("scope_renewal", False),
])
def test_recovery_evidence_profile_is_decision_owned(field, wanted):
    _, observed = _document()
    _exact(observed["recovery"][field], wanted, "recovery_value")


def test_exact_replay_preserves_original_fact_and_timestamp():
    _, observed = _document()
    _exact(observed["replay"], REPLAY, "replay_value")
    assert "original_optional_acceptance_fact" in REPLAY["returns"]
    assert "original_transaction_timestamp" in REPLAY["returns"]
    assert REPLAY["new_fact"] is REPLAY["new_timestamp"] is False


PROSE_HOSTILE = [
    ("historical_basis_non_authority", "Retained historical continuity and sole-active bases are current standing permission."),
    ("current_external_posture", "Protected replay and recovery may use retained historical posture alone."),
    ("mandatory_prospective_fact_coordinate", "The fact coordinate is optional and may be null."),
    ("branch_nonselection", "Caller null vetoes acceptance and non-null forces acceptance."),
    ("nonaccept_fact_collision", "Nonaccept skips the fact collision probe."),
    ("closed_collision_routes", "Implementations may omit or extend collision routes."),
    ("total_absence_currentness", "Local absence proves definitely_not_committed without current continuity."),
    ("replay_original_fact_timestamp", "Replay creates a new fact and refreshes the transaction timestamp."),
    ("admitted_scope_only", "A command relation may select an unadmitted scope."),
]


@pytest.mark.parametrize("boundary,hostile", PROSE_HOSTILE,
                         ids=[boundary for boundary, _ in PROSE_HOSTILE])
def test_hostile_normative_prose_mutation_fails_named_boundary(boundary, hostile):
    text, _ = _document()
    original = _normative_prefix(boundary) + PROSE_CLAUSES[boundary]
    assert text.count(original) == 1
    mutated = text.replace(original, _normative_prefix(boundary) + hostile)
    clauses = _normative_clauses(mutated)
    with pytest.raises(ContractViolation) as error:
        _exact(clauses[boundary], PROSE_CLAUSES[boundary], boundary)
    assert error.value.boundary == boundary


def test_exact_primitive_basis_six_sibling_vectors_and_complete_dag():
    _, profile = _document()
    _validate_preassignment_basis(profile["preassignment_basis"])
    _validate_siblings(profile["preassignment_siblings"])
    order = _validate_dependency_registry(profile["dependency_registry"])
    assert set(order) == set(BRANCHES)
    assert all(len(order[branch]) == profile["dependency_registry"]["expanded_counts"][branch]["nodes"]
               for branch in BRANCHES)
    assert profile["dependency_registry"]["node_count"] == len(EXPECTED_DEPENDENCY_REGISTRY["nodes"])
    assert profile["dependency_registry"]["common_edge_count"] == sum(
        len(row["common_dependencies"]) for row in profile["dependency_registry"]["nodes"])
    assert all(order[b].index("guarded_family_preassignment_basis_v1") < order[b].index("command_digest")
               for b in BRANCHES)
    command = _command_coordinates()
    assert _derive_siblings(command) == {field: vector for _, field, _, vector in SIBLING_SPECS}
    assert all(re.fullmatch(r"[0-9a-f]{64}", value) for value in _derive_siblings(command).values())
    assert _validate_command_relation(command, *_verified_admission_fixture()) is command
    assert profile["command_digest"]["includes"] == PRIMITIVE_NAMES + [
        "preassigned_decision_ref", "preassigned_version_ref",
        "preassigned_acceptance_fact_ref", "preassigned_relation_ref",
        "preassigned_guarded_result_ref", "family_route"]


@pytest.mark.parametrize("coordinate", PRIMITIVE_NAMES)
def test_every_primitive_changes_every_independent_sibling(coordinate):
    original = _command_coordinates()
    changed = deepcopy(original)
    coordinate = "schema_id" if coordinate == "command_profile" else coordinate
    if coordinate == "expected_head_revision":
        changed[coordinate] += 1
    elif coordinate.endswith("_digest"):
        changed[coordinate] = "12" * 32
    else:
        changed[coordinate] += "-changed"
    before, after = _derive_siblings(original), _derive_siblings(changed)
    assert set(before) == set(after) == {field for _, field, _, _ in SIBLING_SPECS}
    assert all(before[field] != after[field] for field in before)
    changed.update(after)
    assert _guarded_command_digest_v1(changed) != _guarded_command_digest_v1(original)
    assert _private_identity_digest(changed["schema_id"],
        {key: value for key, value in changed.items() if key != "relation_digest"}) != original["relation_digest"]


@pytest.mark.parametrize("excluded", [
    "authoritative_branch", "generic_result", "receipt_digest", "transaction_timestamp",
    "terminal_outcome", "postcommit_head", "raw_external_credential",
])
def test_postbranch_and_external_raw_values_cannot_enter_any_sibling(excluded):
    command = _command_coordinates()
    before = _derive_siblings(command)
    command[excluded] = "hostile"
    assert _derive_siblings(command) == before


@pytest.mark.parametrize("sibling", [name for name, *_ in SIBLING_SPECS])
def test_every_sibling_rejects_command_digest_backedge(sibling):
    _, profile = _document()
    changed = deepcopy(profile["dependency_registry"])
    row = next(row for row in changed["nodes"] if row["node"] == "sibling:" + sibling)
    row["common_dependencies"].append("command_digest")
    with pytest.raises(ContractViolation) as error:
        _validate_dependency_registry(changed)
    assert error.value.boundary == "dependency_forbidden_backedge"


@pytest.mark.parametrize("sibling", [name for name, *_ in SIBLING_SPECS])
def test_command_digest_cannot_be_omitted_from_sibling_downstream_edge(sibling):
    _, profile = _document()
    changed = deepcopy(profile["dependency_registry"])
    row = next(row for row in changed["nodes"] if row["node"] == "command_digest")
    row["common_dependencies"].remove("sibling:" + sibling)
    with pytest.raises(ContractViolation) as error:
        _validate_dependency_registry(changed)
    assert error.value.boundary == "dependency_exact_edges"


@pytest.mark.parametrize("fault,boundary", [
    ("drop_node", "dependency_inventory"),
    ("omit_basis_input", "dependency_exact_edges"),
    ("unknown_origin", "dependency_origin_class"),
    ("stage_inversion", "dependency_stage_or_cycle"),
    ("sibling_from_sibling", "dependency_forbidden_backedge"),
    ("relation_from_own_digest", "dependency_stage_or_cycle"),
    ("aggregate_digest_backedge", "dependency_forbidden_backedge"),
])
def test_expanded_dag_negative_controls(fault, boundary):
    _, profile = _document()
    changed = deepcopy(profile["dependency_registry"])
    rows = {row["node"]: row for row in changed["nodes"]}
    if fault == "drop_node":
        changed["nodes"].remove(rows["primitive:program_ref"])
    elif fault == "omit_basis_input":
        rows["guarded_family_preassignment_basis_v1"]["common_dependencies"].remove("primitive:program_ref")
    elif fault == "unknown_origin":
        rows["primitive:program_ref"]["origin_class"] = "hidden_aggregate"
    elif fault == "stage_inversion":
        rows["command_digest"]["stage"] = 3
    elif fault == "sibling_from_sibling":
        rows["sibling:preassigned_decision_ref"]["common_dependencies"].append(
            "sibling:preassigned_resulting_program_version_ref")
    elif fault == "relation_from_own_digest":
        rows["family_relation_value"]["common_dependencies"].append("family_relation_digest")
    else:
        rows["guarded_family_preassignment_basis_v1"]["common_dependencies"].append("generic_receipt_graph_digest")
    with pytest.raises(ContractViolation) as error:
        _validate_dependency_registry(changed)
    assert error.value.boundary == boundary


@pytest.mark.parametrize("field", ADMISSION_BINDING["command_equalities"])
def test_independent_verified_admission_rejects_every_command_mismatch(field):
    act, fact = _verified_admission_fixture()
    command = _command_coordinates()
    _validate_command_relation(command, act, fact)
    changed = deepcopy(command)
    changed[field] = ("12" * 32 if field.endswith("_digest") else "foreign")
    with pytest.raises(ContractViolation) as error:
        _validate_command_relation(changed, act, fact)
    assert error.value.boundary == "admission_binding:" + field


def _load_c2_shared():
    path = ROOT / "tests/test_rw0_c2_durable_progression_decision_semantic_contract.py"
    spec = importlib.util.spec_from_file_location("rw0_c2_shared_contract_interpreter", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixed_admission_vector_independently_binds_command_and_fact():
    act, fact = _verified_admission_fixture()
    _exact(act, EXPECTED_ADMISSION_ACT, "fixed_admission_act_vector")
    _exact(fact, EXPECTED_ADMISSION_FACT, "fixed_admission_fact_vector")
    command = _command_coordinates()
    assert command["admission_fact_digest"] == EXPECTED_ADMISSION_FACT["admission_fact_digest"]
    assert command["admission_act_ref"] == EXPECTED_ADMISSION_ACT["act_ref"]


@pytest.mark.parametrize("field", ["lineage_ref", "scope_ref", "admission_fact_ref",
                                   "admission_fact_digest", "guard_profile", "applicability",
                                   "continuity_source_ref", "continuity_source_digest",
                                   "sole_active_source_ref", "sole_active_source_digest"])
def test_invalid_admission_never_enters_shared_interpreter(field):
    c2 = _load_c2_shared()
    state = c2._state_for_authoritative_branch(c2.EXPECTED_CONTRACT,
                                                "candidate_acceptance")
    act, fact = _verified_admission_fixture()
    command = _command_coordinates()
    command[field] = "12" * 32 if field.endswith("_digest") else "foreign"
    entered = []
    original = c2._interpret

    def sentinel(*args, **kwargs):
        entered.append((args, kwargs))
        raise RuntimeError("C2_SHARED_INTERPRETER_SENTINEL")

    try:
        c2._interpret = sentinel
        with pytest.raises(ContractViolation) as error:
            _private_branch_path(c2, command, act, fact, state, fresh_posture=deepcopy(FRESH_POSTURE_VECTOR))
        assert error.value.boundary.startswith(("admission_binding:",
                                                "current_basis_binding:"))
        assert entered == []
    finally:
        c2._interpret = original


def test_valid_admission_enters_live_shared_interpreter_once():
    c2 = _load_c2_shared()
    state = c2._state_for_authoritative_branch(c2.EXPECTED_CONTRACT,
                                                "candidate_acceptance")
    act, fact = _verified_admission_fixture()
    command = _command_coordinates()
    entered = []
    original = c2._interpret

    def sentinel(*args, **kwargs):
        entered.append((args, kwargs))
        raise RuntimeError("C2_SHARED_INTERPRETER_SENTINEL")

    try:
        c2._interpret = sentinel
        with pytest.raises(RuntimeError, match="^C2_SHARED_INTERPRETER_SENTINEL$"):
            _private_branch_path(c2, command, act, fact, state, fresh_posture=deepcopy(FRESH_POSTURE_VECTOR))
        assert len(entered) == 1
    finally:
        c2._interpret = original


def test_joint_act_fact_command_and_sibling_mutation_fails_fixed_oracle():
    act, fact = _verified_admission_fixture()
    command = _command_coordinates()
    act["lineage_ref"] = fact["lineage_ref"] = command["lineage_ref"] = "foreign-lineage"
    act["projection_digest"] = _private_identity_digest(act["schema_id"],
        {key: value for key, value in act.items() if key != "projection_digest"})
    fact["admission_fact_digest"] = _private_identity_digest(fact["schema_id"],
        {key: value for key, value in fact.items() if key != "admission_fact_digest"})
    command["admission_fact_digest"] = fact["admission_fact_digest"]
    command.update(_derive_siblings(command))
    command["relation_digest"] = _private_identity_digest(command["schema_id"],
        {key: value for key, value in command.items() if key != "relation_digest"})
    with pytest.raises(ContractViolation) as error:
        _validate_prebranch_admission(command, act, fact, fresh_posture=deepcopy(FRESH_POSTURE_VECTOR))
    assert error.value.boundary == "fixed_admission_act_vector"


@pytest.mark.parametrize("branch", list(BRANCHES))
def test_shared_c2_interpreter_branch_neutrality_and_relation_truth_table(branch):
    c2 = _load_c2_shared()
    state = c2._state_for_authoritative_branch(c2.EXPECTED_CONTRACT, branch)
    assert "preassigned_acceptance_fact_ref" not in state
    assert "prospective_acceptance_fact_ref" not in state
    act, fact = _verified_admission_fixture()
    baseline = _command_coordinates()
    for coordinate in (None, "12" * 32, baseline["preassigned_acceptance_fact_ref"]):
        command = deepcopy(baseline)
        command["preassigned_acceptance_fact_ref"] = coordinate
        if coordinate != baseline["preassigned_acceptance_fact_ref"]:
            with pytest.raises(ContractViolation):
                _private_branch_path(c2, command, act, fact, deepcopy(state), fresh_posture=deepcopy(FRESH_POSTURE_VECTOR))
            continue
        derived_branch = _private_branch_path(c2, command, act, fact, deepcopy(state), fresh_posture=deepcopy(FRESH_POSTURE_VECTOR))
        assert derived_branch["branch"] == branch
        assert derived_branch["family"]["guarded_result"]["branch"] == branch
        selector = _selector_instance(command)
        actual_fact = (_acceptance_fact_fixture(command)
                       if branch == "candidate_acceptance" else None)
        relation = deepcopy(derived_branch["family"]["family_relation"])
        roles = _receipt_roles_fixture(derived_branch["branch"], actual_fact)
        _validate_relation_family(derived_branch["branch"], relation, actual_fact, roles, command, selector)
        assert selector["required_collision_routes"][3]["key"] == [coordinate]


def test_private_branch_verifier_structurally_calls_existing_c2_interpreter():
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "_private_branch_path")
    calls = {ast.unparse(node.func) for node in ast.walk(function) if isinstance(node, ast.Call)}
    if ("c2._interpret" not in calls or
            "_validate_prebranch_admission" not in calls or
            "_validate_command_relation" not in calls or
            not any(isinstance(node, ast.Subscript) and ast.unparse(node) == "observation['branch']"
                    for node in ast.walk(function)) or
            any(isinstance(node, ast.FunctionDef) and node.name in
                {"_interpret", "_reduce_branch", "_branch_precedence"}
                for node in tree.body)):
        raise ContractViolation("shared_c2_interpreter_boundary")


RELATION_FAULT_CASES = [
    (branch, fault, boundary)
    for branch in BRANCHES
    for fault, boundary in [
        ("nonaccept_ref", "relation_nonaccept_ref_null"),
        ("nonaccept_digest", "relation_nonaccept_digest_null"),
        ("acceptance_null", "relation_fact_ref"),
        ("missing_fact", "acceptance_fact_membership"),
        ("extra_fact", "nonaccept_fact_membership"),
        ("extra_role", "receipt_role_family"),
    ]
    if ((branch == "candidate_acceptance" and fault in
         {"acceptance_null", "missing_fact", "extra_role"}) or
        (branch != "candidate_acceptance" and fault in
         {"nonaccept_ref", "nonaccept_digest", "extra_fact", "extra_role"}))
]


@pytest.mark.parametrize("branch,fault,boundary", RELATION_FAULT_CASES)
def test_relation_fact_field_negative_controls(branch, fault, boundary):
    command = _command_coordinates()
    selector = _selector_instance(command)
    ref = command["preassigned_acceptance_fact_ref"]
    fact = _acceptance_fact_fixture(command) if branch == "candidate_acceptance" else None
    relation = deepcopy(_family_fixture(branch, command)["family_relation"])
    roles = _receipt_roles_fixture(branch, fact)
    if fault == "nonaccept_ref": relation["acceptance_fact_ref"] = ref
    elif fault == "nonaccept_digest": relation["acceptance_fact_digest"] = "bc" * 32
    elif fault == "acceptance_null": relation["acceptance_fact_ref"] = None
    elif fault == "missing_fact": fact = None
    elif fault == "extra_fact": fact = _acceptance_fact_fixture(command)
    elif fault == "extra_role": roles = roles + [deepcopy(roles[-1])]
    with pytest.raises(ContractViolation) as error:
        _validate_relation_family(branch, relation, fact, roles, command, selector)
    assert error.value.boundary == boundary


@pytest.mark.parametrize("branch", list(BRANCHES))
def test_exact_common_family_and_source_v1_graph_digest(branch):
    command = _command_coordinates()
    selector = _selector_instance(command)
    fact = _acceptance_fact_fixture(command) if branch == "candidate_acceptance" else None
    roles = _receipt_roles_fixture(branch, fact)
    expected_names = EXPECTED_COMMON_RECEIPT_ROLES + (("acceptance_fact",)
                     if branch == "candidate_acceptance" else ())
    assert tuple(row["role"] for row in roles) == expected_names
    relation = deepcopy(_family_fixture(branch, command)["family_relation"])
    graph_digest = _validate_relation_family(branch, relation, fact, roles, command, selector)
    assert graph_digest == EXPECTED_SOURCE_GRAPH_DIGESTS[branch]
    changed = _family_fixture(branch)
    changed["transaction_timestamp"] = "2026-01-01T00:00:01Z"
    assert _source_exact_graph_digest(command, changed, roles) != graph_digest


@pytest.mark.parametrize("field,value,boundary", [
    ("scope_ref", "foreign-scope", "acceptance_fact_binding:scope_ref"),
    ("lineage_ref", "foreign-lineage", "acceptance_fact_binding:lineage_ref"),
    ("admission_fact_ref", "foreign-admission", "acceptance_fact_binding:admission_fact_ref"),
    ("admission_fact_digest", "12" * 32, "acceptance_fact_binding:admission_fact_digest"),
    ("decision_ref", "foreign-decision", "acceptance_fact_binding:decision_ref"),
    ("version_ref", "foreign-version", "acceptance_fact_binding:version_ref"),
    ("historical_head_ref", "foreign-head", "acceptance_fact_binding:historical_head_ref"),
    ("historical_head_digest", "12" * 32, "acceptance_fact_binding:historical_head_digest"),
    ("historical_head_revision", True, "acceptance_fact_head_revision"),
    ("accepted_at", "2026-01-01T00:00:01Z", "acceptance_fact_binding:accepted_at"),
])
def test_recomputed_hostile_acceptance_fact_cannot_escape_owner_binding(field, value, boundary):
    command = _command_coordinates()
    selector = _selector_instance(command)
    fact = _acceptance_fact_fixture(command)
    roles = _receipt_roles_fixture("candidate_acceptance", fact)
    relation = deepcopy(_family_fixture("candidate_acceptance", command)["family_relation"])
    fact[field] = value
    fact["acceptance_fact_digest"] = _private_identity_digest(ACCEPTANCE_SCHEMA,
        {k: v for k, v in fact.items() if k != "acceptance_fact_digest"})
    with pytest.raises(ContractViolation) as error:
        _validate_relation_family("candidate_acceptance", relation, fact, roles, command, selector)
    assert error.value.boundary == boundary


@pytest.mark.parametrize("branch,fault", [
    ("candidate_acceptance", "acceptance_only"),
    ("candidate_acceptance", "omit_common"),
    ("candidate_acceptance", "duplicate_common"),
    ("candidate_acceptance", "substitute_common"),
    ("candidate_acceptance", "reorder_common"),
    ("candidate_acceptance", "omit_acceptance"),
    ("candidate_repair", "extra_acceptance"),
])
def test_complete_receipt_role_family_rejects_missing_duplicate_or_substitution(branch, fault):
    command = _command_coordinates()
    selector = _selector_instance(command)
    fact = _acceptance_fact_fixture(command) if branch == "candidate_acceptance" else None
    roles = _receipt_roles_fixture(branch, fact)
    relation = deepcopy(_family_fixture(branch, command)["family_relation"])
    if fault == "acceptance_only": roles[:] = roles[-1:]
    elif fault == "omit_common": roles.pop(2)
    elif fault == "duplicate_common": roles.insert(2, deepcopy(roles[2]))
    elif fault == "substitute_common": roles[2]["record_digest"] = "12" * 32
    elif fault == "reorder_common": roles[1], roles[2] = roles[2], roles[1]
    elif fault == "omit_acceptance": roles.pop()
    else:
        roles.append({"role": "acceptance_fact", "ordinal": 0,
                      "record_ref": command["preassigned_acceptance_fact_ref"],
                      "record_digest": "12" * 32})
    with pytest.raises(ContractViolation) as error:
        _validate_relation_family(branch, relation, fact, roles, command, selector)
    assert error.value.boundary == "receipt_role_family"


def test_guarded_result_profile_id_is_bound_before_source_graph_hash():
    family = _family_fixture("candidate_acceptance")
    guarded = family["guarded_result"]
    _validate_guarded_result_profile(guarded, "candidate_acceptance", family)
    changed = deepcopy(guarded)
    changed["receipt_graph_profile_id"] = PROFILE_ID + ".other"
    changed["guarded_result_digest"] = _private_identity_digest(changed["schema_id"],
        {k: v for k, v in changed.items() if k != "guarded_result_digest"})
    assert changed["guarded_result_digest"] != guarded["guarded_result_digest"]
    with pytest.raises(ContractViolation) as error:
        _validate_guarded_result_profile(changed, "candidate_acceptance", family)
    assert error.value.boundary == "guarded_result_profile_binding"

# This sentinel is deliberately separate from the target family builder. Its
# optional fields are all distinct so that a same-typed cross-field mapping in
# the unchanged current-v1 graph owner cannot evade the comparison.
SOURCE_RECEIPT_SENTINEL = (
    "governed-execution.nwp-development-mutation-receipt.v1",
    "mutation-sentinel-01", "record_development_progression_decision",
    "governed-execution.nwp-record-development-progression-decision-command.v1",
    "01" * 32, "program-sentinel-02", "decision-sentinel-03",
    "version-sentinel-04", "attempt-sentinel-05", "intent-sentinel-06",
    "fence-sentinel-07", "delivery-sentinel-08", "observation-sentinel-09",
    "result-decision-sentinel-10", "development_progression_decision_recorded",
    "02" * 32, "03" * 32, "committed", "2026-01-02T03:04:05Z",
)
SOURCE_RECEIPT_PREIMAGE_ORDER = (
    "schema_id", "mutation_ref", "mutation_family", "command_schema_id",
    "command_digest", "program_ref", "decision_ref", "result_program_version_ref",
    "result_semantic_attempt_ref", "result_effect_intent_ref", "result_effect_fence_ref",
    "result_delivery_attempt_ref", "result_observation_ref", "result_decision_ref",
    "result_class", "result_projection_digest", "outcome", "committed_at",
)
SOURCE_GRAPH_ENTRY_SENTINELS = (
    ("role-sentinel-A", 0, "record-sentinel-A", "11" * 32),
    ("role-sentinel-B", 1, "record-sentinel-B", "22" * 32),
    ("role-sentinel-C", 2, "record-sentinel-C", "33" * 32),
)


def test_current_v1_receipt_graph_actual_value_mapping_and_digest():
    from ge_nwp_coordinator import _development_decision_row_values as source

    receipt = source.DevelopmentMutationReceiptRowValue._from_validated(
        SOURCE_RECEIPT_SENTINEL, None)
    entries = tuple(source.development_mutation_graph_entry(
        role=role, ordinal=ordinal, record_ref=record_ref,
        record_digest=record_digest)
        for role, ordinal, record_ref, record_digest in SOURCE_GRAPH_ENTRY_SENTINELS)
    expected = dict(zip(SOURCE_RECEIPT_PREIMAGE_ORDER,
                        [value for index, value in enumerate(SOURCE_RECEIPT_SENTINEL)
                         if index != 16], strict=True))
    expected["graph_entries"] = tuple(
        {"role": role, "ordinal": ordinal, "record_ref": ref, "record_digest": digest}
        for role, ordinal, ref, digest in SOURCE_GRAPH_ENTRY_SENTINELS)
    actual = source._receipt_graph_identity(receipt, entries)
    assert list(actual.items()) == list(expected.items())
    assert "mutation_graph_digest" not in actual
    assert "receipt_self_digest" not in actual
    assert "receipt_graph_profile_id" not in actual
    expected_bytes = json.dumps(expected, ensure_ascii=False, allow_nan=False,
                                sort_keys=True, separators=(",", ":")).encode("utf-8")
    actual_bytes = json.dumps(actual, ensure_ascii=False, allow_nan=False,
                              sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert actual_bytes == expected_bytes
    expected_digest = hashlib.sha256(
        b"governed-execution.nwp-development-mutation-receipt.v1.identity\0"
        + expected_bytes).hexdigest()
    assert source.compute_development_mutation_graph_digest(
        receipt=receipt, graph_entries=entries) == expected_digest
    assert [list(entry.items()) for entry in actual["graph_entries"]] == [
        list(entry.items()) for entry in expected["graph_entries"]]


def test_shared_c2_return_value_controls_actual_family_and_fact_membership():
    c2 = _load_c2_shared()
    state = c2._state_for_authoritative_branch(c2.EXPECTED_CONTRACT,
                                                "candidate_acceptance")
    command = _command_coordinates()
    act, fact = _verified_admission_fixture()
    original = c2._interpret
    calls = []

    def alternate(*args, **kwargs):
        calls.append((args, kwargs))
        observed = original(*args, **kwargs)
        assert observed["branch"] == "candidate_acceptance"
        changed = deepcopy(observed)
        changed["branch"] = "candidate_repair"
        return changed

    try:
        c2._interpret = alternate
        result = _private_branch_path(c2, command, act, fact, state,
                                      fresh_posture=deepcopy(FRESH_POSTURE_VECTOR))
    finally:
        c2._interpret = original
    assert len(calls) == 1
    assert result["branch"] == "candidate_repair"
    assert result["family"]["guarded_result"]["branch"] == "candidate_repair"
    assert result["acceptance_fact"] is None
    assert len(result["receipt_roles"]) == 10
    assert all(role["role"] != "acceptance_fact" for role in result["receipt_roles"])


@pytest.mark.parametrize("fault", ["missing", "stale", "unknown", "conflicting", "negative", "false"])
def test_fresh_posture_failure_never_enters_shared_c2(fault):
    c2 = _load_c2_shared()
    state = c2._state_for_authoritative_branch(c2.EXPECTED_CONTRACT,
                                                "candidate_acceptance")
    command = _command_coordinates()
    act, fact = _verified_admission_fixture()
    posture = deepcopy(FRESH_POSTURE_VECTOR)
    if fault == "missing":
        del posture["fresh_current_continuity"]
    elif fault == "false":
        posture["fresh_current_continuity"] = False
    else:
        posture["fresh_current_continuity"]["status"] = fault
    original = c2._interpret
    entered = []

    def counted(*args, **kwargs):
        entered.append((args, kwargs))
        return original(*args, **kwargs)

    try:
        c2._interpret = counted
        with pytest.raises(ContractViolation) as error:
            _private_branch_path(c2, command, act, fact, state,
                                 fresh_posture=posture)
    finally:
        c2._interpret = original
    assert error.value.boundary == "current_external_posture"
    assert entered == []


def test_private_branch_path_requires_explicit_fresh_posture_and_does_not_store_it():
    c2 = _load_c2_shared()
    state = c2._state_for_authoritative_branch(c2.EXPECTED_CONTRACT,
                                                "candidate_acceptance")
    command = _command_coordinates()
    act, fact = _verified_admission_fixture()
    with pytest.raises(TypeError):
        _private_branch_path(c2, command, act, fact, state)
    result = _private_branch_path(c2, command, act, fact, state,
                                  fresh_posture=deepcopy(FRESH_POSTURE_VECTOR))
    assert "fresh_posture" not in result["family"]
    assert "fresh_current_continuity" not in result["family"]
    assert "fresh_current_sole_active" not in result["family"]


PROFILE_FIXED_COMMON_ROLES = (
    "verified_admission_act", "scope_admission_fact", "historical_continuity_basis",
    "historical_sole_active_basis", "decision", "program_version",
    "historical_head_postimage", "generic_v1_result_projection",
    "guarded_family_relation", "guarded_result_composite",
)
PROFILE_FIXED_ROLE_SCHEMAS = {
    "verified_admission_act": "governed-execution.nwp-rw0-c2-verified-admission-act.v1",
    "scope_admission_fact": "governed-execution.nwp-rw0-c2-scope-admission-fact.v1",
    "historical_continuity_basis": "governed-execution.nwp-rw0-c2-verified-lineage-continuity.v1",
    "historical_sole_active_basis": "governed-execution.nwp-rw0-c2-verified-sole-active.v1",
    "decision": "governed-execution.nwp-development-decision.v1",
    "program_version": "governed-execution.nwp-development-program-version.v1",
    "historical_head_postimage": "governed-execution.nwp-development-program-head.v1",
    "generic_v1_result_projection": "governed-execution.nwp-record-development-progression-decision-result.v1",
    "guarded_family_relation": "governed-execution.nwp-rw0-c2-guarded-family-relation.v1",
    "guarded_result_composite": "governed-execution.nwp-rw0-c2-guarded-progression-result.v1",
    "acceptance_fact": "governed-execution.nwp-rw0-c2-bootstrap-acceptance-fact.v1",
}
PROFILE_FIXED_ID = "governed-execution.nwp-rw0-c2-receipt-graph-profile.v1"
PROFILE_FIXED_VERSION = 1
PROFILE_FIXED_ACCEPTANCE_ROLE = "acceptance_fact"
PROFILE_FIXED_ORDINAL = 0


def _assert_fixed_canonical_family(family, branch):
    fixed = FIXED_CANONICAL_OUTPUTS[branch]
    actual = {
        "decision": family["decision_digest"],
        "version": family["version_digest"],
        "head": family["historical_head_digest"],
        "result": family["generic_result_projection_digest"],
        "acceptance": (family["acceptance_fact"]["acceptance_fact_digest"]
                       if family["acceptance_fact"] is not None else None),
        "relation": family["relation_digest"],
        "guarded_result": family["guarded_result"]["guarded_result_digest"],
    }
    for name, wanted in actual.items():
        _exact(wanted, fixed[name], "fixed_canonical_family:" + name)
    return fixed


@pytest.mark.parametrize("branch", list(BRANCHES))
def test_current_v1_and_target_canonical_family_reconstruction(branch):
    from ge_nwp_coordinator import _development_decision_row_values as source

    command = _command_coordinates()
    act, admission = _verified_admission_fixture()
    family = _family_fixture(branch, command)
    fixed = _assert_fixed_canonical_family(family, branch)
    assert family["decision"].decision_kind == BRANCHES[branch][0]
    assert family["decision"].decision_variant == BRANCHES[branch][1]
    assert family["version"].program_version_kind == V1_VERSION_KIND[branch]
    assert family["historical_head_postimage"].program_state == V1_HEAD_STATE[branch]
    assert family["historical_head_postimage"].head_revision == 5
    assert family["historical_head_postimage_row"] == family["family_relation"]["historical_head_postimage"]
    assert family["generic_result_projection"]["decision_ref"] == family["decision_ref"]
    assert family["generic_result_projection"]["result_program_version_ref"] == family["version_ref"]
    assert family["family_relation"]["command_digest"] == _guarded_command_digest_v1(command)
    assert family["family_relation"]["branch"] == branch
    assert family["guarded_result"]["receipt_graph_profile_id"] == PROFILE_FIXED_ID
    assert family["guarded_result"]["branch"] == branch
    assert PROFILE_FIXED_VERSION == 1
    assert PROFILE_FIXED_COMMON_ROLES == EXPECTED_COMMON_RECEIPT_ROLES
    assert set(PROFILE_FIXED_ROLE_SCHEMAS) == set(PROFILE_FIXED_COMMON_ROLES) | {PROFILE_FIXED_ACCEPTANCE_ROLE}
    assert PROFILE_FIXED_ORDINAL == 0
    selector = _selector_instance(command)
    _validate_selector_instance(selector, command)
    fact = family["acceptance_fact"]
    roles = _receipt_roles_fixture(branch, fact)
    assert tuple(row["role"] for row in roles) == PROFILE_FIXED_COMMON_ROLES + (
        (PROFILE_FIXED_ACCEPTANCE_ROLE,) if branch == "candidate_acceptance" else ())
    assert all(row["ordinal"] == PROFILE_FIXED_ORDINAL for row in roles)
    assert len(roles) == (11 if branch == "candidate_acceptance" else 10)
    assert {row["role"] for row in roles} == set(PROFILE_FIXED_COMMON_ROLES) | (
        {PROFILE_FIXED_ACCEPTANCE_ROLE} if fact is not None else set())
    # Every common member is reconstructed from a typed source row or the
    # exact independently fixed target value, not inferred from its digest.
    member_schema = {
        "verified_admission_act": act["schema_id"],
        "scope_admission_fact": admission["schema_id"],
        "historical_continuity_basis": EXPECTED_SCHEMAS[3][1],
        "historical_sole_active_basis": EXPECTED_SCHEMAS[4][1],
        "decision": family["decision"].schema_id,
        "program_version": family["version"].schema_id,
        "historical_head_postimage": family["historical_head_postimage"].schema_id,
        "generic_v1_result_projection": family["generic_result_projection"]["schema_id"],
        "guarded_family_relation": family["family_relation"]["schema_id"],
        "guarded_result_composite": family["guarded_result"]["schema_id"],
    }
    if fact is not None:
        member_schema["acceptance_fact"] = fact["schema_id"]
    _exact(member_schema, {role: PROFILE_FIXED_ROLE_SCHEMAS[role] for role in member_schema},
           "fixed_profile_role_schemas")
    preimage = _source_exact_receipt_preimage(command, family)
    assert preimage["command_digest"] == family["command_digest"]
    graph_digest = _source_exact_graph_digest(command, family, roles)
    assert graph_digest == fixed["graph"]
    receipt_row = dict(preimage, mutation_graph_digest=graph_digest)
    receipt = source.development_mutation_receipt_row_value_from_row_tuple(
        tuple(receipt_row[name] for name in V1_RECEIPT_COLUMNS))
    assert receipt.result_projection.identity_mapping() == family["generic_result_projection"]
    assert receipt.result_projection.computed_digest() == fixed["result"]
    entries = tuple(source.development_mutation_graph_entry(**entry) for entry in roles)
    assert source.compute_development_mutation_graph_digest(
        receipt=receipt, graph_entries=entries) == fixed["graph"]
    source.require_development_mutation_graph_digest_matches_supplied_entries(
        receipt=receipt, graph_entries=entries)
    assert receipt.committed_at == FIXED_FAMILY_INPUT["timestamp"]
    assert family["transaction_timestamp"] == receipt.committed_at


def test_relation_raw_field_dependency_closure_for_every_branch():
    registry = EXPECTED_DEPENDENCY_REGISTRY
    relation_fields = EXPECTED_SCHEMAS[6][4]
    assert set(RELATION_FIELD_DEPENDENCIES) == set(relation_fields) - {"relation_digest"}
    assert "command_digest" in relation_fields
    relation = next(row for row in registry["nodes"] if row["node"] == "family_relation_value")
    for branch in BRANCHES:
        deps = set(relation["common_dependencies"] +
                   relation["dependencies_by_branch"].get(branch, []))
        for field, owner_node in RELATION_FIELD_DEPENDENCIES.items():
            if field.startswith("acceptance_fact_") and branch != "candidate_acceptance":
                assert owner_node not in deps
            else:
                assert owner_node in deps, (branch, field, owner_node)
        assert {"command_digest", "canonical_decision_value", "canonical_decision_digest",
                "canonical_version_value", "canonical_version_digest",
                "historical_head_postimage_value", "historical_head_postimage_digest",
                "generic_result_projection_value", "generic_result_projection_digest",
                "guarded_result_identity_expectation"} <= deps


RECOVERY_MEMBER_REF_FIELDS = {
    "mutation_receipt_route": "mutation_ref",
    "decision_identity_route": "decision_ref",
    "resulting_version_identity_route": "version_ref",
    "acceptance_fact_identity_route": "acceptance_fact_ref",
    "guarded_family_relation_identity_route": "relation_ref",
    "guarded_progression_result_identity_route": "guarded_result_ref",
    "deterministic_family_route": "family_route",
    "admitted_scope_winner_route": "relation_ref",
}


RECOVERY_EVIDENCE_DOMAIN = b"governed-execution.nwp-rw0-c2-route-observation-evidence.v1"


def _route_evidence_digest(evidence_ref):
    return hashlib.sha256(RECOVERY_EVIDENCE_DOMAIN + b"\0" +
                          evidence_ref.encode("utf-8")).hexdigest()


def _complete_observation_ref(member_ref, graph_digest):
    return "exact-family:" + member_ref + ":" + graph_digest


def _typed_recovery_observation_set(selector, statuses, *, fresh_posture):
    if type(statuses) is not dict or set(statuses) != set(RECOVERY_MEMBER_REF_FIELDS):
        raise ContractViolation("recovery_route_coverage")
    observations = []
    for route in selector["required_collision_routes"]:
        role = route["role"]
        status = statuses[role]
        if type(status) is not str or status not in FIXED_RECOVERY_STATUSES:
            raise ContractViolation("recovery_route_status")
        if status in {"unchecked", "unreadable", "absent"}:
            evidence_ref = None
        elif status == "exact_complete_family":
            evidence_ref = _complete_observation_ref(
                selector[RECOVERY_MEMBER_REF_FIELDS[role]],
                FIXED_CANONICAL_OUTPUTS["candidate_acceptance"]["graph"])
        elif status == "competing_complete_scope_winner":
            evidence_ref = "competing-scope-winner:foreign-complete-winner-A"
        else:
            evidence_ref = "safe-observation:" + role + ":" + status
        observations.append({
            "route_role": role,
            "route_key": list(route["key"]),
            "status": status,
            "read_attempted": status != "unchecked",
            "readable": status not in {"unchecked", "unreadable"},
            "evidence_ref": evidence_ref,
            "evidence_digest": _route_evidence_digest(evidence_ref) if evidence_ref else None,
            "total_absence_proved": status == "absent",
        })
    return {
        "lineage_ref": selector["lineage_ref"], "scope_ref": selector["scope_ref"],
        "fresh_current_continuity": {
            "status": fresh_posture["fresh_current_continuity"]["status"],
            "posture_ref": fresh_posture["fresh_current_continuity"]["evidence_ref"],
            "posture_digest": fresh_posture["fresh_current_continuity"]["evidence_digest"],
        },
        "fresh_current_sole_active": {
            "status": fresh_posture["fresh_current_sole_active"]["status"],
            "posture_ref": fresh_posture["fresh_current_sole_active"]["evidence_ref"],
            "posture_digest": fresh_posture["fresh_current_sole_active"]["evidence_digest"],
        },
        "route_observations": observations,
    }


def _validate_recovery_observation_set(selector, observed_set):
    if type(observed_set) is not dict or list(observed_set) != (
            RECOVERY_OBSERVATION_SET["posture_fields"] + ["route_observations"]):
        raise ContractViolation("recovery_observation_shape")
    for name in ("lineage_ref", "scope_ref"):
        if (type(observed_set[name]) is not str or not observed_set[name] or
                observed_set[name] != selector[name]):
            raise ContractViolation("recovery_scope_binding")
    routes = observed_set["route_observations"]
    if type(routes) is not list or len(routes) != len(ROUTES):
        raise ContractViolation("recovery_route_coverage")
    statuses = []
    seen = set()
    for actual, template in zip(routes, selector["required_collision_routes"], strict=True):
        if type(actual) is not dict or list(actual) != RECOVERY_OBSERVATION_SET["route_observation_fields"]:
            raise ContractViolation("recovery_route_shape")
        role, key = actual["route_role"], actual["route_key"]
        if type(role) is not str or role in seen or role != template["role"]:
            raise ContractViolation("recovery_route_identity")
        seen.add(role)
        if (type(key) is not list or key != template["key"] or
                any(type(value) is not str or not value for value in key)):
            raise ContractViolation("recovery_route_identity")
        status = actual["status"]
        if type(status) is not str or status not in FIXED_RECOVERY_STATUSES:
            raise ContractViolation("recovery_route_status")
        rules = RECOVERY_OBSERVATION_SET["route_status_rules"][status]
        for field in ("read_attempted", "readable", "total_absence_proved"):
            if type(actual[field]) is not bool or actual[field] != rules[field]:
                raise ContractViolation("recovery_status_matrix:" + field)
        evidence_ref, evidence_digest = actual["evidence_ref"], actual["evidence_digest"]
        if rules["evidence_ref"] == "null":
            if evidence_ref is not None or evidence_digest is not None:
                raise ContractViolation("recovery_evidence_nullability")
        else:
            if type(evidence_ref) is not str or not evidence_ref:
                raise ContractViolation("recovery_evidence_ref_type")
            if (type(evidence_digest) is not str or
                    re.fullmatch(r"[0-9a-f]{64}", evidence_digest) is None or
                    evidence_digest != _route_evidence_digest(evidence_ref)):
                raise ContractViolation("recovery_evidence_digest_type")
        if status == "competing_complete_scope_winner" and role != "admitted_scope_winner_route":
            raise ContractViolation("recovery_competing_winner")
        statuses.append(status)
    posture = {}
    for field in ("fresh_current_continuity", "fresh_current_sole_active"):
        value = observed_set[field]
        if type(value) is not dict or list(value) != RECOVERY_OBSERVATION_SET["posture_value_fields"]:
            raise ContractViolation("recovery_current_posture_shape")
        if (type(value["status"]) is not str or
                value["status"] not in RECOVERY_OBSERVATION_SET["posture_statuses"] or
                type(value["posture_ref"]) is not str or not value["posture_ref"] or
                type(value["posture_digest"]) is not str or
                re.fullmatch(r"[0-9a-f]{64}", value["posture_digest"]) is None):
            raise ContractViolation("recovery_current_posture_type")
        posture[field] = {"status": value["status"], "evidence_ref": value["posture_ref"],
                          "evidence_digest": value["posture_digest"]}
    return statuses, posture


def _recovery_canonical_binding(command, branch, family, selector):
    return {"command": command, "branch": branch, "family": family,
            "selector": selector}


def _current_recovery_posture_for_test(selector, fresh_posture):
    """Construct external-verifier evidence fixtures; never infer from retained bases."""
    continuity = fresh_posture["fresh_current_continuity"]
    sole_active = fresh_posture["fresh_current_sole_active"]
    continuity_states = {"positive": "positively_established", "missing": "missing",
                         "stale": "stale", "unknown": "unknown",
                         "conflicting": "conflicting", "negative": "negative"}
    sole_active_states = {"positive": "exactly_one_active_authority", "missing": "missing",
                          "stale": "stale", "unknown": "unknown",
                          "conflicting": "conflicting", "negative": "not_exactly_one"}
    return {
        "lineage_ref": selector["lineage_ref"],
        "scope_ref": selector["scope_ref"],
        "current_continuity_posture_ref": continuity["evidence_ref"],
        "current_continuity_posture_digest": continuity["evidence_digest"],
        "continuity_state": continuity_states[continuity["status"]],
        "current_sole_active_posture_ref": sole_active["evidence_ref"],
        "current_sole_active_posture_digest": sole_active["evidence_digest"],
        "sole_active_state": sole_active_states[sole_active["status"]],
    }


def _validate_current_recovery_posture(selector, observed_set, posture):
    if type(posture) is not dict or list(posture) != list(CURRENT_RECOVERY_POSTURE_FIELDS):
        raise ContractViolation("current_recovery_posture_shape")
    for field in CURRENT_RECOVERY_POSTURE_FIELDS:
        if type(posture[field]) is not str:
            raise ContractViolation("current_recovery_posture_type:" + field)
    for field in ("lineage_ref", "scope_ref"):
        if not posture[field] or posture[field] != selector[field]:
            raise ContractViolation("current_recovery_posture_binding:" + field)
    for field in ("current_continuity_posture_ref", "current_sole_active_posture_ref"):
        if not posture[field]:
            raise ContractViolation("current_recovery_posture_ref:" + field)
    for field in ("current_continuity_posture_digest", "current_sole_active_posture_digest"):
        if re.fullmatch(r"[0-9a-f]{64}", posture[field]) is None:
            raise ContractViolation("current_recovery_posture_digest:" + field)
    if posture["continuity_state"] not in CONTINUITY_STATES:
        raise ContractViolation("current_recovery_posture_continuity_state")
    if posture["sole_active_state"] not in SOLE_ACTIVE_STATES:
        raise ContractViolation("current_recovery_posture_sole_active_state")
    state_pairs = (
        ("fresh_current_continuity", "current_continuity_posture_ref",
         "current_continuity_posture_digest", "continuity_state",
         dict(zip(("positive", "missing", "stale", "unknown", "conflicting", "negative"),
                  CONTINUITY_STATES, strict=True))),
        ("fresh_current_sole_active", "current_sole_active_posture_ref",
         "current_sole_active_posture_digest", "sole_active_state",
         dict(zip(("positive", "missing", "stale", "unknown", "conflicting", "negative"),
                  SOLE_ACTIVE_STATES, strict=True))),
    )
    for source, ref_field, digest_field, state_field, mapping in state_pairs:
        observed = observed_set[source]
        if (posture[ref_field] != observed["posture_ref"] or
                posture[digest_field] != observed["posture_digest"] or
                posture[state_field] != mapping[observed["status"]]):
            raise ContractViolation("recovery_result_current_posture_binding")
    return posture


def _validate_recovery_projection_inputs(observed_set, canonical_binding,
                                         validated_current_posture):
    if (type(canonical_binding) is not dict or
            list(canonical_binding) != RECOVERY_PROJECTION_SIGNATURE["canonical_binding_fields"]):
        raise ContractViolation("recovery_canonical_binding_shape")
    command = canonical_binding["command"]
    branch = canonical_binding["branch"]
    family = canonical_binding["family"]
    selector = canonical_binding["selector"]
    if type(branch) is not str or branch not in BRANCHES or type(family) is not dict:
        raise ContractViolation("recovery_canonical_binding_type")
    _validate_selector_instance(selector, command)
    statuses, _ = _validate_recovery_observation_set(selector, observed_set)
    _validate_current_recovery_posture(selector, observed_set, validated_current_posture)
    return command, branch, family, selector, statuses


def _current_recovery_posture_is_positive(posture):
    return (posture["continuity_state"] == "positively_established" and
            posture["sole_active_state"] == "exactly_one_active_authority")


def _recovery_result_projection(observed_set, canonical_binding, validated_current_posture):
    _validate_recovery_projection_inputs(observed_set, canonical_binding,
                                         validated_current_posture)
    classification = _classify_complete_family_recovery(
        observed_set, canonical_binding, validated_current_posture)
    result = {
        "schema_id": EXPECTED_SCHEMAS[-1][1],
        "classification": classification,
        "lineage_ref": validated_current_posture["lineage_ref"],
        "scope_ref": validated_current_posture["scope_ref"],
        "current_continuity_posture_ref": validated_current_posture["current_continuity_posture_ref"],
        "current_continuity_posture_digest": validated_current_posture["current_continuity_posture_digest"],
        "current_sole_active_posture_ref": validated_current_posture["current_sole_active_posture_ref"],
        "current_sole_active_posture_digest": validated_current_posture["current_sole_active_posture_digest"],
    }
    if tuple(result) != ("schema_id",) + RECOVERY_RESULT_FIELDS or classification not in RECOVERY["classes"]:
        raise ContractViolation("recovery_result_projection")
    return result


def _classify_complete_family_recovery(observed_set, canonical_binding,
                                       validated_current_posture):
    _, branch, family, selector, statuses = _validate_recovery_projection_inputs(
        observed_set, canonical_binding, validated_current_posture)
    if not _current_recovery_posture_is_positive(validated_current_posture):
        return "unresolved"
    if all(status == "absent" for status in statuses):
        return "definitely_not_committed"
    if (statuses[-1] == "competing_complete_scope_winner" and
            all(status == "absent" for status in statuses[:-1])):
        return "definitely_not_committed"
    expected = ["exact_complete_family"] * 8
    if branch != "candidate_acceptance":
        expected[3] = "absent"
    if statuses == expected:
        fixed = _assert_fixed_canonical_family(family, branch)
        for row in observed_set["route_observations"]:
            if row["status"] == "exact_complete_family" and row["evidence_ref"] != (
                    _complete_observation_ref(
                        selector[RECOVERY_MEMBER_REF_FIELDS[row["route_role"]]], fixed["graph"])):
                return "unresolved"
        return "committed_exact"
    return "unresolved"


def _classify_recovery_for_v7_fixture(command, branch, family, selector, observed_set):
    """Retain V7 route-matrix tests against the V8 classifier interface."""
    supplied = deepcopy(FRESH_POSTURE_VECTOR)
    for source in ("fresh_current_continuity", "fresh_current_sole_active"):
        supplied[source]["status"] = observed_set[source]["status"]
    posture = _current_recovery_posture_for_test(selector, supplied)
    return _classify_complete_family_recovery(
        observed_set, _recovery_canonical_binding(command, branch, family, selector), posture)


def _project_recovery_for_v7_fixture(command, branch, family, selector, observed_set, *,
                                     verified_fresh_posture):
    posture = _current_recovery_posture_for_test(selector, verified_fresh_posture)
    return _recovery_result_projection(
        observed_set, _recovery_canonical_binding(command, branch, family, selector), posture)


@pytest.mark.parametrize("branch", list(BRANCHES))
def test_typed_recovery_exact_complete_family_and_absence(branch):
    command = _command_coordinates()
    family = _family_fixture(branch, command)
    selector = _selector_instance(command)
    complete = {role: "exact_complete_family" for role in RECOVERY_OBSERVATION_SET["route_roles"]}
    if branch != "candidate_acceptance":
        complete["acceptance_fact_identity_route"] = "absent"
    observed = _typed_recovery_observation_set(selector, complete,
        fresh_posture=FRESH_POSTURE_VECTOR)
    for row in observed["route_observations"]:
        if row["status"] == "exact_complete_family":
            row["evidence_ref"] = _complete_observation_ref(
                selector[RECOVERY_MEMBER_REF_FIELDS[row["route_role"]]],
                FIXED_CANONICAL_OUTPUTS[branch]["graph"])
            row["evidence_digest"] = _route_evidence_digest(row["evidence_ref"])
    assert _classify_recovery_for_v7_fixture(command, branch, family, selector, observed) == "committed_exact"
    result = _project_recovery_for_v7_fixture(command, branch, family, selector, observed,
        verified_fresh_posture=FRESH_POSTURE_VECTOR)
    assert tuple(result) == ("schema_id",) + RECOVERY_RESULT_FIELDS
    assert result["classification"] == "committed_exact"
    assert result["lineage_ref"] == command["lineage_ref"]
    assert result["scope_ref"] == command["scope_ref"]
    assert result["current_continuity_posture_ref"] == FRESH_POSTURE_VECTOR[
        "fresh_current_continuity"]["evidence_ref"]
    assert result["current_sole_active_posture_ref"] == FRESH_POSTURE_VECTOR[
        "fresh_current_sole_active"]["evidence_ref"]
    absent = _typed_recovery_observation_set(selector,
        {role: "absent" for role in RECOVERY_OBSERVATION_SET["route_roles"]},
        fresh_posture=FRESH_POSTURE_VECTOR)
    assert _classify_recovery_for_v7_fixture(command, branch, family, selector, absent) == "definitely_not_committed"
    stale = deepcopy(absent)
    stale["fresh_current_continuity"]["status"] = "stale"
    assert _classify_recovery_for_v7_fixture(command, branch, family, selector, stale) == "unresolved"


@pytest.mark.parametrize("status", FIXED_RECOVERY_STATUSES)
def test_recovery_route_status_grammar_and_classification(status):
    command = _command_coordinates()
    family = _family_fixture("candidate_acceptance", command)
    selector = _selector_instance(command)
    statuses = {role: "absent" for role in RECOVERY_OBSERVATION_SET["route_roles"]}
    statuses["decision_identity_route"] = status
    observed = _typed_recovery_observation_set(selector, statuses,
        fresh_posture=FRESH_POSTURE_VECTOR)
    if status == "exact_complete_family":
        assert _classify_recovery_for_v7_fixture(command, "candidate_acceptance", family,
                                                   selector, observed) == "unresolved"
    elif status == "absent":
        assert _classify_recovery_for_v7_fixture(command, "candidate_acceptance", family,
                                                   selector, observed) == "definitely_not_committed"
    elif status == "competing_complete_scope_winner":
        with pytest.raises(ContractViolation) as error:
            _classify_recovery_for_v7_fixture(command, "candidate_acceptance", family,
                                               selector, observed)
        assert error.value.boundary == "recovery_competing_winner"
    else:
        assert _classify_recovery_for_v7_fixture(command, "candidate_acceptance", family,
                                                   selector, observed) == "unresolved"


def test_recovery_competing_complete_scope_winner_is_not_fresh_acceptance_permission():
    command = _command_coordinates()
    family = _family_fixture("candidate_acceptance", command)
    selector = _selector_instance(command)
    statuses = {role: "absent" for role in RECOVERY_OBSERVATION_SET["route_roles"]}
    statuses["admitted_scope_winner_route"] = "competing_complete_scope_winner"
    observed = _typed_recovery_observation_set(selector, statuses,
        fresh_posture=FRESH_POSTURE_VECTOR)
    assert _classify_recovery_for_v7_fixture(command, "candidate_acceptance", family,
                                               selector, observed) == "definitely_not_committed"
    assert RECOVERY["different_complete_winner_fresh_acceptance_eligible"] is False


FIXED_HISTORICAL_CONTINUITY_BASIS = {
    "schema_id": "governed-execution.nwp-rw0-c2-verified-lineage-continuity.v1",
    "basis_ref": "continuity-basis-A", "source_ref": "continuity-source-A",
    "source_digest": "ce" * 32, "lineage_ref": "lineage-A", "scope_ref": "scope-A",
    "authority_epoch_ref": "epoch-A", "currentness_ref": "continuity-currentness-A",
    "currentness_digest": "a1" * 32, "provenance_ref": "continuity-provenance-A",
    "provenance_digest": "a2" * 32,
    "projection_digest": "e7e50ee17c285a0b54199891c5d2c5a324da0bee5a76fac2c6463145886a90f5",
}
FIXED_HISTORICAL_SOLE_ACTIVE_BASIS = {
    "schema_id": "governed-execution.nwp-rw0-c2-verified-sole-active.v1",
    "basis_ref": "sole-basis-A", "source_ref": "sole-source-A", "source_digest": "df" * 32,
    "lineage_ref": "lineage-A", "scope_ref": "scope-A", "authority_epoch_ref": "epoch-A",
    "currentness_ref": "sole-currentness-A", "currentness_digest": "b1" * 32,
    "active_authority_ref": "active-authority-A",
    "sole_active_assertion_ref": "assertion-A", "sole_active_assertion_digest": "b2" * 32,
    "provenance_ref": "sole-provenance-A", "provenance_digest": "b3" * 32,
    "projection_digest": "29c2547e8aa3f8c2bea89ea149a33ab853a0c5c10fab9fc75b06561b1ae02383",
}


def test_historical_external_basis_members_are_exact_safe_values_without_standing_permission():
    command = _command_coordinates()
    for basis, kind in ((FIXED_HISTORICAL_CONTINUITY_BASIS, "continuity"),
                        (FIXED_HISTORICAL_SOLE_ACTIVE_BASIS, "sole_active")):
        assert list(basis) == EXPECTED_SCHEMAS[3 if kind == "continuity" else 4][4]
        _exact(_private_identity_digest(basis["schema_id"],
            {name: value for name, value in basis.items() if name != "projection_digest"}),
            basis["projection_digest"], "historical_basis_digest:" + kind)
        assert command[kind + "_basis_ref"] == basis["basis_ref"]
        assert command[kind + "_basis_digest"] == basis["projection_digest"]
        assert command[kind + "_source_ref"] == basis["source_ref"]
        assert command[kind + "_source_digest"] == basis["source_digest"]
        assert "fresh_current_continuity" not in basis
        assert "fresh_current_sole_active" not in basis


@pytest.mark.parametrize("assertion", [
    "Replay might create a new fact.",
    "A replay adapter may create a second receipt.",
    "Replay is authorized. It creates a new acceptance fact.",
    "Replay could refresh the transaction timestamp.",
    "Exact replay is authorized to create a new fact.",
])
@pytest.mark.parametrize("style", ["heading", "bullet", "table", "quote", "link_label"])
def test_extended_visible_authority_language_rejected(assertion, style):
    text, _ = _document()
    rendered = {
        "heading": "\n## " + assertion + "\n",
        "bullet": "\n- " + assertion + "\n",
        "table": "\n| " + assertion + " |\n",
        "quote": "\n> " + assertion + "\n",
        "link_label": "\n[" + assertion + "](https://example.invalid/anchor)\n",
    }[style]
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(text + rendered)
    expected_topic = ("single_result_receipt_replay_recovery"
                      if "second receipt" in assertion else "replay_original_fact_timestamp")
    assert error.value.boundary == "normative_untagged:" + expected_topic


def test_neutral_replay_glossary_visible_prose_passes():
    text, _ = _document()
    _scan_normative_prose(text + "\nThe replay glossary may include the term timestamp.\n")


def _owner_machine_at_marker(path, marker):
    if path not in {value[0] for value in OWNER_DOCS.values()}:
        raise ContractViolation("normative_owner_path")
    text = (ROOT / path).read_text(encoding="utf-8")
    exact_marker = "<!-- " + marker + " -->"
    if text.count(exact_marker) != 1:
        raise ContractViolation("normative_owner_marker")
    region = text.split(exact_marker, 1)[1]
    if "```json\n" not in region or "\n```" not in region:
        raise ContractViolation("normative_owner_marker")
    raw = region.split("```json\n", 1)[1].split("\n```", 1)[0]
    return _strict_json(raw)


def _compare_owner_value(observed, comparison, expected):
    if comparison == "equals":
        return type(observed) is type(expected) and observed == expected
    if comparison == "contains":
        return type(observed) is list and any(
            type(item) is type(expected) and item == expected for item in observed)
    if comparison == "not_contains":
        return type(observed) is list and not any(
            type(item) is type(expected) and item == expected for item in observed)
    raise ContractViolation("normative_owner_rule_operator")


def _check_private_structural_consequence(consequence_id, profile):
    # Each arm checks a value-grammar invariant independently of owner pointers
    # and tagged English. The negative controls perturb each arm in isolation.
    if consequence_id == "historical_basis_not_current_permission":
        return (profile["boundaries"]["external_currentness_is_local_durable_fact"] is False
                and profile["replay"]["historical_basis_is_current_permission"] is False)
    if consequence_id == "fresh_posture_required_for_protected_disclosure":
        nodes = {row["node"]: row for row in profile["dependency_registry"]["nodes"]}
        return (profile["replay"]["fresh_external_posture_required"] is True
                and profile["recovery"]["fresh_external_posture_required"] is True
                and "fresh_external_posture" in nodes["replay_projection"]["common_dependencies"]
                and "fresh_external_posture" in nodes["recovery_projection"]["common_dependencies"])
    if consequence_id == "derived_nonnull_coordinate_required":
        fact = profile["prospective_fact_identity"]
        return (fact["required_all_branches"] is True and fact["nullable"] is False
                and fact["command_field"] in profile["schemas"][2][4])
    if consequence_id == "coordinate_cannot_force_or_veto_branch":
        fact = profile["prospective_fact_identity"]
        return (fact["caller_selects_branch"] is False and fact["assertion_only"] is True
                and "caller_branch" in profile["command_digest"]["excludes"])
    if consequence_id == "nonaccept_fact_absent_but_collision_probed":
        fact = profile["prospective_fact_identity"]
        return (type(fact["nonaccept_fact_count"]) is int and fact["nonaccept_fact_count"] == 0
                and fact["collision_probe_all_branches"] is True
                and profile["selector"]["all_branches"] is True)
    if consequence_id == "eight_exact_routes_required":
        selector = profile["selector"]
        return (type(selector["exact_route_count"]) is int and selector["exact_route_count"] == 8
                and selector["concrete_routes_all_branches"] is True
                and [row["role"] for row in profile["collision_route_templates"]]
                == [row["role"] for row in ROUTES])
    if consequence_id == "local_absence_cannot_prove_noncommit":
        recovery = profile["recovery"]
        return (recovery["total_absence_requires_all_routes_checked"] is True
                and recovery["local_absence_without_current_posture_class"] == "unresolved"
                and profile["recovery_observation_set"]["total_absence_rule"]
                == "all_eight_absent_and_proved_with_both_positive_fresh_postures")
    if consequence_id == "replay_creates_no_fact_or_timestamp":
        replay = profile["replay"]
        return (replay["new_fact"] is False and replay["new_timestamp"] is False
                and "original_transaction_timestamp" in replay["returns"]
                and "original_optional_acceptance_fact" in replay["returns"])
    if consequence_id == "command_relation_cannot_admit_scope":
        return (profile["admission_binding"]["command_may_admit_or_select_scope"] is False
                and profile["command_digest"]["admitted_scope_match_required"] is True
                and profile["selector"]["local_absence_proves_unclaimed"] is False)
    if consequence_id == "decision_writer_cannot_provision_admission":
        bounds = profile["boundaries"]
        return (bounds["admission_writer"] == "future_separate_admission_provisioner_only"
                and bounds["acceptance_writer"] == "future_guarded_decision_writer_acceptance_only")
    if consequence_id == "one_decision_owned_result_receipt_replay_recovery":
        bounds = profile["boundaries"]
        return (all(type(bounds[name]) is int and bounds[name] == 1
                    for name in ("receipts", "replay_owners", "recovery_classifiers"))
                and profile["graph"]["generic_receipt_self_digest"] is False)
    if consequence_id == "terminal_cannot_replenish_acceptance":
        return profile["boundaries"]["terminal_creates_or_replenishes_acceptance"] is False
    if consequence_id == "es_cannot_replenish_direct_local_allowance":
        return profile["boundaries"]["es_replenishes_direct_local"] is False
    raise ContractViolation("normative_private_structure_unknown:" + consequence_id)


def _resolve_owner_consequence(clause_id, row, profile=None):
    if profile is None:
        profile = _document()[1]
    _validate_owner_assertion_profile(profile)
    if clause_id not in OWNER_REFERENCE_RULES:
        raise ContractViolation("normative_owner_reference_inventory")
    owner_name, claims, consequence_id = OWNER_REFERENCE_RULES[clause_id]
    path, marker = OWNER_DOCS[owner_name]
    expected = next(item for item in NORMATIVE_REGISTRY if item["clause_id"] == clause_id)
    _exact(row, expected, "normative_owner_reference_inventory")
    owner_machine = _owner_machine_at_marker(path, marker)
    observed = []
    for pointer, comparison, expected_value in claims:
        value = owner_machine
        for component in pointer.strip("/").split("/"):
            if type(value) is not dict or component not in value:
                raise ContractViolation("normative_owner_anchor_missing:" + clause_id)
            value = value[component]
        passed = _compare_owner_value(value, comparison, expected_value)
        observed.append({"json_pointer": pointer, "comparison": comparison,
                         "expected_value": expected_value, "observed_value": value,
                         "passes": passed})
    if not all(assertion["passes"] for assertion in observed):
        raise ContractViolation("normative_owner_assertion:" + clause_id)
    if not _check_private_structural_consequence(consequence_id, profile):
        raise ContractViolation("normative_private_structure:" + clause_id)
    return {"clause_id": clause_id, "owner_document": path,
            "owner_machine_marker": marker, "owner_assertions": observed,
            "private_structural_consequence": consequence_id}


def test_thirteen_normative_clauses_resolve_unchanged_owner_values():
    text, profile = _document()
    tagged = _normative_clauses(text)
    rows = profile["normative_clause_registry"]
    assert len(rows) == 13
    assert set(tagged) == set(OWNER_REFERENCE_RULES)
    _exact(rows, NORMATIVE_REGISTRY, "normative_clause_registry")
    for row in rows:
        clause_id = row["clause_id"]
        resolved = _resolve_owner_consequence(clause_id, row, profile)
        assert resolved["private_structural_consequence"] == row["private_structural_consequence"]
        assert all(item["passes"] for item in resolved["owner_assertions"])
        assert _normalize_visible(tagged[clause_id]) == _normalize_visible(PROSE_CLAUSES[clause_id])
        assert _normative_prefix(clause_id) + tagged[clause_id] in text


@pytest.mark.parametrize("clause_id", list(OWNER_REFERENCE_RULES))
def test_private_clause_owner_reference_mutations_fail(clause_id):
    row = deepcopy(next(row for row in NORMATIVE_REGISTRY if row["clause_id"] == clause_id))
    row["owner_assertions"][0]["json_pointer"] = "/unrelated/true"
    with pytest.raises(ContractViolation) as error:
        _resolve_owner_consequence(clause_id, row)
    assert error.value.boundary == "normative_owner_reference_inventory"


def test_exact_owner_pointer_purposes_and_comparison_grammar():
    seen = set()
    for clause_id, (owner_name, assertions, consequence_id) in OWNER_REFERENCE_RULES.items():
        for pointer, comparison, expected_value in assertions:
            key = (owner_name, pointer)
            assert key in OWNER_POINTER_PURPOSES
            enclosing, terminal, wanted_comparison, wanted_value, allowed = OWNER_POINTER_PURPOSES[key]
            pieces = pointer.strip("/").split("/")
            assert "/".join(pieces[:-1]) == enclosing
            assert pieces[-1] == terminal
            assert comparison == wanted_comparison
            _exact(expected_value, wanted_value, "owner_pointer_purpose:" + clause_id)
            assert consequence_id in allowed
            seen.add(key)
    assert seen == set(OWNER_POINTER_PURPOSES)
    assert _compare_owner_value(False, "equals", False)
    assert not _compare_owner_value(0, "equals", False)
    assert _compare_owner_value(["a", "b"], "contains", "a")
    assert _compare_owner_value(["a", "b"], "not_contains", "c")
    assert not _compare_owner_value(["a", "b"], "not_contains", "a")
    assert not _compare_owner_value([False], "contains", 0)
    with pytest.raises(ContractViolation):
        _compare_owner_value([], "substring", "x")


STRUCTURAL_FAULTS = {
    "historical_basis_not_current_permission": ("boundaries", "external_currentness_is_local_durable_fact", True),
    "fresh_posture_required_for_protected_disclosure": ("replay", "fresh_external_posture_required", False),
    "derived_nonnull_coordinate_required": ("prospective_fact_identity", "required_all_branches", False),
    "coordinate_cannot_force_or_veto_branch": ("prospective_fact_identity", "caller_selects_branch", True),
    "nonaccept_fact_absent_but_collision_probed": ("prospective_fact_identity", "nonaccept_fact_count", 1),
    "eight_exact_routes_required": ("selector", "exact_route_count", 7),
    "local_absence_cannot_prove_noncommit": ("recovery", "total_absence_requires_all_routes_checked", False),
    "replay_creates_no_fact_or_timestamp": ("replay", "new_fact", True),
    "command_relation_cannot_admit_scope": ("admission_binding", "command_may_admit_or_select_scope", True),
    "decision_writer_cannot_provision_admission": ("boundaries", "admission_writer", "decision_writer"),
    "one_decision_owned_result_receipt_replay_recovery": ("boundaries", "receipts", 2),
    "terminal_cannot_replenish_acceptance": ("boundaries", "terminal_creates_or_replenishes_acceptance", True),
    "es_cannot_replenish_direct_local_allowance": ("boundaries", "es_replenishes_direct_local", True),
}


@pytest.mark.parametrize("consequence_id", list(STRUCTURAL_FAULTS))
def test_each_private_structural_consequence_has_a_real_negative_control(consequence_id):
    _, profile = _document()
    assert _check_private_structural_consequence(consequence_id, profile) is True
    changed = deepcopy(profile)
    section, key, hostile = STRUCTURAL_FAULTS[consequence_id]
    changed[section][key] = hostile
    assert _check_private_structural_consequence(consequence_id, changed) is False


def test_every_owner_clause_invokes_its_structural_consequence(monkeypatch):
    calls = []
    original = _check_private_structural_consequence
    def recording(consequence_id, profile):
        calls.append(consequence_id)
        return original(consequence_id, profile)
    monkeypatch.setattr(__import__(__name__), "_check_private_structural_consequence", recording)
    _, profile = _document()
    for row in profile["normative_clause_registry"]:
        _resolve_owner_consequence(row["clause_id"], row, profile)
    assert calls == [row["private_structural_consequence"]
                     for row in profile["normative_clause_registry"]]


def test_guarded_command_digest_fixed_vector_is_used_by_selector_and_family():
    command = _command_coordinates()
    actual = _guarded_command_digest_v1(command)
    assert actual == "a392abcc3f0981b4ac2aeab5d3869aea9f24ba7305b242563e3a41f402b716b1"
    assert COMMAND_DIGEST["fixed_vector_digest"] == actual
    assert COMMAND_DIGEST["domain"] == COMMAND_DOMAIN
    assert [row[0] for row in COMMAND_DIGEST["ordered_preimage"]] == INCLUDES
    assert len(COMMAND_DIGEST["ordered_preimage"]) == 30
    selector = _selector_instance(command)
    assert selector["command_digest"] == actual
    _validate_selector_instance(selector, command)
    for branch in BRANCHES:
        family = _family_fixture(branch, command)
        assert family["command_digest"] == actual
        assert family["family_relation"]["command_digest"] == actual
        if family["acceptance_fact"] is not None:
            assert family["acceptance_fact"]["command_digest"] == actual
        assert _source_exact_receipt_preimage(command, family)["command_digest"] == actual


def test_guarded_command_digest_v2_profile_adds_exact_assertion_after_v1_pairs():
    _, profile = _document()
    v1 = profile["command_digest"]
    v2 = profile["command_digest_v2"]
    command = _command_coordinates()
    pairs = [[name, command["schema_id" if name == "command_profile" else name]]
             for name, _source, _type in v1["ordered_preimage"]]
    assert len(pairs) == 30
    assert v2["ordered_pair_count"] == len(pairs) + 1
    assert v2["ordered_preimage_prefix_ref"] == "command_digest.ordered_preimage"
    assert v2["ordered_preimage_suffix"] == [[
        "expected_branch", "command.expected_branch", "null_or_exact_finite_branch_str"]]
    digests = []
    for assertion in v2["finite_expected_branch_values"]:
        raw = json.dumps(pairs + [["expected_branch", assertion]],
                         ensure_ascii=False, allow_nan=False,
                         separators=(",", ":")).encode("utf-8")
        digests.append(hashlib.sha256(v2["domain"].encode("utf-8") + b"\0" + raw).hexdigest())
    assert len(set(digests)) == 6
    assert digests[0] == v2["fixed_vector_digest"]
    assert digests[0] != v1["fixed_vector_digest"]


@pytest.mark.parametrize("name", PRIMITIVE_NAMES + [field for _, field, _, _ in SIBLING_SPECS])
def test_each_command_coordinate_changes_real_digest_and_old_selector_rejects(name):
    original = _command_coordinates()
    old_digest = _guarded_command_digest_v1(original)
    old_selector = _selector_instance(original)
    changed = deepcopy(original)
    field = "schema_id" if name == "command_profile" else name
    if field == "expected_head_revision":
        changed[field] += 1
    elif field.endswith("_digest") or field.startswith("preassigned_") or field == "family_route":
        changed[field] = "12" * 32
    else:
        changed[field] += "-different"
    if name in PRIMITIVE_NAMES:
        changed.update(_derive_siblings(changed))
    changed["relation_digest"] = _private_identity_digest(changed["schema_id"],
        {key: value for key, value in changed.items() if key != "relation_digest"})
    new_digest = _guarded_command_digest_v1(changed)
    assert new_digest != old_digest
    assert re.fullmatch(r"[0-9a-f]{64}", new_digest)
    with pytest.raises(ContractViolation):
        _validate_selector_instance(old_selector, changed)
    if name not in PRIMITIVE_NAMES:
        with pytest.raises(ContractViolation) as error:
            _validate_command_relation(changed, *_verified_admission_fixture())
        assert error.value.boundary.startswith("preassignment_sibling:")
    else:
        new_selector = _selector_instance(changed)
        assert new_selector["command_digest"] == new_digest
        assert new_selector["selector_digest"] == _private_identity_digest(
            new_selector["schema_id"],
            {key: value for key, value in new_selector.items() if key != "selector_digest"})


@pytest.mark.parametrize("field,route_index,boundary", [
    ("lineage_ref", 7, "selector_command_binding:lineage_ref"),
    ("admission_fact_digest", 7, "selector_command_binding:admission_fact_digest"),
    ("family_route", 6, "selector_command_binding:family_route"),
    ("decision_ref", 1, "selector_command_binding:decision_ref"),
])
def test_self_consistent_selector_route_mutation_still_rejects_command_mismatch(field, route_index, boundary):
    command = _command_coordinates()
    selector = _selector_instance(command)
    selector[field] = "12" * 32 if field.endswith("_digest") or field in {"family_route", "decision_ref"} else "foreign-lineage"
    route = selector["required_collision_routes"][route_index]
    template = ROUTES[route_index]
    route["key"] = [selector[name] for name in template["key_sources"]]
    selector["selector_digest"] = _private_identity_digest(selector["schema_id"],
        {name: value for name, value in selector.items() if name != "selector_digest"})
    with pytest.raises(ContractViolation) as error:
        _validate_selector_instance(selector, command)
    assert error.value.boundary == boundary


def test_same_mutation_different_canonical_command_digest_is_conflict():
    command = _command_coordinates()
    different = deepcopy(command)
    different["decision_basis_ref"] = "different-basis-A"
    different.update(_derive_siblings(different))
    different["relation_digest"] = _private_identity_digest(different["schema_id"],
        {name: value for name, value in different.items() if name != "relation_digest"})
    _validate_command_relation(different, *_verified_admission_fixture())
    assert different["mutation_ref"] == command["mutation_ref"]
    assert _guarded_command_digest_v1(different) != _guarded_command_digest_v1(command)
    with pytest.raises(ContractViolation) as error:
        _validate_selector_instance(_selector_instance(command), different)
    assert error.value.boundary == "selector_command_binding:command_digest"
    _validate_selector_instance(_selector_instance(different), different)
    assert RECOVERY["same_mutation_different_digest_reason"] == "mutation_ref_reuse_conflict"


def test_joint_tagged_prose_and_private_literal_change_fails_owner_value(monkeypatch):
    text, _ = _document()
    clause_id = "replay_original_fact_timestamp"
    hostile = "Replay might create a new fact."
    changed = text.replace(_normative_prefix(clause_id) + PROSE_CLAUSES[clause_id],
                           _normative_prefix(clause_id) + hostile)
    monkeypatch.setitem(PROSE_CLAUSES, clause_id, hostile)
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(changed)
    assert error.value.boundary == "normative_owner_prose_consequence:" + clause_id
    assert all(item["passes"] for item in _resolve_owner_consequence(clause_id,
        next(row for row in NORMATIVE_REGISTRY if row["clause_id"] == clause_id))["owner_assertions"])


@pytest.mark.parametrize("field,value", [
    ("scope_ref", "foreign-scope"),
    ("lineage_ref", "foreign-lineage"),
    ("command_digest", "12" * 32),
    ("historical_head_revision", 6),
    ("historical_head_digest", "13" * 32),
    ("decision_digest", "14" * 32),
    ("version_digest", "15" * 32),
    ("generic_result_projection_digest", "16" * 32),
])
def test_fully_resealed_target_family_still_fails_independent_fixed_oracle(field, value):
    command = _command_coordinates()
    family = _family_fixture("candidate_acceptance", command)
    relation = family["family_relation"]
    relation[field] = value
    relation["relation_digest"] = _private_identity_digest(relation["schema_id"],
        {name: item for name, item in relation.items() if name != "relation_digest"})
    family["relation_digest"] = relation["relation_digest"]
    guarded = family["guarded_result"]
    guarded["family_relation_digest"] = relation["relation_digest"]
    guarded["guarded_result_digest"] = _private_identity_digest(guarded["schema_id"],
        {name: item for name, item in guarded.items() if name != "guarded_result_digest"})
    roles = _receipt_roles_fixture("candidate_acceptance", family["acceptance_fact"])
    roles[-2]["record_digest"] = relation["relation_digest"]
    roles[-1]["record_digest"] = guarded["guarded_result_digest"]
    resealed_graph = _source_exact_graph_digest(command, family, roles)
    assert resealed_graph != FIXED_CANONICAL_OUTPUTS["candidate_acceptance"]["graph"]
    with pytest.raises(ContractViolation) as error:
        _assert_fixed_canonical_family(family, "candidate_acceptance")
    assert error.value.boundary in {"fixed_canonical_family:relation",
                                    "fixed_canonical_family:guarded_result"}


@pytest.mark.parametrize("branch", list(BRANCHES))
def test_v1_decision_kind_variant_cannot_cross_branch_after_digest_reseal(branch):
    from ge_nwp_coordinator import _development_decision_row_values as source

    family = _family_fixture(branch)
    row = deepcopy(family["decision_row"])
    foreign = next(other for other in BRANCHES if other != branch)
    row["decision_kind"] = BRANCHES[foreign][0]
    row["decision_variant"] = BRANCHES[foreign][1]
    row["decision_digest"] = _private_identity_digest(row["schema_id"],
        {name: item for name, item in row.items() if name != "decision_digest"})
    try:
        parsed = source.development_decision_row_value_from_row_tuple(
            tuple(row[name] for name in V1_DECISION_COLUMNS))
    except Exception:
        return
    assert parsed.decision_variant != BRANCHES[branch][1]
    assert parsed.computed_digest() != FIXED_CANONICAL_OUTPUTS[branch]["decision"]


@pytest.mark.parametrize("revision", [True, 6])
def test_resealed_wrong_historical_head_revision_rejected(revision):
    from ge_nwp_coordinator import _development_program_row_values as source

    family = _family_fixture("candidate_acceptance")
    row = deepcopy(family["historical_head_postimage_row"])
    row["head_revision"] = revision
    row["head_digest"] = _private_identity_digest(row["schema_id"],
        {name: item for name, item in row.items() if name != "head_digest"})
    if type(revision) is bool:
        with pytest.raises(Exception):
            source.development_program_head_row_value_from_row_tuple(
                tuple(row[name] for name in V1_HEAD_COLUMNS))
    else:
        parsed = source.development_program_head_row_value_from_row_tuple(
            tuple(row[name] for name in V1_HEAD_COLUMNS))
        assert parsed.computed_digest() != FIXED_CANONICAL_OUTPUTS["candidate_acceptance"]["head"]


def test_joint_profile_and_role_inventory_mutation_fails_fixed_profile_oracle():
    _, profile = _document()
    changed = deepcopy(profile)
    changed["receipt_graph_profile_definition"]["schema_id"] += ".foreign"
    changed["graph"]["common_roles"][0] = "foreign_admission_act"
    changed["receipt_graph_profile_definition"]["common_roles"][0] = "foreign_admission_act"
    with pytest.raises(ContractViolation) as error:
        _validate(changed)
    assert error.value.boundary in {"receipt_graph_profile_definition", "receipt_graph"}


def test_prospective_coordinate_is_not_passed_into_shared_c2_state():
    c2 = _load_c2_shared()
    state = c2._state_for_authoritative_branch(c2.EXPECTED_CONTRACT,
                                                "candidate_repair")
    command = _command_coordinates()
    act, fact = _verified_admission_fixture()
    original = c2._interpret
    seen = []

    def observed(contract, reduction_state):
        assert "preassigned_acceptance_fact_ref" not in reduction_state
        assert "prospective_acceptance_fact_ref" not in reduction_state
        seen.append(True)
        return original(contract, reduction_state)

    try:
        c2._interpret = observed
        result = _private_branch_path(c2, command, act, fact, state,
                                      fresh_posture=deepcopy(FRESH_POSTURE_VECTOR))
    finally:
        c2._interpret = original
    assert seen == [True]
    assert result["branch"] == "candidate_repair"


@pytest.mark.parametrize("branch", list(BRANCHES))
def test_exact_replay_projection_keeps_canonical_family_bytes_and_timestamp(branch):
    command = _command_coordinates()
    family = _family_fixture(branch, command)
    roles = _receipt_roles_fixture(branch, family["acceptance_fact"], command)
    receipt = dict(_source_exact_receipt_preimage(command, family),
                   mutation_graph_digest=FIXED_CANONICAL_OUTPUTS[branch]["graph"])
    original = {
        "decision": family["decision_row"],
        "version": family["version_row"],
        "historical_head_postimage": family["historical_head_postimage_row"],
        "optional_acceptance_fact": family["acceptance_fact"],
        "guarded_relation": family["family_relation"],
        "guarded_result": family["guarded_result"],
        "graph_entries": roles,
        "receipt": receipt,
        "transaction_timestamp": family["transaction_timestamp"],
    }
    original_bytes = json.dumps(original, ensure_ascii=False, allow_nan=False,
                                sort_keys=True, separators=(",", ":")).encode("utf-8")
    replayed = deepcopy(original)
    replay_bytes = json.dumps(replayed, ensure_ascii=False, allow_nan=False,
                             sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert replay_bytes == original_bytes
    assert replayed["transaction_timestamp"] == receipt["committed_at"]
    assert replayed["optional_acceptance_fact"] is None if branch != "candidate_acceptance" else replayed["optional_acceptance_fact"] == family["acceptance_fact"]
    assert REPLAY["new_fact"] is REPLAY["new_timestamp"] is False
    changed = deepcopy(replayed)
    changed["transaction_timestamp"] = "2026-01-01T00:00:01Z"
    assert json.dumps(changed, sort_keys=True, separators=(",", ":")).encode() != original_bytes

# V6 lifecycle partitions are checked against independently authored node and
# edge rows above. A post-read stage number is not a cross-lifecycle clock.
@pytest.mark.parametrize("branch", list(BRANCHES))
def test_v6_fresh_write_dag_exact_nodes_edges_and_prebranch_ancestry(branch):
    _, profile = _document()
    registry = profile["dependency_registry"]
    _validate_dependency_registry(registry)
    partition = registry["lifecycle_partitions"][FRESH_LIFECYCLE]["branch_dags"][branch]
    expected = EXPECTED_DEPENDENCY_REGISTRY["lifecycle_partitions"][FRESH_LIFECYCLE]["branch_dags"][branch]
    _exact(partition, expected, "v6_fresh_partition")
    rows = {row["node"]: row for row in registry["nodes"]}
    active = set(partition["nodes"])
    assert len(active) == partition["node_count"]
    assert sum(len(rows[name]["common_dependencies"]) + len(rows[name]["dependencies_by_branch"].get(branch, []))
               for name in active) == partition["edge_count"]
    ancestors = set()
    frontier = ["authoritative_branch"]
    while frontier:
        name = frontier.pop()
        for parent in rows[name]["common_dependencies"] + rows[name]["dependencies_by_branch"].get(branch, []):
            if parent not in ancestors:
                ancestors.add(parent)
                frontier.append(parent)
    assert {"validated_admission_command_and_current_posture", "command_digest",
            "closed_command_relation_value", "verified_admission_act",
            "verified_scope_admission_fact", "fresh_current_continuity_posture",
            "fresh_current_sole_active_posture", "local_writer_session_fence"} <= ancestors
    assert {"replay_projection", "recovery_projection", *registry["recovery_observation_nodes"]}.isdisjoint(active)
    acceptance = {"acceptance_fact_value", "acceptance_fact_digest"}
    assert (acceptance <= active) == (branch == "candidate_acceptance")
    assert "transaction_timestamp" in active
    assert partition["nodes"].index("authoritative_branch") < partition["nodes"].index("transaction_timestamp")


def test_v6_exact_replay_and_uncertain_recovery_are_postread_graphs():
    _, profile = _document()
    registry = profile["dependency_registry"]
    _validate_dependency_registry(registry)
    replay = registry["lifecycle_partitions"][REPLAY_LIFECYCLE]["dag"]
    recovery = registry["lifecycle_partitions"][RECOVERY_LIFECYCLE]["dag"]
    _exact(replay, EXPECTED_DEPENDENCY_REGISTRY["lifecycle_partitions"][REPLAY_LIFECYCLE]["dag"],
           "v6_replay_partition")
    _exact(recovery, EXPECTED_DEPENDENCY_REGISTRY["lifecycle_partitions"][RECOVERY_LIFECYCLE]["dag"],
           "v6_recovery_partition")
    assert replay["node_count"] == 7 and replay["edge_count"] == 8
    assert recovery["node_count"] == 56 and recovery["edge_count"] == 157
    assert {"replay_receipt_first_mutation_lookup", "replay_canonical_command_digest_observation",
            "replay_exact_persisted_family", "replay_projection"} <= set(replay["nodes"])
    assert {"recovery_selector_value", "complete_family_recovery_observation_set_v1",
            "recovery_projection", *registry["recovery_observation_nodes"]} <= set(recovery["nodes"])
    assert "authoritative_branch" not in replay["nodes"]
    assert "authoritative_branch" not in recovery["nodes"]
    assert "generic_receipt_row_value" not in replay["nodes"]
    assert "generic_receipt_row_value" not in recovery["nodes"]
    changed = deepcopy(registry)
    next(row for row in changed["nodes"] if row["node"] == "recovery_projection")["stage"] = -100
    _validate_dependency_registry(changed)


@pytest.mark.parametrize("fault", [
    "recovery_in_fresh", "branch_from_recovery", "omit_validated_ancestor",
    "historical_substitutes_fresh", "replay_in_fresh", "recovery_creates_member",
    "acceptance_node_missing", "acceptance_edge_on_nonaccept",
])
def test_v6_lifecycle_hostile_partition_controls(fault):
    _, profile = _document()
    changed = deepcopy(profile["dependency_registry"])
    rows = {row["node"]: row for row in changed["nodes"]}
    if fault == "recovery_in_fresh":
        rows["recovery_projection"]["lifecycle_memberships"].insert(0, FRESH_LIFECYCLE)
    elif fault == "branch_from_recovery":
        rows["authoritative_branch"]["common_dependencies"].append("recovery_projection")
    elif fault == "omit_validated_ancestor":
        rows["authoritative_branch"]["common_dependencies"].remove(
            "validated_admission_command_and_current_posture")
    elif fault == "historical_substitutes_fresh":
        rows["validated_admission_command_and_current_posture"]["common_dependencies"].remove(
            "fresh_current_continuity_posture")
        rows["validated_admission_command_and_current_posture"]["common_dependencies"].append(
            "verified_continuity_basis")
    elif fault == "replay_in_fresh":
        rows["replay_projection"]["lifecycle_memberships"].insert(0, FRESH_LIFECYCLE)
    elif fault == "recovery_creates_member":
        rows["generic_receipt_graph_entries_value"]["common_dependencies"].append(
            "recovery_route_observation:mutation_receipt_route")
    elif fault == "acceptance_node_missing":
        rows["acceptance_fact_digest"]["materializes_on"] = ["candidate_repair"]
    else:
        rows["family_relation_value"]["dependencies_by_branch"]["candidate_repair"] = [
            "acceptance_fact_value"]
    with pytest.raises(ContractViolation) as error:
        _validate_dependency_registry(changed)
    assert error.value.boundary.startswith("dependency_")


def test_v6_recovery_status_inventory_and_matrix_are_independently_fixed():
    _, profile = _document()
    observed = profile["recovery_observation_set"]
    assert tuple(observed["route_statuses"]) == FIXED_RECOVERY_STATUSES
    _exact(observed, RECOVERY_OBSERVATION_SET, "recovery_observation_set")
    assert len(observed["route_roles"]) == 8
    for status in FIXED_RECOVERY_STATUSES:
        rules = observed["route_status_rules"][status]
        assert rules["read_attempted"] is (status != "unchecked")
        assert rules["readable"] is (status not in {"unchecked", "unreadable"})
        assert rules["total_absence_proved"] is (status == "absent")
        assert rules["evidence_ref"] == ("null" if status in {"unchecked", "unreadable", "absent"}
                                         else "nonempty_string")
        assert rules["evidence_digest"] == ("null" if status in {"unchecked", "unreadable", "absent"}
                                            else "lowercase_sha256_hex")


@pytest.mark.parametrize("status", FIXED_RECOVERY_STATUSES)
def test_v6_every_recovery_status_exact_typed_fields(status):
    selector = _selector_instance(_command_coordinates())
    statuses = {role: "absent" for role in RECOVERY_MEMBER_REF_FIELDS}
    statuses["admitted_scope_winner_route" if status == "competing_complete_scope_winner"
             else "decision_identity_route"] = status
    observed = _typed_recovery_observation_set(selector, statuses, fresh_posture=FRESH_POSTURE_VECTOR)
    _validate_recovery_observation_set(selector, observed)
    row = observed["route_observations"][7 if status == "competing_complete_scope_winner" else 1]
    assert list(row) == RECOVERY_OBSERVATION_SET["route_observation_fields"]
    for field, value in (("read_attempted", not row["read_attempted"]),
                         ("readable", not row["readable"]),
                         ("total_absence_proved", not row["total_absence_proved"])):
        changed = deepcopy(observed)
        changed["route_observations"][7 if status == "competing_complete_scope_winner" else 1][field] = value
        with pytest.raises(ContractViolation) as error:
            _validate_recovery_observation_set(selector, changed)
        assert error.value.boundary == "recovery_status_matrix:" + field


@pytest.mark.parametrize("field,value,boundary", [
    ("evidence_ref", {}, "recovery_evidence_ref_type"),
    ("evidence_ref", True, "recovery_evidence_ref_type"),
    ("evidence_digest", [], "recovery_evidence_digest_type"),
    ("evidence_digest", True, "recovery_evidence_digest_type"),
])
def test_v6_recovery_evidence_rejects_nonstring_fields(field, value, boundary):
    selector = _selector_instance(_command_coordinates())
    statuses = {role: "absent" for role in RECOVERY_MEMBER_REF_FIELDS}
    statuses["decision_identity_route"] = "partial"
    observed = _typed_recovery_observation_set(selector, statuses, fresh_posture=FRESH_POSTURE_VECTOR)
    observed["route_observations"][1][field] = value
    with pytest.raises(ContractViolation) as error:
        _validate_recovery_observation_set(selector, observed)
    assert error.value.boundary == boundary


@pytest.mark.parametrize("fault", ["missing", "duplicate", "unreadable_as_absent",
                                  "unchecked_as_absent", "mixed_absent_partial",
                                  "historical_posture_pair", "no_fresh_posture"])
def test_v6_recovery_route_and_posture_negative_controls(fault):
    command = _command_coordinates()
    selector = _selector_instance(command)
    family = _family_fixture("candidate_acceptance", command)
    statuses = {role: "absent" for role in RECOVERY_MEMBER_REF_FIELDS}
    if fault == "mixed_absent_partial":
        statuses["decision_identity_route"] = "partial"
    if fault == "unreadable_as_absent":
        statuses["decision_identity_route"] = "unreadable"
    if fault == "unchecked_as_absent":
        statuses["decision_identity_route"] = "unchecked"
    observed = _typed_recovery_observation_set(selector, statuses, fresh_posture=FRESH_POSTURE_VECTOR)
    if fault == "missing":
        observed["route_observations"].pop()
    elif fault == "duplicate":
        observed["route_observations"][1] = deepcopy(observed["route_observations"][0])
    elif fault == "historical_posture_pair":
        observed["fresh_current_continuity"] = {
            "status": "positive", "posture_ref": "historical-continuity-basis-A",
            "posture_digest": "13" * 32}
    elif fault == "no_fresh_posture":
        observed["fresh_current_continuity"]["status"] = "stale"
    if fault in {"missing", "duplicate", "historical_posture_pair"}:
        with pytest.raises(ContractViolation):
            _classify_recovery_for_v7_fixture(command, "candidate_acceptance", family,
                                               selector, observed)
    else:
        outcome = _classify_recovery_for_v7_fixture(command, "candidate_acceptance", family,
                                                      selector, observed)
        assert outcome == "unresolved"


def test_v6_recovery_result_copies_two_current_posture_pairs_and_scope():
    command = _command_coordinates()
    selector = _selector_instance(command)
    statuses = {role: "absent" for role in RECOVERY_MEMBER_REF_FIELDS}
    observed = _typed_recovery_observation_set(selector, statuses, fresh_posture=FRESH_POSTURE_VECTOR)
    family = _family_fixture("candidate_acceptance", command)
    result = _project_recovery_for_v7_fixture(command, "candidate_acceptance", family,
        selector, observed,
        verified_fresh_posture=FRESH_POSTURE_VECTOR)
    assert tuple(result) == ("schema_id",) + RECOVERY_RESULT_FIELDS
    assert result["classification"] == "definitely_not_committed"
    assert result["lineage_ref"] == command["lineage_ref"]
    assert result["scope_ref"] == command["scope_ref"]
    assert result["current_continuity_posture_ref"] == FRESH_POSTURE_VECTOR[
        "fresh_current_continuity"]["evidence_ref"]
    assert result["current_sole_active_posture_digest"] == FRESH_POSTURE_VECTOR[
        "fresh_current_sole_active"]["evidence_digest"]
    assert "fresh_acceptance_eligible" not in result
    historical = deepcopy(observed)
    historical["fresh_current_continuity"]["posture_ref"] = "historical-basis-ref"
    with pytest.raises(ContractViolation) as error:
        _project_recovery_for_v7_fixture(command, "candidate_acceptance", family,
            selector, historical,
            verified_fresh_posture=FRESH_POSTURE_VECTOR)
    assert error.value.boundary == "recovery_result_current_posture_binding"


def test_v7_recovery_result_has_one_seven_field_grammar_in_every_representation():
    text, profile = _document()
    fields = list(RECOVERY_RESULT_FIELDS)
    assert profile["schemas"][-1][4] == ["schema_id"] + fields
    assert profile["recovery_observation_set"]["result_fields"] == fields
    assert profile["private_contract_vocabulary"]["recovery_result_payload_fields"] == fields
    section = text.split("| Position | Recovery-result semantic field | Validated source |\n", 1)[1]
    section = section.split("\n\n", 1)[0]
    lines = section.splitlines()
    assert lines.pop(0) == "|---:|---|---|"
    assert [re.findall(r"`([^`]+)`", line)[0] for line in lines] == fields
    assert [int(line.split("|")[1].strip()) for line in lines] == list(range(1, 8))
    assert "fresh_external_posture_ref" not in profile["schemas"][-1][4]
    assert "observed_family_digest" not in profile["schemas"][-1][4]


def test_v7_recovery_result_projection_computes_classification_and_cannot_override():
    import inspect
    assert "classification" not in inspect.signature(_recovery_result_projection).parameters
    command = _command_coordinates()
    branch = "candidate_acceptance"
    family = _family_fixture(branch, command)
    selector = _selector_instance(command)
    statuses = {role: "absent" for role in RECOVERY_MEMBER_REF_FIELDS}
    absent = _typed_recovery_observation_set(selector, statuses,
        fresh_posture=FRESH_POSTURE_VECTOR)
    result = _project_recovery_for_v7_fixture(command, branch, family, selector, absent,
        verified_fresh_posture=FRESH_POSTURE_VECTOR)
    assert result["classification"] == "definitely_not_committed"
    assert result["schema_id"] == EXPECTED_SCHEMAS[-1][1]
    assert list(result) == EXPECTED_SCHEMAS[-1][4]
    assert result["lineage_ref"] == selector["lineage_ref"]
    assert result["scope_ref"] == selector["scope_ref"]
    assert result["current_continuity_posture_ref"] == FRESH_POSTURE_VECTOR[
        "fresh_current_continuity"]["evidence_ref"]
    assert result["current_continuity_posture_digest"] == FRESH_POSTURE_VECTOR[
        "fresh_current_continuity"]["evidence_digest"]
    assert result["current_sole_active_posture_ref"] == FRESH_POSTURE_VECTOR[
        "fresh_current_sole_active"]["evidence_ref"]
    assert result["current_sole_active_posture_digest"] == FRESH_POSTURE_VECTOR[
        "fresh_current_sole_active"]["evidence_digest"]
    with pytest.raises(TypeError):
        _project_recovery_for_v7_fixture(command, branch, family, selector, absent,
            classification="committed_exact", verified_fresh_posture=FRESH_POSTURE_VECTOR)
    partial = deepcopy(absent)
    row = partial["route_observations"][1]
    row.update(status="partial", evidence_ref="partial-decision-A",
               evidence_digest=_route_evidence_digest("partial-decision-A"),
               total_absence_proved=False)
    assert _project_recovery_for_v7_fixture(command, branch, family, selector, partial,
        verified_fresh_posture=FRESH_POSTURE_VECTOR)["classification"] == "unresolved"
    incomplete = deepcopy(absent)
    incomplete["route_observations"].pop()
    with pytest.raises(ContractViolation) as error:
        _project_recovery_for_v7_fixture(command, branch, family, selector, incomplete,
            verified_fresh_posture=FRESH_POSTURE_VECTOR)
    assert error.value.boundary == "recovery_route_coverage"
    winner = deepcopy(absent)
    winner["route_observations"][-1].update(
        status="competing_complete_scope_winner", evidence_ref="scope-winner-B",
        evidence_digest=_route_evidence_digest("scope-winner-B"),
        total_absence_proved=False)
    projected_winner = _project_recovery_for_v7_fixture(command, branch, family, selector, winner,
        verified_fresh_posture=FRESH_POSTURE_VECTOR)
    assert projected_winner["classification"] == "definitely_not_committed"
    assert "fresh_acceptance_eligible" not in projected_winner
    complete = _typed_recovery_observation_set(selector,
        {role: "exact_complete_family" for role in RECOVERY_MEMBER_REF_FIELDS},
        fresh_posture=FRESH_POSTURE_VECTOR)
    for row in complete["route_observations"]:
        row["evidence_ref"] = _complete_observation_ref(
            selector[RECOVERY_MEMBER_REF_FIELDS[row["route_role"]]],
            FIXED_CANONICAL_OUTPUTS[branch]["graph"])
        row["evidence_digest"] = _route_evidence_digest(row["evidence_ref"])
    assert _project_recovery_for_v7_fixture(command, branch, family, selector, complete,
        verified_fresh_posture=FRESH_POSTURE_VECTOR)["classification"] == "committed_exact"
    historical = deepcopy(absent)
    historical["fresh_current_sole_active"]["posture_ref"] = "historical-basis"
    with pytest.raises(ContractViolation) as error:
        _project_recovery_for_v7_fixture(command, branch, family, selector, historical,
            verified_fresh_posture=FRESH_POSTURE_VECTOR)
    assert error.value.boundary == "recovery_result_current_posture_binding"


@pytest.mark.parametrize("representation", [
    "schema_old_composite", "schema_observed_digest", "schema_no_lineage",
    "schema_no_continuity", "schema_no_sole_active", "observation_old_composite",
    "observation_no_scope", "vocabulary_changed_fields", "vocabulary_changed_status",
    "consumer_old_vocabulary_id",
])
def test_v7_one_sided_recovery_and_vocabulary_drift_rejected(representation):
    _, profile = _document()
    changed = deepcopy(profile)
    fields = changed["schemas"][-1][4]
    if representation == "schema_old_composite":
        fields[:] = ["schema_id", "classification", "selector_digest", "observed_family_digest",
                     "fresh_external_posture_ref", "fresh_external_posture_digest", "reason",
                     "result_digest"]
    elif representation == "schema_observed_digest":
        fields.append("observed_family_digest")
    elif representation == "schema_no_lineage":
        fields.remove("lineage_ref")
    elif representation == "schema_no_continuity":
        fields.remove("current_continuity_posture_digest")
    elif representation == "schema_no_sole_active":
        fields.remove("current_sole_active_posture_ref")
    elif representation == "observation_old_composite":
        changed["recovery_observation_set"]["result_fields"] = [
            "classification", "fresh_external_posture_ref", "fresh_external_posture_digest"]
    elif representation == "observation_no_scope":
        changed["recovery_observation_set"]["result_fields"].remove("scope_ref")
    elif representation == "vocabulary_changed_fields":
        changed["private_contract_vocabulary"]["recovery_result_payload_fields"].remove("lineage_ref")
    elif representation == "vocabulary_changed_status":
        changed["private_contract_vocabulary"]["route_observation_statuses"][6] = "corrupt"
    else:
        changed["recovery_observation_set"]["private_contract_vocabulary_id"] = "successor-v2"
    with pytest.raises(ContractViolation):
        _validate(changed)


def test_v7_static_vocabulary_profile_and_all_v1_consumers():
    _, profile = _document()
    _exact(profile["private_contract_vocabulary"], PRIVATE_VOCABULARY,
           "private_contract_vocabulary")
    assert profile["dependency_registry"]["private_contract_vocabulary_id"] == PRIVATE_VOCABULARY_ID
    assert profile["recovery_observation_set"]["private_contract_vocabulary_id"] == PRIVATE_VOCABULARY_ID
    assert tuple(profile["dependency_registry"]["lifecycle_partitions"]) == LIFECYCLE_NAMES
    assert tuple(profile["recovery_observation_set"]["route_statuses"]) == FIXED_RECOVERY_STATUSES
    assert profile["schemas"][-1][4][1:] == list(RECOVERY_RESULT_FIELDS)

RELATION_RAW_FIELDS = tuple(EXPECTED_SCHEMAS[6][4][:-1])
assert len(RELATION_RAW_FIELDS) == 26


def _different_same_type_relation_value(field, value):
    if type(value) is str:
        if field == "branch":
            return "candidate_repair"
        changed = ("cd" * 32 if re.fullmatch(r"[0-9a-f]{64}", value) else value + "-foreign")
        assert type(changed) is str and changed != value
        return changed
    if type(value) is int:
        return value + 1
    if type(value) is dict:
        changed = deepcopy(value)
        changed["head_revision"] += 1
        return changed
    raise AssertionError(field)


def _reseal_hostile_relation_and_downstream(branch, field, value):
    command = _command_coordinates()
    family = _family_fixture(branch, command)
    relation = family["family_relation"]
    relation[field] = value
    relation["relation_digest"] = _private_identity_digest(relation["schema_id"],
        {name: relation[name] for name in RELATION_RAW_FIELDS})
    family["relation_digest"] = relation["relation_digest"]
    guarded = family["guarded_result"]
    guarded["family_relation_ref"] = relation["relation_ref"]
    guarded["family_relation_digest"] = relation["relation_digest"]
    guarded["guarded_result_digest"] = _private_identity_digest(guarded["schema_id"],
        {name: guarded[name] for name in guarded if name != "guarded_result_digest"})
    roles = _receipt_roles_fixture(branch, family["acceptance_fact"], command)
    for role in roles:
        if role["role"] == "guarded_family_relation":
            role["record_ref"] = relation["relation_ref"]
            role["record_digest"] = relation["relation_digest"]
        if role["role"] == "guarded_result_composite":
            role["record_digest"] = guarded["guarded_result_digest"]
    graph_digest = _source_exact_graph_digest(command, family, roles)
    receipt_row = dict(_source_exact_receipt_preimage(command, family),
                       mutation_graph_digest=graph_digest)
    assert graph_digest != FIXED_CANONICAL_OUTPUTS[branch]["graph"]
    return command, family, relation, roles, receipt_row


@pytest.mark.parametrize("field", RELATION_RAW_FIELDS)
def test_v6_every_raw_relation_field_resealed_hostile_family_rejected(field):
    original = _family_fixture("candidate_acceptance")["family_relation"][field]
    value = _different_same_type_relation_value(field, original)
    command, family, relation, roles, receipt = _reseal_hostile_relation_and_downstream(
        "candidate_acceptance", field, value)
    assert relation["relation_digest"] == _private_identity_digest(relation["schema_id"],
        {name: relation[name] for name in RELATION_RAW_FIELDS})
    assert receipt["mutation_graph_digest"] == _source_exact_graph_digest(command, family, roles)
    with pytest.raises(ContractViolation) as error:
        _validate_relation_family("candidate_acceptance", relation, family["acceptance_fact"],
                                  roles, command, _selector_instance(command))
    wanted = {"acceptance_fact_ref": "relation_fact_ref",
              "acceptance_fact_digest": "relation_fact_digest"}.get(
                  field, "relation_field_binding:" + field)
    assert error.value.boundary == wanted


@pytest.mark.parametrize("field", EXPECTED_SCHEMAS[6][4])
def test_v6_relation_every_required_field_omission_rejected(field):
    command = _command_coordinates()
    family = _family_fixture("candidate_acceptance", command)
    relation = deepcopy(family["family_relation"])
    del relation[field]
    with pytest.raises(ContractViolation) as error:
        _validate_relation_family("candidate_acceptance", relation, family["acceptance_fact"],
                                  _receipt_roles_fixture("candidate_acceptance", family["acceptance_fact"]),
                                  command, _selector_instance(command))
    assert error.value.boundary == "relation_full_field_order"


def test_v6_relation_extra_reordered_duplicate_and_hidden_default_rejected():
    command = _command_coordinates()
    family = _family_fixture("candidate_acceptance", command)
    roles = _receipt_roles_fixture("candidate_acceptance", family["acceptance_fact"])
    selector = _selector_instance(command)
    original = family["family_relation"]
    variants = []
    extra = deepcopy(original)
    extra["unknown"] = "value"
    variants.append(extra)
    reordered = dict(reversed(list(original.items())))
    variants.append(reordered)
    variants.append({"acceptance_fact_ref": original["acceptance_fact_ref"],
                     "acceptance_fact_digest": original["acceptance_fact_digest"]})
    for variant in variants:
        with pytest.raises(ContractViolation) as error:
            _validate_relation_family("candidate_acceptance", variant,
                                      family["acceptance_fact"], roles, command, selector)
        assert error.value.boundary == "relation_full_field_order"
    raw = json.dumps(original, separators=(",", ":"))
    raw = raw.replace('"schema_id":', '"schema_id":"duplicate", "schema_id":', 1)
    with pytest.raises(ContractViolation) as error:
        _strict_json(raw)
    assert error.value.boundary == "duplicate_json_key"


def test_v6_relation_nullability_and_boolean_head_revision_rejected():
    command = _command_coordinates()
    selector = _selector_instance(command)
    for branch in BRANCHES:
        family = _family_fixture(branch, command)
        roles = _receipt_roles_fixture(branch, family["acceptance_fact"])
        for field in ("acceptance_fact_ref", "acceptance_fact_digest"):
            relation = deepcopy(family["family_relation"])
            relation[field] = None if branch == "candidate_acceptance" else "foreign-nonnull"
            relation["relation_digest"] = _private_identity_digest(relation["schema_id"],
                {name: relation[name] for name in RELATION_RAW_FIELDS})
            with pytest.raises(ContractViolation) as error:
                _validate_relation_family(branch, relation, family["acceptance_fact"],
                                          roles, command, selector)
            assert error.value.boundary in {"relation_fact_ref", "relation_fact_digest",
                                            "relation_nonaccept_ref_null",
                                            "relation_nonaccept_digest_null"}
    family = _family_fixture("candidate_acceptance", command)
    relation = deepcopy(family["family_relation"])
    relation["historical_head_revision"] = True
    relation["relation_digest"] = _private_identity_digest(relation["schema_id"],
        {name: relation[name] for name in RELATION_RAW_FIELDS})
    with pytest.raises(ContractViolation) as error:
        _validate_relation_family("candidate_acceptance", relation, family["acceptance_fact"],
                                  _receipt_roles_fixture("candidate_acceptance", family["acceptance_fact"]),
                                  command, selector)
    assert error.value.boundary == "relation_field_binding:historical_head_revision"

@pytest.mark.parametrize("clause_id", [
    "replay_original_fact_timestamp", "branch_nonselection", "total_absence_currentness",
    "admitted_scope_only", "nonaccept_fact_collision", "terminal_nonreplenishment",
    "es_nonreplenishment", "single_result_receipt_replay_recovery",
])
def test_v6_joint_private_prose_machine_and_literal_reversal_fails_owner(clause_id, monkeypatch):
    text, profile = _document()
    original = PROSE_CLAUSES[clause_id]
    hostile = {
        "replay_original_fact_timestamp": "Exact replay may create a new acceptance fact and timestamp.",
        "branch_nonselection": "The prospective fact coordinate may force the authoritative branch.",
        "total_absence_currentness": "Local absence may prove noncommit.",
        "admitted_scope_only": "A command relation may admit an unadmitted scope.",
        "nonaccept_fact_collision": "A nonaccept branch may skip the acceptance collision route.",
        "terminal_nonreplenishment": "A terminal outcome may replenish acceptance.",
        "es_nonreplenishment": "ES routing may replenish the direct-local allowance.",
        "single_result_receipt_replay_recovery": "The guarded family may create a second receipt.",
    }[clause_id]
    changed_text = text.replace(_normative_prefix(clause_id) + original,
                                _normative_prefix(clause_id) + hostile)
    changed_profile = deepcopy(profile)
    row = next(item for item in changed_profile["normative_clause_registry"]
               if item["clause_id"] == clause_id)
    row["private_structural_consequence"] = "reversed_" + row["private_structural_consequence"]
    monkeypatch.setitem(PROSE_CLAUSES, clause_id, hostile)
    monkeypatch.setattr(__import__(__name__), "_document", lambda: (changed_text, changed_profile))
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(changed_text)
    assert error.value.boundary == "normative_clause_registry"


def test_v6_owner_resolver_has_generic_owner_value_path(monkeypatch):
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "_resolve_owner_consequence")
    calls = {ast.unparse(node.func) for node in ast.walk(function) if isinstance(node, ast.Call)}
    assert "_owner_machine_at_marker" in calls
    assert "_compare_owner_value" in calls
    assert "_check_private_structural_consequence" in calls
    assert "all" in calls
    names = {node.id for node in ast.walk(function) if isinstance(node, ast.Name)}
    assert {"PROSE_CLAUSES", "OWNER_ACTION_BY_DECISIVE_PATH",
            "OWNER_REQUIRED_ACTIONS", "FIXED_OWNER_MEANINGS",
            "action", "polarity"}.isdisjoint(names)
    for clause_id, row in zip(OWNER_REFERENCE_RULES, NORMATIVE_REGISTRY, strict=True):
        derived = _resolve_owner_consequence(clause_id, row)
        assert derived["private_structural_consequence"] == OWNER_REFERENCE_RULES[clause_id][2]
        assert all(item["passes"] for item in derived["owner_assertions"])
    original_reader = _owner_machine_at_marker
    def reversed_owner(path, marker):
        owner = deepcopy(original_reader(path, marker))
        owner["family"]["replay_new_fact"] = True
        return owner
    monkeypatch.setattr(__import__(__name__), "_owner_machine_at_marker", reversed_owner)
    row = next(item for item in NORMATIVE_REGISTRY if item["clause_id"] ==
               "replay_original_fact_timestamp")
    with pytest.raises(ContractViolation) as error:
        _resolve_owner_consequence("replay_original_fact_timestamp", row)
    assert error.value.boundary == "normative_owner_assertion:replay_original_fact_timestamp"


@pytest.mark.parametrize("fault", ["unrelated_pointer", "foreign_marker", "foreign_owner_document"])
def test_v6_owner_reference_exact_marker_and_path_rejects_shadow(fault):
    row = deepcopy(NORMATIVE_REGISTRY[7])
    if fault == "unrelated_pointer":
        row["owner_assertions"][0]["json_pointer"] = "/es/separately_governed"
    elif fault == "foreign_marker":
        row["owner_machine_marker"] = "RW0_C2_DURABLE_DECISION_FINITE_ORACLE_BEGIN"
    else:
        row["owner_document"] = OWNER_DOCS["decision"][0]
    with pytest.raises(ContractViolation) as error:
        _resolve_owner_consequence("replay_original_fact_timestamp", row)
    assert error.value.boundary == "normative_owner_reference_inventory"


@pytest.mark.parametrize("neutral", [
    "The replay glossary may include the term timestamp.",
    "The replay diagram may describe receipt creation.",
    "This receipt documentation can include an example.",
    "Timestamp terminology might evolve in explanatory prose.",
])
def test_v6_neutral_compounds_are_not_protected_subjects(neutral):
    text, _ = _document()
    assert _authority_topics(neutral) == []
    _scan_normative_prose(text + "\n\n" + neutral + "\n")


@pytest.mark.parametrize("modal", ["may", "might", "must", "shall", "can", "could",
                                   "is permitted to", "is allowed to", "is authorized to",
                                   "is sufficient to", "may not", "must not", "cannot"])
def test_v6_exact_modal_inventory_is_recognized(modal):
    assert MODAL_RE.search("Replay " + modal + " create a new fact.")
    if modal in {"may not", "must not", "cannot"}:
        assert not _positive_authority("Replay " + modal + " create a new fact.")
    else:
        assert _positive_authority("Replay " + modal + " create a new fact.")
        assert _authority_topics("Replay " + modal + " create a new fact.") == [
            "replay_original_fact_timestamp"]


@pytest.mark.parametrize("assertion,topic", [
    ("Replay might create a new fact.", "replay_original_fact_timestamp"),
    ("A replay adapter may create a second receipt.", "single_result_receipt_replay_recovery"),
    ("Replay is authorized. It creates a new acceptance fact.", "replay_original_fact_timestamp"),
    ("The prospective acceptance coordinate could veto the authoritative branch.", "branch_nonselection"),
    ("Local row absence is sufficient to prove noncommit.", "total_absence_currentness"),
    ("A terminal outcome might renew acceptance.", "terminal_nonreplenishment"),
    ("ES routing could replenish the direct-local allowance.", "es_nonreplenishment"),
])
def test_v6_exact_protected_subject_action_parser(assertion, topic):
    assert _authority_topics(assertion) == [topic]
    text, _ = _document()
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(text + "\n\n" + assertion + "\n")
    assert error.value.boundary == "normative_untagged:" + topic


def test_v6_immediate_it_reference_stays_within_one_visible_block():
    assert _authority_topics("Replay is authorized. It creates a new acceptance fact.") == [
        "replay_original_fact_timestamp"]
    assert _authority_topics("It creates a new acceptance fact.") == []
    text, _ = _document()
    _scan_normative_prose(text + "\n\nReplay is authorized.\n\nIt creates a new acceptance fact.\n")


@pytest.mark.parametrize("assertion,topic", [
    ("Replay may create a new acceptance fact but no new timestamp.",
     "replay_original_fact_timestamp"),
    ("Replay may create a new acceptance fact and no new timestamp.",
     "replay_original_fact_timestamp"),
    ("Replay may not create a new fact; it may create a new timestamp.",
     "replay_original_fact_timestamp"),
    ("Replay may not create a new fact; Replay may create a second receipt.",
     "single_result_receipt_replay_recovery"),
    ("Replay may not create a new fact however Replay may create a new timestamp.",
     "replay_original_fact_timestamp"),
    ("Replay may not create a new fact although Replay may create a new timestamp.",
     "replay_original_fact_timestamp"),
    ("Replay may not create a new fact yet Replay may create a new timestamp.",
     "replay_original_fact_timestamp"),
    ("Replay may not create a new fact while Replay may create a new timestamp.",
     "replay_original_fact_timestamp"),
    ("A replay adapter might create a second receipt but no new timestamp.",
     "single_result_receipt_replay_recovery"),
    ("Replay is authorized. It creates a new acceptance fact.",
     "replay_original_fact_timestamp"),
    ("The prospective acceptance coordinate may force the authoritative branch.",
     "branch_nonselection"),
    ("The reserved acceptance-fact coordinate could veto the authoritative branch.",
     "branch_nonselection"),
    ("Local row absence is sufficient to prove noncommit without current posture.",
     "total_absence_currentness"),
    ("A nonaccept branch may skip the acceptance collision route.",
     "nonaccept_fact_collision"),
    ("A terminal outcome may replenish acceptance but cannot renew allowance.",
     "terminal_nonreplenishment"),
    ("ES routing may replenish the direct-local allowance yet may not renew scope.",
     "es_nonreplenishment"),
])
def test_v7_mixed_clause_positive_authority_is_not_cancelled(assertion, topic):
    assert _authority_topics(assertion) == [topic]
    text, _ = _document()
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(text + "\n\n" + assertion + "\n")
    assert error.value.boundary == "normative_untagged:" + topic


@pytest.mark.parametrize("style", ["heading", "bullet", "table", "quote", "link_label"])
def test_v7_mixed_clause_rejected_in_every_visible_markdown_form(style):
    text, _ = _document()
    assertion = "Replay may create a new acceptance fact but no new timestamp."
    rendered = {
        "heading": "\n## " + assertion + "\n",
        "bullet": "\n- " + assertion + "\n",
        "table": "\n| " + assertion + " |\n",
        "quote": "\n> " + assertion + "\n",
        "link_label": "\n[" + assertion + "](https://example.invalid/contract)\n",
    }[style]
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(text + rendered)
    assert error.value.boundary == "normative_untagged:replay_original_fact_timestamp"


def test_v7_context_does_not_cross_visible_blocks_or_neutral_compounds():
    text, _ = _document()
    _scan_normative_prose(text + "\n\nReplay is authorized.\n\nIt creates a new acceptance fact.\n")
    for neutral in (
        "The replay glossary may include the term timestamp.",
        "The replay diagram may describe receipt creation.",
        "This receipt documentation can include an example.",
        "Timestamp terminology might evolve in explanatory prose.",
    ):
        assert _authority_topics(neutral) == []
        _scan_normative_prose(text + "\n\n" + neutral + "\n")


def _v8_recovery_case(route_kind, raw_posture):
    command = _command_coordinates()
    branch = "candidate_acceptance"
    family = _family_fixture(branch, command)
    selector = _selector_instance(command)
    statuses = {role: "absent" for role in RECOVERY_MEMBER_REF_FIELDS}
    if route_kind == "complete":
        statuses = {role: "exact_complete_family" for role in RECOVERY_MEMBER_REF_FIELDS}
    elif route_kind == "winner":
        statuses["admitted_scope_winner_route"] = "competing_complete_scope_winner"
    elif route_kind == "partial":
        statuses["decision_identity_route"] = "partial"
    else:
        assert route_kind == "absent"
    observed = _typed_recovery_observation_set(selector, statuses,
                                               fresh_posture=raw_posture)
    if route_kind == "complete":
        for row in observed["route_observations"]:
            row["evidence_ref"] = _complete_observation_ref(
                selector[RECOVERY_MEMBER_REF_FIELDS[row["route_role"]]],
                FIXED_CANONICAL_OUTPUTS[branch]["graph"])
            row["evidence_digest"] = _route_evidence_digest(row["evidence_ref"])
    binding = _recovery_canonical_binding(command, branch, family, selector)
    posture = _current_recovery_posture_for_test(selector, raw_posture)
    return observed, binding, posture


def test_v8_current_recovery_posture_is_transient_closed_and_bound():
    _, profile = _document()
    _exact(profile["validated_current_recovery_posture"], CURRENT_RECOVERY_POSTURE,
           "validated_current_recovery_posture")
    assert CURRENT_RECOVERY_POSTURE["fields"] == list(CURRENT_RECOVERY_POSTURE_FIELDS)
    assert len(profile["schemas"]) == 11
    assert all(row[0] != CURRENT_RECOVERY_POSTURE["name"] for row in profile["schemas"])
    assert profile["schemas"][-1][4] == ["schema_id"] + list(RECOVERY_RESULT_FIELDS)


@pytest.mark.parametrize("raw_posture", [FRESH_POSTURE_VECTOR, ALTERNATE_POSTURE_VECTOR])
@pytest.mark.parametrize("route_kind,expected", [
    ("complete", "committed_exact"),
    ("absent", "definitely_not_committed"),
    ("winner", "definitely_not_committed"),
    ("partial", "unresolved"),
])
def test_v8_any_valid_positive_posture_has_generic_classification_and_exact_coordinates(
        raw_posture, route_kind, expected):
    observed, binding, posture = _v8_recovery_case(route_kind, raw_posture)
    assert _classify_complete_family_recovery(observed, binding, posture) == expected
    result = _recovery_result_projection(observed, binding, posture)
    assert result["classification"] == expected
    for field in CURRENT_RECOVERY_POSTURE_FIELDS:
        if field in result:
            assert result[field] == posture[field]
    assert "continuity_state" not in result and "sole_active_state" not in result
    assert "fresh_acceptance_eligible" not in result


@pytest.mark.parametrize("source,status", [
    ("fresh_current_continuity", state)
    for state in ("missing", "stale", "unknown", "conflicting", "negative")
] + [
    ("fresh_current_sole_active", state)
    for state in ("missing", "stale", "unknown", "conflicting", "negative")
])
@pytest.mark.parametrize("route_kind", ["complete", "absent", "winner", "partial"])
def test_v8_well_formed_nonpositive_posture_returns_unresolved(source, status, route_kind):
    raw = deepcopy(ALTERNATE_POSTURE_VECTOR)
    raw[source]["status"] = status
    observed, binding, posture = _v8_recovery_case(route_kind, raw)
    result = _recovery_result_projection(observed, binding, posture)
    assert result["classification"] == "unresolved"
    assert result["lineage_ref"] == posture["lineage_ref"]
    assert result["scope_ref"] == posture["scope_ref"]
    assert result["current_continuity_posture_ref"] == posture["current_continuity_posture_ref"]
    assert result["current_sole_active_posture_digest"] == posture["current_sole_active_posture_digest"]


@pytest.mark.parametrize("field,bad,boundary", [
    ("lineage_ref", "another-lineage", "current_recovery_posture_binding:lineage_ref"),
    ("scope_ref", "another-scope", "current_recovery_posture_binding:scope_ref"),
    ("current_continuity_posture_ref", "", "current_recovery_posture_ref:current_continuity_posture_ref"),
    ("current_sole_active_posture_ref", 7, "current_recovery_posture_type:current_sole_active_posture_ref"),
    ("current_continuity_posture_digest", "ABC", "current_recovery_posture_digest:current_continuity_posture_digest"),
    ("current_sole_active_posture_digest", True, "current_recovery_posture_type:current_sole_active_posture_digest"),
    ("continuity_state", "positive", "current_recovery_posture_continuity_state"),
    ("sole_active_state", "two_active", "current_recovery_posture_sole_active_state"),
])
def test_v8_malformed_or_foreign_current_posture_fails_value_validation(field, bad, boundary):
    observed, binding, posture = _v8_recovery_case("absent", FRESH_POSTURE_VECTOR)
    changed = deepcopy(posture)
    changed[field] = bad
    with pytest.raises(ContractViolation) as error:
        _recovery_result_projection(observed, binding, changed)
    assert error.value.boundary == boundary


def test_v8_historical_basis_cannot_construct_current_validation_record():
    observed, binding, _ = _v8_recovery_case("absent", FRESH_POSTURE_VECTOR)
    historical = {"latch_postimage_ref": "old", "latch_postimage_digest": "13" * 32}
    with pytest.raises(ContractViolation) as error:
        _recovery_result_projection(observed, binding, historical)
    assert error.value.boundary == "current_recovery_posture_shape"


def test_v8_projector_signature_and_classifier_return_dataflow_are_closed(monkeypatch):
    import inspect
    _, profile = _document()
    _exact(profile["recovery_projection_signature"], RECOVERY_PROJECTION_SIGNATURE,
           "recovery_projection_signature")
    signature = inspect.signature(_recovery_result_projection)
    assert list(signature.parameters) == RECOVERY_PROJECTION_SIGNATURE["parameters"]
    assert all(param.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD and
               param.default is inspect.Parameter.empty
               for param in signature.parameters.values())
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "_recovery_result_projection")
    assignments = [node for node in ast.walk(function) if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "classification"
                           for target in node.targets)]
    assert len(assignments) == 1
    call = assignments[0].value
    assert isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    assert call.func.id == RECOVERY_PROJECTION_SIGNATURE["classifier"]
    assert [arg.id for arg in call.args if isinstance(arg, ast.Name)] == [
        "observed_set", "canonical_binding", "validated_current_posture"]
    assert not call.keywords
    assert not any(isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant)
                   and node.slice.value == "classification" for node in ast.walk(function))
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                   and node.func.attr in {"get", "pop", "setdefault"} and
                   any(isinstance(arg, ast.Constant) and arg.value == "classification"
                       for arg in node.args) for node in ast.walk(function))
    result_dict = next(node.value for node in ast.walk(function) if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == "result"
                               for target in node.targets))
    assert isinstance(result_dict, ast.Dict)
    assert any(isinstance(key, ast.Constant) and key.value == "classification" and
               isinstance(value, ast.Name) and value.id == "classification"
               for key, value in zip(result_dict.keys, result_dict.values, strict=True))
    observed, binding, posture = _v8_recovery_case("absent", FRESH_POSTURE_VECTOR)
    module = __import__(__name__)
    for outcome in ("committed_exact", "definitely_not_committed", "unresolved"):
        monkeypatch.setattr(module, "_classify_complete_family_recovery",
                            lambda *_args, result=outcome: result)
        result = _recovery_result_projection(observed, binding, posture)
        assert result["classification"] == outcome
        assert result["lineage_ref"] == posture["lineage_ref"]
        assert result["current_continuity_posture_ref"] == posture["current_continuity_posture_ref"]


@pytest.mark.parametrize("location", ["argument", "binding", "observation", "posture"])
def test_v8_projector_rejects_caller_classification_and_unknown_keys(location):
    observed, binding, posture = _v8_recovery_case("absent", FRESH_POSTURE_VECTOR)
    if location == "argument":
        with pytest.raises(TypeError):
            _recovery_result_projection(observed, binding, posture,
                                        classification="committed_exact")
        return
    if location == "binding":
        binding["classification"] = "committed_exact"
        wanted = "recovery_canonical_binding_shape"
    elif location == "observation":
        observed["classification"] = "committed_exact"
        wanted = "recovery_observation_shape"
    else:
        posture["classification"] = "committed_exact"
        wanted = "current_recovery_posture_shape"
    with pytest.raises(ContractViolation) as error:
        _recovery_result_projection(observed, binding, posture)
    assert error.value.boundary == wanted


def test_v8_owner_assertion_profile_digest_and_independent_first_clause_vector():
    _, profile = _document()
    _validate_owner_assertion_profile(profile)
    assert len(_owner_registry_preimage(NORMATIVE_REGISTRY)) == 7357
    assert _owner_registry_digest(NORMATIVE_REGISTRY) == OWNER_ASSERTION_PROFILE_DIGEST
    assert len(_owner_registry_preimage(NORMATIVE_REGISTRY[:1])) == 492
    assert _owner_registry_digest(NORMATIVE_REGISTRY[:1]) == OWNER_FIRST_CLAUSE_DIGEST
    assert profile["owner_assertion_profile"]["profile_id"] == OWNER_ASSERTION_PROFILE_ID


@pytest.mark.parametrize("fault", ["profile_id", "digest", "first_vector", "inventory"])
def test_v8_owner_profile_one_sided_drift_fails(fault):
    _, profile = _document()
    changed = deepcopy(profile)
    if fault == "profile_id":
        changed["owner_assertion_profile"]["profile_id"] = "rw0-c2-private-owner-assertions-v2"
    elif fault == "digest":
        changed["owner_assertion_profile"]["registry_digest"] = "00" * 32
    elif fault == "first_vector":
        changed["owner_assertion_profile"]["first_clause_vector"]["digest"] = "00" * 32
    else:
        changed["normative_clause_registry"][0]["owner_assertions"][0]["expected_value"] = "unknown"
    with pytest.raises(ContractViolation) as error:
        _validate_owner_assertion_profile(changed)
    assert error.value.boundary in {"owner_assertion_profile", "normative_clause_registry"}


@pytest.mark.parametrize("consequence_id", list(STRUCTURAL_FAULTS))
def test_v8_each_structural_consequence_fails_through_full_clause_validation(
        consequence_id, monkeypatch):
    text, profile = _document()
    assert set(STRUCTURAL_FAULTS) == {row["private_structural_consequence"]
                                    for row in NORMATIVE_REGISTRY}
    changed = deepcopy(profile)
    section, key, hostile = STRUCTURAL_FAULTS[consequence_id]
    changed[section][key] = hostile
    clause = next(row["clause_id"] for row in NORMATIVE_REGISTRY
                  if row["private_structural_consequence"] == consequence_id)
    monkeypatch.setattr(__import__(__name__), "_document", lambda: (text, changed))
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(text)
    assert error.value.boundary == "normative_private_structure:" + clause


def test_v8_structural_helper_has_no_constant_or_private_success_table_return():
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "_check_private_structural_consequence")
    returns = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
    assert len(returns) == 13
    assert not any(isinstance(node.value, ast.Constant) and bool(node.value.value)
                   for node in returns)
    assert not any(isinstance(node.value, ast.Subscript) for node in returns)
    assert set(STRUCTURAL_FAULTS) == {row["private_structural_consequence"]
                                    for row in NORMATIVE_REGISTRY}


def test_v8_integrated_structural_controls_have_no_short_circuit():
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name ==
                    "test_v8_each_structural_consequence_fails_through_full_clause_validation")
    assert not any(isinstance(node, ast.Return) for node in ast.walk(function))
    calls = {ast.unparse(node.func) for node in ast.walk(function) if isinstance(node, ast.Call)}
    assert {"_scan_normative_prose", "monkeypatch.setattr", "pytest.raises"} <= calls
    assert "pytest.skip" not in calls
    assert set(STRUCTURAL_FAULTS) == {row["private_structural_consequence"]
                                    for row in NORMATIVE_REGISTRY}


V8_CONTRASTIVE_CHALLENGES = (
    ("Replay may create a new acceptance fact but no new timestamp.",
     "replay_original_fact_timestamp"),
    ("Replay may not create a new timestamp but may create a new acceptance fact.",
     "replay_original_fact_timestamp"),
    ("Replay may not create a new timestamp; may create a new acceptance fact.",
     "replay_original_fact_timestamp"),
    ("Replay may create a new acceptance fact; may not refresh a timestamp.",
     "replay_original_fact_timestamp"),
    ("Replay may not create a new fact but may create a second receipt.",
     "single_result_receipt_replay_recovery"),
    ("Replay may not create a new fact and may create a second receipt.",
     "single_result_receipt_replay_recovery"),
    ("Replay may not create a new fact, may create a second receipt.",
     "single_result_receipt_replay_recovery"),
    ("Replay may not refresh a timestamp, may create a new acceptance fact.",
     "replay_original_fact_timestamp"),
    ("Replay may create a new acceptance fact, may not refresh a timestamp.",
     "replay_original_fact_timestamp"),
    ("Replay may not create a new timestamp but may create a second receipt.",
     "single_result_receipt_replay_recovery"),
) + tuple(
    ("Replay may not create a new timestamp " + connector +
     " may create a new acceptance fact.", "replay_original_fact_timestamp")
    for connector in ("however", "although", "yet", "while")
) + tuple(
    ("Replay may create a new acceptance fact " + connector +
     " may not create a new timestamp.", "replay_original_fact_timestamp")
    for connector in ("however", "although", "yet", "while")
)


@pytest.mark.parametrize("assertion,topic", V8_CONTRASTIVE_CHALLENGES)
def test_v8_contrastive_segments_retain_subject_and_action_polarity(assertion, topic):
    assert _authority_topics(assertion) == [topic]
    text, _ = _document()
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(text + "\n\n" + assertion + "\n")
    assert error.value.boundary == "normative_untagged:" + topic


@pytest.mark.parametrize("style", ["heading", "bullet", "table", "quote", "link_label"])
def test_v8_reversed_clause_fails_in_every_visible_markdown_form(style):
    text, _ = _document()
    assertion = "Replay may not create a new timestamp but may create a new acceptance fact."
    rendered = {
        "heading": "\n## " + assertion + "\n",
        "bullet": "\n- " + assertion + "\n",
        "table": "\n| " + assertion + " |\n",
        "quote": "\n> " + assertion + "\n",
        "link_label": "\n[" + assertion + "](https://example.invalid/contract)\n",
    }[style]
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(text + rendered)
    assert error.value.boundary == "normative_untagged:replay_original_fact_timestamp"


V8_STRONG_NEUTRAL_CONTROLS = (
    'The replay glossary may quote the phrase "create a new acceptance fact".',
    'The replay diagram may display a node labelled "create a second receipt".',
    'This receipt documentation can show the example text "refresh a timestamp".',
    'Timestamp terminology might include the words "prove noncommit".',
    'The replay example may discuss why software must not create an acceptance fact.',
    'The replay example may quote the phrase "create a new acceptance fact".',
    'The replay documentation may quote the phrase "create a new acceptance fact".',
)


@pytest.mark.parametrize("neutral", V8_STRONG_NEUTRAL_CONTROLS)
def test_v8_strong_neutral_subjects_remain_explanatory(neutral):
    assert _sentence_subjects(neutral) == []
    assert _authority_topics(neutral) == []
    text, _ = _document()
    _scan_normative_prose(text + "\n\n" + neutral + "\n")


@pytest.mark.parametrize("phrase,control", [
    ("replay glossary", V8_STRONG_NEUTRAL_CONTROLS[0]),
    ("replay diagram", V8_STRONG_NEUTRAL_CONTROLS[1]),
    ("replay example", V8_STRONG_NEUTRAL_CONTROLS[5]),
    ("replay documentation", V8_STRONG_NEUTRAL_CONTROLS[6]),
])
def test_v8_each_neutral_exclusion_has_a_protected_action_control(
        phrase, control, monkeypatch):
    assert phrase in NEUTRAL_SUBJECT_PHRASES
    assert _authority_topics(control) == []
    monkeypatch.setattr(__import__(__name__), "NEUTRAL_SUBJECT_PHRASES",
                        tuple(item for item in NEUTRAL_SUBJECT_PHRASES if item != phrase))
    assert _authority_topics(control)
    text, _ = _document()
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(text + "\n\n" + control + "\n")
    assert error.value.boundary.startswith("normative_untagged:")


@pytest.mark.parametrize("raw,kind,depth,visible,blank,list_item", [
    ("> Replay is authorized.", "quote", 1, "Replay is authorized.", False, False),
    ("  > > It may create a fact.", "quote", 2, "It may create a fact.", False, False),
    (">", "quote", 1, "", True, False),
    ("- > Replay is authorized.", "quote", 1, "Replay is authorized.", False, True),
    ("> - Replay is authorized.", "quote", 1, "Replay is authorized.", False, True),
    ("  > It may create a fact.", "quote", 1, "It may create a fact.", False, False),
    ("", "blank", 0, "", True, False),
    ("## Replay is authorized.", "heading", 0, "## Replay is authorized.", False, False),
])
def test_v9_quote_tokens_preserve_origin_before_marker_removal(
        raw, kind, depth, visible, blank, list_item):
    token = _visible_line(raw)
    assert token["original"] == raw
    assert token["kind"] == kind
    assert token["quote_depth"] == depth
    assert token["visible"] == visible
    assert token["blank"] is blank
    assert token["list_item"] is list_item


@pytest.mark.parametrize("source,expected", [
    ("> Replay may not create a new timestamp but\n"
     "> may create a new acceptance fact.",
     ["Replay may not create a new timestamp but may create a new acceptance fact."]),
    ("> Replay is authorized.\n>\n> It creates a new acceptance fact.",
     ["Replay is authorized.", "It creates a new acceptance fact."]),
    ("> Replay is authorized.\n\n> It creates a new acceptance fact.",
     ["Replay is authorized.", "It creates a new acceptance fact."]),
    ("> Replay is authorized.\n>> It creates a new acceptance fact.",
     ["Replay is authorized.", "It creates a new acceptance fact."]),
    ("> Replay is authorized.\nParagraph.\n> It creates a new acceptance fact.",
     ["Replay is authorized.", "Paragraph.", "It creates a new acceptance fact."]),
    ("- > Replay may not create a new timestamp but\n"
     "  > may create a new acceptance fact.",
     ["Replay may not create a new timestamp but may create a new acceptance fact."]),
    ("> - Replay may not create a new timestamp but\n"
     ">   may create a new acceptance fact.",
     ["Replay may not create a new timestamp but may create a new acceptance fact."]),
    ("- > Replay is authorized.\n- > It creates a new acceptance fact.",
     ["Replay is authorized.", "It creates a new acceptance fact."]),
    ("> - Replay is authorized.\n> - It creates a new acceptance fact.",
     ["Replay is authorized.", "It creates a new acceptance fact."]),
])
def test_v9_quote_block_sequences_are_fixed(source, expected):
    assert _visible_blocks(source) == expected


V9_MULTILINE_QUOTE_CHALLENGES = (
    ("> Replay may not create a new timestamp but\n"
     "> may create a new acceptance fact.", "replay_original_fact_timestamp"),
    ("> Replay may create a new acceptance fact but\n"
     "> may not create a new timestamp.", "replay_original_fact_timestamp"),
    ("> Replay may create a new\n"
     "> acceptance fact but may not create a new timestamp.",
     "replay_original_fact_timestamp"),
    ("> Replay may not create a new timestamp;\n"
     "> may create a new acceptance fact.", "replay_original_fact_timestamp"),
    ("> Replay may create a new acceptance fact;\n"
     "> may not create a new timestamp.", "replay_original_fact_timestamp"),
    ("> Replay may create a new\n"
     "> acceptance fact; may not create a new timestamp.",
     "replay_original_fact_timestamp"),
    ("> Replay is authorized.\n"
     "> It creates a new acceptance fact.", "replay_original_fact_timestamp"),
    ("> Replay is authorized and\n"
     "> creates a new acceptance fact.", "replay_original_fact_timestamp"),
    ("> Replay may not create a new timestamp.\n"
     "> It may not refresh a timestamp.\n"
     "> It may create a new acceptance fact.", "replay_original_fact_timestamp"),
    ("- > Replay may not create a new timestamp but\n"
     "  > may create a new acceptance fact.", "replay_original_fact_timestamp"),
    ("> - Replay may not create a new timestamp but\n"
     ">   may create a new acceptance fact.", "replay_original_fact_timestamp"),
) + tuple(
    ("> Replay may not create a new timestamp " + connector + "\n"
     "> may create a new acceptance fact.", "replay_original_fact_timestamp")
    for connector in ("however", "although", "yet", "while")
) + tuple(
    ("> Replay may create a new acceptance fact " + connector + "\n"
     "> may not create a new timestamp.", "replay_original_fact_timestamp")
    for connector in ("however", "although", "yet", "while")
) + tuple(
    ("> Replay may create a new\n"
     "> acceptance fact " + connector + " may not create a new timestamp.",
     "replay_original_fact_timestamp")
    for connector in ("however", "although", "yet", "while")
)


@pytest.mark.parametrize("rendered,topic", V9_MULTILINE_QUOTE_CHALLENGES)
def test_v9_multiline_quote_continuation_rejects_untagged_authority(rendered, topic):
    text, _ = _document()
    assert _authority_topics(_visible_blocks(rendered)[0]) == [topic]
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(text + "\n\n" + rendered + "\n")
    assert error.value.boundary == "normative_untagged:" + topic


@pytest.mark.parametrize("rendered", [
    "> Replay is authorized.\n>\n> It creates a new acceptance fact.",
    "> Replay is authorized.\n\n> It creates a new acceptance fact.",
    "> Replay is authorized.\n>> It creates a new acceptance fact.",
    "> Replay is authorized.\nParagraph.\n> It creates a new acceptance fact.",
    "- > Replay is authorized.\n- > It creates a new acceptance fact.",
    "> - Replay is authorized.\n> - It creates a new acceptance fact.",
])
def test_v9_quote_boundaries_do_not_carry_subject(rendered):
    text, _ = _document()
    _scan_normative_prose(text + "\n\n" + rendered + "\n")


V9_HOSTILE_NEUTRAL_OBJECTS = (
    ("Replay may not create a new timestamp but may create a new acceptance fact "
     "in the replay glossary.", "replay_original_fact_timestamp"),
    ("Replay may create a second receipt as shown in the replay diagram.",
     "single_result_receipt_replay_recovery"),
    ("Replay might refresh a timestamp in a replay example.",
     "replay_original_fact_timestamp"),
    ("Replay may prove noncommit according to timestamp terminology.",
     "total_absence_currentness"),
    ("Replay may create a new acceptance fact in receipt documentation.",
     "replay_original_fact_timestamp"),
    ("Replay may create a new acceptance fact in replay documentation.",
     "replay_original_fact_timestamp"),
)


@pytest.mark.parametrize("assertion,topic", V9_HOSTILE_NEUTRAL_OBJECTS)
def test_v9_neutral_object_never_clears_explicit_protected_subject(assertion, topic):
    assert _neutral_subject_present(assertion) is False
    assert _authority_topics(assertion) == [topic]
    text, _ = _document()
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(text + "\n\n" + assertion + "\n")
    assert error.value.boundary == "normative_untagged:" + topic


@pytest.mark.parametrize("object_phrase", [
    "replay glossary", "replay diagram", "replay example",
    "replay documentation", "receipt documentation", "timestamp terminology",
])
def test_v9_neutral_object_never_clears_inherited_protected_subject(object_phrase):
    assertion = ("Replay may not create a new timestamp but may create a new "
                 "acceptance fact in the " + object_phrase + ".")
    assert _neutral_subject_present(assertion.split(" but ")[1]) is False
    assert _authority_topics(assertion) == ["replay_original_fact_timestamp"]
    text, _ = _document()
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(text + "\n\n" + assertion + "\n")
    assert error.value.boundary == "normative_untagged:replay_original_fact_timestamp"


V9_STRONG_NEUTRAL_CONTROLS = (
    'The replay glossary may quote the phrase "create a new acceptance fact".',
    'The replay diagram may display a node labelled "create a second receipt".',
    'This receipt documentation can show the example text "refresh a timestamp".',
    'Timestamp terminology might include the words "prove noncommit".',
    'The replay example may discuss why software must not create an acceptance fact.',
    'Replay documentation may quote the sentence "Replay may create a new acceptance fact" as a rejected example.',
)


def test_v9_closed_neutral_subject_inventory_and_initial_position():
    assert NEUTRAL_SUBJECT_PHRASES == (
        "replay glossary", "replay diagram", "replay example",
        "replay documentation", "receipt documentation", "timestamp terminology",
    )
    assert _initial_subject_words(
        "The replay glossary may quote a fact in the replay diagram.") == [
            "replay", "glossary"]
    assert _neutral_subject_present(
        "The replay glossary may quote a fact in the replay diagram.") is True
    assert _neutral_subject_present(
        "Replay may quote a fact in the replay glossary.") is False
    assert _neutral_subject_present(
        "The replay glossary appendix may quote a fact.") is False


@pytest.mark.parametrize("assertion", V9_STRONG_NEUTRAL_CONTROLS)
def test_v9_exact_neutral_subjects_remain_explanatory(assertion):
    assert _neutral_subject_present(assertion) is True
    assert _sentence_subjects(assertion) == []
    assert _authority_topics(assertion) == []
    text, _ = _document()
    _scan_normative_prose(text + "\n\n" + assertion + "\n")


def test_v9_neutral_to_protected_transition_and_neutral_pronoun():
    hostile = ("The replay glossary may quote examples. "
               "Replay may create a new acceptance fact.")
    neutral = ("The replay glossary may quote examples. "
               "It may include the term timestamp.")
    neutral_quote = ("The replay glossary may quote examples. "
                     'It may quote the phrase "create a new acceptance fact".')
    assert _authority_topics(hostile) == ["replay_original_fact_timestamp"]
    assert _authority_topics(neutral) == []
    assert _authority_topics(neutral_quote) == []
    text, _ = _document()
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(text + "\n\n" + hostile + "\n")
    assert error.value.boundary == "normative_untagged:replay_original_fact_timestamp"
    _scan_normative_prose(text + "\n\n" + neutral + "\n")
    _scan_normative_prose(text + "\n\n" + neutral_quote + "\n")


@pytest.mark.parametrize("rendered,expected_block", [
    ("## Replay may create a new fact.", "## Replay may create a new fact."),
    ("- Replay may create a new fact.", "Replay may create a new fact."),
    ("| Replay may create a new fact. |", "| Replay may create a new fact. |"),
    ("> Replay may create a new fact.", "Replay may create a new fact."),
    ("[Replay may create a new fact.](https://example.invalid/label)",
     "[Replay may create a new fact.](https://example.invalid/label)"),
])
def test_v9_single_line_visible_markdown_regressions(rendered, expected_block):
    assert _visible_blocks(rendered) == [expected_block]
    text, _ = _document()
    with pytest.raises(ContractViolation) as error:
        _scan_normative_prose(text + "\n\n" + rendered + "\n")
    assert error.value.boundary == "normative_untagged:replay_original_fact_timestamp"
