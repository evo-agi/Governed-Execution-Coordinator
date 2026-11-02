from __future__ import annotations

from copy import deepcopy
import hashlib
import re
import sqlite3
from pathlib import Path

import pytest

import ge_nwp_coordinator.sqlite_migration as sqlite_migration
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import (
    CURRENT_APPLICATION_SCHEMA,
    _migration_statements,
    initialize_database,
    load_migration_catalog,
)
from test_remote_worker_pre_execution_planning_contract import (
    REPAIRED_IMMUTABLE_TABLES,
    REPAIRED_PHASE_ALGEBRA,
    REPAIRED_SELECTION_HEAD_ALL_IMMUTABLE_FIELDS,
    REPAIRED_TABLE_COLUMNS,
    REPAIRED_TABLE_FOREIGN_KEYS,
    REPAIRED_TABLE_ORDER,
    _build_repaired_physical_family,
    _build_repaired_successor_family,
    _insert_exact_c2b3d_parent_rows,
    _insert_exact_repaired_values,
    _install_repaired_temporary_schema,
)


MIGRATION_ID = "0003_cognitive_proposal_and_selection_state"
MIGRATION_SHA256 = "b5c7cac8e074b77ab369579f1f8015f547f1a2776b4b09d612e56280f16c1579"
MIGRATION_SIZE = 161_472
SECTION41_TABLES = (
    "development_model_source_invocations",
    "development_pre_execution_planning_contexts",
    "development_private_proposal_artifact_bindings",
    "development_model_proposals",
    "development_pre_execution_plan_projections",
    "development_model_proposal_evidence_bindings",
    "development_pre_execution_dispositions",
    "development_pre_execution_selection_heads",
    "development_cognitive_mutation_receipts",
)
assert SECTION41_TABLES == REPAIRED_TABLE_ORDER


def _normalized_schema_sql(sql: str) -> str:
    assert type(sql) is str
    return " ".join(sql.split())


def _section41_schema_view(connection: sqlite3.Connection) -> dict[str, object]:
    table_sql = tuple(
        (
            table,
            _normalized_schema_sql(
                connection.execute(
                    "SELECT sql FROM sqlite_schema WHERE type='table' AND name=?",
                    (table,),
                ).fetchone()[0]
            ),
        )
        for table in SECTION41_TABLES
    )
    columns = tuple(
        (
            table,
            tuple(
                tuple(row)
                for row in connection.execute(f'PRAGMA table_xinfo("{table}")')
            ),
        )
        for table in SECTION41_TABLES
    )
    indexes = []
    explicit_indexes = []
    for table in SECTION41_TABLES:
        table_indexes = []
        for _sequence, name, unique, origin, partial in connection.execute(
            f'PRAGMA index_list("{table}")'
        ):
            index_columns = tuple(
                row[2]
                for row in connection.execute(f'PRAGMA index_info("{name}")')
            )
            table_indexes.append((unique, origin, partial, index_columns))
            sql_row = connection.execute(
                "SELECT sql FROM sqlite_schema WHERE type='index' AND name=?",
                (name,),
            ).fetchone()
            if sql_row is not None and sql_row[0] is not None:
                explicit_indexes.append(
                    (table, name, _normalized_schema_sql(sql_row[0]))
                )
        indexes.append((table, tuple(sorted(table_indexes, key=repr))))
    foreign_keys = tuple(
        (
            table,
            tuple(
                tuple(row)
                for row in connection.execute(
                    f'PRAGMA foreign_key_list("{table}")'
                )
            ),
        )
        for table in SECTION41_TABLES
    )
    triggers = tuple(
        (name, table, _normalized_schema_sql(sql))
        for name, table, sql in connection.execute(
            "SELECT name, tbl_name, sql FROM sqlite_schema WHERE type='trigger' "
            "AND tbl_name IN ("
            + ",".join("?" for _table in SECTION41_TABLES)
            + ") ORDER BY name",
            SECTION41_TABLES,
        )
    )
    seed_counts = tuple(
        (
            table,
            connection.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0],
        )
        for table in SECTION41_TABLES
    )
    return {
        "tables": table_sql,
        "columns": columns,
        "indexes": tuple(indexes),
        "explicit_indexes": tuple(explicit_indexes),
        "foreign_keys": foreign_keys,
        "foreign_key_posture_counts": tuple(
            (
                table,
                sql.lower().count("not deferrable initially immediate"),
            )
            for table, sql in table_sql
        ),
        "check_counts": tuple(
            (table, sql.lower().count("check(")) for table, sql in table_sql
        ),
        "triggers": triggers,
        "seed_counts": seed_counts,
    }


