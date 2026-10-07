"""Private pure exact Section 41 nine-role resolution."""

import dataclasses
import typing

from ._section41_post_execution_proposal_family_projection import (
    Section41PostExecutionProposalFamilyProjectionV2,
    _Section41ProjectionValue,
    _c1_contracts,
    _c1_values,
    _cognitive_values,
    _evidence_values,
    _fail,
)

__all__ = ()

_DECISION_CURRENTNESS_PROFILE_PAIR = (
    "rw0-c-proposal-evidence-currentness.v1",
    "88b347a069c92a5804ba53dad4f39a9d7ba6a36413fa38812f81e964a8902e9b",
)


def _validate_exact_nine_role_resolution_set(
    values: object,
) -> tuple["Section41PostExecutionRoleResolutionV3", ...]:
    if type(values) is not tuple or len(values) != 9:
        _fail("invalid_cardinality")
    result = typing.cast(tuple[Section41PostExecutionRoleResolutionV3, ...], values)
    if any(type(value) is not Section41PostExecutionRoleResolutionV3 for value in result):
        _fail("invalid_nested_value")
    roles = (
        "candidate_capsule", "worker_result", "validation_result",
        "independent_review", "standing_policy", "risk_lane",
        "authority_currentness_attestation", "global_stop", "effect_ceiling",
    )
    if tuple(
        (value.context_role, value.context_role_rank, value.context_role_ordinal)
        for value in result
    ) != tuple((role, rank, 0) for rank, role in enumerate(roles, 5)):
        _fail("source_owner_mismatch")
    common = (
        "profile_ref", "profile_digest", "input_context_schema_id",
        "input_context_ref", "input_context_digest", "lineage_context_schema_id",
        "lineage_context_ref", "lineage_context_digest", "projection_schema_id",
        "projection_ref", "projection_digest", "source_invocation_ref",
        "source_invocation_digest", "proposal_ref", "proposal_digest",
        "evidence_set_ref", "evidence_set_digest", "section41_membership_ref",
        "section41_membership_digest", "section41_value_ref",
        "section41_value_digest", "context_role_entry_schema_id",
        "decision_currentness_profile_ref", "decision_currentness_profile_digest",
        "resolution_posture", "result", "reason",
    )
    first = result[0]
    if any(
        any(getattr(value, field) != getattr(first, field) for field in common)
        for value in result[1:]
    ):
        _fail("relation_mismatch")
    if len({value.relation_ref for value in result}) != 9:
        _fail("duplicate_entry")
    if (
        first.decision_currentness_profile_ref,
        first.decision_currentness_profile_digest,
    ) != _DECISION_CURRENTNESS_PROFILE_PAIR:
        _fail("invalid_profile_pair")
    return result

_SECTION41_POST_EXECUTION_ROLE_RESOLUTION_PROFILE_REF = 'section41-post-execution-role-resolution.v3'
_SECTION41_POST_EXECUTION_ROLE_RESOLUTION_PROFILE_DIGEST = '008a8468c608d9db41fe28f19bc582cc9598f58c9b3009e2d79322fd6c22cebc'

