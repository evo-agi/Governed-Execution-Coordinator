from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
import json
import os
from pathlib import Path, PurePath
import pickle
from typing import get_type_hints

import pytest

from ge_nwp_coordinator._cognitive_proposal_semantic_values import PreExecutionProposalSelectionBundleV1
from ge_nwp_coordinator._development_author_effect_establishment_contracts import (
    DevelopmentAuthorEffectEstablishmentCommandV1,
    DevelopmentAuthorEffectEstablishmentResultV1,
)
from ge_nwp_coordinator._development_pre_execution_plan_disposition_contracts import PreExecutionPlanDispositionResultV1
from ge_nwp_coordinator._development_program_initialization_contracts import DevelopmentProgramInitializationResultV1
from ge_nwp_coordinator._rw0_c1_semantic_values import RW0C1EstablishPhaseResultV1
from ge_nwp_coordinator._rw0_d1_handback import RW0D1HandbackV1, _D1RunOwnershipError
from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture, run_rw0_d1_offline
from ge_nwp_coordinator._rw0_d1_process_supervisor import D1ProcessOutcome
from ge_nwp_coordinator._rw0_d1_workspace import D1CandidateCapture, D1CapturedEntry
from ge_nwp_coordinator._rw0_phase_entry_semantic_values import RW0PhaseEntryBasisV1
from ge_nwp_coordinator._rw0_wire_protocol_values import (
    RW0WireProcessResultClassificationV1, RW0WireWorkerResultV1,
)
from ge_nwp_coordinator._worker_execution_semantic_values import CandidateCapsuleManifestV1
from test_rw0_d1_offline_integration import work_spec


_EVIDENCE_TYPES = {
    "program_result": DevelopmentProgramInitializationResultV1,
    "author_result": DevelopmentAuthorEffectEstablishmentResultV1,
    "author_command": DevelopmentAuthorEffectEstablishmentCommandV1,
    "section41_result": PreExecutionPlanDispositionResultV1,
    "selected_bundle": PreExecutionProposalSelectionBundleV1,
    "phase_basis": RW0PhaseEntryBasisV1,
    "phase_result": RW0C1EstablishPhaseResultV1,
    "planner_process": D1ProcessOutcome,
    "worker_process": D1ProcessOutcome,
    "wire_result": RW0WireWorkerResultV1,
    "wire_classification": RW0WireProcessResultClassificationV1,
    "capture": D1CandidateCapture,
    "capsule_manifest": CandidateCapsuleManifestV1,
}


def test_fixed_handback_field_inventory_types_and_repr_flags() -> None:
    expected = (
        "status", "reason", "program_result", "author_result", "author_command",
        "section41_result", "selected_bundle", "phase_basis", "phase_result",
        "planner_process", "worker_process", "wire_result", "wire_classification",
        "capture", "capsule_manifest", "workspace_cleaned",
    )
    actual = fields(RW0D1HandbackV1)
    assert tuple(item.name for item in actual) == expected
    hints = get_type_hints(RW0D1HandbackV1)
    assert hints == {
        "status": str, "reason": str,
        **{name: value | None for name, value in _EVIDENCE_TYPES.items()},
        "workspace_cleaned": bool,
    }
    assert {item.name: item.repr for item in actual} == {
        name: name in {"status", "reason", "workspace_cleaned"}
        for name in expected
    }


def test_closed_status_reason_and_ready_requirements() -> None:
    with pytest.raises(ValueError):
        RW0D1HandbackV1("ready", "complete")
    with pytest.raises(ValueError):
        RW0D1HandbackV1("stopped", "complete")
    with pytest.raises(ValueError):
        RW0D1HandbackV1("capsule_ready", "complete")
    with pytest.raises(ValueError):
        RW0D1HandbackV1("stopped", "made-up-reason")
    for status, reason in (
        ("stopped", "process_cleanup_unresolved"),
        ("stopped", "planner_cleanup_unresolved"),
        ("stopped", "worker_cleanup_unresolved"),
        ("stopped", "workspace_cleanup_unresolved"),
        ("cleanup_unresolved", "durable_conflict"),
        ("cleanup_unresolved", "complete"),
    ):
        with pytest.raises(ValueError, match="^invalid_d1_handback$"):
            RW0D1HandbackV1(status, reason)
    for reason in ("planner_cleanup_unresolved", "worker_cleanup_unresolved"):
        with pytest.raises(ValueError, match="^invalid_d1_handback$"):
            RW0D1HandbackV1("cleanup_unresolved", reason)


