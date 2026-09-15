"""Private atomic mechanics for Section 41 proposal selection.

This module borrows the existing nominal Coordinator mutation capability.  It
does not own a connection, transaction, lock, writer, clock, or public API.
"""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
import typing

from . import _cognitive_proposal_row_values as _rows
from . import _cognitive_proposal_semantic_values as _semantic
from . import _development_decision_row_values as _decision_rows
from . import _development_effect_row_values as _effect_rows
from . import _development_program_row_values as _program_rows
from ._cognitive_proposal_value_support import (
    _CognitiveProposalContractViolation,
    _canonical_bytes,
    _constant_repr,
    _domain_separated_digest,
    _exact_equal,
    _require_canonical_effect_class_json,
    _require_safe_ref,
    _require_sha256,
    _require_utc_second,
    _violate,
    _without_field,
)
from ._development_pre_execution_plan_disposition_contracts import (
    CanonicalC2B3DLineage,
    CognitiveMutationGraphEntryV1,
    CognitiveMutationGraphV1,
    PreExecutionPlanDispositionConflictReasonV1,
    PreExecutionPlanDispositionConflictV1,
    PreExecutionPlanDispositionRecoveryClassificationV1,
    PreExecutionPlanDispositionRecoveryProbeV1,
    PreExecutionPlanDispositionRecoveryResultV1,
    PreExecutionPlanDispositionResultProjectionV1,
    PreExecutionPlanDispositionResultV1,
    PreExecutionSelectionHeadPreimageV1,
    RecordPreExecutionPlanDispositionCommandV1,
    _K8_FIELDS,
    _L34_FIELDS,
    _RECOVERY_PROBE_IDENTITY_SHAPES,
    _PreExecutionPlanDispositionWritePlan,
    _build_pre_execution_plan_disposition_recovery_probe,
    _build_pre_execution_plan_disposition_recovery_probe_from_basis,
    _lineage_from_context,
    _require_exact_recovery_probe,
    _record_command_from_ingress,
)
from ._development_author_effect_establishment_contracts import (
    DevelopmentAuthorEffectEstablishmentCommandV1,
    DevelopmentReviewRequirementEvidenceV1,
    DevelopmentValidationRequirementEvidenceV1,
    _development_effect_authorization_safe_binding,
)
from ._sqlite_development_author_effect_establishment import (
    _genesis_basis_is_current_and_exact,
    _read_and_verify_exact_author_effect_family,
)
from ._sqlite_development_reader_contracts import (
    DevelopmentAttemptFenceCommandEffectRead,
    DevelopmentDeliveryHeadAndCurrentAttemptRead,
    DevelopmentProgramHeadAndCurrentVersionRead,
    DevelopmentWorkItemHeadAndRevisionRead,
)
from ._sqlite_development_readers import (
    _read_development_attempt_fence_command_effect_aggregate,
    _read_development_authority_evaluation_by_exact_ref,
    _read_development_delivery_head,
    _read_development_effect_head,
    _read_development_program_head_and_current_version,
    _read_development_work_item_head_and_revision_by_exact_ref,
    _read_development_work_spec_safe_binding,
)
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from .persistence_contracts import GlobalStopCurrentRecordEnvelope
from .sqlite_transition_read_scope import _read_global_stop_current
from .sqlite_transition_select_support import (
    _MutationReadCapability,
    _execute_select_fetch_bounded,
    _execute_select_fetch_two,
)


__all__ = ()


_MUTATION_FAMILY = "record_pre_execution_plan_disposition"
_RESULT_CLASS = "pre_execution_plan_disposition_recorded"
_OUTCOME = "committed"
_RECEIPT_SCHEMA = "governed-execution.nwp-cognitive-mutation-receipt.v1"
_RECEIPT_DOMAIN = _RECEIPT_SCHEMA + ".identity"
_DISPOSITION_SCHEMA = "governed-execution.nwp-pre-execution-coordinator-disposition.v1"
_HEAD_SCHEMA = "governed-execution.nwp-pre-execution-selection-head.v1"
_COMMAND_SCHEMA = (
    "governed-execution.nwp-record-pre-execution-plan-disposition-command.v1"
)
_RESULT_SCHEMA = "governed-execution.nwp-pre-execution-plan-disposition-result.v1"
_RESULT_DOMAIN = _RESULT_SCHEMA + ".identity"
_GRAPH_DOMAIN = "governed-execution.nwp-cognitive-mutation-graph.v1.identity"

_EVIDENCE_RECOVERY_COLUMNS = (
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
_EVIDENCE_SELECT = (
    "SELECT "
    + ", ".join(_EVIDENCE_RECOVERY_COLUMNS)
    + " FROM development_model_proposal_evidence_bindings "
    "WHERE proposal_ref = ? ORDER BY role_rank, ordinal, evidence_role, "
    "evidence_set_ref, evidence_ref, evidence_digest, evidence_binding_digest, "
    "proposal_phase, schema_id, required_for_selection, evidence_bound_at LIMIT 16"
)
_K8_WHERE = " AND ".join(f"{name} = ?" for name in _K8_FIELDS)
_L34_WHERE = " AND ".join(f"{name} = ?" for name in _L34_FIELDS)


def _l34_values(value: object) -> tuple[object, ...]:
    return tuple(object.__getattribute__(value, name) for name in _L34_FIELDS)


def _database_integrity_failure() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(
        SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
    )


def _mutation_failed() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)


@dataclass(frozen=True, slots=True, repr=False)
class _FreshPreExecutionPlanDisposition:
    command: RecordPreExecutionPlanDispositionCommandV1
    bundle: _semantic.PreExecutionProposalSelectionBundleV1
    current_head: _rows.DevelopmentPreExecutionSelectionHeadRowValue | None
    recovery_probe: PreExecutionPlanDispositionRecoveryProbeV1

    __repr__ = _constant_repr


@dataclass(frozen=True, slots=True, repr=False)
class _VerifiedPersistedPreExecutionPlanDisposition:
    result: PreExecutionPlanDispositionResultV1
    observed_depth: int
    command: RecordPreExecutionPlanDispositionCommandV1
    identity_locators: tuple[tuple[str, tuple[tuple[str, object], ...]], ...]
    recovery_probe: PreExecutionPlanDispositionRecoveryProbeV1

    __repr__ = _constant_repr


class _PlanningSelectionNotPermitted(RuntimeError):
    __slots__ = ()


class _LineageProofOverflow(RuntimeError):
    __slots__ = ("head", "observed_depth")

    def __init__(
        self,
        head: _rows.DevelopmentPreExecutionSelectionHeadRowValue,
        observed_depth: int,
    ) -> None:
        if (
            type(head) is not _rows.DevelopmentPreExecutionSelectionHeadRowValue
            or type(observed_depth) is not int
            or observed_depth != 257
        ):
            raise _database_integrity_failure() from None
        self.head = head
        self.observed_depth = observed_depth
        RuntimeError.__init__(self)

    __repr__ = _constant_repr
    __str__ = _constant_repr


_AUTHORITY_NOT_PERMITTED_REASONS = frozenset(
    {
        "authority_observation_shape_invalid",
        "authority_observation_binding_mismatch",
        "authority_observation_version_invalid",
        "authority_observation_state_ineligible",
        "authority_observation_window_invalid",
    }
)
_PRIVATE_PLAN_NOT_PERMITTED_REASONS = frozenset(
    {
        "private_plan_narrative_invalid",
        "private_plan_nested_collection_invalid",
        "private_plan_closed_vocabulary_invalid",
        "private_plan_artifact_size_invalid",
        "private_plan_prerequisite_order_invalid",
        "private_plan_prerequisite_unreferenced",
        "private_plan_stop_unreferenced",
        "private_plan_validation_link_asymmetric",
        "private_plan_forward_dependency",
    }
)
_PLANNING_RELATION_REASONS = frozenset(
    {
        "preselection_timestamp_digest_mismatch",
        "safe_projection_derivation_mismatch",
        "physical_family_readiness_mismatch",
        "relation_mismatch",
    }
)


def _conflict(
    command: RecordPreExecutionPlanDispositionCommandV1,
    reason: PreExecutionPlanDispositionConflictReasonV1,
) -> PreExecutionPlanDispositionConflictV1:
    return PreExecutionPlanDispositionConflictV1(
        reason=reason,
        mutation_ref=command.mutation_ref,
        command_digest=command.mutation_command_digest,
        program_ref=command.program_ref,
    )


def _relation_violation_conflict_reason(
    violation: _CognitiveProposalContractViolation,
) -> PreExecutionPlanDispositionConflictReasonV1 | None:
    reason = violation.reason
    if reason in _AUTHORITY_NOT_PERMITTED_REASONS:
        return (
            PreExecutionPlanDispositionConflictReasonV1.PLANNING_SELECTION_NOT_PERMITTED
        )
    if reason in _PRIVATE_PLAN_NOT_PERMITTED_REASONS:
        return (
            PreExecutionPlanDispositionConflictReasonV1.PLANNING_SELECTION_NOT_PERMITTED
        )
    if reason in _PLANNING_RELATION_REASONS:
        return PreExecutionPlanDispositionConflictReasonV1.PLANNING_RELATION_CONFLICT
    return None


def _row_parameters(value: _rows._CognitiveRowValue) -> tuple[object, ...]:
    return tuple(value.to_mapping().values())


def _read_rows(
    capability: object,
    *,
    table: str,
    columns: tuple[str, ...],
    where: str,
    parameters: tuple[object, ...],
    limit: int,
) -> list[object]:
    if table not in _rows._TABLE_ORDER or type(columns) is not tuple:
        raise _database_integrity_failure() from None
    sql = f"SELECT {', '.join(columns)} FROM {table} WHERE {where} LIMIT {limit}"
    return _execute_select_fetch_bounded(
        capability=typing.cast(_MutationReadCapability, capability),
        sql=sql,
        parameters=parameters,
        limit=limit,
    )


def _read_exact_row(
    capability: object,
    *,
    table: str,
    where: str,
    parameters: tuple[object, ...],
) -> _rows._CognitiveRowValue | None:
    columns = _rows._TABLE_COLUMNS[table]
    fetched = _read_rows(
        capability,
        table=table,
        columns=columns,
        where=where,
        parameters=parameters,
        limit=2,
    )
    if len(fetched) > 1:
        raise _database_integrity_failure() from None
    if not fetched:
        return None
    try:
        return _rows._row_value_from_tuple(table, fetched[0])
    except _CognitiveProposalContractViolation:
        raise _database_integrity_failure() from None


def _read_receipt(
    capability: object,
    mutation_ref: str,
) -> _rows.DevelopmentCognitiveMutationReceiptRowValue | None:
    row = _read_exact_row(
        capability,
        table=_rows._TABLE_ORDER[8],
        where="mutation_ref = ?",
        parameters=(mutation_ref,),
    )
    if row is None:
        return None
    if type(row) is not _rows.DevelopmentCognitiveMutationReceiptRowValue:
        raise _database_integrity_failure() from None
    return row


def _selection_key_from_command(
    command: RecordPreExecutionPlanDispositionCommandV1,
) -> tuple[tuple[str, str], ...]:
    return tuple(
        (name, typing.cast(str, object.__getattribute__(command, name)))
        for name in _K8_FIELDS
    )


def _selection_key_values(
    command: RecordPreExecutionPlanDispositionCommandV1,
) -> tuple[str, ...]:
    return tuple(value for _name, value in _selection_key_from_command(command))


def _read_selection_head(
    capability: object,
    command: RecordPreExecutionPlanDispositionCommandV1,
) -> _rows.DevelopmentPreExecutionSelectionHeadRowValue | None:
    row = _read_exact_row(
        capability,
        table=_rows._TABLE_ORDER[7],
        where=_K8_WHERE,
        parameters=typing.cast(tuple[object, ...], _selection_key_values(command)),
    )
    if row is None:
        return None
    if type(row) is not _rows.DevelopmentPreExecutionSelectionHeadRowValue:
        raise _database_integrity_failure() from None
    return row


