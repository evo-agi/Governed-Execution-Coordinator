from __future__ import annotations

from dataclasses import dataclass, replace
import sqlite3
from pathlib import Path

import pytest

import ge_nwp_coordinator._cognitive_proposal_row_values as cognitive_rows
import ge_nwp_coordinator._rw0_phase_entry_semantic_values as b1
import ge_nwp_coordinator._rw0_c1_row_values as c1_rows
import ge_nwp_coordinator._rw0_worker_mechanism_capability_values as capability
import ge_nwp_coordinator._worker_execution_semantic_values as worker_values
import ge_nwp_coordinator._sqlite_rw0_c1 as runtime
import ge_nwp_coordinator.sqlite_transition_transaction as transaction
from ge_nwp_coordinator._rw0_c1_mutation_contracts import (
    section41_owner_family_graph_digest,
)
from ge_nwp_coordinator._rw0_c1_semantic_values import (
    RW0C1AdmitEvidenceCommandV1,
    RW0C1AdmitEvidenceResultV1,
    RW0C1ConflictReasonV1,
    RW0C1ConflictV1,
    RW0C1EstablishPhaseCommandV1,
    RW0C1EstablishPhaseResultV1,
    RW0C1MemberLocatorV1,
    RW0C1OwnerRowLocatorV1,
    RW0C1Section41PostExecutionProposalFamilyMemberV1,
    RW0C1TransientPrivateBindingV1,
    RW0C1WireProcessResultClassificationBindingV1,
    RW0C1WireWorkerResultBindingV1,
)
import ge_nwp_coordinator._rw0_wire_protocol_values as wire
from ge_nwp_coordinator._rw0_wire_protocol_values import (
    RW0WireCancellationRequestObservationV1,
    RW0WireProcessObservationV1,
)
from ge_nwp_coordinator._worker_execution_semantic_values import WorkerObservationV1
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError,
    SQLiteMutationStoreErrorCode,
)
from test_rw0_b1_relations import EFFECT_CLASSES, phase_bundle, value
from test_rw0_b1_vectors import mapping_for
from test_rw0_b2_capability_values import (
    declaration_mapping,
    observation_mapping,
    qualification_mapping,
)
from test_rw0_b2_wire_values import (
    adapter_observation,
    process_mapping,
    request_mapping,
    worker_observation,
)
from test_remote_worker_pre_execution_planning_contract import (
    _build_repaired_common_phase_rows,
    _insert_exact_repaired_values,
)


OPERATION_TIME = "2099-01-01T00:00:00Z"


@dataclass
class C1Harness:
    bundle: dict[str, object]
    writer: object
    phase_command: RW0C1EstablishPhaseCommandV1
    phase_result: RW0C1EstablishPhaseResultV1
    delivery_row: object
    source_row: object
    projection_row: object

    def close(self) -> None:
        self.writer.close()


def _row(
    connection: sqlite3.Connection,
    table: str,
    columns: tuple[str, ...],
    where: str,
    parameter: str,
) -> tuple[object, ...]:
    found = connection.execute(
        f"SELECT {', '.join(columns)} FROM {table} WHERE {where} LIMIT 2",
        (parameter,),
    ).fetchall()
    assert len(found) == 1 and type(found[0]) is tuple
    return found[0]


def make_c1_harness(
    tmp_path: Path,
    *,
    suffix: str,
    timestamp: str = OPERATION_TIME,
) -> C1Harness:
    bundle = phase_bundle(tmp_path / suffix)
    location = bundle["author_fixture"].location
    connection = sqlite3.connect(location.database_path)
    try:
        safe_projection_digest = connection.execute(
            "SELECT safe_projection_digest FROM development_work_spec_bindings "
            "WHERE work_spec_ref=?",
            (bundle["work_spec"].work_spec_ref,),
        ).fetchone()[0]
        import ge_nwp_coordinator._development_effect_row_values as effect_rows

        delivery_row = effect_rows.development_delivery_attempt_row_value_from_row_tuple(
            _row(
                connection,
                "development_delivery_attempts",
                effect_rows._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS,
                "delivery_attempt_ref=?",
                bundle["author_delivery"].delivery_attempt_ref,
            )
        )
        proposal = bundle["selected_proposal"]
        source_row = cognitive_rows._row_value_from_tuple(
            "development_model_source_invocations",
            _row(
                connection,
                "development_model_source_invocations",
                cognitive_rows._TABLE_COLUMNS[
                    "development_model_source_invocations"
                ],
                "source_invocation_ref=?",
                proposal.source_invocation_ref,
            ),
        )
        projection_row = cognitive_rows._row_value_from_tuple(
            "development_pre_execution_plan_projections",
            _row(
                connection,
                "development_pre_execution_plan_projections",
                cognitive_rows._TABLE_COLUMNS[
                    "development_pre_execution_plan_projections"
                ],
                "proposal_ref=?",
                proposal.proposal_ref,
            ),
        )
    finally:
        connection.close()
    command = RW0C1EstablishPhaseCommandV1(
        mutation_ref=f"mutation.rw0-c1.phase.{suffix}",
        phase_basis=bundle["basis"],
        work_spec=bundle["work_spec"],
        work_spec_safe_projection_digest=safe_projection_digest,
        expected_program_head_revision=bundle["program_head"].head_revision,
        expected_program_head_digest=bundle["program_head"].head_digest,
        expected_work_item_head_revision=bundle["work_head"].head_revision,
        expected_work_item_head_digest=bundle["work_head"].head_digest,
    )
    writer = acquire_sqlite_writer_session(location)
    original_clock = transaction._capture_transaction_timestamp
    transaction._capture_transaction_timestamp = lambda: timestamp
    try:
        result = writer._establish_rw0_phase(command)
    finally:
        transaction._capture_transaction_timestamp = original_clock
    assert type(result) is RW0C1EstablishPhaseResultV1
    return C1Harness(
        bundle, writer, command, result, delivery_row, source_row, projection_row
    )


def member_locator(
    result: RW0C1AdmitEvidenceResultV1,
    role: str,
) -> RW0C1MemberLocatorV1:
    return RW0C1MemberLocatorV1(
        role,
        result.kind_rank,
        result.membership_ref,
        result.membership_digest,
        result.value_ref,
        result.value_digest,
    )


def _owner_locator(
    role: str,
    owner_role: str,
    row: object,
    *,
    ref_name: str,
    digest_name: str,
) -> RW0C1OwnerRowLocatorV1:
    return RW0C1OwnerRowLocatorV1(
        role,
        owner_role,
        getattr(row, ref_name),
        getattr(row, digest_name),
    )


