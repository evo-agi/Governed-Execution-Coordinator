"""Pure closed four-row terminal plan after fenced owner verification."""
from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from . import _development_decision_row_values as _decision
from ._rw0_c2_progression_contracts import ProgressionDecisionCommittedV1
from ._rw0_c2_progression_rows import _P1Row
from ._rw0_terminal_outcome_contracts import (
    CONTEXT_SCHEMA, OUTCOME_SCHEMA, RESULT_SCHEMA, RECEIPT_SCHEMA,
    GRAPH_PROFILE, GRAPH_ROLES, NORMAL_PAIRS, PREFIX, PROFILE,
    RecordRW0TerminalOutcomeCommandV1, TerminalCommittedV1,
    _canonical, _digest, _identity_digest, _strict_bytes, _time,
)
from ._rw0_terminal_head_witness import TerminalHeadWitness
from ._rw0_terminal_outcome_rows import (
    CONTEXT, OUTCOME, RESULT, RECEIPT, TerminalRow, seal_row,
)
from ._sqlite_rw0_c1 import RW0C1CheckedEvidenceFamilyV1
from ._sqlite_section41_post_execution_proposal import CheckedPostExecutionProposalFamilyV1

__all__: tuple[str, ...] = ()

_P1_RECEIPT_ANCHOR_DOMAIN = PREFIX + "p1-generic-receipt-anchor.v1"
_COMMITTED_RESULT_DOMAIN = PREFIX + "committed-result.v1"


@dataclass(frozen=True, slots=True, repr=False)
class TerminalFacts:
    prior: ProgressionDecisionCommittedV1
    decision: _decision.DevelopmentDecisionRowValue
    relation: _P1Row
    guarded_result: _P1Row
    receipt: _decision.DevelopmentMutationReceiptRowValue
    acceptance: _P1Row | None
    section41: CheckedPostExecutionProposalFamilyV1
    c1_rank15: RW0C1CheckedEvidenceFamilyV1


@dataclass(frozen=True, slots=True, repr=False)
class TerminalPlan:
    rows: tuple[TerminalRow, TerminalRow, TerminalRow, TerminalRow]
    committed: TerminalCommittedV1


def _generic_receipt_anchor(row: _decision.DevelopmentMutationReceiptRowValue) -> str:
    return _digest(_P1_RECEIPT_ANCHOR_DOMAIN, {
        name: getattr(row, name)
        for name in _decision._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS
    })


