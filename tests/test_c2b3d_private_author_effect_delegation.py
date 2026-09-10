from __future__ import annotations

import gc
import inspect
from pathlib import Path
import sqlite3
import traceback

import pytest

import ge_nwp_coordinator
import ge_nwp_coordinator._sqlite_development_author_effect_establishment as runtime
import ge_nwp_coordinator.sqlite_transition_transaction as transaction
from ge_nwp_coordinator._development_author_effect_establishment_contracts import (
    DevelopmentAuthorEffectEstablishmentCommandV1,
    DevelopmentAuthorEffectEstablishmentConflictReasonV1,
    DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1,
    DevelopmentAuthorEffectEstablishmentRecoveryResultV1,
    _author_effect_conflict,
)
from ge_nwp_coordinator._worker_execution_semantic_values import WorkSpecV1
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.state_store import WriterSession
from test_c2b3d_private_atomic_author_effect_establishment import (
    family_counts,
    make_author_effect_fixture,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = (
    ROOT
    / "src/ge_nwp_coordinator/_development_author_effect_establishment_contracts.py",
    ROOT / "src/ge_nwp_coordinator/_sqlite_development_author_effect_establishment.py",
)


class _HostileScalar:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def _called(self, name: str) -> object:
        self.calls.append(name)
        raise AssertionError(f"hostile scalar method called: {name}")

    def __eq__(self, other: object) -> object:
        return self._called("__eq__")

    def __str__(self) -> str:
        return self._called("__str__")

    def __repr__(self) -> str:
        return self._called("__repr__")


class _HostileString(str):
    def __new__(cls) -> "_HostileString":
        return str.__new__(cls, "hostile-subclass")

    def __eq__(self, other: object) -> object:
        raise AssertionError("hostile string equality called")

    def __str__(self) -> str:
        raise AssertionError("hostile string conversion called")


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


def _assert_clean_safe_error(error: SQLiteMutationStoreError) -> None:
    assert error.error_class == "database_integrity_failure"
    assert error.args == ("database_integrity_failure",)
    assert error.internal_detail is None
    assert error.__cause__ is None
    assert error.__context__ is None
    assert getattr(error, "__notes__", None) in (None, [])


def test_private_writer_reduces_before_guard_and_delegates_only_safe_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="delegate")
    raw_work_spec = fixture.work_spec
    captured: list[object] = []

    def delegate(*, operation_lease: object, command: object) -> object:
        captured.extend((operation_lease, command))
        assert type(command) is DevelopmentAuthorEffectEstablishmentCommandV1
        assert command == fixture.command
        assert command is not fixture.command
        assert not isinstance(command, WorkSpecV1)
        cursor = inspect.currentframe()
        found_writer = False
        while cursor is not None:
            if cursor.f_code.co_name == "_establish_development_author_effect_intent":
                found_writer = True
                for name in (
                    "work_spec",
                    "validation_requirement_evidence",
                    "review_requirement_evidence",
                    "attempt_fence",
                    "effect_authorization_safe_binding",
                ):
                    assert cursor.f_locals[name] is None
            cursor = cursor.f_back
        assert found_writer
        return _author_effect_conflict(
            command,
            DevelopmentAuthorEffectEstablishmentConflictReasonV1.SEMANTIC_IDENTITY_CONFLICT,
        )

    monkeypatch.setattr(
        transaction,
        "_run_atomic_development_author_effect_establishment",
        delegate,
    )
    try:
        result = fixture.writer._establish_development_author_effect_intent(
            **fixture.ingress
        )
        assert (
            result.reason
            is DevelopmentAuthorEffectEstablishmentConflictReasonV1.SEMANTIC_IDENTITY_CONFLICT
        )
        assert len(captured) == 2
        assert captured[1] is not raw_work_spec
        assert fixture.writer._resource._mutation_slot is None
        assert fixture.writer._resource._active_operations == {}
    finally:
        fixture.writer.close()


