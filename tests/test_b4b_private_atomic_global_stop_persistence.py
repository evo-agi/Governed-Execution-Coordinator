from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
import sqlite3
import threading
import traceback

import pytest

import ge_nwp_coordinator
from b3_coherent_transition_fixture import (
    global_stop_event_count_for_test,
    make_coherent_transition_fixture_for_test,
    read_back_fixture_for_test,
    transition_event_count_for_test,
)
from ge_nwp_coordinator.global_stop import (
    GlobalStopAction,
    GlobalStopCommand,
    GlobalStopEvaluation,
    GlobalStopEvaluationKind,
    GlobalStopEventOutcome,
    GlobalStopOperatorDecision,
    GlobalStopReasonClass,
    GlobalStopState,
)
from ge_nwp_coordinator.persistence_contracts import (
    GLOBAL_STOP_EVENT_ROW_COLUMNS,
    GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_ROW_COLUMNS,
    SQLITE_SIGNED_INT_MAX,
    GlobalStopEventRecordEnvelope,
    encode_sqlite_boolean,
    global_stop_event_record_envelope_from_row,
    global_stop_operator_decision_canonical_digest,
    global_stop_operator_decision_canonical_json,
)
from ge_nwp_coordinator.sqlite_connection import open_existing_sqlite_connection
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
import ge_nwp_coordinator.sqlite_mutation_transaction_contracts as mutation_contracts
import ge_nwp_coordinator.sqlite_transition_transaction as transaction_module
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.state_store import (
    CommittedGlobalStopUpdate,
    GlobalStopConflict,
    WriterSessionError,
    WriterSessionFailureReason,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
TRANSACTION_MODULE_PATH = PACKAGE_DIR / "sqlite_transition_transaction.py"
WRITER_SESSION_PATH = PACKAGE_DIR / "sqlite_writer_session.py"
PACKAGE_EXPORT_PATH = PACKAGE_DIR / "__init__.py"
MIGRATION_DIR = PACKAGE_DIR / "sqlite_migrations"
B4B_TIMESTAMP = "2026-07-22T12:00:04Z"
PRIVATE_SENTINEL = "b4b-private-sentinel-do-not-leak"


def _decision(
    *,
    ref: str = "operator-decision-b4b-1",
    authorized: bool = True,
) -> GlobalStopOperatorDecision:
    return GlobalStopOperatorDecision(
        decision_ref=ref,
        authorized=authorized,
        reason="accepted" if authorized else "operator_authorization_required",
    )


def _command(
    *,
    action: GlobalStopAction = GlobalStopAction.ACTIVATE,
    key: str = "global-stop-b4b-key-1",
    expected_version: int = 0,
    decision_ref: str = "operator-decision-b4b-1",
    source_stop_id: str | None = None,
    stop_id: str = "global-stop-b4b-1",
    reason_class: GlobalStopReasonClass = GlobalStopReasonClass.OPERATOR_STOP,
    issuer_ref: str = "operator-policy",
    issued_at: str = "2026-07-22T12:00:00Z",
) -> GlobalStopCommand:
    return GlobalStopCommand.create(
        action=action,
        idempotency_key=key,
        expected_version=expected_version,
        source_stop_id=source_stop_id,
        stop_id=stop_id,
        reason_class=reason_class,
        issuer_ref=issuer_ref,
        issued_at=issued_at,
        operator_decision_ref=decision_ref,
    )


def _run_global_stop_apply(
    fixture: object,
    command: GlobalStopCommand,
    decision: GlobalStopOperatorDecision,
) -> object:
    with fixture.writer_session._resource.operation_guard(fixture.writer_session) as operation:
        return transaction_module._run_atomic_global_stop_apply(
            operation_lease=operation,
            global_stop_command=command,
            typed_operator_decision=decision,
        )


def _run_global_stop_apply_raises(
    fixture: object,
    command: GlobalStopCommand,
    decision: GlobalStopOperatorDecision,
    error_class: str,
) -> SQLiteMutationStoreError:
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        _run_global_stop_apply(fixture, command, decision)
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
    assert not getattr(error, "__notes__", ())
    formatted = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    assert PRIVATE_SENTINEL not in formatted


def _assert_committed(result: object, *, replayed: bool) -> CommittedGlobalStopUpdate:
    assert type(result) is CommittedGlobalStopUpdate
    assert result.replayed is replayed
    return result


def _assert_conflict(result: object, conflict_class: str) -> GlobalStopConflict:
    assert type(result) is GlobalStopConflict
    assert result.conflict_class == conflict_class
    return result


def _patch_clock(monkeypatch: pytest.MonkeyPatch, timestamp: str = B4B_TIMESTAMP) -> None:
    monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", lambda: timestamp)


def _receipt_row(decision: GlobalStopOperatorDecision, *, created_at: str = B4B_TIMESTAMP) -> dict[str, object]:
    return {
        "decision_ref": decision.decision_ref,
        "authorized": encode_sqlite_boolean(decision.authorized, "receipt.authorized"),
        "reason": decision.reason,
        "schema_id": decision.schema_id,
        "canonical_json": global_stop_operator_decision_canonical_json(decision),
        "canonical_digest": global_stop_operator_decision_canonical_digest(decision),
        "created_at": created_at,
    }


def _seed_receipt(fixture: object, decision: GlobalStopOperatorDecision, **overrides: object) -> None:
    row = {**_receipt_row(decision), **overrides}
    connection = open_existing_sqlite_connection(fixture.location, read_only=False)
    try:
        connection.execute("BEGIN IMMEDIATE")
        _insert_row(
            connection,
            "global_stop_operator_decision_receipts",
            GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_ROW_COLUMNS,
            row,
        )
        connection.execute("COMMIT")
    except Exception:
        _rollback(connection)
        raise
    finally:
        connection.close()


def _insert_row(
    connection: sqlite3.Connection,
    table_name: str,
    columns: tuple[str, ...],
    row: dict[str, object],
) -> None:
    connection.execute(
        f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
        tuple(row[column] for column in columns),
    )


def _global_stop_event_envelopes(fixture: object) -> tuple[GlobalStopEventRecordEnvelope, ...]:
    connection = open_existing_sqlite_connection(fixture.location, read_only=True)
    try:
        columns = ", ".join(GLOBAL_STOP_EVENT_ROW_COLUMNS)
        rows = connection.execute(
            f"SELECT {columns} FROM global_stop_events ORDER BY event_sequence"
        ).fetchall()
    finally:
        connection.close()
    envelopes: list[GlobalStopEventRecordEnvelope] = []
    for row in rows:
        mapping = dict(zip(GLOBAL_STOP_EVENT_ROW_COLUMNS, tuple(row), strict=True))
        envelope = global_stop_event_record_envelope_from_row(mapping)
        assert type(envelope) is GlobalStopEventRecordEnvelope
        envelopes.append(envelope)
    return tuple(envelopes)


def _receipt_rows(fixture: object) -> tuple[tuple[object, ...], ...]:
    connection = open_existing_sqlite_connection(fixture.location, read_only=True)
    try:
        return tuple(
            tuple(row)
            for row in connection.execute(
                "SELECT decision_ref, authorized, reason FROM global_stop_operator_decision_receipts ORDER BY decision_ref"
            ).fetchall()
        )
    finally:
        connection.close()


def _rollback(connection: sqlite3.Connection) -> None:
    try:
        connection.execute("ROLLBACK")
    except sqlite3.Error:
        pass


def test_private_entry_preflight_runs_before_controller_mutation_slot_sqlite_or_clock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ge_nwp_coordinator.sqlite_writer_session as writer_module

    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        calls = {"mutation": 0, "open": 0, "clock": 0}
        original_mutation_factory = writer_module._MUTATION_LEASE_FACTORY

        def mutation_factory(**kwargs: object) -> object:
            calls["mutation"] += 1
            return original_mutation_factory(**kwargs)

        def fail_open(*args: object, **kwargs: object) -> object:
            calls["open"] += 1
            raise AssertionError("preflight opened SQLite")

        def fail_clock() -> str:
            calls["clock"] += 1
            raise AssertionError("preflight read clock")

        monkeypatch.setattr(writer_module, "_MUTATION_LEASE_FACTORY", mutation_factory)
        monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", fail_open)
        monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", fail_clock)

        with fixture.writer_session._resource.operation_guard(fixture.writer_session) as operation:
            with pytest.raises(Exception) as exc_info:
                transaction_module._run_atomic_global_stop_apply(
                    operation_lease=operation,
                    global_stop_command=object(),  # type: ignore[arg-type]
                    typed_operator_decision=_decision(),
                )

        assert type(exc_info.value).__name__ == "_GlobalStopApplyPreflightError"
        assert calls == {"mutation": 0, "open": 0, "clock": 0}
        assert global_stop_event_count_for_test(fixture) == 0


def test_private_atomic_accepted_activate_commits_event_cas_and_exact_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        decision = _decision()
        command = _command(decision_ref=decision.decision_ref)
        _seed_receipt(fixture, decision)
        _patch_clock(monkeypatch)

        fresh = _assert_committed(_run_global_stop_apply(fixture, command, decision), replayed=False)

        assert fresh.event.outcome is GlobalStopEventOutcome.ACCEPTED
        assert fresh.event.reason == "global_stop_update_accepted"
        assert fresh.state.active is True
        assert fresh.state.version == 1
        envelopes = _global_stop_event_envelopes(fixture)
        assert len(envelopes) == 1
        assert envelopes[0].event_sequence == 0
        assert envelopes[0].event == fresh.event
        assert envelopes[0].replay_state == fresh.state
        assert envelopes[0].created_at == B4B_TIMESTAMP
        assert read_back_fixture_for_test(fixture).global_stop.state == fresh.state
        assert transition_event_count_for_test(fixture) == 0

        calls: list[str] = []

        def fail_if_called(name: str) -> object:
            def inner(*args: object, **kwargs: object) -> object:
                calls.append(name)
                raise AssertionError(f"replay called {name}")

            return inner

        monkeypatch.setattr(transaction_module, "_read_global_stop_event_max_sequence", fail_if_called("max"))
        monkeypatch.setattr(transaction_module, "next_global_stop_event_sequence", fail_if_called("allocator"))
        monkeypatch.setattr(transaction_module, "_global_stop_write_plan", fail_if_called("plan"))
        monkeypatch.setattr(transaction_module, "_execute_global_stop_event_insert", fail_if_called("insert"))
        monkeypatch.setattr(transaction_module, "_execute_accepted_global_stop_current_cas", fail_if_called("cas"))
        monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", fail_if_called("clock"))
        monkeypatch.setattr(transaction_module, "evaluate_global_stop_update", fail_if_called("evaluator"))

        replay = _assert_committed(_run_global_stop_apply(fixture, command, decision), replayed=True)

        assert replay.event == fresh.event
        assert replay.state == fresh.state
        assert calls == []
        assert global_stop_event_count_for_test(fixture) == 1


def test_private_atomic_replace_clear_sequence_and_current_updates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        _patch_clock(monkeypatch)
        activate_decision = _decision(ref="operator-decision-b4b-activate")
        replace_decision = _decision(ref="operator-decision-b4b-replace")
        clear_decision = _decision(ref="operator-decision-b4b-clear")
        for decision in (activate_decision, replace_decision, clear_decision):
            _seed_receipt(fixture, decision)

        activate = _assert_committed(
            _run_global_stop_apply(
                fixture,
                _command(decision_ref=activate_decision.decision_ref, stop_id="global-stop-b4b-a"),
                activate_decision,
            ),
            replayed=False,
        )
        replace_command = _command(
            action=GlobalStopAction.REPLACE,
            key="global-stop-b4b-key-2",
            expected_version=activate.state.version,
            decision_ref=replace_decision.decision_ref,
            source_stop_id=activate.state.stop_id,
            stop_id="global-stop-b4b-b",
            issuer_ref="operator-policy-replace",
            issued_at="2026-07-22T12:00:01Z",
        )
        replaced = _assert_committed(_run_global_stop_apply(fixture, replace_command, replace_decision), replayed=False)
        clear_command = _command(
            action=GlobalStopAction.CLEAR,
            key="global-stop-b4b-key-3",
            expected_version=replaced.state.version,
            decision_ref=clear_decision.decision_ref,
            source_stop_id=replaced.state.stop_id,
            stop_id=replaced.state.stop_id or "global-stop-b4b-b",
            reason_class=replaced.state.reason_class or GlobalStopReasonClass.OPERATOR_STOP,
            issuer_ref=replaced.state.issuer_ref or "operator-policy-replace",
            issued_at=replaced.state.issued_at or "2026-07-22T12:00:01Z",
        )
        cleared = _assert_committed(_run_global_stop_apply(fixture, clear_command, clear_decision), replayed=False)

        assert replaced.state.active is True
        assert replaced.state.stop_id == "global-stop-b4b-b"
        assert cleared.state == GlobalStopState(version=3, active=False)
        envelopes = _global_stop_event_envelopes(fixture)
        assert tuple(envelope.event_sequence for envelope in envelopes) == (0, 1, 2)
        assert tuple(envelope.event for envelope in envelopes) == (activate.event, replaced.event, cleared.event)
        assert read_back_fixture_for_test(fixture).global_stop.state == cleared.state


def test_unauthorized_receipt_persists_domain_rejected_event_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        decision = _decision(authorized=False)
        command = _command(decision_ref=decision.decision_ref)
        _seed_receipt(fixture, decision)
        _patch_clock(monkeypatch)
        before = read_back_fixture_for_test(fixture).global_stop

        result = _assert_committed(_run_global_stop_apply(fixture, command, decision), replayed=False)

        assert result.event.outcome is GlobalStopEventOutcome.DOMAIN_REJECTED
        assert result.event.reason == "operator_authorization_required"
        assert result.state == before.state
        after = read_back_fixture_for_test(fixture).global_stop
        assert after.state == before.state
        assert after.updated_at == before.updated_at
        envelopes = _global_stop_event_envelopes(fixture)
        assert len(envelopes) == 1
        assert envelopes[0].event_sequence == 0
        assert envelopes[0].event == result.event
        assert envelopes[0].replay_state == before.state


def test_missing_mismatched_and_malformed_receipts_do_not_fallback_to_caller_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as missing_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "missing") as fixture:
            decision = _decision()
            command = _command(decision_ref=decision.decision_ref)
            calls: list[str] = []
            missing_patch.setattr(transaction_module, "evaluate_global_stop_update", lambda *args: calls.append("eval"))
            missing_patch.setattr(transaction_module, "_read_global_stop_event_max_sequence", lambda *args: calls.append("max"))

            result = _assert_conflict(_run_global_stop_apply(fixture, command, decision), "validation_failed")

            assert result.conflict_class == "validation_failed"
            assert calls == []
            assert global_stop_event_count_for_test(fixture) == 0
            assert _receipt_rows(fixture) == ()

    with monkeypatch.context() as mismatch_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "mismatch") as fixture:
            persisted = _decision()
            caller = _decision(ref=persisted.decision_ref, authorized=False)
            command = _command(decision_ref=persisted.decision_ref)
            _seed_receipt(fixture, persisted)
            mismatch_patch.setattr(transaction_module, "evaluate_global_stop_update", lambda *args: pytest.fail("caller fallback"))

            result = _assert_conflict(_run_global_stop_apply(fixture, command, caller), "validation_failed")

            assert result.conflict_class == "validation_failed"
            assert global_stop_event_count_for_test(fixture) == 0
            assert _receipt_rows(fixture) == ((persisted.decision_ref, 1, "accepted"),)

    with make_coherent_transition_fixture_for_test(tmp_path / "malformed") as fixture:
        persisted = _decision()
        caller = _decision(ref=persisted.decision_ref, authorized=False)
        command = _command(decision_ref=persisted.decision_ref)
        _seed_receipt(fixture, persisted, canonical_digest="0" * 64)

        _run_global_stop_apply_raises(fixture, command, caller, "database_integrity_failure")

        assert global_stop_event_count_for_test(fixture) == 0


