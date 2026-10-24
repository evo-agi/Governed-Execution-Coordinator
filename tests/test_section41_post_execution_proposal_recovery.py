"""Owner-specific read-only recovery and A/B gap classifications."""

from __future__ import annotations

import sqlite3

import pytest

import ge_nwp_coordinator._rw0_d2_post_execution_continuation as continuation
import ge_nwp_coordinator.sqlite_transition_transaction as transaction
from ge_nwp_coordinator import _cognitive_proposal_row_values as common
from ge_nwp_coordinator._rw0_c1_semantic_values import evidence_admission_recovery_selector
from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture
from ge_nwp_coordinator._rw0_d2_offline import run_rw0_d2_offline
from ge_nwp_coordinator._rw0_d2_post_execution_continuation import (
    _rank15_command, continue_open_rw0_d2_run, prepare_record_command,
)
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError, SQLiteMutationStoreErrorCode,
)
from ge_nwp_coordinator.sqlite_writer_session import (
    _SQLiteWriterSession, acquire_sqlite_writer_session,
)
from test_rw0_d1_offline_integration import work_spec
from test_rw0_d2_post_execution_admission_integration import (
    _advance_program_head_in_test_database, _counts, _record_and_read,
    _omit_optional_capture_observation,
)


def test_a_recovery_is_exact_historical_after_head_move() -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, first, _ = _record_and_read(run)
        _advance_program_head_in_test_database(run)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            recovery = writer._recover_post_execution_proposal(command)
        assert recovery.classification == "committed_exact"
        assert recovery.result.receipt_digest == first.receipt_digest
        assert recovery.result.committed_at == first.committed_at
        assert _counts(run, command.proposal_ref) == (1, 1, 9, 1, 1)


@pytest.mark.parametrize("after_underlying_commit", [False, True])
def test_outer_a_commit_exception_uses_read_only_three_way_recovery(
    monkeypatch: pytest.MonkeyPatch, after_underlying_commit: bool,
) -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, _ = prepare_record_command(run)
        original = transaction._commit_transaction
        calls = []

        def uncertain_first_commit(connection: sqlite3.Connection) -> None:
            calls.append(True)
            monkeypatch.setattr(transaction, "_commit_transaction", original)
            if after_underlying_commit:
                original(connection)
            raise sqlite3.OperationalError("synthetic_a_commit_uncertainty")

        monkeypatch.setattr(transaction, "_commit_transaction", uncertain_first_commit)
        result = continue_open_rw0_d2_run(run)
        assert len(calls) == 1
        if after_underlying_commit:
            assert result.status == "projected"
            assert result.proposal_result.disposition == "exact_replay"
            assert _counts(run, command.proposal_ref) == (1, 1, 9, 1, 1)
        else:
            assert (result.status, result.reason) == (
                "proposal_not_recorded", "definitely_not_committed",
            )
            assert result.proposal_result is None
            assert result.admission_result is None
            assert _counts(run, command.proposal_ref) == (0, 0, 0, 0, 0)


def test_absent_complete_a_routes_are_definitely_not_committed() -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, _ = prepare_record_command(run)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            recovery = writer._recover_post_execution_proposal(command)
        assert recovery.classification == "definitely_not_committed"
        assert _counts(run, command.proposal_ref) == (0, 0, 0, 0, 0)


def test_partial_foreign_a_route_is_unresolved_without_write() -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, _ = prepare_record_command(run)
        table = common._TABLE_ORDER[0]
        row = common._row_value_from_mapping(
            table, run.handback.model_source_invocation.to_mapping()
        )
        columns = common._TABLE_COLUMNS[table]
        with sqlite3.connect(run._d1_run.location.database_path) as db:
            db.execute(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ("
                + ",".join("?" for _ in columns) + ")",
                tuple(row.to_mapping()[name] for name in columns),
            )
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            recovery = writer._recover_post_execution_proposal(command)
        assert recovery.classification == "unresolved"
        assert _counts(run, command.proposal_ref) == (1, 0, 0, 0, 0)


def test_c1_b_absence_then_lost_return_uses_checked_readback_without_second_admit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        # Establish A independently first to inspect B's exact absent route.
        command, _, checked = _record_and_read(run)
        b_command = _rank15_command(checked, run.handback.checked_admissions[0].phase)
        selector = evidence_admission_recovery_selector(b_command)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            before = writer._resolve_rw0_c1_evidence_admission_commit_outcome(selector)
        assert before.disposition.value == "definitely_not_committed"
        # The borrowed continuation replays A historically and issues B once.
        original = _SQLiteWriterSession._admit_rw0_evidence
        calls = []

        def lost_return(self: _SQLiteWriterSession, payload: object) -> object:
            calls.append(True)
            original(self, payload)
            raise SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN)

        monkeypatch.setattr(_SQLiteWriterSession, "_admit_rw0_evidence", lost_return)
        result = continue_open_rw0_d2_run(run)
        assert len(calls) == 1
        assert result.status == "projected"
        assert result.proposal_result.disposition == "exact_replay"
        assert result.admission_result.disposition == "exact_replay"
        assert _counts(run, command.proposal_ref) == (1, 1, 9, 1, 1)
        with sqlite3.connect(run._d1_run.location.database_path) as db:
            assert db.execute(
                "SELECT count(*) FROM rw0_c1_mutation_receipts WHERE mutation_ref=?",
                (b_command.mutation_ref,),
            ).fetchone()[0] == 1


