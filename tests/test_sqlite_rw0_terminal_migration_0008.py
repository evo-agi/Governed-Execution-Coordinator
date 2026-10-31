"""Current 0008 tip and exact historical-prefix compatibility."""
from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing

import pytest

import ge_nwp_coordinator.sqlite_migration as migration
from ge_nwp_coordinator._rw0_terminal_outcome_rows import COLUMNS, OUTCOME, TABLES, seal_row
from ge_nwp_coordinator._rw0_terminal_outcome_contracts import _canonical
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_errors import SQLiteStateErrorCode
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_rw0_terminal_outcome_values import _normal_mapping
from test_sqlite_rw0_terminal_connected import prepared_normal_case


_SHA = "a199ea64b4546d441cde00d8c7def62405ed28a89841a181dc6ba93871845254"
_OLD_SHA = (
    "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148",
    "5859f49994b1467db71911fb60db4f1cfc562af7517dc6e4d81b5b29ca44d56c",
    "b5c7cac8e074b77ab369579f1f8015f547f1a2776b4b09d612e56280f16c1579",
    "967b9c2deb43da625f9ce82d43c9538bfd2fa27c02f3abdfcb12eb3a2aef8cec",
    "583c14e2018c84a942e2e72bbb57d24ae39b2470dc4c286c5f775afe1ef9ea87",
    "58b2731d52e8e199c010b309a29aa831ffb16d4db4e755d20adb694ce0a7305f",
    "505d72c9c54f68e248bebab928e76564d45b853068b8b4021ebc708b640e430c",
)


def _schema(connection):
    return {name: (kind, sql) for kind, name, sql in connection.execute(
        "SELECT type, name, sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' AND sql IS NOT NULL")}


def _inventory(connection):
    return tuple(connection.execute(sql).fetchone()[0] for sql in (
        "SELECT count(*) FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        "SELECT count(*) FROM sqlite_schema WHERE type='trigger'",
        "SELECT count(*) FROM sqlite_schema WHERE type='index' AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL",
    ))


def test_0008_catalog_literal_and_prior_bytes():
    catalog = migration.load_migration_catalog()
    assert tuple(x.sequence for x in catalog.migrations) == tuple(range(1, 9))
    assert tuple(x.checksum for x in catalog.migrations[:7]) == _OLD_SHA
    tip = catalog.migrations[-1]
    assert tip.migration_id == "0008_rw0_terminal_outcome"
    assert tip.resource_name == "0008_rw0_terminal_outcome.sql"
    assert hashlib.sha256(tip.sql_bytes).hexdigest() == tip.checksum == _SHA
    assert tip.min_app_schema == tip.max_app_schema == migration.CURRENT_APPLICATION_SCHEMA == 2
    statements = migration._migration_statements(tip.sql_text)
    assert len(statements) == 12
    assert sum("CREATE TABLE" in s.upper() for s in statements) == 4
    assert sum(s.lstrip().upper().startswith("CREATE TRIGGER") for s in statements) == 8
    for table in ("rw0_terminal_contexts", "rw0_terminal_receipts"):
        definition = next(s for s in statements if f"CREATE TABLE {table} (" in s)
        assert "profile='artificial_offline_normal.v1'" in definition
    context = next(s for s in statements if "CREATE TABLE rw0_terminal_contexts (" in s)
    assert "schema_id='governed-execution.nwp-rw0-terminal-context.v2'" in context
    assert "length(closure_heads_bytes) BETWEEN 1 AND 32768" in context
    outcome = next(s for s in statements if "CREATE TABLE rw0_terminal_outcomes (" in s)
    assert "length(closure_heads_bytes) BETWEEN 1 AND 4096" in outcome


