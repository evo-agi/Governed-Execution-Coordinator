"""Cumulative 0007 schema and explicit 0006-prefix successor checks."""
from __future__ import annotations

import hashlib
import sqlite3

import pytest

import ge_nwp_coordinator.sqlite_migration as migration
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session


_TABLES = (
    "rw0_c2_historical_continuity_bases",
    "rw0_c2_historical_sole_active_bases",
    "rw0_c2_decision_bases",
    "rw0_c2_guarded_family_relations",
    "rw0_c2_guarded_progression_results",
    "rw0_c2_bootstrap_acceptance_facts",
)
_SHA = "505d72c9c54f68e248bebab928e76564d45b853068b8b4021ebc708b640e430c"


def _inventory(connection):
    return tuple(connection.execute(sql).fetchone()[0] for sql in (
        "SELECT count(*) FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        "SELECT count(*) FROM sqlite_schema WHERE type='trigger'",
        "SELECT count(*) FROM sqlite_schema WHERE type='index' AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL",
    ))


def test_literal_0007_catalog_and_unchanged_predecessor():
    catalog = migration.MigrationCatalog(migration.load_migration_catalog().migrations[:7])
    assert tuple(item.sequence for item in catalog.migrations) == (1, 2, 3, 4, 5, 6, 7)
    assert catalog.migrations[5].checksum == (
        "58b2731d52e8e199c010b309a29aa831ffb16d4db4e755d20adb694ce0a7305f"
    )
    latest = catalog.migrations[6]
    assert latest.migration_id == "0007_rw0_c2_progression_decision"
    assert latest.resource_name == "0007_rw0_c2_progression_decision.sql"
    assert hashlib.sha256(latest.sql_bytes).hexdigest() == latest.checksum == _SHA
    assert latest.min_app_schema == latest.max_app_schema == migration.CURRENT_APPLICATION_SCHEMA == 2
    statements = migration._migration_statements(latest.sql_text)
    assert len(statements) == 18
    assert sum(s.lstrip().upper().startswith("CREATE TABLE") for s in statements) == 6
    assert sum(s.lstrip().upper().startswith("CREATE TRIGGER") for s in statements) == 12


def test_fresh_current_0007_schema_is_exact_and_empty(tmp_path):
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "fresh")
    catalog = migration.MigrationCatalog(migration.load_migration_catalog().migrations[:7])
    result = migration._initialize_database_with_catalog(
        location, catalog, current_app_schema=2, verify_managed_invariants=True)
    assert result.classification is migration.DatabaseClassification.MANAGED
    assert result.current_sequence == result.latest_sequence == 7
    assert migration.validate_database(location).classification is migration.DatabaseClassification.UNKNOWN
    with sqlite3.connect(location.database_path) as connection:
        assert _inventory(connection) == (74, 134, 5)
        relation_columns = tuple(row[1] for row in connection.execute(
            'PRAGMA table_info("rw0_c2_guarded_family_relations")'))
        assert len(relation_columns) == 35
        anchor = relation_columns.index("historical_head_postimage")
        assert relation_columns[anchor + 1:anchor + 5] == (
            "historical_work_head_ref", "historical_work_head_revision",
            "historical_work_head_digest", "historical_work_head_postimage")
        assert relation_columns[anchor + 5] == "acceptance_fact_ref"
        relation_sql = connection.execute(
            "SELECT sql FROM sqlite_schema WHERE type='table' AND name='rw0_c2_guarded_family_relations'"
        ).fetchone()[0]
        assert "guarded-family-relation.v2" in relation_sql
        assert "CONSTRAINT replan_work_head_witness CHECK" in relation_sql
        assert 'typeof("historical_work_head_postimage")=\'blob\'' in relation_sql
        foreign_keys = tuple(connection.execute(
            'PRAGMA foreign_key_list("rw0_c2_guarded_family_relations")'))
        assert any(row[2] == "development_work_item_heads"
                   and row[3] == "historical_work_head_ref"
                   and row[4] == "work_item_ref" for row in foreign_keys)
        assert not any(row[3] in {"historical_work_head_digest",
                                      "historical_work_head_postimage"}
                       for row in foreign_keys)
        result_sql = connection.execute(
            "SELECT sql FROM sqlite_schema WHERE type='table' AND name='rw0_c2_guarded_progression_results'"
        ).fetchone()[0]
        assert "guarded-progression-result.v2" in result_sql
        assert "receipt-graph-profile.v2" in result_sql
        for table in _TABLES:
            assert connection.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0] == 0
            assert {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type='trigger' AND tbl_name=?",
                (table,),
            )} == {table + "_no_update", table + "_no_delete"}
            assert " strict" in connection.execute(
                "SELECT lower(sql) FROM sqlite_schema WHERE type='table' AND name=?",
                (table,),
            ).fetchone()[0]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        unique_routes = {
            tuple(column[2] for column in connection.execute(f'PRAGMA index_info("{index[1]}")'))
            for index in connection.execute('PRAGMA index_list("rw0_c2_bootstrap_acceptance_facts")')
            if index[2] == 1
        }
        assert {("admission_fact_ref",), ("lineage_ref",), ("scope_ref",),
                ("mutation_ref",), ("decision_ref",)} <= unique_routes


def test_complete_0006_prefix_requires_explicit_0007_upgrade(tmp_path):
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "prefix")
    full = migration.load_migration_catalog()
    historical = migration.MigrationCatalog(full.migrations[:6])
    old = migration._initialize_database_with_catalog(
        location, historical, current_app_schema=2, verify_managed_invariants=True,
    )
    assert old.current_sequence == old.latest_sequence == 6
    with sqlite3.connect(location.database_path) as connection:
        assert _inventory(connection) == (68, 122, 5)
        assert all(connection.execute(
            "SELECT count(*) FROM sqlite_schema WHERE type='table' AND name=?", (table,),
        ).fetchone()[0] == 0 for table in _TABLES)
    with pytest.raises(Exception):
        with acquire_sqlite_writer_session(location):
            pass
    with sqlite3.connect(location.database_path) as connection:
        assert connection.execute("SELECT max(sequence) FROM schema_migrations").fetchone()[0] == 6
    catalog_0007 = migration.MigrationCatalog(full.migrations[:7])
    upgraded = migration._migrate_database_with_catalog(
        location, catalog_0007, current_app_schema=2,
        verify_managed_invariants=True)
    assert upgraded.current_sequence == upgraded.latest_sequence == 7
    with sqlite3.connect(location.database_path) as connection:
        assert _inventory(connection) == (74, 134, 5)
        assert all(connection.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0] == 0
                   for table in _TABLES)
    assert migration.validate_database(location).classification is migration.DatabaseClassification.UNKNOWN