def test_private_recovery_uses_only_recovery_delegate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="recovery-delegate")
    captured: list[object] = []

    def forbidden_apply(*args: object, **kwargs: object) -> object:
        raise AssertionError("recovery invoked apply delegate")

    def recover(*, operation_lease: object, command: object) -> object:
        captured.extend((operation_lease, command))
        return DevelopmentAuthorEffectEstablishmentRecoveryResultV1(
            disposition=(
                DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1.DEFINITELY_NOT_COMMITTED
            )
        )

    monkeypatch.setattr(
        transaction,
        "_run_atomic_development_author_effect_establishment",
        forbidden_apply,
    )
    monkeypatch.setattr(
        transaction,
        "_run_development_author_effect_establishment_recovery",
        recover,
    )
    try:
        result = fixture.writer._resolve_development_author_effect_establishment_commit_outcome(
            fixture.command
        )
        assert (
            result.disposition
            is DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1.DEFINITELY_NOT_COMMITTED
        )
        assert captured[1] is fixture.command
        assert fixture.writer._resource._mutation_slot is None
    finally:
        fixture.writer.close()


def test_sensitive_reducer_clears_raw_work_spec_from_ordinary_error_graph(
    tmp_path: Path,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="ordinary-privacy")
    raw_work_spec = fixture.work_spec
    ingress = dict(fixture.ingress)
    ingress["program_ref"] = "different-program"
    caught: SQLiteMutationStoreError | None = None
    try:
        fixture.writer._establish_development_author_effect_intent(**ingress)
    except SQLiteMutationStoreError as error:
        caught = error
    finally:
        fixture.writer.close()
    assert caught is not None
    _assert_clean_safe_error(caught)
    assert not _contains_identity(caught.args, raw_work_spec, set())
    assert not _contains_identity(caught.__dict__, raw_work_spec, set())
    rendered = "".join(
        traceback.format_exception(type(caught), caught, caught.__traceback__)
    )
    assert "PRIVATE OBJECTIVE SENTINEL" not in rendered
    cursor = caught.__traceback__
    while cursor is not None:
        if "/src/ge_nwp_coordinator/" in cursor.tb_frame.f_code.co_filename:
            for value in cursor.tb_frame.f_locals.values():
                assert not _contains_identity(value, raw_work_spec, set())
        cursor = cursor.tb_next
    gc.collect()