def test_0008_literal_catalog_applies_independently_with_exact_prefix_inventories():
    catalog = migration.load_migration_catalog()
    with sqlite3.connect(":memory:") as db:
        db.execute("PRAGMA foreign_keys=ON")
        before_0008 = None
        for item in catalog.migrations:
            assert hashlib.sha256(item.sql_bytes).hexdigest() == item.checksum
            db.executescript(item.sql_text)
            if item.sequence == 6:
                assert _inventory(db) == (68, 122, 5)
            elif item.sequence == 7:
                assert _inventory(db) == (74, 134, 5)
                before_0008 = _schema(db)
            elif item.sequence == 8:
                assert _inventory(db) == (78, 142, 5)
                assert before_0008 is not None
                assert all(_schema(db)[key] == value for key, value in before_0008.items())
                assert all(db.execute(f'SELECT count(*) FROM {table}').fetchone()[0] == 0
                           for table in TABLES)
                assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_0008_sql_normal_shape_checks_reject_cancel_and_partial_pairs():
    tip = migration.load_migration_catalog().migrations[-1]
    logical = _normal_mapping()
    heads = logical.pop("closure_heads")
    stop = logical.pop("closure_stop")
    row = seal_row(OUTCOME, {**logical,
                             "closure_heads_bytes": _canonical({"heads": heads}),
                             "closure_stop_bytes": _canonical({"stop": stop})})
    fields = COLUMNS[OUTCOME]
    insert = (f"INSERT INTO {OUTCOME} ({', '.join(fields)}) "
              f"VALUES ({', '.join('?' for _ in fields)})")
    with sqlite3.connect(":memory:") as db:
        db.executescript(tip.sql_text)
        for changed in (
            {"branch": "active_cancel_reconciled"},
            {"outcome": "cancel"},
            {"decision_kind": "accept"},
            {"acceptance_fact_ref": "fact.1"},
            {"acceptance_fact_ref": "fact.1", "acceptance_fact_digest": "a" * 64},
            {"reconciliation_ref": "cancel.1"},
            {"mismatch_digest": "a" * 64},
        ):
            candidate = {**row.mapping, **changed}
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(insert, tuple(candidate[name] for name in fields))
            assert db.execute(f"SELECT count(*) FROM {OUTCOME}").fetchone()[0] == 0
        db.execute(insert, row.values)
        assert db.execute(f"SELECT count(*) FROM {OUTCOME}").fetchone()[0] == 1


