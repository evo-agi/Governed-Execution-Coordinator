"""Test-only checked second-attempt rows for active-cancel lineage probes."""
from __future__ import annotations

import sqlite3

from ge_nwp_coordinator import _development_program_row_values as program_rows
from ge_nwp_coordinator import _development_effect_row_values as effect_rows
from ge_nwp_coordinator._development_row_value_support import _domain_separated_digest
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1, EffectFenceV1, WorkerCommandV1, DeliveryEnvelopeV1,
)


def _row(db: sqlite3.Connection, table: str, where: str, args: tuple[object, ...]) -> dict[str, object]:
    columns = tuple(item[1] for item in db.execute(f"PRAGMA table_info({table})"))
    raw = db.execute(f"SELECT {', '.join(columns)} FROM {table} WHERE {where} LIMIT 1", args).fetchone()
    assert raw is not None
    return dict(zip(columns, raw, strict=True))


def _insert(db: sqlite3.Connection, table: str, columns: tuple[str, ...],
            row: dict[str, object], adapter) -> None:
    values = tuple(row[name] for name in columns)
    adapter(values)
    db.execute(f"INSERT INTO {table} ({', '.join(columns)}) "
               f"VALUES ({', '.join('?' for _ in columns)})", values)


def seed_selected_second_attempt_author_target(
    db: sqlite3.Connection, first_command,
) -> tuple[dict[str, object], ...]:
    """Materialize candidate-repair's already selected attempt B in disposable state."""
    first = first_command.to_mapping()
    program_ref = first["program"]["program_ref"]
    phase = _row(db, "rw0_phase_instances", "phase_basis_ref=?",
                 (first["phase_basis_ref"],))
    decision = _row(db, "development_decisions", "decision_variant=?", ("candidate_repair",))
    assert decision["program_ref"] == program_ref
    second_ref = decision["preassigned_semantic_attempt_ref"]
    candidate_ref = decision["preassigned_candidate_ref"]
    version_ref = decision["resulting_program_version_ref"]
    version = _row(db, "development_program_versions", "program_version_ref=?", (version_ref,))
    member = _row(db, "development_program_version_work_items", "program_version_ref=?",
                  (version_ref,))
    assert second_ref != phase["semantic_attempt_ref"]
    assert candidate_ref != phase["candidate_ref"]

    attempt = _row(db, "development_semantic_attempts", "semantic_attempt_ref=?",
                   (phase["semantic_attempt_ref"],))
    attempt.update(semantic_attempt_ref=second_ref, program_version_ref=version_ref,
                   accepted_intent_revision_ref=version["accepted_intent_revision_ref"],
                   work_item_revision_ref=member["work_item_revision_ref"],
                   attempt_number=2, candidate_ref=candidate_ref,
                   selection_decision_ref=decision["decision_ref"])
    attempt_columns = program_rows._DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS
    attempt["semantic_attempt_digest"] = _domain_separated_digest(
        program_rows._DEVELOPMENT_SEMANTIC_ATTEMPT_DOMAIN,
        {key: attempt[key] for key in attempt_columns if key != "semantic_attempt_digest"})
    _insert(db, "development_semantic_attempts", attempt_columns, attempt,
            program_rows.development_semantic_attempt_row_value_from_row_tuple)

    old_fence = _row(db, "development_attempt_fences", "attempt_fence_ref=?",
                     (phase["attempt_fence_ref"],))
    fence_ref = "attempt-fence.audit.second"
    attempt_fence = dict(old_fence)
    attempt_fence.update(attempt_fence_ref=fence_ref, program_version_ref=version_ref,
                         accepted_intent_revision_ref=version["accepted_intent_revision_ref"],
                         work_item_revision_ref=member["work_item_revision_ref"],
                         semantic_attempt_ref=second_ref)
    af_columns = effect_rows._DEVELOPMENT_ATTEMPT_FENCE_COLUMNS
    old_fence_value = effect_rows.development_attempt_fence_row_value_from_row_tuple(
        tuple(old_fence[key] for key in af_columns)).attempt_fence
    af_value = old_fence_value.to_mapping()
    af_value.update(attempt_fence_ref=fence_ref, program_version_ref=version_ref,
                    accepted_intent_revision_ref=version["accepted_intent_revision_ref"],
                    work_item_revision_ref=member["work_item_revision_ref"],
                    semantic_attempt_ref=second_ref)
    attempt_fence["attempt_fence_digest"] = _domain_separated_digest(
        AttemptFenceV1._DOMAIN,
        {key: value for key, value in af_value.items() if key != "attempt_fence_digest"})
    AttemptFenceV1.from_mapping({**af_value,
        "attempt_fence_digest": attempt_fence["attempt_fence_digest"]})
    _insert(db, "development_attempt_fences", af_columns, attempt_fence,
            effect_rows.development_attempt_fence_row_value_from_row_tuple)

    intent_ref = "effect-intent.audit.second"
    effect_fence_ref = "effect-fence.audit.second"
    command_ref = "command.audit.second"
    delivery_ref = "delivery-attempt.audit.second"
    old_intent = _row(db, "development_effect_intents", "effect_intent_ref=?",
                      (phase["effect_intent_ref"],))
    intent = dict(old_intent)
    intent.update(effect_intent_ref=intent_ref, program_version_ref=version_ref,
                  semantic_attempt_ref=second_ref, candidate_ref=candidate_ref,
                  command_ref=command_ref, basis_decision_ref=decision["decision_ref"])
    i_columns = effect_rows._DEVELOPMENT_EFFECT_INTENT_COLUMNS
    intent["effect_intent_digest"] = _domain_separated_digest(
        effect_rows._EFFECT_INTENT_DOMAIN,
        {key: intent[key] for key in i_columns if key != "effect_intent_digest"})
    _insert(db, "development_effect_intents", i_columns, intent,
            effect_rows.development_effect_intent_row_value_from_row_tuple)

    old_author = _row(db, "development_author_commands", "command_ref=?",
                      (phase["author_command_ref"],))
    a_columns = effect_rows._DEVELOPMENT_AUTHOR_COMMAND_COLUMNS
    author_value = effect_rows.development_author_command_row_value_from_row_tuple(
        tuple(old_author[key] for key in a_columns)).author_command.to_mapping()
    author_value.update(command_ref=command_ref, program_version_ref=version_ref,
                        accepted_intent_revision_ref=version["accepted_intent_revision_ref"],
                        work_item_revision_ref=member["work_item_revision_ref"],
                        semantic_attempt_ref=second_ref, candidate_ref=candidate_ref,
                        effect_intent_ref=intent_ref, attempt_fence_ref=fence_ref,
                        attempt_fence_digest=attempt_fence["attempt_fence_digest"],
                        effect_fence_ref=effect_fence_ref)
    command_digest = _domain_separated_digest(
        WorkerCommandV1._DOMAIN,
        {key: value for key, value in author_value.items()
         if key not in ("command_digest", "effect_fence_digest")})

    old_effect_fence = _row(db, "development_effect_fences", "effect_intent_ref=?",
                            (phase["effect_intent_ref"],))
    ef_columns = effect_rows._DEVELOPMENT_EFFECT_FENCE_COLUMNS
    effect_fence_value = effect_rows.development_effect_fence_row_value_from_row_tuple(
        tuple(old_effect_fence[key] for key in ef_columns)).effect_fence.to_mapping()
    effect_fence_value.update(effect_fence_ref=effect_fence_ref,
                              attempt_fence_ref=fence_ref,
                              attempt_fence_digest=attempt_fence["attempt_fence_digest"],
                              program_version_ref=version_ref,
                              accepted_intent_revision_ref=version["accepted_intent_revision_ref"],
                              work_item_revision_ref=member["work_item_revision_ref"],
                              semantic_attempt_ref=second_ref, effect_intent_ref=intent_ref,
                              command_ref=command_ref, command_digest=command_digest,
                              candidate_ref=candidate_ref)
    effect_fence_digest = _domain_separated_digest(
        EffectFenceV1._DOMAIN,
        {key: value for key, value in effect_fence_value.items()
         if key != "effect_fence_digest"})
    EffectFenceV1.from_mapping({**effect_fence_value,
        "effect_fence_digest": effect_fence_digest})
    effect_fence = dict(old_effect_fence)
    effect_fence.update({key: effect_fence_value[key] for key in effect_fence
                         if key in effect_fence_value and key != "effect_fence_digest"})
    effect_fence["effect_fence_digest"] = effect_fence_digest
    _insert(db, "development_effect_fences", ef_columns, effect_fence,
            effect_rows.development_effect_fence_row_value_from_row_tuple)

    author_value.update(effect_fence_digest=effect_fence_digest,
                        command_digest=command_digest)
    WorkerCommandV1.from_mapping(author_value)
    author = dict(old_author)
    author.update({key: author_value[key] for key in author
                   if key in author_value and key != "path_ceiling_json"})
    _insert(db, "development_author_commands", a_columns, author,
            effect_rows.development_author_command_row_value_from_row_tuple)

    old_delivery = _row(db, "development_delivery_attempts", "effect_intent_ref=?",
                        (phase["effect_intent_ref"],))
    delivery = dict(old_delivery)
    delivery.update(delivery_attempt_ref=delivery_ref, program_version_ref=version_ref,
                    command_ref=command_ref, command_digest=command_digest,
                    semantic_attempt_ref=second_ref, effect_intent_ref=intent_ref,
                    attempt_fence_ref=fence_ref,
                    attempt_fence_digest=attempt_fence["attempt_fence_digest"],
                    effect_fence_ref=effect_fence_ref,
                    effect_fence_digest=effect_fence_digest,
                    basis_decision_ref=decision["decision_ref"])
    d_columns = effect_rows._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS
    envelope = {key: delivery[key] for key in DeliveryEnvelopeV1._FIELDS
                if key != "delivery_envelope_digest"}
    delivery["delivery_envelope_digest"] = _domain_separated_digest(
        DeliveryEnvelopeV1._DOMAIN, envelope)
    DeliveryEnvelopeV1.from_mapping({**envelope,
        "delivery_envelope_digest": delivery["delivery_envelope_digest"]})
    delivery["delivery_attempt_digest"] = _domain_separated_digest(
        effect_rows._DELIVERY_ATTEMPT_DOMAIN,
        {"schema_id": effect_rows._DELIVERY_ATTEMPT_WRAPPER_SCHEMA,
         **{key: delivery[key] for key in (
            "delivery_envelope_digest", "delivery_kind", "delivery_number",
            "predecessor_delivery_attempt_ref", "basis_decision_ref", "recorded_at")}})
    _insert(db, "development_delivery_attempts", d_columns, delivery,
            effect_rows.development_delivery_attempt_row_value_from_row_tuple)

    old_head = _row(db, "development_effect_heads", "effect_intent_ref=?",
                    (phase["effect_intent_ref"],))
    head = dict(old_head)
    head.update(effect_intent_ref=intent_ref, current_effect_fence_ref=effect_fence_ref)
    h_columns = effect_rows._DEVELOPMENT_EFFECT_HEAD_COLUMNS
    head["head_digest"] = _domain_separated_digest(
        effect_rows._EFFECT_HEAD_DOMAIN,
        {key: head[key] for key in h_columns if key != "head_digest"})
    _insert(db, "development_effect_heads", h_columns, head,
            effect_rows.development_effect_head_row_value_from_row_tuple)
    old_delivery_head = _row(db, "development_delivery_heads", "effect_intent_ref=?",
                             (phase["effect_intent_ref"],))
    delivery_head = dict(old_delivery_head)
    delivery_head.update(effect_intent_ref=intent_ref,
                         current_delivery_attempt_ref=delivery_ref)
    dh_columns = effect_rows._DEVELOPMENT_DELIVERY_HEAD_COLUMNS
    delivery_head["head_digest"] = _domain_separated_digest(
        effect_rows._DELIVERY_HEAD_DOMAIN,
        {key: delivery_head[key] for key in dh_columns if key != "head_digest"})
    _insert(db, "development_delivery_heads", dh_columns, delivery_head,
            effect_rows.development_delivery_head_row_value_from_row_tuple)
    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    return attempt, attempt_fence, intent, effect_fence, author, delivery, head, delivery_head
