from __future__ import annotations

import ast
import inspect
import os
from pathlib import Path
import sqlite3
import threading

import pytest

import ge_nwp_coordinator
from ge_nwp_coordinator import StateStore
from ge_nwp_coordinator.persistence_contracts import (
    ADMITTED_BACKLOG_ROW_COLUMNS,
    ADMITTED_BACKLOG_ROW_KEYS,
    AUTHORIZATION_RECEIPT_KEYS,
    AUTHORIZATION_RECEIPT_ROW_COLUMNS,
    AUTHORIZATION_RECEIPT_ROW_KEYS,
    DEPENDENCY_RECEIPT_KEYS,
    DEPENDENCY_RECEIPT_ROW_COLUMNS,
    DEPENDENCY_RECEIPT_ROW_KEYS,
    GLOBAL_STOP_CURRENT_ROW_COLUMNS,
    GLOBAL_STOP_CURRENT_ROW_KEYS,
    LEASE_IDENTITY_RECORD_KEYS,
    LEASE_IDENTITY_RECORD_ROW_COLUMNS,
    LEASE_IDENTITY_RECORD_ROW_KEYS,
    WORK_ITEM_ROW_COLUMNS,
    WORK_ITEM_ROW_KEYS,
)
from ge_nwp_coordinator import sqlite_transition_read_scope as read_scope
from ge_nwp_coordinator.sqlite_transition_read_scope import (
    _ADMITTED_BACKLOG_SELECT,
    _AUTHORIZATION_RECEIPT_SELECT,
    _B3B2A_SELECT_QUERY_SPECS,
    _CURRENT_WORK_ITEM_SELECT,
    _DEPENDENCY_RECEIPT_SELECT,
    _GLOBAL_STOP_CURRENT_SELECT,
    _LEASE_IDENTITY_SELECT,
    _SelectQuerySpec,
    _read_admitted_backlog,
    _read_authorization_receipt,
    _read_current_work_item,
    _read_dependency_receipt,
    _read_global_stop_current,
    _read_lease_identity_record,
)
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _MutationReadCapability,
    _MutationReadCapabilityError,
    _MutationReadCapabilityFailureReason,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "src/ge_nwp_coordinator"
READ_SCOPE_PATH = PACKAGE_DIR / "sqlite_transition_read_scope.py"
SELECT_SUPPORT_PATH = PACKAGE_DIR / "sqlite_transition_select_support.py"


def _imports_sqlite3(source: str, *, filename: str) -> bool:
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name == "sqlite3" or alias.name.startswith("sqlite3.")
            for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and node.level == 0 and (
            node.module == "sqlite3"
            or (node.module or "").startswith("sqlite3.")
        ):
            return True
    return False


EXPECTED_ROW_COLUMNS = {
    "lease_identity_records": (
        "decision_ref",
        "lease_ref",
        "identity_valid",
        "lease_digest",
        "schema_id",
        "canonical_json",
        "canonical_digest",
        "created_at",
    ),
    "authorization_decision_receipts": (
        "decision_ref",
        "lease_ref",
        "lease_identity_decision_ref",
        "lease_identity_valid",
        "authorization_model",
        "authorized",
        "executable",
        "reason",
        "schema_id",
        "canonical_json",
        "canonical_digest",
        "created_at",
    ),
    "dependency_decision_receipts": (
        "decision_ref",
        "work_item_id",
        "dependencies_satisfied",
        "reason",
        "schema_id",
        "canonical_json",
        "canonical_digest",
        "created_at",
    ),
    "work_items": (
        "work_item_id",
        "lease_id",
        "backlog_id",
        "schema_id",
        "state",
        "version",
        "attempt_count",
        "repair_count",
        "budget_consumed",
        "budget_limit",
        "max_attempts",
        "max_repairs",
        "cleanup_required",
        "updated_at",
    ),
    "admitted_backlogs": (
        "backlog_id",
        "lease_ref",
        "schema_id",
        "schema_version",
        "content_digest",
        "canonical_json",
        "admitted_at",
    ),
    "global_stop_current": (
        "singleton_id",
        "schema_id",
        "version",
        "active",
        "stop_id",
        "reason_class",
        "issuer_ref",
        "issued_at",
        "operator_decision_ref",
        "updated_at",
    ),
}

