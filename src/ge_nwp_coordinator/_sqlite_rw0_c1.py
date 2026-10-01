"""Private RW0-C1 durable resolution, planning, readback, and recovery.

This module deliberately owns no SQLite connection, transaction, writer lease,
clock, or commit authority.  It consumes only the nominal mutation read
capability supplied by :mod:`sqlite_transition_transaction` and returns closed
plans for that controller to execute.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import typing

from . import _rw0_phase_entry_semantic_values as _b1
from . import _rw0_wire_protocol_values as _wire
from . import _rw0_worker_mechanism_capability_values as _capability_values
from . import _worker_execution_semantic_values as _worker_values
from ._development_pre_execution_plan_disposition_contracts import (
    CanonicalC2B3DLineage,
    PreExecutionPlanDispositionResultProjectionV1,
    _K8_FIELDS,
    _L34_FIELDS,
)
from ._rw0_c1_mutation_contracts import (
    RW0C1OperandIdentity,
    RW0C1RelationSpecification,
    RW0C1WritePlan,
    admission_graph_digest,
    build_row,
    global_scope_binding_digest,
    k8_digest_from_phase_basis,
    k8_mapping_from_phase_basis,
    membership_digest,
    normalized_owner_mapping,
    operand_set_digest,
    phase_graph_digest,
    relation_digest,
    relation_reference,
    relation_set_digest,
    relation_specifications,
    row_schema_id,
    section41_owner_family_graph_digest,
    typed_payload_table,
    validate_admission_operand_grammar,
    validate_dependency_locators,
)
from ._rw0_c1_row_values import ROW_SPEC_BY_TABLE, RW0C1RowValue
from ._rw0_c1_semantic_values import (
    RW0_C1_KIND_SPECS,
    RW0C1AdmitEvidenceCommandV1,
    RW0C1AdmitEvidenceResultV1,
    RW0C1AdmissionSnapshotBindingV1,
    RW0C1ConflictReasonV1,
    RW0C1ConflictV1,
    RW0C1EstablishPhaseCommandV1,
    RW0C1EstablishPhaseResultV1,
    RW0C1EvidenceAdmissionRecoverySelectorV1,
    RW0C1MemberLocatorV1,
    RW0C1MutationReceiptV1,
    RW0C1OwnerRowLocatorV1,
    RW0C1PreflightError,
    RW0C1RecoveryDispositionV1,
    RW0C1RecoveryProbeV1,
    RW0C1RecoveryResultV1,
    RW0C1Section41PostExecutionProposalFamilyMemberV1,
    RW0C1TransientPrivateBindingV1,
    RW0C1WireProcessResultClassificationBindingV1,
    RW0C1WireWorkerResultBindingV1,
    evidence_identity,
    membership_schema_id,
    relation_evaluation_time,
)
from ._sqlite_development_pre_execution_plan_disposition import (
    _read_disposition_by_ref,
    _read_exact_row as _read_cognitive_exact_row,
    _read_proposal_family_rows,
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
from ._sqlite_rw0_c1_readers import (
    RW0C1MembershipFamily,
    RW0C1OwnerRowSnapshot,
    RW0C1Section41PostExecutionEvidenceFamily,
    RW0C1TypedEvidenceAggregate,
    _read_membership_by_digest,
    _read_membership_by_phase_kind_digest,
    _read_membership_by_phase_kind_ref,
    _read_membership_by_ref,
    _read_membership_family,
    _read_phase_by_digest,
    _read_phase_by_k8,
    _read_phase_by_pair,
    _read_phase_by_ref,
    _read_receipt,
    _read_registry_by_kind_digest,
    _read_registry_by_kind_ref,
    _read_relation_by_digest,
    _read_relation_by_ref,
    _read_relation_operands,
    _read_relation_set,
    _read_section41_post_execution_evidence_family,
    _read_typed_children_by_digest,
    _read_typed_children_by_ref,
    _read_typed_evidence,
    _read_typed_payload_by_kind_digest,
    _read_typed_payload_by_kind_ref,
    _read_development_owner_row,
)
from .global_stop import GLOBAL_STOP_SCHEMA_ID
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from .sqlite_transition_read_scope import _read_global_stop_current


__all__: tuple[str, ...] = ()


_PHASE_RELATION_SCHEMA = (
    "governed-execution.nwp-rw0-c1-phase-entry-basis-relation.v1"
)
_PHASE_RELATION_SPEC = RW0C1RelationSpecification(
    0,
    0,
    _PHASE_RELATION_SCHEMA,
    "relation_attested_at_admission",
)
_PHASE_ROW_SCHEMA = "governed-execution.nwp-rw0-c1-phase-instance-row.v1"
_REGISTRY_ROW_SCHEMA = "governed-execution.nwp-rw0-c1-evidence-value-row.v1"
_RELATION_ROW_SCHEMA = "governed-execution.nwp-rw0-c1-relation-binding.v1"
_OPERAND_ROW_SCHEMA = "governed-execution.nwp-rw0-c1-relation-operand.v1"
_RECEIPT_SCHEMA = "governed-execution.nwp-rw0-c1-mutation-receipt.v1"
_MODEL_PROPOSAL_SCHEMA = "governed-execution.nwp-model-proposal-envelope.v1"
_ARTIFACT_BINDING_SCHEMA = (
    "governed-execution.nwp-private-proposal-artifact-binding.v1"
)
_SELECTION_HEAD_SCHEMA = (
    "governed-execution.nwp-pre-execution-selection-head.v1"
)
_COGNITIVE_RECEIPT_SCHEMA = (
    "governed-execution.nwp-cognitive-mutation-receipt.v1"
)
_SECTION41_EVIDENCE_SET_DOMAIN = (
    "governed-execution.nwp-model-proposal-evidence-set.v1.identity"
)
_POST_EXECUTION_EVIDENCE = (
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


class _RW0C1OwnerRowMissing(Exception):
    """Internal semantic absence; sanitized reader failures remain distinct."""

    __slots__ = ()


class _RW0C1CurrentStateConflict(Exception):
    """Internal admission CAS mismatch, distinct from owner-row absence."""

    __slots__ = ()


def _canonical_owner_digest(domain: str, value: object) -> str:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeError):
        raise _integrity_failure() from None
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + encoded).hexdigest()


@dataclass(frozen=True, slots=True, repr=False)
class _RW0C1PhasePreparation:
    command: RW0C1EstablishPhaseCommandV1
    disposition: object
    selection_result: object
    selection_head: object
    selected_proposal: object
    selected_artifact: object
    cognitive_receipt: object
    work_spec_binding: object
    attempt_fence: object
    author_effect_fence: object
    author_command: object
    author_delivery_row: object
    effect_head: object
    delivery_head: object
    global_stop: object

    def __repr__(self) -> str:
        return "<_RW0C1PhasePreparation>"


@dataclass(frozen=True, slots=True, repr=False)
class _RW0C1EvidencePreparation:
    command: RW0C1AdmitEvidenceCommandV1
    phase: RW0C1RowValue
    basis: object
    dependencies: tuple[RW0C1MembershipFamily, ...]
    result_observation_dependencies: tuple[RW0C1MembershipFamily, ...]
    owner_graph: object
    registry_preexisting: bool

    def __repr__(self) -> str:
        return "<_RW0C1EvidencePreparation>"


@dataclass(frozen=True, slots=True, repr=False)
class _RW0C1AdmissionOwnerRead:
    basis: object
    command: RW0C1AdmitEvidenceCommandV1

    def __post_init__(self) -> None:
        if type(self.command) is not RW0C1AdmitEvidenceCommandV1:
            raise _integrity_failure() from None

    def __repr__(self) -> str:
        return "<_RW0C1AdmissionOwnerRead>"


@dataclass(frozen=True, slots=True, repr=False)
class _RW0C1AdmissionOwnerGraph:
    basis: object
    program: object
    work: object
    work_spec_binding: object
    attempt_fence: object
    author_effect_fence: object
    author_command: object
    author_delivery: object
    selection_disposition: object
    selection_receipt: object
    selection_head: object
    selected_proposal: object
    selected_artifact: object
    effect_head: object
    delivery_head: object
    global_stop: object
    located_owner_rows: tuple[tuple[RW0C1OwnerRowLocatorV1, object], ...]
    section41_evidence_rows: tuple[RW0C1OwnerRowSnapshot, ...]

    def __repr__(self) -> str:
        return "<_RW0C1AdmissionOwnerGraph>"


def _conflict(reason: RW0C1ConflictReasonV1) -> RW0C1ConflictV1:
    return RW0C1ConflictV1(reason)


def _integrity_failure() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(
        SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
    )


def _exact_mapping(left: RW0C1RowValue, right: RW0C1RowValue) -> bool:
    return left.table_name == right.table_name and left.as_tuple() == right.as_tuple()


def _cognitive_family_by_schema(
    rows: tuple[object, ...], expected_schema_id: str,
) -> object:
    matches = [
        item.values
        for item in rows
        if getattr(item.values, "schema_id", None) == expected_schema_id
    ]
    if len(matches) != 1:
        raise _integrity_failure() from None
    return matches[0]


def _selection_result_from_owner_rows(
    disposition: object,
    receipt: object,
) -> PreExecutionPlanDispositionResultProjectionV1:
    fields = {
        "schema_id": "governed-execution.nwp-pre-execution-plan-disposition-result.v1",
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
        "authority_selection_observation_ref": (
            receipt.authority_selection_observation_ref
        ),
        "authority_selection_observation_digest": (
            receipt.authority_selection_observation_digest
        ),
        "mutation_graph_digest": receipt.mutation_graph_digest,
        "recorded_at": receipt.committed_at,
        "result_projection_digest": receipt.result_projection_digest,
    }
    try:
        return PreExecutionPlanDispositionResultProjectionV1(**fields)
    except Exception:
        raise _integrity_failure() from None


def _read_phase_selection_owner_rows(
    capability: object,
    basis: object,
) -> tuple[object, object, object, object, object, object]:
    disposition = _read_disposition_by_ref(capability, basis.disposition_ref)
    if disposition is None:
        raise _RW0C1OwnerRowMissing() from None
    family = _read_proposal_family_rows(capability, disposition)
    proposal = _cognitive_family_by_schema(
        family, _MODEL_PROPOSAL_SCHEMA
    )
    artifact = _cognitive_family_by_schema(
        family, _ARTIFACT_BINDING_SCHEMA
    )
    k8 = k8_mapping_from_phase_basis(basis)
    selection_head = _read_cognitive_exact_row(
        capability,
        table="development_pre_execution_selection_heads",
        where=(
            "program_ref = ? AND semantic_attempt_ref = ? AND candidate_ref = ? "
            "AND effect_intent_ref = ? AND author_command_ref = ? "
            "AND attempt_fence_ref = ? AND effect_fence_ref = ? "
            "AND delivery_attempt_ref = ?"
        ),
        parameters=tuple(k8.values()),
    )
    receipt = _read_cognitive_exact_row(
        capability,
        table="development_cognitive_mutation_receipts",
        where="disposition_ref = ?",
        parameters=(basis.disposition_ref,),
    )
    if selection_head is None or receipt is None:
        raise _RW0C1OwnerRowMissing() from None
    if (
        getattr(selection_head, "schema_id", None) != _SELECTION_HEAD_SCHEMA
        or getattr(receipt, "schema_id", None) != _COGNITIVE_RECEIPT_SCHEMA
    ):
        raise _integrity_failure() from None
    result = _selection_result_from_owner_rows(disposition, receipt)
    return disposition, receipt, result, selection_head, proposal, artifact


def _read_phase_development_owner_rows(
    capability: object,
    basis: object,
) -> tuple[object, object, object, object, object, object, object, object, object]:
    admission_command: RW0C1AdmitEvidenceCommandV1 | None = None
    phase_basis = basis
    if type(basis) is _RW0C1AdmissionOwnerRead:
        phase_basis = basis.basis
        admission_command = basis.command
    lineage = phase_basis.c2b3d_lineage
    program = _read_development_program_head_and_current_version(
        capability, lineage.program_ref
    )
    work = _read_development_work_item_head_and_revision_by_exact_ref(
        capability,
        lineage.program_ref,
        lineage.work_item_ref,
        lineage.work_item_revision_ref,
    )
    if program is None or work is None:
        raise _RW0C1OwnerRowMissing() from None
    if admission_command is not None and not _current_state_matches_admission_command(
        admission_command,
        program,
        work,
    ):
        raise _RW0C1CurrentStateConflict() from None
    work_spec = _read_development_work_spec_safe_binding(
        capability,
        lineage.program_ref,
        lineage.program_version_ref,
        lineage.work_item_ref,
        lineage.work_item_revision_ref,
    )
    effect = _read_development_attempt_fence_command_effect_aggregate(
        capability,
        lineage.program_ref,
        lineage.semantic_attempt_ref,
        lineage.effect_intent_ref,
    )
    authority = _read_development_authority_evaluation_by_exact_ref(
        capability,
        lineage.program_ref,
        lineage.authority_evaluation_ref,
    )
    effect_head = _read_development_effect_head(
        capability, lineage.program_ref, lineage.effect_intent_ref
    )
    delivery = _read_development_delivery_head(
        capability, lineage.program_ref, lineage.effect_intent_ref
    )
    stop = _read_global_stop_current(capability)
    if any(
        item is None
        for item in (
            program,
            work,
            work_spec,
            effect,
            authority,
            effect_head,
            delivery,
            stop,
        )
    ):
        raise _RW0C1OwnerRowMissing() from None
    return (
        program,
        work,
        work_spec,
        effect,
        authority,
        effect_head,
        delivery,
        stop,
        lineage,
    )


def _current_state_matches_phase_command(
    command: RW0C1EstablishPhaseCommandV1,
    program: object,
    work: object,
) -> bool:
    return bool(
        program.program_head.head_revision == command.expected_program_head_revision
        and program.program_head.head_digest == command.expected_program_head_digest
        and work.work_item_head.head_revision == command.expected_work_item_head_revision
        and work.work_item_head.head_digest == command.expected_work_item_head_digest
        and work.is_current
    )


def _current_state_matches_admission_command(
    command: RW0C1AdmitEvidenceCommandV1,
    program: object,
    work: object,
) -> bool:
    return bool(
        program.program_head.head_revision == command.expected_program_head_revision
        and program.program_head.head_digest == command.expected_program_head_digest
        and work.work_item_head.head_revision == command.expected_work_item_head_revision
        and work.work_item_head.head_digest == command.expected_work_item_head_digest
        and work.is_current
    )


def _admission_command_matches_phase_preimages(
    command: RW0C1AdmitEvidenceCommandV1,
    phase: RW0C1RowValue,
) -> bool:
    """Bind every admission command to the immutable phase CAS preimages.

    Those four fields are the durable source used to reconstruct a command
    digest during guarded readback and recovery.  Accepting a later mutable
    head here would make a successfully committed command unreconstructible
    once the current heads progressed again.
    """

    return bool(
        command.expected_program_head_revision
        == phase.value("expected_program_head_revision")
        and command.expected_program_head_digest
        == phase.value("expected_program_head_digest")
        and command.expected_work_item_head_revision
        == phase.value("expected_work_item_head_revision")
        and command.expected_work_item_head_digest
        == phase.value("expected_work_item_head_digest")
    )


def _phase_k8_tuple(basis: object) -> tuple[str, ...]:
    return tuple(typing.cast(str, value) for value in k8_mapping_from_phase_basis(basis).values())


def _phase_replay(
    capability: object,
    command: RW0C1EstablishPhaseCommandV1,
    receipt: RW0C1RowValue,
) -> RW0C1EstablishPhaseResultV1 | RW0C1ConflictV1:
    if receipt.value("command_digest") != command.command_digest:
        return _conflict(RW0C1ConflictReasonV1.MUTATION_REF_REUSE)
    if receipt.value("mutation_family") != "establish_rw0_phase":
        return _conflict(RW0C1ConflictReasonV1.MUTATION_REF_REUSE)
    phase = _read_phase_by_pair(
        capability, command.phase_basis.basis_ref, command.phase_basis.basis_digest
    )
    if phase is None:
        raise _integrity_failure() from None
    relation_set = _read_relation_set(
        capability=capability,
        phase_basis_ref=command.phase_basis.basis_ref,
        membership_ref=None,
    )
    _verify_phase_family_rows(
        phase, relation_set, receipt, capability=capability
    )
    if (
        phase.value("work_spec_ref") != command.work_spec.work_spec_ref
        or phase.value("work_spec_digest") != command.work_spec.work_spec_digest
        or phase.value("work_spec_safe_projection_digest")
        != command.work_spec_safe_projection_digest
        or phase.value("expected_program_head_revision")
        != command.expected_program_head_revision
        or phase.value("expected_program_head_digest")
        != command.expected_program_head_digest
        or phase.value("expected_work_item_head_revision")
        != command.expected_work_item_head_revision
        or phase.value("expected_work_item_head_digest")
        != command.expected_work_item_head_digest
    ):
        raise _integrity_failure() from None
    result = RW0C1EstablishPhaseResultV1(
        mutation_ref=command.mutation_ref,
        command_digest=command.command_digest,
        disposition="exact_replay",
        phase_basis_ref=command.phase_basis.basis_ref,
        phase_basis_digest=command.phase_basis.basis_digest,
        k8_digest=typing.cast(str, phase.value("k8_digest")),
        phase_graph_digest=typing.cast(str, phase.value("phase_graph_digest")),
        receipt_digest=typing.cast(str, receipt.value("receipt_digest")),
        committed_at=typing.cast(str, receipt.value("committed_at")),
    )
    if result.committed_projection_digest() != receipt.value("result_projection_digest"):
        raise _integrity_failure() from None
    return result


def _resolve_rw0_c1_phase_establishment_after_fencing(
    *,
    capability: object,
    command: RW0C1EstablishPhaseCommandV1,
) -> _RW0C1PhasePreparation | RW0C1EstablishPhaseResultV1 | RW0C1ConflictV1:
    if type(command) is not RW0C1EstablishPhaseCommandV1:
        raise _integrity_failure() from None
    receipt = _read_receipt(capability, command.mutation_ref)
    if receipt is not None:
        return _phase_replay(capability, command, receipt)

    basis = command.phase_basis
    by_ref = _read_phase_by_ref(capability, basis.basis_ref)
    by_digest = _read_phase_by_digest(capability, basis.basis_digest)
    by_k8 = _read_phase_by_k8(capability, _phase_k8_tuple(basis))
    if by_ref is not None or by_digest is not None:
        return _conflict(RW0C1ConflictReasonV1.PHASE_IDENTITY_COLLISION)
    if by_k8 is not None:
        return _conflict(RW0C1ConflictReasonV1.K8_COLLISION)
    relation_ref = relation_reference(
        phase_basis_ref=basis.basis_ref,
        phase_basis_digest=basis.basis_digest,
        subject_type="phase_establishment",
        subject_membership_ref=None,
        relation_rank=0,
    )
    if _read_relation_by_ref(capability, relation_ref) is not None:
        return _conflict(RW0C1ConflictReasonV1.RELATION_IDENTITY_COLLISION)

    try:
        (
            disposition,
            cognitive_receipt,
            selection_result,
            selection_head,
            proposal,
            artifact,
        ) = _read_phase_selection_owner_rows(capability, basis)
        (
            program,
            work,
            work_spec_binding,
            effect,
            authority,
            effect_head,
            delivery,
            stop,
            _lineage,
        ) = _read_phase_development_owner_rows(capability, basis)
    except _RW0C1OwnerRowMissing:
        return _conflict(RW0C1ConflictReasonV1.OWNER_ROW_MISSING)
    if not _current_state_matches_phase_command(command, program, work):
        return _conflict(RW0C1ConflictReasonV1.CURRENT_STATE_CONFLICT)
    if (
        work_spec_binding.safe_projection_digest
        != command.work_spec_safe_projection_digest
        or authority.authority_evaluation_digest
        != basis.c2b3d_lineage.authority_evaluation_digest
    ):
        return _conflict(RW0C1ConflictReasonV1.CURRENT_STATE_CONFLICT)
    return _RW0C1PhasePreparation(
        command=command,
        disposition=disposition,
        selection_result=selection_result,
        selection_head=selection_head,
        selected_proposal=proposal,
        selected_artifact=artifact,
        cognitive_receipt=cognitive_receipt,
        work_spec_binding=work_spec_binding,
        attempt_fence=effect.attempt_fence.attempt_fence,
        author_effect_fence=effect.author_effect_fence.effect_fence,
        author_command=effect.author_command.author_command,
        author_delivery_row=delivery.current_delivery_attempt,
        effect_head=effect_head,
        delivery_head=delivery.delivery_head,
        global_stop=stop,
    )


def _owner_operand(
    *,
    ordinal: int,
    role: str,
    owner_role: str,
    schema_id: str,
    row_ref: str,
    row_digest: str,
    revision: int | None = None,
    subrole: str | None = None,
    owner_ordinal: int | None = None,
) -> RW0C1OperandIdentity:
    return RW0C1OperandIdentity(
        ordinal,
        role,
        "existing_owner_row",
        None,
        None,
        None,
        owner_role,
        row_ref,
        revision,
        subrole,
        owner_ordinal,
        None,
        None,
        None,
        schema_id,
        row_ref,
        row_digest,
        None,
    )


def _transient_operand(
    ordinal: int,
    binding: RW0C1TransientPrivateBindingV1,
) -> RW0C1OperandIdentity:
    return RW0C1OperandIdentity(
        ordinal,
        binding.role,
        "transient_private_binding",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        binding.binding_kind,
        binding.error_reason,
        None,
        binding.operand_schema_id,
        binding.operand_ref,
        binding.operand_digest,
        binding.operand_scope_digest,
    )


def _snapshot_operand(
    ordinal: int,
    binding: RW0C1AdmissionSnapshotBindingV1,
) -> RW0C1OperandIdentity:
    return RW0C1OperandIdentity(
        ordinal,
        binding.role,
        "admission_snapshot_binding",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        binding.snapshot_kind,
        binding.operand_schema_id,
        binding.operand_ref,
        binding.operand_digest,
        binding.operand_scope_digest,
    )


def _phase_snapshots(
    preparation: _RW0C1PhasePreparation,
) -> tuple[RW0C1AdmissionSnapshotBindingV1, ...]:
    basis = preparation.command.phase_basis
    k8 = k8_mapping_from_phase_basis(basis)
    selection = RW0C1AdmissionSnapshotBindingV1(
        "selection_head",
        "selection_head_snapshot",
        basis.basis_ref,
        basis.basis_digest,
        (
            ("owner_schema_id", preparation.selection_head.schema_id),
            *((name, value) for name, value in k8.items()),
            ("current_proposal_ref", preparation.selection_head.current_proposal_ref),
            ("current_disposition_ref", preparation.selection_head.current_disposition_ref),
            ("current_disposition", preparation.selection_head.current_disposition),
            ("head_revision", preparation.selection_head.head_revision),
            ("updated_at", preparation.selection_head.updated_at),
            ("head_digest", preparation.selection_head.head_digest),
        ),
    )
    effect = RW0C1AdmissionSnapshotBindingV1(
        "effect_head",
        "effect_head_snapshot",
        basis.basis_ref,
        basis.basis_digest,
        (
            ("owner_schema_id", preparation.effect_head.schema_id),
            ("program_ref", preparation.effect_head.program_ref),
            ("effect_intent_ref", preparation.effect_head.effect_intent_ref),
            ("current_effect_fence_ref", preparation.effect_head.current_effect_fence_ref),
            ("head_revision", preparation.effect_head.head_revision),
            ("effect_state", preparation.effect_head.effect_state),
            (
                "cancellation_effect_intent_ref",
                preparation.effect_head.cancellation_effect_intent_ref,
            ),
            ("updated_at", preparation.effect_head.updated_at),
            ("head_digest", preparation.effect_head.head_digest),
        ),
    )
    delivery = RW0C1AdmissionSnapshotBindingV1(
        "delivery_head",
        "delivery_head_snapshot",
        basis.basis_ref,
        basis.basis_digest,
        (
            ("owner_schema_id", preparation.delivery_head.schema_id),
            ("program_ref", preparation.delivery_head.program_ref),
            ("effect_intent_ref", preparation.delivery_head.effect_intent_ref),
            (
                "current_delivery_attempt_ref",
                preparation.delivery_head.current_delivery_attempt_ref,
            ),
            ("head_revision", preparation.delivery_head.head_revision),
            ("delivery_state", preparation.delivery_head.delivery_state),
            ("updated_at", preparation.delivery_head.updated_at),
            ("head_digest", preparation.delivery_head.head_digest),
        ),
    )
    stop = RW0C1AdmissionSnapshotBindingV1(
        "global_stop_current",
        "global_stop_snapshot",
        basis.basis_ref,
        basis.basis_digest,
        (
            ("owner_schema_id", GLOBAL_STOP_SCHEMA_ID),
            ("stop_ref", preparation.global_stop.state.stop_ref),
            ("version", preparation.global_stop.state.version),
            ("state", preparation.global_stop.state.status.value),
        ),
    )
    return selection, effect, delivery, stop


def _phase_operands(
    preparation: _RW0C1PhasePreparation,
) -> tuple[RW0C1OperandIdentity, ...]:
    command = preparation.command
    work_binding = preparation.work_spec_binding
    delivery = preparation.author_delivery_row
    snapshots = _phase_snapshots(preparation)
    transient = RW0C1TransientPrivateBindingV1.work_spec(
        role="transient_work_spec",
        value=command.work_spec,
        safe_projection_digest=command.work_spec_safe_projection_digest,
    )
    return (
        _owner_operand(
            ordinal=0,
            role="selection_disposition",
            owner_role="development_pre_execution_disposition",
            schema_id=preparation.disposition.schema_id,
            row_ref=command.phase_basis.disposition_ref,
            row_digest=command.phase_basis.disposition_digest,
        ),
        _owner_operand(
            ordinal=1,
            role="selection_receipt",
            owner_role="development_cognitive_mutation_receipt",
            schema_id=preparation.cognitive_receipt.schema_id,
            row_ref=preparation.cognitive_receipt.mutation_ref,
            row_digest=preparation.cognitive_receipt.receipt_digest,
        ),
        _snapshot_operand(2, snapshots[0]),
        _owner_operand(
            ordinal=3,
            role="selected_proposal",
            owner_role="development_model_proposal",
            schema_id=preparation.selected_proposal.schema_id,
            row_ref=preparation.selected_proposal.proposal_ref,
            row_digest=preparation.selected_proposal.proposal_digest,
        ),
        _owner_operand(
            ordinal=4,
            role="selected_artifact",
            owner_role="development_private_proposal_artifact_binding",
            schema_id=preparation.selected_artifact.schema_id,
            row_ref=preparation.selected_artifact.artifact_ref,
            row_digest=preparation.selected_artifact.artifact_binding_digest,
        ),
        _owner_operand(
            ordinal=5,
            role="work_spec_binding",
            owner_role="development_work_spec_binding",
            schema_id=work_binding.schema_id,
            row_ref=work_binding.work_spec_ref,
            row_digest=work_binding.work_spec_binding_digest,
        ),
        _transient_operand(6, transient),
        _owner_operand(
            ordinal=7,
            role="attempt_fence",
            owner_role="development_attempt_fence",
            schema_id=preparation.attempt_fence.schema_id,
            row_ref=preparation.attempt_fence.attempt_fence_ref,
            row_digest=preparation.attempt_fence.attempt_fence_digest,
        ),
        _owner_operand(
            ordinal=8,
            role="author_effect_fence",
            owner_role="development_effect_fence",
            schema_id=preparation.author_effect_fence.schema_id,
            row_ref=preparation.author_effect_fence.effect_fence_ref,
            row_digest=preparation.author_effect_fence.effect_fence_digest,
        ),
        _owner_operand(
            ordinal=9,
            role="author_command",
            owner_role="development_author_command",
            schema_id=preparation.author_command.schema_id,
            row_ref=preparation.author_command.command_ref,
            row_digest=preparation.author_command.command_digest,
        ),
        _owner_operand(
            ordinal=10,
            role="author_delivery",
            owner_role="development_delivery_attempt",
            schema_id=delivery.wrapper_schema_id,
            row_ref=delivery.delivery_attempt_ref,
            row_digest=delivery.delivery_attempt_digest,
        ),
        _snapshot_operand(11, snapshots[1]),
        _snapshot_operand(12, snapshots[2]),
        _snapshot_operand(13, snapshots[3]),
    )


def _phase_row_values(
    preparation: _RW0C1PhasePreparation,
    *,
    operation_timestamp: str,
    k8_digest: str,
    relation_set_value: str,
    graph_digest: str,
) -> dict[str, object]:
    command = preparation.command
    basis = command.phase_basis
    lineage = basis.c2b3d_lineage.to_mapping()
    values: dict[str, object] = {
        "schema_id": _PHASE_ROW_SCHEMA,
        "phase_basis_schema_id": basis.schema_id,
        "phase_basis_ref": basis.basis_ref,
        **lineage,
        "selected_proposal_ref": basis.selected_proposal_ref,
        "selected_proposal_digest": basis.selected_proposal_digest,
        "selected_artifact_ref": basis.selected_artifact_ref,
        "selected_artifact_digest": basis.selected_artifact_digest,
        "selected_artifact_binding_digest": basis.selected_artifact_binding_digest,
        "selected_plan_safe_projection_digest": basis.selected_plan_safe_projection_digest,
        "disposition_ref": basis.disposition_ref,
        "disposition_digest": basis.disposition_digest,
        "disposition": basis.disposition,
        "selection_head_revision": basis.selection_head_revision,
        "selection_head_digest": basis.selection_head_digest,
        "current_effect_head_revision": basis.current_effect_head_revision,
        "current_effect_head_state": basis.current_effect_head_state,
        "current_effect_head_digest": basis.current_effect_head_digest,
        "current_delivery_head_revision": basis.current_delivery_head_revision,
        "current_delivery_head_state": basis.current_delivery_head_state,
        "current_delivery_head_digest": basis.current_delivery_head_digest,
        "global_stop_ref": basis.global_stop_ref,
        "global_stop_version": basis.global_stop_version,
        "global_stop_state": basis.global_stop_state,
        "path_scope_digest": basis.path_scope_digest,
        "phase_basis_digest": basis.basis_digest,
        "k8_digest": k8_digest,
        "expected_program_head_revision": command.expected_program_head_revision,
        "expected_program_head_digest": command.expected_program_head_digest,
        "expected_work_item_head_revision": command.expected_work_item_head_revision,
        "expected_work_item_head_digest": command.expected_work_item_head_digest,
        "selection_head_updated_at": preparation.selection_head.updated_at,
        "current_effect_head_fence_ref": preparation.effect_head.current_effect_fence_ref,
        "current_effect_head_cancellation_effect_intent_ref": (
            preparation.effect_head.cancellation_effect_intent_ref
        ),
        "current_effect_head_updated_at": preparation.effect_head.updated_at,
        "current_delivery_head_attempt_ref": (
            preparation.delivery_head.current_delivery_attempt_ref
        ),
        "current_delivery_head_updated_at": preparation.delivery_head.updated_at,
        "establishment_mutation_ref": command.mutation_ref,
        "established_at": operation_timestamp,
        "relation_count": 1,
        "relation_set_digest": relation_set_value,
        "phase_graph_digest": graph_digest,
    }
    return values


def _relation_and_operand_rows(
    *,
    phase_basis_ref: str,
    phase_basis_digest: str,
    relation_ref: str,
    relation_semantic_digest: str,
    subject_type: str,
    membership_ref: str | None,
    membership_digest_value: str | None,
    kind_rank: int | None,
    value_ref: str | None,
    value_digest: str | None,
    value_schema_id: str | None,
    specification: RW0C1RelationSpecification,
    evaluated_at: str | None,
    operand_set_value: str,
    operands: tuple[RW0C1OperandIdentity, ...],
) -> tuple[RW0C1RowValue, tuple[RW0C1RowValue, ...]]:
    relation = build_row(
        "rw0_relation_bindings",
        {
            "schema_id": _RELATION_ROW_SCHEMA,
            "phase_basis_ref": phase_basis_ref,
            "phase_basis_digest": phase_basis_digest,
            "relation_ref": relation_ref,
            "relation_digest": relation_semantic_digest,
            "subject_type": subject_type,
            "subject_membership_ref": membership_ref,
            "subject_membership_digest": membership_digest_value,
            "subject_kind_rank": kind_rank,
            "subject_value_ref": value_ref,
            "subject_value_digest": value_digest,
            "subject_value_schema_id": value_schema_id,
            "relation_rank": specification.relation_rank,
            "relation_schema_id": specification.relation_schema_id,
            "relation_version": 1,
            "proof_mode": specification.proof_mode,
            "profile_ref": specification.profile_ref,
            "profile_digest": specification.profile_digest,
            "evaluated_at": evaluated_at,
            "operand_count": len(operands),
            "operand_set_digest": operand_set_value,
        },
    )
    operand_rows = tuple(
        build_row(
            "rw0_relation_operands",
            {
                "schema_id": _OPERAND_ROW_SCHEMA,
                "phase_basis_ref": phase_basis_ref,
                "relation_ref": relation_ref,
                "relation_digest": relation_semantic_digest,
                **operand.to_mapping(),
            },
        )
        for operand in operands
    )
    return relation, operand_rows


def _complete_rw0_c1_phase_establishment_preparation(
    preparation: _RW0C1PhasePreparation,
    *,
    operation_timestamp: str,
) -> RW0C1WritePlan | RW0C1ConflictV1:
    if type(preparation) is not _RW0C1PhasePreparation:
        raise _integrity_failure() from None
    command = preparation.command
    basis = command.phase_basis
    try:
        _b1.validate_phase_entry_basis(
            basis=basis,
            lineage=basis.c2b3d_lineage,
            selection_result=preparation.selection_result,
            selection_head=preparation.selection_head,
            selected_proposal=preparation.selected_proposal,
            selected_artifact=preparation.selected_artifact,
            work_spec=command.work_spec,
            attempt_fence=preparation.attempt_fence,
            author_effect_fence=preparation.author_effect_fence,
            author_command=preparation.author_command,
            author_delivery=preparation.author_delivery_row.delivery_envelope,
            effect_head=preparation.effect_head,
            delivery_head=preparation.delivery_head,
            global_stop=preparation.global_stop,
        )
        operands = _phase_operands(preparation)
        relation_ref = relation_reference(
            phase_basis_ref=basis.basis_ref,
            phase_basis_digest=basis.basis_digest,
            subject_type="phase_establishment",
            subject_membership_ref=None,
            relation_rank=0,
        )
        relation_semantic_digest, operand_set_value = relation_digest(
            phase_basis_ref=basis.basis_ref,
            phase_basis_digest=basis.basis_digest,
            relation_ref=relation_ref,
            subject_type="phase_establishment",
            subject_membership_ref=None,
            subject_kind_rank=None,
            subject_value_ref=None,
            subject_value_digest=None,
            subject_value_schema_id=None,
            specification=_PHASE_RELATION_SPEC,
            evaluated_at=None,
            operands=operands,
        )
        relation_set_value = relation_set_digest(
            phase_basis_ref=basis.basis_ref,
            subject_type="phase_establishment",
            subject_ref=basis.basis_ref,
            relations=((0, relation_ref, relation_semantic_digest),),
        )
        k8_digest = k8_digest_from_phase_basis(basis)
        graph_digest = phase_graph_digest(
            {
                "schema_id": "governed-execution.nwp-rw0-c1-phase-graph.v1",
                "phase_basis_ref": basis.basis_ref,
                "phase_basis_digest": basis.basis_digest,
                "k8": k8_mapping_from_phase_basis(basis),
                "relation_count": 1,
                "relation_set_digest": relation_set_value,
                "establishment_mutation_ref": command.mutation_ref,
                "established_at": operation_timestamp,
            }
        )
        phase = build_row(
            "rw0_phase_instances",
            _phase_row_values(
                preparation,
                operation_timestamp=operation_timestamp,
                k8_digest=k8_digest,
                relation_set_value=relation_set_value,
                graph_digest=graph_digest,
            ),
        )
        relation, operand_rows = _relation_and_operand_rows(
            phase_basis_ref=basis.basis_ref,
            phase_basis_digest=basis.basis_digest,
            relation_ref=relation_ref,
            relation_semantic_digest=relation_semantic_digest,
            subject_type="phase_establishment",
            membership_ref=None,
            membership_digest_value=None,
            kind_rank=None,
            value_ref=None,
            value_digest=None,
            value_schema_id=None,
            specification=_PHASE_RELATION_SPEC,
            evaluated_at=None,
            operand_set_value=operand_set_value,
            operands=operands,
        )
        provisional = RW0C1EstablishPhaseResultV1(
            mutation_ref=command.mutation_ref,
            command_digest=command.command_digest,
            disposition="fresh_committed",
            phase_basis_ref=basis.basis_ref,
            phase_basis_digest=basis.basis_digest,
            k8_digest=k8_digest,
            phase_graph_digest=graph_digest,
            receipt_digest="0" * 64,
            committed_at=operation_timestamp,
        )
        receipt_value = RW0C1MutationReceiptV1(
            mutation_ref=command.mutation_ref,
            mutation_family="establish_rw0_phase",
            command_schema_id=command.schema_id,
            command_digest=command.command_digest,
            phase_basis_ref=basis.basis_ref,
            phase_basis_digest=basis.basis_digest,
            membership_ref=None,
            membership_digest=None,
            kind_rank=None,
            value_ref=None,
            value_digest=None,
            value_schema_id=None,
            result_class="rw0_phase_established",
            result_projection_digest=provisional.committed_projection_digest(),
            admission_graph_digest=graph_digest,
            outcome="committed",
            committed_at=operation_timestamp,
        )
        receipt = build_row(
            "rw0_c1_mutation_receipts",
            {
                key: value
                for key, value in receipt_value.identity_mapping().items()
            },
        )
        result = RW0C1EstablishPhaseResultV1(
            mutation_ref=command.mutation_ref,
            command_digest=command.command_digest,
            disposition="fresh_committed",
            phase_basis_ref=basis.basis_ref,
            phase_basis_digest=basis.basis_digest,
            k8_digest=k8_digest,
            phase_graph_digest=graph_digest,
            receipt_digest=receipt_value.receipt_digest,
            committed_at=operation_timestamp,
        )
        return RW0C1WritePlan(
            "establish_rw0_phase",
            (phase, relation, *operand_rows, receipt),
            operation_timestamp,
            result,
        )
    except (RW0C1PreflightError, SQLiteMutationStoreError):
        raise
    except Exception:
        return _conflict(RW0C1ConflictReasonV1.RELATION_FAILURE)


def _verify_phase_family_rows(
    phase: RW0C1RowValue,
    relation_set: object,
    receipt: RW0C1RowValue,
    *,
    capability: object,
) -> None:
    phase_ref = typing.cast(str, phase.value("phase_basis_ref"))
    phase_digest = typing.cast(str, phase.value("phase_basis_digest"))
    relation = relation_set.relations[0] if len(relation_set.relations) == 1 else None
    if (
        phase.table_name != "rw0_phase_instances"
        or receipt.table_name != "rw0_c1_mutation_receipts"
        or relation is None
        or len(relation.operands) != 14
        or relation.binding.value("subject_type")
        != "phase_establishment"
        or relation.binding.value("phase_basis_ref") != phase_ref
        or relation.binding.value("phase_basis_digest") != phase_digest
        or relation.binding.value("subject_membership_ref") is not None
        or relation.binding.value("subject_membership_digest") is not None
        or relation.binding.value("subject_kind_rank") is not None
        or relation.binding.value("subject_value_ref") is not None
        or relation.binding.value("subject_value_digest") is not None
        or relation.binding.value("subject_value_schema_id") is not None
        or relation.binding.value("relation_rank") != 0
        or relation.binding.value("relation_schema_id")
        != _PHASE_RELATION_SCHEMA
        or relation.binding.value("relation_version") != 1
        or relation.binding.value("proof_mode")
        != "relation_attested_at_admission"
        or relation.binding.value("profile_ref") is not None
        or relation.binding.value("profile_digest") is not None
        or relation.binding.value("evaluated_at") is not None
        or relation.binding.value("operand_count") != 14
        or receipt.value("phase_basis_ref") != phase.value("phase_basis_ref")
        or receipt.value("phase_basis_digest") != phase.value("phase_basis_digest")
        or receipt.value("membership_ref") is not None
        or receipt.value("membership_digest") is not None
        or receipt.value("kind_rank") is not None
        or receipt.value("value_ref") is not None
        or receipt.value("value_digest") is not None
        or receipt.value("value_schema_id") is not None
        or receipt.value("admission_graph_digest") != phase.value("phase_graph_digest")
        or receipt.value("committed_at") != phase.value("established_at")
        or receipt.value("mutation_family") != "establish_rw0_phase"
        or receipt.value("command_schema_id")
        != "governed-execution.nwp-rw0-c1-establish-phase-command.v1"
        or receipt.value("result_class") != "rw0_phase_established"
        or receipt.value("outcome") != "committed"
        or receipt.value("mutation_ref") != phase.value("establishment_mutation_ref")
    ):
        raise _integrity_failure() from None
    roles = tuple(
        operand.value("operand_role")
        for operand in relation.operands
    )
    if roles != (
        "selection_disposition",
        "selection_receipt",
        "selection_head",
        "selected_proposal",
        "selected_artifact",
        "work_spec_binding",
        "transient_work_spec",
        "attempt_fence",
        "author_effect_fence",
        "author_command",
        "author_delivery",
        "effect_head",
        "delivery_head",
        "global_stop_current",
    ):
        raise _integrity_failure() from None

    operands = tuple(_operand_identity_from_row(row) for row in relation.operands)
    expected_relation_ref = relation_reference(
        phase_basis_ref=phase_ref,
        phase_basis_digest=phase_digest,
        subject_type="phase_establishment",
        subject_membership_ref=None,
        relation_rank=0,
    )
    expected_relation_digest, expected_operand_set = relation_digest(
        phase_basis_ref=phase_ref,
        phase_basis_digest=phase_digest,
        relation_ref=expected_relation_ref,
        subject_type="phase_establishment",
        subject_membership_ref=None,
        subject_kind_rank=None,
        subject_value_ref=None,
        subject_value_digest=None,
        subject_value_schema_id=None,
        specification=_PHASE_RELATION_SPEC,
        evaluated_at=None,
        operands=operands,
    )
    expected_relation_set = relation_set_digest(
        phase_basis_ref=phase_ref,
        subject_type="phase_establishment",
        subject_ref=phase_ref,
        relations=((0, expected_relation_ref, expected_relation_digest),),
    )
    basis = _phase_basis_from_row(phase)
    expected_k8 = k8_digest_from_phase_basis(basis)
    expected_graph = phase_graph_digest(
        {
            "schema_id": "governed-execution.nwp-rw0-c1-phase-graph.v1",
            "phase_basis_ref": phase_ref,
            "phase_basis_digest": phase_digest,
            "k8": k8_mapping_from_phase_basis(basis),
            "relation_count": 1,
            "relation_set_digest": expected_relation_set,
            "establishment_mutation_ref": phase.value("establishment_mutation_ref"),
            "established_at": phase.value("established_at"),
        }
    )
    if (
        relation.binding.value("relation_ref") != expected_relation_ref
        or relation.binding.value("relation_digest") != expected_relation_digest
        or relation.binding.value("operand_set_digest") != expected_operand_set
        or phase.value("relation_count") != 1
        or phase.value("relation_set_digest") != expected_relation_set
        or phase.value("k8_digest") != expected_k8
        or phase.value("phase_graph_digest") != expected_graph
    ):
        raise _integrity_failure() from None

    immutable_ordinals = (0, 1, 3, 4, 5, 7, 8, 9, 10)
    for ordinal in immutable_ordinals:
        operand = relation.operands[ordinal]
        if operand.value("operand_source") != "existing_owner_row":
            raise _integrity_failure() from None
        locator = _owner_locator_from_operand(operand)
        row = _read_command_owner_row(capability, locator)
        if row is None:
            raise _integrity_failure() from None
        schema_id, row_ref, row_digest = _owner_descriptor(locator.owner_role, row)
        if (
            schema_id != operand.value("operand_schema_id")
            or row_ref != operand.value("operand_ref")
            or row_ref != locator.row_ref
            or row_digest != locator.row_digest
        ):
            raise _integrity_failure() from None

    transient = relation.operands[6]
    if (
        transient.value("operand_source") != "transient_private_binding"
        or transient.value("transient_binding_kind") != "work_spec"
        or transient.value("transient_error_reason") is not None
        or transient.value("operand_schema_id")
        != "governed-execution.nwp-rw0-c1-transient-work-spec-binding.v1"
        or transient.value("operand_ref") != phase.value("work_spec_ref")
        or transient.value("operand_digest") != phase.value("work_spec_digest")
        or transient.value("operand_scope_digest")
        != phase.value("work_spec_safe_projection_digest")
    ):
        raise _integrity_failure() from None

    snapshot_rows = (relation.operands[2], *relation.operands[11:14])
    expected_snapshots = _admission_snapshots_from_phase(phase)
    for row, snapshot in zip(snapshot_rows, expected_snapshots, strict=True):
        expected = _snapshot_operand(
            typing.cast(int, row.value("operand_ordinal")), snapshot
        )
        if any(row.value(name) != getattr(expected, name) for name in expected.__slots__):
            raise _integrity_failure() from None


def _readback_rw0_c1_phase_establishment(
    *, capability: object, plan: RW0C1WritePlan,
) -> RW0C1EstablishPhaseResultV1:
    if type(plan) is not RW0C1WritePlan or plan.mutation_family != "establish_rw0_phase":
        raise _integrity_failure() from None
    result = typing.cast(RW0C1EstablishPhaseResultV1, plan.result)
    phase = _read_phase_by_pair(
        capability, result.phase_basis_ref, result.phase_basis_digest
    )
    receipt = _read_receipt(capability, result.mutation_ref)
    if phase is None or receipt is None:
        raise _integrity_failure() from None
    relation_set = _read_relation_set(
        capability=capability,
        phase_basis_ref=result.phase_basis_ref,
        membership_ref=None,
    )
    _verify_phase_family_rows(
        phase, relation_set, receipt, capability=capability
    )
    observed = (
        phase,
        relation_set.relations[0].binding,
        *relation_set.relations[0].operands,
        receipt,
    )
    if len(observed) != len(plan.rows) or any(
        not _exact_mapping(left, right)
        for left, right in zip(observed, plan.rows, strict=True)
    ):
        raise _integrity_failure() from None
    if (
        receipt.value("receipt_digest") != result.receipt_digest
        or receipt.value("result_projection_digest")
        != result.committed_projection_digest()
    ):
        raise _integrity_failure() from None
    return result


def _recover_rw0_c1_phase_establishment_after_fencing(
    *, capability: object, probe: RW0C1RecoveryProbeV1,
) -> RW0C1RecoveryResultV1:
    if (
        type(probe) is not RW0C1RecoveryProbeV1
        or probe.mutation_family != "establish_rw0_phase"
    ):
        raise _integrity_failure() from None
    try:
        receipt = _read_receipt(capability, probe.mutation_ref)
        phase_ref = _read_phase_by_ref(capability, probe.phase_basis_ref)
        phase_digest = _read_phase_by_digest(capability, probe.phase_basis_digest)
        phase_k8 = _read_phase_by_k8(
            capability,
            typing.cast(tuple[object, ...], probe.k8),
        )
        relation_ref = relation_reference(
            phase_basis_ref=probe.phase_basis_ref,
            phase_basis_digest=probe.phase_basis_digest,
            subject_type="phase_establishment",
            subject_membership_ref=None,
            relation_rank=0,
        )
        relation = _read_relation_by_ref(capability, relation_ref)
        relation_operands = _read_relation_operands(
            capability,
            relation_ref=relation_ref,
        )
        if receipt is None:
            disposition = (
                RW0C1RecoveryDispositionV1.DEFINITELY_NOT_COMMITTED
                if phase_ref is None
                and phase_digest is None
                and phase_k8 is None
                and relation is None
                and len(relation_operands) == 0
                else RW0C1RecoveryDispositionV1.UNRESOLVED
            )
            return RW0C1RecoveryResultV1(
                probe.mutation_family,
                probe.mutation_ref,
                probe.command_digest,
                disposition,
            )
        if (
            receipt.value("mutation_family") != probe.mutation_family
            or receipt.value("command_digest") != probe.command_digest
            or receipt.value("phase_basis_ref") != probe.phase_basis_ref
            or receipt.value("phase_basis_digest") != probe.phase_basis_digest
            or phase_ref is None
            or phase_digest is None
            or phase_k8 is None
            or phase_ref.as_tuple() != phase_digest.as_tuple()
            or phase_ref.as_tuple() != phase_k8.as_tuple()
        ):
            raise ValueError("unresolved")
        relation_set = _read_relation_set(
            capability=capability,
            phase_basis_ref=probe.phase_basis_ref,
            membership_ref=None,
        )
        _verify_phase_family_rows(
            phase_ref, relation_set, receipt, capability=capability
        )
        provisional = RW0C1EstablishPhaseResultV1(
            mutation_ref=probe.mutation_ref,
            command_digest=probe.command_digest,
            disposition="exact_replay",
            phase_basis_ref=probe.phase_basis_ref,
            phase_basis_digest=probe.phase_basis_digest,
            k8_digest=typing.cast(str, phase_ref.value("k8_digest")),
            phase_graph_digest=typing.cast(str, phase_ref.value("phase_graph_digest")),
            receipt_digest=typing.cast(str, receipt.value("receipt_digest")),
            committed_at=typing.cast(str, receipt.value("committed_at")),
        )
        if provisional.committed_projection_digest() != receipt.value(
            "result_projection_digest"
        ):
            raise ValueError("unresolved")
        return RW0C1RecoveryResultV1(
            probe.mutation_family,
            probe.mutation_ref,
            probe.command_digest,
            RW0C1RecoveryDispositionV1.COMMITTED_EXACT,
            typing.cast(str, receipt.value("receipt_digest")),
            typing.cast(str, receipt.value("result_projection_digest")),
            typing.cast(str, phase_ref.value("phase_graph_digest")),
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return RW0C1RecoveryResultV1(
            probe.mutation_family,
            probe.mutation_ref,
            probe.command_digest,
            RW0C1RecoveryDispositionV1.UNRESOLVED,
        )


def _phase_basis_from_row(phase: RW0C1RowValue) -> object:
    if type(phase) is not RW0C1RowValue or phase.table_name != "rw0_phase_instances":
        raise _integrity_failure() from None
    try:
        lineage = {name: phase.value(name) for name in _L34_FIELDS}
        mapping = {
            "schema_id": phase.value("phase_basis_schema_id"),
            "basis_ref": phase.value("phase_basis_ref"),
            "c2b3d_lineage": lineage,
            "selection_key": [
                [name, lineage[name]]
                for name in _K8_FIELDS
            ],
            "selected_proposal_ref": phase.value("selected_proposal_ref"),
            "selected_proposal_digest": phase.value("selected_proposal_digest"),
            "selected_artifact_ref": phase.value("selected_artifact_ref"),
            "selected_artifact_digest": phase.value("selected_artifact_digest"),
            "selected_artifact_binding_digest": phase.value(
                "selected_artifact_binding_digest"
            ),
            "selected_plan_safe_projection_digest": phase.value(
                "selected_plan_safe_projection_digest"
            ),
            "disposition_ref": phase.value("disposition_ref"),
            "disposition_digest": phase.value("disposition_digest"),
            "disposition": phase.value("disposition"),
            "selection_head_revision": phase.value("selection_head_revision"),
            "selection_head_digest": phase.value("selection_head_digest"),
            "current_effect_head_revision": phase.value(
                "current_effect_head_revision"
            ),
            "current_effect_head_state": phase.value("current_effect_head_state"),
            "current_effect_head_digest": phase.value(
                "current_effect_head_digest"
            ),
            "current_delivery_head_revision": phase.value(
                "current_delivery_head_revision"
            ),
            "current_delivery_head_state": phase.value(
                "current_delivery_head_state"
            ),
            "current_delivery_head_digest": phase.value(
                "current_delivery_head_digest"
            ),
            "global_stop_ref": phase.value("global_stop_ref"),
            "global_stop_version": phase.value("global_stop_version"),
            "global_stop_state": phase.value("global_stop_state"),
            "path_scope_digest": phase.value("path_scope_digest"),
            "basis_digest": phase.value("phase_basis_digest"),
        }
        basis = _b1.RW0PhaseEntryBasisV1.from_mapping(mapping)
    except Exception:
        raise _integrity_failure() from None
    return basis


def _owner_value_from_typed_evidence(
    aggregate: RW0C1TypedEvidenceAggregate,
) -> object:
    registry = aggregate.registry
    rank = registry.value("kind_rank")
    if type(rank) is not int or not 1 <= rank <= 12:
        raise _integrity_failure() from None
    spec = RW0_C1_KIND_SPECS[rank - 1]
    payload = aggregate.payload.to_mapping()
    mapping: dict[str, object] = {
        "schema_id": registry.value("value_schema_id"),
        spec.ref_field: registry.value("value_ref"),
        spec.digest_field: registry.value("value_digest"),
    }
    excluded = {
        "schema_id",
        "kind_rank",
        "value_ref",
        "value_digest",
        "value_schema_id",
        "payload_row_digest",
        "allowed_effect_class_count",
        "evidence_ref_count",
    }
    for name, value in payload.items():
        if name not in excluded:
            if rank == 12 and name in {
                "candidate_ref",
                "capsule_manifest_ref",
                "portable_capsule_digest",
                "process_exit_code",
            } and value is None:
                continue
            mapping[name] = value
    ceiling_names = tuple(_b1._CEILING_FIELDS)
    if rank in {1, 2}:
        ceilings = {name: mapping.pop(name) for name in ceiling_names}
        mapping["parent_ceilings" if rank == 1 else "ceilings"] = ceilings
    if rank == 1:
        mapping["allowed_effect_classes"] = [
            child.value("effect_class") for child in aggregate.children
        ]
    if rank == 12:
        mapping["evidence_refs"] = [
            child.value("evidence_ref") for child in aggregate.children
        ]
    try:
        value = spec.value_type.from_mapping(mapping)
    except Exception:
        raise _integrity_failure() from None
    observed_ref, observed_digest, observed_schema, _scope, _mapping = (
        evidence_identity(value, rank)
    )
    if (
        observed_ref != registry.value("value_ref")
        or observed_digest != registry.value("value_digest")
        or observed_schema != registry.value("value_schema_id")
    ):
        raise _integrity_failure() from None
    return value


def _owner_descriptor(role: str, row: object) -> tuple[str, str, str]:
    if type(row) is RW0C1OwnerRowSnapshot:
        snapshot = typing.cast(RW0C1OwnerRowSnapshot, row)
        fields = {
            "development_work_spec_binding": (
                "schema_id",
                "work_spec_ref",
                "work_spec_binding_digest",
            ),
            "development_attempt_fence": (
                "schema_id",
                "attempt_fence_ref",
                "attempt_fence_digest",
            ),
            "development_effect_fence": (
                "schema_id",
                "effect_fence_ref",
                "effect_fence_digest",
            ),
            "development_author_command": (
                "schema_id",
                "command_ref",
                "command_digest",
            ),
            "development_delivery_attempt": (
                "schema_id",
                "delivery_attempt_ref",
                "delivery_attempt_digest",
            ),
            "development_model_proposal_evidence_binding": (
                "schema_id",
                "proposal_ref",
                "evidence_binding_digest",
            ),
        }
        if role not in fields or snapshot.owner_role != role:
            raise _integrity_failure() from None
        schema_name, ref_name, digest_name = fields[role]
        schema_id = (
            snapshot.wrapper_schema_id
            if role == "development_delivery_attempt"
            else snapshot.value(schema_name)
        )
        values = (schema_id, snapshot.value(ref_name), snapshot.value(digest_name))
        if any(type(value) is not str for value in values):
            raise _integrity_failure() from None
        return typing.cast(tuple[str, str, str], values)
    attributes = {
        "development_work_spec_binding": (
            "schema_id",
            "work_spec_ref",
            "work_spec_binding_digest",
        ),
        "development_attempt_fence": (
            "schema_id",
            "attempt_fence_ref",
            "attempt_fence_digest",
        ),
        "development_effect_fence": (
            "schema_id",
            "effect_fence_ref",
            "effect_fence_digest",
        ),
        "development_author_command": (
            "schema_id",
            "command_ref",
            "command_digest",
        ),
        "development_delivery_attempt": (
            "wrapper_schema_id",
            "delivery_attempt_ref",
            "delivery_attempt_digest",
        ),
        "development_model_source_invocation": (
            "schema_id",
            "source_invocation_ref",
            "source_invocation_digest",
        ),
        "development_pre_execution_planning_context": (
            "schema_id",
            "planning_context_ref",
            "planning_context_digest",
        ),
        "development_private_proposal_artifact_binding": (
            "schema_id",
            "artifact_ref",
            "artifact_binding_digest",
        ),
        "development_model_proposal": (
            "schema_id",
            "proposal_ref",
            "proposal_digest",
        ),
        "development_pre_execution_plan_projection": (
            "schema_id",
            "proposal_ref",
            "safe_projection_digest",
        ),
        "development_model_proposal_evidence_binding": (
            "schema_id",
            "proposal_ref",
            "evidence_binding_digest",
        ),
        "development_pre_execution_disposition": (
            "schema_id",
            "disposition_ref",
            "disposition_digest",
        ),
        "development_cognitive_mutation_receipt": (
            "schema_id",
            "mutation_ref",
            "receipt_digest",
        ),
    }
    if role not in attributes:
        raise _integrity_failure() from None
    try:
        schema_name, ref_name, digest_name = attributes[role]
        return (
            typing.cast(str, getattr(row, schema_name)),
            typing.cast(str, getattr(row, ref_name)),
            typing.cast(str, getattr(row, digest_name)),
        )
    except Exception:
        raise _integrity_failure() from None


_COGNITIVE_OWNER_TABLES = {
    "development_model_source_invocation": (
        "development_model_source_invocations",
        "source_invocation_ref = ?",
    ),
    "development_pre_execution_planning_context": (
        "development_pre_execution_planning_contexts",
        "planning_context_ref = ?",
    ),
    "development_private_proposal_artifact_binding": (
        "development_private_proposal_artifact_bindings",
        "artifact_ref = ?",
    ),
    "development_model_proposal": (
        "development_model_proposals",
        "proposal_ref = ?",
    ),
    "development_pre_execution_plan_projection": (
        "development_pre_execution_plan_projections",
        "proposal_ref = ?",
    ),
    "development_pre_execution_disposition": (
        "development_pre_execution_dispositions",
        "disposition_ref = ?",
    ),
    "development_cognitive_mutation_receipt": (
        "development_cognitive_mutation_receipts",
        "mutation_ref = ?",
    ),
}


def _read_command_owner_row(
    capability: object,
    locator: RW0C1OwnerRowLocatorV1,
) -> object | None:
    if locator.owner_role in _COGNITIVE_OWNER_TABLES:
        table, where = _COGNITIVE_OWNER_TABLES[locator.owner_role]
        return _read_cognitive_exact_row(
            capability,
            table=table,
            where=where,
            parameters=(locator.row_ref,),
        )
    if locator.owner_role == "development_model_proposal_evidence_binding":
        family = _read_section41_post_execution_evidence_family(
            capability, proposal_ref=locator.row_ref
        )
        matches = tuple(
            row
            for row in family.rows
            if row.value("evidence_role") == locator.subrole
            and row.value("ordinal") == locator.ordinal
        )
        if len(matches) > 1:
            raise _integrity_failure() from None
        return matches[0] if matches else None
    return _read_development_owner_row(
        capability,
        role=locator.owner_role,
        row_ref=locator.row_ref,
    )


def _resolve_command_owner_rows(
    capability: object,
    locators: tuple[RW0C1OwnerRowLocatorV1, ...],
) -> tuple[tuple[RW0C1OwnerRowLocatorV1, object], ...] | RW0C1ConflictV1:
    resolved: list[tuple[RW0C1OwnerRowLocatorV1, object]] = []
    for locator in locators:
        row = _read_command_owner_row(capability, locator)
        if row is None:
            return _conflict(RW0C1ConflictReasonV1.OWNER_ROW_MISSING)
        schema_id, row_ref, row_digest = _owner_descriptor(locator.owner_role, row)
        if row_ref != locator.row_ref or row_digest != locator.row_digest:
            raise _integrity_failure() from None
        resolved.append((locator, row))
    return tuple(resolved)


def _dependency_family_matches_locator(
    phase_ref: str,
    locator: RW0C1MemberLocatorV1,
    family: RW0C1MembershipFamily,
) -> bool:
    membership = family.membership
    return bool(
        membership.value("phase_basis_ref") == phase_ref
        and membership.value("kind_rank") == locator.kind_rank
        and membership.value("membership_ref") == locator.membership_ref
        and membership.value("membership_digest") == locator.membership_digest
        and membership.value("value_ref") == locator.value_ref
        and membership.value("value_digest") == locator.value_digest
    )


def _read_dependency_families(
    capability: object,
    command: RW0C1AdmitEvidenceCommandV1,
) -> tuple[RW0C1MembershipFamily, ...] | RW0C1ConflictV1:
    dependencies: list[RW0C1MembershipFamily] = []
    for locator in command.prerequisite_member_locators:
        family = _read_membership_family(
            capability,
            phase_basis_ref=command.phase_basis_ref,
            membership_ref=locator.membership_ref,
        )
        if family is None or not _dependency_family_matches_locator(
            command.phase_basis_ref,
            locator,
            family,
        ):
            return _conflict(RW0C1ConflictReasonV1.MISSING_PREREQUISITE_MEMBER)
        dependencies.append(family)
    return tuple(dependencies)


def _read_rank14_result_observation_families(
    capability: object,
    *,
    phase_basis_ref: str,
    evidence_value: object,
    dependencies: tuple[RW0C1MembershipFamily, ...],
) -> tuple[RW0C1MembershipFamily, ...]:
    if (
        type(evidence_value)
        is not RW0C1WireProcessResultClassificationBindingV1
        or evidence_value.result_state != "present"
    ):
        return ()
    result_families = tuple(
        family
        for family in dependencies
        if family.membership.value("kind_rank") == 13
    )
    if len(result_families) != 1:
        raise _integrity_failure() from None
    result_binding = _wrapper_value_from_membership_family(result_families[0])
    if type(result_binding) is not RW0C1WireWorkerResultBindingV1:
        raise _integrity_failure() from None
    observations: list[RW0C1MembershipFamily] = []
    for locator in result_binding.observation_memberships:
        family = _read_membership_family(
            capability,
            phase_basis_ref=phase_basis_ref,
            membership_ref=locator.membership_ref,
        )
        if family is None or not _dependency_family_matches_locator(
            phase_basis_ref,
            locator,
            family,
        ):
            raise _integrity_failure() from None
        observations.append(family)
    return tuple(observations)


def _admission_replay(
    capability: object,
    command: RW0C1AdmitEvidenceCommandV1,
    receipt: RW0C1RowValue,
) -> RW0C1AdmitEvidenceResultV1 | RW0C1ConflictV1:
    if (
        receipt.value("command_digest") != command.command_digest
        or receipt.value("mutation_family") != "admit_rw0_evidence"
    ):
        return _conflict(RW0C1ConflictReasonV1.MUTATION_REF_REUSE)
    membership_ref = receipt.value("membership_ref")
    if type(membership_ref) is not str:
        raise _integrity_failure() from None
    family = _read_membership_family(
        capability,
        phase_basis_ref=command.phase_basis_ref,
        membership_ref=membership_ref,
    )
    if family is None:
        raise _integrity_failure() from None
    _verify_evidence_family_rows(
        family,
        receipt,
        capability=capability,
        replay_command=command,
    )
    membership = family.membership
    result = RW0C1AdmitEvidenceResultV1(
        mutation_ref=command.mutation_ref,
        command_digest=command.command_digest,
        disposition="exact_replay",
        phase_basis_ref=command.phase_basis_ref,
        phase_basis_digest=command.phase_basis_digest,
        membership_ref=typing.cast(str, membership.value("membership_ref")),
        membership_digest=typing.cast(str, membership.value("membership_digest")),
        kind_rank=typing.cast(int, membership.value("kind_rank")),
        value_ref=typing.cast(str, membership.value("value_ref")),
        value_digest=typing.cast(str, membership.value("value_digest")),
        value_schema_id=typing.cast(str, membership.value("value_schema_id")),
        relation_set_digest=typing.cast(
            str, membership.value("relation_set_digest")
        ),
        admission_graph_digest=typing.cast(
            str, membership.value("admission_graph_digest")
        ),
        receipt_digest=typing.cast(str, receipt.value("receipt_digest")),
        committed_at=typing.cast(str, receipt.value("committed_at")),
    )
    if result.committed_projection_digest() != receipt.value(
        "result_projection_digest"
    ):
        raise _integrity_failure() from None
    return result


def _resolve_rw0_c1_evidence_admission_after_fencing(
    *,
    capability: object,
    command: RW0C1AdmitEvidenceCommandV1,
) -> _RW0C1EvidencePreparation | RW0C1AdmitEvidenceResultV1 | RW0C1ConflictV1:
    if type(command) is not RW0C1AdmitEvidenceCommandV1:
        raise _integrity_failure() from None
    receipt = _read_receipt(capability, command.mutation_ref)
    if receipt is not None:
        return _admission_replay(capability, command, receipt)
    phase = _read_phase_by_pair(
        capability,
        command.phase_basis_ref,
        command.phase_basis_digest,
    )
    if phase is None:
        return _conflict(RW0C1ConflictReasonV1.OWNER_ROW_MISSING)
    if not _admission_command_matches_phase_preimages(command, phase):
        return _conflict(RW0C1ConflictReasonV1.CURRENT_STATE_CONFLICT)
    basis = _phase_basis_from_row(phase)
    try:
        (
            program,
            work,
            work_spec_binding,
            effect,
            _authority,
            effect_head,
            delivery,
            stop,
            _lineage,
        ) = _read_phase_development_owner_rows(
            capability,
            _RW0C1AdmissionOwnerRead(basis, command),
        )
    except _RW0C1CurrentStateConflict:
        return _conflict(RW0C1ConflictReasonV1.CURRENT_STATE_CONFLICT)
    except _RW0C1OwnerRowMissing:
        return _conflict(RW0C1ConflictReasonV1.OWNER_ROW_MISSING)
    try:
        validate_admission_operand_grammar(command)
    except RW0C1PreflightError:
        try:
            validate_dependency_locators(
                kind_rank=command.kind_rank,
                evidence_value=command.evidence_value,
                locators=command.prerequisite_member_locators,
            )
        except RW0C1PreflightError:
            return _conflict(
                RW0C1ConflictReasonV1.MISSING_PREREQUISITE_MEMBER
            )
        return _conflict(RW0C1ConflictReasonV1.RELATION_FAILURE)
    value_ref, value_digest, value_schema_id, _scope, _mapping = evidence_identity(
        command.evidence_value,
        command.kind_rank,
    )
    registry_ref = _read_registry_by_kind_ref(
        capability,
        command.kind_rank,
        value_ref,
    )
    registry_digest = _read_registry_by_kind_digest(
        capability,
        command.kind_rank,
        value_digest,
    )
    registry_preexisting = False
    if registry_ref is not None or registry_digest is not None:
        if (
            registry_ref is None
            or registry_digest is None
            or registry_ref.as_tuple() != registry_digest.as_tuple()
            or registry_ref.value("value_schema_id") != value_schema_id
        ):
            return _conflict(RW0C1ConflictReasonV1.MEMBER_IDENTITY_COLLISION)
        typed = _read_typed_evidence(
            capability,
            kind_rank=command.kind_rank,
            value_ref=value_ref,
        )
        if typed is None:
            raise _integrity_failure() from None
        registry_preexisting = True
    if (
        _read_membership_by_ref(capability, command.preassigned_membership_ref)
        is not None
    ):
        return _conflict(RW0C1ConflictReasonV1.MEMBER_IDENTITY_COLLISION)
    if (
        _read_membership_by_phase_kind_ref(
            capability,
            command.phase_basis_ref,
            command.kind_rank,
            value_ref,
        )
        is not None
        or _read_membership_by_phase_kind_digest(
            capability,
            command.phase_basis_ref,
            command.kind_rank,
            value_digest,
        )
        is not None
    ):
        return _conflict(RW0C1ConflictReasonV1.MEMBER_ALREADY_ADMITTED)
    dependencies = _read_dependency_families(capability, command)
    if type(dependencies) is RW0C1ConflictV1:
        return dependencies
    result_observation_dependencies = _read_rank14_result_observation_families(
        capability,
        phase_basis_ref=command.phase_basis_ref,
        evidence_value=command.evidence_value,
        dependencies=typing.cast(
            tuple[RW0C1MembershipFamily, ...],
            dependencies,
        ),
    )
    try:
        (
            disposition,
            cognitive_receipt,
            _selection_result,
            selection_head,
            proposal,
            artifact,
        ) = _read_phase_selection_owner_rows(capability, basis)
    except _RW0C1OwnerRowMissing:
        return _conflict(RW0C1ConflictReasonV1.OWNER_ROW_MISSING)
    located = _resolve_command_owner_rows(capability, command.owner_row_locators)
    if type(located) is RW0C1ConflictV1:
        return located
    section41_evidence_rows: tuple[RW0C1OwnerRowSnapshot, ...] = ()
    if command.kind_rank == 15:
        section41_family: RW0C1Section41PostExecutionEvidenceFamily = (
            _read_section41_post_execution_evidence_family(
                capability,
                proposal_ref=typing.cast(
                    RW0C1Section41PostExecutionProposalFamilyMemberV1,
                    command.evidence_value,
                ).proposal_ref,
            )
        )
        section41_evidence_rows = section41_family.rows
    graph = _RW0C1AdmissionOwnerGraph(
        basis=basis,
        program=program,
        work=work,
        work_spec_binding=work_spec_binding,
        attempt_fence=effect.attempt_fence.attempt_fence,
        author_effect_fence=effect.author_effect_fence.effect_fence,
        author_command=effect.author_command.author_command,
        author_delivery=delivery.current_delivery_attempt.delivery_envelope,
        selection_disposition=disposition,
        selection_receipt=cognitive_receipt,
        selection_head=selection_head,
        selected_proposal=proposal,
        selected_artifact=artifact,
        effect_head=effect_head,
        delivery_head=delivery.delivery_head,
        global_stop=stop,
        located_owner_rows=typing.cast(
            tuple[tuple[RW0C1OwnerRowLocatorV1, object], ...],
            located,
        ),
        section41_evidence_rows=section41_evidence_rows,
    )
    return _RW0C1EvidencePreparation(
        command=command,
        phase=phase,
        basis=basis,
        dependencies=typing.cast(tuple[RW0C1MembershipFamily, ...], dependencies),
        result_observation_dependencies=result_observation_dependencies,
        owner_graph=graph,
        registry_preexisting=registry_preexisting,
    )


def _located_owner_value(
    graph: _RW0C1AdmissionOwnerGraph,
    role: str,
) -> object | None:
    matches = [
        row
        for locator, row in graph.located_owner_rows
        if locator.role == role
    ]
    if len(matches) > 1:
        raise _integrity_failure() from None
    return matches[0] if matches else None


def _owner_effect_fence(
    graph: _RW0C1AdmissionOwnerGraph,
    role: str,
    *,
    fallback: object | None = None,
) -> object | None:
    row = _located_owner_value(graph, role + "_effect_fence")
    if row is None:
        return fallback
    return _semantic_owner_value("development_effect_fence", row)


def _owner_delivery(
    graph: _RW0C1AdmissionOwnerGraph,
    role: str,
    *,
    fallback: object | None = None,
) -> object | None:
    row = _located_owner_value(graph, role + "_delivery")
    if row is None:
        return fallback
    return _semantic_owner_value("development_delivery_attempt", row)


def _transient_private_value(
    command: RW0C1AdmitEvidenceCommandV1,
    binding_kind: str,
) -> object | None:
    matches = [
        binding
        for binding in command.transient_bindings
        if binding.binding_kind == binding_kind
    ]
    if len(matches) > 1:
        raise RW0C1PreflightError("invalid_command") from None
    if not matches:
        return None
    return object.__getattribute__(matches[0], "_private_value")


def _dependency_values(
    preparation: _RW0C1EvidencePreparation,
    rank: int,
) -> tuple[object, ...]:
    values: list[object] = []
    for family in preparation.dependencies:
        if family.membership.value("kind_rank") == rank:
            if rank > 12:
                continue
            values.append(_owner_value_from_typed_evidence(family.typed_evidence))
    return tuple(values)


def _rank14_result_observation_values(
    preparation: _RW0C1EvidencePreparation,
) -> tuple[object, ...]:
    return tuple(
        _owner_value_from_typed_evidence(family.typed_evidence)
        for family in preparation.result_observation_dependencies
    )


def _relation_failure(action: typing.Callable[[], object]) -> bool:
    try:
        action()
        return False
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return True


def _validate_capability_observation_binding(
    declaration: object,
    observation: object,
) -> None:
    declaration_mapping = declaration.to_mapping()
    observation_mapping = observation.to_mapping()
    declaration_pair = (
        declaration_mapping["capability_declaration_ref"],
        declaration_mapping["capability_declaration_digest"],
    )
    named_pair = (
        observation_mapping["capability_declaration_ref"],
        observation_mapping["capability_declaration_digest"],
    )
    shared_coordinates = (
        "worker_artifact_ref",
        "worker_artifact_digest",
        "wire_profile_ref",
        "wire_profile_digest",
    )
    if declaration_pair != named_pair or any(
        declaration_mapping[name] != observation_mapping[name]
        for name in shared_coordinates
    ):
        raise ValueError("relation mismatch")


def _section41_owner_family_matches(
    value: RW0C1Section41PostExecutionProposalFamilyMemberV1,
    located: tuple[tuple[RW0C1OwnerRowLocatorV1, object], ...],
    complete_evidence_rows: tuple[RW0C1OwnerRowSnapshot, ...],
) -> bool:
    try:
        locators = tuple(item[0] for item in located)
        if section41_owner_family_graph_digest(locators) != (
            value.owner_family_graph_digest
        ):
            return False
        by_role = {locator.role: row.to_mapping() for locator, row in located}
        source = by_role["source_invocation"]
        artifact = by_role["artifact_binding"]
        proposal = by_role["model_proposal"]
        if any(
            mapping.get("proposal_phase") != "post_execution_semantic_review"
            for mapping in (source, artifact, proposal)
        ):
            return False
        post_context_schema = (
            "governed-execution.nwp-post-execution-semantic-review-context.v1"
        )
        post_artifact_schema = (
            "governed-execution.nwp-post-execution-semantic-review-artifact.v1"
        )
        post_projection_schema = (
            "governed-execution.nwp-post-execution-semantic-review-safe-projection.v1"
        )
        comparisons = (
            (source, "source_invocation_ref", value.source_invocation_ref),
            (source, "source_invocation_digest", value.source_invocation_digest),
            (source, "model_contract_ref", value.model_contract_ref),
            (source, "model_contract_digest", value.model_contract_digest),
            (source, "model_configuration_ref", value.model_configuration_ref),
            (source, "model_configuration_digest", value.model_configuration_digest),
            (source, "context_schema_id", value.context_schema_id),
            (source, "context_ref", value.context_ref),
            (source, "context_digest", value.context_digest),
            (source, "artifact_schema_id", post_artifact_schema),
            (source, "artifact_ref", value.artifact_ref),
            (source, "artifact_digest", value.artifact_digest),
            (artifact, "artifact_ref", value.artifact_ref),
            (artifact, "artifact_schema_id", post_artifact_schema),
            (artifact, "artifact_digest", value.artifact_digest),
            (artifact, "artifact_binding_digest", value.artifact_binding_digest),
            (artifact, "safe_projection_schema_id", value.safe_projection_schema_id),
            (artifact, "safe_projection_digest", value.safe_projection_digest),
            (proposal, "proposal_ref", value.proposal_ref),
            (proposal, "proposal_digest", value.proposal_digest),
            (proposal, "source_invocation_ref", value.source_invocation_ref),
            (proposal, "source_invocation_digest", value.source_invocation_digest),
            (proposal, "model_contract_ref", value.model_contract_ref),
            (proposal, "model_contract_digest", value.model_contract_digest),
            (proposal, "model_configuration_ref", value.model_configuration_ref),
            (proposal, "model_configuration_digest", value.model_configuration_digest),
            (proposal, "context_schema_id", value.context_schema_id),
            (proposal, "context_ref", value.context_ref),
            (proposal, "context_digest", value.context_digest),
            (proposal, "artifact_schema_id", post_artifact_schema),
            (proposal, "artifact_ref", value.artifact_ref),
            (proposal, "artifact_digest", value.artifact_digest),
            (proposal, "safe_projection_schema_id", value.safe_projection_schema_id),
            (proposal, "safe_projection_digest", value.safe_projection_digest),
            (proposal, "evidence_set_ref", value.evidence_set_ref),
            (proposal, "evidence_set_digest", value.evidence_set_digest),
            (proposal, "recommendation", value.recommendation),
            (proposal, "reason_code", value.reason_code),
            (proposal, "proposal_created_at", value.proposal_created_at),
        )
        if (
            value.context_schema_id != post_context_schema
            or value.safe_projection_schema_id != post_projection_schema
            or any(
                mapping.get(name) != expected
                for mapping, name, expected in comparisons
            )
        ):
            return False
        evidence = located[3:]
        if (
            len(evidence) != value.evidence_binding_count
            or len(complete_evidence_rows) != value.evidence_binding_count
        ):
            return False
        expected_evidence_roles = (
            ()
            if value.evidence_binding_count == 0
            else (
                "candidate_capsule",
                "worker_result",
                "validation_result",
                "independent_review",
                "standing_policy",
                "risk_lane",
                "authority_currentness_attestation",
                "global_stop",
                "effect_ceiling",
            )
        )
        expected_evidence_specs = (
            ()
            if value.evidence_binding_count == 0
            else _POST_EXECUTION_EVIDENCE
        )
        if tuple(item[0] for item in expected_evidence_specs) != (
            expected_evidence_roles
        ):
            return False
        for (locator, located_row), complete_row, (role, rank, required) in zip(
            evidence,
            complete_evidence_rows,
            expected_evidence_specs,
            strict=True,
        ):
            mapping = complete_row.to_mapping()
            if (
                locator.role != role
                or located_row.to_mapping() != mapping
                or mapping.get("proposal_ref") != value.proposal_ref
                or mapping.get("proposal_phase")
                != "post_execution_semantic_review"
                or mapping.get("evidence_set_ref") != value.evidence_set_ref
                or mapping.get("evidence_role") != role
                or mapping.get("role_rank") != rank
                or mapping.get("ordinal") != 0
                or mapping.get("required_for_selection") != required
            ):
                return False
        evidence_set_identity = {
            "evidence_set_ref": value.evidence_set_ref,
            "proposal_ref": value.proposal_ref,
            "proposal_phase": "post_execution_semantic_review",
            "entries": tuple(
                {
                    "evidence_role": row.value("evidence_role"),
                    "role_rank": row.value("role_rank"),
                    "ordinal": row.value("ordinal"),
                    "evidence_ref": row.value("evidence_ref"),
                    "evidence_digest": row.value("evidence_digest"),
                    "evidence_binding_digest": row.value(
                        "evidence_binding_digest"
                    ),
                }
                for row in complete_evidence_rows
            ),
        }
        return (
            _canonical_owner_digest(
                _SECTION41_EVIDENCE_SET_DOMAIN,
                evidence_set_identity,
            )
            == value.evidence_set_digest
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return False


def _wire_wrapper_matches_phase(
    value: (
        RW0C1WireWorkerResultBindingV1
        | RW0C1WireProcessResultClassificationBindingV1
    ),
    basis: object,
) -> bool:
    try:
        lineage = basis.c2b3d_lineage
        return (
            value.phase_basis_ref == basis.basis_ref
            and value.phase_basis_digest == basis.basis_digest
            and value.program_ref == lineage.program_ref
            and value.semantic_attempt_ref == lineage.semantic_attempt_ref
            and value.candidate_ref == lineage.candidate_ref
            and value.effect_intent_ref == lineage.effect_intent_ref
            and value.author_command_ref == lineage.author_command_ref
            and value.attempt_fence_ref == lineage.attempt_fence_ref
            and value.effect_fence_ref == lineage.effect_fence_ref
            and value.delivery_attempt_ref == lineage.delivery_attempt_ref
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return False


def _validate_rank_relation(
    preparation: _RW0C1EvidencePreparation,
    *,
    operation_timestamp: str,
) -> bool:
    command = preparation.command
    rank = command.kind_rank
    graph = typing.cast(_RW0C1AdmissionOwnerGraph, preparation.owner_graph)
    value = command.evidence_value
    basis = graph.basis
    current_effect_fence = _owner_effect_fence(
        graph,
        "current",
        fallback=graph.author_effect_fence,
    )
    capsule = _transient_private_value(command, "candidate_capsule_manifest")
    if rank == 1:
        cancellation_target = _owner_effect_fence(graph, "cancellation_target")
        return _relation_failure(
            lambda: _b1.validate_authority_observation(
                basis=basis,
                observation=value,
                attempt_fence=graph.attempt_fence,
                author_effect_fence=graph.author_effect_fence,
                current_effect_fence=current_effect_fence,
                author_command=graph.author_command,
                capsule_manifest=capsule,
                cancellation_target=cancellation_target,
                now_utc=operation_timestamp,
            )
        )
    if rank == 2:
        authority = _dependency_values(preparation, 1)
        if len(authority) != 1:
            return True
        return _relation_failure(
            lambda: _b1.validate_subordinate_narrowing(
                basis=basis,
                observation=authority[0],
                proposal=value,
                attempt_fence=graph.attempt_fence,
                current_effect_fence=current_effect_fence,
                now_utc=operation_timestamp,
            )
        )
    if rank == 3:
        work_spec = _transient_private_value(command, "work_spec")
        subject = graph.selected_artifact if work_spec is None else work_spec
        return _relation_failure(
            lambda: _b1.validate_custody_binding(
                basis=basis,
                availability=value,
                subject=subject,
                now_utc=operation_timestamp,
            )
        )
    if rank == 4:
        authority = _dependency_values(preparation, 1)
        proposals = _dependency_values(preparation, 2)
        custody = _dependency_values(preparation, 3)
        earlier = _dependency_values(preparation, 4)
        if len(authority) != 1 or len(proposals) != 1 or len(custody) != 1:
            return True
        events = tuple(
            sorted((*earlier, value), key=lambda member: member.sequence_number)
        )
        return _relation_failure(
            lambda: _b1.validate_retrieval_event_sequence(
                basis=basis,
                availability=custody[0],
                observation=authority[0],
                proposal=proposals[0],
                events=events,
                attempt_fence=graph.attempt_fence,
                current_effect_fence=current_effect_fence,
                now_utc=operation_timestamp,
            )
        )
    if rank in {5, 7}:
        return False
    if rank == 6:
        authority = _dependency_values(preparation, 1)
        readiness = _dependency_values(preparation, 5)
        if len(authority) != 1 or len(readiness) != 1:
            return True
        return _relation_failure(
            lambda: _b1.validate_host_qualification(
                basis=basis,
                authority=authority[0],
                readiness=readiness[0],
                qualification=value,
                current_effect_fence=current_effect_fence,
                now_utc=value.evaluated_at,
            )
        ) or value.evaluated_at > operation_timestamp
    if rank == 8:
        declaration = _dependency_values(preparation, 7)
        return len(declaration) != 1 or _relation_failure(
            lambda: _validate_capability_observation_binding(
                declaration[0],
                value,
            )
        )
    if rank == 9:
        authority = _dependency_values(preparation, 1)
        readiness = _dependency_values(preparation, 5)
        host = _dependency_values(preparation, 6)
        declaration = _dependency_values(preparation, 7)
        observation = _dependency_values(preparation, 8)
        if any(
            len(items) != 1
            for items in (authority, readiness, host, declaration, observation)
        ):
            return True
        return _relation_failure(
            lambda: _capability_values.validate_worker_mechanism_capability_qualification(
                declaration=declaration[0],
                observation=observation[0],
                qualification=value,
                phase_basis=basis,
                authority_observation=authority[0],
                readiness_observation=readiness[0],
                host_qualification=host[0],
                current_effect_fence=current_effect_fence,
                now_utc=value.evaluated_at,
            )
        ) or value.evaluated_at != host[0].evaluated_at or value.evaluated_at > operation_timestamp
    target_effect = _owner_effect_fence(
        graph,
        "target",
        fallback=graph.author_effect_fence,
    )
    target_delivery = _owner_delivery(
        graph,
        "target",
        fallback=graph.author_delivery,
    )
    cancellation_effect = _owner_effect_fence(graph, "cancellation")
    cancellation_delivery = _owner_delivery(graph, "cancellation")
    if rank == 10:
        if cancellation_effect is None or cancellation_delivery is None:
            return True
        return _relation_failure(
            lambda: _wire.validate_wire_exact_current_cancellation_request_relation(
                request=value,
                author_command=graph.author_command,
                attempt_fence=graph.attempt_fence,
                author_effect_fence=graph.author_effect_fence,
                target_effect_fence=target_effect,
                target_delivery=target_delivery,
                cancellation_effect_fence=cancellation_effect,
                cancellation_delivery=cancellation_delivery,
                **({} if capsule is None else {"target_capsule_manifest": capsule}),
            )
        )
    if rank == 11:
        return _relation_failure(
            lambda: _wire.validate_wire_exact_current_process_observation_relation(
                observation=value,
                author_command=graph.author_command,
                attempt_fence=graph.attempt_fence,
                author_effect_fence=graph.author_effect_fence,
                target_effect_fence=target_effect,
                target_delivery=target_delivery,
                **({} if capsule is None else {"target_capsule_manifest": capsule}),
            )
        )
    if rank == 12:
        effect = target_effect
        delivery = target_delivery
        cancellation_target: object | None = None
        if value.observation_kind in {
            "cancellation_acknowledged",
            "cancellation_rejected",
        }:
            effect = cancellation_effect
            delivery = cancellation_delivery
            cancellation_target = target_effect
        if effect is None or delivery is None:
            return True
        arguments: dict[str, object] = {
            "observation": value,
            "delivery": delivery,
            "author_command": graph.author_command,
            "attempt_fence": graph.attempt_fence,
            "author_effect_fence": graph.author_effect_fence,
            "effect_fence": effect,
        }
        if capsule is not None:
            arguments["capsule_manifest"] = capsule
        before = _transient_private_value(command, "before_blob_set")
        after = _transient_private_value(command, "after_blob_set")
        if before is not None:
            arguments["before_blobs"] = before
        if after is not None:
            arguments["after_blobs"] = after
        if cancellation_target is not None:
            arguments["cancellation_target"] = cancellation_target
        failed = _relation_failure(
            lambda: _worker_values.validate_observation_relation(**arguments)
        )
        if failed or cancellation_target is None:
            return failed
        requests = _dependency_values(preparation, 10)
        if len(requests) != 1 or cancellation_effect is None or cancellation_delivery is None:
            return True
        return _relation_failure(
            lambda: _wire.validate_wire_exact_current_cancellation_response_relation(
                response=value,
                request=requests[0],
                author_command=graph.author_command,
                attempt_fence=graph.attempt_fence,
                author_effect_fence=graph.author_effect_fence,
                target_effect_fence=target_effect,
                target_delivery=target_delivery,
                cancellation_effect_fence=cancellation_effect,
                cancellation_delivery=cancellation_delivery,
                **({} if capsule is None else {"target_capsule_manifest": capsule}),
            )
        )
    if rank == 13:
        if not _wire_wrapper_matches_phase(value, basis):
            return True
        observations = typing.cast(
            tuple[object, ...],
            _dependency_values(preparation, 12),
        )
        if len(observations) not in {2, 3}:
            return True
        return _relation_failure(
            lambda: _wire.validate_wire_result_relation(
                result=_wire.RW0WireWorkerResultV1._create(observations),
                command=graph.author_command,
                delivery=graph.author_delivery,
                attempt_fence=graph.attempt_fence,
                author_effect_fence=graph.author_effect_fence,
            )
        )
    if rank == 14:
        if not _wire_wrapper_matches_phase(value, basis):
            return True
        adapter_observations = typing.cast(
            tuple[object, ...],
            _dependency_values(preparation, 12),
        )
        requests = _dependency_values(preparation, 10)
        processes = typing.cast(tuple[object, ...], _dependency_values(preparation, 11))
        result: object | None = None
        failure: object | None = None
        if value.result_state == "present":
            result_observations = _rank14_result_observation_values(preparation)
            if len(result_observations) not in {2, 3}:
                return True
            result = _wire.RW0WireWorkerResultV1._create(result_observations)
        elif value.result_state == "finite_failure":
            failure = _transient_private_value(command, "wire_protocol_error")
            if failure is None:
                return True
        classified = _wire.classify_wire_process_result(
            command=graph.author_command,
            delivery=graph.author_delivery,
            attempt_fence=graph.attempt_fence,
            author_effect_fence=graph.author_effect_fence,
            result=result,
            result_failure=failure,
            adapter_observations=adapter_observations,
            request=requests[0] if len(requests) == 1 else None,
            process_observations=processes,
            cancellation_effect_fence=cancellation_effect,
            cancellation_delivery=cancellation_delivery,
        )
        mapping = classified.to_mapping()
        return (
            mapping.get("classification") != value.classification
            or mapping.get("reason") != value.reason
        )
    if rank == 15:
        wrapped = typing.cast(
            RW0C1Section41PostExecutionProposalFamilyMemberV1,
            value,
        )
        if (
            wrapped.phase_basis_ref != basis.basis_ref
            or wrapped.phase_basis_digest != basis.basis_digest
        ):
            return True
        return not _section41_owner_family_matches(
            wrapped,
            graph.located_owner_rows,
            graph.section41_evidence_rows,
        )
    return True


def _member_operand(
    ordinal: int,
    locator: RW0C1MemberLocatorV1,
    family: RW0C1MembershipFamily,
) -> RW0C1OperandIdentity:
    membership = family.membership
    return RW0C1OperandIdentity(
        ordinal,
        locator.role,
        "c1_evidence",
        locator.membership_ref,
        locator.membership_digest,
        locator.kind_rank,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        typing.cast(str, membership.value("value_schema_id")),
        locator.value_ref,
        locator.value_digest,
        typing.cast(str, membership.value("scope_binding_digest")),
    )


def _located_owner_operand(
    ordinal: int,
    locator: RW0C1OwnerRowLocatorV1,
    row: object,
) -> RW0C1OperandIdentity:
    schema_id, row_ref, row_digest = _owner_descriptor(locator.owner_role, row)
    return _owner_operand(
        ordinal=ordinal,
        role=locator.role,
        owner_role=locator.owner_role,
        schema_id=schema_id,
        row_ref=row_ref,
        row_digest=row_digest,
        revision=locator.revision,
        subrole=locator.subrole,
        owner_ordinal=locator.ordinal,
    )


def _admission_snapshots_from_phase(
    phase: RW0C1RowValue,
) -> tuple[RW0C1AdmissionSnapshotBindingV1, ...]:
    phase_ref = typing.cast(str, phase.value("phase_basis_ref"))
    phase_digest = typing.cast(str, phase.value("phase_basis_digest"))
    selection = RW0C1AdmissionSnapshotBindingV1(
        "selection_head",
        "selection_head_snapshot",
        phase_ref,
        phase_digest,
        (
            (
                "owner_schema_id",
                "governed-execution.nwp-pre-execution-selection-head.v1",
            ),
            *((name, phase.value(name)) for name in _K8_FIELDS),
            ("current_proposal_ref", phase.value("selected_proposal_ref")),
            ("current_disposition_ref", phase.value("disposition_ref")),
            ("current_disposition", phase.value("disposition")),
            ("head_revision", phase.value("selection_head_revision")),
            ("updated_at", phase.value("selection_head_updated_at")),
            ("head_digest", phase.value("selection_head_digest")),
        ),
    )
    effect = RW0C1AdmissionSnapshotBindingV1(
        "effect_head",
        "effect_head_snapshot",
        phase_ref,
        phase_digest,
        (
            (
                "owner_schema_id",
                "governed-execution.nwp-development-effect-head.v1",
            ),
            ("program_ref", phase.value("program_ref")),
            ("effect_intent_ref", phase.value("effect_intent_ref")),
            (
                "current_effect_fence_ref",
                phase.value("current_effect_head_fence_ref"),
            ),
            ("head_revision", phase.value("current_effect_head_revision")),
            ("effect_state", phase.value("current_effect_head_state")),
            (
                "cancellation_effect_intent_ref",
                phase.value("current_effect_head_cancellation_effect_intent_ref"),
            ),
            ("updated_at", phase.value("current_effect_head_updated_at")),
            ("head_digest", phase.value("current_effect_head_digest")),
        ),
    )
    delivery = RW0C1AdmissionSnapshotBindingV1(
        "delivery_head",
        "delivery_head_snapshot",
        phase_ref,
        phase_digest,
        (
            (
                "owner_schema_id",
                "governed-execution.nwp-development-delivery-head.v1",
            ),
            ("program_ref", phase.value("program_ref")),
            ("effect_intent_ref", phase.value("effect_intent_ref")),
            (
                "current_delivery_attempt_ref",
                phase.value("current_delivery_head_attempt_ref"),
            ),
            ("head_revision", phase.value("current_delivery_head_revision")),
            ("delivery_state", phase.value("current_delivery_head_state")),
            ("updated_at", phase.value("current_delivery_head_updated_at")),
            ("head_digest", phase.value("current_delivery_head_digest")),
        ),
    )
    stop = RW0C1AdmissionSnapshotBindingV1(
        "global_stop_current",
        "global_stop_snapshot",
        phase_ref,
        phase_digest,
        (
            ("owner_schema_id", GLOBAL_STOP_SCHEMA_ID),
            ("stop_ref", phase.value("global_stop_ref")),
            ("version", phase.value("global_stop_version")),
            ("state", phase.value("global_stop_state")),
        ),
    )
    return selection, effect, delivery, stop


def _admission_operands(
    preparation: _RW0C1EvidencePreparation,
) -> tuple[RW0C1OperandIdentity, ...]:
    command = preparation.command
    by_membership = {
        family.membership.value("membership_ref"): family
        for family in preparation.dependencies
    }
    operands: list[RW0C1OperandIdentity] = []
    for locator in command.prerequisite_member_locators:
        family = by_membership.get(locator.membership_ref)
        if family is None:
            raise RW0C1PreflightError("invalid_value") from None
        operands.append(_member_operand(len(operands), locator, family))
    graph = typing.cast(_RW0C1AdmissionOwnerGraph, preparation.owner_graph)
    by_locator = {
        id(locator): row for locator, row in graph.located_owner_rows
    }
    for locator in command.owner_row_locators:
        row = by_locator.get(id(locator))
        if row is None:
            raise RW0C1PreflightError("invalid_value") from None
        operands.append(_located_owner_operand(len(operands), locator, row))
    for binding in command.transient_bindings:
        operands.append(_transient_operand(len(operands), binding))
    if len(operands) > 14 or len({item.operand_role for item in operands}) != len(operands):
        raise RW0C1PreflightError("invalid_command") from None
    return tuple(operands)


def _scope_binding_digest(
    preparation: _RW0C1EvidencePreparation,
    value_schema_id: str,
) -> str:
    rank = preparation.command.kind_rank
    if rank in {5, 7, 8}:
        return global_scope_binding_digest(rank, value_schema_id)
    if rank in {13, 14}:
        return typing.cast(str, preparation.phase.value("k8_digest"))
    if rank == 15:
        return typing.cast(
            RW0C1Section41PostExecutionProposalFamilyMemberV1,
            preparation.command.evidence_value,
        ).owner_family_graph_digest
    return preparation.command.phase_basis_digest


def _locator_set_digest(
    schema_id: str,
    locators: tuple[RW0C1MemberLocatorV1, ...],
) -> str:
    return admission_graph_digest(
        {
            "schema_id": schema_id,
            "members": [locator.to_mapping() for locator in locators],
        }
    )


def _typed_payload_and_children(
    preparation: _RW0C1EvidencePreparation,
    *,
    value_ref: str,
    value_digest: str,
    value_schema_id: str,
    primary_relation_ref: str | None,
    primary_relation_digest: str | None,
) -> tuple[RW0C1RowValue, tuple[RW0C1RowValue, ...]]:
    command = preparation.command
    rank = command.kind_rank
    table = typed_payload_table(rank)
    columns = ROW_SPEC_BY_TABLE[table].columns
    base: dict[str, object] = {
        "schema_id": row_schema_id(table),
        "kind_rank": rank,
        "value_ref": value_ref,
        "value_digest": value_digest,
        "value_schema_id": value_schema_id,
    }
    children: list[RW0C1RowValue] = []
    if rank <= 12:
        normalized = normalized_owner_mapping(command.evidence_value, rank)
        spec = RW0_C1_KIND_SPECS[rank - 1]
        for name in ("schema_id", spec.ref_field, spec.digest_field):
            normalized.pop(name, None)
        base.update(normalized)
        if rank == 1:
            for ordinal, effect_class in enumerate(
                command.evidence_value.allowed_effect_classes
            ):
                children.append(
                    build_row(
                        "rw0_authority_observation_effect_classes",
                        {
                            "schema_id": row_schema_id(
                                "rw0_authority_observation_effect_classes"
                            ),
                            "kind_rank": 1,
                            "value_ref": value_ref,
                            "value_digest": value_digest,
                            "ordinal": ordinal,
                            "effect_class": effect_class,
                        },
                    )
                )
        elif rank == 12:
            for ordinal, evidence_ref in enumerate(
                command.evidence_value.evidence_refs
            ):
                children.append(
                    build_row(
                        "rw0_c2a_worker_observation_evidence_refs",
                        {
                            "schema_id": row_schema_id(
                                "rw0_c2a_worker_observation_evidence_refs"
                            ),
                            "kind_rank": 12,
                            "value_ref": value_ref,
                            "value_digest": value_digest,
                            "ordinal": ordinal,
                            "evidence_ref": evidence_ref,
                        },
                    )
                )
    elif rank == 13:
        value = typing.cast(RW0C1WireWorkerResultBindingV1, command.evidence_value)
        base.update(
            {
                name: member
                for name, member in value.identity_mapping().items()
                if name not in {"schema_id", "value_ref", "observation_memberships"}
            }
        )
        base.update(
            observation_count=len(value.observation_memberships),
            observation_membership_set_digest=_locator_set_digest(
                "governed-execution.nwp-rw0-c1-worker-result-observation-memberships.v1",
                value.observation_memberships,
            ),
            relation_ref=primary_relation_ref,
            relation_digest=primary_relation_digest,
        )
    elif rank == 14:
        value = typing.cast(
            RW0C1WireProcessResultClassificationBindingV1,
            command.evidence_value,
        )
        identity = value.identity_mapping()
        for name in (
            "schema_id",
            "value_ref",
            "result_membership",
            "adapter_observations",
            "request_membership",
            "process_observations",
        ):
            identity.pop(name, None)
        base.update(identity)
        base.update(
            result_membership_ref=(
                None
                if value.result_membership is None
                else value.result_membership.membership_ref
            ),
            result_membership_digest=(
                None
                if value.result_membership is None
                else value.result_membership.membership_digest
            ),
            adapter_observation_count=len(value.adapter_observations),
            adapter_observation_membership_set_digest=_locator_set_digest(
                "governed-execution.nwp-rw0-c1-adapter-observation-memberships.v1",
                value.adapter_observations,
            ),
            request_membership_ref=(
                None
                if value.request_membership is None
                else value.request_membership.membership_ref
            ),
            request_membership_digest=(
                None
                if value.request_membership is None
                else value.request_membership.membership_digest
            ),
            process_observation_count=len(value.process_observations),
            process_observation_membership_set_digest=_locator_set_digest(
                "governed-execution.nwp-rw0-c1-process-observation-memberships.v1",
                value.process_observations,
            ),
            cancellation_effect_fence_ref=None,
            cancellation_effect_fence_digest=None,
            cancellation_delivery_attempt_ref=None,
            cancellation_delivery_envelope_digest=None,
            relation_ref=primary_relation_ref,
            relation_digest=primary_relation_digest,
        )
        graph = typing.cast(_RW0C1AdmissionOwnerGraph, preparation.owner_graph)
        cancellation_effect = _owner_effect_fence(graph, "cancellation")
        cancellation_delivery = _owner_delivery(graph, "cancellation")
        if cancellation_effect is not None:
            base["cancellation_effect_fence_ref"] = cancellation_effect.effect_fence_ref
            base["cancellation_effect_fence_digest"] = cancellation_effect.effect_fence_digest
        if cancellation_delivery is not None:
            base["cancellation_delivery_attempt_ref"] = cancellation_delivery.delivery_attempt_ref
            base["cancellation_delivery_envelope_digest"] = cancellation_delivery.delivery_envelope_digest
    else:
        value = typing.cast(
            RW0C1Section41PostExecutionProposalFamilyMemberV1,
            command.evidence_value,
        )
        base.update(
            {
                name: member
                for name, member in value.identity_mapping().items()
                if name not in {"schema_id", "value_ref"}
            }
        )
        base.update(
            relation_ref=primary_relation_ref,
            relation_digest=primary_relation_digest,
        )
    for column in columns:
        if column.endswith("_row_digest"):
            continue
        base.setdefault(column, None)
    payload = build_row(
        table,
        {column: base[column] for column in columns if not column.endswith("_row_digest")},
    )
    return payload, tuple(children)


def _complete_rw0_c1_evidence_admission_preparation(
    preparation: _RW0C1EvidencePreparation,
    *,
    operation_timestamp: str,
) -> RW0C1WritePlan | RW0C1ConflictV1:
    if type(preparation) is not _RW0C1EvidencePreparation:
        raise _integrity_failure() from None
    command = preparation.command
    try:
        if _validate_rank_relation(
            preparation,
            operation_timestamp=operation_timestamp,
        ):
            return _conflict(RW0C1ConflictReasonV1.RELATION_FAILURE)
        value_ref, value_digest, value_schema_id, scope_class, _mapping = (
            evidence_identity(command.evidence_value, command.kind_rank)
        )
        operands = _admission_operands(preparation)
        cancellation_response = bool(
            command.kind_rank == 12
            and command.evidence_value.observation_kind
            in {"cancellation_acknowledged", "cancellation_rejected"}
        )
        rank14_state = (
            command.evidence_value.result_state if command.kind_rank == 14 else None
        )
        specifications = relation_specifications(
            kind_rank=command.kind_rank,
            cancellation_response=cancellation_response,
            transient_binding_kinds=tuple(
                binding.binding_kind for binding in command.transient_bindings
            ),
            rank14_result_state=rank14_state,
        )
        host = _dependency_values(preparation, 6)
        relation_identities: list[
            tuple[RW0C1RelationSpecification, str, str, str, str | None]
        ] = []
        for specification in specifications:
            relation_ref = relation_reference(
                phase_basis_ref=command.phase_basis_ref,
                phase_basis_digest=command.phase_basis_digest,
                subject_type="evidence_membership",
                subject_membership_ref=command.preassigned_membership_ref,
                relation_rank=specification.relation_rank,
            )
            evaluated_at = relation_evaluation_time(
                relation_schema_id=specification.relation_schema_id,
                evidence_value=command.evidence_value,
                operation_timestamp=operation_timestamp,
                host_qualification=host[0] if len(host) == 1 else None,
            )
            relation_semantic_digest, operand_digest = relation_digest(
                phase_basis_ref=command.phase_basis_ref,
                phase_basis_digest=command.phase_basis_digest,
                relation_ref=relation_ref,
                subject_type="evidence_membership",
                subject_membership_ref=command.preassigned_membership_ref,
                subject_kind_rank=command.kind_rank,
                subject_value_ref=value_ref,
                subject_value_digest=value_digest,
                subject_value_schema_id=value_schema_id,
                specification=specification,
                evaluated_at=evaluated_at,
                operands=operands,
            )
            relation_identities.append(
                (
                    specification,
                    relation_ref,
                    relation_semantic_digest,
                    operand_digest,
                    evaluated_at,
                )
            )
        relation_set_value = relation_set_digest(
            phase_basis_ref=command.phase_basis_ref,
            subject_type="evidence_membership",
            subject_ref=command.preassigned_membership_ref,
            relations=tuple(
                (spec.relation_rank, ref, digest)
                for spec, ref, digest, _operand_digest, _evaluated_at
                in relation_identities
            ),
        )
        scope_binding = _scope_binding_digest(preparation, value_schema_id)
        graph_identity = {
            "schema_id": "governed-execution.nwp-rw0-c1-evidence-admission-graph.v1",
            "phase_basis_ref": command.phase_basis_ref,
            "phase_basis_digest": command.phase_basis_digest,
            "membership_ref": command.preassigned_membership_ref,
            "kind_rank": command.kind_rank,
            "value_ref": value_ref,
            "value_digest": value_digest,
            "value_schema_id": value_schema_id,
            "scope_binding_digest": scope_binding,
            "relation_set_digest": relation_set_value,
            "relations": [
                {
                    "relation_rank": specification.relation_rank,
                    "relation_ref": relation_ref,
                    "relation_digest": relation_semantic_digest,
                    "operand_set_digest": operand_digest,
                    "evaluated_at": evaluated_at,
                }
                for (
                    specification,
                    relation_ref,
                    relation_semantic_digest,
                    operand_digest,
                    evaluated_at,
                ) in relation_identities
            ],
            "admitted_by_mutation_ref": command.mutation_ref,
            "admitted_at": operation_timestamp,
        }
        graph_digest = admission_graph_digest(graph_identity)
        membership_identity = {
            "schema_id": membership_schema_id(),
            "membership_ref": command.preassigned_membership_ref,
            "phase_basis_ref": command.phase_basis_ref,
            "phase_basis_digest": command.phase_basis_digest,
            "kind_rank": command.kind_rank,
            "value_ref": value_ref,
            "value_digest": value_digest,
            "value_schema_id": value_schema_id,
            "scope_binding_digest": scope_binding,
            "relation_set_digest": relation_set_value,
            "admitted_by_mutation_ref": command.mutation_ref,
            "admitted_at": operation_timestamp,
            "admission_graph_digest": graph_digest,
        }
        membership_digest_value = membership_digest(membership_identity)
        membership = build_row(
            "rw0_evidence_memberships",
            membership_identity,
        )
        if membership.value("membership_digest") != membership_digest_value:
            raise _integrity_failure() from None
        relation_rows: list[RW0C1RowValue] = []
        for (
            specification,
            relation_ref,
            relation_semantic_digest,
            operand_digest,
            evaluated_at,
        ) in relation_identities:
            binding, relation_operands = _relation_and_operand_rows(
                phase_basis_ref=command.phase_basis_ref,
                phase_basis_digest=command.phase_basis_digest,
                relation_ref=relation_ref,
                relation_semantic_digest=relation_semantic_digest,
                subject_type="evidence_membership",
                membership_ref=command.preassigned_membership_ref,
                membership_digest_value=membership_digest_value,
                kind_rank=command.kind_rank,
                value_ref=value_ref,
                value_digest=value_digest,
                value_schema_id=value_schema_id,
                specification=specification,
                evaluated_at=evaluated_at,
                operand_set_value=operand_digest,
                operands=operands,
            )
            relation_rows.extend((binding, *relation_operands))
        primary_ref = relation_identities[0][1] if relation_identities else None
        primary_digest = relation_identities[0][2] if relation_identities else None
        payload, children = _typed_payload_and_children(
            preparation,
            value_ref=value_ref,
            value_digest=value_digest,
            value_schema_id=value_schema_id,
            primary_relation_ref=primary_ref,
            primary_relation_digest=primary_digest,
        )
        registry = build_row(
            "rw0_evidence_values",
            {
                "schema_id": _REGISTRY_ROW_SCHEMA,
                "kind_rank": command.kind_rank,
                "value_ref": value_ref,
                "value_digest": value_digest,
                "value_schema_id": value_schema_id,
                "scope_class": scope_class,
            },
        )
        provisional = RW0C1AdmitEvidenceResultV1(
            mutation_ref=command.mutation_ref,
            command_digest=command.command_digest,
            disposition="fresh_committed",
            phase_basis_ref=command.phase_basis_ref,
            phase_basis_digest=command.phase_basis_digest,
            membership_ref=command.preassigned_membership_ref,
            membership_digest=membership_digest_value,
            kind_rank=command.kind_rank,
            value_ref=value_ref,
            value_digest=value_digest,
            value_schema_id=value_schema_id,
            relation_set_digest=relation_set_value,
            admission_graph_digest=graph_digest,
            receipt_digest="0" * 64,
            committed_at=operation_timestamp,
        )
        receipt_value = RW0C1MutationReceiptV1(
            mutation_ref=command.mutation_ref,
            mutation_family="admit_rw0_evidence",
            command_schema_id=command.schema_id,
            command_digest=command.command_digest,
            phase_basis_ref=command.phase_basis_ref,
            phase_basis_digest=command.phase_basis_digest,
            membership_ref=command.preassigned_membership_ref,
            membership_digest=membership_digest_value,
            kind_rank=command.kind_rank,
            value_ref=value_ref,
            value_digest=value_digest,
            value_schema_id=value_schema_id,
            result_class="rw0_evidence_admitted",
            result_projection_digest=provisional.committed_projection_digest(),
            admission_graph_digest=graph_digest,
            outcome="committed",
            committed_at=operation_timestamp,
        )
        receipt = build_row(
            "rw0_c1_mutation_receipts",
            receipt_value.identity_mapping(),
        )
        result = RW0C1AdmitEvidenceResultV1(
            mutation_ref=command.mutation_ref,
            command_digest=command.command_digest,
            disposition="fresh_committed",
            phase_basis_ref=command.phase_basis_ref,
            phase_basis_digest=command.phase_basis_digest,
            membership_ref=command.preassigned_membership_ref,
            membership_digest=membership_digest_value,
            kind_rank=command.kind_rank,
            value_ref=value_ref,
            value_digest=value_digest,
            value_schema_id=value_schema_id,
            relation_set_digest=relation_set_value,
            admission_graph_digest=graph_digest,
            receipt_digest=receipt_value.receipt_digest,
            committed_at=operation_timestamp,
        )
        prefix: tuple[RW0C1RowValue, ...] = ()
        if not preparation.registry_preexisting:
            prefix = (registry, payload, *children)
        return RW0C1WritePlan(
            "admit_rw0_evidence",
            (*prefix, membership, *relation_rows, receipt),
            operation_timestamp,
            result,
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except SQLiteMutationStoreError:
        raise
    except RW0C1PreflightError:
        return _conflict(RW0C1ConflictReasonV1.RELATION_FAILURE)
    except Exception:
        return _conflict(RW0C1ConflictReasonV1.RELATION_FAILURE)


def _operand_identity_from_row(row: RW0C1RowValue) -> RW0C1OperandIdentity:
    try:
        return RW0C1OperandIdentity(
            *(
                row.value(name)
                for name in RW0C1OperandIdentity.__slots__
            )
        )
    except Exception:
        raise _integrity_failure() from None


def _member_locator_from_operand(row: RW0C1RowValue) -> RW0C1MemberLocatorV1:
    try:
        if row.value("operand_source") != "c1_evidence":
            raise ValueError("wrong source")
        return RW0C1MemberLocatorV1(
            role=typing.cast(str, row.value("operand_role")),
            kind_rank=typing.cast(int, row.value("source_kind_rank")),
            membership_ref=typing.cast(str, row.value("source_membership_ref")),
            membership_digest=typing.cast(
                str,
                row.value("source_membership_digest"),
            ),
            value_ref=typing.cast(str, row.value("operand_ref")),
            value_digest=typing.cast(str, row.value("operand_digest")),
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity_failure() from None


def _owner_locator_from_operand(row: RW0C1RowValue) -> RW0C1OwnerRowLocatorV1:
    try:
        if row.value("operand_source") != "existing_owner_row":
            raise ValueError("wrong source")
        return RW0C1OwnerRowLocatorV1(
            role=typing.cast(str, row.value("operand_role")),
            owner_role=typing.cast(str, row.value("owner_role")),
            row_ref=typing.cast(str, row.value("owner_locator_ref")),
            row_digest=typing.cast(str, row.value("operand_digest")),
            revision=typing.cast(
                int | None,
                row.value("owner_locator_revision"),
            ),
            subrole=typing.cast(
                str | None,
                row.value("owner_locator_subrole"),
            ),
            ordinal=typing.cast(
                int | None,
                row.value("owner_locator_ordinal"),
            ),
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity_failure() from None


def _wrapper_value_from_membership_family(
    family: RW0C1MembershipFamily,
) -> object:
    rank = family.membership.value("kind_rank")
    if rank not in {13, 14, 15} or len(family.relation_set.relations) != 1:
        raise _integrity_failure() from None
    return _wrapper_value_from_membership_family_impl(family)


def _verify_persisted_admission_operand_grammar(
    *,
    rank: int,
    value: object,
    operands: tuple[RW0C1RowValue, ...],
) -> None:
    observed = tuple(
        (
            row.value("operand_role"),
            row.value("operand_source"),
            row.value("source_kind_rank"),
            row.value("owner_role"),
            row.value("transient_binding_kind"),
        )
        for row in operands
    )
    members: list[tuple[str, str, int, None, None]] = []
    owners: list[tuple[str, str, None, str, None]] = []
    transients: list[tuple[str, str, None, None, str]] = []

    def member(role: str, source_rank: int) -> None:
        members.append((role, "c1_evidence", source_rank, None, None))

    def owner(role: str, owner_role: str) -> None:
        owners.append((role, "existing_owner_row", None, owner_role, None))

    def transient(role: str, kind: str) -> None:
        transients.append((role, "transient_private_binding", None, None, kind))

    if rank == 2:
        member("authority_observation", 1)
    elif rank == 4:
        member("authority_observation", 1)
        member("subordinate_proposal", 2)
        member("custody_observation", 3)
        prefix_count = sum(
            1
            for item in observed
            if item[1] == "c1_evidence" and item[2] == 4
        )
        if prefix_count > 2:
            raise _integrity_failure() from None
        for ordinal in range(prefix_count):
            member(f"retrieval_event:{ordinal:03d}", 4)
    elif rank == 6:
        member("authority_observation", 1)
        member("remote_host_readiness", 5)
    elif rank == 8:
        member("capability_declaration", 7)
    elif rank == 9:
        member("authority_observation", 1)
        member("remote_host_readiness", 5)
        member("host_qualification", 6)
        member("capability_declaration", 7)
        member("capability_observation", 8)
    elif rank == 12 and value.observation_kind in {
        "cancellation_acknowledged",
        "cancellation_rejected",
    }:
        member("cancellation_request", 10)
    elif rank == 13:
        wrapped = typing.cast(RW0C1WireWorkerResultBindingV1, value)
        for locator in wrapped.observation_memberships:
            member(locator.role, 12)
    elif rank == 14:
        wrapped = typing.cast(
            RW0C1WireProcessResultClassificationBindingV1,
            value,
        )
        if wrapped.result_membership is not None:
            member("worker_result_binding", 13)
        for locator in wrapped.adapter_observations:
            member(locator.role, 12)
        if wrapped.request_membership is not None:
            member("cancellation_request", 10)
        for locator in wrapped.process_observations:
            member(locator.role, 11)

    for role, owner_role in {
        1: (
            ("attempt_fence", "development_attempt_fence"),
            ("author_effect_fence", "development_effect_fence"),
            ("current_effect_fence", "development_effect_fence"),
            ("author_command", "development_author_command"),
        ),
        2: (
            ("attempt_fence", "development_attempt_fence"),
            ("current_effect_fence", "development_effect_fence"),
        ),
        4: (
            ("attempt_fence", "development_attempt_fence"),
            ("current_effect_fence", "development_effect_fence"),
        ),
        6: (("current_effect_fence", "development_effect_fence"),),
        9: (("current_effect_fence", "development_effect_fence"),),
        10: (
            ("author_command", "development_author_command"),
            ("attempt_fence", "development_attempt_fence"),
            ("author_effect_fence", "development_effect_fence"),
            ("target_effect_fence", "development_effect_fence"),
            ("target_delivery", "development_delivery_attempt"),
            ("cancellation_effect_fence", "development_effect_fence"),
            ("cancellation_delivery", "development_delivery_attempt"),
        ),
        11: (
            ("author_command", "development_author_command"),
            ("attempt_fence", "development_attempt_fence"),
            ("author_effect_fence", "development_effect_fence"),
            ("target_effect_fence", "development_effect_fence"),
            ("target_delivery", "development_delivery_attempt"),
        ),
        12: (
            ("target_delivery", "development_delivery_attempt"),
            ("author_command", "development_author_command"),
            ("attempt_fence", "development_attempt_fence"),
            ("author_effect_fence", "development_effect_fence"),
            ("target_effect_fence", "development_effect_fence"),
        ),
        13: (
            ("author_command", "development_author_command"),
            ("author_delivery", "development_delivery_attempt"),
            ("attempt_fence", "development_attempt_fence"),
            ("author_effect_fence", "development_effect_fence"),
        ),
        14: (
            ("author_command", "development_author_command"),
            ("author_delivery", "development_delivery_attempt"),
            ("attempt_fence", "development_attempt_fence"),
            ("author_effect_fence", "development_effect_fence"),
        ),
        15: (
            ("source_invocation", "development_model_source_invocation"),
            ("artifact_binding", "development_private_proposal_artifact_binding"),
            ("model_proposal", "development_model_proposal"),
        ),
    }.get(rank, ()):
        owner(role, owner_role)

    owner_roles_present = {item[0] for item in observed if item[1] == "existing_owner_row"}
    transient_roles_present = {
        item[0] for item in observed if item[1] == "transient_private_binding"
    }
    if rank == 1:
        if "cancellation_target_effect_fence" in owner_roles_present:
            owner("cancellation_target_effect_fence", "development_effect_fence")
        if "target_capsule_manifest" in transient_roles_present:
            transient("target_capsule_manifest", "candidate_capsule_manifest")
    elif rank == 3:
        if owner_roles_present:
            owner(
                "custody_subject",
                "development_private_proposal_artifact_binding",
            )
        else:
            transient("custody_subject", "work_spec")
    elif rank in {10, 11} and transient_roles_present:
        transient("target_capsule_manifest", "candidate_capsule_manifest")
    elif rank == 12:
        if value.observation_kind in {
            "cancellation_acknowledged",
            "cancellation_rejected",
        }:
            owner("cancellation_effect_fence", "development_effect_fence")
            owner("cancellation_delivery", "development_delivery_attempt")
        for role, kind in (
            ("target_capsule_manifest", "candidate_capsule_manifest"),
            ("before_blob_set", "before_blob_set"),
            ("after_blob_set", "after_blob_set"),
        ):
            if role in transient_roles_present:
                transient(role, kind)
    elif rank == 14:
        if "cancellation_effect_fence" in owner_roles_present:
            owner("cancellation_effect_fence", "development_effect_fence")
            owner("cancellation_delivery", "development_delivery_attempt")
        if typing.cast(
            RW0C1WireProcessResultClassificationBindingV1,
            value,
        ).result_state == "finite_failure":
            transient("worker_result_failure", "wire_protocol_error")
    elif rank == 15:
        wrapped = typing.cast(
            RW0C1Section41PostExecutionProposalFamilyMemberV1,
            value,
        )
        if wrapped.evidence_binding_count == 9:
            for role in (
                "candidate_capsule",
                "worker_result",
                "validation_result",
                "independent_review",
                "standing_policy",
                "risk_lane",
                "authority_currentness_attestation",
                "global_stop",
                "effect_ceiling",
            ):
                owner(role, "development_model_proposal_evidence_binding")
    expected = tuple((*members, *owners, *transients))
    if observed != expected:
        raise _integrity_failure() from None


def _semantic_owner_value(owner_role: str, row: object) -> object:
    """Return the exact semantic value wrapped by one immutable owner row."""

    if type(row) is RW0C1OwnerRowSnapshot:
        semantic = typing.cast(RW0C1OwnerRowSnapshot, row).semantic_value
        if owner_role in {
            "development_attempt_fence",
            "development_effect_fence",
            "development_author_command",
            "development_delivery_attempt",
        }:
            if semantic is None:
                raise _integrity_failure() from None
            return semantic
        return row

    attribute_by_role = {
        "development_attempt_fence": "attempt_fence",
        "development_effect_fence": "effect_fence",
        "development_author_command": "author_command",
        "development_delivery_attempt": "delivery_envelope",
    }
    attribute = attribute_by_role.get(owner_role)
    if attribute is None:
        return row
    try:
        return getattr(row, attribute)
    except Exception:
        raise _integrity_failure() from None


def _verify_recomputable_persisted_relation(
    family: RW0C1MembershipFamily,
    receipt: RW0C1RowValue,
    *,
    capability: object,
    semantic_value: object,
) -> None:
    """Rerun a durable-only owner relation at its persisted semantic instant.

    Attested branches deliberately never enter this helper: their private
    operand is represented only by a privacy-safe aggregate binding.  Every
    other proof mode is reconstructed from the exact immutable member and
    owner operands already verified by the family reader.
    """

    relations = family.relation_set.relations
    if not relations:
        return
    primary = relations[0].binding
    if primary.value("proof_mode") == "relation_attested_at_admission":
        return
    membership = family.membership
    phase = family.phase
    rank = typing.cast(int, membership.value("kind_rank"))
    operands = relations[0].operands
    member_locators = tuple(
        _member_locator_from_operand(row)
        for row in operands
        if row.value("operand_source") == "c1_evidence"
    )
    owner_locators = tuple(
        _owner_locator_from_operand(row)
        for row in operands
        if row.value("operand_source") == "existing_owner_row"
    )
    if any(
        row.value("operand_source") == "transient_private_binding"
        for row in operands
    ):
        raise _integrity_failure() from None

    dependencies: list[RW0C1MembershipFamily] = []
    for locator in member_locators:
        dependency = _read_membership_family(
            capability,
            phase_basis_ref=membership.value("phase_basis_ref"),
            membership_ref=locator.membership_ref,
        )
        if dependency is None or not _dependency_family_matches_locator(
            typing.cast(str, membership.value("phase_basis_ref")),
            locator,
            dependency,
        ):
            raise _integrity_failure() from None
        dependencies.append(dependency)

    result_observation_dependencies = (
        _read_rank14_result_observation_families(
            capability,
            phase_basis_ref=typing.cast(
                str,
                membership.value("phase_basis_ref"),
            ),
            evidence_value=semantic_value,
            dependencies=tuple(dependencies),
        )
        if rank == 14
        else ()
    )

    located: list[tuple[RW0C1OwnerRowLocatorV1, object]] = []
    for locator in owner_locators:
        row = _read_command_owner_row(capability, locator)
        if row is None:
            raise _integrity_failure() from None
        schema_id, row_ref, row_digest = _owner_descriptor(locator.owner_role, row)
        if (
            schema_id != next(
                operand.value("operand_schema_id")
                for operand in operands
                if operand.value("operand_source") == "existing_owner_row"
                and operand.value("operand_role") == locator.role
            )
            or row_ref != locator.row_ref
            or row_digest != locator.row_digest
        ):
            raise _integrity_failure() from None
        located.append((locator, row))

    section41_evidence_rows: tuple[RW0C1OwnerRowSnapshot, ...] = ()
    if rank == 15:
        section41_evidence_rows = (
            _read_section41_post_execution_evidence_family(
                capability,
                proposal_ref=typing.cast(
                    RW0C1Section41PostExecutionProposalFamilyMemberV1,
                    semantic_value,
                ).proposal_ref,
            ).rows
        )

    by_role = {
        locator.role: _semantic_owner_value(locator.owner_role, row)
        for locator, row in located
    }
    basis = _phase_basis_from_row(phase)
    try:
        command = RW0C1AdmitEvidenceCommandV1(
            mutation_ref=typing.cast(
                str, membership.value("admitted_by_mutation_ref")
            ),
            phase_basis_ref=typing.cast(str, membership.value("phase_basis_ref")),
            phase_basis_digest=typing.cast(
                str, membership.value("phase_basis_digest")
            ),
            expected_program_head_revision=typing.cast(
                int, phase.value("expected_program_head_revision")
            ),
            expected_program_head_digest=typing.cast(
                str, phase.value("expected_program_head_digest")
            ),
            expected_work_item_head_revision=typing.cast(
                int, phase.value("expected_work_item_head_revision")
            ),
            expected_work_item_head_digest=typing.cast(
                str, phase.value("expected_work_item_head_digest")
            ),
            preassigned_membership_ref=typing.cast(
                str, membership.value("membership_ref")
            ),
            kind_rank=rank,
            evidence_value=semantic_value,
            prerequisite_member_locators=member_locators,
            owner_row_locators=owner_locators,
        )
    except Exception:
        raise _integrity_failure() from None
    if command.command_digest != receipt.value("command_digest"):
        raise _integrity_failure() from None

    preparation = _RW0C1EvidencePreparation(
        command=command,
        phase=phase,
        basis=basis,
        dependencies=tuple(dependencies),
        result_observation_dependencies=result_observation_dependencies,
        owner_graph=_RW0C1AdmissionOwnerGraph(
            basis=basis,
            program=None,
            work=None,
            work_spec_binding=None,
            attempt_fence=by_role.get("attempt_fence"),
            author_effect_fence=by_role.get("author_effect_fence"),
            author_command=by_role.get("author_command"),
            author_delivery=by_role.get("author_delivery"),
            selection_disposition=None,
            selection_receipt=None,
            selection_head=None,
            selected_proposal=None,
            selected_artifact=by_role.get("custody_subject"),
            effect_head=None,
            delivery_head=None,
            global_stop=None,
            located_owner_rows=tuple(located),
            section41_evidence_rows=section41_evidence_rows,
        ),
        registry_preexisting=True,
    )
    evaluated_at = primary.value("evaluated_at")
    admitted_at = membership.value("admitted_at")
    operation_timestamp = (
        evaluated_at if rank in {1, 2, 3, 4} else admitted_at
    )
    if type(operation_timestamp) is not str or _validate_rank_relation(
        preparation,
        operation_timestamp=operation_timestamp,
    ):
        raise _integrity_failure() from None


def _wrapper_value_from_membership_family_impl(
    family: RW0C1MembershipFamily,
) -> object:
    """Reconstruct one persisted rank-13/14/15 semantic wrapper exactly."""

    rank = family.membership.value("kind_rank")
    payload = family.typed_evidence.payload
    operands = family.relation_set.relations[0].operands
    try:
        binding = family.relation_set.relations[0].binding
        if rank in {13, 14} and (
            payload.value("wire_profile_ref") != "rw0-wire-nwpf-v1"
            or payload.value("wire_profile_digest")
            != "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454"
            or payload.value("relation_ref") != binding.value("relation_ref")
            or payload.value("relation_digest") != binding.value("relation_digest")
        ):
            raise ValueError("wrapper relation mismatch")
        if rank == 13:
            members = tuple(
                _member_locator_from_operand(row)
                for row in operands
                if row.value("operand_source") == "c1_evidence"
            )
            if (
                payload.value("observation_count") != len(members)
                or payload.value("observation_membership_set_digest")
                != _locator_set_digest(
                    (
                        "governed-execution.nwp-rw0-c1-"
                        "worker-result-observation-memberships.v1"
                    ),
                    members,
                )
            ):
                raise ValueError("wrong member set")
            value = RW0C1WireWorkerResultBindingV1(
                value_ref=typing.cast(str, payload.value("value_ref")),
                phase_basis_ref=typing.cast(
                    str,
                    payload.value("phase_basis_ref"),
                ),
                phase_basis_digest=typing.cast(
                    str,
                    payload.value("phase_basis_digest"),
                ),
                program_ref=typing.cast(str, payload.value("program_ref")),
                semantic_attempt_ref=typing.cast(
                    str,
                    payload.value("semantic_attempt_ref"),
                ),
                candidate_ref=typing.cast(str, payload.value("candidate_ref")),
                effect_intent_ref=typing.cast(
                    str,
                    payload.value("effect_intent_ref"),
                ),
                author_command_ref=typing.cast(
                    str,
                    payload.value("author_command_ref"),
                ),
                attempt_fence_ref=typing.cast(
                    str,
                    payload.value("attempt_fence_ref"),
                ),
                effect_fence_ref=typing.cast(
                    str,
                    payload.value("effect_fence_ref"),
                ),
                delivery_attempt_ref=typing.cast(
                    str,
                    payload.value("delivery_attempt_ref"),
                ),
                observation_memberships=members,
                value_digest=typing.cast(str, payload.value("value_digest")),
            )
        elif rank == 14:
            by_role = {
                typing.cast(str, row.value("operand_role")): row
                for row in operands
                if row.value("operand_source") == "c1_evidence"
            }
            result = (
                None
                if payload.value("result_membership_ref") is None
                else _member_locator_from_operand(by_role["worker_result_binding"])
            )
            adapters = tuple(
                _member_locator_from_operand(
                    by_role[f"adapter_observation:{ordinal:03d}"]
                )
                for ordinal in range(
                    typing.cast(int, payload.value("adapter_observation_count"))
                )
            )
            request = (
                None
                if payload.value("request_membership_ref") is None
                else _member_locator_from_operand(by_role["cancellation_request"])
            )
            processes = tuple(
                _member_locator_from_operand(
                    by_role[f"process_observation:{ordinal:03d}"]
                )
                for ordinal in range(
                    typing.cast(int, payload.value("process_observation_count"))
                )
            )
            if (
                (
                    None if result is None else result.membership_ref
                )
                != payload.value("result_membership_ref")
                or (
                    None if result is None else result.membership_digest
                )
                != payload.value("result_membership_digest")
                or (
                    None if request is None else request.membership_ref
                )
                != payload.value("request_membership_ref")
                or (
                    None if request is None else request.membership_digest
                )
                != payload.value("request_membership_digest")
                or
                payload.value("adapter_observation_membership_set_digest")
                != _locator_set_digest(
                    "governed-execution.nwp-rw0-c1-adapter-observation-memberships.v1",
                    adapters,
                )
                or payload.value("process_observation_membership_set_digest")
                != _locator_set_digest(
                    "governed-execution.nwp-rw0-c1-process-observation-memberships.v1",
                    processes,
                )
            ):
                raise ValueError("wrong member set")
            value = RW0C1WireProcessResultClassificationBindingV1(
                value_ref=typing.cast(str, payload.value("value_ref")),
                phase_basis_ref=typing.cast(str, payload.value("phase_basis_ref")),
                phase_basis_digest=typing.cast(
                    str,
                    payload.value("phase_basis_digest"),
                ),
                program_ref=typing.cast(str, payload.value("program_ref")),
                semantic_attempt_ref=typing.cast(
                    str,
                    payload.value("semantic_attempt_ref"),
                ),
                candidate_ref=typing.cast(str, payload.value("candidate_ref")),
                effect_intent_ref=typing.cast(
                    str,
                    payload.value("effect_intent_ref"),
                ),
                author_command_ref=typing.cast(
                    str,
                    payload.value("author_command_ref"),
                ),
                attempt_fence_ref=typing.cast(
                    str,
                    payload.value("attempt_fence_ref"),
                ),
                effect_fence_ref=typing.cast(
                    str,
                    payload.value("effect_fence_ref"),
                ),
                delivery_attempt_ref=typing.cast(
                    str,
                    payload.value("delivery_attempt_ref"),
                ),
                result_state=typing.cast(str, payload.value("result_state")),
                result_membership=result,
                result_failure_reason=typing.cast(
                    str | None,
                    payload.value("result_failure_reason"),
                ),
                adapter_observations=adapters,
                request_membership=request,
                process_observations=processes,
                classification=typing.cast(
                    str,
                    payload.value("classification"),
                ),
                reason=typing.cast(str, payload.value("reason")),
                value_digest=typing.cast(str, payload.value("value_digest")),
            )
        else:
            value = RW0C1Section41PostExecutionProposalFamilyMemberV1(
                **{
                    name: payload.value(name)
                    for name in RW0C1Section41PostExecutionProposalFamilyMemberV1.__slots__
                    if name not in {"schema_id"}
                }
            )
        observed_ref, observed_digest, observed_schema, _scope, _mapping = (
            evidence_identity(value, typing.cast(int, rank))
        )
        registry = family.typed_evidence.registry
        if (
            observed_ref != registry.value("value_ref")
            or observed_digest != registry.value("value_digest")
            or observed_schema != registry.value("value_schema_id")
        ):
            raise ValueError("wrapper mismatch")
        return value
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _integrity_failure() from None


def _probe_rw0_c1_relation_identity_collisions(
    *,
    capability: object,
    plan: RW0C1WritePlan,
) -> RW0C1ConflictV1 | None:
    """Probe both immutable relation identities before the first C1 write."""

    if type(plan) is not RW0C1WritePlan:
        raise _integrity_failure() from None
    relation_rows = tuple(
        row for row in plan.rows if row.table_name == "rw0_relation_bindings"
    )
    expected_count = 1 if plan.mutation_family == "establish_rw0_phase" else None
    if expected_count is not None and len(relation_rows) != expected_count:
        raise _integrity_failure() from None
    if plan.mutation_family == "admit_rw0_evidence" and len(relation_rows) > 2:
        raise _integrity_failure() from None
    for row in relation_rows:
        by_ref = _read_relation_by_ref(capability, row.value("relation_ref"))
        by_digest = _read_relation_by_digest(
            capability,
            row.value("relation_digest"),
        )
        if by_ref is not None or by_digest is not None:
            return _conflict(RW0C1ConflictReasonV1.RELATION_IDENTITY_COLLISION)
    return None


def _persisted_operands_match_replay_command(
    family: RW0C1MembershipFamily,
    command: RW0C1AdmitEvidenceCommandV1,
) -> bool:
    """Compare a replay command with the exact privacy-safe durable operands."""

    relations = family.relation_set.relations
    if not relations:
        return not (
            command.prerequisite_member_locators
            or command.owner_row_locators
            or command.transient_bindings
        )
    operands = relations[0].operands
    try:
        members = tuple(
            _member_locator_from_operand(row).to_mapping()
            for row in operands
            if row.value("operand_source") == "c1_evidence"
        )
        owners = tuple(
            _owner_locator_from_operand(row).to_mapping()
            for row in operands
            if row.value("operand_source") == "existing_owner_row"
        )
        transients = tuple(
            {
                "role": row.value("operand_role"),
                "binding_kind": row.value("transient_binding_kind"),
                "operand_schema_id": row.value("operand_schema_id"),
                "operand_ref": row.value("operand_ref"),
                "operand_digest": row.value("operand_digest"),
                "operand_scope_digest": row.value("operand_scope_digest"),
                "error_reason": row.value("transient_error_reason"),
            }
            for row in operands
            if row.value("operand_source") == "transient_private_binding"
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return False
    return bool(
        members
        == tuple(item.to_mapping() for item in command.prerequisite_member_locators)
        and owners
        == tuple(item.to_mapping() for item in command.owner_row_locators)
        and transients
        == tuple(item.safe_mapping() for item in command.transient_bindings)
    )


def _persisted_operands_match_recovery_selector(
    family: RW0C1MembershipFamily,
    selector: RW0C1EvidenceAdmissionRecoverySelectorV1,
) -> bool:
    """Bind committed immutable member/owner operands to a stable selector."""

    relations = family.relation_set.relations
    if not relations:
        return not (
            selector.prerequisite_member_locators
            or selector.owner_row_locators
        )
    operands = relations[0].operands
    try:
        members = tuple(
            _member_locator_from_operand(row).to_mapping()
            for row in operands
            if row.value("operand_source") == "c1_evidence"
        )
        owners = tuple(
            _owner_locator_from_operand(row).to_mapping()
            for row in operands
            if row.value("operand_source") == "existing_owner_row"
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return False
    return bool(
        members
        == tuple(
            item.to_mapping()
            for item in selector.prerequisite_member_locators
        )
        and owners
        == tuple(item.to_mapping() for item in selector.owner_row_locators)
    )


def _typed_reusable_evidence_matches_recovery_selector(
    aggregate: object,
    selector: RW0C1EvidenceAdmissionRecoverySelectorV1,
) -> bool:
    """Prove an existing global registry/payload is exactly reusable."""

    if (
        type(aggregate) is not RW0C1TypedEvidenceAggregate
        or selector.kind_rank not in {5, 7, 8}
    ):
        return False
    registry = aggregate.registry
    if (
        registry.value("kind_rank") != selector.kind_rank
        or registry.value("value_ref") != selector.value_ref
        or registry.value("value_digest") != selector.value_digest
        or registry.value("value_schema_id") != selector.value_schema_id
        or registry.value("scope_class") != "global_reusable"
    ):
        return False
    semantic_value = _owner_value_from_typed_evidence(aggregate)
    observed_ref, observed_digest, observed_schema, scope, _mapping = (
        evidence_identity(semantic_value, selector.kind_rank)
    )
    return bool(
        observed_ref == selector.value_ref
        and observed_digest == selector.value_digest
        and observed_schema == selector.value_schema_id
        and scope == "global_reusable"
    )


def _verify_evidence_family_rows(
    family: RW0C1MembershipFamily,
    receipt: RW0C1RowValue,
    *,
    capability: object,
    replay_command: RW0C1AdmitEvidenceCommandV1 | None = None,
) -> None:
    membership = family.membership
    registry = family.typed_evidence.registry
    phase = family.phase
    rank = membership.value("kind_rank")
    if (
        type(rank) is not int
        or not 1 <= rank <= 15
        or receipt.table_name != "rw0_c1_mutation_receipts"
        or receipt.value("mutation_family") != "admit_rw0_evidence"
        or receipt.value("command_schema_id")
        != "governed-execution.nwp-rw0-c1-admit-evidence-command.v1"
        or receipt.value("result_class") != "rw0_evidence_admitted"
        or receipt.value("outcome") != "committed"
        or receipt.value("mutation_ref")
        != membership.value("admitted_by_mutation_ref")
        or receipt.value("membership_ref") != membership.value("membership_ref")
        or receipt.value("membership_digest")
        != membership.value("membership_digest")
        or receipt.value("phase_basis_ref") != membership.value("phase_basis_ref")
        or receipt.value("phase_basis_digest")
        != membership.value("phase_basis_digest")
        or receipt.value("kind_rank") != rank
        or receipt.value("value_ref") != membership.value("value_ref")
        or receipt.value("value_digest") != membership.value("value_digest")
        or receipt.value("value_schema_id")
        != membership.value("value_schema_id")
        or receipt.value("admission_graph_digest")
        != membership.value("admission_graph_digest")
        or receipt.value("committed_at") != membership.value("admitted_at")
        or phase.value("phase_basis_ref") != membership.value("phase_basis_ref")
        or phase.value("phase_basis_digest")
        != membership.value("phase_basis_digest")
        or registry.value("scope_class")
        != RW0_C1_KIND_SPECS[rank - 1].scope_class
    ):
        raise _integrity_failure() from None
    if replay_command is not None and (
        type(replay_command) is not RW0C1AdmitEvidenceCommandV1
        or replay_command.mutation_ref != receipt.value("mutation_ref")
        or replay_command.command_digest != receipt.value("command_digest")
        or replay_command.phase_basis_ref != membership.value("phase_basis_ref")
        or replay_command.phase_basis_digest
        != membership.value("phase_basis_digest")
        or replay_command.preassigned_membership_ref
        != membership.value("membership_ref")
        or replay_command.kind_rank != rank
        or not _persisted_operands_match_replay_command(
            family,
            replay_command,
        )
    ):
        raise _integrity_failure() from None
    expected_count = len(family.relation_set.relations)
    if (
        (rank in {5, 7} and expected_count != 0)
        or rank == 12 and expected_count not in {1, 2}
        or rank not in {5, 7, 12} and expected_count != 1
    ):
        raise _integrity_failure() from None
    transient_kinds = tuple(
        typing.cast(str, operand.value("transient_binding_kind"))
        for relation in family.relation_set.relations
        for operand in relation.operands
        if operand.value("operand_source") == "transient_private_binding"
    )
    transient_kinds = tuple(dict.fromkeys(transient_kinds))
    expected_specifications = relation_specifications(
        kind_rank=rank,
        cancellation_response=(rank == 12 and expected_count == 2),
        transient_binding_kinds=transient_kinds,
        rank14_result_state=(
            typing.cast(str, family.typed_evidence.payload.value("result_state"))
            if rank == 14
            else None
        ),
    )
    if len(expected_specifications) != expected_count:
        raise _integrity_failure() from None
    if expected_count == 2:
        first_operands = tuple(
            _operand_identity_from_row(row)
            for row in family.relation_set.relations[0].operands
        )
        second_operands = tuple(
            _operand_identity_from_row(row)
            for row in family.relation_set.relations[1].operands
        )
        if first_operands != second_operands:
            raise _integrity_failure() from None
    relation_identifiers: list[tuple[int, str, str]] = []
    graph_relations: list[dict[str, object]] = []
    for relation, expected_specification in zip(
        family.relation_set.relations, expected_specifications, strict=True
    ):
        binding = relation.binding
        operands = tuple(
            _operand_identity_from_row(row) for row in relation.operands
        )
        specification = RW0C1RelationSpecification(
            rank,
            typing.cast(int, binding.value("relation_rank")),
            typing.cast(str, binding.value("relation_schema_id")),
            typing.cast(str, binding.value("proof_mode")),
            typing.cast(str | None, binding.value("profile_ref")),
            typing.cast(str | None, binding.value("profile_digest")),
        )
        expected_ref = relation_reference(
            phase_basis_ref=typing.cast(str, membership.value("phase_basis_ref")),
            phase_basis_digest=typing.cast(str, membership.value("phase_basis_digest")),
            subject_type="evidence_membership",
            subject_membership_ref=typing.cast(str, membership.value("membership_ref")),
            relation_rank=expected_specification.relation_rank,
        )
        if specification != expected_specification or binding.value("relation_ref") != expected_ref:
            raise _integrity_failure() from None
        expected_digest, expected_operands = relation_digest(
            phase_basis_ref=typing.cast(
                str, membership.value("phase_basis_ref")
            ),
            phase_basis_digest=typing.cast(
                str, membership.value("phase_basis_digest")
            ),
            relation_ref=typing.cast(str, binding.value("relation_ref")),
            subject_type="evidence_membership",
            subject_membership_ref=typing.cast(
                str, membership.value("membership_ref")
            ),
            subject_kind_rank=rank,
            subject_value_ref=typing.cast(str, membership.value("value_ref")),
            subject_value_digest=typing.cast(
                str, membership.value("value_digest")
            ),
            subject_value_schema_id=typing.cast(
                str, membership.value("value_schema_id")
            ),
            specification=specification,
            evaluated_at=typing.cast(str | None, binding.value("evaluated_at")),
            operands=operands,
        )
        if (
            binding.value("relation_digest") != expected_digest
            or binding.value("operand_set_digest") != expected_operands
            or binding.value("phase_basis_ref")
            != membership.value("phase_basis_ref")
            or binding.value("subject_type") != "evidence_membership"
            or binding.value("subject_membership_ref")
            != membership.value("membership_ref")
            or binding.value("subject_membership_digest")
            != membership.value("membership_digest")
            or binding.value("subject_kind_rank") != rank
            or binding.value("subject_value_ref") != membership.value("value_ref")
            or binding.value("subject_value_digest") != membership.value("value_digest")
            or binding.value("subject_value_schema_id")
            != membership.value("value_schema_id")
            or binding.value("phase_basis_digest")
            != membership.value("phase_basis_digest")
            or binding.value("relation_version") != 1
            or binding.value("operand_count") != len(relation.operands)
        ):
            raise _integrity_failure() from None
        relation_identifiers.append(
            (
                specification.relation_rank,
                typing.cast(str, binding.value("relation_ref")),
                expected_digest,
            )
        )
        graph_relations.append(
            {
                "relation_rank": specification.relation_rank,
                "relation_ref": binding.value("relation_ref"),
                "relation_digest": expected_digest,
                "operand_set_digest": expected_operands,
                "evaluated_at": binding.value("evaluated_at"),
            }
        )
        for operand in relation.operands:
            source = operand.value("operand_source")
            if source == "c1_evidence":
                dependency = _read_membership_family(
                    capability,
                    phase_basis_ref=membership.value("phase_basis_ref"),
                    membership_ref=operand.value("source_membership_ref"),
                )
                if (
                    dependency is None
                    or dependency.membership.value("membership_digest")
                    != operand.value("source_membership_digest")
                    or dependency.membership.value("kind_rank")
                    != operand.value("source_kind_rank")
                    or dependency.membership.value("value_ref")
                    != operand.value("operand_ref")
                    or dependency.membership.value("value_digest")
                    != operand.value("operand_digest")
                    or dependency.membership.value("value_schema_id")
                    != operand.value("operand_schema_id")
                    or dependency.membership.value("scope_binding_digest")
                    != operand.value("operand_scope_digest")
                ):
                    raise _integrity_failure() from None
            elif source == "existing_owner_row":
                try:
                    locator = RW0C1OwnerRowLocatorV1(
                        role=typing.cast(str, operand.value("operand_role")),
                        owner_role=typing.cast(str, operand.value("owner_role")),
                        row_ref=typing.cast(str, operand.value("owner_locator_ref")),
                        row_digest=typing.cast(str, operand.value("operand_digest")),
                        revision=typing.cast(
                            int | None, operand.value("owner_locator_revision")
                        ),
                        subrole=typing.cast(
                            str | None, operand.value("owner_locator_subrole")
                        ),
                        ordinal=typing.cast(
                            int | None, operand.value("owner_locator_ordinal")
                        ),
                    )
                except RW0C1PreflightError:
                    raise _integrity_failure() from None
                owner_row = _read_command_owner_row(capability, locator)
                if owner_row is None:
                    raise _integrity_failure() from None
                schema_id, row_ref, row_digest = _owner_descriptor(
                    locator.owner_role, owner_row
                )
                if (
                    schema_id != operand.value("operand_schema_id")
                    or row_ref != locator.row_ref
                    or row_ref != operand.value("operand_ref")
                    or row_digest != locator.row_digest
                ):
                    raise _integrity_failure() from None
            elif source == "admission_snapshot_binding":
                raise _integrity_failure() from None

        evaluated_at = binding.value("evaluated_at")
        admitted_at = membership.value("admitted_at")
        if rank in {1, 2, 3, 4}:
            if evaluated_at != admitted_at:
                raise _integrity_failure() from None
        elif rank == 6:
            if (
                evaluated_at != family.typed_evidence.payload.value("evaluated_at")
                or typing.cast(str, evaluated_at) > typing.cast(str, admitted_at)
            ):
                raise _integrity_failure() from None
        elif rank == 9:
            host_operands = tuple(
                operand
                for operand in relation.operands
                if operand.value("operand_source") == "c1_evidence"
                and operand.value("source_kind_rank") == 6
            )
            if len(host_operands) != 1:
                raise _integrity_failure() from None
            host_family = _read_membership_family(
                capability,
                phase_basis_ref=membership.value("phase_basis_ref"),
                membership_ref=host_operands[0].value("source_membership_ref"),
            )
            if (
                host_family is None
                or evaluated_at
                != family.typed_evidence.payload.value("evaluated_at")
                or evaluated_at
                != host_family.typed_evidence.payload.value("evaluated_at")
                or typing.cast(str, evaluated_at) > typing.cast(str, admitted_at)
            ):
                raise _integrity_failure() from None
        elif evaluated_at is not None:
            raise _integrity_failure() from None
    expected_relation_set = relation_set_digest(
        phase_basis_ref=typing.cast(str, membership.value("phase_basis_ref")),
        subject_type="evidence_membership",
        subject_ref=typing.cast(str, membership.value("membership_ref")),
        relations=tuple(relation_identifiers),
    )
    if membership.value("relation_set_digest") != expected_relation_set:
        raise _integrity_failure() from None
    value_schema_id = typing.cast(str, membership.value("value_schema_id"))
    if rank in {5, 7, 8}:
        expected_scope = global_scope_binding_digest(rank, value_schema_id)
    elif rank in {13, 14}:
        expected_scope = phase.value("k8_digest")
    elif rank == 15:
        expected_scope = family.typed_evidence.payload.value(
            "owner_family_graph_digest"
        )
    else:
        expected_scope = membership.value("phase_basis_digest")
    if membership.value("scope_binding_digest") != expected_scope:
        raise _integrity_failure() from None
    graph_identity = {
        "schema_id": "governed-execution.nwp-rw0-c1-evidence-admission-graph.v1",
        "phase_basis_ref": membership.value("phase_basis_ref"),
        "phase_basis_digest": membership.value("phase_basis_digest"),
        "membership_ref": membership.value("membership_ref"),
        "kind_rank": rank,
        "value_ref": membership.value("value_ref"),
        "value_digest": membership.value("value_digest"),
        "value_schema_id": value_schema_id,
        "scope_binding_digest": expected_scope,
        "relation_set_digest": expected_relation_set,
        "relations": graph_relations,
        "admitted_by_mutation_ref": membership.value("admitted_by_mutation_ref"),
        "admitted_at": membership.value("admitted_at"),
    }
    expected_graph = admission_graph_digest(graph_identity)
    membership_identity = {
        "schema_id": membership.value("schema_id"),
        "membership_ref": membership.value("membership_ref"),
        "phase_basis_ref": membership.value("phase_basis_ref"),
        "phase_basis_digest": membership.value("phase_basis_digest"),
        "kind_rank": rank,
        "value_ref": membership.value("value_ref"),
        "value_digest": membership.value("value_digest"),
        "value_schema_id": value_schema_id,
        "scope_binding_digest": expected_scope,
        "relation_set_digest": expected_relation_set,
        "admitted_by_mutation_ref": membership.value("admitted_by_mutation_ref"),
        "admitted_at": membership.value("admitted_at"),
        "admission_graph_digest": expected_graph,
    }
    if (
        membership.value("admission_graph_digest") != expected_graph
        or membership.value("membership_digest")
        != membership_digest(membership_identity)
        or registry.value("kind_rank") != rank
        or registry.value("value_ref") != membership.value("value_ref")
        or registry.value("value_digest") != membership.value("value_digest")
        or registry.value("value_schema_id") != value_schema_id
    ):
        raise _integrity_failure() from None
    semantic_value = (
        _owner_value_from_typed_evidence(family.typed_evidence)
        if rank <= 12
        else _wrapper_value_from_membership_family(family)
    )
    for relation in family.relation_set.relations:
        _verify_persisted_admission_operand_grammar(
            rank=rank,
            value=semantic_value,
            operands=relation.operands,
        )
    _verify_recomputable_persisted_relation(
        family,
        receipt,
        capability=capability,
        semantic_value=semantic_value,
    )
    if rank in {14, 15}:
        owner_operands = tuple(
            row
            for row in family.relation_set.relations[0].operands
            if row.value("operand_source") == "existing_owner_row"
        )
        located: list[tuple[RW0C1OwnerRowLocatorV1, object]] = []
        for operand in owner_operands:
            locator = _owner_locator_from_operand(operand)
            row = _read_command_owner_row(capability, locator)
            if row is None:
                raise _integrity_failure() from None
            located.append((locator, row))
        if rank == 15:
            if not _section41_owner_family_matches(
                typing.cast(
                    RW0C1Section41PostExecutionProposalFamilyMemberV1,
                    semantic_value,
                ),
                tuple(located),
                _read_section41_post_execution_evidence_family(
                    capability,
                    proposal_ref=typing.cast(
                        RW0C1Section41PostExecutionProposalFamilyMemberV1,
                        semantic_value,
                    ).proposal_ref,
                ).rows,
            ):
                raise _integrity_failure() from None
        else:
            by_role = {locator.role: row for locator, row in located}
            cancellation_effect = by_role.get("cancellation_effect_fence")
            cancellation_delivery = by_role.get("cancellation_delivery")
            payload = family.typed_evidence.payload
            if cancellation_effect is None:
                observed_effect = (None, None)
            else:
                effect_value = _semantic_owner_value(
                    "development_effect_fence", cancellation_effect
                )
                observed_effect = (
                    effect_value.effect_fence_ref,
                    effect_value.effect_fence_digest,
                )
            if cancellation_delivery is None:
                observed_delivery = (None, None)
            else:
                delivery_value = _semantic_owner_value(
                    "development_delivery_attempt", cancellation_delivery
                )
                observed_delivery = (
                    delivery_value.delivery_attempt_ref,
                    delivery_value.delivery_envelope_digest,
                )
            if observed_effect != (
                payload.value("cancellation_effect_fence_ref"),
                payload.value("cancellation_effect_fence_digest"),
            ) or observed_delivery != (
                payload.value("cancellation_delivery_attempt_ref"),
                payload.value("cancellation_delivery_envelope_digest"),
            ):
                raise _integrity_failure() from None


def _readback_rw0_c1_evidence_admission(
    *,
    capability: object,
    plan: RW0C1WritePlan,
) -> RW0C1AdmitEvidenceResultV1:
    if type(plan) is not RW0C1WritePlan or plan.mutation_family != "admit_rw0_evidence":
        raise _integrity_failure() from None
    result = typing.cast(RW0C1AdmitEvidenceResultV1, plan.result)
    family = _read_membership_family(
        capability,
        phase_basis_ref=result.phase_basis_ref,
        membership_ref=result.membership_ref,
    )
    receipt = _read_receipt(capability, result.mutation_ref)
    if family is None or receipt is None:
        raise _integrity_failure() from None
    _verify_evidence_family_rows(family, receipt, capability=capability)
    complete_observed: tuple[RW0C1RowValue, ...] = (
        family.typed_evidence.registry,
        family.typed_evidence.payload,
        *family.typed_evidence.children,
        family.membership,
        *tuple(
            row
            for relation in family.relation_set.relations
            for row in (relation.binding, *relation.operands)
        ),
        receipt,
    )
    if plan.rows[0].table_name == "rw0_evidence_memberships":
        observed = complete_observed[
            2 + len(family.typed_evidence.children):
        ]
    else:
        observed = complete_observed
    if len(observed) != len(plan.rows) or any(
        not _exact_mapping(left, right)
        for left, right in zip(observed, plan.rows, strict=True)
    ):
        raise _integrity_failure() from None
    if (
        receipt.value("receipt_digest") != result.receipt_digest
        or receipt.value("result_projection_digest")
        != result.committed_projection_digest()
    ):
        raise _integrity_failure() from None
    return result


def _recover_rw0_c1_evidence_admission_after_fencing(
    *,
    capability: object,
    selector: RW0C1EvidenceAdmissionRecoverySelectorV1,
) -> RW0C1RecoveryResultV1:
    if type(selector) is not RW0C1EvidenceAdmissionRecoverySelectorV1:
        raise _integrity_failure() from None
    try:
        receipt = _read_receipt(capability, selector.mutation_ref)
        if receipt is not None:
            if (
                receipt.value("mutation_family") != "admit_rw0_evidence"
                or receipt.value("command_digest") != selector.command_digest
                or receipt.value("phase_basis_ref") != selector.phase_basis_ref
                or receipt.value("phase_basis_digest")
                != selector.phase_basis_digest
                or receipt.value("membership_ref")
                != selector.preassigned_membership_ref
                or receipt.value("kind_rank") != selector.kind_rank
                or receipt.value("value_ref") != selector.value_ref
                or receipt.value("value_digest") != selector.value_digest
                or receipt.value("value_schema_id") != selector.value_schema_id
            ):
                raise ValueError("unresolved")
            durable_membership_digest = typing.cast(
                str,
                receipt.value("membership_digest"),
            )
            membership_ref = _read_membership_by_ref(
                capability,
                selector.preassigned_membership_ref,
            )
            membership_digest_row = _read_membership_by_digest(
                capability,
                durable_membership_digest,
            )
            if (
                membership_ref is None
                or membership_digest_row is None
                or membership_ref.as_tuple() != membership_digest_row.as_tuple()
            ):
                raise ValueError("unresolved")
            family = _read_membership_family(
                capability,
                phase_basis_ref=selector.phase_basis_ref,
                membership_ref=selector.preassigned_membership_ref,
            )
            if family is None:
                raise ValueError("unresolved")
            membership = family.membership
            if (
                membership.value("membership_digest")
                != durable_membership_digest
                or membership.value("kind_rank") != selector.kind_rank
                or membership.value("value_ref") != selector.value_ref
                or membership.value("value_digest") != selector.value_digest
                or membership.value("value_schema_id")
                != selector.value_schema_id
                or not _persisted_operands_match_recovery_selector(
                    family,
                    selector,
                )
            ):
                raise ValueError("unresolved")
            _verify_evidence_family_rows(
                family,
                receipt,
                capability=capability,
            )
            result = RW0C1AdmitEvidenceResultV1(
                mutation_ref=selector.mutation_ref,
                command_digest=selector.command_digest,
                disposition="exact_replay",
                phase_basis_ref=selector.phase_basis_ref,
                phase_basis_digest=selector.phase_basis_digest,
                membership_ref=selector.preassigned_membership_ref,
                membership_digest=durable_membership_digest,
                kind_rank=selector.kind_rank,
                value_ref=selector.value_ref,
                value_digest=selector.value_digest,
                value_schema_id=selector.value_schema_id,
                relation_set_digest=typing.cast(
                    str,
                    membership.value("relation_set_digest"),
                ),
                admission_graph_digest=typing.cast(
                    str,
                    membership.value("admission_graph_digest"),
                ),
                receipt_digest=typing.cast(
                    str,
                    receipt.value("receipt_digest"),
                ),
                committed_at=typing.cast(str, receipt.value("committed_at")),
            )
            if result.committed_projection_digest() != receipt.value(
                "result_projection_digest"
            ):
                raise ValueError("unresolved")
            return RW0C1RecoveryResultV1(
                "admit_rw0_evidence",
                selector.mutation_ref,
                selector.command_digest,
                RW0C1RecoveryDispositionV1.COMMITTED_EXACT,
                typing.cast(str, receipt.value("receipt_digest")),
                typing.cast(str, receipt.value("result_projection_digest")),
                typing.cast(str, membership.value("admission_graph_digest")),
            )

        phase_pair = _read_phase_by_pair(
            capability,
            selector.phase_basis_ref,
            selector.phase_basis_digest,
        )
        phase_ref = _read_phase_by_ref(capability, selector.phase_basis_ref)
        phase_digest = _read_phase_by_digest(
            capability,
            selector.phase_basis_digest,
        )
        if (
            phase_pair is None
            or phase_ref is None
            or phase_digest is None
            or phase_pair.as_tuple() != phase_ref.as_tuple()
            or phase_pair.as_tuple() != phase_digest.as_tuple()
        ):
            raise ValueError("unresolved")

        for locator in selector.prerequisite_member_locators:
            dependency = _read_membership_family(
                capability,
                phase_basis_ref=selector.phase_basis_ref,
                membership_ref=locator.membership_ref,
            )
            if dependency is None or not _dependency_family_matches_locator(
                selector.phase_basis_ref,
                locator,
                dependency,
            ):
                raise ValueError("unresolved")
            dependency_receipt = _read_receipt(
                capability,
                dependency.membership.value("admitted_by_mutation_ref"),
            )
            if dependency_receipt is None:
                raise ValueError("unresolved")
            _verify_evidence_family_rows(
                dependency,
                dependency_receipt,
                capability=capability,
            )

        for locator in selector.owner_row_locators:
            owner_row = _read_command_owner_row(capability, locator)
            if owner_row is None:
                raise ValueError("unresolved")
            _schema_id, row_ref, row_digest = _owner_descriptor(
                locator.owner_role,
                owner_row,
            )
            if row_ref != locator.row_ref or row_digest != locator.row_digest:
                raise ValueError("unresolved")

        membership_ref = _read_membership_by_ref(
            capability,
            selector.preassigned_membership_ref,
        )
        membership_route_ref = _read_membership_by_phase_kind_ref(
            capability,
            selector.phase_basis_ref,
            selector.kind_rank,
            selector.value_ref,
        )
        membership_route_digest = _read_membership_by_phase_kind_digest(
            capability,
            selector.phase_basis_ref,
            selector.kind_rank,
            selector.value_digest,
        )
        relation_ref_0 = relation_reference(
            phase_basis_ref=selector.phase_basis_ref,
            phase_basis_digest=selector.phase_basis_digest,
            subject_type="evidence_membership",
            subject_membership_ref=selector.preassigned_membership_ref,
            relation_rank=0,
        )
        relation_ref_1 = relation_reference(
            phase_basis_ref=selector.phase_basis_ref,
            phase_basis_digest=selector.phase_basis_digest,
            subject_type="evidence_membership",
            subject_membership_ref=selector.preassigned_membership_ref,
            relation_rank=1,
        )
        relation_0 = _read_relation_by_ref(capability, relation_ref_0)
        relation_1 = _read_relation_by_ref(capability, relation_ref_1)
        operands_0 = _read_relation_operands(
            capability,
            relation_ref=relation_ref_0,
        )
        operands_1 = _read_relation_operands(
            capability,
            relation_ref=relation_ref_1,
        )
        relation_set = _read_relation_set(
            capability=capability,
            phase_basis_ref=selector.phase_basis_ref,
            membership_ref=selector.preassigned_membership_ref,
        )
        if (
            membership_ref is not None
            or membership_route_ref is not None
            or membership_route_digest is not None
            or relation_0 is not None
            or relation_1 is not None
            or len(operands_0) != 0
            or len(operands_1) != 0
            or len(relation_set.relations) != 0
        ):
            raise ValueError("unresolved")

        registry_ref = _read_registry_by_kind_ref(
            capability,
            selector.kind_rank,
            selector.value_ref,
        )
        registry_digest = _read_registry_by_kind_digest(
            capability,
            selector.kind_rank,
            selector.value_digest,
        )
        payload_ref = _read_typed_payload_by_kind_ref(
            capability,
            kind_rank=selector.kind_rank,
            value_ref=selector.value_ref,
        )
        payload_digest = _read_typed_payload_by_kind_digest(
            capability,
            kind_rank=selector.kind_rank,
            value_digest=selector.value_digest,
        )
        children_ref = _read_typed_children_by_ref(
            capability,
            kind_rank=selector.kind_rank,
            value_ref=selector.value_ref,
        )
        children_digest = _read_typed_children_by_digest(
            capability,
            kind_rank=selector.kind_rank,
            value_digest=selector.value_digest,
        )
        if (
            registry_ref is None
            and registry_digest is None
            and payload_ref is None
            and payload_digest is None
            and len(children_ref) == 0
            and len(children_digest) == 0
        ):
            pass
        elif (
            registry_ref is None
            or registry_digest is None
            or registry_ref.as_tuple() != registry_digest.as_tuple()
            or payload_ref is None
            or payload_digest is None
            or payload_ref.as_tuple() != payload_digest.as_tuple()
            or tuple(row.as_tuple() for row in children_ref)
            != tuple(row.as_tuple() for row in children_digest)
            or not _typed_reusable_evidence_matches_recovery_selector(
                RW0C1TypedEvidenceAggregate(
                    registry_ref,
                    payload_ref,
                    children_ref,
                ),
                selector,
            )
        ):
            raise ValueError("unresolved")
        return RW0C1RecoveryResultV1(
            "admit_rw0_evidence",
            selector.mutation_ref,
            selector.command_digest,
            RW0C1RecoveryDispositionV1.DEFINITELY_NOT_COMMITTED,
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return RW0C1RecoveryResultV1(
            "admit_rw0_evidence",
            selector.mutation_ref,
            selector.command_digest,
            RW0C1RecoveryDispositionV1.UNRESOLVED,
        )
