from __future__ import annotations

import ast
import os
from pathlib import Path
import sqlite3
import threading
from typing import Any, Callable

import pytest

from b3_coherent_transition_fixture import make_coherent_transition_fixture_for_test
from ge_nwp_coordinator.global_stop import (
    GlobalStopAction,
    GlobalStopCommand,
    GlobalStopEvaluationKind,
    GlobalStopEvent,
    GlobalStopOperatorDecision,
    GlobalStopReasonClass,
    GlobalStopState,
    evaluate_global_stop_update,
)
from ge_nwp_coordinator.persistence_contracts import (
    GLOBAL_STOP_EVENT_ROW_COLUMNS,
    GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_ROW_COLUMNS,
    GlobalStopCurrentRecordEnvelope,
    GlobalStopEventRecordEnvelope,
    GlobalStopOperatorDecisionReceiptEnvelope,
    global_stop_event_canonical_digest,
    global_stop_event_canonical_json,
    global_stop_operator_decision_canonical_digest,
    global_stop_operator_decision_canonical_json,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_global_stop_event_contracts import (
    _B4A_GLOBAL_STOP_QUERY_SPECS,
    _GLOBAL_STOP_CURRENT_SELECT,
    _GLOBAL_STOP_EVENT_IDEMPOTENCY_LOOKUP_SELECT,
    _GLOBAL_STOP_EVENT_MAX_SEQUENCE_SELECT,
    _GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_SELECT,
)
from ge_nwp_coordinator.sqlite_global_stop_readers import (
    _read_global_stop_current,
    _read_global_stop_event_for_idempotency,
    _read_global_stop_event_max_sequence,
    _read_global_stop_operator_decision_receipt,
)
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _TransitionReadCapabilityError,
    _TransitionReadCapabilityFailureReason,
)
import ge_nwp_coordinator.sqlite_transition_transaction as transaction_module
from ge_nwp_coordinator.sqlite_writer_session import _WriterIssuanceMatch


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
MIGRATION_PATH = PACKAGE_DIR / "sqlite_migrations/0001_initial.sql"
READERS_PATH = PACKAGE_DIR / "sqlite_global_stop_readers.py"
TS = "2026-07-22T12:00:03Z"
PRIVATE_SQLITE_SENTINEL = "PRIVATE-B4A-READERS-SQLITE-SENTINEL"


class _SyntheticSQLiteError(sqlite3.DatabaseError):
    def __init__(self, sqlite_errorcode: int | None = None) -> None:
        super().__init__(PRIVATE_SQLITE_SENTINEL)
        if sqlite_errorcode is not None:
            self.sqlite_errorcode = sqlite_errorcode