def test_success_handback_requires_every_typed_stage_and_hides_roots() -> None:
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as run:
        handback = run.handback
        assert handback.status == "capsule_ready"
        root = run.location.state_root
        database = run.location.database_path
        for name in _EVIDENCE_TYPES:
            with pytest.raises(ValueError, match="^invalid_d1_handback$"):
                replace(handback, **{name: None})
            for leak in (root, database):
                with pytest.raises(ValueError, match="^invalid_d1_handback$"):
                    replace(handback, **{name: leak})
            for wrong in ([], {}, True):
                with pytest.raises(ValueError, match="^invalid_d1_handback$"):
                    replace(handback, **{name: wrong})
        with pytest.raises(ValueError):
            replace(handback, workspace_cleaned=False)
        with pytest.raises(ValueError):
            replace(handback, status="stopped", reason="worker_frame")
        with pytest.raises(ValueError):
            replace(handback, status="cleanup_unresolved", reason="worker_frame")
        with pytest.raises(ValueError):
            replace(handback, reason="worker_cleanup_unresolved")
        with pytest.raises(ValueError):
            replace(handback, worker_process=replace(handback.worker_process, reason="deadline"))
        with pytest.raises(ValueError):
            replace(handback, author_result=None, author_command=None)
        retained = replace(handback, status="cleanup_unresolved",
                           reason="workspace_cleanup_unresolved", workspace_cleaned=False)
        assert retained.capsule_manifest is handback.capsule_manifest
        assert retained.worker_process is handback.worker_process
        with pytest.raises(ValueError):
            replace(handback, status="cleanup_unresolved",
                    reason="workspace_cleanup_unresolved")
        with pytest.raises(ValueError):
            replace(handback, status="cleanup_unresolved",
                    reason="worker_cleanup_unresolved")
        unproved_worker = replace(handback.worker_process, cleanup_reason="selector_close")
        worker_cleanup = replace(
            handback, status="cleanup_unresolved", reason="worker_cleanup_unresolved",
            worker_process=unproved_worker, wire_result=None,
            wire_classification=None, capture=None, capsule_manifest=None,
        )
        assert worker_cleanup.worker_process is unproved_worker
        unproved_planner = replace(handback.planner_process, cleanup_reason="selector_close")
        planner_cleanup = RW0D1HandbackV1(
            "cleanup_unresolved", "planner_cleanup_unresolved",
            program_result=handback.program_result,
            author_result=handback.author_result,
            author_command=handback.author_command,
            planner_process=unproved_planner,
        )
        assert planner_cleanup.planner_process is unproved_planner

        # Only the declared handback graph is traversed; no arbitrary object
        # attributes or live run-owner internals are inspected.
        forbidden = (str(root), str(database))
        seen: set[int] = set()

        def walk(value: object) -> None:
            if id(value) in seen:
                return
            seen.add(id(value))
            assert not isinstance(value, (PurePath, os.PathLike))
            assert type(value).__name__ not in {
                "RW0D1OfflineRun", "_SQLiteWriterSession", "Connection",
                "CoordinatorStateLocation", "_MutationReadCapability",
            }
            if type(value) is str:
                assert all(secret not in value for secret in forbidden)
            elif type(value) is bytes:
                assert all(secret.encode() not in value for secret in forbidden)
            elif type(value) in (tuple, list, set, frozenset):
                for member in value:
                    walk(member)
            elif type(value) is dict:
                for key, member in value.items():
                    walk(key)
                    walk(member)
            elif type(value) is D1ProcessOutcome:
                for item in fields(value):
                    walk(getattr(value, item.name))
            elif type(value) is D1CandidateCapture:
                walk(value.entries)
                walk(value.changed_path)
            elif type(value) is D1CapturedEntry:
                for item in fields(value):
                    walk(getattr(value, item.name))
            elif type(value) in _EVIDENCE_TYPES.values():
                mapping = getattr(value, "to_mapping", None)
                if mapping is not None:
                    walk(mapping())

        assert tuple(item.name for item in fields(handback)) == tuple(
            item.name for item in fields(RW0D1HandbackV1)
        )
        for item in fields(handback):
            walk(getattr(handback, item.name))
        display = repr(handback) + repr(run)
        assert all(secret not in display for secret in forbidden)
        assert work.objective not in display
        assert handback.capture.entries[0].before.decode() not in display


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX fork")
def test_run_owner_rejects_inherited_custody_and_parent_closes() -> None:
    work = work_spec()
    run = run_rw0_d1_offline(work, artificial_fixture(work))
    root = run.location.state_root
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        results = []
        for action in (
            lambda: run.location, lambda: run.closed, run.close,
            run.__enter__, lambda: run.__exit__(None, None, None),
        ):
            try:
                action()
            except _D1RunOwnershipError as error:
                results.append(str(error) == "d1_run_wrong_process")
            else:
                results.append(False)
        results.extend((run.handback.status == "capsule_ready", root.exists()))
        os.write(write_fd, json.dumps(results).encode())
        os.close(write_fd)
        os._exit(0)
    os.close(write_fd)
    try:
        report = os.read(read_fd, 1024)
        _pid, status = os.waitpid(pid, 0)
        assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
        assert json.loads(report) == [True] * 7
        assert run.closed is False
        assert root.exists()
        run.close()
        run.close()
        assert run.closed
        assert not root.exists()
    finally:
        os.close(read_fd)
        if not run.closed:
            run.close()