QUERY_CONTRACTS = (
    (_CURRENT_WORK_ITEM_SELECT, "work_items", "work_item_id", WORK_ITEM_ROW_COLUMNS),
    (_LEASE_IDENTITY_SELECT, "lease_identity_records", "decision_ref", LEASE_IDENTITY_RECORD_ROW_COLUMNS),
    (
        _AUTHORIZATION_RECEIPT_SELECT,
        "authorization_decision_receipts",
        "decision_ref",
        AUTHORIZATION_RECEIPT_ROW_COLUMNS,
    ),
    (_DEPENDENCY_RECEIPT_SELECT, "dependency_decision_receipts", "decision_ref", DEPENDENCY_RECEIPT_ROW_COLUMNS),
    (_ADMITTED_BACKLOG_SELECT, "admitted_backlogs", "backlog_id", ADMITTED_BACKLOG_ROW_COLUMNS),
    (_GLOBAL_STOP_CURRENT_SELECT, "global_stop_current", "singleton_id", GLOBAL_STOP_CURRENT_ROW_COLUMNS),
)


def _active_explicit_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:", isolation_level=None)
    connection.execute("BEGIN IMMEDIATE")
    return connection


def _cleanup_connection(connection: sqlite3.Connection) -> None:
    try:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
    finally:
        connection.close()


class _TestOnlyB3cTransactionCapability:
    """Tests the future B3c lifecycle contract without adding production authority."""

    __slots__ = ("_connection", "_epoch_marker", "_active", "_owner_process_id", "_owner_thread_id")

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._epoch_marker = object()
        self._active = True
        self._owner_process_id = os.getpid()
        self._owner_thread_id = threading.get_ident()

    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        if os.getpid() != self._owner_process_id:
            raise _MutationReadCapabilityError(_MutationReadCapabilityFailureReason.PROCESS_MISMATCH)
        if threading.get_ident() != self._owner_thread_id:
            raise _MutationReadCapabilityError(_MutationReadCapabilityFailureReason.THREAD_MISMATCH)
        if not self._active or not self._connection.in_transaction:
            raise _MutationReadCapabilityError(_MutationReadCapabilityFailureReason.CAPABILITY_EXPIRED)
        return self._connection

    def _invalidate_before_transaction_end_for_test(self) -> None:
        self._active = False


def _assert_safe_capability_error(
    exc_info: pytest.ExceptionInfo[_MutationReadCapabilityError],
    reason: str,
) -> None:
    assert exc_info.value.reason.value == reason
    assert str(exc_info.value) == reason
    assert exc_info.value.args == (reason,)
    assert "Connection" not in repr(exc_info.value)
    assert ":memory:" not in repr(exc_info.value)
    assert "epoch" not in repr(exc_info.value).lower()
    assert "0x" not in repr(exc_info.value)


def _parsed_contract_sql(sql: str) -> tuple[tuple[str, ...], str, str]:
    lines = sql.splitlines()
    assert len(lines) == 4
    assert lines[0].startswith("SELECT ")
    assert lines[1].startswith("FROM ")
    assert lines[2].startswith("WHERE ")
    assert lines[3] == "LIMIT 2"
    columns = tuple(part.strip() for part in lines[0].removeprefix("SELECT ").split(","))
    table = lines[1].removeprefix("FROM ")
    where = lines[2].removeprefix("WHERE ")
    lookup_column, equals, placeholder = where.split()
    assert equals == "="
    assert placeholder == "?"
    return columns, table, lookup_column