class _ScriptedCursor:
    def __init__(
        self,
        rows: tuple[object, ...] = (),
        *,
        fetch_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self._rows = rows
        self._fetch_error = fetch_error
        self._close_error = close_error
        self.fetchmany_sizes: list[int] = []
        self.close_count = 0

    def fetchmany(self, size: int) -> list[object]:
        self.fetchmany_sizes.append(size)
        if self._fetch_error is not None:
            raise self._fetch_error
        return list(self._rows[:size])

    def close(self) -> None:
        self.close_count += 1
        if self._close_error is not None:
            raise self._close_error


class _RecordingConnection(sqlite3.Connection):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.execute_calls: list[tuple[str, tuple[object, ...]]] = []
        self.scripted_cursor: _ScriptedCursor | None = None
        self.scripted_execute_error: BaseException | None = None

    def execute(self, sql: str, parameters: Any = (), /) -> Any:
        parameter_tuple = tuple(parameters) if parameters is not None else ()
        self.execute_calls.append((sql, parameter_tuple))
        if self.scripted_execute_error is not None:
            raise self.scripted_execute_error
        if self.scripted_cursor is not None:
            return self.scripted_cursor
        return super().execute(sql, parameters)


class _TestsOnlyCapability:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._active = True
        self._pid = os.getpid()
        self._thread = threading.get_ident()

    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        if os.getpid() != self._pid:
            raise _TransitionReadCapabilityError(_TransitionReadCapabilityFailureReason.PROCESS_MISMATCH)
        if threading.get_ident() != self._thread:
            raise _TransitionReadCapabilityError(_TransitionReadCapabilityFailureReason.THREAD_MISMATCH)
        if not self._active or not self._connection.in_transaction:
            raise _TransitionReadCapabilityError(_TransitionReadCapabilityFailureReason.CAPABILITY_EXPIRED)
        return self._connection

    def expire(self) -> None:
        self._active = False


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:", isolation_level=None)
    connection.executescript(MIGRATION_PATH.read_text(encoding="utf-8"))
    connection.execute("BEGIN IMMEDIATE")
    return connection


def _cleanup(connection: sqlite3.Connection) -> None:
    try:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
    finally:
        connection.close()


def _decision(*, authorized: bool = True) -> GlobalStopOperatorDecision:
    return GlobalStopOperatorDecision(
        decision_ref="operator-decision-1",
        authorized=authorized,
        reason="accepted" if authorized else "operator_authorization_required",
    )


def _command() -> GlobalStopCommand:
    return GlobalStopCommand.create(
        action=GlobalStopAction.ACTIVATE,
        idempotency_key="global-stop-key-1",
        expected_version=0,
        stop_id="global-stop-1",
        reason_class=GlobalStopReasonClass.OPERATOR_STOP,
        issuer_ref="operator-policy",
        issued_at="2026-07-22T12:00:00Z",
        operator_decision_ref="operator-decision-1",
    )


def _receipt_row(decision: GlobalStopOperatorDecision) -> dict[str, object]:
    return {
        "decision_ref": decision.decision_ref,
        "authorized": 1 if decision.authorized else 0,
        "reason": decision.reason,
        "schema_id": decision.schema_id,
        "canonical_json": global_stop_operator_decision_canonical_json(decision),
        "canonical_digest": global_stop_operator_decision_canonical_digest(decision),
        "created_at": TS,
    }


def _event_row() -> dict[str, object]:
    state = GlobalStopState()
    command = _command()
    evaluation = evaluate_global_stop_update(state, command, _decision())
    assert evaluation.kind is GlobalStopEvaluationKind.ACCEPTED
    event = evaluation.event
    assert type(event) is GlobalStopEvent
    return {
        "event_ref": event.event_ref,
        "event_sequence": 0,
        "idempotency_key": event.idempotency_key,
        "command_digest": event.command_digest,
        "action": event.action.value,
        "source_version": event.source_version,
        "resulting_version": event.resulting_version,
        "outcome": event.outcome.value,
        "reason": event.reason,
        "operator_decision_ref": event.operator_decision_ref,
        "resulting_global_stop_ref": event.resulting_global_stop_ref,
        "resulting_status": event.resulting_status.value,
        "schema_id": event.schema_id,
        "event_json": global_stop_event_canonical_json(event),
        "event_digest": global_stop_event_canonical_digest(event),
        "replay_global_stop_json": evaluation.state.canonical_json(),
        "replay_global_stop_digest": evaluation.state.canonical_digest(),
        "created_at": TS,
    }


def _insert_row(connection: sqlite3.Connection, table: str, row: dict[str, object], columns: tuple[str, ...]) -> None:
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})"
    connection.execute(sql, tuple(row[column] for column in columns))


def _row_tuple(row: dict[str, object], columns: tuple[str, ...]) -> tuple[object, ...]:
    return tuple(row[column] for column in columns)


def _assert_store_error(exc: pytest.ExceptionInfo[SQLiteMutationStoreError], error_class: str) -> None:
    assert exc.value.error_class == error_class
    assert PRIVATE_SQLITE_SENTINEL not in repr(exc.value)
    assert exc.value.internal_detail is None