def _read_evidence_rows(
    capability: object,
    proposal_ref: str,
) -> tuple[_rows.DevelopmentModelProposalEvidenceBindingRowValue, ...]:
    fetched = _execute_select_fetch_bounded(
        capability=typing.cast(_MutationReadCapability, capability),
        sql=_EVIDENCE_SELECT,
        parameters=(proposal_ref,),
        limit=16,
    )
    if len(fetched) not in (14, 15):
        raise _database_integrity_failure() from None
    result: list[_rows.DevelopmentModelProposalEvidenceBindingRowValue] = []
    try:
        for raw in fetched:
            row = _rows._row_value_from_tuple(_rows._TABLE_ORDER[5], raw)
            if type(row) is not _rows.DevelopmentModelProposalEvidenceBindingRowValue:
                raise _database_integrity_failure() from None
            result.append(row)
    except _CognitiveProposalContractViolation:
        raise _database_integrity_failure() from None
    roles = tuple(row.evidence_role for row in result)
    mandatory = _semantic._EVIDENCE_ROLES
    expected = (
        *mandatory,
        *(() if len(result) == 14 else (_semantic._READINESS_ROLE,)),
    )
    if roles != expected or tuple(row.role_rank for row in result) != tuple(
        range(5, 5 + len(result))
    ):
        raise _database_integrity_failure() from None
    return tuple(result)


def _validate_bundle_relations(
    bundle: _semantic.PreExecutionProposalSelectionBundleV1,
) -> None:
    observation = bundle.authority_observation
    expected = bundle.authority_expected_binding
    observation_mapping = observation.to_mapping()
    expected_mapping = expected.to_mapping()
    if not _exact_equal(
        {
            name: observation_mapping[name]
            for name in _semantic._AUTHORITY_EXPECTED_BINDING_FIELDS
        },
        expected_mapping,
    ):
        _violate("authority_observation_binding_mismatch")
    context = bundle.planning_context
    context_mapping = context.to_mapping()
    context_observation = {
        "authority_selection_observation_schema_id": observation.schema_id,
        "authority_selection_observation_ref": observation.authority_observation_ref,
        "authoritative_subject_kind": observation.authoritative_subject_kind,
        "authoritative_subject_ref": observation.authoritative_subject_ref,
        "authority_observation_state": observation.observation_state,
        "authority_observation_version": observation.observation_version,
        "authority_observation_issued_at": observation.authority_observation_issued_at,
        "authority_observation_expires_at": observation.authority_observation_expires_at,
        "source_authority_ref": observation.source_authority_ref,
        "verification_evidence_ref": observation.verification_evidence_ref,
        "verification_evidence_digest": observation.verification_evidence_digest,
        "authority_selection_observation_digest": observation.authority_observation_digest,
    }
    if any(
        context_mapping[name] != member for name, member in context_observation.items()
    ):
        _violate("authority_observation_binding_mismatch")
    if (
        context.authoritative_subject_kind != "effect_intent"
        or context.authoritative_subject_ref != context.effect_intent_ref
    ):
        _violate("authority_observation_binding_mismatch")

    source = bundle.source_invocation
    binding = bundle.private_artifact_binding
    artifact = bundle.private_artifact
    proposal = bundle.model_proposal
    projection = bundle.safe_projection
    evidence_set = bundle.evidence_set
    relations = (
        (source.proposal_phase, "pre_execution_plan"),
        (source.model_contract_ref, proposal.model_contract_ref),
        (source.model_contract_digest, proposal.model_contract_digest),
        (source.model_configuration_ref, proposal.model_configuration_ref),
        (source.model_configuration_digest, proposal.model_configuration_digest),
        (source.context_schema_id, context.schema_id),
        (source.context_ref, context.planning_context_ref),
        (source.context_digest, context.planning_context_digest),
        (source.artifact_schema_id, artifact.schema_id),
        (source.artifact_ref, binding.artifact_ref),
        (source.artifact_digest, binding.artifact_digest),
        (binding.proposal_phase, "pre_execution_plan"),
        (binding.artifact_schema_id, artifact.schema_id),
        (binding.artifact_ref, artifact.artifact_ref),
        (binding.artifact_digest, artifact.artifact_digest),
        (binding.safe_projection_schema_id, projection.schema_id),
        (binding.safe_projection_digest, projection.safe_projection_digest),
        (artifact.proposal_phase, "pre_execution_plan"),
        (artifact.proposal_ref, proposal.proposal_ref),
        (artifact.planning_context_ref, context.planning_context_ref),
        (artifact.recommendation, proposal.recommendation),
        (artifact.reason_code, proposal.reason_code),
        (projection.proposal_ref, proposal.proposal_ref),
        (projection.proposal_phase, "pre_execution_plan"),
        (projection.artifact_schema_id, artifact.schema_id),
        (projection.artifact_ref, artifact.artifact_ref),
        (projection.artifact_digest, artifact.artifact_digest),
        (projection.planning_context_schema_id, context.schema_id),
        (projection.planning_context_ref, context.planning_context_ref),
        (projection.planning_context_digest, context.planning_context_digest),
        (projection.recommendation, proposal.recommendation),
        (projection.reason_code, proposal.reason_code),
        (proposal.proposal_phase, "pre_execution_plan"),
        (proposal.source_invocation_ref, source.source_invocation_ref),
        (proposal.source_invocation_digest, source.source_invocation_digest),
        (proposal.context_schema_id, context.schema_id),
        (proposal.context_ref, context.planning_context_ref),
        (proposal.context_digest, context.planning_context_digest),
        (proposal.artifact_schema_id, artifact.schema_id),
        (proposal.artifact_ref, artifact.artifact_ref),
        (proposal.artifact_digest, artifact.artifact_digest),
        (proposal.safe_projection_schema_id, projection.schema_id),
        (proposal.safe_projection_digest, projection.safe_projection_digest),
        (proposal.evidence_set_ref, evidence_set.evidence_set_ref),
        (proposal.evidence_set_digest, evidence_set.evidence_set_digest),
        (evidence_set.proposal_ref, proposal.proposal_ref),
        (evidence_set.proposal_phase, "pre_execution_plan"),
    )
    if any(left != right for left, right in relations):
        _violate("preselection_timestamp_digest_mismatch")
    if binding.artifact_canonical_byte_length != len(
        _canonical_bytes(artifact.to_mapping())
    ):
        _violate("private_plan_artifact_size_invalid")
    derived_projection = _semantic._derive_pre_execution_safe_projection_mapping(
        artifact, binding, context, proposal
    )
    if not _exact_equal(projection.to_mapping(), derived_projection):
        _violate("safe_projection_derivation_mismatch")
    if tuple(row.to_mapping() for row in bundle.evidence_bindings) != tuple(
        row.to_mapping() for row in evidence_set.entries
    ):
        _violate("preselection_timestamp_digest_mismatch")
    if any(
        row.proposal_ref != proposal.proposal_ref
        or row.proposal_phase != "pre_execution_plan"
        or row.evidence_set_ref != evidence_set.evidence_set_ref
        for row in bundle.evidence_bindings
    ):
        _violate("preselection_timestamp_digest_mismatch")

    evidence_by_role = {row.evidence_role: row for row in bundle.evidence_bindings}
    evidence_context_bindings = (
        (
            "standing_policy",
            context.standing_policy_ref,
            context.standing_policy_digest,
        ),
        ("risk_lane", context.risk_lane_ref, context.risk_lane_digest),
        (
            "authorized_path_scope",
            evidence_by_role["authorized_path_scope"].evidence_ref,
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
            "validation_requirement",
            context.validation_requirement_ref,
            context.validation_requirement_digest,
        ),
        (
            "review_requirement",
            context.review_requirement_ref,
            context.review_requirement_digest,
        ),
    )
    if any(
        evidence_by_role[role].evidence_ref != expected_ref
        or evidence_by_role[role].evidence_digest != expected_digest
        for role, expected_ref, expected_digest in evidence_context_bindings
    ):
        _violate("preselection_timestamp_digest_mismatch")
    authority_rows = tuple(
        row for row in bundle.evidence_bindings if row.role_rank == 15
    )
    if (
        len(authority_rows) != 1
        or authority_rows[0].evidence_role != "authority_selection_observation"
        or authority_rows[0].evidence_ref != observation.authority_observation_ref
        or authority_rows[0].evidence_digest != observation.authority_observation_digest
    ):
        _violate("authority_observation_binding_mismatch")
    readiness = tuple(row for row in bundle.evidence_bindings if row.role_rank == 19)
    readiness_present = context.qualified_remote_host_readiness_ref is not None
    if readiness_present != (len(readiness) == 1):
        _violate("physical_family_readiness_mismatch")
    if readiness and (
        readiness[0].evidence_ref != context.qualified_remote_host_readiness_ref
        or readiness[0].evidence_digest
        != context.qualified_remote_host_readiness_digest
    ):
        _violate("physical_family_readiness_mismatch")

    attempt = bundle.attempt_fence
    effect = bundle.effect_fence
    attempt_effects = _require_canonical_effect_class_json(
        context.attempt_fence_allowed_effect_classes_json,
        "preselection_timestamp_digest_mismatch",
    )
    effect_effects = _require_canonical_effect_class_json(
        context.effect_fence_allowed_effect_classes_json,
        "preselection_timestamp_digest_mismatch",
    )
    if not (
        attempt.program_ref == context.program_ref
        and attempt.program_version_ref == context.program_version_ref
        and attempt.accepted_intent_revision_ref == context.accepted_intent_revision_ref
        and attempt.work_item_ref == context.work_item_ref
        and attempt.work_item_revision_ref == context.work_item_revision_ref
        and attempt.semantic_attempt_ref == context.semantic_attempt_ref
        and attempt.repository_ref == context.repository_ref
        and attempt.base_git_object_format == context.base_git_object_format
        and attempt.base_git_oid == context.base_git_oid
        and attempt.parent_standing_grant_ref == context.standing_grant_ref
        and attempt.parent_standing_grant_digest == context.standing_grant_digest
        and attempt.attempt_authorization_ref == context.attempt_authorization_ref
        and attempt.attempt_authorization_digest == context.attempt_authorization_digest
        and attempt.attempt_fence_ref == context.attempt_fence_ref
        and attempt.attempt_fence_digest == context.attempt_fence_digest
        and attempt.expires_at == context.attempt_fence_expires_at
        and attempt.global_stop_ref == context.global_stop_ref
        and attempt.global_stop_version == context.global_stop_version
        and effect.effect_fence_ref == context.effect_fence_ref
        and effect.effect_fence_digest == context.effect_fence_digest
        and effect.parent_standing_grant_ref == context.standing_grant_ref
        and effect.parent_standing_grant_digest == context.standing_grant_digest
        and effect.effect_authorization_ref == context.effect_authorization_ref
        and effect.effect_authorization_digest == context.effect_authorization_digest
        and effect.attempt_fence_ref == attempt.attempt_fence_ref
        and effect.attempt_fence_digest == attempt.attempt_fence_digest
        and effect.program_ref == context.program_ref
        and effect.program_version_ref == context.program_version_ref
        and effect.accepted_intent_revision_ref == context.accepted_intent_revision_ref
        and effect.work_item_ref == context.work_item_ref
        and effect.work_item_revision_ref == context.work_item_revision_ref
        and effect.semantic_attempt_ref == context.semantic_attempt_ref
        and effect.effect_intent_ref == context.effect_intent_ref
        and effect.effect_class == "author_candidate"
        and effect.command_ref == context.author_command_ref
        and effect.command_digest == context.author_command_digest
        and effect.candidate_ref == context.candidate_ref
        and effect.repository_ref == context.repository_ref
        and effect.base_git_object_format == context.base_git_object_format
        and effect.base_git_oid == context.base_git_oid
        and effect.expires_at == context.effect_fence_expires_at
        and effect.global_stop_ref == context.global_stop_ref
        and effect.global_stop_version == context.global_stop_version
        and tuple(attempt.allowed_effect_classes) == tuple(attempt_effects)
        and (effect.effect_class,) == tuple(effect_effects)
    ):
        _violate("preselection_timestamp_digest_mismatch")
    paths = artifact.affected_authorized_paths
    if any(
        path not in attempt.path_ceiling or path not in effect.path_ceiling
        for path in paths
    ):
        _violate("private_plan_nested_collection_invalid")
    proposed = artifact.proposed_resource_and_effect_use
    if any(
        effect_class not in attempt.allowed_effect_classes
        for effect_class in proposed.allowed_effect_classes
    ):
        _violate("private_plan_nested_collection_invalid")
    if any(
        effect_class != effect.effect_class
        for effect_class in proposed.allowed_effect_classes
    ):
        _violate("private_plan_nested_collection_invalid")
    for field_name in _semantic._CEILING_FIELDS:
        amount = object.__getattribute__(proposed, field_name)
        if amount > object.__getattribute__(
            attempt.aggregate_ceilings, field_name
        ) or amount > object.__getattribute__(effect.effect_ceilings, field_name):
            _violate("private_plan_nested_collection_invalid")


