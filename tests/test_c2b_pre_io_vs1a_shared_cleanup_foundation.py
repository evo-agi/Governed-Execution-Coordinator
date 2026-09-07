from __future__ import annotations

import ast
import dis
import gc
import hashlib
import importlib.util
import inspect
import os
from pathlib import Path
import select
import sqlite3
import sys
import threading
import textwrap
import traceback
import types
import weakref

import pytest

from b3_coherent_transition_fixture import (
    global_stop_event_count_for_test,
    make_coherent_transition_fixture_for_test,
    transition_event_count_for_test,
)
import ge_nwp_coordinator.sqlite_connection as connection_module
import ge_nwp_coordinator.sqlite_transition_event_readers as transition_reader_module
import ge_nwp_coordinator.sqlite_transition_select_support as select_support_module
from ge_nwp_coordinator.sqlite_errors import (
    SQLiteMutationStoreError,
    SQLiteMutationStoreErrorCode,
)
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import initialize_database
import ge_nwp_coordinator.sqlite_transition_transaction as transaction_module
import ge_nwp_coordinator.sqlite_writer_session as writer_module
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.state_store import (
    CommittedGlobalStopUpdate,
    CommittedTransition,
    WriterSessionError,
)
import test_b4b_private_atomic_global_stop_persistence as global_stop_tests
import test_b3c4b_private_atomic_transition_persistence as transition_tests
import test_b3c1b_rollback_only_writer_fencing as fencing_tests


ROOT = Path(__file__).resolve().parents[1]
CONNECTION_PATH = ROOT / "src/ge_nwp_coordinator/sqlite_connection.py"
TRANSACTION_PATH = ROOT / "src/ge_nwp_coordinator/sqlite_transition_transaction.py"
WRITER_PATH = ROOT / "src/ge_nwp_coordinator/sqlite_writer_session.py"
LOCK_PATH = ROOT / "src/ge_nwp_coordinator/state_authority_lock.py"
CONTRACT_TEST_PATH = ROOT / "tests/test_b3c4c_prerequisite_contract.py"
DURABLE_DOC_PATH = ROOT / ".docs/c2b-durable-development-state.md"
LOCK_SHA256 = "15172ffabe9ff2ad023f283c6e74fd250dd7a661870e5b93ee3b9a2f8873c3fa"
SECTIONS_1_TO_36_SHA256 = "66e481530a34984e89f9a3808cb2c817170d5e4a6374d99a6e6e045f47637cb3"
PROCESS_CONTROL_KINDS = (
    "keyboard-interrupt",
    "system-exit-73",
    "generator-exit",
)