def owner_locators(harness: C1Harness, rank: int) -> tuple[RW0C1OwnerRowLocatorV1, ...]:
    bundle = harness.bundle
    attempt = lambda role: _owner_locator(
        role, "development_attempt_fence", bundle["attempt_fence"],
        ref_name="attempt_fence_ref", digest_name="attempt_fence_digest",
    )
    effect = lambda role: _owner_locator(
        role, "development_effect_fence", bundle["author_effect_fence"],
        ref_name="effect_fence_ref", digest_name="effect_fence_digest",
    )
    command = lambda role: _owner_locator(
        role, "development_author_command", bundle["author_command"],
        ref_name="command_ref", digest_name="command_digest",
    )
    delivery = lambda role: _owner_locator(
        role, "development_delivery_attempt", harness.delivery_row,
        ref_name="delivery_attempt_ref", digest_name="delivery_attempt_digest",
    )
    if rank == 1:
        return (
            attempt("attempt_fence"), effect("author_effect_fence"),
            effect("current_effect_fence"), command("author_command"),
        )
    if rank in {2, 4}:
        return (attempt("attempt_fence"), effect("current_effect_fence"))
    if rank == 3:
        return (
            _owner_locator(
                "custody_subject",
                "development_private_proposal_artifact_binding",
                bundle["selected_artifact"],
                ref_name="artifact_ref",
                digest_name="artifact_binding_digest",
            ),
        )
    if rank in {6, 9}:
        return (effect("current_effect_fence"),)
    if rank == 10:
        return (
            command("author_command"), attempt("attempt_fence"),
            effect("author_effect_fence"), effect("target_effect_fence"),
            delivery("target_delivery"), effect("cancellation_effect_fence"),
            delivery("cancellation_delivery"),
        )
    if rank in {11, 12}:
        return (
            *( (delivery("target_delivery"),) if rank == 12 else () ),
            command("author_command"), attempt("attempt_fence"),
            effect("author_effect_fence"), effect("target_effect_fence"),
            *( () if rank == 12 else (delivery("target_delivery"),) ),
        )
    if rank in {13, 14}:
        return (
            command("author_command"), delivery("author_delivery"),
            attempt("attempt_fence"), effect("author_effect_fence"),
        )
    if rank == 15:
        return (
            _owner_locator(
                "source_invocation", "development_model_source_invocation",
                harness.source_row, ref_name="source_invocation_ref",
                digest_name="source_invocation_digest",
            ),
            _owner_locator(
                "artifact_binding",
                "development_private_proposal_artifact_binding",
                bundle["selected_artifact"], ref_name="artifact_ref",
                digest_name="artifact_binding_digest",
            ),
            _owner_locator(
                "model_proposal", "development_model_proposal",
                bundle["selected_proposal"], ref_name="proposal_ref",
                digest_name="proposal_digest",
            ),
        )
    return ()


def admission_command(
    harness: C1Harness,
    *,
    rank: int,
    value: object,
    sequence: int,
    dependencies: tuple[RW0C1MemberLocatorV1, ...] = (),
    owners: tuple[RW0C1OwnerRowLocatorV1, ...] | None = None,
    transients: tuple[RW0C1TransientPrivateBindingV1, ...] = (),
) -> RW0C1AdmitEvidenceCommandV1:
    bundle = harness.bundle
    return RW0C1AdmitEvidenceCommandV1(
        mutation_ref=f"mutation.rw0-c1.member.{sequence:03d}",
        phase_basis_ref=harness.phase_result.phase_basis_ref,
        phase_basis_digest=harness.phase_result.phase_basis_digest,
        expected_program_head_revision=bundle["program_head"].head_revision,
        expected_program_head_digest=bundle["program_head"].head_digest,
        expected_work_item_head_revision=bundle["work_head"].head_revision,
        expected_work_item_head_digest=bundle["work_head"].head_digest,
        preassigned_membership_ref=f"membership.rw0-c1.{sequence:03d}",
        kind_rank=rank,
        evidence_value=value,
        prerequisite_member_locators=dependencies,
        owner_row_locators=(owner_locators(harness, rank) if owners is None else owners),
        transient_bindings=transients,
    )


def admit(
    harness: C1Harness,
    *,
    rank: int,
    value: object,
    sequence: int,
    dependencies: tuple[RW0C1MemberLocatorV1, ...] = (),
    owners: tuple[RW0C1OwnerRowLocatorV1, ...] | None = None,
    transients: tuple[RW0C1TransientPrivateBindingV1, ...] = (),
) -> RW0C1AdmitEvidenceResultV1:
    command = admission_command(
        harness,
        rank=rank,
        value=value,
        sequence=sequence,
        dependencies=dependencies,
        owners=owners,
        transients=transients,
    )
    result = harness.writer._admit_rw0_evidence(command)
    assert type(result) is RW0C1AdmitEvidenceResultV1, result.safe_projection()
    assert result.kind_rank == rank
    return result


def _mechanics_values(harness: C1Harness) -> dict[int, object]:
    basis = harness.bundle["basis"]
    phase = {
        "phase_basis_ref": basis.basis_ref,
        "phase_basis_digest": basis.basis_digest,
    }
    rank1 = value(b1.RW0AuthorityVerificationObservationV1, **phase)
    rank2 = value(b1.RW0SubordinateAuthorizationProposalV1, **phase)
    rank3 = value(b1.RW0CustodyAvailabilityObservationV1, **phase)
    rank4 = value(b1.RW0RetrievalCapabilityEventObservationV1, **phase)
    rank5 = value(b1.RW0RemoteHostReadinessObservationV1)
    rank6 = value(
        b1.RW0EffectHostQualificationV1,
        **phase,
        evaluated_at="2029-01-01T00:00:00Z",
    )
    declaration_record = declaration_mapping()
    observation_record = observation_mapping(declaration_record)
    rank7 = capability.RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(
        declaration_record
    )
    rank8 = capability.RW0WorkerMechanismCapabilityObservationV1.from_mapping(
        observation_record
    )
    rank9 = capability.RW0WorkerMechanismCapabilityQualificationV1.from_mapping(
        qualification_mapping(declaration_record, observation_record, **phase)
    )
    rank10 = RW0WireCancellationRequestObservationV1.from_mapping(request_mapping())
    rank11 = RW0WireProcessObservationV1.from_mapping(process_mapping())
    return {
        1: rank1, 2: rank2, 3: rank3, 4: rank4, 5: rank5, 6: rank6,
        7: rank7, 8: rank8, 9: rank9, 10: rank10, 11: rank11,
    }


def _install_counted_owner_relation_seams(
    monkeypatch: pytest.MonkeyPatch,
) -> list[str]:
    """Keep the real C1 dispatcher while isolating unrelated owner fixtures."""

    calls: list[str] = []

    def successful(label: str, result: object = None):
        def invoke(*_args: object, **_kwargs: object) -> object:
            calls.append(label)
            return result

        return invoke

    for owner, name, label in (
        (b1, "validate_authority_observation", "rank1_authority"),
        (b1, "validate_subordinate_narrowing", "rank2_narrowing"),
        (b1, "validate_custody_binding", "rank3_custody"),
        (b1, "validate_retrieval_event_sequence", "rank4_retrieval"),
        (b1, "validate_host_qualification", "rank6_host"),
        (
            capability,
            "validate_worker_mechanism_capability_qualification",
            "rank9_capability_qualification",
        ),
        (
            wire,
            "validate_wire_exact_current_cancellation_request_relation",
            "rank10_cancellation_request",
        ),
        (
            wire,
            "validate_wire_exact_current_process_observation_relation",
            "rank11_process",
        ),
        (
            worker_values,
            "validate_observation_relation",
            "rank12_worker_observation",
        ),
        (
            wire,
            "validate_wire_exact_current_cancellation_response_relation",
            "rank12_cancellation_response",
        ),
        (wire, "validate_wire_result_relation", "rank13_worker_result"),
    ):
        monkeypatch.setattr(owner, name, successful(label))

    monkeypatch.setattr(
        runtime,
        "_validate_capability_observation_binding",
        successful("rank8_capability_observation"),
    )

    def classify(**arguments: object) -> object:
        calls.append("rank14_process_result_classifier")
        if arguments["result"] is not None:
            return wire.RW0WireProcessResultClassificationV1._create(
                "usable",
                "usable",
            )
        if arguments["result_failure"] is not None:
            return wire.RW0WireProcessResultClassificationV1._create(
                "unusable",
                "result_invalid",
            )
        return wire.RW0WireProcessResultClassificationV1._create(
            "unusable",
            "result_missing",
        )

    monkeypatch.setattr(wire, "classify_wire_process_result", classify)
    monkeypatch.setattr(
        runtime,
        "_section41_owner_family_matches",
        successful("rank15_section41", True),
    )
    return calls


