"""Exact additive Section 41 0005 catalog and synthetic migration behavior."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

import ge_nwp_coordinator.sqlite_migration as migration
from ge_nwp_coordinator._section41_post_execution_proposal_row_values import (
    _CONTEXT_COLUMNS, _CONTEXT_TABLE, _RECEIPT_COLUMNS, _RECEIPT_TABLE,
)
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session


_EARLIER = (
    ("0001_initial", 17940, "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"),
    ("0002_development_program_and_effect_state", 154434, "5859f49994b1467db71911fb60db4f1cfc562af7517dc6e4d81b5b29ca44d56c"),
    ("0003_cognitive_proposal_and_selection_state", 161472, "b5c7cac8e074b77ab369579f1f8015f547f1a2776b4b09d612e56280f16c1579"),
    ("0004_rw0_c1_durable_evidence", 289058, "967b9c2deb43da625f9ce82d43c9538bfd2fa27c02f3abdfcb12eb3a2aef8cec"),
)


def _location(tmp_path: Path, name: str) -> CoordinatorStateLocation:
    return CoordinatorStateLocation.from_trusted_root(tmp_path / name)


def _inventory(connection: sqlite3.Connection) -> tuple[int, int, int]:
    return tuple(connection.execute(sql).fetchone()[0] for sql in (
        "SELECT count(*) FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        "SELECT count(*) FROM sqlite_schema WHERE type='trigger'",
        "SELECT count(*) FROM sqlite_schema WHERE type='index' AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL",
    ))


def test_literal_catalog_preserves_four_earlier_resources_and_generation_two() -> None:
    catalog = migration.load_migration_catalog()
    assert tuple(item.sequence for item in catalog.migrations) == (1, 2, 3, 4, 5, 6, 7, 8)
    assert tuple((item.migration_id, len(item.sql_bytes),
                  hashlib.sha256(item.sql_bytes).hexdigest())
                 for item in catalog.migrations[:4]) == _EARLIER
    last = catalog.migrations[4]
    assert last.migration_id == "0005_section41_post_execution_proposal_family"
    assert len(last.sql_bytes) == 9516
    assert hashlib.sha256(last.sql_bytes).hexdigest() == (
        "583c14e2018c84a942e2e72bbb57d24ae39b2470dc4c286c5f775afe1ef9ea87"
    )
    assert last.min_app_schema == last.max_app_schema == migration.CURRENT_APPLICATION_SCHEMA == 2
    assert last.destructive is False
    statements = migration._migration_statements(last.sql_text)
    assert len(statements) == 6
    assert sum(s.lstrip().upper().startswith("CREATE TABLE") for s in statements) == 2
    assert sum(s.lstrip().upper().startswith("CREATE TRIGGER") for s in statements) == 4
    assert not any("CREATE INDEX" in s.upper() for s in statements)


def test_fresh_tip_has_exact_tables_columns_foreign_keys_guards_and_zero_seed(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path, "fresh")
    inspection = migration.initialize_database(location)
    assert inspection.current_sequence == inspection.latest_sequence == 8
    with sqlite3.connect(location.database_path) as db:
        assert _inventory(db) == (78, 142, 5)
        for table, columns in ((_CONTEXT_TABLE, _CONTEXT_COLUMNS),
                               (_RECEIPT_TABLE, _RECEIPT_COLUMNS)):
            assert tuple(row[1] for row in db.execute(f'PRAGMA table_xinfo("{table}")')) == columns
            assert db.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0] == 0
            assert " strict" in db.execute(
                "SELECT lower(sql) FROM sqlite_schema WHERE type='table' AND name=?",
                (table,),
            ).fetchone()[0]
            assert {row[0] for row in db.execute(
                "SELECT name FROM sqlite_schema WHERE type='trigger' AND tbl_name=?",
                (table,),
            )} == {f"{table}_no_update", f"{table}_no_delete"}
            foreign = list(db.execute(f'PRAGMA foreign_key_list("{table}")'))
            assert foreign and all(row[5] == "RESTRICT" and row[6] == "RESTRICT"
                                   for row in foreign)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    assert migration.validate_database(location).current_sequence == 8


def test_populated_exact_0004_prefix_requires_explicit_upgrade_and_preserves_owner(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path, "prefix-0004")
    catalog = migration.load_migration_catalog()
    prefix = migration.MigrationCatalog(catalog.migrations[:4])
    migration._initialize_database_with_catalog(
        location, prefix, current_app_schema=2, verify_managed_invariants=True,
    )
    with sqlite3.connect(location.database_path) as db:
        db.execute("INSERT INTO writer_ownership "
                   "(singleton_id,writer_ref,generation,issued_ref,issuance_nonce_digest,acquired_at) "
                   "VALUES (1,'writer-synthetic',1,'issued-synthetic',?,?)",
                   ("b" * 64, "2026-10-22T00:00:00Z"))
        assert _inventory(db) == (62, 110, 5)
    with pytest.raises(Exception):
        # Ordinary writer acquisition may refuse an older exact prefix; it
        # must never append the migration as a side effect.
        with acquire_sqlite_writer_session(location):
            pass
    with sqlite3.connect(location.database_path) as db:
        assert db.execute("SELECT max(sequence) FROM schema_migrations").fetchone()[0] == 4
    upgraded = migration.migrate_database(location)
    assert upgraded.current_sequence == upgraded.latest_sequence == 8
    with sqlite3.connect(location.database_path) as db:
        assert _inventory(db) == (78, 142, 5)
        assert db.execute("SELECT writer_ref,generation FROM writer_ownership").fetchone() == (
            "writer-synthetic", 1,
        )
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_unknown_partial_0005_schema_refuses_administrative_migration(tmp_path: Path) -> None:
    location = _location(tmp_path, "partial")
    catalog = migration.load_migration_catalog()
    prefix = migration.MigrationCatalog(catalog.migrations[:4])
    migration._initialize_database_with_catalog(
        location, prefix, current_app_schema=2, verify_managed_invariants=True,
    )
    with sqlite3.connect(location.database_path) as db:
        db.execute("CREATE TABLE development_post_execution_proposal_contexts(x INTEGER)")
    with pytest.raises(Exception):
        migration.migrate_database(location)
    with sqlite3.connect(location.database_path) as db:
        assert db.execute("SELECT max(sequence) FROM schema_migrations").fetchone()[0] == 4
        assert db.execute("SELECT count(*) FROM sqlite_schema WHERE name=?",
                          (_RECEIPT_TABLE,)).fetchone()[0] == 0


def test_0005_ddl_failure_before_commit_rolls_back_complete_suffix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path, "rollback")
    catalog = migration.load_migration_catalog()
    prefix = migration.MigrationCatalog(catalog.migrations[:4])
    migration._initialize_database_with_catalog(
        location, prefix, current_app_schema=2, verify_managed_invariants=True,
    )
    original = migration._apply_migration_definition_in_transaction
    reached = []

    def fail_after_real_ddl(connection: sqlite3.Connection,
                            item: migration.MigrationDefinition) -> None:
        original(connection, item)
        if item.sequence == 5:
            reached.append(True)
            raise sqlite3.OperationalError("synthetic_0005_precommit_failure")

    monkeypatch.setattr(migration, "_apply_migration_definition_in_transaction",
                        fail_after_real_ddl)
    with pytest.raises(Exception):
        migration.migrate_database(location)
    assert reached
    with sqlite3.connect(location.database_path) as db:
        assert _inventory(db) == (62, 110, 5)
        assert db.execute("SELECT max(sequence) FROM schema_migrations").fetchone()[0] == 4
        assert db.execute("SELECT count(*) FROM sqlite_schema WHERE name IN (?,?)",
                          (_CONTEXT_TABLE, _RECEIPT_TABLE)).fetchone()[0] == 0


def test_exact_old_catalog_refuses_new_schema_as_newer_unsupported(tmp_path: Path) -> None:
    location = _location(tmp_path, "newer")
    migration.initialize_database(location)
    catalog = migration.load_migration_catalog()
    prior = migration.MigrationCatalog(catalog.migrations[:4])
    assessment = migration._assess_location_database(
        location, prior, current_app_schema=2, verify_managed_invariants=True,
    )
    assert assessment.disposition.value == "newer_unsupported"
    assert assessment.reason.value == "database_schema_too_new"
