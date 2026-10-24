"""Cross-owner, currentness, privacy, and branch relation tests."""

import ast
from copy import deepcopy
import hashlib
from pathlib import Path

import pytest

import ge_nwp_coordinator._finite_backlog_risk_source_adapter as adapter
import ge_nwp_coordinator._post_execution_evidence_values as evidence
import ge_nwp_coordinator._post_execution_policy_values as policy
import ge_nwp_coordinator._rw0_c_decision_input_values as decision
import ge_nwp_coordinator._section41_post_execution_proposal_family_projection as projection
import ge_nwp_coordinator._section41_post_execution_role_resolution as resolution
from ge_nwp_coordinator._cognitive_proposal_row_values import (
    DevelopmentModelProposalEvidenceBindingRowValue,
    DevelopmentModelProposalRowValue,
    DevelopmentModelSourceInvocationRowValue,
    DevelopmentPrivateProposalArtifactBindingRowValue,
)
from ge_nwp_coordinator._development_author_effect_establishment_contracts import (
    DevelopmentReviewRequirementEvidenceV1,
    DevelopmentValidationRequirementEvidenceV1,
)
from ge_nwp_coordinator._rw0_c1_mutation_contracts import (
    RW0C1OperandIdentity,
    admission_graph_digest,
    build_row,
    membership_digest,
    operand_set_digest,
    relation_digest,
    relation_set_digest,
    relation_specifications,
    section41_owner_family_graph_digest,
)
from ge_nwp_coordinator._rw0_c1_row_values import (
    MEMBERSHIP_COLUMNS,
    RELATION_COLUMNS,
    rw0_c1_row_value_from_tuple,
)
from ge_nwp_coordinator._rw0_c1_semantic_values import (
    RW0C1MemberLocatorV1,
    RW0C1OwnerRowLocatorV1,
    RW0C1Section41PostExecutionProposalFamilyMemberV1,
    RW0C1WireProcessResultClassificationBindingV1,
    RW0C1WireWorkerResultBindingV1,
)
from ge_nwp_coordinator._rw0_phase_entry_semantic_values import (
    RW0AuthorityVerificationObservationV1,
    RW0EffectHostQualificationV1,
)
from ge_nwp_coordinator._sqlite_rw0_c1 import (
    _located_owner_operand,
    _section41_owner_family_matches,
)
from ge_nwp_coordinator._sqlite_rw0_c1_readers import RW0C1OwnerRowSnapshot
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1,
    CandidateCapsuleManifestV1,
    EffectFenceV1,
    WorkerExecutionValueError,
    WorkerObservationV1,
)
from ge_nwp_coordinator.global_stop import GlobalStopState
from c2a_contract_support import _effect_fence_for_vector, _full_record, _sealed_record
from test_rw0_b1_vectors import mapping_for
from test_post_execution_pure_owner_values import (
    BRANCHES,
    CLASS_BY_V,
    CURRENTNESS_COMPONENTS,
    ROLES,
    _TEST_RECORDS,
    _canonical,
    _ordered_fixture,
    _sample,
    _seal,
)


ROOT = Path(__file__).resolve().parents[1]


def _section41_owner_inputs() -> dict[str, object]:
    source = DevelopmentModelSourceInvocationRowValue(
        **_TEST_RECORDS["golden.owner.source-invocation"]
    )
    artifact = DevelopmentPrivateProposalArtifactBindingRowValue(
        **_TEST_RECORDS["golden.owner.artifact-binding"]
    )
    proposal_row = DevelopmentModelProposalRowValue(
        **_TEST_RECORDS["golden.owner.proposal"]
    )
    evidence_rows = tuple(
        DevelopmentModelProposalEvidenceBindingRowValue(
            **_TEST_RECORDS[
                f"golden.owner.proposal-evidence-row.{rank:02d}.{role}"
            ]
        )
        for rank, role in enumerate(ROLES, 5)
    )
    owner_rows = (source, artifact, proposal_row, *evidence_rows)
    reader_rows = tuple(
        tuple(getattr(row, name) for name in type(row)._COLUMNS)
        for row in owner_rows
    )
    owner_locators = tuple(
        RW0C1OwnerRowLocatorV1(**item)
        for item in _TEST_RECORDS["golden.owner.owner-family-graph"]["owners"]
    )
    value_mapping = dict(_TEST_RECORDS["golden.owner.rank15.value"])
    value_mapping.pop("schema_id")
    rank15_value = RW0C1Section41PostExecutionProposalFamilyMemberV1(
        **value_mapping
    )
    relation_mapping = _TEST_RECORDS["golden.owner.rank15.relation"]
    rank15_relation = rw0_c1_row_value_from_tuple(
        "rw0_relation_bindings",
        tuple(relation_mapping[name] for name in RELATION_COLUMNS),
    )
    graph_fields = (
        "schema_id", "phase_basis_ref", "phase_basis_digest", "membership_ref",
        "kind_rank", "value_ref", "value_digest", "value_schema_id",
        "scope_binding_digest", "relation_set_digest", "relations",
        "admitted_by_mutation_ref", "admitted_at",
    )
    graph_source = _TEST_RECORDS["golden.owner.rank15.graph"]
    rank15_graph = {name: deepcopy(graph_source[name]) for name in graph_fields}
    membership_mapping = dict(_TEST_RECORDS["golden.owner.rank15.membership"])
    membership_identity = {
        name: membership_mapping[name]
        for name in (
            "schema_id", "membership_ref", "phase_basis_ref", "phase_basis_digest",
            "kind_rank", "value_ref", "value_digest", "value_schema_id",
            "scope_binding_digest", "relation_set_digest", "admitted_by_mutation_ref",
            "admitted_at", "admission_graph_digest",
        )
    }
    membership_mapping["membership_digest"] = membership_digest(membership_identity)
    rank15_membership = rw0_c1_row_value_from_tuple(
        "rw0_evidence_memberships",
        tuple(membership_mapping[name] for name in MEMBERSHIP_COLUMNS),
    )
    context = CLASS_BY_V["V02"].from_mapping(_sample("V02"))
    projected = projection.section41_post_execution_proposal_family_projection(
        _sample("V22"),
        input_context=context,
        source_invocation_row=source,
        artifact_binding_row=artifact,
        proposal_row=proposal_row,
        evidence_rows=evidence_rows,
        private_reader_tuples=reader_rows,
        owner_locators=owner_locators,
        rank15_value=rank15_value,
        rank15_relation_row=rank15_relation,
        rank15_admission_graph=rank15_graph,
        rank15_membership_row=rank15_membership,
        admitted_by_mutation_ref=rank15_graph["admitted_by_mutation_ref"],
    )
    return {
        "source": source,
        "artifact": artifact,
        "proposal_row": proposal_row,
        "evidence_rows": evidence_rows,
        "reader_rows": reader_rows,
        "owner_locators": owner_locators,
        "rank15_value": rank15_value,
        "rank15_relation": rank15_relation,
        "rank15_graph": rank15_graph,
        "rank15_membership": rank15_membership,
        "context": context,
        "projection": projected,
    }


def _c1_membership_row(record_id: str) -> object:
    mapping = deepcopy(_TEST_RECORDS[record_id])
    if "membership_digest" not in mapping:
        identity = {
            name: mapping[name]
            for name in (
                "schema_id", "membership_ref", "phase_basis_ref", "phase_basis_digest",
                "kind_rank", "value_ref", "value_digest", "value_schema_id",
                "scope_binding_digest", "relation_set_digest", "admitted_by_mutation_ref",
                "admitted_at", "admission_graph_digest",
            )
        }
        mapping["membership_digest"] = membership_digest(identity)
    return rw0_c1_row_value_from_tuple(
        "rw0_evidence_memberships",
        tuple(mapping[name] for name in MEMBERSHIP_COLUMNS),
    )


def _c1_relation_row(record_id: str) -> object:
    mapping = _TEST_RECORDS[record_id]
    return rw0_c1_row_value_from_tuple(
        "rw0_relation_bindings",
        tuple(mapping[name] for name in RELATION_COLUMNS),
    )


def _reviewer_separation_owner_inputs() -> dict[str, object]:
    author_value_mapping = deepcopy(_TEST_RECORDS["golden.owner.author-rank13.value"])
    author_value_mapping.pop("schema_id")
    author_value_mapping.pop("wire_profile_ref")
    author_value_mapping.pop("wire_profile_digest")
    author_value_mapping["observation_memberships"] = tuple(
        RW0C1MemberLocatorV1(**item)
        for item in author_value_mapping["observation_memberships"]
    )
    return {
        "review_membership_row": _c1_membership_row(
            "golden.owner.review-rank12.membership"
        ),
        "review_observation": WorkerObservationV1.from_mapping(
            deepcopy(_TEST_RECORDS["golden.owner.review-observation"])
        ),
        "review_relation_row": _c1_relation_row(
            "golden.owner.review-rank12.relation"
        ),
        "author_result_membership_row": _c1_membership_row(
            "golden.owner.author-rank13.membership"
        ),
        "author_result_value": RW0C1WireWorkerResultBindingV1(
            **author_value_mapping
        ),
        "author_result_relation_row": _c1_relation_row(
            "golden.owner.author-rank13.relation"
        ),
        "author_observation_membership_rows": tuple(
            _c1_membership_row(
                f"golden.owner.author-rank12.{ordinal:03d}.membership"
            )
            for ordinal in range(3)
        ),
        "author_observations": tuple(
            WorkerObservationV1.from_mapping(
                deepcopy(_TEST_RECORDS[f"golden.owner.author-observation.{ordinal:03d}"])
            )
            for ordinal in range(3)
        ),
        "author_observation_relation_rows": tuple(
            _c1_relation_row(
                f"golden.owner.author-rank12.{ordinal:03d}.relation"
            )
            for ordinal in range(3)
        ),
        "candidate_capsule": CandidateCapsuleManifestV1.from_mapping(
            deepcopy(_sample("V11", 0)["typed_canonical_value"])
        ),
        "support_set": CLASS_BY_V["V13"].from_mapping(
            _ordered_fixture(
                "V13",
                deepcopy(_TEST_RECORDS["golden.V13.reviewer-separation.support-set"]),
            )
        ),
    }


def _reviewer_separation_action(value: object) -> object:
    return evidence.evaluate_post_execution_reviewer_separation(
        value,
        **_reviewer_separation_owner_inputs(),
    )


