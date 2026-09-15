from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from pathlib import Path

import pytest

import ge_nwp_coordinator._cognitive_proposal_semantic_values as semantic
import ge_nwp_coordinator._development_pre_execution_plan_disposition_contracts as contracts
import ge_nwp_coordinator._sqlite_development_pre_execution_plan_disposition as runtime
import ge_nwp_coordinator.sqlite_transition_transaction as transaction
from ge_nwp_coordinator._cognitive_proposal_value_support import (
    _canonical_bytes,
    _domain_separated_digest,
    _without_field,
)
from ge_nwp_coordinator._development_author_effect_establishment_contracts import (
    _development_author_effect_establishment_write_plan,
)
from ge_nwp_coordinator._development_pre_execution_plan_disposition_contracts import (
    PreExecutionPlanDispositionConflictReasonV1,
    PreExecutionPlanDispositionConflictV1,
    PreExecutionPlanDispositionResultV1,
    _record_command_from_ingress,
)
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError,
    SQLiteMutationStoreErrorCode,
)
from test_c2b3d_private_atomic_author_effect_establishment import (
    AuthorEffectFixture,
    make_author_effect_fixture,
)


DECISION_TIME = "2098-01-01T00:00:08Z"


@dataclass(frozen=True)
class Section41Fixture:
    author: AuthorEffectFixture
    bundle: semantic.PreExecutionProposalSelectionBundleV1
    identity: dict[str, object]
    mutation_ref: str
    command_digest: str

    @property
    def command(self) -> object:
        return _record_command_from_ingress(
            self.mutation_ref,
            self.command_digest,
            self.bundle,
            self.identity,
        )

    @property
    def recovery_probe(self) -> object:
        return self.author.writer._prepare_pre_execution_plan_disposition_recovery_probe(
            self.mutation_ref,
            self.command_digest,
            self.bundle,
            self.identity,
        )


def _seal(value_type: type[object], values: dict[str, object]) -> object:
    digest_field = value_type._DIGEST_FIELD  # type: ignore[attr-defined]
    domain = value_type._DOMAIN  # type: ignore[attr-defined]
    fields = dict(values)
    carrier = object.__new__(value_type)
    for name in value_type._FIELD_ORDER:  # type: ignore[attr-defined]
        object.__setattr__(
            carrier,
            name,
            fields.get(name, "0" * 64 if name == digest_field else None),
        )
    mapping = carrier.to_mapping()  # type: ignore[attr-defined]
    fields[digest_field] = _domain_separated_digest(
        domain,
        _without_field(mapping, digest_field),
    )
    return value_type(**fields)


def test_disposition_identity_rejects_hostile_keys_without_equality(
    tmp_path: Path,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="hostile-key")

    class HostileKey(str):
        __hash__ = str.__hash__

        def __eq__(self, other: object) -> bool:
            raise AssertionError("hostile equality executed")

    values = list(fixture.identity.items())
    hostile_identity = {
        HostileKey(values[0][0]): values[0][1],
        **dict(values[1:]),
    }
    with pytest.raises(Exception) as caught:
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            hostile_identity,
            fixture.recovery_probe,
        )
    assert type(caught.value).__name__ in {
        "SQLiteMutationStoreError",
        "_CognitiveProposalContractViolation",
    }
    fixture.author.writer.close()


def _head_revisions(author: AuthorEffectFixture) -> tuple[int, int]:
    connection = sqlite3.connect(author.location.database_path)
    try:
        program = connection.execute(
            "SELECT head_revision FROM development_program_heads "
            "WHERE program_ref = ?",
            (author.command.program_ref,),
        ).fetchone()
        work = connection.execute(
            "SELECT head_revision FROM development_work_item_heads "
            "WHERE program_ref = ? AND work_item_ref = ?",
            (author.command.program_ref, author.command.work_item_ref),
        ).fetchone()
        assert program is not None and work is not None
        return program[0], work[0]
    finally:
        connection.close()


def _artifact(
    *,
    marker: str,
    proposal_ref: str,
    context_ref: str,
    authorized_paths: tuple[str, ...],
) -> semantic.PreExecutionPlanArtifactV1:
    work_ref = f"planning-unit-{marker}"
    output_ref = f"planning-output-{marker}"
    validation_ref = f"planning-validation-{marker}"
    prerequisite_refs = tuple(
        f"planning-prerequisite-{marker}-{index:02d}" for index in range(14)
    )
    work = semantic.PreExecutionWorkUnitV1(
        ordinal=0,
        work_unit_ref=work_ref,
        action_kind="modify_authorized_path",
        summary="Implement the bounded proposal selection change.",
        depends_on_work_unit_refs=(),
        authorized_path_ordinals=tuple(range(len(authorized_paths))),
        expected_output_refs=(output_ref,),
        validation_refs=(validation_ref,),
        required_evidence_roles=semantic._EVIDENCE_ROLES,
        prerequisite_refs=prerequisite_refs,
        stop_condition_refs=(f"planning-stop-{marker}",),
    )
    output = semantic.PreExecutionExpectedOutputV1(
        output_ref=output_ref,
        owner_work_unit_ref=work_ref,
        output_kind="source_change",
        description="A bounded source change with focused evidence.",
    )
    validation = semantic.PreExecutionValidationStepV1(
        ordinal=0,
        validation_ref=validation_ref,
        work_unit_refs=(work_ref,),
        validation_kind="focused_test",
        target="Run focused Section 41 contract tests.",
        success_criterion="All focused assertions pass without warnings.",
    )
    prerequisites = tuple(
        semantic.PreExecutionPrerequisiteV1(
            prerequisite_ref=reference,
            evidence_role=role,
            requirement=f"Verify the required {role.replace('_', ' ')} evidence.",
        )
        for reference, role in zip(
            prerequisite_refs,
            semantic._EVIDENCE_ROLES,
            strict=True,
        )
    )
    values = {
        "schema_id": semantic._SCHEMAS["artifact"],
        "artifact_ref": f"private-plan-{marker}",
        "proposal_ref": proposal_ref,
        "proposal_phase": "pre_execution_plan",
        "planning_context_ref": context_ref,
        "implementation_strategy": (
            "Validate the supplied plan and persist one bounded disposition.",
        ),
        "proposed_work_units": (work,),
        "affected_authorized_paths": authorized_paths,
        "expected_outputs": (output,),
        "validation_strategy": (validation,),
        "material_assumptions": (
            semantic.PreExecutionAssumptionV1(
                assumption_ref=f"planning-assumption-{marker}",
                statement=("The durable lineage remains unchanged during selection."),
            ),
        ),
        "risks_and_uncertainties": (
            semantic.PreExecutionRiskV1(
                risk_ref=f"planning-risk-{marker}",
                risk_kind="correctness",
                description="A relation mismatch could select the wrong proposal.",
                mitigation="Bind every proposal row to the exact current lineage.",
                materiality="material",
                affected_work_unit_refs=(work_ref,),
            ),
        ),
        "required_evidence_and_prerequisites": prerequisites,
        "stop_or_replan_conditions": (
            semantic.PreExecutionStopConditionV1(
                stop_condition_ref=f"planning-stop-{marker}",
                statement=(
                    "Stop if any current authority or lineage relation changes."
                ),
            ),
        ),
        "proposed_resource_and_effect_use": (
            semantic.ProposedResourceAndEffectUseV1(
                allowed_effect_classes=("author_candidate",),
                **{name: 0 for name in semantic._CEILING_FIELDS},
            )
        ),
        "recommendation": "select_for_dispatch_gates",
        "reason_code": "plan.bounded_contract_change",
    }
    return _seal(semantic.PreExecutionPlanArtifactV1, values)  # type: ignore[return-value]


