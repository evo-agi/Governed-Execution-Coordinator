"""Private pure RW0-C decision-input values and evaluators.

These values describe supplied decision inputs only.  They do not create a
durable decision, progress C2B, implement a terminal, or contact execution.
"""

import dataclasses
import typing

from ._post_execution_evidence_values import (
    IndependentReviewDispositionV1,
    PostExecutionGlobalStopSnapshotV1,
    PostExecutionReviewResultSetV1,
    PostExecutionSemanticReviewInputContextV1,
    PostExecutionSourceEffectCeilingEvidenceV1,
    PostExecutionValidationResultSetV1,
    Section41PostExecutionSemanticReviewLineageContextV1,
    ValidationDispositionV1,
    _PostExecutionValue,
    _exact_equal,
    _fail,
)
from ._post_execution_policy_values import (
    DecisionBranchEvaluationEntryV1,
    PostExecutionRiskLaneBranchMatrixV1,
    PostExecutionRiskSourceBindingV1,
    PostExecutionRiskSourceProfileV1,
    PostExecutionStandingPolicyBranchMatrixV1,
    PostExecutionStandingPolicySourceAttestationV1,
)
from ._section41_post_execution_proposal_family_projection import (
    Section41PostExecutionProposalFamilyProjectionV2,
)
from ._section41_post_execution_role_resolution import (
    Section41PostExecutionRoleResolutionV3,
)

__all__ = ()


@dataclasses.dataclass(frozen=True, slots=True, repr=False)
class _MembershipPage:
    """One callback-free transcript page from the frozen LIMIT-257 reader."""

    capability_epoch: object
    cursor: object
    rows: object
    next_cursor: object

    def __repr__(self) -> str:
        return "_MembershipPage()"


_DECISION_BRANCHES = (
    ("candidate_acceptance", "governed", "author_candidate"),
    ("candidate_repair", "governed", "author_candidate"),
    ("attempt_selecting_replan", "governed", "author_candidate"),
    ("program_terminal_reject", "halt_only", None),
    ("post_execution_program_block", "halt_only", None),
)


def _require_cursor(value: object) -> tuple[int, str]:
    if (
        type(value) is not tuple
        or len(value) != 2
        or type(value[0]) is not int
        or type(value[1]) is not str
        or value[0] < 0
        or not value[1]
    ):
        _fail("invalid_field_type")
    return typing.cast(tuple[int, str], value)


def _validate_bounded_membership_closure(
    value: object,
    *,
    pages: object,
) -> "RW0CDecisionMembershipClosureV1":
    """Replay the exact finite page transcript and compare its complete closure."""

    result = typing.cast(
        RW0CDecisionMembershipClosureV1,
        RW0CDecisionMembershipClosureV1.from_supplied(value),
    )
    if type(pages) is not tuple or not pages:
        _fail("invalid_cardinality")
    transcript = typing.cast(tuple[_MembershipPage, ...], pages)
    if any(type(page) is not _MembershipPage for page in transcript):
        _fail("invalid_nested_value")
    first_epoch = transcript[0].capability_epoch
    if type(first_epoch) is not str or not first_epoch:
        _fail("invalid_field_type")
    expected_cursor = (0, "0")
    expected_continuation: tuple[int, str] | None = None
    accepted: list[RW0CDecisionMembershipClosureEntryV1] = []
    for page_index, page in enumerate(transcript):
        if page.capability_epoch != first_epoch:
            _fail("relation_mismatch")
        cursor = _require_cursor(page.cursor)
        if cursor != expected_cursor:
            _fail("relation_mismatch")
        if type(page.rows) is not tuple or len(page.rows) > 257:
            _fail("invalid_cardinality")
        rows = typing.cast(tuple[RW0CDecisionMembershipClosureEntryV1, ...], page.rows)
        if any(type(row) is not RW0CDecisionMembershipClosureEntryV1 for row in rows):
            _fail("invalid_nested_value")
        keys = tuple((row.kind_rank, row.membership_ref) for row in rows)
        if keys != tuple(sorted(keys)):
            _fail("relation_mismatch")
        if len(keys) != len(set(keys)):
            _fail("duplicate_entry")
        if any(key <= cursor for key in keys):
            _fail("relation_mismatch")
        if expected_continuation is not None and (not keys or keys[0] != expected_continuation):
            _fail("relation_mismatch")
        if len(rows) == 257:
            next_cursor = _require_cursor(page.next_cursor)
            if next_cursor != keys[255] or page_index == len(transcript) - 1:
                _fail("relation_mismatch")
            if len(accepted) + 256 > 65536 or len(accepted) == 65280:
                # At 65,536 accepted rows, the 257th fetched row is the
                # mandatory explicit overflow probe.
                _fail("invalid_cardinality")
            accepted.extend(rows[:256])
            expected_cursor = next_cursor
            expected_continuation = keys[256]
        else:
            if page.next_cursor is not None or page_index != len(transcript) - 1:
                _fail("relation_mismatch")
            if len(accepted) + len(rows) > 65536:
                _fail("invalid_cardinality")
            accepted.extend(rows)
            expected_continuation = None
    if expected_continuation is not None:
        _fail("relation_mismatch")
    accepted_keys = tuple((entry.kind_rank, entry.membership_ref) for entry in accepted)
    if accepted_keys != tuple(sorted(accepted_keys)):
        _fail("relation_mismatch")
    if len(accepted_keys) != len(set(accepted_keys)):
        _fail("duplicate_entry")
    if tuple(result.entries) != tuple(accepted):
        _fail("source_owner_mismatch")
    return result


def _evaluate_parent_dispatched_branch_entry(
    parent: object,
) -> _PostExecutionValue:
    if type(parent) not in {
        RW0CDecisionTimeAuthorityBranchMatrixV1,
        RW0CDecisionTimeGlobalStopBranchMatrixV1,
        RW0CDecisionTimeSourceEffectCeilingBranchMatrixV1,
    }:
        _fail("evaluation_contract_mismatch")
    parent._validate_value()
    return typing.cast(_PostExecutionValue, parent)


_CURRENT_SOURCE_TYPES = (
    PostExecutionValidationResultSetV1,
    PostExecutionReviewResultSetV1,
    PostExecutionStandingPolicySourceAttestationV1,
    PostExecutionRiskSourceProfileV1,
    PostExecutionRiskSourceBindingV1,
)
_CURRENT_SOURCE_ROLES = (
    "validation", "review", "policy", "risk_profile", "risk_binding",
)
_CURRENT_SOURCE_SCHEMAS = (
    "governed-execution.nwp-worker-observation.v1",
    "governed-execution.nwp-worker-observation.v1",
    "governed-execution.nwp-post-execution-standing-policy-source-attestation.v1",
    "governed-execution.nwp-post-execution-risk-source-profile.v1",
    "governed-execution.nwp-post-execution-risk-source-binding.v1",
)
_CURRENT_SOURCE_PROFILES = (
    ("post-execution-validation-result-set.v1", "cff49323050cd70855d7fda9b8bcc2666da18a7a3f30f8d8e030a9d60b087d58"),
    ("post-execution-review-result-set.v1", "2dd40a8e0c3628f9e0e3860acc29c0ee908111ce14c7e8dccf944e4b1e9d9730"),
    ("post-execution-standing-policy-source-attestation.v1", "a68f350c418edfe7477cdd8b6b5a709974deff058f382919169154fcbaa7fd12"),
    ("post-execution-risk-source-profile.v1", "1c82ba782f69f24d0e4be84cab71db04f61bedd40f74a3f602c160a408bbca4a"),
    ("post-execution-risk-source-binding.v1", "c4982a13fe91d7af98e87eab7b67d8f9c45b390c82e0232905a53d25dde48471"),
)


