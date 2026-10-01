from __future__ import annotations

import pytest

import ge_nwp_coordinator._rw0_c1_mutation_contracts as contracts
from ge_nwp_coordinator._rw0_c1_semantic_values import (
    RW0C1MemberLocatorV1,
    RW0C1PreflightError,
    RW0C1RecoveryDispositionV1,
    RW0C1RecoveryResultV1,
)
from test_rw0_b1_relations import claims


def test_commit_close_witness_is_monotonic_one_shot_and_nonreusable() -> None:
    witness = contracts._RW0C1CommitCloseWitness()
    assert witness.state == "precommit"
    assert witness.ordinary_failure_is_commit_uncertain is False
    witness._claim_controller()
    witness._mark_commit_attempt_started()
    assert witness.state == "commit_attempt_started"
    assert witness.ordinary_failure_is_commit_uncertain is True
    witness._mark_commit_returned_success()
    assert witness.state == "commit_returned_success"
    witness._mark_close_proof_complete()
    assert witness.state == "close_proof_complete"
    assert witness.ordinary_failure_is_commit_uncertain is True
    with pytest.raises(ValueError):
        witness._claim_controller()
    with pytest.raises(ValueError):
        witness._mark_commit_attempt_started()


def test_precommit_replay_close_witness_completes_without_commit_attempt() -> None:
    witness = contracts._RW0C1CommitCloseWitness()
    witness._claim_controller()
    witness._mark_close_proof_complete()
    assert witness.state == "close_proof_complete"
    assert witness.ordinary_failure_is_commit_uncertain is False


def test_recovery_close_witness_retains_unresolved_normalization_through_close() -> None:
    witness = contracts._RW0C1RecoveryCloseWitness()
    result = RW0C1RecoveryResultV1(
        "admit_rw0_evidence",
        "mutation.rw0-c1.recovery-close",
        "a" * 64,
        RW0C1RecoveryDispositionV1.COMMITTED_EXACT,
        "b" * 64,
        "c" * 64,
        "d" * 64,
    )
    assert witness.result_computed is False
    witness._claim_controller()
    witness._mark_result_computed(result)
    assert witness.result_computed is True
    witness._mark_close_proof_complete()
    assert witness.result_computed is True
    unresolved = witness._unresolved_result()
    assert unresolved.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
    assert unresolved.mutation_ref == result.mutation_ref
    with pytest.raises(ValueError):
        witness._claim_controller()
    with pytest.raises(ValueError):
        witness._mark_result_computed(result)
    with pytest.raises(ValueError):
        witness._mark_close_proof_complete()


def test_k8_order_and_phase_identity_are_exact() -> None:
    basis, *_rest = claims()
    mapping = contracts.k8_mapping_from_phase_basis(basis)
    assert tuple(mapping) == (
        "program_ref", "semantic_attempt_ref", "candidate_ref",
        "effect_intent_ref", "author_command_ref", "attempt_fence_ref",
        "effect_fence_ref", "delivery_attempt_ref",
    )
    assert len(contracts.k8_digest_from_phase_basis(basis)) == 64
    assert contracts.relation_reference(
        phase_basis_ref=basis.basis_ref,
        phase_basis_digest=basis.basis_digest,
        subject_type="phase_establishment",
        subject_membership_ref=None,
        relation_rank=0,
    ) == f"rw0-c1-phase-relation.{basis.basis_digest}"


def test_relation_inventory_cardinality_proof_modes_and_profiles_are_closed() -> None:
    assert set(contracts._RELATION_SPECS) == set(range(1, 16))
    assert contracts.relation_specifications(kind_rank=5) == ()
    assert contracts.relation_specifications(kind_rank=7) == ()
    ordinary = contracts.relation_specifications(kind_rank=12)
    response = contracts.relation_specifications(
        kind_rank=12, cancellation_response=True
    )
    assert len(ordinary) == 1 and len(response) == 2
    assert response[1].relation_rank == 1
    assert response[1].proof_mode == "relation_attested_at_admission"
    assert contracts.relation_specifications(
        kind_rank=14, rank14_result_state="present"
    )[0].proof_mode == "derived_wrapper_recomputable"
    assert contracts.relation_specifications(
        kind_rank=14, rank14_result_state="finite_failure"
    )[0].proof_mode == "relation_attested_at_admission"


def test_dependency_dag_requires_exact_roles_and_same_kind_sequence() -> None:
    locator = RW0C1MemberLocatorV1(
        "authority_observation", 1, "membership.authority.0001", "a" * 64,
        "authority.observation.0001", "b" * 64,
    )
    contracts.validate_dependency_locators(
        kind_rank=2, evidence_value=object(), locators=(locator,)
    )
    wrong = RW0C1MemberLocatorV1(
        "wrong_role", 1, locator.membership_ref, locator.membership_digest,
        locator.value_ref, locator.value_digest,
    )
    with pytest.raises(RW0C1PreflightError) as caught:
        contracts.validate_dependency_locators(
            kind_rank=2, evidence_value=object(), locators=(wrong,)
        )
    assert caught.value.reason == "invalid_command"


def test_operand_relation_and_set_digests_require_dense_bounded_identity() -> None:
    operand = contracts.RW0C1OperandIdentity(
        0, "authority_observation", "c1_evidence",
        "membership.authority.0001", "a" * 64, 1,
        None, None, None, None, None, None, None, None,
        "governed-execution.nwp-rw0-authority-verification-observation.v1",
        "authority.observation.0001", "b" * 64, "c" * 64,
    )
    digest = contracts.operand_set_digest(
        phase_basis_ref="phase.safe.0001",
        relation_ref="relation.safe.0001",
        operands=(operand,),
    )
    assert len(digest) == 64
    relation_set = contracts.relation_set_digest(
        phase_basis_ref="phase.safe.0001",
        subject_type="evidence_membership",
        subject_ref="membership.safe.0001",
        relations=((0, "relation.safe.0001", "d" * 64),),
    )
    assert len(relation_set) == 64
    with pytest.raises(RW0C1PreflightError):
        contracts.relation_set_digest(
            phase_basis_ref="phase.safe.0001",
            subject_type="evidence_membership",
            subject_ref="membership.safe.0001",
            relations=((1, "relation.safe.0001", "d" * 64),),
        )


def test_insert_inventory_is_exact_and_parameterized() -> None:
    assert tuple(item.table_name for item in contracts.INSERT_SPECIFICATIONS) == tuple(
        item.table_name for item in contracts.ROW_SPECS
    )
    assert all(
        item.sql.startswith(f"INSERT INTO {item.table_name} (")
        and item.sql.count("?") == len(item.columns)
        for item in contracts.INSERT_SPECIFICATIONS
    )