def _projection(
    artifact: semantic.PreExecutionPlanArtifactV1,
    context: semantic.PreExecutionPlanningContextV1,
    proposal_ref: str,
) -> semantic.PreExecutionPlanSafeProjectionV1:
    binding_shell = object.__new__(semantic.PrivateProposalArtifactBindingV1)
    proposal_shell = object.__new__(semantic.PreExecutionModelProposalV1)
    object.__setattr__(proposal_shell, "proposal_ref", proposal_ref)
    mapping = semantic._derive_pre_execution_safe_projection_mapping(
        artifact,
        binding_shell,
        context,
        proposal_shell,
    )
    return semantic.PreExecutionPlanSafeProjectionV1(**mapping)


def _build_bundle(
    author: AuthorEffectFixture,
    *,
    marker: str,
    readiness_present: bool,
) -> semantic.PreExecutionProposalSelectionBundleV1:
    command = author.command
    author_plan = _development_author_effect_establishment_write_plan(
        command,
        author._section41_author_result.transaction_timestamp,
    )
    attempt = command.attempt_fence
    effect = command.effect_fence
    work_spec = command.work_spec_safe_projection
    observation = _seal(
        semantic.AuthoritySelectionObservationSafeV1,
        {
            "schema_id": semantic._SCHEMAS["authority_observation"],
            "authority_observation_ref": f"authority-observation-{marker}",
            "authoritative_subject_kind": "effect_intent",
            "authoritative_subject_ref": command.effect_intent_ref,
            "program_ref": command.program_ref,
            "semantic_attempt_ref": command.semantic_attempt_ref,
            "candidate_ref": command.candidate_ref,
            "effect_intent_ref": command.effect_intent_ref,
            "author_command_ref": command.command_ref,
            "attempt_fence_ref": command.attempt_fence_ref,
            "effect_fence_ref": command.effect_fence_ref,
            "delivery_attempt_ref": command.delivery_attempt_ref,
            "authority_evaluation_ref": command.authority_evaluation_ref,
            "authority_evaluation_digest": (
                author_plan.authority_evaluation.authority_evaluation_digest
            ),
            "observation_state": "pending",
            "observation_version": 1,
            "authority_observation_issued_at": "2098-01-01T00:00:01Z",
            "authority_observation_expires_at": "2098-12-01T00:00:00Z",
            "source_authority_ref": f"external-authority-{marker}",
            "verification_evidence_ref": f"authority-proof-{marker}",
            "verification_evidence_digest": "a" * 64,
        },
    )
    expected = semantic.AuthorityExpectedBinding(
        **{
            name: object.__getattribute__(observation, name)
            for name in semantic._AUTHORITY_EXPECTED_BINDING_FIELDS
        }
    )
    program_revision, work_revision = _head_revisions(author)
    readiness_ref = f"qualified-host-{marker}" if readiness_present else None
    readiness_digest = "f" * 64 if readiness_present else None
    context = _seal(
        semantic.PreExecutionPlanningContextV1,
        {
            "schema_id": semantic._SCHEMAS["planning_context"],
            "planning_context_ref": f"planning-context-{marker}",
            "program_ref": command.program_ref,
            "program_version_ref": command.program_version_ref,
            "program_version_number": command.program_version_number,
            "accepted_intent_revision_ref": command.accepted_intent_revision_ref,
            "work_item_ref": command.work_item_ref,
            "work_item_revision_ref": command.work_item_revision_ref,
            "semantic_attempt_ref": command.semantic_attempt_ref,
            "semantic_attempt_digest": author_plan.semantic_attempt.semantic_attempt_digest,
            "attempt_number": command.attempt_number,
            "candidate_ref": command.candidate_ref,
            "basis_decision_ref": command.basis_decision_ref,
            "basis_decision_digest": command.basis_decision_digest,
            "work_spec_ref": work_spec.work_spec_ref,
            "work_spec_digest": work_spec.work_spec_digest,
            "work_spec_safe_projection_digest": work_spec.safe_projection_digest,
            "effect_intent_ref": command.effect_intent_ref,
            "effect_intent_digest": author_plan.effect_intent.effect_intent_digest,
            "author_command_ref": command.command_ref,
            "author_command_digest": author_plan.author_command.command_digest,
            "standing_grant_ref": attempt.parent_standing_grant_ref,
            "standing_grant_digest": attempt.parent_standing_grant_digest,
            "attempt_authorization_ref": attempt.attempt_authorization_ref,
            "attempt_authorization_digest": attempt.attempt_authorization_digest,
            "effect_authorization_ref": effect.effect_authorization_ref,
            "effect_authorization_digest": effect.effect_authorization_digest,
            "attempt_fence_ref": attempt.attempt_fence_ref,
            "attempt_fence_digest": attempt.attempt_fence_digest,
            "attempt_fence_allowed_effect_classes_json": _canonical_bytes(
                tuple(attempt.allowed_effect_classes)
            ).decode("utf-8"),
            "attempt_fence_expires_at": attempt.expires_at,
            "effect_fence_ref": effect.effect_fence_ref,
            "effect_fence_digest": effect.effect_fence_digest,
            "effect_fence_allowed_effect_classes_json": _canonical_bytes(
                (effect.effect_class,)
            ).decode("utf-8"),
            "effect_fence_expires_at": effect.expires_at,
            "delivery_attempt_ref": command.delivery_attempt_ref,
            "delivery_envelope_digest": (
                author_plan.delivery_attempt.delivery_envelope_digest
            ),
            "delivery_attempt_digest": author_plan.delivery_attempt.delivery_attempt_digest,
            "expected_program_head_revision": program_revision,
            "expected_work_item_head_revision": work_revision,
            "expected_effect_head_fence_ref": (
                author_plan.effect_head.current_effect_fence_ref
            ),
            "expected_effect_head_revision": author_plan.effect_head.head_revision,
            "expected_effect_head_digest": author_plan.effect_head.head_digest,
            "expected_delivery_head_attempt_ref": (
                author_plan.delivery_head.current_delivery_attempt_ref
            ),
            "expected_delivery_head_revision": author_plan.delivery_head.head_revision,
            "expected_delivery_head_digest": author_plan.delivery_head.head_digest,
            "global_stop_ref": "global-stop-clear",
            "global_stop_version": 0,
            "global_stop_state": "clear",
            "authority_evaluation_ref": command.authority_evaluation_ref,
            "authority_evaluation_digest": (
                author_plan.authority_evaluation.authority_evaluation_digest
            ),
            "authority_selection_observation_schema_id": observation.schema_id,
            "authority_selection_observation_ref": (
                observation.authority_observation_ref
            ),
            "authoritative_subject_kind": observation.authoritative_subject_kind,
            "authoritative_subject_ref": observation.authoritative_subject_ref,
            "authority_observation_state": observation.observation_state,
            "authority_observation_version": observation.observation_version,
            "authority_observation_issued_at": (
                observation.authority_observation_issued_at
            ),
            "authority_observation_expires_at": (
                observation.authority_observation_expires_at
            ),
            "source_authority_ref": observation.source_authority_ref,
            "verification_evidence_ref": observation.verification_evidence_ref,
            "verification_evidence_digest": observation.verification_evidence_digest,
            "authority_selection_observation_digest": (
                observation.authority_observation_digest
            ),
            "standing_policy_ref": f"standing-policy-{marker}",
            "standing_policy_digest": "b" * 64,
            "risk_lane_ref": f"risk-lane-{marker}",
            "risk_lane_digest": "c" * 64,
            "repository_ref": work_spec.repository_ref,
            "base_git_object_format": work_spec.base_git_object_format,
            "base_git_oid": work_spec.base_git_oid,
            "authorized_path_scope_digest": "d" * 64,
            "cost_ceiling_ref": f"cost-ceiling-{marker}",
            "cost_ceiling_digest": "e" * 64,
            "token_ceiling_ref": f"token-ceiling-{marker}",
            "token_ceiling_digest": "1" * 64,
            "time_ceiling_ref": f"time-ceiling-{marker}",
            "time_ceiling_digest": "2" * 64,
            "delivery_ceiling_ref": f"delivery-ceiling-{marker}",
            "delivery_ceiling_digest": "3" * 64,
            "effect_ceiling_ref": f"effect-ceiling-{marker}",
            "effect_ceiling_digest": "4" * 64,
            "validation_requirement_ref": (
                command.validation_requirement_evidence.requirement_ref
            ),
            "validation_requirement_digest": (
                command.validation_requirement_evidence.requirement_digest
            ),
            "validation_safe_evidence_digest": (
                command.validation_requirement_evidence.safe_evidence_digest
            ),
            "review_requirement_ref": command.review_requirement_evidence.requirement_ref,
            "review_requirement_digest": (
                command.review_requirement_evidence.requirement_digest
            ),
            "review_safe_evidence_digest": (
                command.review_requirement_evidence.safe_evidence_digest
            ),
            "qualified_remote_host_readiness_ref": readiness_ref,
            "qualified_remote_host_readiness_digest": readiness_digest,
            "planning_context_captured_at": "2098-01-01T00:00:02Z",
        },
    )
    proposal_ref = f"model-proposal-{marker}"
    artifact = _artifact(
        marker=marker,
        proposal_ref=proposal_ref,
        context_ref=context.planning_context_ref,
        authorized_paths=tuple(work_spec.authorized_paths),
    )
    projection = _projection(artifact, context, proposal_ref)
    binding = _seal(
        semantic.PrivateProposalArtifactBindingV1,
        {
            "schema_id": semantic._SCHEMAS["artifact_binding"],
            "artifact_ref": artifact.artifact_ref,
            "proposal_phase": "pre_execution_plan",
            "artifact_schema_id": artifact.schema_id,
            "artifact_digest": artifact.artifact_digest,
            "artifact_canonical_byte_length": len(
                _canonical_bytes(artifact.to_mapping())
            ),
            "safe_projection_schema_id": projection.schema_id,
            "safe_projection_digest": projection.safe_projection_digest,
            "privacy_classification": "private_normalized_model_proposal",
            "artifact_validated_at": "2098-01-01T00:00:05Z",
        },
    )
    source = _seal(
        semantic.ModelSourceInvocationV1,
        {
            "schema_id": semantic._SCHEMAS["source_invocation"],
            "source_invocation_ref": f"source-invocation-{marker}",
            "proposal_phase": "pre_execution_plan",
            "model_contract_ref": "model-contract-reasoning",
            "model_contract_digest": "5" * 64,
            "model_configuration_ref": "model-configuration-safe",
            "model_configuration_digest": "6" * 64,
            "context_schema_id": context.schema_id,
            "context_ref": context.planning_context_ref,
            "context_digest": context.planning_context_digest,
            "artifact_schema_id": artifact.schema_id,
            "artifact_ref": artifact.artifact_ref,
            "artifact_digest": artifact.artifact_digest,
            "invocation_status": "normalized_typed_proposal_supplied",
            "source_invocation_started_at": "2098-01-01T00:00:03Z",
            "source_invocation_completed_at": "2098-01-01T00:00:04Z",
        },
    )
    evidence_spec = [
        (
            "standing_policy",
            context.standing_policy_ref,
            context.standing_policy_digest,
        ),
        ("risk_lane", context.risk_lane_ref, context.risk_lane_digest),
        ("repository_binding", f"repository-binding-{marker}", "7" * 64),
        ("base_binding", f"base-binding-{marker}", "8" * 64),
        (
            "authorized_path_scope",
            f"authorized-path-scope-{marker}",
            context.authorized_path_scope_digest,
        ),
        ("cost_ceiling", context.cost_ceiling_ref, context.cost_ceiling_digest),
        ("token_ceiling", context.token_ceiling_ref, context.token_ceiling_digest),
        ("time_ceiling", context.time_ceiling_ref, context.time_ceiling_digest),
        (
            "delivery_ceiling",
            context.delivery_ceiling_ref,
            context.delivery_ceiling_digest,
        ),
        ("effect_ceiling", context.effect_ceiling_ref, context.effect_ceiling_digest),
        (
            "authority_selection_observation",
            observation.authority_observation_ref,
            observation.authority_observation_digest,
        ),
        ("global_stop", f"global-stop-binding-{marker}", "9" * 64),
        (
            "validation_requirement",
            context.validation_requirement_ref,
            context.validation_requirement_digest,
        ),
        (
            "review_requirement",
            context.review_requirement_ref,
            context.review_requirement_digest,
        ),
    ]
    if readiness_present:
        evidence_spec.append(
            (
                semantic._READINESS_ROLE,
                context.qualified_remote_host_readiness_ref,
                context.qualified_remote_host_readiness_digest,
            )
        )
    evidence = tuple(
        _seal(
            semantic.ModelProposalEvidenceBindingV1,
            {
                "schema_id": semantic._SCHEMAS["evidence_binding"],
                "proposal_ref": proposal_ref,
                "proposal_phase": "pre_execution_plan",
                "evidence_set_ref": f"evidence-set-{marker}",
                "evidence_role": role,
                "role_rank": 5 + index,
                "ordinal": 0,
                "evidence_ref": reference,
                "evidence_digest": digest,
                "required_for_selection": 0 if role == semantic._READINESS_ROLE else 1,
                "evidence_bound_at": "2098-01-01T00:00:06Z",
            },
        )
        for index, (role, reference, digest) in enumerate(evidence_spec)
    )
    evidence_set = _seal(
        semantic.ModelProposalEvidenceSetV1,
        {
            "evidence_set_ref": f"evidence-set-{marker}",
            "proposal_ref": proposal_ref,
            "proposal_phase": "pre_execution_plan",
            "entries": evidence,
        },
    )
    proposal = _seal(
        semantic.PreExecutionModelProposalV1,
        {
            "schema_id": semantic._SCHEMAS["proposal"],
            "proposal_ref": proposal_ref,
            "proposal_phase": "pre_execution_plan",
            "source_invocation_ref": source.source_invocation_ref,
            "source_invocation_digest": source.source_invocation_digest,
            "model_contract_ref": source.model_contract_ref,
            "model_contract_digest": source.model_contract_digest,
            "model_configuration_ref": source.model_configuration_ref,
            "model_configuration_digest": source.model_configuration_digest,
            "context_schema_id": context.schema_id,
            "context_ref": context.planning_context_ref,
            "context_digest": context.planning_context_digest,
            "artifact_schema_id": artifact.schema_id,
            "artifact_ref": artifact.artifact_ref,
            "artifact_digest": artifact.artifact_digest,
            "safe_projection_schema_id": projection.schema_id,
            "safe_projection_digest": projection.safe_projection_digest,
            "recommendation": artifact.recommendation,
            "reason_code": artifact.reason_code,
            "evidence_set_ref": evidence_set.evidence_set_ref,
            "evidence_set_digest": evidence_set.evidence_set_digest,
            "proposal_created_at": "2098-01-01T00:00:07Z",
        },
    )
    return semantic.PreExecutionProposalSelectionBundleV1(
        authority_observation=observation,
        authority_expected_binding=expected,
        attempt_fence=attempt,
        effect_fence=effect,
        planning_context=context,
        source_invocation=source,
        private_artifact_binding=binding,
        private_artifact=artifact,
        safe_projection=projection,
        evidence_bindings=evidence,
        evidence_set=evidence_set,
        model_proposal=proposal,
    )


