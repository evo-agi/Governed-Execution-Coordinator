from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sqlite3

import pytest

import ge_nwp_coordinator._cognitive_proposal_row_values as row_values
import ge_nwp_coordinator._cognitive_proposal_semantic_values as semantic
import ge_nwp_coordinator._cognitive_proposal_value_support as support
import ge_nwp_coordinator._development_pre_execution_plan_disposition_contracts as contracts
import ge_nwp_coordinator._sqlite_development_pre_execution_plan_disposition as runtime
from ge_nwp_coordinator._cognitive_proposal_value_support import (
    _CognitiveProposalContractViolation,
    _canonical_bytes,
    _exact_equal,
    _require_nonnegative_integer,
    _require_safe_ref,
)
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError,
    SQLiteMutationStoreErrorCode,
)
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_c2b3d_private_atomic_author_effect_establishment import PATHS
from test_section41_private_atomic_pre_execution_plan_disposition import (
    _artifact,
    _install_section41_downstream_counters,
    _projection,
    _seal,
    make_section41_fixture,
)
from test_remote_worker_pre_execution_planning_contract import (
    _build_repaired_physical_family,
    _repaired_row_digest,
)


class _EqualityBomb:
    def __eq__(self, other: object) -> bool:
        raise AssertionError("hostile equality executed")

    def __hash__(self) -> int:
        raise AssertionError("hostile hash executed")


def _hostile_class_spoof(
    trusted_type: type[object],
) -> tuple[type[object], dict[str, int]]:
    callbacks = {"hash": 0, "equality": 0, "conversion": 0}

    class CollisionMeta(type):
        def __hash__(cls) -> int:
            callbacks["hash"] += 1
            return type.__hash__(trusted_type)

        def __eq__(cls, other: object) -> bool:
            callbacks["equality"] += 1
            return other is trusted_type

    def to_mapping(self: object) -> dict[str, object]:
        callbacks["conversion"] += 1
        raise AssertionError("hostile conversion executed")

    spoof = CollisionMeta(
        trusted_type.__name__,
        (),
        {"__module__": trusted_type.__module__, "to_mapping": to_mapping},
    )
    callbacks.update(hash=0, equality=0, conversion=0)
    return spoof, callbacks


def test_private_modules_export_nothing() -> None:
    assert support.__all__ == ()
    assert semantic.__all__ == ()
    assert row_values.__all__ == ()
    assert contracts.__all__ == ()
    assert runtime.__all__ == ()


def test_safe_model_configuration_is_digest_backed_and_privacy_safe() -> None:
    value = _seal(
        semantic.ModelConfigurationSafeV1,
        {
            "schema_id": semantic._SCHEMAS["model_configuration"],
            "model_configuration_ref": "model-configuration-safe",
            "model_contract_ref": "model-contract-reasoning",
            "model_contract_digest": "1" * 64,
            "implementation_family": "configured_reasoning_model",
            "capability_profile_ref": "capability-profile-safe",
            "capability_profile_digest": "2" * 64,
            "input_policy_ref": "input-policy-safe",
            "input_policy_digest": "3" * 64,
            "output_policy_ref": "output-policy-safe",
            "output_policy_digest": "4" * 64,
        },
    )
    assert value.model_configuration_digest == value.computed_digest()
    encoded = _canonical_bytes(value.to_mapping())
    assert b"credential" not in encoded
    assert b"endpoint" not in encoded
    assert repr(value) == "<ModelConfigurationSafeV1>"


def test_private_artifact_enforces_substantive_closed_graph() -> None:
    artifact = _artifact(
        marker="pure",
        proposal_ref="proposal-pure",
        context_ref="context-pure",
        authorized_paths=PATHS,
    )
    assert artifact.artifact_digest == artifact.computed_digest()
    assert artifact.affected_authorized_paths == PATHS
    assert len(artifact.required_evidence_and_prerequisites) == 14
    assert artifact.proposed_work_units[0].required_evidence_roles == (
        semantic._EVIDENCE_ROLES
    )


def test_hostile_scalars_containers_cycles_and_equality_are_finite() -> None:
    with pytest.raises(_CognitiveProposalContractViolation):
        _require_nonnegative_integer(True)
    with pytest.raises(_CognitiveProposalContractViolation):
        _require_safe_ref("connector-secret")
    cyclic: dict[str, object] = {}
    cyclic["cycle"] = cyclic
    with pytest.raises(_CognitiveProposalContractViolation) as caught:
        _canonical_bytes(cyclic)
    assert caught.value.reason == "canonical_value_invalid"
    assert _exact_equal(_EqualityBomb(), _EqualityBomb()) is False
    with pytest.raises(_CognitiveProposalContractViolation):
        semantic.ModelProposalEvidenceSetV1(
            evidence_set_ref="evidence-set-hostile",
            proposal_ref="proposal-hostile",
            proposal_phase="pre_execution_plan",
            entries=(_EqualityBomb(),),
            evidence_set_digest="0" * 64,
        )


