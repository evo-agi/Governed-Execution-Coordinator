"""Deterministic artificial planner executable for the D1 offline proof."""

from __future__ import annotations

import os
import sys
import time

from ._rw0_d1_process_frames import (
    D1FrameError, decode_planner_request, encode_planner_response,
)


def _main() -> int:
    raw = sys.stdin.buffer.read(256 * 1024 + 9)
    try:
        request = decode_planner_request(raw)
    except D1FrameError:
        return 2
    behavior = request["behavior"]
    if behavior == "timeout":
        time.sleep(60)
        return 3
    if behavior == "nonzero":
        return 3
    if behavior == "stderr_limit":
        os.write(2, b"e" * 70000)
        return 3
    if behavior == "malformed":
        os.write(1, b"D1O1\0\0\0\1{")
        return 0
    if behavior == "oversized":
        os.write(1, b"D1O1\0\1\0\1")
        return 0
    response = encode_planner_response({
        "strategy": "Apply one bounded source change.",
        "target_ordinal": 2,
        "action": request["action"],
        "recommendation": "defer" if behavior == "defer" else "select_for_dispatch_gates",
        "reason": "plan.bounded_contract_change",
        "plan": "Modify the authorized contract test for the artificial proof.",
    })
    os.write(1, response + (b"x" if behavior == "trailing" else b""))
    return 0


def _entry() -> int:
    try:
        return _main()
    except Exception:
        return 4


if __name__ == "__main__":
    raise SystemExit(_entry())
