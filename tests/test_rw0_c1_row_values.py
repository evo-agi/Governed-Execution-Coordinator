from __future__ import annotations

import copy

import pytest

import ge_nwp_coordinator._rw0_c1_row_values as rows


EXPECTED_TABLES = (
    "rw0_phase_instances", "rw0_evidence_values", "rw0_evidence_memberships",
    "rw0_relation_bindings", "rw0_relation_operands", "rw0_c1_mutation_receipts",
    "rw0_authority_verification_observations",
    "rw0_subordinate_authorization_proposals",
    "rw0_custody_availability_observations",
    "rw0_retrieval_capability_event_observations",
    "rw0_remote_host_readiness_observations", "rw0_effect_host_qualifications",
    "rw0_worker_mechanism_capability_declarations",
    "rw0_worker_mechanism_capability_observations",
    "rw0_worker_mechanism_capability_qualifications",
    "rw0_wire_cancellation_request_observations",
    "rw0_wire_process_observations", "rw0_c2a_worker_observations",
    "rw0_wire_worker_result_bindings",
    "rw0_wire_process_result_classification_bindings",
    "rw0_section41_post_execution_proposal_family_members",
    "rw0_authority_observation_effect_classes",
    "rw0_c2a_worker_observation_evidence_refs",
)


def test_row_inventory_and_ordered_columns_are_exact_and_typed() -> None:
    assert tuple(spec.table_name for spec in rows.ROW_SPECS) == EXPECTED_TABLES
    assert len(rows.ROW_SPECS) == 23
    assert len(rows.PHASE_COLUMNS) == 76
    assert rows.EVIDENCE_VALUE_COLUMNS == (
        "schema_id", "kind_rank", "value_ref", "value_digest",
        "value_schema_id", "scope_class", "value_row_digest",
    )
    assert rows.MEMBERSHIP_COLUMNS[:4] == (
        "schema_id", "membership_ref", "membership_digest", "phase_basis_ref",
    )
    assert rows.RELATION_COLUMNS[-3:] == (
        "operand_count", "operand_set_digest", "relation_row_digest",
    )
    assert rows.OPERAND_COLUMNS[-5:] == (
        "operand_schema_id", "operand_ref", "operand_digest",
        "operand_scope_digest", "operand_row_digest",
    )
    assert all(
        len(spec.columns) == len(set(spec.columns)) for spec in rows.ROW_SPECS
    )


def test_kind_scoped_registry_row_is_self_digesting_and_content_free() -> None:
    identity = {
        "schema_id": "governed-execution.nwp-rw0-c1-evidence-value-row.v1",
        "kind_rank": 5,
        "value_ref": "readiness.safe.0001",
        "value_digest": "a" * 64,
        "value_schema_id": (
            "governed-execution.nwp-rw0-remote-host-readiness-observation.v1"
        ),
        "scope_class": "global_reusable",
    }
    mapping = rows.build_row_mapping("rw0_evidence_values", identity)
    value = rows.rw0_c1_row_value_from_mapping("rw0_evidence_values", mapping)
    assert value.to_mapping() == mapping
    assert value.value("kind_rank") == 5
    assert repr(value) == "<RW0C1RowValue>"
    assert "readiness.safe.0001" not in repr(value)
    with pytest.raises(TypeError):
        copy.copy(value)
    damaged = dict(mapping)
    damaged["scope_class"] = "phase_bound"
    with pytest.raises(rows.RW0C1RowValidationError):
        rows.rw0_c1_row_value_from_mapping("rw0_evidence_values", damaged)


def test_typed_tables_and_normalized_children_pin_kind_and_value_schema() -> None:
    assert len(rows.AUTHORITY_OBSERVATION_COLUMNS) > 50
    assert rows.AUTHORITY_OBSERVATION_COLUMNS[-1] == "payload_row_digest"
    assert rows.C2A_OBSERVATION_COLUMNS[-1] == "payload_row_digest"
    assert rows.WORKER_RESULT_BINDING_COLUMNS[1:5] == (
        "kind_rank", "value_ref", "value_digest", "value_schema_id",
    )
    assert "result_state" in rows.PROCESS_RESULT_BINDING_COLUMNS
    assert "result_failure_reason" in rows.PROCESS_RESULT_BINDING_COLUMNS
    assert "owner_family_graph_digest" in rows.SECTION41_MEMBER_COLUMNS
    assert rows.AUTHORITY_EFFECT_CLASS_COLUMNS[-1] == "child_row_digest"
    assert rows.C2A_EVIDENCE_REF_COLUMNS[-1] == "child_row_digest"


def test_mapping_and_tuple_adapters_reject_unknown_shape_or_digest() -> None:
    with pytest.raises(rows.RW0C1RowValidationError):
        rows.rw0_c1_row_value_from_mapping("unknown", {})
    with pytest.raises(rows.RW0C1RowValidationError):
        rows.rw0_c1_row_value_from_tuple("rw0_evidence_values", ())
