"""Closed private artificial-offline active-cancel command and safe outcomes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast
from ._rw0_terminal_outcome_contracts import _canonical, _digest, _safe_ref, _sha, _strict_bytes, _stop
from ._rw0_cancel_decision_rows import COMMAND_SCHEMA, required_roles
from ._development_effect_row_values import _DEVELOPMENT_EFFECT_HEAD_COLUMNS, _DEVELOPMENT_DELIVERY_HEAD_COLUMNS

__all__: tuple[str, ...] = ()

_PROGRAM = ("program_ref", "program_version_ref", "program_version_number", "basis_decision_ref", "head_revision", "head_digest", "semantic_attempt_ref", "candidate_ref", "attempt_fence_ref", "attempt_fence_digest")
_TARGET = ("effect_intent_ref", "effect_class", "effect_fence_ref", "effect_fence_digest", "effect_head", "delivery_attempt_ref", "delivery_head", "originating_command_ref", "originating_command_digest", "capsule_manifest_ref", "capsule_digest")
_SOURCE = ("directive_ref", "directive_digest", "evidence_ref", "evidence_digest")
_BASIS = ("repository_ref", "base_git_object_format", "base_git_oid", "path_ceiling_digest", "audience_ref", "audience_digest")
_FIELDS = ("schema_id", "mutation_ref", "phase_basis_ref", "phase_basis_digest", "decision_ref", "program", "target", "stop", "source", "basis", "evidence", "preassigned_effect_intent_ref", "preassigned_effect_fence_ref", "preassigned_delivery_attempt_ref", "receipt_ref", "command_digest")
_DERIVED = ("decision_ref", "preassigned_effect_intent_ref", "preassigned_effect_fence_ref", "preassigned_delivery_attempt_ref", "receipt_ref")


def _exact(value: object, names: tuple[str, ...]) -> dict[str, object]:
    if type(value) is not dict or set(value) != set(names) or any(type(k) is not str for k in value):
        raise ValueError("invalid active cancel command fields")
    return cast(dict[str, object], value)


def _derived(stable: dict[str, object], name: str) -> str:
    return _digest(COMMAND_SCHEMA + "." + name + ".v1", stable)


def _check(mapping: object) -> dict[str, object]:
    m = _exact(mapping, _FIELDS)
    if m["schema_id"] != COMMAND_SCHEMA:
        raise ValueError("invalid active cancel command schema")
    for name in ("mutation_ref", "phase_basis_ref", "decision_ref", "preassigned_effect_intent_ref", "preassigned_effect_fence_ref", "preassigned_delivery_attempt_ref", "receipt_ref"):
        _safe_ref(m[name])
    _sha(m["phase_basis_digest"])
    p = _exact(m["program"], _PROGRAM)
    t = _exact(m["target"], _TARGET)
    s = _exact(m["source"], _SOURCE)
    b = _exact(m["basis"], _BASIS)
    _stop(m["stop"])
    for name in ("program_ref", "program_version_ref", "basis_decision_ref", "semantic_attempt_ref", "candidate_ref", "attempt_fence_ref"):
        _safe_ref(p[name])
    for name in ("head_digest", "attempt_fence_digest"):
        _sha(p[name])
    for name in ("program_version_number", "head_revision"):
        if type(p[name]) is not int or p[name] < (1 if name == "program_version_number" else 0):
            raise ValueError("invalid active cancel program number")
    for name in ("effect_intent_ref", "effect_fence_ref", "delivery_attempt_ref", "originating_command_ref"):
        _safe_ref(t[name])
    for name in ("effect_fence_digest", "originating_command_digest"):
        _sha(t[name])
    if t["effect_class"] not in ("author_candidate", "validate_candidate", "review_candidate"):
        raise ValueError("unsupported active cancel target")
    if t["effect_class"] == "author_candidate":
        if t["capsule_manifest_ref"] is not None or t["capsule_digest"] is not None:
            raise ValueError("unexpected target capsule")
    else:
        _safe_ref(t["capsule_manifest_ref"])
        _sha(t["capsule_digest"])
    for key, columns in (("effect_head", _DEVELOPMENT_EFFECT_HEAD_COLUMNS), ("delivery_head", _DEVELOPMENT_DELIVERY_HEAD_COLUMNS)):
        postimage = _exact(t[key], columns)
        if postimage["program_ref"] != p["program_ref"] or postimage["effect_intent_ref"] != t["effect_intent_ref"]:
            raise ValueError("wrong target head identity")
        _safe_ref(postimage["effect_intent_ref"])
        _sha(postimage["head_digest"])
        if type(postimage["head_revision"]) is not int or postimage["head_revision"] < 0:
            raise ValueError("invalid target head revision")
    if t["effect_head"]["current_effect_fence_ref"] != t["effect_fence_ref"] or t["delivery_head"]["current_delivery_attempt_ref"] != t["delivery_attempt_ref"]:
        raise ValueError("target head relation differs")
    for name in ("directive_ref", "evidence_ref"):
        _safe_ref(s[name])
    for name in ("directive_digest", "evidence_digest"):
        _sha(s[name])
    for name in ("repository_ref", "audience_ref"):
        _safe_ref(b[name])
    for name in ("path_ceiling_digest", "audience_digest"):
        _sha(b[name])
    if b["base_git_object_format"] not in ("sha1", "sha256") or type(b["base_git_oid"]) is not str or len(b["base_git_oid"]) != (40 if b["base_git_object_format"] == "sha1" else 64):
        raise ValueError("invalid base object")
    evidence = m["evidence"]
    roles = required_roles(cast(str, t["effect_class"]))
    if type(evidence) is not list or len(evidence) != len(roles):
        raise ValueError("incomplete cancel evidence")
    for item, role in zip(evidence, roles, strict=True):
        e = _exact(item, ("role", "ref", "digest"))
        if e["role"] != role:
            raise ValueError("wrong cancel evidence role")
        _safe_ref(e["ref"])
        _sha(e["digest"])
    expected = ((t["effect_intent_ref"], t["effect_head"]["head_digest"]),
                (t["effect_fence_ref"], t["effect_fence_digest"]),
                (s["directive_ref"], s["directive_digest"]),
                (s["evidence_ref"], s["evidence_digest"]))
    if any((item["ref"], item["digest"]) != pair for item, pair in zip(evidence, expected, strict=False)):
        raise ValueError("cancel evidence target differs")
    if len(roles) == 5 and (evidence[4]["ref"], evidence[4]["digest"]) != (t["capsule_manifest_ref"], t["capsule_digest"]):
        raise ValueError("cancel capsule evidence differs")
    stable = {k: m[k] for k in _FIELDS if k not in _DERIVED + ("command_digest",)}
    if any(m[name] != _derived(stable, name) for name in _DERIVED):
        raise ValueError("invalid cancel preassignment")
    if m["command_digest"] != _digest(COMMAND_SCHEMA + ".identity", {k: m[k] for k in _FIELDS if k != "command_digest"}):
        raise ValueError("invalid cancel command digest")
    return m


@dataclass(frozen=True, slots=True, repr=False)
class RecordRW0ActiveCancelDecisionCommandV1:
    safe_bytes: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if type(self.safe_bytes) is not bytes or _canonical(_check(_strict_bytes(self.safe_bytes))) != self.safe_bytes:
            raise ValueError("invalid active cancel command bytes")

    @classmethod
    def prepare(cls, *, mutation_ref: str, phase_basis_ref: str,
                phase_basis_digest: str, program: dict[str, object],
                target: dict[str, object], stop: dict[str, object],
                source: dict[str, object], basis: dict[str, object],
                evidence: list[dict[str, object]]) -> RecordRW0ActiveCancelDecisionCommandV1:
        stable = {"schema_id": COMMAND_SCHEMA, "mutation_ref": mutation_ref,
                  "phase_basis_ref": phase_basis_ref, "phase_basis_digest": phase_basis_digest,
                  "program": program, "target": target, "stop": stop,
                  "source": source, "basis": basis, "evidence": evidence}
        m = {"schema_id": COMMAND_SCHEMA, "mutation_ref": mutation_ref,
             "phase_basis_ref": phase_basis_ref, "phase_basis_digest": phase_basis_digest}
        m.update({name: _derived(stable, name) for name in _DERIVED})
        m.update({"program": program, "target": target, "stop": stop,
                  "source": source, "basis": basis, "evidence": evidence})
        m["command_digest"] = _digest(COMMAND_SCHEMA + ".identity", m)
        return cls(_canonical(_check(m)))

    def to_mapping(self) -> dict[str, object]:
        return _check(_strict_bytes(self.safe_bytes))

    @property
    def command_digest(self) -> str:
        return cast(str, self.to_mapping()["command_digest"])


@dataclass(frozen=True, slots=True)
class CancelDecisionCommittedV1:
    mutation_ref: str
    decision_ref: str
    decision_digest: str
    receipt_ref: str
    receipt_digest: str
    result_digest: str
    recorded_at: str


@dataclass(frozen=True, slots=True)
class CancelDecisionConflictV1:
    reason: str


@dataclass(frozen=True, slots=True)
class CancelDecisionRecoveryV1:
    status: str
    committed: CancelDecisionCommittedV1 | None = None
