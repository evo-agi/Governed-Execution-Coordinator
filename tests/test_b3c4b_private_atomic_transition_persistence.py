from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
import sqlite3
import traceback

import pytest

import ge_nwp_coordinator
from b3_coherent_transition_fixture import (
    FIXTURE_TIMESTAMP,
    _transition_event_row_for_test,
    global_stop_event_count_for_test,
    make_coherent_transition_fixture_for_test,
    read_back_fixture_for_test,
    transition_event_count_for_test,
)
from ge_nwp_coordinator.persistence_contracts import (
    SQLITE_SIGNED_INT_MAX,
    TRANSITION_EVENT_ROW_COLUMNS,
    TransitionEventRecordEnvelope,
    transition_event_record_envelope_from_row,
)
from ge_nwp_coordinator.sqlite_connection import open_existing_sqlite_connection
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
import ge_nwp_coordinator.sqlite_mutation_transaction_contracts as mutation_contracts
import ge_nwp_coordinator.sqlite_transition_transaction as transaction_module
from ge_nwp_coordinator.state_machine import (
    TransitionCommand,
    TransitionEvaluation,
    TransitionEventOutcome,
    WorkItemState,
)
from ge_nwp_coordinator.state_store import (
    CommittedTransition,
    GlobalStopApplyPreflightError,
    GlobalStopApplyPreflightFailureReason,
    TransitionConflict,
    WriterSessionError,
    WriterSessionFailureReason,
)
from test_b3c1b_rollback_only_writer_fencing import _replace_writer_row


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
TRANSACTION_MODULE_PATH = PACKAGE_DIR / "sqlite_transition_transaction.py"
WRITER_SESSION_PATH = PACKAGE_DIR / "sqlite_writer_session.py"
STATE_STORE_PATH = PACKAGE_DIR / "state_store.py"
PACKAGE_EXPORT_PATH = PACKAGE_DIR / "__init__.py"
MIGRATION_DIR = PACKAGE_DIR / "sqlite_migrations"
PRIVATE_SENTINEL = "b3c4b-private-sentinel-do-not-leak"


def _run_apply(fixture: object, command: TransitionCommand | None = None) -> object:
    selected = command if command is not None else fixture.command
    with fixture.writer_session._resource.operation_guard(fixture.writer_session) as operation:
        return transaction_module._run_atomic_transition_apply(
            operation_lease=operation,
            transition_command=selected,
        )


def _run_apply_raises(
    fixture: object,
    error_class: str,
    command: TransitionCommand | None = None,
) -> SQLiteMutationStoreError:
    with pytest.raises(SQLiteMutationStoreError) as exc_info:
        _run_apply(fixture, command)
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


def _assert_committed(result: object, *, replayed: bool) -> CommittedTransition:
    assert type(result) is CommittedTransition
    assert result.replayed is replayed
    return result


def _assert_conflict(result: object, conflict_class: str) -> TransitionConflict:
    assert type(result) is TransitionConflict
    assert result.conflict_class == conflict_class
    return result


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


def _transition_event_envelopes(fixture: object) -> tuple[TransitionEventRecordEnvelope, ...]:
    connection = open_existing_sqlite_connection(fixture.location, read_only=True)
    try:
        columns = ", ".join(TRANSITION_EVENT_ROW_COLUMNS)
        rows = connection.execute(
            f"SELECT {columns} FROM transition_events ORDER BY event_sequence"
        ).fetchall()
    finally:
        connection.close()
    envelopes: list[TransitionEventRecordEnvelope] = []
    for row in rows:
        mapping = dict(zip(TRANSITION_EVENT_ROW_COLUMNS, tuple(row), strict=True))
        envelope = transition_event_record_envelope_from_row(mapping)
        assert type(envelope) is TransitionEventRecordEnvelope
        envelopes.append(envelope)
    return tuple(envelopes)


def _insert_transition_event_row(fixture: object, row: dict[str, object]) -> None:
    connection = open_existing_sqlite_connection(fixture.location, read_only=False)
    try:
        connection.execute("BEGIN IMMEDIATE")
        columns = ", ".join(TRANSITION_EVENT_ROW_COLUMNS)
        placeholders = ", ".join("?" for _ in TRANSITION_EVENT_ROW_COLUMNS)
        connection.execute(
            f"INSERT INTO transition_events ({columns}) VALUES ({placeholders})",
            tuple(row[column] for column in TRANSITION_EVENT_ROW_COLUMNS),
        )
        connection.execute("COMMIT")
    except Exception:
        try:
            connection.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        connection.close()


def _dry_run_evaluation(fixture: object, command: TransitionCommand) -> TransitionEvaluation:
    with fixture.writer_session._resource.operation_guard(fixture.writer_session) as operation:
        result = transaction_module._run_rollback_only_transition_dry_run(
            operation_lease=operation,
            transition_command=command,
        )
    assert type(result.evaluation) is TransitionEvaluation
    return result.evaluation


def _delete_all_rows(fixture: object, table_name: str) -> None:
    connection = sqlite3.connect(fixture.location.database_path)
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(f"DELETE FROM {table_name}")
        connection.commit()
    finally:
        connection.close()


def _patch_clock(monkeypatch: pytest.MonkeyPatch, timestamp: str = FIXTURE_TIMESTAMP) -> None:
    monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", lambda: timestamp)


def _controller_with_resolution_state(state: object) -> object:
    controller = object.__new__(transaction_module._CoordinatorMutationTransactionController)
    controller._resolution_state = state
    return controller


def _capture_resolution_trace(
    monkeypatch: pytest.MonkeyPatch,
    *,
    fail_on: tuple[object, ...] = (),
) -> list[object]:
    trace: list[object] = []
    original_init = transaction_module._CoordinatorMutationTransactionController.__init__
    original_set = transaction_module._CoordinatorMutationTransactionController._set_resolution_state

    def traced_init(self: object, *args: object, **kwargs: object) -> None:
        original_init(self, *args, **kwargs)
        trace.append(self._resolution_state)

    def traced_set(self: object, state: object) -> None:
        if state in fail_on:
            raise transaction_module._database_integrity_failure()
        original_set(self, state)
        trace.append(self._resolution_state)

    monkeypatch.setattr(transaction_module._CoordinatorMutationTransactionController, "__init__", traced_init)
    monkeypatch.setattr(transaction_module._CoordinatorMutationTransactionController, "_set_resolution_state", traced_set)
    return trace


