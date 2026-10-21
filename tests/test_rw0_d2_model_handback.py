"""D2 B uses nine real supplied owners and one separate fake model process."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import tempfile

import pytest

from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture, run_rw0_d1_offline
from ge_nwp_coordinator._rw0_d1_process_supervisor import run_fake_module
from ge_nwp_coordinator._rw0_d2a_offline import run_d2a_checked_evidence
from ge_nwp_coordinator._rw0_d2b_model_frames import (
    decode_model_response, encode_model_request, encode_model_response,
    model_input_digest,
)
from ge_nwp_coordinator._rw0_d2b_model_input import (
    construct_d2b_context, construct_d2b_evidence_supply,
    current_stop_and_ceiling,
)
from ge_nwp_coordinator._rw0_d2b_proposal import normalize_d2_model_response
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_rw0_d1_offline_integration import work_spec


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_nine_role_model_process_and_common_post_phase_values() -> None:
    work = work_spec()
    fixture = artificial_fixture(work)
    with run_rw0_d1_offline(work, fixture) as run:
        bundle = run_d2a_checked_evidence(run, work, fixture)
        with acquire_sqlite_writer_session(run.location) as writer:
            current = writer._read_rw0_d2_current_owner_snapshot(run.handback.phase_basis)
        stop, ceiling = current_stop_and_ceiling(checkpoint=bundle.checkpoint, current=current)
        _lineage, context, safe, manifest = construct_d2b_context(
            checkpoint=bundle.checkpoint, current=current, stop=stop, ceiling=ceiling,
        )
        supply = construct_d2b_evidence_supply(
            checkpoint=bundle.checkpoint, current=current, context=context,
            safe=safe, manifest=manifest, stop=stop, ceiling=ceiling,
        )
        invocation_ref = "source-invocation.d2.fake-review"
        request = encode_model_request({
            "schema_id": "governed-execution.nwp-d2-review-model-request.v1",
            "invocation_ref": invocation_ref, "input_context": context.to_mapping(),
            "evidence_supply": supply.to_mapping(),
            "input_digest": model_input_digest(
                invocation_ref, context.to_mapping(), supply.to_mapping(),
            ),
        })
        started = _now()
        with tempfile.TemporaryDirectory(prefix="d2-model-") as root:
            process = run_fake_module(
                "ge_nwp_coordinator._rw0_d2b_fake_review_model",
                request, cwd=Path(root), output_limit=64 * 1024 + 8,
            )
        assert process.clean_success and process.cleanup_complete
        response = decode_model_response(process.stdout)
        source, artifact, binding, projection, evidence_bindings, evidence_set, proposal, model_binding = (
            normalize_d2_model_response(
                response=response, process=process, context=context,
                input_safe=safe, manifest=manifest, supply=supply, started_at=started,
            )
        )
        assert artifact.recommendation == "accept_candidate"
        assert proposal.recommendation == artifact.recommendation
        assert proposal.proposal_phase == "post_execution_semantic_review"
        assert len(evidence_bindings) == len(evidence_set.entries) == 9
        assert source.artifact_digest == artifact.artifact_digest
        assert binding.safe_projection_digest == projection.safe_projection_digest
        assert model_binding.proposal_digest == proposal.proposal_digest
        with pytest.raises(ValueError, match="^invalid_d2_model_proposal$"):
            normalize_d2_model_response(
                response={**response, "record_digest": "0" * 64},
                process=process, context=context, input_safe=safe,
                manifest=manifest, supply=supply, started_at=started,
            )
        wrong_content = {name: value for name, value in response.items()
                         if name != "record_digest"}
        wrong_content.update(recommendation="block", reason_code="source_result_unknown")
        wrong_frame = encode_model_response(wrong_content)
        wrong_response = decode_model_response(wrong_frame)
        with pytest.raises(ValueError, match="^invalid_d2_model_proposal$"):
            normalize_d2_model_response(
                response=wrong_response, process=process, context=context,
                input_safe=safe, manifest=manifest, supply=supply,
                started_at=started,
            )
        with pytest.raises(ValueError, match="^invalid_d2_model_proposal$"):
            normalize_d2_model_response(
                response=wrong_response, process=replace(process, stdout=wrong_frame),
                context=context, input_safe=safe, manifest=manifest,
                supply=supply, started_at=started,
            )