Section41PostExecutionRoleResolutionV3 = typing.cast(
    type[_Section41ProjectionValue],
    _Section41ProjectionValue._define(
        'Section41PostExecutionRoleResolutionV3', 'ge_nwp_coordinator._section41_post_execution_role_resolution',
        {'v_number': 'V24',
 'schema_id': 'governed-execution.nwp-section41-post-execution-role-resolution.v3',
 'ordered_fields': [{'constant': 'governed-execution.nwp-section41-post-execution-role-resolution.v3',
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
                    {'name': 'input_context_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'input_context_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'input_context_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'projection_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
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
                    {'name': 'context_role_entry_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
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
                    {'name': 'evidence_locator_role',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
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
 'governing_profile_pair': {'profile_digest': '008a8468c608d9db41fe28f19bc582cc9598f58c9b3009e2d79322fd6c22cebc',
                            'profile_ref': 'section41-post-execution-role-resolution.v3'},
 'reference_posture': {'domain': 'governed-execution.nwp-section41-post-execution-role-resolution-reference.v3.identity',
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
 'digest_posture': {'domain': 'governed-execution.nwp-section41-post-execution-role-resolution.v3.identity',
                    'field': 'relation_digest',
                    'self_exclusion': ['relation_digest']}},
        nested={},
        meta={},
    ),
)


def section41_post_execution_role_resolution(
    value: object,
    *,
    requested_role: str,
    family: object,
    projection: object,
    input_context: object,
    evidence_supply: object,
    evidence_role_values: tuple[object, ...],
    evidence_support_values: tuple[tuple[object, ...], ...],
    evidence_rows: object,
    section41_value: object,
    section41_membership_row: object,
) -> Section41PostExecutionRoleResolutionV3:
    """Resolve exactly one requested role from a complete grounded family."""

    complete = _validate_exact_nine_role_resolution_set(family)
    projected = Section41PostExecutionProposalFamilyProjectionV2.from_supplied(projection)
    # These are reachable through the accepted projection -> evidence edge;
    # resolution itself retains its single semantic import edge.
    if (
        type(input_context) is not _evidence_values.PostExecutionSemanticReviewInputContextV1
        or type(evidence_supply) is not _evidence_values.PostExecutionEvidenceSupplyV2
        or type(evidence_rows) is not tuple
        or len(evidence_rows) != 9
        or any(
            type(row)
            is not _evidence_values._cognitive_rows.DevelopmentModelProposalEvidenceBindingRowValue
            for row in evidence_rows
        )
        or type(section41_value)
        is not _c1_values.RW0C1Section41PostExecutionProposalFamilyMemberV1
        or type(section41_membership_row) is not _c1_contracts.RW0C1RowValue
        or section41_membership_row.table_name != "rw0_evidence_memberships"
    ):
        _fail("source_owner_mismatch")
    evidence_supply = _evidence_values.validate_post_execution_evidence_supply(
        evidence_supply,
        role_values=evidence_role_values,
        support_values=evidence_support_values,
    )
    if type(requested_role) is not str:
        _fail("invalid_field_type")
    matches = tuple(item for item in complete if item.context_role == requested_role)
    if len(matches) != 1:
        _fail("source_owner_mismatch")
    selected = matches[0]
    candidate = typing.cast(
        Section41PostExecutionRoleResolutionV3,
        Section41PostExecutionRoleResolutionV3.from_supplied(value),
    )
    if candidate != selected:
        _fail("relation_mismatch")

    role_entries = getattr(input_context, "role_entries", None)
    role_supplies = getattr(evidence_supply, "role_supplies", None)
    if type(role_entries) is not tuple or len(role_entries) != 9:
        _fail("invalid_cardinality")
    if type(role_supplies) is not tuple or len(role_supplies) != 9:
        _fail("invalid_cardinality")
    if getattr(evidence_supply, "input_context", None) != input_context:
        _fail("source_owner_mismatch")
    current_evidence_rows = typing.cast(tuple[object, ...], evidence_rows)
    membership = section41_membership_row.to_mapping()
    if (
        membership["kind_rank"] != 15
        or membership["value_ref"] != section41_value.value_ref
        or membership["value_digest"] != section41_value.value_digest
        or membership["membership_ref"] != selected.section41_membership_ref
        or membership["membership_digest"] != selected.section41_membership_digest
    ):
        _fail("source_owner_mismatch")

    for index, relation in enumerate(complete):
        role_entry = role_entries[index]
        role_supply = role_supplies[index]
        evidence_entry = projected.evidence_bindings[index]
        current_evidence_entry = current_evidence_rows[index]
        if (
            current_evidence_entry.evidence_role != evidence_entry.evidence_role
            or current_evidence_entry.role_rank != evidence_entry.role_rank
            or current_evidence_entry.ordinal != evidence_entry.ordinal
            or current_evidence_entry.evidence_ref != evidence_entry.evidence_ref
            or current_evidence_entry.evidence_digest != evidence_entry.evidence_digest
            or current_evidence_entry.proposal_ref != projected.proposal_ref
            or current_evidence_entry.proposal_phase != projected.proposal_phase
            or current_evidence_entry.evidence_set_ref != projected.evidence_set_ref
            or current_evidence_entry.computed_digest()
            != current_evidence_entry.evidence_binding_digest
        ):
            _fail("source_owner_mismatch")
        expected = {
            "input_context_schema_id": input_context.schema_id,
            "input_context_ref": input_context.input_context_ref,
            "input_context_digest": input_context.input_context_digest,
            "lineage_context_schema_id": input_context.lineage_context_schema_id,
            "lineage_context_ref": input_context.lineage_context_ref,
            "lineage_context_digest": input_context.lineage_context_digest,
            "projection_schema_id": projected.schema_id,
            "projection_ref": projected.projection_ref,
            "projection_digest": projected.projection_digest,
            "source_invocation_ref": projected.source_invocation_ref,
            "source_invocation_digest": projected.source_invocation_digest,
            "proposal_ref": projected.proposal_ref,
            "proposal_digest": projected.proposal_digest,
            "evidence_set_ref": projected.evidence_set_ref,
            "evidence_set_digest": projected.evidence_set_digest,
            "section41_membership_ref": membership["membership_ref"],
            "section41_membership_digest": membership["membership_digest"],
            "section41_value_ref": section41_value.value_ref,
            "section41_value_digest": section41_value.value_digest,
            "context_role_entry_schema_id": role_entry.schema_id,
            "context_role": role_entry.role,
            "context_role_rank": role_entry.role_rank,
            "context_role_ordinal": role_entry.ordinal,
            "evidence_locator_proposal_ref": evidence_entry.proposal_ref,
            "evidence_locator_role": evidence_entry.evidence_role,
            "evidence_locator_ordinal": evidence_entry.ordinal,
            "evidence_binding_digest": current_evidence_entry.evidence_binding_digest,
            "evidence_bound_at": evidence_entry.evidence_bound_at,
            "typed_schema_id": role_supply.typed_schema_id,
            "typed_value_ref": role_supply.typed_value_ref,
            "typed_value_digest": role_supply.typed_value_digest,
            "source_posture": role_entry.source_posture,
            "direct_c1_kind": role_entry.direct_c1_kind,
            "direct_c1_kind_rank": role_entry.direct_c1_kind_rank,
            "direct_c1_membership_ref": role_entry.direct_c1_membership_ref,
            "direct_c1_membership_digest": role_entry.direct_c1_membership_digest,
            "source_profile_ref": role_entry.source_profile_ref,
            "source_profile_digest": role_entry.source_profile_digest,
            "source_binding_schema_id": role_entry.source_binding_schema_id,
            "source_binding_ref": role_entry.source_binding_ref,
            "source_binding_digest": role_entry.source_binding_digest,
            "model_input_posture": role_entry.model_input_posture,
            "decision_currentness_profile_ref": _DECISION_CURRENTNESS_PROFILE_PAIR[0],
            "decision_currentness_profile_digest": _DECISION_CURRENTNESS_PROFILE_PAIR[1],
        }
        if any(getattr(relation, name) != member for name, member in expected.items()):
            _fail("source_owner_mismatch")
        if any(
            getattr(role_supply, name) != getattr(role_entry, name)
            for name in (
                "role", "role_rank", "ordinal", "typed_schema_id", "typed_value_ref",
                "typed_value_digest", "source_profile_ref", "source_profile_digest",
                "source_binding_schema_id", "source_binding_ref", "source_binding_digest",
                "model_input_posture",
            )
        ):
            _fail("source_owner_mismatch")
    return candidate
