"""Independent exact-frame and real child checks for D2 proof roles."""

from __future__ import annotations

import hashlib
import struct

import pytest

from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture, run_rw0_d1_offline
from ge_nwp_coordinator._rw0_d1_process_supervisor import run_fake_module
from ge_nwp_coordinator._rw0_d2a_process_frames import (
    D2CheckingFrameError, decode_checking_request, decode_checking_response,
    encode_checking_request,
)
from ge_nwp_coordinator._rw0_d2a_workspace import D2Reconstruction
from ge_nwp_coordinator._rw0_d2a_evidence import normalize_checking_evidence
from ge_nwp_coordinator._rw0_d2b_model_frames import (
    D2ReviewModelFrameError, decode_model_request, decode_model_response,
    encode_model_request, encode_model_response, model_input_digest,
)
from test_rw0_d1_offline_integration import work_spec
from test_rw0_d2_bound_effect_contracts import _bound_command


def _request(role: str, command: object) -> dict[str, object]:
    return {
        "schema_id": f"governed-execution.nwp-d2-{role}-request.v1",
        "role": role,
        "invocation_ref": f"invocation.d2.{role}",
        "command_digest": command.command_digest,
        "effect_intent_ref": command.effect_intent_ref,
        "effect_fence_ref": command.effect_fence_ref,
        "effect_fence_digest": command.effect_fence.effect_fence_digest,
        "delivery_attempt_ref": command.delivery_attempt_ref,
        "capsule_manifest_ref": command.capsule_manifest_ref,
        "portable_capsule_digest": command.portable_capsule_digest,
        "requirement_ref": command.requirement_ref,
        "requirement_safe_digest": command.requirement_safe_digest,
        "files": [
            {"path": path, "length": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}
            for path, blob in command.after_blob_entries
        ],
    }


def test_checking_frames_and_two_real_processes() -> None:
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as run:
        for role, effect_class in (("validator", "validate_candidate"),
                                   ("reviewer", "review_candidate")):
            command = _bound_command(run.handback, work, effect_class)
            with pytest.raises(D2CheckingFrameError):
                decode_checking_request(role, encode_checking_request(role, _request(role, command)) + b"x")
            with D2Reconstruction(
                capture=run.handback.capture,
                capsule_manifest=run.handback.capsule_manifest,
                author_command=run.handback.author_command,
            ) as reconstruction:
                frame = encode_checking_request(role, _request(role, command))
                observed = run_fake_module(
                    f"ge_nwp_coordinator._rw0_d2a_fake_{role}", frame,
                    cwd=reconstruction.root, output_limit=64 * 1024 + 8,
                )
                assert observed.clean_success, observed.reason
                response = decode_checking_response(role, observed.stdout)
                assert response["outcome"] == "passed"
                assert tuple(response["file_digests"]) == reconstruction.digests
                assert response["effect_fence_digest"] == command.effect_fence.effect_fence_digest
                evidence = normalize_checking_evidence(
                    role=role, process=observed, command=command,
                    author_command=run.handback.author_command,
                    adapter_exit=run.handback.adapter_exit,
                )
                assert evidence.observation.outcome == "passed"
                evidence.validate()
                reconstruction.verify()


def test_review_model_frame_is_closed_and_response_authored() -> None:
    roles = (
        "candidate_capsule", "worker_result", "validation_result",
        "independent_review", "standing_policy", "risk_lane",
        "authority_currentness_attestation", "global_stop", "effect_ceiling",
    )
    context = {
        "schema_id": "governed-execution.nwp-post-execution-semantic-review-context.v1",
        "input_context_ref": "context.test", "input_context_digest": "1" * 64,
    }
    supply = {
        "schema_id": "governed-execution.nwp-post-execution-evidence-supply.v2",
        "input_context": context, "supply_ref": "supply.test",
        "supply_digest": "2" * 64,
        "role_supplies": [{"role": role} for role in roles],
    }
    invocation = "source-invocation.d2.fake-review"
    request = {
        "schema_id": "governed-execution.nwp-d2-review-model-request.v1",
        "invocation_ref": invocation, "input_context": context,
        "evidence_supply": supply,
        "input_digest": model_input_digest(invocation, context, supply),
    }
    frame = encode_model_request(request)
    assert decode_model_request(frame) == request
    assert b"expected_recommendation" not in frame
    with pytest.raises(D2ReviewModelFrameError):
        decode_model_request(frame + b"x")
    with pytest.raises(D2ReviewModelFrameError):
        encode_model_request({**request, "expected_recommendation": "accept_candidate"})
    with pytest.raises(D2ReviewModelFrameError):
        encode_model_request({**request, "input_digest": "0" * 64})
    swapped_supply = {**supply, "role_supplies": [
        supply["role_supplies"][1], supply["role_supplies"][0],
        *supply["role_supplies"][2:],
    ]}
    with pytest.raises(D2ReviewModelFrameError):
        encode_model_request({**request, "evidence_supply": swapped_supply,
                              "input_digest": model_input_digest(
                                  invocation, context, swapped_supply,
                              )})
    payload = frame[8:].replace(b'"invocation_ref":', b'"invocation_ref":"duplicate","invocation_ref":', 1)
    duplicate = frame[:4] + struct.pack(">I", len(payload)) + payload
    with pytest.raises(D2ReviewModelFrameError):
        decode_model_request(duplicate)
    response = {
        "schema_id": "governed-execution.nwp-d2-review-model-response.v1",
        "invocation_ref": invocation, "input_digest": request["input_digest"],
        "input_context_ref": context["input_context_ref"],
        "input_context_digest": context["input_context_digest"],
        "supply_ref": supply["supply_ref"], "supply_digest": supply["supply_digest"],
        "recommendation": "accept_candidate", "reason_code": "source_checks_passed",
        "findings": [], "completed_at": "2026-10-18T00:00:00Z",
    }
    encoded = encode_model_response(response)
    assert decode_model_response(encoded)["recommendation"] == "accept_candidate"
    with pytest.raises(D2ReviewModelFrameError):
        encode_model_response({**response, "expected_recommendation": "block"})
    with pytest.raises(D2ReviewModelFrameError):
        decode_model_response(encoded[:-1] + b"x")