def _record_rollback_and_close(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []
    original_rollback = transaction_module._rollback_transaction
    original_close = transaction_module._close_connection

    def rollback(connection: sqlite3.Connection) -> object:
        calls.append("rollback")
        return original_rollback(connection)

    def close(connection: sqlite3.Connection) -> object:
        calls.append("close")
        return original_close(connection)

    monkeypatch.setattr(transaction_module, "_rollback_transaction", rollback)
    monkeypatch.setattr(transaction_module, "_close_connection", close)
    return calls


def _fresh_block_command(command: TransitionCommand, *, expected_version: int, key: str) -> TransitionCommand:
    return _reissue_command(
        command,
        idempotency_key=key,
        expected_version=expected_version,
        target_state=WorkItemState.BLOCKED,
        dependency_decision_ref=None,
        safe_failure_class="operator_action_required",
    )


def test_resolution_state_setter_enforces_frozen_allowed_graph_for_every_enum_pair() -> None:
    state = transaction_module._MutationCommitResolutionState
    allowed = transaction_module._MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS
    assert allowed is mutation_contracts._MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS

    explicit_disallowed = {
        (state.NEW, state.CLOSED),
        (state.NEW, state.COMMIT_SUCCEEDED),
        (state.TRANSACTION_ACTIVE, state.CAPABILITY_INVALIDATED),
        (state.FENCED, state.ROLLBACK_RESOLVED),
        (state.CAPABILITY_ACTIVE, state.ROLLBACK_RESOLVED),
        (state.PLANNED_OUTCOME, state.ROLLBACK_RESOLVED),
        (state.WRITES_PERFORMED, state.ROLLBACK_RESOLVED),
        (state.COMMIT_ATTEMPT_STARTED, state.ROLLBACK_RESOLVED),
        (state.COMMIT_SUCCEEDED, state.COMMIT_OUTCOME_UNKNOWN),
    }
    assert explicit_disallowed.isdisjoint(allowed)
    for member in state:
        assert (member, member) not in allowed
    assert all(current is not state.CLOSED for current, _next_state in allowed)

    for source in state:
        for target in state:
            controller = _controller_with_resolution_state(source)
            if (source, target) in allowed:
                controller._set_resolution_state(target)
                assert controller._resolution_state is target
            else:
                with pytest.raises(SQLiteMutationStoreError) as exc_info:
                    controller._set_resolution_state(target)
                _assert_mutation_error(exc_info.value, "database_integrity_failure")
                assert controller._resolution_state is source

    bad_current = _controller_with_resolution_state("capability_active")
    with pytest.raises(SQLiteMutationStoreError) as current_error:
        bad_current._set_resolution_state(state.CAPABILITY_INVALIDATED)
    _assert_mutation_error(current_error.value, "database_integrity_failure")
    assert bad_current._resolution_state == "capability_active"

    bad_next = _controller_with_resolution_state(state.NEW)
    with pytest.raises(SQLiteMutationStoreError) as next_error:
        bad_next._set_resolution_state("closed")
    _assert_mutation_error(next_error.value, "database_integrity_failure")
    assert bad_next._resolution_state is state.NEW


def test_resolution_state_traces_record_only_successful_milestones(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = transaction_module._MutationCommitResolutionState
    replay_or_conflict_path = [
        state.NEW,
        state.TRANSACTION_ACTIVE,
        state.FENCED,
        state.CAPABILITY_ACTIVE,
        state.CAPABILITY_INVALIDATED,
        state.ROLLBACK_RESOLVED,
        state.CLOSED,
    ]

    with monkeypatch.context() as replay_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "replay", existing_event=True) as fixture:
            trace = _capture_resolution_trace(replay_patch)
            _assert_committed(_run_apply(fixture), replayed=True)
            assert trace == replay_or_conflict_path

    with monkeypatch.context() as planned_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "planned", ready_dependency=True) as fixture:
            _patch_clock(planned_patch)
            trace = _capture_resolution_trace(planned_patch)
            planned_patch.setattr(
                transaction_module,
                "_execute_transition_event_insert",
                lambda *args: (_ for _ in ()).throw(transaction_module._mutation_failed()),
            )

            _run_apply_raises(fixture, "mutation_failed")

            assert trace == [
                state.NEW,
                state.TRANSACTION_ACTIVE,
                state.FENCED,
                state.CAPABILITY_ACTIVE,
                state.PLANNED_OUTCOME,
                state.CAPABILITY_INVALIDATED,
                state.ROLLBACK_RESOLVED,
                state.CLOSED,
            ]

    with monkeypatch.context() as post_write_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "post-write", ready_dependency=True) as fixture:
            _patch_clock(post_write_patch)
            trace = _capture_resolution_trace(post_write_patch, fail_on=(state.COMMIT_ATTEMPT_STARTED,))

            _run_apply_raises(fixture, "database_integrity_failure")

            assert trace == [
                state.NEW,
                state.TRANSACTION_ACTIVE,
                state.FENCED,
                state.CAPABILITY_ACTIVE,
                state.PLANNED_OUTCOME,
                state.WRITES_PERFORMED,
                state.CAPABILITY_INVALIDATED,
                state.ROLLBACK_RESOLVED,
                state.CLOSED,
            ]

    with monkeypatch.context() as success_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "success", ready_dependency=True) as fixture:
            _patch_clock(success_patch)
            trace = _capture_resolution_trace(success_patch)
            _assert_committed(_run_apply(fixture), replayed=False)
            assert trace == [
                state.NEW,
                state.TRANSACTION_ACTIVE,
                state.FENCED,
                state.CAPABILITY_ACTIVE,
                state.PLANNED_OUTCOME,
                state.WRITES_PERFORMED,
                state.CAPABILITY_INVALIDATED,
                state.COMMIT_ATTEMPT_STARTED,
                state.COMMIT_SUCCEEDED,
                state.CLOSED,
            ]

    with monkeypatch.context() as uncertain_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "uncertain", ready_dependency=True) as fixture:
            _patch_clock(uncertain_patch)
            trace = _capture_resolution_trace(uncertain_patch)
            uncertain_patch.setattr(
                transaction_module,
                "_commit_transaction",
                lambda connection: transaction_module._commit_outcome_unknown(),
            )

            _run_apply_raises(fixture, "commit_outcome_unknown")

            assert trace == [
                state.NEW,
                state.TRANSACTION_ACTIVE,
                state.FENCED,
                state.CAPABILITY_ACTIVE,
                state.PLANNED_OUTCOME,
                state.WRITES_PERFORMED,
                state.CAPABILITY_INVALIDATED,
                state.COMMIT_ATTEMPT_STARTED,
                state.COMMIT_OUTCOME_UNKNOWN,
                state.CLOSED,
            ]

    with monkeypatch.context() as stale_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "stale", existing_event=True) as fixture:
            _replace_writer_row(fixture.location, issuance_nonce_digest="0" * 64)
            trace = _capture_resolution_trace(stale_patch)
            _assert_conflict(_run_apply(fixture), "stale_writer_token")
            assert trace == [state.NEW, state.TRANSACTION_ACTIVE, state.FENCED]