def test_ordered_row_columns_are_single_source_for_existing_key_sets() -> None:
    assert LEASE_IDENTITY_RECORD_ROW_COLUMNS == EXPECTED_ROW_COLUMNS["lease_identity_records"]
    assert AUTHORIZATION_RECEIPT_ROW_COLUMNS == EXPECTED_ROW_COLUMNS["authorization_decision_receipts"]
    assert DEPENDENCY_RECEIPT_ROW_COLUMNS == EXPECTED_ROW_COLUMNS["dependency_decision_receipts"]
    assert WORK_ITEM_ROW_COLUMNS == EXPECTED_ROW_COLUMNS["work_items"]
    assert ADMITTED_BACKLOG_ROW_COLUMNS == EXPECTED_ROW_COLUMNS["admitted_backlogs"]
    assert GLOBAL_STOP_CURRENT_ROW_COLUMNS == EXPECTED_ROW_COLUMNS["global_stop_current"]

    assert LEASE_IDENTITY_RECORD_ROW_KEYS == frozenset(LEASE_IDENTITY_RECORD_ROW_COLUMNS)
    assert LEASE_IDENTITY_RECORD_KEYS == frozenset(LEASE_IDENTITY_RECORD_ROW_COLUMNS[:-1])
    assert AUTHORIZATION_RECEIPT_ROW_KEYS == frozenset(AUTHORIZATION_RECEIPT_ROW_COLUMNS)
    assert AUTHORIZATION_RECEIPT_KEYS == frozenset(AUTHORIZATION_RECEIPT_ROW_COLUMNS[:-1])
    assert DEPENDENCY_RECEIPT_ROW_KEYS == frozenset(DEPENDENCY_RECEIPT_ROW_COLUMNS)
    assert DEPENDENCY_RECEIPT_KEYS == frozenset(DEPENDENCY_RECEIPT_ROW_COLUMNS[:-1])
    assert WORK_ITEM_ROW_KEYS == frozenset(WORK_ITEM_ROW_COLUMNS)
    assert ADMITTED_BACKLOG_ROW_KEYS == frozenset(ADMITTED_BACKLOG_ROW_COLUMNS)
    assert GLOBAL_STOP_CURRENT_ROW_KEYS == frozenset(GLOBAL_STOP_CURRENT_ROW_COLUMNS)


def test_ordered_row_columns_are_safe_nonempty_unique_string_tuples() -> None:
    for columns in EXPECTED_ROW_COLUMNS.values():
        assert type(columns) is tuple
        assert columns
        assert len(columns) == len(set(columns))
        for column in columns:
            assert type(column) is str
            assert column
            assert column[0].islower()
            assert set(column) <= set("abcdefghijklmnopqrstuvwxyz0123456789_")


def test_private_transition_read_capability_is_protocol_only() -> None:
    source = SELECT_SUPPORT_PATH.read_text(encoding="utf-8")
    assert getattr(_MutationReadCapability, "_is_protocol", False) is True
    assert getattr(_MutationReadCapability, "_is_runtime_protocol", False) is False
    assert "_borrow_connection_for_select" in _MutationReadCapability.__dict__
    tree = ast.parse(source)
    protocol = next(node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "_MutationReadCapability")
    assert not any(isinstance(node, ast.FunctionDef) and node.name == "__init__" for node in protocol.body)
    assert "class _TransitionReadScope" not in source
    assert "_create_for_b3c_managed_transition_transaction" not in source
    assert "_require_connection_posture" not in source
    assert "_current_process_id" not in source
    assert "_current_thread_id" not in source
    assert "runtime_checkable" not in source


def test_b3b2b_private_reader_signatures_are_capability_bound() -> None:
    expected = {
        "_read_current_work_item": ("work_item_id", "WorkItemRecordEnvelope | None"),
        "_read_lease_identity_record": ("decision_ref", "LeaseIdentityRecordEnvelope | None"),
        "_read_authorization_receipt": ("decision_ref", "AuthorizationReceiptEnvelope | None"),
        "_read_dependency_receipt": ("decision_ref", "DependencyReceiptEnvelope | None"),
        "_read_admitted_backlog": ("backlog_id", "AdmittedBacklogRecordEnvelope | None"),
        "_read_global_stop_current": (None, "GlobalStopCurrentRecordEnvelope"),
    }
    readers = {
        "_read_current_work_item": _read_current_work_item,
        "_read_lease_identity_record": _read_lease_identity_record,
        "_read_authorization_receipt": _read_authorization_receipt,
        "_read_dependency_receipt": _read_dependency_receipt,
        "_read_admitted_backlog": _read_admitted_backlog,
        "_read_global_stop_current": _read_global_stop_current,
    }
    assert set(readers) == set(expected)
    for reader_name, reader in readers.items():
        signature = inspect.signature(reader)
        parameters = list(signature.parameters.values())
        assert parameters[0].name == "capability"
        assert parameters[0].annotation == "_MutationReadCapability"
        lookup_parameter, return_type = expected[reader_name]
        if lookup_parameter is None:
            assert [parameter.name for parameter in parameters] == ["capability"]
        else:
            assert [parameter.name for parameter in parameters] == ["capability", lookup_parameter]
            assert parameters[1].annotation == "str"
        assert signature.return_annotation == return_type

    source = READ_SCOPE_PATH.read_text(encoding="utf-8")
    assert "_FutureReaderSignatureSpec" not in source
    assert "_FUTURE_B3B2B_READER_SIGNATURES" not in source
    for forbidden in ("StateStore", "WriterSession", "database_path"):
        assert forbidden not in "\n".join(inspect.getsource(reader) for reader in readers.values())


