"""Closed artificial P1 value and identity controls; no SQLite mutation."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from enum import Enum

import pytest

from ge_nwp_coordinator._rw0_c2_progression_contracts import (
    _BASIS_FIELDS, _BASIS_FIELDS_V1, _BASIS_SCHEMA, _BASIS_SCHEMA_V1,
    _GUARD_SCHEMA, _MAX_BASIS_BYTES,
    _canonical, _self_digest, AdmittedCommandRelationV1, ArtificialDecisionGuardSourceV1, DecisionBasisV1,
    DecisionBasisV2, derive_candidate_evidence_reason,
    CognitiveReplanProposalV1, CognitiveReplanWorkSpecTemplateV1,
    RecordProgressionDecisionCommandV1,
    _VALIDATION_CLASSES, _REVIEW_CLASSES,
    ProgressionDecisionReductionV1,
    ProgressionDecisionConflictV1, derive_progression_branch,
)
from ge_nwp_coordinator._rw0_d1_workspace import PATHS
from test_post_execution_pure_owner_values import _sample, _seal, CLASS_BY_V
from test_rw0_c2_private_value_versioning_contract import _command_coordinates
from test_sqlite_rw0_c2_scope_admission import _command


def _basis() -> dict[str, object]:
    admission, _ = _command()
    admitted = admission.to_mapping()
    fact = admitted["expected_admission_fact"]
    act = admitted["verified_admission_act"]
    guard = {
        "schema_id": _GUARD_SCHEMA,
        "lineage_ref": fact["lineage_ref"], "scope_ref": fact["scope_ref"],
        "admission_fact_ref": fact["admission_fact_ref"],
        "admission_fact_digest": fact["admission_fact_digest"],
        "continuity_basis_ref": "continuity-A", "continuity_basis_digest": "11" * 32,
        "sole_active_basis_ref": "sole-A", "sole_active_basis_digest": "22" * 32,
        "no_foreign_claim": True, "acceptance_exhaustively_unclaimed": True,
    }
    guard["guard_digest"] = _self_digest(guard, "guard_digest")
    value = {
        "schema_id": _BASIS_SCHEMA, "basis_ref": "basis-A",
        "verified_admission_act": act, "scope_admission_fact": fact,
        "decision_current_snapshot": _sample("V27"),
        "proposal_family_projection": _sample("V22"),
        "proposal_evidence_currentness": _sample("V29"),
        "standing_policy_branch_matrix": _sample("V17"),
        "risk_lane_branch_matrix": _sample("V18"),
        "decision_time_authority_branch_matrix": _sample("V31"),
        "decision_time_global_stop_branch_matrix": _sample("V32"),
        "decision_time_source_effect_ceiling_branch_matrix": _sample("V33"),
        "historical_continuity_basis_ref": "continuity-A",
        "historical_continuity_basis_digest": "11" * 32,
        "historical_sole_active_basis_ref": "sole-A",
        "historical_sole_active_basis_digest": "22" * 32,
        "bootstrap_guard_evidence": guard,
        "recommendation_consistency_evaluation": _sample("V34"),
        "replan_proposal_safe_projection": None,
        "validation_disposition": _sample("V14"),
        "independent_review_disposition": _sample("V15"),
        "captured_at": "2029-01-01T00:00:00Z",
    }
    value["basis_digest"] = _self_digest(value, "basis_digest")
    return value


def test_exact_23_role_basis_and_measured_fixture_ceiling() -> None:
    value = _basis()
    assert _BASIS_FIELDS == (
        "schema_id", "basis_ref", "verified_admission_act", "scope_admission_fact",
        "decision_current_snapshot", "proposal_family_projection",
        "proposal_evidence_currentness", "standing_policy_branch_matrix",
        "risk_lane_branch_matrix", "decision_time_authority_branch_matrix",
        "decision_time_global_stop_branch_matrix",
        "decision_time_source_effect_ceiling_branch_matrix",
        "historical_continuity_basis_ref", "historical_continuity_basis_digest",
        "historical_sole_active_basis_ref", "historical_sole_active_basis_digest",
        "bootstrap_guard_evidence", "recommendation_consistency_evaluation",
        "replan_proposal_safe_projection", "validation_disposition",
        "independent_review_disposition", "captured_at", "basis_digest",
    )
    assert tuple(value) == _BASIS_FIELDS
    raw = _canonical(value)
    assert len(raw) == 43284 and _MAX_BASIS_BYTES == 49152
    assert DecisionBasisV2.from_json(raw).to_mapping() == value


def test_blocked_v1_predecessor_is_parseable_but_not_a_current_command_basis() -> None:
    from test_rw0_c2_progression_plan import _replan_case

    current = _basis()
    predecessor = {key: current[key] for key in _BASIS_FIELDS_V1}
    predecessor["schema_id"] = _BASIS_SCHEMA_V1
    predecessor["basis_digest"] = _self_digest(predecessor, "basis_digest")
    assert len(predecessor) == 21
    assert DecisionBasisV1.from_mapping(predecessor).to_mapping() == predecessor
    with pytest.raises(ValueError):
        DecisionBasisV2.from_mapping(predecessor)
    with pytest.raises(ValueError, match="invalid P1 command"):
        replace(_replan_case()[0], basis=DecisionBasisV1.from_mapping(predecessor))


def test_basis_v2_exact_recursive_types_and_disposition_snapshot_binding() -> None:
    class TextSubclass(str):
        pass

    value = _basis()
    value["basis_ref"] = TextSubclass("basis-A")
    with pytest.raises(ValueError):
        DecisionBasisV2.from_mapping(value)
    value = _basis()
    value["validation_disposition"]["attempt_number"] = True
    with pytest.raises(ValueError):
        DecisionBasisV2.from_mapping(value)
    for coordinate in ("program_version_ref", "semantic_attempt_ref",
                       "candidate_ref", "attempt_fence_digest",
                       "source_observation_schema_id", "source_observation_ref",
                       "source_observation_digest"):
        value = _basis()
        typed = value["validation_disposition"]
        typed[coordinate] = ("0" * 64 if coordinate.endswith("digest")
                             else "foreign-coordinate")
        value["validation_disposition"] = _seal("V14", typed)
        value["basis_digest"] = _self_digest(value, "basis_digest")
        with pytest.raises(ValueError):
            DecisionBasisV2.from_mapping(value)


def test_noncanonical_duplicate_unknown_and_bool_guard_are_rejected() -> None:
    value = _basis()
    raw = _canonical(value)
    with pytest.raises(ValueError):
        DecisionBasisV2.from_json(raw + b" ")
    with pytest.raises(ValueError):
        DecisionBasisV2.from_json(raw[:-1] + b',"basis_ref":"basis-A"}')
    changed = deepcopy(value)
    changed["extension"] = "forbidden"
    changed["basis_digest"] = _self_digest(changed, "basis_digest")
    with pytest.raises(ValueError):
        DecisionBasisV2.from_mapping(changed)
    changed = deepcopy(value)
    changed["bootstrap_guard_evidence"]["acceptance_exhaustively_unclaimed"] = 1
    changed["bootstrap_guard_evidence"]["guard_digest"] = _self_digest(
        changed["bootstrap_guard_evidence"], "guard_digest")
    changed["basis_digest"] = _self_digest(changed, "basis_digest")
    with pytest.raises(ValueError):
        DecisionBasisV2.from_mapping(changed)


def test_acceptance_eligibility_requires_both_historical_and_current_unclaimed_assertions() -> None:
    source = ArtificialDecisionGuardSourceV1(
        b"", b"", "2020-01-01T00:00:00Z", "2099-01-01T00:00:00Z",
        True, True, True, True, True, True, True,
    )
    historical_true = DecisionBasisV2.from_mapping(_basis())
    assert source.checked_acceptance_eligibility_for(historical_true) is None
    historical_unproven = _basis()
    guard = historical_unproven["bootstrap_guard_evidence"]
    guard["acceptance_exhaustively_unclaimed"] = None
    guard["guard_digest"] = _self_digest(guard, "guard_digest")
    historical_unproven["basis_digest"] = _self_digest(historical_unproven, "basis_digest")
    with pytest.raises(ValueError, match="P1 acceptance eligibility unavailable"):
        source.checked_acceptance_eligibility_for(
            DecisionBasisV2.from_mapping(historical_unproven))
    for current in (False, None):
        with pytest.raises(ValueError, match="P1 acceptance eligibility unavailable"):
            replace(source, acceptance_exhaustively_unclaimed=current).checked_acceptance_eligibility_for(
                historical_true)


def test_exact_nested_source_order_restored_without_widening() -> None:
    value = _basis()
    raw = _canonical(value)
    assert DecisionBasisV2.from_json(raw).digest == value["basis_digest"]
    changed = deepcopy(value)
    changed["proposal_family_projection"]["unknown"] = "x"
    changed["basis_digest"] = _self_digest(changed, "basis_digest")
    with pytest.raises(ValueError):
        DecisionBasisV2.from_mapping(changed)
    changed = deepcopy(value)
    changed["proposal_evidence_currentness"]["proposal_ref"] = "foreign"
    # Keep even a fabricated self-digest from bypassing the source profile.
    changed["basis_digest"] = _self_digest(changed, "basis_digest")
    with pytest.raises(ValueError):
        DecisionBasisV2.from_mapping(changed)


def test_preassignment_siblings_and_command_digest_fixed_vector() -> None:
    value = _command_coordinates()
    relation = AdmittedCommandRelationV1.from_mapping(value)
    assert relation.command_digest == (
        "a392abcc3f0981b4ac2aeab5d3869aea9f24ba7305b242563e3a41f402b716b1"
    )
    changed = deepcopy(value)
    changed["preassigned_acceptance_fact_ref"] = "0" * 64
    changed["relation_digest"] = _self_digest(changed, "relation_digest")
    with pytest.raises(ValueError):
        AdmittedCommandRelationV1.from_mapping(changed)


def test_basis_byte_limit_is_enforced_before_nested_validation() -> None:
    with pytest.raises(ValueError):
        DecisionBasisV2.from_json(b"{" + b" " * _MAX_BASIS_BYTES + b"}")


def _validation_for(cls: str):
    if cls == "accept":
        return CLASS_BY_V["V14"].from_mapping(_sample("V14"))
    source, result, repairability, reason = {
        "repair": ("failed", "repairable_failure", "repairable", "validation_failed_repairable"),
        "replan": ("failed", "replan_required", "same_attempt_insufficient", "validation_failed_replan_required"),
        "terminal": ("failed", "terminal_failure", "nonrepairable", "validation_failed_terminal"),
        "nonconclusive": ("failed", "unknown", "unknown", "validation_failed_unclassified"),
    }[cls]
    result_set = _sample("V38")
    result_set.update(source_outcome=source, source_reason_code=reason,
                      result=result, repairability=repairability, reason=reason)
    result_set = _seal("V38", result_set)
    CLASS_BY_V["V38"].from_mapping(result_set)
    disposition = _sample("V14")
    disposition.update(source_outcome=source, source_reason_code=reason,
                       result=result, repairability=repairability, reason=reason,
                       validation_result_set_ref=result_set["result_set_ref"],
                       validation_result_set_digest=result_set["result_set_digest"])
    return CLASS_BY_V["V14"].from_mapping(_seal("V14", disposition))


def _replan_proposal(basis: dict[str, object]) -> CognitiveReplanProposalV1:
    snapshot = basis["decision_current_snapshot"]
    assert type(snapshot) is dict
    template = dict(
        schema_id="governed-execution.nwp-rw0-c2-cognitive-replan-work-spec-template.v1",
        program_ref=snapshot["program_ref"], work_item_ref=snapshot["work_item_ref"],
        repository_ref="repository.execution-substrate",
        base_git_object_format="sha1", base_git_oid="2" * 40,
        authorized_paths=list(PATHS), objective="Artificial replan only.",
        requirements=["Stay inside proof scope."], exclusions=["No network."],
        validation_requirement_ref="validation.replan-A",
        review_requirement_ref="review.replan-A",
        privacy_classification="private_work_spec",
    )
    template["template_digest"] = _self_digest(template, "template_digest")
    return CognitiveReplanProposalV1(
        "source-intent.replan-A", "ab" * 32,
        CognitiveReplanWorkSpecTemplateV1.from_mapping(template),
    )


@pytest.mark.parametrize("normal,branch", [
    ("accept", "candidate_acceptance"),
    ("repair", "candidate_repair"),
    ("replan", "attempt_selecting_replan"),
    ("terminal", "program_terminal_reject"),
    ("nonconclusive", "post_execution_program_block"),
])
def test_five_branches_are_derived_from_typed_dispositions(normal: str, branch: str) -> None:
    basis = _basis()
    model = basis["recommendation_consistency_evaluation"]
    assert type(model) is dict
    model["authoritative_branch"] = branch
    if branch != "candidate_acceptance":
        model["result"] = "inconsistent"
        model["reason"] = "mapped_branch_differs_from_authoritative_branch"
    basis["recommendation_consistency_evaluation"] = _seal("V34", model)
    proposal = _replan_proposal(basis) if normal == "replan" else None
    if proposal is not None:
        basis["replan_proposal_safe_projection"] = proposal.safe_projection()
    basis["validation_disposition"] = _validation_for(normal).to_mapping()
    basis["basis_digest"] = _self_digest(basis, "basis_digest")
    validated_basis = DecisionBasisV2.from_mapping(basis)
    outcome = derive_progression_branch(
        validated_basis, _validation_for(normal),
        CLASS_BY_V["V15"].from_mapping(_sample("V15")),
        expected_branch=branch, replan_proposal=proposal,
    )
    assert type(outcome) is ProgressionDecisionReductionV1
    assert outcome.branch == branch
    assert (basis["replan_proposal_safe_projection"] is not None) == (normal == "replan")


def test_replan_is_neither_forced_nor_vetoed_by_model_or_extra_proposal() -> None:
    basis = DecisionBasisV2.from_mapping(_basis())
    result = derive_progression_branch(
        basis, _validation_for("accept"),
        CLASS_BY_V["V15"].from_mapping(_sample("V15")),
        expected_branch="attempt_selecting_replan", replan_proposal=None,
    )
    assert type(result) is ProgressionDecisionConflictV1
    assert result.reason_code == "expected_branch_mismatch"
    result = derive_progression_branch(
        basis, _validation_for("accept"),
        CLASS_BY_V["V15"].from_mapping(_sample("V15")),
        expected_branch=None, replan_proposal=_replan_proposal(_basis()),
    )
    assert type(result) is ProgressionDecisionConflictV1
    assert result.reason_code == "required_fact_invalid"


def test_expected_branch_requires_exact_builtin_str_before_advisory_comparison() -> None:
    from test_rw0_c2_progression_plan import _replan_case

    command = _replan_case()[0]
    assert type(command) is RecordProgressionDecisionCommandV1
    assert type(replace(command, expected_branch=None).expected_branch) is type(None)
    assert replace(command, expected_branch="attempt_selecting_replan").expected_branch == (
        "attempt_selecting_replan")
    mismatch = replace(command, expected_branch="candidate_acceptance")
    result = derive_progression_branch(
        mismatch.basis, *mismatch.basis.typed_dispositions(),
        expected_branch=mismatch.expected_branch,
        replan_proposal=mismatch.replan_proposal)
    assert type(result) is ProgressionDecisionConflictV1
    assert result.reason_code == "expected_branch_mismatch"

    equality_calls = []
    class EqualBranch(str):
        def __eq__(self, other):
            equality_calls.append(other)
            return True

    class BranchEnum(Enum):
        REPLAN = "attempt_selecting_replan"

    for invalid in (EqualBranch("foreign"), True, 1, b"attempt_selecting_replan",
                    BranchEnum.REPLAN, object()):
        with pytest.raises(ValueError, match="invalid P1 command"):
            replace(command, expected_branch=invalid)
    assert equality_calls == []


def test_candidate_reason_helper_covers_finite_disposition_vocabulary_and_precedence() -> None:
    validation_cases = (
        (("passed", "passed", "not_applicable", "validation_passed"),
         "candidate_evidence_conclusively_accepted"),
        (("failed", "repairable_failure", "repairable", "validation_failed_repairable"),
         "candidate_evidence_requires_repair"),
        (("failed", "replan_required", "same_attempt_insufficient", "validation_failed_replan_required"),
         "candidate_evidence_requires_replan"),
        (("failed", "terminal_failure", "nonrepairable", "validation_failed_terminal"),
         "candidate_evidence_terminally_rejected"),
        (("failed", "unknown", "unknown", "validation_failed_unclassified"),
         "candidate_evidence_nonconclusive"),
        (("inconclusive", "unknown", "unknown", "validation_inconclusive"),
         "candidate_evidence_nonconclusive"),
        (("not_run", "not_run", "not_applicable", "validation_not_run"),
         "candidate_evidence_nonconclusive"),
    )
    review_cases = (
        (("separate", "passed", "passed", "review_passed"),
         "candidate_evidence_conclusively_accepted"),
        (("separate", "failed", "repair_required", "review_failed_repair_required"),
         "candidate_evidence_requires_repair"),
        (("separate", "failed", "replan_required", "review_failed_replan_required"),
         "candidate_evidence_requires_replan"),
        (("separate", "failed", "terminal_reject", "review_failed_terminal_reject"),
         "candidate_evidence_terminally_rejected"),
        (("separate", "failed", "unknown", "review_failed_unclassified"),
         "candidate_evidence_nonconclusive"),
        (("separate", "inconclusive", "unknown", "review_inconclusive"),
         "candidate_evidence_nonconclusive"),
        (("not_separate", "passed", "basis_conflict", "review_not_operationally_separate"),
         "basis_identity_lineage_profile_provenance_conflict"),
        (("unknown", "passed", "unknown", "reviewer_separation_unknown"),
         "candidate_evidence_nonconclusive"),
        (("conflict", "passed", "basis_conflict", "reviewer_separation_conflict"),
         "basis_identity_lineage_profile_provenance_conflict"),
    )
    assert {pair for pair, _ in validation_cases} == set(_VALIDATION_CLASSES)
    assert {pair for pair, _ in review_cases} == set(_REVIEW_CLASSES)
    accept_validation = _validation_for("accept")
    accept_review = CLASS_BY_V["V15"].from_mapping(_sample("V15"))
    def validation_for(pair):
        value = _sample("V14")
        value.update(zip(("source_outcome", "result", "repairability", "reason"), pair))
        value["source_reason_code"] = pair[3]
        return CLASS_BY_V["V14"].from_mapping(_seal("V14", value))
    def review_for(pair):
        value = _sample("V15")
        value.update(zip(("separation_status", "source_outcome", "result", "reason"), pair))
        value["source_reason_code"] = pair[3]
        return CLASS_BY_V["V15"].from_mapping(_seal("V15", value))
    for pair, expected in validation_cases:
        assert derive_candidate_evidence_reason(validation_for(pair), accept_review) == expected
    for pair, expected in review_cases:
        result = derive_candidate_evidence_reason(accept_validation, review_for(pair))
        assert (result.reason_code if type(result) is ProgressionDecisionConflictV1
                else result) == expected
    repair = validation_for(validation_cases[1][0])
    replan = review_for(review_cases[2][0])
    terminal = review_for(review_cases[3][0])
    nonconclusive = validation_for(validation_cases[4][0])
    assert derive_candidate_evidence_reason(repair, replan) == "candidate_evidence_requires_replan"
    assert derive_candidate_evidence_reason(repair, terminal) == "candidate_evidence_terminally_rejected"
    assert derive_candidate_evidence_reason(nonconclusive, terminal) == "candidate_evidence_nonconclusive"
    assert derive_candidate_evidence_reason(object(), accept_review).reason_code == "required_fact_invalid"