def test_expected_version_and_stale_writer_conflicts_precede_later_reads_and_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as expected_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "expected") as fixture:
            decision = _decision()
            command = _command(expected_version=9, decision_ref=decision.decision_ref)
            _seed_receipt(fixture, decision)
            calls: list[str] = []
            expected_patch.setattr(transaction_module, "_read_global_stop_operator_decision_receipt", lambda *args: calls.append("receipt"))
            expected_patch.setattr(transaction_module, "evaluate_global_stop_update", lambda *args: calls.append("eval"))
            expected_patch.setattr(transaction_module, "_execute_global_stop_event_insert", lambda *args: calls.append("insert"))

            _assert_conflict(_run_global_stop_apply(fixture, command, decision), "expected_version_conflict")

            assert calls == []
            assert global_stop_event_count_for_test(fixture) == 0

    with monkeypatch.context() as stale_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "stale") as fixture:
            from test_b3c1b_rollback_only_writer_fencing import _replace_writer_row

            decision = _decision()
            command = _command(decision_ref=decision.decision_ref)
            _seed_receipt(fixture, decision)
            _replace_writer_row(fixture.location, issuance_nonce_digest="0" * 64)
            calls: list[str] = []
            stale_patch.setattr(transaction_module, "_create_sqlite_mutation_read_capability", lambda **kwargs: calls.append("capability"))
            stale_patch.setattr(transaction_module, "_read_global_stop_event_for_idempotency", lambda *args: calls.append("idempotency"))

            _assert_conflict(_run_global_stop_apply(fixture, command, decision), "stale_writer_token")

            assert calls == []
            assert global_stop_event_count_for_test(fixture) == 0