def test_private_atomic_accepted_transition_commits_event_cas_and_exact_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(
        tmp_path,
        ready_dependency=True,
        dependencies_satisfied=True,
    ) as fixture:
        _patch_clock(monkeypatch)

        fresh = _assert_committed(_run_apply(fixture), replayed=False)

        assert fresh.event.outcome is TransitionEventOutcome.ACCEPTED
        assert fresh.event.reason == "transition_accepted"
        assert fresh.event.lease_runtime.evaluated_at == FIXTURE_TIMESTAMP
        assert fresh.record.state is WorkItemState.READY
        assert fresh.record.version == fixture.work_item.version + 1
        envelopes = _transition_event_envelopes(fixture)
        assert len(envelopes) == 1
        assert envelopes[0].event_sequence == 0
        assert envelopes[0].event == fresh.event
        assert envelopes[0].replay_record == fresh.record
        assert envelopes[0].created_at == FIXTURE_TIMESTAMP
        readback = read_back_fixture_for_test(fixture)
        assert readback.work_item.record == fresh.record
        assert readback.work_item.updated_at == FIXTURE_TIMESTAMP
        assert global_stop_event_count_for_test(fixture) == 0

        calls: list[str] = []

        def fail_if_called(name: str) -> object:
            def inner(*args: object, **kwargs: object) -> object:
                calls.append(name)
                raise AssertionError(f"replay called {name}")

            return inner

        monkeypatch.setattr(transaction_module, "_read_transition_event_max_sequence", fail_if_called("max-sequence"))
        monkeypatch.setattr(transaction_module, "next_transition_event_sequence", fail_if_called("allocator"))
        monkeypatch.setattr(transaction_module, "_transition_write_plan", fail_if_called("plan"))
        monkeypatch.setattr(transaction_module, "_execute_transition_event_insert", fail_if_called("insert"))
        monkeypatch.setattr(transaction_module, "_execute_accepted_work_item_cas", fail_if_called("cas"))
        monkeypatch.setattr(transaction_module, "_utc_transaction_timestamp", fail_if_called("clock"))
        monkeypatch.setattr(transaction_module, "evaluate_transition", fail_if_called("evaluator"))

        replay = _assert_committed(_run_apply(fixture), replayed=True)

        assert replay.event == fresh.event
        assert replay.record == fresh.record
        assert transition_event_count_for_test(fixture) == 1
        assert calls == []


def test_next_fresh_transition_allocates_next_sequence_and_never_reuses_committed_sequence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(
        tmp_path,
        ready_dependency=True,
        dependencies_satisfied=True,
    ) as fixture:
        _patch_clock(monkeypatch)
        first = _assert_committed(_run_apply(fixture), replayed=False)
        second_command = _fresh_block_command(
            fixture.command,
            expected_version=first.record.version,
            key="transition-b3-fixture-k2",
        )

        second = _assert_committed(_run_apply(fixture, second_command), replayed=False)

        envelopes = _transition_event_envelopes(fixture)
        assert tuple(envelope.event_sequence for envelope in envelopes) == (0, 1)
        assert envelopes[0].event == first.event
        assert envelopes[1].event == second.event
        assert second.event.source_version == first.record.version
        assert second.record.version == first.record.version + 1
        assert read_back_fixture_for_test(fixture).work_item.record == second.record


def test_domain_rejected_transition_commits_event_without_current_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        _patch_clock(monkeypatch)
        before = read_back_fixture_for_test(fixture).work_item

        result = _assert_committed(_run_apply(fixture), replayed=False)

        assert result.event.outcome is TransitionEventOutcome.DOMAIN_REJECTED
        assert result.event.reason == "lease_not_authorized"
        assert result.record == fixture.work_item
        after = read_back_fixture_for_test(fixture).work_item
        assert after.record == before.record == fixture.work_item
        assert after.updated_at == before.updated_at == FIXTURE_TIMESTAMP
        envelopes = _transition_event_envelopes(fixture)
        assert len(envelopes) == 1
        assert envelopes[0].event_sequence == 0
        assert envelopes[0].event == result.event
        assert envelopes[0].replay_record == fixture.work_item
        assert transition_event_count_for_test(fixture) == 1


