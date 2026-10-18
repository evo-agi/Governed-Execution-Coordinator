"""Bounded POSIX process facts for artificial D1 child modules.

This module alone owns process launch. Its observations confer no Coordinator
progression, selection, or executable authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time
from typing import Callable


_CHILDREN = frozenset({
    "ge_nwp_coordinator._rw0_d1_fake_planner",
    "ge_nwp_coordinator._rw0_d1_fake_worker",
})
_PROCESS_REASONS = frozenset({
    "ok", "invalid_input", "start_failed", "output_limit", "stderr_limit",
    "nonzero_exit", "deadline", "cancelled", "cleanup_unresolved",
})
_CLEANUP_REASONS = frozenset({
    "process_control", "selector_close", "stream_close", "reap_unproved",
    "group_unproved",
})


@dataclass(frozen=True, slots=True, repr=False)
class D1ProcessOutcome:
    reason: str
    pid: int | None
    process_group: int | None
    exit_code: int | None
    stdout: bytes = field(repr=False)
    stderr: bytes = field(repr=False)
    cancellation_requested: bool = False
    term_delivered: bool = False
    kill_delivered: bool = False
    reaped: bool = False
    group_clear: bool = False
    cleanup_reason: str | None = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Check the complete retained observation without consulting a process."""
        if type(self) is not D1ProcessOutcome:
            raise ValueError("invalid_d1_process_outcome")
        try:
            (reason, pid, group, exit_code, stdout, stderr, cancelled,
             term, kill, reaped, group_clear, cleanup) = (
                object.__getattribute__(self, name) for name in (
                    "reason", "pid", "process_group", "exit_code", "stdout",
                    "stderr", "cancellation_requested", "term_delivered",
                    "kill_delivered", "reaped", "group_clear", "cleanup_reason",
                )
            )
        except AttributeError:
            raise ValueError("invalid_d1_process_outcome") from None
        if (
            type(reason) is not str or reason not in _PROCESS_REASONS
            or (pid is not None and type(pid) is not int)
            or (group is not None and type(group) is not int)
            or (exit_code is not None and type(exit_code) is not int)
            or type(stdout) is not bytes or type(stderr) is not bytes
            or any(type(value) is not bool for value in (
                cancelled, term, kill, reaped, group_clear,
            ))
            or (cleanup is not None and (
                type(cleanup) is not str or cleanup not in _CLEANUP_REASONS
            ))
        ):
            raise ValueError("invalid_d1_process_outcome")
        if reason in {"invalid_input", "start_failed"}:
            if (pid is not None or group is not None or exit_code is not None
                    or stdout or stderr or cancelled or term or kill or reaped
                    or group_clear or cleanup is not None):
                raise ValueError("invalid_d1_process_outcome")
            return
        if (
            pid is None or pid <= 0 or group is None or group != pid
            or len(stdout) > 1024 * 1024 + 1 or len(stderr) > 64 * 1024 + 1
            or (reaped and exit_code is None)
            or (cleanup is None and (not reaped or not group_clear))
            or (cleanup == "reap_unproved" and reaped)
            or (cleanup == "group_unproved" and (group_clear or not reaped))
            or (reason == "ok" and exit_code != 0)
            or (reason == "nonzero_exit" and (exit_code is None or exit_code == 0))
            or (reason == "output_limit" and len(stdout) < 2)
            or (reason == "stderr_limit" and len(stderr) < 2)
            or (reason == "cancelled") != cancelled
            or (term and reason in {"ok", "nonzero_exit"})
            or (reason == "ok" and cleanup == "process_control")
            or (reason == "nonzero_exit" and cleanup == "process_control")
            or (reason == "cleanup_unresolved" and cleanup not in {
                "process_control", "reap_unproved",
            })
            or (reason == "cleanup_unresolved" and cleanup == "reap_unproved"
                and exit_code is not None)
        ):
            raise ValueError("invalid_d1_process_outcome")

    @property
    def cleanup_complete(self) -> bool:
        return self.reaped and self.group_clear and self.cleanup_reason is None

    @property
    def clean_success(self) -> bool:
        """Ordinary clean completion after the caller validates this value."""
        return self.reason == "ok" and self.cleanup_complete


def _group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return True
    return True


def _signal_group(pgid: int, sig: int) -> bool:
    try:
        os.killpg(pgid, sig)
        return True
    except ProcessLookupError:
        return False
    except OSError:
        return False