def test_semantic_value_subclassing_is_disabled() -> None:
    with pytest.raises(TypeError):

        class _Forbidden(semantic.ModelConfigurationSafeV1):
            pass


@pytest.mark.parametrize(
    "value_type",
    (
        semantic.ModelConfigurationSafeV1,
        semantic.PreExecutionWorkUnitV1,
        semantic.ModelProposalEvidenceSetV1,
        semantic.PreExecutionProposalSelectionBundleV1,
    ),
)
def test_concrete_semantic_class_name_and_module_spoofs_are_rejected(
    value_type: type[object],
) -> None:
    with pytest.raises(TypeError):
        type(
            value_type.__name__,
            (value_type,),
            {"__module__": semantic.__name__},
        )


@pytest.mark.parametrize(
    "trusted_type",
    (
        semantic.ModelConfigurationSafeV1,
        semantic.PreExecutionWorkUnitV1,
        semantic.PreExecutionPlanningContextV1,
    ),
)
def test_semantic_registry_rejects_equal_hash_collisions_by_identity_without_callbacks(
    trusted_type: type[object],
) -> None:
    spoof_type, callbacks = _hostile_class_spoof(trusted_type)
    spoof = spoof_type()
    assert spoof_type.__name__ == trusted_type.__name__
    assert spoof_type.__module__ == trusted_type.__module__

    with pytest.raises(_CognitiveProposalContractViolation):
        semantic._reconstruct_exact_semantic_member(spoof, set(), 0)
    with pytest.raises(_CognitiveProposalContractViolation):
        semantic._reconstruct_exact_semantic_value(spoof, trusted_type)
    with pytest.raises(_CognitiveProposalContractViolation):
        support._validate_canonical_value(spoof)
    assert _exact_equal(spoof, spoof) is False
    assert callbacks == {"hash": 0, "equality": 0, "conversion": 0}


_EFFECT_JSON_FIELDS = (
    "attempt_fence_allowed_effect_classes_json",
    "effect_fence_allowed_effect_classes_json",
)


@pytest.mark.parametrize("field", _EFFECT_JSON_FIELDS)
@pytest.mark.parametrize(
    "encoded",
    (
        '["author_candidate"]',
        '["author_candidate","review_candidate","validate_candidate"]',
        (
            '["author_candidate","cancel_effect","local_git_commit",'
            '"review_candidate","validate_candidate"]'
        ),
    ),
)
def test_effect_class_json_valid_canonical_subsets_have_semantic_row_parity(
    field: str,
    encoded: str,
) -> None:
    reconstructed_classes = support._require_canonical_effect_class_json(encoded)
    assert type(reconstructed_classes) is tuple
    assert all(type(member) is str for member in reconstructed_classes)
    member = next(
        item
        for item in _build_repaired_physical_family(False)["physical_rows"]
        if item["role"] == "planning_context"
    )
    semantic_mapping = dict(member["values"])
    semantic_mapping[field] = encoded
    semantic_value = _seal(semantic.PreExecutionPlanningContextV1, semantic_mapping)

    row_mapping = dict(member["values"])
    row_mapping[field] = encoded
    row_mapping["planning_context_digest"] = _repaired_row_digest(
        member["table"], row_mapping
    )
    row_value = row_values._row_value_from_mapping(member["table"], row_mapping)
    assert object.__getattribute__(semantic_value, field) == encoded
    assert object.__getattribute__(row_value, field) == encoded


class _EffectJSONTextSubclass(str):
    pass