def test_0008_fresh_and_explicit_0007_upgrade_preserve_prior_schema(tmp_path):
    full = migration.load_migration_catalog()
    fresh = CoordinatorStateLocation.from_trusted_root(tmp_path / "fresh")
    initialized = migration.initialize_database(fresh)
    assert initialized.current_sequence == initialized.latest_sequence == 8
    assert migration.validate_database(fresh) == initialized
    with sqlite3.connect(fresh.database_path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        assert _inventory(db) == (78, 142, 5)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        for table in TABLES:
            assert tuple(row[1] for row in db.execute(f'PRAGMA table_xinfo("{table}")')) == COLUMNS[table]
            assert db.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0] == 0
            assert {r[0] for r in db.execute("SELECT name FROM sqlite_schema WHERE type='trigger' AND tbl_name=?", (table,))} == {
                table + "_no_update", table + "_no_delete"}
            assert " strict" in db.execute("SELECT lower(sql) FROM sqlite_schema WHERE name=?", (table,)).fetchone()[0]
        assert {tuple(row[2] for row in db.execute(f'PRAGMA index_info("{index[1]}")'))
                for index in db.execute('PRAGMA index_list("rw0_terminal_contexts")') if index[2] == 1} >= {
                    ("mutation_ref",), ("phase_basis_ref",), ("p1_decision_ref",)}
    prefix_location = CoordinatorStateLocation.from_trusted_root(tmp_path / "prefix")
    prefix = migration.MigrationCatalog(full.migrations[:7])
    old = migration._initialize_database_with_catalog(
        prefix_location, prefix, current_app_schema=2, verify_managed_invariants=True)
    assert old.current_sequence == 7
    with sqlite3.connect(prefix_location.database_path) as db:
        before = _schema(db)
        assert _inventory(db) == (74, 134, 5)
    assert migration.validate_database(prefix_location).classification is migration.DatabaseClassification.UNKNOWN
    with pytest.raises(Exception):
        with acquire_sqlite_writer_session(prefix_location):
            pass
    upgraded = migration.migrate_database(prefix_location)
    assert upgraded.current_sequence == upgraded.latest_sequence == 8
    assert migration.validate_database(prefix_location) == upgraded
    with sqlite3.connect(prefix_location.database_path) as db:
        after = _schema(db)
        assert all(after[key] == value for key, value in before.items())
        assert _inventory(db) == (78, 142, 5)
        assert all(db.execute(f'SELECT count(*) FROM {table}').fetchone()[0] == 0 for table in TABLES)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    assert set(before) < set(after)
    older_location = CoordinatorStateLocation.from_trusted_root(tmp_path / "prefix-0006")
    older_catalog = migration.MigrationCatalog(full.migrations[:6])
    older = migration._initialize_database_with_catalog(
        older_location, older_catalog, current_app_schema=2,
        verify_managed_invariants=True)
    assert older.current_sequence == 6
    with sqlite3.connect(older_location.database_path) as db:
        older_schema = _schema(db)
        assert _inventory(db) == (68, 122, 5)
    upgraded_from_0006 = migration.migrate_database(older_location)
    assert upgraded_from_0006.current_sequence == upgraded_from_0006.latest_sequence == 8
    with sqlite3.connect(older_location.database_path) as db:
        complete_schema = _schema(db)
        assert all(complete_schema[key] == value for key, value in older_schema.items())
        assert _inventory(db) == (78, 142, 5)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_0008_old_binary_and_divergent_schema_refusal(tmp_path):
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "old-binary")
    migration.initialize_database(location)
    old_catalog = migration.MigrationCatalog(migration.load_migration_catalog().migrations[:7])
    old_inspection = migration._assess_location_database(
        location, old_catalog, current_app_schema=2,
        verify_managed_invariants=True)
    assert old_inspection.disposition is migration._MigrationDatabaseDisposition.NEWER_UNSUPPORTED
    assert old_inspection.reason is SQLiteStateErrorCode.DATABASE_SCHEMA_TOO_NEW
    with sqlite3.connect(location.database_path) as db:
        db.execute("CREATE TABLE foreign_terminal_suggestion (id INTEGER)")
    assert migration.validate_database(location).classification is migration.DatabaseClassification.UNKNOWN
    with pytest.raises(Exception):
        with acquire_sqlite_writer_session(location):
            pass


@pytest.mark.parametrize("obsolete_checksum", (
    "1937a95ff5d9c18b33af9b1edc352804085ff83d8b5582dcb5f856d4306e8847",
    "5bd540def9028d09c4e2100f61f449acfb3a5c914fa554f47975d8c773d4cd20",
))
def test_0008_blocked_candidate_checksum_is_not_supported_history(tmp_path, obsolete_checksum):
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "blocked-0008")
    migration.initialize_database(location)
    with sqlite3.connect(location.database_path) as db:
        trigger = db.execute("SELECT sql FROM sqlite_schema WHERE name='schema_migrations_no_update'").fetchone()[0]
        db.execute("DROP TRIGGER schema_migrations_no_update")
        db.execute("UPDATE schema_migrations SET schema_digest=? WHERE sequence=8", (
            obsolete_checksum,))
        db.execute(trigger)
    assert migration.validate_database(location).classification is migration.DatabaseClassification.UNKNOWN
    with pytest.raises(Exception):
        with acquire_sqlite_writer_session(location):
            pass