def test_handback_is_nonprinting_and_state_owner_is_distinct() -> None:
    work = work_spec()
    run = run_rw0_d1_offline(work, artificial_fixture(work))
    location = run.location
    try:
        h = run.handback
        assert h.status == "capsule_ready"
        assert "Artificial" not in repr(h)
        assert str(h) == "RW0D1HandbackV1"
        assert str(location.database_path) not in repr(h)
        assert str(location.database_path) not in repr(run)
        with pytest.raises(TypeError):
            pickle.dumps(h)
        with pytest.raises(TypeError):
            pickle.dumps(run)
        with pytest.raises(FrozenInstanceError):
            h.status = "stopped"
    finally:
        run.close()
        run.close()
    assert run.closed
    assert not Path(location.database_path).exists()


_PREFIX = (
    "program_result", "author_result", "author_command", "planner_process",
    "selected_bundle", "section41_result", "phase_basis", "phase_result",
    "worker_process", "wire_result", "wire_classification", "capture",
    "capsule_manifest",
)
_EXPECTED_EXITS = {
    "complete": ("capsule_ready", (13,)),
    "invalid_input": ("stopped", (0,)),
    "durable_commit_unresolved": ("stopped", (0, 1, 5, 7)),
    "durable_conflict": ("stopped", (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)),
    "planner_start": ("stopped", (4,)),
    "planner_frame": ("stopped", (4,)),
    "planner_limit": ("stopped", (4,)),
    "planner_exit": ("stopped", (4,)),
    "planner_deadline": ("stopped", (4,)),
    "planner_cancelled": ("stopped", (4,)),
    "nonselection": ("stopped", (6,)),
    "c1_phase_failure": ("stopped", ()),
    "worker_start": ("stopped", (9,)),
    "worker_frame": ("stopped", (9, 11)),
    "worker_limit": ("stopped", (9,)),
    "worker_exit": ("stopped", (9,)),
    "worker_deadline": ("stopped", (9,)),
    "worker_cancelled": ("stopped", (9,)),
    "unsafe_candidate": ("stopped", (11,)),
    "missing_candidate": ("stopped", (11,)),
    "excessive_candidate": ("stopped", (11,)),
    "capsule_mismatch": ("stopped", (12,)),
    "process_cleanup_unresolved": ("cleanup_unresolved", (0, 1, 2, 3, 4, 5, 6, 7, 8)),
    "planner_cleanup_unresolved": ("cleanup_unresolved", (4,)),
    "worker_cleanup_unresolved": ("cleanup_unresolved", (9,)),
    "workspace_cleanup_unresolved": ("cleanup_unresolved", (8, 9, 10, 11, 12, 13)),
}
_FAILURE_PROCESS_REASONS = {
    "planner_limit": "output_limit", "planner_exit": "nonzero_exit",
    "planner_deadline": "deadline", "planner_cancelled": "cancelled",
    "worker_limit": "output_limit", "worker_exit": "nonzero_exit",
    "worker_deadline": "deadline", "worker_cancelled": "cancelled",
}