def _run_real_controller_with_probe(session: object, monkeypatch: pytest.MonkeyPatch, probe: Callable[[object], None]) -> object:
    original_create = transaction_module._create_sqlite_transition_read_capability
    captured: list[object] = []

    def capture_create(**kwargs: object) -> object:
        capability = original_create(**kwargs)
        captured.append(capability)
        probe(capability)
        return capability

    monkeypatch.setattr(transaction_module, "_create_sqlite_transition_read_capability", capture_create)
    with session._resource.operation_guard(session) as operation:
        result = transaction_module._run_rollback_only_writer_fencing(operation_lease=operation)
    assert result is _WriterIssuanceMatch.MATCH
    assert len(captured) == 1
    return captured[0]


def test_query_specs_are_explicit_immutable_and_table_local() -> None:
    assert _B4A_GLOBAL_STOP_QUERY_SPECS == (
        _GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_SELECT,
        _GLOBAL_STOP_EVENT_IDEMPOTENCY_LOOKUP_SELECT,
        _GLOBAL_STOP_EVENT_MAX_SEQUENCE_SELECT,
        _GLOBAL_STOP_CURRENT_SELECT,
    )
    assert _GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_SELECT.sql.endswith("LIMIT 2")
    assert _GLOBAL_STOP_EVENT_IDEMPOTENCY_LOOKUP_SELECT.sql.endswith("LIMIT 2")
    assert _GLOBAL_STOP_CURRENT_SELECT.sql.endswith("LIMIT 2")
    assert _GLOBAL_STOP_EVENT_MAX_SEQUENCE_SELECT.sql == "SELECT MAX(event_sequence)\nFROM global_stop_events"
    for spec in (
        _GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_SELECT,
        _GLOBAL_STOP_EVENT_IDEMPOTENCY_LOOKUP_SELECT,
        _GLOBAL_STOP_CURRENT_SELECT,
    ):
        assert "SELECT *" not in spec.sql
        assert spec.sql.count("?") == 1
        assert not spec.sql.endswith(";")
        with pytest.raises(Exception):
            spec.sql = "changed"  # type: ignore[misc]


def test_readers_find_missing_and_current_rows_without_mutating() -> None:
    connection = _connection()
    try:
        capability = _TestsOnlyCapability(connection)
        decision = _decision()
        receipt = _receipt_row(decision)
        event = _event_row()
        _insert_row(
            connection,
            "global_stop_operator_decision_receipts",
            receipt,
            GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_ROW_COLUMNS,
        )
        _insert_row(connection, "global_stop_events", event, GLOBAL_STOP_EVENT_ROW_COLUMNS)

        assert _read_global_stop_operator_decision_receipt(capability, "missing") is None
        found_receipt = _read_global_stop_operator_decision_receipt(capability, decision.decision_ref)
        assert type(found_receipt) is GlobalStopOperatorDecisionReceiptEnvelope
        assert found_receipt.decision == decision

        assert _read_global_stop_event_for_idempotency(capability, "missing-key") is None
        found_event = _read_global_stop_event_for_idempotency(capability, "global-stop-key-1")
        assert type(found_event) is GlobalStopEventRecordEnvelope
        assert found_event.event_sequence == 0
        assert _read_global_stop_event_max_sequence(capability) == 0

        current = _read_global_stop_current(capability)
        assert type(current) is GlobalStopCurrentRecordEnvelope
        assert current.state == GlobalStopState()
        assert connection.in_transaction is True
    finally:
        _cleanup(connection)


def test_readers_reject_malformed_lookup_types_rows_and_max_sequence_values() -> None:
    connection = _connection()
    try:
        capability = _TestsOnlyCapability(connection)
        with pytest.raises(ValueError):
            _read_global_stop_operator_decision_receipt(capability, b"operator-decision-1")  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            _read_global_stop_event_for_idempotency(capability, b"global-stop-key-1")  # type: ignore[arg-type]
    finally:
        _cleanup(connection)

    recording = sqlite3.connect(":memory:", factory=_RecordingConnection)
    try:
        capability = _TestsOnlyCapability(recording)
        recording.execute("BEGIN IMMEDIATE")
        bad_receipt = {**_receipt_row(_decision()), "authorized": True}
        recording.scripted_cursor = _ScriptedCursor(
            rows=(_row_tuple(bad_receipt, GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_ROW_COLUMNS),)
        )
        with pytest.raises(SQLiteMutationStoreError) as malformed_receipt:
            _read_global_stop_operator_decision_receipt(capability, "operator-decision-1")
        _assert_store_error(malformed_receipt, "database_integrity_failure")

        recording.scripted_cursor = _ScriptedCursor(rows=((True,),))
        with pytest.raises(SQLiteMutationStoreError) as malformed_max:
            _read_global_stop_event_max_sequence(capability)
        _assert_store_error(malformed_max, "database_integrity_failure")
    finally:
        _cleanup(recording)