def _validate_temporal_relations(
    bundle: _semantic.PreExecutionProposalSelectionBundleV1,
    timestamp: object,
) -> str:
    decision_time = _require_utc_second(timestamp, "preselection_chronology_invalid")
    evidence_times = tuple(row.evidence_bound_at for row in bundle.evidence_bindings)
    if not evidence_times or any(
        value != evidence_times[0] for value in evidence_times
    ):
        _violate("preselection_chronology_invalid")
    observation = bundle.authority_observation
    chronology = (
        observation.authority_observation_issued_at,
        bundle.planning_context.planning_context_captured_at,
        bundle.source_invocation.source_invocation_started_at,
        bundle.source_invocation.source_invocation_completed_at,
        bundle.private_artifact_binding.artifact_validated_at,
        evidence_times[0],
        bundle.model_proposal.proposal_created_at,
        decision_time,
    )
    if tuple(sorted(chronology)) != chronology or not chronology[-2] < decision_time:
        _violate("preselection_chronology_invalid")
    if (
        not observation.authority_observation_issued_at
        < observation.authority_observation_expires_at
    ):
        _violate("authority_observation_window_invalid")
    if not decision_time < observation.authority_observation_expires_at:
        _violate("authority_observation_expired")
    if not decision_time < bundle.attempt_fence.expires_at:
        _violate("attempt_fence_expired")
    if not decision_time < bundle.effect_fence.expires_at:
        _violate("effect_fence_expired")
    return decision_time


_C2B3D_RECEIPT_BY_EFFECT_SELECT = (
    f"SELECT {', '.join(_decision_rows._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS)} "
    "FROM development_mutation_receipts "
    "WHERE program_ref = ? AND result_effect_intent_ref = ? "
    "AND mutation_family = 'establish_development_author_effect_intent' LIMIT 2"
)


