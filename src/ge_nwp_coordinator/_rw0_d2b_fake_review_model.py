"""One deterministic, separate-process cognitive proposal over supplied D2 evidence."""

from __future__ import annotations

from datetime import datetime, timezone
import os
import sys

from ._rw0_d2b_model_frames import decode_model_request, encode_model_response


def _decision(supplies: list[dict[str, object]]) -> tuple[str, str, int | None]:
    values = [entry["typed_canonical_value"] for entry in supplies]
    validation, review = values[2], values[3]
    standing, risk, authority, stop, ceiling = values[4:]
    if stop.get("global_stop_state") != "clear":
        return "block", "global_stop_active", 7
    if (authority.get("status") != "verified"
            or authority.get("revocation_status") != "unrevoked"):
        return "block", "authority_not_current", 6
    if ceiling.get("result") != "compliant":
        return "block", "effect_ceiling_not_compliant", 8
    if any(entry.get("result") != "permit" for entry in standing.get("entries", [])):
        return "block", "standing_policy_not_permitted", 4
    if any(entry.get("result") != "permit" for entry in risk.get("entries", [])):
        return "block", "risk_lane_not_permitted", 5
    if review.get("separation_status") != "separate":
        return "block", "reviewer_separation_not_proved", 3
    if (validation.get("result") == "terminal_failure"
            or review.get("result") == "terminal_reject"):
        return "terminal_reject", "terminal_source_result", (
            2 if validation.get("result") == "terminal_failure" else 3
        )
    if (validation.get("result") == "replan_required"
            or review.get("result") == "replan_required"):
        return "replan", "source_requires_replan", (
            2 if validation.get("result") == "replan_required" else 3
        )
    if (validation.get("result") == "repairable_failure"
            or review.get("result") == "repair_required"):
        return "repair_candidate", "source_requires_repair", (
            2 if validation.get("result") == "repairable_failure" else 3
        )
    if validation.get("result") == "passed" and review.get("result") == "passed":
        return "accept_candidate", "source_checks_passed", None
    return "block", "source_result_unknown", (
        2 if validation.get("result") != "passed" else 3
    )


def _main() -> int:
    request = decode_model_request(sys.stdin.buffer.read(256 * 1024 + 1))
    context = request["input_context"]
    supply = request["evidence_supply"]
    role_supplies = supply["role_supplies"]
    recommendation, reason, index = _decision(role_supplies)
    findings = []
    if index is not None:
        entry = role_supplies[index]
        findings.append({
            "finding_ref": "finding.d2." + entry["role"].replace("_", "-"),
            "source_role": entry["role"],
            "source_value_ref": entry["typed_value_ref"],
            "source_value_digest": entry["typed_value_digest"],
            "reason_code": reason,
        })
    response = {
        "schema_id": "governed-execution.nwp-d2-review-model-response.v1",
        "invocation_ref": request["invocation_ref"],
        "input_digest": request["input_digest"],
        "input_context_ref": context["input_context_ref"],
        "input_context_digest": context["input_context_digest"],
        "supply_ref": supply["supply_ref"],
        "supply_digest": supply["supply_digest"],
        "recommendation": recommendation,
        "reason_code": reason,
        "findings": findings,
        "completed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    os.write(1, encode_model_response(response))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except Exception:
        raise SystemExit(4) from None