# This literal tuple is the sole focused-selector inventory.  Reports compute its
# size from the tuple itself; no document repeats a mutable total.
FOCUSED_REPAIR_NODE_IDS = (
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[after-operation-admission-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[after-operation-admission-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[first-caller-envelope-opcode-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[first-caller-envelope-opcode-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[compiler-normal-with-cleanup-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[compiler-normal-with-cleanup-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[compiler-exceptional-with-cleanup-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[compiler-exceptional-with-cleanup-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[operation-exit-first-opcode-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[operation-exit-first-opcode-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[operation-close-call-setup-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[operation-close-call-setup-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[operation-close-first-opcode-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[operation-close-first-opcode-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[operation-owner-pid-check-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[operation-owner-pid-check-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[first-phase-one-action-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[first-phase-one-action-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[poison-publication-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[poison-publication-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[detailed-cleanup-local-failure-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[detailed-cleanup-local-failure-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[post-poison-normal-lease-close-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[post-poison-normal-lease-close-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[immediately-before-final-assignment-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[immediately-before-final-assignment-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[immediately-after-final-assignment-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[immediately-after-final-assignment-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[first-final-publication-notification-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_retained_lease_exit_envelope_matrix[first-final-publication-notification-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_ordinary_invalid_preflight_process_control_context_graph_is_sanitized[transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_ordinary_invalid_preflight_process_control_context_graph_is_sanitized[global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_stabilization_helper_failures_occur_only_after_direct_poison[state-authority-first-attempt]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_stabilization_helper_failures_occur_only_after_direct_poison[state-authority-both-attempts]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_stabilization_helper_failures_occur_only_after_direct_poison[state-records-first-attempt]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_stabilization_helper_failures_occur_only_after_direct_poison[state-records-both-attempts]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_stabilization_helper_failures_occur_only_after_direct_poison[operation-policy-first-attempt]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_stabilization_helper_failures_occur_only_after_direct_poison[operation-policy-both-attempts]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_stabilization_notification_failure_remains_poisoned_and_private[transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_stabilization_notification_failure_remains_poisoned_and_private[global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exact_invocation_stabilizer_classifies_only_current_resource_records",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_closed_variants_direct_construction_accepts_every_governed_variant",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_controller_resolution_cleanup_required_is_stabilizer_cleanup_owned",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_invocation_correlation_invalid_wrong_unrepresented_and_duplicate_do_not_select_another_operation",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_invocation_correlation_cleanup_owned_is_exact_and_fail_closed",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exact_record_post_poison_consistency_failure_never_reenables_admission[owner-pid]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exact_record_post_poison_consistency_failure_never_reenables_admission[lifecycle-epoch]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_invocation_correlation_is_private_immutable_non_authoritative_identity",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_mutation_usability_exit_boundaries_remain_fail_closed_without_poison[unbound-compiler-cleanup]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_mutation_usability_exit_boundaries_remain_fail_closed_without_poison[operation-exit-first-opcode]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_mutation_usability_exit_boundaries_remain_fail_closed_without_poison[operation-close-call-setup]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_mutation_usability_exit_boundaries_remain_fail_closed_without_poison[operation-close-first-opcode]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_competing_admission_before_poison_is_governed_after_linearization",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_fork_child_poison_sees_invalidated_copy_and_cannot_retire_parent",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_operation_retirement_entry_process_control_is_cleanup_safe[keyboard-interrupt]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_operation_retirement_entry_process_control_is_cleanup_safe[system-exit-73]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_operation_retirement_entry_process_control_is_cleanup_safe[generator-exit]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_direct_live_finalizer_process_control_remains_fail_closed[keyboard-interrupt]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_direct_live_finalizer_process_control_remains_fail_closed[system-exit-73]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_direct_live_finalizer_process_control_remains_fail_closed[generator-exit]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_local_stabilization_failure_cannot_replace_governing_process_control_or_restore_active",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_operation_retirement_post_linearization_durable_response_loss_uses_replay_without_duplicate_effect[transition-keyboard-interrupt]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_operation_retirement_post_linearization_durable_response_loss_uses_replay_without_duplicate_effect[transition-system-exit-73]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_operation_retirement_post_linearization_durable_response_loss_uses_replay_without_duplicate_effect[transition-generator-exit]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_operation_retirement_post_linearization_durable_response_loss_uses_replay_without_duplicate_effect[global-stop-keyboard-interrupt]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_operation_retirement_post_linearization_durable_response_loss_uses_replay_without_duplicate_effect[global-stop-system-exit-73]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_operation_retirement_post_linearization_durable_response_loss_uses_replay_without_duplicate_effect[global-stop-generator-exit]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_underlying_commit_process_control_scrubs_coordinator_traceback_and_replays_once[keyboard-interrupt-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_underlying_commit_process_control_scrubs_coordinator_traceback_and_replays_once[keyboard-interrupt-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_underlying_commit_process_control_scrubs_coordinator_traceback_and_replays_once[system-exit-73-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_underlying_commit_process_control_scrubs_coordinator_traceback_and_replays_once[system-exit-73-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_underlying_commit_process_control_scrubs_coordinator_traceback_and_replays_once[generator-exit-transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_underlying_commit_process_control_scrubs_coordinator_traceback_and_replays_once[generator-exit-global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_transition_safe_error_traceback_direct_locals_and_builtin_containers_exclude_captured_sensitive_authority",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_genuine_bound_public_guard_safe_error_has_complete_outward_privacy[transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_genuine_bound_public_guard_safe_error_has_complete_outward_privacy[global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_genuine_bound_safe_error_severs_active_caller_context_without_mutating_prior[transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_genuine_bound_safe_error_severs_active_caller_context_without_mutating_prior[global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_untrusted_context_bearing_safe_error_is_not_admitted_to_trusted_severance[transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_untrusted_context_bearing_safe_error_is_not_admitted_to_trusted_severance[global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_safe_failure_disposition_preserves_one_exact_content_free_error_object",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_safe_failure_disposition_rejects_subclassed_or_content_bearing_errors",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exception_traceback_sanitizer_is_cycle_bounded_and_identity_preserving",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_hostile_exception_subclass_descriptors_are_not_invoked[__traceback__]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_hostile_exception_subclass_descriptors_are_not_invoked[__cause__]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_hostile_exception_subclass_descriptors_are_not_invoked[__context__]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_hostile_exception_subclass_descriptors_are_not_invoked[args]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_hostile_exception_subclass_descriptors_are_not_invoked[__dict__]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_hostile_exception_subclass_descriptors_are_not_invoked[__notes__]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_hostile_exception_subclass_descriptors_are_not_invoked[exceptions]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_one_ordinary_sanitizer_core_failure_is_bounded_and_retried[before-root-clearing]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_one_ordinary_sanitizer_core_failure_is_bounded_and_retried[after-root-clearing-before-context]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_one_ordinary_sanitizer_core_failure_is_bounded_and_retried[during-cause-traversal]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_one_ordinary_sanitizer_core_failure_is_bounded_and_retried[during-context-traversal]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_one_ordinary_sanitizer_core_failure_is_bounded_and_retried[during-group-child-traversal]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_one_ordinary_sanitizer_core_failure_is_bounded_and_retried[during-exact-container-traversal]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_one_ordinary_failure_immediately_before_sanitizer_core_return_is_bounded",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_primary_sanitizer_call_boundary_failure_preserves_process_control[transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_public_primary_sanitizer_call_boundary_failure_preserves_process_control[global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_genuine_bound_safe_error_primary_sanitizer_failure_preserves_exact_error[transition]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_genuine_bound_safe_error_primary_sanitizer_failure_preserves_exact_error[global-stop]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_governing_process_control_bypasses_safe_failure_disposition_by_identity",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exit_poison_compiled_source_mutant_is_causally_rejected[01_poison_after_state_operation_records_call]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exit_poison_compiled_source_mutant_is_causally_rejected[02_poison_after_operation_blocks_admission_call]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exit_poison_compiled_source_mutant_is_causally_rejected[03_controller_cleanup_resolution_classified_incomplete]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exit_poison_compiled_source_mutant_is_causally_rejected[04_only_root_traceback_cleared]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exit_poison_compiled_source_mutant_is_causally_rejected[05_context_traversal_removed_from_sanitizer]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exit_poison_compiled_source_mutant_is_causally_rejected[06_safe_error_outer_scrub_removed]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exit_poison_compiled_source_mutant_is_causally_rejected[07_bound_guard_correlation_replaced_by_nonmethod_path]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exit_poison_compiled_source_mutant_is_causally_rejected[08_lifecycle_epoch_property_before_poison]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exit_poison_compiled_source_mutant_is_causally_rejected[09_state_authority_call_before_poison]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exit_poison_compiled_source_mutant_is_causally_rejected[10_object_getattribute_exception_fields]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exit_poison_compiled_source_mutant_is_causally_rejected[11_sanitizer_fallback_retry_removed]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exit_poison_compiled_source_mutant_is_causally_rejected[12_sanitizer_failure_escapes_boundary]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_exit_poison_compiled_source_mutant_is_causally_rejected[13_trusted_safe_error_context_severance_removed]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_compiled_writer_source_mutant_is_killed[01_resource_explicit_phase_gate_removed]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_compiled_writer_source_mutant_is_killed[02_unsuccessful_detach_result_accepted]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_compiled_writer_source_mutant_is_killed[03_handle_binding_used_instead_of_resource_record]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_compiled_writer_source_mutant_is_killed[04_lease_loss_removes_record_as_normal_completion]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_vs1a_secondary_identity_ast_guard[resource-identity-comparisons]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_vs1a_secondary_identity_ast_guard[no-process-global-identity-registry]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_vs1a_secondary_identity_ast_guard[opaque-identity-surface]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_vs1a_secondary_identity_ast_guard[caller-envelope-bytecode]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_vs1a_secondary_identity_ast_guard[pre-admission-token-correlation-and-privacy]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_vs1a_secondary_identity_ast_guard[poison-publication-order]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_vs1a_secondary_identity_ast_guard[sanitizer-base-descriptor-boundary]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_vs1a_secondary_identity_ast_guard[poison-readers-and-monotonicity]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_vs1a_secondary_identity_ast_guard[mutation-usability-path-separation]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_vs1a_authenticity_counterfactual_is_causally_rejected[04_direct_live_finalizer_publishes_active]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_vs1a_authenticity_counterfactual_is_causally_rejected[05_direct_live_finalizer_removes_handle]",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_selected_source_removes_every_rejected_mechanism",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_preservation_sections_1_through_36_are_byte_exact",
    "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_focused_repair_node_inventory_is_literal_exact_and_unique",
)


def test_focused_repair_node_inventory_is_literal_exact_and_unique() -> None:
    assert type(FOCUSED_REPAIR_NODE_IDS) is tuple
    assert len(FOCUSED_REPAIR_NODE_IDS) == len(set(FOCUSED_REPAIR_NODE_IDS))
    assert all(
        type(node_id) is str
        and node_id.startswith(
            "tests/test_c2b_pre_io_vs1a_shared_cleanup_foundation.py::test_"
        )
        and not any(character.isspace() for character in node_id)
        for node_id in FOCUSED_REPAIR_NODE_IDS
    )
    module_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    inventory_assignment = next(
        node
        for node in module_tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "FOCUSED_REPAIR_NODE_IDS"
            for target in node.targets
        )
    )
    assert isinstance(inventory_assignment.value, ast.Tuple)
    assert all(
        isinstance(element, ast.Constant) and type(element.value) is str
        for element in inventory_assignment.value.elts
    )

@pytest.fixture(autouse=True)
def _collect_sqlite_resources_after_test() -> object:
    yield
    gc.collect()


def _location(tmp_path: Path) -> CoordinatorStateLocation:
    return CoordinatorStateLocation.from_trusted_root(tmp_path / "state")


def _new_test_resource_identity() -> object:
    return connection_module._new_writer_session_resource_identity()


def _builtin_container_reaches_identity(
    value: object,
    prohibited: tuple[object, ...],
) -> bool:
    pending = [value]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if any(current is item for item in prohibited):
            return True
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        if type(current) is dict:
            pending.extend(current.keys())
            pending.extend(current.values())
        elif type(current) in (tuple, list, set, frozenset):
            pending.extend(current)
    return False


def _builtin_container_reaches_exact_value(
    value: object,
    prohibited: tuple[object, ...],
) -> bool:
    """Traverse only exact built-in containers and compare exact built-in values."""

    pending = [value]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if type(current) in (str, bytes, tuple):
            for forbidden in prohibited:
                if type(current) is type(forbidden) and current == forbidden:
                    return True
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        if type(current) is dict:
            pending.extend(current.keys())
            pending.extend(current.values())
        elif type(current) in (tuple, list, set, frozenset):
            pending.extend(current)
    return False


def _coordinator_frames(error: BaseException) -> list[object]:
    frames: list[object] = []
    current = error.__traceback__
    package_root = str(ROOT / "src/ge_nwp_coordinator")
    while current is not None:
        if current.tb_frame.f_code.co_filename.startswith(package_root):
            frames.append(current.tb_frame)
        current = current.tb_next
    return frames


def _exception_graph(root: BaseException) -> tuple[BaseException, ...]:
    """Return the cycle-bounded exception graph through exact built-in containers."""

    pending: list[object] = [root]
    seen: set[int] = set()
    exceptions: list[BaseException] = []
    while pending:
        current = pending.pop()
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        if isinstance(current, BaseException):
            exceptions.append(current)
            pending.extend(
                (
                    current.__cause__,
                    current.__context__,
                    current.args,
                    current.__dict__,
                    getattr(current, "__notes__", None),
                    (
                        current.exceptions
                        if isinstance(current, BaseExceptionGroup)
                        else None
                    ),
                )
            )
        elif type(current) is dict:
            pending.extend(current.keys())
            pending.extend(current.values())
        elif type(current) in (tuple, list, set, frozenset):
            pending.extend(current)
    return tuple(exceptions)


_TEST_BASE_EXCEPTION_TRACEBACK_DESCRIPTOR = BaseException.__dict__["__traceback__"]
_TEST_BASE_EXCEPTION_CAUSE_DESCRIPTOR = BaseException.__dict__["__cause__"]
_TEST_BASE_EXCEPTION_CONTEXT_DESCRIPTOR = BaseException.__dict__["__context__"]
_TEST_BASE_EXCEPTION_ARGS_DESCRIPTOR = BaseException.__dict__["args"]
_TEST_BASE_EXCEPTION_DICTIONARY_DESCRIPTOR = BaseException.__dict__["__dict__"]
_TEST_BASE_EXCEPTION_GROUP_CHILDREN_DESCRIPTOR = BaseExceptionGroup.__dict__["exceptions"]
_TEST_BASE_EXCEPTION_DESCRIPTOR_GET = type(
    _TEST_BASE_EXCEPTION_TRACEBACK_DESCRIPTOR
).__dict__["__get__"]
_TEST_BASE_EXCEPTION_GROUP_DESCRIPTOR_GET = type(
    _TEST_BASE_EXCEPTION_GROUP_CHILDREN_DESCRIPTOR
).__dict__["__get__"]


def _base_exception_field(error: BaseException, descriptor: object) -> object:
    return _TEST_BASE_EXCEPTION_DESCRIPTOR_GET(
        descriptor,
        error,
        BaseException,
    )


def _base_exception_group_children(error: BaseExceptionGroup) -> tuple[object, ...]:
    children = _TEST_BASE_EXCEPTION_GROUP_DESCRIPTOR_GET(
        _TEST_BASE_EXCEPTION_GROUP_CHILDREN_DESCRIPTOR,
        error,
        BaseExceptionGroup,
    )
    assert type(children) is tuple
    return children


def _coordinator_frames_from_base_exception_storage(
    error: BaseException,
) -> list[object]:
    frames: list[object] = []
    current = _base_exception_field(
        error,
        _TEST_BASE_EXCEPTION_TRACEBACK_DESCRIPTOR,
    )
    package_root = str(ROOT / "src/ge_nwp_coordinator")
    while current is not None:
        if current.tb_frame.f_code.co_filename.startswith(package_root):
            frames.append(current.tb_frame)
        current = current.tb_next
    return frames


def _supported_exception_graph_without_subclass_dispatch(
    root: BaseException,
) -> tuple[BaseException, ...]:
    pending: list[object] = [root]
    seen: set[int] = set()
    exceptions: list[BaseException] = []
    while pending:
        current = list.pop(pending)
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        if isinstance(current, BaseException):
            exceptions.append(current)
            list.extend(
                pending,
                (
                    _base_exception_field(
                        current,
                        _TEST_BASE_EXCEPTION_CAUSE_DESCRIPTOR,
                    ),
                    _base_exception_field(
                        current,
                        _TEST_BASE_EXCEPTION_CONTEXT_DESCRIPTOR,
                    ),
                    _base_exception_field(
                        current,
                        _TEST_BASE_EXCEPTION_ARGS_DESCRIPTOR,
                    ),
                    _base_exception_field(
                        current,
                        _TEST_BASE_EXCEPTION_DICTIONARY_DESCRIPTOR,
                    ),
                    (
                        _base_exception_group_children(current)
                        if isinstance(current, BaseExceptionGroup)
                        else None
                    ),
                ),
            )
        elif type(current) is dict:
            list.extend(pending, dict.keys(current))
            list.extend(pending, dict.values(current))
        elif type(current) in (tuple, list, set, frozenset):
            list.extend(pending, current)
    return tuple(exceptions)


def _assert_exception_graph_has_no_coordinator_traceback(
    root: BaseException,
) -> None:
    assert all(_coordinator_frames(error) == [] for error in _exception_graph(root))


def _assert_exception_graph_excludes(
    root: BaseException,
    prohibited: tuple[object, ...],
) -> None:
    for error in _exception_graph(root):
        assert not _builtin_container_reaches_identity(error.args, prohibited)
        assert not _builtin_container_reaches_identity(error.__dict__, prohibited)
        assert not _builtin_container_reaches_identity(
            getattr(error, "__notes__", None),
            prohibited,
        )


def _assert_traceback_excludes(
    error: BaseException,
    prohibited: tuple[object, ...],
) -> None:
    assert error.__cause__ is None
    assert error.__context__ is None
    assert getattr(error, "__notes__", None) in (None, [])
    assert not _builtin_container_reaches_identity(error.args, prohibited)
    for frame in _coordinator_frames(error):
        for value in frame.f_locals.values():
            assert not _builtin_container_reaches_identity(value, prohibited)


class _FakeFinalizer:
    def __init__(
        self,
        target: object,
        callback: object,
        args: tuple[object, ...],
    ) -> None:
        self.alive = True
        self.atexit = True
        self._target = target
        self._callback = callback
        self._args = args

    def detach(self) -> object:
        if not self.alive:
            return None
        self.alive = False
        return (self._target, self._callback, self._args, {})


def _trace_raise_at(function: object, fragment: str, failure: BaseException) -> None:
    lines, first_line = inspect.getsourcelines(function)
    matching = [
        first_line + offset
        for offset, line in enumerate(lines)
        if fragment in line
    ]
    assert len(matching) == 1
    target = matching[0]

    def trace(frame: object, event: str, arg: object) -> object:
        del arg
        if frame.f_code is function.__code__ and event == "line" and frame.f_lineno == target:
            sys.settrace(None)
            raise failure
        return trace

    sys.settrace(trace)


def _new_scope(tmp_path: Path) -> tuple[object, ...]:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    mutation = operation._acquire_mutation_lease()
    connection = sqlite3.connect(":memory:", isolation_level=None)
    scope = transaction_module._ControllerConnectionScope(
        operation_lease=operation,
        connection=connection,
    )
    return location, session, resource, operation, mutation, connection, scope


def _finish_scope(parts: tuple[object, ...]) -> None:
    _, session, _, operation, mutation, connection, scope = parts
    if not scope._resolved:
        if scope._activation_acknowledgment is not None:
            scope.close_before_commit()
        else:
            connection.close()
    mutation._close()
    operation._close()
    session.close()


def _prepare_close_proved_with_blocker(
    tmp_path: Path,
) -> tuple[object, ...]:
    parts = _new_scope(tmp_path)
    _, session, resource, operation, mutation, connection, scope = parts
    blocker = resource.operation_guard(session)
    scope.activate()
    connection.execute("BEGIN IMMEDIATE")
    assert scope.commit() is None
    assert scope.close_after_commit(
        commit_succeeded=True,
        force_cleanup=False,
    ) is True
    assert type(resource._lifecycle_state) is writer_module._WriterSessionControllerCloseProved
    return (*parts, blocker)


def _finish_pending_with_blocker(
    *,
    session: object,
    resource: object,
    blocker: object,
) -> None:
    blocker._close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitKnownPendingCleanup
    assert resource._active_operations == {}
    session.close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


def _assert_process_control_after_exact_mutation_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: BaseException,
) -> None:
    parts = _prepare_close_proved_with_blocker(tmp_path)
    _, session, resource, operation, mutation, _, _, blocker = parts
    handle = operation._completion_handle
    original_release = resource._release_mutation_slot
    interrupted = False

    def release_then_interrupt(**kwargs: object) -> bool:
        nonlocal interrupted
        released = original_release(**kwargs)
        assert released is True
        if not interrupted:
            interrupted = True
            assert type(resource._lifecycle_state) is writer_module._WriterSessionControllerCloseProvedReleased
            assert resource._mutation_slot is None
            assert handle in _state_operations_for_test(resource)
            raise failure
        return released

    monkeypatch.setattr(resource, "_release_mutation_slot", release_then_interrupt)
    with pytest.raises(type(failure)) as captured:
        with operation:
            mutation._close()
    assert captured.value is failure
    if type(failure) is SystemExit:
        assert captured.value.code == failure.code
    assert interrupted is True
    assert handle.cleanup_required is True
    assert operation._closed is True
    assert operation._finalizer.alive is True
    assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitKnownPendingCleanup
    assert tuple(resource._active_operations) == (blocker._operation_id,)
    assert resource.active_for_owner() is False
    with pytest.raises(WriterSessionError):
        resource.operation_guard(session)
    _finish_pending_with_blocker(
        session=session,
        resource=resource,
        blocker=blocker,
    )


def _state_operations_for_test(resource: object) -> tuple[object, ...]:
    return writer_module._state_operations(resource._lifecycle_state)


def _state_operation_records_for_test(resource: object) -> tuple[object, ...]:
    return writer_module._state_operation_records(resource._lifecycle_state)


def _operation_record_for_test(resource: object, handle: object) -> object:
    return next(
        record
        for record in _state_operation_records_for_test(resource)
        if record.handle is handle
    )


def _two_real_resource_frames(tmp_path: Path) -> tuple[object, ...]:
    location_a = CoordinatorStateLocation.from_trusted_root(tmp_path / "state-a")
    location_b = CoordinatorStateLocation.from_trusted_root(tmp_path / "state-b")
    initialize_database(location_a)
    initialize_database(location_b)
    session_a = acquire_sqlite_writer_session(location_a)
    session_b = acquire_sqlite_writer_session(location_b)
    resource_a = session_a._resource
    resource_b = session_b._resource
    operation_a = resource_a.operation_guard(session_a)
    operation_b = resource_b.operation_guard(session_b)
    mutation_a = operation_a._acquire_mutation_lease()
    mutation_b = operation_b._acquire_mutation_lease()
    frame_a = resource_a._lifecycle_state.frame
    frame_b = resource_b._lifecycle_state.frame
    assert resource_a._lifecycle_epoch == resource_b._lifecycle_epoch == 1
    assert resource_a._resource_identity is not resource_b._resource_identity
    return (
        session_a,
        session_b,
        resource_a,
        resource_b,
        operation_a,
        operation_b,
        mutation_a,
        mutation_b,
        frame_a,
        frame_b,
    )


def _finish_two_real_resource_frames(parts: tuple[object, ...]) -> None:
    session_a, session_b, _, _, operation_a, operation_b, mutation_a, mutation_b, _, _ = parts
    mutation_a._close()
    mutation_b._close()
    operation_a._close()
    operation_b._close()
    session_a.close()
    session_b.close()


def _run_after_commit_process_control(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: BaseException,
) -> tuple[type[BaseException], str]:
    parts = _new_scope(tmp_path)
    _, _, resource, _, _, connection, scope = parts
    original_close = connection_module._RetainedSQLiteConnection._close_with_proof
    scope.activate()
    connection.execute("BEGIN IMMEDIATE")
    assert scope.commit() is None

    def interrupted_close(retained: object) -> None:
        assert retained._borrow_exact_connection() is connection
        raise failure

    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        interrupted_close,
    )
    try:
        with pytest.raises(type(failure)) as captured:
            scope.close_after_commit(commit_succeeded=True, force_cleanup=True)
        assert captured.value is failure
        assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitKnownUnproved
        observed = resource._state
    finally:
        monkeypatch.setattr(
            connection_module._RetainedSQLiteConnection,
            "_close_with_proof",
            original_close,
        )
        _finish_scope(parts)
    return type(failure), observed


def test_close_normal_return_is_the_only_connection_free_proof() -> None:
    connection = sqlite3.connect(":memory:")
    retained = connection_module._make_retained_sqlite_connection(
        connection, _new_test_resource_identity()
    )
    proof = retained._close_with_proof()
    assert type(proof) is connection_module._SQLiteConnectionCloseProof
    assert proof.connection_identity == id(connection)
    assert retained._close_with_proof() is proof
    assert "connection" not in getattr(type(proof), "__slots__", ())


@pytest.mark.parametrize("failure", [RuntimeError("ordinary"), KeyboardInterrupt()])
def test_close_failure_or_interruption_before_proof_allows_later_same_object_close(
    failure: BaseException,
) -> None:
    connection = sqlite3.connect(":memory:")
    retained = connection_module._make_retained_sqlite_connection(
        connection, _new_test_resource_identity()
    )
    _trace_raise_at(
        connection_module._RetainedSQLiteConnection._close_with_proof,
        (
            "proof = _SQLiteConnectionCloseProof("
            if type(failure) is KeyboardInterrupt
            else "sqlite3.Connection.close(exact_connection)"
        ),
        failure,
    )
    with pytest.raises(type(failure)) as captured:
        retained._close_with_proof()
    assert captured.value is failure
    assert retained._borrow_exact_connection() is connection
    if type(failure) is KeyboardInterrupt:
        with pytest.raises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")
    else:
        connection.execute("SELECT 1").close()
    proof = retained._close_with_proof()
    assert proof.connection_identity == id(connection)


def test_close_after_c2_is_rejected_before_another_sqlite_close(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, _, _, _, connection, scope = parts
    original_close = connection_module._RetainedSQLiteConnection._close_with_proof
    calls = 0

    def counted_close(retained: object) -> object:
        nonlocal calls
        calls += 1
        return original_close(retained)

    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        counted_close,
    )
    scope.activate()
    connection.execute("BEGIN IMMEDIATE")
    assert scope.commit() is None
    assert scope.close_after_commit(commit_succeeded=True, force_cleanup=False) is True
    assert scope.close_after_commit(commit_succeeded=True, force_cleanup=False) is True
    assert calls == 1
    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        original_close,
    )
    _finish_scope(parts)


def test_close_source_has_no_probe_programmingerror_or_message_matching() -> None:
    source = inspect.getsource(connection_module._RetainedSQLiteConnection._close_with_proof)
    assert "in_transaction" not in source
    assert "ProgrammingError" not in source
    assert "str(" not in source
    assert "closed" not in source.lower()


def test_controller_scope_construction_failure_precedes_resource_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    mutation = operation._acquire_mutation_lease()
    connection = sqlite3.connect(":memory:", isolation_level=None)
    before = resource._lifecycle_state
    failure = KeyboardInterrupt()

    def fail_retention(exact: sqlite3.Connection, identity: object) -> object:
        assert exact is connection
        assert identity is operation._completion_handle.resource_identity
        raise failure

    monkeypatch.setattr(
        transaction_module,
        "_make_retained_sqlite_connection",
        fail_retention,
    )
    with pytest.raises(KeyboardInterrupt) as captured:
        transaction_module._ControllerConnectionScope(
            operation_lease=operation,
            connection=connection,
        )
    assert captured.value is failure
    assert resource._lifecycle_state is before
    assert type(before) is writer_module._WriterSessionMutationActive
    connection.close()
    mutation._close()
    operation._close()
    session.close()


def test_controller_resource_publication_failure_occurs_before_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, resource, _, _, _, scope = parts
    original = writer_module._WriterSessionOperationLease._activate_controller_scope
    commit_calls: list[str] = []

    def fail_publication(self: object, **kwargs: object) -> object:
        del self, kwargs
        raise RuntimeError("publication-failed")

    monkeypatch.setattr(
        writer_module._WriterSessionOperationLease,
        "_activate_controller_scope",
        fail_publication,
    )
    monkeypatch.setattr(
        transaction_module,
        "_commit_transaction",
        lambda connection: commit_calls.append("commit"),
    )
    with pytest.raises(RuntimeError, match="publication-failed"):
        scope.activate()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionMutationActive
    assert commit_calls == []
    monkeypatch.setattr(
        writer_module._WriterSessionOperationLease,
        "_activate_controller_scope",
        original,
    )
    _finish_scope(parts)


def test_controller_commit_gate_requires_exact_resource_acknowledgment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, resource, _, _, _, scope = parts
    commit_calls: list[object] = []
    monkeypatch.setattr(
        transaction_module,
        "_commit_transaction",
        lambda connection: commit_calls.append(connection),
    )
    with pytest.raises(SQLiteMutationStoreError):
        scope.commit()
    assert commit_calls == []
    acknowledgment = scope.activate()
    assert resource._lifecycle_state is acknowledgment.resolution
    assert scope.commit() is None
    assert len(commit_calls) == 1
    _finish_scope(parts)


def test_controller_precommit_process_control_publishes_abort_unproved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, resource, _, _, connection, scope = parts
    original_close = connection_module._RetainedSQLiteConnection._close_with_proof
    failure = GeneratorExit()
    scope.activate()

    def interrupted_close(retained: object) -> None:
        assert retained._borrow_exact_connection() is connection
        raise failure

    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        interrupted_close,
    )
    with pytest.raises(GeneratorExit) as captured:
        scope.close_before_commit()
    assert captured.value is failure
    assert type(resource._lifecycle_state) is writer_module._WriterSessionAbortCloseUnproved
    assert resource._retained_connection is not None
    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        original_close,
    )
    _finish_scope(parts)


def test_controller_after_commit_normal_close_returns_active_successor(
    tmp_path: Path,
) -> None:
    parts = _new_scope(tmp_path)
    _, session, resource, operation, mutation, connection, scope = parts
    scope.activate()
    connection.execute("BEGIN IMMEDIATE")
    assert scope.commit() is None
    assert scope.close_after_commit(commit_succeeded=True, force_cleanup=False) is True
    assert type(resource._lifecycle_state) is writer_module._WriterSessionControllerCloseProved
    assert not hasattr(scope, "_connection")
    assert scope._retained_connection is None
    mutation._close()
    operation._close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
    session.close()


def test_controller_after_commit_ordinary_close_failure_preserves_qk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, resource, _, _, connection, scope = parts
    original_close = connection_module._RetainedSQLiteConnection._close_with_proof
    scope.activate()
    connection.execute("BEGIN IMMEDIATE")
    assert scope.commit() is None

    def failed_close(retained: object) -> None:
        assert retained._borrow_exact_connection() is connection
        raise RuntimeError("close-failed")

    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        failed_close,
    )
    assert scope.close_after_commit(commit_succeeded=True, force_cleanup=True) is False
    assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitKnownUnproved
    assert resource._state == writer_module._COMMIT_SUCCEEDED_QUARANTINED
    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        original_close,
    )
    _finish_scope(parts)


def test_controller_after_commit_uncertain_close_failure_preserves_qu(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, resource, _, _, connection, scope = parts
    original_close = connection_module._RetainedSQLiteConnection._close_with_proof
    scope.activate()

    def failed_close(retained: object) -> None:
        assert retained._borrow_exact_connection() is connection
        raise RuntimeError("close-failed")

    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        failed_close,
    )
    assert scope.close_after_commit(commit_succeeded=False, force_cleanup=True) is False
    assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitUncertainUnproved
    assert resource._state == writer_module._COMMIT_UNCERTAIN_QUARANTINED
    monkeypatch.setattr(
        connection_module._RetainedSQLiteConnection,
        "_close_with_proof",
        original_close,
    )
    _finish_scope(parts)


def test_controller_after_commit_keyboard_interrupt_stabilizes_qk_before_reraise(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert _run_after_commit_process_control(
        tmp_path,
        monkeypatch,
        KeyboardInterrupt(),
    ) == (KeyboardInterrupt, writer_module._COMMIT_SUCCEEDED_QUARANTINED)


def test_controller_after_commit_systemexit_stabilizes_qk_before_reraise(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert _run_after_commit_process_control(
        tmp_path,
        monkeypatch,
        SystemExit(7),
    ) == (SystemExit, writer_module._COMMIT_SUCCEEDED_QUARANTINED)


def test_controller_after_commit_generatorexit_stabilizes_qk_before_reraise(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert _run_after_commit_process_control(
        tmp_path,
        monkeypatch,
        GeneratorExit(),
    ) == (GeneratorExit, writer_module._COMMIT_SUCCEEDED_QUARANTINED)


def test_controller_explicit_close_waits_for_successor_and_operation_completion(
    tmp_path: Path,
) -> None:
    parts = _new_scope(tmp_path)
    _, session, resource, operation, mutation, connection, scope = parts
    scope.activate()
    connection.execute("BEGIN IMMEDIATE")
    assert scope.commit() is None
    started = threading.Event()
    finished = threading.Event()

    def close_session() -> None:
        started.set()
        session.close()
        finished.set()

    closer = threading.Thread(target=close_session)
    closer.start()
    assert started.wait(2)
    assert not finished.wait(0.05)
    assert scope.close_after_commit(commit_succeeded=True, force_cleanup=False) is True
    mutation._close()
    operation._close()
    closer.join(2)
    assert not closer.is_alive()
    assert finished.is_set()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


@pytest.mark.parametrize("after_assignment", [False, True])
def test_controller_successor_publication_interruption_retries_same_exact_successor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    after_assignment: bool,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, resource, _, _, connection, scope = parts
    scope.activate()
    connection.execute("BEGIN IMMEDIATE")
    assert scope.commit() is None
    original = writer_module._WriterSessionResource._publish_controller_resolution_for_operation
    calls = 0
    failure = KeyboardInterrupt()

    def interrupted(self: object, operation_lease: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            if after_assignment:
                original(self, operation_lease, **kwargs)
            raise failure
        return original(self, operation_lease, **kwargs)

    monkeypatch.setattr(
        writer_module._WriterSessionResource,
        "_publish_controller_resolution_for_operation",
        interrupted,
    )
    with pytest.raises(KeyboardInterrupt) as captured:
        scope.close_after_commit(commit_succeeded=True, force_cleanup=True)
    assert captured.value is failure
    assert calls == 2
    assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitKnownPendingCleanup
    assert scope._resolved is True
    monkeypatch.setattr(
        writer_module._WriterSessionResource,
        "_publish_controller_resolution_for_operation",
        original,
    )
    _finish_scope(parts)


def test_controller_stale_scope_and_aliases_are_rejected_after_handoff(
    tmp_path: Path,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, resource, _, _, connection, scope = parts
    acknowledgment = scope.activate()
    assert not hasattr(scope, "_connection")
    assert scope._retained_connection is not None
    connection.execute("BEGIN IMMEDIATE")
    assert scope.commit() is None
    assert scope.close_after_commit(commit_succeeded=True, force_cleanup=False) is True
    assert resource._lifecycle_state is not acknowledgment.resolution
    assert scope._retained_connection is None
    assert scope._activation_acknowledgment is None
    with pytest.raises(SQLiteMutationStoreError):
        scope.commit()
    _finish_scope(parts)


def test_controller_activation_interruption_after_assignment_is_retryable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, resource, _, _, _, scope = parts
    original = writer_module._WriterSessionOperationLease._activate_controller_scope
    failure = KeyboardInterrupt()
    calls = 0

    def assigned_then_interrupted(self: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        result = original(self, **kwargs)
        if calls == 1:
            raise failure
        return result

    monkeypatch.setattr(
        writer_module._WriterSessionOperationLease,
        "_activate_controller_scope",
        assigned_then_interrupted,
    )
    with pytest.raises(KeyboardInterrupt) as captured:
        scope.activate()
    assert captured.value is failure
    observed = resource._lifecycle_state
    assert type(observed) is writer_module._WriterSessionControllerResolution
    assert scope._activation_acknowledgment.resolution is observed
    assert scope.activate() is scope._activation_acknowledgment
    monkeypatch.setattr(
        writer_module._WriterSessionOperationLease,
        "_activate_controller_scope",
        original,
    )
    _finish_scope(parts)


def test_closed_variants_direct_construction_accepts_every_governed_variant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    mutation = operation._acquire_mutation_lease()
    active = resource._lifecycle_state
    assert type(active) is writer_module._WriterSessionMutationActive
    activity, slot = active.frame.activity, active.frame.slot
    authority, operations = activity.authority, activity.operations
    cleanup = writer_module._ContinueCleanup(
        writer_module._CleanupBeforeR1WithSlot(activity, slot)
    )
    connection = sqlite3.connect(":memory:")
    retained = connection_module._make_retained_sqlite_connection(
        connection, operation._completion_handle.resource_identity
    )
    proof_connection = sqlite3.connect(":memory:")
    proof_retained = connection_module._make_retained_sqlite_connection(
        proof_connection, operation._completion_handle.resource_identity
    )
    proof = proof_retained._close_with_proof()
    token = writer_module._ControllerScopeToken(retained, operation._completion_handle)
    proof_token = writer_module._ControllerScopeToken(
        proof_retained,
        operation._completion_handle,
    )
    resume = writer_module._ResumeActive()
    no_slot_cleanup = writer_module._ContinueCleanup(
        writer_module._CleanupBeforeR1NoSlot(activity)
    )
    zero_activity = writer_module._WriterSessionActivity(authority, ())

    variants = (
        writer_module._WriterSessionActive(zero_activity),
        writer_module._WriterSessionOperationsActive(activity),
        writer_module._WriterSessionMutationActive(active.frame),
        writer_module._WriterSessionControllerResolution(
            active.frame, token, writer_module._ResumeIfCloseProvedAndStillEligible()
        ),
        writer_module._WriterSessionControllerCloseProved(
            active.frame,
            proof_token,
            writer_module._ControllerResolutionIntent.COMMIT_KNOWN,
            proof,
            resume,
        ),
        writer_module._WriterSessionControllerCloseProvedReleased(
            activity,
            proof_token,
            writer_module._ControllerResolutionIntent.COMMIT_KNOWN,
            proof,
            resume,
        ),
        writer_module._WriterSessionAbortCloseUnproved(token, retained, cleanup),
        writer_module._WriterSessionCommitUncertainUnproved(token, retained, cleanup),
        writer_module._WriterSessionCommitKnownUnproved(token, retained, cleanup),
        writer_module._WriterSessionAbortPendingCleanup(proof_token, proof, cleanup),
        writer_module._WriterSessionCommitUncertainPendingCleanup(proof_token, proof, cleanup),
        writer_module._WriterSessionCommitKnownPendingCleanup(proof_token, proof, cleanup),
        writer_module._WriterSessionOperationsClosing(no_slot_cleanup),
        writer_module._WriterSessionMutationClosing(cleanup),
        writer_module._WriterSessionOrdinaryCleanup(cleanup),
        writer_module._WriterSessionTerminalX(),
        writer_module._WriterSessionForkInvalid(),
    )
    assert len({type(variant) for variant in variants}) == len(variants)
    assert all(str(id(connection)) not in repr(variant) for variant in variants)
    assert all(":memory:" not in repr(variant) for variant in variants)
    carrier_variants = variants[1:15]
    assert len(carrier_variants) == 14
    expected_records = activity.operation_records
    assert len(expected_records) == 1
    correlation = expected_records[0].invocation_correlation
    post_poison_calls: list[type[object]] = []

    def fail_after_poison(state: object) -> object:
        post_poison_calls.append(type(state))
        assert resource._operation_exit_process_control_poisoned_value
        raise RuntimeError("stop after direct scanner poison")

    with monkeypatch.context() as patch:
        patch.setattr(writer_module, "_state_authority", fail_after_poison)
        for carrier in carrier_variants:
            resource._lifecycle_state = carrier
            resource._operation_exit_process_control_poisoned_value = False
            with pytest.raises(RuntimeError, match="stop after direct scanner poison"):
                resource._stabilize_operation_exit_for_process_control(correlation)
            assert resource._operation_exit_process_control_poisoned_value

        claimable_carriers = (
            variants[6],
            variants[7],
            variants[8],
            variants[9],
            variants[10],
            variants[11],
            variants[14],
        )
        assert len(claimable_carriers) == len(writer_module._CLEANUP_PENDING_TYPES) == 7
        for claim_epoch, carrier in enumerate(claimable_carriers, start=1):
            claim = writer_module._WriterSessionCleanupClaim(
                token=writer_module._CleanupClaimToken(),
                owner_thread_ref=weakref.ref(threading.current_thread()),
                resource_identity=resource._resource_identity,
                owner_pid=os.getpid(),
                lifecycle_epoch=correlation.lifecycle_epoch,
                claim_epoch=claim_epoch,
            )
            resource._lifecycle_state = writer_module._WriterSessionCleanupClaimed(
                carrier,
                claim,
            )
            resource._operation_exit_process_control_poisoned_value = False
            with pytest.raises(RuntimeError, match="stop after direct scanner poison"):
                resource._stabilize_operation_exit_for_process_control(correlation)
            assert resource._operation_exit_process_control_poisoned_value

    assert len(post_poison_calls) == 21
    resource._lifecycle_state = active
    resource._operation_exit_process_control_poisoned_value = False
    connection.close()
    mutation._close()
    operation._close()
    session.close()


def test_closed_variants_reject_prohibited_combinations(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    mutation = operation._acquire_mutation_lease()
    state = resource._lifecycle_state
    activity, slot = state.frame.activity, state.frame.slot
    authority, operations = activity.authority, activity.operations
    cleanup = writer_module._ContinueCleanup(
        writer_module._CleanupBeforeR1WithSlot(activity, slot)
    )
    no_slot_cleanup = writer_module._ContinueCleanup(
        writer_module._CleanupBeforeR1NoSlot(activity)
    )
    connection = sqlite3.connect(":memory:")
    retained = connection_module._make_retained_sqlite_connection(
        connection, operation._completion_handle.resource_identity
    )
    token = writer_module._ControllerScopeToken(retained, operation._completion_handle)

    with pytest.raises(ValueError):
        writer_module._WriterSessionCommitUncertainUnproved(
            token, None, cleanup
        )
    with pytest.raises(ValueError):
        writer_module._WriterSessionCommitKnownUnproved(
            token, retained, no_slot_cleanup
        )
    with pytest.raises(ValueError):
        writer_module._WriterSessionCommitKnownPendingCleanup(token, retained, cleanup)
    with pytest.raises(ValueError):
        writer_module._WriterSessionOperationsActive(
            writer_module._WriterSessionActivity(authority, ())
        )
    with pytest.raises(ValueError):
        writer_module._WriterSessionMutationFrame(
            writer_module._WriterSessionActivity(authority, ()),
            slot,
        )
    with pytest.raises(TypeError):
        writer_module._WriterSessionTerminalX(authority=authority)
    with pytest.raises(TypeError):
        writer_module._WriterSessionTerminalX(operation=operations[0])

    state_types = (
        writer_module._WriterSessionCommitUncertainUnproved,
        writer_module._WriterSessionCommitKnownUnproved,
        writer_module._WriterSessionCommitUncertainPendingCleanup,
        writer_module._WriterSessionCommitKnownPendingCleanup,
    )
    for state_type in state_types:
        fields = set(getattr(state_type, "__dataclass_fields__"))
        assert not {"retained_connection", "close_proof"} <= fields
    connection.close()
    mutation._close()
    operation._close()
    session.close()


def test_structural_cleanup_cursors_encode_r2_r3_l1_h2_t1_consequences(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    mutation = operation._acquire_mutation_lease()
    state = resource._lifecycle_state
    activity, slot = state.frame.activity, state.frame.slot
    authority = activity.authority
    lock = authority.authority_lock
    binding = authority.database_binding
    cursors = (
        writer_module._CleanupBeforeR1WithSlot(activity, slot),
        writer_module._CleanupBeforeR2WithSlot(
            lock, binding, slot, authority.resource_identity
        ),
        writer_module._CleanupBeforeR3(lock, binding, authority.resource_identity),
        writer_module._CleanupBeforeL1(lock, authority.resource_identity),
        writer_module._CleanupBeforeH1(lock, authority.resource_identity),
        writer_module._CleanupBeforeH2(lock, authority.resource_identity),
        writer_module._CleanupBeforeT1(authority.resource_identity),
    )
    assert hasattr(cursors[0], "operations") and hasattr(cursors[0], "slot")
    assert not hasattr(cursors[1], "operations") and hasattr(cursors[1], "slot")
    assert not hasattr(cursors[2], "slot") and hasattr(cursors[2], "database_binding")
    assert not hasattr(cursors[3], "database_binding") and hasattr(cursors[3], "authority_lock")
    assert not hasattr(cursors[6], "authority_lock")
    assert len({type(cursor) for cursor in cursors}) == len(cursors)
    mutation._close()
    operation._close()
    session.close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
    assert resource not in writer_module._ACTIVE_SESSION_RESOURCES.values()


def test_operation_finalizer_is_constructed_before_active_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    observations: list[tuple[object, ...]] = []

    def factory(target: object, callback: object, *args: object) -> _FakeFinalizer:
        observations.append((target, callback, args, tuple(resource._active_operations)))
        return _FakeFinalizer(target, callback, args)

    monkeypatch.setattr(writer_module, "_FINALIZER_FACTORY", factory)
    operation = resource.operation_guard(session)
    assert len(observations) == 1
    assert observations[0][3] == ()
    assert len(resource._active_operations) == 1
    operation._close()
    session.close()


def test_operation_finalizer_construction_failure_leaves_no_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    failure = KeyboardInterrupt()

    def fail_factory(*args: object) -> object:
        del args
        raise failure

    monkeypatch.setattr(writer_module, "_FINALIZER_FACTORY", fail_factory)
    with pytest.raises(KeyboardInterrupt) as captured:
        resource.operation_guard(session)
    assert captured.value is failure
    assert resource._active_operations == {}
    assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
    session.close()


def test_operation_publication_failure_detaches_preconstructed_completion(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    failure = RuntimeError("publication-window")
    _trace_raise_at(
        writer_module._WriterSessionResource._begin_operation,
        "self._lifecycle_state = successor",
        failure,
    )
    try:
        with pytest.raises(RuntimeError) as captured:
            resource.operation_guard(session)
    finally:
        sys.settrace(None)
    assert captured.value is failure
    assert resource._active_operations == {}
    assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
    session.close()


def test_operation_process_control_after_publication_unwinds_exact_record(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    failure = KeyboardInterrupt()
    _trace_raise_at(
        writer_module._WriterSessionResource._begin_operation,
        "self._last_next_operation_id = operation_id + 1",
        failure,
    )
    try:
        with pytest.raises(KeyboardInterrupt) as captured:
            resource.operation_guard(session)
    finally:
        sys.settrace(None)
    assert captured.value is failure
    assert resource._active_operations == {}
    assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
    session.close()


def test_never_published_operation_callback_is_idempotent_noop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    callback_and_args: list[tuple[object, tuple[object, ...]]] = []

    def factory(target: object, callback: object, *args: object) -> _FakeFinalizer:
        callback_and_args.append((callback, args))
        return _FakeFinalizer(target, callback, args)

    monkeypatch.setattr(writer_module, "_FINALIZER_FACTORY", factory)
    failure = RuntimeError("before-publication")
    _trace_raise_at(
        writer_module._WriterSessionResource._begin_operation,
        "self._lifecycle_state = successor",
        failure,
    )
    try:
        with pytest.raises(RuntimeError):
            resource.operation_guard(session)
    finally:
        sys.settrace(None)
    callback, args = callback_and_args[0]
    callback(*args)
    callback(*args)
    assert resource._active_operations == {}
    assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
    session.close()


def test_operation_completion_is_exact_and_idempotent() -> None:
    handle = writer_module._OperationCompletionHandle(
        resource_identity=_new_test_resource_identity(),
        operation_id=1,
        owner_pid=os.getpid(),
        owner_thread=threading.get_ident(),
        lifecycle_epoch=1,
    )
    assert handle.operation_id == 1
    assert repr(handle) == "<_OperationCompletionHandle>"


def test_operation_explicit_completion_then_finalizer_is_harmless(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    operation._close()
    operation._close()
    assert handle not in _state_operations_for_test(resource)
    writer_module._finalize_writer_session_operation(resource, handle)
    writer_module._finalize_writer_session_operation(resource, handle)
    assert resource._active_operations == {}
    session.close()


def test_operation_publication_requires_resource_owned_explicit_retirement(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    preparation = resource._prepare_operation_retirement(handle)
    assert preparation is not None
    assert not hasattr(writer_module, "_OperationLocalRetirementAcknowledgment")

    with pytest.raises(WriterSessionError):
        resource._publish_prepared_operation_retirement(preparation, None)
    with pytest.raises(WriterSessionError):
        resource._publish_prepared_operation_retirement(preparation, operation)
    assert operation._closed is False
    assert operation._finalizer.alive is True
    assert handle in _state_operations_for_test(resource)
    assert resource.active_for_owner() is False

    with resource._condition:
        operation._closed = True
    with pytest.raises(WriterSessionError):
        resource._publish_prepared_operation_retirement(preparation, operation)
    assert operation._finalizer.alive is True
    assert handle in _state_operations_for_test(resource)

    operation._close()
    assert operation._closed is True
    assert operation._finalizer.alive is False
    assert handle not in _state_operations_for_test(resource)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
    session.close()


def test_direct_live_operation_finalizer_fails_closed_and_retry_reaches_terminal_x(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle

    operation._finalizer()

    assert operation._closed is True
    assert operation._finalizer.alive is False
    assert operation._session is session
    assert handle.cleanup_required is True
    assert handle not in _state_operations_for_test(resource)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
    assert resource.active_for_owner() is False
    with pytest.raises(WriterSessionError):
        resource.operation_guard(session)

    operation._close()
    assert handle not in _state_operations_for_test(resource)
    session.close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


def test_genuine_operation_collection_is_cleanup_only_and_reaches_x(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    operation_ref = weakref.ref(operation)

    operation = None
    gc.collect()

    assert operation_ref() is None
    assert handle._bound_operation_lease() is None
    assert handle.operation_finalizer is not None
    assert handle.operation_finalizer.alive is False
    assert handle not in _state_operations_for_test(resource)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
    assert resource.active_for_owner() is False
    session.close()


def test_never_published_same_resource_and_stale_epoch_handles_reject(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    initial_state = resource._lifecycle_state

    never_published = writer_module._OperationCompletionHandle(
        resource_identity=resource._resource_identity,
        operation_id=resource._next_operation_id,
        owner_pid=os.getpid(),
        owner_thread=threading.get_ident(),
        lifecycle_epoch=resource._lifecycle_epoch,
    )
    preparation = writer_module._OperationRetirementPreparationAcknowledgment(
        resource._resource_identity,
        resource._lifecycle_epoch,
        never_published,
    )
    never_published._record_retirement_preparation_acknowledgment(preparation)
    with pytest.raises(AttributeError):
        object.__setattr__(
            never_published,
            "_local_retirement_acknowledgment",
            object(),
        )
    with pytest.raises(WriterSessionError):
        resource._publish_prepared_operation_retirement(preparation, None)

    stale = writer_module._OperationCompletionHandle(
        resource_identity=resource._resource_identity,
        operation_id=resource._next_operation_id + 1,
        owner_pid=os.getpid(),
        owner_thread=threading.get_ident(),
        lifecycle_epoch=resource._lifecycle_epoch + 1,
    )
    stale_preparation = writer_module._OperationRetirementPreparationAcknowledgment(
        resource._resource_identity,
        resource._lifecycle_epoch + 1,
        stale,
    )
    with pytest.raises(WriterSessionError):
        resource._publish_prepared_operation_retirement(stale_preparation, None)

    assert resource._lifecycle_state is initial_state
    assert _state_operations_for_test(resource) == ()
    session.close()


def test_cross_resource_operation_lease_cannot_authorize_retirement(
    tmp_path: Path,
) -> None:
    location_a = CoordinatorStateLocation.from_trusted_root(tmp_path / "state-a")
    location_b = CoordinatorStateLocation.from_trusted_root(tmp_path / "state-b")
    initialize_database(location_a)
    initialize_database(location_b)
    session_a = acquire_sqlite_writer_session(location_a)
    session_b = acquire_sqlite_writer_session(location_b)
    resource_a = session_a._resource
    resource_b = session_b._resource
    operation_a = resource_a.operation_guard(session_a)
    operation_b = resource_b.operation_guard(session_b)
    handle_a = operation_a._completion_handle
    preparation_a = resource_a._prepare_operation_retirement(handle_a)
    assert preparation_a is not None

    assert resource_a._retire_operation_lease_locally(
        preparation_a,
        operation_b,
    ) is False
    with pytest.raises(WriterSessionError):
        resource_a._publish_prepared_operation_retirement(
            preparation_a,
            operation_b,
        )
    with pytest.raises(WriterSessionError):
        resource_b._publish_prepared_operation_retirement(
            preparation_a,
            operation_a,
        )
    assert handle_a in _state_operations_for_test(resource_a)
    assert operation_a._closed is False
    assert operation_a._finalizer.alive is True

    operation_a._close()
    operation_b._close()
    session_a.close()
    session_b.close()


def test_operation_finalizer_callback_in_fork_child_is_non_authoritative(
    tmp_path: Path,
) -> None:
    assert hasattr(os, "fork")
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        try:
            writer_module._finalize_writer_session_operation(resource, handle)
            payload = f"{resource._state}:{len(resource._active_operations)}"
            os.write(write_fd, payload.encode("ascii"))
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    ready, _, _ = select.select([read_fd], [], [], 3)
    assert ready == [read_fd]
    payload = os.read(read_fd, 256).decode("ascii")
    os.close(read_fd)
    waited, status = os.waitpid(child, 0)
    assert waited == child and status == 0
    assert payload == "fork_invalid:0"
    assert len(resource._active_operations) == 1
    operation._close()
    session.close()


def test_mutation_lease_construction_failure_unwinds_published_slot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    failure = GeneratorExit()

    def fail_factory(**kwargs: object) -> object:
        del kwargs
        raise failure

    monkeypatch.setattr(writer_module, "_MUTATION_LEASE_FACTORY", fail_factory)
    with pytest.raises(GeneratorExit) as captured:
        operation._acquire_mutation_lease()
    assert captured.value is failure
    assert resource._mutation_slot is None
    assert len(resource._active_operations) == 1
    operation._close()
    session.close()


def _install_claim_in_thread(
    resource: object,
    ready: threading.Event,
    release: threading.Event | None,
    captured: list[object],
) -> None:
    with resource._condition:
        resource._freeze_admission_locked()
        pending = resource._lifecycle_state
        claim = resource._install_cleanup_claim_locked(pending)
        assert resource._require_cleanup_claim_locked(claim).claim is claim
        captured.extend((threading.current_thread(), threading.get_ident(), claim))
    ready.set()
    if release is not None:
        assert release.wait(5)


def test_cleanup_claim_exact_live_owner_and_live_other_thread_rejection(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    ready = threading.Event()
    release = threading.Event()
    captured: list[object] = []
    owner = threading.Thread(
        target=_install_claim_in_thread,
        args=(resource, ready, release, captured),
    )
    owner.start()
    assert ready.wait(2)
    owner_thread, _, claim = captured
    assert owner_thread is owner
    assert claim.owner_thread_ref() is owner
    with resource._condition:
        state = resource._lifecycle_state
        assert resource._claim_or_take_over_locked(
            state,
            blocking=False,
            finalizer=False,
        ) is None
    release.set()
    owner.join(2)
    assert not owner.is_alive()
    resource._continue_cleanup(blocking=True, finalizer=False)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
    session.close()


def test_cleanup_claim_dead_thread_object_present_is_taken_over(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    ready = threading.Event()
    captured: list[object] = []
    owner = threading.Thread(
        target=_install_claim_in_thread,
        args=(resource, ready, None, captured),
    )
    owner.start()
    assert ready.wait(2)
    owner.join(2)
    assert not owner.is_alive()
    old_claim = captured[2]
    assert old_claim.owner_thread_ref() is owner
    with resource._condition:
        new_claim = resource._claim_or_take_over_locked(
            resource._lifecycle_state,
            blocking=False,
            finalizer=False,
        )
        assert new_claim is not old_claim
        assert new_claim.claim_epoch == old_claim.claim_epoch + 1
    resource._release_cleanup_claim(new_claim)
    resource._continue_cleanup(blocking=True, finalizer=False)
    session.close()


def test_cleanup_claim_dead_weakref_is_taken_over(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    ready = threading.Event()
    captured: list[object] = []
    owner = threading.Thread(
        target=_install_claim_in_thread,
        args=(resource, ready, None, captured),
    )
    owner.start()
    assert ready.wait(2)
    owner.join(2)
    old_claim = captured[2]
    captured[0] = None
    del owner
    gc.collect()
    assert old_claim.owner_thread_ref() is None
    with resource._condition:
        new_claim = resource._claim_or_take_over_locked(
            resource._lifecycle_state,
            blocking=False,
            finalizer=False,
        )
        assert new_claim is not old_claim
    resource._release_cleanup_claim(new_claim)
    resource._continue_cleanup(blocking=True, finalizer=False)
    session.close()


def test_cleanup_claim_recycled_integer_creates_new_exact_thread_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    ready = threading.Event()
    captured: list[object] = []
    owner = threading.Thread(
        target=_install_claim_in_thread,
        args=(resource, ready, None, captured),
    )
    owner.start()
    assert ready.wait(2)
    owner.join(2)
    old_owner, old_ident, old_claim = captured
    takeover: list[object] = []
    started = threading.Event()
    proceed = threading.Event()
    finished = threading.Event()

    def contender() -> None:
        contender_thread = threading.current_thread()
        contender_ident = threading.get_ident()
        takeover.extend((contender_thread, contender_ident))
        started.set()
        assert proceed.wait(5)
        with resource._condition:
            claim = resource._claim_or_take_over_locked(
                resource._lifecycle_state,
                blocking=False,
                finalizer=False,
            )
            takeover.append(claim)
        finished.set()

    monkeypatch.setattr(writer_module, "get_ident", lambda: old_ident)
    contender_thread = threading.Thread(target=contender)
    contender_thread.start()
    assert started.wait(2)
    proceed.set()
    assert finished.wait(2)
    contender_thread.join(2)
    new_claim = takeover[2]
    assert takeover[0] is contender_thread
    assert old_owner is not contender_thread
    assert old_claim.token is not new_claim.token
    assert new_claim.claim_epoch == old_claim.claim_epoch + 1
    resource._continue_cleanup(blocking=True, finalizer=False)
    session.close()


def test_cleanup_claim_stale_token_epoch_cursor_and_process_are_rejected(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    with resource._condition:
        resource._freeze_admission_locked()
        claim = resource._install_cleanup_claim_locked(resource._lifecycle_state)
        stale_claims = (
            writer_module._WriterSessionCleanupClaim(
                token=writer_module._CleanupClaimToken(),
                owner_thread_ref=claim.owner_thread_ref,
                resource_identity=claim.resource_identity,
                owner_pid=claim.owner_pid,
                lifecycle_epoch=claim.lifecycle_epoch,
                claim_epoch=claim.claim_epoch,
            ),
            writer_module._WriterSessionCleanupClaim(
                token=claim.token,
                owner_thread_ref=claim.owner_thread_ref,
                resource_identity=claim.resource_identity,
                owner_pid=claim.owner_pid,
                lifecycle_epoch=claim.lifecycle_epoch,
                claim_epoch=claim.claim_epoch + 1,
            ),
            writer_module._WriterSessionCleanupClaim(
                token=claim.token,
                owner_thread_ref=claim.owner_thread_ref,
                resource_identity=claim.resource_identity,
                owner_pid=claim.owner_pid + 1,
                lifecycle_epoch=claim.lifecycle_epoch,
                claim_epoch=claim.claim_epoch,
            ),
        )
        for stale in stale_claims:
            with pytest.raises(SQLiteMutationStoreError):
                resource._require_cleanup_claim_locked(stale)
        assert "pending_state_identity" not in claim.__dataclass_fields__
        assert "resume_cursor" not in claim.__dataclass_fields__
    resource._release_cleanup_claim(claim)
    resource._continue_cleanup(blocking=True, finalizer=False)
    session.close()


def test_thread_affine_retained_connection_remains_truthfully_unproved_elsewhere() -> None:
    retained_and_connection: list[object] = []

    def owner() -> None:
        connection = sqlite3.connect(":memory:", check_same_thread=False)
        retained_and_connection.extend(
            (
                connection_module._make_retained_sqlite_connection(
                    connection, _new_test_resource_identity()
                ),
                connection,
            )
        )

    thread = threading.Thread(target=owner)
    thread.start()
    thread.join(2)
    retained, connection = retained_and_connection
    with pytest.raises(RuntimeError, match="connection custody unavailable"):
        retained._close_with_proof()
    connection.close()


def test_transition_safe_error_traceback_direct_locals_and_builtin_containers_exclude_captured_sensitive_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(
        tmp_path,
        ready_dependency=True,
    ) as fixture:
        resource = fixture.writer_session._resource
        captured: list[object] = [
            fixture.command,
            fixture.writer_session,
            resource,
            resource._credential,
            resource._authority_lock,
        ]
        raw = RuntimeError("vs1a-transition-private-sentinel")
        captured_cursor: list[sqlite3.Cursor] = []
        captured_connection: list[sqlite3.Connection] = []
        captured_disposition: list[object] = []
        captured_sql: list[str] = []
        captured_parameters: list[tuple[object, ...]] = []
        target_active = False
        original_execute = transition_reader_module._execute_select_fetch_two
        original_cursor_close = select_support_module._close_cursor_safely
        original_open = transaction_module._open_bound_existing_sqlite_connection
        original_controller_init = transaction_module._CoordinatorMutationTransactionController.__init__
        original_mutation_factory = writer_module._MUTATION_LEASE_FACTORY
        original_disposition = transaction_module._safe_mutation_failure_disposition
        original_begin = resource._begin_operation
        target_sql = transition_reader_module._TRANSITION_EVENT_IDEMPOTENCY_LOOKUP_SELECT.sql
        expected_parameters = (
            fixture.command.work_item_id,
            fixture.command.idempotency_key,
        )

        def capture_execute(**kwargs: object) -> object:
            nonlocal target_active
            if kwargs["sql"] == target_sql:
                captured.extend((kwargs["capability"], kwargs["capability"]._state))
                captured_sql.append(kwargs["sql"])
                captured_parameters.append(kwargs["parameters"])
                target_active = True
                try:
                    return original_execute(**kwargs)
                finally:
                    target_active = False
            return original_execute(**kwargs)

        def fail_target_cursor_close(cursor: object) -> object:
            if target_active:
                assert type(cursor) is sqlite3.Cursor
                captured_cursor.append(cursor)
                cursor.close()
                raise raw
            return original_cursor_close(cursor)

        def capture_open(*args: object, **kwargs: object) -> sqlite3.Connection:
            connection = original_open(*args, **kwargs)
            captured_connection.append(connection)
            return connection

        def capture_controller(self: object, *args: object, **kwargs: object) -> None:
            original_controller_init(self, *args, **kwargs)
            captured.append(self)

        def capture_mutation(**kwargs: object) -> object:
            lease = original_mutation_factory(**kwargs)
            captured.append(lease)
            return lease

        def capture_disposition(error: SQLiteMutationStoreError) -> object:
            disposition = original_disposition(error)
            captured_disposition.append(disposition)
            return disposition

        assert type(resource.operation_guard) is types.MethodType

        def capture_begin(
            owner_session: object,
            invocation_correlation: object,
        ) -> object:
            operation = original_begin(owner_session, invocation_correlation)
            captured.extend((operation, invocation_correlation))
            return operation

        monkeypatch.setattr(transition_reader_module, "_execute_select_fetch_two", capture_execute)
        monkeypatch.setattr(select_support_module, "_close_cursor_safely", fail_target_cursor_close)
        monkeypatch.setattr(transaction_module, "_open_bound_existing_sqlite_connection", capture_open)
        monkeypatch.setattr(
            transaction_module._CoordinatorMutationTransactionController,
            "__init__",
            capture_controller,
        )
        monkeypatch.setattr(writer_module, "_MUTATION_LEASE_FACTORY", capture_mutation)
        monkeypatch.setattr(transaction_module, "_safe_mutation_failure_disposition", capture_disposition)
        monkeypatch.setattr(resource, "_begin_operation", capture_begin)
        with pytest.raises(SQLiteMutationStoreError) as raised:
            fixture.writer_session.apply_transition(fixture.command)
        error = raised.value
        assert captured_sql == [target_sql]
        assert captured_parameters == [expected_parameters]
        assert len(captured_cursor) == len(captured_connection) == 1
        assert len(captured_disposition) == 1
        disposition = captured_disposition[0]
        assert error is disposition.error
        assert error.error_class == "mutation_failed"
        database_path = fixture.location.database_path
        resolved_path = str(database_path.resolve())
        captured.extend(
            (
                raw,
                captured_cursor[0],
                captured_connection[0],
                database_path,
                resolved_path,
                target_sql,
                expected_parameters,
                *expected_parameters,
            )
        )
        prohibited = tuple(item for item in captured if item is not None)
        _assert_traceback_excludes(error, prohibited)
        safe_values = (resolved_path, target_sql, expected_parameters, *expected_parameters)
        for frame in _coordinator_frames(error):
            for value in frame.f_locals.values():
                assert not _builtin_container_reaches_exact_value(value, safe_values)
        rendered = "\n".join(
            (
                str(error),
                repr(error),
                repr(error.args),
                repr(getattr(error, "__notes__", None)),
                "".join(traceback.format_exception(error)),
            )
        )
        for forbidden in (str(raw), resolved_path, target_sql, *expected_parameters):
            assert forbidden not in rendered
        with pytest.raises(sqlite3.ProgrammingError):
            captured_cursor[0].fetchone()
        with pytest.raises(sqlite3.ProgrammingError):
            captured_connection[0].execute("SELECT 1")
        assert resource._mutation_slot is None
        assert resource._active_operations == {}


@pytest.mark.parametrize(
    "effect_kind",
    ("transition", "global-stop"),
    ids=("transition", "global-stop"),
)
def test_genuine_bound_public_guard_safe_error_has_complete_outward_privacy(
    effect_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        session = fixture.writer_session
        resource = session._resource
        assert type(resource.operation_guard) is types.MethodType
        original_begin = resource._begin_operation
        correlations: list[object] = []
        operations: list[object] = []
        records: list[object] = []

        def capture_begin(
            owner_session: object,
            invocation_correlation: object,
        ) -> object:
            operation = original_begin(owner_session, invocation_correlation)
            correlations.append(invocation_correlation)
            operations.append(operation)
            records.append(
                _operation_record_for_test(
                    resource,
                    operation._completion_handle,
                )
            )
            return operation

        exact_error = transaction_module._mutation_failed()
        disposition = transaction_module._safe_mutation_failure_disposition(
            exact_error
        )

        def safe_result(**kwargs: object) -> object:
            assert kwargs
            return disposition

        with monkeypatch.context() as patch:
            patch.setattr(resource, "_begin_operation", capture_begin)
            patch.setattr(
                transaction_module,
                (
                    "_run_atomic_transition_apply"
                    if effect_kind == "transition"
                    else "_run_atomic_global_stop_apply"
                ),
                safe_result,
            )
            with pytest.raises(SQLiteMutationStoreError) as raised:
                if effect_kind == "transition":
                    session.apply_transition(fixture.command)
                else:
                    session.apply_global_stop_update(
                        global_stop_tests._command(),
                        global_stop_tests._decision(),
                    )

        error = raised.value
        assert error is exact_error
        assert error.error_class == "mutation_failed"
        assert error.args == ("mutation_failed",)
        assert error.__cause__ is None
        assert error.__context__ is None
        assert len(correlations) == len(operations) == len(records) == 1
        assert records[0].invocation_correlation is correlations[0]
        _assert_exception_graph_has_no_coordinator_traceback(error)
        _assert_exception_graph_excludes(
            error,
            (
                correlations[0],
                operations[0],
                operations[0]._completion_handle,
                records[0],
                session,
                resource,
                fixture.command,
            ),
        )
        assert resource._operation_exit_process_control_poisoned_value is False
        assert resource.active_for_owner() is True
        session.close()
        assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


@pytest.mark.parametrize(
    "effect_kind",
    ("transition", "global-stop"),
    ids=("transition", "global-stop"),
)
def test_genuine_bound_safe_error_severs_active_caller_context_without_mutating_prior(
    effect_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        session = fixture.writer_session
        resource = session._resource
        assert type(resource.operation_guard) is types.MethodType
        original_begin = resource._begin_operation
        correlations: list[object] = []
        operations: list[object] = []
        records: list[object] = []

        def capture_begin(
            owner_session: object,
            invocation_correlation: object,
        ) -> object:
            operation = original_begin(owner_session, invocation_correlation)
            correlations.append(invocation_correlation)
            operations.append(operation)
            records.append(
                _operation_record_for_test(
                    resource,
                    operation._completion_handle,
                )
            )
            return operation

        transition_command = fixture.command
        global_stop_command = global_stop_tests._command()
        operator_decision = global_stop_tests._decision()
        invoked_command = (
            transition_command
            if effect_kind == "transition"
            else global_stop_command
        )
        exact_error = transaction_module._mutation_failed()
        disposition = transaction_module._safe_mutation_failure_disposition(
            exact_error
        )

        def safe_result(**kwargs: object) -> object:
            assert kwargs
            return disposition

        cause = _raised_exception_for_sanitizer(
            LookupError("caller-owned-cause")
        )
        context = _raised_exception_for_sanitizer(
            ValueError("caller-owned-context")
        )
        private_marker = object()
        connection = sqlite3.connect(":memory:")
        cursor = connection.cursor()
        prior_reference: RuntimeError | None = None
        outward_error: SQLiteMutationStoreError | None = None
        prior_traceback: object | None = None
        prior_cause: BaseException | None = None
        prior_context: BaseException | None = None
        prior_args: tuple[object, ...] | None = None
        prior_notes: list[str] | None = None
        prior_dictionary: dict[str, object] | None = None
        prior_dictionary_snapshot: dict[str, object] | None = None
        prior_suppress_context: bool | None = None
        cause_traceback = cause.__traceback__
        context_traceback = context.__traceback__
        private_payload = (
            session,
            invoked_command,
            operator_decision if effect_kind == "global-stop" else None,
            private_marker,
            connection,
            cursor,
        )
        try:
            try:
                raise RuntimeError("caller-owned-prior", private_payload)
            except RuntimeError as prior:
                prior_reference = prior
                prior.__cause__ = cause
                prior.__context__ = context
                prior.__suppress_context__ = True
                prior.add_note("caller-owned-note")
                prior.caller_owned = {
                    "marker": private_marker,
                    "connection": connection,
                    "cursor": cursor,
                }
                prior_traceback = prior.__traceback__
                prior_cause = prior.__cause__
                prior_context = prior.__context__
                prior_args = prior.args
                prior_notes = prior.__notes__
                prior_dictionary = prior.__dict__
                prior_dictionary_snapshot = dict(prior_dictionary)
                prior_suppress_context = prior.__suppress_context__

                with monkeypatch.context() as patch:
                    patch.setattr(resource, "_begin_operation", capture_begin)
                    patch.setattr(
                        transaction_module,
                        (
                            "_run_atomic_transition_apply"
                            if effect_kind == "transition"
                            else "_run_atomic_global_stop_apply"
                        ),
                        safe_result,
                    )
                    try:
                        if effect_kind == "transition":
                            session.apply_transition(transition_command)
                        else:
                            session.apply_global_stop_update(
                                global_stop_command,
                                operator_decision,
                            )
                    except SQLiteMutationStoreError as caught:
                        outward_error = caught
                    else:
                        pytest.fail("safe error did not escape")

            assert prior_reference is not None
            assert outward_error is exact_error
            assert type(outward_error) is SQLiteMutationStoreError
            assert outward_error.error_class == "mutation_failed"
            assert outward_error.args == ("mutation_failed",)
            assert outward_error.internal_detail is None
            assert outward_error.__cause__ is None
            assert outward_error.__context__ is None
            assert outward_error.__suppress_context__ is True
            assert getattr(outward_error, "__notes__", None) is None
            assert (
                writer_module._is_accepted_outward_safe_mutation_store_error(
                    outward_error
                )
                is True
            )
            assert len(correlations) == len(operations) == len(records) == 1
            assert records[0].invocation_correlation is correlations[0]
            _assert_exception_graph_has_no_coordinator_traceback(outward_error)
            _assert_exception_graph_excludes(
                outward_error,
                (
                    correlations[0],
                    operations[0],
                    operations[0]._completion_handle,
                    records[0],
                    session,
                    resource,
                    transition_command,
                    global_stop_command,
                    operator_decision,
                    private_marker,
                    connection,
                    cursor,
                    prior_reference,
                    cause,
                    context,
                ),
            )

            assert prior_reference.__traceback__ is prior_traceback
            assert prior_reference.__cause__ is prior_cause is cause
            assert prior_reference.__context__ is prior_context is context
            assert prior_reference.__suppress_context__ is prior_suppress_context
            assert prior_reference.args is prior_args
            assert prior_reference.args == ("caller-owned-prior", private_payload)
            assert prior_reference.__notes__ is prior_notes
            assert prior_reference.__notes__ == ["caller-owned-note"]
            assert prior_reference.__dict__ is prior_dictionary
            assert prior_reference.__dict__ == prior_dictionary_snapshot
            assert cause.__traceback__ is cause_traceback
            assert context.__traceback__ is context_traceback
            assert cursor.execute("SELECT 1").fetchone() == (1,)
            assert connection.execute("SELECT 2").fetchone() == (2,)
            assert resource._operation_exit_process_control_poisoned_value is False
            assert resource.active_for_owner() is True
            assert resource._mutation_slot is None
            assert resource._active_operations == {}
        finally:
            cursor.close()
            connection.close()


@pytest.mark.parametrize(
    "effect_kind",
    ("transition", "global-stop"),
    ids=("transition", "global-stop"),
)
def test_untrusted_context_bearing_safe_error_is_not_admitted_to_trusted_severance(
    effect_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        session = fixture.writer_session
        resource = session._resource
        assert type(resource.operation_guard) is types.MethodType
        unexpected_context = RuntimeError("untrusted-context")
        malformed = SQLiteMutationStoreError(
            SQLiteMutationStoreErrorCode.MUTATION_FAILED
        )
        malformed.__context__ = unexpected_context
        acceptance_results: list[bool] = []
        severance_calls: list[object] = []
        original_validator = (
            writer_module._is_accepted_outward_safe_mutation_store_error
        )

        def raise_malformed(**kwargs: object) -> object:
            assert kwargs
            raise malformed

        def observe_acceptance(error: SQLiteMutationStoreError) -> bool:
            assert error is malformed
            assert error.__context__ is unexpected_context
            assert writer_module._require_safe_mutation_store_error_payload(error) is error
            result = original_validator(error)
            acceptance_results.append(result)
            return result

        def forbidden_trusted_severance(error: SQLiteMutationStoreError) -> None:
            severance_calls.append(error)
            raise AssertionError("untrusted error entered trusted severance")

        with monkeypatch.context() as patch:
            patch.setattr(
                transaction_module,
                (
                    "_run_atomic_transition_apply"
                    if effect_kind == "transition"
                    else "_run_atomic_global_stop_apply"
                ),
                raise_malformed,
            )
            patch.setattr(
                writer_module,
                "_is_accepted_outward_safe_mutation_store_error",
                observe_acceptance,
            )
            patch.setattr(
                writer_module,
                "_raise_safe_mutation_store_error",
                forbidden_trusted_severance,
            )
            with pytest.raises(SQLiteMutationStoreError) as outward:
                if effect_kind == "transition":
                    session.apply_transition(fixture.command)
                else:
                    session.apply_global_stop_update(
                        global_stop_tests._command(),
                        global_stop_tests._decision(),
                    )

        assert outward.value is malformed
        assert acceptance_results == [False]
        assert severance_calls == []
        assert malformed.__context__ is unexpected_context
        assert original_validator(malformed) is False
        assert resource._operation_exit_process_control_poisoned_value is False
        assert resource.active_for_owner() is True
        assert resource._mutation_slot is None
        assert resource._active_operations == {}


def test_safe_failure_disposition_preserves_one_exact_content_free_error_object() -> None:
    exact_error = transaction_module._mutation_failed()
    try:
        raise exact_error
    except SQLiteMutationStoreError as caught:
        assert caught is exact_error
        disposition = transaction_module._safe_mutation_failure_disposition(caught)

    assert type(disposition) is writer_module._SafeMutationFailureDisposition
    assert disposition.error is exact_error
    assert exact_error.__traceback__ is None
    assert exact_error.__cause__ is None
    assert exact_error.__context__ is None
    assert getattr(exact_error, "__notes__", None) is None
    assert writer_module._safe_mutation_error_from_disposition(disposition) is exact_error

    with pytest.raises(SQLiteMutationStoreError) as outward:
        writer_module._raise_safe_mutation_store_error(exact_error)
    assert outward.value is exact_error
    assert outward.value.__cause__ is None
    assert outward.value.__context__ is None


def test_safe_failure_disposition_rejects_subclassed_or_content_bearing_errors() -> None:
    class StoreErrorSubclass(SQLiteMutationStoreError):
        pass

    with_detail = SQLiteMutationStoreError(
        SQLiteMutationStoreErrorCode.MUTATION_FAILED,
        internal_detail=object(),
    )
    with_note = SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)
    with_note.add_note("private")
    malformed_args = SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)
    malformed_args.args = ("mutation_failed", "private")
    wrong_code = SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)
    wrong_code.error_class = "unrecognized_mutation_error"
    wrong_code.args = ("unrecognized_mutation_error",)
    candidates = (
        StoreErrorSubclass(SQLiteMutationStoreErrorCode.MUTATION_FAILED),
        with_detail,
        with_note,
        malformed_args,
        wrong_code,
    )

    for candidate in candidates:
        disposition = transaction_module._safe_mutation_failure_disposition(candidate)
        replacement = disposition.error
        assert replacement is not candidate
        assert type(replacement) is SQLiteMutationStoreError
        assert replacement.error_class == "database_integrity_failure"
        assert replacement.args == ("database_integrity_failure",)
        assert replacement.internal_detail is None
        assert replacement.__traceback__ is None
        assert replacement.__cause__ is None
        assert replacement.__context__ is None
        assert getattr(replacement, "__notes__", None) is None


def test_exception_traceback_sanitizer_is_cycle_bounded_and_identity_preserving() -> None:
    def raised(error: BaseException) -> BaseException:
        try:
            raise error
        except BaseException as caught:
            return caught

    cause = raised(RuntimeError("cause"))
    context = raised(ValueError("context"))
    group_child = raised(KeyError("group-child"))
    nested_child = raised(OSError("nested-child"))
    opaque_child = raised(LookupError("opaque-child"))
    group = raised(ExceptionGroup("group", [group_child]))
    cycle: list[object] = []
    cycle.append(cycle)
    cycle.extend((nested_child, {"group": group}, {cause}, frozenset({context})))
    root = raised(KeyboardInterrupt("root", cycle))
    root.__cause__ = cause
    root.__context__ = context
    root.__suppress_context__ = True
    root.add_note("preserved-note")

    class Opaque:
        pass

    opaque = Opaque()
    opaque.child = opaque_child
    root.embedded = {"cycle": cycle, "opaque": opaque}

    class SlottedOpaqueError(RuntimeError):
        __slots__ = ("slotted_child",)

    slotted_child = raised(ArithmeticError("slotted-child"))
    slotted = SlottedOpaqueError("slotted")
    slotted.slotted_child = slotted_child
    root.slotted = slotted
    original_args = root.args
    original_notes = root.__notes__
    original_group_children = group.exceptions
    original_dictionary = root.__dict__

    writer_module._sanitize_exception_traceback_graph(root)

    assert all(
        error.__traceback__ is None
        for error in (root, cause, context, group, group_child, nested_child)
    )
    assert opaque_child.__traceback__ is not None
    assert root.__cause__ is cause
    assert root.__context__ is context
    assert root.__suppress_context__ is True
    assert root.args is original_args
    assert root.__notes__ is original_notes
    assert root.__notes__ == ["preserved-note"]
    assert root.__dict__ is original_dictionary
    assert group.exceptions is original_group_children
    assert slotted.__traceback__ is None
    assert slotted_child.__traceback__ is not None


HOSTILE_EXCEPTION_DESCRIPTOR_FIELDS = (
    "__traceback__",
    "__cause__",
    "__context__",
    "args",
    "__dict__",
    "__notes__",
    "exceptions",
)


def _raised_exception_for_sanitizer(error: BaseException) -> BaseException:
    try:
        raise error
    except BaseException as caught:
        return caught


def _sanitizer_fault_graph() -> tuple[object, ...]:
    cause = _raised_exception_for_sanitizer(RuntimeError("cause"))
    context = _raised_exception_for_sanitizer(ValueError("context"))
    group_child = _raised_exception_for_sanitizer(KeyError("group-child"))
    container_child = _raised_exception_for_sanitizer(OSError("container-child"))
    group = _raised_exception_for_sanitizer(
        ExceptionGroup("group", [group_child])
    )
    container: list[object] = [container_child]
    context.embedded = {"group": group, "container": container}
    root = SystemExit(73)
    root.__cause__ = cause
    root.__context__ = context
    root.__suppress_context__ = True
    root.add_note("preserved-note")
    return (
        root,
        cause,
        context,
        group,
        group_child,
        container,
        container_child,
    )


def _assert_sanitizer_fault_graph_preserved_and_scrubbed(
    graph: tuple[object, ...],
) -> None:
    (
        root,
        cause,
        context,
        group,
        group_child,
        _,
        container_child,
    ) = graph
    assert type(root) is SystemExit
    assert root.code == 73
    assert root.args == (73,)
    assert root.__cause__ is cause
    assert root.__context__ is context
    assert root.__suppress_context__ is True
    assert root.__notes__ == ["preserved-note"]
    assert isinstance(group, BaseExceptionGroup)
    assert _base_exception_group_children(group) == (group_child,)
    for error in (root, cause, context, group, group_child, container_child):
        assert isinstance(error, BaseException)
        assert _coordinator_frames_from_base_exception_storage(error) == []
        if error is not root:
            assert _base_exception_field(
                error,
                _TEST_BASE_EXCEPTION_TRACEBACK_DESCRIPTOR,
            ) is None


@pytest.mark.parametrize(
    "field_name",
    HOSTILE_EXCEPTION_DESCRIPTOR_FIELDS,
    ids=HOSTILE_EXCEPTION_DESCRIPTOR_FIELDS,
)
def test_hostile_exception_subclass_descriptors_are_not_invoked(
    field_name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    descriptor_calls: list[str] = []
    descriptor_failure = RuntimeError(f"hostile-{field_name}")

    def hostile_descriptor(instance: BaseException) -> object:
        assert isinstance(instance, BaseException)
        descriptor_calls.append(field_name)
        raise descriptor_failure

    if field_name == "exceptions":
        hostile_type = type(
            "ExternallyDefinedHostileExceptionGroup",
            (ExceptionGroup,),
            {"exceptions": property(hostile_descriptor)},
        )
        child = _raised_exception_for_sanitizer(KeyError("hostile-group-child"))
        hostile = hostile_type("hostile-group", [child])
        expected_group_children = (child,)
    else:
        hostile_type = type(
            "ExternallyDefinedHostileException",
            (RuntimeError,),
            {field_name: property(hostile_descriptor)},
        )
        hostile = hostile_type("hostile")
        child = None
        expected_group_children = None
    hostile = _raised_exception_for_sanitizer(hostile)
    hostile_dictionary = _base_exception_field(
        hostile,
        _TEST_BASE_EXCEPTION_DICTIONARY_DESCRIPTOR,
    )
    assert type(hostile_dictionary) is dict
    notes = ["hostile-note"]
    hostile_dictionary["__notes__"] = notes
    original_hostile_args = _base_exception_field(
        hostile,
        _TEST_BASE_EXCEPTION_ARGS_DESCRIPTOR,
    )
    opaque_child = _raised_exception_for_sanitizer(LookupError("opaque-slot"))
    dynamic_child = _raised_exception_for_sanitizer(IndexError("dynamic-property"))
    hostile_type.dynamic_child = property(lambda instance: dynamic_child)
    hostile_type.arbitrary_slot_claim = opaque_child

    with make_coherent_transition_fixture_for_test(
        tmp_path / field_name.replace("_", "field"),
    ) as fixture:
        session = fixture.writer_session
        resource = session._resource
        original_begin = resource._begin_operation
        operations: list[object] = []

        def capture_begin(
            owner_session: object,
            invocation_correlation: object,
        ) -> object:
            operation = original_begin(owner_session, invocation_correlation)
            operations.append(operation)
            return operation

        def hostile_delegate(**kwargs: object) -> object:
            assert kwargs
            raise hostile

        governing = SystemExit(73)
        _, guarded = _guarded_public_code("transition")
        target = (
            guarded,
            _instruction_offset(guarded, opname="WITH_EXCEPT_START"),
        )
        targets = (target,)
        with monkeypatch.context() as patch:
            patch.setattr(resource, "_begin_operation", capture_begin)
            patch.setattr(
                transaction_module,
                "_run_atomic_transition_apply",
                hostile_delegate,
            )
            tool_id, pending, reached = _arm_instruction_process_control(
                targets,
                governing,
            )
            observed: BaseException | None = None
            try:
                session.apply_transition(fixture.command)
            except BaseException as error:
                observed = error
            finally:
                _disarm_instruction_process_control(tool_id, targets)

        assert pending == [] and reached == [target]
        assert observed is governing
        assert descriptor_calls == []
        assert governing.__context__ is hostile
        assert _coordinator_frames_from_base_exception_storage(governing) == []
        assert _base_exception_field(
            hostile,
            _TEST_BASE_EXCEPTION_TRACEBACK_DESCRIPTOR,
        ) is None
        assert _base_exception_field(
            hostile,
            _TEST_BASE_EXCEPTION_ARGS_DESCRIPTOR,
        ) is original_hostile_args
        assert _base_exception_field(
            hostile,
            _TEST_BASE_EXCEPTION_DICTIONARY_DESCRIPTOR,
        ) is hostile_dictionary
        assert hostile_dictionary["__notes__"] is notes
        if expected_group_children is not None:
            assert isinstance(hostile, BaseExceptionGroup)
            assert _base_exception_group_children(hostile) == expected_group_children
            assert _base_exception_field(
                child,
                _TEST_BASE_EXCEPTION_TRACEBACK_DESCRIPTOR,
            ) is None
        assert _base_exception_field(
            dynamic_child,
            _TEST_BASE_EXCEPTION_TRACEBACK_DESCRIPTOR,
        ) is not None
        assert _base_exception_field(
            opaque_child,
            _TEST_BASE_EXCEPTION_TRACEBACK_DESCRIPTOR,
        ) is not None
        assert len(operations) == 1
        assert resource._operation_exit_process_control_poisoned
        assert resource.active_for_owner() is False
        operations[0]._close()
        session.close()


SANITIZER_FAILURE_PHASES = (
    "before-root-clearing",
    "after-root-clearing-before-context",
    "during-cause-traversal",
    "during-context-traversal",
    "during-group-child-traversal",
    "during-exact-container-traversal",
)


def _faulted_primary_sanitizer(
    phase: str,
    graph: tuple[object, ...],
) -> tuple[object, list[str]]:
    root, cause, context, _, group_child, container, _ = graph
    tripped: list[str] = []
    failure = RuntimeError(f"sanitizer-{phase}")
    original_set = writer_module._BASE_EXCEPTION_DESCRIPTOR_SET
    original_get = writer_module._BASE_EXCEPTION_DESCRIPTOR_GET
    original_type = type

    def trip() -> None:
        assert tripped == []
        tripped.append(phase)
        raise failure

    def descriptor_set(
        descriptor: object,
        current: object,
        value: object,
    ) -> object:
        if phase == "before-root-clearing" and current is root:
            trip()
        if phase == "during-cause-traversal" and current is cause:
            trip()
        if phase == "during-context-traversal" and current is context:
            trip()
        if phase == "during-group-child-traversal" and current is group_child:
            trip()
        return original_set(descriptor, current, value)

    def descriptor_get(
        descriptor: object,
        current: object,
        owner: object,
    ) -> object:
        if (
            phase == "after-root-clearing-before-context"
            and current is root
            and descriptor is writer_module._BASE_EXCEPTION_CAUSE_DESCRIPTOR
        ):
            trip()
        return original_get(descriptor, current, owner)

    def exact_type(current: object) -> type[object]:
        if phase == "during-exact-container-traversal" and current is container:
            trip()
        return original_type(current)

    def primary(exact_root: BaseException) -> None:
        writer_module._sanitize_exception_traceback_graph_pass(
            exact_root,
            _base_descriptor_get=descriptor_get,
            _base_descriptor_set=descriptor_set,
            _type=exact_type,
        )

    return primary, tripped


@pytest.mark.parametrize(
    "phase",
    SANITIZER_FAILURE_PHASES,
    ids=SANITIZER_FAILURE_PHASES,
)
def test_one_ordinary_sanitizer_core_failure_is_bounded_and_retried(
    phase: str,
    tmp_path: Path,
) -> None:
    with make_coherent_transition_fixture_for_test(
        tmp_path / phase,
    ) as fixture:
        resource = fixture.writer_session._resource
        correlation = resource._new_operation_invocation_correlation()
        operation = resource.operation_guard(
            fixture.writer_session,
            _invocation_correlation=correlation,
        )
        assert resource._stabilize_operation_exit_for_process_control(
            correlation
        ) is writer_module._OperationExitProcessControlDisposition.REPRESENTED_INCOMPLETE
        graph = _sanitizer_fault_graph()
        root = graph[0]
        assert isinstance(root, SystemExit)
        primary, tripped = _faulted_primary_sanitizer(phase, graph)

        def raise_and_sanitize() -> None:
            try:
                raise root
            except (KeyboardInterrupt, SystemExit, GeneratorExit) as governing:
                writer_module._sanitize_exception_traceback_graph(
                    governing,
                    _primary_pass=primary,
                )
                raise

        with pytest.raises(SystemExit) as outward:
            raise_and_sanitize()
        assert outward.value is root
        assert tripped == [phase]
        _assert_sanitizer_fault_graph_preserved_and_scrubbed(graph)
        assert resource._operation_exit_process_control_poisoned
        assert resource.active_for_owner() is False
        with pytest.raises(WriterSessionError):
            resource.operation_guard(fixture.writer_session)
        operation._close()
        fixture.writer_session.close()


def test_one_ordinary_failure_immediately_before_sanitizer_core_return_is_bounded(
) -> None:
    graph = _sanitizer_fault_graph()
    root = graph[0]
    assert isinstance(root, SystemExit)
    code = writer_module._sanitize_exception_traceback_graph_pass.__code__
    return_offsets = tuple(
        instruction.offset
        for instruction in dis.get_instructions(code)
        if instruction.opname in ("RETURN_VALUE", "RETURN_CONST")
    )
    assert return_offsets
    target = (code, return_offsets[-1])
    failure = RuntimeError("sanitizer-before-core-return")
    tool_id, pending, reached = _arm_instruction_process_control((target,), failure)
    try:
        writer_module._sanitize_exception_traceback_graph(root)
    finally:
        _disarm_instruction_process_control(tool_id, (target,))
    assert pending == [] and reached == [target]
    _assert_sanitizer_fault_graph_preserved_and_scrubbed(graph)


@pytest.mark.parametrize(
    "effect_kind",
    ("transition", "global-stop"),
    ids=("transition", "global-stop"),
)
def test_public_primary_sanitizer_call_boundary_failure_preserves_process_control(
    effect_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for kind in PROCESS_CONTROL_KINDS:
        with make_coherent_transition_fixture_for_test(
            tmp_path / effect_kind / kind,
        ) as fixture:
            session = fixture.writer_session
            resource = session._resource
            original_begin = resource._begin_operation
            operations: list[object] = []
            correlations: list[object] = []

            def capture_begin(
                owner_session: object,
                invocation_correlation: object,
            ) -> object:
                operation = original_begin(owner_session, invocation_correlation)
                operations.append(operation)
                correlations.append(invocation_correlation)
                return operation

            failure = _entry_process_control_for_kind(kind)
            graph = _sanitizer_fault_graph()
            _, cause, context, group, group_child, _, container_child = graph
            failure.__cause__ = cause
            failure.__context__ = context
            failure.__suppress_context__ = True
            failure.add_note("boundary-note")
            original_args = failure.args
            original_notes = failure.__notes__
            original_group_children = _base_exception_group_children(group)
            boundary_failures: list[BaseException] = []

            def fail_at_primary_call_boundary(root: BaseException) -> None:
                assert root is failure
                injected = RuntimeError("primary-sanitizer-call-boundary")
                boundary_failures.append(injected)
                raise injected

            targets = _public_exit_targets(
                effect_kind,
                "after-operation-admission",
            )
            with monkeypatch.context() as patch:
                patch.setattr(resource, "_begin_operation", capture_begin)
                patch.setattr(
                    writer_module,
                    "_sanitize_exception_traceback_graph",
                    fail_at_primary_call_boundary,
                )
                tool_id, pending, reached = _arm_instruction_process_control(
                    targets,
                    failure,
                )
                observed: BaseException | None = None
                try:
                    if effect_kind == "transition":
                        session.apply_transition(fixture.command)
                    else:
                        session.apply_global_stop_update(
                            global_stop_tests._command(),
                            global_stop_tests._decision(),
                        )
                except BaseException as error:
                    observed = error
                finally:
                    _disarm_instruction_process_control(tool_id, targets)

            assert pending == [] and reached == list(targets)
            assert observed is failure
            assert type(observed) is type(failure)
            assert observed.args is original_args
            if type(observed) is SystemExit:
                assert observed.code == 73
            assert observed.__cause__ is cause
            assert observed.__context__ is context
            assert observed.__suppress_context__ is True
            assert observed.__notes__ is original_notes
            assert observed.__notes__ == ["boundary-note"]
            assert len(boundary_failures) == 1
            assert boundary_failures[0] is not observed
            assert _base_exception_group_children(group) is original_group_children
            for error in (observed, cause, context, group, group_child, container_child):
                assert _coordinator_frames(error) == []
            assert len(operations) == len(correlations) == 1
            record = _operation_record_for_test(
                resource,
                operations[0]._completion_handle,
            )
            _assert_exception_graph_excludes(
                observed,
                (
                    correlations[0],
                    operations[0],
                    operations[0]._completion_handle,
                    record,
                    resource,
                    session,
                    fixture.command,
                ),
            )
            assert resource._operation_exit_process_control_poisoned
            assert resource.active_for_owner() is False
            operations[0]._close()
            session.close()


@pytest.mark.parametrize(
    "effect_kind",
    ("transition", "global-stop"),
    ids=("transition", "global-stop"),
)
def test_genuine_bound_safe_error_primary_sanitizer_failure_preserves_exact_error(
    effect_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        session = fixture.writer_session
        resource = session._resource
        original_begin = resource._begin_operation
        correlations: list[object] = []
        operations: list[object] = []
        records: list[object] = []

        def capture_begin(
            owner_session: object,
            invocation_correlation: object,
        ) -> object:
            operation = original_begin(owner_session, invocation_correlation)
            correlations.append(invocation_correlation)
            operations.append(operation)
            records.append(
                _operation_record_for_test(
                    resource,
                    operation._completion_handle,
                )
            )
            return operation

        exact_error = transaction_module._mutation_failed()
        disposition = transaction_module._safe_mutation_failure_disposition(
            exact_error
        )

        def safe_result(**kwargs: object) -> object:
            assert kwargs
            return disposition

        sanitizer_failures: list[RuntimeError] = []

        def fail_at_primary_call_boundary(root: BaseException) -> None:
            assert root is exact_error
            injected = RuntimeError("safe-error-sanitizer-call-boundary")
            sanitizer_failures.append(injected)
            raise injected

        with monkeypatch.context() as patch:
            patch.setattr(resource, "_begin_operation", capture_begin)
            patch.setattr(
                transaction_module,
                (
                    "_run_atomic_transition_apply"
                    if effect_kind == "transition"
                    else "_run_atomic_global_stop_apply"
                ),
                safe_result,
            )
            patch.setattr(
                writer_module,
                "_sanitize_exception_traceback_graph",
                fail_at_primary_call_boundary,
            )
            with pytest.raises(SQLiteMutationStoreError) as outward:
                if effect_kind == "transition":
                    session.apply_transition(fixture.command)
                else:
                    session.apply_global_stop_update(
                        global_stop_tests._command(),
                        global_stop_tests._decision(),
                    )

        error = outward.value
        assert error is exact_error
        assert type(error) is SQLiteMutationStoreError
        assert error.error_class == "mutation_failed"
        assert error.args == ("mutation_failed",)
        assert error.internal_detail is None
        assert error.__cause__ is None
        assert error.__context__ is None
        assert getattr(error, "__notes__", None) is None
        assert len(sanitizer_failures) == 1
        assert _coordinator_frames(error) == []
        assert len(correlations) == len(operations) == len(records) == 1
        _assert_exception_graph_excludes(
            error,
            (
                correlations[0],
                operations[0],
                operations[0]._completion_handle,
                records[0],
                session,
                resource,
                fixture.command,
            ),
        )
        assert resource._operation_exit_process_control_poisoned_value is False
        assert resource.active_for_owner() is True
        session.close()


def test_governing_process_control_bypasses_safe_failure_disposition_by_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failure = KeyboardInterrupt()

    def interrupt(*args: object, **kwargs: object) -> object:
        raise failure

    with make_coherent_transition_fixture_for_test(
        tmp_path,
        ready_dependency=True,
    ) as fixture:
        monkeypatch.setattr(
            transaction_module._CoordinatorMutationTransactionController,
            "run_atomic_transition_apply",
            interrupt,
        )
        with fixture.writer_session._resource.operation_guard(
            fixture.writer_session
        ) as operation:
            with pytest.raises(KeyboardInterrupt) as raised:
                transaction_module._run_atomic_transition_apply(
                    operation_lease=operation,
                    transition_command=fixture.command,
                )
        assert raised.value is failure
        assert fixture.writer_session.active is True
        assert fixture.writer_session._resource._mutation_slot is None
        assert fixture.writer_session._resource._active_operations == {}


@pytest.mark.parametrize("underlying_commit", (False, True))
def test_transition_same_wrapper_uncertainty_retry_uses_fresh_operation_and_connection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    underlying_commit: bool,
) -> None:
    with make_coherent_transition_fixture_for_test(
        tmp_path,
        ready_dependency=True,
    ) as fixture:
        resource = fixture.writer_session._resource
        operations: list[object] = []
        connections: list[sqlite3.Connection] = []
        commit_calls = 0
        original_guard = resource.operation_guard
        original_open = transaction_module._open_bound_existing_sqlite_connection
        original_commit = transaction_module._commit_transaction

        def capture_guard(session: object) -> object:
            operation = original_guard(session)
            operations.append(operation)
            return operation

        def capture_open(*args: object, **kwargs: object) -> sqlite3.Connection:
            connection = original_open(*args, **kwargs)
            connections.append(connection)
            return connection

        def uncertain_commit(connection: sqlite3.Connection) -> None:
            nonlocal commit_calls
            commit_calls += 1
            if underlying_commit:
                connection.execute("COMMIT")
            raise RuntimeError("transaction commit observation unavailable")

        monkeypatch.setattr(resource, "operation_guard", capture_guard)
        monkeypatch.setattr(
            transaction_module,
            "_open_bound_existing_sqlite_connection",
            capture_open,
        )
        monkeypatch.setattr(transaction_module, "_commit_transaction", uncertain_commit)

        with pytest.raises(SQLiteMutationStoreError) as uncertain:
            fixture.writer_session.apply_transition(fixture.command)
        assert uncertain.value.error_class == "commit_outcome_unknown"
        assert commit_calls == 1
        assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
        assert resource._mutation_slot is None
        assert resource._active_operations == {}
        assert transition_event_count_for_test(fixture) == int(underlying_commit)
        with pytest.raises(sqlite3.ProgrammingError):
            connections[0].execute("SELECT 1")

        monkeypatch.setattr(transaction_module, "_commit_transaction", original_commit)
        retried = fixture.writer_session.apply_transition(fixture.command)
        assert type(retried) is CommittedTransition
        assert retried.replayed is underlying_commit
        assert commit_calls == 1
        assert len(operations) == 2
        assert operations[0] is not operations[1]
        assert len(connections) == 2
        assert connections[0] is not connections[1]
        for connection in connections:
            with pytest.raises(sqlite3.ProgrammingError):
                connection.execute("SELECT 1")
        assert transition_event_count_for_test(fixture) == 1
        assert tuple(
            envelope.event_sequence
            for envelope in transition_tests._transition_event_envelopes(fixture)
        ) == (0,)

        if underlying_commit:
            changed = transition_tests._fresh_block_command(
                fixture.command,
                expected_version=fixture.command.expected_version,
                key=fixture.command.idempotency_key,
            )
            conflict = fixture.writer_session.apply_transition(changed)
            assert type(conflict).__name__ == "TransitionConflict"
            assert conflict.conflict_class == "idempotency_key_reuse_conflict"
            assert transition_event_count_for_test(fixture) == 1


@pytest.mark.parametrize("underlying_commit", (False, True))
def test_global_stop_same_wrapper_uncertainty_retry_uses_fresh_operation_and_connection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    underlying_commit: bool,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        decision = global_stop_tests._decision()
        command = global_stop_tests._command(decision_ref=decision.decision_ref)
        global_stop_tests._seed_receipt(fixture, decision)
        global_stop_tests._patch_clock(monkeypatch)
        resource = fixture.writer_session._resource
        operations: list[object] = []
        connections: list[sqlite3.Connection] = []
        commit_calls = 0
        original_guard = resource.operation_guard
        original_open = transaction_module._open_bound_existing_sqlite_connection
        original_commit = transaction_module._commit_transaction

        def capture_guard(session: object) -> object:
            operation = original_guard(session)
            operations.append(operation)
            return operation

        def capture_open(*args: object, **kwargs: object) -> sqlite3.Connection:
            connection = original_open(*args, **kwargs)
            connections.append(connection)
            return connection

        def uncertain_commit(connection: sqlite3.Connection) -> None:
            nonlocal commit_calls
            commit_calls += 1
            if underlying_commit:
                connection.execute("COMMIT")
            raise RuntimeError("global-stop commit observation unavailable")

        monkeypatch.setattr(resource, "operation_guard", capture_guard)
        monkeypatch.setattr(
            transaction_module,
            "_open_bound_existing_sqlite_connection",
            capture_open,
        )
        monkeypatch.setattr(transaction_module, "_commit_transaction", uncertain_commit)

        with pytest.raises(SQLiteMutationStoreError) as uncertain:
            fixture.writer_session.apply_global_stop_update(command, decision)
        assert uncertain.value.error_class == "commit_outcome_unknown"
        assert commit_calls == 1
        assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
        assert resource._mutation_slot is None
        assert resource._active_operations == {}
        assert global_stop_event_count_for_test(fixture) == int(underlying_commit)
        with pytest.raises(sqlite3.ProgrammingError):
            connections[0].execute("SELECT 1")

        monkeypatch.setattr(transaction_module, "_commit_transaction", original_commit)
        retried = fixture.writer_session.apply_global_stop_update(command, decision)
        assert type(retried) is CommittedGlobalStopUpdate
        assert retried.replayed is underlying_commit
        assert commit_calls == 1
        assert len(operations) == 2
        assert operations[0] is not operations[1]
        assert len(connections) == 2
        assert connections[0] is not connections[1]
        for connection in connections:
            with pytest.raises(sqlite3.ProgrammingError):
                connection.execute("SELECT 1")
        assert global_stop_event_count_for_test(fixture) == 1
        assert tuple(
            envelope.event_sequence
            for envelope in global_stop_tests._global_stop_event_envelopes(fixture)
        ) == (0,)

        if underlying_commit:
            changed = global_stop_tests._command(
                key=command.idempotency_key,
                expected_version=command.expected_version,
                decision_ref=decision.decision_ref,
                stop_id="global-stop-vs1a-changed",
            )
            conflict = fixture.writer_session.apply_global_stop_update(changed, decision)
            assert type(conflict).__name__ == "GlobalStopConflict"
            assert conflict.conflict_class == "idempotency_key_reuse_conflict"
            assert global_stop_event_count_for_test(fixture) == 1


@pytest.mark.parametrize(
    "effect_kind",
    ("transition", "global-stop"),
    ids=("transition", "global-stop"),
)
@pytest.mark.parametrize(
    "kind",
    PROCESS_CONTROL_KINDS,
    ids=PROCESS_CONTROL_KINDS,
)
def test_underlying_commit_process_control_scrubs_coordinator_traceback_and_replays_once(
    effect_kind: str,
    kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(
        tmp_path,
        ready_dependency=True,
    ) as fixture:
        command: object = fixture.command
        decision: object | None = None
        if effect_kind == "global-stop":
            decision = global_stop_tests._decision()
            command = global_stop_tests._command(
                decision_ref=decision.decision_ref,
            )
            global_stop_tests._seed_receipt(fixture, decision)
            global_stop_tests._patch_clock(monkeypatch)

        resource = fixture.writer_session._resource
        captured_connections: list[sqlite3.Connection] = []
        captured_operations: list[object] = []
        captured_correlations: list[object] = []
        original_open = transaction_module._open_bound_existing_sqlite_connection
        original_begin = resource._begin_operation

        def capture_open(*args: object, **kwargs: object) -> sqlite3.Connection:
            connection = original_open(*args, **kwargs)
            captured_connections.append(connection)
            return connection

        def capture_begin(
            owner_session: object,
            invocation_correlation: object,
        ) -> object:
            operation = original_begin(owner_session, invocation_correlation)
            captured_operations.append(operation)
            captured_correlations.append(invocation_correlation)
            return operation

        failure = _entry_process_control_for_kind(kind)

        def commit_then_interrupt(connection: sqlite3.Connection) -> object:
            connection.execute("COMMIT")
            raise failure

        with monkeypatch.context() as patch:
            patch.setattr(
                transaction_module,
                "_open_bound_existing_sqlite_connection",
                capture_open,
            )
            patch.setattr(resource, "_begin_operation", capture_begin)
            patch.setattr(
                transaction_module,
                "_commit_transaction",
                commit_then_interrupt,
            )
            observed: BaseException | None = None
            try:
                if effect_kind == "transition":
                    fixture.writer_session.apply_transition(command)
                else:
                    assert decision is not None
                    fixture.writer_session.apply_global_stop_update(
                        command,
                        decision,
                    )
            except BaseException as error:
                observed = error

        assert observed is failure
        _assert_exact_process_control_object(observed, failure)
        _assert_exception_graph_has_no_coordinator_traceback(observed)
        assert observed.__cause__ is None
        assert observed.__context__ is None
        assert getattr(observed, "__notes__", None) in (None, [])
        assert len(captured_connections) == 1
        assert len(captured_operations) == len(captured_correlations) == 1
        _assert_exception_graph_excludes(
            observed,
            tuple(
                item
                for item in (
                    captured_connections[0],
                    captured_operations[0],
                    captured_operations[0]._completion_handle,
                    captured_correlations[0],
                    resource,
                    fixture.writer_session,
                    command,
                    decision,
                )
                if item is not None
            ),
        )
        with pytest.raises(sqlite3.ProgrammingError):
            captured_connections[0].execute("SELECT 1")
        if effect_kind == "transition":
            assert transition_event_count_for_test(fixture) == 1
        else:
            assert global_stop_event_count_for_test(fixture) == 1

        observed = None
        failure.__traceback__ = None
        fixture.writer_session.close()
        replay_session = acquire_sqlite_writer_session(fixture.location)
        try:
            if effect_kind == "transition":
                replay = replay_session.apply_transition(command)
                assert type(replay) is CommittedTransition
                assert transition_event_count_for_test(fixture) == 1
            else:
                assert decision is not None
                replay = replay_session.apply_global_stop_update(
                    command,
                    decision,
                )
                assert type(replay) is CommittedGlobalStopUpdate
                assert global_stop_event_count_for_test(fixture) == 1
            assert replay.replayed is True
        finally:
            replay_session.close()


def test_bounded_privacy_traversal_is_cycle_aware_and_does_not_follow_attributes() -> None:
    secret = object()
    cycle: list[object] = []
    nested = {"a": (cycle, {"b": frozenset({secret})})}
    cycle.append(nested)
    assert _builtin_container_reaches_identity(nested, (secret,)) is True

    class Box:
        pass

    box = Box()
    box.secret = secret
    assert _builtin_container_reaches_identity(box, (secret,)) is False


def test_preservation_transition_nominal_success_and_exact_replay(
    tmp_path: Path,
) -> None:
    with make_coherent_transition_fixture_for_test(
        tmp_path,
        ready_dependency=True,
    ) as fixture:
        committed = fixture.writer_session.apply_transition(fixture.command)
        replay = fixture.writer_session.apply_transition(fixture.command)
        assert type(committed) is CommittedTransition
        assert type(replay) is CommittedTransition
        assert committed.replayed is False
        assert replay.replayed is True
        assert replay.event == committed.event
        assert replay.record == committed.record
        assert transition_event_count_for_test(fixture) == 1


def test_preservation_global_stop_nominal_success_and_exact_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with make_coherent_transition_fixture_for_test(tmp_path) as fixture:
        decision = global_stop_tests._decision()
        command = global_stop_tests._command(decision_ref=decision.decision_ref)
        global_stop_tests._seed_receipt(fixture, decision)
        global_stop_tests._patch_clock(monkeypatch)
        committed = fixture.writer_session.apply_global_stop_update(command, decision)
        replay = fixture.writer_session.apply_global_stop_update(command, decision)
        assert type(committed) is CommittedGlobalStopUpdate
        assert type(replay) is CommittedGlobalStopUpdate
        assert committed.replayed is False
        assert replay.replayed is True
        assert replay.event == committed.event
        assert replay.state == committed.state
        assert global_stop_event_count_for_test(fixture) == 1


def test_preservation_rollback_only_controller_returns_session_to_active(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    controller = transaction_module._CoordinatorMutationTransactionController(
        key=transaction_module._CONTROLLER_CONSTRUCTION_KEY,
        operation_lease=operation,
    )
    assert controller.run() is writer_module._WriterIssuanceMatch.MATCH
    assert resource._mutation_slot is None
    assert len(resource._active_operations) == 1
    operation._close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
    session.close()


def test_preservation_sections_1_through_36_are_byte_exact() -> None:
    data = DURABLE_DOC_PATH.read_bytes()
    marker = b"## 37. C2B Pre-I/O VS1A Shared Cleanup Foundation"
    assert data.count(marker) == 1
    prefix = data.split(marker, 1)[0]
    assert prefix.endswith(b"\n\n")
    assert hashlib.sha256(prefix[:-1]).hexdigest() == SECTIONS_1_TO_36_SHA256


def test_preservation_program_initialization_and_durable_rows_remain_absent(
    tmp_path: Path,
) -> None:
    # The committed node ID is preserved; VS1B changes its direct oracle from
    # source absence to private-source presence while fresh schema rows remain empty.
    assert (
        ROOT / "src/ge_nwp_coordinator/_development_program_initialization_contracts.py"
    ).exists()
    assert (
        ROOT / "src/ge_nwp_coordinator/_sqlite_development_program_initialization.py"
    ).exists()
    location = _location(tmp_path)
    initialize_database(location)
    connection = sqlite3.connect(location.database_path)
    try:
        assert connection.execute(
            "SELECT COUNT(*) FROM development_program_heads"
        ).fetchone() == (0,)
        assert connection.execute(
            "SELECT COUNT(*) FROM development_mutation_receipts"
        ).fetchone() == (0,)
    finally:
        connection.close()


def test_selected_source_removes_every_rejected_mechanism() -> None:
    connection_source = CONNECTION_PATH.read_text(encoding="utf-8")
    transaction_source = TRANSACTION_PATH.read_text(encoding="utf-8")
    writer_source = WRITER_PATH.read_text(encoding="utf-8")
    combined = connection_source + transaction_source + writer_source
    for rejected in (
        "_RetainedSQLiteConnectionSnapshot",
        "_ConnectionResolutionEscrow",
        "_ConnectionResolutionAcknowledgment",
        "_ControllerConnectionResolutionHandle",
        "_WriterSessionLifecycleSnapshot",
        "cleanup_steps_completed",
    ):
        assert rejected not in combined
    retained_close = inspect.getsource(
        connection_module._RetainedSQLiteConnection._close_with_proof
    )
    assert "in_transaction" not in retained_close
    assert "ProgrammingError" not in retained_close
    claim_source = inspect.getsource(
        writer_module._WriterSessionResource._install_cleanup_claim_locked
    )
    assert "get_ident" not in claim_source
    begin_source = inspect.getsource(
        writer_module._WriterSessionResource._begin_operation
    )
    assert begin_source.index("_FINALIZER_FACTORY(") < begin_source.index(
        "self._lifecycle_state = successor"
    )
    resolution_fields = set(
        writer_module._WriterSessionControllerResolution.__dataclass_fields__
    )
    assert "connection" not in resolution_fields


def test_controller_disposal_after_resolution_before_publication_selects_cleanup_under_resource_lock(
    tmp_path: Path,
) -> None:
    parts = _new_scope(tmp_path)
    _, session, resource, operation, mutation, _, scope = parts
    scope.activate()
    started = threading.Event()
    finished = threading.Event()

    def dispose() -> None:
        started.set()
        session.close()
        finished.set()

    closer = threading.Thread(target=dispose)
    closer.start()
    assert started.wait(2)
    with resource._condition:
        assert resource._condition.wait_for(
            lambda: (
                type(resource._lifecycle_state)
                is writer_module._WriterSessionControllerResolution
                and type(resource._lifecycle_state.policy)
                is writer_module._CleanupRequiredAfterResolution
            ),
            timeout=2,
        )
    assert scope.close_after_commit(commit_succeeded=True, force_cleanup=False)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitKnownPendingCleanup
    mutation._close()
    operation._close()
    closer.join(2)
    assert not closer.is_alive() and finished.is_set()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


def test_controller_resolution_cleanup_required_is_stabilizer_cleanup_owned(
    tmp_path: Path,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, resource, operation, _, _, scope = parts
    scope.activate()
    record = _operation_record_for_test(
        resource,
        operation._completion_handle,
    )
    with resource._condition:
        resource._freeze_admission_locked()
        cleanup_resolution = resource._lifecycle_state
        assert type(cleanup_resolution) is writer_module._WriterSessionControllerResolution
        assert type(cleanup_resolution.policy) is writer_module._CleanupRequiredAfterResolution

    disposition = resource._stabilize_operation_exit_for_process_control(
        record.invocation_correlation,
    )
    assert disposition is (
        writer_module._OperationExitProcessControlDisposition.REPRESENTED_CLEANUP_OWNED
    )
    assert resource._operation_exit_process_control_poisoned_value
    with resource._condition:
        resource._lifecycle_state = cleanup_resolution
        resource._operation_exit_process_control_poisoned_value = False
    _finish_scope(parts)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


def test_controller_disposal_while_publication_waits_for_resource_lock_selects_cleanup(
    tmp_path: Path,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, resource, _, _, _, scope = parts
    scope.activate()
    locked = threading.Event()
    release = threading.Event()

    def hold_disposal_lock() -> None:
        with resource._condition:
            resource._freeze_admission_locked()
            locked.set()
            assert release.wait(2)

    disposer = threading.Thread(target=hold_disposal_lock)
    disposer.start()
    assert locked.wait(2)
    release.set()
    assert scope.close_after_commit(commit_succeeded=True, force_cleanup=False)
    disposer.join(2)
    assert not disposer.is_alive()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitKnownPendingCleanup
    _finish_scope(parts)


def test_controller_publication_failure_before_assignment_preserves_scope_until_exact_acknowledgment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, resource, _, _, _, scope = parts
    activation = scope.activate()
    original = writer_module._WriterSessionResource._select_controller_successor_locked
    calls = 0

    def fail_before_assignment(self: object, *args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        if calls <= 2:
            raise RuntimeError("before-publication")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(
        writer_module._WriterSessionResource,
        "_select_controller_successor_locked",
        fail_before_assignment,
    )
    with pytest.raises(RuntimeError, match="before-publication"):
        scope.close_after_commit(commit_succeeded=True, force_cleanup=False)
    assert resource._lifecycle_state is activation.resolution
    assert scope._resolved is False
    assert scope._retained_connection is not None
    monkeypatch.setattr(
        writer_module._WriterSessionResource,
        "_select_controller_successor_locked",
        original,
    )
    assert scope.close_after_commit(commit_succeeded=True, force_cleanup=False)
    assert scope._resolved is True
    assert type(scope._publication_acknowledgment) is writer_module._ControllerSuccessorPublicationAcknowledgment
    _finish_scope(parts)


def test_controller_cleanup_publication_allows_mutation_operation_and_explicit_close_to_complete(
    tmp_path: Path,
) -> None:
    parts = _new_scope(tmp_path)
    _, session, resource, operation, mutation, _, scope = parts
    scope.activate()
    assert scope.close_after_commit(commit_succeeded=True, force_cleanup=True)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitKnownPendingCleanup
    mutation._close()
    operation._close()
    session.close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


def _assert_production_post_publication_process_control(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: BaseException,
) -> None:
    original = transaction_module._ControllerConnectionScope._accept_publication_acknowledgment
    raised = False

    def interrupt_after_ack(
        self: object,
        acknowledgment: object,
        facts: object,
    ) -> None:
        nonlocal raised
        original(self, acknowledgment, facts)
        if not raised:
            raised = True
            raise failure

    monkeypatch.setattr(
        transaction_module._ControllerConnectionScope,
        "_accept_publication_acknowledgment",
        interrupt_after_ack,
    )
    with make_coherent_transition_fixture_for_test(
        tmp_path,
        ready_dependency=True,
    ) as fixture:
        resource = fixture.writer_session._resource
        with pytest.raises(type(failure)) as captured:
            fixture.writer_session.apply_transition(fixture.command)
        assert captured.value is failure
        if type(failure) is SystemExit:
            assert captured.value.code == failure.code
        assert type(resource._lifecycle_state) not in (
            writer_module._WriterSessionActive,
            writer_module._WriterSessionOperationsActive,
            writer_module._WriterSessionMutationActive,
            writer_module._WriterSessionControllerCloseProved,
            writer_module._WriterSessionControllerCloseProvedReleased,
        )
        assert resource._mutation_slot is None
        assert resource._active_operations == {}


def test_production_transition_post_publication_keyboardinterrupt_forces_cleanup_before_operation_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_production_post_publication_process_control(
        tmp_path, monkeypatch, KeyboardInterrupt()
    )


def test_production_transition_post_publication_systemexit_forces_cleanup_before_operation_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_production_post_publication_process_control(
        tmp_path, monkeypatch, SystemExit(73)
    )


def test_production_transition_post_publication_generatorexit_forces_cleanup_before_operation_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_production_post_publication_process_control(
        tmp_path, monkeypatch, GeneratorExit()
    )


def test_keyboardinterrupt_after_exact_mutation_release_before_operation_completion_cannot_restore_active(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_process_control_after_exact_mutation_release(
        tmp_path,
        monkeypatch,
        KeyboardInterrupt(),
    )


def test_systemexit_after_exact_mutation_release_before_operation_completion_preserves_exact_object_code_and_cannot_restore_active(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_process_control_after_exact_mutation_release(
        tmp_path,
        monkeypatch,
        SystemExit(73),
    )


def test_generatorexit_after_exact_mutation_release_before_operation_completion_cannot_restore_active(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_process_control_after_exact_mutation_release(
        tmp_path,
        monkeypatch,
        GeneratorExit(),
    )


def test_local_stabilization_failure_cannot_replace_governing_process_control_or_restore_active(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parts = _prepare_close_proved_with_blocker(tmp_path)
    _, session, resource, operation, mutation, _, _, blocker = parts
    handle = operation._completion_handle
    governing = KeyboardInterrupt()
    local = RuntimeError("local-stabilization")
    original_release = resource._release_mutation_slot
    original_prepare = resource._prepare_operation_retirement
    interrupted = False

    def release_then_interrupt(**kwargs: object) -> bool:
        nonlocal interrupted
        released = original_release(**kwargs)
        assert released is True
        if not interrupted:
            interrupted = True
            assert type(resource._lifecycle_state) is writer_module._WriterSessionControllerCloseProvedReleased
            raise governing
        return released

    def fail_local_completion(exact_handle: object) -> object:
        assert exact_handle is handle
        raise local

    monkeypatch.setattr(resource, "_release_mutation_slot", release_then_interrupt)
    monkeypatch.setattr(
        resource,
        "_prepare_operation_retirement",
        fail_local_completion,
    )
    with pytest.raises(KeyboardInterrupt) as captured:
        with operation:
            mutation._close()
    assert captured.value is governing
    assert captured.value is not local
    assert handle.cleanup_required is True
    assert operation._closed is False
    assert operation._finalizer.alive is True
    assert type(resource._lifecycle_state) is writer_module._WriterSessionControllerCloseProvedReleased
    assert handle in _state_operations_for_test(resource)
    assert resource.active_for_owner() is False
    with pytest.raises(WriterSessionError):
        resource.operation_guard(session)

    monkeypatch.setattr(
        resource,
        "_prepare_operation_retirement",
        original_prepare,
    )
    operation._close()
    assert handle not in _state_operations_for_test(resource)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitKnownPendingCleanup
    _finish_pending_with_blocker(
        session=session,
        resource=resource,
        blocker=blocker,
    )


def test_process_control_during_first_operation_completion_restores_structure_and_retries_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parts = _prepare_close_proved_with_blocker(tmp_path)
    _, session, resource, operation, mutation, _, _, blocker = parts
    mutation._close()
    handle = operation._completion_handle
    governing = KeyboardInterrupt()
    original_successor = resource._state_after_operation_completion
    interrupted = False

    def successor_then_interrupt(*args: object, **kwargs: object) -> object:
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            raise governing
        return original_successor(*args, **kwargs)

    monkeypatch.setattr(
        resource,
        "_state_after_operation_completion",
        successor_then_interrupt,
    )
    with pytest.raises(KeyboardInterrupt) as captured:
        operation._close()
    assert captured.value is governing
    assert interrupted is True
    assert handle.cleanup_required is True
    assert operation._closed is True
    assert operation._finalizer.alive is False
    assert type(resource._lifecycle_state) is writer_module._WriterSessionControllerCloseProvedReleased
    assert handle in _state_operations_for_test(resource)
    operation._close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitKnownPendingCleanup
    assert handle not in _state_operations_for_test(resource)
    assert blocker._completion_handle in _state_operations_for_test(resource)
    _finish_pending_with_blocker(
        session=session,
        resource=resource,
        blocker=blocker,
    )


def test_operation_finalizer_is_cleanup_only_and_never_calls_normal_publisher(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parts = _prepare_close_proved_with_blocker(tmp_path)
    _, session, resource, operation, mutation, _, _, blocker = parts
    mutation._close()
    handle = operation._completion_handle
    original_publish = resource._publish_prepared_operation_retirement
    calls = 0

    def interrupt_before_publication(*args: object) -> None:
        nonlocal calls
        calls += 1
        original_publish(*args)

    monkeypatch.setattr(
        resource,
        "_publish_prepared_operation_retirement",
        interrupt_before_publication,
    )
    assert operation._finalizer.alive is True
    operation._finalizer()
    assert calls == 0
    assert operation._finalizer.alive is False
    assert handle.cleanup_required is True
    assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitKnownPendingCleanup
    assert handle not in _state_operations_for_test(resource)
    assert blocker._completion_handle in _state_operations_for_test(resource)
    monkeypatch.setattr(
        resource,
        "_publish_prepared_operation_retirement",
        original_publish,
    )
    assert operation._closed is True
    assert operation._session is session
    operation._close()
    assert handle not in _state_operations_for_test(resource)
    assert type(resource._lifecycle_state) is not writer_module._WriterSessionActive
    _finish_pending_with_blocker(
        session=session,
        resource=resource,
        blocker=blocker,
    )


def test_disposal_after_exact_mutation_release_before_operation_completion_remains_nonadmitting_and_reaches_terminal_x(
    tmp_path: Path,
) -> None:
    parts = _prepare_close_proved_with_blocker(tmp_path)
    _, session, resource, operation, mutation, _, _, blocker = parts
    handle = operation._completion_handle
    mutation._close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionControllerCloseProvedReleased
    assert resource._mutation_slot is None
    assert handle in _state_operations_for_test(resource)

    released = threading.Event()
    disposal_current = threading.Event()
    allow_disposer_return = threading.Event()
    thread_failures: list[BaseException] = []

    def make_disposal_current() -> None:
        try:
            assert released.wait(2)
            with resource._condition:
                assert type(resource._lifecycle_state) is writer_module._WriterSessionControllerCloseProvedReleased
                resource._freeze_admission_locked()
                disposal_current.set()
                assert allow_disposer_return.wait(2)
        except BaseException as error:
            thread_failures.append(error)
            disposal_current.set()

    disposer = threading.Thread(target=make_disposal_current)
    disposer.start()
    released.set()
    assert disposal_current.wait(2)
    assert thread_failures == []
    assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitKnownPendingCleanup
    assert handle in _state_operations_for_test(resource)
    assert blocker._completion_handle in _state_operations_for_test(resource)
    allow_disposer_return.set()
    disposer.join(2)
    assert not disposer.is_alive()
    assert thread_failures == []
    assert resource.active_for_owner() is False
    with pytest.raises(WriterSessionError):
        resource.operation_guard(session)

    operation._close()
    assert handle not in _state_operations_for_test(resource)
    assert blocker._completion_handle in _state_operations_for_test(resource)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitKnownPendingCleanup
    with pytest.raises(WriterSessionError):
        resource.operation_guard(session)
    _finish_pending_with_blocker(
        session=session,
        resource=resource,
        blocker=blocker,
    )
    with pytest.raises(WriterSessionError):
        resource.operation_guard(session)


def test_post_publication_resume_active_is_atomically_replaced_by_cleanup_direction(
    tmp_path: Path,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, resource, _, _, _, scope = parts
    scope.activate()
    assert scope.close_after_commit(commit_succeeded=True, force_cleanup=False)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionControllerCloseProved
    with resource._condition:
        resource._freeze_admission_locked()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionCommitKnownPendingCleanup
    _finish_scope(parts)


def test_operation_completion_after_forced_cleanup_cannot_restore_active(
    tmp_path: Path,
) -> None:
    parts = _new_scope(tmp_path)
    _, session, resource, operation, mutation, _, scope = parts
    scope.activate()
    assert scope.close_after_commit(commit_succeeded=False, force_cleanup=True)
    mutation._close()
    operation._close()
    assert type(resource._lifecycle_state) not in (
        writer_module._WriterSessionActive,
        writer_module._WriterSessionOperationsActive,
        writer_module._WriterSessionMutationActive,
    )
    session.close()


def test_no_resume_active_is_constructed_before_exact_close_proof(
    tmp_path: Path,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, resource, _, _, _, scope = parts
    activation = scope.activate()
    assert resource._lifecycle_state is activation.resolution
    assert type(activation.resolution.policy) is writer_module._ResumeIfCloseProvedAndStillEligible
    assert not any(
        type(value) is writer_module._ResumeActive
        for value in activation.resolution.__dict__.values()
    ) if hasattr(activation.resolution, "__dict__") else True
    _finish_scope(parts)


def test_resume_active_is_field_free_proof_gated_and_cannot_reach_slot_or_cleanup_cursor() -> None:
    assert writer_module._ResumeActive.__dataclass_fields__ == {}
    assert writer_module._ResumeActive.__slots__ == ()
    resume = writer_module._ResumeActive()
    for name in ("slot", "connection", "close_proof", "cleanup", "cursor", "claim"):
        assert not hasattr(resume, name)
    with pytest.raises(TypeError):
        writer_module._ResumeActive(object())


def test_controller_resolution_policy_strengthens_only_from_resume_if_eligible_to_cleanup_required(
    tmp_path: Path,
) -> None:
    parts = _new_scope(tmp_path)
    _, _, resource, _, _, _, scope = parts
    scope.activate()
    assert type(resource._lifecycle_state.policy) is writer_module._ResumeIfCloseProvedAndStillEligible
    with resource._condition:
        resource._freeze_admission_locked()
        first = resource._lifecycle_state
        resource._freeze_admission_locked()
        second = resource._lifecycle_state
    assert type(first.policy) is writer_module._CleanupRequiredAfterResolution
    assert type(second.policy) is writer_module._CleanupRequiredAfterResolution
    _finish_scope(parts)


def test_continue_cleanup_remains_nonadmitting(tmp_path: Path) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    with resource._condition:
        resource._freeze_admission_locked()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionOrdinaryCleanup
    assert type(resource._lifecycle_state.cleanup) is writer_module._ContinueCleanup
    with pytest.raises(WriterSessionError):
        resource.operation_guard(session)
    session.close()


def test_operation_completion_after_resume_requires_prior_exact_mutation_release(
    tmp_path: Path,
) -> None:
    parts = _new_scope(tmp_path)
    _, session, resource, operation, mutation, _, scope = parts
    scope.activate()
    assert scope.close_after_commit(commit_succeeded=True, force_cleanup=False)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionControllerCloseProved
    operation._close()
    assert type(resource._lifecycle_state) not in (
        writer_module._WriterSessionActive,
        writer_module._WriterSessionOperationsActive,
        writer_module._WriterSessionMutationActive,
    )
    mutation._close()
    session.close()


def test_closed_variants_reject_cross_wired_authority_activity_and_mutation_slot() -> None:
    identity = _new_test_resource_identity()
    first = writer_module._OperationCompletionHandle(
        identity, 1, os.getpid(), threading.get_ident(), 1
    )
    clone = writer_module._OperationCompletionHandle(
        identity, 1, os.getpid(), threading.get_ident(), 1
    )
    assert first is not clone and first != clone
    authority = object.__new__(writer_module._WriterSessionAuthority)
    object.__setattr__(authority, "resource_identity", identity)
    record = object.__new__(writer_module._WriterSessionOperationRecord)
    object.__setattr__(record, "handle", first)
    activity = object.__new__(writer_module._WriterSessionActivity)
    object.__setattr__(activity, "authority", authority)
    object.__setattr__(activity, "operation_records", (record,))
    slot = writer_module._WriterSessionMutationSlot(
        operation=clone,
        token=writer_module._WriterSessionMutationToken(),
    )
    with pytest.raises(ValueError):
        writer_module._WriterSessionMutationFrame(activity, slot)


def test_two_real_same_epoch_resources_reject_cross_wired_activity(
    tmp_path: Path,
) -> None:
    parts = _two_real_resource_frames(tmp_path)
    _, _, _, _, operation_a, operation_b, _, _, frame_a, frame_b = parts
    try:
        same_resource = writer_module._WriterSessionActivity(
            frame_a.activity.authority,
            (frame_a.activity.operation_records[0],),
        )
        assert same_resource.authority.resource_identity is operation_a._completion_handle.resource_identity
        with pytest.raises(ValueError, match="invalid writer activity"):
            writer_module._WriterSessionActivity(
                frame_a.activity.authority,
                (frame_b.activity.operation_records[0],),
            )
    finally:
        _finish_two_real_resource_frames(parts)


def test_two_real_same_epoch_resources_reject_cross_wired_mutation_frame(
    tmp_path: Path,
) -> None:
    parts = _two_real_resource_frames(tmp_path)
    _, _, _, _, _, _, _, _, frame_a, frame_b = parts
    try:
        same_resource = writer_module._WriterSessionMutationFrame(
            frame_a.activity,
            frame_a.slot,
        )
        assert same_resource.slot is frame_a.slot
        with pytest.raises(ValueError, match="invalid mutation frame"):
            writer_module._WriterSessionMutationFrame(
                frame_a.activity,
                frame_b.slot,
            )
    finally:
        _finish_two_real_resource_frames(parts)


def test_two_real_same_epoch_resources_reject_cross_wired_cleanup_cursor(
    tmp_path: Path,
) -> None:
    parts = _two_real_resource_frames(tmp_path)
    _, _, _, _, _, _, _, _, frame_a, frame_b = parts
    try:
        same_resource = writer_module._CleanupBeforeR1WithSlot(
            frame_a.activity,
            frame_a.slot,
        )
        assert same_resource.resource_identity is frame_a.activity.authority.resource_identity
        with pytest.raises(ValueError, match="invalid cleanup cursor"):
            writer_module._CleanupBeforeR1WithSlot(
                frame_a.activity,
                frame_b.slot,
            )
    finally:
        _finish_two_real_resource_frames(parts)


def test_two_real_same_epoch_resources_reject_cross_wired_unproved_state(
    tmp_path: Path,
) -> None:
    parts = _two_real_resource_frames(tmp_path)
    _, _, _, _, operation_a, operation_b, _, _, frame_a, frame_b = parts
    connection_a = sqlite3.connect(":memory:")
    connection_b = sqlite3.connect(":memory:")
    retained_a = connection_module._make_retained_sqlite_connection(
        connection_a,
        operation_a._completion_handle.resource_identity,
    )
    retained_b = connection_module._make_retained_sqlite_connection(
        connection_b,
        operation_b._completion_handle.resource_identity,
    )
    try:
        token_a = writer_module._ControllerScopeToken(
            retained_a,
            operation_a._completion_handle,
        )
        token_b = writer_module._ControllerScopeToken(
            retained_b,
            operation_b._completion_handle,
        )
        cleanup_a = writer_module._ContinueCleanup(
            writer_module._CleanupBeforeR1WithSlot(
                frame_a.activity,
                frame_a.slot,
            )
        )
        cleanup_b = writer_module._ContinueCleanup(
            writer_module._CleanupBeforeR1WithSlot(
                frame_b.activity,
                frame_b.slot,
            )
        )
        same_resource = writer_module._WriterSessionCommitUncertainUnproved(
            token_a,
            retained_a,
            cleanup_a,
        )
        assert same_resource.cleanup is cleanup_a
        with pytest.raises(ValueError, match="invalid controller-resolution state"):
            writer_module._WriterSessionControllerResolution(
                frame_a,
                token_b,
                writer_module._ResumeIfCloseProvedAndStillEligible(),
            )
        with pytest.raises(ValueError, match="invalid close-unproved state"):
            writer_module._WriterSessionCommitUncertainUnproved(
                token_b,
                retained_b,
                cleanup_a,
            )
        with pytest.raises(ValueError, match="invalid close-unproved state"):
            writer_module._WriterSessionCommitUncertainUnproved(
                token_a,
                retained_a,
                cleanup_b,
            )
        proof_a = retained_a._close_with_proof()
        proof_b = retained_b._close_with_proof()
        same_proved_resource = writer_module._WriterSessionCommitUncertainPendingCleanup(
            token_a,
            proof_a,
            cleanup_a,
        )
        assert same_proved_resource.close_proof is proof_a
        with pytest.raises(ValueError, match="invalid close-proved cleanup state"):
            writer_module._WriterSessionCommitUncertainPendingCleanup(
                token_b,
                proof_b,
                cleanup_a,
            )
        claim_a = writer_module._WriterSessionCleanupClaim(
            token=writer_module._CleanupClaimToken(),
            owner_thread_ref=weakref.ref(threading.current_thread()),
            resource_identity=operation_a._completion_handle.resource_identity,
            owner_pid=os.getpid(),
            lifecycle_epoch=1,
            claim_epoch=1,
        )
        claim_b = writer_module._WriterSessionCleanupClaim(
            token=writer_module._CleanupClaimToken(),
            owner_thread_ref=weakref.ref(threading.current_thread()),
            resource_identity=operation_b._completion_handle.resource_identity,
            owner_pid=os.getpid(),
            lifecycle_epoch=1,
            claim_epoch=1,
        )
        claimed = writer_module._WriterSessionCleanupClaimed(
            same_resource,
            claim_a,
        )
        assert claimed.claim is claim_a
        with pytest.raises(ValueError, match="invalid claimed-cleanup state"):
            writer_module._WriterSessionCleanupClaimed(
                same_resource,
                claim_b,
            )
    finally:
        retained_a._close_with_proof()
        retained_b._close_with_proof()
        _finish_two_real_resource_frames(parts)


def test_operation_completion_disposition_is_monotonic_payload_free_and_nonserializable(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    with resource._condition:
        assert handle.cleanup_required is False
    assert resource._mark_operation_cleanup_required(handle) is True
    assert resource._mark_operation_cleanup_required(handle) is True
    with resource._condition:
        assert handle.cleanup_required is True
    with pytest.raises(AttributeError):
        handle._cleanup_required = False
    with resource._condition:
        assert handle.cleanup_required is True
    assert not any(
        name in handle.__slots__
        for name in ("exception", "traceback", "args", "code", "payload")
    )
    with pytest.raises(TypeError):
        handle.__reduce__()
    operation._close()
    assert type(resource._lifecycle_state) is not writer_module._WriterSessionActive
    session.close()


def _process_control_for_kind(kind: str) -> BaseException:
    if kind == "keyboard-interrupt":
        return KeyboardInterrupt()
    if kind == "system-exit-73":
        return SystemExit(73)
    if kind == "generator-exit":
        return GeneratorExit()
    raise AssertionError("unknown process-control kind")


def _entry_process_control_for_kind(kind: str) -> BaseException:
    if kind == "keyboard-interrupt":
        return KeyboardInterrupt("entry")
    if kind == "system-exit-73":
        return SystemExit(73)
    if kind == "generator-exit":
        return GeneratorExit("entry")
    raise AssertionError("unknown process-control kind")


def _assert_exact_process_control(
    captured: pytest.ExceptionInfo[BaseException],
    exact: BaseException,
) -> None:
    assert captured.value is exact
    assert type(captured.value) is type(exact)
    assert captured.value.args == exact.args
    if type(exact) is SystemExit:
        assert captured.value.code == 73


def _instruction_offset(
    code: types.CodeType,
    *,
    opname: str,
    argval: object = None,
    occurrence: int = 0,
) -> int:
    matches = [
        instruction.offset
        for instruction in dis.get_instructions(code)
        if instruction.opname == opname
        and (argval is None or instruction.argval == argval)
    ]
    assert len(matches) > occurrence
    return matches[occurrence]


def _operation_guard_return_boundary_offset(code: types.CodeType) -> int:
    """Return the first instruction after the operation-guard call."""

    instructions = list(dis.get_instructions(code))
    guard_load = next(
        index
        for index, instruction in reversed(tuple(enumerate(instructions)))
        if instruction.opname == "LOAD_ATTR"
        and instruction.argval == "operation_guard"
    )
    call_index = next(
        index
        for index in range(guard_load + 1, len(instructions))
        if instructions[index].opname in ("CALL", "CALL_FUNCTION_EX")
    )
    boundary = instructions[call_index + 1]
    assert boundary.opname == "BEFORE_WITH"
    return boundary.offset


def _first_instruction_offset(code: types.CodeType) -> int:
    return next(
        instruction.offset
        for instruction in dis.get_instructions(code)
        if instruction.opname not in {"COPY_FREE_VARS", "MAKE_CELL", "RESUME"}
    )


def _arm_instruction_process_control(
    targets: tuple[tuple[types.CodeType, int], ...],
    failure: BaseException,
) -> tuple[int, list[tuple[types.CodeType, int]], list[tuple[types.CodeType, int]]]:
    assert targets
    tool_id = next(
        candidate
        for candidate in range(5, -1, -1)
        if sys.monitoring.get_tool(candidate) is None
    )
    pending = list(targets)
    reached: list[tuple[types.CodeType, int]] = []

    def callback(code: types.CodeType, instruction_offset: int) -> None:
        if pending and pending[0] == (code, instruction_offset):
            reached.append(pending.pop(0))
            raise failure

    sys.monitoring.use_tool_id(tool_id, "vs1a-exit-envelope-test")
    sys.monitoring.register_callback(
        tool_id,
        sys.monitoring.events.INSTRUCTION,
        callback,
    )
    for code in {target[0] for target in targets}:
        sys.monitoring.set_local_events(
            tool_id,
            code,
            sys.monitoring.events.INSTRUCTION,
        )
    return tool_id, pending, reached


def _arm_instruction_process_control_with_hook(
    targets: tuple[tuple[types.CodeType, int], ...],
    failure: BaseException,
    hook: object,
) -> tuple[int, list[tuple[types.CodeType, int]], list[tuple[types.CodeType, int]]]:
    assert targets and callable(hook)
    tool_id = next(
        candidate
        for candidate in range(5, -1, -1)
        if sys.monitoring.get_tool(candidate) is None
    )
    pending = list(targets)
    reached: list[tuple[types.CodeType, int]] = []

    def callback(code: types.CodeType, instruction_offset: int) -> None:
        if pending and pending[0] == (code, instruction_offset):
            reached.append(pending.pop(0))
            hook()  # type: ignore[operator]
            raise failure

    sys.monitoring.use_tool_id(tool_id, "vs1a-post-poison-fault-test")
    sys.monitoring.register_callback(
        tool_id,
        sys.monitoring.events.INSTRUCTION,
        callback,
    )
    for code in {target[0] for target in targets}:
        sys.monitoring.set_local_events(
            tool_id,
            code,
            sys.monitoring.events.INSTRUCTION,
        )
    return tool_id, pending, reached


def _disarm_instruction_process_control(
    tool_id: int,
    targets: tuple[tuple[types.CodeType, int], ...],
) -> None:
    for code in {target[0] for target in targets}:
        sys.monitoring.set_local_events(tool_id, code, 0)
    sys.monitoring.register_callback(
        tool_id,
        sys.monitoring.events.INSTRUCTION,
        None,
    )
    sys.monitoring.free_tool_id(tool_id)


PUBLIC_EXIT_BOUNDARIES = (
    "after-operation-admission",
    "first-caller-envelope-opcode",
    "compiler-normal-with-cleanup",
    "compiler-exceptional-with-cleanup",
    "operation-exit-first-opcode",
    "operation-close-call-setup",
    "operation-close-first-opcode",
    "operation-owner-pid-check",
    "first-phase-one-action",
    "poison-publication",
    "detailed-cleanup-local-failure",
    "post-poison-normal-lease-close",
    "immediately-before-final-assignment",
    "immediately-after-final-assignment",
    "first-final-publication-notification",
)


def _guarded_public_code(effect_kind: str) -> tuple[types.CodeType, types.CodeType]:
    public = getattr(
        writer_module._SQLiteWriterSession,
        "apply_transition" if effect_kind == "transition" else "apply_global_stop_update",
    ).__code__
    guarded = next(
        constant
        for constant in public.co_consts
        if type(constant) is types.CodeType
        and constant.co_name.startswith("_guarded_")
    )
    return public, guarded


def _normal_operation_close_setup_offset() -> int:
    instructions = list(
        dis.get_instructions(writer_module._WriterSessionOperationLease.__exit__)
    )
    close_loads = [
        index
        for index, instruction in enumerate(instructions)
        if instruction.opname == "LOAD_ATTR" and instruction.argval == "_close"
    ]
    assert len(close_loads) == 2
    return instructions[close_loads[-1] - 1].offset


def _final_assignment_offsets() -> tuple[int, int]:
    instructions = list(
        dis.get_instructions(
            writer_module._WriterSessionResource._publish_prepared_operation_retirement
        )
    )
    assignment_index = next(
        index
        for index, instruction in enumerate(instructions)
        if instruction.opname == "STORE_ATTR"
        and instruction.argval == "_lifecycle_state"
    )
    return (
        instructions[assignment_index].offset,
        instructions[assignment_index + 1].offset,
    )


def _public_exit_targets(
    effect_kind: str,
    boundary: str,
) -> tuple[tuple[types.CodeType, int], ...]:
    public, guarded = _guarded_public_code(effect_kind)
    normal_cleanup = _instruction_offset(guarded, opname="SWAP")
    before_assignment, after_assignment = _final_assignment_offsets()
    if boundary == "after-operation-admission":
        return ((guarded, _operation_guard_return_boundary_offset(guarded)),)
    if boundary == "first-caller-envelope-opcode":
        return ((public, dis.Bytecode(public).exception_entries[0].start),)
    if boundary in (
        "compiler-normal-with-cleanup",
        "detailed-cleanup-local-failure",
        "post-poison-normal-lease-close",
    ):
        return ((guarded, normal_cleanup),)
    if boundary == "compiler-exceptional-with-cleanup":
        return (
            (
                guarded,
                _instruction_offset(guarded, opname="WITH_EXCEPT_START"),
            ),
        )
    if boundary == "operation-exit-first-opcode":
        code = writer_module._WriterSessionOperationLease.__exit__.__code__
        return ((code, _first_instruction_offset(code)),)
    if boundary == "operation-close-call-setup":
        code = writer_module._WriterSessionOperationLease.__exit__.__code__
        return ((code, _normal_operation_close_setup_offset()),)
    if boundary == "operation-close-first-opcode":
        code = writer_module._WriterSessionOperationLease._close.__code__
        return ((code, _first_instruction_offset(code)),)
    if boundary == "operation-owner-pid-check":
        code = writer_module._WriterSessionOperationLease._close.__code__
        return (
            (
                code,
                _instruction_offset(code, opname="LOAD_FAST", argval="self"),
            ),
        )
    if boundary == "first-phase-one-action":
        code = writer_module._WriterSessionResource._prepare_operation_retirement.__code__
        return ((code, _first_instruction_offset(code)),)
    if boundary == "poison-publication":
        poison_code = (
            writer_module._WriterSessionResource
            ._stabilize_operation_exit_for_process_control.__code__
        )
        return (
            (guarded, normal_cleanup),
            (
                poison_code,
                _instruction_offset(
                    poison_code,
                    opname="STORE_ATTR",
                    argval="_operation_exit_process_control_poisoned_value",
                ),
            ),
        )
    if boundary == "immediately-before-final-assignment":
        code = (
            writer_module._WriterSessionResource
            ._publish_prepared_operation_retirement.__code__
        )
        return ((code, before_assignment),)
    if boundary == "immediately-after-final-assignment":
        code = (
            writer_module._WriterSessionResource
            ._publish_prepared_operation_retirement.__code__
        )
        return ((code, after_assignment),)
    if boundary == "first-final-publication-notification":
        code = (
            writer_module._WriterSessionResource
            ._notify_operation_retirement_waiters_locked.__code__
        )
        return ((code, _first_instruction_offset(code)),)
    raise AssertionError("unknown public exit boundary")


def _assert_exact_process_control_object(
    observed: BaseException,
    exact: BaseException,
) -> None:
    assert observed is exact
    assert type(observed) is type(exact)
    assert observed.args == exact.args
    if type(exact) is SystemExit:
        assert observed.code == 73


@pytest.mark.parametrize(
    "effect_kind",
    ("transition", "global-stop"),
    ids=("transition", "global-stop"),
)
@pytest.mark.parametrize(
    "boundary",
    PUBLIC_EXIT_BOUNDARIES,
    ids=PUBLIC_EXIT_BOUNDARIES,
)
def test_public_retained_lease_exit_envelope_matrix(
    effect_kind: str,
    boundary: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for kind in PROCESS_CONTROL_KINDS:
        case_root = tmp_path / effect_kind / boundary / kind
        with make_coherent_transition_fixture_for_test(case_root) as fixture:
            session = fixture.writer_session
            resource = session._resource
            operations: list[object] = []
            correlations: list[object] = []
            admitted_records: list[object] = []
            original_guard = resource.operation_guard
            cleanup_failure_reached = False

            original_begin = resource._begin_operation

            def capture_begin(
                owner_session: object,
                invocation_correlation: object,
            ) -> object:
                operation = original_begin(
                    owner_session,
                    invocation_correlation,
                )
                correlations.append(invocation_correlation)
                operations.append(operation)
                admitted_records.append(
                    _operation_record_for_test(
                        resource,
                        operation._completion_handle,
                    )
                )
                return operation

            def successful_delegate(**kwargs: object) -> object:
                assert kwargs
                return object()

            body_cause = ValueError("body failure cause")
            body_failure = RuntimeError("body failure before exceptional cleanup")

            def exceptional_delegate(**kwargs: object) -> object:
                assert kwargs
                try:
                    raise body_cause
                except ValueError:
                    raise body_failure from body_cause

            failure = _entry_process_control_for_kind(kind)
            targets = _public_exit_targets(effect_kind, boundary)
            tool_id = -1
            pending: list[tuple[types.CodeType, int]] = []
            reached: list[tuple[types.CodeType, int]] = []
            with monkeypatch.context() as patch:
                patch.setattr(resource, "_begin_operation", capture_begin)
                delegate = (
                    exceptional_delegate
                    if boundary == "compiler-exceptional-with-cleanup"
                    else successful_delegate
                )
                if effect_kind == "transition":
                    patch.setattr(
                        transaction_module,
                        "_run_atomic_transition_apply",
                        delegate,
                    )
                else:
                    patch.setattr(
                        transaction_module,
                        "_run_atomic_global_stop_apply",
                        delegate,
                    )
                if boundary == "detailed-cleanup-local-failure":
                    original_replace = (
                        resource._state_with_replaced_operation_record_locked
                    )

                    def fail_detailed_replacement(*args: object) -> object:
                        nonlocal cleanup_failure_reached
                        if resource._operation_exit_process_control_poisoned_value:
                            cleanup_failure_reached = True
                            raise RuntimeError("post-poison detailed cleanup failure")
                        return original_replace(*args)

                    patch.setattr(
                        resource,
                        "_state_with_replaced_operation_record_locked",
                        fail_detailed_replacement,
                    )

                tool_id, pending, reached = _arm_instruction_process_control(
                    targets,
                    failure,
                )
                observed: BaseException | None = None
                try:
                    if effect_kind == "transition":
                        session.apply_transition(fixture.command)
                    else:
                        session.apply_global_stop_update(
                            global_stop_tests._command(),
                            global_stop_tests._decision(),
                        )
                except BaseException as error:
                    observed = error
                finally:
                    _disarm_instruction_process_control(tool_id, targets)

            assert pending == []
            assert reached == list(targets)
            assert observed is not None
            _assert_exact_process_control_object(observed, failure)
            _assert_exception_graph_has_no_coordinator_traceback(observed)
            assert observed.__cause__ is None
            if boundary == "compiler-exceptional-with-cleanup":
                assert observed.__context__ is body_failure
                assert str(observed.__context__) == (
                    "body failure before exceptional cleanup"
                )
                assert observed.__context__.__traceback__ is None
                assert observed.__context__.__cause__ is body_cause
                assert body_cause.__traceback__ is None
            else:
                assert observed.__context__ is None
            assert getattr(observed, "__notes__", None) in (None, [])
            observed = None
            failure.__traceback__ = None

            no_admission = boundary == "first-caller-envelope-opcode"
            post_linearized = boundary in (
                "immediately-after-final-assignment",
                "first-final-publication-notification",
            )
            if no_admission:
                assert operations == []
                assert resource._active_operations == {}
                assert not resource._operation_exit_process_control_poisoned
                assert resource.active_for_owner()
                followup = original_guard(session)
                followup._close()
                session.close()
                assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
                continue

            assert len(operations) == 1
            operation = operations[0]
            handle = operation._completion_handle
            assert len(correlations) == 1
            assert len(admitted_records) == 1
            assert admitted_records[0].invocation_correlation is correlations[0]
            if post_linearized:
                assert handle not in _state_operations_for_test(resource)
                assert not resource._operation_exit_process_control_poisoned
                assert resource.active_for_owner()
                final_state = resource._lifecycle_state
                operation._close()
                assert resource._lifecycle_state is final_state
                followup = original_guard(session)
                followup._close()
                assert resource.active_for_owner()
                session.close()
                assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
                continue

            assert handle in _state_operations_for_test(resource)
            assert resource._operation_exit_process_control_poisoned
            assert not resource.active_for_owner()
            with pytest.raises(WriterSessionError):
                original_guard(session)
            with pytest.raises(WriterSessionError):
                operation._acquire_mutation_lease()
            if boundary == "detailed-cleanup-local-failure":
                assert cleanup_failure_reached
                record = _operation_record_for_test(resource, handle)
                assert record.cleanup_required is False
                assert handle.cleanup_required is True
            operation._close()
            assert handle not in _state_operations_for_test(resource)
            session.close()
            assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


@pytest.mark.parametrize(
    "effect_kind",
    ("transition", "global-stop"),
    ids=("transition", "global-stop"),
)
def test_ordinary_invalid_preflight_process_control_context_graph_is_sanitized(
    effect_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for kind in PROCESS_CONTROL_KINDS:
        with make_coherent_transition_fixture_for_test(
            tmp_path / effect_kind / kind,
        ) as fixture:
            session = fixture.writer_session
            resource = session._resource
            original_begin = resource._begin_operation
            original_sanitize = writer_module._sanitize_exception_traceback_graph
            operations: list[object] = []
            correlations: list[object] = []
            pre_sanitize_contexts: list[BaseException | None] = []

            def capture_begin(
                owner_session: object,
                invocation_correlation: object,
            ) -> object:
                operation = original_begin(owner_session, invocation_correlation)
                operations.append(operation)
                correlations.append(invocation_correlation)
                return operation

            def capture_sanitize(root: BaseException) -> None:
                pre_sanitize_contexts.append(root.__context__)
                original_sanitize(root)

            failure = _entry_process_control_for_kind(kind)
            targets = _public_exit_targets(
                effect_kind,
                "compiler-exceptional-with-cleanup",
            )
            with monkeypatch.context() as patch:
                patch.setattr(resource, "_begin_operation", capture_begin)
                patch.setattr(
                    writer_module,
                    "_sanitize_exception_traceback_graph",
                    capture_sanitize,
                )
                tool_id, pending, reached = _arm_instruction_process_control(
                    targets,
                    failure,
                )
                observed: BaseException | None = None
                try:
                    if effect_kind == "transition":
                        session.apply_transition(object())
                    else:
                        session.apply_global_stop_update(object(), object())
                except BaseException as error:
                    observed = error
                finally:
                    _disarm_instruction_process_control(tool_id, targets)

            assert pending == [] and reached == list(targets)
            assert observed is failure
            assert len(pre_sanitize_contexts) == 1
            assert observed.__context__ is pre_sanitize_contexts[0]
            assert type(observed.__context__).__name__ in (
                "TransitionApplyPreflightError",
                "GlobalStopApplyPreflightError",
            )
            assert observed.__context__.__traceback__ is None
            _assert_exception_graph_has_no_coordinator_traceback(observed)
            assert len(operations) == len(correlations) == 1
            record = _operation_record_for_test(
                resource,
                operations[0]._completion_handle,
            )
            _assert_exception_graph_excludes(
                observed,
                (
                    correlations[0],
                    operations[0],
                    operations[0]._completion_handle,
                    record,
                    resource,
                    session,
                    fixture.command,
                ),
            )
            if type(failure) is SystemExit:
                assert failure.code == 73
            operations[0]._close()
            session.close()
            assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


@pytest.mark.parametrize(
    ("helper_name", "failure_mode"),
    (
        ("_state_authority", "first"),
        ("_state_authority", "both"),
        ("_state_operation_records", "first"),
        ("_state_operation_records", "both"),
        ("_operation_blocks_admission", "first"),
        ("_operation_blocks_admission", "both"),
    ),
    ids=(
        "state-authority-first-attempt",
        "state-authority-both-attempts",
        "state-records-first-attempt",
        "state-records-both-attempts",
        "operation-policy-first-attempt",
        "operation-policy-both-attempts",
    ),
)
def test_public_stabilization_helper_failures_occur_only_after_direct_poison(
    helper_name: str,
    failure_mode: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for effect_kind in ("transition", "global-stop"):
        for kind in PROCESS_CONTROL_KINDS:
            with make_coherent_transition_fixture_for_test(
                tmp_path / helper_name / failure_mode / effect_kind / kind,
            ) as fixture:
                session = fixture.writer_session
                resource = session._resource
                original_begin = resource._begin_operation
                original_helper = getattr(writer_module, helper_name)
                operations: list[object] = []
                correlations: list[object] = []
                poison_at_helper: list[bool] = []
                helper_calls = 0
                failure_enabled = False

                def capture_begin(
                    owner_session: object,
                    invocation_correlation: object,
                ) -> object:
                    operation = original_begin(
                        owner_session,
                        invocation_correlation,
                    )
                    operations.append(operation)
                    correlations.append(invocation_correlation)
                    return operation

                def faulted_helper(*args: object, **kwargs: object) -> object:
                    nonlocal helper_calls
                    assert args and not kwargs
                    if not failure_enabled:
                        return original_helper(*args)
                    helper_calls += 1
                    poison_at_helper.append(
                        resource._operation_exit_process_control_poisoned_value
                    )
                    if failure_mode == "both" or helper_calls == 1:
                        raise RuntimeError(
                            f"post-poison-{helper_name}-{failure_mode}"
                        )
                    return original_helper(*args)

                def enable_failure() -> None:
                    nonlocal failure_enabled
                    failure_enabled = True

                failure = _entry_process_control_for_kind(kind)
                targets = _public_exit_targets(
                    effect_kind,
                    "after-operation-admission",
                )
                with monkeypatch.context() as patch:
                    patch.setattr(resource, "_begin_operation", capture_begin)
                    patch.setattr(writer_module, helper_name, faulted_helper)
                    tool_id, pending, reached = (
                        _arm_instruction_process_control_with_hook(
                            targets,
                            failure,
                            enable_failure,
                        )
                    )
                    observed: BaseException | None = None
                    try:
                        if effect_kind == "transition":
                            session.apply_transition(fixture.command)
                        else:
                            session.apply_global_stop_update(
                                global_stop_tests._command(),
                                global_stop_tests._decision(),
                            )
                    except BaseException as error:
                        observed = error
                    finally:
                        _disarm_instruction_process_control(tool_id, targets)

                assert pending == [] and reached == list(targets)
                assert observed is failure
                _assert_exact_process_control_object(observed, failure)
                _assert_exception_graph_has_no_coordinator_traceback(observed)
                expected_helper_calls = (
                    (
                        4
                        if helper_name == "_state_authority"
                        else 3
                    )
                    if helper_name in ("_state_authority", "_state_operation_records")
                    and failure_mode == "first"
                    else 2
                )
                assert helper_calls == expected_helper_calls
                assert poison_at_helper == [True] * expected_helper_calls
                assert len(operations) == len(correlations) == 1
                record = _operation_record_for_test(
                    resource,
                    operations[0]._completion_handle,
                )
                assert record.invocation_correlation is correlations[0]
                assert record.cleanup_required is (failure_mode == "first")
                assert resource._operation_exit_process_control_poisoned_value
                assert resource.active_for_owner() is False
                with pytest.raises(WriterSessionError):
                    resource.operation_guard(session)
                operations[0]._close()
                session.close()
                assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


@pytest.mark.parametrize(
    "effect_kind",
    ("transition", "global-stop"),
    ids=("transition", "global-stop"),
)
def test_public_stabilization_notification_failure_remains_poisoned_and_private(
    effect_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for kind in PROCESS_CONTROL_KINDS:
        with make_coherent_transition_fixture_for_test(
            tmp_path / effect_kind / kind,
        ) as fixture:
            session = fixture.writer_session
            resource = session._resource
            original_begin = resource._begin_operation
            original_notify = resource._condition.notify_all
            operations: list[object] = []
            correlations: list[object] = []
            poison_at_notification: list[bool] = []
            failure_enabled = False

            def capture_begin(
                owner_session: object,
                invocation_correlation: object,
            ) -> object:
                operation = original_begin(owner_session, invocation_correlation)
                operations.append(operation)
                correlations.append(invocation_correlation)
                return operation

            def fail_notification() -> None:
                if failure_enabled:
                    poison_at_notification.append(
                        resource._operation_exit_process_control_poisoned_value
                    )
                    raise RuntimeError("post-poison-notification-failure")
                original_notify()

            def enable_failure() -> None:
                nonlocal failure_enabled
                failure_enabled = True

            failure = _entry_process_control_for_kind(kind)
            targets = _public_exit_targets(
                effect_kind,
                "after-operation-admission",
            )
            with monkeypatch.context() as patch:
                patch.setattr(resource, "_begin_operation", capture_begin)
                patch.setattr(resource._condition, "notify_all", fail_notification)
                tool_id, pending, reached = (
                    _arm_instruction_process_control_with_hook(
                        targets,
                        failure,
                        enable_failure,
                    )
                )
                observed: BaseException | None = None
                try:
                    if effect_kind == "transition":
                        session.apply_transition(fixture.command)
                    else:
                        session.apply_global_stop_update(
                            global_stop_tests._command(),
                            global_stop_tests._decision(),
                        )
                except BaseException as error:
                    observed = error
                finally:
                    _disarm_instruction_process_control(tool_id, targets)

            assert pending == [] and reached == list(targets)
            assert observed is failure
            _assert_exact_process_control_object(observed, failure)
            _assert_exception_graph_has_no_coordinator_traceback(observed)
            assert poison_at_notification == [True, True]
            assert len(operations) == len(correlations) == 1
            record = _operation_record_for_test(
                resource,
                operations[0]._completion_handle,
            )
            assert record.invocation_correlation is correlations[0]
            assert record.cleanup_required is True
            assert resource._operation_exit_process_control_poisoned_value
            assert resource.active_for_owner() is False
            operations[0]._close()
            session.close()
            assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


def test_exact_invocation_stabilizer_classifies_only_current_resource_records(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource

    assert resource._stabilize_operation_exit_for_process_control(None) is (
        writer_module._OperationExitProcessControlDisposition.INVALID_OR_WRONG_RESOURCE
    )
    assert not resource._operation_exit_process_control_poisoned

    correlation = resource._new_operation_invocation_correlation()
    operation = resource.operation_guard(
        session,
        _invocation_correlation=correlation,
    )
    handle = operation._completion_handle
    record = _operation_record_for_test(resource, handle)
    assert record.invocation_correlation is correlation
    assert resource._stabilize_operation_exit_for_process_control(correlation) is (
        writer_module._OperationExitProcessControlDisposition.REPRESENTED_INCOMPLETE
    )
    assert resource._operation_exit_process_control_poisoned
    with pytest.raises(WriterSessionError):
        resource.operation_guard(session)
    with pytest.raises(WriterSessionError):
        operation._acquire_mutation_lease()
    operation._close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
    session.close()

    second_location = CoordinatorStateLocation.from_trusted_root(
        tmp_path / "linearized-state"
    )
    initialize_database(second_location)
    second_session = acquire_sqlite_writer_session(second_location)
    second_resource = second_session._resource
    completed_correlation = (
        second_resource._new_operation_invocation_correlation()
    )
    completed = second_resource.operation_guard(
        second_session,
        _invocation_correlation=completed_correlation,
    )
    completed._close()
    final_state = second_resource._lifecycle_state
    assert type(final_state) is writer_module._WriterSessionActive
    assert second_resource._stabilize_operation_exit_for_process_control(
        completed_correlation
    ) is writer_module._OperationExitProcessControlDisposition.NOT_CURRENTLY_REPRESENTED
    assert second_resource._lifecycle_state is final_state
    assert not second_resource._operation_exit_process_control_poisoned
    followup = second_resource.operation_guard(second_session)
    followup._close()
    second_session.close()


def test_invocation_correlation_invalid_wrong_unrepresented_and_duplicate_do_not_select_another_operation(
    tmp_path: Path,
) -> None:
    location_a = CoordinatorStateLocation.from_trusted_root(tmp_path / "state-a")
    location_b = CoordinatorStateLocation.from_trusted_root(tmp_path / "state-b")
    initialize_database(location_a)
    initialize_database(location_b)
    session_a = acquire_sqlite_writer_session(location_a)
    session_b = acquire_sqlite_writer_session(location_b)
    resource_a = session_a._resource
    resource_b = session_b._resource
    represented = resource_a._new_operation_invocation_correlation()
    unrepresented = resource_a._new_operation_invocation_correlation()
    wrong_resource = resource_b._new_operation_invocation_correlation()
    operation = resource_a.operation_guard(
        session_a,
        _invocation_correlation=represented,
    )
    try:
        record = _operation_record_for_test(
            resource_a,
            operation._completion_handle,
        )
        assert record.invocation_correlation is represented
        for invalid in (None, object(), wrong_resource):
            assert resource_a._stabilize_operation_exit_for_process_control(
                invalid
            ) is (
                writer_module._OperationExitProcessControlDisposition
                .INVALID_OR_WRONG_RESOURCE
            )
        assert resource_a._stabilize_operation_exit_for_process_control(
            unrepresented
        ) is (
            writer_module._OperationExitProcessControlDisposition
            .NOT_CURRENTLY_REPRESENTED
        )
        assert record.cleanup_required is False
        assert not resource_a._operation_exit_process_control_poisoned
        assert resource_a.active_for_owner()
        with pytest.raises(ValueError, match="invalid operation invocation correlation"):
            resource_a.operation_guard(
                session_a,
                _invocation_correlation=represented,
            )
        assert record.cleanup_required is False
        assert not resource_a._operation_exit_process_control_poisoned
        assert resource_a.active_for_owner()
    finally:
        operation._close()
        session_a.close()
        session_b.close()


def test_invocation_correlation_cleanup_owned_is_exact_and_fail_closed(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    correlation = resource._new_operation_invocation_correlation()
    operation = resource.operation_guard(
        session,
        _invocation_correlation=correlation,
    )
    handle = operation._completion_handle
    assert resource._mark_operation_cleanup_required(handle) is True
    assert resource._stabilize_operation_exit_for_process_control(
        correlation
    ) is (
        writer_module._OperationExitProcessControlDisposition
        .REPRESENTED_CLEANUP_OWNED
    )
    assert resource._operation_exit_process_control_poisoned
    assert not resource.active_for_owner()
    operation._close()
    session.close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


@pytest.mark.parametrize(
    "field_name",
    ("owner_pid", "lifecycle_epoch"),
    ids=("owner-pid", "lifecycle-epoch"),
)
def test_exact_record_post_poison_consistency_failure_never_reenables_admission(
    field_name: str,
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    correlation = resource._new_operation_invocation_correlation()
    operation = resource.operation_guard(
        session,
        _invocation_correlation=correlation,
    )
    original_value = getattr(correlation, field_name)
    object.__setattr__(correlation, field_name, original_value + 1)
    try:
        assert resource._stabilize_operation_exit_for_process_control(
            correlation
        ) is (
            writer_module._OperationExitProcessControlDisposition
            .INVALID_OR_WRONG_RESOURCE
        )
        assert resource._operation_exit_process_control_poisoned
        assert resource.active_for_owner() is False
        with pytest.raises(WriterSessionError):
            resource.operation_guard(session)
        with pytest.raises(WriterSessionError):
            operation._acquire_mutation_lease()
    finally:
        object.__setattr__(correlation, field_name, original_value)
    operation._close()
    session.close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


def test_invocation_correlation_is_private_immutable_non_authoritative_identity(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    correlation = resource._new_operation_invocation_correlation()
    assert repr(correlation) == "<_OperationInvocationCorrelation>"
    assert "_OperationInvocationCorrelation" not in writer_module.__all__
    with pytest.raises(AttributeError):
        correlation.owner_pid = os.getpid()
    with pytest.raises(TypeError):
        correlation.__reduce__()
    assert not any(
        name in correlation.__slots__
        for name in (
            "credential",
            "authority_lock",
            "connection",
            "cursor",
            "command",
            "decision",
            "result",
        )
    )
    session.close()


MUTATION_USABILITY_EXIT_BOUNDARIES = (
    "unbound-compiler-cleanup",
    "operation-exit-first-opcode",
    "operation-close-call-setup",
    "operation-close-first-opcode",
)


def _mutation_usability_exit_target(
    boundary: str,
) -> tuple[types.CodeType, int]:
    if boundary == "unbound-compiler-cleanup":
        code = writer_module._WriterSessionResource.require_usable_for_mutation.__code__
        instruction = next(
            instruction
            for instruction in dis.get_instructions(code)
            if instruction.offset == 40
        )
        assert instruction.opname == "LOAD_CONST"
        return code, instruction.offset
    if boundary == "operation-exit-first-opcode":
        code = writer_module._WriterSessionOperationLease.__exit__.__code__
        return code, _first_instruction_offset(code)
    if boundary == "operation-close-call-setup":
        code = writer_module._WriterSessionOperationLease.__exit__.__code__
        return code, _normal_operation_close_setup_offset()
    if boundary == "operation-close-first-opcode":
        code = writer_module._WriterSessionOperationLease._close.__code__
        return code, _first_instruction_offset(code)
    raise AssertionError("unknown mutation-usability boundary")


@pytest.mark.parametrize(
    "boundary",
    MUTATION_USABILITY_EXIT_BOUNDARIES,
    ids=MUTATION_USABILITY_EXIT_BOUNDARIES,
)
def test_mutation_usability_exit_boundaries_remain_fail_closed_without_poison(
    boundary: str,
    tmp_path: Path,
) -> None:
    for kind in PROCESS_CONTROL_KINDS:
        location = CoordinatorStateLocation.from_trusted_root(
            tmp_path / boundary / kind / "state"
        )
        initialize_database(location)
        session = acquire_sqlite_writer_session(location)
        resource = session._resource
        target = _mutation_usability_exit_target(boundary)
        targets = (target,)
        failure = _entry_process_control_for_kind(kind)
        tool_id, pending, reached = _arm_instruction_process_control(
            targets,
            failure,
        )
        observed: BaseException | None = None
        try:
            resource.require_usable_for_mutation(session)
        except BaseException as error:
            observed = error
        finally:
            _disarm_instruction_process_control(tool_id, targets)
        assert pending == []
        assert reached == [target]
        assert observed is not None
        _assert_exact_process_control_object(observed, failure)
        assert not resource._operation_exit_process_control_poisoned
        assert not resource.active_for_owner()
        with pytest.raises(WriterSessionError):
            resource.operation_guard(session)

        if boundary == "unbound-compiler-cleanup":
            assert resource._active_operations == {}
            assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
        else:
            records = _state_operation_records_for_test(resource)
            assert len(records) == 1
            assert records[0].phase is writer_module._OperationRetirementPhase.PREPARED
            observed = None
            failure.__traceback__ = None
            gc.collect()
            assert resource._active_operations == {}
            assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
        observed = None
        failure.__traceback__ = None
        session.close()


def test_competing_admission_before_poison_is_governed_after_linearization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for kind in PROCESS_CONTROL_KINDS:
        with make_coherent_transition_fixture_for_test(
            tmp_path / kind
        ) as fixture:
            session = fixture.writer_session
            resource = session._resource
            original_guard = resource.operation_guard
            original_stabilize = (
                resource._stabilize_operation_exit_for_process_control
            )
            envelope_reached = threading.Event()
            allow_poison = threading.Event()
            poison_published = threading.Event()
            competitor_admitted = threading.Event()
            competitor_closed = threading.Event()
            caller_operations: list[object] = []
            caller_errors: list[BaseException] = []
            thread_errors: list[BaseException] = []

            original_begin = resource._begin_operation

            def capture_begin(
                owner_session: object,
                invocation_correlation: object,
            ) -> object:
                operation = original_begin(
                    owner_session,
                    invocation_correlation,
                )
                caller_operations.append(operation)
                return operation

            def gated_stabilize(exact_correlation: object) -> object:
                envelope_reached.set()
                assert allow_poison.wait(5)
                result = original_stabilize(exact_correlation)
                poison_published.set()
                return result

            def delegate(**kwargs: object) -> object:
                assert kwargs
                return object()

            failure = _entry_process_control_for_kind(kind)
            _, guarded = _guarded_public_code("transition")
            target = (guarded, _instruction_offset(guarded, opname="SWAP"))
            targets = (target,)
            tool_id = -1
            pending: list[tuple[types.CodeType, int]] = []
            reached: list[tuple[types.CodeType, int]] = []

            def caller() -> None:
                try:
                    session.apply_transition(fixture.command)
                except BaseException as error:
                    caller_errors.append(error)
                try:
                    assert competitor_closed.wait(5)
                    assert len(caller_operations) == 2
                    caller_operations[0]._close()
                except BaseException as error:
                    thread_errors.append(error)

            def competitor() -> None:
                try:
                    operation = original_guard(session)
                    competitor_admitted.set()
                    assert poison_published.wait(5)
                    assert resource._operation_exit_process_control_poisoned
                    operation._close()
                except BaseException as error:
                    thread_errors.append(error)
                finally:
                    competitor_closed.set()

            with monkeypatch.context() as patch:
                patch.setattr(resource, "_begin_operation", capture_begin)
                patch.setattr(
                    resource,
                    "_stabilize_operation_exit_for_process_control",
                    gated_stabilize,
                )
                patch.setattr(
                    transaction_module,
                    "_run_atomic_transition_apply",
                    delegate,
                )
                tool_id, pending, reached = _arm_instruction_process_control(
                    targets,
                    failure,
                )
                caller_thread = threading.Thread(target=caller)
                competitor_thread = threading.Thread(target=competitor)
                try:
                    caller_thread.start()
                    assert envelope_reached.wait(5)
                    competitor_thread.start()
                    assert competitor_admitted.wait(5)
                    assert not resource._operation_exit_process_control_poisoned
                    allow_poison.set()
                    caller_thread.join(5)
                    competitor_thread.join(5)
                    assert not caller_thread.is_alive()
                    assert not competitor_thread.is_alive()
                finally:
                    allow_poison.set()
                    _disarm_instruction_process_control(tool_id, targets)

            assert pending == []
            assert reached == [target]
            assert thread_errors == []
            assert len(caller_errors) == 1
            _assert_exact_process_control_object(caller_errors[0], failure)
            assert resource._operation_exit_process_control_poisoned
            assert not resource.active_for_owner()
            with pytest.raises(WriterSessionError):
                original_guard(session)
            caller_errors.clear()
            failure.__traceback__ = None
            session.close()
            assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


def test_fork_child_poison_sees_invalidated_copy_and_cannot_retire_parent(
    tmp_path: Path,
) -> None:
    if not hasattr(os, "fork"):
        pytest.skip("fork is not available")
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    correlation = resource._new_operation_invocation_correlation()
    operation = resource.operation_guard(
        session,
        _invocation_correlation=correlation,
    )
    handle = operation._completion_handle
    read_fd, write_fd = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(read_fd)
        outcome = b"failure"
        try:
            disposition = (
                resource._stabilize_operation_exit_for_process_control(
                    correlation
                )
            )
            assert disposition is (
                writer_module._OperationExitProcessControlDisposition
                .INVALID_OR_WRONG_RESOURCE
            )
            assert not resource._operation_exit_process_control_poisoned
            try:
                resource.operation_guard(session)
            except WriterSessionError:
                pass
            else:
                raise AssertionError("fork child admitted parent operation")
            assert handle not in _state_operations_for_test(resource)
            outcome = b"ok"
        except BaseException:
            outcome = ("failure:" + traceback.format_exc()).encode("utf-8")
        try:
            os.write(write_fd, outcome)
        finally:
            os.close(write_fd)
            os._exit(0 if outcome == b"ok" else 1)

    os.close(write_fd)
    try:
        payload = os.read(read_fd, 8192)
    finally:
        os.close(read_fd)
    waited_pid, status = os.waitpid(child_pid, 0)
    assert waited_pid == child_pid
    assert os.WIFEXITED(status)
    assert os.WEXITSTATUS(status) == 0, payload.decode("utf-8", "replace")
    assert payload == b"ok"
    assert not resource._operation_exit_process_control_poisoned
    assert handle in _state_operations_for_test(resource)
    assert resource.active_for_owner()
    operation._close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
    session.close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


@pytest.mark.parametrize("kind", PROCESS_CONTROL_KINDS, ids=PROCESS_CONTROL_KINDS)
def test_operation_retirement_entry_process_control_is_cleanup_safe(
    kind: str,
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    failure = _entry_process_control_for_kind(kind)

    _trace_raise_at(
        writer_module._WriterSessionOperationLease._close,
        "if self._owner_pid != os.getpid():",
        failure,
    )
    try:
        with pytest.raises(type(failure)) as captured:
            operation._close()
    finally:
        sys.settrace(None)
    _assert_exact_process_control(captured, failure)

    record = _operation_record_for_test(resource, handle)
    assert record.phase is writer_module._OperationRetirementPhase.ADMITTED
    assert record.cleanup_required is True
    assert handle.cleanup_required is True
    assert handle in _state_operations_for_test(resource)
    assert resource.active_for_owner() is False
    assert operation._closed is False
    assert operation._finalizer.alive is True
    assert operation._session is session
    assert all(
        value is not failure
        for name in handle.__slots__
        for value in (getattr(handle, name),)
    )
    with pytest.raises(WriterSessionError):
        resource.operation_guard(session)

    operation._close()
    assert handle not in _state_operations_for_test(resource)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
    session.close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


def _run_entry_process_control_stabilization_counterfactual(
    kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    failure = _entry_process_control_for_kind(kind)
    calls = 0

    def omit_stabilization(exact_handle: object) -> bool:
        nonlocal calls
        calls += 1
        assert exact_handle is handle
        return True

    try:
        monkeypatch.setattr(
            resource,
            "_mark_operation_cleanup_required",
            omit_stabilization,
        )
        _trace_raise_at(
            writer_module._WriterSessionOperationLease._close,
            "if self._owner_pid != os.getpid():",
            failure,
        )
        try:
            with pytest.raises(type(failure)) as captured:
                operation._close()
        finally:
            sys.settrace(None)
        _assert_exact_process_control(captured, failure)
        assert calls == 1, "entry stabilization seam not reached"
        assert resource.active_for_owner() is False, (
            "entry process-control admission invariant"
        )
    finally:
        monkeypatch.undo()
        operation._close()
        session.close()


@pytest.mark.parametrize("kind", PROCESS_CONTROL_KINDS, ids=PROCESS_CONTROL_KINDS)
def test_entry_process_control_before_phase1_leaves_resource_admitting_is_causally_rejected(
    kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(
        AssertionError,
        match="entry process-control admission invariant",
    ):
        _run_entry_process_control_stabilization_counterfactual(
            kind,
            tmp_path,
            monkeypatch,
        )


@pytest.mark.parametrize("kind", PROCESS_CONTROL_KINDS, ids=PROCESS_CONTROL_KINDS)
def test_direct_live_finalizer_process_control_remains_fail_closed(
    kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    failure = _process_control_for_kind(kind)
    original_continue = resource._continue_cleanup
    calls = 0

    def interrupt(*, blocking: bool, finalizer: bool) -> None:
        nonlocal calls
        assert blocking is False
        assert finalizer is True
        calls += 1
        raise failure

    monkeypatch.setattr(
        resource,
        "_continue_cleanup",
        interrupt,
    )
    operation._finalizer()
    assert calls == 1
    assert operation._closed is False
    assert operation._finalizer.alive is False
    assert operation._session is session
    assert handle.cleanup_required is True
    assert handle in _state_operations_for_test(resource)
    assert resource.active_for_owner() is False
    assert all(
        value is not failure
        for name in handle.__slots__
        for value in (getattr(handle, name),)
    )

    monkeypatch.setattr(
        resource,
        "_continue_cleanup",
        original_continue,
    )
    operation._close()
    assert handle not in _state_operations_for_test(resource)
    session.close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


@pytest.mark.parametrize("kind", PROCESS_CONTROL_KINDS, ids=PROCESS_CONTROL_KINDS)
def test_operation_retirement_post_phase1_acknowledgment_process_control_is_cleanup_safe(
    kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    failure = _process_control_for_kind(kind)
    original_prepare = resource._prepare_operation_retirement
    interrupted = False

    def prepare_then_interrupt(exact_handle: object) -> object:
        nonlocal interrupted
        acknowledgment = original_prepare(exact_handle)
        if not interrupted:
            interrupted = True
            assert acknowledgment is handle.retirement_preparation_acknowledgment
            raise failure
        return acknowledgment

    monkeypatch.setattr(
        resource,
        "_prepare_operation_retirement",
        prepare_then_interrupt,
    )
    with pytest.raises(type(failure)) as captured:
        operation._close()
    _assert_exact_process_control(captured, failure)
    assert interrupted is True
    assert operation._closed is False
    assert operation._finalizer.alive is True
    assert handle in _state_operations_for_test(resource)
    assert resource.active_for_owner() is False
    with pytest.raises(WriterSessionError):
        resource.operation_guard(session)

    operation._close()
    assert handle not in _state_operations_for_test(resource)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
    session.close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


@pytest.mark.parametrize("kind", PROCESS_CONTROL_KINDS, ids=PROCESS_CONTROL_KINDS)
def test_operation_retirement_post_local_terminal_pre_detach_process_control_is_cleanup_safe(
    kind: str,
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    failure = _process_control_for_kind(kind)
    _trace_raise_at(
        writer_module._WriterSessionResource._retire_operation_lease_locally,
        "finalizer.detach()",
        failure,
    )
    try:
        with pytest.raises(type(failure)) as captured:
            operation._close()
    finally:
        sys.settrace(None)
    _assert_exact_process_control(captured, failure)
    assert operation._closed is True
    assert operation._finalizer.alive is True
    assert handle in _state_operations_for_test(resource)
    assert resource.active_for_owner() is False

    operation._close()
    assert operation._finalizer.alive is True
    assert handle not in _state_operations_for_test(resource)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
    session.close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


@pytest.mark.parametrize("kind", PROCESS_CONTROL_KINDS, ids=PROCESS_CONTROL_KINDS)
def test_operation_retirement_post_detach_pre_final_publication_process_control_is_cleanup_safe(
    kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    authority_lock = resource._authority_lock
    assert authority_lock is not None
    failure = _process_control_for_kind(kind)
    original_close = authority_lock.close
    interrupted = False

    def close_then_interrupt() -> None:
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            raise failure
        original_close()

    writer_module._finalize_writer_session_resource(resource)
    monkeypatch.setattr(
        authority_lock,
        "close",
        close_then_interrupt,
    )
    with pytest.raises(type(failure)) as captured:
        operation._close()
    _assert_exact_process_control(captured, failure)
    assert interrupted is True
    assert operation._closed is True
    assert operation._finalizer.alive is False
    assert operation._session is session
    with resource._condition:
        record = _operation_record_for_test(resource, handle)
        assert record.phase is writer_module._OperationRetirementPhase.EXPLICIT_RETIRED
    assert handle in _state_operations_for_test(resource)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionOperationsClosing
    assert resource.active_for_owner() is False

    operation._close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
    assert handle not in _state_operations_for_test(resource)
    operation._close()
    session.close()


@pytest.mark.parametrize(
    ("kind", "successor_kind"),
    tuple((kind, "resume") for kind in PROCESS_CONTROL_KINDS),
    ids=tuple(f"resume-{kind}" for kind in PROCESS_CONTROL_KINDS),
)
def test_operation_retirement_post_linearization_response_loss_preserves_final_state(
    kind: str,
    successor_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    failure = _process_control_for_kind(kind)
    if successor_kind == "cleanup":
        assert resource._mark_operation_cleanup_required(handle) is True
    original_notify = resource._notify_operation_retirement_waiters_locked
    notification_calls = 0

    def interrupt_then_notify() -> None:
        nonlocal notification_calls
        notification_calls += 1
        if notification_calls == 1:
            raise failure
        original_notify()

    monkeypatch.setattr(
        resource,
        "_notify_operation_retirement_waiters_locked",
        interrupt_then_notify,
    )
    with pytest.raises(type(failure)) as captured:
        operation._close()
    _assert_exact_process_control(captured, failure)
    assert notification_calls == 2
    final_state = resource._lifecycle_state
    assert handle not in _state_operations_for_test(resource)
    assert operation._closed is True
    assert operation._finalizer.alive is False
    assert operation._credential is None
    assert operation._authority_lock is None

    operation._close()
    assert resource._lifecycle_state is final_state
    if successor_kind == "resume":
        assert type(final_state) is writer_module._WriterSessionActive
        followup = resource.operation_guard(session)
        followup._close()
        assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
    else:
        assert type(final_state) is writer_module._WriterSessionOrdinaryCleanup
        with pytest.raises(WriterSessionError):
            resource.operation_guard(session)
    session.close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX


@pytest.mark.parametrize(
    ("effect_kind", "kind"),
    tuple(
        (effect_kind, kind)
        for effect_kind in ("transition", "global-stop")
        for kind in PROCESS_CONTROL_KINDS
    ),
    ids=tuple(
        f"{effect_kind}-{kind}"
        for effect_kind in ("transition", "global-stop")
        for kind in PROCESS_CONTROL_KINDS
    ),
)
def test_operation_retirement_post_linearization_durable_response_loss_uses_replay_without_duplicate_effect(
    effect_kind: str,
    kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failure = _process_control_for_kind(kind)
    with make_coherent_transition_fixture_for_test(
        tmp_path,
        ready_dependency=True,
    ) as fixture:
        resource = fixture.writer_session._resource
        original_notify = resource._notify_operation_retirement_waiters_locked
        notification_calls = 0

        def interrupt_then_notify() -> None:
            nonlocal notification_calls
            notification_calls += 1
            if notification_calls == 1:
                raise failure
            original_notify()

        monkeypatch.setattr(
            resource,
            "_notify_operation_retirement_waiters_locked",
            interrupt_then_notify,
        )
        if effect_kind == "transition":
            with pytest.raises(type(failure)) as captured:
                fixture.writer_session.apply_transition(fixture.command)
            _assert_exact_process_control(captured, failure)
            assert _coordinator_frames(captured.value) == []
            final_state = resource._lifecycle_state
            assert type(final_state) is writer_module._WriterSessionActive
            assert not resource._operation_exit_process_control_poisoned
            assert transition_event_count_for_test(fixture) == 1

            replay = fixture.writer_session.apply_transition(fixture.command)
            assert type(replay) is CommittedTransition
            assert replay.replayed is True
            assert transition_event_count_for_test(fixture) == 1
            changed = transition_tests._fresh_block_command(
                fixture.command,
                expected_version=fixture.command.expected_version,
                key=fixture.command.idempotency_key,
            )
            conflict = fixture.writer_session.apply_transition(changed)
            assert type(conflict).__name__ == "TransitionConflict"
            assert conflict.conflict_class == "idempotency_key_reuse_conflict"
            assert transition_event_count_for_test(fixture) == 1
        else:
            decision = global_stop_tests._decision()
            command = global_stop_tests._command(
                decision_ref=decision.decision_ref
            )
            global_stop_tests._seed_receipt(fixture, decision)
            global_stop_tests._patch_clock(monkeypatch)
            with pytest.raises(type(failure)) as captured:
                fixture.writer_session.apply_global_stop_update(command, decision)
            _assert_exact_process_control(captured, failure)
            assert _coordinator_frames(captured.value) == []
            final_state = resource._lifecycle_state
            assert type(final_state) is writer_module._WriterSessionActive
            assert not resource._operation_exit_process_control_poisoned
            assert global_stop_event_count_for_test(fixture) == 1

            replay = fixture.writer_session.apply_global_stop_update(
                command,
                decision,
            )
            assert type(replay) is CommittedGlobalStopUpdate
            assert replay.replayed is True
            assert global_stop_event_count_for_test(fixture) == 1
            changed = global_stop_tests._command(
                key=command.idempotency_key,
                expected_version=command.expected_version,
                decision_ref=decision.decision_ref,
                stop_id="global-stop-vs1a-response-loss-changed",
            )
            conflict = fixture.writer_session.apply_global_stop_update(
                changed,
                decision,
            )
            assert type(conflict).__name__ == "GlobalStopConflict"
            assert conflict.conflict_class == "idempotency_key_reuse_conflict"
            assert global_stop_event_count_for_test(fixture) == 1

        assert notification_calls >= 4
        assert resource._lifecycle_state is not final_state
        assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
        assert resource._mutation_slot is None
        assert resource._active_operations == {}


def test_handle_side_disposition_cannot_change_resource_admission_truth(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    disposition_written = threading.Event()
    admission_attempted = threading.Event()
    allow_writer_release = threading.Event()
    admission_finished = threading.Event()
    thread_failures: list[BaseException] = []
    admitted: list[object] = []

    def write_disposition() -> None:
        try:
            with resource._condition:
                handle._mark_cleanup_required()
                disposition_written.set()
                assert allow_writer_release.wait(2)
        except BaseException as error:
            thread_failures.append(error)
            disposition_written.set()

    def attempt_admission() -> None:
        try:
            assert disposition_written.wait(2)
            admission_attempted.set()
            followup = resource.operation_guard(session)
            admitted.append(followup)
            followup._close()
        except BaseException as error:
            thread_failures.append(error)
        finally:
            admission_finished.set()

    writer = threading.Thread(target=write_disposition)
    admitter = threading.Thread(target=attempt_admission)
    writer.start()
    admitter.start()
    assert admission_attempted.wait(2)
    assert admission_finished.is_set() is False
    allow_writer_release.set()
    writer.join(2)
    admitter.join(2)
    assert not writer.is_alive()
    assert not admitter.is_alive()
    assert thread_failures == []
    assert admission_finished.is_set() is True
    assert len(admitted) == 1
    assert _operation_record_for_test(resource, handle).cleanup_required is False

    operation._close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
    session.close()


def test_object_setattr_on_every_handle_mirror_cannot_change_resource_record(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    admitted = _operation_record_for_test(resource, handle)
    expected = (
        admitted.resource_identity,
        admitted.operation_id,
        admitted.owner_pid,
        admitted.owner_thread,
        admitted.lifecycle_epoch,
        admitted.lease_reference,
        admitted.finalizer,
        admitted.phase,
        admitted.cleanup_required,
        admitted.mutation_release_acknowledgment,
        admitted.retirement_preparation_acknowledgment,
    )
    replacements = {
        "resource_identity": object(),
        "operation_id": admitted.operation_id + 1000,
        "owner_pid": admitted.owner_pid + 1000,
        "owner_thread": admitted.owner_thread + 1000,
        "lifecycle_epoch": admitted.lifecycle_epoch + 1000,
        "_cleanup_required": True,
        "_mutation_release_acknowledgment": object(),
        "_retirement_preparation_acknowledgment": object(),
        "_operation_lease_ref": weakref.ref(operation),
        "_operation_finalizer": object(),
    }

    for field, replacement in replacements.items():
        original = object.__getattribute__(handle, field)
        object.__setattr__(handle, field, replacement)
        unchanged = _operation_record_for_test(resource, handle)
        assert (
            unchanged.resource_identity,
            unchanged.operation_id,
            unchanged.owner_pid,
            unchanged.owner_thread,
            unchanged.lifecycle_epoch,
            unchanged.lease_reference,
            unchanged.finalizer,
            unchanged.phase,
            unchanged.cleanup_required,
            unchanged.mutation_release_acknowledgment,
            unchanged.retirement_preparation_acknowledgment,
        ) == expected
        object.__setattr__(handle, field, original)

    operation._close()
    assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
    session.close()


def test_operation_retirement_final_assignment_is_last_authoritative_action(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    operation._close()
    final_state = resource._lifecycle_state
    assert type(final_state) is writer_module._WriterSessionActive
    assert handle not in _state_operations_for_test(resource)
    assert operation._closed is True
    assert operation._finalizer.alive is False
    assert operation._credential is None
    assert operation._authority_lock is None
    assert operation._session is session
    local_state = (
        operation._retirement_requested,
        operation._closed,
        operation._preparation_acknowledgment,
        operation._finalizer.alive,
        operation._credential,
        operation._authority_lock,
        operation._session,
    )
    operation._close()
    assert resource._lifecycle_state is final_state
    assert (
        operation._retirement_requested,
        operation._closed,
        operation._preparation_acknowledgment,
        operation._finalizer.alive,
        operation._credential,
        operation._authority_lock,
        operation._session,
    ) == local_state

    close_source = textwrap.dedent(
        inspect.getsource(writer_module._WriterSessionOperationLease._close)
    )
    assert close_source.index("_prepare_operation_retirement(") < close_source.index(
        "_retire_operation_lease_locally("
    )
    assert close_source.index("_retire_operation_lease_locally(") < close_source.index(
        "_publish_prepared_operation_retirement("
    )
    local_retirement_source = textwrap.dedent(
        inspect.getsource(
            writer_module._WriterSessionResource._retire_operation_lease_locally
        )
    )
    assert "with self._condition:" in local_retirement_source
    assert local_retirement_source.index("operation_lease._closed = True") < (
        local_retirement_source.index("finalizer.detach()")
    )
    tree = ast.parse(close_source)
    close_definition = tree.body[0]
    assert isinstance(close_definition, (ast.FunctionDef, ast.AsyncFunctionDef))
    governing_try = next(
        statement
        for statement in close_definition.body
        if isinstance(statement, ast.Try)
    )
    assert isinstance(governing_try.body[-1], ast.Expr)
    assert "_publish_prepared_operation_retirement" in ast.unparse(
        governing_try.body[-1]
    )
    session.close()


PRODUCTION_PATH_COUNTERFACTUALS = (
    "01_phase1_publishes_active",
    "02_phase1_removes_exact_handle",
    "03_local_terminality_before_phase1_ack",
    "04_finalizer_detach_before_nonadmitting_preparation",
    "05_disposition_write_outside_condition",
    "06_disposition_read_outside_condition",
    "07_final_publication_ignores_cleanup_required",
    "08_final_publication_restores_active_during_disposal",
    "09_prepublication_process_control_leaves_active",
    "10_postdetach_process_control_loses_retry_owner",
    "11_final_assignment_followed_by_authority_mutation",
    "12_idempotent_retry_misclassifies_incomplete_operation",
)


AUTHENTICITY_PRODUCTION_COUNTERFACTUALS = (
    "01_fabricated_local_retirement_ack_authorizes_publication",
    "04_direct_live_finalizer_publishes_active",
    "05_direct_live_finalizer_removes_handle",
    "06_never_published_acknowledged_handle_classified_complete",
    "07_absent_handle_forged_local_history_classified_complete",
    "08_cross_resource_retirement_proof_accepted",
    "09_stale_epoch_retirement_proof_accepted",
    "12_response_loss_requires_internal_matched_none_forgery",
)


EXPLICIT_RETIREMENT_RUNTIME_COUNTERFACTUALS = (
    "01_dead_finalizer_accepted_as_explicit_detach",
    "02_finalizer_alive_false_before_callback_allows_active",
    "03_direct_detach_plus_lease_collection_counts_as_retirement",
    "05_lease_loss_before_explicit_retirement_restores_active",
    "06_lease_loss_before_explicit_retirement_strands_cleanup",
    "07_handle_lease_binding_replacement_changes_resource_truth",
    "08_handle_finalizer_binding_replacement_changes_resource_truth",
    "09_same_handle_fake_pair_authorizes_publication",
    "10_explicit_retirement_accepts_unsuccessful_detach",
    "11_orphan_cleanup_requires_missing_live_lease",
    "12_gc_or_finalizer_path_publishes_normal_active",
)


EXPLICIT_RETIREMENT_SOURCE_MUTANTS = (
    "01_resource_explicit_phase_gate_removed",
    "02_unsuccessful_detach_result_accepted",
    "03_handle_binding_used_instead_of_resource_record",
    "04_lease_loss_removes_record_as_normal_completion",
)


EXIT_POISON_SOURCE_MUTANTS = (
    "01_poison_after_state_operation_records_call",
    "02_poison_after_operation_blocks_admission_call",
    "03_controller_cleanup_resolution_classified_incomplete",
    "04_only_root_traceback_cleared",
    "05_context_traversal_removed_from_sanitizer",
    "06_safe_error_outer_scrub_removed",
    "07_bound_guard_correlation_replaced_by_nonmethod_path",
    "08_lifecycle_epoch_property_before_poison",
    "09_state_authority_call_before_poison",
    "10_object_getattribute_exception_fields",
    "11_sanitizer_fallback_retry_removed",
    "12_sanitizer_failure_escapes_boundary",
    "13_trusted_safe_error_context_severance_removed",
)


SECONDARY_AST_GUARDS = (
    "resource-identity-comparisons",
    "no-process-global-identity-registry",
    "opaque-identity-surface",
    "caller-envelope-bytecode",
    "pre-admission-token-correlation-and-privacy",
    "poison-publication-order",
    "sanitizer-base-descriptor-boundary",
    "poison-readers-and-monotonicity",
    "mutation-usability-path-separation",
)


def _run_production_path_counterfactual(
    case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    invariant = "production retirement invariant"
    try:
        if case == "01_phase1_publishes_active":
            original = resource._prepare_operation_retirement

            def mutant(exact_handle: object) -> object:
                acknowledgment = original(exact_handle)
                with resource._condition:
                    authority = writer_module._state_authority(
                        resource._lifecycle_state
                    )
                    assert authority is not None
                    resource._lifecycle_state = writer_module._WriterSessionActive(
                        writer_module._WriterSessionActivity(authority, ())
                    )
                return acknowledgment

            monkeypatch.setattr(resource, "_prepare_operation_retirement", mutant)
            assert resource._prepare_operation_retirement(handle) is not None
            assert type(resource._lifecycle_state) is not writer_module._WriterSessionActive, invariant
            return

        if case == "02_phase1_removes_exact_handle":
            original = resource._prepare_operation_retirement

            def mutant(exact_handle: object) -> object:
                acknowledgment = original(exact_handle)
                with resource._condition:
                    state = resource._lifecycle_state
                    authority = writer_module._state_authority(state)
                    assert authority is not None
                    activity = writer_module._WriterSessionActivity(authority, ())
                    resource._lifecycle_state = writer_module._WriterSessionOrdinaryCleanup(
                        writer_module._ContinueCleanup(
                            writer_module._CleanupBeforeR1NoSlot(activity)
                        )
                    )
                return acknowledgment

            monkeypatch.setattr(resource, "_prepare_operation_retirement", mutant)
            assert resource._prepare_operation_retirement(handle) is not None
            assert handle in _state_operations_for_test(resource), invariant
            return

        if case == "03_local_terminality_before_phase1_ack":
            original = resource._prepare_operation_retirement

            def mutant(exact_handle: object) -> object:
                operation._closed = True
                return original(exact_handle)

            monkeypatch.setattr(resource, "_prepare_operation_retirement", mutant)
            assert resource._prepare_operation_retirement(handle) is not None
            assert operation._closed is False, invariant
            return

        if case == "04_finalizer_detach_before_nonadmitting_preparation":
            original = resource._prepare_operation_retirement
            admission_at_detach: list[bool] = []

            def mutant(exact_handle: object) -> object:
                operation._finalizer.detach()
                admission_at_detach.append(resource.active_for_owner())
                return original(exact_handle)

            monkeypatch.setattr(resource, "_prepare_operation_retirement", mutant)
            assert resource._prepare_operation_retirement(handle) is not None
            assert admission_at_detach == [False], invariant
            return

        if case == "05_disposition_write_outside_condition":
            lock_observations: list[bool] = []

            def mutant(exact_handle: object) -> bool:
                assert exact_handle is handle
                lock_observations.append(resource._lifecycle_lock.locked())
                handle._mark_cleanup_required()
                return True

            monkeypatch.setattr(resource, "_mark_operation_cleanup_required", mutant)
            assert resource._mark_operation_cleanup_required(handle) is True
            assert lock_observations == [True], invariant
            return

        if case == "06_disposition_read_outside_condition":
            original = resource._publish_prepared_operation_retirement
            lock_observations: list[bool] = []

            def mutant(*args: object) -> None:
                lock_observations.append(resource._lifecycle_lock.locked())
                assert handle.cleanup_required is False
                original(*args)

            monkeypatch.setattr(
                resource,
                "_publish_prepared_operation_retirement",
                mutant,
            )
            operation._close()
            assert lock_observations == [True], invariant
            return

        if case == "07_final_publication_ignores_cleanup_required":
            assert resource._mark_operation_cleanup_required(handle) is True

            def mutant(exact_handle: object) -> None:
                assert exact_handle is handle
                with resource._condition:
                    authority = writer_module._state_authority(
                        resource._lifecycle_state
                    )
                    assert authority is not None
                    resource._lifecycle_state = writer_module._WriterSessionActive(
                        writer_module._WriterSessionActivity(authority, ())
                    )

            monkeypatch.setattr(
                resource,
                "_continue_operation_cleanup_if_required",
                mutant,
            )
            operation._close()
            assert type(resource._lifecycle_state) is not writer_module._WriterSessionActive, invariant
            return

        if case == "08_final_publication_restores_active_during_disposal":
            with resource._condition:
                resource._freeze_admission_locked()

            def mutant(state: object, exact: object) -> object:
                assert exact is handle
                authority = writer_module._state_authority(state)
                assert authority is not None
                return writer_module._WriterSessionActive(
                    writer_module._WriterSessionActivity(authority, ())
                )

            monkeypatch.setattr(
                resource,
                "_operation_retirement_cleanup_successor_locked",
                mutant,
            )
            operation._close()
            assert type(resource._lifecycle_state) is not writer_module._WriterSessionActive, invariant
            return

        if case == "09_prepublication_process_control_leaves_active":
            def mutant(*args: object) -> None:
                del args
                with resource._condition:
                    authority = writer_module._state_authority(
                        resource._lifecycle_state
                    )
                    assert authority is not None
                    resource._lifecycle_state = writer_module._WriterSessionActive(
                        writer_module._WriterSessionActivity(authority, ())
                    )
                raise KeyboardInterrupt()

            monkeypatch.setattr(
                resource,
                "_publish_prepared_operation_retirement",
                mutant,
            )
            with pytest.raises(KeyboardInterrupt):
                operation._close()
            assert type(resource._lifecycle_state) is not writer_module._WriterSessionActive, invariant
            return

        if case == "10_postdetach_process_control_loses_retry_owner":
            original = resource._retire_operation_lease_locally

            def mutant(*args: object) -> bool:
                retired = original(*args)
                operation._session = None
                raise KeyboardInterrupt()

            monkeypatch.setattr(resource, "_retire_operation_lease_locally", mutant)
            with pytest.raises(KeyboardInterrupt):
                operation._close()
            assert operation._session is session, invariant
            return

        if case == "11_final_assignment_followed_by_authority_mutation":
            original = resource._publish_prepared_operation_retirement

            def mutant(*args: object) -> None:
                original(*args)
                with resource._condition:
                    state = resource._lifecycle_state
                    assert type(state) is writer_module._WriterSessionActive
                    resource._lifecycle_state = writer_module._WriterSessionOrdinaryCleanup(
                        writer_module._ContinueCleanup(
                            writer_module._CleanupBeforeR1NoSlot(state.activity)
                        )
                    )

            monkeypatch.setattr(
                resource,
                "_publish_prepared_operation_retirement",
                mutant,
            )
            operation._close()
            assert type(resource._lifecycle_state) is writer_module._WriterSessionActive, invariant
            return

        if case == "12_idempotent_retry_misclassifies_incomplete_operation":
            def mutant(*args: object) -> None:
                del args
                return None

            monkeypatch.setattr(
                resource,
                "_publish_prepared_operation_retirement",
                mutant,
            )
            operation._close()
            assert handle not in _state_operations_for_test(resource), invariant
            return

        raise AssertionError("unhandled production counterfactual")
    finally:
        monkeypatch.undo()
        try:
            operation._close()
        except BaseException:
            pass
        try:
            session.close()
        except BaseException:
            pass
        if operation._finalizer is not None and operation._finalizer.alive:
            operation._finalizer.detach()


def _run_authenticity_production_counterfactual(
    case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    invariant = "production authenticity invariant"
    second_session: object | None = None
    second_operation: object | None = None

    def force_active_without_exact_local_retirement() -> None:
        with resource._condition:
            state = resource._lifecycle_state
            authority = writer_module._state_authority(state)
            assert authority is not None
            resource._lifecycle_state = writer_module._WriterSessionActive(
                writer_module._WriterSessionActivity(authority, ())
            )

    try:
        if case == "01_fabricated_local_retirement_ack_authorizes_publication":
            preparation = resource._prepare_operation_retirement(handle)
            assert preparation is not None
            fabricated = object()

            def mutant(*args: object) -> None:
                assert args == (preparation, fabricated)
                force_active_without_exact_local_retirement()

            monkeypatch.setattr(
                resource,
                "_publish_prepared_operation_retirement",
                mutant,
            )
            resource._publish_prepared_operation_retirement(preparation, fabricated)
            assert handle in _state_operations_for_test(resource), invariant
            return

        if case == "04_direct_live_finalizer_publishes_active":
            calls = 0

            def mutant(exact_handle: object) -> bool:
                nonlocal calls
                calls += 1
                assert exact_handle is handle
                force_active_without_exact_local_retirement()
                return False

            monkeypatch.setattr(
                resource,
                "_mark_operation_orphaned",
                mutant,
            )
            operation._finalizer()
            assert calls == 1
            assert type(resource._lifecycle_state) is not writer_module._WriterSessionActive, invariant
            return

        if case == "05_direct_live_finalizer_removes_handle":
            original = resource._state_after_operation_completion
            calls = 0

            def mutant(
                state: object,
                record: object,
                remaining: tuple[object, ...],
            ) -> object:
                nonlocal calls
                calls += 1
                assert record.handle is handle
                assert record.phase is writer_module._OperationRetirementPhase.ORPHANED
                assert record.cleanup_required is True
                assert remaining == ()
                original(state, record, remaining)
                authority = writer_module._state_authority(state)
                assert authority is not None
                return writer_module._WriterSessionActive(
                    writer_module._WriterSessionActivity(authority, ())
                )

            monkeypatch.setattr(
                resource,
                "_state_after_operation_completion",
                mutant,
            )
            operation._finalizer()
            assert calls == 1
            assert handle in _state_operations_for_test(resource), invariant
            return

        if case in (
            "06_never_published_acknowledged_handle_classified_complete",
            "07_absent_handle_forged_local_history_classified_complete",
        ):
            absent = writer_module._OperationCompletionHandle(
                resource_identity=resource._resource_identity,
                operation_id=resource._next_operation_id,
                owner_pid=os.getpid(),
                owner_thread=threading.get_ident(),
                lifecycle_epoch=resource._lifecycle_epoch,
            )
            preparation = writer_module._OperationRetirementPreparationAcknowledgment(
                resource._resource_identity,
                resource._lifecycle_epoch,
                absent,
            )
            forged_history = object()
            accepted = False

            def mutant(*args: object) -> None:
                nonlocal accepted
                assert args[0] is preparation
                if case == "07_absent_handle_forged_local_history_classified_complete":
                    assert args[1] is forged_history
                accepted = True

            monkeypatch.setattr(
                resource,
                "_publish_prepared_operation_retirement",
                mutant,
            )
            supplied = (
                forged_history
                if case == "07_absent_handle_forged_local_history_classified_complete"
                else None
            )
            resource._publish_prepared_operation_retirement(preparation, supplied)
            assert accepted is False, invariant
            return

        if case == "08_cross_resource_retirement_proof_accepted":
            other_location = CoordinatorStateLocation.from_trusted_root(
                tmp_path / "other-state"
            )
            initialize_database(other_location)
            second_session = acquire_sqlite_writer_session(other_location)
            other_resource = second_session._resource
            second_operation = other_resource.operation_guard(second_session)
            preparation = resource._prepare_operation_retirement(handle)
            assert preparation is not None
            original = resource._retire_operation_lease_locally

            def mutant(*args: object) -> bool:
                assert args == (preparation, second_operation)
                return original(preparation, operation)

            monkeypatch.setattr(
                resource,
                "_retire_operation_lease_locally",
                mutant,
            )
            accepted = resource._retire_operation_lease_locally(
                preparation,
                second_operation,
            )
            assert accepted is False, invariant
            return

        if case == "09_stale_epoch_retirement_proof_accepted":
            stale = writer_module._OperationCompletionHandle(
                resource_identity=resource._resource_identity,
                operation_id=resource._next_operation_id,
                owner_pid=os.getpid(),
                owner_thread=threading.get_ident(),
                lifecycle_epoch=resource._lifecycle_epoch + 1,
            )
            preparation = writer_module._OperationRetirementPreparationAcknowledgment(
                resource._resource_identity,
                resource._lifecycle_epoch + 1,
                stale,
            )
            accepted = False

            def mutant(*args: object) -> None:
                nonlocal accepted
                assert args == (preparation, None)
                accepted = True

            monkeypatch.setattr(
                resource,
                "_publish_prepared_operation_retirement",
                mutant,
            )
            resource._publish_prepared_operation_retirement(preparation, None)
            assert accepted is False, invariant
            return

        if case == "12_response_loss_requires_internal_matched_none_forgery":
            operation._close()
            preparation = operation._preparation_acknowledgment
            assert preparation is not None
            publication_called = False

            monkeypatch.setattr(
                resource,
                "_prepare_operation_retirement",
                lambda exact: preparation if exact is handle else None,
            )
            monkeypatch.setattr(
                resource,
                "_retire_operation_lease_locally",
                lambda *args: True,
            )

            def mutant(*args: object) -> None:
                nonlocal publication_called
                publication_called = True

            monkeypatch.setattr(
                resource,
                "_publish_prepared_operation_retirement",
                mutant,
            )
            operation._close()
            assert publication_called is False, invariant
            return

        raise AssertionError("unhandled authenticity counterfactual")
    finally:
        monkeypatch.undo()
        if operation._session is None:
            operation._session = session
        try:
            operation._close()
        except BaseException:
            pass
        if operation._finalizer is not None and operation._finalizer.alive:
            operation._abandon_before_publication()
        try:
            session.close()
        except BaseException:
            pass
        if second_operation is not None:
            try:
                second_operation._close()
            except BaseException:
                pass
        if second_session is not None:
            try:
                second_session.close()
            except BaseException:
                pass


@pytest.mark.parametrize(
    "case",
    PRODUCTION_PATH_COUNTERFACTUALS,
    ids=PRODUCTION_PATH_COUNTERFACTUALS,
)
def test_vs1a_repair_counterfactual_is_causally_rejected(
    case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(AssertionError, match="production retirement invariant"):
        _run_production_path_counterfactual(
            case,
            tmp_path,
            monkeypatch,
        )


@pytest.mark.parametrize(
    "case",
    AUTHENTICITY_PRODUCTION_COUNTERFACTUALS,
    ids=AUTHENTICITY_PRODUCTION_COUNTERFACTUALS,
)
def test_vs1a_authenticity_counterfactual_is_causally_rejected(
    case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(AssertionError, match="production authenticity invariant"):
        _run_authenticity_production_counterfactual(
            case,
            tmp_path,
            monkeypatch,
        )


def _replace_source_exact(
    source: str,
    original: str,
    replacement: str,
    *,
    count: int,
) -> str:
    assert source.count(original) == count
    return source.replace(original, replacement)


def _replace_legacy_delegation_source_exact(
    source: str,
    original: str,
    replacement: str,
    *,
    count: int,
) -> str:
    boundary = "    def _initialize_development_program("
    assert source.count(boundary) == 1
    legacy, initialization = source.split(boundary, 1)
    legacy = _replace_source_exact(
        legacy,
        original,
        replacement,
        count=count,
    )
    return legacy + boundary + initialization


def _load_exit_poison_source_mutant(
    case: str,
    tmp_path: Path,
) -> tuple[types.ModuleType, Path, str]:
    live_before = WRITER_PATH.read_bytes()
    source = live_before.decode("utf-8")
    poison_assignment = (
        "                        self._operation_exit_process_control_poisoned_value = True\n"
    )
    classification_start = '''            cleanup_owned = bool(
                _operation_blocks_admission(exact_record)
'''
    if case in (
        "01_poison_after_state_operation_records_call",
        "02_poison_after_operation_blocks_admission_call",
    ):
        source = _replace_source_exact(
            source,
            poison_assignment,
            "",
            count=1,
        )
        delayed_helper = (
            "_state_operation_records(pending_state)"
            if case == "01_poison_after_state_operation_records_call"
            else "_operation_blocks_admission(exact_record)"
        )
        source = _replace_source_exact(
            source,
            classification_start,
            (
                f"            {delayed_helper}\n"
                "            self._operation_exit_process_control_poisoned_value = True\n"
                + classification_start
            ),
            count=1,
        )
    elif case == "03_controller_cleanup_resolution_classified_incomplete":
        source = _replace_source_exact(
            source,
            '''                or (
                    type(pending_state) is _WriterSessionControllerResolution
                    and type(pending_state.policy)
                    is _CleanupRequiredAfterResolution
                )
''',
            "                or False  # source mutant drops cleanup resolution policy\n",
            count=1,
        )
    elif case == "04_only_root_traceback_cleared":
        source = _replace_source_exact(
            source,
            '''            _base_descriptor_set(  # type: ignore[operator]
                _traceback_descriptor,
                current,
                None,
            )
            cause = _base_descriptor_get(  # type: ignore[operator]
''',
            '''            _base_descriptor_set(  # type: ignore[operator]
                _traceback_descriptor,
                current,
                None,
            )
            return  # source mutant clears only the root traceback
            cause = _base_descriptor_get(  # type: ignore[operator]
''',
            count=1,
        )
    elif case == "05_context_traversal_removed_from_sanitizer":
        source = _replace_source_exact(
            source,
            "                (cause, context, arguments, attributes, children),\n",
            "                (cause, None, arguments, attributes, children),\n",
            count=1,
        )
    elif case == "06_safe_error_outer_scrub_removed":
        source = _replace_source_exact(
            source,
            '''                _sanitize_exception_traceback_graph_at_outward_boundary(
                    safe_error,
                    _sanitize_exception_traceback_graph,
                )
''',
            "                pass  # source mutant removes safe-error outer scrub\n",
            count=2,
        )
        source = _replace_legacy_delegation_source_exact(
            source,
            '''            _sanitize_exception_traceback_graph_at_outward_boundary(
                safe_error,
                _sanitize_exception_traceback_graph,
            )
''',
            "            pass  # source mutant removes safe-error outer scrub\n",
            count=2,
        )
    elif case == "07_bound_guard_correlation_replaced_by_nonmethod_path":
        source = _replace_legacy_delegation_source_exact(
            source,
            "                if type(bound_operation_guard) is MethodType\n",
            "                if False  # source mutant forces non-method compatibility path\n",
            count=2,
        )
    elif case in (
        "08_lifecycle_epoch_property_before_poison",
        "09_state_authority_call_before_poison",
    ):
        pre_poison_statement = (
            "        _ = self._lifecycle_epoch  # source mutant pre-poison property\n"
            if case == "08_lifecycle_epoch_property_before_poison"
            else "        _state_authority(self._lifecycle_state)  # source mutant pre-poison helper\n"
        )
        source = _replace_source_exact(
            source,
            '''        """Stabilize only the exact currently represented invocation."""

        if (
''',
            '''        """Stabilize only the exact currently represented invocation."""

''' + pre_poison_statement + "        if (\n",
            count=1,
        )
    elif case == "10_object_getattribute_exception_fields":
        source = _replace_source_exact(
            source,
            '''        if _isinstance(current, _base_exception_type):  # type: ignore[operator]
            # Traceback storage is cleared before any other field is read.
''',
            '''        if _isinstance(current, _base_exception_type):  # type: ignore[operator]
            object.__getattribute__(current, "__context__")
            # Source mutant restores dispatch through subclass data descriptors.
            # Traceback storage is cleared before any other field is read.
''',
            count=1,
        )
    elif case == "11_sanitizer_fallback_retry_removed":
        source = _replace_source_exact(
            source,
            "        _fallback_pass(root)  # type: ignore[operator]\n",
            "        raise  # source mutant removes bounded fallback\n",
            count=2,
        )
    elif case == "12_sanitizer_failure_escapes_boundary":
        source = _replace_legacy_delegation_source_exact(
            source,
            '''            _sanitize_exception_traceback_graph_at_outward_boundary(
                governing,
                _sanitize_exception_traceback_graph,
            )
''',
            "            _sanitize_exception_traceback_graph(governing)\n",
            count=2,
        )
    elif case == "13_trusted_safe_error_context_severance_removed":
        source = _replace_source_exact(
            source,
            '''        _BASE_EXCEPTION_DESCRIPTOR_SET(
            _BASE_EXCEPTION_CONTEXT_DESCRIPTOR,
            attached,
            None,
        )
''',
            "        pass  # source mutant removes trusted safe-error context severance\n",
            count=1,
        )
    else:
        raise AssertionError("unhandled correlation/privacy source mutant")

    mutant_path = tmp_path / f"sqlite_writer_session_{case}.py"
    assert not mutant_path.resolve().is_relative_to(ROOT.resolve())
    mutant_path.write_text(source, encoding="utf-8")
    parsed = ast.parse(mutant_path.read_text(encoding="utf-8"), str(mutant_path))
    compile(parsed, str(mutant_path), "exec")

    module_name = f"ge_nwp_coordinator._vs1a_exit_poison_mutant_{case}"
    spec = importlib.util.spec_from_file_location(module_name, mutant_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    module._AT_FORK_REGISTERED = True
    assert WRITER_PATH.read_bytes() == live_before
    return module, mutant_path, hashlib.sha256(live_before).hexdigest()


def _mutant_guarded_public_code(
    module: types.ModuleType,
    effect_kind: str,
) -> tuple[types.CodeType, types.CodeType]:
    public = getattr(
        module._SQLiteWriterSession,
        "apply_transition" if effect_kind == "transition" else "apply_global_stop_update",
    ).__code__
    guarded = next(
        constant
        for constant in public.co_consts
        if type(constant) is types.CodeType
        and constant.co_name.startswith("_guarded_")
    )
    return public, guarded


def _assert_counterfactual_rejected(
    condition: bool,
    invariant: str,
) -> None:
    with pytest.raises(AssertionError, match=invariant):
        assert condition, invariant


def _exception_graph_has_frame_from_path(
    root: BaseException,
    path: str,
) -> bool:
    for error in _exception_graph(root):
        current = error.__traceback__
        while current is not None:
            if current.tb_frame.f_code.co_filename == path:
                return True
            current = current.tb_next
    return False


def _exercise_correlation_privacy_source_mutant(
    module: types.ModuleType,
    case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> bool:
    location = _location(tmp_path)
    initialize_database(location)
    session = module.acquire_sqlite_writer_session(location)
    resource = session._resource
    operations: list[object] = []
    mutations: list[object] = []
    observed: BaseException | None = None
    failure: BaseException | None = None
    retained: object | None = None
    try:
        if case in (
            "01_poison_after_state_operation_records_call",
            "02_poison_after_operation_blocks_admission_call",
        ):
            represented = resource._new_operation_invocation_correlation()
            operation = resource.operation_guard(
                session,
                _invocation_correlation=represented,
            )
            operations.append(operation)
            helper_name = (
                "_state_operation_records"
                if case == "01_poison_after_state_operation_records_call"
                else "_operation_blocks_admission"
            )
            helper_failure = RuntimeError("mutant pre-poison helper failure")

            def fail_helper(*args: object, **kwargs: object) -> object:
                assert args and not kwargs
                raise helper_failure

            with monkeypatch.context() as patch:
                patch.setattr(module, helper_name, fail_helper)
                try:
                    resource._stabilize_operation_exit_for_process_control(
                        represented
                    )
                except BaseException as error:
                    observed = error
            return bool(
                observed is helper_failure
                and not resource._operation_exit_process_control_poisoned
            )

        if case in (
            "08_lifecycle_epoch_property_before_poison",
            "09_state_authority_call_before_poison",
        ):
            represented = resource._new_operation_invocation_correlation()
            operation = resource.operation_guard(
                session,
                _invocation_correlation=represented,
            )
            operations.append(operation)
            helper_failure = RuntimeError("mutant pre-poison authority failure")

            def fail_authority(*args: object, **kwargs: object) -> object:
                assert args and not kwargs
                raise helper_failure

            with monkeypatch.context() as patch:
                patch.setattr(module, "_state_authority", fail_authority)
                try:
                    resource._stabilize_operation_exit_for_process_control(
                        represented
                    )
                except BaseException as error:
                    observed = error
            return bool(
                observed is helper_failure
                and not resource._operation_exit_process_control_poisoned
                and resource.active_for_owner()
            )

        if case == "03_controller_cleanup_resolution_classified_incomplete":
            represented = resource._new_operation_invocation_correlation()
            operation = resource.operation_guard(
                session,
                _invocation_correlation=represented,
            )
            operations.append(operation)
            mutation = operation._acquire_mutation_lease()
            mutations.append(mutation)
            connection = sqlite3.connect(":memory:", isolation_level=None)
            retained = module._make_retained_sqlite_connection(
                connection,
                resource._resource_identity,
            )
            scope_token = module._ControllerScopeToken(
                retained,
                operation._completion_handle,
            )
            with resource._condition:
                original_state = resource._lifecycle_state
                assert type(original_state) is module._WriterSessionMutationActive
                resource._lifecycle_state = module._WriterSessionControllerResolution(
                    original_state.frame,
                    scope_token,
                    module._CleanupRequiredAfterResolution(),
                )
            disposition = resource._stabilize_operation_exit_for_process_control(
                represented
            )
            survived = disposition is not (
                module._OperationExitProcessControlDisposition.REPRESENTED_CLEANUP_OWNED
            )
            with resource._condition:
                resource._lifecycle_state = original_state
                resource._operation_exit_process_control_poisoned_value = False
            return survived

        original_begin = resource._begin_operation
        correlations: list[object] = []
        records: list[object] = []

        def capture_begin(
            owner_session: object,
            invocation_correlation: object,
        ) -> object:
            operation = original_begin(owner_session, invocation_correlation)
            operations.append(operation)
            correlations.append(invocation_correlation)
            records.append(module._state_operation_records(resource._lifecycle_state)[0])
            return operation

        if case == "10_object_getattribute_exception_fields":
            descriptor_calls: list[str] = []
            descriptor_failure = RuntimeError("mutant hostile descriptor")

            def hostile_context(instance: BaseException) -> object:
                assert isinstance(instance, BaseException)
                descriptor_calls.append("__context__")
                raise descriptor_failure

            hostile_type = type(
                "ExternallyDefinedMutantHostileException",
                (RuntimeError,),
                {"__context__": property(hostile_context)},
            )
            hostile = _raised_exception_for_sanitizer(hostile_type("hostile"))
            failure = KeyboardInterrupt("mutant governing")
            failure.__context__ = hostile

            def governing_delegate(**kwargs: object) -> object:
                assert kwargs
                raise failure

            with monkeypatch.context() as patch:
                patch.setattr(resource, "_begin_operation", capture_begin)
                patch.setattr(
                    transaction_module,
                    "_run_atomic_transition_apply",
                    governing_delegate,
                )
                try:
                    session.apply_transition(None)
                except BaseException as error:
                    observed = error
            return bool(
                descriptor_calls
                and observed is descriptor_failure
                and observed is not failure
            )

        if case == "11_sanitizer_fallback_retry_removed":
            failure = KeyboardInterrupt("mutant governing")
            sanitizer_failure = RuntimeError("mutant sanitizer core failure")

            def governing_delegate(**kwargs: object) -> object:
                assert kwargs
                raise failure

            core_code = module._sanitize_exception_traceback_graph_pass.__code__
            target = (
                core_code,
                _instruction_offset(
                    core_code,
                    opname="LOAD_FAST",
                    argval="_base_descriptor_set",
                ),
            )
            targets = (target,)
            with monkeypatch.context() as patch:
                patch.setattr(resource, "_begin_operation", capture_begin)
                patch.setattr(
                    transaction_module,
                    "_run_atomic_transition_apply",
                    governing_delegate,
                )
                tool_id, pending, reached = _arm_instruction_process_control(
                    targets,
                    sanitizer_failure,
                )
                try:
                    session.apply_transition(None)
                except BaseException as error:
                    observed = error
                finally:
                    _disarm_instruction_process_control(tool_id, targets)
            assert pending == [] and reached == [target]
            return bool(
                observed is sanitizer_failure
                and observed is not failure
            )

        if case == "12_sanitizer_failure_escapes_boundary":
            failure = KeyboardInterrupt("mutant governing")
            sanitizer_failure = RuntimeError("mutant sanitizer boundary failure")

            def governing_delegate(**kwargs: object) -> object:
                assert kwargs
                raise failure

            def fail_sanitizer(root: BaseException) -> None:
                assert root is failure
                raise sanitizer_failure

            with monkeypatch.context() as patch:
                patch.setattr(resource, "_begin_operation", capture_begin)
                patch.setattr(
                    transaction_module,
                    "_run_atomic_transition_apply",
                    governing_delegate,
                )
                patch.setattr(
                    module,
                    "_sanitize_exception_traceback_graph",
                    fail_sanitizer,
                )
                try:
                    session.apply_transition(None)
                except BaseException as error:
                    observed = error
            return bool(
                observed is sanitizer_failure
                and observed is not failure
            )

        if case in (
            "04_only_root_traceback_cleared",
            "05_context_traversal_removed_from_sanitizer",
        ):
            failure = KeyboardInterrupt("entry")
            body_failure = RuntimeError("mutant context")

            def exceptional_delegate(**kwargs: object) -> object:
                assert kwargs
                raise body_failure

            _, guarded = _mutant_guarded_public_code(module, "transition")
            target = (
                guarded,
                _instruction_offset(guarded, opname="WITH_EXCEPT_START"),
            )
            targets = (target,)
            with monkeypatch.context() as patch:
                patch.setattr(resource, "_begin_operation", capture_begin)
                patch.setattr(
                    transaction_module,
                    "_run_atomic_transition_apply",
                    exceptional_delegate,
                )
                tool_id, pending, reached = _arm_instruction_process_control(
                    targets,
                    failure,
                )
                try:
                    session.apply_transition(None)
                except BaseException as error:
                    observed = error
                finally:
                    _disarm_instruction_process_control(tool_id, targets)
            assert pending == [] and reached == [target]
            assert observed is failure
            assert observed.__context__ is body_failure
            return _exception_graph_has_frame_from_path(observed, module.__file__)

        if case in (
            "06_safe_error_outer_scrub_removed",
            "07_bound_guard_correlation_replaced_by_nonmethod_path",
        ):
            created_correlations: list[object] = []
            original_new_correlation = (
                resource._new_operation_invocation_correlation
            )

            def capture_new_correlation() -> object:
                correlation = original_new_correlation()
                created_correlations.append(correlation)
                return correlation

            exact_error = SQLiteMutationStoreError(
                SQLiteMutationStoreErrorCode.MUTATION_FAILED
            )
            disposition = module._SafeMutationFailureDisposition(exact_error)

            def safe_delegate(**kwargs: object) -> object:
                assert kwargs
                return disposition

            with monkeypatch.context() as patch:
                patch.setattr(resource, "_begin_operation", capture_begin)
                if case == "07_bound_guard_correlation_replaced_by_nonmethod_path":
                    patch.setattr(
                        resource,
                        "_new_operation_invocation_correlation",
                        capture_new_correlation,
                    )
                patch.setattr(
                    transaction_module,
                    "_run_atomic_transition_apply",
                    safe_delegate,
                )
                try:
                    session.apply_transition(None)
                except BaseException as error:
                    observed = error
            assert observed is exact_error
            assert len(correlations) == len(records) == 1
            if case == "06_safe_error_outer_scrub_removed":
                return _exception_graph_has_frame_from_path(
                    observed,
                    module.__file__,
                )
            return bool(
                len(created_correlations) == 2
                and created_correlations[0] is not created_correlations[1]
                and correlations == [created_correlations[1]]
                and records[0].invocation_correlation
                is created_correlations[1]
            )

        if case == "13_trusted_safe_error_context_severance_removed":
            assert type(resource.operation_guard) is types.MethodType
            exact_error = SQLiteMutationStoreError(
                SQLiteMutationStoreErrorCode.MUTATION_FAILED
            )
            disposition = module._SafeMutationFailureDisposition(exact_error)
            prior = RuntimeError("mutant-caller-owned-context")

            def safe_delegate(**kwargs: object) -> object:
                assert kwargs
                return disposition

            try:
                raise prior
            except RuntimeError as active_prior:
                assert active_prior is prior
                with monkeypatch.context() as patch:
                    patch.setattr(resource, "_begin_operation", capture_begin)
                    patch.setattr(
                        transaction_module,
                        "_run_atomic_transition_apply",
                        safe_delegate,
                    )
                    try:
                        session.apply_transition(None)
                    except BaseException as error:
                        observed = error
            return bool(
                observed is exact_error
                and observed.__cause__ is None
                and observed.__context__ is prior
                and len(correlations) == len(records) == 1
            )

        raise AssertionError("unhandled correlation/privacy source mutant")
    finally:
        if failure is not None:
            failure.__traceback__ = None
        observed = None
        if retained is not None:
            try:
                retained._close_with_proof()
            except BaseException:
                pass
        for mutation in mutations:
            try:
                mutation._close()
            except BaseException:
                pass
        for operation in operations:
            try:
                operation._close()
            except BaseException:
                pass
        try:
            session.close()
        except BaseException:
            pass


@pytest.mark.parametrize(
    "case",
    EXIT_POISON_SOURCE_MUTANTS,
    ids=EXIT_POISON_SOURCE_MUTANTS,
)
def test_exit_poison_compiled_source_mutant_is_causally_rejected(
    case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module, mutant_path, live_sha256 = _load_exit_poison_source_mutant(
        case,
        tmp_path,
    )
    invariant = "correlation/privacy source mutant survived"
    try:
        assert mutant_path.is_file()
        with pytest.raises(AssertionError, match=invariant):
            assert not _exercise_correlation_privacy_source_mutant(
                module,
                case,
                tmp_path / "runtime",
                monkeypatch,
            ), invariant
        assert hashlib.sha256(WRITER_PATH.read_bytes()).hexdigest() == live_sha256
    finally:
        sys.modules.pop(module.__name__, None)


def _load_compiled_writer_source_mutant(
    case: str,
    tmp_path: Path,
) -> tuple[types.ModuleType, Path, str]:
    live_before = WRITER_PATH.read_bytes()
    source = live_before.decode("utf-8")
    replacements: list[tuple[str, str]]
    if case == "01_resource_explicit_phase_gate_removed":
        replacements = [
            (
                "                    or record.phase is not _OperationRetirementPhase.EXPLICIT_RETIRED\n",
                "                    or False  # compiled source mutant removes explicit phase gate\n",
            )
        ]
    elif case == "02_unsuccessful_detach_result_accepted":
        replacements = [
            (
                "    if type(detach_result) is not tuple or len(detach_result) != 4:\n"
                "        return False\n",
                "    if detach_result is None:\n"
                "        return True  # compiled source mutant accepts failed detach\n"
                "    if type(detach_result) is not tuple or len(detach_result) != 4:\n"
                "        return False\n",
            )
        ]
    elif case == "03_handle_binding_used_instead_of_resource_record":
        replacements = [
            (
                "            admitted_lease = record.lease_reference()\n"
                "            finalizer = record.finalizer\n",
                "            admitted_lease = operation._bound_operation_lease()\n"
                "            finalizer = operation.operation_finalizer\n",
            ),
            (
                "                admitted_operation_lease = record.lease_reference()\n",
                "                admitted_operation_lease = operation._bound_operation_lease()\n",
            ),
            (
                "                    or operation_lease._finalizer is not record.finalizer\n",
                "                    or operation_lease._finalizer is not operation.operation_finalizer\n",
            ),
        ]
    elif case == "04_lease_loss_removes_record_as_normal_completion":
        replacements = [
            (
                "            else:\n"
                "                successor_record = replace(\n"
                "                    record,\n"
                "                    phase=_OperationRetirementPhase.ORPHANED,\n"
                "                    cleanup_required=True,\n"
                "                )\n"
                "                record.handle._mark_cleanup_required()\n"
                "                self._lifecycle_state = (\n"
                "                    self._state_with_replaced_operation_record_locked(\n"
                "                        state,\n"
                "                        record,\n"
                "                        successor_record,\n"
                "                    )\n"
                "                )\n"
                "                self._freeze_admission_locked()\n"
                "                self._condition.notify_all()\n",
                "            else:\n"
                "                remaining = tuple(\n"
                "                    candidate\n"
                "                    for candidate in _state_operation_records(state)\n"
                "                    if candidate is not record\n"
                "                )\n"
                "                self._lifecycle_state = self._state_after_operation_completion(\n"
                "                    state, record, remaining\n"
                "                )\n"
                "                self._condition.notify_all()\n"
                "                return\n",
            )
        ]
    else:
        raise AssertionError("unhandled writer source mutant")

    for original, replacement in replacements:
        assert source.count(original) == 1
        source = source.replace(original, replacement, 1)

    mutant_path = tmp_path / f"sqlite_writer_session_retirement_{case}.py"
    assert not mutant_path.resolve().is_relative_to(ROOT.resolve())
    mutant_path.write_text(source, encoding="utf-8")
    parsed = ast.parse(mutant_path.read_text(encoding="utf-8"), str(mutant_path))
    compile(parsed, str(mutant_path), "exec")

    module_name = f"ge_nwp_coordinator._vs1a_source_mutant_{case}"
    spec = importlib.util.spec_from_file_location(module_name, mutant_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    module._AT_FORK_REGISTERED = True
    assert WRITER_PATH.read_bytes() == live_before
    return module, mutant_path, hashlib.sha256(live_before).hexdigest()


def _run_compiled_writer_source_mutant(
    case: str,
    tmp_path: Path,
) -> None:
    module, mutant_path, live_sha256 = _load_compiled_writer_source_mutant(
        case,
        tmp_path,
    )
    assert mutant_path.is_file()
    assert hashlib.sha256(WRITER_PATH.read_bytes()).hexdigest() == live_sha256
    location = _location(tmp_path)
    initialize_database(location)
    session = module.acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = None
    fake_lease = None
    invariant = "compiled writer source mutant survived"
    try:
        if case == "02_unsuccessful_detach_result_accepted":
            class _UnsuccessfulFinalizer:
                def __init__(self) -> None:
                    self.alive = True
                    self.atexit = True

                def detach(self) -> None:
                    self.alive = False
                    return None

            module._FINALIZER_FACTORY = lambda *args: _UnsuccessfulFinalizer()

        operation = resource.operation_guard(session)
        handle = operation._completion_handle

        if case == "01_resource_explicit_phase_gate_removed":
            preparation = resource._prepare_operation_retirement(handle)
            assert preparation is not None
            assert operation._finalizer.detach() is not None
            operation._closed = True
            resource._publish_prepared_operation_retirement(
                preparation,
                operation,
            )
            assert type(resource._lifecycle_state) is not module._WriterSessionActive, invariant

        elif case == "02_unsuccessful_detach_result_accepted":
            operation._close()
            assert type(resource._lifecycle_state) is not module._WriterSessionActive, invariant

        elif case == "03_handle_binding_used_instead_of_resource_record":
            credential = resource._credential
            authority_lock = resource._authority_lock
            assert credential is not None and authority_lock is not None
            fake_lease = module._WriterSessionOperationLease(
                resource=resource,
                session=session,
                credential=credential,
                authority_lock=authority_lock,
                completion_handle=handle,
            )
            fake_finalizer = weakref.finalize(
                fake_lease,
                module._finalize_writer_session_operation,
                resource,
                handle,
            )
            fake_finalizer.atexit = False
            fake_lease._attach_finalizer(fake_finalizer)
            object.__setattr__(handle, "_operation_lease_ref", weakref.ref(fake_lease))
            object.__setattr__(handle, "_operation_finalizer", fake_finalizer)
            preparation = resource._prepare_operation_retirement(handle)
            assert preparation is not None
            assert resource._retire_operation_lease_locally(
                preparation,
                fake_lease,
            ) is True
            resource._publish_prepared_operation_retirement(
                preparation,
                fake_lease,
            )
            assert operation._closed is True, invariant

        elif case == "04_lease_loss_removes_record_as_normal_completion":
            operation_reference = weakref.ref(operation)
            operation = None
            gc.collect()
            assert operation_reference() is None
            assert type(resource._lifecycle_state) is not module._WriterSessionActive, invariant

        else:
            raise AssertionError("unhandled compiled writer source mutant")
    finally:
        if fake_lease is not None:
            try:
                fake_lease._abandon_before_publication()
            except BaseException:
                pass
        if operation is not None:
            try:
                operation._close()
            except BaseException:
                pass
        try:
            session.close()
        except BaseException:
            pass
        sys.modules.pop(module.__name__, None)
        assert hashlib.sha256(WRITER_PATH.read_bytes()).hexdigest() == live_sha256


@pytest.mark.parametrize(
    "case",
    EXPLICIT_RETIREMENT_SOURCE_MUTANTS,
    ids=EXPLICIT_RETIREMENT_SOURCE_MUTANTS,
)
def test_compiled_writer_source_mutant_is_killed(
    case: str,
    tmp_path: Path,
) -> None:
    with pytest.raises(AssertionError, match="compiled writer source mutant survived"):
        _run_compiled_writer_source_mutant(case, tmp_path)


@pytest.mark.parametrize(
    "case",
    EXPLICIT_RETIREMENT_RUNTIME_COUNTERFACTUALS,
    ids=EXPLICIT_RETIREMENT_RUNTIME_COUNTERFACTUALS,
)
def test_explicit_retirement_runtime_counterfactual_fails_closed(
    case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle

    if case == "01_dead_finalizer_accepted_as_explicit_detach":
        preparation = resource._prepare_operation_retirement(handle)
        assert preparation is not None
        assert operation._finalizer.detach() is not None
        assert operation._finalizer.alive is False
        assert resource._retire_operation_lease_locally(preparation, operation) is False
        assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX

    elif case == "02_finalizer_alive_false_before_callback_allows_active":
        callback_entered = threading.Event()
        allow_callback = threading.Event()
        callback_failures: list[BaseException] = []
        original_mark = resource._mark_operation_orphaned

        def delayed_mark(exact_handle: object) -> bool:
            callback_entered.set()
            assert allow_callback.wait(2)
            return original_mark(exact_handle)

        monkeypatch.setattr(resource, "_mark_operation_orphaned", delayed_mark)

        def invoke_exact_finalizer() -> None:
            try:
                operation._finalizer()
            except BaseException as error:
                callback_failures.append(error)

        thread = threading.Thread(target=invoke_exact_finalizer)
        thread.start()
        assert callback_entered.wait(2)
        assert operation._finalizer.alive is False
        opening_record = _operation_record_for_test(resource, handle)
        assert opening_record.cleanup_required is False

        operation._close()
        assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
        assert handle not in _state_operations_for_test(resource)
        with pytest.raises(WriterSessionError):
            resource.operation_guard(session)

        allow_callback.set()
        thread.join(2)
        assert not thread.is_alive()
        assert callback_failures == []
        assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX

    elif case == "03_direct_detach_plus_lease_collection_counts_as_retirement":
        exact_finalizer = operation._finalizer
        operation_reference = weakref.ref(operation)
        assert exact_finalizer.detach() is not None
        operation = None
        gc.collect()
        assert operation_reference() is None
        assert exact_finalizer.alive is False
        assert handle._bound_operation_lease() is None
        assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
        assert handle not in _state_operations_for_test(resource)

    elif case == "05_lease_loss_before_explicit_retirement_restores_active":
        operation_reference = weakref.ref(operation)
        operation = None
        gc.collect()
        assert operation_reference() is None
        assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
        assert not resource.active_for_owner()

    elif case == "06_lease_loss_before_explicit_retirement_strands_cleanup":
        original_continue = resource._continue_cleanup
        cleanup_attempted = threading.Event()

        def pause_cleanup(*, blocking: bool, finalizer: bool) -> None:
            assert blocking is False
            assert finalizer is True
            cleanup_attempted.set()

        monkeypatch.setattr(resource, "_continue_cleanup", pause_cleanup)
        operation_reference = weakref.ref(operation)
        operation = None
        gc.collect()
        assert operation_reference() is None
        assert cleanup_attempted.is_set()
        assert handle in _state_operations_for_test(resource)
        assert not resource.active_for_owner()

        monkeypatch.setattr(resource, "_continue_cleanup", original_continue)
        session.close()
        assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
        assert handle not in _state_operations_for_test(resource)

    elif case in (
        "07_handle_lease_binding_replacement_changes_resource_truth",
        "08_handle_finalizer_binding_replacement_changes_resource_truth",
    ):
        record = _operation_record_for_test(resource, handle)
        admitted_reference = record.lease_reference
        admitted_finalizer = record.finalizer
        if case.startswith("07_"):
            object.__setattr__(
                handle,
                "_operation_lease_ref",
                weakref.ref(operation),
            )
            assert handle._operation_lease_ref is not admitted_reference
        else:
            substitute = object()
            object.__setattr__(handle, "_operation_finalizer", substitute)
            assert handle.operation_finalizer is substitute
        unchanged = _operation_record_for_test(resource, handle)
        assert unchanged.lease_reference is admitted_reference
        assert unchanged.finalizer is admitted_finalizer
        operation._close()
        assert type(resource._lifecycle_state) is writer_module._WriterSessionActive

    elif case == "09_same_handle_fake_pair_authorizes_publication":
        credential = resource._credential
        authority_lock = resource._authority_lock
        assert credential is not None and authority_lock is not None
        fake_lease = writer_module._WriterSessionOperationLease(
            resource=resource,
            session=session,
            credential=credential,
            authority_lock=authority_lock,
            completion_handle=handle,
        )
        fake_finalizer = weakref.finalize(fake_lease, lambda: None)
        fake_finalizer.atexit = False
        fake_lease._attach_finalizer(fake_finalizer)
        object.__setattr__(handle, "_operation_lease_ref", weakref.ref(fake_lease))
        object.__setattr__(handle, "_operation_finalizer", fake_finalizer)
        preparation = resource._prepare_operation_retirement(handle)
        assert preparation is not None
        assert resource._retire_operation_lease_locally(
            preparation,
            fake_lease,
        ) is False
        with pytest.raises(WriterSessionError):
            resource._publish_prepared_operation_retirement(
                preparation,
                fake_lease,
            )
        record = _operation_record_for_test(resource, handle)
        assert record.lease_reference() is operation
        assert record.finalizer is operation._finalizer
        assert operation._closed is False
        assert operation._finalizer.alive is True
        fake_lease._abandon_before_publication()
        operation._close()
        assert type(resource._lifecycle_state) is writer_module._WriterSessionActive

    elif case == "10_explicit_retirement_accepts_unsuccessful_detach":
        class _UnsuccessfulFinalizer:
            def __init__(self) -> None:
                self.alive = True
                self.atexit = True

            def detach(self) -> None:
                self.alive = False
                return None

        operation._close()
        assert type(resource._lifecycle_state) is writer_module._WriterSessionActive

        def factory(*args: object) -> _UnsuccessfulFinalizer:
            del args
            return _UnsuccessfulFinalizer()

        monkeypatch.setattr(writer_module, "_FINALIZER_FACTORY", factory)
        operation = resource.operation_guard(session)
        handle = operation._completion_handle
        operation._close()
        assert operation._closed is True
        assert operation._finalizer.alive is False
        assert handle not in _state_operations_for_test(resource)
        assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX

    elif case == "11_orphan_cleanup_requires_missing_live_lease":
        operation._finalizer()
        assert operation is not None
        assert operation._closed is True
        assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
        assert handle not in _state_operations_for_test(resource)

    elif case == "12_gc_or_finalizer_path_publishes_normal_active":
        operation._finalizer()
        assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
        assert type(resource._lifecycle_state) is not writer_module._WriterSessionActive

    else:
        raise AssertionError("unhandled explicit-retirement counterfactual")

    session.close()


def test_explicit_normal_retirement_records_detach_before_final_assignment(
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle

    admitted = _operation_record_for_test(resource, handle)
    assert admitted.phase is writer_module._OperationRetirementPhase.ADMITTED
    assert admitted.lease_reference() is operation
    assert admitted.finalizer is operation._finalizer

    preparation = resource._prepare_operation_retirement(handle)
    assert preparation is not None
    prepared = _operation_record_for_test(resource, handle)
    assert prepared.phase is writer_module._OperationRetirementPhase.PREPARED
    assert prepared.retirement_preparation_acknowledgment is preparation
    assert not resource.active_for_owner()

    assert resource._retire_operation_lease_locally(preparation, operation) is True
    retired = _operation_record_for_test(resource, handle)
    assert retired.phase is writer_module._OperationRetirementPhase.EXPLICIT_RETIRED
    assert retired.finalizer is operation._finalizer
    assert operation._closed is True
    assert operation._finalizer.alive is False
    assert handle in _state_operations_for_test(resource)
    assert not resource.active_for_owner()

    resource._publish_prepared_operation_retirement(preparation, operation)
    assert handle not in _state_operations_for_test(resource)
    assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
    session.close()


LEASE_DISAPPEARANCE_PHASES = (
    "before_phase1",
    "after_phase1",
    "before_explicit_terminality",
    "after_local_terminality_before_detach",
    "after_successful_detach_before_final_assignment",
)


@pytest.mark.parametrize(
    "phase",
    LEASE_DISAPPEARANCE_PHASES,
    ids=LEASE_DISAPPEARANCE_PHASES,
)
def test_lease_disappearance_phase_matrix(
    phase: str,
    tmp_path: Path,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    operation_reference = weakref.ref(operation)
    preparation = None

    if phase != "before_phase1":
        preparation = resource._prepare_operation_retirement(handle)
        assert preparation is not None

    if phase == "after_local_terminality_before_detach":
        failure = RuntimeError("before-explicit-detach")
        _trace_raise_at(
            writer_module._WriterSessionResource._retire_operation_lease_locally,
            "finalizer.detach()",
            failure,
        )
        try:
            with pytest.raises(RuntimeError) as captured:
                resource._retire_operation_lease_locally(preparation, operation)
        finally:
            sys.settrace(None)
        assert captured.value is failure
        interrupted = _operation_record_for_test(resource, handle)
        assert interrupted.phase is writer_module._OperationRetirementPhase.ORPHANED
        assert interrupted.cleanup_required is True
        failure.__traceback__ = None
        del captured
    elif phase == "after_successful_detach_before_final_assignment":
        assert resource._retire_operation_lease_locally(preparation, operation) is True
        retired = _operation_record_for_test(resource, handle)
        assert retired.phase is writer_module._OperationRetirementPhase.EXPLICIT_RETIRED
        assert operation._finalizer.alive is False

    operation = None
    gc.collect()
    assert operation_reference() is None
    assert handle not in _state_operations_for_test(resource)

    if phase == "after_successful_detach_before_final_assignment":
        assert type(resource._lifecycle_state) is writer_module._WriterSessionActive
        followup = resource.operation_guard(session)
        followup._close()
    else:
        assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
        assert not resource.active_for_owner()
    session.close()


SESSION_DISAPPEARANCE_CASES = (
    "lease_gone_wrapper_live",
    "lease_gone_wrapper_collected",
    "session_finalizer_with_represented_orphan",
)


@pytest.mark.parametrize(
    "case",
    SESSION_DISAPPEARANCE_CASES,
    ids=SESSION_DISAPPEARANCE_CASES,
)
def test_session_wrapper_disappearance_matrix(
    case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    operation_reference = weakref.ref(operation)

    if case == "session_finalizer_with_represented_orphan":
        original_continue = resource._continue_cleanup

        def pause_cleanup(*, blocking: bool, finalizer: bool) -> None:
            assert blocking is False
            assert finalizer is True

        monkeypatch.setattr(resource, "_continue_cleanup", pause_cleanup)
        operation = None
        gc.collect()
        assert operation_reference() is None
        assert handle in _state_operations_for_test(resource)
        record = _operation_record_for_test(resource, handle)
        assert record.phase is writer_module._OperationRetirementPhase.ORPHANED
        monkeypatch.setattr(resource, "_continue_cleanup", original_continue)
        session._finalizer()
        assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
        assert handle not in _state_operations_for_test(resource)
        session.close()
        return

    session_reference = weakref.ref(session)
    operation = None
    if case == "lease_gone_wrapper_collected":
        session = None
    gc.collect()
    assert operation_reference() is None
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
    assert handle not in _state_operations_for_test(resource)
    if case == "lease_gone_wrapper_live":
        assert session_reference() is session
        session.close()
    else:
        assert session_reference() is None


@pytest.mark.parametrize("kind", PROCESS_CONTROL_KINDS, ids=PROCESS_CONTROL_KINDS)
def test_process_control_after_lease_loss_classification_reaches_terminal_x(
    kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    location = _location(tmp_path)
    initialize_database(location)
    session = acquire_sqlite_writer_session(location)
    resource = session._resource
    operation = resource.operation_guard(session)
    handle = operation._completion_handle
    operation_reference = weakref.ref(operation)
    failure = _process_control_for_kind(kind)
    original_continue = resource._continue_cleanup
    calls = 0

    def interrupt_once(*, blocking: bool, finalizer: bool) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            record = _operation_record_for_test(resource, handle)
            assert record.phase is writer_module._OperationRetirementPhase.ORPHANED
            raise failure
        original_continue(blocking=blocking, finalizer=finalizer)

    monkeypatch.setattr(resource, "_continue_cleanup", interrupt_once)
    operation = None
    gc.collect()
    assert operation_reference() is None
    assert calls >= 2
    assert type(resource._lifecycle_state) is writer_module._WriterSessionTerminalX
    assert handle not in _state_operations_for_test(resource)
    session.close()


@pytest.mark.parametrize(
    "guard",
    SECONDARY_AST_GUARDS,
    ids=SECONDARY_AST_GUARDS,
)
def test_vs1a_secondary_identity_ast_guard(guard: str) -> None:
    if guard == "resource-identity-comparisons":
        for source_path in (CONNECTION_PATH, WRITER_PATH):
            source = source_path.read_text(encoding="utf-8")
            comparisons = [
                node
                for node in ast.walk(ast.parse(source))
                if isinstance(node, ast.Compare)
                and "resource_identity"
                in (ast.get_source_segment(source, node) or "")
            ]
            assert comparisons
            assert all(
                all(
                    isinstance(operator, (ast.Is, ast.IsNot))
                    for operator in node.ops
                )
                for node in comparisons
            )
        return

    if guard == "no-process-global-identity-registry":
        for source_path in (CONNECTION_PATH, WRITER_PATH):
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
            mutable_identity_globals = [
                node
                for node in tree.body
                if isinstance(node, (ast.Assign, ast.AnnAssign))
                and isinstance(
                    node.value,
                    (
                        ast.Dict,
                        ast.List,
                        ast.Set,
                        ast.DictComp,
                        ast.ListComp,
                        ast.SetComp,
                    ),
                )
                and "RESOURCE" in ast.unparse(node).upper()
                and "IDENTITY" in ast.unparse(node).upper()
            ]
            assert mutable_identity_globals == []
        return

    if guard == "opaque-identity-surface":
        identity = connection_module._new_writer_session_resource_identity()
        assert repr(identity) == "<_WriterSessionResourceIdentity>"
        with pytest.raises(TypeError):
            identity.__reduce__()
        assert "_WriterSessionResourceIdentity" not in writer_module.__all__
        assert "_WriterSessionResourceIdentity" not in getattr(
            connection_module,
            "__all__",
            (),
        )
        return

    if guard == "caller-envelope-bytecode":
        for effect_kind in ("transition", "global-stop"):
            public, guarded = _guarded_public_code(effect_kind)
            public_instructions = list(dis.get_instructions(public))
            public_entries = dis.Bytecode(public).exception_entries
            guarded_call = next(
                instruction
                for instruction in public_instructions
                if instruction.opname == "CALL"
                and any(
                    entry.start <= instruction.offset < entry.end
                    for entry in public_entries
                )
            )
            assert any(
                entry.start <= guarded_call.offset < entry.end
                for entry in public_entries
            )
            normal_cleanup = _instruction_offset(guarded, opname="SWAP")
            assert not any(
                entry.start <= normal_cleanup < entry.end
                for entry in dis.Bytecode(guarded).exception_entries
            )
            public_source = inspect.getsource(
                getattr(
                    writer_module._SQLiteWriterSession,
                    (
                        "apply_transition"
                        if effect_kind == "transition"
                        else "apply_global_stop_update"
                    ),
                )
            )
            assert "except (KeyboardInterrupt, SystemExit, GeneratorExit) as governing:" in public_source
            assert "_stabilize_operation_exit_for_process_control(" in public_source
        exit_code = writer_module._WriterSessionOperationLease.__exit__.__code__
        close_code = writer_module._WriterSessionOperationLease._close.__code__
        assert _first_instruction_offset(exit_code) < min(
            entry.start for entry in dis.Bytecode(exit_code).exception_entries
        )
        assert _first_instruction_offset(close_code) < min(
            entry.start for entry in dis.Bytecode(close_code).exception_entries
        )
        return

    if guard == "pre-admission-token-correlation-and-privacy":
        for method in (
            writer_module._SQLiteWriterSession.apply_transition,
            writer_module._SQLiteWriterSession.apply_global_stop_update,
        ):
            source = inspect.getsource(method)
            assert "_new_operation_invocation_correlation()" in source
            assert "_guarded_" in source
            assert "_invocation_correlation" in source
            assert "_sanitize_exception_traceback_graph_at_outward_boundary(" in source
            assert "governing,\n                _sanitize_exception_traceback_graph," in source
            assert "safe_error,\n                    _sanitize_exception_traceback_graph," in source
            assert "raise governing" not in source
            assert "operation_handle = operation_lease._completion_handle" not in source
        stabilize_source = inspect.getsource(
            writer_module._WriterSessionResource
            ._stabilize_operation_exit_for_process_control
        )
        assert "candidate.handle.invocation_correlation" in stabilize_source
        assert "is invocation_correlation" in stabilize_source
        assert "invocation_correlation.resource_identity is not self._resource_identity" in stabilize_source
        assert "self._process_owner_pid_value == -1" in stabilize_source
        assert "thread" not in writer_module._OperationExitProcessControlDisposition.__dict__
        assert not any(
            token in stabilize_source
            for token in (
                "sys.exception",
                "traceback",
                "SystemExit.code",
                "transition_command",
                "global_stop_command",
                "typed_operator_decision",
                "credential",
            )
        )
        return

    if guard == "poison-publication-order":
        source = inspect.getsource(
            writer_module._WriterSessionResource
            ._stabilize_operation_exit_for_process_control
        )
        assignment = "self._operation_exit_process_control_poisoned_value = True"
        assert source.count(assignment) == 1
        exact_match = "candidate.handle.invocation_correlation"
        assert source.index(exact_match) < source.index(assignment)
        pre_poison = source[: source.index(assignment)]
        assert not any(
            helper in pre_poison
            for helper in (
                "_lifecycle_epoch",
                "_state_authority",
                "_state_operation_records",
                "_operation_blocks_admission",
                "_state_with_replaced_operation_record_locked",
                "_state_after_operation_completion",
                "_mark_operation_cleanup_required",
                "notify",
            )
        )
        parsed = ast.parse(textwrap.dedent(source))
        function = parsed.body[0]
        assert isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef))
        poison_nodes = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Attribute)
            and node.targets[0].attr
            == "_operation_exit_process_control_poisoned_value"
        ]
        assert len(poison_nodes) == 1
        poison_node = poison_nodes[0]
        pre_poison_calls = [
            call
            for call in ast.walk(function)
            if isinstance(call, ast.Call) and call.lineno < poison_node.lineno
        ]
        assert pre_poison_calls
        assert all(
            isinstance(call.func, ast.Name) and call.func.id == "type"
            for call in pre_poison_calls
        )
        pre_poison_attributes = {
            node.attr
            for node in ast.walk(function)
            if isinstance(node, ast.Attribute) and node.lineno < poison_node.lineno
        }
        assert not pre_poison_attributes & {
            "_lifecycle_epoch",
            "_owner_pid",
            "active_for_owner",
        }
        record_loop = next(
            node
            for node in ast.walk(function)
            if isinstance(node, ast.For)
            and isinstance(node.target, ast.Name)
            and node.target.id == "candidate"
        )
        exact_branch = next(node for node in record_loop.body if isinstance(node, ast.If))
        first_match_branch = exact_branch.body[0]
        assert isinstance(first_match_branch, ast.If)
        assert len(first_match_branch.body) == 2
        record_assignment, poison_assignment = first_match_branch.body
        assert isinstance(record_assignment, ast.Assign)
        assert isinstance(record_assignment.targets[0], ast.Name)
        assert record_assignment.targets[0].id == "exact_record"
        assert isinstance(poison_assignment, ast.Assign)
        assert isinstance(poison_assignment.targets[0], ast.Attribute)
        assert poison_assignment.targets[0].attr == (
            "_operation_exit_process_control_poisoned_value"
        )
        assert all(
            isinstance(call.func, ast.Name) and call.func.id == "type"
            for call in ast.walk(exact_branch.test)
            if isinstance(call, ast.Call)
        )
        assert source.index(assignment) < source.index("_operation_blocks_admission(")
        assert source.index(assignment) < source.index(
            "self._mark_operation_cleanup_required(exact_record.handle)"
        )
        assert source.index(assignment) < source.index("self._condition.notify_all()")
        instructions = list(
            dis.get_instructions(
                writer_module._WriterSessionResource
                ._stabilize_operation_exit_for_process_control
            )
        )
        poison_instruction_index = next(
            index
            for index, instruction in enumerate(instructions)
            if instruction.opname == "STORE_ATTR"
            and instruction.argval
            == "_operation_exit_process_control_poisoned_value"
        )
        bytecode_pre_poison = instructions[:poison_instruction_index]
        assert not any(
            instruction.argval in {
                "_lifecycle_epoch",
                "_state_authority",
                "_state_operation_records",
                "_operation_blocks_admission",
            }
            for instruction in bytecode_pre_poison
        )
        assert not any(
            instruction.opname == "LOAD_METHOD"
            for instruction in bytecode_pre_poison
        )
        bytecode_call_indices = [
            index
            for index, instruction in enumerate(bytecode_pre_poison)
            if instruction.opname in ("CALL", "CALL_FUNCTION_EX")
        ]
        context_exit_call_indices = [
            index
            for index in bytecode_call_indices
            if bytecode_pre_poison[index].opname == "CALL"
            and bytecode_pre_poison[index].arg == 2
            and all(
                instruction.opname == "LOAD_CONST"
                and instruction.argval is None
                for instruction in bytecode_pre_poison[index - 3 : index]
            )
        ]
        assert len(context_exit_call_indices) == 1
        assert len(bytecode_call_indices) - 1 == len(pre_poison_calls)
        bytecode_names = [instruction.argval for instruction in bytecode_pre_poison]
        assert bytecode_names.index("resource_identity") < bytecode_names.index(
            "_process_owner_pid_value"
        )
        assert bytecode_names.index("_process_owner_pid_value") < bytecode_names.index(
            "_condition"
        )
        assert bytecode_names.index("_condition") < bytecode_names.index(
            "_lifecycle_state"
        )
        exact_identity_load_index = max(
            index
            for index, name in enumerate(bytecode_names)
            if name == "invocation_correlation"
        )
        assert bytecode_names.index("_lifecycle_state") < exact_identity_load_index
        assert exact_identity_load_index < len(bytecode_pre_poison)
        return

    if guard == "sanitizer-base-descriptor-boundary":
        core_source = inspect.getsource(
            writer_module._sanitize_exception_traceback_graph_pass
        )
        assert "_base_descriptor_set(" in core_source
        assert "_base_descriptor_get(" in core_source
        assert "_group_descriptor_get(" in core_source
        assert core_source.index("_base_descriptor_set(") < core_source.index(
            "cause = _base_descriptor_get("
        )
        assert "object.__getattribute__(current" not in core_source
        assert "object.__setattr__(current" not in core_source
        assert "getattr(current" not in core_source
        assert "current.__traceback__" not in core_source
        assert "current.__cause__" not in core_source
        assert "current.__context__" not in core_source
        assert "current.args" not in core_source
        assert "current.__dict__" not in core_source
        assert "current.exceptions" not in core_source
        assert "current_type is dict" in core_source
        assert "current_type in (tuple, list, set, frozenset)" in core_source
        assert (
            writer_module._BASE_EXCEPTION_TRACEBACK_DESCRIPTOR
            is BaseException.__dict__["__traceback__"]
        )
        assert (
            writer_module._BASE_EXCEPTION_CAUSE_DESCRIPTOR
            is BaseException.__dict__["__cause__"]
        )
        assert (
            writer_module._BASE_EXCEPTION_CONTEXT_DESCRIPTOR
            is BaseException.__dict__["__context__"]
        )
        assert (
            writer_module._BASE_EXCEPTION_ARGS_DESCRIPTOR
            is BaseException.__dict__["args"]
        )
        assert (
            writer_module._BASE_EXCEPTION_DICTIONARY_DESCRIPTOR
            is BaseException.__dict__["__dict__"]
        )
        assert (
            writer_module._BASE_EXCEPTION_GROUP_CHILDREN_DESCRIPTOR
            is BaseExceptionGroup.__dict__["exceptions"]
        )
        primary_source = inspect.getsource(
            writer_module._sanitize_exception_traceback_graph
        )
        boundary_source = inspect.getsource(
            writer_module._sanitize_exception_traceback_graph_at_outward_boundary
        )
        assert "except Exception:" in primary_source
        assert "_fallback_pass(root)" in primary_source
        assert "except Exception:" in boundary_source
        assert "_fallback_pass(root)" in boundary_source
        assert (
            writer_module._sanitize_exception_traceback_graph.__defaults__[-1]
            is writer_module._sanitize_exception_traceback_graph_pass
        )
        assert (
            writer_module
            ._sanitize_exception_traceback_graph_at_outward_boundary
            .__defaults__[-1]
            is writer_module._sanitize_exception_traceback_graph_pass
        )
        return

    if guard == "poison-readers-and-monotonicity":
        module_source = WRITER_PATH.read_text(encoding="utf-8")
        assert module_source.count(
            "self._operation_exit_process_control_poisoned_value = False"
        ) == 1
        assert module_source.count(
            "self._operation_exit_process_control_poisoned_value = True"
        ) == 1
        for function in (
            writer_module._WriterSessionResource.active_for_owner,
            writer_module._WriterSessionResource._require_active_lifecycle,
            writer_module._WriterSessionResource._begin_operation,
            writer_module._WriterSessionResource._acquire_mutation_lease_for_operation,
            writer_module._WriterSessionResource._activate_controller_scope_for_operation,
            writer_module._WriterSessionResource._require_active_mutation_authority_for_operation,
            writer_module._WriterSessionResource._release_mutation_slot,
            writer_module._WriterSessionResource._clear_mutation_slot_owned_by_operation,
            writer_module._WriterSessionResource._select_controller_successor_locked,
            writer_module._WriterSessionResource._state_after_operation_completion,
        ):
            assert "_operation_exit_process_control_poisoned_value" in inspect.getsource(
                function
            )
        return

    if guard == "mutation-usability-path-separation":
        source = inspect.getsource(
            writer_module._WriterSessionResource.require_usable_for_mutation
        )
        assert "_prepare_for_context_exit=True" in source
        assert "_stabilize_operation_exit_for_process_control" not in source
        assert "except (KeyboardInterrupt, SystemExit, GeneratorExit)" not in source
        for method in (
            writer_module._SQLiteWriterSession.apply_transition,
            writer_module._SQLiteWriterSession.apply_global_stop_update,
        ):
            assert "_prepare_for_context_exit=True" not in inspect.getsource(method)
        return

    raise AssertionError("unhandled secondary identity AST guard")


def test_lifecycle_components_have_one_structural_owner() -> None:
    assert tuple(writer_module._WriterSessionActivity.__dataclass_fields__) == (
        "authority",
        "operation_records",
    )
    assert tuple(writer_module._WriterSessionMutationFrame.__dataclass_fields__) == (
        "activity",
        "slot",
    )
    assert tuple(writer_module._WriterSessionMutationActive.__dataclass_fields__) == ("frame",)
    for state_type in (
        writer_module._WriterSessionAbortCloseUnproved,
        writer_module._WriterSessionCommitUncertainUnproved,
        writer_module._WriterSessionCommitKnownUnproved,
        writer_module._WriterSessionAbortPendingCleanup,
        writer_module._WriterSessionCommitUncertainPendingCleanup,
        writer_module._WriterSessionCommitKnownPendingCleanup,
    ):
        fields = set(state_type.__dataclass_fields__)
        assert not fields & {"authority", "operations", "slot"}
    source = WRITER_PATH.read_text(encoding="utf-8")
    assert "class _OperationCompletionToken" not in source
    assert "class _WriterSessionOperationRecord" in source
    assert tuple(
        writer_module._WriterSessionOperationRecord.__dataclass_fields__
    ) == (
        "handle",
        "resource_identity",
        "operation_id",
        "owner_pid",
        "owner_thread",
        "lifecycle_epoch",
        "lease_reference",
        "finalizer",
        "phase",
        "cleanup_required",
        "mutation_release_acknowledgment",
        "retirement_preparation_acknowledgment",
    )
    assert "class _ControllerPreparedSuccessors" not in source


def test_cleanup_claim_has_no_pending_state_or_cursor_duplicate() -> None:
    fields = set(writer_module._WriterSessionCleanupClaim.__dataclass_fields__)
    assert "pending_state_identity" not in fields
    assert "resume_cursor" not in fields
    assert tuple(writer_module._WriterSessionCleanupClaimed.__dataclass_fields__) == (
        "pending_state",
        "claim",
    )


def test_close_proof_owner_has_no_callback_parameter_and_noop_cannot_mint_proof() -> None:
    signature = inspect.signature(
        connection_module._RetainedSQLiteConnection._close_with_proof
    )
    assert tuple(signature.parameters) == ("self",)
    connection = sqlite3.connect(":memory:")
    retained = connection_module._make_retained_sqlite_connection(
        connection, _new_test_resource_identity()
    )
    with pytest.raises(TypeError):
        retained._close_with_proof(lambda: None)
    assert retained._borrow_exact_connection() is connection
    assert type(retained._close_with_proof()) is connection_module._SQLiteConnectionCloseProof


def test_close_proof_has_one_exact_production_construction_site() -> None:
    tree = ast.parse(CONNECTION_PATH.read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_SQLiteConnectionCloseProof"
    ]
    assert len(calls) == 1
    source = inspect.getsource(connection_module._RetainedSQLiteConnection._close_with_proof)
    assert source.count("sqlite3.Connection.close(exact_connection)") == 1
    assert source.index("sqlite3.Connection.close(exact_connection)") < source.index(
        "proof = _SQLiteConnectionCloseProof("
    )
