"""Private persisted cancel-bound pre-effect terminal row values."""
from __future__ import annotations

from dataclasses import dataclass
from ._rw0_terminal_outcome_contracts import _digest, _safe_ref, _sha, _time, _strict_bytes

__all__: tuple[str, ...] = ()

CONTEXT = "rw0_cancel_pre_effect_contexts"
OUTCOME = "rw0_cancel_pre_effect_outcomes"
RESULT = "rw0_cancel_pre_effect_results"
RECEIPT = "rw0_cancel_pre_effect_receipts"
TABLES = (CONTEXT, OUTCOME, RESULT, RECEIPT)
SCHEMAS = {
    CONTEXT: "governed-execution.nwp-rw0-cancel-pre-effect-context.v1",
    OUTCOME: "governed-execution.nwp-rw0-cancel-pre-effect-outcome.v1",
    RESULT: "governed-execution.nwp-rw0-cancel-pre-effect-result.v1",
    RECEIPT: "governed-execution.nwp-rw0-cancel-pre-effect-receipt.v1",
}
COLUMNS = {
    CONTEXT: tuple("schema_id context_ref context_digest profile mutation_ref phase_basis_ref phase_basis_digest program_ref decision_ref decision_digest decision_receipt_ref decision_receipt_digest target_effect_intent_ref mismatch_class mismatch_ref mismatch_digest verification_safe_bytes closure_heads_bytes closure_stop_bytes command_safe_bytes recorded_at".split()),
    OUTCOME: tuple("schema_id outcome_value_ref outcome_value_digest context_ref context_digest phase_basis_ref phase_basis_digest branch outcome decision_ref decision_digest decision_kind mismatch_ref mismatch_digest closure_heads_bytes closure_stop_bytes".split()),
    RESULT: tuple("schema_id result_ref result_digest outcome_value_ref outcome_value_digest context_ref context_digest branch outcome recorded_at".split()),
    RECEIPT: tuple("schema_id receipt_ref receipt_digest mutation_ref command_digest profile family_route phase_basis_ref phase_basis_digest decision_ref context_ref context_digest outcome_value_ref outcome_value_digest result_ref result_digest graph_profile graph_digest committed_result_digest recorded_at".split()),
}
PRIMARY = {CONTEXT: "context_ref", OUTCOME: "outcome_value_ref", RESULT: "result_ref", RECEIPT: "receipt_ref"}
SELF_DIGEST = {CONTEXT: "context_digest", OUTCOME: "outcome_value_digest", RESULT: "result_digest", RECEIPT: "receipt_digest"}
PROFILE = "artificial_offline_cancel_pre_effect_block.v1"
GRAPH_PROFILE = "governed-execution.nwp-rw0-terminal-cancel-pre-effect-block-graph.v1"
BRANCH = "pre_effect_cancel_basis_unusable"
MISMATCH_CLASSES = frozenset(("program_head", "program_version", "semantic_attempt", "effect_head", "delivery_head", "global_stop", "attempt_fence", "effect_fence", "preassignment", "persisted_basis"))


@dataclass(frozen=True, slots=True, repr=False)
class CancelTerminalRow:
    table: str
    values: tuple[object, ...]

    @property
    def mapping(self) -> dict[str, object]:
        return dict(zip(COLUMNS[self.table], self.values, strict=True))


def checked_row(table: str, raw: object) -> CancelTerminalRow:
    if table not in TABLES or type(raw) is not tuple or len(raw) != len(COLUMNS[table]):
        raise ValueError("invalid cancel terminal row shape")
    value = dict(zip(COLUMNS[table], raw, strict=True))
    if value["schema_id"] != SCHEMAS[table] or type(value["schema_id"]) is not str:
        raise ValueError("invalid cancel terminal schema")
    for name, item in value.items():
        if name == "schema_id":
            continue
        if name.endswith("_ref") or name == "family_route":
            _safe_ref(item)
        elif name.endswith("_digest"):
            _sha(item)
        elif name.endswith("_bytes"):
            if type(item) is not bytes:
                raise ValueError("invalid cancel terminal safe bytes")
            _strict_bytes(item)
        elif name == "recorded_at":
            _time(item)
    if "profile" in value and value["profile"] != PROFILE:
        raise ValueError("invalid cancel terminal profile")
    if "graph_profile" in value and value["graph_profile"] != GRAPH_PROFILE:
        raise ValueError("invalid cancel terminal graph profile")
    if "branch" in value and value["branch"] != BRANCH:
        raise ValueError("invalid cancel terminal branch")
    if "outcome" in value and value["outcome"] != "block":
        raise ValueError("invalid cancel terminal outcome")
    if "decision_kind" in value and value["decision_kind"] != "cancel":
        raise ValueError("invalid cancel terminal decision kind")
    if "mismatch_class" in value and value["mismatch_class"] not in MISMATCH_CLASSES:
        raise ValueError("invalid cancel terminal mismatch class")
    self_name = SELF_DIGEST[table]
    expected = _digest(SCHEMAS[table] + ".identity", {k: v.hex() if type(v) is bytes else v for k, v in value.items() if k != self_name})
    if value[self_name] != expected:
        raise ValueError("invalid cancel terminal row digest")
    return CancelTerminalRow(table, raw)
