"""Private branch-neutral route values and persisted normal-family coherence."""
from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from ._rw0_terminal_outcome_contracts import (
    COMMAND_SCHEMA, GRAPH_PROFILE, GRAPH_ROLES, HEAD_ROLES, MANIFEST_ROLES,
    NORMAL_PAIRS, PREFIX, PROFILE, _PREASSIGNED, _SELECTOR_FIELDS,
    _canonical, _digest, _exact, _head, _identity_digest, _safe_ref, _sha,
    _stop, _strict_bytes, _time,
)
from ._rw0_terminal_head_witness import witness_from_bytes
from ._rw0_terminal_outcome_rows import (
    CONTEXT, OUTCOME, RECEIPT, RESULT, TerminalRow,
)

__all__: tuple[str, ...] = ()

TABLE = "rw0_terminal_anchors"
SCHEMA = "governed-execution.nwp-rw0-terminal-anchor.v1"
COLUMNS = (
    "schema_id", "phase_basis_ref", "phase_basis_digest", "family_profile",
    "family_route", "mutation_ref", "command_digest", "program_ref",
    "decision_ref", "context_ref", "context_digest", "outcome_value_ref",
    "outcome_value_digest", "result_ref", "result_digest", "receipt_ref",
    "receipt_digest", "graph_profile", "graph_digest",
    "committed_result_digest", "recorded_at",
)
_REFS = (
    "phase_basis_ref", "family_route", "mutation_ref", "program_ref",
    "decision_ref", "context_ref", "outcome_value_ref", "result_ref",
    "receipt_ref",
)
_DIGESTS = (
    "phase_basis_digest", "command_digest", "context_digest",
    "outcome_value_digest", "result_digest", "receipt_digest",
    "graph_digest", "committed_result_digest",
)
_COMMITTED_RESULT_DOMAIN = PREFIX + "committed-result.v1"


@dataclass(frozen=True, slots=True, repr=False)
class TerminalAnchorRow:
    values: tuple[object, ...]

    @property
    def mapping(self) -> dict[str, object]:
        return dict(zip(COLUMNS, self.values, strict=True))


def checked_anchor_row(raw: object) -> TerminalAnchorRow:
    if type(raw) is not tuple or len(raw) != len(COLUMNS):
        raise ValueError("invalid terminal anchor tuple")
    value = dict(zip(COLUMNS, raw, strict=True))
    if value["schema_id"] != SCHEMA or type(value["schema_id"]) is not str:
        raise ValueError("invalid terminal anchor schema")
    for name in _REFS:
        _safe_ref(value[name])
    for name in _DIGESTS:
        _sha(value[name])
    from ._rw0_cancel_pre_effect_terminal_rows import PROFILE as CANCEL_PROFILE, GRAPH_PROFILE as CANCEL_GRAPH
    if type(value["family_profile"]) is not str or value["family_profile"] not in (PROFILE, CANCEL_PROFILE):
        raise ValueError("unsupported terminal anchor profile")
    expected_graph = GRAPH_PROFILE if value["family_profile"] == PROFILE else CANCEL_GRAPH
    if type(value["graph_profile"]) is not str or value["graph_profile"] != expected_graph:
        raise ValueError("unsupported terminal anchor graph")
    _time(value["recorded_at"])
    return TerminalAnchorRow(raw)