def make_section41_fixture(
    tmp_path: Path,
    *,
    suffix: str,
    readiness_present: bool = False,
    marker: str = "first",
) -> Section41Fixture:
    author = make_author_effect_fixture(tmp_path, suffix=suffix)
    result = author.writer._establish_development_author_effect_intent(**author.ingress)
    author._section41_author_result = result
    bundle = _build_bundle(
        author,
        marker=f"{suffix}-{marker}",
        readiness_present=readiness_present,
    )
    identity: dict[str, object] = {
        "preassigned_disposition_ref": f"planning-disposition-{suffix}-{marker}",
        "expected_current_selection_revision": None,
        "expected_current_selection_head_digest": None,
        "disposition": "selected_for_dispatch_gates",
        "disposition_reason_code": "selection.policy_bounds_satisfied",
        "supersedes_disposition_ref": None,
    }
    fields = {
        "schema_id": (
            "governed-execution.nwp-record-pre-execution-plan-disposition-command.v1"
        ),
        "mutation_ref": f"cognitive-mutation-{suffix}-{marker}",
        "proposal_ref": bundle.model_proposal.proposal_ref,
        "proposal_digest": bundle.model_proposal.proposal_digest,
        "source_invocation_ref": bundle.source_invocation.source_invocation_ref,
        "source_invocation_digest": bundle.source_invocation.source_invocation_digest,
        "artifact_ref": bundle.private_artifact_binding.artifact_ref,
        "artifact_digest": bundle.private_artifact_binding.artifact_digest,
        "artifact_binding_digest": (
            bundle.private_artifact_binding.artifact_binding_digest
        ),
        "planning_context_ref": bundle.planning_context.planning_context_ref,
        "planning_context_digest": bundle.planning_context.planning_context_digest,
        "safe_projection_digest": bundle.safe_projection.safe_projection_digest,
        "evidence_set_ref": bundle.evidence_set.evidence_set_ref,
        "evidence_set_digest": bundle.evidence_set.evidence_set_digest,
        **identity,
        "program_ref": bundle.planning_context.program_ref,
        "semantic_attempt_ref": bundle.planning_context.semantic_attempt_ref,
        "candidate_ref": bundle.planning_context.candidate_ref,
        "effect_intent_ref": bundle.planning_context.effect_intent_ref,
        "author_command_ref": bundle.planning_context.author_command_ref,
        "author_command_digest": bundle.planning_context.author_command_digest,
        "attempt_fence_ref": bundle.planning_context.attempt_fence_ref,
        "attempt_fence_digest": bundle.planning_context.attempt_fence_digest,
        "effect_fence_ref": bundle.planning_context.effect_fence_ref,
        "effect_fence_digest": bundle.planning_context.effect_fence_digest,
        "delivery_attempt_ref": bundle.planning_context.delivery_attempt_ref,
        "delivery_envelope_digest": (bundle.planning_context.delivery_envelope_digest),
    }
    digest = _domain_separated_digest(
        "governed-execution.nwp-record-pre-execution-plan-disposition-command.v1.identity",
        fields,
    )
    return Section41Fixture(
        author=author,
        bundle=bundle,
        identity=identity,
        mutation_ref=fields["mutation_ref"],
        command_digest=digest,
    )


