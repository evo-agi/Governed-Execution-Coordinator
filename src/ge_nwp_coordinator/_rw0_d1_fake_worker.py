"""Deterministic artificial coding worker; it owns no Coordinator authority."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import time

from ._rw0_d1_process_frames import D1FrameError, decode_worker_launch
from ._rw0_wire_protocol_values import (
    RW0WireWorkerResultV1, decode_wire_command_frame, encode_wire_result_frame,
)
from ._worker_execution_semantic_values import (
    AttemptFenceV1, EffectFenceV1, WorkerObservationV1,
)


def _observed_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _main() -> int:
    raw = sys.stdin.buffer.read(256 * 1024 + 9)
    try:
        launch = decode_worker_launch(raw)
        frame = base64.b64decode(launch["command_frame_b64"], validate=True)
        attempt = AttemptFenceV1.from_mapping(launch["attempt_fence"])
        effect = EffectFenceV1.from_mapping(launch["effect_fence"])
        command, delivery = decode_wire_command_frame(
            frame, attempt_fence=attempt, author_effect_fence=effect,
        )
        if (command.effect_class != "author_candidate"
                or launch["action"] != "modify_authorized_path"
                or tuple(command.path_ceiling) != tuple(attempt.path_ceiling)
                or launch["target_ordinal"] != 2):
            return 2
    except (D1FrameError, ValueError, TypeError, KeyError):
        return 2
    started_at = _observed_now()
    behavior = launch["behavior"]
    if behavior == "timeout":
        time.sleep(60)
        return 3
    if behavior == "nonzero":
        return 3
    if behavior == "stderr_limit":
        os.write(2, b"e" * 70000)
        return 3
    if behavior == "malformed":
        os.write(1, b"NWPF\0\0\0\0")
        return 0
    target = Path(command.path_ceiling[launch["target_ordinal"]])
    captured_at: str | None = None
    if behavior == "extra_path":
        Path("unexpected.txt").write_bytes(b"unexpected\n")
    elif behavior == "unsafe_path":
        target.unlink()
        target.symlink_to("/tmp")
    elif behavior != "missing_candidate":
        with target.open("ab") as stream:
            stream.write(b"\n// RW0-D1 artificial bounded candidate\n")
        captured_at = _observed_now()
    completed_at = _observed_now()
    events = [("worker_started", started_at)]
    if captured_at is not None:
        events.append(("candidate_captured", captured_at))
    events.append(("worker_completed", completed_at))
    observations = tuple(
        WorkerObservationV1.create(
            observation_ref=f"observation.d1.{kind.replace('_', '-')}",
            source_kind="worker", source_ref="worker.d1.fake",
            source_invocation_ref="invocation.d1.fake",
            observation_kind=kind,
            outcome={"worker_started": "started", "candidate_captured": "captured",
                     "worker_completed": "completed"}[kind],
            reason_code="reason.none",
            evidence_refs=["evidence.d1.fake"],
            observed_at=observed_at,
            delivery=delivery, author_command=command,
            attempt_fence=attempt, author_effect_fence=effect,
            effect_fence=effect,
        )
        for kind, observed_at in events
    )
    result = RW0WireWorkerResultV1._create(observations)
    os.write(1, encode_wire_result_frame(
        result=result, command=command, delivery=delivery,
        attempt_fence=attempt, author_effect_fence=effect,
    ))
    return 0


def _entry() -> int:
    try:
        return _main()
    except Exception:
        return 4


if __name__ == "__main__":
    raise SystemExit(_entry())
