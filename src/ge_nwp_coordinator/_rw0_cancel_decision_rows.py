"""Private exact persisted cancellation decision receipt and binding rows."""
from __future__ import annotations

from dataclasses import dataclass
from ._rw0_terminal_outcome_contracts import _digest, _safe_ref, _sha, _time, _strict_bytes

__all__: tuple[str, ...] = ()

BINDING = "rw0_cancel_decision_evidence_bindings"
RECEIPT = "rw0_cancel_decision_receipts"
TABLES = (BINDING, RECEIPT)
SCHEMAS = {
    BINDING: "governed-execution.nwp-rw0-cancel-decision-evidence-binding.v1",
    RECEIPT: "governed-execution.nwp-rw0-cancel-decision-receipt.v1",
}
COLUMNS = {
    BINDING: tuple("schema_id binding_ref mutation_ref program_ref decision_ref phase_basis_ref phase_basis_digest role evidence_ref evidence_digest binding_digest".split()),
    RECEIPT: tuple("schema_id receipt_ref mutation_ref command_schema_id command_digest phase_basis_ref phase_basis_digest program_ref program_version_ref program_version_number semantic_attempt_ref decision_ref decision_digest target_effect_intent_ref target_effect_fence_ref target_effect_fence_digest target_effect_head_revision target_effect_head_digest target_effect_head_postimage target_delivery_attempt_ref target_delivery_head_revision target_delivery_head_digest target_delivery_head_postimage basis_safe_bytes command_safe_bytes authority_evidence_bytes recorded_at result_digest receipt_digest".split()),
}
PRIMARY = {BINDING: "binding_ref", RECEIPT: "receipt_ref"}
ROLES = ("cancel_target_effect", "cancel_target_effect_fence", "cancel_source_directive", "cancel_source_evidence")
CAPSULE_ROLE = "cancel_target_capsule"
COMMAND_SCHEMA = "governed-execution.nwp-record-rw0-cancel-decision-command.v1"


@dataclass(frozen=True, slots=True, repr=False)
class CancelDecisionRow:
    table: str
    values: tuple[object, ...]

    @property
    def mapping(self) -> dict[str, object]:
        return dict(zip(COLUMNS[self.table], self.values, strict=True))


def _identity(value: dict[str, object], self_name: str) -> dict[str, object]:
    return {k: v.hex() if type(v) is bytes else v for k, v in value.items() if k != self_name}


def checked_row(table: str, raw: object) -> CancelDecisionRow:
    if table not in TABLES or type(raw) is not tuple or len(raw) != len(COLUMNS[table]):
        raise ValueError("invalid cancel decision row shape")
    value = dict(zip(COLUMNS[table], raw, strict=True))
    if type(value["schema_id"]) is not str or value["schema_id"] != SCHEMAS[table]:
        raise ValueError("invalid cancel decision row schema")
    for name, item in value.items():
        if name == "schema_id":
            continue
        if name.endswith("_ref"):
            _safe_ref(item)
        elif name.endswith("_digest"):
            _sha(item)
        elif name.endswith("_bytes") or name.endswith("_postimage"):
            if type(item) is not bytes:
                raise ValueError("invalid cancel decision safe bytes")
            _strict_bytes(item)
        elif name == "recorded_at":
            _time(item)
        elif name.endswith("_revision") or name.endswith("_number"):
            if type(item) is not int or item < 0:
                raise ValueError("invalid cancel decision number")
    if table == BINDING:
        if value["role"] not in ROLES + (CAPSULE_ROLE,):
            raise ValueError("invalid cancel role")
        self_name = "binding_digest"
    else:
        if value["command_schema_id"] != COMMAND_SCHEMA:
            raise ValueError("invalid cancel command schema")
        expected_result = _digest(SCHEMAS[RECEIPT] + ".result.v1", {
            "mutation_ref": value["mutation_ref"], "decision_ref": value["decision_ref"],
            "decision_digest": value["decision_digest"], "recorded_at": value["recorded_at"],
        })
        if value["result_digest"] != expected_result:
            raise ValueError("invalid cancel result digest")
        self_name = "receipt_digest"
    expected = _digest(SCHEMAS[table] + ".identity", _identity(value, self_name))
    if value[self_name] != expected:
        raise ValueError("invalid cancel decision row digest")
    return CancelDecisionRow(table, raw)


def required_roles(target_class: str) -> tuple[str, ...]:
    if target_class == "author_candidate":
        return ROLES
    if target_class in ("validate_candidate", "review_candidate"):
        return ROLES + (CAPSULE_ROLE,)
    raise ValueError("unsupported cancel target")
