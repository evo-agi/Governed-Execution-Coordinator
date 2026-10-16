"""Finite synthetic histories for the target-only admission recording owner.

The small checker models logical family observations, not a production writer,
SQL engine, source authenticator, or managed-cell implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / ".docs/rw0-c2-scope-admission-provisioning-contract.md"
PRIVATE = ROOT / ".docs/rw0-c2-private-value-versioning.md"
SCHEMA = "governed-execution.nwp-rw0-c2-"
PROFILE = "rw0-c2-single-realization-proof-v1"
TIME = "2026-10-14T12:00:00Z"
EXPECTED_A_COMMAND_DIGEST = "edbe634aa21135def100d25a182e15a3208770d2fed54a717455fee59f62d72b"
EXPECTED_A_ACT_DIGEST = "cfcd726c87164e89779d0c1b13a080746e21cdf092be6ba11015e9c052634b1c"
EXPECTED_A_FACT_DIGEST = "68303f1a8c16309605c3701d88ad63858b40a6a4ae5b0ad8ee116a44b5d33ae1"
REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]{0,95}\Z", re.ASCII)
RESERVED = ("connector-", "tunnel-", "workspace-", "org-", "organization-", "user-")
ACT_FIELDS = ("schema_id act_ref act_digest lineage_ref scope_ref guard_profile "
              "applicability provenance_ref provenance_digest projection_digest").split()
FACT_FIELDS = ("schema_id admission_fact_ref act_ref act_digest lineage_ref scope_ref "
               "guard_profile applicability provenance_ref provenance_digest "
               "one_shot_ceiling admission_fact_digest").split()
BASIS_FIELDS = ("schema_id operation_ref command_digest act_projection_digest "
                "admission_fact_ref admission_fact_digest enrollment_ref incarnation_ref "
                "authority_process_ref storage_custody_ref enrollment_evidence_ref "
                "enrollment_evidence_digest recording_permission_evidence_ref "
                "recording_permission_evidence_digest custody_evidence_ref "
                "custody_evidence_digest recorded_at basis_digest").split()
RESULT_FIELDS = ("schema_id operation_ref command_digest admission_fact_ref "
                 "admission_fact_digest basis_digest recorded_at result_class "
                 "result_digest").split()
RECEIPT_FIELDS = ("schema_id operation_ref command_digest act_ref act_digest "
                  "act_projection_digest admission_fact_ref admission_fact_digest "
                  "basis_digest result_digest recorded_at outcome receipt_digest").split()
SHARED = ("act_ref", "act_digest", "lineage_ref", "scope_ref", "guard_profile",
          "applicability", "provenance_ref", "provenance_digest")
COMMAND_FIELDS = ("schema_id operation_ref verified_admission_act expected_admission_fact "
                  "enrollment_ref incarnation_ref authority_process_ref "
                  "storage_custody_ref proof_profile_id command_digest").split()


def _digest(schema: str, value: dict[str, object], own: str) -> str:
    raw = {key: part for key, part in value.items() if key != own}
    encoded = json.dumps(raw, ensure_ascii=False, allow_nan=False,
                         sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256((schema + ".identity").encode() + b"\0" + encoded).hexdigest()


def _safe_ref(value: object) -> bool:
    return (type(value) is str and REF.fullmatch(value) is not None
            and not value.lower().startswith(RESERVED))


def _safe_digest(value: object) -> bool:
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}\Z", value) is not None


def _exact_fields(value: object, fields: list[str], *,
                  object_fields: tuple[str, ...] = (),
                  int_fields: tuple[str, ...] = ()) -> bool:
    """Check one closed synthetic v1 object before equality or JSON hashing."""
    if (type(value) is not dict
            or any(type(key) is not str for key in value)
            or set(value) != set(fields)):
        return False
    return all(type(value[name]) is (dict if name in object_fields else
                                     int if name in int_fields else str)
               for name in fields)


def _act_and_fact(letter: str) -> tuple[dict[str, object], dict[str, object]]:
    # Fixture-authored candidate values. Source subjects below are separate,
    # fixed observations; no checker path derives a source from this candidate.
    if letter == "A":
        act_ref, act_digest, lineage, scope, provenance, provenance_digest = (
            "act-A", "ac" * 32, "lineage-A", "scope-A", "policy-proof-A", "b1" * 32)
        fact_ref = "admission-A"
    elif letter == "B":
        act_ref, act_digest, lineage, scope, provenance, provenance_digest = (
            "act-B", "bc" * 32, "lineage-B", "scope-B", "policy-proof-B", "b2" * 32)
        fact_ref = "admission-B"
    elif letter == "C":
        act_ref, act_digest, lineage, scope, provenance, provenance_digest = (
            "act-omega", "cd" * 32, "lineage-cedar", "scope-ivory",
            "policy-proof-saffron", "d3" * 32)
        fact_ref = "admission-cobalt"
    else:
        raise AssertionError("unknown synthetic source")
    act = {
        "schema_id": SCHEMA + "verified-admission-act.v1",
        "act_ref": act_ref, "act_digest": act_digest,
        "lineage_ref": lineage, "scope_ref": scope,
        "guard_profile": "rw0-c2-guard-v1",
        "applicability": "admitted_direct_local_bootstrap",
        "provenance_ref": provenance,
        "provenance_digest": provenance_digest,
    }
    act["projection_digest"] = _digest(str(act["schema_id"]), act, "projection_digest")
    fact = {
        "schema_id": SCHEMA + "scope-admission-fact.v1",
        "admission_fact_ref": fact_ref,
        **{name: act[name] for name in SHARED},
        "one_shot_ceiling": 1,
    }
    fact["admission_fact_digest"] = _digest(str(fact["schema_id"]), fact,
                                               "admission_fact_digest")
    return act, fact


def _command(letter: str = "A", **changes: object) -> dict[str, object]:
    act, fact = _act_and_fact(letter)
    enrollment, incarnation, process, storage = (
        ("enrollment-river", "incarnation-slate", "process-binding-larch",
         "storage-binding-opal") if letter == "C" else
        ("enrollment-" + letter, "incarnation-" + letter,
         "process-binding-" + letter, "storage-binding-" + letter))
    value: dict[str, object] = {
        "schema_id": SCHEMA + "record-scope-admission-command.v1",
        "operation_ref": "admission-operation-" + letter,
        "verified_admission_act": act, "expected_admission_fact": fact,
        "enrollment_ref": enrollment,
        "incarnation_ref": incarnation,
        "authority_process_ref": process,
        "storage_custody_ref": storage,
        "proof_profile_id": PROFILE,
    }
    value.update(changes)
    value["command_digest"] = _digest(str(value["schema_id"]), value,
                                      "command_digest")
    return value


def _valid_command(value: object) -> bool:
    if not _exact_fields(value, COMMAND_FIELDS,
                         object_fields=("verified_admission_act",
                                        "expected_admission_fact")):
        return False
    command = value
    if (command["schema_id"] != SCHEMA + "record-scope-admission-command.v1"
            or command["proof_profile_id"] != PROFILE
            or any(not _safe_ref(command[name]) for name in
                   ("operation_ref", "enrollment_ref", "incarnation_ref",
                    "authority_process_ref", "storage_custody_ref"))):
        return False
    act = command["verified_admission_act"]
    fact = command["expected_admission_fact"]
    if (not _exact_fields(act, ACT_FIELDS)
            or not _exact_fields(fact, FACT_FIELDS,
                                 int_fields=("one_shot_ceiling",))):
        return False
    if (act["schema_id"] != SCHEMA + "verified-admission-act.v1"
            or fact["schema_id"] != SCHEMA + "scope-admission-fact.v1"
            or any(not _safe_ref(act[name]) for name in
                   ("act_ref", "lineage_ref", "scope_ref", "provenance_ref"))
            or not _safe_ref(fact["admission_fact_ref"])
            or any(not _safe_digest(act[name]) for name in
                   ("act_digest", "provenance_digest", "projection_digest"))
            or not _safe_digest(fact["admission_fact_digest"])
            or fact["one_shot_ceiling"] != 1
            or not act["guard_profile"]
            or not act["applicability"]
            or any(fact[name] != act[name] for name in SHARED)):
        return False
    return (_digest(str(act["schema_id"]), act, "projection_digest")
            == act["projection_digest"]
            and _digest(str(fact["schema_id"]), fact, "admission_fact_digest")
            == fact["admission_fact_digest"]
            and _digest(str(command["schema_id"]), command, "command_digest")
            == command["command_digest"])


@dataclass(frozen=True)
class _PolicySubject:
    audience: str
    act_ref: str
    act_digest: str
    projection_digest: str
    lineage_ref: str
    scope_ref: str
    guard_profile: str
    applicability: str
    provenance_ref: str
    provenance_digest: str


@dataclass(frozen=True)
class _EnrollmentSubject:
    lineage_ref: str
    scope_ref: str
    enrollment_ref: str
    incarnation_ref: str


@dataclass(frozen=True)
class _CustodySubject:
    lineage_ref: str
    scope_ref: str
    incarnation_ref: str
    authority_process_ref: str
    storage_custody_ref: str


@dataclass(frozen=True)
class _EvidenceCoords:
    enrollment_ref: str
    enrollment_digest: str
    recording_permission_ref: str
    recording_permission_digest: str
    custody_ref: str
    custody_digest: str


@dataclass(frozen=True)
class _VerifiedSource:
    policy: _PolicySubject
    enrollment: _EnrollmentSubject
    custody: _CustodySubject
    evidence: _EvidenceCoords


_FIRST_EVIDENCE = _EvidenceCoords(
    "enrollment-proof-first", "11" * 32, "policy-proof-first", "22" * 32,
    "custody-proof-first", "33" * 32)
_SOURCE_A = _VerifiedSource(
    _PolicySubject(
        "ge-nwp-coordinator", "act-A", "ac" * 32, EXPECTED_A_ACT_DIGEST,
        "lineage-A", "scope-A", "rw0-c2-guard-v1",
        "admitted_direct_local_bootstrap", "policy-proof-A", "b1" * 32),
    _EnrollmentSubject("lineage-A", "scope-A", "enrollment-A", "incarnation-A"),
    _CustodySubject("lineage-A", "scope-A", "incarnation-A",
                    "process-binding-A", "storage-binding-A"),
    _FIRST_EVIDENCE)
_SOURCE_B = _VerifiedSource(
    _PolicySubject(
        "ge-nwp-coordinator", "act-B", "bc" * 32,
        "bdff9a95984dd081b7282635943bc9c5df89ba636bb098deb2a31374b0a87776",
        "lineage-B", "scope-B", "rw0-c2-guard-v1",
        "admitted_direct_local_bootstrap", "policy-proof-B", "b2" * 32),
    _EnrollmentSubject("lineage-B", "scope-B", "enrollment-B", "incarnation-B"),
    _CustodySubject("lineage-B", "scope-B", "incarnation-B",
                    "process-binding-B", "storage-binding-B"),
    _EvidenceCoords("enrollment-proof-B", "44" * 32, "policy-proof-B-recording",
                    "55" * 32, "custody-proof-B", "66" * 32))
_SOURCE_C = _VerifiedSource(
    _PolicySubject(
        "ge-nwp-coordinator", "act-omega", "cd" * 32,
        "4ac7ee396b84f5698a7cc4e9f6f19d5c19701a38d230bb6368c60c5095ebc68b",
        "lineage-cedar", "scope-ivory", "rw0-c2-guard-v1",
        "admitted_direct_local_bootstrap", "policy-proof-saffron", "d3" * 32),
    _EnrollmentSubject("lineage-cedar", "scope-ivory", "enrollment-river",
                       "incarnation-slate"),
    _CustodySubject("lineage-cedar", "scope-ivory", "incarnation-slate",
                    "process-binding-larch", "storage-binding-opal"),
    _EvidenceCoords("enrollment-proof-copper", "77" * 32,
                    "policy-proof-copper-recording", "88" * 32,
                    "custody-proof-copper", "99" * 32))
_RENEWED_A = replace(
    _SOURCE_A,
    evidence=_EvidenceCoords("enrollment-proof-renewed", "a1" * 32,
                             "policy-proof-renewed", "a2" * 32,
                             "custody-proof-renewed", "a3" * 32))


@dataclass(frozen=True)
class _Premises:
    source: _VerifiedSource = _SOURCE_A  # Fixed independently of the caller's command.
    authenticated_act: bool = True
    original_enrollment: bool = True
    activated_original_incarnation: bool = True
    original_process_and_storage: bool = True
    sole_active_no_foreign: bool = True
    same_original_process: bool = True
    supervisor_live: bool = True
    recording_permission: bool = True
    disclosure_permission: bool = True
    current_source: bool = True
    local_writer_fenced: bool = True
    old_execution_excluded: bool = True


def _valid_source_observation(premises: object) -> bool:
    """Reject noncanonical source scalars before any authority comparison."""
    if type(premises) is not _Premises:
        return False
    try:
        source = premises.source
        if (type(source) is not _VerifiedSource
                or type(source.policy) is not _PolicySubject
                or type(source.enrollment) is not _EnrollmentSubject
                or type(source.custody) is not _CustodySubject
                or type(source.evidence) is not _EvidenceCoords):
            return False
        return (all(type(getattr(source.policy, name)) is str for name in (
            "audience", "act_ref", "act_digest", "projection_digest",
            "lineage_ref", "scope_ref", "guard_profile", "applicability",
            "provenance_ref", "provenance_digest"))
            and all(type(getattr(source.enrollment, name)) is str for name in (
                "lineage_ref", "scope_ref", "enrollment_ref", "incarnation_ref"))
            and all(type(getattr(source.custody, name)) is str for name in (
                "lineage_ref", "scope_ref", "incarnation_ref",
                "authority_process_ref", "storage_custody_ref"))
            and all(type(getattr(source.evidence, name)) is str for name in (
                "enrollment_ref", "enrollment_digest", "recording_permission_ref",
                "recording_permission_digest", "custody_ref", "custody_digest"))
            and all(type(getattr(premises, name)) is bool for name in (
                "authenticated_act", "original_enrollment",
                "activated_original_incarnation", "original_process_and_storage",
                "sole_active_no_foreign", "same_original_process", "supervisor_live",
                "recording_permission", "disclosure_permission", "current_source",
                "local_writer_fenced", "old_execution_excluded")))
    except AttributeError:
        return False


@dataclass(frozen=True)
class _Family:
    command: dict[str, object]
    act: dict[str, object]
    fact: dict[str, object]
    basis: dict[str, object]
    result: dict[str, object]
    receipt: dict[str, object]


def _valid_recording_time(value: object) -> bool:
    if (type(value) is not str or len(value) != 20
            or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
                            r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value) is None):
        return False
    try:
        return (datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").strftime(
            "%Y-%m-%dT%H:%M:%SZ") == value)
    except (ValueError, OverflowError):
        return False


def _family(command: dict[str, object], time: str = TIME,
            evidence: _EvidenceCoords = _FIRST_EVIDENCE) -> _Family:
    act = command["verified_admission_act"]
    fact = command["expected_admission_fact"]
    assert type(act) is dict and type(fact) is dict
    basis: dict[str, object] = {
        "schema_id": SCHEMA + "scope-admission-recording-basis.v1",
        "operation_ref": command["operation_ref"],
        "command_digest": command["command_digest"],
        "act_projection_digest": act["projection_digest"],
        "admission_fact_ref": fact["admission_fact_ref"],
        "admission_fact_digest": fact["admission_fact_digest"],
        **{name: command[name] for name in
           ("enrollment_ref", "incarnation_ref", "authority_process_ref",
            "storage_custody_ref")},
        "enrollment_evidence_ref": evidence.enrollment_ref,
        "enrollment_evidence_digest": evidence.enrollment_digest,
        "recording_permission_evidence_ref": evidence.recording_permission_ref,
        "recording_permission_evidence_digest": evidence.recording_permission_digest,
        "custody_evidence_ref": evidence.custody_ref,
        "custody_evidence_digest": evidence.custody_digest,
        "recorded_at": time,
    }
    basis["basis_digest"] = _digest(str(basis["schema_id"]), basis, "basis_digest")
    result: dict[str, object] = {
        "schema_id": SCHEMA + "scope-admission-recording-result.v1",
        "operation_ref": command["operation_ref"],
        "command_digest": command["command_digest"],
        "admission_fact_ref": fact["admission_fact_ref"],
        "admission_fact_digest": fact["admission_fact_digest"],
        "basis_digest": basis["basis_digest"], "recorded_at": time,
        "result_class": "scope_admission_recorded",
    }
    result["result_digest"] = _digest(str(result["schema_id"]), result, "result_digest")
    receipt: dict[str, object] = {
        "schema_id": SCHEMA + "scope-admission-recording-receipt.v1",
        "operation_ref": command["operation_ref"],
        "command_digest": command["command_digest"],
        "act_ref": act["act_ref"], "act_digest": act["act_digest"],
        "act_projection_digest": act["projection_digest"],
        "admission_fact_ref": fact["admission_fact_ref"],
        "admission_fact_digest": fact["admission_fact_digest"],
        "basis_digest": basis["basis_digest"],
        "result_digest": result["result_digest"],
        "recorded_at": time, "outcome": "committed",
    }
    receipt["receipt_digest"] = _digest(str(receipt["schema_id"]), receipt,
                                        "receipt_digest")
    return _Family(command, act, fact, basis, result, receipt)


def _complete(item: _Family) -> bool:
    try:
        if (type(item) is not _Family
                or not _valid_command(item.command)
                or not _exact_fields(item.act, ACT_FIELDS)
                or not _exact_fields(item.fact, FACT_FIELDS,
                                     int_fields=("one_shot_ceiling",))
                or not _exact_fields(item.basis, BASIS_FIELDS)
                or not _exact_fields(item.result, RESULT_FIELDS)
                or not _exact_fields(item.receipt, RECEIPT_FIELDS)):
            return False
        basis = item.basis
        if not _valid_recording_time(basis["recorded_at"]):
            return False
        evidence = _EvidenceCoords(
            basis["enrollment_evidence_ref"], basis["enrollment_evidence_digest"],
            basis["recording_permission_evidence_ref"],
            basis["recording_permission_evidence_digest"],
            basis["custody_evidence_ref"], basis["custody_evidence_digest"])
        expected = _family(item.command, basis["recorded_at"], evidence)
        # Evidence digests and refs can vary; verify their own closed identity
        # and every dependency rather than compare to one fixed fixture.
        act, fact = item.act, item.fact
        command = item.command
        if (item.act != command["verified_admission_act"]
                or item.fact != command["expected_admission_fact"]
                or basis["schema_id"] != expected.basis["schema_id"]
                or any(basis[name] != command[name] for name in
                       ("operation_ref", "command_digest", "enrollment_ref",
                        "incarnation_ref", "authority_process_ref", "storage_custody_ref"))
                or basis["act_projection_digest"] != act["projection_digest"]
                or basis["admission_fact_ref"] != fact["admission_fact_ref"]
                or basis["admission_fact_digest"] != fact["admission_fact_digest"]
                or any(not _safe_ref(basis[name]) for name in
                       ("enrollment_evidence_ref", "recording_permission_evidence_ref",
                        "custody_evidence_ref"))
                or any(not _safe_digest(basis[name]) for name in
                       ("enrollment_evidence_digest", "recording_permission_evidence_digest",
                        "custody_evidence_digest"))
                or _digest(str(basis["schema_id"]), basis, "basis_digest")
                != basis["basis_digest"]):
            return False
        result = item.result
        receipt = item.receipt
        return (result["schema_id"] == expected.result["schema_id"]
                and receipt["schema_id"] == expected.receipt["schema_id"]
                and result["operation_ref"] == command["operation_ref"]
                and result["command_digest"] == command["command_digest"]
                and result["admission_fact_ref"] == fact["admission_fact_ref"]
                and result["admission_fact_digest"] == fact["admission_fact_digest"]
                and result["basis_digest"] == basis["basis_digest"]
                and result["recorded_at"] == basis["recorded_at"]
                and result["result_class"] == "scope_admission_recorded"
                and _digest(str(result["schema_id"]), result, "result_digest")
                == result["result_digest"]
                and receipt["operation_ref"] == command["operation_ref"]
                and receipt["command_digest"] == command["command_digest"]
                and receipt["act_ref"] == act["act_ref"]
                and receipt["act_digest"] == act["act_digest"]
                and receipt["act_projection_digest"] == act["projection_digest"]
                and receipt["admission_fact_ref"] == fact["admission_fact_ref"]
                and receipt["admission_fact_digest"] == fact["admission_fact_digest"]
                and receipt["basis_digest"] == basis["basis_digest"]
                and receipt["result_digest"] == result["result_digest"]
                and receipt["recorded_at"] == basis["recorded_at"]
                and receipt["outcome"] == "committed"
                and _digest(str(receipt["schema_id"]), receipt, "receipt_digest")
                == receipt["receipt_digest"])
    except (KeyError, TypeError, ValueError):
        return False


@dataclass
class _Store:
    families: list[object] = field(default_factory=list)  # May contain malformed observations.
    fragments: bool = False
    unreadable: bool = False
    downstream_missing_admission: bool = False
    unrelated_programs: tuple[str, ...] = ()
    enrollment_writes: int = 0
    acceptances: int = 0


def _source_boundary(command: dict[str, object], premises: _Premises) -> str | None:
    """Join separately authored policy, enrollment and live-cell subjects."""
    if not _valid_source_observation(premises):
        return "recording_authority_unavailable"
    act = command["verified_admission_act"]
    assert type(act) is dict  # _valid_command has already accepted this shape.
    source = premises.source
    if not premises.authenticated_act or not premises.current_source:
        return "recording_authority_unavailable"
    policy = source.policy
    if (policy.audience != "ge-nwp-coordinator"
            or policy.guard_profile != "rw0-c2-guard-v1"
            or policy.applicability != "admitted_direct_local_bootstrap"
            or (act["act_ref"], act["act_digest"], act["projection_digest"],
                act["lineage_ref"], act["scope_ref"], act["guard_profile"],
                act["applicability"], act["provenance_ref"],
                act["provenance_digest"]) !=
            (policy.act_ref, policy.act_digest, policy.projection_digest,
             policy.lineage_ref, policy.scope_ref, policy.guard_profile,
             policy.applicability, policy.provenance_ref,
             policy.provenance_digest)):
        return "recording_authority_unavailable"
    if not (premises.original_enrollment and premises.activated_original_incarnation
            and premises.original_process_and_storage and premises.sole_active_no_foreign
            and premises.same_original_process and premises.supervisor_live
            and premises.local_writer_fenced):
        return "original_custody_unavailable"
    enrollment = source.enrollment
    custody = source.custody
    if (enrollment.lineage_ref != policy.lineage_ref
            or enrollment.scope_ref != policy.scope_ref
            or custody.lineage_ref != enrollment.lineage_ref
            or custody.scope_ref != enrollment.scope_ref
            or custody.incarnation_ref != enrollment.incarnation_ref
            or command["enrollment_ref"] != enrollment.enrollment_ref
            or command["incarnation_ref"] != enrollment.incarnation_ref
            or command["authority_process_ref"] != custody.authority_process_ref
            or command["storage_custody_ref"] != custody.storage_custody_ref):
        return "original_custody_unavailable"
    return None


def _entry(command: dict[str, object], premises: _Premises) -> str | None:
    if not _valid_command(command):
        return "invalid_input"
    denied = _source_boundary(command, premises)
    if denied is not None:
        return denied
    if not premises.disclosure_permission:
        return "recording_authority_unavailable"
    return None


def _recording_evidence_valid(evidence: _EvidenceCoords) -> bool:
    return (type(evidence) is _EvidenceCoords
            and all(_safe_ref(value) for value in
                    (evidence.enrollment_ref, evidence.recording_permission_ref,
                     evidence.custody_ref))
            and all(_safe_digest(value) for value in
                    (evidence.enrollment_digest, evidence.recording_permission_digest,
                     evidence.custody_digest)))


def _observed_complete(item: object) -> bool:
    return type(item) is _Family and _complete(item)


def _aliases(command: dict[str, object], item: _Family) -> bool:
    act = command["verified_admission_act"]
    fact = command["expected_admission_fact"]
    assert type(act) is dict and type(fact) is dict
    return (item.act["act_ref"] == act["act_ref"]
            or item.act["act_digest"] == act["act_digest"]
            or item.fact["admission_fact_ref"] == fact["admission_fact_ref"]
            or item.fact["lineage_ref"] == fact["lineage_ref"]
            or item.fact["scope_ref"] == fact["scope_ref"])


def _apply(store: _Store, command: dict[str, object], premises: _Premises,
           *, time: str = TIME, commit: str = "success") -> str:
    denied = _entry(command, premises)
    if denied is not None:
        return denied
    if store.fragments or store.unreadable:
        return "family_unverifiable"
    observed = list(store.families)
    if any(not _observed_complete(item) for item in observed):
        return "family_unverifiable"
    matches = [item for item in observed
               if item.receipt["operation_ref"] == command["operation_ref"]]
    if matches:
        if (len(matches) != 1
                or any(other is not matches[0] and _aliases(command, other)
                       for other in observed)):
            return "family_unverifiable"
        if matches[0].receipt["command_digest"] != command["command_digest"]:
            return "operation_identity_conflict"
        return "exact_replay"
    if not premises.recording_permission:
        return "recording_authority_unavailable"
    if not _recording_evidence_valid(premises.source.evidence):
        return "recording_authority_unavailable"
    if store.downstream_missing_admission:
        return "family_unverifiable"
    aliases = [item for item in observed if _aliases(command, item)]
    if aliases:
        act = command["verified_admission_act"]
        assert type(act) is dict
        if any(item.act["act_ref"] == act["act_ref"]
               and item.act["act_digest"] == act["act_digest"] for item in aliases):
            return "already_recorded_under_other_operation"
        return "admission_identity_conflict"
    if commit == "before":
        return "provably_no_write"
    if commit in {"success", "attempted_lost", "cleanup_lost"}:
        if not _valid_recording_time(time):
            return "invalid_input"
        store.families.append(_family(command, time, premises.source.evidence))
        return "scope_admission_recorded" if commit == "success" else "commit_outcome_unknown"
    raise AssertionError("unknown synthetic commit case")


def _readback(store: _Store, command: dict[str, object], premises: _Premises) -> str:
    denied = _entry(command, premises)
    if denied is not None:
        return "unresolved" if denied == "original_custody_unavailable" else denied
    if not premises.old_execution_excluded or store.fragments or store.unreadable:
        return "unresolved"
    observed = list(store.families)
    if any(not _observed_complete(item) for item in observed):
        return "unresolved"
    original = [item for item in observed
                if item.receipt["operation_ref"] == command["operation_ref"]]
    if len(original) > 1:
        return "unresolved"
    if len(original) == 1:
        item = original[0]
        return ("committed_exact" if item.command["command_digest"] == command["command_digest"]
                and not any(other is not item and _aliases(command, other)
                            for other in observed) else "unresolved")
    if store.downstream_missing_admission or any(_aliases(command, item)
                                                 for item in observed):
        return "unresolved"
    return "definitely_not_committed"


class _TrackedFamilies(list[object]):
    """Observe the actual synthetic protected family read/write boundary."""

    def __init__(self, members: list[object]) -> None:
        super().__init__(members)
        self.trace: list[str] = []

    def __iter__(self):  # type: ignore[override]
        self.trace.append("iterate")
        return super().__iter__()

    def __len__(self) -> int:
        self.trace.append("length")
        return super().__len__()

    def __getitem__(self, index):  # type: ignore[override]
        self.trace.append("index")
        return super().__getitem__(index)

    def append(self, item: object) -> None:
        self.trace.append("append")
        super().append(item)


def _resealed_act_command(command: dict[str, object],
                          **changes: object) -> dict[str, object]:
    act = {**command["verified_admission_act"], **changes}
    act["projection_digest"] = _digest(str(act["schema_id"]), act, "projection_digest")
    fact = {**command["expected_admission_fact"],
            **{name: act[name] for name in SHARED}}
    fact["admission_fact_digest"] = _digest(str(fact["schema_id"]), fact,
                                               "admission_fact_digest")
    resealed = {**command, "verified_admission_act": act,
                "expected_admission_fact": fact}
    resealed["command_digest"] = _digest(str(resealed["schema_id"]), resealed,
                                          "command_digest")
    return resealed


def test_owner_inventory_and_preserved_adopted_schemas() -> None:
    owner = OWNER.read_text(encoding="utf-8")
    private = PRIVATE.read_text(encoding="utf-8")
    machine = json.loads(owner.split("<!-- RW0_C2_SCOPE_PROVISIONING_MACHINE_BEGIN -->", 1)[1]
                         .split("```json", 1)[1].split("```", 1)[0])
    adopted = json.loads(private.split("<!-- RW0_C2_PRIVATE_VALUES_MACHINE_BEGIN -->", 1)[1]
                         .split("```json", 1)[1].split("```", 1)[0])
    assert machine["status"] == "accepted_target_not_implemented"
    assert machine["family"] == "record_scope_admission"
    assert machine["proof_profile_id"] == PROFILE
    assert machine["schemas"]["command"] == COMMAND_FIELDS
    assert set(machine["schemas"]) == {"command", "basis", "result", "receipt",
                                       "conflict", "readback_selector", "readback_result"}
    assert machine["schemas"]["readback_selector"] == [
        "schema_id", "original_command", "selector_digest"]
    assert machine["schemas"]["readback_result"] == [
        "schema_id", "classification", "result", "receipt"]
    assert machine["recovery"] == ["committed_exact", "definitely_not_committed", "unresolved"]
    assert machine["collision_roles"] == ["operation_receipt", "admission_fact_identity",
                                          "lineage_occupancy", "scope_occupancy",
                                          "verified_act_binding"]
    assert [row[1:] for row in adopted["schemas"][:2]] == [
        [SCHEMA + "verified-admission-act.v1",
         SCHEMA + "verified-admission-act.v1.identity", "external_safe_evidence", ACT_FIELDS],
        [SCHEMA + "scope-admission-fact.v1",
         SCHEMA + "scope-admission-fact.v1.identity", "immutable_durable_fact", FACT_FIELDS],
    ]
    assert len(adopted["schemas"]) == 11
    assert "development_mutation_receipts" in owner
    assert "No raw credential" in owner
    assert "neither is a C2 acceptance receipt" in owner


def test_fixed_vector_and_two_distinct_positive_sources() -> None:
    a = _command("A")
    b = _command("B")
    c = _command("C")
    assert a["verified_admission_act"]["projection_digest"] == EXPECTED_A_ACT_DIGEST
    assert a["expected_admission_fact"]["admission_fact_digest"] == EXPECTED_A_FACT_DIGEST
    assert a["command_digest"] == EXPECTED_A_COMMAND_DIGEST
    assert EXPECTED_A_COMMAND_DIGEST in OWNER.read_text(encoding="utf-8")
    assert _valid_command(a) and _valid_command(b) and _valid_command(c)
    store = _Store()
    assert _apply(store, a, _Premises()) == "scope_admission_recorded"
    assert _apply(store, b, _Premises(source=_SOURCE_B),
                  time="2026-10-14T12:01:00Z") == "scope_admission_recorded"
    assert _apply(store, c, _Premises(source=_SOURCE_C),
                  time="2026-10-14T12:02:00Z") == "scope_admission_recorded"
    assert len(store.families) == 3
    assert store.families[0].fact != store.families[1].fact
    assert c["enrollment_ref"] == "enrollment-river"  # Opaque, not a suffix rule.
    assert all(_observed_complete(item) for item in store.families)


def test_first_recording_before_program_and_forged_or_empty_local_state() -> None:
    command = _command()
    store = _Store()
    before = (store.unrelated_programs, store.enrollment_writes, store.acceptances)
    assert _apply(store, command, replace(_Premises(), authenticated_act=False)) == "recording_authority_unavailable"
    assert _apply(store, command, replace(_Premises(), original_enrollment=False)) == "original_custody_unavailable"
    assert store.families == []
    assert _apply(store, command, _Premises()) == "scope_admission_recorded"
    assert (store.unrelated_programs, store.enrollment_writes, store.acceptances) == before
    assert len(store.families) == 1
    assert _complete(store.families[0])
    assert not any("program_ref" in member for member in
                   (store.families[0].basis, store.families[0].result,
                    store.families[0].receipt, store.families[0].fact))


def test_replay_uses_original_family_after_fresh_evidence_and_downstream_use() -> None:
    command = _command()
    store = _Store(unrelated_programs=("program-unrelated",))
    assert _apply(store, command, _Premises()) == "scope_admission_recorded"
    original = store.families[0]
    store.unrelated_programs += ("program-later-using-admission",)
    store.acceptances = 1
    assert _apply(store, command, replace(_Premises(), recording_permission=False,
                                           source=_RENEWED_A),
                  time="2026-10-15T00:00:00Z") == "exact_replay"
    assert store.families == [original]
    assert store.families[0].receipt["recorded_at"] == TIME
    assert _readback(store, command, _Premises()) == "committed_exact"
    other_operation = _command(operation_ref="admission-operation-other")
    assert _apply(store, other_operation, _Premises()) == "already_recorded_under_other_operation"
    act, fact = _act_and_fact("A")
    fact["admission_fact_ref"] = "admission-alternate"
    fact["admission_fact_digest"] = _digest(str(fact["schema_id"]), fact,
                                               "admission_fact_digest")
    alternate = _command(operation_ref="admission-operation-alternate",
                         verified_admission_act=act, expected_admission_fact=fact)
    assert _apply(store, alternate, _Premises()) == "already_recorded_under_other_operation"
    assert len(store.families) == 1


@pytest.mark.parametrize("change,expected", [
    ({"operation_ref": "admission-operation-A", "enrollment_ref": "other-enrollment"},
     "original_custody_unavailable"),
    ({"proof_profile_id": "other-profile"}, "invalid_input"),
    ({"incarnation_ref": "other-incarnation"}, "original_custody_unavailable"),
])
def test_same_operation_change_is_no_write(change: dict[str, object], expected: str) -> None:
    store = _Store()
    assert _apply(store, _command(), _Premises()) == "scope_admission_recorded"
    assert _apply(store, _command(**change), _Premises()) == expected
    assert len(store.families) == 1


def test_same_operation_different_valid_fact_command_conflicts() -> None:
    command = _command()
    store = _Store()
    assert _apply(store, command, _Premises()) == "scope_admission_recorded"
    _, fact = _act_and_fact("A")
    fact["admission_fact_ref"] = "admission-alternate"
    fact["admission_fact_digest"] = _digest(str(fact["schema_id"]), fact,
                                               "admission_fact_digest")
    changed = _command(expected_admission_fact=fact)
    assert _valid_command(changed)
    assert _apply(store, changed, _Premises()) == "operation_identity_conflict"
    assert len(store.families) == 1


def test_foreign_alias_and_occupied_target_do_not_mutate() -> None:
    store = _Store()
    assert _apply(store, _command(), _Premises()) == "scope_admission_recorded"
    act, fact = _act_and_fact("B")
    fact["scope_ref"] = "scope-A"
    fact["admission_fact_digest"] = _digest(str(fact["schema_id"]), fact,
                                               "admission_fact_digest")
    foreign_scope = _command("B", expected_admission_fact=fact)
    assert _apply(store, foreign_scope, _Premises()) == "invalid_input"
    act["scope_ref"] = "scope-A"
    act["projection_digest"] = _digest(str(act["schema_id"]), act,
                                        "projection_digest")
    fact["scope_ref"] = "scope-A"
    fact["admission_fact_digest"] = _digest(str(fact["schema_id"]), fact,
                                               "admission_fact_digest")
    alias = _command("B", verified_admission_act=act, expected_admission_fact=fact)
    same_scope_source = replace(
        _SOURCE_B,
        policy=replace(_SOURCE_B.policy, scope_ref="scope-A",
                       projection_digest="a07b339e28835077ac502dc765e630ccbca7559822585b32e4a823971cdde621"),
        enrollment=replace(_SOURCE_B.enrollment, scope_ref="scope-A"),
        custody=replace(_SOURCE_B.custody, scope_ref="scope-A"))
    assert _apply(store, alias, _Premises(source=same_scope_source)) == "admission_identity_conflict"
    act2, fact2 = _act_and_fact("B")
    fact2["admission_fact_ref"] = "admission-A"
    fact2["admission_fact_digest"] = _digest(str(fact2["schema_id"]), fact2,
                                                "admission_fact_digest")
    occupied = _command("B", verified_admission_act=act2, expected_admission_fact=fact2)
    assert _apply(store, occupied, _Premises(source=_SOURCE_B)) == "admission_identity_conflict"
    assert len(store.families) == 1


def test_sequential_duplicate_after_lost_response_replays_one_family() -> None:
    command = _command()
    store = _Store()
    assert _apply(store, command, _Premises(), commit="attempted_lost") == "commit_outcome_unknown"
    assert _apply(store, command, _Premises()) == "exact_replay"
    assert len(store.families) == 1
    assert _readback(store, command, _Premises()) == "committed_exact"
    assert store.enrollment_writes == 0 and store.acceptances == 0


def test_precommit_failure_attempted_commit_and_cleanup_loss() -> None:
    command = _command()
    clean = _Store()
    assert _apply(clean, command, _Premises(), commit="before") == "provably_no_write"
    assert _readback(clean, command, _Premises()) == "definitely_not_committed"
    uncertain = _Store()
    assert _apply(uncertain, command, _Premises(), commit="attempted_lost") == "commit_outcome_unknown"
    assert _readback(uncertain, command, _Premises()) == "committed_exact"
    cleanup = _Store()
    assert _apply(cleanup, command, _Premises(), commit="cleanup_lost") == "commit_outcome_unknown"
    assert _readback(cleanup, command, _Premises()) == "committed_exact"


def test_readback_complete_absent_partial_duplicate_unreadable_and_foreign() -> None:
    command = _command()
    family = _family(command)
    assert _readback(_Store(families=[family]), command, _Premises()) == "committed_exact"
    assert _readback(_Store(), command, _Premises()) == "definitely_not_committed"
    assert _readback(_Store(fragments=True), command, _Premises()) == "unresolved"
    assert _apply(_Store(families=[family], fragments=True), command,
                  _Premises()) == "family_unverifiable"
    assert _readback(_Store(unreadable=True), command, _Premises()) == "unresolved"
    assert _readback(_Store(families=[family, family]), command, _Premises()) == "unresolved"
    assert _readback(_Store(families=[_family(_command("B"))]), command,
                     _Premises()) == "definitely_not_committed"
    assert _readback(_Store(families=[_family(_command(operation_ref="other"))]),
                     command, _Premises()) == "unresolved"
    broken = replace(family, receipt={**family.receipt, "result_digest": "ab" * 32})
    assert _readback(_Store(families=[broken]), command, _Premises()) == "unresolved"
    assert _apply(_Store(downstream_missing_admission=True), command,
                  _Premises()) == "family_unverifiable"


def test_old_execution_exclusion_and_explicit_resubmission() -> None:
    command = _command()
    store = _Store()
    pending = replace(_Premises(), old_execution_excluded=False)
    assert _readback(store, command, pending) == "unresolved"
    assert _readback(store, command, _Premises()) == "definitely_not_committed"
    assert store.families == []  # readback never retries
    assert _apply(store, command, _Premises()) == "scope_admission_recorded"
    assert _apply(store, command, _Premises()) == "exact_replay"
    assert len(store.families) == 1


def test_same_process_fresh_writer_vs_restart_and_restore() -> None:
    command = _command()
    store = _Store()
    same_process_fresh_session = _Premises(local_writer_fenced=True)
    assert _readback(store, command, same_process_fresh_session) == "definitely_not_committed"
    for lost in (replace(_Premises(), same_original_process=False),
                 replace(_Premises(), supervisor_live=False),
                 replace(_Premises(), original_process_and_storage=False)):
        assert _readback(store, command, lost) == "unresolved"
        assert _apply(store, command, lost) == "original_custody_unavailable"
    clone = _Store()  # identical pre-recording local bytes and retained enrollment
    assert _readback(clone, command,
                     replace(_Premises(), original_process_and_storage=False)) == "unresolved"
    assert clone.families == []


def test_revocation_and_disclosure_permission_are_current_separate_checks() -> None:
    command = _command()
    store = _Store()
    assert _apply(store, command, _Premises()) == "scope_admission_recorded"
    original = store.families[0]
    assert _apply(store, command, replace(_Premises(), recording_permission=False,
                                           disclosure_permission=True)) == "exact_replay"
    assert _apply(store, command, replace(_Premises(), recording_permission=False,
                                           disclosure_permission=False)) == "recording_authority_unavailable"
    assert _readback(store, command,
                     replace(_Premises(), disclosure_permission=False)) == "recording_authority_unavailable"
    assert _apply(_Store(), command,
                  replace(_Premises(), recording_permission=False)) == "recording_authority_unavailable"
    assert store.families == [original]


def test_disclosure_denial_precedes_every_protected_family_path(
        monkeypatch: pytest.MonkeyPatch) -> None:
    command = _command()
    exact = _family(command)
    alternate_fact = {**command["expected_admission_fact"],
                      "admission_fact_ref": "admission-alternate"}
    alternate_fact["admission_fact_digest"] = _digest(
        str(alternate_fact["schema_id"]), alternate_fact, "admission_fact_digest")
    conflicting = _family(_command(expected_admission_fact=alternate_fact))
    malformed_original = replace(exact, receipt={**exact.receipt,
                                                  "result_digest": "ab" * 32})
    malformed_orphan = replace(_family(_command("B")), act={})
    cases = (
        ("empty", []),
        ("exact_original", [exact]),
        ("conflicting_original", [conflicting]),
        ("malformed_original", [malformed_original]),
        ("alias", [_family(_command(operation_ref="other-operation"))]),
        ("malformed_orphan", [malformed_orphan]),
    )

    def fail_family_build(*_args: object, **_kwargs: object) -> _Family:
        raise AssertionError("unauthorized entry constructed a recording family")

    monkeypatch.setitem(globals(), "_family", fail_family_build)
    no_disclosure = replace(_Premises(), recording_permission=True,
                            disclosure_permission=False)
    for label, members in cases:
        observed = _TrackedFamilies(members)
        store = _Store(families=observed)
        observed.trace.clear()  # Fixture arrangement is outside the checker call.
        assert _apply(store, command, no_disclosure) == "recording_authority_unavailable", label
        assert observed.trace == [], label
        assert _readback(store, command, no_disclosure) == "recording_authority_unavailable", label
        assert observed.trace == [], label
        assert list.__len__(observed) == len(members)
        assert store.enrollment_writes == 0 and store.acceptances == 0


def test_verified_source_subjects_bind_resealed_candidates_before_read(
        monkeypatch: pytest.MonkeyPatch) -> None:
    command = _command()
    original = _family(command)
    observed = _TrackedFamilies([original])
    store = _Store(families=observed)
    b_under_a = _command(
        "B", enrollment_ref="enrollment-A", incarnation_ref="incarnation-A",
        authority_process_ref="process-binding-A",
        storage_custody_ref="storage-binding-A")
    foreign_scope = _resealed_act_command(command, scope_ref="scope-foreign")
    foreign_act_digest = _resealed_act_command(command, act_digest="fe" * 32)
    wrong_incarnation = _command(incarnation_ref="incarnation-foreign")
    cases = (
        (b_under_a, _Premises(), "recording_authority_unavailable"),
        (foreign_scope, _Premises(), "recording_authority_unavailable"),
        (foreign_act_digest, _Premises(), "recording_authority_unavailable"),
        (wrong_incarnation, _Premises(), "original_custody_unavailable"),
        (command, replace(_Premises(), original_process_and_storage=False),
         "original_custody_unavailable"),
        (command, _Premises(source=replace(
            _SOURCE_A, policy=replace(_SOURCE_A.policy, guard_profile="foreign-profile"))),
         "recording_authority_unavailable"),
        (command, _Premises(source=replace(
            _SOURCE_A, policy=replace(_SOURCE_A.policy, audience="foreign-audience"))),
         "recording_authority_unavailable"),
        (command, _Premises(source=replace(_SOURCE_A, enrollment=_SOURCE_B.enrollment)),
         "original_custody_unavailable"),
    )

    original_builder = _family
    builds: list[_Family] = []

    def track_family_build(*args: object, **kwargs: object) -> _Family:
        built = original_builder(*args, **kwargs)
        builds.append(built)
        return built

    monkeypatch.setitem(globals(), "_family", track_family_build)
    for candidate, premises, expected in cases:
        assert _valid_command(candidate)
        observed.trace.clear()
        builds.clear()
        assert _apply(store, candidate, premises) == expected
        assert observed.trace == []
        assert builds == []
        assert list.__len__(observed) == 1
        assert list.__getitem__(observed, 0) is original
    assert store.enrollment_writes == 0 and store.acceptances == 0


def test_renewed_source_evidence_preserves_history_and_stable_binding() -> None:
    command = _command()
    store = _Store()
    assert _apply(store, command, _Premises()) == "scope_admission_recorded"
    original = store.families[0]
    assert original.basis["enrollment_evidence_ref"] == _FIRST_EVIDENCE.enrollment_ref
    assert _RENEWED_A.evidence != _FIRST_EVIDENCE
    renewed = replace(_Premises(), source=_RENEWED_A,
                      recording_permission=False, disclosure_permission=True)
    assert _apply(store, command, renewed, time="2026-10-15T00:00:00Z") == "exact_replay"
    assert _readback(store, command, renewed) == "committed_exact"
    assert store.families[0] is original
    assert original.receipt["recorded_at"] == TIME
    b_under_a = _command(
        "B", enrollment_ref="enrollment-A", incarnation_ref="incarnation-A",
        authority_process_ref="process-binding-A",
        storage_custody_ref="storage-binding-A")
    assert _valid_command(b_under_a)
    assert _apply(store, b_under_a, renewed) == "recording_authority_unavailable"
    assert store.families == [original]


def test_command_exact_builtin_types_precede_source_and_protected_state(
        monkeypatch: pytest.MonkeyPatch) -> None:
    class StringChild(str):
        pass

    class IntegerChild(int):
        pass

    class ObjectChild(dict):
        pass

    command = _command()
    original = _family(command)
    observed = _TrackedFamilies([original])
    store = _Store(families=observed)
    act = {**command["verified_admission_act"],
           "guard_profile": StringChild("rw0-c2-guard-v1")}
    fact = {**command["expected_admission_fact"],
            "guard_profile": act["guard_profile"]}
    applicability_act = {**command["verified_admission_act"],
                         "applicability": StringChild("admitted_direct_local_bootstrap")}
    applicability_fact = {**command["expected_admission_fact"],
                          "applicability": applicability_act["applicability"]}
    fact_with_integer_child = {**command["expected_admission_fact"],
                               "one_shot_ceiling": IntegerChild(1)}
    cases = (
        {**command, "schema_id": StringChild(command["schema_id"])},
        {**command, "verified_admission_act": act,
         "expected_admission_fact": fact},
        {**command, "verified_admission_act": applicability_act,
         "expected_admission_fact": applicability_fact},
        {**command, "proof_profile_id": StringChild(PROFILE)},
        {**command, "command_digest": StringChild(command["command_digest"])},
        {**command, "expected_admission_fact": fact_with_integer_child},
        {**command, "verified_admission_act": ObjectChild(command["verified_admission_act"])},
    )
    assert type(cases[0]["schema_id"]) is StringChild
    assert type(act["guard_profile"]) is StringChild
    assert type(applicability_act["applicability"]) is StringChild
    assert type(fact_with_integer_child["one_shot_ceiling"]) is IntegerChild
    assert _digest(str(cases[0]["schema_id"]), cases[0], "command_digest") == command["command_digest"]
    assert _digest(str(act["schema_id"]), act, "projection_digest") == act["projection_digest"]
    assert _valid_command(command) and _observed_complete(original)

    def fail_source(*_args: object) -> str:
        raise AssertionError("malformed command reached the source relation")

    def fail_family(*_args: object, **_kwargs: object) -> _Family:
        raise AssertionError("malformed command constructed a family")

    monkeypatch.setitem(globals(), "_source_boundary", fail_source)
    monkeypatch.setitem(globals(), "_family", fail_family)
    for bad in cases:
        assert not _valid_command(bad)
        observed.trace.clear()
        assert _apply(store, bad, _Premises()) == "invalid_input"
        assert _readback(store, bad, _Premises()) == "invalid_input"
        assert observed.trace == []
        assert list.__getitem__(observed, 0) is original
    assert store.enrollment_writes == 0 and store.acceptances == 0


@pytest.mark.parametrize("member,field,value_kind", (
    ("command", "schema_id", "string"),
    ("act", "guard_profile", "string"),
    ("fact", "applicability", "string"),
    ("fact", "one_shot_ceiling", "integer"),
    ("basis", "operation_ref", "string"),
    ("result", "result_class", "string"),
    ("receipt", "outcome", "string"),
    ("receipt", "outcome", "object"),
))
def test_observed_builtin_subclasses_never_complete_or_recover(
        member: str, field: str, value_kind: str) -> None:
    class StringChild(str):
        pass

    class IntegerChild(int):
        pass

    class ObjectChild(dict):
        pass

    command = _command()
    original = _family(command)
    original_member = getattr(original, member)
    if value_kind == "object":
        hostile_member = ObjectChild(original_member)
    else:
        hostile_value = (StringChild(original_member[field]) if value_kind == "string"
                         else IntegerChild(original_member[field]))
        hostile_member = {**original_member, field: hostile_value}
        assert type(hostile_member[field]) is (StringChild if value_kind == "string"
                                               else IntegerChild)
    assert hostile_member == original_member  # Canonical text and digest still match.
    malformed = replace(original, **{member: hostile_member})
    store = _Store(families=[malformed])
    assert _valid_command(command) and _observed_complete(original)
    assert not _observed_complete(malformed)
    assert not _complete(malformed)
    assert _apply(store, command, _Premises()) == "family_unverifiable"
    assert _readback(store, command, _Premises()) == "unresolved"
    assert len(store.families) == 1 and store.families[0] is malformed
    assert store.enrollment_writes == 0 and store.acceptances == 0


@pytest.mark.parametrize("field,foreign", (
    ("guard_profile", "foreign-guard-profile"),
    ("applicability", "foreign-applicability"),
))
def test_resealed_foreign_profile_or_applicability_reaches_source_owner_gate(
        field: str, foreign: str, monkeypatch: pytest.MonkeyPatch) -> None:
    command = _command()
    original = _family(command)
    observed = _TrackedFamilies([original])
    store = _Store(families=observed)
    candidate = _resealed_act_command(command, **{field: foreign})
    act = candidate["verified_admission_act"]
    fact = candidate["expected_admission_fact"]
    assert type(act[field]) is str and act[field] == fact[field] == foreign
    assert candidate["command_digest"] != command["command_digest"]
    assert _valid_command(candidate)  # Foreign exact strings are structurally sound.
    empty = _resealed_act_command(command, **{field: ""})
    assert not _valid_command(empty)
    observed.trace.clear()
    assert _apply(store, empty, _Premises()) == "invalid_input"
    assert observed.trace == []
    assert _apply(store, command, replace(_Premises(), source=_RENEWED_A,
                                          recording_permission=False)) == "exact_replay"
    assert store.families[0] is original

    source_boundary = _source_boundary
    reached: list[_VerifiedSource] = []

    def track_source(candidate_command: dict[str, object], premises: _Premises) -> str | None:
        reached.append(premises.source)
        return source_boundary(candidate_command, premises)

    def fail_family(*_args: object, **_kwargs: object) -> _Family:
        raise AssertionError("foreign request constructed a family")

    monkeypatch.setitem(globals(), "_source_boundary", track_source)
    monkeypatch.setitem(globals(), "_family", fail_family)
    matched_foreign_policy = replace(
        _SOURCE_A.policy, **{field: foreign,
                             "projection_digest": act["projection_digest"]})
    matched_foreign_source = replace(_SOURCE_A, policy=matched_foreign_policy)
    for source in (_SOURCE_A, _RENEWED_A, matched_foreign_source):
        premises = replace(_Premises(), source=source,
                           recording_permission=True, disclosure_permission=True)
        observed.trace.clear()
        before = len(reached)
        assert _apply(store, candidate, premises) == "recording_authority_unavailable"
        assert _readback(store, candidate, premises) == "recording_authority_unavailable"
        assert reached[before:] == [source, source]
        assert observed.trace == []
        assert list.__getitem__(observed, 0) is original
    assert store.enrollment_writes == 0 and store.acceptances == 0


def test_every_source_scalar_has_exact_builtin_type_before_comparison_or_read(
        monkeypatch: pytest.MonkeyPatch) -> None:
    # This fixed inventory is independent of the field lists in the checker.
    source_fields = {
        "policy": ("audience", "act_ref", "act_digest", "projection_digest",
                   "lineage_ref", "scope_ref", "guard_profile", "applicability",
                   "provenance_ref", "provenance_digest"),
        "enrollment": ("lineage_ref", "scope_ref", "enrollment_ref",
                       "incarnation_ref"),
        "custody": ("lineage_ref", "scope_ref", "incarnation_ref",
                    "authority_process_ref", "storage_custody_ref"),
        "evidence": ("enrollment_ref", "enrollment_digest",
                     "recording_permission_ref", "recording_permission_digest",
                     "custody_ref", "custody_digest"),
    }
    boolean_fields = (
        "authenticated_act", "original_enrollment",
        "activated_original_incarnation", "original_process_and_storage",
        "sole_active_no_foreign", "same_original_process", "supervisor_live",
        "recording_permission", "disclosure_permission", "current_source",
        "local_writer_fenced", "old_execution_excluded")
    for role, names in source_fields.items():
        assert tuple(getattr(type(getattr(_SOURCE_A, role)), "__dataclass_fields__")) == names
    assert tuple(_Premises.__dataclass_fields__) == ("source", *boolean_fields)

    class ComparingText(str):
        def __eq__(self, _other: object) -> bool:
            raise AssertionError("source comparison preceded exact-type validation")

        def __ne__(self, _other: object) -> bool:
            raise AssertionError("source comparison preceded exact-type validation")

    command = _command()
    original = _family(command)
    observed = _TrackedFamilies([original])
    store = _Store(families=observed)

    def fail_family(*_args: object, **_kwargs: object) -> _Family:
        raise AssertionError("malformed source constructed a family")

    def fail_time(_value: object) -> bool:
        raise AssertionError("malformed source reached timestamp validation")

    monkeypatch.setitem(globals(), "_family", fail_family)
    monkeypatch.setitem(globals(), "_valid_recording_time", fail_time)
    cases: list[_Premises] = []
    for role, names in source_fields.items():
        subject = getattr(_SOURCE_A, role)
        for name in names:
            changed = replace(subject, **{name: ComparingText(getattr(subject, name))})
            cases.append(_Premises(source=replace(_SOURCE_A, **{role: changed})))
    cases.extend(replace(_Premises(), **{name: 1}) for name in boolean_fields)
    cases.append(_Premises(source=replace(_SOURCE_A, evidence=object())))
    cases.append(_Premises(source=replace(
        _SOURCE_A, policy=object.__new__(_PolicySubject))))
    for premises in cases:
        observed.trace.clear()
        assert _apply(store, command, premises) == "recording_authority_unavailable"
        assert _readback(store, command, premises) == "recording_authority_unavailable"
        assert observed.trace == []
        assert list.__len__(observed) == 1
        assert list.__getitem__(observed, 0) is original


@pytest.mark.parametrize("field,source_text", (
    ("guard_profile", "rw0-c2-guard-v1"),
    ("guard_profile", "foreign-guard-profile"),
    ("applicability", "admitted_direct_local_bootstrap"),
    ("applicability", "foreign-applicability"),
))
def test_hostile_source_profile_and_applicability_cannot_match_owner_literals(
        field: str, source_text: str, monkeypatch: pytest.MonkeyPatch) -> None:
    class FalseInequality(str):
        def __eq__(self, _other: object) -> bool:
            return True

        def __ne__(self, _other: object) -> bool:
            return False

    command = _command()
    original = _family(command)
    observed = _TrackedFamilies([original])
    source = replace(_SOURCE_A, policy=replace(
        _SOURCE_A.policy, **{field: FalseInequality(source_text)}))
    premises = _Premises(source=source)
    store = _Store(families=observed)

    def fail_family(*_args: object, **_kwargs: object) -> _Family:
        raise AssertionError("hostile source constructed a family")

    monkeypatch.setitem(globals(), "_family", fail_family)
    assert _apply(store, command, premises) == "recording_authority_unavailable"
    assert _readback(store, command, premises) == "recording_authority_unavailable"
    assert observed.trace == []
    assert list.__getitem__(observed, 0) is original


@pytest.mark.parametrize("invalid_time", (
    "not-a-timestamp", "2026-10-14T12:00:00.0Z",
    "2026-10-14T12:00:00+00:00", "2026-10-14T12:00:00z",
    " 2026-10-14T12:00:00Z", "2026-10-14T12:00:00Z ",
    "2026-02-30T12:00:00Z", "2026-10-14T25:00:00Z",
))
def test_invalid_fresh_timestamp_stops_before_family_construction_and_append(
        invalid_time: str, monkeypatch: pytest.MonkeyPatch) -> None:
    command = _command()
    observed = _TrackedFamilies([])
    store = _Store(families=observed)
    valid_time = _valid_recording_time
    seen: list[object] = []

    def track_time(value: object) -> bool:
        seen.append(value)
        return valid_time(value)

    def fail_family(*_args: object, **_kwargs: object) -> _Family:
        raise AssertionError("invalid time constructed a family")

    monkeypatch.setitem(globals(), "_valid_recording_time", track_time)
    monkeypatch.setitem(globals(), "_family", fail_family)
    assert _apply(store, command, _Premises(), time=invalid_time) == "invalid_input"
    assert len(seen) == 1 and seen[0] is invalid_time
    assert "iterate" in observed.trace and "append" not in observed.trace
    assert list.__len__(observed) == 0


def test_timestamp_subclass_and_valid_a_b_c_fresh_sources(
        monkeypatch: pytest.MonkeyPatch) -> None:
    class StringChild(str):
        pass

    original_builder = _family
    calls: list[object] = []

    def track_family(command: dict[str, object], time: str = TIME,
                     evidence: _EvidenceCoords = _FIRST_EVIDENCE) -> _Family:
        calls.append(time)
        return original_builder(command, time, evidence)

    monkeypatch.setitem(globals(), "_family", track_family)
    assert not _valid_recording_time(StringChild(TIME))
    for letter, source in (("A", _SOURCE_A), ("B", _SOURCE_B), ("C", _SOURCE_C)):
        bad_members = _TrackedFamilies([])
        assert _apply(_Store(families=bad_members), _command(letter),
                      _Premises(source=source), time=StringChild(TIME)) == "invalid_input"
        assert calls == [] and "append" not in bad_members.trace
        assert list.__len__(bad_members) == 0
        good_members = _TrackedFamilies([])
        assert _apply(_Store(families=good_members), _command(letter),
                      _Premises(source=source), time=TIME) == "scope_admission_recorded"
        assert calls[-1] is TIME and good_members.trace[-1] == "append"
        family = list.__getitem__(good_members, 0)
        assert family.basis["recorded_at"] == TIME
        assert family.result["recorded_at"] == TIME
        assert family.receipt["recorded_at"] == TIME
        calls.clear()


def test_replay_and_readback_ignore_invalid_new_time_and_preserve_original(
        monkeypatch: pytest.MonkeyPatch) -> None:
    command = _command()
    original = _family(command)
    observed = _TrackedFamilies([original])
    store = _Store(families=observed)
    valid_time = _valid_recording_time
    checked: list[object] = []

    def track_time(value: object) -> bool:
        checked.append(value)
        return valid_time(value)

    monkeypatch.setitem(globals(), "_valid_recording_time", track_time)
    premises = replace(_Premises(), source=_RENEWED_A, recording_permission=False)
    assert _apply(store, command, premises, time="not-a-timestamp") == "exact_replay"
    assert _readback(store, command, premises) == "committed_exact"
    assert checked and all(value == TIME for value in checked)
    assert "append" not in observed.trace
    assert list.__len__(observed) == 1 and list.__getitem__(observed, 0) is original
    assert original.basis["recorded_at"] == original.result["recorded_at"] == TIME
    assert original.receipt["recorded_at"] == TIME


def test_disclosure_denial_precedes_invalid_time_and_renewed_fresh_time_gate(
        monkeypatch: pytest.MonkeyPatch) -> None:
    command = _command()
    denied_members = _TrackedFamilies([])
    denied = replace(_Premises(), disclosure_permission=False)
    real_time = _valid_recording_time
    checked: list[object] = []

    def track_time(value: object) -> bool:
        checked.append(value)
        return real_time(value)

    monkeypatch.setitem(globals(), "_valid_recording_time", track_time)
    assert _apply(_Store(families=denied_members), command, denied,
                  time="not-a-timestamp") == "recording_authority_unavailable"
    assert denied_members.trace == [] and checked == []

    renewed_members = _TrackedFamilies([])
    renewed = replace(_Premises(), source=_RENEWED_A)
    assert _apply(_Store(families=renewed_members), command, renewed,
                  time="not-a-timestamp") == "invalid_input"
    assert checked == ["not-a-timestamp"]
    assert "iterate" in renewed_members.trace and "append" not in renewed_members.trace
    assert list.__len__(renewed_members) == 0
    assert _apply(_Store(), command, renewed, time=TIME) == "scope_admission_recorded"


@pytest.mark.parametrize("shape", (
    "missing_act_mapping", "act_wrong_container", "act_missing_field",
    "missing_fact", "missing_basis", "null_family",
))
def test_malformed_observed_orphan_is_unresolved_and_never_repaired(shape: str) -> None:
    command = _command()
    orphan = _family(_command("B"))  # Original A receipt is genuinely absent.
    if shape == "missing_act_mapping":
        observed: object = replace(orphan, act={})
    elif shape == "act_wrong_container":
        observed = replace(orphan, act=["not-an-act"])
    elif shape == "act_missing_field":
        observed = replace(orphan, act={key: value for key, value in orphan.act.items()
                                        if key != "act_ref"})
    elif shape == "missing_fact":
        observed = replace(orphan, fact={})
    elif shape == "missing_basis":
        observed = replace(orphan, basis={})
    else:
        observed = None
    store = _Store(families=[observed])
    assert not store.fragments
    assert _readback(store, command, _Premises()) == "unresolved"
    assert _apply(store, command, _Premises()) == "family_unverifiable"
    assert len(store.families) == 1 and store.families[0] is observed
    assert store.enrollment_writes == 0 and store.acceptances == 0


def test_closed_inputs_and_bool_as_int_fail_before_local_absence() -> None:
    command = _command()
    for bad in (
        {**command, "unexpected": "value"},
        {**command, "expected_admission_fact": {
            **command["expected_admission_fact"], "one_shot_ceiling": True}},
        {**command, "operation_ref": "connector-not-safe"},
        {**command, "command_digest": "00" * 32},
    ):
        assert _apply(_Store(), bad, _Premises()) == "invalid_input"
    with pytest.raises(ValueError):
        json.loads('{"outer":{"operation_ref":"one","operation_ref":"two"}}',
                   object_pairs_hook=lambda pairs: _reject_duplicates(pairs))


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value


def test_direct_counterexamples_to_missing_checks_and_widened_powers() -> None:
    command = _command()
    absent = _Store()
    no_enrollment = replace(_Premises(), original_enrollment=False)
    no_custody = replace(_Premises(), original_process_and_storage=False)
    restarted = replace(_Premises(), same_original_process=False)
    assert [_apply(absent, command, p) for p in (no_enrollment, no_custody, restarted)] == [
        "original_custody_unavailable"] * 3
    assert all(not absent.families for _ in (no_enrollment, no_custody, restarted))
    assert _readback(absent, command,
                     replace(_Premises(), old_execution_excluded=False)) == "unresolved"
    # These tempting shortcuts each return the opposite of the required result.
    assert not absent.families  # local absence would falsely approve all three
    assert _readback(absent, command, _Premises()) == "definitely_not_committed"
    assert _apply(absent, command, _Premises()) == "scope_admission_recorded"
    assert _apply(absent, _command(operation_ref="new-operation"),
                  _Premises()) == "already_recorded_under_other_operation"
    assert absent.enrollment_writes == 0 and absent.acceptances == 0
    assert _apply(absent, command, restarted) == "original_custody_unavailable"


def test_offline_repetition_and_future_owner_nonclaims() -> None:
    offline = (_Store(), _Store())
    for fixture in offline:
        assert fixture.enrollment_writes == 0 and fixture.acceptances == 0
        assert fixture.families == []
    owner = OWNER.read_text(encoding="utf-8")
    for statement in ("RW0-D remains repeatable offline engineering",
                      "supplier conformance gate remains mandatory",
                      "The recovery owner is this provisioner",
                      "never later C2 acceptance", "new enrollment, or new incarnation"):
        assert statement in owner
