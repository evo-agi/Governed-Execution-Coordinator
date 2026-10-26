"""Closed private artificial-offline RW0-C2 P1 values.

No value here authenticates external policy, authorizes execution, owns a worker,
or grants a durable decision. The guarded transaction verifies supplied values
against independent current owners and is the sole durable decision author.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
from typing import cast

from ._development_program_row_values import (
    development_work_spec_safe_projection_from_work_spec,
)
from ._post_execution_policy_values import (
    PostExecutionStandingPolicyBranchMatrixV1,
    PostExecutionRiskLaneBranchMatrixV1,
)
from ._post_execution_evidence_values import (
    ValidationDispositionV1, IndependentReviewDispositionV1,
)
from ._rw0_c_decision_input_values import (
    RW0CDecisionCurrentSnapshotV1,
    RW0CProposalEvidenceCurrentnessV1,
    RW0CDecisionTimeAuthorityBranchMatrixV1,
    RW0CDecisionTimeGlobalStopBranchMatrixV1,
    RW0CDecisionTimeSourceEffectCeilingBranchMatrixV1,
    RW0CRecommendationConsistencyEvaluationV1,
)
from ._section41_post_execution_proposal_family_projection import (
    Section41PostExecutionProposalFamilyProjectionV2,
)
from ._rw0_c2_scope_admission_contracts import (
    _canonical as _p0_canonical,
    _check_act_and_fact,
    _digest_value,
    _pairs,
    _ref,
    _time,
)
from ._worker_execution_semantic_values import WorkSpecV1, _AUTHORIZED_PATHS

__all__: tuple[str, ...] = ()

_PREFIX = "governed-execution.nwp-rw0-c2-"
_BASIS_SCHEMA_V1 = _PREFIX + "decision-basis.v1"
_BASIS_SCHEMA = _PREFIX + "decision-basis.v2"
_GUARD_SCHEMA = _PREFIX + "bootstrap-guard-evidence.v1"
_REPLAN_SCHEMA = _PREFIX + "cognitive-replan-safe-projection.v1"
_TEMPLATE_SCHEMA = _PREFIX + "cognitive-replan-work-spec-template.v1"
_TEMPLATE_SAFE_SCHEMA = _PREFIX + "cognitive-replan-work-spec-template-safe.v1"
_RELATION_SCHEMA = _PREFIX + "admitted-command-relation.v1"
_COMMAND_SCHEMA = "governed-execution.nwp-record-development-progression-decision-command.v1"
_BRANCHES = (
    "candidate_acceptance", "candidate_repair", "attempt_selecting_replan",
    "program_terminal_reject", "post_execution_program_block",
)
_BASIS_FIELDS_V1 = (
    "schema_id", "basis_ref", "verified_admission_act", "scope_admission_fact",
    "decision_current_snapshot", "proposal_family_projection",
    "proposal_evidence_currentness", "standing_policy_branch_matrix",
    "risk_lane_branch_matrix", "decision_time_authority_branch_matrix",
    "decision_time_global_stop_branch_matrix",
    "decision_time_source_effect_ceiling_branch_matrix",
    "historical_continuity_basis_ref", "historical_continuity_basis_digest",
    "historical_sole_active_basis_ref", "historical_sole_active_basis_digest",
    "bootstrap_guard_evidence", "recommendation_consistency_evaluation",
    "replan_proposal_safe_projection", "captured_at", "basis_digest",
)
_BASIS_FIELDS = (_BASIS_FIELDS_V1[:-2] + (
    "validation_disposition", "independent_review_disposition",
) + _BASIS_FIELDS_V1[-2:])
_NESTED = {
    "decision_current_snapshot": RW0CDecisionCurrentSnapshotV1,
    "proposal_family_projection": Section41PostExecutionProposalFamilyProjectionV2,
    "proposal_evidence_currentness": RW0CProposalEvidenceCurrentnessV1,
    "standing_policy_branch_matrix": PostExecutionStandingPolicyBranchMatrixV1,
    "risk_lane_branch_matrix": PostExecutionRiskLaneBranchMatrixV1,
    "decision_time_authority_branch_matrix": RW0CDecisionTimeAuthorityBranchMatrixV1,
    "decision_time_global_stop_branch_matrix": RW0CDecisionTimeGlobalStopBranchMatrixV1,
    "decision_time_source_effect_ceiling_branch_matrix": RW0CDecisionTimeSourceEffectCeilingBranchMatrixV1,
    "recommendation_consistency_evaluation": RW0CRecommendationConsistencyEvaluationV1,
}
_GUARD_FIELDS = (
    "schema_id", "lineage_ref", "scope_ref", "admission_fact_ref",
    "admission_fact_digest", "continuity_basis_ref", "continuity_basis_digest",
    "sole_active_basis_ref", "sole_active_basis_digest", "no_foreign_claim",
    "acceptance_exhaustively_unclaimed", "guard_digest",
)
_REPLAN_FIELDS = (
    "schema_id", "source_intent_ref", "source_intent_digest",
    "work_spec_template_safe_projection", "proposal_digest",
)
_TEMPLATE_FIELDS = (
    "schema_id", "program_ref", "work_item_ref", "repository_ref",
    "base_git_object_format", "base_git_oid", "authorized_paths",
    "objective", "requirements", "exclusions",
    "validation_requirement_ref", "review_requirement_ref",
    "privacy_classification", "template_digest",
)
_TEMPLATE_SAFE_FIELDS = (
    "schema_id", "program_ref", "work_item_ref", "repository_ref",
    "base_git_object_format", "base_git_oid", "authorized_paths",
    "validation_requirement_ref", "review_requirement_ref",
    "privacy_classification", "template_digest", "safe_projection_digest",
)
_REPLAN_SUCCESSOR_FIELDS = (
    "command_digest", "program_ref", "current_program_version_ref",
    "current_accepted_intent_revision_ref", "work_item_ref",
    "current_work_item_revision_ref", "source_intent_ref",
    "source_intent_digest", "work_spec_template_digest",
    "preassigned_version_ref",
)
_RELATION_FIELDS = (
    "schema_id", "lineage_ref", "scope_ref", "admission_fact_ref",
    "admission_fact_digest", "guard_profile", "applicability",
    "admission_act_ref", "admission_act_digest", "continuity_basis_ref",
    "continuity_basis_digest", "continuity_source_ref", "continuity_source_digest",
    "sole_active_basis_ref", "sole_active_basis_digest", "sole_active_source_ref",
    "sole_active_source_digest", "mutation_ref", "program_ref", "decision_basis_ref",
    "decision_basis_digest", "expected_head_ref", "expected_head_revision",
    "expected_head_digest", "preassigned_decision_ref", "preassigned_version_ref",
    "preassigned_acceptance_fact_ref", "preassigned_relation_ref",
    "preassigned_guarded_result_ref", "family_route", "relation_digest",
)
_PREASSIGNMENT_FIELDS = (
    "command_profile", "lineage_ref", "scope_ref", "admission_fact_ref",
    "admission_fact_digest", "admission_act_ref", "admission_act_digest",
    "guard_profile", "applicability", "continuity_basis_ref",
    "continuity_basis_digest", "continuity_source_ref", "continuity_source_digest",
    "sole_active_basis_ref", "sole_active_basis_digest", "sole_active_source_ref",
    "sole_active_source_digest", "mutation_ref", "program_ref",
    "decision_basis_ref", "decision_basis_digest", "expected_head_ref",
    "expected_head_revision", "expected_head_digest",
)
_SIBLINGS = (
    ("preassigned_decision_ref", _PREFIX + "preassigned-decision-ref.v1"),
    ("preassigned_version_ref", _PREFIX + "preassigned-resulting-version-ref.v1"),
    ("preassigned_relation_ref", _PREFIX + "preassigned-guarded-relation-ref.v1"),
    ("preassigned_guarded_result_ref", _PREFIX + "preassigned-guarded-result-ref.v1"),
    ("family_route", _PREFIX + "deterministic-family-route.v1"),
    ("preassigned_acceptance_fact_ref", _PREFIX + "bootstrap-acceptance-fact.v1.prospective-ref"),
)
_COMMAND_DIGEST_FIELDS = (
    *_PREASSIGNMENT_FIELDS,
    "preassigned_decision_ref", "preassigned_version_ref",
    "preassigned_acceptance_fact_ref", "preassigned_relation_ref",
    "preassigned_guarded_result_ref", "family_route",
)
_MAX_BASIS_BYTES = 49152  # Closed v2 dispositions fit without a physical ceiling change.
_MAX_DEPTH = 16
_MAX_NODES = 4096
_MAX_LIST = 257
_MAX_STRING_BYTES = 8192


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      sort_keys=True, separators=(",", ":")).encode("utf-8")


def _ordered_pairs(value: list[tuple[str, object]]) -> bytes:
    return json.dumps([[key, item] for key, item in value], ensure_ascii=False,
                      allow_nan=False, separators=(",", ":")).encode("utf-8")


def _digest(domain: str, value: object, *, ordered: bool = False) -> str:
    preimage = _ordered_pairs(cast(list[tuple[str, object]], value)) if ordered else _canonical(value)
    return hashlib.sha256(domain.encode("utf-8") + b"\0" + preimage).hexdigest()


def _self_digest(value: dict[str, object], own: str) -> str:
    schema = value.get("schema_id")
    if type(schema) is not str:
        raise ValueError("invalid P1 schema")
    return _digest(schema + ".identity", {k: v for k, v in value.items() if k != own})


def _exact(value: object, fields: tuple[str, ...]) -> dict[str, object]:
    if type(value) is not dict or set(value) != set(fields) or any(type(k) is not str for k in value):
        raise ValueError("invalid P1 fields")
    return value


def _walk(value: object, depth: int = 0, budget: list[int] | None = None) -> None:
    if budget is None:
        budget = [_MAX_NODES]
    budget[0] -= 1
    if budget[0] < 0 or depth > _MAX_DEPTH:
        raise ValueError("P1 value limit")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if not -(2**63) <= value < 2**63:
            raise ValueError("P1 integer limit")
        return
    if type(value) is str:
        if len(value.encode("utf-8")) > _MAX_STRING_BYTES:
            raise ValueError("P1 string limit")
        return
    if type(value) is list:
        if len(value) > _MAX_LIST:
            raise ValueError("P1 list limit")
        for item in value:
            _walk(item, depth + 1, budget)
        return
    if type(value) is dict:
        if len(value) > _MAX_LIST:
            raise ValueError("P1 map limit")
        for key, item in value.items():
            if type(key) is not str or len(key.encode("utf-8")) > 128:
                raise ValueError("P1 key limit")
            _walk(item, depth + 1, budget)
        return
    raise ValueError("invalid P1 recursive type")


def _strict_json(raw: bytes, *, ceiling: int = _MAX_BASIS_BYTES) -> dict[str, object]:
    if type(raw) is not bytes or not 1 <= len(raw) <= ceiling:
        raise ValueError("invalid P1 JSON size")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    _walk(value)
    if type(value) is not dict or _canonical(value) != raw:
        raise ValueError("noncanonical P1 JSON")
    return value


def _guard_mapping(value: object) -> dict[str, object]:
    guard = _exact(value, _GUARD_FIELDS)
    if (guard["schema_id"] != _GUARD_SCHEMA
        or any(not _ref(guard[name]) for name in (
            "lineage_ref", "scope_ref", "admission_fact_ref", "continuity_basis_ref",
            "sole_active_basis_ref"))
        or any(not _digest_value(guard[name]) for name in (
            "admission_fact_digest", "continuity_basis_digest", "sole_active_basis_digest",
            "guard_digest"))
        or guard["no_foreign_claim"] is not True
        or not (guard["acceptance_exhaustively_unclaimed"] is None
                or guard["acceptance_exhaustively_unclaimed"] is True)
        or _self_digest(guard, "guard_digest") != guard["guard_digest"]):
        raise ValueError("invalid P1 guard evidence")
    return guard


def _replan_mapping(value: object) -> dict[str, object]:
    projection = _exact(value, _REPLAN_FIELDS)
    if (projection["schema_id"] != _REPLAN_SCHEMA
        or not _ref(projection["source_intent_ref"])
        or any(not _digest_value(projection[name]) for name in (
            "source_intent_digest", "proposal_digest"))
        or type(projection["work_spec_template_safe_projection"]) is not dict
        or _self_digest(projection, "proposal_digest") != projection["proposal_digest"]):
        raise ValueError("invalid P1 replan projection")
    _template_safe_mapping(projection["work_spec_template_safe_projection"])
    return projection


def _private_text(value: object) -> bool:
    return (type(value) is str and 1 <= len(value) <= 512
            and all(ord(char) >= 32 and ord(char) != 127 for char in value))


def _private_text_array(value: object) -> bool:
    return (type(value) is list and 1 <= len(value) <= 32
            and all(_private_text(item) for item in value)
            and len(value) == len(set(value)))


def _template_mapping(value: object) -> dict[str, object]:
    template = _exact(value, _TEMPLATE_FIELDS)
    if (template["schema_id"] != _TEMPLATE_SCHEMA
        or any(not _ref(template[name]) for name in (
            "program_ref", "work_item_ref", "repository_ref",
            "validation_requirement_ref", "review_requirement_ref"))
        or template["base_git_object_format"] != "sha1"
        or type(template["base_git_oid"]) is not str
        or len(template["base_git_oid"]) != 40
        or any(char not in "0123456789abcdef" for char in template["base_git_oid"])
        or type(template["authorized_paths"]) is not list
        or any(type(path) is not str for path in template["authorized_paths"])
        or tuple(template["authorized_paths"]) != _AUTHORIZED_PATHS
        or not _private_text(template["objective"])
        or not _private_text_array(template["requirements"])
        or not _private_text_array(template["exclusions"])
        or template["privacy_classification"] != "private_work_spec"
        or not _digest_value(template["template_digest"])
        or _self_digest(template, "template_digest") != template["template_digest"]):
        raise ValueError("invalid P1 replan template")
    return template


def _template_safe_mapping(value: object) -> dict[str, object]:
    safe = _exact(value, _TEMPLATE_SAFE_FIELDS)
    if (safe["schema_id"] != _TEMPLATE_SAFE_SCHEMA
        or any(not _ref(safe[name]) for name in (
            "program_ref", "work_item_ref", "repository_ref",
            "validation_requirement_ref", "review_requirement_ref"))
        or safe["base_git_object_format"] != "sha1"
        or type(safe["base_git_oid"]) is not str or len(safe["base_git_oid"]) != 40
        or any(char not in "0123456789abcdef" for char in safe["base_git_oid"])
        or type(safe["authorized_paths"]) is not list
        or any(type(path) is not str for path in safe["authorized_paths"])
        or tuple(safe["authorized_paths"]) != _AUTHORIZED_PATHS
        or safe["privacy_classification"] != "private_work_spec"
        or not _digest_value(safe["template_digest"])
        or not _digest_value(safe["safe_projection_digest"])
        or _self_digest(safe, "safe_projection_digest") != safe["safe_projection_digest"]):
        raise ValueError("invalid P1 replan template projection")
    return safe


def _ordered_source_mapping(value: object, value_type: type[object]) -> dict[str, object]:
    """Restore source-owned field order after canonical sorted-key JSON parsing."""
    fields = getattr(value_type, "_FIELDS", None)
    nested = getattr(value_type, "_NESTED", None)
    if type(fields) is not tuple or type(nested) is not dict:
        raise ValueError("invalid P1 source type")
    raw = _exact(value, fields)
    ordered = {name: raw[name] for name in fields}
    for name, child_type in nested.items():
        children = raw[name]
        if type(children) is not list:
            raise ValueError("invalid P1 source children")
        ordered[name] = [_ordered_source_mapping(item, child_type) for item in children]
    return ordered


@dataclass(frozen=True, slots=True, repr=False)
class CognitiveReplanWorkSpecTemplateV1:
    canonical_bytes: bytes = field(repr=False)

    @classmethod
    def from_mapping(cls, value: dict[str, object]) -> "CognitiveReplanWorkSpecTemplateV1":
        return cls.from_json(_canonical(value))

    @classmethod
    def from_json(cls, raw: bytes) -> "CognitiveReplanWorkSpecTemplateV1":
        value = _strict_json(raw, ceiling=16384)
        _template_mapping(value)
        return cls(raw)

    def to_mapping(self) -> dict[str, object]:
        return _template_mapping(_strict_json(self.canonical_bytes, ceiling=16384))

    @property
    def digest(self) -> str:
        return cast(str, self.to_mapping()["template_digest"])

    def safe_projection(self) -> dict[str, object]:
        value = self.to_mapping()
        safe = {
            name: (_TEMPLATE_SAFE_SCHEMA if name == "schema_id" else value[name])
            for name in _TEMPLATE_SAFE_FIELDS[:-1]
        }
        safe["safe_projection_digest"] = _self_digest(safe, "safe_projection_digest")
        return _template_safe_mapping(safe)


@dataclass(frozen=True, slots=True, repr=False)
class CognitiveReplanProposalV1:
    source_intent_ref: str
    source_intent_digest: str
    work_spec_template: CognitiveReplanWorkSpecTemplateV1 = field(repr=False)

    def __post_init__(self) -> None:
        if (not _ref(self.source_intent_ref)
            or not _digest_value(self.source_intent_digest)
            or type(self.work_spec_template) is not CognitiveReplanWorkSpecTemplateV1):
            raise ValueError("invalid transient replan proposal")
        self.safe_projection()

    def safe_projection(self) -> dict[str, object]:
        result: dict[str, object] = {
            "schema_id": _REPLAN_SCHEMA,
            "source_intent_ref": self.source_intent_ref,
            "source_intent_digest": self.source_intent_digest,
            "work_spec_template_safe_projection": self.work_spec_template.safe_projection(),
        }
        result["proposal_digest"] = _self_digest(result, "proposal_digest")
        return _replan_mapping(_strict_json(_canonical(result), ceiling=16384))


def derive_replan_durable_refs(
    *, command_digest: str, program_ref: str, current_program_version_ref: str,
    current_accepted_intent_revision_ref: str, work_item_ref: str,
    current_work_item_revision_ref: str, source_intent_ref: str,
    source_intent_digest: str, work_spec_template_digest: str,
    preassigned_version_ref: str,
) -> tuple[str, str, str]:
    """Derive three independent post-command siblings from one ordered transcript."""
    values = locals()
    if (any(not _digest_value(values[name]) for name in (
            "command_digest", "source_intent_digest", "work_spec_template_digest"))
        or any(not _ref(values[name]) for name in _REPLAN_SUCCESSOR_FIELDS
               if name not in ("command_digest", "source_intent_digest",
                               "work_spec_template_digest"))):
        raise ValueError("invalid P1 replan successor transcript")
    transcript = [(name, values[name]) for name in _REPLAN_SUCCESSOR_FIELDS]
    return tuple(_digest(_PREFIX + domain, transcript, ordered=True) for domain in (
        "replan-accepted-intent-revision-ref.v1",
        "replan-work-item-revision-ref.v1",
        "replan-work-spec-ref.v1",
    ))


def bind_replan_work_spec(
    template: CognitiveReplanWorkSpecTemplateV1, *, work_spec_ref: str,
    program_version_ref: str, accepted_intent_revision_ref: str,
    work_item_revision_ref: str,
) -> WorkSpecV1:
    """Bind version-neutral private content to Coordinator-derived 0002 refs."""
    if (type(template) is not CognitiveReplanWorkSpecTemplateV1
        or any(not _ref(value) for value in (
            work_spec_ref, program_version_ref, accepted_intent_revision_ref,
            work_item_revision_ref))):
        raise ValueError("invalid P1 final WorkSpec binding")
    value = template.to_mapping()
    final = WorkSpecV1.create(
        work_spec_ref=work_spec_ref,
        program_ref=cast(str, value["program_ref"]),
        program_version_ref=program_version_ref,
        accepted_intent_revision_ref=accepted_intent_revision_ref,
        work_item_ref=cast(str, value["work_item_ref"]),
        work_item_revision_ref=work_item_revision_ref,
        repository_ref=cast(str, value["repository_ref"]),
        base_git_oid=cast(str, value["base_git_oid"]),
        authorized_paths=cast(list[str], value["authorized_paths"]),
        objective=cast(str, value["objective"]),
        requirements=cast(list[str], value["requirements"]),
        exclusions=cast(list[str], value["exclusions"]),
        validation_requirement_ref=cast(str, value["validation_requirement_ref"]),
        review_requirement_ref=cast(str, value["review_requirement_ref"]),
    )
    bound = final.to_mapping()
    for name in _TEMPLATE_FIELDS[1:-1]:
        if name in bound and bound[name] != value[name]:
            raise ValueError("inconsistent P1 final WorkSpec")
    if (bound["work_spec_ref"] != work_spec_ref
        or bound["program_version_ref"] != program_version_ref
        or bound["accepted_intent_revision_ref"] != accepted_intent_revision_ref
        or bound["work_item_revision_ref"] != work_item_revision_ref):
        raise ValueError("inconsistent P1 final WorkSpec refs")
    development_work_spec_safe_projection_from_work_spec(work_spec=final)
    return final


def _require_bound_replan_work_spec(
    template: CognitiveReplanWorkSpecTemplateV1, *, candidate: WorkSpecV1,
    work_spec_ref: str, program_version_ref: str,
    accepted_intent_revision_ref: str, work_item_revision_ref: str,
) -> None:
    """Reject detached final values during plan verification and readback."""
    if type(candidate) is not WorkSpecV1:
        raise ValueError("invalid P1 final WorkSpec candidate")
    expected = bind_replan_work_spec(
        template, work_spec_ref=work_spec_ref,
        program_version_ref=program_version_ref,
        accepted_intent_revision_ref=accepted_intent_revision_ref,
        work_item_revision_ref=work_item_revision_ref,
    )
    if candidate.to_mapping() != expected.to_mapping():
        raise ValueError("detached P1 final WorkSpec")


def _typed_basis_dispositions(
    basis: dict[str, object],
) -> tuple[ValidationDispositionV1, IndependentReviewDispositionV1]:
    snapshot = cast(dict[str, object], basis["decision_current_snapshot"])
    values: list[object] = []
    for name, role, value_type in (
        ("validation_disposition", "validation", ValidationDispositionV1),
        ("independent_review_disposition", "review", IndependentReviewDispositionV1),
    ):
        raw = basis[name]
        if type(raw) is not dict:
            raise ValueError("invalid P1 basis disposition")
        typed = value_type.from_mapping(_ordered_source_mapping(raw, value_type))
        observed = typed.to_mapping()
        source = next((item for item in snapshot["external_sources"]
                       if item["role"] == role), None)
        if (source is None or source["source_available"] is not True
            or any(observed[key] != snapshot[key] for key in (
                "program_ref", "program_version_ref", "accepted_intent_revision_ref",
                "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
                "candidate_ref", "attempt_fence_ref", "attempt_fence_digest"))
            or observed["source_observation_schema_id"] != source["source_schema_id"]
            or observed["source_observation_ref"] != source["source_ref"]
            or observed["source_observation_digest"] != source["source_digest"]):
            raise ValueError("inconsistent P1 basis disposition")
        values.append(typed)
    return cast(tuple[ValidationDispositionV1, IndependentReviewDispositionV1],
                tuple(values))


def _basis_mapping(value: object, *, predecessor: bool = False) -> dict[str, object]:
    basis = _exact(value, _BASIS_FIELDS_V1 if predecessor else _BASIS_FIELDS)
    if (basis["schema_id"] != (_BASIS_SCHEMA_V1 if predecessor else _BASIS_SCHEMA)
        or not _ref(basis["basis_ref"])
        or not _time(basis["captured_at"])
        or any(not _ref(basis[name]) for name in (
            "historical_continuity_basis_ref", "historical_sole_active_basis_ref"))
        or any(not _digest_value(basis[name]) for name in (
            "historical_continuity_basis_digest", "historical_sole_active_basis_digest",
            "basis_digest"))):
        raise ValueError("invalid P1 basis scalar")
    _check_act_and_fact(basis["verified_admission_act"], basis["scope_admission_fact"])
    guard = _guard_mapping(basis["bootstrap_guard_evidence"])
    if (guard["lineage_ref"] != basis["scope_admission_fact"]["lineage_ref"]
        or guard["scope_ref"] != basis["scope_admission_fact"]["scope_ref"]
        or guard["admission_fact_ref"] != basis["scope_admission_fact"]["admission_fact_ref"]
        or guard["admission_fact_digest"] != basis["scope_admission_fact"]["admission_fact_digest"]
        or guard["continuity_basis_ref"] != basis["historical_continuity_basis_ref"]
        or guard["continuity_basis_digest"] != basis["historical_continuity_basis_digest"]
        or guard["sole_active_basis_ref"] != basis["historical_sole_active_basis_ref"]
        or guard["sole_active_basis_digest"] != basis["historical_sole_active_basis_digest"]):
        raise ValueError("invalid P1 guard relation")
    for name, value_type in _NESTED.items():
        raw = basis[name]
        if type(raw) is not dict:
            raise ValueError("invalid P1 nested value")
        value_type.from_mapping(_ordered_source_mapping(raw, value_type))
    if basis["replan_proposal_safe_projection"] is not None:
        _replan_mapping(basis["replan_proposal_safe_projection"])
    snapshot = cast(dict[str, object], basis["decision_current_snapshot"])
    if not predecessor:
        _typed_basis_dispositions(basis)
    projection = cast(dict[str, object], basis["proposal_family_projection"])
    currentness = cast(dict[str, object], basis["proposal_evidence_currentness"])
    model = cast(dict[str, object], basis["recommendation_consistency_evaluation"])
    policy = cast(dict[str, object], basis["standing_policy_branch_matrix"])
    risk = cast(dict[str, object], basis["risk_lane_branch_matrix"])
    authority = cast(dict[str, object], basis["decision_time_authority_branch_matrix"])
    stop = cast(dict[str, object], basis["decision_time_global_stop_branch_matrix"])
    ceiling = cast(dict[str, object], basis["decision_time_source_effect_ceiling_branch_matrix"])
    if (currentness["proposal_ref"] != projection["proposal_ref"]
        or currentness["proposal_digest"] != projection["proposal_digest"]
        or currentness["snapshot_ref"] != snapshot["snapshot_ref"]
        or currentness["snapshot_digest"] != snapshot["snapshot_digest"]
        or model["proposal_ref"] != projection["proposal_ref"]
        or model["proposal_digest"] != projection["proposal_digest"]
        or model["snapshot_ref"] != snapshot["snapshot_ref"]
        or model["snapshot_digest"] != snapshot["snapshot_digest"]
        or model["proposal_currentness_ref"] != currentness["currentness_ref"]
        or model["proposal_currentness_digest"] != currentness["currentness_digest"]
        or model["model_recommendation"] != projection["recommendation"]
        or policy["program_ref"] != snapshot["program_ref"]
        or risk["program_ref"] != snapshot["program_ref"]
        or any(matrix["snapshot_ref"] != snapshot["snapshot_ref"]
               or matrix["snapshot_digest"] != snapshot["snapshot_digest"]
               for matrix in (authority, stop, ceiling))
        or authority["proposal_ref"] != projection["proposal_ref"]
        or authority["proposal_digest"] != projection["proposal_digest"]
        or stop["global_stop_ref"] != snapshot["global_stop_ref"]
        or stop["global_stop_digest"] != snapshot["global_stop_digest"]):
        raise ValueError("inconsistent P1 basis coordinates")
    if _self_digest(basis, "basis_digest") != basis["basis_digest"]:
        raise ValueError("invalid P1 basis digest")
    _walk(basis)
    if len(_canonical(basis)) > _MAX_BASIS_BYTES:
        raise ValueError("P1 basis too large")
    return basis


@dataclass(frozen=True, slots=True, repr=False)
class DecisionBasisV1:
    canonical_bytes: bytes = field(repr=False)

    @classmethod
    def from_mapping(cls, value: dict[str, object]) -> "DecisionBasisV1":
        return cls.from_json(_canonical(value))

    @classmethod
    def from_json(cls, raw: bytes) -> "DecisionBasisV1":
        value = _strict_json(raw)
        _basis_mapping(value, predecessor=True)
        return cls(raw)

    def to_mapping(self) -> dict[str, object]:
        return _basis_mapping(_strict_json(self.canonical_bytes), predecessor=True)

    @property
    def digest(self) -> str:
        return cast(str, self.to_mapping()["basis_digest"])


@dataclass(frozen=True, slots=True, repr=False)
class DecisionBasisV2:
    canonical_bytes: bytes = field(repr=False)

    @classmethod
    def from_mapping(cls, value: dict[str, object]) -> "DecisionBasisV2":
        _walk(value)
        return cls.from_json(_canonical(value))

    @classmethod
    def from_json(cls, raw: bytes) -> "DecisionBasisV2":
        value = _strict_json(raw)
        _basis_mapping(value)
        return cls(raw)

    def to_mapping(self) -> dict[str, object]:
        return _basis_mapping(_strict_json(self.canonical_bytes))

    @property
    def digest(self) -> str:
        return cast(str, self.to_mapping()["basis_digest"])

    def typed_dispositions(
        self,
    ) -> tuple[ValidationDispositionV1, IndependentReviewDispositionV1]:
        return _typed_basis_dispositions(self.to_mapping())


def _safe_evidence(value: object, *, sole: bool) -> dict[str, object]:
    fields = (
        "schema_id", "basis_ref", "source_ref", "source_digest", "lineage_ref",
        "scope_ref", "authority_epoch_ref", "currentness_ref", "currentness_digest",
    ) + (("active_authority_ref", "sole_active_assertion_ref", "sole_active_assertion_digest") if sole else ()) + (
        "provenance_ref", "provenance_digest", "projection_digest",
    )
    evidence = _exact(value, fields)
    schema = _PREFIX + ("verified-sole-active.v1" if sole else "verified-lineage-continuity.v1")
    if (evidence["schema_id"] != schema
        or any(not _ref(evidence[name]) for name in fields
               if name.endswith("_ref") or name in ("basis_ref", "lineage_ref", "scope_ref"))
        or any(not _digest_value(evidence[name]) for name in fields
               if name.endswith("_digest"))
        or _self_digest(evidence, "projection_digest") != evidence["projection_digest"]):
        raise ValueError("invalid P1 historical source evidence")
    return evidence


@dataclass(frozen=True, slots=True, repr=False)
class ArtificialDecisionGuardSourceV1:
    """Independent task-owned currentness and custody subject for offline proof."""
    continuity_bytes: bytes = field(repr=False)
    sole_active_bytes: bytes = field(repr=False)
    current_at: str
    expires_at: str
    continuity_positive: bool
    sole_active_positive: bool
    no_foreign_claim: bool
    disclosure_permitted: bool
    recording_permitted: bool
    old_execution_excluded: bool
    acceptance_exhaustively_unclaimed: bool | None = None

    def checked_for(self, basis: DecisionBasisV2, *, now: str, write: bool) -> tuple[dict[str, object], dict[str, object]]:
        """Validate universal current posture for recording or disclosure."""
        if (type(basis) is not DecisionBasisV2 or type(write) is not bool
            or not _time(now) or not _time(self.current_at) or not _time(self.expires_at)
            or not self.current_at <= now < self.expires_at
            or any(type(getattr(self, name)) is not bool for name in (
                "continuity_positive", "sole_active_positive", "no_foreign_claim",
                "disclosure_permitted", "recording_permitted", "old_execution_excluded"))
            or (self.acceptance_exhaustively_unclaimed is not None
                and type(self.acceptance_exhaustively_unclaimed) is not bool)
            or not self.continuity_positive or not self.sole_active_positive
            or not self.no_foreign_claim
            or not (self.recording_permitted if write else self.disclosure_permitted)):
            raise ValueError("P1 guard source unavailable")
        continuity = _safe_evidence(_strict_json(self.continuity_bytes), sole=False)
        sole = _safe_evidence(_strict_json(self.sole_active_bytes), sole=True)
        value = basis.to_mapping()
        fact = cast(dict[str, object], value["scope_admission_fact"])
        guard = cast(dict[str, object], value["bootstrap_guard_evidence"])
        if (any(item["lineage_ref"] != fact["lineage_ref"] or item["scope_ref"] != fact["scope_ref"] for item in (continuity, sole))
            or continuity["basis_ref"] != value["historical_continuity_basis_ref"]
            or continuity["projection_digest"] != value["historical_continuity_basis_digest"]
            or sole["basis_ref"] != value["historical_sole_active_basis_ref"]
            or sole["projection_digest"] != value["historical_sole_active_basis_digest"]
            or guard["no_foreign_claim"] is not self.no_foreign_claim):
            raise ValueError("P1 guard source mismatch")
        return continuity, sole

    def checked_acceptance_eligibility_for(self, basis: DecisionBasisV2) -> None:
        """Check only fresh acceptance eligibility after universal admission."""
        if type(basis) is not DecisionBasisV2:
            raise ValueError("invalid P1 acceptance basis")
        guard = cast(dict[str, object], basis.to_mapping()["bootstrap_guard_evidence"])
        if (guard["acceptance_exhaustively_unclaimed"] is not True
            or self.acceptance_exhaustively_unclaimed is not True):
            raise ValueError("P1 acceptance eligibility unavailable")


def _relation_mapping(value: object) -> dict[str, object]:
    relation = _exact(value, _RELATION_FIELDS)
    if (relation["schema_id"] != _RELATION_SCHEMA
        or any(not _ref(relation[name]) for name in _RELATION_FIELDS
               if name.endswith("_ref") or name in ("lineage_ref", "scope_ref", "program_ref", "family_route")
               if name not in ("preassigned_decision_ref", "preassigned_version_ref",
                               "preassigned_acceptance_fact_ref", "preassigned_relation_ref",
                               "preassigned_guarded_result_ref"))
        or any(not _digest_value(relation[name]) for name in _RELATION_FIELDS
               if name.endswith("_digest"))
        or type(relation["expected_head_revision"]) is not int
        or relation["expected_head_revision"] < 0):
        raise ValueError("invalid P1 command relation")
    pairs = [(name, _RELATION_SCHEMA if name == "command_profile" else relation[name]) for name in _PREASSIGNMENT_FIELDS]
    for field, domain in _SIBLINGS:
        if relation[field] != _digest(domain, pairs, ordered=True):
            raise ValueError("invalid P1 preassignment")
    if _self_digest(relation, "relation_digest") != relation["relation_digest"]:
        raise ValueError("invalid P1 relation digest")
    return relation


@dataclass(frozen=True, slots=True, repr=False)
class AdmittedCommandRelationV1:
    canonical_bytes: bytes = field(repr=False)

    @classmethod
    def from_mapping(cls, value: dict[str, object]) -> "AdmittedCommandRelationV1":
        return cls.from_json(_canonical(value))

    @classmethod
    def from_json(cls, raw: bytes) -> "AdmittedCommandRelationV1":
        value = _strict_json(raw, ceiling=16384)
        _relation_mapping(value)
        return cls(raw)

    def to_mapping(self) -> dict[str, object]:
        return _relation_mapping(_strict_json(self.canonical_bytes, ceiling=16384))

    @property
    def command_digest(self) -> str:
        relation = self.to_mapping()
        pairs = [(name, _RELATION_SCHEMA if name == "command_profile" else relation[name])
                 for name in _COMMAND_DIGEST_FIELDS]
        return _digest(_PREFIX + "guarded-command-digest.v1.identity", pairs, ordered=True)


def derive_successor_selection_refs(
    *, command_digest: str, program_ref: str,
    selected_attempt_ref: str, selected_candidate_ref: str, branch: str,
) -> tuple[str, str]:
    """Coordinator-owned branch-specific prospective refs, with no new row."""
    if (not _digest_value(command_digest) or not _ref(program_ref)
        or not _ref(selected_attempt_ref) or not _ref(selected_candidate_ref)
        or branch not in ("candidate_repair", "attempt_selecting_replan")):
        raise ValueError("invalid P1 successor basis")
    preimage = {
        "schema_id": _PREFIX + "prospective-successor-selection.v1",
        "command_digest": command_digest,
        "program_ref": program_ref,
        "selected_attempt_ref": selected_attempt_ref,
        "selected_candidate_ref": selected_candidate_ref,
        "branch": branch,
    }
    return (
        _digest(_PREFIX + "prospective-semantic-attempt-ref.v1", preimage),
        _digest(_PREFIX + "prospective-candidate-ref.v1", preimage),
    )


@dataclass(frozen=True, slots=True, repr=False)
class RecordProgressionDecisionCommandV1:
    relation: AdmittedCommandRelationV1
    basis: DecisionBasisV2
    expected_branch: str | None
    replan_proposal: CognitiveReplanProposalV1 | None = field(repr=False)

    def __post_init__(self) -> None:
        if (type(self.relation) is not AdmittedCommandRelationV1
            or type(self.basis) is not DecisionBasisV2
            or self.expected_branch is not None and (
                type(self.expected_branch) is not str
                or self.expected_branch not in _BRANCHES)
            or self.replan_proposal is not None and type(self.replan_proposal) is not CognitiveReplanProposalV1):
            raise ValueError("invalid P1 command")
        relation = self.relation.to_mapping()
        basis = self.basis.to_mapping()
        fact = cast(dict[str, object], basis["scope_admission_fact"])
        act = cast(dict[str, object], basis["verified_admission_act"])
        if (relation["decision_basis_ref"] != basis["basis_ref"]
            or relation["decision_basis_digest"] != basis["basis_digest"]
            or any(relation[name] != fact[name] for name in (
                "lineage_ref", "scope_ref", "admission_fact_ref", "admission_fact_digest",
                "guard_profile", "applicability"))
            or relation["admission_act_ref"] != act["act_ref"]
            or relation["admission_act_digest"] != act["act_digest"]
            or relation["continuity_basis_ref"] != basis["historical_continuity_basis_ref"]
            or relation["continuity_basis_digest"] != basis["historical_continuity_basis_digest"]
            or relation["sole_active_basis_ref"] != basis["historical_sole_active_basis_ref"]
            or relation["sole_active_basis_digest"] != basis["historical_sole_active_basis_digest"]
            or relation["program_ref"] != basis["decision_current_snapshot"]["program_ref"]):
            raise ValueError("inconsistent P1 command")
        projection = basis["replan_proposal_safe_projection"]
        if self.replan_proposal is None and projection is not None:
            raise ValueError("missing P1 replan proposal")
        if self.replan_proposal is not None and self.replan_proposal.safe_projection() != projection:
            raise ValueError("inconsistent P1 replan proposal")

    @property
    def command_digest(self) -> str:
        """Current exact command identity, including the optimistic assertion."""
        if self.expected_branch is not None and (
            type(self.expected_branch) is not str
            or self.expected_branch not in _BRANCHES
        ):
            raise ValueError("invalid P1 expected branch")
        relation = self.relation.to_mapping()
        pairs = [(name, _RELATION_SCHEMA if name == "command_profile" else relation[name])
                 for name in _COMMAND_DIGEST_FIELDS]
        pairs.append(("expected_branch", self.expected_branch))
        return _digest(_PREFIX + "guarded-command-digest.v2.identity", pairs, ordered=True)


@dataclass(frozen=True, slots=True, repr=False)
class ProgressionDecisionConflictV1:
    reason_code: str

    def __post_init__(self) -> None:
        if self.reason_code not in {
            "required_fact_invalid", "basis_identity_lineage_profile_provenance_conflict",
            "stale_caller_expectation", "mutation_ref_reuse_conflict",
            "preassigned_identity_or_family_route_collision", "matrix_conflict",
            "expected_branch_mismatch", "halt_only_matrix_contract_conflict",
            "bootstrap_acceptance_guard_conflict", "family_unverifiable",
        }:
            raise ValueError("invalid P1 conflict")


@dataclass(frozen=True, slots=True, repr=False)
class ProgressionDecisionCommittedV1:
    mutation_ref: str
    command_digest: str
    decision_ref: str
    program_version_ref: str
    branch: str
    result_digest: str
    receipt_graph_digest: str
    decided_at: str

    def __post_init__(self) -> None:
        if (any(not _ref(getattr(self, name)) for name in (
            "mutation_ref", "decision_ref", "program_version_ref"))
            or any(not _digest_value(getattr(self, name)) for name in (
                "command_digest", "result_digest", "receipt_graph_digest"))
            or self.branch not in _BRANCHES or not _time(self.decided_at)):
            raise ValueError("invalid P1 committed result")


@dataclass(frozen=True, slots=True, repr=False)
class ProgressionDecisionRecoveryV1:
    classification: str
    committed: ProgressionDecisionCommittedV1 | None = None

    def __post_init__(self) -> None:
        if (self.classification not in {"committed_exact", "definitely_not_committed", "unresolved"}
            or (self.classification == "committed_exact") != (type(self.committed) is ProgressionDecisionCommittedV1)):
            raise ValueError("invalid P1 recovery")


@dataclass(frozen=True, slots=True, repr=False)
class ProgressionDecisionReductionV1:
    branch: str
    reason_code: str
    candidate_reason_code: str

    def __post_init__(self) -> None:
        if (self.branch not in _BRANCHES
            or self.reason_code not in {
                "candidate_evidence_conclusively_accepted",
                "candidate_evidence_requires_repair",
                "candidate_evidence_requires_replan",
                "candidate_evidence_terminally_rejected",
                "decision_basis_not_current", "candidate_evidence_nonconclusive",
                "productive_branch_not_permitted",
            }
            or self.candidate_reason_code not in {
                "candidate_evidence_conclusively_accepted",
                "candidate_evidence_requires_repair",
                "candidate_evidence_requires_replan",
                "candidate_evidence_terminally_rejected",
                "candidate_evidence_nonconclusive",
            }):
            raise ValueError("invalid P1 reduction")


_VALIDATION_CLASSES = {
    ("passed", "passed", "not_applicable", "validation_passed"): "accept",
    ("failed", "repairable_failure", "repairable", "validation_failed_repairable"): "repair",
    ("failed", "replan_required", "same_attempt_insufficient", "validation_failed_replan_required"): "replan",
    ("failed", "terminal_failure", "nonrepairable", "validation_failed_terminal"): "terminal",
    ("failed", "unknown", "unknown", "validation_failed_unclassified"): "nonconclusive",
    ("inconclusive", "unknown", "unknown", "validation_inconclusive"): "nonconclusive",
    ("not_run", "not_run", "not_applicable", "validation_not_run"): "nonconclusive",
}
_REVIEW_CLASSES = {
    ("separate", "passed", "passed", "review_passed"): "accept",
    ("separate", "failed", "repair_required", "review_failed_repair_required"): "repair",
    ("separate", "failed", "replan_required", "review_failed_replan_required"): "replan",
    ("separate", "failed", "terminal_reject", "review_failed_terminal_reject"): "terminal",
    ("separate", "failed", "unknown", "review_failed_unclassified"): "nonconclusive",
    ("separate", "inconclusive", "unknown", "review_inconclusive"): "nonconclusive",
    ("not_separate", "passed", "basis_conflict", "review_not_operationally_separate"): "conflict",
    ("unknown", "passed", "unknown", "reviewer_separation_unknown"): "nonconclusive",
    ("conflict", "passed", "basis_conflict", "reviewer_separation_conflict"): "conflict",
}
_CANDIDATE_REASON_BY_CLASS = {
    "accept": "candidate_evidence_conclusively_accepted",
    "repair": "candidate_evidence_requires_repair",
    "replan": "candidate_evidence_requires_replan",
    "terminal": "candidate_evidence_terminally_rejected",
    "nonconclusive": "candidate_evidence_nonconclusive",
}
_CANDIDATE_CLASS_BY_REASON = {
    reason: name for name, reason in _CANDIDATE_REASON_BY_CLASS.items()
}


def derive_candidate_evidence_reason(
    validation: ValidationDispositionV1,
    review: IndependentReviewDispositionV1,
) -> str | ProgressionDecisionConflictV1:
    """Classify only the two exact typed dispositions, without current state."""
    if (type(validation) is not ValidationDispositionV1
        or type(review) is not IndependentReviewDispositionV1):
        return ProgressionDecisionConflictV1("required_fact_invalid")
    try:
        validation_map = validation.to_mapping()
        review_map = review.to_mapping()
        vclass = _VALIDATION_CLASSES.get((validation_map["source_outcome"],
            validation_map["result"], validation_map["repairability"],
            validation_map["reason"]))
        if (validation_map["result"] == "basis_conflict"
            and validation_map["repairability"] == "conflict"
            and validation_map["reason"] == "source_observation_mismatch"):
            vclass = "conflict"
        rclass = _REVIEW_CLASSES.get((review_map["separation_status"],
            review_map["source_outcome"], review_map["result"], review_map["reason"]))
        if rclass is None and review_map["separation_status"] in {
            "not_separate", "unknown", "conflict"
        }:
            override = {
                ("not_separate", "basis_conflict", "review_not_operationally_separate"): "conflict",
                ("unknown", "unknown", "reviewer_separation_unknown"): "nonconclusive",
                ("conflict", "basis_conflict", "reviewer_separation_conflict"): "conflict",
            }
            rclass = override.get((review_map["separation_status"],
                review_map["result"], review_map["reason"]))
        if vclass is None or rclass is None:
            return ProgressionDecisionConflictV1("required_fact_invalid")
        if "conflict" in (vclass, rclass):
            return ProgressionDecisionConflictV1(
                "basis_identity_lineage_profile_provenance_conflict")
        normal = ("nonconclusive" if "nonconclusive" in (vclass, rclass) else
                  max((vclass, rclass), key=("accept", "repair", "replan", "terminal").index))
        return _CANDIDATE_REASON_BY_CLASS[normal]
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return ProgressionDecisionConflictV1("required_fact_invalid")


_MATRIX_ROLES = (
    "standing_policy_branch_matrix", "risk_lane_branch_matrix",
    "decision_time_authority_branch_matrix",
    "decision_time_global_stop_branch_matrix",
    "decision_time_source_effect_ceiling_branch_matrix",
)
_PRODUCTIVE_PERMITS = (
    "policy_permits", "risk_lane_permits", "authority_verified_current",
    "global_stop_clear", "source_effect_within_current_ceilings",
)
_HALT_PERMITS = (
    "halt_only_policy_not_applicable", "halt_only_risk_not_applicable",
    "halt_only_authority_not_applicable", "halt_only_stop_checked",
    "halt_only_ceiling_not_applicable",
)


def derive_progression_branch(
    basis: DecisionBasisV2,
    validation: ValidationDispositionV1,
    review: IndependentReviewDispositionV1,
    *, expected_branch: str | None,
    replan_proposal: CognitiveReplanProposalV1 | None,
) -> ProgressionDecisionReductionV1 | ProgressionDecisionConflictV1:
    """Pure five-branch reducer; V34 is checked only after branch selection."""
    if (type(basis) is not DecisionBasisV2
        or type(validation) is not ValidationDispositionV1
        or type(review) is not IndependentReviewDispositionV1
        or expected_branch is not None and type(expected_branch) is not str):
        return ProgressionDecisionConflictV1("required_fact_invalid")
    try:
        value = basis.to_mapping()
        projection = cast(dict[str, object], value["proposal_family_projection"])
        currentness = cast(dict[str, object], value["proposal_evidence_currentness"])
        embedded_validation, embedded_review = basis.typed_dispositions()
        if (validation.to_mapping() != embedded_validation.to_mapping()
            or review.to_mapping() != embedded_review.to_mapping()):
            return ProgressionDecisionConflictV1(
                "basis_identity_lineage_profile_provenance_conflict")
        candidate_reason = derive_candidate_evidence_reason(
            embedded_validation, embedded_review)
        if type(candidate_reason) is ProgressionDecisionConflictV1:
            return candidate_reason
        if currentness["result"] == "conflict":
            return ProgressionDecisionConflictV1(
                "basis_identity_lineage_profile_provenance_conflict")
        if currentness["result"] not in {"current", "stale", "unknown"}:
            return ProgressionDecisionConflictV1("required_fact_invalid")
        normal = _CANDIDATE_CLASS_BY_REASON[candidate_reason]
        candidate = {
            "accept": "candidate_acceptance", "repair": "candidate_repair",
            "replan": "attempt_selecting_replan", "terminal": "program_terminal_reject",
            "nonconclusive": "post_execution_program_block",
        }[normal]
        matrices = [cast(dict[str, object], value[name]) for name in _MATRIX_ROLES]
        for matrix in matrices:
            entries = matrix["entries"]
            if (type(entries) is not list or len(entries) != 5
                or tuple(item["branch"] for item in entries) != _BRANCHES):
                return ProgressionDecisionConflictV1("required_fact_invalid")
        block_reason: str | None = None
        if currentness["result"] in {"stale", "unknown"}:
            block_reason = "decision_basis_not_current"
        elif normal == "nonconclusive":
            block_reason = "candidate_evidence_nonconclusive"
        if candidate in _BRANCHES[:3]:
            index = _BRANCHES.index(candidate)
            results = []
            for owner, matrix in enumerate(matrices):
                entry = matrix["entries"][index]
                if (entry["applicability"] != "governed"
                    or entry["governed_effect_class"] != "author_candidate"
                    or entry["result"] == "conflict"):
                    return ProgressionDecisionConflictV1("matrix_conflict")
                if entry["result"] == "permit" and entry["reason"] != _PRODUCTIVE_PERMITS[owner]:
                    return ProgressionDecisionConflictV1("matrix_conflict")
                results.append(entry["result"])
            if any(result in {"deny", "unknown"} for result in results) and block_reason is None:
                block_reason = "productive_branch_not_permitted"
        branch = "post_execution_program_block" if block_reason is not None else candidate
        if branch in _BRANCHES[3:]:
            index = _BRANCHES.index(branch)
            for owner, matrix in enumerate(matrices):
                entry = matrix["entries"][index]
                if (entry["applicability"] != "halt_only"
                    or entry["governed_effect_class"] is not None
                    or entry["result"] != "permit"
                    or entry["reason"] != _HALT_PERMITS[owner]):
                    return ProgressionDecisionConflictV1(
                        "matrix_conflict" if entry["result"] == "conflict"
                        else "halt_only_matrix_contract_conflict")
        if expected_branch is not None and expected_branch != branch:
            return ProgressionDecisionConflictV1("expected_branch_mismatch")
        guard = cast(dict[str, object], value["bootstrap_guard_evidence"])
        if branch == "candidate_acceptance" and guard["acceptance_exhaustively_unclaimed"] is not True:
            return ProgressionDecisionConflictV1("bootstrap_acceptance_guard_conflict")
        if (branch == "attempt_selecting_replan") != (type(replan_proposal) is CognitiveReplanProposalV1):
            return ProgressionDecisionConflictV1("required_fact_invalid")
        if (branch == "attempt_selecting_replan") != (value["replan_proposal_safe_projection"] is not None):
            return ProgressionDecisionConflictV1("required_fact_invalid")
        if replan_proposal is not None and replan_proposal.safe_projection() != value["replan_proposal_safe_projection"]:
            return ProgressionDecisionConflictV1("required_fact_invalid")
        model = cast(dict[str, object], value["recommendation_consistency_evaluation"])
        if model["authoritative_branch"] != branch or model["model_recommendation"] != projection["recommendation"]:
            return ProgressionDecisionConflictV1("required_fact_invalid")
        return ProgressionDecisionReductionV1(branch, block_reason or candidate_reason, candidate_reason)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return ProgressionDecisionConflictV1("required_fact_invalid")