def valid_rank1_value(harness: C1Harness) -> b1.RW0AuthorityVerificationObservationV1:
    bundle = harness.bundle
    basis = bundle["basis"]
    attempt = bundle["attempt_fence"]
    effect = bundle["author_effect_fence"]
    return value(
        b1.RW0AuthorityVerificationObservationV1,
        phase_basis_ref=basis.basis_ref,
        phase_basis_digest=basis.basis_digest,
        parent_grant_ref=attempt.parent_standing_grant_ref,
        parent_grant_digest=attempt.parent_standing_grant_digest,
        attempt_basis_ref=attempt.attempt_authorization_ref,
        attempt_basis_digest=attempt.attempt_authorization_digest,
        effect_basis_ref=effect.effect_authorization_ref,
        effect_basis_digest=effect.effect_authorization_digest,
        attempt_fence_ref=attempt.attempt_fence_ref,
        attempt_fence_digest=attempt.attempt_fence_digest,
        effect_fence_ref=effect.effect_fence_ref,
        effect_fence_digest=effect.effect_fence_digest,
        audience_ref=attempt.program_ref,
        repository_ref=attempt.repository_ref,
        base_git_object_format=attempt.base_git_object_format,
        base_git_oid=attempt.base_git_oid,
        path_scope_digest=b1._path_scope_binding_digest(
            bundle["work_spec"].authorized_paths
        ),
        allowed_effect_classes=list(EFFECT_CLASSES),
        parent_ceilings=attempt.aggregate_ceilings.to_mapping(),
        effect_class=effect.effect_class,
        grant_expires_at="2100-01-01T00:00:00Z",
        observed_at="2028-01-01T00:00:00Z",
        observation_expires_at="2100-01-01T00:00:00Z",
        current_effect_head_digest=basis.current_effect_head_digest,
        current_delivery_head_digest=basis.current_delivery_head_digest,
        global_stop_ref=basis.global_stop_ref,
        global_stop_version=basis.global_stop_version,
        global_stop_state=basis.global_stop_state,
    )


def _install_rank15_owner_family(
    harness: C1Harness,
    *,
    evidence_binding_count: int,
) -> tuple[
    tuple[RW0C1OwnerRowLocatorV1, ...],
    RW0C1Section41PostExecutionProposalFamilyMemberV1,
]:
    physical = _build_repaired_common_phase_rows(
        "post_execution_semantic_review",
        "post_execution_semantic_review",
        "post_execution_semantic_review",
        post_evidence_count=evidence_binding_count,
    )
    connection = sqlite3.connect(
        harness.bundle["author_fixture"].location.database_path
    )
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        for member in physical:
            _insert_exact_repaired_values(
                connection,
                member["table"],
                member["values"],
            )
        connection.commit()
    finally:
        connection.close()
    rows = tuple(
        cognitive_rows._row_value_from_mapping(
            member["table"], member["values"]
        )
        for member in physical
    )
    source, artifact, proposal, *evidence = rows
    owners = (
        _owner_locator(
            "source_invocation",
            "development_model_source_invocation",
            source,
            ref_name="source_invocation_ref",
            digest_name="source_invocation_digest",
        ),
        _owner_locator(
            "artifact_binding",
            "development_private_proposal_artifact_binding",
            artifact,
            ref_name="artifact_ref",
            digest_name="artifact_binding_digest",
        ),
        _owner_locator(
            "model_proposal",
            "development_model_proposal",
            proposal,
            ref_name="proposal_ref",
            digest_name="proposal_digest",
        ),
        *(
            RW0C1OwnerRowLocatorV1(
                row.evidence_role,
                "development_model_proposal_evidence_binding",
                row.proposal_ref,
                row.evidence_binding_digest,
                None,
                row.evidence_role,
                0,
            )
            for row in evidence
        ),
    )
    wrapped = RW0C1Section41PostExecutionProposalFamilyMemberV1(
        f"postexecution.family.safe.{evidence_binding_count:04d}",
        harness.phase_result.phase_basis_ref,
        harness.phase_result.phase_basis_digest,
        source.source_invocation_ref,
        source.source_invocation_digest,
        artifact.artifact_ref,
        artifact.artifact_digest,
        artifact.artifact_binding_digest,
        proposal.proposal_ref,
        proposal.proposal_digest,
        proposal.model_contract_ref,
        proposal.model_contract_digest,
        proposal.model_configuration_ref,
        proposal.model_configuration_digest,
        "governed-execution.nwp-post-execution-semantic-review-context.v1",
        proposal.context_ref,
        proposal.context_digest,
        "governed-execution.nwp-post-execution-semantic-review-safe-projection.v1",
        proposal.safe_projection_digest,
        proposal.evidence_set_ref,
        proposal.evidence_set_digest,
        evidence_binding_count,
        proposal.recommendation,
        proposal.reason_code,
        proposal.proposal_created_at,
        section41_owner_family_graph_digest(owners),
    )
    return owners, wrapped


def _rank14_value(
    harness: C1Harness,
    *,
    sequence: int,
    result_state: str,
    result_membership: RW0C1MemberLocatorV1 | None = None,
    result_failure_reason: str | None = None,
    adapter_observations: tuple[RW0C1MemberLocatorV1, ...] = (),
    request_membership: RW0C1MemberLocatorV1 | None = None,
    process_observations: tuple[RW0C1MemberLocatorV1, ...] = (),
    classification: str,
    reason: str,
) -> RW0C1WireProcessResultClassificationBindingV1:
    basis = harness.bundle["basis"]
    lineage = basis.c2b3d_lineage
    return RW0C1WireProcessResultClassificationBindingV1(
        f"process-result.binding.c1.{sequence:04d}",
        basis.basis_ref,
        basis.basis_digest,
        lineage.program_ref,
        lineage.semantic_attempt_ref,
        lineage.candidate_ref,
        lineage.effect_intent_ref,
        lineage.author_command_ref,
        lineage.attempt_fence_ref,
        lineage.effect_fence_ref,
        lineage.delivery_attempt_ref,
        result_state,
        result_membership,
        result_failure_reason,
        adapter_observations,
        request_membership,
        process_observations,
        classification,
        reason,
    )


def _assert_conflict(
    outcome: object,
    reason: RW0C1ConflictReasonV1,
) -> None:
    assert type(outcome) is RW0C1ConflictV1
    assert outcome.reason is reason
    assert outcome.safe_projection() == {"reason": reason.value}


def test_phase_establishment_is_atomic_receipt_last_replayed_without_new_clock(
    tmp_path: Path,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="phase-atomic")
    try:
        assert harness.phase_result.disposition == "fresh_committed"
        original_timestamp = harness.phase_result.committed_at
        original_clock = transaction._capture_transaction_timestamp
        transaction._capture_transaction_timestamp = lambda: (_ for _ in ()).throw(
            AssertionError("replay captured a clock")
        )
        try:
            replay = harness.writer._establish_rw0_phase(harness.phase_command)
        finally:
            transaction._capture_transaction_timestamp = original_clock
        assert type(replay) is RW0C1EstablishPhaseResultV1
        assert replay.disposition == "exact_replay"
        assert replay.committed_at == original_timestamp
        connection = sqlite3.connect(
            harness.bundle["author_fixture"].location.database_path
        )
        try:
            assert connection.execute("SELECT count(*) FROM rw0_phase_instances").fetchone() == (1,)
            assert connection.execute(
                "SELECT count(*) FROM rw0_relation_operands"
            ).fetchone() == (14,)
            assert connection.execute(
                "SELECT mutation_family FROM rw0_c1_mutation_receipts"
            ).fetchone() == ("establish_rw0_phase",)
        finally:
            connection.close()
    finally:
        harness.close()


