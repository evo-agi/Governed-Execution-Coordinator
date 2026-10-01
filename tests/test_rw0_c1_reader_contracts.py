from __future__ import annotations

import ge_nwp_coordinator._sqlite_rw0_c1_reader_contracts as readers
from ge_nwp_coordinator._rw0_c1_row_values import ROW_SPEC_BY_TABLE


def test_literal_reader_inventory_is_closed_bounded_and_explicit() -> None:
    specifications = readers.ALL_SELECT_SPECIFICATIONS
    assert len(specifications) == 52
    assert len({item.query_id for item in specifications}) == 52
    assert {item.fetch_limit for item in specifications} == {
        2, 3, 15, 16, 257, 258,
    }
    for item in specifications:
        if item is readers.SECTION41_POST_EXECUTION_EVIDENCE_FAMILY:
            assert item.table_name == (
                "development_model_proposal_evidence_bindings"
            )
        else:
            assert item.columns == ROW_SPEC_BY_TABLE[item.table_name].columns
        assert item.sql.startswith(
            f"SELECT {', '.join(item.columns)} FROM {item.table_name} "
        )
        assert "SELECT *" not in item.sql.upper()
        assert item.sql.endswith(f"LIMIT {item.fetch_limit}")
        assert ";" not in item.sql


def test_relation_operand_page_and_child_overflow_limits_are_exact() -> None:
    assert readers.RELATIONS_FOR_PHASE.fetch_limit == 3
    assert readers.RELATIONS_FOR_MEMBERSHIP.fetch_limit == 3
    assert readers.OPERANDS_FOR_RELATION.fetch_limit == 15
    assert readers.AUTHORITY_EFFECT_CLASSES.fetch_limit == 16
    assert readers.AUTHORITY_EFFECT_CLASSES_BY_DIGEST.fetch_limit == 16
    assert readers.MEMBERSHIP_PAGE.fetch_limit == 257
    assert readers.C2A_EVIDENCE_REFS.fetch_limit == 258
    assert readers.C2A_EVIDENCE_REFS_BY_DIGEST.fetch_limit == 258
    assert (
        "ORDER BY relation_rank ASC, relation_ref ASC"
        in readers.RELATIONS_FOR_MEMBERSHIP.sql
    )
    assert "ORDER BY operand_ordinal ASC" in readers.OPERANDS_FOR_RELATION.sql
    assert "WHERE relation_ref = ?" in readers.OPERANDS_FOR_RELATION.sql
    assert "phase_basis_ref = ?" not in readers.OPERANDS_FOR_RELATION.sql
    assert len(readers.TYPED_VALUE_BY_KIND_REF) == 15
    assert len(readers.TYPED_VALUE_BY_KIND_DIGEST) == 15
    assert all(
        "kind_rank = ? AND value_digest = ?" in item.sql
        for item in readers.TYPED_VALUE_BY_KIND_DIGEST
    )
    assert (
        "ORDER BY kind_rank ASC, membership_ref ASC"
        in readers.MEMBERSHIP_PAGE.sql
    )
    section41 = readers.SECTION41_POST_EXECUTION_EVIDENCE_FAMILY
    assert section41.fetch_limit == 16
    assert "WHERE proposal_ref = ?" in section41.sql
    assert (
        "ORDER BY role_rank, ordinal, evidence_role, evidence_set_ref, "
        "evidence_ref, evidence_digest, evidence_binding_digest, "
        "proposal_phase, schema_id, required_for_selection, evidence_bound_at"
        in section41.sql
    )


def test_owner_reader_contracts_are_literal_data_only_limit_two_queries() -> None:
    assert tuple(item.role for item in readers.OWNER_DEVELOPMENT_SELECTS) == (
        "development_work_spec_binding",
        "development_attempt_fence",
        "development_effect_fence",
        "development_author_command",
        "development_delivery_attempt",
    )
    for item in readers.OWNER_DEVELOPMENT_SELECTS:
        assert item.fetch_limit == 2
        assert item.sql.startswith(
            f"SELECT {', '.join(item.columns)} FROM {item.table_name} "
        )
        assert item.sql.endswith("LIMIT 2")
        assert "SELECT *" not in item.sql.upper()