def test_0008_all_recorded_at_columns_enforce_calendar_and_ascii_bytes(monkeypatch):
    """Direct SQL inserts isolate each timestamp CHECK with real parent rows."""
    valid = (
        "0001-01-01T00:00:00Z", "9999-12-31T23:59:59Z",
        "2000-02-29T12:00:00Z", "2024-02-29T12:00:00Z",
        "1900-02-28T23:59:59Z", "2100-02-28T23:59:59Z",
        "2026-01-31T12:00:00Z", "2026-04-30T12:00:00Z",
        "2026-12-31T23:59:59Z",
    )
    invalid = (
        "2026-13-27T12:00:00Z", "2026-00-27T12:00:00Z",
        "2026-00-00T12:00:00Z", "2026-01-00T12:00:00Z",
        "2026-01-32T12:00:00Z", "2026-02-29T12:00:00Z",
        "2024-02-30T12:00:00Z", "2026-04-31T12:00:00Z",
        "1900-02-29T12:00:00Z", "2100-02-29T12:00:00Z",
        "0000-01-01T00:00:00Z", "2026-01-01T24:00:00Z",
        "2026-01-01T25:00:00Z", "2026-01-01T12:60:00Z",
        "2026-01-01T12:00:60Z", "2026-01-01T12:00:00.0Z",
        "2026-01-01T12:00:00+00:00", " 2026-01-01T12:00:00Z",
        "2026-01-01T12:00:00z", "２０２６-01-01T12:00:00Z",
        "2026-01-01T12:00:00Z\x00", "2026-01-01T12:00:\x0000Z",
        None, 20260101120000, True, b"2026-01-01T12:00:00Z",
    )
    timestamp_tables = ("rw0_terminal_contexts", "rw0_terminal_results",
                        "rw0_terminal_receipts")
    with prepared_normal_case(monkeypatch) as (location, command, source, _):
        with closing(sqlite3.connect(":memory:")) as synthetic:
            with closing(sqlite3.connect(location.database_path)) as before:
                before.backup(synthetic)
            synthetic.execute("PRAGMA foreign_keys=ON")
            assert synthetic.execute("PRAGMA foreign_keys").fetchone() == (1,)
            with acquire_sqlite_writer_session(location) as writer:
                assert writer._record_terminal_outcome(command, source).outcome == "accept"
            with closing(sqlite3.connect(location.database_path)) as committed:
                base = {table: committed.execute(f"SELECT * FROM {table}").fetchone()
                        for table in TABLES}
            assert all(row is not None for row in base.values())
            columns = {table: tuple(row[1] for row in synthetic.execute(
                f'PRAGMA table_xinfo("{table}")')) for table in TABLES}
            inserts = {table: f"INSERT INTO {table} ({', '.join(columns[table])}) "
                      f"VALUES ({', '.join('?' for _ in columns[table])})"
                      for table in TABLES}

            def attempt(table, timestamp):
                synthetic.execute("SAVEPOINT timestamp_case")
                try:
                    for parent in TABLES[:TABLES.index(table)]:
                        synthetic.execute(inserts[parent], base[parent])
                    values = list(base[table])
                    values[columns[table].index("recorded_at")] = timestamp
                    try:
                        synthetic.execute(inserts[table], values)
                    except sqlite3.IntegrityError:
                        assert synthetic.execute(
                            f"SELECT count(*) FROM {table}").fetchone() == (0,)
                        return False
                    assert synthetic.execute(
                        f"SELECT count(*) FROM {table}").fetchone() == (1,)
                    assert synthetic.execute("PRAGMA foreign_key_check").fetchall() == []
                    return True
                finally:
                    synthetic.execute("ROLLBACK TO timestamp_case")
                    synthetic.execute("RELEASE timestamp_case")

            for table in timestamp_tables:
                for value in valid:
                    assert attempt(table, value), (table, value)
                for value in invalid:
                    # The paired valid insert uses the same parent rows, keys,
                    # digests and savepoint arrangement as the negative.
                    assert attempt(table, "2024-02-29T12:00:00Z"), table
                    assert not attempt(table, value), (table, value)
