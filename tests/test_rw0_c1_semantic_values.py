from __future__ import annotations

import copy

import pytest

import ge_nwp_coordinator._rw0_c1_semantic_values as values
import ge_nwp_coordinator._rw0_phase_entry_semantic_values as b1
import ge_nwp_coordinator._rw0_wire_protocol_values as wire
from ge_nwp_coordinator._worker_execution_semantic_values import (
    CandidateCapsuleManifestV1,
    WorkSpecV1,
)
from tests.c2a_contract_support import _full_record
from test_rw0_b1_relations import claims, value
from test_rw0_b2_capability_relations import host_graph


EXPECTED_KINDS = (
    "authority_verification_observation",
    "subordinate_authorization_proposal",
    "custody_availability_observation",
    "retrieval_capability_event_observation",
    "remote_host_readiness_observation",
    "effect_host_qualification",
    "worker_mechanism_capability_declaration",
    "worker_mechanism_capability_observation",
    "worker_mechanism_capability_qualification",
    "wire_cancellation_request_observation",
    "wire_process_observation",
    "c2a_worker_observation",
    "wire_worker_result_binding",
    "wire_process_result_classification_binding",
    "section41_post_execution_proposal_family_member",
)


def _locator(role: str, rank: int, suffix: str) -> values.RW0C1MemberLocatorV1:
    return values.RW0C1MemberLocatorV1(
        role,
        rank,
        f"membership.{suffix}",
        (hex(rank)[2:] * 64)[:64],
        f"value.{suffix}",
        (hex(rank + 1)[2:] * 64)[:64],
    )


def test_exact_fifteen_kind_inventory_schemas_and_scope_classes() -> None:
    assert tuple(member.value for member in values.RW0C1EvidenceKindV1) == EXPECTED_KINDS
    assert values.RW0_C1_KIND_RANKS == tuple(enumerate(EXPECTED_KINDS, 1))
    assert tuple(spec.rank for spec in values.RW0_C1_KIND_SPECS) == tuple(range(1, 16))
    assert tuple(spec.kind.value for spec in values.RW0_C1_KIND_SPECS) == EXPECTED_KINDS
    assert tuple(spec.scope_class for spec in values.RW0_C1_KIND_SPECS) == (
        "phase_bound", "phase_bound", "phase_bound", "phase_bound",
        "global_reusable", "phase_bound", "global_reusable", "global_reusable",
        "phase_bound", "k8_bound", "k8_bound", "k8_bound", "k8_bound",
        "k8_bound", "existing_owner_row_bound",
    )


def test_private_values_are_final_immutable_content_free_and_noncopyable() -> None:
    locator = _locator("authority_observation", 1, "authority.0001")
    assert repr(locator) == "<RW0C1MemberLocatorV1>"
    assert locator.membership_ref not in repr(locator)
    with pytest.raises(TypeError):
        copy.copy(locator)
    with pytest.raises(TypeError):
        copy.deepcopy(locator)
    with pytest.raises(TypeError):
        class Forbidden(values.RW0C1MemberLocatorV1):
            pass
    with pytest.raises(AttributeError):
        locator.role = "other"  # type: ignore[misc]


def test_transient_and_snapshot_bindings_persist_only_safe_aggregate_identity() -> None:
    work_spec = WorkSpecV1.from_mapping(_full_record("WorkSpecV1"))
    transient = values.RW0C1TransientPrivateBindingV1.work_spec(
        role="custody_subject",
        value=work_spec,
        safe_projection_digest="a" * 64,
    )
    assert transient.safe_mapping() == {
        "role": "custody_subject",
        "binding_kind": "work_spec",
        "operand_schema_id": (
            "governed-execution.nwp-rw0-c1-transient-work-spec-binding.v1"
        ),
        "operand_ref": work_spec.work_spec_ref,
        "operand_digest": work_spec.work_spec_digest,
        "operand_scope_digest": "a" * 64,
        "error_reason": None,
    }
    assert "authorized_paths" not in transient.safe_mapping()
    snapshot = values.RW0C1AdmissionSnapshotBindingV1(
        "effect_head",
        "effect_head_snapshot",
        "phase.safe.0001",
        "b" * 64,
        (("head_revision", 3), ("effect_state", "authorized")),
    )
    assert snapshot.operand_ref == f"rw0-c1-snapshot.effect.{'b' * 64}"
    assert snapshot.operand_scope_digest == "b" * 64
    assert set(snapshot.safe_mapping()) == {
        "role", "snapshot_kind", "operand_schema_id", "operand_ref",
        "operand_digest", "operand_scope_digest",
    }

    manifest = CandidateCapsuleManifestV1.from_mapping(
        _full_record("CandidateCapsuleManifestV1")
    )
    capsule = values.RW0C1TransientPrivateBindingV1.candidate_capsule_manifest(
        role="target_capsule_manifest",
        value=manifest,
    )
    assert "entries" not in capsule.safe_mapping()
    blobs = {
        "private-a": b"alpha",
        "private-b": b"beta",
        "private-c": b"gamma",
    }
    blob_binding = values.RW0C1TransientPrivateBindingV1.blob_set(
        role="before_blob_set",
        binding_kind="before_blob_set",
        blobs=blobs,
        authorized_path_scope_digest="c" * 64,
    )
    assert not set(blobs).intersection(str(blob_binding.safe_mapping()))
    with pytest.raises(wire.RW0WireProtocolError) as caught:
        wire._raise_public("short_header")
    error_binding = values.RW0C1TransientPrivateBindingV1.wire_protocol_error(
        role="worker_result_failure",
        value=caught.value,
    )
    assert error_binding.safe_mapping()["error_reason"] == "short_header"
    assert "traceback" not in str(error_binding.safe_mapping())