@pytest.mark.parametrize("field", _EFFECT_JSON_FIELDS)
@pytest.mark.parametrize(
    "encoded",
    (
        "not-json",
        "[]",
        '["unknown_effect"]',
        '["author_candidate","author_candidate"]',
        '["validate_candidate","author_candidate"]',
        "[1]",
        "{}",
        '"author_candidate"',
        '["author_candidate", "validate_candidate"]',
        '["\\u0061uthor_candidate"]',
        '["author_candidate"] trailing',
        '["\ud800"]',
        _EffectJSONTextSubclass('["author_candidate"]'),
    ),
)
def test_effect_class_json_invalid_encodings_fail_finitely_with_semantic_row_parity(
    field: str,
    encoded: object,
) -> None:
    member = next(
        item
        for item in _build_repaired_physical_family(False)["physical_rows"]
        if item["role"] == "planning_context"
    )
    mapping = dict(member["values"])
    mapping[field] = encoded

    with pytest.raises(_CognitiveProposalContractViolation) as semantic_failure:
        semantic.PreExecutionPlanningContextV1(**mapping)
    with pytest.raises(_CognitiveProposalContractViolation) as row_failure:
        row_values._row_value_from_mapping(member["table"], mapping)

    assert semantic_failure.value.reason == "invalid_field_value"
    assert row_failure.value.reason == "physical_family_row_digest_mismatch"
    for failure in (semantic_failure.value, row_failure.value):
        assert failure.__cause__ is None
        assert failure.__context__ is None
        assert encoded not in failure.args


def test_section42_reports_identity_only_dispatch_and_shared_effect_json_without_rewriting_section41() -> None:
    document = (
        Path(__file__).parents[1] / ".docs" / "c2b-durable-development-state.md"
    ).read_bytes()
    section41_start = document.index(b"## 41. ")
    section42_start = document.index(b"## 42. ", section41_start)
    section41 = document[section41_start : section42_start - 1]
    assert len(section41) == 522_877
    assert sha256(section41).hexdigest() == (
        "1198a3f56554cc6659572686669a95a62c04cd5789a149b4655d68fbf870c350"
    )
    section42 = document[section42_start:].decode("utf-8")
    assert "Every attacker-derived class object is compared" in section42
    assert "only by an iterative `is` check" in section42
    assert "one canonical C2A effect-class JSON" in section42
    assert "Both planning-context\neffect-class JSON fields use the same" in section42
    assert "without invoking metaclass hash/equality" in section42


@pytest.mark.parametrize(
    ("role", "field", "replacement", "reason"),
    (
        ("planning_context", "program_version_number", 0, "invalid_field_value"),
        ("planning_context", "attempt_number", 0, "invalid_field_value"),
        (
            "planning_context",
            "base_git_object_format",
            "sha256",
            "invalid_field_value",
        ),
        (
            "planning_context",
            "authority_selection_observation_schema_id",
            "governed-execution.wrong-authority-observation.v1",
            "invalid_field_value",
        ),
        (
            "source_invocation",
            "context_schema_id",
            "governed-execution.wrong-context.v1",
            "invalid_field_value",
        ),
        (
            "pre_execution_plan_projection",
            "work_unit_count",
            33,
            "safe_projection_derivation_mismatch",
        ),
    ),
)
def test_standalone_semantic_values_enforce_field_specific_grammar(
    role: str,
    field: str,
    replacement: object,
    reason: str,
) -> None:
    physical = _build_repaired_physical_family(False)["physical_rows"]
    member = next(item for item in physical if item["role"] == role)
    value_type = {
        "planning_context": semantic.PreExecutionPlanningContextV1,
        "source_invocation": semantic.ModelSourceInvocationV1,
        "pre_execution_plan_projection": semantic.PreExecutionPlanSafeProjectionV1,
    }[role]
    mapping = dict(member["values"])
    if role == "pre_execution_plan_projection":
        mapping["allowed_effect_classes"] = tuple(
            json.loads(mapping["allowed_effect_classes"])
        )
    mapping[field] = replacement
    with pytest.raises(_CognitiveProposalContractViolation) as caught:
        _seal(value_type, mapping)
    assert caught.value.reason == reason


def _shared_exact_tuple_dag() -> tuple[object, ...]:
    node: tuple[object, ...] = ("leaf",)
    for _level in range(8):
        node = (node,) * 8
    return node


def test_exact_semantic_reconstruction_exhausts_the_shared_budget_deterministically() -> None:
    hostile = _shared_exact_tuple_dag()
    budget = semantic._SemanticReconstructionBudget(
        semantic._MAX_SEMANTIC_RECONSTRUCTION_WORK
    )

    with pytest.raises(_CognitiveProposalContractViolation) as caught:
        semantic._reconstruct_exact_semantic_member(hostile, set(), 0, budget)

    assert caught.value.reason == "private_plan_nested_collection_invalid"
    assert budget.consumed == semantic._MAX_SEMANTIC_RECONSTRUCTION_WORK
    assert budget.remaining == 0