def test_pre_apply_invalid_from_fresh_evaluator_fails_closed_without_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        decision = _decision()
        command = _command(decision_ref=decision.decision_ref)
        _seed_receipt(fixture, decision)

        def pre_apply_invalid(state: GlobalStopState, command: GlobalStopCommand, decision: GlobalStopOperatorDecision) -> GlobalStopEvaluation:
            return GlobalStopEvaluation(
                kind=GlobalStopEvaluationKind.PRE_APPLY_INVALID,
                state=state,
                event=None,
                reason="decision_reference_mismatch",
            )

        monkeypatch.setattr(transaction_module, "evaluate_global_stop_update", pre_apply_invalid)

        _run_global_stop_apply_raises(fixture, command, decision, "database_integrity_failure")

        assert global_stop_event_count_for_test(fixture) == 0


def test_sequence_overflow_collision_insert_cas_and_rollback_failures_leave_no_partial_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as overflow_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "overflow") as fixture:
            decision = _decision()
            command = _command(decision_ref=decision.decision_ref)
            _seed_receipt(fixture, decision)
            _patch_clock(overflow_patch)
            overflow_patch.setattr(transaction_module, "_read_global_stop_event_max_sequence", lambda capability: SQLITE_SIGNED_INT_MAX)

            _run_global_stop_apply_raises(fixture, command, decision, "event_sequence_exhausted")

            assert global_stop_event_count_for_test(fixture) == 0
            assert read_back_fixture_for_test(fixture).global_stop.state == GlobalStopState()

    with monkeypatch.context() as collision_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "collision") as fixture:
            first_decision = _decision(ref="operator-decision-b4b-first")
            second_decision = _decision(ref="operator-decision-b4b-second")
            _seed_receipt(fixture, first_decision)
            _seed_receipt(fixture, second_decision)
            _patch_clock(collision_patch)
            first_command = _command(decision_ref=first_decision.decision_ref, stop_id="global-stop-b4b-first")
            _assert_committed(_run_global_stop_apply(fixture, first_command, first_decision), replayed=False)
            second_command = _command(
                key="global-stop-b4b-key-2",
                expected_version=1,
                decision_ref=second_decision.decision_ref,
                action=GlobalStopAction.REPLACE,
                source_stop_id="global-stop-b4b-first",
                stop_id="global-stop-b4b-second",
            )
            collision_patch.setattr(transaction_module, "_read_global_stop_event_max_sequence", lambda capability: None)

            _run_global_stop_apply_raises(fixture, second_command, second_decision, "database_integrity_failure")

            assert tuple(envelope.event_sequence for envelope in _global_stop_event_envelopes(fixture)) == (0,)

    with monkeypatch.context() as insert_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "insert") as fixture:
            decision = _decision()
            command = _command(decision_ref=decision.decision_ref)
            _seed_receipt(fixture, decision)
            _patch_clock(insert_patch)
            insert_patch.setattr(transaction_module, "_execute_global_stop_event_insert", lambda *args: (_ for _ in ()).throw(transaction_module._mutation_failed()))

            _run_global_stop_apply_raises(fixture, command, decision, "mutation_failed")

            assert global_stop_event_count_for_test(fixture) == 0
            assert read_back_fixture_for_test(fixture).global_stop.state == GlobalStopState()

    with monkeypatch.context() as cas_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "cas") as fixture:
            decision = _decision()
            command = _command(decision_ref=decision.decision_ref)
            _seed_receipt(fixture, decision)
            _patch_clock(cas_patch)
            cas_patch.setattr(transaction_module, "_execute_accepted_global_stop_current_cas", lambda *args: (_ for _ in ()).throw(transaction_module._database_integrity_failure()))

            _run_global_stop_apply_raises(fixture, command, decision, "database_integrity_failure")

            assert global_stop_event_count_for_test(fixture) == 0
            assert read_back_fixture_for_test(fixture).global_stop.state == GlobalStopState()

    with monkeypatch.context() as rollback_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "rollback") as fixture:
            decision = _decision()
            command = _command(decision_ref=decision.decision_ref)
            _seed_receipt(fixture, decision)
            _patch_clock(rollback_patch)
            rollback_patch.setattr(transaction_module, "_execute_global_stop_event_insert", lambda *args: (_ for _ in ()).throw(transaction_module._mutation_failed()))
            rollback_patch.setattr(transaction_module, "_rollback_transaction", lambda connection: transaction_module._mutation_failed())

            _run_global_stop_apply_raises(fixture, command, decision, "mutation_failed")

            assert global_stop_event_count_for_test(fixture) == 0