def expected_normal_anchor(
    context: TerminalRow, outcome: TerminalRow,
    result: TerminalRow, receipt: TerminalRow,
) -> TerminalAnchorRow:
    """Check only persisted normal-family evidence, never current heads."""
    if (type(context) is not TerminalRow or context.table != CONTEXT
        or type(outcome) is not TerminalRow or outcome.table != OUTCOME
        or type(result) is not TerminalRow or result.table != RESULT
        or type(receipt) is not TerminalRow or receipt.table != RECEIPT):
        raise ValueError("invalid terminal family")
    c, o, x, r = (row.mapping for row in (context, outcome, result, receipt))
    if (
        c["profile"] != PROFILE or r["profile"] != PROFILE
        or r["graph_profile"] != GRAPH_PROFILE
        or o["branch"] != "normal" or x["branch"] != "normal"
        or o["outcome"] != x["outcome"]
        or o["outcome"] != o["decision_kind"]
        or o["outcome"] not in NORMAL_PAIRS.values()
        or c["context_ref"] != r["context_ref"]
        or c["context_digest"] != r["context_digest"]
        or c["mutation_ref"] != r["mutation_ref"]
        or c["phase_basis_ref"] != r["phase_basis_ref"]
        or c["phase_basis_digest"] != r["phase_basis_digest"]
        or c["p1_decision_ref"] != r["p1_decision_ref"]
        or c["recorded_at"] != r["recorded_at"]
        or o["context_ref"] != c["context_ref"]
        or o["context_digest"] != c["context_digest"]
        or o["phase_basis_ref"] != c["phase_basis_ref"]
        or o["phase_basis_digest"] != c["phase_basis_digest"]
        or o["outcome_value_ref"] != r["outcome_value_ref"]
        or o["outcome_value_digest"] != r["outcome_value_digest"]
        or o["decision_ref"] != c["p1_decision_ref"]
        or o["decision_digest"] != c["p1_decision_digest"]
        or o["decision_kind"] != c["p1_decision_kind"]
        or o["guarded_result_ref"] != c["p1_result_ref"]
        or o["guarded_result_digest"] != c["p1_result_digest"]
        or o["p1_receipt_mutation_ref"] != c["p1_receipt_mutation_ref"]
        or o["p1_receipt_graph_digest"] != c["p1_receipt_graph_digest"]
        or o["evidence_set_ref"] != c["evidence_set_ref"]
        or o["evidence_set_digest"] != c["evidence_set_digest"]
        or o["acceptance_fact_ref"] != c["acceptance_fact_ref"]
        or o["acceptance_fact_digest"] != c["acceptance_fact_digest"]
        or o["closure_stop_bytes"] != c["closure_stop_bytes"]
        or x["result_ref"] != r["result_ref"]
        or x["result_digest"] != r["result_digest"]
        or x["context_ref"] != c["context_ref"]
        or x["context_digest"] != c["context_digest"]
        or x["outcome_value_ref"] != o["outcome_value_ref"]
        or x["outcome_value_digest"] != o["outcome_value_digest"]
        or x["recorded_at"] != r["recorded_at"]
    ):
        raise ValueError("invalid terminal family relation")
    safe = _exact(_strict_bytes(cast(bytes, c["command_safe_bytes"])), _SELECTOR_FIELDS)
    if (safe["schema_id"] != COMMAND_SCHEMA
        or safe["profile"] != PROFILE
        or safe["command_digest"] != r["command_digest"]
        or safe["phase_basis_ref"] != r["phase_basis_ref"]
        or safe["phase_basis_digest"] != r["phase_basis_digest"]
        or safe["mutation_ref"] != r["mutation_ref"]
        or any(safe[name] != r[name] for name in (
            "context_ref", "outcome_value_ref", "result_ref", "receipt_ref", "family_route"
        ))
        or _identity_digest(COMMAND_SCHEMA, safe, "command_digest") != r["command_digest"]):
        raise ValueError("invalid terminal command binding")
    witness = witness_from_bytes(c["closure_heads_bytes"])
    if (safe["heads"] != list(witness.coordinates)
        or _canonical({"heads": list(witness.coordinates)}) != o["closure_heads_bytes"]
        or safe["stop"] != _strict_bytes(cast(bytes, c["closure_stop_bytes"]), limit=1024)["stop"]):
        raise ValueError("invalid terminal head binding")
    manifest = _strict_bytes(cast(bytes, c["reached_owner_manifest_bytes"]), limit=8192)
    members = manifest["roles"]
    if (type(members) is not list or len(members) != len(MANIFEST_ROLES)
        or members != safe["reached_owners"]):
        raise ValueError("invalid terminal graph manifest")
    for item, role in zip(members, MANIFEST_ROLES, strict=True):
        checked = _exact(item, ("role", "ref", "digest"))
        if checked["role"] != role:
            raise ValueError("invalid terminal graph role")
        _safe_ref(checked["ref"])
        _sha(checked["digest"])
    owner_coordinates = (
        (0, c["p0_fact_ref"], c["p0_fact_digest"]),
        (1, c["phase_basis_ref"], c["phase_basis_digest"]),
        (4, c["section41_proposal_ref"], c["section41_proposal_digest"]),
        (14, c["c1_membership_ref"], c["c1_membership_digest"]),
        (15, c["p1_decision_ref"], c["p1_decision_digest"]),
        (16, c["p1_result_ref"], c["p1_result_digest"]),
        (17, c["p1_receipt_mutation_ref"], c["p1_receipt_graph_digest"]),
    )
    if any(members[index]["ref"] != ref or members[index]["digest"] != digest
           for index, ref, digest in owner_coordinates):
        raise ValueError("invalid terminal owner coordinates")
    if type(safe["heads"]) is not list or len(safe["heads"]) != len(HEAD_ROLES):
        raise ValueError("invalid terminal saved heads")
    for head, role in zip(safe["heads"], HEAD_ROLES, strict=True):
        _head(head, role)
    _stop(safe["stop"])
    stable = {key: safe[key] for key in (
        "schema_id", "profile", "mutation_ref", "phase_basis_ref",
        "phase_basis_digest", "p1", "section41", "c1_rank15",
        "reached_owners", "heads", "stop",
    )}
    transcript = [[key, stable[key]] for key in stable]
    for name, domain in _PREASSIGNED:
        if safe[name] != _digest(domain, transcript):
            raise ValueError("invalid terminal preassignment")
    if (safe["expected_branch"] is not None
        and NORMAL_PAIRS.get(safe["expected_branch"]) != o["outcome"]
        or safe["expected_outcome"] is not None
        and safe["expected_outcome"] != o["outcome"]):
        raise ValueError("invalid terminal asserted outcome")
    members = list(members)
    members.extend((
        {"role": "terminal_context", "ref": c["context_ref"], "digest": c["context_digest"]},
        {"role": "terminal_outcome", "ref": o["outcome_value_ref"], "digest": o["outcome_value_digest"]},
        {"role": "terminal_result", "ref": x["result_ref"], "digest": x["result_digest"]},
    ))
    if c["acceptance_fact_ref"] is not None:
        members.append({
            "role": "acceptance_fact", "ref": c["acceptance_fact_ref"],
            "digest": c["acceptance_fact_digest"],
        })
    if tuple(item["role"] for item in members) != GRAPH_ROLES + (
        ("acceptance_fact",) if c["acceptance_fact_ref"] is not None else ()
    ):
        raise ValueError("invalid terminal graph roles")
    graph = _digest(GRAPH_PROFILE + ".identity", members)
    committed = _digest(_COMMITTED_RESULT_DOMAIN, {
        "command_digest": r["command_digest"],
        "context_digest": c["context_digest"],
        "outcome_value_digest": o["outcome_value_digest"],
        "result_digest": x["result_digest"],
        "graph_digest": graph,
        "recorded_at": r["recorded_at"],
    })
    if graph != r["graph_digest"] or committed != r["committed_result_digest"]:
        raise ValueError("invalid terminal graph digest")
    return checked_anchor_row((
        SCHEMA, r["phase_basis_ref"], r["phase_basis_digest"], r["profile"],
        r["family_route"], r["mutation_ref"], r["command_digest"],
        c["program_ref"], r["p1_decision_ref"], r["context_ref"],
        r["context_digest"], r["outcome_value_ref"], r["outcome_value_digest"],
        r["result_ref"], r["result_digest"], r["receipt_ref"],
        r["receipt_digest"], r["graph_profile"], r["graph_digest"],
        r["committed_result_digest"], r["recorded_at"],
    ))


