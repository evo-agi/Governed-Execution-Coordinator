"""Pure checked plan for one generic cancel decision and exact private receipt."""
from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from . import _development_decision_row_values as generic
from ._development_row_value_support import _domain_separated_digest
from ._rw0_terminal_outcome_contracts import _canonical, _digest
from ._rw0_cancel_decision_contracts import RecordRW0ActiveCancelDecisionCommandV1, CancelDecisionCommittedV1
from ._rw0_cancel_decision_rows import BINDING, RECEIPT, SCHEMAS, COLUMNS, CancelDecisionRow, checked_row, COMMAND_SCHEMA

__all__: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CancelDecisionPlan:
    decision: generic.DevelopmentDecisionRowValue
    bindings: tuple[CancelDecisionRow, ...]
    receipt: CancelDecisionRow
    committed: CancelDecisionCommittedV1


def _row(table: str, values: dict[str, object], self_name: str) -> CancelDecisionRow:
    values["schema_id"] = SCHEMAS[table]
    values[self_name] = _digest(SCHEMAS[table] + ".identity", {
        k: v.hex() if type(v) is bytes else v for k, v in values.items() if k != self_name
    })
    return checked_row(table, tuple(values[name] for name in COLUMNS[table]))


def build_cancel_decision_plan(command: RecordRW0ActiveCancelDecisionCommandV1,
                               recorded_at: str) -> CancelDecisionPlan:
    if type(command) is not RecordRW0ActiveCancelDecisionCommandV1:
        raise ValueError("invalid cancel command")
    m = command.to_mapping()
    p, t, s = (cast(dict[str, object], m[k]) for k in ("program", "target", "source"))
    stop = cast(dict[str, object], m["stop"])
    decision = {name: None for name in generic._DEVELOPMENT_DECISION_COLUMNS}
    decision.update({
        "schema_id": generic._DEVELOPMENT_DECISION_SCHEMA,
        "mutation_ref": m["mutation_ref"], "decision_ref": m["decision_ref"],
        "program_ref": p["program_ref"], "decision_kind": "cancel",
        "decision_variant": "effect_cancellation", "basis_decision_ref": p["basis_decision_ref"],
        "basis_program_version_ref": p["program_version_ref"],
        "basis_program_version_number": p["program_version_number"],
        "expected_program_head_revision": p["head_revision"],
        "selected_semantic_attempt_ref": p["semantic_attempt_ref"],
        "selected_candidate_ref": p["candidate_ref"],
        "selected_attempt_fence_ref": p["attempt_fence_ref"],
        "selected_attempt_fence_digest": p["attempt_fence_digest"],
        "target_effect_intent_ref": t["effect_intent_ref"],
        "target_effect_class": t["effect_class"],
        "target_effect_fence_ref": t["effect_fence_ref"],
        "target_effect_fence_digest": t["effect_fence_digest"],
        "expected_target_effect_head_revision": t["effect_head"]["head_revision"],
        "originating_command_ref": t["originating_command_ref"],
        "originating_command_digest": t["originating_command_digest"],
        "target_capsule_manifest_ref": t["capsule_manifest_ref"],
        "target_portable_capsule_digest": t["capsule_digest"],
        "coding_global_stop_ref": stop["ref"],
        "coding_global_stop_version": stop["version"],
        "source_directive_ref": s["directive_ref"],
        "source_directive_digest": s["directive_digest"],
        "source_evidence_ref": s["evidence_ref"],
        "source_evidence_digest": s["evidence_digest"],
        "preassigned_effect_intent_ref": m["preassigned_effect_intent_ref"],
        "preassigned_effect_fence_ref": m["preassigned_effect_fence_ref"],
        "preassigned_delivery_attempt_ref": m["preassigned_delivery_attempt_ref"],
        "reason_code": "active_cancel_pre_effect", "decided_at": recorded_at,
    })
    decision["decision_digest"] = _domain_separated_digest(
        generic._DEVELOPMENT_DECISION_DOMAIN,
        {k: decision[k] for k in generic._DEVELOPMENT_DECISION_COLUMNS if k != "decision_digest"},
    )
    typed_decision = generic.development_decision_row_value_from_row_tuple(
        tuple(decision[k] for k in generic._DEVELOPMENT_DECISION_COLUMNS))
    bindings = []
    for evidence in cast(list[dict[str, object]], m["evidence"]):
        role = cast(str, evidence["role"])
        binding = _row(BINDING, {
            "binding_ref": _digest(SCHEMAS[BINDING] + "." + role + ".ref.v1", command.command_digest),
            "mutation_ref": m["mutation_ref"], "program_ref": p["program_ref"],
            "decision_ref": m["decision_ref"], "phase_basis_ref": m["phase_basis_ref"],
            "phase_basis_digest": m["phase_basis_digest"], "role": role,
            "evidence_ref": evidence["ref"], "evidence_digest": evidence["digest"],
        }, "binding_digest")
        bindings.append(binding)
    result_digest = _digest(SCHEMAS[RECEIPT] + ".result.v1", {
        "mutation_ref": m["mutation_ref"], "decision_ref": m["decision_ref"],
        "decision_digest": typed_decision.decision_digest, "recorded_at": recorded_at,
    })
    receipt = _row(RECEIPT, {
        "receipt_ref": m["receipt_ref"], "mutation_ref": m["mutation_ref"],
        "command_schema_id": COMMAND_SCHEMA, "command_digest": command.command_digest,
        "phase_basis_ref": m["phase_basis_ref"], "phase_basis_digest": m["phase_basis_digest"],
        "program_ref": p["program_ref"], "program_version_ref": p["program_version_ref"],
        "program_version_number": p["program_version_number"],
        "semantic_attempt_ref": p["semantic_attempt_ref"], "decision_ref": m["decision_ref"],
        "decision_digest": typed_decision.decision_digest,
        "target_effect_intent_ref": t["effect_intent_ref"],
        "target_effect_fence_ref": t["effect_fence_ref"],
        "target_effect_fence_digest": t["effect_fence_digest"],
        "target_effect_head_revision": t["effect_head"]["head_revision"],
        "target_effect_head_digest": t["effect_head"]["head_digest"],
        "target_effect_head_postimage": _canonical(t["effect_head"]),
        "target_delivery_attempt_ref": t["delivery_attempt_ref"],
        "target_delivery_head_revision": t["delivery_head"]["head_revision"],
        "target_delivery_head_digest": t["delivery_head"]["head_digest"],
        "target_delivery_head_postimage": _canonical(t["delivery_head"]),
        "basis_safe_bytes": _canonical({"program": p, "basis": m["basis"], "stop": stop}),
        "command_safe_bytes": command.safe_bytes,
        "authority_evidence_bytes": _canonical({"source": s}),
        "recorded_at": recorded_at, "result_digest": result_digest,
    }, "receipt_digest")
    r = receipt.mapping
    return CancelDecisionPlan(typed_decision, tuple(bindings), receipt,
        CancelDecisionCommittedV1(cast(str,m["mutation_ref"]), cast(str,m["decision_ref"]),
            typed_decision.decision_digest, cast(str,r["receipt_ref"]),
            cast(str,r["receipt_digest"]), cast(str,r["result_digest"]), recorded_at))