def _install_dangling_successor_above_unadvanced_head(
    fixture: Section41Fixture,
    *,
    marker: str,
) -> tuple[PreExecutionPlanDispositionResultV1, object, dict[str, object]]:
    retained_probe = fixture.recovery_probe
    root_plan = runtime._build_write_plan(
        runtime._FreshPreExecutionPlanDisposition(
            fixture.command,
            fixture.bundle,
            None,
            retained_probe,
        ),
        DECISION_TIME,
    )
    root_result = fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        retained_probe,
    )
    successor_bundle = _build_bundle(
        fixture.author,
        marker=marker,
        readiness_present=True,
    )
    successor_identity: dict[str, object] = {
        "preassigned_disposition_ref": f"planning-disposition-{marker}",
        "expected_current_selection_revision": root_result.selection_head_revision,
        "expected_current_selection_head_digest": root_result.selection_head_digest,
        "disposition": "selected_for_dispatch_gates",
        "disposition_reason_code": "selection.policy_bounds_satisfied",
        "supersedes_disposition_ref": root_result.disposition_ref,
    }
    successor_fields = fixture.command.to_mapping()
    successor_fields.pop("mutation_command_digest")
    successor_fields.update(
        {
            "mutation_ref": f"cognitive-mutation-{marker}",
            "proposal_ref": successor_bundle.model_proposal.proposal_ref,
            "proposal_digest": successor_bundle.model_proposal.proposal_digest,
            "source_invocation_ref": (
                successor_bundle.source_invocation.source_invocation_ref
            ),
            "source_invocation_digest": (
                successor_bundle.source_invocation.source_invocation_digest
            ),
            "artifact_ref": successor_bundle.private_artifact_binding.artifact_ref,
            "artifact_digest": (
                successor_bundle.private_artifact_binding.artifact_digest
            ),
            "artifact_binding_digest": (
                successor_bundle.private_artifact_binding.artifact_binding_digest
            ),
            "planning_context_ref": (
                successor_bundle.planning_context.planning_context_ref
            ),
            "planning_context_digest": (
                successor_bundle.planning_context.planning_context_digest
            ),
            "safe_projection_digest": (
                successor_bundle.safe_projection.safe_projection_digest
            ),
            "evidence_set_ref": successor_bundle.evidence_set.evidence_set_ref,
            "evidence_set_digest": successor_bundle.evidence_set.evidence_set_digest,
            **successor_identity,
        }
    )
    successor_digest = _domain_separated_digest(
        contracts._COMMAND_DOMAIN,
        successor_fields,
    )
    successor_probe = (
        fixture.author.writer._prepare_pre_execution_plan_disposition_recovery_probe(
            successor_fields["mutation_ref"],
            successor_digest,
            successor_bundle,
            successor_identity,
        )
    )
    successor_result = (
        fixture.author.writer._record_pre_execution_plan_disposition(
            successor_fields["mutation_ref"],
            successor_digest,
            successor_bundle,
            successor_identity,
            successor_probe,
        )
    )
    assert successor_result.selection_head_revision == 1

    root_head = next(
        member.values.to_mapping()
        for member in root_plan.rows
        if member.table == runtime._rows._TABLE_ORDER[7]
    )
    mutable_head_fields = (
        "current_proposal_ref",
        "current_disposition_ref",
        "current_disposition",
        "head_revision",
        "updated_at",
        "head_digest",
    )
    connection = sqlite3.connect(fixture.author.location.database_path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        cursor = connection.execute(
            "UPDATE development_pre_execution_selection_heads SET "
            + ", ".join(f"{name} = ?" for name in mutable_head_fields)
            + " WHERE "
            + " AND ".join(f"{name} = ?" for name in runtime._K8_FIELDS),
            tuple(root_head[name] for name in mutable_head_fields)
            + tuple(root_head[name] for name in runtime._K8_FIELDS),
        )
        assert cursor.rowcount == 1
        cursor.close()
        connection.commit()
        foreign_key_failures = tuple(connection.execute("PRAGMA foreign_key_check"))
        integrity_check = connection.execute("PRAGMA integrity_check").fetchone()
        disposition_count = connection.execute(
            "SELECT COUNT(*) FROM development_pre_execution_dispositions"
        ).fetchone()
        receipt_count = connection.execute(
            "SELECT COUNT(*) FROM development_cognitive_mutation_receipts"
        ).fetchone()
        head_revision = connection.execute(
            "SELECT head_revision FROM development_pre_execution_selection_heads"
        ).fetchone()
        dangling_count = connection.execute(
            "SELECT COUNT(*) FROM development_pre_execution_dispositions "
            "WHERE "
            + " AND ".join(f"{name} = ?" for name in runtime._L34_FIELDS)
            + " AND prior_selection_head_revision = ? "
            "AND supersedes_disposition_ref = ?",
            tuple(root_head[name] for name in runtime._L34_FIELDS)
            + (root_head["head_revision"], root_head["current_disposition_ref"]),
        ).fetchone()
    finally:
        connection.close()
    evidence = {
        "foreign_key_failures": foreign_key_failures,
        "integrity_check": integrity_check,
        "disposition_count": disposition_count,
        "receipt_count": receipt_count,
        "head_revision": head_revision,
        "dangling_count": dangling_count,
    }
    return root_result, retained_probe, evidence


@pytest.mark.parametrize("readiness_present", (False, True))
def test_fresh_apply_and_receipt_first_exact_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    readiness_present: bool,
) -> None:
    fixture = make_section41_fixture(
        tmp_path,
        suffix=f"fresh-{int(readiness_present)}",
        readiness_present=readiness_present,
    )
    recovery_probe = fixture.recovery_probe
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
    )
    result = fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        recovery_probe,
    )
    assert type(result) is PreExecutionPlanDispositionResultV1
    assert result.recorded_at == DECISION_TIME
    connection = sqlite3.connect(fixture.author.location.database_path)
    try:
        counts = {
            table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in (
                "development_model_source_invocations",
                "development_pre_execution_planning_contexts",
                "development_private_proposal_artifact_bindings",
                "development_model_proposals",
                "development_pre_execution_plan_projections",
                "development_model_proposal_evidence_bindings",
                "development_pre_execution_dispositions",
                "development_pre_execution_selection_heads",
                "development_cognitive_mutation_receipts",
            )
        }
    finally:
        connection.close()
    assert tuple(counts.values()) == (
        1,
        1,
        1,
        1,
        1,
        15 if readiness_present else 14,
        1,
        1,
        1,
    )

    def fresh_path_forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("fresh bundle traversed during replay")

    monkeypatch.setattr(
        "ge_nwp_coordinator._sqlite_development_pre_execution_plan_disposition._validate_bundle_relations",
        fresh_path_forbidden,
    )
    replay = fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        recovery_probe,
    )
    assert replay.to_mapping() == result.to_mapping()
    fixture.author.writer.close()