def test_test_only_capability_rejects_transaction_a_reuse_after_transaction_b_starts() -> None:
    connection = _active_explicit_connection()
    try:
        capability_a = _TestOnlyB3cTransactionCapability(connection)
        assert capability_a._borrow_connection_for_select() is connection

        capability_a._invalidate_before_transaction_end_for_test()
        connection.execute("ROLLBACK")
        connection.execute("BEGIN IMMEDIATE")

        with pytest.raises(_MutationReadCapabilityError) as old_capability:
            capability_a._borrow_connection_for_select()
        _assert_safe_capability_error(old_capability, "mutation_read_capability_expired")

        capability_b = _TestOnlyB3cTransactionCapability(connection)
        assert capability_b._borrow_connection_for_select() is connection
    finally:
        _cleanup_connection(connection)


def test_invalidated_test_capability_stays_invalid_after_posture_restore_and_restart() -> None:
    connection = _active_explicit_connection()
    try:
        capability = _TestOnlyB3cTransactionCapability(connection)
        capability._invalidate_before_transaction_end_for_test()
        connection.execute("ROLLBACK")
        connection.row_factory = sqlite3.Row
        connection.row_factory = None
        connection.text_factory = bytes
        connection.text_factory = str
        connection.isolation_level = ""
        connection.isolation_level = None
        connection.execute("BEGIN IMMEDIATE")

        with pytest.raises(_MutationReadCapabilityError) as exc_info:
            capability._borrow_connection_for_select()
        _assert_safe_capability_error(exc_info, "mutation_read_capability_expired")
    finally:
        _cleanup_connection(connection)


def test_test_only_capability_rejects_after_transaction_end_without_restart() -> None:
    connection = _active_explicit_connection()
    try:
        capability = _TestOnlyB3cTransactionCapability(connection)
        capability._invalidate_before_transaction_end_for_test()
        connection.execute("ROLLBACK")

        with pytest.raises(_MutationReadCapabilityError) as exc_info:
            capability._borrow_connection_for_select()
        _assert_safe_capability_error(exc_info, "mutation_read_capability_expired")
    finally:
        connection.close()


def test_test_only_capability_rejects_thread_and_process_mismatch_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = _active_explicit_connection()
    try:
        capability = _TestOnlyB3cTransactionCapability(connection)
        reasons: list[_MutationReadCapabilityFailureReason] = []

        def borrow_in_another_thread() -> None:
            try:
                capability._borrow_connection_for_select()
            except _MutationReadCapabilityError as exc:
                reasons.append(exc.reason)

        thread = threading.Thread(target=borrow_in_another_thread)
        thread.start()
        thread.join(timeout=5)
        assert not thread.is_alive()
        assert reasons == [_MutationReadCapabilityFailureReason.THREAD_MISMATCH]

        monkeypatch.setattr(os, "getpid", lambda: capability._owner_process_id + 1)
        with pytest.raises(_MutationReadCapabilityError) as exc_info:
            capability._borrow_connection_for_select()
        _assert_safe_capability_error(exc_info, "process_mismatch")
    finally:
        _cleanup_connection(connection)


def test_test_only_capability_borrow_does_not_mutate_connection_lifecycle_or_posture() -> None:
    connection = _active_explicit_connection()
    try:
        capability = _TestOnlyB3cTransactionCapability(connection)
        before = (
            connection.isolation_level,
            connection.row_factory,
            connection.text_factory,
            connection.in_transaction,
        )
        assert capability._borrow_connection_for_select() is connection
        after = (
            connection.isolation_level,
            connection.row_factory,
            connection.text_factory,
            connection.in_transaction,
        )
        assert after == before
    finally:
        _cleanup_connection(connection)