def test_commit_uncertainty_retry_fresh_replay_and_changed_digest_conflict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path / "before") as fixture:
        decision = _decision()
        command = _command(decision_ref=decision.decision_ref)
        _seed_receipt(fixture, decision)
        _patch_clock(monkeypatch)
        rollback_calls = 0

        def no_commit_raised(connection: sqlite3.Connection) -> None:
            raise RuntimeError(PRIVATE_SENTINEL)

        def rollback(connection: sqlite3.Connection) -> object:
            nonlocal rollback_calls
            rollback_calls += 1
            raise AssertionError("rollback after commit attempt")

        monkeypatch.setattr(transaction_module, "_commit_transaction", no_commit_raised)
        monkeypatch.setattr(transaction_module, "_rollback_transaction", rollback)
        _run_global_stop_apply_raises(fixture, command, decision, "commit_outcome_unknown")

        assert rollback_calls == 0
        assert global_stop_event_count_for_test(fixture) == 0
        assert read_back_fixture_for_test(fixture).global_stop.state == GlobalStopState()

        monkeypatch.undo()
        _patch_clock(monkeypatch)
        fresh = _assert_committed(_run_global_stop_apply(fixture, command, decision), replayed=False)
        assert fresh.event.outcome is GlobalStopEventOutcome.ACCEPTED
        assert tuple(envelope.event_sequence for envelope in _global_stop_event_envelopes(fixture)) == (0,)

    with make_coherent_transition_fixture_for_test(tmp_path / "after") as fixture:
        decision = _decision()
        command = _command(decision_ref=decision.decision_ref)
        _seed_receipt(fixture, decision)
        _patch_clock(monkeypatch)

        def commit_then_raise(connection: sqlite3.Connection) -> None:
            connection.execute("COMMIT")
            raise RuntimeError(PRIVATE_SENTINEL)

        monkeypatch.setattr(transaction_module, "_commit_transaction", commit_then_raise)
        _run_global_stop_apply_raises(fixture, command, decision, "commit_outcome_unknown")

        assert global_stop_event_count_for_test(fixture) == 1
        committed = _global_stop_event_envelopes(fixture)[0]
        assert read_back_fixture_for_test(fixture).global_stop.state == committed.replay_state

        calls: list[str] = []
        monkeypatch.setattr(transaction_module, "_commit_transaction", lambda connection: None)
        monkeypatch.setattr(transaction_module, "_read_global_stop_event_max_sequence", lambda *args: calls.append("max"))
        monkeypatch.setattr(transaction_module, "evaluate_global_stop_update", lambda *args: calls.append("evaluator"))
        monkeypatch.setattr(transaction_module, "_execute_global_stop_event_insert", lambda *args: calls.append("insert"))
        replay = _assert_committed(_run_global_stop_apply(fixture, command, decision), replayed=True)

        assert replay.event == committed.event
        assert replay.state == committed.replay_state
        assert calls == []
        assert global_stop_event_count_for_test(fixture) == 1

        changed = _command(
            key=command.idempotency_key,
            expected_version=command.expected_version,
            decision_ref=decision.decision_ref,
            stop_id="global-stop-b4b-changed",
        )
        _assert_conflict(_run_global_stop_apply(fixture, changed, decision), "idempotency_key_reuse_conflict")


