"""Migration 0009 registry shape and explicit normal-family backfill."""
from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing, contextmanager, nullcontext
from unittest.mock import patch

import pytest

from ge_nwp_coordinator import sqlite_migration as migration
from ge_nwp_coordinator import sqlite_transition_transaction as transaction
from ge_nwp_coordinator._rw0_terminal_anchor_rows import COLUMNS as ANCHOR_COLUMNS
from ge_nwp_coordinator._rw0_terminal_outcome_contracts import RecordRW0TerminalOutcomeCommandV1
from ge_nwp_coordinator._rw0_terminal_outcome_rows import COLUMNS, TABLES
from ge_nwp_coordinator.sqlite_errors import SQLiteStateError, SQLiteStateErrorCode
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_sqlite_rw0_terminal_connected import prepared_normal_case


BACKFILL_COLUMNS = (
    "schema_id", "phase_basis_ref", "phase_basis_digest", "family_profile",
    "family_route", "mutation_ref", "command_digest", "program_ref",
    "decision_ref", "context_ref", "context_digest", "outcome_value_ref",
    "outcome_value_digest", "result_ref", "result_digest", "receipt_ref",
    "receipt_digest", "graph_profile", "graph_digest",
    "committed_result_digest", "recorded_at",
)


def _inventory(connection: sqlite3.Connection) -> tuple[int, int, int, int, int]:
    tables = tuple(row[0] for row in connection.execute(
        "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
    triggers = connection.execute("SELECT COUNT(*) FROM sqlite_schema WHERE type='trigger'").fetchone()[0]
    indexes = connection.execute(
        "SELECT COUNT(*) FROM sqlite_schema WHERE type='index' AND sql IS NOT NULL").fetchone()[0]
    columns = sum(len(connection.execute(f'PRAGMA table_info("{table}")').fetchall()) for table in tables)
    foreign_keys = sum(len({row[0] for row in connection.execute(
        f'PRAGMA foreign_key_list("{table}")')}) for table in tables)
    return len(tables), triggers, indexes, columns, foreign_keys


def test_0009_literal_catalog_and_fresh_install(tmp_path):
    catalog = migration.load_migration_catalog()
    assert tuple(item.sequence for item in catalog.migrations) == tuple(range(1, 10))
    tip = catalog.migrations[-1]
    assert tip.migration_id == "0009_rw0_terminal_anchor_registry"
    assert tip.resource_name == "0009_rw0_terminal_anchor_registry.sql"
    assert tip.checksum == hashlib.sha256(tip.sql_bytes).hexdigest()
    assert (tip.min_app_schema, tip.max_app_schema, tip.destructive) == (2, 2, False)
    statements = migration._migration_statements(tip.sql_text)
    assert len(statements) == 6
    assert sum("CREATE TABLE" in statement.upper() for statement in statements) == 1
    assert sum(statement.lstrip().upper().startswith("CREATE TRIGGER") for statement in statements) == 4
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "fresh")
    inspected = migration.initialize_database(location)
    assert inspected.current_sequence == inspected.latest_sequence == 9
    assert migration.validate_database(location) == inspected
    with sqlite3.connect(location.database_path) as connection:
        assert _inventory(connection) == (79, 146, 5, 1814, 242)
        assert tuple(row[1] for row in connection.execute(
            'PRAGMA table_info("rw0_terminal_anchors")')) == ANCHOR_COLUMNS
        assert all(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
                   for table in (*TABLES, "rw0_terminal_anchors"))
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_0009_exact_empty_0008_prefix_requires_explicit_migration(tmp_path):
    catalog = migration.load_migration_catalog()
    prefix = migration.MigrationCatalog(catalog.migrations[:8])
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "prefix")
    old = migration._initialize_database_with_catalog(
        location, prefix, current_app_schema=2, verify_managed_invariants=True)
    assert old.current_sequence == 8
    assert migration.validate_database(location).classification is migration.DatabaseClassification.UNKNOWN
    migrated = migration.migrate_database(location)
    assert migrated.current_sequence == migrated.latest_sequence == 9
    with sqlite3.connect(location.database_path) as connection:
        assert _inventory(connection) == (79, 146, 5, 1814, 242)
        assert connection.execute("SELECT COUNT(*) FROM rw0_terminal_anchors").fetchone()[0] == 0


def test_0008_catalog_cannot_admit_0009_database(tmp_path):
    catalog = migration.load_migration_catalog()
    prefix = migration.MigrationCatalog(catalog.migrations[:8])
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "newer")
    migration.initialize_database(location)
    old_binary_assessment = migration._assess_location_database(
        location, prefix, current_app_schema=2,
        verify_managed_invariants=True)
    assert old_binary_assessment.disposition is migration._MigrationDatabaseDisposition.NEWER_UNSUPPORTED
    assert old_binary_assessment.reason is SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW


def _retarget_terminal_mutation(command, mutation_ref):
    safe = command.to_mapping()
    return RecordRW0TerminalOutcomeCommandV1.prepare(
        mutation_ref=mutation_ref, p1_command=command.p1_command,
        section41_command=command.section41_command, c1_rank15=command.c1_rank15,
        heads=tuple(safe["heads"]), stop=safe["stop"],
        prior_decision_digest=safe["reached_owners"][15]["digest"],
        prior_guarded_result_digest=safe["reached_owners"][16]["digest"],
        prior_receipt_graph_digest=safe["reached_owners"][17]["digest"],
        expected_branch=safe["expected_branch"],
        expected_outcome=safe["expected_outcome"],
    )


@contextmanager
def _committed_0008_family(monkeypatch, tmp_path, *, mutation_ref=None, recorded_at=None):
    """Put source-coherent normal rows into an exact 0008 physical/history tip."""
    catalog = migration.load_migration_catalog()
    prefix = migration.MigrationCatalog(catalog.migrations[:8])
    with prepared_normal_case(monkeypatch) as (source_location, command, source, _):
        if mutation_ref is not None:
            command = _retarget_terminal_mutation(command, mutation_ref)
        old_location = CoordinatorStateLocation.from_trusted_root(tmp_path / "old")
        migration._initialize_database_with_catalog(
            old_location, prefix, current_app_schema=2,
            verify_managed_invariants=True)
        with closing(sqlite3.connect(source_location.database_path)) as source_db, closing(
            sqlite3.connect(old_location.database_path)
        ) as old_db:
            source_db.backup(old_db)
            history_guard = old_db.execute(
                "SELECT sql FROM sqlite_schema WHERE name='schema_migrations_no_delete'"
            ).fetchone()[0]
            old_db.execute("DROP TRIGGER rw0_terminal_receipts_register_anchor")
            old_db.execute("DROP TABLE rw0_terminal_anchors")
            old_db.execute("DROP TRIGGER schema_migrations_no_delete")
            old_db.execute("DELETE FROM schema_migrations WHERE sequence=9")
            old_db.execute(history_guard)
            old_db.commit()
            assert _inventory(old_db)[:3] == (78, 142, 5)
        assert migration._assess_location_database(
            old_location, prefix, current_app_schema=2,
            verify_managed_invariants=True,
        ).disposition is migration._MigrationDatabaseDisposition.CURRENT
        timestamp_scope = (patch.object(
            transaction, "_capture_transaction_timestamp", return_value=recorded_at)
            if recorded_at is not None else nullcontext())
        with timestamp_scope:
            with acquire_sqlite_writer_session(source_location) as writer:
                committed = writer._record_terminal_outcome(command, source)
                assert committed.outcome == "accept"
        with closing(sqlite3.connect(source_location.database_path)) as source_db, closing(
            sqlite3.connect(old_location.database_path)
        ) as old_db:
            old_db.execute("PRAGMA foreign_keys=ON")
            original = {}
            for table in TABLES:
                row = source_db.execute(f"SELECT {', '.join(COLUMNS[table])} FROM {table}").fetchone()
                assert row is not None
                original[table] = row
                old_db.execute(
                    f"INSERT INTO {table} ({', '.join(COLUMNS[table])}) "
                    f"VALUES ({', '.join('?' for _ in COLUMNS[table])})", row)
            old_db.commit()
            assert old_db.execute("PRAGMA foreign_key_check").fetchall() == []
        yield old_location, original, command, source