def _require_exact_value(value: object, value_type: type[_PostExecutionValue]) -> _PostExecutionValue:
    if type(value) is not value_type:
        _fail("source_owner_mismatch")
    result = typing.cast(_PostExecutionValue, value)
    result._validate_value()
    return result


def _require_source_tuple(value: object) -> tuple[_PostExecutionValue, ...]:
    if type(value) is not tuple or len(value) != 5:
        _fail("invalid_cardinality")
    result = typing.cast(tuple[object, ...], value)
    if any(type(member) is not expected for member, expected in zip(result, _CURRENT_SOURCE_TYPES, strict=True)):
        _fail("source_owner_mismatch")
    typed = tuple(typing.cast(_PostExecutionValue, member) for member in result)
    for member in typed:
        member._validate_value()
    binding = typing.cast(PostExecutionRiskSourceBindingV1, typed[4])
    profile = typing.cast(PostExecutionRiskSourceProfileV1, typed[3])
    if (
        binding.source_profile_schema_id != profile.schema_id
        or binding.source_profile_ref != profile.source_profile_ref
        or binding.source_profile_digest != profile.source_profile_digest
    ):
        _fail("source_owner_mismatch")
    return typed


def _source_coordinate(source: _PostExecutionValue, index: int) -> tuple[object, ...]:
    if index == 0:
        typed = typing.cast(PostExecutionValidationResultSetV1, source)
        source_ref, source_digest = typed.source_observation_ref, typed.source_observation_digest
    elif index == 1:
        typed = typing.cast(PostExecutionReviewResultSetV1, source)
        source_ref, source_digest = typed.source_observation_ref, typed.source_observation_digest
    elif index == 2:
        typed = typing.cast(PostExecutionStandingPolicySourceAttestationV1, source)
        source_ref, source_digest = typed.attestation_ref, typed.attestation_digest
    elif index == 3:
        typed = typing.cast(PostExecutionRiskSourceProfileV1, source)
        source_ref, source_digest = typed.source_profile_ref, typed.source_profile_digest
    else:
        typed = typing.cast(PostExecutionRiskSourceBindingV1, source)
        source_ref, source_digest = typed.source_binding_ref, typed.source_binding_digest
    return (
        _CURRENT_SOURCE_ROLES[index], _CURRENT_SOURCE_SCHEMAS[index],
        source_ref, source_digest, _CURRENT_SOURCE_PROFILES[index][0],
        _CURRENT_SOURCE_PROFILES[index][1], True,
    )


def _candidate_coordinate(value: "ExternalCurrentSourceCoordinateV1") -> tuple[object, ...]:
    return (
        value.role, value.source_schema_id, value.source_ref, value.source_digest,
        value.profile_ref, value.profile_digest, value.source_available,
    )


def _matrix_pairs(value: _PostExecutionValue) -> tuple[tuple[object, object], ...]:
    return tuple((entry.result, entry.reason) for entry in typing.cast(tuple[DecisionBranchEvaluationEntryV1, ...], value.entries))


def _expected_matrix_pairs(
    governed: tuple[str, str],
    halt: tuple[str, str],
) -> tuple[tuple[str, str], ...]:
    return tuple(governed if applicability == "governed" else halt for _, applicability, _ in _DECISION_BRANCHES)


def _lineage_matches_snapshot(
    lineage: Section41PostExecutionSemanticReviewLineageContextV1,
    snapshot: "RW0CDecisionCurrentSnapshotV1",
) -> bool:
    return all(
        _exact_equal(getattr(lineage, field), getattr(snapshot, field))
        for field in (
            "program_ref", "program_version_ref", "accepted_intent_revision_ref",
            "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
            "candidate_ref", "attempt_fence_ref", "attempt_fence_digest",
            "effect_fence_ref", "effect_fence_digest",
        )
    )

_RW0_C_DECISION_CURRENT_SNAPSHOT_PROFILE_REF = 'rw0-c-decision-current-snapshot.v1'
_RW0_C_DECISION_CURRENT_SNAPSHOT_PROFILE_DIGEST = '8bc6f746c2b071f9295c171c9e0caacddda4f61f4d0dfde571bbebb46e0da7dc'
_RW0_C_DECISION_MEMBERSHIP_CLOSURE_PROFILE_REF = 'rw0-c-decision-membership-closure.v1'
_RW0_C_DECISION_MEMBERSHIP_CLOSURE_PROFILE_DIGEST = 'db06318a51022ccec345e29a66008e96dd8cf81231bdb8055167960efce07928'
_RW0_C_DECISION_TIME_AUTHORITY_BRANCH_PROFILE_REF = 'rw0-c-decision-time-authority-branch.v1'
_RW0_C_DECISION_TIME_AUTHORITY_BRANCH_PROFILE_DIGEST = '07384a871dd87a8387c97bb1cd60e6cc8207333428e04e7766044ec8567677dc'
_RW0_C_DECISION_TIME_GLOBAL_STOP_BRANCH_PROFILE_REF = 'rw0-c-decision-time-global-stop-branch.v1'
_RW0_C_DECISION_TIME_GLOBAL_STOP_BRANCH_PROFILE_DIGEST = '6139df3c64d3736e6938605bc6abef22c258e4841ffe8b641d7a70490f6a5e47'
_RW0_C_DECISION_TIME_SOURCE_EFFECT_CEILING_BRANCH_PROFILE_REF = 'rw0-c-decision-time-source-effect-ceiling-branch.v1'
_RW0_C_DECISION_TIME_SOURCE_EFFECT_CEILING_BRANCH_PROFILE_DIGEST = '41a6233d964b084cc582bfbaca6ef34e57601996a0d0fc59c77024427af700d2'
_RW0_C_PROPOSAL_EVIDENCE_CURRENTNESS_PROFILE_REF = 'rw0-c-proposal-evidence-currentness.v1'
_RW0_C_PROPOSAL_EVIDENCE_CURRENTNESS_PROFILE_DIGEST = '88b347a069c92a5804ba53dad4f39a9d7ba6a36413fa38812f81e964a8902e9b'
_RW0_C_RECOMMENDATION_CONSISTENCY_PROFILE_REF = 'rw0-c-recommendation-consistency.v1'
_RW0_C_RECOMMENDATION_CONSISTENCY_PROFILE_DIGEST = 'b85aba9ee6564d53dcb075c5bb60e33a3b923a504c9b38046f2f96aa28f05ebd'

RW0CDecisionMembershipClosureEntryV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'RW0CDecisionMembershipClosureEntryV1', 'ge_nwp_coordinator._rw0_c_decision_input_values',
        {'v_number': 'V26',
 'schema_id': 'governed-execution.nwp-rw0-c-decision-membership-closure-entry.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-rw0-c-decision-membership-closure-entry.v1',
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
                    {'name': 'value_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
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
 'governing_profile_pair': {'profile_digest': 'db06318a51022ccec345e29a66008e96dd8cf81231bdb8055167960efce07928',
                            'profile_ref': 'rw0-c-decision-membership-closure.v1'},
 'reference_posture': {'posture': 'parent_bound_or_no_standalone_ref'},
 'digest_posture': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
        nested={},
        meta={},
    ),
)