def _read_c2b3d_author_receipt(
    capability: object,
    context: _semantic.PreExecutionPlanningContextV1,
) -> _decision_rows.DevelopmentMutationReceiptRowValue | None:
    fetched = _execute_select_fetch_two(
        capability=typing.cast(_MutationReadCapability, capability),
        sql=_C2B3D_RECEIPT_BY_EFFECT_SELECT,
        parameters=(context.program_ref, context.effect_intent_ref),
    )
    if not fetched:
        return None
    if len(fetched) != 1:
        raise _database_integrity_failure() from None
    try:
        return _decision_rows.development_mutation_receipt_row_value_from_row_tuple(
            fetched[0]
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None


def _current_c2b3d_lineage_is_exact(
    capability: object,
    context: _semantic.PreExecutionPlanningContextV1,
) -> tuple[bool, tuple[str, ...] | None]:
    """Prove the exact current C2B3D family and return WorkSpec path order."""

    try:
        program = _read_development_program_head_and_current_version(
            capability, context.program_ref
        )
        work = _read_development_work_item_head_and_revision_by_exact_ref(
            capability,
            context.program_ref,
            context.work_item_ref,
            context.work_item_revision_ref,
        )
        work_binding = _read_development_work_spec_safe_binding(
            capability,
            context.program_ref,
            context.program_version_ref,
            context.work_item_ref,
            context.work_item_revision_ref,
        )
        aggregate = _read_development_attempt_fence_command_effect_aggregate(
            capability,
            context.program_ref,
            context.semantic_attempt_ref,
            context.effect_intent_ref,
        )
        authority = _read_development_authority_evaluation_by_exact_ref(
            capability,
            context.program_ref,
            context.authority_evaluation_ref,
        )
        effect_head = _read_development_effect_head(
            capability, context.program_ref, context.effect_intent_ref
        )
        delivery_head = _read_development_delivery_head(
            capability, context.program_ref, context.effect_intent_ref
        )
        receipt = _read_c2b3d_author_receipt(capability, context)
        if (
            type(program) is not DevelopmentProgramHeadAndCurrentVersionRead
            or type(work) is not DevelopmentWorkItemHeadAndRevisionRead
            or type(work_binding)
            is not _program_rows.DevelopmentWorkSpecBindingRowValue
            or type(aggregate) is not DevelopmentAttemptFenceCommandEffectRead
            or type(authority)
            is not _effect_rows.DevelopmentAuthorityEvaluationRowValue
            or type(effect_head) is not _effect_rows.DevelopmentEffectHeadRowValue
            or type(delivery_head) is not DevelopmentDeliveryHeadAndCurrentAttemptRead
            or type(receipt) is not _decision_rows.DevelopmentMutationReceiptRowValue
        ):
            return False, None

        projection = work_binding.safe_projection
        attempt = aggregate.attempt_fence.attempt_fence
        effect = aggregate.author_effect_fence.effect_fence
        worker_command = aggregate.author_command.worker_command
        delivery = delivery_head.current_delivery_attempt
        validation = DevelopmentValidationRequirementEvidenceV1(
            schema_id=(
                "governed-execution.nwp-development-validation-requirement-evidence.v1"
            ),
            requirement_ref=context.validation_requirement_ref,
            requirement_digest=context.validation_requirement_digest,
            work_spec_ref=context.work_spec_ref,
            work_spec_digest=context.work_spec_digest,
            safe_evidence_digest=context.validation_safe_evidence_digest,
        )
        review = DevelopmentReviewRequirementEvidenceV1(
            schema_id=(
                "governed-execution.nwp-development-review-requirement-evidence.v1"
            ),
            requirement_ref=context.review_requirement_ref,
            requirement_digest=context.review_requirement_digest,
            work_spec_ref=context.work_spec_ref,
            work_spec_digest=context.work_spec_digest,
            safe_evidence_digest=context.review_safe_evidence_digest,
        )
        authorization_binding = _development_effect_authorization_safe_binding(
            parent_standing_grant_ref=effect.parent_standing_grant_ref,
            parent_standing_grant_digest=effect.parent_standing_grant_digest,
            effect_authorization_ref=effect.effect_authorization_ref,
            effect_authorization_digest=effect.effect_authorization_digest,
            attempt_fence_ref=effect.attempt_fence_ref,
            attempt_fence_digest=effect.attempt_fence_digest,
            semantic_attempt_ref=effect.semantic_attempt_ref,
            effect_intent_ref=effect.effect_intent_ref,
            effect_class=effect.effect_class,
            path_ceiling=effect.path_ceiling,
            effect_ceilings=effect.effect_ceilings,
            expires_at=effect.expires_at,
            global_stop_ref=effect.global_stop_ref,
            global_stop_version=effect.global_stop_version,
        )
        reconstructed = DevelopmentAuthorEffectEstablishmentCommandV1(
            schema_id=(
                "governed-execution.nwp-establish-development-author-effect-intent-command.v1"
            ),
            mutation_ref=receipt.mutation_ref,
            program_ref=context.program_ref,
            program_version_ref=context.program_version_ref,
            program_version_number=context.program_version_number,
            accepted_intent_revision_ref=context.accepted_intent_revision_ref,
            work_item_ref=context.work_item_ref,
            work_item_revision_ref=context.work_item_revision_ref,
            basis_decision_ref=context.basis_decision_ref,
            basis_decision_digest=context.basis_decision_digest,
            semantic_attempt_ref=context.semantic_attempt_ref,
            candidate_ref=context.candidate_ref,
            attempt_number=context.attempt_number,
            attempt_fence_ref=context.attempt_fence_ref,
            effect_intent_ref=context.effect_intent_ref,
            effect_fence_ref=context.effect_fence_ref,
            command_ref=context.author_command_ref,
            authority_evaluation_ref=context.authority_evaluation_ref,
            delivery_attempt_ref=context.delivery_attempt_ref,
            adapter_safe_correlation_ref=delivery.adapter_safe_correlation_ref,
            coding_global_stop_ref=context.global_stop_ref,
            coding_global_stop_version=context.global_stop_version,
            capsule_schema_id=worker_command.capsule_schema_id,
            capsule_profile_ref=worker_command.capsule_profile_ref,
            privacy_classification=worker_command.privacy_classification,
            redaction_profile_ref=worker_command.redaction_profile_ref,
            work_spec_safe_projection=projection,
            validation_requirement_evidence=validation,
            review_requirement_evidence=review,
            attempt_fence=attempt,
            effect_authorization_safe_binding=authorization_binding,
            worker_command=worker_command,
            effect_fence=effect,
            delivery_envelope=delivery.delivery_envelope,
            command_digest=receipt.command_digest,
        )
        if not _genesis_basis_is_current_and_exact(capability, reconstructed):
            return False, None
        _read_and_verify_exact_author_effect_family(
            capability=capability,
            command=reconstructed,
            receipt=receipt,
        )

        actual_lineage = CanonicalC2B3DLineage(
            program_ref=reconstructed.program_ref,
            program_version_ref=reconstructed.program_version_ref,
            program_version_number=reconstructed.program_version_number,
            accepted_intent_revision_ref=reconstructed.accepted_intent_revision_ref,
            work_item_ref=reconstructed.work_item_ref,
            work_item_revision_ref=reconstructed.work_item_revision_ref,
            semantic_attempt_ref=reconstructed.semantic_attempt_ref,
            semantic_attempt_digest=aggregate.semantic_attempt.semantic_attempt_digest,
            attempt_number=reconstructed.attempt_number,
            candidate_ref=reconstructed.candidate_ref,
            basis_decision_ref=reconstructed.basis_decision_ref,
            basis_decision_digest=reconstructed.basis_decision_digest,
            work_spec_ref=projection.work_spec_ref,
            work_spec_digest=projection.work_spec_digest,
            work_spec_safe_projection_digest=projection.safe_projection_digest,
            effect_intent_ref=reconstructed.effect_intent_ref,
            effect_intent_digest=aggregate.effect_intent.effect_intent_digest,
            author_command_ref=reconstructed.command_ref,
            author_command_digest=aggregate.author_command.command_digest,
            standing_grant_ref=attempt.parent_standing_grant_ref,
            standing_grant_digest=attempt.parent_standing_grant_digest,
            attempt_authorization_ref=attempt.attempt_authorization_ref,
            attempt_authorization_digest=attempt.attempt_authorization_digest,
            effect_authorization_ref=effect.effect_authorization_ref,
            effect_authorization_digest=effect.effect_authorization_digest,
            attempt_fence_ref=attempt.attempt_fence_ref,
            attempt_fence_digest=attempt.attempt_fence_digest,
            effect_fence_ref=effect.effect_fence_ref,
            effect_fence_digest=effect.effect_fence_digest,
            delivery_attempt_ref=delivery.delivery_attempt_ref,
            delivery_envelope_digest=delivery.delivery_envelope_digest,
            delivery_attempt_digest=delivery.delivery_attempt_digest,
            authority_evaluation_ref=authority.authority_evaluation_ref,
            authority_evaluation_digest=authority.authority_evaluation_digest,
        )
        head = program.program_head
        work_head = work.work_item_head
        current_effect_head = effect_head
        current_delivery_head = delivery_head.delivery_head
        exact = bool(
            _exact_equal(
                _lineage_from_context(context).to_mapping(),
                actual_lineage.to_mapping(),
            )
            and head.head_revision == context.expected_program_head_revision
            and head.program_state == "active"
            and work.is_current
            and work_head.head_revision == context.expected_work_item_head_revision
            and work_head.work_state == "planned"
            and current_effect_head.current_effect_fence_ref
            == context.expected_effect_head_fence_ref
            and current_effect_head.head_revision
            == context.expected_effect_head_revision
            and current_effect_head.head_digest == context.expected_effect_head_digest
            and current_delivery_head.current_delivery_attempt_ref
            == context.expected_delivery_head_attempt_ref
            and current_delivery_head.head_revision
            == context.expected_delivery_head_revision
            and current_delivery_head.head_digest
            == context.expected_delivery_head_digest
            and projection.repository_ref == context.repository_ref
            and projection.base_git_object_format == context.base_git_object_format
            and projection.base_git_oid == context.base_git_oid
            and projection.validation_requirement_ref
            == context.validation_requirement_ref
            and projection.review_requirement_ref == context.review_requirement_ref
            and attempt.expires_at == context.attempt_fence_expires_at
            and effect.expires_at == context.effect_fence_expires_at
            and _canonical_bytes(tuple(attempt.allowed_effect_classes)).decode("utf-8")
            == context.attempt_fence_allowed_effect_classes_json
            and _canonical_bytes((effect.effect_class,)).decode("utf-8")
            == context.effect_fence_allowed_effect_classes_json
        )
        return exact, tuple(projection.authorized_paths) if exact else None
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except SQLiteMutationStoreError:
        raise
    except Exception:
        return False, None


_IDENTITY_FIELDS = {
    table: tuple(
        fields
        for candidate_table, fields in _RECOVERY_PROBE_IDENTITY_SHAPES
        if candidate_table == table
    )
    for table in _rows._TABLE_ORDER
}
assert sum(len(items) for items in _IDENTITY_FIELDS.values()) == 30


def _identity_locators_for_rows(
    rows: tuple[_rows.CanonicalCognitivePhysicalRow, ...],
) -> tuple[tuple[str, tuple[tuple[str, object], ...]], ...]:
    by_table: dict[str, list[dict[str, object]]] = {
        table: [] for table in _rows._TABLE_ORDER
    }
    for member in rows:
        by_table[member.table].append(member.values.to_mapping())
    locators: list[tuple[str, tuple[tuple[str, object], ...]]] = []
    for table in _rows._TABLE_ORDER:
        selected = by_table[table][0]
        for identity in _IDENTITY_FIELDS[table]:
            locators.append((table, tuple((name, selected[name]) for name in identity)))
    return tuple(locators)


def _any_identity_collision(
    capability: object,
    locators: tuple[tuple[str, tuple[tuple[str, object], ...]], ...],
    *,
    allowed_head: _rows.DevelopmentPreExecutionSelectionHeadRowValue | None,
    evidence_member_locators: tuple[
        tuple[
            tuple[tuple[str, object], ...],
            tuple[tuple[str, object], ...],
        ],
        ...,
    ] = (),
) -> bool:
    for table, locator in locators:
        where = " AND ".join(f"{name} = ?" for name, _value in locator)
        parameters = tuple(value for _name, value in locator)
        fetched = _read_rows(
            capability,
            table=table,
            columns=_rows._TABLE_COLUMNS[table],
            where=where,
            parameters=parameters,
            limit=2,
        )
        if fetched:
            if (
                table == _rows._TABLE_ORDER[7]
                and allowed_head is not None
                and len(fetched) == 1
            ):
                try:
                    observed = _rows._row_value_from_tuple(table, fetched[0])
                except _CognitiveProposalContractViolation:
                    return True
                if _exact_equal(observed.to_mapping(), allowed_head.to_mapping()):
                    continue
            return True
    evidence_table = _rows._TABLE_ORDER[5]
    for route_pair in evidence_member_locators:
        for locator in route_pair:
            where = " AND ".join(f"{name} = ?" for name, _value in locator)
            fetched = _read_rows(
                capability,
                table=evidence_table,
                columns=_rows._TABLE_COLUMNS[evidence_table],
                where=where,
                parameters=tuple(value for _name, value in locator),
                limit=2,
            )
            if fetched:
                return True
    return False


def _preclock_identity_locators(
    command: RecordPreExecutionPlanDispositionCommandV1,
    bundle: _semantic.PreExecutionProposalSelectionBundleV1,
    current_head: _rows.DevelopmentPreExecutionSelectionHeadRowValue | None,
) -> tuple[tuple[str, tuple[tuple[str, object], ...]], ...]:
    del current_head
    return _build_pre_execution_plan_disposition_recovery_probe(
        command, bundle
    ).identity_locators


def _head_preimage_matches(
    command: RecordPreExecutionPlanDispositionCommandV1,
    head: _rows.DevelopmentPreExecutionSelectionHeadRowValue | None,
) -> bool:
    if head is None:
        return bool(
            command.expected_current_selection_revision is None
            and command.expected_current_selection_head_digest is None
            and command.supersedes_disposition_ref is None
        )
    return bool(
        command.expected_current_selection_revision == head.head_revision
        and command.expected_current_selection_head_digest == head.head_digest
        and command.supersedes_disposition_ref == head.current_disposition_ref
    )


def _resolve_pre_execution_plan_disposition_after_fencing(
    *,
    capability: object,
    mutation_ref: object,
    mutation_command_digest: object,
    bundle: object,
    disposition_identity: object,
    recovery_probe: object,
) -> (
    PreExecutionPlanDispositionResultV1
    | PreExecutionPlanDispositionConflictV1
    | _FreshPreExecutionPlanDisposition
):
    try:
        checked_ref = _require_safe_ref(
            mutation_ref, "cognitive_mutation_identity_invalid"
        )
        checked_digest = _require_sha256(
            mutation_command_digest, "cognitive_mutation_identity_invalid"
        )
        checked_probe = _require_exact_recovery_probe(recovery_probe)
        if not (
            checked_probe.command.mutation_ref == checked_ref
            and checked_probe.command.mutation_command_digest == checked_digest
        ):
            _violate("recovery_unresolved")
    except _CognitiveProposalContractViolation:
        raise _database_integrity_failure() from None

    receipt = _read_receipt(capability, checked_ref)
    if receipt is not None:
        # Persisted-family integrity and ancestry are proved before digest
        # comparison, preventing replay-address disclosure on corruption.
        try:
            persisted = _read_and_verify_persisted_family(
                capability=capability,
                receipt=receipt,
            )
        except _LineageProofOverflow:
            raise _database_integrity_failure() from None
        if receipt.command_digest != checked_digest:
            return PreExecutionPlanDispositionConflictV1(
                reason=PreExecutionPlanDispositionConflictReasonV1.MUTATION_REF_REUSE_CONFLICT,
                mutation_ref=checked_ref,
                command_digest=checked_digest,
                program_ref=receipt.program_ref,
            )
        if not (
            _exact_equal(
                persisted.command.to_mapping(), checked_probe.command.to_mapping()
            )
            and _exact_equal(
                persisted.recovery_probe.to_mapping(), checked_probe.to_mapping()
            )
        ):
            raise _database_integrity_failure() from None
        return persisted.result

    try:
        checked_bundle = _semantic._require_exact_pre_execution_bundle(bundle)
        command = _record_command_from_ingress(
            checked_ref,
            checked_digest,
            checked_bundle,
            disposition_identity,
        )
        expected_probe = _build_pre_execution_plan_disposition_recovery_probe(
            command, checked_bundle
        )
        if not _exact_equal(expected_probe.to_mapping(), checked_probe.to_mapping()):
            raise _database_integrity_failure() from None
    except _CognitiveProposalContractViolation as violation:
        if violation.reason == "proposal_disposition_identity_collapse":
            try:
                checked_bundle = _semantic._require_exact_pre_execution_bundle(bundle)
                context = checked_bundle.planning_context
                return PreExecutionPlanDispositionConflictV1(
                    reason=(
                        PreExecutionPlanDispositionConflictReasonV1.SEMANTIC_IDENTITY_CONFLICT
                    ),
                    mutation_ref=checked_ref,
                    command_digest=checked_digest,
                    program_ref=context.program_ref,
                )
            except _CognitiveProposalContractViolation:
                pass
        raise _database_integrity_failure() from None

    pending_relation_conflict: PreExecutionPlanDispositionConflictReasonV1 | None = None
    try:
        _validate_bundle_relations(checked_bundle)
    except _CognitiveProposalContractViolation as violation:
        pending_relation_conflict = _relation_violation_conflict_reason(violation)
        if pending_relation_conflict is None:
            raise _database_integrity_failure() from None

    context = checked_bundle.planning_context
    exact_lineage, authorized_paths = _current_c2b3d_lineage_is_exact(
        capability, context
    )
    if not exact_lineage or authorized_paths is None:
        return _conflict(
            command,
            PreExecutionPlanDispositionConflictReasonV1.PLANNING_RELATION_CONFLICT,
        )

    stop_envelope = _read_global_stop_current(
        typing.cast(_MutationReadCapability, capability)
    )
    if type(stop_envelope) is not GlobalStopCurrentRecordEnvelope:
        raise _database_integrity_failure() from None
    stop = stop_envelope.state
    if (
        stop.stop_ref != context.global_stop_ref
        or stop.version != context.global_stop_version
    ):
        return _conflict(
            command,
            PreExecutionPlanDispositionConflictReasonV1.GLOBAL_STOP_VERSION_CONFLICT,
        )
    if stop.active:
        return _conflict(
            command,
            PreExecutionPlanDispositionConflictReasonV1.PLANNING_SELECTION_NOT_PERMITTED,
        )
    if context.global_stop_state != "clear" and pending_relation_conflict is None:
        pending_relation_conflict = (
            PreExecutionPlanDispositionConflictReasonV1.PLANNING_RELATION_CONFLICT
        )

    head = _read_selection_head(capability, command)
    if head is not None:
        expected_lineage = tuple(
            object.__getattribute__(checked_bundle.planning_context, name)
            for name in _L34_FIELDS
        )
        if (
            tuple(object.__getattribute__(head, name) for name in _L34_FIELDS)
            != expected_lineage
        ):
            return _conflict(
                command,
                PreExecutionPlanDispositionConflictReasonV1.SELECTION_HEAD_VERSION_CONFLICT,
            )
    if not _head_preimage_matches(command, head):
        return _conflict(
            command,
            PreExecutionPlanDispositionConflictReasonV1.SELECTION_HEAD_VERSION_CONFLICT,
        )

    artifact_paths = checked_bundle.private_artifact.affected_authorized_paths
    if (
        tuple(path for path in authorized_paths if path in artifact_paths)
        != artifact_paths
    ):
        pending_relation_conflict = (
            PreExecutionPlanDispositionConflictReasonV1.PLANNING_SELECTION_NOT_PERMITTED
        )
    expected_disposition = {
        "select_for_dispatch_gates": "selected_for_dispatch_gates",
        "defer": "deferred",
        "replan": "deferred",
        "block": "blocked",
        "terminal_reject": "blocked",
    }[checked_bundle.model_proposal.recommendation]
    if command.disposition != expected_disposition:
        pending_relation_conflict = (
            PreExecutionPlanDispositionConflictReasonV1.PLANNING_SELECTION_NOT_PERMITTED
        )
    if command.disposition == "selected_for_dispatch_gates" and any(
        risk.materiality == "blocking"
        for risk in checked_bundle.private_artifact.risks_and_uncertainties
    ):
        pending_relation_conflict = (
            PreExecutionPlanDispositionConflictReasonV1.PLANNING_SELECTION_NOT_PERMITTED
        )
    if pending_relation_conflict is not None:
        return _conflict(command, pending_relation_conflict)

    if _any_identity_collision(
        capability,
        checked_probe.identity_locators,
        allowed_head=head,
        evidence_member_locators=checked_probe.evidence_member_locators,
    ):
        return _conflict(
            command,
            PreExecutionPlanDispositionConflictReasonV1.SEMANTIC_IDENTITY_CONFLICT,
        )
    return _FreshPreExecutionPlanDisposition(
        command, checked_bundle, head, checked_probe
    )


def _mapping_in_order(table: str, values: dict[str, object]) -> dict[str, object]:
    columns = _rows._TABLE_COLUMNS[table]
    if set(values) != set(columns):
        raise _database_integrity_failure() from None
    return {name: values[name] for name in columns}


def _seal_row_mapping(
    table: str,
    values: dict[str, object],
) -> dict[str, object]:
    digest_field = _rows._DIGEST_FIELDS[table]
    provisional = dict(values)
    provisional.pop(digest_field, None)
    digest_identity = dict(provisional)
    if table == _rows._TABLE_ORDER[4]:
        try:
            digest_identity[
                "allowed_effect_classes"
            ] = _require_canonical_effect_class_json(
                digest_identity["allowed_effect_classes"],
                "physical_family_row_digest_mismatch",
            )
        except _CognitiveProposalContractViolation:
            raise _database_integrity_failure() from None
    provisional[digest_field] = _domain_separated_digest(
        _rows._DOMAINS[table], digest_identity
    )
    return _mapping_in_order(table, provisional)


def _physical_row(
    *,
    table: str,
    role: str,
    rank: int | None,
    values: dict[str, object],
) -> _rows.CanonicalCognitivePhysicalRow:
    try:
        row_value = _rows._row_value_from_mapping(table, values)
        return _rows.CanonicalCognitivePhysicalRow(
            table=table,
            role=role,
            rank=rank,
            ordinal=0,
            values=row_value,
        )
    except _CognitiveProposalContractViolation:
        raise _database_integrity_failure() from None


def _build_write_plan(
    fresh: _FreshPreExecutionPlanDisposition,
    transaction_timestamp: object,
) -> _PreExecutionPlanDispositionWritePlan:
    if type(fresh) is not _FreshPreExecutionPlanDisposition:
        raise _database_integrity_failure() from None
    try:
        timestamp = _validate_temporal_relations(fresh.bundle, transaction_timestamp)
    except _CognitiveProposalContractViolation as violation:
        if violation.reason in {
            "authority_observation_window_invalid",
            "authority_observation_expired",
            "attempt_fence_expired",
            "effect_fence_expired",
        }:
            raise _PlanningSelectionNotPermitted() from None
        raise _database_integrity_failure() from None
    command = fresh.command
    bundle = fresh.bundle
    context = bundle.planning_context
    lineage = {name: object.__getattribute__(context, name) for name in _L34_FIELDS}
    if fresh.current_head is None:
        prior_revision = -1
        prior_digest = None
        resulting_revision = 0
    else:
        prior_revision = fresh.current_head.head_revision
        prior_digest = fresh.current_head.head_digest
        resulting_revision = prior_revision + 1

    head_values = {
        "schema_id": _HEAD_SCHEMA,
        **lineage,
        "current_proposal_ref": command.proposal_ref,
        "current_disposition_ref": command.preassigned_disposition_ref,
        "current_disposition": command.disposition,
        "head_revision": resulting_revision,
        "updated_at": timestamp,
    }
    head_mapping = _seal_row_mapping(_rows._TABLE_ORDER[7], head_values)
    disposition_values = {
        "schema_id": _DISPOSITION_SCHEMA,
        "disposition_ref": command.preassigned_disposition_ref,
        "program_ref": context.program_ref,
        "program_version_ref": context.program_version_ref,
        "accepted_intent_revision_ref": context.accepted_intent_revision_ref,
        "work_item_ref": context.work_item_ref,
        "work_item_revision_ref": context.work_item_revision_ref,
        "proposal_ref": command.proposal_ref,
        "proposal_phase": "pre_execution_plan",
        "proposal_digest": command.proposal_digest,
        "planning_context_ref": command.planning_context_ref,
        "planning_context_digest": command.planning_context_digest,
        "evidence_set_ref": command.evidence_set_ref,
        "evidence_set_digest": command.evidence_set_digest,
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
        "disposition": command.disposition,
        "reason_code": command.disposition_reason_code,
        "supersedes_disposition_ref": command.supersedes_disposition_ref,
        "expected_selection_head_revision": command.expected_current_selection_revision,
        "expected_selection_head_digest": command.expected_current_selection_head_digest,
        "prior_selection_head_revision": prior_revision,
        "prior_selection_head_digest": prior_digest,
        "resulting_selection_head_revision": resulting_revision,
        "selection_head_postimage_digest": head_mapping["head_digest"],
        "authority_selection_observation_ref": bundle.authority_observation.authority_observation_ref,
        "authority_selection_observation_digest": bundle.authority_observation.authority_observation_digest,
        "coordinator_disposition_decided_at": timestamp,
        **{
            name: lineage[name]
            for name in _L34_FIELDS
            if name
            not in {
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
            }
        },
    }
    disposition_mapping = _seal_row_mapping(_rows._TABLE_ORDER[6], disposition_values)

    members: list[_rows.CanonicalCognitivePhysicalRow] = []
    members.append(
        _physical_row(
            table=_rows._TABLE_ORDER[0],
            role="source_invocation",
            rank=0,
            values=bundle.source_invocation.to_mapping(),
        )
    )
    members.append(
        _physical_row(
            table=_rows._TABLE_ORDER[1],
            role="planning_context",
            rank=1,
            values=context.to_mapping(),
        )
    )
    members.append(
        _physical_row(
            table=_rows._TABLE_ORDER[2],
            role="private_artifact_binding",
            rank=2,
            values=bundle.private_artifact_binding.to_mapping(),
        )
    )
    members.append(
        _physical_row(
            table=_rows._TABLE_ORDER[3],
            role="model_proposal",
            rank=3,
            values=bundle.model_proposal.to_mapping(),
        )
    )
    projection_mapping = bundle.safe_projection.to_mapping()
    projection_mapping["allowed_effect_classes"] = _canonical_bytes(
        bundle.safe_projection.allowed_effect_classes
    ).decode("utf-8")
    members.append(
        _physical_row(
            table=_rows._TABLE_ORDER[4],
            role="pre_execution_plan_projection",
            rank=4,
            values=projection_mapping,
        )
    )
    for binding in bundle.evidence_bindings:
        members.append(
            _physical_row(
                table=_rows._TABLE_ORDER[5],
                role=f"evidence.{binding.evidence_role}",
                rank=binding.role_rank,
                values=binding.to_mapping(),
            )
        )
    members.append(
        _physical_row(
            table=_rows._TABLE_ORDER[6],
            role="coordinator_disposition",
            rank=20,
            values=disposition_mapping,
        )
    )
    members.append(
        _physical_row(
            table=_rows._TABLE_ORDER[7],
            role="selection_head_postimage",
            rank=21,
            values=head_mapping,
        )
    )

    graph_entries = tuple(
        CognitiveMutationGraphEntryV1(
            role=member.role,
            rank=member.rank,
            ordinal=member.ordinal,
            table=member.table,
            locator=member.locator(),
            member_digest=member.member_digest,
        )
        for member in members
    )
    graph_fields: dict[str, object] = {
        "mutation_ref": command.mutation_ref,
        "command_digest": command.mutation_command_digest,
        "entries": tuple(entry.to_mapping() for entry in graph_entries),
    }
    graph = CognitiveMutationGraphV1(
        mutation_ref=command.mutation_ref,
        command_digest=command.mutation_command_digest,
        entries=graph_entries,
        mutation_graph_digest=_domain_separated_digest(_GRAPH_DOMAIN, graph_fields),
    )
    result_fields: dict[str, object] = {
        "schema_id": _RESULT_SCHEMA,
        "mutation_ref": command.mutation_ref,
        "command_digest": command.mutation_command_digest,
        "proposal_ref": command.proposal_ref,
        "disposition_ref": command.preassigned_disposition_ref,
        "disposition_digest": disposition_mapping["disposition_digest"],
        "disposition": command.disposition,
        "program_ref": command.program_ref,
        "semantic_attempt_ref": command.semantic_attempt_ref,
        "candidate_ref": command.candidate_ref,
        "effect_intent_ref": command.effect_intent_ref,
        "selection_head_revision": resulting_revision,
        "selection_head_digest": head_mapping["head_digest"],
        "authority_selection_observation_ref": bundle.authority_observation.authority_observation_ref,
        "authority_selection_observation_digest": bundle.authority_observation.authority_observation_digest,
        "mutation_graph_digest": graph.mutation_graph_digest,
        "recorded_at": timestamp,
    }
    result_fields["result_projection_digest"] = _domain_separated_digest(
        _RESULT_DOMAIN, result_fields
    )
    projection = PreExecutionPlanDispositionResultProjectionV1(**result_fields)
    receipt_values = {
        "schema_id": _RECEIPT_SCHEMA,
        "mutation_ref": command.mutation_ref,
        "mutation_family": _MUTATION_FAMILY,
        "command_schema_id": _COMMAND_SCHEMA,
        "command_digest": command.mutation_command_digest,
        "program_ref": command.program_ref,
        "proposal_ref": command.proposal_ref,
        "disposition_ref": command.preassigned_disposition_ref,
        "disposition_digest": disposition_mapping["disposition_digest"],
        "authority_selection_observation_ref": bundle.authority_observation.authority_observation_ref,
        "authority_selection_observation_digest": bundle.authority_observation.authority_observation_digest,
        "effect_intent_ref": command.effect_intent_ref,
        "selection_head_revision": resulting_revision,
        "selection_head_digest": head_mapping["head_digest"],
        "result_class": _RESULT_CLASS,
        "result_projection_digest": projection.result_projection_digest,
        "mutation_graph_digest": graph.mutation_graph_digest,
        "outcome": _OUTCOME,
        "committed_at": timestamp,
    }
    receipt_mapping = _seal_row_mapping(_rows._TABLE_ORDER[8], receipt_values)
    receipt_member = _physical_row(
        table=_rows._TABLE_ORDER[8], role="receipt", rank=None, values=receipt_mapping
    )
    members.append(receipt_member)
    result = PreExecutionPlanDispositionResultV1(
        projection=projection,
        receipt_digest=typing.cast(str, receipt_mapping["receipt_digest"]),
    )
    return _PreExecutionPlanDispositionWritePlan(
        command=command,
        rows=tuple(members),
        graph=graph,
        planned_result=result,
        recovery_probe=fresh.recovery_probe,
    )


def _execute_pre_execution_plan_disposition_writes(
    connection: sqlite3.Connection,
    plan: _PreExecutionPlanDispositionWritePlan,
) -> None:
    if (
        type(connection) is not sqlite3.Connection
        or type(plan) is not _PreExecutionPlanDispositionWritePlan
    ):
        raise _mutation_failed() from None
    for member in plan.rows:
        table = member.table
        row = member.values
        if table == _rows._TABLE_ORDER[7] and row.head_revision > 0:
            columns = _rows._TABLE_COLUMNS[table]
            mutable = (
                "current_proposal_ref",
                "current_disposition_ref",
                "current_disposition",
                "head_revision",
                "updated_at",
                "head_digest",
            )
            sql = (
                "UPDATE development_pre_execution_selection_heads SET "
                + ", ".join(f"{name} = ?" for name in mutable)
                + " WHERE "
                + _K8_WHERE
                + " AND current_disposition_ref = ? AND head_revision = ? AND head_digest = ?"
            )
            previous_revision = row.head_revision - 1
            disposition = next(
                item.values for item in plan.rows if item.table == _rows._TABLE_ORDER[6]
            )
            parameters = (
                *(object.__getattribute__(row, name) for name in mutable),
                *(object.__getattribute__(row, name) for name in _K8_FIELDS),
                disposition.supersedes_disposition_ref,
                previous_revision,
                disposition.prior_selection_head_digest,
            )
            try:
                cursor = connection.execute(sql, parameters)
                affected = cursor.rowcount
                cursor.close()
            except sqlite3.Error as exc:
                raise _classify_write_error(exc) from None
            if affected == 0:
                raise _SelectionHeadCASConflict() from None
            if affected != 1:
                raise _database_integrity_failure() from None
            continue
        columns = _rows._TABLE_COLUMNS[table]
        sql = (
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES "
            f"({', '.join('?' for _ in columns)})"
        )
        try:
            cursor = connection.execute(sql, _row_parameters(row))
            affected = cursor.rowcount
            cursor.close()
        except sqlite3.Error as exc:
            raise _classify_write_error(exc) from None
        if affected != 1:
            raise _database_integrity_failure() from None


class _SelectionHeadCASConflict(RuntimeError):
    __slots__ = ()


def _classify_write_error(error: sqlite3.Error) -> SQLiteMutationStoreError:
    code = getattr(error, "sqlite_errorcode", None)
    if type(code) is int and (code & 0xFF) in {
        sqlite3.SQLITE_CONSTRAINT,
        sqlite3.SQLITE_CORRUPT,
        sqlite3.SQLITE_MISMATCH,
        sqlite3.SQLITE_NOTADB,
        sqlite3.SQLITE_SCHEMA,
    }:
        return _database_integrity_failure()
    return _mutation_failed()


def _read_disposition_by_ref(
    capability: object,
    disposition_ref: str,
) -> _rows.DevelopmentPreExecutionDispositionRowValue:
    row = _read_exact_row(
        capability,
        table=_rows._TABLE_ORDER[6],
        where="disposition_ref = ?",
        parameters=(disposition_ref,),
    )
    if type(row) is not _rows.DevelopmentPreExecutionDispositionRowValue:
        raise _database_integrity_failure() from None
    return row


def _read_proposal_family_rows(
    capability: object,
    disposition: _rows.DevelopmentPreExecutionDispositionRowValue,
) -> tuple[_rows.CanonicalCognitivePhysicalRow, ...]:
    proposal = _read_exact_row(
        capability,
        table=_rows._TABLE_ORDER[3],
        where="proposal_ref = ?",
        parameters=(disposition.proposal_ref,),
    )
    if type(proposal) is not _rows.DevelopmentModelProposalRowValue:
        raise _database_integrity_failure() from None
    source = _read_exact_row(
        capability,
        table=_rows._TABLE_ORDER[0],
        where="source_invocation_ref = ?",
        parameters=(proposal.source_invocation_ref,),
    )
    context = _read_exact_row(
        capability,
        table=_rows._TABLE_ORDER[1],
        where="planning_context_ref = ?",
        parameters=(disposition.planning_context_ref,),
    )
    artifact = _read_exact_row(
        capability,
        table=_rows._TABLE_ORDER[2],
        where="artifact_ref = ?",
        parameters=(proposal.artifact_ref,),
    )
    projection = _read_exact_row(
        capability,
        table=_rows._TABLE_ORDER[4],
        where="proposal_ref = ?",
        parameters=(proposal.proposal_ref,),
    )
    if (
        type(source) is not _rows.DevelopmentModelSourceInvocationRowValue
        or type(context) is not _rows.DevelopmentPreExecutionPlanningContextRowValue
        or type(artifact) is not _rows.DevelopmentPrivateProposalArtifactBindingRowValue
        or type(projection) is not _rows.DevelopmentPreExecutionPlanProjectionRowValue
    ):
        raise _database_integrity_failure() from None
    if _l34_values(context) != _l34_values(disposition):
        raise _database_integrity_failure() from None
    evidence = _read_evidence_rows(capability, proposal.proposal_ref)
    relations = (
        (source.proposal_phase, proposal.proposal_phase),
        (source.model_contract_ref, proposal.model_contract_ref),
        (source.model_contract_digest, proposal.model_contract_digest),
        (source.model_configuration_ref, proposal.model_configuration_ref),
        (source.model_configuration_digest, proposal.model_configuration_digest),
        (source.context_schema_id, context.schema_id),
        (source.context_ref, context.planning_context_ref),
        (source.context_digest, context.planning_context_digest),
        (source.artifact_schema_id, artifact.artifact_schema_id),
        (source.artifact_ref, artifact.artifact_ref),
        (source.artifact_digest, artifact.artifact_digest),
        (artifact.proposal_phase, proposal.proposal_phase),
        (artifact.artifact_schema_id, proposal.artifact_schema_id),
        (artifact.artifact_ref, proposal.artifact_ref),
        (artifact.artifact_digest, proposal.artifact_digest),
        (artifact.safe_projection_schema_id, proposal.safe_projection_schema_id),
        (artifact.safe_projection_digest, proposal.safe_projection_digest),
        (projection.proposal_ref, proposal.proposal_ref),
        (projection.proposal_phase, proposal.proposal_phase),
        (projection.artifact_schema_id, artifact.artifact_schema_id),
        (projection.artifact_ref, artifact.artifact_ref),
        (projection.artifact_digest, artifact.artifact_digest),
        (projection.planning_context_schema_id, context.schema_id),
        (projection.planning_context_ref, context.planning_context_ref),
        (projection.planning_context_digest, context.planning_context_digest),
        (projection.recommendation, proposal.recommendation),
        (projection.reason_code, proposal.reason_code),
        (proposal.proposal_digest, disposition.proposal_digest),
        (proposal.context_ref, context.planning_context_ref),
        (proposal.context_digest, context.planning_context_digest),
        (proposal.source_invocation_ref, source.source_invocation_ref),
        (proposal.source_invocation_digest, source.source_invocation_digest),
        (proposal.artifact_ref, artifact.artifact_ref),
        (proposal.artifact_digest, artifact.artifact_digest),
        (proposal.safe_projection_digest, projection.safe_projection_digest),
        (proposal.evidence_set_ref, disposition.evidence_set_ref),
        (proposal.evidence_set_digest, disposition.evidence_set_digest),
        (artifact.safe_projection_digest, projection.safe_projection_digest),
        (context.planning_context_digest, disposition.planning_context_digest),
        (proposal.proposal_phase, disposition.proposal_phase),
        (context.authoritative_subject_kind, "effect_intent"),
        (context.authoritative_subject_ref, context.effect_intent_ref),
        (context.global_stop_state, "clear"),
    )
    if any(left != right for left, right in relations):
        raise _database_integrity_failure() from None
    if (proposal.recommendation, disposition.disposition) not in (
        ("select_for_dispatch_gates", "selected_for_dispatch_gates"),
        ("defer", "deferred"),
        ("replan", "deferred"),
        ("block", "blocked"),
        ("terminal_reject", "blocked"),
    ):
        raise _database_integrity_failure() from None
    entries = tuple(
        {
            "evidence_role": row.evidence_role,
            "role_rank": row.role_rank,
            "ordinal": row.ordinal,
            "evidence_ref": row.evidence_ref,
            "evidence_digest": row.evidence_digest,
            "evidence_binding_digest": row.evidence_binding_digest,
        }
        for row in evidence
    )
    evidence_identity = {
        "evidence_set_ref": proposal.evidence_set_ref,
        "proposal_ref": proposal.proposal_ref,
        "proposal_phase": proposal.proposal_phase,
        "entries": entries,
    }
    if (
        _domain_separated_digest(_semantic._EVIDENCE_SET_DOMAIN, evidence_identity)
        != proposal.evidence_set_digest
    ):
        raise _database_integrity_failure() from None
    if any(
        row.proposal_ref != proposal.proposal_ref
        or row.proposal_phase != proposal.proposal_phase
        or row.evidence_set_ref != proposal.evidence_set_ref
        or row.ordinal != 0
        or row.required_for_selection
        != (0 if row.evidence_role == _semantic._READINESS_ROLE else 1)
        for row in evidence
    ):
        raise _database_integrity_failure() from None
    evidence_by_role = {row.evidence_role: row for row in evidence}
    context_evidence = (
        (
            "standing_policy",
            context.standing_policy_ref,
            context.standing_policy_digest,
        ),
        ("risk_lane", context.risk_lane_ref, context.risk_lane_digest),
        (
            "authorized_path_scope",
            evidence_by_role["authorized_path_scope"].evidence_ref,
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
            "validation_requirement",
            context.validation_requirement_ref,
            context.validation_requirement_digest,
        ),
        (
            "review_requirement",
            context.review_requirement_ref,
            context.review_requirement_digest,
        ),
    )
    if any(
        evidence_by_role[role].evidence_ref != reference
        or evidence_by_role[role].evidence_digest != digest
        for role, reference, digest in context_evidence
    ):
        raise _database_integrity_failure() from None
    authority = evidence[10]
    if not (
        authority.evidence_role == "authority_selection_observation"
        and authority.evidence_ref == disposition.authority_selection_observation_ref
        and authority.evidence_digest
        == disposition.authority_selection_observation_digest
        and context.authority_selection_observation_ref == authority.evidence_ref
        and context.authority_selection_observation_digest == authority.evidence_digest
    ):
        raise _database_integrity_failure() from None
    readiness = evidence_by_role.get(_semantic._READINESS_ROLE)
    if (readiness is None) is not (
        context.qualified_remote_host_readiness_ref is None
    ) or (
        readiness is not None
        and (
            readiness.evidence_ref != context.qualified_remote_host_readiness_ref
            or readiness.evidence_digest
            != context.qualified_remote_host_readiness_digest
        )
    ):
        raise _database_integrity_failure() from None
    observation_mapping = {
        "schema_id": context.authority_selection_observation_schema_id,
        "authority_observation_ref": context.authority_selection_observation_ref,
        "authoritative_subject_kind": context.authoritative_subject_kind,
        "authoritative_subject_ref": context.authoritative_subject_ref,
        "program_ref": context.program_ref,
        "semantic_attempt_ref": context.semantic_attempt_ref,
        "candidate_ref": context.candidate_ref,
        "effect_intent_ref": context.effect_intent_ref,
        "author_command_ref": context.author_command_ref,
        "attempt_fence_ref": context.attempt_fence_ref,
        "effect_fence_ref": context.effect_fence_ref,
        "delivery_attempt_ref": context.delivery_attempt_ref,
        "authority_evaluation_ref": context.authority_evaluation_ref,
        "authority_evaluation_digest": context.authority_evaluation_digest,
        "observation_state": context.authority_observation_state,
        "observation_version": context.authority_observation_version,
        "authority_observation_issued_at": context.authority_observation_issued_at,
        "authority_observation_expires_at": context.authority_observation_expires_at,
        "source_authority_ref": context.source_authority_ref,
        "verification_evidence_ref": context.verification_evidence_ref,
        "verification_evidence_digest": context.verification_evidence_digest,
    }
    if context.authority_selection_observation_digest != _domain_separated_digest(
        _semantic._DOMAINS["authority_observation"], observation_mapping
    ):
        raise _database_integrity_failure() from None
    evidence_times = tuple(row.evidence_bound_at for row in evidence)
    chronology = (
        context.authority_observation_issued_at,
        context.planning_context_captured_at,
        source.source_invocation_started_at,
        source.source_invocation_completed_at,
        artifact.artifact_validated_at,
        evidence_times[0],
        proposal.proposal_created_at,
        disposition.coordinator_disposition_decided_at,
    )
    if (
        any(value != evidence_times[0] for value in evidence_times)
        or tuple(sorted(chronology)) != chronology
        or not proposal.proposal_created_at
        < disposition.coordinator_disposition_decided_at
        < context.authority_observation_expires_at
        or not disposition.coordinator_disposition_decided_at
        < context.attempt_fence_expires_at
        or not disposition.coordinator_disposition_decided_at
        < context.effect_fence_expires_at
    ):
        raise _database_integrity_failure() from None
    rows: list[_rows.CanonicalCognitivePhysicalRow] = [
        _rows.CanonicalCognitivePhysicalRow(
            _rows._TABLE_ORDER[0], "source_invocation", 0, 0, source
        ),
        _rows.CanonicalCognitivePhysicalRow(
            _rows._TABLE_ORDER[1], "planning_context", 1, 0, context
        ),
        _rows.CanonicalCognitivePhysicalRow(
            _rows._TABLE_ORDER[2], "private_artifact_binding", 2, 0, artifact
        ),
        _rows.CanonicalCognitivePhysicalRow(
            _rows._TABLE_ORDER[3], "model_proposal", 3, 0, proposal
        ),
        _rows.CanonicalCognitivePhysicalRow(
            _rows._TABLE_ORDER[4], "pre_execution_plan_projection", 4, 0, projection
        ),
    ]
    rows.extend(
        _rows.CanonicalCognitivePhysicalRow(
            _rows._TABLE_ORDER[5],
            f"evidence.{row.evidence_role}",
            row.role_rank,
            0,
            row,
        )
        for row in evidence
    )
    return tuple(rows)


def _selection_head_postimage_from_disposition(
    disposition: _rows.DevelopmentPreExecutionDispositionRowValue,
) -> _rows.DevelopmentPreExecutionSelectionHeadRowValue:
    if type(disposition) is not _rows.DevelopmentPreExecutionDispositionRowValue:
        raise _database_integrity_failure() from None
    mapping: dict[str, object] = {
        "schema_id": _HEAD_SCHEMA,
        **{
            name: object.__getattribute__(disposition, name)
            for name in _L34_FIELDS
        },
        "current_proposal_ref": disposition.proposal_ref,
        "current_disposition_ref": disposition.disposition_ref,
        "current_disposition": disposition.disposition,
        "head_revision": disposition.resulting_selection_head_revision,
        "updated_at": disposition.coordinator_disposition_decided_at,
        "head_digest": disposition.selection_head_postimage_digest,
    }
    try:
        return _rows.DevelopmentPreExecutionSelectionHeadRowValue(
            **_mapping_in_order(_rows._TABLE_ORDER[7], mapping)
        )
    except _CognitiveProposalContractViolation:
        raise _database_integrity_failure() from None


def _read_disposition_inventory(
    capability: object,
    disposition: _rows.DevelopmentPreExecutionDispositionRowValue,
    current_head: _rows.DevelopmentPreExecutionSelectionHeadRowValue,
) -> tuple[_rows.DevelopmentPreExecutionDispositionRowValue, ...]:
    if (
        type(disposition) is not _rows.DevelopmentPreExecutionDispositionRowValue
        or type(current_head)
        is not _rows.DevelopmentPreExecutionSelectionHeadRowValue
        or current_head.head_revision
        < disposition.resulting_selection_head_revision
    ):
        raise _database_integrity_failure() from None
    lower_revision = max(
        disposition.resulting_selection_head_revision,
        current_head.head_revision - 257,
    )
    expected_count = current_head.head_revision - lower_revision + 1
    columns = (
        *_rows._TABLE_COLUMNS[_rows._TABLE_ORDER[6]],
        "COUNT(*) OVER ()",
    )
    fetched = _read_rows(
        capability,
        table=_rows._TABLE_ORDER[6],
        columns=columns,
        where=(
            _K8_WHERE
            + " AND resulting_selection_head_revision BETWEEN ? AND ? "
            + "ORDER BY resulting_selection_head_revision DESC, disposition_ref ASC"
        ),
        parameters=tuple(
            object.__getattribute__(disposition, name) for name in _K8_FIELDS
        )
        + (lower_revision, current_head.head_revision),
        limit=258,
    )
    if len(fetched) != expected_count:
        raise _database_integrity_failure() from None
    result: list[_rows.DevelopmentPreExecutionDispositionRowValue] = []
    try:
        for raw in fetched:
            if type(raw) is not tuple or len(raw) != len(columns):
                raise _database_integrity_failure() from None
            raw_tuple = typing.cast(tuple[object, ...], raw)
            if type(raw_tuple[-1]) is not int or raw_tuple[-1] != expected_count:
                raise _database_integrity_failure() from None
            row = _rows._row_value_from_tuple(
                _rows._TABLE_ORDER[6],
                raw_tuple[:-1],
            )
            if type(row) is not _rows.DevelopmentPreExecutionDispositionRowValue:
                raise _database_integrity_failure() from None
            if tuple(
                object.__getattribute__(row, name) for name in _L34_FIELDS
            ) != tuple(
                object.__getattribute__(disposition, name) for name in _L34_FIELDS
            ):
                raise _database_integrity_failure() from None
            result.append(row)
    except _CognitiveProposalContractViolation:
        raise _database_integrity_failure() from None
    return tuple(result)


def _require_no_dangling_successor(
    capability: object,
    current_head: _rows.DevelopmentPreExecutionSelectionHeadRowValue,
) -> None:
    if type(current_head) is not _rows.DevelopmentPreExecutionSelectionHeadRowValue:
        raise _database_integrity_failure() from None
    fetched = _read_rows(
        capability,
        table=_rows._TABLE_ORDER[6],
        columns=_rows._TABLE_COLUMNS[_rows._TABLE_ORDER[6]],
        where=(
            _L34_WHERE
            + " AND prior_selection_head_revision = ?"
            + " AND supersedes_disposition_ref = ?"
        ),
        parameters=(
            *_l34_values(current_head),
            current_head.head_revision,
            current_head.current_disposition_ref,
        ),
        limit=2,
    )
    try:
        for raw in fetched:
            successor = _rows._row_value_from_tuple(_rows._TABLE_ORDER[6], raw)
            if (
                type(successor)
                is not _rows.DevelopmentPreExecutionDispositionRowValue
                or _l34_values(successor) != _l34_values(current_head)
                or successor.supersedes_disposition_ref
                != current_head.current_disposition_ref
                or successor.prior_selection_head_revision
                != current_head.head_revision
                or successor.prior_selection_head_digest != current_head.head_digest
                or successor.expected_selection_head_revision
                != current_head.head_revision
                or successor.expected_selection_head_digest != current_head.head_digest
                or successor.resulting_selection_head_revision
                != current_head.head_revision + 1
            ):
                raise _database_integrity_failure() from None
    except _CognitiveProposalContractViolation:
        raise _database_integrity_failure() from None
    if fetched:
        raise _database_integrity_failure() from None


def _prove_current_head_descends_from_receipt(
    capability: object,
    receipt: _rows.DevelopmentCognitiveMutationReceiptRowValue,
    receipt_disposition: _rows.DevelopmentPreExecutionDispositionRowValue,
) -> tuple[_rows.DevelopmentPreExecutionSelectionHeadRowValue, int]:
    command_shell = object.__new__(RecordPreExecutionPlanDispositionCommandV1)
    for name in _K8_FIELDS:
        object.__setattr__(
            command_shell, name, object.__getattribute__(receipt_disposition, name)
        )
    head = _read_selection_head(
        capability,
        typing.cast(RecordPreExecutionPlanDispositionCommandV1, command_shell),
    )
    if head is None:
        raise _database_integrity_failure() from None
    if _l34_values(head) != _l34_values(receipt_disposition):
        raise _database_integrity_failure() from None
    receipt_postimage = _selection_head_postimage_from_disposition(
        receipt_disposition
    )
    if not (
        receipt.disposition_ref == receipt_disposition.disposition_ref
        and receipt.disposition_digest == receipt_disposition.disposition_digest
        and receipt.selection_head_revision
        == receipt_disposition.resulting_selection_head_revision
        and receipt.selection_head_digest == receipt_postimage.head_digest
    ):
        raise _database_integrity_failure() from None
    observed_depth = (
        head.head_revision - receipt_disposition.resulting_selection_head_revision
    )
    inventory = _read_disposition_inventory(
        capability,
        receipt_disposition,
        head,
    )
    _require_no_dangling_successor(capability, head)
    expected_window_depth = min(observed_depth, 257)
    if len(inventory) != expected_window_depth + 1:
        raise _database_integrity_failure() from None
    visited_refs: set[str] = set()
    visited_revisions: set[int] = set()
    postimages: list[_rows.DevelopmentPreExecutionSelectionHeadRowValue] = []
    for index, row in enumerate(inventory):
        expected_revision = head.head_revision - index
        if (
            row.resulting_selection_head_revision != expected_revision
            or row.disposition_ref in visited_refs
            or row.resulting_selection_head_revision in visited_revisions
            or _l34_values(row) != _l34_values(receipt_disposition)
        ):
            raise _database_integrity_failure() from None
        postimage = _selection_head_postimage_from_disposition(row)
        visited_refs.add(row.disposition_ref)
        visited_revisions.add(row.resulting_selection_head_revision)
        postimages.append(postimage)
        if index == 0:
            if not _exact_equal(postimage.to_mapping(), head.to_mapping()):
                raise _database_integrity_failure() from None
            continue
        successor = inventory[index - 1]
        if not (
            successor.supersedes_disposition_ref == row.disposition_ref
            and successor.prior_selection_head_revision
            == row.resulting_selection_head_revision
            and successor.prior_selection_head_digest == postimage.head_digest
        ):
            raise _database_integrity_failure() from None
    if observed_depth <= 257:
        if not (
            _exact_equal(inventory[-1].to_mapping(), receipt_disposition.to_mapping())
            and _exact_equal(
                postimages[-1].to_mapping(), receipt_postimage.to_mapping()
            )
        ):
            raise _database_integrity_failure() from None
    if observed_depth >= 257:
        raise _LineageProofOverflow(head, 257) from None
    return head, observed_depth


def _graph_from_members(
    mutation_ref: str,
    command_digest: str,
    members: tuple[_rows.CanonicalCognitivePhysicalRow, ...],
) -> CognitiveMutationGraphV1:
    entries = tuple(
        CognitiveMutationGraphEntryV1(
            role=member.role,
            rank=member.rank,
            ordinal=member.ordinal,
            table=member.table,
            locator=member.locator(),
            member_digest=member.member_digest,
        )
        for member in members
        if member.rank is not None
    )
    identity = {
        "mutation_ref": mutation_ref,
        "command_digest": command_digest,
        "entries": tuple(entry.to_mapping() for entry in entries),
    }
    return CognitiveMutationGraphV1(
        mutation_ref=mutation_ref,
        command_digest=command_digest,
        entries=entries,
        mutation_graph_digest=_domain_separated_digest(_GRAPH_DOMAIN, identity),
    )


def _verified_row_for_locator(
    capability: object,
    table: str,
    locator: tuple[tuple[str, object], ...],
) -> _rows._CognitiveRowValue | None:
    fetched = _read_rows(
        capability,
        table=table,
        columns=_rows._TABLE_COLUMNS[table],
        where=" AND ".join(f"{name} = ?" for name, _value in locator),
        parameters=tuple(value for _name, value in locator),
        limit=2,
    )
    if len(fetched) > 1:
        raise _database_integrity_failure() from None
    if not fetched:
        return None
    try:
        return _rows._row_value_from_tuple(table, fetched[0])
    except _CognitiveProposalContractViolation:
        raise _database_integrity_failure() from None


def _evidence_member_locators_for_rows(
    members: tuple[_rows.CanonicalCognitivePhysicalRow, ...],
) -> tuple[
    tuple[
        tuple[tuple[str, object], ...],
        tuple[tuple[str, object], ...],
    ],
    ...,
]:
    result = []
    for member in members:
        if member.table != _rows._TABLE_ORDER[5]:
            continue
        value = member.values
        if type(value) is not _rows.DevelopmentModelProposalEvidenceBindingRowValue:
            raise _database_integrity_failure() from None
        result.append(
            (
                (
                    ("proposal_ref", value.proposal_ref),
                    ("evidence_role", value.evidence_role),
                    ("ordinal", value.ordinal),
                ),
                (
                    ("proposal_ref", value.proposal_ref),
                    ("role_rank", value.role_rank),
                    ("ordinal", value.ordinal),
                ),
            )
        )
    return tuple(result)


def _verify_all_persisted_identity_routes(
    *,
    capability: object,
    members: tuple[_rows.CanonicalCognitivePhysicalRow, ...],
    current_head: _rows.DevelopmentPreExecutionSelectionHeadRowValue,
    historical_head: _rows.DevelopmentPreExecutionSelectionHeadRowValue,
    observed_depth: int,
    persisted_probe: PreExecutionPlanDispositionRecoveryProbeV1,
) -> tuple[tuple[str, tuple[tuple[str, object], ...]], ...]:
    locators = _identity_locators_for_rows(members)
    evidence_member_locators = _evidence_member_locators_for_rows(members)
    if (
        len(locators) != 30
        or not _exact_equal(locators, persisted_probe.identity_locators)
        or not _exact_equal(
            evidence_member_locators, persisted_probe.evidence_member_locators
        )
    ):
        raise _database_integrity_failure() from None
    by_table: dict[str, list[_rows._CognitiveRowValue]] = {
        table: [] for table in _rows._TABLE_ORDER
    }
    for member in members:
        by_table[member.table].append(member.values)
    for index, (table, locator) in enumerate(locators):
        observed = _verified_row_for_locator(capability, table, locator)
        if table == _rows._TABLE_ORDER[7]:
            if index < 26:
                if observed is None or not _exact_equal(
                    observed.to_mapping(), current_head.to_mapping()
                ):
                    raise _database_integrity_failure() from None
            elif observed_depth == 0:
                if observed is None or not _exact_equal(
                    observed.to_mapping(), historical_head.to_mapping()
                ):
                    raise _database_integrity_failure() from None
            elif observed is not None:
                raise _database_integrity_failure() from None
            continue
        expected = by_table[table][0]
        if observed is None or not _exact_equal(
            observed.to_mapping(), expected.to_mapping()
        ):
            raise _database_integrity_failure() from None

    evidence_members = by_table[_rows._TABLE_ORDER[5]]
    if len(evidence_members) != len(evidence_member_locators):
        raise _database_integrity_failure() from None
    for expected, route_pair in zip(
        evidence_members,
        evidence_member_locators,
        strict=True,
    ):
        for locator in route_pair:
            observed = _verified_row_for_locator(
                capability, _rows._TABLE_ORDER[5], locator
            )
            if observed is None or not _exact_equal(
                observed.to_mapping(), expected.to_mapping()
            ):
                raise _database_integrity_failure() from None
    return locators


def _read_and_verify_persisted_family(
    *,
    capability: object,
    receipt: _rows.DevelopmentCognitiveMutationReceiptRowValue,
) -> _VerifiedPersistedPreExecutionPlanDisposition:
    if not (
        receipt.mutation_family == _MUTATION_FAMILY
        and receipt.command_schema_id == _COMMAND_SCHEMA
        and receipt.result_class == _RESULT_CLASS
        and receipt.outcome == _OUTCOME
    ):
        raise _database_integrity_failure() from None
    disposition = _read_disposition_by_ref(capability, receipt.disposition_ref)
    proposal_members = _read_proposal_family_rows(capability, disposition)
    lineage_overflow: _LineageProofOverflow | None = None
    try:
        head, depth = _prove_current_head_descends_from_receipt(
            capability, receipt, disposition
        )
    except _LineageProofOverflow as overflow:
        lineage_overflow = overflow
        head = overflow.head
        depth = overflow.observed_depth
    historical_head = _selection_head_postimage_from_disposition(disposition)
    persisted_context = proposal_members[1].values
    if not (
        type(persisted_context)
        is _rows.DevelopmentPreExecutionPlanningContextRowValue
        and _l34_values(persisted_context)
        == _l34_values(disposition)
        == _l34_values(historical_head)
    ):
        raise _database_integrity_failure() from None

    disposition_member = _rows.CanonicalCognitivePhysicalRow(
        _rows._TABLE_ORDER[6], "coordinator_disposition", 20, 0, disposition
    )
    head_member = _rows.CanonicalCognitivePhysicalRow(
        _rows._TABLE_ORDER[7], "selection_head_postimage", 21, 0, historical_head
    )
    members = (*proposal_members, disposition_member, head_member)
    graph = _graph_from_members(receipt.mutation_ref, receipt.command_digest, members)
    if graph.mutation_graph_digest != receipt.mutation_graph_digest:
        raise _database_integrity_failure() from None
    if not (
        receipt.program_ref == disposition.program_ref
        and receipt.proposal_ref == disposition.proposal_ref
        and receipt.disposition_digest == disposition.disposition_digest
        and receipt.authority_selection_observation_ref
        == disposition.authority_selection_observation_ref
        and receipt.authority_selection_observation_digest
        == disposition.authority_selection_observation_digest
        and receipt.effect_intent_ref == disposition.effect_intent_ref
        and receipt.selection_head_digest == disposition.selection_head_postimage_digest
        and receipt.committed_at == disposition.coordinator_disposition_decided_at
    ):
        raise _database_integrity_failure() from None
    source = typing.cast(
        _rows.DevelopmentModelSourceInvocationRowValue,
        proposal_members[0].values,
    )
    context = typing.cast(
        _rows.DevelopmentPreExecutionPlanningContextRowValue,
        proposal_members[1].values,
    )
    artifact = typing.cast(
        _rows.DevelopmentPrivateProposalArtifactBindingRowValue,
        proposal_members[2].values,
    )
    proposal = typing.cast(
        _rows.DevelopmentModelProposalRowValue,
        proposal_members[3].values,
    )
    projection_row = typing.cast(
        _rows.DevelopmentPreExecutionPlanProjectionRowValue,
        proposal_members[4].values,
    )
    command_fields: dict[str, object] = {
        "schema_id": _COMMAND_SCHEMA,
        "mutation_ref": receipt.mutation_ref,
        "proposal_ref": proposal.proposal_ref,
        "proposal_digest": proposal.proposal_digest,
        "source_invocation_ref": source.source_invocation_ref,
        "source_invocation_digest": source.source_invocation_digest,
        "artifact_ref": artifact.artifact_ref,
        "artifact_digest": artifact.artifact_digest,
        "artifact_binding_digest": artifact.artifact_binding_digest,
        "planning_context_ref": context.planning_context_ref,
        "planning_context_digest": context.planning_context_digest,
        "safe_projection_digest": projection_row.safe_projection_digest,
        "evidence_set_ref": proposal.evidence_set_ref,
        "evidence_set_digest": proposal.evidence_set_digest,
        "preassigned_disposition_ref": disposition.disposition_ref,
        "expected_current_selection_revision": disposition.expected_selection_head_revision,
        "expected_current_selection_head_digest": disposition.expected_selection_head_digest,
        "disposition": disposition.disposition,
        "disposition_reason_code": disposition.reason_code,
        "supersedes_disposition_ref": disposition.supersedes_disposition_ref,
        "program_ref": disposition.program_ref,
        "semantic_attempt_ref": disposition.semantic_attempt_ref,
        "candidate_ref": disposition.candidate_ref,
        "effect_intent_ref": disposition.effect_intent_ref,
        "author_command_ref": disposition.author_command_ref,
        "author_command_digest": disposition.author_command_digest,
        "attempt_fence_ref": disposition.attempt_fence_ref,
        "attempt_fence_digest": disposition.attempt_fence_digest,
        "effect_fence_ref": disposition.effect_fence_ref,
        "effect_fence_digest": disposition.effect_fence_digest,
        "delivery_attempt_ref": disposition.delivery_attempt_ref,
        "delivery_envelope_digest": disposition.delivery_envelope_digest,
        "mutation_command_digest": receipt.command_digest,
    }
    try:
        persisted_command = RecordPreExecutionPlanDispositionCommandV1(**command_fields)
        semantic_context = _semantic.PreExecutionPlanningContextV1(
            **context.to_mapping()
        )
        semantic_bindings = tuple(
            _semantic.ModelProposalEvidenceBindingV1(**member.values.to_mapping())
            for member in proposal_members[5:]
        )
        persisted_probe = (
            _build_pre_execution_plan_disposition_recovery_probe_from_basis(
                persisted_command,
                semantic_context,
                semantic_bindings,
            )
        )
    except _CognitiveProposalContractViolation:
        raise _database_integrity_failure() from None
    receipt_member = _rows.CanonicalCognitivePhysicalRow(
        _rows._TABLE_ORDER[8], "receipt", None, 0, receipt
    )
    all_members = (*members, receipt_member)
    identity_locators = _verify_all_persisted_identity_routes(
        capability=capability,
        members=all_members,
        current_head=head,
        historical_head=historical_head,
        observed_depth=depth,
        persisted_probe=persisted_probe,
    )
    result_fields: dict[str, object] = {
        "schema_id": _RESULT_SCHEMA,
        "mutation_ref": receipt.mutation_ref,
        "command_digest": receipt.command_digest,
        "proposal_ref": receipt.proposal_ref,
        "disposition_ref": receipt.disposition_ref,
        "disposition_digest": receipt.disposition_digest,
        "disposition": disposition.disposition,
        "program_ref": receipt.program_ref,
        "semantic_attempt_ref": disposition.semantic_attempt_ref,
        "candidate_ref": disposition.candidate_ref,
        "effect_intent_ref": receipt.effect_intent_ref,
        "selection_head_revision": receipt.selection_head_revision,
        "selection_head_digest": receipt.selection_head_digest,
        "authority_selection_observation_ref": receipt.authority_selection_observation_ref,
        "authority_selection_observation_digest": receipt.authority_selection_observation_digest,
        "mutation_graph_digest": receipt.mutation_graph_digest,
        "recorded_at": receipt.committed_at,
    }
    result_fields["result_projection_digest"] = _domain_separated_digest(
        _RESULT_DOMAIN, result_fields
    )
    if result_fields["result_projection_digest"] != receipt.result_projection_digest:
        raise _database_integrity_failure() from None
    try:
        projection = PreExecutionPlanDispositionResultProjectionV1(**result_fields)
        result = PreExecutionPlanDispositionResultV1(
            projection=projection,
            receipt_digest=receipt.receipt_digest,
        )
        verified = _VerifiedPersistedPreExecutionPlanDisposition(
            result=result,
            observed_depth=depth,
            command=persisted_command,
            identity_locators=identity_locators,
            recovery_probe=persisted_probe,
        )
        if lineage_overflow is not None:
            raise lineage_overflow
        return verified
    except _CognitiveProposalContractViolation:
        raise _database_integrity_failure() from None


def _unresolved_recovery(depth: int = 0) -> PreExecutionPlanDispositionRecoveryResultV1:
    return PreExecutionPlanDispositionRecoveryResultV1(
        classification=PreExecutionPlanDispositionRecoveryClassificationV1.UNRESOLVED,
        observed_depth=depth,
        committed_result=None,
    )


def _recover_pre_execution_plan_disposition_after_fencing(
    *,
    capability: object,
    probe: object,
) -> PreExecutionPlanDispositionRecoveryResultV1:
    try:
        checked = _require_exact_recovery_probe(probe)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return _unresolved_recovery()
    try:
        receipt = _read_receipt(capability, checked.command.mutation_ref)
        if receipt is not None:
            persisted = _read_and_verify_persisted_family(
                capability=capability,
                receipt=receipt,
            )
            if not (
                receipt.command_digest == checked.command.mutation_command_digest
                and _exact_equal(
                    persisted.command.to_mapping(), checked.command.to_mapping()
                )
                and _exact_equal(
                    persisted.recovery_probe.to_mapping(), checked.to_mapping()
                )
            ):
                return _unresolved_recovery(persisted.observed_depth)
            return PreExecutionPlanDispositionRecoveryResultV1(
                classification=PreExecutionPlanDispositionRecoveryClassificationV1.COMMITTED_EXACT,
                observed_depth=persisted.observed_depth,
                committed_result=persisted.result,
            )

        head = _read_selection_head(capability, checked.command)
        expected = checked.expected_preimage
        if head is None:
            if expected.expected_current_selection_revision is not None:
                return _unresolved_recovery()
        elif not (
            expected.expected_current_selection_revision == head.head_revision
            and expected.expected_current_selection_head_digest == head.head_digest
            and expected.supersedes_disposition_ref == head.current_disposition_ref
            and _exact_equal(
                tuple(
                    (name, object.__getattribute__(head, name))
                    for name in _K8_FIELDS
                ),
                checked.selection_key,
            )
            and _exact_equal(
                tuple(object.__getattribute__(head, name) for name in _L34_FIELDS),
                tuple(
                    object.__getattribute__(checked.planning_context, name)
                    for name in _L34_FIELDS
                ),
            )
        ):
            return _unresolved_recovery()
        absence_invalid = False
        for index, (table, locator) in enumerate(checked.identity_locators):
            observed = _verified_row_for_locator(capability, table, locator)
            if table != _rows._TABLE_ORDER[7]:
                if observed is not None:
                    absence_invalid = True
                continue
            if head is None:
                if observed is not None:
                    absence_invalid = True
            elif index < 26:
                if observed is None or not _exact_equal(
                    observed.to_mapping(), head.to_mapping()
                ):
                    absence_invalid = True
            elif observed is not None:
                absence_invalid = True
        for route_pair in checked.evidence_member_locators:
            for locator in route_pair:
                if (
                    _verified_row_for_locator(
                        capability, _rows._TABLE_ORDER[5], locator
                    )
                    is not None
                ):
                    absence_invalid = True
        if _read_rows(
            capability,
            table=_rows._TABLE_ORDER[5],
            columns=("1",),
            where="proposal_ref = ?",
            parameters=(checked.command.proposal_ref,),
            limit=16,
        ):
            absence_invalid = True
        if absence_invalid:
            return _unresolved_recovery()
        return PreExecutionPlanDispositionRecoveryResultV1(
            classification=PreExecutionPlanDispositionRecoveryClassificationV1.DEFINITELY_NOT_COMMITTED,
            observed_depth=0,
            committed_result=None,
        )
    except _LineageProofOverflow as overflow:
        return _unresolved_recovery(overflow.observed_depth)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return _unresolved_recovery()


def _require_fresh_pre_execution_plan_disposition(
    value: object,
) -> _FreshPreExecutionPlanDisposition:
    if type(value) is not _FreshPreExecutionPlanDisposition:
        raise _database_integrity_failure() from None
    return typing.cast(_FreshPreExecutionPlanDisposition, value)
