"""Independent finite oracle for C2B2 migration 0002 and generation 2."""

from __future__ import annotations

from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

import pytest

import ge_nwp_coordinator.sqlite_migration as migration_module
from ge_nwp_coordinator.sqlite_errors import SQLiteStateError
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation


# This finite 0002 oracle exercises the exact historical generation-2 catalog
# through 0005. Current-tip 0006/0007 coverage belongs to their own physical
# migration suites; the production loader is checked separately below.
_PRODUCTION_CATALOG_LOADER = migration_module.load_migration_catalog


@pytest.fixture(autouse=True)
def _historical_catalog_0005(monkeypatch: pytest.MonkeyPatch) -> None:
    historical = migration_module.MigrationCatalog(
        _PRODUCTION_CATALOG_LOADER().migrations[:5]
    )
    assert tuple(item.sequence for item in historical.migrations) == (1, 2, 3, 4, 5)
    monkeypatch.setattr(migration_module, "load_migration_catalog", lambda: historical)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_0001_PATH = (
    REPOSITORY_ROOT
    / "src"
    / "ge_nwp_coordinator"
    / "sqlite_migrations"
    / "0001_initial.sql"
)
MIGRATION_0002_PATH = (
    REPOSITORY_ROOT
    / "src"
    / "ge_nwp_coordinator"
    / "sqlite_migrations"
    / "0002_development_program_and_effect_state.sql"
)
MIGRATION_0003_PATH = (
    REPOSITORY_ROOT
    / "src"
    / "ge_nwp_coordinator"
    / "sqlite_migrations"
    / "0003_cognitive_proposal_and_selection_state.sql"
)
MIGRATION_0004_PATH = (
    REPOSITORY_ROOT
    / "src"
    / "ge_nwp_coordinator"
    / "sqlite_migrations"
    / "0004_rw0_c1_durable_evidence.sql"
)
MIGRATION_0005_PATH = (
    REPOSITORY_ROOT / "src" / "ge_nwp_coordinator" / "sqlite_migrations"
    / "0005_section41_post_execution_proposal_family.sql"
)
MIGRATION_PACKAGE_PATH = MIGRATION_0002_PATH.parent

