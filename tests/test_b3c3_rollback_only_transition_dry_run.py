from __future__ import annotations

import inspect
import os
from pathlib import Path
import re
import sqlite3
import threading
from typing import Any

import pytest

import ge_nwp_coordinator
from b3_coherent_transition_fixture import (
    FIXTURE_TIMESTAMP,
    _replace_work_item_lease_for_test,
    make_coherent_transition_fixture_for_test,
    transition_event_count_for_test,
)
from ge_nwp_coordinator.lease import AuthorizationDecision, AuthorizationModel
from ge_nwp_coordinator.persistence_contracts import AuthorizationReceiptEnvelope
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_transition_dry_run_contracts import (
    _RollbackOnlyTransitionDryRunResultKind,
    _TransitionDryRunPreflightError,
    _TransitionDryRunPreflightFailureReason,
)
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _TransitionReadCapabilityError,
    _TransitionReadCapabilityFailureReason,
)
import ge_nwp_coordinator.sqlite_transition_transaction as transaction_module
import ge_nwp_coordinator.sqlite_writer_session as writer_module
from ge_nwp_coordinator.state_machine import (
    TransitionCommand,
    TransitionEvaluation,
    TransitionEvaluationKind,
    WorkItemState,
)
from ge_nwp_coordinator.state_store import WriterSessionError, WriterSessionFailureReason
from test_b3c1b_rollback_only_writer_fencing import (
    _delete_writer_row,
    _replace_writer_row,
    _state_counts,
    _writer_rows,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
TRANSACTION_MODULE_PATH = PACKAGE_DIR / "sqlite_transition_transaction.py"


def _run_dry_run(fixture: object, command: TransitionCommand | None = None) -> object:
    selected = command if command is not None else fixture.command
    with fixture.writer_session._resource.operation_guard(fixture.writer_session) as operation:
        return transaction_module._run_rollback_only_transition_dry_run(
            operation_lease=operation,
            transition_command=selected,
        )


def _run_dry_run_raises(
    fixture: object,
    error_class: str,
    command: TransitionCommand | None = None,
) -> SQLiteMutationStoreError:
    selected = command if command is not None else fixture.command
    with fixture.writer_session._resource.operation_guard(fixture.writer_session) as operation:
        with pytest.raises(SQLiteMutationStoreError) as exc_info:
            transaction_module._run_rollback_only_transition_dry_run(
                operation_lease=operation,
                transition_command=selected,
            )
    _assert_mutation_error(exc_info.value, error_class)
    assert fixture.writer_session._resource._mutation_slot is None
    return exc_info.value


def _assert_mutation_error(error: SQLiteMutationStoreError, error_class: str) -> None:
    assert error.error_class == error_class
    assert str(error) == error_class
    assert error.args == (error_class,)
    assert error.internal_detail is None
    assert error.__cause__ is None
    assert error.__context__ is None
    assert error.error_class != "commit_outcome_unknown"


def _assert_conflict(result: object, conflict_class: str) -> None:
    assert result.kind is _RollbackOnlyTransitionDryRunResultKind.APPLY_CONFLICT
    assert result.conflict.conflict_class == conflict_class
    assert result.replayed_transition is None
    assert result.evaluation is None


def _assert_no_state_change(fixture: object, before: dict[str, int]) -> None:
    assert _state_counts(fixture.location) == before


def _reissue_command(command: TransitionCommand, **overrides: object) -> TransitionCommand:
    values: dict[str, object] = {
        "work_item_id": command.work_item_id,
        "idempotency_key": command.idempotency_key,
        "expected_version": command.expected_version,
        "target_state": command.target_state,
        "lease_identity_decision_ref": command.lease_identity_decision_ref,
        "authorization_decision_ref": command.authorization_decision_ref,
        "global_stop_ref": command.global_stop_ref,
        "global_stop_version": command.global_stop_version,
        "dependency_decision_ref": command.dependency_decision_ref,
        "evidence_refs": command.evidence_refs,
        "safe_failure_class": command.safe_failure_class,
        "budget_cost": command.budget_cost,
    }
    values.update(overrides)
    return TransitionCommand.create(**values)  # type: ignore[arg-type]


def _unchecked_command(command: TransitionCommand, **overrides: object) -> TransitionCommand:
    clone = object.__new__(TransitionCommand)
    clone.__dict__.update(command.__dict__)
    clone.__dict__.update(overrides)
    return clone


def _delete_all_rows(fixture: object, table_name: str) -> None:
    connection = sqlite3.connect(fixture.location.database_path)
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(f"DELETE FROM {table_name}")
        connection.commit()
    finally:
        connection.close()


def _set_operator_policy_authorization(fixture: object) -> TransitionCommand:
    decision = AuthorizationDecision(
        decision_ref=fixture.authorization.decision_ref,
        lease_ref=fixture.lease.lease_id,
        lease_identity_decision_ref=fixture.lease_identity_validation.decision_ref,
        lease_identity_valid=fixture.lease_identity_validation.identity_valid,
        authorization_model=AuthorizationModel.OPERATOR_POLICY,
        authorized=True,
        executable=False,
        reason="accepted",
    )
    return _reissue_command(fixture.command, authorization_decision_ref=decision.decision_ref)


def _patch_clock(monkeypatch: pytest.MonkeyPatch, timestamp: str = FIXTURE_TIMESTAMP) -> None:
    monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", lambda: timestamp)


def test_preflight_failures_happen_before_mutation_slot_sqlite_readers_timestamp_or_evaluator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        calls = {
            "mutation": 0,
            "open": 0,
            "reader": 0,
            "timestamp": 0,
            "evaluator": 0,
        }

        def mutation_factory(**kwargs: object) -> object:
            calls["mutation"] += 1
            return original_mutation_factory(**kwargs)

        def fail_open(*args: object, **kwargs: object) -> sqlite3.Connection:
            calls["open"] += 1
            raise AssertionError("preflight opened sqlite")

        def fail_reader(*args: object, **kwargs: object) -> object:
            calls["reader"] += 1
            raise AssertionError("preflight called reader")

        def fail_timestamp() -> str:
            calls["timestamp"] += 1
            raise AssertionError("preflight called timestamp")

        def fail_evaluator(*args: object, **kwargs: object) -> object:
            calls["evaluator"] += 1
            raise AssertionError("preflight called evaluator")

        original_mutation_factory = writer_module._MUTATION_LEASE_FACTORY
        monkeypatch.setattr(writer_module, "_MUTATION_LEASE_FACTORY", mutation_factory)
        monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_open)
        monkeypatch.setattr(transaction_module, "_read_transition_event_for_idempotency", fail_reader)
        monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", fail_timestamp)
        monkeypatch.setattr(transaction_module, "evaluate_transition", fail_evaluator)

        invalid_cases = (
            (
                object(),
                _TransitionDryRunPreflightFailureReason.INVALID_COMMAND,
            ),
            (
                _unchecked_command(fixture.command, canonical_command_digest="0" * 64),
                _TransitionDryRunPreflightFailureReason.INVALID_COMMAND,
            ),
            (
                _reissue_command(fixture.command, dependency_decision_ref="deps-non-ready"),
                _TransitionDryRunPreflightFailureReason.UNSUPPORTED_COMMAND,
            ),
            (
                _reissue_command(fixture.command, budget_cost=1),
                _TransitionDryRunPreflightFailureReason.UNSUPPORTED_COMMAND,
            ),
        )

        for command, reason in invalid_cases:
            with fixture.writer_session._resource.operation_guard(fixture.writer_session) as operation:
                with pytest.raises(_TransitionDryRunPreflightError) as exc_info:
                    transaction_module._run_rollback_only_transition_dry_run(
                        operation_lease=operation,
                        transition_command=command,  # type: ignore[arg-type]
                    )
                assert exc_info.value.reason is reason
                mutation = operation._acquire_mutation_lease()
                operation._require_active_mutation_authority()
                mutation._close()

        assert calls == {"mutation": 4, "open": 0, "reader": 0, "timestamp": 0, "evaluator": 0}


