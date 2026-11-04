from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

import ge_nwp_coordinator.sqlite_migration as migration
from ge_nwp_coordinator._rw0_c1_row_values import ROW_SPECS
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation


MIGRATION_ID = "0004_rw0_c1_durable_evidence"
MIGRATION_SHA256 = "967b9c2deb43da625f9ce82d43c9538bfd2fa27c02f3abdfcb12eb3a2aef8cec"
MIGRATION_SIZE = 289_058
RW0_C1_TABLES = (
    "rw0_phase_instances",
    "rw0_evidence_values",
    "rw0_evidence_memberships",
    "rw0_relation_bindings",
    "rw0_relation_operands",
    "rw0_c1_mutation_receipts",
    "rw0_authority_verification_observations",
    "rw0_subordinate_authorization_proposals",
    "rw0_custody_availability_observations",
    "rw0_retrieval_capability_event_observations",
    "rw0_remote_host_readiness_observations",
    "rw0_effect_host_qualifications",
    "rw0_worker_mechanism_capability_declarations",
    "rw0_worker_mechanism_capability_observations",
    "rw0_worker_mechanism_capability_qualifications",
    "rw0_wire_cancellation_request_observations",
    "rw0_wire_process_observations",
    "rw0_c2a_worker_observations",
    "rw0_wire_worker_result_bindings",
    "rw0_wire_process_result_classification_bindings",
    "rw0_section41_post_execution_proposal_family_members",
    "rw0_authority_observation_effect_classes",
    "rw0_c2a_worker_observation_evidence_refs",
)
RW0_C1_INDEXES = (
    "idx_rw0_phase_instances_k8_lookup",
    "idx_rw0_evidence_memberships_phase_kind_page",
    "idx_rw0_relation_operands_c1_membership_lookup",
    "idx_rw0_c1_mutation_receipts_phase_family_lookup",
)


def _location(tmp_path: Path, suffix: str) -> CoordinatorStateLocation:
    return CoordinatorStateLocation.from_trusted_root(tmp_path / suffix)


