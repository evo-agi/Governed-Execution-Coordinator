"""Private no-I/O RW0-C1 durable row contracts.

Ordered column tuples are the single source of row shape used by migration
tests, literal readers, write plans, and readback.  The values are deliberately
generic and content-free at their representation boundary; semantic ownership
remains with the existing B1/B2/C2A/Section 41 modules.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import hashlib
import json
import re
import typing

__all__: tuple[str, ...] = ()


_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


PHASE_COLUMNS = (
    "schema_id", "phase_basis_schema_id", "phase_basis_ref", "program_ref",
    "program_version_ref", "program_version_number", "accepted_intent_revision_ref",
    "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
    "semantic_attempt_digest", "attempt_number", "candidate_ref",
    "basis_decision_ref", "basis_decision_digest", "work_spec_ref",
    "work_spec_digest", "work_spec_safe_projection_digest", "effect_intent_ref",
    "effect_intent_digest", "author_command_ref", "author_command_digest",
    "standing_grant_ref", "standing_grant_digest", "attempt_authorization_ref",
    "attempt_authorization_digest", "effect_authorization_ref",
    "effect_authorization_digest", "attempt_fence_ref", "attempt_fence_digest",
    "effect_fence_ref", "effect_fence_digest", "delivery_attempt_ref",
    "delivery_envelope_digest", "delivery_attempt_digest", "authority_evaluation_ref",
    "authority_evaluation_digest", "selected_proposal_ref", "selected_proposal_digest",
    "selected_artifact_ref", "selected_artifact_digest",
    "selected_artifact_binding_digest", "selected_plan_safe_projection_digest",
    "disposition_ref", "disposition_digest", "disposition",
    "selection_head_revision", "selection_head_digest", "current_effect_head_revision",
    "current_effect_head_state", "current_effect_head_digest",
    "current_delivery_head_revision", "current_delivery_head_state",
    "current_delivery_head_digest", "global_stop_ref", "global_stop_version",
    "global_stop_state", "path_scope_digest", "phase_basis_digest", "k8_digest",
    "expected_program_head_revision", "expected_program_head_digest",
    "expected_work_item_head_revision", "expected_work_item_head_digest",
    "selection_head_updated_at", "current_effect_head_fence_ref",
    "current_effect_head_cancellation_effect_intent_ref",
    "current_effect_head_updated_at", "current_delivery_head_attempt_ref",
    "current_delivery_head_updated_at", "establishment_mutation_ref", "established_at",
    "relation_count", "relation_set_digest", "phase_graph_digest", "phase_row_digest",
)

EVIDENCE_VALUE_COLUMNS = (
    "schema_id", "kind_rank", "value_ref", "value_digest", "value_schema_id",
    "scope_class", "value_row_digest",
)

MEMBERSHIP_COLUMNS = (
    "schema_id", "membership_ref", "membership_digest", "phase_basis_ref",
    "phase_basis_digest", "kind_rank", "value_ref", "value_digest",
    "value_schema_id", "scope_binding_digest", "relation_set_digest",
    "admitted_by_mutation_ref", "admitted_at", "admission_graph_digest",
)

RELATION_COLUMNS = (
    "schema_id", "phase_basis_ref", "phase_basis_digest", "relation_ref",
    "relation_digest", "subject_type", "subject_membership_ref",
    "subject_membership_digest", "subject_kind_rank", "subject_value_ref",
    "subject_value_digest", "subject_value_schema_id", "relation_rank",
    "relation_schema_id", "relation_version", "proof_mode", "profile_ref",
    "profile_digest", "evaluated_at", "operand_count", "operand_set_digest",
    "relation_row_digest",
)

OPERAND_COLUMNS = (
    "schema_id", "phase_basis_ref", "relation_ref", "relation_digest",
    "operand_ordinal", "operand_role", "operand_source", "source_membership_ref",
    "source_membership_digest", "source_kind_rank", "owner_role",
    "owner_locator_ref", "owner_locator_revision", "owner_locator_subrole",
    "owner_locator_ordinal", "transient_binding_kind", "transient_error_reason",
    "snapshot_binding_kind", "operand_schema_id", "operand_ref", "operand_digest",
    "operand_scope_digest", "operand_row_digest",
)

RECEIPT_COLUMNS = (
    "schema_id", "mutation_ref", "mutation_family", "command_schema_id",
    "command_digest", "phase_basis_ref", "phase_basis_digest", "membership_ref",
    "membership_digest", "kind_rank", "value_ref", "value_digest",
    "value_schema_id", "result_class", "result_projection_digest",
    "admission_graph_digest", "outcome", "committed_at", "receipt_digest",
)

_TYPED_PREFIX = ("schema_id", "kind_rank", "value_ref", "value_digest", "value_schema_id")

AUTHORITY_OBSERVATION_COLUMNS = _TYPED_PREFIX + (
    "source_ref", "evidence_ref", "evidence_digest", "phase_basis_ref",
    "phase_basis_digest", "parent_grant_ref", "parent_grant_digest",
    "grant_family_ref", "grant_family_digest", "attempt_basis_ref",
    "attempt_basis_digest", "effect_basis_ref", "effect_basis_digest",
    "attempt_fence_ref", "attempt_fence_digest", "effect_fence_ref",
    "effect_fence_digest", "audience_ref", "repository_ref",
    "base_git_object_format", "base_git_oid", "path_scope_digest",
    "allowed_effect_class_count", "max_active_invocations", "max_candidate_bytes",
    "max_changed_files", "max_cost_microusd", "max_cpu_seconds", "max_deliveries",
    "max_deployments", "max_local_commits", "max_memory_bytes", "max_merges",
    "max_model_input_tokens", "max_model_output_tokens", "max_pull_requests",
    "max_pushes", "max_wall_seconds", "effect_class", "status", "family_status",
    "revocation_status", "grant_expires_at", "observed_at", "observation_expires_at",
    "current_effect_head_digest", "current_delivery_head_digest", "global_stop_ref",
    "global_stop_version", "global_stop_state", "payload_row_digest",
)

SUBORDINATE_PROPOSAL_COLUMNS = _TYPED_PREFIX + (
    "phase_basis_ref", "phase_basis_digest", "verification_ref", "verification_digest",
    "parent_grant_ref", "parent_grant_digest", "grant_family_ref",
    "grant_family_digest", "attempt_basis_ref", "attempt_basis_digest",
    "effect_basis_ref", "effect_basis_digest", "attempt_fence_ref",
    "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest",
    "audience_ref", "repository_ref", "base_git_object_format", "base_git_oid",
    "path_scope_digest", "effect_class", "max_active_invocations",
    "max_candidate_bytes", "max_changed_files", "max_cost_microusd",
    "max_cpu_seconds", "max_deliveries", "max_deployments", "max_local_commits",
    "max_memory_bytes", "max_merges", "max_model_input_tokens",
    "max_model_output_tokens", "max_pull_requests", "max_pushes", "max_wall_seconds",
    "expires_at", "global_stop_ref", "global_stop_version", "payload_row_digest",
)

CUSTODY_OBSERVATION_COLUMNS = _TYPED_PREFIX + (
    "source_ref", "evidence_ref", "evidence_digest", "phase_basis_ref",
    "phase_basis_digest", "subject_kind", "subject_ref", "subject_semantic_digest",
    "content_sha256", "byte_length", "availability", "observed_at", "expires_at",
    "payload_row_digest",
)

RETRIEVAL_EVENT_COLUMNS = _TYPED_PREFIX + (
    "source_ref", "evidence_ref", "evidence_digest", "phase_basis_ref",
    "phase_basis_digest", "safe_correlation_ref", "subject_kind", "subject_ref",
    "subject_semantic_digest", "content_sha256", "byte_length", "semantic_attempt_ref",
    "attempt_fence_ref", "attempt_fence_digest", "effect_intent_ref",
    "effect_fence_ref", "effect_fence_digest", "audience_ref", "repository_ref",
    "base_git_object_format", "base_git_oid", "path_scope_digest",
    "authority_observation_ref", "authority_observation_digest",
    "subordinate_proposal_ref", "subordinate_proposal_digest",
    "custody_observation_ref", "custody_observation_digest", "event_kind",
    "predecessor_event_ref", "predecessor_event_digest", "sequence_number",
    "occurred_at", "expires_at", "payload_row_digest",
)

READINESS_OBSERVATION_COLUMNS = _TYPED_PREFIX + (
    "source_ref", "evidence_ref", "evidence_digest", "safe_host_correlation_ref",
    "status", "platform", "platform_profile_ref", "platform_profile_digest",
    "architecture_profile_ref", "architecture_profile_digest", "worker_artifact_ref",
    "worker_artifact_digest", "worker_protocol_ref", "worker_protocol_digest",
    "execution_identity_profile_ref", "execution_identity_profile_digest",
    "process_profile_ref", "process_profile_digest", "isolation_profile_ref",
    "isolation_profile_digest", "resource_profile_ref", "resource_profile_digest",
    "cancellation_profile_ref", "cancellation_profile_digest",
    "credential_handoff_profile_ref", "credential_handoff_profile_digest",
    "capsule_store_profile_ref", "capsule_store_profile_digest",
    "validation_tool_profile_ref", "validation_tool_profile_digest",
    "review_tool_profile_ref", "review_tool_profile_digest", "cleanup_profile_ref",
    "cleanup_profile_digest", "observed_at", "expires_at", "payload_row_digest",
)

HOST_QUALIFICATION_COLUMNS = _TYPED_PREFIX + (
    "phase_basis_ref", "phase_basis_digest", "effect_intent_ref", "effect_fence_ref",
    "effect_fence_digest", "verification_ref", "verification_digest", "readiness_ref",
    "readiness_digest", "required_scenario_profile_ref",
    "required_scenario_profile_digest", "required_platform_profile_ref",
    "required_platform_profile_digest", "required_architecture_profile_ref",
    "required_architecture_profile_digest", "required_worker_artifact_ref",
    "required_worker_artifact_digest", "required_worker_protocol_ref",
    "required_worker_protocol_digest", "required_execution_identity_profile_ref",
    "required_execution_identity_profile_digest", "required_process_profile_ref",
    "required_process_profile_digest", "required_isolation_profile_ref",
    "required_isolation_profile_digest", "required_resource_profile_ref",
    "required_resource_profile_digest", "required_cancellation_profile_ref",
    "required_cancellation_profile_digest", "required_credential_handoff_profile_ref",
    "required_credential_handoff_profile_digest", "required_capsule_store_profile_ref",
    "required_capsule_store_profile_digest", "required_validation_tool_profile_ref",
    "required_validation_tool_profile_digest", "required_review_tool_profile_ref",
    "required_review_tool_profile_digest", "required_cleanup_profile_ref",
    "required_cleanup_profile_digest", "result", "reason", "evaluated_at",
    "payload_row_digest",
)

_CAPABILITY_DIMENSIONS = (
    "noninteractive_operation", "wire_command_input_only", "wire_result_output_only",
    "protocol_stdout_only", "private_bounded_diagnostic_stderr",
    "external_cancellation_control_supported", "external_deadline_control_supported",
    "invocation_bound_logical_context", "private_history_non_authority",
    "isolated_credential_use", "private_interaction_material", "zero_git_effects",
    "restricted_network_access", "external_session_non_authority",
)

CAPABILITY_DECLARATION_COLUMNS = _TYPED_PREFIX + (
    "declaration_source_kind", "declaration_source_ref", "worker_artifact_ref",
    "worker_artifact_digest", "wire_profile_ref", "wire_profile_digest",
) + _CAPABILITY_DIMENSIONS + ("payload_row_digest",)

CAPABILITY_OBSERVATION_COLUMNS = _TYPED_PREFIX + (
    "observation_source_kind", "observation_source_ref", "observation_source_invocation_ref",
    "evidence_ref", "evidence_digest", "capability_declaration_ref",
    "capability_declaration_digest", "worker_artifact_ref", "worker_artifact_digest",
    "wire_profile_ref", "wire_profile_digest",
) + _CAPABILITY_DIMENSIONS + ("observed_at", "expires_at", "payload_row_digest")

CAPABILITY_QUALIFICATION_COLUMNS = _TYPED_PREFIX + (
    "capability_declaration_ref", "capability_declaration_digest",
    "capability_observation_ref", "capability_observation_digest", "worker_artifact_ref",
    "worker_artifact_digest", "wire_profile_ref", "wire_profile_digest",
    "phase_basis_ref", "phase_basis_digest", "authority_observation_ref",
    "authority_observation_digest", "readiness_observation_ref",
    "readiness_observation_digest", "host_qualification_ref",
    "host_qualification_digest", "effect_intent_ref", "effect_fence_ref",
    "effect_fence_digest", "result", "reason", "evaluated_at", "payload_row_digest",
)

WIRE_REQUEST_COLUMNS = _TYPED_PREFIX + (
    "source_kind", "source_ref", "source_invocation_ref", "evidence_ref",
    "evidence_digest", "program_ref", "program_version_ref",
    "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref",
    "semantic_attempt_ref", "candidate_ref", "command_ref", "command_digest",
    "attempt_fence_ref", "attempt_fence_digest", "cancellation_effect_intent_ref",
    "cancellation_effect_fence_ref", "cancellation_effect_fence_digest",
    "cancellation_delivery_attempt_ref", "cancellation_delivery_envelope_digest",
    "target_effect_intent_ref", "target_effect_fence_ref", "target_effect_fence_digest",
    "target_delivery_attempt_ref", "target_delivery_envelope_digest", "observed_at",
    "payload_row_digest",
)

WIRE_PROCESS_COLUMNS = _TYPED_PREFIX + (
    "source_kind", "source_ref", "source_invocation_ref", "evidence_ref",
    "evidence_digest", "event_kind", "program_ref", "program_version_ref",
    "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref",
    "semantic_attempt_ref", "candidate_ref", "command_ref", "command_digest",
    "attempt_fence_ref", "attempt_fence_digest", "effect_intent_ref",
    "effect_fence_ref", "effect_fence_digest", "delivery_attempt_ref",
    "delivery_envelope_digest", "observed_at", "payload_row_digest",
)

C2A_OBSERVATION_COLUMNS = _TYPED_PREFIX + (
    "source_kind", "source_ref", "source_invocation_ref", "delivery_attempt_ref",
    "program_ref", "program_version_ref", "accepted_intent_revision_ref",
    "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
    "effect_intent_ref", "command_ref", "command_digest", "attempt_fence_ref",
    "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest",
    "observation_kind", "outcome", "reason_code", "evidence_ref_count",
    "observed_at", "candidate_ref", "capsule_manifest_ref", "portable_capsule_digest",
    "process_exit_code", "payload_row_digest",
)

WORKER_RESULT_BINDING_COLUMNS = _TYPED_PREFIX + (
    "phase_basis_ref", "phase_basis_digest", "program_ref", "semantic_attempt_ref",
    "candidate_ref", "effect_intent_ref", "author_command_ref", "attempt_fence_ref",
    "effect_fence_ref", "delivery_attempt_ref", "wire_profile_ref",
    "wire_profile_digest", "observation_count", "observation_membership_set_digest",
    "relation_ref", "relation_digest", "payload_row_digest",
)

PROCESS_RESULT_BINDING_COLUMNS = _TYPED_PREFIX + (
    "phase_basis_ref", "phase_basis_digest", "program_ref", "semantic_attempt_ref",
    "candidate_ref", "effect_intent_ref", "author_command_ref", "attempt_fence_ref",
    "effect_fence_ref", "delivery_attempt_ref", "wire_profile_ref",
    "wire_profile_digest", "result_state", "result_membership_ref",
    "result_membership_digest", "result_failure_reason", "adapter_observation_count",
    "adapter_observation_membership_set_digest", "request_membership_ref",
    "request_membership_digest", "process_observation_count",
    "process_observation_membership_set_digest", "cancellation_effect_fence_ref",
    "cancellation_effect_fence_digest", "cancellation_delivery_attempt_ref",
    "cancellation_delivery_envelope_digest", "classification", "reason",
    "relation_ref", "relation_digest", "payload_row_digest",
)

SECTION41_MEMBER_COLUMNS = _TYPED_PREFIX + (
    "phase_basis_ref", "phase_basis_digest", "source_invocation_ref",
    "source_invocation_digest", "artifact_ref", "artifact_digest",
    "artifact_binding_digest", "proposal_ref", "proposal_digest", "model_contract_ref",
    "model_contract_digest", "model_configuration_ref", "model_configuration_digest",
    "context_schema_id", "context_ref", "context_digest", "safe_projection_schema_id",
    "safe_projection_digest", "evidence_set_ref", "evidence_set_digest",
    "evidence_binding_count", "recommendation", "reason_code", "proposal_created_at",
    "owner_family_graph_digest", "payload_row_digest",
)

AUTHORITY_EFFECT_CLASS_COLUMNS = (
    "schema_id", "kind_rank", "value_ref", "value_digest", "ordinal", "effect_class",
    "child_row_digest",
)
C2A_EVIDENCE_REF_COLUMNS = (
    "schema_id", "kind_rank", "value_ref", "value_digest", "ordinal", "evidence_ref",
    "child_row_digest",
)


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1RowSpec:
    table_name: str
    columns: tuple[str, ...]
    digest_column: str


ROW_SPECS: tuple[RW0C1RowSpec, ...] = (
    RW0C1RowSpec("rw0_phase_instances", PHASE_COLUMNS, "phase_row_digest"),
    RW0C1RowSpec("rw0_evidence_values", EVIDENCE_VALUE_COLUMNS, "value_row_digest"),
    RW0C1RowSpec("rw0_evidence_memberships", MEMBERSHIP_COLUMNS, "membership_digest"),
    RW0C1RowSpec("rw0_relation_bindings", RELATION_COLUMNS, "relation_row_digest"),
    RW0C1RowSpec("rw0_relation_operands", OPERAND_COLUMNS, "operand_row_digest"),
    RW0C1RowSpec("rw0_c1_mutation_receipts", RECEIPT_COLUMNS, "receipt_digest"),
    RW0C1RowSpec("rw0_authority_verification_observations", AUTHORITY_OBSERVATION_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_subordinate_authorization_proposals", SUBORDINATE_PROPOSAL_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_custody_availability_observations", CUSTODY_OBSERVATION_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_retrieval_capability_event_observations", RETRIEVAL_EVENT_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_remote_host_readiness_observations", READINESS_OBSERVATION_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_effect_host_qualifications", HOST_QUALIFICATION_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_worker_mechanism_capability_declarations", CAPABILITY_DECLARATION_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_worker_mechanism_capability_observations", CAPABILITY_OBSERVATION_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_worker_mechanism_capability_qualifications", CAPABILITY_QUALIFICATION_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_wire_cancellation_request_observations", WIRE_REQUEST_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_wire_process_observations", WIRE_PROCESS_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_c2a_worker_observations", C2A_OBSERVATION_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_wire_worker_result_bindings", WORKER_RESULT_BINDING_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_wire_process_result_classification_bindings", PROCESS_RESULT_BINDING_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_section41_post_execution_proposal_family_members", SECTION41_MEMBER_COLUMNS, "payload_row_digest"),
    RW0C1RowSpec("rw0_authority_observation_effect_classes", AUTHORITY_EFFECT_CLASS_COLUMNS, "child_row_digest"),
    RW0C1RowSpec("rw0_c2a_worker_observation_evidence_refs", C2A_EVIDENCE_REF_COLUMNS, "child_row_digest"),
)
ROW_SPEC_BY_TABLE = {spec.table_name: spec for spec in ROW_SPECS}

_COMMON_ROW_SCHEMAS = {
    "rw0_phase_instances": "governed-execution.nwp-rw0-c1-phase-instance-row.v1",
    "rw0_evidence_values": "governed-execution.nwp-rw0-c1-evidence-value-row.v1",
    "rw0_evidence_memberships": "governed-execution.nwp-rw0-c1-evidence-membership.v1",
    "rw0_relation_bindings": "governed-execution.nwp-rw0-c1-relation-binding.v1",
    "rw0_relation_operands": "governed-execution.nwp-rw0-c1-relation-operand.v1",
    "rw0_c1_mutation_receipts": "governed-execution.nwp-rw0-c1-mutation-receipt.v1",
    "rw0_authority_observation_effect_classes": (
        "governed-execution.nwp-rw0-c1-authority-effect-class-row.v1"
    ),
    "rw0_c2a_worker_observation_evidence_refs": (
        "governed-execution.nwp-rw0-c1-worker-observation-evidence-ref-row.v1"
    ),
}
_TYPED_TABLES = tuple(spec.table_name for spec in ROW_SPECS[6:21])
_ROW_SCHEMA_BY_TABLE = dict(_COMMON_ROW_SCHEMAS)
_ROW_SCHEMA_BY_TABLE.update(
    {
        table: (
            "governed-execution.nwp-rw0-c1-"
            + table.removeprefix("rw0_").replace("_", "-")
            + "-payload-row.v1"
        )
        for table in _TYPED_TABLES
    }
)
_VALUE_SCHEMA_BY_RANK = (
    "governed-execution.nwp-rw0-authority-verification-observation.v1",
    "governed-execution.nwp-rw0-subordinate-authorization-proposal.v1",
    "governed-execution.nwp-rw0-custody-availability-observation.v1",
    "governed-execution.nwp-rw0-retrieval-capability-event-observation.v1",
    "governed-execution.nwp-rw0-remote-host-readiness-observation.v1",
    "governed-execution.nwp-rw0-effect-host-qualification.v1",
    "governed-execution.nwp-rw0-worker-mechanism-capability-declaration.v1",
    "governed-execution.nwp-rw0-worker-mechanism-capability-observation.v1",
    "governed-execution.nwp-rw0-worker-mechanism-capability-qualification.v1",
    "governed-execution.nwp-rw0-wire-cancellation-request-observation.v1",
    "governed-execution.nwp-rw0-wire-process-observation.v1",
    "governed-execution.nwp-worker-observation.v1",
    "governed-execution.nwp-rw0-c1-wire-worker-result-binding.v1",
    "governed-execution.nwp-rw0-c1-wire-process-result-classification-binding.v1",
    (
        "governed-execution.nwp-rw0-c1-"
        "section41-post-execution-proposal-family-member.v1"
    ),
)


class RW0C1RowValidationError(ValueError):
    __slots__ = ()

    def __init__(self) -> None:
        ValueError.__init__(self, "invalid_rw0_c1_row")


class RW0C1RowValue:
    __slots__ = ("_spec", "_values")

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled") from None

    @classmethod
    def _create(cls, spec: RW0C1RowSpec, values: tuple[object, ...]) -> "RW0C1RowValue":
        result = object.__new__(cls)
        object.__setattr__(result, "_spec", spec)
        object.__setattr__(result, "_values", values)
        return result

    @property
    def table_name(self) -> str:
        return self._spec.table_name

    @property
    def columns(self) -> tuple[str, ...]:
        return self._spec.columns

    def as_tuple(self) -> tuple[object, ...]:
        return self._values

    def to_mapping(self) -> dict[str, object]:
        return dict(zip(self._spec.columns, self._values, strict=True))

    def value(self, column: str) -> object:
        if type(column) is not str or column not in self._spec.columns:
            raise RW0C1RowValidationError() from None
        return self._values[self._spec.columns.index(column)]

    def __repr__(self) -> str:
        return "<RW0C1RowValue>"

    def __setattr__(self, name: str, value: object) -> typing.NoReturn:
        raise AttributeError("immutable") from None

    def __copy__(self) -> typing.NoReturn:
        raise TypeError("copy disabled") from None

    def __deepcopy__(self, memo: object) -> typing.NoReturn:
        raise TypeError("copy disabled") from None

    def __reduce__(self) -> typing.NoReturn:
        raise TypeError("pickling disabled") from None

    def __reduce_ex__(self, protocol: int) -> typing.NoReturn:
        raise TypeError("pickling disabled") from None


def _canonical_bytes(mapping: dict[str, object]) -> bytes:
    try:
        return json.dumps(mapping, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        raise RW0C1RowValidationError() from None


def _require_sha256(value: object) -> str:
    if type(value) is not str or _DIGEST_PATTERN.fullmatch(value) is None:
        raise RW0C1RowValidationError() from None
    return value


def _require_utc_timestamp(value: object) -> str:
    try:
        if (
            type(value) is not str
            or len(value) != 20
            or value[4] != "-"
            or value[7] != "-"
            or value[10] != "T"
            or value[13] != ":"
            or value[16] != ":"
            or value[19] != "Z"
            or not (
                value[0:4]
                + value[5:7]
                + value[8:10]
                + value[11:13]
                + value[14:16]
                + value[17:19]
            ).isdigit()
        ):
            raise ValueError
        parsed = datetime.datetime(
            int(value[0:4]),
            int(value[5:7]),
            int(value[8:10]),
            int(value[11:13]),
            int(value[14:16]),
            int(value[17:19]),
            tzinfo=datetime.timezone.utc,
        )
        rendered = (
            f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}T"
            f"{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}Z"
        )
        if rendered != value:
            raise ValueError
    except (TypeError, ValueError, OverflowError):
        raise RW0C1RowValidationError() from None
    return value


def row_digest(schema_id: str, mapping_without_digest: dict[str, object]) -> str:
    if type(schema_id) is not str or not schema_id:
        raise RW0C1RowValidationError() from None
    return hashlib.sha256(
        (schema_id + ".identity").encode("utf-8")
        + b"\x00"
        + _canonical_bytes(mapping_without_digest)
    ).hexdigest()


def rw0_c1_row_value_from_mapping(
    table_name: object, mapping: object, *, verify_digest: bool = True,
) -> RW0C1RowValue:
    if type(table_name) is not str or table_name not in ROW_SPEC_BY_TABLE or type(mapping) is not dict:
        raise RW0C1RowValidationError() from None
    spec = ROW_SPEC_BY_TABLE[table_name]
    if tuple(mapping) != spec.columns:
        raise RW0C1RowValidationError() from None
    values = tuple(mapping[column] for column in spec.columns)
    if any(type(value) not in {str, int, type(None)} for value in values):
        raise RW0C1RowValidationError() from None
    if mapping["schema_id"] != _ROW_SCHEMA_BY_TABLE[table_name]:
        raise RW0C1RowValidationError() from None
    kind_rank = mapping.get("kind_rank")
    if table_name in _TYPED_TABLES:
        expected_rank = _TYPED_TABLES.index(table_name) + 1
        if (
            kind_rank != expected_rank
            or mapping.get("value_schema_id")
            != _VALUE_SCHEMA_BY_RANK[expected_rank - 1]
        ):
            raise RW0C1RowValidationError() from None
    elif table_name == "rw0_evidence_values":
        if (
            type(kind_rank) is not int
            or not 1 <= kind_rank <= 15
            or mapping.get("value_schema_id")
            != _VALUE_SCHEMA_BY_RANK[kind_rank - 1]
        ):
            raise RW0C1RowValidationError() from None
    elif table_name in {
        "rw0_authority_observation_effect_classes",
        "rw0_c2a_worker_observation_evidence_refs",
    }:
        expected_rank = (
            1
            if table_name == "rw0_authority_observation_effect_classes"
            else 12
        )
        if kind_rank != expected_rank:
            raise RW0C1RowValidationError() from None
    for column, value in mapping.items():
        if value is None:
            continue
        if (
            column.endswith("_digest")
            or column.endswith("_sha256")
            or column in {"base_git_oid"}
            and mapping.get("base_git_object_format") == "sha256"
        ):
            _require_sha256(value)
        if column.endswith("_at"):
            _require_utc_timestamp(value)
    if verify_digest:
        stored = mapping[spec.digest_column]
        if type(stored) is not str:
            raise RW0C1RowValidationError() from None
        identity = {column: mapping[column] for column in spec.columns if column != spec.digest_column}
        if stored != row_digest(typing.cast(str, mapping["schema_id"]), identity):
            raise RW0C1RowValidationError() from None
    return RW0C1RowValue._create(spec, values)


def rw0_c1_row_value_from_tuple(table_name: object, row: object) -> RW0C1RowValue:
    if type(table_name) is not str or table_name not in ROW_SPEC_BY_TABLE or type(row) is not tuple:
        raise RW0C1RowValidationError() from None
    spec = ROW_SPEC_BY_TABLE[table_name]
    if len(row) != len(spec.columns):
        raise RW0C1RowValidationError() from None
    mapping = dict(zip(spec.columns, row, strict=True))
    return rw0_c1_row_value_from_mapping(table_name, mapping)


def build_row_mapping(
    table_name: str, values_without_digest: dict[str, object],
) -> dict[str, object]:
    if table_name not in ROW_SPEC_BY_TABLE:
        raise RW0C1RowValidationError() from None
    spec = ROW_SPEC_BY_TABLE[table_name]
    expected = tuple(column for column in spec.columns if column != spec.digest_column)
    if tuple(values_without_digest) != expected:
        raise RW0C1RowValidationError() from None
    schema_id = values_without_digest.get("schema_id")
    if type(schema_id) is not str:
        raise RW0C1RowValidationError() from None
    result = dict(values_without_digest)
    result[spec.digest_column] = row_digest(schema_id, result)
    ordered = {column: result[column] for column in spec.columns}
    rw0_c1_row_value_from_mapping(table_name, ordered)
    return ordered
