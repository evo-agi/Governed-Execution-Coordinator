"""Transient D1 handback and distinct parent-only disposable-state custody."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import os
from pathlib import Path
import shutil

from ._cognitive_proposal_semantic_values import PreExecutionProposalSelectionBundleV1
from ._development_author_effect_establishment_contracts import (
    DevelopmentAuthorEffectEstablishmentCommandV1,
    DevelopmentAuthorEffectEstablishmentResultV1,
)
from ._development_pre_execution_plan_disposition_contracts import (
    PreExecutionPlanDispositionResultV1,
)
from ._development_program_initialization_contracts import (
    DevelopmentProgramInitializationResultV1,
)
from ._rw0_c1_semantic_values import RW0C1EstablishPhaseResultV1
from ._rw0_d1_process_supervisor import D1ProcessOutcome
from ._rw0_d1_workspace import D1CandidateCapture, D1WorkspaceError
from ._rw0_phase_entry_semantic_values import RW0PhaseEntryBasisV1
from ._rw0_wire_protocol_values import (
    RW0WireProcessResultClassificationV1, RW0WireWorkerResultV1,
)
from ._worker_execution_semantic_values import (
    CandidateCapsuleManifestV1, WorkerObservationV1,
    validate_observation_relation,
)
from .sqlite_location import CoordinatorStateLocation


_STATUSES = frozenset({"capsule_ready", "stopped", "cleanup_unresolved"})
_REASONS = frozenset({
    "complete", "invalid_input", "durable_conflict", "durable_commit_unresolved",
    "planner_start", "planner_frame", "planner_limit", "planner_exit",
    "planner_deadline", "planner_cancelled", "nonselection", "c1_phase_failure",
    "worker_start", "worker_frame", "worker_limit", "worker_exit",
    "worker_deadline", "worker_cancelled", "unsafe_candidate",
    "missing_candidate", "excessive_candidate", "capsule_mismatch",
    "process_cleanup_unresolved", "planner_cleanup_unresolved",
    "worker_cleanup_unresolved", "workspace_cleanup_unresolved",
})
_CLEANUP_REASONS = frozenset({
    "process_cleanup_unresolved", "planner_cleanup_unresolved",
    "worker_cleanup_unresolved", "workspace_cleanup_unresolved",
})
_EVIDENCE_ORDER = (
    "program_result", "author_result", "author_command", "planner_process",
    "selected_bundle", "section41_result", "phase_basis", "phase_result",
    "worker_process", "wire_result", "adapter_exit", "wire_classification", "capture",
    "capsule_manifest",
)
_STOP_STAGES = {
    "invalid_input": (0,),
    "durable_commit_unresolved": (0, 1, 5, 7),
    "durable_conflict": (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12),
    "planner_start": (4,), "planner_frame": (4,),
    "planner_limit": (4,), "planner_exit": (4,),
    "planner_deadline": (4,), "planner_cancelled": (4,),
    "nonselection": (6,),
    "worker_start": (9,), "worker_frame": (9, 12),
    "worker_limit": (9,), "worker_exit": (9,),
    "worker_deadline": (9,), "worker_cancelled": (9,),
    "unsafe_candidate": (12,), "missing_candidate": (12,),
    "excessive_candidate": (12,), "capsule_mismatch": (13,),
}
_CLEANUP_STAGES = {
    "process_cleanup_unresolved": (0, 1, 2, 3, 4, 5, 6, 7, 8),
    "planner_cleanup_unresolved": (4,),
    "worker_cleanup_unresolved": (9,),
    "workspace_cleanup_unresolved": (8, 9, 10, 11, 12, 13, 14),
}
_PROCESS_FAILURES = {
    "planner_limit": ("output_limit", "stderr_limit"),
    "planner_exit": ("nonzero_exit",),
    "planner_deadline": ("deadline",),
    "planner_cancelled": ("cancelled",),
    "worker_limit": ("output_limit", "stderr_limit"),
    "worker_exit": ("nonzero_exit",),
    "worker_deadline": ("deadline",),
    "worker_cancelled": ("cancelled",),
}


def _invalid_handback() -> None:
    raise ValueError("invalid_d1_handback")


def _adapter_invocation_ref(worker: D1ProcessOutcome) -> str:
    """Bind the local adapter fact to this exact retained worker invocation."""
    if (type(worker) is not D1ProcessOutcome or type(worker.pid) is not int
            or worker.pid <= 0 or type(worker.stdout) is not bytes):
        _invalid_handback()
    identity = str(worker.pid).encode("ascii") + b"\0" + worker.stdout
    return "adapter.invocation.d1." + hashlib.sha256(identity).hexdigest()


def _started_and_clean(process: D1ProcessOutcome | None) -> bool:
    return (process is not None and process.pid is not None
            and process.process_group is not None and process.cleanup_complete)


def _failed_start(process: D1ProcessOutcome | None) -> bool:
    return (process is not None and process.reason in {"start_failed", "invalid_input"}
            and process.pid is None and process.process_group is None
            and process.exit_code is None and process.stdout == b""
            and process.stderr == b"" and not process.cancellation_requested
            and not process.term_delivered and not process.kill_delivered
            and not process.reaped and not process.group_clear
            and process.cleanup_reason is None)


@dataclass(frozen=True, slots=True, repr=False)
class RW0D1HandbackV1:
    status: str
    reason: str
    program_result: DevelopmentProgramInitializationResultV1 | None = field(default=None, repr=False)
    author_result: DevelopmentAuthorEffectEstablishmentResultV1 | None = field(default=None, repr=False)
    author_command: DevelopmentAuthorEffectEstablishmentCommandV1 | None = field(default=None, repr=False)
    section41_result: PreExecutionPlanDispositionResultV1 | None = field(default=None, repr=False)
    selected_bundle: PreExecutionProposalSelectionBundleV1 | None = field(default=None, repr=False)
    phase_basis: RW0PhaseEntryBasisV1 | None = field(default=None, repr=False)
    phase_result: RW0C1EstablishPhaseResultV1 | None = field(default=None, repr=False)
    planner_process: D1ProcessOutcome | None = field(default=None, repr=False)
    worker_process: D1ProcessOutcome | None = field(default=None, repr=False)
    wire_result: RW0WireWorkerResultV1 | None = field(default=None, repr=False)
    adapter_exit: WorkerObservationV1 | None = field(default=None, repr=False)
    wire_classification: RW0WireProcessResultClassificationV1 | None = field(default=None, repr=False)
    capture: D1CandidateCapture | None = field(default=None, repr=False)
    capsule_manifest: CandidateCapsuleManifestV1 | None = field(default=None, repr=False)
    workspace_cleaned: bool = False

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if type(self) is not RW0D1HandbackV1:
            _invalid_handback()
        if type(self.status) is not str or self.status not in _STATUSES:
            _invalid_handback()
        if type(self.reason) is not str or self.reason not in _REASONS:
            _invalid_handback()
        if type(self.workspace_cleaned) is not bool:
            _invalid_handback()
        evidence = (
            (self.program_result, DevelopmentProgramInitializationResultV1),
            (self.author_result, DevelopmentAuthorEffectEstablishmentResultV1),
            (self.author_command, DevelopmentAuthorEffectEstablishmentCommandV1),
            (self.section41_result, PreExecutionPlanDispositionResultV1),
            (self.selected_bundle, PreExecutionProposalSelectionBundleV1),
            (self.phase_basis, RW0PhaseEntryBasisV1),
            (self.phase_result, RW0C1EstablishPhaseResultV1),
            (self.planner_process, D1ProcessOutcome),
            (self.worker_process, D1ProcessOutcome),
            (self.wire_result, RW0WireWorkerResultV1),
            (self.adapter_exit, WorkerObservationV1),
            (self.wire_classification, RW0WireProcessResultClassificationV1),
            (self.capture, D1CandidateCapture),
            (self.capsule_manifest, CandidateCapsuleManifestV1),
        )
        if any(value is not None and type(value) is not expected
               for value, expected in evidence):
            _invalid_handback()
        for process in (self.planner_process, self.worker_process):
            if process is not None:
                try:
                    process.validate()
                except ValueError:
                    _invalid_handback()
        if self.capture is not None:
            try:
                self.capture.validate()
            except D1WorkspaceError:
                _invalid_handback()
        if self.adapter_exit is not None:
            try:
                command = self.author_command
                worker = self.worker_process
                wire = self.wire_result
                if (type(command) is not DevelopmentAuthorEffectEstablishmentCommandV1
                        or type(worker) is not D1ProcessOutcome
                        or type(wire) is not RW0WireWorkerResultV1):
                    _invalid_handback()
                adapter = WorkerObservationV1.from_mapping(self.adapter_exit.to_mapping())
                if (adapter.to_mapping() != self.adapter_exit.to_mapping()
                        or adapter.observation_ref != "observation.d1.process-exited"
                        or adapter.source_kind != "direct_local_adapter"
                        or adapter.source_ref != "adapter.d1.fake"
                        or adapter.source_invocation_ref != _adapter_invocation_ref(worker)
                        or adapter.observation_kind != "process_exited"
                        or adapter.outcome != "exited"
                        or adapter.process_exit_code != worker.exit_code
                        or type(wire.observations) is not tuple
                        or len(wire.observations) not in (2, 3)
                        or wire.observations[-1].observed_at > adapter.observed_at):
                    _invalid_handback()
                validate_observation_relation(
                    observation=adapter, delivery=command.delivery_envelope,
                    author_command=command.worker_command,
                    attempt_fence=command.attempt_fence,
                    author_effect_fence=command.effect_fence,
                    effect_fence=command.effect_fence,
                )
            except Exception:
                _invalid_handback()
        values = tuple(getattr(self, name) for name in _EVIDENCE_ORDER)
        stage = sum(value is not None for value in values)
        if any(value is None for value in values[:stage]):
            _invalid_handback()
        if stage < 8 and self.workspace_cleaned:
            _invalid_handback()
        if stage >= 9 and self.reason != "workspace_cleanup_unresolved" and not self.workspace_cleaned:
            _invalid_handback()
        if (stage >= 3 and self.author_result.command_digest != self.author_command.command_digest):
            _invalid_handback()
        if (stage >= 6 and self.section41_result.proposal_ref
                != self.selected_bundle.model_proposal.proposal_ref):
            _invalid_handback()
        if stage >= 7 and (
            self.section41_result.disposition != "selected_for_dispatch_gates"
            or self.phase_basis.disposition_ref != self.section41_result.disposition_ref
            or self.phase_basis.disposition_digest != self.section41_result.disposition_digest
            or self.phase_basis.selected_proposal_ref != self.selected_bundle.model_proposal.proposal_ref
            or self.phase_basis.selected_proposal_digest != self.selected_bundle.model_proposal.proposal_digest
        ):
            _invalid_handback()
        if stage >= 8 and (
            self.phase_result.phase_basis_ref != self.phase_basis.basis_ref
            or self.phase_result.phase_basis_digest != self.phase_basis.basis_digest
        ):
            _invalid_handback()
        if stage >= 5 and not self.planner_process.clean_success:
            _invalid_handback()
        if stage >= 10 and not self.worker_process.clean_success:
            _invalid_handback()
        if stage >= 13 and self.wire_classification.classification != "usable":
            _invalid_handback()
        if self.status == "capsule_ready":
            if self.reason != "complete" or stage != 14 or not self.workspace_cleaned:
                _invalid_handback()
        elif self.status == "stopped":
            if stage not in _STOP_STAGES.get(self.reason, ()):
                _invalid_handback()
        elif stage not in _CLEANUP_STAGES.get(self.reason, ()):
            _invalid_handback()
        if self.status == "stopped":
            if self.reason in ("planner_start", "worker_start"):
                process = self.planner_process if self.reason == "planner_start" else self.worker_process
                if not _failed_start(process):
                    _invalid_handback()
            elif self.reason in _PROCESS_FAILURES:
                process = self.planner_process if self.reason.startswith("planner") else self.worker_process
                if not _started_and_clean(process) or process.reason not in _PROCESS_FAILURES[self.reason]:
                    _invalid_handback()
            elif self.reason == "planner_frame":
                if not self.planner_process.clean_success:
                    _invalid_handback()
            elif self.reason == "worker_frame":
                if (not self.worker_process.clean_success
                        or (stage == 12 and self.wire_classification.classification == "usable")):
                    _invalid_handback()
            elif self.reason == "nonselection":
                if self.section41_result.disposition == "selected_for_dispatch_gates":
                    _invalid_handback()
            elif self.reason in {"unsafe_candidate", "missing_candidate", "excessive_candidate"}:
                if self.wire_classification.classification != "usable":
                    _invalid_handback()
            elif self.reason == "durable_conflict":
                if (stage == 4 and not self.planner_process.clean_success
                        or stage == 6 and self.section41_result.disposition != "selected_for_dispatch_gates"
                        or stage == 9 and not self.worker_process.clean_success
                        or stage == 12 and self.wire_classification.classification != "usable"):
                    _invalid_handback()
        elif self.status == "cleanup_unresolved":
            if self.reason == "workspace_cleanup_unresolved" and self.workspace_cleaned:
                _invalid_handback()
            if self.reason == "process_cleanup_unresolved" and self.workspace_cleaned:
                _invalid_handback()
            if self.reason == "planner_cleanup_unresolved" and (
                self.planner_process.pid is None or self.planner_process.cleanup_complete
            ):
                _invalid_handback()
            if self.reason == "worker_cleanup_unresolved" and (
                self.worker_process.pid is None or self.worker_process.cleanup_complete
            ):
                _invalid_handback()

    def __str__(self) -> str:
        return "RW0D1HandbackV1"

    def __reduce__(self) -> object:
        raise TypeError("serialization disabled")


class _D1RunOwnershipError(RuntimeError):
    """Content-free rejection of inherited disposable-state custody."""


class RW0D1OfflineRun:
    """Explicit state-root owner kept in the parent process for a later D2."""

    __slots__ = ("_state_root", "_location", "_closed", "_creator_pid", "handback")

    def __init__(self, state_root: Path | None, location: CoordinatorStateLocation | None,
                 handback: RW0D1HandbackV1) -> None:
        if type(handback) is not RW0D1HandbackV1:
            raise TypeError("invalid_d1_run")
        self._state_root = state_root
        self._location = location
        self._closed = False
        self._creator_pid = os.getpid()
        self.handback = handback

    def _require_creator(self) -> None:
        if os.getpid() != self._creator_pid:
            raise _D1RunOwnershipError("d1_run_wrong_process")

    @property
    def location(self) -> CoordinatorStateLocation:
        self._require_creator()
        if self._closed or self._location is None:
            raise RuntimeError("d1_state_closed")
        return self._location

    @property
    def closed(self) -> bool:
        self._require_creator()
        return self._closed

    def close(self) -> None:
        self._require_creator()
        if self._closed:
            return
        if self._state_root is not None:
            shutil.rmtree(self._state_root)
        self._location = None
        self._state_root = None
        self._closed = True

    def __enter__(self) -> RW0D1OfflineRun:
        self._require_creator()
        if self._closed:
            raise RuntimeError("d1_state_closed")
        return self

    def __exit__(self, *_: object) -> None:
        self._require_creator()
        self.close()

    def __repr__(self) -> str:
        return "RW0D1OfflineRun"

    __str__ = __repr__

    def __reduce__(self) -> object:
        raise TypeError("serialization disabled")
