"""Private canonical post-execution model content and transient normalization."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from typing import cast

from ._cognitive_proposal_semantic_values import (
    ModelProposalEvidenceBindingV1, ModelProposalEvidenceSetV1,
    ModelSourceInvocationV1, PreExecutionModelProposalV1,
    PrivateProposalArtifactBindingV1,
    _EVIDENCE_SET_DOMAIN, _POST_EXECUTION_ROLES,
)
from ._cognitive_proposal_value_support import (
    _canonical_bytes, _domain_separated_digest, _require_reason_code,
    _require_safe_ref, _require_sha256, _require_utc_second,
)
from ._post_execution_evidence_values import (
    PostExecutionEvidenceSupplyV2, PostExecutionModelInputBindingV2,
    PostExecutionModelInputSafeProjectionV2, PostExecutionPrivateInputManifestV2,
    PostExecutionSemanticReviewInputContextV1,
    validate_post_execution_model_input_binding,
)
from ._rw0_d2a_evidence import _seal_post_value
from ._rw0_d2b_model_frames import decode_model_response, model_input_digest
from ._rw0_d1_process_supervisor import D1ProcessOutcome

__all__: tuple[str, ...] = ()

_PHASE = "post_execution_semantic_review"
_CONTEXT_SCHEMA = "governed-execution.nwp-post-execution-semantic-review-context.v1"
_ARTIFACT_SCHEMA = "governed-execution.nwp-post-execution-semantic-review-artifact.v1"
_PROJECTION_SCHEMA = "governed-execution.nwp-post-execution-semantic-review-safe-projection.v1"
_RECOMMENDATIONS = (
    "accept_candidate", "repair_candidate", "replan", "terminal_reject", "block",
)
_MODEL_CONTRACT_REF = "model-contract.d2.fake-review"
_MODEL_CONFIGURATION_REF = "model-configuration.d2.fake-review"
_MODEL_CONTRACT_DIGEST = hashlib.sha256(_MODEL_CONTRACT_REF.encode()).hexdigest()
_MODEL_CONFIGURATION_DIGEST = hashlib.sha256(_MODEL_CONFIGURATION_REF.encode()).hexdigest()


def _fail() -> None:
    raise ValueError("invalid_d2_model_proposal") from None


def _digest(schema: str, mapping: dict[str, object]) -> str:
    return _domain_separated_digest(schema + ".identity", mapping)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True, slots=True, repr=False)
class RW0D2ReviewFindingV1:
    finding_ref: str
    source_role: str
    source_value_ref: str
    source_value_digest: str
    reason_code: str

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if type(self) is not RW0D2ReviewFindingV1:
            _fail()
        try:
            _require_safe_ref(self.finding_ref)
            if type(self.source_role) is not str or self.source_role not in _POST_EXECUTION_ROLES:
                _fail()
            _require_safe_ref(self.source_value_ref)
            _require_sha256(self.source_value_digest)
            _require_reason_code(self.reason_code)
        except ValueError:
            _fail()

    def to_mapping(self) -> dict[str, object]:
        self.validate()
        return {name: getattr(self, name) for name in (
            "finding_ref", "source_role", "source_value_ref",
            "source_value_digest", "reason_code",
        )}

    def __reduce__(self) -> object:
        raise TypeError("serialization disabled")


@dataclass(frozen=True, slots=True, repr=False)
class PostExecutionSemanticReviewArtifactV1:
    schema_id: str
    artifact_ref: str
    proposal_ref: str
    proposal_phase: str
    input_context_ref: str
    capsule_manifest_ref: str
    validation_disposition_ref: str
    review_disposition_ref: str
    findings: tuple[RW0D2ReviewFindingV1, ...] = field(repr=False)
    recommendation: str = ""
    reason_code: str = ""
    artifact_digest: str = ""

    def __post_init__(self) -> None:
        self.validate()

    def _mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id, "artifact_ref": self.artifact_ref,
            "proposal_ref": self.proposal_ref, "proposal_phase": self.proposal_phase,
            "input_context_ref": self.input_context_ref,
            "capsule_manifest_ref": self.capsule_manifest_ref,
            "validation_disposition_ref": self.validation_disposition_ref,
            "review_disposition_ref": self.review_disposition_ref,
            "findings": tuple(item.to_mapping() for item in self.findings),
            "recommendation": self.recommendation, "reason_code": self.reason_code,
            "artifact_digest": self.artifact_digest,
        }

    def to_mapping(self) -> dict[str, object]:
        self.validate()
        return self._mapping()

    def validate(self) -> None:
        if (type(self) is not PostExecutionSemanticReviewArtifactV1
                or self.schema_id != _ARTIFACT_SCHEMA
                or self.proposal_phase != _PHASE
                or type(self.findings) is not tuple or len(self.findings) > 8
                or any(type(item) is not RW0D2ReviewFindingV1 for item in self.findings)
                or self.recommendation not in _RECOMMENDATIONS):
            _fail()
        try:
            for value in (self.artifact_ref, self.proposal_ref, self.input_context_ref,
                          self.capsule_manifest_ref, self.validation_disposition_ref,
                          self.review_disposition_ref):
                _require_safe_ref(value)
            _require_reason_code(self.reason_code)
            _require_sha256(self.artifact_digest)
            for item in self.findings:
                item.validate()
            ranks = tuple(_POST_EXECUTION_ROLES.index(item.source_role)
                          for item in self.findings)
            if (ranks != tuple(sorted(ranks))
                    or len({item.finding_ref for item in self.findings}) != len(self.findings)):
                _fail()
            mapping = self._mapping()
            if self.artifact_digest != _digest(_ARTIFACT_SCHEMA, {
                name: value for name, value in mapping.items() if name != "artifact_digest"
            }) or len(_canonical_bytes(mapping)) > 65_536:
                _fail()
        except ValueError:
            _fail()

    def __reduce__(self) -> object:
        raise TypeError("serialization disabled")


@dataclass(frozen=True, slots=True, repr=False)
class PostExecutionSemanticReviewSafeProjectionV1:
    schema_id: str
    proposal_ref: str
    proposal_phase: str
    artifact_schema_id: str
    artifact_ref: str
    artifact_digest: str
    input_context_schema_id: str
    input_context_ref: str
    input_context_digest: str
    recommendation: str
    reason_code: str
    safe_projection_digest: str

    def __post_init__(self) -> None:
        self.validate()

    def to_mapping(self) -> dict[str, object]:
        self.validate()
        return {name: getattr(self, name) for name in (
            "schema_id", "proposal_ref", "proposal_phase", "artifact_schema_id",
            "artifact_ref", "artifact_digest", "input_context_schema_id",
            "input_context_ref", "input_context_digest", "recommendation",
            "reason_code", "safe_projection_digest",
        )}

    def validate(self) -> None:
        if (type(self) is not PostExecutionSemanticReviewSafeProjectionV1
                or self.schema_id != _PROJECTION_SCHEMA
                or self.proposal_phase != _PHASE
                or self.artifact_schema_id != _ARTIFACT_SCHEMA
                or self.input_context_schema_id != _CONTEXT_SCHEMA
                or self.recommendation not in _RECOMMENDATIONS):
            _fail()
        try:
            for value in (self.proposal_ref, self.artifact_ref, self.input_context_ref):
                _require_safe_ref(value)
            for value in (self.artifact_digest, self.input_context_digest,
                          self.safe_projection_digest):
                _require_sha256(value)
            _require_reason_code(self.reason_code)
            unsigned = {name: getattr(self, name) for name in (
                "schema_id", "proposal_ref", "proposal_phase", "artifact_schema_id",
                "artifact_ref", "artifact_digest", "input_context_schema_id",
                "input_context_ref", "input_context_digest", "recommendation", "reason_code",
            )}
            if self.safe_projection_digest != _digest(_PROJECTION_SCHEMA, unsigned):
                _fail()
        except ValueError:
            _fail()

    def __reduce__(self) -> object:
        raise TypeError("serialization disabled")


def _common(cls: type, identity: dict[str, object]):
    field = cls._DIGEST_FIELD
    digest = _domain_separated_digest(cls._DOMAIN, identity)
    return cls(**{**identity, field: digest})


def _check_child_content_against_supply(
    response: dict[str, object], supply: PostExecutionEvidenceSupplyV2,
) -> None:
    """Refuse a well-formed but source-inconsistent child choice or finding."""
    roles = supply.to_mapping()["role_supplies"]
    values = tuple(item["typed_canonical_value"] for item in roles)
    validation, review = values[2], values[3]
    standing, risk, authority, stop, ceiling = values[4:]
    if stop["global_stop_state"] != "clear":
        expected = ("block", "global_stop_active", 7)
    elif authority["status"] != "verified" or authority["revocation_status"] != "unrevoked":
        expected = ("block", "authority_not_current", 6)
    elif ceiling["result"] != "compliant":
        expected = ("block", "effect_ceiling_not_compliant", 8)
    elif any(item["result"] != "permit" for item in standing["entries"]):
        expected = ("block", "standing_policy_not_permitted", 4)
    elif any(item["result"] != "permit" for item in risk["entries"]):
        expected = ("block", "risk_lane_not_permitted", 5)
    elif review["separation_status"] != "separate":
        expected = ("block", "reviewer_separation_not_proved", 3)
    elif validation["result"] == "terminal_failure" or review["result"] == "terminal_reject":
        expected = ("terminal_reject", "terminal_source_result",
                    2 if validation["result"] == "terminal_failure" else 3)
    elif validation["result"] == "replan_required" or review["result"] == "replan_required":
        expected = ("replan", "source_requires_replan",
                    2 if validation["result"] == "replan_required" else 3)
    elif validation["result"] == "repairable_failure" or review["result"] == "repair_required":
        expected = ("repair_candidate", "source_requires_repair",
                    2 if validation["result"] == "repairable_failure" else 3)
    elif validation["result"] == "passed" and review["result"] == "passed":
        expected = ("accept_candidate", "source_checks_passed", None)
    else:
        expected = ("block", "source_result_unknown",
                    2 if validation["result"] != "passed" else 3)
    recommendation, reason, index = expected
    if response["recommendation"] != recommendation or response["reason_code"] != reason:
        _fail()
    expected_findings = () if index is None else ({
        "finding_ref": "finding.d2." + roles[index]["role"].replace("_", "-"),
        "source_role": roles[index]["role"],
        "source_value_ref": roles[index]["typed_value_ref"],
        "source_value_digest": roles[index]["typed_value_digest"],
        "reason_code": reason,
    },)
    if tuple(response["findings"]) != expected_findings:
        _fail()


def normalize_d2_model_response(
    *, response: dict[str, object], process: D1ProcessOutcome,
    context: PostExecutionSemanticReviewInputContextV1,
    input_safe: PostExecutionModelInputSafeProjectionV2,
    manifest: PostExecutionPrivateInputManifestV2,
    supply: PostExecutionEvidenceSupplyV2,
    started_at: str,
) -> tuple[
    ModelSourceInvocationV1, PostExecutionSemanticReviewArtifactV1,
    PrivateProposalArtifactBindingV1, PostExecutionSemanticReviewSafeProjectionV1,
    tuple[ModelProposalEvidenceBindingV1, ...], ModelProposalEvidenceSetV1,
    PreExecutionModelProposalV1, PostExecutionModelInputBindingV2,
]:
    """Bind child-authored content to the exact input; no decision-time branch."""
    if (type(response) is not dict or type(process) is not D1ProcessOutcome
            or not process.clean_success or not process.cleanup_complete
            or type(context) is not PostExecutionSemanticReviewInputContextV1
            or type(input_safe) is not PostExecutionModelInputSafeProjectionV2
            or type(manifest) is not PostExecutionPrivateInputManifestV2
            or type(supply) is not PostExecutionEvidenceSupplyV2):
        _fail()
    process.validate()
    try:
        if decode_model_response(process.stdout) != response:
            _fail()
    except ValueError:
        _fail()
    for item in (context, input_safe, manifest, supply):
        item._validate_value()
    _require_utc_second(started_at)
    if (response["invocation_ref"] != "source-invocation.d2.fake-review"
            or response["input_digest"] != model_input_digest(
                response["invocation_ref"], context.to_mapping(), supply.to_mapping()
            )
            or response["input_context_ref"] != context.input_context_ref
            or response["input_context_digest"] != context.input_context_digest
            or response["supply_ref"] != supply.supply_ref
            or response["supply_digest"] != supply.supply_digest
            or response["recommendation"] not in _RECOMMENDATIONS):
        _fail()
    _check_child_content_against_supply(response, supply)
    completed_at = response["completed_at"]
    after_process = _now()
    if not started_at <= completed_at <= after_process:
        _fail()
    entries = tuple(context.role_entries)
    findings = tuple(RW0D2ReviewFindingV1(**item) for item in response["findings"])
    if any(
        item.source_value_ref != entries[_POST_EXECUTION_ROLES.index(item.source_role)].typed_value_ref
        or item.source_value_digest != entries[_POST_EXECUTION_ROLES.index(item.source_role)].typed_value_digest
        for item in findings
    ):
        _fail()
    proposal_ref = context.preassigned_proposal_ref
    artifact_ref = "artifact.d2.post-review"
    artifact_identity = {
        "schema_id": _ARTIFACT_SCHEMA, "artifact_ref": artifact_ref,
        "proposal_ref": proposal_ref, "proposal_phase": _PHASE,
        "input_context_ref": context.input_context_ref,
        "capsule_manifest_ref": entries[0].typed_value_ref,
        "validation_disposition_ref": entries[2].typed_value_ref,
        "review_disposition_ref": entries[3].typed_value_ref,
        "findings": tuple(item.to_mapping() for item in findings),
        "recommendation": response["recommendation"],
        "reason_code": response["reason_code"],
    }
    artifact = PostExecutionSemanticReviewArtifactV1(
        **{**artifact_identity, "findings": findings,
           "artifact_digest": _digest(_ARTIFACT_SCHEMA, artifact_identity)}
    )
    projection_identity = {
        "schema_id": _PROJECTION_SCHEMA, "proposal_ref": proposal_ref,
        "proposal_phase": _PHASE, "artifact_schema_id": _ARTIFACT_SCHEMA,
        "artifact_ref": artifact.artifact_ref,
        "artifact_digest": artifact.artifact_digest,
        "input_context_schema_id": context.schema_id,
        "input_context_ref": context.input_context_ref,
        "input_context_digest": context.input_context_digest,
        "recommendation": artifact.recommendation, "reason_code": artifact.reason_code,
    }
    projection = PostExecutionSemanticReviewSafeProjectionV1(
        **{**projection_identity,
           "safe_projection_digest": _digest(_PROJECTION_SCHEMA, projection_identity)}
    )
    validated_at = _now()
    if validated_at < completed_at:
        _fail()
    source = cast(ModelSourceInvocationV1, _common(ModelSourceInvocationV1, {
        "schema_id": ModelSourceInvocationV1._SCHEMA,
        "source_invocation_ref": response["invocation_ref"],
        "proposal_phase": _PHASE,
        "model_contract_ref": _MODEL_CONTRACT_REF,
        "model_contract_digest": _MODEL_CONTRACT_DIGEST,
        "model_configuration_ref": _MODEL_CONFIGURATION_REF,
        "model_configuration_digest": _MODEL_CONFIGURATION_DIGEST,
        "context_schema_id": context.schema_id,
        "context_ref": context.input_context_ref,
        "context_digest": context.input_context_digest,
        "artifact_schema_id": artifact.schema_id,
        "artifact_ref": artifact.artifact_ref,
        "artifact_digest": artifact.artifact_digest,
        "invocation_status": "normalized_typed_proposal_supplied",
        "source_invocation_started_at": started_at,
        "source_invocation_completed_at": completed_at,
    }))
    binding = cast(PrivateProposalArtifactBindingV1, _common(
        PrivateProposalArtifactBindingV1, {
            "schema_id": PrivateProposalArtifactBindingV1._SCHEMA,
            "artifact_ref": artifact.artifact_ref, "proposal_phase": _PHASE,
            "artifact_schema_id": artifact.schema_id,
            "artifact_digest": artifact.artifact_digest,
            "artifact_canonical_byte_length": len(_canonical_bytes(artifact.to_mapping())),
            "safe_projection_schema_id": projection.schema_id,
            "safe_projection_digest": projection.safe_projection_digest,
            "privacy_classification": "private_normalized_model_proposal",
            "artifact_validated_at": validated_at,
        },
    ))
    bound_at = _now()
    if bound_at < validated_at:
        _fail()
    evidence_set_ref = "evidence-set.d2.post-review"
    bindings = tuple(cast(ModelProposalEvidenceBindingV1, _common(
        ModelProposalEvidenceBindingV1, {
            "schema_id": ModelProposalEvidenceBindingV1._SCHEMA,
            "proposal_ref": proposal_ref, "proposal_phase": _PHASE,
            "evidence_set_ref": evidence_set_ref,
            "evidence_role": entry.role, "role_rank": entry.role_rank,
            "ordinal": 0, "evidence_ref": entry.typed_value_ref,
            "evidence_digest": entry.typed_value_digest,
            "required_for_selection": 1, "evidence_bound_at": bound_at,
        },
    )) for entry in entries)
    evidence_identity = {
        "evidence_set_ref": evidence_set_ref, "proposal_ref": proposal_ref,
        "proposal_phase": _PHASE,
        "entries": tuple({
            "evidence_role": item.evidence_role, "role_rank": item.role_rank,
            "ordinal": item.ordinal, "evidence_ref": item.evidence_ref,
            "evidence_digest": item.evidence_digest,
            "evidence_binding_digest": item.evidence_binding_digest,
        } for item in bindings),
    }
    evidence_set = ModelProposalEvidenceSetV1(
        evidence_set_ref, proposal_ref, _PHASE, bindings,
        _domain_separated_digest(_EVIDENCE_SET_DOMAIN, evidence_identity),
    )
    created_at = _now()
    if created_at < bound_at:
        _fail()
    proposal = cast(PreExecutionModelProposalV1, _common(PreExecutionModelProposalV1, {
        "schema_id": PreExecutionModelProposalV1._SCHEMA,
        "proposal_ref": proposal_ref, "proposal_phase": _PHASE,
        "source_invocation_ref": source.source_invocation_ref,
        "source_invocation_digest": source.source_invocation_digest,
        "model_contract_ref": source.model_contract_ref,
        "model_contract_digest": source.model_contract_digest,
        "model_configuration_ref": source.model_configuration_ref,
        "model_configuration_digest": source.model_configuration_digest,
        "context_schema_id": context.schema_id,
        "context_ref": context.input_context_ref,
        "context_digest": context.input_context_digest,
        "artifact_schema_id": artifact.schema_id,
        "artifact_ref": artifact.artifact_ref,
        "artifact_digest": artifact.artifact_digest,
        "safe_projection_schema_id": projection.schema_id,
        "safe_projection_digest": projection.safe_projection_digest,
        "recommendation": artifact.recommendation,
        "reason_code": artifact.reason_code,
        "evidence_set_ref": evidence_set.evidence_set_ref,
        "evidence_set_digest": evidence_set.evidence_set_digest,
        "proposal_created_at": created_at,
    }))
    model_binding_cls = PostExecutionModelInputBindingV2
    model_binding = _seal_post_value(model_binding_cls, {
        "schema_id": model_binding_cls._SCHEMA_ID,
        "profile_ref": model_binding_cls._PROFILE_PAIR[0],
        "profile_digest": model_binding_cls._PROFILE_PAIR[1],
        "input_context_schema_id": context.schema_id,
        "input_context_ref": context.input_context_ref,
        "input_context_digest": context.input_context_digest,
        "lineage_context_schema_id": context.lineage_context_schema_id,
        "lineage_context_ref": context.lineage_context_ref,
        "lineage_context_digest": context.lineage_context_digest,
        "model_input_safe_projection_schema_id": input_safe.schema_id,
        "model_input_safe_projection_ref": input_safe.projection_ref,
        "model_input_safe_projection_digest": input_safe.projection_digest,
        "private_input_manifest_schema_id": manifest.schema_id,
        "private_input_manifest_ref": manifest.manifest_ref,
        "private_input_manifest_digest": manifest.manifest_digest,
        "source_invocation_ref": source.source_invocation_ref,
        "source_invocation_digest": source.source_invocation_digest,
        "model_contract_ref": source.model_contract_ref,
        "model_contract_digest": source.model_contract_digest,
        "model_configuration_ref": source.model_configuration_ref,
        "model_configuration_digest": source.model_configuration_digest,
        "artifact_schema_id": artifact.schema_id,
        "artifact_ref": artifact.artifact_ref,
        "artifact_digest": artifact.artifact_digest,
        "artifact_binding_digest": binding.artifact_binding_digest,
        "artifact_safe_projection_schema_id": projection.schema_id,
        "artifact_safe_projection_digest": projection.safe_projection_digest,
        "proposal_ref": proposal.proposal_ref,
        "proposal_digest": proposal.proposal_digest,
        "evidence_set_ref": evidence_set.evidence_set_ref,
        "evidence_set_digest": evidence_set.evidence_set_digest,
        "source_invocation_started_at": started_at,
        "source_invocation_completed_at": completed_at,
        "artifact_validated_at": validated_at,
        "result": "bound", "reason": "exact_model_input_binding",
    })
    validate_post_execution_model_input_binding(
        model_binding, input_context=context, safe_projection=input_safe,
        private_manifest=manifest,
    )
    return source, artifact, binding, projection, bindings, evidence_set, proposal, model_binding