def snapshot_compatible(
    command: RecordRW0TerminalOutcomeCommandV1,
    facts: TerminalFacts,
    witness: TerminalHeadWitness,
) -> bool:
    """One predecessor relation for fresh capture and saved history alike."""
    if (type(command) is not RecordRW0TerminalOutcomeCommandV1
        or type(facts) is not TerminalFacts
        or type(witness) is not TerminalHeadWitness):
        raise ValueError("invalid terminal compatibility input")
    program, work, selection, effect, delivery = witness.postimages
    phase = facts.c1_rank15.phase
    relation = facts.relation.mapping
    basis = command.p1_command.basis.to_mapping()
    selected = cast(dict[str, object], basis["decision_current_snapshot"])
    phase_value = phase.value
    program_post = _strict_bytes(cast(bytes, relation["historical_head_postimage"]), limit=4096)
    if program != program_post:
        return False
    if facts.prior.branch == "attempt_selecting_replan":
        work_post = _strict_bytes(cast(bytes, relation["historical_work_head_postimage"]), limit=4096)
        if work != work_post:
            return False
    elif (work["work_item_ref"] != selected["work_item_ref"]
          or work["current_work_item_revision_ref"] != phase_value("work_item_revision_ref")
          or work["head_revision"] != phase_value("expected_work_item_head_revision")
          or work["head_digest"] != phase_value("expected_work_item_head_digest")):
        return False
    program_ref = command.p1_command.relation.to_mapping()["program_ref"]
    effect_ref = phase_value("effect_intent_ref")
    if (program["program_ref"] != program_ref
        or work["program_ref"] != program_ref
        or selection["program_ref"] != program_ref
        or effect["program_ref"] != program_ref
        or delivery["program_ref"] != program_ref
        or selection["work_item_ref"] != phase_value("work_item_ref")
        or selection["work_item_revision_ref"] != phase_value("work_item_revision_ref")
        or selection["program_version_ref"] != phase_value("program_version_ref")
        or selection["effect_intent_ref"] != effect_ref
        or effect["effect_intent_ref"] != effect_ref
        or delivery["effect_intent_ref"] != effect_ref
        or selection["effect_fence_ref"] != phase_value("effect_fence_ref")
        or effect["current_effect_fence_ref"] != phase_value("current_effect_head_fence_ref")
        or selection["delivery_attempt_ref"] != phase_value("delivery_attempt_ref")
        or delivery["current_delivery_attempt_ref"] != phase_value("current_delivery_head_attempt_ref")
        or selection["head_revision"] != phase_value("selection_head_revision")
        or selection["head_digest"] != phase_value("selection_head_digest")
        or selection["updated_at"] != phase_value("selection_head_updated_at")
        or effect["head_revision"] != phase_value("current_effect_head_revision")
        or effect["head_digest"] != phase_value("current_effect_head_digest")
        or effect["effect_state"] != phase_value("current_effect_head_state")
        or effect["cancellation_effect_intent_ref"] != phase_value("current_effect_head_cancellation_effect_intent_ref")
        or effect["updated_at"] != phase_value("current_effect_head_updated_at")
        or delivery["head_revision"] != phase_value("current_delivery_head_revision")
        or delivery["head_digest"] != phase_value("current_delivery_head_digest")
        or delivery["delivery_state"] != phase_value("current_delivery_head_state")
        or delivery["updated_at"] != phase_value("current_delivery_head_updated_at")):
        return False
    return True