def test_sql_trace_receipt_select_event_before_cas_and_no_receipt_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        decision = _decision()
        command = _command(decision_ref=decision.decision_ref)
        _seed_receipt(fixture, decision)
        _patch_clock(monkeypatch)
        traced_sql: list[str] = []
        original_open = transaction_module._open_bound_existing_sqlite_connection

        def tracing_open(*args: object, **kwargs: object) -> sqlite3.Connection:
            connection = original_open(*args, **kwargs)
            connection.set_trace_callback(traced_sql.append)
            return connection

        monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", tracing_open)

        _assert_committed(_run_global_stop_apply(fixture, command, decision), replayed=False)

        normalized = "\n".join(statement.upper() for statement in traced_sql)
        assert "SELECT DECISION_REF, AUTHORIZED, REASON" in normalized
        assert "FROM GLOBAL_STOP_OPERATOR_DECISION_RECEIPTS" in normalized
        assert "INSERT INTO GLOBAL_STOP_EVENTS" in normalized
        assert "UPDATE GLOBAL_STOP_CURRENT" in normalized
        assert normalized.index("INSERT INTO GLOBAL_STOP_EVENTS") < normalized.index("UPDATE GLOBAL_STOP_CURRENT")
        assert "INSERT INTO GLOBAL_STOP_OPERATOR_DECISION_RECEIPTS" not in normalized
        assert "UPDATE GLOBAL_STOP_OPERATOR_DECISION_RECEIPTS" not in normalized
        assert "DELETE FROM GLOBAL_STOP_OPERATOR_DECISION_RECEIPTS" not in normalized
        assert "CREATE " not in normalized
        assert normalized.count("COMMIT") == 1


