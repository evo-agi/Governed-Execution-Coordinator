from __future__ import annotations

import gc
from pathlib import Path
import sqlite3
import traceback

import pytest

import ge_nwp_coordinator
import ge_nwp_coordinator.sqlite_transition_transaction as transaction_module
from ge_nwp_coordinator._development_program_initialization_contracts import (
    DevelopmentProgramInitializationCommandV1,
    DevelopmentProgramInitializationConflictReasonV1,
    _initialization_conflict,
)
from ge_nwp_coordinator._sqlite_development_program_initialization import (
    _reduce_development_program_initialization_command,
)
from ge_nwp_coordinator._worker_execution_semantic_values import WorkSpecV1
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.state_store import WriterSession
from test_c2b3_private_atomic_program_initialization import PATHS, make_genesis_fixture


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = (
    ROOT
    / "src/ge_nwp_coordinator/_development_program_initialization_contracts.py",
    ROOT
    / "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py",
)


class _HostileScalar:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def _called(self, name: str) -> object:
        self.calls.append(name)
        raise AssertionError(f"hostile scalar method called: {name}")

    def __eq__(self, other: object) -> object:
        return self._called("__eq__")

    def __ne__(self, other: object) -> object:
        return self._called("__ne__")

    def __str__(self) -> str:
        return self._called("__str__")

    def __repr__(self) -> str:
        return self._called("__repr__")


def _contains_identity(value: object, target: object, seen: set[int]) -> bool:
    if value is target:
        return True
    identity = id(value)
    if identity in seen:
        return False
    seen.add(identity)
    if type(value) in (tuple, list, set, frozenset):
        return any(_contains_identity(item, target, seen) for item in value)
    if type(value) is dict:
        return any(
            _contains_identity(key, target, seen)
            or _contains_identity(item, target, seen)
            for key, item in value.items()
        )
    return False


def test_private_writer_delegation_passes_only_exact_safe_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_genesis_fixture(tmp_path)
    captured: list[object] = []

    def delegate(*, operation_lease: object, command: object) -> object:
        captured.extend((operation_lease, command))
        assert type(command) is DevelopmentProgramInitializationCommandV1
        assert not isinstance(command, WorkSpecV1)
        return _initialization_conflict(
            command,
            DevelopmentProgramInitializationConflictReasonV1.SEMANTIC_IDENTITY_CONFLICT,
        )

    monkeypatch.setattr(
        transaction_module,
        "_run_atomic_development_program_initialization",
        delegate,
    )
    try:
        result = fixture.writer_session._apply_development_program_initialization(
            fixture.command
        )
        assert result.reason is DevelopmentProgramInitializationConflictReasonV1.SEMANTIC_IDENTITY_CONFLICT
        assert captured[1] is fixture.command
        assert fixture.writer_session._resource._mutation_slot is None
        assert fixture.writer_session._resource._active_operations == {}
    finally:
        fixture.writer_session.close()


def test_sensitive_reducer_clears_raw_work_spec_from_safe_error_graph(
    tmp_path: Path,
) -> None:
    fixture = make_genesis_fixture(tmp_path)
    raw_work_spec = fixture.work_spec
    caught: SQLiteMutationStoreError | None = None
    try:
        fixture.writer_session._initialize_development_program(
            mutation_ref="mutation-private",
            program_ref="different-program",
            program_version_ref=raw_work_spec.program_version_ref,
            accepted_intent_revision_ref=raw_work_spec.accepted_intent_revision_ref,
            decision_ref="decision-private",
            preassigned_semantic_attempt_ref="semantic-attempt-private",
            preassigned_candidate_ref="candidate-private",
            coding_global_stop_ref="global-stop-clear",
            coding_global_stop_version=0,
            source_intent_ref="source-intent-private",
            source_intent_digest="1" * 64,
            work_spec=raw_work_spec,
        )
    except SQLiteMutationStoreError as error:
        caught = error
    finally:
        fixture.writer_session.close()
    assert caught is not None
    assert caught.error_class == "database_integrity_failure"
    assert caught.__cause__ is None
    assert caught.__context__ is None
    assert getattr(caught, "__notes__", None) in (None, [])
    assert not _contains_identity(caught.args, raw_work_spec, set())
    assert not _contains_identity(caught.__dict__, raw_work_spec, set())
    assert "PRIVATE OBJECTIVE SENTINEL" not in "".join(
        traceback.format_exception(type(caught), caught, caught.__traceback__)
    )
    cursor = caught.__traceback__
    while cursor is not None:
        if "/src/ge_nwp_coordinator/" in cursor.tb_frame.f_code.co_filename:
            for value in cursor.tb_frame.f_locals.values():
                assert not _contains_identity(value, raw_work_spec, set())
        cursor = cursor.tb_next
    gc.collect()