RW0CDecisionMembershipClosureV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'RW0CDecisionMembershipClosureV1', 'ge_nwp_coordinator._rw0_c_decision_input_values',
        {'v_number': 'V25',
 'schema_id': 'governed-execution.nwp-rw0-c-decision-membership-closure.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-rw0-c-decision-membership-closure.v1',
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
 'governing_profile_pair': {'profile_digest': 'db06318a51022ccec345e29a66008e96dd8cf81231bdb8055167960efce07928',
                            'profile_ref': 'rw0-c-decision-membership-closure.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-rw0-c-decision-membership-closure.v1.key',
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
 'digest_posture': {'domain': 'governed-execution.nwp-rw0-c-decision-membership-closure.v1.identity',
                    'field': 'closure_digest',
                    'self_exclusion': ['closure_digest']}},
        nested={'entries': RW0CDecisionMembershipClosureEntryV1},
        meta={},
    ),
)


ExternalCurrentSourceCoordinateV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'ExternalCurrentSourceCoordinateV1', 'ge_nwp_coordinator._rw0_c_decision_input_values',
        {'v_number': 'V28',
 'schema_id': 'governed-execution.nwp-rw0-c-external-current-source-coordinate.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-rw0-c-external-current-source-coordinate.v1',
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
 'governing_profile_pair': {'profile_digest': '8bc6f746c2b071f9295c171c9e0caacddda4f61f4d0dfde571bbebb46e0da7dc',
                            'profile_ref': 'rw0-c-decision-current-snapshot.v1'},
 'reference_posture': {'posture': 'parent_bound_or_no_standalone_ref'},
 'digest_posture': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
        nested={},
        meta={},
    ),
)


RW0CDecisionCurrentSnapshotV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'RW0CDecisionCurrentSnapshotV1', 'ge_nwp_coordinator._rw0_c_decision_input_values',
        {'v_number': 'V27',
 'schema_id': 'governed-execution.nwp-rw0-c-decision-current-snapshot.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-rw0-c-decision-current-snapshot.v1',
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
 'governing_profile_pair': {'profile_digest': '8bc6f746c2b071f9295c171c9e0caacddda4f61f4d0dfde571bbebb46e0da7dc',
                            'profile_ref': 'rw0-c-decision-current-snapshot.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-rw0-c-decision-current-snapshot.v1.key',
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
 'digest_posture': {'domain': 'governed-execution.nwp-rw0-c-decision-current-snapshot.v1.identity',
                    'field': 'snapshot_digest',
                    'self_exclusion': ['snapshot_digest']}},
        nested={'external_sources': ExternalCurrentSourceCoordinateV1},
        meta={},
    ),
)


RW0CProposalEvidenceCurrentnessComponentV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'RW0CProposalEvidenceCurrentnessComponentV1', 'ge_nwp_coordinator._rw0_c_decision_input_values',
        {'v_number': 'V30',
 'schema_id': 'governed-execution.nwp-rw0-c-proposal-evidence-currentness-component.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-rw0-c-proposal-evidence-currentness-component.v1',
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
 'governing_profile_pair': {'profile_digest': '88b347a069c92a5804ba53dad4f39a9d7ba6a36413fa38812f81e964a8902e9b',
                            'profile_ref': 'rw0-c-proposal-evidence-currentness.v1'},
 'reference_posture': {'posture': 'parent_bound_or_no_standalone_ref'},
 'digest_posture': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
        nested={},
        meta={},
    ),
)


RW0CProposalEvidenceCurrentnessV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'RW0CProposalEvidenceCurrentnessV1', 'ge_nwp_coordinator._rw0_c_decision_input_values',
        {'v_number': 'V29',
 'schema_id': 'governed-execution.nwp-rw0-c-proposal-evidence-currentness.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-rw0-c-proposal-evidence-currentness.v1',
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
 'governing_profile_pair': {'profile_digest': '88b347a069c92a5804ba53dad4f39a9d7ba6a36413fa38812f81e964a8902e9b',
                            'profile_ref': 'rw0-c-proposal-evidence-currentness.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-rw0-c-proposal-evidence-currentness.v1.key',
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
 'digest_posture': {'domain': 'governed-execution.nwp-rw0-c-proposal-evidence-currentness.v1.identity',
                    'field': 'currentness_digest',
                    'self_exclusion': ['currentness_digest']}},
        nested={'components': RW0CProposalEvidenceCurrentnessComponentV1},
        meta={},
    ),
)


RW0CDecisionTimeAuthorityBranchMatrixV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'RW0CDecisionTimeAuthorityBranchMatrixV1', 'ge_nwp_coordinator._rw0_c_decision_input_values',
        {'v_number': 'V31',
 'schema_id': 'governed-execution.nwp-rw0-c-decision-time-authority-branch-matrix.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-rw0-c-decision-time-authority-branch-matrix.v1',
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
                              'parent_identity_protection': 'the parent matrix ref/digest pair '
                                                            'identifies the matrix and '
                                                            'matrix_digest binds exact child order '
                                                            'and canonical bytes',
                              'parent_profile_dispatch': {'profile_digest': '07384a871dd87a8387c97bb1cd60e6cc8207333428e04e7766044ec8567677dc',
                                                          'profile_ref': 'rw0-c-decision-time-authority-branch.v1'},
                              'parent_source_binding': {'direct_fields': ['snapshot_ref',
                                                                          'snapshot_digest',
                                                                          'proposal_ref',
                                                                          'proposal_digest',
                                                                          'profile_ref',
                                                                          'profile_digest'],
                                                        'posture': 'parent_only',
                                                        'proof': 'the exact current snapshot binds '
                                                                 'closure and selected-authority '
                                                                 'membership lineage; the proposal '
                                                                 'pair and authority profile '
                                                                 'complete the unique authority '
                                                                 'basis shared by all five entries',
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
 'governing_profile_pair': {'profile_digest': '07384a871dd87a8387c97bb1cd60e6cc8207333428e04e7766044ec8567677dc',
                            'profile_ref': 'rw0-c-decision-time-authority-branch.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-rw0-c-decision-time-authority-branch-matrix.v1.key',
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
 'digest_posture': {'domain': 'governed-execution.nwp-rw0-c-decision-time-authority-branch-matrix.v1.identity',
                    'field': 'matrix_digest',
                    'self_exclusion': ['matrix_digest']}},
        nested={'entries': DecisionBranchEvaluationEntryV1},
        meta={'matrix': {'branches': (('candidate_acceptance', 'governed', 'author_candidate'),
                         ('candidate_repair', 'governed', 'author_candidate'),
                         ('attempt_selecting_replan', 'governed', 'author_candidate'),
                         ('program_terminal_reject', 'halt_only', None),
                         ('post_execution_program_block', 'halt_only', None)),
            'allowed_pairs': (('conflict', 'snapshot_or_phase_mismatch'),
                              ('conflict', 'parent_or_fence_identity_mismatch'),
                              ('conflict', 'profile_mismatch'),
                              ('conflict', 'support_conflict'),
                              ('permit', 'halt_only_authority_not_applicable'),
                              ('deny', 'authority_denied'),
                              ('deny', 'authority_revoked'),
                              ('deny', 'attempt_fence_expired'),
                              ('deny', 'effect_fence_expired'),
                              ('deny', 'authority_grant_expired'),
                              ('deny', 'authority_observation_expired'),
                              ('deny', 'effect_class_not_allowed'),
                              ('unknown', 'authority_status_unknown'),
                              ('unknown', 'family_status_unknown'),
                              ('unknown', 'revocation_status_unknown'),
                              ('permit', 'authority_verified_current'))}},
    ),
)