def test_reuse_and_selection_head_conflicts_are_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="conflicts")
    recovery_probe = fixture.recovery_probe
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
    )
    fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        recovery_probe,
    )
    reuse_identity = dict(fixture.identity)
    reuse_identity["disposition_reason_code"] = "selection.changed-policy-basis"
    reuse_fields = fixture.command.to_mapping()
    reuse_fields.pop("mutation_command_digest")
    reuse_fields["disposition_reason_code"] = reuse_identity[
        "disposition_reason_code"
    ]
    reuse_digest = _domain_separated_digest(
        "governed-execution.nwp-record-pre-execution-plan-disposition-command.v1.identity",
        reuse_fields,
    )
    reuse_probe = (
        fixture.author.writer._prepare_pre_execution_plan_disposition_recovery_probe(
            fixture.mutation_ref,
            reuse_digest,
            fixture.bundle,
            reuse_identity,
        )
    )
    reuse = fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        reuse_digest,
        fixture.bundle,
        reuse_identity,
        reuse_probe,
    )
    assert type(reuse) is PreExecutionPlanDispositionConflictV1
    assert (
        reuse.reason
        is PreExecutionPlanDispositionConflictReasonV1.MUTATION_REF_REUSE_CONFLICT
    )

    second_bundle = _build_bundle(
        fixture.author,
        marker="conflicts-second",
        readiness_present=False,
    )
    second_identity = dict(fixture.identity)
    second_identity["preassigned_disposition_ref"] = (
        "planning-disposition-conflicts-second"
    )
    fields = {
        **fixture.command.to_mapping(),
        "mutation_ref": "cognitive-mutation-conflicts-second",
        "proposal_ref": second_bundle.model_proposal.proposal_ref,
        "proposal_digest": second_bundle.model_proposal.proposal_digest,
        "source_invocation_ref": second_bundle.source_invocation.source_invocation_ref,
        "source_invocation_digest": second_bundle.source_invocation.source_invocation_digest,
        "artifact_ref": second_bundle.private_artifact_binding.artifact_ref,
        "artifact_digest": second_bundle.private_artifact_binding.artifact_digest,
        "artifact_binding_digest": second_bundle.private_artifact_binding.artifact_binding_digest,
        "planning_context_ref": second_bundle.planning_context.planning_context_ref,
        "planning_context_digest": second_bundle.planning_context.planning_context_digest,
        "safe_projection_digest": second_bundle.safe_projection.safe_projection_digest,
        "evidence_set_ref": second_bundle.evidence_set.evidence_set_ref,
        "evidence_set_digest": second_bundle.evidence_set.evidence_set_digest,
        "preassigned_disposition_ref": second_identity["preassigned_disposition_ref"],
    }
    fields.pop("mutation_command_digest")
    second_digest = _domain_separated_digest(
        "governed-execution.nwp-record-pre-execution-plan-disposition-command.v1.identity",
        fields,
    )
    conflict = fixture.author.writer._record_pre_execution_plan_disposition(
        fields["mutation_ref"],
        second_digest,
        second_bundle,
        second_identity,
        fixture.author.writer._prepare_pre_execution_plan_disposition_recovery_probe(
            fields["mutation_ref"], second_digest, second_bundle, second_identity
        ),
    )
    assert type(conflict) is PreExecutionPlanDispositionConflictV1
    assert (
        conflict.reason
        is PreExecutionPlanDispositionConflictReasonV1.SELECTION_HEAD_VERSION_CONFLICT
    )
    fixture.author.writer.close()