def test_command_result_and_receipt_schemas_form_closed_exact_projections() -> None:
    basis, _authority, _proposal, work_spec, *_rest = claims()
    establish = values.RW0C1EstablishPhaseCommandV1(
        mutation_ref="mutation.phase.values.0001",
        phase_basis=basis,
        work_spec=work_spec,
        work_spec_safe_projection_digest="1" * 64,
        expected_program_head_revision=2,
        expected_program_head_digest="2" * 64,
        expected_work_item_head_revision=3,
        expected_work_item_head_digest="3" * 64,
    )
    readiness = value(
        b1.RW0RemoteHostReadinessObservationV1,
        observation_ref="readiness.values.0001",
    )
    admit = values.RW0C1AdmitEvidenceCommandV1(
        mutation_ref="mutation.member.values.0001",
        phase_basis_ref=basis.basis_ref,
        phase_basis_digest=basis.basis_digest,
        expected_program_head_revision=2,
        expected_program_head_digest="2" * 64,
        expected_work_item_head_revision=3,
        expected_work_item_head_digest="3" * 64,
        preassigned_membership_ref="membership.values.0001",
        kind_rank=5,
        evidence_value=readiness,
    )
    timestamp = "2029-01-01T00:00:00Z"
    phase_result = values.RW0C1EstablishPhaseResultV1(
        establish.mutation_ref,
        establish.command_digest,
        "fresh_committed",
        basis.basis_ref,
        basis.basis_digest,
        "4" * 64,
        "5" * 64,
        "6" * 64,
        timestamp,
    )
    value_ref, value_digest, value_schema_id, _scope, _mapping = (
        values.evidence_identity(readiness, 5)
    )
    member_result = values.RW0C1AdmitEvidenceResultV1(
        admit.mutation_ref,
        admit.command_digest,
        "fresh_committed",
        basis.basis_ref,
        basis.basis_digest,
        admit.preassigned_membership_ref,
        "7" * 64,
        5,
        value_ref,
        value_digest,
        value_schema_id,
        "8" * 64,
        "9" * 64,
        "a" * 64,
        timestamp,
    )
    phase_receipt = values.RW0C1MutationReceiptV1(
        establish.mutation_ref,
        "establish_rw0_phase",
        establish.schema_id,
        establish.command_digest,
        basis.basis_ref,
        basis.basis_digest,
        None,
        None,
        None,
        None,
        None,
        None,
        "rw0_phase_established",
        phase_result.committed_projection_digest(),
        phase_result.phase_graph_digest,
        "committed",
        timestamp,
    )
    member_receipt = values.RW0C1MutationReceiptV1(
        admit.mutation_ref,
        "admit_rw0_evidence",
        admit.schema_id,
        admit.command_digest,
        basis.basis_ref,
        basis.basis_digest,
        member_result.membership_ref,
        member_result.membership_digest,
        5,
        value_ref,
        value_digest,
        value_schema_id,
        "rw0_evidence_admitted",
        member_result.committed_projection_digest(),
        member_result.admission_graph_digest,
        "committed",
        timestamp,
    )
    assert tuple(establish.identity_mapping()) == (
        "schema_id",
        "mutation_ref",
        "phase_basis",
        "work_spec",
        "work_spec_safe_projection_digest",
        "expected_program_head_revision",
        "expected_program_head_digest",
        "expected_work_item_head_revision",
        "expected_work_item_head_digest",
    )
    assert tuple(admit.identity_mapping())[-4:] == (
        "evidence_value",
        "prerequisite_member_locators",
        "owner_row_locators",
        "transient_bindings",
    )
    assert phase_receipt.mutation_family == "establish_rw0_phase"
    assert member_receipt.mutation_family == "admit_rw0_evidence"
    assert phase_result.safe_projection()["schema_id"].endswith("result.v1")
    assert member_result.safe_projection()["schema_id"].endswith("result.v1")