def test_phase_receipt_precedence_identity_and_k8_conflicts_are_content_free(
    tmp_path: Path,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="phase-conflicts")
    try:
        mutation_reuse = replace(
            harness.phase_command,
            expected_program_head_revision=(
                harness.phase_command.expected_program_head_revision + 1
            ),
            command_digest="",
        )
        _assert_conflict(
            harness.writer._establish_rw0_phase(mutation_reuse),
            RW0C1ConflictReasonV1.MUTATION_REF_REUSE,
        )

        identity_collision = replace(
            harness.phase_command,
            mutation_ref="mutation.rw0-c1.phase.identity-collision",
            command_digest="",
        )
        _assert_conflict(
            harness.writer._establish_rw0_phase(identity_collision),
            RW0C1ConflictReasonV1.PHASE_IDENTITY_COLLISION,
        )

        altered_mapping = harness.phase_command.phase_basis.to_mapping()
        altered_mapping["basis_ref"] = "phase.basis.k8-collision.0001"
        altered_mapping["selection_head_revision"] = (
            altered_mapping["selection_head_revision"] + 1
        )
        altered_mapping["basis_digest"] = b1._trusted_b1_digest(
            b1.RW0PhaseEntryBasisV1,
            altered_mapping,
        )
        altered_basis = b1.RW0PhaseEntryBasisV1.from_mapping(altered_mapping)
        k8_collision = replace(
            harness.phase_command,
            mutation_ref="mutation.rw0-c1.phase.k8-collision",
            phase_basis=altered_basis,
            command_digest="",
        )
        _assert_conflict(
            harness.writer._establish_rw0_phase(k8_collision),
            RW0C1ConflictReasonV1.K8_COLLISION,
        )
    finally:
        harness.close()


def test_admission_conflicts_cover_receipt_identity_dependency_relation_and_owner_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="admission-conflicts")
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: OPERATION_TIME,
    )
    values_by_rank = _mechanics_values(harness)
    try:
        original_command = admission_command(
            harness,
            rank=5,
            value=values_by_rank[5],
            sequence=201,
        )
        original = harness.writer._admit_rw0_evidence(original_command)
        assert type(original) is RW0C1AdmitEvidenceResultV1

        mutation_reuse = replace(
            original_command,
            preassigned_membership_ref="membership.rw0-c1.reused-command",
            command_digest="",
        )
        _assert_conflict(
            harness.writer._admit_rw0_evidence(mutation_reuse),
            RW0C1ConflictReasonV1.MUTATION_REF_REUSE,
        )

        member_identity_collision = replace(
            original_command,
            mutation_ref="mutation.rw0-c1.member.identity-collision",
            command_digest="",
        )
        _assert_conflict(
            harness.writer._admit_rw0_evidence(member_identity_collision),
            RW0C1ConflictReasonV1.MEMBER_IDENTITY_COLLISION,
        )

        already_admitted = replace(
            original_command,
            mutation_ref="mutation.rw0-c1.member.already-admitted",
            preassigned_membership_ref="membership.rw0-c1.already-admitted",
            command_digest="",
        )
        _assert_conflict(
            harness.writer._admit_rw0_evidence(already_admitted),
            RW0C1ConflictReasonV1.MEMBER_ALREADY_ADMITTED,
        )

        current_state = admission_command(
            harness,
            rank=5,
            value=value(
                b1.RW0RemoteHostReadinessObservationV1,
                observation_ref="remote.host.current-conflict.0001",
            ),
            sequence=202,
        )
        current_state = replace(
            current_state,
            expected_work_item_head_revision=(
                current_state.expected_work_item_head_revision + 1
            ),
            command_digest="",
        )
        connection = sqlite3.connect(
            harness.bundle["author_fixture"].location.database_path
        )
        try:
            raw_phase = connection.execute(
                "SELECT "
                + ", ".join(c1_rows.PHASE_COLUMNS)
                + " FROM rw0_phase_instances WHERE phase_basis_ref=?",
                (harness.phase_result.phase_basis_ref,),
            ).fetchone()
        finally:
            connection.close()
        assert type(raw_phase) is tuple
        phase_row = c1_rows.rw0_c1_row_value_from_tuple(
            "rw0_phase_instances",
            raw_phase,
        )
        assert runtime._admission_command_matches_phase_preimages(
            original_command,
            phase_row,
        )
        assert not runtime._admission_command_matches_phase_preimages(
            current_state,
            phase_row,
        )
        _assert_conflict(
            harness.writer._admit_rw0_evidence(current_state),
            RW0C1ConflictReasonV1.CURRENT_STATE_CONFLICT,
        )

        missing = RW0C1MemberLocatorV1(
            "authority_observation",
            1,
            "membership.rw0-c1.missing.0001",
            "a" * 64,
            "authority.observation.missing.0001",
            "b" * 64,
        )
        missing_dependency = admission_command(
            harness,
            rank=2,
            value=values_by_rank[2],
            sequence=203,
            dependencies=(missing,),
        )
        _assert_conflict(
            harness.writer._admit_rw0_evidence(missing_dependency),
            RW0C1ConflictReasonV1.MISSING_PREREQUISITE_MEMBER,
        )

        relation_failure = admission_command(
            harness,
            rank=1,
            value=values_by_rank[1],
            sequence=204,
        )
        _assert_conflict(
            harness.writer._admit_rw0_evidence(relation_failure),
            RW0C1ConflictReasonV1.RELATION_FAILURE,
        )

        missing_owners = list(owner_locators(harness, 1))
        missing_owners[0] = replace(
            missing_owners[0],
            row_ref="attempt.fence.missing.0001",
        )
        owner_missing = admission_command(
            harness,
            rank=1,
            value=valid_rank1_value(harness),
            sequence=205,
            owners=tuple(missing_owners),
        )
        _assert_conflict(
            harness.writer._admit_rw0_evidence(owner_missing),
            RW0C1ConflictReasonV1.OWNER_ROW_MISSING,
        )

        foreign_wrapper = replace(
            _rank14_value(
                harness,
                sequence=207,
                result_state="absent",
                classification="unusable",
                reason="result_missing",
            ),
            program_ref="program.foreign.0001",
            value_digest="",
        )
        wrapper_relation_failure = admission_command(
            harness,
            rank=14,
            value=foreign_wrapper,
            sequence=207,
        )
        _assert_conflict(
            harness.writer._admit_rw0_evidence(wrapper_relation_failure),
            RW0C1ConflictReasonV1.RELATION_FAILURE,
        )

        monkeypatch.setattr(
            runtime,
            "_read_relation_by_ref",
            lambda *args, **kwargs: object(),
        )
        monkeypatch.setattr(
            runtime,
            "_validate_rank_relation",
            lambda *args, **kwargs: False,
        )
        relation_collision = admission_command(
            harness,
            rank=1,
            value=valid_rank1_value(harness),
            sequence=206,
        )
        _assert_conflict(
            harness.writer._admit_rw0_evidence(relation_collision),
            RW0C1ConflictReasonV1.RELATION_IDENTITY_COLLISION,
        )
    finally:
        harness.close()