def test_wrong_operation_lease_type_fails_before_preflight(monkeypatch: pytest.MonkeyPatch) -> None:
    preflight_calls = 0

    def fail_preflight(command: object) -> object:
        nonlocal preflight_calls
        preflight_calls += 1
        raise AssertionError("wrong lease reached preflight")

    monkeypatch.setattr(transaction_module, "_validate_transition_dry_run_preflight", fail_preflight)
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        transaction_module._run_rollback_only_transition_dry_run(
            operation_lease=object(),  # type: ignore[arg-type]
            transition_command=object(),  # type: ignore[arg-type]
        )
    _assert_mutation_error(exc_info.value, "mutation_failed")
    assert preflight_calls == 0


def test_stale_writer_returns_conflict_before_idempotency_disclosure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, existing_event=True) as fixture:
        _replace_writer_row(fixture.location, issuance_nonce_digest="0" * 64)
        calls = {"idempotency": 0, "timestamp": 0, "evaluator": 0}
        before = _state_counts(fixture.location)

        def fail_idempotency(*args: object, **kwargs: object) -> object:
            calls["idempotency"] += 1
            raise AssertionError("stale writer disclosed idempotency")

        monkeypatch.setattr(transaction_module, "_read_transition_event_for_idempotency", fail_idempotency)
        monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", lambda: calls.__setitem__("timestamp", 1))
        monkeypatch.setattr(transaction_module, "evaluate_transition", lambda *args: calls.__setitem__("evaluator", 1))

        result = _run_dry_run(fixture)

        _assert_conflict(result, "stale_writer_token")
        assert calls == {"idempotency": 0, "timestamp": 0, "evaluator": 0}
        _assert_no_state_change(fixture, before)