def test_query_specs_are_immutable_parameterized_select_contracts() -> None:
    assert _B3B2A_SELECT_QUERY_SPECS == tuple(spec for spec, *_ in QUERY_CONTRACTS)
    assert len(_B3B2A_SELECT_QUERY_SPECS) == 6
    assert len({spec.query_id for spec in _B3B2A_SELECT_QUERY_SPECS}) == 6

    for spec, table_name, lookup_column, columns in QUERY_CONTRACTS:
        if table_name == "global_stop_current":
            assert type(spec).__name__ == "_GlobalStopSelectQuerySpec"
        else:
            assert isinstance(spec, _SelectQuerySpec)
        assert spec.table_name == table_name
        assert spec.lookup_column == lookup_column
        assert spec.columns == columns
        assert len(spec.columns) == len(set(spec.columns))
        assert spec.sql == f"SELECT {', '.join(columns)}\nFROM {table_name}\nWHERE {lookup_column} = ?\nLIMIT 2"

        parsed_columns, parsed_table, parsed_lookup = _parsed_contract_sql(spec.sql)
        assert parsed_columns == columns
        assert parsed_table == table_name
        assert parsed_lookup == lookup_column

        assert "SELECT *" not in spec.sql
        assert "JOIN" not in spec.sql.upper().split()
        assert "(" not in spec.sql
        assert ")" not in spec.sql
        assert spec.sql.count("?") == 1
        assert not spec.sql.endswith(";")
        for forbidden_table in (
            "transition_events",
            "global_stop_events",
            "schema_migrations",
            "writer_ownership",
            "global_stop_operator_decision_receipts",
        ):
            assert forbidden_table not in spec.sql
        for forbidden_token in (
            "INSERT",
            "UPDATE",
            "DELETE",
            "CREATE",
            "ALTER",
            "DROP",
            "BEGIN",
            "COMMIT",
            "ROLLBACK",
            "PRAGMA",
            "EXECUTE",
            "IDEMPOTENCY",
            "REPLAY",
        ):
            assert forbidden_token not in spec.sql.upper().split()

        with pytest.raises(Exception):
            spec.table_name = "changed"  # type: ignore[misc]


def test_query_spec_type_and_constants_remain_internal_and_unexported() -> None:
    assert not hasattr(read_scope, "__all__")
    for name in (
        "_SelectQuerySpec",
        "_CURRENT_WORK_ITEM_SELECT",
        "_LEASE_IDENTITY_SELECT",
        "_AUTHORIZATION_RECEIPT_SELECT",
        "_DEPENDENCY_RECEIPT_SELECT",
        "_ADMITTED_BACKLOG_SELECT",
        "_GLOBAL_STOP_CURRENT_SELECT",
        "_B3B2A_SELECT_QUERY_SPECS",
        "_read_current_work_item",
        "_read_lease_identity_record",
        "_read_authorization_receipt",
        "_read_dependency_receipt",
        "_read_admitted_backlog",
        "_read_global_stop_current",
    ):
        assert name not in ge_nwp_coordinator.__all__
        assert not hasattr(ge_nwp_coordinator, name)
    for name in (
        "_MutationReadCapability",
        "_MutationReadCapabilityError",
        "_MutationReadCapabilityFailureReason",
    ):
        assert name not in ge_nwp_coordinator.__all__
        assert not hasattr(ge_nwp_coordinator, name)


def test_b3b2a_does_not_widen_public_state_store_or_add_observer_apis() -> None:
    assert list(inspect.signature(StateStore.read_current).parameters) == ["self", "work_item_id"]
    assert list(inspect.signature(StateStore.read_global_stop).parameters) == ["self"]
    for forbidden in (
        "read_lease_identity",
        "read_authorization_receipt",
        "read_dependency_receipt",
        "read_admitted_backlog",
        "read_transition_event",
        "read_replay",
        "lookup_idempotency",
        "transition_read_scope",
    ):
        assert not hasattr(StateStore, forbidden)

    state_store_source = (PACKAGE_DIR / "state_store.py").read_text(encoding="utf-8")
    assert "sqlite_transition_read_scope" not in state_store_source


