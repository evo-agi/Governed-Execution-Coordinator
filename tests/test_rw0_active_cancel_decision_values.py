"""Closed, safe private cancellation command and planned row values."""
from __future__ import annotations

import pytest

from ge_nwp_coordinator._rw0_cancel_decision_contracts import RecordRW0ActiveCancelDecisionCommandV1
from ge_nwp_coordinator._rw0_cancel_decision_plan import build_cancel_decision_plan
from ge_nwp_coordinator._rw0_terminal_outcome_contracts import _canonical


def _command(target_class: str = "author_candidate") -> RecordRW0ActiveCancelDecisionCommandV1:
    digest = "a" * 64
    program = {"program_ref": "program.offline", "program_version_ref": "version.offline",
               "program_version_number": 1, "basis_decision_ref": "decision.prior",
               "head_revision": 0, "head_digest": digest,
               "semantic_attempt_ref": "attempt.offline", "candidate_ref": "candidate.offline",
               "attempt_fence_ref": "fence.attempt", "attempt_fence_digest": digest}
    effect_head = {"schema_id": "governed-execution.nwp-development-effect-head.v1",
                   "effect_intent_ref": "effect.offline", "program_ref": "program.offline",
                   "current_effect_fence_ref": "fence.effect", "head_revision": 0,
                   "effect_state": "ready_for_delivery", "cancellation_effect_intent_ref": None,
                   "updated_at": "2026-11-02T00:00:00Z", "head_digest": digest}
    delivery_head = {"schema_id": "governed-execution.nwp-development-delivery-head.v1",
                     "effect_intent_ref": "effect.offline", "program_ref": "program.offline",
                     "current_delivery_attempt_ref": "delivery.offline", "head_revision": 0,
                     "delivery_state": "planned", "updated_at": "2026-11-02T00:00:00Z",
                     "head_digest": "b" * 64}
    source = {"directive_ref": "directive.offline", "directive_digest": "c" * 64,
              "evidence_ref": "evidence.offline", "evidence_digest": "d" * 64}
    capsule = target_class in ("validate_candidate", "review_candidate")
    target = {"effect_intent_ref": "effect.offline", "effect_class": target_class,
              "effect_fence_ref": "fence.effect", "effect_fence_digest": "e" * 64,
              "effect_head": effect_head, "delivery_attempt_ref": "delivery.offline",
              "delivery_head": delivery_head, "originating_command_ref": "command.offline",
              "originating_command_digest": "f" * 64,
              "capsule_manifest_ref": "capsule.offline" if capsule else None,
              "capsule_digest": "1" * 64 if capsule else None}
    evidence = [
        {"role": "cancel_target_effect", "ref": "effect.offline", "digest": digest},
        {"role": "cancel_target_effect_fence", "ref": "fence.effect", "digest": "e" * 64},
        {"role": "cancel_source_directive", "ref": source["directive_ref"], "digest": source["directive_digest"]},
        {"role": "cancel_source_evidence", "ref": source["evidence_ref"], "digest": source["evidence_digest"]},
    ]
    if capsule:
        evidence.append({"role": "cancel_target_capsule", "ref": "capsule.offline", "digest": "1" * 64})
    return RecordRW0ActiveCancelDecisionCommandV1.prepare(
        mutation_ref="mutation.offline", phase_basis_ref="phase.offline",
        phase_basis_digest="2" * 64, program=program, target=target,
        stop={"ref": "stop.clear", "version": 0, "state": "clear", "updated_at": "1970-01-01T00:00:00Z"},
        source=source,
        basis={"repository_ref": "repository.offline", "base_git_object_format": "sha1",
               "base_git_oid": "3" * 40, "path_ceiling_digest": "4" * 64,
               "audience_ref": "audience.offline", "audience_digest": "5" * 64},
        evidence=evidence)


@pytest.mark.parametrize("target_class,roles", (
    ("author_candidate", 4), ("validate_candidate", 5), ("review_candidate", 5),
))
def test_closed_target_roles_and_cancel_decision_plan(target_class, roles):
    command = _command(target_class)
    plan = build_cancel_decision_plan(command, "2026-11-02T00:01:00Z")
    assert plan.decision.decision_kind == "cancel"
    assert plan.decision.decision_variant == "effect_cancellation"
    assert len(plan.bindings) == roles
    assert plan.receipt.mapping["target_effect_head_postimage"] == _canonical(command.to_mapping()["target"]["effect_head"])
    assert plan.receipt.mapping["target_delivery_head_postimage"] == _canonical(command.to_mapping()["target"]["delivery_head"])
    assert plan.decision.resulting_program_version_ref is None


@pytest.mark.parametrize("mutation", ("unknown", "role", "digest", "preassignment"))
def test_cancel_command_rejects_open_or_rebound_fields(mutation):
    command = _command()
    m = command.to_mapping()
    if mutation == "unknown":
        m["extension"] = "x"
    elif mutation == "role":
        m["evidence"][0]["role"] = "cancel_source_evidence"
    elif mutation == "digest":
        m["target"]["effect_head"]["head_digest"] = "0" * 64
    else:
        m["preassigned_effect_intent_ref"] = "changed"
    with pytest.raises(ValueError):
        RecordRW0ActiveCancelDecisionCommandV1(_canonical(m))
