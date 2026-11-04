"""P0-only additive migration, explicit upgrade, and immutable SQL routes."""
from __future__ import annotations

import hashlib
import sqlite3

import pytest

import ge_nwp_coordinator.sqlite_migration as migration
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator._rw0_c2_scope_admission_contracts import _TABLE_FIELDS


def _inventory(connection):
    return tuple(connection.execute(sql).fetchone()[0] for sql in (
        "SELECT count(*) FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        "SELECT count(*) FROM sqlite_schema WHERE type='trigger'",
        "SELECT count(*) FROM sqlite_schema WHERE type='index' AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL",
    ))


def test_0006_literal_catalog_and_earlier_checksums():
    catalog = migration.load_migration_catalog()
    assert tuple(item.sequence for item in catalog.migrations) == tuple(range(1, 11))
    assert tuple(item.checksum for item in catalog.migrations[:5]) == (
        "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148",
        "5859f49994b1467db71911fb60db4f1cfc562af7517dc6e4d81b5b29ca44d56c",
        "b5c7cac8e074b77ab369579f1f8015f547f1a2776b4b09d612e56280f16c1579",
        "967b9c2deb43da625f9ce82d43c9538bfd2fa27c02f3abdfcb12eb3a2aef8cec",
        "583c14e2018c84a942e2e72bbb57d24ae39b2470dc4c286c5f775afe1ef9ea87",
    )
    last = catalog.migrations[5]
    assert last.migration_id == "0006_rw0_c2_scope_admission"
    assert last.resource_name == "0006_rw0_c2_scope_admission.sql"
    assert hashlib.sha256(last.sql_bytes).hexdigest() == last.checksum == (
        "58b2731d52e8e199c010b309a29aa831ffb16d4db4e755d20adb694ce0a7305f"
    )
    assert last.min_app_schema == last.max_app_schema == migration.CURRENT_APPLICATION_SCHEMA == 2
    statements = migration._migration_statements(last.sql_text)
    assert len(statements) == 12
    assert sum(item.lstrip().upper().startswith("CREATE TABLE") for item in statements) == 4
    assert sum(item.lstrip().upper().startswith("CREATE TRIGGER") for item in statements) == 8


def test_0006_fresh_schema_and_zero_seed(tmp_path):
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "fresh")
    historical_catalog = migration.MigrationCatalog(
        migration.load_migration_catalog().migrations[:6]
    )
    result = migration._initialize_database_with_catalog(
        location, historical_catalog, current_app_schema=2,
        verify_managed_invariants=True,
    )
    assert result.current_sequence == result.latest_sequence == 6
    with sqlite3.connect(location.database_path) as connection:
        assert _inventory(connection) == (68, 122, 5)
        for table, fields in _TABLE_FIELDS.items():
            assert tuple(row[1] for row in connection.execute(f'PRAGMA table_xinfo("{table}")')) == fields
            assert connection.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0] == 0
            assert {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type='trigger' AND tbl_name=?", (table,)
            )} == {table + "_no_update", table + "_no_delete"}
            assert " strict" in connection.execute(
                "SELECT lower(sql) FROM sqlite_schema WHERE type='table' AND name=?", (table,)
            ).fetchone()[0]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        indexes = connection.execute(
            'PRAGMA index_list("rw0_c2_scope_admission_facts")'
        ).fetchall()
        unique_routes = {
            tuple(row[2] for row in connection.execute(
                f'PRAGMA index_info("{index[1]}")'
            ))
            for index in indexes if index[2] == 1
        }
        assert {('act_ref',), ('lineage_ref',), ('scope_ref',)} <= unique_routes
        for table in _TABLE_FIELDS:
            routes = {
                tuple(row[2] for row in connection.execute(
                    f'PRAGMA index_info("{index[1]}")'
                ))
                for index in connection.execute(f'PRAGMA index_list("{table}")')
                if index[2] == 1
            }
            assert all(
                coordinate not in route
                for route in routes
                for coordinate in (
                    'enrollment_ref', 'incarnation_ref',
                    'authority_process_ref', 'storage_custody_ref',
                )
            )
        for table in (
            "rw0_c2_historical_continuity_bases",
            "rw0_c2_historical_sole_active_bases",
            "rw0_c2_decision_bases",
            "rw0_c2_guarded_family_relations",
            "rw0_c2_guarded_progression_results",
            "rw0_c2_bootstrap_acceptance_facts",
        ):
            assert connection.execute(
                "SELECT count(*) FROM sqlite_schema WHERE type='table' AND name=?",
                (table,),
            ).fetchone()[0] == 0
    current_inspection = migration.validate_database(location)
    assert current_inspection.classification is migration.DatabaseClassification.UNKNOWN
    assert current_inspection.latest_sequence == 10


def test_populated_0005_prefix_requires_explicit_upgrade(tmp_path):
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "prefix")
    full = migration.load_migration_catalog()
    prefix = migration.MigrationCatalog(full.migrations[:5])
    migration._initialize_database_with_catalog(
        location, prefix, current_app_schema=2, verify_managed_invariants=True,
    )
    with sqlite3.connect(location.database_path) as connection:
        connection.execute(
            "INSERT INTO writer_ownership "
            "(singleton_id,writer_ref,generation,issued_ref,issuance_nonce_digest,acquired_at) "
            "VALUES (1,'writer-synthetic',1,'issued-synthetic',?,?)",
            ("b" * 64, "2026-10-22T00:00:00Z"),
        )
        assert _inventory(connection) == (64, 114, 5)
    with pytest.raises(Exception):
        with acquire_sqlite_writer_session(location):
            pass
    with sqlite3.connect(location.database_path) as connection:
        assert connection.execute("SELECT max(sequence) FROM schema_migrations").fetchone()[0] == 5
    historical_catalog = migration.MigrationCatalog(full.migrations[:6])
    result = migration._migrate_database_with_catalog(
        location, historical_catalog, current_app_schema=2,
        verify_managed_invariants=True,
    )
    assert result.current_sequence == result.latest_sequence == 6
    with sqlite3.connect(location.database_path) as connection:
        assert _inventory(connection) == (68, 122, 5)
        assert connection.execute("SELECT writer_ref,generation FROM writer_ownership").fetchone() == (
            "writer-synthetic", 1,
        )
    with pytest.raises(Exception):
        with acquire_sqlite_writer_session(location):
            pass
    result = migration.migrate_database(location)
    assert result.current_sequence == result.latest_sequence == 10
    with sqlite3.connect(location.database_path) as connection:
        assert _inventory(connection) == (85, 159, 5)
        assert connection.execute("SELECT writer_ref,generation FROM writer_ownership").fetchone() == (
            "writer-synthetic", 1,
        )
