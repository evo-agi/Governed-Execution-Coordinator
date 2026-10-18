"""Production-private construction of the current Section 41 and C1 values.

The artificial fixture supplies external observations; the guarded current
writer remains the sole durable selection and phase owner.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json

from . import _cognitive_proposal_semantic_values as semantic
from ._cognitive_proposal_value_support import (
    _canonical_bytes, _domain_separated_digest, _without_field,
)
from ._development_author_effect_establishment_contracts import (
    _development_author_effect_establishment_write_plan,
)
from ._rw0_phase_entry_semantic_values import RW0PhaseEntryBasisV1
from ._rw0_c1_semantic_values import RW0C1EstablishPhaseCommandV1
from ._development_pre_execution_plan_disposition_contracts import (
    CanonicalC2B3DLineage, _L34_FIELDS, _K8_FIELDS,
)

@dataclass(frozen=True, slots=True, repr=False)
class _AuthorContext:
    command: object
    result: object


def _digest(domain: str, identity: dict[str, object]) -> str:
    data = json.dumps(identity, sort_keys=True, ensure_ascii=False,
                      allow_nan=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(domain.encode("utf-8") + b"\0" + data).hexdigest()

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

def _artifact(
    *,
    marker: str,
    proposal_ref: str,
    context_ref: str,
    authorized_paths: tuple[str, ...],
    planner: dict[str, object],
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
        summary=planner["plan"],
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
        "implementation_strategy": (planner["strategy"],),
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
        "recommendation": planner["recommendation"],
        "reason_code": planner["reason"],
    }
    return _seal(semantic.PreExecutionPlanArtifactV1, values)

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
    author: _AuthorContext,
    *,
    marker: str,
    readiness_present: bool,
    planner: dict[str, object],
    program_revision: int,
    work_revision: int,
) -> semantic.PreExecutionProposalSelectionBundleV1:
    origin = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(seconds=20)

    def at(second: int) -> str:
        return (origin + timedelta(seconds=second)).strftime("%Y-%m-%dT%H:%M:%SZ")

    command = author.command
    author_plan = _development_author_effect_establishment_write_plan(
        command,
        author.result.transaction_timestamp,
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
            "authority_observation_issued_at": at(0),
            "authority_observation_expires_at": "2099-01-01T00:00:00Z",
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
            "planning_context_captured_at": at(1),
        },
    )
    proposal_ref = f"model-proposal-{marker}"
    artifact = _artifact(
        marker=marker,
        proposal_ref=proposal_ref,
        context_ref=context.planning_context_ref,
        authorized_paths=tuple(work_spec.authorized_paths),
        planner=planner,
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
            "artifact_validated_at": at(4),
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
            "source_invocation_started_at": at(2),
            "source_invocation_completed_at": at(3),
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
                "evidence_bound_at": at(5),
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
            "proposal_created_at": at(6),
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


def section41_disposition_identity_and_digest(
    bundle: semantic.PreExecutionProposalSelectionBundleV1,
    *, mutation_ref: str, disposition_ref: str,
) -> tuple[dict[str, object], str]:
    """Bind parent-preassigned IDs to the exact planner-derived proposal."""
    disposition = (
        "selected_for_dispatch_gates"
        if bundle.model_proposal.recommendation == "select_for_dispatch_gates"
        else "deferred"
    )
    identity: dict[str, object] = {
        "preassigned_disposition_ref": disposition_ref,
        "expected_current_selection_revision": None,
        "expected_current_selection_head_digest": None,
        "disposition": disposition,
        "disposition_reason_code": (
            "selection.policy_bounds_satisfied" if disposition == "selected_for_dispatch_gates"
            else "selection.planner_deferred"
        ),
        "supersedes_disposition_ref": None,
    }
    context = bundle.planning_context
    fields = {
        "schema_id": "governed-execution.nwp-record-pre-execution-plan-disposition-command.v1",
        "mutation_ref": mutation_ref,
        "proposal_ref": bundle.model_proposal.proposal_ref,
        "proposal_digest": bundle.model_proposal.proposal_digest,
        "source_invocation_ref": bundle.source_invocation.source_invocation_ref,
        "source_invocation_digest": bundle.source_invocation.source_invocation_digest,
        "artifact_ref": bundle.private_artifact_binding.artifact_ref,
        "artifact_digest": bundle.private_artifact_binding.artifact_digest,
        "artifact_binding_digest": bundle.private_artifact_binding.artifact_binding_digest,
        "planning_context_ref": context.planning_context_ref,
        "planning_context_digest": context.planning_context_digest,
        "safe_projection_digest": bundle.safe_projection.safe_projection_digest,
        "evidence_set_ref": bundle.evidence_set.evidence_set_ref,
        "evidence_set_digest": bundle.evidence_set.evidence_set_digest,
        **identity,
        "program_ref": context.program_ref,
        "semantic_attempt_ref": context.semantic_attempt_ref,
        "candidate_ref": context.candidate_ref,
        "effect_intent_ref": context.effect_intent_ref,
        "author_command_ref": context.author_command_ref,
        "author_command_digest": context.author_command_digest,
        "attempt_fence_ref": context.attempt_fence_ref,
        "attempt_fence_digest": context.attempt_fence_digest,
        "effect_fence_ref": context.effect_fence_ref,
        "effect_fence_digest": context.effect_fence_digest,
        "delivery_attempt_ref": context.delivery_attempt_ref,
        "delivery_envelope_digest": context.delivery_envelope_digest,
    }
    return identity, _digest(fields["schema_id"] + ".identity", fields)


def make_phase_command(
    *, bundle: semantic.PreExecutionProposalSelectionBundleV1,
    disposition_result: object, genesis_plan: object,
    author_plan: object, work_spec: object,
    mutation_ref: str = "mutation.d1.phase",
) -> tuple[RW0PhaseEntryBasisV1, RW0C1EstablishPhaseCommandV1]:
    """Construct the current C1 command from exact committed selection evidence."""
    context = bundle.planning_context
    lineage = CanonicalC2B3DLineage(
        **{name: getattr(context, name) for name in _L34_FIELDS}
    )
    path_scope = _digest(
        "governed-execution.nwp-rw0-current-path-scope-binding.v1.identity",
        list(work_spec.authorized_paths),
    )
    identity = {
        "schema_id": RW0PhaseEntryBasisV1._SCHEMA,
        "basis_ref": "basis.d1.offline",
        "c2b3d_lineage": lineage.to_mapping(),
        "selection_key": [[name, getattr(lineage, name)] for name in _K8_FIELDS],
        "selected_proposal_ref": bundle.model_proposal.proposal_ref,
        "selected_proposal_digest": bundle.model_proposal.proposal_digest,
        "selected_artifact_ref": bundle.private_artifact.artifact_ref,
        "selected_artifact_digest": bundle.private_artifact.artifact_digest,
        "selected_artifact_binding_digest": bundle.private_artifact_binding.artifact_binding_digest,
        "selected_plan_safe_projection_digest": bundle.safe_projection.safe_projection_digest,
        "disposition_ref": disposition_result.disposition_ref,
        "disposition_digest": disposition_result.disposition_digest,
        "disposition": disposition_result.disposition,
        "selection_head_revision": disposition_result.selection_head_revision,
        "selection_head_digest": disposition_result.selection_head_digest,
        "current_effect_head_revision": author_plan.effect_head.head_revision,
        "current_effect_head_state": author_plan.effect_head.effect_state,
        "current_effect_head_digest": author_plan.effect_head.head_digest,
        "current_delivery_head_revision": author_plan.delivery_head.head_revision,
        "current_delivery_head_state": author_plan.delivery_head.delivery_state,
        "current_delivery_head_digest": author_plan.delivery_head.head_digest,
        "global_stop_ref": "global-stop-clear",
        "global_stop_version": 0,
        "global_stop_state": "clear",
        "path_scope_digest": path_scope,
    }
    basis = RW0PhaseEntryBasisV1.from_mapping({
        **identity,
        "basis_digest": _digest(RW0PhaseEntryBasisV1._SCHEMA + ".identity", identity),
    })
    phase = RW0C1EstablishPhaseCommandV1(
        mutation_ref=mutation_ref, phase_basis=basis,
        work_spec=work_spec,
        work_spec_safe_projection_digest=context.work_spec_safe_projection_digest,
        expected_program_head_revision=genesis_plan.program_head.head_revision,
        expected_program_head_digest=genesis_plan.program_head.head_digest,
        expected_work_item_head_revision=genesis_plan.work_item_head.head_revision,
        expected_work_item_head_digest=genesis_plan.work_item_head.head_digest,
    )
    return basis, phase
