from __future__ import annotations

import ast
from pathlib import Path
import re
import sqlite3

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "sqlite" / "coordinator-state-v1.sql"


def _contains_requests_client_usage(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name == "requests" or alias.name.startswith("requests.")
            for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and (
            node.module == "requests"
            or (node.module or "").startswith("requests.")
        ):
            return True
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "requests"
        ):
            return True
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue
        if node.args[0].value != "requests":
            continue
        if isinstance(function, ast.Name) and function.id == "__import__":
            return True
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "importlib"
            and function.attr == "import_module"
        ):
            return True
    return False


def _assert_no_requests_client_usage(paths: tuple[Path, ...]) -> None:
    accepted = (
        "class Example:\n    max_pull_requests = 1\n"
        "payload = {'max_pull_requests': 1}\n"
        "def max_pull_requests() -> int:\n    return 1\n"
    )
    rejected = (
        "import requests\n",
        "import requests as rq\nrq.get(...)\n",
        "from requests import get\nget(...)\n",
        "from requests import get as http_get\nhttp_get(...)\n",
        "requests.get(...)\n",
        "__import__('requests')\n",
        "importlib.import_module('requests')\n",
    )
    assert not _contains_requests_client_usage(accepted)
    assert all(_contains_requests_client_usage(source) for source in rejected)
    assert not any(
        _contains_requests_client_usage(path.read_text(encoding="utf-8"))
        for path in paths
    )


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _schema() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8")


def _connect_schema() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(_schema())
    return connection


