"""Private, artificial-offline RW0-C2 P0 values.

These values validate already-verified safe evidence. They do not authenticate an
external policy, enroll a cell, or authorize any live effect.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import re
from typing import Any

_PREFIX = "governed-execution.nwp-rw0-c2-"
_PROFILE = "rw0-c2-single-realization-proof-v1"
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]{0,95}\Z", re.ASCII)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_RESERVED = ("connector-", "tunnel-", "workspace-", "org-", "organization-", "user-")
_ACT = ("schema_id", "act_ref", "act_digest", "lineage_ref", "scope_ref", "guard_profile", "applicability", "provenance_ref", "provenance_digest", "projection_digest")
_FACT = ("schema_id", "admission_fact_ref", "act_ref", "act_digest", "lineage_ref", "scope_ref", "guard_profile", "applicability", "provenance_ref", "provenance_digest", "one_shot_ceiling", "admission_fact_digest")
_COMMAND = ("schema_id", "operation_ref", "verified_admission_act", "expected_admission_fact", "enrollment_ref", "incarnation_ref", "authority_process_ref", "storage_custody_ref", "proof_profile_id", "command_digest")
_BASIS = ("schema_id", "operation_ref", "command_digest", "act_projection_digest", "admission_fact_ref", "admission_fact_digest", "enrollment_ref", "incarnation_ref", "authority_process_ref", "storage_custody_ref", "enrollment_evidence_ref", "enrollment_evidence_digest", "recording_permission_evidence_ref", "recording_permission_evidence_digest", "custody_evidence_ref", "custody_evidence_digest", "recorded_at", "basis_digest")
_RESULT = ("schema_id", "operation_ref", "command_digest", "admission_fact_ref", "admission_fact_digest", "basis_digest", "recorded_at", "result_class", "result_digest")
_RECEIPT = ("schema_id", "operation_ref", "command_digest", "act_ref", "act_digest", "act_projection_digest", "admission_fact_ref", "admission_fact_digest", "basis_digest", "result_digest", "recorded_at", "outcome", "receipt_digest")
_TABLE_FIELDS = {
    "rw0_c2_verified_admission_acts": _ACT,
    "rw0_c2_scope_admission_facts": _FACT,
    "rw0_c2_scope_admission_recording_bases": _BASIS,
    "rw0_c2_scope_admission_recording_receipts": _RECEIPT,
}


def _ref(value: object) -> bool:
    return type(value) is str and _REF.fullmatch(value) is not None and not value.lower().startswith(_RESERVED)


def _digest_value(value: object) -> bool:
    return type(value) is str and _DIGEST.fullmatch(value) is not None


def _time(value: object) -> bool:
    if type(value) is not str or len(value) != 20:
        return False
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%dT%H:%M:%SZ") == value
    except (ValueError, OverflowError):
        return False


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in items:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _strict_json(raw: bytes) -> dict[str, object]:
    if type(raw) is not bytes or len(raw) > 65536:
        raise ValueError("invalid P0 JSON")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    if type(value) is not dict or _canonical(value) != raw:
        raise ValueError("noncanonical P0 JSON")
    return value


def _self_digest(value: dict[str, object], own: str) -> str:
    schema = value["schema_id"]
    if type(schema) is not str:
        raise ValueError("invalid schema")
    preimage = {key: item for key, item in value.items() if key != own}
    return hashlib.sha256((schema + ".identity").encode("utf-8") + b"\0" + _canonical(preimage)).hexdigest()


def _exact(value: object, fields: tuple[str, ...], *, int_fields: tuple[str, ...] = ()) -> dict[str, object]:
    if type(value) is not dict or set(value) != set(fields) or any(type(key) is not str for key in value):
        raise ValueError("invalid P0 fields")
    if any(type(value[name]) is not (int if name in int_fields else str) for name in fields):
        raise ValueError("invalid P0 type")
    return value


def _check_act_and_fact(act: object, fact: object) -> tuple[dict[str, object], dict[str, object]]:
    act = _exact(act, _ACT)
    fact = _exact(fact, _FACT, int_fields=("one_shot_ceiling",))
    if (act["schema_id"] != _PREFIX + "verified-admission-act.v1"
        or fact["schema_id"] != _PREFIX + "scope-admission-fact.v1"
        or act["guard_profile"] != "rw0-c2-guard-v1"
        or act["applicability"] != "admitted_direct_local_bootstrap"
        or fact["one_shot_ceiling"] != 1
        or any(not _ref(act[name]) for name in ("act_ref", "lineage_ref", "scope_ref", "provenance_ref"))
        or not _ref(fact["admission_fact_ref"])
        or any(not _digest_value(act[name]) for name in ("act_digest", "provenance_digest", "projection_digest"))
        or not _digest_value(fact["admission_fact_digest"])
        or any(fact[name] != act[name] for name in ("act_ref", "act_digest", "lineage_ref", "scope_ref", "guard_profile", "applicability", "provenance_ref", "provenance_digest"))
        or _self_digest(act, "projection_digest") != act["projection_digest"]
        or _self_digest(fact, "admission_fact_digest") != fact["admission_fact_digest"]):
        raise ValueError("invalid admission act or fact")
    return act, fact


@dataclass(frozen=True, slots=True, repr=False)
class ScopeAdmissionCommandV1:
    canonical_bytes: bytes

    @classmethod
    def from_mapping(cls, value: dict[str, object]) -> "ScopeAdmissionCommandV1":
        if type(value) is not dict:
            raise ValueError("invalid admission command")
        return cls.from_json(_canonical(value))

    @classmethod
    def from_json(cls, raw: bytes) -> "ScopeAdmissionCommandV1":
        value = _strict_json(raw)
        if set(value) != set(_COMMAND) or any(type(key) is not str for key in value):
            raise ValueError("invalid admission command")
        if (value["schema_id"] != _PREFIX + "record-scope-admission-command.v1"
            or value["proof_profile_id"] != _PROFILE
            or any(not _ref(value[name]) for name in ("operation_ref", "enrollment_ref", "incarnation_ref", "authority_process_ref", "storage_custody_ref"))
            or not _digest_value(value["command_digest"])):
            raise ValueError("invalid admission command")
        _check_act_and_fact(value["verified_admission_act"], value["expected_admission_fact"])
        if _self_digest(value, "command_digest") != value["command_digest"]:
            raise ValueError("invalid admission command digest")
        return cls(raw)

    def to_mapping(self) -> dict[str, object]:
        return _strict_json(self.canonical_bytes)


@dataclass(frozen=True, slots=True, repr=False)
class ArtificialAdmissionSourceV1:
    """Test-owned independent safe source observation; never a live verifier."""
    policy_act_bytes: bytes
    audience: str
    enrollment_ref: str
    incarnation_ref: str
    authority_process_ref: str
    storage_custody_ref: str
    enrollment_evidence_ref: str
    enrollment_evidence_digest: str
    recording_permission_evidence_ref: str
    recording_permission_evidence_digest: str
    custody_evidence_ref: str
    custody_evidence_digest: str
    recording_permitted: bool
    disclosure_permitted: bool
    original_custody: bool
    old_execution_excluded: bool

    def checked_for(self, command: ScopeAdmissionCommandV1, *, disclosure: bool) -> dict[str, object]:
        if type(command) is not ScopeAdmissionCommandV1 or type(disclosure) is not bool:
            raise ValueError("invalid admission source input")
        requested = ScopeAdmissionCommandV1.from_json(command.canonical_bytes).to_mapping()
        act = _strict_json(self.policy_act_bytes)
        _check_act_and_fact(act, requested["expected_admission_fact"])
        if (self.audience != "ge-nwp-coordinator"
            or requested["verified_admission_act"] != act
            or any(getattr(self, name) != requested[name] for name in ("enrollment_ref", "incarnation_ref", "authority_process_ref", "storage_custody_ref"))
            or any(not _ref(getattr(self, name)) for name in ("enrollment_evidence_ref", "recording_permission_evidence_ref", "custody_evidence_ref"))
            or any(not _digest_value(getattr(self, name)) for name in ("enrollment_evidence_digest", "recording_permission_evidence_digest", "custody_evidence_digest"))
            or any(type(getattr(self, name)) is not bool for name in ("recording_permitted", "disclosure_permitted", "original_custody", "old_execution_excluded"))
            or not self.original_custody
            or not (self.disclosure_permitted if disclosure else self.recording_permitted)):
            raise ValueError("admission authority unavailable")
        return requested


def _build_family(command: ScopeAdmissionCommandV1, source: ArtificialAdmissionSourceV1, recorded_at: str) -> tuple[dict[str, object], ...]:
    if not _time(recorded_at):
        raise ValueError("invalid recording time")
    value = source.checked_for(command, disclosure=False)
    act = value["verified_admission_act"]
    fact = value["expected_admission_fact"]
    assert type(act) is dict and type(fact) is dict
    basis: dict[str, object] = {
        "schema_id": _PREFIX + "scope-admission-recording-basis.v1",
        "operation_ref": value["operation_ref"], "command_digest": value["command_digest"],
        "act_projection_digest": act["projection_digest"],
        "admission_fact_ref": fact["admission_fact_ref"], "admission_fact_digest": fact["admission_fact_digest"],
        **{name: value[name] for name in ("enrollment_ref", "incarnation_ref", "authority_process_ref", "storage_custody_ref")},
        **{name: getattr(source, name) for name in ("enrollment_evidence_ref", "enrollment_evidence_digest", "recording_permission_evidence_ref", "recording_permission_evidence_digest", "custody_evidence_ref", "custody_evidence_digest")},
        "recorded_at": recorded_at,
    }
    basis["basis_digest"] = _self_digest(basis, "basis_digest")
    result: dict[str, object] = {
        "schema_id": _PREFIX + "scope-admission-recording-result.v1",
        "operation_ref": value["operation_ref"], "command_digest": value["command_digest"],
        "admission_fact_ref": fact["admission_fact_ref"], "admission_fact_digest": fact["admission_fact_digest"],
        "basis_digest": basis["basis_digest"], "recorded_at": recorded_at,
        "result_class": "scope_admission_recorded",
    }
    result["result_digest"] = _self_digest(result, "result_digest")
    receipt: dict[str, object] = {
        "schema_id": _PREFIX + "scope-admission-recording-receipt.v1",
        "operation_ref": value["operation_ref"], "command_digest": value["command_digest"],
        "act_ref": act["act_ref"], "act_digest": act["act_digest"],
        "act_projection_digest": act["projection_digest"],
        "admission_fact_ref": fact["admission_fact_ref"], "admission_fact_digest": fact["admission_fact_digest"],
        "basis_digest": basis["basis_digest"], "result_digest": result["result_digest"],
        "recorded_at": recorded_at, "outcome": "committed",
    }
    receipt["receipt_digest"] = _self_digest(receipt, "receipt_digest")
    return act, fact, basis, result, receipt


@dataclass(frozen=True, slots=True, repr=False)
class ScopeAdmissionCommittedV1:
    result: dict[str, object]
    receipt: dict[str, object]


@dataclass(frozen=True, slots=True, repr=False)
class ScopeAdmissionConflictV1:
    reason_code: str

    def __post_init__(self) -> None:
        if self.reason_code not in {
            "scope_admission_provisioning.operation_identity_conflict",
            "scope_admission_provisioning.already_recorded_under_other_operation",
            "scope_admission_provisioning.admission_identity_conflict",
            "scope_admission_provisioning.family_unverifiable",
        }:
            raise ValueError("invalid admission conflict")


@dataclass(frozen=True, slots=True, repr=False)
class ScopeAdmissionRecoveryV1:
    classification: str
    committed: ScopeAdmissionCommittedV1 | None = None

    def __post_init__(self) -> None:
        if self.classification not in {"committed_exact", "definitely_not_committed", "unresolved"}:
            raise ValueError("invalid admission recovery")
        if (self.classification == "committed_exact") != (type(self.committed) is ScopeAdmissionCommittedV1):
            raise ValueError("invalid admission recovery result")
