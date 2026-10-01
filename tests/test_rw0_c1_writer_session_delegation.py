from __future__ import annotations

import ast
from pathlib import Path

import pytest

import ge_nwp_coordinator
import ge_nwp_coordinator.sqlite_transition_transaction as transaction
import ge_nwp_coordinator.sqlite_writer_session as writer_module
from ge_nwp_coordinator._rw0_c1_mutation_contracts import (
    _RW0C1CommitCloseWitness,
    _RW0C1RecoveryCloseWitness,
)
from ge_nwp_coordinator._rw0_c1_semantic_values import (
    RW0C1RecoveryDispositionV1,
    RW0C1RecoveryResultV1,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from test_rw0_c1_private_atomic_persistence import make_c1_harness


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_METHODS = {
    "_establish_rw0_phase",
    "_resolve_rw0_c1_phase_establishment_commit_outcome",
    "_admit_rw0_evidence",
    "_resolve_rw0_c1_evidence_admission_commit_outcome",
}
METHOD_SUFFIX = {
    name: f"delegation-{index}"
    for index, name in enumerate(sorted(PRIVATE_METHODS), start=1)
}


@pytest.mark.parametrize(
    ("session_method", "delegate_name", "payload_keyword", "witness_keyword"),
    (
        (
            "_establish_rw0_phase",
            "_run_atomic_rw0_c1_phase_establishment",
            "command",
            "commit_close_witness",
        ),
        (
            "_resolve_rw0_c1_phase_establishment_commit_outcome",
            "_run_rw0_c1_phase_establishment_recovery",
            "probe",
            "recovery_close_witness",
        ),
        (
            "_admit_rw0_evidence",
            "_run_atomic_rw0_c1_evidence_admission",
            "command",
            "commit_close_witness",
        ),
        (
            "_resolve_rw0_c1_evidence_admission_commit_outcome",
            "_run_rw0_c1_evidence_admission_recovery",
            "selector",
            "recovery_close_witness",
        ),
    ),
    ids=(
        "_establish_rw0_phase-_run_atomic_rw0_c1_phase_establishment-command",
        "_resolve_rw0_c1_phase_establishment_commit_outcome-"
        "_run_rw0_c1_phase_establishment_recovery-probe",
        "_admit_rw0_evidence-_run_atomic_rw0_c1_evidence_admission-command",
        "_resolve_rw0_c1_evidence_admission_commit_outcome-"
        "_run_rw0_c1_evidence_admission_recovery-probe",
    ),
)
def test_private_concrete_methods_delegate_once_with_exact_lease_and_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    session_method: str,
    delegate_name: str,
    payload_keyword: str,
    witness_keyword: str,
) -> None:
    harness = make_c1_harness(tmp_path, suffix=METHOD_SUFFIX[session_method])
    resource = harness.writer._resource
    payload = object()
    sentinel = object()
    calls: list[tuple[object, object]] = []

    def delegate(**kwargs: object) -> object:
        assert tuple(kwargs) == (
            "operation_lease",
            payload_keyword,
            witness_keyword,
        )
        calls.append((kwargs["operation_lease"], kwargs[payload_keyword]))
        assert len(resource._active_operations) == 1
        witness = kwargs[witness_keyword]
        if witness_keyword == "commit_close_witness":
            assert type(witness) is _RW0C1CommitCloseWitness
        else:
            assert type(witness) is _RW0C1RecoveryCloseWitness
            recovered = RW0C1RecoveryResultV1(
                "establish_rw0_phase",
                "mutation.rw0-c1.delegation",
                "d" * 64,
                RW0C1RecoveryDispositionV1.UNRESOLVED,
            )
            witness._claim_controller()
            witness._mark_result_computed(recovered)
            return recovered
        return sentinel

    monkeypatch.setattr(transaction, delegate_name, delegate)
    try:
        result = getattr(harness.writer, session_method)(payload)
        if witness_keyword == "commit_close_witness":
            assert result is sentinel
        else:
            assert type(result) is RW0C1RecoveryResultV1
            assert result.disposition is RW0C1RecoveryDispositionV1.UNRESOLVED
        assert len(calls) == 1
        assert calls[0][1] is payload
        assert len(resource._active_operations) == 0
        assert resource._mutation_slot is None
    finally:
        harness.close()


