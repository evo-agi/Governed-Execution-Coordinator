"""Independent direct-literal oracle for the C2B3A initialization freeze."""

import ast
from copy import deepcopy
from pathlib import Path

import pytest


ORACLE_SOURCE_PATH = Path(__file__)
ORACLE_SOURCE_PARENT = ORACLE_SOURCE_PATH.parents[1]
ROOT = ORACLE_SOURCE_PARENT.resolve()
OWNER_PATH = ROOT / ".docs" / "c2b-durable-development-state.md"
PLANNING_PATH = ROOT / ".docs" / "c2b3-program-initialization.md"
TEST_PATH = ROOT / "tests" / "test_c2b3_program_initialization_contract.py"
BEGIN_MARKER = "<!-- C2B3_PROGRAM_INITIALIZATION_CONTRACT_PYTHON_BEGIN -->"
END_MARKER = "<!-- C2B3_PROGRAM_INITIALIZATION_CONTRACT_PYTHON_END -->"
VECTOR_BEGIN_MARKER = (
    "<!-- C2B3_PROGRAM_INITIALIZATION_GOLDEN_VECTOR_PYTHON_BEGIN -->"
)
VECTOR_END_MARKER = "<!-- C2B3_PROGRAM_INITIALIZATION_GOLDEN_VECTOR_PYTHON_END -->"
ALLOWED_ORACLE_IMPORTS = ("ast", "copy", "pathlib", "pytest")
ALLOWED_ORACLE_RELATIVE_PATHS = (
    ".docs/c2b-durable-development-state.md",
    ".docs/c2b3-program-initialization.md",
    "tests/test_c2b3_program_initialization_contract.py",
)
PLANNING_AUTHORITY_CLAIMS = (
    "the planning document is semantic authority",
    "the planning document co-owns semantic truth",
)
PLANNING_CURRENT_SOURCE_CLAIMS = (
    "program initialization source is current",
    "program initialization is implemented",
    "private delegation is current",
    "receipt persistence is current",
    "replay runtime is current",
    "recovery runtime is current",
    "author-effect source is current",
)


