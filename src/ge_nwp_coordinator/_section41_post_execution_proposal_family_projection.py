"""Private pure Section 41 post-execution proposal-family projection."""

import dataclasses
import typing

from . import _post_execution_evidence_values as _evidence_values
from ._post_execution_evidence_values import (
    PostExecutionSemanticReviewInputContextV1,
    _PostExecutionValue,
    _c1_contracts,
    _c1_values,
    _cognitive_rows,
    _cognitive_values,
    _exact_equal,
    _fail,
)

__all__ = ()

_Section41ProjectionValue = _PostExecutionValue


def _section41_projection_exact_equal(left: object, right: object) -> bool:
    return _exact_equal(left, right)

_SECTION41_POST_EXECUTION_PROJECTION_PROFILE_REF = 'section41-post-execution-proposal-family-projection.v2'
_SECTION41_POST_EXECUTION_PROJECTION_PROFILE_DIGEST = '76b0fdedd0fbbd3c6400be3f8e22eacdf585eb28280d12f38834d513b8cdb411'

Section41PostExecutionProjectionEvidenceEntryV2 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'Section41PostExecutionProjectionEvidenceEntryV2', 'ge_nwp_coordinator._section41_post_execution_proposal_family_projection',
        {'v_number': 'V23',
 'schema_id': 'governed-execution.nwp-section41-post-execution-projection-evidence-entry.v2',
 'ordered_fields': [{'constant': 'governed-execution.nwp-section41-post-execution-projection-evidence-entry.v2',
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
                    {'name': 'source_binding_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'source_binding_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'projection_evidence_entry_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': '76b0fdedd0fbbd3c6400be3f8e22eacdf585eb28280d12f38834d513b8cdb411',
                            'profile_ref': 'section41-post-execution-proposal-family-projection.v2'},
 'reference_posture': {'posture': 'parent_bound_or_no_standalone_ref'},
 'digest_posture': {'domain': 'governed-execution.nwp-section41-post-execution-projection-evidence-entry.v2.identity',
                    'field': 'projection_evidence_entry_digest',
                    'self_exclusion': ['projection_evidence_entry_digest']}},
        nested={},
        meta={},
    ),
)