def test_missing_or_malformed_writer_row_preserves_fencing_integrity_taxonomy(tmp_path: Path) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path / "missing") as fixture:
        _delete_writer_row(fixture.location)
        _run_dry_run_raises(fixture, "database_integrity_failure")

    with make_coherent_transition_fixture_for_test(tmp_path / "malformed") as fixture:
        _replace_writer_row(fixture.location, generation=0)
        _run_dry_run_raises(fixture, "database_integrity_failure")


def test_exact_replay_returns_committed_replay_after_cleanup_and_skips_context_clock_evaluator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, existing_event=True) as fixture:
        before = _state_counts(fixture.location)
        calls: list[str] = []

        def fail_if_called(name: str) -> object:
            def inner(*args: object, **kwargs: object) -> object:
                calls.append(name)
                raise AssertionError(f"replay called {name}")

            return inner

        for name in (
            "_read_current_work_item",
            "_read_lease_identity_record",
            "_read_admitted_backlog",
            "_read_authorization_receipt",
            "_read_dependency_receipt",
            "_read_global_stop_current",
        ):
            monkeypatch.setattr(transaction_module, name, fail_if_called(name))
        monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", fail_if_called("clock"))
        monkeypatch.setattr(transaction_module, "evaluate_transition", fail_if_called("evaluator"))

        result = _run_dry_run(fixture)

        assert result.kind is _RollbackOnlyTransitionDryRunResultKind.EXACT_REPLAY
        assert result.replayed_transition.replayed is True
        assert result.conflict is None
        assert result.evaluation is None
        assert calls == []
        _assert_no_state_change(fixture, before)


def test_idempotency_key_reuse_conflict_skips_context_clock_evaluator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, existing_event=True) as fixture:
        before = _state_counts(fixture.location)
        conflict_command = _reissue_command(
            fixture.command,
            target_state=WorkItemState.BLOCKED,
            safe_failure_class="operator_action_required",
        )
        calls: list[str] = []
        monkeypatch.setattr(
            transaction_module,
            "_read_current_work_item",
            lambda *args, **kwargs: calls.append("current"),
        )
        monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", lambda: calls.append("clock"))
        monkeypatch.setattr(transaction_module, "evaluate_transition", lambda *args: calls.append("evaluator"))

        result = _run_dry_run(fixture, conflict_command)

        _assert_conflict(result, "idempotency_key_reuse_conflict")
        assert calls == []
        _assert_no_state_change(fixture, before)


def test_malformed_idempotency_event_row_is_integrity_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, existing_event=True) as fixture:
        monkeypatch.setattr(
            transaction_module,
            "_read_transition_event_for_idempotency",
            lambda *args, **kwargs: transaction_module._database_integrity_failure(),
        )
        _run_dry_run_raises(fixture, "database_integrity_failure")