EXPECTED_INITIALIZATION_CONTRACT = {
    "contract_identity": {
        "workstream": "COORDINATOR_C2B3A_PROGRAM_INITIALIZATION_CONTRACT_FREEZE",
        "repository_tranche": "C2B3 — Program Initialization And Author-Effect Establishment",
        "this_freeze": "C2B3A program-initialization contract only",
        "semantic_owner": ".docs/c2b-durable-development-state.md#35-c2b3a-program-initialization-contract-freeze",
        "status_record": ".docs/c2b3-program-initialization.md",
        "status_record_authority": "planning only; not semantic authority",
        "implementation_status": "contract frozen; production source absent",
    },
    "tranche_boundary": {
        "C2B3A": "program-initialization contract only",
        "C2B3B": "later private atomic initialization implementation",
        "C2B3C": "later author-effect contract freeze",
        "C2B3D": "later private atomic author-effect implementation",
        "combined_family_implementation": False,
    },
    "five_path_scope": {
        "tracked_modifications": (
            ".docs/c2b-durable-development-state.md",
            "tests/test_c2b0_durable_state_contract.py",
            "AGENTS.md",
        ),
        "untracked_additions": (
            ".docs/c2b3-program-initialization.md",
            "tests/test_c2b3_program_initialization_contract.py",
        ),
        "total_paths": 5,
        "production_source_paths": (),
        "migration_paths": (),
        "schema_paths": (),
        "public_api_paths": (),
    },
    "owner_decisions": {
        "initial_work_item_count": 1,
        "initial_work_spec_count": 1,
        "membership_ordinal": 0,
        "first_author_attempt_number": 1,
        "initial_author_basis": ("initialize", "program_genesis"),
        "planned_adapter_kind": "execution_substrate",
        "route_effect": "absent",
        "work_spec_ingress": "same-call transient only",
        "work_spec_custody": "absent",
        "recovery_lifecycle": "close-complete-gated later call under a newly acquired concrete session and fresh operation lease",
        "automatic_semantic_retry": False,
        "family_graph_membership": "family-created rows only",
        "duplicate_program_classification": "semantic_identity_conflict",
    },
    "initialization_golden_vector": {
        "owner_literal_marker": "C2B3_PROGRAM_INITIALIZATION_GOLDEN_VECTOR_PYTHON",
        "oracle_literal_name": "EXPECTED_INITIALIZATION_GOLDEN_VECTOR",
        "vector_id": "c2b3a-initialization-single-work-v1",
        "vector_version": 1,
        "family": "initialize_development_program",
        "single_work": True,
        "direct_owner_literal": True,
        "direct_independent_oracle_literal": True,
        "oracle_runtime_derivation": False,
        "proves_implementation": False,
        "required_components": (
            "all safe command input values",
            "exact WorkSpec safe-projection mapping",
            "exact accepted-intent canonical mapping and UTF-8 byte-hex",
            "accepted-intent safe-projection digest",
            "exact safe-command canonical mapping and UTF-8 byte-hex",
            "command digest",
            "one transaction timestamp",
            "all nine complete persisted row mappings and applicable self-digests",
            "program-head and work-item-head historical postimages",
            "all eight ordered graph entries with rank, role, ordinal, ref, and digest",
            "exact result projection and digest",
            "mutation-graph digest",
            "complete mutation-receipt scalar envelope",
            "private committed result",
            "private exact-replay result",
        ),
    },
    "semantic_ref_ownership": {
        "owner": "semantic caller",
        "preassigned_refs": (
            "mutation_ref",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "decision_ref",
            "work_item_ref",
            "work_item_revision_ref",
            "work_spec_ref",
            "preassigned_semantic_attempt_ref",
            "preassigned_candidate_ref",
        ),
        "initializer_generated_semantic_refs": (),
        "forbidden_ref_derivations": (
            "random",
            "UUID",
            "clock-derived",
            "rowid-derived",
            "implicit",
        ),
        "coordinator_derived_values": (
            "fixed genesis numbers and states",
            "dense ordinal 0",
            "one transaction timestamp",
            "safe projections",
            "canonical identities",
            "row digests",
            "result projection digest",
            "mutation graph digest",
            "complete locator material",
        ),
    },
    "existing_work_spec_safe_projection": {
        "semantic_name": "DevelopmentWorkSpecSafeProjection",
        "schema_id": "governed-execution.nwp-development-work-spec-safe-projection.v1",
        "digest_domain": "governed-execution.nwp-development-work-spec-safe-projection.v1.identity",
        "ordered_fields": (
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
            "work_spec_digest",
            "safe_projection_digest",
        ),
        "replacement_invented": False,
        "source_or_identity_modified": False,
    },
    "accepted_intent_safe_projection": {
        "semantic_name": "DevelopmentAcceptedIntentSafeProjectionV1",
        "schema_id": "governed-execution.nwp-development-accepted-intent-safe-projection.v1",
        "digest_domain": "governed-execution.nwp-development-accepted-intent-safe-projection.v1.identity",
        "ordered_fields": (
            "schema_id",
            "source_intent_ref",
            "source_intent_digest",
            "initial_work_spec_safe_projection",
            "safe_projection_digest",
        ),
        "identity_excludes": ("safe_projection_digest",),
        "nested_projection_exact_type": "DevelopmentWorkSpecSafeProjection",
        "derived_from": (
            "caller-supplied source_intent_ref",
            "caller-supplied source_intent_digest",
            "exact transient WorkSpecV1",
            "existing WorkSpec safe-projection builder",
        ),
        "caller_forbidden": (
            "completed accepted-intent projection",
            "safe_projection_digest",
            "generic mapping",
            "substitute WorkSpec safe projection",
            "subclass or structural stand-in",
        ),
        "private_fields_absent": (
            "objective",
            "requirements text",
            "exclusions text",
            "prompt",
            "response",
            "transcript",
            "credential",
            "endpoint",
            "retrieval material",
            "capsule content",
            "workspace path",
        ),
        "persisted_row_fields": (
            "source_intent_ref",
            "source_intent_digest",
            "safe_projection_digest",
        ),
    },
    "sensitive_ingress": {
        "work_spec_type": "exact built-in WorkSpecV1",
        "work_spec_count": 1,
        "container_ingress": False,
        "additional_inputs": (
            "all preassigned safe semantic refs",
            "caller-supplied source_intent_ref",
            "caller-supplied source_intent_digest",
            "expected coding_global_stop_ref",
            "expected coding_global_stop_version",
        ),
        "caller": "future Coordinator-internal semantic/progression caller already holding the exact value",
        "possession_meaning": "input provenance only; not executable authority",
        "closed_outcomes": (
            "one complete safe initialization command",
            "one closed privacy-safe failure discriminant",
        ),
        "retrieval_by_ref": False,
        "restart_safe_retrieval": False,
        "private_custody_store": False,
    },
    "safe_command": {
        "semantic_name": "DevelopmentProgramInitializationCommandV1",
        "schema_id": "governed-execution.nwp-initialize-development-program-command.v1",
        "digest_domain": "governed-execution.nwp-initialize-development-program-command.v1.identity",
        "ordered_fields": (
            "schema_id",
            "mutation_ref",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "decision_ref",
            "preassigned_semantic_attempt_ref",
            "preassigned_candidate_ref",
            "coding_global_stop_ref",
            "coding_global_stop_version",
            "reason_code",
            "work_spec_safe_projection",
            "accepted_intent_safe_projection",
            "command_digest",
        ),
        "exact_field_types": (
            ("schema_id", "str"),
            ("mutation_ref", "str"),
            ("program_ref", "str"),
            ("program_version_ref", "str"),
            ("accepted_intent_revision_ref", "str"),
            ("decision_ref", "str"),
            ("preassigned_semantic_attempt_ref", "str"),
            ("preassigned_candidate_ref", "str"),
            ("coding_global_stop_ref", "str"),
            ("coding_global_stop_version", "int excluding bool"),
            ("reason_code", "str"),
            ("work_spec_safe_projection", "exact DevelopmentWorkSpecSafeProjection"),
            ("accepted_intent_safe_projection", "exact DevelopmentAcceptedIntentSafeProjectionV1"),
            ("command_digest", "str"),
        ),
        "reason_code": "program_genesis",
        "identity_excludes": ("command_digest",),
        "digest_owner": "Coordinator sensitive reducer",
        "cross_relations": (
            "work_spec_safe_projection.program_ref == command.program_ref",
            "work_spec_safe_projection.program_version_ref == command.program_version_ref",
            "work_spec_safe_projection.accepted_intent_revision_ref == command.accepted_intent_revision_ref",
            "accepted_intent_safe_projection.initial_work_spec_safe_projection == command.work_spec_safe_projection",
            "accepted_intent_safe_projection.source_intent_ref == persisted accepted-intent source_intent_ref",
            "accepted_intent_safe_projection.source_intent_digest == persisted accepted-intent source_intent_digest",
            "preassigned_attempt_candidate_binding.work_item_ref == safe command work_spec_safe_projection.work_item_ref == sole program-version membership work_item_ref == sole WorkSpec binding work_item_ref",
            "preassigned_attempt_candidate_binding.work_item_revision_ref == safe command work_spec_safe_projection.work_item_revision_ref == sole program-version membership work_item_revision_ref == sole WorkSpec binding work_item_revision_ref",
            "preassigned_attempt_candidate_binding.preassigned_semantic_attempt_ref == safe command preassigned_semantic_attempt_ref == initialize decision preassigned_semantic_attempt_ref",
            "preassigned_attempt_candidate_binding.preassigned_candidate_ref == safe command preassigned_candidate_ref == initialize decision preassigned_candidate_ref",
        ),
        "rejects": (
            "Boolean as integer",
            "subclasses",
            "coercion",
            "generic mappings",
            "extension fields",
            "optional metadata",
            "caller-supplied digests",
            "implicit refs",
            "zero WorkSpecs",
            "multiple WorkSpecs",
            "caller-supplied membership ordinal",
            "implicit sorting",
        ),
        "contains_complete_work_spec": False,
    },
    "genesis_cardinality": {
        "program_versions": 1,
        "accepted_intent_revisions": 1,
        "work_item_heads": 1,
        "work_item_revisions": 1,
        "program_version_memberships": 1,
        "work_spec_safe_bindings": 1,
        "preassigned_attempt_candidate_binding": {
            "ordered_fields": (
                "work_item_ref",
                "work_item_revision_ref",
                "preassigned_semantic_attempt_ref",
                "preassigned_candidate_ref",
            ),
            "relations": (
                "preassigned_attempt_candidate_binding.work_item_ref == safe command work_spec_safe_projection.work_item_ref == sole program-version membership work_item_ref == sole WorkSpec binding work_item_ref",
                "preassigned_attempt_candidate_binding.work_item_revision_ref == safe command work_spec_safe_projection.work_item_revision_ref == sole program-version membership work_item_revision_ref == sole WorkSpec binding work_item_revision_ref",
                "preassigned_attempt_candidate_binding.preassigned_semantic_attempt_ref == safe command preassigned_semantic_attempt_ref == initialize decision preassigned_semantic_attempt_ref",
                "preassigned_attempt_candidate_binding.preassigned_candidate_ref == safe command preassigned_candidate_ref == initialize decision preassigned_candidate_ref",
            ),
            "future_lineage_only": True,
            "creates_selects_authorizes_or_executes_attempt_or_candidate": False,
        },
        "hidden_selection_rule": False,
        "permanent_one_work_item_architecture": False,
        "later_additional_work_owner": "C2B6 replan mechanics",
    },
    "row_and_head_ledger": {
        "inserted_row_count": 9,
        "inserted_rows": (
            "program_head",
            "program_version",
            "accepted_intent_revision",
            "work_item_head",
            "work_item_revision",
            "program_version_work_item",
            "work_spec_binding",
            "initialize_decision",
            "mutation_receipt",
        ),
        "postimages": {
            "program_head": (
                ("current_program_version_number", 1),
                ("current_program_version_ref", "exact program_version_ref"),
                ("head_revision", 0),
                ("program_state", "active"),
            ),
            "program_version": (
                ("program_version_number", 1),
                ("program_version_kind", "initial"),
                ("creating_decision_ref", "exact decision_ref"),
            ),
            "accepted_intent_revision": (
                ("accepted_intent_revision_number", 1),
                ("prior_accepted_intent_revision_ref", None),
                ("safe_projection_digest", "derived accepted-intent safe_projection_digest"),
            ),
            "work_item_head": (
                ("current_work_item_revision_number", 1),
                ("current_work_item_revision_ref", "exact work_item_revision_ref"),
                ("head_revision", 0),
                ("work_state", "planned"),
            ),
            "work_item_revision": (
                ("work_item_revision_number", 1),
                ("work_item_revision_kind", "initial"),
                ("prior_work_item_revision_ref", None),
            ),
            "program_version_work_item": (
                ("membership_ordinal", 0),
                ("work_item_ref", "exact work_item_ref"),
                ("work_item_revision_ref", "exact work_item_revision_ref"),
            ),
            "work_spec_binding": (
                ("safe_projection", "exact existing DevelopmentWorkSpecSafeProjection"),
                ("recorded_at", "one transaction timestamp"),
            ),
            "initialize_decision": (
                ("decision_kind", "initialize"),
                ("decision_variant", "program_genesis"),
                ("basis_decision_ref", None),
                ("basis_program_version_ref", None),
                ("basis_semantic_attempt_ref", None),
                ("basis_effect_intent_ref", None),
                ("expected_program_head_revision", 0),
                ("resulting_program_version_number", 1),
                ("resulting_program_version_ref", "exact program_version_ref"),
                ("selected_semantic_attempt_ref", None),
                ("selected_candidate_ref", None),
                ("preassigned_semantic_attempt_ref", "exact preassigned_semantic_attempt_ref"),
                ("preassigned_candidate_ref", "exact preassigned_candidate_ref"),
                ("reason_code", "program_genesis"),
            ),
            "mutation_receipt": (
                ("mutation_family", "initialize_development_program"),
                ("outcome", "committed"),
            ),
        },
        "single_transaction_timestamp": True,
        "absent_rows_and_effects": (
            "revision_edge",
            "semantic_attempt",
            "effect",
            "command row",
            "delivery",
            "observation",
            "capsule",
            "Git row",
            "external request",
        ),
    },
    "write_order": {
        "foreign_keys_continuously_enabled": True,
        "ordered_rows": (
            "program_head",
            "accepted_intent_revision",
            "work_item_head",
            "work_item_revision",
            "initialize_decision",
            "program_version",
            "program_version_work_item",
            "work_spec_binding",
            "mutation_receipt",
        ),
    },
    "initialize_graph": {
        "entry_count": 8,
        "receipt_is_envelope": True,
        "receipt_is_entry": False,
        "entries": (
            (0, "program_head_postimage", 0, "program_ref"),
            (1, "accepted_intent_revision", 0, "accepted_intent_revision_ref"),
            (2, "initialize_decision", 0, "decision_ref"),
            (3, "program_version", 0, "program_version_ref"),
            (4, "work_item_head_postimage", 0, "work_item_ref"),
            (5, "work_item_revision", 0, "work_item_revision_ref"),
            (6, "program_version_work_item", 0, "work_item_ref"),
            (7, "work_spec_binding", 0, "work_spec_ref"),
        ),
        "ordering": ("rank ASC", "ordinal ASC"),
        "mutable_preimages": "exact absence; not graph entries",
        "basis_and_global_stop_rows": "verified dependencies; not graph entries",
        "same_ref_distinct_roles_allowed": "work_item_ref",
        "digest_primitive": "existing common supplied-entry mutation-graph digest primitive",
    },
    "complete_graph_locator": {
        "starts_from": ("exact safe command", "mutation receipt"),
        "lookups": (
            "receipt by mutation_ref",
            "initialize decision and resulting version by program_ref + decision_ref",
            "accepted-intent revision by program_ref + accepted_intent_revision_ref",
            "program head by program_ref",
            "sole complete membership by program_ref + program_version_ref",
            "work-item head and exact revision by program_ref + work_item_ref + work_item_revision_ref",
            "WorkSpec binding by exact program/version/work/revision identity, then exact work_spec_ref equality",
        ),
        "completeness": (
            "exactly one membership",
            "membership ordinal 0",
            "exactly one matching WorkSpec binding",
            "returned binding work_spec_ref equals safe-command work_spec_ref and graph-entry expected work_spec_ref",
            "all row self-digests valid",
            "all cross-row relations valid",
            "historical program-head postimage valid",
            "historical work-head postimage valid",
            "persisted result projection valid",
            "mutation graph digest valid",
        ),
        "physical_lookup_key": (
            "program_ref",
            "program_version_ref",
            "work_item_ref",
            "work_item_revision_ref",
        ),
        "returned_work_spec_ref_mismatch": "database_integrity_failure",
        "forbidden_selection": ("absence", "latest row", "timestamp", "rowid", "scan", "different WorkSpec"),
        "generic_graph_engine": False,
        "future_reads": "bounded family-specific absence/collision reads only",
    },
    "persisted_result_projection": {
        "schema_id": "governed-execution.nwp-initialize-development-program-result.v1",
        "digest_domain": "governed-execution.nwp-initialize-development-program-result.v1.identity",
        "ordered_fields": (
            "schema_id",
            "program_ref",
            "decision_ref",
            "result_program_version_ref",
            "result_decision_ref",
        ),
        "result_program_version_ref": "exactly program_version_ref",
        "result_decision_ref": "exactly decision_ref",
    },
    "private_apply_result": {
        "semantic_name": "DevelopmentProgramInitializationResultV1",
        "ordered_fields": (
            "disposition",
            "mutation_ref",
            "command_digest",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "decision_ref",
            "work_item_ref",
            "work_item_revision_ref",
            "work_spec_ref",
            "preassigned_semantic_attempt_ref",
            "preassigned_candidate_ref",
            "transaction_timestamp",
        ),
        "dispositions": ("committed", "exact_replay"),
    },
    "private_outcome_ownership": {
        "future_module": "src/ge_nwp_coordinator/_development_program_initialization_contracts.py",
        "module_present_this_turn": False,
        "package_root_export": False,
        "conflict_reason": {
            "semantic_name": "DevelopmentProgramInitializationConflictReasonV1",
            "values": (
                "mutation_ref_reuse_conflict",
                "global_stop_version_conflict",
                "coding_global_stop_active",
                "semantic_identity_conflict",
            ),
        },
        "conflict_result": {
            "semantic_name": "DevelopmentProgramInitializationConflictV1",
            "ordered_fields": ("reason", "mutation_ref", "command_digest", "program_ref"),
            "reason_type": "exact DevelopmentProgramInitializationConflictReasonV1",
            "posture": (
                "not persisted",
                "not canonical durable identity",
                "not a SQLite safe error",
                "not a public apply-conflict value",
                "not package-exported",
                "not authority",
            ),
        },
        "recovery_disposition": {
            "semantic_name": "DevelopmentProgramInitializationRecoveryDispositionV1",
            "values": ("committed_exact", "definitely_not_committed", "unresolved"),
        },
        "existing_sqlite_store_error_reasons": (
            "database_integrity_failure",
            "mutation_failed",
            "commit_outcome_unknown",
        ),
        "public_surfaces_unchanged": (
            "models.APPLY_CONFLICT_REASONS",
            "sqlite_errors",
            "package root",
            "StateStore",
            "public WriterSession protocol",
        ),
    },
    "mutation_receipt": {
        "family": "initialize_development_program",
        "command_schema_id": "governed-execution.nwp-initialize-development-program-command.v1",
        "result_class": "development_program_initialized",
        "result_attempt_ref": None,
        "result_effect_ref": None,
        "result_fence_ref": None,
        "result_delivery_ref": None,
        "result_observation_ref": None,
        "outcome": "committed",
        "self_digest": None,
        "graph_entry_count": 8,
        "failed_fresh_receipt": False,
    },
    "exact_replay": {
        "after_writer_fencing": True,
        "ordered_steps": (
            "read receipt by mutation_ref",
            "absent receipt selects fresh path",
            "present receipt with different command digest is mutation_ref_reuse_conflict",
            "validate receipt family, schema, and scalar algebra",
            "locate all eight graph entries",
            "validate every row self-digest",
            "validate all program/version/decision/intent/work/membership/WorkSpec relations",
            "reconstruct historical program and work head postimages",
            "recompute accepted-intent projection, persisted result projection, and graph digest",
            "return original private result with disposition exact_replay",
        ),
        "incomplete_or_malformed_graph": "database_integrity_failure",
        "contradictory_same_revision_head": "database_integrity_failure",
        "later_valid_head_advancement": "allowed; historical replay remains exact",
        "later_C2B6_lineage_proven": False,
    },
    "commit_uncertainty_cleanup_gate": {
        "commit_attempt_exception": "controller records commit_outcome_unknown",
        "raw_connection_owner_before_close": "transaction controller retains exclusive custody",
        "close_attempt_precedes": (
            "clearing controller connection custody",
            "making the mutation slot available",
            "returning commit_outcome_unknown to the caller",
        ),
        "close_complete": {
            "controller_connection_custody": "cleared",
            "mutation_slot_available": True,
            "session_quarantined": False,
            "outward_store_error": "commit_outcome_unknown",
            "original_apply_error": {
                "type": "SQLiteMutationStoreError",
                "reason": "commit_outcome_unknown",
                "internal_detail": None,
                "cause": None,
                "context": None,
                "notes": None,
                "raised_from": None,
            },
            "slot_release_gate": "only after close proof",
            "fresh_resolver": "permitted later under a new operation lease and reacquired same shared slot",
        },
        "close_not_proved": {
            "ordered_steps": (
                "commit attempt raises",
                "controller retains connection custody and mutation slot",
                "close is attempted",
                "close not proved",
                "connection custody transfers to private _WriterSessionResource",
                "session quarantine is recorded",
                "writer-authority lock remains retained",
                "mutation slot remains unavailable",
                "fresh content-free commit_outcome_unknown is raised from None",
            ),
            "raw_connection_custody": "transferred to and retained by private _WriterSessionResource",
            "session_state": "commit-uncertain quarantined",
            "writer_authority_lock": "retained by that concrete session",
            "mutation_slot_available": False,
            "original_apply_error": {
                "type": "SQLiteMutationStoreError",
                "reason": "commit_outcome_unknown",
                "internal_detail": None,
                "cause": None,
                "context": None,
                "notes": None,
                "raised_from": None,
            },
            "close_failure_role": "secondary",
            "close_failure_replaces_primary_error": False,
            "close_failure_decorates_primary_error": False,
            "close_failure_leaks_outward": False,
            "close_exception_in_outward_error_graph": False,
            "same_session_mutation": False,
            "same_session_database_backed_resolver": False,
            "same_session_resolver_disposition": "unresolved before operation-lease acquisition, database open, BEGIN, or SQL",
            "permitted_work": "explicit close/finalization of the retained connection only",
            "new_session_resolver_before_proved_close": False,
            "definitely_not_committed": False,
            "automatic_semantic_retry": False,
            "process_control_close_interruption_ordered_steps": (
                "observe the exact process-control exception object from connection close",
                "retain the mutation slot",
                "retain the writer-authority lock",
                "transfer the uncertain raw connection into the private _WriterSessionResource",
                "publish the concrete session as commit-uncertain quarantined",
                "confirm same-session mutation and database-backed recovery remain forbidden",
                "confirm no operation lease, database open, BEGIN, or SQL can occur",
                "re-raise the identical process-control exception object",
            ),
            "process_control_exceptions": {
                "KeyboardInterrupt": {
                    "exception_identity_preserved": True,
                    "connection_custody_transferred_before_propagation": True,
                    "quarantine_published_before_propagation": True,
                    "writer_lock_retained_before_propagation": True,
                    "mutation_slot_retained_before_propagation": True,
                    "same_session_database_recovery_allowed": False,
                    "operation_lease_allowed_before_close_proof": False,
                    "database_open_allowed_before_close_proof": False,
                    "begin_allowed_before_close_proof": False,
                    "sql_allowed_before_close_proof": False,
                    "ordinary_store_error_conversion": False,
                    "automatic_semantic_retry": False,
                },
                "SystemExit": {
                    "exception_identity_preserved": True,
                    "connection_custody_transferred_before_propagation": True,
                    "quarantine_published_before_propagation": True,
                    "writer_lock_retained_before_propagation": True,
                    "mutation_slot_retained_before_propagation": True,
                    "same_session_database_recovery_allowed": False,
                    "operation_lease_allowed_before_close_proof": False,
                    "database_open_allowed_before_close_proof": False,
                    "begin_allowed_before_close_proof": False,
                    "sql_allowed_before_close_proof": False,
                    "ordinary_store_error_conversion": False,
                    "automatic_semantic_retry": False,
                },
                "GeneratorExit": {
                    "exception_identity_preserved": True,
                    "connection_custody_transferred_before_propagation": True,
                    "quarantine_published_before_propagation": True,
                    "writer_lock_retained_before_propagation": True,
                    "mutation_slot_retained_before_propagation": True,
                    "same_session_database_recovery_allowed": False,
                    "operation_lease_allowed_before_close_proof": False,
                    "database_open_allowed_before_close_proof": False,
                    "begin_allowed_before_close_proof": False,
                    "sql_allowed_before_close_proof": False,
                    "ordinary_store_error_conversion": False,
                    "automatic_semantic_retry": False,
                },
            },
            "process_control_exception_graph_ledger": (
                {
                    "branch_name": "KeyboardInterrupt",
                    "propagation_form": "bare_reraise",
                    "same_exception_object": True,
                    "exact_type_preserved": True,
                    "args_preserved": True,
                    "system_exit_code_preserved_or_not_applicable": "not_applicable",
                    "caught_traceback_tail_identity_preserved": True,
                    "repair_owned_traceback_frame_delta": 0,
                    "cause_before": None,
                    "cause_after": None,
                    "context_before": None,
                    "context_after": None,
                    "suppress_context_before": False,
                    "suppress_context_after": False,
                    "notes_before": "absent",
                    "notes_after": "absent",
                    "private_material_in_exception_graph": False,
                    "automatic_semantic_retry": False,
                },
                {
                    "branch_name": "SystemExit",
                    "propagation_form": "bare_reraise",
                    "same_exception_object": True,
                    "exact_type_preserved": True,
                    "args_preserved": True,
                    "system_exit_code_preserved_or_not_applicable": "preserved",
                    "caught_traceback_tail_identity_preserved": True,
                    "repair_owned_traceback_frame_delta": 0,
                    "cause_before": None,
                    "cause_after": None,
                    "context_before": None,
                    "context_after": None,
                    "suppress_context_before": False,
                    "suppress_context_after": False,
                    "notes_before": "absent",
                    "notes_after": "absent",
                    "private_material_in_exception_graph": False,
                    "automatic_semantic_retry": False,
                },
                {
                    "branch_name": "GeneratorExit",
                    "propagation_form": "bare_reraise",
                    "same_exception_object": True,
                    "exact_type_preserved": True,
                    "args_preserved": True,
                    "system_exit_code_preserved_or_not_applicable": "not_applicable",
                    "caught_traceback_tail_identity_preserved": True,
                    "repair_owned_traceback_frame_delta": 0,
                    "cause_before": None,
                    "cause_after": None,
                    "context_before": None,
                    "context_after": None,
                    "suppress_context_before": False,
                    "suppress_context_after": False,
                    "notes_before": "absent",
                    "notes_after": "absent",
                    "private_material_in_exception_graph": False,
                    "automatic_semantic_retry": False,
                },
            ),
        },
        "quarantine_clearance": (
            "proven retained-connection closure",
            "proven writer-authority-lock release",
            "newly acquired concrete writer session",
            "exact safe command",
        ),
        "caller_authored_clearance": False,
        "forbidden_clearance_evidence": (
            "cleanup token",
            "Boolean assertion",
            "path marker",
            "report",
            "timeout",
        ),
        "forbidden_outward_material": (
            "raw connection",
            "cursor",
            "transaction controller",
            "mutation-slot object",
            "writer-lock object",
            "quarantine object",
            "ordinary commit exception",
            "close implementation details",
            "SQLite path",
            "SQL or parameters",
            "WorkSpec material",
        ),
        "forbidden_outward_destinations": (
            "safe command",
            "receipt",
            "apply result",
            "resolver result",
            "public value",
            "exception payload",
            "log",
            "report",
            "future C2B3-owned outward traceback locals",
        ),
        "process_control_exception_graph_privacy": {
            "forbidden_material": (
                "ordinary commit exception",
                "ordinary close exception",
                "raw SQLite exception",
                "connection",
                "cursor",
                "controller",
                "mutation-slot object",
                "writer-lock object",
                "quarantine object",
                "database path",
                "SQL",
                "parameters",
                "WorkSpec content",
                "private test sentinel",
            ),
            "forbidden_surfaces": (
                "exception args",
                "str or repr",
                "__cause__ graph",
                "__context__ graph",
                "__notes__",
                "formatted traceback",
                "C2B3-owned traceback-frame locals",
                "returned or persisted values",
                "logs or reports",
            ),
            "sole_permitted_outward_exception": "the identical process-control exception object",
        },
    },
    "commit_outcome_recovery": {
        "semantic_name": "DevelopmentProgramInitializationRecoveryResultV1",
        "disposition_owner": "DevelopmentProgramInitializationRecoveryDispositionV1",
        "dispositions": (
            "committed_exact",
            "definitely_not_committed",
            "unresolved",
        ),
        "inputs": (
            "currently valid concrete _SQLiteWriterSession",
            "exact safe initialization command",
        ),
        "accepts_work_spec": False,
        "lifecycle": (
            "prior uncertain connection closure and prior writer-lock release are proven",
            "newly acquired concrete writer session",
            "new operation guard and fresh operation lease",
            "reacquire existing shared mutation slot",
            "same transaction-controller class",
            "fresh readback-only BEGIN IMMEDIATE",
            "managed schema and resource revalidation",
            "writer fencing",
            "same nominal read capability",
            "readback only",
            "rollback and close",
        ),
        "same_session_resolver_while_quarantined": False,
        "mutation_slot_available_before_close_completion": False,
        "close_not_proved_disposition": "unresolved",
        "committed_exact_requires": (
            "exact receipt",
            "exact command digest",
            "exact persisted result",
            "all eight graph entries",
            "all row self-digests",
            "all cross-row relations",
            "both historical head postimages",
            "exact result-projection digest",
            "exact mutation-graph digest",
        ),
        "definitely_not_committed_requires_all_absent": (
            "receipt for mutation_ref",
            "program head for program_ref",
            "program version for program_version_ref",
            "accepted-intent revision for accepted_intent_revision_ref",
            "decision for decision_ref",
            "work-item head for work_item_ref",
            "work-item revision for work_item_revision_ref",
            "membership for command identities",
            "WorkSpec binding for work_spec_ref",
        ),
        "unresolved_evidence": (
            "receipt-only",
            "graph-without-receipt",
            "partial graph",
            "mixed evidence",
            "malformed evidence",
            "contradictory postimage",
            "unlocatable evidence",
            "any state other than exact committed or exact all-absent",
        ),
        "basis_or_global_stop_presence_proves_family_commit": False,
        "automatic_semantic_retry": False,
        "fresh_retry_after_definitely_not_committed": "caller must supply the exact complete WorkSpecV1 again",
    },
    "conflict_precedence": {
        "after_writer_fencing": (
            (1, "exact receipt replay"),
            (2, "mutation_ref_reuse_conflict"),
            (3, "global_stop_version_conflict"),
            (4, "coding_global_stop_active"),
            (5, "semantic_identity_conflict"),
            (6, "database_integrity_failure"),
            (7, "mutation_failed"),
            (8, "commit_outcome_unknown"),
        ),
        "classification_conditions": (
            ("exact receipt replay", "same mutation_ref and same command digest with an exact complete persisted family"),
            ("mutation_ref_reuse_conflict", "same mutation_ref and different command digest"),
            ("global_stop_version_conflict", "coding-global-stop ref or version mismatch"),
            ("coding_global_stop_active", "active exact coding global stop"),
            ("semantic_identity_conflict", "pre-existing program or colliding genesis semantic identity"),
            ("database_integrity_failure", "malformed or contradictory persisted state"),
            ("mutation_failed", "operational SQLite or capability failure"),
            ("commit_outcome_unknown", "commit-attempt exception"),
        ),
        "semantic_identity_conflict_visibility": "private",
        "program_head_conflict": "reserved for later non-genesis CAS-bearing families",
        "failed_fresh_operation_creates_receipt": False,
    },
    "privacy_and_traceback": {
        "ordered_failure_boundary": (
            "sensitive WorkSpec reducer",
            "safe closed outcome",
            "raw reducer returns normally",
            "outer wrapper clears WorkSpec and caught-exception references",
            "fresh bounded outward failure from None",
        ),
        "complete_work_spec_forbidden_destinations": (
            "SQLite",
            "safe command",
            "receipt",
            "result",
            "resolver input",
            "exception payload",
            "log",
            "report",
            "traceback locals owned by future C2B3 source",
        ),
        "forbidden_custody_sources": (
            "chat",
            "model memory",
            "Bridge",
            "reports",
            "connectors",
            "logs",
            "transcripts",
        ),
        "transaction_controller_receives_work_spec": False,
        "contract_freeze_persists_or_executes_work_spec": False,
    },
    "later_author_effect_owner_decisions": {
        "complete_contract_frozen": False,
        "source_implemented": False,
        "initial_basis": ("initialize", "program_genesis"),
        "attempt_number": 1,
        "planned_adapter_kind": "execution_substrate",
        "route_effect": "absent",
        "planned_adapter_value_authority": "safe planned-row value only; no ES compatibility, dispatch permission, route eligibility, reliable submit, or current API binding",
        "adapter_safe_correlation_ref": "preassigned, safe, non-authoritative",
        "work_spec_ingress": "same-call transient only",
        "authority_evaluation": {
            "authorship": "Coordinator-authored pending evidence",
            "evaluation_scope": "effect",
            "evaluation_subject_ref": "exact effect_intent_ref",
            "semantic_attempt_ref": None,
            "effect_intent_ref": "exact effect_intent_ref",
            "authority_ref": "exact externally authored effect_authorization_ref",
            "authority_digest": "exact externally authored effect_authorization_digest",
            "authority_state": "pending",
            "reason_code": "external_verification_pending",
            "expires_at": None,
            "evaluated_at": "one transaction timestamp",
            "authority_evaluation_ref": "preassigned and command-bound",
            "dispatch_eligibility": False,
        },
        "coordinator_does_not_author": (
            "verified",
            "blocked",
            "stale",
            "revoked",
            "expired",
            "executable permission",
            "ES admission",
            "worker authorization",
        ),
        "requirement_provenance": {
            "refs": "exact validation_requirement_ref and review_requirement_ref from WorkSpec",
            "digests": "exact typed safe requirement evidence supplied in the same future private call",
            "raw_digest_only_input": False,
            "digest_inference_from_refs": False,
            "digest_inference_from_text_reports_or_runtime": False,
        },
        "recovery": "explicit fresh-lease readback",
        "graph_membership": "family-created rows only",
        "C2B3C_must_freeze_before_source": (
            "exact typed requirement evidence",
            "exact author command",
            "AttemptFence ingress",
            "all author refs",
            "effect and delivery postimages",
            "nine graph entries",
            "golden vector",
            "replay matrix",
            "recovery matrix",
            "privacy matrix",
        ),
        "direct_local_bootstrap_selected": False,
        "direct_local_posture": "separate later proof/contract; never a silently selected runtime alternative",
        "ES_invocation_or_compatibility_claim": False,
    },
    "future_c2b3b_maximum_path_scope": {
        "tranche": "C2B3B_PRIVATE_ATOMIC_INITIALIZATION",
        "maximum_paths": 24,
        "production": (
            "src/ge_nwp_coordinator/_development_program_initialization_contracts.py",
            "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py",
            "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
            "src/ge_nwp_coordinator/sqlite_writer_session.py",
            "src/ge_nwp_coordinator/sqlite_connection.py",
        ),
        "documentation_status": (
            ".docs/c2b-durable-development-state.md",
            ".docs/c2b3-program-initialization.md",
            ".docs/c2b2-private-readers.md",
            ".docs/architecture.md",
            ".docs/durable-state-model.md",
            ".docs/sqlite-operations-and-recovery.md",
            ".docs/sqlite-threat-model.md",
            "README.md",
            "AGENTS.md",
        ),
        "tests": (
            "tests/test_c2b3_program_initialization_contract.py",
            "tests/test_c2b3_private_atomic_program_initialization.py",
            "tests/test_c2b3_program_initialization_recovery.py",
            "tests/test_c2b3_private_program_initialization_delegation.py",
            "tests/test_c2b2_field_level_contract.py",
            "tests/test_c2b2_private_development_readers.py",
            "tests/test_c2b2_development_reader_contracts.py",
            "tests/test_runtime_non_authority.py",
            "tests/test_architecture_contracts.py",
            "tests/test_c2b0_durable_state_contract.py",
        ),
        "counts": {
            "production": 5,
            "documentation_status": 9,
            "tests": 10,
            "total": 24,
        },
        "production_responsibilities": {
            "src/ge_nwp_coordinator/_development_program_initialization_contracts.py": (
                "private pure command, projection, result, conflict, recovery, graph, and quarantine-admission values",
                "no process-control result or enum",
                "no ordinary-value representation of KeyboardInterrupt, SystemExit, or GeneratorExit",
                "no SQLite",
                "no I/O",
                "no package export",
            ),
            "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py": (
                "sensitive same-call reducer",
                "safe initialization command construction",
                "exact replay",
                "fresh apply",
                "family-specific graph location and verification",
                "explicit recovery resolver",
                "does not catch, translate, wrap, or retry KeyboardInterrupt, SystemExit, or GeneratorExit after transaction cleanup returns them for propagation",
                "no public API",
                "no external I/O",
            ),
            "src/ge_nwp_coordinator/sqlite_transition_transaction.py": (
                "preserve one-commit-attempt ownership",
                "retain uncertain connection and mutation slot after commit exception",
                "attempt close before custody clear",
                "transfer retained connection into session resource when close is unproved",
                "reduce and detach the ordinary commit failure before close-time process-control handling",
                "own the narrow close-interruption catch point",
                "recognize exactly KeyboardInterrupt, SystemExit, and GeneratorExit",
                "catch exactly KeyboardInterrupt, SystemExit, and GeneratorExit from close",
                "retain connection and mutation-slot custody for a named process-control close interruption",
                "retain connection, slot, and writer-lock custody",
                "request session-resource quarantine publication and wait for publication completion",
                "re-raise the identical process-control exception only after publication completion",
                "perform a bare re-raise in the same catch suite",
                "add no traceback frame beyond bare-reraise semantics",
                "add no cause, context, note, or exception-graph material",
                "do not execute unconditional slot release in a named process-control branch",
                "never unconditionally release the slot after commit uncertainty",
                "preserve fresh content-free commit_outcome_unknown",
                "admit no semantic retry",
            ),
            "src/ge_nwp_coordinator/sqlite_writer_session.py": (
                "private program-initialization delegation only",
                "_WriterSessionResource retained-connection custody",
                "commit-uncertain quarantine state",
                "writer-lock and mutation-slot retention",
                "reject new operations while quarantined",
                "acknowledge quarantine publication before the transaction layer re-raises a named process-control exception",
                "publication acknowledgement must not raise or attach an ordinary exception to the process-control exception",
                "publication helpers receive no authority to propagate or replace the caught process-control exception",
                "admit close/finalization only while quarantined",
                "release quarantine only after proved closure and session disposal",
                "no public WriterSession protocol change",
            ),
            "src/ge_nwp_coordinator/sqlite_connection.py": (
                "one private C2B3B-only connection posture or equivalent explicit mechanism permitting proved closure from session-resource finalization",
                "cross-thread close from session-resource finalization is permitted only for proved closure",
                "may surface the exact close-time KeyboardInterrupt, SystemExit, or GeneratorExit",
                "no cross-thread SQL",
                "no public raw connection",
                "no public signature widening",
                "no second connection authority",
                "existing ordinary connection behavior preserved",
            ),
        },
        "twenty_fifth_path": "future implementation stop condition",
        "forbidden": (
            "pyproject.toml",
            "package __init__.py",
            "state_store.py",
            "sqlite_errors.py",
            "models.py public values",
            "sqlite_mutation_transaction_contracts.py",
            "migration SQL or catalog",
            "schemas",
            "C2B4-C2B6 implementation",
            "another repository",
        ),
        "authorized_by_this_freeze": False,
    },
    "nonimplementation": {
        "program_initialization_source": False,
        "private_writer_session_methods": False,
        "sqlite_insert_or_update_execution": False,
        "mutation_receipt_persistence": False,
        "production_reader_integration": False,
        "exact_replay_runtime": False,
        "commit_outcome_recovery_runtime": False,
        "author_effect_source": False,
        "complete_author_effect_contract": False,
        "public_C2B_API": False,
        "StateStore_widening": False,
        "WriterSession_public_surface_widening": False,
        "package_root_export": False,
        "dependency_or_entry_surface": False,
        "WorkSpec_custody_or_retrieval": False,
        "authority_verification": False,
        "worker_or_model_execution": False,
        "direct_local_execution": False,
        "Execution_Substrate_invocation": False,
        "Bridge_integration": False,
        "schema_change": False,
        "migration_0001_change": False,
        "migration_0002_change": False,
        "migration_0003_creation": False,
        "C2B4_C2B5_C2B6_behavior": False,
        "external_IO": False,
    },
}