def build_terminal_plan(
    command: RecordRW0TerminalOutcomeCommandV1,
    facts: TerminalFacts, witness: TerminalHeadWitness,
    stop: dict[str, object], recorded_at: str,
) -> TerminalPlan:
    if (type(command) is not RecordRW0TerminalOutcomeCommandV1
        or type(facts) is not TerminalFacts
        or type(witness) is not TerminalHeadWitness):
        raise ValueError("invalid terminal plan input")
    _time(recorded_at)
    selector = command.to_mapping()
    relation = command.p1_command.relation.to_mapping()
    basis = command.p1_command.basis.to_mapping()
    act = cast(dict[str, object], basis["verified_admission_act"])
    fact = cast(dict[str, object], basis["scope_admission_fact"])
    post = facts.section41
    prior = facts.prior
    decision = facts.decision
    p1_relation = facts.relation.mapping
    p1_result = facts.guarded_result.mapping
    c1 = facts.c1_rank15
    if (prior.branch not in NORMAL_PAIRS
        or decision.decision_kind != NORMAL_PAIRS[prior.branch]
        or p1_relation["branch"] != prior.branch
        or prior.decision_ref != decision.decision_ref
        or prior.receipt_graph_digest != facts.receipt.mutation_graph_digest
        or prior.result_digest != p1_result["guarded_result_digest"]
        or post.command != command.section41_command
        or c1.admission_result.membership_ref != command.c1_rank15.membership_ref
        or witness.coordinates != tuple(selector["heads"])
        or stop != selector["stop"]
        or not snapshot_compatible(command, facts, witness)):
        raise ValueError("terminal predecessor mismatch")
    acceptance = facts.acceptance.mapping if facts.acceptance is not None else None
    if (prior.branch == "candidate_acceptance") != (acceptance is not None):
        raise ValueError("terminal acceptance mismatch")
    if acceptance is not None and (
        acceptance["acceptance_fact_ref"] != relation["preassigned_acceptance_fact_ref"]
        or acceptance["acceptance_fact_ref"] != p1_relation["acceptance_fact_ref"]
        or acceptance["acceptance_fact_digest"] != p1_relation["acceptance_fact_digest"]
        or acceptance["decision_ref"] != decision.decision_ref
        or acceptance["decision_digest"] != decision.decision_digest
        or acceptance["lineage_ref"] != fact["lineage_ref"]
        or acceptance["scope_ref"] != fact["scope_ref"]
    ):
        raise ValueError("terminal acceptance mismatch")
    acceptance_ref = acceptance["acceptance_fact_ref"] if acceptance is not None else None
    acceptance_digest = acceptance["acceptance_fact_digest"] if acceptance is not None else None
    witness_bytes = witness.canonical_bytes
    heads_bytes = _canonical({"heads": list(witness.coordinates)})
    stop_bytes = _canonical({"stop": stop})
    context = seal_row(CONTEXT, {
        "schema_id": CONTEXT_SCHEMA,
        "context_ref": selector["context_ref"], "profile": PROFILE,
        "mutation_ref": selector["mutation_ref"],
        "phase_basis_ref": selector["phase_basis_ref"],
        "phase_basis_digest": selector["phase_basis_digest"],
        "program_ref": relation["program_ref"],
        "lineage_ref": fact["lineage_ref"], "scope_ref": fact["scope_ref"],
        "p0_act_ref": act["act_ref"], "p0_act_digest": act["act_digest"],
        "p0_fact_ref": fact["admission_fact_ref"],
        "p0_fact_digest": fact["admission_fact_digest"],
        "section41_context_ref": post.context.context_ref,
        "section41_context_digest": post.context.context_digest,
        "section41_proposal_ref": post.proposal.proposal_ref,
        "section41_proposal_digest": post.proposal.proposal_digest,
        "section41_receipt_mutation_ref": post.receipt.mutation_ref,
        "section41_receipt_digest": post.receipt.receipt_digest,
        "evidence_set_ref": post.receipt.evidence_set_ref,
        "evidence_set_digest": post.receipt.evidence_set_digest,
        "c1_membership_ref": c1.admission_result.membership_ref,
        "c1_membership_digest": c1.admission_result.membership_digest,
        "c1_receipt_digest": c1.admission_result.receipt_digest,
        "p1_basis_ref": basis["basis_ref"], "p1_basis_digest": basis["basis_digest"],
        "p1_decision_ref": decision.decision_ref,
        "p1_decision_digest": decision.decision_digest,
        "p1_decision_kind": decision.decision_kind,
        "p1_result_ref": p1_result["guarded_result_ref"],
        "p1_result_digest": p1_result["guarded_result_digest"],
        "p1_receipt_mutation_ref": facts.receipt.mutation_ref,
        "p1_receipt_graph_digest": facts.receipt.mutation_graph_digest,
        "p1_receipt_digest_anchor": _generic_receipt_anchor(facts.receipt),
        "acceptance_fact_ref": acceptance_ref,
        "acceptance_fact_digest": acceptance_digest,
        "command_safe_bytes": command.safe_bytes,
        "reached_owner_manifest_bytes": _canonical({"roles": selector["reached_owners"]}),
        "closure_heads_bytes": witness_bytes,
        "closure_stop_bytes": stop_bytes,
        "recorded_at": recorded_at, "context_digest": "",
    })
    c = context.mapping
    outcome = seal_row(OUTCOME, {
        "schema_id": OUTCOME_SCHEMA,
        "outcome_value_ref": selector["outcome_value_ref"],
        "context_ref": c["context_ref"], "context_digest": c["context_digest"],
        "phase_basis_ref": selector["phase_basis_ref"],
        "phase_basis_digest": selector["phase_basis_digest"],
        "branch": "normal", "outcome": NORMAL_PAIRS[prior.branch],
        "decision_ref": decision.decision_ref,
        "decision_digest": decision.decision_digest,
        "decision_kind": decision.decision_kind,
        "guarded_result_ref": p1_result["guarded_result_ref"],
        "guarded_result_digest": p1_result["guarded_result_digest"],
        "p1_receipt_mutation_ref": facts.receipt.mutation_ref,
        "p1_receipt_graph_digest": facts.receipt.mutation_graph_digest,
        "closure_heads_bytes": heads_bytes, "closure_stop_bytes": stop_bytes,
        "evidence_set_ref": post.receipt.evidence_set_ref,
        "evidence_set_digest": post.receipt.evidence_set_digest,
        "acceptance_fact_ref": acceptance_ref,
        "acceptance_fact_digest": acceptance_digest,
        "reconciliation_ref": None, "reconciliation_digest": None,
        "mismatch_ref": None, "mismatch_digest": None,
        "outcome_value_digest": "",
    })
    o = outcome.mapping
    result = seal_row(RESULT, {
        "schema_id": RESULT_SCHEMA,
        "result_ref": selector["result_ref"],
        "outcome_value_ref": o["outcome_value_ref"],
        "outcome_value_digest": o["outcome_value_digest"],
        "context_ref": c["context_ref"], "context_digest": c["context_digest"],
        "branch": "normal", "outcome": o["outcome"],
        "recorded_at": recorded_at, "result_digest": "",
    })
    r = result.mapping
    members = list(selector["reached_owners"])
    members.extend((
        {"role": "terminal_context", "ref": c["context_ref"], "digest": c["context_digest"]},
        {"role": "terminal_outcome", "ref": o["outcome_value_ref"], "digest": o["outcome_value_digest"]},
        {"role": "terminal_result", "ref": r["result_ref"], "digest": r["result_digest"]},
    ))
    if acceptance is not None:
        members.append({"role": "acceptance_fact", "ref": acceptance_ref,
                        "digest": acceptance_digest})
    if tuple(item["role"] for item in members) != GRAPH_ROLES + (
        ("acceptance_fact",) if acceptance is not None else ()):
        raise ValueError("terminal graph roles")
    graph = _digest(GRAPH_PROFILE + ".identity", members)
    committed_digest = _digest(_COMMITTED_RESULT_DOMAIN, {
        "command_digest": command.command_digest,
        "context_digest": c["context_digest"],
        "outcome_value_digest": o["outcome_value_digest"],
        "result_digest": r["result_digest"], "graph_digest": graph,
        "recorded_at": recorded_at,
    })
    receipt = seal_row(RECEIPT, {
        "schema_id": RECEIPT_SCHEMA,
        "receipt_ref": selector["receipt_ref"],
        "mutation_ref": selector["mutation_ref"],
        "command_digest": command.command_digest, "profile": PROFILE,
        "family_route": selector["family_route"],
        "phase_basis_ref": selector["phase_basis_ref"],
        "phase_basis_digest": selector["phase_basis_digest"],
        "p1_decision_ref": decision.decision_ref,
        "context_ref": c["context_ref"], "context_digest": c["context_digest"],
        "outcome_value_ref": o["outcome_value_ref"],
        "outcome_value_digest": o["outcome_value_digest"],
        "result_ref": r["result_ref"], "result_digest": r["result_digest"],
        "graph_profile": GRAPH_PROFILE, "graph_digest": graph,
        "committed_result_digest": committed_digest,
        "recorded_at": recorded_at, "receipt_digest": "",
    })
    committed = TerminalCommittedV1(
        mutation_ref=cast(str, selector["mutation_ref"]),
        command_digest=command.command_digest,
        receipt_ref=cast(str, selector["receipt_ref"]),
        outcome_value_ref=cast(str, selector["outcome_value_ref"]),
        outcome=cast(str, o["outcome"]),
        committed_result_digest=committed_digest, recorded_at=recorded_at,
    )
    return TerminalPlan((context, outcome, result, receipt), committed)