def test_ordinary_pre_guard_failure_severs_active_caller_context_without_mutation(
    tmp_path: Path,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="ordinary-active-context")
    resource = fixture.writer._resource
    ingress = dict(fixture.ingress)
    ingress["program_ref"] = "different-program"
    private_marker = object()
    private_payload = (
        private_marker,
        {"nested": [fixture.work_spec]},
    )

    def raised_with_traceback(error: BaseException) -> BaseException:
        try:
            raise error
        except BaseException as caught:
            return caught

    cause = raised_with_traceback(LookupError("caller-owned-cause"))
    context = raised_with_traceback(ValueError("caller-owned-context"))
    prior_exception = RuntimeError("caller-owned-prior", private_payload)
    prior_reference: RuntimeError | None = None
    outward_error: SQLiteMutationStoreError | None = None
    prior_traceback: object | None = None
    prior_cause: BaseException | None = None
    prior_context: BaseException | None = None
    prior_args: tuple[object, ...] | None = None
    prior_notes: list[str] | None = None
    prior_dictionary: dict[str, object] | None = None
    prior_dictionary_snapshot: dict[str, object] | None = None
    prior_suppress_context: bool | None = None
    cause_traceback = cause.__traceback__
    context_traceback = context.__traceback__

    try:
        assert resource._active_operations == {}
        assert resource._mutation_slot is None
        assert resource._operation_exit_process_control_poisoned is False
        assert resource.active_for_owner() is True
        next_operation_id = resource._next_operation_id
        counts_before = family_counts(fixture.location)

        try:
            raise prior_exception
        except RuntimeError as prior:
            assert prior is prior_exception
            prior_reference = prior
            prior.__cause__ = cause
            prior.__context__ = context
            prior.__suppress_context__ = True
            prior.add_note("caller-owned-note")
            prior.caller_owned = {
                "marker": private_marker,
                "nested": [fixture.work_spec],
            }
            prior_traceback = prior.__traceback__
            prior_cause = prior.__cause__
            prior_context = prior.__context__
            prior_args = prior.args
            prior_notes = prior.__notes__
            prior_dictionary = prior.__dict__
            prior_dictionary_snapshot = dict(prior_dictionary)
            prior_suppress_context = prior.__suppress_context__

            try:
                fixture.writer._establish_development_author_effect_intent(**ingress)
            except SQLiteMutationStoreError as caught:
                outward_error = caught
            else:
                pytest.fail("ordinary reducer rejection did not escape")

        assert outward_error is not None
        assert type(outward_error) is SQLiteMutationStoreError
        assert outward_error.error_class == "database_integrity_failure"
        assert outward_error.args == ("database_integrity_failure",)
        assert outward_error.internal_detail is None
        if outward_error.__cause__ is not None:
            pytest.fail("outward ordinary error retained a cause")
        if outward_error.__context__ is not None:
            pytest.fail("outward ordinary error retained caller context")
        assert outward_error.__suppress_context__ is True
        assert getattr(outward_error, "__notes__", None) is None
        assert outward_error.__dict__ == {
            "error_class": "database_integrity_failure",
            "_internal_detail": None,
        }
        _assert_clean_safe_error(outward_error)

        prohibited = (
            private_marker,
            fixture.work_spec,
            prior_reference,
            cause,
            context,
        )
        for value in prohibited:
            assert not _contains_identity(outward_error.args, value, set())
            assert not _contains_identity(outward_error.__dict__, value, set())
            assert not _contains_identity(
                getattr(outward_error, "__notes__", None), value, set()
            )
        cursor = outward_error.__traceback__
        while cursor is not None:
            if cursor.tb_frame.f_code.co_filename.startswith(
                str(ROOT / "src/ge_nwp_coordinator")
            ):
                pytest.fail("outward ordinary error retained a Coordinator frame")
            cursor = cursor.tb_next

        assert prior_reference is prior_exception
        if prior_reference.__traceback__ is not prior_traceback:
            pytest.fail("caller traceback was mutated")
        assert prior_reference.__cause__ is prior_cause is cause
        assert prior_reference.__context__ is prior_context is context
        assert prior_reference.__suppress_context__ is prior_suppress_context
        assert prior_reference.args is prior_args
        assert prior_reference.args == ("caller-owned-prior", private_payload)
        assert prior_reference.__notes__ is prior_notes
        assert prior_reference.__notes__ == ["caller-owned-note"]
        assert prior_reference.__dict__ is prior_dictionary
        assert prior_reference.__dict__ == prior_dictionary_snapshot
        if cause.__traceback__ is not cause_traceback:
            pytest.fail("caller cause traceback was mutated")
        if context.__traceback__ is not context_traceback:
            pytest.fail("caller context traceback was mutated")

        assert resource._next_operation_id == next_operation_id
        assert resource._active_operations == {}
        assert resource._mutation_slot is None
        assert family_counts(fixture.location) == counts_before
        assert resource._operation_exit_process_control_poisoned is False
        assert resource.active_for_owner() is True
    finally:
        fixture.writer.close()
    gc.collect()