EXPECTED_INITIALIZATION_GOLDEN_VECTOR = {'vector_id': 'c2b3a-initialization-single-work-v1',
 'vector_version': 1,
 'transaction_timestamp': '2026-08-21T12:34:56Z',
 'safe_command_input_values': {'mutation_ref': 'mutation-c2b3a-1',
                               'program_ref': 'program-c2b3a-1',
                               'program_version_ref': 'program-version-c2b3a-1',
                               'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                               'decision_ref': 'decision-c2b3a-1',
                               'preassigned_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                               'preassigned_candidate_ref': 'candidate-c2b3a-1',
                               'coding_global_stop_ref': 'coding-global-stop-c2b3a-1',
                               'coding_global_stop_version': 0,
                               'reason_code': 'program_genesis',
                               'source_intent_ref': 'source-intent-c2b3a-1',
                               'source_intent_digest': '1111111111111111111111111111111111111111111111111111111111111111',
                               'work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                             'work_spec_ref': 'work-spec-c2b3a-1',
                                                             'program_ref': 'program-c2b3a-1',
                                                             'program_version_ref': 'program-version-c2b3a-1',
                                                             'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                             'work_item_ref': 'work-item-c2b3a-1',
                                                             'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                             'repository_ref': 'repository-c2b3a-1',
                                                             'base_git_object_format': 'sha1',
                                                             'base_git_oid': '2222222222222222222222222222222222222222',
                                                             'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                  'PLANS.md',
                                                                                  'docs_contract_test.go'),
                                                             'validation_requirement_ref': 'validation-c2b3a-1',
                                                             'review_requirement_ref': 'review-c2b3a-1',
                                                             'privacy_classification': 'private_work_spec',
                                                             'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                             'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'}},
 'work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                               'work_spec_ref': 'work-spec-c2b3a-1',
                               'program_ref': 'program-c2b3a-1',
                               'program_version_ref': 'program-version-c2b3a-1',
                               'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                               'work_item_ref': 'work-item-c2b3a-1',
                               'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                               'repository_ref': 'repository-c2b3a-1',
                               'base_git_object_format': 'sha1',
                               'base_git_oid': '2222222222222222222222222222222222222222',
                               'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                    'PLANS.md',
                                                    'docs_contract_test.go'),
                               'validation_requirement_ref': 'validation-c2b3a-1',
                               'review_requirement_ref': 'review-c2b3a-1',
                               'privacy_classification': 'private_work_spec',
                               'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                               'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
 'accepted_intent_safe_projection': {'schema_id': 'governed-execution.nwp-development-accepted-intent-safe-projection.v1',
                                     'source_intent_ref': 'source-intent-c2b3a-1',
                                     'source_intent_digest': '1111111111111111111111111111111111111111111111111111111111111111',
                                     'initial_work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                                           'work_spec_ref': 'work-spec-c2b3a-1',
                                                                           'program_ref': 'program-c2b3a-1',
                                                                           'program_version_ref': 'program-version-c2b3a-1',
                                                                           'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                           'work_item_ref': 'work-item-c2b3a-1',
                                                                           'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                           'repository_ref': 'repository-c2b3a-1',
                                                                           'base_git_object_format': 'sha1',
                                                                           'base_git_oid': '2222222222222222222222222222222222222222',
                                                                           'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                'PLANS.md',
                                                                                                'docs_contract_test.go'),
                                                                           'validation_requirement_ref': 'validation-c2b3a-1',
                                                                           'review_requirement_ref': 'review-c2b3a-1',
                                                                           'privacy_classification': 'private_work_spec',
                                                                           'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                           'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
                                     'safe_projection_digest': '8e76f55695e0f3bda1af480bb00fbd4bcff4c6c0270d80c65ffbe61f67c92ce1'},
 'accepted_intent_canonical_mapping': {'schema_id': 'governed-execution.nwp-development-accepted-intent-safe-projection.v1',
                                       'source_intent_ref': 'source-intent-c2b3a-1',
                                       'source_intent_digest': '1111111111111111111111111111111111111111111111111111111111111111',
                                       'initial_work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                                             'work_spec_ref': 'work-spec-c2b3a-1',
                                                                             'program_ref': 'program-c2b3a-1',
                                                                             'program_version_ref': 'program-version-c2b3a-1',
                                                                             'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                             'work_item_ref': 'work-item-c2b3a-1',
                                                                             'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                             'repository_ref': 'repository-c2b3a-1',
                                                                             'base_git_object_format': 'sha1',
                                                                             'base_git_oid': '2222222222222222222222222222222222222222',
                                                                             'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                  'PLANS.md',
                                                                                                  'docs_contract_test.go'),
                                                                             'validation_requirement_ref': 'validation-c2b3a-1',
                                                                             'review_requirement_ref': 'review-c2b3a-1',
                                                                             'privacy_classification': 'private_work_spec',
                                                                             'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                             'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'}},
 'accepted_intent_canonical_utf8_hex': '7b22696e697469616c5f776f726b5f737065635f736166655f70726f6a656374696f6e223a7b2261636365707465645f696e74656e745f7265766973696f6e5f726566223a2261636365707465642d696e74656e742d63326233612d31222c22617574686f72697a65645f7061746873223a5b222e646f63732f73797374656d5f6f766572766965772f6879627269645f696e746567726174696f6e5f6172636869746563747572655f6164722e6d64222c22504c414e532e6d64222c22646f63735f636f6e74726163745f746573742e676f225d2c22626173655f6769745f6f626a6563745f666f726d6174223a2273686131222c22626173655f6769745f6f6964223a2232323232323232323232323232323232323232323232323232323232323232323232323232323232222c22707269766163795f636c617373696669636174696f6e223a22707269766174655f776f726b5f73706563222c2270726f6772616d5f726566223a2270726f6772616d2d63326233612d31222c2270726f6772616d5f76657273696f6e5f726566223a2270726f6772616d2d76657273696f6e2d63326233612d31222c227265706f7369746f72795f726566223a227265706f7369746f72792d63326233612d31222c227265766965775f726571756972656d656e745f726566223a227265766965772d63326233612d31222c22736166655f70726f6a656374696f6e5f646967657374223a2231613464653930343961353439623536373161653163303662323831656563393939393335393934306138623631386165663766663762343865343363656162222c22736368656d615f6964223a22676f7665726e65642d657865637574696f6e2e6e77702d646576656c6f706d656e742d776f726b2d737065632d736166652d70726f6a656374696f6e2e7631222c2276616c69646174696f6e5f726571756972656d656e745f726566223a2276616c69646174696f6e2d63326233612d31222c22776f726b5f6974656d5f726566223a22776f726b2d6974656d2d63326233612d31222c22776f726b5f6974656d5f7265766973696f6e5f726566223a22776f726b2d6974656d2d7265766973696f6e2d63326233612d31222c22776f726b5f737065635f646967657374223a2232393532633962303332353762343364363939383366616165626565383961356538383466373161356239646465366165623736393532323463643233643963222c22776f726b5f737065635f726566223a22776f726b2d737065632d63326233612d31227d2c22736368656d615f6964223a22676f7665726e65642d657865637574696f6e2e6e77702d646576656c6f706d656e742d61636365707465642d696e74656e742d736166652d70726f6a656374696f6e2e7631222c22736f757263655f696e74656e745f646967657374223a2231313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131222c22736f757263655f696e74656e745f726566223a22736f757263652d696e74656e742d63326233612d31227d',
 'accepted_intent_safe_projection_digest': '8e76f55695e0f3bda1af480bb00fbd4bcff4c6c0270d80c65ffbe61f67c92ce1',
 'safe_command': {'schema_id': 'governed-execution.nwp-initialize-development-program-command.v1',
                  'mutation_ref': 'mutation-c2b3a-1',
                  'program_ref': 'program-c2b3a-1',
                  'program_version_ref': 'program-version-c2b3a-1',
                  'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                  'decision_ref': 'decision-c2b3a-1',
                  'preassigned_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                  'preassigned_candidate_ref': 'candidate-c2b3a-1',
                  'coding_global_stop_ref': 'coding-global-stop-c2b3a-1',
                  'coding_global_stop_version': 0,
                  'reason_code': 'program_genesis',
                  'work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                'work_spec_ref': 'work-spec-c2b3a-1',
                                                'program_ref': 'program-c2b3a-1',
                                                'program_version_ref': 'program-version-c2b3a-1',
                                                'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                'work_item_ref': 'work-item-c2b3a-1',
                                                'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                'repository_ref': 'repository-c2b3a-1',
                                                'base_git_object_format': 'sha1',
                                                'base_git_oid': '2222222222222222222222222222222222222222',
                                                'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                     'PLANS.md',
                                                                     'docs_contract_test.go'),
                                                'validation_requirement_ref': 'validation-c2b3a-1',
                                                'review_requirement_ref': 'review-c2b3a-1',
                                                'privacy_classification': 'private_work_spec',
                                                'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
                  'accepted_intent_safe_projection': {'schema_id': 'governed-execution.nwp-development-accepted-intent-safe-projection.v1',
                                                      'source_intent_ref': 'source-intent-c2b3a-1',
                                                      'source_intent_digest': '1111111111111111111111111111111111111111111111111111111111111111',
                                                      'initial_work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                                                            'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                            'program_ref': 'program-c2b3a-1',
                                                                                            'program_version_ref': 'program-version-c2b3a-1',
                                                                                            'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                            'work_item_ref': 'work-item-c2b3a-1',
                                                                                            'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                            'repository_ref': 'repository-c2b3a-1',
                                                                                            'base_git_object_format': 'sha1',
                                                                                            'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                            'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                                 'PLANS.md',
                                                                                                                 'docs_contract_test.go'),
                                                                                            'validation_requirement_ref': 'validation-c2b3a-1',
                                                                                            'review_requirement_ref': 'review-c2b3a-1',
                                                                                            'privacy_classification': 'private_work_spec',
                                                                                            'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                            'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
                                                      'safe_projection_digest': '8e76f55695e0f3bda1af480bb00fbd4bcff4c6c0270d80c65ffbe61f67c92ce1'},
                  'command_digest': 'f2e9b97cc6bc70b24b75925f534d375edec3ad51382a966e2c95930eb8a5c5c8'},
 'safe_command_canonical_mapping': {'schema_id': 'governed-execution.nwp-initialize-development-program-command.v1',
                                    'mutation_ref': 'mutation-c2b3a-1',
                                    'program_ref': 'program-c2b3a-1',
                                    'program_version_ref': 'program-version-c2b3a-1',
                                    'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                    'decision_ref': 'decision-c2b3a-1',
                                    'preassigned_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                    'preassigned_candidate_ref': 'candidate-c2b3a-1',
                                    'coding_global_stop_ref': 'coding-global-stop-c2b3a-1',
                                    'coding_global_stop_version': 0,
                                    'reason_code': 'program_genesis',
                                    'work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                                  'work_spec_ref': 'work-spec-c2b3a-1',
                                                                  'program_ref': 'program-c2b3a-1',
                                                                  'program_version_ref': 'program-version-c2b3a-1',
                                                                  'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                  'work_item_ref': 'work-item-c2b3a-1',
                                                                  'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                  'repository_ref': 'repository-c2b3a-1',
                                                                  'base_git_object_format': 'sha1',
                                                                  'base_git_oid': '2222222222222222222222222222222222222222',
                                                                  'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                       'PLANS.md',
                                                                                       'docs_contract_test.go'),
                                                                  'validation_requirement_ref': 'validation-c2b3a-1',
                                                                  'review_requirement_ref': 'review-c2b3a-1',
                                                                  'privacy_classification': 'private_work_spec',
                                                                  'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                  'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
                                    'accepted_intent_safe_projection': {'schema_id': 'governed-execution.nwp-development-accepted-intent-safe-projection.v1',
                                                                        'source_intent_ref': 'source-intent-c2b3a-1',
                                                                        'source_intent_digest': '1111111111111111111111111111111111111111111111111111111111111111',
                                                                        'initial_work_spec_safe_projection': {'schema_id': 'governed-execution.nwp-development-work-spec-safe-projection.v1',
                                                                                                              'work_spec_ref': 'work-spec-c2b3a-1',
                                                                                                              'program_ref': 'program-c2b3a-1',
                                                                                                              'program_version_ref': 'program-version-c2b3a-1',
                                                                                                              'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                                                                              'work_item_ref': 'work-item-c2b3a-1',
                                                                                                              'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                                                                              'repository_ref': 'repository-c2b3a-1',
                                                                                                              'base_git_object_format': 'sha1',
                                                                                                              'base_git_oid': '2222222222222222222222222222222222222222',
                                                                                                              'authorized_paths': ('.docs/system_overview/hybrid_integration_architecture_adr.md',
                                                                                                                                   'PLANS.md',
                                                                                                                                   'docs_contract_test.go'),
                                                                                                              'validation_requirement_ref': 'validation-c2b3a-1',
                                                                                                              'review_requirement_ref': 'review-c2b3a-1',
                                                                                                              'privacy_classification': 'private_work_spec',
                                                                                                              'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                                                                                              'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab'},
                                                                        'safe_projection_digest': '8e76f55695e0f3bda1af480bb00fbd4bcff4c6c0270d80c65ffbe61f67c92ce1'}},
 'safe_command_canonical_utf8_hex': '7b2261636365707465645f696e74656e745f7265766973696f6e5f726566223a2261636365707465642d696e74656e742d63326233612d31222c2261636365707465645f696e74656e745f736166655f70726f6a656374696f6e223a7b22696e697469616c5f776f726b5f737065635f736166655f70726f6a656374696f6e223a7b2261636365707465645f696e74656e745f7265766973696f6e5f726566223a2261636365707465642d696e74656e742d63326233612d31222c22617574686f72697a65645f7061746873223a5b222e646f63732f73797374656d5f6f766572766965772f6879627269645f696e746567726174696f6e5f6172636869746563747572655f6164722e6d64222c22504c414e532e6d64222c22646f63735f636f6e74726163745f746573742e676f225d2c22626173655f6769745f6f626a6563745f666f726d6174223a2273686131222c22626173655f6769745f6f6964223a2232323232323232323232323232323232323232323232323232323232323232323232323232323232222c22707269766163795f636c617373696669636174696f6e223a22707269766174655f776f726b5f73706563222c2270726f6772616d5f726566223a2270726f6772616d2d63326233612d31222c2270726f6772616d5f76657273696f6e5f726566223a2270726f6772616d2d76657273696f6e2d63326233612d31222c227265706f7369746f72795f726566223a227265706f7369746f72792d63326233612d31222c227265766965775f726571756972656d656e745f726566223a227265766965772d63326233612d31222c22736166655f70726f6a656374696f6e5f646967657374223a2231613464653930343961353439623536373161653163303662323831656563393939393335393934306138623631386165663766663762343865343363656162222c22736368656d615f6964223a22676f7665726e65642d657865637574696f6e2e6e77702d646576656c6f706d656e742d776f726b2d737065632d736166652d70726f6a656374696f6e2e7631222c2276616c69646174696f6e5f726571756972656d656e745f726566223a2276616c69646174696f6e2d63326233612d31222c22776f726b5f6974656d5f726566223a22776f726b2d6974656d2d63326233612d31222c22776f726b5f6974656d5f7265766973696f6e5f726566223a22776f726b2d6974656d2d7265766973696f6e2d63326233612d31222c22776f726b5f737065635f646967657374223a2232393532633962303332353762343364363939383366616165626565383961356538383466373161356239646465366165623736393532323463643233643963222c22776f726b5f737065635f726566223a22776f726b2d737065632d63326233612d31227d2c22736166655f70726f6a656374696f6e5f646967657374223a2238653736663535363935653066336264613161663438306262303066626434626366663463366330323730643830633635666662653631663637633932636531222c22736368656d615f6964223a22676f7665726e65642d657865637574696f6e2e6e77702d646576656c6f706d656e742d61636365707465642d696e74656e742d736166652d70726f6a656374696f6e2e7631222c22736f757263655f696e74656e745f646967657374223a2231313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131313131222c22736f757263655f696e74656e745f726566223a22736f757263652d696e74656e742d63326233612d31227d2c22636f64696e675f676c6f62616c5f73746f705f726566223a22636f64696e672d676c6f62616c2d73746f702d63326233612d31222c22636f64696e675f676c6f62616c5f73746f705f76657273696f6e223a302c226465636973696f6e5f726566223a226465636973696f6e2d63326233612d31222c226d75746174696f6e5f726566223a226d75746174696f6e2d63326233612d31222c2270726561737369676e65645f63616e6469646174655f726566223a2263616e6469646174652d63326233612d31222c2270726561737369676e65645f73656d616e7469635f617474656d70745f726566223a2273656d616e7469632d617474656d70742d63326233612d31222c2270726f6772616d5f726566223a2270726f6772616d2d63326233612d31222c2270726f6772616d5f76657273696f6e5f726566223a2270726f6772616d2d76657273696f6e2d63326233612d31222c22726561736f6e5f636f6465223a2270726f6772616d5f67656e65736973222c22736368656d615f6964223a22676f7665726e65642d657865637574696f6e2e6e77702d696e697469616c697a652d646576656c6f706d656e742d70726f6772616d2d636f6d6d616e642e7631222c22776f726b5f737065635f736166655f70726f6a656374696f6e223a7b2261636365707465645f696e74656e745f7265766973696f6e5f726566223a2261636365707465642d696e74656e742d63326233612d31222c22617574686f72697a65645f7061746873223a5b222e646f63732f73797374656d5f6f766572766965772f6879627269645f696e746567726174696f6e5f6172636869746563747572655f6164722e6d64222c22504c414e532e6d64222c22646f63735f636f6e74726163745f746573742e676f225d2c22626173655f6769745f6f626a6563745f666f726d6174223a2273686131222c22626173655f6769745f6f6964223a2232323232323232323232323232323232323232323232323232323232323232323232323232323232222c22707269766163795f636c617373696669636174696f6e223a22707269766174655f776f726b5f73706563222c2270726f6772616d5f726566223a2270726f6772616d2d63326233612d31222c2270726f6772616d5f76657273696f6e5f726566223a2270726f6772616d2d76657273696f6e2d63326233612d31222c227265706f7369746f72795f726566223a227265706f7369746f72792d63326233612d31222c227265766965775f726571756972656d656e745f726566223a227265766965772d63326233612d31222c22736166655f70726f6a656374696f6e5f646967657374223a2231613464653930343961353439623536373161653163303662323831656563393939393335393934306138623631386165663766663762343865343363656162222c22736368656d615f6964223a22676f7665726e65642d657865637574696f6e2e6e77702d646576656c6f706d656e742d776f726b2d737065632d736166652d70726f6a656374696f6e2e7631222c2276616c69646174696f6e5f726571756972656d656e745f726566223a2276616c69646174696f6e2d63326233612d31222c22776f726b5f6974656d5f726566223a22776f726b2d6974656d2d63326233612d31222c22776f726b5f6974656d5f7265766973696f6e5f726566223a22776f726b2d6974656d2d7265766973696f6e2d63326233612d31222c22776f726b5f737065635f646967657374223a2232393532633962303332353762343364363939383366616165626565383961356538383466373161356239646465366165623736393532323463643233643963222c22776f726b5f737065635f726566223a22776f726b2d737065632d63326233612d31227d7d',
 'command_digest': 'f2e9b97cc6bc70b24b75925f534d375edec3ad51382a966e2c95930eb8a5c5c8',
 'persisted_rows': {'program_head': {'schema_id': 'governed-execution.nwp-development-program-head.v1',
                                     'program_ref': 'program-c2b3a-1',
                                     'current_program_version_ref': 'program-version-c2b3a-1',
                                     'current_program_version_number': 1,
                                     'head_revision': 0,
                                     'program_state': 'active',
                                     'updated_at': '2026-08-21T12:34:56Z',
                                     'head_digest': '79b933902d113c5dda9c054b56cb105a8f9ed25513eaf91656c72efe53ee7058'},
                    'accepted_intent_revision': {'schema_id': 'governed-execution.nwp-development-accepted-intent-revision.v1',
                                                 'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                                 'program_ref': 'program-c2b3a-1',
                                                 'accepted_intent_revision_number': 1,
                                                 'prior_accepted_intent_revision_ref': None,
                                                 'source_intent_ref': 'source-intent-c2b3a-1',
                                                 'source_intent_digest': '1111111111111111111111111111111111111111111111111111111111111111',
                                                 'safe_projection_digest': '8e76f55695e0f3bda1af480bb00fbd4bcff4c6c0270d80c65ffbe61f67c92ce1',
                                                 'created_at': '2026-08-21T12:34:56Z',
                                                 'accepted_intent_revision_digest': '4f903ee159a9ee9ac8bb1ce0803ed4d899e73a16da6a8dd84621ccd30bfd60ab'},
                    'work_item_head': {'schema_id': 'governed-execution.nwp-development-work-item-head.v1',
                                       'work_item_ref': 'work-item-c2b3a-1',
                                       'program_ref': 'program-c2b3a-1',
                                       'current_work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                       'current_work_item_revision_number': 1,
                                       'head_revision': 0,
                                       'work_state': 'planned',
                                       'updated_at': '2026-08-21T12:34:56Z',
                                       'head_digest': '67acca455028e770d816c509ac1c6936cf69a7ec582da412941df2b7f0986405'},
                    'work_item_revision': {'schema_id': 'governed-execution.nwp-development-work-item-revision.v1',
                                           'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                           'program_ref': 'program-c2b3a-1',
                                           'work_item_ref': 'work-item-c2b3a-1',
                                           'work_item_revision_number': 1,
                                           'work_item_revision_kind': 'initial',
                                           'prior_work_item_revision_ref': None,
                                           'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                           'created_at': '2026-08-21T12:34:56Z',
                                           'work_item_revision_digest': '23d7354b797a03faf0bdaee2bce03752258443cc9e232a26c47a0e8a7069a215'},
                    'initialize_decision': {'schema_id': 'governed-execution.nwp-development-decision.v1',
                                            'mutation_ref': 'mutation-c2b3a-1',
                                            'decision_ref': 'decision-c2b3a-1',
                                            'program_ref': 'program-c2b3a-1',
                                            'decision_kind': 'initialize',
                                            'decision_variant': 'program_genesis',
                                            'basis_decision_ref': None,
                                            'basis_program_version_ref': None,
                                            'basis_program_version_number': None,
                                            'expected_program_head_revision': 0,
                                            'resulting_program_version_ref': 'program-version-c2b3a-1',
                                            'resulting_program_version_number': 1,
                                            'selected_semantic_attempt_ref': None,
                                            'selected_candidate_ref': None,
                                            'selected_attempt_fence_ref': None,
                                            'selected_attempt_fence_digest': None,
                                            'target_effect_intent_ref': None,
                                            'target_effect_class': None,
                                            'target_effect_fence_ref': None,
                                            'target_effect_fence_digest': None,
                                            'expected_target_effect_head_revision': None,
                                            'target_delivery_attempt_ref': None,
                                            'originating_command_ref': None,
                                            'originating_command_digest': None,
                                            'target_capsule_manifest_ref': None,
                                            'target_portable_capsule_digest': None,
                                            'coding_global_stop_ref': 'coding-global-stop-c2b3a-1',
                                            'coding_global_stop_version': 0,
                                            'source_directive_ref': None,
                                            'source_directive_digest': None,
                                            'source_evidence_ref': None,
                                            'source_evidence_digest': None,
                                            'preassigned_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                            'preassigned_candidate_ref': 'candidate-c2b3a-1',
                                            'preassigned_effect_intent_ref': None,
                                            'preassigned_effect_fence_ref': None,
                                            'preassigned_delivery_attempt_ref': None,
                                            'resulting_accepted_intent_revision_ref': None,
                                            'resulting_work_item_ref': None,
                                            'resulting_work_item_revision_ref': None,
                                            'reason_code': 'program_genesis',
                                            'decided_at': '2026-08-21T12:34:56Z',
                                            'decision_digest': 'e743c359aea93d7931250552b62bc741d84c490f9ebb68e071c8616cc5fb4b96'},
                    'program_version': {'schema_id': 'governed-execution.nwp-development-program-version.v1',
                                        'program_version_ref': 'program-version-c2b3a-1',
                                        'program_ref': 'program-c2b3a-1',
                                        'program_version_number': 1,
                                        'program_version_kind': 'initial',
                                        'creating_decision_ref': 'decision-c2b3a-1',
                                        'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                        'created_at': '2026-08-21T12:34:56Z',
                                        'program_version_digest': 'f06037aaa718343f8676ec00d5b26b2be6fd7ab58683292f6fbe4b461b8374b9'},
                    'program_version_work_item': {'schema_id': 'governed-execution.nwp-development-program-version-work-item.v1',
                                                  'program_ref': 'program-c2b3a-1',
                                                  'program_version_ref': 'program-version-c2b3a-1',
                                                  'work_item_ref': 'work-item-c2b3a-1',
                                                  'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                                  'membership_ordinal': 0,
                                                  'created_at': '2026-08-21T12:34:56Z',
                                                  'membership_digest': 'e2dc7953947fe1bf8ea643b9398c1b18278a18dd27d5fb7e3ca7663e4d8b3fb9'},
                    'work_spec_binding': {'schema_id': 'governed-execution.nwp-development-work-spec-binding.v1',
                                          'work_spec_ref': 'work-spec-c2b3a-1',
                                          'program_ref': 'program-c2b3a-1',
                                          'program_version_ref': 'program-version-c2b3a-1',
                                          'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                          'work_item_ref': 'work-item-c2b3a-1',
                                          'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                          'repository_ref': 'repository-c2b3a-1',
                                          'base_git_object_format': 'sha1',
                                          'base_git_oid': '2222222222222222222222222222222222222222',
                                          'authorized_paths_json': '[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"]',
                                          'validation_requirement_ref': 'validation-c2b3a-1',
                                          'review_requirement_ref': 'review-c2b3a-1',
                                          'privacy_classification': 'private_work_spec',
                                          'work_spec_digest': '2952c9b03257b43d69983faaebee89a5e884f71a5b9dde6aeb7695224cd23d9c',
                                          'safe_projection_digest': '1a4de9049a549b5671ae1c06b281eec9999359940a8b618aef7ff7b48e43ceab',
                                          'recorded_at': '2026-08-21T12:34:56Z',
                                          'work_spec_binding_digest': 'ada4d473f82b01649e66c82a13e7732a257247d032cd9d7ca8d5be03a7cb3afa'},
                    'mutation_receipt': {'schema_id': 'governed-execution.nwp-development-mutation-receipt.v1',
                                         'mutation_ref': 'mutation-c2b3a-1',
                                         'mutation_family': 'initialize_development_program',
                                         'command_schema_id': 'governed-execution.nwp-initialize-development-program-command.v1',
                                         'command_digest': 'f2e9b97cc6bc70b24b75925f534d375edec3ad51382a966e2c95930eb8a5c5c8',
                                         'program_ref': 'program-c2b3a-1',
                                         'decision_ref': 'decision-c2b3a-1',
                                         'result_program_version_ref': 'program-version-c2b3a-1',
                                         'result_semantic_attempt_ref': None,
                                         'result_effect_intent_ref': None,
                                         'result_effect_fence_ref': None,
                                         'result_delivery_attempt_ref': None,
                                         'result_observation_ref': None,
                                         'result_decision_ref': 'decision-c2b3a-1',
                                         'result_class': 'development_program_initialized',
                                         'result_projection_digest': '7844ff36f20e1c6fe7fc3d687ac96d5162fc3a1f723c87512ace84d241451d76',
                                         'mutation_graph_digest': '150699722ad8e573a56b4673fbd1e41434d894757f48bb83e4826f474b1511ee',
                                         'outcome': 'committed',
                                         'committed_at': '2026-08-21T12:34:56Z'}},
 'historical_postimages': {'program_head': {'schema_id': 'governed-execution.nwp-development-program-head.v1',
                                            'program_ref': 'program-c2b3a-1',
                                            'current_program_version_ref': 'program-version-c2b3a-1',
                                            'current_program_version_number': 1,
                                            'head_revision': 0,
                                            'program_state': 'active',
                                            'updated_at': '2026-08-21T12:34:56Z',
                                            'head_digest': '79b933902d113c5dda9c054b56cb105a8f9ed25513eaf91656c72efe53ee7058'},
                           'work_item_head': {'schema_id': 'governed-execution.nwp-development-work-item-head.v1',
                                              'work_item_ref': 'work-item-c2b3a-1',
                                              'program_ref': 'program-c2b3a-1',
                                              'current_work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                              'current_work_item_revision_number': 1,
                                              'head_revision': 0,
                                              'work_state': 'planned',
                                              'updated_at': '2026-08-21T12:34:56Z',
                                              'head_digest': '67acca455028e770d816c509ac1c6936cf69a7ec582da412941df2b7f0986405'}},
 'graph_entries': ({'rank': 0,
                    'role': 'program_head_postimage',
                    'ordinal': 0,
                    'record_ref': 'program-c2b3a-1',
                    'record_digest': '79b933902d113c5dda9c054b56cb105a8f9ed25513eaf91656c72efe53ee7058'},
                   {'rank': 1,
                    'role': 'accepted_intent_revision',
                    'ordinal': 0,
                    'record_ref': 'accepted-intent-c2b3a-1',
                    'record_digest': '4f903ee159a9ee9ac8bb1ce0803ed4d899e73a16da6a8dd84621ccd30bfd60ab'},
                   {'rank': 2,
                    'role': 'initialize_decision',
                    'ordinal': 0,
                    'record_ref': 'decision-c2b3a-1',
                    'record_digest': 'e743c359aea93d7931250552b62bc741d84c490f9ebb68e071c8616cc5fb4b96'},
                   {'rank': 3,
                    'role': 'program_version',
                    'ordinal': 0,
                    'record_ref': 'program-version-c2b3a-1',
                    'record_digest': 'f06037aaa718343f8676ec00d5b26b2be6fd7ab58683292f6fbe4b461b8374b9'},
                   {'rank': 4,
                    'role': 'work_item_head_postimage',
                    'ordinal': 0,
                    'record_ref': 'work-item-c2b3a-1',
                    'record_digest': '67acca455028e770d816c509ac1c6936cf69a7ec582da412941df2b7f0986405'},
                   {'rank': 5,
                    'role': 'work_item_revision',
                    'ordinal': 0,
                    'record_ref': 'work-item-revision-c2b3a-1',
                    'record_digest': '23d7354b797a03faf0bdaee2bce03752258443cc9e232a26c47a0e8a7069a215'},
                   {'rank': 6,
                    'role': 'program_version_work_item',
                    'ordinal': 0,
                    'record_ref': 'work-item-c2b3a-1',
                    'record_digest': 'e2dc7953947fe1bf8ea643b9398c1b18278a18dd27d5fb7e3ca7663e4d8b3fb9'},
                   {'rank': 7,
                    'role': 'work_spec_binding',
                    'ordinal': 0,
                    'record_ref': 'work-spec-c2b3a-1',
                    'record_digest': 'ada4d473f82b01649e66c82a13e7732a257247d032cd9d7ca8d5be03a7cb3afa'}),
 'result_projection': {'schema_id': 'governed-execution.nwp-initialize-development-program-result.v1',
                       'program_ref': 'program-c2b3a-1',
                       'decision_ref': 'decision-c2b3a-1',
                       'result_program_version_ref': 'program-version-c2b3a-1',
                       'result_decision_ref': 'decision-c2b3a-1'},
 'result_projection_digest': '7844ff36f20e1c6fe7fc3d687ac96d5162fc3a1f723c87512ace84d241451d76',
 'mutation_graph_digest': '150699722ad8e573a56b4673fbd1e41434d894757f48bb83e4826f474b1511ee',
 'mutation_receipt': {'schema_id': 'governed-execution.nwp-development-mutation-receipt.v1',
                      'mutation_ref': 'mutation-c2b3a-1',
                      'mutation_family': 'initialize_development_program',
                      'command_schema_id': 'governed-execution.nwp-initialize-development-program-command.v1',
                      'command_digest': 'f2e9b97cc6bc70b24b75925f534d375edec3ad51382a966e2c95930eb8a5c5c8',
                      'program_ref': 'program-c2b3a-1',
                      'decision_ref': 'decision-c2b3a-1',
                      'result_program_version_ref': 'program-version-c2b3a-1',
                      'result_semantic_attempt_ref': None,
                      'result_effect_intent_ref': None,
                      'result_effect_fence_ref': None,
                      'result_delivery_attempt_ref': None,
                      'result_observation_ref': None,
                      'result_decision_ref': 'decision-c2b3a-1',
                      'result_class': 'development_program_initialized',
                      'result_projection_digest': '7844ff36f20e1c6fe7fc3d687ac96d5162fc3a1f723c87512ace84d241451d76',
                      'mutation_graph_digest': '150699722ad8e573a56b4673fbd1e41434d894757f48bb83e4826f474b1511ee',
                      'outcome': 'committed',
                      'committed_at': '2026-08-21T12:34:56Z'},
 'private_committed_result': {'disposition': 'committed',
                              'mutation_ref': 'mutation-c2b3a-1',
                              'command_digest': 'f2e9b97cc6bc70b24b75925f534d375edec3ad51382a966e2c95930eb8a5c5c8',
                              'program_ref': 'program-c2b3a-1',
                              'program_version_ref': 'program-version-c2b3a-1',
                              'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                              'decision_ref': 'decision-c2b3a-1',
                              'work_item_ref': 'work-item-c2b3a-1',
                              'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                              'work_spec_ref': 'work-spec-c2b3a-1',
                              'preassigned_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                              'preassigned_candidate_ref': 'candidate-c2b3a-1',
                              'transaction_timestamp': '2026-08-21T12:34:56Z'},
 'private_exact_replay_result': {'disposition': 'exact_replay',
                                 'mutation_ref': 'mutation-c2b3a-1',
                                 'command_digest': 'f2e9b97cc6bc70b24b75925f534d375edec3ad51382a966e2c95930eb8a5c5c8',
                                 'program_ref': 'program-c2b3a-1',
                                 'program_version_ref': 'program-version-c2b3a-1',
                                 'accepted_intent_revision_ref': 'accepted-intent-c2b3a-1',
                                 'decision_ref': 'decision-c2b3a-1',
                                 'work_item_ref': 'work-item-c2b3a-1',
                                 'work_item_revision_ref': 'work-item-revision-c2b3a-1',
                                 'work_spec_ref': 'work-spec-c2b3a-1',
                                 'preassigned_semantic_attempt_ref': 'semantic-attempt-c2b3a-1',
                                 'preassigned_candidate_ref': 'candidate-c2b3a-1',
                                 'transaction_timestamp': '2026-08-21T12:34:56Z'}}