def _exit_specimen(success: RW0D1HandbackV1, deferred: RW0D1HandbackV1,
                   reason: str, stage: int) -> RW0D1HandbackV1:
    status, _stages = _EXPECTED_EXITS[reason]
    source = deferred if reason == "nonselection" else success
    facts = {name: getattr(source, name) for name in _PREFIX[:stage]}
    if reason in {"planner_start", "worker_start"}:
        facts["planner_process" if reason == "planner_start" else "worker_process"] = (
            D1ProcessOutcome("start_failed", None, None, None, b"", b"")
        )
    elif reason in _FAILURE_PROCESS_REASONS:
        name = "planner_process" if reason.startswith("planner") else "worker_process"
        process_reason = _FAILURE_PROCESS_REASONS[reason]
        changes: dict[str, object] = {"reason": process_reason}
        if process_reason == "nonzero_exit":
            changes["exit_code"] = 17
        elif process_reason == "cancelled":
            changes["cancellation_requested"] = True
        elif process_reason == "stderr_limit":
            changes["stderr"] = b"limit exceeded"
        facts[name] = replace(facts[name], **changes)
    elif reason == "planner_cleanup_unresolved":
        facts["planner_process"] = replace(facts["planner_process"],
                                           cleanup_reason="selector_close")
    elif reason == "worker_cleanup_unresolved":
        facts["worker_process"] = replace(facts["worker_process"],
                                          cleanup_reason="selector_close")
    elif reason == "worker_frame" and stage == 11:
        facts["wire_classification"] = RW0WireProcessResultClassificationV1._create(
            "unusable", "process_failed",
        )
    return RW0D1HandbackV1(
        status, reason, workspace_cleaned=(stage >= 9 and
                                            reason != "workspace_cleanup_unresolved"),
        **facts,
    )


def test_fixed_reason_prefix_matrix_and_neighboring_stage_rejections() -> None:
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as success_run:
        with run_rw0_d1_offline(
            work, artificial_fixture(work, planner_behavior="defer"),
        ) as deferred_run:
            success = success_run.handback
            deferred = deferred_run.handback
            assert set(_EXPECTED_EXITS) == {
                "complete", "invalid_input", "durable_commit_unresolved",
                "durable_conflict", "planner_start", "planner_frame",
                "planner_limit", "planner_exit", "planner_deadline",
                "planner_cancelled", "nonselection", "c1_phase_failure",
                "worker_start", "worker_frame", "worker_limit", "worker_exit",
                "worker_deadline", "worker_cancelled", "unsafe_candidate",
                "missing_candidate", "excessive_candidate", "capsule_mismatch",
                "process_cleanup_unresolved", "planner_cleanup_unresolved",
                "worker_cleanup_unresolved", "workspace_cleanup_unresolved",
            }
            for reason, (status, stages) in _EXPECTED_EXITS.items():
                if not stages:
                    with pytest.raises(ValueError, match="^invalid_d1_handback$"):
                        RW0D1HandbackV1(status, reason)
                    continue
                for stage in stages:
                    specimen = _exit_specimen(success, deferred, reason, stage)
                    assert (specimen.status, specimen.reason) == (status, reason)
                    if stage > 1:
                        with pytest.raises(ValueError, match="^invalid_d1_handback$"):
                            replace(specimen, program_result=None)
                    if reason in {
                        "invalid_input", "planner_start", "planner_frame",
                        "planner_limit", "planner_exit", "planner_deadline",
                        "planner_cancelled", "nonselection", "worker_start",
                        "worker_frame", "worker_limit", "worker_exit",
                        "worker_deadline", "worker_cancelled", "unsafe_candidate",
                        "missing_candidate", "excessive_candidate", "capsule_mismatch",
                    } and stage < 13:
                        with pytest.raises(ValueError, match="^invalid_d1_handback$"):
                            replace(specimen, **{
                                _PREFIX[stage]: getattr(success, _PREFIX[stage]),
                            })
                    if status == "stopped":
                        with pytest.raises(ValueError, match="^invalid_d1_handback$"):
                            replace(specimen, status="cleanup_unresolved")
                    elif status == "cleanup_unresolved":
                        with pytest.raises(ValueError, match="^invalid_d1_handback$"):
                            replace(specimen, status="stopped")
            for reason in ("invalid_input", "planner_frame", "worker_start"):
                with pytest.raises(ValueError, match="^invalid_d1_handback$"):
                    replace(success, status="stopped", reason=reason,
                            capsule_manifest=None)
            with pytest.raises(ValueError, match="^invalid_d1_handback$"):
                replace(_exit_specimen(success, deferred, "worker_start", 9),
                        worker_process=success.worker_process)