def test_b_committed_but_projection_failure_is_reported_as_admitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        def fail_projection(*args: object) -> object:
            raise ValueError("synthetic_projection_check_failed")
        monkeypatch.setattr(continuation, "_project", fail_projection)
        result = continue_open_rw0_d2_run(run)
        assert result.status == "admitted_verification_failed"
        assert result.proposal_result.disposition == "fresh_committed"
        assert result.admission_result.kind_rank == 15
        with sqlite3.connect(run._d1_run.location.database_path) as db:
            assert db.execute(
                "SELECT count(*) FROM rw0_c1_mutation_receipts WHERE mutation_ref=?",
                (result.admission_result.mutation_ref,),
            ).fetchone()[0] == 1


def test_a_committed_but_first_fresh_readback_failure_stops_before_b(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, _ = prepare_record_command(run)
        reached = []

        def fail_read(self: _SQLiteWriterSession, payload: object) -> object:
            reached.append(True)
            raise SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)

        monkeypatch.setattr(_SQLiteWriterSession, "_read_post_execution_proposal", fail_read)
        result = continue_open_rw0_d2_run(run)
        assert reached
        assert result.status == "proposal_recorded_verification_failed"
        assert result.proposal_result.disposition == "fresh_committed"
        assert result.admission_result is None
        assert _counts(run, command.proposal_ref) == (1, 1, 9, 1, 1)
        with sqlite3.connect(run._d1_run.location.database_path) as db:
            assert db.execute(
                "SELECT count(*) FROM rw0_c1_mutation_receipts WHERE kind_rank=15"
            ).fetchone()[0] == 0


@pytest.mark.parametrize("after_underlying_commit", [False, True])
@pytest.mark.parametrize("worker_count", (2, 3))
def test_real_b_commit_call_uncertainty_is_resolved_without_duplicate_admit(
    monkeypatch: pytest.MonkeyPatch, after_underlying_commit: bool,
    worker_count: int,
) -> None:
    if worker_count == 2:
        _omit_optional_capture_observation(monkeypatch)
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        assert len(run.handback.d1_handback.wire_result.observations) == worker_count
        assert len(run.handback.checked_admissions) == worker_count + 11
        command, _, _ = _record_and_read(run)
        original = transaction._commit_transaction
        calls = []

        def uncertain_commit(connection: sqlite3.Connection) -> object:
            calls.append(True)
            if after_underlying_commit:
                original(connection)
            raise sqlite3.OperationalError("synthetic_b_commit_uncertainty")

        monkeypatch.setattr(transaction, "_commit_transaction", uncertain_commit)
        result = continue_open_rw0_d2_run(run)
        assert len(calls) == 1
        if after_underlying_commit:
            assert result.status == "projected"
            assert result.admission_result.disposition == "exact_replay"
            expected_b = 1
        else:
            assert result.status == "proposal_recorded_not_admitted"
            assert result.reason == "definitely_not_committed"
            assert result.admission_result is None
            expected_b = 0
        assert _counts(run, command.proposal_ref) == (1, 1, 9, 1, 1)
        with sqlite3.connect(run._d1_run.location.database_path) as db:
            assert db.execute(
                "SELECT count(*) FROM rw0_c1_mutation_receipts WHERE kind_rank=15"
            ).fetchone()[0] == expected_b


@pytest.mark.parametrize("worker_count", (2, 3))
def test_b_failure_after_real_rows_before_commit_rolls_back_b_only(
    monkeypatch: pytest.MonkeyPatch, worker_count: int,
) -> None:
    if worker_count == 2:
        _omit_optional_capture_observation(monkeypatch)
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        assert len(run.handback.d1_handback.wire_result.observations) == worker_count
        assert len(run.handback.checked_admissions) == worker_count + 11
        command, _, _ = _record_and_read(run)
        reached = []

        def fail_readback(*args: object, **kwargs: object) -> object:
            reached.append(True)
            raise SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)

        monkeypatch.setattr(transaction, "_readback_rw0_c1_evidence_admission", fail_readback)
        result = continue_open_rw0_d2_run(run)
        assert reached
        assert result.status == "proposal_recorded_not_admitted"
        assert result.proposal_result.disposition == "exact_replay"
        assert _counts(run, command.proposal_ref) == (1, 1, 9, 1, 1)
        with sqlite3.connect(run._d1_run.location.database_path) as db:
            assert db.execute(
                "SELECT count(*) FROM rw0_c1_mutation_receipts WHERE kind_rank=15"
            ).fetchone()[0] == 0