def _install_raw_packaged_schema() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    migration_root = (
        Path(__file__).parents[1]
        / "src"
        / "ge_nwp_coordinator"
        / "sqlite_migrations"
    )
    for resource in (
        "0001_initial.sql",
        "0002_development_program_and_effect_state.sql",
        "0003_cognitive_proposal_and_selection_state.sql",
    ):
        sql_bytes = (migration_root / resource).read_bytes()
        connection.executescript(sql_bytes.decode("utf-8"))
    return connection


def _open_production_schema(tmp_path: Path, name: str) -> sqlite3.Connection:
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / name)
    initialize_database(location)
    connection = sqlite3.connect(location.database_path)
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def test_catalog_identity_and_literal_sql_statement_inventory() -> None:
    catalog = load_migration_catalog()
    assert tuple(item.sequence for item in catalog.migrations) == (1, 2, 3, 4, 5, 6, 7, 8, 9)
    migration = catalog.by_sequence(3)
    assert migration.migration_id == MIGRATION_ID
    assert migration.sequence == 3
    assert migration.min_app_schema == migration.max_app_schema == 2
    assert migration.destructive is False
    assert len(migration.sql_bytes) == MIGRATION_SIZE
    assert hashlib.sha256(migration.sql_bytes).hexdigest() == MIGRATION_SHA256
    statements = _migration_statements(migration.sql_text)
    assert len(statements) == 27
    assert (
        sum(
            statement.lstrip().upper().startswith("CREATE TABLE")
            for statement in statements
        )
        == 9
    )
    assert (
        sum(
            statement.lstrip().upper().startswith("CREATE TRIGGER")
            for statement in statements
        )
        == 18
    )
    statement_prefixes = tuple(statement.lstrip().upper() for statement in statements)
    assert not any(
        statement.startswith(("BEGIN", "COMMIT", "ROLLBACK", "PRAGMA"))
        for statement in statement_prefixes
    )
    assert not any(
        statement.startswith("CREATE VIEW") for statement in statement_prefixes
    )
    assert not any(
        statement.startswith("CREATE INDEX") for statement in statement_prefixes
    )
    assert not any(
        statement.startswith("INSERT INTO") for statement in statement_prefixes
    )


def test_generation_two_fresh_database_has_exact_cumulative_inventory(
    tmp_path: Path,
) -> None:
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "state")
    initialize_database(location)
    connection = sqlite3.connect(location.database_path)
    try:
        tables = tuple(
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        )
        triggers = tuple(
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'trigger' ORDER BY name"
            )
        )
        explicit_indexes = tuple(
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'index' "
                "AND sql IS NOT NULL ORDER BY name"
            )
        )
        columns = sum(
            len(connection.execute(f'PRAGMA table_info("{table}")').fetchall())
            for table in tables
        )
        foreign_keys = sum(
            len(
                {
                    row[0]
                    for row in connection.execute(
                        f'PRAGMA foreign_key_list("{table}")'
                    ).fetchall()
                }
            )
            for table in tables
        )
        history = connection.execute(
            "SELECT sequence, migration_id, schema_digest, min_app_schema, "
            "max_app_schema FROM schema_migrations ORDER BY sequence"
        ).fetchall()
        seed_count = sum(
            connection.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
            for table in SECTION41_TABLES
        )
    finally:
        connection.close()
    assert len(tables) == 79
    assert columns == 1814
    assert foreign_keys == 242
    assert len(triggers) == 146
    assert len(explicit_indexes) == 5
    assert seed_count == 0
    assert history[-1] == (
        9,
        "0009_rw0_terminal_anchor_registry",
        "ee9a063b4974bffee39af691dc059535172f189e89d96789befe716cd89b3d25",
        2,
        2,
    )
    assert CURRENT_APPLICATION_SCHEMA == 2