def test_actual_current_state_cas_precedes_registry_and_membership_collision_probes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="admission-cas-precedence")
    evidence_value = _mechanics_values(harness)[5]
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", lambda: OPERATION_TIME)
    try:
        assert type(
            harness.writer._admit_rw0_evidence(
                admission_command(
                    harness,
                    rank=5,
                    value=evidence_value,
                    sequence=220,
                )
            )
        ) is RW0C1AdmitEvidenceResultV1
        stale = admission_command(
            harness,
            rank=5,
            value=evidence_value,
            sequence=221,
        )
        events: list[str] = []

        def stale_actual_state(*_args: object, **_kwargs: object) -> bool:
            events.append("actual_current_state_cas")
            return False

        def forbidden_collision(*_args: object, **_kwargs: object) -> object:
            events.append("collision_probe")
            raise AssertionError("collision probe disclosed before current-state CAS")

        monkeypatch.setattr(
            runtime,
            "_current_state_matches_admission_command",
            stale_actual_state,
        )
        monkeypatch.setattr(
            runtime,
            "_read_registry_by_kind_ref",
            forbidden_collision,
        )
        monkeypatch.setattr(
            runtime,
            "_read_registry_by_kind_digest",
            forbidden_collision,
        )
        _assert_conflict(
            harness.writer._admit_rw0_evidence(stale),
            RW0C1ConflictReasonV1.CURRENT_STATE_CONFLICT,
        )
        assert events == ["actual_current_state_cas"]
    finally:
        harness.close()


@pytest.mark.parametrize(
    "reader_outcome",
    (
        None,
        "database_integrity_failure",
        "mutation_failed",
        "commit_outcome_unknown",
    ),
)
def test_actual_owner_reader_none_is_absence_but_safe_faults_propagate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reader_outcome: str | None,
) -> None:
    harness = make_c1_harness(
        tmp_path,
        suffix=f"owner-reader-{(reader_outcome or 'none').replace('_', '-')}",
    )
    command = admission_command(
        harness,
        rank=5,
        value=_mechanics_values(harness)[5],
        sequence=230,
    )

    if reader_outcome is None:
        monkeypatch.setattr(
            runtime,
            "_read_development_program_head_and_current_version",
            lambda *_a: None,
        )
    else:
        expected_error = SQLiteMutationStoreError(
            SQLiteMutationStoreErrorCode(reader_outcome)
        )

        def failed_reader(*_args: object) -> object:
            raise expected_error

        monkeypatch.setattr(
            runtime,
            "_read_development_program_head_and_current_version",
            failed_reader,
        )
    try:
        if reader_outcome is None:
            _assert_conflict(
                harness.writer._admit_rw0_evidence(command),
                RW0C1ConflictReasonV1.OWNER_ROW_MISSING,
            )
        else:
            with pytest.raises(SQLiteMutationStoreError) as caught:
                harness.writer._admit_rw0_evidence(command)
            assert caught.value.error_class == reader_outcome
            assert caught.value.args == (reader_outcome,)
    finally:
        harness.close()


def test_all_fifteen_kinds_persist_one_member_per_mutation_with_full_readback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="all-kinds")
    owner_calls = _install_counted_owner_relation_seams(monkeypatch)
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", lambda: OPERATION_TIME)
    results: dict[int, RW0C1AdmitEvidenceResultV1] = {}
    values_by_rank = _mechanics_values(harness)
    sequence = 1
    try:
        results[1] = admit(harness, rank=1, value=values_by_rank[1], sequence=sequence)
        sequence += 1
        results[2] = admit(
            harness, rank=2, value=values_by_rank[2], sequence=sequence,
            dependencies=(member_locator(results[1], "authority_observation"),),
        )
        sequence += 1
        results[3] = admit(harness, rank=3, value=values_by_rank[3], sequence=sequence)
        sequence += 1
        results[4] = admit(
            harness, rank=4, value=values_by_rank[4], sequence=sequence,
            dependencies=(
                member_locator(results[1], "authority_observation"),
                member_locator(results[2], "subordinate_proposal"),
                member_locator(results[3], "custody_observation"),
            ),
        )
        sequence += 1
        results[5] = admit(harness, rank=5, value=values_by_rank[5], sequence=sequence)
        sequence += 1
        results[6] = admit(
            harness, rank=6, value=values_by_rank[6], sequence=sequence,
            dependencies=(
                member_locator(results[1], "authority_observation"),
                member_locator(results[5], "remote_host_readiness"),
            ),
        )
        sequence += 1
        results[7] = admit(harness, rank=7, value=values_by_rank[7], sequence=sequence)
        sequence += 1
        results[8] = admit(
            harness, rank=8, value=values_by_rank[8], sequence=sequence,
            dependencies=(member_locator(results[7], "capability_declaration"),),
        )
        sequence += 1
        results[9] = admit(
            harness, rank=9, value=values_by_rank[9], sequence=sequence,
            dependencies=(
                member_locator(results[1], "authority_observation"),
                member_locator(results[5], "remote_host_readiness"),
                member_locator(results[6], "host_qualification"),
                member_locator(results[7], "capability_declaration"),
                member_locator(results[8], "capability_observation"),
            ),
        )
        sequence += 1
        results[10] = admit(harness, rank=10, value=values_by_rank[10], sequence=sequence)
        sequence += 1
        results[11] = admit(harness, rank=11, value=values_by_rank[11], sequence=sequence)
        sequence += 1
        started = worker_observation("worker_started", "observation.c1.started.0001")
        completed = worker_observation("worker_completed", "observation.c1.completed.0001")
        results[12] = admit(harness, rank=12, value=started, sequence=sequence)
        sequence += 1
        completed_result = admit(harness, rank=12, value=completed, sequence=sequence)
        sequence += 1
        observation_locators = (
            member_locator(results[12], "worker_observation:000"),
            member_locator(completed_result, "worker_observation:001"),
        )
        basis = harness.bundle["basis"]
        rank13 = RW0C1WireWorkerResultBindingV1(
            "worker-result.binding.c1.0001", basis.basis_ref, basis.basis_digest,
            basis.c2b3d_lineage.program_ref, basis.c2b3d_lineage.semantic_attempt_ref,
            basis.c2b3d_lineage.candidate_ref, basis.c2b3d_lineage.effect_intent_ref,
            basis.c2b3d_lineage.author_command_ref, basis.c2b3d_lineage.attempt_fence_ref,
            basis.c2b3d_lineage.effect_fence_ref, basis.c2b3d_lineage.delivery_attempt_ref,
            observation_locators,
        )
        results[13] = admit(
            harness, rank=13, value=rank13, sequence=sequence,
            dependencies=observation_locators,
        )
        sequence += 1
        rank14 = RW0C1WireProcessResultClassificationBindingV1(
            "process-result.binding.c1.0001", basis.basis_ref, basis.basis_digest,
            basis.c2b3d_lineage.program_ref, basis.c2b3d_lineage.semantic_attempt_ref,
            basis.c2b3d_lineage.candidate_ref, basis.c2b3d_lineage.effect_intent_ref,
            basis.c2b3d_lineage.author_command_ref, basis.c2b3d_lineage.attempt_fence_ref,
            basis.c2b3d_lineage.effect_fence_ref, basis.c2b3d_lineage.delivery_attempt_ref,
            "absent", None, None, (), None, (), "unusable", "result_missing",
        )
        results[14] = admit(harness, rank=14, value=rank14, sequence=sequence)
        sequence += 1
        rank15_owners, rank15_value = _install_rank15_owner_family(
            harness,
            evidence_binding_count=0,
        )
        results[15] = admit(
            harness,
            rank=15,
            value=rank15_value,
            sequence=sequence,
            owners=rank15_owners,
        )
        assert set(results) == set(range(1, 16))
        assert set(owner_calls) == {
            "rank1_authority",
            "rank2_narrowing",
            "rank3_custody",
            "rank4_retrieval",
            "rank6_host",
            "rank8_capability_observation",
            "rank9_capability_qualification",
            "rank10_cancellation_request",
            "rank11_process",
            "rank12_worker_observation",
            "rank13_worker_result",
            "rank14_process_result_classifier",
            "rank15_section41",
        }
        connection = sqlite3.connect(
            harness.bundle["author_fixture"].location.database_path
        )
        try:
            assert connection.execute(
                "SELECT count(*) FROM rw0_evidence_memberships"
            ).fetchone() == (16,)
            assert connection.execute(
                "SELECT count(DISTINCT kind_rank) FROM rw0_evidence_memberships"
            ).fetchone() == (15,)
            assert connection.execute(
                "SELECT count(*) FROM rw0_c1_mutation_receipts"
            ).fetchone() == (17,)
            assert connection.execute(
                "SELECT count(*) FROM rw0_relation_bindings "
                "WHERE subject_type='evidence_membership'"
            ).fetchone() == (14,)
        finally:
            connection.close()
    finally:
        harness.close()


