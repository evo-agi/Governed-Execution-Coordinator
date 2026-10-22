"""One artificial, private RW0-D1 invocation through current durable owners."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import math
from pathlib import Path
import shutil
import tempfile
from typing import Callable

from ._development_author_effect_establishment_contracts import (
    _development_author_effect_establishment_write_plan,
    _development_effect_authorization_safe_binding,
    _development_review_requirement_evidence,
    _development_validation_requirement_evidence,
)
from ._development_program_initialization_contracts import (
    _development_program_initialization_write_plan,
)
from ._rw0_c1_semantic_values import RW0C1RecoveryProbeV1
from ._rw0_d1_capsule import build_candidate_capsule, verify_candidate_capsule
from ._rw0_d1_handback import (
    RW0D1HandbackV1, RW0D1OfflineRun, _adapter_invocation_ref,
)
from ._rw0_d1_pre_execution import (
    _AuthorContext, _build_bundle, make_phase_command,
    section41_disposition_identity_and_digest,
)
from ._rw0_d1_process_frames import (
    D1FrameError, decode_planner_response, encode_planner_request,
    encode_worker_launch,
)
from ._rw0_d1_process_supervisor import D1ProcessOutcome, run_fake_module
from ._rw0_d1_workspace import D1Workspace, D1WorkspaceError, PATHS
from ._rw0_wire_protocol_values import (
    classify_wire_process_result, decode_wire_result_frame,
    encode_wire_command_frame,
)
from ._sqlite_development_author_effect_establishment import (
    _reduce_development_author_effect_establishment_command,
)
from ._sqlite_development_program_initialization import (
    _reduce_development_program_initialization_command,
)
from ._worker_execution_semantic_values import (
    AttemptFenceV1, CeilingsV1, WorkSpecV1, WorkerObservationV1,
)
from .sqlite_errors import SQLiteMutationStoreError
from .sqlite_location import CoordinatorStateLocation
from .sqlite_migration import initialize_database
from .sqlite_writer_session import acquire_sqlite_writer_session


@dataclass(frozen=True, slots=True, repr=False)
class D1ArtificialFixture:
    work_spec: WorkSpecV1
    base_entries: tuple[tuple[str, bytes, str], ...]
    planner_behavior: str = "normal"
    worker_behavior: str = "normal"
    planner_timeout: float = 5.0
    worker_timeout: float = 5.0

    def __post_init__(self) -> None:
        if (type(self.work_spec) is not WorkSpecV1
                or type(self.base_entries) is not tuple
                or len(self.base_entries) != 3
                or any(type(entry) is not tuple or len(entry) != 3
                       for entry in self.base_entries)
                or tuple(name for name, _blob, _mode in self.base_entries) != PATHS
                or any(type(name) is not str or type(blob) is not bytes
                           or len(blob) > 1_048_576 or type(mode) is not str
                           or mode != "100644"
                           for name, blob, mode in self.base_entries)
                or type(self.planner_behavior) is not str
                or self.planner_behavior not in {
                    "normal", "malformed", "oversized", "trailing", "nonzero",
                    "timeout", "stderr_limit", "defer",
                }
                or type(self.worker_behavior) is not str
                or self.worker_behavior not in {
                    "normal", "malformed", "nonzero", "timeout", "stderr_limit",
                    "missing_candidate", "extra_path", "unsafe_path",
                }
                or any(type(limit) not in (int, float) or not math.isfinite(limit)
                       or not 0 < limit <= 30
                       for limit in (self.planner_timeout, self.worker_timeout))):
            raise ValueError("invalid_d1_fixture")

    def base_blobs(self) -> dict[str, bytes]:
        return {name: blob for name, blob, _mode in self.base_entries}


def artificial_fixture(work_spec: WorkSpecV1, *, planner_behavior: str = "normal",
                       worker_behavior: str = "normal") -> D1ArtificialFixture:
    """Closed artificial base; the WorkSpec supplies its preassigned Git coordinate."""
    return D1ArtificialFixture(
        work_spec,
        (
            (PATHS[0], b"# Artificial integration architecture\n", "100644"),
            (PATHS[1], b"# Artificial plan\n", "100644"),
            (PATHS[2], b"package contracts\n\nfunc TestContract() {}\n", "100644"),
        ),
        planner_behavior, worker_behavior,
    )


class _D1Stop(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason


def _author_ingress(work_spec: WorkSpecV1, genesis_plan: object) -> dict[str, object]:
    aggregate = CeilingsV1.create(
        max_active_invocations=1, max_candidate_bytes=1_048_576,
        max_changed_files=3, max_cost_microusd=100_000, max_cpu_seconds=600,
        max_deliveries=3, max_deployments=0, max_local_commits=1,
        max_memory_bytes=2_147_483_648, max_merges=0,
        max_model_input_tokens=200_000, max_model_output_tokens=50_000,
        max_pull_requests=0, max_pushes=0, max_wall_seconds=1_800,
    )
    effect = CeilingsV1.create(**{
        **aggregate.to_mapping(), "max_deliveries": 1, "max_local_commits": 0,
    })
    attempt = AttemptFenceV1.create(
        attempt_fence_ref="attempt-fence.d1",
        parent_standing_grant_ref="standing-grant.d1",
        parent_standing_grant_digest="3" * 64,
        attempt_authorization_ref="attempt-authorization.d1",
        attempt_authorization_digest="4" * 64,
        program_ref=work_spec.program_ref,
        program_version_ref=work_spec.program_version_ref,
        accepted_intent_revision_ref=work_spec.accepted_intent_revision_ref,
        work_item_ref=work_spec.work_item_ref,
        work_item_revision_ref=work_spec.work_item_revision_ref,
        semantic_attempt_ref="semantic-attempt.d1",
        repository_ref=work_spec.repository_ref,
        base_git_oid=work_spec.base_git_oid,
        path_ceiling=list(PATHS),
        allowed_effect_classes=[
            "author_candidate", "cancel_effect", "local_git_commit",
            "review_candidate", "validate_candidate",
        ],
        aggregate_ceilings=aggregate, expires_at="2099-01-01T00:00:00Z",
        global_stop_ref="global-stop-clear", global_stop_version=0,
    )
    validation = _development_validation_requirement_evidence(
        requirement_ref=work_spec.validation_requirement_ref,
        requirement_digest="6" * 64, work_spec_ref=work_spec.work_spec_ref,
        work_spec_digest=work_spec.work_spec_digest,
    )
    review = _development_review_requirement_evidence(
        requirement_ref=work_spec.review_requirement_ref,
        requirement_digest="7" * 64, work_spec_ref=work_spec.work_spec_ref,
        work_spec_digest=work_spec.work_spec_digest,
    )
    binding = _development_effect_authorization_safe_binding(
        parent_standing_grant_ref=attempt.parent_standing_grant_ref,
        parent_standing_grant_digest=attempt.parent_standing_grant_digest,
        effect_authorization_ref="effect-authorization.d1",
        effect_authorization_digest="5" * 64,
        attempt_fence_ref=attempt.attempt_fence_ref,
        attempt_fence_digest=attempt.attempt_fence_digest,
        semantic_attempt_ref=attempt.semantic_attempt_ref,
        effect_intent_ref="effect-intent.d1",
        effect_class="author_candidate", path_ceiling=attempt.path_ceiling,
        effect_ceilings=effect, expires_at="2099-01-01T00:00:00Z",
        global_stop_ref=attempt.global_stop_ref,
        global_stop_version=attempt.global_stop_version,
    )
    return {
        "mutation_ref": "mutation-author.d1",
        "program_ref": work_spec.program_ref,
        "program_version_ref": work_spec.program_version_ref,
        "program_version_number": 1,
        "accepted_intent_revision_ref": work_spec.accepted_intent_revision_ref,
        "work_item_ref": work_spec.work_item_ref,
        "work_item_revision_ref": work_spec.work_item_revision_ref,
        "basis_decision_ref": "decision.d1",
        "basis_decision_digest": genesis_plan.initialize_decision.decision_digest,
        "semantic_attempt_ref": "semantic-attempt.d1",
        "candidate_ref": "candidate.d1",
        "attempt_number": 1,
        "attempt_fence_ref": attempt.attempt_fence_ref,
        "effect_intent_ref": "effect-intent.d1",
        "effect_fence_ref": "effect-fence.d1",
        "command_ref": "command.d1",
        "authority_evaluation_ref": "authority-evaluation.d1",
        "delivery_attempt_ref": "delivery-attempt.d1",
        "adapter_safe_correlation_ref": "adapter-correlation.d1",
        "coding_global_stop_ref": "global-stop-clear",
        "coding_global_stop_version": 0,
        "work_spec": work_spec,
        "validation_requirement_evidence": validation,
        "review_requirement_evidence": review,
        "attempt_fence": attempt,
        "effect_authorization_safe_binding": binding,
    }


def _call_durable(writer: object, location: CoordinatorStateLocation,
                  method: str, args: tuple[object, ...], kwargs: dict[str, object],
                  recovery_method: str, recovery_arg: object,
                  *, replay_after_recovery: bool = False) -> tuple[object, object]:
    try:
        return getattr(writer, method)(*args, **kwargs), writer
    except SQLiteMutationStoreError as error:
        if error.error_class != "commit_outcome_unknown":
            raise _D1Stop("durable_conflict") from None
    try:
        writer.close()
    except Exception:
        raise _D1Stop("process_cleanup_unresolved") from None
    fresh = acquire_sqlite_writer_session(location)
    try:
        recovery = getattr(fresh, recovery_method)(recovery_arg)
        classification = getattr(recovery, "classification",
                                 getattr(recovery, "disposition", None))
        if classification != "committed_exact":
            raise _D1Stop("durable_commit_unresolved")
        result = getattr(recovery, "committed_result", None)
        if replay_after_recovery:
            result = getattr(fresh, method)(*args, **kwargs)
        if result is None:
            raise _D1Stop("durable_commit_unresolved")
        return result, fresh
    except BaseException:
        fresh.close()
        raise


def _process_reason(prefix: str, reason: str) -> str:
    return {
        "start_failed": prefix + "_start", "invalid_input": prefix + "_start",
        "output_limit": prefix + "_limit", "stderr_limit": prefix + "_limit",
        "nonzero_exit": prefix + "_exit", "deadline": prefix + "_deadline",
        "cancelled": prefix + "_cancelled",
        "cleanup_unresolved": "process_cleanup_unresolved",
    }.get(reason, prefix + "_exit")


def _close_writer_before_child(writer: object) -> None:
    try:
        writer.close()
    except Exception:
        raise _D1Stop("process_cleanup_unresolved") from None


def run_rw0_d1_offline(
    work_spec: WorkSpecV1, fixture: D1ArtificialFixture,
    *, cancelled: Callable[[], bool] | None = None,
) -> RW0D1OfflineRun:
    facts: dict[str, object] = {}
    root: Path | None = None
    location: CoordinatorStateLocation | None = None
    writer: object | None = None
    workspace: D1Workspace | None = None
    scratch: tempfile.TemporaryDirectory[str] | None = None
    reason = "complete"
    workspace_cleaned = False
    invalid_process = False
    try:
        if (type(work_spec) is not WorkSpecV1 or type(fixture) is not D1ArtificialFixture
                or fixture.work_spec.to_mapping() != work_spec.to_mapping()
                or tuple(work_spec.authorized_paths) != PATHS
                or work_spec.repository_ref != "repository.execution-substrate"
                or (cancelled is not None and not callable(cancelled))):
            raise _D1Stop("invalid_input")
        base = fixture.base_blobs()
        root = Path(tempfile.mkdtemp(prefix="rw0-d1-state-"))
        location = CoordinatorStateLocation.from_trusted_root(root)
        initialize_database(location)
        writer = acquire_sqlite_writer_session(location)
        genesis = _reduce_development_program_initialization_command(
            mutation_ref="mutation-genesis.d1",
            program_ref=work_spec.program_ref,
            program_version_ref=work_spec.program_version_ref,
            accepted_intent_revision_ref=work_spec.accepted_intent_revision_ref,
            decision_ref="decision.d1",
            preassigned_semantic_attempt_ref="semantic-attempt.d1",
            preassigned_candidate_ref="candidate.d1",
            coding_global_stop_ref="global-stop-clear",
            coding_global_stop_version=0,
            source_intent_ref="source-intent.d1", source_intent_digest="1" * 64,
            work_spec=work_spec,
        )
        program_result, writer = _call_durable(
            writer, location, "_apply_development_program_initialization",
            (genesis,), {}, "_resolve_development_program_initialization_commit_outcome",
            genesis,
        )
        facts["program_result"] = program_result
        genesis_plan = _development_program_initialization_write_plan(
            genesis, program_result.transaction_timestamp,
        )
        ingress = _author_ingress(work_spec, genesis_plan)
        expected_author_command = _reduce_development_author_effect_establishment_command(
            **ingress,
        )
        author_result, writer = _call_durable(
            writer, location, "_establish_development_author_effect_intent",
            (), ingress, "_resolve_development_author_effect_establishment_commit_outcome",
            expected_author_command,
        )
        facts["author_result"] = author_result
        if author_result.command_digest != expected_author_command.command_digest:
            raise _D1Stop("durable_conflict")
        facts["author_command"] = expected_author_command
        author_plan = _development_author_effect_establishment_write_plan(
            expected_author_command, author_result.transaction_timestamp,
        )
        _close_writer_before_child(writer)
        writer = None
        scratch = tempfile.TemporaryDirectory(prefix="rw0-d1-planner-")
        planner_request = encode_planner_request({
            "objective": work_spec.objective,
            "requirements": list(work_spec.requirements),
            "exclusions": list(work_spec.exclusions),
            "path_ordinals": [0, 1, 2], "action": "modify_authorized_path",
            "behavior": fixture.planner_behavior,
        })
        planner_process = run_fake_module(
            "ge_nwp_coordinator._rw0_d1_fake_planner", planner_request,
            cwd=Path(scratch.name), timeout_seconds=fixture.planner_timeout,
            output_limit=64 * 1024 + 8, cancelled=cancelled,
        )
        facts["planner_process"] = planner_process
        try:
            if type(planner_process) is not D1ProcessOutcome:
                raise ValueError("invalid_d1_process_outcome")
            planner_process.validate()
        except ValueError:
            invalid_process = True
            raise
        if planner_process.reason in {"start_failed", "invalid_input"}:
            raise _D1Stop("planner_start")
        if not planner_process.cleanup_complete:
            raise _D1Stop("planner_cleanup_unresolved")
        if planner_process.reason != "ok":
            raise _D1Stop(_process_reason("planner", planner_process.reason))
        try:
            planner = decode_planner_response(planner_process.stdout)
        except D1FrameError:
            raise _D1Stop("planner_frame") from None
        if planner["action"] != "modify_authorized_path" or planner["target_ordinal"] != 2:
            raise _D1Stop("planner_frame")
        scratch.cleanup()
        scratch = None
        bundle = _build_bundle(
            _AuthorContext(expected_author_command, author_result),
            marker="d1", readiness_present=False, planner=planner,
            program_revision=genesis_plan.program_head.head_revision,
            work_revision=genesis_plan.work_item_head.head_revision,
        )
        facts["selected_bundle"] = bundle
        identity, digest = section41_disposition_identity_and_digest(
            bundle, mutation_ref="cognitive-mutation.d1",
            disposition_ref="planning-disposition.d1",
        )
        writer = acquire_sqlite_writer_session(location)
        probe = writer._prepare_pre_execution_plan_disposition_recovery_probe(
            "cognitive-mutation.d1", digest, bundle, identity,
        )
        selection, writer = _call_durable(
            writer, location, "_record_pre_execution_plan_disposition",
            ("cognitive-mutation.d1", digest, bundle, identity, probe), {},
            "_resolve_pre_execution_plan_disposition_commit_outcome", probe,
        )
        facts["section41_result"] = selection
        if selection.disposition != "selected_for_dispatch_gates":
            raise _D1Stop("nonselection")
        basis, phase_command = make_phase_command(
            bundle=bundle, disposition_result=selection,
            genesis_plan=genesis_plan, author_plan=author_plan,
            work_spec=work_spec,
        )
        facts["phase_basis"] = basis
        phase_probe = RW0C1RecoveryProbeV1(
            "establish_rw0_phase", phase_command.mutation_ref,
            phase_command.command_digest, basis.basis_ref, basis.basis_digest,
            k8=tuple(member for _name, member in basis.selection_key),
        )
        phase_result, writer = _call_durable(
            writer, location, "_establish_rw0_phase", (phase_command,), {},
            "_resolve_rw0_c1_phase_establishment_commit_outcome", phase_probe,
            replay_after_recovery=True,
        )
        facts["phase_result"] = phase_result
        _close_writer_before_child(writer)
        writer = None
        workspace = D1Workspace(base)
        worker_command = expected_author_command.worker_command
        delivery = expected_author_command.delivery_envelope
        attempt = expected_author_command.attempt_fence
        effect_fence = expected_author_command.effect_fence
        wire_command = encode_wire_command_frame(
            command=worker_command, delivery=delivery,
            attempt_fence=attempt, author_effect_fence=effect_fence,
        )
        worker_launch = encode_worker_launch({
            "command_frame_b64": base64.b64encode(wire_command).decode("ascii"),
            "attempt_fence": attempt.to_mapping(),
            "effect_fence": effect_fence.to_mapping(),
            "target_ordinal": planner["target_ordinal"],
            "action": planner["action"], "behavior": fixture.worker_behavior,
        })
        worker_process = run_fake_module(
            "ge_nwp_coordinator._rw0_d1_fake_worker", worker_launch,
            cwd=workspace.root, timeout_seconds=fixture.worker_timeout,
            output_limit=64 * 1024 + 8, cancelled=cancelled,
        )
        facts["worker_process"] = worker_process
        try:
            if type(worker_process) is not D1ProcessOutcome:
                raise ValueError("invalid_d1_process_outcome")
            worker_process.validate()
        except ValueError:
            invalid_process = True
            raise
        if worker_process.reason in {"start_failed", "invalid_input"}:
            raise _D1Stop("worker_start")
        if not worker_process.cleanup_complete:
            raise _D1Stop("worker_cleanup_unresolved")
        if worker_process.reason != "ok":
            raise _D1Stop(_process_reason("worker", worker_process.reason))
        try:
            wire_result = decode_wire_result_frame(
                worker_process.stdout, command=worker_command,
                delivery=delivery, attempt_fence=attempt,
                author_effect_fence=effect_fence,
            )
        except Exception:
            raise _D1Stop("worker_frame") from None
        facts["wire_result"] = wire_result
        adapter_exit = WorkerObservationV1.create(
            observation_ref="observation.d1.process-exited",
            source_kind="direct_local_adapter", source_ref="adapter.d1.fake",
            source_invocation_ref=_adapter_invocation_ref(worker_process),
            observation_kind="process_exited", outcome="exited",
            reason_code="reason.none", evidence_refs=["evidence.d1.process"],
            observed_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            process_exit_code=worker_process.exit_code,
            delivery=delivery, author_command=worker_command,
            attempt_fence=attempt, author_effect_fence=effect_fence,
            effect_fence=effect_fence,
        )
        facts["adapter_exit"] = adapter_exit
        classification = classify_wire_process_result(
            command=worker_command, delivery=delivery, attempt_fence=attempt,
            author_effect_fence=effect_fence, result=wire_result,
            result_failure=None, adapter_observations=(adapter_exit,),
            request=None, process_observations=(),
            cancellation_effect_fence=None, cancellation_delivery=None,
        )
        facts["wire_classification"] = classification
        if classification.classification != "usable":
            raise _D1Stop("worker_frame")
        try:
            capture = workspace.capture(selected_path=PATHS[planner["target_ordinal"]])
        except D1WorkspaceError as error:
            raise _D1Stop(str(error)) from None
        facts["capture"] = capture
        try:
            manifest = build_candidate_capsule(
                capture, command=worker_command, attempt_fence=attempt,
                effect_fence=effect_fence, manifest_ref="capsule-manifest.d1",
            )
            verify_candidate_capsule(
                manifest, immutable_base=base, capture=capture,
                command=worker_command, attempt_fence=attempt,
                effect_fence=effect_fence,
            )
        except Exception:
            raise _D1Stop("capsule_mismatch") from None
        facts["capsule_manifest"] = manifest
    except _D1Stop as stopped:
        reason = stopped.reason
    except Exception:
        reason = "durable_conflict"
    finally:
        if writer is not None:
            try:
                writer.close()
            except Exception:
                reason = "process_cleanup_unresolved"
        if scratch is not None:
            try:
                scratch.cleanup()
            except Exception:
                reason = "process_cleanup_unresolved"
        if workspace is not None:
            try:
                workspace.close()
                workspace_cleaned = True
            except Exception:
                reason = "workspace_cleanup_unresolved"
    status = (
        "capsule_ready" if reason == "complete"
        else "cleanup_unresolved" if reason.endswith("cleanup_unresolved")
        else "stopped"
    )
    try:
        if invalid_process:
            raise ValueError("invalid_d1_process_outcome")
        handback = RW0D1HandbackV1(
            status, reason, workspace_cleaned=workspace_cleaned, **facts,
        )
        return RW0D1OfflineRun(root, location, handback)
    except BaseException:
        if root is not None:
            shutil.rmtree(root)
        raise
