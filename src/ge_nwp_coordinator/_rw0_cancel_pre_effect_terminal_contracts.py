"""Closed private selector for one proven local pre-effect cancel block."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast
from ._rw0_terminal_outcome_contracts import _canonical, _digest, _safe_ref, _sha, _strict_bytes, _stop
from ._rw0_cancel_decision_contracts import RecordRW0ActiveCancelDecisionCommandV1, CancelDecisionCommittedV1
from ._rw0_cancel_pre_effect_terminal_rows import PROFILE, BRANCH, MISMATCH_CLASSES
from ._sqlite_rw0_cancel_currentness import CancelCurrentnessV1

__all__: tuple[str, ...] = ()

COMMAND_SCHEMA = "governed-execution.nwp-record-rw0-cancel-pre-effect-block-command.v1"
_FIELDS = ("schema_id", "profile", "mutation_ref", "phase_basis_ref", "phase_basis_digest", "program_ref", "decision_ref", "decision_digest", "decision_receipt_ref", "decision_receipt_digest", "decision_command_digest", "target_effect_intent_ref", "mismatch_class", "mismatch_ref", "mismatch_digest", "verification", "heads", "stop", "context_ref", "outcome_value_ref", "result_ref", "receipt_ref", "family_route", "command_digest")
_DERIVED = ("context_ref", "outcome_value_ref", "result_ref", "receipt_ref", "family_route")


def _check(value: object) -> dict[str, object]:
    if type(value) is not dict or set(value) != set(_FIELDS):
        raise ValueError("invalid cancel terminal command")
    m = cast(dict[str, object], value)
    if m["schema_id"] != COMMAND_SCHEMA or m["profile"] != PROFILE:
        raise ValueError("invalid cancel terminal command schema")
    for name in ("mutation_ref", "phase_basis_ref", "program_ref", "decision_ref", "decision_receipt_ref", "target_effect_intent_ref", "mismatch_ref", *_DERIVED):
        _safe_ref(m[name])
    for name in ("phase_basis_digest", "decision_digest", "decision_receipt_digest", "decision_command_digest", "mismatch_digest", "command_digest"):
        _sha(m[name])
    if m["mismatch_class"] not in MISMATCH_CLASSES:
        raise ValueError("invalid cancel mismatch class")
    if type(m["verification"]) is not dict or m["verification"] != {
        "classification": "proven_coordinator_mismatch", "mismatch_class": m["mismatch_class"],
        "mismatch_ref": m["mismatch_ref"], "mismatch_digest": m["mismatch_digest"]}:
        raise ValueError("invalid cancel verification binding")
    if type(m["heads"]) is not dict or set(m["heads"]) != {"heads"} or type(m["heads"]["heads"]) is not dict:
        raise ValueError("invalid cancel head binding")
    if type(m["stop"]) is not dict or set(m["stop"]) != {"stop"}:
        raise ValueError("invalid cancel stop binding")
    _stop(m["stop"]["stop"])
    stable = {k: m[k] for k in _FIELDS if k not in _DERIVED + ("command_digest",)}
    if any(m[name] != _digest(COMMAND_SCHEMA + "." + name + ".v1", stable)
           for name in _DERIVED):
        raise ValueError("invalid cancel terminal preassignment")
    if m["command_digest"] != _digest(COMMAND_SCHEMA + ".identity", {k: m[k] for k in _FIELDS if k != "command_digest"}):
        raise ValueError("invalid cancel terminal command digest")
    return m


@dataclass(frozen=True, slots=True, repr=False)
class RecordRW0CancelPreEffectTerminalCommandV1:
    safe_bytes: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if type(self.safe_bytes) is not bytes or _canonical(_check(_strict_bytes(self.safe_bytes))) != self.safe_bytes:
            raise ValueError("invalid cancel terminal bytes")

    @classmethod
    def prepare(cls, *, mutation_ref: str,
                decision_command: RecordRW0ActiveCancelDecisionCommandV1,
                committed: CancelDecisionCommittedV1,
                verification: CancelCurrentnessV1) -> RecordRW0CancelPreEffectTerminalCommandV1:
        if (type(decision_command) is not RecordRW0ActiveCancelDecisionCommandV1
            or type(committed) is not CancelDecisionCommittedV1
            or type(verification) is not CancelCurrentnessV1
            or verification.classification != "proven_coordinator_mismatch"
            or any(v is None for v in (verification.mismatch_class, verification.mismatch_ref,
                                       verification.mismatch_digest, verification.heads_bytes,
                                       verification.stop_bytes, verification.verification_safe_bytes))):
            raise ValueError("proven cancel mismatch required")
        d = decision_command.to_mapping()
        if (committed.mutation_ref != d["mutation_ref"] or committed.decision_ref != d["decision_ref"]):
            raise ValueError("wrong cancel decision")
        stable = {
            "schema_id": COMMAND_SCHEMA, "profile": PROFILE, "mutation_ref": mutation_ref,
            "phase_basis_ref": d["phase_basis_ref"], "phase_basis_digest": d["phase_basis_digest"],
            "program_ref": d["program"]["program_ref"], "decision_ref": committed.decision_ref,
            "decision_digest": committed.decision_digest,
            "decision_receipt_ref": committed.receipt_ref,
            "decision_receipt_digest": committed.receipt_digest,
            "decision_command_digest": decision_command.command_digest,
            "target_effect_intent_ref": d["target"]["effect_intent_ref"],
            "mismatch_class": verification.mismatch_class,
            "mismatch_ref": verification.mismatch_ref,
            "mismatch_digest": verification.mismatch_digest,
            "verification": _strict_bytes(cast(bytes, verification.verification_safe_bytes)),
            "heads": _strict_bytes(cast(bytes, verification.heads_bytes)),
            "stop": _strict_bytes(cast(bytes, verification.stop_bytes)),
        }
        m = dict(stable)
        m.update({name: _digest(COMMAND_SCHEMA + "." + name + ".v1", stable)
                  for name in _DERIVED})
        m["command_digest"] = _digest(COMMAND_SCHEMA + ".identity", m)
        return cls(_canonical(_check(m)))

    def to_mapping(self) -> dict[str, object]:
        return _check(_strict_bytes(self.safe_bytes))

    @property
    def command_digest(self) -> str:
        return cast(str, self.to_mapping()["command_digest"])


@dataclass(frozen=True, slots=True)
class CancelTerminalCommittedV1:
    mutation_ref: str
    decision_ref: str
    receipt_ref: str
    receipt_digest: str
    graph_digest: str
    committed_result_digest: str
    recorded_at: str


@dataclass(frozen=True, slots=True)
class CancelTerminalConflictV1:
    reason: str


@dataclass(frozen=True, slots=True)
class CancelTerminalRecoveryV1:
    status: str
    committed: CancelTerminalCommittedV1 | None = None
