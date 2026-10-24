"""Closed safe-basis, command, row and result grammar for native post-D2 A."""

from __future__ import annotations

from dataclasses import replace
import copy
import json

import pytest

from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture
from ge_nwp_coordinator._rw0_d2_offline import run_rw0_d2_offline
from ge_nwp_coordinator._rw0_d2_post_execution_continuation import prepare_record_command
from ge_nwp_coordinator._section41_post_execution_proposal_mutation_contracts import (
    PostExecutionEvidenceSelectorV1,
    RecordPostExecutionProposalResultV1,
    checked_safe_basis_bytes,
    safe_basis_digest,
)
from ge_nwp_coordinator._section41_post_execution_proposal_row_values import (
    _CONTEXT_TABLE, _RECEIPT_TABLE, row_from_mapping, seal_row,
)
from test_rw0_d1_offline_integration import work_spec
from test_rw0_d2_post_execution_admission_integration import _omit_optional_capture_observation


@pytest.fixture(scope="module")
def real_basis() -> tuple[object, bytes]:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        return prepare_record_command(run)


@pytest.fixture(scope="module")
def two_observation_basis() -> tuple[object, bytes]:
    patch = pytest.MonkeyPatch()
    try:
        _omit_optional_capture_observation(patch)
        work = work_spec()
        with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
            return prepare_record_command(run)
    finally:
        patch.undo()


def test_both_exact_safe_basis_layouts_and_rank_mutants(
    real_basis: tuple[object, bytes], two_observation_basis: tuple[object, bytes],
) -> None:
    for count, (_command, encoded) in ((14, real_basis), (13, two_observation_basis)):
        assert checked_safe_basis_bytes(encoded) == encoded
        witness = json.loads(encoded)["d2_checkpoint_witness"]["checked_memberships"]
        assert len(witness) == count
        expected = (
            (12, 12, 12, 13, 14, 1, 1, 5, 6, 12, 6, 12, 1)
            if count == 13 else
            (12, 12, 12, 12, 13, 14, 1, 1, 5, 6, 12, 6, 12, 1)
        )
        assert tuple(item["kind_rank"] for item in witness) == expected
        for mutation in ("rank", "order", "omitted", "inserted", "bool_rank"):
            altered = json.loads(encoded)
            members = altered["d2_checkpoint_witness"]["checked_memberships"]
            tail = count - 11
            if mutation == "rank":
                members[tail + 1]["kind_rank"] = 12
            elif mutation == "order":
                members[tail], members[tail + 1] = members[tail + 1], members[tail]
            elif mutation == "omitted":
                members.pop(tail + 1)
            elif mutation == "inserted":
                members.insert(tail + 1, copy.deepcopy(members[tail + 1]))
            else:
                members[tail + 1]["kind_rank"] = True
            with pytest.raises(ValueError):
                checked_safe_basis_bytes(altered)


def test_real_basis_is_exact_closed_canonical_and_bounded(real_basis: tuple[object, bytes]) -> None:
    command, encoded = real_basis
    assert checked_safe_basis_bytes(encoded) == encoded
    assert len(encoded) < 131072
    assert safe_basis_digest(encoded) == command.safe_basis_digest
    for private_marker in (
        b'"typed_canonical_value"', b'"support_set_canonical_value"',
        b'"raw_prompt"', b'"raw_response"', b'/Users/', b'PRIVATE_CANARY',
    ):
        assert private_marker not in encoded
    basis = json.loads(encoded)
    assert set(basis) == {
        "lineage_v01", "context_v02", "capsule_safe_projection_v04",
        "model_safe_projection_v05", "private_input_manifest_v07",
        "model_input_binding_v09", "artifact_safe_projection",
        "d2_checkpoint_witness",
    }
    assert len(basis["d2_checkpoint_witness"]["checked_memberships"]) == 14
    assert len(basis["d2_checkpoint_witness"]["bound_effects"]) == 2
    assert len(basis["d2_checkpoint_witness"]["child_attestations"]) == 3
    assert tuple(item.role for item in command.evidence_selectors) == (
        "candidate_capsule", "worker_result", "validation_result",
        "independent_review", "standing_policy", "risk_lane",
        "authority_currentness_attestation", "global_stop", "effect_ceiling",
    )


