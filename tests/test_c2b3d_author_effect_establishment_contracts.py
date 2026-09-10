from __future__ import annotations

from dataclasses import replace
import runpy
from pathlib import Path

import pytest

from ge_nwp_coordinator import (
    _development_author_effect_establishment_contracts as contracts,
)
from ge_nwp_coordinator import _development_program_row_values as program_rows
from ge_nwp_coordinator._development_author_effect_establishment_contracts import (
    DevelopmentAuthorEffectEstablishmentCommandV1,
    DevelopmentEffectAuthorizationSafeBindingV1,
    DevelopmentReviewRequirementEvidenceV1,
    DevelopmentValidationRequirementEvidenceV1,
    _development_author_effect_establishment_write_plan,
)
from ge_nwp_coordinator._sqlite_development_author_effect_establishment import (
    _reduce_development_author_effect_establishment_command,
)
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1,
    CeilingsV1,
    DeliveryEnvelopeV1,
    EffectFenceV1,
    WorkSpecV1,
    WorkerCommandV1,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError


ROOT = Path(__file__).resolve().parents[1]
VECTOR = runpy.run_path(str(ROOT / "tests/test_c2b3c_author_effect_contract.py"))[
    "EXPECTED_FAMILY_GOLDEN_VECTOR"
]


def golden_inputs() -> tuple[WorkSpecV1, dict[str, object]]:
    values = VECTOR["inputs"]
    basis = values["committed_vs1b_genesis_basis"]
    refs = values["preassigned_author_effect_refs"]
    authority = values["standing_and_subordinate_authority"]
    requirements = values["requirement_evidence"]
    stop = values["coding_global_stop"]
    work_spec = WorkSpecV1.create(
        work_spec_ref=basis["work_spec_ref"],
        program_ref=basis["program_ref"],
        program_version_ref=basis["program_version_ref"],
        accepted_intent_revision_ref=basis["accepted_intent_revision_ref"],
        work_item_ref=basis["work_item_ref"],
        work_item_revision_ref=basis["work_item_revision_ref"],
        repository_ref=basis["repository_ref"],
        base_git_oid=basis["base_git_oid"],
        authorized_paths=list(basis["authorized_paths"]),
        objective="PRIVATE OBJECTIVE SENTINEL",
        requirements=["PRIVATE REQUIREMENT SENTINEL"],
        exclusions=["PRIVATE EXCLUSION SENTINEL"],
        validation_requirement_ref=basis["validation_requirement_ref"],
        review_requirement_ref=basis["review_requirement_ref"],
    )
    attempt = AttemptFenceV1.from_mapping(
        VECTOR["canonical_values"]["attempt_fence"]["complete_mapping"]
    )
    validation = DevelopmentValidationRequirementEvidenceV1(
        **requirements["validation"]
    )
    review = DevelopmentReviewRequirementEvidenceV1(**requirements["review"])
    binding_mapping = VECTOR["canonical_values"]["effect_authorization_safe_binding"][
        "complete_mapping"
    ]
    binding = DevelopmentEffectAuthorizationSafeBindingV1(
        **{
            **binding_mapping,
            "effect_ceilings": CeilingsV1.from_mapping(
                binding_mapping["effect_ceilings"]
            ),
        }
    )
    ingress: dict[str, object] = {
        "mutation_ref": refs["mutation_ref"],
        "program_ref": basis["program_ref"],
        "program_version_ref": basis["program_version_ref"],
        "program_version_number": basis["program_version_number"],
        "accepted_intent_revision_ref": basis["accepted_intent_revision_ref"],
        "work_item_ref": basis["work_item_ref"],
        "work_item_revision_ref": basis["work_item_revision_ref"],
        "basis_decision_ref": basis["basis_decision_ref"],
        "basis_decision_digest": basis["basis_decision_digest"],
        "semantic_attempt_ref": basis["semantic_attempt_ref"],
        "candidate_ref": basis["candidate_ref"],
        "attempt_number": basis["attempt_number"],
        "attempt_fence_ref": refs["attempt_fence_ref"],
        "effect_intent_ref": refs["effect_intent_ref"],
        "effect_fence_ref": refs["effect_fence_ref"],
        "command_ref": refs["command_ref"],
        "authority_evaluation_ref": refs["authority_evaluation_ref"],
        "delivery_attempt_ref": refs["delivery_attempt_ref"],
        "adapter_safe_correlation_ref": refs["adapter_safe_correlation_ref"],
        "coding_global_stop_ref": stop["global_stop_ref"],
        "coding_global_stop_version": stop["global_stop_version"],
        "work_spec": work_spec,
        "validation_requirement_evidence": validation,
        "review_requirement_evidence": review,
        "attempt_fence": attempt,
        "effect_authorization_safe_binding": binding,
    }
    assert authority["effect_authorization_ref"] == binding.effect_authorization_ref
    return work_spec, ingress