def test_migrations_0001_and_0002_remain_byte_exact() -> None:
    catalog = load_migration_catalog()
    assert tuple(
        (item.migration_id, item.checksum) for item in catalog.migrations[:2]
    ) == (
        (
            "0001_initial",
            "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148",
        ),
        (
            "0002_development_program_and_effect_state",
            "5859f49994b1467db71911fb60db4f1cfc562af7517dc6e4d81b5b29ca44d56c",
        ),
    )


def test_raw_production_and_independent_oracle_have_exact_section41_schema(
    tmp_path: Path,
) -> None:
    raw = _install_raw_packaged_schema()
    production = _open_production_schema(tmp_path, "production-schema")
    oracle, inventory = _install_repaired_temporary_schema(
        seed_c2b3d_parents=False
    )
    try:
        raw_view = _section41_schema_view(raw)
        production_view = _section41_schema_view(production)
        oracle_view = _section41_schema_view(oracle)
        assert raw_view == production_view == oracle_view
        assert tuple(table for table, _sql in raw_view["tables"]) == SECTION41_TABLES
        assert len(raw_view["triggers"]) == 18
        assert raw_view["explicit_indexes"] == ()
        assert all(count == 0 for _table, count in raw_view["seed_counts"])
        assert all(count > 0 for _table, count in raw_view["check_counts"])
        assert sum(
            count for _table, count in raw_view["foreign_key_posture_counts"]
        ) == sum(len(specifications) for specifications in REPAIRED_TABLE_FOREIGN_KEYS.values())
        assert inventory["added_tables"] == 9
        assert inventory["added_triggers"] == 18
        assert inventory["added_explicit_indexes"] == 0
    finally:
        raw.close()
        production.close()
        oracle.close()


