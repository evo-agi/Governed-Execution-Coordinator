"""Integrated D1 proof through current private durable owners."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
from types import SimpleNamespace

import pytest

import ge_nwp_coordinator._rw0_d1_offline as offline
import ge_nwp_coordinator._rw0_d1_process_supervisor as supervisor
from ge_nwp_coordinator._rw0_d1_capsule import D1CapsuleError
from ge_nwp_coordinator._rw0_d1_workspace import PATHS
from ge_nwp_coordinator._rw0_d1_process_supervisor import D1ProcessOutcome
from ge_nwp_coordinator._rw0_d1_workspace import D1CandidateCapture
from ge_nwp_coordinator._rw0_c1_semantic_values import (
    RW0C1EstablishPhaseResultV1, RW0C1RecoveryResultV1,
)
from ge_nwp_coordinator._worker_execution_semantic_values import WorkSpecV1
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError, SQLiteMutationStoreErrorCode,
)
from ge_nwp_coordinator.sqlite_writer_session import _SQLiteWriterSession


def work_spec() -> WorkSpecV1:
    return WorkSpecV1.create(
        work_spec_ref="work-spec.d1", program_ref="program.d1",
        program_version_ref="program-version.d1",
        accepted_intent_revision_ref="accepted-intent.d1",
        work_item_ref="work-item.d1",
        work_item_revision_ref="work-item-revision.d1",
        repository_ref="repository.execution-substrate", base_git_oid="2" * 40,
        authorized_paths=list(PATHS),
        objective="Make one artificial source change.",
        requirements=["Change only an authorized file."],
        exclusions=["Do not contact network."],
        validation_requirement_ref="validation.d1",
        review_requirement_ref="review.d1",
    )


@dataclass(slots=True, repr=False)
class _ObservedLaunch:
    role: str
    argv: tuple[object, ...]
    attempt_at: int
    group_owned: bool
    environment: dict[object, object] | None
    cwd: object
    launch_options: dict[str, object]
    child: subprocess.Popen[bytes] | None = None
    created_at: int | None = None
    failure: BaseException | None = None


class _D1InvocationObserver:
    """Test-local call-through evidence below handback and supervisor outcomes."""

    def __init__(self) -> None:
        self.events: list[tuple[str, object]] = []
        self.launches: list[_ObservedLaunch] = []
        self.emergency_cleanup: list[int] = []
        self.acquired_locations: list[object] = []
        self.planner_scratches: list[Path] = []
        self.workspace_roots: list[Path] = []

    def _record(self, kind: str, value: object) -> int:
        self.events.append((kind, value))
        return len(self.events) - 1

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Install after any response-loss fault, so only the result returned to
        # the runner can be a successful C1/recovery observation.
        original_popen = supervisor.subprocess.Popen
        original_acquire = offline.acquire_sqlite_writer_session
        original_close = _SQLiteWriterSession.close
        original_phase = _SQLiteWriterSession._establish_rw0_phase
        original_recovery = (
            _SQLiteWriterSession._resolve_rw0_c1_phase_establishment_commit_outcome
        )
        original_tempdir = offline.tempfile.TemporaryDirectory
        original_workspace_init = offline.D1Workspace.__init__

        def observed_popen(argv: object, *args: object, **kwargs: object) -> object:
            vector = tuple(argv) if type(argv) in (tuple, list) else (argv,)
            module = vector[3] if len(vector) == 4 and vector[2] == "-m" else None
            role = {
                "ge_nwp_coordinator._rw0_d1_fake_planner": "planner",
                "ge_nwp_coordinator._rw0_d1_fake_worker": "worker",
            }.get(module, "unexpected")
            launch = _ObservedLaunch(
                role, vector, self._record("launch_attempt", role),
                kwargs.get("start_new_session") is True,
                dict(kwargs["env"]) if type(kwargs.get("env")) is dict else None,
                kwargs.get("cwd"),
                {key: kwargs.get(key) for key in (
                    "stdin", "stdout", "stderr", "shell", "start_new_session",
                    "close_fds", "pass_fds",
                )},
            )
            self.launches.append(launch)
            try:
                child = original_popen(argv, *args, **kwargs)
            except BaseException as error:
                launch.failure = error
                self._record("launch_failed", launch)
                raise
            launch.child = child
            launch.created_at = self._record("launch_created", launch)
            return child

        def observed_acquire(location: object) -> object:
            writer = original_acquire(location)
            self.acquired_locations.append(location)
            self._record("writer_acquired", writer)
            return writer

        def observed_tempdir(*args: object, **kwargs: object) -> object:
            scratch = original_tempdir(*args, **kwargs)
            if kwargs.get("prefix") == "rw0-d1-planner-":
                self.planner_scratches.append(Path(scratch.name).resolve())
            return scratch

        def observed_workspace_init(workspace: object, base: object) -> None:
            original_workspace_init(workspace, base)
            self.workspace_roots.append(workspace.root.resolve())

        def observed_close(writer: object) -> None:
            original_close(writer)
            self._record("writer_closed", writer)

        def observed_phase(writer: object, command: object) -> object:
            self._record("c1_enter", (writer, command))
            result = original_phase(writer, command)
            self._record("c1_return", (writer, command, result))
            return result

        def observed_recovery(writer: object, probe: object) -> object:
            self._record("recovery_enter", (writer, probe))
            result = original_recovery(writer, probe)
            self._record("recovery_return", (writer, probe, result))
            return result

        monkeypatch.setattr(supervisor.subprocess, "Popen", observed_popen)
        monkeypatch.setattr(offline, "acquire_sqlite_writer_session", observed_acquire)
        monkeypatch.setattr(offline.tempfile, "TemporaryDirectory", observed_tempdir)
        monkeypatch.setattr(offline.D1Workspace, "__init__", observed_workspace_init)
        monkeypatch.setattr(_SQLiteWriterSession, "close", observed_close)
        monkeypatch.setattr(_SQLiteWriterSession, "_establish_rw0_phase", observed_phase)
        monkeypatch.setattr(
            _SQLiteWriterSession,
            "_resolve_rw0_c1_phase_establishment_commit_outcome",
            observed_recovery,
        )

    def assert_launches(self, expected: tuple[str, ...], handback: object,
                        location: object) -> None:
        # Check every actual call-boundary snapshot before comparing the returned
        # handback or launch count, including any launch it did not report.
        if not self.acquired_locations or any(
            acquired is not location for acquired in self.acquired_locations
        ):
            raise AssertionError("d1_parent_location_observation")
        parent_coordinates = {
            str(location.state_root), str(Path(location.state_root).resolve()),
            str(location.database_path), str(Path(location.database_path).resolve()),
        }
        expected_cwds = {
            "planner": tuple(self.planner_scratches),
            "worker": tuple(self.workspace_roots),
        }
        modules = {
            "planner": "ge_nwp_coordinator._rw0_d1_fake_planner",
            "worker": "ge_nwp_coordinator._rw0_d1_fake_worker",
        }
        fixed_env = {
            "PYTHONPATH": str(Path(supervisor.__file__).resolve().parent.parent),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "LANG": "C",
            "LC_ALL": "C",
            "__CF_USER_TEXT_ENCODING": "0x0:0:0",
        }
        allowed_env_keys = {
            "PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "PYTHONIOENCODING",
            "LANG", "LC_ALL", "__CF_USER_TEXT_ENCODING", "TMPDIR",
        }
        for launch in self.launches:
            if launch.role not in modules:
                raise AssertionError("d1_unexpected_child_module")
            environment = launch.environment
            if environment is None or type(launch.cwd) is not str:
                raise AssertionError("d1_child_input_types")
            if (any(type(item) is not str for item in launch.argv)
                    or any(type(key) is not str or type(value) is not str
                           for key, value in environment.items())):
                raise AssertionError("d1_child_input_types")
            resolved_cwd = Path(launch.cwd).resolve()
            child_inputs = (*launch.argv, str(resolved_cwd),
                            *(item for pair in environment.items() for item in pair))
            if any(forbidden in item for forbidden in parent_coordinates
                   for item in child_inputs):
                raise AssertionError("d1_child_parent_state_exposed")
            if launch.argv != (
                str(Path(sys.executable).resolve()), "-B", "-m", modules[launch.role]
            ):
                raise AssertionError("d1_child_argv")
            if resolved_cwd not in expected_cwds[launch.role]:
                raise AssertionError("d1_child_cwd")
            if set(environment) != allowed_env_keys:
                raise AssertionError("d1_child_env_keys")
            if any(environment[key] != value for key, value in fixed_env.items()):
                raise AssertionError("d1_child_env_fixed_values")
            if environment["TMPDIR"] != str(resolved_cwd):
                raise AssertionError("d1_child_env_tmpdir")
            if launch.launch_options != {
                "stdin": subprocess.PIPE, "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE, "shell": False,
                "start_new_session": True, "close_fds": True, "pass_fds": (),
            }:
                raise AssertionError("d1_child_launch_options")
        assert all(launch.failure is None and launch.child is not None
                   and launch.created_at is not None for launch in self.launches)
        pids = tuple(launch.child.pid for launch in self.launches)
        assert all(type(pid) is int and pid > 0 for pid in pids)
        assert len(set(pids)) == len(pids)
        assert tuple(launch.role for launch in self.launches) == expected
        for launch in self.launches:
            assert launch.argv[1:3] == ("-B", "-m")
            assert launch.group_owned
            earlier = [(at, writer) for at, (kind, writer) in enumerate(self.events)
                       if kind == "writer_acquired" and at < launch.attempt_at]
            assert earlier, "child attempted without a guarded writer"
            acquired_at, writer = earlier[-1]
            assert any(kind == "writer_closed" and value is writer
                       and acquired_at < at < launch.attempt_at
                       for at, (kind, value) in enumerate(self.events)), (
                           "child attempted before the relevant writer close returned"
                       )
            assert launch.child.poll() is not None
            assert not supervisor._group_alive(launch.child.pid)
        for role, value in (("planner", handback.planner_process),
                            ("worker", handback.worker_process)):
            observed = [launch for launch in self.launches if launch.role == role]
            if value is not None:
                assert len(observed) == 1
                assert value.pid == observed[0].child.pid
                assert value.process_group == observed[0].child.pid
                assert value.reaped and value.group_clear
                assert value.exit_code == observed[0].child.returncode
            else:
                assert not observed

    def assert_worker_after_effective_c1(self, handback: object) -> None:
        assert handback.phase_result is not None
        for launch in self.launches:
            if launch.role != "worker":
                continue
            phase_returns = [
                (at, value) for at, (kind, value) in enumerate(self.events)
                if kind == "c1_return" and at < launch.attempt_at
            ]
            assert phase_returns, "worker attempted before effective C1 success"
            phase_at, (writer, command, result) = phase_returns[-1]
            assert type(result) is RW0C1EstablishPhaseResultV1
            assert result is handback.phase_result
            assert result.disposition in {"fresh_committed", "exact_replay"}
            assert result.mutation_ref == command.mutation_ref
            assert result.command_digest == command.command_digest
            assert result.phase_basis_ref == command.phase_basis.basis_ref
            assert result.phase_basis_digest == command.phase_basis.basis_digest
            assert result.phase_basis_ref == handback.phase_basis.basis_ref
            assert result.phase_basis_digest == handback.phase_basis.basis_digest
            recoveries = [
                (at, value) for at, (kind, value) in enumerate(self.events)
                if kind == "recovery_return" and at < launch.attempt_at
            ]
            resolved_at = phase_at
            if recoveries:
                recovery_at, (_recovery_writer, probe, recovery) = recoveries[-1]
                assert type(recovery) is RW0C1RecoveryResultV1
                assert recovery.disposition.value == "committed_exact"
                assert recovery.mutation_ref == probe.mutation_ref == result.mutation_ref
                assert recovery.command_digest == probe.command_digest == result.command_digest
                assert recovery.receipt_digest == result.receipt_digest
                assert recovery_at < phase_at
                assert result.disposition == "exact_replay"
                resolved_at = recovery_at
            assert any(kind == "writer_closed" and value is writer
                       and resolved_at < at < launch.attempt_at
                       for at, (kind, value) in enumerate(self.events)), (
                           "worker attempted before the C1/recovery writer close returned"
                       )

    def cleanup_owned_children(self) -> None:
        # Emergency cleanup is independent of the returned handback; ordinary
        # D1 supervision should leave this list empty, even for a discarded PID.
        for launch in self.launches:
            child = launch.child
            if child is None:
                continue
            if child.poll() is None or (launch.group_owned and supervisor._group_alive(child.pid)):
                self.emergency_cleanup.append(child.pid)
                try:
                    if launch.group_owned:
                        os.killpg(child.pid, signal.SIGKILL)
                    else:
                        child.kill()
                except ProcessLookupError:
                    pass
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass


def test_full_d1_through_guarded_writers_and_parent_capsule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    observed = _D1InvocationObserver()
    observed.install(monkeypatch)
    try:
        with offline.run_rw0_d1_offline(work, offline.artificial_fixture(work)) as run:
            value = run.handback
            observed.assert_launches(("planner", "worker"), value, run.location)
            observed.assert_worker_after_effective_c1(value)
            assert value.status == "capsule_ready"
            assert value.reason == "complete"
            assert value.program_result.disposition == "committed"
            assert value.author_result.disposition == "committed"
            assert value.section41_result.disposition == "selected_for_dispatch_gates"
            assert value.phase_result.disposition == "fresh_committed"
            assert value.planner_process.pid != value.worker_process.pid
            for process in (value.planner_process, value.worker_process):
                assert type(process.pid) is int and process.pid > 0
                assert process.process_group == process.pid
                assert type(process.exit_code) is int and process.exit_code == 0
                assert process.clean_success
            assert value.planner_process.cleanup_complete
            assert value.worker_process.cleanup_complete
            assert value.capture.changed_path == PATHS[2]
            assert value.capsule_manifest.candidate_ref == value.author_command.candidate_ref
            assert value.workspace_cleaned is True
            assert value.wire_classification.classification == "usable"
            assert value.wire_classification.reason == "usable"
            location = run.location
            assert Path(location.database_path).is_file()
    finally:
        observed.cleanup_owned_children()
    assert observed.emergency_cleanup == []
    assert run.closed
    assert not Path(location.database_path).exists()


def test_actual_launch_observer_rejects_parent_path_in_allowed_env_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    observed = _D1InvocationObserver()
    observed.install(monkeypatch)
    try:
        with offline.run_rw0_d1_offline(work, offline.artificial_fixture(work)) as run:
            observed.assert_launches(("planner", "worker"), run.handback, run.location)
            launch = observed.launches[0]
            assert launch.environment is not None
            original = launch.environment["LANG"]
            try:
                launch.environment["LANG"] = str(run.location.database_path)
                with pytest.raises(AssertionError,
                                   match="^d1_child_parent_state_exposed$"):
                    observed.assert_launches(("planner", "worker"),
                                             run.handback, run.location)
            finally:
                launch.environment["LANG"] = original
    finally:
        observed.cleanup_owned_children()
    assert observed.emergency_cleanup == []


def test_runner_independently_verifies_its_capsule_before_ready_handback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    fixture = offline.artificial_fixture(work)
    events: list[str] = []
    captures: list[D1CandidateCapture] = []
    built: list[tuple[D1CandidateCapture, object]] = []
    verified: list[tuple[object, dict[str, object]]] = []
    workspace_roots: list[Path] = []
    original_capture = offline.D1Workspace.capture
    original_build = offline.build_candidate_capsule
    original_verify = offline.verify_candidate_capsule
    original_post_init = offline.RW0D1HandbackV1.__post_init__

    def observed_capture(self: object, *, selected_path: str) -> D1CandidateCapture:
        capture = original_capture(self, selected_path=selected_path)
        workspace_roots.append(self.root)
        captures.append(capture)
        events.append("capture")
        return capture

    def observed_build(capture: D1CandidateCapture, **kwargs: object) -> object:
        manifest = original_build(capture, **kwargs)
        built.append((capture, manifest))
        events.append("build")
        return manifest

    def observed_verify(manifest: object, **kwargs: object) -> None:
        events.append("verify_enter")
        verified.append((manifest, kwargs))
        result = original_verify(manifest, **kwargs)
        events.append("verify_complete")
        return result

    def observed_handback(self: object) -> None:
        if self.status == "capsule_ready":
            events.append("ready_enter")
        original_post_init(self)
        if self.status == "capsule_ready":
            events.append("ready_complete")

    monkeypatch.setattr(offline.D1Workspace, "capture", observed_capture)
    monkeypatch.setattr(offline, "build_candidate_capsule", observed_build)
    monkeypatch.setattr(offline, "verify_candidate_capsule", observed_verify)
    monkeypatch.setattr(offline.RW0D1HandbackV1, "__post_init__", observed_handback)

    run = offline.run_rw0_d1_offline(work, fixture)
    try:
        events.append("returned")
        handback = run.handback
        state_root = run.location.state_root
        assert events == [
            "capture", "build", "verify_enter", "verify_complete",
            "ready_enter", "ready_complete", "returned",
        ]
        assert len(captures) == len(built) == len(verified) == len(workspace_roots) == 1
        capture = captures[0]
        built_capture, manifest = built[0]
        verified_manifest, inputs = verified[0]
        assert built_capture is capture is handback.capture is inputs["capture"]
        assert manifest is verified_manifest is handback.capsule_manifest
        assert inputs["immutable_base"] == fixture.base_blobs()
        assert inputs["command"] is handback.author_command.worker_command
        assert inputs["attempt_fence"] is handback.author_command.attempt_fence
        assert inputs["effect_fence"] is handback.author_command.effect_fence
        assert manifest.program_ref == work.program_ref
        assert manifest.candidate_ref == handback.author_command.candidate_ref
        assert manifest.command_digest == handback.author_command.worker_command.command_digest
        assert manifest.base_git_oid == work.base_git_oid
        assert tuple(entry.path for entry in manifest.entries) == PATHS
        assert (handback.status, handback.reason, handback.workspace_cleaned) == (
            "capsule_ready", "complete", True,
        )
        assert handback.program_result.disposition == "committed"
        assert handback.author_result.disposition == "committed"
        assert handback.section41_result.disposition == "selected_for_dispatch_gates"
        assert handback.phase_result.disposition == "fresh_committed"
        assert not workspace_roots[0].exists()
        for process in (handback.planner_process, handback.worker_process):
            assert process.reaped and process.group_clear and process.cleanup_complete
            assert not supervisor._group_alive(process.process_group)
        assert handback.planner_process.pid != handback.worker_process.pid
        assert state_root.exists() and not run.closed
    finally:
        run.close()
        run.close()
    assert run.closed and not state_root.exists()


def test_runner_verifier_relation_refusal_stops_before_ready_handback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    fixture = offline.artificial_fixture(work)
    events: list[str] = []
    captures: list[D1CandidateCapture] = []
    built: list[object] = []
    refusals: list[D1CapsuleError] = []
    successful_verifications: list[object] = []
    handback_statuses: list[str] = []
    workspace_roots: list[Path] = []
    durable_methods = (
        "_apply_development_program_initialization",
        "_establish_development_author_effect_intent",
        "_record_pre_execution_plan_disposition",
        "_establish_rw0_phase",
    )
    durable_calls = {name: 0 for name in durable_methods}
    original_capture = offline.D1Workspace.capture
    original_build = offline.build_candidate_capsule
    original_verify = offline.verify_candidate_capsule
    original_post_init = offline.RW0D1HandbackV1.__post_init__

    for method in durable_methods:
        original = getattr(_SQLiteWriterSession, method)

        def counted(self: object, *args: object, _method: str = method,
                    _original: object = original, **kwargs: object) -> object:
            durable_calls[_method] += 1
            return _original(self, *args, **kwargs)

        monkeypatch.setattr(_SQLiteWriterSession, method, counted)

    def observed_capture(self: object, *, selected_path: str) -> D1CandidateCapture:
        capture = original_capture(self, selected_path=selected_path)
        workspace_roots.append(self.root)
        captures.append(capture)
        events.append("capture")
        return capture

    def observed_build(capture: D1CandidateCapture, **kwargs: object) -> object:
        manifest = original_build(capture, **kwargs)
        built.append(manifest)
        events.append("build")
        return manifest

    def observed_verify(manifest: object, **kwargs: object) -> None:
        events.append("verify_enter")
        capture = kwargs["capture"]
        changed = capture.entries[2]
        inconsistent = replace(
            capture,
            entries=(*capture.entries[:2], replace(changed, after=changed.after + b"// mismatch\n")),
        )
        assert inconsistent.validate() is None
        assert inconsistent.changed_path == PATHS[2]
        try:
            result = original_verify(manifest, **{**kwargs, "capture": inconsistent})
        except D1CapsuleError as error:
            refusals.append(error)
            events.append("verify_refused")
            raise
        successful_verifications.append(result)
        events.append("verify_returned")
        return result

    def observed_handback(self: object) -> None:
        handback_statuses.append(self.status)
        events.append("handback_enter")
        original_post_init(self)
        events.append("handback_complete")

    monkeypatch.setattr(offline.D1Workspace, "capture", observed_capture)
    monkeypatch.setattr(offline, "build_candidate_capsule", observed_build)
    monkeypatch.setattr(offline, "verify_candidate_capsule", observed_verify)
    monkeypatch.setattr(offline.RW0D1HandbackV1, "__post_init__", observed_handback)

    run = offline.run_rw0_d1_offline(work, fixture)
    try:
        events.append("returned")
        handback = run.handback
        state_root = run.location.state_root
        assert events == [
            "capture", "build", "verify_enter", "verify_refused",
            "handback_enter", "handback_complete", "returned",
        ]
        assert handback_statuses == ["stopped"]
        assert len(captures) == len(built) == len(refusals) == len(workspace_roots) == 1
        assert successful_verifications == []
        assert type(refusals[0]) is D1CapsuleError
        assert str(refusals[0]) == "capsule_mismatch"
        assert (handback.status, handback.reason, handback.workspace_cleaned) == (
            "stopped", "capsule_mismatch", True,
        )
        assert handback.capture is captures[0]
        assert handback.capsule_manifest is None
        assert all(durable_calls[name] == 1 for name in durable_methods)
        assert handback.program_result.disposition == "committed"
        assert handback.author_result.disposition == "committed"
        assert handback.author_result.command_digest == handback.author_command.command_digest
        assert handback.section41_result.disposition == "selected_for_dispatch_gates"
        assert handback.phase_result.disposition == "fresh_committed"
        assert handback.phase_result.phase_basis_digest == handback.phase_basis.basis_digest
        assert handback.wire_classification.classification == "usable"
        assert not workspace_roots[0].exists()
        for process in (handback.planner_process, handback.worker_process):
            assert process.reaped and process.group_clear and process.cleanup_complete
            assert not supervisor._group_alive(process.process_group)
        assert state_root.exists() and not run.closed
        for sensitive in (str(state_root), str(workspace_roots[0])):
            assert sensitive not in str(refusals[0])
            assert sensitive not in repr(handback)
        assert fixture.base_entries[2][1].decode() not in repr(handback)
    finally:
        run.close()
        run.close()
    assert run.closed and not state_root.exists()


@pytest.mark.parametrize("stage,method", (
    ("program", "_apply_development_program_initialization"),
    ("author", "_establish_development_author_effect_intent"),
    ("selection", "_record_pre_execution_plan_disposition"),
    ("phase", "_establish_rw0_phase"),
))
def test_committed_response_loss_uses_exact_recovery(
    monkeypatch: pytest.MonkeyPatch, stage: str, method: str,
) -> None:
    original = getattr(_SQLiteWriterSession, method)
    calls = 0

    def lost_response(self: object, *args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        result = original(self, *args, **kwargs)
        if calls == 1:
            raise SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN)
        return result

    monkeypatch.setattr(_SQLiteWriterSession, method, lost_response)
    observed = _D1InvocationObserver()
    observed.install(monkeypatch)
    work = work_spec()
    try:
        with offline.run_rw0_d1_offline(work, offline.artificial_fixture(work)) as run:
            observed.assert_launches(("planner", "worker"), run.handback, run.location)
            observed.assert_worker_after_effective_c1(run.handback)
            assert run.handback.status == "capsule_ready"
            selected = getattr(run.handback, {
                "program": "program_result", "author": "author_result",
                "selection": "section41_result", "phase": "phase_result",
            }[stage])
            if stage != "selection":
                assert selected.disposition in {"exact_replay", "committed"}
            assert calls == (2 if stage == "phase" else 1)
            if stage == "phase":
                assert selected.disposition == "exact_replay"
                assert len([1 for kind, _ in observed.events
                            if kind == "recovery_return"]) == 1
    finally:
        observed.cleanup_owned_children()
    assert observed.emergency_cleanup == []


def test_unresolved_program_recovery_stops_before_planner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _SQLiteWriterSession._apply_development_program_initialization
    committed: list[object] = []

    def lost_response(self: object, command: object) -> object:
        committed.append(original(self, command))
        raise SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN)

    monkeypatch.setattr(_SQLiteWriterSession, "_apply_development_program_initialization", lost_response)
    monkeypatch.setattr(
        _SQLiteWriterSession, "_resolve_development_program_initialization_commit_outcome",
        lambda self, command: SimpleNamespace(disposition="unresolved"),
    )
    observed = _D1InvocationObserver()
    observed.install(monkeypatch)
    work = work_spec()
    try:
        with offline.run_rw0_d1_offline(work, offline.artificial_fixture(work)) as run:
            observed.assert_launches((), run.handback, run.location)
            assert len(committed) == 1
            assert committed[0].disposition == "committed"
            assert run.handback.status == "stopped"
            assert run.handback.reason == "durable_commit_unresolved"
            assert run.handback.planner_process is None
            assert run.handback.worker_process is None
    finally:
        observed.cleanup_owned_children()
    assert observed.emergency_cleanup == []


@pytest.mark.parametrize("stage,method,recovery_method,expected_roles", (
    ("author", "_establish_development_author_effect_intent",
     "_resolve_development_author_effect_establishment_commit_outcome", ()),
    ("selection", "_record_pre_execution_plan_disposition",
     "_resolve_pre_execution_plan_disposition_commit_outcome", ("planner",)),
))
def test_unresolved_pre_phase_recovery_never_launches_worker(
    monkeypatch: pytest.MonkeyPatch, stage: str, method: str,
    recovery_method: str, expected_roles: tuple[str, ...],
) -> None:
    original = getattr(_SQLiteWriterSession, method)
    committed: list[object] = []

    def lost_response(self: object, *args: object, **kwargs: object) -> object:
        committed.append(original(self, *args, **kwargs))
        raise SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN)

    monkeypatch.setattr(_SQLiteWriterSession, method, lost_response)
    monkeypatch.setattr(
        _SQLiteWriterSession, recovery_method,
        lambda self, probe: SimpleNamespace(disposition="unresolved"),
    )
    observed = _D1InvocationObserver()
    observed.install(monkeypatch)
    work = work_spec()
    try:
        with offline.run_rw0_d1_offline(work, offline.artificial_fixture(work)) as run:
            observed.assert_launches(expected_roles, run.handback, run.location)
            assert len(committed) == 1
            assert committed[0].disposition == (
                "committed" if stage == "author" else "selected_for_dispatch_gates"
            )
            assert (run.handback.status, run.handback.reason) == (
                "stopped", "durable_commit_unresolved",
            )
            assert run.handback.program_result is not None
            assert run.handback.worker_process is None
            assert run.handback.phase_result is None
            assert run.handback.wire_result is None
            if stage == "selection":
                assert run.handback.author_result is not None
                assert run.handback.planner_process is not None
            else:
                assert run.handback.author_result is None
                assert run.handback.planner_process is None
    finally:
        observed.cleanup_owned_children()
    assert observed.emergency_cleanup == []


@pytest.mark.parametrize("behavior,reason", (
    ("malformed", "planner_frame"),
    ("nonzero", "planner_exit"),
    ("timeout", "planner_deadline"),
    ("stderr_limit", "planner_limit"),
    ("defer", "nonselection"),
))
def test_planner_failure_or_nonselection_stops_before_worker(
    behavior: str, reason: str,
) -> None:
    work = work_spec()
    fixture = offline.artificial_fixture(work, planner_behavior=behavior)
    if behavior == "timeout":
        fixture = offline.D1ArtificialFixture(
            fixture.work_spec, fixture.base_entries, behavior, "normal", 0.1, 5.0,
        )
    with offline.run_rw0_d1_offline(work, fixture) as run:
        assert run.handback.status == "stopped"
        assert run.handback.reason == reason
        assert run.handback.worker_process is None
        if behavior == "nonzero":
            assert run.handback.planner_process.reason == "nonzero_exit"
            assert run.handback.planner_process.exit_code == 3
        if behavior == "malformed":
            assert run.handback.planner_process.clean_success
        if behavior == "defer":
            assert run.handback.section41_result.disposition == "deferred"
            assert run.handback.phase_result is None


@pytest.mark.parametrize("behavior,reason", (
    ("malformed", "worker_frame"),
    ("nonzero", "worker_exit"),
    ("timeout", "worker_deadline"),
    ("stderr_limit", "worker_limit"),
    ("missing_candidate", "missing_candidate"),
    ("extra_path", "excessive_candidate"),
    ("unsafe_path", "unsafe_candidate"),
))
def test_worker_failure_keeps_durable_phase_but_no_capsule(
    behavior: str, reason: str,
) -> None:
    work = work_spec()
    fixture = offline.artificial_fixture(work, worker_behavior=behavior)
    if behavior == "timeout":
        fixture = offline.D1ArtificialFixture(
            fixture.work_spec, fixture.base_entries, "normal", behavior, 5.0, 0.1,
        )
    with offline.run_rw0_d1_offline(work, fixture) as run:
        assert run.handback.status == "stopped"
        assert run.handback.reason == reason
        assert run.handback.phase_result is not None
        assert run.handback.capsule_manifest is None
        if behavior == "nonzero":
            assert run.handback.worker_process.reason == "nonzero_exit"
            assert run.handback.worker_process.exit_code == 3
            assert run.handback.wire_classification is None
        if behavior == "malformed":
            assert run.handback.worker_process.clean_success


@pytest.mark.parametrize("target,reason", (
    ("planner", "planner_cancelled"),
    ("worker", "worker_cancelled"),
))
def test_cancelled_process_stops_without_capsule(
    monkeypatch: pytest.MonkeyPatch, target: str, reason: str,
) -> None:
    original = offline.run_fake_module

    def cancel_target(module: str, request: bytes, **kwargs: object) -> object:
        if module.endswith("_rw0_d1_fake_" + target):
            kwargs["cancelled"] = lambda: True
        return original(module, request, **kwargs)

    monkeypatch.setattr(offline, "run_fake_module", cancel_target)
    work = work_spec()
    with offline.run_rw0_d1_offline(work, offline.artificial_fixture(work)) as run:
        assert run.handback.status == "stopped"
        assert run.handback.reason == reason
        assert run.handback.capsule_manifest is None
        if target == "planner":
            assert run.handback.worker_process is None
        else:
            assert run.handback.phase_result is not None


def test_writer_close_uncertainty_blocks_first_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _SQLiteWriterSession.close
    closes = 0

    def uncertain_close(self: object) -> None:
        nonlocal closes
        closes += 1
        original(self)
        if closes == 1:
            raise OSError("lost close acknowledgement")

    monkeypatch.setattr(_SQLiteWriterSession, "close", uncertain_close)
    work = work_spec()
    with offline.run_rw0_d1_offline(work, offline.artificial_fixture(work)) as run:
        assert run.handback.status == "cleanup_unresolved"
        assert run.handback.reason == "process_cleanup_unresolved"
        assert run.handback.planner_process is None


def _fail_selector_close_for_stage(
    monkeypatch: pytest.MonkeyPatch, stage: str,
) -> dict[str, int]:
    original_selector = supervisor.selectors.DefaultSelector
    original_group_alive = supervisor._group_alive
    target_call = 1 if stage == "planner" else 2
    observations = {"created": 0, "failed_close": 0, "group_check": 0}

    class StageSelector:
        def __init__(self) -> None:
            self._wrapped = original_selector()
            observations["created"] += 1
            self._number = observations["created"]

        def __getattr__(self, name: str) -> object:
            return getattr(self._wrapped, name)

        def close(self) -> None:
            self._wrapped.close()
            if self._number == target_call:
                observations["failed_close"] += 1
                raise OSError("raw selector path must stay private")

    def observed_group(pgid: int) -> bool:
        observations["group_check"] += 1
        return original_group_alive(pgid)

    monkeypatch.setattr(supervisor.selectors, "DefaultSelector", StageSelector)
    monkeypatch.setattr(supervisor, "_group_alive", observed_group)
    return observations


@pytest.mark.parametrize("stage,expected_reason", (
    ("planner", "planner_cleanup_unresolved"),
    ("worker", "worker_cleanup_unresolved"),
))
def test_real_child_selector_close_uncertainty_keeps_stage_evidence(
    monkeypatch: pytest.MonkeyPatch, stage: str, expected_reason: str,
) -> None:
    observed = _fail_selector_close_for_stage(monkeypatch, stage)
    work = work_spec()
    with offline.run_rw0_d1_offline(work, offline.artificial_fixture(work)) as run:
        handback = run.handback
        assert handback.status == "cleanup_unresolved"
        assert handback.reason == expected_reason
        assert handback.program_result is not None
        assert handback.author_result is not None
        assert handback.author_command is not None
        target = handback.planner_process if stage == "planner" else handback.worker_process
        assert target is not None
        assert target.pid is not None and target.reaped and target.group_clear
        assert target.cleanup_reason == "selector_close"
        assert target.cleanup_complete is False
        assert not supervisor._group_alive(target.process_group)
        assert handback.capsule_manifest is None
        assert "raw selector path" not in repr(handback)
        if stage == "planner":
            assert handback.section41_result is None
            assert handback.phase_result is None
            assert handback.worker_process is None
            assert observed["created"] == 1
        else:
            assert handback.planner_process.cleanup_complete
            assert handback.section41_result is not None
            assert handback.phase_result is not None
            assert observed["created"] == 2
    assert observed["failed_close"] == 1
    assert observed["group_check"] >= observed["created"]


def test_planner_timeout_and_selector_failure_keep_both_facts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = _fail_selector_close_for_stage(monkeypatch, "planner")
    work = work_spec()
    fixture = offline.artificial_fixture(work, planner_behavior="timeout")
    fixture = offline.D1ArtificialFixture(
        fixture.work_spec, fixture.base_entries, "timeout", "normal", 0.1, 5.0,
    )
    with offline.run_rw0_d1_offline(work, fixture) as run:
        handback = run.handback
        assert handback.status == "cleanup_unresolved"
        assert handback.reason == "planner_cleanup_unresolved"
        process = handback.planner_process
        assert process is not None
        assert process.reason == "deadline"
        assert process.cleanup_reason == "selector_close"
        assert process.term_delivered and process.reaped and process.group_clear
        assert handback.section41_result is None
        assert handback.worker_process is None
    assert observed["failed_close"] == 1
    assert observed["group_check"] >= 1


def test_canonical_malformed_planner_action_stops_before_section41(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = offline.run_fake_module

    def malformed_planner(module: str, request: bytes, **kwargs: object):
        outcome = original(module, request, **kwargs)
        if module.endswith("_rw0_d1_fake_planner"):
            payload = json.loads(outcome.stdout[8:])
            payload["action"] = []
            encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                 separators=(",", ":")).encode()
            outcome = replace(outcome, stdout=b"D1O1" + struct.pack(">I", len(encoded)) + encoded)
        return outcome

    monkeypatch.setattr(offline, "run_fake_module", malformed_planner)
    work = work_spec()
    with offline.run_rw0_d1_offline(work, offline.artificial_fixture(work)) as run:
        handback = run.handback
        assert handback.status == "stopped"
        assert handback.reason == "planner_frame"
        assert handback.planner_process is not None
        assert handback.planner_process.pid is not None
        assert handback.planner_process.cleanup_complete
        assert handback.section41_result is None
        assert handback.phase_result is None
        assert handback.worker_process is None
        assert "TypeError" not in repr(handback)


def test_invalid_input_has_no_later_evidence_or_state_root() -> None:
    work = work_spec()
    with offline.run_rw0_d1_offline(None, offline.artificial_fixture(work)) as run:
        h = run.handback
        assert (h.status, h.reason, h.workspace_cleaned) == ("stopped", "invalid_input", False)
        assert all(getattr(h, name) is None for name in (
            "program_result", "author_result", "author_command", "planner_process",
            "selected_bundle", "section41_result", "phase_basis", "phase_result",
            "worker_process", "wire_result", "adapter_exit", "wire_classification", "capture",
            "capsule_manifest",
        ))
        with pytest.raises(RuntimeError, match="^d1_state_closed$"):
            _ = run.location


@pytest.mark.parametrize("target", ("planner", "worker"))
def test_failed_launch_retains_exact_observation_and_prior_stage(
    monkeypatch: pytest.MonkeyPatch, target: str,
) -> None:
    original = offline.run_fake_module

    def fail_target(module: str, request: bytes, **kwargs: object) -> D1ProcessOutcome:
        if module.endswith("_rw0_d1_fake_" + target):
            return D1ProcessOutcome("start_failed", None, None, None, b"", b"")
        return original(module, request, **kwargs)

    monkeypatch.setattr(offline, "run_fake_module", fail_target)
    work = work_spec()
    with offline.run_rw0_d1_offline(work, offline.artificial_fixture(work)) as run:
        h = run.handback
        assert (h.status, h.reason) == ("stopped", target + "_start")
        process = h.planner_process if target == "planner" else h.worker_process
        assert process is not None and process.reason == "start_failed"
        assert process.pid is None and not process.cleanup_complete
        assert h.program_result is not None and h.author_command is not None
        if target == "planner":
            assert h.selected_bundle is None and h.phase_result is None
            assert h.worker_process is None and not h.workspace_cleaned
        else:
            assert h.selected_bundle is not None and h.phase_result is not None
            assert h.wire_result is None and h.capture is None and h.workspace_cleaned


def test_unresolved_phase_recovery_retains_only_prior_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _SQLiteWriterSession._establish_rw0_phase
    committed: list[RW0C1EstablishPhaseResultV1] = []

    def lost_phase(self: object, command: object) -> object:
        committed.append(original(self, command))
        raise SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.COMMIT_OUTCOME_UNKNOWN)

    monkeypatch.setattr(_SQLiteWriterSession, "_establish_rw0_phase", lost_phase)
    monkeypatch.setattr(
        _SQLiteWriterSession, "_resolve_rw0_c1_phase_establishment_commit_outcome",
        lambda self, probe: SimpleNamespace(classification="unresolved"),
    )
    observed = _D1InvocationObserver()
    observed.install(monkeypatch)
    work = work_spec()
    try:
        with offline.run_rw0_d1_offline(work, offline.artificial_fixture(work)) as run:
            h = run.handback
            observed.assert_launches(("planner",), h, run.location)
            assert len(committed) == 1
            assert committed[0].disposition == "fresh_committed"
            assert committed[0].phase_basis_ref == h.phase_basis.basis_ref
            assert committed[0].phase_basis_digest == h.phase_basis.basis_digest
            assert [kind for kind, _ in observed.events if kind.startswith("c1_")] == [
                "c1_enter",
            ]
            recoveries = [value for kind, value in observed.events
                          if kind == "recovery_return"]
            assert len(recoveries) == 1
            assert recoveries[0][2].classification == "unresolved"
            assert (h.status, h.reason) == ("stopped", "durable_commit_unresolved")
            assert h.program_result is not None and h.author_result is not None
            assert h.section41_result.disposition == "selected_for_dispatch_gates"
            assert h.phase_basis is not None and h.phase_result is None
            assert h.worker_process is None and h.capture is None
            assert h.wire_result is None and h.wire_classification is None
            assert h.capsule_manifest is None
    finally:
        observed.cleanup_owned_children()
    assert observed.emergency_cleanup == []


def test_workspace_cleanup_uncertainty_retains_complete_prior_observations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = offline.D1Workspace.close

    def lost_close(self: object) -> None:
        original(self)
        raise OSError("raw workspace path stays private")

    monkeypatch.setattr(offline.D1Workspace, "close", lost_close)
    work = work_spec()
    with offline.run_rw0_d1_offline(work, offline.artificial_fixture(work)) as run:
        h = run.handback
        assert (h.status, h.reason, h.workspace_cleaned) == (
            "cleanup_unresolved", "workspace_cleanup_unresolved", False,
        )
        assert h.worker_process.cleanup_complete
        assert h.capture is not None and h.capsule_manifest is not None
        assert "raw workspace path" not in repr(h)


@pytest.mark.parametrize("hostile_kind", ("run", "object", "state_root"))
def test_actual_capture_injection_rejects_handback_and_cleans_new_state(
    monkeypatch: pytest.MonkeyPatch, hostile_kind: str,
) -> None:
    work = work_spec()
    with offline.run_rw0_d1_offline(work, offline.artificial_fixture(work)) as live_run:
        hostile = {"run": live_run, "object": object(),
                   "state_root": live_run.location.state_root}[hostile_kind]
        original_capture = offline.D1Workspace.capture
        original_mkdtemp = offline.tempfile.mkdtemp
        new_roots: list[Path] = []

        def tracked_mkdtemp(*args: object, **kwargs: object) -> str:
            root = original_mkdtemp(*args, **kwargs)
            if kwargs.get("prefix") == "rw0-d1-state-":
                new_roots.append(Path(root))
            return root

        def injected_capture(self: object, *, selected_path: str) -> D1CandidateCapture:
            valid = original_capture(self, selected_path=selected_path)
            forged = object.__new__(D1CandidateCapture)
            object.__setattr__(forged, "entries", (
                valid.entries[0], hostile, valid.entries[2],
            ))
            object.__setattr__(forged, "changed_path", valid.changed_path)
            return forged

        monkeypatch.setattr(offline.tempfile, "mkdtemp", tracked_mkdtemp)
        monkeypatch.setattr(offline.D1Workspace, "capture", injected_capture)
        with pytest.raises(ValueError, match="^invalid_d1_handback$"):
            offline.run_rw0_d1_offline(work, offline.artificial_fixture(work))
        assert len(new_roots) == 1 and not new_roots[0].exists()
        assert live_run.closed is False and live_run.location.state_root.exists()


@pytest.mark.parametrize("target,changes,expected_launches", (
    ("planner", {"pid": -1}, 1),
    ("worker", {"exit_code": 99}, 2),
))
def test_actual_return_substitution_refuses_contradictory_process_and_cleans_only_new_roots(
    monkeypatch: pytest.MonkeyPatch, target: str, changes: dict[str, object],
    expected_launches: int,
) -> None:
    work = work_spec()
    with offline.run_rw0_d1_offline(work, offline.artificial_fixture(work)) as live_run:
        live_root = live_run.location.state_root
        original_process = offline.run_fake_module
        original_mkdtemp = offline.tempfile.mkdtemp
        new_roots: list[Path] = []
        observed: list[D1ProcessOutcome] = []
        classifications = 0
        original_classifier = offline.classify_wire_process_result

        def tracked_mkdtemp(*args: object, **kwargs: object) -> str:
            root = original_mkdtemp(*args, **kwargs)
            if str(kwargs.get("prefix", "")).startswith("rw0-d1-"):
                new_roots.append(Path(root))
            return root

        def counted_classifier(**kwargs: object) -> object:
            nonlocal classifications
            classifications += 1
            return original_classifier(**kwargs)

        def substituted_process(module: str, request: bytes, **kwargs: object) -> D1ProcessOutcome:
            process = original_process(module, request, **kwargs)
            observed.append(process)
            if module.endswith("_rw0_d1_fake_" + target):
                forged = object.__new__(D1ProcessOutcome)
                for item in fields(D1ProcessOutcome):
                    object.__setattr__(forged, item.name,
                                       changes.get(item.name, getattr(process, item.name)))
                return forged
            return process

        monkeypatch.setattr(offline.tempfile, "mkdtemp", tracked_mkdtemp)
        monkeypatch.setattr(offline, "classify_wire_process_result", counted_classifier)
        monkeypatch.setattr(offline, "run_fake_module", substituted_process)
        with pytest.raises(ValueError, match="^invalid_d1_process_outcome$") as error:
            offline.run_rw0_d1_offline(work, offline.artificial_fixture(work))
        assert len(observed) == expected_launches
        assert classifications == 0
        assert new_roots and all(not root.exists() for root in new_roots)
        assert all(process.reaped and process.group_clear for process in observed)
        assert all(not supervisor._group_alive(process.process_group) for process in observed)
        assert live_run.closed is False and live_root.exists()
        assert str(live_root) not in str(error.value)
        assert all(str(root) not in str(error.value) for root in new_roots)