@pytest.mark.parametrize("mutation_ref,recorded_at", (
    ("terminal.backfill.one", "2030-01-02T03:04:05Z"),
    ("terminal.backfill.two", "2031-06-07T08:09:10Z"),
))
def test_0009_populated_0008_prefix_backfills_exactly_without_rewriting(
    monkeypatch, tmp_path, mutation_ref, recorded_at,
):
    with _committed_0008_family(
        monkeypatch, tmp_path, mutation_ref=mutation_ref, recorded_at=recorded_at,
    ) as (location, original, command, source):
        with closing(sqlite3.connect(location.database_path)) as before:
            assert _inventory(before)[:3] == (78, 142, 5)
            assert all(before.execute(f"SELECT * FROM {table}").fetchone() == original[table]
                       for table in TABLES)
        migrated = migration.migrate_database(location)
        assert migrated.current_sequence == migrated.latest_sequence == 9
        with closing(sqlite3.connect(location.database_path)) as after:
            assert _inventory(after) == (79, 146, 5, 1814, 242)
            assert all(after.execute(f"SELECT * FROM {table}").fetchone() == original[table]
                       for table in TABLES)
            context, outcome, result, receipt = (
                dict(zip(COLUMNS[table], original[table], strict=True)) for table in TABLES
            )
            assert receipt["mutation_ref"] == mutation_ref
            assert receipt["recorded_at"] == recorded_at
            assert context["context_ref"] == receipt["context_ref"]
            assert outcome["outcome_value_ref"] == receipt["outcome_value_ref"]
            assert result["result_ref"] == receipt["result_ref"]
            expected = (
                "governed-execution.nwp-rw0-terminal-anchor.v1",
                receipt["phase_basis_ref"], receipt["phase_basis_digest"],
                receipt["profile"], receipt["family_route"],
                receipt["mutation_ref"], receipt["command_digest"],
                context["program_ref"], receipt["p1_decision_ref"],
                receipt["context_ref"], receipt["context_digest"],
                receipt["outcome_value_ref"], receipt["outcome_value_digest"],
                receipt["result_ref"], receipt["result_digest"],
                receipt["receipt_ref"], receipt["receipt_digest"],
                receipt["graph_profile"], receipt["graph_digest"],
                receipt["committed_result_digest"], receipt["recorded_at"],
            )
            anchor = after.execute(
                f"SELECT {', '.join(BACKFILL_COLUMNS)} FROM rw0_terminal_anchors"
            ).fetchall()
            assert anchor == [expected]
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._record_terminal_outcome(command, source).outcome == "accept"
            assert writer._recover_terminal_outcome(command, source).classification == "committed_exact"


@pytest.mark.parametrize("damage", ("partial", "contradictory"))
def test_0009_malformed_0008_family_rolls_back(monkeypatch, tmp_path, damage):
    with _committed_0008_family(monkeypatch, tmp_path) as (location, original, _, __):
        with closing(sqlite3.connect(location.database_path)) as connection:
            if damage == "partial":
                guard = connection.execute(
                    "SELECT sql FROM sqlite_schema WHERE name='rw0_terminal_receipts_no_delete'"
                ).fetchone()[0]
                connection.execute("DROP TRIGGER rw0_terminal_receipts_no_delete")
                connection.execute("DELETE FROM rw0_terminal_receipts")
                connection.execute(guard)
            else:
                guard = connection.execute(
                    "SELECT sql FROM sqlite_schema WHERE name='rw0_terminal_outcomes_no_update'"
                ).fetchone()[0]
                connection.execute("DROP TRIGGER rw0_terminal_outcomes_no_update")
                connection.execute("UPDATE rw0_terminal_outcomes SET decision_digest=?", ("f" * 64,))
                connection.execute(guard)
            connection.commit()
        with pytest.raises(SQLiteStateError):
            migration.migrate_database(location)
        with closing(sqlite3.connect(location.database_path)) as after:
            assert _inventory(after)[:3] == (78, 142, 5)
            assert after.execute(
                "SELECT COUNT(*) FROM schema_migrations WHERE sequence=9").fetchone()[0] == 0
            assert after.execute(
                "SELECT COUNT(*) FROM sqlite_schema WHERE name='rw0_terminal_anchors'").fetchone()[0] == 0


def test_0009_commit_response_loss_recovers_populated_backfill(monkeypatch, tmp_path):
    with _committed_0008_family(monkeypatch, tmp_path) as (location, original, _, __):
        original_commit = migration._attempt_migration_commit
        attempts = []

        def lost_response(connection):
            attempts.append(1)
            original_commit(connection)
            raise sqlite3.OperationalError("lost migration acknowledgement")

        with monkeypatch.context() as patch:
            patch.setattr(migration, "_attempt_migration_commit", lost_response)
            migrated = migration.migrate_database(location)
        assert migrated.current_sequence == migrated.latest_sequence == 9
        assert attempts == [1]
        with closing(sqlite3.connect(location.database_path)) as connection:
            assert connection.execute("SELECT COUNT(*) FROM rw0_terminal_anchors").fetchone()[0] == 1
            assert all(connection.execute(f"SELECT * FROM {table}").fetchone() == original[table]
                       for table in TABLES)


def test_0009_precommit_response_loss_is_definitely_not_committed(tmp_path, monkeypatch):
    catalog = migration.load_migration_catalog()
    prefix = migration.MigrationCatalog(catalog.migrations[:8])
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "old")
    migration._initialize_database_with_catalog(
        location, prefix, current_app_schema=2, verify_managed_invariants=True)
    attempts = []

    def fail_before_commit(connection):
        attempts.append(1)
        raise sqlite3.OperationalError("lost migration before commit")

    with monkeypatch.context() as patch:
        patch.setattr(migration, "_attempt_migration_commit", fail_before_commit)
        with pytest.raises(SQLiteStateError) as caught:
            migration.migrate_database(location)
    assert caught.value.error_class == SQLiteStateErrorCode.MIGRATION_FAILED.value
    assert attempts == [1]
    assert migration._assess_location_database(
        location, prefix, current_app_schema=2,
        verify_managed_invariants=True,
    ).disposition is migration._MigrationDatabaseDisposition.CURRENT


