from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import types
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = ROOT / ".docs/c2b-durable-development-state.md"
BEGIN_MARKER = "<!-- C2B2_FIELD_LEVEL_CONTRACT_JSON_BEGIN -->"
END_MARKER = "<!-- C2B2_FIELD_LEVEL_CONTRACT_JSON_END -->"
OWNER_LEDGER_TEST_NAME = "test_c2b2_owner_ledger_matches_the_independent_literal_oracle"
EXPECTED_SLICE2_PRODUCTION_MODULES = (
    "_development_decision_row_values.py",
    "_development_effect_row_values.py",
    "_development_program_row_values.py",
    "_development_row_value_support.py",
)

EXPECTED_ORACLE_IMPORTS = (
    ("__future__", "from-import", "annotations", None),
    ("ast", "import", None, None),
    ("copy", "from-import", "deepcopy", None),
    ("dataclasses", "from-import", "dataclass", None),
    ("hashlib", "import", None, None),
    ("json", "import", None, None),
    ("pathlib", "from-import", "Path", None),
    ("types", "import", None, None),
    ("typing", "from-import", "Any", None),
    ("pytest", "import", None, None),
)

EXPECTED_ORACLE_FILESYSTEM_READS = (
    (
        "_owner_contract",
        "OWNER_PATH",
        "read_text",
        "text",
        "utf-8",
        "sole candidate semantic input",
    ),
    (
        "_oracle_source",
        "Path(__file__)",
        "read_text",
        "text",
        "utf-8",
        "architecture self-check source",
    ),
)

EXPECTED_HASH_CALL_SITES = (
    (
        "_graph_digest_from_identity",
        "hashlib.sha256",
        1,
        "domain-separated mutation-graph semantic identity",
    ),
    (
        "test_c2b2_common_graph_digest_primitive_is_closed_and_order_sensitive",
        "hashlib.sha256",
        1,
        "independent semantic graph-digest formula check",
    ),
)

EXPECTED_CONTRACT = {
  "c2a_persistence": {
    "cross_row_invariants": [
      {
        "aggregate_reader_enforcement": "The completed aggregate validates the exact parent first, consumes every internal page in one capability object and epoch, proves start=0, unit increments, no overlap or duplicate ordinal/pair, requires each work_item_ref to appear at most once regardless of membership_ordinal or work_item_revision_ref, binds each exact work-item revision, and rejects empty membership for every currently defined program-version kind.",
        "authority_effect": "Integrity validation only; no execution or external authority is created.",
        "exact_pass_condition": "An absent exact parent returns None; for every present program/version aggregate with n members, n>=1, sorted (membership_ordinal, work_item_ref) rows have ordinals exactly 0..n-1, and every work_item_ref is unique across the complete aggregate.",
        "future_mutation_preflight_enforcement": "Initialization and replan write plans precompute dense ordinals and reject duplicates or gaps before write.",
        "input_tables_and_fields": [
          "development_program_version_work_items.program_ref",
          "development_program_version_work_items.program_version_ref",
          "development_program_version_work_items.membership_ordinal",
          "development_program_version_work_items.work_item_ref"
        ],
        "invariant_id": "membership_ordinals_contiguous",
        "owning_tranche": "C2B2 reader contract; C2B3 initialization and C2B6 replan mutation preflight.",
        "privacy_effect": "Only safe refs, ordinals, and digests participate.",
        "private_adapter_enforcement": "Each row adapter validates exact scalar types and row digest.",
        "safe_failure": "database_integrity_failure for a malformed parent or persisted empty, gapped, overlapping, duplicate-ordinal, duplicate-pair, duplicate-work-item-ref, or mismatched membership/revision aggregate; mutation_failed before exceeding the operational maximum_members ceiling.",
        "sql_enforced_portion": "UNIQUE(program_ref, program_version_ref, membership_ordinal) rejects duplicate ordinals; SQL does not prove gaps or completeness."
      },
      {
        "aggregate_reader_enforcement": "Program/version/decision aggregates prove basis identity, exact arithmetic, and current-head correspondence.",
        "authority_effect": "Durable progression integrity only; not external standing authority.",
        "exact_pass_condition": "Genesis is version 1 with null basis; each version-advancing non-genesis decision binds the authoritative basis and resulting_program_version_number=basis_program_version_number+1; non-version-advancing decisions have no resulting version fields.",
        "future_mutation_preflight_enforcement": "Current head is read inside the transaction; preflight computes exactly the next version and CAS basis.",
        "input_tables_and_fields": [
          "development_program_heads.current_program_version_ref",
          "development_program_heads.current_program_version_number",
          "development_program_versions.program_version_number",
          "development_decisions.basis_program_version_ref",
          "development_decisions.basis_program_version_number",
          "development_decisions.resulting_program_version_ref",
          "development_decisions.resulting_program_version_number"
        ],
        "invariant_id": "version_number_advancement",
        "owning_tranche": "C2B2 reader contract; C2B3 genesis and C2B6 progression mutation preflight.",
        "privacy_effect": "No private payload participates.",
        "private_adapter_enforcement": "Adapters validate positive integers and ref/number group completeness.",
        "safe_failure": "program_head_conflict for stale caller expectation; database_integrity_failure for an impossible persisted graph.",
        "sql_enforced_portion": "Positive integer predicates, unique program/version number, and the closed decision nullability algebra; arithmetic across rows is not SQL-enforced."
      },
      {
        "aggregate_reader_enforcement": "Aggregate readers verify current record/head identity and reject incoherent revision evidence.",
        "authority_effect": "Conflict fencing only; no authorization issuance.",
        "exact_pass_condition": "Each mutable-head update compares the caller-bound expected revision and advances the stored head revision by exactly one; genesis program/work heads begin at revision 0.",
        "future_mutation_preflight_enforcement": "One CAS predicate and rowcount=1 are required for every mutable-head update.",
        "input_tables_and_fields": [
          "development_program_heads.head_revision",
          "development_work_item_heads.head_revision",
          "development_effect_heads.head_revision",
          "development_delivery_heads.head_revision",
          "development_decisions.expected_program_head_revision",
          "development_decisions.expected_target_effect_head_revision"
        ],
        "invariant_id": "head_revision_advancement",
        "owning_tranche": "C2B3/C2B5/C2B6 mutation runtime with C2B2 private-reader prerequisites.",
        "privacy_effect": "Counters only.",
        "private_adapter_enforcement": "Adapters require exact built-in nonnegative integers.",
        "safe_failure": "program_head_conflict or target_effect_state_conflict for stale expectations; database_integrity_failure for malformed persisted state.",
        "sql_enforced_portion": "Nonnegative integer checks only; exact CAS arithmetic belongs to the transaction mutation."
      },
      {
        "aggregate_reader_enforcement": "Reject any ref/digest mismatch before returning an aggregate or replay.",
        "authority_effect": "A valid digest proves identity only, never execution permission.",
        "exact_pass_condition": "Every digest paired with a reference equals the recomputed digest of the exact referenced canonical record; paired fields are both absent or both present where nullable.",
        "future_mutation_preflight_enforcement": "Write plans derive digests from canonical records and never accept caller-computed durable digests as authority.",
        "input_tables_and_fields": [
          "all persisted ref/digest pairs",
          "decision selected/target/originating ref-digest fields",
          "receipt graph record_ref/record_digest entries"
        ],
        "invariant_id": "ref_digest_equality",
        "owning_tranche": "C2B2 adapters/readers; later C2B mutation tranches.",
        "privacy_effect": "Digest validation does not reveal source bytes or secrets.",
        "private_adapter_enforcement": "Recompute every row, C2A, projection, nested-envelope, decision, and graph digest.",
        "safe_failure": "database_integrity_failure for persisted mismatch; domain rejection before write for incoherent proposed records.",
        "sql_enforced_portion": "Scalar digest predicates, nullable group CHECKs, and FKs for local refs; digest equality is not SQL-enforced."
      },
      {
        "aggregate_reader_enforcement": "Read the exact cancellation decision, cancellation intent/fence, target intent/fence, and capsule binding; prove the class-conditioned null/equality algebra before returning.",
        "authority_effect": "Binding evidence only; no effect authorization is minted.",
        "exact_pass_condition": "For cancel_effect targeting author_candidate, the cancellation effect intent portable_capsule_digest, cancellation effect fence portable_capsule_digest, decision target_capsule_manifest_ref, and decision target_portable_capsule_digest are all null. For cancel_effect targeting validate_candidate or review_candidate, the intent digest is non-null and equals both the target/cancellation fence portable digest and decision.target_portable_capsule_digest; the cancellation effect fence carries that same digest and its target-fence ref/digest identifies the exact target.",
        "future_mutation_preflight_enforcement": "Cancellation preflight rejects a missing, extra, stale, or mismatched capsule binding before any write.",
        "input_tables_and_fields": [
          "development_decisions.target_effect_class",
          "development_decisions.target_capsule_manifest_ref",
          "development_decisions.target_portable_capsule_digest",
          "development_decisions.target_effect_fence_ref",
          "development_effect_intents.effect_class",
          "development_effect_intents.cancellation_target_effect_intent_ref",
          "development_effect_intents.portable_capsule_digest",
          "development_effect_fences.effect_intent_ref",
          "development_effect_fences.portable_capsule_digest",
          "development_effect_fences.cancellation_target_effect_fence_ref",
          "development_effect_fences.cancellation_target_effect_fence_digest"
        ],
        "invariant_id": "cancellation_capsule_target_binding",
        "negative_cases": [
          "extra capsule on author target",
          "missing capsule on validation target",
          "missing capsule on review target",
          "sibling capsule digest",
          "arbitrary unrelated digest",
          "decision/intent/fence disagreement"
        ],
        "owning_tranche": "C2B2 reader contract; C2B5 cancellation mutation.",
        "privacy_effect": "Only safe capsule refs and portable digests persist; capsule bytes never persist in 0002.",
        "private_adapter_enforcement": "Reconstruct C2A values and invoke cancellation/effect coherence validation.",
        "safe_failure": "domain rejection before write; database_integrity_failure if persisted evidence is incoherent.",
        "sql_enforced_portion": "Closed decision and effect-fence nullable-group CHECKs; cross-row equality is not SQL-enforced."
      },
      {
        "aggregate_reader_enforcement": "Attempt/fence aggregates repeat reconstruction before return.",
        "authority_effect": "Effect ceiling representation only; the mask is not permission.",
        "exact_pass_condition": "The integer mask is 1..31, has no unknown bits, and reconstructs exactly the canonical C2A ordered unique effect-class list using bit order author_candidate,cancel_effect,local_git_commit,review_candidate,validate_candidate.",
        "future_mutation_preflight_enforcement": "Encode only a validated nonempty C2A closed list; reject duplicates, unknown classes, or noncanonical ordering.",
        "input_tables_and_fields": [
          "development_attempt_fences.allowed_effect_class_mask"
        ],
        "invariant_id": "c2a_effect_class_mask_reconstruction",
        "owning_tranche": "C2B2 C2A adapter/reader contract; C2B3 author establishment.",
        "privacy_effect": "Closed class bits only.",
        "private_adapter_enforcement": "Decode bits to the exact canonical list, reconstruct AttemptFenceV1, and verify its digest/coherence.",
        "safe_failure": "database_integrity_failure for malformed persisted mask; domain rejection before write for invalid proposal.",
        "sql_enforced_portion": "Exact integer storage and BETWEEN 1 AND 31."
      },
      {
        "aggregate_reader_enforcement": "Transaction aggregate reads and compares the authoritative singleton before returning a mutation context.",
        "authority_effect": "Preserves external stop authority; Coordinator cannot reinterpret or mint it.",
        "exact_pass_condition": "Every mutation binds the exact authoritative schema-0001 coding global-stop ref/version observed inside the same transaction; productive operations fail when stop is active and risk-reducing cancellation remains governed by its exact later contract.",
        "future_mutation_preflight_enforcement": "Fresh path binds the observed pair and applies the stop policy before write.",
        "input_tables_and_fields": [
          "development_decisions.coding_global_stop_ref",
          "development_decisions.coding_global_stop_version",
          "development_attempt_fences.global_stop_ref",
          "development_attempt_fences.global_stop_version",
          "development_effect_fences.global_stop_ref",
          "development_effect_fences.global_stop_version",
          "development_author_commands.global_stop_ref",
          "development_author_commands.global_stop_version",
          "schema-0001 global_stop_current"
        ],
        "invariant_id": "global_stop_binding",
        "owning_tranche": "C2B3/C2B5/C2B6 mutation transactions using existing schema-0001 global-stop authority.",
        "privacy_effect": "Safe ref and version only.",
        "private_adapter_enforcement": "Adapters validate ref/version shape without treating it as caller authority.",
        "safe_failure": "coding_global_stop_active or apply conflict for current state; database_integrity_failure for persisted mismatch.",
        "sql_enforced_portion": "Scalar/ref-version checks only; migration 0002 intentionally has no FK to the schema-0001 singleton."
      },
      {
        "aggregate_reader_enforcement": "After 0003 the observation resolver must prove exact-one complete result graph before replay.",
        "authority_effect": "Observation existence is knowledge evidence, not execution authorization.",
        "exact_pass_condition": "An observation-ingest receipt has exactly one result_observation_ref resolving to the complete migration-0003 observation graph; all other receipt families have it null.",
        "future_mutation_preflight_enforcement": "C2B5 observation ingest writes the result and receipt atomically under the shared transaction.",
        "input_tables_and_fields": [
          "development_mutation_receipts.result_observation_ref",
          "migration-0003 observation tables"
        ],
        "invariant_id": "observation_result_existence_after_0003",
        "owning_tranche": "C2B4 migration-0003 resolver contract and C2B5 observation ingest.",
        "privacy_effect": "The 0002 receipt contains only a safe observation ref and digests; source bytes remain excluded.",
        "private_adapter_enforcement": "The 0002 receipt adapter preserves the safe ref but does not claim existence before 0003.",
        "safe_failure": "database_integrity_failure for missing, duplicate, or incomplete persisted observation result.",
        "sql_enforced_portion": "The migration-0002 closed receipt union controls nullability; no 0002 FK targets future tables."
      }
    ],
    "delivery_wrapper_digest_contract": {
      "c2b_delivery_attempt_wrapper": {
        "basis_decision_treatment": "basis_decision_ref is required and participates in wrapper identity.",
        "database_column_for_literal_schema_id": None,
        "delivery_lineage_fields": [
          "delivery_kind",
          "delivery_number",
          "predecessor_delivery_attempt_ref"
        ],
        "digest_domain": "governed-execution.nwp-development-delivery-attempt.v1.identity",
        "identity_value_sources": {
          "basis_decision_ref": "persisted",
          "delivery_envelope_digest": "recomputed nested C2A digest",
          "delivery_kind": "persisted",
          "delivery_number": "persisted",
          "predecessor_delivery_attempt_ref": "persisted nullable lineage",
          "recorded_at": "persisted whole-second UTC",
          "schema_id": "literal governed-execution.nwp-development-delivery-attempt.v1"
        },
        "literal_schema_canonical_key": "schema_id",
        "literal_schema_derivation": "The adapter supplies the fixed wrapper schema literal; it is not caller input and adding a twentieth SQL column is neither necessary nor authorized.",
        "literal_wrapper_schema_id": "governed-execution.nwp-development-delivery-attempt.v1",
        "nested_delivery_envelope_digest_treatment": "Included as one exact digest identity input; nested envelope fields are not duplicated into the wrapper identity.",
        "operational_fields_excluded": [],
        "ordered_identity_keys": [
          "schema_id",
          "delivery_envelope_digest",
          "delivery_kind",
          "delivery_number",
          "predecessor_delivery_attempt_ref",
          "basis_decision_ref",
          "recorded_at"
        ],
        "recorded_at_participation": True,
        "self_digest_exclusion": "delivery_attempt_digest"
      },
      "counterfactuals": [
        "nested_delivery_envelope_substitution changes or invalidates delivery_envelope_digest",
        "wrapper_schema_substitution changes or invalidates delivery_attempt_digest"
      ],
      "nested_delivery_envelope": {
        "digest_domain": "governed-execution.nwp-delivery-envelope.v1.identity",
        "ordered_identity_keys": [
          "schema_id",
          "delivery_attempt_ref",
          "program_ref",
          "program_version_ref",
          "command_ref",
          "command_digest",
          "semantic_attempt_ref",
          "effect_intent_ref",
          "attempt_fence_ref",
          "attempt_fence_digest",
          "effect_fence_ref",
          "effect_fence_digest",
          "adapter_kind",
          "adapter_safe_correlation_ref"
        ],
        "schema_id": "governed-execution.nwp-delivery-envelope.v1",
        "self_digest_exclusion": "delivery_envelope_digest"
      }
    },
    "field_mapping_ledger": [
      {
        "c2a_field": "schema_id",
        "input_b_durable_column": "schema_id",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[schema_id]",
        "repaired_sql_column": "schema_id",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "attempt_fence_ref",
        "input_b_durable_column": "attempt_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[attempt_fence_ref]",
        "repaired_sql_column": "attempt_fence_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "parent_standing_grant_ref",
        "input_b_durable_column": "parent_standing_grant_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[parent_standing_grant_ref]",
        "repaired_sql_column": "parent_standing_grant_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "parent_standing_grant_digest",
        "input_b_durable_column": "parent_standing_grant_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[parent_standing_grant_digest]",
        "repaired_sql_column": "parent_standing_grant_digest",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "attempt_authorization_ref",
        "input_b_durable_column": "attempt_authorization_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[attempt_authorization_ref]",
        "repaired_sql_column": "attempt_authorization_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "attempt_authorization_digest",
        "input_b_durable_column": "attempt_authorization_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[attempt_authorization_digest]",
        "repaired_sql_column": "attempt_authorization_digest",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "program_ref",
        "input_b_durable_column": "program_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[program_ref]",
        "repaired_sql_column": "program_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "program_version_ref",
        "input_b_durable_column": "program_version_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[program_version_ref]",
        "repaired_sql_column": "program_version_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "accepted_intent_revision_ref",
        "input_b_durable_column": "accepted_intent_revision_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[accepted_intent_revision_ref]",
        "repaired_sql_column": "accepted_intent_revision_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "work_item_ref",
        "input_b_durable_column": "work_item_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[work_item_ref]",
        "repaired_sql_column": "work_item_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "work_item_revision_ref",
        "input_b_durable_column": "work_item_revision_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[work_item_revision_ref]",
        "repaired_sql_column": "work_item_revision_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "semantic_attempt_ref",
        "input_b_durable_column": "semantic_attempt_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[semantic_attempt_ref]",
        "repaired_sql_column": "semantic_attempt_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "repository_ref",
        "input_b_durable_column": "repository_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[repository_ref]",
        "repaired_sql_column": "repository_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "base_git_object_format",
        "input_b_durable_column": "base_git_object_format",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[base_git_object_format]",
        "repaired_sql_column": "base_git_object_format",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "base_git_oid",
        "input_b_durable_column": "base_git_oid",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[base_git_oid]",
        "repaired_sql_column": "base_git_oid",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "path_ceiling",
        "input_b_durable_column": "path_ceiling_json",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[path_ceiling_json]",
        "repaired_sql_column": "path_ceiling_json",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "allowed_effect_classes",
        "input_b_durable_column": "allowed_effect_class_mask",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[allowed_effect_class_mask]",
        "repaired_sql_column": "allowed_effect_class_mask",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_active_invocations",
        "input_b_durable_column": "aggregate_max_active_invocations",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_active_invocations]",
        "repaired_sql_column": "aggregate_max_active_invocations",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_candidate_bytes",
        "input_b_durable_column": "aggregate_max_candidate_bytes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_candidate_bytes]",
        "repaired_sql_column": "aggregate_max_candidate_bytes",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_changed_files",
        "input_b_durable_column": "aggregate_max_changed_files",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_changed_files]",
        "repaired_sql_column": "aggregate_max_changed_files",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_cost_microusd",
        "input_b_durable_column": "aggregate_max_cost_microusd",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_cost_microusd]",
        "repaired_sql_column": "aggregate_max_cost_microusd",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_cpu_seconds",
        "input_b_durable_column": "aggregate_max_cpu_seconds",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_cpu_seconds]",
        "repaired_sql_column": "aggregate_max_cpu_seconds",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_deliveries",
        "input_b_durable_column": "aggregate_max_deliveries",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_deliveries]",
        "repaired_sql_column": "aggregate_max_deliveries",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_deployments",
        "input_b_durable_column": "aggregate_max_deployments",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_deployments]",
        "repaired_sql_column": "aggregate_max_deployments",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_local_commits",
        "input_b_durable_column": "aggregate_max_local_commits",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_local_commits]",
        "repaired_sql_column": "aggregate_max_local_commits",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_memory_bytes",
        "input_b_durable_column": "aggregate_max_memory_bytes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_memory_bytes]",
        "repaired_sql_column": "aggregate_max_memory_bytes",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_merges",
        "input_b_durable_column": "aggregate_max_merges",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_merges]",
        "repaired_sql_column": "aggregate_max_merges",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_model_input_tokens",
        "input_b_durable_column": "aggregate_max_model_input_tokens",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_model_input_tokens]",
        "repaired_sql_column": "aggregate_max_model_input_tokens",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_model_output_tokens",
        "input_b_durable_column": "aggregate_max_model_output_tokens",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_model_output_tokens]",
        "repaired_sql_column": "aggregate_max_model_output_tokens",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_pull_requests",
        "input_b_durable_column": "aggregate_max_pull_requests",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_pull_requests]",
        "repaired_sql_column": "aggregate_max_pull_requests",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_pushes",
        "input_b_durable_column": "aggregate_max_pushes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_pushes]",
        "repaired_sql_column": "aggregate_max_pushes",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "aggregate_ceilings.max_wall_seconds",
        "input_b_durable_column": "aggregate_max_wall_seconds",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[aggregate_max_wall_seconds]",
        "repaired_sql_column": "aggregate_max_wall_seconds",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "expires_at",
        "input_b_durable_column": "expires_at",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[expires_at]",
        "repaired_sql_column": "expires_at",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "global_stop_ref",
        "input_b_durable_column": "global_stop_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[global_stop_ref]",
        "repaired_sql_column": "global_stop_ref",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "global_stop_version",
        "input_b_durable_column": "global_stop_version",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[global_stop_version]",
        "repaired_sql_column": "global_stop_version",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "attempt_fence_digest",
        "input_b_durable_column": "attempt_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_attempt_fences].columns[attempt_fence_digest]",
        "repaired_sql_column": "attempt_fence_digest",
        "table": "development_attempt_fences",
        "value_type": "AttemptFenceV1"
      },
      {
        "c2a_field": "schema_id",
        "input_b_durable_column": "schema_id",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[schema_id]",
        "repaired_sql_column": "schema_id",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_fence_ref",
        "input_b_durable_column": "effect_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_fence_ref]",
        "repaired_sql_column": "effect_fence_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "parent_standing_grant_ref",
        "input_b_durable_column": "parent_standing_grant_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[parent_standing_grant_ref]",
        "repaired_sql_column": "parent_standing_grant_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "parent_standing_grant_digest",
        "input_b_durable_column": "parent_standing_grant_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[parent_standing_grant_digest]",
        "repaired_sql_column": "parent_standing_grant_digest",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_authorization_ref",
        "input_b_durable_column": "effect_authorization_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_authorization_ref]",
        "repaired_sql_column": "effect_authorization_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_authorization_digest",
        "input_b_durable_column": "effect_authorization_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_authorization_digest]",
        "repaired_sql_column": "effect_authorization_digest",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "attempt_fence_ref",
        "input_b_durable_column": "attempt_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[attempt_fence_ref]",
        "repaired_sql_column": "attempt_fence_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "attempt_fence_digest",
        "input_b_durable_column": "attempt_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[attempt_fence_digest]",
        "repaired_sql_column": "attempt_fence_digest",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "program_ref",
        "input_b_durable_column": "program_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[program_ref]",
        "repaired_sql_column": "program_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "program_version_ref",
        "input_b_durable_column": "program_version_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[program_version_ref]",
        "repaired_sql_column": "program_version_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "accepted_intent_revision_ref",
        "input_b_durable_column": "accepted_intent_revision_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[accepted_intent_revision_ref]",
        "repaired_sql_column": "accepted_intent_revision_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "work_item_ref",
        "input_b_durable_column": "work_item_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[work_item_ref]",
        "repaired_sql_column": "work_item_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "work_item_revision_ref",
        "input_b_durable_column": "work_item_revision_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[work_item_revision_ref]",
        "repaired_sql_column": "work_item_revision_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "semantic_attempt_ref",
        "input_b_durable_column": "semantic_attempt_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[semantic_attempt_ref]",
        "repaired_sql_column": "semantic_attempt_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_intent_ref",
        "input_b_durable_column": "effect_intent_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_intent_ref]",
        "repaired_sql_column": "effect_intent_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_class",
        "input_b_durable_column": "effect_class",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_class]",
        "repaired_sql_column": "effect_class",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "command_ref",
        "input_b_durable_column": "command_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[command_ref]",
        "repaired_sql_column": "command_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "command_digest",
        "input_b_durable_column": "command_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[command_digest]",
        "repaired_sql_column": "command_digest",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "candidate_ref",
        "input_b_durable_column": "candidate_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[candidate_ref]",
        "repaired_sql_column": "candidate_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "repository_ref",
        "input_b_durable_column": "repository_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[repository_ref]",
        "repaired_sql_column": "repository_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "base_git_object_format",
        "input_b_durable_column": "base_git_object_format",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[base_git_object_format]",
        "repaired_sql_column": "base_git_object_format",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "base_git_oid",
        "input_b_durable_column": "base_git_oid",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[base_git_oid]",
        "repaired_sql_column": "base_git_oid",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "path_ceiling",
        "input_b_durable_column": "path_ceiling_json",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[path_ceiling_json]",
        "repaired_sql_column": "path_ceiling_json",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_active_invocations",
        "input_b_durable_column": "effect_max_active_invocations",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_active_invocations]",
        "repaired_sql_column": "effect_max_active_invocations",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_candidate_bytes",
        "input_b_durable_column": "effect_max_candidate_bytes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_candidate_bytes]",
        "repaired_sql_column": "effect_max_candidate_bytes",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_changed_files",
        "input_b_durable_column": "effect_max_changed_files",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_changed_files]",
        "repaired_sql_column": "effect_max_changed_files",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_cost_microusd",
        "input_b_durable_column": "effect_max_cost_microusd",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_cost_microusd]",
        "repaired_sql_column": "effect_max_cost_microusd",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_cpu_seconds",
        "input_b_durable_column": "effect_max_cpu_seconds",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_cpu_seconds]",
        "repaired_sql_column": "effect_max_cpu_seconds",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_deliveries",
        "input_b_durable_column": "effect_max_deliveries",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_deliveries]",
        "repaired_sql_column": "effect_max_deliveries",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_deployments",
        "input_b_durable_column": "effect_max_deployments",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_deployments]",
        "repaired_sql_column": "effect_max_deployments",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_local_commits",
        "input_b_durable_column": "effect_max_local_commits",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_local_commits]",
        "repaired_sql_column": "effect_max_local_commits",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_memory_bytes",
        "input_b_durable_column": "effect_max_memory_bytes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_memory_bytes]",
        "repaired_sql_column": "effect_max_memory_bytes",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_merges",
        "input_b_durable_column": "effect_max_merges",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_merges]",
        "repaired_sql_column": "effect_max_merges",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_model_input_tokens",
        "input_b_durable_column": "effect_max_model_input_tokens",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_model_input_tokens]",
        "repaired_sql_column": "effect_max_model_input_tokens",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_model_output_tokens",
        "input_b_durable_column": "effect_max_model_output_tokens",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_model_output_tokens]",
        "repaired_sql_column": "effect_max_model_output_tokens",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_pull_requests",
        "input_b_durable_column": "effect_max_pull_requests",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_pull_requests]",
        "repaired_sql_column": "effect_max_pull_requests",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_pushes",
        "input_b_durable_column": "effect_max_pushes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_pushes]",
        "repaired_sql_column": "effect_max_pushes",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_ceilings.max_wall_seconds",
        "input_b_durable_column": "effect_max_wall_seconds",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_max_wall_seconds]",
        "repaired_sql_column": "effect_max_wall_seconds",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "expires_at",
        "input_b_durable_column": "expires_at",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[expires_at]",
        "repaired_sql_column": "expires_at",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "global_stop_ref",
        "input_b_durable_column": "global_stop_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[global_stop_ref]",
        "repaired_sql_column": "global_stop_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "global_stop_version",
        "input_b_durable_column": "global_stop_version",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[global_stop_version]",
        "repaired_sql_column": "global_stop_version",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "portable_capsule_digest",
        "input_b_durable_column": "portable_capsule_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[portable_capsule_digest]",
        "repaired_sql_column": "portable_capsule_digest",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "cancellation_target_effect_intent_ref",
        "input_b_durable_column": "cancellation_target_effect_intent_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[cancellation_target_effect_intent_ref]",
        "repaired_sql_column": "cancellation_target_effect_intent_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "cancellation_target_effect_fence_ref",
        "input_b_durable_column": "cancellation_target_effect_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[cancellation_target_effect_fence_ref]",
        "repaired_sql_column": "cancellation_target_effect_fence_ref",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "cancellation_target_effect_fence_digest",
        "input_b_durable_column": "cancellation_target_effect_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[cancellation_target_effect_fence_digest]",
        "repaired_sql_column": "cancellation_target_effect_fence_digest",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "effect_fence_digest",
        "input_b_durable_column": "effect_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_effect_fences].columns[effect_fence_digest]",
        "repaired_sql_column": "effect_fence_digest",
        "table": "development_effect_fences",
        "value_type": "EffectFenceV1"
      },
      {
        "c2a_field": "schema_id",
        "input_b_durable_column": "schema_id",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[schema_id]",
        "repaired_sql_column": "schema_id",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "command_ref",
        "input_b_durable_column": "command_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[command_ref]",
        "repaired_sql_column": "command_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "program_ref",
        "input_b_durable_column": "program_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[program_ref]",
        "repaired_sql_column": "program_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "program_version_ref",
        "input_b_durable_column": "program_version_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[program_version_ref]",
        "repaired_sql_column": "program_version_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "accepted_intent_revision_ref",
        "input_b_durable_column": "accepted_intent_revision_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[accepted_intent_revision_ref]",
        "repaired_sql_column": "accepted_intent_revision_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "work_item_ref",
        "input_b_durable_column": "work_item_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[work_item_ref]",
        "repaired_sql_column": "work_item_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "work_item_revision_ref",
        "input_b_durable_column": "work_item_revision_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[work_item_revision_ref]",
        "repaired_sql_column": "work_item_revision_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "semantic_attempt_ref",
        "input_b_durable_column": "semantic_attempt_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[semantic_attempt_ref]",
        "repaired_sql_column": "semantic_attempt_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_intent_ref",
        "input_b_durable_column": "effect_intent_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_intent_ref]",
        "repaired_sql_column": "effect_intent_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_class",
        "input_b_durable_column": "effect_class",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_class]",
        "repaired_sql_column": "effect_class",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "candidate_ref",
        "input_b_durable_column": "candidate_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[candidate_ref]",
        "repaired_sql_column": "candidate_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "repository_ref",
        "input_b_durable_column": "repository_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[repository_ref]",
        "repaired_sql_column": "repository_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "base_git_object_format",
        "input_b_durable_column": "base_git_object_format",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[base_git_object_format]",
        "repaired_sql_column": "base_git_object_format",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "base_git_oid",
        "input_b_durable_column": "base_git_oid",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[base_git_oid]",
        "repaired_sql_column": "base_git_oid",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "path_ceiling",
        "input_b_durable_column": "path_ceiling_json",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[path_ceiling_json]",
        "repaired_sql_column": "path_ceiling_json",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "work_spec_ref",
        "input_b_durable_column": "work_spec_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[work_spec_ref]",
        "repaired_sql_column": "work_spec_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "work_spec_digest",
        "input_b_durable_column": "work_spec_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[work_spec_digest]",
        "repaired_sql_column": "work_spec_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "standing_grant_ref",
        "input_b_durable_column": "standing_grant_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[standing_grant_ref]",
        "repaired_sql_column": "standing_grant_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "standing_grant_digest",
        "input_b_durable_column": "standing_grant_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[standing_grant_digest]",
        "repaired_sql_column": "standing_grant_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "attempt_authorization_ref",
        "input_b_durable_column": "attempt_authorization_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[attempt_authorization_ref]",
        "repaired_sql_column": "attempt_authorization_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "attempt_authorization_digest",
        "input_b_durable_column": "attempt_authorization_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[attempt_authorization_digest]",
        "repaired_sql_column": "attempt_authorization_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_authorization_ref",
        "input_b_durable_column": "effect_authorization_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_authorization_ref]",
        "repaired_sql_column": "effect_authorization_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_authorization_digest",
        "input_b_durable_column": "effect_authorization_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_authorization_digest]",
        "repaired_sql_column": "effect_authorization_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "attempt_fence_ref",
        "input_b_durable_column": "attempt_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[attempt_fence_ref]",
        "repaired_sql_column": "attempt_fence_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "attempt_fence_digest",
        "input_b_durable_column": "attempt_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[attempt_fence_digest]",
        "repaired_sql_column": "attempt_fence_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_fence_ref",
        "input_b_durable_column": "effect_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_fence_ref]",
        "repaired_sql_column": "effect_fence_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_fence_digest",
        "input_b_durable_column": "effect_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_fence_digest]",
        "repaired_sql_column": "effect_fence_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "global_stop_ref",
        "input_b_durable_column": "global_stop_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[global_stop_ref]",
        "repaired_sql_column": "global_stop_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "global_stop_version",
        "input_b_durable_column": "global_stop_version",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[global_stop_version]",
        "repaired_sql_column": "global_stop_version",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "validation_requirement_ref",
        "input_b_durable_column": "validation_requirement_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[validation_requirement_ref]",
        "repaired_sql_column": "validation_requirement_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "validation_requirement_digest",
        "input_b_durable_column": "validation_requirement_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[validation_requirement_digest]",
        "repaired_sql_column": "validation_requirement_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "review_requirement_ref",
        "input_b_durable_column": "review_requirement_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[review_requirement_ref]",
        "repaired_sql_column": "review_requirement_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "review_requirement_digest",
        "input_b_durable_column": "review_requirement_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[review_requirement_digest]",
        "repaired_sql_column": "review_requirement_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "capsule_schema_id",
        "input_b_durable_column": "capsule_schema_id",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[capsule_schema_id]",
        "repaired_sql_column": "capsule_schema_id",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "capsule_profile_ref",
        "input_b_durable_column": "capsule_profile_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[capsule_profile_ref]",
        "repaired_sql_column": "capsule_profile_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_active_invocations",
        "input_b_durable_column": "effect_max_active_invocations",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_active_invocations]",
        "repaired_sql_column": "effect_max_active_invocations",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_candidate_bytes",
        "input_b_durable_column": "effect_max_candidate_bytes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_candidate_bytes]",
        "repaired_sql_column": "effect_max_candidate_bytes",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_changed_files",
        "input_b_durable_column": "effect_max_changed_files",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_changed_files]",
        "repaired_sql_column": "effect_max_changed_files",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_cost_microusd",
        "input_b_durable_column": "effect_max_cost_microusd",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_cost_microusd]",
        "repaired_sql_column": "effect_max_cost_microusd",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_cpu_seconds",
        "input_b_durable_column": "effect_max_cpu_seconds",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_cpu_seconds]",
        "repaired_sql_column": "effect_max_cpu_seconds",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_deliveries",
        "input_b_durable_column": "effect_max_deliveries",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_deliveries]",
        "repaired_sql_column": "effect_max_deliveries",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_deployments",
        "input_b_durable_column": "effect_max_deployments",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_deployments]",
        "repaired_sql_column": "effect_max_deployments",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_local_commits",
        "input_b_durable_column": "effect_max_local_commits",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_local_commits]",
        "repaired_sql_column": "effect_max_local_commits",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_memory_bytes",
        "input_b_durable_column": "effect_max_memory_bytes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_memory_bytes]",
        "repaired_sql_column": "effect_max_memory_bytes",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_merges",
        "input_b_durable_column": "effect_max_merges",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_merges]",
        "repaired_sql_column": "effect_max_merges",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_model_input_tokens",
        "input_b_durable_column": "effect_max_model_input_tokens",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_model_input_tokens]",
        "repaired_sql_column": "effect_max_model_input_tokens",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_model_output_tokens",
        "input_b_durable_column": "effect_max_model_output_tokens",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_model_output_tokens]",
        "repaired_sql_column": "effect_max_model_output_tokens",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_pull_requests",
        "input_b_durable_column": "effect_max_pull_requests",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_pull_requests]",
        "repaired_sql_column": "effect_max_pull_requests",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_pushes",
        "input_b_durable_column": "effect_max_pushes",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_pushes]",
        "repaired_sql_column": "effect_max_pushes",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "effect_ceilings.max_wall_seconds",
        "input_b_durable_column": "effect_max_wall_seconds",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[effect_max_wall_seconds]",
        "repaired_sql_column": "effect_max_wall_seconds",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "privacy_classification",
        "input_b_durable_column": "privacy_classification",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[privacy_classification]",
        "repaired_sql_column": "privacy_classification",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "redaction_profile_ref",
        "input_b_durable_column": "redaction_profile_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[redaction_profile_ref]",
        "repaired_sql_column": "redaction_profile_ref",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "command_digest",
        "input_b_durable_column": "command_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_author_commands].columns[command_digest]",
        "repaired_sql_column": "command_digest",
        "table": "development_author_commands",
        "value_type": "WorkerCommandV1"
      },
      {
        "c2a_field": "schema_id",
        "input_b_durable_column": "schema_id",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[schema_id]",
        "repaired_sql_column": "schema_id",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "delivery_attempt_ref",
        "input_b_durable_column": "delivery_attempt_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[delivery_attempt_ref]",
        "repaired_sql_column": "delivery_attempt_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "program_ref",
        "input_b_durable_column": "program_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[program_ref]",
        "repaired_sql_column": "program_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "program_version_ref",
        "input_b_durable_column": "program_version_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[program_version_ref]",
        "repaired_sql_column": "program_version_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "command_ref",
        "input_b_durable_column": "command_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[command_ref]",
        "repaired_sql_column": "command_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "command_digest",
        "input_b_durable_column": "command_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[command_digest]",
        "repaired_sql_column": "command_digest",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "semantic_attempt_ref",
        "input_b_durable_column": "semantic_attempt_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[semantic_attempt_ref]",
        "repaired_sql_column": "semantic_attempt_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "effect_intent_ref",
        "input_b_durable_column": "effect_intent_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[effect_intent_ref]",
        "repaired_sql_column": "effect_intent_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "attempt_fence_ref",
        "input_b_durable_column": "attempt_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[attempt_fence_ref]",
        "repaired_sql_column": "attempt_fence_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "attempt_fence_digest",
        "input_b_durable_column": "attempt_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[attempt_fence_digest]",
        "repaired_sql_column": "attempt_fence_digest",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "effect_fence_ref",
        "input_b_durable_column": "effect_fence_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[effect_fence_ref]",
        "repaired_sql_column": "effect_fence_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "effect_fence_digest",
        "input_b_durable_column": "effect_fence_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[effect_fence_digest]",
        "repaired_sql_column": "effect_fence_digest",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "adapter_kind",
        "input_b_durable_column": "adapter_kind",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[adapter_kind]",
        "repaired_sql_column": "adapter_kind",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "adapter_safe_correlation_ref",
        "input_b_durable_column": "adapter_safe_correlation_ref",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[adapter_safe_correlation_ref]",
        "repaired_sql_column": "adapter_safe_correlation_ref",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      },
      {
        "c2a_field": "delivery_envelope_digest",
        "input_b_durable_column": "delivery_envelope_digest",
        "match": "yes",
        "repaired_contract_spec_field": "tables[development_delivery_attempts].columns[delivery_envelope_digest]",
        "repaired_sql_column": "delivery_envelope_digest",
        "table": "development_delivery_attempts",
        "value_type": "DeliveryEnvelopeV1"
      }
    ],
    "summary_mappings": {
      "AttemptFenceV1": {
        "allowed_effect_classes_encoding": {
          "bit_order": [
            "author_candidate",
            "cancel_effect",
            "local_git_commit",
            "review_candidate",
            "validate_candidate"
          ],
          "column": "allowed_effect_class_mask",
          "valid_mask_range": [
            1,
            31
          ]
        },
        "operational_fields_excluded": [
          "recorded_at"
        ],
        "path_ceiling_encoding": {
          "canonical_value": [
            ".docs/system_overview/hybrid_integration_architecture_adr.md",
            "PLANS.md",
            "docs_contract_test.go"
          ],
          "column": "path_ceiling_json"
        },
        "table": "development_attempt_fences"
      },
      "CandidateCapsuleManifestV1": "migration_0003_safe_evidence_binding_only",
      "CapsuleEntryV1": "never_persisted",
      "CeilingsV1": {
        "fields": [
          "max_active_invocations",
          "max_candidate_bytes",
          "max_changed_files",
          "max_cost_microusd",
          "max_cpu_seconds",
          "max_deliveries",
          "max_deployments",
          "max_local_commits",
          "max_memory_bytes",
          "max_merges",
          "max_model_input_tokens",
          "max_model_output_tokens",
          "max_pull_requests",
          "max_pushes",
          "max_wall_seconds"
        ],
        "mapping": "flattened"
      },
      "DeliveryEnvelopeV1": {
        "nested_envelope_digest": "delivery_envelope_digest",
        "table": "development_delivery_attempts",
        "wrapper_digest": "delivery_attempt_digest"
      },
      "EffectFenceV1": {
        "operational_fields_excluded": [
          "recorded_at"
        ],
        "path_ceiling_encoding": {
          "canonical_value": [
            ".docs/system_overview/hybrid_integration_architecture_adr.md",
            "PLANS.md",
            "docs_contract_test.go"
          ],
          "column": "path_ceiling_json"
        },
        "table": "development_effect_fences"
      },
      "WorkerCommandV1": {
        "identity_excludes": [
          "effect_fence_digest",
          "command_digest",
          "recorded_at"
        ],
        "path_ceiling_encoding": {
          "canonical_value": [
            ".docs/system_overview/hybrid_integration_architecture_adr.md",
            "PLANS.md",
            "docs_contract_test.go"
          ],
          "column": "path_ceiling_json"
        },
        "table": "development_author_commands"
      },
      "WorkerObservationV1": "migration_0003_only"
    }
  },
  "classification": {
    "absent": [
      "C2B2 private readers",
      "C2B mutations and exact replay or recovery",
      "C2B product runtime caller"
    ],
    "accepted_c2b2_field_level_target_contract": "private readers and later integration over the migration-0002 core",
    "current_implemented_contract": "C2B2 Slice 1 migration administration and physical representation at application generation 2 and terminal tip 0002_development_program_and_effect_state plus Slice 2 pure private row/value source",
    "later_tranche_target_contract": "family-specific mutation, exact replay, recovery, and complete graph verification"
  },
  "common_graph_digest_primitive": {
    "array_order_significant": True,
    "closed_envelope": True,
    "closed_graph_entry": True,
    "domain": "governed-execution.nwp-development-mutation-receipt.v1.identity",
    "domain_separator_hex": "00",
    "duplicate_role_ordinal": "reject",
    "duplicate_role_record_ref": "reject",
    "encoding": "compact_sorted_key_utf8_json",
    "formula": "SHA-256(UTF8(domain) || 0x00 || compact sorted-key UTF-8 JSON(identity))",
    "graph_entry_ordered_keys": [
      "role",
      "ordinal",
      "record_ref",
      "record_digest"
    ],
    "identity_additional_field": "graph_entries",
    "identity_envelope_fields": [
      "schema_id",
      "mutation_ref",
      "mutation_family",
      "command_schema_id",
      "command_digest",
      "program_ref",
      "decision_ref",
      "result_program_version_ref",
      "result_semantic_attempt_ref",
      "result_effect_intent_ref",
      "result_effect_fence_ref",
      "result_delivery_attempt_ref",
      "result_observation_ref",
      "result_decision_ref",
      "result_class",
      "result_projection_digest",
      "outcome",
      "committed_at"
    ],
    "role_string_owner": "owning_family_contract",
    "same_record_ref_in_distinct_roles": "permitted",
    "self_digest_exclusion": "mutation_graph_digest"
  },
  "contract_id": "governed-execution.coordinator.c2b2-field-level-contract-freeze.v1",
  "decision_envelope": {
    "column_count": 43,
    "decision_kinds": [
      "initialize",
      "accept",
      "repair",
      "replan",
      "terminal_reject",
      "block",
      "redeliver",
      "cancel"
    ],
    "decision_variants": [
      "program_genesis",
      "candidate_acceptance",
      "candidate_repair",
      "program_replan",
      "attempt_selecting_replan",
      "program_terminal_reject",
      "program_block",
      "productive_redelivery",
      "cancellation_redelivery",
      "effect_cancellation"
    ],
    "digest_contract": {
      "domain": "governed-execution.nwp-development-decision.v1.identity",
      "identity_fields": [
        "schema_id",
        "mutation_ref",
        "decision_ref",
        "program_ref",
        "decision_kind",
        "decision_variant",
        "basis_decision_ref",
        "basis_program_version_ref",
        "basis_program_version_number",
        "expected_program_head_revision",
        "resulting_program_version_ref",
        "resulting_program_version_number",
        "selected_semantic_attempt_ref",
        "selected_candidate_ref",
        "selected_attempt_fence_ref",
        "selected_attempt_fence_digest",
        "target_effect_intent_ref",
        "target_effect_class",
        "target_effect_fence_ref",
        "target_effect_fence_digest",
        "expected_target_effect_head_revision",
        "target_delivery_attempt_ref",
        "originating_command_ref",
        "originating_command_digest",
        "target_capsule_manifest_ref",
        "target_portable_capsule_digest",
        "coding_global_stop_ref",
        "coding_global_stop_version",
        "source_directive_ref",
        "source_directive_digest",
        "source_evidence_ref",
        "source_evidence_digest",
        "preassigned_semantic_attempt_ref",
        "preassigned_candidate_ref",
        "preassigned_effect_intent_ref",
        "preassigned_effect_fence_ref",
        "preassigned_delivery_attempt_ref",
        "resulting_accepted_intent_revision_ref",
        "resulting_work_item_ref",
        "resulting_work_item_revision_ref",
        "reason_code",
        "decided_at"
      ],
      "schema_id": "governed-execution.nwp-development-decision.v1",
      "self_digest_excluded": True,
      "timestamp_included": True
    },
    "mutation_implemented": False,
    "non_version_advancing_kinds": [
      "redeliver",
      "cancel"
    ],
    "ordered_columns": [
      "schema_id",
      "mutation_ref",
      "decision_ref",
      "program_ref",
      "decision_kind",
      "decision_variant",
      "basis_decision_ref",
      "basis_program_version_ref",
      "basis_program_version_number",
      "expected_program_head_revision",
      "resulting_program_version_ref",
      "resulting_program_version_number",
      "selected_semantic_attempt_ref",
      "selected_candidate_ref",
      "selected_attempt_fence_ref",
      "selected_attempt_fence_digest",
      "target_effect_intent_ref",
      "target_effect_class",
      "target_effect_fence_ref",
      "target_effect_fence_digest",
      "expected_target_effect_head_revision",
      "target_delivery_attempt_ref",
      "originating_command_ref",
      "originating_command_digest",
      "target_capsule_manifest_ref",
      "target_portable_capsule_digest",
      "coding_global_stop_ref",
      "coding_global_stop_version",
      "source_directive_ref",
      "source_directive_digest",
      "source_evidence_ref",
      "source_evidence_digest",
      "preassigned_semantic_attempt_ref",
      "preassigned_candidate_ref",
      "preassigned_effect_intent_ref",
      "preassigned_effect_fence_ref",
      "preassigned_delivery_attempt_ref",
      "resulting_accepted_intent_revision_ref",
      "resulting_work_item_ref",
      "resulting_work_item_revision_ref",
      "reason_code",
      "decided_at",
      "decision_digest"
    ],
    "representation_owner": "C2B2",
    "variant_matrix": [
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_initialize_development_program",
        "kind": "initialize",
        "required_groups": [
          "result_version",
          "preassigned_attempt"
        ],
        "required_non_null_fields": [
          "preassigned_candidate_ref",
          "preassigned_semantic_attempt_ref",
          "resulting_program_version_number",
          "resulting_program_version_ref"
        ],
        "required_null_groups": [
          "basis",
          "selection",
          "target_effect",
          "target_delivery",
          "originating_command",
          "capsule",
          "source",
          "preassigned_effect",
          "preassigned_delivery",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='initialize' AND decision_variant='program_genesis' AND basis_decision_ref IS NULL AND basis_program_version_ref IS NULL AND basis_program_version_number IS NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NULL AND selected_candidate_ref IS NULL AND selected_attempt_fence_ref IS NULL AND selected_attempt_fence_digest IS NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND resulting_program_version_number=1 AND expected_program_head_revision=0)",
        "variant": "program_genesis",
        "version_advancing": True
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "accept",
        "required_groups": [
          "basis",
          "result_version",
          "selection"
        ],
        "required_non_null_fields": [
          "selected_attempt_fence_digest",
          "selected_attempt_fence_ref",
          "basis_decision_ref",
          "selected_candidate_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "resulting_program_version_number",
          "resulting_program_version_ref",
          "selected_semantic_attempt_ref"
        ],
        "required_null_groups": [
          "target_effect",
          "target_delivery",
          "originating_command",
          "capsule",
          "source",
          "preassigned_attempt",
          "preassigned_effect",
          "preassigned_delivery",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='accept' AND decision_variant='candidate_acceptance' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL)",
        "variant": "candidate_acceptance",
        "version_advancing": True
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "repair",
        "required_groups": [
          "basis",
          "result_version",
          "selection",
          "preassigned_attempt"
        ],
        "required_non_null_fields": [
          "selected_attempt_fence_digest",
          "selected_attempt_fence_ref",
          "basis_decision_ref",
          "selected_candidate_ref",
          "preassigned_candidate_ref",
          "preassigned_semantic_attempt_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "resulting_program_version_number",
          "resulting_program_version_ref",
          "selected_semantic_attempt_ref"
        ],
        "required_null_groups": [
          "target_effect",
          "target_delivery",
          "originating_command",
          "capsule",
          "source",
          "preassigned_effect",
          "preassigned_delivery",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='repair' AND decision_variant='candidate_repair' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL)",
        "variant": "candidate_repair",
        "version_advancing": True
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "replan",
        "required_groups": [
          "basis",
          "result_version",
          "result_intent"
        ],
        "required_non_null_fields": [
          "basis_decision_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "resulting_accepted_intent_revision_ref",
          "resulting_program_version_number",
          "resulting_program_version_ref"
        ],
        "required_null_groups": [
          "selection",
          "target_effect",
          "target_delivery",
          "originating_command",
          "capsule",
          "source",
          "preassigned_attempt",
          "preassigned_effect",
          "preassigned_delivery",
          "result_work"
        ],
        "sql_branch": "(decision_kind='replan' AND decision_variant='program_replan' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NULL AND selected_candidate_ref IS NULL AND selected_attempt_fence_ref IS NULL AND selected_attempt_fence_digest IS NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NOT NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL)",
        "variant": "program_replan",
        "version_advancing": True
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "replan",
        "required_groups": [
          "basis",
          "result_version",
          "selection",
          "preassigned_attempt",
          "result_intent",
          "result_work"
        ],
        "required_non_null_fields": [
          "selected_attempt_fence_digest",
          "selected_attempt_fence_ref",
          "basis_decision_ref",
          "selected_candidate_ref",
          "preassigned_candidate_ref",
          "preassigned_semantic_attempt_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "resulting_accepted_intent_revision_ref",
          "resulting_program_version_number",
          "resulting_program_version_ref",
          "resulting_work_item_ref",
          "resulting_work_item_revision_ref",
          "selected_semantic_attempt_ref"
        ],
        "required_null_groups": [
          "target_effect",
          "target_delivery",
          "originating_command",
          "capsule",
          "source",
          "preassigned_effect",
          "preassigned_delivery"
        ],
        "sql_branch": "(decision_kind='replan' AND decision_variant='attempt_selecting_replan' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NOT NULL AND resulting_work_item_ref IS NOT NULL AND resulting_work_item_revision_ref IS NOT NULL)",
        "variant": "attempt_selecting_replan",
        "version_advancing": True
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "terminal_reject",
        "required_groups": [
          "basis",
          "result_version",
          "selection"
        ],
        "required_non_null_fields": [
          "selected_attempt_fence_digest",
          "selected_attempt_fence_ref",
          "basis_decision_ref",
          "selected_candidate_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "resulting_program_version_number",
          "resulting_program_version_ref",
          "selected_semantic_attempt_ref"
        ],
        "required_null_groups": [
          "target_effect",
          "target_delivery",
          "originating_command",
          "capsule",
          "source",
          "preassigned_attempt",
          "preassigned_effect",
          "preassigned_delivery",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='terminal_reject' AND decision_variant='program_terminal_reject' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL)",
        "variant": "program_terminal_reject",
        "version_advancing": True
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "block",
        "required_groups": [
          "basis",
          "result_version"
        ],
        "required_non_null_fields": [
          "basis_decision_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "resulting_program_version_number",
          "resulting_program_version_ref"
        ],
        "required_null_groups": [
          "selection",
          "target_effect",
          "target_delivery",
          "originating_command",
          "capsule",
          "source",
          "preassigned_attempt",
          "preassigned_effect",
          "preassigned_delivery",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='block' AND decision_variant='program_block' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NULL AND selected_candidate_ref IS NULL AND selected_attempt_fence_ref IS NULL AND selected_attempt_fence_digest IS NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL)",
        "variant": "program_block",
        "version_advancing": True
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "redeliver",
        "required_groups": [
          "basis",
          "selection",
          "target_effect",
          "target_delivery",
          "originating_command",
          "preassigned_delivery"
        ],
        "required_non_null_fields": [
          "selected_attempt_fence_digest",
          "selected_attempt_fence_ref",
          "basis_decision_ref",
          "selected_candidate_ref",
          "expected_target_effect_head_revision",
          "originating_command_digest",
          "originating_command_ref",
          "preassigned_delivery_attempt_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "selected_semantic_attempt_ref",
          "target_delivery_attempt_ref",
          "target_effect_class",
          "target_effect_fence_digest",
          "target_effect_fence_ref",
          "target_effect_intent_ref"
        ],
        "required_null_groups": [
          "result_version",
          "capsule",
          "source",
          "preassigned_attempt",
          "preassigned_effect",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='redeliver' AND decision_variant='productive_redelivery' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NOT NULL AND originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND target_effect_class IN ('author_candidate','validate_candidate','review_candidate'))",
        "variant": "productive_redelivery",
        "version_advancing": False
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "redeliver",
        "required_groups": [
          "basis",
          "selection",
          "target_effect",
          "target_delivery",
          "originating_command",
          "preassigned_delivery"
        ],
        "required_non_null_fields": [
          "selected_attempt_fence_digest",
          "selected_attempt_fence_ref",
          "basis_decision_ref",
          "selected_candidate_ref",
          "expected_target_effect_head_revision",
          "originating_command_digest",
          "originating_command_ref",
          "preassigned_delivery_attempt_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "selected_semantic_attempt_ref",
          "target_delivery_attempt_ref",
          "target_effect_class",
          "target_effect_fence_digest",
          "target_effect_fence_ref",
          "target_effect_intent_ref"
        ],
        "required_null_groups": [
          "result_version",
          "capsule",
          "source",
          "preassigned_attempt",
          "preassigned_effect",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='redeliver' AND decision_variant='cancellation_redelivery' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NOT NULL AND originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND target_effect_class='cancel_effect')",
        "variant": "cancellation_redelivery",
        "version_advancing": False
      },
      {
        "evidence_binding": "deferred_to_migration_0003",
        "future_mutation_owner": "_record_development_progression_decision",
        "kind": "cancel",
        "required_groups": [
          "basis",
          "selection",
          "target_effect",
          "originating_command",
          "source",
          "preassigned_effect",
          "preassigned_delivery"
        ],
        "required_non_null_fields": [
          "selected_attempt_fence_digest",
          "selected_attempt_fence_ref",
          "basis_decision_ref",
          "selected_candidate_ref",
          "expected_target_effect_head_revision",
          "originating_command_digest",
          "originating_command_ref",
          "preassigned_delivery_attempt_ref",
          "preassigned_effect_fence_ref",
          "preassigned_effect_intent_ref",
          "basis_program_version_number",
          "basis_program_version_ref",
          "selected_semantic_attempt_ref",
          "source_directive_digest",
          "source_directive_ref",
          "source_evidence_digest",
          "source_evidence_ref",
          "target_effect_class",
          "target_effect_fence_digest",
          "target_effect_fence_ref",
          "target_effect_intent_ref"
        ],
        "required_null_groups": [
          "result_version",
          "target_delivery",
          "preassigned_attempt",
          "result_intent",
          "result_work"
        ],
        "sql_branch": "(decision_kind='cancel' AND decision_variant='effect_cancellation' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND ((target_effect_class='author_candidate' AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL) OR (target_effect_class IN ('validate_candidate','review_candidate') AND target_capsule_manifest_ref IS NOT NULL AND target_portable_capsule_digest IS NOT NULL)) AND source_directive_ref IS NOT NULL AND source_directive_digest IS NOT NULL AND source_evidence_ref IS NOT NULL AND source_evidence_digest IS NOT NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NOT NULL AND preassigned_effect_fence_ref IS NOT NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND target_effect_class IN ('author_candidate','validate_candidate','review_candidate'))",
        "variant": "effect_cancellation",
        "version_advancing": False
      }
    ],
    "version_advancing_kinds": [
      "initialize",
      "accept",
      "repair",
      "replan",
      "terminal_reject",
      "block"
    ]
  },
  "explicit_indexes": [
    {
      "columns": [
        "command_ref"
      ],
      "name": "uq_development_effect_intents_author_command",
      "sql": "CREATE UNIQUE INDEX uq_development_effect_intents_author_command\nON development_effect_intents(command_ref)\nWHERE effect_class = 'author_candidate';",
      "table": "development_effect_intents",
      "where": "effect_class = 'author_candidate'"
    }
  ],
  "family_replay_boundary": {
    "c2b2_does_not_freeze_or_implement": [
      "complete mutation-family replay graphs",
      "complete family graph verifier",
      "historical mutable-head replay",
      "family graph locators",
      "mutation",
      "recovery"
    ],
    "ownership": {
      "C2B3": [
        "initialize graph/replay",
        "author-effect graph/replay"
      ],
      "C2B4": [
        "migration-0003 row contracts/readers only"
      ],
      "C2B5": [
        "observation ingest graph/replay",
        "bound validation/review/cancellation effect graph/replay",
        "cancel graph/replay",
        "redeliver graph/replay"
      ],
      "C2B6": [
        "accept graph/replay",
        "repair graph/replay",
        "replan graph/replay",
        "terminal_reject graph/replay",
        "block graph/replay",
        "eligibility/latch/version/head replay"
      ]
    },
    "proposal_replay_material_classification": "reviewed later-tranche proposal evidence; not current C2B2 contract authority",
    "required_before_first_family_writer": [
      "closed role inventory",
      "role ranks",
      "ordinal sources",
      "record-ref derivations",
      "graph member locators",
      "historical mutable-head postimages",
      "family golden vectors",
      "complete exact replay",
      "commit-outcome recovery"
    ]
  },
  "foreign_keys": [
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "current_program_version_ref"
      ],
      "child_table": "development_program_heads",
      "deferrability": "DEFERRABLE INITIALLY DEFERRED",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "program_head_current_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref"
      ],
      "child_table": "development_program_versions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref"
      ],
      "parent_table": "development_program_heads",
      "role": "program_version_program"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "child_table": "development_program_versions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "program_version_accepted_intent_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "creating_decision_ref"
      ],
      "child_table": "development_program_versions",
      "deferrability": "DEFERRABLE INITIALLY DEFERRED",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "decision_ref"
      ],
      "parent_table": "development_decisions",
      "role": "program_version_creating_decision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref"
      ],
      "child_table": "development_accepted_intent_revisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref"
      ],
      "parent_table": "development_program_heads",
      "role": "accepted_intent_program"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "prior_accepted_intent_revision_ref"
      ],
      "child_table": "development_accepted_intent_revisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "accepted_intent_prior_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref"
      ],
      "child_table": "development_work_item_heads",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref"
      ],
      "parent_table": "development_program_heads",
      "role": "work_item_head_program"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "current_work_item_revision_ref"
      ],
      "child_table": "development_work_item_heads",
      "deferrability": "DEFERRABLE INITIALLY DEFERRED",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "work_item_head_current_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref"
      ],
      "child_table": "development_work_item_revisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref"
      ],
      "parent_table": "development_work_item_heads",
      "role": "work_item_revision_head"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "prior_work_item_revision_ref"
      ],
      "child_table": "development_work_item_revisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "work_item_revision_prior"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "child_table": "development_work_item_revisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "work_item_revision_accepted_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_program_version_work_items",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "membership_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "child_table": "development_program_version_work_items",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "membership_work_item_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref"
      ],
      "child_table": "development_revision_edges",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref"
      ],
      "parent_table": "development_program_heads",
      "role": "revision_edge_program"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "from_accepted_intent_revision_ref"
      ],
      "child_table": "development_revision_edges",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "revision_edge_from_accepted_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "to_accepted_intent_revision_ref"
      ],
      "child_table": "development_revision_edges",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "revision_edge_to_accepted_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "from_work_item_revision_ref"
      ],
      "child_table": "development_revision_edges",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "revision_edge_from_work_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "to_work_item_revision_ref"
      ],
      "child_table": "development_revision_edges",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "revision_edge_to_work_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_work_spec_bindings",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "work_spec_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "child_table": "development_work_spec_bindings",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "work_spec_accepted_intent_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "child_table": "development_work_spec_bindings",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "work_spec_work_item_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_semantic_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "semantic_attempt_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "child_table": "development_semantic_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "semantic_attempt_accepted_intent_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "child_table": "development_semantic_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "semantic_attempt_work_item_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "selection_decision_ref"
      ],
      "child_table": "development_semantic_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "decision_ref"
      ],
      "parent_table": "development_decisions",
      "role": "semantic_attempt_selection_decision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_attempt_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "attempt_fence_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "child_table": "development_attempt_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "attempt_fence_accepted_intent_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "child_table": "development_attempt_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "attempt_fence_work_item_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "child_table": "development_attempt_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "attempt_fence_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref"
      ],
      "child_table": "development_authority_evaluations",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref"
      ],
      "parent_table": "development_program_heads",
      "role": "authority_evaluation_program"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "child_table": "development_authority_evaluations",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "authority_evaluation_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "child_table": "development_authority_evaluations",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "authority_evaluation_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_effect_intents",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "effect_intent_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "child_table": "development_effect_intents",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "effect_intent_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Require equal program_ref, exact basis decision identity/digest, and basis-kind coherence; mismatch is database_integrity_failure.",
      "child_columns": [
        "basis_decision_ref"
      ],
      "child_table": "development_effect_intents",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "decision_ref"
      ],
      "parent_table": "development_decisions",
      "role": "effect_intent_basis_decision_owner_exception"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "command_ref"
      ],
      "child_table": "development_effect_intents",
      "deferrability": "DEFERRABLE INITIALLY DEFERRED",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "command_ref"
      ],
      "parent_table": "development_author_commands",
      "role": "author_effect_intent_command"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "cancellation_target_effect_intent_ref"
      ],
      "child_table": "development_effect_intents",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "cancellation_target_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "effect_fence_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "effect_fence_accepted_intent_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "effect_fence_work_item_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "effect_fence_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "effect_fence_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "attempt_fence_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "attempt_fence_ref"
      ],
      "parent_table": "development_attempt_fences",
      "role": "effect_fence_attempt_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "command_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "DEFERRABLE INITIALLY DEFERRED",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "command_ref"
      ],
      "parent_table": "development_author_commands",
      "role": "author_effect_fence_command"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "cancellation_target_effect_intent_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "effect_fence_cancellation_target_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "cancellation_target_effect_fence_ref"
      ],
      "child_table": "development_effect_fences",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "parent_table": "development_effect_fences",
      "role": "effect_fence_cancellation_target_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "author_command_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "author_command_accepted_intent_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "author_command_work_item_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "author_command_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "author_command_author_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "attempt_fence_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "attempt_fence_ref"
      ],
      "parent_table": "development_attempt_fences",
      "role": "author_command_attempt_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "parent_table": "development_effect_fences",
      "role": "author_command_effect_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "work_spec_ref"
      ],
      "child_table": "development_author_commands",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "work_spec_ref"
      ],
      "parent_table": "development_work_spec_bindings",
      "role": "author_command_work_spec_binding"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "child_table": "development_effect_heads",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "effect_head_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "current_effect_fence_ref"
      ],
      "child_table": "development_effect_heads",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "parent_table": "development_effect_fences",
      "role": "effect_head_current_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "cancellation_effect_intent_ref"
      ],
      "child_table": "development_effect_heads",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "effect_head_cancellation_effect"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "delivery_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "command_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "command_ref"
      ],
      "parent_table": "development_author_commands",
      "role": "delivery_originating_command"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "delivery_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "delivery_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "attempt_fence_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "attempt_fence_ref"
      ],
      "parent_table": "development_attempt_fences",
      "role": "delivery_attempt_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "parent_table": "development_effect_fences",
      "role": "delivery_effect_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "predecessor_delivery_attempt_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "delivery_attempt_ref"
      ],
      "parent_table": "development_delivery_attempts",
      "role": "delivery_predecessor"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "basis_decision_ref"
      ],
      "child_table": "development_delivery_attempts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "decision_ref"
      ],
      "parent_table": "development_decisions",
      "role": "delivery_basis_decision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "child_table": "development_delivery_heads",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "delivery_head_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "current_delivery_attempt_ref"
      ],
      "child_table": "development_delivery_heads",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "delivery_attempt_ref"
      ],
      "parent_table": "development_delivery_attempts",
      "role": "delivery_head_current_delivery_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref"
      ],
      "parent_table": "development_program_heads",
      "role": "decision_program"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "basis_decision_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "decision_ref"
      ],
      "parent_table": "development_decisions",
      "role": "decision_basis_decision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "basis_program_version_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "decision_basis_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "resulting_program_version_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "DEFERRABLE INITIALLY DEFERRED",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "initialize_decision_resulting_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "selected_semantic_attempt_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "decision_selected_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "selected_attempt_fence_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "attempt_fence_ref"
      ],
      "parent_table": "development_attempt_fences",
      "role": "decision_selected_attempt_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "target_effect_intent_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "decision_target_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "target_effect_fence_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "parent_table": "development_effect_fences",
      "role": "decision_target_effect_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "target_delivery_attempt_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "delivery_attempt_ref"
      ],
      "parent_table": "development_delivery_attempts",
      "role": "decision_target_delivery_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "originating_command_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "command_ref"
      ],
      "parent_table": "development_author_commands",
      "role": "decision_originating_command"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "resulting_accepted_intent_revision_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "accepted_intent_revision_ref"
      ],
      "parent_table": "development_accepted_intent_revisions",
      "role": "decision_resulting_accepted_intent_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "resulting_work_item_ref",
        "resulting_work_item_revision_ref"
      ],
      "child_table": "development_decisions",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref"
      ],
      "parent_table": "development_work_item_revisions",
      "role": "decision_resulting_work_item_revision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref"
      ],
      "parent_table": "development_program_heads",
      "role": "receipt_program"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "decision_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "decision_ref"
      ],
      "parent_table": "development_decisions",
      "role": "receipt_decision"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "result_program_version_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "program_version_ref"
      ],
      "parent_table": "development_program_versions",
      "role": "receipt_result_program_version"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "result_semantic_attempt_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "semantic_attempt_ref"
      ],
      "parent_table": "development_semantic_attempts",
      "role": "receipt_result_semantic_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "result_effect_intent_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_intent_ref"
      ],
      "parent_table": "development_effect_intents",
      "role": "receipt_result_effect_intent"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "result_effect_fence_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "effect_fence_ref"
      ],
      "parent_table": "development_effect_fences",
      "role": "receipt_result_effect_fence"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "result_delivery_attempt_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "delivery_attempt_ref"
      ],
      "parent_table": "development_delivery_attempts",
      "role": "receipt_result_delivery_attempt"
    },
    {
      "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
      "child_columns": [
        "program_ref",
        "result_decision_ref"
      ],
      "child_table": "development_mutation_receipts",
      "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
      "on_delete": "RESTRICT",
      "on_update": "RESTRICT",
      "parent_columns": [
        "program_ref",
        "decision_ref"
      ],
      "parent_table": "development_decisions",
      "role": "receipt_result_decision"
    }
  ],
  "nonimplementation": {
    "complete_family_replay": False,
    "database_mutation": False,
    "dependency": False,
    "migration_0002_repository_sql": False,
    "migration_0003_pulled_forward": False,
    "mutation_or_recovery_api": False,
    "package_root_export": False,
    "production_source": False,
    "public_reader": False,
    "runtime_authority": False,
    "state_store_method": False,
    "writer_session_method": False
  },
  "oracle_architecture": {
    "allowed_literal_nodes": [
      "dict",
      "list",
      "tuple",
      "str",
      "int",
      "bool",
      "None"
    ],
    "allowed_repository_reads": [
      ".docs/c2b-durable-development-state.md"
    ],
    "architecture_self_check_additional_read": "tests/test_c2b2_field_level_contract.py",
    "dynamic_dispatch": "forbidden",
    "expected_contract_assignment_count": 1,
    "expected_contract_rhs": "directly literal Python expression",
    "forbidden_imports": [
      "another collected test",
      "ge_nwp_coordinator production source",
      "sqlite3",
      "importlib or dynamic import"
    ],
    "forbidden_input_reads": [
      "external SQL",
      "external proposal JSON",
      "production source",
      "Downloads or proposal-artifact path"
    ],
    "forbidden_literal_nodes": [
      "nonconstant Name",
      "Call",
      "Attribute",
      "Subscript",
      "comprehension",
      "generator",
      "lambda",
      "formatted string"
    ],
    "forbidden_runtime_selection": [
      "eval",
      "exec",
      "built-in compile",
      "__import__",
      "getattr-based callable selection",
      "globals-based callable selection",
      "locals-based callable selection",
      "call through Subscript",
      "callable registry",
      "validator registry",
      "generic dispatch table"
    ],
    "permitted_semantic_sha256_call_sites": [
      {
        "enclosing_function": "_graph_digest_from_identity",
        "purpose": "produce the domain-separated semantic mutation-graph digest"
      },
      {
        "enclosing_function": "test_c2b2_common_graph_digest_primitive_is_closed_and_order_sensitive",
        "purpose": "independently verify the semantic mutation-graph golden formula"
      }
    ],
    "runtime_literal_equality": "ast.literal_eval(assignment value) equals runtime EXPECTED_CONTRACT",
    "source_or_file_hash_authority": "forbidden; diagnostic hashes cannot substitute for semantic equality"
  },
  "privacy_contract": {
    "forbidden_persistent_material": [
      "WorkSpec objective",
      "requirements",
      "exclusions",
      "credentials",
      "private endpoints",
      "bearer retrieval material",
      "private prompts or responses",
      "transcripts",
      "source bytes",
      "candidate bytes",
      "capsule bytes or entries",
      "physical workspace paths",
      "TLS/SPIFFE/Vault/Codex/OpenAI material"
    ],
    "persisted_classes": [
      "safe references",
      "digests",
      "fixed states",
      "integer counters and ceilings",
      "whole-second UTC timestamps",
      "exact current repository-relative C2A path arrays"
    ],
    "privacy_vocabularies": {
      "work_spec": "private_work_spec",
      "worker_command": "private_source_change"
    },
    "safe_failure": "privacy-safe closed error vocabulary; no exception string or diagnostic includes persisted private material"
  },
  "private_readers": {
    "aggregate_value_contracts": [
      {
        "fields": [
          "program_head",
          "current_program_version"
        ],
        "type": "DevelopmentProgramHeadAndCurrentVersionRead"
      },
      {
        "fields": [
          "initialize_decision",
          "resulting_program_version"
        ],
        "type": "DevelopmentInitializeDecisionAndResultingVersionRead"
      },
      {
        "fields": [
          "work_item_head",
          "work_item_revision",
          "is_current"
        ],
        "type": "DevelopmentWorkItemHeadAndRevisionRead"
      },
      {
        "fields": [
          "membership",
          "work_item_revision"
        ],
        "type": "DevelopmentProgramVersionMembershipEntry"
      },
      {
        "fields": [
          "program_version",
          "entries"
        ],
        "type": "DevelopmentProgramVersionMembershipRead"
      },
      {
        "fields": [
          "semantic_attempt",
          "effect_intent",
          "author_command",
          "attempt_fence",
          "current_effect_fence",
          "author_effect_fence"
        ],
        "type": "DevelopmentAttemptFenceCommandEffectRead"
      },
      {
        "fields": [
          "delivery_head",
          "current_delivery_attempt"
        ],
        "type": "DevelopmentDeliveryHeadAndCurrentAttemptRead"
      }
    ],
    "common_contract": {
      "aggregate_value_posture": [
        "manual slots",
        "no __dict__ or weakref",
        "factory-only construction",
        "no subclassing",
        "exact-type equality",
        "unhashable",
        "content-free repr/str",
        "copy/deepcopy identity",
        "pickle disabled",
        "tuples for collections",
        "no SQL, parameters, row tuples, mappings, cursors, connections, capabilities, or epochs retained"
      ],
      "capability_errors_outside_reader_safe_error": [
        "mutation_read_capability_unavailable",
        "mutation_read_capability_expired",
        "process_mismatch",
        "thread_mismatch"
      ],
      "capability_path_order": [
        "pure lookup/resource validation",
        "function-local import of _SQLiteMutationReadCapability",
        "type(capability) is _SQLiteMutationReadCapability",
        "capability borrow",
        "literal SQL execution"
      ],
      "invalid_authority_zero_borrow_zero_sql_matrix": [
        "None",
        "arbitrary object",
        "structural stand-in",
        "forged borrow object",
        "raw sqlite3.Connection",
        "nominal subclass"
      ],
      "lookup_validation_failure": "database_integrity_failure",
      "no_partial_aggregate": True,
      "post_borrow_error_classification": {
        "earlier_execute_or_fetch_failure_precedence": "preserved over later cursor-close failure",
        "operational_busy_locked_closed_unknown_io": "mutation_failed",
        "otherwise_successful_read_then_cursor_close_failure": "mutation_failed",
        "sqlite_schema_cardinality_row_relation_contradiction": "database_integrity_failure"
      },
      "reader_safe_error": "mutation_failed_or_database_integrity_failure",
      "reconnaissance_binding": {
        "planning_decision": "BLOCKED_PENDING_READER_CONTRACT_CHANGE",
        "turn_verdict": "COORDINATOR_C2B2_SLICE_3_RECONNAISSANCE_BLOCKED"
      },
      "shared_bounded_fetch_future_contract": {
        "accepted_limits": [
          2,
          257
        ],
        "bounded_core_owns": [
          "one borrow",
          "one cursor",
          "literal execute with exact tuple",
          "fetchmany(limit)",
          "cursor close",
          "execute/fetch precedence over close",
          "safe SQLite error classification"
        ],
        "bounded_core_owns_no": [
          "nominal authority",
          "semantic dispatch",
          "table dispatch"
        ],
        "compatibility_wrapper": "_execute_select_fetch_two() remains with unchanged observable behavior",
        "source_path": "src/ge_nwp_coordinator/sqlite_transition_select_support.py"
      },
      "status": {
        "accepted_target": "exact twelve private readers under this reset contract",
        "current": [
          "generation-2 migration-0002 schema",
          "four private pure row/value modules"
        ],
        "still_absent": [
          "reader source",
          "SELECT execution",
          "nominal capability use by C2B2",
          "production caller",
          "mutation and receipt persistence",
          "family-complete graph verification",
          "replay and recovery",
          "C2B3",
          "migration 0003"
        ]
      }
    },
    "empty_membership_permitted_program_version_kinds": [],
    "future_implementation_allowlist": {
      "existing_documentation_modifications": [
        ".docs/c2b-durable-development-state.md",
        ".docs/c2b2-migration-0002.md",
        ".docs/c2b2-pure-durable-row-values.md",
        ".docs/architecture.md",
        ".docs/autonomous-software-development-operating-model.md",
        ".docs/durable-state-model.md",
        ".docs/software-development-progression-boundary.md",
        ".docs/sqlite-threat-model.md",
        "README.md",
        "AGENTS.md"
      ],
      "existing_production_source_modifications": [
        "src/ge_nwp_coordinator/sqlite_transition_select_support.py"
      ],
      "existing_test_modifications": [
        "tests/test_c2b2_field_level_contract.py",
        "tests/test_c2b0_durable_state_contract.py",
        "tests/test_architecture_contracts.py",
        "tests/test_autonomous_software_development_operating_model.py",
        "tests/test_software_development_progression_boundary.py",
        "tests/test_runtime_non_authority.py",
        "tests/test_c2a_nonimplementation.py"
      ],
      "maximum_path_count": 23,
      "new_documentation": [
        ".docs/c2b2-private-readers.md"
      ],
      "new_focused_tests": [
        "tests/test_c2b2_development_reader_contracts.py",
        "tests/test_c2b2_private_development_readers.py"
      ],
      "new_production_source": [
        "src/ge_nwp_coordinator/_sqlite_development_reader_contracts.py",
        "src/ge_nwp_coordinator/_sqlite_development_readers.py"
      ],
      "package_or_configuration_modifications": [],
      "schema_or_migration_modifications": [],
      "twenty_fourth_path_disposition": "stop condition; not implicit authorization"
    },
    "prohibited_authority_locators": [
      "latest timestamp",
      "MAX(evaluated_at)",
      "rowid",
      "lexicographic ref order",
      "preferred authority state",
      "verified-first selection",
      "unbounded subject scan",
      "receipt digest"
    ],
    "roles": [
      {
        "absence_precedence": {
          "absent_root": "return None and execute no child SQL",
          "malformed_or_duplicate_root": "database_integrity_failure and execute no child SQL",
          "parent_validation_before_child_sql": True,
          "partial_aggregate_return": "forbidden",
          "present_root_required_child": "not_applicable",
          "root_query": "mutation_receipt"
        },
        "aggregate_fields": [],
        "bounded_aggregate_verification": "permitted",
        "cardinality": "singleton",
        "complete_mutation_family_replay_verification": False,
        "decoded_private_value": "DevelopmentMutationReceiptRowValue",
        "duplicate_result": "database_integrity_failure",
        "future_caller": [
          "C2B3",
          "C2B5",
          "C2B6"
        ],
        "later_tranche_exclusions": [
          "default graph_entries to ()",
          "graph verification",
          "family completeness",
          "referenced-row existence",
          "family row location",
          "exact replay",
          "recovery"
        ],
        "lookup_identity": [
          "mutation_ref"
        ],
        "malformed_row_result": "database_integrity_failure",
        "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
        "operational_inputs": [],
        "private_function": "_read_development_mutation_receipt_by_mutation_ref",
        "query_order": [
          "mutation_receipt"
        ],
        "result_type": "DevelopmentMutationReceiptRowValue | None",
        "role": "mutation_receipt_by_mutation_ref",
        "row_digest_verification": "not_applicable: the receipt has no row self-digest",
        "safe_error": "mutation_failed_or_database_integrity_failure",
        "selects": [
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "mutation_ref",
              "mutation_family",
              "command_schema_id",
              "command_digest",
              "program_ref",
              "decision_ref",
              "result_program_version_ref",
              "result_semantic_attempt_ref",
              "result_effect_intent_ref",
              "result_effect_fence_ref",
              "result_delivery_attempt_ref",
              "result_observation_ref",
              "result_decision_ref",
              "result_class",
              "result_projection_digest",
              "mutation_graph_digest",
              "outcome",
              "committed_at"
            ],
            "limit": 2,
            "lookup_key": [
              "mutation_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "mutation_ref"
            ],
            "parameter_tuple": "(mutation_ref,)",
            "query_id": "mutation_receipt",
            "query_sql": "SELECT schema_id, mutation_ref, mutation_family, command_schema_id, command_digest, program_ref, decision_ref, result_program_version_ref, result_semantic_attempt_ref, result_effect_intent_ref, result_effect_fence_ref, result_delivery_attempt_ref, result_observation_ref, result_decision_ref, result_class, result_projection_digest, mutation_graph_digest, outcome, committed_at FROM development_mutation_receipts WHERE mutation_ref = ? LIMIT 2",
            "table": "development_mutation_receipts"
          }
        ],
        "signature": "(capability, mutation_ref) -> DevelopmentMutationReceiptRowValue | None",
        "signature_inputs": [
          "capability",
          "mutation_ref"
        ],
        "slice3_cross_row_validation": [
          "exact row shape and scalar algebra",
          "result projection",
          "result_projection_digest",
          "mutation_graph_digest lowercase SHA-256 shape"
        ]
      },
      {
        "absence_precedence": {
          "absent_root": "return None and execute no child SQL",
          "malformed_or_duplicate_root": "database_integrity_failure and execute no child SQL",
          "parent_validation_before_child_sql": True,
          "partial_aggregate_return": "forbidden",
          "present_root_required_child": "not_applicable",
          "root_query": "decision"
        },
        "aggregate_fields": [],
        "bounded_aggregate_verification": "permitted",
        "cardinality": "singleton",
        "complete_mutation_family_replay_verification": False,
        "decoded_private_value": "DevelopmentDecisionRowValue",
        "duplicate_result": "database_integrity_failure",
        "future_caller": [
          "C2B3",
          "C2B5",
          "C2B6"
        ],
        "later_tranche_exclusions": [
          "family graph location",
          "family completeness",
          "exact replay",
          "commit-outcome recovery",
          "mutation"
        ],
        "lookup_identity": [
          "decision_ref"
        ],
        "malformed_row_result": "database_integrity_failure",
        "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
        "operational_inputs": [],
        "private_function": "_read_development_decision_by_decision_ref",
        "query_order": [
          "decision"
        ],
        "result_type": "DevelopmentDecisionRowValue | None",
        "role": "decision_by_decision_ref",
        "row_digest_verification": "required_before_return",
        "safe_error": "mutation_failed_or_database_integrity_failure",
        "selects": [
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "mutation_ref",
              "decision_ref",
              "program_ref",
              "decision_kind",
              "decision_variant",
              "basis_decision_ref",
              "basis_program_version_ref",
              "basis_program_version_number",
              "expected_program_head_revision",
              "resulting_program_version_ref",
              "resulting_program_version_number",
              "selected_semantic_attempt_ref",
              "selected_candidate_ref",
              "selected_attempt_fence_ref",
              "selected_attempt_fence_digest",
              "target_effect_intent_ref",
              "target_effect_class",
              "target_effect_fence_ref",
              "target_effect_fence_digest",
              "expected_target_effect_head_revision",
              "target_delivery_attempt_ref",
              "originating_command_ref",
              "originating_command_digest",
              "target_capsule_manifest_ref",
              "target_portable_capsule_digest",
              "coding_global_stop_ref",
              "coding_global_stop_version",
              "source_directive_ref",
              "source_directive_digest",
              "source_evidence_ref",
              "source_evidence_digest",
              "preassigned_semantic_attempt_ref",
              "preassigned_candidate_ref",
              "preassigned_effect_intent_ref",
              "preassigned_effect_fence_ref",
              "preassigned_delivery_attempt_ref",
              "resulting_accepted_intent_revision_ref",
              "resulting_work_item_ref",
              "resulting_work_item_revision_ref",
              "reason_code",
              "decided_at",
              "decision_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "decision_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "decision_ref"
            ],
            "parameter_tuple": "(decision_ref,)",
            "query_id": "decision",
            "query_sql": "SELECT schema_id, mutation_ref, decision_ref, program_ref, decision_kind, decision_variant, basis_decision_ref, basis_program_version_ref, basis_program_version_number, expected_program_head_revision, resulting_program_version_ref, resulting_program_version_number, selected_semantic_attempt_ref, selected_candidate_ref, selected_attempt_fence_ref, selected_attempt_fence_digest, target_effect_intent_ref, target_effect_class, target_effect_fence_ref, target_effect_fence_digest, expected_target_effect_head_revision, target_delivery_attempt_ref, originating_command_ref, originating_command_digest, target_capsule_manifest_ref, target_portable_capsule_digest, coding_global_stop_ref, coding_global_stop_version, source_directive_ref, source_directive_digest, source_evidence_ref, source_evidence_digest, preassigned_semantic_attempt_ref, preassigned_candidate_ref, preassigned_effect_intent_ref, preassigned_effect_fence_ref, preassigned_delivery_attempt_ref, resulting_accepted_intent_revision_ref, resulting_work_item_ref, resulting_work_item_revision_ref, reason_code, decided_at, decision_digest FROM development_decisions WHERE decision_ref = ? LIMIT 2",
            "table": "development_decisions"
          }
        ],
        "signature": "(capability, decision_ref) -> DevelopmentDecisionRowValue | None",
        "signature_inputs": [
          "capability",
          "decision_ref"
        ],
        "slice3_cross_row_validation": []
      },
      {
        "absence_precedence": {
          "absent_root": "return None and execute no child SQL",
          "malformed_or_duplicate_root": "database_integrity_failure and execute no child SQL",
          "parent_validation_before_child_sql": True,
          "partial_aggregate_return": "forbidden",
          "present_root_required_child": "missing, duplicate, malformed, or mismatched current program version is database_integrity_failure",
          "root_query": "program_head"
        },
        "aggregate_fields": [
          "program_head",
          "current_program_version"
        ],
        "bounded_aggregate_verification": "permitted",
        "cardinality": "root_plus_one_required_child",
        "complete_mutation_family_replay_verification": False,
        "decoded_private_value": "DevelopmentProgramHeadAndCurrentVersionRead",
        "duplicate_result": "database_integrity_failure",
        "future_caller": [
          "C2B3",
          "C2B6"
        ],
        "later_tranche_exclusions": [
          "family graph location",
          "family completeness",
          "exact replay",
          "commit-outcome recovery",
          "mutation"
        ],
        "lookup_identity": [
          "program_ref"
        ],
        "malformed_row_result": "database_integrity_failure",
        "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
        "operational_inputs": [],
        "private_function": "_read_development_program_head_and_current_version",
        "query_order": [
          "program_head",
          "current_program_version"
        ],
        "result_type": "DevelopmentProgramHeadAndCurrentVersionRead | None",
        "role": "program_head_and_current_version",
        "row_digest_verification": "required_before_return",
        "safe_error": "mutation_failed_or_database_integrity_failure",
        "selects": [
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "program_ref",
              "current_program_version_ref",
              "current_program_version_number",
              "head_revision",
              "program_state",
              "updated_at",
              "head_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref"
            ],
            "parameter_tuple": "(program_ref,)",
            "query_id": "program_head",
            "query_sql": "SELECT schema_id, program_ref, current_program_version_ref, current_program_version_number, head_revision, program_state, updated_at, head_digest FROM development_program_heads WHERE program_ref = ? LIMIT 2",
            "table": "development_program_heads"
          },
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "program_version_ref",
              "program_ref",
              "program_version_number",
              "program_version_kind",
              "creating_decision_ref",
              "accepted_intent_revision_ref",
              "created_at",
              "program_version_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "program_head.current_program_version_ref",
              "program_head.current_program_version_number"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "program_head.current_program_version_ref",
              "program_head.current_program_version_number"
            ],
            "parameter_tuple": "(program_ref, program_head.current_program_version_ref, program_head.current_program_version_number)",
            "query_id": "current_program_version",
            "query_sql": "SELECT schema_id, program_version_ref, program_ref, program_version_number, program_version_kind, creating_decision_ref, accepted_intent_revision_ref, created_at, program_version_digest FROM development_program_versions WHERE program_ref = ? AND program_version_ref = ? AND program_version_number = ? LIMIT 2",
            "table": "development_program_versions"
          }
        ],
        "signature": "(capability, program_ref) -> DevelopmentProgramHeadAndCurrentVersionRead | None",
        "signature_inputs": [
          "capability",
          "program_ref"
        ],
        "slice3_cross_row_validation": [
          "exact program identity",
          "current program-version ref equality",
          "current program-version number equality"
        ]
      },
      {
        "absence_precedence": {
          "absent_root": "return None and execute no child SQL",
          "malformed_or_duplicate_root": "database_integrity_failure and execute no child SQL",
          "parent_validation_before_child_sql": True,
          "partial_aggregate_return": "forbidden",
          "present_root_required_child": "missing, duplicate, malformed, or mismatched resulting program version is database_integrity_failure",
          "root_query": "initialize_decision"
        },
        "aggregate_fields": [
          "initialize_decision",
          "resulting_program_version"
        ],
        "bounded_aggregate_verification": "permitted",
        "cardinality": "root_plus_one_required_child",
        "complete_mutation_family_replay_verification": False,
        "decoded_private_value": "DevelopmentInitializeDecisionAndResultingVersionRead",
        "duplicate_result": "database_integrity_failure",
        "future_caller": [
          "C2B3"
        ],
        "later_tranche_exclusions": [
          "generalized arbitrary version-advancing decision reader"
        ],
        "lookup_identity": [
          "program_ref",
          "decision_ref"
        ],
        "malformed_row_result": "database_integrity_failure",
        "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
        "operational_inputs": [],
        "private_function": "_read_development_initialize_decision_and_resulting_version",
        "query_order": [
          "initialize_decision",
          "resulting_program_version"
        ],
        "result_type": "DevelopmentInitializeDecisionAndResultingVersionRead | None",
        "role": "initialize_decision_and_resulting_version",
        "row_digest_verification": "required_before_return",
        "safe_error": "mutation_failed_or_database_integrity_failure",
        "selects": [
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "mutation_ref",
              "decision_ref",
              "program_ref",
              "decision_kind",
              "decision_variant",
              "basis_decision_ref",
              "basis_program_version_ref",
              "basis_program_version_number",
              "expected_program_head_revision",
              "resulting_program_version_ref",
              "resulting_program_version_number",
              "selected_semantic_attempt_ref",
              "selected_candidate_ref",
              "selected_attempt_fence_ref",
              "selected_attempt_fence_digest",
              "target_effect_intent_ref",
              "target_effect_class",
              "target_effect_fence_ref",
              "target_effect_fence_digest",
              "expected_target_effect_head_revision",
              "target_delivery_attempt_ref",
              "originating_command_ref",
              "originating_command_digest",
              "target_capsule_manifest_ref",
              "target_portable_capsule_digest",
              "coding_global_stop_ref",
              "coding_global_stop_version",
              "source_directive_ref",
              "source_directive_digest",
              "source_evidence_ref",
              "source_evidence_digest",
              "preassigned_semantic_attempt_ref",
              "preassigned_candidate_ref",
              "preassigned_effect_intent_ref",
              "preassigned_effect_fence_ref",
              "preassigned_delivery_attempt_ref",
              "resulting_accepted_intent_revision_ref",
              "resulting_work_item_ref",
              "resulting_work_item_revision_ref",
              "reason_code",
              "decided_at",
              "decision_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "decision_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "decision_ref"
            ],
            "parameter_tuple": "(program_ref, decision_ref)",
            "query_id": "initialize_decision",
            "query_sql": "SELECT schema_id, mutation_ref, decision_ref, program_ref, decision_kind, decision_variant, basis_decision_ref, basis_program_version_ref, basis_program_version_number, expected_program_head_revision, resulting_program_version_ref, resulting_program_version_number, selected_semantic_attempt_ref, selected_candidate_ref, selected_attempt_fence_ref, selected_attempt_fence_digest, target_effect_intent_ref, target_effect_class, target_effect_fence_ref, target_effect_fence_digest, expected_target_effect_head_revision, target_delivery_attempt_ref, originating_command_ref, originating_command_digest, target_capsule_manifest_ref, target_portable_capsule_digest, coding_global_stop_ref, coding_global_stop_version, source_directive_ref, source_directive_digest, source_evidence_ref, source_evidence_digest, preassigned_semantic_attempt_ref, preassigned_candidate_ref, preassigned_effect_intent_ref, preassigned_effect_fence_ref, preassigned_delivery_attempt_ref, resulting_accepted_intent_revision_ref, resulting_work_item_ref, resulting_work_item_revision_ref, reason_code, decided_at, decision_digest FROM development_decisions WHERE program_ref = ? AND decision_ref = ? LIMIT 2",
            "table": "development_decisions"
          },
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "program_version_ref",
              "program_ref",
              "program_version_number",
              "program_version_kind",
              "creating_decision_ref",
              "accepted_intent_revision_ref",
              "created_at",
              "program_version_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "initialize_decision.resulting_program_version_ref",
              "initialize_decision.resulting_program_version_number"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "initialize_decision.resulting_program_version_ref",
              "initialize_decision.resulting_program_version_number"
            ],
            "parameter_tuple": "(program_ref, initialize_decision.resulting_program_version_ref, initialize_decision.resulting_program_version_number)",
            "query_id": "resulting_program_version",
            "query_sql": "SELECT schema_id, program_version_ref, program_ref, program_version_number, program_version_kind, creating_decision_ref, accepted_intent_revision_ref, created_at, program_version_digest FROM development_program_versions WHERE program_ref = ? AND program_version_ref = ? AND program_version_number = ? LIMIT 2",
            "table": "development_program_versions"
          }
        ],
        "signature": "(capability, program_ref, decision_ref) -> DevelopmentInitializeDecisionAndResultingVersionRead | None",
        "signature_inputs": [
          "capability",
          "program_ref",
          "decision_ref"
        ],
        "slice3_cross_row_validation": [
          "decision_kind == initialize",
          "decision_variant == program_genesis",
          "basis version fields are null",
          "resulting version fields are present",
          "program version kind == initial",
          "program version number == 1",
          "program version creating_decision_ref == decision_ref",
          "program identity is exact"
        ]
      },
      {
        "absence_precedence": {
          "absent_root": "return None and execute no child SQL",
          "malformed_or_duplicate_root": "database_integrity_failure and execute no child SQL",
          "parent_validation_before_child_sql": True,
          "partial_aggregate_return": "forbidden",
          "present_root_required_child": "not_applicable",
          "root_query": "accepted_intent_revision"
        },
        "aggregate_fields": [],
        "bounded_aggregate_verification": "permitted",
        "cardinality": "singleton",
        "complete_mutation_family_replay_verification": False,
        "decoded_private_value": "DevelopmentAcceptedIntentRevisionRowValue",
        "duplicate_result": "database_integrity_failure",
        "future_caller": [
          "C2B3",
          "C2B6"
        ],
        "later_tranche_exclusions": [
          "family graph location",
          "family completeness",
          "exact replay",
          "commit-outcome recovery",
          "mutation"
        ],
        "lookup_identity": [
          "program_ref",
          "accepted_intent_revision_ref"
        ],
        "malformed_row_result": "database_integrity_failure",
        "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
        "operational_inputs": [],
        "private_function": "_read_development_accepted_intent_revision_by_exact_ref",
        "query_order": [
          "accepted_intent_revision"
        ],
        "result_type": "DevelopmentAcceptedIntentRevisionRowValue | None",
        "role": "accepted_intent_revision_by_exact_ref",
        "row_digest_verification": "required_before_return",
        "safe_error": "mutation_failed_or_database_integrity_failure",
        "selects": [
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "accepted_intent_revision_ref",
              "program_ref",
              "accepted_intent_revision_number",
              "prior_accepted_intent_revision_ref",
              "source_intent_ref",
              "source_intent_digest",
              "safe_projection_digest",
              "created_at",
              "accepted_intent_revision_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "accepted_intent_revision_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "accepted_intent_revision_ref"
            ],
            "parameter_tuple": "(program_ref, accepted_intent_revision_ref)",
            "query_id": "accepted_intent_revision",
            "query_sql": "SELECT schema_id, accepted_intent_revision_ref, program_ref, accepted_intent_revision_number, prior_accepted_intent_revision_ref, source_intent_ref, source_intent_digest, safe_projection_digest, created_at, accepted_intent_revision_digest FROM development_accepted_intent_revisions WHERE program_ref = ? AND accepted_intent_revision_ref = ? LIMIT 2",
            "table": "development_accepted_intent_revisions"
          }
        ],
        "signature": "(capability, program_ref, accepted_intent_revision_ref) -> DevelopmentAcceptedIntentRevisionRowValue | None",
        "signature_inputs": [
          "capability",
          "program_ref",
          "accepted_intent_revision_ref"
        ],
        "slice3_cross_row_validation": []
      },
      {
        "absence_precedence": {
          "absent_root": "return None and execute no child SQL",
          "malformed_or_duplicate_root": "database_integrity_failure and execute no child SQL",
          "parent_validation_before_child_sql": True,
          "partial_aggregate_return": "forbidden",
          "present_root_required_child": "missing, duplicate, malformed, or mismatched exact requested revision is database_integrity_failure",
          "root_query": "work_item_head"
        },
        "aggregate_fields": [
          "work_item_head",
          "work_item_revision",
          "is_current"
        ],
        "bounded_aggregate_verification": "permitted",
        "cardinality": "root_plus_one_required_child",
        "complete_mutation_family_replay_verification": False,
        "decoded_private_value": "DevelopmentWorkItemHeadAndRevisionRead",
        "duplicate_result": "database_integrity_failure",
        "future_caller": [
          "C2B3",
          "C2B5",
          "C2B6"
        ],
        "historical_revision_allowed": True,
        "is_current_rule": "true iff both head.current_work_item_revision_ref == revision.work_item_revision_ref and head.current_work_item_revision_number == revision.work_item_revision_number",
        "later_tranche_exclusions": [
          "family graph location",
          "family completeness",
          "exact replay",
          "commit-outcome recovery",
          "mutation"
        ],
        "lookup_identity": [
          "program_ref",
          "work_item_ref",
          "work_item_revision_ref"
        ],
        "malformed_row_result": "database_integrity_failure",
        "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
        "operational_inputs": [],
        "partial_current_match_result": "database_integrity_failure",
        "private_function": "_read_development_work_item_head_and_revision_by_exact_ref",
        "query_order": [
          "work_item_head",
          "work_item_revision"
        ],
        "result_type": "DevelopmentWorkItemHeadAndRevisionRead | None",
        "role": "work_item_head_and_revision_by_exact_ref",
        "row_digest_verification": "required_before_return",
        "safe_error": "mutation_failed_or_database_integrity_failure",
        "selects": [
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "work_item_ref",
              "program_ref",
              "current_work_item_revision_ref",
              "current_work_item_revision_number",
              "head_revision",
              "work_state",
              "updated_at",
              "head_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "work_item_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "work_item_ref"
            ],
            "parameter_tuple": "(program_ref, work_item_ref)",
            "query_id": "work_item_head",
            "query_sql": "SELECT schema_id, work_item_ref, program_ref, current_work_item_revision_ref, current_work_item_revision_number, head_revision, work_state, updated_at, head_digest FROM development_work_item_heads WHERE program_ref = ? AND work_item_ref = ? LIMIT 2",
            "table": "development_work_item_heads"
          },
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "work_item_revision_ref",
              "program_ref",
              "work_item_ref",
              "work_item_revision_number",
              "work_item_revision_kind",
              "prior_work_item_revision_ref",
              "accepted_intent_revision_ref",
              "created_at",
              "work_item_revision_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "work_item_ref",
              "work_item_revision_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "work_item_ref",
              "work_item_revision_ref"
            ],
            "parameter_tuple": "(program_ref, work_item_ref, work_item_revision_ref)",
            "query_id": "work_item_revision",
            "query_sql": "SELECT schema_id, work_item_revision_ref, program_ref, work_item_ref, work_item_revision_number, work_item_revision_kind, prior_work_item_revision_ref, accepted_intent_revision_ref, created_at, work_item_revision_digest FROM development_work_item_revisions WHERE program_ref = ? AND work_item_ref = ? AND work_item_revision_ref = ? LIMIT 2",
            "table": "development_work_item_revisions"
          }
        ],
        "signature": "(capability, program_ref, work_item_ref, work_item_revision_ref) -> DevelopmentWorkItemHeadAndRevisionRead | None",
        "signature_inputs": [
          "capability",
          "program_ref",
          "work_item_ref",
          "work_item_revision_ref"
        ],
        "slice3_cross_row_validation": [
          "program and work-item identity are exact",
          "a valid historical requested revision is permitted",
          "is_current is true only when current ref and current number both equal the requested revision ref and number",
          "exactly one current ref/number match is database_integrity_failure"
        ],
        "work_state_revision_kind_relation": "not frozen by this reader contract"
      },
      {
        "absence_precedence": {
          "absent_root": "return None and execute no child SQL",
          "malformed_or_duplicate_root": "database_integrity_failure and execute no child SQL",
          "parent_validation_before_child_sql": True,
          "partial_aggregate_return": "forbidden",
          "present_root_required_child": "zero membership or any missing, duplicate, malformed, mismatched, gapped, overlapping, or duplicate membership/revision child is database_integrity_failure",
          "root_query": "program_version_root"
        },
        "aggregate_fields": [
          "program_version",
          "entries"
        ],
        "all_pages_same_capability_object_and_epoch": True,
        "bounded_aggregate_verification": "permitted",
        "cardinality": "one parent singleton plus internally completed paged membership and one required revision singleton per member",
        "complete_mutation_family_replay_verification": False,
        "continuation_exposed": False,
        "continuation_pair": [
          "last_returned_membership_ordinal",
          "last_returned_work_item_ref"
        ],
        "decoded_private_value": "DevelopmentProgramVersionMembershipRead",
        "duplicate_result": "database_integrity_failure",
        "duplicate_work_item_ref_detection_order": "when the second occurrence of a work_item_ref is observed, fail before issuing a child-revision query for that duplicate occurrence",
        "duplicate_work_item_ref_result": "database_integrity_failure",
        "duplicate_work_item_ref_scope": [
          "within one membership page",
          "across two or more membership pages",
          "across the 256/257 boundary",
          "regardless of differing membership_ordinal",
          "regardless of differing work_item_revision_ref"
        ],
        "empty_membership_permitted_program_version_kinds": [],
        "fetch_bound": 257,
        "future_caller": [
          "C2B3",
          "C2B6"
        ],
        "has_more_rule": "the 257th physical row is has_more evidence only and is re-read as the next page first row",
        "later_tranche_exclusions": [
          "family graph location",
          "family completeness",
          "exact replay",
          "commit-outcome recovery",
          "mutation"
        ],
        "lookup_identity": [
          "program_ref",
          "program_version_ref"
        ],
        "malformed_row_result": "database_integrity_failure",
        "maximum_members_failure": "mutation_failed before the bound is exceeded",
        "maximum_members_rule": "exact built-in positive int; bool and subclasses rejected before capability borrow",
        "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
        "operational_inputs": [
          "maximum_members"
        ],
        "ordering": [
          "membership_ordinal ASC",
          "work_item_ref ASC"
        ],
        "private_function": "_read_development_paged_program_version_membership",
        "query_order": [
          "program_version_root",
          "membership_first_page",
          "membership_continuation_page zero or more times",
          "membership_work_item_revision once per returned membership in membership order"
        ],
        "result_type": "DevelopmentProgramVersionMembershipRead | None",
        "return_bound_per_page": 256,
        "returned_value_is_one_completed_aggregate": True,
        "role": "paged_program_version_membership",
        "row_digest_verification": "required_before_return",
        "safe_error": "mutation_failed_or_database_integrity_failure",
        "selects": [
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "program_version_ref",
              "program_ref",
              "program_version_number",
              "program_version_kind",
              "creating_decision_ref",
              "accepted_intent_revision_ref",
              "created_at",
              "program_version_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "program_version_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "program_version_ref"
            ],
            "parameter_tuple": "(program_ref, program_version_ref)",
            "query_id": "program_version_root",
            "query_sql": "SELECT schema_id, program_version_ref, program_ref, program_version_number, program_version_kind, creating_decision_ref, accepted_intent_revision_ref, created_at, program_version_digest FROM development_program_versions WHERE program_ref = ? AND program_version_ref = ? LIMIT 2",
            "table": "development_program_versions"
          },
          {
            "cardinality_rule": "zero through 257 physical rows; the 257th row is has_more evidence only",
            "condition": "always",
            "fetch": "fetchmany(257)",
            "fields": [
              "schema_id",
              "program_ref",
              "program_version_ref",
              "work_item_ref",
              "work_item_revision_ref",
              "membership_ordinal",
              "created_at",
              "membership_digest"
            ],
            "limit": 257,
            "lookup_key": [
              "program_ref",
              "program_version_ref"
            ],
            "ordering": [
              "membership_ordinal ASC",
              "work_item_ref ASC"
            ],
            "parameter_order": [
              "program_ref",
              "program_version_ref"
            ],
            "parameter_tuple": "(program_ref, program_version_ref)",
            "query_id": "membership_first_page",
            "query_sql": "SELECT schema_id, program_ref, program_version_ref, work_item_ref, work_item_revision_ref, membership_ordinal, created_at, membership_digest FROM development_program_version_work_items WHERE program_ref = ? AND program_version_ref = ? ORDER BY membership_ordinal ASC, work_item_ref ASC LIMIT 257",
            "table": "development_program_version_work_items"
          },
          {
            "cardinality_rule": "zero through 257 physical rows; the 257th row is has_more evidence only",
            "condition": "zero or more pages while the preceding page has_more",
            "fetch": "fetchmany(257)",
            "fields": [
              "schema_id",
              "program_ref",
              "program_version_ref",
              "work_item_ref",
              "work_item_revision_ref",
              "membership_ordinal",
              "created_at",
              "membership_digest"
            ],
            "limit": 257,
            "lookup_key": [
              "program_ref",
              "program_version_ref",
              "after_membership_ordinal",
              "after_membership_ordinal",
              "after_work_item_ref"
            ],
            "ordering": [
              "membership_ordinal ASC",
              "work_item_ref ASC"
            ],
            "parameter_order": [
              "program_ref",
              "program_version_ref",
              "after_membership_ordinal",
              "after_membership_ordinal",
              "after_work_item_ref"
            ],
            "parameter_tuple": "(program_ref, program_version_ref, after_membership_ordinal, after_membership_ordinal, after_work_item_ref)",
            "query_id": "membership_continuation_page",
            "query_sql": "SELECT schema_id, program_ref, program_version_ref, work_item_ref, work_item_revision_ref, membership_ordinal, created_at, membership_digest FROM development_program_version_work_items WHERE program_ref = ? AND program_version_ref = ? AND (membership_ordinal > ? OR (membership_ordinal = ? AND work_item_ref > ?)) ORDER BY membership_ordinal ASC, work_item_ref ASC LIMIT 257",
            "table": "development_program_version_work_items"
          },
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "once for each returned membership in membership order",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "work_item_revision_ref",
              "program_ref",
              "work_item_ref",
              "work_item_revision_number",
              "work_item_revision_kind",
              "prior_work_item_revision_ref",
              "accepted_intent_revision_ref",
              "created_at",
              "work_item_revision_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "membership.work_item_ref",
              "membership.work_item_revision_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "membership.work_item_ref",
              "membership.work_item_revision_ref"
            ],
            "parameter_tuple": "(program_ref, membership.work_item_ref, membership.work_item_revision_ref)",
            "query_id": "membership_work_item_revision",
            "query_sql": "SELECT schema_id, work_item_revision_ref, program_ref, work_item_ref, work_item_revision_number, work_item_revision_kind, prior_work_item_revision_ref, accepted_intent_revision_ref, created_at, work_item_revision_digest FROM development_work_item_revisions WHERE program_ref = ? AND work_item_ref = ? AND work_item_revision_ref = ? LIMIT 2",
            "table": "development_work_item_revisions"
          }
        ],
        "signature": "(capability, program_ref, program_version_ref, maximum_members) -> DevelopmentProgramVersionMembershipRead | None",
        "signature_inputs": [
          "capability",
          "program_ref",
          "program_version_ref",
          "maximum_members"
        ],
        "slice3_cross_row_validation": [
          "strict (membership_ordinal ASC, work_item_ref ASC) order",
          "no page overlap",
          "no duplicate (membership_ordinal, work_item_ref) pair",
          "each work_item_ref appears at most once in the completed aggregate",
          "dense membership ordinals exactly 0..n-1",
          "every membership binds its exact work-item revision",
          "completed traversal before return"
        ],
        "unique_work_item_ref_rule": "Each work_item_ref appears at most once in the completed DevelopmentProgramVersionMembershipRead aggregate."
      },
      {
        "absence_precedence": {
          "absent_root": "return None and execute no child SQL",
          "malformed_or_duplicate_root": "database_integrity_failure and execute no child SQL",
          "parent_validation_before_child_sql": True,
          "partial_aggregate_return": "forbidden",
          "present_root_required_child": "not_applicable",
          "root_query": "work_spec_safe_binding"
        },
        "aggregate_fields": [],
        "bounded_aggregate_verification": "permitted",
        "cardinality": "singleton",
        "complete_mutation_family_replay_verification": False,
        "decoded_private_value": "DevelopmentWorkSpecBindingRowValue",
        "duplicate_result": "database_integrity_failure",
        "future_caller": [
          "C2B3",
          "C2B5",
          "C2B6"
        ],
        "later_tranche_exclusions": [
          "family graph location",
          "family completeness",
          "exact replay",
          "commit-outcome recovery",
          "mutation"
        ],
        "lookup_identity": [
          "program_ref",
          "program_version_ref",
          "work_item_ref",
          "work_item_revision_ref"
        ],
        "malformed_row_result": "database_integrity_failure",
        "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
        "operational_inputs": [],
        "private_function": "_read_development_work_spec_safe_binding",
        "query_order": [
          "work_spec_safe_binding"
        ],
        "result_type": "DevelopmentWorkSpecBindingRowValue | None",
        "role": "work_spec_safe_binding",
        "row_digest_verification": "required_before_return",
        "safe_error": "mutation_failed_or_database_integrity_failure",
        "selects": [
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "work_spec_ref",
              "program_ref",
              "program_version_ref",
              "accepted_intent_revision_ref",
              "work_item_ref",
              "work_item_revision_ref",
              "repository_ref",
              "base_git_object_format",
              "base_git_oid",
              "authorized_paths_json",
              "validation_requirement_ref",
              "review_requirement_ref",
              "privacy_classification",
              "work_spec_digest",
              "safe_projection_digest",
              "recorded_at",
              "work_spec_binding_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "program_version_ref",
              "work_item_ref",
              "work_item_revision_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "program_version_ref",
              "work_item_ref",
              "work_item_revision_ref"
            ],
            "parameter_tuple": "(program_ref, program_version_ref, work_item_ref, work_item_revision_ref)",
            "query_id": "work_spec_safe_binding",
            "query_sql": "SELECT schema_id, work_spec_ref, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, repository_ref, base_git_object_format, base_git_oid, authorized_paths_json, validation_requirement_ref, review_requirement_ref, privacy_classification, work_spec_digest, safe_projection_digest, recorded_at, work_spec_binding_digest FROM development_work_spec_bindings WHERE program_ref = ? AND program_version_ref = ? AND work_item_ref = ? AND work_item_revision_ref = ? LIMIT 2",
            "table": "development_work_spec_bindings"
          }
        ],
        "signature": "(capability, program_ref, program_version_ref, work_item_ref, work_item_revision_ref) -> DevelopmentWorkSpecBindingRowValue | None",
        "signature_inputs": [
          "capability",
          "program_ref",
          "program_version_ref",
          "work_item_ref",
          "work_item_revision_ref"
        ],
        "slice3_cross_row_validation": []
      },
      {
        "absence_precedence": {
          "absent_root": "return None and execute no child SQL",
          "malformed_or_duplicate_root": "database_integrity_failure and execute no child SQL",
          "parent_validation_before_child_sql": True,
          "partial_aggregate_return": "forbidden",
          "present_root_required_child": "any absent, duplicate, malformed, or relationally mismatched required child is database_integrity_failure",
          "root_query": "effect_intent_root"
        },
        "aggregate_fields": [
          "semantic_attempt",
          "effect_intent",
          "author_command",
          "attempt_fence",
          "current_effect_fence",
          "author_effect_fence"
        ],
        "authority_evaluation_query": False,
        "authority_evaluation_returned": False,
        "bounded_aggregate_verification": "permitted",
        "cardinality": "effect-intent root plus four required singleton children and one conditional singleton child",
        "complete_mutation_family_replay_verification": False,
        "decoded_refs_and_digests_rule": "The aggregate's decoded refs and digests are evidence only.",
        "decoded_private_value": "DevelopmentAttemptFenceCommandEffectRead",
        "duplicate_result": "database_integrity_failure",
        "explicit_no_proof": {
          "capsule_identity": "not proved",
          "capsule_custody": "not proved",
          "semantic_acceptance": "not proved",
          "execution_permission": "not proved"
        },
        "future_caller": [
          "C2B3",
          "C2B5",
          "C2B6"
        ],
        "granting_effect": "No field, digest, row, or successful query grants authorization, route eligibility, execution permission, semantic acceptance, capsule retrieval authority, or capsule custody.",
        "implicit_authority_locator_permitted": False,
        "later_tranche_exclusions": [
          "authority evaluation query or inference",
          "capsule retrieval",
          "cancellation-target row coherence",
          "authority verification",
          "graph completeness",
          "exact replay",
          "recovery"
        ],
        "lookup_identity": [
          "program_ref",
          "semantic_attempt_ref",
          "effect_intent_ref"
        ],
        "malformed_row_result": "database_integrity_failure",
        "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
        "operational_inputs": [],
        "private_function": "_read_development_attempt_fence_command_effect_aggregate",
        "query_order": [
          "effect_intent_root",
          "semantic_attempt",
          "author_command",
          "attempt_fence",
          "current_effect_fence",
          "author_effect_fence only when distinct, otherwise reuse current_effect_fence"
        ],
        "result_type": "DevelopmentAttemptFenceCommandEffectRead | None",
        "role": "attempt_fence_command_effect_aggregate",
        "root_disposition": "effect_intent",
        "row_digest_verification": "required_before_return",
        "safe_error": "mutation_failed_or_database_integrity_failure",
        "selects": [
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "effect_intent_ref",
              "program_ref",
              "program_version_ref",
              "semantic_attempt_ref",
              "effect_class",
              "candidate_ref",
              "command_ref",
              "basis_decision_ref",
              "cancellation_target_effect_intent_ref",
              "expected_target_effect_head_revision",
              "portable_capsule_digest",
              "created_at",
              "effect_intent_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "effect_intent_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "effect_intent_ref"
            ],
            "parameter_tuple": "(program_ref, effect_intent_ref)",
            "query_id": "effect_intent_root",
            "query_sql": "SELECT schema_id, effect_intent_ref, program_ref, program_version_ref, semantic_attempt_ref, effect_class, candidate_ref, command_ref, basis_decision_ref, cancellation_target_effect_intent_ref, expected_target_effect_head_revision, portable_capsule_digest, created_at, effect_intent_digest FROM development_effect_intents WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2",
            "table": "development_effect_intents"
          },
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "semantic_attempt_ref",
              "program_ref",
              "program_version_ref",
              "accepted_intent_revision_ref",
              "work_item_ref",
              "work_item_revision_ref",
              "attempt_number",
              "candidate_ref",
              "attempt_phase",
              "selection_decision_ref",
              "created_at",
              "semantic_attempt_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "semantic_attempt_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "semantic_attempt_ref"
            ],
            "parameter_tuple": "(program_ref, semantic_attempt_ref)",
            "query_id": "semantic_attempt",
            "query_sql": "SELECT schema_id, semantic_attempt_ref, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, attempt_number, candidate_ref, attempt_phase, selection_decision_ref, created_at, semantic_attempt_digest FROM development_semantic_attempts WHERE program_ref = ? AND semantic_attempt_ref = ? LIMIT 2",
            "table": "development_semantic_attempts"
          },
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "command_ref",
              "program_ref",
              "program_version_ref",
              "accepted_intent_revision_ref",
              "work_item_ref",
              "work_item_revision_ref",
              "semantic_attempt_ref",
              "effect_intent_ref",
              "effect_class",
              "candidate_ref",
              "repository_ref",
              "base_git_object_format",
              "base_git_oid",
              "path_ceiling_json",
              "work_spec_ref",
              "work_spec_digest",
              "standing_grant_ref",
              "standing_grant_digest",
              "attempt_authorization_ref",
              "attempt_authorization_digest",
              "effect_authorization_ref",
              "effect_authorization_digest",
              "attempt_fence_ref",
              "attempt_fence_digest",
              "effect_fence_ref",
              "effect_fence_digest",
              "global_stop_ref",
              "global_stop_version",
              "validation_requirement_ref",
              "validation_requirement_digest",
              "review_requirement_ref",
              "review_requirement_digest",
              "capsule_schema_id",
              "capsule_profile_ref",
              "effect_max_active_invocations",
              "effect_max_candidate_bytes",
              "effect_max_changed_files",
              "effect_max_cost_microusd",
              "effect_max_cpu_seconds",
              "effect_max_deliveries",
              "effect_max_deployments",
              "effect_max_local_commits",
              "effect_max_memory_bytes",
              "effect_max_merges",
              "effect_max_model_input_tokens",
              "effect_max_model_output_tokens",
              "effect_max_pull_requests",
              "effect_max_pushes",
              "effect_max_wall_seconds",
              "privacy_classification",
              "redaction_profile_ref",
              "command_digest",
              "recorded_at"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "effect_intent.command_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "effect_intent.command_ref"
            ],
            "parameter_tuple": "(program_ref, effect_intent.command_ref)",
            "query_id": "author_command",
            "query_sql": "SELECT schema_id, command_ref, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, semantic_attempt_ref, effect_intent_ref, effect_class, candidate_ref, repository_ref, base_git_object_format, base_git_oid, path_ceiling_json, work_spec_ref, work_spec_digest, standing_grant_ref, standing_grant_digest, attempt_authorization_ref, attempt_authorization_digest, effect_authorization_ref, effect_authorization_digest, attempt_fence_ref, attempt_fence_digest, effect_fence_ref, effect_fence_digest, global_stop_ref, global_stop_version, validation_requirement_ref, validation_requirement_digest, review_requirement_ref, review_requirement_digest, capsule_schema_id, capsule_profile_ref, effect_max_active_invocations, effect_max_candidate_bytes, effect_max_changed_files, effect_max_cost_microusd, effect_max_cpu_seconds, effect_max_deliveries, effect_max_deployments, effect_max_local_commits, effect_max_memory_bytes, effect_max_merges, effect_max_model_input_tokens, effect_max_model_output_tokens, effect_max_pull_requests, effect_max_pushes, effect_max_wall_seconds, privacy_classification, redaction_profile_ref, command_digest, recorded_at FROM development_author_commands WHERE program_ref = ? AND command_ref = ? LIMIT 2",
            "table": "development_author_commands"
          },
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "attempt_fence_ref",
              "parent_standing_grant_ref",
              "parent_standing_grant_digest",
              "attempt_authorization_ref",
              "attempt_authorization_digest",
              "program_ref",
              "program_version_ref",
              "accepted_intent_revision_ref",
              "work_item_ref",
              "work_item_revision_ref",
              "semantic_attempt_ref",
              "repository_ref",
              "base_git_object_format",
              "base_git_oid",
              "path_ceiling_json",
              "allowed_effect_class_mask",
              "aggregate_max_active_invocations",
              "aggregate_max_candidate_bytes",
              "aggregate_max_changed_files",
              "aggregate_max_cost_microusd",
              "aggregate_max_cpu_seconds",
              "aggregate_max_deliveries",
              "aggregate_max_deployments",
              "aggregate_max_local_commits",
              "aggregate_max_memory_bytes",
              "aggregate_max_merges",
              "aggregate_max_model_input_tokens",
              "aggregate_max_model_output_tokens",
              "aggregate_max_pull_requests",
              "aggregate_max_pushes",
              "aggregate_max_wall_seconds",
              "expires_at",
              "global_stop_ref",
              "global_stop_version",
              "attempt_fence_digest",
              "recorded_at"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "author_command.attempt_fence_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "author_command.attempt_fence_ref"
            ],
            "parameter_tuple": "(program_ref, author_command.attempt_fence_ref)",
            "query_id": "attempt_fence",
            "query_sql": "SELECT schema_id, attempt_fence_ref, parent_standing_grant_ref, parent_standing_grant_digest, attempt_authorization_ref, attempt_authorization_digest, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, semantic_attempt_ref, repository_ref, base_git_object_format, base_git_oid, path_ceiling_json, allowed_effect_class_mask, aggregate_max_active_invocations, aggregate_max_candidate_bytes, aggregate_max_changed_files, aggregate_max_cost_microusd, aggregate_max_cpu_seconds, aggregate_max_deliveries, aggregate_max_deployments, aggregate_max_local_commits, aggregate_max_memory_bytes, aggregate_max_merges, aggregate_max_model_input_tokens, aggregate_max_model_output_tokens, aggregate_max_pull_requests, aggregate_max_pushes, aggregate_max_wall_seconds, expires_at, global_stop_ref, global_stop_version, attempt_fence_digest, recorded_at FROM development_attempt_fences WHERE program_ref = ? AND attempt_fence_ref = ? LIMIT 2",
            "table": "development_attempt_fences"
          },
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "effect_fence_ref",
              "parent_standing_grant_ref",
              "parent_standing_grant_digest",
              "effect_authorization_ref",
              "effect_authorization_digest",
              "attempt_fence_ref",
              "attempt_fence_digest",
              "program_ref",
              "program_version_ref",
              "accepted_intent_revision_ref",
              "work_item_ref",
              "work_item_revision_ref",
              "semantic_attempt_ref",
              "effect_intent_ref",
              "effect_class",
              "command_ref",
              "command_digest",
              "candidate_ref",
              "repository_ref",
              "base_git_object_format",
              "base_git_oid",
              "path_ceiling_json",
              "effect_max_active_invocations",
              "effect_max_candidate_bytes",
              "effect_max_changed_files",
              "effect_max_cost_microusd",
              "effect_max_cpu_seconds",
              "effect_max_deliveries",
              "effect_max_deployments",
              "effect_max_local_commits",
              "effect_max_memory_bytes",
              "effect_max_merges",
              "effect_max_model_input_tokens",
              "effect_max_model_output_tokens",
              "effect_max_pull_requests",
              "effect_max_pushes",
              "effect_max_wall_seconds",
              "expires_at",
              "global_stop_ref",
              "global_stop_version",
              "portable_capsule_digest",
              "cancellation_target_effect_intent_ref",
              "cancellation_target_effect_fence_ref",
              "cancellation_target_effect_fence_digest",
              "effect_fence_digest",
              "recorded_at"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "effect_intent_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "effect_intent_ref"
            ],
            "parameter_tuple": "(program_ref, effect_intent_ref)",
            "query_id": "current_effect_fence",
            "query_sql": "SELECT schema_id, effect_fence_ref, parent_standing_grant_ref, parent_standing_grant_digest, effect_authorization_ref, effect_authorization_digest, attempt_fence_ref, attempt_fence_digest, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, semantic_attempt_ref, effect_intent_ref, effect_class, command_ref, command_digest, candidate_ref, repository_ref, base_git_object_format, base_git_oid, path_ceiling_json, effect_max_active_invocations, effect_max_candidate_bytes, effect_max_changed_files, effect_max_cost_microusd, effect_max_cpu_seconds, effect_max_deliveries, effect_max_deployments, effect_max_local_commits, effect_max_memory_bytes, effect_max_merges, effect_max_model_input_tokens, effect_max_model_output_tokens, effect_max_pull_requests, effect_max_pushes, effect_max_wall_seconds, expires_at, global_stop_ref, global_stop_version, portable_capsule_digest, cancellation_target_effect_intent_ref, cancellation_target_effect_fence_ref, cancellation_target_effect_fence_digest, effect_fence_digest, recorded_at FROM development_effect_fences WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2",
            "table": "development_effect_fences"
          },
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "only when author_command.effect_fence_ref differs from current_effect_fence.effect_fence_ref; otherwise reuse current_effect_fence by identity",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "effect_fence_ref",
              "parent_standing_grant_ref",
              "parent_standing_grant_digest",
              "effect_authorization_ref",
              "effect_authorization_digest",
              "attempt_fence_ref",
              "attempt_fence_digest",
              "program_ref",
              "program_version_ref",
              "accepted_intent_revision_ref",
              "work_item_ref",
              "work_item_revision_ref",
              "semantic_attempt_ref",
              "effect_intent_ref",
              "effect_class",
              "command_ref",
              "command_digest",
              "candidate_ref",
              "repository_ref",
              "base_git_object_format",
              "base_git_oid",
              "path_ceiling_json",
              "effect_max_active_invocations",
              "effect_max_candidate_bytes",
              "effect_max_changed_files",
              "effect_max_cost_microusd",
              "effect_max_cpu_seconds",
              "effect_max_deliveries",
              "effect_max_deployments",
              "effect_max_local_commits",
              "effect_max_memory_bytes",
              "effect_max_merges",
              "effect_max_model_input_tokens",
              "effect_max_model_output_tokens",
              "effect_max_pull_requests",
              "effect_max_pushes",
              "effect_max_wall_seconds",
              "expires_at",
              "global_stop_ref",
              "global_stop_version",
              "portable_capsule_digest",
              "cancellation_target_effect_intent_ref",
              "cancellation_target_effect_fence_ref",
              "cancellation_target_effect_fence_digest",
              "effect_fence_digest",
              "recorded_at"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "author_command.effect_fence_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "author_command.effect_fence_ref"
            ],
            "parameter_tuple": "(program_ref, author_command.effect_fence_ref)",
            "query_id": "author_effect_fence",
            "query_sql": "SELECT schema_id, effect_fence_ref, parent_standing_grant_ref, parent_standing_grant_digest, effect_authorization_ref, effect_authorization_digest, attempt_fence_ref, attempt_fence_digest, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, semantic_attempt_ref, effect_intent_ref, effect_class, command_ref, command_digest, candidate_ref, repository_ref, base_git_object_format, base_git_oid, path_ceiling_json, effect_max_active_invocations, effect_max_candidate_bytes, effect_max_changed_files, effect_max_cost_microusd, effect_max_cpu_seconds, effect_max_deliveries, effect_max_deployments, effect_max_local_commits, effect_max_memory_bytes, effect_max_merges, effect_max_model_input_tokens, effect_max_model_output_tokens, effect_max_pull_requests, effect_max_pushes, effect_max_wall_seconds, expires_at, global_stop_ref, global_stop_version, portable_capsule_digest, cancellation_target_effect_intent_ref, cancellation_target_effect_fence_ref, cancellation_target_effect_fence_digest, effect_fence_digest, recorded_at FROM development_effect_fences WHERE program_ref = ? AND effect_fence_ref = ? LIMIT 2",
            "table": "development_effect_fences"
          }
        ],
        "signature": "(capability, program_ref, semantic_attempt_ref, effect_intent_ref) -> DevelopmentAttemptFenceCommandEffectRead | None",
        "signature_inputs": [
          "capability",
          "program_ref",
          "semantic_attempt_ref",
          "effect_intent_ref"
        ],
        "slice3_cross_row_validation": [
          "program identity",
          "program version",
          "accepted-intent revision",
          "work item and revision",
          "semantic attempt",
          "candidate",
          "repository and base OID",
          "global-stop ref and version",
          "intent-to-command ref",
          "attempt-fence ref and digest",
          "current-fence effect-intent ref",
          "current-fence command ref and digest",
          "author-fence ref and digest from the command",
          "effect ceilings are no wider than attempt ceilings",
          "author-candidate current and author fences are the same exact row",
          "bound-effect current and author fences may differ but both cohere with the originating author command"
        ]
      },
      {
        "absence_precedence": {
          "absent_root": "return None and execute no child SQL",
          "malformed_or_duplicate_root": "database_integrity_failure and execute no child SQL",
          "parent_validation_before_child_sql": True,
          "partial_aggregate_return": "forbidden",
          "present_root_required_child": "not_applicable",
          "root_query": "authority_evaluation"
        },
        "aggregate_fields": [],
        "authority_boundary": {
          "evidence_only": "The decoded authority-evaluation row is evidence only.",
          "executable_permission": "The row confers no executable permission.",
          "verified_state": "A verified state does not itself authorize a worker, adapter, route, mutation, retry, replay, or external effect.",
          "reader_authority": "The reader does not issue, renew, reinterpret, or consume executable authority."
        },
        "bounded_aggregate_verification": "permitted",
        "cardinality": "singleton",
        "complete_mutation_family_replay_verification": False,
        "decoded_private_value": "DevelopmentAuthorityEvaluationRowValue",
        "duplicate_result": "database_integrity_failure",
        "future_caller": [
          "C2B3",
          "C2B5"
        ],
        "later_tranche_exclusions": [
          "family graph location",
          "family completeness",
          "exact replay",
          "commit-outcome recovery",
          "mutation"
        ],
        "lookup_identity": [
          "program_ref",
          "authority_evaluation_ref"
        ],
        "malformed_row_result": "database_integrity_failure",
        "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
        "operational_inputs": [],
        "private_function": "_read_development_authority_evaluation_by_exact_ref",
        "query_order": [
          "authority_evaluation"
        ],
        "result_type": "DevelopmentAuthorityEvaluationRowValue | None",
        "role": "authority_evaluation_by_exact_ref",
        "row_digest_verification": "required_before_return",
        "safe_error": "mutation_failed_or_database_integrity_failure",
        "same_subject_multiple_rows_permitted": True,
        "selection_rule": "exact program_ref and authority_evaluation_ref only",
        "selects": [
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "authority_evaluation_ref",
              "program_ref",
              "evaluation_scope",
              "evaluation_subject_ref",
              "semantic_attempt_ref",
              "effect_intent_ref",
              "authority_ref",
              "authority_digest",
              "authority_state",
              "reason_code",
              "expires_at",
              "evaluated_at",
              "authority_evaluation_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "authority_evaluation_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "authority_evaluation_ref"
            ],
            "parameter_tuple": "(program_ref, authority_evaluation_ref)",
            "query_id": "authority_evaluation",
            "query_sql": "SELECT schema_id, authority_evaluation_ref, program_ref, evaluation_scope, evaluation_subject_ref, semantic_attempt_ref, effect_intent_ref, authority_ref, authority_digest, authority_state, reason_code, expires_at, evaluated_at, authority_evaluation_digest FROM development_authority_evaluations WHERE program_ref = ? AND authority_evaluation_ref = ? LIMIT 2",
            "table": "development_authority_evaluations"
          }
        ],
        "signature": "(capability, program_ref, authority_evaluation_ref) -> DevelopmentAuthorityEvaluationRowValue | None",
        "signature_inputs": [
          "capability",
          "program_ref",
          "authority_evaluation_ref"
        ],
        "slice3_cross_row_validation": [],
        "sole_authority_evaluation_reader": True
      },
      {
        "absence_precedence": {
          "absent_root": "return None and execute no child SQL",
          "malformed_or_duplicate_root": "database_integrity_failure and execute no child SQL",
          "parent_validation_before_child_sql": True,
          "partial_aggregate_return": "forbidden",
          "present_root_required_child": "not_applicable",
          "root_query": "effect_head"
        },
        "aggregate_fields": [],
        "bounded_aggregate_verification": "permitted",
        "cardinality": "singleton",
        "complete_mutation_family_replay_verification": False,
        "decoded_private_value": "DevelopmentEffectHeadRowValue",
        "duplicate_result": "database_integrity_failure",
        "future_caller": [
          "C2B3",
          "C2B5"
        ],
        "later_tranche_exclusions": [
          "current effect-fence fetch or coherence",
          "cancellation-target graph",
          "effect family completeness"
        ],
        "lookup_identity": [
          "program_ref",
          "effect_intent_ref"
        ],
        "malformed_row_result": "database_integrity_failure",
        "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
        "operational_inputs": [],
        "private_function": "_read_development_effect_head",
        "query_order": [
          "effect_head"
        ],
        "result_type": "DevelopmentEffectHeadRowValue | None",
        "role": "effect_head",
        "row_digest_verification": "required_before_return",
        "safe_error": "mutation_failed_or_database_integrity_failure",
        "selects": [
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "effect_intent_ref",
              "program_ref",
              "current_effect_fence_ref",
              "head_revision",
              "effect_state",
              "cancellation_effect_intent_ref",
              "updated_at",
              "head_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "effect_intent_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "effect_intent_ref"
            ],
            "parameter_tuple": "(program_ref, effect_intent_ref)",
            "query_id": "effect_head",
            "query_sql": "SELECT schema_id, effect_intent_ref, program_ref, current_effect_fence_ref, head_revision, effect_state, cancellation_effect_intent_ref, updated_at, head_digest FROM development_effect_heads WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2",
            "table": "development_effect_heads"
          }
        ],
        "signature": "(capability, program_ref, effect_intent_ref) -> DevelopmentEffectHeadRowValue | None",
        "signature_inputs": [
          "capability",
          "program_ref",
          "effect_intent_ref"
        ],
        "singleton_only": True,
        "slice3_cross_row_validation": [
          "row-local digest",
          "row-local cancellation nullability"
        ]
      },
      {
        "absence_precedence": {
          "absent_root": "return None and execute no child SQL",
          "malformed_or_duplicate_root": "database_integrity_failure and execute no child SQL",
          "parent_validation_before_child_sql": True,
          "partial_aggregate_return": "forbidden",
          "present_root_required_child": "missing, duplicate, malformed, or mismatched current delivery attempt is database_integrity_failure",
          "root_query": "delivery_head"
        },
        "aggregate_fields": [
          "delivery_head",
          "current_delivery_attempt"
        ],
        "bounded_aggregate_verification": "permitted",
        "cardinality": "root_plus_one_required_child",
        "complete_mutation_family_replay_verification": False,
        "decoded_private_value": "DevelopmentDeliveryHeadAndCurrentAttemptRead",
        "duplicate_result": "database_integrity_failure",
        "future_caller": [
          "C2B3",
          "C2B5"
        ],
        "later_tranche_exclusions": [
          "delivery_number == head_revision + 1 inference",
          "delivery-state to delivery-kind mapping",
          "family graph completeness",
          "exact replay",
          "recovery"
        ],
        "lookup_identity": [
          "program_ref",
          "effect_intent_ref"
        ],
        "malformed_row_result": "database_integrity_failure",
        "nominal_capability_requirement": "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
        "operational_inputs": [],
        "private_function": "_read_development_delivery_head",
        "query_order": [
          "delivery_head",
          "current_delivery_attempt"
        ],
        "result_type": "DevelopmentDeliveryHeadAndCurrentAttemptRead | None",
        "role": "delivery_head",
        "row_digest_verification": "required_before_return",
        "safe_error": "mutation_failed_or_database_integrity_failure",
        "selects": [
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "effect_intent_ref",
              "program_ref",
              "current_delivery_attempt_ref",
              "head_revision",
              "delivery_state",
              "updated_at",
              "head_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "effect_intent_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "effect_intent_ref"
            ],
            "parameter_tuple": "(program_ref, effect_intent_ref)",
            "query_id": "delivery_head",
            "query_sql": "SELECT schema_id, effect_intent_ref, program_ref, current_delivery_attempt_ref, head_revision, delivery_state, updated_at, head_digest FROM development_delivery_heads WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2",
            "table": "development_delivery_heads"
          },
          {
            "cardinality_rule": "zero rows permitted only under the enclosing root/child rule; one row succeeds; two rows are database_integrity_failure",
            "condition": "always",
            "fetch": "fetchmany(2)",
            "fields": [
              "schema_id",
              "delivery_attempt_ref",
              "program_ref",
              "program_version_ref",
              "command_ref",
              "command_digest",
              "semantic_attempt_ref",
              "effect_intent_ref",
              "attempt_fence_ref",
              "attempt_fence_digest",
              "effect_fence_ref",
              "effect_fence_digest",
              "adapter_kind",
              "adapter_safe_correlation_ref",
              "delivery_envelope_digest",
              "delivery_kind",
              "delivery_number",
              "predecessor_delivery_attempt_ref",
              "basis_decision_ref",
              "recorded_at",
              "delivery_attempt_digest"
            ],
            "limit": 2,
            "lookup_key": [
              "program_ref",
              "effect_intent_ref",
              "delivery_head.current_delivery_attempt_ref"
            ],
            "ordering": None,
            "parameter_order": [
              "program_ref",
              "effect_intent_ref",
              "delivery_head.current_delivery_attempt_ref"
            ],
            "parameter_tuple": "(program_ref, effect_intent_ref, delivery_head.current_delivery_attempt_ref)",
            "query_id": "current_delivery_attempt",
            "query_sql": "SELECT schema_id, delivery_attempt_ref, program_ref, program_version_ref, command_ref, command_digest, semantic_attempt_ref, effect_intent_ref, attempt_fence_ref, attempt_fence_digest, effect_fence_ref, effect_fence_digest, adapter_kind, adapter_safe_correlation_ref, delivery_envelope_digest, delivery_kind, delivery_number, predecessor_delivery_attempt_ref, basis_decision_ref, recorded_at, delivery_attempt_digest FROM development_delivery_attempts WHERE program_ref = ? AND effect_intent_ref = ? AND delivery_attempt_ref = ? LIMIT 2",
            "table": "development_delivery_attempts"
          }
        ],
        "signature": "(capability, program_ref, effect_intent_ref) -> DevelopmentDeliveryHeadAndCurrentAttemptRead | None",
        "signature_inputs": [
          "capability",
          "program_ref",
          "effect_intent_ref"
        ],
        "slice3_cross_row_validation": [
          "exact program identity",
          "exact effect-intent identity",
          "current delivery-attempt ref equality"
        ]
      }
    ],
    "validation_and_audit_plan": {
      "eight_file_compatibility_group": {
        "comparison_evidence": {
          "passed": 315,
          "skipped": 0,
          "emitted_warnings": 0
        },
        "evidence_classification": "comparison evidence only; not a durable compatibility contract",
        "paths": [
          "tests/test_c2b2_development_program_row_values.py",
          "tests/test_c2b2_development_effect_row_values.py",
          "tests/test_c2b2_development_decision_row_values.py",
          "tests/test_c2b2_development_row_value_boundaries.py",
          "tests/test_b3b2b_select_readers.py",
          "tests/test_b3c2_transition_event_readers.py",
          "tests/test_b4a_global_stop_readers.py",
          "tests/test_b3c1b_rollback_only_writer_fencing.py"
        ],
        "requirements": [
          "all tests pass",
          "zero skipped tests",
          "report every warning actually emitted"
        ],
        "warning_policy": {
          "unqualified_w_error": False,
          "warning_filters": [],
          "pytest_warning_configuration": []
        }
      },
      "focused_validation": [
        "dedicated field-level oracle under -W error",
        "C2B owner and field-level contract under -W error",
        "future Slice-3 reader-contract tests under -W error",
        "future Slice-3 reader-execution tests under -W error",
        "current-status and authority regression under -W error",
        "migration-0002 preservation",
        "post-hygiene strict SQLite gate under -W error",
        "eight-file Slice-2 and existing-reader compatibility group without an unqualified -W error",
        "full tests collection",
        "full Coordinator suite without an unqualified -W error"
      ],
      "fresh_independent_audit": [
        "exact two-path provenance",
        "semantic diff limited to reader contract and mapping fields",
        "all twelve signatures and result types",
        "all literal SQL and parameter/query order",
        "bidirectional table-role mapping",
        "role-9 authority removal and prohibited locator matrix",
        "role-10 exact-ref authority",
        "role-6 historical/current semantics",
        "role-7 parent, completion, bound, empty, and pagination semantics",
        "missing-root and child precedence",
        "receipt graph non-completeness",
        "capability and error ordering",
        "exact future 23-path allowlist",
        "oracle literal independence and counterfactual discrimination",
        "full validation",
        "continued reader nonimplementation"
      ],
      "full_suite_warning_policy": {
        "unqualified_w_error": False,
        "skipped": 0,
        "resource_warning_count": 0,
        "pytest_unraisable_exception_warning_count": 0,
        "permitted_warning": "only the three previously classified Python 3.13 multithreaded-fork DeprecationWarnings, if they recur",
        "new_warning": "none"
      },
      "strict_validation_groups": [
        "dedicated field-level oracle",
        "oracle plus C2B0 owner contract",
        "future Slice-3 reader-contract tests",
        "future Slice-3 reader-execution tests",
        "changed architecture, status, and non-authority tests",
        "completed five-file SQLite-hygiene gate"
      ]
    },
    "workstream_identity": "COORDINATOR_C2B2_SLICE_3_PRIVATE_READER_CONTRACT_RESET"
  },
  "receipt_envelope": {
    "column_count": 19,
    "common_required_fields": [
      "schema_id",
      "mutation_ref",
      "mutation_family",
      "command_schema_id",
      "command_digest",
      "program_ref",
      "result_class",
      "result_projection_digest",
      "mutation_graph_digest",
      "outcome",
      "committed_at"
    ],
    "family_matrix": [
      {
        "command_schema_id": "governed-execution.nwp-initialize-development-program-command.v1",
        "family": "initialize_development_program",
        "required_non_null_result_fields": [
          "decision_ref",
          "result_program_version_ref",
          "result_decision_ref"
        ],
        "required_null_result_fields": [
          "result_semantic_attempt_ref",
          "result_effect_intent_ref",
          "result_effect_fence_ref",
          "result_delivery_attempt_ref",
          "result_observation_ref"
        ],
        "result_class": "development_program_initialized",
        "result_identity_keys": [
          "schema_id",
          "program_ref",
          "decision_ref",
          "result_program_version_ref",
          "result_decision_ref"
        ],
        "result_projection_digest_domain": "governed-execution.nwp-initialize-development-program-result.v1.identity",
        "result_projection_schema_id": "governed-execution.nwp-initialize-development-program-result.v1",
        "sql_branch": "(mutation_family='initialize_development_program' AND command_schema_id='governed-execution.nwp-initialize-development-program-command.v1' AND result_class='development_program_initialized' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NULL AND result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND result_delivery_attempt_ref IS NULL AND result_observation_ref IS NULL AND result_decision_ref IS NOT NULL AND result_decision_ref=decision_ref)"
      },
      {
        "command_schema_id": "governed-execution.nwp-establish-development-author-effect-intent-command.v1",
        "family": "establish_development_author_effect_intent",
        "required_non_null_result_fields": [
          "decision_ref",
          "result_program_version_ref",
          "result_semantic_attempt_ref",
          "result_effect_intent_ref",
          "result_effect_fence_ref",
          "result_delivery_attempt_ref"
        ],
        "required_null_result_fields": [
          "result_observation_ref",
          "result_decision_ref"
        ],
        "result_class": "development_author_effect_intent_established",
        "result_identity_keys": [
          "schema_id",
          "program_ref",
          "decision_ref",
          "result_program_version_ref",
          "result_semantic_attempt_ref",
          "result_effect_intent_ref",
          "result_effect_fence_ref",
          "result_delivery_attempt_ref"
        ],
        "result_projection_digest_domain": "governed-execution.nwp-establish-development-author-effect-intent-result.v1.identity",
        "result_projection_schema_id": "governed-execution.nwp-establish-development-author-effect-intent-result.v1",
        "sql_branch": "(mutation_family='establish_development_author_effect_intent' AND command_schema_id='governed-execution.nwp-establish-development-author-effect-intent-command.v1' AND result_class='development_author_effect_intent_established' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NOT NULL AND result_effect_intent_ref IS NOT NULL AND result_effect_fence_ref IS NOT NULL AND result_delivery_attempt_ref IS NOT NULL AND result_observation_ref IS NULL AND result_decision_ref IS NULL)"
      },
      {
        "command_schema_id": "governed-execution.nwp-establish-development-bound-effect-intent-command.v1",
        "family": "establish_development_bound_effect_intent",
        "required_non_null_result_fields": [
          "decision_ref",
          "result_program_version_ref",
          "result_semantic_attempt_ref",
          "result_effect_intent_ref",
          "result_effect_fence_ref",
          "result_delivery_attempt_ref"
        ],
        "required_null_result_fields": [
          "result_observation_ref",
          "result_decision_ref"
        ],
        "result_class": "development_bound_effect_intent_established",
        "result_identity_keys": [
          "schema_id",
          "program_ref",
          "decision_ref",
          "result_program_version_ref",
          "result_semantic_attempt_ref",
          "result_effect_intent_ref",
          "result_effect_fence_ref",
          "result_delivery_attempt_ref"
        ],
        "result_projection_digest_domain": "governed-execution.nwp-establish-development-bound-effect-intent-result.v1.identity",
        "result_projection_schema_id": "governed-execution.nwp-establish-development-bound-effect-intent-result.v1",
        "sql_branch": "(mutation_family='establish_development_bound_effect_intent' AND command_schema_id='governed-execution.nwp-establish-development-bound-effect-intent-command.v1' AND result_class='development_bound_effect_intent_established' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NOT NULL AND result_effect_intent_ref IS NOT NULL AND result_effect_fence_ref IS NOT NULL AND result_delivery_attempt_ref IS NOT NULL AND result_observation_ref IS NULL AND result_decision_ref IS NULL)"
      },
      {
        "command_schema_id": "governed-execution.nwp-ingest-development-source-observation-command.v1",
        "family": "ingest_development_source_observation",
        "required_non_null_result_fields": [
          "result_observation_ref"
        ],
        "required_null_result_fields": [
          "decision_ref",
          "result_program_version_ref",
          "result_semantic_attempt_ref",
          "result_effect_intent_ref",
          "result_effect_fence_ref",
          "result_delivery_attempt_ref",
          "result_decision_ref"
        ],
        "result_class": "development_source_observation_ingested",
        "result_identity_keys": [
          "schema_id",
          "program_ref",
          "result_observation_ref"
        ],
        "result_projection_digest_domain": "governed-execution.nwp-ingest-development-source-observation-result.v1.identity",
        "result_projection_schema_id": "governed-execution.nwp-ingest-development-source-observation-result.v1",
        "sql_branch": "(mutation_family='ingest_development_source_observation' AND command_schema_id='governed-execution.nwp-ingest-development-source-observation-command.v1' AND result_class='development_source_observation_ingested' AND decision_ref IS NULL AND result_program_version_ref IS NULL AND result_semantic_attempt_ref IS NULL AND result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND result_delivery_attempt_ref IS NULL AND result_observation_ref IS NOT NULL AND result_decision_ref IS NULL)"
      },
      {
        "command_schema_id": "governed-execution.nwp-record-development-progression-decision-command.v1",
        "family": "record_development_progression_decision",
        "required_non_null_result_fields": [
          "decision_ref",
          "result_program_version_ref",
          "result_decision_ref"
        ],
        "required_null_result_fields": [
          "result_semantic_attempt_ref",
          "result_effect_intent_ref",
          "result_effect_fence_ref",
          "result_delivery_attempt_ref",
          "result_observation_ref"
        ],
        "result_class": "development_progression_decision_recorded",
        "result_identity_keys": [
          "schema_id",
          "program_ref",
          "decision_ref",
          "result_program_version_ref",
          "result_decision_ref"
        ],
        "result_projection_digest_domain": "governed-execution.nwp-record-development-progression-decision-result.v1.identity",
        "result_projection_schema_id": "governed-execution.nwp-record-development-progression-decision-result.v1",
        "sql_branch": "(mutation_family='record_development_progression_decision' AND command_schema_id='governed-execution.nwp-record-development-progression-decision-command.v1' AND result_class='development_progression_decision_recorded' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NULL AND result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND result_delivery_attempt_ref IS NULL AND result_observation_ref IS NULL AND result_decision_ref IS NOT NULL AND result_decision_ref=decision_ref)"
      }
    ],
    "ordered_columns": [
      "schema_id",
      "mutation_ref",
      "mutation_family",
      "command_schema_id",
      "command_digest",
      "program_ref",
      "decision_ref",
      "result_program_version_ref",
      "result_semantic_attempt_ref",
      "result_effect_intent_ref",
      "result_effect_fence_ref",
      "result_delivery_attempt_ref",
      "result_observation_ref",
      "result_decision_ref",
      "result_class",
      "result_projection_digest",
      "mutation_graph_digest",
      "outcome",
      "committed_at"
    ],
    "outcomes": [
      "committed"
    ],
    "safe_contradiction_result": "database_integrity_failure"
  },
  "receipt_scalar_coherence": {
    "establish_development_author_effect_intent": {
      "decision_ref": "exact_basis_decision",
      "result_decision_ref": "null",
      "result_delivery_attempt_ref": "exact_created_initial_delivery",
      "result_effect_fence_ref": "exact_created_author_effect_fence",
      "result_effect_intent_ref": "exact_created_author_effect_intent",
      "result_observation_ref": "null",
      "result_program_version_ref": "equals_effect_intent.program_version_ref_and_exact_basis_decision_bound_program_version_ref",
      "result_semantic_attempt_ref": "exact_created_attempt"
    },
    "establish_development_bound_effect_intent": {
      "decision_ref": "exact_basis_decision",
      "result_decision_ref": "null",
      "result_delivery_attempt_ref": "exact_created_initial_delivery",
      "result_effect_fence_ref": "exact_created_bound_effect_fence",
      "result_effect_intent_ref": "exact_created_bound_effect_intent",
      "result_observation_ref": "null",
      "result_program_version_ref": "equals_effect_intent.program_version_ref_and_exact_basis_decision_bound_program_version_ref",
      "result_semantic_attempt_ref": "exact_existing_attempt"
    },
    "every_family": {
      "contradiction_result": "database_integrity_failure",
      "projection_schema_domain_identity_from_receipt_family_matrix": True,
      "row_to_result_equality": "exact",
      "self_digest_exclusions": [
        "result_projection_digest"
      ]
    },
    "ingest_development_source_observation": {
      "all_decision_version_attempt_effect_fence_delivery_result_refs": "null",
      "observation_parent_graph_owner": "migration_0003",
      "result_observation_ref": "exact_safe_observation_result_ref"
    },
    "initialize_development_program": {
      "all_effect_attempt_delivery_observation_result_refs": "null",
      "decision_ref": "exact_initialize_decision",
      "result_decision_ref": "equals_decision_ref",
      "result_program_version_ref": "equals_decision.resulting_program_version_ref_and_created_program_version_ref"
    },
    "record_development_progression_decision": {
      "advancing_kinds_use_new_resulting_version": [
        "accept",
        "repair",
        "replan",
        "terminal_reject",
        "block"
      ],
      "all_attempt_effect_fence_delivery_observation_result_refs": "null",
      "decision_ref": "exact_committed_decision",
      "non_advancing_kinds_use_unchanged_basis_version": [
        "redeliver",
        "cancel"
      ],
      "result_decision_ref": "equals_decision_ref",
      "result_program_version_ref": "decision.resulting_program_version_ref_when_non_null_else_decision.basis_program_version_ref"
    }
  },
  "scalar_and_compound_contracts": {
    "closed_state_vocabularies": {
      "adapter_kind": [
        "direct_local_bootstrap",
        "execution_substrate"
      ],
      "attempt_phase": [
        "established"
      ],
      "authority_state": [
        "pending",
        "verified",
        "blocked",
        "stale",
        "revoked",
        "expired"
      ],
      "command_schema_id": [
        "governed-execution.nwp-initialize-development-program-command.v1",
        "governed-execution.nwp-establish-development-author-effect-intent-command.v1",
        "governed-execution.nwp-establish-development-bound-effect-intent-command.v1",
        "governed-execution.nwp-ingest-development-source-observation-command.v1",
        "governed-execution.nwp-record-development-progression-decision-command.v1"
      ],
      "decision_kind": [
        "initialize",
        "accept",
        "repair",
        "replan",
        "terminal_reject",
        "block",
        "redeliver",
        "cancel"
      ],
      "decision_variant": [
        "program_genesis",
        "candidate_acceptance",
        "candidate_repair",
        "program_replan",
        "attempt_selecting_replan",
        "program_terminal_reject",
        "program_block",
        "productive_redelivery",
        "cancellation_redelivery",
        "effect_cancellation"
      ],
      "delivery_kind": [
        "initial",
        "redelivery"
      ],
      "delivery_state": [
        "planned",
        "submitted",
        "outcome_unknown",
        "acknowledged",
        "rejected",
        "completed"
      ],
      "effect_class": [
        "author_candidate",
        "cancel_effect",
        "local_git_commit",
        "review_candidate",
        "validate_candidate"
      ],
      "effect_state": [
        "ready_for_delivery",
        "delivery_pending",
        "delivery_outcome_unknown",
        "observed",
        "cancellation_effect_established",
        "terminal"
      ],
      "evaluation_scope": [
        "attempt",
        "effect"
      ],
      "mutation_family": [
        "initialize_development_program",
        "establish_development_author_effect_intent",
        "establish_development_bound_effect_intent",
        "ingest_development_source_observation",
        "record_development_progression_decision"
      ],
      "program_state": [
        "active",
        "accepted",
        "terminal_rejected",
        "blocked"
      ],
      "program_version_kind": [
        "initial",
        "accepted",
        "repair",
        "replan",
        "terminal_rejected",
        "blocked"
      ],
      "receipt_outcome": [
        "committed"
      ],
      "result_class": [
        "development_program_initialized",
        "development_author_effect_intent_established",
        "development_bound_effect_intent_established",
        "development_source_observation_ingested",
        "development_progression_decision_recorded"
      ],
      "revision_edge_kind": [
        "accepted_intent_supersedes",
        "work_item_supersedes",
        "work_item_split",
        "work_item_merge"
      ],
      "target_effect_class": [
        "author_candidate",
        "cancel_effect",
        "local_git_commit",
        "review_candidate",
        "validate_candidate"
      ],
      "work_revision_kind": [
        "initial",
        "replan"
      ],
      "work_spec_privacy_classification": [
        "private_work_spec"
      ],
      "work_state": [
        "planned",
        "active",
        "accepted",
        "repair_required",
        "terminal_rejected",
        "blocked"
      ],
      "worker_command_privacy_classification": [
        "private_source_change"
      ]
    },
    "compound_value_encodings": {
      "CeilingsV1": {
        "encoding": "fifteen flattened nonnegative ANY/integer columns",
        "fields": [
          "max_active_invocations",
          "max_candidate_bytes",
          "max_changed_files",
          "max_cost_microusd",
          "max_cpu_seconds",
          "max_deliveries",
          "max_deployments",
          "max_local_commits",
          "max_memory_bytes",
          "max_merges",
          "max_model_input_tokens",
          "max_model_output_tokens",
          "max_pull_requests",
          "max_pushes",
          "max_wall_seconds"
        ]
      },
      "allowed_effect_classes": {
        "bit_order": [
          "author_candidate",
          "cancel_effect",
          "local_git_commit",
          "review_candidate",
          "validate_candidate"
        ],
        "encoding": "closed five-bit integer mask"
      },
      "path_ceiling": {
        "encoding": "exact canonical JSON text",
        "paths": [
          ".docs/system_overview/hybrid_integration_architecture_adr.md",
          "PLANS.md",
          "docs_contract_test.go"
        ],
        "value": "[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]"
      }
    },
    "digest_predicates": {
      "git_sha1_oid": "typeof(x)='text' AND length(x)=40 AND x=lower(x) AND x NOT GLOB '*[^0-9a-f]*'",
      "sha256": "typeof(x)='text' AND length(x)=64 AND x=lower(x) AND x NOT GLOB '*[^0-9a-f]*'"
    },
    "nullable_pair_conventions": {
      "enforcement": "column checks plus named bidirectional table checks",
      "rule": "every declared ref/digest or ref/version group is both-null or both-present"
    },
    "reason_code_predicate": "typeof(x)='text' AND length(x) BETWEEN 1 AND 96 AND substr(x,1,1) GLOB '[a-z]' AND x NOT GLOB '*[^a-z0-9_.-]*'",
    "safe_ref_predicate": "typeof(x)='text' AND length(x) BETWEEN 1 AND 96 AND substr(x,1,1) GLOB '[0-9A-Za-z]' AND x NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(x,1,instr(x,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
    "scalar_conventions": {
      "empty_string_required_fields": "rejected",
      "git_sha1_oid_predicate": "typeof(x)='text' AND length(x)=40 AND x=lower(x) AND x NOT GLOB '*[^0-9a-f]*'",
      "maximum_safe_ref_length": 96,
      "nonnegative_integer_predicate": "typeof(x)='integer' AND x>=0",
      "positive_integer_predicate": "typeof(x)='integer' AND x>=1",
      "python_boundary": "exact built-in types; bool rejected when int required",
      "reason_code_predicate": "typeof(x)='text' AND length(x) BETWEEN 1 AND 96 AND substr(x,1,1) GLOB '[a-z]' AND x NOT GLOB '*[^a-z0-9_.-]*'",
      "safe_ref_predicate": "typeof(x)='text' AND length(x) BETWEEN 1 AND 96 AND substr(x,1,1) GLOB '[0-9A-Za-z]' AND x NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(x,1,instr(x,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
      "sha256_predicate": "typeof(x)='text' AND length(x)=64 AND x=lower(x) AND x NOT GLOB '*[^0-9a-f]*'",
      "sqlite_declaration_type": "ANY",
      "tables_strict": True,
      "timestamp_predicate": "typeof(x)='text' AND length(x)=20 AND x GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(x,1,4) BETWEEN '0001' AND '9999' AND substr(x,6,2) BETWEEN '01' AND '12' AND substr(x,9,2) BETWEEN '01' AND '31' AND substr(x,12,2) BETWEEN '00' AND '23' AND substr(x,15,2) BETWEEN '00' AND '59' AND substr(x,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',x) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',x)=x"
    },
    "timestamp_predicate": "typeof(x)='text' AND length(x)=20 AND x GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(x,1,4) BETWEEN '0001' AND '9999' AND substr(x,6,2) BETWEEN '01' AND '12' AND substr(x,9,2) BETWEEN '01' AND '31' AND substr(x,12,2) BETWEEN '00' AND '23' AND substr(x,15,2) BETWEEN '00' AND '59' AND substr(x,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',x) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',x)=x"
  },
  "sql_core": {
    "application_generation": 2,
    "compatibility": [
      2,
      2
    ],
    "current_migration_0001_changed": False,
    "deferred_foreign_key_count": 6,
    "destructive": False,
    "explicit_index_count": 1,
    "foreign_key_count": 87,
    "immutable_table_count": 15,
    "immutable_table_names": [
      "development_program_versions",
      "development_accepted_intent_revisions",
      "development_work_item_revisions",
      "development_program_version_work_items",
      "development_revision_edges",
      "development_work_spec_bindings",
      "development_semantic_attempts",
      "development_attempt_fences",
      "development_authority_evaluations",
      "development_effect_intents",
      "development_effect_fences",
      "development_author_commands",
      "development_delivery_attempts",
      "development_decisions",
      "development_mutation_receipts"
    ],
    "immutable_trigger_count": 30,
    "migration_0003_present": False,
    "migration_catalog_target": [
      {
        "changed": False,
        "compatibility": [
          1,
          1
        ],
        "migration_id": "0001_initial",
        "sequence": 1
      },
      {
        "compatibility": [
          2,
          2
        ],
        "destructive": False,
        "migration_id": "0002_development_program_and_effect_state",
        "sequence": 2
      }
    ],
    "migration_id": "0002_development_program_and_effect_state",
    "mutable_table_count": 4,
    "mutable_table_names": [
      "development_program_heads",
      "development_work_item_heads",
      "development_effect_heads",
      "development_delivery_heads"
    ],
    "seed_c2b_rows": 0,
    "sequence": 2,
    "sql_rendering_contract": {
      "final_newline": True,
      "indentation": "two spaces for table members and trigger SELECT",
      "index_position": "after all tables and before triggers",
      "statement_separator": "two LF bytes",
      "table_statement_order": [
        "development_program_heads",
        "development_program_versions",
        "development_accepted_intent_revisions",
        "development_work_item_heads",
        "development_work_item_revisions",
        "development_program_version_work_items",
        "development_revision_edges",
        "development_work_spec_bindings",
        "development_semantic_attempts",
        "development_attempt_fences",
        "development_authority_evaluations",
        "development_effect_intents",
        "development_effect_fences",
        "development_author_commands",
        "development_effect_heads",
        "development_delivery_attempts",
        "development_delivery_heads",
        "development_decisions",
        "development_mutation_receipts"
      ],
      "trigger_order": "immutable table order; UPDATE then DELETE"
    },
    "strict_tables": True,
    "table_count": 19,
    "table_names_in_order": [
      "development_program_heads",
      "development_program_versions",
      "development_accepted_intent_revisions",
      "development_work_item_heads",
      "development_work_item_revisions",
      "development_program_version_work_items",
      "development_revision_edges",
      "development_work_spec_bindings",
      "development_semantic_attempts",
      "development_attempt_fences",
      "development_authority_evaluations",
      "development_effect_intents",
      "development_effect_fences",
      "development_author_commands",
      "development_effect_heads",
      "development_delivery_attempts",
      "development_delivery_heads",
      "development_decisions",
      "development_mutation_receipts"
    ],
    "view_count": 0
  },
  "tables": [
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-program-head.v1'",
          "constant": "governed-execution.nwp-development-program-head.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(current_program_version_ref)='text' AND length(current_program_version_ref) BETWEEN 1 AND 96 AND substr(current_program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND current_program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(current_program_version_ref,1,instr(current_program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "current_program_version_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(current_program_version_number)='integer' AND current_program_version_number>=1",
          "constant": None,
          "enum_values": None,
          "logical_type": "positive_integer",
          "name": "current_program_version_number",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(head_revision)='integer' AND head_revision>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "head_revision",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_state)='text' AND program_state IN ('active','accepted','terminal_rejected','blocked')",
          "constant": None,
          "enum_values": [
            "active",
            "accepted",
            "terminal_rejected",
            "blocked"
          ],
          "logical_type": "closed_enum",
          "name": "program_state",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(updated_at)='text' AND length(updated_at)=20 AND updated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(updated_at,1,4) BETWEEN '0001' AND '9999' AND substr(updated_at,6,2) BETWEEN '01' AND '12' AND substr(updated_at,9,2) BETWEEN '01' AND '31' AND substr(updated_at,12,2) BETWEEN '00' AND '23' AND substr(updated_at,15,2) BETWEEN '00' AND '59' AND substr(updated_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at)=updated_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "updated_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(head_digest)='text' AND length(head_digest)=64 AND head_digest=lower(head_digest) AND head_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "head_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "head_digest",
      "digest_domain": "governed-execution.nwp-development-program-head.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "program_ref",
        "current_program_version_ref",
        "current_program_version_number",
        "head_revision",
        "program_state",
        "updated_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "current_program_version_ref"
          ],
          "deferrability": "DEFERRABLE INITIALLY DEFERRED",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "program_head_current_program_version"
        }
      ],
      "future_mutation_owner": "program_progression_CAS",
      "immutable_triggers": [],
      "mutable": True,
      "name": "development_program_heads",
      "primary_key": [
        "program_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "program_head_and_current_version"
      ],
      "record_schema_id": "governed-execution.nwp-development-program-head.v1",
      "role": "program_progression_head",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [],
      "timestamp_participation": {
        "updated_at": True
      },
      "unique_constraints": []
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-program-version.v1'",
          "constant": "governed-execution.nwp-development-program-version.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_version_number)='integer' AND program_version_number>=1",
          "constant": None,
          "enum_values": None,
          "logical_type": "positive_integer",
          "name": "program_version_number",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_version_kind)='text' AND program_version_kind IN ('initial','accepted','repair','replan','terminal_rejected','blocked')",
          "constant": None,
          "enum_values": [
            "initial",
            "accepted",
            "repair",
            "replan",
            "terminal_rejected",
            "blocked"
          ],
          "logical_type": "closed_enum",
          "name": "program_version_kind",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(creating_decision_ref)='text' AND length(creating_decision_ref) BETWEEN 1 AND 96 AND substr(creating_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND creating_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(creating_decision_ref,1,instr(creating_decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "creating_decision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "created_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_version_digest)='text' AND length(program_version_digest)=64 AND program_version_digest=lower(program_version_digest) AND program_version_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "program_version_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "program_version_digest",
      "digest_domain": "governed-execution.nwp-development-program-version.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "program_version_ref",
        "program_ref",
        "program_version_number",
        "program_version_kind",
        "creating_decision_ref",
        "accepted_intent_revision_ref",
        "created_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref"
          ],
          "parent_table": "development_program_heads",
          "role": "program_version_program"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "program_version_accepted_intent_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "creating_decision_ref"
          ],
          "deferrability": "DEFERRABLE INITIALLY DEFERRED",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "decision_ref"
          ],
          "parent_table": "development_decisions",
          "role": "program_version_creating_decision"
        }
      ],
      "future_mutation_owner": "_initialize_development_program_or_progression_decision",
      "immutable_triggers": [
        "development_program_versions_no_update",
        "development_program_versions_no_delete"
      ],
      "mutable": False,
      "name": "development_program_versions",
      "primary_key": [
        "program_version_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "program_head_and_current_version",
        "initialize_decision_and_resulting_version",
        "paged_program_version_membership"
      ],
      "record_schema_id": "governed-execution.nwp-development-program-version.v1",
      "role": "program_version_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [
        {
          "name": "initial_program_version_number",
          "sql": "((program_version_kind='initial' AND program_version_number=1) OR (program_version_kind<>'initial' AND program_version_number>=2))"
        }
      ],
      "timestamp_participation": {
        "created_at": True
      },
      "unique_constraints": [
        [
          "program_ref",
          "program_version_ref"
        ],
        [
          "program_ref",
          "program_version_number"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-accepted-intent-revision.v1'",
          "constant": "governed-execution.nwp-development-accepted-intent-revision.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(accepted_intent_revision_number)='integer' AND accepted_intent_revision_number>=1",
          "constant": None,
          "enum_values": None,
          "logical_type": "positive_integer",
          "name": "accepted_intent_revision_number",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "prior_accepted_intent_revision_ref IS NULL OR (typeof(prior_accepted_intent_revision_ref)='text' AND length(prior_accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(prior_accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND prior_accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(prior_accepted_intent_revision_ref,1,instr(prior_accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "prior_accepted_intent_revision_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(source_intent_ref)='text' AND length(source_intent_ref) BETWEEN 1 AND 96 AND substr(source_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND source_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(source_intent_ref,1,instr(source_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "source_intent_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(source_intent_digest)='text' AND length(source_intent_digest)=64 AND source_intent_digest=lower(source_intent_digest) AND source_intent_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "source_intent_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(safe_projection_digest)='text' AND length(safe_projection_digest)=64 AND safe_projection_digest=lower(safe_projection_digest) AND safe_projection_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "safe_projection_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "created_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(accepted_intent_revision_digest)='text' AND length(accepted_intent_revision_digest)=64 AND accepted_intent_revision_digest=lower(accepted_intent_revision_digest) AND accepted_intent_revision_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "accepted_intent_revision_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "accepted_intent_revision_digest",
      "digest_domain": "governed-execution.nwp-development-accepted-intent-revision.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "accepted_intent_revision_ref",
        "program_ref",
        "accepted_intent_revision_number",
        "prior_accepted_intent_revision_ref",
        "source_intent_ref",
        "source_intent_digest",
        "safe_projection_digest",
        "created_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref"
          ],
          "parent_table": "development_program_heads",
          "role": "accepted_intent_program"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "prior_accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "accepted_intent_prior_revision"
        }
      ],
      "future_mutation_owner": "_initialize_development_program_or_replan",
      "immutable_triggers": [
        "development_accepted_intent_revisions_no_update",
        "development_accepted_intent_revisions_no_delete"
      ],
      "mutable": False,
      "name": "development_accepted_intent_revisions",
      "primary_key": [
        "accepted_intent_revision_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "accepted_intent_revision_by_exact_ref"
      ],
      "record_schema_id": "governed-execution.nwp-development-accepted-intent-revision.v1",
      "role": "accepted_intent_revision_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [
        {
          "name": "accepted_intent_prior_bidirectional",
          "sql": "((accepted_intent_revision_number=1 AND prior_accepted_intent_revision_ref IS NULL) OR (accepted_intent_revision_number>=2 AND prior_accepted_intent_revision_ref IS NOT NULL))"
        }
      ],
      "timestamp_participation": {
        "created_at": True
      },
      "unique_constraints": [
        [
          "program_ref",
          "accepted_intent_revision_ref"
        ],
        [
          "program_ref",
          "accepted_intent_revision_number"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-work-item-head.v1'",
          "constant": "governed-execution.nwp-development-work-item-head.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(current_work_item_revision_ref)='text' AND length(current_work_item_revision_ref) BETWEEN 1 AND 96 AND substr(current_work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND current_work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(current_work_item_revision_ref,1,instr(current_work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "current_work_item_revision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(current_work_item_revision_number)='integer' AND current_work_item_revision_number>=1",
          "constant": None,
          "enum_values": None,
          "logical_type": "positive_integer",
          "name": "current_work_item_revision_number",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(head_revision)='integer' AND head_revision>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "head_revision",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_state)='text' AND work_state IN ('planned','active','accepted','repair_required','terminal_rejected','blocked')",
          "constant": None,
          "enum_values": [
            "planned",
            "active",
            "accepted",
            "repair_required",
            "terminal_rejected",
            "blocked"
          ],
          "logical_type": "closed_enum",
          "name": "work_state",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(updated_at)='text' AND length(updated_at)=20 AND updated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(updated_at,1,4) BETWEEN '0001' AND '9999' AND substr(updated_at,6,2) BETWEEN '01' AND '12' AND substr(updated_at,9,2) BETWEEN '01' AND '31' AND substr(updated_at,12,2) BETWEEN '00' AND '23' AND substr(updated_at,15,2) BETWEEN '00' AND '59' AND substr(updated_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at)=updated_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "updated_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(head_digest)='text' AND length(head_digest)=64 AND head_digest=lower(head_digest) AND head_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "head_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "head_digest",
      "digest_domain": "governed-execution.nwp-development-work-item-head.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "work_item_ref",
        "program_ref",
        "current_work_item_revision_ref",
        "current_work_item_revision_number",
        "head_revision",
        "work_state",
        "updated_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref"
          ],
          "parent_table": "development_program_heads",
          "role": "work_item_head_program"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "current_work_item_revision_ref"
          ],
          "deferrability": "DEFERRABLE INITIALLY DEFERRED",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "work_item_head_current_revision"
        }
      ],
      "future_mutation_owner": "program_work_item_CAS",
      "immutable_triggers": [],
      "mutable": True,
      "name": "development_work_item_heads",
      "primary_key": [
        "work_item_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "work_item_head_and_revision_by_exact_ref"
      ],
      "record_schema_id": "governed-execution.nwp-development-work-item-head.v1",
      "role": "work_item_progression_head",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [],
      "timestamp_participation": {
        "updated_at": True
      },
      "unique_constraints": [
        [
          "program_ref",
          "work_item_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-work-item-revision.v1'",
          "constant": "governed-execution.nwp-development-work-item-revision.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_revision_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_revision_number)='integer' AND work_item_revision_number>=1",
          "constant": None,
          "enum_values": None,
          "logical_type": "positive_integer",
          "name": "work_item_revision_number",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_revision_kind)='text' AND work_item_revision_kind IN ('initial','replan')",
          "constant": None,
          "enum_values": [
            "initial",
            "replan"
          ],
          "logical_type": "closed_enum",
          "name": "work_item_revision_kind",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "prior_work_item_revision_ref IS NULL OR (typeof(prior_work_item_revision_ref)='text' AND length(prior_work_item_revision_ref) BETWEEN 1 AND 96 AND substr(prior_work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND prior_work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(prior_work_item_revision_ref,1,instr(prior_work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "prior_work_item_revision_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "created_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_revision_digest)='text' AND length(work_item_revision_digest)=64 AND work_item_revision_digest=lower(work_item_revision_digest) AND work_item_revision_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "work_item_revision_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "work_item_revision_digest",
      "digest_domain": "governed-execution.nwp-development-work-item-revision.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "work_item_revision_ref",
        "program_ref",
        "work_item_ref",
        "work_item_revision_number",
        "work_item_revision_kind",
        "prior_work_item_revision_ref",
        "accepted_intent_revision_ref",
        "created_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref"
          ],
          "parent_table": "development_work_item_heads",
          "role": "work_item_revision_head"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "prior_work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "work_item_revision_prior"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "work_item_revision_accepted_intent"
        }
      ],
      "future_mutation_owner": "_initialize_development_program_or_replan",
      "immutable_triggers": [
        "development_work_item_revisions_no_update",
        "development_work_item_revisions_no_delete"
      ],
      "mutable": False,
      "name": "development_work_item_revisions",
      "primary_key": [
        "work_item_revision_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "work_item_head_and_revision_by_exact_ref",
        "paged_program_version_membership"
      ],
      "record_schema_id": "governed-execution.nwp-development-work-item-revision.v1",
      "role": "work_item_revision_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [
        {
          "name": "work_revision_prior_bidirectional",
          "sql": "((work_item_revision_kind='initial' AND work_item_revision_number=1 AND prior_work_item_revision_ref IS NULL) OR (work_item_revision_kind='replan' AND work_item_revision_number>=2 AND prior_work_item_revision_ref IS NOT NULL))"
        }
      ],
      "timestamp_participation": {
        "created_at": True
      },
      "unique_constraints": [
        [
          "program_ref",
          "work_item_ref",
          "work_item_revision_ref"
        ],
        [
          "program_ref",
          "work_item_revision_ref"
        ],
        [
          "program_ref",
          "work_item_ref",
          "work_item_revision_number"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-program-version-work-item.v1'",
          "constant": "governed-execution.nwp-development-program-version-work-item.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": False,
          "pk_ordinal": 2,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": False,
          "pk_ordinal": 3,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_revision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(membership_ordinal)='integer' AND membership_ordinal>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "membership_ordinal",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "created_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(membership_digest)='text' AND length(membership_digest)=64 AND membership_digest=lower(membership_digest) AND membership_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "membership_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "membership_digest",
      "digest_domain": "governed-execution.nwp-development-program-version-work-item.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "program_ref",
        "program_version_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "membership_ordinal",
        "created_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "membership_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "membership_work_item_revision"
        }
      ],
      "future_mutation_owner": "_initialize_development_program_or_replan",
      "immutable_triggers": [
        "development_program_version_work_items_no_update",
        "development_program_version_work_items_no_delete"
      ],
      "mutable": False,
      "name": "development_program_version_work_items",
      "primary_key": [
        "program_ref",
        "program_version_ref",
        "work_item_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "paged_program_version_membership"
      ],
      "record_schema_id": "governed-execution.nwp-development-program-version-work-item.v1",
      "role": "program_version_membership_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [],
      "timestamp_participation": {
        "created_at": True
      },
      "unique_constraints": [
        [
          "program_ref",
          "program_version_ref",
          "membership_ordinal"
        ]
      ]
    },
    {
      "c2b2_reader_treatment": "durable row representation only",
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-revision-edge.v1'",
          "constant": "governed-execution.nwp-development-revision-edge.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(revision_edge_ref)='text' AND length(revision_edge_ref) BETWEEN 1 AND 96 AND substr(revision_edge_ref,1,1) GLOB '[0-9A-Za-z]' AND revision_edge_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(revision_edge_ref,1,instr(revision_edge_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "revision_edge_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(relation_key_digest)='text' AND length(relation_key_digest)=64 AND relation_key_digest=lower(relation_key_digest) AND relation_key_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "relation_key_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(revision_edge_kind)='text' AND revision_edge_kind IN ('accepted_intent_supersedes','work_item_supersedes','work_item_split','work_item_merge')",
          "constant": None,
          "enum_values": [
            "accepted_intent_supersedes",
            "work_item_supersedes",
            "work_item_split",
            "work_item_merge"
          ],
          "logical_type": "closed_enum",
          "name": "revision_edge_kind",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "from_accepted_intent_revision_ref IS NULL OR (typeof(from_accepted_intent_revision_ref)='text' AND length(from_accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(from_accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND from_accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(from_accepted_intent_revision_ref,1,instr(from_accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "from_accepted_intent_revision_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "to_accepted_intent_revision_ref IS NULL OR (typeof(to_accepted_intent_revision_ref)='text' AND length(to_accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(to_accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND to_accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(to_accepted_intent_revision_ref,1,instr(to_accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "to_accepted_intent_revision_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "from_work_item_revision_ref IS NULL OR (typeof(from_work_item_revision_ref)='text' AND length(from_work_item_revision_ref) BETWEEN 1 AND 96 AND substr(from_work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND from_work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(from_work_item_revision_ref,1,instr(from_work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "from_work_item_revision_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "to_work_item_revision_ref IS NULL OR (typeof(to_work_item_revision_ref)='text' AND length(to_work_item_revision_ref) BETWEEN 1 AND 96 AND substr(to_work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND to_work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(to_work_item_revision_ref,1,instr(to_work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "to_work_item_revision_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "created_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(revision_edge_digest)='text' AND length(revision_edge_digest)=64 AND revision_edge_digest=lower(revision_edge_digest) AND revision_edge_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "revision_edge_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "revision_edge_digest",
      "digest_domain": "governed-execution.nwp-development-revision-edge.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "revision_edge_ref",
        "relation_key_digest",
        "program_ref",
        "revision_edge_kind",
        "from_accepted_intent_revision_ref",
        "to_accepted_intent_revision_ref",
        "from_work_item_revision_ref",
        "to_work_item_revision_ref",
        "created_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref"
          ],
          "parent_table": "development_program_heads",
          "role": "revision_edge_program"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "from_accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "revision_edge_from_accepted_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "to_accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "revision_edge_to_accepted_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "from_work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "revision_edge_from_work_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "to_work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "revision_edge_to_work_revision"
        }
      ],
      "future_mutation_owner": "_record_development_progression_decision",
      "future_reader_owner": "C2B6",
      "future_reader_owner_reason": "exact revision-edge selection is progression-family-specific and belongs to the C2B6 graph-locator/replay contract before C2B6 writers",
      "immutable_triggers": [
        "development_revision_edges_no_update",
        "development_revision_edges_no_delete"
      ],
      "mutable": False,
      "name": "development_revision_edges",
      "primary_key": [
        "revision_edge_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [],
      "record_schema_id": "governed-execution.nwp-development-revision-edge.v1",
      "role": "revision_edge_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [
        {
          "name": "revision_edge_endpoint_algebra",
          "sql": "((revision_edge_kind='accepted_intent_supersedes' AND from_accepted_intent_revision_ref IS NOT NULL AND to_accepted_intent_revision_ref IS NOT NULL AND from_work_item_revision_ref IS NULL AND to_work_item_revision_ref IS NULL) OR (revision_edge_kind IN ('work_item_supersedes','work_item_split','work_item_merge') AND from_accepted_intent_revision_ref IS NULL AND to_accepted_intent_revision_ref IS NULL AND from_work_item_revision_ref IS NOT NULL AND to_work_item_revision_ref IS NOT NULL))"
        }
      ],
      "timestamp_participation": {
        "created_at": True
      },
      "unique_constraints": [
        [
          "relation_key_digest"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-work-spec-binding.v1'",
          "constant": "governed-execution.nwp-development-work-spec-binding.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_spec_ref)='text' AND length(work_spec_ref) BETWEEN 1 AND 96 AND substr(work_spec_ref,1,1) GLOB '[0-9A-Za-z]' AND work_spec_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_spec_ref,1,instr(work_spec_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_spec_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_revision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(repository_ref)='text' AND length(repository_ref) BETWEEN 1 AND 96 AND substr(repository_ref,1,1) GLOB '[0-9A-Za-z]' AND repository_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(repository_ref,1,instr(repository_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "repository_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(base_git_object_format)='text' AND base_git_object_format='sha1'",
          "constant": "sha1",
          "enum_values": None,
          "logical_type": "constant_text",
          "name": "base_git_object_format",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(base_git_oid)='text' AND length(base_git_oid)=40 AND base_git_oid=lower(base_git_oid) AND base_git_oid NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "git_sha1_oid",
          "name": "base_git_oid",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": "[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]",
          "check_sql": "typeof(authorized_paths_json)='text' AND authorized_paths_json='[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]'",
          "constant": None,
          "enum_values": None,
          "logical_type": "canonical_json",
          "name": "authorized_paths_json",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(validation_requirement_ref)='text' AND length(validation_requirement_ref) BETWEEN 1 AND 96 AND substr(validation_requirement_ref,1,1) GLOB '[0-9A-Za-z]' AND validation_requirement_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(validation_requirement_ref,1,instr(validation_requirement_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "validation_requirement_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(review_requirement_ref)='text' AND length(review_requirement_ref) BETWEEN 1 AND 96 AND substr(review_requirement_ref,1,1) GLOB '[0-9A-Za-z]' AND review_requirement_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(review_requirement_ref,1,instr(review_requirement_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "review_requirement_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(privacy_classification)='text' AND privacy_classification='private_work_spec'",
          "constant": "private_work_spec",
          "enum_values": None,
          "logical_type": "constant_text",
          "name": "privacy_classification",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_spec_digest)='text' AND length(work_spec_digest)=64 AND work_spec_digest=lower(work_spec_digest) AND work_spec_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "work_spec_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(safe_projection_digest)='text' AND length(safe_projection_digest)=64 AND safe_projection_digest=lower(safe_projection_digest) AND safe_projection_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "safe_projection_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "recorded_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_spec_binding_digest)='text' AND length(work_spec_binding_digest)=64 AND work_spec_binding_digest=lower(work_spec_binding_digest) AND work_spec_binding_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "work_spec_binding_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "work_spec_binding_digest",
      "digest_domain": "governed-execution.nwp-development-work-spec-binding.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "work_spec_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "authorized_paths_json",
        "validation_requirement_ref",
        "review_requirement_ref",
        "privacy_classification",
        "work_spec_digest",
        "safe_projection_digest",
        "recorded_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "work_spec_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "work_spec_accepted_intent_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "work_spec_work_item_revision"
        }
      ],
      "future_mutation_owner": "_initialize_development_program_or_replan",
      "immutable_triggers": [
        "development_work_spec_bindings_no_update",
        "development_work_spec_bindings_no_delete"
      ],
      "mutable": False,
      "name": "development_work_spec_bindings",
      "primary_key": [
        "work_spec_ref"
      ],
      "privacy_class": "safe_private_work_spec_projection",
      "reader_roles": [
        "work_spec_safe_binding"
      ],
      "record_schema_id": "governed-execution.nwp-development-work-spec-binding.v1",
      "role": "work_spec_binding_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [],
      "timestamp_participation": {
        "recorded_at": True,
        "safe_projection_digest": False
      },
      "unique_constraints": [
        [
          "program_ref",
          "program_version_ref",
          "work_item_ref",
          "work_item_revision_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-semantic-attempt.v1'",
          "constant": "governed-execution.nwp-development-semantic-attempt.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "semantic_attempt_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_revision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(attempt_number)='integer' AND attempt_number>=1",
          "constant": None,
          "enum_values": None,
          "logical_type": "positive_integer",
          "name": "attempt_number",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(candidate_ref)='text' AND length(candidate_ref) BETWEEN 1 AND 96 AND substr(candidate_ref,1,1) GLOB '[0-9A-Za-z]' AND candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(candidate_ref,1,instr(candidate_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "candidate_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(attempt_phase)='text' AND attempt_phase IN ('established')",
          "constant": None,
          "enum_values": [
            "established"
          ],
          "logical_type": "closed_enum",
          "name": "attempt_phase",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(selection_decision_ref)='text' AND length(selection_decision_ref) BETWEEN 1 AND 96 AND substr(selection_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND selection_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(selection_decision_ref,1,instr(selection_decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "selection_decision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "created_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(semantic_attempt_digest)='text' AND length(semantic_attempt_digest)=64 AND semantic_attempt_digest=lower(semantic_attempt_digest) AND semantic_attempt_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "semantic_attempt_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "semantic_attempt_digest",
      "digest_domain": "governed-execution.nwp-development-semantic-attempt.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "semantic_attempt_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "attempt_number",
        "candidate_ref",
        "attempt_phase",
        "selection_decision_ref",
        "created_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "semantic_attempt_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "semantic_attempt_accepted_intent_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "semantic_attempt_work_item_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "selection_decision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "decision_ref"
          ],
          "parent_table": "development_decisions",
          "role": "semantic_attempt_selection_decision"
        }
      ],
      "future_mutation_owner": "_establish_development_author_effect_intent",
      "immutable_triggers": [
        "development_semantic_attempts_no_update",
        "development_semantic_attempts_no_delete"
      ],
      "mutable": False,
      "name": "development_semantic_attempts",
      "primary_key": [
        "semantic_attempt_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "attempt_fence_command_effect_aggregate"
      ],
      "record_schema_id": "governed-execution.nwp-development-semantic-attempt.v1",
      "role": "semantic_attempt_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [],
      "timestamp_participation": {
        "created_at": True
      },
      "unique_constraints": [
        [
          "program_ref",
          "semantic_attempt_ref"
        ],
        [
          "program_ref",
          "candidate_ref"
        ],
        [
          "program_ref",
          "work_item_ref",
          "attempt_number"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-attempt-fence.v1'",
          "constant": "governed-execution.nwp-attempt-fence.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(attempt_fence_ref)='text' AND length(attempt_fence_ref) BETWEEN 1 AND 96 AND substr(attempt_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(attempt_fence_ref,1,instr(attempt_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "attempt_fence_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(parent_standing_grant_ref)='text' AND length(parent_standing_grant_ref) BETWEEN 1 AND 96 AND substr(parent_standing_grant_ref,1,1) GLOB '[0-9A-Za-z]' AND parent_standing_grant_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(parent_standing_grant_ref,1,instr(parent_standing_grant_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "parent_standing_grant_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(parent_standing_grant_digest)='text' AND length(parent_standing_grant_digest)=64 AND parent_standing_grant_digest=lower(parent_standing_grant_digest) AND parent_standing_grant_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "parent_standing_grant_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(attempt_authorization_ref)='text' AND length(attempt_authorization_ref) BETWEEN 1 AND 96 AND substr(attempt_authorization_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_authorization_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(attempt_authorization_ref,1,instr(attempt_authorization_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "attempt_authorization_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(attempt_authorization_digest)='text' AND length(attempt_authorization_digest)=64 AND attempt_authorization_digest=lower(attempt_authorization_digest) AND attempt_authorization_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "attempt_authorization_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_revision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "semantic_attempt_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(repository_ref)='text' AND length(repository_ref) BETWEEN 1 AND 96 AND substr(repository_ref,1,1) GLOB '[0-9A-Za-z]' AND repository_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(repository_ref,1,instr(repository_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "repository_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(base_git_object_format)='text' AND base_git_object_format='sha1'",
          "constant": "sha1",
          "enum_values": None,
          "logical_type": "constant_text",
          "name": "base_git_object_format",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(base_git_oid)='text' AND length(base_git_oid)=40 AND base_git_oid=lower(base_git_oid) AND base_git_oid NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "git_sha1_oid",
          "name": "base_git_oid",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": "[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]",
          "check_sql": "typeof(path_ceiling_json)='text' AND path_ceiling_json='[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]'",
          "constant": None,
          "enum_values": None,
          "logical_type": "canonical_json",
          "name": "path_ceiling_json",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(allowed_effect_class_mask)='integer' AND allowed_effect_class_mask BETWEEN 1 AND 31",
          "constant": None,
          "enum_values": None,
          "logical_type": "effect_class_mask",
          "name": "allowed_effect_class_mask",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_active_invocations)='integer' AND aggregate_max_active_invocations>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_active_invocations",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_candidate_bytes)='integer' AND aggregate_max_candidate_bytes>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_candidate_bytes",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_changed_files)='integer' AND aggregate_max_changed_files>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_changed_files",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_cost_microusd)='integer' AND aggregate_max_cost_microusd>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_cost_microusd",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_cpu_seconds)='integer' AND aggregate_max_cpu_seconds>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_cpu_seconds",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_deliveries)='integer' AND aggregate_max_deliveries>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_deliveries",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_deployments)='integer' AND aggregate_max_deployments>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_deployments",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_local_commits)='integer' AND aggregate_max_local_commits>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_local_commits",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_memory_bytes)='integer' AND aggregate_max_memory_bytes>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_memory_bytes",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_merges)='integer' AND aggregate_max_merges>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_merges",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_model_input_tokens)='integer' AND aggregate_max_model_input_tokens>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_model_input_tokens",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_model_output_tokens)='integer' AND aggregate_max_model_output_tokens>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_model_output_tokens",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_pull_requests)='integer' AND aggregate_max_pull_requests>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_pull_requests",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_pushes)='integer' AND aggregate_max_pushes>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_pushes",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(aggregate_max_wall_seconds)='integer' AND aggregate_max_wall_seconds>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "aggregate_max_wall_seconds",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(expires_at)='text' AND length(expires_at)=20 AND expires_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(expires_at,1,4) BETWEEN '0001' AND '9999' AND substr(expires_at,6,2) BETWEEN '01' AND '12' AND substr(expires_at,9,2) BETWEEN '01' AND '31' AND substr(expires_at,12,2) BETWEEN '00' AND '23' AND substr(expires_at,15,2) BETWEEN '00' AND '59' AND substr(expires_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',expires_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',expires_at)=expires_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "expires_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(global_stop_ref)='text' AND length(global_stop_ref) BETWEEN 1 AND 96 AND substr(global_stop_ref,1,1) GLOB '[0-9A-Za-z]' AND global_stop_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(global_stop_ref,1,instr(global_stop_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "global_stop_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(global_stop_version)='integer' AND global_stop_version>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "global_stop_version",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(attempt_fence_digest)='text' AND length(attempt_fence_digest)=64 AND attempt_fence_digest=lower(attempt_fence_digest) AND attempt_fence_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "attempt_fence_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "recorded_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "attempt_fence_digest",
      "digest_domain": "governed-execution.nwp-attempt-fence.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "attempt_fence_ref",
        "parent_standing_grant_ref",
        "parent_standing_grant_digest",
        "attempt_authorization_ref",
        "attempt_authorization_digest",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "path_ceiling_json",
        "allowed_effect_class_mask",
        "aggregate_max_active_invocations",
        "aggregate_max_candidate_bytes",
        "aggregate_max_changed_files",
        "aggregate_max_cost_microusd",
        "aggregate_max_cpu_seconds",
        "aggregate_max_deliveries",
        "aggregate_max_deployments",
        "aggregate_max_local_commits",
        "aggregate_max_memory_bytes",
        "aggregate_max_merges",
        "aggregate_max_model_input_tokens",
        "aggregate_max_model_output_tokens",
        "aggregate_max_pull_requests",
        "aggregate_max_pushes",
        "aggregate_max_wall_seconds",
        "expires_at",
        "global_stop_ref",
        "global_stop_version"
      ],
      "excluded_operational_fields": [
        "recorded_at"
      ],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "attempt_fence_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "attempt_fence_accepted_intent_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "attempt_fence_work_item_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "attempt_fence_semantic_attempt"
        }
      ],
      "future_mutation_owner": "_establish_development_author_effect_intent",
      "immutable_triggers": [
        "development_attempt_fences_no_update",
        "development_attempt_fences_no_delete"
      ],
      "mutable": False,
      "name": "development_attempt_fences",
      "primary_key": [
        "attempt_fence_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "attempt_fence_command_effect_aggregate"
      ],
      "record_schema_id": "governed-execution.nwp-attempt-fence.v1",
      "role": "attempt_fence_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [],
      "timestamp_participation": {
        "expires_at": True,
        "recorded_at": False
      },
      "unique_constraints": [
        [
          "program_ref",
          "attempt_fence_ref"
        ],
        [
          "program_ref",
          "semantic_attempt_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-authority-evaluation.v1'",
          "constant": "governed-execution.nwp-development-authority-evaluation.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(authority_evaluation_ref)='text' AND length(authority_evaluation_ref) BETWEEN 1 AND 96 AND substr(authority_evaluation_ref,1,1) GLOB '[0-9A-Za-z]' AND authority_evaluation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(authority_evaluation_ref,1,instr(authority_evaluation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "authority_evaluation_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(evaluation_scope)='text' AND evaluation_scope IN ('attempt','effect')",
          "constant": None,
          "enum_values": [
            "attempt",
            "effect"
          ],
          "logical_type": "closed_enum",
          "name": "evaluation_scope",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(evaluation_subject_ref)='text' AND length(evaluation_subject_ref) BETWEEN 1 AND 96 AND substr(evaluation_subject_ref,1,1) GLOB '[0-9A-Za-z]' AND evaluation_subject_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(evaluation_subject_ref,1,instr(evaluation_subject_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "evaluation_subject_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "semantic_attempt_ref IS NULL OR (typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "semantic_attempt_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "effect_intent_ref IS NULL OR (typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "effect_intent_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(authority_ref)='text' AND length(authority_ref) BETWEEN 1 AND 96 AND substr(authority_ref,1,1) GLOB '[0-9A-Za-z]' AND authority_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(authority_ref,1,instr(authority_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "authority_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(authority_digest)='text' AND length(authority_digest)=64 AND authority_digest=lower(authority_digest) AND authority_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "authority_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(authority_state)='text' AND authority_state IN ('pending','verified','blocked','stale','revoked','expired')",
          "constant": None,
          "enum_values": [
            "pending",
            "verified",
            "blocked",
            "stale",
            "revoked",
            "expired"
          ],
          "logical_type": "closed_enum",
          "name": "authority_state",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(reason_code)='text' AND length(reason_code) BETWEEN 1 AND 96 AND substr(reason_code,1,1) GLOB '[a-z]' AND reason_code NOT GLOB '*[^a-z0-9_.-]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "reason_code",
          "name": "reason_code",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "expires_at IS NULL OR (typeof(expires_at)='text' AND length(expires_at)=20 AND expires_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(expires_at,1,4) BETWEEN '0001' AND '9999' AND substr(expires_at,6,2) BETWEEN '01' AND '12' AND substr(expires_at,9,2) BETWEEN '01' AND '31' AND substr(expires_at,12,2) BETWEEN '00' AND '23' AND substr(expires_at,15,2) BETWEEN '00' AND '59' AND substr(expires_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',expires_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',expires_at)=expires_at)",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "expires_at",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(evaluated_at)='text' AND length(evaluated_at)=20 AND evaluated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(evaluated_at,1,4) BETWEEN '0001' AND '9999' AND substr(evaluated_at,6,2) BETWEEN '01' AND '12' AND substr(evaluated_at,9,2) BETWEEN '01' AND '31' AND substr(evaluated_at,12,2) BETWEEN '00' AND '23' AND substr(evaluated_at,15,2) BETWEEN '00' AND '59' AND substr(evaluated_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',evaluated_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',evaluated_at)=evaluated_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "evaluated_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(authority_evaluation_digest)='text' AND length(authority_evaluation_digest)=64 AND authority_evaluation_digest=lower(authority_evaluation_digest) AND authority_evaluation_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "authority_evaluation_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "authority_evaluation_digest",
      "digest_domain": "governed-execution.nwp-development-authority-evaluation.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "authority_evaluation_ref",
        "program_ref",
        "evaluation_scope",
        "evaluation_subject_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "authority_ref",
        "authority_digest",
        "authority_state",
        "reason_code",
        "expires_at",
        "evaluated_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref"
          ],
          "parent_table": "development_program_heads",
          "role": "authority_evaluation_program"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "authority_evaluation_semantic_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "authority_evaluation_effect_intent"
        }
      ],
      "future_mutation_owner": "effect_establishment_authority_binding",
      "immutable_triggers": [
        "development_authority_evaluations_no_update",
        "development_authority_evaluations_no_delete"
      ],
      "mutable": False,
      "name": "development_authority_evaluations",
      "primary_key": [
        "authority_evaluation_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "authority_evaluation_by_exact_ref"
      ],
      "record_schema_id": "governed-execution.nwp-development-authority-evaluation.v1",
      "role": "authority_evaluation_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [
        {
          "name": "authority_scope_subject_algebra",
          "sql": "((evaluation_scope='attempt' AND semantic_attempt_ref IS NOT NULL AND effect_intent_ref IS NULL AND evaluation_subject_ref=semantic_attempt_ref) OR (evaluation_scope='effect' AND semantic_attempt_ref IS NULL AND effect_intent_ref IS NOT NULL AND evaluation_subject_ref=effect_intent_ref))"
        },
        {
          "name": "authority_expiry_algebra",
          "sql": "((authority_state IN ('verified','expired') AND expires_at IS NOT NULL) OR (authority_state IN ('pending','blocked','stale','revoked') AND expires_at IS NULL))"
        }
      ],
      "timestamp_participation": {
        "evaluated_at": True,
        "expires_at": True
      },
      "unique_constraints": [
        [
          "program_ref",
          "authority_evaluation_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-effect-intent.v1'",
          "constant": "governed-execution.nwp-development-effect-intent.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "effect_intent_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "semantic_attempt_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_class)='text' AND effect_class IN ('author_candidate','cancel_effect','local_git_commit','review_candidate','validate_candidate')",
          "constant": None,
          "enum_values": [
            "author_candidate",
            "cancel_effect",
            "local_git_commit",
            "review_candidate",
            "validate_candidate"
          ],
          "logical_type": "closed_enum",
          "name": "effect_class",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(candidate_ref)='text' AND length(candidate_ref) BETWEEN 1 AND 96 AND substr(candidate_ref,1,1) GLOB '[0-9A-Za-z]' AND candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(candidate_ref,1,instr(candidate_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "candidate_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(command_ref)='text' AND length(command_ref) BETWEEN 1 AND 96 AND substr(command_ref,1,1) GLOB '[0-9A-Za-z]' AND command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(command_ref,1,instr(command_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "command_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(basis_decision_ref)='text' AND length(basis_decision_ref) BETWEEN 1 AND 96 AND substr(basis_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND basis_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(basis_decision_ref,1,instr(basis_decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "basis_decision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "cancellation_target_effect_intent_ref IS NULL OR (typeof(cancellation_target_effect_intent_ref)='text' AND length(cancellation_target_effect_intent_ref) BETWEEN 1 AND 96 AND substr(cancellation_target_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND cancellation_target_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(cancellation_target_effect_intent_ref,1,instr(cancellation_target_effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "cancellation_target_effect_intent_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "expected_target_effect_head_revision IS NULL OR (typeof(expected_target_effect_head_revision)='integer' AND expected_target_effect_head_revision>=0)",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "expected_target_effect_head_revision",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "portable_capsule_digest IS NULL OR (typeof(portable_capsule_digest)='text' AND length(portable_capsule_digest)=64 AND portable_capsule_digest=lower(portable_capsule_digest) AND portable_capsule_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "portable_capsule_digest",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(created_at)='text' AND length(created_at)=20 AND created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(created_at,1,4) BETWEEN '0001' AND '9999' AND substr(created_at,6,2) BETWEEN '01' AND '12' AND substr(created_at,9,2) BETWEEN '01' AND '31' AND substr(created_at,12,2) BETWEEN '00' AND '23' AND substr(created_at,15,2) BETWEEN '00' AND '59' AND substr(created_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',created_at)=created_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "created_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_intent_digest)='text' AND length(effect_intent_digest)=64 AND effect_intent_digest=lower(effect_intent_digest) AND effect_intent_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "effect_intent_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "effect_intent_digest",
      "digest_domain": "governed-execution.nwp-development-effect-intent.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "effect_intent_ref",
        "program_ref",
        "program_version_ref",
        "semantic_attempt_ref",
        "effect_class",
        "candidate_ref",
        "command_ref",
        "basis_decision_ref",
        "cancellation_target_effect_intent_ref",
        "expected_target_effect_head_revision",
        "portable_capsule_digest",
        "created_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [
        "uq_development_effect_intents_author_command"
      ],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "effect_intent_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "effect_intent_semantic_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Require equal program_ref, exact basis decision identity/digest, and basis-kind coherence; mismatch is database_integrity_failure.",
          "child_columns": [
            "basis_decision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "decision_ref"
          ],
          "parent_table": "development_decisions",
          "role": "effect_intent_basis_decision_owner_exception"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "command_ref"
          ],
          "deferrability": "DEFERRABLE INITIALLY DEFERRED",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "command_ref"
          ],
          "parent_table": "development_author_commands",
          "role": "author_effect_intent_command"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "cancellation_target_effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "cancellation_target_effect_intent"
        }
      ],
      "future_mutation_owner": "effect_establishment",
      "immutable_triggers": [
        "development_effect_intents_no_update",
        "development_effect_intents_no_delete"
      ],
      "mutable": False,
      "name": "development_effect_intents",
      "primary_key": [
        "effect_intent_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "attempt_fence_command_effect_aggregate"
      ],
      "record_schema_id": "governed-execution.nwp-development-effect-intent.v1",
      "role": "effect_intent_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [
        {
          "name": "effect_intent_cancellation_algebra",
          "sql": "((effect_class='cancel_effect' AND cancellation_target_effect_intent_ref IS NOT NULL AND expected_target_effect_head_revision IS NOT NULL) OR (effect_class<>'cancel_effect' AND cancellation_target_effect_intent_ref IS NULL AND expected_target_effect_head_revision IS NULL))"
        },
        {
          "name": "effect_intent_capsule_algebra",
          "sql": "((effect_class='author_candidate' AND portable_capsule_digest IS NULL) OR (effect_class IN ('validate_candidate','review_candidate','local_git_commit') AND portable_capsule_digest IS NOT NULL) OR effect_class='cancel_effect')"
        }
      ],
      "timestamp_participation": {
        "created_at": True
      },
      "unique_constraints": [
        [
          "program_ref",
          "effect_intent_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-effect-fence.v1'",
          "constant": "governed-execution.nwp-effect-fence.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_fence_ref)='text' AND length(effect_fence_ref) BETWEEN 1 AND 96 AND substr(effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_fence_ref,1,instr(effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "effect_fence_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(parent_standing_grant_ref)='text' AND length(parent_standing_grant_ref) BETWEEN 1 AND 96 AND substr(parent_standing_grant_ref,1,1) GLOB '[0-9A-Za-z]' AND parent_standing_grant_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(parent_standing_grant_ref,1,instr(parent_standing_grant_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "parent_standing_grant_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(parent_standing_grant_digest)='text' AND length(parent_standing_grant_digest)=64 AND parent_standing_grant_digest=lower(parent_standing_grant_digest) AND parent_standing_grant_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "parent_standing_grant_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_authorization_ref)='text' AND length(effect_authorization_ref) BETWEEN 1 AND 96 AND substr(effect_authorization_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_authorization_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_authorization_ref,1,instr(effect_authorization_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "effect_authorization_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_authorization_digest)='text' AND length(effect_authorization_digest)=64 AND effect_authorization_digest=lower(effect_authorization_digest) AND effect_authorization_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "effect_authorization_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(attempt_fence_ref)='text' AND length(attempt_fence_ref) BETWEEN 1 AND 96 AND substr(attempt_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(attempt_fence_ref,1,instr(attempt_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "attempt_fence_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(attempt_fence_digest)='text' AND length(attempt_fence_digest)=64 AND attempt_fence_digest=lower(attempt_fence_digest) AND attempt_fence_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "attempt_fence_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_revision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "semantic_attempt_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "effect_intent_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_class)='text' AND effect_class IN ('author_candidate','cancel_effect','local_git_commit','review_candidate','validate_candidate')",
          "constant": None,
          "enum_values": [
            "author_candidate",
            "cancel_effect",
            "local_git_commit",
            "review_candidate",
            "validate_candidate"
          ],
          "logical_type": "closed_enum",
          "name": "effect_class",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(command_ref)='text' AND length(command_ref) BETWEEN 1 AND 96 AND substr(command_ref,1,1) GLOB '[0-9A-Za-z]' AND command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(command_ref,1,instr(command_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "command_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(command_digest)='text' AND length(command_digest)=64 AND command_digest=lower(command_digest) AND command_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "command_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(candidate_ref)='text' AND length(candidate_ref) BETWEEN 1 AND 96 AND substr(candidate_ref,1,1) GLOB '[0-9A-Za-z]' AND candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(candidate_ref,1,instr(candidate_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "candidate_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(repository_ref)='text' AND length(repository_ref) BETWEEN 1 AND 96 AND substr(repository_ref,1,1) GLOB '[0-9A-Za-z]' AND repository_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(repository_ref,1,instr(repository_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "repository_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(base_git_object_format)='text' AND base_git_object_format='sha1'",
          "constant": "sha1",
          "enum_values": None,
          "logical_type": "constant_text",
          "name": "base_git_object_format",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(base_git_oid)='text' AND length(base_git_oid)=40 AND base_git_oid=lower(base_git_oid) AND base_git_oid NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "git_sha1_oid",
          "name": "base_git_oid",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": "[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]",
          "check_sql": "typeof(path_ceiling_json)='text' AND path_ceiling_json='[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]'",
          "constant": None,
          "enum_values": None,
          "logical_type": "canonical_json",
          "name": "path_ceiling_json",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_active_invocations)='integer' AND effect_max_active_invocations>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_active_invocations",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_candidate_bytes)='integer' AND effect_max_candidate_bytes>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_candidate_bytes",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_changed_files)='integer' AND effect_max_changed_files>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_changed_files",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_cost_microusd)='integer' AND effect_max_cost_microusd>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_cost_microusd",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_cpu_seconds)='integer' AND effect_max_cpu_seconds>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_cpu_seconds",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_deliveries)='integer' AND effect_max_deliveries>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_deliveries",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_deployments)='integer' AND effect_max_deployments>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_deployments",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_local_commits)='integer' AND effect_max_local_commits>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_local_commits",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_memory_bytes)='integer' AND effect_max_memory_bytes>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_memory_bytes",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_merges)='integer' AND effect_max_merges>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_merges",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_model_input_tokens)='integer' AND effect_max_model_input_tokens>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_model_input_tokens",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_model_output_tokens)='integer' AND effect_max_model_output_tokens>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_model_output_tokens",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_pull_requests)='integer' AND effect_max_pull_requests>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_pull_requests",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_pushes)='integer' AND effect_max_pushes>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_pushes",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_wall_seconds)='integer' AND effect_max_wall_seconds>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_wall_seconds",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(expires_at)='text' AND length(expires_at)=20 AND expires_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(expires_at,1,4) BETWEEN '0001' AND '9999' AND substr(expires_at,6,2) BETWEEN '01' AND '12' AND substr(expires_at,9,2) BETWEEN '01' AND '31' AND substr(expires_at,12,2) BETWEEN '00' AND '23' AND substr(expires_at,15,2) BETWEEN '00' AND '59' AND substr(expires_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',expires_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',expires_at)=expires_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "expires_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(global_stop_ref)='text' AND length(global_stop_ref) BETWEEN 1 AND 96 AND substr(global_stop_ref,1,1) GLOB '[0-9A-Za-z]' AND global_stop_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(global_stop_ref,1,instr(global_stop_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "global_stop_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(global_stop_version)='integer' AND global_stop_version>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "global_stop_version",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "portable_capsule_digest IS NULL OR (typeof(portable_capsule_digest)='text' AND length(portable_capsule_digest)=64 AND portable_capsule_digest=lower(portable_capsule_digest) AND portable_capsule_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "portable_capsule_digest",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "cancellation_target_effect_intent_ref IS NULL OR (typeof(cancellation_target_effect_intent_ref)='text' AND length(cancellation_target_effect_intent_ref) BETWEEN 1 AND 96 AND substr(cancellation_target_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND cancellation_target_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(cancellation_target_effect_intent_ref,1,instr(cancellation_target_effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "cancellation_target_effect_intent_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "cancellation_target_effect_fence_ref IS NULL OR (typeof(cancellation_target_effect_fence_ref)='text' AND length(cancellation_target_effect_fence_ref) BETWEEN 1 AND 96 AND substr(cancellation_target_effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND cancellation_target_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(cancellation_target_effect_fence_ref,1,instr(cancellation_target_effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "cancellation_target_effect_fence_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "cancellation_target_effect_fence_digest IS NULL OR (typeof(cancellation_target_effect_fence_digest)='text' AND length(cancellation_target_effect_fence_digest)=64 AND cancellation_target_effect_fence_digest=lower(cancellation_target_effect_fence_digest) AND cancellation_target_effect_fence_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "cancellation_target_effect_fence_digest",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_fence_digest)='text' AND length(effect_fence_digest)=64 AND effect_fence_digest=lower(effect_fence_digest) AND effect_fence_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "effect_fence_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "recorded_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "effect_fence_digest",
      "digest_domain": "governed-execution.nwp-effect-fence.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "effect_fence_ref",
        "parent_standing_grant_ref",
        "parent_standing_grant_digest",
        "effect_authorization_ref",
        "effect_authorization_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "effect_class",
        "command_ref",
        "command_digest",
        "candidate_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "path_ceiling_json",
        "effect_max_active_invocations",
        "effect_max_candidate_bytes",
        "effect_max_changed_files",
        "effect_max_cost_microusd",
        "effect_max_cpu_seconds",
        "effect_max_deliveries",
        "effect_max_deployments",
        "effect_max_local_commits",
        "effect_max_memory_bytes",
        "effect_max_merges",
        "effect_max_model_input_tokens",
        "effect_max_model_output_tokens",
        "effect_max_pull_requests",
        "effect_max_pushes",
        "effect_max_wall_seconds",
        "expires_at",
        "global_stop_ref",
        "global_stop_version",
        "portable_capsule_digest",
        "cancellation_target_effect_intent_ref",
        "cancellation_target_effect_fence_ref",
        "cancellation_target_effect_fence_digest"
      ],
      "excluded_operational_fields": [
        "recorded_at"
      ],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "effect_fence_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "effect_fence_accepted_intent_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "effect_fence_work_item_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "effect_fence_semantic_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "effect_fence_effect_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "attempt_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "attempt_fence_ref"
          ],
          "parent_table": "development_attempt_fences",
          "role": "effect_fence_attempt_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "command_ref"
          ],
          "deferrability": "DEFERRABLE INITIALLY DEFERRED",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "command_ref"
          ],
          "parent_table": "development_author_commands",
          "role": "author_effect_fence_command"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "cancellation_target_effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "effect_fence_cancellation_target_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "cancellation_target_effect_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "parent_table": "development_effect_fences",
          "role": "effect_fence_cancellation_target_fence"
        }
      ],
      "future_mutation_owner": "effect_establishment",
      "immutable_triggers": [
        "development_effect_fences_no_update",
        "development_effect_fences_no_delete"
      ],
      "mutable": False,
      "name": "development_effect_fences",
      "primary_key": [
        "effect_fence_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "attempt_fence_command_effect_aggregate"
      ],
      "record_schema_id": "governed-execution.nwp-effect-fence.v1",
      "role": "effect_fence_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [
        {
          "name": "effect_fence_cancellation_algebra",
          "sql": "((effect_class='cancel_effect' AND cancellation_target_effect_intent_ref IS NOT NULL AND cancellation_target_effect_fence_ref IS NOT NULL AND cancellation_target_effect_fence_digest IS NOT NULL) OR (effect_class<>'cancel_effect' AND cancellation_target_effect_intent_ref IS NULL AND cancellation_target_effect_fence_ref IS NULL AND cancellation_target_effect_fence_digest IS NULL))"
        },
        {
          "name": "effect_fence_capsule_algebra",
          "sql": "((effect_class='author_candidate' AND portable_capsule_digest IS NULL) OR (effect_class IN ('validate_candidate','review_candidate','local_git_commit') AND portable_capsule_digest IS NOT NULL) OR effect_class='cancel_effect')"
        }
      ],
      "timestamp_participation": {
        "expires_at": True,
        "recorded_at": False
      },
      "unique_constraints": [
        [
          "program_ref",
          "effect_fence_ref"
        ],
        [
          "program_ref",
          "effect_intent_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-worker-command.v1'",
          "constant": "governed-execution.nwp-worker-command.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(command_ref)='text' AND length(command_ref) BETWEEN 1 AND 96 AND substr(command_ref,1,1) GLOB '[0-9A-Za-z]' AND command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(command_ref,1,instr(command_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "command_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(accepted_intent_revision_ref)='text' AND length(accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(accepted_intent_revision_ref,1,instr(accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "accepted_intent_revision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_ref)='text' AND length(work_item_ref) BETWEEN 1 AND 96 AND substr(work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_ref,1,instr(work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_item_revision_ref)='text' AND length(work_item_revision_ref) BETWEEN 1 AND 96 AND substr(work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_item_revision_ref,1,instr(work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_item_revision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "semantic_attempt_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "effect_intent_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_class)='text' AND effect_class='author_candidate'",
          "constant": "author_candidate",
          "enum_values": None,
          "logical_type": "constant_text",
          "name": "effect_class",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(candidate_ref)='text' AND length(candidate_ref) BETWEEN 1 AND 96 AND substr(candidate_ref,1,1) GLOB '[0-9A-Za-z]' AND candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(candidate_ref,1,instr(candidate_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "candidate_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(repository_ref)='text' AND length(repository_ref) BETWEEN 1 AND 96 AND substr(repository_ref,1,1) GLOB '[0-9A-Za-z]' AND repository_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(repository_ref,1,instr(repository_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "repository_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(base_git_object_format)='text' AND base_git_object_format='sha1'",
          "constant": "sha1",
          "enum_values": None,
          "logical_type": "constant_text",
          "name": "base_git_object_format",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(base_git_oid)='text' AND length(base_git_oid)=40 AND base_git_oid=lower(base_git_oid) AND base_git_oid NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "git_sha1_oid",
          "name": "base_git_oid",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": "[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]",
          "check_sql": "typeof(path_ceiling_json)='text' AND path_ceiling_json='[\".docs/system_overview/hybrid_integration_architecture_adr.md\",\"PLANS.md\",\"docs_contract_test.go\"]'",
          "constant": None,
          "enum_values": None,
          "logical_type": "canonical_json",
          "name": "path_ceiling_json",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_spec_ref)='text' AND length(work_spec_ref) BETWEEN 1 AND 96 AND substr(work_spec_ref,1,1) GLOB '[0-9A-Za-z]' AND work_spec_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(work_spec_ref,1,instr(work_spec_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "work_spec_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(work_spec_digest)='text' AND length(work_spec_digest)=64 AND work_spec_digest=lower(work_spec_digest) AND work_spec_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "work_spec_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(standing_grant_ref)='text' AND length(standing_grant_ref) BETWEEN 1 AND 96 AND substr(standing_grant_ref,1,1) GLOB '[0-9A-Za-z]' AND standing_grant_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(standing_grant_ref,1,instr(standing_grant_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "standing_grant_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(standing_grant_digest)='text' AND length(standing_grant_digest)=64 AND standing_grant_digest=lower(standing_grant_digest) AND standing_grant_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "standing_grant_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(attempt_authorization_ref)='text' AND length(attempt_authorization_ref) BETWEEN 1 AND 96 AND substr(attempt_authorization_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_authorization_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(attempt_authorization_ref,1,instr(attempt_authorization_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "attempt_authorization_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(attempt_authorization_digest)='text' AND length(attempt_authorization_digest)=64 AND attempt_authorization_digest=lower(attempt_authorization_digest) AND attempt_authorization_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "attempt_authorization_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_authorization_ref)='text' AND length(effect_authorization_ref) BETWEEN 1 AND 96 AND substr(effect_authorization_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_authorization_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_authorization_ref,1,instr(effect_authorization_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "effect_authorization_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_authorization_digest)='text' AND length(effect_authorization_digest)=64 AND effect_authorization_digest=lower(effect_authorization_digest) AND effect_authorization_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "effect_authorization_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(attempt_fence_ref)='text' AND length(attempt_fence_ref) BETWEEN 1 AND 96 AND substr(attempt_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(attempt_fence_ref,1,instr(attempt_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "attempt_fence_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(attempt_fence_digest)='text' AND length(attempt_fence_digest)=64 AND attempt_fence_digest=lower(attempt_fence_digest) AND attempt_fence_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "attempt_fence_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_fence_ref)='text' AND length(effect_fence_ref) BETWEEN 1 AND 96 AND substr(effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_fence_ref,1,instr(effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "effect_fence_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_fence_digest)='text' AND length(effect_fence_digest)=64 AND effect_fence_digest=lower(effect_fence_digest) AND effect_fence_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "effect_fence_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(global_stop_ref)='text' AND length(global_stop_ref) BETWEEN 1 AND 96 AND substr(global_stop_ref,1,1) GLOB '[0-9A-Za-z]' AND global_stop_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(global_stop_ref,1,instr(global_stop_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "global_stop_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(global_stop_version)='integer' AND global_stop_version>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "global_stop_version",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(validation_requirement_ref)='text' AND length(validation_requirement_ref) BETWEEN 1 AND 96 AND substr(validation_requirement_ref,1,1) GLOB '[0-9A-Za-z]' AND validation_requirement_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(validation_requirement_ref,1,instr(validation_requirement_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "validation_requirement_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(validation_requirement_digest)='text' AND length(validation_requirement_digest)=64 AND validation_requirement_digest=lower(validation_requirement_digest) AND validation_requirement_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "validation_requirement_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(review_requirement_ref)='text' AND length(review_requirement_ref) BETWEEN 1 AND 96 AND substr(review_requirement_ref,1,1) GLOB '[0-9A-Za-z]' AND review_requirement_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(review_requirement_ref,1,instr(review_requirement_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "review_requirement_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(review_requirement_digest)='text' AND length(review_requirement_digest)=64 AND review_requirement_digest=lower(review_requirement_digest) AND review_requirement_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "review_requirement_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(capsule_schema_id)='text' AND capsule_schema_id='governed-execution.nwp-candidate-capsule-manifest.v1'",
          "constant": "governed-execution.nwp-candidate-capsule-manifest.v1",
          "enum_values": None,
          "logical_type": "constant_text",
          "name": "capsule_schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(capsule_profile_ref)='text' AND length(capsule_profile_ref) BETWEEN 1 AND 96 AND substr(capsule_profile_ref,1,1) GLOB '[0-9A-Za-z]' AND capsule_profile_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(capsule_profile_ref,1,instr(capsule_profile_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "capsule_profile_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_active_invocations)='integer' AND effect_max_active_invocations>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_active_invocations",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_candidate_bytes)='integer' AND effect_max_candidate_bytes>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_candidate_bytes",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_changed_files)='integer' AND effect_max_changed_files>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_changed_files",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_cost_microusd)='integer' AND effect_max_cost_microusd>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_cost_microusd",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_cpu_seconds)='integer' AND effect_max_cpu_seconds>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_cpu_seconds",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_deliveries)='integer' AND effect_max_deliveries>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_deliveries",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_deployments)='integer' AND effect_max_deployments>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_deployments",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_local_commits)='integer' AND effect_max_local_commits>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_local_commits",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_memory_bytes)='integer' AND effect_max_memory_bytes>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_memory_bytes",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_merges)='integer' AND effect_max_merges>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_merges",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_model_input_tokens)='integer' AND effect_max_model_input_tokens>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_model_input_tokens",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_model_output_tokens)='integer' AND effect_max_model_output_tokens>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_model_output_tokens",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_pull_requests)='integer' AND effect_max_pull_requests>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_pull_requests",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_pushes)='integer' AND effect_max_pushes>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_pushes",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_max_wall_seconds)='integer' AND effect_max_wall_seconds>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "effect_max_wall_seconds",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(privacy_classification)='text' AND privacy_classification='private_source_change'",
          "constant": "private_source_change",
          "enum_values": None,
          "logical_type": "constant_text",
          "name": "privacy_classification",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(redaction_profile_ref)='text' AND length(redaction_profile_ref) BETWEEN 1 AND 96 AND substr(redaction_profile_ref,1,1) GLOB '[0-9A-Za-z]' AND redaction_profile_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(redaction_profile_ref,1,instr(redaction_profile_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "redaction_profile_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(command_digest)='text' AND length(command_digest)=64 AND command_digest=lower(command_digest) AND command_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "command_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "recorded_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "command_digest",
      "digest_domain": "governed-execution.nwp-worker-command.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "command_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "effect_class",
        "candidate_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "path_ceiling_json",
        "work_spec_ref",
        "work_spec_digest",
        "standing_grant_ref",
        "standing_grant_digest",
        "attempt_authorization_ref",
        "attempt_authorization_digest",
        "effect_authorization_ref",
        "effect_authorization_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "global_stop_ref",
        "global_stop_version",
        "validation_requirement_ref",
        "validation_requirement_digest",
        "review_requirement_ref",
        "review_requirement_digest",
        "capsule_schema_id",
        "capsule_profile_ref",
        "effect_max_active_invocations",
        "effect_max_candidate_bytes",
        "effect_max_changed_files",
        "effect_max_cost_microusd",
        "effect_max_cpu_seconds",
        "effect_max_deliveries",
        "effect_max_deployments",
        "effect_max_local_commits",
        "effect_max_memory_bytes",
        "effect_max_merges",
        "effect_max_model_input_tokens",
        "effect_max_model_output_tokens",
        "effect_max_pull_requests",
        "effect_max_pushes",
        "effect_max_wall_seconds",
        "privacy_classification",
        "redaction_profile_ref"
      ],
      "excluded_operational_fields": [
        "effect_fence_digest",
        "recorded_at"
      ],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "author_command_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "author_command_accepted_intent_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "author_command_work_item_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "author_command_semantic_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "author_command_author_effect_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "attempt_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "attempt_fence_ref"
          ],
          "parent_table": "development_attempt_fences",
          "role": "author_command_attempt_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "parent_table": "development_effect_fences",
          "role": "author_command_effect_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "work_spec_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "work_spec_ref"
          ],
          "parent_table": "development_work_spec_bindings",
          "role": "author_command_work_spec_binding"
        }
      ],
      "future_mutation_owner": "_establish_development_author_effect_intent",
      "immutable_triggers": [
        "development_author_commands_no_update",
        "development_author_commands_no_delete"
      ],
      "mutable": False,
      "name": "development_author_commands",
      "primary_key": [
        "command_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "attempt_fence_command_effect_aggregate"
      ],
      "record_schema_id": "governed-execution.nwp-worker-command.v1",
      "role": "author_command_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [],
      "timestamp_participation": {
        "recorded_at": False
      },
      "unique_constraints": [
        [
          "program_ref",
          "command_ref"
        ],
        [
          "effect_intent_ref"
        ],
        [
          "candidate_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-effect-head.v1'",
          "constant": "governed-execution.nwp-development-effect-head.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "effect_intent_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(current_effect_fence_ref)='text' AND length(current_effect_fence_ref) BETWEEN 1 AND 96 AND substr(current_effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND current_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(current_effect_fence_ref,1,instr(current_effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "current_effect_fence_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(head_revision)='integer' AND head_revision>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "head_revision",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_state)='text' AND effect_state IN ('ready_for_delivery','delivery_pending','delivery_outcome_unknown','observed','cancellation_effect_established','terminal')",
          "constant": None,
          "enum_values": [
            "ready_for_delivery",
            "delivery_pending",
            "delivery_outcome_unknown",
            "observed",
            "cancellation_effect_established",
            "terminal"
          ],
          "logical_type": "closed_enum",
          "name": "effect_state",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "cancellation_effect_intent_ref IS NULL OR (typeof(cancellation_effect_intent_ref)='text' AND length(cancellation_effect_intent_ref) BETWEEN 1 AND 96 AND substr(cancellation_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND cancellation_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(cancellation_effect_intent_ref,1,instr(cancellation_effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "cancellation_effect_intent_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(updated_at)='text' AND length(updated_at)=20 AND updated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(updated_at,1,4) BETWEEN '0001' AND '9999' AND substr(updated_at,6,2) BETWEEN '01' AND '12' AND substr(updated_at,9,2) BETWEEN '01' AND '31' AND substr(updated_at,12,2) BETWEEN '00' AND '23' AND substr(updated_at,15,2) BETWEEN '00' AND '59' AND substr(updated_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at)=updated_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "updated_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(head_digest)='text' AND length(head_digest)=64 AND head_digest=lower(head_digest) AND head_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "head_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "head_digest",
      "digest_domain": "governed-execution.nwp-development-effect-head.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "effect_intent_ref",
        "program_ref",
        "current_effect_fence_ref",
        "head_revision",
        "effect_state",
        "cancellation_effect_intent_ref",
        "updated_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "effect_head_effect_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "current_effect_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "parent_table": "development_effect_fences",
          "role": "effect_head_current_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "cancellation_effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "effect_head_cancellation_effect"
        }
      ],
      "future_mutation_owner": "effect_head_CAS",
      "immutable_triggers": [],
      "mutable": True,
      "name": "development_effect_heads",
      "primary_key": [
        "effect_intent_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "effect_head"
      ],
      "record_schema_id": "governed-execution.nwp-development-effect-head.v1",
      "role": "effect_progression_head",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [
        {
          "name": "effect_head_cancellation_algebra",
          "sql": "((effect_state='cancellation_effect_established' AND cancellation_effect_intent_ref IS NOT NULL) OR (effect_state<>'cancellation_effect_established' AND cancellation_effect_intent_ref IS NULL))"
        }
      ],
      "timestamp_participation": {
        "updated_at": True
      },
      "unique_constraints": [
        [
          "program_ref",
          "effect_intent_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-delivery-envelope.v1'",
          "constant": "governed-execution.nwp-delivery-envelope.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(delivery_attempt_ref)='text' AND length(delivery_attempt_ref) BETWEEN 1 AND 96 AND substr(delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(delivery_attempt_ref,1,instr(delivery_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "delivery_attempt_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_version_ref)='text' AND length(program_version_ref) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_version_ref,1,instr(program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_version_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(command_ref)='text' AND length(command_ref) BETWEEN 1 AND 96 AND substr(command_ref,1,1) GLOB '[0-9A-Za-z]' AND command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(command_ref,1,instr(command_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "command_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(command_digest)='text' AND length(command_digest)=64 AND command_digest=lower(command_digest) AND command_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "command_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(semantic_attempt_ref)='text' AND length(semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(semantic_attempt_ref,1,instr(semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "semantic_attempt_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "effect_intent_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(attempt_fence_ref)='text' AND length(attempt_fence_ref) BETWEEN 1 AND 96 AND substr(attempt_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(attempt_fence_ref,1,instr(attempt_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "attempt_fence_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(attempt_fence_digest)='text' AND length(attempt_fence_digest)=64 AND attempt_fence_digest=lower(attempt_fence_digest) AND attempt_fence_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "attempt_fence_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_fence_ref)='text' AND length(effect_fence_ref) BETWEEN 1 AND 96 AND substr(effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_fence_ref,1,instr(effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "effect_fence_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_fence_digest)='text' AND length(effect_fence_digest)=64 AND effect_fence_digest=lower(effect_fence_digest) AND effect_fence_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "effect_fence_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(adapter_kind)='text' AND adapter_kind IN ('direct_local_bootstrap','execution_substrate')",
          "constant": None,
          "enum_values": [
            "direct_local_bootstrap",
            "execution_substrate"
          ],
          "logical_type": "closed_enum",
          "name": "adapter_kind",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(adapter_safe_correlation_ref)='text' AND length(adapter_safe_correlation_ref) BETWEEN 1 AND 96 AND substr(adapter_safe_correlation_ref,1,1) GLOB '[0-9A-Za-z]' AND adapter_safe_correlation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(adapter_safe_correlation_ref,1,instr(adapter_safe_correlation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "adapter_safe_correlation_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(delivery_envelope_digest)='text' AND length(delivery_envelope_digest)=64 AND delivery_envelope_digest=lower(delivery_envelope_digest) AND delivery_envelope_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "delivery_envelope_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(delivery_kind)='text' AND delivery_kind IN ('initial','redelivery')",
          "constant": None,
          "enum_values": [
            "initial",
            "redelivery"
          ],
          "logical_type": "closed_enum",
          "name": "delivery_kind",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(delivery_number)='integer' AND delivery_number>=1",
          "constant": None,
          "enum_values": None,
          "logical_type": "positive_integer",
          "name": "delivery_number",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "predecessor_delivery_attempt_ref IS NULL OR (typeof(predecessor_delivery_attempt_ref)='text' AND length(predecessor_delivery_attempt_ref) BETWEEN 1 AND 96 AND substr(predecessor_delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND predecessor_delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(predecessor_delivery_attempt_ref,1,instr(predecessor_delivery_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "predecessor_delivery_attempt_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(basis_decision_ref)='text' AND length(basis_decision_ref) BETWEEN 1 AND 96 AND substr(basis_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND basis_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(basis_decision_ref,1,instr(basis_decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "basis_decision_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(recorded_at)='text' AND length(recorded_at)=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(recorded_at,1,4) BETWEEN '0001' AND '9999' AND substr(recorded_at,6,2) BETWEEN '01' AND '12' AND substr(recorded_at,9,2) BETWEEN '01' AND '31' AND substr(recorded_at,12,2) BETWEEN '00' AND '23' AND substr(recorded_at,15,2) BETWEEN '00' AND '59' AND substr(recorded_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "recorded_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(delivery_attempt_digest)='text' AND length(delivery_attempt_digest)=64 AND delivery_attempt_digest=lower(delivery_attempt_digest) AND delivery_attempt_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "delivery_attempt_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "derived_literal_identity_fields": {
        "schema_id": "governed-execution.nwp-development-delivery-attempt.v1"
      },
      "digest_column": "delivery_attempt_digest",
      "digest_domain": "governed-execution.nwp-development-delivery-attempt.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "delivery_envelope_digest",
        "delivery_kind",
        "delivery_number",
        "predecessor_delivery_attempt_ref",
        "basis_decision_ref",
        "recorded_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "delivery_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "command_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "command_ref"
          ],
          "parent_table": "development_author_commands",
          "role": "delivery_originating_command"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "delivery_semantic_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "delivery_effect_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "attempt_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "attempt_fence_ref"
          ],
          "parent_table": "development_attempt_fences",
          "role": "delivery_attempt_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "parent_table": "development_effect_fences",
          "role": "delivery_effect_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "predecessor_delivery_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "delivery_attempt_ref"
          ],
          "parent_table": "development_delivery_attempts",
          "role": "delivery_predecessor"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "basis_decision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "decision_ref"
          ],
          "parent_table": "development_decisions",
          "role": "delivery_basis_decision"
        }
      ],
      "future_mutation_owner": "effect_establishment_or_redelivery_decision",
      "immutable_triggers": [
        "development_delivery_attempts_no_update",
        "development_delivery_attempts_no_delete"
      ],
      "mutable": False,
      "name": "development_delivery_attempts",
      "nested_digest_contracts": [
        {
          "digest_column": "delivery_envelope_digest",
          "domain": "governed-execution.nwp-delivery-envelope.v1.identity",
          "identity_fields": [
            "schema_id",
            "delivery_attempt_ref",
            "program_ref",
            "program_version_ref",
            "command_ref",
            "command_digest",
            "semantic_attempt_ref",
            "effect_intent_ref",
            "attempt_fence_ref",
            "attempt_fence_digest",
            "effect_fence_ref",
            "effect_fence_digest",
            "adapter_kind",
            "adapter_safe_correlation_ref"
          ],
          "schema_id": "governed-execution.nwp-delivery-envelope.v1",
          "self_digest_excluded": True
        }
      ],
      "primary_key": [
        "delivery_attempt_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "delivery_head"
      ],
      "record_schema_id": "governed-execution.nwp-development-delivery-attempt.v1",
      "role": "delivery_attempt_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [
        {
          "name": "delivery_predecessor_algebra",
          "sql": "((delivery_kind='initial' AND delivery_number=1 AND predecessor_delivery_attempt_ref IS NULL) OR (delivery_kind='redelivery' AND delivery_number>=2 AND predecessor_delivery_attempt_ref IS NOT NULL))"
        }
      ],
      "timestamp_participation": {
        "recorded_at": True
      },
      "unique_constraints": [
        [
          "program_ref",
          "delivery_attempt_ref"
        ],
        [
          "program_ref",
          "effect_intent_ref",
          "delivery_number"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-delivery-head.v1'",
          "constant": "governed-execution.nwp-development-delivery-head.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(effect_intent_ref)='text' AND length(effect_intent_ref) BETWEEN 1 AND 96 AND substr(effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(effect_intent_ref,1,instr(effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "effect_intent_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(current_delivery_attempt_ref)='text' AND length(current_delivery_attempt_ref) BETWEEN 1 AND 96 AND substr(current_delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND current_delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(current_delivery_attempt_ref,1,instr(current_delivery_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "current_delivery_attempt_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(head_revision)='integer' AND head_revision>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "head_revision",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(delivery_state)='text' AND delivery_state IN ('planned','submitted','outcome_unknown','acknowledged','rejected','completed')",
          "constant": None,
          "enum_values": [
            "planned",
            "submitted",
            "outcome_unknown",
            "acknowledged",
            "rejected",
            "completed"
          ],
          "logical_type": "closed_enum",
          "name": "delivery_state",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(updated_at)='text' AND length(updated_at)=20 AND updated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(updated_at,1,4) BETWEEN '0001' AND '9999' AND substr(updated_at,6,2) BETWEEN '01' AND '12' AND substr(updated_at,9,2) BETWEEN '01' AND '31' AND substr(updated_at,12,2) BETWEEN '00' AND '23' AND substr(updated_at,15,2) BETWEEN '00' AND '59' AND substr(updated_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',updated_at)=updated_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "updated_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(head_digest)='text' AND length(head_digest)=64 AND head_digest=lower(head_digest) AND head_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "head_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "head_digest",
      "digest_domain": "governed-execution.nwp-development-delivery-head.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "effect_intent_ref",
        "program_ref",
        "current_delivery_attempt_ref",
        "head_revision",
        "delivery_state",
        "updated_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "delivery_head_effect_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "current_delivery_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "delivery_attempt_ref"
          ],
          "parent_table": "development_delivery_attempts",
          "role": "delivery_head_current_delivery_attempt"
        }
      ],
      "future_mutation_owner": "delivery_head_CAS",
      "immutable_triggers": [],
      "mutable": True,
      "name": "development_delivery_heads",
      "primary_key": [
        "effect_intent_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "delivery_head"
      ],
      "record_schema_id": "governed-execution.nwp-development-delivery-head.v1",
      "role": "delivery_progression_head",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [],
      "timestamp_participation": {
        "updated_at": True
      },
      "unique_constraints": [
        [
          "program_ref",
          "effect_intent_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-decision.v1'",
          "constant": "governed-execution.nwp-development-decision.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(mutation_ref)='text' AND length(mutation_ref) BETWEEN 1 AND 96 AND substr(mutation_ref,1,1) GLOB '[0-9A-Za-z]' AND mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(mutation_ref,1,instr(mutation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "mutation_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(decision_ref)='text' AND length(decision_ref) BETWEEN 1 AND 96 AND substr(decision_ref,1,1) GLOB '[0-9A-Za-z]' AND decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(decision_ref,1,instr(decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "decision_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(decision_kind)='text' AND decision_kind IN ('initialize','accept','repair','replan','terminal_reject','block','redeliver','cancel')",
          "constant": None,
          "enum_values": [
            "initialize",
            "accept",
            "repair",
            "replan",
            "terminal_reject",
            "block",
            "redeliver",
            "cancel"
          ],
          "logical_type": "closed_enum",
          "name": "decision_kind",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(decision_variant)='text' AND decision_variant IN ('program_genesis','candidate_acceptance','candidate_repair','program_replan','attempt_selecting_replan','program_terminal_reject','program_block','productive_redelivery','cancellation_redelivery','effect_cancellation')",
          "constant": None,
          "enum_values": [
            "program_genesis",
            "candidate_acceptance",
            "candidate_repair",
            "program_replan",
            "attempt_selecting_replan",
            "program_terminal_reject",
            "program_block",
            "productive_redelivery",
            "cancellation_redelivery",
            "effect_cancellation"
          ],
          "logical_type": "closed_enum",
          "name": "decision_variant",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "basis_decision_ref IS NULL OR (typeof(basis_decision_ref)='text' AND length(basis_decision_ref) BETWEEN 1 AND 96 AND substr(basis_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND basis_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(basis_decision_ref,1,instr(basis_decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "basis_decision_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "basis_program_version_ref IS NULL OR (typeof(basis_program_version_ref)='text' AND length(basis_program_version_ref) BETWEEN 1 AND 96 AND substr(basis_program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND basis_program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(basis_program_version_ref,1,instr(basis_program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "basis_program_version_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "basis_program_version_number IS NULL OR (typeof(basis_program_version_number)='integer' AND basis_program_version_number>=1)",
          "constant": None,
          "enum_values": None,
          "logical_type": "positive_integer",
          "name": "basis_program_version_number",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(expected_program_head_revision)='integer' AND expected_program_head_revision>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "expected_program_head_revision",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "resulting_program_version_ref IS NULL OR (typeof(resulting_program_version_ref)='text' AND length(resulting_program_version_ref) BETWEEN 1 AND 96 AND substr(resulting_program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND resulting_program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(resulting_program_version_ref,1,instr(resulting_program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "resulting_program_version_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "resulting_program_version_number IS NULL OR (typeof(resulting_program_version_number)='integer' AND resulting_program_version_number>=1)",
          "constant": None,
          "enum_values": None,
          "logical_type": "positive_integer",
          "name": "resulting_program_version_number",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "selected_semantic_attempt_ref IS NULL OR (typeof(selected_semantic_attempt_ref)='text' AND length(selected_semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(selected_semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND selected_semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(selected_semantic_attempt_ref,1,instr(selected_semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "selected_semantic_attempt_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "selected_candidate_ref IS NULL OR (typeof(selected_candidate_ref)='text' AND length(selected_candidate_ref) BETWEEN 1 AND 96 AND substr(selected_candidate_ref,1,1) GLOB '[0-9A-Za-z]' AND selected_candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(selected_candidate_ref,1,instr(selected_candidate_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "selected_candidate_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "selected_attempt_fence_ref IS NULL OR (typeof(selected_attempt_fence_ref)='text' AND length(selected_attempt_fence_ref) BETWEEN 1 AND 96 AND substr(selected_attempt_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND selected_attempt_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(selected_attempt_fence_ref,1,instr(selected_attempt_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "selected_attempt_fence_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "selected_attempt_fence_digest IS NULL OR (typeof(selected_attempt_fence_digest)='text' AND length(selected_attempt_fence_digest)=64 AND selected_attempt_fence_digest=lower(selected_attempt_fence_digest) AND selected_attempt_fence_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "selected_attempt_fence_digest",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "target_effect_intent_ref IS NULL OR (typeof(target_effect_intent_ref)='text' AND length(target_effect_intent_ref) BETWEEN 1 AND 96 AND substr(target_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND target_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(target_effect_intent_ref,1,instr(target_effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "target_effect_intent_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "target_effect_class IS NULL OR (typeof(target_effect_class)='text' AND target_effect_class IN ('author_candidate','cancel_effect','local_git_commit','review_candidate','validate_candidate'))",
          "constant": None,
          "enum_values": [
            "author_candidate",
            "cancel_effect",
            "local_git_commit",
            "review_candidate",
            "validate_candidate"
          ],
          "logical_type": "closed_enum",
          "name": "target_effect_class",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "target_effect_fence_ref IS NULL OR (typeof(target_effect_fence_ref)='text' AND length(target_effect_fence_ref) BETWEEN 1 AND 96 AND substr(target_effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND target_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(target_effect_fence_ref,1,instr(target_effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "target_effect_fence_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "target_effect_fence_digest IS NULL OR (typeof(target_effect_fence_digest)='text' AND length(target_effect_fence_digest)=64 AND target_effect_fence_digest=lower(target_effect_fence_digest) AND target_effect_fence_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "target_effect_fence_digest",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "expected_target_effect_head_revision IS NULL OR (typeof(expected_target_effect_head_revision)='integer' AND expected_target_effect_head_revision>=0)",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "expected_target_effect_head_revision",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "target_delivery_attempt_ref IS NULL OR (typeof(target_delivery_attempt_ref)='text' AND length(target_delivery_attempt_ref) BETWEEN 1 AND 96 AND substr(target_delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND target_delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(target_delivery_attempt_ref,1,instr(target_delivery_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "target_delivery_attempt_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "originating_command_ref IS NULL OR (typeof(originating_command_ref)='text' AND length(originating_command_ref) BETWEEN 1 AND 96 AND substr(originating_command_ref,1,1) GLOB '[0-9A-Za-z]' AND originating_command_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(originating_command_ref,1,instr(originating_command_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "originating_command_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "originating_command_digest IS NULL OR (typeof(originating_command_digest)='text' AND length(originating_command_digest)=64 AND originating_command_digest=lower(originating_command_digest) AND originating_command_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "originating_command_digest",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "target_capsule_manifest_ref IS NULL OR (typeof(target_capsule_manifest_ref)='text' AND length(target_capsule_manifest_ref) BETWEEN 1 AND 96 AND substr(target_capsule_manifest_ref,1,1) GLOB '[0-9A-Za-z]' AND target_capsule_manifest_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(target_capsule_manifest_ref,1,instr(target_capsule_manifest_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "target_capsule_manifest_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "target_portable_capsule_digest IS NULL OR (typeof(target_portable_capsule_digest)='text' AND length(target_portable_capsule_digest)=64 AND target_portable_capsule_digest=lower(target_portable_capsule_digest) AND target_portable_capsule_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "target_portable_capsule_digest",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(coding_global_stop_ref)='text' AND length(coding_global_stop_ref) BETWEEN 1 AND 96 AND substr(coding_global_stop_ref,1,1) GLOB '[0-9A-Za-z]' AND coding_global_stop_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(coding_global_stop_ref,1,instr(coding_global_stop_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "coding_global_stop_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(coding_global_stop_version)='integer' AND coding_global_stop_version>=0",
          "constant": None,
          "enum_values": None,
          "logical_type": "nonnegative_integer",
          "name": "coding_global_stop_version",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "source_directive_ref IS NULL OR (typeof(source_directive_ref)='text' AND length(source_directive_ref) BETWEEN 1 AND 96 AND substr(source_directive_ref,1,1) GLOB '[0-9A-Za-z]' AND source_directive_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(source_directive_ref,1,instr(source_directive_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "source_directive_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "source_directive_digest IS NULL OR (typeof(source_directive_digest)='text' AND length(source_directive_digest)=64 AND source_directive_digest=lower(source_directive_digest) AND source_directive_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "source_directive_digest",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "source_evidence_ref IS NULL OR (typeof(source_evidence_ref)='text' AND length(source_evidence_ref) BETWEEN 1 AND 96 AND substr(source_evidence_ref,1,1) GLOB '[0-9A-Za-z]' AND source_evidence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(source_evidence_ref,1,instr(source_evidence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "source_evidence_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "source_evidence_digest IS NULL OR (typeof(source_evidence_digest)='text' AND length(source_evidence_digest)=64 AND source_evidence_digest=lower(source_evidence_digest) AND source_evidence_digest NOT GLOB '*[^0-9a-f]*')",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "source_evidence_digest",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "preassigned_semantic_attempt_ref IS NULL OR (typeof(preassigned_semantic_attempt_ref)='text' AND length(preassigned_semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(preassigned_semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND preassigned_semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(preassigned_semantic_attempt_ref,1,instr(preassigned_semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "preassigned_semantic_attempt_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "preassigned_candidate_ref IS NULL OR (typeof(preassigned_candidate_ref)='text' AND length(preassigned_candidate_ref) BETWEEN 1 AND 96 AND substr(preassigned_candidate_ref,1,1) GLOB '[0-9A-Za-z]' AND preassigned_candidate_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(preassigned_candidate_ref,1,instr(preassigned_candidate_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "preassigned_candidate_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "preassigned_effect_intent_ref IS NULL OR (typeof(preassigned_effect_intent_ref)='text' AND length(preassigned_effect_intent_ref) BETWEEN 1 AND 96 AND substr(preassigned_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND preassigned_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(preassigned_effect_intent_ref,1,instr(preassigned_effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "preassigned_effect_intent_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "preassigned_effect_fence_ref IS NULL OR (typeof(preassigned_effect_fence_ref)='text' AND length(preassigned_effect_fence_ref) BETWEEN 1 AND 96 AND substr(preassigned_effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND preassigned_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(preassigned_effect_fence_ref,1,instr(preassigned_effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "preassigned_effect_fence_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "preassigned_delivery_attempt_ref IS NULL OR (typeof(preassigned_delivery_attempt_ref)='text' AND length(preassigned_delivery_attempt_ref) BETWEEN 1 AND 96 AND substr(preassigned_delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND preassigned_delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(preassigned_delivery_attempt_ref,1,instr(preassigned_delivery_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "preassigned_delivery_attempt_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "resulting_accepted_intent_revision_ref IS NULL OR (typeof(resulting_accepted_intent_revision_ref)='text' AND length(resulting_accepted_intent_revision_ref) BETWEEN 1 AND 96 AND substr(resulting_accepted_intent_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND resulting_accepted_intent_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(resulting_accepted_intent_revision_ref,1,instr(resulting_accepted_intent_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "resulting_accepted_intent_revision_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "resulting_work_item_ref IS NULL OR (typeof(resulting_work_item_ref)='text' AND length(resulting_work_item_ref) BETWEEN 1 AND 96 AND substr(resulting_work_item_ref,1,1) GLOB '[0-9A-Za-z]' AND resulting_work_item_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(resulting_work_item_ref,1,instr(resulting_work_item_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "resulting_work_item_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "resulting_work_item_revision_ref IS NULL OR (typeof(resulting_work_item_revision_ref)='text' AND length(resulting_work_item_revision_ref) BETWEEN 1 AND 96 AND substr(resulting_work_item_revision_ref,1,1) GLOB '[0-9A-Za-z]' AND resulting_work_item_revision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(resulting_work_item_revision_ref,1,instr(resulting_work_item_revision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "resulting_work_item_revision_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(reason_code)='text' AND length(reason_code) BETWEEN 1 AND 96 AND substr(reason_code,1,1) GLOB '[a-z]' AND reason_code NOT GLOB '*[^a-z0-9_.-]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "reason_code",
          "name": "reason_code",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(decided_at)='text' AND length(decided_at)=20 AND decided_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(decided_at,1,4) BETWEEN '0001' AND '9999' AND substr(decided_at,6,2) BETWEEN '01' AND '12' AND substr(decided_at,9,2) BETWEEN '01' AND '31' AND substr(decided_at,12,2) BETWEEN '00' AND '23' AND substr(decided_at,15,2) BETWEEN '00' AND '59' AND substr(decided_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',decided_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',decided_at)=decided_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "decided_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(decision_digest)='text' AND length(decision_digest)=64 AND decision_digest=lower(decision_digest) AND decision_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "decision_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": "decision_digest",
      "digest_domain": "governed-execution.nwp-development-decision.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "mutation_ref",
        "decision_ref",
        "program_ref",
        "decision_kind",
        "decision_variant",
        "basis_decision_ref",
        "basis_program_version_ref",
        "basis_program_version_number",
        "expected_program_head_revision",
        "resulting_program_version_ref",
        "resulting_program_version_number",
        "selected_semantic_attempt_ref",
        "selected_candidate_ref",
        "selected_attempt_fence_ref",
        "selected_attempt_fence_digest",
        "target_effect_intent_ref",
        "target_effect_class",
        "target_effect_fence_ref",
        "target_effect_fence_digest",
        "expected_target_effect_head_revision",
        "target_delivery_attempt_ref",
        "originating_command_ref",
        "originating_command_digest",
        "target_capsule_manifest_ref",
        "target_portable_capsule_digest",
        "coding_global_stop_ref",
        "coding_global_stop_version",
        "source_directive_ref",
        "source_directive_digest",
        "source_evidence_ref",
        "source_evidence_digest",
        "preassigned_semantic_attempt_ref",
        "preassigned_candidate_ref",
        "preassigned_effect_intent_ref",
        "preassigned_effect_fence_ref",
        "preassigned_delivery_attempt_ref",
        "resulting_accepted_intent_revision_ref",
        "resulting_work_item_ref",
        "resulting_work_item_revision_ref",
        "reason_code",
        "decided_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref"
          ],
          "parent_table": "development_program_heads",
          "role": "decision_program"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "basis_decision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "decision_ref"
          ],
          "parent_table": "development_decisions",
          "role": "decision_basis_decision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "basis_program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "decision_basis_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "resulting_program_version_ref"
          ],
          "deferrability": "DEFERRABLE INITIALLY DEFERRED",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "initialize_decision_resulting_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "selected_semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "decision_selected_semantic_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "selected_attempt_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "attempt_fence_ref"
          ],
          "parent_table": "development_attempt_fences",
          "role": "decision_selected_attempt_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "target_effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "decision_target_effect_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "target_effect_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "parent_table": "development_effect_fences",
          "role": "decision_target_effect_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "target_delivery_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "delivery_attempt_ref"
          ],
          "parent_table": "development_delivery_attempts",
          "role": "decision_target_delivery_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "originating_command_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "command_ref"
          ],
          "parent_table": "development_author_commands",
          "role": "decision_originating_command"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "resulting_accepted_intent_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "accepted_intent_revision_ref"
          ],
          "parent_table": "development_accepted_intent_revisions",
          "role": "decision_resulting_accepted_intent_revision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "resulting_work_item_ref",
            "resulting_work_item_revision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "work_item_ref",
            "work_item_revision_ref"
          ],
          "parent_table": "development_work_item_revisions",
          "role": "decision_resulting_work_item_revision"
        }
      ],
      "future_mutation_owner": "_initialize_development_program_or_record_progression_decision",
      "immutable_triggers": [
        "development_decisions_no_update",
        "development_decisions_no_delete"
      ],
      "mutable": False,
      "name": "development_decisions",
      "primary_key": [
        "decision_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "decision_by_decision_ref",
        "initialize_decision_and_resulting_version"
      ],
      "record_schema_id": "governed-execution.nwp-development-decision.v1",
      "role": "development_decision_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [
        {
          "name": "decision_closed_variant_algebra",
          "sql": "((decision_kind='initialize' AND decision_variant='program_genesis' AND basis_decision_ref IS NULL AND basis_program_version_ref IS NULL AND basis_program_version_number IS NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NULL AND selected_candidate_ref IS NULL AND selected_attempt_fence_ref IS NULL AND selected_attempt_fence_digest IS NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND resulting_program_version_number=1 AND expected_program_head_revision=0) OR (decision_kind='accept' AND decision_variant='candidate_acceptance' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL) OR (decision_kind='repair' AND decision_variant='candidate_repair' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL) OR (decision_kind='replan' AND decision_variant='program_replan' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NULL AND selected_candidate_ref IS NULL AND selected_attempt_fence_ref IS NULL AND selected_attempt_fence_digest IS NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NOT NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL) OR (decision_kind='replan' AND decision_variant='attempt_selecting_replan' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NOT NULL AND preassigned_candidate_ref IS NOT NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NOT NULL AND resulting_work_item_ref IS NOT NULL AND resulting_work_item_revision_ref IS NOT NULL) OR (decision_kind='terminal_reject' AND decision_variant='program_terminal_reject' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL) OR (decision_kind='block' AND decision_variant='program_block' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NOT NULL AND resulting_program_version_number IS NOT NULL AND selected_semantic_attempt_ref IS NULL AND selected_candidate_ref IS NULL AND selected_attempt_fence_ref IS NULL AND selected_attempt_fence_digest IS NULL AND target_effect_intent_ref IS NULL AND target_effect_class IS NULL AND target_effect_fence_ref IS NULL AND target_effect_fence_digest IS NULL AND expected_target_effect_head_revision IS NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NULL AND originating_command_digest IS NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL) OR (decision_kind='redeliver' AND decision_variant='productive_redelivery' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NOT NULL AND originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND target_effect_class IN ('author_candidate','validate_candidate','review_candidate')) OR (decision_kind='redeliver' AND decision_variant='cancellation_redelivery' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NOT NULL AND originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL AND source_directive_ref IS NULL AND source_directive_digest IS NULL AND source_evidence_ref IS NULL AND source_evidence_digest IS NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NULL AND preassigned_effect_fence_ref IS NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND target_effect_class='cancel_effect') OR (decision_kind='cancel' AND decision_variant='effect_cancellation' AND basis_decision_ref IS NOT NULL AND basis_program_version_ref IS NOT NULL AND basis_program_version_number IS NOT NULL AND resulting_program_version_ref IS NULL AND resulting_program_version_number IS NULL AND selected_semantic_attempt_ref IS NOT NULL AND selected_candidate_ref IS NOT NULL AND selected_attempt_fence_ref IS NOT NULL AND selected_attempt_fence_digest IS NOT NULL AND target_effect_intent_ref IS NOT NULL AND target_effect_class IS NOT NULL AND target_effect_fence_ref IS NOT NULL AND target_effect_fence_digest IS NOT NULL AND expected_target_effect_head_revision IS NOT NULL AND target_delivery_attempt_ref IS NULL AND originating_command_ref IS NOT NULL AND originating_command_digest IS NOT NULL AND ((target_effect_class='author_candidate' AND target_capsule_manifest_ref IS NULL AND target_portable_capsule_digest IS NULL) OR (target_effect_class IN ('validate_candidate','review_candidate') AND target_capsule_manifest_ref IS NOT NULL AND target_portable_capsule_digest IS NOT NULL)) AND source_directive_ref IS NOT NULL AND source_directive_digest IS NOT NULL AND source_evidence_ref IS NOT NULL AND source_evidence_digest IS NOT NULL AND preassigned_semantic_attempt_ref IS NULL AND preassigned_candidate_ref IS NULL AND preassigned_effect_intent_ref IS NOT NULL AND preassigned_effect_fence_ref IS NOT NULL AND preassigned_delivery_attempt_ref IS NOT NULL AND resulting_accepted_intent_revision_ref IS NULL AND resulting_work_item_ref IS NULL AND resulting_work_item_revision_ref IS NULL AND target_effect_class IN ('author_candidate','validate_candidate','review_candidate')))"
        }
      ],
      "timestamp_participation": {
        "decided_at": True
      },
      "unique_constraints": [
        [
          "program_ref",
          "decision_ref"
        ],
        [
          "mutation_ref"
        ]
      ]
    },
    {
      "columns": [
        {
          "canonical_json_value": None,
          "check_sql": "typeof(schema_id)='text' AND schema_id='governed-execution.nwp-development-mutation-receipt.v1'",
          "constant": "governed-execution.nwp-development-mutation-receipt.v1",
          "enum_values": None,
          "logical_type": "schema_id",
          "name": "schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(mutation_ref)='text' AND length(mutation_ref) BETWEEN 1 AND 96 AND substr(mutation_ref,1,1) GLOB '[0-9A-Za-z]' AND mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(mutation_ref,1,instr(mutation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "mutation_ref",
          "nullable": False,
          "pk_ordinal": 1,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(mutation_family)='text' AND mutation_family IN ('initialize_development_program','establish_development_author_effect_intent','establish_development_bound_effect_intent','ingest_development_source_observation','record_development_progression_decision')",
          "constant": None,
          "enum_values": [
            "initialize_development_program",
            "establish_development_author_effect_intent",
            "establish_development_bound_effect_intent",
            "ingest_development_source_observation",
            "record_development_progression_decision"
          ],
          "logical_type": "closed_enum",
          "name": "mutation_family",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(command_schema_id)='text' AND command_schema_id IN ('governed-execution.nwp-initialize-development-program-command.v1','governed-execution.nwp-establish-development-author-effect-intent-command.v1','governed-execution.nwp-establish-development-bound-effect-intent-command.v1','governed-execution.nwp-ingest-development-source-observation-command.v1','governed-execution.nwp-record-development-progression-decision-command.v1')",
          "constant": None,
          "enum_values": [
            "governed-execution.nwp-initialize-development-program-command.v1",
            "governed-execution.nwp-establish-development-author-effect-intent-command.v1",
            "governed-execution.nwp-establish-development-bound-effect-intent-command.v1",
            "governed-execution.nwp-ingest-development-source-observation-command.v1",
            "governed-execution.nwp-record-development-progression-decision-command.v1"
          ],
          "logical_type": "closed_enum",
          "name": "command_schema_id",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(command_digest)='text' AND length(command_digest)=64 AND command_digest=lower(command_digest) AND command_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "command_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(program_ref)='text' AND length(program_ref) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "program_ref",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "decision_ref IS NULL OR (typeof(decision_ref)='text' AND length(decision_ref) BETWEEN 1 AND 96 AND substr(decision_ref,1,1) GLOB '[0-9A-Za-z]' AND decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(decision_ref,1,instr(decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "decision_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "result_program_version_ref IS NULL OR (typeof(result_program_version_ref)='text' AND length(result_program_version_ref) BETWEEN 1 AND 96 AND substr(result_program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND result_program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_program_version_ref,1,instr(result_program_version_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "result_program_version_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "result_semantic_attempt_ref IS NULL OR (typeof(result_semantic_attempt_ref)='text' AND length(result_semantic_attempt_ref) BETWEEN 1 AND 96 AND substr(result_semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND result_semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_semantic_attempt_ref,1,instr(result_semantic_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "result_semantic_attempt_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "result_effect_intent_ref IS NULL OR (typeof(result_effect_intent_ref)='text' AND length(result_effect_intent_ref) BETWEEN 1 AND 96 AND substr(result_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND result_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_effect_intent_ref,1,instr(result_effect_intent_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "result_effect_intent_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "result_effect_fence_ref IS NULL OR (typeof(result_effect_fence_ref)='text' AND length(result_effect_fence_ref) BETWEEN 1 AND 96 AND substr(result_effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND result_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_effect_fence_ref,1,instr(result_effect_fence_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "result_effect_fence_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "result_delivery_attempt_ref IS NULL OR (typeof(result_delivery_attempt_ref)='text' AND length(result_delivery_attempt_ref) BETWEEN 1 AND 96 AND substr(result_delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND result_delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_delivery_attempt_ref,1,instr(result_delivery_attempt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "result_delivery_attempt_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "result_observation_ref IS NULL OR (typeof(result_observation_ref)='text' AND length(result_observation_ref) BETWEEN 1 AND 96 AND substr(result_observation_ref,1,1) GLOB '[0-9A-Za-z]' AND result_observation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_observation_ref,1,instr(result_observation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "result_observation_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "result_decision_ref IS NULL OR (typeof(result_decision_ref)='text' AND length(result_decision_ref) BETWEEN 1 AND 96 AND substr(result_decision_ref,1,1) GLOB '[0-9A-Za-z]' AND result_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_decision_ref,1,instr(result_decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))",
          "constant": None,
          "enum_values": None,
          "logical_type": "safe_ref",
          "name": "result_decision_ref",
          "nullable": True,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(result_class)='text' AND result_class IN ('development_program_initialized','development_author_effect_intent_established','development_bound_effect_intent_established','development_source_observation_ingested','development_progression_decision_recorded')",
          "constant": None,
          "enum_values": [
            "development_program_initialized",
            "development_author_effect_intent_established",
            "development_bound_effect_intent_established",
            "development_source_observation_ingested",
            "development_progression_decision_recorded"
          ],
          "logical_type": "closed_enum",
          "name": "result_class",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(result_projection_digest)='text' AND length(result_projection_digest)=64 AND result_projection_digest=lower(result_projection_digest) AND result_projection_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "result_projection_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(mutation_graph_digest)='text' AND length(mutation_graph_digest)=64 AND mutation_graph_digest=lower(mutation_graph_digest) AND mutation_graph_digest NOT GLOB '*[^0-9a-f]*'",
          "constant": None,
          "enum_values": None,
          "logical_type": "sha256",
          "name": "mutation_graph_digest",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(outcome)='text' AND outcome='committed'",
          "constant": "committed",
          "enum_values": None,
          "logical_type": "constant_text",
          "name": "outcome",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        },
        {
          "canonical_json_value": None,
          "check_sql": "typeof(committed_at)='text' AND length(committed_at)=20 AND committed_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND substr(committed_at,1,4) BETWEEN '0001' AND '9999' AND substr(committed_at,6,2) BETWEEN '01' AND '12' AND substr(committed_at,9,2) BETWEEN '01' AND '31' AND substr(committed_at,12,2) BETWEEN '00' AND '23' AND substr(committed_at,15,2) BETWEEN '00' AND '59' AND substr(committed_at,18,2) BETWEEN '00' AND '59' AND strftime('%Y-%m-%dT%H:%M:%SZ',committed_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%SZ',committed_at)=committed_at",
          "constant": None,
          "enum_values": None,
          "logical_type": "timestamp",
          "name": "committed_at",
          "nullable": False,
          "pk_ordinal": 0,
          "privacy_class": "safe_operational",
          "sqlite_declaration_type": "ANY"
        }
      ],
      "digest_column": None,
      "digest_domain": "governed-execution.nwp-development-mutation-receipt.v1.identity",
      "exact_digest_identity_fields": [
        "schema_id",
        "mutation_ref",
        "mutation_family",
        "command_schema_id",
        "command_digest",
        "program_ref",
        "decision_ref",
        "result_program_version_ref",
        "result_semantic_attempt_ref",
        "result_effect_intent_ref",
        "result_effect_fence_ref",
        "result_delivery_attempt_ref",
        "result_observation_ref",
        "result_decision_ref",
        "result_class",
        "result_projection_digest",
        "outcome",
        "committed_at"
      ],
      "excluded_operational_fields": [],
      "explicit_indexes": [],
      "foreign_keys": [
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref"
          ],
          "parent_table": "development_program_heads",
          "role": "receipt_program"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "decision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "decision_ref"
          ],
          "parent_table": "development_decisions",
          "role": "receipt_decision"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "result_program_version_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "program_version_ref"
          ],
          "parent_table": "development_program_versions",
          "role": "receipt_result_program_version"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "result_semantic_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "semantic_attempt_ref"
          ],
          "parent_table": "development_semantic_attempts",
          "role": "receipt_result_semantic_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "result_effect_intent_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_intent_ref"
          ],
          "parent_table": "development_effect_intents",
          "role": "receipt_result_effect_intent"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "result_effect_fence_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "effect_fence_ref"
          ],
          "parent_table": "development_effect_fences",
          "role": "receipt_result_effect_fence"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "result_delivery_attempt_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "delivery_attempt_ref"
          ],
          "parent_table": "development_delivery_attempts",
          "role": "receipt_result_delivery_attempt"
        },
        {
          "aggregate_validation_outside_sqlite": "Recompute parent and child row digests and validate relation-specific semantic coherence in the private aggregate reader; mismatch is database_integrity_failure.",
          "child_columns": [
            "program_ref",
            "result_decision_ref"
          ],
          "deferrability": "NOT DEFERRABLE INITIALLY IMMEDIATE",
          "on_delete": "RESTRICT",
          "on_update": "RESTRICT",
          "parent_columns": [
            "program_ref",
            "decision_ref"
          ],
          "parent_table": "development_decisions",
          "role": "receipt_result_decision"
        }
      ],
      "future_mutation_owner": "all_five_C2B_mutation_families",
      "immutable_triggers": [
        "development_mutation_receipts_no_update",
        "development_mutation_receipts_no_delete"
      ],
      "mutable": False,
      "name": "development_mutation_receipts",
      "primary_key": [
        "mutation_ref"
      ],
      "privacy_class": "safe_operational",
      "reader_roles": [
        "mutation_receipt_by_mutation_ref"
      ],
      "record_schema_id": "governed-execution.nwp-development-mutation-receipt.v1",
      "role": "development_mutation_receipt_record",
      "seed_rows": [],
      "self_digest_excluded": True,
      "strict": True,
      "table_checks": [
        {
          "name": "receipt_closed_family_algebra",
          "sql": "((mutation_family='initialize_development_program' AND command_schema_id='governed-execution.nwp-initialize-development-program-command.v1' AND result_class='development_program_initialized' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NULL AND result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND result_delivery_attempt_ref IS NULL AND result_observation_ref IS NULL AND result_decision_ref IS NOT NULL AND result_decision_ref=decision_ref) OR (mutation_family='establish_development_author_effect_intent' AND command_schema_id='governed-execution.nwp-establish-development-author-effect-intent-command.v1' AND result_class='development_author_effect_intent_established' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NOT NULL AND result_effect_intent_ref IS NOT NULL AND result_effect_fence_ref IS NOT NULL AND result_delivery_attempt_ref IS NOT NULL AND result_observation_ref IS NULL AND result_decision_ref IS NULL) OR (mutation_family='establish_development_bound_effect_intent' AND command_schema_id='governed-execution.nwp-establish-development-bound-effect-intent-command.v1' AND result_class='development_bound_effect_intent_established' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NOT NULL AND result_effect_intent_ref IS NOT NULL AND result_effect_fence_ref IS NOT NULL AND result_delivery_attempt_ref IS NOT NULL AND result_observation_ref IS NULL AND result_decision_ref IS NULL) OR (mutation_family='ingest_development_source_observation' AND command_schema_id='governed-execution.nwp-ingest-development-source-observation-command.v1' AND result_class='development_source_observation_ingested' AND decision_ref IS NULL AND result_program_version_ref IS NULL AND result_semantic_attempt_ref IS NULL AND result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND result_delivery_attempt_ref IS NULL AND result_observation_ref IS NOT NULL AND result_decision_ref IS NULL) OR (mutation_family='record_development_progression_decision' AND command_schema_id='governed-execution.nwp-record-development-progression-decision-command.v1' AND result_class='development_progression_decision_recorded' AND decision_ref IS NOT NULL AND result_program_version_ref IS NOT NULL AND result_semantic_attempt_ref IS NULL AND result_effect_intent_ref IS NULL AND result_effect_fence_ref IS NULL AND result_delivery_attempt_ref IS NULL AND result_observation_ref IS NULL AND result_decision_ref IS NOT NULL AND result_decision_ref=decision_ref))"
        }
      ],
      "timestamp_participation": {
        "committed_at": True
      },
      "unique_constraints": []
    }
  ],
  "triggers": [
    {
      "body_sql": "CREATE TRIGGER development_program_versions_no_update\nBEFORE UPDATE ON development_program_versions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_program_versions');\nEND;",
      "diagnostic": "append_only_development_program_versions",
      "name": "development_program_versions_no_update",
      "operation": "UPDATE",
      "table": "development_program_versions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_program_versions_no_delete\nBEFORE DELETE ON development_program_versions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_program_versions');\nEND;",
      "diagnostic": "append_only_development_program_versions",
      "name": "development_program_versions_no_delete",
      "operation": "DELETE",
      "table": "development_program_versions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_accepted_intent_revisions_no_update\nBEFORE UPDATE ON development_accepted_intent_revisions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_accepted_intent_revisions');\nEND;",
      "diagnostic": "append_only_development_accepted_intent_revisions",
      "name": "development_accepted_intent_revisions_no_update",
      "operation": "UPDATE",
      "table": "development_accepted_intent_revisions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_accepted_intent_revisions_no_delete\nBEFORE DELETE ON development_accepted_intent_revisions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_accepted_intent_revisions');\nEND;",
      "diagnostic": "append_only_development_accepted_intent_revisions",
      "name": "development_accepted_intent_revisions_no_delete",
      "operation": "DELETE",
      "table": "development_accepted_intent_revisions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_work_item_revisions_no_update\nBEFORE UPDATE ON development_work_item_revisions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_work_item_revisions');\nEND;",
      "diagnostic": "append_only_development_work_item_revisions",
      "name": "development_work_item_revisions_no_update",
      "operation": "UPDATE",
      "table": "development_work_item_revisions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_work_item_revisions_no_delete\nBEFORE DELETE ON development_work_item_revisions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_work_item_revisions');\nEND;",
      "diagnostic": "append_only_development_work_item_revisions",
      "name": "development_work_item_revisions_no_delete",
      "operation": "DELETE",
      "table": "development_work_item_revisions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_program_version_work_items_no_update\nBEFORE UPDATE ON development_program_version_work_items\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_program_version_work_items');\nEND;",
      "diagnostic": "append_only_development_program_version_work_items",
      "name": "development_program_version_work_items_no_update",
      "operation": "UPDATE",
      "table": "development_program_version_work_items",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_program_version_work_items_no_delete\nBEFORE DELETE ON development_program_version_work_items\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_program_version_work_items');\nEND;",
      "diagnostic": "append_only_development_program_version_work_items",
      "name": "development_program_version_work_items_no_delete",
      "operation": "DELETE",
      "table": "development_program_version_work_items",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_revision_edges_no_update\nBEFORE UPDATE ON development_revision_edges\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_revision_edges');\nEND;",
      "diagnostic": "append_only_development_revision_edges",
      "name": "development_revision_edges_no_update",
      "operation": "UPDATE",
      "table": "development_revision_edges",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_revision_edges_no_delete\nBEFORE DELETE ON development_revision_edges\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_revision_edges');\nEND;",
      "diagnostic": "append_only_development_revision_edges",
      "name": "development_revision_edges_no_delete",
      "operation": "DELETE",
      "table": "development_revision_edges",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_work_spec_bindings_no_update\nBEFORE UPDATE ON development_work_spec_bindings\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_work_spec_bindings');\nEND;",
      "diagnostic": "append_only_development_work_spec_bindings",
      "name": "development_work_spec_bindings_no_update",
      "operation": "UPDATE",
      "table": "development_work_spec_bindings",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_work_spec_bindings_no_delete\nBEFORE DELETE ON development_work_spec_bindings\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_work_spec_bindings');\nEND;",
      "diagnostic": "append_only_development_work_spec_bindings",
      "name": "development_work_spec_bindings_no_delete",
      "operation": "DELETE",
      "table": "development_work_spec_bindings",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_semantic_attempts_no_update\nBEFORE UPDATE ON development_semantic_attempts\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_semantic_attempts');\nEND;",
      "diagnostic": "append_only_development_semantic_attempts",
      "name": "development_semantic_attempts_no_update",
      "operation": "UPDATE",
      "table": "development_semantic_attempts",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_semantic_attempts_no_delete\nBEFORE DELETE ON development_semantic_attempts\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_semantic_attempts');\nEND;",
      "diagnostic": "append_only_development_semantic_attempts",
      "name": "development_semantic_attempts_no_delete",
      "operation": "DELETE",
      "table": "development_semantic_attempts",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_attempt_fences_no_update\nBEFORE UPDATE ON development_attempt_fences\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_attempt_fences');\nEND;",
      "diagnostic": "append_only_development_attempt_fences",
      "name": "development_attempt_fences_no_update",
      "operation": "UPDATE",
      "table": "development_attempt_fences",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_attempt_fences_no_delete\nBEFORE DELETE ON development_attempt_fences\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_attempt_fences');\nEND;",
      "diagnostic": "append_only_development_attempt_fences",
      "name": "development_attempt_fences_no_delete",
      "operation": "DELETE",
      "table": "development_attempt_fences",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_authority_evaluations_no_update\nBEFORE UPDATE ON development_authority_evaluations\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_authority_evaluations');\nEND;",
      "diagnostic": "append_only_development_authority_evaluations",
      "name": "development_authority_evaluations_no_update",
      "operation": "UPDATE",
      "table": "development_authority_evaluations",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_authority_evaluations_no_delete\nBEFORE DELETE ON development_authority_evaluations\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_authority_evaluations');\nEND;",
      "diagnostic": "append_only_development_authority_evaluations",
      "name": "development_authority_evaluations_no_delete",
      "operation": "DELETE",
      "table": "development_authority_evaluations",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_effect_intents_no_update\nBEFORE UPDATE ON development_effect_intents\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_effect_intents');\nEND;",
      "diagnostic": "append_only_development_effect_intents",
      "name": "development_effect_intents_no_update",
      "operation": "UPDATE",
      "table": "development_effect_intents",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_effect_intents_no_delete\nBEFORE DELETE ON development_effect_intents\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_effect_intents');\nEND;",
      "diagnostic": "append_only_development_effect_intents",
      "name": "development_effect_intents_no_delete",
      "operation": "DELETE",
      "table": "development_effect_intents",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_effect_fences_no_update\nBEFORE UPDATE ON development_effect_fences\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_effect_fences');\nEND;",
      "diagnostic": "append_only_development_effect_fences",
      "name": "development_effect_fences_no_update",
      "operation": "UPDATE",
      "table": "development_effect_fences",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_effect_fences_no_delete\nBEFORE DELETE ON development_effect_fences\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_effect_fences');\nEND;",
      "diagnostic": "append_only_development_effect_fences",
      "name": "development_effect_fences_no_delete",
      "operation": "DELETE",
      "table": "development_effect_fences",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_author_commands_no_update\nBEFORE UPDATE ON development_author_commands\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_author_commands');\nEND;",
      "diagnostic": "append_only_development_author_commands",
      "name": "development_author_commands_no_update",
      "operation": "UPDATE",
      "table": "development_author_commands",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_author_commands_no_delete\nBEFORE DELETE ON development_author_commands\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_author_commands');\nEND;",
      "diagnostic": "append_only_development_author_commands",
      "name": "development_author_commands_no_delete",
      "operation": "DELETE",
      "table": "development_author_commands",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_delivery_attempts_no_update\nBEFORE UPDATE ON development_delivery_attempts\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_delivery_attempts');\nEND;",
      "diagnostic": "append_only_development_delivery_attempts",
      "name": "development_delivery_attempts_no_update",
      "operation": "UPDATE",
      "table": "development_delivery_attempts",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_delivery_attempts_no_delete\nBEFORE DELETE ON development_delivery_attempts\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_delivery_attempts');\nEND;",
      "diagnostic": "append_only_development_delivery_attempts",
      "name": "development_delivery_attempts_no_delete",
      "operation": "DELETE",
      "table": "development_delivery_attempts",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_decisions_no_update\nBEFORE UPDATE ON development_decisions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_decisions');\nEND;",
      "diagnostic": "append_only_development_decisions",
      "name": "development_decisions_no_update",
      "operation": "UPDATE",
      "table": "development_decisions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_decisions_no_delete\nBEFORE DELETE ON development_decisions\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_decisions');\nEND;",
      "diagnostic": "append_only_development_decisions",
      "name": "development_decisions_no_delete",
      "operation": "DELETE",
      "table": "development_decisions",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_mutation_receipts_no_update\nBEFORE UPDATE ON development_mutation_receipts\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_mutation_receipts');\nEND;",
      "diagnostic": "append_only_development_mutation_receipts",
      "name": "development_mutation_receipts_no_update",
      "operation": "UPDATE",
      "table": "development_mutation_receipts",
      "timing": "BEFORE"
    },
    {
      "body_sql": "CREATE TRIGGER development_mutation_receipts_no_delete\nBEFORE DELETE ON development_mutation_receipts\nBEGIN\n  SELECT RAISE(ABORT, 'append_only_development_mutation_receipts');\nEND;",
      "diagnostic": "append_only_development_mutation_receipts",
      "name": "development_mutation_receipts_no_delete",
      "operation": "DELETE",
      "table": "development_mutation_receipts",
      "timing": "BEFORE"
    }
  ],
  "work_spec_safe_projection": {
    "digest_domain": "governed-execution.nwp-development-work-spec-safe-projection.v1.identity",
    "ordered_keys": [
      "schema_id",
      "work_spec_ref",
      "program_ref",
      "program_version_ref",
      "accepted_intent_revision_ref",
      "work_item_ref",
      "work_item_revision_ref",
      "repository_ref",
      "base_git_object_format",
      "base_git_oid",
      "authorized_paths",
      "validation_requirement_ref",
      "review_requirement_ref",
      "privacy_classification",
      "work_spec_digest"
    ],
    "projection_is_complete_WorkSpecV1": False,
    "recorded_at_participates_in_projection_digest": False,
    "schema_id": "governed-execution.nwp-development-work-spec-safe-projection.v1",
    "source_field_treatment": {
      "authorized_paths": "stored as exact safe derived three-path canonical JSON",
      "credentials, endpoints, and retrieval material": "forbidden",
      "exclusions": "forbidden",
      "objective": "forbidden",
      "physical workspace path": "forbidden",
      "requirements": "forbidden",
      "safe references and source digest": "stored unchanged"
    }
  }
}

EXPECTED_TOP_LEVEL_KEYS = frozenset(
    {
        "contract_id",
        "classification",
        "sql_core",
        "tables",
        "foreign_keys",
        "triggers",
        "explicit_indexes",
        "scalar_and_compound_contracts",
        "c2a_persistence",
        "work_spec_safe_projection",
        "privacy_contract",
        "decision_envelope",
        "receipt_envelope",
        "receipt_scalar_coherence",
        "common_graph_digest_primitive",
        "private_readers",
        "family_replay_boundary",
        "nonimplementation",
        "oracle_architecture",
    }
)

EXPECTED_TABLE_NAMES = (
    "development_program_heads",
    "development_program_versions",
    "development_accepted_intent_revisions",
    "development_work_item_heads",
    "development_work_item_revisions",
    "development_program_version_work_items",
    "development_revision_edges",
    "development_work_spec_bindings",
    "development_semantic_attempts",
    "development_attempt_fences",
    "development_authority_evaluations",
    "development_effect_intents",
    "development_effect_fences",
    "development_author_commands",
    "development_effect_heads",
    "development_delivery_attempts",
    "development_delivery_heads",
    "development_decisions",
    "development_mutation_receipts",
)

EXPECTED_READER_ROLES = (
    "mutation_receipt_by_mutation_ref",
    "decision_by_decision_ref",
    "program_head_and_current_version",
    "initialize_decision_and_resulting_version",
    "accepted_intent_revision_by_exact_ref",
    "work_item_head_and_revision_by_exact_ref",
    "paged_program_version_membership",
    "work_spec_safe_binding",
    "attempt_fence_command_effect_aggregate",
    "authority_evaluation_by_exact_ref",
    "effect_head",
    "delivery_head",
)

EXPECTED_READER_FUTURE_CALLERS = {
    "mutation_receipt_by_mutation_ref": ["C2B3", "C2B5", "C2B6"],
    "decision_by_decision_ref": ["C2B3", "C2B5", "C2B6"],
    "program_head_and_current_version": ["C2B3", "C2B6"],
    "initialize_decision_and_resulting_version": ["C2B3"],
    "accepted_intent_revision_by_exact_ref": ["C2B3", "C2B6"],
    "work_item_head_and_revision_by_exact_ref": ["C2B3", "C2B5", "C2B6"],
    "paged_program_version_membership": ["C2B3", "C2B6"],
    "work_spec_safe_binding": ["C2B3", "C2B5", "C2B6"],
    "attempt_fence_command_effect_aggregate": ["C2B3", "C2B5", "C2B6"],
    "authority_evaluation_by_exact_ref": ["C2B3", "C2B5"],
    "effect_head": ["C2B3", "C2B5"],
    "delivery_head": ["C2B3", "C2B5"],
}

EXPECTED_PRIVATE_FUNCTIONS = (
    "_read_development_mutation_receipt_by_mutation_ref",
    "_read_development_decision_by_decision_ref",
    "_read_development_program_head_and_current_version",
    "_read_development_initialize_decision_and_resulting_version",
    "_read_development_accepted_intent_revision_by_exact_ref",
    "_read_development_work_item_head_and_revision_by_exact_ref",
    "_read_development_paged_program_version_membership",
    "_read_development_work_spec_safe_binding",
    "_read_development_attempt_fence_command_effect_aggregate",
    "_read_development_authority_evaluation_by_exact_ref",
    "_read_development_effect_head",
    "_read_development_delivery_head",
)

EXPECTED_SIGNATURE_INPUTS = {
    "mutation_receipt_by_mutation_ref": ["capability", "mutation_ref"],
    "decision_by_decision_ref": ["capability", "decision_ref"],
    "program_head_and_current_version": ["capability", "program_ref"],
    "initialize_decision_and_resulting_version": [
        "capability",
        "program_ref",
        "decision_ref",
    ],
    "accepted_intent_revision_by_exact_ref": [
        "capability",
        "program_ref",
        "accepted_intent_revision_ref",
    ],
    "work_item_head_and_revision_by_exact_ref": [
        "capability",
        "program_ref",
        "work_item_ref",
        "work_item_revision_ref",
    ],
    "paged_program_version_membership": [
        "capability",
        "program_ref",
        "program_version_ref",
        "maximum_members",
    ],
    "work_spec_safe_binding": [
        "capability",
        "program_ref",
        "program_version_ref",
        "work_item_ref",
        "work_item_revision_ref",
    ],
    "attempt_fence_command_effect_aggregate": [
        "capability",
        "program_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
    ],
    "authority_evaluation_by_exact_ref": [
        "capability",
        "program_ref",
        "authority_evaluation_ref",
    ],
    "effect_head": ["capability", "program_ref", "effect_intent_ref"],
    "delivery_head": ["capability", "program_ref", "effect_intent_ref"],
}

EXPECTED_RESULT_TYPES = {
    "mutation_receipt_by_mutation_ref": "DevelopmentMutationReceiptRowValue | None",
    "decision_by_decision_ref": "DevelopmentDecisionRowValue | None",
    "program_head_and_current_version": "DevelopmentProgramHeadAndCurrentVersionRead | None",
    "initialize_decision_and_resulting_version": "DevelopmentInitializeDecisionAndResultingVersionRead | None",
    "accepted_intent_revision_by_exact_ref": "DevelopmentAcceptedIntentRevisionRowValue | None",
    "work_item_head_and_revision_by_exact_ref": "DevelopmentWorkItemHeadAndRevisionRead | None",
    "paged_program_version_membership": "DevelopmentProgramVersionMembershipRead | None",
    "work_spec_safe_binding": "DevelopmentWorkSpecBindingRowValue | None",
    "attempt_fence_command_effect_aggregate": "DevelopmentAttemptFenceCommandEffectRead | None",
    "authority_evaluation_by_exact_ref": "DevelopmentAuthorityEvaluationRowValue | None",
    "effect_head": "DevelopmentEffectHeadRowValue | None",
    "delivery_head": "DevelopmentDeliveryHeadAndCurrentAttemptRead | None",
}

EXPECTED_AGGREGATE_VALUE_FIELDS = {
    "DevelopmentProgramHeadAndCurrentVersionRead": [
        "program_head",
        "current_program_version",
    ],
    "DevelopmentInitializeDecisionAndResultingVersionRead": [
        "initialize_decision",
        "resulting_program_version",
    ],
    "DevelopmentWorkItemHeadAndRevisionRead": [
        "work_item_head",
        "work_item_revision",
        "is_current",
    ],
    "DevelopmentProgramVersionMembershipEntry": [
        "membership",
        "work_item_revision",
    ],
    "DevelopmentProgramVersionMembershipRead": ["program_version", "entries"],
    "DevelopmentAttemptFenceCommandEffectRead": [
        "semantic_attempt",
        "effect_intent",
        "author_command",
        "attempt_fence",
        "current_effect_fence",
        "author_effect_fence",
    ],
    "DevelopmentDeliveryHeadAndCurrentAttemptRead": [
        "delivery_head",
        "current_delivery_attempt",
    ],
}

EXPECTED_QUERY_ORDERS = {
    "mutation_receipt_by_mutation_ref": ["mutation_receipt"],
    "decision_by_decision_ref": ["decision"],
    "program_head_and_current_version": [
        "program_head",
        "current_program_version",
    ],
    "initialize_decision_and_resulting_version": [
        "initialize_decision",
        "resulting_program_version",
    ],
    "accepted_intent_revision_by_exact_ref": ["accepted_intent_revision"],
    "work_item_head_and_revision_by_exact_ref": [
        "work_item_head",
        "work_item_revision",
    ],
    "paged_program_version_membership": [
        "program_version_root",
        "membership_first_page",
        "membership_continuation_page zero or more times",
        "membership_work_item_revision once per returned membership in membership order",
    ],
    "work_spec_safe_binding": ["work_spec_safe_binding"],
    "attempt_fence_command_effect_aggregate": [
        "effect_intent_root",
        "semantic_attempt",
        "author_command",
        "attempt_fence",
        "current_effect_fence",
        "author_effect_fence only when distinct, otherwise reuse current_effect_fence",
    ],
    "authority_evaluation_by_exact_ref": ["authority_evaluation"],
    "effect_head": ["effect_head"],
    "delivery_head": ["delivery_head", "current_delivery_attempt"],
}

EXPECTED_CAPABILITY_PATH_ORDER = (
    "pure lookup/resource validation",
    "function-local import of _SQLiteMutationReadCapability",
    "type(capability) is _SQLiteMutationReadCapability",
    "capability borrow",
    "literal SQL execution",
)

EXPECTED_CAPABILITY_ERRORS = (
    "mutation_read_capability_unavailable",
    "mutation_read_capability_expired",
    "process_mismatch",
    "thread_mismatch",
)

EXPECTED_PROHIBITED_AUTHORITY_LOCATORS = (
    "latest timestamp",
    "MAX(evaluated_at)",
    "rowid",
    "lexicographic ref order",
    "preferred authority state",
    "verified-first selection",
    "unbounded subject scan",
    "receipt digest",
)

EXPECTED_ROLE_SEVEN_UNIQUE_WORK_ITEM_REF_RULE = (
    "Each work_item_ref appears at most once in the completed "
    "DevelopmentProgramVersionMembershipRead aggregate."
)

EXPECTED_ROLE_SEVEN_DUPLICATE_WORK_ITEM_REF_SCOPE = (
    "within one membership page",
    "across two or more membership pages",
    "across the 256/257 boundary",
    "regardless of differing membership_ordinal",
    "regardless of differing work_item_revision_ref",
)

EXPECTED_ROLE_NINE_NO_PROOF = {
    "capsule_identity": "not proved",
    "capsule_custody": "not proved",
    "semantic_acceptance": "not proved",
    "execution_permission": "not proved",
}

EXPECTED_ROLE_TEN_AUTHORITY_BOUNDARY = {
    "evidence_only": "The decoded authority-evaluation row is evidence only.",
    "executable_permission": "The row confers no executable permission.",
    "verified_state": (
        "A verified state does not itself authorize a worker, adapter, route, "
        "mutation, retry, replay, or external effect."
    ),
    "reader_authority": (
        "The reader does not issue, renew, reinterpret, or consume executable "
        "authority."
    ),
}

EXPECTED_EIGHT_FILE_COMPATIBILITY_GROUP = (
    "tests/test_c2b2_development_program_row_values.py",
    "tests/test_c2b2_development_effect_row_values.py",
    "tests/test_c2b2_development_decision_row_values.py",
    "tests/test_c2b2_development_row_value_boundaries.py",
    "tests/test_b3b2b_select_readers.py",
    "tests/test_b3c2_transition_event_readers.py",
    "tests/test_b4a_global_stop_readers.py",
    "tests/test_b3c1b_rollback_only_writer_fencing.py",
)

EXPECTED_STRICT_READER_VALIDATION_GROUPS = (
    "dedicated field-level oracle",
    "oracle plus C2B0 owner contract",
    "future Slice-3 reader-contract tests",
    "future Slice-3 reader-execution tests",
    "changed architecture, status, and non-authority tests",
    "completed five-file SQLite-hygiene gate",
)

EXPECTED_AGGREGATE_VALUE_POSTURE = (
    "manual slots",
    "no __dict__ or weakref",
    "factory-only construction",
    "no subclassing",
    "exact-type equality",
    "unhashable",
    "content-free repr/str",
    "copy/deepcopy identity",
    "pickle disabled",
    "tuples for collections",
    "no SQL, parameters, row tuples, mappings, cursors, connections, capabilities, or epochs retained",
)

EXPECTED_FUTURE_IMPLEMENTATION_PATHS = (
    "src/ge_nwp_coordinator/_sqlite_development_reader_contracts.py",
    "src/ge_nwp_coordinator/_sqlite_development_readers.py",
    "src/ge_nwp_coordinator/sqlite_transition_select_support.py",
    ".docs/c2b2-private-readers.md",
    ".docs/c2b-durable-development-state.md",
    ".docs/c2b2-migration-0002.md",
    ".docs/c2b2-pure-durable-row-values.md",
    ".docs/architecture.md",
    ".docs/autonomous-software-development-operating-model.md",
    ".docs/durable-state-model.md",
    ".docs/software-development-progression-boundary.md",
    ".docs/sqlite-threat-model.md",
    "README.md",
    "AGENTS.md",
    "tests/test_c2b2_development_reader_contracts.py",
    "tests/test_c2b2_private_development_readers.py",
    "tests/test_c2b2_field_level_contract.py",
    "tests/test_c2b0_durable_state_contract.py",
    "tests/test_architecture_contracts.py",
    "tests/test_autonomous_software_development_operating_model.py",
    "tests/test_software_development_progression_boundary.py",
    "tests/test_runtime_non_authority.py",
    "tests/test_c2a_nonimplementation.py",
)

EXPECTED_TABLE_READER_ROLES = {
    "development_program_heads": ["program_head_and_current_version"],
    "development_program_versions": [
        "program_head_and_current_version",
        "initialize_decision_and_resulting_version",
        "paged_program_version_membership",
    ],
    "development_accepted_intent_revisions": ["accepted_intent_revision_by_exact_ref"],
    "development_work_item_heads": ["work_item_head_and_revision_by_exact_ref"],
    "development_work_item_revisions": [
        "work_item_head_and_revision_by_exact_ref",
        "paged_program_version_membership",
    ],
    "development_program_version_work_items": ["paged_program_version_membership"],
    "development_revision_edges": [],
    "development_work_spec_bindings": ["work_spec_safe_binding"],
    "development_semantic_attempts": ["attempt_fence_command_effect_aggregate"],
    "development_attempt_fences": ["attempt_fence_command_effect_aggregate"],
    "development_authority_evaluations": ["authority_evaluation_by_exact_ref"],
    "development_effect_intents": ["attempt_fence_command_effect_aggregate"],
    "development_effect_fences": ["attempt_fence_command_effect_aggregate"],
    "development_author_commands": ["attempt_fence_command_effect_aggregate"],
    "development_effect_heads": ["effect_head"],
    "development_delivery_attempts": ["delivery_head"],
    "development_delivery_heads": ["delivery_head"],
    "development_decisions": [
        "decision_by_decision_ref",
        "initialize_decision_and_resulting_version",
    ],
    "development_mutation_receipts": ["mutation_receipt_by_mutation_ref"],
}

EXPECTED_TABLE_SEMANTIC_ROLES = {
    "development_program_heads": "program_progression_head",
    "development_program_versions": "program_version_record",
    "development_accepted_intent_revisions": "accepted_intent_revision_record",
    "development_work_item_heads": "work_item_progression_head",
    "development_work_item_revisions": "work_item_revision_record",
    "development_program_version_work_items": "program_version_membership_record",
    "development_revision_edges": "revision_edge_record",
    "development_work_spec_bindings": "work_spec_binding_record",
    "development_semantic_attempts": "semantic_attempt_record",
    "development_attempt_fences": "attempt_fence_record",
    "development_authority_evaluations": "authority_evaluation_record",
    "development_effect_intents": "effect_intent_record",
    "development_effect_fences": "effect_fence_record",
    "development_author_commands": "author_command_record",
    "development_effect_heads": "effect_progression_head",
    "development_delivery_attempts": "delivery_attempt_record",
    "development_delivery_heads": "delivery_progression_head",
    "development_decisions": "development_decision_record",
    "development_mutation_receipts": "development_mutation_receipt_record",
}

_OLD_READER_IDENTITIES = {
    "program_head_and_current_version_by_program_ref",
    "program_version_work_membership_and_revisions",
    "attempt_fence_command_effect_graph",
    "delivery_head_and_current_attempt",
}

_FAILURE_IDENTIFIERS = {
    "C2B2_ORACLE_DUPLICATE_DEFINITION",
    "C2B2_ORACLE_DYNAMIC_DISPATCH",
    "C2B2_ORACLE_EXPECTED_NOT_LITERAL",
    "C2B2_ORACLE_FORBIDDEN_INPUT",
    "C2B2_ORACLE_RUNTIME_BINDING",
    "C2B2_ORACLE_SOURCE_HASH_AUTHORITY",
    "C2B2_READER_FUTURE_CALLER_INVALID",
    "C2B2_READER_FUTURE_CALLER_MISSING",
    "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
    "C2B2_READER_AUTHORITY_BOUNDARY_MISMATCH",
    "C2B2_READER_AUTHORITY_LOCATOR_FORBIDDEN",
    "C2B2_READER_CAPABILITY_ORDER_MISMATCH",
    "C2B2_READER_IMPLEMENTATION_SCOPE_MISMATCH",
    "C2B2_READER_LITERAL_SQL_MISMATCH",
    "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
    "C2B2_READER_RECEIPT_BOUNDARY_MISMATCH",
    "C2B2_READER_SIGNATURE_MISMATCH",
    "C2B2_READER_VALIDATION_POLICY_MISMATCH",
    "C2B2_REVISION_EDGE_READER_OWNERSHIP",
    "C2B2_TABLE_READER_ROLE_DIRECTION_MISMATCH",
    "C2B2_TABLE_READER_ROLE_MISMATCH",
    "C2B2_TABLE_READER_ROLE_UNKNOWN",
    "absent_inventory",
    "advancing_kinds",
    "c2a_mapping_count",
    "c2a_mapping_match",
    "c2a_mapping_types",
    "c2a_persistence",
    "classification",
    "column_count",
    "common_graph_digest_primitive",
    "contract_id",
    "current_generation_tip",
    "decision_column_count",
    "decision_envelope",
    "decision_kind_count",
    "decision_matrix_count",
    "decision_mutation_absent",
    "decision_representation_owner",
    "decision_variant_count",
    "decision_version_advancement",
    "deferred_foreign_key_count",
    "explicit_index_count",
    "explicit_index_ledger",
    "explicit_index_sql",
    "family_replay_boundary",
    "family_replay_not_elevated",
    "foreign_key_actions",
    "foreign_key_count",
    "foreign_key_ledger",
    "generic_payload_metadata_bag",
    "graph_entry_keys",
    "graph_identity_envelope_fields",
    "graph_identity_field_count",
    "immutable_table_count",
    "mutable_table_count",
    "nonadvancing_kinds",
    "nonimplementation",
    "nonimplementation_flags",
    "oracle_architecture",
    "owner_begin_marker",
    "owner_end_marker",
    "owner_json_closer",
    "owner_json_opener",
    "privacy_contract",
    "privacy_forbidden_inventory",
    "private_reader_ledger",
    "private_reader_roles",
    "proposal_evidence_classification",
    "reader_capability_unavailable",
    "reader_fetch_bound",
    "reader_limit",
    "reader_lookup_identity",
    "reader_nominal_capability",
    "reader_ordered_select_columns",
    "reader_paging_bound",
    "reader_paging_order",
    "reader_private_value",
    "reader_replay_claim",
    "reader_safe_error",
    "reader_select_table",
    "reader_selects",
    "receipt_column_count",
    "receipt_envelope",
    "receipt_family_count",
    "receipt_outcome",
    "receipt_scalar_coherence",
    "revision_edge_relation_key_uniqueness",
    "scalar_and_compound_contracts",
    "seed_rows",
    "sql_core",
    "sqlite_any_declarations",
    "strict_tables",
    "table_count",
    "table_field_ledger",
    "table_ledger_order",
    "table_order",
    "top_level_keys",
    "tranche_ownership",
    "trigger_count",
    "trigger_ledger",
    "trigger_names",
    "trigger_operations",
    "work_spec_safe_projection",
}

RESULT_REFERENCE_FIELDS = (
    "decision_ref",
    "result_program_version_ref",
    "result_semantic_attempt_ref",
    "result_effect_intent_ref",
    "result_effect_fence_ref",
    "result_delivery_attempt_ref",
    "result_observation_ref",
    "result_decision_ref",
)


class _ContractViolation(AssertionError):
    pass


class _DatabaseIntegrityFailure(Exception):
    pass


def _require(condition: bool, identifier: str) -> None:
    if identifier not in _FAILURE_IDENTIFIERS:
        raise AssertionError("invalid_contract_failure_identifier")
    if not condition:
        raise _ContractViolation(identifier)


def _integrity(condition: bool) -> None:
    if not condition:
        raise _DatabaseIntegrityFailure("database_integrity_failure")


def _validate_completed_membership_work_item_refs(
    entries: tuple[tuple[int, str, str], ...],
    child_revision_queries: list[tuple[str, str]],
) -> tuple[tuple[int, str, str], ...]:
    _require(type(entries) is tuple, "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH")
    _require(
        type(child_revision_queries) is list,
        "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
    )
    seen_work_item_refs: set[str] = set()
    for expected_ordinal, entry in enumerate(entries):
        _require(
            type(entry) is tuple and len(entry) == 3,
            "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
        )
        membership_ordinal, work_item_ref, work_item_revision_ref = entry
        _require(
            type(membership_ordinal) is int
            and membership_ordinal == expected_ordinal
            and type(work_item_ref) is str
            and bool(work_item_ref)
            and type(work_item_revision_ref) is str
            and bool(work_item_revision_ref),
            "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
        )
        _require(
            work_item_ref not in seen_work_item_refs,
            "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
        )
        seen_work_item_refs.add(work_item_ref)
        child_revision_queries.append((work_item_ref, work_item_revision_ref))
    return entries


def _owner_contract() -> dict[str, Any]:
    owner = OWNER_PATH.read_text(encoding="utf-8")
    _require(owner.count(BEGIN_MARKER) == 1, "owner_begin_marker")
    _require(owner.count(END_MARKER) == 1, "owner_end_marker")
    payload = owner.split(BEGIN_MARKER, 1)[1].split(END_MARKER, 1)[0].strip()
    _require(payload.startswith("```json\n"), "owner_json_opener")
    _require(payload.endswith("\n```"), "owner_json_closer")
    return json.loads(payload[len("```json\n") : -len("\n```")])


def _table_map(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["name"]: item for item in contract["tables"]}


def _reader_map(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["role"]: item
        for item in contract["private_readers"]["roles"]
    }


def _validate_classification(contract: dict[str, Any]) -> None:
    _require(
        contract["classification"] == EXPECTED_CONTRACT["classification"],
        "classification",
    )
    _require(
        "application generation 2 and terminal tip "
        "0002_development_program_and_effect_state plus Slice 2 pure private "
        "row/value source"
        in contract["classification"]["current_implemented_contract"],
        "current_generation_tip",
    )
    _require(
        contract["classification"]["absent"]
        == [
            "C2B2 private readers",
            "C2B mutations and exact replay or recovery",
            "C2B product runtime caller",
        ],
        "absent_inventory",
    )


def _validate_revision_edge_reader_ownership(contract: dict[str, Any]) -> None:
    tables = contract.get("tables")
    if type(tables) is not list:
        return
    revision_edge_tables = [
        item
        for item in tables
        if type(item) is dict and item.get("name") == "development_revision_edges"
    ]
    if len(revision_edge_tables) != 1:
        return

    revision_edges = revision_edge_tables[0]
    expected_revision_edge_tables = [
        item
        for item in EXPECTED_CONTRACT["tables"]
        if item["name"] == "development_revision_edges"
    ]
    _require(
        len(expected_revision_edge_tables) == 1,
        "C2B2_REVISION_EDGE_READER_OWNERSHIP",
    )
    expected_revision_edges = expected_revision_edge_tables[0]
    ownership_key_tokens = (
        "historical",
        "locator",
        "postimage",
        "query",
        "reader",
        "replay",
    )
    unexpected_ownership_keys = {
        key
        for key in revision_edges
        if key not in expected_revision_edges
        and any(token in key.lower() for token in ownership_key_tokens)
    }
    _require(
        not unexpected_ownership_keys,
        "C2B2_REVISION_EDGE_READER_OWNERSHIP",
    )
    _require(
        revision_edges.get("reader_roles") == [],
        "C2B2_REVISION_EDGE_READER_OWNERSHIP",
    )
    _require(
        revision_edges.get("c2b2_reader_treatment")
        == "durable row representation only"
        and revision_edges.get("future_reader_owner") == "C2B6"
        and revision_edges.get("future_reader_owner_reason")
        == (
            "exact revision-edge selection is progression-family-specific and belongs "
            "to the C2B6 graph-locator/replay contract before C2B6 writers"
        ),
        "C2B2_REVISION_EDGE_READER_OWNERSHIP",
    )

    revision_edge_columns = {
        column["name"]
        for column in expected_revision_edges["columns"]
    }
    other_table_columns = {
        column["name"]
        for table in EXPECTED_CONTRACT["tables"]
        if table["name"] != "development_revision_edges"
        for column in table["columns"]
    }
    revision_edge_only_columns = revision_edge_columns - other_table_columns
    reader_contract = contract.get("private_readers")
    if type(reader_contract) is not dict:
        return
    readers = reader_contract.get("roles")
    if type(readers) is not list:
        return
    for reader in readers:
        if type(reader) is not dict:
            continue
        role = reader.get("role")
        lookup_identity = reader.get("lookup_identity")
        lookup_fields = set(lookup_identity) if type(lookup_identity) is list else set()
        reader_has_revision_edge_surface = (
            type(role) is str
            and "revision_edge" in role.lower()
        ) or bool(lookup_fields & revision_edge_only_columns) or any(
            type(item) is str and "revision_edge" in item.lower()
            for item in lookup_fields
        ) or any(
            key not in {
                "absence_result",
                "all_pages_same_capability_epoch",
                "bounded_aggregate_verification",
                "cardinality",
                "complete_mutation_family_replay_verification",
                "continuation_pair_rule",
                "decoded_private_value",
                "duplicate_result",
                "fetch_bound",
                "future_caller",
                "has_more_rule",
                "limit",
                "lookup_identity",
                "malformed_row_result",
                "nominal_capability_requirement",
                "ordering",
                "return_bound",
                "role",
                "row_digest_verification",
                "safe_error",
                "selects",
            }
            and "revision_edge" in key.lower()
            for key in reader
        )
        selects = reader.get("selects")
        if type(selects) is list:
            for select in selects:
                if type(select) is not dict:
                    continue
                fields = select.get("fields")
                selected_fields = set(fields) if type(fields) is list else set()
                query_sql = select.get("query_sql")
                reader_has_revision_edge_surface = (
                    reader_has_revision_edge_surface
                    or select.get("table") == "development_revision_edges"
                    or bool(selected_fields & revision_edge_only_columns)
                    or (
                        type(query_sql) is str
                        and "development_revision_edges" in query_sql
                    )
                )
        _require(
            not reader_has_revision_edge_surface,
            "C2B2_REVISION_EDGE_READER_OWNERSHIP",
        )


def _validate_table_reader_mapping(contract: dict[str, Any]) -> None:
    _validate_revision_edge_reader_ownership(contract)
    tables = _table_map(contract)
    reader_contract = contract.get("private_readers")
    readers = (
        reader_contract.get("roles")
        if type(reader_contract) is dict
        else None
    )
    if type(readers) is list:
        role_nine = next(
            (
                reader
                for reader in readers
                if type(reader) is dict
                and reader.get("role")
                == "attempt_fence_command_effect_aggregate"
            ),
            None,
        )
        if type(role_nine) is dict and type(role_nine.get("selects")) is list:
            _require(
                all(
                    type(select) is dict
                    and select.get("table")
                    != "development_authority_evaluations"
                    for select in role_nine["selects"]
                ),
                "C2B2_READER_AUTHORITY_LOCATOR_FORBIDDEN",
            )
    for table_name in EXPECTED_TABLE_NAMES:
        table = tables[table_name]
        _require(
            "reader_role" not in table,
            "C2B2_TABLE_READER_ROLE_MISMATCH",
        )
        reader_roles = table.get("reader_roles")
        _require(
            type(reader_roles) is list,
            "C2B2_TABLE_READER_ROLE_MISMATCH",
        )
        for reader_role in reader_roles:
            _require(
                type(reader_role) is str and reader_role in EXPECTED_READER_ROLES,
                "C2B2_TABLE_READER_ROLE_UNKNOWN",
            )
        semantic_role = table.get("role")
        _require(
            semantic_role == EXPECTED_TABLE_SEMANTIC_ROLES[table_name]
            and semantic_role not in EXPECTED_READER_ROLES
            and semantic_role not in _OLD_READER_IDENTITIES,
            "C2B2_TABLE_READER_ROLE_MISMATCH",
        )
        _require(
            reader_roles == EXPECTED_TABLE_READER_ROLES[table_name],
            "C2B2_TABLE_READER_ROLE_MISMATCH",
        )
    if type(readers) is list:
        for reader in readers:
            if type(reader) is not dict or type(reader.get("selects")) is not list:
                continue
            role = reader.get("role")
            for select in reader["selects"]:
                selected_table = select.get("table") if type(select) is dict else None
                _require(
                    selected_table in tables
                    and role in tables[selected_table]["reader_roles"],
                    "C2B2_TABLE_READER_ROLE_DIRECTION_MISMATCH",
                )
        for table_name, table in tables.items():
            for role in table["reader_roles"]:
                matching_reader = next(
                    (
                        reader
                        for reader in readers
                        if type(reader) is dict and reader.get("role") == role
                    ),
                    None,
                )
                _require(
                    type(matching_reader) is dict
                    and any(
                        type(select) is dict
                        and select.get("table") == table_name
                        for select in matching_reader.get("selects", [])
                    ),
                    "C2B2_TABLE_READER_ROLE_DIRECTION_MISMATCH",
                )


def _validate_sql_core(contract: dict[str, Any]) -> None:
    core = contract["sql_core"]
    expected_core = EXPECTED_CONTRACT["sql_core"]
    _require(core == expected_core, "sql_core")
    _require(tuple(core["table_names_in_order"]) == EXPECTED_TABLE_NAMES, "table_order")
    _require(tuple(item["name"] for item in contract["tables"]) == EXPECTED_TABLE_NAMES, "table_ledger_order")
    _validate_table_reader_mapping(contract)
    _require(contract["tables"] == EXPECTED_CONTRACT["tables"], "table_field_ledger")
    _require(contract["foreign_keys"] == EXPECTED_CONTRACT["foreign_keys"], "foreign_key_ledger")
    _require(contract["triggers"] == EXPECTED_CONTRACT["triggers"], "trigger_ledger")
    _require(
        contract["explicit_indexes"] == EXPECTED_CONTRACT["explicit_indexes"],
        "explicit_index_ledger",
    )

    tables = contract["tables"]
    foreign_keys = contract["foreign_keys"]
    triggers = contract["triggers"]
    _require(len(tables) == core["table_count"] == 19, "table_count")
    _require(sum(len(item["columns"]) for item in tables) == 362, "column_count")
    _require(all(item["strict"] is True for item in tables), "strict_tables")
    _require(
        all(
            column["sqlite_declaration_type"] == "ANY"
            for item in tables
            for column in item["columns"]
        ),
        "sqlite_any_declarations",
    )
    _require(sum(item["mutable"] for item in tables) == 4, "mutable_table_count")
    _require(sum(not item["mutable"] for item in tables) == 15, "immutable_table_count")
    _require(all(not item["seed_rows"] for item in tables), "seed_rows")
    _require(len(foreign_keys) == 87, "foreign_key_count")
    _require(
        sum(
            item["deferrability"] == "DEFERRABLE INITIALLY DEFERRED"
            for item in foreign_keys
        )
        == 6,
        "deferred_foreign_key_count",
    )
    _require(
        all(item["on_update"] == item["on_delete"] == "RESTRICT" for item in foreign_keys),
        "foreign_key_actions",
    )
    _require(len(triggers) == 30, "trigger_count")
    _require(len({item["name"] for item in triggers}) == 30, "trigger_names")
    _require(
        {item["operation"] for item in triggers} == {"UPDATE", "DELETE"},
        "trigger_operations",
    )
    _require(len(contract["explicit_indexes"]) == 1, "explicit_index_count")
    _require(
        contract["explicit_indexes"][0]["sql"]
        == "CREATE UNIQUE INDEX uq_development_effect_intents_author_command\n"
        "ON development_effect_intents(command_ref)\n"
        "WHERE effect_class = 'author_candidate';",
        "explicit_index_sql",
    )
    column_names = {
        column["name"]
        for item in tables
        for column in item["columns"]
    }
    _require(
        column_names.isdisjoint({"payload", "metadata", "extensions", "extension_bag"}),
        "generic_payload_metadata_bag",
    )


def _validate_scalar_c2a_privacy(contract: dict[str, Any]) -> None:
    _require(
        contract["scalar_and_compound_contracts"]
        == EXPECTED_CONTRACT["scalar_and_compound_contracts"],
        "scalar_and_compound_contracts",
    )
    _require(
        contract["c2a_persistence"] == EXPECTED_CONTRACT["c2a_persistence"],
        "c2a_persistence",
    )
    _require(
        contract["work_spec_safe_projection"]
        == EXPECTED_CONTRACT["work_spec_safe_projection"],
        "work_spec_safe_projection",
    )
    _require(
        contract["privacy_contract"] == EXPECTED_CONTRACT["privacy_contract"],
        "privacy_contract",
    )
    ledger = contract["c2a_persistence"]["field_mapping_ledger"]
    _require(len(ledger) == 150, "c2a_mapping_count")
    _require(all(item["match"] == "yes" for item in ledger), "c2a_mapping_match")
    _require(
        {item["value_type"] for item in ledger}
        == {"AttemptFenceV1", "EffectFenceV1", "WorkerCommandV1", "DeliveryEnvelopeV1"},
        "c2a_mapping_types",
    )
    relation_table = _table_map(contract)["development_revision_edges"]
    _require(
        ["relation_key_digest"] in relation_table["unique_constraints"],
        "revision_edge_relation_key_uniqueness",
    )
    forbidden = contract["privacy_contract"]["forbidden_persistent_material"]
    for phrase in (
        "WorkSpec objective",
        "requirements",
        "exclusions",
        "credentials",
        "private endpoints",
        "private prompts or responses",
        "transcripts",
        "candidate bytes",
        "capsule bytes or entries",
        "physical workspace paths",
    ):
        _require(phrase in forbidden, "privacy_forbidden_inventory")


def _validate_decision_envelope(contract: dict[str, Any]) -> None:
    decision = contract["decision_envelope"]
    _require(decision == EXPECTED_CONTRACT["decision_envelope"], "decision_envelope")
    _require(len(decision["ordered_columns"]) == decision["column_count"] == 43, "decision_column_count")
    _require(len(decision["decision_kinds"]) == 8, "decision_kind_count")
    _require(len(decision["decision_variants"]) == 10, "decision_variant_count")
    _require(len(decision["variant_matrix"]) == 10, "decision_matrix_count")
    advancing = set(decision["version_advancing_kinds"])
    nonadvancing = set(decision["non_version_advancing_kinds"])
    _require(advancing == {"initialize", "accept", "repair", "replan", "terminal_reject", "block"}, "advancing_kinds")
    _require(nonadvancing == {"redeliver", "cancel"}, "nonadvancing_kinds")
    for variant in decision["variant_matrix"]:
        expected = variant["kind"] in advancing
        _require(variant["version_advancing"] is expected, "decision_version_advancement")
    _require(decision["representation_owner"] == "C2B2", "decision_representation_owner")
    _require(decision["mutation_implemented"] is False, "decision_mutation_absent")


def _validate_receipt_envelope(contract: dict[str, Any]) -> None:
    receipt = contract["receipt_envelope"]
    _require(receipt == EXPECTED_CONTRACT["receipt_envelope"], "receipt_envelope")
    _require(len(receipt["ordered_columns"]) == receipt["column_count"] == 19, "receipt_column_count")
    _require(len(receipt["family_matrix"]) == 5, "receipt_family_count")
    _require(receipt["outcomes"] == ["committed"], "receipt_outcome")
    _require(
        all(
            "exact_replay_result" not in item
            and "fresh_path_orphan_check" not in item
            and "graph_roles" not in item
            for item in receipt["family_matrix"]
        ),
        "family_replay_not_elevated",
    )
    _require(
        contract["receipt_scalar_coherence"]
        == EXPECTED_CONTRACT["receipt_scalar_coherence"],
        "receipt_scalar_coherence",
    )


def _validate_graph_primitive(contract: dict[str, Any]) -> None:
    graph = contract["common_graph_digest_primitive"]
    _require(
        graph == EXPECTED_CONTRACT["common_graph_digest_primitive"],
        "common_graph_digest_primitive",
    )
    receipt_fields = contract["receipt_envelope"]["ordered_columns"]
    _require(
        graph["identity_envelope_fields"]
        == [item for item in receipt_fields if item != "mutation_graph_digest"],
        "graph_identity_envelope_fields",
    )
    _require(len(graph["identity_envelope_fields"]) == 18, "graph_identity_field_count")
    _require(graph["graph_entry_ordered_keys"] == ["role", "ordinal", "record_ref", "record_digest"], "graph_entry_keys")


def _validate_reader_required_keys(contract: dict[str, Any]) -> None:
    reader_contract = contract.get("private_readers")
    _require(type(reader_contract) is dict, "private_reader_ledger")
    expected_reader_contract = EXPECTED_CONTRACT["private_readers"]

    _require(
        "future_implementation_allowlist" in reader_contract,
        "C2B2_READER_IMPLEMENTATION_SCOPE_MISMATCH",
    )
    scope = reader_contract["future_implementation_allowlist"]
    expected_scope = expected_reader_contract["future_implementation_allowlist"]
    _require(
        type(scope) is dict
        and set(scope) == set(expected_scope)
        and all(type(scope[key]) is type(expected_scope[key]) for key in expected_scope),
        "C2B2_READER_IMPLEMENTATION_SCOPE_MISMATCH",
    )

    _require(
        "validation_and_audit_plan" in reader_contract,
        "C2B2_READER_VALIDATION_POLICY_MISMATCH",
    )
    validation_plan = reader_contract["validation_and_audit_plan"]
    expected_validation_plan = expected_reader_contract["validation_and_audit_plan"]
    _require(
        type(validation_plan) is dict
        and set(validation_plan) == set(expected_validation_plan)
        and all(
            type(validation_plan[key]) is type(expected_validation_plan[key])
            for key in expected_validation_plan
        ),
        "C2B2_READER_VALIDATION_POLICY_MISMATCH",
    )
    _require(
        "eight_file_compatibility_group" in validation_plan
        and type(validation_plan["eight_file_compatibility_group"]) is dict,
        "C2B2_READER_VALIDATION_POLICY_MISMATCH",
    )
    compatibility_group = validation_plan["eight_file_compatibility_group"]
    expected_compatibility_group = expected_validation_plan[
        "eight_file_compatibility_group"
    ]
    _require(
        set(compatibility_group) == set(expected_compatibility_group)
        and all(
            type(compatibility_group[key])
            is type(expected_compatibility_group[key])
            for key in expected_compatibility_group
        )
        and "warning_policy" in compatibility_group
        and type(compatibility_group["warning_policy"]) is dict
        and set(compatibility_group["warning_policy"])
        == set(expected_compatibility_group["warning_policy"])
        and all(
            type(compatibility_group["warning_policy"][key])
            is type(expected_compatibility_group["warning_policy"][key])
            for key in expected_compatibility_group["warning_policy"]
        ),
        "C2B2_READER_VALIDATION_POLICY_MISMATCH",
    )

    _require(
        all(
            key in reader_contract
            for key in (
                "aggregate_value_contracts",
                "common_contract",
                "empty_membership_permitted_program_version_kinds",
                "prohibited_authority_locators",
                "roles",
                "workstream_identity",
            )
        ),
        "private_reader_ledger",
    )
    _require(
        all(
            type(reader_contract[key]) is type(expected_reader_contract[key])
            for key in expected_reader_contract
        ),
        "private_reader_ledger",
    )
    aggregate_contracts = reader_contract["aggregate_value_contracts"]
    expected_aggregate_contracts = expected_reader_contract["aggregate_value_contracts"]
    _require(
        type(aggregate_contracts) is list
        and len(aggregate_contracts) == len(expected_aggregate_contracts)
        and all(
            type(item) is dict
            and set(item) == set(expected_aggregate_contracts[index])
            and all(
                type(item[key]) is type(expected_aggregate_contracts[index][key])
                for key in expected_aggregate_contracts[index]
            )
            for index, item in enumerate(aggregate_contracts)
        ),
        "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
    )
    common = reader_contract["common_contract"]
    expected_common = expected_reader_contract["common_contract"]
    _require(
        type(common) is dict
        and set(common) == set(expected_common)
        and all(
            type(common[key]) is type(expected_common[key])
            for key in expected_common
        )
        and type(common.get("shared_bounded_fetch_future_contract")) is dict
        and set(common["shared_bounded_fetch_future_contract"])
        == set(expected_common["shared_bounded_fetch_future_contract"]),
        "C2B2_READER_CAPABILITY_ORDER_MISMATCH",
    )

    readers = reader_contract["roles"]
    _require(
        type(readers) is list
        and len(readers) == len(EXPECTED_READER_ROLES)
        and all(type(reader) is dict for reader in readers),
        "private_reader_roles",
    )
    _require(
        tuple(reader.get("role") for reader in readers) == EXPECTED_READER_ROLES,
        "private_reader_roles",
    )
    expected_readers = expected_reader_contract["roles"]
    for index, reader in enumerate(readers):
        expected_reader = expected_readers[index]
        if "future_caller" not in reader:
            _require(False, "C2B2_READER_FUTURE_CALLER_MISSING")
        missing_keys = set(expected_reader) - set(reader)
        if missing_keys:
            if reader["role"] == "paged_program_version_membership":
                _require(False, "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH")
            if reader["role"] == "attempt_fence_command_effect_aggregate":
                _require(False, "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH")
            if reader["role"] == "authority_evaluation_by_exact_ref":
                _require(False, "C2B2_READER_AUTHORITY_BOUNDARY_MISMATCH")
            if missing_keys & {"query_order", "selects"}:
                _require(False, "C2B2_READER_LITERAL_SQL_MISMATCH")
            if missing_keys & {
                "private_function",
                "result_type",
                "signature",
                "signature_inputs",
            }:
                _require(False, "C2B2_READER_SIGNATURE_MISMATCH")
            _require(False, "private_reader_ledger")
        mismatched_types = {
            key
            for key in expected_reader
            if type(reader[key]) is not type(expected_reader[key])
        }
        if mismatched_types:
            if "future_caller" in mismatched_types:
                _require(False, "C2B2_READER_FUTURE_CALLER_INVALID")
            if reader["role"] == "paged_program_version_membership":
                _require(False, "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH")
            if reader["role"] == "attempt_fence_command_effect_aggregate":
                _require(False, "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH")
            if reader["role"] == "authority_evaluation_by_exact_ref":
                _require(False, "C2B2_READER_AUTHORITY_BOUNDARY_MISMATCH")
            if mismatched_types & {"query_order", "selects"}:
                _require(False, "C2B2_READER_LITERAL_SQL_MISMATCH")
            if mismatched_types & {
                "private_function",
                "result_type",
                "signature",
                "signature_inputs",
            }:
                _require(False, "C2B2_READER_SIGNATURE_MISMATCH")
            _require(False, "private_reader_ledger")

        selects = reader["selects"]
        expected_selects = expected_reader["selects"]
        _require(
            type(selects) is list and len(selects) == len(expected_selects),
            "C2B2_READER_LITERAL_SQL_MISMATCH",
        )
        for select_index, select in enumerate(selects):
            _require(
                type(select) is dict
                and set(select) == set(expected_selects[select_index])
                and all(
                    type(select[key])
                    is type(expected_selects[select_index][key])
                    for key in expected_selects[select_index]
                ),
                "C2B2_READER_LITERAL_SQL_MISMATCH",
            )

    role_map = {reader["role"]: reader for reader in readers}
    paged = role_map["paged_program_version_membership"]
    _require(
        type(paged["maximum_members_rule"]) is str
        and type(paged["unique_work_item_ref_rule"]) is str
        and type(paged["duplicate_work_item_ref_scope"]) is list
        and type(paged["duplicate_work_item_ref_result"]) is str
        and type(paged["duplicate_work_item_ref_detection_order"]) is str,
        "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
    )
    role_nine = role_map["attempt_fence_command_effect_aggregate"]
    _require(
        type(role_nine["explicit_no_proof"]) is dict
        and set(role_nine["explicit_no_proof"]) == set(EXPECTED_ROLE_NINE_NO_PROOF)
        and all(
            type(role_nine["explicit_no_proof"][key]) is str
            for key in EXPECTED_ROLE_NINE_NO_PROOF
        )
        and type(role_nine["decoded_refs_and_digests_rule"]) is str
        and type(role_nine["granting_effect"]) is str,
        "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
    )
    role_ten = role_map["authority_evaluation_by_exact_ref"]
    _require(
        type(role_ten["authority_boundary"]) is dict
        and set(role_ten["authority_boundary"])
        == set(EXPECTED_ROLE_TEN_AUTHORITY_BOUNDARY)
        and all(
            type(role_ten["authority_boundary"][key]) is str
            for key in EXPECTED_ROLE_TEN_AUTHORITY_BOUNDARY
        ),
        "C2B2_READER_AUTHORITY_BOUNDARY_MISMATCH",
    )


def _validate_reader_validation_policy(reader_contract: dict[str, Any]) -> None:
    plan = reader_contract["validation_and_audit_plan"]
    compatibility = plan["eight_file_compatibility_group"]
    _require(
        tuple(compatibility["paths"]) == EXPECTED_EIGHT_FILE_COMPATIBILITY_GROUP
        and compatibility["warning_policy"]
        == {
            "unqualified_w_error": False,
            "warning_filters": [],
            "pytest_warning_configuration": [],
        }
        and compatibility["requirements"]
        == [
            "all tests pass",
            "zero skipped tests",
            "report every warning actually emitted",
        ]
        and compatibility["comparison_evidence"]
        == {"passed": 315, "skipped": 0, "emitted_warnings": 0}
        and compatibility["evidence_classification"]
        == "comparison evidence only; not a durable compatibility contract"
        and tuple(plan["strict_validation_groups"])
        == EXPECTED_STRICT_READER_VALIDATION_GROUPS
        and plan["full_suite_warning_policy"]
        == {
            "unqualified_w_error": False,
            "skipped": 0,
            "resource_warning_count": 0,
            "pytest_unraisable_exception_warning_count": 0,
            "permitted_warning": (
                "only the three previously classified Python 3.13 "
                "multithreaded-fork DeprecationWarnings, if they recur"
            ),
            "new_warning": "none",
        }
        and plan == EXPECTED_CONTRACT["private_readers"]["validation_and_audit_plan"],
        "C2B2_READER_VALIDATION_POLICY_MISMATCH",
    )


def _validate_readers(contract: dict[str, Any]) -> None:
    _validate_revision_edge_reader_ownership(contract)
    _validate_reader_required_keys(contract)
    reader_contract = contract["private_readers"]
    _require(type(reader_contract) is dict, "private_reader_ledger")
    readers = reader_contract["roles"]
    _require(
        tuple(item.get("role") for item in readers) == EXPECTED_READER_ROLES,
        "private_reader_roles",
    )
    tables = _table_map(contract)
    expected_readers = EXPECTED_CONTRACT["private_readers"]["roles"]
    for index, reader in enumerate(readers):
        expected_reader = expected_readers[index]
        _require(
            "future_caller" in reader,
            "C2B2_READER_FUTURE_CALLER_MISSING",
        )
        _require(
            type(reader["future_caller"]) is list
            and bool(reader["future_caller"])
            and reader["future_caller"]
            == EXPECTED_READER_FUTURE_CALLERS[reader["role"]],
            "C2B2_READER_FUTURE_CALLER_INVALID",
        )
        _require(
            reader["private_function"] == EXPECTED_PRIVATE_FUNCTIONS[index]
            and reader["signature_inputs"]
            == EXPECTED_SIGNATURE_INPUTS[reader["role"]]
            and reader["result_type"] == EXPECTED_RESULT_TYPES[reader["role"]]
            and reader["signature"]
            == "("
            + ", ".join(EXPECTED_SIGNATURE_INPUTS[reader["role"]])
            + ") -> "
            + EXPECTED_RESULT_TYPES[reader["role"]],
            "C2B2_READER_SIGNATURE_MISMATCH",
        )
        _require(reader["lookup_identity"], "reader_lookup_identity")
        _require(reader["selects"], "reader_selects")
        _require(
            reader["decoded_private_value"]
            == reader["result_type"].removesuffix(" | None"),
            "reader_private_value",
        )
        _require(reader["safe_error"] == "mutation_failed_or_database_integrity_failure", "reader_safe_error")
        _require(
            reader["nominal_capability_requirement"]
            == "type(capability) is _SQLiteMutationReadCapability before borrow or SQL",
            "reader_nominal_capability",
        )
        _require(reader["complete_mutation_family_replay_verification"] is False, "reader_replay_claim")
        _require(
            reader["query_order"] == EXPECTED_QUERY_ORDERS[reader["role"]],
            "C2B2_READER_LITERAL_SQL_MISMATCH",
        )
        _require(
            reader["absence_precedence"] == expected_reader["absence_precedence"],
            "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
        )
        _require(
            [select.get("query_id") for select in reader["selects"]]
            == [select["query_id"] for select in expected_reader["selects"]],
            "C2B2_READER_LITERAL_SQL_MISMATCH",
        )
        for select_index, select in enumerate(reader["selects"]):
            expected_select = expected_reader["selects"][select_index]
            _require(select["table"] in tables, "reader_select_table")
            _require(
                select["fields"]
                == [item["name"] for item in tables[select["table"]]["columns"]],
                "reader_ordered_select_columns",
            )
            _require(
                select == expected_select
                and type(select["query_sql"]) is str
                and type(select["parameter_order"]) is list
                and type(select["parameter_tuple"]) is str
                and select["limit"] in {2, 257}
                and select["fetch"] == f"fetchmany({select['limit']})"
                and select["query_sql"].endswith(f" LIMIT {select['limit']}"),
                "C2B2_READER_LITERAL_SQL_MISMATCH",
            )

    aggregate_fields = {
        item["type"]: item["fields"]
        for item in reader_contract["aggregate_value_contracts"]
    }
    _require(
        aggregate_fields == EXPECTED_AGGREGATE_VALUE_FIELDS,
        "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
    )
    common = reader_contract["common_contract"]
    _require(
        tuple(common["capability_path_order"])
        == EXPECTED_CAPABILITY_PATH_ORDER
        and tuple(common["capability_errors_outside_reader_safe_error"])
        == EXPECTED_CAPABILITY_ERRORS
        and tuple(common["aggregate_value_posture"])
        == EXPECTED_AGGREGATE_VALUE_POSTURE
        and common["no_partial_aggregate"] is True,
        "C2B2_READER_CAPABILITY_ORDER_MISMATCH",
    )
    _require(
        common["shared_bounded_fetch_future_contract"]["accepted_limits"]
        == [2, 257],
        "C2B2_READER_CAPABILITY_ORDER_MISMATCH",
    )

    role_map = {reader["role"]: reader for reader in readers}
    receipt = role_map["mutation_receipt_by_mutation_ref"]
    _require(
        receipt["row_digest_verification"]
        == "not_applicable: the receipt has no row self-digest"
        and receipt["slice3_cross_row_validation"]
        == [
            "exact row shape and scalar algebra",
            "result projection",
            "result_projection_digest",
            "mutation_graph_digest lowercase SHA-256 shape",
        ]
        and receipt["later_tranche_exclusions"]
        == expected_readers[0]["later_tranche_exclusions"],
        "C2B2_READER_RECEIPT_BOUNDARY_MISMATCH",
    )

    role_nine = role_map["attempt_fence_command_effect_aggregate"]
    authority_selecting_roles = [
        reader["role"]
        for reader in readers
        if any(
            select["table"] == "development_authority_evaluations"
            for select in reader["selects"]
        )
    ]
    _require(
        tuple(reader_contract["prohibited_authority_locators"])
        == EXPECTED_PROHIBITED_AUTHORITY_LOCATORS
        and role_nine["authority_evaluation_query"] is False
        and role_nine["authority_evaluation_returned"] is False
        and role_nine["implicit_authority_locator_permitted"] is False
        and role_nine["root_disposition"] == "effect_intent"
        and role_nine["later_tranche_exclusions"]
        == expected_readers[8]["later_tranche_exclusions"]
        and authority_selecting_roles == ["authority_evaluation_by_exact_ref"],
        "C2B2_READER_AUTHORITY_LOCATOR_FORBIDDEN",
    )
    _require(
        role_nine["explicit_no_proof"] == EXPECTED_ROLE_NINE_NO_PROOF
        and role_nine["decoded_refs_and_digests_rule"]
        == "The aggregate's decoded refs and digests are evidence only."
        and role_nine["granting_effect"]
        == (
            "No field, digest, row, or successful query grants authorization, "
            "route eligibility, execution permission, semantic acceptance, "
            "capsule retrieval authority, or capsule custody."
        ),
        "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
    )
    role_ten = role_map["authority_evaluation_by_exact_ref"]
    _require(
        role_ten["lookup_identity"]
        == ["program_ref", "authority_evaluation_ref"]
        and role_ten["same_subject_multiple_rows_permitted"] is True
        and role_ten["sole_authority_evaluation_reader"] is True,
        "C2B2_READER_AUTHORITY_LOCATOR_FORBIDDEN",
    )
    _require(
        role_ten["authority_boundary"] == EXPECTED_ROLE_TEN_AUTHORITY_BOUNDARY,
        "C2B2_READER_AUTHORITY_BOUNDARY_MISMATCH",
    )

    work_item = role_map["work_item_head_and_revision_by_exact_ref"]
    _require(
        work_item["historical_revision_allowed"] is True
        and work_item["is_current_rule"]
        == expected_readers[5]["is_current_rule"]
        and work_item["partial_current_match_result"]
        == "database_integrity_failure"
        and work_item["work_state_revision_kind_relation"]
        == "not frozen by this reader contract",
        "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
    )
    paged = next(item for item in readers if item["role"] == "paged_program_version_membership")
    _require(
        paged["ordering"]
        == ["membership_ordinal ASC", "work_item_ref ASC"],
        "reader_paging_order",
    )
    _require(
        paged["return_bound_per_page"] == 256
        and paged["fetch_bound"] == 257
        and paged["continuation_exposed"] is False
        and paged["returned_value_is_one_completed_aggregate"] is True
        and paged["empty_membership_permitted_program_version_kinds"] == []
        and paged["maximum_members_rule"]
        == "exact built-in positive int; bool and subclasses rejected before capability borrow"
        and paged["maximum_members_failure"]
        == "mutation_failed before the bound is exceeded",
        "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
    )
    _require(
        paged["slice3_cross_row_validation"]
        == expected_readers[6]["slice3_cross_row_validation"]
        and paged["continuation_pair"]
        == ["last_returned_membership_ordinal", "last_returned_work_item_ref"]
        and paged["all_pages_same_capability_object_and_epoch"] is True
        and paged["has_more_rule"]
        == expected_readers[6]["has_more_rule"]
        and paged["unique_work_item_ref_rule"]
        == EXPECTED_ROLE_SEVEN_UNIQUE_WORK_ITEM_REF_RULE
        and tuple(paged["duplicate_work_item_ref_scope"])
        == EXPECTED_ROLE_SEVEN_DUPLICATE_WORK_ITEM_REF_SCOPE
        and paged["duplicate_work_item_ref_result"]
        == "database_integrity_failure"
        and paged["duplicate_work_item_ref_detection_order"]
        == (
            "when the second occurrence of a work_item_ref is observed, fail "
            "before issuing a child-revision query for that duplicate occurrence"
        ),
        "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
    )
    _require(
        role_map["effect_head"]["singleton_only"] is True
        and role_map["effect_head"]["later_tranche_exclusions"]
        == expected_readers[10]["later_tranche_exclusions"]
        and role_map["delivery_head"]["later_tranche_exclusions"]
        == expected_readers[11]["later_tranche_exclusions"],
        "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
    )

    scope = reader_contract["future_implementation_allowlist"]
    scope_paths = (
        scope["new_production_source"]
        + scope["existing_production_source_modifications"]
        + scope["new_documentation"]
        + scope["existing_documentation_modifications"]
        + scope["new_focused_tests"]
        + scope["existing_test_modifications"]
    )
    _require(
        tuple(scope_paths) == EXPECTED_FUTURE_IMPLEMENTATION_PATHS
        and len(scope_paths) == len(set(scope_paths)) == 23
        and scope["maximum_path_count"] == 23
        and scope["package_or_configuration_modifications"] == []
        and scope["schema_or_migration_modifications"] == [],
        "C2B2_READER_IMPLEMENTATION_SCOPE_MISMATCH",
    )
    _require(
        "tests/test_c2b2_development_readers.py" not in scope_paths
        and "tests/test_b3b2b_select_readers.py" not in scope_paths,
        "C2B2_READER_IMPLEMENTATION_SCOPE_MISMATCH",
    )
    _validate_reader_validation_policy(reader_contract)
    _require(
        reader_contract == EXPECTED_CONTRACT["private_readers"],
        "private_reader_ledger",
    )


def _validate_boundary(contract: dict[str, Any]) -> None:
    _require(
        contract["family_replay_boundary"]
        == EXPECTED_CONTRACT["family_replay_boundary"],
        "family_replay_boundary",
    )
    _require(
        contract["nonimplementation"] == EXPECTED_CONTRACT["nonimplementation"],
        "nonimplementation",
    )
    _require(
        all(value is False for value in contract["nonimplementation"].values()),
        "nonimplementation_flags",
    )
    _require(
        contract["oracle_architecture"] == EXPECTED_CONTRACT["oracle_architecture"],
        "oracle_architecture",
    )
    boundary = contract["family_replay_boundary"]
    _require(
        boundary["proposal_replay_material_classification"]
        == "reviewed later-tranche proposal evidence; not current C2B2 contract authority",
        "proposal_evidence_classification",
    )
    _require(
        boundary["ownership"]
        == {
            "C2B3": ["initialize graph/replay", "author-effect graph/replay"],
            "C2B4": ["migration-0003 row contracts/readers only"],
            "C2B5": [
                "observation ingest graph/replay",
                "bound validation/review/cancellation effect graph/replay",
                "cancel graph/replay",
                "redeliver graph/replay",
            ],
            "C2B6": [
                "accept graph/replay",
                "repair graph/replay",
                "replan graph/replay",
                "terminal_reject graph/replay",
                "block graph/replay",
                "eligibility/latch/version/head replay",
            ],
        },
        "tranche_ownership",
    )


def _validate_contract(contract: dict[str, Any]) -> None:
    _require(set(contract) == EXPECTED_TOP_LEVEL_KEYS, "top_level_keys")
    _require(contract["contract_id"] == EXPECTED_CONTRACT["contract_id"], "contract_id")
    _validate_revision_edge_reader_ownership(contract)
    _validate_classification(contract)
    _validate_sql_core(contract)
    _validate_scalar_c2a_privacy(contract)
    _validate_decision_envelope(contract)
    _validate_receipt_envelope(contract)
    _validate_graph_primitive(contract)
    _validate_readers(contract)
    _validate_boundary(contract)


def _null(receipt: dict[str, Any], *fields: str) -> None:
    _integrity(all(receipt[field] is None for field in fields))


def _validate_receipt_scalar_instance(
    family: str,
    receipt: dict[str, Any],
    decision: dict[str, Any] | None,
    rows: dict[str, Any],
) -> None:
    _integrity(set(receipt) == set(RESULT_REFERENCE_FIELDS))
    if family == "initialize_development_program":
        _integrity(decision is not None and decision["decision_kind"] == "initialize")
        _integrity(receipt["decision_ref"] == decision["decision_ref"])
        _integrity(receipt["result_decision_ref"] == receipt["decision_ref"])
        _integrity(
            receipt["result_program_version_ref"]
            == decision["resulting_program_version_ref"]
            == rows["created_program_version_ref"]
        )
        _null(
            receipt,
            "result_semantic_attempt_ref",
            "result_effect_intent_ref",
            "result_effect_fence_ref",
            "result_delivery_attempt_ref",
            "result_observation_ref",
        )
        return

    if family in {
        "establish_development_author_effect_intent",
        "establish_development_bound_effect_intent",
    }:
        _integrity(decision is not None)
        _integrity(receipt["decision_ref"] == decision["decision_ref"])
        _integrity(
            receipt["result_program_version_ref"]
            == rows["effect_intent_program_version_ref"]
            == rows["basis_program_version_ref"]
        )
        expected_attempt_key = (
            "created_semantic_attempt_ref"
            if family == "establish_development_author_effect_intent"
            else "existing_semantic_attempt_ref"
        )
        _integrity(receipt["result_semantic_attempt_ref"] == rows[expected_attempt_key])
        _integrity(receipt["result_effect_intent_ref"] == rows["created_effect_intent_ref"])
        _integrity(receipt["result_effect_fence_ref"] == rows["created_effect_fence_ref"])
        _integrity(receipt["result_delivery_attempt_ref"] == rows["created_delivery_attempt_ref"])
        _null(receipt, "result_observation_ref", "result_decision_ref")
        return

    if family == "ingest_development_source_observation":
        _integrity(decision is None)
        _integrity(receipt["result_observation_ref"] == rows["safe_observation_result_ref"])
        _null(
            receipt,
            "decision_ref",
            "result_program_version_ref",
            "result_semantic_attempt_ref",
            "result_effect_intent_ref",
            "result_effect_fence_ref",
            "result_delivery_attempt_ref",
            "result_decision_ref",
        )
        return

    _integrity(family == "record_development_progression_decision")
    _integrity(decision is not None)
    advancing = {"accept", "repair", "replan", "terminal_reject", "block"}
    nonadvancing = {"redeliver", "cancel"}
    kind = decision["decision_kind"]
    _integrity(kind in advancing | nonadvancing)
    _integrity(receipt["decision_ref"] == decision["decision_ref"])
    _integrity(receipt["result_decision_ref"] == receipt["decision_ref"])
    if kind in advancing:
        _integrity(decision["resulting_program_version_ref"] is not None)
        expected_version = decision["resulting_program_version_ref"]
    else:
        _integrity(decision["resulting_program_version_ref"] is None)
        expected_version = decision["basis_program_version_ref"]
    _integrity(receipt["result_program_version_ref"] == expected_version)
    _null(
        receipt,
        "result_semantic_attempt_ref",
        "result_effect_intent_ref",
        "result_effect_fence_ref",
        "result_delivery_attempt_ref",
        "result_observation_ref",
    )


def _base_receipt() -> dict[str, Any]:
    return {field: None for field in RESULT_REFERENCE_FIELDS}


def _validate_graph_identity(identity: dict[str, Any]) -> None:
    graph = EXPECTED_CONTRACT["common_graph_digest_primitive"]
    expected_keys = set(graph["identity_envelope_fields"]) | {"graph_entries"}
    _integrity(set(identity) == expected_keys)
    entries = identity["graph_entries"]
    _integrity(type(entries) is list)
    role_ordinals: set[tuple[str, int]] = set()
    role_refs: set[tuple[str, str]] = set()
    expected_entry_keys = set(graph["graph_entry_ordered_keys"])
    for entry in entries:
        _integrity(type(entry) is dict and set(entry) == expected_entry_keys)
        _integrity(type(entry["role"]) is str and bool(entry["role"]))
        _integrity(type(entry["ordinal"]) is int and entry["ordinal"] >= 0)
        _integrity(type(entry["record_ref"]) is str and bool(entry["record_ref"]))
        digest = entry["record_digest"]
        _integrity(
            type(digest) is str
            and len(digest) == 64
            and digest == digest.lower()
            and all(character in "0123456789abcdef" for character in digest)
        )
        role_ordinal = (entry["role"], entry["ordinal"])
        role_ref = (entry["role"], entry["record_ref"])
        _integrity(role_ordinal not in role_ordinals)
        _integrity(role_ref not in role_refs)
        role_ordinals.add(role_ordinal)
        role_refs.add(role_ref)


def _graph_digest_from_identity(identity: dict[str, Any]) -> str:
    _validate_graph_identity(identity)
    graph = EXPECTED_CONTRACT["common_graph_digest_primitive"]
    encoded = json.dumps(
        identity,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(graph["domain"].encode("utf-8") + b"\x00" + encoded).hexdigest()


def _mutation_graph_digest(
    receipt: dict[str, Any],
    graph_entries: list[dict[str, Any]],
) -> str:
    columns = EXPECTED_CONTRACT["receipt_envelope"]["ordered_columns"]
    _integrity(set(receipt) == set(columns))
    identity = {
        key: receipt[key]
        for key in EXPECTED_CONTRACT["common_graph_digest_primitive"][
            "identity_envelope_fields"
        ]
    }
    identity["graph_entries"] = graph_entries
    return _graph_digest_from_identity(identity)


def _sample_receipt_envelope() -> dict[str, Any]:
    return {
        "schema_id": "governed-execution.nwp-development-mutation-receipt.v1",
        "mutation_ref": "mutation-1",
        "mutation_family": "initialize_development_program",
        "command_schema_id": "governed-execution.nwp-initialize-development-program-command.v1",
        "command_digest": "1" * 64,
        "program_ref": "program-1",
        "decision_ref": "decision-1",
        "result_program_version_ref": "program-version-1",
        "result_semantic_attempt_ref": None,
        "result_effect_intent_ref": None,
        "result_effect_fence_ref": None,
        "result_delivery_attempt_ref": None,
        "result_observation_ref": None,
        "result_decision_ref": "decision-1",
        "result_class": "development_program_initialized",
        "result_projection_digest": "2" * 64,
        "mutation_graph_digest": "3" * 64,
        "outcome": "committed",
        "committed_at": "2026-08-12T12:00:00Z",
    }


@dataclass(frozen=True)
class _SQLiteMutationReadCapability:
    epoch: object


class _StructuralCapabilityStandIn:
    def borrow(self) -> object:
        return object()


def _require_nominal_capability(capability: object) -> _SQLiteMutationReadCapability:
    _require(
        type(capability) is _SQLiteMutationReadCapability,
        "reader_capability_unavailable",
    )
    return capability


def _validate_work_spec_projection_instance(projection: dict[str, Any]) -> None:
    expected_keys = set(EXPECTED_CONTRACT["work_spec_safe_projection"]["ordered_keys"])
    _integrity(set(projection) == expected_keys)
    forbidden_tokens = {
        "objective",
        "requirements",
        "exclusions",
        "prompt",
        "model_response",
        "transcript",
        "candidate_bytes",
        "capsule_bytes",
        "physical_workspace_path",
        "credentials",
        "tokens",
        "private_endpoints",
        "retrieval_material",
    }
    _integrity(set(projection).isdisjoint(forbidden_tokens))


def _is_direct_expected_literal(node: ast.expr) -> bool:
    if isinstance(node, ast.Constant):
        return type(node.value) in {str, int, bool, type(None)}
    if isinstance(node, (ast.List, ast.Tuple)):
        return all(_is_direct_expected_literal(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            key is not None
            and _is_direct_expected_literal(key)
            and _is_direct_expected_literal(value)
            for key, value in zip(node.keys, node.values, strict=True)
        )
    return (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and type(node.operand.value) is int
        and node.operand.value >= 0
    )


def _read_path_expression(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name) and node.id == "OWNER_PATH":
        return "OWNER_PATH"
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Path"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "__file__"
        and not node.keywords
    ):
        return "Path(__file__)"
    return None


def _enclosing_function(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> str | None:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
        current = parents.get(current)
    return None


def _require_direct_module_literal(
    tree: ast.Module,
    assignment_name: str,
    runtime_value: object,
    identifier: str,
) -> None:
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == assignment_name
    ]
    _require(len(assignments) == 1, identifier)
    assignment_value = assignments[0].value
    _require(_is_direct_expected_literal(assignment_value), identifier)
    try:
        literal_value = ast.literal_eval(assignment_value)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        raise _ContractViolation(identifier) from None
    _require(literal_value == runtime_value, identifier)


def _node_source_position(node: ast.AST) -> tuple[int, int]:
    return (node.lineno, node.col_offset)


def _actual_import_ledger(tree: ast.Module) -> tuple[tuple[object, ...], ...]:
    imports = sorted(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ),
        key=_node_source_position,
    )
    ledger: list[tuple[object, ...]] = []
    for node in imports:
        if isinstance(node, ast.Import):
            for alias in node.names:
                ledger.append((alias.name, "import", None, alias.asname))
        else:
            module = "." * node.level + (node.module or "")
            for alias in node.names:
                ledger.append((module, "from-import", alias.name, alias.asname))
    return tuple(ledger)


def _expression_contains_callable_value(
    node: ast.AST,
    function_names: set[str],
) -> bool:
    if isinstance(node, ast.Name):
        return node.id in function_names
    if isinstance(node, ast.Call):
        return any(
            _expression_contains_callable_value(argument, function_names)
            for argument in node.args
        ) or any(
            _expression_contains_callable_value(keyword.value, function_names)
            for keyword in node.keywords
        )
    return any(
        _expression_contains_callable_value(child, function_names)
        for child in ast.iter_child_nodes(node)
    )


def _is_executable_collection_expression(node: ast.AST) -> bool:
    if isinstance(node, (ast.Dict, ast.List, ast.Set, ast.Tuple)):
        return True
    if isinstance(node, (ast.DictComp, ast.GeneratorExp, ast.ListComp, ast.SetComp)):
        return True
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"dict", "list", "set", "tuple"}
    ):
        return True
    return (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Add)
        and (
            _is_executable_collection_expression(node.left)
            or _is_executable_collection_expression(node.right)
        )
    )


def _assignment_target_names(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, (ast.List, ast.Tuple)):
        return {
            name
            for item in node.elts
            for name in _assignment_target_names(item)
        }
    return set()


def _selected_registry_value(node: ast.AST) -> bool:
    return isinstance(node, ast.Subscript) or (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
    )


def _validate_oracle_architecture(
    source: str,
    runtime_owner_test: object,
) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        raise _ContractViolation("C2B2_ORACLE_EXPECTED_NOT_LITERAL") from None

    top_level_definitions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    top_level_definition_names = [node.name for node in top_level_definitions]
    _require(
        len(top_level_definition_names) == len(set(top_level_definition_names)),
        "C2B2_ORACLE_DUPLICATE_DEFINITION",
    )
    owner_definitions = [
        node
        for node in top_level_definitions
        if node.name == OWNER_LEDGER_TEST_NAME
    ]
    _require(
        len(owner_definitions) == 1,
        "C2B2_ORACLE_RUNTIME_BINDING",
    )
    owner_definition = owner_definitions[0]

    _require_direct_module_literal(
        tree,
        "EXPECTED_CONTRACT",
        EXPECTED_CONTRACT,
        "C2B2_ORACLE_EXPECTED_NOT_LITERAL",
    )
    _require_direct_module_literal(
        tree,
        "EXPECTED_ORACLE_IMPORTS",
        EXPECTED_ORACLE_IMPORTS,
        "C2B2_ORACLE_FORBIDDEN_INPUT",
    )
    _require_direct_module_literal(
        tree,
        "EXPECTED_ORACLE_FILESYSTEM_READS",
        EXPECTED_ORACLE_FILESYSTEM_READS,
        "C2B2_ORACLE_FORBIDDEN_INPUT",
    )
    _require_direct_module_literal(
        tree,
        "EXPECTED_HASH_CALL_SITES",
        EXPECTED_HASH_CALL_SITES,
        "C2B2_ORACLE_SOURCE_HASH_AUTHORITY",
    )

    hashlib_import_count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "hashlib":
                    _require(
                        alias.asname is None,
                        "C2B2_ORACLE_SOURCE_HASH_AUTHORITY",
                    )
                    hashlib_import_count += 1
                elif alias.name.startswith("hashlib."):
                    raise _ContractViolation("C2B2_ORACLE_SOURCE_HASH_AUTHORITY")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "hashlib" or module.startswith("hashlib."):
                raise _ContractViolation("C2B2_ORACLE_SOURCE_HASH_AUTHORITY")
    _require(
        hashlib_import_count == 1,
        "C2B2_ORACLE_SOURCE_HASH_AUTHORITY",
    )

    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "hashlib":
            parent = parents.get(node)
            grandparent = parents.get(parent) if parent is not None else None
            _require(
                isinstance(parent, ast.Attribute)
                and parent.value is node
                and parent.attr == "sha256"
                and isinstance(grandparent, ast.Call)
                and grandparent.func is parent,
                "C2B2_ORACLE_SOURCE_HASH_AUTHORITY",
            )

    actual_hash_calls: list[tuple[str | None, str]] = []
    alternate_hash_constructors = {
        "adler32",
        "blake2b",
        "blake2s",
        "crc32",
        "file_digest",
        "hash",
        "md5",
        "sha1",
        "sha224",
        "sha256",
        "sha384",
        "sha3_224",
        "sha3_256",
        "sha3_384",
        "sha3_512",
        "sha512",
        "shake_128",
        "shake_256",
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "__import__":
            imported_module = (
                node.args[0].value
                if node.args
                and isinstance(node.args[0], ast.Constant)
                and type(node.args[0].value) is str
                else None
            )
            if imported_module == "hashlib" or (
                type(imported_module) is str
                and imported_module.startswith("hashlib.")
            ):
                raise _ContractViolation("C2B2_ORACLE_SOURCE_HASH_AUTHORITY")
            raise _ContractViolation("C2B2_ORACLE_FORBIDDEN_INPUT")
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "hashlib"
        ):
            _require(
                node.func.attr == "sha256",
                "C2B2_ORACLE_SOURCE_HASH_AUTHORITY",
            )
            actual_hash_calls.append(
                (_enclosing_function(node, parents), "hashlib.sha256")
            )
        elif isinstance(node.func, ast.Name) and (
            node.func.id.lower() in alternate_hash_constructors
            or "sha256" in node.func.id.lower()
        ):
            raise _ContractViolation("C2B2_ORACLE_SOURCE_HASH_AUTHORITY")
        elif (
            isinstance(node.func, ast.Attribute)
            and node.func.attr.lower() in alternate_hash_constructors
        ):
            raise _ContractViolation("C2B2_ORACLE_SOURCE_HASH_AUTHORITY")
    expected_hash_calls = tuple(
        (function_name, callee)
        for function_name, callee, count, _purpose in EXPECTED_HASH_CALL_SITES
        for _index in range(count)
    )
    _require(
        tuple(actual_hash_calls) == expected_hash_calls,
        "C2B2_ORACLE_SOURCE_HASH_AUTHORITY",
    )

    _require(
        _actual_import_ledger(tree) == EXPECTED_ORACLE_IMPORTS,
        "C2B2_ORACLE_FORBIDDEN_INPUT",
    )

    read_methods = {"exists", "is_dir", "is_file", "open", "read_bytes", "read_text", "stat"}
    actual_reads: list[tuple[str | None, str | None, str, str, str | None]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "open":
            raise _ContractViolation("C2B2_ORACLE_FORBIDDEN_INPUT")
        if isinstance(node, ast.Attribute) and node.attr in read_methods:
            parent = parents.get(node)
            _require(
                isinstance(parent, ast.Call) and parent.func is node,
                "C2B2_ORACLE_FORBIDDEN_INPUT",
            )
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr in read_methods:
            encoding_keywords = [
                keyword
                for keyword in node.keywords
                if keyword.arg == "encoding"
            ]
            encoding = (
                encoding_keywords[0].value.value
                if len(encoding_keywords) == 1
                and isinstance(encoding_keywords[0].value, ast.Constant)
                and type(encoding_keywords[0].value.value) is str
                else None
            )
            actual_reads.append(
                (
                    _enclosing_function(node, parents),
                    _read_path_expression(node.func.value),
                    node.func.attr,
                    "text" if node.func.attr == "read_text" else "other",
                    encoding,
                )
            )
            _require(
                not node.args
                and len(node.keywords) == 1
                and encoding == "utf-8",
                "C2B2_ORACLE_FORBIDDEN_INPUT",
            )
    expected_reads = tuple(
        (function_name, path_expression, method, mode, encoding)
        for function_name, path_expression, method, mode, encoding, _purpose
        in EXPECTED_ORACLE_FILESYSTEM_READS
    )
    _require(
        tuple(actual_reads) == expected_reads,
        "C2B2_ORACLE_FORBIDDEN_INPUT",
    )

    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    forbidden_dynamic_names = {
        "__import__",
        "compile",
        "eval",
        "exec",
        "getattr",
        "globals",
        "locals",
    }
    loop_bound_names = {
        name
        for node in ast.walk(tree)
        if isinstance(node, (ast.For, ast.AsyncFor))
        for name in _assignment_target_names(node.target)
    }
    loop_bound_names.update(
        name
        for node in ast.walk(tree)
        if isinstance(node, (ast.DictComp, ast.GeneratorExp, ast.ListComp, ast.SetComp))
        for generator in node.generators
        for name in _assignment_target_names(generator.target)
    )
    selected_registry_aliases: set[str] = set()
    alias_edges: list[tuple[set[str], str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = {
                name
                for target in node.targets
                for name in _assignment_target_names(target)
            }
            value = node.value
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)):
            targets = _assignment_target_names(node.target)
            value = node.value
        else:
            continue
        if _selected_registry_value(value):
            selected_registry_aliases.update(targets)
        elif isinstance(value, ast.Name):
            alias_edges.append((targets, value.id))
    changed = True
    while changed:
        changed = False
        for targets, source_name in alias_edges:
            if source_name in selected_registry_aliases:
                prior_size = len(selected_registry_aliases)
                selected_registry_aliases.update(targets)
                changed = changed or len(selected_registry_aliases) != prior_size

    for node in ast.walk(tree):
        if isinstance(node, ast.Lambda):
            raise _ContractViolation("C2B2_ORACLE_DYNAMIC_DISPATCH")
        if isinstance(node, ast.Call):
            if isinstance(node.func, (ast.Call, ast.Subscript)):
                raise _ContractViolation("C2B2_ORACLE_DYNAMIC_DISPATCH")
            if isinstance(node.func, ast.Attribute) and node.func.attr == "__call__":
                raise _ContractViolation("C2B2_ORACLE_DYNAMIC_DISPATCH")
            if isinstance(node.func, ast.Name) and node.func.id in forbidden_dynamic_names:
                raise _ContractViolation("C2B2_ORACLE_DYNAMIC_DISPATCH")
            if isinstance(node.func, ast.Name) and node.func.id in (
                loop_bound_names | selected_registry_aliases
            ):
                raise _ContractViolation("C2B2_ORACLE_DYNAMIC_DISPATCH")
            if isinstance(node.func, ast.Attribute) and node.func.attr in forbidden_dynamic_names:
                raise _ContractViolation("C2B2_ORACLE_DYNAMIC_DISPATCH")
        if (
            _is_executable_collection_expression(node)
            and _expression_contains_callable_value(node, function_names)
        ):
            raise _ContractViolation("C2B2_ORACLE_DYNAMIC_DISPATCH")
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
            value = node.value
            if isinstance(value, ast.Name) and value.id in function_names:
                raise _ContractViolation("C2B2_ORACLE_DYNAMIC_DISPATCH")

    _require(
        type(runtime_owner_test) is types.FunctionType,
        "C2B2_ORACLE_RUNTIME_BINDING",
    )
    _require(
        isinstance(owner_definition, ast.FunctionDef)
        and not owner_definition.decorator_list
        and runtime_owner_test.__module__ == __name__
        and runtime_owner_test.__name__ == OWNER_LEDGER_TEST_NAME
        and runtime_owner_test.__qualname__ == OWNER_LEDGER_TEST_NAME
        and runtime_owner_test.__code__.co_filename == __file__
        and runtime_owner_test.__code__.co_firstlineno == owner_definition.lineno
        and owner_definition.name == OWNER_LEDGER_TEST_NAME
        and "__wrapped__" not in runtime_owner_test.__dict__,
        "C2B2_ORACLE_RUNTIME_BINDING",
    )

    has_direct_semantic_equality = any(
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Name)
        and node.left.id == "owner"
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.Eq)
        and len(node.comparators) == 1
        and isinstance(node.comparators[0], ast.Name)
        and node.comparators[0].id == "EXPECTED_CONTRACT"
        for node in ast.walk(owner_definition)
    )
    has_direct_semantic_validation = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_validate_contract"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "owner"
        for node in ast.walk(owner_definition)
    )
    _require(
        has_direct_semantic_equality and has_direct_semantic_validation,
        "C2B2_ORACLE_SOURCE_HASH_AUTHORITY",
    )


def _oracle_source() -> str:
    return Path(__file__).read_text(encoding="utf-8")


def _source_has_live_oracle_architecture(source: str) -> bool:
    try:
        _validate_oracle_architecture(
            source,
            test_c2b2_owner_ledger_matches_the_independent_literal_oracle,
        )
    except _ContractViolation:
        return False
    return True


def _store_mutant_source(tmp_path: Path, name: str, source: str) -> None:
    mutant_path = tmp_path / name
    written = mutant_path.write_text(source, encoding="utf-8", newline="")
    assert written == len(source)


def _expect_oracle_architecture_rejection(source: str, expected_identifier: str) -> None:
    if expected_identifier not in _FAILURE_IDENTIFIERS:
        raise AssertionError("invalid_expected_failure_identifier")
    try:
        _validate_oracle_architecture(
            source,
            test_c2b2_owner_ledger_matches_the_independent_literal_oracle,
        )
    except _ContractViolation as exc:
        assert type(exc) is _ContractViolation
        assert exc.args == (expected_identifier,)
        return
    raise AssertionError("oracle_architecture_rejection_not_observed")


def _expect_contract_rejection(
    candidate: dict[str, Any],
    expected_identifier: str,
) -> None:
    if expected_identifier not in _FAILURE_IDENTIFIERS:
        raise AssertionError("invalid_expected_failure_identifier")
    try:
        _validate_contract(candidate)
    except _ContractViolation as exc:
        assert type(exc) is _ContractViolation
        assert exc.args == (expected_identifier,)
        return
    raise AssertionError("contract_rejection_not_observed")


def test_c2b2_owner_ledger_matches_the_independent_literal_oracle() -> None:
    owner = _owner_contract()
    assert owner == EXPECTED_CONTRACT
    _validate_contract(owner)


def test_c2b2_sql_core_and_all_nineteen_field_ledgers_are_exact() -> None:
    _validate_sql_core(EXPECTED_CONTRACT)
    tables = _table_map(EXPECTED_CONTRACT)
    assert len(tables) == 19
    assert sum(len(item["columns"]) for item in tables.values()) == 362
    for table_name in EXPECTED_TABLE_NAMES:
        item = tables[table_name]
        assert item["record_schema_id"].startswith("governed-execution.nwp-")
        assert item["record_schema_id"].endswith(".v1")
        assert item["digest_domain"].endswith(".identity")
        assert item["digest_column"] not in item["exact_digest_identity_fields"]
        assert item["self_digest_excluded"] is True
        assert set(item["timestamp_participation"]).issubset(
            {column["name"] for column in item["columns"]}
        )


def test_c2b2_scalar_c2a_and_work_spec_privacy_contracts_are_exact() -> None:
    _validate_scalar_c2a_privacy(EXPECTED_CONTRACT)
    projection = {
        key: None
        for key in EXPECTED_CONTRACT["work_spec_safe_projection"]["ordered_keys"]
    }
    _validate_work_spec_projection_instance(projection)
    private_projection = dict(projection, objective="private objective")
    with pytest.raises(_DatabaseIntegrityFailure, match="^database_integrity_failure$"):
        _validate_work_spec_projection_instance(private_projection)


def test_c2b2_decision_and_structural_receipt_envelopes_are_exact() -> None:
    _validate_decision_envelope(EXPECTED_CONTRACT)
    _validate_receipt_envelope(EXPECTED_CONTRACT)
    assert EXPECTED_CONTRACT["receipt_envelope"]["common_required_fields"] == [
        "schema_id",
        "mutation_ref",
        "mutation_family",
        "command_schema_id",
        "command_digest",
        "program_ref",
        "result_class",
        "result_projection_digest",
        "mutation_graph_digest",
        "outcome",
        "committed_at",
    ]


def test_c2b2_receipt_scalar_result_coherence_accepts_every_exact_branch() -> None:
    initialize = _base_receipt()
    initialize.update(
        decision_ref="decision-init",
        result_program_version_ref="version-1",
        result_decision_ref="decision-init",
    )
    _validate_receipt_scalar_instance(
        "initialize_development_program",
        initialize,
        {
            "decision_kind": "initialize",
            "decision_ref": "decision-init",
            "resulting_program_version_ref": "version-1",
        },
        {"created_program_version_ref": "version-1"},
    )

    author = _base_receipt()
    author.update(
        decision_ref="decision-basis",
        result_program_version_ref="version-basis",
        result_semantic_attempt_ref="attempt-new",
        result_effect_intent_ref="effect-author",
        result_effect_fence_ref="effect-fence-author",
        result_delivery_attempt_ref="delivery-initial",
    )
    author_rows = {
        "effect_intent_program_version_ref": "version-basis",
        "basis_program_version_ref": "version-basis",
        "created_semantic_attempt_ref": "attempt-new",
        "created_effect_intent_ref": "effect-author",
        "created_effect_fence_ref": "effect-fence-author",
        "created_delivery_attempt_ref": "delivery-initial",
    }
    _validate_receipt_scalar_instance(
        "establish_development_author_effect_intent",
        author,
        {"decision_ref": "decision-basis"},
        author_rows,
    )

    bound = dict(author)
    bound.update(
        result_semantic_attempt_ref="attempt-existing",
        result_effect_intent_ref="effect-bound",
        result_effect_fence_ref="effect-fence-bound",
    )
    bound_rows = dict(
        author_rows,
        existing_semantic_attempt_ref="attempt-existing",
        created_effect_intent_ref="effect-bound",
        created_effect_fence_ref="effect-fence-bound",
    )
    _validate_receipt_scalar_instance(
        "establish_development_bound_effect_intent",
        bound,
        {"decision_ref": "decision-basis"},
        bound_rows,
    )

    observation = _base_receipt()
    observation["result_observation_ref"] = "observation-safe"
    _validate_receipt_scalar_instance(
        "ingest_development_source_observation",
        observation,
        None,
        {"safe_observation_result_ref": "observation-safe"},
    )

    for kind in ("accept", "repair", "replan", "terminal_reject", "block"):
        progression = _base_receipt()
        progression.update(
            decision_ref=f"decision-{kind}",
            result_program_version_ref=f"version-result-{kind}",
            result_decision_ref=f"decision-{kind}",
        )
        _validate_receipt_scalar_instance(
            "record_development_progression_decision",
            progression,
            {
                "decision_kind": kind,
                "decision_ref": f"decision-{kind}",
                "basis_program_version_ref": "version-basis",
                "resulting_program_version_ref": f"version-result-{kind}",
            },
            {},
        )

    for kind in ("redeliver", "cancel"):
        progression = _base_receipt()
        progression.update(
            decision_ref=f"decision-{kind}",
            result_program_version_ref="version-basis",
            result_decision_ref=f"decision-{kind}",
        )
        _validate_receipt_scalar_instance(
            "record_development_progression_decision",
            progression,
            {
                "decision_kind": kind,
                "decision_ref": f"decision-{kind}",
                "basis_program_version_ref": "version-basis",
                "resulting_program_version_ref": None,
            },
            {},
        )


def test_c2b2_receipt_scalar_result_counterfactuals_fail_closed() -> None:
    failures: list[tuple[str, dict[str, Any], dict[str, Any] | None, dict[str, Any]]] = []

    initialize = _base_receipt()
    initialize.update(
        decision_ref="decision-init",
        result_decision_ref="decision-init",
        result_program_version_ref="version-basis",
    )
    failures.append(
        (
            "initialize_development_program",
            initialize,
            {
                "decision_kind": "initialize",
                "decision_ref": "decision-init",
                "resulting_program_version_ref": "version-result",
            },
            {"created_program_version_ref": "version-result"},
        )
    )

    effect = _base_receipt()
    effect.update(
        decision_ref="decision-basis",
        result_program_version_ref="version-wrong",
        result_semantic_attempt_ref="attempt-new",
        result_effect_intent_ref="effect-new",
        result_effect_fence_ref="fence-new",
        result_delivery_attempt_ref="delivery-new",
    )
    failures.append(
        (
            "establish_development_author_effect_intent",
            effect,
            {"decision_ref": "decision-basis"},
            {
                "effect_intent_program_version_ref": "version-basis",
                "basis_program_version_ref": "version-basis",
                "created_semantic_attempt_ref": "attempt-new",
                "created_effect_intent_ref": "effect-new",
                "created_effect_fence_ref": "fence-new",
                "created_delivery_attempt_ref": "delivery-new",
            },
        )
    )

    observation = _base_receipt()
    observation.update(
        result_observation_ref="observation-safe",
        result_program_version_ref="version-invented",
    )
    failures.append(
        (
            "ingest_development_source_observation",
            observation,
            None,
            {"safe_observation_result_ref": "observation-safe"},
        )
    )

    advancing = _base_receipt()
    advancing.update(
        decision_ref="decision-accept",
        result_decision_ref="decision-accept",
        result_program_version_ref="version-basis",
    )
    failures.append(
        (
            "record_development_progression_decision",
            advancing,
            {
                "decision_kind": "accept",
                "decision_ref": "decision-accept",
                "basis_program_version_ref": "version-basis",
                "resulting_program_version_ref": "version-new",
            },
            {},
        )
    )

    nonadvancing = _base_receipt()
    nonadvancing.update(
        decision_ref="decision-cancel",
        result_decision_ref="decision-cancel",
        result_program_version_ref="version-invented",
    )
    failures.append(
        (
            "record_development_progression_decision",
            nonadvancing,
            {
                "decision_kind": "cancel",
                "decision_ref": "decision-cancel",
                "basis_program_version_ref": "version-basis",
                "resulting_program_version_ref": "version-invented",
            },
            {},
        )
    )

    mismatch = _base_receipt()
    mismatch.update(
        decision_ref="decision-redeliver",
        result_decision_ref="decision-other",
        result_program_version_ref="version-basis",
    )
    failures.append(
        (
            "record_development_progression_decision",
            mismatch,
            {
                "decision_kind": "redeliver",
                "decision_ref": "decision-redeliver",
                "basis_program_version_ref": "version-basis",
                "resulting_program_version_ref": None,
            },
            {},
        )
    )

    for family, receipt, decision, rows in failures:
        with pytest.raises(_DatabaseIntegrityFailure, match="^database_integrity_failure$"):
            _validate_receipt_scalar_instance(family, receipt, decision, rows)


def test_c2b2_common_graph_digest_primitive_is_closed_and_order_sensitive() -> None:
    _validate_graph_primitive(EXPECTED_CONTRACT)
    receipt = _sample_receipt_envelope()
    entries = [
        {
            "role": "role-a",
            "ordinal": 0,
            "record_ref": "record-shared",
            "record_digest": "a" * 64,
        },
        {
            "role": "role-b",
            "ordinal": 0,
            "record_ref": "record-shared",
            "record_digest": "b" * 64,
        },
    ]
    digest = _mutation_graph_digest(receipt, entries)
    assert len(digest) == 64
    assert digest != _mutation_graph_digest(receipt, list(reversed(entries)))

    identity = {
        key: receipt[key]
        for key in EXPECTED_CONTRACT["common_graph_digest_primitive"][
            "identity_envelope_fields"
        ]
    }
    identity["graph_entries"] = entries
    canonical = json.dumps(
        identity,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert digest == hashlib.sha256(
        b"governed-execution.nwp-development-mutation-receipt.v1.identity"
        + b"\x00"
        + canonical
    ).hexdigest()


def test_c2b2_common_graph_digest_negative_controls_are_exact() -> None:
    receipt = _sample_receipt_envelope()
    entry = {
        "role": "role-a",
        "ordinal": 0,
        "record_ref": "record-a",
        "record_digest": "a" * 64,
    }

    missing_envelope = dict(receipt)
    del missing_envelope["program_ref"]
    with pytest.raises(_DatabaseIntegrityFailure, match="^database_integrity_failure$"):
        _mutation_graph_digest(missing_envelope, [entry])

    unknown_envelope = dict(receipt, metadata={})
    with pytest.raises(_DatabaseIntegrityFailure, match="^database_integrity_failure$"):
        _mutation_graph_digest(unknown_envelope, [entry])

    unknown_entry_key = dict(entry, metadata={})
    with pytest.raises(_DatabaseIntegrityFailure, match="^database_integrity_failure$"):
        _mutation_graph_digest(receipt, [unknown_entry_key])

    missing_entry_key = dict(entry)
    del missing_entry_key["record_digest"]
    with pytest.raises(_DatabaseIntegrityFailure, match="^database_integrity_failure$"):
        _mutation_graph_digest(receipt, [missing_entry_key])

    duplicate_role_ordinal = [entry, dict(entry, record_ref="record-b")]
    with pytest.raises(_DatabaseIntegrityFailure, match="^database_integrity_failure$"):
        _mutation_graph_digest(receipt, duplicate_role_ordinal)

    duplicate_role_ref = [entry, dict(entry, ordinal=1)]
    with pytest.raises(_DatabaseIntegrityFailure, match="^database_integrity_failure$"):
        _mutation_graph_digest(receipt, duplicate_role_ref)

    identity_with_self = {
        key: receipt[key]
        for key in EXPECTED_CONTRACT["common_graph_digest_primitive"][
            "identity_envelope_fields"
        ]
    }
    identity_with_self["mutation_graph_digest"] = receipt["mutation_graph_digest"]
    identity_with_self["graph_entries"] = [entry]
    with pytest.raises(_DatabaseIntegrityFailure, match="^database_integrity_failure$"):
        _graph_digest_from_identity(identity_with_self)

    same_ref_distinct_roles = [
        entry,
        dict(entry, role="role-b", record_digest="b" * 64),
    ]
    assert len(_mutation_graph_digest(receipt, same_ref_distinct_roles)) == 64


def test_c2b2_private_reader_boundary_requires_nominal_authority() -> None:
    _validate_readers(EXPECTED_CONTRACT)
    capability = _SQLiteMutationReadCapability(epoch=object())
    assert _require_nominal_capability(capability) is capability

    with pytest.raises(_ContractViolation, match="^reader_capability_unavailable$"):
        _require_nominal_capability(_StructuralCapabilityStandIn())
    with pytest.raises(_ContractViolation, match="^reader_capability_unavailable$"):
        _require_nominal_capability(object())

    class _CapabilitySubclass(_SQLiteMutationReadCapability):
        pass

    with pytest.raises(_ContractViolation, match="^reader_capability_unavailable$"):
        _require_nominal_capability(_CapabilitySubclass(epoch=object()))


def test_c2b2_reader_future_callers_are_exact() -> None:
    _validate_readers(EXPECTED_CONTRACT)
    assert {
        reader["role"]: reader["future_caller"]
        for reader in EXPECTED_CONTRACT["private_readers"]["roles"]
    } == EXPECTED_READER_FUTURE_CALLERS


def test_c2b2_reader_future_caller_counterfactuals_are_exact() -> None:
    for index, role in enumerate(EXPECTED_READER_ROLES):
        expected = EXPECTED_READER_FUTURE_CALLERS[role]

        candidate = deepcopy(EXPECTED_CONTRACT)
        del candidate["private_readers"]["roles"][index]["future_caller"]
        _expect_contract_rejection(
            candidate,
            "C2B2_READER_FUTURE_CALLER_MISSING",
        )

        candidate = deepcopy(EXPECTED_CONTRACT)
        candidate["private_readers"]["roles"][index]["future_caller"] = []
        _expect_contract_rejection(
            candidate,
            "C2B2_READER_FUTURE_CALLER_INVALID",
        )

        reordered = list(reversed(expected))
        if reordered == expected:
            reordered = ["C2B6", "C2B3"]
        candidate = deepcopy(EXPECTED_CONTRACT)
        candidate["private_readers"]["roles"][index]["future_caller"] = reordered
        _expect_contract_rejection(
            candidate,
            "C2B2_READER_FUTURE_CALLER_INVALID",
        )

        candidate = deepcopy(EXPECTED_CONTRACT)
        candidate["private_readers"]["roles"][index]["future_caller"] = expected[:-1]
        _expect_contract_rejection(
            candidate,
            "C2B2_READER_FUTURE_CALLER_INVALID",
        )

        extra_tranche = next(
            (tranche for tranche in ("C2B3", "C2B5", "C2B6") if tranche not in expected),
            expected[0],
        )
        candidate = deepcopy(EXPECTED_CONTRACT)
        candidate["private_readers"]["roles"][index]["future_caller"] = [*expected, extra_tranche]
        _expect_contract_rejection(
            candidate,
            "C2B2_READER_FUTURE_CALLER_INVALID",
        )

        for forbidden in ("C2B2", "C2B4", "C2B7"):
            candidate = deepcopy(EXPECTED_CONTRACT)
            candidate["private_readers"]["roles"][index]["future_caller"] = [*expected, forbidden]
            _expect_contract_rejection(
                candidate,
                "C2B2_READER_FUTURE_CALLER_INVALID",
            )


def test_c2b2_table_to_reader_mapping_is_exact() -> None:
    _validate_table_reader_mapping(EXPECTED_CONTRACT)
    tables = _table_map(EXPECTED_CONTRACT)
    assert {
        name: tables[name]["reader_roles"]
        for name in EXPECTED_TABLE_NAMES
    } == EXPECTED_TABLE_READER_ROLES
    assert {
        name: tables[name]["role"]
        for name in EXPECTED_TABLE_NAMES
    } == EXPECTED_TABLE_SEMANTIC_ROLES
    assert all("reader_role" not in table for table in tables.values())


def test_c2b2_table_to_reader_mapping_counterfactuals_are_exact() -> None:
    old_identities = (
        "program_head_and_current_version_by_program_ref",
        "program_version_work_membership_and_revisions",
        "attempt_fence_command_effect_graph",
        "delivery_head_and_current_attempt",
    )
    for old_identity in old_identities:
        candidate = deepcopy(EXPECTED_CONTRACT)
        candidate["tables"][0]["reader_roles"] = [old_identity]
        _expect_contract_rejection(
            candidate,
            "C2B2_TABLE_READER_ROLE_UNKNOWN",
        )

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][0]["reader_roles"] = ["unknown_reader_role"]
    _expect_contract_rejection(candidate, "C2B2_TABLE_READER_ROLE_UNKNOWN")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][0]["reader_roles"] = ["delivery_head"]
    _expect_contract_rejection(candidate, "C2B2_TABLE_READER_ROLE_MISMATCH")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][0]["reader_roles"] = []
    _expect_contract_rejection(candidate, "C2B2_TABLE_READER_ROLE_MISMATCH")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][0]["reader_roles"].append("decision_by_decision_ref")
    _expect_contract_rejection(candidate, "C2B2_TABLE_READER_ROLE_MISMATCH")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][0]["reader_roles"] = "program_head_and_current_version"
    _expect_contract_rejection(candidate, "C2B2_TABLE_READER_ROLE_MISMATCH")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][0]["role"] = "program_head_and_current_version"
    _expect_contract_rejection(candidate, "C2B2_TABLE_READER_ROLE_MISMATCH")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][0]["reader_role"] = "program_head_and_current_version"
    _expect_contract_rejection(candidate, "C2B2_TABLE_READER_ROLE_MISMATCH")


def test_c2b2_revision_edge_reader_disposition_is_exact() -> None:
    revision_edges = _table_map(EXPECTED_CONTRACT)["development_revision_edges"]
    assert revision_edges["reader_roles"] == []
    assert revision_edges["c2b2_reader_treatment"] == "durable row representation only"
    assert revision_edges["future_reader_owner"] == "C2B6"

    candidate = deepcopy(EXPECTED_CONTRACT)
    _table_map(candidate)["development_revision_edges"]["reader_roles"] = [
        "work_item_head_and_revision_by_exact_ref"
    ]
    _expect_contract_rejection(
        candidate,
        "C2B2_REVISION_EDGE_READER_OWNERSHIP",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    _table_map(candidate)["development_revision_edges"]["future_reader_owner"] = "C2B5"
    _expect_contract_rejection(
        candidate,
        "C2B2_REVISION_EDGE_READER_OWNERSHIP",
    )


def test_c2b2_reader_signatures_results_queries_and_aggregate_fields_are_exact() -> None:
    readers = EXPECTED_CONTRACT["private_readers"]["roles"]
    assert tuple(reader["private_function"] for reader in readers) == EXPECTED_PRIVATE_FUNCTIONS
    assert {
        reader["role"]: reader["signature_inputs"]
        for reader in readers
    } == EXPECTED_SIGNATURE_INPUTS
    assert {
        reader["role"]: reader["result_type"]
        for reader in readers
    } == EXPECTED_RESULT_TYPES
    assert {
        reader["role"]: reader["query_order"]
        for reader in readers
    } == EXPECTED_QUERY_ORDERS
    assert {
        item["type"]: item["fields"]
        for item in EXPECTED_CONTRACT["private_readers"]["aggregate_value_contracts"]
    } == EXPECTED_AGGREGATE_VALUE_FIELDS
    assert all(
        type(select["query_sql"]) is str
        and select["query_sql"].startswith("SELECT ")
        and select["fetch"] == f"fetchmany({select['limit']})"
        for reader in readers
        for select in reader["selects"]
    )


def test_c2b2_role_nine_authority_locator_counterfactuals_fail_exactly() -> None:
    exact_authority_select = deepcopy(
        _reader_map(EXPECTED_CONTRACT)["authority_evaluation_by_exact_ref"]["selects"][0]
    )
    for query_sql in (
        exact_authority_select["query_sql"],
        exact_authority_select["query_sql"].replace(
            " LIMIT 2",
            " ORDER BY evaluated_at DESC LIMIT 2",
        ),
        exact_authority_select["query_sql"].replace(
            " LIMIT 2",
            " ORDER BY rowid DESC LIMIT 2",
        ),
        exact_authority_select["query_sql"].replace(
            " LIMIT 2",
            " AND authority_state = 'verified' LIMIT 2",
        ),
        exact_authority_select["query_sql"].replace(
            "authority_evaluation_ref = ?",
            "evaluation_subject_ref = ?",
        ),
    ):
        candidate = deepcopy(EXPECTED_CONTRACT)
        authority_select = deepcopy(exact_authority_select)
        authority_select["query_sql"] = query_sql
        _reader_map(candidate)["attempt_fence_command_effect_aggregate"]["selects"].append(
            authority_select
        )
        _expect_contract_rejection(
            candidate,
            "C2B2_READER_AUTHORITY_LOCATOR_FORBIDDEN",
        )


def test_c2b2_role_ten_is_the_only_exact_authority_reader() -> None:
    readers = _reader_map(EXPECTED_CONTRACT)
    role_nine = readers["attempt_fence_command_effect_aggregate"]
    role_ten = readers["authority_evaluation_by_exact_ref"]
    assert all(
        select["table"] != "development_authority_evaluations"
        for select in role_nine["selects"]
    )
    assert role_ten["lookup_identity"] == [
        "program_ref",
        "authority_evaluation_ref",
    ]
    assert role_ten["same_subject_multiple_rows_permitted"] is True

    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["authority_evaluation_by_exact_ref"][
        "same_subject_multiple_rows_permitted"
    ] = False
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_AUTHORITY_LOCATOR_FORBIDDEN",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["authority_evaluation_by_exact_ref"][
        "sole_authority_evaluation_reader"
    ] = False
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_AUTHORITY_LOCATOR_FORBIDDEN",
    )


def test_c2b2_repair1_role_nine_explicit_no_proof_removals_are_rejected() -> None:
    role_nine = _reader_map(EXPECTED_CONTRACT)[
        "attempt_fence_command_effect_aggregate"
    ]
    assert role_nine["explicit_no_proof"] == EXPECTED_ROLE_NINE_NO_PROOF
    assert role_nine["decoded_refs_and_digests_rule"] == (
        "The aggregate's decoded refs and digests are evidence only."
    )
    for claim in (
        "capsule_identity",
        "capsule_custody",
        "semantic_acceptance",
        "execution_permission",
    ):
        candidate = deepcopy(EXPECTED_CONTRACT)
        del _reader_map(candidate)["attempt_fence_command_effect_aggregate"][
            "explicit_no_proof"
        ][claim]
        _expect_contract_rejection(
            candidate,
            "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
        )


def test_c2b2_repair1_role_nine_positive_proof_inversions_are_rejected() -> None:
    for claim in (
        "capsule_identity",
        "capsule_custody",
        "semantic_acceptance",
        "execution_permission",
    ):
        candidate = deepcopy(EXPECTED_CONTRACT)
        _reader_map(candidate)["attempt_fence_command_effect_aggregate"][
            "explicit_no_proof"
        ][claim] = "proved"
        _expect_contract_rejection(
            candidate,
            "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
        )


def test_c2b2_repair1_role_ten_evidence_only_boundary_is_exact() -> None:
    role_ten = _reader_map(EXPECTED_CONTRACT)[
        "authority_evaluation_by_exact_ref"
    ]
    assert role_ten["authority_boundary"] == EXPECTED_ROLE_TEN_AUTHORITY_BOUNDARY
    _validate_readers(EXPECTED_CONTRACT)

    candidate = deepcopy(EXPECTED_CONTRACT)
    del _reader_map(candidate)["authority_evaluation_by_exact_ref"][
        "authority_boundary"
    ]["evidence_only"]
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_AUTHORITY_BOUNDARY_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["authority_evaluation_by_exact_ref"][
        "authority_boundary"
    ]["executable_permission"] = "The row grants executable permission."
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_AUTHORITY_BOUNDARY_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["authority_evaluation_by_exact_ref"][
        "authority_boundary"
    ]["verified_state"] = "A verified authority state is executable permission."
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_AUTHORITY_BOUNDARY_MISMATCH",
    )

    for forbidden_reader_claim in (
        "The reader issues executable authority.",
        "The reader consumes executable authority.",
        "The reader renews executable authority.",
    ):
        candidate = deepcopy(EXPECTED_CONTRACT)
        _reader_map(candidate)["authority_evaluation_by_exact_ref"][
            "authority_boundary"
        ]["reader_authority"] = forbidden_reader_claim
        _expect_contract_rejection(
            candidate,
            "C2B2_READER_AUTHORITY_BOUNDARY_MISMATCH",
        )


def test_c2b2_bidirectional_table_reader_mapping_counterfactuals_fail_exactly() -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    _table_map(candidate)["development_program_versions"]["reader_roles"].remove(
        "paged_program_version_membership"
    )
    _expect_contract_rejection(candidate, "C2B2_TABLE_READER_ROLE_MISMATCH")

    candidate = deepcopy(EXPECTED_CONTRACT)
    _table_map(candidate)["development_work_item_revisions"]["reader_roles"].remove(
        "paged_program_version_membership"
    )
    _expect_contract_rejection(candidate, "C2B2_TABLE_READER_ROLE_MISMATCH")

    candidate = deepcopy(EXPECTED_CONTRACT)
    _table_map(candidate)["development_program_heads"]["reader_roles"].append(
        "decision_by_decision_ref"
    )
    _expect_contract_rejection(candidate, "C2B2_TABLE_READER_ROLE_MISMATCH")

    candidate = deepcopy(EXPECTED_CONTRACT)
    extra_select = deepcopy(
        _reader_map(candidate)["program_head_and_current_version"]["selects"][0]
    )
    _reader_map(candidate)["effect_head"]["selects"].append(extra_select)
    _expect_contract_rejection(
        candidate,
        "C2B2_TABLE_READER_ROLE_DIRECTION_MISMATCH",
    )


def test_c2b2_literal_sql_parameter_and_query_order_counterfactuals_fail_exactly() -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    del _reader_map(candidate)["mutation_receipt_by_mutation_ref"]["selects"][0][
        "query_sql"
    ]
    _expect_contract_rejection(candidate, "C2B2_READER_LITERAL_SQL_MISMATCH")

    candidate = deepcopy(EXPECTED_CONTRACT)
    select = _reader_map(candidate)["decision_by_decision_ref"]["selects"][0]
    select["fields"][:2] = reversed(select["fields"][:2])
    _expect_contract_rejection(candidate, "reader_ordered_select_columns")

    candidate = deepcopy(EXPECTED_CONTRACT)
    select = _reader_map(candidate)["program_head_and_current_version"]["selects"][1]
    select["parameter_order"][:2] = reversed(select["parameter_order"][:2])
    _expect_contract_rejection(candidate, "C2B2_READER_LITERAL_SQL_MISMATCH")

    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["program_head_and_current_version"]["query_order"].reverse()
    _expect_contract_rejection(candidate, "C2B2_READER_LITERAL_SQL_MISMATCH")

    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["effect_head"]["selects"][0]["limit"] = 257
    _expect_contract_rejection(candidate, "C2B2_READER_LITERAL_SQL_MISMATCH")

    candidate = deepcopy(EXPECTED_CONTRACT)
    membership_select = _reader_map(candidate)["paged_program_version_membership"][
        "selects"
    ][1]
    membership_select["limit"] = 256
    _expect_contract_rejection(candidate, "C2B2_READER_LITERAL_SQL_MISMATCH")


def test_c2b2_work_item_historical_current_counterfactuals_fail_exactly() -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["work_item_head_and_revision_by_exact_ref"][
        "historical_revision_allowed"
    ] = False
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["work_item_head_and_revision_by_exact_ref"][
        "is_current_rule"
    ] = "true when either ref or number matches"
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
    )


def test_c2b2_membership_parent_completion_and_empty_counterfactuals_fail_exactly() -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["paged_program_version_membership"]["selects"].pop(0)
    _expect_contract_rejection(
        candidate,
        "C2B2_TABLE_READER_ROLE_DIRECTION_MISMATCH",
    )

    for key, bad_value in (
        ("continuation_exposed", True),
        ("returned_value_is_one_completed_aggregate", False),
        ("empty_membership_permitted_program_version_kinds", ["initial"]),
        ("maximum_members_failure", "return a partial aggregate"),
    ):
        candidate = deepcopy(EXPECTED_CONTRACT)
        _reader_map(candidate)["paged_program_version_membership"][key] = bad_value
        _expect_contract_rejection(
            candidate,
            "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
        )


def test_c2b2_membership_dense_order_counterfactuals_fail_exactly() -> None:
    for required_rule in (
        "strict (membership_ordinal ASC, work_item_ref ASC) order",
        "no page overlap",
        "no duplicate (membership_ordinal, work_item_ref) pair",
        "dense membership ordinals exactly 0..n-1",
    ):
        candidate = deepcopy(EXPECTED_CONTRACT)
        rules = _reader_map(candidate)["paged_program_version_membership"][
            "slice3_cross_row_validation"
        ]
        rules.remove(required_rule)
        _expect_contract_rejection(
            candidate,
            "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
        )


def test_c2b2_repair1_membership_duplicate_work_item_ref_sequences_are_rejected() -> None:
    duplicate_queries: list[tuple[str, str]] = []
    with pytest.raises(
        _ContractViolation,
        match="^C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH$",
    ):
        _validate_completed_membership_work_item_refs(
            (
                (0, "work-a", "revision-a"),
                (1, "work-a", "revision-a"),
            ),
            duplicate_queries,
        )
    assert duplicate_queries == [("work-a", "revision-a")]

    different_revision_queries: list[tuple[str, str]] = []
    with pytest.raises(
        _ContractViolation,
        match="^C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH$",
    ):
        _validate_completed_membership_work_item_refs(
            (
                (0, "work-a", "revision-a"),
                (1, "work-a", "revision-b"),
            ),
            different_revision_queries,
        )
    assert different_revision_queries == [("work-a", "revision-a")]


def test_c2b2_repair1_membership_cross_page_duplicate_is_rejected_before_child_query() -> None:
    entries = (
        (0, "work-a", "revision-a"),
        *tuple(
            (ordinal, f"work-{ordinal:03d}", f"revision-{ordinal:03d}")
            for ordinal in range(1, 256)
        ),
        (256, "work-a", "revision-duplicate"),
    )
    child_revision_queries: list[tuple[str, str]] = []
    with pytest.raises(
        _ContractViolation,
        match="^C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH$",
    ):
        _validate_completed_membership_work_item_refs(
            entries,
            child_revision_queries,
        )
    assert len(child_revision_queries) == 256
    assert child_revision_queries[0] == ("work-a", "revision-a")
    assert ("work-a", "revision-duplicate") not in child_revision_queries


def test_c2b2_repair1_membership_unique_reference_positive_controls_are_exact() -> None:
    entries = (
        (0, "work-a", "shared-revision"),
        (1, "work-aa", "shared-revision"),
        (2, "work-ab", "revision-ab"),
    )
    child_revision_queries: list[tuple[str, str]] = []
    assert (
        _validate_completed_membership_work_item_refs(
            entries,
            child_revision_queries,
        )
        is entries
    )
    assert child_revision_queries == [
        ("work-a", "shared-revision"),
        ("work-aa", "shared-revision"),
        ("work-ab", "revision-ab"),
    ]


def test_c2b2_repair1_membership_uniqueness_contract_counterfactuals_are_exact() -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    del _reader_map(candidate)["paged_program_version_membership"][
        "unique_work_item_ref_rule"
    ]
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["paged_program_version_membership"][
        "unique_work_item_ref_rule"
    ] = "Dense membership ordinals establish uniqueness."
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["paged_program_version_membership"][
        "unique_work_item_ref_rule"
    ] = "Query ordering establishes uniqueness."
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["paged_program_version_membership"][
        "slice3_cross_row_validation"
    ].remove("each work_item_ref appears at most once in the completed aggregate")
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
    )


def test_c2b2_root_child_precedence_counterfactuals_fail_exactly() -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["program_head_and_current_version"]["absence_precedence"][
        "absent_root"
    ] = "return None after child SQL"
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["initialize_decision_and_resulting_version"][
        "absence_precedence"
    ]["malformed_or_duplicate_root"] = "continue to child SQL"
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
    )


def test_c2b2_effect_head_and_receipt_boundary_counterfactuals_fail_exactly() -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["effect_head"]["later_tranche_exclusions"].remove(
        "current effect-fence fetch or coherence"
    )
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["mutation_receipt_by_mutation_ref"][
        "later_tranche_exclusions"
    ].remove("default graph_entries to ()")
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_RECEIPT_BOUNDARY_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    _reader_map(candidate)["mutation_receipt_by_mutation_ref"][
        "later_tranche_exclusions"
    ].remove("family completeness")
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_RECEIPT_BOUNDARY_MISMATCH",
    )


def test_c2b2_capability_order_and_error_separation_counterfactuals_fail_exactly() -> None:
    common = EXPECTED_CONTRACT["private_readers"]["common_contract"]
    assert tuple(common["capability_path_order"]) == EXPECTED_CAPABILITY_PATH_ORDER
    assert tuple(common["capability_errors_outside_reader_safe_error"]) == EXPECTED_CAPABILITY_ERRORS

    candidate = deepcopy(EXPECTED_CONTRACT)
    path_order = candidate["private_readers"]["common_contract"][
        "capability_path_order"
    ]
    path_order[2], path_order[3] = path_order[3], path_order[2]
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_CAPABILITY_ORDER_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    path_order = candidate["private_readers"]["common_contract"][
        "capability_path_order"
    ]
    path_order[2], path_order[4] = path_order[4], path_order[2]
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_CAPABILITY_ORDER_MISMATCH",
    )


def test_c2b2_future_implementation_allowlist_22_and_24_path_counterfactuals_fail() -> None:
    scope = EXPECTED_CONTRACT["private_readers"]["future_implementation_allowlist"]
    assert len(EXPECTED_FUTURE_IMPLEMENTATION_PATHS) == scope["maximum_path_count"] == 23

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["private_readers"]["future_implementation_allowlist"][
        "existing_test_modifications"
    ].pop()
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_IMPLEMENTATION_SCOPE_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["private_readers"]["future_implementation_allowlist"][
        "existing_test_modifications"
    ].append("tests/twenty_fourth_path.py")
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_IMPLEMENTATION_SCOPE_MISMATCH",
    )


def test_c2b2_repair1_future_implementation_path_substitutions_are_rejected() -> None:
    scope = EXPECTED_CONTRACT["private_readers"]["future_implementation_allowlist"]
    assert len(EXPECTED_FUTURE_IMPLEMENTATION_PATHS) == 23
    assert len(set(EXPECTED_FUTURE_IMPLEMENTATION_PATHS)) == 23
    assert scope["new_focused_tests"][-1] == (
        "tests/test_c2b2_private_development_readers.py"
    )
    assert "tests/test_c2a_nonimplementation.py" in scope["existing_test_modifications"]
    assert "tests/test_c2b2_development_readers.py" not in EXPECTED_FUTURE_IMPLEMENTATION_PATHS
    assert "tests/test_b3b2b_select_readers.py" not in EXPECTED_FUTURE_IMPLEMENTATION_PATHS

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["private_readers"]["future_implementation_allowlist"][
        "new_focused_tests"
    ][-1] = "tests/test_c2b2_development_readers.py"
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_IMPLEMENTATION_SCOPE_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    existing_tests = candidate["private_readers"]["future_implementation_allowlist"][
        "existing_test_modifications"
    ]
    existing_tests[existing_tests.index("tests/test_c2a_nonimplementation.py")] = (
        "tests/test_b3b2b_select_readers.py"
    )
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_IMPLEMENTATION_SCOPE_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate_scope = candidate["private_readers"]["future_implementation_allowlist"]
    candidate_scope["new_focused_tests"][-1] = (
        "tests/test_c2b2_development_readers.py"
    )
    candidate_existing_tests = candidate_scope["existing_test_modifications"]
    candidate_existing_tests[
        candidate_existing_tests.index("tests/test_c2a_nonimplementation.py")
    ] = "tests/test_b3b2b_select_readers.py"
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_IMPLEMENTATION_SCOPE_MISMATCH",
    )


def test_c2b2_repair1_future_implementation_path_count_and_duplicate_controls_are_exact() -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["private_readers"]["future_implementation_allowlist"][
        "existing_test_modifications"
    ].append("tests/twenty_fourth_path.py")
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_IMPLEMENTATION_SCOPE_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["private_readers"]["future_implementation_allowlist"][
        "existing_test_modifications"
    ].pop()
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_IMPLEMENTATION_SCOPE_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    existing_tests = candidate["private_readers"]["future_implementation_allowlist"][
        "existing_test_modifications"
    ]
    existing_tests[-1] = existing_tests[0]
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_IMPLEMENTATION_SCOPE_MISMATCH",
    )


def test_c2b2_repair1_required_reader_key_removals_use_fixed_diagnostics() -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    del _reader_map(candidate)["paged_program_version_membership"][
        "maximum_members_rule"
    ]
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    del _reader_map(candidate)["paged_program_version_membership"][
        "unique_work_item_ref_rule"
    ]
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_MEMBERSHIP_CONTRACT_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    del _reader_map(candidate)["attempt_fence_command_effect_aggregate"][
        "explicit_no_proof"
    ]
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_AGGREGATE_CONTRACT_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    del _reader_map(candidate)["authority_evaluation_by_exact_ref"][
        "authority_boundary"
    ]["evidence_only"]
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_AUTHORITY_BOUNDARY_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    del candidate["private_readers"]["future_implementation_allowlist"]
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_IMPLEMENTATION_SCOPE_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    del candidate["private_readers"]["validation_and_audit_plan"][
        "eight_file_compatibility_group"
    ]["warning_policy"]
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_VALIDATION_POLICY_MISMATCH",
    )


def test_c2b2_repair1_validation_policy_counterfactuals_are_exact() -> None:
    _validate_reader_validation_policy(EXPECTED_CONTRACT["private_readers"])

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["private_readers"]["validation_and_audit_plan"][
        "eight_file_compatibility_group"
    ]["warning_policy"]["unqualified_w_error"] = True
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_VALIDATION_POLICY_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["private_readers"]["validation_and_audit_plan"][
        "eight_file_compatibility_group"
    ]["warning_policy"]["warning_filters"].append("ignore::ResourceWarning")
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_VALIDATION_POLICY_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["private_readers"]["validation_and_audit_plan"][
        "eight_file_compatibility_group"
    ]["warning_policy"]["pytest_warning_configuration"].append(
        "filterwarnings=ignore"
    )
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_VALIDATION_POLICY_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["private_readers"]["validation_and_audit_plan"][
        "eight_file_compatibility_group"
    ]["paths"].remove("tests/test_b3c1b_rollback_only_writer_fencing.py")
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_VALIDATION_POLICY_MISMATCH",
    )

    candidate = deepcopy(EXPECTED_CONTRACT)
    paths = candidate["private_readers"]["validation_and_audit_plan"][
        "eight_file_compatibility_group"
    ]["paths"]
    paths[-1] = "tests/test_b3c1a_mutation_authority.py"
    _expect_contract_rejection(
        candidate,
        "C2B2_READER_VALIDATION_POLICY_MISMATCH",
    )


def test_c2b2_exact_failure_identifiers_reject_weak_expectations() -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["metadata"] = {}

    with pytest.raises(AssertionError):
        _expect_contract_rejection(candidate, "")
    with pytest.raises(AssertionError):
        _expect_contract_rejection(candidate, "top_level")
    with pytest.raises(AssertionError):
        _expect_contract_rejection(candidate, "sql_core")

    try:
        _validate_contract(candidate)
    except _ContractViolation as exc:
        assert type(exc) is _ContractViolation
        assert str(exc) == "top_level_keys"
        assert "/" not in str(exc)
    else:
        raise AssertionError("exact_failure_identifier_not_observed")


def test_oracle_architecture_accepts_live_literal_oracle() -> None:
    _validate_oracle_architecture(
        _oracle_source(),
        test_c2b2_owner_ledger_matches_the_independent_literal_oracle,
    )


def test_oracle_architecture_rejects_duplicate_owner_test_definition(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    owner_definition = (
        "def test_c2b2_owner_ledger_matches_the_independent_literal_oracle() -> None:\n"
        "    owner = _owner_contract()\n"
        "    assert owner == EXPECTED_CONTRACT\n"
        "    _validate_contract(owner)\n"
    )
    assert source.count(owner_definition) == 1
    mutant = source + "\n\n" + owner_definition
    _store_mutant_source(tmp_path, "duplicate_owner_test.py", mutant)
    _expect_oracle_architecture_rejection(
        mutant,
        "C2B2_ORACLE_DUPLICATE_DEFINITION",
    )


def test_oracle_architecture_binds_to_runtime_owner_test_function(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    _store_mutant_source(tmp_path, "runtime_binding_source.py", source)
    _validate_oracle_architecture(
        source,
        test_c2b2_owner_ledger_matches_the_independent_literal_oracle,
    )
    try:
        _validate_oracle_architecture(source, _oracle_source)
    except _ContractViolation as exc:
        assert type(exc) is _ContractViolation
        assert exc.args == ("C2B2_ORACLE_RUNTIME_BINDING",)
    else:
        raise AssertionError("oracle_runtime_binding_rejection_not_observed")


def test_oracle_architecture_rejects_aliased_sha256_source_hash_acceptance(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    import_anchor = "import hashlib\n"
    owner_anchor = (
        "def test_c2b2_owner_ledger_matches_the_independent_literal_oracle() -> None:\n"
        "    owner = _owner_contract()\n"
        "    assert owner == EXPECTED_CONTRACT\n"
        "    _validate_contract(owner)\n"
    )
    owner_replacement = (
        "def test_c2b2_owner_ledger_matches_the_independent_literal_oracle() -> None:\n"
        "    owner_source = OWNER_PATH.read_bytes()\n"
        "    assert _audit_hash(owner_source).hexdigest() == _audit_hash(owner_source).hexdigest()\n"
    )
    assert source.count(import_anchor) == 1
    assert source.count(owner_anchor) == 1
    mutant = source.replace(
        import_anchor,
        import_anchor + "from hashlib import sha256 as _audit_hash\n",
        1,
    ).replace(owner_anchor, owner_replacement, 1)
    _store_mutant_source(tmp_path, "aliased_sha256_source_hash.py", mutant)
    _expect_oracle_architecture_rejection(
        mutant,
        "C2B2_ORACLE_SOURCE_HASH_AUTHORITY",
    )


def test_oracle_architecture_rejects_dynamic_hashlib_import(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    mutant = source + (
        "\n\ndef _audit_dynamic_hash_import():\n"
        "    return __import__(\"hashlib\").sha256(b\"owner source\").hexdigest()\n"
    )
    _store_mutant_source(tmp_path, "dynamic_hashlib_import.py", mutant)
    _expect_oracle_architecture_rejection(
        mutant,
        "C2B2_ORACLE_SOURCE_HASH_AUTHORITY",
    )


def test_oracle_architecture_rejects_sqlite3_dbapi2_import(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    anchor = "import json\n"
    assert source.count(anchor) == 1
    mutant = source.replace(
        anchor,
        anchor + "from sqlite3.dbapi2 import connect as _audit_connect\n",
        1,
    )
    _store_mutant_source(tmp_path, "sqlite3_dbapi2_import.py", mutant)
    _expect_oracle_architecture_rejection(
        mutant,
        "C2B2_ORACLE_FORBIDDEN_INPUT",
    )


def test_oracle_architecture_rejects_packaged_test_import(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    anchor = "import pytest\n"
    assert source.count(anchor) == 1
    mutant = source.replace(
        anchor,
        anchor + "from tests import test_architecture_contracts as _audit_test_module\n",
        1,
    )
    _store_mutant_source(tmp_path, "packaged_test_import.py", mutant)
    _expect_oracle_architecture_rejection(
        mutant,
        "C2B2_ORACLE_FORBIDDEN_INPUT",
    )


def test_oracle_architecture_rejects_aliased_builtin_open_external_read(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    import_anchor = "import ast\n"
    owner_anchor = "    owner = OWNER_PATH.read_text(encoding=\"utf-8\")\n"
    assert source.count(import_anchor) == 1
    assert source.count(owner_anchor) == 1
    mutant = source.replace(
        import_anchor,
        import_anchor + "from builtins import open as _audit_open\n",
        1,
    ).replace(
        owner_anchor,
        "    owner = _audit_open(\"external-proposal.json\", encoding=\"utf-8\").read()\n",
        1,
    )
    _store_mutant_source(tmp_path, "aliased_builtin_open.py", mutant)
    _expect_oracle_architecture_rejection(
        mutant,
        "C2B2_ORACLE_FORBIDDEN_INPUT",
    )


def test_oracle_architecture_rejects_dict_constructor_loop_dispatch(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    dispatch_helper = (
        "\n\ndef _audit_dispatch_through_dict_constructor(contract):\n"
        "    validators = dict(owner=_validate_contract)\n"
        "    for validator in validators.values():\n"
        "        validator(contract)\n"
    )
    mutant = source + dispatch_helper
    _store_mutant_source(tmp_path, "dict_constructor_loop_dispatch.py", mutant)
    _expect_oracle_architecture_rejection(
        mutant,
        "C2B2_ORACLE_DYNAMIC_DISPATCH",
    )


def test_oracle_architecture_rejects_registry_selected_alias_dispatch(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    mutant = source + (
        "\n\ndef _audit_registry_selected_alias(registry, contract):\n"
        "    validator = registry.get(\"owner\")\n"
        "    validator(contract)\n"
    )
    _store_mutant_source(tmp_path, "registry_selected_alias.py", mutant)
    _expect_oracle_architecture_rejection(
        mutant,
        "C2B2_ORACLE_DYNAMIC_DISPATCH",
    )


def test_oracle_architecture_rejects_mapping_comprehension_dispatch(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    mutant = source + (
        "\n\ndef _audit_mapping_comprehension_dispatch(registry, contract):\n"
        "    return [validator(contract) for validator in registry.values()]\n"
    )
    _store_mutant_source(tmp_path, "mapping_comprehension_dispatch.py", mutant)
    _expect_oracle_architecture_rejection(
        mutant,
        "C2B2_ORACLE_DYNAMIC_DISPATCH",
    )


def test_revision_edge_query_locator_replay_and_reader_surfaces_use_exact_identifier(
    tmp_path: Path,
) -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    _table_map(candidate)["development_revision_edges"]["c2b2_query"] = "SELECT"
    (tmp_path / "revision_edge_query.json").write_text(
        json.dumps(candidate, sort_keys=True),
        encoding="utf-8",
        newline="",
    )
    _expect_contract_rejection(candidate, "C2B2_REVISION_EDGE_READER_OWNERSHIP")

    candidate = deepcopy(EXPECTED_CONTRACT)
    _table_map(candidate)["development_revision_edges"]["c2b2_locator"] = "locator"
    (tmp_path / "revision_edge_locator.json").write_text(
        json.dumps(candidate, sort_keys=True),
        encoding="utf-8",
        newline="",
    )
    _expect_contract_rejection(candidate, "C2B2_REVISION_EDGE_READER_OWNERSHIP")

    candidate = deepcopy(EXPECTED_CONTRACT)
    _table_map(candidate)["development_revision_edges"]["c2b2_replay"] = "replay"
    _expect_contract_rejection(candidate, "C2B2_REVISION_EDGE_READER_OWNERSHIP")

    candidate = deepcopy(EXPECTED_CONTRACT)
    _table_map(candidate)["development_revision_edges"]["historical_postimage"] = "postimage"
    _expect_contract_rejection(candidate, "C2B2_REVISION_EDGE_READER_OWNERSHIP")

    candidate = deepcopy(EXPECTED_CONTRACT)
    _table_map(candidate)["development_revision_edges"]["c2b2_reader"] = "reader"
    _expect_contract_rejection(candidate, "C2B2_REVISION_EDGE_READER_OWNERSHIP")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["private_readers"]["roles"][0]["selects"].append(
        {
            "fields": ["relation_key_digest"],
            "table": "development_revision_edges",
        }
    )
    _expect_contract_rejection(candidate, "C2B2_REVISION_EDGE_READER_OWNERSHIP")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["private_readers"]["roles"][0]["selects"][0]["fields"].append(
        "relation_key_digest"
    )
    _expect_contract_rejection(candidate, "C2B2_REVISION_EDGE_READER_OWNERSHIP")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["private_readers"]["roles"][0]["lookup_identity"].append(
        "relation_key_digest"
    )
    _expect_contract_rejection(candidate, "C2B2_REVISION_EDGE_READER_OWNERSHIP")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["private_readers"]["roles"].append(
        {
            "lookup_identity": ["relation_key_digest"],
            "role": "revision_edge_by_exact_ref",
            "selects": [
                {
                    "fields": ["relation_key_digest"],
                    "table": "development_revision_edges",
                }
            ],
        }
    )
    _expect_contract_rejection(candidate, "C2B2_REVISION_EDGE_READER_OWNERSHIP")

    candidate = deepcopy(EXPECTED_CONTRACT)
    _table_map(candidate)["development_revision_edges"]["future_reader_owner"] = "C2B5"
    _expect_contract_rejection(candidate, "C2B2_REVISION_EDGE_READER_OWNERSHIP")

    candidate = deepcopy(EXPECTED_CONTRACT)
    del _table_map(candidate)["development_revision_edges"]["future_reader_owner"]
    _expect_contract_rejection(candidate, "C2B2_REVISION_EDGE_READER_OWNERSHIP")

    candidate = deepcopy(EXPECTED_CONTRACT)
    _table_map(candidate)["development_revision_edges"]["c2b2_reader_treatment"] = "reader"
    _expect_contract_rejection(candidate, "C2B2_REVISION_EDGE_READER_OWNERSHIP")


def test_oracle_architecture_rejects_owner_document_derived_expected_truth(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    anchor = "EXPECTED_CONTRACT = {\n"
    replacement = (
        "def _derive_expected_from_owner_document():\n"
        "    owner_text = OWNER_PATH.read_text(encoding=\"utf-8\")\n"
        "    payload = owner_text.split(BEGIN_MARKER, 1)[1].split(END_MARKER, 1)[0].strip()\n"
        "    return json.loads(payload[len(\"```json\\n\"):-len(\"\\n```\")])\n\n\n"
        "EXPECTED_CONTRACT = _derive_expected_from_owner_document()\n"
        "_UNUSED_LITERAL_EXPECTED_CONTRACT = {\n"
    )
    assert source.count(anchor) == 1
    mutant = source.replace(anchor, replacement, 1)
    _store_mutant_source(tmp_path, "owner_derived.py", mutant)
    _expect_oracle_architecture_rejection(
        mutant,
        "C2B2_ORACLE_EXPECTED_NOT_LITERAL",
    )


def test_oracle_architecture_rejects_external_sql_derived_inventory(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    anchor = "EXPECTED_TABLE_NAMES = (\n"
    replacement = (
        "def _derive_table_names_from_external_sql():\n"
        "    sql_inventory = Path(__file__).with_name(\"external.sql\").read_text(encoding=\"utf-8\")\n"
        "    return tuple(json.loads(sql_inventory)[\"table_names\"])\n\n\n"
        "EXPECTED_TABLE_NAMES = _derive_table_names_from_external_sql()\n"
        "_UNUSED_LITERAL_EXPECTED_TABLE_NAMES = (\n"
    )
    assert source.count(anchor) == 1
    mutant = source.replace(anchor, replacement, 1)
    _store_mutant_source(tmp_path, "external_sql_derived.py", mutant)
    _expect_oracle_architecture_rejection(mutant, "C2B2_ORACLE_FORBIDDEN_INPUT")


def test_oracle_architecture_rejects_sqlite_introspection_derived_inventory(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    import_anchor = "import json\n"
    assignment_anchor = "EXPECTED_TABLE_NAMES = (\n"
    assert source.count(import_anchor) == 1
    assert source.count(assignment_anchor) == 1
    mutant = source.replace(import_anchor, import_anchor + "import sqlite3 as _oracle_sqlite3\n", 1)
    replacement = (
        "def _derive_table_names_from_sqlite_introspection():\n"
        "    connection = _oracle_sqlite3.connect(\":memory:\")\n"
        "    for table_name in EXPECTED_CONTRACT[\"sql_core\"][\"table_names_in_order\"]:\n"
        "        connection.execute(f'CREATE TABLE \"{table_name}\" (value ANY) STRICT')\n"
        "    rows = connection.execute(\"SELECT name FROM sqlite_schema WHERE type='table' ORDER BY rowid\").fetchall()\n"
        "    connection.close()\n"
        "    return tuple(row[0] for row in rows)\n\n\n"
        "EXPECTED_TABLE_NAMES = _derive_table_names_from_sqlite_introspection()\n"
        "_UNUSED_LITERAL_EXPECTED_TABLE_NAMES = (\n"
    )
    mutant = mutant.replace(assignment_anchor, replacement, 1)
    _store_mutant_source(tmp_path, "sqlite_introspection_derived.py", mutant)
    _expect_oracle_architecture_rejection(mutant, "C2B2_ORACLE_FORBIDDEN_INPUT")


def test_oracle_architecture_rejects_proposal_json_derived_ledger(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    anchor = "EXPECTED_TABLE_NAMES = (\n"
    replacement = (
        "def _derive_table_names_from_proposal_json():\n"
        "    proposal = json.loads(Path(__file__).with_name(\"proposal.json\").read_text(encoding=\"utf-8\"))\n"
        "    return tuple(table[\"name\"] for table in proposal[\"tables\"])\n\n\n"
        "EXPECTED_TABLE_NAMES = _derive_table_names_from_proposal_json()\n"
        "_UNUSED_LITERAL_EXPECTED_TABLE_NAMES = (\n"
    )
    assert source.count(anchor) == 1
    mutant = source.replace(anchor, replacement, 1)
    _store_mutant_source(tmp_path, "proposal_json_derived.py", mutant)
    _expect_oracle_architecture_rejection(mutant, "C2B2_ORACLE_FORBIDDEN_INPUT")


def test_oracle_architecture_rejects_production_source_derived_generation(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    anchor = "\nEXPECTED_TOP_LEVEL_KEYS = frozenset(\n"
    insertion = (
        "\ndef _derive_generation_from_production_source():\n"
        "    production = Path(__file__).with_name(\"sqlite_migration.py\").read_text(encoding=\"utf-8\")\n"
        "    line = next(item for item in production.splitlines() if item.startswith(\"CURRENT_APPLICATION_SCHEMA = \"))\n"
        "    return int(line.rsplit(\" \", 1)[1])\n\n\n"
        "_PRODUCTION_GENERATION = _derive_generation_from_production_source()\n"
        "EXPECTED_CONTRACT[\"classification\"][\"current_implemented_contract\"] = "
        "EXPECTED_CONTRACT[\"classification\"][\"current_implemented_contract\"].replace(\"generation 2\", f\"generation {_PRODUCTION_GENERATION}\")\n"
        "\nEXPECTED_TOP_LEVEL_KEYS = frozenset(\n"
    )
    assert source.count(anchor) == 1
    mutant = source.replace(anchor, insertion, 1)
    _store_mutant_source(tmp_path, "production_source_derived.py", mutant)
    _expect_oracle_architecture_rejection(mutant, "C2B2_ORACLE_FORBIDDEN_INPUT")


def test_oracle_architecture_rejects_another_collected_test_derived_inventory(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    import_anchor = "import pytest\n"
    assignment_anchor = "EXPECTED_TABLE_NAMES = (\n"
    assert source.count(import_anchor) == 1
    assert source.count(assignment_anchor) == 1
    mutant = source.replace(
        import_anchor,
        import_anchor + "from test_other_inventory import EXPECTED_TABLE_NAMES as _OTHER_TEST_TABLE_NAMES\n",
        1,
    )
    mutant = mutant.replace(
        assignment_anchor,
        "EXPECTED_TABLE_NAMES = tuple(_OTHER_TEST_TABLE_NAMES)\n"
        "_UNUSED_LITERAL_EXPECTED_TABLE_NAMES = (\n",
        1,
    )
    _store_mutant_source(tmp_path, "collected_test_derived.py", mutant)
    _expect_oracle_architecture_rejection(mutant, "C2B2_ORACLE_FORBIDDEN_INPUT")


def test_oracle_architecture_rejects_generic_dispatch_table_validator(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    anchor = (
        "def _validate_contract(contract: dict[str, Any]) -> None:\n"
        "    _require(set(contract) == EXPECTED_TOP_LEVEL_KEYS, \"top_level_keys\")\n"
        "    _require(contract[\"contract_id\"] == EXPECTED_CONTRACT[\"contract_id\"], \"contract_id\")\n"
        "    _validate_revision_edge_reader_ownership(contract)\n"
        "    _validate_classification(contract)\n"
        "    _validate_sql_core(contract)\n"
        "    _validate_scalar_c2a_privacy(contract)\n"
        "    _validate_decision_envelope(contract)\n"
        "    _validate_receipt_envelope(contract)\n"
        "    _validate_graph_primitive(contract)\n"
        "    _validate_readers(contract)\n"
        "    _validate_boundary(contract)\n"
    )
    replacement = (
        "def _validate_contract(contract: dict[str, Any]) -> None:\n"
        "    _require(set(contract) == EXPECTED_TOP_LEVEL_KEYS, \"top_level_keys\")\n"
        "    _require(contract[\"contract_id\"] == EXPECTED_CONTRACT[\"contract_id\"], \"contract_id\")\n"
        "    _validate_revision_edge_reader_ownership(contract)\n"
        "    validators = {\n"
        "        \"classification\": _validate_classification,\n"
        "        \"sql\": _validate_sql_core,\n"
        "        \"scalar\": _validate_scalar_c2a_privacy,\n"
        "        \"decision\": _validate_decision_envelope,\n"
        "        \"receipt\": _validate_receipt_envelope,\n"
        "        \"graph\": _validate_graph_primitive,\n"
        "        \"readers\": _validate_readers,\n"
        "        \"boundary\": _validate_boundary,\n"
        "    }\n"
        "    for validator_name in (\"classification\", \"sql\", \"scalar\", \"decision\", \"receipt\", \"graph\", \"readers\", \"boundary\"):\n"
        "        validators[validator_name](contract)\n"
    )
    assert source.count(anchor) == 1
    mutant = source.replace(anchor, replacement, 1)
    _store_mutant_source(tmp_path, "generic_dispatch.py", mutant)
    _expect_oracle_architecture_rejection(mutant, "C2B2_ORACLE_DYNAMIC_DISPATCH")


def test_oracle_architecture_rejects_arbitrary_callable_registry_validator(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    anchor = "    _validate_contract(owner)\n"
    replacement = (
        "    callable_registry = [_validate_contract]\n"
        "    callable_registry[0](owner)\n"
    )
    assert source.count(anchor) == 1
    mutant = source.replace(anchor, replacement, 1)
    _store_mutant_source(tmp_path, "callable_registry.py", mutant)
    _expect_oracle_architecture_rejection(mutant, "C2B2_ORACLE_DYNAMIC_DISPATCH")


def test_oracle_architecture_rejects_source_hash_only_acceptance(
    tmp_path: Path,
) -> None:
    source = _oracle_source()
    if not _source_has_live_oracle_architecture(source):
        return
    anchor = (
        "def test_c2b2_owner_ledger_matches_the_independent_literal_oracle() -> None:\n"
        "    owner = _owner_contract()\n"
        "    assert owner == EXPECTED_CONTRACT\n"
        "    _validate_contract(owner)\n"
    )
    replacement = (
        "def test_c2b2_owner_ledger_matches_the_independent_literal_oracle() -> None:\n"
        "    owner_source = OWNER_PATH.read_bytes()\n"
        "    assert hashlib.sha256(owner_source).hexdigest() == hashlib.sha256(owner_source).hexdigest()\n"
    )
    assert source.count(anchor) == 1
    mutant = source.replace(anchor, replacement, 1)
    _store_mutant_source(tmp_path, "source_hash_only.py", mutant)
    _expect_oracle_architecture_rejection(
        mutant,
        "C2B2_ORACLE_SOURCE_HASH_AUTHORITY",
    )


def test_c2b2_sql_core_counterfactual_matrix_rejects_every_shape_change() -> None:
    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"].pop()
    _expect_contract_rejection(candidate, "table_ledger_order")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"].append(deepcopy(candidate["tables"][-1]))
    _expect_contract_rejection(candidate, "table_ledger_order")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][:2] = reversed(candidate["tables"][:2])
    _expect_contract_rejection(candidate, "table_ledger_order")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][0]["columns"][:2] = reversed(candidate["tables"][0]["columns"][:2])
    _expect_contract_rejection(candidate, "table_field_ledger")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][0]["columns"][0]["sqlite_declaration_type"] = "TEXT"
    _expect_contract_rejection(candidate, "table_field_ledger")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][0]["columns"][0]["nullable"] = True
    _expect_contract_rejection(candidate, "table_field_ledger")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][0]["columns"][0]["check_sql"] = "typeof(schema_id)='blob'"
    _expect_contract_rejection(candidate, "table_field_ledger")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][0]["columns"][1]["pk_ordinal"] = 0
    _expect_contract_rejection(candidate, "table_field_ledger")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][5]["unique_constraints"].append(["program_ref"])
    _expect_contract_rejection(candidate, "table_field_ledger")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["foreign_keys"][0]["parent_table"] = "development_decisions"
    _expect_contract_rejection(candidate, "foreign_key_ledger")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["foreign_keys"][0]["on_delete"] = "CASCADE"
    _expect_contract_rejection(candidate, "foreign_key_ledger")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["foreign_keys"][0]["deferrability"] = "NOT DEFERRABLE INITIALLY IMMEDIATE"
    _expect_contract_rejection(candidate, "foreign_key_ledger")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["triggers"].pop()
    _expect_contract_rejection(candidate, "trigger_ledger")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["triggers"].append(deepcopy(candidate["triggers"][-1]))
    _expect_contract_rejection(candidate, "trigger_ledger")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["explicit_indexes"].append({"name": "second_index"})
    _expect_contract_rejection(candidate, "explicit_index_ledger")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][0]["seed_rows"].append({"program_ref": "seed"})
    _expect_contract_rejection(candidate, "table_field_ledger")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["sql_core"]["current_migration_0001_changed"] = True
    _expect_contract_rejection(candidate, "sql_core")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["sql_core"]["migration_0003_present"] = True
    _expect_contract_rejection(candidate, "sql_core")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["tables"][0]["columns"].append(
        {
            "name": "metadata",
            "sqlite_declaration_type": "ANY",
            "logical_type": "generic_payload",
            "nullable": True,
            "check_sql": None,
            "pk_ordinal": 0,
        }
    )
    _expect_contract_rejection(candidate, "table_field_ledger")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["metadata"] = {}
    _expect_contract_rejection(candidate, "top_level_keys")


def test_c2b2_decision_replay_and_ownership_counterfactuals_fail() -> None:
    for kind in ("redeliver", "cancel"):
        candidate = deepcopy(EXPECTED_CONTRACT)
        variant = next(
            row
            for row in candidate["decision_envelope"]["variant_matrix"]
            if row["kind"] == kind
        )
        variant["version_advancing"] = True
        _expect_contract_rejection(candidate, "decision_envelope")

    for frozen_item in (
        "complete mutation-family replay graphs",
        "historical mutable-head replay",
        "family graph locators",
    ):
        candidate = deepcopy(EXPECTED_CONTRACT)
        candidate["family_replay_boundary"]["c2b2_does_not_freeze_or_implement"].remove(
            frozen_item
        )
        _expect_contract_rejection(candidate, "family_replay_boundary")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["nonimplementation"]["mutation_or_recovery_api"] = True
    _expect_contract_rejection(candidate, "nonimplementation")

    for tranche, item in (
        ("C2B3", "initialize graph/replay"),
        ("C2B3", "author-effect graph/replay"),
        ("C2B5", "observation ingest graph/replay"),
        ("C2B5", "bound validation/review/cancellation effect graph/replay"),
        ("C2B5", "cancel graph/replay"),
        ("C2B5", "redeliver graph/replay"),
        ("C2B6", "accept graph/replay"),
    ):
        candidate = deepcopy(EXPECTED_CONTRACT)
        candidate["family_replay_boundary"]["ownership"][tranche].remove(item)
        _expect_contract_rejection(candidate, "family_replay_boundary")

    candidate = deepcopy(EXPECTED_CONTRACT)
    candidate["family_replay_boundary"]["ownership"]["C2B4"].append("mutation runtime")
    _expect_contract_rejection(candidate, "family_replay_boundary")

    for flag in (
        "public_reader",
        "state_store_method",
        "writer_session_method",
        "package_root_export",
        "dependency",
    ):
        candidate = deepcopy(EXPECTED_CONTRACT)
        candidate["nonimplementation"][flag] = True
        _expect_contract_rejection(candidate, "nonimplementation")


def test_historical_field_freeze_nonimplementation_object_is_preserved() -> None:
    _validate_boundary(EXPECTED_CONTRACT)
    assert EXPECTED_CONTRACT["nonimplementation"] == {
        "complete_family_replay": False,
        "database_mutation": False,
        "dependency": False,
        "migration_0002_repository_sql": False,
        "migration_0003_pulled_forward": False,
        "mutation_or_recovery_api": False,
        "package_root_export": False,
        "production_source": False,
        "public_reader": False,
        "runtime_authority": False,
        "state_store_method": False,
        "writer_session_method": False,
    }


def test_slice2_source_boundary_is_exactly_four_private_modules() -> None:
    package = ROOT / "src/ge_nwp_coordinator"
    present = tuple(
        sorted(path.name for path in package.glob("_development_*row_value*.py"))
    )
    assert present == EXPECTED_SLICE2_PRODUCTION_MODULES