def test_current_work_item_missing_and_expected_version_conflicts_skip_context_and_clock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name, command_factory, expected in (
        ("missing", lambda fixture: fixture.command, "work_item_not_found"),
        ("lower", lambda fixture: _reissue_command(fixture.command, expected_version=0), "expected_version_conflict"),
        ("higher", lambda fixture: _reissue_command(fixture.command, expected_version=2), "expected_version_conflict"),
    ):
        with make_coherent_transition_fixture_for_test(tmp_path / name, ready_dependency=True) as fixture:
            if name == "missing":
                _delete_all_rows(fixture, "work_items")
            calls: list[str] = []
            monkeypatch.setattr(
                transaction_module,
                "_read_lease_identity_record",
                lambda *args, **kwargs: calls.append("lease"),
            )
            monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", lambda: calls.append("clock"))
            monkeypatch.setattr(transaction_module, "evaluate_transition", lambda *args: calls.append("evaluator"))

            result = _run_dry_run(fixture, command_factory(fixture))

            _assert_conflict(result, expected)
            assert calls == []


def test_context_readers_are_called_in_pinned_order_and_non_ready_skips_dependency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path / "ready", ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        calls: list[str] = []
        originals = {
            "idempotency": transaction_module._read_transition_event_for_idempotency,
            "current": transaction_module._read_current_work_item,
            "lease": transaction_module._read_lease_identity_record,
            "backlog": transaction_module._read_admitted_backlog,
            "authorization": transaction_module._read_authorization_receipt,
            "dependency": transaction_module._read_dependency_receipt,
            "global": transaction_module._read_global_stop_current,
        }

        for label, original in originals.items():
            def wrapper(*args: object, _label: str = label, _original: object = original, **kwargs: object) -> object:
                calls.append(_label)
                return _original(*args, **kwargs)

            monkeypatch.setattr(transaction_module, f"_read_{'transition_event_for_idempotency' if label == 'idempotency' else label}", wrapper, raising=False)

        monkeypatch.setattr(transaction_module, "_read_current_work_item", lambda *args, **kwargs: (calls.append("current"), originals["current"](*args, **kwargs))[1])
        monkeypatch.setattr(transaction_module, "_read_lease_identity_record", lambda *args, **kwargs: (calls.append("lease"), originals["lease"](*args, **kwargs))[1])
        monkeypatch.setattr(transaction_module, "_read_admitted_backlog", lambda *args, **kwargs: (calls.append("backlog"), originals["backlog"](*args, **kwargs))[1])
        monkeypatch.setattr(transaction_module, "_read_authorization_receipt", lambda *args, **kwargs: (calls.append("authorization"), originals["authorization"](*args, **kwargs))[1])
        monkeypatch.setattr(transaction_module, "_read_dependency_receipt", lambda *args, **kwargs: (calls.append("dependency"), originals["dependency"](*args, **kwargs))[1])
        monkeypatch.setattr(transaction_module, "_read_global_stop_current", lambda *args, **kwargs: (calls.append("global"), originals["global"](*args, **kwargs))[1])
        monkeypatch.setattr(transaction_module, "_read_transition_event_for_idempotency", lambda *args, **kwargs: (calls.append("idempotency"), originals["idempotency"](*args, **kwargs))[1])

        result = _run_dry_run(fixture)

        assert result.kind is _RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED
        assert calls == ["idempotency", "current", "lease", "backlog", "authorization", "dependency", "global"]

    with make_coherent_transition_fixture_for_test(tmp_path / "non-ready") as fixture:
        _patch_clock(monkeypatch)
        dependency_calls = 0

        def fail_dependency(*args: object, **kwargs: object) -> object:
            nonlocal dependency_calls
            dependency_calls += 1
            raise AssertionError("non-ready read dependency")

        monkeypatch.setattr(transaction_module, "_read_dependency_receipt", fail_dependency)
        result = _run_dry_run(fixture)
        assert result.kind is _RollbackOnlyTransitionDryRunResultKind.DOMAIN_REJECTED_EVALUATION_NOT_PERSISTED
        assert dependency_calls == 0