def test_rank6_and_rank9_temporal_equality_persists_and_earlier_equal_time_reuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    equal_time = "2029-01-01T00:00:00Z"
    later_admission_time = "2030-01-01T00:00:00Z"
    harness = make_c1_harness(
        tmp_path,
        suffix="temporal-equality",
        timestamp=equal_time,
    )
    values_by_rank = _mechanics_values(harness)
    _install_counted_owner_relation_seams(monkeypatch)
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: equal_time,
    )
    try:
        authority = admit(
            harness,
            rank=1,
            value=values_by_rank[1],
            sequence=520,
        )
        readiness = admit(
            harness,
            rank=5,
            value=values_by_rank[5],
            sequence=521,
        )
        host = admit(
            harness,
            rank=6,
            value=values_by_rank[6],
            sequence=522,
            dependencies=(
                member_locator(authority, "authority_observation"),
                member_locator(readiness, "remote_host_readiness"),
            ),
        )
        declaration = admit(
            harness,
            rank=7,
            value=values_by_rank[7],
            sequence=523,
        )
        observation = admit(
            harness,
            rank=8,
            value=values_by_rank[8],
            sequence=524,
            dependencies=(
                member_locator(declaration, "capability_declaration"),
            ),
        )
        qualification_dependencies = (
            member_locator(authority, "authority_observation"),
            member_locator(readiness, "remote_host_readiness"),
            member_locator(host, "host_qualification"),
            member_locator(declaration, "capability_declaration"),
            member_locator(observation, "capability_observation"),
        )
        qualification = admit(
            harness,
            rank=9,
            value=values_by_rank[9],
            sequence=525,
            dependencies=qualification_dependencies,
        )

        connection = sqlite3.connect(
            harness.bundle["author_fixture"].location.database_path
        )
        try:
            assert connection.execute(
                "SELECT m.admitted_at, r.evaluated_at "
                "FROM rw0_evidence_memberships AS m "
                "JOIN rw0_relation_bindings AS r "
                "ON r.subject_membership_ref=m.membership_ref "
                "WHERE m.membership_ref IN (?,?) ORDER BY m.kind_rank",
                (host.membership_ref, qualification.membership_ref),
            ).fetchall() == [(equal_time, equal_time), (equal_time, equal_time)]
        finally:
            connection.close()

        declaration_record = declaration_mapping()
        observation_record = observation_mapping(declaration_record)
        phase = {
            "phase_basis_ref": harness.bundle["basis"].basis_ref,
            "phase_basis_digest": harness.bundle["basis"].basis_digest,
        }
        later_value = capability.RW0WorkerMechanismCapabilityQualificationV1.from_mapping(
            qualification_mapping(
                declaration_record,
                observation_record,
                **phase,
                capability_qualification_ref=(
                    "capability-qualification.safe.temporal-later"
                ),
                evaluated_at=equal_time,
            )
        )
        monkeypatch.setattr(
            transaction,
            "_capture_transaction_timestamp",
            lambda: later_admission_time,
        )
        later = admit(
            harness,
            rank=9,
            value=later_value,
            sequence=526,
            dependencies=qualification_dependencies,
        )
        connection = sqlite3.connect(
            harness.bundle["author_fixture"].location.database_path
        )
        try:
            assert connection.execute(
                "SELECT m.admitted_at, r.evaluated_at "
                "FROM rw0_evidence_memberships AS m "
                "JOIN rw0_relation_bindings AS r "
                "ON r.subject_membership_ref=m.membership_ref "
                "WHERE m.membership_ref=?",
                (later.membership_ref,),
            ).fetchone() == (later_admission_time, equal_time)
        finally:
            connection.close()
    finally:
        harness.close()


@pytest.mark.parametrize("evidence_binding_count", (0, 9))
def test_rank15_causally_wraps_exact_section41_post_execution_family(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    evidence_binding_count: int,
) -> None:
    harness = make_c1_harness(
        tmp_path,
        suffix=f"rank15-section41-{evidence_binding_count}",
    )
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: OPERATION_TIME,
    )
    try:
        owners, wrapped = _install_rank15_owner_family(
            harness,
            evidence_binding_count=evidence_binding_count,
        )
        command = admission_command(
            harness,
            rank=15,
            value=wrapped,
            sequence=300 + evidence_binding_count,
            owners=owners,
        )
        result = harness.writer._admit_rw0_evidence(command)
        assert type(result) is RW0C1AdmitEvidenceResultV1
        replay = harness.writer._admit_rw0_evidence(command)
        assert type(replay) is RW0C1AdmitEvidenceResultV1
        assert replay.disposition == "exact_replay"
        assert replay.committed_projection_digest() == (
            result.committed_projection_digest()
        )

        connection = sqlite3.connect(
            harness.bundle["author_fixture"].location.database_path
        )
        try:
            operands = connection.execute(
                "SELECT o.operand_role, o.owner_role "
                "FROM rw0_relation_operands AS o "
                "JOIN rw0_relation_bindings AS r "
                "ON r.relation_ref=o.relation_ref "
                "WHERE r.subject_membership_ref=? ORDER BY o.operand_ordinal",
                (result.membership_ref,),
            ).fetchall()
            assert tuple(operands[:3]) == (
                (
                    "source_invocation",
                    "development_model_source_invocation",
                ),
                (
                    "artifact_binding",
                    "development_private_proposal_artifact_binding",
                ),
                ("model_proposal", "development_model_proposal"),
            )
            assert len(operands) == 3 + evidence_binding_count
            assert all(role != "safe_projection" for role, _owner in operands)
        finally:
            connection.close()
    finally:
        harness.close()


