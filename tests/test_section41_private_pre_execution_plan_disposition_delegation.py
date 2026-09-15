from __future__ import annotations

from pathlib import Path

import pytest

import ge_nwp_coordinator
import ge_nwp_coordinator.sqlite_transition_transaction as transaction
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError,
    SQLiteMutationStoreErrorCode,
)
from ge_nwp_coordinator.state_store import WriterSession
from test_section41_private_atomic_pre_execution_plan_disposition import (
    make_section41_fixture,
)


def test_private_ingress_delegates_once_with_operation_lease_and_input_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="delegate")
    recovery_probe = fixture.recovery_probe
    sentinel = object()
    calls: list[dict[str, object]] = []

    def delegate(**kwargs: object) -> object:
        calls.append(kwargs)
        return sentinel

    monkeypatch.setattr(
        transaction,
        "_run_atomic_pre_execution_plan_disposition",
        delegate,
    )
    result = fixture.author.writer._record_pre_execution_plan_disposition(
        fixture.mutation_ref,
        fixture.command_digest,
        fixture.bundle,
        fixture.identity,
        recovery_probe,
    )
    assert result is sentinel
    assert len(calls) == 1
    call = calls[0]
    assert type(call["operation_lease"]).__name__ == "_WriterSessionOperationLease"
    assert call["bundle"] is fixture.bundle
    assert call["disposition_identity"] is fixture.identity
    assert call["mutation_ref"] is fixture.mutation_ref
    assert call["mutation_command_digest"] is fixture.command_digest
    assert call["recovery_probe"].to_mapping() == recovery_probe.to_mapping()
    fixture.author.writer.close()


def test_private_recovery_delegates_exact_probe_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="recover-delegate")
    probe = fixture.recovery_probe
    sentinel = object()
    calls: list[dict[str, object]] = []

    def delegate(**kwargs: object) -> object:
        calls.append(kwargs)
        return sentinel

    monkeypatch.setattr(
        transaction,
        "_run_pre_execution_plan_disposition_recovery",
        delegate,
    )
    result = (
        fixture.author.writer._resolve_pre_execution_plan_disposition_commit_outcome(
            probe
        )
    )
    assert result is sentinel
    assert len(calls) == 1
    assert calls[0]["probe"].to_mapping() == probe.to_mapping()
    assert calls[0]["probe"] is not probe
    assert type(calls[0]["operation_lease"]).__name__ == "_WriterSessionOperationLease"
    fixture.author.writer.close()


def test_malformed_nominal_carrier_fails_before_delegate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="bad-carrier")

    def delegate(**kwargs: object) -> object:
        raise AssertionError("delegate reached")

    monkeypatch.setattr(
        transaction,
        "_run_atomic_pre_execution_plan_disposition",
        delegate,
    )
    with pytest.raises(SQLiteMutationStoreError) as caught:
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            object(),
            fixture.identity,
            fixture.recovery_probe,
        )
    assert (
        caught.value.error_class
        == SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value
    )
    fixture.author.writer.close()


def test_process_control_identity_crosses_private_delegation_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="process-control")
    recovery_probe = fixture.recovery_probe
    governing = KeyboardInterrupt()

    def delegate(**kwargs: object) -> object:
        raise governing

    monkeypatch.setattr(
        transaction,
        "_run_atomic_pre_execution_plan_disposition",
        delegate,
    )
    with pytest.raises(KeyboardInterrupt) as caught:
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            recovery_probe,
        )
    assert caught.value is governing
    fixture.author.writer.close()


@pytest.mark.parametrize("exception_type", (SystemExit, GeneratorExit))
def test_remaining_process_control_identities_cross_private_delegation_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    exception_type: type[BaseException],
) -> None:
    fixture = make_section41_fixture(
        tmp_path,
        suffix=f"process-control-{exception_type.__name__}",
    )
    recovery_probe = fixture.recovery_probe
    governing = exception_type("direct-trusted-process-control")

    def delegate(**kwargs: object) -> object:
        raise governing

    monkeypatch.setattr(
        transaction,
        "_run_atomic_pre_execution_plan_disposition",
        delegate,
    )
    with pytest.raises(exception_type) as caught:
        fixture.author.writer._record_pre_execution_plan_disposition(
            fixture.mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            recovery_probe,
        )
    assert caught.value is governing
    fixture.author.writer.close()


def test_private_surface_does_not_widen_public_protocol_or_package() -> None:
    assert not hasattr(WriterSession, "_record_pre_execution_plan_disposition")
    assert not hasattr(
        WriterSession,
        "_resolve_pre_execution_plan_disposition_commit_outcome",
    )
    assert not hasattr(ge_nwp_coordinator, "PreExecutionPlanDispositionResultV1")


def _exact_container_contains(value: object, target: str) -> bool:
    if type(value) is str:
        return value == target
    if type(value) in (tuple, list, set, frozenset):
        return any(_exact_container_contains(member, target) for member in value)
    if type(value) is dict:
        return any(
            _exact_container_contains(member, target)
            for pair in value.items()
            for member in pair
        )
    return False


@pytest.mark.parametrize(
    "raw_mutation_ref",
    ("surrogate-\ud800-secret", "raw-sensitive-mutation-ref"),
)
def test_private_preguard_outward_error_graph_and_library_traceback_locals_are_content_free(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    raw_mutation_ref: str,
) -> None:
    fixture = make_section41_fixture(tmp_path, suffix="privacy-preguard")
    recovery_probe = fixture.recovery_probe
    delegate_calls = 0

    def delegate(**kwargs: object) -> object:
        nonlocal delegate_calls
        delegate_calls += 1
        return object()

    monkeypatch.setattr(
        type(fixture.author.writer),
        "_run_pre_execution_plan_disposition_operation",
        delegate,
    )
    with pytest.raises(SQLiteMutationStoreError) as caught:
        fixture.author.writer._record_pre_execution_plan_disposition(
            raw_mutation_ref,
            fixture.command_digest,
            fixture.bundle,
            fixture.identity,
            recovery_probe,
        )
    error = caught.value
    assert delegate_calls == 0
    assert error.__cause__ is None
    assert error.__context__ is None
    assert not hasattr(error, "__notes__")
    assert not _exact_container_contains(error.args, raw_mutation_ref)
    assert not _exact_container_contains(error.__dict__, raw_mutation_ref)
    traceback = error.__traceback__
    while traceback is not None:
        frame = traceback.tb_frame
        if "/src/ge_nwp_coordinator/" in frame.f_code.co_filename:
            assert not any(
                _exact_container_contains(value, raw_mutation_ref)
                for value in frame.f_locals.values()
            )
        traceback = traceback.tb_next
    fixture.author.writer.close()