def test_evidence_recovery_selector_is_pure_preapply_and_needs_no_membership_digest() -> None:
    basis, _authority, _proposal, _work_spec, *_rest = claims()
    readiness = value(
        b1.RW0RemoteHostReadinessObservationV1,
        observation_ref="readiness.selector.0001",
    )
    command = values.RW0C1AdmitEvidenceCommandV1(
        mutation_ref="mutation.member.selector.0001",
        phase_basis_ref=basis.basis_ref,
        phase_basis_digest=basis.basis_digest,
        expected_program_head_revision=2,
        expected_program_head_digest="2" * 64,
        expected_work_item_head_revision=3,
        expected_work_item_head_digest="3" * 64,
        preassigned_membership_ref="membership.selector.0001",
        kind_rank=5,
        evidence_value=readiness,
    )

    constructor = getattr(
        values,
        "evidence_admission_recovery_selector",
        None,
    )
    assert callable(constructor)
    selector = constructor(command)
    value_ref, value_digest, value_schema_id, _scope, _mapping = (
        values.evidence_identity(readiness, 5)
    )
    assert tuple(selector.identity_mapping()) == (
        "schema_id",
        "mutation_ref",
        "command_digest",
        "phase_basis_ref",
        "phase_basis_digest",
        "preassigned_membership_ref",
        "kind_rank",
        "value_ref",
        "value_digest",
        "value_schema_id",
        "prerequisite_member_locators",
        "owner_row_locators",
    )
    assert selector.schema_id == (
        "governed-execution.nwp-rw0-c1-"
        "evidence-admission-recovery-selector.v1"
    )
    assert selector.mutation_ref == command.mutation_ref
    assert selector.command_digest == command.command_digest
    assert selector.preassigned_membership_ref == command.preassigned_membership_ref
    assert (selector.value_ref, selector.value_digest, selector.value_schema_id) == (
        value_ref,
        value_digest,
        value_schema_id,
    )
    assert not hasattr(selector, "membership_digest")
    assert not hasattr(selector, "admitted_at")
    assert not hasattr(selector, "relation_set_digest")
    assert not hasattr(selector, "result_digest")
    assert not hasattr(selector, "receipt_digest")
    assert not hasattr(selector, "transient_bindings")
    assert len(selector.selector_digest) == 64
    assert repr(selector) == "<RW0C1EvidenceAdmissionRecoverySelectorV1>"
    with pytest.raises(TypeError):
        copy.copy(selector)


def test_rank13_and_rank14_result_state_branch_algebras_are_closed() -> None:
    started = _locator("worker_observation:000", 12, "started.0001")
    completed = _locator("worker_observation:001", 12, "completed.0001")
    result = values.RW0C1WireWorkerResultBindingV1(
        "worker-result.safe.0001", "phase.safe.0001", "a" * 64,
        "program.safe.0001", "attempt.safe.0001", "candidate.safe.0001",
        "effect.safe.0001", "command.safe.0001", "attempt-fence.safe.0001",
        "effect-fence.safe.0001", "delivery.safe.0001", (started, completed),
    )
    assert result.observation_memberships == (started, completed)
    result_member = _locator("worker_result_binding", 13, "result.0001")
    adapter0 = _locator("adapter_observation:000", 12, "adapter.0001")
    present = values.RW0C1WireProcessResultClassificationBindingV1(
        "classification.present.0001", "phase.safe.0001", "a" * 64,
        "program.safe.0001", "attempt.safe.0001", "candidate.safe.0001",
        "effect.safe.0001", "command.safe.0001", "attempt-fence.safe.0001",
        "effect-fence.safe.0001", "delivery.safe.0001", "present",
        result_member, None, (adapter0,), None, (), "usable", "usable",
    )
    assert present.result_state == "present" and present.result_failure_reason is None
    absent = values.RW0C1WireProcessResultClassificationBindingV1(
        "classification.absent.0001", "phase.safe.0001", "a" * 64,
        "program.safe.0001", "attempt.safe.0001", "candidate.safe.0001",
        "effect.safe.0001", "command.safe.0001", "attempt-fence.safe.0001",
        "effect-fence.safe.0001", "delivery.safe.0001", "absent",
        None, None, (), None, (), "unusable", "result_missing",
    )
    assert absent.result_state == "absent"
    with pytest.raises(values.RW0C1PreflightError):
        values.RW0C1WireProcessResultClassificationBindingV1(
            "classification.invalid.0001", "phase.safe.0001", "a" * 64,
            "program.safe.0001", "attempt.safe.0001", "candidate.safe.0001",
            "effect.safe.0001", "command.safe.0001", "attempt-fence.safe.0001",
            "effect-fence.safe.0001", "delivery.safe.0001", "finite_failure",
            result_member, "bad_magic", (), None, (), "unusable", "result_invalid",
        )


