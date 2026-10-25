"""Parent-only D2 A sequence through the existing guarded durable owners."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib

from ._development_author_effect_establishment_contracts import (
    _development_author_effect_establishment_write_plan,
)
from ._development_bound_effect_establishment_contracts import (
    DevelopmentBoundEffectEstablishmentCommandV1,
    DevelopmentBoundEffectEstablishmentResultV1,
    _development_bound_effect_authorization_safe_binding,
    _development_bound_effect_establishment_write_plan,
    _reduce_development_bound_effect_establishment_command,
)
from ._development_program_initialization_contracts import (
    _development_program_initialization_write_plan,
)
from ._rw0_c1_semantic_values import (
    RW0C1AdmitEvidenceCommandV1, RW0C1AdmitEvidenceResultV1,
    RW0C1MemberLocatorV1, RW0C1OwnerRowLocatorV1,
    RW0C1RecoveryDispositionV1, RW0C1TransientPrivateBindingV1,
    RW0C1WireProcessResultClassificationBindingV1,
    RW0C1WireWorkerResultBindingV1, evidence_admission_recovery_selector,
)
from ._rw0_d1_handback import RW0D1OfflineRun
from ._rw0_d1_offline import D1ArtificialFixture, _reduce_development_program_initialization_command
from ._rw0_d1_process_supervisor import run_fake_module
from ._rw0_d2a_evidence import (
    RW0D2CheckingEvidenceV1, _D2CheckingInputInvalid,
    _resolve_d2_checked_layout, artificial_authority_observation,
    artificial_host_qualification, artificial_policy_evidence,
    artificial_readiness_observation, checked_reviewer_separation,
    checking_disposition, checking_result_set, normalize_checking_evidence,
)
from ._rw0_d2a_handback import RW0D2BoundEffectProofV1, RW0D2EvidenceCheckpointV1
from ._rw0_d2a_process_frames import encode_checking_request
from ._rw0_d2a_workspace import D2Reconstruction
from ._sqlite_rw0_c1 import RW0C1CheckedEvidenceFamilyV1
from ._worker_execution_semantic_values import WorkSpecV1
from .sqlite_errors import SQLiteMutationStoreError
from .sqlite_location import CoordinatorStateLocation
from .sqlite_writer_session import acquire_sqlite_writer_session

__all__: tuple[str, ...] = ()


class _D2AStop(ValueError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        self.bound_effects: tuple[RW0D2BoundEffectProofV1, ...] = ()
        self.checked_families: tuple[RW0C1CheckedEvidenceFamilyV1, ...] = ()
        self.child_outcomes: tuple[object, ...] = ()
        super().__init__(reason)


@dataclass(slots=True, repr=False)
class _D2AProgress:
    bound_effects: list[RW0D2BoundEffectProofV1] = field(default_factory=list)
    checked_families: list[RW0C1CheckedEvidenceFamilyV1] = field(default_factory=list)
    child_outcomes: list[object] = field(default_factory=list)


@dataclass(frozen=True, slots=True, repr=False)
class _RW0D2AAdmittedBundle:
    bound_commands: tuple[DevelopmentBoundEffectEstablishmentCommandV1, ...] = field(repr=False)
    bound_results: tuple[DevelopmentBoundEffectEstablishmentResultV1, ...] = field(repr=False)
    checked_families: tuple[RW0C1CheckedEvidenceFamilyV1, ...] = field(repr=False)
    checking_evidence: tuple[RW0D2CheckingEvidenceV1, ...] = field(repr=False)
    checkpoint: RW0D2EvidenceCheckpointV1 = field(repr=False)

    def validate(self) -> None:
        if (type(self) is not _RW0D2AAdmittedBundle
                or type(self.bound_commands) is not tuple or len(self.bound_commands) != 2
                or type(self.bound_results) is not tuple or len(self.bound_results) != 2
                or type(self.checked_families) is not tuple
                or type(self.checking_evidence) is not tuple or len(self.checking_evidence) != 2
                or type(self.checkpoint) is not RW0D2EvidenceCheckpointV1):
            raise _D2AStop("evidence_incomplete")
        if tuple(command.effect_class for command in self.bound_commands) != (
            "validate_candidate", "review_candidate"
        ) or any(result.command_digest != command.command_digest
                 for result, command in zip(self.bound_results, self.bound_commands, strict=True)):
            raise _D2AStop("evidence_mismatch")
        for family in self.checked_families:
            if type(family) is not RW0C1CheckedEvidenceFamilyV1:
                raise _D2AStop("evidence_mismatch")
            family.validate()
        _resolve_d2_checked_layout(self.checkpoint.d1_handback).validate_prefix(
            self.checked_families, complete=True,
        )
        for evidence in self.checking_evidence:
            if type(evidence) is not RW0D2CheckingEvidenceV1:
                raise _D2AStop("evidence_mismatch")
            evidence.validate()
        self.checkpoint.validate()
        if (self.checkpoint.admitted_families != self.checked_families
                or self.checkpoint.validation_source is not self.checking_evidence[0]
                or self.checkpoint.review_source is not self.checking_evidence[1]):
            raise _D2AStop("evidence_mismatch")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _preimages(work_spec: WorkSpecV1, handback: object) -> tuple[int, str, int, str]:
    genesis = _reduce_development_program_initialization_command(
        mutation_ref="mutation-genesis.d1",
        program_ref=work_spec.program_ref,
        program_version_ref=work_spec.program_version_ref,
        accepted_intent_revision_ref=work_spec.accepted_intent_revision_ref,
        decision_ref="decision.d1",
        preassigned_semantic_attempt_ref="semantic-attempt.d1",
        preassigned_candidate_ref="candidate.d1",
        coding_global_stop_ref="global-stop-clear",
        coding_global_stop_version=0,
        source_intent_ref="source-intent.d1", source_intent_digest="1" * 64,
        work_spec=work_spec,
    )
    if genesis.command_digest != handback.program_result.command_digest:
        raise _D2AStop("d1_genesis_mismatch")
    plan = _development_program_initialization_write_plan(
        genesis, handback.program_result.transaction_timestamp,
    )
    return (
        plan.program_head.head_revision, plan.program_head.head_digest,
        plan.work_item_head.head_revision, plan.work_item_head.head_digest,
    )


def _bound_command(handback: object, work_spec: WorkSpecV1, effect_class: str) -> DevelopmentBoundEffectEstablishmentCommandV1:
    author = handback.author_command
    suffix = "validation" if effect_class == "validate_candidate" else "review"
    binding = _development_bound_effect_authorization_safe_binding(
        parent_standing_grant_ref=author.attempt_fence.parent_standing_grant_ref,
        parent_standing_grant_digest=author.attempt_fence.parent_standing_grant_digest,
        effect_authorization_ref="effect-authorization.d2." + suffix,
        effect_authorization_digest=hashlib.sha256(("effect-authorization.d2." + suffix).encode()).hexdigest(),
        attempt_fence_ref=author.attempt_fence_ref,
        attempt_fence_digest=author.attempt_fence.attempt_fence_digest,
        semantic_attempt_ref=author.semantic_attempt_ref,
        effect_intent_ref="effect-intent.d2." + suffix,
        effect_class=effect_class,
        path_ceiling=author.attempt_fence.path_ceiling,
        effect_ceilings=author.effect_authorization_safe_binding.effect_ceilings,
        expires_at=author.effect_authorization_safe_binding.expires_at,
        global_stop_ref=author.coding_global_stop_ref,
        global_stop_version=author.coding_global_stop_version,
    )
    return _reduce_development_bound_effect_establishment_command(
        mutation_ref="mutation.d2." + suffix,
        effect_class=effect_class,
        effect_intent_ref="effect-intent.d2." + suffix,
        effect_fence_ref="effect-fence.d2." + suffix,
        authority_evaluation_ref="authority-evaluation.d2." + suffix,
        delivery_attempt_ref="delivery-attempt.d2." + suffix,
        adapter_safe_correlation_ref="adapter-correlation.d2." + suffix,
        author_command=author,
        selected_disposition=handback.section41_result,
        phase_basis=handback.phase_basis,
        work_spec=work_spec,
        capture=handback.capture,
        capsule_manifest=handback.capsule_manifest,
        requirement_evidence=(author.validation_requirement_evidence
                              if effect_class == "validate_candidate"
                              else author.review_requirement_evidence),
        effect_authorization_safe_binding=binding,
    )


def _establish_bound(location: CoordinatorStateLocation, command: DevelopmentBoundEffectEstablishmentCommandV1) -> DevelopmentBoundEffectEstablishmentResultV1:
    writer = acquire_sqlite_writer_session(location)
    uncertain = False
    result: object = None
    try:
        try:
            result = writer._establish_development_bound_effect_intent(command)
        except SQLiteMutationStoreError as error:
            if error.error_class != "commit_outcome_unknown":
                raise _D2AStop("bound_effect_conflict") from None
            uncertain = True
    finally:
        try:
            writer.close()
        except Exception:
            raise _D2AStop("writer_cleanup_unresolved") from None
    if uncertain:
        with acquire_sqlite_writer_session(location) as fresh:
            recovery = fresh._resolve_development_bound_effect_establishment_commit_outcome(command)
            if recovery.disposition != "committed_exact":
                raise _D2AStop("bound_effect_commit_unresolved")
            result = recovery.committed_result
    if (type(result) is not DevelopmentBoundEffectEstablishmentResultV1
            or result.command_digest != command.command_digest):
        raise _D2AStop("bound_effect_conflict")
    return result


def _locator(role: str, row: object, ref: str, digest: str, owner_role: str) -> RW0C1OwnerRowLocatorV1:
    return RW0C1OwnerRowLocatorV1(
        role, owner_role, getattr(row, ref), getattr(row, digest),
    )


def _member(role: str, result: RW0C1AdmitEvidenceResultV1) -> RW0C1MemberLocatorV1:
    return RW0C1MemberLocatorV1(
        role, result.kind_rank, result.membership_ref, result.membership_digest,
        result.value_ref, result.value_digest,
    )


def _admit_and_check(
    location: CoordinatorStateLocation, command: RW0C1AdmitEvidenceCommandV1,
) -> RW0C1CheckedEvidenceFamilyV1:
    writer = acquire_sqlite_writer_session(location)
    uncertain = False
    result: object = None
    try:
        try:
            result = writer._admit_rw0_evidence(command)
        except SQLiteMutationStoreError as error:
            if error.error_class != "commit_outcome_unknown":
                raise _D2AStop("c1_admission_failed") from None
            uncertain = True
        if not uncertain:
            if type(result) is not RW0C1AdmitEvidenceResultV1:
                raise _D2AStop("c1_admission_failed")
            checked = writer._read_rw0_c1_checked_family(result)
            if type(checked) is not RW0C1CheckedEvidenceFamilyV1:
                raise _D2AStop("c1_readback_failed")
            checked.validate()
            return checked
    finally:
        try:
            writer.close()
        except Exception:
            raise _D2AStop("writer_cleanup_unresolved") from None
    if uncertain:
        with acquire_sqlite_writer_session(location) as fresh:
            probe = evidence_admission_recovery_selector(command)
            recovery = fresh._resolve_rw0_c1_evidence_admission_commit_outcome(probe)
            if recovery.disposition is not RW0C1RecoveryDispositionV1.COMMITTED_EXACT:
                raise _D2AStop("c1_commit_unresolved")
            result = fresh._admit_rw0_evidence(command)
            if type(result) is not RW0C1AdmitEvidenceResultV1:
                raise _D2AStop("c1_readback_failed")
            checked = fresh._read_rw0_c1_checked_family(result)
            if type(checked) is not RW0C1CheckedEvidenceFamilyV1:
                raise _D2AStop("c1_readback_failed")
            checked.validate()
            return checked
    raise _D2AStop("c1_admission_failed")


def _admit(
    *, location: CoordinatorStateLocation, handback: object,
    preimages: tuple[int, str, int, str], label: str, rank: int, value: object,
    owners: tuple[RW0C1OwnerRowLocatorV1, ...] = (),
    dependencies: tuple[RW0C1MemberLocatorV1, ...] = (),
    transients: tuple[RW0C1TransientPrivateBindingV1, ...] = (),
) -> RW0C1CheckedEvidenceFamilyV1:
    program_revision, program_digest, work_revision, work_digest = preimages
    command = RW0C1AdmitEvidenceCommandV1(
        mutation_ref="mutation.d2.admit." + label,
        phase_basis_ref=handback.phase_basis.basis_ref,
        phase_basis_digest=handback.phase_basis.basis_digest,
        expected_program_head_revision=program_revision,
        expected_program_head_digest=program_digest,
        expected_work_item_head_revision=work_revision,
        expected_work_item_head_digest=work_digest,
        preassigned_membership_ref="membership.d2." + label,
        kind_rank=rank, evidence_value=value,
        prerequisite_member_locators=dependencies,
        owner_row_locators=owners, transient_bindings=transients,
    )
    checked = _admit_and_check(location, command)
    if checked.evidence_value.to_mapping() != value.to_mapping():
        raise _D2AStop("c1_readback_failed")
    return checked


def _run_checker(
    *, role: str, command: DevelopmentBoundEffectEstablishmentCommandV1,
    handback: object, cancelled: object, progress: _D2AProgress,
) -> tuple[RW0D2CheckingEvidenceV1, str]:
    with D2Reconstruction(
        capture=handback.capture, capsule_manifest=handback.capsule_manifest,
        author_command=handback.author_command,
    ) as reconstruction:
        root_identity = str(reconstruction.root)
        request = encode_checking_request(role, {
            "schema_id": f"governed-execution.nwp-d2-{role}-request.v1",
            "role": role,
            "invocation_ref": "invocation.d2." + role,
            "command_digest": command.command_digest,
            "effect_intent_ref": command.effect_intent_ref,
            "effect_fence_ref": command.effect_fence_ref,
            "effect_fence_digest": command.effect_fence.effect_fence_digest,
            "delivery_attempt_ref": command.delivery_attempt_ref,
            "capsule_manifest_ref": command.capsule_manifest_ref,
            "portable_capsule_digest": command.portable_capsule_digest,
            "requirement_ref": command.requirement_ref,
            "requirement_safe_digest": command.requirement_safe_digest,
            "files": [
                {"path": path, "length": len(blob),
                 "sha256": hashlib.sha256(blob).hexdigest()}
                for path, blob in command.after_blob_entries
            ],
        })
        process = run_fake_module(
            "ge_nwp_coordinator._rw0_d2a_fake_" + role,
            request, cwd=reconstruction.root,
            output_limit=64 * 1024 + 8, cancelled=cancelled,
        )
        process.validate()
        progress.child_outcomes.append(process)
        if not process.cleanup_complete:
            raise _D2AStop("process_cleanup_unresolved")
        if not process.clean_success:
            raise _D2AStop(role + "_process_failed")
        try:
            evidence = normalize_checking_evidence(
                role=role, process=process, command=command,
                author_command=handback.author_command,
                adapter_exit=handback.adapter_exit,
            )
        except _D2CheckingInputInvalid:
            raise _D2AStop(role + "_evidence_invalid") from None
        reconstruction.verify()
        return evidence, root_identity


def _run_d2a_checked_evidence_impl(
    d1_run: RW0D1OfflineRun, work_spec: WorkSpecV1,
    fixture: D1ArtificialFixture, *, cancelled: object = None,
    progress: _D2AProgress,
) -> _RW0D2AAdmittedBundle:
    """Borrow one D1 run; never assume ownership of its disposable database."""
    if (type(d1_run) is not RW0D1OfflineRun
            or type(work_spec) is not WorkSpecV1
            or type(fixture) is not D1ArtificialFixture
            or fixture.work_spec.to_mapping() != work_spec.to_mapping()
            or d1_run.closed or d1_run.handback.status != "capsule_ready"
            or (cancelled is not None and not callable(cancelled))):
        raise _D2AStop("invalid_d1_input")
    handback = d1_run.handback
    handback.validate()
    layout = _resolve_d2_checked_layout(handback)
    location = d1_run.location
    preimages = _preimages(work_spec, handback)
    author = handback.author_command
    author_plan = _development_author_effect_establishment_write_plan(
        author, handback.author_result.transaction_timestamp,
    )
    bound_commands = tuple(
        _bound_command(handback, work_spec, kind)
        for kind in ("validate_candidate", "review_candidate")
    )
    bound_results_list: list[DevelopmentBoundEffectEstablishmentResultV1] = []
    for command in bound_commands:
        result = _establish_bound(location, command)
        bound_results_list.append(result)
        progress.bound_effects.append(RW0D2BoundEffectProofV1(
            command, result, command.effect_fence, command.delivery_envelope,
            command.requirement_evidence,
        ))
    bound_results = tuple(bound_results_list)
    bound_plans = tuple(
        _development_bound_effect_establishment_write_plan(command, result.transaction_timestamp)
        for command, result in zip(bound_commands, bound_results, strict=True)
    )
    author_command_owner = _locator("author_command", author_plan.author_command,
                                    "command_ref", "command_digest", "development_author_command")
    author_delivery_owner = _locator("author_delivery", author_plan.delivery_attempt,
                                     "delivery_attempt_ref", "delivery_attempt_digest",
                                     "development_delivery_attempt")
    attempt_owner = _locator("attempt_fence", author_plan.attempt_fence,
                             "attempt_fence_ref", "attempt_fence_digest",
                             "development_attempt_fence")
    author_fence_owner = _locator("author_effect_fence", author_plan.effect_fence,
                                  "effect_fence_ref", "effect_fence_digest",
                                  "development_effect_fence")
    author_target_fence = _locator("target_effect_fence", author_plan.effect_fence,
                                   "effect_fence_ref", "effect_fence_digest",
                                   "development_effect_fence")
    author_target_delivery = _locator("target_delivery", author_plan.delivery_attempt,
                                      "delivery_attempt_ref", "delivery_attempt_digest",
                                      "development_delivery_attempt")
    author_observation_owners = (
        author_target_delivery, author_command_owner, attempt_owner,
        author_fence_owner, author_target_fence,
    )
    result_owners = (
        author_command_owner, author_delivery_owner, attempt_owner, author_fence_owner,
    )
    checked = progress.checked_families
    author_observations = handback.wire_result.observations
    for ordinal, observation in enumerate(author_observations):
        checked.append(_admit(
            location=location, handback=handback, preimages=preimages,
            label=f"author-observation.{ordinal}", rank=12,
            value=observation, owners=author_observation_owners,
        ))
    author_obs_families = tuple(checked)
    checked.append(_admit(
        location=location, handback=handback, preimages=preimages,
        label="adapter-exit", rank=12, value=handback.adapter_exit,
        owners=author_observation_owners,
    ))
    adapter_family = checked[-1]
    basis = handback.phase_basis
    lineage = basis.c2b3d_lineage
    observation_locators = tuple(
        _member(f"worker_observation:{ordinal:03d}", family.admission_result)
        for ordinal, family in enumerate(author_obs_families)
    )
    worker_binding = RW0C1WireWorkerResultBindingV1(
        "worker-result.d2", basis.basis_ref, basis.basis_digest,
        lineage.program_ref, lineage.semantic_attempt_ref, lineage.candidate_ref,
        lineage.effect_intent_ref, lineage.author_command_ref,
        lineage.attempt_fence_ref, lineage.effect_fence_ref,
        lineage.delivery_attempt_ref, observation_locators,
    )
    checked.append(_admit(
        location=location, handback=handback, preimages=preimages,
        label="worker-result", rank=13, value=worker_binding,
        owners=result_owners, dependencies=observation_locators,
    ))
    worker_result_family = checked[-1]
    result_locator = _member("worker_result_binding", worker_result_family.admission_result)
    adapter_locator = _member("adapter_observation:000", adapter_family.admission_result)
    classification_binding = RW0C1WireProcessResultClassificationBindingV1(
        "process-result.d2", basis.basis_ref, basis.basis_digest,
        lineage.program_ref, lineage.semantic_attempt_ref, lineage.candidate_ref,
        lineage.effect_intent_ref, lineage.author_command_ref,
        lineage.attempt_fence_ref, lineage.effect_fence_ref,
        lineage.delivery_attempt_ref, "present", result_locator, None,
        (adapter_locator,), None, (),
        handback.wire_classification.classification,
        handback.wire_classification.reason,
    )
    checked.append(_admit(
        location=location, handback=handback, preimages=preimages,
        label="process-result", rank=14, value=classification_binding,
        owners=result_owners, dependencies=(result_locator, adapter_locator),
    ))

    def bound_authority_owners(index: int) -> tuple[RW0C1OwnerRowLocatorV1, ...]:
        current = _locator("current_effect_fence", bound_plans[index].effect_fence,
                           "effect_fence_ref", "effect_fence_digest", "development_effect_fence")
        return (attempt_owner, author_fence_owner, current, author_command_owner)

    capsule_binding = RW0C1TransientPrivateBindingV1.candidate_capsule_manifest(
        role="target_capsule_manifest", value=handback.capsule_manifest,
    )
    authority = tuple(
        artificial_authority_observation(
            basis=basis, author_command=author,
            current_effect_fence=command.effect_fence,
            capsule_manifest=handback.capsule_manifest,
            source_suffix="validation" if index == 0 else "review",
        ) for index, command in enumerate(bound_commands)
    )
    checked.append(_admit(
        location=location, handback=handback, preimages=preimages,
        label="validation-authority", rank=1, value=authority[0],
        owners=bound_authority_owners(0), transients=(capsule_binding,),
    ))
    validation_authority = checked[-1]
    checked.append(_admit(
        location=location, handback=handback, preimages=preimages,
        label="review-authority", rank=1, value=authority[1],
        owners=bound_authority_owners(1), transients=(capsule_binding,),
    ))
    review_authority = checked[-1]
    readiness = artificial_readiness_observation()
    checked.append(_admit(
        location=location, handback=handback, preimages=preimages,
        label="readiness", rank=5, value=readiness,
    ))
    readiness_family = checked[-1]

    def qualify(index: int, label: str, authority_family: RW0C1CheckedEvidenceFamilyV1) -> None:
        qualification = artificial_host_qualification(
            basis=basis, authority=authority[index], readiness=readiness,
            current_effect_fence=bound_commands[index].effect_fence,
        )
        checked.append(_admit(
            location=location, handback=handback, preimages=preimages,
            label=label + "-qualification", rank=6, value=qualification,
            owners=(bound_authority_owners(index)[2],),
            dependencies=(
                _member("authority_observation", authority_family.admission_result),
                _member("remote_host_readiness", readiness_family.admission_result),
            ),
        ))

    def observe_checker(index: int, role: str) -> tuple[RW0D2CheckingEvidenceV1, str]:
        evidence, root = _run_checker(
            role=role, command=bound_commands[index], handback=handback,
            cancelled=cancelled, progress=progress,
        )
        target_delivery = _locator("target_delivery", bound_plans[index].delivery_attempt,
                                   "delivery_attempt_ref", "delivery_attempt_digest",
                                   "development_delivery_attempt")
        target_fence = _locator("target_effect_fence", bound_plans[index].effect_fence,
                                "effect_fence_ref", "effect_fence_digest", "development_effect_fence")
        before = RW0C1TransientPrivateBindingV1.blob_set(
            role="before_blob_set", binding_kind="before_blob_set",
            blobs=dict(bound_commands[index].before_blob_entries),
            authorized_path_scope_digest=handback.capsule_manifest.authorized_path_scope_digest,
        )
        after = RW0C1TransientPrivateBindingV1.blob_set(
            role="after_blob_set", binding_kind="after_blob_set",
            blobs=dict(bound_commands[index].after_blob_entries),
            authorized_path_scope_digest=handback.capsule_manifest.authorized_path_scope_digest,
        )
        checked.append(_admit(
            location=location, handback=handback, preimages=preimages,
            label=role + "-observation", rank=12, value=evidence.observation,
            owners=(target_delivery, author_command_owner, attempt_owner,
                    author_fence_owner, target_fence),
            transients=(capsule_binding, before, after),
        ))
        return evidence, root

    qualify(0, "validation", validation_authority)
    validation_evidence, validation_root = observe_checker(0, "validator")
    qualify(1, "review", review_authority)
    review_evidence, review_root = observe_checker(1, "reviewer")
    if validation_root == review_root:
        raise _D2AStop("reconstruction_not_independent")
    author_authority = artificial_authority_observation(
        basis=basis, author_command=author,
        current_effect_fence=author.effect_fence,
        capsule_manifest=None, source_suffix="author",
    )
    checked.append(_admit(
        location=location, handback=handback, preimages=preimages,
        label="author-authority", rank=1, value=author_authority,
        owners=(attempt_owner, author_fence_owner,
                _locator("current_effect_fence", author_plan.effect_fence,
                         "effect_fence_ref", "effect_fence_digest", "development_effect_fence"),
                author_command_owner),
    ))
    checked_families = tuple(checked)
    separation, separation_support = checked_reviewer_separation(
        checked_families=checked_families,
        capsule_manifest=handback.capsule_manifest,
        d1_handback=handback,
    )
    validation_result_set = checking_result_set(
        evidence=validation_evidence,
        qualification=layout.family(checked_families, "validation_qualification").evidence_value,
        expires_at=author.attempt_fence.expires_at,
    )
    review_result_set = checking_result_set(
        evidence=review_evidence,
        qualification=layout.family(checked_families, "review_qualification").evidence_value,
        expires_at=author.attempt_fence.expires_at,
    )
    attempt_digest = author_plan.semantic_attempt.semantic_attempt_digest
    validation_disposition, validation_support = checking_disposition(
        evidence=validation_evidence, result_set=validation_result_set,
        qualification=layout.family(checked_families, "validation_qualification").evidence_value,
        semantic_attempt_digest=attempt_digest, attempt_number=1,
        reviewer_separation=None,
    )
    review_disposition, review_support = checking_disposition(
        evidence=review_evidence, result_set=review_result_set,
        qualification=layout.family(checked_families, "review_qualification").evidence_value,
        semantic_attempt_digest=attempt_digest, attempt_number=1,
        reviewer_separation=separation,
    )
    policy_sources, policy_matrices, policy_supports = artificial_policy_evidence(
        handback=handback,
        author_authority=layout.family(checked_families, "author_authority").evidence_value,
    )
    checkpoint = RW0D2EvidenceCheckpointV1(
        d1_handback=handback,
        capture=handback.capture,
        capsule_manifest=handback.capsule_manifest,
        adapter_exit=handback.adapter_exit,
        bound_effects=tuple(
            RW0D2BoundEffectProofV1(
                command, result, command.effect_fence,
                command.delivery_envelope, command.requirement_evidence,
            ) for command, result in zip(bound_commands, bound_results, strict=True)
        ),
        admitted_families=checked_families,
        authority_sources=(
            layout.family(checked_families, "validation_authority").evidence_value,
            layout.family(checked_families, "review_authority").evidence_value,
            layout.family(checked_families, "author_authority").evidence_value,
        ),
        readiness_source=layout.family(checked_families, "readiness").evidence_value,
        qualifications=(layout.family(checked_families, "validation_qualification").evidence_value,
                        layout.family(checked_families, "review_qualification").evidence_value),
        validator_process=validation_evidence.process,
        reviewer_process=review_evidence.process,
        validation_source=validation_evidence,
        review_source=review_evidence,
        validation_result_set=validation_result_set,
        review_result_set=review_result_set,
        validation_disposition=validation_disposition,
        review_disposition=review_disposition,
        reviewer_separation=separation,
        policy_sources=policy_sources,
        policy_matrices=policy_matrices,
        support_sets=(separation_support, validation_support,
                      review_support, *policy_supports),
    )
    bundle = _RW0D2AAdmittedBundle(
        bound_commands, bound_results, checked_families,
        (validation_evidence, review_evidence), checkpoint,
    )
    bundle.validate()
    return bundle


def run_d2a_checked_evidence(
    d1_run: RW0D1OfflineRun, work_spec: WorkSpecV1,
    fixture: D1ArtificialFixture, *, cancelled: object = None,
) -> _RW0D2AAdmittedBundle:
    """Borrow D1 and retain the actual dependency-closed reached prefix on stop."""
    progress = _D2AProgress()
    try:
        return _run_d2a_checked_evidence_impl(
            d1_run, work_spec, fixture, cancelled=cancelled, progress=progress,
        )
    except _D2AStop as stop:
        stop.bound_effects = tuple(progress.bound_effects)
        stop.checked_families = tuple(progress.checked_families)
        stop.child_outcomes = tuple(progress.child_outcomes)
        raise
