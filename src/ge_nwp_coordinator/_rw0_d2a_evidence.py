"""Typed normalization of actual D2 checking-child source records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json

from ._development_author_effect_establishment_contracts import (
    DevelopmentAuthorEffectEstablishmentCommandV1,
)
from ._development_bound_effect_establishment_contracts import (
    DevelopmentBoundEffectEstablishmentCommandV1,
    _require_exact_development_bound_effect_command,
)
from ._rw0_c1_semantic_values import (
    RW0C1MemberLocatorV1, RW0C1WireProcessResultClassificationBindingV1,
    RW0C1WireWorkerResultBindingV1,
)
from ._rw0_d1_handback import RW0D1HandbackV1
from ._finite_backlog_risk_source_adapter import (
    FiniteBacklogRiskSourceBindingV1, finite_backlog_risk_source_projection,
)
from ._rw0_d1_process_supervisor import D1ProcessOutcome
from ._rw0_d2a_process_frames import D2CheckingFrameError, decode_checking_response
from ._post_execution_evidence_values import (
    IndependentReviewDispositionV1, ValidationDispositionV1,
    PostExecutionReviewResultSetV1, PostExecutionValidationResultSetV1,
    PostExecutionReviewerSeparationAuthorObservationLocatorV1,
    PostExecutionReviewerSeparationEvaluationV1, PostExecutionSupportEntryV1,
    PostExecutionSupportSetV1,
    construct_post_execution_support_set, evaluate_post_execution_reviewer_separation,
    validate_independent_review_disposition, validate_validation_disposition,
    validate_post_execution_review_result_set,
    validate_post_execution_validation_result_set,
)
from ._post_execution_policy_values import (
    PostExecutionRiskLaneBranchMatrixV1,
    PostExecutionRiskPolicyAttestationV1,
    PostExecutionStandingPolicyBranchMatrixV1,
    PostExecutionStandingPolicySourceAttestationV1,
    post_execution_risk_source_binding,
    post_execution_risk_source_profile,
    validate_post_execution_risk_lane_matrix_relation,
    validate_post_execution_risk_policy_attestation,
    validate_post_execution_standing_policy_attestation,
    validate_post_execution_standing_policy_matrix_relation,
)
from ._rw0_phase_entry_semantic_values import (
    RW0AuthorityVerificationObservationV1, RW0EffectHostQualificationV1,
    RW0PhaseEntryBasisV1, RW0RemoteHostReadinessObservationV1,
    validate_authority_observation, validate_host_qualification,
)
from ._worker_execution_semantic_values import (
    CandidateCapsuleManifestV1, EffectFenceV1, WorkerObservationV1,
    validate_observation_relation,
)

__all__: tuple[str, ...] = ()

_ROLE_EFFECT = {"validator": "validate_candidate", "reviewer": "review_candidate"}
_ROLE_SOURCE = {"validator": "validator.d2.fake", "reviewer": "reviewer.d2.fake"}
_ROLE_EVIDENCE = {"validator": "evidence.d2.validation", "reviewer": "evidence.d2.review"}
_ROLE_KIND = {"validator": "validation_completed", "reviewer": "independent_review_completed"}
_ROLE_OUTCOME_REASON = {
    "validator": frozenset({
        ("passed", "validation_passed"),
        ("failed", "validation_failed_repairable"),
        ("failed", "validation_failed_replan_required"),
        ("failed", "validation_failed_terminal"),
        ("failed", "validation_failed_unclassified"),
        ("inconclusive", "validation_inconclusive"),
    }),
    "reviewer": frozenset({
        ("passed", "review_passed"),
        ("failed", "review_failed_repair_required"),
        ("failed", "review_failed_replan_required"),
        ("failed", "review_failed_terminal_reject"),
        ("failed", "review_failed_unclassified"),
        ("inconclusive", "review_inconclusive"),
    }),
}

_D2_TAIL_ROLES = (
    "adapter_exit", "worker_result", "process_result",
    "validation_authority", "review_authority", "readiness",
    "validation_qualification", "validator_observation",
    "review_qualification", "reviewer_observation", "author_authority",
)
_D2_TAIL_LABELS = (
    "adapter-exit", "worker-result", "process-result",
    "validation-authority", "review-authority", "readiness",
    "validation-qualification", "validator-observation",
    "review-qualification", "reviewer-observation", "author-authority",
)
_D2_TAIL_RANKS = (12, 13, 14, 1, 1, 5, 6, 12, 6, 12, 1)
_D2_LEGAL_RANKS = frozenset((
    (12, 12, *_D2_TAIL_RANKS),
    (12, 12, 12, *_D2_TAIL_RANKS),
))


@dataclass(frozen=True, slots=True)
class _D2CheckedLayout:
    """The one finite role map, anchored to the actual D1 Wire observation tuple."""

    d1_handback: RW0D1HandbackV1 = field(repr=False)
    roles: tuple[str, ...]
    labels: tuple[str, ...]
    ranks: tuple[int, ...]
    worker_count: int

    def index(self, role: str) -> int:
        if type(role) is not str or role not in self.roles:
            _fail()
        return self.roles.index(role)

    def through(self, role: str) -> int:
        return self.index(role) + 1

    def family(self, families: tuple[object, ...], role: str) -> object:
        return families[self.index(role)]

    def validate_prefix(self, families: tuple[object, ...], *, complete: bool = False) -> None:
        from ._sqlite_rw0_c1 import RW0C1CheckedEvidenceFamilyV1

        if (type(families) is not tuple or len(families) > len(self.roles)
                or (complete and len(families) != len(self.roles))):
            _fail()
        basis = self.d1_handback.phase_basis
        observations = self.d1_handback.wire_result.observations
        types = (
            *(WorkerObservationV1 for _ in observations),
            WorkerObservationV1, RW0C1WireWorkerResultBindingV1,
            RW0C1WireProcessResultClassificationBindingV1,
            RW0AuthorityVerificationObservationV1,
            RW0AuthorityVerificationObservationV1,
            RW0RemoteHostReadinessObservationV1,
            RW0EffectHostQualificationV1, WorkerObservationV1,
            RW0EffectHostQualificationV1, WorkerObservationV1,
            RW0AuthorityVerificationObservationV1,
        )
        for index, family in enumerate(families):
            if type(family) is not RW0C1CheckedEvidenceFamilyV1:
                _fail()
            family.validate()
            result = family.admission_result
            if (type(result.kind_rank) is not int or result.kind_rank != self.ranks[index]
                    or result.mutation_ref != "mutation.d2.admit." + self.labels[index]
                    or result.membership_ref != "membership.d2." + self.labels[index]
                    or type(family.evidence_value) is not types[index]
                    or (result.phase_basis_ref, result.phase_basis_digest)
                    != (basis.basis_ref, basis.basis_digest)):
                _fail()
            if index < self.worker_count and (
                family.evidence_value.to_mapping() != observations[index].to_mapping()
            ):
                _fail()
            if index == self.index("adapter_exit") and (
                family.evidence_value.to_mapping() != self.d1_handback.adapter_exit.to_mapping()
            ):
                _fail()
            if index == self.index("worker_result"):
                members = family.evidence_value.observation_memberships
                if (len(members) != self.worker_count
                        or any(not _same_member(locator, prior, f"worker_observation:{ordinal:03d}")
                               for ordinal, (locator, prior) in enumerate(zip(
                                   members, families[:self.worker_count], strict=True,
                               )))):
                    _fail()
            if index == self.index("process_result"):
                value = family.evidence_value
                if (value.result_state != "present" or value.result_failure_reason is not None
                        or value.request_membership is not None or value.process_observations
                        or not _same_member(value.result_membership,
                                            self.family(families, "worker_result"),
                                            "worker_result_binding")
                        or len(value.adapter_observations) != 1
                        or not _same_member(value.adapter_observations[0],
                                            self.family(families, "adapter_exit"),
                                            "adapter_observation:000")
                        or (value.classification, value.reason) != (
                            self.d1_handback.wire_classification.classification,
                            self.d1_handback.wire_classification.reason,
                        )):
                    _fail()


def _same_member(locator: object, family: object, role: str) -> bool:
    if type(locator) is not RW0C1MemberLocatorV1:
        return False
    result = family.admission_result
    return (
        locator.role == role
        and (locator.kind_rank, locator.membership_ref, locator.membership_digest,
             locator.value_ref, locator.value_digest)
        == (result.kind_rank, result.membership_ref, result.membership_digest,
            result.value_ref, result.value_digest)
    )


def _resolve_d2_checked_layout(d1_handback: RW0D1HandbackV1) -> _D2CheckedLayout:
    if type(d1_handback) is not RW0D1HandbackV1:
        _fail()
    d1_handback.validate()
    if d1_handback.status != "capsule_ready" or d1_handback.wire_result is None:
        _fail()
    observations = d1_handback.wire_result.observations
    if type(observations) is not tuple or len(observations) not in (2, 3):
        _fail()
    kinds = tuple(
        item.observation_kind if type(item) is WorkerObservationV1 else None
        for item in observations
    )
    expected = (("worker_started", "worker_completed") if len(observations) == 2
                else ("worker_started", "candidate_captured", "worker_completed"))
    if kinds != expected:
        _fail()
    count = len(observations)
    return _D2CheckedLayout(
        d1_handback,
        tuple(f"worker_observation:{ordinal:03d}" for ordinal in range(count))
        + _D2_TAIL_ROLES,
        tuple(f"author-observation.{ordinal}" for ordinal in range(count))
        + _D2_TAIL_LABELS,
        (12,) * count + _D2_TAIL_RANKS,
        count,
    )


def _fail() -> None:
    raise ValueError("invalid_d2_checking_evidence")


class _D2CheckingInputInvalid(ValueError):
    """Only a decoded child frame or its closed command relation is invalid."""


def _decode_child_checking_record(
    role: str, frame: bytes, command: DevelopmentBoundEffectEstablishmentCommandV1,
    adapter_exit: WorkerObservationV1,
) -> dict[str, object]:
    try:
        record = decode_checking_response(role, frame)
    except D2CheckingFrameError:
        raise _D2CheckingInputInvalid("invalid_d2_checking_child_record") from None
    observed_at = record["observed_at"]
    try:
        parsed_at = datetime.strptime(observed_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise _D2CheckingInputInvalid("invalid_d2_checking_child_record") from None
    if (parsed_at.strftime("%Y-%m-%dT%H:%M:%SZ") != observed_at
            or (record["outcome"], record["reason_code"]) not in _ROLE_OUTCOME_REASON[role]):
        raise _D2CheckingInputInvalid("invalid_d2_checking_child_record") from None
    if (record["command_digest"] != command.command_digest
            or record["effect_fence_ref"] != command.effect_fence_ref
            or record["effect_fence_digest"] != command.effect_fence.effect_fence_digest
            or record["delivery_attempt_ref"] != command.delivery_attempt_ref
            or record["capsule_manifest_ref"] != command.capsule_manifest_ref
            or record["portable_capsule_digest"] != command.portable_capsule_digest
            or record["source_ref"] != _ROLE_SOURCE[role]
            or record["evidence_ref"] != _ROLE_EVIDENCE[role]
            or record["invocation_ref"] != "invocation.d2." + role
            or tuple(record["file_digests"]) != tuple(
                entry.after_blob_sha256 for entry in command.capsule_manifest.entries
            )
            or record["observed_at"] < adapter_exit.observed_at):
        raise _D2CheckingInputInvalid("invalid_d2_checking_child_record") from None
    return record


def _identity_digest(schema: str, mapping: dict[str, object]) -> str:
    payload = json.dumps(mapping, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256((schema + ".identity").encode("utf-8") + b"\0" + payload).hexdigest()


def artificial_authority_observation(
    *, basis: RW0PhaseEntryBasisV1,
    author_command: DevelopmentAuthorEffectEstablishmentCommandV1,
    current_effect_fence: EffectFenceV1,
    capsule_manifest: CandidateCapsuleManifestV1 | None,
    source_suffix: str,
    observed_at: str | None = None,
) -> RW0AuthorityVerificationObservationV1:
    """Supply one explicit proof-only verification assertion for an actual fence."""
    if (type(basis) is not RW0PhaseEntryBasisV1
            or type(author_command) is not DevelopmentAuthorEffectEstablishmentCommandV1
            or type(current_effect_fence) is not EffectFenceV1
            or type(source_suffix) is not str
            or source_suffix not in {"author", "validation", "review"}
            or (capsule_manifest is not None
                and type(capsule_manifest) is not CandidateCapsuleManifestV1)):
        _fail()
    attempt = author_command.attempt_fence
    now = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    identity = {
        "schema_id": RW0AuthorityVerificationObservationV1._SCHEMA,
        "observation_ref": "authority-observation.d2." + source_suffix,
        "source_ref": "authority-source.d2.fake",
        "evidence_ref": "authority-evidence.d2." + source_suffix,
        "evidence_digest": hashlib.sha256(("authority-evidence.d2." + source_suffix).encode()).hexdigest(),
        "phase_basis_ref": basis.basis_ref,
        "phase_basis_digest": basis.basis_digest,
        "parent_grant_ref": attempt.parent_standing_grant_ref,
        "parent_grant_digest": attempt.parent_standing_grant_digest,
        "grant_family_ref": "grant-family.d2.fake",
        "grant_family_digest": hashlib.sha256(b"grant-family.d2.fake").hexdigest(),
        "attempt_basis_ref": attempt.attempt_authorization_ref,
        "attempt_basis_digest": attempt.attempt_authorization_digest,
        "effect_basis_ref": current_effect_fence.effect_authorization_ref,
        "effect_basis_digest": current_effect_fence.effect_authorization_digest,
        "attempt_fence_ref": attempt.attempt_fence_ref,
        "attempt_fence_digest": attempt.attempt_fence_digest,
        "effect_fence_ref": current_effect_fence.effect_fence_ref,
        "effect_fence_digest": current_effect_fence.effect_fence_digest,
        "audience_ref": attempt.program_ref,
        "repository_ref": attempt.repository_ref,
        "base_git_object_format": attempt.base_git_object_format,
        "base_git_oid": attempt.base_git_oid,
        "path_scope_digest": basis.path_scope_digest,
        "allowed_effect_classes": list(attempt.allowed_effect_classes),
        "effect_class": current_effect_fence.effect_class,
        "parent_ceilings": attempt.aggregate_ceilings.to_mapping(),
        "status": "verified", "family_status": "compatible",
        "revocation_status": "unrevoked",
        "grant_expires_at": attempt.expires_at,
        "observed_at": now,
        "observation_expires_at": attempt.expires_at,
        "current_effect_head_digest": basis.current_effect_head_digest,
        "current_delivery_head_digest": basis.current_delivery_head_digest,
        "global_stop_ref": basis.global_stop_ref,
        "global_stop_version": basis.global_stop_version,
        "global_stop_state": basis.global_stop_state,
    }
    identity["observation_digest"] = _identity_digest(
        RW0AuthorityVerificationObservationV1._SCHEMA, identity,
    )
    try:
        observation = RW0AuthorityVerificationObservationV1.from_mapping(identity)
        validate_authority_observation(
            basis=basis, observation=observation,
            attempt_fence=attempt, author_effect_fence=author_command.effect_fence,
            current_effect_fence=current_effect_fence,
            author_command=author_command.worker_command,
            capsule_manifest=capsule_manifest, cancellation_target=None,
            now_utc=now,
        )
        return observation
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        _fail()


_PROFILES = (
    "platform_profile", "architecture_profile", "worker_artifact",
    "worker_protocol", "execution_identity_profile", "process_profile",
    "isolation_profile", "resource_profile", "cancellation_profile",
    "credential_handoff_profile", "capsule_store_profile",
    "validation_tool_profile", "review_tool_profile", "cleanup_profile",
)


def artificial_readiness_observation(
    *, observed_at: str | None = None,
) -> RW0RemoteHostReadinessObservationV1:
    """Supply a fixed artificial Linux proof profile, not host authentication."""
    now = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    identity: dict[str, object] = {
        "schema_id": RW0RemoteHostReadinessObservationV1._SCHEMA,
        "observation_ref": "readiness-observation.d2.fake",
        "source_ref": "readiness-source.d2.fake",
        "evidence_ref": "readiness-evidence.d2.fake",
        "evidence_digest": hashlib.sha256(b"readiness-evidence.d2.fake").hexdigest(),
        "safe_host_correlation_ref": "host-correlation.d2.fake",
        "status": "ready", "platform": "linux",
        "observed_at": now, "expires_at": "2099-01-01T00:00:00Z",
    }
    for stem in _PROFILES:
        reference = "profile.d2." + stem.replace("_", "-")
        identity[stem + "_ref"] = reference
        identity[stem + "_digest"] = hashlib.sha256(reference.encode()).hexdigest()
    identity["observation_digest"] = _identity_digest(
        RW0RemoteHostReadinessObservationV1._SCHEMA, identity,
    )
    try:
        return RW0RemoteHostReadinessObservationV1.from_mapping(identity)
    except Exception:
        _fail()


def artificial_host_qualification(
    *, basis: RW0PhaseEntryBasisV1,
    authority: RW0AuthorityVerificationObservationV1,
    readiness: RW0RemoteHostReadinessObservationV1,
    current_effect_fence: EffectFenceV1,
    evaluated_at: str | None = None,
) -> RW0EffectHostQualificationV1:
    """Evaluate the existing B1 relation over exact artificial source values."""
    now = evaluated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if (type(basis) is not RW0PhaseEntryBasisV1
            or type(authority) is not RW0AuthorityVerificationObservationV1
            or type(readiness) is not RW0RemoteHostReadinessObservationV1
            or type(current_effect_fence) is not EffectFenceV1):
        _fail()
    identity: dict[str, object] = {
        "schema_id": RW0EffectHostQualificationV1._SCHEMA,
        "qualification_ref": "qualification.d2." + current_effect_fence.effect_class.replace("_", "-"),
        "phase_basis_ref": basis.basis_ref,
        "phase_basis_digest": basis.basis_digest,
        "effect_intent_ref": current_effect_fence.effect_intent_ref,
        "effect_fence_ref": current_effect_fence.effect_fence_ref,
        "effect_fence_digest": current_effect_fence.effect_fence_digest,
        "verification_ref": authority.observation_ref,
        "verification_digest": authority.observation_digest,
        "readiness_ref": readiness.observation_ref,
        "readiness_digest": readiness.observation_digest,
        "required_scenario_profile_ref": "scenario.d2.fake",
        "required_scenario_profile_digest": hashlib.sha256(b"scenario.d2.fake").hexdigest(),
        "result": "qualified", "reason": "qualified", "evaluated_at": now,
    }
    for stem in _PROFILES:
        identity["required_" + stem + "_ref"] = getattr(readiness, stem + "_ref")
        identity["required_" + stem + "_digest"] = getattr(readiness, stem + "_digest")
    identity["qualification_digest"] = _identity_digest(
        RW0EffectHostQualificationV1._SCHEMA, identity,
    )
    try:
        qualification = RW0EffectHostQualificationV1.from_mapping(identity)
        validate_host_qualification(
            basis=basis, authority=authority, readiness=readiness,
            qualification=qualification, current_effect_fence=current_effect_fence,
            now_utc=now,
        )
        return qualification
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        _fail()


def _digest_domain(domain: str, mapping: dict[str, object]) -> str:
    payload = json.dumps(mapping, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(domain.encode("utf-8") + b"\0" + payload).hexdigest()


def _seal_post_value(cls: type, identity: dict[str, object]) -> object:
    """Seal an explicit owner-derived mapping using its current pure grammar."""
    reference = cls._REFERENCE
    digest = cls._DIGEST
    ref_field = reference["field"]
    if reference.get("posture") in {"generated", "generated_and_owner_supplied_for_revalidation"}:
        identity[ref_field] = reference["prefix"] + _digest_domain(
            reference["domain"], {
                key: identity[key] for key in reference["preimage_fields"]
            },
        )
    elif reference.get("posture") != "supplied_not_generated" or ref_field not in identity:
        _fail()
    digest_field = digest["field"]
    identity[digest_field] = _digest_domain(
        digest["domain"], {
            key: value for key, value in identity.items()
            if key not in digest["self_exclusion"]
        },
    )
    if set(identity) != set(cls._FIELDS):
        _fail()
    return cls.from_mapping({field_name: identity[field_name] for field_name in cls._FIELDS})


def checking_result_set(
    *, evidence: RW0D2CheckingEvidenceV1,
    qualification: RW0EffectHostQualificationV1,
    expires_at: str,
) -> PostExecutionValidationResultSetV1 | PostExecutionReviewResultSetV1:
    """Bind one actual child observation to requirement and qualification."""
    evidence.validate()
    if type(qualification) is not RW0EffectHostQualificationV1:
        _fail()
    role = evidence.role
    cls = (PostExecutionValidationResultSetV1 if role == "validator"
           else PostExecutionReviewResultSetV1)
    observation = evidence.observation
    requirement = evidence.command.requirement_evidence
    profile_ref, profile_digest = cls._PROFILE_PAIR
    result_by_reason = {
        "validation_passed": ("passed", "not_applicable"),
        "validation_failed_repairable": ("repairable_failure", "repairable"),
        "validation_failed_replan_required": ("replan_required", "same_attempt_insufficient"),
        "validation_failed_terminal": ("terminal_failure", "nonrepairable"),
        "validation_failed_unclassified": ("unknown", "unknown"),
        "validation_inconclusive": ("unknown", "unknown"),
        "review_passed": ("passed", None),
        "review_failed_repair_required": ("repair_required", None),
        "review_failed_replan_required": ("replan_required", None),
        "review_failed_terminal_reject": ("terminal_reject", None),
        "review_failed_unclassified": ("unknown", None),
        "review_inconclusive": ("unknown", None),
    }
    if observation.reason_code not in result_by_reason:
        _fail()
    result, repairability = result_by_reason[observation.reason_code]
    if (role == "validator") != (repairability is not None):
        _fail()
    identity: dict[str, object] = {
        "schema_id": cls._SCHEMA_ID,
        "profile_ref": profile_ref, "profile_digest": profile_digest,
        "source_observation_schema_id": observation.schema_id,
        "source_observation_ref": observation.observation_ref,
        "source_observation_digest": observation.observation_digest,
        "source_kind": observation.source_kind,
        "source_ref": observation.source_ref,
        "source_invocation_ref": observation.source_invocation_ref,
        "delivery_attempt_ref": observation.delivery_attempt_ref,
        "observation_kind": observation.observation_kind,
        "source_outcome": observation.outcome,
        "source_reason_code": observation.reason_code,
        "source_evidence_refs": list(observation.evidence_refs),
        "source_observed_at": observation.observed_at,
        "program_ref": observation.program_ref,
        "program_version_ref": observation.program_version_ref,
        "accepted_intent_revision_ref": observation.accepted_intent_revision_ref,
        "work_item_ref": observation.work_item_ref,
        "work_item_revision_ref": observation.work_item_revision_ref,
        "semantic_attempt_ref": observation.semantic_attempt_ref,
        "effect_intent_ref": observation.effect_intent_ref,
        "effect_class": evidence.command.effect_class,
        "command_ref": observation.command_ref,
        "command_digest": observation.command_digest,
        "attempt_fence_ref": observation.attempt_fence_ref,
        "attempt_fence_digest": observation.attempt_fence_digest,
        "effect_fence_ref": observation.effect_fence_ref,
        "effect_fence_digest": observation.effect_fence_digest,
        "candidate_ref": observation.candidate_ref,
        "capsule_manifest_ref": observation.capsule_manifest_ref,
        "portable_capsule_digest": observation.portable_capsule_digest,
        "requirement_evidence_schema_id": requirement.schema_id,
        "requirement_evidence_ref": requirement.requirement_ref,
        "requirement_evidence_safe_digest": requirement.safe_evidence_digest,
        "requirement_digest": requirement.requirement_digest,
        "requirement_work_spec_ref": requirement.work_spec_ref,
        "requirement_work_spec_digest": requirement.work_spec_digest,
        "result_author_ref": observation.source_ref,
        "result_author_invocation_ref": observation.source_invocation_ref,
        "result_set_evidence_refs": list(observation.evidence_refs),
        "result": result, "reason": observation.reason_code,
        "evaluated_at": _now_at_or_after(observation.observed_at),
        "expires_at": expires_at,
        "tool_profile_ref": getattr(
            qualification, "required_" + ("validation" if role == "validator" else "review") + "_tool_profile_ref"
        ),
        "tool_profile_digest": getattr(
            qualification, "required_" + ("validation" if role == "validator" else "review") + "_tool_profile_digest"
        ),
        "tool_qualification_schema_id": qualification.schema_id,
        "tool_qualification_ref": qualification.qualification_ref,
        "tool_qualification_digest": qualification.qualification_digest,
    }
    if role == "validator":
        identity["repairability"] = repairability
    try:
        value = _seal_post_value(cls, identity)
        if role == "validator":
            return validate_post_execution_validation_result_set(
                value, source_observation=observation,
                requirement_evidence=requirement,
                tool_qualification=qualification,
            )
        return validate_post_execution_review_result_set(
            value, source_observation=observation,
            requirement_evidence=requirement,
            tool_qualification=qualification,
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        _fail()


def _now_at_or_after(earliest: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if now < earliest:
        _fail()
    return now


def _support_set(entries: tuple[tuple[str, int, int, str, str, str], ...]) -> PostExecutionSupportSetV1:
    members = tuple(PostExecutionSupportEntryV1.from_mapping({
        "role": role, "rank": rank, "ordinal": ordinal,
        "source_schema_id": schema, "source_ref": reference,
        "source_digest": digest,
    }) for role, rank, ordinal, schema, reference, digest in entries)
    profile_ref, profile_digest = PostExecutionSupportSetV1._PROFILE_PAIR
    identity = {
        "schema_id": PostExecutionSupportSetV1._SCHEMA_ID,
        "profile_ref": profile_ref, "profile_digest": profile_digest,
        "entries": [entry.to_mapping() for entry in members],
    }
    result = _seal_post_value(PostExecutionSupportSetV1, identity)
    return construct_post_execution_support_set(result, entries=members)


def checked_reviewer_separation(
    *, checked_families: tuple[object, ...],
    capsule_manifest: CandidateCapsuleManifestV1,
    d1_handback: RW0D1HandbackV1,
) -> tuple[PostExecutionReviewerSeparationEvaluationV1, PostExecutionSupportSetV1]:
    """Derive V40 only from exact checked C1 membership/relation/value rows."""
    if type(capsule_manifest) is not CandidateCapsuleManifestV1:
        _fail()
    layout = _resolve_d2_checked_layout(d1_handback)
    layout.validate_prefix(checked_families, complete=True)
    review = layout.family(checked_families, "reviewer_observation")
    author_result = layout.family(checked_families, "worker_result")
    author_members = checked_families[:layout.worker_count]
    review_observation = review.evidence_value
    author_value = author_result.evidence_value
    review_member = review.membership.to_mapping()
    review_relation = review.relations.relations[0].binding.to_mapping()
    result_member = author_result.membership.to_mapping()
    result_relation = author_result.relations.relations[0].binding.to_mapping()
    author_rows = tuple(item.membership.to_mapping() for item in author_members)
    author_relations = tuple(item.relations.relations[0].binding.to_mapping()
                             for item in author_members)
    author_observations = tuple(item.evidence_value for item in author_members)
    support = _support_set((
        ("review_observation_membership", 1, 0, review_member["schema_id"],
         review_member["membership_ref"], review_member["membership_digest"]),
        ("author_worker_result_membership", 2, 0, result_member["schema_id"],
         result_member["membership_ref"], result_member["membership_digest"]),
    ))
    locators = []
    for ordinal, (member, relation, observation) in enumerate(zip(
        author_rows, author_relations, author_observations, strict=True,
    )):
        locator = {
            "schema_id": PostExecutionReviewerSeparationAuthorObservationLocatorV1._SCHEMA_ID,
            "ordinal": ordinal,
            "membership_schema_id": member["schema_id"],
            "membership_ref": member["membership_ref"],
            "membership_digest": member["membership_digest"],
            "value_schema_id": observation.schema_id,
            "value_ref": observation.observation_ref,
            "value_digest": observation.observation_digest,
            "relation_row_schema_id": relation["schema_id"],
            "relation_ref": relation["relation_ref"],
            "relation_digest": relation["relation_digest"],
            "relation_row_digest": relation["relation_row_digest"],
            "relation_schema_id": relation["relation_schema_id"],
            "source_kind": observation.source_kind,
            "source_ref": observation.source_ref,
            "source_invocation_ref": observation.source_invocation_ref,
            "observation_kind": observation.observation_kind,
            "effect_intent_ref": observation.effect_intent_ref,
            "effect_fence_ref": observation.effect_fence_ref,
            "effect_fence_digest": observation.effect_fence_digest,
            "delivery_attempt_ref": observation.delivery_attempt_ref,
        }
        locators.append(PostExecutionReviewerSeparationAuthorObservationLocatorV1.from_mapping(
            {name: locator[name] for name in PostExecutionReviewerSeparationAuthorObservationLocatorV1._FIELDS}
        ).to_mapping())
    author = author_observations[-1]
    identity = {
        "schema_id": PostExecutionReviewerSeparationEvaluationV1._SCHEMA_ID,
        "profile_ref": PostExecutionReviewerSeparationEvaluationV1._PROFILE_PAIR[0],
        "profile_digest": PostExecutionReviewerSeparationEvaluationV1._PROFILE_PAIR[1],
        "phase_basis_ref": review_member["phase_basis_ref"],
        "phase_basis_digest": review_member["phase_basis_digest"],
        "review_membership_schema_id": review_member["schema_id"],
        "review_membership_ref": review_member["membership_ref"],
        "review_membership_digest": review_member["membership_digest"],
        "review_value_schema_id": review_observation.schema_id,
        "review_value_ref": review_observation.observation_ref,
        "review_value_digest": review_observation.observation_digest,
        "review_relation_row_schema_id": review_relation["schema_id"],
        "review_relation_ref": review_relation["relation_ref"],
        "review_relation_digest": review_relation["relation_digest"],
        "review_relation_row_digest": review_relation["relation_row_digest"],
        "review_relation_schema_id": review_relation["relation_schema_id"],
        "author_result_membership_schema_id": result_member["schema_id"],
        "author_result_membership_ref": result_member["membership_ref"],
        "author_result_membership_digest": result_member["membership_digest"],
        "author_result_value_schema_id": author_value.schema_id,
        "author_result_value_ref": author_value.value_ref,
        "author_result_value_digest": author_value.value_digest,
        "author_result_relation_row_schema_id": result_relation["schema_id"],
        "author_result_relation_ref": result_relation["relation_ref"],
        "author_result_relation_digest": result_relation["relation_digest"],
        "author_result_relation_row_digest": result_relation["relation_row_digest"],
        "author_result_relation_schema_id": result_relation["relation_schema_id"],
        "author_observation_locators": locators,
        "review_source_kind": review_observation.source_kind,
        "review_source_ref": review_observation.source_ref,
        "review_source_invocation_ref": review_observation.source_invocation_ref,
        "author_source_kind": author.source_kind,
        "author_source_ref": author.source_ref,
        "author_source_invocation_ref": author.source_invocation_ref,
        "review_effect_intent_ref": review_observation.effect_intent_ref,
        "review_effect_fence_ref": review_observation.effect_fence_ref,
        "review_effect_fence_digest": review_observation.effect_fence_digest,
        "review_delivery_attempt_ref": review_observation.delivery_attempt_ref,
        "author_effect_intent_ref": author.effect_intent_ref,
        "author_effect_fence_ref": author.effect_fence_ref,
        "author_effect_fence_digest": author.effect_fence_digest,
        "author_delivery_attempt_ref": author.delivery_attempt_ref,
        "author_command_ref": author.command_ref,
        "author_command_digest": author.command_digest,
        "attempt_fence_ref": author.attempt_fence_ref,
        "attempt_fence_digest": author.attempt_fence_digest,
        "program_ref": author.program_ref,
        "program_version_ref": author.program_version_ref,
        "accepted_intent_revision_ref": author.accepted_intent_revision_ref,
        "work_item_ref": author.work_item_ref,
        "work_item_revision_ref": author.work_item_revision_ref,
        "semantic_attempt_ref": author.semantic_attempt_ref,
        "candidate_ref": capsule_manifest.candidate_ref,
        "capsule_manifest_ref": capsule_manifest.capsule_manifest_ref,
        "portable_capsule_digest": capsule_manifest.portable_capsule_digest,
        "support_set_ref": support.support_set_ref,
        "support_set_digest": support.support_set_digest,
        "status": "separate",
        "reason": "governed_review_graph_separate",
        "evaluated_at": review_observation.observed_at,
    }
    result = _seal_post_value(PostExecutionReviewerSeparationEvaluationV1, identity)
    return evaluate_post_execution_reviewer_separation(
        result, review_membership_row=review.membership,
        review_observation=review_observation,
        review_relation_row=review.relations.relations[0].binding,
        author_result_membership_row=author_result.membership,
        author_result_value=author_value,
        author_result_relation_row=author_result.relations.relations[0].binding,
        author_observation_membership_rows=tuple(item.membership for item in author_members),
        author_observations=author_observations,
        author_observation_relation_rows=tuple(item.relations.relations[0].binding
                                               for item in author_members),
        candidate_capsule=capsule_manifest, support_set=support,
    ), support


def checking_disposition(
    *, evidence: RW0D2CheckingEvidenceV1,
    result_set: PostExecutionValidationResultSetV1 | PostExecutionReviewResultSetV1,
    qualification: RW0EffectHostQualificationV1,
    semantic_attempt_digest: str, attempt_number: int,
    reviewer_separation: PostExecutionReviewerSeparationEvaluationV1 | None,
) -> tuple[ValidationDispositionV1 | IndependentReviewDispositionV1, PostExecutionSupportSetV1]:
    """Construct V14/V15 from actual child, requirement, qualification and C1 proof."""
    evidence.validate()
    role = evidence.role
    if (type(qualification) is not RW0EffectHostQualificationV1
            or type(semantic_attempt_digest) is not str
            or type(attempt_number) is not int or attempt_number != 1
            or (role == "validator" and (type(result_set) is not PostExecutionValidationResultSetV1
                                         or reviewer_separation is not None))
            or (role == "reviewer" and (type(result_set) is not PostExecutionReviewResultSetV1
                                        or type(reviewer_separation) is not PostExecutionReviewerSeparationEvaluationV1))):
        _fail()
    observation = evidence.observation
    requirement = evidence.command.requirement_evidence
    cls = ValidationDispositionV1 if role == "validator" else IndependentReviewDispositionV1
    prefix = "validation" if role == "validator" else "review"
    support_entries = [
        (prefix + "_result_set", 1, 0, result_set.schema_id,
         result_set.result_set_ref, result_set.result_set_digest),
        (prefix + "_qualification", 2, 0, qualification.schema_id,
         qualification.qualification_ref, qualification.qualification_digest),
    ]
    if reviewer_separation is not None:
        support_entries.append(("reviewer_separation", 3, 0,
                                reviewer_separation.schema_id,
                                reviewer_separation.evaluation_ref,
                                reviewer_separation.evaluation_digest))
    support = _support_set(tuple(support_entries))
    identity: dict[str, object] = {
        "schema_id": cls._SCHEMA_ID,
        "profile_ref": cls._PROFILE_PAIR[0],
        "profile_digest": cls._PROFILE_PAIR[1],
        "source_observation_schema_id": observation.schema_id,
        "source_observation_ref": observation.observation_ref,
        "source_observation_digest": observation.observation_digest,
        "delivery_attempt_ref": observation.delivery_attempt_ref,
        "source_kind": observation.source_kind,
        "source_ref": observation.source_ref,
        "source_invocation_ref": observation.source_invocation_ref,
        "observation_kind": observation.observation_kind,
        "source_outcome": observation.outcome,
        "source_reason_code": observation.reason_code,
        "source_evidence_refs": list(observation.evidence_refs),
        "source_observed_at": observation.observed_at,
        "author_role": "validator" if role == "validator" else "independent_reviewer",
        "program_ref": observation.program_ref,
        "program_version_ref": observation.program_version_ref,
        "accepted_intent_revision_ref": observation.accepted_intent_revision_ref,
        "work_item_ref": observation.work_item_ref,
        "work_item_revision_ref": observation.work_item_revision_ref,
        "semantic_attempt_ref": observation.semantic_attempt_ref,
        "semantic_attempt_digest": semantic_attempt_digest,
        "attempt_number": attempt_number,
        "candidate_ref": observation.candidate_ref,
        "capsule_manifest_ref": observation.capsule_manifest_ref,
        "portable_capsule_digest": observation.portable_capsule_digest,
        "command_ref": observation.command_ref,
        "command_digest": observation.command_digest,
        "attempt_fence_ref": observation.attempt_fence_ref,
        "attempt_fence_digest": observation.attempt_fence_digest,
        "effect_intent_ref": observation.effect_intent_ref,
        "effect_fence_ref": observation.effect_fence_ref,
        "effect_fence_digest": observation.effect_fence_digest,
        "effect_class": evidence.command.effect_class,
        prefix + "_tool_profile_ref": result_set.tool_profile_ref,
        prefix + "_tool_profile_digest": result_set.tool_profile_digest,
        prefix + "_tool_qualification_schema_id": qualification.schema_id,
        prefix + "_tool_qualification_ref": qualification.qualification_ref,
        prefix + "_tool_qualification_digest": qualification.qualification_digest,
        prefix + "_requirement_schema_id": requirement.schema_id,
        prefix + "_requirement_ref": requirement.requirement_ref,
        prefix + "_requirement_safe_evidence_digest": requirement.safe_evidence_digest,
        prefix + "_requirement_digest": requirement.requirement_digest,
        prefix + "_requirement_work_spec_ref": requirement.work_spec_ref,
        prefix + "_requirement_work_spec_digest": requirement.work_spec_digest,
        prefix + "_result_set_schema_id": result_set.schema_id,
        prefix + "_result_set_ref": result_set.result_set_ref,
        prefix + "_result_set_digest": result_set.result_set_digest,
        "result": result_set.result,
        "reason": result_set.reason,
        "evaluated_at": result_set.evaluated_at,
        "expires_at": result_set.expires_at,
        "support_set_ref": support.support_set_ref,
        "support_set_digest": support.support_set_digest,
    }
    if role == "validator":
        identity["repairability"] = result_set.repairability
    else:
        identity.update({
            "reviewer_separation_schema_id": reviewer_separation.schema_id,
            "reviewer_separation_ref": reviewer_separation.evaluation_ref,
            "reviewer_separation_digest": reviewer_separation.evaluation_digest,
            "separation_status": reviewer_separation.status,
        })
    try:
        value = _seal_post_value(cls, identity)
        if role == "validator":
            return validate_validation_disposition(
                value, validation_result_set=result_set,
            ), support
        return validate_independent_review_disposition(
            value, review_result_set=result_set,
            reviewer_separation=reviewer_separation,
        ), support
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        _fail()


_POLICY_BRANCHES = (
    ("candidate_acceptance", "governed", "author_candidate"),
    ("candidate_repair", "governed", "author_candidate"),
    ("attempt_selecting_replan", "governed", "author_candidate"),
    ("program_terminal_reject", "halt_only", None),
    ("post_execution_program_block", "halt_only", None),
)
_CEILING_FIELDS = (
    "max_active_invocations", "max_candidate_bytes", "max_changed_files",
    "max_cost_microusd", "max_cpu_seconds", "max_deliveries",
    "max_deployments", "max_local_commits", "max_memory_bytes", "max_merges",
    "max_model_input_tokens", "max_model_output_tokens", "max_pull_requests",
    "max_pushes", "max_wall_seconds",
)


def _policy_entries(*, risk: bool, assertions: bool) -> list[dict[str, object]]:
    schema = (
        "governed-execution.nwp-post-execution-risk-policy-branch-assertion.v1"
        if risk else "governed-execution.nwp-post-execution-standing-policy-branch-assertion.v1"
    )
    return [
        {
            **({"schema_id": schema} if assertions else {}),
            "branch": branch, "applicability": applicability,
            "governed_effect_class": effect,
            "result": "permit",
            "reason": (
                ("risk_lane_permits" if risk else "policy_permits")
                if applicability == "governed" else
                (("halt_only_risk_lane_not_applicable" if assertions else "halt_only_risk_not_applicable")
                 if risk else "halt_only_policy_not_applicable")
            ),
        }
        for branch, applicability, effect in _POLICY_BRANCHES
    ]


def artificial_policy_evidence(
    *, handback: object,
    author_authority: RW0AuthorityVerificationObservationV1,
) -> tuple[tuple[object, ...], tuple[object, ...], tuple[PostExecutionSupportSetV1, PostExecutionSupportSetV1]]:
    """Supply closed artificial policy/risk evidence bound to the real D1 lineage."""
    author = handback.author_command
    if (type(author_authority) is not RW0AuthorityVerificationObservationV1
            or type(author) is not DevelopmentAuthorEffectEstablishmentCommandV1):
        _fail()
    now = _now_at_or_after(author_authority.observed_at)
    attempt = author.attempt_fence
    effect = author.effect_fence
    if not now < attempt.expires_at:
        _fail()
    policy_ref = "standing-policy.d2.artificial"
    policy_digest = hashlib.sha256(policy_ref.encode()).hexdigest()
    source_ref = "standing-policy-source.d2.artificial"
    source_evidence_ref = "standing-policy-evidence.d2.artificial"
    ceiling = attempt.aggregate_ceilings.to_mapping()
    standing_identity = {
        "schema_id": PostExecutionStandingPolicySourceAttestationV1._SCHEMA_ID,
        "attestation_ref": "standing-policy-attestation.d2.artificial",
        "profile_ref": PostExecutionStandingPolicySourceAttestationV1._PROFILE_PAIR[0],
        "profile_digest": PostExecutionStandingPolicySourceAttestationV1._PROFILE_PAIR[1],
        "source_owner_kind": "standing_policy_owner",
        "source_owner_ref": source_ref,
        "source_owner_invocation_ref": "standing-policy-invocation.d2.artificial",
        "source_evidence_ref": source_evidence_ref,
        "source_evidence_digest": hashlib.sha256(source_evidence_ref.encode()).hexdigest(),
        "policy_ref": policy_ref, "policy_digest": policy_digest,
        "parent_grant_ref": attempt.parent_standing_grant_ref,
        "parent_grant_digest": attempt.parent_standing_grant_digest,
        "grant_family_ref": author_authority.grant_family_ref,
        "grant_family_digest": author_authority.grant_family_digest,
        "audience_ref": attempt.program_ref,
        "repository_ref": attempt.repository_ref,
        "path_scope_digest": handback.phase_basis.path_scope_digest,
        "policy_status": "active", "revocation_status": "unrevoked",
        "allowed_branches": [branch for branch, _, _ in _POLICY_BRANCHES],
        "allowed_risk_lanes": ["risk.standard"],
        "allowed_effect_classes": list(attempt.allowed_effect_classes),
        **{name: ceiling[name] for name in _CEILING_FIELDS},
        "branch_assertions": _policy_entries(risk=False, assertions=True),
        "not_before": author_authority.observed_at,
        "expires_at": attempt.expires_at, "evaluated_at": now,
    }
    standing = validate_post_execution_standing_policy_attestation(
        _seal_post_value(PostExecutionStandingPolicySourceAttestationV1, standing_identity)
    )
    backlog_ref = "backlog.d2.artificial"
    mapper_ref = "risk-mapper.d2.artificial"
    mapping_ref = "risk-mapping-evidence.d2.artificial"
    finite = _seal_post_value(FiniteBacklogRiskSourceBindingV1, {
        "schema_id": FiniteBacklogRiskSourceBindingV1._SCHEMA_ID,
        "development_work_item_ref": author.work_item_ref,
        "backlog_ref": backlog_ref,
        "backlog_digest": hashlib.sha256(backlog_ref.encode()).hexdigest(),
        "backlog_lease_ref": "backlog-lease.d2.artificial",
        "backlog_work_item_id": "backlog-item.d2.artificial",
        "risk_lane": "risk.standard",
        "mapping_author_ref": mapper_ref,
        "mapping_author_digest": hashlib.sha256(mapper_ref.encode()).hexdigest(),
        "mapping_evidence_ref": mapping_ref,
        "mapping_evidence_digest": hashlib.sha256(mapping_ref.encode()).hexdigest(),
    })
    profile, binding = finite_backlog_risk_source_projection(
        finite, evaluated_at=now, expires_at=attempt.expires_at,
    )
    post_execution_risk_source_profile(profile)
    post_execution_risk_source_binding(binding, source_profile=profile, source_value=finite)
    risk_source_ref = "risk-policy-evidence.d2.artificial"
    risk_identity = {
        "schema_id": PostExecutionRiskPolicyAttestationV1._SCHEMA_ID,
        "attestation_ref": "risk-policy-attestation.d2.artificial",
        "profile_ref": PostExecutionRiskPolicyAttestationV1._PROFILE_PAIR[0],
        "profile_digest": PostExecutionRiskPolicyAttestationV1._PROFILE_PAIR[1],
        "source_owner_kind": "risk_policy_owner",
        "source_owner_ref": "risk-policy-owner.d2.artificial",
        "source_owner_invocation_ref": "risk-policy-invocation.d2.artificial",
        "source_evidence_ref": risk_source_ref,
        "source_evidence_digest": hashlib.sha256(risk_source_ref.encode()).hexdigest(),
        "risk_policy_ref": "risk-policy.d2.artificial",
        "risk_policy_digest": hashlib.sha256(b"risk-policy.d2.artificial").hexdigest(),
        "policy_status": "active", "revocation_status": "unrevoked",
        "allowed_risk_lanes": ["risk.standard"],
        "required_risk_lane": "risk.standard",
        "source_profile_schema_id": profile.schema_id,
        "source_profile_ref": profile.source_profile_ref,
        "source_profile_digest": profile.source_profile_digest,
        "branch_assertions": _policy_entries(risk=True, assertions=True),
        "not_before": author_authority.observed_at,
        "expires_at": attempt.expires_at, "evaluated_at": now,
    }
    risk = validate_post_execution_risk_policy_attestation(
        _seal_post_value(PostExecutionRiskPolicyAttestationV1, risk_identity)
    )
    standing_support = _support_set((
        ("standing_policy_attestation", 1, 0, standing.schema_id,
         standing.attestation_ref, standing.attestation_digest),
        ("author_authority", 2, 0, author_authority.schema_id,
         author_authority.observation_ref, author_authority.observation_digest),
        ("attempt_fence", 3, 0, attempt.schema_id,
         attempt.attempt_fence_ref, attempt.attempt_fence_digest),
        ("author_effect_fence", 4, 0, effect.schema_id,
         effect.effect_fence_ref, effect.effect_fence_digest),
    ))
    risk_support = _support_set((
        ("finite_risk_source", 1, 0, finite.schema_id, finite.binding_ref, finite.binding_digest),
        ("risk_source_profile", 2, 0, profile.schema_id,
         profile.source_profile_ref, profile.source_profile_digest),
        ("risk_source_binding", 3, 0, binding.schema_id,
         binding.source_binding_ref, binding.source_binding_digest),
        ("risk_policy_attestation", 4, 0, risk.schema_id,
         risk.attestation_ref, risk.attestation_digest),
    ))
    common = {
        "proposal_phase": "post_execution_semantic_review",
        "program_ref": author.program_ref,
        "program_version_ref": author.program_version_ref,
        "accepted_intent_revision_ref": author.accepted_intent_revision_ref,
        "work_item_revision_ref": author.work_item_revision_ref,
        "semantic_attempt_ref": author.semantic_attempt_ref,
        "candidate_ref": author.candidate_ref,
        "author_command_ref": author.command_ref,
        "risk_lane": "risk.standard",
        "not_before": author_authority.observed_at,
        "expires_at": attempt.expires_at, "evaluated_at": now,
    }
    standing_matrix = validate_post_execution_standing_policy_matrix_relation(
        _seal_post_value(PostExecutionStandingPolicyBranchMatrixV1, {
            "schema_id": PostExecutionStandingPolicyBranchMatrixV1._SCHEMA_ID,
            "matrix_ref": "standing-policy-matrix.d2.artificial",
            "profile_ref": PostExecutionStandingPolicyBranchMatrixV1._PROFILE_PAIR[0],
            "profile_digest": PostExecutionStandingPolicyBranchMatrixV1._PROFILE_PAIR[1],
            **common, "work_item_ref": author.work_item_ref,
            "effect_intent_ref": author.effect_intent_ref,
            "matrix_author_ref": standing.source_owner_ref,
            "matrix_author_invocation_ref": standing.source_owner_invocation_ref,
            "policy_source_schema_id": standing.schema_id,
            "policy_source_ref": standing.attestation_ref,
            "policy_source_digest": standing.attestation_digest,
            "policy_status": standing.policy_status,
            "policy_revocation_status": standing.revocation_status,
            "parent_grant_ref": standing.parent_grant_ref,
            "parent_grant_digest": standing.parent_grant_digest,
            "grant_family_ref": standing.grant_family_ref,
            "grant_family_digest": standing.grant_family_digest,
            "audience_ref": standing.audience_ref,
            "repository_ref": standing.repository_ref,
            "path_scope_digest": standing.path_scope_digest,
            "source_effect_fence_ref": effect.effect_fence_ref,
            "source_effect_fence_digest": effect.effect_fence_digest,
            "source_effect_class": effect.effect_class,
            "allowed_branches": list(standing.allowed_branches),
            "allowed_risk_lanes": list(standing.allowed_risk_lanes),
            "allowed_effect_classes": list(standing.allowed_effect_classes),
            "policy_ceilings": {name: getattr(standing, name) for name in _CEILING_FIELDS},
            "entries": _policy_entries(risk=False, assertions=False),
            "support_set_ref": standing_support.support_set_ref,
            "support_set_digest": standing_support.support_set_digest,
        }), policy_source=standing,
    )
    risk_matrix = validate_post_execution_risk_lane_matrix_relation(
        _seal_post_value(PostExecutionRiskLaneBranchMatrixV1, {
            "schema_id": PostExecutionRiskLaneBranchMatrixV1._SCHEMA_ID,
            "matrix_ref": "risk-lane-matrix.d2.artificial",
            "profile_ref": PostExecutionRiskLaneBranchMatrixV1._PROFILE_PAIR[0],
            "profile_digest": PostExecutionRiskLaneBranchMatrixV1._PROFILE_PAIR[1],
            **common, "development_work_item_ref": author.work_item_ref,
            "matrix_author_ref": risk.source_owner_ref,
            "matrix_author_invocation_ref": risk.source_owner_invocation_ref,
            "source_profile_schema_id": profile.schema_id,
            "source_profile_ref": profile.source_profile_ref,
            "source_profile_digest": profile.source_profile_digest,
            "source_binding_schema_id": binding.schema_id,
            "source_binding_ref": binding.source_binding_ref,
            "source_binding_digest": binding.source_binding_digest,
            "risk_policy_schema_id": risk.schema_id,
            "risk_policy_ref": risk.attestation_ref,
            "risk_policy_digest": risk.attestation_digest,
            "policy_status": risk.policy_status,
            "policy_revocation_status": risk.revocation_status,
            "allowed_risk_lanes": list(risk.allowed_risk_lanes),
            "required_risk_lane": risk.required_risk_lane,
            "entries": _policy_entries(risk=True, assertions=False),
            "support_set_ref": risk_support.support_set_ref,
            "support_set_digest": risk_support.support_set_digest,
        }), risk_policy=risk, source_profile=profile,
        source_binding=binding,
    )
    return (standing, risk, finite, profile, binding), (standing_matrix, risk_matrix), (
        standing_support, risk_support,
    )


@dataclass(frozen=True, slots=True, repr=False)
class RW0D2CheckingEvidenceV1:
    role: str
    command: DevelopmentBoundEffectEstablishmentCommandV1 = field(repr=False)
    author_command: DevelopmentAuthorEffectEstablishmentCommandV1 = field(repr=False)
    process: D1ProcessOutcome = field(repr=False)
    observation: WorkerObservationV1 = field(repr=False)
    source_frame: bytes = field(repr=False)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if (type(self) is not RW0D2CheckingEvidenceV1
                or type(self.role) is not str or self.role not in _ROLE_EFFECT
                or type(self.author_command) is not DevelopmentAuthorEffectEstablishmentCommandV1
                or type(self.process) is not D1ProcessOutcome
                or type(self.observation) is not WorkerObservationV1
                or type(self.source_frame) is not bytes):
            _fail()
        try:
            command = _require_exact_development_bound_effect_command(self.command)
            process = self.process
            process.validate()
            if not process.clean_success or process.stdout != self.source_frame:
                _fail()
            record = decode_checking_response(self.role, self.source_frame)
            observation = WorkerObservationV1.from_mapping(self.observation.to_mapping())
            if (observation.to_mapping() != self.observation.to_mapping()
                    or command.effect_class != _ROLE_EFFECT[self.role]
                    or record["command_digest"] != command.command_digest
                    or record["effect_fence_ref"] != command.effect_fence_ref
                    or record["effect_fence_digest"] != command.effect_fence.effect_fence_digest
                    or record["delivery_attempt_ref"] != command.delivery_attempt_ref
                    or record["capsule_manifest_ref"] != command.capsule_manifest_ref
                    or record["portable_capsule_digest"] != command.portable_capsule_digest
                    or record["source_ref"] != _ROLE_SOURCE[self.role]
                    or record["evidence_ref"] != _ROLE_EVIDENCE[self.role]
                    or tuple(record["file_digests"]) != tuple(
                        entry.after_blob_sha256 for entry in command.capsule_manifest.entries
                    )
                    or observation.source_invocation_ref != record["invocation_ref"]
                    or observation.source_ref != record["source_ref"]
                    or observation.evidence_refs != (record["evidence_ref"],)
                    or observation.observation_kind != _ROLE_KIND[self.role]
                    or observation.outcome != record["outcome"]
                    or observation.reason_code != record["reason_code"]
                    or observation.observed_at != record["observed_at"]):
                _fail()
            author = self.author_command
            if (author.command_ref != command.originating_command_ref
                    or author.worker_command.command_digest != command.originating_command_digest
                    or author.effect_fence_ref != command.author_effect_fence_ref):
                _fail()
            validate_observation_relation(
                observation=observation, delivery=command.delivery_envelope,
                author_command=author.worker_command,
                attempt_fence=author.attempt_fence,
                author_effect_fence=author.effect_fence,
                effect_fence=command.effect_fence,
                capsule_manifest=command.capsule_manifest,
                before_blobs=dict(command.before_blob_entries),
                after_blobs=dict(command.after_blob_entries),
            )
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception:
            _fail()

    def __reduce__(self) -> object:
        raise TypeError("serialization disabled")


def normalize_checking_evidence(
    *, role: str, process: D1ProcessOutcome,
    command: DevelopmentBoundEffectEstablishmentCommandV1,
    author_command: DevelopmentAuthorEffectEstablishmentCommandV1,
    adapter_exit: WorkerObservationV1,
) -> RW0D2CheckingEvidenceV1:
    if (type(role) is not str or role not in _ROLE_EFFECT
            or type(process) is not D1ProcessOutcome
            or type(author_command) is not DevelopmentAuthorEffectEstablishmentCommandV1
            or type(adapter_exit) is not WorkerObservationV1):
        _fail()
    checked = _require_exact_development_bound_effect_command(command)
    process.validate()
    WorkerObservationV1.from_mapping(adapter_exit.to_mapping())
    if not process.clean_success:
        _fail()
    record = _decode_child_checking_record(role, process.stdout, checked, adapter_exit)
    observation = WorkerObservationV1.create(
        observation_ref=("observation.d2.validation-completed" if role == "validator"
                         else "observation.d2.review-completed"),
        source_kind=("validator" if role == "validator" else "independent_reviewer"),
        source_ref=record["source_ref"],
        source_invocation_ref=record["invocation_ref"],
        observation_kind=_ROLE_KIND[role], outcome=record["outcome"],
        reason_code=record["reason_code"],
        evidence_refs=[record["evidence_ref"]],
        observed_at=record["observed_at"],
        delivery=checked.delivery_envelope,
        author_command=author_command.worker_command,
        attempt_fence=author_command.attempt_fence,
        author_effect_fence=author_command.effect_fence,
        effect_fence=checked.effect_fence,
        capsule_manifest=checked.capsule_manifest,
        before_blobs=dict(checked.before_blob_entries),
        after_blobs=dict(checked.after_blob_entries),
    )
    return RW0D2CheckingEvidenceV1(
        role, checked, author_command, process, observation, process.stdout,
    )