@pytest.mark.parametrize(
    ("table_name", "ready_dependency", "error_class", "conflict_class"),
    (
        ("lease_identity_records", False, None, "validation_failed"),
        ("authorization_decision_receipts", False, None, "validation_failed"),
        ("dependency_decision_receipts", True, None, "validation_failed"),
        ("admitted_backlogs", False, "database_integrity_failure", None),
        ("global_stop_current", False, "database_integrity_failure", None),
    ),
)
def test_missing_context_row_classifications(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    table_name: str,
    ready_dependency: bool,
    error_class: str | None,
    conflict_class: str | None,
) -> None:
    with make_coherent_transition_fixture_for_test(
        tmp_path / table_name,
        ready_dependency=ready_dependency,
    ) as fixture:
        if table_name == "lease_identity_records":
            monkeypatch.setattr(transaction_module, "_read_lease_identity_record", lambda *args, **kwargs: None)
        elif table_name == "authorization_decision_receipts":
            monkeypatch.setattr(transaction_module, "_read_authorization_receipt", lambda *args, **kwargs: None)
        elif table_name == "dependency_decision_receipts":
            monkeypatch.setattr(transaction_module, "_read_dependency_receipt", lambda *args, **kwargs: None)
        elif table_name == "admitted_backlogs":
            monkeypatch.setattr(transaction_module, "_read_admitted_backlog", lambda *args, **kwargs: None)
        elif table_name == "global_stop_current":
            monkeypatch.setattr(
                transaction_module,
                "_read_global_stop_current",
                lambda *args, **kwargs: (_ for _ in ()).throw(transaction_module._database_integrity_failure()),
            )
        if error_class is not None:
            _run_dry_run_raises(fixture, error_class)
        else:
            result = _run_dry_run(fixture)
            _assert_conflict(result, conflict_class)


def test_authority_binding_runtime_taxonomy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path / "valid", ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        result = _run_dry_run(fixture)
        assert result.kind is _RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED

    with make_coherent_transition_fixture_for_test(tmp_path / "persisted-contradiction") as fixture:
        _replace_work_item_lease_for_test(fixture)
        _run_dry_run_raises(fixture, "database_integrity_failure")

    with make_coherent_transition_fixture_for_test(tmp_path / "global-stop-mismatch") as fixture:
        mismatch = _reissue_command(fixture.command, global_stop_ref="operator-global-stop")
        result = _run_dry_run(fixture, mismatch)
        _assert_conflict(result, "validation_failed")

    with make_coherent_transition_fixture_for_test(tmp_path / "operator-policy") as fixture:
        command = _set_operator_policy_authorization(fixture)
        operator_decision = AuthorizationDecision(
            decision_ref=fixture.authorization.decision_ref,
            lease_ref=fixture.lease.lease_id,
            lease_identity_decision_ref=fixture.lease_identity_validation.decision_ref,
            lease_identity_valid=fixture.lease_identity_validation.identity_valid,
            authorization_model=AuthorizationModel.OPERATOR_POLICY,
            authorized=True,
            executable=False,
            reason="accepted",
        )
        with monkeypatch.context() as policy_patch:
            policy_patch.setattr(
                transaction_module,
                "_read_authorization_receipt",
                lambda *args, **kwargs: AuthorizationReceiptEnvelope(decision=operator_decision, created_at=FIXTURE_TIMESTAMP),
            )
            result = _run_dry_run(fixture, command)
        _assert_conflict(result, "validation_failed")

    with make_coherent_transition_fixture_for_test(tmp_path / "false-ready", ready_dependency=True, dependencies_satisfied=False) as fixture:
        _patch_clock(monkeypatch)
        result = _run_dry_run(fixture)
        assert result.kind is _RollbackOnlyTransitionDryRunResultKind.DOMAIN_REJECTED_EVALUATION_NOT_PERSISTED
        assert result.evaluation.reason == "dependencies_not_satisfied"