def test_global_stop_and_transition_mutations_share_one_prompt_mutation_slot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases = (
        ("global-stop-first", "transition-second"),
        ("transition-first", "global-stop-second"),
        ("global-stop-first", "global-stop-second"),
    )
    for first, second in cases:
        with monkeypatch.context() as case_patch:
            with make_coherent_transition_fixture_for_test(tmp_path / f"{first}-{second}") as fixture:
                decision = _decision()
                command = _command(decision_ref=decision.decision_ref)
                _seed_receipt(fixture, decision)
                _patch_clock(case_patch)
                original_open = transaction_module._open_bound_existing_sqlite_connection
                entered = threading.Event()
                release = threading.Event()
                first_result: list[object] = []
                first_error: list[BaseException] = []

                def blocking_open(*args: object, **kwargs: object) -> sqlite3.Connection:
                    entered.set()
                    if not release.wait(timeout=5):
                        raise RuntimeError(PRIVATE_SENTINEL)
                    return original_open(*args, **kwargs)

                case_patch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", blocking_open)

                def run_first() -> None:
                    try:
                        if first == "transition-first":
                            with fixture.writer_session._resource.operation_guard(fixture.writer_session) as operation:
                                first_result.append(
                                    transaction_module._run_atomic_transition_apply(
                                        operation_lease=operation,
                                        transition_command=fixture.command,
                                    )
                                )
                        else:
                            first_result.append(_run_global_stop_apply(fixture, command, decision))
                    except Exception as exc:
                        first_error.append(exc)

                thread = threading.Thread(target=run_first)
                thread.start()
                assert entered.wait(timeout=5)
                try:
                    with pytest.raises(WriterSessionError) as exc_info:
                        if second == "transition-second":
                            with fixture.writer_session._resource.operation_guard(fixture.writer_session) as operation:
                                transaction_module._run_atomic_transition_apply(
                                    operation_lease=operation,
                                    transition_command=fixture.command,
                                )
                        else:
                            _run_global_stop_apply(fixture, command, decision)
                    assert exc_info.value.reason is WriterSessionFailureReason.WRITER_SESSION_MUTATION_IN_PROGRESS
                    assert fixture.writer_session._resource._mutation_slot is not None
                finally:
                    release.set()
                    thread.join(timeout=5)
                assert not thread.is_alive()
                assert first_error == []
                assert len(first_result) == 1
                assert fixture.writer_session._resource._mutation_slot is None