def _maximum_cardinality_artifact(
    template: semantic.PreExecutionPlanArtifactV1,
) -> semantic.PreExecutionPlanArtifactV1:
    work_refs = tuple(f"w{index:02d}" for index in range(32))
    output_refs = tuple(f"o{index:02d}" for index in range(32))
    validation_refs = tuple(f"v{index:02d}" for index in range(32))
    prerequisite_refs = tuple(f"p{index:02d}" for index in range(32))
    stop_refs = tuple(f"s{index:02d}" for index in range(16))
    paths = tuple(f"f/{index:02d}" for index in range(64))
    prerequisite_roles = tuple(
        semantic._EVIDENCE_ROLES[
            min(
                index * len(semantic._EVIDENCE_ROLES) // len(prerequisite_refs),
                len(semantic._EVIDENCE_ROLES) - 1,
            )
        ]
        for index in range(len(prerequisite_refs))
    )
    work_units = tuple(
        semantic.PreExecutionWorkUnitV1(
            ordinal=index,
            work_unit_ref=work_refs[index],
            action_kind="analyze",
            summary="A",
            depends_on_work_unit_refs=work_refs[:index],
            authorized_path_ordinals=tuple(range(len(paths))),
            expected_output_refs=(output_refs[index],),
            validation_refs=validation_refs,
            required_evidence_roles=semantic._EVIDENCE_ROLES,
            prerequisite_refs=prerequisite_refs,
            stop_condition_refs=stop_refs,
        )
        for index in range(len(work_refs))
    )
    outputs = tuple(
        semantic.PreExecutionExpectedOutputV1(
            output_ref=output_refs[index],
            owner_work_unit_ref=work_refs[index],
            output_kind="source_change",
            description="A",
        )
        for index in range(len(output_refs))
    )
    validations = tuple(
        semantic.PreExecutionValidationStepV1(
            ordinal=index,
            validation_ref=validation_refs[index],
            work_unit_refs=work_refs,
            validation_kind="focused_test",
            target="A",
            success_criterion="A",
        )
        for index in range(len(validation_refs))
    )
    artifact = _seal(
        semantic.PreExecutionPlanArtifactV1,
        {
            "schema_id": semantic._SCHEMAS["artifact"],
            "artifact_ref": template.artifact_ref,
            "proposal_ref": template.proposal_ref,
            "proposal_phase": "pre_execution_plan",
            "planning_context_ref": template.planning_context_ref,
            "implementation_strategy": tuple(f"S{index}" for index in range(8)),
            "proposed_work_units": work_units,
            "affected_authorized_paths": paths,
            "expected_outputs": outputs,
            "validation_strategy": validations,
            "material_assumptions": tuple(
                semantic.PreExecutionAssumptionV1(
                    assumption_ref=f"a{index:02d}", statement="A"
                )
                for index in range(16)
            ),
            "risks_and_uncertainties": tuple(
                semantic.PreExecutionRiskV1(
                    risk_ref=f"r{index:02d}",
                    risk_kind="correctness",
                    description="A",
                    mitigation="A",
                    materiality="material",
                    affected_work_unit_refs=work_refs,
                )
                for index in range(16)
            ),
            "required_evidence_and_prerequisites": tuple(
                semantic.PreExecutionPrerequisiteV1(
                    prerequisite_ref=prerequisite_refs[index],
                    evidence_role=prerequisite_roles[index],
                    requirement="A",
                )
                for index in range(len(prerequisite_refs))
            ),
            "stop_or_replan_conditions": tuple(
                semantic.PreExecutionStopConditionV1(
                    stop_condition_ref=stop_refs[index], statement="A"
                )
                for index in range(len(stop_refs))
            ),
            "proposed_resource_and_effect_use": (
                semantic.ProposedResourceAndEffectUseV1(
                    allowed_effect_classes=semantic._EFFECT_CLASSES,
                    **{name: 0 for name in semantic._CEILING_FIELDS},
                )
            ),
            "recommendation": "select_for_dispatch_gates",
            "reason_code": "plan.maximum_valid",
        },
    )
    return artifact  # type: ignore[return-value]