def run_fake_module(
    module: str,
    request: bytes,
    *,
    cwd: Path,
    timeout_seconds: float = 5.0,
    output_limit: int = 256 * 1024,
    stderr_limit: int = 16 * 1024,
    cancelled: Callable[[], bool] | None = None,
) -> D1ProcessOutcome:
    if (os.name != "posix" or type(module) is not str or module not in _CHILDREN
            or type(request) is not bytes or len(request) > 256 * 1024
            or not isinstance(cwd, Path) or not cwd.is_dir()
            or type(timeout_seconds) not in (int, float)
            or not 0 < timeout_seconds <= 30
            or type(output_limit) is not int or not 0 < output_limit <= 1024 * 1024
            or type(stderr_limit) is not int or not 0 < stderr_limit <= 64 * 1024
            or (cancelled is not None and not callable(cancelled))):
        return D1ProcessOutcome("invalid_input", None, None, None, b"", b"")
    executable = str(Path(sys.executable).resolve())
    package_src = str(Path(__file__).resolve().parent.parent)
    env = {
        "PYTHONPATH": package_src,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "LANG": "C",
        "LC_ALL": "C",
        "__CF_USER_TEXT_ENCODING": "0x0:0:0",
        "TMPDIR": str(cwd.resolve()),
    }
    try:
        child = subprocess.Popen(
            (executable, "-B", "-m", module),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=str(cwd), env=env,
            shell=False, start_new_session=True,
            close_fds=True, pass_fds=(),
        )
    except OSError:
        return D1ProcessOutcome("start_failed", None, None, None, b"", b"")
    assert child.stdin is not None and child.stdout is not None and child.stderr is not None
    pid = child.pid
    pgid = pid
    selector: selectors.BaseSelector | None = None
    out = bytearray()
    err = bytearray()
    sent = 0
    reason = "ok"
    cancel_seen = False
    term_sent = False
    kill_sent = False
    reaped = False
    deadline = time.monotonic() + timeout_seconds
    termination_at: float | None = None
    cleanup_reason: str | None = None
    try:
        selector = selectors.DefaultSelector()
        for stream in (child.stdin, child.stdout, child.stderr):
            os.set_blocking(stream.fileno(), False)
        selector.register(child.stdout, selectors.EVENT_READ, "stdout")
        selector.register(child.stderr, selectors.EVENT_READ, "stderr")
        selector.register(child.stdin, selectors.EVENT_WRITE, "stdin")
        while child.poll() is None or selector.get_map():
            now = time.monotonic()
            if reason == "ok" and cancelled is not None:
                try:
                    cancel_seen = cancelled() is True
                except BaseException:
                    cancel_seen = True
                if cancel_seen:
                    reason = "cancelled"
            if reason == "ok" and now >= deadline:
                reason = "deadline"
            if reason != "ok" and termination_at is None:
                term_sent = _signal_group(pgid, signal.SIGTERM)
                termination_at = now
            if termination_at is not None and now - termination_at >= 0.3 and _group_alive(pgid):
                kill_sent = _signal_group(pgid, signal.SIGKILL) or kill_sent
            events = selector.select(0.025)
            for key, _ in events:
                name = key.data
                stream = key.fileobj
                if name == "stdin":
                    if sent == len(request) or reason != "ok":
                        selector.unregister(stream)
                        stream.close()
                        continue
                    try:
                        sent += os.write(stream.fileno(), request[sent:sent + 65536])
                    except (BrokenPipeError, OSError):
                        selector.unregister(stream)
                        stream.close()
                else:
                    try:
                        block = os.read(stream.fileno(), 65536)
                    except BlockingIOError:
                        continue
                    if not block:
                        selector.unregister(stream)
                        stream.close()
                        continue
                    target = out if name == "stdout" else err
                    limit = output_limit if name == "stdout" else stderr_limit
                    target.extend(block[: max(0, limit + 1 - len(target))])
                    if len(target) > limit and reason == "ok":
                        reason = "output_limit" if name == "stdout" else "stderr_limit"
            if child.poll() is not None and not selector.get_map():
                break
            if termination_at is not None and now - termination_at > 1.0:
                break
        try:
            child.wait(timeout=0.5)
            reaped = True
        except subprocess.TimeoutExpired:
            kill_sent = _signal_group(pgid, signal.SIGKILL) or kill_sent
            try:
                child.wait(timeout=0.5)
                reaped = True
            except subprocess.TimeoutExpired:
                reaped = False
        if reason == "ok":
            if child.returncode is None:
                reason = "cleanup_unresolved"
            elif child.returncode != 0:
                reason = "nonzero_exit"
    except BaseException:
        if reason == "ok":
            reason = "cleanup_unresolved"
        cleanup_reason = "process_control"
        term_sent = _signal_group(pgid, signal.SIGTERM) or term_sent
        time.sleep(0.05)
        kill_sent = _signal_group(pgid, signal.SIGKILL) or kill_sent
        try:
            child.wait(timeout=0.5)
            reaped = True
        except BaseException:
            reaped = False
    finally:
        if selector is not None:
            try:
                selector.close()
            except Exception:
                if cleanup_reason is None:
                    cleanup_reason = "selector_close"
        for stream in (child.stdin, child.stdout, child.stderr):
            try:
                stream.close()
            except Exception:
                if cleanup_reason is None:
                    cleanup_reason = "stream_close"
    group_clear = not _group_alive(pgid)
    if not group_clear:
        kill_sent = _signal_group(pgid, signal.SIGKILL) or kill_sent
        time.sleep(0.02)
        group_clear = not _group_alive(pgid)
    if not reaped and cleanup_reason is None:
        cleanup_reason = "reap_unproved"
    if not group_clear and cleanup_reason is None:
        cleanup_reason = "group_unproved"
    return D1ProcessOutcome(
        reason, pid, pgid, child.returncode, bytes(out), bytes(err),
        cancel_seen, term_sent, kill_sent, reaped, group_clear, cleanup_reason,
    )
