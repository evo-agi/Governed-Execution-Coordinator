"""A runs inside the guarded owner transaction with one commit attempt."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import sqlite3

import pytest

import ge_nwp_coordinator._sqlite_rw0_c1 as c1_reader
import ge_nwp_coordinator._sqlite_section41_post_execution_proposal as store
import ge_nwp_coordinator.sqlite_transition_transaction as transaction
from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture
from ge_nwp_coordinator._rw0_d2_offline import run_rw0_d2_offline
from ge_nwp_coordinator._rw0_d2_post_execution_continuation import prepare_record_command
from ge_nwp_coordinator._section41_post_execution_proposal_mutation_contracts import (
    checked_safe_basis_bytes, safe_basis_digest,
)
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError, SQLiteMutationStoreErrorCode,
)
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_rw0_d1_offline_integration import work_spec
from test_rw0_d2_post_execution_admission_integration import (
    _advance_program_head_in_test_database, _counts,
)


def test_precommit_receipt_insert_failure_rolls_back_all_a_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, safe = prepare_record_command(run)
        original = store._insert
        reached = []

        def fail_receipt(connection: sqlite3.Connection, table: str,
                         columns: tuple[str, ...], values: tuple[object, ...]) -> None:
            if table == "development_post_execution_proposal_receipts":
                reached.append(True)
                raise SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)
            original(connection, table, columns, values)

        monkeypatch.setattr(store, "_insert", fail_receipt)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as caught:
                writer._record_post_execution_proposal(command, run, safe)
        assert reached and caught.value.error_class == "mutation_failed"
        assert _counts(run, command.proposal_ref) == (0, 0, 0, 0, 0)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            assert writer._recover_post_execution_proposal(command).classification == (
                "definitely_not_committed"
            )


@pytest.mark.parametrize("after_underlying_commit", [False, True])
def test_one_commit_call_and_read_only_recovery_classifies_real_a_transaction(
    monkeypatch: pytest.MonkeyPatch, after_underlying_commit: bool,
) -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, safe = prepare_record_command(run)
        original = transaction._commit_transaction
        calls = []

        def fail_at_commit(connection: sqlite3.Connection) -> object:
            calls.append(True)
            if after_underlying_commit:
                original(connection)
            raise sqlite3.OperationalError("synthetic_commit_lost_return")

        monkeypatch.setattr(transaction, "_commit_transaction", fail_at_commit)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as caught:
                writer._record_post_execution_proposal(command, run, safe)
        assert caught.value.error_class == "commit_outcome_unknown"
        assert len(calls) == 1
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            recovery = writer._recover_post_execution_proposal(command)
        assert recovery.classification == (
            "committed_exact" if after_underlying_commit
            else "definitely_not_committed"
        )
        assert _counts(run, command.proposal_ref) == (
            (1, 1, 9, 1, 1) if after_underlying_commit else (0, 0, 0, 0, 0)
        )


def test_changed_command_reuses_mutation_ref_only_as_identity_conflict() -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, safe = prepare_record_command(run)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            committed = writer._record_post_execution_proposal(command, run, safe)
        changed = replace(command, c1_membership_ref="different-member", command_digest="")
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            conflict = writer._record_post_execution_proposal(changed, run, safe)
        assert conflict.reason == "identity_conflict"
        assert _counts(run, command.proposal_ref) == (1, 1, 9, 1, 1)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            checked = writer._read_post_execution_proposal(command)
        assert checked.receipt.receipt_digest == committed.receipt_digest


def test_fresh_a_rechecks_actual_changed_program_head_before_any_target_write() -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, safe = prepare_record_command(run)
        _advance_program_head_in_test_database(run)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            conflict = writer._record_post_execution_proposal(command, run, safe)
        assert conflict.reason == "currentness_conflict"
        assert _counts(run, command.proposal_ref) == (0, 0, 0, 0, 0)


def test_fresh_owner_select_failure_is_integrity_error_before_any_a_effect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, safe = prepare_record_command(run)
        reached: list[str] = []

        def fail_owner_select(*args: object, **kwargs: object) -> object:
            reached.append("owner_select")
            raise sqlite3.OperationalError("synthetic owner SELECT failure")

        def forbid(name: str) -> object:
            def unexpected(*args: object, **kwargs: object) -> object:
                reached.append(name)
                raise AssertionError(f"unexpected {name}")

            return unexpected

        with monkeypatch.context() as patch:
            patch.setattr(c1_reader, "_read_phase_by_pair", fail_owner_select)
            patch.setattr(store, "_route_probe", forbid("route_probe"))
            patch.setattr(store, "_insert", forbid("insert"))
            patch.setattr(store, "_committed_digest", forbid("receipt_construction"))
            patch.setattr(transaction, "_commit_transaction", forbid("commit"))
            with acquire_sqlite_writer_session(run._d1_run.location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as caught:
                    writer._record_post_execution_proposal(command, run, safe)

        assert caught.value.error_class == "database_integrity_failure"
        assert reached == ["owner_select"]
        assert _counts(run, command.proposal_ref) == (0, 0, 0, 0, 0)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            assert writer._recover_post_execution_proposal(command).classification == (
                "definitely_not_committed"
            )


@pytest.mark.parametrize("control", [KeyboardInterrupt, SystemExit, GeneratorExit])
def test_fresh_owner_read_process_control_stays_unsuppressed(
    monkeypatch: pytest.MonkeyPatch, control: type[BaseException],
) -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, safe = prepare_record_command(run)
        reached = []

        def raise_control(*args: object, **kwargs: object) -> object:
            reached.append("owner_select")
            raise control()

        with monkeypatch.context() as patch:
            patch.setattr(c1_reader, "_read_phase_by_pair", raise_control)
            with acquire_sqlite_writer_session(run._d1_run.location) as writer:
                with pytest.raises(control):
                    writer._record_post_execution_proposal(command, run, safe)

        assert reached == ["owner_select"]
        assert _counts(run, command.proposal_ref) == (0, 0, 0, 0, 0)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            assert writer._recover_post_execution_proposal(command).classification == (
                "definitely_not_committed"
            )


def test_false_typed_c1_witness_refused_by_original_run_gate_before_target_rows() -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, safe = prepare_record_command(run)
        basis = json.loads(safe)
        basis["d2_checkpoint_witness"]["checked_memberships"][0][
            "membership_digest"
        ] = "0" * 64
        forged_safe = checked_safe_basis_bytes(basis)
        forged_command = replace(
            command, safe_basis_digest=safe_basis_digest(forged_safe),
            command_digest="",
        )
        witness_reached = []
        derivation_reached = []
        currentness_reached = []
        original_witness = store._check_witness
        original_derivation = store.prepare_record_command
        original_currentness = store._read_rw0_d2_current_owner_snapshot_after_fencing

        def observed_witness(capability: object, payload: dict[str, object]) -> None:
            witness_reached.append(True)
            original_witness(capability, payload)

        def observed_derivation(value: object) -> tuple[object, bytes]:
            derivation_reached.append(value is run)
            return original_derivation(value)

        def observed_currentness(*args: object, **kwargs: object) -> object:
            currentness_reached.append(True)
            return original_currentness(*args, **kwargs)

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(store, "_check_witness", observed_witness)
            patch.setattr(store, "prepare_record_command", observed_derivation)
            patch.setattr(
                store, "_read_rw0_d2_current_owner_snapshot_after_fencing",
                observed_currentness,
            )
            with acquire_sqlite_writer_session(run._d1_run.location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as caught:
                    writer._record_post_execution_proposal(
                        forged_command, run, forged_safe,
                    )
        assert caught.value.error_class == "database_integrity_failure"
        assert derivation_reached == [True]
        assert witness_reached == [] and currentness_reached == []
        assert _counts(run, command.proposal_ref) == (0, 0, 0, 0, 0)


@pytest.mark.parametrize("seconds_after_expiry", [-1, 0, 1])
def test_strict_transaction_sample_before_at_and_after_expiry(
    monkeypatch: pytest.MonkeyPatch, seconds_after_expiry: int,
) -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, safe = prepare_record_command(run)
        checkpoint = run.handback.evidence_checkpoint
        expiries = (
            checkpoint.d1_handback.author_command.attempt_fence.expires_at,
            checkpoint.d1_handback.author_command.effect_fence.expires_at,
            *(proof.current_fence.expires_at for proof in checkpoint.bound_effects),
            *(source.observation_expires_at for source in checkpoint.authority_sources),
            checkpoint.readiness_source.expires_at,
            checkpoint.validation_result_set.expires_at,
            checkpoint.review_result_set.expires_at,
            checkpoint.validation_disposition.expires_at,
            checkpoint.review_disposition.expires_at,
            checkpoint.policy_sources[0].expires_at,
            checkpoint.policy_sources[1].expires_at,
            checkpoint.policy_sources[4].expires_at,
            checkpoint.policy_matrices[0].expires_at,
            checkpoint.policy_matrices[1].expires_at,
        )
        boundary = datetime.fromisoformat(min(expiries).replace("Z", "+00:00"))
        sampled = (boundary + timedelta(seconds=seconds_after_expiry)).astimezone(
            timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        monkeypatch.setattr(transaction, "_capture_transaction_timestamp", lambda: sampled)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            result = writer._record_post_execution_proposal(command, run, safe)
        if seconds_after_expiry < 0:
            assert result.disposition == "fresh_committed"
            assert _counts(run, command.proposal_ref) == (1, 1, 9, 1, 1)
        else:
            assert result.reason == "currentness_conflict"
            assert _counts(run, command.proposal_ref) == (0, 0, 0, 0, 0)