@pytest.mark.parametrize(
    "hostile_field",
    (
        "mutation_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "decision_ref",
        "preassigned_semantic_attempt_ref",
        "preassigned_candidate_ref",
        "coding_global_stop_ref",
        "source_intent_ref",
    ),
)
def test_sensitive_reducer_validates_each_supplied_ref_before_relational_comparison(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    hostile_field: str,
) -> None:
    raw_work_spec = WorkSpecV1.create(
        work_spec_ref="work-spec-hostile",
        program_ref="program-hostile",
        program_version_ref="program-version-hostile",
        accepted_intent_revision_ref="accepted-intent-hostile",
        work_item_ref="work-item-hostile",
        work_item_revision_ref="work-item-revision-hostile",
        repository_ref="repository-hostile",
        base_git_oid="2" * 40,
        authorized_paths=list(PATHS),
        objective="PRIVATE HOSTILE OBJECTIVE SENTINEL",
        requirements=["PRIVATE HOSTILE REQUIREMENT SENTINEL"],
        exclusions=["PRIVATE HOSTILE EXCLUSION SENTINEL"],
        validation_requirement_ref="validation-hostile",
        review_requirement_ref="review-hostile",
    )
    hostile = _HostileScalar()
    arguments: dict[str, object] = {
        "mutation_ref": "mutation-hostile",
        "program_ref": raw_work_spec.program_ref,
        "program_version_ref": raw_work_spec.program_version_ref,
        "accepted_intent_revision_ref": raw_work_spec.accepted_intent_revision_ref,
        "decision_ref": "decision-hostile",
        "preassigned_semantic_attempt_ref": "semantic-attempt-hostile",
        "preassigned_candidate_ref": "candidate-hostile",
        "coding_global_stop_ref": "global-stop-clear",
        "coding_global_stop_version": 0,
        "source_intent_ref": "source-intent-hostile",
        "source_intent_digest": "1" * 64,
        "work_spec": raw_work_spec,
    }
    arguments[hostile_field] = hostile

    def forbidden_database_open(*args: object, **kwargs: object) -> object:
        raise AssertionError("malformed scalar opened a database")

    monkeypatch.setattr(sqlite3, "connect", forbidden_database_open)
    caught: SQLiteMutationStoreError | None = None
    try:
        _reduce_development_program_initialization_command(**arguments)
    except SQLiteMutationStoreError as error:
        caught = error
    assert caught is not None
    assert caught.error_class == "database_integrity_failure"
    assert caught.args == ("database_integrity_failure",)
    assert caught.internal_detail is None
    assert caught.__cause__ is None
    assert caught.__context__ is None
    assert hostile.calls == []
    assert not _contains_identity(caught.args, raw_work_spec, set())
    assert not _contains_identity(caught.__dict__, raw_work_spec, set())
    assert "PRIVATE HOSTILE OBJECTIVE SENTINEL" not in "".join(
        traceback.format_exception(type(caught), caught, caught.__traceback__)
    )
    cursor = caught.__traceback__
    while cursor is not None:
        if "/src/ge_nwp_coordinator/" in cursor.tb_frame.f_code.co_filename:
            for value in cursor.tb_frame.f_locals.values():
                assert not _contains_identity(value, raw_work_spec, set())
        cursor = cursor.tb_next
    assert tuple(tmp_path.iterdir()) == ()
    gc.collect()


def test_private_additions_do_not_widen_public_api_or_select_route() -> None:
    assert "_initialize_development_program" not in WriterSession.__dict__
    assert (
        "_resolve_development_program_initialization_commit_outcome"
        not in WriterSession.__dict__
    )
    assert not hasattr(ge_nwp_coordinator, "DevelopmentProgramInitializationCommandV1")
    assert not hasattr(ge_nwp_coordinator, "initialize_development_program")
    combined = "\n".join(path.read_text(encoding="utf-8") for path in SOURCE_PATHS)
    for prohibited in (
        "requests.",
        "urllib",
        "socket.",
        "subprocess",
        "ExecutionSubstrate",
        "OpenAIBridge",
        "git commit",
        "bootstrap_latch",
    ):
        assert prohibited not in combined
    assert "WorkSpecV1" not in Path(
        ROOT / "src/ge_nwp_coordinator/sqlite_transition_transaction.py"
    ).read_text(encoding="utf-8")