def _resealed_review_owner_rows(
    prefix: str, value: object, *, kind_rank: int,
) -> tuple[object, object]:
    """Rebuild a fixture's C1 proof chain after changing its typed value."""
    membership = deepcopy(_TEST_RECORDS[prefix + ".membership"])
    relation = deepcopy(_TEST_RECORDS[prefix + ".relation"])
    graph = deepcopy(_TEST_RECORDS[prefix + ".graph"])
    operands = tuple(
        RW0C1OperandIdentity(**item)
        for item in _TEST_RECORDS[prefix + ".operands"]
    )
    value_ref = value.observation_ref if kind_rank == 12 else value.value_ref
    value_digest = value.observation_digest if kind_rank == 12 else value.value_digest
    value_schema_id = value.schema_id
    new_relation_digest, operand_digest = relation_digest(
        phase_basis_ref=relation["phase_basis_ref"],
        phase_basis_digest=relation["phase_basis_digest"],
        relation_ref=relation["relation_ref"],
        subject_type=relation["subject_type"],
        subject_membership_ref=relation["subject_membership_ref"],
        subject_kind_rank=kind_rank,
        subject_value_ref=value_ref,
        subject_value_digest=value_digest,
        subject_value_schema_id=value_schema_id,
        specification=relation_specifications(kind_rank=kind_rank)[0],
        evaluated_at=relation["evaluated_at"],
        operands=operands,
    )
    new_relation_set_digest = relation_set_digest(
        phase_basis_ref=membership["phase_basis_ref"],
        subject_type="evidence_membership",
        subject_ref=membership["membership_ref"],
        relations=((0, relation["relation_ref"], new_relation_digest),),
    )
    graph["value_digest"] = value_digest
    graph["relation_set_digest"] = new_relation_set_digest
    graph["relations"][0]["relation_digest"] = new_relation_digest
    graph["relations"][0]["operand_set_digest"] = operand_digest
    membership["value_digest"] = value_digest
    membership["relation_set_digest"] = new_relation_set_digest
    membership["admission_graph_digest"] = admission_graph_digest(graph)
    member_row = build_row(
        "rw0_evidence_memberships",
        {key: membership[key] for key in MEMBERSHIP_COLUMNS if key != "membership_digest"},
    )
    relation["subject_membership_digest"] = member_row.to_mapping()["membership_digest"]
    relation["subject_value_digest"] = value_digest
    relation["relation_digest"] = new_relation_digest
    relation["operand_set_digest"] = operand_digest
    relation_row = build_row(
        "rw0_relation_bindings",
        {key: relation[key] for key in RELATION_COLUMNS if key != "relation_row_digest"},
    )
    return member_row, relation_row


def _rebound_author_result(inputs: dict[str, object], *, candidate_ref: str | None = None) -> None:
    old_value = inputs["author_result_value"]
    mapping = old_value.to_mapping()
    for field in ("schema_id", "wire_profile_ref", "wire_profile_digest", "value_digest"):
        mapping.pop(field)
    mapping["candidate_ref"] = candidate_ref or mapping["candidate_ref"]
    mapping["observation_memberships"] = tuple(
        RW0C1MemberLocatorV1(
            role=f"worker_observation:{ordinal:03d}", kind_rank=12,
            membership_ref=member.to_mapping()["membership_ref"],
            membership_digest=member.to_mapping()["membership_digest"],
            value_ref=observation.observation_ref,
            value_digest=observation.observation_digest,
        )
        for ordinal, (member, observation) in enumerate(zip(
            inputs["author_observation_membership_rows"],
            inputs["author_observations"], strict=True,
        ))
    )
    value = RW0C1WireWorkerResultBindingV1(**mapping)
    inputs["author_result_value"] = value
    member, relation = _resealed_review_owner_rows(
        "golden.owner.author-rank13", value, kind_rank=13,
    )
    inputs["author_result_membership_row"] = member
    inputs["author_result_relation_row"] = relation
    _refresh_reviewer_support_set(inputs)


def _refresh_reviewer_support_set(inputs: dict[str, object]) -> None:
    mapping = inputs["support_set"].to_mapping()
    mapping["entries"][0]["source_digest"] = (
        inputs["review_membership_row"].to_mapping()["membership_digest"]
    )
    mapping["entries"][1]["source_digest"] = (
        inputs["author_result_membership_row"].to_mapping()["membership_digest"]
    )
    inputs["support_set"] = CLASS_BY_V["V13"].from_mapping(
        _ordered_fixture("V13", _seal("V13", mapping))
    )


def _two_observation_reviewer_owner() -> tuple[dict[str, object], dict[str, object]]:
    inputs = _reviewer_separation_owner_inputs()
    inputs["author_observations"] = (
        inputs["author_observations"][0], inputs["author_observations"][2],
    )
    inputs["author_observation_membership_rows"] = (
        inputs["author_observation_membership_rows"][0],
        inputs["author_observation_membership_rows"][2],
    )
    inputs["author_observation_relation_rows"] = (
        inputs["author_observation_relation_rows"][0],
        inputs["author_observation_relation_rows"][2],
    )
    _rebound_author_result(inputs)
    return inputs, _reviewer_value_for_owner(inputs)


def _reviewer_value_for_owner(inputs: dict[str, object]) -> dict[str, object]:
    value = _sample("V40")
    review = inputs["review_observation"]
    review_member = inputs["review_membership_row"].to_mapping()
    review_relation = inputs["review_relation_row"].to_mapping()
    author_value = inputs["author_result_value"]
    author_member = inputs["author_result_membership_row"].to_mapping()
    author_relation = inputs["author_result_relation_row"].to_mapping()
    value.update(
        review_value_digest=review.observation_digest,
        review_membership_digest=review_member["membership_digest"],
        review_relation_digest=review_relation["relation_digest"],
        review_relation_row_digest=review_relation["relation_row_digest"],
        author_result_value_digest=author_value.value_digest,
        author_result_membership_digest=author_member["membership_digest"],
        author_result_relation_digest=author_relation["relation_digest"],
        author_result_relation_row_digest=author_relation["relation_row_digest"],
        support_set_ref=inputs["support_set"].support_set_ref,
        support_set_digest=inputs["support_set"].support_set_digest,
    )
    locators = []
    for ordinal, (member, observation, relation) in enumerate(zip(
        inputs["author_observation_membership_rows"],
        inputs["author_observations"],
        inputs["author_observation_relation_rows"], strict=True,
    )):
        row = member.to_mapping()
        relation_row = relation.to_mapping()
        item = deepcopy(_sample("V40")["author_observation_locators"][0])
        item.update(
            ordinal=ordinal,
            membership_ref=row["membership_ref"],
            membership_digest=row["membership_digest"],
            value_ref=observation.observation_ref,
            value_digest=observation.observation_digest,
            relation_ref=relation_row["relation_ref"],
            relation_digest=relation_row["relation_digest"],
            relation_row_digest=relation_row["relation_row_digest"],
            observation_kind=observation.observation_kind,
        )
        locators.append(item)
    value["author_observation_locators"] = locators
    return _seal("V40", value)


def _resealed_worker_observation(observation: WorkerObservationV1, **changes: object) -> WorkerObservationV1:
    mapping = observation.to_mapping()
    mapping.update(changes)
    mapping.pop("observation_digest")
    return WorkerObservationV1.from_mapping(_sealed_record("WorkerObservationV1", mapping))


def test_v40_two_observation_parent_capture_owner_relation_passes() -> None:
    inputs, expected = _two_observation_reviewer_owner()
    assert tuple(item.observation_kind for item in inputs["author_observations"]) == (
        "worker_started", "worker_completed",
    )
    completed_mapping = inputs["author_observations"][1].to_mapping()
    assert "candidate_ref" not in completed_mapping
    assert "capsule_manifest_ref" not in completed_mapping
    assert "portable_capsule_digest" not in completed_mapping
    result = evidence.evaluate_post_execution_reviewer_separation(expected, **inputs)
    assert (result.status, result.reason) == (
        "separate", "governed_review_graph_separate",
    )
    assert len(result.author_observation_locators) == 2
    assert result.candidate_ref == inputs["candidate_capsule"].candidate_ref


def test_v40_three_observation_owner_relation_remains_exact() -> None:
    inputs = _reviewer_separation_owner_inputs()
    expected = _sample("V40")
    assert evidence.evaluate_post_execution_reviewer_separation(expected, **inputs).to_mapping() == (
        CLASS_BY_V["V40"].from_mapping(expected).to_mapping()
    )
    assert inputs["author_observations"][1].observation_kind == "candidate_captured"


def test_v40_two_observation_resealed_rank13_candidate_mismatch_reaches_relation() -> None:
    inputs, _ = _two_observation_reviewer_owner()
    _rebound_author_result(inputs, candidate_ref="candidate.other.0001")
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        evidence.evaluate_post_execution_reviewer_separation(
            _reviewer_value_for_owner(inputs), **inputs,
        )
    assert caught.value.reason == "source_owner_mismatch"


@pytest.mark.parametrize("field,other", (
    ("candidate_ref", "candidate.other.0001"),
    ("capsule_manifest_ref", "capsule.other.0001"),
))
def test_v40_two_observation_resealed_review_capsule_mismatch_reaches_relation(
    field: str, other: str,
) -> None:
    inputs, _ = _two_observation_reviewer_owner()
    changed = _resealed_worker_observation(inputs["review_observation"], **{field: other})
    inputs["review_observation"] = changed
    member, relation = _resealed_review_owner_rows(
        "golden.owner.review-rank12", changed, kind_rank=12,
    )
    inputs["review_membership_row"] = member
    inputs["review_relation_row"] = relation
    _refresh_reviewer_support_set(inputs)
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        evidence.evaluate_post_execution_reviewer_separation(
            _reviewer_value_for_owner(inputs), **inputs,
        )
    assert caught.value.reason == "source_owner_mismatch"


def test_v40_three_observation_resealed_capture_mismatch_reaches_relation() -> None:
    inputs = _reviewer_separation_owner_inputs()
    changed = _resealed_worker_observation(
        inputs["author_observations"][1], candidate_ref="candidate.other.0001",
    )
    observations = list(inputs["author_observations"])
    observations[1] = changed
    inputs["author_observations"] = tuple(observations)
    member, relation = _resealed_review_owner_rows(
        "golden.owner.author-rank12.001", changed, kind_rank=12,
    )
    members = list(inputs["author_observation_membership_rows"])
    relations = list(inputs["author_observation_relation_rows"])
    members[1], relations[1] = member, relation
    inputs["author_observation_membership_rows"] = tuple(members)
    inputs["author_observation_relation_rows"] = tuple(relations)
    _rebound_author_result(inputs)
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        evidence.evaluate_post_execution_reviewer_separation(
            _reviewer_value_for_owner(inputs), **inputs,
        )
    assert caught.value.reason == "source_owner_mismatch"


def test_v40_completed_observation_cannot_synthesize_candidate_capture() -> None:
    inputs, _ = _two_observation_reviewer_owner()
    mapping = inputs["author_observations"][1].to_mapping()
    mapping["candidate_ref"] = inputs["candidate_capsule"].candidate_ref
    mapping.pop("observation_digest")
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkerObservationV1.from_mapping(_sealed_record("WorkerObservationV1", mapping))
    assert (caught.value.reason, caught.value.field_path) == (
        "invalid_field_value", "WorkerObservationV1.conditional_fields",
    )


