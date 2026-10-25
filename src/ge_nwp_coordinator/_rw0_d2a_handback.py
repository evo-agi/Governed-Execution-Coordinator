"""Resource-free D2 A evidence checkpoint; never holds the D1 run owner."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._finite_backlog_risk_source_adapter import FiniteBacklogRiskSourceBindingV1
from ._development_bound_effect_establishment_contracts import (
    DevelopmentBoundEffectEstablishmentCommandV1,
    DevelopmentBoundEffectEstablishmentResultV1,
    _require_exact_development_bound_effect_command,
)
from ._development_author_effect_establishment_contracts import (
    DevelopmentReviewRequirementEvidenceV1,
    DevelopmentValidationRequirementEvidenceV1,
)
from ._post_execution_evidence_values import (
    IndependentReviewDispositionV1,
    PostExecutionReviewResultSetV1,
    PostExecutionReviewerSeparationEvaluationV1,
    PostExecutionSupportSetV1,
    PostExecutionValidationResultSetV1,
    ValidationDispositionV1,
)
from ._post_execution_policy_values import (
    PostExecutionRiskLaneBranchMatrixV1,
    PostExecutionStandingPolicyBranchMatrixV1,
    PostExecutionRiskPolicyAttestationV1,
    PostExecutionStandingPolicySourceAttestationV1,
    PostExecutionRiskSourceBindingV1,
    PostExecutionRiskSourceProfileV1,
)
from ._rw0_d1_handback import RW0D1HandbackV1
from ._rw0_d1_process_supervisor import D1ProcessOutcome
from ._rw0_d1_workspace import D1CandidateCapture
from ._rw0_d2a_evidence import RW0D2CheckingEvidenceV1, _resolve_d2_checked_layout
from ._rw0_phase_entry_semantic_values import (
    RW0AuthorityVerificationObservationV1,
    RW0EffectHostQualificationV1,
    RW0RemoteHostReadinessObservationV1,
)
from ._sqlite_rw0_c1 import RW0C1CheckedEvidenceFamilyV1
from ._worker_execution_semantic_values import (
    CandidateCapsuleManifestV1,
    DeliveryEnvelopeV1,
    EffectFenceV1,
    WorkerObservationV1,
)

__all__: tuple[str, ...] = ()


def _invalid() -> None:
    raise ValueError("invalid_d2_evidence_checkpoint") from None


@dataclass(frozen=True, slots=True, repr=False)
class RW0D2BoundEffectProofV1:
    command: DevelopmentBoundEffectEstablishmentCommandV1 = field(repr=False)
    confirmed_result: DevelopmentBoundEffectEstablishmentResultV1 = field(repr=False)
    current_fence: EffectFenceV1 = field(repr=False)
    delivery: DeliveryEnvelopeV1 = field(repr=False)
    requirement: DevelopmentValidationRequirementEvidenceV1 | DevelopmentReviewRequirementEvidenceV1 = field(repr=False)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if (type(self) is not RW0D2BoundEffectProofV1
                or type(self.confirmed_result) is not DevelopmentBoundEffectEstablishmentResultV1
                or type(self.current_fence) is not EffectFenceV1
                or type(self.delivery) is not DeliveryEnvelopeV1
                or type(self.requirement) not in (
                    DevelopmentValidationRequirementEvidenceV1,
                    DevelopmentReviewRequirementEvidenceV1,
                )):
            _invalid()
        try:
            command = _require_exact_development_bound_effect_command(self.command)
            if (self.confirmed_result.command_digest != command.command_digest
                    or self.confirmed_result.disposition not in ("committed", "exact_replay")
                    or self.current_fence.to_mapping() != command.effect_fence.to_mapping()
                    or self.delivery.to_mapping() != command.delivery_envelope.to_mapping()
                    or self.requirement != command.requirement_evidence):
                _invalid()
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception:
            _invalid()

    def __reduce__(self) -> object:
        raise TypeError("serialization disabled")


@dataclass(frozen=True, slots=True, repr=False)
class RW0D2EvidenceCheckpointV1:
    d1_handback: RW0D1HandbackV1 = field(repr=False)
    capture: D1CandidateCapture = field(repr=False)
    capsule_manifest: CandidateCapsuleManifestV1 = field(repr=False)
    adapter_exit: WorkerObservationV1 = field(repr=False)
    bound_effects: tuple[RW0D2BoundEffectProofV1, RW0D2BoundEffectProofV1] = field(repr=False)
    admitted_families: tuple[RW0C1CheckedEvidenceFamilyV1, ...] = field(repr=False)
    authority_sources: tuple[RW0AuthorityVerificationObservationV1, RW0AuthorityVerificationObservationV1, RW0AuthorityVerificationObservationV1] = field(repr=False)
    readiness_source: RW0RemoteHostReadinessObservationV1 = field(repr=False)
    qualifications: tuple[RW0EffectHostQualificationV1, RW0EffectHostQualificationV1] = field(repr=False)
    validator_process: D1ProcessOutcome = field(repr=False)
    reviewer_process: D1ProcessOutcome = field(repr=False)
    validation_source: RW0D2CheckingEvidenceV1 = field(repr=False)
    review_source: RW0D2CheckingEvidenceV1 = field(repr=False)
    validation_result_set: PostExecutionValidationResultSetV1 = field(repr=False)
    review_result_set: PostExecutionReviewResultSetV1 = field(repr=False)
    validation_disposition: ValidationDispositionV1 = field(repr=False)
    review_disposition: IndependentReviewDispositionV1 = field(repr=False)
    reviewer_separation: PostExecutionReviewerSeparationEvaluationV1 = field(repr=False)
    policy_sources: tuple[PostExecutionStandingPolicySourceAttestationV1, PostExecutionRiskPolicyAttestationV1, FiniteBacklogRiskSourceBindingV1, PostExecutionRiskSourceProfileV1, PostExecutionRiskSourceBindingV1] = field(repr=False)
    policy_matrices: tuple[PostExecutionStandingPolicyBranchMatrixV1, PostExecutionRiskLaneBranchMatrixV1] = field(repr=False)
    support_sets: tuple[PostExecutionSupportSetV1, ...] = field(repr=False)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Revalidate every nested evidence value without I/O or run custody."""
        if (type(self) is not RW0D2EvidenceCheckpointV1
                or type(self.d1_handback) is not RW0D1HandbackV1
                or type(self.capture) is not D1CandidateCapture
                or type(self.capsule_manifest) is not CandidateCapsuleManifestV1
                or type(self.adapter_exit) is not WorkerObservationV1
                or type(self.bound_effects) is not tuple or len(self.bound_effects) != 2
                or type(self.admitted_families) is not tuple
                or type(self.authority_sources) is not tuple or len(self.authority_sources) != 3
                or type(self.readiness_source) is not RW0RemoteHostReadinessObservationV1
                or type(self.qualifications) is not tuple or len(self.qualifications) != 2
                or type(self.validator_process) is not D1ProcessOutcome
                or type(self.reviewer_process) is not D1ProcessOutcome
                or type(self.validation_source) is not RW0D2CheckingEvidenceV1
                or type(self.review_source) is not RW0D2CheckingEvidenceV1
                or type(self.validation_result_set) is not PostExecutionValidationResultSetV1
                or type(self.review_result_set) is not PostExecutionReviewResultSetV1
                or type(self.validation_disposition) is not ValidationDispositionV1
                or type(self.review_disposition) is not IndependentReviewDispositionV1
                or type(self.reviewer_separation) is not PostExecutionReviewerSeparationEvaluationV1
                or type(self.policy_sources) is not tuple or len(self.policy_sources) != 5
                or type(self.policy_matrices) is not tuple or len(self.policy_matrices) != 2
                or type(self.support_sets) is not tuple or len(self.support_sets) < 3):
            _invalid()
        try:
            self.d1_handback.validate()
            layout = _resolve_d2_checked_layout(self.d1_handback)
            layout.validate_prefix(self.admitted_families, complete=True)
            self.capture.validate()
            CandidateCapsuleManifestV1.from_mapping(self.capsule_manifest.to_mapping())
            WorkerObservationV1.from_mapping(self.adapter_exit.to_mapping())
            for proof in self.bound_effects:
                if type(proof) is not RW0D2BoundEffectProofV1:
                    _invalid()
                proof.validate()
            for family in self.admitted_families:
                if type(family) is not RW0C1CheckedEvidenceFamilyV1:
                    _invalid()
                family.validate()
            for source in self.authority_sources:
                if type(source) is not RW0AuthorityVerificationObservationV1:
                    _invalid()
                RW0AuthorityVerificationObservationV1.from_mapping(source.to_mapping())
            RW0RemoteHostReadinessObservationV1.from_mapping(self.readiness_source.to_mapping())
            for qualification in self.qualifications:
                if type(qualification) is not RW0EffectHostQualificationV1:
                    _invalid()
                RW0EffectHostQualificationV1.from_mapping(qualification.to_mapping())
            for process in (self.validator_process, self.reviewer_process):
                process.validate()
                if not process.clean_success or not process.cleanup_complete:
                    _invalid()
            for source in (self.validation_source, self.review_source):
                source.validate()
            for value in (
                self.validation_result_set, self.review_result_set,
                self.validation_disposition, self.review_disposition,
                self.reviewer_separation, *self.policy_sources,
                *self.policy_matrices, *self.support_sets,
            ):
                value._validate_value()
            if (self.d1_handback.status != "capsule_ready"
                    or not self.d1_handback.workspace_cleaned
                    or self.d1_handback.capture is not self.capture
                    or self.d1_handback.capsule_manifest is not self.capsule_manifest
                    or self.d1_handback.adapter_exit is not self.adapter_exit
                    or tuple(proof.command.effect_class for proof in self.bound_effects)
                    != ("validate_candidate", "review_candidate")
                    or self.validation_source.process is not self.validator_process
                    or self.review_source.process is not self.reviewer_process
                    or self.validation_source.observation.to_mapping()
                    != layout.family(self.admitted_families, "validator_observation").evidence_value.to_mapping()
                    or self.review_source.observation.to_mapping()
                    != layout.family(self.admitted_families, "reviewer_observation").evidence_value.to_mapping()
                    or self.validation_result_set.source_observation_digest
                    != self.validation_source.observation.observation_digest
                    or self.review_result_set.source_observation_digest
                    != self.review_source.observation.observation_digest
                    or self.validation_disposition.validation_result_set_digest
                    != self.validation_result_set.result_set_digest
                    or self.review_disposition.review_result_set_digest
                    != self.review_result_set.result_set_digest
                    or self.review_disposition.reviewer_separation_digest
                    != self.reviewer_separation.evaluation_digest
                    or self.reviewer_separation.status != "separate"):
                _invalid()
            self._validate_authority_role_bindings()
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception:
            _invalid()

    def _validate_authority_role_bindings(self) -> None:
        """Join each historical authority source to its checked C1 role family."""
        basis = self.d1_handback.phase_basis
        author = self.d1_handback.author_command
        attempt = author.attempt_fence
        author_fence = author.effect_fence
        author_command = author.worker_command
        role_fences = (
            self.bound_effects[0].current_fence,
            self.bound_effects[1].current_fence,
            author_fence,
        )
        layout = _resolve_d2_checked_layout(self.d1_handback)
        role_families = tuple(layout.index(role) for role in (
            "validation_authority", "review_authority", "author_authority",
        ))
        member_refs: list[str] = []
        for source_index, (family_index, fence) in enumerate(zip(
            role_families, role_fences, strict=True,
        )):
            source = self.authority_sources[source_index]
            family = self.admitted_families[family_index]
            result = family.admission_result
            member = family.membership
            source_identity = (
                source.schema_id, source.observation_ref, source.observation_digest,
            )
            if (type(result.kind_rank) is not int or result.kind_rank != 1
                    or family.evidence_value.to_mapping() != source.to_mapping()
                    or any(
                        type(row.value("kind_rank")) is not int
                        or row.value("kind_rank") != 1
                        or tuple(row.value(name) for name in (
                            "value_schema_id", "value_ref", "value_digest",
                        )) != source_identity
                        for row in (family.registry, family.payload, member, family.receipt)
                    )
                    or (result.value_schema_id, result.value_ref, result.value_digest)
                    != source_identity
                    or any(tuple(row.value(name) for name in (
                        "phase_basis_ref", "phase_basis_digest",
                    )) != (basis.basis_ref, basis.basis_digest)
                           for row in (family.phase, member, family.receipt))
                    or (result.phase_basis_ref, result.phase_basis_digest)
                    != (basis.basis_ref, basis.basis_digest)
                    or (source.phase_basis_ref, source.phase_basis_digest)
                    != (basis.basis_ref, basis.basis_digest)
                    or (member.value("membership_ref"), member.value("membership_digest"))
                    != (result.membership_ref, result.membership_digest)
                    or (family.receipt.value("membership_ref"),
                        family.receipt.value("membership_digest"))
                    != (result.membership_ref, result.membership_digest)
                    or member.value("relation_set_digest") != result.relation_set_digest
                    or family.receipt.value("result_projection_digest")
                    != result.committed_projection_digest()
                    or source.effect_class != fence.effect_class
                    or (source.effect_fence_ref, source.effect_fence_digest)
                    != (fence.effect_fence_ref, fence.effect_fence_digest)
                    or (source.parent_grant_ref, source.parent_grant_digest)
                    != (attempt.parent_standing_grant_ref,
                        attempt.parent_standing_grant_digest)
                    or (fence.parent_standing_grant_ref,
                        fence.parent_standing_grant_digest)
                    != (attempt.parent_standing_grant_ref,
                        attempt.parent_standing_grant_digest)
                    or (source.attempt_basis_ref, source.attempt_basis_digest)
                    != (attempt.attempt_authorization_ref,
                        attempt.attempt_authorization_digest)
                    or (source.effect_basis_ref, source.effect_basis_digest)
                    != (fence.effect_authorization_ref,
                        fence.effect_authorization_digest)
                    or (source.attempt_fence_ref, source.attempt_fence_digest)
                    != (attempt.attempt_fence_ref, attempt.attempt_fence_digest)
                    or (fence.attempt_fence_ref, fence.attempt_fence_digest)
                    != (attempt.attempt_fence_ref, attempt.attempt_fence_digest)
                    or (source.audience_ref, source.repository_ref,
                        source.base_git_object_format, source.base_git_oid)
                    != (author_command.program_ref, author_command.repository_ref,
                        author_command.base_git_object_format,
                        author_command.base_git_oid)
                    or source.path_scope_digest != basis.path_scope_digest
                    or (source.current_effect_head_digest,
                        source.current_delivery_head_digest,
                        source.global_stop_ref, source.global_stop_version,
                        source.global_stop_state)
                    != (basis.current_effect_head_digest,
                        basis.current_delivery_head_digest,
                        basis.global_stop_ref, basis.global_stop_version,
                        basis.global_stop_state)):
                _invalid()
            if len(family.relations.relations) != 1:
                _invalid()
            relation = family.relations.relations[0]
            binding = relation.binding
            if (type(binding.value("subject_kind_rank")) is not int
                    or binding.value("subject_kind_rank") != 1
                    or binding.value("subject_type") != "evidence_membership"
                    or type(binding.value("relation_rank")) is not int
                    or binding.value("relation_rank") != 0
                    or tuple(binding.value(name) for name in (
                        "phase_basis_ref", "phase_basis_digest",
                        "subject_membership_ref", "subject_membership_digest",
                        "subject_value_ref", "subject_value_digest",
                        "subject_value_schema_id",
                    )) != (
                        basis.basis_ref, basis.basis_digest,
                        result.membership_ref, result.membership_digest,
                        source.observation_ref, source.observation_digest,
                        source.schema_id,
                    )):
                _invalid()
            expected_operands = (
                ("attempt_fence", "development_attempt_fence",
                 attempt.attempt_fence_ref, attempt.attempt_fence_digest),
                ("author_effect_fence", "development_effect_fence",
                 author_fence.effect_fence_ref, author_fence.effect_fence_digest),
                ("current_effect_fence", "development_effect_fence",
                 fence.effect_fence_ref, fence.effect_fence_digest),
                ("author_command", "development_author_command",
                 author_command.command_ref, author_command.command_digest),
            )
            if source_index < 2:
                expected_operands += ((
                    "target_capsule_manifest", None,
                    self.capsule_manifest.capsule_manifest_ref,
                    self.capsule_manifest.portable_capsule_digest,
                ),)
            if (type(binding.value("operand_count")) is not int
                    or binding.value("operand_count") != len(expected_operands)
                    or tuple(tuple(operand.value(name) for name in (
                        "operand_role", "owner_role", "operand_ref", "operand_digest",
                    )) for operand in relation.operands) != expected_operands):
                _invalid()
            if source_index < 2:
                qualification = self.qualifications[source_index]
                if (qualification.verification_ref,
                        qualification.verification_digest,
                        qualification.phase_basis_ref,
                        qualification.phase_basis_digest,
                        qualification.effect_intent_ref,
                        qualification.effect_fence_ref,
                        qualification.effect_fence_digest,
                        qualification.readiness_ref,
                        qualification.readiness_digest) != (
                            source.observation_ref, source.observation_digest,
                            basis.basis_ref, basis.basis_digest,
                            fence.effect_intent_ref,
                            fence.effect_fence_ref, fence.effect_fence_digest,
                            self.readiness_source.observation_ref,
                            self.readiness_source.observation_digest):
                    _invalid()
            member_refs.append(result.membership_ref)
        if len(set(member_refs)) != 3:
            _invalid()

    def __reduce__(self) -> object:
        raise TypeError("serialization disabled")