def test_atomic_preflight_finishes_before_controller_mutation_slot_sqlite_or_clock(
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
                transaction_module._run_atomic_transition_apply(
                    operation_lease=operation,
                    transition_command=object(),  # type: ignore[arg-type]
                )

        assert type(exc_info.value).__name__ == "_TransitionDryRunPreflightError"
        assert calls == {"mutation": 0, "open": 0, "clock": 0}
        assert transition_event_count_for_test(fixture) == 0


def test_stale_writer_returns_conflict_before_capability_idempotency_or_sequence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, existing_event=True) as fixture:
        _replace_writer_row(fixture.location, issuance_nonce_digest="0" * 64)
        before = transition_event_count_for_test(fixture)
        calls: list[str] = []

        def fail_if_called(name: str) -> object:
            def inner(*args: object, **kwargs: object) -> object:
                calls.append(name)
                raise AssertionError(f"stale writer reached {name}")

            return inner

        monkeypatch.setattr(transaction_module, "_create_sqlite_mutation_read_capability", fail_if_called("capability"))
        monkeypatch.setattr(transaction_module, "_read_transition_event_for_idempotency", fail_if_called("idempotency"))
        monkeypatch.setattr(transaction_module, "_read_transition_event_max_sequence", fail_if_called("max-sequence"))
        monkeypatch.setattr(transaction_module, "evaluate_transition", fail_if_called("evaluator"))

        result = _assert_conflict(_run_apply(fixture), "stale_writer_token")

        assert result.conflict_class == "stale_writer_token"
        assert calls == []
        assert transition_event_count_for_test(fixture) == before


def test_idempotency_conflict_and_pre_evaluation_conflicts_perform_no_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as replay_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "idempotency", existing_event=True) as fixture:
            conflict_command = _reissue_command(
                fixture.command,
                target_state=WorkItemState.BLOCKED,
                safe_failure_class="operator_action_required",
            )
            calls: list[str] = []
            replay_patch.setattr(transaction_module, "_read_current_work_item", lambda *args, **kwargs: calls.append("current"))
            replay_patch.setattr(transaction_module, "_read_transition_event_max_sequence", lambda *args: calls.append("max"))
            replay_patch.setattr(transaction_module, "_execute_transition_event_insert", lambda *args: calls.append("insert"))

            result = _assert_conflict(_run_apply(fixture, conflict_command), "idempotency_key_reuse_conflict")

            assert result.conflict_class == "idempotency_key_reuse_conflict"
            assert calls == []
            assert transition_event_count_for_test(fixture) == 1

    for name, command_factory, expected in (
        ("missing", lambda fixture: fixture.command, "work_item_not_found"),
        ("lower", lambda fixture: _reissue_command(fixture.command, expected_version=0), "expected_version_conflict"),
        ("higher", lambda fixture: _reissue_command(fixture.command, expected_version=2), "expected_version_conflict"),
    ):
        with monkeypatch.context() as conflict_patch:
            with make_coherent_transition_fixture_for_test(tmp_path / name, ready_dependency=True) as fixture:
                conflict_patch.setattr(transaction_module, "_utc_transaction_timestamp", lambda: FIXTURE_TIMESTAMP)
                if name == "missing":
                    _delete_all_rows(fixture, "work_items")
                no_fresh_calls: list[str] = []
                conflict_patch.setattr(
                    transaction_module,
                    "_read_transition_event_max_sequence",
                    lambda *args: no_fresh_calls.append("max"),
                )
                conflict_patch.setattr(
                    transaction_module,
                    "_execute_transition_event_insert",
                    lambda *args: no_fresh_calls.append("insert"),
                )

                result = _assert_conflict(_run_apply(fixture, command_factory(fixture)), expected)

                assert result.conflict_class == expected
                assert no_fresh_calls == []
                assert transition_event_count_for_test(fixture) == 0


def test_sequence_overflow_rolls_back_without_event_or_current_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        _patch_clock(monkeypatch)
        before = read_back_fixture_for_test(fixture).work_item.record
        monkeypatch.setattr(
            transaction_module,
            "_read_transition_event_max_sequence",
            lambda capability: SQLITE_SIGNED_INT_MAX,
        )

        _run_apply_raises(fixture, "event_sequence_exhausted")

        assert transition_event_count_for_test(fixture) == 0
        assert read_back_fixture_for_test(fixture).work_item.record == before


def test_event_ref_sequence_and_idempotency_collisions_after_miss_are_integrity_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as event_ref_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "event-ref") as fixture:
            event_ref_patch.setattr(transaction_module, "_utc_transaction_timestamp", lambda: FIXTURE_TIMESTAMP)
            future_evaluation = _dry_run_evaluation(fixture, fixture.command)
            assert future_evaluation.event is not None
            collision_row = dict(_transition_event_row_for_test(
                future_evaluation.event,
                future_evaluation.record,
                event_sequence=0,
            ))
            collision_row["idempotency_key"] = "transition-b3-fixture-seed"
            collision_row["command_digest"] = "0" * 64
            _insert_transition_event_row(fixture, collision_row)

            _run_apply_raises(fixture, "database_integrity_failure")
            assert transition_event_count_for_test(fixture) == 1

    with monkeypatch.context() as sequence_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "sequence", existing_event=True) as fixture:
            sequence_patch.setattr(transaction_module, "_utc_transaction_timestamp", lambda: FIXTURE_TIMESTAMP)
            sequence_patch.setattr(transaction_module, "_read_transition_event_max_sequence", lambda capability: None)
            fresh_command = _reissue_command(fixture.command, idempotency_key="transition-b3-fixture-k2")

            _run_apply_raises(fixture, "database_integrity_failure", fresh_command)
            assert transition_event_count_for_test(fixture) == 1

    with monkeypatch.context() as idempotency_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "idempotency", existing_event=True) as fixture:
            idempotency_patch.setattr(transaction_module, "_read_transition_event_for_idempotency", lambda *args: None)
            idempotency_patch.setattr(transaction_module, "_utc_transaction_timestamp", lambda: "2026-07-14T00:00:04Z")

            _run_apply_raises(fixture, "database_integrity_failure")
            assert transition_event_count_for_test(fixture) == 1