@pytest.mark.parametrize("form,reason", (
    ("one", "invalid_cardinality"),
    ("four", "invalid_cardinality"),
    ("duplicate", "duplicate_entry"),
    ("omitted", "invalid_cardinality"),
    ("inserted", "relation_mismatch"),
    ("reordered", "relation_mismatch"),
))
def test_v40_two_observation_locator_cardinality_and_order_reject(
    form: str, reason: str,
) -> None:
    inputs, expected = _two_observation_reviewer_owner()
    locators = deepcopy(expected["author_observation_locators"])
    if form in {"one", "omitted"}:
        locators = locators[:1]
    elif form == "four":
        locators = locators + [deepcopy(locators[0]), deepcopy(locators[1])]
    elif form == "duplicate":
        locators[1] = deepcopy(locators[0])
    elif form == "inserted":
        extra = deepcopy(_sample("V40")["author_observation_locators"][2])
        locators.insert(1, extra)
    else:
        locators.reverse()
    expected["author_observation_locators"] = locators
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        evidence.evaluate_post_execution_reviewer_separation(_seal("V40", expected), **inputs)
    assert caught.value.reason == reason


def _wire_process_result_value(mapping: dict[str, object]) -> object:
    payload = deepcopy(mapping)
    payload.pop("schema_id")
    payload.pop("wire_profile_ref")
    payload.pop("wire_profile_digest")
    for name in ("result_membership", "request_membership"):
        if payload[name] is not None:
            payload[name] = RW0C1MemberLocatorV1(**payload[name])
    for name in ("adapter_observations", "process_observations"):
        payload[name] = tuple(RW0C1MemberLocatorV1(**item) for item in payload[name])
    return RW0C1WireProcessResultClassificationBindingV1(**payload)


def _support_owner(mapping: dict[str, object]) -> object:
    schema_id = mapping["schema_id"]
    v_number = next(
        (
            v_number for v_number, value_type in CLASS_BY_V.items()
            if value_type._SCHEMA_ID == schema_id
        ),
        None,
    )
    if v_number == "V40":
        return _reviewer_separation_action(_ordered_fixture("V40", mapping))
    if v_number is not None:
        return CLASS_BY_V[v_number].from_mapping(
            _ordered_fixture(v_number, mapping)
        )
    if schema_id.endswith("-profile.v1"):
        return deepcopy(mapping)
    if schema_id == "governed-execution.nwp-worker-observation.v1":
        return WorkerObservationV1.from_mapping(deepcopy(mapping))
    if schema_id == "governed-execution.nwp-candidate-capsule-manifest.v1":
        return CandidateCapsuleManifestV1.from_mapping(deepcopy(mapping))
    if schema_id == "governed-execution.nwp-rw0-effect-host-qualification.v1":
        return RW0EffectHostQualificationV1.from_mapping(deepcopy(mapping))
    if schema_id == "governed-execution.nwp-development-validation-requirement-evidence.v1":
        return DevelopmentValidationRequirementEvidenceV1(**deepcopy(mapping))
    if schema_id == "governed-execution.nwp-development-review-requirement-evidence.v1":
        return DevelopmentReviewRequirementEvidenceV1(**deepcopy(mapping))
    if schema_id == "governed-execution.nwp-rw0-authority-verification-observation.v1":
        return RW0AuthorityVerificationObservationV1.from_mapping(deepcopy(mapping))
    if schema_id == "governed-execution.nwp-attempt-fence.v1":
        return AttemptFenceV1.from_mapping(deepcopy(mapping))
    if schema_id == "governed-execution.nwp-effect-fence.v1":
        return EffectFenceV1.from_mapping(deepcopy(mapping))
    if schema_id == "governed-execution.nwp-global-stop.v1":
        return GlobalStopState.from_dict(deepcopy(mapping))
    raise AssertionError(schema_id)


def _evidence_supply_owner_inputs() -> dict[str, object]:
    supply = _sample("V10")
    raw_supplies = supply["role_supplies"]
    role_values: list[object] = []
    support_values: list[tuple[object, ...]] = []
    for index, raw_supply in enumerate(raw_supplies):
        typed = raw_supply["typed_canonical_value"]
        if index == 1:
            role_values.append(_wire_process_result_value(typed))
        else:
            role_values.append(_support_owner(typed))
        support_values.append(tuple(
            _support_owner(item) for item in raw_supply["support_canonical_values"]
        ))
    return {
        "role_values": tuple(role_values),
        "support_values": tuple(support_values),
    }


def _evidence_supply_action(value: object) -> object:
    return evidence.validate_post_execution_evidence_supply(
        value,
        **_evidence_supply_owner_inputs(),
    )


def _observation_from_result_set(mapping: dict[str, object]) -> WorkerObservationV1:
    renamed = {
        "schema_id": "source_observation_schema_id",
        "observation_ref": "source_observation_ref",
        "outcome": "source_outcome",
        "reason_code": "source_reason_code",
        "evidence_refs": "source_evidence_refs",
        "observed_at": "source_observed_at",
        "observation_digest": "source_observation_digest",
    }
    direct = (
        "source_kind", "source_ref", "source_invocation_ref", "delivery_attempt_ref",
        "program_ref", "program_version_ref", "accepted_intent_revision_ref",
        "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
        "effect_intent_ref", "command_ref", "command_digest", "attempt_fence_ref",
        "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest",
        "observation_kind", "candidate_ref", "capsule_manifest_ref",
        "portable_capsule_digest",
    )
    source = {target: mapping[origin] for target, origin in renamed.items()}
    source.update({name: mapping[name] for name in direct})
    return WorkerObservationV1.from_mapping(source)


def _qualified_result_set(v_number: str) -> tuple[object, WorkerObservationV1, object, RW0EffectHostQualificationV1]:
    mapping = _sample(v_number)
    observation = _observation_from_result_set(mapping)
    requirement_type = (
        DevelopmentValidationRequirementEvidenceV1
        if v_number == "V38"
        else DevelopmentReviewRequirementEvidenceV1
    )
    requirement = requirement_type(
        schema_id=mapping["requirement_evidence_schema_id"],
        requirement_ref=mapping["requirement_evidence_ref"],
        requirement_digest=mapping["requirement_digest"],
        work_spec_ref=mapping["requirement_work_spec_ref"],
        work_spec_digest=mapping["requirement_work_spec_digest"],
        safe_evidence_digest=mapping["requirement_evidence_safe_digest"],
    )
    profile_prefix = "validation" if v_number == "V38" else "review"
    qualification_mapping = mapping_for(
        RW0EffectHostQualificationV1,
        qualification_ref=mapping["tool_qualification_ref"],
        effect_intent_ref=mapping["effect_intent_ref"],
        effect_fence_ref=mapping["effect_fence_ref"],
        effect_fence_digest=mapping["effect_fence_digest"],
        **{
            f"required_{profile_prefix}_tool_profile_ref": mapping["tool_profile_ref"],
            f"required_{profile_prefix}_tool_profile_digest": mapping["tool_profile_digest"],
        },
    )
    qualification = RW0EffectHostQualificationV1.from_mapping(qualification_mapping)
    mapping["tool_qualification_digest"] = qualification.qualification_digest
    mapping = _seal(v_number, mapping)
    return CLASS_BY_V[v_number].from_mapping(mapping), observation, requirement, qualification


def _source_ceiling_action_inputs() -> tuple[object, AttemptFenceV1, EffectFenceV1, RW0AuthorityVerificationObservationV1, object, object]:
    attempt_mapping = _full_record("AttemptFenceV1")
    effect_mapping = _effect_fence_for_vector("author")
    attempt = AttemptFenceV1.from_mapping(attempt_mapping)
    effect = EffectFenceV1.from_mapping(effect_mapping)
    authority_mapping = mapping_for(
        RW0AuthorityVerificationObservationV1,
        parent_grant_ref=attempt_mapping["parent_standing_grant_ref"],
        parent_grant_digest=attempt_mapping["parent_standing_grant_digest"],
        attempt_basis_ref=attempt_mapping["attempt_authorization_ref"],
        attempt_basis_digest=attempt_mapping["attempt_authorization_digest"],
        effect_basis_ref=effect_mapping["effect_authorization_ref"],
        effect_basis_digest=effect_mapping["effect_authorization_digest"],
        attempt_fence_ref=attempt_mapping["attempt_fence_ref"],
        attempt_fence_digest=attempt_mapping["attempt_fence_digest"],
        effect_fence_ref=effect_mapping["effect_fence_ref"],
        effect_fence_digest=effect_mapping["effect_fence_digest"],
        repository_ref=attempt_mapping["repository_ref"],
        base_git_object_format=attempt_mapping["base_git_object_format"],
        base_git_oid=attempt_mapping["base_git_oid"],
        allowed_effect_classes=attempt_mapping["allowed_effect_classes"],
        effect_class=effect_mapping["effect_class"],
        parent_ceilings=attempt_mapping["aggregate_ceilings"],
        global_stop_ref=attempt_mapping["global_stop_ref"],
        global_stop_version=attempt_mapping["global_stop_version"],
        global_stop_state="clear",
        observed_at="2029-01-01T00:00:00Z",
        grant_expires_at="2030-01-01T00:00:00Z",
        observation_expires_at="2030-01-01T00:00:00Z",
    )
    authority = RW0AuthorityVerificationObservationV1.from_mapping(authority_mapping)
    policy_mapping = _sample("V17")
    policy_mapping.update(
        program_ref=attempt_mapping["program_ref"],
        program_version_ref=attempt_mapping["program_version_ref"],
        accepted_intent_revision_ref=attempt_mapping["accepted_intent_revision_ref"],
        work_item_ref=attempt_mapping["work_item_ref"],
        work_item_revision_ref=attempt_mapping["work_item_revision_ref"],
        semantic_attempt_ref=attempt_mapping["semantic_attempt_ref"],
        candidate_ref=effect_mapping["candidate_ref"],
        effect_intent_ref=effect_mapping["effect_intent_ref"],
        author_command_ref=effect_mapping["command_ref"],
        source_effect_fence_ref=effect_mapping["effect_fence_ref"],
        source_effect_fence_digest=effect_mapping["effect_fence_digest"],
        source_effect_class=effect_mapping["effect_class"],
        parent_grant_ref=authority_mapping["parent_grant_ref"],
        parent_grant_digest=authority_mapping["parent_grant_digest"],
        grant_family_ref=authority_mapping["grant_family_ref"],
        grant_family_digest=authority_mapping["grant_family_digest"],
        audience_ref=authority_mapping["audience_ref"],
        repository_ref=authority_mapping["repository_ref"],
        path_scope_digest=authority_mapping["path_scope_digest"],
        policy_ceilings=authority_mapping["parent_ceilings"],
        not_before="2028-01-01T00:00:00Z",
        evaluated_at="2029-01-01T00:00:00Z",
        expires_at="2030-01-01T00:00:00Z",
    )
    policy_matrix = CLASS_BY_V["V17"].from_mapping(_seal("V17", policy_mapping))
    support_mapping = _ordered_fixture(
        "V13", deepcopy(_TEST_RECORDS["golden.V13.effect-ceiling.support-set"])
    )
    support_sources = (
        (attempt_mapping["schema_id"], attempt_mapping["attempt_fence_ref"], attempt_mapping["attempt_fence_digest"]),
        (effect_mapping["schema_id"], effect_mapping["effect_fence_ref"], effect_mapping["effect_fence_digest"]),
        (authority_mapping["schema_id"], authority_mapping["observation_ref"], authority_mapping["observation_digest"]),
        (policy_matrix.schema_id, policy_matrix.matrix_ref, policy_matrix.matrix_digest),
    )
    for entry, (schema_id, source_ref, source_digest) in zip(
        support_mapping["entries"], support_sources, strict=False
    ):
        entry.update(
            source_schema_id=schema_id,
            source_ref=source_ref,
            source_digest=source_digest,
        )
    support = CLASS_BY_V["V13"].from_mapping(_seal("V13", support_mapping))
    candidate_mapping = _sample("V21")
    candidate_mapping.update(
        program_ref=attempt_mapping["program_ref"],
        program_version_ref=attempt_mapping["program_version_ref"],
        accepted_intent_revision_ref=attempt_mapping["accepted_intent_revision_ref"],
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
        attempt_allowed_effect_classes=attempt_mapping["allowed_effect_classes"],
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
        authority_allowed_effect_classes=authority_mapping["allowed_effect_classes"],
        authority_ceilings=authority_mapping["parent_ceilings"],
        authority_grant_expires_at=authority_mapping["grant_expires_at"],
        authority_observation_expires_at=authority_mapping["observation_expires_at"],
        evaluated_at="2029-01-01T00:00:00Z",
        support_set_ref=support.support_set_ref,
        support_set_digest=support.support_set_digest,
    )
    candidate = CLASS_BY_V["V21"].from_mapping(_seal("V21", candidate_mapping))
    return candidate, attempt, effect, authority, policy_matrix, support