def test_process_control_identity_survives_reducer_and_raw_material_is_cleared(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="process-privacy")
    raw_work_spec = fixture.work_spec
    governing = KeyboardInterrupt("private-process-control-sentinel")

    def interrupt_from_mapping(mapping: object) -> object:
        raise governing

    monkeypatch.setattr(runtime.WorkSpecV1, "from_mapping", interrupt_from_mapping)
    caught: BaseException | None = None
    try:
        fixture.writer._establish_development_author_effect_intent(**fixture.ingress)
    except BaseException as error:
        caught = error
    finally:
        fixture.writer.close()
    assert caught is governing
    assert caught.__cause__ is None
    assert caught.__context__ is None
    rendered = "".join(
        traceback.format_exception(type(caught), caught, caught.__traceback__)
    )
    assert "PRIVATE OBJECTIVE SENTINEL" not in rendered
    cursor = caught.__traceback__
    while cursor is not None:
        if "/src/ge_nwp_coordinator/" in cursor.tb_frame.f_code.co_filename:
            for value in cursor.tb_frame.f_locals.values():
                assert not _contains_identity(value, raw_work_spec, set())
        cursor = cursor.tb_next
    gc.collect()


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("mutation_ref", _HostileScalar()),
        ("program_ref", _HostileString()),
        ("program_version_number", True),
        ("attempt_number", 1.0),
        ("coding_global_stop_version", False),
    ),
)
def test_exact_input_types_reject_without_database_or_hostile_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    fixture = make_author_effect_fixture(
        tmp_path,
        suffix=f"hostile-{field.replace('_', '-')}",
    )
    fixture.writer.close()
    ingress = dict(fixture.ingress)
    ingress[field] = value

    def forbidden_connect(*args: object, **kwargs: object) -> object:
        raise AssertionError("malformed input opened SQLite")

    monkeypatch.setattr(sqlite3, "connect", forbidden_connect)
    with pytest.raises(SQLiteMutationStoreError) as captured:
        runtime._reduce_development_author_effect_establishment_command(**ingress)
    _assert_clean_safe_error(captured.value)
    if type(value) is _HostileScalar:
        assert value.calls == []


def test_pending_authority_and_planned_delivery_are_nonexecutable(
    tmp_path: Path,
) -> None:
    fixture = make_author_effect_fixture(tmp_path, suffix="nonexecuting")
    try:
        fixture.writer._establish_development_author_effect_intent(**fixture.ingress)
        connection = sqlite3.connect(fixture.location.database_path)
        try:
            authority = connection.execute(
                "SELECT authority_state, reason_code, expires_at "
                "FROM development_authority_evaluations "
                "WHERE authority_evaluation_ref = ?",
                (fixture.command.authority_evaluation_ref,),
            ).fetchone()
            delivery = connection.execute(
                "SELECT delivery_state FROM development_delivery_heads "
                "WHERE effect_intent_ref = ?",
                (fixture.command.effect_intent_ref,),
            ).fetchone()
        finally:
            connection.close()
        assert authority == ("pending", "external_verification_pending", None)
        assert delivery == ("planned",)
        assert (
            fixture.command.delivery_envelope.adapter_kind == "direct_local_bootstrap"
        )
        ceilings = fixture.command.worker_command.effect_ceilings
        assert (
            ceilings.max_local_commits,
            ceilings.max_pushes,
            ceilings.max_pull_requests,
            ceilings.max_merges,
            ceilings.max_deployments,
        ) == (0, 0, 0, 0, 0)
    finally:
        fixture.writer.close()


def test_private_additions_do_not_widen_public_api_or_external_effect_surface() -> None:
    assert "_establish_development_author_effect_intent" not in WriterSession.__dict__
    assert (
        "_resolve_development_author_effect_establishment_commit_outcome"
        not in WriterSession.__dict__
    )
    assert not hasattr(
        ge_nwp_coordinator,
        "DevelopmentAuthorEffectEstablishmentCommandV1",
    )
    assert not hasattr(ge_nwp_coordinator, "establish_development_author_effect_intent")
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
    assert "WorkSpecV1" not in (
        ROOT / "src/ge_nwp_coordinator/sqlite_transition_transaction.py"
    ).read_text(encoding="utf-8")