def _bundle_with_replaced_artifact(
    original: semantic.PreExecutionProposalSelectionBundleV1,
    artifact: semantic.PreExecutionPlanArtifactV1,
) -> semantic.PreExecutionProposalSelectionBundleV1:
    projection = _projection(
        artifact,
        original.planning_context,
        original.model_proposal.proposal_ref,
    )
    source_mapping = original.source_invocation.to_mapping()
    source_mapping["artifact_digest"] = artifact.artifact_digest
    source = _seal(semantic.ModelSourceInvocationV1, source_mapping)
    binding_mapping = original.private_artifact_binding.to_mapping()
    binding_mapping.update(
        {
            "artifact_digest": artifact.artifact_digest,
            "artifact_canonical_byte_length": len(
                _canonical_bytes(artifact.to_mapping())
            ),
            "safe_projection_digest": projection.safe_projection_digest,
        }
    )
    binding = _seal(semantic.PrivateProposalArtifactBindingV1, binding_mapping)
    proposal_mapping = original.model_proposal.to_mapping()
    proposal_mapping.update(
        {
            "source_invocation_digest": source.source_invocation_digest,
            "artifact_digest": artifact.artifact_digest,
            "safe_projection_digest": projection.safe_projection_digest,
        }
    )
    proposal = _seal(semantic.PreExecutionModelProposalV1, proposal_mapping)
    return semantic.PreExecutionProposalSelectionBundleV1(
        authority_observation=original.authority_observation,
        authority_expected_binding=original.authority_expected_binding,
        attempt_fence=original.attempt_fence,
        effect_fence=original.effect_fence,
        planning_context=original.planning_context,
        source_invocation=source,
        private_artifact_binding=binding,
        private_artifact=artifact,
        safe_projection=projection,
        evidence_bindings=original.evidence_bindings,
        evidence_set=original.evidence_set,
        model_proposal=proposal,
    )


def test_maximum_cardinality_section41_artifact_and_bundle_remain_accepted(
    tmp_path: Path,
) -> None:
    fixture = make_section41_fixture(
        tmp_path,
        suffix="maximum-semantic-graph",
        readiness_present=True,
    )
    artifact = _maximum_cardinality_artifact(fixture.bundle.private_artifact)
    bundle = _bundle_with_replaced_artifact(fixture.bundle, artifact)

    assert len(artifact.implementation_strategy) == 8
    assert len(artifact.proposed_work_units) == 32
    assert len(artifact.affected_authorized_paths) == 64
    assert len(artifact.expected_outputs) == 32
    assert len(artifact.validation_strategy) == 32
    assert len(artifact.material_assumptions) == 16
    assert len(artifact.risks_and_uncertainties) == 16
    assert len(artifact.required_evidence_and_prerequisites) == 32
    assert len(artifact.stop_or_replan_conditions) == 16
    assert (
        artifact.proposed_resource_and_effect_use.allowed_effect_classes
        == semantic._EFFECT_CLASSES
    )
    assert len(_canonical_bytes(artifact.to_mapping())) <= 65_536
    budget = semantic._SemanticReconstructionBudget(
        semantic._MAX_DECLARED_SEMANTIC_GRAPH_WORK
    )
    exact_member = semantic._reconstruct_exact_semantic_member(
        bundle, set(), 0, budget
    )
    assert budget.consumed == semantic._MAX_DECLARED_SEMANTIC_GRAPH_WORK
    assert budget.remaining == 0
    assert exact_member.to_mapping() == bundle.to_mapping()
    reconstructed = semantic._reconstruct_exact_semantic_value(
        bundle, semantic.PreExecutionProposalSelectionBundleV1
    )
    assert reconstructed.to_mapping() == bundle.to_mapping()
    fixture.author.writer.close()


@pytest.mark.parametrize(
    "hostile_location", ("private_artifact", "attempt_fence", "effect_fence")
)
def test_writer_receipt_miss_rejects_shared_dag_before_clock_dml_commit_or_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    hostile_location: str,
) -> None:
    suffix = {
        "private_artifact": "dag-art",
        "attempt_fence": "dag-attempt",
        "effect_fence": "dag-effect",
    }[hostile_location]
    fixture = make_section41_fixture(
        tmp_path, suffix=suffix
    )
    retained_probe = fixture.recovery_probe
    hostile = _shared_exact_tuple_dag()
    if hostile_location == "private_artifact":
        object.__setattr__(
            fixture.bundle.private_artifact,
            "implementation_strategy",
            hostile,
        )
    else:
        object.__setattr__(
            object.__getattribute__(fixture.bundle, hostile_location),
            "_path_ceiling",
            hostile,
        )
    calls = _install_section41_downstream_counters(monkeypatch)

    with pytest.raises(SQLiteMutationStoreError) as caught:
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            retained_probe,
        )

    assert caught.value.error_class == (
        SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value
    )
    assert calls == {
        "current": 0,
        "clock": 0,
        "result": 0,
        "dml": 0,
        "commit": 0,
    }
    connection = sqlite3.connect(fixture.author.location.database_path)
    try:
        assert sum(
            connection.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
            for table in row_values._TABLE_ORDER
        ) == 0
    finally:
        connection.close()
    fixture.author.writer.close()
    replacement_writer = acquire_sqlite_writer_session(fixture.author.location)
    replacement_writer.close()