def _forged_capture(capture: D1CandidateCapture, role: str, hostile: object) -> D1CandidateCapture:
    forged = object.__new__(D1CandidateCapture)
    entries: object = capture.entries
    changed_path: object = capture.changed_path
    if role == "entries":
        entries = hostile
    elif role == "entry":
        entries = (capture.entries[0], hostile, capture.entries[2])
    elif role == "changed_path":
        changed_path = hostile
    else:
        entry = object.__new__(D1CapturedEntry)
        for name in ("path", "mode", "before", "after"):
            object.__setattr__(entry, name, hostile if name == role
                               else getattr(capture.entries[2], name))
        entries = (capture.entries[0], capture.entries[1], entry)
    object.__setattr__(forged, "entries", entries)
    object.__setattr__(forged, "changed_path", changed_path)
    return forged


def test_live_resource_and_object_cannot_cross_any_capture_role_or_handback_status() -> None:
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as run:
        handback = run.handback
        for hostile in (run, object(), run.location.state_root):
            for role in ("entries", "entry", "changed_path", "path", "mode",
                         "before", "after"):
                forged = _forged_capture(handback.capture, role, hostile)
                for status, reason, changes in (
                    ("capsule_ready", "complete", {}),
                    ("stopped", "capsule_mismatch", {"capsule_manifest": None}),
                    ("cleanup_unresolved", "workspace_cleanup_unresolved",
                     {"workspace_cleaned": False}),
                ):
                    with pytest.raises(ValueError, match="^invalid_d1_handback$"):
                        replace(handback, status=status, reason=reason,
                                capture=forged, **changes)
        assert run.closed is False
        assert run.location.state_root.exists()


def _forged_process(value: D1ProcessOutcome, **changes: object) -> D1ProcessOutcome:
    forged = object.__new__(D1ProcessOutcome)
    for item in fields(D1ProcessOutcome):
        object.__setattr__(forged, item.name,
                           changes.get(item.name, getattr(value, item.name)))
    return forged