def _decision_chain() -> dict[str, object]:
    owners = _section41_owner_inputs()
    lineage = CLASS_BY_V["V01"].from_mapping(_sample("V01"))
    context = owners["context"]
    entries = tuple(CLASS_BY_V["V26"].from_mapping(_sample("V26", index)) for index in range(8))
    pages = (decision._MembershipPage("epoch.1", (0, "0"), entries, None),)
    closure = decision.rw0_c_decision_membership_closure(_sample("V25"), pages=pages)
    stop = CLASS_BY_V["V20"].from_mapping(_sample("V20"))
    ceiling = CLASS_BY_V["V21"].from_mapping(_sample("V21"))
    sources = tuple(
        CLASS_BY_V[v_number].from_mapping(_sample(v_number))
        for v_number in ("V38", "V39", "V41", "V43", "V44")
    )
    snapshot = decision.rw0_c_decision_current_snapshot(
        _sample("V27"),
        lineage_context=lineage,
        input_context=context,
        membership_closure=closure,
        selected_authority_membership=entries[0],
        selected_section41_membership=entries[7],
        global_stop_snapshot=stop,
        source_effect_ceiling=ceiling,
        external_sources=sources,
    )
    authority_matrix = decision.evaluate_rw0_c_decision_time_authority_branches(
        _sample("V31"),
        snapshot=snapshot,
        projection=owners["projection"],
        lineage_context=lineage,
        input_context=context,
        membership_closure=closure,
        selected_authority_membership=entries[0],
        source_effect_ceiling=ceiling,
    )
    stop_matrix = decision.evaluate_rw0_c_decision_time_global_stop_branches(
        _sample("V32"), snapshot=snapshot, global_stop_snapshot=stop
    )
    ceiling_matrix = decision.evaluate_rw0_c_decision_time_source_effect_ceiling_branches(
        _sample("V33"),
        snapshot=snapshot,
        lineage_context=lineage,
        source_effect_ceiling=ceiling,
    )
    currentness = decision.evaluate_rw0_c_proposal_evidence_currentness(
        _sample("V29"),
        projection=owners["projection"],
        snapshot=snapshot,
        proposal_evidence=tuple(
            CLASS_BY_V[v_number].from_mapping(_sample(v_number))
            for v_number in ("V14", "V15", "V17", "V18")
        ),
        proposal_sources=sources,
    )
    return {
        **owners,
        "lineage": lineage,
        "entries": entries,
        "pages": pages,
        "closure": closure,
        "stop": stop,
        "ceiling": ceiling,
        "sources": sources,
        "snapshot": snapshot,
        "authority_matrix": authority_matrix,
        "stop_matrix": stop_matrix,
        "ceiling_matrix": ceiling_matrix,
        "currentness": currentness,
    }


def _active_stop_snapshot() -> tuple[object, GlobalStopState]:
    state = GlobalStopState.from_dict(_TEST_RECORDS["golden.owner.global-stop.active"])
    support_mapping = _ordered_fixture(
        "V13", deepcopy(_TEST_RECORDS["golden.V13.global-stop.support-set"])
    )
    support_mapping["entries"][0].update(
        source_ref=state.stop_ref,
        source_digest=state.canonical_digest(),
    )
    support = CLASS_BY_V["V13"].from_mapping(_seal("V13", support_mapping))
    snapshot_mapping = _sample("V20")
    source = state.to_dict()
    snapshot_mapping.update(
        global_stop_ref=state.stop_ref,
        global_stop_version=source["version"],
        global_stop_state=state.status.value,
        global_stop_stop_id=source["stop_id"],
        global_stop_reason_class=source["reason_class"],
        global_stop_issuer_ref=source["issuer_ref"],
        global_stop_issued_at=source["issued_at"],
        global_stop_operator_decision_ref=source["operator_decision_ref"],
        global_stop_digest=state.canonical_digest(),
        global_stop_updated_at="2026-09-30T12:00:01Z",
        evaluated_at="2026-09-30T12:00:02Z",
        support_set_ref=support.support_set_ref,
        support_set_digest=support.support_set_digest,
    )
    snapshot_mapping = _seal("V20", snapshot_mapping)
    snapshot = evidence.post_execution_global_stop_snapshot(
        snapshot_mapping,
        current_state=state,
        updated_at="2026-09-30T12:00:01Z",
        support_set=support,
    )
    return snapshot, state


def _synthetic_closure_entry(index: int) -> object:
    mapping = _sample("V26", 0)
    mapping.update(
        kind_rank=1,
        membership_ref=f"membership.synthetic.{index:05d}",
        membership_digest=hashlib.sha256(f"membership:{index}".encode()).hexdigest(),
        value_ref=f"value.synthetic.{index:05d}",
        value_digest=hashlib.sha256(f"value:{index}".encode()).hexdigest(),
    )
    return CLASS_BY_V["V26"].from_mapping(mapping)


OWNER_GOLDEN_RECORD_IDS = tuple(
    record_id for record_id in _TEST_RECORDS if record_id.startswith("golden.owner.")
)


def _member_locator(mapping: object) -> RW0C1MemberLocatorV1:
    assert type(mapping) is dict
    return RW0C1MemberLocatorV1(**mapping)