def test_event_insert_and_cas_failures_roll_back_partial_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path / "insert-close", ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        close_calls = 0
        original_close_cursor = transaction_module._close_cursor_safely

        def close_insert_cursor(cursor: object) -> object:
            nonlocal close_calls
            close_calls += 1
            if close_calls == 2:
                return transaction_module._mutation_failed()
            return original_close_cursor(cursor)

        monkeypatch.setattr(transaction_module, "_close_cursor_safely", close_insert_cursor)
        _run_apply_raises(fixture, "mutation_failed")
        assert transition_event_count_for_test(fixture) == 0
        assert read_back_fixture_for_test(fixture).work_item.record == fixture.work_item

    with make_coherent_transition_fixture_for_test(tmp_path / "cas-close", ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        close_calls = 0
        original_close_cursor = transaction_module._close_cursor_safely

        def close_cas_cursor(cursor: object) -> object:
            nonlocal close_calls
            close_calls += 1
            if close_calls == 3:
                return transaction_module._mutation_failed()
            return original_close_cursor(cursor)

        monkeypatch.setattr(transaction_module, "_close_cursor_safely", close_cas_cursor)
        _run_apply_raises(fixture, "mutation_failed")
        assert transition_event_count_for_test(fixture) == 0
        assert read_back_fixture_for_test(fixture).work_item.record == fixture.work_item


def test_capability_invalidation_rollback_and_close_failures_preserve_no_partial_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path / "capability", ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        monkeypatch.setattr(
            transaction_module,
            "_invalidate_sqlite_mutation_read_capability",
            lambda *args, **kwargs: transaction_module._mutation_failed(),
        )

        _run_apply_raises(fixture, "mutation_failed")

        assert transition_event_count_for_test(fixture) == 0
        assert read_back_fixture_for_test(fixture).work_item.record == fixture.work_item

    with make_coherent_transition_fixture_for_test(tmp_path / "rollback", ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        monkeypatch.setattr(transaction_module, "_execute_transition_event_insert", lambda *args: (_ for _ in ()).throw(transaction_module._mutation_failed()))
        monkeypatch.setattr(transaction_module, "_rollback_transaction", lambda connection: transaction_module._mutation_failed())
        _run_apply_raises(fixture, "mutation_failed")
        assert transition_event_count_for_test(fixture) == 0

    with make_coherent_transition_fixture_for_test(tmp_path / "close", ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        monkeypatch.setattr(transaction_module, "_read_transition_event_max_sequence", lambda capability: (_ for _ in ()).throw(transaction_module._mutation_failed()))
        monkeypatch.setattr(transaction_module, "_close_connection", lambda connection: transaction_module._mutation_failed())
        _run_apply_raises(fixture, "mutation_failed")
        assert transition_event_count_for_test(fixture) == 0


def test_cleanup_failures_do_not_fabricate_successful_resolution_milestones(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = transaction_module._MutationCommitResolutionState

    invalidation_cases = (
        ("capability-active", True, None, [state.NEW, state.TRANSACTION_ACTIVE, state.FENCED, state.CAPABILITY_ACTIVE]),
        (
            "planned-outcome",
            False,
            "event-insert",
            [state.NEW, state.TRANSACTION_ACTIVE, state.FENCED, state.CAPABILITY_ACTIVE, state.PLANNED_OUTCOME],
        ),
        (
            "writes-performed",
            False,
            None,
            [
                state.NEW,
                state.TRANSACTION_ACTIVE,
                state.FENCED,
                state.CAPABILITY_ACTIVE,
                state.PLANNED_OUTCOME,
                state.WRITES_PERFORMED,
            ],
        ),
    )
    for name, existing_event, fail_mode, expected_trace in invalidation_cases:
        with monkeypatch.context() as failure_patch:
            with make_coherent_transition_fixture_for_test(
                tmp_path / name,
                existing_event=existing_event,
                ready_dependency=not existing_event,
            ) as fixture:
                _patch_clock(failure_patch)
                trace = _capture_resolution_trace(failure_patch)
                cleanup_calls = _record_rollback_and_close(failure_patch)
                if fail_mode == "event-insert":
                    failure_patch.setattr(
                        transaction_module,
                        "_execute_transition_event_insert",
                        lambda *args: (_ for _ in ()).throw(transaction_module._mutation_failed()),
                    )
                failure_patch.setattr(
                    transaction_module,
                    "_invalidate_sqlite_mutation_read_capability",
                    lambda *args, **kwargs: transaction_module._mutation_failed(),
                )

                _run_apply_raises(fixture, "mutation_failed")

                assert trace == expected_trace
                assert state.CAPABILITY_INVALIDATED not in trace
                assert state.ROLLBACK_RESOLVED not in trace
                assert state.CLOSED not in trace
                assert cleanup_calls == ["rollback", "close"]

    with monkeypatch.context() as rollback_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "rollback-failure", ready_dependency=True) as fixture:
            _patch_clock(rollback_patch)
            trace = _capture_resolution_trace(rollback_patch)
            close_calls: list[str] = []
            original_close = transaction_module._close_connection
            rollback_patch.setattr(
                transaction_module,
                "_read_transition_event_max_sequence",
                lambda capability: (_ for _ in ()).throw(transaction_module._mutation_failed()),
            )
            rollback_patch.setattr(
                transaction_module,
                "_rollback_transaction",
                lambda connection: transaction_module._mutation_failed(),
            )

            def close(connection: sqlite3.Connection) -> object:
                close_calls.append("close")
                return original_close(connection)

            rollback_patch.setattr(transaction_module, "_close_connection", close)

            _run_apply_raises(fixture, "mutation_failed")

            assert trace == [
                state.NEW,
                state.TRANSACTION_ACTIVE,
                state.FENCED,
                state.CAPABILITY_ACTIVE,
                state.CAPABILITY_INVALIDATED,
            ]
            assert state.ROLLBACK_RESOLVED not in trace
            assert state.CLOSED not in trace
            assert close_calls == ["close"]

    with monkeypatch.context() as close_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "close-failure", ready_dependency=True) as fixture:
            _patch_clock(close_patch)
            trace = _capture_resolution_trace(close_patch)
            original_close = transaction_module._close_connection
            close_patch.setattr(
                transaction_module,
                "_read_transition_event_max_sequence",
                lambda capability: (_ for _ in ()).throw(transaction_module._mutation_failed()),
            )

            def close_after_rollback(connection: sqlite3.Connection) -> object:
                original_close(connection)
                return transaction_module._mutation_failed()

            close_patch.setattr(transaction_module, "_close_connection", close_after_rollback)

            _run_apply_raises(fixture, "mutation_failed")

            assert trace == [
                state.NEW,
                state.TRANSACTION_ACTIVE,
                state.FENCED,
                state.CAPABILITY_ACTIVE,
                state.CAPABILITY_INVALIDATED,
                state.ROLLBACK_RESOLVED,
            ]
            assert state.CLOSED not in trace


def test_resolution_setter_failures_preserve_cleanup_and_commit_boundaries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = transaction_module._MutationCommitResolutionState

    with monkeypatch.context() as precommit_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "precommit", ready_dependency=True) as fixture:
            _patch_clock(precommit_patch)
            trace = _capture_resolution_trace(precommit_patch, fail_on=(state.CAPABILITY_INVALIDATED,))
            cleanup_calls = _record_rollback_and_close(precommit_patch)
            commit_calls: list[str] = []

            def commit(connection: sqlite3.Connection) -> object:
                commit_calls.append("commit")
                return None

            precommit_patch.setattr(transaction_module, "_commit_transaction", commit)

            _run_apply_raises(fixture, "database_integrity_failure")

            assert trace == [
                state.NEW,
                state.TRANSACTION_ACTIVE,
                state.FENCED,
                state.CAPABILITY_ACTIVE,
                state.PLANNED_OUTCOME,
                state.WRITES_PERFORMED,
            ]
            assert state.CAPABILITY_INVALIDATED not in trace
            assert state.ROLLBACK_RESOLVED not in trace
            assert state.CLOSED not in trace
            assert cleanup_calls == ["rollback", "close"]
            assert commit_calls == []
            assert transition_event_count_for_test(fixture) == 0

    with monkeypatch.context() as success_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "success", ready_dependency=True) as fixture:
            _patch_clock(success_patch)
            trace = _capture_resolution_trace(success_patch, fail_on=(state.COMMIT_SUCCEEDED,))
            rollback_calls: list[str] = []
            close_calls: list[str] = []
            success_patch.setattr(
                transaction_module,
                "_rollback_transaction",
                lambda connection: rollback_calls.append("rollback"),
            )
            original_close = transaction_module._close_connection

            def close(connection: sqlite3.Connection) -> object:
                close_calls.append("close")
                return original_close(connection)

            success_patch.setattr(transaction_module, "_close_connection", close)

            result = _assert_committed(_run_apply(fixture), replayed=False)

            assert result.event.outcome is TransitionEventOutcome.ACCEPTED
            assert trace == [
                state.NEW,
                state.TRANSACTION_ACTIVE,
                state.FENCED,
                state.CAPABILITY_ACTIVE,
                state.PLANNED_OUTCOME,
                state.WRITES_PERFORMED,
                state.CAPABILITY_INVALIDATED,
                state.COMMIT_ATTEMPT_STARTED,
            ]
            assert state.COMMIT_SUCCEEDED not in trace
            assert state.COMMIT_OUTCOME_UNKNOWN not in trace
            assert state.CLOSED not in trace
            assert rollback_calls == []
            assert close_calls == ["close"]
            assert transition_event_count_for_test(fixture) == 1

    with monkeypatch.context() as uncertain_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "uncertain", ready_dependency=True) as fixture:
            _patch_clock(uncertain_patch)
            trace = _capture_resolution_trace(uncertain_patch, fail_on=(state.COMMIT_OUTCOME_UNKNOWN,))
            rollback_calls: list[str] = []
            close_calls: list[str] = []
            uncertain_patch.setattr(
                transaction_module,
                "_rollback_transaction",
                lambda connection: rollback_calls.append("rollback"),
            )
            uncertain_patch.setattr(
                transaction_module,
                "_commit_transaction",
                lambda connection: transaction_module._commit_outcome_unknown(),
            )
            original_close = transaction_module._close_connection

            def close(connection: sqlite3.Connection) -> object:
                close_calls.append("close")
                return original_close(connection)

            uncertain_patch.setattr(transaction_module, "_close_connection", close)

            _run_apply_raises(fixture, "commit_outcome_unknown")

            assert trace == [
                state.NEW,
                state.TRANSACTION_ACTIVE,
                state.FENCED,
                state.CAPABILITY_ACTIVE,
                state.PLANNED_OUTCOME,
                state.WRITES_PERFORMED,
                state.CAPABILITY_INVALIDATED,
                state.COMMIT_ATTEMPT_STARTED,
            ]
            assert state.COMMIT_OUTCOME_UNKNOWN not in trace
            assert state.CLOSED not in trace
            assert rollback_calls == []
            assert close_calls == ["close"]