RW0CDecisionTimeGlobalStopBranchMatrixV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'RW0CDecisionTimeGlobalStopBranchMatrixV1', 'ge_nwp_coordinator._rw0_c_decision_input_values',
        {'v_number': 'V32',
 'schema_id': 'governed-execution.nwp-rw0-c-decision-time-global-stop-branch-matrix.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-rw0-c-decision-time-global-stop-branch-matrix.v1',
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
                              'parent_identity_protection': 'the parent matrix ref/digest pair '
                                                            'identifies the matrix and '
                                                            'matrix_digest binds exact child order '
                                                            'and canonical bytes',
                              'parent_profile_dispatch': {'profile_digest': '6139df3c64d3736e6938605bc6abef22c258e4841ffe8b641d7a70490f6a5e47',
                                                          'profile_ref': 'rw0-c-decision-time-global-stop-branch.v1'},
                              'parent_source_binding': {'direct_fields': ['global_stop_ref',
                                                                          'global_stop_digest',
                                                                          'snapshot_ref',
                                                                          'snapshot_digest',
                                                                          'profile_ref',
                                                                          'profile_digest'],
                                                        'posture': 'parent_only',
                                                        'proof': 'the V32 parent directly binds '
                                                                 'the exact global-stop source '
                                                                 'plus snapshot and profile used '
                                                                 'by all five entries'},
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
 'governing_profile_pair': {'profile_digest': '6139df3c64d3736e6938605bc6abef22c258e4841ffe8b641d7a70490f6a5e47',
                            'profile_ref': 'rw0-c-decision-time-global-stop-branch.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-rw0-c-decision-time-global-stop-branch-matrix.v1.key',
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
 'digest_posture': {'domain': 'governed-execution.nwp-rw0-c-decision-time-global-stop-branch-matrix.v1.identity',
                    'field': 'matrix_digest',
                    'self_exclusion': ['matrix_digest']}},
        nested={'entries': DecisionBranchEvaluationEntryV1},
        meta={'matrix': {'branches': (('candidate_acceptance', 'governed', 'author_candidate'),
                         ('candidate_repair', 'governed', 'author_candidate'),
                         ('attempt_selecting_replan', 'governed', 'author_candidate'),
                         ('program_terminal_reject', 'halt_only', None),
                         ('post_execution_program_block', 'halt_only', None)),
            'allowed_pairs': (('conflict', 'snapshot_or_stop_identity_mismatch'),
                              ('conflict', 'profile_mismatch'),
                              ('unknown', 'global_stop_unknown'),
                              ('permit', 'halt_only_stop_checked'),
                              ('deny', 'global_stop_active'),
                              ('permit', 'global_stop_clear'))}},
    ),
)


RW0CDecisionTimeSourceEffectCeilingBranchMatrixV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'RW0CDecisionTimeSourceEffectCeilingBranchMatrixV1', 'ge_nwp_coordinator._rw0_c_decision_input_values',
        {'v_number': 'V33',
 'schema_id': 'governed-execution.nwp-rw0-c-decision-time-source-effect-ceiling-branch-matrix.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-rw0-c-decision-time-source-effect-ceiling-branch-matrix.v1',
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
                              'parent_identity_protection': 'the parent matrix ref/digest pair '
                                                            'identifies the matrix and '
                                                            'matrix_digest binds exact child order '
                                                            'and canonical bytes',
                              'parent_profile_dispatch': {'profile_digest': '41a6233d964b084cc582bfbaca6ef34e57601996a0d0fc59c77024427af700d2',
                                                          'profile_ref': 'rw0-c-decision-time-source-effect-ceiling-branch.v1'},
                              'parent_source_binding': {'direct_fields': ['source_effect_ceiling_ref',
                                                                          'source_effect_ceiling_digest',
                                                                          'snapshot_ref',
                                                                          'snapshot_digest',
                                                                          'profile_ref',
                                                                          'profile_digest'],
                                                        'posture': 'parent_only',
                                                        'proof': 'the V33 parent directly binds '
                                                                 'the exact source-effect-ceiling '
                                                                 'source plus snapshot and profile '
                                                                 'used by all five entries'},
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
 'governing_profile_pair': {'profile_digest': '41a6233d964b084cc582bfbaca6ef34e57601996a0d0fc59c77024427af700d2',
                            'profile_ref': 'rw0-c-decision-time-source-effect-ceiling-branch.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-rw0-c-decision-time-source-effect-ceiling-branch-matrix.v1.key',
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
 'digest_posture': {'domain': 'governed-execution.nwp-rw0-c-decision-time-source-effect-ceiling-branch-matrix.v1.identity',
                    'field': 'matrix_digest',
                    'self_exclusion': ['matrix_digest']}},
        nested={'entries': DecisionBranchEvaluationEntryV1},
        meta={'matrix': {'branches': (('candidate_acceptance', 'governed', 'author_candidate'),
                         ('candidate_repair', 'governed', 'author_candidate'),
                         ('attempt_selecting_replan', 'governed', 'author_candidate'),
                         ('program_terminal_reject', 'halt_only', None),
                         ('post_execution_program_block', 'halt_only', None)),
            'allowed_pairs': (('conflict', 'snapshot_lineage_or_fence_mismatch'),
                              ('conflict', 'proposal_evidence_conflict'),
                              ('conflict', 'profile_mismatch'),
                              ('conflict', 'support_conflict'),
                              ('permit', 'halt_only_ceiling_not_applicable'),
                              ('deny', 'proposal_evidence_noncompliant'),
                              ('deny', 'attempt_fence_expired'),
                              ('deny', 'effect_fence_expired'),
                              ('deny', 'authority_grant_expired'),
                              ('deny', 'authority_observation_expired'),
                              ('deny', 'effect_class_not_allowed'),
                              ('deny', 'source_effect_exceeds_current_attempt'),
                              ('deny', 'source_effect_exceeds_current_effect'),
                              ('deny', 'source_effect_exceeds_current_authority'),
                              ('unknown', 'proposal_evidence_unknown'),
                              ('unknown', 'current_authority_unknown'),
                              ('permit', 'source_effect_within_current_ceilings'))}},
    ),
)


RW0CRecommendationConsistencyEvaluationV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'RW0CRecommendationConsistencyEvaluationV1', 'ge_nwp_coordinator._rw0_c_decision_input_values',
        {'v_number': 'V34',
 'schema_id': 'governed-execution.nwp-rw0-c-recommendation-consistency-evaluation.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-rw0-c-recommendation-consistency-evaluation.v1',
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
                    {'name': 'model_recommendation',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'mapped_branch', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'authoritative_branch',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
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
 'governing_profile_pair': {'profile_digest': 'b85aba9ee6564d53dcb075c5bb60e33a3b923a504c9b38046f2f96aa28f05ebd',
                            'profile_ref': 'rw0-c-recommendation-consistency.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-rw0-c-recommendation-consistency-evaluation.v1.key',
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
 'digest_posture': {'domain': 'governed-execution.nwp-rw0-c-recommendation-consistency-evaluation.v1.identity',
                    'field': 'evaluation_digest',
                    'self_exclusion': ['evaluation_digest']}},
        nested={},
        meta={},
    ),
)


