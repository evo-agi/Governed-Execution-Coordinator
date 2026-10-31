"""Private normal-profile RW0 terminal values; no I/O or effect authority."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import re
from typing import cast

from ._rw0_c2_progression_contracts import (
    RecordProgressionDecisionCommandV1, _canonical, _strict_json, _walk,
)
from ._rw0_c1_semantic_values import RW0C1AdmitEvidenceResultV1
from ._section41_post_execution_proposal_mutation_contracts import (
    RecordPostExecutionProposalCommandV1,
)

__all__: tuple[str, ...] = ()

PROFILE = "artificial_offline_normal.v1"
PREFIX = "governed-execution.nwp-rw0-terminal-"
COMMAND_SCHEMA = "governed-execution.nwp-record-rw0-terminal-outcome-command.v1"
CONTEXT_SCHEMA = PREFIX + "context.v2"
OUTCOME_SCHEMA = PREFIX + "outcome-value.v2"
RESULT_SCHEMA = PREFIX + "result.v1"
RECEIPT_SCHEMA = PREFIX + "receipt.v1"
GRAPH_PROFILE = PREFIX + "normal-graph.v1"
NORMAL_PAIRS = {
    "candidate_acceptance": "accept",
    "candidate_repair": "repair",
    "attempt_selecting_replan": "replan",
    "program_terminal_reject": "terminal_reject",
    "post_execution_program_block": "block",
}
HEAD_ROLES = ("program", "work", "selection", "effect", "delivery")
EVIDENCE_ROLES = (
    "candidate_capsule", "worker_result", "validation_result",
    "independent_review", "standing_policy", "risk_lane",
    "authority_currentness_attestation", "global_stop", "effect_ceiling",
)
MANIFEST_ROLES = (
    "p0_fact", "phase", "section41_source", "section41_artifact",
    "section41_proposal", *EVIDENCE_ROLES, "c1_rank15", "p1_decision",
    "p1_guarded_result", "p1_generic_receipt",
)
GRAPH_ROLES = (*MANIFEST_ROLES, "terminal_context", "terminal_outcome",
               "terminal_result")
_REF = re.compile(r"[0-9A-Za-z][0-9A-Za-z.-]{0,95}\Z", re.ASCII)
_SHA = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z", re.ASCII)
_RESERVED = ("connector-", "tunnel-", "workspace-", "org-", "organization-", "user-")
_HEAD_FIELDS = ("role", "owner_ref", "revision", "digest")
_STOP_FIELDS = ("ref", "version", "state", "updated_at")
_SELECTOR_FIELDS = (
    "schema_id", "profile", "mutation_ref", "phase_basis_ref",
    "phase_basis_digest", "p1", "section41", "c1_rank15", "reached_owners",
    "heads", "stop", "expected_branch", "expected_outcome", "context_ref",
    "outcome_value_ref", "result_ref", "receipt_ref", "family_route",
    "command_digest",
)
_PREASSIGNED = (
    ("context_ref", PREFIX + "context-ref.v1"),
    ("outcome_value_ref", PREFIX + "outcome-ref.v1"),
    ("result_ref", PREFIX + "result-ref.v1"),
    ("receipt_ref", PREFIX + "receipt-ref.v1"),
    ("family_route", PREFIX + "family-route.v1"),
)


def _safe_ref(value: object) -> str:
    if (type(value) is not str or _REF.fullmatch(value) is None
        or value.lower().startswith(_RESERVED)):
        raise ValueError("invalid terminal reference")
    return value


def _sha(value: object) -> str:
    if type(value) is not str or _SHA.fullmatch(value) is None:
        raise ValueError("invalid terminal digest")
    return value


def _time(value: object) -> str:
    if type(value) is not str or _TIME.fullmatch(value) is None:
        raise ValueError("invalid terminal time")
    try:
        if datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").strftime(
            "%Y-%m-%dT%H:%M:%SZ") != value:
            raise ValueError("invalid terminal time")
    except ValueError:
        raise ValueError("invalid terminal time") from None
    return value


def _exact(value: object, fields: tuple[str, ...]) -> dict[str, object]:
    if type(value) is not dict or set(value) != set(fields) or any(type(k) is not str for k in value):
        raise ValueError("invalid terminal fields")
    return cast(dict[str, object], value)


def _digest(domain: str, value: object) -> str:
    return hashlib.sha256(domain.encode("utf-8") + b"\0" + _canonical(value)).hexdigest()


def _identity_digest(schema: str, mapping: dict[str, object], self_field: str) -> str:
    return _digest(schema + ".identity", {k: v for k, v in mapping.items() if k != self_field})


def _strict_bytes(raw: bytes, *, limit: int = 49152) -> dict[str, object]:
    return _strict_json(raw, ceiling=limit)


def _head(value: object, role: str) -> dict[str, object]:
    if type(role) is not str:
        raise ValueError("invalid terminal role")
    item = _exact(value, _HEAD_FIELDS)
    if (type(item["role"]) is not str or item["role"] != role
        or type(item["revision"]) is not int or not 0 <= item["revision"] < 2**63):
        raise ValueError("invalid terminal head")
    _safe_ref(item["owner_ref"])
    _sha(item["digest"])
    return item


def _stop(value: object) -> dict[str, object]:
    item = _exact(value, _STOP_FIELDS)
    _safe_ref(item["ref"])
    if (type(item["version"]) is not int or not 0 <= item["version"] < 2**63
        or type(item["state"]) is not str or item["state"] not in ("active", "clear")):
        raise ValueError("invalid terminal stop")
    _time(item["updated_at"])
    return item


def _p1_selector(command: RecordProgressionDecisionCommandV1) -> dict[str, object]:
    relation = command.relation.to_mapping()
    basis = command.basis.to_mapping()
    names = (
        "lineage_ref", "scope_ref", "admission_fact_ref", "admission_fact_digest",
        "mutation_ref", "program_ref", "decision_basis_ref", "decision_basis_digest",
        "preassigned_decision_ref", "preassigned_version_ref",
        "preassigned_acceptance_fact_ref", "preassigned_relation_ref",
        "preassigned_guarded_result_ref", "family_route", "relation_digest",
    )
    return {
        "command_digest": command.command_digest,
        "relation": {name: relation[name] for name in names},
        "expected_branch": command.expected_branch,
        "replan_safe_projection": basis["replan_proposal_safe_projection"],
        "basis_ref": basis["basis_ref"], "basis_digest": basis["basis_digest"],
    }


def _section41_selector(command: RecordPostExecutionProposalCommandV1) -> dict[str, object]:
    return {"identity": command.identity_mapping(), "command_digest": command.command_digest}


def _c1_selector(value: RW0C1AdmitEvidenceResultV1) -> dict[str, object]:
    if value.kind_rank != 15:
        raise ValueError("terminal rank-15 selector required")
    mapping = value.safe_projection()
    mapping["disposition"] = "committed"
    mapping.pop("result_digest")
    return mapping


def _owner_manifest(
    p1: RecordProgressionDecisionCommandV1,
    post: RecordPostExecutionProposalCommandV1,
    c1: RW0C1AdmitEvidenceResultV1,
    decision_digest: str,
    guarded_result_digest: str,
    receipt_graph_digest: str,
) -> list[dict[str, str]]:
    relation = p1.relation.to_mapping()
    basis = p1.basis.to_mapping()
    fact = cast(dict[str, object], basis["scope_admission_fact"])
    entries = [
        ("p0_fact", fact["admission_fact_ref"], fact["admission_fact_digest"]),
        ("phase", post.phase_basis_ref, post.phase_basis_digest),
        ("section41_source", post.source_invocation_ref, post.source_invocation_digest),
        ("section41_artifact", post.artifact_ref, post.artifact_binding_digest),
        ("section41_proposal", post.proposal_ref, post.proposal_digest),
    ]
    entries.extend((selector.role, selector.ref, selector.digest)
                   for selector in post.evidence_selectors)
    entries.extend((
        ("c1_rank15", c1.membership_ref, c1.membership_digest),
        ("p1_decision", relation["preassigned_decision_ref"], _sha(decision_digest)),
        ("p1_guarded_result", relation["preassigned_guarded_result_ref"], _sha(guarded_result_digest)),
        ("p1_generic_receipt", relation["mutation_ref"], _sha(receipt_graph_digest)),
    ))
    if tuple(item[0] for item in entries) != MANIFEST_ROLES:
        raise ValueError("invalid terminal owner role inventory")
    return [{"role": role, "ref": _safe_ref(ref), "digest": _sha(digest)}
            for role, ref, digest in entries]


@dataclass(frozen=True, slots=True, repr=False)
class RecordRW0TerminalOutcomeCommandV1:
    """Safe canonical selector plus mandatory original transient owner operands."""

    safe_bytes: bytes = field(repr=False)
    p1_command: RecordProgressionDecisionCommandV1 = field(repr=False)
    section41_command: RecordPostExecutionProposalCommandV1 = field(repr=False)
    c1_rank15: RW0C1AdmitEvidenceResultV1 = field(repr=False)

    @classmethod
    def prepare(cls, *, mutation_ref: str,
                p1_command: RecordProgressionDecisionCommandV1,
                section41_command: RecordPostExecutionProposalCommandV1,
                c1_rank15: RW0C1AdmitEvidenceResultV1,
                heads: tuple[dict[str, object], ...], stop: dict[str, object],
                prior_decision_digest: str, prior_guarded_result_digest: str,
                prior_receipt_graph_digest: str,
                expected_branch: str | None = None,
                expected_outcome: str | None = None,
                ) -> "RecordRW0TerminalOutcomeCommandV1":
        if (type(p1_command) is not RecordProgressionDecisionCommandV1
            or type(section41_command) is not RecordPostExecutionProposalCommandV1
            or type(c1_rank15) is not RW0C1AdmitEvidenceResultV1
            or type(heads) is not tuple or len(heads) != 5):
            raise ValueError("invalid terminal operands")
        relation = p1_command.relation.to_mapping()
        if (section41_command.phase_basis_ref != c1_rank15.phase_basis_ref
            or section41_command.phase_basis_digest != c1_rank15.phase_basis_digest
            or section41_command.c1_membership_ref != c1_rank15.membership_ref
            or section41_command.c1_mutation_ref != c1_rank15.mutation_ref):
            raise ValueError("terminal predecessor selector mismatch")
        if expected_branch is not None and (type(expected_branch) is not str or expected_branch not in NORMAL_PAIRS):
            raise ValueError("unsupported terminal branch")
        if expected_outcome is not None and (type(expected_outcome) is not str or expected_outcome not in NORMAL_PAIRS.values()):
            raise ValueError("unsupported terminal outcome")
        checked_heads = [_head(item, role) for item, role in zip(heads, HEAD_ROLES, strict=True)]
        checked_stop = _stop(stop)
        stable = {
            "schema_id": COMMAND_SCHEMA, "profile": PROFILE,
            "mutation_ref": _safe_ref(mutation_ref),
            "phase_basis_ref": section41_command.phase_basis_ref,
            "phase_basis_digest": section41_command.phase_basis_digest,
            "p1": _p1_selector(p1_command),
            "section41": _section41_selector(section41_command),
            "c1_rank15": _c1_selector(c1_rank15),
            "reached_owners": _owner_manifest(
                p1_command, section41_command, c1_rank15,
                prior_decision_digest, prior_guarded_result_digest,
                prior_receipt_graph_digest),
            "heads": checked_heads, "stop": checked_stop,
        }
        transcript = [[key, stable[key]] for key in stable]
        derived = {name: _digest(domain, transcript)
                   for name, domain in _PREASSIGNED}
        payload = {
            **stable, "expected_branch": expected_branch,
            "expected_outcome": expected_outcome, **derived,
        }
        payload["command_digest"] = _identity_digest(COMMAND_SCHEMA, payload, "command_digest")
        return cls(_canonical(payload), p1_command, section41_command, c1_rank15)

    def __post_init__(self) -> None:
        if (type(self.p1_command) is not RecordProgressionDecisionCommandV1
            or type(self.section41_command) is not RecordPostExecutionProposalCommandV1
            or type(self.c1_rank15) is not RW0C1AdmitEvidenceResultV1):
            raise ValueError("invalid terminal operands")
        payload = _exact(_strict_bytes(self.safe_bytes), _SELECTOR_FIELDS)
        if payload["schema_id"] != COMMAND_SCHEMA or payload["profile"] != PROFILE:
            raise ValueError("unsupported terminal profile")
        _safe_ref(payload["mutation_ref"])
        _safe_ref(payload["phase_basis_ref"])
        _sha(payload["phase_basis_digest"])
        manifest = payload["reached_owners"]
        if type(manifest) is not list or len(manifest) != len(MANIFEST_ROLES):
            raise ValueError("invalid terminal owner manifest")
        for entry, role in zip(manifest, MANIFEST_ROLES, strict=True):
            item = _exact(entry, ("role", "ref", "digest"))
            if item["role"] != role:
                raise ValueError("invalid terminal owner role")
            _safe_ref(item["ref"])
            _sha(item["digest"])
        if (payload["phase_basis_ref"] != self.section41_command.phase_basis_ref
            or payload["phase_basis_digest"] != self.section41_command.phase_basis_digest
            or payload["p1"] != _p1_selector(self.p1_command)
            or payload["section41"] != _section41_selector(self.section41_command)
            or payload["c1_rank15"] != _c1_selector(self.c1_rank15)
            or manifest != _owner_manifest(
                self.p1_command, self.section41_command, self.c1_rank15,
                cast(str, payload["reached_owners"][15]["digest"]),
                cast(str, payload["reached_owners"][16]["digest"]),
                cast(str, payload["reached_owners"][17]["digest"]))):
            raise ValueError("terminal predecessor selector mismatch")
        heads = payload["heads"]
        if type(heads) is not list or len(heads) != 5:
            raise ValueError("invalid terminal heads")
        for item, role in zip(heads, HEAD_ROLES, strict=True):
            _head(item, role)
        _stop(payload["stop"])
        if payload["expected_branch"] is not None and (
            type(payload["expected_branch"]) is not str or payload["expected_branch"] not in NORMAL_PAIRS):
            raise ValueError("unsupported terminal branch")
        if payload["expected_outcome"] is not None and (
            type(payload["expected_outcome"]) is not str or payload["expected_outcome"] not in NORMAL_PAIRS.values()):
            raise ValueError("unsupported terminal outcome")
        stable = {key: payload[key] for key in (
            "schema_id", "profile", "mutation_ref", "phase_basis_ref",
            "phase_basis_digest", "p1", "section41", "c1_rank15",
            "reached_owners", "heads", "stop",
        )}
        transcript = [[key, stable[key]] for key in stable]
        for name, domain in _PREASSIGNED:
            if payload[name] != _digest(domain, transcript):
                raise ValueError("invalid terminal preassignment")
        if payload["command_digest"] != _identity_digest(COMMAND_SCHEMA, payload, "command_digest"):
            raise ValueError("invalid terminal command digest")

    def to_mapping(self) -> dict[str, object]:
        return _exact(_strict_bytes(self.safe_bytes), _SELECTOR_FIELDS)

    @property
    def command_digest(self) -> str:
        return cast(str, self.to_mapping()["command_digest"])


_OUTCOME_FIELDS = (
    "schema_id", "outcome_value_ref", "context_ref", "context_digest",
    "phase_basis_ref", "phase_basis_digest", "branch", "outcome",
    "decision_ref", "decision_digest", "decision_kind", "guarded_result_ref",
    "guarded_result_digest", "p1_receipt_mutation_ref", "p1_receipt_graph_digest",
    "closure_heads", "closure_stop", "evidence_set_ref", "evidence_set_digest",
    "acceptance_fact_ref", "acceptance_fact_digest", "reconciliation_ref",
    "reconciliation_digest", "mismatch_ref", "mismatch_digest",
    "outcome_value_digest",
)


@dataclass(frozen=True, slots=True, repr=False)
class RW0TerminalOutcomeV2:
    canonical_bytes: bytes = field(repr=False)

    @classmethod
    def from_mapping(cls, mapping: dict[str, object]) -> "RW0TerminalOutcomeV2":
        _walk(mapping)
        return cls(_canonical(mapping))

    def __post_init__(self) -> None:
        value = _exact(_strict_bytes(self.canonical_bytes, limit=16384), _OUTCOME_FIELDS)
        if (value["schema_id"] != OUTCOME_SCHEMA or value["branch"] != "normal"
            or type(value["outcome"]) is not str or value["outcome"] not in NORMAL_PAIRS.values()
            or type(value["decision_kind"]) is not str
            or value["decision_kind"] != value["outcome"]):
            raise ValueError("invalid normal terminal shape")
        for name in _OUTCOME_FIELDS:
            if name.endswith("_ref") and name not in (
                "acceptance_fact_ref", "reconciliation_ref", "mismatch_ref"):
                _safe_ref(value[name])
            if name.endswith("_digest") and name not in (
                "acceptance_fact_digest", "reconciliation_digest", "mismatch_digest"):
                _sha(value[name])
        for name in ("reconciliation_ref", "reconciliation_digest", "mismatch_ref", "mismatch_digest"):
            if value[name] is not None:
                raise ValueError("cancel binding in normal terminal")
        if value["outcome"] == "accept":
            _safe_ref(value["acceptance_fact_ref"])
            _sha(value["acceptance_fact_digest"])
        elif value["acceptance_fact_ref"] is not None or value["acceptance_fact_digest"] is not None:
            raise ValueError("unexpected terminal acceptance fact")
        heads = value["closure_heads"]
        if type(heads) is not list or len(heads) != 5:
            raise ValueError("invalid terminal heads")
        for item, role in zip(heads, HEAD_ROLES, strict=True):
            _head(item, role)
        _stop(value["closure_stop"])
        if value["outcome_value_digest"] != _identity_digest(OUTCOME_SCHEMA, value, "outcome_value_digest"):
            raise ValueError("invalid terminal outcome digest")

    def to_mapping(self) -> dict[str, object]:
        return _exact(_strict_bytes(self.canonical_bytes, limit=16384), _OUTCOME_FIELDS)


@dataclass(frozen=True, slots=True)
class TerminalConflictV1:
    reason: str

    def __post_init__(self) -> None:
        if type(self.reason) is not str or self.reason not in ("command_reuse", "stale_currentness", "route_collision",
                               "predecessor_mismatch", "protected_posture_unavailable"):
            raise ValueError("invalid terminal conflict")


@dataclass(frozen=True, slots=True)
class TerminalCommittedV1:
    mutation_ref: str
    command_digest: str
    receipt_ref: str
    outcome_value_ref: str
    outcome: str
    committed_result_digest: str
    recorded_at: str

    def __post_init__(self) -> None:
        for value in (self.mutation_ref, self.receipt_ref, self.outcome_value_ref):
            _safe_ref(value)
        for value in (self.command_digest, self.committed_result_digest):
            _sha(value)
        if type(self.outcome) is not str or self.outcome not in NORMAL_PAIRS.values():
            raise ValueError("invalid terminal outcome")
        _time(self.recorded_at)


@dataclass(frozen=True, slots=True)
class TerminalRecoveryV1:
    classification: str
    committed: TerminalCommittedV1 | None = None

    def __post_init__(self) -> None:
        if (type(self.classification) is not str
            or self.classification not in ("committed_exact", "definitely_not_committed", "unresolved")
            or (self.classification == "committed_exact"
                and type(self.committed) is not TerminalCommittedV1)
            or (self.classification != "committed_exact" and self.committed is not None)):
            raise ValueError("invalid terminal recovery")
