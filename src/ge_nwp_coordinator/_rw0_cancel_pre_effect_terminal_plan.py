"""Pure four-row cancel-bound terminal block plan."""
from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from ._rw0_terminal_outcome_contracts import _canonical, _digest
from ._rw0_terminal_anchor_rows import _COMMITTED_RESULT_DOMAIN, expected_cancel_anchor, TerminalAnchorRow
from ._rw0_cancel_pre_effect_terminal_contracts import RecordRW0CancelPreEffectTerminalCommandV1, CancelTerminalCommittedV1
from ._rw0_cancel_pre_effect_terminal_rows import (
    CONTEXT, OUTCOME, RESULT, RECEIPT, COLUMNS, SCHEMAS, PROFILE,
    GRAPH_PROFILE, BRANCH, CancelTerminalRow, checked_row,
)

__all__: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CancelTerminalPlan:
    rows: tuple[CancelTerminalRow, CancelTerminalRow, CancelTerminalRow, CancelTerminalRow]
    anchor: TerminalAnchorRow
    committed: CancelTerminalCommittedV1


def _row(table: str, values: dict[str, object], self_name: str) -> CancelTerminalRow:
    values["schema_id"] = SCHEMAS[table]
    values[self_name] = _digest(SCHEMAS[table] + ".identity", {
        k: v.hex() if type(v) is bytes else v for k, v in values.items() if k != self_name
    })
    return checked_row(table, tuple(values[name] for name in COLUMNS[table]))


def build_cancel_terminal_plan(command: RecordRW0CancelPreEffectTerminalCommandV1,
                               recorded_at: str) -> CancelTerminalPlan:
    m = command.to_mapping()
    context = _row(CONTEXT, {
        "context_ref": m["context_ref"], "profile": PROFILE,
        "mutation_ref": m["mutation_ref"], "phase_basis_ref": m["phase_basis_ref"],
        "phase_basis_digest": m["phase_basis_digest"], "program_ref": m["program_ref"],
        "decision_ref": m["decision_ref"], "decision_digest": m["decision_digest"],
        "decision_receipt_ref": m["decision_receipt_ref"],
        "decision_receipt_digest": m["decision_receipt_digest"],
        "target_effect_intent_ref": m["target_effect_intent_ref"],
        "mismatch_class": m["mismatch_class"], "mismatch_ref": m["mismatch_ref"],
        "mismatch_digest": m["mismatch_digest"],
        "verification_safe_bytes": _canonical(m["verification"]),
        "closure_heads_bytes": _canonical(m["heads"]),
        "closure_stop_bytes": _canonical(m["stop"]),
        "command_safe_bytes": command.safe_bytes, "recorded_at": recorded_at,
    }, "context_digest")
    c = context.mapping
    outcome = _row(OUTCOME, {
        "outcome_value_ref": m["outcome_value_ref"],
        "context_ref": c["context_ref"], "context_digest": c["context_digest"],
        "phase_basis_ref": m["phase_basis_ref"], "phase_basis_digest": m["phase_basis_digest"],
        "branch": BRANCH, "outcome": "block", "decision_ref": m["decision_ref"],
        "decision_digest": m["decision_digest"], "decision_kind": "cancel",
        "mismatch_ref": m["mismatch_ref"], "mismatch_digest": m["mismatch_digest"],
        "closure_heads_bytes": c["closure_heads_bytes"], "closure_stop_bytes": c["closure_stop_bytes"],
    }, "outcome_value_digest")
    o = outcome.mapping
    result = _row(RESULT, {
        "result_ref": m["result_ref"], "outcome_value_ref": o["outcome_value_ref"],
        "outcome_value_digest": o["outcome_value_digest"], "context_ref": c["context_ref"],
        "context_digest": c["context_digest"], "branch": BRANCH, "outcome": "block",
        "recorded_at": recorded_at,
    }, "result_digest")
    x = result.mapping
    members = [
        {"role": "cancel_decision", "ref": m["decision_ref"], "digest": m["decision_digest"]},
        {"role": "cancel_decision_receipt", "ref": m["decision_receipt_ref"], "digest": m["decision_receipt_digest"]},
        {"role": "terminal_context", "ref": c["context_ref"], "digest": c["context_digest"]},
        {"role": "terminal_outcome", "ref": o["outcome_value_ref"], "digest": o["outcome_value_digest"]},
        {"role": "terminal_result", "ref": x["result_ref"], "digest": x["result_digest"]},
    ]
    graph = _digest(GRAPH_PROFILE + ".identity", members)
    committed = _digest(_COMMITTED_RESULT_DOMAIN, {
        "command_digest": command.command_digest, "context_digest": c["context_digest"],
        "outcome_value_digest": o["outcome_value_digest"], "result_digest": x["result_digest"],
        "graph_digest": graph, "recorded_at": recorded_at,
    })
    receipt = _row(RECEIPT, {
        "receipt_ref": m["receipt_ref"], "mutation_ref": m["mutation_ref"],
        "command_digest": command.command_digest, "profile": PROFILE,
        "family_route": m["family_route"], "phase_basis_ref": m["phase_basis_ref"],
        "phase_basis_digest": m["phase_basis_digest"], "decision_ref": m["decision_ref"],
        "context_ref": c["context_ref"], "context_digest": c["context_digest"],
        "outcome_value_ref": o["outcome_value_ref"],
        "outcome_value_digest": o["outcome_value_digest"],
        "result_ref": x["result_ref"], "result_digest": x["result_digest"],
        "graph_profile": GRAPH_PROFILE, "graph_digest": graph,
        "committed_result_digest": committed, "recorded_at": recorded_at,
    }, "receipt_digest")
    anchor = expected_cancel_anchor(context, outcome, result, receipt)
    r = receipt.mapping
    return CancelTerminalPlan((context, outcome, result, receipt), anchor,
        CancelTerminalCommittedV1(cast(str,m["mutation_ref"]), cast(str,m["decision_ref"]),
            cast(str,r["receipt_ref"]), cast(str,r["receipt_digest"]), graph, committed, recorded_at))
