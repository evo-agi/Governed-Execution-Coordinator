"""Single-input offline D2 composition over the existing guarded owners."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
from typing import Callable

from ._rw0_d1_offline import D1ArtificialFixture, run_rw0_d1_offline
from ._rw0_d1_process_supervisor import D1ProcessOutcome, run_fake_module
from ._rw0_d2a_offline import _D2AStop, run_d2a_checked_evidence
from ._rw0_d2b_model_frames import (
    decode_model_response, encode_model_request, model_input_digest,
)
from ._rw0_d2b_model_input import (
    construct_d2b_context, construct_d2b_evidence_supply,
    current_stop_and_ceiling,
)
from ._rw0_d2b_proposal import normalize_d2_model_response
from ._rw0_d2_handback import RW0D2OfflineRun, RW0D2PreadmissionHandbackV1
from ._worker_execution_semantic_values import WorkSpecV1
from .sqlite_writer_session import acquire_sqlite_writer_session

__all__: tuple[str, ...] = ()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_rw0_d2_offline(
    work_spec: WorkSpecV1, fixture: D1ArtificialFixture,
    *, cancelled: Callable[[], bool] | None = None,
) -> RW0D2OfflineRun:
    """Execute one D1, A evidence closure, and one bounded B model handback."""
    d1_run = run_rw0_d1_offline(work_spec, fixture, cancelled=cancelled)
    facts: dict[str, object] = {
        "d1_handback": d1_run.handback,
        "committed_bound_effects": (), "checked_admissions": (),
        "child_outcomes": (),
    }
    try:
        if d1_run.handback.status != "capsule_ready":
            handback = RW0D2PreadmissionHandbackV1(
                status="stopped", reason="d1_stopped", **facts,
            )
            return RW0D2OfflineRun(d1_run, handback)
        try:
            bundle = run_d2a_checked_evidence(
                d1_run, work_spec, fixture, cancelled=cancelled,
            )
        except _D2AStop as stop:
            facts.update(
                committed_bound_effects=stop.bound_effects,
                checked_admissions=stop.checked_families,
                child_outcomes=stop.child_outcomes,
            )
            handback = RW0D2PreadmissionHandbackV1(
                status=("cleanup_unresolved" if stop.reason.endswith("cleanup_unresolved")
                        else "stopped"), reason=stop.reason, **facts,
            )
            return RW0D2OfflineRun(d1_run, handback)
        checkpoint = bundle.checkpoint
        facts.update(
            committed_bound_effects=checkpoint.bound_effects,
            checked_admissions=checkpoint.admitted_families,
            child_outcomes=(checkpoint.validator_process, checkpoint.reviewer_process),
            evidence_checkpoint=checkpoint,
        )
        try:
            # No B source is constructed while a writer session remains open.
            with acquire_sqlite_writer_session(d1_run.location) as writer:
                current = writer._read_rw0_d2_current_owner_snapshot(
                    d1_run.handback.phase_basis,
                )
            stop, ceiling = current_stop_and_ceiling(
                checkpoint=checkpoint, current=current,
            )
            _lineage, context, input_safe, manifest = construct_d2b_context(
                checkpoint=checkpoint, current=current, stop=stop, ceiling=ceiling,
            )
            supply = construct_d2b_evidence_supply(
                checkpoint=checkpoint, current=current, context=context,
                safe=input_safe, manifest=manifest, stop=stop, ceiling=ceiling,
            )
            facts.update(input_context=context, evidence_supply=supply)
            invocation_ref = "source-invocation.d2.fake-review"
            request = encode_model_request({
                "schema_id": "governed-execution.nwp-d2-review-model-request.v1",
                "invocation_ref": invocation_ref,
                "input_context": context.to_mapping(),
                "evidence_supply": supply.to_mapping(),
                "input_digest": model_input_digest(
                    invocation_ref, context.to_mapping(), supply.to_mapping(),
                ),
            })
            started_at = _now()
            scratch = tempfile.TemporaryDirectory(prefix="rw0-d2-model-")
            scratch_cleanup_failed = False
            try:
                process = run_fake_module(
                    "ge_nwp_coordinator._rw0_d2b_fake_review_model",
                    request, cwd=Path(scratch.name), output_limit=64 * 1024 + 8,
                    cancelled=cancelled,
                )
                process.validate()
                facts["model_process"] = process
                facts["child_outcomes"] = (
                    checkpoint.validator_process, checkpoint.reviewer_process, process,
                )
            finally:
                try:
                    scratch.cleanup()
                except Exception:
                    scratch_cleanup_failed = True
            if scratch_cleanup_failed:
                raise ValueError("model_workspace_cleanup_unresolved")
            if not process.cleanup_complete:
                raise ValueError("model_process_cleanup_unresolved")
            if not process.clean_success:
                raise ValueError("model_process_failed")
            response = decode_model_response(process.stdout)
            (source, artifact, binding, projection, evidence_bindings,
             evidence_set, proposal, model_binding) = normalize_d2_model_response(
                response=response, process=process, context=context,
                input_safe=input_safe, manifest=manifest, supply=supply,
                started_at=started_at,
            )
            facts.update(
                model_input_binding=model_binding,
                model_source_invocation=source,
                private_artifact=artifact, artifact_binding=binding,
                safe_projection=projection, evidence_bindings=evidence_bindings,
                evidence_set=evidence_set, proposal=proposal,
            )
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception as error:
            reason = str(error)
            if reason not in {
                "model_process_cleanup_unresolved", "model_process_failed",
                "model_workspace_cleanup_unresolved",
            }:
                reason = "model_input_or_normalization_failed"
            handback = RW0D2PreadmissionHandbackV1(
                status=("cleanup_unresolved" if reason.endswith("cleanup_unresolved")
                        else "stopped"), reason=reason, **facts,
            )
            return RW0D2OfflineRun(d1_run, handback)
        handback = RW0D2PreadmissionHandbackV1(
            status="preadmission_ready", reason="complete", **facts,
        )
        return RW0D2OfflineRun(d1_run, handback)
    except BaseException:
        d1_run.close()
        raise