def test_public_boundaries_static_neutralization_and_b4c_adapter_keeps_private_exports_closed(
    tmp_path: Path,
) -> None:
    source = TRANSACTION_MODULE_PATH.read_text(encoding="utf-8")
    writer_source = WRITER_SESSION_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    function_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

    assert class_names.count("_CoordinatorMutationTransactionController") == 1
    assert class_names.count("_SQLiteMutationReadCapability") == 1
    assert class_names.count("_MutationCapabilityState") == 1
    assert "_TransitionTransactionController" not in class_names
    assert "_SQLiteTransitionReadCapability" not in class_names
    assert "_TransactionCapabilityState" not in class_names
    assert function_names.count("_create_sqlite_mutation_read_capability") == 1
    assert function_names.count("_invalidate_sqlite_mutation_read_capability") == 1
    assert "_create_sqlite_transition_read_capability" not in function_names
    assert "_invalidate_sqlite_transition_read_capability" not in function_names
    assert "_run_rollback_only_writer_fencing" in function_names
    assert "_run_rollback_only_transition_dry_run" in function_names
    assert "_run_atomic_transition_apply" in function_names
    assert "_run_atomic_global_stop_apply" in function_names
    assert source.count("class _CoordinatorMutationTransactionController") == 1
    assert source.count("_MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS") == 2
    assert mutation_contracts._MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS is transaction_module._MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS
    assert "_run_atomic_global_stop_apply" in writer_source
    assert "_run_atomic_global_stop_apply" not in PACKAGE_EXPORT_PATH.read_text(encoding="utf-8")
    assert not hasattr(ge_nwp_coordinator, "_run_atomic_global_stop_apply")
    assert not list(MIGRATION_DIR.glob("0002*"))

    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        result = fixture.writer_session.apply_global_stop_update(_command(), _decision())
        assert type(result) is GlobalStopConflict
        assert result.conflict_class == "validation_failed"
        assert global_stop_event_count_for_test(fixture) == 0


def test_crash_reacquisition_replays_committed_global_stop_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        decision = _decision()
        command = _command(decision_ref=decision.decision_ref)
        _seed_receipt(fixture, decision)
        _patch_clock(monkeypatch)
        result = _assert_committed(_run_global_stop_apply(fixture, command, decision), replayed=False)
        location = fixture.location
        fixture.writer_session.close()

        restarted = acquire_sqlite_writer_session(location)
        try:
            restarted_fixture = replace(fixture, writer_session=restarted)
            replay = _assert_committed(_run_global_stop_apply(restarted_fixture, command, decision), replayed=True)
            assert replay.event == result.event
            assert replay.state == result.state
            assert global_stop_event_count_for_test(restarted_fixture) == 1
        finally:
            restarted.close()