def test_receipt_hit_route_bearing_command_mismatch_is_mutation_ref_reuse_conflict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="route-bearing-reuse")
    original_probe = fixture.recovery_probe
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
    )
    fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        original_probe,
    )

    reuse_identity = dict(fixture.identity)
    reuse_identity["preassigned_disposition_ref"] = (
        "planning-disposition-route-bearing-reuse-different"
    )
    reuse_fields = fixture.command.to_mapping()
    reuse_fields.pop("mutation_command_digest")
    reuse_fields["preassigned_disposition_ref"] = reuse_identity[
        "preassigned_disposition_ref"
    ]
    reuse_digest = _domain_separated_digest(
        contracts._COMMAND_DOMAIN,
        reuse_fields,
    )
    reuse_probe = (
        fixture.author.writer._prepare_pre_execution_plan_disposition_recovery_probe(
            fixture.mutation_ref,
            reuse_digest,
            fixture.bundle,
            reuse_identity,
        )
    )

    def fresh_bundle_forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("receipt reuse traversed the supplied fresh bundle")

    monkeypatch.setattr(runtime, "_validate_bundle_relations", fresh_bundle_forbidden)
    downstream = _install_section41_downstream_counters(monkeypatch)
    conflict = fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        reuse_digest,
        fixture.bundle,
        reuse_identity,
        reuse_probe,
    )
    assert type(conflict) is PreExecutionPlanDispositionConflictV1
    assert (
        conflict.reason
        is PreExecutionPlanDispositionConflictReasonV1.MUTATION_REF_REUSE_CONFLICT
    )
    assert conflict.command_digest == reuse_digest
    assert downstream == {
        "current": 0,
        "clock": 0,
        "result": 0,
        "dml": 0,
        "commit": 0,
    }
    fixture.author.writer.close()