EXPECTED_MIGRATION_0001_SHA256 = "1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"
EXPECTED_MIGRATION_ID = "0002_development_program_and_effect_state"
EXPECTED_SEQUENCE = 2
EXPECTED_RESOURCE_NAME = "0002_development_program_and_effect_state.sql"
EXPECTED_SHA256 = "5859f49994b1467db71911fb60db4f1cfc562af7517dc6e4d81b5b29ca44d56c"
SECTION41_MIGRATION_ID = "0003_cognitive_proposal_and_selection_state"
SECTION41_RESOURCE_NAME = "0003_cognitive_proposal_and_selection_state.sql"
SECTION41_SHA256 = "b5c7cac8e074b77ab369579f1f8015f547f1a2776b4b09d612e56280f16c1579"
RW0_C1_MIGRATION_ID = "0004_rw0_c1_durable_evidence"
RW0_C1_RESOURCE_NAME = "0004_rw0_c1_durable_evidence.sql"
RW0_C1_SHA256 = "967b9c2deb43da625f9ce82d43c9538bfd2fa27c02f3abdfcb12eb3a2aef8cec"
CURRENT_MIGRATION_ID = "0005_section41_post_execution_proposal_family"
CURRENT_SEQUENCE = 5
CURRENT_RESOURCE_NAME = "0005_section41_post_execution_proposal_family.sql"
CURRENT_SHA256 = "583c14e2018c84a942e2e72bbb57d24ae39b2470dc4c286c5f775afe1ef9ea87"
SECTION41_TABLE_NAMES = (
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
SECTION41_TRIGGER_NAMES = tuple(
    sorted(
        (
            *(
                name
                for table in SECTION41_TABLE_NAMES
                if table != "development_pre_execution_selection_heads"
                for name in (f"{table}_no_delete", f"{table}_no_update")
            ),
            "development_pre_execution_selection_heads_lineage_immutable",
            "development_pre_execution_selection_heads_no_delete",
        )
    )
)
RW0_C1_TABLE_NAMES = (
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
RW0_C1_TRIGGER_NAMES = tuple(
    sorted(
        trigger
        for table in RW0_C1_TABLE_NAMES
        for trigger in (f"{table}_no_delete", f"{table}_no_update")
    )
)
RW0_C1_INDEX_NAMES = (
    "idx_rw0_phase_instances_k8_lookup",
    "idx_rw0_evidence_memberships_phase_kind_page",
    "idx_rw0_relation_operands_c1_membership_lookup",
    "idx_rw0_c1_mutation_receipts_phase_family_lookup",
)
POST_EXECUTION_TABLE_NAMES = (
    "development_post_execution_proposal_contexts",
    "development_post_execution_proposal_receipts",
)
POST_EXECUTION_TRIGGER_NAMES = tuple(
    f"{table}_no_{operation}"
    for table in POST_EXECUTION_TABLE_NAMES
    for operation in ("update", "delete")
)
EXPECTED_SIZE = 154_434
EXPECTED_COMPATIBILITY = (2, 2)
EXPECTED_DESTRUCTIVE = False
EXPECTED_SQLITE_MINIMUM = (3, 37, 0)
EXPECTED_STATEMENT_COUNT = 50
EXPECTED_CUMULATIVE_TABLE_COUNT = 64
EXPECTED_CUMULATIVE_COLUMN_COUNT = 1518
EXPECTED_CUMULATIVE_TRIGGER_COUNT = 114
EXPECTED_CUMULATIVE_EXPLICIT_INDEX_COUNT = 5
EXPECTED_CUMULATIVE_FOREIGN_KEY_COUNT = 197
EXPECTED_NEW_FOREIGN_KEY_COUNT = 87
EXPECTED_NEW_DEFERRED_FOREIGN_KEY_COUNT = 6
EXPECTED_NEW_COLUMN_COUNT = 362
EXPECTED_NEW_IMMUTABLE_TABLE_COUNT = 15
EXPECTED_NEW_MUTABLE_TABLE_COUNT = 4
EXPECTED_INDEX_SQL = (
    "CREATE UNIQUE INDEX uq_development_effect_intents_author_command\n"
    "ON development_effect_intents(command_ref)\n"
    "WHERE effect_class = 'author_candidate';"
)

EXPECTED_TABLES = ({'name': 'development_program_heads',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-program-head.v1'",
               0),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('current_program_version_ref',
               'ANY',
               False,
               "typeof(current_program_version_ref)='text' AND length(current_program_version_ref) BETWEEN 1 AND 96 "
               "AND substr(current_program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND current_program_version_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(current_program_version_ref,1,instr(current_program_version_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('current_program_version_number',
               'ANY',
               False,
               "typeof(current_program_version_number)='integer' AND current_program_version_number>=1",
               0),
              ('head_revision', 'ANY', False, "typeof(head_revision)='integer' AND head_revision>=0", 0),
              ('program_state',
               'ANY',
               False,
               "typeof(program_state)='text' AND program_state IN ('active','accepted','terminal_rejected','blocked')",
               0),
              ('updated_at',
               'ANY',
               False,
               "typeof(updated_at)='text' AND length(updated_at)=20 AND updated_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(updated_at,1,4) BETWEEN '0001' AND '9999' AND substr(updated_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(updated_at,9,2) BETWEEN '01' AND '31' AND substr(updated_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(updated_at,15,2) BETWEEN '00' AND '59' AND substr(updated_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',updated_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',updated_at)=updated_at",
               0),
              ('head_digest',
               'ANY',
               False,
               "typeof(head_digest)='text' AND length(head_digest)=64 AND head_digest=lower(head_digest) AND "
               "head_digest NOT GLOB '*[^0-9a-f]*'",
               0)),
  'primary_key': ('program_ref',),
  'unique_constraints': (),
  'table_checks': (),
  'mutable': True},
 {'name': 'development_program_versions',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-program-version.v1'",
               0),
              ('program_version_ref',
               'ANY',
               False,
               "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND "
               "substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' "
               "AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('program_version_number',
               'ANY',
               False,
               "typeof(program_version_number)='integer' AND program_version_number>=1",
               0),
              ('program_version_kind',
               'ANY',
               False,
               "typeof(program_version_kind)='text' AND program_version_kind IN "
               "('initial','accepted','repair','replan','terminal_rejected','blocked')",
               0),
              ('creating_decision_ref',
               'ANY',
               False,
               "typeof(creating_decision_ref)='text' AND length(creating_decision_ref) BETWEEN 1 AND 96 AND "
               "substr(creating_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND creating_decision_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(creating_decision_ref,1,instr(creating_decision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('accepted_intent_revision_ref',
               'ANY',
               False,
               "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 "
               "AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('created_at',
               'ANY',
               False,
               "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
               0),
              ('program_version_digest',
               'ANY',
               False,
               "typeof(program_version_digest)='text' AND length(program_version_digest)=64 AND "
               "program_version_digest=lower(program_version_digest) AND program_version_digest NOT GLOB '*[^0-9a-f]*'",
               0)),
  'primary_key': ('program_version_ref',),
  'unique_constraints': (('program_ref', 'program_version_ref'), ('program_ref', 'program_version_number')),
  'table_checks': (('initial_program_version_number',
                    "((program_version_kind='initial' AND program_version_number=1) OR "
                    "(program_version_kind<>'initial' AND program_version_number>=2))"),),
  'mutable': False},
 {'name': 'development_accepted_intent_revisions',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND "
               "schema_id='governed-execution.nwp-development-accepted-intent-revision.v1'",
               0),
              ('accepted_intent_revision_ref',
               'ANY',
               False,
               "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 "
               "AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('accepted_intent_revision_number',
               'ANY',
               False,
               "typeof(accepted_intent_revision_number)='integer' AND accepted_intent_revision_number>=1",
               0),
              ('prior_accepted_intent_revision_ref',
               'ANY',
               True,
               "prior_accepted_intent_revision_ref IS NULL OR (typeof(prior_accepted_intent_revision_ref)='text' AND "
               'length(prior_accepted_intent_revision_ref) BETWEEN 1 AND 96 AND '
               "substr(prior_accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND "
               "prior_accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(prior_accepted_intent_revision_ref,1,instr(prior_accepted_intent_revision_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('source_intent_ref',
               'ANY',
               False,
               "typeof(source_intent_ref)='text' AND length(source_intent_ref) BETWEEN 1 AND 96 AND "
               "substr(source_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND source_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(source_intent_ref,1,instr(source_intent_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('source_intent_digest',
               'ANY',
               False,
               "typeof(source_intent_digest)='text' AND length(source_intent_digest)=64 AND "
               "source_intent_digest=lower(source_intent_digest) AND source_intent_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('safe_projection_digest',
               'ANY',
               False,
               "typeof(safe_projection_digest)='text' AND length(safe_projection_digest)=64 AND "
               "safe_projection_digest=lower(safe_projection_digest) AND safe_projection_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('created_at',
               'ANY',
               False,
               "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
               0),
              ('accepted_intent_revision_digest',
               'ANY',
               False,
               "typeof(accepted_intent_revision_digest)='text' AND length(accepted_intent_revision_digest)=64 AND "
               'accepted_intent_revision_digest=lower(accepted_intent_revision_digest) AND '
               "accepted_intent_revision_digest NOT GLOB '*[^0-9a-f]*'",
               0)),
  'primary_key': ('accepted_intent_revision_ref',),
  'unique_constraints': (('program_ref', 'accepted_intent_revision_ref'),
                         ('program_ref', 'accepted_intent_revision_number')),
  'table_checks': (('accepted_intent_prior_bidirectional',
                    '((accepted_intent_revision_number=1 AND prior_accepted_intent_revision_ref IS NULL) OR '
                    '(accepted_intent_revision_number>=2 AND prior_accepted_intent_revision_ref IS NOT NULL))'),),
  'mutable': False},
 {'name': 'development_work_item_heads',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-work-item-head.v1'",
               0),
              ('work_item_ref',
               'ANY',
               False,
               "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('current_work_item_revision_ref',
               'ANY',
               False,
               "typeof(current_work_item_revision_ref)='text' AND length(current_work_item_revision_ref) BETWEEN 1 AND "
               "96 AND substr(current_work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND "
               "current_work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(current_work_item_revision_ref,1,instr(current_work_item_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('current_work_item_revision_number',
               'ANY',
               False,
               "typeof(current_work_item_revision_number)='integer' AND current_work_item_revision_number>=1",
               0),
              ('head_revision', 'ANY', False, "typeof(head_revision)='integer' AND head_revision>=0", 0),
              ('work_state',
               'ANY',
               False,
               "typeof(work_state)='text' AND work_state IN "
               "('planned','active','accepted','repair_required','terminal_rejected','blocked')",
               0),
              ('updated_at',
               'ANY',
               False,
               "typeof(updated_at)='text' AND length(updated_at)=20 AND updated_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(updated_at,1,4) BETWEEN '0001' AND '9999' AND substr(updated_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(updated_at,9,2) BETWEEN '01' AND '31' AND substr(updated_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(updated_at,15,2) BETWEEN '00' AND '59' AND substr(updated_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',updated_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',updated_at)=updated_at",
               0),
              ('head_digest',
               'ANY',
               False,
               "typeof(head_digest)='text' AND length(head_digest)=64 AND head_digest=lower(head_digest) AND "
               "head_digest NOT GLOB '*[^0-9a-f]*'",
               0)),
  'primary_key': ('work_item_ref',),
  'unique_constraints': (('program_ref', 'work_item_ref'),),
  'table_checks': (),
  'mutable': True},
 {'name': 'development_work_item_revisions',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-work-item-revision.v1'",
               0),
              ('work_item_revision_ref',
               'ANY',
               False,
               "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND "
               "substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('work_item_ref',
               'ANY',
               False,
               "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('work_item_revision_number',
               'ANY',
               False,
               "typeof(work_item_revision_number)='integer' AND work_item_revision_number>=1",
               0),
              ('work_item_revision_kind',
               'ANY',
               False,
               "typeof(work_item_revision_kind)='text' AND work_item_revision_kind IN ('initial','replan')",
               0),
              ('prior_work_item_revision_ref',
               'ANY',
               True,
               "prior_work_item_revision_ref IS NULL OR (typeof(prior_work_item_revision_ref)='text' AND "
               'length(prior_work_item_revision_ref) BETWEEN 1 AND 96 AND substr(prior_work_item_revision_ref,1,1) '
               "GLOB '[0-9A-Za-z]' AND prior_work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(prior_work_item_revision_ref,1,instr(prior_work_item_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('accepted_intent_revision_ref',
               'ANY',
               False,
               "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 "
               "AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('created_at',
               'ANY',
               False,
               "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
               0),
              ('work_item_revision_digest',
               'ANY',
               False,
               "typeof(work_item_revision_digest)='text' AND length(work_item_revision_digest)=64 AND "
               'work_item_revision_digest=lower(work_item_revision_digest) AND work_item_revision_digest NOT GLOB '
               "'*[^0-9a-f]*'",
               0)),
  'primary_key': ('work_item_revision_ref',),
  'unique_constraints': (('program_ref', 'work_item_ref', 'work_item_revision_ref'),
                         ('program_ref', 'work_item_revision_ref'),
                         ('program_ref', 'work_item_ref', 'work_item_revision_number')),
  'table_checks': (('work_revision_prior_bidirectional',
                    "((work_item_revision_kind='initial' AND work_item_revision_number=1 AND "
                    "prior_work_item_revision_ref IS NULL) OR (work_item_revision_kind='replan' AND "
                    'work_item_revision_number>=2 AND prior_work_item_revision_ref IS NOT NULL))'),),
  'mutable': False},
 {'name': 'development_program_version_work_items',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND "
               "schema_id='governed-execution.nwp-development-program-version-work-item.v1'",
               0),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('program_version_ref',
               'ANY',
               False,
               "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND "
               "substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' "
               "AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               2),
              ('work_item_ref',
               'ANY',
               False,
               "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               3),
              ('work_item_revision_ref',
               'ANY',
               False,
               "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND "
               "substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('membership_ordinal', 'ANY', False, "typeof(membership_ordinal)='integer' AND membership_ordinal>=0", 0),
              ('created_at',
               'ANY',
               False,
               "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
               0),
              ('membership_digest',
               'ANY',
               False,
               "typeof(membership_digest)='text' AND length(membership_digest)=64 AND "
               "membership_digest=lower(membership_digest) AND membership_digest NOT GLOB '*[^0-9a-f]*'",
               0)),
  'primary_key': ('program_ref', 'program_version_ref', 'work_item_ref'),
  'unique_constraints': (('program_ref', 'program_version_ref', 'membership_ordinal'),),
  'table_checks': (),
  'mutable': False},
 {'name': 'development_revision_edges',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-revision-edge.v1'",
               0),
              ('revision_edge_ref',
               'ANY',
               False,
               "typeof(revision_edge_ref)='text' AND length(revision_edge_ref) BETWEEN 1 AND 96 AND "
               "substr(revision_edge_ref,1,1) GLOB '[0-9A-Za-z]' AND revision_edge_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(revision_edge_ref,1,instr(revision_edge_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('relation_key_digest',
               'ANY',
               False,
               "typeof(relation_key_digest)='text' AND length(relation_key_digest)=64 AND "
               "relation_key_digest=lower(relation_key_digest) AND relation_key_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('revision_edge_kind',
               'ANY',
               False,
               "typeof(revision_edge_kind)='text' AND revision_edge_kind IN "
               "('accepted_intent_supersedes','work_item_supersedes','work_item_split','work_item_merge')",
               0),
              ('from_accepted_intent_revision_ref',
               'ANY',
               True,
               "from_accepted_intent_revision_ref IS NULL OR (typeof(from_accepted_intent_revision_ref)='text' AND "
               'length(from_accepted_intent_revision_ref) BETWEEN 1 AND 96 AND '
               "substr(from_accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND from_accepted_intent_revision_ref "
               "NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(from_accepted_intent_revision_ref,1,instr(from_accepted_intent_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('to_accepted_intent_revision_ref',
               'ANY',
               True,
               "to_accepted_intent_revision_ref IS NULL OR (typeof(to_accepted_intent_revision_ref)='text' AND "
               'length(to_accepted_intent_revision_ref) BETWEEN 1 AND 96 AND '
               "substr(to_accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND to_accepted_intent_revision_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(to_accepted_intent_revision_ref,1,instr(to_accepted_intent_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('from_work_item_revision_ref',
               'ANY',
               True,
               "from_work_item_revision_ref IS NULL OR (typeof(from_work_item_revision_ref)='text' AND "
               'length(from_work_item_revision_ref) BETWEEN 1 AND 96 AND substr(from_work_item_revision_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND from_work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(from_work_item_revision_ref,1,instr(from_work_item_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('to_work_item_revision_ref',
               'ANY',
               True,
               "to_work_item_revision_ref IS NULL OR (typeof(to_work_item_revision_ref)='text' AND "
               'length(to_work_item_revision_ref) BETWEEN 1 AND 96 AND substr(to_work_item_revision_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND to_work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(to_work_item_revision_ref,1,instr(to_work_item_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('created_at',
               'ANY',
               False,
               "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
               0),
              ('revision_edge_digest',
               'ANY',
               False,
               "typeof(revision_edge_digest)='text' AND length(revision_edge_digest)=64 AND "
               "revision_edge_digest=lower(revision_edge_digest) AND revision_edge_digest NOT GLOB '*[^0-9a-f]*'",
               0)),
  'primary_key': ('revision_edge_ref',),
  'unique_constraints': (('relation_key_digest',),),
  'table_checks': (('revision_edge_endpoint_algebra',
                    "((revision_edge_kind='accepted_intent_supersedes' AND from_accepted_intent_revision_ref IS NOT "
                    'NULL AND to_accepted_intent_revision_ref IS NOT NULL AND from_work_item_revision_ref IS NULL AND '
                    'to_work_item_revision_ref IS NULL) OR (revision_edge_kind IN '
                    "('work_item_supersedes','work_item_split','work_item_merge') AND "
                    'from_accepted_intent_revision_ref IS NULL AND to_accepted_intent_revision_ref IS NULL AND '
                    'from_work_item_revision_ref IS NOT NULL AND to_work_item_revision_ref IS NOT NULL))'),),
  'mutable': False},
 {'name': 'development_work_spec_bindings',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-work-spec-binding.v1'",
               0),
              ('work_spec_ref',
               'ANY',
               False,
               "typeof(work_spec_ref)='text' AND length(work_spec_ref) BETWEEN 1 AND 96 AND substr(work_spec_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND work_spec_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(work_spec_ref,1,instr(work_spec_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('program_version_ref',
               'ANY',
               False,
               "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND "
               "substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' "
               "AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('accepted_intent_revision_ref',
               'ANY',
               False,
               "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 "
               "AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('work_item_ref',
               'ANY',
               False,
               "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('work_item_revision_ref',
               'ANY',
               False,
               "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND "
               "substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('repository_ref',
               'ANY',
               False,
               "typeof(repository_ref)='text' AND length(repository_ref) BETWEEN 1 AND 96 AND "
               "substr(repository_ref,1,1) GLOB '[0-9A-Za-z]' AND repository_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(repository_ref,1,instr(repository_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('base_git_object_format',
               'ANY',
               False,
               "typeof(base_git_object_format)='text' AND base_git_object_format='sha1'",
               0),
              ('base_git_oid',
               'ANY',
               False,
               "typeof(base_git_oid)='text' AND length(base_git_oid)=40 AND base_git_oid=lower(base_git_oid) AND "
               "base_git_oid NOT GLOB '*[^0-9a-f]*'",
               0),
              ('authorized_paths_json',
               'ANY',
               False,
               "typeof(authorized_paths_json)='text' AND "
               'authorized_paths_json=\'[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"]\'',
               0),
              ('validation_requirement_ref',
               'ANY',
               False,
               "typeof(validation_requirement_ref)='text' AND length(validation_requirement_ref) BETWEEN 1 AND 96 AND "
               "substr(validation_requirement_ref,1,1) GLOB '[0-9A-Za-z]' AND validation_requirement_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND "
               "lower(substr(validation_requirement_ref,1,instr(validation_requirement_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('review_requirement_ref',
               'ANY',
               False,
               "typeof(review_requirement_ref)='text' AND length(review_requirement_ref) BETWEEN 1 AND 96 AND "
               "substr(review_requirement_ref,1,1) GLOB '[0-9A-Za-z]' AND review_requirement_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(review_requirement_ref,1,instr(review_requirement_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('privacy_classification',
               'ANY',
               False,
               "typeof(privacy_classification)='text' AND privacy_classification='private_work_spec'",
               0),
              ('work_spec_digest',
               'ANY',
               False,
               "typeof(work_spec_digest)='text' AND length(work_spec_digest)=64 AND "
               "work_spec_digest=lower(work_spec_digest) AND work_spec_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('safe_projection_digest',
               'ANY',
               False,
               "typeof(safe_projection_digest)='text' AND length(safe_projection_digest)=64 AND "
               "safe_projection_digest=lower(safe_projection_digest) AND safe_projection_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('recorded_at',
               'ANY',
               False,
               "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' "
               "AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' "
               "AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' "
               "AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
               0),
              ('work_spec_binding_digest',
               'ANY',
               False,
               "typeof(work_spec_binding_digest)='text' AND length(work_spec_binding_digest)=64 AND "
               'work_spec_binding_digest=lower(work_spec_binding_digest) AND work_spec_binding_digest NOT GLOB '
               "'*[^0-9a-f]*'",
               0)),
  'primary_key': ('work_spec_ref',),
  'unique_constraints': (('program_ref', 'program_version_ref', 'work_item_ref', 'work_item_revision_ref'),),
  'table_checks': (),
  'mutable': False},
 {'name': 'development_semantic_attempts',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-semantic-attempt.v1'",
               0),
              ('semantic_attempt_ref',
               'ANY',
               False,
               "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND "
               "substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('program_version_ref',
               'ANY',
               False,
               "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND "
               "substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' "
               "AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('accepted_intent_revision_ref',
               'ANY',
               False,
               "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 "
               "AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('work_item_ref',
               'ANY',
               False,
               "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('work_item_revision_ref',
               'ANY',
               False,
               "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND "
               "substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('attempt_number', 'ANY', False, "typeof(attempt_number)='integer' AND attempt_number>=1", 0),
              ('candidate_ref',
               'ANY',
               False,
               "typeof(candidate_ref)='text' AND length(candidate_ref) BETWEEN 1 AND 96 AND substr(candidate_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(candidate_ref,1,instr(candidate_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('attempt_phase', 'ANY', False, "typeof(attempt_phase)='text' AND attempt_phase IN ('established')", 0),
              ('selection_decision_ref',
               'ANY',
               False,
               "typeof(selection_decision_ref)='text' AND length(selection_decision_ref) BETWEEN 1 AND 96 AND "
               "substr(selection_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND selection_decision_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(selection_decision_ref,1,instr(selection_decision_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('created_at',
               'ANY',
               False,
               "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
               0),
              ('semantic_attempt_digest',
               'ANY',
               False,
               "typeof(semantic_attempt_digest)='text' AND length(semantic_attempt_digest)=64 AND "
               'semantic_attempt_digest=lower(semantic_attempt_digest) AND semantic_attempt_digest NOT GLOB '
               "'*[^0-9a-f]*'",
               0)),
  'primary_key': ('semantic_attempt_ref',),
  'unique_constraints': (('program_ref', 'semantic_attempt_ref'),
                         ('program_ref', 'candidate_ref'),
                         ('program_ref', 'work_item_ref', 'attempt_number')),
  'table_checks': (),
  'mutable': False},
 {'name': 'development_attempt_fences',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-attempt-fence.v1'",
               0),
              ('attempt_fence_ref',
               'ANY',
               False,
               "typeof(attempt_fence_ref)='text' AND length(attempt_fence_ref) BETWEEN 1 AND 96 AND "
               "substr(attempt_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(attempt_fence_ref,1,instr(attempt_fence_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('parent_standing_grant_ref',
               'ANY',
               False,
               "typeof(parent_standing_grant_ref)='text' AND length(parent_standing_grant_ref) BETWEEN 1 AND 96 AND "
               "substr(parent_standing_grant_ref,1,1) GLOB '[0-9A-Za-z]' AND parent_standing_grant_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(parent_standing_grant_ref,1,instr(parent_standing_grant_ref,'-'))) "
               "NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('parent_standing_grant_digest',
               'ANY',
               False,
               "typeof(parent_standing_grant_digest)='text' AND length(parent_standing_grant_digest)=64 AND "
               'parent_standing_grant_digest=lower(parent_standing_grant_digest) AND parent_standing_grant_digest NOT '
               "GLOB '*[^0-9a-f]*'",
               0),
              ('attempt_authorization_ref',
               'ANY',
               False,
               "typeof(attempt_authorization_ref)='text' AND length(attempt_authorization_ref) BETWEEN 1 AND 96 AND "
               "substr(attempt_authorization_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_authorization_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(attempt_authorization_ref,1,instr(attempt_authorization_ref,'-'))) "
               "NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('attempt_authorization_digest',
               'ANY',
               False,
               "typeof(attempt_authorization_digest)='text' AND length(attempt_authorization_digest)=64 AND "
               'attempt_authorization_digest=lower(attempt_authorization_digest) AND attempt_authorization_digest NOT '
               "GLOB '*[^0-9a-f]*'",
               0),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('program_version_ref',
               'ANY',
               False,
               "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND "
               "substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' "
               "AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('accepted_intent_revision_ref',
               'ANY',
               False,
               "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 "
               "AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('work_item_ref',
               'ANY',
               False,
               "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('work_item_revision_ref',
               'ANY',
               False,
               "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND "
               "substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('semantic_attempt_ref',
               'ANY',
               False,
               "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND "
               "substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('repository_ref',
               'ANY',
               False,
               "typeof(repository_ref)='text' AND length(repository_ref) BETWEEN 1 AND 96 AND "
               "substr(repository_ref,1,1) GLOB '[0-9A-Za-z]' AND repository_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(repository_ref,1,instr(repository_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('base_git_object_format',
               'ANY',
               False,
               "typeof(base_git_object_format)='text' AND base_git_object_format='sha1'",
               0),
              ('base_git_oid',
               'ANY',
               False,
               "typeof(base_git_oid)='text' AND length(base_git_oid)=40 AND base_git_oid=lower(base_git_oid) AND "
               "base_git_oid NOT GLOB '*[^0-9a-f]*'",
               0),
              ('path_ceiling_json',
               'ANY',
               False,
               "typeof(path_ceiling_json)='text' AND "
               'path_ceiling_json=\'[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"]\'',
               0),
              ('allowed_effect_class_mask',
               'ANY',
               False,
               "typeof(allowed_effect_class_mask)='integer' AND allowed_effect_class_mask BETWEEN 1 AND 31",
               0),
              ('aggregate_max_active_invocations',
               'ANY',
               False,
               "typeof(aggregate_max_active_invocations)='integer' AND aggregate_max_active_invocations>=0",
               0),
              ('aggregate_max_candidate_bytes',
               'ANY',
               False,
               "typeof(aggregate_max_candidate_bytes)='integer' AND aggregate_max_candidate_bytes>=0",
               0),
              ('aggregate_max_changed_files',
               'ANY',
               False,
               "typeof(aggregate_max_changed_files)='integer' AND aggregate_max_changed_files>=0",
               0),
              ('aggregate_max_cost_microusd',
               'ANY',
               False,
               "typeof(aggregate_max_cost_microusd)='integer' AND aggregate_max_cost_microusd>=0",
               0),
              ('aggregate_max_cpu_seconds',
               'ANY',
               False,
               "typeof(aggregate_max_cpu_seconds)='integer' AND aggregate_max_cpu_seconds>=0",
               0),
              ('aggregate_max_deliveries',
               'ANY',
               False,
               "typeof(aggregate_max_deliveries)='integer' AND aggregate_max_deliveries>=0",
               0),
              ('aggregate_max_deployments',
               'ANY',
               False,
               "typeof(aggregate_max_deployments)='integer' AND aggregate_max_deployments>=0",
               0),
              ('aggregate_max_local_commits',
               'ANY',
               False,
               "typeof(aggregate_max_local_commits)='integer' AND aggregate_max_local_commits>=0",
               0),
              ('aggregate_max_memory_bytes',
               'ANY',
               False,
               "typeof(aggregate_max_memory_bytes)='integer' AND aggregate_max_memory_bytes>=0",
               0),
              ('aggregate_max_merges',
               'ANY',
               False,
               "typeof(aggregate_max_merges)='integer' AND aggregate_max_merges>=0",
               0),
              ('aggregate_max_model_input_tokens',
               'ANY',
               False,
               "typeof(aggregate_max_model_input_tokens)='integer' AND aggregate_max_model_input_tokens>=0",
               0),
              ('aggregate_max_model_output_tokens',
               'ANY',
               False,
               "typeof(aggregate_max_model_output_tokens)='integer' AND aggregate_max_model_output_tokens>=0",
               0),
              ('aggregate_max_pull_requests',
               'ANY',
               False,
               "typeof(aggregate_max_pull_requests)='integer' AND aggregate_max_pull_requests>=0",
               0),
              ('aggregate_max_pushes',
               'ANY',
               False,
               "typeof(aggregate_max_pushes)='integer' AND aggregate_max_pushes>=0",
               0),
              ('aggregate_max_wall_seconds',
               'ANY',
               False,
               "typeof(aggregate_max_wall_seconds)='integer' AND aggregate_max_wall_seconds>=0",
               0),
              ('expires_at',
               'ANY',
               False,
               "typeof(expires_at)='text' AND length(expires_at)=20 AND expires_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(expires_at,1,4) BETWEEN '0001' AND '9999' AND substr(expires_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(expires_at,9,2) BETWEEN '01' AND '31' AND substr(expires_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(expires_at,15,2) BETWEEN '00' AND '59' AND substr(expires_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',expires_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',expires_at)=expires_at",
               0),
              ('global_stop_ref',
               'ANY',
               False,
               "typeof(global_stop_ref)='text' AND length(global_stop_ref) BETWEEN 1 AND 96 AND "
               "substr(global_stop_ref,1,1) GLOB '[0-9A-Za-z]' AND global_stop_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(global_stop_ref,1,instr(global_stop_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('global_stop_version',
               'ANY',
               False,
               "typeof(global_stop_version)='integer' AND global_stop_version>=0",
               0),
              ('attempt_fence_digest',
               'ANY',
               False,
               "typeof(attempt_fence_digest)='text' AND length(attempt_fence_digest)=64 AND "
               "attempt_fence_digest=lower(attempt_fence_digest) AND attempt_fence_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('recorded_at',
               'ANY',
               False,
               "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' "
               "AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' "
               "AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' "
               "AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
               0)),
  'primary_key': ('attempt_fence_ref',),
  'unique_constraints': (('program_ref', 'attempt_fence_ref'), ('program_ref', 'semantic_attempt_ref')),
  'table_checks': (),
  'mutable': False},
 {'name': 'development_authority_evaluations',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-authority-evaluation.v1'",
               0),
              ('authority_evaluation_ref',
               'ANY',
               False,
               "typeof(authority_evaluation_ref)='text' AND length(authority_evaluation_ref) BETWEEN 1 AND 96 AND "
               "substr(authority_evaluation_ref,1,1) GLOB '[0-9A-Za-z]' AND authority_evaluation_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(authority_evaluation_ref,1,instr(authority_evaluation_ref,'-'))) "
               "NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('evaluation_scope',
               'ANY',
               False,
               "typeof(evaluation_scope)='text' AND evaluation_scope IN ('attempt','effect')",
               0),
              ('evaluation_subject_ref',
               'ANY',
               False,
               "typeof(evaluation_subject_ref)='text' AND length(evaluation_subject_ref) BETWEEN 1 AND 96 AND "
               "substr(evaluation_subject_ref,1,1) GLOB '[0-9A-Za-z]' AND evaluation_subject_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(evaluation_subject_ref,1,instr(evaluation_subject_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('semantic_attempt_ref',
               'ANY',
               True,
               "semantic_attempt_ref IS NULL OR (typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) "
               "BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('effect_intent_ref',
               'ANY',
               True,
               "effect_intent_ref IS NULL OR (typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 "
               "AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('authority_ref',
               'ANY',
               False,
               "typeof(authority_ref)='text' AND length(authority_ref) BETWEEN 1 AND 96 AND substr(authority_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND authority_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(authority_ref,1,instr(authority_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('authority_digest',
               'ANY',
               False,
               "typeof(authority_digest)='text' AND length(authority_digest)=64 AND "
               "authority_digest=lower(authority_digest) AND authority_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('authority_state',
               'ANY',
               False,
               "typeof(authority_state)='text' AND authority_state IN "
               "('pending','verified','blocked','stale','revoked','expired')",
               0),
              ('reason_code',
               'ANY',
               False,
               "typeof(reason_code)='text' AND length(reason_code) BETWEEN 1 AND 96 AND substr(reason_code,1,1) GLOB "
               "'[a-z]' AND reason_code NOT GLOB '*[^a-z0-9_.-]*'",
               0),
              ('expires_at',
               'ANY',
               True,
               "expires_at IS NULL OR (typeof(expires_at)='text' AND length(expires_at)=20 AND expires_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(expires_at,1,4) BETWEEN '0001' AND '9999' AND substr(expires_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(expires_at,9,2) BETWEEN '01' AND '31' AND substr(expires_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(expires_at,15,2) BETWEEN '00' AND '59' AND substr(expires_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',expires_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',expires_at)=expires_at)",
               0),
              ('evaluated_at',
               'ANY',
               False,
               "typeof(evaluated_at)='text' AND length(evaluated_at)=20 AND evaluated_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(evaluated_at,1,4) BETWEEN '0001' AND '9999' AND substr(evaluated_at,6,2) BETWEEN '01' AND '12' "
               "AND substr(evaluated_at,9,2) BETWEEN '01' AND '31' AND substr(evaluated_at,12,2) BETWEEN '00' AND '23' "
               "AND substr(evaluated_at,15,2) BETWEEN '00' AND '59' AND substr(evaluated_at,18,2) BETWEEN '00' AND "
               "'59' AND strftime('%Y-%m-%dT%H:%M:%SZ',evaluated_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',evaluated_at)=evaluated_at",
               0),
              ('authority_evaluation_digest',
               'ANY',
               False,
               "typeof(authority_evaluation_digest)='text' AND length(authority_evaluation_digest)=64 AND "
               'authority_evaluation_digest=lower(authority_evaluation_digest) AND authority_evaluation_digest NOT '
               "GLOB '*[^0-9a-f]*'",
               0)),
  'primary_key': ('authority_evaluation_ref',),
  'unique_constraints': (('program_ref', 'authority_evaluation_ref'),),
  'table_checks': (('authority_scope_subject_algebra',
                    "((evaluation_scope='attempt' AND semantic_attempt_ref IS NOT NULL AND effect_intent_ref IS NULL "
                    "AND evaluation_subject_ref=semantic_attempt_ref) OR (evaluation_scope='effect' AND "
                    'semantic_attempt_ref IS NULL AND effect_intent_ref IS NOT NULL AND '
                    'evaluation_subject_ref=effect_intent_ref))'),
                   ('authority_expiry_algebra',
                    "((authority_state IN ('verified','expired') AND expires_at IS NOT NULL) OR (authority_state IN "
                    "('pending','blocked','stale','revoked') AND expires_at IS NULL))")),
  'mutable': False},
 {'name': 'development_effect_intents',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-effect-intent.v1'",
               0),
              ('effect_intent_ref',
               'ANY',
               False,
               "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND "
               "substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('program_version_ref',
               'ANY',
               False,
               "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND "
               "substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' "
               "AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('semantic_attempt_ref',
               'ANY',
               False,
               "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND "
               "substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('effect_class',
               'ANY',
               False,
               "typeof(effect_class)='text' AND effect_class IN "
               "('author_candidate','cancel_effect','local_git_commit','review_candidate','validate_candidate')",
               0),
              ('candidate_ref',
               'ANY',
               False,
               "typeof(candidate_ref)='text' AND length(candidate_ref) BETWEEN 1 AND 96 AND substr(candidate_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(candidate_ref,1,instr(candidate_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('command_ref',
               'ANY',
               False,
               "typeof(command_ref)='text' AND length(command_ref) BETWEEN 1 AND 96 AND substr(command_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(command_ref,1,instr(command_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('basis_decision_ref',
               'ANY',
               False,
               "typeof(basis_decision_ref)='text' AND length(basis_decision_ref) BETWEEN 1 AND 96 AND "
               "substr(basis_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND basis_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' "
               "AND lower(substr(basis_decision_ref,1,instr(basis_decision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('cancellation_target_effect_intent_ref',
               'ANY',
               True,
               "cancellation_target_effect_intent_ref IS NULL OR (typeof(cancellation_target_effect_intent_ref)='text' "
               'AND length(cancellation_target_effect_intent_ref) BETWEEN 1 AND 96 AND '
               "substr(cancellation_target_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND "
               "cancellation_target_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(cancellation_target_effect_intent_ref,1,instr(cancellation_target_effect_intent_ref,'-'))) "
               "NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('expected_target_effect_head_revision',
               'ANY',
               True,
               'expected_target_effect_head_revision IS NULL OR '
               "(typeof(expected_target_effect_head_revision)='integer' AND expected_target_effect_head_revision>=0)",
               0),
              ('portable_capsule_digest',
               'ANY',
               True,
               "portable_capsule_digest IS NULL OR (typeof(portable_capsule_digest)='text' AND "
               'length(portable_capsule_digest)=64 AND portable_capsule_digest=lower(portable_capsule_digest) AND '
               "portable_capsule_digest NOT GLOB '*[^0-9a-f]*')",
               0),
              ('created_at',
               'ANY',
               False,
               "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
               0),
              ('effect_intent_digest',
               'ANY',
               False,
               "typeof(effect_intent_digest)='text' AND length(effect_intent_digest)=64 AND "
               "effect_intent_digest=lower(effect_intent_digest) AND effect_intent_digest NOT GLOB '*[^0-9a-f]*'",
               0)),
  'primary_key': ('effect_intent_ref',),
  'unique_constraints': (('program_ref', 'effect_intent_ref'),),
  'table_checks': (('effect_intent_cancellation_algebra',
                    "((effect_class='cancel_effect' AND cancellation_target_effect_intent_ref IS NOT NULL AND "
                    "expected_target_effect_head_revision IS NOT NULL) OR (effect_class<>'cancel_effect' AND "
                    'cancellation_target_effect_intent_ref IS NULL AND expected_target_effect_head_revision IS NULL))'),
                   ('effect_intent_capsule_algebra',
                    "((effect_class='author_candidate' AND portable_capsule_digest IS NULL) OR (effect_class IN "
                    "('validate_candidate','review_candidate','local_git_commit') AND portable_capsule_digest IS NOT "
                    "NULL) OR effect_class='cancel_effect')")),
  'mutable': False},
 {'name': 'development_effect_fences',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-effect-fence.v1'",
               0),
              ('effect_fence_ref',
               'ANY',
               False,
               "typeof(effect_fence_ref)='text' AND length(effect_fence_ref) BETWEEN 1 AND 96 AND "
               "substr(effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(effect_fence_ref,1,instr(effect_fence_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('parent_standing_grant_ref',
               'ANY',
               False,
               "typeof(parent_standing_grant_ref)='text' AND length(parent_standing_grant_ref) BETWEEN 1 AND 96 AND "
               "substr(parent_standing_grant_ref,1,1) GLOB '[0-9A-Za-z]' AND parent_standing_grant_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(parent_standing_grant_ref,1,instr(parent_standing_grant_ref,'-'))) "
               "NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('parent_standing_grant_digest',
               'ANY',
               False,
               "typeof(parent_standing_grant_digest)='text' AND length(parent_standing_grant_digest)=64 AND "
               'parent_standing_grant_digest=lower(parent_standing_grant_digest) AND parent_standing_grant_digest NOT '
               "GLOB '*[^0-9a-f]*'",
               0),
              ('effect_authorization_ref',
               'ANY',
               False,
               "typeof(effect_authorization_ref)='text' AND length(effect_authorization_ref) BETWEEN 1 AND 96 AND "
               "substr(effect_authorization_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_authorization_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(effect_authorization_ref,1,instr(effect_authorization_ref,'-'))) "
               "NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('effect_authorization_digest',
               'ANY',
               False,
               "typeof(effect_authorization_digest)='text' AND length(effect_authorization_digest)=64 AND "
               'effect_authorization_digest=lower(effect_authorization_digest) AND effect_authorization_digest NOT '
               "GLOB '*[^0-9a-f]*'",
               0),
              ('attempt_fence_ref',
               'ANY',
               False,
               "typeof(attempt_fence_ref)='text' AND length(attempt_fence_ref) BETWEEN 1 AND 96 AND "
               "substr(attempt_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(attempt_fence_ref,1,instr(attempt_fence_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('attempt_fence_digest',
               'ANY',
               False,
               "typeof(attempt_fence_digest)='text' AND length(attempt_fence_digest)=64 AND "
               "attempt_fence_digest=lower(attempt_fence_digest) AND attempt_fence_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('program_version_ref',
               'ANY',
               False,
               "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND "
               "substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' "
               "AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('accepted_intent_revision_ref',
               'ANY',
               False,
               "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 "
               "AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('work_item_ref',
               'ANY',
               False,
               "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('work_item_revision_ref',
               'ANY',
               False,
               "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND "
               "substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('semantic_attempt_ref',
               'ANY',
               False,
               "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND "
               "substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('effect_intent_ref',
               'ANY',
               False,
               "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND "
               "substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('effect_class',
               'ANY',
               False,
               "typeof(effect_class)='text' AND effect_class IN "
               "('author_candidate','cancel_effect','local_git_commit','review_candidate','validate_candidate')",
               0),
              ('command_ref',
               'ANY',
               False,
               "typeof(command_ref)='text' AND length(command_ref) BETWEEN 1 AND 96 AND substr(command_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(command_ref,1,instr(command_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('command_digest',
               'ANY',
               False,
               "typeof(command_digest)='text' AND length(command_digest)=64 AND command_digest=lower(command_digest) "
               "AND command_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('candidate_ref',
               'ANY',
               False,
               "typeof(candidate_ref)='text' AND length(candidate_ref) BETWEEN 1 AND 96 AND substr(candidate_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(candidate_ref,1,instr(candidate_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('repository_ref',
               'ANY',
               False,
               "typeof(repository_ref)='text' AND length(repository_ref) BETWEEN 1 AND 96 AND "
               "substr(repository_ref,1,1) GLOB '[0-9A-Za-z]' AND repository_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(repository_ref,1,instr(repository_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('base_git_object_format',
               'ANY',
               False,
               "typeof(base_git_object_format)='text' AND base_git_object_format='sha1'",
               0),
              ('base_git_oid',
               'ANY',
               False,
               "typeof(base_git_oid)='text' AND length(base_git_oid)=40 AND base_git_oid=lower(base_git_oid) AND "
               "base_git_oid NOT GLOB '*[^0-9a-f]*'",
               0),
              ('path_ceiling_json',
               'ANY',
               False,
               "typeof(path_ceiling_json)='text' AND "
               'path_ceiling_json=\'[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"]\'',
               0),
              ('effect_max_active_invocations',
               'ANY',
               False,
               "typeof(effect_max_active_invocations)='integer' AND effect_max_active_invocations>=0",
               0),
              ('effect_max_candidate_bytes',
               'ANY',
               False,
               "typeof(effect_max_candidate_bytes)='integer' AND effect_max_candidate_bytes>=0",
               0),
              ('effect_max_changed_files',
               'ANY',
               False,
               "typeof(effect_max_changed_files)='integer' AND effect_max_changed_files>=0",
               0),
              ('effect_max_cost_microusd',
               'ANY',
               False,
               "typeof(effect_max_cost_microusd)='integer' AND effect_max_cost_microusd>=0",
               0),
              ('effect_max_cpu_seconds',
               'ANY',
               False,
               "typeof(effect_max_cpu_seconds)='integer' AND effect_max_cpu_seconds>=0",
               0),
              ('effect_max_deliveries',
               'ANY',
               False,
               "typeof(effect_max_deliveries)='integer' AND effect_max_deliveries>=0",
               0),
              ('effect_max_deployments',
               'ANY',
               False,
               "typeof(effect_max_deployments)='integer' AND effect_max_deployments>=0",
               0),
              ('effect_max_local_commits',
               'ANY',
               False,
               "typeof(effect_max_local_commits)='integer' AND effect_max_local_commits>=0",
               0),
              ('effect_max_memory_bytes',
               'ANY',
               False,
               "typeof(effect_max_memory_bytes)='integer' AND effect_max_memory_bytes>=0",
               0),
              ('effect_max_merges', 'ANY', False, "typeof(effect_max_merges)='integer' AND effect_max_merges>=0", 0),
              ('effect_max_model_input_tokens',
               'ANY',
               False,
               "typeof(effect_max_model_input_tokens)='integer' AND effect_max_model_input_tokens>=0",
               0),
              ('effect_max_model_output_tokens',
               'ANY',
               False,
               "typeof(effect_max_model_output_tokens)='integer' AND effect_max_model_output_tokens>=0",
               0),
              ('effect_max_pull_requests',
               'ANY',
               False,
               "typeof(effect_max_pull_requests)='integer' AND effect_max_pull_requests>=0",
               0),
              ('effect_max_pushes', 'ANY', False, "typeof(effect_max_pushes)='integer' AND effect_max_pushes>=0", 0),
              ('effect_max_wall_seconds',
               'ANY',
               False,
               "typeof(effect_max_wall_seconds)='integer' AND effect_max_wall_seconds>=0",
               0),
              ('expires_at',
               'ANY',
               False,
               "typeof(expires_at)='text' AND length(expires_at)=20 AND expires_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(expires_at,1,4) BETWEEN '0001' AND '9999' AND substr(expires_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(expires_at,9,2) BETWEEN '01' AND '31' AND substr(expires_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(expires_at,15,2) BETWEEN '00' AND '59' AND substr(expires_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',expires_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',expires_at)=expires_at",
               0),
              ('global_stop_ref',
               'ANY',
               False,
               "typeof(global_stop_ref)='text' AND length(global_stop_ref) BETWEEN 1 AND 96 AND "
               "substr(global_stop_ref,1,1) GLOB '[0-9A-Za-z]' AND global_stop_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(global_stop_ref,1,instr(global_stop_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('global_stop_version',
               'ANY',
               False,
               "typeof(global_stop_version)='integer' AND global_stop_version>=0",
               0),
              ('portable_capsule_digest',
               'ANY',
               True,
               "portable_capsule_digest IS NULL OR (typeof(portable_capsule_digest)='text' AND "
               'length(portable_capsule_digest)=64 AND portable_capsule_digest=lower(portable_capsule_digest) AND '
               "portable_capsule_digest NOT GLOB '*[^0-9a-f]*')",
               0),
              ('cancellation_target_effect_intent_ref',
               'ANY',
               True,
               "cancellation_target_effect_intent_ref IS NULL OR (typeof(cancellation_target_effect_intent_ref)='text' "
               'AND length(cancellation_target_effect_intent_ref) BETWEEN 1 AND 96 AND '
               "substr(cancellation_target_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND "
               "cancellation_target_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(cancellation_target_effect_intent_ref,1,instr(cancellation_target_effect_intent_ref,'-'))) "
               "NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('cancellation_target_effect_fence_ref',
               'ANY',
               True,
               "cancellation_target_effect_fence_ref IS NULL OR (typeof(cancellation_target_effect_fence_ref)='text' "
               'AND length(cancellation_target_effect_fence_ref) BETWEEN 1 AND 96 AND '
               "substr(cancellation_target_effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND "
               "cancellation_target_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(cancellation_target_effect_fence_ref,1,instr(cancellation_target_effect_fence_ref,'-'))) "
               "NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('cancellation_target_effect_fence_digest',
               'ANY',
               True,
               'cancellation_target_effect_fence_digest IS NULL OR '
               "(typeof(cancellation_target_effect_fence_digest)='text' AND "
               'length(cancellation_target_effect_fence_digest)=64 AND '
               'cancellation_target_effect_fence_digest=lower(cancellation_target_effect_fence_digest) AND '
               "cancellation_target_effect_fence_digest NOT GLOB '*[^0-9a-f]*')",
               0),
              ('effect_fence_digest',
               'ANY',
               False,
               "typeof(effect_fence_digest)='text' AND length(effect_fence_digest)=64 AND "
               "effect_fence_digest=lower(effect_fence_digest) AND effect_fence_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('recorded_at',
               'ANY',
               False,
               "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' "
               "AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' "
               "AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' "
               "AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
               0)),
  'primary_key': ('effect_fence_ref',),
  'unique_constraints': (('program_ref', 'effect_fence_ref'), ('program_ref', 'effect_intent_ref')),
  'table_checks': (('effect_fence_cancellation_algebra',
                    "((effect_class='cancel_effect' AND cancellation_target_effect_intent_ref IS NOT NULL AND "
                    'cancellation_target_effect_fence_ref IS NOT NULL AND cancellation_target_effect_fence_digest IS '
                    "NOT NULL) OR (effect_class<>'cancel_effect' AND cancellation_target_effect_intent_ref IS NULL AND "
                    'cancellation_target_effect_fence_ref IS NULL AND cancellation_target_effect_fence_digest IS '
                    'NULL))'),
                   ('effect_fence_capsule_algebra',
                    "((effect_class='author_candidate' AND portable_capsule_digest IS NULL) OR (effect_class IN "
                    "('validate_candidate','review_candidate','local_git_commit') AND portable_capsule_digest IS NOT "
                    "NULL) OR effect_class='cancel_effect')")),
  'mutable': False},
 {'name': 'development_author_commands',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-worker-command.v1'",
               0),
              ('command_ref',
               'ANY',
               False,
               "typeof(command_ref)='text' AND length(command_ref) BETWEEN 1 AND 96 AND substr(command_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(command_ref,1,instr(command_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('program_version_ref',
               'ANY',
               False,
               "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND "
               "substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' "
               "AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('accepted_intent_revision_ref',
               'ANY',
               False,
               "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 "
               "AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('work_item_ref',
               'ANY',
               False,
               "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('work_item_revision_ref',
               'ANY',
               False,
               "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND "
               "substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('semantic_attempt_ref',
               'ANY',
               False,
               "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND "
               "substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('effect_intent_ref',
               'ANY',
               False,
               "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND "
               "substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('effect_class', 'ANY', False, "typeof(effect_class)='text' AND effect_class='author_candidate'", 0),
              ('candidate_ref',
               'ANY',
               False,
               "typeof(candidate_ref)='text' AND length(candidate_ref) BETWEEN 1 AND 96 AND substr(candidate_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(candidate_ref,1,instr(candidate_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('repository_ref',
               'ANY',
               False,
               "typeof(repository_ref)='text' AND length(repository_ref) BETWEEN 1 AND 96 AND "
               "substr(repository_ref,1,1) GLOB '[0-9A-Za-z]' AND repository_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(repository_ref,1,instr(repository_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('base_git_object_format',
               'ANY',
               False,
               "typeof(base_git_object_format)='text' AND base_git_object_format='sha1'",
               0),
              ('base_git_oid',
               'ANY',
               False,
               "typeof(base_git_oid)='text' AND length(base_git_oid)=40 AND base_git_oid=lower(base_git_oid) AND "
               "base_git_oid NOT GLOB '*[^0-9a-f]*'",
               0),
              ('path_ceiling_json',
               'ANY',
               False,
               "typeof(path_ceiling_json)='text' AND "
               'path_ceiling_json=\'[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"]\'',
               0),
              ('work_spec_ref',
               'ANY',
               False,
               "typeof(work_spec_ref)='text' AND length(work_spec_ref) BETWEEN 1 AND 96 AND substr(work_spec_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND work_spec_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(work_spec_ref,1,instr(work_spec_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('work_spec_digest',
               'ANY',
               False,
               "typeof(work_spec_digest)='text' AND length(work_spec_digest)=64 AND "
               "work_spec_digest=lower(work_spec_digest) AND work_spec_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('standing_grant_ref',
               'ANY',
               False,
               "typeof(standing_grant_ref)='text' AND length(standing_grant_ref) BETWEEN 1 AND 96 AND "
               "substr(standing_grant_ref,1,1) GLOB '[0-9A-Za-z]' AND standing_grant_ref NOT GLOB '*[^0-9A-Za-z.-]*' "
               "AND lower(substr(standing_grant_ref,1,instr(standing_grant_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('standing_grant_digest',
               'ANY',
               False,
               "typeof(standing_grant_digest)='text' AND length(standing_grant_digest)=64 AND "
               "standing_grant_digest=lower(standing_grant_digest) AND standing_grant_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('attempt_authorization_ref',
               'ANY',
               False,
               "typeof(attempt_authorization_ref)='text' AND length(attempt_authorization_ref) BETWEEN 1 AND 96 AND "
               "substr(attempt_authorization_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_authorization_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(attempt_authorization_ref,1,instr(attempt_authorization_ref,'-'))) "
               "NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('attempt_authorization_digest',
               'ANY',
               False,
               "typeof(attempt_authorization_digest)='text' AND length(attempt_authorization_digest)=64 AND "
               'attempt_authorization_digest=lower(attempt_authorization_digest) AND attempt_authorization_digest NOT '
               "GLOB '*[^0-9a-f]*'",
               0),
              ('effect_authorization_ref',
               'ANY',
               False,
               "typeof(effect_authorization_ref)='text' AND length(effect_authorization_ref) BETWEEN 1 AND 96 AND "
               "substr(effect_authorization_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_authorization_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(effect_authorization_ref,1,instr(effect_authorization_ref,'-'))) "
               "NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('effect_authorization_digest',
               'ANY',
               False,
               "typeof(effect_authorization_digest)='text' AND length(effect_authorization_digest)=64 AND "
               'effect_authorization_digest=lower(effect_authorization_digest) AND effect_authorization_digest NOT '
               "GLOB '*[^0-9a-f]*'",
               0),
              ('attempt_fence_ref',
               'ANY',
               False,
               "typeof(attempt_fence_ref)='text' AND length(attempt_fence_ref) BETWEEN 1 AND 96 AND "
               "substr(attempt_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(attempt_fence_ref,1,instr(attempt_fence_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('attempt_fence_digest',
               'ANY',
               False,
               "typeof(attempt_fence_digest)='text' AND length(attempt_fence_digest)=64 AND "
               "attempt_fence_digest=lower(attempt_fence_digest) AND attempt_fence_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('effect_fence_ref',
               'ANY',
               False,
               "typeof(effect_fence_ref)='text' AND length(effect_fence_ref) BETWEEN 1 AND 96 AND "
               "substr(effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(effect_fence_ref,1,instr(effect_fence_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('effect_fence_digest',
               'ANY',
               False,
               "typeof(effect_fence_digest)='text' AND length(effect_fence_digest)=64 AND "
               "effect_fence_digest=lower(effect_fence_digest) AND effect_fence_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('global_stop_ref',
               'ANY',
               False,
               "typeof(global_stop_ref)='text' AND length(global_stop_ref) BETWEEN 1 AND 96 AND "
               "substr(global_stop_ref,1,1) GLOB '[0-9A-Za-z]' AND global_stop_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(global_stop_ref,1,instr(global_stop_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('global_stop_version',
               'ANY',
               False,
               "typeof(global_stop_version)='integer' AND global_stop_version>=0",
               0),
              ('validation_requirement_ref',
               'ANY',
               False,
               "typeof(validation_requirement_ref)='text' AND length(validation_requirement_ref) BETWEEN 1 AND 96 AND "
               "substr(validation_requirement_ref,1,1) GLOB '[0-9A-Za-z]' AND validation_requirement_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND "
               "lower(substr(validation_requirement_ref,1,instr(validation_requirement_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('validation_requirement_digest',
               'ANY',
               False,
               "typeof(validation_requirement_digest)='text' AND length(validation_requirement_digest)=64 AND "
               'validation_requirement_digest=lower(validation_requirement_digest) AND validation_requirement_digest '
               "NOT GLOB '*[^0-9a-f]*'",
               0),
              ('review_requirement_ref',
               'ANY',
               False,
               "typeof(review_requirement_ref)='text' AND length(review_requirement_ref) BETWEEN 1 AND 96 AND "
               "substr(review_requirement_ref,1,1) GLOB '[0-9A-Za-z]' AND review_requirement_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(review_requirement_ref,1,instr(review_requirement_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('review_requirement_digest',
               'ANY',
               False,
               "typeof(review_requirement_digest)='text' AND length(review_requirement_digest)=64 AND "
               'review_requirement_digest=lower(review_requirement_digest) AND review_requirement_digest NOT GLOB '
               "'*[^0-9a-f]*'",
               0),
              ('capsule_schema_id',
               'ANY',
               False,
               "typeof(capsule_schema_id)='text' AND "
               "capsule_schema_id='governed-execution.nwp-candidate-capsule-manifest.v1'",
               0),
              ('capsule_profile_ref',
               'ANY',
               False,
               "typeof(capsule_profile_ref)='text' AND length(capsule_profile_ref) BETWEEN 1 AND 96 AND "
               "substr(capsule_profile_ref,1,1) GLOB '[0-9A-Za-z]' AND capsule_profile_ref NOT GLOB '*[^0-9A-Za-z.-]*' "
               "AND lower(substr(capsule_profile_ref,1,instr(capsule_profile_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('effect_max_active_invocations',
               'ANY',
               False,
               "typeof(effect_max_active_invocations)='integer' AND effect_max_active_invocations>=0",
               0),
              ('effect_max_candidate_bytes',
               'ANY',
               False,
               "typeof(effect_max_candidate_bytes)='integer' AND effect_max_candidate_bytes>=0",
               0),
              ('effect_max_changed_files',
               'ANY',
               False,
               "typeof(effect_max_changed_files)='integer' AND effect_max_changed_files>=0",
               0),
              ('effect_max_cost_microusd',
               'ANY',
               False,
               "typeof(effect_max_cost_microusd)='integer' AND effect_max_cost_microusd>=0",
               0),
              ('effect_max_cpu_seconds',
               'ANY',
               False,
               "typeof(effect_max_cpu_seconds)='integer' AND effect_max_cpu_seconds>=0",
               0),
              ('effect_max_deliveries',
               'ANY',
               False,
               "typeof(effect_max_deliveries)='integer' AND effect_max_deliveries>=0",
               0),
              ('effect_max_deployments',
               'ANY',
               False,
               "typeof(effect_max_deployments)='integer' AND effect_max_deployments>=0",
               0),
              ('effect_max_local_commits',
               'ANY',
               False,
               "typeof(effect_max_local_commits)='integer' AND effect_max_local_commits>=0",
               0),
              ('effect_max_memory_bytes',
               'ANY',
               False,
               "typeof(effect_max_memory_bytes)='integer' AND effect_max_memory_bytes>=0",
               0),
              ('effect_max_merges', 'ANY', False, "typeof(effect_max_merges)='integer' AND effect_max_merges>=0", 0),
              ('effect_max_model_input_tokens',
               'ANY',
               False,
               "typeof(effect_max_model_input_tokens)='integer' AND effect_max_model_input_tokens>=0",
               0),
              ('effect_max_model_output_tokens',
               'ANY',
               False,
               "typeof(effect_max_model_output_tokens)='integer' AND effect_max_model_output_tokens>=0",
               0),
              ('effect_max_pull_requests',
               'ANY',
               False,
               "typeof(effect_max_pull_requests)='integer' AND effect_max_pull_requests>=0",
               0),
              ('effect_max_pushes', 'ANY', False, "typeof(effect_max_pushes)='integer' AND effect_max_pushes>=0", 0),
              ('effect_max_wall_seconds',
               'ANY',
               False,
               "typeof(effect_max_wall_seconds)='integer' AND effect_max_wall_seconds>=0",
               0),
              ('privacy_classification',
               'ANY',
               False,
               "typeof(privacy_classification)='text' AND privacy_classification='private_source_change'",
               0),
              ('redaction_profile_ref',
               'ANY',
               False,
               "typeof(redaction_profile_ref)='text' AND length(redaction_profile_ref) BETWEEN 1 AND 96 AND "
               "substr(redaction_profile_ref,1,1) GLOB '[0-9A-Za-z]' AND redaction_profile_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(redaction_profile_ref,1,instr(redaction_profile_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('command_digest',
               'ANY',
               False,
               "typeof(command_digest)='text' AND length(command_digest)=64 AND command_digest=lower(command_digest) "
               "AND command_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('recorded_at',
               'ANY',
               False,
               "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' "
               "AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' "
               "AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' "
               "AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
               0)),
  'primary_key': ('command_ref',),
  'unique_constraints': (('program_ref', 'command_ref'), ('effect_intent_ref',), ('candidate_ref',)),
  'table_checks': (),
  'mutable': False},
 {'name': 'development_effect_heads',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-effect-head.v1'",
               0),
              ('effect_intent_ref',
               'ANY',
               False,
               "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND "
               "substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('current_effect_fence_ref',
               'ANY',
               False,
               "typeof(current_effect_fence_ref)='text' AND length(current_effect_fence_ref) BETWEEN 1 AND 96 AND "
               "substr(current_effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND current_effect_fence_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(current_effect_fence_ref,1,instr(current_effect_fence_ref,'-'))) "
               "NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('head_revision', 'ANY', False, "typeof(head_revision)='integer' AND head_revision>=0", 0),
              ('effect_state',
               'ANY',
               False,
               "typeof(effect_state)='text' AND effect_state IN "
               "('ready_for_delivery','delivery_pending','delivery_outcome_unknown','observed','cancellation_effect_established','terminal')",
               0),
              ('cancellation_effect_intent_ref',
               'ANY',
               True,
               "cancellation_effect_intent_ref IS NULL OR (typeof(cancellation_effect_intent_ref)='text' AND "
               'length(cancellation_effect_intent_ref) BETWEEN 1 AND 96 AND substr(cancellation_effect_intent_ref,1,1) '
               "GLOB '[0-9A-Za-z]' AND cancellation_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(cancellation_effect_intent_ref,1,instr(cancellation_effect_intent_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('updated_at',
               'ANY',
               False,
               "typeof(updated_at)='text' AND length(updated_at)=20 AND updated_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(updated_at,1,4) BETWEEN '0001' AND '9999' AND substr(updated_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(updated_at,9,2) BETWEEN '01' AND '31' AND substr(updated_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(updated_at,15,2) BETWEEN '00' AND '59' AND substr(updated_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',updated_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',updated_at)=updated_at",
               0),
              ('head_digest',
               'ANY',
               False,
               "typeof(head_digest)='text' AND length(head_digest)=64 AND head_digest=lower(head_digest) AND "
               "head_digest NOT GLOB '*[^0-9a-f]*'",
               0)),
  'primary_key': ('effect_intent_ref',),
  'unique_constraints': (('program_ref', 'effect_intent_ref'),),
  'table_checks': (('effect_head_cancellation_algebra',
                    "((effect_state='cancellation_effect_established' AND cancellation_effect_intent_ref IS NOT NULL) "
                    "OR (effect_state<>'cancellation_effect_established' AND cancellation_effect_intent_ref IS "
                    'NULL))'),),
  'mutable': True},
 {'name': 'development_delivery_attempts',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-delivery-envelope.v1'",
               0),
              ('delivery_attempt_ref',
               'ANY',
               False,
               "typeof(delivery_attempt_ref)='text' AND length(delivery_attempt_ref) BETWEEN 1 AND 96 AND "
               "substr(delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND delivery_attempt_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(delivery_attempt_ref,1,instr(delivery_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('program_version_ref',
               'ANY',
               False,
               "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND "
               "substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' "
               "AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('command_ref',
               'ANY',
               False,
               "typeof(command_ref)='text' AND length(command_ref) BETWEEN 1 AND 96 AND substr(command_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(command_ref,1,instr(command_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('command_digest',
               'ANY',
               False,
               "typeof(command_digest)='text' AND length(command_digest)=64 AND command_digest=lower(command_digest) "
               "AND command_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('semantic_attempt_ref',
               'ANY',
               False,
               "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND "
               "substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('effect_intent_ref',
               'ANY',
               False,
               "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND "
               "substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('attempt_fence_ref',
               'ANY',
               False,
               "typeof(attempt_fence_ref)='text' AND length(attempt_fence_ref) BETWEEN 1 AND 96 AND "
               "substr(attempt_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(attempt_fence_ref,1,instr(attempt_fence_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('attempt_fence_digest',
               'ANY',
               False,
               "typeof(attempt_fence_digest)='text' AND length(attempt_fence_digest)=64 AND "
               "attempt_fence_digest=lower(attempt_fence_digest) AND attempt_fence_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('effect_fence_ref',
               'ANY',
               False,
               "typeof(effect_fence_ref)='text' AND length(effect_fence_ref) BETWEEN 1 AND 96 AND "
               "substr(effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(effect_fence_ref,1,instr(effect_fence_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('effect_fence_digest',
               'ANY',
               False,
               "typeof(effect_fence_digest)='text' AND length(effect_fence_digest)=64 AND "
               "effect_fence_digest=lower(effect_fence_digest) AND effect_fence_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('adapter_kind',
               'ANY',
               False,
               "typeof(adapter_kind)='text' AND adapter_kind IN ('direct_local_bootstrap','execution_substrate')",
               0),
              ('adapter_safe_correlation_ref',
               'ANY',
               False,
               "typeof(adapter_safe_correlation_ref)='text' AND length(adapter_safe_correlation_ref) BETWEEN 1 AND 96 "
               "AND substr(adapter_safe_correlation_ref,1,1) GLOB '[0-9A-Za-z]' AND adapter_safe_correlation_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(adapter_safe_correlation_ref,1,instr(adapter_safe_correlation_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('delivery_envelope_digest',
               'ANY',
               False,
               "typeof(delivery_envelope_digest)='text' AND length(delivery_envelope_digest)=64 AND "
               'delivery_envelope_digest=lower(delivery_envelope_digest) AND delivery_envelope_digest NOT GLOB '
               "'*[^0-9a-f]*'",
               0),
              ('delivery_kind',
               'ANY',
               False,
               "typeof(delivery_kind)='text' AND delivery_kind IN ('initial','redelivery')",
               0),
              ('delivery_number', 'ANY', False, "typeof(delivery_number)='integer' AND delivery_number>=1", 0),
              ('predecessor_delivery_attempt_ref',
               'ANY',
               True,
               "predecessor_delivery_attempt_ref IS NULL OR (typeof(predecessor_delivery_attempt_ref)='text' AND "
               'length(predecessor_delivery_attempt_ref) BETWEEN 1 AND 96 AND '
               "substr(predecessor_delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND predecessor_delivery_attempt_ref "
               "NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(predecessor_delivery_attempt_ref,1,instr(predecessor_delivery_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('basis_decision_ref',
               'ANY',
               False,
               "typeof(basis_decision_ref)='text' AND length(basis_decision_ref) BETWEEN 1 AND 96 AND "
               "substr(basis_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND basis_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' "
               "AND lower(substr(basis_decision_ref,1,instr(basis_decision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('recorded_at',
               'ANY',
               False,
               "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' "
               "AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' "
               "AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' "
               "AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
               0),
              ('delivery_attempt_digest',
               'ANY',
               False,
               "typeof(delivery_attempt_digest)='text' AND length(delivery_attempt_digest)=64 AND "
               'delivery_attempt_digest=lower(delivery_attempt_digest) AND delivery_attempt_digest NOT GLOB '
               "'*[^0-9a-f]*'",
               0)),
  'primary_key': ('delivery_attempt_ref',),
  'unique_constraints': (('program_ref', 'delivery_attempt_ref'),
                         ('program_ref', 'effect_intent_ref', 'delivery_number')),
  'table_checks': (('delivery_predecessor_algebra',
                    "((delivery_kind='initial' AND delivery_number=1 AND predecessor_delivery_attempt_ref IS NULL) OR "
                    "(delivery_kind='redelivery' AND delivery_number>=2 AND predecessor_delivery_attempt_ref IS NOT "
                    'NULL))'),),
  'mutable': False},
 {'name': 'development_delivery_heads',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-delivery-head.v1'",
               0),
              ('effect_intent_ref',
               'ANY',
               False,
               "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND "
               "substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('current_delivery_attempt_ref',
               'ANY',
               False,
               "typeof(current_delivery_attempt_ref)='text' AND length(current_delivery_attempt_ref) BETWEEN 1 AND 96 "
               "AND substr(current_delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND current_delivery_attempt_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(current_delivery_attempt_ref,1,instr(current_delivery_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('head_revision', 'ANY', False, "typeof(head_revision)='integer' AND head_revision>=0", 0),
              ('delivery_state',
               'ANY',
               False,
               "typeof(delivery_state)='text' AND delivery_state IN "
               "('planned','submitted','outcome_unknown','acknowledged','rejected','completed')",
               0),
              ('updated_at',
               'ANY',
               False,
               "typeof(updated_at)='text' AND length(updated_at)=20 AND updated_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(updated_at,1,4) BETWEEN '0001' AND '9999' AND substr(updated_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(updated_at,9,2) BETWEEN '01' AND '31' AND substr(updated_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(updated_at,15,2) BETWEEN '00' AND '59' AND substr(updated_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',updated_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',updated_at)=updated_at",
               0),
              ('head_digest',
               'ANY',
               False,
               "typeof(head_digest)='text' AND length(head_digest)=64 AND head_digest=lower(head_digest) AND "
               "head_digest NOT GLOB '*[^0-9a-f]*'",
               0)),
  'primary_key': ('effect_intent_ref',),
  'unique_constraints': (('program_ref', 'effect_intent_ref'),),
  'table_checks': (),
  'mutable': True},
 {'name': 'development_decisions',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-decision.v1'",
               0),
              ('mutation_ref',
               'ANY',
               False,
               "typeof(mutation_ref)='text' AND length(mutation_ref) BETWEEN 1 AND 96 AND substr(mutation_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(mutation_ref,1,instr(mutation_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('decision_ref',
               'ANY',
               False,
               "typeof(decision_ref)='text' AND length(decision_ref) BETWEEN 1 AND 96 AND substr(decision_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(decision_ref,1,instr(decision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('decision_kind',
               'ANY',
               False,
               "typeof(decision_kind)='text' AND decision_kind IN "
               "('initialize','accept','repair','replan','terminal_reject','block','redeliver','cancel')",
               0),
              ('decision_variant',
               'ANY',
               False,
               "typeof(decision_variant)='text' AND decision_variant IN "
               "('program_genesis','candidate_acceptance','candidate_repair','program_replan','attempt_selecting_replan','program_terminal_reject','program_block','productive_redelivery','cancellation_redelivery','effect_cancellation')",
               0),
              ('basis_decision_ref',
               'ANY',
               True,
               "basis_decision_ref IS NULL OR (typeof(basis_decision_ref)='text' AND length(basis_decision_ref) "
               "BETWEEN 1 AND 96 AND substr(basis_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND basis_decision_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(basis_decision_ref,1,instr(basis_decision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('basis_program_version_ref',
               'ANY',
               True,
               "basis_program_version_ref IS NULL OR (typeof(basis_program_version_ref)='text' AND "
               'length(basis_program_version_ref) BETWEEN 1 AND 96 AND substr(basis_program_version_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND basis_program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(basis_program_version_ref,1,instr(basis_program_version_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('basis_program_version_number',
               'ANY',
               True,
               "basis_program_version_number IS NULL OR (typeof(basis_program_version_number)='integer' AND "
               'basis_program_version_number>=1)',
               0),
              ('expected_program_head_revision',
               'ANY',
               False,
               "typeof(expected_program_head_revision)='integer' AND expected_program_head_revision>=0",
               0),
              ('resulting_program_version_ref',
               'ANY',
               True,
               "resulting_program_version_ref IS NULL OR (typeof(resulting_program_version_ref)='text' AND "
               'length(resulting_program_version_ref) BETWEEN 1 AND 96 AND substr(resulting_program_version_ref,1,1) '
               "GLOB '[0-9A-Za-z]' AND resulting_program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(resulting_program_version_ref,1,instr(resulting_program_version_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('resulting_program_version_number',
               'ANY',
               True,
               "resulting_program_version_number IS NULL OR (typeof(resulting_program_version_number)='integer' AND "
               'resulting_program_version_number>=1)',
               0),
              ('selected_semantic_attempt_ref',
               'ANY',
               True,
               "selected_semantic_attempt_ref IS NULL OR (typeof(selected_semantic_attempt_ref)='text' AND "
               'length(selected_semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(selected_semantic_attempt_ref,1,1) '
               "GLOB '[0-9A-Za-z]' AND selected_semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(selected_semantic_attempt_ref,1,instr(selected_semantic_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('selected_candidate_ref',
               'ANY',
               True,
               "selected_candidate_ref IS NULL OR (typeof(selected_candidate_ref)='text' AND "
               'length(selected_candidate_ref) BETWEEN 1 AND 96 AND substr(selected_candidate_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND selected_candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(selected_candidate_ref,1,instr(selected_candidate_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('selected_attempt_fence_ref',
               'ANY',
               True,
               "selected_attempt_fence_ref IS NULL OR (typeof(selected_attempt_fence_ref)='text' AND "
               'length(selected_attempt_fence_ref) BETWEEN 1 AND 96 AND substr(selected_attempt_fence_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND selected_attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(selected_attempt_fence_ref,1,instr(selected_attempt_fence_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('selected_attempt_fence_digest',
               'ANY',
               True,
               "selected_attempt_fence_digest IS NULL OR (typeof(selected_attempt_fence_digest)='text' AND "
               'length(selected_attempt_fence_digest)=64 AND '
               'selected_attempt_fence_digest=lower(selected_attempt_fence_digest) AND selected_attempt_fence_digest '
               "NOT GLOB '*[^0-9a-f]*')",
               0),
              ('target_effect_intent_ref',
               'ANY',
               True,
               "target_effect_intent_ref IS NULL OR (typeof(target_effect_intent_ref)='text' AND "
               'length(target_effect_intent_ref) BETWEEN 1 AND 96 AND substr(target_effect_intent_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND target_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(target_effect_intent_ref,1,instr(target_effect_intent_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('target_effect_class',
               'ANY',
               True,
               "target_effect_class IS NULL OR (typeof(target_effect_class)='text' AND target_effect_class IN "
               "('author_candidate','cancel_effect','local_git_commit','review_candidate','validate_candidate'))",
               0),
              ('target_effect_fence_ref',
               'ANY',
               True,
               "target_effect_fence_ref IS NULL OR (typeof(target_effect_fence_ref)='text' AND "
               'length(target_effect_fence_ref) BETWEEN 1 AND 96 AND substr(target_effect_fence_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND target_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(target_effect_fence_ref,1,instr(target_effect_fence_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('target_effect_fence_digest',
               'ANY',
               True,
               "target_effect_fence_digest IS NULL OR (typeof(target_effect_fence_digest)='text' AND "
               'length(target_effect_fence_digest)=64 AND target_effect_fence_digest=lower(target_effect_fence_digest) '
               "AND target_effect_fence_digest NOT GLOB '*[^0-9a-f]*')",
               0),
              ('expected_target_effect_head_revision',
               'ANY',
               True,
               'expected_target_effect_head_revision IS NULL OR '
               "(typeof(expected_target_effect_head_revision)='integer' AND expected_target_effect_head_revision>=0)",
               0),
              ('target_delivery_attempt_ref',
               'ANY',
               True,
               "target_delivery_attempt_ref IS NULL OR (typeof(target_delivery_attempt_ref)='text' AND "
               'length(target_delivery_attempt_ref) BETWEEN 1 AND 96 AND substr(target_delivery_attempt_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND target_delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(target_delivery_attempt_ref,1,instr(target_delivery_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('originating_command_ref',
               'ANY',
               True,
               "originating_command_ref IS NULL OR (typeof(originating_command_ref)='text' AND "
               'length(originating_command_ref) BETWEEN 1 AND 96 AND substr(originating_command_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND originating_command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(originating_command_ref,1,instr(originating_command_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('originating_command_digest',
               'ANY',
               True,
               "originating_command_digest IS NULL OR (typeof(originating_command_digest)='text' AND "
               'length(originating_command_digest)=64 AND originating_command_digest=lower(originating_command_digest) '
               "AND originating_command_digest NOT GLOB '*[^0-9a-f]*')",
               0),
              ('target_capsule_manifest_ref',
               'ANY',
               True,
               "target_capsule_manifest_ref IS NULL OR (typeof(target_capsule_manifest_ref)='text' AND "
               'length(target_capsule_manifest_ref) BETWEEN 1 AND 96 AND substr(target_capsule_manifest_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND target_capsule_manifest_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(target_capsule_manifest_ref,1,instr(target_capsule_manifest_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('target_portable_capsule_digest',
               'ANY',
               True,
               "target_portable_capsule_digest IS NULL OR (typeof(target_portable_capsule_digest)='text' AND "
               'length(target_portable_capsule_digest)=64 AND '
               'target_portable_capsule_digest=lower(target_portable_capsule_digest) AND '
               "target_portable_capsule_digest NOT GLOB '*[^0-9a-f]*')",
               0),
              ('coding_global_stop_ref',
               'ANY',
               False,
               "typeof(coding_global_stop_ref)='text' AND length(coding_global_stop_ref) BETWEEN 1 AND 96 AND "
               "substr(coding_global_stop_ref,1,1) GLOB '[0-9A-Za-z]' AND coding_global_stop_ref NOT GLOB "
               "'*[^0-9A-Za-z.-]*' AND lower(substr(coding_global_stop_ref,1,instr(coding_global_stop_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('coding_global_stop_version',
               'ANY',
               False,
               "typeof(coding_global_stop_version)='integer' AND coding_global_stop_version>=0",
               0),
              ('source_directive_ref',
               'ANY',
               True,
               "source_directive_ref IS NULL OR (typeof(source_directive_ref)='text' AND length(source_directive_ref) "
               "BETWEEN 1 AND 96 AND substr(source_directive_ref,1,1) GLOB '[0-9A-Za-z]' AND source_directive_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(source_directive_ref,1,instr(source_directive_ref,'-'))) NOT "
               "IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('source_directive_digest',
               'ANY',
               True,
               "source_directive_digest IS NULL OR (typeof(source_directive_digest)='text' AND "
               'length(source_directive_digest)=64 AND source_directive_digest=lower(source_directive_digest) AND '
               "source_directive_digest NOT GLOB '*[^0-9a-f]*')",
               0),
              ('source_evidence_ref',
               'ANY',
               True,
               "source_evidence_ref IS NULL OR (typeof(source_evidence_ref)='text' AND length(source_evidence_ref) "
               "BETWEEN 1 AND 96 AND substr(source_evidence_ref,1,1) GLOB '[0-9A-Za-z]' AND source_evidence_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(source_evidence_ref,1,instr(source_evidence_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('source_evidence_digest',
               'ANY',
               True,
               "source_evidence_digest IS NULL OR (typeof(source_evidence_digest)='text' AND "
               'length(source_evidence_digest)=64 AND source_evidence_digest=lower(source_evidence_digest) AND '
               "source_evidence_digest NOT GLOB '*[^0-9a-f]*')",
               0),
              ('preassigned_semantic_attempt_ref',
               'ANY',
               True,
               "preassigned_semantic_attempt_ref IS NULL OR (typeof(preassigned_semantic_attempt_ref)='text' AND "
               'length(preassigned_semantic_attempt_ref) BETWEEN 1 AND 96 AND '
               "substr(preassigned_semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND preassigned_semantic_attempt_ref "
               "NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(preassigned_semantic_attempt_ref,1,instr(preassigned_semantic_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('preassigned_candidate_ref',
               'ANY',
               True,
               "preassigned_candidate_ref IS NULL OR (typeof(preassigned_candidate_ref)='text' AND "
               'length(preassigned_candidate_ref) BETWEEN 1 AND 96 AND substr(preassigned_candidate_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND preassigned_candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(preassigned_candidate_ref,1,instr(preassigned_candidate_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('preassigned_effect_intent_ref',
               'ANY',
               True,
               "preassigned_effect_intent_ref IS NULL OR (typeof(preassigned_effect_intent_ref)='text' AND "
               'length(preassigned_effect_intent_ref) BETWEEN 1 AND 96 AND substr(preassigned_effect_intent_ref,1,1) '
               "GLOB '[0-9A-Za-z]' AND preassigned_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(preassigned_effect_intent_ref,1,instr(preassigned_effect_intent_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('preassigned_effect_fence_ref',
               'ANY',
               True,
               "preassigned_effect_fence_ref IS NULL OR (typeof(preassigned_effect_fence_ref)='text' AND "
               'length(preassigned_effect_fence_ref) BETWEEN 1 AND 96 AND substr(preassigned_effect_fence_ref,1,1) '
               "GLOB '[0-9A-Za-z]' AND preassigned_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(preassigned_effect_fence_ref,1,instr(preassigned_effect_fence_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('preassigned_delivery_attempt_ref',
               'ANY',
               True,
               "preassigned_delivery_attempt_ref IS NULL OR (typeof(preassigned_delivery_attempt_ref)='text' AND "
               'length(preassigned_delivery_attempt_ref) BETWEEN 1 AND 96 AND '
               "substr(preassigned_delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND preassigned_delivery_attempt_ref "
               "NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(preassigned_delivery_attempt_ref,1,instr(preassigned_delivery_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('resulting_accepted_intent_revision_ref',
               'ANY',
               True,
               'resulting_accepted_intent_revision_ref IS NULL OR '
               "(typeof(resulting_accepted_intent_revision_ref)='text' AND "
               'length(resulting_accepted_intent_revision_ref) BETWEEN 1 AND 96 AND '
               "substr(resulting_accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND "
               "resulting_accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(resulting_accepted_intent_revision_ref,1,instr(resulting_accepted_intent_revision_ref,'-'))) "
               "NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('resulting_work_item_ref',
               'ANY',
               True,
               "resulting_work_item_ref IS NULL OR (typeof(resulting_work_item_ref)='text' AND "
               'length(resulting_work_item_ref) BETWEEN 1 AND 96 AND substr(resulting_work_item_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND resulting_work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(resulting_work_item_ref,1,instr(resulting_work_item_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('resulting_work_item_revision_ref',
               'ANY',
               True,
               "resulting_work_item_revision_ref IS NULL OR (typeof(resulting_work_item_revision_ref)='text' AND "
               'length(resulting_work_item_revision_ref) BETWEEN 1 AND 96 AND '
               "substr(resulting_work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND resulting_work_item_revision_ref "
               "NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(resulting_work_item_revision_ref,1,instr(resulting_work_item_revision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('reason_code',
               'ANY',
               False,
               "typeof(reason_code)='text' AND length(reason_code) BETWEEN 1 AND 96 AND substr(reason_code,1,1) GLOB "
               "'[a-z]' AND reason_code NOT GLOB '*[^a-z0-9_.-]*'",
               0),
              ('decided_at',
               'ANY',
               False,
               "typeof(decided_at)='text' AND length(decided_at)=20 AND decided_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(decided_at,1,4) BETWEEN '0001' AND '9999' AND substr(decided_at,6,2) BETWEEN '01' AND '12' AND "
               "substr(decided_at,9,2) BETWEEN '01' AND '31' AND substr(decided_at,12,2) BETWEEN '00' AND '23' AND "
               "substr(decided_at,15,2) BETWEEN '00' AND '59' AND substr(decided_at,18,2) BETWEEN '00' AND '59' AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',decided_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',decided_at)=decided_at",
               0),
              ('decision_digest',
               'ANY',
               False,
               "typeof(decision_digest)='text' AND length(decision_digest)=64 AND "
               "decision_digest=lower(decision_digest) AND decision_digest NOT GLOB '*[^0-9a-f]*'",
               0)),
  'primary_key': ('decision_ref',),
  'unique_constraints': (('program_ref', 'decision_ref'), ('mutation_ref',)),
  'table_checks': (('decision_closed_variant_algebra',
                    "((decision_kind='initialize' AND decision_variant='program_genesis' AND basis_decision_ref IS "
                    'NULL AND basis_program_version_ref IS NULL AND basis_program_version_number IS NULL AND '
                    'resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND '
                    'selected_semantic_attempt_ref IS NULL AND selected_candidate_ref IS NULL AND '
                    'selected_attempt_fence_ref IS NULL AND selected_attempt_fence_digest IS NULL AND '
                    'target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS '
                    'NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND '
                    'target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND '
                    'originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND '
                    'target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND '
                    'source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS '
                    'NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL '
                    'AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND '
                    'preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND '
                    'resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND '
                    'resulting_program_version_number=1 AND expected_program_head_revision=0) OR '
                    "(decision_kind='accept' AND decision_variant='candidate_acceptance' AND basis_decision_ref IS NOT "
                    'NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND '
                    'resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND '
                    'selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND '
                    'selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND '
                    'target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS '
                    'NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND '
                    'target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND '
                    'originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND '
                    'target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND '
                    'source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS '
                    'NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND '
                    'preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND '
                    'preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND '
                    'resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL) OR '
                    "(decision_kind='repair' AND decision_variant='candidate_repair' AND basis_decision_ref IS NOT "
                    'NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND '
                    'resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND '
                    'selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND '
                    'selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND '
                    'target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS '
                    'NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND '
                    'target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND '
                    'originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND '
                    'target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND '
                    'source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS '
                    'NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL '
                    'AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND '
                    'preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND '
                    'resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL) OR '
                    "(decision_kind='replan' AND decision_variant='program_replan' AND basis_decision_ref IS NOT NULL "
                    'AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND '
                    'resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND '
                    'selected_semantic_attempt_ref IS NULL AND selected_candidate_ref IS NULL AND '
                    'selected_attempt_fence_ref IS NULL AND selected_attempt_fence_digest IS NULL AND '
                    'target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS '
                    'NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND '
                    'target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND '
                    'originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND '
                    'target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND '
                    'source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS '
                    'NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND '
                    'preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND '
                    'preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NOT NULL '
                    'AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL) OR '
                    "(decision_kind='replan' AND decision_variant='attempt_selecting_replan' AND basis_decision_ref IS "
                    'NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL '
                    'AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL '
                    'AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND '
                    'selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND '
                    'target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS '
                    'NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND '
                    'target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND '
                    'originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND '
                    'target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND '
                    'source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS '
                    'NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL '
                    'AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND '
                    'preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NOT NULL '
                    'AND resulting_work_item_ref IS NOT NULL AND resulting_work_item_revision_ref IS NOT NULL) OR '
                    "(decision_kind='terminal_reject' AND decision_variant='program_terminal_reject' AND "
                    'basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND '
                    'basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND '
                    'resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND '
                    'selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND '
                    'selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND '
                    'target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS '
                    'NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND '
                    'originating_command_ref IS NULL AND originating_command_digest IS NULL AND '
                    'target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND '
                    'source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL '
                    'AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND '
                    'preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND '
                    'preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND '
                    'resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND '
                    "resulting_work_item_revision_ref IS NULL) OR (decision_kind='block' AND "
                    "decision_variant='program_block' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref "
                    'IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT '
                    'NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NULL '
                    'AND selected_candidate_ref IS NULL AND selected_attempt_fence_ref IS NULL AND '
                    'selected_attempt_fence_digest IS NULL AND target_effect_intent_ref IS NULL AND '
                    'target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS '
                    'NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND '
                    'originating_command_ref IS NULL AND originating_command_digest IS NULL AND '
                    'target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND '
                    'source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL '
                    'AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND '
                    'preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND '
                    'preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND '
                    'resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND '
                    "resulting_work_item_revision_ref IS NULL) OR (decision_kind='redeliver' AND "
                    "decision_variant='productive_redelivery' AND basis_decision_ref IS NOT NULL AND "
                    'basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND '
                    'resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND '
                    'selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND '
                    'selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND '
                    'target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND '
                    'target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND '
                    'expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NOT NULL AND '
                    'originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND '
                    'target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND '
                    'source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL '
                    'AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND '
                    'preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND '
                    'preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND '
                    'resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND '
                    'resulting_work_item_revision_ref IS NULL AND target_effect_class IN '
                    "('author_candidate','validate_candidate','review_candidate')) OR (decision_kind='redeliver' AND "
                    "decision_variant='cancellation_redelivery' AND basis_decision_ref IS NOT NULL AND "
                    'basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND '
                    'resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND '
                    'selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND '
                    'selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND '
                    'target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND '
                    'target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND '
                    'expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NOT NULL AND '
                    'originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND '
                    'target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND '
                    'source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL '
                    'AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND '
                    'preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND '
                    'preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND '
                    'resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND '
                    "resulting_work_item_revision_ref IS NULL AND target_effect_class='cancel_effect') OR "
                    "(decision_kind='cancel' AND decision_variant='effect_cancellation' AND basis_decision_ref IS NOT "
                    'NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND '
                    'resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND '
                    'selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND '
                    'selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND '
                    'target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND '
                    'target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND '
                    'expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NULL AND '
                    'originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND '
                    "((target_effect_class='author_candidate' AND target_capsule_manifest_ref IS NULL AND "
                    'target_portable_capsule_digest IS NULL) OR (target_effect_class IN '
                    "('validate_candidate','review_candidate') AND target_capsule_manifest_ref IS NOT NULL AND "
                    'target_portable_capsule_digest IS NOT NULL)) AND source_directive_ref IS NOT NULL AND '
                    'source_directive_digest IS NOT NULL AND source_evidence_ref IS NOT NULL AND '
                    'source_evidence_digest IS NOT NULL AND preassigned_semantic_attempt_ref IS NULL AND '
                    'preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NOT NULL AND '
                    'preassigned_effect_fence_ref IS NOT NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND '
                    'resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND '
                    'resulting_work_item_revision_ref IS NULL AND target_effect_class IN '
                    "('author_candidate','validate_candidate','review_candidate')))"),),
  'mutable': False},
 {'name': 'development_mutation_receipts',
  'columns': (('schema_id',
               'ANY',
               False,
               "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-mutation-receipt.v1'",
               0),
              ('mutation_ref',
               'ANY',
               False,
               "typeof(mutation_ref)='text' AND length(mutation_ref) BETWEEN 1 AND 96 AND substr(mutation_ref,1,1) "
               "GLOB '[0-9A-Za-z]' AND mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(mutation_ref,1,instr(mutation_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               1),
              ('mutation_family',
               'ANY',
               False,
               "typeof(mutation_family)='text' AND mutation_family IN "
               "('initialize_development_program','establish_development_author_effect_intent','establish_development_bound_effect_intent','ingest_development_source_observation','record_development_progression_decision')",
               0),
              ('command_schema_id',
               'ANY',
               False,
               "typeof(command_schema_id)='text' AND command_schema_id IN "
               "('governed-execution.nwp-initialize-development-program-command.v1','governed-execution.nwp-establish-development-author-effect-intent-command.v1','governed-execution.nwp-establish-development-bound-effect-intent-command.v1','governed-execution.nwp-ingest-development-source-observation-command.v1','governed-execution.nwp-record-development-progression-decision-command.v1')",
               0),
              ('command_digest',
               'ANY',
               False,
               "typeof(command_digest)='text' AND length(command_digest)=64 AND command_digest=lower(command_digest) "
               "AND command_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('program_ref',
               'ANY',
               False,
               "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB "
               "'[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-')",
               0),
              ('decision_ref',
               'ANY',
               True,
               "decision_ref IS NULL OR (typeof(decision_ref)='text' AND length(decision_ref) BETWEEN 1 AND 96 AND "
               "substr(decision_ref,1,1) GLOB '[0-9A-Za-z]' AND decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(decision_ref,1,instr(decision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('result_program_version_ref',
               'ANY',
               True,
               "result_program_version_ref IS NULL OR (typeof(result_program_version_ref)='text' AND "
               'length(result_program_version_ref) BETWEEN 1 AND 96 AND substr(result_program_version_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND result_program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(result_program_version_ref,1,instr(result_program_version_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('result_semantic_attempt_ref',
               'ANY',
               True,
               "result_semantic_attempt_ref IS NULL OR (typeof(result_semantic_attempt_ref)='text' AND "
               'length(result_semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(result_semantic_attempt_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND result_semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(result_semantic_attempt_ref,1,instr(result_semantic_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('result_effect_intent_ref',
               'ANY',
               True,
               "result_effect_intent_ref IS NULL OR (typeof(result_effect_intent_ref)='text' AND "
               'length(result_effect_intent_ref) BETWEEN 1 AND 96 AND substr(result_effect_intent_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND result_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(result_effect_intent_ref,1,instr(result_effect_intent_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('result_effect_fence_ref',
               'ANY',
               True,
               "result_effect_fence_ref IS NULL OR (typeof(result_effect_fence_ref)='text' AND "
               'length(result_effect_fence_ref) BETWEEN 1 AND 96 AND substr(result_effect_fence_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND result_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(result_effect_fence_ref,1,instr(result_effect_fence_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('result_delivery_attempt_ref',
               'ANY',
               True,
               "result_delivery_attempt_ref IS NULL OR (typeof(result_delivery_attempt_ref)='text' AND "
               'length(result_delivery_attempt_ref) BETWEEN 1 AND 96 AND substr(result_delivery_attempt_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND result_delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(result_delivery_attempt_ref,1,instr(result_delivery_attempt_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('result_observation_ref',
               'ANY',
               True,
               "result_observation_ref IS NULL OR (typeof(result_observation_ref)='text' AND "
               'length(result_observation_ref) BETWEEN 1 AND 96 AND substr(result_observation_ref,1,1) GLOB '
               "'[0-9A-Za-z]' AND result_observation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND "
               "lower(substr(result_observation_ref,1,instr(result_observation_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('result_decision_ref',
               'ANY',
               True,
               "result_decision_ref IS NULL OR (typeof(result_decision_ref)='text' AND length(result_decision_ref) "
               "BETWEEN 1 AND 96 AND substr(result_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND result_decision_ref NOT "
               "GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_decision_ref,1,instr(result_decision_ref,'-'))) NOT IN "
               "('connector-','tunnel-','workspace-','org-','organization-','user-'))",
               0),
              ('result_class',
               'ANY',
               False,
               "typeof(result_class)='text' AND result_class IN "
               "('development_program_initialized','development_author_effect_intent_established','development_bound_effect_intent_established','development_source_observation_ingested','development_progression_decision_recorded')",
               0),
              ('result_projection_digest',
               'ANY',
               False,
               "typeof(result_projection_digest)='text' AND length(result_projection_digest)=64 AND "
               'result_projection_digest=lower(result_projection_digest) AND result_projection_digest NOT GLOB '
               "'*[^0-9a-f]*'",
               0),
              ('mutation_graph_digest',
               'ANY',
               False,
               "typeof(mutation_graph_digest)='text' AND length(mutation_graph_digest)=64 AND "
               "mutation_graph_digest=lower(mutation_graph_digest) AND mutation_graph_digest NOT GLOB '*[^0-9a-f]*'",
               0),
              ('outcome', 'ANY', False, "typeof(outcome)='text' AND outcome='committed'", 0),
              ('committed_at',
               'ANY',
               False,
               "typeof(committed_at)='text' AND length(committed_at)=20 AND committed_at GLOB "
               "'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND "
               "substr(committed_at,1,4) BETWEEN '0001' AND '9999' AND substr(committed_at,6,2) BETWEEN '01' AND '12' "
               "AND substr(committed_at,9,2) BETWEEN '01' AND '31' AND substr(committed_at,12,2) BETWEEN '00' AND '23' "
               "AND substr(committed_at,15,2) BETWEEN '00' AND '59' AND substr(committed_at,18,2) BETWEEN '00' AND "
               "'59' AND strftime('%Y-%m-%dT%H:%M:%SZ',committed_at) IS NOT NULL AND "
               "strftime('%Y-%m-%dT%H:%M:%SZ',committed_at)=committed_at",
               0)),
  'primary_key': ('mutation_ref',),
  'unique_constraints': (),
  'table_checks': (('receipt_closed_family_algebra',
                    "((mutation_family='initialize_development_program' AND "
                    "command_schema_id='governed-execution.nwp-initialize-development-program-command.v1' AND "
                    "result_class='development_program_initialized' AND decision_ref IS NOT NULL AND "
                    'result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NULL AND '
                    'result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND '
                    'result_delivery_attempt_ref IS NULL AND result_observation_ref IS NULL AND result_decision_ref IS '
                    'NOT NULL AND result_decision_ref=decision_ref) OR '
                    "(mutation_family='establish_development_author_effect_intent' AND "
                    "command_schema_id='governed-execution.nwp-establish-development-author-effect-intent-command.v1' "
                    "AND result_class='development_author_effect_intent_established' AND decision_ref IS NOT NULL AND "
                    'result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NOT NULL AND '
                    'result_effect_intent_ref IS NOT NULL AND result_effect_fence_ref IS NOT NULL AND '
                    'result_delivery_attempt_ref IS NOT NULL AND result_observation_ref IS NULL AND '
                    "result_decision_ref IS NULL) OR (mutation_family='establish_development_bound_effect_intent' AND "
                    "command_schema_id='governed-execution.nwp-establish-development-bound-effect-intent-command.v1' "
                    "AND result_class='development_bound_effect_intent_established' AND decision_ref IS NOT NULL AND "
                    'result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NOT NULL AND '
                    'result_effect_intent_ref IS NOT NULL AND result_effect_fence_ref IS NOT NULL AND '
                    'result_delivery_attempt_ref IS NOT NULL AND result_observation_ref IS NULL AND '
                    "result_decision_ref IS NULL) OR (mutation_family='ingest_development_source_observation' AND "
                    "command_schema_id='governed-execution.nwp-ingest-development-source-observation-command.v1' AND "
                    "result_class='development_source_observation_ingested' AND decision_ref IS NULL AND "
                    'result_program_version_ref IS NULL AND result_semantic_attempt_ref IS NULL AND '
                    'result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND '
                    'result_delivery_attempt_ref IS NULL AND result_observation_ref IS NOT NULL AND '
                    "result_decision_ref IS NULL) OR (mutation_family='record_development_progression_decision' AND "
                    "command_schema_id='governed-execution.nwp-record-development-progression-decision-command.v1' AND "
                    "result_class='development_progression_decision_recorded' AND decision_ref IS NOT NULL AND "
                    'result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NULL AND '
                    'result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND '
                    'result_delivery_attempt_ref IS NULL AND result_observation_ref IS NULL AND result_decision_ref IS '
                    'NOT NULL AND result_decision_ref=decision_ref))'),),
  'mutable': False})

