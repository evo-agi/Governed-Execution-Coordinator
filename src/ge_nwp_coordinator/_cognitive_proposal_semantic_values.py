"""Pure typed Section 41 pre-execution cognitive proposal values.

The values retain only normalized private planning inputs and privacy-safe
projections.  They perform no I/O and grant no execution or retrieval authority.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, fields, make_dataclass
import re
import typing
import unicodedata

from ._cognitive_proposal_value_support import (
    SQLITE_INTEGER_MAX,
    _CognitiveProposalContractViolation,
    _EFFECT_CLASS_ORDER,
    _canonical_bytes,
    _constant_repr,
    _disable_pickle,
    _domain_separated_digest,
    _exact_equal,
    _require_canonical_string,
    _require_canonical_effect_class_json,
    _require_enum,
    _require_nonnegative_integer,
    _require_optional_safe_ref,
    _require_optional_sha256,
    _require_positive_integer,
    _require_reason_code,
    _require_safe_ref,
    _require_sha1,
    _require_sha256,
    _require_sqlite_integer,
    _require_utc_second,
    _select_exact_type,
    _violate,
    _without_field,
)
from ._worker_execution_semantic_values import (
    AttemptFenceV1,
    CeilingsV1,
    EffectFenceV1,
    _AUTHORIZED_PATHS as _WORKER_AUTHORIZED_PATHS,
)


__all__ = ()


_SCHEMAS = {
    "model_configuration": "governed-execution.nwp-model-configuration-safe.v1",
    "authority_observation": "governed-execution.nwp-authority-observation-attestation-safe.v1",
    "planning_context": "governed-execution.nwp-pre-execution-planning-context.v1",
    "source_invocation": "governed-execution.nwp-model-source-invocation.v1",
    "artifact_binding": "governed-execution.nwp-private-proposal-artifact-binding.v1",
    "artifact": "governed-execution.nwp-pre-execution-plan-artifact.v1",
    "projection": "governed-execution.nwp-pre-execution-plan-safe-projection.v1",
    "evidence_binding": "governed-execution.nwp-model-proposal-evidence-binding.v1",
    "proposal": "governed-execution.nwp-model-proposal-envelope.v1",
}
_DOMAINS = {name: schema + ".identity" for name, schema in _SCHEMAS.items()}
_EVIDENCE_SET_DOMAIN = "governed-execution.nwp-model-proposal-evidence-set.v1.identity"

_EFFECT_CLASSES = _EFFECT_CLASS_ORDER
_EVIDENCE_ROLES = (
    "standing_policy",
    "risk_lane",
    "repository_binding",
    "base_binding",
    "authorized_path_scope",
    "cost_ceiling",
    "token_ceiling",
    "time_ceiling",
    "delivery_ceiling",
    "effect_ceiling",
    "authority_selection_observation",
    "global_stop",
    "validation_requirement",
    "review_requirement",
)
_READINESS_ROLE = "qualified_remote_host_readiness"
_PRE_EXECUTION_RECOMMENDATIONS = (
    "select_for_dispatch_gates",
    "defer",
    "block",
    "replan",
    "terminal_reject",
)
_POST_EXECUTION_RECOMMENDATIONS = (
    "accept_candidate", "repair_candidate", "replan", "terminal_reject", "block",
)
_POST_EXECUTION_ROLES = (
    "candidate_capsule", "worker_result", "validation_result",
    "independent_review", "standing_policy", "risk_lane",
    "authority_currentness_attestation", "global_stop", "effect_ceiling",
)
_POST_EXECUTION_SCHEMAS = (
    "governed-execution.nwp-post-execution-semantic-review-context.v1",
    "governed-execution.nwp-post-execution-semantic-review-artifact.v1",
    "governed-execution.nwp-post-execution-semantic-review-safe-projection.v1",
)
_PHASE_SCHEMAS = {
    "pre_execution_plan": (
        _SCHEMAS["planning_context"], _SCHEMAS["artifact"], _SCHEMAS["projection"],
    ),
    "post_execution_semantic_review": _POST_EXECUTION_SCHEMAS,
}
_CEILING_FIELDS = (
    "max_active_invocations",
    "max_candidate_bytes",
    "max_changed_files",
    "max_cost_microusd",
    "max_cpu_seconds",
    "max_deliveries",
    "max_deployments",
    "max_local_commits",
    "max_memory_bytes",
    "max_merges",
    "max_model_input_tokens",
    "max_model_output_tokens",
    "max_pull_requests",
    "max_pushes",
    "max_wall_seconds",
)


def _to_plain(value: object) -> object:
    kind = type(value)
    trusted_kind = _semantic_type_by_identity(kind)
    if trusted_kind is not None:
        return value.to_mapping()
    if kind is tuple:
        return tuple(
            _to_plain(member) for member in typing.cast(tuple[object, ...], value)
        )
    if kind is str or kind is int or kind is bool or kind is type(None):
        return value
    _violate("invalid_field_type")


_SEMANTIC_CLASSES: tuple[type[object], ...] = ()


def _semantic_type_by_identity(candidate_type: object) -> type[object] | None:
    return _select_exact_type(candidate_type, _SEMANTIC_CLASSES)


def _reject_concrete_subclass(cls: type[object], **kwargs: object) -> typing.NoReturn:
    raise TypeError("subclassing disabled")


class _SemanticValue:
    __slots__ = ()
    __hash__ = None
    _FIELD_ORDER: tuple[str, ...] = ()
    _SCHEMA: str | None = None
    _DOMAIN: str | None = None
    _DIGEST_FIELD: str | None = None

    def __post_init__(self) -> None:
        _validate_semantic_value(self)

    def to_mapping(self) -> dict[str, object]:
        return {
            name: _to_plain(object.__getattribute__(self, name))
            for name in self._FIELD_ORDER
        }

    identity_mapping = to_mapping

    def computed_digest(self) -> str:
        if self._DOMAIN is None or self._DIGEST_FIELD is None:
            _violate("invalid_field_value")
        mapping = self.to_mapping()
        return _domain_separated_digest(
            typing.cast(str, self._DOMAIN),
            _without_field(mapping, typing.cast(str, self._DIGEST_FIELD)),
        )

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> None:
        if cls.__module__ != __name__:
            raise TypeError("subclassing disabled")


def _make_value_class(
    name: str,
    field_order: tuple[str, ...],
    *,
    schema: str | None = None,
    domain: str | None = None,
    digest_field: str | None = None,
) -> type[_SemanticValue]:
    global _SEMANTIC_CLASSES

    namespace = {
        "__module__": __name__,
        "_FIELD_ORDER": field_order,
        "_SCHEMA": schema,
        "_DOMAIN": domain,
        "_DIGEST_FIELD": digest_field,
        "__init_subclass__": _reject_concrete_subclass,
    }
    result = typing.cast(
        type[_SemanticValue],
        make_dataclass(
            name,
            [(field_name, object) for field_name in field_order],
            bases=(_SemanticValue,),
            namespace=namespace,
            frozen=True,
            slots=True,
            repr=False,
        ),
    )
    _SEMANTIC_CLASSES = (*_SEMANTIC_CLASSES, result)
    return result


_MODEL_CONFIGURATION_FIELDS = (
    "schema_id",
    "model_configuration_ref",
    "model_contract_ref",
    "model_contract_digest",
    "implementation_family",
    "capability_profile_ref",
    "capability_profile_digest",
    "input_policy_ref",
    "input_policy_digest",
    "output_policy_ref",
    "output_policy_digest",
    "model_configuration_digest",
)
_AUTHORITY_OBSERVATION_FIELDS = (
    "schema_id",
    "authority_observation_ref",
    "authoritative_subject_kind",
    "authoritative_subject_ref",
    "program_ref",
    "semantic_attempt_ref",
    "candidate_ref",
    "effect_intent_ref",
    "author_command_ref",
    "attempt_fence_ref",
    "effect_fence_ref",
    "delivery_attempt_ref",
    "authority_evaluation_ref",
    "authority_evaluation_digest",
    "observation_state",
    "observation_version",
    "authority_observation_issued_at",
    "authority_observation_expires_at",
    "source_authority_ref",
    "verification_evidence_ref",
    "verification_evidence_digest",
    "authority_observation_digest",
)
_AUTHORITY_EXPECTED_BINDING_FIELDS = (
    "authoritative_subject_kind",
    "authoritative_subject_ref",
    "program_ref",
    "semantic_attempt_ref",
    "candidate_ref",
    "effect_intent_ref",
    "author_command_ref",
    "attempt_fence_ref",
    "effect_fence_ref",
    "delivery_attempt_ref",
    "authority_evaluation_ref",
    "authority_evaluation_digest",
    "source_authority_ref",
    "verification_evidence_ref",
    "verification_evidence_digest",
)
_PLANNING_CONTEXT_FIELDS = (
    "schema_id",
    "planning_context_ref",
    "program_ref",
    "program_version_ref",
    "program_version_number",
    "accepted_intent_revision_ref",
    "work_item_ref",
    "work_item_revision_ref",
    "semantic_attempt_ref",
    "semantic_attempt_digest",
    "attempt_number",
    "candidate_ref",
    "basis_decision_ref",
    "basis_decision_digest",
    "work_spec_ref",
    "work_spec_digest",
    "work_spec_safe_projection_digest",
    "effect_intent_ref",
    "effect_intent_digest",
    "author_command_ref",
    "author_command_digest",
    "standing_grant_ref",
    "standing_grant_digest",
    "attempt_authorization_ref",
    "attempt_authorization_digest",
    "effect_authorization_ref",
    "effect_authorization_digest",
    "attempt_fence_ref",
    "attempt_fence_digest",
    "attempt_fence_allowed_effect_classes_json",
    "attempt_fence_expires_at",
    "effect_fence_ref",
    "effect_fence_digest",
    "effect_fence_allowed_effect_classes_json",
    "effect_fence_expires_at",
    "delivery_attempt_ref",
    "delivery_envelope_digest",
    "delivery_attempt_digest",
    "expected_program_head_revision",
    "expected_work_item_head_revision",
    "expected_effect_head_fence_ref",
    "expected_effect_head_revision",
    "expected_effect_head_digest",
    "expected_delivery_head_attempt_ref",
    "expected_delivery_head_revision",
    "expected_delivery_head_digest",
    "global_stop_ref",
    "global_stop_version",
    "global_stop_state",
    "authority_evaluation_ref",
    "authority_evaluation_digest",
    "authority_selection_observation_schema_id",
    "authority_selection_observation_ref",
    "authoritative_subject_kind",
    "authoritative_subject_ref",
    "authority_observation_state",
    "authority_observation_version",
    "authority_observation_issued_at",
    "authority_observation_expires_at",
    "source_authority_ref",
    "verification_evidence_ref",
    "verification_evidence_digest",
    "authority_selection_observation_digest",
    "standing_policy_ref",
    "standing_policy_digest",
    "risk_lane_ref",
    "risk_lane_digest",
    "repository_ref",
    "base_git_object_format",
    "base_git_oid",
    "authorized_path_scope_digest",
    "cost_ceiling_ref",
    "cost_ceiling_digest",
    "token_ceiling_ref",
    "token_ceiling_digest",
    "time_ceiling_ref",
    "time_ceiling_digest",
    "delivery_ceiling_ref",
    "delivery_ceiling_digest",
    "effect_ceiling_ref",
    "effect_ceiling_digest",
    "validation_requirement_ref",
    "validation_requirement_digest",
    "validation_safe_evidence_digest",
    "review_requirement_ref",
    "review_requirement_digest",
    "review_safe_evidence_digest",
    "qualified_remote_host_readiness_ref",
    "qualified_remote_host_readiness_digest",
    "planning_context_captured_at",
    "planning_context_digest",
)
_SOURCE_INVOCATION_FIELDS = (
    "schema_id",
    "source_invocation_ref",
    "proposal_phase",
    "model_contract_ref",
    "model_contract_digest",
    "model_configuration_ref",
    "model_configuration_digest",
    "context_schema_id",
    "context_ref",
    "context_digest",
    "artifact_schema_id",
    "artifact_ref",
    "artifact_digest",
    "invocation_status",
    "source_invocation_started_at",
    "source_invocation_completed_at",
    "source_invocation_digest",
)
_ARTIFACT_BINDING_FIELDS = (
    "schema_id",
    "artifact_ref",
    "proposal_phase",
    "artifact_schema_id",
    "artifact_digest",
    "artifact_canonical_byte_length",
    "safe_projection_schema_id",
    "safe_projection_digest",
    "privacy_classification",
    "artifact_validated_at",
    "artifact_binding_digest",
)
_WORK_UNIT_FIELDS = (
    "ordinal",
    "work_unit_ref",
    "action_kind",
    "summary",
    "depends_on_work_unit_refs",
    "authorized_path_ordinals",
    "expected_output_refs",
    "validation_refs",
    "required_evidence_roles",
    "prerequisite_refs",
    "stop_condition_refs",
)
_EXPECTED_OUTPUT_FIELDS = (
    "output_ref",
    "owner_work_unit_ref",
    "output_kind",
    "description",
)
_VALIDATION_STEP_FIELDS = (
    "ordinal",
    "validation_ref",
    "work_unit_refs",
    "validation_kind",
    "target",
    "success_criterion",
)
_ASSUMPTION_FIELDS = ("assumption_ref", "statement")
_RISK_FIELDS = (
    "risk_ref",
    "risk_kind",
    "description",
    "mitigation",
    "materiality",
    "affected_work_unit_refs",
)
_PREREQUISITE_FIELDS = ("prerequisite_ref", "evidence_role", "requirement")
_STOP_CONDITION_FIELDS = ("stop_condition_ref", "statement")
_RESOURCE_FIELDS = ("allowed_effect_classes", *_CEILING_FIELDS)
_ARTIFACT_FIELDS = (
    "schema_id",
    "artifact_ref",
    "proposal_ref",
    "proposal_phase",
    "planning_context_ref",
    "implementation_strategy",
    "proposed_work_units",
    "affected_authorized_paths",
    "expected_outputs",
    "validation_strategy",
    "material_assumptions",
    "risks_and_uncertainties",
    "required_evidence_and_prerequisites",
    "stop_or_replan_conditions",
    "proposed_resource_and_effect_use",
    "recommendation",
    "reason_code",
    "artifact_digest",
)
_PROJECTION_FIELDS = (
    "schema_id",
    "proposal_ref",
    "proposal_phase",
    "artifact_schema_id",
    "artifact_ref",
    "artifact_digest",
    "planning_context_schema_id",
    "planning_context_ref",
    "planning_context_digest",
    "strategy_item_count",
    "work_unit_count",
    "affected_path_count",
    "affected_path_set_digest",
    "expected_output_count",
    "expected_output_set_digest",
    "validation_step_count",
    "validation_strategy_digest",
    "assumption_count",
    "assumption_set_digest",
    "risk_count",
    "risk_set_digest",
    "prerequisite_count",
    "prerequisite_set_digest",
    "stop_condition_count",
    "stop_condition_set_digest",
    "proposed_resource_effect_use_digest",
    "allowed_effect_classes",
    "recommendation",
    "reason_code",
    "safe_projection_digest",
)
_EVIDENCE_BINDING_FIELDS = (
    "schema_id",
    "proposal_ref",
    "proposal_phase",
    "evidence_set_ref",
    "evidence_role",
    "role_rank",
    "ordinal",
    "evidence_ref",
    "evidence_digest",
    "required_for_selection",
    "evidence_bound_at",
    "evidence_binding_digest",
)
_PROPOSAL_FIELDS = (
    "schema_id",
    "proposal_ref",
    "proposal_phase",
    "source_invocation_ref",
    "source_invocation_digest",
    "model_contract_ref",
    "model_contract_digest",
    "model_configuration_ref",
    "model_configuration_digest",
    "context_schema_id",
    "context_ref",
    "context_digest",
    "artifact_schema_id",
    "artifact_ref",
    "artifact_digest",
    "safe_projection_schema_id",
    "safe_projection_digest",
    "recommendation",
    "reason_code",
    "evidence_set_ref",
    "evidence_set_digest",
    "proposal_created_at",
    "proposal_digest",
)


ModelConfigurationSafeV1 = _make_value_class(
    "ModelConfigurationSafeV1",
    _MODEL_CONFIGURATION_FIELDS,
    schema=_SCHEMAS["model_configuration"],
    domain=_DOMAINS["model_configuration"],
    digest_field="model_configuration_digest",
)
AuthoritySelectionObservationSafeV1 = _make_value_class(
    "AuthoritySelectionObservationSafeV1",
    _AUTHORITY_OBSERVATION_FIELDS,
    schema=_SCHEMAS["authority_observation"],
    domain=_DOMAINS["authority_observation"],
    digest_field="authority_observation_digest",
)
AuthorityExpectedBinding = _make_value_class(
    "AuthorityExpectedBinding",
    _AUTHORITY_EXPECTED_BINDING_FIELDS,
)
PreExecutionPlanningContextV1 = _make_value_class(
    "PreExecutionPlanningContextV1",
    _PLANNING_CONTEXT_FIELDS,
    schema=_SCHEMAS["planning_context"],
    domain=_DOMAINS["planning_context"],
    digest_field="planning_context_digest",
)
ModelSourceInvocationV1 = _make_value_class(
    "ModelSourceInvocationV1",
    _SOURCE_INVOCATION_FIELDS,
    schema=_SCHEMAS["source_invocation"],
    domain=_DOMAINS["source_invocation"],
    digest_field="source_invocation_digest",
)
PrivateProposalArtifactBindingV1 = _make_value_class(
    "PrivateProposalArtifactBindingV1",
    _ARTIFACT_BINDING_FIELDS,
    schema=_SCHEMAS["artifact_binding"],
    domain=_DOMAINS["artifact_binding"],
    digest_field="artifact_binding_digest",
)
PreExecutionWorkUnitV1 = _make_value_class("PreExecutionWorkUnitV1", _WORK_UNIT_FIELDS)
PreExecutionExpectedOutputV1 = _make_value_class(
    "PreExecutionExpectedOutputV1", _EXPECTED_OUTPUT_FIELDS
)
PreExecutionValidationStepV1 = _make_value_class(
    "PreExecutionValidationStepV1", _VALIDATION_STEP_FIELDS
)
PreExecutionAssumptionV1 = _make_value_class(
    "PreExecutionAssumptionV1", _ASSUMPTION_FIELDS
)
PreExecutionRiskV1 = _make_value_class("PreExecutionRiskV1", _RISK_FIELDS)
PreExecutionPrerequisiteV1 = _make_value_class(
    "PreExecutionPrerequisiteV1", _PREREQUISITE_FIELDS
)
PreExecutionStopConditionV1 = _make_value_class(
    "PreExecutionStopConditionV1", _STOP_CONDITION_FIELDS
)
ProposedResourceAndEffectUseV1 = _make_value_class(
    "ProposedResourceAndEffectUseV1", _RESOURCE_FIELDS
)
PreExecutionPlanArtifactV1 = _make_value_class(
    "PreExecutionPlanArtifactV1",
    _ARTIFACT_FIELDS,
    schema=_SCHEMAS["artifact"],
    domain=_DOMAINS["artifact"],
    digest_field="artifact_digest",
)
PreExecutionPlanSafeProjectionV1 = _make_value_class(
    "PreExecutionPlanSafeProjectionV1",
    _PROJECTION_FIELDS,
    schema=_SCHEMAS["projection"],
    domain=_DOMAINS["projection"],
    digest_field="safe_projection_digest",
)
ModelProposalEvidenceBindingV1 = _make_value_class(
    "ModelProposalEvidenceBindingV1",
    _EVIDENCE_BINDING_FIELDS,
    schema=_SCHEMAS["evidence_binding"],
    domain=_DOMAINS["evidence_binding"],
    digest_field="evidence_binding_digest",
)
PreExecutionModelProposalV1 = _make_value_class(
    "PreExecutionModelProposalV1",
    _PROPOSAL_FIELDS,
    schema=_SCHEMAS["proposal"],
    domain=_DOMAINS["proposal"],
    digest_field="proposal_digest",
)


@dataclass(frozen=True, slots=True, repr=False)
class ModelProposalEvidenceSetV1(_SemanticValue):
    evidence_set_ref: object
    proposal_ref: object
    proposal_phase: object
    entries: object
    evidence_set_digest: object

    _FIELD_ORDER = (
        "evidence_set_ref",
        "proposal_ref",
        "proposal_phase",
        "entries",
        "evidence_set_digest",
    )
    _DOMAIN = _EVIDENCE_SET_DOMAIN
    _DIGEST_FIELD = "evidence_set_digest"

    __init_subclass__ = _reject_concrete_subclass

    def __post_init__(self) -> None:
        # ``to_mapping`` intentionally emits the smaller evidence-set entry
        # identity.  Validate the carrier before that method can dereference a
        # hostile member supplied directly to the dataclass constructor.
        if type(self.entries) is not tuple or any(
            type(binding) is not ModelProposalEvidenceBindingV1
            for binding in typing.cast(tuple[object, ...], self.entries)
        ):
            _violate("preselection_timestamp_record_invalid")
        _SemanticValue.__post_init__(self)

    def to_mapping(self) -> dict[str, object]:
        bindings = typing.cast(tuple[ModelProposalEvidenceBindingV1, ...], self.entries)
        return {
            "evidence_set_ref": self.evidence_set_ref,
            "proposal_ref": self.proposal_ref,
            "proposal_phase": self.proposal_phase,
            "entries": tuple(
                {
                    "evidence_role": binding.evidence_role,
                    "role_rank": binding.role_rank,
                    "ordinal": binding.ordinal,
                    "evidence_ref": binding.evidence_ref,
                    "evidence_digest": binding.evidence_digest,
                    "evidence_binding_digest": binding.evidence_binding_digest,
                }
                for binding in bindings
            ),
            "evidence_set_digest": self.evidence_set_digest,
        }


@dataclass(frozen=True, slots=True, repr=False)
class PreExecutionProposalSelectionBundleV1(_SemanticValue):
    authority_observation: object
    authority_expected_binding: object
    attempt_fence: object
    effect_fence: object
    planning_context: object
    source_invocation: object
    private_artifact_binding: object
    private_artifact: object
    safe_projection: object
    evidence_bindings: object
    evidence_set: object
    model_proposal: object

    _FIELD_ORDER = (
        "authority_observation",
        "authority_expected_binding",
        "attempt_fence",
        "effect_fence",
        "planning_context",
        "source_invocation",
        "private_artifact_binding",
        "private_artifact",
        "safe_projection",
        "evidence_bindings",
        "evidence_set",
        "model_proposal",
    )

    __init_subclass__ = _reject_concrete_subclass

    def __post_init__(self) -> None:
        expected = (
            (self.authority_observation, AuthoritySelectionObservationSafeV1),
            (self.authority_expected_binding, AuthorityExpectedBinding),
            (self.attempt_fence, AttemptFenceV1),
            (self.effect_fence, EffectFenceV1),
            (self.planning_context, PreExecutionPlanningContextV1),
            (self.source_invocation, ModelSourceInvocationV1),
            (self.private_artifact_binding, PrivateProposalArtifactBindingV1),
            (self.private_artifact, PreExecutionPlanArtifactV1),
            (self.safe_projection, PreExecutionPlanSafeProjectionV1),
            (self.evidence_set, ModelProposalEvidenceSetV1),
            (self.model_proposal, PreExecutionModelProposalV1),
        )
        if any(type(member) is not member_type for member, member_type in expected):
            _violate("invalid_field_type")
        if type(self.evidence_bindings) is not tuple or any(
            type(binding) is not ModelProposalEvidenceBindingV1
            for binding in typing.cast(tuple[object, ...], self.evidence_bindings)
        ):
            _violate("preselection_timestamp_record_invalid")
        _SemanticValue.__post_init__(self)

    def to_mapping(self) -> dict[str, object]:
        return {
            "authority_observation": self.authority_observation.to_mapping(),
            "authority_expected_binding": self.authority_expected_binding.to_mapping(),
            "attempt_fence": self.attempt_fence.to_mapping(),
            "effect_fence": self.effect_fence.to_mapping(),
            "planning_context": self.planning_context.to_mapping(),
            "source_invocation": self.source_invocation.to_mapping(),
            "private_artifact_binding": self.private_artifact_binding.to_mapping(),
            "private_artifact": self.private_artifact.to_mapping(),
            "safe_projection": self.safe_projection.to_mapping(),
            "evidence_bindings": tuple(
                binding.to_mapping() for binding in self.evidence_bindings
            ),
            "evidence_set": self.evidence_set.to_mapping(),
            "model_proposal": self.model_proposal.to_mapping(),
        }


_SEMANTIC_CLASSES = (
    *_SEMANTIC_CLASSES,
    ModelProposalEvidenceSetV1,
    PreExecutionProposalSelectionBundleV1,
)


# Each number below is the exact maximum clone work implied by the existing
# collection ceilings.  A semantic object, tuple container, scalar field, and
# repeated tuple member each cost one unit; shared acyclic members therefore
# retain per-occurrence accounting rather than becoming an aliasing signal.
# Across all 32 work units, dependency edges total at most sum(range(32)); the
# ownership/coverage rule makes expected-output references total exactly 32.
_MAX_ALL_WORK_UNITS_RECONSTRUCTION_WORK = (
    32 * (1 + 4 + 7)
    + sum(range(32))
    + 32 * 64
    + 32
    + 32 * 32
    + 32 * len(_EVIDENCE_ROLES)
    + 32 * 32
    + 32 * 16
)
_MAX_OUTPUT_RECONSTRUCTION_WORK = 1 + len(_EXPECTED_OUTPUT_FIELDS)
_MAX_VALIDATION_RECONSTRUCTION_WORK = 1 + 5 + (1 + 32)
_MAX_ASSUMPTION_RECONSTRUCTION_WORK = 1 + len(_ASSUMPTION_FIELDS)
_MAX_RISK_RECONSTRUCTION_WORK = 1 + 5 + (1 + 32)
_MAX_PREREQUISITE_RECONSTRUCTION_WORK = 1 + len(_PREREQUISITE_FIELDS)
_MAX_STOP_RECONSTRUCTION_WORK = 1 + len(_STOP_CONDITION_FIELDS)
_MAX_RESOURCE_RECONSTRUCTION_WORK = (
    1 + len(_CEILING_FIELDS) + 1 + len(_EFFECT_CLASSES)
)
_MAX_ARTIFACT_RECONSTRUCTION_WORK = sum(
    (
        1,
        8,
        1 + 8,
        1 + _MAX_ALL_WORK_UNITS_RECONSTRUCTION_WORK,
        1 + 64,
        1 + 32 * _MAX_OUTPUT_RECONSTRUCTION_WORK,
        1 + 32 * _MAX_VALIDATION_RECONSTRUCTION_WORK,
        1 + 16 * _MAX_ASSUMPTION_RECONSTRUCTION_WORK,
        1 + 16 * _MAX_RISK_RECONSTRUCTION_WORK,
        1 + 32 * _MAX_PREREQUISITE_RECONSTRUCTION_WORK,
        1 + 16 * _MAX_STOP_RECONSTRUCTION_WORK,
        _MAX_RESOURCE_RECONSTRUCTION_WORK,
    )
)
_MAX_EVIDENCE_BINDING_RECONSTRUCTION_WORK = 1 + len(_EVIDENCE_BINDING_FIELDS)
_MAX_EVIDENCE_SET_RECONSTRUCTION_WORK = (
    1 + 4 + 1 + 15 * _MAX_EVIDENCE_BINDING_RECONSTRUCTION_WORK
)
_MAX_PROJECTION_RECONSTRUCTION_WORK = (
    1 + len(_PROJECTION_FIELDS) - 1 + 1 + len(_EFFECT_CLASSES)
)
_MAX_ATTEMPT_FENCE_RECONSTRUCTION_WORK = (
    1
    + len(AttemptFenceV1._FIELDS)
    + len(_WORKER_AUTHORIZED_PATHS)
    + len(_EFFECT_CLASSES)
    + len(_CEILING_FIELDS)
)
_MAX_EFFECT_FENCE_RECONSTRUCTION_WORK = (
    1
    + len(EffectFenceV1._FIELDS)
    + len(_WORKER_AUTHORIZED_PATHS)
    + len(_CEILING_FIELDS)
)
_MAX_DECLARED_SEMANTIC_GRAPH_WORK = sum(
    (
        1,
        1 + len(_AUTHORITY_OBSERVATION_FIELDS),
        1 + len(_AUTHORITY_EXPECTED_BINDING_FIELDS),
        _MAX_ATTEMPT_FENCE_RECONSTRUCTION_WORK,
        _MAX_EFFECT_FENCE_RECONSTRUCTION_WORK,
        1 + len(_PLANNING_CONTEXT_FIELDS),
        1 + len(_SOURCE_INVOCATION_FIELDS),
        1 + len(_ARTIFACT_BINDING_FIELDS),
        _MAX_ARTIFACT_RECONSTRUCTION_WORK,
        _MAX_PROJECTION_RECONSTRUCTION_WORK,
        1 + 15 * _MAX_EVIDENCE_BINDING_RECONSTRUCTION_WORK,
        _MAX_EVIDENCE_SET_RECONSTRUCTION_WORK,
        1 + len(_PROPOSAL_FIELDS),
    )
)
# Two complete declared graphs plus the maximum evidence-binding collection
# twice cover composite constructor validation: once for the bundle's explicit
# binding tuple and once for the evidence-set's own exact entry validation.
# The derivation remains closed and finite rather than depending on input shape.
_MAX_SEMANTIC_RECONSTRUCTION_WORK = (
    2 * _MAX_DECLARED_SEMANTIC_GRAPH_WORK
    + 2 * 15 * _MAX_EVIDENCE_BINDING_RECONSTRUCTION_WORK
)
assert type(_MAX_SEMANTIC_RECONSTRUCTION_WORK) is int
assert _MAX_SEMANTIC_RECONSTRUCTION_WORK > _MAX_DECLARED_SEMANTIC_GRAPH_WORK > 0


class _SemanticReconstructionBudget:
    __slots__ = ("_remaining", "_consumed", "_exhaustion_reason")

    def __init__(
        self,
        limit: int = _MAX_SEMANTIC_RECONSTRUCTION_WORK,
        exhaustion_reason: str = "private_plan_nested_collection_invalid",
    ) -> None:
        if type(limit) is not int or limit <= 0:
            _violate("private_plan_nested_collection_invalid")
        if type(exhaustion_reason) is not str or exhaustion_reason not in (
            "private_plan_nested_collection_invalid",
            "recovery_unresolved",
        ):
            _violate("private_plan_nested_collection_invalid")
        self._remaining = limit
        self._consumed = 0
        self._exhaustion_reason = exhaustion_reason

    @property
    def remaining(self) -> int:
        return self._remaining

    @property
    def consumed(self) -> int:
        return self._consumed

    @property
    def exhaustion_reason(self) -> str:
        return self._exhaustion_reason

    def consume(self) -> None:
        if self._remaining == 0:
            _violate(self._exhaustion_reason)
        self._remaining -= 1
        self._consumed += 1


_CURRENT_SEMANTIC_RECONSTRUCTION_BUDGET: ContextVar[
    _SemanticReconstructionBudget | None
] = ContextVar(
    "_CURRENT_SEMANTIC_RECONSTRUCTION_BUDGET",
    default=None,
)


def _current_semantic_reconstruction_budget(
) -> _SemanticReconstructionBudget | None:
    return _CURRENT_SEMANTIC_RECONSTRUCTION_BUDGET.get()


def _resolve_semantic_reconstruction_budget(
    supplied: _SemanticReconstructionBudget | None,
) -> _SemanticReconstructionBudget:
    if supplied is not None and type(supplied) is not _SemanticReconstructionBudget:
        _violate("private_plan_nested_collection_invalid")
    current = _current_semantic_reconstruction_budget()
    if supplied is None:
        return current if current is not None else _SemanticReconstructionBudget()
    if current is not None and supplied is not current:
        _violate(current.exhaustion_reason)
    return supplied


class _SemanticReconstructionBudgetScope:
    __slots__ = ("_budget", "_token")

    def __init__(self, budget: _SemanticReconstructionBudget) -> None:
        if type(budget) is not _SemanticReconstructionBudget:
            _violate("private_plan_nested_collection_invalid")
        self._budget = budget
        self._token: object | None = None

    def __enter__(self) -> None:
        current = _current_semantic_reconstruction_budget()
        if current is not None:
            if current is not self._budget:
                _violate(current.exhaustion_reason)
            return None
        self._token = _CURRENT_SEMANTIC_RECONSTRUCTION_BUDGET.set(self._budget)
        return None

    def __exit__(
        self,
        exception_type: object,
        exception: object,
        traceback: object,
    ) -> None:
        del exception_type, exception, traceback
        token = self._token
        self._token = None
        if token is not None:
            _CURRENT_SEMANTIC_RECONSTRUCTION_BUDGET.reset(token)  # type: ignore[arg-type]


def _semantic_reconstruction_budget_scope(
    budget: _SemanticReconstructionBudget,
) -> _SemanticReconstructionBudgetScope:
    return _SemanticReconstructionBudgetScope(budget)


def _reconstruct_exact_fence(
    value: object,
    budget: _SemanticReconstructionBudget | None = None,
) -> AttemptFenceV1 | EffectFenceV1:
    budget = _resolve_semantic_reconstruction_budget(budget)
    kind = type(value)
    trusted_kind = _select_exact_type(kind, (AttemptFenceV1, EffectFenceV1))
    if trusted_kind is None:
        _violate("invalid_field_type")
    budget.consume()
    checked_mapping: dict[str, object] = {}
    sequence_fields = (
        ("path_ceiling",)
        if trusted_kind is EffectFenceV1
        else ("path_ceiling", "allowed_effect_classes")
    )
    ceilings_field = (
        "effect_ceilings"
        if trusted_kind is EffectFenceV1
        else "aggregate_ceilings"
    )
    for field in trusted_kind._FIELDS:
        budget.consume()
        try:
            member = object.__getattribute__(value, f"_{field}")
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception:
            _violate("invalid_field_type")
        if field in sequence_fields:
            if type(member) is not tuple or len(member) > 64:
                _violate("invalid_field_type")
            checked_sequence = []
            for item in typing.cast(tuple[object, ...], member):
                budget.consume()
                checked_sequence.append(item)
            checked_mapping[field] = checked_sequence
        elif field == ceilings_field:
            if type(member) is not CeilingsV1:
                _violate("invalid_field_type")
            ceiling_mapping: dict[str, object] = {}
            for ceiling_field in _CEILING_FIELDS:
                budget.consume()
                try:
                    ceiling_mapping[ceiling_field] = object.__getattribute__(
                        member, f"_{ceiling_field}"
                    )
                except (KeyboardInterrupt, SystemExit, GeneratorExit):
                    raise
                except Exception:
                    _violate("invalid_field_type")
            checked_mapping[field] = ceiling_mapping
        else:
            checked_mapping[field] = member
    reconstructed: object = None
    failed = False
    try:
        reconstructed = trusted_kind.from_mapping(checked_mapping)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        failed = True
    if failed or type(reconstructed) is not trusted_kind:
        _violate("invalid_field_type")
    return typing.cast(AttemptFenceV1 | EffectFenceV1, reconstructed)


def _reconstruct_exact_semantic_member(
    value: object,
    active: set[int],
    depth: int,
    budget: _SemanticReconstructionBudget | None = None,
) -> object:
    budget = _resolve_semantic_reconstruction_budget(budget)
    if depth > 128:
        _violate("invalid_field_type")
    kind = type(value)
    if _select_exact_type(kind, (AttemptFenceV1, EffectFenceV1)) is not None:
        return _reconstruct_exact_fence(value, budget)
    budget.consume()
    if kind is str or kind is int or kind is bool or kind is type(None):
        return value
    if kind is tuple:
        identity = id(value)
        if identity in active:
            _violate("invalid_field_type")
        sequence = typing.cast(tuple[object, ...], value)
        if len(sequence) > 64:
            _violate("private_plan_nested_collection_invalid")
        active.add(identity)
        try:
            return tuple(
                _reconstruct_exact_semantic_member(
                    member, active, depth + 1, budget
                )
                for member in sequence
            )
        finally:
            active.discard(identity)
    trusted_kind = _semantic_type_by_identity(kind)
    if trusted_kind is None:
        _violate("invalid_field_type")
    identity = id(value)
    if identity in active:
        _violate("invalid_field_type")
    active.add(identity)
    try:
        values: dict[str, object] = {}
        missing = False
        for name in typing.cast(type[_SemanticValue], trusted_kind)._FIELD_ORDER:
            try:
                member = object.__getattribute__(value, name)
            except (KeyboardInterrupt, SystemExit, GeneratorExit):
                raise
            except Exception:
                missing = True
                break
            values[name] = _reconstruct_exact_semantic_member(
                member, active, depth + 1, budget
            )
        if missing:
            _violate("invalid_field_type")
        reconstructed: object = None
        failed = False
        try:
            reconstructed = trusted_kind(**values)
        except _CognitiveProposalContractViolation:
            raise
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception:
            failed = True
        if failed or type(reconstructed) is not trusted_kind:
            _violate("invalid_field_type")
        return reconstructed
    finally:
        active.discard(identity)


def _reconstruct_exact_semantic_value(
    value: object,
    expected: type[object],
    budget: _SemanticReconstructionBudget | None = None,
) -> _SemanticValue:
    if (
        type(expected) is not type
        or _semantic_type_by_identity(expected) is not expected
    ):
        _violate("invalid_field_type")
    if type(value) is not expected:
        _violate("invalid_field_type")
    exact_budget = _resolve_semantic_reconstruction_budget(budget)
    try:
        with _semantic_reconstruction_budget_scope(exact_budget):
            reconstructed = _reconstruct_exact_semantic_member(
                value,
                set(),
                0,
                exact_budget,
            )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except _CognitiveProposalContractViolation:
        raise
    except (MemoryError, RecursionError):
        _violate(exact_budget.exhaustion_reason)
    if type(reconstructed) is not expected:
        _violate("invalid_field_type")
    return typing.cast(_SemanticValue, reconstructed)


def _require_type(value: object, expected: type[object]) -> None:
    if type(value) is not expected:
        _violate("invalid_field_type")


def _require_tuple_of(
    value: object,
    expected: type[object],
    minimum: int,
    maximum: int,
) -> tuple[object, ...]:
    if type(value) is not tuple or not minimum <= len(value) <= maximum:
        _violate("private_plan_nested_collection_invalid")
    result = typing.cast(tuple[object, ...], value)
    if any(type(member) is not expected for member in result):
        _violate("private_plan_nested_collection_invalid")
    return result


def _narrative(value: object, maximum: int) -> str:
    if type(value) is not str:
        _violate("private_plan_narrative_invalid")
    result = typing.cast(str, value)
    if any(0xD800 <= ord(character) <= 0xDFFF for character in result):
        _violate("private_plan_narrative_invalid")
    encoded = result.encode("utf-8", errors="strict")
    if (
        not 1 <= len(encoded) <= maximum
        or result != result.strip()
        or unicodedata.normalize("NFC", result) != result
        or any(unicodedata.category(character) == "Cc" for character in result)
        or not any(
            unicodedata.category(character)[:1] in ("L", "N") for character in result
        )
        or result.casefold()
        in {"...", "n/a", "none", "placeholder", "tbd", "todo", "unknown"}
    ):
        _violate("private_plan_narrative_invalid")
    return result


def _ordered_unique_refs(
    value: object, allowed: tuple[str, ...], minimum: int = 1
) -> tuple[str, ...]:
    if type(value) is not tuple or not minimum <= len(value) <= len(allowed):
        _violate("private_plan_nested_collection_invalid")
    result = typing.cast(tuple[object, ...], value)
    if (
        any(type(item) is not str or item not in allowed for item in result)
        or len(set(typing.cast(tuple[str, ...], result))) != len(result)
        or tuple(item for item in allowed if item in result) != result
    ):
        _violate("private_plan_nested_collection_invalid")
    return typing.cast(tuple[str, ...], result)


def _validate_nested(value: _SemanticValue) -> None:
    kind = type(value)
    mapping = value.to_mapping()
    if kind is PreExecutionWorkUnitV1:
        _require_nonnegative_integer(
            mapping["ordinal"], "private_plan_nested_collection_invalid"
        )
        _require_safe_ref(
            mapping["work_unit_ref"], "private_plan_nested_collection_invalid"
        )
        _require_enum(
            mapping["action_kind"],
            (
                "analyze",
                "modify_authorized_path",
                "create_authorized_path",
                "delete_authorized_path",
                "run_validation",
                "review_evidence",
                "prepare_candidate",
            ),
            "private_plan_closed_vocabulary_invalid",
        )
        _narrative(mapping["summary"], 512)
        for field_name in (
            "depends_on_work_unit_refs",
            "expected_output_refs",
            "validation_refs",
            "required_evidence_roles",
            "prerequisite_refs",
            "stop_condition_refs",
        ):
            members = mapping[field_name]
            if type(members) is not tuple or any(
                type(item) is not str for item in members
            ):
                _violate("private_plan_nested_collection_invalid")
        ordinals = mapping["authorized_path_ordinals"]
        if type(ordinals) is not tuple or any(
            type(item) is not int or item < 0 for item in ordinals
        ):
            _violate("private_plan_nested_collection_invalid")
    elif kind is PreExecutionExpectedOutputV1:
        _require_safe_ref(
            mapping["output_ref"], "private_plan_nested_collection_invalid"
        )
        _require_safe_ref(
            mapping["owner_work_unit_ref"], "private_plan_nested_collection_invalid"
        )
        _require_enum(
            mapping["output_kind"],
            (
                "source_change",
                "test_change",
                "documentation_change",
                "candidate_manifest",
                "validation_evidence",
            ),
            "private_plan_closed_vocabulary_invalid",
        )
        _narrative(mapping["description"], 512)
    elif kind is PreExecutionValidationStepV1:
        _require_nonnegative_integer(
            mapping["ordinal"], "private_plan_nested_collection_invalid"
        )
        _require_safe_ref(
            mapping["validation_ref"], "private_plan_nested_collection_invalid"
        )
        if type(mapping["work_unit_refs"]) is not tuple:
            _violate("private_plan_nested_collection_invalid")
        _require_enum(
            mapping["validation_kind"],
            (
                "focused_test",
                "contract_test",
                "static_check",
                "build",
                "manual_review",
            ),
            "private_plan_closed_vocabulary_invalid",
        )
        _narrative(mapping["target"], 512)
        _narrative(mapping["success_criterion"], 512)
    elif kind is PreExecutionAssumptionV1:
        _require_safe_ref(
            mapping["assumption_ref"], "private_plan_nested_collection_invalid"
        )
        _narrative(mapping["statement"], 512)
    elif kind is PreExecutionRiskV1:
        _require_safe_ref(mapping["risk_ref"], "private_plan_nested_collection_invalid")
        _require_enum(
            mapping["risk_kind"],
            (
                "correctness",
                "authority",
                "privacy",
                "compatibility",
                "operational",
                "unknown",
            ),
            "private_plan_closed_vocabulary_invalid",
        )
        _require_enum(
            mapping["materiality"],
            ("material", "blocking"),
            "private_plan_closed_vocabulary_invalid",
        )
        _narrative(mapping["description"], 512)
        _narrative(mapping["mitigation"], 512)
        if type(mapping["affected_work_unit_refs"]) is not tuple:
            _violate("private_plan_nested_collection_invalid")
    elif kind is PreExecutionPrerequisiteV1:
        _require_safe_ref(
            mapping["prerequisite_ref"], "private_plan_nested_collection_invalid"
        )
        _require_enum(
            mapping["evidence_role"],
            _EVIDENCE_ROLES,
            "private_plan_closed_vocabulary_invalid",
        )
        _narrative(mapping["requirement"], 512)
    elif kind is PreExecutionStopConditionV1:
        _require_safe_ref(
            mapping["stop_condition_ref"], "private_plan_nested_collection_invalid"
        )
        _narrative(mapping["statement"], 512)
    elif kind is ProposedResourceAndEffectUseV1:
        effects = mapping["allowed_effect_classes"]
        if type(effects) is not tuple:
            _violate("private_plan_nested_collection_invalid")
        _ordered_unique_refs(effects, _EFFECT_CLASSES)
        for field_name in _CEILING_FIELDS:
            _require_nonnegative_integer(
                mapping[field_name], "private_plan_nested_collection_invalid"
            )


def _validate_artifact(value: PreExecutionPlanArtifactV1) -> None:
    mapping = value.to_mapping()
    for field_name in ("artifact_ref", "proposal_ref", "planning_context_ref"):
        _require_safe_ref(mapping[field_name], "private_plan_nested_collection_invalid")
    _require_enum(
        mapping["proposal_phase"],
        ("pre_execution_plan",),
        "private_plan_closed_vocabulary_invalid",
    )
    work_units = _require_tuple_of(
        value.proposed_work_units, PreExecutionWorkUnitV1, 1, 32
    )
    outputs = _require_tuple_of(
        value.expected_outputs, PreExecutionExpectedOutputV1, 1, 32
    )
    validations = _require_tuple_of(
        value.validation_strategy, PreExecutionValidationStepV1, 1, 32
    )
    assumptions = _require_tuple_of(
        value.material_assumptions, PreExecutionAssumptionV1, 1, 16
    )
    risks = _require_tuple_of(value.risks_and_uncertainties, PreExecutionRiskV1, 1, 16)
    prerequisites = _require_tuple_of(
        value.required_evidence_and_prerequisites, PreExecutionPrerequisiteV1, 1, 32
    )
    stops = _require_tuple_of(
        value.stop_or_replan_conditions, PreExecutionStopConditionV1, 1, 16
    )
    _require_type(
        value.proposed_resource_and_effect_use, ProposedResourceAndEffectUseV1
    )
    strategies = value.implementation_strategy
    if type(strategies) is not tuple or not 1 <= len(strategies) <= 8:
        _violate("private_plan_nested_collection_invalid")
    for item in strategies:
        _narrative(item, 768)
    if len(set(typing.cast(tuple[str, ...], strategies))) != len(strategies):
        _violate("private_plan_nested_collection_invalid")
    paths = value.affected_authorized_paths
    if (
        type(paths) is not tuple
        or not 1 <= len(paths) <= 64
        or any(type(path) is not str for path in paths)
    ):
        _violate("private_plan_nested_collection_invalid")
    for path in paths:
        checked_path = _require_canonical_string(
            path, reason="private_plan_nested_collection_invalid"
        )
        if (
            not checked_path
            or len(checked_path.encode("utf-8")) > 512
            or checked_path.startswith("/")
            or any(part in ("", ".", "..") for part in checked_path.split("/"))
        ):
            _violate("private_plan_nested_collection_invalid")
    if len(set(paths)) != len(paths) or tuple(sorted(paths)) != paths:
        _violate("private_plan_nested_collection_invalid")
    work_refs = tuple(typing.cast(str, unit.work_unit_ref) for unit in work_units)
    output_refs = tuple(typing.cast(str, output.output_ref) for output in outputs)
    validation_refs = tuple(
        typing.cast(str, step.validation_ref) for step in validations
    )
    prerequisite_refs = tuple(
        typing.cast(str, item.prerequisite_ref) for item in prerequisites
    )
    stop_refs = tuple(typing.cast(str, item.stop_condition_ref) for item in stops)
    risk_refs = tuple(typing.cast(str, risk.risk_ref) for risk in risks)
    assumption_refs = tuple(
        typing.cast(str, assumption.assumption_ref) for assumption in assumptions
    )
    for collection in (
        work_refs,
        output_refs,
        validation_refs,
        assumption_refs,
        risk_refs,
        prerequisite_refs,
        stop_refs,
    ):
        if len(set(collection)) != len(collection):
            _violate("private_plan_nested_collection_invalid")
    if tuple(typing.cast(int, unit.ordinal) for unit in work_units) != tuple(
        range(len(work_units))
    ):
        _violate("private_plan_nested_collection_invalid")
    if tuple(typing.cast(int, step.ordinal) for step in validations) != tuple(
        range(len(validations))
    ):
        _violate("private_plan_nested_collection_invalid")
    for index, unit in enumerate(work_units):
        dependencies = typing.cast(tuple[str, ...], unit.depends_on_work_unit_refs)
        if any(ref not in work_refs[:index] for ref in dependencies):
            _violate("private_plan_forward_dependency")
        _ordered_unique_refs(dependencies, work_refs[:index], minimum=0)
        ordinals = typing.cast(tuple[int, ...], unit.authorized_path_ordinals)
        if (
            not ordinals
            or tuple(sorted(set(ordinals))) != ordinals
            or any(item >= len(paths) for item in ordinals)
        ):
            _violate("private_plan_nested_collection_invalid")
        _ordered_unique_refs(unit.expected_output_refs, output_refs)
        _ordered_unique_refs(unit.validation_refs, validation_refs)
        _ordered_unique_refs(unit.required_evidence_roles, _EVIDENCE_ROLES)
        _ordered_unique_refs(unit.prerequisite_refs, prerequisite_refs)
        _ordered_unique_refs(unit.stop_condition_refs, stop_refs)
    owners = {
        typing.cast(str, output.output_ref): output.owner_work_unit_ref
        for output in outputs
    }
    if any(output.owner_work_unit_ref not in work_refs for output in outputs):
        _violate("private_plan_nested_collection_invalid")
    if {ref for unit in work_units for ref in unit.expected_output_refs} != set(
        output_refs
    ):
        _violate("private_plan_nested_collection_invalid")
    for unit in work_units:
        if any(owners[ref] != unit.work_unit_ref for ref in unit.expected_output_refs):
            _violate("private_plan_nested_collection_invalid")
    if {ref for unit in work_units for ref in unit.validation_refs} != set(
        validation_refs
    ):
        _violate("private_plan_nested_collection_invalid")
    if {ref for unit in work_units for ref in unit.prerequisite_refs} != set(
        prerequisite_refs
    ):
        _violate("private_plan_prerequisite_unreferenced")
    if {ref for unit in work_units for ref in unit.stop_condition_refs} != set(
        stop_refs
    ):
        _violate("private_plan_stop_unreferenced")
    by_unit = {typing.cast(str, unit.work_unit_ref): unit for unit in work_units}
    by_validation = {
        typing.cast(str, step.validation_ref): step for step in validations
    }
    for unit in work_units:
        if any(
            unit.work_unit_ref not in by_validation[ref].work_unit_refs
            for ref in unit.validation_refs
        ):
            _violate("private_plan_validation_link_asymmetric")
    for step in validations:
        _ordered_unique_refs(step.work_unit_refs, work_refs)
        if any(
            step.validation_ref not in by_unit[ref].validation_refs
            for ref in step.work_unit_refs
        ):
            _violate("private_plan_validation_link_asymmetric")
    for risk in risks:
        _ordered_unique_refs(risk.affected_work_unit_refs, work_refs)
    ranks = tuple(
        _EVIDENCE_ROLES.index(typing.cast(str, item.evidence_role))
        for item in prerequisites
    )
    if tuple(sorted(ranks)) != ranks:
        _violate("private_plan_prerequisite_order_invalid")
    if tuple(sorted(stop_refs)) != stop_refs:
        _violate("private_plan_nested_collection_invalid")
    _require_enum(
        mapping["recommendation"],
        _PRE_EXECUTION_RECOMMENDATIONS,
        "private_plan_closed_vocabulary_invalid",
    )
    _require_reason_code(
        mapping["reason_code"], "private_plan_nested_collection_invalid"
    )
    if len(_canonical_bytes(mapping)) > 65_536:
        _violate("private_plan_artifact_size_invalid")


def _validate_semantic_value(value: _SemanticValue) -> None:
    kind = type(value)
    trusted_kind = _semantic_type_by_identity(kind)
    if trusted_kind is None:
        _violate("invalid_field_type")
    trusted_value_type = typing.cast(type[_SemanticValue], trusted_kind)
    if trusted_kind is PreExecutionPlanningContextV1:
        mapping = {
            name: object.__getattribute__(value, name)
            for name in trusted_value_type._FIELD_ORDER
        }
    else:
        mapping = value.to_mapping()
    if tuple(mapping) != trusted_value_type._FIELD_ORDER:
        _violate("invalid_field_type")
    if trusted_value_type._SCHEMA is not None:
        _require_enum(mapping.get("schema_id"), (trusted_value_type._SCHEMA,))
    if _select_exact_type(
        kind,
        (
            PreExecutionWorkUnitV1,
            PreExecutionExpectedOutputV1,
            PreExecutionValidationStepV1,
            PreExecutionAssumptionV1,
            PreExecutionRiskV1,
            PreExecutionPrerequisiteV1,
            PreExecutionStopConditionV1,
            ProposedResourceAndEffectUseV1,
        ),
    ) is not None:
        _validate_nested(value)
    if kind is ModelConfigurationSafeV1:
        for field_name in _MODEL_CONFIGURATION_FIELDS[1:-1]:
            if field_name == "implementation_family":
                _require_enum(mapping[field_name], ("configured_reasoning_model",))
            elif field_name.endswith("_digest"):
                _require_sha256(mapping[field_name])
            else:
                _require_safe_ref(mapping[field_name])
    elif kind is AuthoritySelectionObservationSafeV1:
        for field_name in _AUTHORITY_OBSERVATION_FIELDS[1:14]:
            if field_name.endswith("_digest"):
                _require_sha256(
                    mapping[field_name], "authority_observation_shape_invalid"
                )
            elif field_name == "authoritative_subject_kind":
                _require_enum(
                    mapping[field_name],
                    ("effect_intent",),
                    "authority_observation_shape_invalid",
                )
            else:
                _require_safe_ref(
                    mapping[field_name], "authority_observation_shape_invalid"
                )
        _require_enum(
            mapping["observation_state"],
            ("pending", "verified"),
            "authority_observation_state_ineligible",
        )
        _require_positive_integer(
            mapping["observation_version"], "authority_observation_version_invalid"
        )
        _require_utc_second(
            mapping["authority_observation_issued_at"],
            "authority_observation_window_invalid",
        )
        _require_utc_second(
            mapping["authority_observation_expires_at"],
            "authority_observation_window_invalid",
        )
        _require_safe_ref(
            mapping["source_authority_ref"], "authority_observation_shape_invalid"
        )
        _require_safe_ref(
            mapping["verification_evidence_ref"], "authority_observation_shape_invalid"
        )
        _require_sha256(
            mapping["verification_evidence_digest"],
            "authority_observation_shape_invalid",
        )
    elif kind is AuthorityExpectedBinding:
        for field_name in _AUTHORITY_EXPECTED_BINDING_FIELDS:
            if field_name.endswith("_digest"):
                _require_sha256(
                    mapping[field_name], "authority_observation_binding_mismatch"
                )
            elif field_name == "authoritative_subject_kind":
                _require_enum(
                    mapping[field_name],
                    ("effect_intent",),
                    "authority_observation_binding_mismatch",
                )
            else:
                _require_safe_ref(
                    mapping[field_name], "authority_observation_binding_mismatch"
                )
    elif kind is PreExecutionPlanningContextV1:
        _validate_context_mapping(mapping)
    elif kind is ModelSourceInvocationV1:
        _validate_source_mapping(mapping)
    elif kind is PrivateProposalArtifactBindingV1:
        _validate_artifact_binding_mapping(mapping)
    elif kind is PreExecutionPlanArtifactV1:
        _validate_artifact(typing.cast(PreExecutionPlanArtifactV1, value))
    elif kind is PreExecutionPlanSafeProjectionV1:
        _validate_projection_mapping(mapping)
    elif kind is ModelProposalEvidenceBindingV1:
        _validate_evidence_binding_mapping(mapping)
    elif kind is ModelProposalEvidenceSetV1:
        _validate_evidence_set(typing.cast(ModelProposalEvidenceSetV1, value))
    elif kind is PreExecutionModelProposalV1:
        _validate_proposal_mapping(mapping)
    elif kind is PreExecutionProposalSelectionBundleV1:
        _validate_bundle(typing.cast(PreExecutionProposalSelectionBundleV1, value))
    if trusted_value_type._DIGEST_FIELD is not None:
        stored = _require_sha256(mapping[trusted_value_type._DIGEST_FIELD])
        if stored != value.computed_digest():
            _violate("digest_mismatch")


def _validate_context_mapping(mapping: dict[str, object]) -> None:
    nullable = {
        "qualified_remote_host_readiness_ref",
        "qualified_remote_host_readiness_digest",
    }
    for name, member in mapping.items():
        if name == "schema_id":
            continue
        if name in nullable:
            (
                _require_optional_sha256
                if name.endswith("_digest")
                else _require_optional_safe_ref
            )(member)
        elif name.endswith("_digest"):
            _require_sha256(member)
        elif name.endswith("_at") or name.endswith("_expires_at"):
            _require_utc_second(member)
        elif name in (
            "program_version_number",
            "attempt_number",
            "authority_observation_version",
        ):
            _require_positive_integer(member)
        elif name.endswith("_version") or name.endswith("_revision"):
            _require_nonnegative_integer(member)
        elif name == "global_stop_state":
            _require_enum(member, ("clear", "active"))
        elif name == "authority_observation_state":
            _require_enum(member, ("pending", "verified"))
        elif name == "authoritative_subject_kind":
            _require_enum(member, ("effect_intent",))
        elif name == "authority_selection_observation_schema_id":
            _require_enum(member, (_SCHEMAS["authority_observation"],))
        elif name == "base_git_object_format":
            _require_enum(member, ("sha1",))
        elif name == "base_git_oid":
            _require_sha1(member)
        elif name == "attempt_fence_allowed_effect_classes_json" or name == (
            "effect_fence_allowed_effect_classes_json"
        ):
            _require_canonical_effect_class_json(member)
        elif name.endswith("_ref"):
            _require_safe_ref(member)
    if (mapping["qualified_remote_host_readiness_ref"] is None) is not (
        mapping["qualified_remote_host_readiness_digest"] is None
    ):
        _violate("physical_family_readiness_mismatch")


def _validate_source_mapping(mapping: dict[str, object]) -> None:
    phase = _require_enum(mapping["proposal_phase"], tuple(_PHASE_SCHEMAS))
    context_schema, artifact_schema, _ = _PHASE_SCHEMAS[phase]
    for name in _SOURCE_INVOCATION_FIELDS[1:]:
        member = mapping[name]
        if name.endswith("_digest"):
            _require_sha256(member)
        elif name.endswith("_at"):
            _require_utc_second(member)
        elif name == "proposal_phase":
            _require_enum(member, (phase,))
        elif name == "invocation_status":
            _require_enum(member, ("normalized_typed_proposal_supplied",))
        elif name == "context_schema_id":
            _require_enum(member, (context_schema,))
        elif name == "artifact_schema_id":
            _require_enum(member, (artifact_schema,))
        else:
            _require_safe_ref(member)


def _validate_artifact_binding_mapping(mapping: dict[str, object]) -> None:
    phase = _require_enum(mapping["proposal_phase"], tuple(_PHASE_SCHEMAS))
    _, artifact_schema, projection_schema = _PHASE_SCHEMAS[phase]
    for name in _ARTIFACT_BINDING_FIELDS[1:]:
        member = mapping[name]
        if name.endswith("_digest"):
            _require_sha256(member)
        elif name == "artifact_canonical_byte_length":
            length = _require_positive_integer(member)
            if length > 65_536:
                _violate("private_plan_artifact_size_invalid")
        elif name == "proposal_phase":
            _require_enum(member, (phase,))
        elif name == "privacy_classification":
            _require_enum(member, ("private_normalized_model_proposal",))
        elif name == "artifact_validated_at":
            _require_utc_second(member)
        elif name == "artifact_schema_id":
            _require_enum(member, (artifact_schema,))
        elif name == "safe_projection_schema_id":
            _require_enum(member, (projection_schema,))
        else:
            _require_safe_ref(member)


def _validate_projection_mapping(mapping: dict[str, object]) -> None:
    count_maxima = {
        "strategy_item_count": 8,
        "work_unit_count": 32,
        "affected_path_count": 64,
        "expected_output_count": 32,
        "validation_step_count": 32,
        "assumption_count": 16,
        "risk_count": 16,
        "prerequisite_count": 32,
        "stop_condition_count": 16,
    }
    for name in _PROJECTION_FIELDS[1:]:
        member = mapping[name]
        if name.endswith("_digest"):
            _require_sha256(member)
        elif name.endswith("_count"):
            value = _require_positive_integer(member)
            if value > count_maxima[name]:
                _violate("safe_projection_derivation_mismatch")
        elif name == "proposal_phase":
            _require_enum(member, ("pre_execution_plan",))
        elif name == "artifact_schema_id":
            _require_enum(member, (_SCHEMAS["artifact"],))
        elif name == "planning_context_schema_id":
            _require_enum(member, (_SCHEMAS["planning_context"],))
        elif name == "allowed_effect_classes":
            _ordered_unique_refs(member, _EFFECT_CLASSES)
        elif name == "recommendation":
            _require_enum(member, _PRE_EXECUTION_RECOMMENDATIONS)
        elif name == "reason_code":
            _require_reason_code(member)
        else:
            _require_safe_ref(member)


def _validate_evidence_binding_mapping(mapping: dict[str, object]) -> None:
    phase = _require_enum(mapping["proposal_phase"], tuple(_PHASE_SCHEMAS))
    roles = ((*_EVIDENCE_ROLES, _READINESS_ROLE)
             if phase == "pre_execution_plan" else _POST_EXECUTION_ROLES)
    role = _require_enum(mapping["evidence_role"], roles)
    expected_rank = 5 + roles.index(role)
    if mapping["role_rank"] != expected_rank or mapping["ordinal"] != 0:
        _violate("preselection_timestamp_record_invalid")
    if type(mapping["required_for_selection"]) is not int or mapping[
        "required_for_selection"
    ] not in (0, 1):
        _violate("preselection_timestamp_record_invalid")
    if bool(mapping["required_for_selection"]) is not (
        phase == "post_execution_semantic_review" or role != _READINESS_ROLE
    ):
        _violate("preselection_timestamp_record_invalid")
    for name in ("proposal_ref", "evidence_set_ref", "evidence_ref"):
        _require_safe_ref(mapping[name])
    for name in ("evidence_digest", "evidence_binding_digest"):
        _require_sha256(mapping[name])
    _require_enum(mapping["proposal_phase"], (phase,))
    _require_utc_second(mapping["evidence_bound_at"])


def _validate_evidence_set(value: ModelProposalEvidenceSetV1) -> None:
    _require_safe_ref(value.evidence_set_ref)
    _require_safe_ref(value.proposal_ref)
    phase = _require_enum(value.proposal_phase, tuple(_PHASE_SCHEMAS))
    raw_entries = _require_tuple_of(
        value.entries, ModelProposalEvidenceBindingV1,
        14 if phase == "pre_execution_plan" else 9,
        15 if phase == "pre_execution_plan" else 9,
    )
    entries = tuple(
        typing.cast(
            ModelProposalEvidenceBindingV1,
            _reconstruct_exact_semantic_value(
                binding, ModelProposalEvidenceBindingV1
            ),
        )
        for binding in raw_entries
    )
    expected = (tuple((*_EVIDENCE_ROLES,
                       *(() if len(entries) == 14 else (_READINESS_ROLE,))))
                if phase == "pre_execution_plan" else _POST_EXECUTION_ROLES)
    if tuple(binding.evidence_role for binding in entries) != expected:
        _violate("preselection_timestamp_record_invalid")
    if any(
        not _exact_equal(binding.proposal_ref, value.proposal_ref)
        or not _exact_equal(binding.evidence_set_ref, value.evidence_set_ref)
        or not _exact_equal(binding.proposal_phase, value.proposal_phase)
        for binding in entries
    ):
        _violate("preselection_timestamp_digest_mismatch")


def _validate_proposal_mapping(mapping: dict[str, object]) -> None:
    phase = _require_enum(mapping["proposal_phase"], tuple(_PHASE_SCHEMAS))
    context_schema, artifact_schema, projection_schema = _PHASE_SCHEMAS[phase]
    for name in _PROPOSAL_FIELDS[1:]:
        member = mapping[name]
        if name.endswith("_digest"):
            _require_sha256(member)
        elif name == "proposal_phase":
            _require_enum(member, (phase,))
        elif name == "recommendation":
            _require_enum(member, (_PRE_EXECUTION_RECOMMENDATIONS
                                  if phase == "pre_execution_plan"
                                  else _POST_EXECUTION_RECOMMENDATIONS))
        elif name == "reason_code":
            _require_reason_code(member)
        elif name == "proposal_created_at":
            _require_utc_second(member)
        elif name == "context_schema_id":
            _require_enum(member, (context_schema,))
        elif name == "artifact_schema_id":
            _require_enum(member, (artifact_schema,))
        elif name == "safe_projection_schema_id":
            _require_enum(member, (projection_schema,))
        else:
            _require_safe_ref(member)


def _validate_bundle(value: PreExecutionProposalSelectionBundleV1) -> None:
    reconstructed: dict[type[object], object] = {}
    for member, expected in (
        (value.authority_observation, AuthoritySelectionObservationSafeV1),
        (value.authority_expected_binding, AuthorityExpectedBinding),
        (value.attempt_fence, AttemptFenceV1),
        (value.effect_fence, EffectFenceV1),
        (value.planning_context, PreExecutionPlanningContextV1),
        (value.source_invocation, ModelSourceInvocationV1),
        (value.private_artifact_binding, PrivateProposalArtifactBindingV1),
        (value.private_artifact, PreExecutionPlanArtifactV1),
        (value.safe_projection, PreExecutionPlanSafeProjectionV1),
        (value.evidence_set, ModelProposalEvidenceSetV1),
        (value.model_proposal, PreExecutionModelProposalV1),
    ):
        if expected is AttemptFenceV1 or expected is EffectFenceV1:
            if type(member) is not expected:
                _violate("invalid_field_type")
            reconstructed[expected] = _reconstruct_exact_fence(member)
        else:
            reconstructed[expected] = _reconstruct_exact_semantic_value(
                member, expected
            )
    raw_bindings = _require_tuple_of(
        value.evidence_bindings, ModelProposalEvidenceBindingV1, 14, 15
    )
    bindings = tuple(
        _reconstruct_exact_semantic_value(binding, ModelProposalEvidenceBindingV1)
        for binding in raw_bindings
    )
    evidence_set = typing.cast(
        ModelProposalEvidenceSetV1,
        reconstructed[ModelProposalEvidenceSetV1],
    )
    if not _exact_equal(
        tuple(binding.to_mapping() for binding in bindings),
        tuple(binding.to_mapping() for binding in evidence_set.entries),
    ):
        _violate("preselection_timestamp_digest_mismatch")


def _derive_pre_execution_safe_projection_mapping(
    artifact: PreExecutionPlanArtifactV1,
    binding: PrivateProposalArtifactBindingV1,
    context: PreExecutionPlanningContextV1,
    proposal: PreExecutionModelProposalV1,
) -> dict[str, object]:
    for value, expected in (
        (artifact, PreExecutionPlanArtifactV1),
        (binding, PrivateProposalArtifactBindingV1),
        (context, PreExecutionPlanningContextV1),
        (proposal, PreExecutionModelProposalV1),
    ):
        _require_type(value, expected)
    mapping = artifact.to_mapping()
    result: dict[str, object] = {
        "schema_id": _SCHEMAS["projection"],
        "proposal_ref": proposal.proposal_ref,
        "proposal_phase": "pre_execution_plan",
        "artifact_schema_id": artifact.schema_id,
        "artifact_ref": artifact.artifact_ref,
        "artifact_digest": artifact.artifact_digest,
        "planning_context_schema_id": context.schema_id,
        "planning_context_ref": context.planning_context_ref,
        "planning_context_digest": context.planning_context_digest,
        "strategy_item_count": len(artifact.implementation_strategy),
        "work_unit_count": len(artifact.proposed_work_units),
        "affected_path_count": len(artifact.affected_authorized_paths),
        "affected_path_set_digest": _domain_separated_digest(
            "governed-execution.nwp-pre-execution-affected-path-set.v1.identity",
            artifact.affected_authorized_paths,
        ),
        "expected_output_count": len(artifact.expected_outputs),
        "expected_output_set_digest": _domain_separated_digest(
            "governed-execution.nwp-pre-execution-expected-output-set.v1.identity",
            tuple(item.to_mapping() for item in artifact.expected_outputs),
        ),
        "validation_step_count": len(artifact.validation_strategy),
        "validation_strategy_digest": _domain_separated_digest(
            "governed-execution.nwp-pre-execution-validation-strategy.v1.identity",
            tuple(item.to_mapping() for item in artifact.validation_strategy),
        ),
        "assumption_count": len(artifact.material_assumptions),
        "assumption_set_digest": _domain_separated_digest(
            "governed-execution.nwp-pre-execution-assumption-set.v1.identity",
            tuple(item.to_mapping() for item in artifact.material_assumptions),
        ),
        "risk_count": len(artifact.risks_and_uncertainties),
        "risk_set_digest": _domain_separated_digest(
            "governed-execution.nwp-pre-execution-risk-set.v1.identity",
            tuple(item.to_mapping() for item in artifact.risks_and_uncertainties),
        ),
        "prerequisite_count": len(artifact.required_evidence_and_prerequisites),
        "prerequisite_set_digest": _domain_separated_digest(
            "governed-execution.nwp-pre-execution-prerequisite-set.v1.identity",
            tuple(
                item.to_mapping()
                for item in artifact.required_evidence_and_prerequisites
            ),
        ),
        "stop_condition_count": len(artifact.stop_or_replan_conditions),
        "stop_condition_set_digest": _domain_separated_digest(
            "governed-execution.nwp-pre-execution-stop-condition-set.v1.identity",
            tuple(item.to_mapping() for item in artifact.stop_or_replan_conditions),
        ),
        "proposed_resource_effect_use_digest": _domain_separated_digest(
            "governed-execution.nwp-pre-execution-resource-effect-use.v1.identity",
            artifact.proposed_resource_and_effect_use.to_mapping(),
        ),
        "allowed_effect_classes": artifact.proposed_resource_and_effect_use.allowed_effect_classes,
        "recommendation": artifact.recommendation,
        "reason_code": artifact.reason_code,
    }
    result["safe_projection_digest"] = _domain_separated_digest(
        _DOMAINS["projection"], result
    )
    return result


def _require_exact_pre_execution_bundle(
    value: object,
) -> PreExecutionProposalSelectionBundleV1:
    return typing.cast(
        PreExecutionProposalSelectionBundleV1,
        _reconstruct_exact_semantic_value(
            value, PreExecutionProposalSelectionBundleV1
        ),
    )