def test_readers_enforce_bounded_cardinality_and_cursor_error_precedence() -> None:
    recording = sqlite3.connect(":memory:", factory=_RecordingConnection)
    try:
        capability = _TestsOnlyCapability(recording)
        recording.execute("BEGIN IMMEDIATE")
        receipt_tuple = _row_tuple(_receipt_row(_decision()), GLOBAL_STOP_OPERATOR_DECISION_RECEIPT_ROW_COLUMNS)
        recording.scripted_cursor = _ScriptedCursor(rows=(receipt_tuple, receipt_tuple))
        with pytest.raises(SQLiteMutationStoreError) as multiple:
            _read_global_stop_operator_decision_receipt(capability, "operator-decision-1")
        _assert_store_error(multiple, "database_integrity_failure")
        assert recording.scripted_cursor.fetchmany_sizes == [2]
        assert recording.scripted_cursor.close_count == 1

        recording.scripted_cursor = _ScriptedCursor(
            rows=(receipt_tuple,),
            close_error=_SyntheticSQLiteError(),
        )
        with pytest.raises(SQLiteMutationStoreError) as close_failure:
            _read_global_stop_operator_decision_receipt(capability, "operator-decision-1")
        _assert_store_error(close_failure, "mutation_failed")

        recording.scripted_cursor = _ScriptedCursor(
            rows=(receipt_tuple,),
            fetch_error=_SyntheticSQLiteError(getattr(sqlite3, "SQLITE_CORRUPT", 11)),
            close_error=_SyntheticSQLiteError(),
        )
        with pytest.raises(SQLiteMutationStoreError) as fetch_failure:
            _read_global_stop_operator_decision_receipt(capability, "operator-decision-1")
        _assert_store_error(fetch_failure, "database_integrity_failure")
    finally:
        _cleanup(recording)


def test_real_nominal_capability_reads_current_and_expires(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        summary: dict[str, object] = {}

        def probe(capability: object) -> None:
            summary["current"] = _read_global_stop_current(capability)  # type: ignore[arg-type]
            summary["max"] = _read_global_stop_event_max_sequence(capability)  # type: ignore[arg-type]

        capability = _run_real_controller_with_probe(fixture.writer_session, monkeypatch, probe)
        assert type(summary["current"]) is GlobalStopCurrentRecordEnvelope
        assert summary["max"] is None
        with pytest.raises(_TransitionReadCapabilityError) as expired:
            _read_global_stop_event_max_sequence(capability)  # type: ignore[arg-type]
        assert expired.value.reason is _TransitionReadCapabilityFailureReason.CAPABILITY_EXPIRED


def test_reader_module_has_no_runtime_caller_or_mutation_sql() -> None:
    source = READERS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert "commit" not in source
    assert "rollback" not in source
    assert "INSERT" not in source
    assert "UPDATE" not in source
    assert "DELETE" not in source
    assert "sqlite3.connect" not in source
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            assert not node.name.startswith("read_")

    writer_source = (PACKAGE_DIR / "sqlite_writer_session.py").read_text(encoding="utf-8")
    transaction_source = (PACKAGE_DIR / "sqlite_transition_transaction.py").read_text(encoding="utf-8")
    assert "_read_global_stop_event_for_idempotency" not in writer_source
    assert "_read_global_stop_operator_decision_receipt" not in writer_source
    assert "_read_global_stop_event_for_idempotency" not in transaction_source
    assert "_read_global_stop_operator_decision_receipt" not in transaction_source