def test_commit_uncertainty_without_underlying_commit_retries_as_fresh_apply(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, ready_dependency=True) as fixture:
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
        _run_apply_raises(fixture, "commit_outcome_unknown")

        assert rollback_calls == 0
        assert transition_event_count_for_test(fixture) == 0
        assert read_back_fixture_for_test(fixture).work_item.record == fixture.work_item

        monkeypatch.undo()
        _patch_clock(monkeypatch)
        result = _assert_committed(_run_apply(fixture), replayed=False)
        assert result.event.outcome is TransitionEventOutcome.ACCEPTED
        assert tuple(envelope.event_sequence for envelope in _transition_event_envelopes(fixture)) == (0,)


def test_commit_uncertainty_after_underlying_commit_retries_as_exact_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)

        def commit_then_raise(connection: sqlite3.Connection) -> None:
            connection.execute("COMMIT")
            raise RuntimeError(PRIVATE_SENTINEL)

        monkeypatch.setattr(transaction_module, "_commit_transaction", commit_then_raise)
        _run_apply_raises(fixture, "commit_outcome_unknown")

        assert transition_event_count_for_test(fixture) == 1
        committed = _transition_event_envelopes(fixture)[0]
        assert read_back_fixture_for_test(fixture).work_item.record == committed.replay_record

        calls: list[str] = []
        monkeypatch.setattr(transaction_module, "_commit_transaction", lambda connection: None)
        monkeypatch.setattr(transaction_module, "_read_transition_event_max_sequence", lambda *args: calls.append("max"))
        monkeypatch.setattr(transaction_module, "evaluate_transition", lambda *args: calls.append("evaluator"))
        monkeypatch.setattr(transaction_module, "_execute_transition_event_insert", lambda *args: calls.append("insert"))
        replay = _assert_committed(_run_apply(fixture), replayed=True)

        assert replay.event == committed.event
        assert replay.record == committed.replay_record
        assert calls == []
        assert transition_event_count_for_test(fixture) == 1

        changed_digest = _fresh_block_command(
            fixture.command,
            expected_version=fixture.command.expected_version,
            key=fixture.command.idempotency_key,
        )
        conflict = _assert_conflict(_run_apply(fixture, changed_digest), "idempotency_key_reuse_conflict")
        assert conflict.conflict_class == "idempotency_key_reuse_conflict"


