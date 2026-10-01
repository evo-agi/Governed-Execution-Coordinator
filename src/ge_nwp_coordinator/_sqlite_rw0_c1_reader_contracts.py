"""Literal private SELECT contracts for RW0-C1 durable families."""

from __future__ import annotations

from dataclasses import dataclass

from ._rw0_c1_row_values import ROW_SPEC_BY_TABLE


__all__: tuple[str, ...] = ()


_ACCEPTED_LIMITS = frozenset({2, 3, 15, 16, 257, 258})

_SECTION41_EVIDENCE_COLUMNS = (
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

_DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS = (
    "schema_id",
    "work_spec_ref",
    "program_ref",
    "program_version_ref",
    "accepted_intent_revision_ref",
    "work_item_ref",
    "work_item_revision_ref",
    "repository_ref",
    "base_git_object_format",
    "base_git_oid",
    "authorized_paths_json",
    "validation_requirement_ref",
    "review_requirement_ref",
    "privacy_classification",
    "work_spec_digest",
    "safe_projection_digest",
    "recorded_at",
    "work_spec_binding_digest",
)

_DEVELOPMENT_ATTEMPT_FENCE_COLUMNS = (
    "schema_id",
    "attempt_fence_ref",
    "parent_standing_grant_ref",
    "parent_standing_grant_digest",
    "attempt_authorization_ref",
    "attempt_authorization_digest",
    "program_ref",
    "program_version_ref",
    "accepted_intent_revision_ref",
    "work_item_ref",
    "work_item_revision_ref",
    "semantic_attempt_ref",
    "repository_ref",
    "base_git_object_format",
    "base_git_oid",
    "path_ceiling_json",
    "allowed_effect_class_mask",
    "aggregate_max_active_invocations",
    "aggregate_max_candidate_bytes",
    "aggregate_max_changed_files",
    "aggregate_max_cost_microusd",
    "aggregate_max_cpu_seconds",
    "aggregate_max_deliveries",
    "aggregate_max_deployments",
    "aggregate_max_local_commits",
    "aggregate_max_memory_bytes",
    "aggregate_max_merges",
    "aggregate_max_model_input_tokens",
    "aggregate_max_model_output_tokens",
    "aggregate_max_pull_requests",
    "aggregate_max_pushes",
    "aggregate_max_wall_seconds",
    "expires_at",
    "global_stop_ref",
    "global_stop_version",
    "attempt_fence_digest",
    "recorded_at",
)

_DEVELOPMENT_EFFECT_FENCE_COLUMNS = (
    "schema_id",
    "effect_fence_ref",
    "parent_standing_grant_ref",
    "parent_standing_grant_digest",
    "effect_authorization_ref",
    "effect_authorization_digest",
    "attempt_fence_ref",
    "attempt_fence_digest",
    "program_ref",
    "program_version_ref",
    "accepted_intent_revision_ref",
    "work_item_ref",
    "work_item_revision_ref",
    "semantic_attempt_ref",
    "effect_intent_ref",
    "effect_class",
    "command_ref",
    "command_digest",
    "candidate_ref",
    "repository_ref",
    "base_git_object_format",
    "base_git_oid",
    "path_ceiling_json",
    "effect_max_active_invocations",
    "effect_max_candidate_bytes",
    "effect_max_changed_files",
    "effect_max_cost_microusd",
    "effect_max_cpu_seconds",
    "effect_max_deliveries",
    "effect_max_deployments",
    "effect_max_local_commits",
    "effect_max_memory_bytes",
    "effect_max_merges",
    "effect_max_model_input_tokens",
    "effect_max_model_output_tokens",
    "effect_max_pull_requests",
    "effect_max_pushes",
    "effect_max_wall_seconds",
    "expires_at",
    "global_stop_ref",
    "global_stop_version",
    "portable_capsule_digest",
    "cancellation_target_effect_intent_ref",
    "cancellation_target_effect_fence_ref",
    "cancellation_target_effect_fence_digest",
    "effect_fence_digest",
    "recorded_at",
)

_DEVELOPMENT_AUTHOR_COMMAND_COLUMNS = (
    "schema_id",
    "command_ref",
    "program_ref",
    "program_version_ref",
    "accepted_intent_revision_ref",
    "work_item_ref",
    "work_item_revision_ref",
    "semantic_attempt_ref",
    "effect_intent_ref",
    "effect_class",
    "candidate_ref",
    "repository_ref",
    "base_git_object_format",
    "base_git_oid",
    "path_ceiling_json",
    "work_spec_ref",
    "work_spec_digest",
    "standing_grant_ref",
    "standing_grant_digest",
    "attempt_authorization_ref",
    "attempt_authorization_digest",
    "effect_authorization_ref",
    "effect_authorization_digest",
    "attempt_fence_ref",
    "attempt_fence_digest",
    "effect_fence_ref",
    "effect_fence_digest",
    "global_stop_ref",
    "global_stop_version",
    "validation_requirement_ref",
    "validation_requirement_digest",
    "review_requirement_ref",
    "review_requirement_digest",
    "capsule_schema_id",
    "capsule_profile_ref",
    "effect_max_active_invocations",
    "effect_max_candidate_bytes",
    "effect_max_changed_files",
    "effect_max_cost_microusd",
    "effect_max_cpu_seconds",
    "effect_max_deliveries",
    "effect_max_deployments",
    "effect_max_local_commits",
    "effect_max_memory_bytes",
    "effect_max_merges",
    "effect_max_model_input_tokens",
    "effect_max_model_output_tokens",
    "effect_max_pull_requests",
    "effect_max_pushes",
    "effect_max_wall_seconds",
    "privacy_classification",
    "redaction_profile_ref",
    "command_digest",
    "recorded_at",
)

_DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS = (
    "schema_id",
    "delivery_attempt_ref",
    "program_ref",
    "program_version_ref",
    "command_ref",
    "command_digest",
    "semantic_attempt_ref",
    "effect_intent_ref",
    "attempt_fence_ref",
    "attempt_fence_digest",
    "effect_fence_ref",
    "effect_fence_digest",
    "adapter_kind",
    "adapter_safe_correlation_ref",
    "delivery_envelope_digest",
    "delivery_kind",
    "delivery_number",
    "predecessor_delivery_attempt_ref",
    "basis_decision_ref",
    "recorded_at",
    "delivery_attempt_digest",
)


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1SelectSpecification:
    query_id: str
    table_name: str
    columns: tuple[str, ...]
    sql: str
    fetch_limit: int

    def __post_init__(self) -> None:
        if (
            type(self.query_id) is not str
            or not self.query_id
            or self.table_name not in ROW_SPEC_BY_TABLE
            or self.columns != ROW_SPEC_BY_TABLE[self.table_name].columns
            or type(self.sql) is not str
            or not self.sql.startswith("SELECT ")
            or "SELECT *" in self.sql.upper()
            or self.fetch_limit not in _ACCEPTED_LIMITS
            or not self.sql.endswith(f"LIMIT {self.fetch_limit}")
        ):
            raise ValueError("invalid RW0-C1 SELECT specification")

    def __repr__(self) -> str:
        return "<RW0C1SelectSpecification>"


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1OwnerSelectSpecification:
    role: str
    table_name: str
    columns: tuple[str, ...]
    sql: str
    fetch_limit: int = 2

    def __post_init__(self) -> None:
        if (
            type(self.role) is not str
            or not self.role
            or type(self.table_name) is not str
            or not self.table_name.startswith("development_")
            or type(self.columns) is not tuple
            or not self.columns
            or not self.sql.startswith("SELECT ")
            or "SELECT *" in self.sql.upper()
            or not self.sql.endswith("LIMIT 2")
            or self.fetch_limit != 2
        ):
            raise ValueError("invalid RW0-C1 owner SELECT specification")

    def __repr__(self) -> str:
        return "<RW0C1OwnerSelectSpecification>"


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1Section41FamilySelectSpecification:
    query_id: str
    table_name: str
    columns: tuple[str, ...]
    sql: str
    fetch_limit: int = 16

    def __post_init__(self) -> None:
        if (
            self.query_id != "rw0_c1_section41_post_execution_evidence_family"
            or self.table_name != "development_model_proposal_evidence_bindings"
            or self.columns != _SECTION41_EVIDENCE_COLUMNS
            or not self.sql.startswith("SELECT ")
            or "SELECT *" in self.sql.upper()
            or not self.sql.endswith("LIMIT 16")
            or self.fetch_limit != 16
        ):
            raise ValueError("invalid RW0-C1 Section 41 SELECT specification")

    def __repr__(self) -> str:
        return "<RW0C1Section41FamilySelectSpecification>"


def _select(
    query_id: str,
    table_name: str,
    where: str,
    *,
    order_by: str | None = None,
    limit: int = 2,
) -> RW0C1SelectSpecification:
    columns = ROW_SPEC_BY_TABLE[table_name].columns
    sql = f"SELECT {', '.join(columns)} FROM {table_name} WHERE {where}"
    if order_by is not None:
        sql += f" ORDER BY {order_by}"
    sql += f" LIMIT {limit}"
    return RW0C1SelectSpecification(query_id, table_name, columns, sql, limit)


RECEIPT_BY_MUTATION_REF = _select(
    "rw0_c1_receipt_by_mutation_ref",
    "rw0_c1_mutation_receipts",
    "mutation_ref = ?",
)
PHASE_BY_REF = _select(
    "rw0_c1_phase_by_ref", "rw0_phase_instances", "phase_basis_ref = ?"
)
PHASE_BY_PAIR = _select(
    "rw0_c1_phase_by_pair",
    "rw0_phase_instances",
    "phase_basis_ref = ? AND phase_basis_digest = ?",
)
PHASE_BY_DIGEST = _select(
    "rw0_c1_phase_by_digest", "rw0_phase_instances", "phase_basis_digest = ?"
)
PHASE_BY_K8 = _select(
    "rw0_c1_phase_by_k8",
    "rw0_phase_instances",
    "program_ref = ? AND semantic_attempt_ref = ? AND candidate_ref = ? "
    "AND effect_intent_ref = ? AND author_command_ref = ? AND attempt_fence_ref = ? "
    "AND effect_fence_ref = ? AND delivery_attempt_ref = ?",
)
EVIDENCE_BY_KIND_REF = _select(
    "rw0_c1_evidence_by_kind_ref",
    "rw0_evidence_values",
    "kind_rank = ? AND value_ref = ?",
)
EVIDENCE_BY_KIND_DIGEST = _select(
    "rw0_c1_evidence_by_kind_digest",
    "rw0_evidence_values",
    "kind_rank = ? AND value_digest = ?",
)
MEMBERSHIP_BY_REF = _select(
    "rw0_c1_membership_by_ref", "rw0_evidence_memberships", "membership_ref = ?"
)
MEMBERSHIP_BY_DIGEST = _select(
    "rw0_c1_membership_by_digest",
    "rw0_evidence_memberships",
    "membership_digest = ?",
)
MEMBERSHIP_BY_PHASE_KIND_REF = _select(
    "rw0_c1_membership_by_phase_kind_ref",
    "rw0_evidence_memberships",
    "phase_basis_ref = ? AND kind_rank = ? AND value_ref = ?",
)
MEMBERSHIP_BY_PHASE_KIND_DIGEST = _select(
    "rw0_c1_membership_by_phase_kind_digest",
    "rw0_evidence_memberships",
    "phase_basis_ref = ? AND kind_rank = ? AND value_digest = ?",
)
RELATION_BY_REF = _select(
    "rw0_c1_relation_by_ref", "rw0_relation_bindings", "relation_ref = ?"
)
RELATION_BY_DIGEST = _select(
    "rw0_c1_relation_by_digest", "rw0_relation_bindings", "relation_digest = ?"
)
RELATIONS_FOR_PHASE = _select(
    "rw0_c1_relations_for_phase",
    "rw0_relation_bindings",
    "phase_basis_ref = ? AND subject_type = 'phase_establishment'",
    order_by="relation_rank ASC, relation_ref ASC",
    limit=3,
)
RELATIONS_FOR_MEMBERSHIP = _select(
    "rw0_c1_relations_for_membership",
    "rw0_relation_bindings",
    "phase_basis_ref = ? AND subject_type = 'evidence_membership' "
    "AND subject_membership_ref = ?",
    order_by="relation_rank ASC, relation_ref ASC",
    limit=3,
)
OPERANDS_FOR_RELATION = _select(
    "rw0_c1_operands_for_relation",
    "rw0_relation_operands",
    "relation_ref = ?",
    order_by="operand_ordinal ASC",
    limit=15,
)
MEMBERSHIP_PAGE = _select(
    "rw0_c1_membership_page",
    "rw0_evidence_memberships",
    "phase_basis_ref = ? AND (kind_rank > ? OR (kind_rank = ? AND membership_ref > ?))",
    order_by="kind_rank ASC, membership_ref ASC",
    limit=257,
)


TYPED_VALUE_BY_KIND_REF: tuple[RW0C1SelectSpecification, ...] = tuple(
    _select(
        f"rw0_c1_typed_value_rank_{rank}",
        table_name,
        "kind_rank = ? AND value_ref = ?",
    )
    for rank, table_name in enumerate(
        (
            "rw0_authority_verification_observations",
            "rw0_subordinate_authorization_proposals",
            "rw0_custody_availability_observations",
            "rw0_retrieval_capability_event_observations",
            "rw0_remote_host_readiness_observations",
            "rw0_effect_host_qualifications",
            "rw0_worker_mechanism_capability_declarations",
            "rw0_worker_mechanism_capability_observations",
            "rw0_worker_mechanism_capability_qualifications",
            "rw0_wire_cancellation_request_observations",
            "rw0_wire_process_observations",
            "rw0_c2a_worker_observations",
            "rw0_wire_worker_result_bindings",
            "rw0_wire_process_result_classification_bindings",
            "rw0_section41_post_execution_proposal_family_members",
        ),
        1,
    )
)
TYPED_VALUE_BY_KIND_DIGEST: tuple[RW0C1SelectSpecification, ...] = tuple(
    _select(
        f"rw0_c1_typed_value_rank_{rank}_by_digest",
        table_name,
        "kind_rank = ? AND value_digest = ?",
    )
    for rank, table_name in enumerate(
        tuple(item.table_name for item in TYPED_VALUE_BY_KIND_REF),
        1,
    )
)

AUTHORITY_EFFECT_CLASSES = _select(
    "rw0_c1_authority_effect_classes",
    "rw0_authority_observation_effect_classes",
    "kind_rank = 1 AND value_ref = ?",
    order_by="ordinal ASC",
    limit=16,
)
AUTHORITY_EFFECT_CLASSES_BY_DIGEST = _select(
    "rw0_c1_authority_effect_classes_by_digest",
    "rw0_authority_observation_effect_classes",
    "kind_rank = 1 AND value_digest = ?",
    order_by="ordinal ASC",
    limit=16,
)
C2A_EVIDENCE_REFS = _select(
    "rw0_c1_c2a_evidence_refs",
    "rw0_c2a_worker_observation_evidence_refs",
    "kind_rank = 12 AND value_ref = ?",
    order_by="ordinal ASC",
    limit=258,
)
C2A_EVIDENCE_REFS_BY_DIGEST = _select(
    "rw0_c1_c2a_evidence_refs_by_digest",
    "rw0_c2a_worker_observation_evidence_refs",
    "kind_rank = 12 AND value_digest = ?",
    order_by="ordinal ASC",
    limit=258,
)

_SECTION41_EVIDENCE_TABLE = "development_model_proposal_evidence_bindings"
SECTION41_POST_EXECUTION_EVIDENCE_FAMILY = (
    RW0C1Section41FamilySelectSpecification(
        "rw0_c1_section41_post_execution_evidence_family",
        _SECTION41_EVIDENCE_TABLE,
        _SECTION41_EVIDENCE_COLUMNS,
        "SELECT "
        + ", ".join(_SECTION41_EVIDENCE_COLUMNS)
        + " FROM development_model_proposal_evidence_bindings "
        "WHERE proposal_ref = ? ORDER BY role_rank, ordinal, evidence_role, "
        "evidence_set_ref, evidence_ref, evidence_digest, "
        "evidence_binding_digest, proposal_phase, schema_id, "
        "required_for_selection, evidence_bound_at LIMIT 16",
    )
)

ALL_SELECT_SPECIFICATIONS = (
    RECEIPT_BY_MUTATION_REF,
    PHASE_BY_REF,
    PHASE_BY_PAIR,
    PHASE_BY_DIGEST,
    PHASE_BY_K8,
    EVIDENCE_BY_KIND_REF,
    EVIDENCE_BY_KIND_DIGEST,
    MEMBERSHIP_BY_REF,
    MEMBERSHIP_BY_DIGEST,
    MEMBERSHIP_BY_PHASE_KIND_REF,
    MEMBERSHIP_BY_PHASE_KIND_DIGEST,
    RELATION_BY_REF,
    RELATION_BY_DIGEST,
    RELATIONS_FOR_PHASE,
    RELATIONS_FOR_MEMBERSHIP,
    OPERANDS_FOR_RELATION,
    MEMBERSHIP_PAGE,
    *TYPED_VALUE_BY_KIND_REF,
    *TYPED_VALUE_BY_KIND_DIGEST,
    AUTHORITY_EFFECT_CLASSES,
    AUTHORITY_EFFECT_CLASSES_BY_DIGEST,
    C2A_EVIDENCE_REFS,
    C2A_EVIDENCE_REFS_BY_DIGEST,
    SECTION41_POST_EXECUTION_EVIDENCE_FAMILY,
)


def _owner_select(
    role: str,
    table_name: str,
    columns: tuple[str, ...],
    identity_column: str,
) -> RW0C1OwnerSelectSpecification:
    return RW0C1OwnerSelectSpecification(
        role,
        table_name,
        columns,
        f"SELECT {', '.join(columns)} FROM {table_name} "
        f"WHERE {identity_column} = ? LIMIT 2",
    )


OWNER_DEVELOPMENT_SELECTS: tuple[RW0C1OwnerSelectSpecification, ...] = (
    _owner_select(
        "development_work_spec_binding",
        "development_work_spec_bindings",
        _DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS,
        "work_spec_ref",
    ),
    _owner_select(
        "development_attempt_fence",
        "development_attempt_fences",
        _DEVELOPMENT_ATTEMPT_FENCE_COLUMNS,
        "attempt_fence_ref",
    ),
    _owner_select(
        "development_effect_fence",
        "development_effect_fences",
        _DEVELOPMENT_EFFECT_FENCE_COLUMNS,
        "effect_fence_ref",
    ),
    _owner_select(
        "development_author_command",
        "development_author_commands",
        _DEVELOPMENT_AUTHOR_COMMAND_COLUMNS,
        "command_ref",
    ),
    _owner_select(
        "development_delivery_attempt",
        "development_delivery_attempts",
        _DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS,
        "delivery_attempt_ref",
    ),
)
OWNER_DEVELOPMENT_SELECT_BY_ROLE = {
    specification.role: specification
    for specification in OWNER_DEVELOPMENT_SELECTS
}