def test_both_processes_are_revalidated_at_every_handback_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as run:
        success = run.handback
        database = run.location.database_path
        before = database.read_bytes()
        before_mtime = database.stat().st_mtime_ns
        import ge_nwp_coordinator._rw0_d1_process_supervisor as supervisor
        monkeypatch.setattr(supervisor, "_group_alive", lambda _pgid: (_ for _ in ()).throw(
            AssertionError("handback must not query process existence")))

        # Each specimen is otherwise valid at its own reason/prefix stage.
        categories = (
            success,
            _exit_specimen(success, success, "planner_frame", 4),
            _exit_specimen(success, success, "worker_frame", 9),
            _exit_specimen(success, success, "worker_frame", 11),
            _exit_specimen(success, success, "durable_conflict", 4),
            _exit_specimen(success, success, "durable_conflict", 9),
            _exit_specimen(success, success, "planner_cleanup_unresolved", 4),
            _exit_specimen(success, success, "worker_cleanup_unresolved", 9),
            _exit_specimen(success, success, "workspace_cleanup_unresolved", 13),
        )
        for specimen in categories:
            for name in ("planner_process", "worker_process"):
                process = getattr(specimen, name)
                if process is None:
                    continue
                for changes in ({"exit_code": 99}, {"exit_code": None},
                                {"pid": -1}, {"process_group": -1}):
                    forged = _forged_process(process, **changes)
                    with pytest.raises(ValueError, match="^invalid_d1_handback$"):
                        replace(specimen, **{name: forged})

        # This is the reported ready-handback mutation, including neighboring
        # primitive and fixed-launch group contradictions for both process roles.
        class IntSubclass(int):
            pass

        for name in ("planner_process", "worker_process"):
            process = getattr(success, name)
            mutations = (
                {"exit_code": 99}, {"exit_code": None}, {"exit_code": -15},
                {"exit_code": False}, {"exit_code": IntSubclass(0)},
                *({"pid": value} for value in (-1, 0, None, True, IntSubclass(process.pid))),
                *({"process_group": value} for value in (
                    -1, 0, None, True, IntSubclass(process.process_group), process.pid + 1,
                )),
                {"pid": -1, "process_group": -1},
                {"pid": 0, "process_group": 0},
                {"pid": True, "process_group": True},
                {"pid": IntSubclass(process.pid),
                 "process_group": IntSubclass(process.process_group)},
                {"reaped": False}, {"group_clear": False},
                {"cleanup_reason": "process_control"},
            )
            for changes in mutations:
                with pytest.raises(ValueError, match="^invalid_d1_handback$"):
                    replace(success, **{name: _forged_process(process, **changes)})
                with pytest.raises(ValueError, match="^invalid_d1_process_outcome$"):
                    replace(process, **changes)

        valid_failure = replace(success.worker_process, reason="nonzero_exit", exit_code=99)
        assert valid_failure.validate() is None
        with pytest.raises(ValueError, match="^invalid_d1_handback$"):
            replace(success, worker_process=valid_failure)
        unusable = RW0WireProcessResultClassificationV1._create(
            "unusable", "process_failed",
        )
        with pytest.raises(ValueError, match="^invalid_d1_handback$"):
            replace(success, wire_classification=unusable)
        assert database.read_bytes() == before
        assert database.stat().st_mtime_ns == before_mtime


def test_valid_failed_planner_cannot_appear_in_later_handback_prefix() -> None:
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as run:
        success = run.handback
        failed_planner = replace(
            success.planner_process, reason="nonzero_exit", exit_code=17,
        )
        assert failed_planner.validate() is None
        assert failed_planner.pid > 0
        assert failed_planner.process_group == failed_planner.pid
        assert failed_planner.reaped and failed_planner.group_clear
        assert failed_planner.cleanup_complete and not failed_planner.clean_success

        # The same valid failure belongs to its own planner-stage handback.
        own_stage = _exit_specimen(success, success, "planner_exit", 4)
        assert own_stage.planner_process == failed_planner
        assert (own_stage.status, own_stage.reason) == ("stopped", "planner_exit")

        worker_start = _exit_specimen(success, success, "worker_start", 9)
        assert worker_start.planner_process.clean_success
        assert worker_start.worker_process.reason == "start_failed"
        assert worker_start.worker_process.pid is None
        assert worker_start.phase_result is success.phase_result
        assert worker_start.workspace_cleaned

        later_stages = (
            worker_start,
            _exit_specimen(success, success, "durable_conflict", 9),
            _exit_specimen(success, success, "worker_cleanup_unresolved", 9),
            success,
        )
        for valid_stage in later_stages:
            assert valid_stage.planner_process.clean_success
            with pytest.raises(ValueError, match="^invalid_d1_handback$"):
                replace(valid_stage, planner_process=failed_planner)