def test_close_failure_after_commit_success_or_uncertainty_does_not_change_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = transaction_module._MutationCommitResolutionState

    with monkeypatch.context() as success_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "success", ready_dependency=True) as fixture:
            _patch_clock(success_patch)
            trace = _capture_resolution_trace(success_patch)
            original_close = transaction_module._close_connection

            def close_after_success(connection: sqlite3.Connection) -> object:
                original_close(connection)
                return transaction_module._mutation_failed()

            success_patch.setattr(transaction_module, "_close_connection", close_after_success)
            result = _assert_committed(_run_apply(fixture), replayed=False)
            assert result.event.outcome is TransitionEventOutcome.ACCEPTED
            assert transition_event_count_for_test(fixture) == 1
            assert trace[-1] is state.COMMIT_SUCCEEDED
            assert state.CLOSED not in trace

    with monkeypatch.context() as uncertainty_patch:
        with make_coherent_transition_fixture_for_test(tmp_path / "uncertain", ready_dependency=True) as fixture:
            _patch_clock(uncertainty_patch)
            trace = _capture_resolution_trace(uncertainty_patch)
            original_close = transaction_module._close_connection

            def close_after_uncertainty(connection: sqlite3.Connection) -> object:
                original_close(connection)
                return transaction_module._mutation_failed()

            uncertainty_patch.setattr(
                transaction_module,
                "_commit_transaction",
                lambda connection: transaction_module._commit_outcome_unknown(),
            )
            uncertainty_patch.setattr(transaction_module, "_close_connection", close_after_uncertainty)
            _run_apply_raises(fixture, "commit_outcome_unknown")
            assert transition_event_count_for_test(fixture) == 0
            assert trace[-1] is state.COMMIT_OUTCOME_UNKNOWN
            assert state.CLOSED not in trace


def test_capability_is_invalidated_before_commit_and_expires_after_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        captured: list[object] = []
        original_create = transaction_module._create_sqlite_mutation_read_capability

        def create(**kwargs: object) -> object:
            capability = original_create(**kwargs)
            captured.append(capability)
            return capability

        def assert_expired_before_commit(connection: sqlite3.Connection) -> object:
            with pytest.raises(Exception) as exc_info:
                captured[0]._borrow_connection_for_select()
            assert type(exc_info.value).__name__ == "_MutationReadCapabilityError"
            return None

        monkeypatch.setattr(transaction_module, "_create_sqlite_mutation_read_capability", create)
        monkeypatch.setattr(transaction_module, "_commit_transaction", assert_expired_before_commit)
        _assert_committed(_run_apply(fixture), replayed=False)

        with pytest.raises(Exception) as exc_info:
            captured[0]._borrow_connection_for_select()
        assert type(exc_info.value).__name__ == "_MutationReadCapabilityError"


def test_representative_sql_traces_have_no_hidden_retry_or_b4_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases = (
        ("accepted", True, None, ("INSERT INTO transition_events", "UPDATE work_items", "COMMIT")),
        ("domain", False, None, ("INSERT INTO transition_events", "COMMIT")),
        ("expected", True, "expected", ("ROLLBACK",)),
    )
    for name, ready, mode, required in cases:
        with monkeypatch.context() as trace_patch:
            with make_coherent_transition_fixture_for_test(
                tmp_path / name,
                ready_dependency=ready,
                dependencies_satisfied=True,
            ) as fixture:
                trace_patch.setattr(transaction_module, "_utc_transaction_timestamp", lambda: FIXTURE_TIMESTAMP)
                traced_sql: list[str] = []
                original_open = transaction_module._open_bound_existing_sqlite_connection

                def tracing_open(*args: object, **kwargs: object) -> sqlite3.Connection:
                    connection = original_open(*args, **kwargs)
                    connection.set_trace_callback(traced_sql.append)
                    return connection

                trace_patch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", tracing_open)
                command = (
                    _reissue_command(fixture.command, expected_version=fixture.command.expected_version + 10)
                    if mode == "expected"
                    else fixture.command
                )
                result = _run_apply(fixture, command)
                if mode == "expected":
                    _assert_conflict(result, "expected_version_conflict")
                else:
                    _assert_committed(result, replayed=False)

                normalized = "\n".join(statement.upper() for statement in traced_sql)
                for statement in required:
                    assert statement.upper() in normalized
                assert normalized.count("INSERT INTO TRANSITION_EVENTS") <= 1
                assert normalized.count("UPDATE WORK_ITEMS") <= (1 if ready and mode is None else 0)
                assert "INSERT INTO GLOBAL_STOP_EVENTS" not in normalized
                assert "UPDATE GLOBAL_STOP_CURRENT" not in normalized
                assert "DELETE " not in normalized
                assert "REPLACE " not in normalized


def test_crash_restart_readback_and_retry_after_reacquisition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path, ready_dependency=True) as fixture:
        _patch_clock(monkeypatch)
        result = _assert_committed(_run_apply(fixture), replayed=False)
        location = fixture.location
        fixture.writer_session.close()

        from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session

        restarted = acquire_sqlite_writer_session(location)
        try:
            restarted_fixture = replace(fixture, writer_session=restarted)
            replay = _assert_committed(_run_apply(restarted_fixture), replayed=True)
            assert replay.event == result.event
            assert replay.record == result.record
            assert transition_event_count_for_test(restarted_fixture) == 1
        finally:
            restarted.close()