def _inventory(location: CoordinatorStateLocation) -> tuple[int, int, int]:
    connection = sqlite3.connect(location.database_path)
    try:
        tables = connection.execute(
            "SELECT count(*) FROM sqlite_schema WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        ).fetchone()[0]
        triggers = connection.execute(
            "SELECT count(*) FROM sqlite_schema WHERE type='trigger'"
        ).fetchone()[0]
        indexes = connection.execute(
            "SELECT count(*) FROM sqlite_schema WHERE type='index' "
            "AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL"
        ).fetchone()[0]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        return tables, triggers, indexes
    finally:
        connection.close()


def test_catalog_identity_and_literal_statement_inventory() -> None:
    catalog = migration.load_migration_catalog()
    assert tuple(item.sequence for item in catalog.migrations) == tuple(range(1, 11))
    item = catalog.migrations[3]  # frozen 0004 oracle inside the current catalog
    assert item.migration_id == MIGRATION_ID
    assert item.sequence == 4
    assert item.min_app_schema == item.max_app_schema == 2
    assert item.destructive is False
    assert len(item.sql_bytes) == MIGRATION_SIZE
    assert hashlib.sha256(item.sql_bytes).hexdigest() == MIGRATION_SHA256
    statements = migration._migration_statements(item.sql_text)
    assert len(statements) == 73
    prefixes = tuple(statement.lstrip().upper() for statement in statements)
    assert sum(value.startswith("CREATE TABLE") for value in prefixes) == 23
    assert sum(value.startswith("CREATE TRIGGER") for value in prefixes) == 46
    assert sum(
        value.startswith("CREATE INDEX")
        or value.startswith("CREATE UNIQUE INDEX")
        for value in prefixes
    ) == 4
    assert not any(
        value.startswith(("BEGIN", "COMMIT", "ROLLBACK", "PRAGMA", "INSERT"))
        for value in prefixes
    )


def test_fresh_generation_two_database_has_exact_rw0_c1_and_cumulative_inventory(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path, "fresh")
    inspection = migration.initialize_database(location)
    assert inspection.current_sequence == inspection.latest_sequence == 10
    assert migration.CURRENT_APPLICATION_SCHEMA == 2
    assert _inventory(location) == (85, 159, 5)
    connection = sqlite3.connect(location.database_path)
    try:
        tables = tuple(
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type='table' "
                "AND name LIKE 'rw0_%' ORDER BY name"
            )
        )
        p0_tables = {
            "rw0_c2_verified_admission_acts",
            "rw0_c2_scope_admission_facts",
            "rw0_c2_scope_admission_recording_bases",
            "rw0_c2_scope_admission_recording_receipts",
        }
        p1_tables = {
            "rw0_c2_historical_continuity_bases",
            "rw0_c2_historical_sole_active_bases",
            "rw0_c2_decision_bases",
            "rw0_c2_guarded_family_relations",
            "rw0_c2_guarded_progression_results",
            "rw0_c2_bootstrap_acceptance_facts",
        }
        terminal_tables = {
            "rw0_terminal_contexts", "rw0_terminal_outcomes",
            "rw0_terminal_results", "rw0_terminal_receipts",
        }
        cancel_tables = {
            "rw0_cancel_decision_evidence_bindings", "rw0_cancel_decision_receipts",
            "rw0_cancel_pre_effect_contexts", "rw0_cancel_pre_effect_outcomes",
            "rw0_cancel_pre_effect_results", "rw0_cancel_pre_effect_receipts",
        }
        assert set(tables) == set(RW0_C1_TABLES) | p0_tables | p1_tables | terminal_tables | cancel_tables | {"rw0_terminal_anchors"}
        assert all(
            connection.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
            == 0
            for table in (*RW0_C1_TABLES, *p0_tables, *p1_tables, *terminal_tables, *cancel_tables, "rw0_terminal_anchors")
        )
        trigger_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type='trigger' "
                "AND tbl_name LIKE 'rw0_%'"
            )
        }
        assert trigger_names == {
            f"{table}_{operation}"
            for table in (*RW0_C1_TABLES, *p0_tables, *p1_tables, *terminal_tables, *cancel_tables)
            for operation in ("no_update", "no_delete")
        } | {"rw0_terminal_anchors_no_update", "rw0_terminal_anchors_no_delete",
             "rw0_terminal_anchors_require_registered_family", "rw0_terminal_receipts_register_anchor",
             "rw0_cancel_pre_effect_receipts_register_anchor"}
        index_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type='index' "
                "AND name LIKE 'idx_rw0_%' AND sql IS NOT NULL"
            )
        }
        assert index_names == set(RW0_C1_INDEXES)
        assert all(
            " strict" in connection.execute(
                "SELECT lower(sql) FROM sqlite_schema "
                "WHERE type='table' AND name=?",
                (table,),
            ).fetchone()[0]
            for table in RW0_C1_TABLES
        )
        assert tuple(spec.table_name for spec in ROW_SPECS) == RW0_C1_TABLES
        for spec in ROW_SPECS:
            observed_columns = tuple(
                row[1]
                for row in connection.execute(
                    f'PRAGMA table_xinfo("{spec.table_name}")'
                )
            )
            assert observed_columns == spec.columns
    finally:
        connection.close()


@pytest.mark.parametrize("prefix_length", (1, 2, 3))
def test_exact_supported_prefixes_upgrade_to_generation_two_tip(
    tmp_path: Path, prefix_length: int,
) -> None:
    full = migration.load_migration_catalog()
    prefix = migration.MigrationCatalog(full.migrations[:prefix_length])
    location = _location(tmp_path, f"prefix-{prefix_length}")
    migration._initialize_database_with_catalog(
        location,
        prefix,
        current_app_schema=1 if prefix_length == 1 else 2,
        verify_managed_invariants=True,
    )
    upgraded = migration.migrate_database(location)
    assert upgraded.current_sequence == upgraded.latest_sequence == 10
    assert migration.CURRENT_APPLICATION_SCHEMA == 2
    assert _inventory(location) == (85, 159, 5)


def test_migrations_0001_through_0003_retain_frozen_literal_identities() -> None:
    catalog = migration.load_migration_catalog()
    assert tuple(
        (
            item.migration_id,
            len(item.sql_bytes),
            hashlib.sha256(item.sql_bytes).hexdigest(),
        )
        for item in catalog.migrations[:3]
    ) == (
        (
            "0001_initial",
            17_940,
            "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148",
        ),
        (
            "0002_development_program_and_effect_state",
            154_434,
            "5859f49994b1467db71911fb60db4f1cfc562af7517dc6e4d81b5b29ca44d56c",
        ),
        (
            "0003_cognitive_proposal_and_selection_state",
            161_472,
            "b5c7cac8e074b77ab369579f1f8015f547f1a2776b4b09d612e56280f16c1579",
        ),
    )