def expected_cancel_anchor(context: object, outcome: object,
                           result: object, receipt: object) -> TerminalAnchorRow:
    """Check one immutable cancel-bound family without reading mutable heads."""
    from ._rw0_cancel_pre_effect_terminal_rows import (
        CONTEXT as C, OUTCOME as O, RESULT as X, RECEIPT as R,
        CancelTerminalRow, PROFILE as CP, GRAPH_PROFILE as CG, BRANCH,
    )
    if any(type(row) is not CancelTerminalRow or row.table != table
           for row, table in zip((context, outcome, result, receipt), (C, O, X, R), strict=True)):
        raise ValueError("invalid cancel terminal family")
    c, o, x, r = (row.mapping for row in (context, outcome, result, receipt))
    if (
        c["profile"] != CP or r["profile"] != CP or r["graph_profile"] != CG
        or o["branch"] != BRANCH or x["branch"] != BRANCH
        or o["outcome"] != "block" or x["outcome"] != "block"
        or o["decision_kind"] != "cancel"
        or c["mutation_ref"] != r["mutation_ref"]
        or c["phase_basis_ref"] != r["phase_basis_ref"]
        or c["phase_basis_digest"] != r["phase_basis_digest"]
        or c["decision_ref"] != r["decision_ref"]
        or o["context_ref"] != c["context_ref"]
        or o["context_digest"] != c["context_digest"]
        or o["phase_basis_ref"] != c["phase_basis_ref"]
        or o["phase_basis_digest"] != c["phase_basis_digest"]
        or o["decision_ref"] != c["decision_ref"]
        or o["decision_digest"] != c["decision_digest"]
        or o["mismatch_ref"] != c["mismatch_ref"]
        or o["mismatch_digest"] != c["mismatch_digest"]
        or o["closure_heads_bytes"] != c["closure_heads_bytes"]
        or o["closure_stop_bytes"] != c["closure_stop_bytes"]
        or x["outcome_value_ref"] != o["outcome_value_ref"]
        or x["outcome_value_digest"] != o["outcome_value_digest"]
        or x["context_ref"] != c["context_ref"]
        or x["context_digest"] != c["context_digest"]
        or x["recorded_at"] != r["recorded_at"]
        or c["recorded_at"] != r["recorded_at"]
        or r["context_ref"] != c["context_ref"]
        or r["context_digest"] != c["context_digest"]
        or r["outcome_value_ref"] != o["outcome_value_ref"]
        or r["outcome_value_digest"] != o["outcome_value_digest"]
        or r["result_ref"] != x["result_ref"]
        or r["result_digest"] != x["result_digest"]
    ):
        raise ValueError("invalid cancel terminal relation")
    members = [
        {"role": "cancel_decision", "ref": c["decision_ref"], "digest": c["decision_digest"]},
        {"role": "cancel_decision_receipt", "ref": c["decision_receipt_ref"], "digest": c["decision_receipt_digest"]},
        {"role": "terminal_context", "ref": c["context_ref"], "digest": c["context_digest"]},
        {"role": "terminal_outcome", "ref": o["outcome_value_ref"], "digest": o["outcome_value_digest"]},
        {"role": "terminal_result", "ref": x["result_ref"], "digest": x["result_digest"]},
    ]
    graph = _digest(CG + ".identity", members)
    committed = _digest(_COMMITTED_RESULT_DOMAIN, {
        "command_digest": r["command_digest"],
        "context_digest": c["context_digest"],
        "outcome_value_digest": o["outcome_value_digest"],
        "result_digest": x["result_digest"],
        "graph_digest": graph,
        "recorded_at": r["recorded_at"],
    })
    if graph != r["graph_digest"] or committed != r["committed_result_digest"]:
        raise ValueError("invalid cancel terminal graph")
    return checked_anchor_row((
        SCHEMA, r["phase_basis_ref"], r["phase_basis_digest"], r["profile"],
        r["family_route"], r["mutation_ref"], r["command_digest"],
        c["program_ref"], r["decision_ref"], r["context_ref"],
        r["context_digest"], r["outcome_value_ref"], r["outcome_value_digest"],
        r["result_ref"], r["result_digest"], r["receipt_ref"],
        r["receipt_digest"], r["graph_profile"], r["graph_digest"],
        r["committed_result_digest"], r["recorded_at"],
    ))
