"""Artificial, separate-process validation of reconstructed candidate bytes."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import sys

from ._rw0_d2a_process_frames import (
    decode_checking_request, encode_checking_response,
)
from ._rw0_d2a_workspace import read_exact_reconstruction


def _main() -> int:
    request = decode_checking_request("validator", sys.stdin.buffer.read(256 * 1024 + 9))
    files = read_exact_reconstruction(Path.cwd())
    digests = [hashlib.sha256(blob).hexdigest() for _path, blob in files]
    if any(
        entry["path"] != path or entry["length"] != len(blob)
        or entry["sha256"] != digest
        for entry, (path, blob), digest in zip(request["files"], files, digests, strict=True)
    ):
        return 2
    try:
        architecture, plan, contract = (blob.decode("utf-8") for _path, blob in files)
    except UnicodeError:
        outcome, reason = "inconclusive", "validation_inconclusive"
    else:
        if "VALIDATION-TERMINAL" in contract:
            outcome, reason = "failed", "validation_failed_terminal"
        elif "VALIDATION-REPLAN" in contract:
            outcome, reason = "failed", "validation_failed_replan_required"
        elif "VALIDATION-UNCLASSIFIED" in contract:
            outcome, reason = "failed", "validation_failed_unclassified"
        elif ("func TestContract()" in contract
                and "RW0-D1 artificial bounded candidate" in contract
                and architecture.strip() and plan.strip()):
            outcome, reason = "passed", "validation_passed"
        else:
            outcome, reason = "failed", "validation_failed_repairable"
    response = {
        "schema_id": "governed-execution.nwp-d2-validator-response.v1",
        "role": "validator", "invocation_ref": request["invocation_ref"],
        "command_digest": request["command_digest"],
        "effect_fence_ref": request["effect_fence_ref"],
        "effect_fence_digest": request["effect_fence_digest"],
        "delivery_attempt_ref": request["delivery_attempt_ref"],
        "capsule_manifest_ref": request["capsule_manifest_ref"],
        "portable_capsule_digest": request["portable_capsule_digest"],
        "outcome": outcome, "reason_code": reason,
        "source_ref": "validator.d2.fake", "evidence_ref": "evidence.d2.validation",
        "observed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file_digests": digests,
    }
    os.write(1, encode_checking_response("validator", response))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except Exception:
        raise SystemExit(4) from None
