"""Fenced local currentness proof; no external source or effect authorization."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import cast
from . import _development_effect_row_values as e
from . import _development_program_row_values as p
from ._rw0_terminal_outcome_contracts import _canonical, _digest
from ._rw0_cancel_decision_contracts import RecordRW0ActiveCancelDecisionCommandV1
from ._sqlite_rw0_c2_progression import _one as _program_one
from ._sqlite_rw0_c1_readers import _read_phase_by_pair, _read_relation_set, _read_receipt
from ._sqlite_rw0_c1 import _verify_phase_family_rows
from .persistence_contracts import (
    GLOBAL_STOP_CURRENT_ROW_COLUMNS, GlobalStopCurrentRecordEnvelope,
    global_stop_current_envelope_from_row,
)
from .sqlite_global_stop_event_contracts import _GLOBAL_STOP_CURRENT_SELECT, _GLOBAL_STOP_SINGLETON_ID
from .sqlite_transition_select_support import _MutationReadCapability, _execute_select_fetch_bounded
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode

__all__: tuple[str, ...] = ()

_EFFECT = {
    "development_effect_intents": (e._DEVELOPMENT_EFFECT_INTENT_COLUMNS, e.development_effect_intent_row_value_from_row_tuple),
    "development_effect_fences": (e._DEVELOPMENT_EFFECT_FENCE_COLUMNS, e.development_effect_fence_row_value_from_row_tuple),
    "development_effect_heads": (e._DEVELOPMENT_EFFECT_HEAD_COLUMNS, e.development_effect_head_row_value_from_row_tuple),
    "development_delivery_attempts": (e._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS, e.development_delivery_attempt_row_value_from_row_tuple),
    "development_delivery_heads": (e._DEVELOPMENT_DELIVERY_HEAD_COLUMNS, e.development_delivery_head_row_value_from_row_tuple),
    "development_author_commands": (e._DEVELOPMENT_AUTHOR_COMMAND_COLUMNS, e.development_author_command_row_value_from_row_tuple),
}


def _integrity() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def _effect_one(capability: object, table: str, key: str, value: object) -> object | None:
    if table not in _EFFECT or key not in _EFFECT[table][0]:
        raise _integrity() from None
    columns, adapter = _EFFECT[table]
    try:
        rows = _execute_select_fetch_bounded(
            capability=cast(_MutationReadCapability, capability),
            sql=f"SELECT {', '.join(columns)} FROM {table} WHERE {key}=? LIMIT 2",
            parameters=(value,), limit=2)
        if len(rows) > 1:
            raise _integrity()
        return adapter(rows[0]) if rows else None
    except SQLiteMutationStoreError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None


def _read_cancel_global_stop_current(capability: object) -> GlobalStopCurrentRecordEnvelope:
    try:
        rows = _execute_select_fetch_bounded(
            capability=cast(_MutationReadCapability, capability),
            sql=_GLOBAL_STOP_CURRENT_SELECT.sql,
            parameters=(_GLOBAL_STOP_SINGLETON_ID,), limit=2)
        if len(rows) != 1 or type(rows[0]) is not tuple:
            raise _integrity()
        envelope = global_stop_current_envelope_from_row(
            dict(zip(GLOBAL_STOP_CURRENT_ROW_COLUMNS, rows[0], strict=True)))
        if type(envelope) is not GlobalStopCurrentRecordEnvelope:
            raise _integrity()
        return envelope
    except SQLiteMutationStoreError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None


@dataclass(frozen=True, slots=True)
class CancelCurrentnessV1:
    classification: str
    mismatch_class: str | None = None
    mismatch_ref: str | None = None
    mismatch_digest: str | None = None
    heads_bytes: bytes | None = None
    stop_bytes: bytes | None = None
    verification_safe_bytes: bytes | None = None


def checked_immutable_cancel_lineage(
    capability: object, command: RecordRW0ActiveCancelDecisionCommandV1,
) -> tuple[object, p.DevelopmentSemanticAttemptRowValue,
           e.DevelopmentAttemptFenceRowValue, e.DevelopmentEffectIntentRowValue,
           e.DevelopmentEffectFenceRowValue, e.DevelopmentDeliveryAttemptRowValue,
           e.DevelopmentAuthorCommandRowValue] | None:
    """Check saved phase-to-target lineage without consulting mutable heads or stop."""
    m = command.to_mapping()
    program, target = (cast(dict[str, object], m[k]) for k in ("program", "target"))
    phase = _read_phase_by_pair(capability, m["phase_basis_ref"], m["phase_basis_digest"])
    if phase is None:
        return None
    receipt = _read_receipt(capability, phase.value("establishment_mutation_ref"))
    relation = _read_relation_set(capability, phase_basis_ref=m["phase_basis_ref"], membership_ref=None)
    if receipt is None:
        return None
    _verify_phase_family_rows(phase, relation, receipt, capability=capability)
    phase_version = _program_one(capability, "development_program_versions", "program_version_ref = ?",
                                 (phase.value("program_version_ref"),))
    attempt = _program_one(capability, "development_semantic_attempts", "semantic_attempt_ref = ?",
                           (program["semantic_attempt_ref"],))
    attempt_fence = _program_one(capability, "development_attempt_fences", "attempt_fence_ref = ?",
                                 (program["attempt_fence_ref"],))
    intent = _effect_one(capability, "development_effect_intents", "effect_intent_ref", target["effect_intent_ref"])
    fence = _effect_one(capability, "development_effect_fences", "effect_fence_ref", target["effect_fence_ref"])
    delivery = _effect_one(capability, "development_delivery_attempts", "delivery_attempt_ref", target["delivery_attempt_ref"])
    author = _effect_one(capability, "development_author_commands", "command_ref", target["originating_command_ref"])
    author_intent = _effect_one(capability, "development_effect_intents", "effect_intent_ref", phase.value("effect_intent_ref"))
    author_fence = _effect_one(capability, "development_effect_fences", "effect_fence_ref", phase.value("effect_fence_ref"))
    if (type(phase_version) is not p.DevelopmentProgramVersionRowValue
        or type(attempt) is not p.DevelopmentSemanticAttemptRowValue
        or type(attempt_fence) is not e.DevelopmentAttemptFenceRowValue
        or type(intent) is not e.DevelopmentEffectIntentRowValue
        or type(fence) is not e.DevelopmentEffectFenceRowValue
        or type(delivery) is not e.DevelopmentDeliveryAttemptRowValue
        or type(author) is not e.DevelopmentAuthorCommandRowValue
        or type(author_intent) is not e.DevelopmentEffectIntentRowValue
        or type(author_fence) is not e.DevelopmentEffectFenceRowValue):
        return None
    full_phase_fields = (
        "program_ref", "program_version_ref", "accepted_intent_revision_ref",
        "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
    )
    if (any(getattr(value, field) != phase.value(field)
            for value in (attempt, attempt_fence, fence, author)
            for field in full_phase_fields)
        or any(getattr(value, field) != phase.value(field)
               for value in (intent, delivery)
               for field in ("program_ref", "program_version_ref", "semantic_attempt_ref"))):
        return None
    if (phase.value("program_ref") != program["program_ref"]
        or phase.value("semantic_attempt_ref") != program["semantic_attempt_ref"]
        or phase.value("candidate_ref") != program["candidate_ref"]
        or phase.value("attempt_fence_ref") != program["attempt_fence_ref"]
        or phase.value("attempt_fence_digest") != program["attempt_fence_digest"]
        or phase_version.program_ref != phase.value("program_ref")
        or phase_version.program_version_number != phase.value("program_version_number")
        or attempt.semantic_attempt_digest != phase.value("semantic_attempt_digest")
        or attempt.attempt_number != phase.value("attempt_number")
        or attempt.candidate_ref != phase.value("candidate_ref")
        or attempt.selection_decision_ref != phase.value("basis_decision_ref")
        or attempt_fence.attempt_fence_digest != phase.value("attempt_fence_digest")
        or intent.candidate_ref != phase.value("candidate_ref")
        or intent.basis_decision_ref != phase.value("basis_decision_ref")
        or intent.effect_class != target["effect_class"]
        or intent.command_ref != author.command_ref
        or fence.effect_intent_ref != intent.effect_intent_ref
        or fence.effect_class != intent.effect_class
        or fence.candidate_ref != phase.value("candidate_ref")
        or fence.command_ref != author.command_ref
        or fence.command_digest != author.command_digest
        or fence.attempt_fence_ref != attempt_fence.attempt_fence_ref
        or fence.attempt_fence_digest != attempt_fence.attempt_fence_digest
        or fence.effect_fence_digest != target["effect_fence_digest"]
        or delivery.effect_intent_ref != intent.effect_intent_ref
        or delivery.command_ref != author.command_ref
        or delivery.command_digest != author.command_digest
        or delivery.attempt_fence_ref != attempt_fence.attempt_fence_ref
        or delivery.attempt_fence_digest != attempt_fence.attempt_fence_digest
        or delivery.effect_fence_ref != fence.effect_fence_ref
        or delivery.effect_fence_digest != fence.effect_fence_digest
        or delivery.basis_decision_ref != phase.value("basis_decision_ref")
        or author.command_ref != phase.value("author_command_ref")
        or author.command_digest != phase.value("author_command_digest")
        or author.effect_intent_ref != phase.value("effect_intent_ref")
        or author.effect_fence_ref != phase.value("effect_fence_ref")
        or author.effect_fence_digest != phase.value("effect_fence_digest")
        or author.attempt_fence_ref != attempt_fence.attempt_fence_ref
        or author.attempt_fence_digest != attempt_fence.attempt_fence_digest
        or author.candidate_ref != phase.value("candidate_ref")
        or author_intent.effect_intent_digest != phase.value("effect_intent_digest")
        or author_intent.effect_intent_ref != author.effect_intent_ref
        or author_intent.effect_class != "author_candidate"
        or author_fence.effect_fence_digest != phase.value("effect_fence_digest")
        or author_fence.effect_intent_ref != author.effect_intent_ref
        or author_fence.command_ref != author.command_ref
        or author_fence.attempt_fence_ref != attempt_fence.attempt_fence_ref
        or target["originating_command_digest"] != author.command_digest
        or target["effect_intent_ref"] != intent.effect_intent_ref
        or target["effect_fence_ref"] != fence.effect_fence_ref
        or target["delivery_attempt_ref"] != delivery.delivery_attempt_ref
        or author.repository_ref != fence.repository_ref
        or author.base_git_object_format != fence.base_git_object_format
        or author.base_git_oid != fence.base_git_oid
        or author.path_ceiling_json != fence.path_ceiling_json):
        return None
    if target["effect_class"] == "author_candidate":
        if (intent.effect_intent_ref != phase.value("effect_intent_ref")
            or fence.effect_fence_ref != phase.value("effect_fence_ref")
            or target["capsule_manifest_ref"] is not None
            or target["capsule_digest"] is not None
            or intent.portable_capsule_digest is not None
            or fence.portable_capsule_digest is not None):
            return None
    elif target["effect_class"] in ("validate_candidate", "review_candidate"):
        if (intent.effect_intent_ref == phase.value("effect_intent_ref")
            or target["capsule_digest"] != intent.portable_capsule_digest
            or target["capsule_digest"] != fence.portable_capsule_digest):
            return None
    else:
        return None
    return phase, attempt, attempt_fence, intent, fence, delivery, author


def check_coordinator_facts(capability: object,
                            command: RecordRW0ActiveCancelDecisionCommandV1,
                            *, external_source_available: bool = True) -> CancelCurrentnessV1:
    """Check immutable lineage first, then mutable facts; source input is artificial."""
    m = command.to_mapping()
    program, target = (cast(dict[str, object], m[k]) for k in ("program", "target"))
    try:
        lineage = checked_immutable_cancel_lineage(capability, command)
        if lineage is None:
            return CancelCurrentnessV1("integrity_failure")
        _, attempt, attempt_fence, intent, fence, delivery, author_command = lineage
        head = _program_one(capability, "development_program_heads", "program_ref = ?", (program["program_ref"],))
        version = _program_one(capability, "development_program_versions", "program_version_ref = ?", (program["program_version_ref"],))
        effect_head = _effect_one(capability, "development_effect_heads", "effect_intent_ref", target["effect_intent_ref"])
        delivery_head = _effect_one(capability, "development_delivery_heads", "effect_intent_ref", target["effect_intent_ref"])
        if (type(head) is not p.DevelopmentProgramHeadRowValue
            or type(version) is not p.DevelopmentProgramVersionRowValue
            or type(effect_head) is not e.DevelopmentEffectHeadRowValue
            or type(delivery_head) is not e.DevelopmentDeliveryHeadRowValue):
            return CancelCurrentnessV1("integrity_failure")
        if version.program_ref != program["program_ref"]:
            return CancelCurrentnessV1("integrity_failure")
        stop_envelope = _read_cancel_global_stop_current(capability)
        state = stop_envelope.state
        actual_stop = {"ref": state.stop_ref, "version": state.version,
                       "state": "active" if state.active else "clear", "updated_at": stop_envelope.updated_at}
        effect_image = {key: getattr(effect_head, key) for key in e._DEVELOPMENT_EFFECT_HEAD_COLUMNS}
        delivery_image = {key: getattr(delivery_head, key) for key in e._DEVELOPMENT_DELIVERY_HEAD_COLUMNS}
        heads = {"program": {"ref": head.program_ref, "version_ref": head.current_program_version_ref,
                              "version_number": head.current_program_version_number,
                              "revision": head.head_revision, "digest": head.head_digest},
                 "attempt": {"ref": attempt.semantic_attempt_ref, "digest": attempt.semantic_attempt_digest},
                 "effect": effect_image, "delivery": delivery_image,
                 "attempt_fence": {"ref": attempt_fence.attempt_fence_ref, "digest": attempt_fence.attempt_fence_digest},
                 "effect_fence": {"ref": fence.effect_fence_ref, "digest": fence.effect_fence_digest}}
        mismatches = [
            ("program_head", head.program_ref, {"ref": program["program_ref"], "version_ref": program["program_version_ref"], "version_number": program["program_version_number"], "revision": program["head_revision"], "digest": program["head_digest"]}, heads["program"]),
            ("program_version", version.program_version_ref,
             {"number": program["program_version_number"], "creating_decision_ref": program["basis_decision_ref"]},
             {"number": version.program_version_number, "creating_decision_ref": version.creating_decision_ref}),
            ("semantic_attempt", attempt.semantic_attempt_ref, {"candidate_ref": program["candidate_ref"]}, {"candidate_ref": attempt.candidate_ref}),
            ("attempt_fence", attempt_fence.attempt_fence_ref, {"ref": program["attempt_fence_ref"], "digest": program["attempt_fence_digest"]}, heads["attempt_fence"]),
            ("effect_fence", fence.effect_fence_ref, {"ref": target["effect_fence_ref"], "digest": target["effect_fence_digest"]}, heads["effect_fence"]),
            ("effect_head", effect_head.effect_intent_ref, target["effect_head"], effect_image),
            ("delivery_head", delivery_head.effect_intent_ref, target["delivery_head"], delivery_image),
            ("global_stop", state.stop_ref, m["stop"], actual_stop),
        ]
        basis = cast(dict[str, object], m["basis"])
        actual_basis = {"repository_ref": fence.repository_ref,
                        "base_git_object_format": fence.base_git_object_format,
                        "base_git_oid": fence.base_git_oid,
                        "path_ceiling_digest": hashlib.sha256(
                            fence.path_ceiling_json.encode("utf-8")).hexdigest(),
                        "audience_ref": basis["audience_ref"],
                        "audience_digest": basis["audience_digest"]}
        mismatches.append(("persisted_basis", fence.effect_fence_ref, basis, actual_basis))
        for table, key, ref, digest_name in (
            ("development_effect_intents", "effect_intent_ref", m["preassigned_effect_intent_ref"], "effect_intent_digest"),
            ("development_effect_fences", "effect_fence_ref", m["preassigned_effect_fence_ref"], "effect_fence_digest"),
            ("development_delivery_attempts", "delivery_attempt_ref", m["preassigned_delivery_attempt_ref"], "delivery_attempt_digest"),
        ):
            unexpected = _effect_one(capability, table, key, ref)
            if unexpected is not None:
                mismatches.append(("preassignment", ref, {"absent": True},
                                   {"ref": ref, "digest": getattr(unexpected, digest_name)}))
        mismatch = next(((cls, ref, expected, actual) for cls, ref, expected, actual in mismatches if expected != actual), None)
        closure_heads = _canonical({"heads": heads})
        closure_stop = _canonical({"stop": actual_stop})
        if mismatch is not None:
            cls, ref, expected, actual = mismatch
            digest = _digest("governed-execution.nwp-rw0-cancel-mismatch.v1", {
                "class": cls, "ref": ref, "expected": expected, "actual": actual})
            verification = _canonical({"classification": "proven_coordinator_mismatch", "mismatch_class": cls,
                                       "mismatch_ref": ref, "mismatch_digest": digest})
            return CancelCurrentnessV1("proven_coordinator_mismatch", cls, ref, digest,
                                       closure_heads, closure_stop, verification)
        if not external_source_available:
            return CancelCurrentnessV1("external_source_unresolved", heads_bytes=closure_heads,
                                       stop_bytes=closure_stop)
        return CancelCurrentnessV1("locally_current_source_unverified", heads_bytes=closure_heads,
                                   stop_bytes=closure_stop,
                                   verification_safe_bytes=_canonical({"classification": "locally_current_source_unverified"}))
    except SQLiteMutationStoreError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return CancelCurrentnessV1("integrity_failure")


def verify_after_fencing(capability: object,
                         command: RecordRW0ActiveCancelDecisionCommandV1,
                         *, external_source_available: bool = True) -> CancelCurrentnessV1:
    """Verify one exact persisted cancel family before a fresh local recheck."""
    from ._sqlite_rw0_cancel_decision import _one, _family_exact
    from ._rw0_cancel_decision_rows import RECEIPT
    from ._sqlite_rw0_terminal_anchor import read_terminal_anchor
    from ._sqlite_rw0_terminal_outcome import _anchor_family_exact
    from ._sqlite_rw0_cancel_pre_effect_terminal import check_phase_route_rows
    try:
        m = command.to_mapping()
        receipt = _one(capability, RECEIPT, "mutation_ref", m["mutation_ref"])
        if receipt is None:
            return CancelCurrentnessV1("commit_or_readback_unresolved")
        plan = _family_exact(capability, receipt)
        if (receipt.mapping["command_digest"] != command.command_digest
            or receipt.mapping["command_safe_bytes"] != command.safe_bytes
            or plan.committed.decision_ref != m["decision_ref"]):
            return CancelCurrentnessV1("integrity_failure")
        anchor = read_terminal_anchor(capability, "phase_basis_ref", m["phase_basis_ref"])
        check_phase_route_rows(capability, cast(str, m["phase_basis_ref"]), anchor)
        if anchor is not None:
            _anchor_family_exact(capability, anchor)
            return CancelCurrentnessV1("occupied_terminal_phase")
        return check_coordinator_facts(
            capability, command, external_source_available=external_source_available)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return CancelCurrentnessV1("integrity_failure")