def test_rank15_rejects_foreign_phase_wrapper_before_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="rank15-foreign-phase")
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: OPERATION_TIME,
    )
    try:
        owners, wrapped = _install_rank15_owner_family(
            harness,
            evidence_binding_count=0,
        )
        foreign = replace(
            wrapped,
            phase_basis_ref="phase.foreign.rank15.0001",
            value_digest="",
        )
        _assert_conflict(
            harness.writer._admit_rw0_evidence(
                admission_command(
                    harness,
                    rank=15,
                    value=foreign,
                    sequence=399,
                    owners=owners,
                )
            ),
            RW0C1ConflictReasonV1.RELATION_FAILURE,
        )
        connection = sqlite3.connect(
            harness.bundle["author_fixture"].location.database_path
        )
        try:
            assert connection.execute(
                "SELECT count(*) FROM rw0_evidence_memberships "
                "WHERE membership_ref='membership.rw0-c1.399'"
            ).fetchone() == (0,)
        finally:
            connection.close()
    finally:
        harness.close()


def test_atomic_controller_fences_plans_writes_reads_back_then_commits_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="controller-order")
    events: list[str] = []
    controller = transaction._CoordinatorMutationTransactionController
    original_fence = controller._run_until_writer_fencing_resolution
    original_resolve = transaction._resolve_rw0_c1_evidence_admission_after_fencing
    original_complete = transaction._complete_rw0_c1_evidence_admission_preparation
    original_probe = transaction._probe_rw0_c1_relation_identity_collisions
    original_readback = transaction._readback_rw0_c1_evidence_admission
    original_commit = controller._commit_after_fresh_writes

    def counted_fence(self: object) -> object:
        events.append("writer_fencing")
        return original_fence(self)

    def counted_resolve(*, capability: object, command: object) -> object:
        events.append("receipt_and_prerequisite_reads")
        return original_resolve(capability=capability, command=command)

    def counted_clock() -> str:
        events.append("operation_clock")
        return OPERATION_TIME

    def counted_complete(
        preparation: object,
        *,
        operation_timestamp: str,
    ) -> object:
        events.append("relation_and_write_plan")
        planned = original_complete(
            preparation,
            operation_timestamp=operation_timestamp,
        )
        assert type(planned) is runtime.RW0C1WritePlan
        assert planned.rows[-1].table_name == "rw0_c1_mutation_receipts"
        return planned

    def counted_probe(*, capability: object, plan: object) -> object:
        events.append("relation_collision_probe")
        return original_probe(capability=capability, plan=plan)

    def counted_readback(*, capability: object, plan: object) -> object:
        events.append("guarded_readback")
        return original_readback(capability=capability, plan=plan)

    def counted_commit(
        self: object,
        planned_result: object,
        *,
        force_cleanup_on_uncertainty: bool = False,
    ) -> object:
        events.append("commit_attempt")
        return original_commit(
            self,
            planned_result,
            force_cleanup_on_uncertainty=force_cleanup_on_uncertainty,
        )

    monkeypatch.setattr(
        controller,
        "_run_until_writer_fencing_resolution",
        counted_fence,
    )
    monkeypatch.setattr(
        transaction,
        "_resolve_rw0_c1_evidence_admission_after_fencing",
        counted_resolve,
    )
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", counted_clock)
    monkeypatch.setattr(
        transaction,
        "_complete_rw0_c1_evidence_admission_preparation",
        counted_complete,
    )
    monkeypatch.setattr(
        transaction,
        "_probe_rw0_c1_relation_identity_collisions",
        counted_probe,
    )
    monkeypatch.setattr(
        transaction,
        "_readback_rw0_c1_evidence_admission",
        counted_readback,
    )
    monkeypatch.setattr(controller, "_commit_after_fresh_writes", counted_commit)
    try:
        result = harness.writer._admit_rw0_evidence(
            admission_command(
                harness,
                rank=5,
                value=_mechanics_values(harness)[5],
                sequence=250,
            )
        )
        assert type(result) is RW0C1AdmitEvidenceResultV1
        assert events == [
            "writer_fencing",
            "receipt_and_prerequisite_reads",
            "operation_clock",
            "relation_and_write_plan",
            "relation_collision_probe",
            "guarded_readback",
            "commit_attempt",
        ]
    finally:
        harness.close()


def test_cancellation_response_and_all_rank14_branches_persist_exact_closure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="branch-closure")
    owner_calls = _install_counted_owner_relation_seams(monkeypatch)
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", lambda: OPERATION_TIME)
    values_by_rank = _mechanics_values(harness)
    try:
        request = admit(
            harness,
            rank=10,
            value=values_by_rank[10],
            sequence=301,
        )
        response_owners = (
            *owner_locators(harness, 12),
            _owner_locator(
                "cancellation_effect_fence",
                "development_effect_fence",
                harness.bundle["author_effect_fence"],
                ref_name="effect_fence_ref",
                digest_name="effect_fence_digest",
            ),
            _owner_locator(
                "cancellation_delivery",
                "development_delivery_attempt",
                harness.delivery_row,
                ref_name="delivery_attempt_ref",
                digest_name="delivery_attempt_digest",
            ),
        )
        response = admit(
            harness,
            rank=12,
            value=adapter_observation(
                "cancellation_acknowledged",
                "observation.c1.cancellation-acknowledged.0001",
            ),
            sequence=302,
            dependencies=(member_locator(request, "cancellation_request"),),
            owners=response_owners,
        )

        started = admit(
            harness,
            rank=12,
            value=worker_observation(
                "worker_started",
                "observation.c1.rank14-started.0001",
            ),
            sequence=303,
        )
        completed = admit(
            harness,
            rank=12,
            value=worker_observation(
                "worker_completed",
                "observation.c1.rank14-completed.0001",
            ),
            sequence=304,
        )
        worker_observations = (
            member_locator(started, "worker_observation:000"),
            member_locator(completed, "worker_observation:001"),
        )
        basis = harness.bundle["basis"]
        lineage = basis.c2b3d_lineage
        worker_result_value = RW0C1WireWorkerResultBindingV1(
            "worker-result.binding.c1.branch-closure.0001",
            basis.basis_ref,
            basis.basis_digest,
            lineage.program_ref,
            lineage.semantic_attempt_ref,
            lineage.candidate_ref,
            lineage.effect_intent_ref,
            lineage.author_command_ref,
            lineage.attempt_fence_ref,
            lineage.effect_fence_ref,
            lineage.delivery_attempt_ref,
            worker_observations,
        )
        worker_result = admit(
            harness,
            rank=13,
            value=worker_result_value,
            sequence=305,
            dependencies=worker_observations,
        )
        result_locator = member_locator(worker_result, "worker_result_binding")
        adapter_observations = (
            member_locator(started, "adapter_observation:000"),
            member_locator(completed, "adapter_observation:001"),
        )
        present_value = _rank14_value(
            harness,
            sequence=1,
            result_state="present",
            result_membership=result_locator,
            adapter_observations=adapter_observations,
            classification="usable",
            reason="usable",
        )
        present = admit(
            harness,
            rank=14,
            value=present_value,
            sequence=306,
            dependencies=(result_locator, *adapter_observations),
        )

        with pytest.raises(wire.RW0WireProtocolError) as caught:
            wire._raise_public("short_header")
        sealed_failure = caught.value
        failure_binding = RW0C1TransientPrivateBindingV1.wire_protocol_error(
            role="worker_result_failure",
            value=sealed_failure,
        )
        finite_value = _rank14_value(
            harness,
            sequence=2,
            result_state="finite_failure",
            result_failure_reason=sealed_failure.reason,
            classification="unusable",
            reason="result_invalid",
        )
        finite = admit(
            harness,
            rank=14,
            value=finite_value,
            sequence=307,
            transients=(failure_binding,),
        )
        absent_value = _rank14_value(
            harness,
            sequence=3,
            result_state="absent",
            classification="unusable",
            reason="result_missing",
        )
        absent = admit(
            harness,
            rank=14,
            value=absent_value,
            sequence=308,
        )

        connection = sqlite3.connect(
            harness.bundle["author_fixture"].location.database_path
        )
        try:
            assert connection.execute(
                "SELECT relation_rank, proof_mode FROM rw0_relation_bindings "
                "WHERE subject_membership_ref=? ORDER BY relation_rank",
                (response.membership_ref,),
            ).fetchall() == [
                (0, "relation_recomputable"),
                (1, "relation_attested_at_admission"),
            ]
            assert connection.execute(
                "SELECT result_state, result_membership_ref, "
                "result_failure_reason FROM "
                "rw0_wire_process_result_classification_bindings "
                "ORDER BY result_state"
            ).fetchall() == [
                ("absent", None, None),
                ("finite_failure", None, "short_header"),
                ("present", worker_result.membership_ref, None),
            ]
            proof_by_membership = dict(
                connection.execute(
                    "SELECT subject_membership_ref, proof_mode "
                    "FROM rw0_relation_bindings "
                    "WHERE subject_membership_ref IN (?,?,?)",
                    (
                        present.membership_ref,
                        finite.membership_ref,
                        absent.membership_ref,
                    ),
                ).fetchall()
            )
            assert proof_by_membership == {
                present.membership_ref: "derived_wrapper_recomputable",
                finite.membership_ref: "relation_attested_at_admission",
                absent.membership_ref: "derived_wrapper_recomputable",
            }
            assert {
                "rank10_cancellation_request",
                "rank12_worker_observation",
                "rank12_cancellation_response",
                "rank13_worker_result",
                "rank14_process_result_classifier",
            }.issubset(owner_calls)
        finally:
            connection.close()
    finally:
        harness.close()