def test_public_caller_export_state_store_schema_and_b4_boundaries_remain_closed(tmp_path: Path) -> None:
    assert "_run_atomic_transition_apply" not in PACKAGE_EXPORT_PATH.read_text(encoding="utf-8")
    assert "_run_atomic_transition_apply" not in STATE_STORE_PATH.read_text(encoding="utf-8")
    assert not hasattr(ge_nwp_coordinator, "_run_atomic_transition_apply")
    assert not list(MIGRATION_DIR.glob("0002*"))

    writer_source = WRITER_SESSION_PATH.read_text(encoding="utf-8")
    writer_tree = ast.parse(writer_source)
    sqlite_session = next(
        node for node in ast.walk(writer_tree)
        if isinstance(node, ast.ClassDef) and node.name == "_SQLiteWriterSession"
    )
    public_apply = next(
        node for node in sqlite_session.body
        if isinstance(node, ast.FunctionDef) and node.name == "apply_transition"
    )
    public_apply_source = ast.get_source_segment(writer_source, public_apply)
    assert public_apply_source is not None
    assert writer_source.count("_run_atomic_transition_apply") == 2
    assert public_apply_source.count("_run_atomic_transition_apply") == 2
    assert "sqlite_transition_write_contracts" not in writer_source
    assert "sqlite3" not in public_apply_source
    assert "BEGIN" not in public_apply_source
    assert "COMMIT" not in public_apply_source
    assert "ROLLBACK" not in public_apply_source
    assert "_CoordinatorMutationTransactionController" not in public_apply_source
    assert "_create_sqlite_mutation_read_capability" not in public_apply_source
    assert "_read_transition_event_max_sequence" not in public_apply_source
    assert "next_transition_event_sequence" not in public_apply_source
    assert "_transition_write_plan" not in public_apply_source
    assert "_acquire_mutation_lease" not in public_apply_source

    delegate_calls = [
        (class_node.name, function_node.name)
        for class_node in ast.walk(writer_tree)
        if isinstance(class_node, ast.ClassDef)
        for function_node in class_node.body
        if isinstance(function_node, ast.FunctionDef)
        for node in ast.walk(function_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_run_atomic_transition_apply"
    ]
    assert delegate_calls == [("_SQLiteWriterSession", "apply_transition")]
    delegate_call = next(
        node for node in ast.walk(public_apply)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_run_atomic_transition_apply"
    )
    assert delegate_call.args == []
    assert [keyword.arg for keyword in delegate_call.keywords] == [
        "operation_lease",
        "transition_command",
    ]

    production_call_paths = [
        path.name for path in PACKAGE_DIR.glob("*.py")
        if path.name != "sqlite_transition_transaction.py"
        and "_run_atomic_transition_apply" in path.read_text(encoding="utf-8")
    ]
    assert production_call_paths == ["sqlite_writer_session.py"]

    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        with pytest.raises(GlobalStopApplyPreflightError) as exc_info:
            fixture.writer_session.apply_global_stop_update(None, None)  # type: ignore[arg-type]
        assert exc_info.value.reason is GlobalStopApplyPreflightFailureReason.INVALID_COMMAND
        assert transition_event_count_for_test(fixture) == 0
        assert global_stop_event_count_for_test(fixture) == 0


def test_static_one_controller_private_atomic_shape_and_write_contract_consumption() -> None:
    source = TRANSACTION_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    function_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    controller_class = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "_CoordinatorMutationTransactionController"
    )
    setter = next(
        node for node in controller_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "_set_resolution_state"
    )
    constructor = next(
        node for node in controller_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    )
    setter_source = ast.get_source_segment(source, setter)
    assert setter_source is not None

    assert class_names.count("_CoordinatorMutationTransactionController") == 1
    assert "_RollbackOnlyTransitionTransactionController" not in class_names
    assert function_names.count("_set_resolution_state") == 1
    assert function_names.count("_create_sqlite_mutation_read_capability") == 1
    assert "_run_rollback_only_writer_fencing" in function_names
    assert "_run_rollback_only_transition_dry_run" in function_names
    assert "_run_atomic_transition_apply" in function_names
    assert "Callable" not in source
    assert "callback" not in source
    assert "observer" not in source
    assert "raw_connection" not in source
    assert source.count("sqlite_transition_write_contracts") == 1
    assert source.count("sqlite_mutation_transaction_contracts") == 1
    assert source.count("_MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS") == 2
    assert "_TRANSITION_RESOLUTION_ROLLBACK_STATES" not in source
    assert "_read_transition_event_max_sequence" in source
    assert "next_transition_event_sequence" in source
    assert "connection.execute(\"COMMIT\")" in source
    assert "connection.commit(" not in source

    assert any(
        isinstance(node, ast.ImportFrom)
        and node.module == "ge_nwp_coordinator.sqlite_mutation_transaction_contracts"
        and any(alias.name == "_MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS" for alias in node.names)
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(target, ast.Name)
        and target.id == "_MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS"
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
    )
    assert "current_state = self._resolution_state" in setter_source
    assert "type(current_state) is not _MutationCommitResolutionState" in setter_source
    assert "type(state) is not _MutationCommitResolutionState" in setter_source
    assert "if (current_state, state) not in _MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS" in setter_source
    assert setter_source.index(
        "if (current_state, state) not in _MUTATION_COMMIT_RESOLUTION_ALLOWED_TRANSITIONS"
    ) < setter_source.index("self._resolution_state = state")

    def resolution_assignments(function: ast.FunctionDef) -> list[ast.Assign]:
        return [
            node for node in ast.walk(function)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Attribute) and target.attr == "_resolution_state"
                for target in node.targets
            )
        ]

    constructor_assignments = resolution_assignments(constructor)
    setter_assignments = resolution_assignments(setter)
    all_resolution_assignments = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Attribute) and target.attr == "_resolution_state"
            for target in node.targets
        )
    ]
    assert len(constructor_assignments) == 1
    assert len(setter_assignments) == 1
    assert len(all_resolution_assignments) == 2
    assert "self._resolution_state = _MutationCommitResolutionState.NEW" in ast.get_source_segment(
        source,
        constructor_assignments[0],
    )
    assert "self._resolution_state = state" in ast.get_source_segment(source, setter_assignments[0])
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "__setattr__"
        and any(isinstance(arg, ast.Constant) and arg.value == "_resolution_state" for arg in node.args)
        for node in ast.walk(tree)
    )