class _ContractViolation(Exception):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise _ContractViolation(code)


def _read_allowed_text(path: Path) -> str:
    try:
        relative = path.relative_to(ROOT)
    except ValueError:
        raise _ContractViolation("C2B3A_ORACLE_FORBIDDEN_INPUT") from None
    requested = relative.as_posix()
    _require(
        requested in ALLOWED_ORACLE_RELATIVE_PATHS,
        "C2B3A_ORACLE_FORBIDDEN_INPUT",
    )
    expected = ROOT / requested
    _require(path == expected, "C2B3A_ORACLE_FORBIDDEN_INPUT")
    _require(not expected.is_symlink(), "C2B3A_ORACLE_FORBIDDEN_INPUT")
    try:
        resolved = expected.resolve(strict=True)
    except (OSError, RuntimeError):
        raise _ContractViolation("C2B3A_ORACLE_FORBIDDEN_INPUT") from None
    _require(resolved == expected, "C2B3A_ORACLE_FORBIDDEN_INPUT")
    return resolved.read_text(encoding="utf-8")


def _owner_contract(text: str | None = None) -> dict[str, object]:
    source = _read_allowed_text(OWNER_PATH) if text is None else text
    _require(type(source) is str, "C2B3A_OWNER_LITERAL_INVALID")
    _require(source.count(BEGIN_MARKER) == 1, "C2B3A_OWNER_MARKER_INVALID")
    _require(source.count(END_MARKER) == 1, "C2B3A_OWNER_MARKER_INVALID")
    before, remainder = source.split(BEGIN_MARKER, 1)
    payload, after = remainder.split(END_MARKER, 1)
    _require(before.endswith("\n"), "C2B3A_OWNER_MARKER_INVALID")
    _require(after.startswith("\n"), "C2B3A_OWNER_MARKER_INVALID")
    stripped_payload = payload.strip()
    lines = stripped_payload.splitlines()
    _require(len(lines) >= 3, "C2B3A_OWNER_LITERAL_INVALID")
    _require(lines[0] == "```python", "C2B3A_OWNER_FENCE_INVALID")
    _require(lines[-1] == "```", "C2B3A_OWNER_FENCE_INVALID")
    try:
        newline = "\n"
        value = ast.literal_eval(newline.join(lines[1:-1]))
    except (SyntaxError, ValueError):
        raise _ContractViolation("C2B3A_OWNER_LITERAL_INVALID") from None
    _require(type(value) is dict, "C2B3A_OWNER_LITERAL_INVALID")
    return value


def _owner_golden_vector(text: str | None = None) -> dict[str, object]:
    source = _read_allowed_text(OWNER_PATH) if text is None else text
    _require(type(source) is str, "C2B3A_GOLDEN_VECTOR_LITERAL_INVALID")
    _require(
        source.count(VECTOR_BEGIN_MARKER) == 1,
        "C2B3A_GOLDEN_VECTOR_MARKER_INVALID",
    )
    _require(
        source.count(VECTOR_END_MARKER) == 1,
        "C2B3A_GOLDEN_VECTOR_MARKER_INVALID",
    )
    before, remainder = source.split(VECTOR_BEGIN_MARKER, 1)
    payload, after = remainder.split(VECTOR_END_MARKER, 1)
    _require(before.endswith("\n"), "C2B3A_GOLDEN_VECTOR_MARKER_INVALID")
    _require(after.startswith("\n"), "C2B3A_GOLDEN_VECTOR_MARKER_INVALID")
    stripped_payload = payload.strip()
    lines = stripped_payload.splitlines()
    _require(len(lines) >= 3, "C2B3A_GOLDEN_VECTOR_LITERAL_INVALID")
    _require(lines[0] == "```python", "C2B3A_GOLDEN_VECTOR_FENCE_INVALID")
    _require(lines[-1] == "```", "C2B3A_GOLDEN_VECTOR_FENCE_INVALID")
    try:
        newline = "\n"
        value = ast.literal_eval(newline.join(lines[1:-1]))
    except (SyntaxError, ValueError):
        raise _ContractViolation("C2B3A_GOLDEN_VECTOR_LITERAL_INVALID") from None
    _require(type(value) is dict, "C2B3A_GOLDEN_VECTOR_LITERAL_INVALID")
    return value


def _validate_golden_vector(candidate: object) -> None:
    _require(type(candidate) is dict, "C2B3A_GOLDEN_VECTOR_INVALID")
    _require(
        candidate == EXPECTED_INITIALIZATION_GOLDEN_VECTOR,
        "C2B3A_GOLDEN_VECTOR_INVALID",
    )


def _planning_markdown_prefix_stripped(line: str) -> str:
    remaining = line
    while True:
        candidate = remaining.lstrip(" \t")
        if candidate.startswith(">"):
            remaining = candidate[1:]
            continue
        if (
            len(candidate) >= 2
            and candidate[0] in "-+*"
            and candidate[1] in " \t"
        ):
            remaining = candidate[2:]
            continue
        digit_end = 0
        while digit_end < len(candidate):
            digit = candidate[digit_end]
            if not digit.isdigit():
                break
            digit_end += 1
        if (
            digit_end > 0
            and digit_end + 1 < len(candidate)
            and candidate[digit_end] in ".)"
            and candidate[digit_end + 1] in " \t"
        ):
            remaining = candidate[digit_end + 2 :]
            continue
        return candidate


def _planning_fence_candidate(line: str) -> tuple[str, int, str] | None:
    candidate = _planning_markdown_prefix_stripped(line)
    if not candidate or candidate[0] not in "`~":
        return None
    marker = candidate[0]
    run_length = 0
    while run_length < len(candidate) and candidate[run_length] == marker:
        run_length += 1
    if run_length < 3:
        return None
    remainder = candidate[run_length:]
    if marker == "`" and "`" in remainder:
        return None
    return marker, run_length, remainder


def _planning_normalized_line(line: str) -> str:
    stripped = _planning_markdown_prefix_stripped(line)
    lowered = stripped.lower()
    ascii_spaced = lowered.replace("\t", " ")
    pieces = ascii_spaced.split(" ")
    separator = " "
    normalized = separator.join(piece for piece in pieces if piece)
    if normalized.endswith("."):
        normalized = normalized[:-1]
    return normalized


def _planning_nonfenced_normalized_lines(text: str) -> tuple[str, ...]:
    lines = text.splitlines()
    _require(
        bool(lines) and lines[0] == "# C2B3 Program Initialization",
        "C2B3A_CURRENT_SOURCE_CONTRADICTION",
    )
    prose: list[str] = []
    fence: tuple[str, int] | None = None
    for line in lines:
        candidate = _planning_fence_candidate(line)
        if fence is not None:
            if (
                candidate is not None
                and candidate[0] == fence[0]
                and candidate[1] >= fence[1]
                and all(character in " \t" for character in candidate[2])
            ):
                fence = None
            continue
        if candidate is not None:
            fence = (candidate[0], candidate[1])
            continue
        normalized = _planning_normalized_line(line)
        if normalized:
            prose.append(normalized)
    _require(fence is None, "C2B3A_CURRENT_SOURCE_CONTRADICTION")
    return tuple(prose)


def _validate_planning_status(text: object) -> None:
    _require(type(text) is str, "C2B3A_CURRENT_SOURCE_CONTRADICTION")
    assert isinstance(text, str)
    prose = _planning_nonfenced_normalized_lines(text)
    for claim in PLANNING_AUTHORITY_CLAIMS:
        _require(
            claim not in prose,
            "C2B3A_PLANNING_AUTHORITY_CONTRADICTION",
        )
    for claim in PLANNING_CURRENT_SOURCE_CLAIMS:
        _require(
            claim not in prose,
            "C2B3A_CURRENT_SOURCE_CONTRADICTION",
        )