def test_timestamp_runtime_context_and_evaluator_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path / "accepted", ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        calls = {"clock": 0, "runtime": 0, "context": 0, "evaluator": 0}
        original_runtime = transaction_module.derive_lease_runtime_decision
        original_context = transaction_module.TransitionContext
        original_evaluate = transaction_module.evaluate_transition

        def clock() -> str:
            calls["clock"] += 1
            return "2026-07-14T00:00:04Z"

        def runtime(*args: object, **kwargs: object) -> object:
            calls["runtime"] += 1
            return original_runtime(*args, **kwargs)

        def context(*args: object, **kwargs: object) -> object:
            calls["context"] += 1
            return original_context(*args, **kwargs)

        def evaluate(*args: object, **kwargs: object) -> object:
            calls["evaluator"] += 1
            return original_evaluate(*args, **kwargs)

        monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", clock)
        monkeypatch.setattr(transaction_module, "derive_lease_runtime_decision", runtime)
        monkeypatch.setattr(transaction_module, "TransitionContext", context)
        monkeypatch.setattr(transaction_module, "evaluate_transition", evaluate)

        result = _run_dry_run(fixture)

        assert result.kind is _RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED
        assert result.evaluation.event.lease_runtime.evaluated_at == "2026-07-14T00:00:04Z"
        assert calls == {"clock": 1, "runtime": 1, "context": 1, "evaluator": 1}

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", transaction_module._utc_transaction_timestamp())


def test_clock_failure_and_evaluator_failures_are_safely_classified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path / "clock", ready_dependency=True) as fixture:
        monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", lambda: (_ for _ in ()).throw(RuntimeError("private-clock")))
        _run_dry_run_raises(fixture, "mutation_failed")

    with make_coherent_transition_fixture_for_test(tmp_path / "pre-apply", ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)

        def pre_apply(record: object, command: object, context: object) -> TransitionEvaluation:
            return TransitionEvaluation(
                kind=TransitionEvaluationKind.PRE_APPLY_INVALID,
                reason="work_item_id_mismatch",
                record=record,
                event=None,
            )

        monkeypatch.setattr(transaction_module, "evaluate_transition", pre_apply)
        _run_dry_run_raises(fixture, "database_integrity_failure")

    with make_coherent_transition_fixture_for_test(tmp_path / "ordinary", ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        monkeypatch.setattr(transaction_module, "evaluate_transition", lambda *args: (_ for _ in ()).throw(RuntimeError("private-eval")))
        _run_dry_run_raises(fixture, "mutation_failed")


def test_real_evaluator_domain_rejected_and_accepted_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path / "unsupported-auth") as fixture:
        _patch_clock(monkeypatch)
        result = _run_dry_run(fixture)
        assert result.kind is _RollbackOnlyTransitionDryRunResultKind.DOMAIN_REJECTED_EVALUATION_NOT_PERSISTED
        assert result.evaluation.reason == "lease_not_authorized"

    with make_coherent_transition_fixture_for_test(
        tmp_path / "false-dependency",
        ready_dependency=True,
        dependencies_satisfied=False,
    ) as fixture:
        _patch_clock(monkeypatch)
        result = _run_dry_run(fixture)
        assert result.kind is _RollbackOnlyTransitionDryRunResultKind.DOMAIN_REJECTED_EVALUATION_NOT_PERSISTED
        assert result.evaluation.reason == "dependencies_not_satisfied"

    with make_coherent_transition_fixture_for_test(
        tmp_path / "accepted",
        ready_dependency=True,
        dependencies_satisfied=True,
    ) as fixture:
        _patch_clock(monkeypatch)
        result = _run_dry_run(fixture)
        assert result.kind is _RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED
        assert result.evaluation.reason == "transition_accepted"
        assert transition_event_count_for_test(fixture) == 0


def test_lease_runtime_boundaries_are_source_backed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cases = (
        ("2026-07-14T00:00:00Z", "lease_not_yet_valid"),
        ("2026-07-14T00:00:01Z", "transition_accepted"),
        ("2026-07-15T00:00:00Z", "lease_expired"),
    )
    for timestamp, expected_reason in cases:
        with make_coherent_transition_fixture_for_test(
            tmp_path / expected_reason,
            ready_dependency=True,
            dependencies_satisfied=True,
        ) as fixture:
            _patch_clock(monkeypatch, timestamp)
            result = _run_dry_run(fixture)
            assert result.evaluation.reason == expected_reason


