"""Closed normal V2 values and fixed independent canonical vector."""
from __future__ import annotations

import pytest

from ge_nwp_coordinator._rw0_terminal_outcome_contracts import (
    GRAPH_ROLES, HEAD_ROLES, MANIFEST_ROLES, NORMAL_PAIRS,
    OUTCOME_SCHEMA, RW0TerminalOutcomeV2, TerminalCommittedV1,
    TerminalConflictV1, TerminalRecoveryV1, _head, _safe_ref, _strict_bytes,
)

_A = "a" * 64
_VECTOR = "cb0e41539d399b50e8ad27f76f7b0ed0c1599a82020b2075c71583f8369935e0"


def _normal_mapping():
    return {
        "schema_id": OUTCOME_SCHEMA, "outcome_value_ref": "outcome.1",
        "context_ref": "context.1", "context_digest": _A,
        "phase_basis_ref": "phase.1", "phase_basis_digest": _A,
        "branch": "normal", "outcome": "repair",
        "decision_ref": "decision.1", "decision_digest": _A,
        "decision_kind": "repair", "guarded_result_ref": "guarded.1",
        "guarded_result_digest": _A, "p1_receipt_mutation_ref": "p1mutation.1",
        "p1_receipt_graph_digest": _A,
        "closure_heads": [
            {"role": role, "owner_ref": role + ".1", "revision": 0, "digest": _A}
            for role in HEAD_ROLES],
        "closure_stop": {"ref": "global-stop.clear", "version": 0,
                         "state": "clear", "updated_at": "2020-01-01T00:00:00Z"},
        "evidence_set_ref": "evidence.1", "evidence_set_digest": _A,
        "acceptance_fact_ref": None, "acceptance_fact_digest": None,
        "reconciliation_ref": None, "reconciliation_digest": None,
        "mismatch_ref": None, "mismatch_digest": None,
        "outcome_value_digest": _VECTOR,
    }


def test_fixed_normal_v2_vector_and_closed_roles():
    value = RW0TerminalOutcomeV2.from_mapping(_normal_mapping())
    assert value.to_mapping()["outcome_value_digest"] == _VECTOR
    assert tuple(NORMAL_PAIRS.items()) == (
        ("candidate_acceptance", "accept"), ("candidate_repair", "repair"),
        ("attempt_selecting_replan", "replan"),
        ("program_terminal_reject", "terminal_reject"),
        ("post_execution_program_block", "block"))
    assert len(MANIFEST_ROLES) == 18
    assert GRAPH_ROLES[-3:] == ("terminal_context", "terminal_outcome", "terminal_result")


@pytest.mark.parametrize("change", (
    {"branch": "active_cancel_reconciled"},
    {"outcome": "cancel"},
    {"decision_kind": "accept"},
    {"acceptance_fact_ref": "foreign.1", "acceptance_fact_digest": _A},
    {"reconciliation_ref": "cancel.1"},
    {"mismatch_digest": _A},
    {"outcome": True},
    {"outcome": None},
    {"unsupported": "extension"},
))
def test_normal_v2_rejects_cancel_foreign_acceptance_and_extra_fields(change):
    mapping = {**_normal_mapping(), **change}
    with pytest.raises(ValueError):
        RW0TerminalOutcomeV2.from_mapping(mapping)


def test_normal_v2_rejects_bool_revision_and_noncanonical_bytes():
    mapping = _normal_mapping()
    mapping["closure_heads"][0]["revision"] = True
    with pytest.raises(ValueError):
        RW0TerminalOutcomeV2.from_mapping(mapping)
    with pytest.raises(ValueError):
        _strict_bytes(b'{"a":1,"a":2}')
    with pytest.raises(ValueError):
        _strict_bytes(b'{"a":"\xff"}')
    with pytest.raises(ValueError):
        _strict_bytes(b'{}' + b' ' * 49152)
    with pytest.raises(ValueError):
        _strict_bytes(b'{"nested":' * 18 + b'null' + b'}' * 18)
    mapping = _normal_mapping()
    mapping["closure_stop"]["updated_at"] = "2020-02-30T00:00:00Z"
    with pytest.raises(ValueError):
        RW0TerminalOutcomeV2.from_mapping(mapping)


def test_normal_v2_ref_and_accept_pair_are_closed():
    class StringSubclass(str):
        pass
    class DictSubclass(dict):
        pass
    with pytest.raises(ValueError):
        RW0TerminalOutcomeV2.from_mapping(DictSubclass(_normal_mapping()))
    for bad in (StringSubclass("valid.ref"), "connector-private", "user-secret", "-leading", "bad/route"):
        with pytest.raises(ValueError):
            _safe_ref(bad)
    mapping = _normal_mapping()
    mapping["decision_kind"] = StringSubclass("repair")
    with pytest.raises(ValueError):
        RW0TerminalOutcomeV2.from_mapping(mapping)
    mapping = _normal_mapping()
    mapping["outcome"] = mapping["decision_kind"] = "accept"
    with pytest.raises(ValueError):
        RW0TerminalOutcomeV2.from_mapping(mapping)


def test_terminal_a03_exact_builtin_roles_and_enums_precede_equality():
    class StringSubclass(str):
        pass

    class EqualitySpy:
        calls = []

        def __eq__(self, other):
            self.calls.append(other)
            return True

    calibration = EqualitySpy()
    assert calibration == "calibration"
    assert EqualitySpy.calls == ["calibration"]
    EqualitySpy.calls.clear()

    head = _normal_mapping()["closure_heads"][0]
    assert _head(head, "program") == head
    for role in (StringSubclass("program"), EqualitySpy()):
        with pytest.raises(ValueError):
            _head(head, role)
        assert EqualitySpy.calls == []
        with pytest.raises(ValueError):
            _head({**head, "role": role}, "program")
        assert EqualitySpy.calls == []
    assert TerminalConflictV1("stale_currentness").reason == "stale_currentness"
    assert TerminalRecoveryV1("unresolved").classification == "unresolved"
    for value in (StringSubclass("stale_currentness"), EqualitySpy()):
        with pytest.raises(ValueError):
            TerminalConflictV1(value)
        assert EqualitySpy.calls == []
    for value in (StringSubclass("unresolved"), EqualitySpy()):
        with pytest.raises(ValueError):
            TerminalRecoveryV1(value)
        assert EqualitySpy.calls == []
    committed = TerminalCommittedV1("mutation.1", _A, "receipt.1", "outcome.1",
                                    "accept", _A, "2020-01-01T00:00:00Z")
    assert TerminalRecoveryV1("committed_exact", committed).committed is committed
    for classification, slot in (("committed_exact", None),
                                 ("unresolved", committed),
                                 ("definitely_not_committed", object())):
        with pytest.raises(ValueError):
            TerminalRecoveryV1(classification, slot)
