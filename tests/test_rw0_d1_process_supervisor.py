from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path
import sys

import pytest

import ge_nwp_coordinator._rw0_d1_process_supervisor as supervisor
from ge_nwp_coordinator._rw0_d1_process_frames import encode_planner_request


def request(behavior: str = "normal") -> bytes:
    return encode_planner_request({
        "objective": "Make one artificial change.",
        "requirements": ["Stay in scope."], "exclusions": ["No network."],
        "path_ordinals": [0, 1, 2], "action": "modify_authorized_path",
        "behavior": behavior,
    })


def inject_selector_close_failure(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    original_selector = supervisor.selectors.DefaultSelector
    original_group_alive = supervisor._group_alive
    observations = {"close": 0, "group_check": 0}

    class FailingSelector:
        def __init__(self) -> None:
            self._wrapped = original_selector()

        def __getattr__(self, name: str) -> object:
            return getattr(self._wrapped, name)

        def close(self) -> None:
            self._wrapped.close()
            observations["close"] += 1
            raise OSError("raw selector cleanup detail must not escape")

    def observed_group(pgid: int) -> bool:
        observations["group_check"] += 1
        return original_group_alive(pgid)

    monkeypatch.setattr(supervisor.selectors, "DefaultSelector", FailingSelector)
    monkeypatch.setattr(supervisor, "_group_alive", observed_group)
    return observations


def test_real_child_pid_group_reap_and_bounded_output(tmp_path: Path) -> None:
    result = supervisor.run_fake_module(
        "ge_nwp_coordinator._rw0_d1_fake_planner", request(), cwd=tmp_path,
    )
    assert result.reason == "ok"
    assert result.pid != os.getpid()
    assert result.process_group == result.pid
    assert result.exit_code == 0
    assert result.cleanup_complete
    assert len(result.stdout) < 64 * 1024
    assert not supervisor._group_alive(result.process_group)


@pytest.mark.parametrize("behavior,expected", (
    ("nonzero", "nonzero_exit"),
    ("timeout", "deadline"),
    ("stderr_limit", "stderr_limit"),
))
def test_process_failures_are_reaped(
    tmp_path: Path, behavior: str, expected: str,
) -> None:
    result = supervisor.run_fake_module(
        "ge_nwp_coordinator._rw0_d1_fake_planner", request(behavior),
        cwd=tmp_path, timeout_seconds=0.1 if behavior == "timeout" else 5.0,
        stderr_limit=128,
    )
    assert result.reason == expected
    assert result.cleanup_complete
    if behavior == "timeout":
        assert result.term_delivered


def test_cancellation_is_request_and_signal_not_semantic_exit(tmp_path: Path) -> None:
    result = supervisor.run_fake_module(
        "ge_nwp_coordinator._rw0_d1_fake_planner", request("timeout"),
        cwd=tmp_path, cancelled=lambda: True,
    )
    assert result.reason == "cancelled"
    assert result.cancellation_requested
    assert result.term_delivered
    assert result.cleanup_complete


def test_start_failure_and_unsupported_child_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalid = supervisor.run_fake_module("os", request(), cwd=tmp_path)
    assert invalid.reason == "invalid_input"
    assert invalid.pid is None

    def fail_start(*args: object, **kwargs: object) -> object:
        raise OSError("test start failure")

    monkeypatch.setattr(supervisor.subprocess, "Popen", fail_start)
    result = supervisor.run_fake_module(
        "ge_nwp_coordinator._rw0_d1_fake_planner", request(), cwd=tmp_path,
    )
    assert result.reason == "start_failed"
    assert result.pid is None


def test_child_observes_sanitized_argv_env_cwd_and_no_parent_fd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = Path(supervisor.__file__).parent
    module_path = package / "_rw0_d1_probe_temp.py"
    module = "ge_nwp_coordinator._rw0_d1_probe_temp"
    descriptor = os.open(tmp_path / "parent-secret", os.O_CREAT | os.O_RDWR, 0o600)
    os.set_inheritable(descriptor, True)
    try:
        module_path.write_text(
            "import json, os, sys\n"
            "try:\n"
            f" os.fstat({descriptor})\n"
            " inherited = True\n"
            "except OSError:\n"
            " inherited = False\n"
            "sys.stdin.buffer.read()\n"
            "os.write(1, json.dumps({'argv':sys.argv,'env':sorted(os.environ),"
            "'cwd':os.getcwd(),'inherited':inherited}).encode())\n"
        )
        monkeypatch.setattr(supervisor, "_CHILDREN", supervisor._CHILDREN | {module})
        result = supervisor.run_fake_module(module, b"bounded input", cwd=tmp_path)
        assert result.reason == "ok"
        observed = json.loads(result.stdout)
        assert observed["argv"] == [str(module_path)]
        assert observed["cwd"] == str(tmp_path)
        assert observed["inherited"] is False
        assert set(observed["env"]) == {
            "LANG", "LC_ALL", "PYTHONDONTWRITEBYTECODE", "PYTHONIOENCODING",
            "PYTHONPATH", "TMPDIR", "__CF_USER_TEXT_ENCODING",
        }
        assert not any("secret" in key.lower() for key in observed["env"])
    finally:
        os.close(descriptor)
        module_path.unlink(missing_ok=True)


def test_cleanup_uncertainty_blocks_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = supervisor._group_alive
    monkeypatch.setattr(supervisor, "_group_alive", lambda pgid: True)
    result = supervisor.run_fake_module(
        "ge_nwp_coordinator._rw0_d1_fake_planner", request(), cwd=tmp_path,
    )
    assert result.reason == "ok"
    assert result.cleanup_reason == "group_unproved"
    assert result.reaped
    monkeypatch.setattr(supervisor, "_group_alive", original)


@pytest.mark.parametrize("behavior,timeout,cancelled,expected", (
    ("normal", 5.0, None, "ok"),
    ("timeout", 0.1, None, "deadline"),
    ("timeout", 5.0, lambda: True, "cancelled"),
))
def test_selector_cleanup_failure_preserves_process_facts_and_group_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    behavior: str, timeout: float, cancelled, expected: str,
) -> None:
    observations = inject_selector_close_failure(monkeypatch)
    outcome = supervisor.run_fake_module(
        "ge_nwp_coordinator._rw0_d1_fake_planner", request(behavior),
        cwd=tmp_path, timeout_seconds=timeout, cancelled=cancelled,
    )
    assert outcome.reason == expected
    assert outcome.cleanup_reason == "selector_close"
    assert outcome.cleanup_complete is False
    assert outcome.pid is not None and outcome.pid != os.getpid()
    assert outcome.process_group == outcome.pid
    assert outcome.reaped and outcome.group_clear
    assert outcome.exit_code is not None
    assert observations["close"] == 1
    assert observations["group_check"] >= 1
    assert not supervisor._group_alive(outcome.process_group)
    assert "raw selector cleanup detail" not in repr(outcome)
    if expected == "deadline":
        assert outcome.term_delivered
    if expected == "cancelled":
        assert outcome.cancellation_requested and outcome.term_delivered