def _validate_contract(candidate: object) -> None:
    _require(type(candidate) is dict, "C2B3A_TOP_LEVEL_INVALID")
    assert isinstance(candidate, dict)
    _require(
        tuple(candidate) == tuple(EXPECTED_INITIALIZATION_CONTRACT),
        "C2B3A_TOP_LEVEL_INVALID",
    )
    _require(
        candidate["contract_identity"]
        == EXPECTED_INITIALIZATION_CONTRACT["contract_identity"],
        "C2B3A_CONTRACT_IDENTITY_INVALID",
    )
    _require(
        candidate["tranche_boundary"]
        == EXPECTED_INITIALIZATION_CONTRACT["tranche_boundary"],
        "C2B3A_TRANCHE_BOUNDARY_INVALID",
    )
    _require(
        candidate["five_path_scope"]
        == EXPECTED_INITIALIZATION_CONTRACT["five_path_scope"],
        "C2B3A_WRITE_SCOPE_INVALID",
    )
    _require(
        candidate["owner_decisions"]
        == EXPECTED_INITIALIZATION_CONTRACT["owner_decisions"],
        "C2B3A_OWNER_DECISIONS_INVALID",
    )
    _require(
        candidate["initialization_golden_vector"]
        == EXPECTED_INITIALIZATION_CONTRACT["initialization_golden_vector"],
        "C2B3A_GOLDEN_VECTOR_INVALID",
    )
    _require(
        candidate["semantic_ref_ownership"]
        == EXPECTED_INITIALIZATION_CONTRACT["semantic_ref_ownership"],
        "C2B3A_SEMANTIC_REFS_INVALID",
    )
    _require(
        candidate["existing_work_spec_safe_projection"]
        == EXPECTED_INITIALIZATION_CONTRACT[
            "existing_work_spec_safe_projection"
        ],
        "C2B3A_WORK_SPEC_PROJECTION_INVALID",
    )
    _require(
        candidate["accepted_intent_safe_projection"]
        == EXPECTED_INITIALIZATION_CONTRACT[
            "accepted_intent_safe_projection"
        ],
        "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID",
    )
    _require(
        candidate["sensitive_ingress"]
        == EXPECTED_INITIALIZATION_CONTRACT["sensitive_ingress"],
        "C2B3A_SENSITIVE_INGRESS_INVALID",
    )
    _require(
        candidate["safe_command"]
        == EXPECTED_INITIALIZATION_CONTRACT["safe_command"],
        "C2B3A_SAFE_COMMAND_INVALID",
    )
    _require(
        candidate["genesis_cardinality"]
        == EXPECTED_INITIALIZATION_CONTRACT["genesis_cardinality"],
        "C2B3A_GENESIS_CARDINALITY_INVALID",
    )
    _require(
        candidate["row_and_head_ledger"]
        == EXPECTED_INITIALIZATION_CONTRACT["row_and_head_ledger"],
        "C2B3A_ROW_LEDGER_INVALID",
    )
    _require(
        candidate["write_order"]
        == EXPECTED_INITIALIZATION_CONTRACT["write_order"],
        "C2B3A_WRITE_ORDER_INVALID",
    )
    _require(
        candidate["initialize_graph"]
        == EXPECTED_INITIALIZATION_CONTRACT["initialize_graph"],
        "C2B3A_GRAPH_INVALID",
    )
    _require(
        candidate["complete_graph_locator"]
        == EXPECTED_INITIALIZATION_CONTRACT["complete_graph_locator"],
        "C2B3A_LOCATOR_INVALID",
    )
    _require(
        candidate["persisted_result_projection"]
        == EXPECTED_INITIALIZATION_CONTRACT["persisted_result_projection"],
        "C2B3A_RESULT_PROJECTION_INVALID",
    )
    _require(
        candidate["private_apply_result"]
        == EXPECTED_INITIALIZATION_CONTRACT["private_apply_result"],
        "C2B3A_PRIVATE_RESULT_INVALID",
    )
    _require(
        candidate["private_outcome_ownership"]
        == EXPECTED_INITIALIZATION_CONTRACT["private_outcome_ownership"],
        "C2B3A_OUTCOME_OWNERSHIP_INVALID",
    )
    _require(
        candidate["mutation_receipt"]
        == EXPECTED_INITIALIZATION_CONTRACT["mutation_receipt"],
        "C2B3A_RECEIPT_INVALID",
    )
    _require(
        candidate["exact_replay"]
        == EXPECTED_INITIALIZATION_CONTRACT["exact_replay"],
        "C2B3A_REPLAY_INVALID",
    )
    _require(
        candidate["commit_uncertainty_cleanup_gate"]
        == EXPECTED_INITIALIZATION_CONTRACT["commit_uncertainty_cleanup_gate"],
        "C2B3A_RECOVERY_ADMISSION_INVALID",
    )
    _require(
        candidate["commit_outcome_recovery"]
        == EXPECTED_INITIALIZATION_CONTRACT["commit_outcome_recovery"],
        "C2B3A_RECOVERY_INVALID",
    )
    _require(
        candidate["conflict_precedence"]
        == EXPECTED_INITIALIZATION_CONTRACT["conflict_precedence"],
        "C2B3A_CONFLICT_PRECEDENCE_INVALID",
    )
    _require(
        candidate["privacy_and_traceback"]
        == EXPECTED_INITIALIZATION_CONTRACT["privacy_and_traceback"],
        "C2B3A_PRIVACY_INVALID",
    )
    _require(
        candidate["later_author_effect_owner_decisions"]
        == EXPECTED_INITIALIZATION_CONTRACT[
            "later_author_effect_owner_decisions"
        ],
        "C2B3A_LATER_AUTHOR_BOUNDARY_INVALID",
    )
    _require(
        candidate["future_c2b3b_maximum_path_scope"]
        == EXPECTED_INITIALIZATION_CONTRACT[
            "future_c2b3b_maximum_path_scope"
        ],
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        candidate["nonimplementation"]
        == EXPECTED_INITIALIZATION_CONTRACT["nonimplementation"],
        "C2B3A_NONIMPLEMENTATION_INVALID",
    )


def _candidate() -> dict[str, object]:
    value = deepcopy(EXPECTED_INITIALIZATION_CONTRACT)
    assert type(value) is dict
    return value


def _golden_candidate() -> dict[str, object]:
    value = deepcopy(EXPECTED_INITIALIZATION_GOLDEN_VECTOR)
    assert type(value) is dict
    return value


def _traceback_signature(
    traceback_object: object,
) -> tuple[tuple[int, int, str], ...]:
    signature: tuple[tuple[int, int, str], ...] = ()
    current = traceback_object
    while current is not None:
        signature += (
            (
                id(current),
                id(current.tb_frame.f_code),
                current.tb_frame.f_code.co_name,
            ),
        )
        current = current.tb_next
    return signature


def _exception_graph_snapshot(
    exception: BaseException,
) -> tuple[object, object, bool, bool, object]:
    notes_present = "__notes__" in exception.__dict__
    notes = exception.__dict__["__notes__"] if notes_present else None
    return (
        exception.__cause__,
        exception.__context__,
        exception.__suppress_context__,
        notes_present,
        notes,
    )


def _process_control_exception_graph_contains_private_material(
    exception: BaseException,
) -> bool:
    forbidden = (
        "repair4-private-",
        "ordinary commit exception",
        "ordinary close exception",
        "raw SQLite exception",
        "/private/tmp/repair4-sensitive",
        "SELECT repair4-sensitive",
        "work-spec-repair4-sensitive",
    )
    seen: tuple[int, ...] = ()
    current: BaseException | None = exception
    while current is not None and id(current) not in seen:
        seen += (id(current),)
        rendered_exception = repr(current)
        rendered_string = str(current)
        rendered_args = repr(current.args)
        rendered_dictionary = repr(current.__dict__)
        rendered_traceback = repr(
            _traceback_signature(current.__traceback__)
        )
        rendered = (
            rendered_exception,
            rendered_string,
            rendered_args,
            rendered_dictionary,
            rendered_traceback,
        )
        if any(item in value for item in forbidden for value in rendered):
            return True
        traceback_object = current.__traceback__
        while traceback_object is not None:
            for local_name in traceback_object.tb_frame.f_locals:
                local_value = repr(
                    traceback_object.tb_frame.f_locals[local_name]
                )
                if any(item in local_value for item in forbidden):
                    return True
            traceback_object = traceback_object.tb_next
        if current.__cause__ is not None:
            current = current.__cause__
        else:
            current = current.__context__
    return False


def _bare_reraise_reference(
    injected_exception: BaseException,
) -> dict[str, object]:
    caught_traceback_tail = None
    caught_signature: tuple[tuple[int, int, str], ...] = ()
    graph_before: tuple[object, object, bool, bool, object] | None = None
    try:
        try:
            raise injected_exception
        except BaseException as caught_exception:
            caught_traceback_tail = caught_exception.__traceback__
            caught_signature = _traceback_signature(caught_traceback_tail)
            graph_before = _exception_graph_snapshot(caught_exception)
            raise
    except BaseException as propagated_exception:
        propagated_signature = _traceback_signature(
            propagated_exception.__traceback__
        )
        return {
            "same_exception_object": propagated_exception is injected_exception,
            "caught_traceback_tail_identity_preserved": propagated_exception.__traceback__
            is caught_traceback_tail,
            "repair_owned_traceback_frame_delta": len(propagated_signature)
            - len(caught_signature),
            "caught_signature": caught_signature,
            "propagated_signature": propagated_signature,
            "graph_before": graph_before,
            "graph_after": _exception_graph_snapshot(propagated_exception),
            "private_material_in_exception_graph": _process_control_exception_graph_contains_private_material(
                propagated_exception
            ),
        }
    assert False


def _named_reraise_reference(
    injected_exception: BaseException,
) -> dict[str, object]:
    caught_traceback_tail = None
    caught_signature: tuple[tuple[int, int, str], ...] = ()
    try:
        try:
            raise injected_exception
        except BaseException as caught_exception:
            caught_traceback_tail = caught_exception.__traceback__
            caught_signature = _traceback_signature(caught_traceback_tail)
            raise caught_exception
    except BaseException as propagated_exception:
        propagated_signature = _traceback_signature(
            propagated_exception.__traceback__
        )
        return {
            "same_exception_object": propagated_exception is injected_exception,
            "caught_traceback_tail_identity_preserved": propagated_exception.__traceback__
            is caught_traceback_tail,
            "repair_owned_traceback_frame_delta": len(propagated_signature)
            - len(caught_signature),
            "caught_signature": caught_signature,
            "propagated_signature": propagated_signature,
        }
    assert False


def _expect_violation(candidate: object, code: str) -> None:
    with pytest.raises(_ContractViolation) as exc_info:
        _validate_contract(candidate)
    assert str(exc_info.value) == code


def _expect_golden_violation(candidate: object) -> None:
    with pytest.raises(_ContractViolation) as exc_info:
        _validate_golden_vector(candidate)
    assert str(exc_info.value) == "C2B3A_GOLDEN_VECTOR_INVALID"