def test_fresh_commit_is_attempted_once_and_uncertainty_is_explicit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="uncertain")
    recovery_probe = fixture.recovery_probe
    calls = 0

    def uncertain_commit(connection: sqlite3.Connection) -> object:
        nonlocal calls
        calls += 1
        raise sqlite3.OperationalError("injected commit uncertainty")

    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
    )
    monkeypatch.setattr(transaction, "_commit_transaction", uncertain_commit)
    with pytest.raises(SQLiteMutationStoreError) as caught:
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            recovery_probe,
        )
    assert (
        caught.value.error_class
        == SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN.value
    )
    assert calls == 1
    fixture.author.writer.close()


def _install_section41_downstream_counters(
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, int]:
    calls = {"current": 0, "clock": 0, "result": 0, "dml": 0, "commit": 0}

    def current(*args: object, **kwargs: object) -> tuple[bool, None]:
        calls["current"] += 1
        return False, None

    def clock(*args: object, **kwargs: object) -> str:
        calls["clock"] += 1
        return DECISION_TIME

    def dml(*args: object, **kwargs: object) -> None:
        calls["dml"] += 1

    def result(*args: object, **kwargs: object) -> object:
        calls["result"] += 1
        raise AssertionError("result construction reached")

    def commit(*args: object, **kwargs: object) -> None:
        calls["commit"] += 1

    monkeypatch.setattr(runtime, "_current_c2b3d_lineage_is_exact", current)
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", clock)
    monkeypatch.setattr(
        transaction, "_pre_execution_plan_disposition_write_plan", result
    )
    monkeypatch.setattr(
        transaction, "_execute_pre_execution_plan_disposition_writes", dml
    )
    monkeypatch.setattr(transaction, "_commit_transaction", commit)
    return calls


def _equal_hash_semantic_spoof(
    trusted_value: object,
) -> tuple[object, dict[str, int]]:
    trusted_type = type(trusted_value)
    callbacks = {"hash": 0, "equality": 0, "mapping": 0, "construction": 0}

    class CollisionMeta(type):
        def __hash__(cls) -> int:
            callbacks["hash"] += 1
            return type.__hash__(trusted_type)

        def __eq__(cls, other: object) -> bool:
            callbacks["equality"] += 1
            return other is trusted_type

        def __call__(cls, *args: object, **kwargs: object) -> object:
            callbacks["construction"] += 1
            return trusted_type(*args, **kwargs)

    field_order = trusted_type._FIELD_ORDER  # type: ignore[attr-defined]

    def to_mapping(self: object) -> dict[str, object]:
        callbacks["mapping"] += 1
        return {
            name: object.__getattribute__(self, name) for name in field_order
        }

    spoof_type = CollisionMeta(
        trusted_type.__name__,
        (),
        {
            "__module__": trusted_type.__module__,
            "_FIELD_ORDER": field_order,
            "to_mapping": to_mapping,
        },
    )
    spoof = object.__new__(spoof_type)
    spoof.__dict__.update(
        {
            name: object.__getattribute__(trusted_value, name)
            for name in field_order
        }
    )
    callbacks.update(hash=0, equality=0, mapping=0, construction=0)
    return spoof, callbacks


def _shared_tuple_dag(depth: int) -> tuple[object, ...]:
    node: tuple[object, ...] = ("bounded-leaf",)
    for _index in range(depth):
        node = (node, node)
    return node


def test_write_preflight_rejects_shared_dag_before_operation_guard_sql_clock_or_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="write-shared-dag")
    probe = fixture.recovery_probe
    shared = _shared_tuple_dag(10)
    object.__setattr__(
        probe,
        "identity_locators",
        tuple((shared, shared) for _index in range(30)),
    )
    monkeypatch.setattr(
        contracts,
        "_MAX_EXACT_CONTRACT_RECONSTRUCTION_WORK",
        5_000,
        raising=False,
    )
    calls = {
        "operation": 0,
        "connection": 0,
        "query": 0,
        "clock": 0,
        "write": 0,
        "commit": 0,
        "result": 0,
    }

    def forbidden(name: str):
        def invoke(*args: object, **kwargs: object) -> object:
            calls[name] += 1
            raise AssertionError(f"{name} reached")

        return invoke

    monkeypatch.setattr(
        type(fixture.author.writer),
        "_run_pre_execution_plan_disposition_operation",
        forbidden("operation"),
    )
    monkeypatch.setattr(
        transaction, "_open_controller_connection", forbidden("connection")
    )
    monkeypatch.setattr(runtime, "_read_receipt", forbidden("query"))
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", forbidden("clock")
    )
    monkeypatch.setattr(
        transaction,
        "_execute_pre_execution_plan_disposition_writes",
        forbidden("write"),
    )
    monkeypatch.setattr(transaction, "_commit_transaction", forbidden("commit"))
    monkeypatch.setattr(
        transaction,
        "_pre_execution_plan_disposition_write_plan",
        forbidden("result"),
    )
    with pytest.raises(SQLiteMutationStoreError) as caught:
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            probe,
        )
    assert caught.value.error_class == (
        SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value
    )
    assert calls == {
        "operation": 0,
        "connection": 0,
        "query": 0,
        "clock": 0,
        "write": 0,
        "commit": 0,
        "result": 0,
    }
    fixture.author.writer.close()


def test_equal_hash_semantic_spoof_on_receipt_miss_fails_before_all_downstream_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="metaclass-receipt-miss")
    recovery_probe = fixture.recovery_probe
    artifact = fixture.bundle.private_artifact
    spoof, callbacks = _equal_hash_semantic_spoof(
        artifact.proposed_work_units[0]
    )
    object.__setattr__(artifact, "proposed_work_units", (spoof,))

    receipt_calls = 0
    read_receipt = runtime._read_receipt

    def receipt(*args: object, **kwargs: object) -> object:
        nonlocal receipt_calls
        receipt_calls += 1
        return read_receipt(*args, **kwargs)

    monkeypatch.setattr(runtime, "_read_receipt", receipt)
    downstream = _install_section41_downstream_counters(monkeypatch)
    with pytest.raises(SQLiteMutationStoreError) as caught:
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            recovery_probe,
        )
    assert receipt_calls == 1
    assert callbacks == {"hash": 0, "equality": 0, "mapping": 0, "construction": 0}
    assert downstream == {
        "current": 0,
        "clock": 0,
        "result": 0,
        "dml": 0,
        "commit": 0,
    }
    assert caught.value.error_class == SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None

    connection = sqlite3.connect(fixture.author.location.database_path)
    try:
        durable_count = sum(
            connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in (
                "development_model_source_invocations",
                "development_pre_execution_planning_contexts",
                "development_private_proposal_artifact_bindings",
                "development_model_proposals",
                "development_pre_execution_plan_projections",
                "development_model_proposal_evidence_bindings",
                "development_pre_execution_dispositions",
                "development_pre_execution_selection_heads",
                "development_cognitive_mutation_receipts",
            )
        )
    finally:
        connection.close()
    assert durable_count == 0
    fixture.author.writer.close()


