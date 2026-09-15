"""Private immutable row values for Section 41 cognitive state."""

from __future__ import annotations

from dataclasses import dataclass, make_dataclass
import typing

from ._cognitive_proposal_value_support import (
    _constant_repr,
    _disable_pickle,
    _domain_separated_digest,
    _require_canonical_string,
    _require_canonical_effect_class_json,
    _require_enum,
    _require_exact_mapping,
    _require_nonnegative_integer,
    _require_optional_safe_ref,
    _require_optional_sha256,
    _require_positive_integer,
    _require_reason_code,
    _require_safe_ref,
    _require_sha1,
    _require_sha256,
    _require_utc_second,
    _violate,
    _without_field,
)


__all__ = ()


_TABLE_ORDER = (
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
_TABLE_COLUMNS = {
    _TABLE_ORDER[0]: (
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
    ),
    _TABLE_ORDER[1]: (
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
    ),
    _TABLE_ORDER[2]: (
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
    ),
    _TABLE_ORDER[3]: (
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
    ),
    _TABLE_ORDER[4]: (
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
    ),
    _TABLE_ORDER[5]: (
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
    ),
    _TABLE_ORDER[6]: (
        "schema_id",
        "disposition_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "proposal_ref",
        "proposal_phase",
        "proposal_digest",
        "planning_context_ref",
        "planning_context_digest",
        "evidence_set_ref",
        "evidence_set_digest",
        "semantic_attempt_ref",
        "candidate_ref",
        "effect_intent_ref",
        "author_command_ref",
        "author_command_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
        "delivery_attempt_ref",
        "delivery_envelope_digest",
        "disposition",
        "reason_code",
        "supersedes_disposition_ref",
        "expected_selection_head_revision",
        "expected_selection_head_digest",
        "prior_selection_head_revision",
        "prior_selection_head_digest",
        "resulting_selection_head_revision",
        "selection_head_postimage_digest",
        "authority_selection_observation_ref",
        "authority_selection_observation_digest",
        "coordinator_disposition_decided_at",
        "program_version_number",
        "semantic_attempt_digest",
        "attempt_number",
        "basis_decision_ref",
        "basis_decision_digest",
        "work_spec_ref",
        "work_spec_digest",
        "work_spec_safe_projection_digest",
        "effect_intent_digest",
        "standing_grant_ref",
        "standing_grant_digest",
        "attempt_authorization_ref",
        "attempt_authorization_digest",
        "effect_authorization_ref",
        "effect_authorization_digest",
        "delivery_attempt_digest",
        "authority_evaluation_ref",
        "authority_evaluation_digest",
        "disposition_digest",
    ),
    _TABLE_ORDER[7]: (
        "schema_id",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "candidate_ref",
        "effect_intent_ref",
        "author_command_ref",
        "author_command_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
        "delivery_attempt_ref",
        "delivery_envelope_digest",
        "current_proposal_ref",
        "current_disposition_ref",
        "current_disposition",
        "head_revision",
        "updated_at",
        "program_version_number",
        "semantic_attempt_digest",
        "attempt_number",
        "basis_decision_ref",
        "basis_decision_digest",
        "work_spec_ref",
        "work_spec_digest",
        "work_spec_safe_projection_digest",
        "effect_intent_digest",
        "standing_grant_ref",
        "standing_grant_digest",
        "attempt_authorization_ref",
        "attempt_authorization_digest",
        "effect_authorization_ref",
        "effect_authorization_digest",
        "delivery_attempt_digest",
        "authority_evaluation_ref",
        "authority_evaluation_digest",
        "head_digest",
    ),
    _TABLE_ORDER[8]: (
        "schema_id",
        "mutation_ref",
        "mutation_family",
        "command_schema_id",
        "command_digest",
        "program_ref",
        "proposal_ref",
        "disposition_ref",
        "disposition_digest",
        "authority_selection_observation_ref",
        "authority_selection_observation_digest",
        "effect_intent_ref",
        "selection_head_revision",
        "selection_head_digest",
        "result_class",
        "result_projection_digest",
        "mutation_graph_digest",
        "outcome",
        "committed_at",
        "receipt_digest",
    ),
}
_TABLE_SCHEMAS = {
    _TABLE_ORDER[0]: "governed-execution.nwp-model-source-invocation.v1",
    _TABLE_ORDER[1]: "governed-execution.nwp-pre-execution-planning-context.v1",
    _TABLE_ORDER[2]: "governed-execution.nwp-private-proposal-artifact-binding.v1",
    _TABLE_ORDER[3]: "governed-execution.nwp-model-proposal-envelope.v1",
    _TABLE_ORDER[4]: "governed-execution.nwp-pre-execution-plan-safe-projection.v1",
    _TABLE_ORDER[5]: "governed-execution.nwp-model-proposal-evidence-binding.v1",
    _TABLE_ORDER[6]: "governed-execution.nwp-pre-execution-coordinator-disposition.v1",
    _TABLE_ORDER[7]: "governed-execution.nwp-pre-execution-selection-head.v1",
    _TABLE_ORDER[8]: "governed-execution.nwp-cognitive-mutation-receipt.v1",
}
_DIGEST_FIELDS = {
    _TABLE_ORDER[0]: "source_invocation_digest",
    _TABLE_ORDER[1]: "planning_context_digest",
    _TABLE_ORDER[2]: "artifact_binding_digest",
    _TABLE_ORDER[3]: "proposal_digest",
    _TABLE_ORDER[4]: "safe_projection_digest",
    _TABLE_ORDER[5]: "evidence_binding_digest",
    _TABLE_ORDER[6]: "disposition_digest",
    _TABLE_ORDER[7]: "head_digest",
    _TABLE_ORDER[8]: "receipt_digest",
}
_DOMAINS = {table: _TABLE_SCHEMAS[table] + ".identity" for table in _TABLE_ORDER}
_CLASS_TABLES: tuple[tuple[type[object], str], ...] = ()


def _row_registration_for_exact_type(
    candidate_type: object,
) -> tuple[type[object], str] | None:
    for trusted_type, table in _CLASS_TABLES:
        if candidate_type is trusted_type:
            return trusted_type, table
    return None


def _reject_concrete_subclass(cls: type[object], **kwargs: object) -> typing.NoReturn:
    raise TypeError("subclassing disabled")

_PRE_PHASE = "pre_execution_plan"
_POST_PHASE = "post_execution_semantic_review"
_PRE_CONTEXT_SCHEMA = "governed-execution.nwp-pre-execution-planning-context.v1"
_POST_CONTEXT_SCHEMA = (
    "governed-execution.nwp-post-execution-semantic-review-context.v1"
)
_PRE_ARTIFACT_SCHEMA = "governed-execution.nwp-pre-execution-plan-artifact.v1"
_POST_ARTIFACT_SCHEMA = (
    "governed-execution.nwp-post-execution-semantic-review-artifact.v1"
)
_PRE_PROJECTION_SCHEMA = "governed-execution.nwp-pre-execution-plan-safe-projection.v1"
_POST_PROJECTION_SCHEMA = (
    "governed-execution.nwp-post-execution-semantic-review-safe-projection.v1"
)
_AUTHORITY_OBSERVATION_SCHEMA = (
    "governed-execution.nwp-authority-observation-attestation-safe.v1"
)
_COMMAND_SCHEMA = (
    "governed-execution.nwp-record-pre-execution-plan-disposition-command.v1"
)
_PRE_RECOMMENDATIONS = (
    "select_for_dispatch_gates",
    "defer",
    "block",
    "replan",
    "terminal_reject",
)
_POST_RECOMMENDATIONS = (
    "accept_candidate",
    "repair_candidate",
    "replan",
    "terminal_reject",
    "block",
)
_DISPOSITIONS = ("selected_for_dispatch_gates", "deferred", "blocked")
_PRE_EVIDENCE = (
    ("standing_policy", 5, 1),
    ("risk_lane", 6, 1),
    ("repository_binding", 7, 1),
    ("base_binding", 8, 1),
    ("authorized_path_scope", 9, 1),
    ("cost_ceiling", 10, 1),
    ("token_ceiling", 11, 1),
    ("time_ceiling", 12, 1),
    ("delivery_ceiling", 13, 1),
    ("effect_ceiling", 14, 1),
    ("authority_selection_observation", 15, 1),
    ("global_stop", 16, 1),
    ("validation_requirement", 17, 1),
    ("review_requirement", 18, 1),
    ("qualified_remote_host_readiness", 19, 0),
)
_POST_EVIDENCE = (
    ("candidate_capsule", 5, 1),
    ("worker_result", 6, 1),
    ("validation_result", 7, 1),
    ("independent_review", 8, 1),
    ("standing_policy", 9, 1),
    ("risk_lane", 10, 1),
    ("authority_currentness_attestation", 11, 1),
    ("global_stop", 12, 1),
    ("effect_ceiling", 13, 1),
)
_COUNT_MAXIMA = {
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


class _CognitiveRowValue:
    __slots__ = ()
    __hash__ = None
    _TABLE = ""
    _COLUMNS: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_row(self)

    def to_mapping(self) -> dict[str, object]:
        return {name: object.__getattribute__(self, name) for name in self._COLUMNS}

    identity_mapping = to_mapping

    def computed_digest(self) -> str:
        mapping = self.to_mapping()
        if self._TABLE == "development_pre_execution_plan_projections":
            mapping["allowed_effect_classes"] = _require_canonical_effect_class_json(
                mapping["allowed_effect_classes"],
                "physical_family_row_digest_mismatch",
            )
        return _domain_separated_digest(
            _DOMAINS[self._TABLE],
            _without_field(mapping, _DIGEST_FIELDS[self._TABLE]),
        )

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> None:
        if cls.__module__ != __name__:
            raise TypeError("subclassing disabled")


def _make_row_class(name: str, table: str) -> type[_CognitiveRowValue]:
    global _CLASS_TABLES

    result = typing.cast(
        type[_CognitiveRowValue],
        make_dataclass(
            name,
            [(column, object) for column in _TABLE_COLUMNS[table]],
            bases=(_CognitiveRowValue,),
            namespace={
                "__module__": __name__,
                "_TABLE": table,
                "_COLUMNS": _TABLE_COLUMNS[table],
                "__init_subclass__": _reject_concrete_subclass,
            },
            frozen=True,
            slots=True,
            repr=False,
        ),
    )
    _CLASS_TABLES = (*_CLASS_TABLES, (result, table))
    return result


DevelopmentModelSourceInvocationRowValue = _make_row_class(
    "DevelopmentModelSourceInvocationRowValue", _TABLE_ORDER[0]
)
DevelopmentPreExecutionPlanningContextRowValue = _make_row_class(
    "DevelopmentPreExecutionPlanningContextRowValue", _TABLE_ORDER[1]
)
DevelopmentPrivateProposalArtifactBindingRowValue = _make_row_class(
    "DevelopmentPrivateProposalArtifactBindingRowValue", _TABLE_ORDER[2]
)
DevelopmentModelProposalRowValue = _make_row_class(
    "DevelopmentModelProposalRowValue", _TABLE_ORDER[3]
)
DevelopmentPreExecutionPlanProjectionRowValue = _make_row_class(
    "DevelopmentPreExecutionPlanProjectionRowValue", _TABLE_ORDER[4]
)
DevelopmentModelProposalEvidenceBindingRowValue = _make_row_class(
    "DevelopmentModelProposalEvidenceBindingRowValue", _TABLE_ORDER[5]
)
DevelopmentPreExecutionDispositionRowValue = _make_row_class(
    "DevelopmentPreExecutionDispositionRowValue", _TABLE_ORDER[6]
)
DevelopmentPreExecutionSelectionHeadRowValue = _make_row_class(
    "DevelopmentPreExecutionSelectionHeadRowValue", _TABLE_ORDER[7]
)
DevelopmentCognitiveMutationReceiptRowValue = _make_row_class(
    "DevelopmentCognitiveMutationReceiptRowValue", _TABLE_ORDER[8]
)


_ROLE_INVENTORY = (
    ("source_invocation", 0, _TABLE_ORDER[0]),
    ("planning_context", 1, _TABLE_ORDER[1]),
    ("private_artifact_binding", 2, _TABLE_ORDER[2]),
    ("model_proposal", 3, _TABLE_ORDER[3]),
    ("pre_execution_plan_projection", 4, _TABLE_ORDER[4]),
    ("evidence.standing_policy", 5, _TABLE_ORDER[5]),
    ("evidence.risk_lane", 6, _TABLE_ORDER[5]),
    ("evidence.repository_binding", 7, _TABLE_ORDER[5]),
    ("evidence.base_binding", 8, _TABLE_ORDER[5]),
    ("evidence.authorized_path_scope", 9, _TABLE_ORDER[5]),
    ("evidence.cost_ceiling", 10, _TABLE_ORDER[5]),
    ("evidence.token_ceiling", 11, _TABLE_ORDER[5]),
    ("evidence.time_ceiling", 12, _TABLE_ORDER[5]),
    ("evidence.delivery_ceiling", 13, _TABLE_ORDER[5]),
    ("evidence.effect_ceiling", 14, _TABLE_ORDER[5]),
    ("evidence.authority_selection_observation", 15, _TABLE_ORDER[5]),
    ("evidence.global_stop", 16, _TABLE_ORDER[5]),
    ("evidence.validation_requirement", 17, _TABLE_ORDER[5]),
    ("evidence.review_requirement", 18, _TABLE_ORDER[5]),
    ("evidence.qualified_remote_host_readiness", 19, _TABLE_ORDER[5]),
    ("coordinator_disposition", 20, _TABLE_ORDER[6]),
    ("selection_head_postimage", 21, _TABLE_ORDER[7]),
)


@dataclass(frozen=True, slots=True, repr=False)
class CanonicalCognitivePhysicalRow:
    table: str
    role: str
    rank: int | None
    ordinal: int
    values: _CognitiveRowValue

    __init_subclass__ = _reject_concrete_subclass

    def __post_init__(self) -> None:
        checked_table = _require_enum(
            self.table, _TABLE_ORDER, "physical_family_row_digest_mismatch"
        )
        _require_canonical_string(
            self.role, reason="physical_family_row_digest_mismatch"
        )
        if type(self.ordinal) is not int or self.ordinal != 0:
            _violate("physical_family_order_mismatch")
        registration = _row_registration_for_exact_type(type(self.values))
        if registration is None or registration[1] != checked_table:
            _violate("physical_family_row_digest_mismatch")
        checked_values = _require_exact_row_value(self.values)
        if self.rank is None:
            if self.table != _TABLE_ORDER[8] or self.role != "receipt":
                _violate("physical_family_receipt_in_graph")
        elif (
            type(self.rank) is not int
            or (self.role, self.rank, self.table) not in _ROLE_INVENTORY
        ):
            _violate("physical_family_order_mismatch")
        object.__setattr__(self, "values", checked_values)

    def locator(self) -> tuple[tuple[str, object], ...]:
        mapping = self.values.to_mapping()
        if self.table == _TABLE_ORDER[5]:
            names = ("proposal_ref", "evidence_role", "ordinal")
        elif self.table == _TABLE_ORDER[7]:
            names = (
                "program_ref",
                "semantic_attempt_ref",
                "candidate_ref",
                "effect_intent_ref",
                "author_command_ref",
                "attempt_fence_ref",
                "effect_fence_ref",
                "delivery_attempt_ref",
            )
        else:
            names = {
                _TABLE_ORDER[0]: ("source_invocation_ref",),
                _TABLE_ORDER[1]: ("planning_context_ref",),
                _TABLE_ORDER[2]: ("artifact_ref",),
                _TABLE_ORDER[3]: ("proposal_ref",),
                _TABLE_ORDER[4]: ("proposal_ref",),
                _TABLE_ORDER[6]: ("disposition_ref",),
                _TABLE_ORDER[8]: ("mutation_ref",),
            }[self.table]
        return tuple((name, mapping[name]) for name in names)

    @property
    def member_digest(self) -> str:
        return typing.cast(str, self.values.to_mapping()[_DIGEST_FIELDS[self.table]])

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle


def _validate_row(value: _CognitiveRowValue) -> None:
    registration = _row_registration_for_exact_type(type(value))
    if registration is None:
        _violate("physical_family_row_digest_mismatch")
    mapping = value.to_mapping()
    table = registration[1]
    if tuple(mapping) != _TABLE_COLUMNS[table]:
        _violate("physical_family_row_digest_mismatch")
    _require_enum(
        mapping["schema_id"],
        (_TABLE_SCHEMAS[table],),
        "physical_family_row_digest_mismatch",
    )
    nullable_names = {
        "supersedes_disposition_ref",
        "expected_selection_head_revision",
        "expected_selection_head_digest",
        "prior_selection_head_digest",
        "qualified_remote_host_readiness_ref",
        "qualified_remote_host_readiness_digest",
    }
    integer_names = {
        "program_version_number",
        "attempt_number",
        "expected_program_head_revision",
        "expected_work_item_head_revision",
        "expected_effect_head_revision",
        "expected_delivery_head_revision",
        "global_stop_version",
        "authority_observation_version",
        "artifact_canonical_byte_length",
        "strategy_item_count",
        "work_unit_count",
        "affected_path_count",
        "expected_output_count",
        "validation_step_count",
        "assumption_count",
        "risk_count",
        "prerequisite_count",
        "stop_condition_count",
        "role_rank",
        "ordinal",
        "required_for_selection",
        "expected_selection_head_revision",
        "prior_selection_head_revision",
        "resulting_selection_head_revision",
        "head_revision",
        "selection_head_revision",
    }
    time_names = {
        "source_invocation_started_at",
        "source_invocation_completed_at",
        "attempt_fence_expires_at",
        "effect_fence_expires_at",
        "authority_observation_issued_at",
        "authority_observation_expires_at",
        "planning_context_captured_at",
        "artifact_validated_at",
        "proposal_created_at",
        "evidence_bound_at",
        "coordinator_disposition_decided_at",
        "updated_at",
        "committed_at",
    }
    vocabulary_names = {
        "proposal_phase",
        "invocation_status",
        "privacy_classification",
        "recommendation",
        "evidence_role",
        "disposition",
        "current_disposition",
        "mutation_family",
        "result_class",
        "outcome",
        "global_stop_state",
        "authoritative_subject_kind",
        "authority_observation_state",
        "base_git_object_format",
        "context_schema_id",
        "artifact_schema_id",
        "safe_projection_schema_id",
        "planning_context_schema_id",
        "authority_selection_observation_schema_id",
        "command_schema_id",
    }
    positive_names = {
        "program_version_number",
        "attempt_number",
        "authority_observation_version",
    }
    for name, member in mapping.items():
        if name == "schema_id":
            continue
        if name in nullable_names and member is None:
            continue
        if name.endswith("_digest"):
            _require_sha256(member, "physical_family_row_digest_mismatch")
        elif name in time_names:
            _require_utc_second(member, "physical_family_row_digest_mismatch")
        elif name in integer_names:
            if name == "prior_selection_head_revision":
                if type(member) is not int or member < -1:
                    _violate("physical_family_row_digest_mismatch")
            elif name in positive_names:
                _require_positive_integer(member, "physical_family_row_digest_mismatch")
            elif name == "artifact_canonical_byte_length":
                if (
                    not 1
                    <= _require_positive_integer(
                        member, "physical_family_row_digest_mismatch"
                    )
                    <= 65_536
                ):
                    _violate("physical_family_row_digest_mismatch")
            elif name in _COUNT_MAXIMA:
                if (
                    not 1
                    <= _require_positive_integer(
                        member, "physical_family_row_digest_mismatch"
                    )
                    <= _COUNT_MAXIMA[name]
                ):
                    _violate("physical_family_row_digest_mismatch")
            else:
                _require_nonnegative_integer(
                    member, "physical_family_row_digest_mismatch"
                )
        elif name == "base_git_oid":
            _require_sha1(member, "physical_family_row_digest_mismatch")
        elif name == "allowed_effect_classes" or name.endswith("_json"):
            _require_canonical_effect_class_json(
                member, "physical_family_row_digest_mismatch"
            )
        elif name == "reason_code":
            _require_reason_code(member, "physical_family_row_digest_mismatch")
        elif name.endswith("_ref"):
            _require_safe_ref(member, "physical_family_row_digest_mismatch")
        elif name in vocabulary_names:
            _require_canonical_string(
                member, reason="physical_family_row_digest_mismatch"
            )

    if table == _TABLE_ORDER[0]:
        phase = _require_enum(
            mapping["proposal_phase"],
            (_PRE_PHASE, _POST_PHASE),
            "physical_family_row_digest_mismatch",
        )
        expected = (
            (_PRE_CONTEXT_SCHEMA, _PRE_ARTIFACT_SCHEMA)
            if phase == _PRE_PHASE
            else (_POST_CONTEXT_SCHEMA, _POST_ARTIFACT_SCHEMA)
        )
        _require_enum(
            mapping["context_schema_id"],
            (expected[0],),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["artifact_schema_id"],
            (expected[1],),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["invocation_status"],
            ("normalized_typed_proposal_supplied",),
            "physical_family_row_digest_mismatch",
        )
    elif table == _TABLE_ORDER[1]:
        _require_enum(
            mapping["global_stop_state"],
            ("clear", "active"),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["authoritative_subject_kind"],
            ("effect_intent",),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["authority_observation_state"],
            ("pending", "verified"),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["authority_selection_observation_schema_id"],
            (_AUTHORITY_OBSERVATION_SCHEMA,),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["base_git_object_format"],
            ("sha1",),
            "physical_family_row_digest_mismatch",
        )
        if (mapping["qualified_remote_host_readiness_ref"] is None) is not (
            mapping["qualified_remote_host_readiness_digest"] is None
        ):
            _violate("physical_family_row_digest_mismatch")
    elif table == _TABLE_ORDER[2]:
        phase = _require_enum(
            mapping["proposal_phase"],
            (_PRE_PHASE, _POST_PHASE),
            "physical_family_row_digest_mismatch",
        )
        expected = (
            (_PRE_ARTIFACT_SCHEMA, _PRE_PROJECTION_SCHEMA)
            if phase == _PRE_PHASE
            else (_POST_ARTIFACT_SCHEMA, _POST_PROJECTION_SCHEMA)
        )
        _require_enum(
            mapping["artifact_schema_id"],
            (expected[0],),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["safe_projection_schema_id"],
            (expected[1],),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["privacy_classification"],
            ("private_normalized_model_proposal",),
            "physical_family_row_digest_mismatch",
        )
    elif table == _TABLE_ORDER[3]:
        phase = _require_enum(
            mapping["proposal_phase"],
            (_PRE_PHASE, _POST_PHASE),
            "physical_family_row_digest_mismatch",
        )
        if phase == _PRE_PHASE:
            expected = (
                _PRE_CONTEXT_SCHEMA,
                _PRE_ARTIFACT_SCHEMA,
                _PRE_PROJECTION_SCHEMA,
            )
            recommendations = _PRE_RECOMMENDATIONS
        else:
            expected = (
                _POST_CONTEXT_SCHEMA,
                _POST_ARTIFACT_SCHEMA,
                _POST_PROJECTION_SCHEMA,
            )
            recommendations = _POST_RECOMMENDATIONS
        _require_enum(
            mapping["context_schema_id"],
            (expected[0],),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["artifact_schema_id"],
            (expected[1],),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["safe_projection_schema_id"],
            (expected[2],),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["recommendation"],
            recommendations,
            "physical_family_row_digest_mismatch",
        )
    elif table == _TABLE_ORDER[4]:
        _require_enum(
            mapping["proposal_phase"],
            (_PRE_PHASE,),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["artifact_schema_id"],
            (_PRE_ARTIFACT_SCHEMA,),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["planning_context_schema_id"],
            (_PRE_CONTEXT_SCHEMA,),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["recommendation"],
            _PRE_RECOMMENDATIONS,
            "physical_family_row_digest_mismatch",
        )
    elif table == _TABLE_ORDER[5]:
        phase = _require_enum(
            mapping["proposal_phase"],
            (_PRE_PHASE, _POST_PHASE),
            "physical_family_row_digest_mismatch",
        )
        inventory = _PRE_EVIDENCE if phase == _PRE_PHASE else _POST_EVIDENCE
        role = _require_enum(
            mapping["evidence_role"],
            tuple(item[0] for item in inventory),
            "physical_family_row_digest_mismatch",
        )
        expected = next(item for item in inventory if item[0] == role)
        if (
            mapping["role_rank"] != expected[1]
            or mapping["ordinal"] != 0
            or mapping["required_for_selection"] != expected[2]
        ):
            _violate("physical_family_row_digest_mismatch")
    elif table == _TABLE_ORDER[6]:
        _require_enum(
            mapping["proposal_phase"],
            (_PRE_PHASE,),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["disposition"], _DISPOSITIONS, "physical_family_row_digest_mismatch"
        )
        if mapping["disposition_ref"] == mapping["proposal_ref"]:
            _violate("proposal_disposition_identity_collapse")
        root = mapping["resulting_selection_head_revision"] == 0
        if root:
            if not (
                mapping["prior_selection_head_revision"] == -1
                and mapping["supersedes_disposition_ref"] is None
                and mapping["prior_selection_head_digest"] is None
                and mapping["expected_selection_head_revision"] is None
                and mapping["expected_selection_head_digest"] is None
            ):
                _violate("physical_family_row_digest_mismatch")
        elif not (
            mapping["prior_selection_head_revision"]
            == mapping["resulting_selection_head_revision"] - 1
            and mapping["supersedes_disposition_ref"] is not None
            and mapping["prior_selection_head_digest"] is not None
            and mapping["expected_selection_head_revision"]
            == mapping["prior_selection_head_revision"]
            and mapping["expected_selection_head_digest"]
            == mapping["prior_selection_head_digest"]
        ):
            _violate("physical_family_row_digest_mismatch")
    elif table == _TABLE_ORDER[7]:
        _require_enum(
            mapping["current_disposition"],
            _DISPOSITIONS,
            "physical_family_row_digest_mismatch",
        )
    elif table == _TABLE_ORDER[8]:
        _require_enum(
            mapping["mutation_family"],
            ("record_pre_execution_plan_disposition",),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["command_schema_id"],
            (_COMMAND_SCHEMA,),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["result_class"],
            ("pre_execution_plan_disposition_recorded",),
            "physical_family_row_digest_mismatch",
        )
        _require_enum(
            mapping["outcome"], ("committed",), "physical_family_row_digest_mismatch"
        )
    if mapping[_DIGEST_FIELDS[table]] != value.computed_digest():
        _violate("physical_family_row_digest_mismatch")


def _row_value_from_mapping(table: str, mapping: object) -> _CognitiveRowValue:
    checked_table = _require_enum(
        table, _TABLE_ORDER, "physical_family_row_digest_mismatch"
    )
    checked_mapping = _require_exact_mapping(
        mapping,
        _TABLE_COLUMNS[checked_table],
        "physical_family_row_digest_mismatch",
    )
    row_class: type[object] | None = None
    for trusted_type, owned_table in _CLASS_TABLES:
        if owned_table == checked_table:
            row_class = trusted_type
            break
    if row_class is None:
        _violate("physical_family_row_digest_mismatch")
    return typing.cast(_CognitiveRowValue, row_class(**checked_mapping))


def _require_exact_row_value(value: object) -> _CognitiveRowValue:
    row_type = type(value)
    registration = _row_registration_for_exact_type(row_type)
    if registration is None:
        _violate("physical_family_row_digest_mismatch")
    trusted_type, table = registration
    mapping: dict[str, object] = {}
    missing = False
    for name in _TABLE_COLUMNS[table]:
        try:
            member = object.__getattribute__(value, name)
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception:
            missing = True
            break
        member_type = type(member)
        if (
            member_type is not str
            and member_type is not int
            and member_type is not bool
            and member_type is not type(None)
        ):
            _violate("physical_family_row_digest_mismatch")
        mapping[name] = member
    if missing:
        _violate("physical_family_row_digest_mismatch")
    reconstructed = _row_value_from_mapping(table, mapping)
    if type(reconstructed) is not trusted_type:
        _violate("physical_family_row_digest_mismatch")
    return reconstructed


def _require_exact_physical_row(value: object) -> CanonicalCognitivePhysicalRow:
    if type(value) is not CanonicalCognitivePhysicalRow:
        _violate("physical_family_row_digest_mismatch")
    try:
        table = object.__getattribute__(value, "table")
        role = object.__getattribute__(value, "role")
        rank = object.__getattribute__(value, "rank")
        ordinal = object.__getattribute__(value, "ordinal")
        row_value = object.__getattribute__(value, "values")
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        _violate("physical_family_row_digest_mismatch")
    return CanonicalCognitivePhysicalRow(
        table=table,
        role=role,
        rank=rank,
        ordinal=ordinal,
        values=_require_exact_row_value(row_value),
    )


def _row_value_from_tuple(table: str, row: object) -> _CognitiveRowValue:
    checked_table = _require_enum(
        table, _TABLE_ORDER, "physical_family_row_digest_mismatch"
    )
    if type(row) is not tuple or len(row) != len(_TABLE_COLUMNS[checked_table]):
        _violate("physical_family_row_digest_mismatch")
    mapping = dict(
        zip(
            _TABLE_COLUMNS[checked_table],
            typing.cast(tuple[object, ...], row),
            strict=True,
        )
    )
    return _row_value_from_mapping(checked_table, mapping)