@pytest.mark.parametrize("record_id", OWNER_GOLDEN_RECORD_IDS)
def test_each_of_46_current_owner_goldens_executes_its_current_owner_contract(record_id: str) -> None:
    payload = deepcopy(_TEST_RECORDS[record_id])
    if record_id == "golden.owner.source-invocation":
        value = DevelopmentModelSourceInvocationRowValue(**payload)
        assert value.to_mapping() == payload
    elif record_id == "golden.owner.artifact-binding":
        value = DevelopmentPrivateProposalArtifactBindingRowValue(**payload)
        assert value.to_mapping() == payload
    elif record_id == "golden.owner.proposal":
        value = DevelopmentModelProposalRowValue(**payload)
        assert value.to_mapping() == payload
    elif ".proposal-evidence-row." in record_id:
        value = DevelopmentModelProposalEvidenceBindingRowValue(**payload)
        assert value.to_mapping() == payload
    elif record_id == "golden.owner.evidence-set":
        rows = tuple(
            DevelopmentModelProposalEvidenceBindingRowValue(
                **_TEST_RECORDS[
                    f"golden.owner.proposal-evidence-row.{rank:02d}.{role}"
                ]
            )
            for rank, role in enumerate(ROLES, 5)
        )
        identity = {
            "evidence_set_ref": payload["evidence_set_ref"],
            "proposal_ref": payload["proposal_ref"],
            "proposal_phase": payload["proposal_phase"],
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
        assert identity == {
            "evidence_set_ref": payload["evidence_set_ref"],
            "proposal_ref": payload["proposal_ref"],
            "proposal_phase": payload["proposal_phase"],
            "entries": tuple(payload["entries"]),
        }
        assert evidence._domain_separated_digest(
            "governed-execution.nwp-model-proposal-evidence-set.v1.identity",
            identity,
        ) == payload["evidence_set_digest"]
    elif record_id == "golden.owner.owner-family-graph":
        locators = tuple(RW0C1OwnerRowLocatorV1(**item) for item in payload["owners"])
        assert section41_owner_family_graph_digest(locators) == _TEST_RECORDS[
            "golden.owner.rank15.value"
        ]["owner_family_graph_digest"]
    elif record_id == "golden.owner.global-stop.active":
        assert GlobalStopState.from_dict(payload).to_dict() == payload
    elif "observation" in record_id and not record_id.endswith((".graph", ".membership", ".operands", ".relation")):
        assert WorkerObservationV1.from_mapping(payload).to_mapping() == payload
    elif record_id.endswith(".operands"):
        operands = tuple(RW0C1OperandIdentity(**item) for item in payload)
        relation_payload = _TEST_RECORDS[record_id.removesuffix(".operands") + ".relation"]
        assert operand_set_digest(
            phase_basis_ref=relation_payload["phase_basis_ref"],
            relation_ref=relation_payload["relation_ref"],
            operands=operands,
        ) == relation_payload["operand_set_digest"]
    elif record_id.endswith(".relation"):
        row = rw0_c1_row_value_from_tuple(
            "rw0_relation_bindings",
            tuple(payload[name] for name in RELATION_COLUMNS),
        )
        assert row.to_mapping() == payload
    elif record_id.endswith(".membership"):
        identity = {
            name: payload[name]
            for name in (
                "schema_id", "membership_ref", "phase_basis_ref", "phase_basis_digest",
                "kind_rank", "value_ref", "value_digest", "value_schema_id",
                "scope_binding_digest", "relation_set_digest", "admitted_by_mutation_ref",
                "admitted_at", "admission_graph_digest",
            )
        }
        payload["membership_digest"] = membership_digest(identity)
        row = rw0_c1_row_value_from_tuple(
            "rw0_evidence_memberships",
            tuple(payload[name] for name in MEMBERSHIP_COLUMNS),
        )
        assert row.to_mapping() == payload
    elif record_id.endswith(".graph"):
        digest = admission_graph_digest(payload)
        membership_payload = _TEST_RECORDS[record_id.removesuffix(".graph") + ".membership"]
        assert digest == membership_payload["admission_graph_digest"]
    elif record_id == "golden.owner.author-rank13.value":
        payload.pop("schema_id")
        payload.pop("wire_profile_ref")
        payload.pop("wire_profile_digest")
        payload["observation_memberships"] = tuple(
            _member_locator(item) for item in payload["observation_memberships"]
        )
        value = RW0C1WireWorkerResultBindingV1(**payload)
        assert value.value_digest == _TEST_RECORDS[record_id]["value_digest"]
    elif record_id == "golden.owner.rank14.value":
        expected = deepcopy(payload)
        payload.pop("schema_id")
        payload.pop("wire_profile_ref")
        payload.pop("wire_profile_digest")
        for name in ("result_membership", "request_membership"):
            if payload[name] is not None:
                payload[name] = _member_locator(payload[name])
        for name in ("adapter_observations", "process_observations"):
            payload[name] = tuple(_member_locator(item) for item in payload[name])
        value = RW0C1WireProcessResultClassificationBindingV1(**payload)
        assert value.to_mapping() == expected
    elif record_id == "golden.owner.rank15.value":
        expected = deepcopy(payload)
        payload.pop("schema_id")
        value = RW0C1Section41PostExecutionProposalFamilyMemberV1(**payload)
        assert value.to_mapping() == expected
    else:
        raise AssertionError(record_id)


ACTION_NAMES = (
    "validate_independent_review_disposition",
    "validate_post_execution_evidence_supply",
    "post_execution_global_stop_snapshot",
    "validate_post_execution_model_input_binding",
    "validate_post_execution_review_result_set",
    "evaluate_post_execution_reviewer_separation",
    "construct_post_execution_semantic_review_input",
    "evaluate_post_execution_source_effect_ceiling",
    "construct_post_execution_support_set",
    "validate_post_execution_validation_result_set",
    "validate_validation_disposition",
    "validate_post_execution_risk_lane_matrix_relation",
    "validate_post_execution_risk_policy_attestation",
    "post_execution_risk_source_binding",
    "post_execution_risk_source_profile",
    "validate_post_execution_standing_policy_matrix_relation",
    "validate_post_execution_standing_policy_attestation",
    "finite_backlog_risk_source_projection",
    "section41_post_execution_proposal_family_projection",
    "section41_post_execution_role_resolution",
    "rw0_c_decision_current_snapshot",
    "rw0_c_decision_membership_closure",
    "evaluate_rw0_c_decision_time_authority_branches",
    "evaluate_rw0_c_decision_time_global_stop_branches",
    "evaluate_rw0_c_decision_time_source_effect_ceiling_branches",
    "evaluate_rw0_c_proposal_evidence_currentness",
    "evaluate_rw0_c_recommendation_consistency",
)


@pytest.mark.parametrize("action_name", ACTION_NAMES)
def test_all_27_frozen_actions_execute_against_independent_typed_inputs(action_name: str) -> None:
    if action_name == "validate_independent_review_disposition":
        result = evidence.validate_independent_review_disposition(
            _sample("V15"),
            review_result_set=CLASS_BY_V["V39"].from_mapping(_sample("V39")),
            reviewer_separation=CLASS_BY_V["V40"].from_mapping(_sample("V40")),
        )
    elif action_name == "validate_post_execution_evidence_supply":
        result = _evidence_supply_action(_sample("V10"))
    elif action_name == "post_execution_global_stop_snapshot":
        support = CLASS_BY_V["V13"].from_mapping(
            _ordered_fixture("V13", _TEST_RECORDS["golden.V13.global-stop.support-set"])
        )
        result = evidence.post_execution_global_stop_snapshot(
            _sample("V20"), current_state=GlobalStopState(version=7),
            updated_at="2026-09-30T11:59:45Z", support_set=support,
        )
    elif action_name == "validate_post_execution_model_input_binding":
        result = evidence.validate_post_execution_model_input_binding(
            _sample("V09"), input_context=CLASS_BY_V["V02"].from_mapping(_sample("V02")),
            safe_projection=CLASS_BY_V["V05"].from_mapping(_sample("V05")),
            private_manifest=CLASS_BY_V["V07"].from_mapping(_sample("V07")),
        )
    elif action_name in {"validate_post_execution_review_result_set", "validate_post_execution_validation_result_set"}:
        v_number = "V39" if "review" in action_name else "V38"
        candidate, observation, requirement, qualification = _qualified_result_set(v_number)
        action = getattr(evidence, action_name)
        result = action(
            candidate, source_observation=observation,
            requirement_evidence=requirement, tool_qualification=qualification,
        )
    elif action_name == "evaluate_post_execution_reviewer_separation":
        result = _reviewer_separation_action(_sample("V40"))
    elif action_name == "construct_post_execution_semantic_review_input":
        result = evidence.construct_post_execution_semantic_review_input(
            _sample("V02"),
            lineage_context=CLASS_BY_V["V01"].from_mapping(_sample("V01")),
            role_entries=tuple(CLASS_BY_V["V03"].from_mapping(_sample("V03", index)) for index in range(9)),
            safe_projection=CLASS_BY_V["V05"].from_mapping(_sample("V05")),
            private_manifest=CLASS_BY_V["V07"].from_mapping(_sample("V07")),
        )
    elif action_name == "evaluate_post_execution_source_effect_ceiling":
        candidate, attempt, effect, authority, policy_matrix, support = _source_ceiling_action_inputs()
        result = evidence.evaluate_post_execution_source_effect_ceiling(
            candidate, attempt_fence=attempt, effect_fence=effect,
            authority_observation=authority, standing_policy_matrix=policy_matrix,
            support_set=support,
        )
    elif action_name == "construct_post_execution_support_set":
        results = []
        for record_id in sorted(key for key in _TEST_RECORDS if key.startswith("golden.V13.")):
            mapping = _ordered_fixture("V13", _TEST_RECORDS[record_id])
            entries = tuple(CLASS_BY_V["V12"].from_mapping(item) for item in mapping["entries"])
            results.append(evidence.construct_post_execution_support_set(mapping, entries=entries))
        assert len(results) == 7
        result = results[0]
    elif action_name == "validate_validation_disposition":
        result = evidence.validate_validation_disposition(
            _sample("V14"), validation_result_set=CLASS_BY_V["V38"].from_mapping(_sample("V38"))
        )
    elif action_name == "validate_post_execution_risk_lane_matrix_relation":
        result = policy.validate_post_execution_risk_lane_matrix_relation(
            _sample("V18"), risk_policy=CLASS_BY_V["V42"].from_mapping(_sample("V42")),
            source_profile=CLASS_BY_V["V43"].from_mapping(_sample("V43")),
            source_binding=CLASS_BY_V["V44"].from_mapping(_sample("V44")),
        )
    elif action_name == "validate_post_execution_risk_policy_attestation":
        result = policy.validate_post_execution_risk_policy_attestation(_sample("V42"))
    elif action_name == "post_execution_risk_source_binding":
        result = policy.post_execution_risk_source_binding(
            _sample("V44"), source_profile=CLASS_BY_V["V43"].from_mapping(_sample("V43")),
            source_value=CLASS_BY_V["V19"].from_mapping(_sample("V19")),
        )
    elif action_name == "post_execution_risk_source_profile":
        result = policy.post_execution_risk_source_profile(_sample("V43"))
    elif action_name == "validate_post_execution_standing_policy_matrix_relation":
        result = policy.validate_post_execution_standing_policy_matrix_relation(
            _sample("V17"), policy_source=CLASS_BY_V["V41"].from_mapping(_sample("V41"))
        )
    elif action_name == "validate_post_execution_standing_policy_attestation":
        result = policy.validate_post_execution_standing_policy_attestation(_sample("V41"))
    elif action_name == "finite_backlog_risk_source_projection":
        result = adapter.finite_backlog_risk_source_projection(
            _sample("V19"), evaluated_at="2026-09-30T11:59:53Z",
            expires_at="2026-10-01T01:30:00Z",
        )
        assert tuple(item.to_mapping() for item in result) == (_sample("V43"), _sample("V44"))
        return
    elif action_name == "section41_post_execution_proposal_family_projection":
        result = _section41_owner_inputs()["projection"]
    elif action_name == "section41_post_execution_role_resolution":
        owners = _section41_owner_inputs()
        supply_owners = _evidence_supply_owner_inputs()
        family = tuple(CLASS_BY_V["V24"].from_mapping(_sample("V24", index)) for index in range(9))
        result = resolution.section41_post_execution_role_resolution(
            _sample("V24"), requested_role=ROLES[0], family=family,
            projection=owners["projection"], input_context=owners["context"],
            evidence_supply=CLASS_BY_V["V10"].from_mapping(_sample("V10")),
            evidence_role_values=supply_owners["role_values"],
            evidence_support_values=supply_owners["support_values"],
            evidence_rows=owners["evidence_rows"], section41_value=owners["rank15_value"],
            section41_membership_row=owners["rank15_membership"],
        )
    else:
        chain = _decision_chain()
        if action_name == "rw0_c_decision_current_snapshot":
            result = chain["snapshot"]
        elif action_name == "rw0_c_decision_membership_closure":
            result = chain["closure"]
        elif action_name == "evaluate_rw0_c_decision_time_authority_branches":
            result = chain["authority_matrix"]
        elif action_name == "evaluate_rw0_c_decision_time_global_stop_branches":
            result = chain["stop_matrix"]
        elif action_name == "evaluate_rw0_c_decision_time_source_effect_ceiling_branches":
            result = chain["ceiling_matrix"]
        elif action_name == "evaluate_rw0_c_proposal_evidence_currentness":
            result = chain["currentness"]
        else:
            result = decision.evaluate_rw0_c_recommendation_consistency(
                _sample("V34"), projection=chain["projection"], snapshot=chain["snapshot"],
                proposal_currentness=chain["currentness"], authority_matrix=chain["authority_matrix"],
                global_stop_matrix=chain["stop_matrix"], source_effect_ceiling_matrix=chain["ceiling_matrix"],
                authoritative_branch="candidate_acceptance", lineage_context=chain["lineage"],
                input_context=chain["context"], membership_closure=chain["closure"],
                selected_authority_membership=chain["entries"][0], global_stop_snapshot=chain["stop"],
                source_effect_ceiling=chain["ceiling"],
            )
    assert result is not None


def test_v22_resigned_artifact_before_source_chronology_rejects_causally() -> None:
    owners = _section41_owner_inputs()
    candidate = _sample("V22")
    candidate["artifact_validated_at"] = "2026-09-30T11:59:57Z"
    candidate = _seal("V22", candidate)
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        projection.section41_post_execution_proposal_family_projection(
            candidate,
            input_context=owners["context"],
            source_invocation_row=owners["source"],
            artifact_binding_row=owners["artifact"],
            proposal_row=owners["proposal_row"],
            evidence_rows=owners["evidence_rows"],
            private_reader_tuples=owners["reader_rows"],
            owner_locators=owners["owner_locators"],
            rank15_value=owners["rank15_value"],
            rank15_relation_row=owners["rank15_relation"],
            rank15_admission_graph=owners["rank15_graph"],
            rank15_membership_row=owners["rank15_membership"],
            admitted_by_mutation_ref=owners["rank15_graph"]["admitted_by_mutation_ref"],
        )
    assert caught.value.reason == "relation_mismatch"


def test_v22_fully_resealed_source_proposal_model_contract_mismatch_rejects_causally() -> None:
    owners = _section41_owner_inputs()

    proposal_mapping = owners["proposal_row"].to_mapping()
    proposal_mapping["model_contract_ref"] = "model-contract-inconsistent.1"
    proposal_mapping["proposal_digest"] = evidence._domain_separated_digest(
        proposal_mapping["schema_id"] + ".identity",
        {
            name: member for name, member in proposal_mapping.items()
            if name != "proposal_digest"
        },
    )
    hostile_proposal = DevelopmentModelProposalRowValue(**proposal_mapping)

    locator_mappings = [item.to_mapping() for item in owners["owner_locators"]]
    locator_mappings[2]["row_digest"] = hostile_proposal.proposal_digest
    hostile_locators = tuple(
        RW0C1OwnerRowLocatorV1(**mapping) for mapping in locator_mappings
    )
    hostile_owner_digest = section41_owner_family_graph_digest(hostile_locators)

    rank15_mapping = owners["rank15_value"].to_mapping()
    rank15_mapping.pop("schema_id")
    rank15_mapping.pop("value_digest")
    rank15_mapping["proposal_digest"] = hostile_proposal.proposal_digest
    rank15_mapping["owner_family_graph_digest"] = hostile_owner_digest
    hostile_rank15 = RW0C1Section41PostExecutionProposalFamilyMemberV1(
        **rank15_mapping
    )

    owner_rows = (
        owners["source"], owners["artifact"], hostile_proposal,
        *owners["evidence_rows"],
    )
    operands = tuple(
        _located_owner_operand(ordinal, locator, row)
        for ordinal, (locator, row) in enumerate(
            zip(hostile_locators, owner_rows, strict=True)
        )
    )
    relation_mapping = owners["rank15_relation"].to_mapping()
    hostile_relation_digest, hostile_operand_set_digest = relation_digest(
        phase_basis_ref=relation_mapping["phase_basis_ref"],
        phase_basis_digest=relation_mapping["phase_basis_digest"],
        relation_ref=relation_mapping["relation_ref"],
        subject_type=relation_mapping["subject_type"],
        subject_membership_ref=relation_mapping["subject_membership_ref"],
        subject_kind_rank=relation_mapping["subject_kind_rank"],
        subject_value_ref=hostile_rank15.value_ref,
        subject_value_digest=hostile_rank15.value_digest,
        subject_value_schema_id=hostile_rank15.schema_id,
        specification=relation_specifications(kind_rank=15)[0],
        evaluated_at=relation_mapping["evaluated_at"],
        operands=operands,
    )
    hostile_relation_set_digest = relation_set_digest(
        phase_basis_ref=hostile_rank15.phase_basis_ref,
        subject_type="evidence_membership",
        subject_ref=relation_mapping["subject_membership_ref"],
        relations=((0, relation_mapping["relation_ref"], hostile_relation_digest),),
    )

    hostile_graph = deepcopy(owners["rank15_graph"])
    hostile_graph.update(
        value_digest=hostile_rank15.value_digest,
        scope_binding_digest=hostile_owner_digest,
        relation_set_digest=hostile_relation_set_digest,
        relations=[{
            "relation_ref": relation_mapping["relation_ref"],
            "relation_digest": hostile_relation_digest,
            "relation_rank": 0,
            "operand_set_digest": hostile_operand_set_digest,
            "evaluated_at": None,
        }],
    )
    hostile_graph_digest = admission_graph_digest(hostile_graph)

    membership_mapping = owners["rank15_membership"].to_mapping()
    membership_mapping.update(
        value_digest=hostile_rank15.value_digest,
        scope_binding_digest=hostile_owner_digest,
        relation_set_digest=hostile_relation_set_digest,
        admission_graph_digest=hostile_graph_digest,
    )
    hostile_membership = build_row(
        "rw0_evidence_memberships",
        {
            name: membership_mapping[name]
            for name in MEMBERSHIP_COLUMNS
            if name != "membership_digest"
        },
    )

    relation_mapping.update(
        relation_digest=hostile_relation_digest,
        subject_membership_digest=hostile_membership.to_mapping()[
            "membership_digest"
        ],
        subject_value_digest=hostile_rank15.value_digest,
        operand_set_digest=hostile_operand_set_digest,
    )
    hostile_relation = build_row(
        "rw0_relation_bindings",
        {
            name: relation_mapping[name]
            for name in RELATION_COLUMNS
            if name != "relation_row_digest"
        },
    )

    evidence_snapshots = tuple(
        RW0C1OwnerRowSnapshot(
            owner_role=locator.role,
            columns=type(row)._COLUMNS,
            values=tuple(getattr(row, name) for name in type(row)._COLUMNS),
        )
        for locator, row in zip(
            hostile_locators[3:], owners["evidence_rows"], strict=True
        )
    )
    assert not _section41_owner_family_matches(
        hostile_rank15,
        tuple(zip(hostile_locators, owner_rows, strict=True)),
        evidence_snapshots,
    )

    candidate = _sample("V22")
    candidate["proposal_digest"] = hostile_proposal.proposal_digest
    candidate["owner_family_graph_digest"] = hostile_owner_digest
    candidate = _seal("V22", candidate)
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        projection.section41_post_execution_proposal_family_projection(
            candidate,
            input_context=owners["context"],
            source_invocation_row=owners["source"],
            artifact_binding_row=owners["artifact"],
            proposal_row=hostile_proposal,
            evidence_rows=owners["evidence_rows"],
            private_reader_tuples=tuple(
                tuple(getattr(row, name) for name in type(row)._COLUMNS)
                for row in owner_rows
            ),
            owner_locators=hostile_locators,
            rank15_value=hostile_rank15,
            rank15_relation_row=hostile_relation,
            rank15_admission_graph=hostile_graph,
            rank15_membership_row=hostile_membership,
            admitted_by_mutation_ref=hostile_graph["admitted_by_mutation_ref"],
        )
    assert caught.value.reason == "relation_mismatch"


@pytest.mark.parametrize(
    "v_number,index,mutation,expected_reason",
    (
        (
            "V03", 0,
            {
                "source_profile_ref": "unexpected-profile.1",
                "source_profile_digest": "f" * 64,
            },
            "invalid_profile_pair",
        ),
        (
            "V03", 1,
            {
                "direct_c1_kind": None,
                "direct_c1_kind_rank": None,
                "direct_c1_membership_ref": None,
                "direct_c1_membership_digest": None,
            },
            "source_owner_mismatch",
        ),
        (
            "V11", 1,
            {
                "source_profile_ref": "unexpected-profile.1",
                "source_profile_digest": "f" * 64,
            },
            "invalid_profile_pair",
        ),
    ),
)
def test_v03_v11_frozen_role_branch_table_rejects_hostile_substitutions(
    v_number: str,
    index: int,
    mutation: dict[str, object],
    expected_reason: str,
) -> None:
    candidate = _sample(v_number, index)
    candidate.update(mutation)
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        CLASS_BY_V[v_number].from_mapping(candidate)
    assert caught.value.reason == expected_reason


_V03_BRANCH_DIMENSIONS = (
    "role", "rank", "ordinal", "typed_schema", "source_posture",
    "model_input_posture", "direct_c1", "source_profile", "source_binding",
)
_V11_BRANCH_DIMENSIONS = (
    "role", "rank", "ordinal", "typed_schema", "model_input_posture",
    "source_profile", "source_binding", "support",
)
_EXHAUSTIVE_ROLE_BRANCH_CASES = tuple(
    (v_number, index, dimension)
    for v_number, dimensions in (
        ("V03", _V03_BRANCH_DIMENSIONS),
        ("V11", _V11_BRANCH_DIMENSIONS),
    )
    for index in range(9)
    for dimension in dimensions
)


def _mutated_role_branch(
    v_number: str,
    index: int,
    dimension: str,
) -> dict[str, object]:
    candidate = deepcopy(_sample(v_number, index))
    alternate = (index + 1) % 9
    if dimension == "role":
        candidate["role"] = ROLES[alternate]
    elif dimension == "rank":
        candidate["role_rank"] = alternate + 5
    elif dimension == "ordinal":
        candidate["ordinal"] = 1
    elif dimension == "typed_schema":
        candidate["typed_schema_id"] = _sample(
            v_number, alternate
        )["typed_schema_id"]
    elif dimension == "source_posture":
        candidate["source_posture"] = (
            "c1_admitted_exact_value"
            if candidate["source_posture"] != "c1_admitted_exact_value"
            else "transient_owner_resupply"
        )
    elif dimension == "model_input_posture":
        candidate["model_input_posture"] = (
            "private_exact_canonical_value"
            if candidate["model_input_posture"] != "private_exact_canonical_value"
            else "nonprivate_exact_canonical_value"
        )
    elif dimension == "direct_c1":
        names = (
            "direct_c1_kind", "direct_c1_kind_rank",
            "direct_c1_membership_ref", "direct_c1_membership_digest",
        )
        donor = _sample("V03", 1)
        replacement = (
            (None, None, None, None)
            if candidate["direct_c1_kind"] is not None
            else tuple(donor[name] for name in names)
        )
        candidate.update(zip(names, replacement, strict=True))
    elif dimension == "source_profile":
        if candidate["source_profile_ref"] is None:
            donor = _sample(v_number, 1)
            for name in (
                "source_profile_ref", "source_profile_digest",
                "source_profile_canonical_value",
            ):
                if name in candidate:
                    candidate[name] = deepcopy(donor[name])
        elif index == 5:
            candidate["source_profile_ref"] = None
            candidate["source_profile_digest"] = None
            if "source_profile_canonical_value" in candidate:
                candidate["source_profile_canonical_value"] = None
        else:
            candidate["source_profile_ref"] = "unexpected-profile.1"
            candidate["source_profile_digest"] = "f" * 64
    elif dimension == "source_binding":
        binding_names = (
            "source_binding_schema_id", "source_binding_ref",
            "source_binding_digest", "source_binding_canonical_value",
        )
        if candidate["source_binding_schema_id"] is None:
            donor = _sample(v_number, 1)
            for name in binding_names:
                if name in candidate:
                    candidate[name] = deepcopy(donor[name])
        else:
            candidate["source_binding_schema_id"] = None
            candidate["source_binding_ref"] = None
            candidate["source_binding_digest"] = None
            if "source_binding_canonical_value" in candidate:
                candidate["source_binding_canonical_value"] = None
    else:
        assert dimension == "support" and v_number == "V11"
        support_names = (
            "support_set_ref", "support_set_digest", "support_set_canonical_value",
            "support_value_count", "support_canonical_values",
        )
        if candidate["support_value_count"] == 0:
            donor = _sample("V11", 2)
            for name in support_names:
                candidate[name] = deepcopy(donor[name])
        else:
            candidate.update(
                support_set_ref=None,
                support_set_digest=None,
                support_set_canonical_value=None,
                support_value_count=0,
                support_canonical_values=[],
            )
    return candidate


@pytest.mark.parametrize(
    "v_number,index,dimension",
    _EXHAUSTIVE_ROLE_BRANCH_CASES,
)
def test_v03_v11_each_role_rejects_every_wrong_branch_and_restores_exactly(
    v_number: str,
    index: int,
    dimension: str,
) -> None:
    baseline = _sample(v_number, index)
    baseline_bytes = _canonical(baseline)
    mutated = _mutated_role_branch(v_number, index, dimension)
    assert _canonical(mutated) != baseline_bytes

    if v_number == "V03":
        with pytest.raises(evidence._PostExecutionContractViolation):
            CLASS_BY_V["V03"].from_mapping(mutated)
    else:
        parent = deepcopy(_sample("V10"))
        parent["role_supplies"][index] = mutated
        parent = _seal("V10", parent)
        with pytest.raises(evidence._PostExecutionContractViolation):
            _evidence_supply_action(parent)

    restored = _sample(v_number, index)
    assert _canonical(restored) == baseline_bytes
    assert CLASS_BY_V[v_number].from_mapping(restored).to_mapping() == restored


def test_v24_fabricated_decision_currentness_pair_rejects_in_grammar_and_action() -> None:
    candidate = _sample("V24")
    candidate.update(
        decision_currentness_profile_ref=(
            "rw0-c-proposal-evidence-currentness.fabricated"
        ),
        decision_currentness_profile_digest="f" * 64,
    )
    candidate = _seal("V24", candidate)
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        CLASS_BY_V["V24"].from_mapping(candidate)
    assert caught.value.reason == "invalid_profile_pair"

    owners = _section41_owner_inputs()
    supply_owners = _evidence_supply_owner_inputs()
    accepted_mappings = [_sample("V24", index) for index in range(9)]
    hostile_mappings = []
    for accepted in accepted_mappings:
        hostile = deepcopy(accepted)
        hostile.update(
            decision_currentness_profile_ref=(
                "rw0-c-proposal-evidence-currentness.fabricated"
            ),
            decision_currentness_profile_digest="f" * 64,
        )
        hostile = _seal("V24", hostile)
        assert hostile["relation_ref"] != accepted["relation_ref"]
        assert hostile["relation_digest"] != accepted["relation_digest"]
        hostile_mappings.append(hostile)

    family = [
        CLASS_BY_V["V24"].from_mapping(mapping)
        for mapping in accepted_mappings
    ]
    for value, hostile in zip(family, hostile_mappings, strict=True):
        for name in (
            "decision_currentness_profile_ref",
            "decision_currentness_profile_digest",
            "relation_ref",
            "relation_digest",
        ):
            object.__setattr__(value, name, hostile[name])
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        resolution.section41_post_execution_role_resolution(
            _sample("V24"), requested_role="candidate_capsule",
            family=tuple(family), projection=owners["projection"],
            input_context=owners["context"],
            evidence_supply=CLASS_BY_V["V10"].from_mapping(_sample("V10")),
            evidence_role_values=supply_owners["role_values"],
            evidence_support_values=supply_owners["support_values"],
            evidence_rows=owners["evidence_rows"],
            section41_value=owners["rank15_value"],
            section41_membership_row=owners["rank15_membership"],
        )
    assert caught.value.reason == "invalid_profile_pair"

    restored_family = tuple(
        CLASS_BY_V["V24"].from_mapping(mapping)
        for mapping in accepted_mappings
    )
    for index, accepted in enumerate(accepted_mappings):
        recovered = resolution.section41_post_execution_role_resolution(
            accepted, requested_role=ROLES[index], family=restored_family,
            projection=owners["projection"], input_context=owners["context"],
            evidence_supply=CLASS_BY_V["V10"].from_mapping(_sample("V10")),
            evidence_role_values=supply_owners["role_values"],
            evidence_support_values=supply_owners["support_values"],
            evidence_rows=owners["evidence_rows"],
            section41_value=owners["rank15_value"],
            section41_membership_row=owners["rank15_membership"],
        )
        assert _canonical(recovered.to_mapping()) == _canonical(accepted)


def test_v24_resigned_rank5_role_substitution_rejects_before_resolution_identity() -> None:
    owners = _section41_owner_inputs()
    supply_owners = _evidence_supply_owner_inputs()
    family_mappings = [_sample("V24", index) for index in range(9)]
    family_mappings[0]["context_role"] = "worker_result"
    family_mappings[0] = _seal("V24", family_mappings[0])
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        family = tuple(
            CLASS_BY_V["V24"].from_mapping(mapping) for mapping in family_mappings
        )
        resolution.section41_post_execution_role_resolution(
            _sample("V24"), requested_role="candidate_capsule", family=family,
            projection=owners["projection"], input_context=owners["context"],
            evidence_supply=CLASS_BY_V["V10"].from_mapping(_sample("V10")),
            evidence_role_values=supply_owners["role_values"],
            evidence_support_values=supply_owners["support_values"],
            evidence_rows=owners["evidence_rows"], section41_value=owners["rank15_value"],
            section41_membership_row=owners["rank15_membership"],
        )
    assert caught.value.reason == "source_owner_mismatch"


def test_v25_resigned_incomplete_subset_rejects_against_complete_transcript() -> None:
    complete = tuple(CLASS_BY_V["V26"].from_mapping(_sample("V26", index)) for index in range(8))
    incomplete = _sample("V25")
    incomplete["entries"] = [complete[0].to_mapping()]
    incomplete["entry_count"] = 1
    incomplete = _seal("V25", incomplete)
    pages = (decision._MembershipPage("epoch.1", (0, "0"), complete, None),)
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        decision.rw0_c_decision_membership_closure(incomplete, pages=pages)
    assert caught.value.reason == "source_owner_mismatch"


@pytest.mark.parametrize(
    "case",
    ("reordered", "duplicate", "premature", "no_progress", "continuation", "epoch"),
)
def test_v25_finite_page_transcript_controls_reject_at_the_causal_layer(case: str) -> None:
    canonical = tuple(CLASS_BY_V["V26"].from_mapping(_sample("V26", index)) for index in range(8))
    if case == "reordered":
        pages = (decision._MembershipPage("epoch.1", (0, "0"), tuple(reversed(canonical)), None),)
    elif case == "duplicate":
        pages = (decision._MembershipPage("epoch.1", (0, "0"), (canonical[0], canonical[0]), None),)
    else:
        rows = tuple(_synthetic_closure_entry(index) for index in range(258))
        first = decision._MembershipPage("epoch.1", (0, "0"), rows[:257], (1, rows[255].membership_ref))
        if case == "premature":
            pages = (first,)
        elif case == "no_progress":
            pages = (first, decision._MembershipPage("epoch.1", (0, "0"), rows[256:], None))
        elif case == "continuation":
            pages = (first, decision._MembershipPage("epoch.1", (1, rows[255].membership_ref), rows[257:], None))
        else:
            pages = (first, decision._MembershipPage("epoch.2", (1, rows[255].membership_ref), rows[256:], None))
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        decision.rw0_c_decision_membership_closure(_sample("V25"), pages=pages)
    assert caught.value.reason in {"relation_mismatch", "duplicate_entry"}


def test_v25_explicit_65537th_entry_overflow_probe_rejects() -> None:
    rows = tuple(_synthetic_closure_entry(index) for index in range(65537))
    pages = tuple(
        decision._MembershipPage(
            "epoch.overflow",
            (0, "0") if page == 0 else (1, rows[page * 256 - 1].membership_ref),
            rows[page * 256 : page * 256 + 257],
            (1, rows[page * 256 + 255].membership_ref),
        )
        for page in range(256)
    ) + (
        decision._MembershipPage(
            "epoch.overflow", (1, rows[65535].membership_ref), (rows[65536],), None
        ),
    )
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        decision.rw0_c_decision_membership_closure(_sample("V25"), pages=pages)
    assert caught.value.reason == "invalid_cardinality"


def test_v32_resigned_clear_results_reject_against_active_stop_owner() -> None:
    stop, _state = _active_stop_snapshot()
    snapshot = CLASS_BY_V["V27"].from_mapping(_sample("V27", 1))
    candidate = _sample("V32", 1)
    candidate["entries"] = deepcopy(_sample("V32")["entries"])
    candidate = _seal("V32", candidate)
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        decision.evaluate_rw0_c_decision_time_global_stop_branches(
            candidate, snapshot=snapshot, global_stop_snapshot=stop
        )
    assert caught.value.reason == "evaluation_contract_mismatch"


def test_v40_resigned_reused_reviewer_invocation_cannot_claim_separate() -> None:
    candidate = _sample("V40")
    candidate["review_source_invocation_ref"] = candidate["author_source_invocation_ref"]
    candidate = _seal("V40", candidate)
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        _reviewer_separation_action(candidate)
    assert caught.value.reason == "evaluation_contract_mismatch"


def test_v14_resigned_failed_source_cannot_claim_validation_passed() -> None:
    result_mapping = _sample("V38")
    result_mapping.update(
        source_outcome="failed",
        source_reason_code="validation_failed_repairable",
        result="repairable_failure",
        repairability="repairable",
        reason="validation_failed_repairable",
    )
    failed_result = CLASS_BY_V["V38"].from_mapping(_seal("V38", result_mapping))
    candidate = _sample("V14")
    candidate.update(
        source_outcome="failed",
        source_reason_code="validation_failed_repairable",
        validation_result_set_ref=failed_result.result_set_ref,
        validation_result_set_digest=failed_result.result_set_digest,
    )
    candidate = _seal("V14", candidate)
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        evidence.validate_validation_disposition(
            candidate, validation_result_set=failed_result
        )
    assert caught.value.reason == "evaluation_contract_mismatch"


def test_current_rank15_and_migration0003_grounding_stay_current_owned() -> None:
    assert RW0C1Section41PostExecutionProposalFamilyMemberV1.__module__.endswith("._rw0_c1_semantic_values")
    assert membership_digest.__module__.endswith("._rw0_c1_mutation_contracts")
    assert admission_graph_digest.__module__.endswith("._rw0_c1_mutation_contracts")
    assert section41_owner_family_graph_digest.__module__.endswith("._rw0_c1_mutation_contracts")
    migration = (ROOT / "src/ge_nwp_coordinator/sqlite_migrations/0003_cognitive_proposal_and_selection_state.sql").read_text()
    for rank, role in enumerate(ROLES, 5):
        assert f"'{role}'" in migration
        assert str(rank) in migration
    rank15_preimages = (
        {"admitted_by_mutation_ref": "c1-admit-section41-golden.0001", "kind_rank": 15},
        {"admitted_by_mutation_ref": "c1-admit-section41-golden.0001", "subject_kind_rank": 15},
    )
    assert all(item["admitted_by_mutation_ref"] == "c1-admit-section41-golden.0001" for item in rank15_preimages)


def test_current_rank15_family_reconstructs_and_passes_the_current_matcher() -> None:
    owners = _section41_owner_inputs()
    owner_rows = (
        owners["source"],
        owners["artifact"],
        owners["proposal_row"],
        *owners["evidence_rows"],
    )
    located = tuple(zip(owners["owner_locators"], owner_rows, strict=True))
    evidence_snapshots = tuple(
        RW0C1OwnerRowSnapshot(
            owner_role=locator.role,
            columns=type(row)._COLUMNS,
            values=tuple(getattr(row, name) for name in type(row)._COLUMNS),
        )
        for locator, row in located[3:]
    )
    assert len(located) == 12
    assert len(evidence_snapshots) == 9
    assert _section41_owner_family_matches(
        owners["rank15_value"],
        located,
        evidence_snapshots,
    )


def test_exact_private_resupply_round_trip_and_safe_projection_exclusions() -> None:
    supplied = CLASS_BY_V["V10"].from_mapping(_sample("V10"))
    reconstructed = CLASS_BY_V["V10"].from_mapping(supplied.to_mapping())
    assert reconstructed == supplied
    capsule_projection = CLASS_BY_V["V04"].from_mapping(_sample("V04"))
    forbidden = {"entries", "path", "operation", "mode", "blob", "body", "byte_length", "custody"}
    assert forbidden.isdisjoint(capsule_projection.to_mapping())
    assert "entries" not in CLASS_BY_V["V04"]._FIELDS


def test_resigned_typed_resupply_bytes_must_equal_the_independent_owner() -> None:
    candidate = deepcopy(_sample("V10"))
    capsule = candidate["role_supplies"][0]["typed_canonical_value"]
    capsule["repository_ref"] = "repository-substituted.1"
    capsule = _sealed_record(
        "CandidateCapsuleManifestV1",
        {
            name: value
            for name, value in capsule.items()
            if name != "portable_capsule_digest"
        },
    )
    candidate["role_supplies"][0]["typed_canonical_value"] = capsule
    candidate["role_supplies"][0]["typed_value_digest"] = capsule[
        "portable_capsule_digest"
    ]
    candidate = _seal("V10", candidate)
    CLASS_BY_V["V10"].from_mapping(candidate)
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        _evidence_supply_action(candidate)
    assert caught.value.reason == "relation_mismatch"


def test_membership_closure_is_bounded_sorted_and_duplicate_free() -> None:
    mapping = _sample("V25")
    mapping["entries"] = [_sample("V26", 0), _sample("V26", 1)]
    mapping["entry_count"] = 2
    mapping = _seal("V25", mapping)
    rows = tuple(CLASS_BY_V["V26"].from_mapping(item) for item in mapping["entries"])
    pages = (decision._MembershipPage("epoch.1", (0, "0"), rows, None),)
    value = decision.rw0_c_decision_membership_closure(mapping, pages=pages)
    assert tuple((entry.kind_rank, entry.membership_ref) for entry in value.entries) == tuple(
        (entry.kind_rank, entry.membership_ref) for entry in rows
    )
    duplicate = dict(mapping)
    duplicate["entries"] = [mapping["entries"][0], mapping["entries"][0]]
    duplicate = _seal("V25", duplicate)
    with pytest.raises(evidence._PostExecutionContractViolation) as caught:
        CLASS_BY_V["V25"].from_mapping(duplicate)
    assert caught.value.reason == "duplicate_entry"


def test_snapshot_and_proposal_currentness_keep_five_distinct_components() -> None:
    snapshot = CLASS_BY_V["V27"].from_mapping(_sample("V27"))
    currentness = CLASS_BY_V["V29"].from_mapping(_sample("V29"))
    assert tuple(source.role for source in snapshot.external_sources) == CURRENTNESS_COMPONENTS
    assert tuple(component.component for component in currentness.components) == CURRENTNESS_COMPONENTS
    assert set(CURRENTNESS_COMPONENTS) == {"validation", "review", "policy", "risk_profile", "risk_binding"}


def test_v32_active_stop_precedence_outcomes_are_exact() -> None:
    stop_mapping = _sample("V20")
    stop_mapping.update(
        global_stop_ref="active-stop.1",
        global_stop_state="active",
        global_stop_version=8,
        global_stop_stop_id="active-stop.1",
        global_stop_issued_at="2026-09-30T11:59:45Z",
        global_stop_issuer_ref="operator.1",
        global_stop_reason_class="operator_stop",
        global_stop_operator_decision_ref="operator-decision.1",
    )
    stop = CLASS_BY_V["V20"].from_mapping(_seal("V20", stop_mapping))
    snapshot_mapping = _sample("V27", 1)
    snapshot_mapping["global_stop_ref"] = stop.global_stop_ref
    snapshot_mapping["global_stop_digest"] = stop.global_stop_digest
    snapshot = CLASS_BY_V["V27"].from_mapping(_seal("V27", snapshot_mapping))
    mapping = _sample("V32")
    mapping["snapshot_ref"] = snapshot.snapshot_ref
    mapping["snapshot_digest"] = snapshot.snapshot_digest
    mapping["global_stop_ref"] = stop.global_stop_ref
    mapping["global_stop_digest"] = stop.global_stop_digest
    entries = []
    for branch, applicability, effect in BRANCHES:
        entries.append({
            "branch": branch,
            "applicability": applicability,
            "governed_effect_class": effect,
            "result": "deny" if applicability == "governed" else "permit",
            "reason": "global_stop_active" if applicability == "governed" else "halt_only_stop_checked",
        })
    mapping["entries"] = entries
    mapping = _seal("V32", mapping)
    value = decision.evaluate_rw0_c_decision_time_global_stop_branches(
        mapping,
        snapshot=snapshot,
        global_stop_snapshot=stop,
    )
    assert tuple(entry.result for entry in value.entries) == ("deny", "deny", "deny", "permit", "permit")


def test_v40_proves_only_operational_separation() -> None:
    value = _reviewer_separation_action(_sample("V40"))
    assert (value.status, value.reason) == ("separate", "governed_review_graph_separate")
    forbidden_claims = {
        "identity_authenticated", "person_ref", "provider_ref", "account_ref", "credential_ref",
        "host_ref", "organization_ref", "principal_ref", "source_authenticity", "quality", "permission",
    }
    assert forbidden_claims.isdisjoint(value.to_mapping())


def test_finite_backlog_adapter_is_one_way_and_does_not_collapse_ids() -> None:
    source_mapping = _sample("V19")
    source_mapping["development_work_item_ref"] = "development-item.1"
    source_mapping["backlog_work_item_id"] = "backlog-item.99"
    source_mapping = _seal("V19", source_mapping)
    profile, binding = adapter.finite_backlog_risk_source_projection(
        source_mapping,
        evaluated_at="2030-01-02T00:00:00Z",
        expires_at="2030-01-03T00:00:00Z",
    )
    assert binding.development_work_item_ref == "development-item.1"
    assert source_mapping["backlog_work_item_id"] == "backlog-item.99"
    assert binding.development_work_item_ref != source_mapping["backlog_work_item_id"]
    assert profile.external_authority_claim is False
    adapter_source = (ROOT / "src/ge_nwp_coordinator/_finite_backlog_risk_source_adapter.py").read_text()
    assert "backlog import" not in adapter_source


def test_policy_and_decision_matrix_reason_vocabularies_are_distinct() -> None:
    expected = {
        "V17": ("policy_permits", "halt_only_policy_not_applicable"),
        "V18": ("risk_lane_permits", "halt_only_risk_not_applicable"),
        "V31": ("authority_verified_current", "halt_only_authority_not_applicable"),
        "V32": ("global_stop_clear", "halt_only_stop_checked"),
        "V33": ("source_effect_within_current_ceilings", "halt_only_ceiling_not_applicable"),
    }
    for v_number, reasons in expected.items():
        value = CLASS_BY_V[v_number].from_mapping(_sample(v_number))
        assert (value.entries[0].reason, value.entries[-1].reason) == reasons


EQUALITY_RECORD_IDS = tuple(
    record_id for record_id in _TEST_RECORDS if record_id.startswith("equality.")
)


@pytest.mark.parametrize("record_id", EQUALITY_RECORD_IDS)
def test_each_of_36_cross_boundary_equalities_executes_exact_typed_values(record_id: str) -> None:
    expected = _TEST_RECORDS[record_id]
    rank = expected["role_rank"]
    index = rank - 5
    assert len(EQUALITY_RECORD_IDS) == 36

    t1 = CLASS_BY_V["V03"].from_mapping(_sample("V03", index))
    model_input = CLASS_BY_V["V06"].from_mapping(_sample("V06", index))
    projection_entry = CLASS_BY_V["V23"].from_mapping(_sample("V23", index))
    exact_supply = CLASS_BY_V["V11"].from_mapping(_sample("V11", index))
    resolved = CLASS_BY_V["V24"].from_mapping(_sample("V24", index))

    boundary = expected["boundary"]
    if boundary == "T1_context":
        schema, ref, digest = t1.typed_schema_id, t1.typed_value_ref, t1.typed_value_digest
    elif boundary == "model_input":
        schema, ref, digest = (
            model_input.typed_schema_id,
            model_input.typed_value_ref,
            model_input.typed_value_digest,
        )
    elif boundary == "Section41_projection":
        schema, ref, digest = (
            t1.typed_schema_id,
            projection_entry.evidence_ref,
            projection_entry.evidence_digest,
        )
    else:
        assert boundary == "exact_resupply"
        schema, ref, digest = (
            exact_supply.typed_schema_id,
            exact_supply.typed_value_ref,
            exact_supply.typed_value_digest,
        )

    assert (t1.role, t1.role_rank, t1.ordinal) == (expected["role"], rank, 0)
    assert (schema, ref, digest) == (
        expected["schema_equality"],
        expected["ref_equality"],
        expected["digest_equality"],
    )
    assert (
        model_input.typed_schema_id,
        model_input.typed_value_ref,
        model_input.typed_value_digest,
    ) == (schema, ref, digest)
    assert (
        projection_entry.evidence_ref,
        projection_entry.evidence_digest,
    ) == (ref, digest)
    assert (
        exact_supply.typed_schema_id,
        exact_supply.typed_value_ref,
        exact_supply.typed_value_digest,
    ) == (schema, ref, digest)
    assert (
        resolved.typed_schema_id,
        resolved.typed_value_ref,
        resolved.typed_value_digest,
    ) == (schema, ref, digest)

    assert projection_entry.proposal_phase == expected["phase_equality"]
    assert (resolved.lineage_context_ref, resolved.lineage_context_digest) == (
        expected["lineage_context_ref"], expected["lineage_context_digest"]
    )
    assert {
        t1.model_input_posture,
        model_input.model_input_posture,
        exact_supply.model_input_posture,
        resolved.model_input_posture,
    } == {expected["privacy_posture"]}
    assert (t1.source_profile_ref, t1.source_profile_digest) == (
        expected["profile_ref_equality"], expected["profile_digest_equality"]
    )
    assert (
        t1.source_binding_schema_id,
        t1.source_binding_ref,
        t1.source_binding_digest,
    ) == (
        expected["source_binding_schema_equality"],
        expected["source_binding_ref_equality"],
        expected["source_binding_digest_equality"],
    )
    assert (t1.direct_c1_membership_ref, t1.direct_c1_membership_digest) == (
        expected["c1_membership_ref_equality"], expected["c1_membership_digest_equality"]
    )
    assert resolved.result == "resolved" and resolved.reason == "exact_role_binding"
    assert exact_supply.typed_canonical_value is not None
    assert expected["proposal_evidence_exact"] is True
    assert expected["resolution_exact"] is True
    assert expected["supply_exact"] is True
    assert expected["future_retention_rule"].startswith("retain only safe projection")
