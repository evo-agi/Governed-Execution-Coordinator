"""Private C1 exact checked readback after a real guarded admission."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sqlite3

import pytest

import ge_nwp_coordinator.sqlite_transition_transaction as transaction
from ge_nwp_coordinator._sqlite_rw0_c1 import RW0C1CheckedEvidenceFamilyV1
from ge_nwp_coordinator._development_author_effect_establishment_contracts import (
    _development_author_effect_establishment_write_plan,
)
from ge_nwp_coordinator._development_bound_effect_establishment_contracts import (
    _development_bound_effect_establishment_write_plan,
)
from ge_nwp_coordinator._rw0_c1_semantic_values import (
    RW0C1AdmitEvidenceCommandV1, RW0C1AdmitEvidenceResultV1,
    RW0C1MemberLocatorV1, RW0C1OwnerRowLocatorV1,
    RW0C1TransientPrivateBindingV1,
    RW0C1WireProcessResultClassificationBindingV1,
    RW0C1WireWorkerResultBindingV1,
)
from ge_nwp_coordinator._rw0_d2a_evidence import (
    artificial_authority_observation, artificial_host_qualification,
    artificial_readiness_observation,
)
from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture, run_rw0_d1_offline
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_rw0_d1_offline_integration import work_spec
from test_rw0_d2_bound_effect_contracts import _bound_command
from test_rw0_c1_private_atomic_persistence import (
    OPERATION_TIME, _mechanics_values, admit, make_c1_harness,
)


def test_checked_family_readback_reconstructs_actual_rank_five(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="d2-checked-rank5")
    monkeypatch.setattr(transaction, "_capture_transaction_timestamp", lambda: OPERATION_TIME)
    try:
        admitted = admit(harness, rank=5, value=_mechanics_values(harness)[5], sequence=1)
        checked = harness.writer._read_rw0_c1_checked_family(admitted)
        assert type(checked) is RW0C1CheckedEvidenceFamilyV1
        assert checked.admission_result.membership_ref == admitted.membership_ref
        assert checked.evidence_value.to_mapping() == _mechanics_values(harness)[5].to_mapping()
        checked.validate()
        with pytest.raises(SQLiteMutationStoreError):
            harness.writer._read_rw0_c1_checked_family(
                replace(admitted, receipt_digest="0" * 64, result_digest="")
            )
    finally:
        harness.close()


def test_actual_d1_observation_admits_after_both_bound_effects() -> None:
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as run:
        bound_commands = {}
        bound_plans = {}
        for kind in ("validate_candidate", "review_candidate"):
            command = _bound_command(run.handback, work, kind)
            with acquire_sqlite_writer_session(run.location) as writer:
                result = writer._establish_development_bound_effect_intent(command)
                assert result.disposition == "committed"
            bound_commands[kind] = command
            bound_plans[kind] = _development_bound_effect_establishment_write_plan(
                command, result.transaction_timestamp,
            )
        author = run.handback.author_command
        plan = _development_author_effect_establishment_write_plan(
            author, run.handback.author_result.transaction_timestamp,
        )
        connection = sqlite3.connect(run.location.database_path)
        try:
            program_revision, program_digest = connection.execute(
                "SELECT head_revision, head_digest FROM development_program_heads WHERE program_ref=?",
                (work.program_ref,),
            ).fetchone()
            work_revision, work_digest = connection.execute(
                "SELECT head_revision, head_digest FROM development_work_item_heads WHERE work_item_ref=?",
                (work.work_item_ref,),
            ).fetchone()
        finally:
            connection.close()
        owners = (
            RW0C1OwnerRowLocatorV1(
                "target_delivery", "development_delivery_attempt",
                plan.delivery_attempt.delivery_attempt_ref,
                plan.delivery_attempt.delivery_attempt_digest,
            ),
            RW0C1OwnerRowLocatorV1(
                "author_command", "development_author_command",
                plan.author_command.command_ref, plan.author_command.command_digest,
            ),
            RW0C1OwnerRowLocatorV1(
                "attempt_fence", "development_attempt_fence",
                plan.attempt_fence.attempt_fence_ref,
                plan.attempt_fence.attempt_fence_digest,
            ),
            RW0C1OwnerRowLocatorV1(
                "author_effect_fence", "development_effect_fence",
                plan.effect_fence.effect_fence_ref, plan.effect_fence.effect_fence_digest,
            ),
            RW0C1OwnerRowLocatorV1(
                "target_effect_fence", "development_effect_fence",
                plan.effect_fence.effect_fence_ref, plan.effect_fence.effect_fence_digest,
            ),
        )
        observed = run.handback.wire_result.observations[0]
        with acquire_sqlite_writer_session(run.location) as writer:
            observed_results = []
            for index, observation in enumerate(run.handback.wire_result.observations):
                command = RW0C1AdmitEvidenceCommandV1(
                    mutation_ref=f"mutation.d2.admit.worker.{index}",
                    phase_basis_ref=run.handback.phase_basis.basis_ref,
                    phase_basis_digest=run.handback.phase_basis.basis_digest,
                    expected_program_head_revision=program_revision,
                    expected_program_head_digest=program_digest,
                    expected_work_item_head_revision=work_revision,
                    expected_work_item_head_digest=work_digest,
                    preassigned_membership_ref=f"membership.d2.worker.{index}",
                    kind_rank=12, evidence_value=observation,
                    owner_row_locators=owners,
                )
                result = writer._admit_rw0_evidence(command)
                assert type(result) is RW0C1AdmitEvidenceResultV1, result.safe_projection()
                checked = writer._read_rw0_c1_checked_family(result)
                assert checked.evidence_value.to_mapping() == observation.to_mapping()
                observed_results.append(result)
            adapter_command = RW0C1AdmitEvidenceCommandV1(
                mutation_ref="mutation.d2.admit.adapter",
                phase_basis_ref=run.handback.phase_basis.basis_ref,
                phase_basis_digest=run.handback.phase_basis.basis_digest,
                expected_program_head_revision=program_revision,
                expected_program_head_digest=program_digest,
                expected_work_item_head_revision=work_revision,
                expected_work_item_head_digest=work_digest,
                preassigned_membership_ref="membership.d2.adapter",
                kind_rank=12, evidence_value=run.handback.adapter_exit,
                owner_row_locators=owners,
            )
            adapter_result = writer._admit_rw0_evidence(adapter_command)
            assert type(adapter_result) is RW0C1AdmitEvidenceResultV1, adapter_result.safe_projection()
            assert writer._read_rw0_c1_checked_family(adapter_result).evidence_value.to_mapping() == run.handback.adapter_exit.to_mapping()
            basis = run.handback.phase_basis
            lineage = basis.c2b3d_lineage
            worker_locators = tuple(
                RW0C1MemberLocatorV1(
                    f"worker_observation:{index:03d}", 12,
                    item.membership_ref, item.membership_digest,
                    item.value_ref, item.value_digest,
                ) for index, item in enumerate(observed_results)
            )
            result_owners = (
                owners[1],
                RW0C1OwnerRowLocatorV1(
                    "author_delivery", "development_delivery_attempt",
                    plan.delivery_attempt.delivery_attempt_ref,
                    plan.delivery_attempt.delivery_attempt_digest,
                ),
                owners[2], owners[3],
            )
            worker_binding = RW0C1WireWorkerResultBindingV1(
                "worker-result.d2", basis.basis_ref, basis.basis_digest,
                lineage.program_ref, lineage.semantic_attempt_ref,
                lineage.candidate_ref, lineage.effect_intent_ref,
                lineage.author_command_ref, lineage.attempt_fence_ref,
                lineage.effect_fence_ref, lineage.delivery_attempt_ref,
                worker_locators,
            )
            worker_binding_command = RW0C1AdmitEvidenceCommandV1(
                mutation_ref="mutation.d2.admit.worker-result",
                phase_basis_ref=basis.basis_ref, phase_basis_digest=basis.basis_digest,
                expected_program_head_revision=program_revision,
                expected_program_head_digest=program_digest,
                expected_work_item_head_revision=work_revision,
                expected_work_item_head_digest=work_digest,
                preassigned_membership_ref="membership.d2.worker-result",
                kind_rank=13, evidence_value=worker_binding,
                prerequisite_member_locators=worker_locators,
                owner_row_locators=result_owners,
            )
            worker_result = writer._admit_rw0_evidence(worker_binding_command)
            assert type(worker_result) is RW0C1AdmitEvidenceResultV1, worker_result.safe_projection()
            assert writer._read_rw0_c1_checked_family(worker_result).evidence_value.to_mapping() == worker_binding.to_mapping()
            worker_locator = RW0C1MemberLocatorV1(
                "worker_result_binding", 13, worker_result.membership_ref,
                worker_result.membership_digest, worker_result.value_ref,
                worker_result.value_digest,
            )
            adapter_locator = RW0C1MemberLocatorV1(
                "adapter_observation:000", 12, adapter_result.membership_ref,
                adapter_result.membership_digest, adapter_result.value_ref,
                adapter_result.value_digest,
            )
            classification_binding = RW0C1WireProcessResultClassificationBindingV1(
                "process-result.d2", basis.basis_ref, basis.basis_digest,
                lineage.program_ref, lineage.semantic_attempt_ref,
                lineage.candidate_ref, lineage.effect_intent_ref,
                lineage.author_command_ref, lineage.attempt_fence_ref,
                lineage.effect_fence_ref, lineage.delivery_attempt_ref,
                "present", worker_locator, None, (adapter_locator,), None, (),
                run.handback.wire_classification.classification,
                run.handback.wire_classification.reason,
            )
            classification_command = RW0C1AdmitEvidenceCommandV1(
                mutation_ref="mutation.d2.admit.process-result",
                phase_basis_ref=basis.basis_ref, phase_basis_digest=basis.basis_digest,
                expected_program_head_revision=program_revision,
                expected_program_head_digest=program_digest,
                expected_work_item_head_revision=work_revision,
                expected_work_item_head_digest=work_digest,
                preassigned_membership_ref="membership.d2.process-result",
                kind_rank=14, evidence_value=classification_binding,
                prerequisite_member_locators=(worker_locator, adapter_locator),
                owner_row_locators=result_owners,
            )
            classification_result = writer._admit_rw0_evidence(classification_command)
            assert type(classification_result) is RW0C1AdmitEvidenceResultV1, classification_result.safe_projection()
            assert writer._read_rw0_c1_checked_family(classification_result).evidence_value.to_mapping() == classification_binding.to_mapping()
            bound = bound_commands["validate_candidate"]
            bound_plan = bound_plans["validate_candidate"]
            authority = artificial_authority_observation(
                basis=run.handback.phase_basis,
                author_command=author,
                current_effect_fence=bound.effect_fence,
                capsule_manifest=run.handback.capsule_manifest,
                source_suffix="validation",
            )
            authority_owners = (
                RW0C1OwnerRowLocatorV1(
                    "attempt_fence", "development_attempt_fence",
                    plan.attempt_fence.attempt_fence_ref,
                    plan.attempt_fence.attempt_fence_digest,
                ),
                RW0C1OwnerRowLocatorV1(
                    "author_effect_fence", "development_effect_fence",
                    plan.effect_fence.effect_fence_ref, plan.effect_fence.effect_fence_digest,
                ),
                RW0C1OwnerRowLocatorV1(
                    "current_effect_fence", "development_effect_fence",
                    bound_plan.effect_fence.effect_fence_ref,
                    bound_plan.effect_fence.effect_fence_digest,
                ),
                RW0C1OwnerRowLocatorV1(
                    "author_command", "development_author_command",
                    plan.author_command.command_ref, plan.author_command.command_digest,
                ),
            )
            authority_command = RW0C1AdmitEvidenceCommandV1(
                mutation_ref="mutation.d2.admit.validation-authority",
                phase_basis_ref=run.handback.phase_basis.basis_ref,
                phase_basis_digest=run.handback.phase_basis.basis_digest,
                expected_program_head_revision=program_revision,
                expected_program_head_digest=program_digest,
                expected_work_item_head_revision=work_revision,
                expected_work_item_head_digest=work_digest,
                preassigned_membership_ref="membership.d2.validation-authority",
                kind_rank=1, evidence_value=authority,
                owner_row_locators=authority_owners,
                transient_bindings=(RW0C1TransientPrivateBindingV1.candidate_capsule_manifest(
                    role="target_capsule_manifest", value=run.handback.capsule_manifest,
                ),),
            )
            authority_result = writer._admit_rw0_evidence(authority_command)
            assert type(authority_result) is RW0C1AdmitEvidenceResultV1, authority_result.safe_projection()
            assert writer._read_rw0_c1_checked_family(authority_result).evidence_value.to_mapping() == authority.to_mapping()
            readiness = artificial_readiness_observation()
            readiness_command = RW0C1AdmitEvidenceCommandV1(
                mutation_ref="mutation.d2.admit.readiness",
                phase_basis_ref=run.handback.phase_basis.basis_ref,
                phase_basis_digest=run.handback.phase_basis.basis_digest,
                expected_program_head_revision=program_revision,
                expected_program_head_digest=program_digest,
                expected_work_item_head_revision=work_revision,
                expected_work_item_head_digest=work_digest,
                preassigned_membership_ref="membership.d2.readiness",
                kind_rank=5, evidence_value=readiness,
            )
            readiness_result = writer._admit_rw0_evidence(readiness_command)
            assert type(readiness_result) is RW0C1AdmitEvidenceResultV1, readiness_result.safe_projection()
            assert writer._read_rw0_c1_checked_family(readiness_result).evidence_value.to_mapping() == readiness.to_mapping()
            qualification = artificial_host_qualification(
                basis=run.handback.phase_basis, authority=authority,
                readiness=readiness, current_effect_fence=bound.effect_fence,
            )
            qualification_command = RW0C1AdmitEvidenceCommandV1(
                mutation_ref="mutation.d2.admit.validation-qualification",
                phase_basis_ref=run.handback.phase_basis.basis_ref,
                phase_basis_digest=run.handback.phase_basis.basis_digest,
                expected_program_head_revision=program_revision,
                expected_program_head_digest=program_digest,
                expected_work_item_head_revision=work_revision,
                expected_work_item_head_digest=work_digest,
                preassigned_membership_ref="membership.d2.validation-qualification",
                kind_rank=6, evidence_value=qualification,
                owner_row_locators=(authority_owners[2],),
                prerequisite_member_locators=(
                    RW0C1MemberLocatorV1(
                        "authority_observation", 1,
                        authority_result.membership_ref, authority_result.membership_digest,
                        authority_result.value_ref, authority_result.value_digest,
                    ),
                    RW0C1MemberLocatorV1(
                        "remote_host_readiness", 5,
                        readiness_result.membership_ref, readiness_result.membership_digest,
                        readiness_result.value_ref, readiness_result.value_digest,
                    ),
                ),
            )
            qualified_result = writer._admit_rw0_evidence(qualification_command)
            assert type(qualified_result) is RW0C1AdmitEvidenceResultV1, qualified_result.safe_projection()
            assert writer._read_rw0_c1_checked_family(qualified_result).evidence_value.to_mapping() == qualification.to_mapping()