EXPECTED_FOREIGN_KEYS = (('development_program_heads',
  ('program_ref', 'current_program_version_ref'),
  'development_program_versions',
  ('program_ref', 'program_version_ref'),
  'RESTRICT',
  'RESTRICT',
  'DEFERRABLE INITIALLY DEFERRED'),
 ('development_program_versions',
  ('program_ref',),
  'development_program_heads',
  ('program_ref',),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_program_versions',
  ('program_ref', 'accepted_intent_revision_ref'),
  'development_accepted_intent_revisions',
  ('program_ref', 'accepted_intent_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_program_versions',
  ('program_ref', 'creating_decision_ref'),
  'development_decisions',
  ('program_ref', 'decision_ref'),
  'RESTRICT',
  'RESTRICT',
  'DEFERRABLE INITIALLY DEFERRED'),
 ('development_accepted_intent_revisions',
  ('program_ref',),
  'development_program_heads',
  ('program_ref',),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_accepted_intent_revisions',
  ('program_ref', 'prior_accepted_intent_revision_ref'),
  'development_accepted_intent_revisions',
  ('program_ref', 'accepted_intent_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_work_item_heads',
  ('program_ref',),
  'development_program_heads',
  ('program_ref',),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_work_item_heads',
  ('program_ref', 'work_item_ref', 'current_work_item_revision_ref'),
  'development_work_item_revisions',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'DEFERRABLE INITIALLY DEFERRED'),
 ('development_work_item_revisions',
  ('program_ref', 'work_item_ref'),
  'development_work_item_heads',
  ('program_ref', 'work_item_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_work_item_revisions',
  ('program_ref', 'work_item_ref', 'prior_work_item_revision_ref'),
  'development_work_item_revisions',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_work_item_revisions',
  ('program_ref', 'accepted_intent_revision_ref'),
  'development_accepted_intent_revisions',
  ('program_ref', 'accepted_intent_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_program_version_work_items',
  ('program_ref', 'program_version_ref'),
  'development_program_versions',
  ('program_ref', 'program_version_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_program_version_work_items',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'development_work_item_revisions',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_revision_edges',
  ('program_ref',),
  'development_program_heads',
  ('program_ref',),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_revision_edges',
  ('program_ref', 'from_accepted_intent_revision_ref'),
  'development_accepted_intent_revisions',
  ('program_ref', 'accepted_intent_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_revision_edges',
  ('program_ref', 'to_accepted_intent_revision_ref'),
  'development_accepted_intent_revisions',
  ('program_ref', 'accepted_intent_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_revision_edges',
  ('program_ref', 'from_work_item_revision_ref'),
  'development_work_item_revisions',
  ('program_ref', 'work_item_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_revision_edges',
  ('program_ref', 'to_work_item_revision_ref'),
  'development_work_item_revisions',
  ('program_ref', 'work_item_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_work_spec_bindings',
  ('program_ref', 'program_version_ref'),
  'development_program_versions',
  ('program_ref', 'program_version_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_work_spec_bindings',
  ('program_ref', 'accepted_intent_revision_ref'),
  'development_accepted_intent_revisions',
  ('program_ref', 'accepted_intent_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_work_spec_bindings',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'development_work_item_revisions',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_semantic_attempts',
  ('program_ref', 'program_version_ref'),
  'development_program_versions',
  ('program_ref', 'program_version_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_semantic_attempts',
  ('program_ref', 'accepted_intent_revision_ref'),
  'development_accepted_intent_revisions',
  ('program_ref', 'accepted_intent_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_semantic_attempts',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'development_work_item_revisions',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_semantic_attempts',
  ('program_ref', 'selection_decision_ref'),
  'development_decisions',
  ('program_ref', 'decision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_attempt_fences',
  ('program_ref', 'program_version_ref'),
  'development_program_versions',
  ('program_ref', 'program_version_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_attempt_fences',
  ('program_ref', 'accepted_intent_revision_ref'),
  'development_accepted_intent_revisions',
  ('program_ref', 'accepted_intent_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_attempt_fences',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'development_work_item_revisions',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_attempt_fences',
  ('program_ref', 'semantic_attempt_ref'),
  'development_semantic_attempts',
  ('program_ref', 'semantic_attempt_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_authority_evaluations',
  ('program_ref',),
  'development_program_heads',
  ('program_ref',),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_authority_evaluations',
  ('program_ref', 'semantic_attempt_ref'),
  'development_semantic_attempts',
  ('program_ref', 'semantic_attempt_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_authority_evaluations',
  ('program_ref', 'effect_intent_ref'),
  'development_effect_intents',
  ('program_ref', 'effect_intent_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_intents',
  ('program_ref', 'program_version_ref'),
  'development_program_versions',
  ('program_ref', 'program_version_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_intents',
  ('program_ref', 'semantic_attempt_ref'),
  'development_semantic_attempts',
  ('program_ref', 'semantic_attempt_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_intents',
  ('basis_decision_ref',),
  'development_decisions',
  ('decision_ref',),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_intents',
  ('program_ref', 'command_ref'),
  'development_author_commands',
  ('program_ref', 'command_ref'),
  'RESTRICT',
  'RESTRICT',
  'DEFERRABLE INITIALLY DEFERRED'),
 ('development_effect_intents',
  ('program_ref', 'cancellation_target_effect_intent_ref'),
  'development_effect_intents',
  ('program_ref', 'effect_intent_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_fences',
  ('program_ref', 'program_version_ref'),
  'development_program_versions',
  ('program_ref', 'program_version_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_fences',
  ('program_ref', 'accepted_intent_revision_ref'),
  'development_accepted_intent_revisions',
  ('program_ref', 'accepted_intent_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_fences',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'development_work_item_revisions',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_fences',
  ('program_ref', 'semantic_attempt_ref'),
  'development_semantic_attempts',
  ('program_ref', 'semantic_attempt_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_fences',
  ('program_ref', 'effect_intent_ref'),
  'development_effect_intents',
  ('program_ref', 'effect_intent_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_fences',
  ('program_ref', 'attempt_fence_ref'),
  'development_attempt_fences',
  ('program_ref', 'attempt_fence_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_fences',
  ('program_ref', 'command_ref'),
  'development_author_commands',
  ('program_ref', 'command_ref'),
  'RESTRICT',
  'RESTRICT',
  'DEFERRABLE INITIALLY DEFERRED'),
 ('development_effect_fences',
  ('program_ref', 'cancellation_target_effect_intent_ref'),
  'development_effect_intents',
  ('program_ref', 'effect_intent_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_fences',
  ('program_ref', 'cancellation_target_effect_fence_ref'),
  'development_effect_fences',
  ('program_ref', 'effect_fence_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_author_commands',
  ('program_ref', 'program_version_ref'),
  'development_program_versions',
  ('program_ref', 'program_version_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_author_commands',
  ('program_ref', 'accepted_intent_revision_ref'),
  'development_accepted_intent_revisions',
  ('program_ref', 'accepted_intent_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_author_commands',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'development_work_item_revisions',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_author_commands',
  ('program_ref', 'semantic_attempt_ref'),
  'development_semantic_attempts',
  ('program_ref', 'semantic_attempt_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_author_commands',
  ('program_ref', 'effect_intent_ref'),
  'development_effect_intents',
  ('program_ref', 'effect_intent_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_author_commands',
  ('program_ref', 'attempt_fence_ref'),
  'development_attempt_fences',
  ('program_ref', 'attempt_fence_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_author_commands',
  ('program_ref', 'effect_fence_ref'),
  'development_effect_fences',
  ('program_ref', 'effect_fence_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_author_commands',
  ('work_spec_ref',),
  'development_work_spec_bindings',
  ('work_spec_ref',),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_heads',
  ('program_ref', 'effect_intent_ref'),
  'development_effect_intents',
  ('program_ref', 'effect_intent_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_heads',
  ('program_ref', 'current_effect_fence_ref'),
  'development_effect_fences',
  ('program_ref', 'effect_fence_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_effect_heads',
  ('program_ref', 'cancellation_effect_intent_ref'),
  'development_effect_intents',
  ('program_ref', 'effect_intent_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_delivery_attempts',
  ('program_ref', 'program_version_ref'),
  'development_program_versions',
  ('program_ref', 'program_version_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_delivery_attempts',
  ('program_ref', 'command_ref'),
  'development_author_commands',
  ('program_ref', 'command_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_delivery_attempts',
  ('program_ref', 'semantic_attempt_ref'),
  'development_semantic_attempts',
  ('program_ref', 'semantic_attempt_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_delivery_attempts',
  ('program_ref', 'effect_intent_ref'),
  'development_effect_intents',
  ('program_ref', 'effect_intent_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_delivery_attempts',
  ('program_ref', 'attempt_fence_ref'),
  'development_attempt_fences',
  ('program_ref', 'attempt_fence_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_delivery_attempts',
  ('program_ref', 'effect_fence_ref'),
  'development_effect_fences',
  ('program_ref', 'effect_fence_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_delivery_attempts',
  ('program_ref', 'predecessor_delivery_attempt_ref'),
  'development_delivery_attempts',
  ('program_ref', 'delivery_attempt_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_delivery_attempts',
  ('program_ref', 'basis_decision_ref'),
  'development_decisions',
  ('program_ref', 'decision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_delivery_heads',
  ('program_ref', 'effect_intent_ref'),
  'development_effect_intents',
  ('program_ref', 'effect_intent_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_delivery_heads',
  ('program_ref', 'current_delivery_attempt_ref'),
  'development_delivery_attempts',
  ('program_ref', 'delivery_attempt_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_decisions',
  ('program_ref',),
  'development_program_heads',
  ('program_ref',),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_decisions',
  ('program_ref', 'basis_decision_ref'),
  'development_decisions',
  ('program_ref', 'decision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_decisions',
  ('program_ref', 'basis_program_version_ref'),
  'development_program_versions',
  ('program_ref', 'program_version_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_decisions',
  ('program_ref', 'resulting_program_version_ref'),
  'development_program_versions',
  ('program_ref', 'program_version_ref'),
  'RESTRICT',
  'RESTRICT',
  'DEFERRABLE INITIALLY DEFERRED'),
 ('development_decisions',
  ('program_ref', 'selected_semantic_attempt_ref'),
  'development_semantic_attempts',
  ('program_ref', 'semantic_attempt_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_decisions',
  ('program_ref', 'selected_attempt_fence_ref'),
  'development_attempt_fences',
  ('program_ref', 'attempt_fence_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_decisions',
  ('program_ref', 'target_effect_intent_ref'),
  'development_effect_intents',
  ('program_ref', 'effect_intent_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_decisions',
  ('program_ref', 'target_effect_fence_ref'),
  'development_effect_fences',
  ('program_ref', 'effect_fence_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_decisions',
  ('program_ref', 'target_delivery_attempt_ref'),
  'development_delivery_attempts',
  ('program_ref', 'delivery_attempt_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_decisions',
  ('program_ref', 'originating_command_ref'),
  'development_author_commands',
  ('program_ref', 'command_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_decisions',
  ('program_ref', 'resulting_accepted_intent_revision_ref'),
  'development_accepted_intent_revisions',
  ('program_ref', 'accepted_intent_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_decisions',
  ('program_ref', 'resulting_work_item_ref', 'resulting_work_item_revision_ref'),
  'development_work_item_revisions',
  ('program_ref', 'work_item_ref', 'work_item_revision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_mutation_receipts',
  ('program_ref',),
  'development_program_heads',
  ('program_ref',),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_mutation_receipts',
  ('program_ref', 'decision_ref'),
  'development_decisions',
  ('program_ref', 'decision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_mutation_receipts',
  ('program_ref', 'result_program_version_ref'),
  'development_program_versions',
  ('program_ref', 'program_version_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_mutation_receipts',
  ('program_ref', 'result_semantic_attempt_ref'),
  'development_semantic_attempts',
  ('program_ref', 'semantic_attempt_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_mutation_receipts',
  ('program_ref', 'result_effect_intent_ref'),
  'development_effect_intents',
  ('program_ref', 'effect_intent_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_mutation_receipts',
  ('program_ref', 'result_effect_fence_ref'),
  'development_effect_fences',
  ('program_ref', 'effect_fence_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_mutation_receipts',
  ('program_ref', 'result_delivery_attempt_ref'),
  'development_delivery_attempts',
  ('program_ref', 'delivery_attempt_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'),
 ('development_mutation_receipts',
  ('program_ref', 'result_decision_ref'),
  'development_decisions',
  ('program_ref', 'decision_ref'),
  'RESTRICT',
  'RESTRICT',
  'NOT DEFERRABLE INITIALLY IMMEDIATE'))

EXPECTED_TRIGGERS = (('development_program_versions_no_update',
  'development_program_versions',
  'UPDATE',
  'CREATE TRIGGER development_program_versions_no_update\n'
  'BEFORE UPDATE ON development_program_versions\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_program_versions');\n"
  'END;'),
 ('development_program_versions_no_delete',
  'development_program_versions',
  'DELETE',
  'CREATE TRIGGER development_program_versions_no_delete\n'
  'BEFORE DELETE ON development_program_versions\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_program_versions');\n"
  'END;'),
 ('development_accepted_intent_revisions_no_update',
  'development_accepted_intent_revisions',
  'UPDATE',
  'CREATE TRIGGER development_accepted_intent_revisions_no_update\n'
  'BEFORE UPDATE ON development_accepted_intent_revisions\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_accepted_intent_revisions');\n"
  'END;'),
 ('development_accepted_intent_revisions_no_delete',
  'development_accepted_intent_revisions',
  'DELETE',
  'CREATE TRIGGER development_accepted_intent_revisions_no_delete\n'
  'BEFORE DELETE ON development_accepted_intent_revisions\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_accepted_intent_revisions');\n"
  'END;'),
 ('development_work_item_revisions_no_update',
  'development_work_item_revisions',
  'UPDATE',
  'CREATE TRIGGER development_work_item_revisions_no_update\n'
  'BEFORE UPDATE ON development_work_item_revisions\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_work_item_revisions');\n"
  'END;'),
 ('development_work_item_revisions_no_delete',
  'development_work_item_revisions',
  'DELETE',
  'CREATE TRIGGER development_work_item_revisions_no_delete\n'
  'BEFORE DELETE ON development_work_item_revisions\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_work_item_revisions');\n"
  'END;'),
 ('development_program_version_work_items_no_update',
  'development_program_version_work_items',
  'UPDATE',
  'CREATE TRIGGER development_program_version_work_items_no_update\n'
  'BEFORE UPDATE ON development_program_version_work_items\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_program_version_work_items');\n"
  'END;'),
 ('development_program_version_work_items_no_delete',
  'development_program_version_work_items',
  'DELETE',
  'CREATE TRIGGER development_program_version_work_items_no_delete\n'
  'BEFORE DELETE ON development_program_version_work_items\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_program_version_work_items');\n"
  'END;'),
 ('development_revision_edges_no_update',
  'development_revision_edges',
  'UPDATE',
  'CREATE TRIGGER development_revision_edges_no_update\n'
  'BEFORE UPDATE ON development_revision_edges\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_revision_edges');\n"
  'END;'),
 ('development_revision_edges_no_delete',
  'development_revision_edges',
  'DELETE',
  'CREATE TRIGGER development_revision_edges_no_delete\n'
  'BEFORE DELETE ON development_revision_edges\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_revision_edges');\n"
  'END;'),
 ('development_work_spec_bindings_no_update',
  'development_work_spec_bindings',
  'UPDATE',
  'CREATE TRIGGER development_work_spec_bindings_no_update\n'
  'BEFORE UPDATE ON development_work_spec_bindings\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_work_spec_bindings');\n"
  'END;'),
 ('development_work_spec_bindings_no_delete',
  'development_work_spec_bindings',
  'DELETE',
  'CREATE TRIGGER development_work_spec_bindings_no_delete\n'
  'BEFORE DELETE ON development_work_spec_bindings\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_work_spec_bindings');\n"
  'END;'),
 ('development_semantic_attempts_no_update',
  'development_semantic_attempts',
  'UPDATE',
  'CREATE TRIGGER development_semantic_attempts_no_update\n'
  'BEFORE UPDATE ON development_semantic_attempts\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_semantic_attempts');\n"
  'END;'),
 ('development_semantic_attempts_no_delete',
  'development_semantic_attempts',
  'DELETE',
  'CREATE TRIGGER development_semantic_attempts_no_delete\n'
  'BEFORE DELETE ON development_semantic_attempts\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_semantic_attempts');\n"
  'END;'),
 ('development_attempt_fences_no_update',
  'development_attempt_fences',
  'UPDATE',
  'CREATE TRIGGER development_attempt_fences_no_update\n'
  'BEFORE UPDATE ON development_attempt_fences\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_attempt_fences');\n"
  'END;'),
 ('development_attempt_fences_no_delete',
  'development_attempt_fences',
  'DELETE',
  'CREATE TRIGGER development_attempt_fences_no_delete\n'
  'BEFORE DELETE ON development_attempt_fences\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_attempt_fences');\n"
  'END;'),
 ('development_authority_evaluations_no_update',
  'development_authority_evaluations',
  'UPDATE',
  'CREATE TRIGGER development_authority_evaluations_no_update\n'
  'BEFORE UPDATE ON development_authority_evaluations\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_authority_evaluations');\n"
  'END;'),
 ('development_authority_evaluations_no_delete',
  'development_authority_evaluations',
  'DELETE',
  'CREATE TRIGGER development_authority_evaluations_no_delete\n'
  'BEFORE DELETE ON development_authority_evaluations\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_authority_evaluations');\n"
  'END;'),
 ('development_effect_intents_no_update',
  'development_effect_intents',
  'UPDATE',
  'CREATE TRIGGER development_effect_intents_no_update\n'
  'BEFORE UPDATE ON development_effect_intents\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_effect_intents');\n"
  'END;'),
 ('development_effect_intents_no_delete',
  'development_effect_intents',
  'DELETE',
  'CREATE TRIGGER development_effect_intents_no_delete\n'
  'BEFORE DELETE ON development_effect_intents\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_effect_intents');\n"
  'END;'),
 ('development_effect_fences_no_update',
  'development_effect_fences',
  'UPDATE',
  'CREATE TRIGGER development_effect_fences_no_update\n'
  'BEFORE UPDATE ON development_effect_fences\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_effect_fences');\n"
  'END;'),
 ('development_effect_fences_no_delete',
  'development_effect_fences',
  'DELETE',
  'CREATE TRIGGER development_effect_fences_no_delete\n'
  'BEFORE DELETE ON development_effect_fences\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_effect_fences');\n"
  'END;'),
 ('development_author_commands_no_update',
  'development_author_commands',
  'UPDATE',
  'CREATE TRIGGER development_author_commands_no_update\n'
  'BEFORE UPDATE ON development_author_commands\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_author_commands');\n"
  'END;'),
 ('development_author_commands_no_delete',
  'development_author_commands',
  'DELETE',
  'CREATE TRIGGER development_author_commands_no_delete\n'
  'BEFORE DELETE ON development_author_commands\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_author_commands');\n"
  'END;'),
 ('development_delivery_attempts_no_update',
  'development_delivery_attempts',
  'UPDATE',
  'CREATE TRIGGER development_delivery_attempts_no_update\n'
  'BEFORE UPDATE ON development_delivery_attempts\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_delivery_attempts');\n"
  'END;'),
 ('development_delivery_attempts_no_delete',
  'development_delivery_attempts',
  'DELETE',
  'CREATE TRIGGER development_delivery_attempts_no_delete\n'
  'BEFORE DELETE ON development_delivery_attempts\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_delivery_attempts');\n"
  'END;'),
 ('development_decisions_no_update',
  'development_decisions',
  'UPDATE',
  'CREATE TRIGGER development_decisions_no_update\n'
  'BEFORE UPDATE ON development_decisions\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_decisions');\n"
  'END;'),
 ('development_decisions_no_delete',
  'development_decisions',
  'DELETE',
  'CREATE TRIGGER development_decisions_no_delete\n'
  'BEFORE DELETE ON development_decisions\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_decisions');\n"
  'END;'),
 ('development_mutation_receipts_no_update',
  'development_mutation_receipts',
  'UPDATE',
  'CREATE TRIGGER development_mutation_receipts_no_update\n'
  'BEFORE UPDATE ON development_mutation_receipts\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_mutation_receipts');\n"
  'END;'),
 ('development_mutation_receipts_no_delete',
  'development_mutation_receipts',
  'DELETE',
  'CREATE TRIGGER development_mutation_receipts_no_delete\n'
  'BEFORE DELETE ON development_mutation_receipts\n'
  'BEGIN\n'
  "  SELECT RAISE(ABORT, 'append_only_development_mutation_receipts');\n"
  'END;'))


EXPECTED_TABLE_NAMES = tuple(table["name"] for table in EXPECTED_TABLES)
EXPECTED_IMMUTABLE_TABLE_NAMES = tuple(
    table["name"] for table in EXPECTED_TABLES if not table["mutable"]
)
EXPECTED_MUTABLE_TABLE_NAMES = tuple(
    table["name"] for table in EXPECTED_TABLES if table["mutable"]
)


def _render_expected_statements() -> tuple[str, ...]:
    foreign_keys_by_table: dict[str, list[tuple[Any, ...]]] = {
        table_name: [] for table_name in EXPECTED_TABLE_NAMES
    }
    for foreign_key in EXPECTED_FOREIGN_KEYS:
        foreign_keys_by_table[foreign_key[0]].append(foreign_key)

    statements: list[str] = []
    for table in EXPECTED_TABLES:
        members: list[str] = []
        for name, declaration, nullable, check_sql, _pk_ordinal in table["columns"]:
            member = f"{name} {declaration}"
            if not nullable:
                member += " NOT NULL"
            member += f" CHECK ({check_sql})"
            members.append(member)
        members.append(f"PRIMARY KEY ({', '.join(table['primary_key'])})")
        for unique_columns in table["unique_constraints"]:
            members.append(f"UNIQUE ({', '.join(unique_columns)})")
        for check_name, check_sql in table["table_checks"]:
            members.append(f"CONSTRAINT {check_name} CHECK ({check_sql})")
        for (
            _child_table,
            child_columns,
            parent_table,
            parent_columns,
            on_update,
            on_delete,
            deferrability,
        ) in foreign_keys_by_table[table["name"]]:
            members.append(
                f"FOREIGN KEY ({', '.join(child_columns)}) "
                f"REFERENCES {parent_table} ({', '.join(parent_columns)}) "
                f"ON UPDATE {on_update} ON DELETE {on_delete} {deferrability}"
            )
        statements.append(
            f"CREATE TABLE {table['name']} (\n"
            + ",\n".join(f"  {member}" for member in members)
            + "\n) STRICT;"
        )
    statements.append(EXPECTED_INDEX_SQL)
    statements.extend(trigger[3] for trigger in EXPECTED_TRIGGERS)
    return tuple(statements)


def _expected_sql_text() -> str:
    return "\n\n".join(_render_expected_statements()) + "\n"


def _location(tmp_path: Path, name: str) -> CoordinatorStateLocation:
    return CoordinatorStateLocation.from_trusted_root(tmp_path / name / "state")


def _prefix_one_catalog() -> migration_module.MigrationCatalog:
    production = migration_module.load_migration_catalog()
    return migration_module.MigrationCatalog(migrations=(production.migrations[0],))


def _assessment_for_catalog_prefix(
    catalog: migration_module.MigrationCatalog,
    sequence: int,
    disposition: migration_module._MigrationDatabaseDisposition,
) -> migration_module._MigrationDatabaseAssessment:
    history = tuple(
        migration_module._MigrationHistoryRow(
            migration_id=migration.migration_id,
            sequence=migration.sequence,
            schema_digest=migration.checksum,
            applied_at="2026-08-14T00:00:00Z",
            min_app_schema=migration.min_app_schema,
            max_app_schema=migration.max_app_schema,
        )
        for migration in catalog.migrations[:sequence]
    )
    return migration_module._MigrationDatabaseAssessment(
        disposition=disposition,
        history=history,
    )


def _initialize_prefix_one(location: CoordinatorStateLocation):
    return migration_module._initialize_database_with_catalog(
        location,
        _prefix_one_catalog(),
        current_app_schema=1,
        verify_managed_invariants=True,
    )


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _history_rows(location: CoordinatorStateLocation) -> list[tuple[Any, ...]]:
    with closing(sqlite3.connect(location.database_path)) as connection, connection:
        return connection.execute(
            """
            SELECT migration_id, sequence, schema_digest, applied_at,
                   min_app_schema, max_app_schema
            FROM schema_migrations
            ORDER BY sequence
            """
        ).fetchall()


def _schema_counts(connection: sqlite3.Connection) -> dict[str, int]:
    schema_rows = connection.execute(
        """
        SELECT type, name
        FROM sqlite_schema
        WHERE name NOT LIKE 'sqlite_%'
        ORDER BY type, name
        """
    ).fetchall()
    tables = tuple(name for object_type, name in schema_rows if object_type == "table")
    return {
        "tables": len(tables),
        "columns": sum(
            len(connection.execute(f'PRAGMA table_xinfo("{table}")').fetchall())
            for table in tables
        ),
        "triggers": sum(object_type == "trigger" for object_type, _name in schema_rows),
        "indexes": sum(object_type == "index" for object_type, _name in schema_rows),
        "views": sum(object_type == "view" for object_type, _name in schema_rows),
        "foreign_keys": sum(
            len(
                {
                    row[0]
                    for row in connection.execute(
                        f'PRAGMA foreign_key_list("{table}")'
                    ).fetchall()
                }
            )
            for table in tables
        ),
    }


def _user_table_names(connection: sqlite3.Connection) -> tuple[str, ...]:
    return tuple(
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_schema "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    )


def _canonical_table_row_snapshot(
    connection: sqlite3.Connection,
    table_names: tuple[str, ...],
) -> tuple[tuple[str, tuple[str, ...], tuple[tuple[Any, ...], ...]], ...]:
    snapshot = []
    for table in table_names:
        columns = tuple(
            row[1]
            for row in connection.execute(f'PRAGMA table_xinfo("{table}")')
        )
        rows = tuple(
            sorted(
                (
                    tuple(row)
                    for row in connection.execute(f'SELECT * FROM "{table}"')
                ),
                key=repr,
            )
        )
        snapshot.append((table, columns, rows))
    return tuple(snapshot)


def _canonical_snapshot_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _normalized_complete_schema_manifest(
    connection: sqlite3.Connection,
) -> tuple[tuple[str, str, str, str | None], ...]:
    return tuple(
        (
            object_type,
            name,
            table_name,
            None if sql is None else " ".join(sql.split()),
        )
        for object_type, name, table_name, sql in connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_schema "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        )
    )


def _seed_terminal_0002_genesis_family(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("BEGIN IMMEDIATE")
    connection.execute("PRAGMA defer_foreign_keys=ON")
    connection.execute(
        """
        INSERT INTO development_program_heads
            (schema_id, program_ref, current_program_version_ref,
             current_program_version_number, head_revision, program_state,
             updated_at, head_digest)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "governed-execution.nwp-development-program-head.v1",
            "program-migration-prefix-1",
            "program-version-migration-prefix-1",
            1,
            0,
            "active",
            "2026-08-14T00:00:01Z",
            "1" * 64,
        ),
    )
    connection.execute(
        """
        INSERT INTO development_accepted_intent_revisions
            (schema_id, accepted_intent_revision_ref, program_ref,
             accepted_intent_revision_number, prior_accepted_intent_revision_ref,
             source_intent_ref, source_intent_digest, safe_projection_digest,
             created_at, accepted_intent_revision_digest)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "governed-execution.nwp-development-accepted-intent-revision.v1",
            "accepted-intent-migration-prefix-1",
            "program-migration-prefix-1",
            1,
            None,
            "source-intent-migration-prefix-1",
            "2" * 64,
            "3" * 64,
            "2026-08-14T00:00:01Z",
            "4" * 64,
        ),
    )
    connection.execute(
        """
        INSERT INTO development_program_versions
            (schema_id, program_version_ref, program_ref,
             program_version_number, program_version_kind,
             creating_decision_ref, accepted_intent_revision_ref,
             created_at, program_version_digest)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "governed-execution.nwp-development-program-version.v1",
            "program-version-migration-prefix-1",
            "program-migration-prefix-1",
            1,
            "initial",
            "decision-migration-prefix-1",
            "accepted-intent-migration-prefix-1",
            "2026-08-14T00:00:01Z",
            "5" * 64,
        ),
    )
    connection.execute(
        """
        INSERT INTO development_decisions
            (schema_id, mutation_ref, decision_ref, program_ref,
             decision_kind, decision_variant, expected_program_head_revision,
             resulting_program_version_ref, resulting_program_version_number,
             coding_global_stop_ref, coding_global_stop_version,
             preassigned_semantic_attempt_ref, preassigned_candidate_ref,
             reason_code, decided_at, decision_digest)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "governed-execution.nwp-development-decision.v1",
            "mutation-migration-prefix-1",
            "decision-migration-prefix-1",
            "program-migration-prefix-1",
            "initialize",
            "program_genesis",
            0,
            "program-version-migration-prefix-1",
            1,
            "coding-global-stop-migration-prefix-1",
            0,
            "semantic-attempt-migration-prefix-1",
            "candidate-migration-prefix-1",
            "program.genesis",
            "2026-08-14T00:00:01Z",
            "6" * 64,
        ),
    )
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    connection.execute("COMMIT")


def _create_database_from_literal_sql(
    location: CoordinatorStateLocation,
    *,
    migration_0002_sql: str | None,
    history_sequences: tuple[int, ...],
    history_0002_checksum: str = EXPECTED_SHA256,
) -> None:
    location.state_root.mkdir(mode=0o700, parents=True)
    migration_0001 = MIGRATION_0001_PATH.read_text(encoding="utf-8")
    catalog = migration_module.load_migration_catalog()
    with closing(
        sqlite3.connect(location.database_path, isolation_level=None)
    ) as connection, connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        for statement in migration_module._migration_statements(migration_0001):
            connection.execute(statement)
        if migration_0002_sql is not None:
            for statement in migration_module._migration_statements(migration_0002_sql):
                connection.execute(statement)
        for sequence in history_sequences:
            migration = catalog.by_sequence(sequence)
            assert migration is not None
            connection.execute(
                """
                INSERT INTO schema_migrations
                    (migration_id, sequence, schema_digest, applied_at,
                     min_app_schema, max_app_schema)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    migration.migration_id,
                    migration.sequence,
                    history_0002_checksum if sequence == 2 else migration.checksum,
                    "2026-08-14T00:00:00Z",
                    migration.min_app_schema,
                    migration.max_app_schema,
                ),
            )
        connection.execute("COMMIT")
    location.database_path.chmod(0o600)


def _assert_safe_unknown(location: CoordinatorStateLocation) -> None:
    inspection = migration_module.inspect_database(location)
    assert inspection.classification is migration_module.DatabaseClassification.UNKNOWN
    assert inspection.current_sequence == 0
    assert inspection.latest_sequence == CURRENT_SEQUENCE
    assert inspection.current_migration_id is None
    assert inspection.reason in {
        "migration_checksum_mismatch",
        "migration_history_invalid",
        "schema_fingerprint_mismatch",
        "schema_verification_failed",
    }
    rendered = repr(inspection) + str(inspection.reason)
    assert str(location.state_root) not in rendered
    assert "CREATE TABLE" not in rendered


def test_literal_sql_identity_format_statement_order_and_complete_oracle() -> None:
    payload = MIGRATION_0002_PATH.read_bytes()
    text = payload.decode("utf-8", "strict")
    expected_statements = _render_expected_statements()

    assert len(payload) == EXPECTED_SIZE
    assert hashlib.sha256(payload).hexdigest() == EXPECTED_SHA256
    assert text == _expected_sql_text()
    assert migration_module._migration_statements(text) == expected_statements
    assert len(expected_statements) == EXPECTED_STATEMENT_COUNT
    assert tuple(
        statement.split(" ", 2)[2].split(" ", 1)[0]
        for statement in expected_statements[:19]
    ) == EXPECTED_TABLE_NAMES
    assert expected_statements[19] == EXPECTED_INDEX_SQL
    assert expected_statements[20:] == tuple(trigger[3] for trigger in EXPECTED_TRIGGERS)
    assert sum(statement.startswith("CREATE TABLE ") for statement in expected_statements) == 19
    assert sum(statement.startswith("CREATE UNIQUE INDEX ") for statement in expected_statements) == 1
    assert sum(statement.startswith("CREATE TRIGGER ") for statement in expected_statements) == 30
    assert all(
        not statement.lstrip().startswith(("PRAGMA", "BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE"))
        for statement in expected_statements
    )
    assert "CREATE VIEW" not in text
    assert "INSERT INTO" not in text
    assert "\x00" not in text
    assert "\r" not in text
    assert not payload.startswith(b"\xef\xbb\xbf")
    assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
    assert all(line.rstrip(" \t") == line for line in text.splitlines())


def test_literal_table_column_key_check_fk_trigger_and_index_inventory() -> None:
    assert len(EXPECTED_TABLES) == 19
    assert sum(len(table["columns"]) for table in EXPECTED_TABLES) == EXPECTED_NEW_COLUMN_COUNT
    assert all(column[1] == "ANY" for table in EXPECTED_TABLES for column in table["columns"])
    assert len(EXPECTED_IMMUTABLE_TABLE_NAMES) == EXPECTED_NEW_IMMUTABLE_TABLE_COUNT
    assert len(EXPECTED_MUTABLE_TABLE_NAMES) == EXPECTED_NEW_MUTABLE_TABLE_COUNT
    assert len(EXPECTED_FOREIGN_KEYS) == EXPECTED_NEW_FOREIGN_KEY_COUNT
    assert sum(item[6] == "DEFERRABLE INITIALLY DEFERRED" for item in EXPECTED_FOREIGN_KEYS) == 6
    assert len(EXPECTED_TRIGGERS) == 30
    assert len({trigger[0] for trigger in EXPECTED_TRIGGERS}) == 30
    assert tuple(trigger[1] for trigger in EXPECTED_TRIGGERS[::2]) == EXPECTED_IMMUTABLE_TABLE_NAMES
    assert all(
        EXPECTED_TRIGGERS[offset][2:] == (
            "UPDATE",
            EXPECTED_TRIGGERS[offset][3],
        )
        for offset in range(0, len(EXPECTED_TRIGGERS), 2)
    )
    assert all(
        EXPECTED_TRIGGERS[offset][2] == "UPDATE"
        and EXPECTED_TRIGGERS[offset + 1][2] == "DELETE"
        for offset in range(0, len(EXPECTED_TRIGGERS), 2)
    )

    connection = sqlite3.connect(":memory:", isolation_level=None)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        for statement in _render_expected_statements():
            connection.execute(statement)
        for table in EXPECTED_TABLES:
            rows = connection.execute(
                f'PRAGMA table_xinfo("{table["name"]}")'
            ).fetchall()
            assert tuple((row[1], row[2], not bool(row[3]), row[5]) for row in rows) == tuple(
                (name, declaration, nullable, pk_ordinal)
                for name, declaration, nullable, _check_sql, pk_ordinal in table["columns"]
            )
            schema_sql = connection.execute(
                "SELECT sql FROM sqlite_schema WHERE type='table' AND name=?",
                (table["name"],),
            ).fetchone()[0]
            expected_statement = next(
                statement
                for statement in _render_expected_statements()
                if statement.startswith(f"CREATE TABLE {table['name']} ")
            )
            assert schema_sql == expected_statement.removesuffix(";")
            assert connection.execute(
                f'SELECT COUNT(*) FROM "{table["name"]}"'
            ).fetchone() == (0,)
        observed_fk_count = sum(
            len(
                {
                    row[0]
                    for row in connection.execute(
                        f'PRAGMA foreign_key_list("{table_name}")'
                    ).fetchall()
                }
            )
            for table_name in EXPECTED_TABLE_NAMES
        )
        assert observed_fk_count == EXPECTED_NEW_FOREIGN_KEY_COUNT
        observed_triggers = tuple(
            connection.execute(
                "SELECT name, tbl_name, sql FROM sqlite_schema WHERE type='trigger' ORDER BY rowid"
            ).fetchall()
        )
        assert observed_triggers == tuple(
            (name, table, body.removesuffix(";"))
            for name, table, _operation, body in EXPECTED_TRIGGERS
        )
        observed_indexes = connection.execute(
            """
            SELECT name, sql FROM sqlite_schema
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
        assert observed_indexes == [
            (
                "uq_development_effect_intents_author_command",
                EXPECTED_INDEX_SQL.removesuffix(";"),
            )
        ]
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_schema WHERE type='view'"
        ).fetchone() == (0,)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        connection.execute("ROLLBACK")
    finally:
        connection.close()


def test_current_migration_documentation_matches_catalog_and_scopes_historical_0002() -> None:
    catalog = migration_module.load_migration_catalog()
    production = _PRODUCTION_CATALOG_LOADER()
    assert tuple(item.sequence for item in production.migrations) == (1, 2, 3, 4, 5, 6, 7, 8, 9)
    assert production.migrations[-1].migration_id == "0009_rw0_terminal_anchor_registry"
    migrations = catalog.migrations
    current_tip = migrations[-1].migration_id
    complete_catalog = "[" + ", ".join(item.migration_id for item in migrations) + "]"
    short_catalog = "[" + ", ".join(f"{item.sequence:04d}" for item in migrations) + "]"
    resource_count = len(migrations)

    document_paths = (
        REPOSITORY_ROOT / ".docs/c2b2-migration-0002.md",
        REPOSITORY_ROOT / ".docs/sqlite-state-backend-adr.md",
        REPOSITORY_ROOT / ".docs/b3-transition-persistence-contract.md",
        REPOSITORY_ROOT / ".docs/b3c0a-transition-authority-and-order.md",
        REPOSITORY_ROOT / ".docs/autonomous-software-development-operating-model.md",
        REPOSITORY_ROOT / ".docs/architecture.md",
        REPOSITORY_ROOT / ".docs/durable-state-model.md",
    )
    sources = {path: path.read_text(encoding="utf-8") for path in document_paths}
    migration_status = " ".join(sources[document_paths[0]].split())
    backend_status = " ".join(sources[document_paths[1]].split())

    assert migration_module.CURRENT_APPLICATION_SCHEMA == 2
    assert complete_catalog in migration_status
    assert short_catalog in migration_status
    assert current_tip in migration_status
    assert current_tip in backend_status
    assert f"current production SQL resource count is `{resource_count}`" in migration_status
    assert f"current production SQL resource count is `{resource_count}`" in backend_status
    current_catalog = "[" + ", ".join(item.migration_id for item in production.migrations) + "]"
    assert current_catalog in migration_status
    assert "current production SQL resource count is `7`" in migration_status
    assert "current production SQL resource count is `7`" in backend_status
    assert "Migration 0002 is an unchanged historical prefix" in migration_status
    assert "Migration 0002 remains an unchanged historical prefix" in backend_status
    assert "C2B2 did not implement or acquire ownership of migration 0003" in migration_status
    assert "C2B2 did not implement or acquire ownership of migration 0003" in backend_status

    historical_claims = []
    for path in document_paths[:2]:
        for paragraph in sources[path].split("\n\n"):
            compacted = " ".join(paragraph.split())
            lowered = compacted.lower()
            if (
                "exactly two production sql" in lowered
                or "fresh initialization selected `[0001, 0002]`" in lowered
            ):
                historical_claims.append(compacted)
    assert len(historical_claims) == 3
    for paragraph in historical_claims:
        assert "tranche completion" in paragraph.lower()
        assert "historical" in paragraph.lower()

    current_stale_claims = (
        "the cumulative physical tip is now migration 0002",
        "migration 0003 remains absent",
        "migration 0003 and all source/runtime remain absent",
        "temporary current-generation-2 database at terminal migration `0002_development_program_and_effect_state`",
        "current physical generation-2, terminal-0002 database",
        "exact generation-2 tip 0002 is managed current state",
    )
    for source in sources.values():
        current_text = " ".join(source.split()).lower()
        for stale in current_stale_claims:
            assert stale not in current_text


def test_generation_two_catalog_is_exact_and_0001_is_preserved() -> None:
    catalog = migration_module.load_migration_catalog()

    assert migration_module.CURRENT_APPLICATION_SCHEMA == 2
    assert tuple(migration.migration_id for migration in catalog.migrations) == (
        "0001_initial",
        EXPECTED_MIGRATION_ID,
        SECTION41_MIGRATION_ID,
        RW0_C1_MIGRATION_ID,
        CURRENT_MIGRATION_ID,
    )
    assert tuple(migration.sequence for migration in catalog.migrations) == (1, 2, 3, 4, 5)
    assert tuple(migration.resource_name for migration in catalog.migrations) == (
        "0001_initial.sql",
        EXPECTED_RESOURCE_NAME,
        SECTION41_RESOURCE_NAME,
        RW0_C1_RESOURCE_NAME,
        CURRENT_RESOURCE_NAME,
    )
    assert hashlib.sha256(MIGRATION_0001_PATH.read_bytes()).hexdigest() == EXPECTED_MIGRATION_0001_SHA256
    first, second, third, fourth, fifth = catalog.migrations
    assert (first.min_app_schema, first.max_app_schema, first.destructive) == (1, 1, False)
    assert (
        second.migration_id,
        second.sequence,
        second.resource_name,
        second.checksum,
        second.min_app_schema,
        second.max_app_schema,
        second.destructive,
    ) == (
        EXPECTED_MIGRATION_ID,
        EXPECTED_SEQUENCE,
        EXPECTED_RESOURCE_NAME,
        EXPECTED_SHA256,
        *EXPECTED_COMPATIBILITY,
        EXPECTED_DESTRUCTIVE,
    )
    assert second.sql_bytes == MIGRATION_0002_PATH.read_bytes()
    assert (
        third.migration_id,
        third.sequence,
        third.resource_name,
        third.checksum,
        third.min_app_schema,
        third.max_app_schema,
        third.destructive,
    ) == (
        SECTION41_MIGRATION_ID,
        3,
        SECTION41_RESOURCE_NAME,
        SECTION41_SHA256,
        2,
        2,
        False,
    )
    assert third.sql_bytes == MIGRATION_0003_PATH.read_bytes()
    assert (
        fourth.migration_id,
        fourth.sequence,
        fourth.resource_name,
        fourth.checksum,
        fourth.min_app_schema,
        fourth.max_app_schema,
        fourth.destructive,
    ) == (
        RW0_C1_MIGRATION_ID,
        4,
        RW0_C1_RESOURCE_NAME,
        RW0_C1_SHA256,
        2,
        2,
        False,
    )
    assert fourth.sql_bytes == MIGRATION_0004_PATH.read_bytes()
    assert (
        fifth.migration_id, fifth.sequence, fifth.resource_name,
        fifth.checksum, fifth.min_app_schema, fifth.max_app_schema,
        fifth.destructive,
    ) == (CURRENT_MIGRATION_ID, 5, CURRENT_RESOURCE_NAME, CURRENT_SHA256,
          2, 2, False)
    assert fifth.sql_bytes == MIGRATION_0005_PATH.read_bytes()
    assert tuple(sorted(path.name for path in MIGRATION_PACKAGE_PATH.glob("*.sql"))) == (
        "0001_initial.sql",
        EXPECTED_RESOURCE_NAME,
        SECTION41_RESOURCE_NAME,
        RW0_C1_RESOURCE_NAME,
        CURRENT_RESOURCE_NAME,
        "0006_rw0_c2_scope_admission.sql",
        "0007_rw0_c2_progression_decision.sql",
        "0008_rw0_terminal_outcome.sql",
        "0009_rw0_terminal_anchor_registry.sql",
    )


def test_fresh_generation_two_initialization_has_one_timestamp_and_exact_current_schema(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path, "fresh")

    inspection = migration_module.initialize_database(location)

    assert inspection == migration_module.DatabaseInspection(
        classification=migration_module.DatabaseClassification.MANAGED,
        current_sequence=CURRENT_SEQUENCE,
        latest_sequence=CURRENT_SEQUENCE,
        current_migration_id=CURRENT_MIGRATION_ID,
    )
    history = _history_rows(location)
    assert tuple(row[:3] + row[4:] for row in history) == (
        ("0001_initial", 1, EXPECTED_MIGRATION_0001_SHA256, 1, 1),
        (EXPECTED_MIGRATION_ID, 2, EXPECTED_SHA256, 2, 2),
        (SECTION41_MIGRATION_ID, 3, SECTION41_SHA256, 2, 2),
        (RW0_C1_MIGRATION_ID, 4, RW0_C1_SHA256, 2, 2),
        (CURRENT_MIGRATION_ID, 5, CURRENT_SHA256, 2, 2),
    )
    assert len({row[3] for row in history}) == 1
    with closing(sqlite3.connect(location.database_path)) as connection, connection:
        counts = _schema_counts(connection)
        assert counts == {
            "tables": EXPECTED_CUMULATIVE_TABLE_COUNT,
            "columns": EXPECTED_CUMULATIVE_COLUMN_COUNT,
            "triggers": EXPECTED_CUMULATIVE_TRIGGER_COUNT,
            "indexes": EXPECTED_CUMULATIVE_EXPLICIT_INDEX_COUNT,
            "views": 0,
            "foreign_keys": EXPECTED_CUMULATIVE_FOREIGN_KEY_COUNT,
        }
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert all(
            connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone() == (0,)
            for table in EXPECTED_TABLE_NAMES
        )
        strict_tables = {
            row[1] for row in connection.execute("PRAGMA table_list") if row[5] == 1
        }
        assert set(EXPECTED_TABLE_NAMES) <= strict_tables


def test_exact_0001_is_observationally_unknown_then_explicitly_migrates_complete_suffix(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path, "upgrade")
    prefix_inspection = _initialize_prefix_one(location)
    before_history = _history_rows(location)
    before_digest = _file_sha256(location.database_path)

    assert prefix_inspection.current_sequence == prefix_inspection.latest_sequence == 1
    ordinary = migration_module.inspect_database(location)
    assert ordinary.classification is migration_module.DatabaseClassification.UNKNOWN
    assert ordinary.reason == "database_schema_incompatible"
    assert ordinary.current_sequence == 0
    assert ordinary.latest_sequence == CURRENT_SEQUENCE
    assert _file_sha256(location.database_path) == before_digest

    migrated = migration_module.migrate_database(location)
    history = _history_rows(location)
    assert migrated.classification is migration_module.DatabaseClassification.MANAGED
    assert migrated.current_sequence == migrated.latest_sequence == CURRENT_SEQUENCE
    assert migrated.current_migration_id == CURRENT_MIGRATION_ID
    assert history[0] == before_history[0]
    assert history[1][0:3] == (EXPECTED_MIGRATION_ID, 2, EXPECTED_SHA256)
    assert history[1][4:] == (2, 2)
    assert history[2][0:3] == (SECTION41_MIGRATION_ID, 3, SECTION41_SHA256)
    assert history[2][4:] == (2, 2)
    assert history[3][0:3] == (RW0_C1_MIGRATION_ID, 4, RW0_C1_SHA256)
    assert history[3][4:] == (2, 2)
    assert history[4][0:3] == (CURRENT_MIGRATION_ID, 5, CURRENT_SHA256)
    assert history[4][4:] == (2, 2)
    assert history[1][3] == history[2][3] == history[3][3] == history[4][3]
    with closing(sqlite3.connect(location.database_path)) as connection, connection:
        assert _schema_counts(connection) == {
            "tables": 64,
            "columns": 1518,
            "triggers": 114,
            "indexes": 5,
            "views": 0,
            "foreign_keys": 197,
        }
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_exact_packaged_terminal_0002_applies_complete_suffix_and_matches_fresh_current_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upgrade = _location(tmp_path, "exact-terminal-0002")
    fresh = _location(tmp_path, "fresh-current")
    production_catalog = migration_module.load_migration_catalog()
    assert tuple(
        migration.migration_id for migration in production_catalog.migrations
    ) == (
        "0001_initial",
        EXPECTED_MIGRATION_ID,
        SECTION41_MIGRATION_ID,
        RW0_C1_MIGRATION_ID,
        CURRENT_MIGRATION_ID,
    )
    prefix_catalog = migration_module.MigrationCatalog(
        migrations=production_catalog.migrations[:2]
    )

    prefix_inspection = migration_module._initialize_database_with_catalog(
        upgrade,
        prefix_catalog,
        current_app_schema=2,
        verify_managed_invariants=True,
    )
    assert prefix_inspection == migration_module.DatabaseInspection(
        classification=migration_module.DatabaseClassification.MANAGED,
        current_sequence=2,
        latest_sequence=2,
        current_migration_id=EXPECTED_MIGRATION_ID,
    )
    with closing(
        sqlite3.connect(upgrade.database_path, isolation_level=None)
    ) as connection, connection:
        _seed_terminal_0002_genesis_family(connection)

    before_database_bytes = upgrade.database_path.read_bytes()
    before_history = tuple(_history_rows(upgrade))
    before_history_bytes = _canonical_snapshot_bytes(before_history)
    with closing(sqlite3.connect(upgrade.database_path)) as connection:
        before_tables = _user_table_names(connection)
        assert not set(SECTION41_TABLE_NAMES) & set(before_tables)
        retained_tables = tuple(
            table for table in before_tables if table != "schema_migrations"
        )
        before_rows = _canonical_table_row_snapshot(connection, retained_tables)
        before_rows_bytes = _canonical_snapshot_bytes(before_rows)
        before_schema = _normalized_complete_schema_manifest(connection)
        seeded_counts = {
            table: connection.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]
            for table in (
                "development_program_heads",
                "development_program_versions",
                "development_accepted_intent_revisions",
                "development_decisions",
            )
        }
        assert seeded_counts == {
            "development_program_heads": 1,
            "development_program_versions": 1,
            "development_accepted_intent_revisions": 1,
            "development_decisions": 1,
        }
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    ordinary = migration_module.inspect_database(upgrade)
    assert ordinary == migration_module.DatabaseInspection(
        classification=migration_module.DatabaseClassification.UNKNOWN,
        current_sequence=0,
        latest_sequence=CURRENT_SEQUENCE,
        current_migration_id=None,
        reason="database_schema_incompatible",
    )
    assert upgrade.database_path.read_bytes() == before_database_bytes
    assert _canonical_snapshot_bytes(tuple(_history_rows(upgrade))) == before_history_bytes
    with closing(sqlite3.connect(upgrade.database_path)) as connection:
        assert _canonical_snapshot_bytes(
            _canonical_table_row_snapshot(connection, retained_tables)
        ) == before_rows_bytes

    applied_migration_ids: list[str] = []
    real_apply = migration_module._apply_migration_definition_in_transaction

    def record_real_apply(
        connection: sqlite3.Connection,
        migration: migration_module.MigrationDefinition,
    ) -> None:
        applied_migration_ids.append(migration.migration_id)
        real_apply(connection, migration)

    monkeypatch.setattr(
        migration_module,
        "_apply_migration_definition_in_transaction",
        record_real_apply,
    )
    migrated = migration_module.migrate_database(upgrade)
    monkeypatch.setattr(
        migration_module,
        "_apply_migration_definition_in_transaction",
        real_apply,
    )

    assert applied_migration_ids == [
        SECTION41_MIGRATION_ID, RW0_C1_MIGRATION_ID, CURRENT_MIGRATION_ID,
    ]
    assert migrated == migration_module.DatabaseInspection(
        classification=migration_module.DatabaseClassification.MANAGED,
        current_sequence=CURRENT_SEQUENCE,
        latest_sequence=CURRENT_SEQUENCE,
        current_migration_id=CURRENT_MIGRATION_ID,
    )
    after_history = tuple(_history_rows(upgrade))
    assert after_history[:2] == before_history
    assert _canonical_snapshot_bytes(after_history[:2]) == before_history_bytes
    assert len(after_history) == 5
    assert after_history[2][:3] == (
        SECTION41_MIGRATION_ID,
        3,
        SECTION41_SHA256,
    )
    assert after_history[2][4:] == (2, 2)
    assert after_history[3][:3] == (
        RW0_C1_MIGRATION_ID,
        4,
        RW0_C1_SHA256,
    )
    assert after_history[3][4:] == (2, 2)
    assert after_history[4][:3] == (CURRENT_MIGRATION_ID, 5, CURRENT_SHA256)
    assert after_history[4][4:] == (2, 2)

    with closing(sqlite3.connect(upgrade.database_path)) as connection:
        after_tables = _user_table_names(connection)
        after_rows = _canonical_table_row_snapshot(connection, retained_tables)
        after_schema = _normalized_complete_schema_manifest(connection)
        new_schema_objects = {
            (object_type, name)
            for object_type, name, _table_name, _sql in after_schema
        } - {
            (object_type, name)
            for object_type, name, _table_name, _sql in before_schema
        }
        assert set(after_tables) - set(before_tables) == set(
            (*SECTION41_TABLE_NAMES, *RW0_C1_TABLE_NAMES,
             *POST_EXECUTION_TABLE_NAMES)
        )
        assert set(before_tables) <= set(after_tables)
        assert new_schema_objects == {
            *(("table", table) for table in SECTION41_TABLE_NAMES),
            *(("trigger", trigger) for trigger in SECTION41_TRIGGER_NAMES),
            *(("table", table) for table in RW0_C1_TABLE_NAMES),
            *(("trigger", trigger) for trigger in RW0_C1_TRIGGER_NAMES),
            *(("index", index) for index in RW0_C1_INDEX_NAMES),
            *(("table", table) for table in POST_EXECUTION_TABLE_NAMES),
            *(("trigger", trigger) for trigger in POST_EXECUTION_TRIGGER_NAMES),
        }
        assert len(new_schema_objects) == 106
        assert _canonical_snapshot_bytes(after_rows) == before_rows_bytes
        assert all(
            connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()
            == (0,)
            for table in (*SECTION41_TABLE_NAMES, *RW0_C1_TABLE_NAMES,
                          *POST_EXECUTION_TABLE_NAMES)
        )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]

    fresh_inspection = migration_module.initialize_database(fresh)
    assert fresh_inspection == migrated
    with closing(sqlite3.connect(fresh.database_path)) as connection:
        fresh_schema = _normalized_complete_schema_manifest(connection)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
    assert after_schema == fresh_schema
    fresh_history = tuple(_history_rows(fresh))
    assert tuple(row[:3] + row[4:] for row in after_history) == tuple(
        row[:3] + row[4:] for row in fresh_history
    )


def test_current_tip_is_newer_unsupported_to_generation_one_catalog(tmp_path: Path) -> None:
    location = _location(tmp_path, "newer")
    migration_module.initialize_database(location)

    assessment = migration_module._assess_location_database(
        location,
        _prefix_one_catalog(),
        current_app_schema=1,
        verify_managed_invariants=True,
    )

    assert assessment.disposition.value == "newer_unsupported"
    assert assessment.reason is not None
    assert assessment.reason.value == "database_schema_too_new"


def test_sqlite_runtime_floor_accepts_exact_floor_and_rejects_one_version_below(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(migration_module.sqlite3, "sqlite_version_info", EXPECTED_SQLITE_MINIMUM)
    migration_module._require_sqlite_strict_runtime()

    monkeypatch.setattr(migration_module.sqlite3, "sqlite_version_info", (3, 36, 99))
    with pytest.raises(SQLiteStateError) as exc_info:
        migration_module._require_sqlite_strict_runtime()
    assert exc_info.value.error_class == "sqlite_posture_unavailable"
    assert str(exc_info.value) == "sqlite_posture_unavailable"
    assert "3.36" not in repr(exc_info.value)


def test_unsupported_runtime_current_to_absent_initialize_drift_stops_before_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path, "unsupported-current-to-absent")
    catalog = migration_module.load_migration_catalog()
    current = _assessment_for_catalog_prefix(
        catalog,
        2,
        migration_module._MigrationDatabaseDisposition.CURRENT,
    )
    absent = _assessment_for_catalog_prefix(
        catalog,
        0,
        migration_module._MigrationDatabaseDisposition.ABSENT,
    )
    history_observations: list[str] = []
    full_observations: list[str] = []
    effects: list[str] = []

    def observe_history(*_args: object, **_kwargs: object):
        history_observations.append("current")
        return current

    def observe_full(*_args: object, **_kwargs: object):
        full_observations.append("absent")
        return absent

    def forbidden(*_args: object, **_kwargs: object):
        effects.append("effect")
        raise AssertionError("unsupported runtime reached an administrative effect")

    monkeypatch.setattr(migration_module.sqlite3, "sqlite_version_info", (3, 36, 99))
    monkeypatch.setattr(migration_module, "_assess_location_database_history_only", observe_history)
    monkeypatch.setattr(migration_module, "_assess_location_database", observe_full)
    monkeypatch.setattr(migration_module, "acquire_state_authority_lock", forbidden)
    monkeypatch.setattr(migration_module, "_open_sqlite_connection", forbidden)
    monkeypatch.setattr(migration_module, "_open_bound_existing_sqlite_connection", forbidden)
    monkeypatch.setattr(migration_module, "_expected_schema_manifest_for_sequence", forbidden)

    with pytest.raises(SQLiteStateError) as exc_info:
        migration_module.initialize_database(location)

    assert exc_info.value.error_class == "sqlite_posture_unavailable"
    assert str(exc_info.value) == "sqlite_posture_unavailable"
    assert "3.36" not in repr(exc_info.value)
    assert history_observations == ["current"]
    assert full_observations == []
    assert effects == []
    assert not location.state_root.exists()
    assert not location.state_authority_lock_path.exists()
    assert not location.database_path.exists()


def test_unsupported_runtime_current_to_0001_migrate_drift_stops_before_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path, "unsupported-current-to-0001")
    catalog = migration_module.load_migration_catalog()
    current = _assessment_for_catalog_prefix(
        catalog,
        2,
        migration_module._MigrationDatabaseDisposition.CURRENT,
    )
    older = _assessment_for_catalog_prefix(
        catalog,
        1,
        migration_module._MigrationDatabaseDisposition.SUPPORTED_OLDER_PREFIX,
    )
    history_observations: list[str] = []
    full_observations: list[str] = []
    effects: list[str] = []

    def observe_history(*_args: object, **_kwargs: object):
        history_observations.append("current")
        return current

    def observe_full(*_args: object, **_kwargs: object):
        full_observations.append("0001")
        return older

    def forbidden(*_args: object, **_kwargs: object):
        effects.append("effect")
        raise AssertionError("unsupported runtime reached an administrative effect")

    monkeypatch.setattr(migration_module.sqlite3, "sqlite_version_info", (3, 36, 99))
    monkeypatch.setattr(migration_module, "_assess_location_database_history_only", observe_history)
    monkeypatch.setattr(migration_module, "_assess_location_database", observe_full)
    monkeypatch.setattr(migration_module, "acquire_state_authority_lock", forbidden)
    monkeypatch.setattr(migration_module, "_open_sqlite_connection", forbidden)
    monkeypatch.setattr(migration_module, "_open_bound_existing_sqlite_connection", forbidden)
    monkeypatch.setattr(migration_module, "_expected_schema_manifest_for_sequence", forbidden)

    with pytest.raises(SQLiteStateError) as exc_info:
        migration_module.migrate_database(location)

    assert exc_info.value.error_class == "sqlite_posture_unavailable"
    assert str(exc_info.value) == "sqlite_posture_unavailable"
    assert "3.36" not in repr(exc_info.value)
    assert history_observations == ["current"]
    assert full_observations == []
    assert effects == []
    assert not location.state_root.exists()
    assert not location.state_authority_lock_path.exists()
    assert not location.database_path.exists()


def test_exact_runtime_floor_supports_stable_fresh_and_exact_upgrade(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fresh = _location(tmp_path, "floor-fresh")
    upgrade = _location(tmp_path, "floor-upgrade")
    monkeypatch.setattr(migration_module.sqlite3, "sqlite_version_info", EXPECTED_SQLITE_MINIMUM)

    initialized = migration_module.initialize_database(fresh)
    _initialize_prefix_one(upgrade)
    migrated = migration_module.migrate_database(upgrade)

    assert initialized.classification is migration_module.DatabaseClassification.MANAGED
    assert migrated.classification is migration_module.DatabaseClassification.MANAGED
    assert initialized.current_sequence == migrated.current_sequence == CURRENT_SEQUENCE


def test_unsupported_runtime_refuses_fresh_initialization_before_any_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path, "unsupported-fresh")
    calls: list[str] = []

    def forbidden(*_args, **_kwargs):
        calls.append("effect")
        raise AssertionError("unsupported runtime reached an effect")

    monkeypatch.setattr(migration_module.sqlite3, "sqlite_version_info", (3, 36, 99))
    monkeypatch.setattr(migration_module, "acquire_state_authority_lock", forbidden)
    monkeypatch.setattr(migration_module, "_open_sqlite_connection", forbidden)
    monkeypatch.setattr(migration_module, "_open_bound_existing_sqlite_connection", forbidden)
    monkeypatch.setattr(migration_module, "_expected_schema_manifest_for_sequence", forbidden)

    with pytest.raises(SQLiteStateError) as exc_info:
        migration_module.initialize_database(location)

    assert exc_info.value.error_class == "sqlite_posture_unavailable"
    assert str(exc_info.value) == "sqlite_posture_unavailable"
    assert calls == []
    assert not location.state_root.exists()
    assert not location.state_authority_lock_path.exists()
    assert not location.database_path.exists()


def test_unsupported_runtime_refuses_exact_upgrade_before_lock_or_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path, "unsupported-upgrade")
    _initialize_prefix_one(location)
    before_database = location.database_path.read_bytes()
    before_history = _history_rows(location)
    calls: list[str] = []

    def forbidden(*_args, **_kwargs):
        calls.append("effect")
        raise AssertionError("unsupported runtime reached an effect")

    monkeypatch.setattr(migration_module.sqlite3, "sqlite_version_info", (3, 36, 99))
    monkeypatch.setattr(migration_module, "acquire_state_authority_lock", forbidden)
    monkeypatch.setattr(migration_module, "_open_bound_existing_sqlite_connection", forbidden)
    monkeypatch.setattr(migration_module, "_expected_schema_manifest_for_sequence", forbidden)

    with pytest.raises(SQLiteStateError) as exc_info:
        migration_module.migrate_database(location)

    assert exc_info.value.error_class == "sqlite_posture_unavailable"
    assert str(exc_info.value) == "sqlite_posture_unavailable"
    assert calls == []
    assert location.database_path.read_bytes() == before_database
    assert _history_rows(location) == before_history


def test_unsupported_runtime_can_still_classify_exact_0001_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path, "unsupported-prefix")
    _initialize_prefix_one(location)
    before = location.database_path.read_bytes()
    monkeypatch.setattr(migration_module.sqlite3, "sqlite_version_info", (3, 36, 99))

    inspection = migration_module.inspect_database(location)

    assert inspection.classification is migration_module.DatabaseClassification.UNKNOWN
    assert inspection.reason == "database_schema_incompatible"
    assert location.database_path.read_bytes() == before


def test_installed_current_tip_validation_on_unsupported_runtime_fails_safely(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path, "unsupported-current")
    migration_module.initialize_database(location)
    before = location.database_path.read_bytes()
    monkeypatch.setattr(migration_module.sqlite3, "sqlite_version_info", (3, 36, 99))

    inspection = migration_module.validate_database(location)

    assert inspection.classification is migration_module.DatabaseClassification.UNKNOWN
    assert inspection.reason == "sqlite_posture_unavailable"
    assert location.database_path.read_bytes() == before
    assert "3.36" not in repr(inspection)


def test_zero_seed_checks_are_sequence_scoped_and_not_an_ordinary_managed_invariant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fresh = _location(tmp_path, "zero-fresh")
    upgraded = _location(tmp_path, "zero-upgrade")
    original_bootstrap = migration_module._verify_empty_bootstrap_tables
    original_c2b2 = migration_module._verify_empty_c2b2_migration_tables
    bootstrap_calls: list[int] = []
    c2b2_calls: list[int] = []

    def count_bootstrap(connection: sqlite3.Connection) -> None:
        bootstrap_calls.append(1)
        original_bootstrap(connection)

    def count_c2b2(connection: sqlite3.Connection) -> None:
        c2b2_calls.append(1)
        original_c2b2(connection)

    monkeypatch.setattr(migration_module, "_verify_empty_bootstrap_tables", count_bootstrap)
    monkeypatch.setattr(migration_module, "_verify_empty_c2b2_migration_tables", count_c2b2)
    migration_module.initialize_database(fresh)
    _initialize_prefix_one(upgraded)
    assert bootstrap_calls == [1, 1]
    migration_module.migrate_database(upgraded)
    assert bootstrap_calls == [1, 1]
    assert c2b2_calls == [1, 1]

    def forbidden_c2b2_check(_connection: sqlite3.Connection) -> None:
        raise AssertionError("ordinary inspection called migration-completion emptiness")

    monkeypatch.setattr(
        migration_module,
        "_verify_empty_c2b2_migration_tables",
        forbidden_c2b2_check,
    )
    assert migration_module.inspect_database(fresh).classification is migration_module.DatabaseClassification.MANAGED
    assert migration_module.inspect_database(upgraded).classification is migration_module.DatabaseClassification.MANAGED


def test_unexpected_c2b2_seed_during_migration_rolls_back_safely(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path, "seed-negative")
    original_apply = migration_module._apply_migration_definition_in_transaction

    def apply_with_seed(connection: sqlite3.Connection, migration) -> None:
        original_apply(connection, migration)
        if migration.migration_id == EXPECTED_MIGRATION_ID:
            connection.execute(
                """
                INSERT INTO development_program_heads
                    (schema_id, program_ref, current_program_version_ref,
                     current_program_version_number, head_revision, program_state,
                     updated_at, head_digest)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "governed-execution.nwp-development-program-head.v1",
                    "program-1",
                    "version-1",
                    1,
                    0,
                    "active",
                    "2026-08-14T00:00:00Z",
                    "0" * 64,
                ),
            )

    monkeypatch.setattr(
        migration_module,
        "_apply_migration_definition_in_transaction",
        apply_with_seed,
    )

    with pytest.raises(SQLiteStateError) as exc_info:
        migration_module.initialize_database(location)

    assert exc_info.value.error_class == "schema_verification_failed"
    assert "program-1" not in repr(exc_info.value)
    with closing(sqlite3.connect(location.database_path)) as connection, connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%'"
        ).fetchone() == (0,)


@pytest.mark.parametrize(
    "replacement",
    [
        (
            "schema_id ANY NOT NULL CHECK",
            "schema_id TEXT NOT NULL CHECK",
        ),
        (
            "schema_id ANY NOT NULL CHECK",
            "schema_id ANY CHECK",
        ),
        (
            "program_state IN ('active','accepted','terminal_rejected','blocked')",
            "program_state IN ('active','accepted','terminal_rejected')",
        ),
        (
            "REFERENCES development_program_versions (program_ref, program_version_ref)",
            "REFERENCES development_program_versions (program_ref, program_version_number)",
        ),
        (
            "append_only_development_program_versions",
            "append_only_development_program_versions_changed",
        ),
        (
            "WHERE effect_class = 'author_candidate';",
            "WHERE effect_class = 'validate_candidate';",
        ),
    ],
)
def test_wrong_column_check_fk_trigger_or_index_fails_exact_schema_verification(
    tmp_path: Path,
    replacement: tuple[str, str],
) -> None:
    location = _location(tmp_path, hashlib.sha256(repr(replacement).encode()).hexdigest()[:12])
    old, new = replacement
    candidate = _expected_sql_text()
    assert candidate.count(old) >= 1
    candidate = candidate.replace(old, new, 1)
    _create_database_from_literal_sql(
        location,
        migration_0002_sql=candidate,
        history_sequences=(1, 2),
    )

    _assert_safe_unknown(location)


@pytest.mark.parametrize(
    ("migration_0002_sql", "history_sequences"),
    [
        (None, (1, 2)),
        (_expected_sql_text(), (1,)),
        (_render_expected_statements()[0] + "\n", (1,)),
    ],
)
def test_history_only_schema_only_and_partial_0002_fail_closed(
    tmp_path: Path,
    migration_0002_sql: str | None,
    history_sequences: tuple[int, ...],
) -> None:
    name = hashlib.sha256(repr((migration_0002_sql is None, history_sequences, len(migration_0002_sql or ''))).encode()).hexdigest()[:12]
    location = _location(tmp_path, name)
    _create_database_from_literal_sql(
        location,
        migration_0002_sql=migration_0002_sql,
        history_sequences=history_sequences,
    )

    _assert_safe_unknown(location)


@pytest.mark.parametrize("object_sql", ["CREATE TABLE unexpected_extra (value INTEGER)", "CREATE VIEW unexpected_view AS SELECT 1 AS value"])
def test_extra_object_or_view_fails_closed(tmp_path: Path, object_sql: str) -> None:
    location = _location(tmp_path, hashlib.sha256(object_sql.encode()).hexdigest()[:12])
    migration_module.initialize_database(location)
    with closing(sqlite3.connect(location.database_path)) as connection, connection:
        connection.execute(object_sql)
        connection.commit()

    _assert_safe_unknown(location)


def test_wrong_0002_history_metadata_fails_closed(tmp_path: Path) -> None:
    location = _location(tmp_path, "history-metadata")
    _create_database_from_literal_sql(
        location,
        migration_0002_sql=_expected_sql_text(),
        history_sequences=(1, 2),
        history_0002_checksum="f" * 64,
    )

    _assert_safe_unknown(location)