def rw0_c_decision_current_snapshot(
    value: object,
    *,
    lineage_context: Section41PostExecutionSemanticReviewLineageContextV1,
    input_context: PostExecutionSemanticReviewInputContextV1,
    membership_closure: RW0CDecisionMembershipClosureV1,
    selected_authority_membership: RW0CDecisionMembershipClosureEntryV1,
    selected_section41_membership: RW0CDecisionMembershipClosureEntryV1,
    global_stop_snapshot: PostExecutionGlobalStopSnapshotV1,
    source_effect_ceiling: PostExecutionSourceEffectCeilingEvidenceV1,
    external_sources: tuple[_PostExecutionValue, ...],
) -> RW0CDecisionCurrentSnapshotV1:
    """Verify one snapshot as the exact projection of its current owners."""

    lineage = typing.cast(
        Section41PostExecutionSemanticReviewLineageContextV1,
        _require_exact_value(lineage_context, Section41PostExecutionSemanticReviewLineageContextV1),
    )
    context = typing.cast(
        PostExecutionSemanticReviewInputContextV1,
        _require_exact_value(input_context, PostExecutionSemanticReviewInputContextV1),
    )
    closure = typing.cast(
        RW0CDecisionMembershipClosureV1,
        _require_exact_value(membership_closure, RW0CDecisionMembershipClosureV1),
    )
    authority_member = typing.cast(
        RW0CDecisionMembershipClosureEntryV1,
        _require_exact_value(selected_authority_membership, RW0CDecisionMembershipClosureEntryV1),
    )
    section41_member = typing.cast(
        RW0CDecisionMembershipClosureEntryV1,
        _require_exact_value(selected_section41_membership, RW0CDecisionMembershipClosureEntryV1),
    )
    stop = typing.cast(
        PostExecutionGlobalStopSnapshotV1,
        _require_exact_value(global_stop_snapshot, PostExecutionGlobalStopSnapshotV1),
    )
    ceiling = typing.cast(
        PostExecutionSourceEffectCeilingEvidenceV1,
        _require_exact_value(source_effect_ceiling, PostExecutionSourceEffectCeilingEvidenceV1),
    )
    sources = _require_source_tuple(external_sources)
    candidate = typing.cast(
        RW0CDecisionCurrentSnapshotV1,
        RW0CDecisionCurrentSnapshotV1.from_supplied(value),
    )
    if (
        context.lineage_context_schema_id != lineage.schema_id
        or context.lineage_context_ref != lineage.lineage_context_ref
        or context.lineage_context_digest != lineage.lineage_context_digest
        or closure.phase_basis_ref != context.phase_basis_ref
        or closure.phase_basis_digest != context.phase_basis_digest
        or authority_member.kind_rank != 1
        or section41_member.kind_rank != 15
        or authority_member not in closure.entries
        or section41_member not in closure.entries
        or authority_member.value_ref != ceiling.authority_observation_ref
        or authority_member.value_digest != ceiling.authority_observation_digest
    ):
        _fail("source_owner_mismatch")
    if not _lineage_matches_snapshot(lineage, candidate):
        _fail("source_owner_mismatch")
    for field in (
        "program_ref", "program_version_ref", "accepted_intent_revision_ref",
        "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
        "candidate_ref", "attempt_fence_ref", "attempt_fence_digest",
        "effect_fence_ref", "effect_fence_digest",
    ):
        if not _exact_equal(getattr(ceiling, field), getattr(candidate, field)):
            _fail("source_owner_mismatch")
    expected = {
        "phase_basis_ref": context.phase_basis_ref,
        "phase_basis_digest": context.phase_basis_digest,
        "membership_closure_ref": closure.closure_ref,
        "membership_closure_digest": closure.closure_digest,
        "selected_authority_membership_ref": authority_member.membership_ref,
        "selected_authority_membership_digest": authority_member.membership_digest,
        "selected_section41_membership_ref": section41_member.membership_ref,
        "selected_section41_membership_digest": section41_member.membership_digest,
        "global_stop_ref": stop.global_stop_ref,
        "global_stop_digest": stop.global_stop_digest,
        "captured_at": closure.captured_at,
    }
    if any(not _exact_equal(getattr(candidate, field), expected_value) for field, expected_value in expected.items()):
        _fail("source_owner_mismatch")
    if tuple(_candidate_coordinate(item) for item in candidate.external_sources) != tuple(
        _source_coordinate(source, index) for index, source in enumerate(sources)
    ):
        _fail("source_owner_mismatch")
    validation = typing.cast(PostExecutionValidationResultSetV1, sources[0])
    review = typing.cast(PostExecutionReviewResultSetV1, sources[1])
    policy = typing.cast(PostExecutionStandingPolicySourceAttestationV1, sources[2])
    risk_binding = typing.cast(PostExecutionRiskSourceBindingV1, sources[4])
    if not (
        stop.evaluated_at <= candidate.captured_at
        and ceiling.evaluated_at <= candidate.captured_at
        and validation.evaluated_at <= candidate.captured_at < validation.expires_at
        and review.evaluated_at <= candidate.captured_at < review.expires_at
        and policy.evaluated_at <= candidate.captured_at < policy.expires_at
        and risk_binding.evaluated_at <= candidate.captured_at < risk_binding.expires_at
    ):
        _fail("relation_mismatch")
    return candidate


def rw0_c_decision_membership_closure(
    value: object,
    *,
    pages: tuple[_MembershipPage, ...],
) -> RW0CDecisionMembershipClosureV1:
    """Replay the frozen 256/257 transcript and verify the complete closure."""

    return _validate_bounded_membership_closure(value, pages=pages)