def _assert_preassigned_binding(
    contract: dict[str, object],
    vector: dict[str, object],
) -> None:
    relations = (
        "preassigned_attempt_candidate_binding.work_item_ref == safe command work_spec_safe_projection.work_item_ref == sole program-version membership work_item_ref == sole WorkSpec binding work_item_ref",
        "preassigned_attempt_candidate_binding.work_item_revision_ref == safe command work_spec_safe_projection.work_item_revision_ref == sole program-version membership work_item_revision_ref == sole WorkSpec binding work_item_revision_ref",
        "preassigned_attempt_candidate_binding.preassigned_semantic_attempt_ref == safe command preassigned_semantic_attempt_ref == initialize decision preassigned_semantic_attempt_ref",
        "preassigned_attempt_candidate_binding.preassigned_candidate_ref == safe command preassigned_candidate_ref == initialize decision preassigned_candidate_ref",
    )
    cardinality = contract["genesis_cardinality"]
    _require(
        "selected_attempt_candidate_binding" not in cardinality,
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    _require(
        "preassigned_attempt_candidate_binding" in cardinality,
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    binding = cardinality["preassigned_attempt_candidate_binding"]
    _require(
        binding["ordered_fields"]
        == (
            "work_item_ref",
            "work_item_revision_ref",
            "preassigned_semantic_attempt_ref",
            "preassigned_candidate_ref",
        ),
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    _require(
        binding["relations"] == relations,
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    _require(
        tuple(contract["safe_command"]["cross_relations"][-4:]) == relations,
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    binding_rendered = repr(binding)
    binding_text = binding_rendered.lower()
    for forbidden in (
        "selected",
        "current",
        "created",
        "authorized",
        "executable",
    ):
        _require(
            forbidden not in binding_text,
            "C2B3A_PREASSIGNED_BINDING_INVALID",
        )
    _require(
        binding["future_lineage_only"] is True,
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    _require(
        binding["creates_selects_authorizes_or_executes_attempt_or_candidate"]
        is False,
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )

    safe = vector["safe_command"]
    projection = safe["work_spec_safe_projection"]
    rows = vector["persisted_rows"]
    decision = rows["initialize_decision"]
    membership = rows["program_version_work_item"]
    work_spec_binding = rows["work_spec_binding"]
    _require(
        projection["work_item_ref"]
        == membership["work_item_ref"]
        == work_spec_binding["work_item_ref"],
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    _require(
        projection["work_item_revision_ref"]
        == membership["work_item_revision_ref"]
        == work_spec_binding["work_item_revision_ref"],
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    _require(
        safe["preassigned_semantic_attempt_ref"]
        == decision["preassigned_semantic_attempt_ref"],
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    _require(
        safe["preassigned_candidate_ref"]
        == decision["preassigned_candidate_ref"],
        "C2B3A_PREASSIGNED_BINDING_INVALID",
    )
    for field in (
        "selected_semantic_attempt_ref",
        "selected_candidate_ref",
        "selected_attempt_fence_ref",
        "selected_attempt_fence_digest",
    ):
        _require(
            decision[field] is None,
            "C2B3A_PREASSIGNED_BINDING_INVALID",
        )
    for absent_role in ("semantic_attempt", "candidate", "attempt_fence"):
        _require(
            absent_role not in rows,
            "C2B3A_PREASSIGNED_BINDING_INVALID",
        )


def _assert_original_apply_outcome(contract: dict[str, object]) -> None:
    expected_error = {
        "type": "SQLiteMutationStoreError",
        "reason": "commit_outcome_unknown",
        "internal_detail": None,
        "cause": None,
        "context": None,
        "notes": None,
        "raised_from": None,
    }
    gate = contract["commit_uncertainty_cleanup_gate"]
    complete = gate["close_complete"]
    quarantined = gate["close_not_proved"]
    _require(
        complete.get("original_apply_error") == expected_error,
        "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID",
    )
    _require(
        quarantined.get("original_apply_error") == expected_error,
        "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID",
    )
    _require(
        quarantined["ordered_steps"]
        == (
            "commit attempt raises",
            "controller retains connection custody and mutation slot",
            "close is attempted",
            "close not proved",
            "connection custody transfers to private _WriterSessionResource",
            "session quarantine is recorded",
            "writer-authority lock remains retained",
            "mutation slot remains unavailable",
            "fresh content-free commit_outcome_unknown is raised from None",
        ),
        "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID",
    )
    for field in (
        "close_failure_replaces_primary_error",
        "close_failure_decorates_primary_error",
        "close_failure_leaks_outward",
        "close_exception_in_outward_error_graph",
        "mutation_slot_available",
        "same_session_database_backed_resolver",
        "new_session_resolver_before_proved_close",
        "automatic_semantic_retry",
    ):
        _require(
            quarantined[field] is False,
            "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID",
        )
    _require(
        quarantined["same_session_resolver_disposition"]
        == "unresolved before operation-lease acquisition, database open, BEGIN, or SQL",
        "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID",
    )
    _require(
        complete["session_quarantined"] is False
        and complete["mutation_slot_available"] is True
        and complete["slot_release_gate"] == "only after close proof",
        "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID",
    )
    _require(
        tuple(quarantined["process_control_exceptions"])
        == ("KeyboardInterrupt", "SystemExit", "GeneratorExit"),
        "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID",
    )


def _assert_future_c2b3b_scope(contract: dict[str, object]) -> None:
    production = (
        "src/ge_nwp_coordinator/_development_program_initialization_contracts.py",
        "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py",
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "src/ge_nwp_coordinator/sqlite_writer_session.py",
        "src/ge_nwp_coordinator/sqlite_connection.py",
    )
    documentation_status = (
        ".docs/c2b-durable-development-state.md",
        ".docs/c2b3-program-initialization.md",
        ".docs/c2b2-private-readers.md",
        ".docs/architecture.md",
        ".docs/durable-state-model.md",
        ".docs/sqlite-operations-and-recovery.md",
        ".docs/sqlite-threat-model.md",
        "README.md",
        "AGENTS.md",
    )
    tests = (
        "tests/test_c2b3_program_initialization_contract.py",
        "tests/test_c2b3_private_atomic_program_initialization.py",
        "tests/test_c2b3_program_initialization_recovery.py",
        "tests/test_c2b3_private_program_initialization_delegation.py",
        "tests/test_c2b2_field_level_contract.py",
        "tests/test_c2b2_private_development_readers.py",
        "tests/test_c2b2_development_reader_contracts.py",
        "tests/test_runtime_non_authority.py",
        "tests/test_architecture_contracts.py",
        "tests/test_c2b0_durable_state_contract.py",
    )
    scope = contract["future_c2b3b_maximum_path_scope"]
    _require(
        scope["tranche"] == "C2B3B_PRIVATE_ATOMIC_INITIALIZATION",
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        scope["maximum_paths"] == 24
        and scope["production"] == production
        and scope["documentation_status"] == documentation_status
        and scope["tests"] == tests,
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        scope["counts"]
        == {
            "production": 5,
            "documentation_status": 9,
            "tests": 10,
            "total": 24,
        },
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    combined = production + documentation_status + tests
    _require(
        len(combined) == 24 and len(set(combined)) == 24,
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    responsibilities = scope["production_responsibilities"]
    _require(
        tuple(responsibilities) == production,
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        "no process-control result or enum"
        in responsibilities[
            "src/ge_nwp_coordinator/_development_program_initialization_contracts.py"
        ],
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        "does not catch, translate, wrap, or retry KeyboardInterrupt, SystemExit, or GeneratorExit after transaction cleanup returns them for propagation"
        in responsibilities[
            "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py"
        ],
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        "retain uncertain connection and mutation slot after commit exception"
        in responsibilities["src/ge_nwp_coordinator/sqlite_transition_transaction.py"],
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        "re-raise the identical process-control exception only after publication completion"
        in responsibilities["src/ge_nwp_coordinator/sqlite_transition_transaction.py"],
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    for exact_responsibility in (
        "reduce and detach the ordinary commit failure before close-time process-control handling",
        "catch exactly KeyboardInterrupt, SystemExit, and GeneratorExit from close",
        "retain connection, slot, and writer-lock custody",
        "perform a bare re-raise in the same catch suite",
        "add no traceback frame beyond bare-reraise semantics",
        "add no cause, context, note, or exception-graph material",
    ):
        _require(
            exact_responsibility
            in responsibilities[
                "src/ge_nwp_coordinator/sqlite_transition_transaction.py"
            ],
            "C2B3A_FUTURE_SCOPE_INVALID",
        )
    _require(
        "_WriterSessionResource retained-connection custody"
        in responsibilities["src/ge_nwp_coordinator/sqlite_writer_session.py"],
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        "acknowledge quarantine publication before the transaction layer re-raises a named process-control exception"
        in responsibilities["src/ge_nwp_coordinator/sqlite_writer_session.py"],
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    for exact_responsibility in (
        "publication acknowledgement must not raise or attach an ordinary exception to the process-control exception",
        "publication helpers receive no authority to propagate or replace the caught process-control exception",
    ):
        _require(
            exact_responsibility
            in responsibilities["src/ge_nwp_coordinator/sqlite_writer_session.py"],
            "C2B3A_FUTURE_SCOPE_INVALID",
        )
    connection_responsibilities = responsibilities[
        "src/ge_nwp_coordinator/sqlite_connection.py"
    ]
    _require(
        "cross-thread close from session-resource finalization is permitted only for proved closure"
        in connection_responsibilities,
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        "may surface the exact close-time KeyboardInterrupt, SystemExit, or GeneratorExit"
        in connection_responsibilities,
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    scope_text = repr(scope)
    _require(
        "StateStore quarantine" not in scope_text
        and "public WriterSession quarantine" not in scope_text,
        "C2B3A_FUTURE_SCOPE_INVALID",
    )
    _require(
        scope["twenty_fifth_path"] == "future implementation stop condition"
        and scope["authorized_by_this_freeze"] is False,
        "C2B3A_FUTURE_SCOPE_INVALID",
    )


def _enclosing_function_name(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> str | None:
    current = parents.get(node)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
        current = parents.get(current)
    return None


def _assigned_names(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, (ast.Tuple, ast.List)):
        names: list[str] = []
        for element in node.elts:
            names.extend(_assigned_names(element))
        return tuple(names)
    return ()


def _direct_literal_assignment(
    tree: ast.Module,
    name: str,
    expected: object,
) -> None:
    assignments = [
        statement
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == name
    ]
    _require(len(assignments) == 1, "C2B3A_ORACLE_EXPECTED_NOT_LITERAL")
    assignment = assignments[0]
    _require(isinstance(assignment.value, ast.Dict), "C2B3A_ORACLE_EXPECTED_NOT_LITERAL")
    try:
        value = ast.literal_eval(assignment.value)
    except (SyntaxError, ValueError):
        raise _ContractViolation("C2B3A_ORACLE_EXPECTED_NOT_LITERAL") from None
    _require(value == expected, "C2B3A_ORACLE_EXPECTED_NOT_LITERAL")


def _direct_allowed_import_inventory(tree: ast.Module) -> None:
    assignments = [
        statement
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "ALLOWED_ORACLE_IMPORTS"
    ]
    _require(len(assignments) == 1, "C2B3A_ORACLE_FORBIDDEN_INPUT")
    assignment = assignments[0]
    _require(isinstance(assignment.value, ast.Tuple), "C2B3A_ORACLE_FORBIDDEN_INPUT")
    _require(
        ast.literal_eval(assignment.value) == ("ast", "copy", "pathlib", "pytest"),
        "C2B3A_ORACLE_FORBIDDEN_INPUT",
    )


def _assert_oracle_architecture(source: str) -> None:
    try:
        tree = ast.parse(source, filename=TEST_PATH.name)
    except SyntaxError:
        raise _ContractViolation("C2B3A_ORACLE_FORBIDDEN_INPUT") from None
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    top_level_nodes = {id(node) for node in tree.body}
    observed_imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            _require(id(node) in top_level_nodes, "C2B3A_ORACLE_FORBIDDEN_INPUT")
            for item in node.names:
                _require(item.asname is None, "C2B3A_ORACLE_FORBIDDEN_INPUT")
                observed_imports.append(item.name)
        elif isinstance(node, ast.ImportFrom):
            _require(id(node) in top_level_nodes, "C2B3A_ORACLE_FORBIDDEN_INPUT")
            _require(
                node.level == 0 and node.module is not None,
                "C2B3A_ORACLE_FORBIDDEN_INPUT",
            )
            for item in node.names:
                _require(item.asname is None, "C2B3A_ORACLE_FORBIDDEN_INPUT")
            observed_imports.append(node.module)
    _require(
        tuple(sorted(observed_imports)) == ("ast", "copy", "pathlib", "pytest"),
        "C2B3A_ORACLE_FORBIDDEN_INPUT",
    )

    forbidden_dynamic_names = {
        "eval",
        "exec",
        "compile",
        "getattr",
        "setattr",
        "delattr",
        "globals",
        "locals",
        "vars",
        "__import__",
        "import_module",
        "open",
    }
    allowed_read_calls = 0
    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            _require(
                node.id not in forbidden_dynamic_names,
                "C2B3A_ORACLE_FORBIDDEN_INPUT",
            )
        if isinstance(node, ast.Attribute):
            _require(
                node.attr not in forbidden_dynamic_names,
                "C2B3A_ORACLE_FORBIDDEN_INPUT",
            )
        if isinstance(node, ast.Lambda):
            raise _ContractViolation("C2B3A_ORACLE_DYNAMIC_DISPATCH")
        if isinstance(node, ast.Call):
            _require(
                not isinstance(node.func, ast.Subscript),
                "C2B3A_ORACLE_DYNAMIC_DISPATCH",
            )
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "read_text",
                "read_bytes",
                "open",
            }:
                _require(
                    node.func.attr == "read_text"
                    and _enclosing_function_name(node, parents) == "_read_allowed_text"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "resolved"
                    and not node.args
                    and len(node.keywords) == 1
                    and node.keywords[0].arg == "encoding"
                    and isinstance(node.keywords[0].value, ast.Constant)
                    and node.keywords[0].value.value == "utf-8",
                    "C2B3A_ORACLE_FORBIDDEN_INPUT",
                )
                allowed_read_calls += 1
            if isinstance(node.func, ast.Name) and node.func.id == "_read_allowed_text":
                _require(
                    len(node.args) == 1
                    and isinstance(node.args[0], ast.Name)
                    and node.args[0].id in {"OWNER_PATH", "PLANNING_PATH", "TEST_PATH"}
                    and not node.keywords,
                    "C2B3A_ORACLE_FORBIDDEN_INPUT",
                )
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            normalized_name = node.name.lower()
            _require(
                "dispatch" not in normalized_name
                and "runner" not in normalized_name
                and "run_mutation" not in normalized_name
                and "run_counterfactual" not in normalized_name,
                "C2B3A_ORACLE_DYNAMIC_DISPATCH",
            )
            parameter_names = {
                argument.arg
                for argument in (
                    *node.args.posonlyargs,
                    *node.args.args,
                    *node.args.kwonlyargs,
                )
            }
            if node.args.vararg is not None:
                parameter_names.add(node.args.vararg.arg)
            if node.args.kwarg is not None:
                parameter_names.add(node.args.kwarg.arg)
            for descendant in ast.walk(node):
                if isinstance(descendant, ast.Call) and isinstance(
                    descendant.func, ast.Name
                ):
                    _require(
                        descendant.func.id not in parameter_names,
                        "C2B3A_ORACLE_DYNAMIC_DISPATCH",
                    )
        if isinstance(node, ast.For):
            loop_names = set(_assigned_names(node.target))
            for descendant in ast.walk(node):
                if isinstance(descendant, ast.Call) and isinstance(
                    descendant.func, ast.Name
                ):
                    _require(
                        descendant.func.id not in loop_names,
                        "C2B3A_ORACLE_DYNAMIC_DISPATCH",
                    )
        if isinstance(node, ast.comprehension):
            loop_names = set(_assigned_names(node.target))
            container = parents.get(node)
            while container is not None and not isinstance(
                container,
                (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp),
            ):
                container = parents.get(container)
            _require(container is not None, "C2B3A_ORACLE_DYNAMIC_DISPATCH")
            for descendant in ast.walk(container):
                if isinstance(descendant, ast.Call) and isinstance(
                    descendant.func, ast.Name
                ):
                    _require(
                        descendant.func.id not in loop_names,
                        "C2B3A_ORACLE_DYNAMIC_DISPATCH",
                    )
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            target_names = tuple(
                name for target in targets for name in _assigned_names(target)
            )
            _require(
                not any(
                    "registry" in name.lower()
                    or "dispatcher" in name.lower()
                    or "runners" in name.lower()
                    for name in target_names
                ),
                "C2B3A_ORACLE_DYNAMIC_DISPATCH",
            )
            value = node.value
            if isinstance(value, ast.Name):
                _require(
                    value.id not in function_names,
                    "C2B3A_ORACLE_DYNAMIC_DISPATCH",
                )
            if isinstance(value, (ast.Dict, ast.List, ast.Tuple, ast.Set)):
                _require(
                    not any(
                        (
                            isinstance(descendant, ast.Name)
                            and descendant.id in function_names
                            and not (
                                isinstance(parents.get(descendant), ast.Call)
                                and parents.get(descendant).func is descendant
                            )
                        )
                        or isinstance(descendant, (ast.Attribute, ast.Lambda))
                        for descendant in ast.walk(value)
                    ),
                    "C2B3A_ORACLE_DYNAMIC_DISPATCH",
                )
    _require(allowed_read_calls == 1, "C2B3A_ORACLE_FORBIDDEN_INPUT")
    _direct_allowed_import_inventory(tree)
    _direct_literal_assignment(
        tree,
        "EXPECTED_INITIALIZATION_CONTRACT",
        EXPECTED_INITIALIZATION_CONTRACT,
    )
    _direct_literal_assignment(
        tree,
        "EXPECTED_INITIALIZATION_GOLDEN_VECTOR",
        EXPECTED_INITIALIZATION_GOLDEN_VECTOR,
    )


def test_owner_literal_equals_independent_expected_contract() -> None:
    owner_contract_candidate = _owner_contract()
    assert owner_contract_candidate == EXPECTED_INITIALIZATION_CONTRACT
    assert tuple(owner_contract_candidate) == tuple(EXPECTED_INITIALIZATION_CONTRACT)
    _validate_contract(owner_contract_candidate)


def test_owner_golden_vector_equals_independent_direct_literal() -> None:
    owner_golden_vector_candidate = _owner_golden_vector()
    assert owner_golden_vector_candidate == EXPECTED_INITIALIZATION_GOLDEN_VECTOR
    assert tuple(owner_golden_vector_candidate) == tuple(
        EXPECTED_INITIALIZATION_GOLDEN_VECTOR
    )
    observed_repr = repr(owner_golden_vector_candidate)
    expected_repr = repr(EXPECTED_INITIALIZATION_GOLDEN_VECTOR)
    assert observed_repr.encode("utf-8") == expected_repr.encode("utf-8")
    owner_source = _read_allowed_text(OWNER_PATH)
    owner_parts = owner_source.split(VECTOR_BEGIN_MARKER, 1)
    vector_remainder = owner_parts[1]
    vector_parts = vector_remainder.split(
        VECTOR_END_MARKER,
        1,
    )
    payload = vector_parts[0]
    stripped_payload = payload.strip()
    payload_lines = stripped_payload.splitlines()
    newline = "\n"
    owner_literal_source = newline.join(payload_lines[1:-1])
    oracle_source = _read_allowed_text(TEST_PATH)
    oracle_tree = ast.parse(oracle_source, filename=TEST_PATH.name)
    assignment = next(
        statement
        for statement in oracle_tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "EXPECTED_INITIALIZATION_GOLDEN_VECTOR"
    )
    oracle_literal_source = ast.get_source_segment(oracle_source, assignment.value)
    assert oracle_literal_source == owner_literal_source
    _validate_golden_vector(owner_golden_vector_candidate)


def test_golden_vector_is_complete_privacy_safe_single_work_ledger() -> None:
    vector = deepcopy(EXPECTED_INITIALIZATION_GOLDEN_VECTOR)
    assert vector["vector_id"] == "c2b3a-initialization-single-work-v1"
    assert vector["vector_version"] == 1
    assert vector["transaction_timestamp"] == "2026-08-21T12:34:56Z"
    rows = vector["persisted_rows"]
    assert type(rows) is dict and len(rows) == 9
    assert type(vector["graph_entries"]) is tuple and len(vector["graph_entries"]) == 8
    decision = rows["initialize_decision"]
    assert decision["selected_semantic_attempt_ref"] is None
    assert decision["selected_candidate_ref"] is None
    assert decision["preassigned_semantic_attempt_ref"] == "semantic-attempt-c2b3a-1"
    assert decision["preassigned_candidate_ref"] == "candidate-c2b3a-1"
    binding_ref = rows["work_spec_binding"]["work_spec_ref"]
    assert binding_ref == vector["safe_command"]["work_spec_safe_projection"]["work_spec_ref"]
    assert binding_ref == vector["graph_entries"][7]["record_ref"]
    assert vector["mutation_receipt"] == rows["mutation_receipt"]
    rendered = repr(vector)
    for forbidden in ("objective", "requirements text", "exclusions text", "credential", "endpoint"):
        assert forbidden not in rendered


def test_golden_vector_digest_byte_row_graph_and_envelope_mutants_are_rejected() -> None:
    candidate = _golden_candidate()
    candidate["accepted_intent_safe_projection_digest"] = "0" * 64
    _expect_golden_violation(candidate)

    candidate = _golden_candidate()
    candidate["safe_command_canonical_utf8_hex"] = "00"
    _expect_golden_violation(candidate)

    candidate = _golden_candidate()
    candidate["persisted_rows"]["program_head"]["head_digest"] = "0" * 64
    _expect_golden_violation(candidate)

    candidate = _golden_candidate()
    candidate["graph_entries"][0]["record_digest"] = "0" * 64
    _expect_golden_violation(candidate)

    candidate = _golden_candidate()
    candidate["result_projection_digest"] = "0" * 64
    _expect_golden_violation(candidate)

    candidate = _golden_candidate()
    candidate["mutation_graph_digest"] = "0" * 64
    _expect_golden_violation(candidate)

    candidate = _golden_candidate()
    candidate["mutation_receipt"]["result_class"] = "different"
    _expect_golden_violation(candidate)

    candidate = _golden_candidate()
    del candidate["private_exact_replay_result"]
    _expect_golden_violation(candidate)


def test_golden_vector_parser_rejects_marker_fence_and_literal_bypasses() -> None:
    text = _read_allowed_text(OWNER_PATH)
    with pytest.raises(_ContractViolation) as exc_info:
        _owner_golden_vector(text.replace(VECTOR_BEGIN_MARKER, "", 1))
    assert str(exc_info.value) == "C2B3A_GOLDEN_VECTOR_MARKER_INVALID"

    with pytest.raises(_ContractViolation) as exc_info:
        _owner_golden_vector(text.replace(VECTOR_END_MARKER, VECTOR_BEGIN_MARKER, 1))
    assert str(exc_info.value) == "C2B3A_GOLDEN_VECTOR_MARKER_INVALID"

    vector_start = text.index(VECTOR_BEGIN_MARKER)
    vector_tail = text[vector_start:]
    with pytest.raises(_ContractViolation) as exc_info:
        _owner_golden_vector(
            text[:vector_start]
            + vector_tail.replace("```python", "```json", 1)
        )
    assert str(exc_info.value) == "C2B3A_GOLDEN_VECTOR_FENCE_INVALID"

    with pytest.raises(_ContractViolation) as exc_info:
        _owner_golden_vector(
            text[:vector_start]
            + vector_tail.replace("{'vector_id'", "dict(vector_id", 1)
        )
    assert str(exc_info.value) == "C2B3A_GOLDEN_VECTOR_LITERAL_INVALID"


def test_expected_contract_is_one_direct_literal_with_bounded_oracle_inputs() -> None:
    source = _read_allowed_text(TEST_PATH)
    _assert_oracle_architecture(source)


def test_oracle_architecture_counterfactuals_are_rejected() -> None:
    source = _read_allowed_text(TEST_PATH)
    insertion = "\ndef test_owner_literal_equals_independent_expected_contract"

    composite = """
def _architecture_probe():
    import hashlib
    import sqlite3
    import importlib
    import builtins
    builtins.eval("0")
    builtins.exec("pass")
    builtins.compile("0", "x", "eval")
    builtins.getattr(object(), "x", None)
    importlib.import_module("ge_nwp_coordinator")
    Path("/alternate").read_text(encoding="utf-8")
    Path("/alternate").read_bytes()
    VALIDATOR_REGISTRY = {"contract": _validate_contract}
    VALIDATOR_REGISTRY["contract"]({})
    for validator in VALIDATOR_REGISTRY.values():
        validator({})

def _run_mutation(value):
    return _validate_contract(value)
"""
    mutant = source.replace(insertion, composite + insertion, 1)
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_oracle_architecture(mutant)
    assert str(exc_info.value) == "C2B3A_ORACLE_FORBIDDEN_INPUT"

    for snippet, expected_code in (
        (
            '\nVALIDATOR_REGISTRY = {"contract": _validate_contract}\n',
            "C2B3A_ORACLE_DYNAMIC_DISPATCH",
        ),
        (
            "\ndef _semantic_dispatcher(value):\n    return _validate_contract(value)\n",
            "C2B3A_ORACLE_DYNAMIC_DISPATCH",
        ),
        (
            "\ndef _run_mutation(value):\n    return _validate_contract(value)\n",
            "C2B3A_ORACLE_DYNAMIC_DISPATCH",
        ),
        (
            '\nALTERNATE_DATA = Path("/alternate").read_bytes()\n',
            "C2B3A_ORACLE_FORBIDDEN_INPUT",
        ),
        (
            '\nCALLABLES = {"contract": _validate_contract}\nCALLABLES["contract"]({})\n',
            "C2B3A_ORACLE_DYNAMIC_DISPATCH",
        ),
        (
            '\nCALLABLES = (_validate_contract,)\nfor callback in CALLABLES:\n    callback({})\n',
            "C2B3A_ORACLE_DYNAMIC_DISPATCH",
        ),
    ):
        mutant = source.replace(insertion, snippet + insertion, 1)
        with pytest.raises(_ContractViolation) as exc_info:
            _assert_oracle_architecture(mutant)
        assert str(exc_info.value) == expected_code

    mutant = source.replace(
        "EXPECTED_INITIALIZATION_GOLDEN_VECTOR = {",
        "EXPECTED_INITIALIZATION_GOLDEN_VECTOR = _owner_golden_vector() or {",
        1,
    )
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_oracle_architecture(mutant)
    assert str(exc_info.value) == "C2B3A_ORACLE_EXPECTED_NOT_LITERAL"

    mutant = source.replace(
        "EXPECTED_INITIALIZATION_GOLDEN_VECTOR = {",
        "EXPECTED_INITIALIZATION_GOLDEN_VECTOR = _production_vector() or {",
        1,
    )
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_oracle_architecture(mutant)
    assert str(exc_info.value) == "C2B3A_ORACLE_EXPECTED_NOT_LITERAL"


def test_owner_literal_parser_rejects_marker_fence_and_literal_bypasses() -> None:
    text = _read_allowed_text(OWNER_PATH)

    _expect_code = "C2B3A_OWNER_MARKER_INVALID"
    with pytest.raises(_ContractViolation) as exc_info:
        _owner_contract(text.replace(BEGIN_MARKER, "", 1))
    assert str(exc_info.value) == _expect_code

    with pytest.raises(_ContractViolation) as exc_info:
        _owner_contract(text.replace(END_MARKER, BEGIN_MARKER, 1))
    assert str(exc_info.value) == _expect_code

    with pytest.raises(_ContractViolation) as exc_info:
        _owner_contract(text.replace("```python", "```json", 1))
    assert str(exc_info.value) == "C2B3A_OWNER_FENCE_INVALID"

    with pytest.raises(_ContractViolation) as exc_info:
        _owner_contract(text.replace("{\n    \"contract_identity\"", "dict(contract_identity", 1))
    assert str(exc_info.value) == "C2B3A_OWNER_LITERAL_INVALID"


def _planning_mutant_at_position(text: str, claim: str, position: str) -> str:
    if position == "prelude":
        return text.replace(
            "# C2B3 Program Initialization\n",
            "# C2B3 Program Initialization\n\n" + claim + "\n",
            1,
        )
    if position == "middle":
        return text.replace(
            "## Private Delegation Shape",
            claim + "\n\n## Private Delegation Shape",
            1,
        )
    if position == "after-source-layout":
        return text.replace(
            "## Planned C2B3B Source Layout\n",
            "## Planned C2B3B Source Layout\n\n" + claim + "\n",
            1,
        )
    assert position == "tail"
    return text.rstrip("\n") + "\n\n" + claim + "\n"


def test_planning_status_baseline_scans_complete_nonfenced_document() -> None:
    planning_document_candidate = _read_allowed_text(PLANNING_PATH)
    _validate_planning_status(planning_document_candidate)


@pytest.mark.parametrize(
    "position",
    ("prelude", "middle", "after-source-layout", "tail"),
)
@pytest.mark.parametrize(
    ("claim", "code"),
    (
        (
            "The planning document is semantic authority.",
            "C2B3A_PLANNING_AUTHORITY_CONTRADICTION",
        ),
        (
            "The planning document co-owns semantic truth.",
            "C2B3A_PLANNING_AUTHORITY_CONTRADICTION",
        ),
        (
            "Program initialization source is current.",
            "C2B3A_CURRENT_SOURCE_CONTRADICTION",
        ),
        (
            "Program initialization is implemented.",
            "C2B3A_CURRENT_SOURCE_CONTRADICTION",
        ),
        (
            "Private delegation is current.",
            "C2B3A_CURRENT_SOURCE_CONTRADICTION",
        ),
        (
            "Receipt persistence is current.",
            "C2B3A_CURRENT_SOURCE_CONTRADICTION",
        ),
        (
            "Replay runtime is current.",
            "C2B3A_CURRENT_SOURCE_CONTRADICTION",
        ),
        (
            "Recovery runtime is current.",
            "C2B3A_CURRENT_SOURCE_CONTRADICTION",
        ),
        (
            "Author-effect source is current.",
            "C2B3A_CURRENT_SOURCE_CONTRADICTION",
        ),
    ),
)
def test_planning_additive_contradictions_are_rejected_at_every_position(
    claim: str,
    code: str,
    position: str,
) -> None:
    planning_document_candidate = _read_allowed_text(PLANNING_PATH)
    _validate_planning_status(planning_document_candidate)
    mutant = _planning_mutant_at_position(
        planning_document_candidate,
        claim,
        position,
    )
    with pytest.raises(_ContractViolation) as exc_info:
        _validate_planning_status(mutant)
    assert str(exc_info.value) == code


@pytest.mark.parametrize("marker", ("```", "~~~"))
def test_planning_correctly_closed_fenced_claim_is_ignored(marker: str) -> None:
    planning_document_candidate = _read_allowed_text(PLANNING_PATH)
    fenced = (
        marker
        + "text\nAuthor-effect source is current.\n"
        + marker
        + "\n"
    )
    mutant = _planning_mutant_at_position(
        planning_document_candidate,
        fenced,
        "middle",
    )
    _validate_planning_status(mutant)


def test_planning_unclosed_fence_and_text_bearing_pseudo_closer_are_bounded() -> None:
    planning_document_candidate = _read_allowed_text(PLANNING_PATH)
    unclosed = _planning_mutant_at_position(
        planning_document_candidate,
        "```text\nAuthor-effect source is current.",
        "tail",
    )
    with pytest.raises(_ContractViolation) as exc_info:
        _validate_planning_status(unclosed)
    assert str(exc_info.value) == "C2B3A_CURRENT_SOURCE_CONTRADICTION"

    fenced = (
        "```text\n"
        "``` text-bearing pseudo-closer\n"
        "> - Author-effect source is current.\n"
        "```"
    )
    pseudo_closer = _planning_mutant_at_position(
        planning_document_candidate,
        fenced,
        "middle",
    )
    _validate_planning_status(pseudo_closer)


def test_planning_markdown_prefixes_do_not_hide_forbidden_claims() -> None:
    planning_document_candidate = _read_allowed_text(PLANNING_PATH)
    mutant = _planning_mutant_at_position(
        planning_document_candidate,
        "> - Author-effect\t source   is current.",
        "tail",
    )
    with pytest.raises(_ContractViolation) as exc_info:
        _validate_planning_status(mutant)
    assert str(exc_info.value) == "C2B3A_CURRENT_SOURCE_CONTRADICTION"


def test_owner_and_five_path_scope_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    del candidate["owner_decisions"]["route_effect"]
    _expect_violation(candidate, "C2B3A_OWNER_DECISIONS_INVALID")

    candidate = _candidate()
    candidate["owner_decisions"]["unknown_owner_decision"] = True
    _expect_violation(candidate, "C2B3A_OWNER_DECISIONS_INVALID")

    candidate = _candidate()
    candidate["five_path_scope"]["untracked_additions"] += ("sixth-path",)
    candidate["five_path_scope"]["total_paths"] = 6
    _expect_violation(candidate, "C2B3A_WRITE_SCOPE_INVALID")

    candidate = _candidate()
    candidate["five_path_scope"]["production_source_paths"] = ("production-source",)
    _expect_violation(candidate, "C2B3A_WRITE_SCOPE_INVALID")

    candidate = _candidate()
    candidate["five_path_scope"]["migration_paths"] = ("migration",)
    _expect_violation(candidate, "C2B3A_WRITE_SCOPE_INVALID")

    candidate = _candidate()
    candidate["five_path_scope"]["public_api_paths"] = ("public-api",)
    _expect_violation(candidate, "C2B3A_WRITE_SCOPE_INVALID")


def test_genesis_cardinality_and_selection_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    candidate["genesis_cardinality"]["work_item_heads"] = 0
    _expect_violation(candidate, "C2B3A_GENESIS_CARDINALITY_INVALID")

    candidate = _candidate()
    candidate["genesis_cardinality"]["work_item_heads"] = 2
    _expect_violation(candidate, "C2B3A_GENESIS_CARDINALITY_INVALID")

    candidate = _candidate()
    candidate["sensitive_ingress"]["work_spec_count"] = 0
    _expect_violation(candidate, "C2B3A_SENSITIVE_INGRESS_INVALID")

    candidate = _candidate()
    candidate["sensitive_ingress"]["work_spec_count"] = 2
    _expect_violation(candidate, "C2B3A_SENSITIVE_INGRESS_INVALID")

    candidate = _candidate()
    candidate["sensitive_ingress"]["container_ingress"] = True
    _expect_violation(candidate, "C2B3A_SENSITIVE_INGRESS_INVALID")

    candidate = _candidate()
    candidate["owner_decisions"]["membership_ordinal"] = 1
    _expect_violation(candidate, "C2B3A_OWNER_DECISIONS_INVALID")

    candidate = _candidate()
    rejects = candidate["safe_command"]["rejects"]
    candidate["safe_command"]["rejects"] = tuple(
        item for item in rejects if item != "caller-supplied membership ordinal"
    )
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    rejects = candidate["safe_command"]["rejects"]
    candidate["safe_command"]["rejects"] = tuple(
        item for item in rejects if item != "implicit sorting"
    )
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")


def test_genesis_decision_selected_and_preassigned_algebra_is_closed() -> None:
    expected_postimage = _candidate()["row_and_head_ledger"]["postimages"][
        "initialize_decision"
    ]

    for field, value in (
        ("selected_semantic_attempt_ref", "semantic-attempt-c2b3a-1"),
        ("selected_candidate_ref", "candidate-c2b3a-1"),
        ("preassigned_semantic_attempt_ref", None),
        ("preassigned_candidate_ref", None),
    ):
        candidate = _candidate()
        postimage = list(expected_postimage)
        position = next(
            index for index, item in enumerate(postimage) if item[0] == field
        )
        postimage[position] = (field, value)
        candidate["row_and_head_ledger"]["postimages"]["initialize_decision"] = tuple(
            postimage
        )
        _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")

    candidate = _candidate()
    moved = []
    for field, value in expected_postimage:
        if field == "selected_semantic_attempt_ref":
            value = "exact preassigned_semantic_attempt_ref"
        elif field == "selected_candidate_ref":
            value = "exact preassigned_candidate_ref"
        elif field in {
            "preassigned_semantic_attempt_ref",
            "preassigned_candidate_ref",
        }:
            value = None
        moved.append((field, value))
    candidate["row_and_head_ledger"]["postimages"]["initialize_decision"] = tuple(
        moved
    )
    _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")


def test_accepted_intent_projection_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    candidate["accepted_intent_safe_projection"]["schema_id"] = "wrong"
    _expect_violation(candidate, "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID")

    candidate = _candidate()
    candidate["accepted_intent_safe_projection"]["digest_domain"] = "wrong"
    _expect_violation(candidate, "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID")

    candidate = _candidate()
    fields = candidate["accepted_intent_safe_projection"]["ordered_fields"]
    candidate["accepted_intent_safe_projection"]["ordered_fields"] = tuple(
        item for item in fields if item != "source_intent_ref"
    )
    _expect_violation(candidate, "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID")

    candidate = _candidate()
    candidate["accepted_intent_safe_projection"]["ordered_fields"] += ("objective",)
    _expect_violation(candidate, "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID")

    candidate = _candidate()
    forbidden = candidate["accepted_intent_safe_projection"]["caller_forbidden"]
    candidate["accepted_intent_safe_projection"]["caller_forbidden"] = tuple(
        item for item in forbidden if item != "safe_projection_digest"
    )
    _expect_violation(candidate, "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID")

    candidate = _candidate()
    candidate["accepted_intent_safe_projection"]["nested_projection_exact_type"] = "mapping"
    _expect_violation(candidate, "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID")

    candidate = _candidate()
    candidate["accepted_intent_safe_projection"]["ordered_fields"] += (
        "requirements",
        "exclusions",
    )
    _expect_violation(candidate, "C2B3A_ACCEPTED_INTENT_PROJECTION_INVALID")


def test_safe_command_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    candidate["safe_command"]["ordered_fields"] = candidate["safe_command"][
        "ordered_fields"
    ][:-1]
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    candidate["safe_command"]["ordered_fields"] += ("metadata",)
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    fields = list(candidate["safe_command"]["ordered_fields"])
    fields[1], fields[2] = fields[2], fields[1]
    candidate["safe_command"]["ordered_fields"] = tuple(fields)
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    candidate["safe_command"]["schema_id"] = "wrong"
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    candidate["safe_command"]["digest_domain"] = "wrong"
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    field_types = list(candidate["safe_command"]["exact_field_types"])
    field_types[9] = ("coding_global_stop_version", "bool")
    candidate["safe_command"]["exact_field_types"] = tuple(field_types)
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    rejects = candidate["safe_command"]["rejects"]
    candidate["safe_command"]["rejects"] = tuple(
        item for item in rejects if item != "subclasses"
    )
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    rejects = candidate["safe_command"]["rejects"]
    candidate["safe_command"]["rejects"] = tuple(
        item for item in rejects if item != "implicit refs"
    )
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    candidate["safe_command"]["reason_code"] = "initialize"
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    candidate = _candidate()
    candidate["safe_command"]["identity_excludes"] = ()
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")


def test_row_write_and_graph_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    candidate["row_and_head_ledger"]["inserted_rows"] = candidate[
        "row_and_head_ledger"
    ]["inserted_rows"][:-1]
    _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")

    candidate = _candidate()
    candidate["row_and_head_ledger"]["inserted_rows"] += ("extra_row",)
    _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")

    candidate = _candidate()
    candidate["row_and_head_ledger"]["inserted_rows"] += ("revision_edge",)
    _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")

    candidate = _candidate()
    candidate["row_and_head_ledger"]["inserted_rows"] += ("semantic_attempt",)
    _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")

    candidate = _candidate()
    postimage = list(candidate["row_and_head_ledger"]["postimages"]["program_head"])
    postimage[3] = ("program_state", "accepted")
    candidate["row_and_head_ledger"]["postimages"]["program_head"] = tuple(postimage)
    _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")

    candidate = _candidate()
    postimage = list(candidate["row_and_head_ledger"]["postimages"]["work_item_head"])
    postimage[2] = ("head_revision", 1)
    candidate["row_and_head_ledger"]["postimages"]["work_item_head"] = tuple(postimage)
    _expect_violation(candidate, "C2B3A_ROW_LEDGER_INVALID")

    candidate = _candidate()
    order = list(candidate["write_order"]["ordered_rows"])
    order[0], order[1] = order[1], order[0]
    candidate["write_order"]["ordered_rows"] = tuple(order)
    _expect_violation(candidate, "C2B3A_WRITE_ORDER_INVALID")

    candidate = _candidate()
    candidate["initialize_graph"]["receipt_is_entry"] = True
    _expect_violation(candidate, "C2B3A_GRAPH_INVALID")

    candidate = _candidate()
    entries = list(candidate["initialize_graph"]["entries"])
    entries[0] = (0, "wrong_role", 0, "program_ref")
    candidate["initialize_graph"]["entries"] = tuple(entries)
    _expect_violation(candidate, "C2B3A_GRAPH_INVALID")

    candidate = _candidate()
    entries = list(candidate["initialize_graph"]["entries"])
    entries[1] = (2, "accepted_intent_revision", 0, "accepted_intent_revision_ref")
    candidate["initialize_graph"]["entries"] = tuple(entries)
    _expect_violation(candidate, "C2B3A_GRAPH_INVALID")

    candidate = _candidate()
    entries = list(candidate["initialize_graph"]["entries"])
    entries[2] = (2, "initialize_decision", 1, "decision_ref")
    candidate["initialize_graph"]["entries"] = tuple(entries)
    _expect_violation(candidate, "C2B3A_GRAPH_INVALID")

    candidate = _candidate()
    entries = list(candidate["initialize_graph"]["entries"])
    entries[3] = (3, "program_version", 0, "program_ref")
    candidate["initialize_graph"]["entries"] = tuple(entries)
    _expect_violation(candidate, "C2B3A_GRAPH_INVALID")

    candidate = _candidate()
    candidate["initialize_graph"]["entries"] += (
        (8, "coding_global_stop_dependency", 0, "coding_global_stop_ref"),
    )
    _expect_violation(candidate, "C2B3A_GRAPH_INVALID")


def test_locator_result_receipt_and_existing_projection_are_closed() -> None:
    candidate = _candidate()
    candidate["existing_work_spec_safe_projection"]["schema_id"] = "replacement"
    _expect_violation(candidate, "C2B3A_WORK_SPEC_PROJECTION_INVALID")

    candidate = _candidate()
    candidate["complete_graph_locator"]["lookups"] = candidate[
        "complete_graph_locator"
    ]["lookups"][:-1]
    _expect_violation(candidate, "C2B3A_LOCATOR_INVALID")

    candidate = _candidate()
    candidate["complete_graph_locator"]["completeness"] = candidate[
        "complete_graph_locator"
    ]["completeness"][:-1]
    _expect_violation(candidate, "C2B3A_LOCATOR_INVALID")

    candidate = _candidate()
    candidate["persisted_result_projection"]["result_program_version_ref"] = (
        "caller-selected version"
    )
    _expect_violation(candidate, "C2B3A_RESULT_PROJECTION_INVALID")

    candidate = _candidate()
    candidate["private_apply_result"]["dispositions"] += ("unknown",)
    _expect_violation(candidate, "C2B3A_PRIVATE_RESULT_INVALID")

    candidate = _candidate()
    candidate["mutation_receipt"]["self_digest"] = "present"
    _expect_violation(candidate, "C2B3A_RECEIPT_INVALID")


def test_work_spec_locator_exact_ref_relation_and_selection_are_closed() -> None:
    candidate = _candidate()
    candidate["complete_graph_locator"]["lookups"] = tuple(
        lookup.replace(", then exact work_spec_ref equality", "")
        for lookup in candidate["complete_graph_locator"]["lookups"]
    )
    _expect_violation(candidate, "C2B3A_LOCATOR_INVALID")

    candidate = _candidate()
    candidate["complete_graph_locator"]["returned_work_spec_ref_mismatch"] = (
        "select different WorkSpec"
    )
    _expect_violation(candidate, "C2B3A_LOCATOR_INVALID")

    candidate = _candidate()
    candidate["complete_graph_locator"]["forbidden_selection"] = (
        "absence",
        "scan",
    )
    _expect_violation(candidate, "C2B3A_LOCATOR_INVALID")


def test_replay_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    steps = candidate["exact_replay"]["ordered_steps"]
    candidate["exact_replay"]["ordered_steps"] = tuple(
        item for item in steps if item != "locate all eight graph entries"
    )
    _expect_violation(candidate, "C2B3A_REPLAY_INVALID")

    candidate = _candidate()
    steps = list(candidate["exact_replay"]["ordered_steps"])
    steps[2] = "present receipt with different command digest is exact replay"
    candidate["exact_replay"]["ordered_steps"] = tuple(steps)
    _expect_violation(candidate, "C2B3A_REPLAY_INVALID")

    candidate = _candidate()
    candidate["exact_replay"]["incomplete_or_malformed_graph"] = "exact_replay"
    _expect_violation(candidate, "C2B3A_REPLAY_INVALID")

    candidate = _candidate()
    candidate["exact_replay"]["later_valid_head_advancement"] = "replay failure"
    _expect_violation(candidate, "C2B3A_REPLAY_INVALID")

    candidate = _candidate()
    candidate["exact_replay"]["contradictory_same_revision_head"] = "exact_replay"
    _expect_violation(candidate, "C2B3A_REPLAY_INVALID")


def test_commit_recovery_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    candidate["commit_outcome_recovery"]["committed_exact_requires"] = (
        "exact receipt",
    )
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    candidate["commit_outcome_recovery"]["committed_exact_requires"] = (
        "both historical head postimages",
    )
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    candidate["commit_outcome_recovery"]["committed_exact_requires"] = (
        "partial graph",
    )
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    absent = candidate["commit_outcome_recovery"][
        "definitely_not_committed_requires_all_absent"
    ]
    candidate["commit_outcome_recovery"][
        "definitely_not_committed_requires_all_absent"
    ] = absent[:-1]
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    candidate["commit_outcome_recovery"][
        "basis_or_global_stop_presence_proves_family_commit"
    ] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    candidate["commit_outcome_recovery"]["automatic_semantic_retry"] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    candidate["commit_outcome_recovery"]["accepts_work_spec"] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    candidate["commit_outcome_recovery"][
        "mutation_slot_available_before_close_completion"
    ] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")


def test_preassigned_attempt_candidate_binding_is_exact_and_cross_related() -> None:
    _assert_preassigned_binding(
        EXPECTED_INITIALIZATION_CONTRACT,
        EXPECTED_INITIALIZATION_GOLDEN_VECTOR,
    )
    owner_contract_candidate = _owner_contract()
    _assert_preassigned_binding(
        owner_contract_candidate,
        EXPECTED_INITIALIZATION_GOLDEN_VECTOR,
    )


def test_preassigned_binding_mutants_b01_through_b08_are_rejected() -> None:
    contract = _candidate()
    cardinality = contract["genesis_cardinality"]
    binding = cardinality.pop(
        "preassigned_attempt_candidate_binding"
    )
    contract["genesis_cardinality"]["selected_attempt_candidate_binding"] = binding
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(contract, _golden_candidate())
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"

    contract = _candidate()
    relations = list(
        contract["genesis_cardinality"]["preassigned_attempt_candidate_binding"][
            "relations"
        ]
    )
    relations[0] = "selected attempt/candidate binding"
    contract["genesis_cardinality"]["preassigned_attempt_candidate_binding"][
        "relations"
    ] = tuple(relations)
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(contract, _golden_candidate())
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"

    contract = _candidate()
    relations = list(
        contract["genesis_cardinality"]["preassigned_attempt_candidate_binding"][
            "relations"
        ]
    )
    relations[1] = "bind work revision to selected null refs"
    contract["genesis_cardinality"]["preassigned_attempt_candidate_binding"][
        "relations"
    ] = tuple(relations)
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(contract, _golden_candidate())
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"

    vector = _golden_candidate()
    vector["safe_command"]["preassigned_semantic_attempt_ref"] = "different-attempt"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(_candidate(), vector)
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"

    vector = _golden_candidate()
    vector["persisted_rows"]["initialize_decision"][
        "preassigned_candidate_ref"
    ] = "different-candidate"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(_candidate(), vector)
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"

    vector = _golden_candidate()
    vector["persisted_rows"]["program_version_work_item"][
        "work_item_revision_ref"
    ] = "different-work-revision"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(_candidate(), vector)
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"

    vector = _golden_candidate()
    vector["persisted_rows"]["initialize_decision"][
        "selected_semantic_attempt_ref"
    ] = "selected-attempt"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(_candidate(), vector)
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"

    contract = _candidate()
    contract["genesis_cardinality"]["preassigned_attempt_candidate_binding"][
        "future_lineage_only"
    ] = "selected/current/created/authorized"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_preassigned_binding(contract, _golden_candidate())
    assert str(exc_info.value) == "C2B3A_PREASSIGNED_BINDING_INVALID"


def test_original_apply_outcome_and_quarantine_branch_are_exact() -> None:
    _assert_original_apply_outcome(EXPECTED_INITIALIZATION_CONTRACT)
    _assert_original_apply_outcome(_owner_contract())


def test_original_apply_outcome_mutants_u09_through_u14_are_rejected() -> None:
    candidate = _candidate()
    del candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "original_apply_error"
    ]
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_original_apply_outcome(candidate)
    assert str(exc_info.value) == "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID"

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "original_apply_error"
    ]["reason"] = "mutation_failed"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_original_apply_outcome(candidate)
    assert str(exc_info.value) == "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID"

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "original_apply_error"
    ]["context"] = "close failed: private detail"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_original_apply_outcome(candidate)
    assert str(exc_info.value) == "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID"

    candidate = _candidate()
    steps = list(
        candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
            "ordered_steps"
        ]
    )
    steps[5], steps[7] = steps[7], steps[5]
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "ordered_steps"
    ] = tuple(steps)
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_original_apply_outcome(candidate)
    assert str(exc_info.value) == "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID"

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "original_apply_error"
    ]["reason"] = "unresolved"
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_original_apply_outcome(candidate)
    assert str(exc_info.value) == "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID"

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "same_session_database_backed_resolver"
    ] = True
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_original_apply_outcome(candidate)
    assert str(exc_info.value) == "C2B3A_ORIGINAL_APPLY_OUTCOME_INVALID"


def test_process_control_close_interruption_contract_is_exact() -> None:
    close_not_proved_candidate = _candidate()["commit_uncertainty_cleanup_gate"][
        "close_not_proved"
    ]
    assert close_not_proved_candidate[
        "process_control_close_interruption_ordered_steps"
    ] == (
        "observe the exact process-control exception object from connection close",
        "retain the mutation slot",
        "retain the writer-authority lock",
        "transfer the uncertain raw connection into the private _WriterSessionResource",
        "publish the concrete session as commit-uncertain quarantined",
        "confirm same-session mutation and database-backed recovery remain forbidden",
        "confirm no operation lease, database open, BEGIN, or SQL can occur",
        "re-raise the identical process-control exception object",
    )
    process_control_candidate = close_not_proved_candidate[
        "process_control_exceptions"
    ]
    assert tuple(process_control_candidate) == (
        "KeyboardInterrupt",
        "SystemExit",
        "GeneratorExit",
    )
    assert process_control_candidate["KeyboardInterrupt"] == {
        "exception_identity_preserved": True,
        "connection_custody_transferred_before_propagation": True,
        "quarantine_published_before_propagation": True,
        "writer_lock_retained_before_propagation": True,
        "mutation_slot_retained_before_propagation": True,
        "same_session_database_recovery_allowed": False,
        "operation_lease_allowed_before_close_proof": False,
        "database_open_allowed_before_close_proof": False,
        "begin_allowed_before_close_proof": False,
        "sql_allowed_before_close_proof": False,
        "ordinary_store_error_conversion": False,
        "automatic_semantic_retry": False,
    }
    assert process_control_candidate["SystemExit"] == {
        "exception_identity_preserved": True,
        "connection_custody_transferred_before_propagation": True,
        "quarantine_published_before_propagation": True,
        "writer_lock_retained_before_propagation": True,
        "mutation_slot_retained_before_propagation": True,
        "same_session_database_recovery_allowed": False,
        "operation_lease_allowed_before_close_proof": False,
        "database_open_allowed_before_close_proof": False,
        "begin_allowed_before_close_proof": False,
        "sql_allowed_before_close_proof": False,
        "ordinary_store_error_conversion": False,
        "automatic_semantic_retry": False,
    }
    assert process_control_candidate["GeneratorExit"] == {
        "exception_identity_preserved": True,
        "connection_custody_transferred_before_propagation": True,
        "quarantine_published_before_propagation": True,
        "writer_lock_retained_before_propagation": True,
        "mutation_slot_retained_before_propagation": True,
        "same_session_database_recovery_allowed": False,
        "operation_lease_allowed_before_close_proof": False,
        "database_open_allowed_before_close_proof": False,
        "begin_allowed_before_close_proof": False,
        "sql_allowed_before_close_proof": False,
        "ordinary_store_error_conversion": False,
        "automatic_semantic_retry": False,
    }


def test_process_control_exception_graph_ledger_is_exact() -> None:
    expected_ledger = (
        {
            "branch_name": "KeyboardInterrupt",
            "propagation_form": "bare_reraise",
            "same_exception_object": True,
            "exact_type_preserved": True,
            "args_preserved": True,
            "system_exit_code_preserved_or_not_applicable": "not_applicable",
            "caught_traceback_tail_identity_preserved": True,
            "repair_owned_traceback_frame_delta": 0,
            "cause_before": None,
            "cause_after": None,
            "context_before": None,
            "context_after": None,
            "suppress_context_before": False,
            "suppress_context_after": False,
            "notes_before": "absent",
            "notes_after": "absent",
            "private_material_in_exception_graph": False,
            "automatic_semantic_retry": False,
        },
        {
            "branch_name": "SystemExit",
            "propagation_form": "bare_reraise",
            "same_exception_object": True,
            "exact_type_preserved": True,
            "args_preserved": True,
            "system_exit_code_preserved_or_not_applicable": "preserved",
            "caught_traceback_tail_identity_preserved": True,
            "repair_owned_traceback_frame_delta": 0,
            "cause_before": None,
            "cause_after": None,
            "context_before": None,
            "context_after": None,
            "suppress_context_before": False,
            "suppress_context_after": False,
            "notes_before": "absent",
            "notes_after": "absent",
            "private_material_in_exception_graph": False,
            "automatic_semantic_retry": False,
        },
        {
            "branch_name": "GeneratorExit",
            "propagation_form": "bare_reraise",
            "same_exception_object": True,
            "exact_type_preserved": True,
            "args_preserved": True,
            "system_exit_code_preserved_or_not_applicable": "not_applicable",
            "caught_traceback_tail_identity_preserved": True,
            "repair_owned_traceback_frame_delta": 0,
            "cause_before": None,
            "cause_after": None,
            "context_before": None,
            "context_after": None,
            "suppress_context_before": False,
            "suppress_context_after": False,
            "notes_before": "absent",
            "notes_after": "absent",
            "private_material_in_exception_graph": False,
            "automatic_semantic_retry": False,
        },
    )
    gate = _candidate()["commit_uncertainty_cleanup_gate"]
    assert gate["close_not_proved"][
        "process_control_exception_graph_ledger"
    ] == expected_ledger
    assert gate["process_control_exception_graph_privacy"] == {
        "forbidden_material": (
            "ordinary commit exception",
            "ordinary close exception",
            "raw SQLite exception",
            "connection",
            "cursor",
            "controller",
            "mutation-slot object",
            "writer-lock object",
            "quarantine object",
            "database path",
            "SQL",
            "parameters",
            "WorkSpec content",
            "private test sentinel",
        ),
        "forbidden_surfaces": (
            "exception args",
            "str or repr",
            "__cause__ graph",
            "__context__ graph",
            "__notes__",
            "formatted traceback",
            "C2B3-owned traceback-frame locals",
            "returned or persisted values",
            "logs or reports",
        ),
        "sole_permitted_outward_exception": "the identical process-control exception object",
    }


def test_bare_reraise_reference_model_distinguishes_named_reraise() -> None:
    bare = _bare_reraise_reference(
        KeyboardInterrupt("repair4-bare-reference")
    )
    named = _named_reraise_reference(
        KeyboardInterrupt("repair4-named-reference")
    )
    assert bare["same_exception_object"] is True
    assert bare["caught_traceback_tail_identity_preserved"] is True
    assert bare["repair_owned_traceback_frame_delta"] == 0
    assert bare["caught_signature"] == bare["propagated_signature"]
    assert bare["graph_before"] == (None, None, False, False, None)
    assert bare["graph_after"] == (None, None, False, False, None)
    assert bare["private_material_in_exception_graph"] is False
    assert named["same_exception_object"] is True
    assert named["caught_traceback_tail_identity_preserved"] is False
    assert named["repair_owned_traceback_frame_delta"] == 1
    assert named["caught_signature"] != named["propagated_signature"]


def test_keyboard_interrupt_close_fault_publishes_before_identical_propagation() -> None:
    reference_observation = _bare_reraise_reference(
        KeyboardInterrupt("repair4-keyboard-reference")
    )
    injected_exception = KeyboardInterrupt("repair4-keyboard")
    event_ledger: list[str] = []
    controller_connection_custody = True
    session_resource_connection_custody = False
    mutation_slot_retained = True
    writer_lock_retained = True
    quarantine_published = False
    same_session_mutation_allowed = False
    same_session_database_recovery_allowed = False
    operation_lease_count = 0
    database_open_count = 0
    begin_count = 0
    sql_count = 0
    automatic_semantic_retry_count = 0
    ordinary_store_error = None
    propagation_caught = False
    caught_traceback_tail = None
    caught_traceback_signature: tuple[tuple[int, int, str], ...] = ()
    caught_exception_graph = None

    try:
        try:
            raise injected_exception
        except KeyboardInterrupt as caught_exception:
            event_ledger.append("observe exact close exception")
            assert caught_exception is injected_exception
            caught_traceback_tail = caught_exception.__traceback__
            caught_traceback_signature = _traceback_signature(
                caught_traceback_tail
            )
            caught_exception_graph = _exception_graph_snapshot(
                caught_exception
            )
            event_ledger.append("retain mutation slot")
            assert mutation_slot_retained is True
            event_ledger.append("retain writer-authority lock")
            assert writer_lock_retained is True
            controller_connection_custody = False
            session_resource_connection_custody = True
            event_ledger.append("transfer connection custody")
            quarantine_published = True
            event_ledger.append("publish quarantine")
            event_ledger.append("forbid same-session mutation and recovery")
            assert same_session_mutation_allowed is False
            assert same_session_database_recovery_allowed is False
            event_ledger.append("forbid lease open begin and sql")
            assert (
                operation_lease_count,
                database_open_count,
                begin_count,
                sql_count,
            ) == (0, 0, 0, 0)
            event_ledger.append("re-raise identical exception")
            raise
    except KeyboardInterrupt as propagated_exception:
        propagation_caught = True
        propagated_traceback_signature = _traceback_signature(
            propagated_exception.__traceback__
        )
        assert propagated_exception is injected_exception
        assert type(propagated_exception) is KeyboardInterrupt
        assert propagated_exception.args == ("repair4-keyboard",)
        assert propagated_exception.__traceback__ is caught_traceback_tail
        assert propagated_traceback_signature == caught_traceback_signature
        assert tuple(
            item[1] for item in propagated_traceback_signature
        ) == tuple(item[1] for item in caught_traceback_signature)
        assert tuple(
            item[2] for item in propagated_traceback_signature
        ) == tuple(item[2] for item in caught_traceback_signature)
        assert propagated_traceback_signature[-1] == caught_traceback_signature[-1]
        assert len(propagated_traceback_signature) - len(
            caught_traceback_signature
        ) == 0
        assert caught_exception_graph == (None, None, False, False, None)
        assert _exception_graph_snapshot(propagated_exception) == (
            None,
            None,
            False,
            False,
            None,
        )
        assert (
            _process_control_exception_graph_contains_private_material(
                propagated_exception
            )
            is False
        )
        assert controller_connection_custody is False
        assert session_resource_connection_custody is True
        assert quarantine_published is True
        assert writer_lock_retained is True
        assert mutation_slot_retained is True
        assert ordinary_store_error is None
        assert automatic_semantic_retry_count == 0

    assert propagation_caught is True
    assert reference_observation["same_exception_object"] is True
    assert reference_observation[
        "caught_traceback_tail_identity_preserved"
    ] is True
    assert reference_observation["repair_owned_traceback_frame_delta"] == 0
    assert reference_observation["graph_before"] == (
        None,
        None,
        False,
        False,
        None,
    )
    assert reference_observation["graph_after"] == (
        None,
        None,
        False,
        False,
        None,
    )
    assert tuple(event_ledger) == (
        "observe exact close exception",
        "retain mutation slot",
        "retain writer-authority lock",
        "transfer connection custody",
        "publish quarantine",
        "forbid same-session mutation and recovery",
        "forbid lease open begin and sql",
        "re-raise identical exception",
    )


def test_system_exit_close_fault_publishes_before_identical_propagation() -> None:
    reference_observation = _bare_reraise_reference(SystemExit(43))
    injected_exception = SystemExit(41)
    event_ledger: list[str] = []
    controller_connection_custody = True
    session_resource_connection_custody = False
    mutation_slot_retained = True
    writer_lock_retained = True
    quarantine_published = False
    same_session_mutation_allowed = False
    same_session_database_recovery_allowed = False
    operation_lease_count = 0
    database_open_count = 0
    begin_count = 0
    sql_count = 0
    automatic_semantic_retry_count = 0
    ordinary_store_error = None
    propagation_caught = False
    caught_traceback_tail = None
    caught_traceback_signature: tuple[tuple[int, int, str], ...] = ()
    caught_exception_graph = None

    try:
        try:
            raise injected_exception
        except SystemExit as caught_exception:
            event_ledger.append("observe exact close exception")
            assert caught_exception is injected_exception
            caught_traceback_tail = caught_exception.__traceback__
            caught_traceback_signature = _traceback_signature(
                caught_traceback_tail
            )
            caught_exception_graph = _exception_graph_snapshot(
                caught_exception
            )
            event_ledger.append("retain mutation slot")
            assert mutation_slot_retained is True
            event_ledger.append("retain writer-authority lock")
            assert writer_lock_retained is True
            controller_connection_custody = False
            session_resource_connection_custody = True
            event_ledger.append("transfer connection custody")
            quarantine_published = True
            event_ledger.append("publish quarantine")
            event_ledger.append("forbid same-session mutation and recovery")
            assert same_session_mutation_allowed is False
            assert same_session_database_recovery_allowed is False
            event_ledger.append("forbid lease open begin and sql")
            assert (
                operation_lease_count,
                database_open_count,
                begin_count,
                sql_count,
            ) == (0, 0, 0, 0)
            event_ledger.append("re-raise identical exception")
            raise
    except SystemExit as propagated_exception:
        propagation_caught = True
        propagated_traceback_signature = _traceback_signature(
            propagated_exception.__traceback__
        )
        assert propagated_exception is injected_exception
        assert type(propagated_exception) is SystemExit
        assert propagated_exception.args == (41,)
        assert propagated_exception.code == 41
        assert propagated_exception.__traceback__ is caught_traceback_tail
        assert propagated_traceback_signature == caught_traceback_signature
        assert tuple(
            item[1] for item in propagated_traceback_signature
        ) == tuple(item[1] for item in caught_traceback_signature)
        assert tuple(
            item[2] for item in propagated_traceback_signature
        ) == tuple(item[2] for item in caught_traceback_signature)
        assert propagated_traceback_signature[-1] == caught_traceback_signature[-1]
        assert len(propagated_traceback_signature) - len(
            caught_traceback_signature
        ) == 0
        assert caught_exception_graph == (None, None, False, False, None)
        assert _exception_graph_snapshot(propagated_exception) == (
            None,
            None,
            False,
            False,
            None,
        )
        assert (
            _process_control_exception_graph_contains_private_material(
                propagated_exception
            )
            is False
        )
        assert controller_connection_custody is False
        assert session_resource_connection_custody is True
        assert quarantine_published is True
        assert writer_lock_retained is True
        assert mutation_slot_retained is True
        assert ordinary_store_error is None
        assert automatic_semantic_retry_count == 0

    assert propagation_caught is True
    assert reference_observation["same_exception_object"] is True
    assert reference_observation[
        "caught_traceback_tail_identity_preserved"
    ] is True
    assert reference_observation["repair_owned_traceback_frame_delta"] == 0
    assert reference_observation["graph_before"] == (
        None,
        None,
        False,
        False,
        None,
    )
    assert reference_observation["graph_after"] == (
        None,
        None,
        False,
        False,
        None,
    )
    assert tuple(event_ledger) == (
        "observe exact close exception",
        "retain mutation slot",
        "retain writer-authority lock",
        "transfer connection custody",
        "publish quarantine",
        "forbid same-session mutation and recovery",
        "forbid lease open begin and sql",
        "re-raise identical exception",
    )


def test_generator_exit_close_fault_publishes_before_identical_propagation() -> None:
    reference_observation = _bare_reraise_reference(
        GeneratorExit("repair4-generator-reference")
    )
    injected_exception = GeneratorExit("repair4-generator")
    event_ledger: list[str] = []
    controller_connection_custody = True
    session_resource_connection_custody = False
    mutation_slot_retained = True
    writer_lock_retained = True
    quarantine_published = False
    same_session_mutation_allowed = False
    same_session_database_recovery_allowed = False
    operation_lease_count = 0
    database_open_count = 0
    begin_count = 0
    sql_count = 0
    automatic_semantic_retry_count = 0
    ordinary_store_error = None
    propagation_caught = False
    caught_traceback_tail = None
    caught_traceback_signature: tuple[tuple[int, int, str], ...] = ()
    caught_exception_graph = None

    try:
        try:
            raise injected_exception
        except GeneratorExit as caught_exception:
            event_ledger.append("observe exact close exception")
            assert caught_exception is injected_exception
            caught_traceback_tail = caught_exception.__traceback__
            caught_traceback_signature = _traceback_signature(
                caught_traceback_tail
            )
            caught_exception_graph = _exception_graph_snapshot(
                caught_exception
            )
            event_ledger.append("retain mutation slot")
            assert mutation_slot_retained is True
            event_ledger.append("retain writer-authority lock")
            assert writer_lock_retained is True
            controller_connection_custody = False
            session_resource_connection_custody = True
            event_ledger.append("transfer connection custody")
            quarantine_published = True
            event_ledger.append("publish quarantine")
            event_ledger.append("forbid same-session mutation and recovery")
            assert same_session_mutation_allowed is False
            assert same_session_database_recovery_allowed is False
            event_ledger.append("forbid lease open begin and sql")
            assert (
                operation_lease_count,
                database_open_count,
                begin_count,
                sql_count,
            ) == (0, 0, 0, 0)
            event_ledger.append("re-raise identical exception")
            raise
    except GeneratorExit as propagated_exception:
        propagation_caught = True
        propagated_traceback_signature = _traceback_signature(
            propagated_exception.__traceback__
        )
        assert propagated_exception is injected_exception
        assert type(propagated_exception) is GeneratorExit
        assert propagated_exception.args == ("repair4-generator",)
        assert propagated_exception.__traceback__ is caught_traceback_tail
        assert propagated_traceback_signature == caught_traceback_signature
        assert tuple(
            item[1] for item in propagated_traceback_signature
        ) == tuple(item[1] for item in caught_traceback_signature)
        assert tuple(
            item[2] for item in propagated_traceback_signature
        ) == tuple(item[2] for item in caught_traceback_signature)
        assert propagated_traceback_signature[-1] == caught_traceback_signature[-1]
        assert len(propagated_traceback_signature) - len(
            caught_traceback_signature
        ) == 0
        assert caught_exception_graph == (None, None, False, False, None)
        assert _exception_graph_snapshot(propagated_exception) == (
            None,
            None,
            False,
            False,
            None,
        )
        assert (
            _process_control_exception_graph_contains_private_material(
                propagated_exception
            )
            is False
        )
        assert controller_connection_custody is False
        assert session_resource_connection_custody is True
        assert quarantine_published is True
        assert writer_lock_retained is True
        assert mutation_slot_retained is True
        assert ordinary_store_error is None
        assert automatic_semantic_retry_count == 0

    assert propagation_caught is True
    assert reference_observation["same_exception_object"] is True
    assert reference_observation[
        "caught_traceback_tail_identity_preserved"
    ] is True
    assert reference_observation["repair_owned_traceback_frame_delta"] == 0
    assert reference_observation["graph_before"] == (
        None,
        None,
        False,
        False,
        None,
    )
    assert reference_observation["graph_after"] == (
        None,
        None,
        False,
        False,
        None,
    )
    assert tuple(event_ledger) == (
        "observe exact close exception",
        "retain mutation slot",
        "retain writer-authority lock",
        "transfer connection custody",
        "publish quarantine",
        "forbid same-session mutation and recovery",
        "forbid lease open begin and sql",
        "re-raise identical exception",
    )


def test_future_c2b3b_twenty_four_path_scope_is_exact() -> None:
    _assert_future_c2b3b_scope(EXPECTED_INITIALIZATION_CONTRACT)
    _assert_future_c2b3b_scope(_owner_contract())


def test_future_c2b3b_scope_mutants_s01_through_s07_are_rejected() -> None:
    for omitted in (
        "src/ge_nwp_coordinator/sqlite_writer_session.py",
        "src/ge_nwp_coordinator/sqlite_transition_transaction.py",
        "src/ge_nwp_coordinator/sqlite_connection.py",
    ):
        candidate = _candidate()
        scope = candidate["future_c2b3b_maximum_path_scope"]
        scope["production"] = tuple(
            path for path in scope["production"] if path != omitted
        )
        with pytest.raises(_ContractViolation) as exc_info:
            _assert_future_c2b3b_scope(candidate)
        assert str(exc_info.value) == "C2B3A_FUTURE_SCOPE_INVALID"

    candidate = _candidate()
    candidate["future_c2b3b_maximum_path_scope"]["maximum_paths"] = 23
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_future_c2b3b_scope(candidate)
    assert str(exc_info.value) == "C2B3A_FUTURE_SCOPE_INVALID"

    candidate = _candidate()
    scope = candidate["future_c2b3b_maximum_path_scope"]
    scope["tests"] += ("tests/twenty_fifth_path.py",)
    scope["counts"]["tests"] = 11
    scope["counts"]["total"] = 25
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_future_c2b3b_scope(candidate)
    assert str(exc_info.value) == "C2B3A_FUTURE_SCOPE_INVALID"

    candidate = _candidate()
    responsibilities = candidate["future_c2b3b_maximum_path_scope"][
        "production_responsibilities"
    ]
    responsibilities["src/ge_nwp_coordinator/sqlite_writer_session.py"] += (
        "StateStore quarantine or public WriterSession quarantine method",
    )
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_future_c2b3b_scope(candidate)
    assert str(exc_info.value) == "C2B3A_FUTURE_SCOPE_INVALID"

    candidate = _candidate()
    responsibilities = candidate["future_c2b3b_maximum_path_scope"][
        "production_responsibilities"
    ]
    connection_path = "src/ge_nwp_coordinator/sqlite_connection.py"
    responsibilities[connection_path] = tuple(
        item
        for item in responsibilities[connection_path]
        if not item.startswith("cross-thread close")
    )
    with pytest.raises(_ContractViolation) as exc_info:
        _assert_future_c2b3b_scope(candidate)
    assert str(exc_info.value) == "C2B3A_FUTURE_SCOPE_INVALID"


def test_commit_uncertainty_cleanup_gate_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_attempt_precedes"] = (
        "clearing controller connection custody",
    )
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "raw_connection_custody"
    ] = "suppressed close failure and cleared custody"
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "same_session_database_backed_resolver"
    ] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "same_session_resolver_disposition"
    ] = "open SQLite, BEGIN, then classify unresolved"
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "definitely_not_committed"
    ] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["close_not_proved"][
        "automatic_semantic_retry"
    ] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["caller_authored_clearance"] = True
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")

    candidate = _candidate()
    candidate["commit_uncertainty_cleanup_gate"]["raw_connection_owner_before_close"] = (
        "outside controller and session-resource custody"
    )
    _expect_violation(candidate, "C2B3A_RECOVERY_ADMISSION_INVALID")


def test_stop_conflict_and_receipt_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    precedence = list(candidate["conflict_precedence"]["after_writer_fencing"])
    precedence[0], precedence[3] = precedence[3], precedence[0]
    candidate["conflict_precedence"]["after_writer_fencing"] = tuple(precedence)
    _expect_violation(candidate, "C2B3A_CONFLICT_PRECEDENCE_INVALID")

    candidate = _candidate()
    candidate["conflict_precedence"]["program_head_conflict"] = (
        "genesis collision classification"
    )
    _expect_violation(candidate, "C2B3A_CONFLICT_PRECEDENCE_INVALID")

    candidate = _candidate()
    precedence = list(candidate["conflict_precedence"]["after_writer_fencing"])
    precedence[3], precedence[4] = precedence[4], precedence[3]
    candidate["conflict_precedence"]["after_writer_fencing"] = tuple(precedence)
    _expect_violation(candidate, "C2B3A_CONFLICT_PRECEDENCE_INVALID")

    candidate = _candidate()
    candidate["conflict_precedence"]["failed_fresh_operation_creates_receipt"] = True
    _expect_violation(candidate, "C2B3A_CONFLICT_PRECEDENCE_INVALID")

    candidate = _candidate()
    candidate["conflict_precedence"]["semantic_identity_conflict_visibility"] = "public"
    _expect_violation(candidate, "C2B3A_CONFLICT_PRECEDENCE_INVALID")

    candidate = _candidate()
    candidate["mutation_receipt"]["failed_fresh_receipt"] = True
    _expect_violation(candidate, "C2B3A_RECEIPT_INVALID")


def test_private_conflict_and_recovery_outcome_owners_are_closed() -> None:
    candidate = _candidate()
    candidate["private_outcome_ownership"]["conflict_reason"]["values"] = candidate[
        "private_outcome_ownership"
    ]["conflict_reason"]["values"][:-1]
    _expect_violation(candidate, "C2B3A_OUTCOME_OWNERSHIP_INVALID")

    candidate = _candidate()
    candidate["private_outcome_ownership"]["conflict_reason"]["values"] += (
        "fifth_conflict",
    )
    _expect_violation(candidate, "C2B3A_OUTCOME_OWNERSHIP_INVALID")

    candidate = _candidate()
    candidate["private_outcome_ownership"]["public_surfaces_unchanged"] = tuple(
        surface
        for surface in candidate["private_outcome_ownership"][
            "public_surfaces_unchanged"
        ]
        if surface != "models.APPLY_CONFLICT_REASONS"
    )
    _expect_violation(candidate, "C2B3A_OUTCOME_OWNERSHIP_INVALID")

    candidate = _candidate()
    candidate["private_outcome_ownership"]["public_surfaces_unchanged"] = tuple(
        surface
        for surface in candidate["private_outcome_ownership"][
            "public_surfaces_unchanged"
        ]
        if surface != "sqlite_errors"
    )
    _expect_violation(candidate, "C2B3A_OUTCOME_OWNERSHIP_INVALID")

    candidate = _candidate()
    candidate["private_outcome_ownership"]["recovery_disposition"][
        "values"
    ] = ("committed_exact", "definitely_not_committed")
    _expect_violation(candidate, "C2B3A_OUTCOME_OWNERSHIP_INVALID")

    candidate = _candidate()
    candidate["private_outcome_ownership"]["recovery_disposition"]["values"] += (
        "fourth_disposition",
    )
    _expect_violation(candidate, "C2B3A_OUTCOME_OWNERSHIP_INVALID")

    candidate = _candidate()
    candidate["commit_outcome_recovery"]["disposition_owner"] = "unspecified"
    _expect_violation(candidate, "C2B3A_RECOVERY_INVALID")

    candidate = _candidate()
    candidate["private_outcome_ownership"]["package_root_export"] = True
    _expect_violation(candidate, "C2B3A_OUTCOME_OWNERSHIP_INVALID")


def test_privacy_and_custody_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    destinations = candidate["privacy_and_traceback"][
        "complete_work_spec_forbidden_destinations"
    ]
    candidate["privacy_and_traceback"][
        "complete_work_spec_forbidden_destinations"
    ] = tuple(item for item in destinations if item != "SQLite")
    _expect_violation(candidate, "C2B3A_PRIVACY_INVALID")

    candidate = _candidate()
    candidate["safe_command"]["contains_complete_work_spec"] = True
    _expect_violation(candidate, "C2B3A_SAFE_COMMAND_INVALID")

    for destination in ("receipt", "result", "resolver input"):
        candidate = _candidate()
        destinations = candidate["privacy_and_traceback"][
            "complete_work_spec_forbidden_destinations"
        ]
        candidate["privacy_and_traceback"][
            "complete_work_spec_forbidden_destinations"
        ] = tuple(item for item in destinations if item != destination)
        _expect_violation(candidate, "C2B3A_PRIVACY_INVALID")

    for custody_source in ("chat", "Bridge", "reports"):
        candidate = _candidate()
        sources = candidate["privacy_and_traceback"]["forbidden_custody_sources"]
        candidate["privacy_and_traceback"]["forbidden_custody_sources"] = tuple(
            item for item in sources if item != custody_source
        )
        _expect_violation(candidate, "C2B3A_PRIVACY_INVALID")

    candidate = _candidate()
    candidate["sensitive_ingress"]["restart_safe_retrieval"] = True
    _expect_violation(candidate, "C2B3A_SENSITIVE_INGRESS_INVALID")

    candidate = _candidate()
    candidate["privacy_and_traceback"]["transaction_controller_receives_work_spec"] = True
    _expect_violation(candidate, "C2B3A_PRIVACY_INVALID")


def test_later_author_effect_counterfactuals_are_rejected() -> None:
    candidate = _candidate()
    candidate["later_author_effect_owner_decisions"]["authority_evaluation"][
        "authority_state"
    ] = "verified"
    _expect_violation(candidate, "C2B3A_LATER_AUTHOR_BOUNDARY_INVALID")

    candidate = _candidate()
    candidate["later_author_effect_owner_decisions"]["authority_evaluation"][
        "semantic_attempt_ref"
    ] = "attempt-ref"
    _expect_violation(candidate, "C2B3A_LATER_AUTHOR_BOUNDARY_INVALID")

    candidate = _candidate()
    candidate["later_author_effect_owner_decisions"][
        "direct_local_bootstrap_selected"
    ] = True
    _expect_violation(candidate, "C2B3A_LATER_AUTHOR_BOUNDARY_INVALID")

    candidate = _candidate()
    candidate["later_author_effect_owner_decisions"][
        "ES_invocation_or_compatibility_claim"
    ] = True
    _expect_violation(candidate, "C2B3A_LATER_AUTHOR_BOUNDARY_INVALID")

    candidate = _candidate()
    candidate["later_author_effect_owner_decisions"]["requirement_provenance"][
        "raw_digest_only_input"
    ] = True
    _expect_violation(candidate, "C2B3A_LATER_AUTHOR_BOUNDARY_INVALID")

    candidate = _candidate()
    candidate["later_author_effect_owner_decisions"]["source_implemented"] = True
    _expect_violation(candidate, "C2B3A_LATER_AUTHOR_BOUNDARY_INVALID")


def test_nonimplementation_surface_is_closed() -> None:
    for key in (
        "program_initialization_source",
        "private_writer_session_methods",
        "sqlite_insert_or_update_execution",
        "mutation_receipt_persistence",
        "production_reader_integration",
        "public_C2B_API",
        "StateStore_widening",
        "WriterSession_public_surface_widening",
        "schema_change",
        "migration_0003_creation",
        "external_IO",
    ):
        candidate = _candidate()
        candidate["nonimplementation"][key] = True
        _expect_violation(candidate, "C2B3A_NONIMPLEMENTATION_INVALID")