def golden_command() -> DevelopmentAuthorEffectEstablishmentCommandV1:
    values = VECTOR["canonical_values"]
    projection_mapping = values["work_spec_safe_projection"]["complete_mapping"]
    projection = program_rows._persisted_safe_projection_from_fields(
        work_spec_ref=projection_mapping["work_spec_ref"],
        program_ref=projection_mapping["program_ref"],
        program_version_ref=projection_mapping["program_version_ref"],
        accepted_intent_revision_ref=projection_mapping["accepted_intent_revision_ref"],
        work_item_ref=projection_mapping["work_item_ref"],
        work_item_revision_ref=projection_mapping["work_item_revision_ref"],
        repository_ref=projection_mapping["repository_ref"],
        base_git_object_format=projection_mapping["base_git_object_format"],
        base_git_oid=projection_mapping["base_git_oid"],
        authorized_paths=projection_mapping["authorized_paths"],
        validation_requirement_ref=projection_mapping["validation_requirement_ref"],
        review_requirement_ref=projection_mapping["review_requirement_ref"],
        privacy_classification=projection_mapping["privacy_classification"],
        work_spec_digest=projection_mapping["work_spec_digest"],
        persisted_safe_projection_digest=projection_mapping["safe_projection_digest"],
    )
    binding_mapping = values["effect_authorization_safe_binding"]["complete_mapping"]
    command_mapping = dict(values["safe_mutation_command"]["complete_mapping"])
    command_mapping.update(
        work_spec_safe_projection=projection,
        validation_requirement_evidence=DevelopmentValidationRequirementEvidenceV1(
            **values["validation_requirement_evidence"]["complete_mapping"]
        ),
        review_requirement_evidence=DevelopmentReviewRequirementEvidenceV1(
            **values["review_requirement_evidence"]["complete_mapping"]
        ),
        attempt_fence=AttemptFenceV1.from_mapping(command_mapping["attempt_fence"]),
        effect_authorization_safe_binding=(
            DevelopmentEffectAuthorizationSafeBindingV1(
                **{
                    **binding_mapping,
                    "effect_ceilings": CeilingsV1.from_mapping(
                        binding_mapping["effect_ceilings"]
                    ),
                }
            )
        ),
        worker_command=WorkerCommandV1.from_mapping(command_mapping["worker_command"]),
        effect_fence=EffectFenceV1.from_mapping(command_mapping["effect_fence"]),
        delivery_envelope=DeliveryEnvelopeV1.from_mapping(
            command_mapping["delivery_envelope"]
        ),
    )
    return DevelopmentAuthorEffectEstablishmentCommandV1(**command_mapping)


def test_golden_vector_command_plan_graph_receipt_and_result_are_exact() -> None:
    command = golden_command()
    expected_command = VECTOR["canonical_values"]["safe_mutation_command"]
    assert command.identity_mapping() == expected_command["canonical_identity_mapping"]
    assert command.command_digest == expected_command["digest"]

    plan = _development_author_effect_establishment_write_plan(
        command, VECTOR["transaction_timestamp"]
    )
    actual_rows = {
        "semantic_attempt": tuple(plan.semantic_attempt._values),
        "attempt_fence": contracts._attempt_fence_parameters(
            plan.attempt_fence.attempt_fence,
            plan.attempt_fence.recorded_at,
        ),
        "author_effect_intent": tuple(plan.effect_intent._values),
        "author_effect_fence": contracts._effect_fence_parameters(
            plan.effect_fence.effect_fence,
            plan.effect_fence.recorded_at,
        ),
        "author_command": contracts._author_command_parameters(
            plan.author_command.worker_command,
            plan.author_command.recorded_at,
        ),
        "authority_evaluation": tuple(plan.authority_evaluation._values),
        "effect_head_postimage": tuple(plan.effect_head._values),
        "initial_delivery_attempt": (
            tuple(plan.delivery_attempt.delivery_envelope.to_mapping().values())
            + tuple(plan.delivery_attempt._values[1:])
        ),
        "delivery_head_postimage": tuple(plan.delivery_head._values),
    }
    assert tuple(actual_rows) == tuple(VECTOR["persisted_postimages"])[:-1]
    for name, actual in actual_rows.items():
        assert actual == tuple(VECTOR["persisted_postimages"][name].values())
    assert tuple(plan.mutation_receipt._values[:19]) == tuple(
        VECTOR["receipt_envelope"]["complete_mapping"].values()
    )
    assert tuple(
        (entry.role, entry.ordinal, entry.record_ref, entry.record_digest)
        for entry in plan.graph_entries
    ) == tuple(
        (entry["role"], entry["ordinal"], entry["record_ref"], entry["record_digest"])
        for entry in VECTOR["graph_entries"]
    )
    assert (
        plan.planned_result.identity_mapping()
        == VECTOR["fresh_committed_result"]["mapping"]
    )
    assert (
        plan.planned_result.computed_digest()
        == VECTOR["fresh_committed_result"]["digest"]
    )


@pytest.mark.parametrize(
    "field,bad_value",
    (
        ("program_version_number", True),
        ("attempt_number", 2),
        ("coding_global_stop_version", False),
        ("capsule_profile_ref", "capsule-profile.changed-v1"),
        ("redaction_profile_ref", "redaction.changed-v1"),
    ),
)
def test_exact_types_cardinality_profiles_and_digest_identity_fail_closed(
    field: str,
    bad_value: object,
) -> None:
    command = golden_command()
    with pytest.raises(SQLiteMutationStoreError):
        replace(command, **{field: bad_value})


def test_requirement_authority_and_command_digest_mutants_fail_closed() -> None:
    command = golden_command()
    validation = command.validation_requirement_evidence
    assert type(validation) is DevelopmentValidationRequirementEvidenceV1
    with pytest.raises(SQLiteMutationStoreError):
        replace(validation, requirement_digest="8" * 64)

    binding = command.effect_authorization_safe_binding
    assert type(binding) is DevelopmentEffectAuthorizationSafeBindingV1
    with pytest.raises(SQLiteMutationStoreError):
        replace(binding, safe_binding_digest="8" * 64)

    assert type(command) is DevelopmentAuthorEffectEstablishmentCommandV1
    with pytest.raises(SQLiteMutationStoreError):
        replace(command, command_digest="8" * 64)