def test_0009_committed_but_broken_backfill_is_unresolved(monkeypatch, tmp_path):
    with _committed_0008_family(monkeypatch, tmp_path) as (location, _, __, ___):
        original_commit = migration._attempt_migration_commit
        attempts = []

        def corrupt_after_commit(connection):
            attempts.append(1)
            original_commit(connection)
            with closing(sqlite3.connect(location.database_path)) as corrupt:
                guard = corrupt.execute(
                    "SELECT sql FROM sqlite_schema WHERE name='rw0_terminal_anchors_no_delete'"
                ).fetchone()[0]
                corrupt.execute("DROP TRIGGER rw0_terminal_anchors_no_delete")
                corrupt.execute("DELETE FROM rw0_terminal_anchors")
                corrupt.execute(guard)
                corrupt.commit()
            raise sqlite3.OperationalError("lost migration after corruption")

        with monkeypatch.context() as patch:
            patch.setattr(migration, "_attempt_migration_commit", corrupt_after_commit)
            with pytest.raises(SQLiteStateError) as caught:
                migration.migrate_database(location)
        assert caught.value.error_class == SQLiteStateErrorCode.MIGRATION_OUTCOME_UNRESOLVED.value
        assert attempts == [1]


def test_0009_post_commit_close_failure_recovers(monkeypatch, tmp_path):
    catalog = migration.load_migration_catalog()
    prefix = migration.MigrationCatalog(catalog.migrations[:8])
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "old")
    migration._initialize_database_with_catalog(
        location, prefix, current_app_schema=2, verify_managed_invariants=True)
    original_close = migration._close_migration_connection
    calls = []

    def close_then_fail(connection):
        calls.append(1)
        if len(calls) == 1:
            connection.close()
            raise sqlite3.OperationalError("lost close acknowledgement")
        return original_close(connection)

    with monkeypatch.context() as patch:
        patch.setattr(migration, "_close_migration_connection", close_then_fail)
        migrated = migration.migrate_database(location)
    assert migrated.current_sequence == migrated.latest_sequence == 9
    assert len(calls) >= 2


def test_0009_direct_orphan_anchor_rejected_by_family_guard_with_fk_parents(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, _, _):
        safe = command.to_mapping()
        relation = safe["p1"]["relation"]
        candidate = {
            "schema_id": "governed-execution.nwp-rw0-terminal-anchor.v1",
            "phase_basis_ref": safe["phase_basis_ref"],
            "phase_basis_digest": safe["phase_basis_digest"],
            "family_profile": "artificial_offline_normal.v1",
            "family_route": safe["family_route"],
            "mutation_ref": safe["mutation_ref"],
            "command_digest": safe["command_digest"],
            "program_ref": relation["program_ref"],
            "decision_ref": relation["preassigned_decision_ref"],
            "context_ref": safe["context_ref"], "context_digest": "a" * 64,
            "outcome_value_ref": safe["outcome_value_ref"],
            "outcome_value_digest": "a" * 64,
            "result_ref": safe["result_ref"], "result_digest": "a" * 64,
            "receipt_ref": safe["receipt_ref"], "receipt_digest": "a" * 64,
            "graph_profile": "governed-execution.nwp-rw0-terminal-normal-graph.v1",
            "graph_digest": "a" * 64, "committed_result_digest": "a" * 64,
            "recorded_at": "2030-01-02T03:04:05Z",
        }
        with closing(sqlite3.connect(location.database_path)) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            assert connection.execute(
                "SELECT COUNT(*) FROM rw0_phase_instances "
                "WHERE phase_basis_ref=? AND phase_basis_digest=?",
                (candidate["phase_basis_ref"], candidate["phase_basis_digest"]),
            ).fetchone()[0] == 1
            assert connection.execute(
                "SELECT COUNT(*) FROM development_decisions "
                "WHERE program_ref=? AND decision_ref=?",
                (candidate["program_ref"], candidate["decision_ref"]),
            ).fetchone()[0] == 1
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
            with pytest.raises(sqlite3.IntegrityError, match="invalid_rw0_terminal_anchor"):
                connection.execute(
                    f"INSERT INTO rw0_terminal_anchors ({', '.join(ANCHOR_COLUMNS)}) "
                    f"VALUES ({', '.join('?' for _ in ANCHOR_COLUMNS)})",
                    tuple(candidate[name] for name in ANCHOR_COLUMNS),
                )
            assert connection.execute("SELECT COUNT(*) FROM rw0_terminal_anchors").fetchone()[0] == 0