Section41PostExecutionProposalFamilyProjectionV2 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'Section41PostExecutionProposalFamilyProjectionV2', 'ge_nwp_coordinator._section41_post_execution_proposal_family_projection',
        {'v_number': 'V22',
 'schema_id': 'governed-execution.nwp-section41-post-execution-proposal-family-projection.v2',
 'ordered_fields': [{'constant': 'governed-execution.nwp-section41-post-execution-proposal-family-projection.v2',
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
                    {'name': 'safe_projection_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
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
 'governing_profile_pair': {'profile_digest': '76b0fdedd0fbbd3c6400be3f8e22eacdf585eb28280d12f38834d513b8cdb411',
                            'profile_ref': 'section41-post-execution-proposal-family-projection.v2'},
 'reference_posture': {'domain': 'governed-execution.nwp-section41-post-execution-proposal-family-projection-reference.v2.identity',
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
 'digest_posture': {'domain': 'governed-execution.nwp-section41-post-execution-proposal-family-projection.v2.identity',
                    'field': 'projection_digest',
                    'self_exclusion': ['projection_digest']}},
        nested={'evidence_bindings': Section41PostExecutionProjectionEvidenceEntryV2},
        meta={},
    ),
)


def _row_tuple(value: object) -> tuple[object, ...]:
    columns = getattr(type(value), "_COLUMNS", None)
    if type(columns) is not tuple:
        _fail("source_owner_mismatch")
    return tuple(getattr(value, name) for name in typing.cast(tuple[str, ...], columns))


def _require_current_cognitive_row(value: object, expected: type[object]) -> object:
    if type(value) is not expected:
        _fail("source_owner_mismatch")
    # The current row owner already verified the row digest in __post_init__.
    if value.computed_digest() != getattr(value, expected._COLUMNS[-1]):
        _fail("source_owner_mismatch")
    return value


def _require_rank15_admission(
    *,
    owner_locators: object,
    owner_rows: tuple[object, ...],
    rank15_value: object,
    rank15_relation_row: object,
    rank15_admission_graph: object,
    rank15_membership_row: object,
    admitted_by_mutation_ref: object,
) -> str:
    if (
        type(owner_locators) is not tuple
        or len(owner_locators) != 12
        or any(type(item) is not _c1_values.RW0C1OwnerRowLocatorV1 for item in owner_locators)
        or type(rank15_value)
        is not _c1_values.RW0C1Section41PostExecutionProposalFamilyMemberV1
        or type(rank15_relation_row) is not _c1_contracts.RW0C1RowValue
        or type(rank15_membership_row) is not _c1_contracts.RW0C1RowValue
        or type(rank15_admission_graph) is not dict
        or type(admitted_by_mutation_ref) is not str
        or len(owner_rows) != 12
    ):
        _fail("source_owner_mismatch")
    try:
        owner_digest = _c1_contracts.section41_owner_family_graph_digest(
            typing.cast(tuple[_c1_values.RW0C1OwnerRowLocatorV1, ...], owner_locators)
        )
    except _c1_values.RW0C1PreflightError:
        _fail("source_owner_mismatch")
    if owner_digest != rank15_value.owner_family_graph_digest:
        _fail("source_owner_mismatch")

    relation = rank15_relation_row.to_mapping()
    membership = rank15_membership_row.to_mapping()
    graph = typing.cast(dict[str, object], rank15_admission_graph)
    if (
        rank15_relation_row.table_name != "rw0_relation_bindings"
        or rank15_membership_row.table_name != "rw0_evidence_memberships"
        or tuple(graph) != (
            "schema_id", "phase_basis_ref", "phase_basis_digest", "membership_ref",
            "kind_rank", "value_ref", "value_digest", "value_schema_id",
            "scope_binding_digest", "relation_set_digest", "relations",
            "admitted_by_mutation_ref", "admitted_at",
        )
        or graph["schema_id"]
        != "governed-execution.nwp-rw0-c1-evidence-admission-graph.v1"
        or graph["admitted_by_mutation_ref"] != admitted_by_mutation_ref
        or membership["admitted_by_mutation_ref"] != admitted_by_mutation_ref
        or graph["membership_ref"] != membership["membership_ref"]
        or graph["kind_rank"] != 15
        or membership["kind_rank"] != 15
        or relation["subject_kind_rank"] != 15
        or relation["subject_membership_ref"] != membership["membership_ref"]
        or relation["subject_membership_digest"] != membership["membership_digest"]
        or relation["subject_value_ref"] != rank15_value.value_ref
        or relation["subject_value_digest"] != rank15_value.value_digest
        or graph["value_ref"] != rank15_value.value_ref
        or graph["value_digest"] != rank15_value.value_digest
        or graph["value_schema_id"] != rank15_value.schema_id
        or membership["value_ref"] != rank15_value.value_ref
        or membership["value_digest"] != rank15_value.value_digest
        or membership["value_schema_id"] != rank15_value.schema_id
        or graph["scope_binding_digest"] != owner_digest
        or membership["scope_binding_digest"] != owner_digest
        or graph["relation_set_digest"] != membership["relation_set_digest"]
        or graph["phase_basis_ref"] != rank15_value.phase_basis_ref
        or graph["phase_basis_digest"] != rank15_value.phase_basis_digest
        or membership["phase_basis_ref"] != rank15_value.phase_basis_ref
        or membership["phase_basis_digest"] != rank15_value.phase_basis_digest
        or graph["admitted_at"] != membership["admitted_at"]
        or graph["relations"] != [
            {
                "relation_ref": relation["relation_ref"],
                "relation_digest": relation["relation_digest"],
                "relation_rank": relation["relation_rank"],
                "operand_set_digest": relation["operand_set_digest"],
                "evaluated_at": relation["evaluated_at"],
            }
        ]
    ):
        _fail("source_owner_mismatch")
    try:
        descriptor_fields = (
            ("schema_id", "source_invocation_ref", "source_invocation_digest"),
            ("schema_id", "artifact_ref", "artifact_binding_digest"),
            ("schema_id", "proposal_ref", "proposal_digest"),
            *(("schema_id", "proposal_ref", "evidence_binding_digest"),) * 9,
        )
        operands = tuple(
            _c1_contracts.RW0C1OperandIdentity(
                ordinal,
                locator.role,
                "existing_owner_row",
                None,
                None,
                None,
                locator.owner_role,
                typing.cast(str, getattr(row, fields[1])),
                locator.revision,
                locator.subrole,
                locator.ordinal,
                None,
                None,
                None,
                typing.cast(str, getattr(row, fields[0])),
                typing.cast(str, getattr(row, fields[1])),
                typing.cast(str, getattr(row, fields[2])),
                None,
            )
            for ordinal, (locator, row, fields) in enumerate(
                zip(owner_locators, owner_rows, descriptor_fields, strict=True)
            )
        )
        specification = _c1_contracts.relation_specifications(kind_rank=15)[0]
        expected_relation_ref = _c1_contracts.relation_reference(
            phase_basis_ref=rank15_value.phase_basis_ref,
            phase_basis_digest=rank15_value.phase_basis_digest,
            subject_type="evidence_membership",
            subject_membership_ref=membership["membership_ref"],
            relation_rank=0,
        )
        expected_relation_digest, expected_operand_digest = (
            _c1_contracts.relation_digest(
                phase_basis_ref=rank15_value.phase_basis_ref,
                phase_basis_digest=rank15_value.phase_basis_digest,
                relation_ref=expected_relation_ref,
                subject_type="evidence_membership",
                subject_membership_ref=membership["membership_ref"],
                subject_kind_rank=15,
                subject_value_ref=rank15_value.value_ref,
                subject_value_digest=rank15_value.value_digest,
                subject_value_schema_id=rank15_value.schema_id,
                specification=specification,
                evaluated_at=None,
                operands=operands,
            )
        )
        expected_relation_set_digest = _c1_contracts.relation_set_digest(
            phase_basis_ref=rank15_value.phase_basis_ref,
            subject_type="evidence_membership",
            subject_ref=membership["membership_ref"],
            relations=((0, expected_relation_ref, expected_relation_digest),),
        )
        graph_digest = _c1_contracts.admission_graph_digest(graph)
        membership_identity = {
            name: membership[name]
            for name in (
                "schema_id", "membership_ref", "phase_basis_ref", "phase_basis_digest",
                "kind_rank", "value_ref", "value_digest", "value_schema_id",
                "scope_binding_digest", "relation_set_digest", "admitted_by_mutation_ref",
                "admitted_at", "admission_graph_digest",
            )
        }
        membership_digest = _c1_contracts.membership_digest(membership_identity)
    except _c1_values.RW0C1PreflightError:
        _fail("source_owner_mismatch")
    if (
        relation["schema_id"]
        != "governed-execution.nwp-rw0-c1-relation-binding.v1"
        or relation["phase_basis_ref"] != rank15_value.phase_basis_ref
        or relation["phase_basis_digest"] != rank15_value.phase_basis_digest
        or relation["relation_ref"] != expected_relation_ref
        or relation["relation_digest"] != expected_relation_digest
        or relation["subject_type"] != "evidence_membership"
        or relation["subject_membership_ref"] != membership["membership_ref"]
        or relation["subject_membership_digest"] != membership["membership_digest"]
        or relation["subject_kind_rank"] != 15
        or relation["subject_value_ref"] != rank15_value.value_ref
        or relation["subject_value_digest"] != rank15_value.value_digest
        or relation["subject_value_schema_id"] != rank15_value.schema_id
        or relation["relation_rank"] != specification.relation_rank
        or relation["relation_schema_id"] != specification.relation_schema_id
        or relation["relation_version"] != 1
        or relation["proof_mode"] != specification.proof_mode
        or relation["profile_ref"] != specification.profile_ref
        or relation["profile_digest"] != specification.profile_digest
        or relation["evaluated_at"] is not None
        or relation["operand_count"] != 12
        or relation["operand_set_digest"] != expected_operand_digest
        or graph["relation_set_digest"] != expected_relation_set_digest
        or membership["relation_set_digest"] != expected_relation_set_digest
        or membership["admission_graph_digest"] != graph_digest
        or membership["membership_digest"] != membership_digest
    ):
        _fail("source_owner_mismatch")
    return owner_digest


def _require_exact_owner_family_coherence(
    *,
    context: PostExecutionSemanticReviewInputContextV1,
    source: _cognitive_rows.DevelopmentModelSourceInvocationRowValue,
    artifact: _cognitive_rows.DevelopmentPrivateProposalArtifactBindingRowValue,
    proposal: _cognitive_rows.DevelopmentModelProposalRowValue,
    rows: tuple[_cognitive_rows.DevelopmentModelProposalEvidenceBindingRowValue, ...],
    owner_locators: tuple[_c1_values.RW0C1OwnerRowLocatorV1, ...],
    rank15: _c1_values.RW0C1Section41PostExecutionProposalFamilyMemberV1,
) -> None:
    """Require the same exact family relation accepted by the C1 matcher."""

    expected_locator_coordinates = (
        (
            "source_invocation", "development_model_source_invocation",
            source.source_invocation_ref, source.source_invocation_digest,
            None, None, None,
        ),
        (
            "artifact_binding", "development_private_proposal_artifact_binding",
            artifact.artifact_ref, artifact.artifact_binding_digest,
            None, None, None,
        ),
        (
            "model_proposal", "development_model_proposal",
            proposal.proposal_ref, proposal.proposal_digest,
            None, None, None,
        ),
        *tuple(
            (
                row.evidence_role,
                "development_model_proposal_evidence_binding",
                row.proposal_ref,
                row.evidence_binding_digest,
                None,
                row.evidence_role,
                0,
            )
            for row in rows
        ),
    )
    observed_locator_coordinates = tuple(
        (
            locator.role, locator.owner_role, locator.row_ref, locator.row_digest,
            locator.revision, locator.subrole, locator.ordinal,
        )
        for locator in owner_locators
    )
    if observed_locator_coordinates != expected_locator_coordinates:
        _fail("relation_mismatch")

    post_context_schema = (
        "governed-execution.nwp-post-execution-semantic-review-context.v1"
    )
    post_artifact_schema = (
        "governed-execution.nwp-post-execution-semantic-review-artifact.v1"
    )
    post_projection_schema = (
        "governed-execution.nwp-post-execution-semantic-review-safe-projection.v1"
    )
    exact_pairs = (
        (context.schema_id, post_context_schema),
        (rank15.context_schema_id, post_context_schema),
        (rank15.safe_projection_schema_id, post_projection_schema),
        (source.proposal_phase, "post_execution_semantic_review"),
        (artifact.proposal_phase, "post_execution_semantic_review"),
        (proposal.proposal_phase, "post_execution_semantic_review"),
        (source.source_invocation_ref, rank15.source_invocation_ref),
        (source.source_invocation_digest, rank15.source_invocation_digest),
        (source.model_contract_ref, rank15.model_contract_ref),
        (source.model_contract_digest, rank15.model_contract_digest),
        (source.model_configuration_ref, rank15.model_configuration_ref),
        (source.model_configuration_digest, rank15.model_configuration_digest),
        (source.context_schema_id, rank15.context_schema_id),
        (source.context_ref, rank15.context_ref),
        (source.context_digest, rank15.context_digest),
        (source.artifact_schema_id, post_artifact_schema),
        (source.artifact_ref, rank15.artifact_ref),
        (source.artifact_digest, rank15.artifact_digest),
        (artifact.artifact_schema_id, post_artifact_schema),
        (artifact.artifact_ref, rank15.artifact_ref),
        (artifact.artifact_digest, rank15.artifact_digest),
        (artifact.artifact_binding_digest, rank15.artifact_binding_digest),
        (artifact.safe_projection_schema_id, rank15.safe_projection_schema_id),
        (artifact.safe_projection_digest, rank15.safe_projection_digest),
        (proposal.proposal_ref, rank15.proposal_ref),
        (proposal.proposal_digest, rank15.proposal_digest),
        (proposal.source_invocation_ref, rank15.source_invocation_ref),
        (proposal.source_invocation_digest, rank15.source_invocation_digest),
        (proposal.model_contract_ref, rank15.model_contract_ref),
        (proposal.model_contract_digest, rank15.model_contract_digest),
        (proposal.model_configuration_ref, rank15.model_configuration_ref),
        (proposal.model_configuration_digest, rank15.model_configuration_digest),
        (proposal.context_schema_id, rank15.context_schema_id),
        (proposal.context_ref, rank15.context_ref),
        (proposal.context_digest, rank15.context_digest),
        (proposal.artifact_schema_id, post_artifact_schema),
        (proposal.artifact_ref, rank15.artifact_ref),
        (proposal.artifact_digest, rank15.artifact_digest),
        (proposal.safe_projection_schema_id, rank15.safe_projection_schema_id),
        (proposal.safe_projection_digest, rank15.safe_projection_digest),
        (proposal.evidence_set_ref, rank15.evidence_set_ref),
        (proposal.evidence_set_digest, rank15.evidence_set_digest),
        (proposal.recommendation, rank15.recommendation),
        (proposal.reason_code, rank15.reason_code),
        (proposal.proposal_created_at, rank15.proposal_created_at),
        (context.input_context_ref, rank15.context_ref),
        (context.input_context_digest, rank15.context_digest),
        (rank15.evidence_binding_count, 9),
    )
    if any(not _exact_equal(left, right) for left, right in exact_pairs):
        _fail("relation_mismatch")

    expected_evidence = tuple(
        (role, rank, 0, 1)
        for rank, role in enumerate(_evidence_values._ROLE_NAMES, 5)
    )
    observed_evidence = tuple(
        (row.evidence_role, row.role_rank, row.ordinal, row.required_for_selection)
        for row in rows
    )
    if observed_evidence != expected_evidence or any(
        row.proposal_ref != rank15.proposal_ref
        or row.proposal_phase != "post_execution_semantic_review"
        or row.evidence_set_ref != rank15.evidence_set_ref
        for row in rows
    ) or len({row.evidence_bound_at for row in rows}) != 1:
        _fail("relation_mismatch")

    evidence_identity = {
        "evidence_set_ref": rank15.evidence_set_ref,
        "proposal_ref": rank15.proposal_ref,
        "proposal_phase": "post_execution_semantic_review",
        "entries": tuple(
            {
                "evidence_role": row.evidence_role,
                "role_rank": row.role_rank,
                "ordinal": row.ordinal,
                "evidence_ref": row.evidence_ref,
                "evidence_digest": row.evidence_digest,
                "evidence_binding_digest": row.evidence_binding_digest,
            }
            for row in rows
        ),
    }
    if _evidence_values._domain_separated_digest(
        "governed-execution.nwp-model-proposal-evidence-set.v1.identity",
        evidence_identity,
    ) != rank15.evidence_set_digest:
        _fail("relation_mismatch")


def section41_post_execution_proposal_family_projection(
    value: object,
    *,
    input_context: object,
    source_invocation_row: object,
    artifact_binding_row: object,
    proposal_row: object,
    evidence_rows: object,
    private_reader_tuples: object,
    owner_locators: object,
    rank15_value: object,
    rank15_relation_row: object,
    rank15_admission_graph: object,
    rank15_membership_row: object,
    admitted_by_mutation_ref: object,
) -> Section41PostExecutionProposalFamilyProjectionV2:
    """Verify an expected projection from the complete current-owner family.

    The function consumes already reconstructed current row/value owners and
    exact reader tuples.  It performs no read and treats ``value`` only as the
    expected output assertion.
    """

    context = PostExecutionSemanticReviewInputContextV1.from_supplied(input_context)
    source = typing.cast(
        _cognitive_rows.DevelopmentModelSourceInvocationRowValue,
        _require_current_cognitive_row(
            source_invocation_row,
            _cognitive_rows.DevelopmentModelSourceInvocationRowValue,
        ),
    )
    artifact = typing.cast(
        _cognitive_rows.DevelopmentPrivateProposalArtifactBindingRowValue,
        _require_current_cognitive_row(
            artifact_binding_row,
            _cognitive_rows.DevelopmentPrivateProposalArtifactBindingRowValue,
        ),
    )
    proposal = typing.cast(
        _cognitive_rows.DevelopmentModelProposalRowValue,
        _require_current_cognitive_row(
            proposal_row,
            _cognitive_rows.DevelopmentModelProposalRowValue,
        ),
    )
    if (
        type(evidence_rows) is not tuple
        or len(evidence_rows) != 9
        or type(private_reader_tuples) is not tuple
        or len(private_reader_tuples) != 12
    ):
        _fail("source_owner_mismatch")
    rows = typing.cast(
        tuple[_cognitive_rows.DevelopmentModelProposalEvidenceBindingRowValue, ...],
        evidence_rows,
    )
    if any(
        type(row) is not _cognitive_rows.DevelopmentModelProposalEvidenceBindingRowValue
        or row.computed_digest() != row.evidence_binding_digest
        for row in rows
    ):
        _fail("source_owner_mismatch")
    owner_rows: tuple[object, ...] = (source, artifact, proposal, *rows)
    if any(type(item) is not tuple for item in private_reader_tuples) or tuple(
        typing.cast(tuple[object, ...], item) for item in private_reader_tuples
    ) != tuple(_row_tuple(row) for row in owner_rows):
        _fail("source_owner_mismatch")

    owner_digest = _require_rank15_admission(
        owner_locators=owner_locators,
        owner_rows=owner_rows,
        rank15_value=rank15_value,
        rank15_relation_row=rank15_relation_row,
        rank15_admission_graph=rank15_admission_graph,
        rank15_membership_row=rank15_membership_row,
        admitted_by_mutation_ref=admitted_by_mutation_ref,
    )
    rank15 = typing.cast(
        _c1_values.RW0C1Section41PostExecutionProposalFamilyMemberV1,
        rank15_value,
    )
    _require_exact_owner_family_coherence(
        context=context,
        source=source,
        artifact=artifact,
        proposal=proposal,
        rows=rows,
        owner_locators=typing.cast(
            tuple[_c1_values.RW0C1OwnerRowLocatorV1, ...], owner_locators
        ),
        rank15=rank15,
    )
    candidate = typing.cast(
        Section41PostExecutionProposalFamilyProjectionV2,
        Section41PostExecutionProposalFamilyProjectionV2.from_supplied(value),
    )

    if tuple(
        (row.evidence_role, row.role_rank, row.ordinal) for row in rows
    ) != tuple(
        (entry.role, entry.role_rank, entry.ordinal) for entry in context.role_entries
    ) or any(
        row.evidence_ref != entry.typed_value_ref
        or row.evidence_digest != entry.typed_value_digest
        for row, entry in zip(rows, context.role_entries, strict=True)
    ):
        _fail("source_owner_mismatch")
    evidence_entries = tuple(
        {
            "evidence_role": row.evidence_role,
            "role_rank": row.role_rank,
            "ordinal": row.ordinal,
            "evidence_ref": row.evidence_ref,
            "evidence_digest": row.evidence_digest,
            "evidence_binding_digest": row.evidence_binding_digest,
        }
        for row in rows
    )
    evidence_identity = {
        "evidence_set_ref": proposal.evidence_set_ref,
        "proposal_ref": proposal.proposal_ref,
        "proposal_phase": proposal.proposal_phase,
        "entries": evidence_entries,
    }
    if (
        any(
            row.proposal_ref != proposal.proposal_ref
            or row.proposal_phase != proposal.proposal_phase
            or row.evidence_set_ref != proposal.evidence_set_ref
            for row in rows
        )
        or _evidence_values._domain_separated_digest(
            "governed-execution.nwp-model-proposal-evidence-set.v1.identity",
            evidence_identity,
        )
        != proposal.evidence_set_digest
    ):
        _fail("source_owner_mismatch")

    expected_entries = tuple(
        {
            "proposal_ref": row.proposal_ref,
            "proposal_phase": row.proposal_phase,
            "evidence_set_ref": row.evidence_set_ref,
            "evidence_role": row.evidence_role,
            "role_rank": row.role_rank,
            "ordinal": row.ordinal,
            "evidence_ref": row.evidence_ref,
            "evidence_digest": row.evidence_digest,
            "required_for_selection": row.required_for_selection,
            "evidence_bound_at": row.evidence_bound_at,
            "source_binding_schema_id": row.schema_id,
            "source_binding_digest": row.evidence_binding_digest,
        }
        for index, row in enumerate(rows)
    )
    for expected, observed in zip(expected_entries, candidate.evidence_bindings, strict=True):
        observed_mapping = observed.to_mapping()
        if any(not _exact_equal(observed_mapping[name], member) for name, member in expected.items()):
            _fail("source_owner_mismatch")

    expected = {
        "proposal_phase": source.proposal_phase,
        "source_invocation_ref": source.source_invocation_ref,
        "source_invocation_digest": source.source_invocation_digest,
        "artifact_ref": artifact.artifact_ref,
        "artifact_digest": artifact.artifact_digest,
        "artifact_binding_digest": artifact.artifact_binding_digest,
        "proposal_ref": proposal.proposal_ref,
        "proposal_digest": proposal.proposal_digest,
        "model_contract_ref": source.model_contract_ref,
        "model_contract_digest": source.model_contract_digest,
        "model_configuration_ref": source.model_configuration_ref,
        "model_configuration_digest": source.model_configuration_digest,
        "input_context_schema_id": context.schema_id,
        "input_context_ref": context.input_context_ref,
        "input_context_digest": context.input_context_digest,
        "lineage_context_schema_id": context.lineage_context_schema_id,
        "lineage_context_ref": context.lineage_context_ref,
        "lineage_context_digest": context.lineage_context_digest,
        "safe_projection_schema_id": artifact.safe_projection_schema_id,
        "safe_projection_digest": artifact.safe_projection_digest,
        "evidence_set_ref": proposal.evidence_set_ref,
        "evidence_set_digest": proposal.evidence_set_digest,
        "evidence_binding_count": 9,
        "owner_family_graph_digest": owner_digest,
        "recommendation": proposal.recommendation,
        "reason_code": proposal.reason_code,
        "source_invocation_started_at": source.source_invocation_started_at,
        "source_invocation_completed_at": source.source_invocation_completed_at,
        "artifact_validated_at": artifact.artifact_validated_at,
        "evidence_bound_at": rows[0].evidence_bound_at,
        "proposal_created_at": proposal.proposal_created_at,
        "projection_evaluated_at": proposal.proposal_created_at,
    }
    if any(not _exact_equal(getattr(candidate, name), member) for name, member in expected.items()):
        _fail("source_owner_mismatch")
    rank15_expected = {
        "source_invocation_ref": candidate.source_invocation_ref,
        "source_invocation_digest": candidate.source_invocation_digest,
        "artifact_ref": candidate.artifact_ref,
        "artifact_digest": candidate.artifact_digest,
        "artifact_binding_digest": candidate.artifact_binding_digest,
        "proposal_ref": candidate.proposal_ref,
        "proposal_digest": candidate.proposal_digest,
        "model_contract_ref": candidate.model_contract_ref,
        "model_contract_digest": candidate.model_contract_digest,
        "model_configuration_ref": candidate.model_configuration_ref,
        "model_configuration_digest": candidate.model_configuration_digest,
        "context_schema_id": candidate.input_context_schema_id,
        "context_ref": candidate.input_context_ref,
        "context_digest": candidate.input_context_digest,
        "safe_projection_schema_id": candidate.safe_projection_schema_id,
        "safe_projection_digest": candidate.safe_projection_digest,
        "evidence_set_ref": candidate.evidence_set_ref,
        "evidence_set_digest": candidate.evidence_set_digest,
        "evidence_binding_count": candidate.evidence_binding_count,
        "recommendation": candidate.recommendation,
        "reason_code": candidate.reason_code,
        "proposal_created_at": candidate.proposal_created_at,
        "owner_family_graph_digest": candidate.owner_family_graph_digest,
    }
    if any(not _exact_equal(getattr(rank15, name), member) for name, member in rank15_expected.items()):
        _fail("source_owner_mismatch")
    if not (
        context.constructed_at <= source.source_invocation_started_at
        <= source.source_invocation_completed_at <= artifact.artifact_validated_at
        <= rows[0].evidence_bound_at <= proposal.proposal_created_at
    ):
        _fail("relation_mismatch")
    return candidate
