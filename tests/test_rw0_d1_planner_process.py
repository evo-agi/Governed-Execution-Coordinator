from __future__ import annotations

from pathlib import Path

import pytest

from ge_nwp_coordinator._rw0_d1_process_frames import (
    D1FrameError, decode_planner_response,
)
from ge_nwp_coordinator._rw0_d1_process_supervisor import run_fake_module
from test_rw0_d1_process_supervisor import request


@pytest.mark.parametrize("behavior,reason", (
    ("normal", "ok"), ("malformed", "ok"), ("oversized", "ok"),
    ("trailing", "ok"), ("nonzero", "nonzero_exit"),
    ("stderr_limit", "stderr_limit"),
))
def test_separate_planner_closed_response(
    tmp_path: Path, behavior: str, reason: str,
) -> None:
    result = run_fake_module(
        "ge_nwp_coordinator._rw0_d1_fake_planner", request(behavior),
        cwd=tmp_path, stderr_limit=128,
    )
    assert result.reason == reason
    assert result.cleanup_complete
    if behavior == "normal":
        response = decode_planner_response(result.stdout)
        assert response["target_ordinal"] == 2
        assert response["recommendation"] == "select_for_dispatch_gates"
        assert set(response) == {
            "strategy", "target_ordinal", "action", "recommendation",
            "reason", "plan",
        }
        assert not any(key.endswith("_ref") for key in response)
    if behavior in {"malformed", "oversized", "trailing"}:
        with pytest.raises(D1FrameError):
            decode_planner_response(result.stdout)


def test_planner_deadline_and_cancel_are_distinct(tmp_path: Path) -> None:
    deadline = run_fake_module(
        "ge_nwp_coordinator._rw0_d1_fake_planner", request("timeout"),
        cwd=tmp_path, timeout_seconds=0.1,
    )
    cancelled = run_fake_module(
        "ge_nwp_coordinator._rw0_d1_fake_planner", request("timeout"),
        cwd=tmp_path, cancelled=lambda: True,
    )
    assert deadline.reason == "deadline"
    assert cancelled.reason == "cancelled"
    assert deadline.cleanup_complete and cancelled.cleanup_complete