@pytest.mark.parametrize("addition", [
    {"private_input_supply_v10": {"typed_canonical_value": "PRIVATE_CANARY"}},
    {"role_supply_v11": {"raw_payload": "PRIVATE_CANARY"}},
    {"path": "/tmp/PRIVATE_CANARY"},
    {"raw_work_spec": "PRIVATE_CANARY"},
])
def test_retention_allowlist_rejects_private_extensions(
    real_basis: tuple[object, bytes], addition: dict[str, object],
) -> None:
    basis = json.loads(real_basis[1])
    basis.update(addition)
    with pytest.raises(ValueError):
        checked_safe_basis_bytes(basis)
    assert b"PRIVATE_CANARY" not in real_basis[1]


def test_duplicate_keys_noncanonical_bytes_and_size_ceiling_refuse(
    real_basis: tuple[object, bytes],
) -> None:
    encoded = real_basis[1]
    with pytest.raises(ValueError):
        checked_safe_basis_bytes(b'{"lineage_v01":{},"lineage_v01":{}}')
    with pytest.raises(ValueError):
        checked_safe_basis_bytes(b" " + encoded)
    with pytest.raises(ValueError):
        checked_safe_basis_bytes(b" " * 131072)
    with pytest.raises(ValueError):
        checked_safe_basis_bytes(b" " * 131073)


def test_exact_nested_types_and_relations_refuse(real_basis: tuple[object, bytes]) -> None:
    basis = json.loads(real_basis[1])
    bad = copy.deepcopy(basis)
    bad["d2_checkpoint_witness"]["checked_memberships"][0]["kind_rank"] = True
    with pytest.raises(ValueError):
        checked_safe_basis_bytes(bad)
    bad = copy.deepcopy(basis)
    bad["context_v02"]["lineage_context_ref"] = "alien.context"
    with pytest.raises(ValueError):
        checked_safe_basis_bytes(bad)
    bad = copy.deepcopy(basis)
    bad["d2_checkpoint_witness"]["child_attestations"][2]["cleanup_complete"] = False
    with pytest.raises(ValueError):
        checked_safe_basis_bytes(bad)


def test_command_selector_and_result_digests_are_closed(real_basis: tuple[object, bytes]) -> None:
    command = real_basis[0]
    with pytest.raises(ValueError):
        replace(command, proposal_digest="0" * 64)
    with pytest.raises(ValueError):
        replace(command, evidence_selectors=command.evidence_selectors[::-1], command_digest="")
    selector = command.evidence_selectors[0]
    with pytest.raises(ValueError):
        PostExecutionEvidenceSelectorV1(
            selector.role, True, selector.ordinal, selector.schema_id,
            selector.ref, selector.digest,
        )
    result = RecordPostExecutionProposalResultV1(
        mutation_ref=command.mutation_ref, command_digest=command.command_digest,
        disposition="fresh_committed", proposal_ref=command.proposal_ref,
        context_ref=command.context_ref, context_row_digest="1" * 64,
        mutation_graph_digest="2" * 64, committed_result_digest="3" * 64,
        receipt_digest="4" * 64, committed_at="2026-10-22T00:00:00Z",
    )
    assert result.result_digest != result.receipt_digest
    with pytest.raises(ValueError):
        replace(result, receipt_digest="5" * 64)


def test_context_and_receipt_rows_reject_missing_extra_and_tampered_digest(
    real_basis: tuple[object, bytes],
) -> None:
    command, encoded = real_basis
    context = seal_row(_CONTEXT_TABLE, {
        "schema_id": "governed-execution.nwp-section41-post-execution-proposal-context-row.v1",
        "proposal_phase": "post_execution_semantic_review",
        "context_ref": command.context_ref,
        "context_digest": command.context_digest,
        "proposal_ref": command.proposal_ref,
        "proposal_digest": command.proposal_digest,
        "phase_basis_ref": command.phase_basis_ref,
        "phase_basis_digest": command.phase_basis_digest,
        "safe_basis_bytes": encoded,
        "safe_basis_digest": command.safe_basis_digest,
    })
    mapping = context.to_mapping()
    with pytest.raises(ValueError):
        row_from_mapping(_CONTEXT_TABLE, {**mapping, "unknown": "x"})
    with pytest.raises(ValueError):
        row_from_mapping(_CONTEXT_TABLE, {**mapping, "context_row_digest": "0" * 64})
    with pytest.raises(ValueError):
        row_from_mapping(_CONTEXT_TABLE, {**mapping, "safe_basis_bytes": encoded + b" "})
    with pytest.raises(ValueError):
        seal_row(_RECEIPT_TABLE, {"schema_id": "unexpected"})
