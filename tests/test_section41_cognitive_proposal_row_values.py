from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import ge_nwp_coordinator._cognitive_proposal_row_values as rows
from ge_nwp_coordinator._cognitive_proposal_value_support import (
    _CognitiveProposalContractViolation,
)
from test_remote_worker_pre_execution_planning_contract import (
    _build_repaired_common_phase_rows,
    _build_repaired_physical_family,
    _repaired_row_digest,
)


@pytest.mark.parametrize("readiness_present", (False, True))
def test_all_oracle_rows_reconstruct_with_exact_order_and_self_digests(
    readiness_present: bool,
) -> None:
    oracle = _build_repaired_physical_family(readiness_present)
    physical = oracle["physical_rows"]
    reconstructed = []
    for member in physical:
        value = rows._row_value_from_mapping(member["table"], member["values"])
        canonical = rows.CanonicalCognitivePhysicalRow(
            table=member["table"],
            role=member["role"],
            rank=member["rank"],
            ordinal=member["ordinal"],
            values=value,
        )
        assert value.to_mapping() == member["values"]
        assert value.computed_digest() == canonical.member_digest
        assert canonical.values is not value
        assert canonical.values.to_mapping() == value.to_mapping()
        reconstructed.append(canonical)
    assert len(reconstructed) == (23 if readiness_present else 22)
    assert reconstructed[-1].rank is None
    assert reconstructed[-1].role == "receipt"


def test_row_mapping_and_tuple_carriers_must_be_exact_builtins() -> None:
    oracle = _build_repaired_physical_family(False)["physical_rows"][0]

    class MappingSubclass(dict):
        pass

    class TupleSubclass(tuple):
        pass

    with pytest.raises(_CognitiveProposalContractViolation):
        rows._row_value_from_mapping(oracle["table"], MappingSubclass(oracle["values"]))
    with pytest.raises(_CognitiveProposalContractViolation):
        rows._row_value_from_tuple(
            oracle["table"], TupleSubclass(oracle["values"].values())
        )

    class HostileKey(str):
        __hash__ = str.__hash__

        def __eq__(self, other: object) -> bool:
            raise AssertionError("hostile equality executed")

    hostile = dict(oracle["values"])
    first_value = hostile.pop("schema_id")
    hostile = {HostileKey("schema_id"): first_value, **hostile}
    with pytest.raises(_CognitiveProposalContractViolation):
        rows._row_value_from_mapping(oracle["table"], hostile)


@pytest.mark.parametrize("evidence_count", (0, 9))
def test_common_post_execution_rows_retain_exact_representability(
    evidence_count: int,
) -> None:
    physical = _build_repaired_common_phase_rows(
        "post_execution_semantic_review",
        "post_execution_semantic_review",
        "post_execution_semantic_review",
        post_evidence_count=evidence_count,
    )
    for member in physical:
        value = rows._row_value_from_mapping(member["table"], member["values"])
        assert (
            value.computed_digest()
            == member["values"][rows._DIGEST_FIELDS[member["table"]]]
        )


def test_redigested_row_that_violates_sql_enum_grammar_fails_closed() -> None:
    member = _build_repaired_physical_family(False)["physical_rows"][0]
    changed = dict(member["values"])
    changed["invocation_status"] = "unknown"
    changed["source_invocation_digest"] = _repaired_row_digest(member["table"], changed)
    with pytest.raises(_CognitiveProposalContractViolation):
        rows._row_value_from_mapping(member["table"], changed)


def test_wrong_row_digest_and_mutation_fail_closed() -> None:
    oracle = _build_repaired_physical_family(False)["physical_rows"][0]
    changed = dict(oracle["values"])
    changed["source_invocation_digest"] = "f" * 64
    with pytest.raises(_CognitiveProposalContractViolation) as caught:
        rows._row_value_from_mapping(oracle["table"], changed)
    assert caught.value.reason == "physical_family_row_digest_mismatch"

    value = rows._row_value_from_mapping(oracle["table"], oracle["values"])
    with pytest.raises(FrozenInstanceError):
        value.source_invocation_ref = "changed"  # type: ignore[misc]
    assert repr(value) == "<DevelopmentModelSourceInvocationRowValue>"


def test_concrete_row_module_and_name_spoof_is_rejected() -> None:
    value_type = rows.DevelopmentModelProposalRowValue
    with pytest.raises(TypeError):
        type(
            value_type.__name__,
            (value_type,),
            {"__module__": rows.__name__},
        )


@pytest.mark.parametrize("role", ("source_invocation", "model_proposal"))
def test_row_registry_and_physical_carrier_reject_equal_hash_spoofs_without_callbacks(
    role: str,
) -> None:
    member = next(
        item
        for item in _build_repaired_physical_family(False)["physical_rows"]
        if item["role"] == role
    )
    trusted_type = type(
        rows._row_value_from_mapping(member["table"], member["values"])
    )
    callbacks = {"hash": 0, "equality": 0, "conversion": 0}

    class CollisionMeta(type):
        def __hash__(cls) -> int:
            callbacks["hash"] += 1
            return type.__hash__(trusted_type)

        def __eq__(cls, other: object) -> bool:
            callbacks["equality"] += 1
            return other is trusted_type

    def to_mapping(self: object) -> dict[str, object]:
        callbacks["conversion"] += 1
        raise AssertionError("hostile conversion executed")

    spoof_type = CollisionMeta(
        trusted_type.__name__,
        (),
        {"__module__": trusted_type.__module__, "to_mapping": to_mapping},
    )
    spoof = spoof_type()
    spoof.__dict__.update(member["values"])
    callbacks.update(hash=0, equality=0, conversion=0)
    assert spoof_type.__name__ == trusted_type.__name__
    assert spoof_type.__module__ == trusted_type.__module__

    with pytest.raises(_CognitiveProposalContractViolation):
        rows._require_exact_row_value(spoof)
    with pytest.raises(_CognitiveProposalContractViolation):
        rows.CanonicalCognitivePhysicalRow(
            table=member["table"],
            role=member["role"],
            rank=member["rank"],
            ordinal=member["ordinal"],
            values=spoof,  # type: ignore[arg-type]
        )
    assert callbacks == {"hash": 0, "equality": 0, "conversion": 0}


def test_exact_row_reconstruction_rejects_post_mutation_and_disposition_collapse_reason_is_dedicated() -> None:
    physical = _build_repaired_physical_family(False)["physical_rows"]
    source_member = next(item for item in physical if item["role"] == "source_invocation")
    source = rows._row_value_from_mapping(
        source_member["table"], source_member["values"]
    )
    object.__setattr__(source, "source_invocation_ref", "source-mutated")
    with pytest.raises(_CognitiveProposalContractViolation):
        rows._require_exact_row_value(source)

    disposition_member = next(
        item for item in physical if item["role"] == "coordinator_disposition"
    )
    collapsed = dict(disposition_member["values"])
    collapsed["disposition_ref"] = collapsed["proposal_ref"]
    collapsed["disposition_digest"] = _repaired_row_digest(
        disposition_member["table"], collapsed
    )
    with pytest.raises(_CognitiveProposalContractViolation) as caught:
        rows._row_value_from_mapping(disposition_member["table"], collapsed)
    assert caught.value.reason == "proposal_disposition_identity_collapse"