@pytest.mark.parametrize("session_method", tuple(sorted(PRIVATE_METHODS)))
def test_invalid_private_payloads_return_only_content_free_store_errors(
    tmp_path: Path,
    session_method: str,
) -> None:
    harness = make_c1_harness(
        tmp_path,
        suffix="invalid-" + METHOD_SUFFIX[session_method],
    )
    try:
        with pytest.raises(SQLiteMutationStoreError) as caught:
            getattr(harness.writer, session_method)(object())
        error = caught.value
        assert type(error) is SQLiteMutationStoreError
        assert error.error_class == "mutation_failed"
        assert error.args == ("mutation_failed",)
        assert error.internal_detail is None
        assert error.__cause__ is None
        assert error.__context__ is None
        assert not getattr(error, "__notes__", ())
        assert len(harness.writer._resource._active_operations) == 0
        assert harness.writer._resource._mutation_slot is None
    finally:
        harness.close()


def test_process_control_interrupt_stabilizes_and_releases_operation_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = make_c1_harness(tmp_path, suffix="process-control")
    resource = harness.writer._resource
    calls: list[object] = []
    original = writer_module._WriterSessionResource._stabilize_operation_exit_for_process_control

    def counted(self: object, correlation: object) -> None:
        calls.append(correlation)
        original(self, correlation)

    def interrupted(**_kwargs: object) -> object:
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        writer_module._WriterSessionResource,
        "_stabilize_operation_exit_for_process_control",
        counted,
    )
    monkeypatch.setattr(
        transaction,
        "_run_atomic_rw0_c1_phase_establishment",
        interrupted,
    )
    try:
        with pytest.raises(KeyboardInterrupt):
            harness.writer._establish_rw0_phase(object())
        assert len(calls) == 1
        assert calls[0] is not None
        assert len(resource._active_operations) == 0
        assert resource._mutation_slot is None
        assert harness.writer.active is False
    finally:
        harness.close()


def test_c1_delegation_is_private_to_concrete_session_and_uses_one_controller() -> None:
    writer_path = ROOT / "src/ge_nwp_coordinator/sqlite_writer_session.py"
    transaction_path = ROOT / "src/ge_nwp_coordinator/sqlite_transition_transaction.py"
    runtime_path = ROOT / "src/ge_nwp_coordinator/_sqlite_rw0_c1.py"
    state_store_path = ROOT / "src/ge_nwp_coordinator/state_store.py"
    package_path = ROOT / "src/ge_nwp_coordinator/__init__.py"

    writer_tree = ast.parse(writer_path.read_text(encoding="utf-8"))
    concrete = next(
        node
        for node in writer_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "_SQLiteWriterSession"
    )
    concrete_methods = {
        node.name for node in concrete.body if isinstance(node, ast.FunctionDef)
    }
    assert PRIVATE_METHODS <= concrete_methods
    assert "_run_rw0_c1_operation" in concrete_methods

    protected_text = (
        state_store_path.read_text(encoding="utf-8")
        + package_path.read_text(encoding="utf-8")
    )
    assert all(name not in protected_text for name in PRIVATE_METHODS)
    assert all(not hasattr(ge_nwp_coordinator, name) for name in PRIVATE_METHODS)

    transaction_source = transaction_path.read_text(encoding="utf-8")
    runtime_source = runtime_path.read_text(encoding="utf-8")
    assert transaction_source.count(
        "class _CoordinatorMutationTransactionController:"
    ) == 1
    assert "class _CoordinatorMutationTransactionController:" not in runtime_source
    assert "sqlite3" not in runtime_source