def evaluate_rw0_c_decision_time_authority_branches(
    value: object,
    *,
    snapshot: RW0CDecisionCurrentSnapshotV1,
    projection: Section41PostExecutionProposalFamilyProjectionV2,
    lineage_context: Section41PostExecutionSemanticReviewLineageContextV1,
    input_context: PostExecutionSemanticReviewInputContextV1,
    membership_closure: RW0CDecisionMembershipClosureV1,
    selected_authority_membership: RW0CDecisionMembershipClosureEntryV1,
    source_effect_ceiling: PostExecutionSourceEffectCeilingEvidenceV1,
) -> RW0CDecisionTimeAuthorityBranchMatrixV1:
    """Derive the authority matrix from the exact current snapshot and owners."""

    snap = typing.cast(RW0CDecisionCurrentSnapshotV1, _require_exact_value(snapshot, RW0CDecisionCurrentSnapshotV1))
    proposal = typing.cast(
        Section41PostExecutionProposalFamilyProjectionV2,
        _require_exact_value(projection, Section41PostExecutionProposalFamilyProjectionV2),
    )
    lineage = typing.cast(
        Section41PostExecutionSemanticReviewLineageContextV1,
        _require_exact_value(lineage_context, Section41PostExecutionSemanticReviewLineageContextV1),
    )
    context = typing.cast(
        PostExecutionSemanticReviewInputContextV1,
        _require_exact_value(input_context, PostExecutionSemanticReviewInputContextV1),
    )
    closure = typing.cast(
        RW0CDecisionMembershipClosureV1,
        _require_exact_value(membership_closure, RW0CDecisionMembershipClosureV1),
    )
    authority_member = typing.cast(
        RW0CDecisionMembershipClosureEntryV1,
        _require_exact_value(selected_authority_membership, RW0CDecisionMembershipClosureEntryV1),
    )
    ceiling = typing.cast(
        PostExecutionSourceEffectCeilingEvidenceV1,
        _require_exact_value(source_effect_ceiling, PostExecutionSourceEffectCeilingEvidenceV1),
    )
    candidate = typing.cast(
        RW0CDecisionTimeAuthorityBranchMatrixV1,
        RW0CDecisionTimeAuthorityBranchMatrixV1.from_supplied(value),
    )
    if (
        candidate.snapshot_ref != snap.snapshot_ref
        or candidate.snapshot_digest != snap.snapshot_digest
        or candidate.proposal_ref != proposal.proposal_ref
        or candidate.proposal_digest != proposal.proposal_digest
        or candidate.evaluated_at < snap.captured_at
    ):
        _fail("source_owner_mismatch")
    phase_mismatch = (
        closure.closure_ref != snap.membership_closure_ref
        or closure.closure_digest != snap.membership_closure_digest
        or closure.phase_basis_ref != snap.phase_basis_ref
        or closure.phase_basis_digest != snap.phase_basis_digest
        or context.phase_basis_ref != snap.phase_basis_ref
        or context.phase_basis_digest != snap.phase_basis_digest
        or authority_member.kind_rank != 1
        or authority_member not in closure.entries
        or authority_member.membership_ref != snap.selected_authority_membership_ref
        or authority_member.membership_digest != snap.selected_authority_membership_digest
    )
    parent_mismatch = (
        not _lineage_matches_snapshot(lineage, snap)
        or context.lineage_context_ref != lineage.lineage_context_ref
        or context.lineage_context_digest != lineage.lineage_context_digest
        or proposal.input_context_ref != context.input_context_ref
        or proposal.input_context_digest != context.input_context_digest
        or proposal.lineage_context_ref != lineage.lineage_context_ref
        or proposal.lineage_context_digest != lineage.lineage_context_digest
        or authority_member.value_ref != ceiling.authority_observation_ref
        or authority_member.value_digest != ceiling.authority_observation_digest
        or any(
            not _exact_equal(getattr(ceiling, field), getattr(snap, field))
            for field in (
                "program_ref", "program_version_ref", "accepted_intent_revision_ref",
                "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
                "candidate_ref", "attempt_fence_ref", "attempt_fence_digest",
                "effect_fence_ref", "effect_fence_digest",
            )
        )
    )
    if phase_mismatch:
        expected = _expected_matrix_pairs(
            ("conflict", "snapshot_or_phase_mismatch"),
            ("conflict", "snapshot_or_phase_mismatch"),
        )
    elif parent_mismatch:
        expected = _expected_matrix_pairs(
            ("conflict", "parent_or_fence_identity_mismatch"),
            ("conflict", "parent_or_fence_identity_mismatch"),
        )
    elif ceiling.result == "conflict":
        expected = _expected_matrix_pairs(("conflict", "support_conflict"), ("conflict", "support_conflict"))
    else:
        if ceiling.authority_status == "denied" or ceiling.authority_family_status == "incompatible":
            governed = ("deny", "authority_denied")
        elif ceiling.authority_revocation_status == "revoked":
            governed = ("deny", "authority_revoked")
        elif candidate.evaluated_at >= ceiling.attempt_fence_expires_at:
            governed = ("deny", "attempt_fence_expired")
        elif candidate.evaluated_at >= ceiling.effect_fence_expires_at:
            governed = ("deny", "effect_fence_expired")
        elif candidate.evaluated_at >= ceiling.authority_grant_expires_at:
            governed = ("deny", "authority_grant_expired")
        elif candidate.evaluated_at >= ceiling.authority_observation_expires_at:
            governed = ("deny", "authority_observation_expired")
        elif "author_candidate" not in ceiling.attempt_allowed_effect_classes or "author_candidate" not in ceiling.authority_allowed_effect_classes:
            governed = ("deny", "effect_class_not_allowed")
        elif ceiling.authority_status == "unknown":
            governed = ("unknown", "authority_status_unknown")
        elif ceiling.authority_family_status == "unknown":
            governed = ("unknown", "family_status_unknown")
        elif ceiling.authority_revocation_status == "unknown":
            governed = ("unknown", "revocation_status_unknown")
        else:
            governed = ("permit", "authority_verified_current")
        expected = _expected_matrix_pairs(governed, ("permit", "halt_only_authority_not_applicable"))
    if _matrix_pairs(candidate) != expected:
        _fail("evaluation_contract_mismatch")
    return candidate


def evaluate_rw0_c_decision_time_global_stop_branches(
    value: object,
    *,
    snapshot: RW0CDecisionCurrentSnapshotV1,
    global_stop_snapshot: PostExecutionGlobalStopSnapshotV1,
) -> RW0CDecisionTimeGlobalStopBranchMatrixV1:
    """Derive the global-stop matrix with the frozen source-bound precedence."""

    snap = typing.cast(RW0CDecisionCurrentSnapshotV1, _require_exact_value(snapshot, RW0CDecisionCurrentSnapshotV1))
    stop = typing.cast(
        PostExecutionGlobalStopSnapshotV1,
        _require_exact_value(global_stop_snapshot, PostExecutionGlobalStopSnapshotV1),
    )
    candidate = typing.cast(
        RW0CDecisionTimeGlobalStopBranchMatrixV1,
        RW0CDecisionTimeGlobalStopBranchMatrixV1.from_supplied(value),
    )
    if (
        candidate.snapshot_ref != snap.snapshot_ref
        or candidate.snapshot_digest != snap.snapshot_digest
        or candidate.global_stop_ref != stop.global_stop_ref
        or candidate.global_stop_digest != stop.global_stop_digest
        or candidate.evaluated_at < snap.captured_at
    ):
        _fail("source_owner_mismatch")
    if snap.global_stop_ref != stop.global_stop_ref or snap.global_stop_digest != stop.global_stop_digest:
        expected = _expected_matrix_pairs(
            ("conflict", "snapshot_or_stop_identity_mismatch"),
            ("conflict", "snapshot_or_stop_identity_mismatch"),
        )
    elif stop.global_stop_state == "unknown":
        expected = _expected_matrix_pairs(
            ("unknown", "global_stop_unknown"), ("unknown", "global_stop_unknown")
        )
    else:
        governed = (
            ("deny", "global_stop_active")
            if stop.global_stop_state == "active"
            else ("permit", "global_stop_clear")
        )
        expected = _expected_matrix_pairs(governed, ("permit", "halt_only_stop_checked"))
    if _matrix_pairs(candidate) != expected:
        _fail("evaluation_contract_mismatch")
    return candidate