def test_conflict_preflight_recovery_and_result_vocabularies_are_exact() -> None:
    assert tuple(member.value for member in values.RW0C1ConflictReasonV1) == (
        "stale_writer_token", "mutation_ref_reuse", "phase_identity_collision",
        "k8_collision", "current_state_conflict", "member_identity_collision",
        "member_already_admitted", "missing_prerequisite_member",
        "relation_failure", "relation_identity_collision", "owner_row_missing",
    )
    assert tuple(member.value for member in values.RW0C1RecoveryDispositionV1) == (
        "committed_exact", "definitely_not_committed", "unresolved",
    )
    conflict = values.RW0C1ConflictV1(
        values.RW0C1ConflictReasonV1.MUTATION_REF_REUSE
    )
    assert conflict.safe_projection() == {"reason": "mutation_ref_reuse"}
    probe = values.RW0C1RecoveryProbeV1(
        "establish_rw0_phase", "mutation.phase.0001", "a" * 64,
        "phase.safe.0001", "b" * 64,
        k8=tuple(f"k8.safe.{index}" for index in range(8)),
    )
    assert probe.k8 is not None and len(probe.k8) == 8
    recovery = values.RW0C1RecoveryResultV1(
        "establish_rw0_phase", probe.mutation_ref, probe.command_digest,
        values.RW0C1RecoveryDispositionV1.DEFINITELY_NOT_COMMITTED,
    )
    assert recovery.safe_projection()["disposition"] == "definitely_not_committed"
    preflight = values.RW0C1PreflightError("secret-value")
    assert preflight.reason == "invalid_value"
    assert repr(preflight) == "<RW0C1PreflightError>"


def test_temporal_source_registry_separates_operation_and_subject_time() -> None:
    _basis, authority, *_rest = claims()
    operation_time = "2029-01-01T00:00:00Z"
    assert values.relation_evaluation_time(
        relation_schema_id=(
            "governed-execution.nwp-rw0-c1-"
            "authority-verification-observation-relation.v1"
        ),
        evidence_value=authority,
        operation_timestamp=operation_time,
    ) == operation_time
    _basis, _authority, _readiness, host, _effect = host_graph()
    assert values.relation_evaluation_time(
        relation_schema_id=(
            "governed-execution.nwp-rw0-c1-host-qualification-relation.v1"
        ),
        evidence_value=host,
        operation_timestamp="2029-01-02T00:00:00Z",
    ) == host.evaluated_at
    assert values.relation_evaluation_time(
        relation_schema_id=(
            "governed-execution.nwp-rw0-c1-host-qualification-relation.v1"
        ),
        evidence_value=host,
        operation_timestamp=host.evaluated_at,
    ) == host.evaluated_at
    assert values.relation_evaluation_time(
        relation_schema_id=(
            "governed-execution.nwp-rw0-c1-wire-worker-result-relation.v1"
        ),
        evidence_value=object(),
        operation_timestamp=operation_time,
    ) is None
    with pytest.raises(values.RW0C1PreflightError):
        values.relation_evaluation_time(
            relation_schema_id=(
                "governed-execution.nwp-rw0-c1-unknown-relation.v1"
            ),
            evidence_value=object(),
            operation_timestamp=operation_time,
        )
    with pytest.raises(values.RW0C1PreflightError):
        values.relation_evaluation_time(
            relation_schema_id=(
                "governed-execution.nwp-rw0-c1-host-qualification-relation.v1"
            ),
            evidence_value=host,
            operation_timestamp="2028-01-01T00:00:00Z",
        )