def _tables(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {row[0] for row in rows}


def _triggers(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'").fetchall()
    return {row[0] for row in rows}


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def _insert_reference_records(connection: sqlite3.Connection) -> None:
    digest = "a" * 64
    timestamp = "2026-07-15T00:00:00Z"
    connection.execute(
        """
        INSERT INTO schema_migrations
            (migration_id, sequence, schema_digest, applied_at, min_app_schema, max_app_schema)
        VALUES ('coordinator-state-v1-fixture', 1, ?, ?, 1, 1)
        """,
        (digest, timestamp),
    )
    connection.execute(
        """
        INSERT INTO lease_identity_records
            (decision_ref, lease_ref, identity_valid, lease_digest, schema_id, canonical_json, canonical_digest, created_at)
        VALUES
            ('lease-identity-lease-1', 'lease-1', 1, ?, 'governed-execution.nwp-standing-lease.v1', '{}', ?, ?)
        """,
        (digest, digest, timestamp),
    )
    connection.execute(
        """
        INSERT INTO authorization_decision_receipts
            (decision_ref, lease_ref, lease_identity_decision_ref, lease_identity_valid, authorization_model,
             authorized, executable, reason, schema_id, canonical_json, canonical_digest, created_at)
        VALUES
            ('authz-lease-1', 'lease-1', 'lease-identity-lease-1', 1, 'unsupported',
             0, 0, 'unsupported_authorization_model',
             'governed-execution.nwp-authorization-decision.v1', '{}', ?, ?)
        """,
        (digest, timestamp),
    )
    connection.execute(
        """
        INSERT INTO admitted_backlogs
            (backlog_id, lease_ref, schema_id, schema_version, content_digest, canonical_json, admitted_at)
        VALUES
            ('backlog-1', 'lease-1', 'governed-execution.nwp-finite-backlog.v1', 1, ?, '{}', ?)
        """,
        (digest, timestamp),
    )
    connection.execute(
        """
        INSERT INTO dependency_decision_receipts
            (decision_ref, work_item_id, dependencies_satisfied, reason, schema_id, canonical_json, canonical_digest, created_at)
        VALUES
            ('deps-ready', 'wi-1', 1, 'accepted',
             'governed-execution.nwp-dependency-decision.v1', '{}', ?, ?)
        """,
        (digest, timestamp),
    )
    connection.execute(
        """
        INSERT INTO global_stop_operator_decision_receipts
            (decision_ref, authorized, reason, schema_id, canonical_json, canonical_digest, created_at)
        VALUES
            ('operator-decision-1', 1, 'accepted',
             'governed-execution.nwp-global-stop-operator-decision.v1', '{}', ?, ?)
        """,
        (digest, timestamp),
    )
    connection.execute(
        """
        INSERT INTO work_items
            (work_item_id, lease_id, backlog_id, schema_id, state, version, attempt_count, repair_count,
             budget_consumed, budget_limit, max_attempts, max_repairs, cleanup_required, updated_at)
        VALUES
            ('wi-1', 'lease-1', 'backlog-1', 'governed-execution.nwp-work-item-state.v1',
             'proposed', 0, 0, 0, 0, 10, 1, 0, 0, ?)
        """,
        (timestamp,),
    )
    connection.execute(
        """
        INSERT INTO global_stop_current
            (singleton_id, schema_id, version, active, stop_id, reason_class, issuer_ref,
             issued_at, operator_decision_ref, updated_at)
        VALUES
            (1, 'governed-execution.nwp-global-stop.v1', 0, 0, NULL, NULL, NULL, NULL, NULL, ?)
        """,
        (timestamp,),
    )


def _insert_transition_event(
    connection: sqlite3.Connection,
    *,
    work_item_id: str = "wi-1",
    event_ref: str = "transition-event-1",
    sequence: int = 1,
    idempotency_key: str = "transition-k1",
    command_digest: str = "b" * 64,
) -> None:
    timestamp = "2026-07-15T00:00:00Z"
    digest = "c" * 64
    connection.execute(
        """
        INSERT INTO transition_events
            (event_ref, event_sequence, work_item_id, lease_id, idempotency_key, command_digest,
             source_state, source_version, resulting_state, resulting_version, outcome, reason,
             evidence_refs_json, budget_cost_delta, attempt_count_delta, repair_count_delta,
             lease_identity_decision_ref, authorization_decision_ref, dependency_decision_ref,
             global_stop_ref, global_stop_version, schema_id, event_json, event_digest,
             replay_work_item_json, replay_work_item_digest, created_at)
        VALUES
            (?, ?, ?, 'lease-1', ?, ?, 'proposed', 0, 'lease_admitted', 1,
             'accepted', 'transition_accepted', '[]', 0, 0, 0,
             'lease-identity-lease-1', 'authz-lease-1', NULL, 'global-stop-clear', 0,
             'governed-execution.nwp-transition-event.v1', '{}', ?, '{}', ?, ?)
        """,
        (event_ref, sequence, work_item_id, idempotency_key, command_digest, digest, digest, timestamp),
    )


def _insert_global_stop_event(
    connection: sqlite3.Connection,
    *,
    event_ref: str = "global-stop-event-1",
    sequence: int = 1,
    idempotency_key: str = "stop-k1",
    command_digest: str = "d" * 64,
) -> None:
    timestamp = "2026-07-15T00:00:00Z"
    digest = "e" * 64
    connection.execute(
        """
        INSERT INTO global_stop_events
            (event_ref, event_sequence, idempotency_key, command_digest, action, source_version,
             resulting_version, outcome, reason, operator_decision_ref, resulting_global_stop_ref,
             resulting_status, schema_id, event_json, event_digest, replay_global_stop_json,
             replay_global_stop_digest, created_at)
        VALUES
            (?, ?, ?, ?, 'activate', 0, 1, 'accepted', 'global_stop_update_accepted',
             'operator-decision-1', 'stop-1', 'active',
             'governed-execution.nwp-global-stop-event.v1', '{}', ?, '{}', ?, ?)
        """,
        (event_ref, sequence, idempotency_key, command_digest, digest, digest, timestamp),
    )


def test_docs_pin_sqlite_selection_and_b1_bootstrap_scope() -> None:
    adr = _read(".docs/sqlite-state-backend-adr.md")
    schema_doc = _read(".docs/sqlite-schema-v1.md")
    threat = _read(".docs/sqlite-threat-model.md")
    operations = _read(".docs/sqlite-operations-and-recovery.md")
    bootstrap = _read(".docs/sqlite-bootstrap-and-migrations.md")
    combined = "\n".join((adr, schema_doc, threat, operations, bootstrap))
    normalized = " ".join(combined.split())

    for phrase in (
            "one private local SQLite database",
            "C2B1 implements the current bounded administrative migration framework",
            "current application generation 2",
            "exact production catalog tip `0002_development_program_and_effect_state`",
            "`0002_development_program_and_effect_state.sql` production SQL resources",
        "Migration 0002 is now the current generation-2 physical C2B2 extension",
        "leaves migration 0001 and those historical row meanings unchanged",
        "filesystem-backed regular non-symlink resource",
        "Non-filesystem or zip-backed migration resources are currently unsupported",
        "reject any selected destructive definition before expected-manifest SQLite activity",
        "supported older prefix is public `UNKNOWN`, not `MANAGED`",
        "Migration history is authoritative installed-migration evidence",
        "cumulative packaged SQL is authoritative expected schema",
        "`migration_outcome_unresolved`",
        "no automatic retry",
        "live-schema manifest",
        "does not implement a production `StateStore`",
        "`journal_mode=DELETE`",
        "`synchronous=FULL`",
        "`BEGIN IMMEDIATE`",
        "no separate idempotency tables",
        "exact replay",
        "exclusive OS advisory lock",
        "monotonically increasing generation",
        "no TTL, heartbeat, or automatic failover",
        "externally supplied typed decisions are never trusted solely by shape",
        "Reports are projections",
        "Bridge, Control Plane, Execution Substrate, Maintenance Agent, and Infrastructure Manager",
    ):
        assert phrase in normalized
    assert "A future migration 0002" not in schema_doc


def test_schema_fixture_loads_in_memory_and_has_expected_tables() -> None:
    with _connect_schema() as connection:
        assert _tables(connection) == {
            "schema_migrations",
            "writer_ownership",
            "lease_identity_records",
            "authorization_decision_receipts",
            "admitted_backlogs",
            "dependency_decision_receipts",
            "global_stop_operator_decision_receipts",
            "work_items",
            "transition_events",
            "global_stop_current",
            "global_stop_events",
        }


def test_schema_has_no_report_or_private_payload_tables_or_columns() -> None:
    with _connect_schema() as connection:
        table_names = _tables(connection)
        serialized_tables = " ".join(sorted(table_names)).lower()
        forbidden_table_fragments = ("report", "prompt", "credential", "endpoint", "path", "worker", "bridge")
        for fragment in forbidden_table_fragments:
            assert fragment not in serialized_tables

        forbidden_column_fragments = (
            "private_brief",
            "raw_prompt",
            "prompt",
            "raw_log",
            "credential",
            "endpoint",
            "local_path",
            "report_payload",
            "worker_artifact",
            "bridge_evidence",
        )
        for table in table_names:
            serialized_columns = " ".join(sorted(_columns(connection, table))).lower()
            for fragment in forbidden_column_fragments:
                assert fragment not in serialized_columns


def test_event_owned_idempotency_and_replay_snapshots_are_in_event_tables() -> None:
    with _connect_schema() as connection:
        _insert_reference_records(connection)
        _insert_transition_event(connection)
        _insert_global_stop_event(connection)

        with pytest.raises(sqlite3.IntegrityError):
            _insert_transition_event(
                connection,
                event_ref="transition-event-duplicate-key",
                sequence=2,
                idempotency_key="transition-k1",
                command_digest="f" * 64,
            )

        with pytest.raises(sqlite3.IntegrityError):
            _insert_global_stop_event(
                connection,
                event_ref="global-stop-event-duplicate-key",
                sequence=2,
                idempotency_key="stop-k1",
                command_digest="f" * 64,
            )

        assert "replay_work_item_json" in _columns(connection, "transition_events")
        assert "replay_work_item_digest" in _columns(connection, "transition_events")
        assert "replay_global_stop_json" in _columns(connection, "global_stop_events")
        assert "replay_global_stop_digest" in _columns(connection, "global_stop_events")
        assert not any("idempotency" in table and table not in {"transition_events", "global_stop_events"} for table in _tables(connection))


def test_event_tables_and_immutable_receipts_are_append_only_by_trigger() -> None:
    with _connect_schema() as connection:
        _insert_reference_records(connection)
        _insert_transition_event(connection)
        _insert_global_stop_event(connection)
        triggers = _triggers(connection)

        for trigger in (
            "transition_events_no_update",
            "transition_events_no_delete",
            "global_stop_events_no_update",
            "global_stop_events_no_delete",
            "lease_identity_records_no_update",
            "authorization_decision_receipts_no_update",
        ):
            assert trigger in triggers

        with pytest.raises(sqlite3.DatabaseError, match="append_only_transition_events"):
            connection.execute("UPDATE transition_events SET reason = 'invalid_predecessor' WHERE event_ref = 'transition-event-1'")
        with pytest.raises(sqlite3.DatabaseError, match="append_only_transition_events"):
            connection.execute("DELETE FROM transition_events WHERE event_ref = 'transition-event-1'")
        with pytest.raises(sqlite3.DatabaseError, match="append_only_global_stop_events"):
            connection.execute("UPDATE global_stop_events SET reason = 'global_stop_update_blocked' WHERE event_ref = 'global-stop-event-1'")


def test_current_state_tables_are_mutable_authority_with_enum_and_boolean_checks() -> None:
    with _connect_schema() as connection:
        _insert_reference_records(connection)
        connection.execute("UPDATE work_items SET state = 'lease_admitted', version = 1 WHERE work_item_id = 'wi-1'")
        row = connection.execute("SELECT state, version FROM work_items WHERE work_item_id = 'wi-1'").fetchone()
        assert row == ("lease_admitted", 1)

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO work_items
                    (work_item_id, lease_id, backlog_id, schema_id, state, version, attempt_count,
                     repair_count, budget_consumed, budget_limit, max_attempts, max_repairs,
                     cleanup_required, updated_at)
                VALUES
                    ('wi-bad', 'lease-1', 'backlog-1', 'governed-execution.nwp-work-item-state.v1',
                     'not_a_state', 0, 0, 0, 0, 0, 1, 0, 0, '2026-07-15T00:00:00Z')
                """
            )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE global_stop_current SET active = 2 WHERE singleton_id = 1")


def test_foreign_keys_bind_events_to_authoritative_records() -> None:
    with _connect_schema() as connection:
        _insert_reference_records(connection)
        with pytest.raises(sqlite3.IntegrityError):
            _insert_transition_event(connection, work_item_id="missing-work-item")

        fk_tables = {
            row[2]
            for row in connection.execute("PRAGMA foreign_key_list(transition_events)").fetchall()
        }
        assert {
            "work_items",
            "lease_identity_records",
            "authorization_decision_receipts",
            "dependency_decision_receipts",
        } <= fk_tables


def test_schema_fixture_declares_rollback_journal_posture_without_strict_tables() -> None:
    schema = _schema()
    assert "PRAGMA journal_mode = DELETE;" in schema
    assert "PRAGMA synchronous = FULL;" in schema
    assert "PRAGMA locking_mode = NORMAL;" in schema
    assert "PRAGMA foreign_keys = ON;" in schema
    assert "PRAGMA trusted_schema = OFF;" in schema
    assert "BEGIN IMMEDIATE for mutation transactions" in schema
    assert "STRICT" not in schema


def test_b1_static_scan_keeps_sqlite_out_of_state_store_and_runtime_service() -> None:
    source_files = list((ROOT / "src").rglob("*.py"))
    _assert_no_requests_client_usage(tuple(source_files))
    source = "\n".join(path.read_text(encoding="utf-8") for path in source_files)
    source_without_lock = "\n".join(
        path.read_text(encoding="utf-8")
        for path in source_files
        if path.name != "state_authority_lock.py"
    )
    lock_source = _read("src/ge_nwp_coordinator/state_authority_lock.py")

    forbidden_runtime_fragments = (
        "msvcrt",
        "class SQLiteStateStore",
        "class SqliteStateStore",
        "CoordinatorService",
        "while True",
        "subprocess",
        "socket",
        "urllib",
    )
    for fragment in forbidden_runtime_fragments:
        assert fragment not in source
    for fragment in ("fcntl", "LOCK_EX", "LOCK_NB"):
        assert fragment not in source_without_lock
        assert fragment in lock_source

    sqlite_importers = {
        path.relative_to(ROOT).as_posix()
        for path in source_files
        if "import sqlite3" in path.read_text(encoding="utf-8")
    }
    assert sqlite_importers == {
        "src/ge_nwp_coordinator/sqlite_connection.py",
        "src/ge_nwp_coordinator/sqlite_migration.py",
        "src/ge_nwp_coordinator/sqlite_transition_select_support.py",
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "src/ge_nwp_coordinator/sqlite_writer_session.py",
    }

    state_store = _read("src/ge_nwp_coordinator/state_store.py")
    assert "class StateStore(Protocol)" in state_store
    assert not re.search(r"class\s+\w*SQLite\w*StateStore", source)
    assert "class SQLiteStateStore" not in source
    assert "class SqliteStateStore" not in source


def test_no_persistent_database_or_journal_artifacts_exist() -> None:
    forbidden_suffixes = (".db", ".sqlite")
    forbidden_exact_suffixes = ("-wal", "-shm")
    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_file():
            name = path.name
            assert not name.endswith(forbidden_suffixes)
            assert not name.endswith(forbidden_exact_suffixes)
            assert "journal" not in name.lower()
