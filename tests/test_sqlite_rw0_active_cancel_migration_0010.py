"""Literal sequence-10 migration, mixed registry, and prefix compatibility."""
from __future__ import annotations

import hashlib
import sqlite3

from ge_nwp_coordinator import sqlite_migration as migration
from ge_nwp_coordinator._sqlite_rw0_terminal_anchor_migration_invariants import verify_terminal_anchor_backfill
from ge_nwp_coordinator._sqlite_rw0_terminal_anchor_migration_invariants_0010 import verify_terminal_anchor_families_0010
from ge_nwp_coordinator.sqlite_errors import SQLiteStateErrorCode
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from test_sqlite_rw0_terminal_anchor_migration_0009 import _inventory


NEW_TABLES = (
    "rw0_cancel_decision_evidence_bindings", "rw0_cancel_decision_receipts",
    "rw0_cancel_pre_effect_contexts", "rw0_cancel_pre_effect_outcomes",
    "rw0_cancel_pre_effect_results", "rw0_cancel_pre_effect_receipts",
)


def test_0010_literal_fresh_install_and_exact_inventory(tmp_path):
    catalog = migration.load_migration_catalog()
    assert tuple(item.sequence for item in catalog.migrations) == tuple(range(1, 11))
    tip = catalog.migrations[-1]
    assert tip.migration_id == "0010_rw0_active_cancel_pre_effect_safety_closure"
    assert tip.description == "RW0 active-cancel pre-effect decision and proven-unusable terminal closure"
    assert tip.checksum == hashlib.sha256(tip.sql_bytes).hexdigest()
    assert (tip.min_app_schema, tip.max_app_schema, tip.destructive) == (2, 2, False)
    statements = migration._migration_statements(tip.sql_text)
    assert len(statements) == 21
    assert sum("CREATE TABLE" in s.upper() for s in statements) == 6
    assert sum(s.lstrip().upper().startswith("CREATE TRIGGER") for s in statements) == 14
    assert sum(s.lstrip().upper().startswith("DROP TRIGGER") for s in statements) == 1
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "fresh")
    inspected = migration.initialize_database(location)
    assert inspected.current_sequence == inspected.latest_sequence == 10
    assert migration.validate_database(location) == inspected
    with sqlite3.connect(location.database_path) as connection:
        assert _inventory(connection) == (85, 159, 5, 1921, 262)
        assert all(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone() == (0,)
                   for table in NEW_TABLES)
        verify_terminal_anchor_backfill(connection)
        verify_terminal_anchor_families_0010(connection)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_0010_exact_0009_prefix_migrates_and_old_binary_refuses(tmp_path):
    catalog = migration.load_migration_catalog()
    prefix = migration.MigrationCatalog(catalog.migrations[:9])
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "prefix")
    old = migration._initialize_database_with_catalog(
        location, prefix, current_app_schema=2, verify_managed_invariants=True)
    assert old.current_sequence == 9
    with sqlite3.connect(location.database_path) as connection:
        assert _inventory(connection) == (79, 146, 5, 1814, 242)
        verify_terminal_anchor_backfill(connection)
    assert migration.validate_database(location).classification is migration.DatabaseClassification.UNKNOWN
    migrated = migration.migrate_database(location)
    assert migrated.current_sequence == migrated.latest_sequence == 10
    with sqlite3.connect(location.database_path) as connection:
        assert _inventory(connection) == (85, 159, 5, 1921, 262)
        verify_terminal_anchor_families_0010(connection)
    old_assessment = migration._assess_location_database(
        location, prefix, current_app_schema=2, verify_managed_invariants=True)
    assert old_assessment.disposition is migration._MigrationDatabaseDisposition.NEWER_UNSUPPORTED
    assert old_assessment.reason is SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW


def test_0010_lost_commit_response_uses_exact_combined_invariant(monkeypatch, tmp_path):
    catalog = migration.load_migration_catalog()
    prefix = migration.MigrationCatalog(catalog.migrations[:9])
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "uncertain")
    migration._initialize_database_with_catalog(
        location, prefix, current_app_schema=2, verify_managed_invariants=True)
    original_commit = migration._attempt_migration_commit
    attempts = []

    def lost_response(connection):
        attempts.append(1)
        original_commit(connection)
        raise sqlite3.OperationalError("lost migration acknowledgement")

    with monkeypatch.context() as patch:
        patch.setattr(migration, "_attempt_migration_commit", lost_response)
        migrated = migration.migrate_database(location)
    assert attempts == [1]
    assert migrated.current_sequence == migrated.latest_sequence == 10
    with sqlite3.connect(location.database_path) as connection:
        verify_terminal_anchor_families_0010(connection)
        assert _inventory(connection) == (85, 159, 5, 1921, 262)