def test_rank14_present_reconstructs_the_admitted_rank13_worker_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="rank14-present-owner")
    monkeypatch.setattr(
        transaction,
        "_capture_transaction_timestamp",
        lambda: OPERATION_TIME,
    )
    bundle = harness.bundle

    def phase_observation(kind: str, reference: str) -> WorkerObservationV1:
        return WorkerObservationV1.create(
            observation_ref=reference,
            source_kind="worker",
            source_ref="worker.c1.rank14-owner.0001",
            source_invocation_ref="invocation.c1.rank14-owner.0001",
            observation_kind=kind,
            outcome={
                "worker_started": "started",
                "worker_completed": "completed",
            }[kind],
            reason_code="reason.none",
            evidence_refs=["evidence.c1.rank14-owner.0001"],
            observed_at="2028-01-01T00:00:00Z",
            delivery=bundle["author_delivery"],
            author_command=bundle["author_command"],
            attempt_fence=bundle["attempt_fence"],
            author_effect_fence=bundle["author_effect_fence"],
            effect_fence=bundle["author_effect_fence"],
        )

    try:
        started = admit(
            harness,
            rank=12,
            value=phase_observation(
                "worker_started",
                "observation.c1.rank14-owner-started.0001",
            ),
            sequence=351,
        )
        completed = admit(
            harness,
            rank=12,
            value=phase_observation(
                "worker_completed",
                "observation.c1.rank14-owner-completed.0001",
            ),
            sequence=352,
        )
        exited = admit(
            harness,
            rank=12,
            value=WorkerObservationV1.create(
                observation_ref="observation.c1.rank14-owner-exited.0001",
                source_kind="direct_local_adapter",
                source_ref="adapter.c1.rank14-owner.0001",
                source_invocation_ref="adapter-invocation.c1.rank14-owner.0001",
                observation_kind="process_exited",
                outcome="exited",
                reason_code="reason.none",
                evidence_refs=["evidence.c1.rank14-owner.0002"],
                observed_at="2028-01-01T00:00:01Z",
                delivery=bundle["author_delivery"],
                author_command=bundle["author_command"],
                attempt_fence=bundle["attempt_fence"],
                author_effect_fence=bundle["author_effect_fence"],
                effect_fence=bundle["author_effect_fence"],
                process_exit_code=0,
            ),
            sequence=353,
        )
        observation_locators = (
            member_locator(started, "worker_observation:000"),
            member_locator(completed, "worker_observation:001"),
        )
        basis = harness.bundle["basis"]
        lineage = basis.c2b3d_lineage
        worker_result = admit(
            harness,
            rank=13,
            value=RW0C1WireWorkerResultBindingV1(
                "worker-result.binding.c1.rank14-owner.0001",
                basis.basis_ref,
                basis.basis_digest,
                lineage.program_ref,
                lineage.semantic_attempt_ref,
                lineage.candidate_ref,
                lineage.effect_intent_ref,
                lineage.author_command_ref,
                lineage.attempt_fence_ref,
                lineage.effect_fence_ref,
                lineage.delivery_attempt_ref,
                observation_locators,
            ),
            sequence=354,
            dependencies=observation_locators,
        )
        result_locator = member_locator(worker_result, "worker_result_binding")
        adapter_locator = member_locator(exited, "adapter_observation:000")
        classified = admit(
            harness,
            rank=14,
            value=_rank14_value(
                harness,
                sequence=4,
                result_state="present",
                result_membership=result_locator,
                adapter_observations=(adapter_locator,),
                classification="usable",
                reason="usable",
            ),
            sequence=355,
            dependencies=(result_locator, adapter_locator),
        )
        assert classified.kind_rank == 14
    finally:
        harness.close()


def test_capability_observation_structural_relation_is_invoked_and_replayed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="capability-relation")
    values_by_rank = _mechanics_values(harness)
    calls: list[tuple[object, object]] = []
    original = runtime._validate_capability_observation_binding

    def counted(declaration: object, observation: object) -> None:
        calls.append((declaration, observation))
        original(declaration, observation)

    monkeypatch.setattr(
        runtime,
        "_validate_capability_observation_binding",
        counted,
    )
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", lambda: OPERATION_TIME)
    try:
        declaration = admit(
            harness,
            rank=7,
            value=values_by_rank[7],
            sequence=101,
        )
        command = admission_command(
            harness,
            rank=8,
            value=values_by_rank[8],
            sequence=102,
            dependencies=(member_locator(declaration, "capability_declaration"),),
        )
        fresh = harness.writer._admit_rw0_evidence(command)
        assert type(fresh) is RW0C1AdmitEvidenceResultV1
        assert fresh.disposition == "fresh_committed"
        assert len(calls) == 2

        monkeypatch.setattr(
            transaction,
            "_capture_transaction_timestamp",
            lambda: (_ for _ in ()).throw(AssertionError("replay captured a clock")),
        )
        replay = harness.writer._admit_rw0_evidence(command)
        assert type(replay) is RW0C1AdmitEvidenceResultV1
        assert replay.disposition == "exact_replay"
        assert replay.committed_at == fresh.committed_at
        assert len(calls) == 3
        assert all(pair == (values_by_rank[7], values_by_rank[8]) for pair in calls)
    finally:
        harness.close()


def test_c1_runtime_owns_no_connection_clock_or_external_io() -> None:
    source = Path(runtime.__file__).read_text(encoding="utf-8")
    assert "import sqlite3" not in source
    assert "sqlite3.connect" not in source
    assert "BEGIN IMMEDIATE" not in source
    assert ".commit(" not in source
    assert "subprocess" not in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "import urllib" not in source
    assert "from urllib" not in source
