"""Private guarded delegation, process custody, and outer disposal outcome."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture
from ge_nwp_coordinator._rw0_d2_handback import RW0D2OfflineRun
from ge_nwp_coordinator._rw0_d2_offline import run_rw0_d2_offline
from ge_nwp_coordinator._rw0_d2_post_execution_continuation import (
    PostD2ContinuationResultV1,
    continue_open_rw0_d2_run, prepare_record_command,
    run_rw0_d2_post_execution_continuation,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_rw0_d1_offline_integration import work_spec
from test_rw0_d2_post_execution_admission_integration import _counts


def test_outer_result_status_and_cleanup_fields_are_closed() -> None:
    with pytest.raises(ValueError, match="invalid_post_d2_continuation_result"):
        PostD2ContinuationResultV1("invented", "complete")
    with pytest.raises(ValueError, match="invalid_post_d2_continuation_result"):
        PostD2ContinuationResultV1("projected", "complete")
    with pytest.raises(ValueError, match="invalid_post_d2_continuation_result"):
        PostD2ContinuationResultV1("cleanup_unresolved", "cleanup", cleanup_complete=True)


def test_outer_owner_publishes_clean_cleanup_only_after_disposal() -> None:
    work = work_spec()
    result = run_rw0_d2_post_execution_continuation(
        work, artificial_fixture(work),
    )
    assert result.status == "projected"
    assert result.cleanup_complete is True


def test_private_ingress_rejects_invalid_command_before_target_write() -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, safe = prepare_record_command(run)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as caught:
                writer._record_post_execution_proposal(object(), run, safe)
        assert caught.value.error_class == "database_integrity_failure"
        assert _counts(run, command.proposal_ref) == (0, 0, 0, 0, 0)


def test_borrowed_continuation_refuses_wrong_creator_process_before_a() -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, _ = prepare_record_command(run)
        creator = run._creator_pid
        run._creator_pid = os.getpid() + 1
        try:
            with pytest.raises(RuntimeError, match="d2_run_wrong_process"):
                continue_open_rw0_d2_run(run)
        finally:
            run._creator_pid = creator
        assert _counts(run, command.proposal_ref) == (0, 0, 0, 0, 0)


def test_closed_run_cannot_be_used_as_restart_custody() -> None:
    work = work_spec()
    run = run_rw0_d2_offline(work, artificial_fixture(work))
    prepare_record_command(run)
    run.close()
    with pytest.raises(RuntimeError, match="d2_run_closed"):
        prepare_record_command(run)
    with pytest.raises(RuntimeError, match="d2_run_closed"):
        continue_open_rw0_d2_run(run)


def test_outer_owner_reports_late_cleanup_failure_without_clean_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    original = RW0D2OfflineRun.close
    calls = []

    def close_then_fail(self: RW0D2OfflineRun) -> None:
        calls.append(True)
        original(self)
        raise OSError("synthetic_disposal_report_failure")

    monkeypatch.setattr(RW0D2OfflineRun, "close", close_then_fail)
    result = run_rw0_d2_post_execution_continuation(work, artificial_fixture(work))
    assert len(calls) == 1
    assert result.status == "cleanup_unresolved"
    assert result.cleanup_complete is False
    assert result.proposal_result is not None
    assert result.admission_result is not None


def test_new_entry_is_private_and_unchanged_pure_v22_is_not_edited() -> None:
    package = Path(__file__).resolve().parents[1] / "src/ge_nwp_coordinator"
    writer_source = (package / "sqlite_writer_session.py").read_text()
    continuation_source = (package / "_rw0_d2_post_execution_continuation.py").read_text()
    protocol_source = (package / "state_store.py").read_text()
    assert "def _record_post_execution_proposal(" in writer_source
    assert "def run_rw0_d2_post_execution_continuation(" in continuation_source
    assert "def record_post_execution_proposal(" not in protocol_source
    assert "_section41_post_execution_proposal_family_projection" in continuation_source