def test_result_cleanup_precedence_slot_release_and_capability_expiration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path / "order", ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        with monkeypatch.context() as lifecycle_patch:
            events: list[str] = []
            captured: list[object] = []
            original_create = transaction_module._create_sqlite_transition_read_capability
            original_invalidate = transaction_module._invalidate_sqlite_transition_read_capability
            original_rollback = transaction_module._rollback_transaction
            original_close = transaction_module._close_connection

            def create(**kwargs: object) -> object:
                capability = original_create(**kwargs)
                captured.append(capability)
                events.append("capability-created")
                return capability

            def invalidate(*args: object, **kwargs: object) -> object:
                events.append("invalidate")
                return original_invalidate(*args, **kwargs)

            def rollback(connection: sqlite3.Connection) -> object:
                events.append("rollback")
                return original_rollback(connection)

            def close(connection: sqlite3.Connection) -> object:
                events.append("close")
                return original_close(connection)

            lifecycle_patch.setattr(transaction_module, "_create_sqlite_transition_read_capability", create)
            lifecycle_patch.setattr(transaction_module, "_invalidate_sqlite_transition_read_capability", invalidate)
            lifecycle_patch.setattr(transaction_module, "_rollback_transaction", rollback)
            lifecycle_patch.setattr(transaction_module, "_close_connection", close)

            result = _run_dry_run(fixture)
            events.append("returned")

            assert result.kind is _RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED
            assert events == ["capability-created", "invalidate", "rollback", "close", "returned"]
            assert fixture.writer_session._resource._mutation_slot is None

    with make_coherent_transition_fixture_for_test(tmp_path / "expired", ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        captured = []
        original_create = transaction_module._create_sqlite_transition_read_capability

        def capture_create(**kwargs: object) -> object:
            capability = original_create(**kwargs)
            captured.append(capability)
            return capability

        monkeypatch.setattr(transaction_module, "_create_sqlite_transition_read_capability", capture_create)
        _run_dry_run(fixture)
        with pytest.raises(_TransitionReadCapabilityError) as exc_info:
            captured[0]._borrow_connection_for_select()
        assert exc_info.value.reason is _TransitionReadCapabilityFailureReason.CAPABILITY_EXPIRED


def test_rollback_and_close_failures_supersede_planned_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path / "rollback", ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        monkeypatch.setattr(transaction_module, "_rollback_transaction", lambda connection: transaction_module._mutation_failed())
        _run_dry_run_raises(fixture, "mutation_failed")

    with make_coherent_transition_fixture_for_test(tmp_path / "close", ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        monkeypatch.setattr(transaction_module, "_close_connection", lambda connection: transaction_module._mutation_failed())
        _run_dry_run_raises(fixture, "mutation_failed")


def test_capability_wrong_thread_and_fork_fail_closed_after_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        captured: list[object] = []
        original_create = transaction_module._create_sqlite_transition_read_capability

        def create(**kwargs: object) -> object:
            capability = original_create(**kwargs)
            captured.append(capability)
            return capability

        monkeypatch.setattr(transaction_module, "_create_sqlite_transition_read_capability", create)
        _run_dry_run(fixture)
        capability = captured[0]

        thread_results: list[str] = []

        def borrow_in_thread() -> None:
            try:
                capability._borrow_connection_for_select()
            except _TransitionReadCapabilityError as exc:
                thread_results.append(exc.reason.value)

        thread = threading.Thread(target=borrow_in_thread)
        thread.start()
        thread.join(5)
        assert not thread.is_alive()
        assert thread_results == [_TransitionReadCapabilityFailureReason.PROCESS_MISMATCH.value] or thread_results == [
            _TransitionReadCapabilityFailureReason.THREAD_MISMATCH.value
        ]

        if not hasattr(os, "fork"):
            return
        read_fd, write_fd = os.pipe()
        child = os.fork()
        if child == 0:
            os.close(read_fd)
            try:
                try:
                    capability._borrow_connection_for_select()
                except _TransitionReadCapabilityError as exc:
                    os.write(write_fd, exc.reason.value.encode("ascii"))
                else:
                    os.write(write_fd, b"unexpected")
            finally:
                os.close(write_fd)
                os._exit(0)
        os.close(write_fd)
        try:
            result = os.read(read_fd, 256).decode("ascii")
        finally:
            os.close(read_fd)
            os.waitpid(child, 0)
        assert result == _TransitionReadCapabilityFailureReason.PROCESS_MISMATCH.value


def test_dry_run_does_not_mutate_tables_read_sequence_or_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        before_counts = _state_counts(fixture.location)
        before_writer = _writer_rows(fixture.location)
        traced_sql: list[str] = []
        original_open = transaction_module._open_bound_existing_sqlite_connection

        def tracing_open(*args: object, **kwargs: object) -> sqlite3.Connection:
            connection = original_open(*args, **kwargs)
            connection.set_trace_callback(traced_sql.append)
            return connection

        monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", tracing_open)
        result = _run_dry_run(fixture)

        assert result.kind is _RollbackOnlyTransitionDryRunResultKind.ACCEPTED_EVALUATION_NOT_PERSISTED
        assert _state_counts(fixture.location) == before_counts
        assert _writer_rows(fixture.location) == before_writer
        normalized = "\n".join(statement.upper() for statement in traced_sql)
        assert "MAX(EVENT_SEQUENCE)" not in normalized
        assert "NEXT_TRANSITION_EVENT_SEQUENCE" not in normalized
        assert "COMMIT" not in normalized
        for forbidden in ("INSERT ", "UPDATE ", "DELETE ", "REPLACE "):
            assert forbidden not in normalized


def test_public_non_integration_boundaries_remain_closed() -> None:
    package_source = (PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8")
    writer_source = (PACKAGE_DIR / "sqlite_writer_session.py").read_text(encoding="utf-8")
    state_store_source = (PACKAGE_DIR / "state_store.py").read_text(encoding="utf-8")

    assert "_run_rollback_only_transition_dry_run" not in package_source
    assert "_RollbackOnlyTransitionDryRunResult" not in ge_nwp_coordinator.__all__
    assert not hasattr(ge_nwp_coordinator, "_run_rollback_only_transition_dry_run")
    assert "_run_rollback_only_transition_dry_run" not in writer_source
    assert "WRITER_SESSION_MUTATION_UNAVAILABLE" in writer_source
    assert "_run_rollback_only_transition_dry_run" not in state_store_source


def test_static_b3c3_runtime_gates() -> None:
    source = TRANSACTION_MODULE_PATH.read_text(encoding="utf-8")
    dry_run_source = (
        inspect.getsource(transaction_module._TransitionTransactionController._run_transition_dry_run_transaction)
        + inspect.getsource(transaction_module._TransitionTransactionController._run_until_transition_resolution)
        + inspect.getsource(transaction_module._evaluate_bound_transition)
    )

    assert "_read_transition_event_for_idempotency" in source
    assert "match_transition_event_idempotency" in source
    assert "_read_transition_event_max_sequence" not in dry_run_source
    assert "next_transition_event_sequence" not in dry_run_source
    assert "MAX(event_sequence)" not in dry_run_source
    assert "_run_rollback_only_writer_fencing" in source
    assert "_run_rollback_only_transition_dry_run" in source
    assert "_run_atomic_transition_apply" in source
    assert source.count("class _TransitionTransactionController") == 1
    assert "_RollbackOnlyTransitionTransactionController" not in source
    assert source.count("def _create_sqlite_transition_read_capability") == 1
    for forbidden in (
        "Callable",
        "callback",
        "observer",
        "for_test",
        "controller_for_test",
        "raw_connection",
        "commit_outcome_unknown",
        "INSERT INTO transition_events",
        "UPDATE work_items",
        "UPDATE global_stop_current",
        "connection.commit",
        ".commit(",
        "COMMIT",
    ):
        assert forbidden not in dry_run_source
    order = [
        dry_run_source.index("_read_transition_event_for_idempotency"),
        dry_run_source.index("match_transition_event_idempotency"),
        dry_run_source.index("_read_current_work_item"),
        dry_run_source.index("_read_lease_identity_record"),
        dry_run_source.index("_read_admitted_backlog"),
        dry_run_source.index("_read_authorization_receipt"),
        dry_run_source.index("_read_dependency_receipt"),
        dry_run_source.index("_read_global_stop_current"),
        dry_run_source.index("_bind_b3c3_transition_authority"),
        dry_run_source.index("_capture_transaction_timestamp"),
        dry_run_source.index("_evaluate_bound_transition"),
    ]
    assert order == sorted(order)