def test_b3b2b_production_module_only_adds_private_bounded_select_readers() -> None:
    source = READ_SCOPE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_calls = {
        "executemany",
        "executescript",
        "cursor",
        "fetchone",
        "fetchall",
        "commit",
        "rollback",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls
            elif isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls

    function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert {
        "_read_current_work_item",
        "_read_lease_identity_record",
        "_read_authorization_receipt",
        "_read_dependency_receipt",
        "_read_admitted_backlog",
    } <= function_names
    assert "from ge_nwp_coordinator.sqlite_global_stop_readers import _read_global_stop_current" in source
    assert not any(name.startswith("read_") for name in function_names)
    assert "_borrow_connection_for_select" not in function_names

    for forbidden in (
        "class _TransitionReadScope",
        "_create_for_b3c_managed_transition_transaction",
        "_borrow_connection_for_b3b2b",
        "_require_connection_posture",
        "work_item_record_from_row",
        "validate_b3_work_item_authority_binding",
        "TransitionContext",
        "TransitionConflict",
        "row_to_mapping",
        "sqlite3.connect",
        "connection.close",
        "database_path",
        "idempotency_key",
        "event_sequence",
        "expected_version",
    ):
        assert forbidden not in source


def test_b3b2a_runtime_import_is_the_only_new_sqlite_importer() -> None:
    source_files = list((ROOT / "src").rglob("*.py"))
    sources = {
        path.relative_to(ROOT).as_posix(): path.read_text(encoding="utf-8")
        for path in source_files
    }
    expected_sqlite_importers = {
        "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py",
        "src/ge_nwp_coordinator/sqlite_connection.py",
        "src/ge_nwp_coordinator/sqlite_migration.py",
        "src/ge_nwp_coordinator/sqlite_transition_select_support.py",
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "src/ge_nwp_coordinator/sqlite_writer_session.py",
    }
    sqlite_importers = {
        relative_path
        for relative_path, source in sources.items()
        if _imports_sqlite3(source, filename=relative_path)
    }
    assert sqlite_importers == expected_sqlite_importers

    challenge_sources = (
        ("import sqlite3\n", True),
        ("import sqlite3 as database\n", True),
        ("import sqlite3.dbapi2 as dbapi2\n", True),
        ("import os, sqlite3 as database\n", True),
        ("from sqlite3 import connect\n", True),
        ("from sqlite3 import connect as open_database\n", True),
        ("from sqlite3 import connect, Row as RowType\n", True),
        ("from sqlite3.dbapi2 import connect as open_database\n", True),
        (
            "try:\n"
            "    import sqlite3\n"
            "except ImportError:\n"
            "    pass\n",
            True,
        ),
        ("# import sqlite3\n", False),
        ('text = "import sqlite3"\n', False),
        ('"""import sqlite3"""\n', False),
        ("from . import sqlite3\n", False),
        ("from .sqlite3 import connect\n", False),
        ("from ..sqlite3.dbapi2 import connect\n", False),
        (
            'import importlib\nimportlib.import_module("sqlite3")\n',
            False,
        ),
    )
    assert tuple(
        _imports_sqlite3(source, filename=f"<sqlite-import-challenge-{index}>")
        for index, (source, _) in enumerate(challenge_sources)
    ) == tuple(expected for _, expected in challenge_sources)
    with pytest.raises(SyntaxError):
        _imports_sqlite3("from sqlite3 import\n", filename="<invalid-python>")

    seventh_path = "src/ge_nwp_coordinator/_seventh_sqlite_importer.py"
    for seventh_source in (
        "from sqlite3 import connect\n",
        "import sqlite3 as database\n",
    ):
        seventh_sources = {**sources, seventh_path: seventh_source}
        seventh_importers = {
            relative_path
            for relative_path, source in seventh_sources.items()
            if _imports_sqlite3(source, filename=relative_path)
        }
        assert seventh_importers == expected_sqlite_importers | {seventh_path}
        with pytest.raises(AssertionError):
            assert seventh_importers == expected_sqlite_importers


def test_b3b2a_docs_pin_private_non_executing_protocol_and_b3c_authority() -> None:
    docs = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            ".docs/b3b2a-read-scope-and-query-contracts.md",
            ".docs/b3-transition-persistence-contract.md",
            ".docs/architecture.md",
            ".docs/durable-state-model.md",
            ".docs/writer-session-authority.md",
            "README.md",
            "AGENTS.md",
        )
    )
    normalized = " ".join(docs.split())
    for phrase in (
        "private B3b2b SELECT readers now consume these contracts with no production integration",
        "ordered schema-0001 row-column tuples",
        "six immutable parameterized `SELECT` specifications",
        "private future-B3c transaction capability protocol",
        "B3b2a by itself does not execute SQL",
        "B3b2b now implements private readers",
        "fetchmany(2)",
        "`commit_outcome_unknown` is never produced by B3b2b",
        "`connection.in_transaction` is not transaction identity",
        "Future B3c must own one opaque epoch per `BEGIN IMMEDIATE` transaction",
        "B3b2b readers accept only the private capability protocol",
        "public `StateStore` is not widened",
    ):
        assert phrase in normalized