def evaluate_rw0_c_decision_time_source_effect_ceiling_branches(
    value: object,
    *,
    snapshot: RW0CDecisionCurrentSnapshotV1,
    lineage_context: Section41PostExecutionSemanticReviewLineageContextV1,
    source_effect_ceiling: PostExecutionSourceEffectCeilingEvidenceV1,
) -> RW0CDecisionTimeSourceEffectCeilingBranchMatrixV1:
    """Derive the source-effect-ceiling matrix from its exact evidence owner."""

    snap = typing.cast(RW0CDecisionCurrentSnapshotV1, _require_exact_value(snapshot, RW0CDecisionCurrentSnapshotV1))
    lineage = typing.cast(
        Section41PostExecutionSemanticReviewLineageContextV1,
        _require_exact_value(lineage_context, Section41PostExecutionSemanticReviewLineageContextV1),
    )
    ceiling = typing.cast(
        PostExecutionSourceEffectCeilingEvidenceV1,
        _require_exact_value(source_effect_ceiling, PostExecutionSourceEffectCeilingEvidenceV1),
    )
    candidate = typing.cast(
        RW0CDecisionTimeSourceEffectCeilingBranchMatrixV1,
        RW0CDecisionTimeSourceEffectCeilingBranchMatrixV1.from_supplied(value),
    )
    if (
        candidate.snapshot_ref != snap.snapshot_ref
        or candidate.snapshot_digest != snap.snapshot_digest
        or candidate.source_effect_ceiling_ref != ceiling.evidence_ref
        or candidate.source_effect_ceiling_digest != ceiling.evidence_digest
        or candidate.evaluated_at < snap.captured_at
    ):
        _fail("source_owner_mismatch")
    lineage_mismatch = (
        not _lineage_matches_snapshot(lineage, snap)
        or any(
            not _exact_equal(getattr(ceiling, field), getattr(snap, field))
            for field in (
                "program_ref", "program_version_ref", "accepted_intent_revision_ref",
                "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
                "candidate_ref", "attempt_fence_ref", "attempt_fence_digest",
                "effect_fence_ref", "effect_fence_digest",
            )
        )
    )
    if lineage_mismatch:
        expected = _expected_matrix_pairs(
            ("conflict", "snapshot_lineage_or_fence_mismatch"),
            ("conflict", "snapshot_lineage_or_fence_mismatch"),
        )
    elif ceiling.result == "conflict":
        reason = "support_conflict" if ceiling.reason == "support_conflict" else "proposal_evidence_conflict"
        expected = _expected_matrix_pairs(("conflict", reason), ("conflict", reason))
    else:
        reason_map = {
            "authority_denied_or_revoked": ("deny", "proposal_evidence_noncompliant"),
            "attempt_fence_expired": ("deny", "attempt_fence_expired"),
            "effect_fence_expired": ("deny", "effect_fence_expired"),
            "authority_grant_expired": ("deny", "authority_grant_expired"),
            "authority_observation_expired": ("deny", "authority_observation_expired"),
            "effect_class_not_allowed_by_attempt": ("deny", "effect_class_not_allowed"),
            "effect_class_not_allowed_by_authority": ("deny", "effect_class_not_allowed"),
            "effect_exceeds_attempt": ("deny", "source_effect_exceeds_current_attempt"),
            "effect_exceeds_effect_fence": ("deny", "source_effect_exceeds_current_effect"),
            "effect_exceeds_authority": ("deny", "source_effect_exceeds_current_authority"),
            "authority_status_unknown": ("unknown", "current_authority_unknown"),
            "authority_family_unknown": ("unknown", "current_authority_unknown"),
            "authority_revocation_unknown": ("unknown", "current_authority_unknown"),
            "authority_ceiling_unknown": ("unknown", "current_authority_unknown"),
        }
        if candidate.evaluated_at >= ceiling.attempt_fence_expires_at:
            governed = ("deny", "attempt_fence_expired")
        elif candidate.evaluated_at >= ceiling.effect_fence_expires_at:
            governed = ("deny", "effect_fence_expired")
        elif candidate.evaluated_at >= ceiling.authority_grant_expires_at:
            governed = ("deny", "authority_grant_expired")
        elif candidate.evaluated_at >= ceiling.authority_observation_expires_at:
            governed = ("deny", "authority_observation_expired")
        elif ceiling.result == "compliant":
            governed = ("permit", "source_effect_within_current_ceilings")
        elif ceiling.reason in reason_map:
            governed = reason_map[typing.cast(str, ceiling.reason)]
        elif ceiling.result == "unknown":
            governed = ("unknown", "proposal_evidence_unknown")
        else:
            governed = ("deny", "proposal_evidence_noncompliant")
        expected = _expected_matrix_pairs(governed, ("permit", "halt_only_ceiling_not_applicable"))
    if _matrix_pairs(candidate) != expected:
        _fail("evaluation_contract_mismatch")
    return candidate


def evaluate_rw0_c_proposal_evidence_currentness(
    value: object,
    *,
    projection: Section41PostExecutionProposalFamilyProjectionV2,
    snapshot: RW0CDecisionCurrentSnapshotV1,
    proposal_evidence: tuple[_PostExecutionValue, ...],
    proposal_sources: tuple[_PostExecutionValue, ...],
) -> RW0CProposalEvidenceCurrentnessV1:
    """Compare five proposal source owners with five independently current owners."""

    proposal = typing.cast(
        Section41PostExecutionProposalFamilyProjectionV2,
        _require_exact_value(projection, Section41PostExecutionProposalFamilyProjectionV2),
    )
    snap = typing.cast(RW0CDecisionCurrentSnapshotV1, _require_exact_value(snapshot, RW0CDecisionCurrentSnapshotV1))
    if type(proposal_evidence) is not tuple or tuple(type(item) for item in proposal_evidence) != (
        ValidationDispositionV1,
        IndependentReviewDispositionV1,
        PostExecutionStandingPolicyBranchMatrixV1,
        PostExecutionRiskLaneBranchMatrixV1,
    ):
        _fail("source_owner_mismatch")
    evidence = tuple(typing.cast(_PostExecutionValue, item) for item in proposal_evidence)
    for item in evidence:
        item._validate_value()
    sources = _require_source_tuple(proposal_sources)
    validation = typing.cast(ValidationDispositionV1, evidence[0])
    review = typing.cast(IndependentReviewDispositionV1, evidence[1])
    policy_matrix = typing.cast(PostExecutionStandingPolicyBranchMatrixV1, evidence[2])
    risk_matrix = typing.cast(PostExecutionRiskLaneBranchMatrixV1, evidence[3])
    validation_source = typing.cast(PostExecutionValidationResultSetV1, sources[0])
    review_source = typing.cast(PostExecutionReviewResultSetV1, sources[1])
    policy_source = typing.cast(PostExecutionStandingPolicySourceAttestationV1, sources[2])
    risk_profile = typing.cast(PostExecutionRiskSourceProfileV1, sources[3])
    risk_binding = typing.cast(PostExecutionRiskSourceBindingV1, sources[4])
    if (
        validation.source_observation_ref != validation_source.source_observation_ref
        or validation.source_observation_digest != validation_source.source_observation_digest
        or validation.validation_result_set_ref != validation_source.result_set_ref
        or validation.validation_result_set_digest != validation_source.result_set_digest
        or review.source_observation_ref != review_source.source_observation_ref
        or review.source_observation_digest != review_source.source_observation_digest
        or review.review_result_set_ref != review_source.result_set_ref
        or review.review_result_set_digest != review_source.result_set_digest
        or policy_matrix.policy_source_schema_id != policy_source.schema_id
        or policy_matrix.policy_source_ref != policy_source.attestation_ref
        or policy_matrix.policy_source_digest != policy_source.attestation_digest
        or risk_matrix.source_profile_schema_id != risk_profile.schema_id
        or risk_matrix.source_profile_ref != risk_profile.source_profile_ref
        or risk_matrix.source_profile_digest != risk_profile.source_profile_digest
        or risk_matrix.source_binding_schema_id != risk_binding.schema_id
        or risk_matrix.source_binding_ref != risk_binding.source_binding_ref
        or risk_matrix.source_binding_digest != risk_binding.source_binding_digest
    ):
        _fail("source_owner_mismatch")
    projection_expected = (
        ("validation_result", validation.disposition_ref, validation.disposition_digest),
        ("independent_review", review.disposition_ref, review.disposition_digest),
        ("standing_policy", policy_matrix.matrix_ref, policy_matrix.matrix_digest),
        ("risk_lane", risk_matrix.matrix_ref, risk_matrix.matrix_digest),
    )
    projected = {
        entry.evidence_role: (entry.evidence_ref, entry.evidence_digest)
        for entry in proposal.evidence_bindings
    }
    if any(projected.get(role) != (source_ref, source_digest) for role, source_ref, source_digest in projection_expected):
        _fail("source_owner_mismatch")
    candidate = typing.cast(
        RW0CProposalEvidenceCurrentnessV1,
        RW0CProposalEvidenceCurrentnessV1.from_supplied(value),
    )
    if (
        candidate.proposal_ref != proposal.proposal_ref
        or candidate.proposal_digest != proposal.proposal_digest
        or candidate.snapshot_ref != snap.snapshot_ref
        or candidate.snapshot_digest != snap.snapshot_digest
        or candidate.evaluated_at != snap.captured_at
    ):
        _fail("source_owner_mismatch")
    proposal_coordinates = tuple(_source_coordinate(source, index) for index, source in enumerate(sources))
    # The proposal is current only through the earliest expiring member of its
    # five-source currentness set.  Preserve each source coordinate separately,
    # but bind every component to that common finite decision horizon.
    currentness_horizon = min(
        validation_source.expires_at,
        review_source.expires_at,
        policy_source.expires_at,
        risk_binding.expires_at,
    )
    expiries = (currentness_horizon,) * 5
    expected_components: list[tuple[object, ...]] = []
    for index, (proposal_coordinate, current) in enumerate(zip(proposal_coordinates, snap.external_sources, strict=True)):
        role, source_schema, proposal_ref, proposal_digest, profile_ref, profile_digest, _ = proposal_coordinate
        if not current.source_available:
            result_reason = ("unknown", "source_unavailable")
        elif current.source_ref == proposal_ref and current.source_digest != proposal_digest:
            result_reason = ("conflict", "same_ref_different_digest")
        elif current.source_ref != proposal_ref:
            result_reason = ("stale", "different_well_formed_source_pair")
        elif candidate.evaluated_at >= expiries[index]:
            result_reason = ("stale", "exact_source_expired_at_evaluation")
        else:
            result_reason = ("current", "exact_ref_digest_profile_and_freshness")
        expected_components.append((
            role, source_schema, proposal_ref, proposal_digest,
            current.source_schema_id, current.source_ref, current.source_digest,
            profile_ref, profile_digest, expiries[index], candidate.evaluated_at,
            result_reason[0], result_reason[1],
        ))
    observed_components = tuple((
        item.component, item.proposal_source_schema_id, item.proposal_source_ref,
        item.proposal_source_digest, item.current_source_schema_id,
        item.current_source_ref, item.current_source_digest, item.profile_ref,
        item.profile_digest, item.source_expires_at, item.evaluated_at,
        item.result, item.reason,
    ) for item in candidate.components)
    if observed_components != tuple(expected_components):
        _fail("evaluation_contract_mismatch")
    return candidate