def test_stream_cleanup_failure_is_typed_after_real_reap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_popen = supervisor.subprocess.Popen
    closes = 0

    class LateCloseFailure:
        def __init__(self, stream: object) -> None:
            self._stream = stream

        def fileno(self) -> int:
            return self._stream.fileno()

        def close(self) -> None:
            nonlocal closes
            closes += 1
            self._stream.close()
            if closes == 2:
                raise OSError("raw stream cleanup detail must not escape")

    def wrapped_popen(*args: object, **kwargs: object):
        child = original_popen(*args, **kwargs)
        child.stdout = LateCloseFailure(child.stdout)
        return child

    monkeypatch.setattr(supervisor.subprocess, "Popen", wrapped_popen)
    result = supervisor.run_fake_module(
        "ge_nwp_coordinator._rw0_d1_fake_planner", request(), cwd=tmp_path,
    )
    assert closes == 2
    assert result.reason == "ok"
    assert result.cleanup_reason == "stream_close"
    assert result.cleanup_complete is False
    assert result.pid is not None and result.reaped and result.group_clear
    assert not supervisor._group_alive(result.process_group)
    assert "raw stream cleanup detail" not in repr(result)


def test_process_value_reason_and_fact_matrix_is_independent_of_supervisor_calls() -> None:
    class IntSubclass(int):
        pass

    class BytesSubclass(bytes):
        pass

    class StrSubclass(str):
        pass

    class Hostile:
        def __eq__(self, other: object) -> bool:
            raise AssertionError("hostile equality was used")

        def __lt__(self, other: object) -> bool:
            raise AssertionError("hostile ordering was used")

    outcome = supervisor.D1ProcessOutcome(
        "ok", 1001, 1001, 0, b"frame", b"", reaped=True, group_clear=True,
    )
    no_launch = supervisor.D1ProcessOutcome(
        "start_failed", None, None, None, b"", b"",
    )
    valid = (
        no_launch,
        replace(no_launch, reason="invalid_input"),
        outcome,
        replace(outcome, reason="nonzero_exit", exit_code=99),
        replace(outcome, reason="nonzero_exit", exit_code=-15),
        replace(outcome, reason="nonzero_exit", exit_code=3,
                cleanup_reason="selector_close"),
        replace(outcome, reason="cancelled", cancellation_requested=True),
        replace(outcome, reason="deadline"),
        replace(outcome, reason="output_limit", stdout=b"xx", exit_code=-15,
                term_delivered=True),
        replace(outcome, reason="stderr_limit", stderr=b"xx", exit_code=0),
        replace(outcome, cleanup_reason="selector_close"),
        replace(outcome, cleanup_reason="stream_close"),
        replace(outcome, group_clear=False, cleanup_reason="group_unproved"),
        replace(outcome, reaped=False, cleanup_reason="reap_unproved"),
        replace(outcome, reason="cleanup_unresolved", exit_code=None,
                reaped=False, group_clear=False, cleanup_reason="process_control"),
        replace(outcome, reason="cleanup_unresolved",
                cleanup_reason="process_control"),
        replace(outcome, reason="cleanup_unresolved", exit_code=None,
                reaped=False, cleanup_reason="reap_unproved"),
    )
    for specimen in valid:
        assert specimen.validate() is None
    assert valid[6].exit_code == 0  # Cancellation may finish with zero.
    assert valid[10].reason == "ok" and not valid[10].cleanup_complete

    invalid = (
        ("ok_exit_99", outcome, {"exit_code": 99}),
        ("ok_exit_absent", outcome, {"exit_code": None}),
        ("ok_signal_exit", outcome, {"exit_code": -15}),
        ("bool_exit", outcome, {"exit_code": False}),
        ("subclass_exit", outcome, {"exit_code": IntSubclass(0)}),
        ("negative_pid", outcome, {"pid": -1}),
        ("zero_pid", outcome, {"pid": 0}),
        ("absent_pid", outcome, {"pid": None}),
        ("bool_pid", outcome, {"pid": True}),
        ("subclass_pid", outcome, {"pid": IntSubclass(1001)}),
        ("negative_group", outcome, {"process_group": -1}),
        ("zero_group", outcome, {"process_group": 0}),
        ("absent_group", outcome, {"process_group": None}),
        ("bool_group", outcome, {"process_group": True}),
        ("subclass_group", outcome, {"process_group": IntSubclass(1001)}),
        ("different_group", outcome, {"process_group": 1002}),
        ("nonzero_reason_zero_exit", outcome, {"reason": "nonzero_exit"}),
        ("nonzero_reason_absent_exit", outcome,
         {"reason": "nonzero_exit", "exit_code": None, "reaped": False,
          "cleanup_reason": "reap_unproved"}),
        ("no_launch_pid", no_launch, {"pid": 1001}),
        ("no_launch_exit", no_launch, {"exit_code": 0}),
        ("no_launch_output", no_launch, {"stdout": b"diagnostic"}),
        ("no_launch_signal", no_launch, {"term_delivered": True}),
        ("empty_output_limit", outcome, {"reason": "output_limit", "stdout": b""}),
        ("empty_stderr_limit", outcome, {"reason": "stderr_limit", "stderr": b""}),
        ("cancel_without_request", outcome, {"reason": "cancelled"}),
        ("request_without_cancel", outcome, {"cancellation_requested": True}),
        ("term_with_success", outcome, {"term_delivered": True}),
        ("unreaped_without_cleanup", outcome, {"reaped": False}),
        ("unclear_group_without_cleanup", outcome, {"group_clear": False}),
        ("reap_unproved_but_reaped", outcome, {"cleanup_reason": "reap_unproved"}),
        ("group_unproved_but_clear", outcome, {"cleanup_reason": "group_unproved"}),
        ("control_failure_but_ok", outcome, {"cleanup_reason": "process_control"}),
        ("control_failure_after_nonzero_label", outcome,
         {"reason": "nonzero_exit", "exit_code": 3,
          "cleanup_reason": "process_control"}),
        ("unresolved_without_cleanup", outcome, {"reason": "cleanup_unresolved"}),
        ("unresolved_reap_with_known_exit", outcome,
         {"reason": "cleanup_unresolved", "reaped": False,
          "cleanup_reason": "reap_unproved"}),
        ("wrong_reason_type", outcome, {"reason": StrSubclass("ok")}),
        ("wrong_bytes_type", outcome, {"stdout": BytesSubclass(b"frame")}),
        ("wrong_bool_type", outcome, {"reaped": 1}),
        ("wrong_cleanup_type", outcome, {"cleanup_reason": StrSubclass("selector_close")}),
        ("hostile_exit", outcome, {"exit_code": Hostile()}),
        ("hostile_pid", outcome, {"pid": Hostile()}),
    )
    for label, base, changes in invalid:
        with pytest.raises(ValueError, match="^invalid_d1_process_outcome$") as error:
            replace(base, **changes)
        assert str(error.value) == "invalid_d1_process_outcome", label