def test_statement_count_preserving_parser_mutant_is_caught_by_independent_views(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_parser = sqlite_migration._migration_statements
    mutated_statement_count = 0

    def weakened_parser(sql_text: str) -> tuple[str, ...]:
        nonlocal mutated_statement_count
        statements = original_parser(sql_text)
        if "development_pre_execution_selection_heads" not in sql_text:
            return statements
        target = 'CHECK(typeof("schema_id")=\'text\''
        weakened = list(statements)
        matches = 0
        for index, statement in enumerate(weakened):
            if statement.lstrip().startswith(
                'CREATE TABLE "development_model_source_invocations"'
            ):
                assert statement.count(target) == 1
                weakened[index] = statement.replace(
                    target, 'CHECK(1 OR typeof("schema_id")=\'text\'', 1
                )
                matches += 1
        assert matches == 1
        assert len(weakened) == len(statements) == 27
        mutated_statement_count = len(weakened)
        return tuple(weakened)

    monkeypatch.setattr(sqlite_migration, "_migration_statements", weakened_parser)
    production = _open_production_schema(tmp_path, "mutant-production-schema")
    raw = _install_raw_packaged_schema()
    oracle, _inventory = _install_repaired_temporary_schema(
        seed_c2b3d_parents=False
    )
    try:
        raw_view = _section41_schema_view(raw)
        production_view = _section41_schema_view(production)
        oracle_view = _section41_schema_view(oracle)
        assert mutated_statement_count == 27
        assert raw_view == oracle_view
        assert production_view != raw_view
        assert production_view["columns"] == raw_view["columns"]
        assert production_view["indexes"] == raw_view["indexes"]
        assert production_view["foreign_keys"] == raw_view["foreign_keys"]
        assert production_view["triggers"] == raw_view["triggers"]
        differing_tables = tuple(
            table
            for (table, production_sql), (raw_table, raw_sql) in zip(
                production_view["tables"], raw_view["tables"], strict=True
            )
            if production_sql != raw_sql and table == raw_table
        )
        assert differing_tables == ("development_model_source_invocations",)
    finally:
        production.close()
        raw.close()
        oracle.close()


def _insert_family_prefix(
    connection: sqlite3.Connection,
    family: dict[str, object],
    target_table: str,
) -> dict[str, object]:
    for member in family["physical_rows"]:
        if member["table"] == target_table:
            return deepcopy(member["values"])
        _insert_exact_repaired_values(
            connection, member["table"], member["values"]
        )
    raise AssertionError(target_table)


def _invalid_check_value(kind: str) -> object:
    if (
        kind.startswith("int:")
        or kind.startswith("literal_int:")
        or kind
        in {
            "bool_int",
            "nonnegative_int",
            "nullable_nonnegative_int",
            "phase_evidence_rank",
            "positive_int",
            "selection_prior_revision",
        }
    ):
        return "not-an-integer"
    return 0


def _assert_check_rejects(
    connection: sqlite3.Connection,
    family: dict[str, object],
    table: str,
    updates: dict[str, object],
    *,
    label: object,
) -> None:
    mapping = _insert_family_prefix(connection, family, table)
    mapping.update(updates)
    with pytest.raises(sqlite3.IntegrityError) as caught:
        _insert_exact_repaired_values(connection, table, mapping)
    assert caught.value.sqlite_errorname == "SQLITE_CONSTRAINT_CHECK", label
    connection.rollback()


def _alternate_foreign_key_value(value: object) -> object:
    if type(value) is int:
        return value + 1
    assert type(value) is str
    if len(value) == 64:
        return ("f" if value[0] != "f" else "e") + value[1:]
    candidate = value + ".foreign"
    if len(candidate.encode("utf-8")) <= 96:
        return candidate
    return value[:-1] + ("x" if value[-1] != "x" else "y")


def test_production_schema_rejects_every_section41_check_and_foreign_key_class(
    tmp_path: Path,
) -> None:
    connection = _open_production_schema(tmp_path, "production-negatives")
    connection.execute("PRAGMA foreign_keys=ON")
    _insert_exact_c2b3d_parent_rows(connection)
    connection.commit()
    root = _build_repaired_physical_family(False)
    successor = _build_repaired_successor_family(
        root, suffix="migration-negative-successor"
    )
    try:
        checked_columns = []
        for table in SECTION41_TABLES:
            member = next(
                item for item in root["physical_rows"] if item["table"] == table
            )
            for field, kind in REPAIRED_TABLE_COLUMNS[table]:
                _assert_check_rejects(
                    connection,
                    root,
                    table,
                    {field: _invalid_check_value(kind)},
                    label=(table, field, kind),
                )
                checked_columns.append((table, field))
        assert len(checked_columns) == sum(
            len(columns) for columns in REPAIRED_TABLE_COLUMNS.values()
        )

        post = REPAIRED_PHASE_ALGEBRA["post_execution_semantic_review"]
        phase_and_relational_cases = (
            (
                SECTION41_TABLES[0],
                {"context_schema_id": post["context_schema_id"]},
                "source-phase",
            ),
            (
                SECTION41_TABLES[2],
                {"artifact_schema_id": post["private_artifact_schema_id"]},
                "artifact-phase",
            ),
            (
                SECTION41_TABLES[3],
                {"recommendation": post["recommendations"][0]},
                "proposal-phase",
            ),
            (
                SECTION41_TABLES[5],
                {
                    "evidence_role": post["evidence_roles"][0][0],
                    "role_rank": post["evidence_roles"][0][1],
                    "required_for_selection": int(post["evidence_roles"][0][2]),
                },
                "evidence-phase",
            ),
            (
                SECTION41_TABLES[6],
                {
                    "disposition_ref": next(
                        item["values"]["proposal_ref"]
                        for item in root["physical_rows"]
                        if item["table"] == SECTION41_TABLES[6]
                    )
                },
                "proposal-disposition-noncollapse",
            ),
            (
                SECTION41_TABLES[6],
                {"expected_selection_head_revision": 0},
                "root-or-successor",
            ),
        )
        for table, updates, label in phase_and_relational_cases:
            _assert_check_rejects(
                connection, root, table, updates, label=label
            )

        observed_foreign_keys = []
        column_kinds = {
            table: dict(columns)
            for table, columns in REPAIRED_TABLE_COLUMNS.items()
        }
        for table, specifications in REPAIRED_TABLE_FOREIGN_KEYS.items():
            for relation_index, specification in enumerate(specifications):
                child_columns, parent_table, _parent_columns, timing = specification
                assert timing == "IMMEDIATE"
                if table == parent_table:
                    for member in root["physical_rows"]:
                        _insert_exact_repaired_values(
                            connection, member["table"], member["values"]
                        )
                    mapping = _insert_family_prefix(
                        connection, successor, table
                    )
                else:
                    mapping = _insert_family_prefix(connection, root, table)
                field = next(
                    (
                        name
                        for name in reversed(child_columns)
                        if name.endswith("_ref") and mapping[name] is not None
                    ),
                    child_columns[-1],
                )
                assert field in column_kinds[table]
                mapping[field] = _alternate_foreign_key_value(mapping[field])
                with pytest.raises(sqlite3.IntegrityError) as caught:
                    _insert_exact_repaired_values(connection, table, mapping)
                assert caught.value.sqlite_errorname == (
                    "SQLITE_CONSTRAINT_FOREIGNKEY"
                ), (table, relation_index, field)
                observed_foreign_keys.append((table, relation_index))
                connection.rollback()
        assert len(observed_foreign_keys) == sum(
            len(specifications)
            for specifications in REPAIRED_TABLE_FOREIGN_KEYS.values()
        )
    finally:
        connection.close()


def test_production_schema_rejects_every_section41_trigger_class(
    tmp_path: Path,
) -> None:
    connection = _open_production_schema(tmp_path, "production-triggers")
    connection.execute("PRAGMA foreign_keys=ON")
    _insert_exact_c2b3d_parent_rows(connection)
    family = _build_repaired_physical_family(False)
    for member in family["physical_rows"]:
        _insert_exact_repaired_values(
            connection, member["table"], member["values"]
        )
    connection.commit()
    before_counts = tuple(
        connection.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
        for table in SECTION41_TABLES
    )
    try:
        for table in REPAIRED_IMMUTABLE_TABLES:
            with pytest.raises(sqlite3.IntegrityError) as update_failure:
                connection.execute(
                    f'UPDATE "{table}" SET "schema_id"="schema_id"'
                )
            assert update_failure.value.sqlite_errorname == (
                "SQLITE_CONSTRAINT_TRIGGER"
            ), (table, "update")
            assert str(update_failure.value) == f"immutable_{table}"
            with pytest.raises(sqlite3.IntegrityError) as delete_failure:
                connection.execute(f'DELETE FROM "{table}"')
            assert delete_failure.value.sqlite_errorname == (
                "SQLITE_CONSTRAINT_TRIGGER"
            ), (table, "delete")
            assert str(delete_failure.value) == f"immutable_{table}"

        head_table = SECTION41_TABLES[7]
        with pytest.raises(sqlite3.IntegrityError) as head_delete_failure:
            connection.execute(f'DELETE FROM "{head_table}"')
        assert head_delete_failure.value.sqlite_errorname == (
            "SQLITE_CONSTRAINT_TRIGGER"
        )
        assert str(head_delete_failure.value) == "append_only_selection_head"
        assert "program_version_number" in REPAIRED_SELECTION_HEAD_ALL_IMMUTABLE_FIELDS
        with pytest.raises(sqlite3.IntegrityError) as lineage_failure:
            connection.execute(
                f'UPDATE "{head_table}" SET '
                '"program_version_number"="program_version_number"+1'
            )
        assert lineage_failure.value.sqlite_errorname == (
            "SQLITE_CONSTRAINT_TRIGGER"
        )
        assert str(lineage_failure.value) == "immutable_selection_head_lineage"
        after_counts = tuple(
            connection.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
            for table in SECTION41_TABLES
        )
        assert after_counts == before_counts
    finally:
        connection.rollback()
        connection.close()