def test_same_length_post_construction_private_narrative_mutation_fails_before_current_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="mutated-narrative")
    recovery_probe = fixture.recovery_probe
    work_unit = fixture.bundle.private_artifact.proposed_work_units[0]
    original = work_unit.summary
    changed = original[:-1] + ("!" if original[-1] != "!" else ".")
    assert len(changed) == len(original) and changed != original
    object.__setattr__(work_unit, "summary", changed)
    calls = _install_section41_downstream_counters(monkeypatch)
    with pytest.raises(SQLiteMutationStoreError):
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            recovery_probe,
        )
    assert calls == {
        "current": 0,
        "clock": 0,
        "result": 0,
        "dml": 0,
        "commit": 0,
    }
    fixture.author.writer.close()


def test_stale_nested_evidence_self_digest_fails_before_current_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="stale-evidence-digest")
    recovery_probe = fixture.recovery_probe
    binding = fixture.bundle.evidence_bindings[1]
    original = binding.evidence_ref
    replacement = "x" if original[-1] != "x" else "y"
    object.__setattr__(binding, "evidence_ref", original[:-1] + replacement)
    calls = _install_section41_downstream_counters(monkeypatch)
    with pytest.raises(SQLiteMutationStoreError):
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            recovery_probe,
        )
    assert calls == {
        "current": 0,
        "clock": 0,
        "result": 0,
        "dml": 0,
        "commit": 0,
    }
    fixture.author.writer.close()


@pytest.mark.parametrize(
    "hostile_kind",
    ("equality-and-hash", "iteration", "unhashable", "cycle"),
)
def test_hostile_nested_fresh_values_are_rejected_without_callbacks_or_downstream_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    hostile_kind: str,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix=f"hostile-{hostile_kind}")
    recovery_probe = fixture.recovery_probe
    callbacks = {"equality": 0, "hash": 0, "iteration": 0}

    class HostileString(str):
        def __eq__(self, other: object) -> bool:
            callbacks["equality"] += 1
            raise KeyboardInterrupt()

        def __hash__(self) -> int:
            callbacks["hash"] += 1
            raise SystemExit()

    class HostileTuple(tuple):
        def __iter__(self) -> object:
            callbacks["iteration"] += 1
            raise GeneratorExit()

    artifact = fixture.bundle.private_artifact
    if hostile_kind == "equality-and-hash":
        object.__setattr__(
            fixture.bundle.evidence_bindings[1],
            "evidence_ref",
            HostileString("evidence-hostile"),
        )
    elif hostile_kind == "iteration":
        object.__setattr__(
            artifact,
            "implementation_strategy",
            HostileTuple(artifact.implementation_strategy),
        )
    elif hostile_kind == "unhashable":
        object.__setattr__(artifact, "implementation_strategy", ({},))
    else:
        object.__setattr__(artifact, "implementation_strategy", (artifact,))
    calls = _install_section41_downstream_counters(monkeypatch)
    with pytest.raises(SQLiteMutationStoreError):
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            recovery_probe,
        )
    assert callbacks == {"equality": 0, "hash": 0, "iteration": 0}
    assert calls == {
        "current": 0,
        "clock": 0,
        "result": 0,
        "dml": 0,
        "commit": 0,
    }
    fixture.author.writer.close()


def test_exact_receipt_replay_does_not_traverse_hostile_fresh_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="hostile-replay")
    recovery_probe = fixture.recovery_probe
    monkeypatch.setattr(
        transaction, "_capture_transaction_timestamp", lambda: DECISION_TIME
    )
    committed = fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        recovery_probe,
    )
    artifact = fixture.bundle.private_artifact
    spoof, callbacks = _equal_hash_semantic_spoof(
        artifact.proposed_work_units[0]
    )
    object.__setattr__(artifact, "proposed_work_units", (spoof,))
    downstream = _install_section41_downstream_counters(monkeypatch)
    replay = fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        recovery_probe,
    )
    assert replay.to_mapping() == committed.to_mapping()
    assert callbacks == {"hash": 0, "equality": 0, "mapping": 0, "construction": 0}
    assert downstream == {
        "current": 0,
        "clock": 0,
        "result": 0,
        "dml": 0,
        "commit": 0,
    }
    fixture.author.writer.close()


def test_receipt_hit_rejects_dangling_successor_above_unadvanced_head_before_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="dangling-successor-replay")
    try:
        monkeypatch.setattr(
            transaction,
            "_capture_transaction_timestamp",
            lambda: DECISION_TIME,
        )
        _root_result, retained_probe, evidence = (
            _install_dangling_successor_above_unadvanced_head(
                fixture,
                marker="dangling-successor-replay-next",
            )
        )
        assert evidence == {
            "foreign_key_failures": (),
            "integrity_check": ("ok",),
            "disposition_count": (2,),
            "receipt_count": (2,),
            "head_revision": (0,),
            "dangling_count": (1,),
        }

        result_constructions = 0

        def result_forbidden(*args: object, **kwargs: object) -> object:
            nonlocal result_constructions
            result_constructions += 1
            raise AssertionError("dangling successor reached result construction")

        downstream = _install_section41_downstream_counters(monkeypatch)
        monkeypatch.setattr(
            runtime,
            "PreExecutionPlanDispositionResultProjectionV1",
            result_forbidden,
        )
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
        assert str(caught.value) == "database_integrity_failure"
        assert caught.value.args == ("database_integrity_failure",)
        assert result_constructions == 0
        assert downstream == {
            "current": 0,
            "clock": 0,
            "result": 0,
            "dml": 0,
            "commit": 0,
        }
    finally:
        fixture.author.writer.close()