def evaluate_rw0_c_recommendation_consistency(
    value: object,
    *,
    projection: Section41PostExecutionProposalFamilyProjectionV2,
    snapshot: RW0CDecisionCurrentSnapshotV1,
    proposal_currentness: RW0CProposalEvidenceCurrentnessV1,
    authority_matrix: RW0CDecisionTimeAuthorityBranchMatrixV1,
    global_stop_matrix: RW0CDecisionTimeGlobalStopBranchMatrixV1,
    source_effect_ceiling_matrix: RW0CDecisionTimeSourceEffectCeilingBranchMatrixV1,
    authoritative_branch: str,
    lineage_context: Section41PostExecutionSemanticReviewLineageContextV1,
    input_context: PostExecutionSemanticReviewInputContextV1,
    membership_closure: RW0CDecisionMembershipClosureV1,
    selected_authority_membership: RW0CDecisionMembershipClosureEntryV1,
    global_stop_snapshot: PostExecutionGlobalStopSnapshotV1,
    source_effect_ceiling: PostExecutionSourceEffectCeilingEvidenceV1,
) -> RW0CRecommendationConsistencyEvaluationV1:
    """Compare model evidence with one already-derived authoritative branch."""

    proposal = typing.cast(
        Section41PostExecutionProposalFamilyProjectionV2,
        _require_exact_value(projection, Section41PostExecutionProposalFamilyProjectionV2),
    )
    snap = typing.cast(RW0CDecisionCurrentSnapshotV1, _require_exact_value(snapshot, RW0CDecisionCurrentSnapshotV1))
    currentness = typing.cast(
        RW0CProposalEvidenceCurrentnessV1,
        _require_exact_value(proposal_currentness, RW0CProposalEvidenceCurrentnessV1),
    )
    authority = evaluate_rw0_c_decision_time_authority_branches(
        authority_matrix,
        snapshot=snap,
        projection=proposal,
        lineage_context=lineage_context,
        input_context=input_context,
        membership_closure=membership_closure,
        selected_authority_membership=selected_authority_membership,
        source_effect_ceiling=source_effect_ceiling,
    )
    stop = evaluate_rw0_c_decision_time_global_stop_branches(
        global_stop_matrix,
        snapshot=snap,
        global_stop_snapshot=global_stop_snapshot,
    )
    ceiling = evaluate_rw0_c_decision_time_source_effect_ceiling_branches(
        source_effect_ceiling_matrix,
        snapshot=snap,
        lineage_context=lineage_context,
        source_effect_ceiling=source_effect_ceiling,
    )
    if type(authoritative_branch) is not str or authoritative_branch not in {item[0] for item in _DECISION_BRANCHES}:
        _fail("invalid_field_value")
    candidate = typing.cast(
        RW0CRecommendationConsistencyEvaluationV1,
        RW0CRecommendationConsistencyEvaluationV1.from_supplied(value),
    )
    if (
        candidate.proposal_ref != proposal.proposal_ref
        or candidate.proposal_digest != proposal.proposal_digest
        or candidate.snapshot_ref != snap.snapshot_ref
        or candidate.snapshot_digest != snap.snapshot_digest
        or candidate.proposal_currentness_ref != currentness.currentness_ref
        or candidate.proposal_currentness_digest != currentness.currentness_digest
        or candidate.authoritative_branch != authoritative_branch
        or len({authority.evaluated_at, stop.evaluated_at, ceiling.evaluated_at, candidate.evaluated_at}) != 1
    ):
        _fail("source_owner_mismatch")
    selected_index = tuple(item[0] for item in _DECISION_BRANCHES).index(authoritative_branch)
    selected_results = (
        authority.entries[selected_index].result,
        stop.entries[selected_index].result,
        ceiling.entries[selected_index].result,
    )
    if (
        any(result == "conflict" for result in selected_results)
        or currentness.proposal_ref != proposal.proposal_ref
        or currentness.proposal_digest != proposal.proposal_digest
        or currentness.snapshot_ref != snap.snapshot_ref
        or currentness.snapshot_digest != snap.snapshot_digest
    ):
        expected = ("basis_conflict", "identity_or_provenance_mismatch")
    elif currentness.result != "current" or any(result != "permit" for result in selected_results):
        expected = ("stale_context", "proposal_or_snapshot_not_current")
    elif candidate.mapped_branch == authoritative_branch:
        expected = ("consistent", "mapped_branch_equals_authoritative_branch")
    else:
        expected = ("inconsistent", "mapped_branch_differs_from_authoritative_branch")
    if (candidate.result, candidate.reason) != expected:
        _fail("evaluation_contract_mismatch")
    return candidate
