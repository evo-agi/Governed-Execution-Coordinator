"""Private pure post-execution evidence and projection-safe values.

This module owns only closed no-I/O value reconstruction and pure validation.
It does not retrieve evidence, authenticate a source, issue authority, decide
progression, or mutate durable state.
"""

import dataclasses
import datetime
import hashlib
import json
import re
import typing

from . import _cognitive_proposal_row_values as _cognitive_rows
from . import _cognitive_proposal_semantic_values as _cognitive_values
from . import _development_author_effect_establishment_contracts as _requirement_values
from . import _rw0_c1_mutation_contracts as _c1_contracts
from . import _rw0_c1_semantic_values as _c1_values
from . import _rw0_phase_entry_semantic_values as _phase_values
from . import _worker_execution_semantic_values as _worker_values
from .global_stop import GlobalStopState as _GlobalStopState


__all__ = ()


_VIOLATION_REASONS = frozenset({
    "invalid_mapping",
    "unknown_field",
    "missing_field",
    "invalid_schema_id",
    "invalid_field_type",
    "invalid_field_value",
    "invalid_nested_value",
    "invalid_profile_pair",
    "invalid_reference",
    "invalid_digest",
    "duplicate_entry",
    "invalid_cardinality",
    "relation_mismatch",
    "source_owner_mismatch",
    "evaluation_contract_mismatch",
})
_VIOLATION_TOKEN = object()
_SAFE_REF = re.compile(r"[0-9A-Za-z][0-9A-Za-z.-]{0,95}\Z", re.ASCII)
_SAFE_GENERATED_REF = re.compile(r"[0-9A-Za-z][0-9A-Za-z.-]{0,127}\Z", re.ASCII)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_SHA1 = re.compile(r"[0-9a-f]{40}\Z", re.ASCII)
_UTC_SECOND = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z",
    re.ASCII,
)
_RESERVED_REF_PREFIXES = (
    "connector-", "tunnel-", "workspace-", "org-", "organization-", "user-",
)
_MAPPING_TAG = object()
_LIST_TAG = object()

_BRANCHES = (
    "candidate_acceptance",
    "candidate_repair",
    "attempt_selecting_replan",
    "program_terminal_reject",
    "post_execution_program_block",
)
_EFFECT_CLASSES = (
    "author_candidate",
    "cancel_effect",
    "local_git_commit",
    "review_candidate",
    "validate_candidate",
)
_CURRENTNESS_COMPONENTS = (
    "validation", "review", "policy", "risk_profile", "risk_binding",
)
_CURRENTNESS_SOURCE_SCHEMAS = (
    "governed-execution.nwp-worker-observation.v1",
    "governed-execution.nwp-worker-observation.v1",
    "governed-execution.nwp-post-execution-standing-policy-source-attestation.v1",
    "governed-execution.nwp-post-execution-risk-source-profile.v1",
    "governed-execution.nwp-post-execution-risk-source-binding.v1",
)
_CURRENTNESS_PROFILES = (
    ("post-execution-validation-result-set.v1", "cff49323050cd70855d7fda9b8bcc2666da18a7a3f30f8d8e030a9d60b087d58"),
    ("post-execution-review-result-set.v1", "2dd40a8e0c3628f9e0e3860acc29c0ee908111ce14c7e8dccf944e4b1e9d9730"),
    ("post-execution-standing-policy-source-attestation.v1", "a68f350c418edfe7477cdd8b6b5a709974deff058f382919169154fcbaa7fd12"),
    ("post-execution-risk-source-profile.v1", "1c82ba782f69f24d0e4be84cab71db04f61bedd40f74a3f602c160a408bbca4a"),
    ("post-execution-risk-source-binding.v1", "c4982a13fe91d7af98e87eab7b67d8f9c45b390c82e0232905a53d25dde48471"),
)
_ROLE_NAMES = (
    "candidate_capsule",
    "worker_result",
    "validation_result",
    "independent_review",
    "standing_policy",
    "risk_lane",
    "authority_currentness_attestation",
    "global_stop",
    "effect_ceiling",
)
_ROLE_TYPED_SCHEMAS = (
    "governed-execution.nwp-candidate-capsule-manifest.v1",
    "governed-execution.nwp-rw0-c1-wire-process-result-classification-binding.v1",
    "governed-execution.nwp-validation-disposition.v1",
    "governed-execution.nwp-independent-review-disposition.v1",
    "governed-execution.nwp-post-execution-standing-policy-branch-matrix.v1",
    "governed-execution.nwp-post-execution-risk-lane-branch-matrix.v1",
    "governed-execution.nwp-rw0-authority-verification-observation.v1",
    "governed-execution.nwp-post-execution-global-stop-snapshot.v1",
    "governed-execution.nwp-post-execution-source-effect-ceiling-evidence.v1",
)
_ROLE_SOURCE_POSTURES = (
    "transient_private_resupply", "c1_admitted_exact_value",
    "transient_owner_resupply", "transient_owner_resupply",
    "transient_owner_resupply", "transient_owner_resupply",
    "c1_admitted_exact_value", "transient_owner_resupply",
    "transient_owner_resupply",
)
_ROLE_MODEL_POSTURES = (
    "private_exact_canonical_value",
    "nonprivate_exact_canonical_value", "nonprivate_exact_canonical_value",
    "nonprivate_exact_canonical_value", "nonprivate_exact_canonical_value",
    "nonprivate_exact_canonical_value", "nonprivate_exact_canonical_value",
    "nonprivate_exact_canonical_value", "nonprivate_exact_canonical_value",
)
_ROLE_DIRECT_C1 = (
    None,
    ("wire_process_result_classification_binding", 14),
    None,
    None,
    None,
    None,
    ("authority_verification_observation", 1),
    None,
    None,
)
_ROLE_SOURCE_PROFILE_SCHEMAS = (
    None,
    "governed-execution.nwp-rw0-wire-protocol-profile.v1",
    "governed-execution.nwp-validation-disposition-profile.v1",
    "governed-execution.nwp-independent-review-disposition-profile.v1",
    "governed-execution.nwp-post-execution-standing-policy-matrix-profile.v1",
    "governed-execution.nwp-post-execution-risk-source-profile.v1",
    None,
    "governed-execution.nwp-post-execution-global-stop-profile.v1",
    "governed-execution.nwp-post-execution-source-effect-ceiling-profile.v1",
)
_ROLE_SOURCE_PROFILE_PAIRS = (
    None,
    ("rw0-wire-nwpf-v1", "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454"),
    ("validation-disposition.v1", "65a2af00efe0fd6d83cafe5c713536c12e71814544c342d907ef62a2f3cb4048"),
    ("independent-review-disposition.v1", "c5a87ab332790e95f4cd0fb4790149115e8b15a5e4cd0786272cc535b1b23a78"),
    ("post-execution-standing-policy-matrix.v1", "d0c25cc85f015d222d1fa9ef14d375fe68f16f17283326a9df7d5605cdc9c539"),
    None,
    None,
    ("post-execution-global-stop.v1", "5f2be30f5f081f5c159596375ba872bc08e012e389706b084a79b21baaab9142"),
    ("post-execution-source-effect-ceiling.v1", "6aa721b81b9b341e0e5b3ce3bc10590641dd4d4f50c056ae65e8dc4b605eff1a"),
)
_ROLE_SOURCE_BINDING_SCHEMAS = (
    None,
    "governed-execution.nwp-rw0-c1-relation-binding.v1",
    "governed-execution.nwp-worker-observation.v1",
    "governed-execution.nwp-worker-observation.v1",
    "governed-execution.nwp-post-execution-standing-policy-source-attestation.v1",
    "governed-execution.nwp-post-execution-risk-source-binding.v1",
    None,
    "governed-execution.nwp-global-stop.v1",
    "governed-execution.nwp-effect-fence.v1",
)
_ROLE_SUPPORT_VALUE_COUNTS = (0, 0, 6, 7, 4, 4, 0, 2, 5)
_ROLE_TYPED_IDENTITY_FIELDS = (
    ("capsule_manifest_ref", "portable_capsule_digest"),
    ("value_ref", "value_digest"),
    ("disposition_ref", "disposition_digest"),
    ("disposition_ref", "disposition_digest"),
    ("matrix_ref", "matrix_digest"),
    ("matrix_ref", "matrix_digest"),
    ("observation_ref", "observation_digest"),
    ("snapshot_ref", "snapshot_digest"),
    ("evidence_ref", "evidence_digest"),
)
_DECISION_CURRENTNESS_PROFILE_PAIR = (
    "rw0-c-proposal-evidence-currentness.v1",
    "88b347a069c92a5804ba53dad4f39a9d7ba6a36413fa38812f81e964a8902e9b",
)
_CEILING_FIELDS = (
    "max_active_invocations", "max_candidate_bytes", "max_changed_files",
    "max_cost_microusd", "max_cpu_seconds", "max_deliveries",
    "max_deployments", "max_local_commits", "max_memory_bytes", "max_merges",
    "max_model_input_tokens", "max_model_output_tokens", "max_pull_requests",
    "max_pushes", "max_wall_seconds",
)
_LIST_ENUMS: dict[tuple[str, str], tuple[object, ...]] = {
    ("V17", "allowed_branches"): _BRANCHES,
    ("V17", "allowed_effect_classes"): _EFFECT_CLASSES,
    ("V21", "attempt_allowed_effect_classes"): _EFFECT_CLASSES,
    ("V21", "authority_allowed_effect_classes"): _EFFECT_CLASSES,
    ("V41", "allowed_branches"): _BRANCHES,
    ("V41", "allowed_effect_classes"): _EFFECT_CLASSES,
}

_INTEGER_BOUNDS: dict[tuple[str, str], tuple[int, int]] = {
    ("V01", "program_version_number"): (1, 2**63 - 1),
    ("V01", "attempt_number"): (1, 2**63 - 1),
    ("V03", "role_rank"): (5, 13),
    ("V03", "ordinal"): (0, 0),
    ("V03", "direct_c1_kind_rank"): (1, 15),
    ("V05", "entry_count"): (9, 9),
    ("V06", "role_rank"): (5, 13),
    ("V06", "ordinal"): (0, 0),
    ("V07", "entry_count"): (1, 1),
    ("V08", "role_rank"): (5, 5),
    ("V08", "ordinal"): (0, 0),
    ("V08", "canonical_byte_length"): (0, 2**63 - 1),
    ("V10", "role_supply_count"): (9, 9),
    ("V11", "role_rank"): (5, 13),
    ("V11", "ordinal"): (0, 0),
    ("V11", "support_value_count"): (0, 16),
    ("V12", "rank"): (1, 16),
    ("V12", "ordinal"): (0, 0),
    ("V14", "attempt_number"): (1, 2**63 - 1),
    ("V15", "attempt_number"): (1, 2**63 - 1),
    ("V22", "evidence_binding_count"): (9, 9),
    ("V23", "role_rank"): (5, 13),
    ("V23", "ordinal"): (0, 0),
    ("V23", "required_for_selection"): (1, 1),
    ("V24", "context_role_rank"): (5, 13),
    ("V24", "context_role_ordinal"): (0, 0),
    ("V24", "evidence_locator_ordinal"): (0, 0),
    ("V24", "direct_c1_kind_rank"): (1, 15),
    ("V25", "entry_count"): (0, 65536),
    ("V26", "kind_rank"): (1, 15),
    ("V27", "external_source_count"): (5, 5),
    ("V29", "component_count"): (5, 5),
    ("V31", "entry_count"): (5, 5),
    ("V32", "entry_count"): (5, 5),
    ("V33", "entry_count"): (5, 5),
    ("V40.n01", "ordinal"): (0, 2),
    ("V43", "profile_version"): (1, 1),
}

_VALIDATION_TUPLES = (
    ("passed", "passed", "not_applicable", "validation_passed"),
    ("failed", "repairable_failure", "repairable", "validation_failed_repairable"),
    ("failed", "replan_required", "same_attempt_insufficient", "validation_failed_replan_required"),
    ("failed", "terminal_failure", "nonrepairable", "validation_failed_terminal"),
    ("failed", "unknown", "unknown", "validation_failed_unclassified"),
    ("inconclusive", "unknown", "unknown", "validation_inconclusive"),
    ("not_run", "not_run", "not_applicable", "validation_not_run"),
)
_REVIEW_TUPLES = (
    ("passed", "passed", "review_passed"),
    ("failed", "repair_required", "review_failed_repair_required"),
    ("failed", "replan_required", "review_failed_replan_required"),
    ("failed", "terminal_reject", "review_failed_terminal_reject"),
    ("failed", "unknown", "review_failed_unclassified"),
    ("inconclusive", "unknown", "review_inconclusive"),
)
_MATRIX_REASONS = (
    "policy_identity_conflict", "evaluator_profile_mismatch", "support_conflict",
    "halt_only_policy_not_applicable", "policy_revoked", "policy_not_yet_valid",
    "policy_expired", "branch_not_allowed", "audience_mismatch", "repository_mismatch",
    "path_scope_mismatch", "risk_lane_not_allowed", "effect_class_not_allowed",
    "ceilings_exceeded", "policy_status_unknown", "policy_currentness_unknown",
    "policy_permits", "risk_source_conflict", "halt_only_risk_not_applicable",
    "required_lane_mismatch", "risk_lane_permits", "snapshot_or_phase_mismatch",
    "parent_or_fence_identity_mismatch", "profile_mismatch",
    "halt_only_authority_not_applicable", "authority_denied", "authority_revoked",
    "attempt_fence_expired", "effect_fence_expired", "authority_grant_expired",
    "authority_observation_expired", "authority_status_unknown", "family_status_unknown",
    "revocation_status_unknown", "authority_verified_current",
    "snapshot_or_stop_identity_mismatch", "global_stop_unknown", "halt_only_stop_checked",
    "global_stop_active", "global_stop_clear", "snapshot_lineage_or_fence_mismatch",
    "proposal_evidence_conflict", "halt_only_ceiling_not_applicable",
    "proposal_evidence_noncompliant", "source_effect_exceeds_current_attempt",
    "source_effect_exceeds_current_effect", "source_effect_exceeds_current_authority",
    "proposal_evidence_unknown", "current_authority_unknown",
    "source_effect_within_current_ceilings",
    # Accepted stale-dispatch controls remain syntactically well-formed so the
    # consuming parent profile, rather than scalar grammar, owns rejection.
    "halt_only_risk_lane_not_applicable", "current_evidence_permits",
    "halt_only_checked",
)
_SCALAR_ENUMS: dict[tuple[str, str], tuple[object, ...]] = {
    ("V03", "role"): _ROLE_NAMES,
    ("V06", "role"): _ROLE_NAMES,
    ("V08", "role"): ("candidate_capsule",),
    ("V11", "role"): _ROLE_NAMES,
    ("V14", "source_kind"): ("validator",),
    ("V14", "observation_kind"): ("validation_completed",),
    ("V14", "source_outcome"): tuple(item[0] for item in _VALIDATION_TUPLES),
    ("V14", "author_role"): ("validator",),
    ("V14", "effect_class"): ("validate_candidate",),
    ("V14", "result"): tuple(item[1] for item in _VALIDATION_TUPLES) + ("basis_conflict",),
    ("V14", "repairability"): tuple(item[2] for item in _VALIDATION_TUPLES) + ("conflict",),
    ("V14", "reason"): tuple(item[3] for item in _VALIDATION_TUPLES) + ("source_observation_mismatch",),
    ("V15", "source_kind"): ("independent_reviewer",),
    ("V15", "observation_kind"): ("independent_review_completed",),
    ("V15", "source_outcome"): ("passed", "failed", "inconclusive"),
    ("V15", "author_role"): ("independent_reviewer",),
    ("V15", "effect_class"): ("review_candidate",),
    ("V15", "separation_status"): ("separate", "not_separate", "unknown", "conflict"),
    ("V15", "result"): tuple(item[1] for item in _REVIEW_TUPLES) + ("basis_conflict",),
    ("V15", "reason"): tuple(item[2] for item in _REVIEW_TUPLES) + (
        "review_not_operationally_separate", "reviewer_separation_unknown",
        "reviewer_separation_conflict",
    ),
    ("V16", "branch"): _BRANCHES,
    ("V16", "applicability"): ("governed", "halt_only"),
    ("V16", "governed_effect_class"): ("author_candidate",),
    ("V16", "result"): ("permit", "deny", "unknown", "conflict"),
    ("V16", "reason"): _MATRIX_REASONS,
    ("V20", "global_stop_state"): ("clear", "active", "unknown"),
    ("V20", "global_stop_reason_class"): ("operator_stop", "policy_stop", "safety_stop"),
    ("V21", "source_effect_class"): _EFFECT_CLASSES,
    ("V21", "effect_fence_class"): _EFFECT_CLASSES,
    ("V21", "authority_status"): ("verified", "denied", "unknown"),
    ("V21", "authority_family_status"): ("compatible", "incompatible", "unknown"),
    ("V21", "authority_revocation_status"): ("unrevoked", "revoked", "unknown"),
    ("V21", "result"): ("compliant", "noncompliant", "unknown", "conflict"),
    ("V21", "reason"): (
        "profile_mismatch", "lineage_conflict", "fence_identity_conflict",
        "authority_identity_conflict", "support_conflict",
        "authority_denied_or_revoked", "attempt_fence_expired",
        "effect_fence_expired", "authority_grant_expired",
        "authority_observation_expired", "effect_class_not_allowed_by_attempt",
        "effect_class_not_allowed_by_authority", "effect_exceeds_attempt",
        "effect_exceeds_effect_fence", "effect_exceeds_authority",
        "authority_status_unknown", "authority_family_unknown",
        "authority_revocation_unknown", "authority_ceiling_unknown",
        "source_effect_within_ceilings",
    ),
    ("V22", "proposal_phase"): ("post_execution_semantic_review",),
    ("V22", "recommendation"): ("accept_candidate", "repair_candidate", "replan", "terminal_reject", "block"),
    ("V23", "evidence_role"): _ROLE_NAMES,
    ("V24", "context_role"): _ROLE_NAMES,
    ("V24", "evidence_locator_role"): _ROLE_NAMES,
    ("V28", "role"): _CURRENTNESS_COMPONENTS,
    ("V29", "result"): ("current", "stale", "unknown", "conflict"),
    ("V29", "reason"): (
        "all_components_current", "component_source_stale",
        "component_source_unknown", "component_basis_conflict",
    ),
    ("V30", "component"): _CURRENTNESS_COMPONENTS,
    ("V30", "result"): ("current", "stale", "unknown", "conflict"),
    ("V30", "reason"): (
        "exact_ref_digest_profile_and_freshness", "same_ref_different_digest",
        "different_well_formed_source_pair", "exact_source_expired_at_evaluation",
        "source_unavailable", "malformed_or_wrong_profile",
    ),
    ("V34", "model_recommendation"): ("accept_candidate", "repair_candidate", "replan", "terminal_reject", "block"),
    ("V34", "mapped_branch"): _BRANCHES,
    ("V34", "authoritative_branch"): _BRANCHES,
    ("V34", "result"): ("consistent", "inconsistent", "stale_context", "basis_conflict"),
    ("V34", "reason"): (
        "identity_or_provenance_mismatch", "proposal_or_snapshot_not_current",
        "mapped_branch_equals_authoritative_branch",
        "mapped_branch_differs_from_authoritative_branch",
    ),
    ("V38", "source_kind"): ("validator",),
    ("V38", "observation_kind"): ("validation_completed",),
    ("V38", "source_outcome"): tuple(item[0] for item in _VALIDATION_TUPLES),
    ("V38", "effect_class"): ("validate_candidate",),
    ("V38", "result"): tuple(item[1] for item in _VALIDATION_TUPLES),
    ("V38", "repairability"): tuple(item[2] for item in _VALIDATION_TUPLES),
    ("V38", "reason"): tuple(item[3] for item in _VALIDATION_TUPLES),
    ("V39", "source_kind"): ("independent_reviewer",),
    ("V39", "observation_kind"): ("independent_review_completed",),
    ("V39", "source_outcome"): ("passed", "failed", "inconclusive"),
    ("V39", "effect_class"): ("review_candidate",),
    ("V39", "result"): tuple(item[1] for item in _REVIEW_TUPLES),
    ("V39", "reason"): tuple(item[2] for item in _REVIEW_TUPLES),
    ("V40", "review_source_kind"): ("independent_reviewer",),
    ("V40", "author_source_kind"): ("worker",),
    ("V40", "status"): ("separate", "not_separate", "unknown", "conflict"),
    ("V40", "reason"): (
        "governed_review_graph_separate", "review_source_invocation_reused",
        "review_effect_identity_reused", "review_delivery_identity_reused",
        "author_source_evidence_absent", "author_source_invocation_unresolved",
        "source_role_conflict", "author_source_evidence_conflict",
        "cross_lineage_conflict", "same_phase_closure_conflict",
    ),
    ("V40.n01", "source_kind"): ("worker",),
    ("V40.n01", "observation_kind"): ("worker_started", "candidate_captured", "worker_completed"),
    ("V41", "source_owner_kind"): ("standing_policy_owner",),
    ("V41", "policy_status"): ("active", "inactive", "unknown"),
    ("V41", "revocation_status"): ("unrevoked", "revoked", "unknown"),
    ("V41.n01", "branch"): _BRANCHES,
    ("V41.n01", "applicability"): ("governed", "halt_only"),
    ("V41.n01", "governed_effect_class"): ("author_candidate",),
    ("V41.n01", "result"): ("permit", "deny", "unknown", "conflict"),
    ("V41.n01", "reason"): _MATRIX_REASONS,
    ("V42", "source_owner_kind"): ("risk_policy_owner",),
    ("V42", "policy_status"): ("active", "inactive", "unknown"),
    ("V42", "revocation_status"): ("unrevoked", "revoked", "unknown"),
    ("V42.n01", "branch"): _BRANCHES,
    ("V42.n01", "applicability"): ("governed", "halt_only"),
    ("V42.n01", "governed_effect_class"): ("author_candidate",),
    ("V42.n01", "result"): ("permit", "deny", "unknown", "conflict"),
    ("V42.n01", "reason"): _MATRIX_REASONS + ("halt_only_risk_lane_not_applicable",),
}


class _PostExecutionContractViolation(ValueError):
    """Finite content-free private contract failure."""

    __slots__ = ("_reason",)

    def __init__(self, *args: object, **kwargs: object) -> None:
        if (
            len(args) != 2
            or kwargs
            or args[0] is not _VIOLATION_TOKEN
            or type(args[1]) is not str
            or args[1] not in _VIOLATION_REASONS
        ):
            raise TypeError("construction disabled") from None
        object.__setattr__(self, "_reason", args[1])
        ValueError.__init__(self, args[1])

    @property
    def reason(self) -> str:
        return self._reason

    def __setattr__(self, name: str, value: object) -> None:
        if name in {"__traceback__", "__context__", "__cause__", "__suppress_context__"}:
            BaseException.__setattr__(self, name, value)
            return
        raise AttributeError("immutable")

    def __delattr__(self, name: str) -> typing.NoReturn:
        raise AttributeError("immutable")

    def __repr__(self) -> str:
        return "_PostExecutionContractViolation()"


def _fail(reason: str) -> typing.NoReturn:
    if type(reason) is not str or reason not in _VIOLATION_REASONS:
        reason = "invalid_field_value"
    raise _PostExecutionContractViolation(_VIOLATION_TOKEN, reason) from None


def _require_exact_mapping(value: object) -> dict[str, object]:
    if type(value) is not dict:
        _fail("invalid_mapping")
    mapping = typing.cast(dict[object, object], value)
    if any(type(key) is not str for key in mapping):
        _fail("invalid_mapping")
    return typing.cast(dict[str, object], mapping)


def _require_exact_keys(
    mapping: dict[str, object], fields: tuple[str, ...]
) -> dict[str, object]:
    if any(key not in fields for key in mapping):
        _fail("unknown_field")
    if any(field not in mapping for field in fields):
        _fail("missing_field")
    if len(mapping) != len(fields):
        _fail("invalid_mapping")
    if tuple(mapping) != fields:
        _fail("invalid_mapping")
    return mapping


def _require_exact_tuple(value: object) -> tuple[object, ...]:
    if type(value) is not tuple:
        _fail("invalid_field_type")
    return typing.cast(tuple[object, ...], value)


def _require_exact_list(value: object) -> list[object]:
    if type(value) is not list:
        _fail("invalid_field_type")
    return typing.cast(list[object], value)


def _require_exact_str(value: object) -> str:
    if type(value) is not str:
        _fail("invalid_field_type")
    result = typing.cast(str, value)
    if any(0xD800 <= ord(character) <= 0xDFFF for character in result):
        _fail("invalid_field_value")
    if any(ord(character) < 32 or ord(character) == 127 for character in result):
        _fail("invalid_field_value")
    return result


def _require_safe_ref(value: object) -> str:
    result = _require_exact_str(value)
    if (
        _SAFE_REF.fullmatch(result) is None
        or result.lower().startswith(_RESERVED_REF_PREFIXES)
    ):
        _fail("invalid_reference")
    return result


def _require_sha256(value: object) -> str:
    result = _require_exact_str(value)
    if _SHA256.fullmatch(result) is None:
        _fail("invalid_digest")
    return result


def _require_sha1_oid(value: object) -> str:
    result = _require_exact_str(value)
    if _SHA1.fullmatch(result) is None:
        _fail("invalid_field_value")
    return result


def _require_exact_int(value: object) -> int:
    if type(value) is not int:
        _fail("invalid_field_type")
    result = typing.cast(int, value)
    if not 0 <= result <= 2**63 - 1:
        _fail("invalid_field_value")
    return result


def _require_exact_bool(value: object) -> bool:
    if type(value) is not bool:
        _fail("invalid_field_type")
    return typing.cast(bool, value)


def _require_whole_second_utc(value: object) -> str:
    result = _require_exact_str(value)
    parsed = None
    if _UTC_SECOND.fullmatch(result) is not None and not result.startswith("0000-"):
        try:
            parsed = datetime.datetime.strptime(result, "%Y-%m-%dT%H:%M:%SZ")
        except (TypeError, ValueError, OverflowError):
            parsed = None
    if parsed is None or parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != result:
        _fail("invalid_field_value")
    return result


def _require_enum(value: object, allowed: tuple[object, ...]) -> object:
    if not any(type(value) is type(item) and value == item for item in allowed):
        _fail("invalid_field_value")
    return value


def _require_nullable(value: object, validator: typing.Callable[[object], object]) -> object:
    if value is None:
        return None
    return validator(value)


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, OverflowError):
        _fail("invalid_field_value")


def _domain_separated_digest(domain: str, value: object) -> str:
    domain_value = _require_exact_str(domain)
    return hashlib.sha256(domain_value.encode("utf-8") + b"\0" + _canonical_bytes(value)).hexdigest()


def _generated_ref(prefix: str, domain: str, value: object) -> str:
    prefix_value = _require_exact_str(prefix)
    return prefix_value + _domain_separated_digest(domain, value)


def _exact_equal(left: object, right: object) -> bool:
    return type(left) is type(right) and left == right


def _validate_role_branch_table(mapping: dict[str, object], rank: int) -> None:
    """Enforce the frozen nine-role direct/profile/binding/support branches."""

    index = rank - 5
    direct_fields = (
        "direct_c1_kind", "direct_c1_kind_rank",
        "direct_c1_membership_ref", "direct_c1_membership_digest",
    )
    if all(name in mapping for name in direct_fields):
        direct = _ROLE_DIRECT_C1[index]
        direct_values = tuple(mapping[name] for name in direct_fields)
        if direct is None:
            if any(value is not None for value in direct_values):
                _fail("source_owner_mismatch")
        elif (
            direct_values[0] != direct[0]
            or direct_values[1] != direct[1]
            or direct_values[2] is None
            or direct_values[3] is None
        ):
            _fail("source_owner_mismatch")

    profile_fields = ("source_profile_ref", "source_profile_digest")
    if all(name in mapping for name in profile_fields):
        profile_schema = _ROLE_SOURCE_PROFILE_SCHEMAS[index]
        profile_pair = _ROLE_SOURCE_PROFILE_PAIRS[index]
        profile_values = tuple(mapping[name] for name in profile_fields)
        canonical_profile = mapping.get("source_profile_canonical_value")
        if profile_schema is None:
            if any(value is not None for value in profile_values) or (
                "source_profile_canonical_value" in mapping
                and canonical_profile is not None
            ):
                _fail("invalid_profile_pair")
        elif (
            any(value is None for value in profile_values)
            or (
                "source_profile_canonical_value" in mapping
                and canonical_profile is None
            )
        ):
            _fail("invalid_profile_pair")
        elif profile_pair is not None and profile_values != profile_pair:
            _fail("invalid_profile_pair")

    binding_fields = (
        "source_binding_schema_id", "source_binding_ref", "source_binding_digest",
    )
    if all(name in mapping for name in binding_fields):
        binding_schema = _ROLE_SOURCE_BINDING_SCHEMAS[index]
        binding_values = tuple(mapping[name] for name in binding_fields)
        canonical_binding = mapping.get("source_binding_canonical_value")
        if binding_schema is None:
            if any(value is not None for value in binding_values) or (
                "source_binding_canonical_value" in mapping
                and canonical_binding is not None
            ):
                _fail("source_owner_mismatch")
        elif (
            binding_values[0] != binding_schema
            or binding_values[1] is None
            or binding_values[2] is None
            or (
                "source_binding_canonical_value" in mapping
                and canonical_binding is None
            )
        ):
            _fail("source_owner_mismatch")

    if "support_value_count" in mapping:
        expected_count = _ROLE_SUPPORT_VALUE_COUNTS[index]
        support_fields = (
            "support_set_ref", "support_set_digest", "support_set_canonical_value",
        )
        support_values = tuple(mapping[name] for name in support_fields)
        canonical_values = typing.cast(list[object], mapping["support_canonical_values"])
        if expected_count == 0:
            if (
                any(value is not None for value in support_values)
                or mapping["support_value_count"] != 0
                or canonical_values
            ):
                _fail("source_owner_mismatch")
        elif (
            any(value is None for value in support_values)
            or mapping["support_value_count"] != expected_count
            or len(canonical_values) != expected_count
        ):
            _fail("source_owner_mismatch")


class _PostExecutionValue:
    __slots__ = ()
    __hash__ = None
    _V_NUMBER = ""
    _FIELDS: tuple[str, ...] = ()
    _FIELD_SPECS: tuple[dict[str, object], ...] = ()
    _SCHEMA_ID: str | None = None
    _PROFILE_PAIR: tuple[str, str] | None = None
    _REFERENCE: dict[str, object] = {}
    _DIGEST: dict[str, object] = {}
    _NESTED: dict[str, type[object]] = {}
    _META: dict[str, object] = {}

    @classmethod
    def _define(
        cls,
        name: str,
        module_name: str,
        allocation: dict[str, object],
        nested: dict[str, type[object]] | None = None,
        meta: dict[str, object] | None = None,
    ) -> type[object]:
        ordered = typing.cast(list[dict[str, object]], allocation["ordered_fields"])
        field_names = tuple(typing.cast(str, item["name"]) for item in ordered)
        pair = allocation.get("governing_profile_pair")

        def _reject_subclass(subclass: type[object], **kwargs: object) -> typing.NoReturn:
            raise TypeError("subclassing disabled")

        namespace = {
            "__module__": module_name,
            "_V_NUMBER": allocation["v_number"],
            "_FIELDS": field_names,
            "_FIELD_SPECS": tuple(ordered),
            "_SCHEMA_ID": allocation.get("schema_id"),
            "_PROFILE_PAIR": None
            if pair is None
            else (pair["profile_ref"], pair["profile_digest"]),
            "_REFERENCE": allocation.get("reference_posture") or {},
            "_DIGEST": allocation.get("digest_posture") or {},
            "_NESTED": {} if nested is None else dict(nested),
            "_META": {} if meta is None else dict(meta),
            "__init_subclass__": _reject_subclass,
        }
        return dataclasses.make_dataclass(
            name,
            [(field_name, object) for field_name in field_names],
            bases=(cls,),
            namespace=namespace,
            frozen=True,
            slots=True,
            repr=False,
            module=module_name,
        )

    @classmethod
    def from_mapping(cls, value: object) -> typing.Self:
        mapping = _require_exact_keys(_require_exact_mapping(value), cls._FIELDS)
        converted = [
            cls._normalize_field(spec, mapping[typing.cast(str, spec["name"])])
            for spec in cls._FIELD_SPECS
        ]
        return cls(*converted)

    @classmethod
    def from_supplied(cls, value: object) -> typing.Self:
        if type(value) is cls:
            return typing.cast(typing.Self, value)
        return cls.from_mapping(value)

    def __post_init__(self) -> None:
        for spec in self._FIELD_SPECS:
            name = typing.cast(str, spec["name"])
            normalized = self._normalize_field(
                spec, object.__getattribute__(self, name), _internal=True
            )
            object.__setattr__(self, name, normalized)
        self._validate_value()

    @classmethod
    def _freeze_json(cls, value: object) -> object:
        if type(value) is dict:
            mapping = _require_exact_mapping(value)
            return (_MAPPING_TAG, tuple((key, cls._freeze_json(member)) for key, member in mapping.items()))
        if type(value) is list:
            return (_LIST_TAG, tuple(cls._freeze_json(member) for member in typing.cast(list[object], value)))
        if type(value) is str:
            return _require_exact_str(value)
        if type(value) is int:
            return _require_exact_int(value)
        if type(value) is bool or value is None:
            return value
        if type(value) is tuple and len(typing.cast(tuple[object, ...], value)) == 2:
            marker = typing.cast(tuple[object, ...], value)[0]
            if marker is _MAPPING_TAG or marker is _LIST_TAG:
                return value
        _fail("invalid_nested_value")

    @classmethod
    def _thaw_json(cls, value: object) -> object:
        if type(value) is tuple and len(typing.cast(tuple[object, ...], value)) == 2:
            marker, members = typing.cast(tuple[object, ...], value)
            if marker is _MAPPING_TAG:
                return {
                    typing.cast(str, key): cls._thaw_json(member)
                    for key, member in typing.cast(tuple[tuple[object, object], ...], members)
                }
            if marker is _LIST_TAG:
                return [cls._thaw_json(member) for member in typing.cast(tuple[object, ...], members)]
        return value

    @classmethod
    def _normalize_field(
        cls,
        spec: dict[str, object],
        value: object,
        *,
        _internal: bool = False,
    ) -> object:
        name = typing.cast(str, spec["name"])
        nullable = bool(spec.get("nullable"))
        if value is None:
            if nullable or spec["type"] == "exact_null":
                return None
            _fail("invalid_field_type")
        field_type = spec["type"]
        nested = cls._NESTED.get(name)
        if field_type in {"exact_builtin_str", "exact_builtin_str_or_exact_null"}:
            result: object = _require_exact_str(value)
            rule = spec.get("rule")
            if name.endswith("_digest") or rule == "64_lowercase_hex" or (
                type(rule) is str and "64_lowercase_hex" in rule
            ):
                result = _require_sha256(value)
            elif name == "base_git_oid":
                result = _require_sha1_oid(value)
            elif type(rule) is str and "whole_second_UTC" in rule:
                result = _require_whole_second_utc(value)
            elif type(rule) is str and "1..96_ASCII_bytes" in rule:
                result = _require_safe_ref(value)
            elif name.endswith("_ref"):
                generated_field = cls._REFERENCE.get("field") == name and cls._REFERENCE.get("posture") in {
                    "generated", "generated_and_owner_supplied_for_revalidation",
                }
                generated_shape = re.fullmatch(
                    r"[0-9A-Za-z][0-9A-Za-z._-]{0,62}\.[0-9a-f]{64}",
                    typing.cast(str, result),
                    re.ASCII,
                ) is not None
                if generated_field or generated_shape:
                    if _SAFE_GENERATED_REF.fullmatch(typing.cast(str, result)) is None:
                        _fail("invalid_reference")
                elif type(rule) is str and "bounded_exact_string" in rule:
                    encoded = typing.cast(str, result).encode("utf-8")
                    if not 1 <= len(encoded) <= 96:
                        _fail("invalid_reference")
                elif _SAFE_REF.fullmatch(typing.cast(str, result)) is None:
                    _fail("invalid_reference")
                if typing.cast(str, result).lower().startswith(_RESERVED_REF_PREFIXES):
                    _fail("invalid_reference")
            elif type(rule) is str and "bounded_exact_string" in rule:
                encoded = typing.cast(str, result).encode("utf-8")
                if not 1 <= len(encoded) <= 96:
                    _fail("invalid_field_value")
            if "enum" in spec:
                result = _require_enum(result, tuple(typing.cast(list[object], spec["enum"])))
            accepted = _SCALAR_ENUMS.get((cls._V_NUMBER, name))
            if accepted is not None:
                result = _require_enum(result, accepted)
            return result
        if field_type == "exact_null" and cls._V_NUMBER == "V20" and name in {
            "global_stop_stop_id",
            "global_stop_reason_class",
            "global_stop_issuer_ref",
            "global_stop_issued_at",
            "global_stop_operator_decision_ref",
        }:
            # V20's canonical clear exemplar carries nulls, while its frozen
            # active branch carries the exact owner strings.  Keep that branch
            # conditional here so the literal exemplar metadata does not turn
            # into an accidental clear-only grammar.
            result = _require_exact_str(value)
            if name == "global_stop_issued_at":
                return _require_whole_second_utc(result)
            if name == "global_stop_reason_class":
                return _require_enum(result, _SCALAR_ENUMS[("V20", name)])
            if _SAFE_REF.fullmatch(result) is None or result.lower().startswith(_RESERVED_REF_PREFIXES):
                _fail("invalid_reference")
            return result
        if field_type in {
            "exact_builtin_int", "exact_builtin_int_bool_rejected",
            "exact_builtin_int_bool_rejected_or_exact_null",
        }:
            result = _require_exact_int(value)
            bounds = _INTEGER_BOUNDS.get((cls._V_NUMBER, name))
            if bounds is not None and not bounds[0] <= result <= bounds[1]:
                _fail("invalid_field_value")
            return result
        if field_type == "exact_builtin_bool":
            return _require_exact_bool(value)
        if field_type in {"exact_builtin_dict", "exact_builtin_dict_or_exact_null"}:
            if nested is not None:
                if _internal and type(value) is nested:
                    return value
                if type(value) is not dict:
                    _fail("invalid_field_type")
                return nested.from_mapping(value)
            if _internal and type(value) is tuple and len(typing.cast(tuple[object, ...], value)) == 2:
                marker = typing.cast(tuple[object, ...], value)[0]
                if marker is _MAPPING_TAG:
                    return value
            if type(value) is not dict:
                _fail("invalid_field_type")
            return cls._freeze_json(value)
        if field_type == "exact_builtin_list":
            if type(value) is list:
                members = tuple(typing.cast(list[object], value))
            elif _internal and type(value) is tuple:
                members = typing.cast(tuple[object, ...], value)
            else:
                _fail("invalid_field_type")
            rule = spec.get("rule")
            minimum = 0
            maximum = 2**63 - 1
            if "cardinality" in spec:
                minimum = maximum = typing.cast(int, spec["cardinality"])
            elif type(rule) is dict:
                minimum = typing.cast(int, rule.get("minimum", minimum))
                maximum = typing.cast(int, rule.get("maximum", maximum))
            if not minimum <= len(members) <= maximum:
                _fail("invalid_cardinality")
            if nested is not None:
                normalized = tuple(
                    member if type(member) is nested else nested.from_mapping(member)
                    for member in members
                )
            else:
                item_type = rule.get("item_type") if type(rule) is dict else None
                if item_type == "exact_builtin_str_safe_ref":
                    normalized = tuple(_require_safe_ref(member) for member in members)
                elif item_type == "exact_builtin_str_enum":
                    allowed = _LIST_ENUMS.get((cls._V_NUMBER, name))
                    if allowed is None:
                        _fail("invalid_field_value")
                    normalized = tuple(
                        typing.cast(str, _require_enum(member, allowed))
                        for member in members
                    )
                else:
                    normalized = tuple(cls._freeze_json(member) for member in members)
            return normalized
        if field_type == "exact_null":
            _fail("invalid_field_type")
        _fail("invalid_field_type")

    @classmethod
    def _plain(cls, value: object) -> object:
        if isinstance(value, _PostExecutionValue):
            return value.to_mapping()
        if type(value) is tuple:
            members = typing.cast(tuple[object, ...], value)
            if len(members) == 2 and (members[0] is _MAPPING_TAG or members[0] is _LIST_TAG):
                return cls._thaw_json(value)
            return [cls._plain(member) for member in members]
        return value

    def to_mapping(self) -> dict[str, object]:
        return {
            name: self._plain(object.__getattribute__(self, name))
            for name in self._FIELDS
        }

    identity_mapping = to_mapping

    def computed_ref(self) -> str:
        posture = self._REFERENCE
        if posture.get("posture") not in {"generated", "generated_and_owner_supplied_for_revalidation"}:
            _fail("invalid_reference")
        mapping = self.to_mapping()
        preimage = {
            field: mapping[typing.cast(str, field)]
            for field in typing.cast(list[str], posture["preimage_fields"])
        }
        return _generated_ref(
            typing.cast(str, posture["prefix"]),
            typing.cast(str, posture["domain"]),
            preimage,
        )

    def computed_digest(self) -> str:
        posture = self._DIGEST
        domain = posture.get("domain")
        exclusions = posture.get("self_exclusion")
        if type(domain) is not str or type(exclusions) is not list:
            _fail("invalid_digest")
        mapping = self.to_mapping()
        preimage = {
            key: value for key, value in mapping.items()
            if key not in typing.cast(list[str], exclusions)
        }
        return _domain_separated_digest(domain, preimage)

    def _validate_value(self) -> None:
        mapping = self.to_mapping()
        if "schema_id" in mapping and self._SCHEMA_ID is not None and mapping["schema_id"] != self._SCHEMA_ID:
            _fail("invalid_schema_id")
        for spec in self._FIELD_SPECS:
            if "constant" in spec and mapping[typing.cast(str, spec["name"])] != spec["constant"]:
                _fail("invalid_schema_id")
        if (
            self._PROFILE_PAIR is not None
            and "profile_ref" in mapping
            and self._V_NUMBER not in {"V09", "V10", "V13", "V28", "V30"}
        ):
            if (mapping["profile_ref"], mapping["profile_digest"]) != self._PROFILE_PAIR:
                _fail("invalid_profile_pair")
        self._validate_lists(mapping)
        self._validate_relations(mapping)
        posture = self._REFERENCE
        field = posture.get("field")
        if posture.get("posture") in {"generated", "generated_and_owner_supplied_for_revalidation"}:
            if type(field) is not str or mapping[field] != self.computed_ref():
                _fail("invalid_reference")
        digest_field = self._DIGEST.get("field")
        if type(digest_field) is str and mapping[digest_field] != self.computed_digest():
            _fail("invalid_digest")

    def _validate_lists(self, mapping: dict[str, object]) -> None:
        for spec in self._FIELD_SPECS:
            if spec["type"] != "exact_builtin_list":
                continue
            name = typing.cast(str, spec["name"])
            value = typing.cast(list[object], mapping[name])
            encoded = tuple(_canonical_bytes(member) for member in value)
            rule = spec.get("rule")
            duplicate_rule = rule.get("duplicates") if type(rule) is dict else None
            duplicates = type(duplicate_rule) is str and duplicate_rule.startswith("reject")
            ordering = rule.get("ordering") if type(rule) is dict else spec.get("ordering")
            if duplicates or "duplicates_rejected" in str(ordering):
                if len(encoded) != len(set(encoded)):
                    _fail("duplicate_entry")
            if ordering == "strict_lexicographic" and value != sorted(value):
                _fail("relation_mismatch")
            if ordering == "canonical_branch_order":
                expected = [item for item in _BRANCHES if item in value]
                if value != expected:
                    _fail("relation_mismatch")
            if ordering in {
                "canonical_effect_class_order",
                "strict_lexicographic_current_effect_class_order",
            }:
                expected = [item for item in _EFFECT_CLASSES if item in value]
                if value != expected:
                    _fail("relation_mismatch")
            if ordering == "exact_owner_inventory_by_consumer_order":
                coordinates = tuple(
                    (typing.cast(dict[str, object], item)["rank"],
                     typing.cast(dict[str, object], item)["ordinal"])
                    for item in value
                )
                if coordinates != tuple(sorted(coordinates)):
                    _fail("relation_mismatch")
        count_fields = {
            "role_entries": "role_entry_count",
            "role_supplies": "role_supply_count",
            "support_canonical_values": "support_value_count",
            "evidence_bindings": "evidence_binding_count",
            "external_sources": "external_source_count",
            "components": "component_count",
        }
        if "entries" in mapping and "entry_count" in mapping:
            count_fields["entries"] = "entry_count"
        for list_field, count_field in count_fields.items():
            if list_field in mapping and count_field in mapping:
                if len(typing.cast(list[object], mapping[list_field])) != mapping[count_field]:
                    _fail("invalid_cardinality")

    def _validate_relations(self, mapping: dict[str, object]) -> None:
        if "base_git_object_format" in mapping and "base_git_oid" in mapping:
            if mapping["base_git_object_format"] != "sha1":
                _fail("relation_mismatch")
            _require_sha1_oid(mapping["base_git_oid"])
        for start, end in (
            ("not_before", "expires_at"),
            ("evaluated_at", "expires_at"),
        ):
            if start in mapping and end in mapping and mapping[start] is not None and mapping[end] is not None:
                if typing.cast(str, mapping[start]) >= typing.cast(str, mapping[end]):
                    _fail("relation_mismatch")
        if (
            "source_invocation_started_at" in mapping
            and "source_invocation_completed_at" in mapping
            and typing.cast(str, mapping["source_invocation_started_at"])
            > typing.cast(str, mapping["source_invocation_completed_at"])
        ):
            _fail("relation_mismatch")
        if self._V_NUMBER == "V16":
            expected = dict((branch, (applicability, effect)) for branch, applicability, effect in _CANONICAL_BRANCHES)
            branch = typing.cast(str, mapping["branch"])
            if branch not in expected or expected[branch] != (
                mapping["applicability"], mapping["governed_effect_class"]
            ):
                _fail("evaluation_contract_mismatch")
        matrix = self._META.get("matrix")
        if type(matrix) is dict:
            branches = typing.cast(tuple[tuple[str, str, str | None], ...], matrix["branches"])
            entries = typing.cast(list[dict[str, object]], mapping["entries"])
            if tuple((entry["branch"], entry["applicability"], entry["governed_effect_class"]) for entry in entries) != branches:
                _fail("evaluation_contract_mismatch")
            allowed_pairs = typing.cast(tuple[tuple[str, str], ...], matrix["allowed_pairs"])
            if any((entry["result"], entry["reason"]) not in allowed_pairs for entry in entries):
                _fail("evaluation_contract_mismatch")
        assertion_branches = self._META.get("assertion_branches")
        if type(assertion_branches) is tuple:
            assertions = typing.cast(list[dict[str, object]], mapping["branch_assertions"])
            if tuple((item["branch"], item["applicability"], item["governed_effect_class"]) for item in assertions) != assertion_branches:
                _fail("evaluation_contract_mismatch")
        if self._V_NUMBER in {"V14", "V38"}:
            allowed = {
                ("passed", "not_applicable", "validation_passed"),
                ("repairable_failure", "repairable", "validation_failed_repairable"),
                ("replan_required", "same_attempt_insufficient", "validation_failed_replan_required"),
                ("terminal_failure", "nonrepairable", "validation_failed_terminal"),
                ("unknown", "unknown", "validation_failed_unclassified"),
                ("unknown", "unknown", "validation_inconclusive"),
                ("not_run", "not_applicable", "validation_not_run"),
                ("basis_conflict", "conflict", "source_observation_mismatch"),
            }
            if (mapping["result"], mapping["repairability"], mapping["reason"]) not in allowed:
                _fail("evaluation_contract_mismatch")
        if self._V_NUMBER in {"V15", "V39"}:
            allowed = {
                ("passed", "review_passed"),
                ("repair_required", "review_failed_repair_required"),
                ("replan_required", "review_failed_replan_required"),
                ("terminal_reject", "review_failed_terminal_reject"),
                ("unknown", "review_failed_unclassified"),
                ("unknown", "review_inconclusive"),
                ("basis_conflict", "review_not_operationally_separate"),
                ("unknown", "reviewer_separation_unknown"),
                ("basis_conflict", "reviewer_separation_conflict"),
            }
            if (mapping["result"], mapping["reason"]) not in allowed:
                _fail("evaluation_contract_mismatch")
        if self._V_NUMBER == "V40":
            allowed = {
                ("separate", "governed_review_graph_separate"),
                ("not_separate", "review_source_invocation_reused"),
                ("not_separate", "review_effect_identity_reused"),
                ("not_separate", "review_delivery_identity_reused"),
                ("unknown", "author_source_evidence_absent"),
                ("unknown", "author_source_invocation_unresolved"),
                ("conflict", "source_role_conflict"),
                ("conflict", "author_source_evidence_conflict"),
                ("conflict", "cross_lineage_conflict"),
                ("conflict", "same_phase_closure_conflict"),
            }
            if (mapping["status"], mapping["reason"]) not in allowed:
                _fail("evaluation_contract_mismatch")
        if self._V_NUMBER == "V34":
            branch = _RECOMMENDATION_BRANCHES.get(typing.cast(str, mapping["model_recommendation"]))
            if branch != mapping["mapped_branch"]:
                _fail("evaluation_contract_mismatch")
            expected = "consistent" if branch == mapping["authoritative_branch"] else "inconsistent"
            if mapping["result"] in {"consistent", "inconsistent"} and mapping["result"] != expected:
                _fail("evaluation_contract_mismatch")
            if mapping["result"] == "consistent" and mapping["reason"] != "mapped_branch_equals_authoritative_branch":
                _fail("evaluation_contract_mismatch")
            if mapping["result"] == "inconsistent" and mapping["reason"] != "mapped_branch_differs_from_authoritative_branch":
                _fail("evaluation_contract_mismatch")

        if self._V_NUMBER in {"V03", "V06", "V08", "V11", "V23"}:
            role_field = "evidence_role" if self._V_NUMBER == "V23" else "role"
            rank_field = "role_rank"
            rank = typing.cast(int, mapping[rank_field])
            if not 5 <= rank <= 13 or mapping[role_field] != _ROLE_NAMES[rank - 5]:
                _fail("source_owner_mismatch")
            if mapping.get("ordinal") != 0:
                _fail("relation_mismatch")
            typed_schema = mapping.get("typed_schema_id")
            if typed_schema is not None and typed_schema != _ROLE_TYPED_SCHEMAS[rank - 5]:
                _fail("source_owner_mismatch")
            if "source_posture" in mapping and mapping["source_posture"] != _ROLE_SOURCE_POSTURES[rank - 5]:
                _fail("source_owner_mismatch")
            if "model_input_posture" in mapping and mapping["model_input_posture"] != _ROLE_MODEL_POSTURES[rank - 5]:
                _fail("relation_mismatch")
            if self._V_NUMBER == "V08" and rank != 5:
                _fail("source_owner_mismatch")
            if self._V_NUMBER in {"V03", "V11"}:
                _validate_role_branch_table(mapping, rank)

        if self._V_NUMBER == "V11":
            support = mapping["support_set_canonical_value"]
            values = typing.cast(list[dict[str, object]], mapping["support_canonical_values"])
            nullable_fields = (
                "support_set_ref", "support_set_digest", "support_set_canonical_value",
            )
            if support is None:
                if (
                    any(mapping[name] is not None for name in nullable_fields)
                    or mapping["support_value_count"] != 0
                    or values
                ):
                    _fail("relation_mismatch")
            else:
                support_mapping = typing.cast(dict[str, object], support)
                expected_support_keys = tuple(sorted(PostExecutionSupportSetV1._FIELDS))
                if tuple(support_mapping) != expected_support_keys:
                    _fail("invalid_nested_value")
                raw_entries = support_mapping["entries"]
                if type(raw_entries) is not list:
                    _fail("invalid_nested_value")
                ordered_entries = []
                for entry in typing.cast(list[object], raw_entries):
                    if type(entry) is not dict or tuple(typing.cast(dict[str, object], entry)) != tuple(
                        sorted(PostExecutionSupportEntryV1._FIELDS)
                    ):
                        _fail("invalid_nested_value")
                    ordered_entries.append({
                        name: typing.cast(dict[str, object], entry)[name]
                        for name in PostExecutionSupportEntryV1._FIELDS
                    })
                ordered_support = {
                    name: ordered_entries if name == "entries" else support_mapping[name]
                    for name in PostExecutionSupportSetV1._FIELDS
                }
                support_value = PostExecutionSupportSetV1.from_mapping(ordered_support)
                if (
                    mapping["support_set_ref"] != support_value.support_set_ref
                    or mapping["support_set_digest"] != support_value.support_set_digest
                    or mapping["support_value_count"] != len(values)
                    or len(values) != len(support_value.entries)
                ):
                    _fail("source_owner_mismatch")
                for entry, canonical_value in zip(support_value.entries, values, strict=True):
                    if type(canonical_value) is not dict or tuple(canonical_value) != tuple(
                        sorted(canonical_value)
                    ):
                        _fail("invalid_nested_value")
                    if canonical_value.get("schema_id") != entry.source_schema_id:
                        _fail("source_owner_mismatch")
                    ref_is_present = entry.source_ref in canonical_value.values()
                    clear_stop = (
                        entry.source_ref == "global-stop-clear"
                        and canonical_value.get("active") is False
                    )
                    if not (ref_is_present or clear_stop):
                        _fail("source_owner_mismatch")

        role_lists = {
            "V02": "role_entries",
            "V05": "entries",
            "V10": "role_supplies",
            "V22": "evidence_bindings",
        }
        role_list_field = role_lists.get(self._V_NUMBER)
        if role_list_field is not None:
            values = typing.cast(list[dict[str, object]], mapping[role_list_field])
            role_field = "evidence_role" if self._V_NUMBER == "V22" else "role"
            if tuple((item[role_field], item["role_rank"], item["ordinal"]) for item in values) != tuple(
                (role, rank, 0) for rank, role in enumerate(_ROLE_NAMES, 5)
            ):
                _fail("source_owner_mismatch")

        if self._V_NUMBER in {"V14", "V38"} and mapping["result"] != "basis_conflict":
            actual = (
                mapping["source_outcome"], mapping["result"],
                mapping["repairability"], mapping["reason"],
            )
            if actual not in _VALIDATION_TUPLES:
                _fail("evaluation_contract_mismatch")
            if mapping["source_reason_code"] != mapping["reason"]:
                _fail("evaluation_contract_mismatch")
        if self._V_NUMBER in {"V15", "V39"}:
            if self._V_NUMBER == "V15" and mapping["separation_status"] != "separate":
                expected_by_status = {
                    "not_separate": ("basis_conflict", "review_not_operationally_separate"),
                    "unknown": ("unknown", "reviewer_separation_unknown"),
                    "conflict": ("basis_conflict", "reviewer_separation_conflict"),
                }
                if (mapping["result"], mapping["reason"]) != expected_by_status[mapping["separation_status"]]:
                    _fail("evaluation_contract_mismatch")
            else:
                actual_review = (mapping["source_outcome"], mapping["result"], mapping["reason"])
                if actual_review not in _REVIEW_TUPLES:
                    _fail("evaluation_contract_mismatch")
                if mapping["source_reason_code"] != mapping["reason"]:
                    _fail("evaluation_contract_mismatch")

        if self._V_NUMBER in {"V14", "V15", "V38", "V39"}:
            if mapping["source_observed_at"] > mapping["evaluated_at"]:
                _fail("relation_mismatch")
            if mapping["source_evidence_refs"] != mapping.get(
                "result_set_evidence_refs", mapping["source_evidence_refs"]
            ):
                _fail("source_owner_mismatch")
            if "result_author_ref" in mapping and (
                mapping["result_author_ref"] != mapping["source_ref"]
                or mapping["result_author_invocation_ref"] != mapping["source_invocation_ref"]
            ):
                _fail("source_owner_mismatch")

        if self._V_NUMBER == "V20":
            if mapping["global_stop_schema_id"] != "governed-execution.nwp-global-stop.v1":
                _fail("source_owner_mismatch")
            details = (
                "global_stop_stop_id", "global_stop_reason_class", "global_stop_issuer_ref",
                "global_stop_issued_at", "global_stop_operator_decision_ref",
            )
            state = mapping["global_stop_state"]
            if state == "clear":
                if mapping["global_stop_ref"] != "global-stop-clear" or any(mapping[name] is not None for name in details):
                    _fail("source_owner_mismatch")
            elif state == "active":
                if any(mapping[name] is None for name in details):
                    _fail("source_owner_mismatch")
                if mapping["global_stop_ref"] != mapping["global_stop_stop_id"]:
                    _fail("source_owner_mismatch")
            if mapping["global_stop_updated_at"] > mapping["evaluated_at"]:
                _fail("relation_mismatch")
            if mapping["global_stop_issued_at"] is not None and mapping["global_stop_issued_at"] > mapping["global_stop_updated_at"]:
                _fail("relation_mismatch")

        if self._V_NUMBER == "V21":
            if (
                mapping["attempt_fence_schema_id"]
                != "governed-execution.nwp-attempt-fence.v1"
                or mapping["effect_fence_schema_id"]
                != "governed-execution.nwp-effect-fence.v1"
                or mapping["authority_schema_id"]
                != "governed-execution.nwp-rw0-authority-verification-observation.v1"
            ):
                _fail("source_owner_mismatch")
            ceiling_names = (
                "source_effect_ceilings", "attempt_ceilings", "effect_ceilings", "authority_ceilings",
            )
            ceilings: dict[str, dict[str, object]] = {}
            for name in ceiling_names:
                value = typing.cast(dict[str, object], mapping[name])
                if tuple(value) != _CEILING_FIELDS:
                    _fail("invalid_nested_value")
                if any(type(value[field]) is not int or typing.cast(int, value[field]) < 0 for field in _CEILING_FIELDS):
                    _fail("invalid_nested_value")
                ceilings[name] = value
            expected_result: tuple[str, str]
            if mapping["effect_fence_class"] != mapping["source_effect_class"]:
                expected_result = ("conflict", "fence_identity_conflict")
            elif mapping["authority_family_status"] == "incompatible":
                expected_result = ("conflict", "authority_identity_conflict")
            elif mapping["authority_status"] == "denied" or mapping["authority_revocation_status"] == "revoked":
                expected_result = ("noncompliant", "authority_denied_or_revoked")
            elif mapping["evaluated_at"] >= mapping["attempt_fence_expires_at"]:
                expected_result = ("noncompliant", "attempt_fence_expired")
            elif mapping["evaluated_at"] >= mapping["effect_fence_expires_at"]:
                expected_result = ("noncompliant", "effect_fence_expired")
            elif mapping["evaluated_at"] >= mapping["authority_grant_expires_at"]:
                expected_result = ("noncompliant", "authority_grant_expired")
            elif mapping["evaluated_at"] >= mapping["authority_observation_expires_at"]:
                expected_result = ("noncompliant", "authority_observation_expired")
            elif mapping["source_effect_class"] not in mapping["attempt_allowed_effect_classes"]:
                expected_result = ("noncompliant", "effect_class_not_allowed_by_attempt")
            elif mapping["source_effect_class"] not in mapping["authority_allowed_effect_classes"]:
                expected_result = ("noncompliant", "effect_class_not_allowed_by_authority")
            elif any(typing.cast(int, ceilings["source_effect_ceilings"][field]) > typing.cast(int, ceilings["attempt_ceilings"][field]) for field in _CEILING_FIELDS):
                expected_result = ("noncompliant", "effect_exceeds_attempt")
            elif any(typing.cast(int, ceilings["source_effect_ceilings"][field]) > typing.cast(int, ceilings["effect_ceilings"][field]) for field in _CEILING_FIELDS):
                expected_result = ("noncompliant", "effect_exceeds_effect_fence")
            elif any(typing.cast(int, ceilings["source_effect_ceilings"][field]) > typing.cast(int, ceilings["authority_ceilings"][field]) for field in _CEILING_FIELDS):
                expected_result = ("noncompliant", "effect_exceeds_authority")
            elif "unknown" in {
                mapping["authority_status"], mapping["authority_family_status"],
                mapping["authority_revocation_status"],
            }:
                reason = {
                    "authority_status": "authority_status_unknown",
                    "authority_family_status": "authority_family_unknown",
                    "authority_revocation_status": "authority_revocation_unknown",
                }
                field = next(name for name in reason if mapping[name] == "unknown")
                expected_result = ("unknown", reason[field])
            else:
                expected_result = ("compliant", "source_effect_within_ceilings")
            if (mapping["result"], mapping["reason"]) != expected_result:
                _fail("evaluation_contract_mismatch")

        if self._V_NUMBER == "V22":
            times = tuple(typing.cast(str, mapping[name]) for name in (
                "source_invocation_started_at", "source_invocation_completed_at",
                "artifact_validated_at", "evidence_bound_at", "proposal_created_at",
            ))
            if times != tuple(sorted(times)) or mapping["projection_evaluated_at"] != mapping["proposal_created_at"]:
                _fail("relation_mismatch")
            for item in typing.cast(list[dict[str, object]], mapping["evidence_bindings"]):
                if (
                    item["proposal_ref"] != mapping["proposal_ref"]
                    or item["proposal_phase"] != mapping["proposal_phase"]
                    or item["evidence_set_ref"] != mapping["evidence_set_ref"]
                    or item["evidence_bound_at"] != mapping["evidence_bound_at"]
                ):
                    _fail("source_owner_mismatch")

        if self._V_NUMBER == "V23":
            if mapping["required_for_selection"] != 1:
                _fail("relation_mismatch")

        if self._V_NUMBER == "V24":
            rank = typing.cast(int, mapping["context_role_rank"])
            if not 5 <= rank <= 13:
                _fail("source_owner_mismatch")
            _validate_role_branch_table(mapping, rank)
            if (
                mapping["decision_currentness_profile_ref"],
                mapping["decision_currentness_profile_digest"],
            ) != _DECISION_CURRENTNESS_PROFILE_PAIR:
                _fail("invalid_profile_pair")
            expected_role = _ROLE_NAMES[rank - 5]
            if (
                mapping["context_role"] != expected_role
                or mapping["context_role_ordinal"] != 0
                or mapping["evidence_locator_role"] != expected_role
                or mapping["evidence_locator_ordinal"] != 0
                or mapping["evidence_locator_proposal_ref"] != mapping["proposal_ref"]
                or mapping["typed_schema_id"] != _ROLE_TYPED_SCHEMAS[rank - 5]
                or mapping["source_posture"] != _ROLE_SOURCE_POSTURES[rank - 5]
                or mapping["model_input_posture"] != _ROLE_MODEL_POSTURES[rank - 5]
                or mapping["result"] != "resolved"
                or mapping["reason"] != "exact_role_binding"
                or mapping["resolution_posture"] != "recomputable_from_exact_resupply"
            ):
                _fail("source_owner_mismatch")

        if self._V_NUMBER == "V25":
            entries = typing.cast(list[dict[str, object]], mapping["entries"])
            keys = tuple((item["kind_rank"], item["membership_ref"]) for item in entries)
            if keys != tuple(sorted(keys)) or len(keys) != len(set(keys)):
                _fail("relation_mismatch")

        if self._V_NUMBER == "V27":
            sources = typing.cast(list[dict[str, object]], mapping["external_sources"])
            if tuple(item["role"] for item in sources) != _CURRENTNESS_COMPONENTS:
                _fail("source_owner_mismatch")
            for index, item in enumerate(sources):
                if (
                    item["source_schema_id"] != _CURRENTNESS_SOURCE_SCHEMAS[index]
                    or (item["profile_ref"], item["profile_digest"]) != _CURRENTNESS_PROFILES[index]
                ):
                    _fail("source_owner_mismatch")

        if self._V_NUMBER == "V30":
            index = _CURRENTNESS_COMPONENTS.index(typing.cast(str, mapping["component"]))
            if (
                mapping["proposal_source_schema_id"] != _CURRENTNESS_SOURCE_SCHEMAS[index]
                or mapping["current_source_schema_id"] != _CURRENTNESS_SOURCE_SCHEMAS[index]
                or (mapping["profile_ref"], mapping["profile_digest"]) != _CURRENTNESS_PROFILES[index]
            ):
                _fail("source_owner_mismatch")
            allowed_pairs = {
                ("current", "exact_ref_digest_profile_and_freshness"),
                ("conflict", "same_ref_different_digest"),
                ("stale", "different_well_formed_source_pair"),
                ("stale", "exact_source_expired_at_evaluation"),
                ("unknown", "source_unavailable"),
                ("conflict", "malformed_or_wrong_profile"),
            }
            if (mapping["result"], mapping["reason"]) not in allowed_pairs:
                _fail("evaluation_contract_mismatch")

        if self._V_NUMBER == "V29":
            components = typing.cast(list[dict[str, object]], mapping["components"])
            if tuple(item["component"] for item in components) != _CURRENTNESS_COMPONENTS:
                _fail("source_owner_mismatch")
            precedence = ("conflict", "stale", "unknown")
            aggregate = next((result for result in precedence if any(item["result"] == result for item in components)), "current")
            outer = {
                "conflict": ("conflict", "component_basis_conflict"),
                "stale": ("stale", "component_source_stale"),
                "unknown": ("unknown", "component_source_unknown"),
                "current": ("current", "all_components_current"),
            }[aggregate]
            if (mapping["result"], mapping["reason"]) != outer:
                _fail("evaluation_contract_mismatch")

        if self._V_NUMBER == "V32":
            if mapping["global_stop_ref"] == "global-stop-clear":
                governed = ("permit", "global_stop_clear")
            elif mapping["global_stop_ref"].startswith("global-stop-unknown"):
                governed = ("unknown", "global_stop_unknown")
            else:
                governed = ("deny", "global_stop_active")
            expected_entries = tuple(
                governed if applicability == "governed" else ("permit", "halt_only_stop_checked")
                for _, applicability, _ in _CANONICAL_BRANCHES
            )
            observed_entries = tuple(
                (entry["result"], entry["reason"])
                for entry in typing.cast(list[dict[str, object]], mapping["entries"])
            )
            if observed_entries != expected_entries:
                _fail("evaluation_contract_mismatch")

        if self._V_NUMBER == "V40":
            locators = typing.cast(list[dict[str, object]], mapping["author_observation_locators"])
            if tuple(item["ordinal"] for item in locators) != tuple(range(len(locators))):
                _fail("relation_mismatch")
            if any(
                item["source_kind"] != "worker"
                or item["source_ref"] != mapping["author_source_ref"]
                or item["source_invocation_ref"] != mapping["author_source_invocation_ref"]
                for item in locators
            ):
                _fail("source_owner_mismatch")
            if mapping["review_source_kind"] != "independent_reviewer" or mapping["author_source_kind"] != "worker":
                derived_separation = ("conflict", "source_role_conflict")
            elif mapping["review_source_invocation_ref"] == mapping["author_source_invocation_ref"]:
                derived_separation = ("not_separate", "review_source_invocation_reused")
            elif (
                mapping["review_effect_intent_ref"] == mapping["author_effect_intent_ref"]
                or mapping["review_effect_fence_ref"] == mapping["author_effect_fence_ref"]
                or mapping["review_effect_fence_digest"] == mapping["author_effect_fence_digest"]
            ):
                derived_separation = ("not_separate", "review_effect_identity_reused")
            elif mapping["review_delivery_attempt_ref"] == mapping["author_delivery_attempt_ref"]:
                derived_separation = ("not_separate", "review_delivery_identity_reused")
            else:
                derived_separation = ("separate", "governed_review_graph_separate")
            if (mapping["status"], mapping["reason"]) != derived_separation:
                _fail("evaluation_contract_mismatch")

        if self._V_NUMBER == "V41":
            _require_whole_second_utc(mapping["not_before"])
            if not mapping["not_before"] <= mapping["evaluated_at"] < mapping["expires_at"]:
                _fail("relation_mismatch")
            ceilings = {field: mapping[field] for field in _CEILING_FIELDS}
            if any(type(value) is not int or typing.cast(int, value) < 0 for value in ceilings.values()):
                _fail("invalid_field_value")
            assertions = typing.cast(list[dict[str, object]], mapping["branch_assertions"])
            for item in assertions:
                if item["applicability"] == "halt_only":
                    expected_assertion = ("permit", "halt_only_policy_not_applicable")
                elif mapping["revocation_status"] == "revoked":
                    expected_assertion = ("deny", "policy_revoked")
                elif mapping["policy_status"] == "unknown":
                    expected_assertion = ("unknown", "policy_status_unknown")
                elif mapping["policy_status"] != "active":
                    expected_assertion = ("unknown", "policy_currentness_unknown")
                elif item["branch"] not in mapping["allowed_branches"]:
                    expected_assertion = ("deny", "branch_not_allowed")
                elif item["governed_effect_class"] not in mapping["allowed_effect_classes"]:
                    expected_assertion = ("deny", "effect_class_not_allowed")
                else:
                    expected_assertion = ("permit", "policy_permits")
                if (item["result"], item["reason"]) != expected_assertion:
                    _fail("evaluation_contract_mismatch")

        if self._V_NUMBER == "V42":
            _require_whole_second_utc(mapping["not_before"])
            if not mapping["not_before"] <= mapping["evaluated_at"] < mapping["expires_at"]:
                _fail("relation_mismatch")
            if mapping["required_risk_lane"] not in mapping["allowed_risk_lanes"]:
                _fail("relation_mismatch")
            assertions = typing.cast(list[dict[str, object]], mapping["branch_assertions"])
            for item in assertions:
                if item["applicability"] == "halt_only":
                    expected_assertion = ("permit", "halt_only_risk_lane_not_applicable")
                elif mapping["revocation_status"] == "revoked":
                    expected_assertion = ("deny", "policy_revoked")
                elif mapping["policy_status"] == "unknown":
                    expected_assertion = ("unknown", "policy_status_unknown")
                elif mapping["policy_status"] != "active":
                    expected_assertion = ("unknown", "policy_currentness_unknown")
                elif mapping["required_risk_lane"] not in mapping["allowed_risk_lanes"]:
                    expected_assertion = ("deny", "required_lane_mismatch")
                else:
                    expected_assertion = ("permit", "risk_lane_permits")
                if (item["result"], item["reason"]) != expected_assertion:
                    _fail("evaluation_contract_mismatch")

        if self._V_NUMBER == "V43":
            if (
                mapping["source_family"] != "versioned_external_risk_source"
                or mapping["source_system_schema_id"] != "governed-execution.nwp-finite-backlog-risk-source-binding.v1"
                or mapping["adapter_profile_ref"] != "finite_backlog_risk_source.v1"
                or mapping["adapter_profile_digest"] != "2ea8aa75234deb0901d3ca0a32d19877da072378e1acd438c901ce5cf1e489bc"
                or mapping["profile_version"] != 1
                or mapping["external_authority_claim"] is not False
            ):
                _fail("source_owner_mismatch")

        if self._V_NUMBER == "V44":
            if mapping["source_profile_schema_id"] != "governed-execution.nwp-post-execution-risk-source-profile.v1":
                _fail("source_owner_mismatch")

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"

    __str__ = __repr__

    def __copy__(self) -> typing.NoReturn:
        raise TypeError("copy disabled")

    def __deepcopy__(self, memo: object) -> typing.NoReturn:
        raise TypeError("copy disabled")

    def __reduce__(self) -> typing.NoReturn:
        raise TypeError("pickling disabled")

    def __reduce_ex__(self, protocol: object) -> typing.NoReturn:
        raise TypeError("pickling disabled")


_CANONICAL_BRANCHES = (
    ("candidate_acceptance", "governed", "author_candidate"),
    ("candidate_repair", "governed", "author_candidate"),
    ("attempt_selecting_replan", "governed", "author_candidate"),
    ("program_terminal_reject", "halt_only", None),
    ("post_execution_program_block", "halt_only", None),
)
_RECOMMENDATION_BRANCHES = {
    "accept_candidate": "candidate_acceptance",
    "repair_candidate": "candidate_repair",
    "replan": "attempt_selecting_replan",
    "terminal_reject": "program_terminal_reject",
    "block": "post_execution_program_block",
}
_CURRENT_OWNER_SEAMS = (
    _cognitive_rows.DevelopmentModelSourceInvocationRowValue,
    _cognitive_values.ModelSourceInvocationV1,
    _requirement_values.DevelopmentValidationRequirementEvidenceV1,
    _requirement_values.DevelopmentReviewRequirementEvidenceV1,
    _c1_contracts.membership_digest,
    _c1_values.RW0C1Section41PostExecutionProposalFamilyMemberV1,
    _phase_values.RW0EffectHostQualificationV1,
    _worker_values.AttemptFenceV1,
    _GlobalStopState,
)


_INDEPENDENT_REVIEW_DISPOSITION_PROFILE_REF = 'independent-review-disposition.v1'
_INDEPENDENT_REVIEW_DISPOSITION_PROFILE_DIGEST = 'c5a87ab332790e95f4cd0fb4790149115e8b15a5e4cd0786272cc535b1b23a78'
_POST_EXECUTION_EVIDENCE_SUPPLY_PROFILE_REF = 'post-execution-evidence-supply.v2'
_POST_EXECUTION_EVIDENCE_SUPPLY_PROFILE_DIGEST = '59a4a741fb394767f341dc57c514bb3e022737196905c7bed1f05295376d3a02'
_POST_EXECUTION_GLOBAL_STOP_PROFILE_REF = 'post-execution-global-stop.v1'
_POST_EXECUTION_GLOBAL_STOP_PROFILE_DIGEST = '5f2be30f5f081f5c159596375ba872bc08e012e389706b084a79b21baaab9142'
_POST_EXECUTION_MODEL_INPUT_BINDING_PROFILE_REF = 'post-execution-model-input-binding.v2'
_POST_EXECUTION_MODEL_INPUT_BINDING_PROFILE_DIGEST = '1bbc54604228066b13aa6cbed7cb98b1962a2a4f63920938cf9e824faf253bbb'
_POST_EXECUTION_REVIEW_RESULT_SET_PROFILE_REF = 'post-execution-review-result-set.v1'
_POST_EXECUTION_REVIEW_RESULT_SET_PROFILE_DIGEST = '2dd40a8e0c3628f9e0e3860acc29c0ee908111ce14c7e8dccf944e4b1e9d9730'
_POST_EXECUTION_REVIEWER_SEPARATION_PROFILE_REF = 'post-execution-reviewer-separation-evaluation.v1'
_POST_EXECUTION_REVIEWER_SEPARATION_PROFILE_DIGEST = '477867ca6eecb36bd77629452489637ef43af2d79c97ffb72b5cce0969d80a2f'
_POST_EXECUTION_SEMANTIC_REVIEW_INPUT_PROFILE_REF = 'post-execution-semantic-review-input.v2'
_POST_EXECUTION_SEMANTIC_REVIEW_INPUT_PROFILE_DIGEST = 'd4693a9cd9beb9d58edf2e492176182b69b5ed2fa8da34419709e2392333e54e'
_POST_EXECUTION_SOURCE_EFFECT_CEILING_PROFILE_REF = 'post-execution-source-effect-ceiling.v1'
_POST_EXECUTION_SOURCE_EFFECT_CEILING_PROFILE_DIGEST = '6aa721b81b9b341e0e5b3ce3bc10590641dd4d4f50c056ae65e8dc4b605eff1a'
_POST_EXECUTION_SUPPORT_SET_PROFILE_REF = 'post-execution-support-set.v1'
_POST_EXECUTION_SUPPORT_SET_PROFILE_DIGEST = 'dc2428d307d9ebb5bcff78fa494a70339a7a57a330a2a8c8fce284f971b8ab52'
_POST_EXECUTION_VALIDATION_RESULT_SET_PROFILE_REF = 'post-execution-validation-result-set.v1'
_POST_EXECUTION_VALIDATION_RESULT_SET_PROFILE_DIGEST = 'cff49323050cd70855d7fda9b8bcc2666da18a7a3f30f8d8e030a9d60b087d58'
_VALIDATION_DISPOSITION_PROFILE_REF = 'validation-disposition.v1'
_VALIDATION_DISPOSITION_PROFILE_DIGEST = '65a2af00efe0fd6d83cafe5c713536c12e71814544c342d907ef62a2f3cb4048'

Section41PostExecutionSemanticReviewLineageContextV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'Section41PostExecutionSemanticReviewLineageContextV1', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V01',
 'schema_id': 'governed-execution.nwp-section41-post-execution-semantic-review-lineage-context.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-section41-post-execution-semantic-review-lineage-context.v1',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'proposal_phase', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'program_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'program_version_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'program_version_number',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'accepted_intent_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'semantic_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'semantic_attempt_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_number',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'candidate_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'basis_decision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'basis_decision_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_spec_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_spec_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_spec_safe_projection_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_intent_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_intent_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_command_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_command_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'standing_grant_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'standing_grant_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_authorization_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_authorization_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_authorization_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_authorization_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'delivery_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'delivery_envelope_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'delivery_attempt_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'authority_evaluation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'authority_evaluation_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': 'd4693a9cd9beb9d58edf2e492176182b69b5ed2fa8da34419709e2392333e54e',
                            'profile_ref': 'post-execution-semantic-review-input.v2'},
 'reference_posture': {'domain': 'governed-execution.nwp-section41-post-execution-semantic-review-lineage-context-reference.v1.identity',
                       'field': 'lineage_context_ref',
                       'posture': 'generated',
                       'prefix': 'section41-post-lineage.',
                       'preimage_fields': ['proposal_phase',
                                           'program_ref',
                                           'program_version_ref',
                                           'program_version_number',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'semantic_attempt_digest',
                                           'attempt_number',
                                           'candidate_ref',
                                           'basis_decision_ref',
                                           'basis_decision_digest',
                                           'work_spec_ref',
                                           'work_spec_digest',
                                           'work_spec_safe_projection_digest',
                                           'effect_intent_ref',
                                           'effect_intent_digest',
                                           'author_command_ref',
                                           'author_command_digest',
                                           'standing_grant_ref',
                                           'standing_grant_digest',
                                           'attempt_authorization_ref',
                                           'attempt_authorization_digest',
                                           'effect_authorization_ref',
                                           'effect_authorization_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'delivery_attempt_ref',
                                           'delivery_envelope_digest',
                                           'delivery_attempt_digest',
                                           'authority_evaluation_ref',
                                           'authority_evaluation_digest']},
 'digest_posture': {'domain': 'governed-execution.nwp-section41-post-execution-semantic-review-lineage-context.v1.identity',
                    'field': 'lineage_context_digest',
                    'self_exclusion': ['lineage_context_digest']}},
        nested={},
        meta={},
    ),
)


PostExecutionSemanticReviewRoleEntryV2 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionSemanticReviewRoleEntryV2', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V03',
 'schema_id': 'governed-execution.nwp-post-execution-semantic-review-role-entry.v2',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-semantic-review-role-entry.v2',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'role',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'role_rank',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'ordinal',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'typed_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'typed_value_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'typed_value_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_posture', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'branch_rule': 'non_null_only_for_roles_with_direct_c1_in_governing_profile;otherwise_null',
                     'name': 'direct_c1_kind',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_direct_c1_in_governing_profile;otherwise_null',
                     'name': 'direct_c1_kind_rank',
                     'nullable': True,
                     'type': 'exact_builtin_int_bool_rejected_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_direct_c1_in_governing_profile;otherwise_null',
                     'name': 'direct_c1_membership_ref',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_direct_c1_in_governing_profile;otherwise_null',
                     'name': 'direct_c1_membership_digest',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_source_profile_in_governing_profile;otherwise_null',
                     'name': 'source_profile_ref',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_source_profile_in_governing_profile;otherwise_null',
                     'name': 'source_profile_digest',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
                     'name': 'source_binding_schema_id',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
                     'name': 'source_binding_ref',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
                     'name': 'source_binding_digest',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'name': 'model_input_posture',
                     'nullable': False,
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': 'd4693a9cd9beb9d58edf2e492176182b69b5ed2fa8da34419709e2392333e54e',
                            'profile_ref': 'post-execution-semantic-review-input.v2'},
 'reference_posture': {'posture': 'parent_bound_or_no_standalone_ref'},
 'digest_posture': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
        nested={},
        meta={},
    ),
)


CandidateCapsuleSafeProjectionV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'CandidateCapsuleSafeProjectionV1', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V04',
 'schema_id': 'governed-execution.nwp-candidate-capsule-safe-projection.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-candidate-capsule-safe-projection.v1',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'candidate_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'capsule_manifest_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'portable_capsule_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'program_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'program_version_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'accepted_intent_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'semantic_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_intent_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'command_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'command_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'repository_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'base_git_object_format',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'base_git_oid', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'authorized_path_scope_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'projection_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'projection_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': 'd4693a9cd9beb9d58edf2e492176182b69b5ed2fa8da34419709e2392333e54e',
                            'profile_ref': 'post-execution-semantic-review-input.v2'},
 'reference_posture': {'domain': 'governed-execution.nwp-candidate-capsule-safe-projection-reference.v1.identity',
                       'field': 'projection_ref',
                       'posture': 'generated',
                       'prefix': 'candidate-safe-projection.',
                       'preimage_fields': ['candidate_ref',
                                           'capsule_manifest_ref',
                                           'portable_capsule_digest',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'effect_intent_ref',
                                           'command_ref',
                                           'command_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'repository_ref',
                                           'base_git_object_format',
                                           'base_git_oid',
                                           'authorized_path_scope_digest']},
 'digest_posture': {'domain': 'governed-execution.nwp-candidate-capsule-safe-projection.v1.identity',
                    'field': 'projection_digest',
                    'self_exclusion': ['projection_digest']}},
        nested={},
        meta={},
    ),
)


PostExecutionModelInputProjectionEntryV2 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionModelInputProjectionEntryV2', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V06',
 'schema_id': 'governed-execution.nwp-post-execution-model-input-projection-entry.v2',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-model-input-projection-entry.v2',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'role',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'role_rank',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'ordinal',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'typed_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'typed_value_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'typed_value_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'model_value_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'model_value_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'model_value_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'model_input_posture',
                     'nullable': False,
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': 'd4693a9cd9beb9d58edf2e492176182b69b5ed2fa8da34419709e2392333e54e',
                            'profile_ref': 'post-execution-semantic-review-input.v2'},
 'reference_posture': {'posture': 'parent_bound_or_no_standalone_ref'},
 'digest_posture': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
        nested={},
        meta={},
    ),
)


PostExecutionModelInputSafeProjectionV2 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionModelInputSafeProjectionV2', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V05',
 'schema_id': 'governed-execution.nwp-post-execution-model-input-safe-projection.v2',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-model-input-safe-projection.v2',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'proposal_phase', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'entry_count',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'cardinality': 9,
                     'name': 'entries',
                     'nullable': False,
                     'ordering': 'literal_owner_order;duplicates_rejected_when_profile_requires',
                     'type': 'exact_builtin_list'},
                    {'name': 'projection_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'projection_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': 'd4693a9cd9beb9d58edf2e492176182b69b5ed2fa8da34419709e2392333e54e',
                            'profile_ref': 'post-execution-semantic-review-input.v2'},
 'reference_posture': {'domain': 'governed-execution.nwp-post-execution-model-input-safe-projection-reference.v2.identity',
                       'field': 'projection_ref',
                       'posture': 'generated',
                       'prefix': 'post-model-input-projection-v2.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'proposal_phase',
                                           'lineage_context_schema_id',
                                           'lineage_context_ref',
                                           'lineage_context_digest',
                                           'entry_count',
                                           'entries']},
 'digest_posture': {'domain': 'governed-execution.nwp-post-execution-model-input-safe-projection.v2.identity',
                    'field': 'projection_digest',
                    'self_exclusion': ['projection_digest']}},
        nested={'entries': PostExecutionModelInputProjectionEntryV2},
        meta={},
    ),
)


PostExecutionPrivateInputManifestEntryV2 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionPrivateInputManifestEntryV2', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V08',
 'schema_id': 'governed-execution.nwp-post-execution-private-input-manifest-entry.v2',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-private-input-manifest-entry.v2',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'role',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'role_rank',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'ordinal',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'typed_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'typed_value_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'typed_value_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'canonical_byte_length',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'privacy_classification',
                     'nullable': False,
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': 'd4693a9cd9beb9d58edf2e492176182b69b5ed2fa8da34419709e2392333e54e',
                            'profile_ref': 'post-execution-semantic-review-input.v2'},
 'reference_posture': {'posture': 'parent_bound_or_no_standalone_ref'},
 'digest_posture': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
        nested={},
        meta={},
    ),
)


PostExecutionPrivateInputManifestV2 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionPrivateInputManifestV2', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V07',
 'schema_id': 'governed-execution.nwp-post-execution-private-input-manifest.v2',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-private-input-manifest.v2',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'proposal_phase', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'entry_count',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'cardinality': 1,
                     'name': 'entries',
                     'nullable': False,
                     'ordering': 'literal_owner_order;duplicates_rejected_when_profile_requires',
                     'type': 'exact_builtin_list'},
                    {'name': 'manifest_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'manifest_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': 'd4693a9cd9beb9d58edf2e492176182b69b5ed2fa8da34419709e2392333e54e',
                            'profile_ref': 'post-execution-semantic-review-input.v2'},
 'reference_posture': {'domain': 'governed-execution.nwp-post-execution-private-input-manifest-reference.v2.identity',
                       'field': 'manifest_ref',
                       'posture': 'generated',
                       'prefix': 'post-private-input-manifest-v2.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'proposal_phase',
                                           'lineage_context_schema_id',
                                           'lineage_context_ref',
                                           'lineage_context_digest',
                                           'entry_count',
                                           'entries']},
 'digest_posture': {'domain': 'governed-execution.nwp-post-execution-private-input-manifest.v2.identity',
                    'field': 'manifest_digest',
                    'self_exclusion': ['manifest_digest']}},
        nested={'entries': PostExecutionPrivateInputManifestEntryV2},
        meta={},
    ),
)


PostExecutionSemanticReviewInputContextV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionSemanticReviewInputContextV1', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V02',
 'schema_id': 'governed-execution.nwp-post-execution-semantic-review-context.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-semantic-review-context.v1',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'input_context_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'proposal_phase', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'phase_basis_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'phase_basis_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'preassigned_proposal_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'role_entry_count',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'cardinality': 9,
                     'name': 'role_entries',
                     'nullable': False,
                     'ordering': 'literal_owner_order;duplicates_rejected_when_profile_requires',
                     'type': 'exact_builtin_list'},
                    {'name': 'model_input_safe_projection_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'model_input_safe_projection_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'model_input_safe_projection_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'private_input_manifest_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'private_input_manifest_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'private_input_manifest_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'constructed_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'input_context_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': 'd4693a9cd9beb9d58edf2e492176182b69b5ed2fa8da34419709e2392333e54e',
                            'profile_ref': 'post-execution-semantic-review-input.v2'},
 'reference_posture': {'domain': 'governed-execution.nwp-post-execution-semantic-review-input-context-reference.v1.identity',
                       'field': 'input_context_ref',
                       'posture': 'generated',
                       'prefix': 'post-semantic-input-context.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'proposal_phase',
                                           'lineage_context_schema_id',
                                           'lineage_context_ref',
                                           'lineage_context_digest',
                                           'phase_basis_ref',
                                           'phase_basis_digest',
                                           'preassigned_proposal_ref',
                                           'role_entry_count',
                                           'role_entries',
                                           'model_input_safe_projection_schema_id',
                                           'model_input_safe_projection_ref',
                                           'model_input_safe_projection_digest',
                                           'private_input_manifest_schema_id',
                                           'private_input_manifest_ref',
                                           'private_input_manifest_digest',
                                           'constructed_at']},
 'digest_posture': {'domain': 'governed-execution.nwp-post-execution-semantic-review-context.v1.identity',
                    'field': 'input_context_digest',
                    'self_exclusion': ['input_context_digest']}},
        nested={'role_entries': PostExecutionSemanticReviewRoleEntryV2},
        meta={},
    ),
)


PostExecutionModelInputBindingV2 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionModelInputBindingV2', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V09',
 'schema_id': 'governed-execution.nwp-post-execution-model-input-binding.v2',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-model-input-binding.v2',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'input_context_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'input_context_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'input_context_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'lineage_context_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'model_input_safe_projection_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'model_input_safe_projection_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'model_input_safe_projection_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'private_input_manifest_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'private_input_manifest_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'private_input_manifest_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_invocation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_invocation_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'model_contract_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'model_contract_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'model_configuration_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'model_configuration_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'artifact_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'artifact_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'artifact_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'artifact_binding_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'artifact_safe_projection_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'artifact_safe_projection_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'proposal_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'proposal_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'evidence_set_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'evidence_set_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_invocation_started_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_invocation_completed_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'artifact_validated_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'result',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'reason',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'binding_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'binding_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': '1bbc54604228066b13aa6cbed7cb98b1962a2a4f63920938cf9e824faf253bbb',
                            'profile_ref': 'post-execution-model-input-binding.v2'},
 'reference_posture': {'domain': 'governed-execution.nwp-post-execution-model-input-binding.v2.key',
                       'field': 'binding_ref',
                       'posture': 'generated',
                       'prefix': 'post-model-input-binding-v2.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'input_context_schema_id',
                                           'input_context_ref',
                                           'input_context_digest',
                                           'lineage_context_schema_id',
                                           'lineage_context_ref',
                                           'lineage_context_digest',
                                           'model_input_safe_projection_schema_id',
                                           'model_input_safe_projection_ref',
                                           'model_input_safe_projection_digest',
                                           'private_input_manifest_schema_id',
                                           'private_input_manifest_ref',
                                           'private_input_manifest_digest',
                                           'source_invocation_ref',
                                           'source_invocation_digest',
                                           'model_contract_ref',
                                           'model_contract_digest',
                                           'model_configuration_ref',
                                           'model_configuration_digest',
                                           'artifact_schema_id',
                                           'artifact_ref',
                                           'artifact_digest',
                                           'artifact_binding_digest',
                                           'artifact_safe_projection_schema_id',
                                           'artifact_safe_projection_digest',
                                           'proposal_ref',
                                           'proposal_digest',
                                           'evidence_set_ref',
                                           'evidence_set_digest',
                                           'source_invocation_started_at',
                                           'source_invocation_completed_at',
                                           'artifact_validated_at',
                                           'result',
                                           'reason']},
 'digest_posture': {'domain': 'governed-execution.nwp-post-execution-model-input-binding.v2.identity',
                    'field': 'binding_digest',
                    'self_exclusion': ['binding_digest']}},
        nested={},
        meta={},
    ),
)


PostExecutionRoleSupplyV2 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionRoleSupplyV2', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V11',
 'schema_id': 'governed-execution.nwp-post-execution-role-supply.v2',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-role-supply.v2',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'role',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'role_rank',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'ordinal',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'typed_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'typed_value_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'typed_value_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'typed_canonical_value',
                     'nullable': False,
                     'type': 'exact_builtin_dict',
                     'unknown_nested_fields': 'reject'},
                    {'branch_rule': 'non_null_only_for_roles_with_source_profile_in_governing_profile;otherwise_null',
                     'name': 'source_profile_ref',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_source_profile_in_governing_profile;otherwise_null',
                     'name': 'source_profile_digest',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_source_profile_in_governing_profile;otherwise_null',
                     'name': 'source_profile_canonical_value',
                     'nullable': True,
                     'type': 'exact_builtin_dict_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
                     'name': 'source_binding_schema_id',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
                     'name': 'source_binding_ref',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
                     'name': 'source_binding_digest',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_source_binding_in_governing_profile;otherwise_null',
                     'name': 'source_binding_canonical_value',
                     'nullable': True,
                     'type': 'exact_builtin_dict_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_support_set_in_governing_profile;otherwise_null',
                     'name': 'support_set_ref',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_support_set_in_governing_profile;otherwise_null',
                     'name': 'support_set_digest',
                     'nullable': True,
                     'type': 'exact_builtin_str_or_exact_null'},
                    {'branch_rule': 'non_null_only_for_roles_with_support_set_in_governing_profile;otherwise_null',
                     'name': 'support_set_canonical_value',
                     'nullable': True,
                     'type': 'exact_builtin_dict_or_exact_null'},
                    {'name': 'support_value_count',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'support_canonical_values',
                     'nullable': False,
                     'rule': {'branch_rule': 'support_set_is_null_iff_support_value_count_is_zero_and_values_are_empty',
                              'count_equality': 'length_equals_support_value_count',
                              'item_type': 'exact_builtin_dict',
                              'maximum': 16,
                              'minimum': 0,
                              'ordering': 'exact_support_set_entry_order',
                              'value_equality': 'non_null_support_set_length_and_each_value_match_entry_schema_ref_digest_in_order'},
                     'type': 'exact_builtin_list'},
                    {'name': 'model_input_posture',
                     'nullable': False,
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': '59a4a741fb394767f341dc57c514bb3e022737196905c7bed1f05295376d3a02',
                            'profile_ref': 'post-execution-evidence-supply.v2'},
 'reference_posture': {'posture': 'parent_bound_or_no_standalone_ref'},
 'digest_posture': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
        nested={},
        meta={},
    ),
)


PostExecutionEvidenceSupplyV2 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionEvidenceSupplyV2', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V10',
 'schema_id': 'governed-execution.nwp-post-execution-evidence-supply.v2',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-evidence-supply.v2',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'input_context',
                     'nullable': False,
                     'type': 'exact_builtin_dict',
                     'unknown_nested_fields': 'reject'},
                    {'name': 'model_input_safe_projection',
                     'nullable': False,
                     'type': 'exact_builtin_dict',
                     'unknown_nested_fields': 'reject'},
                    {'name': 'private_input_manifest',
                     'nullable': False,
                     'type': 'exact_builtin_dict',
                     'unknown_nested_fields': 'reject'},
                    {'name': 'role_supply_count',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'cardinality': 9,
                     'name': 'role_supplies',
                     'nullable': False,
                     'ordering': 'literal_owner_order;duplicates_rejected_when_profile_requires',
                     'type': 'exact_builtin_list'},
                    {'name': 'supply_created_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'supply_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'supply_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': '59a4a741fb394767f341dc57c514bb3e022737196905c7bed1f05295376d3a02',
                            'profile_ref': 'post-execution-evidence-supply.v2'},
 'reference_posture': {'domain': 'governed-execution.nwp-post-execution-evidence-supply.v2.key',
                       'field': 'supply_ref',
                       'posture': 'generated',
                       'prefix': 'post-evidence-supply-v2.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'input_context',
                                           'model_input_safe_projection',
                                           'private_input_manifest',
                                           'role_supply_count',
                                           'role_supplies',
                                           'supply_created_at']},
 'digest_posture': {'domain': 'governed-execution.nwp-post-execution-evidence-supply.v2.identity',
                    'field': 'supply_digest',
                    'self_exclusion': ['supply_digest']}},
        nested={'input_context': PostExecutionSemanticReviewInputContextV1, 'model_input_safe_projection': PostExecutionModelInputSafeProjectionV2, 'private_input_manifest': PostExecutionPrivateInputManifestV2, 'role_supplies': PostExecutionRoleSupplyV2},
        meta={},
    ),
)


PostExecutionSupportEntryV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionSupportEntryV1', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V12',
 'schema_id': 'governed-execution.nwp-post-execution-support-entry.v1',
 'ordered_fields': [{'name': 'role',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'rank',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'ordinal',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'source_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'source_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': 'dc2428d307d9ebb5bcff78fa494a70339a7a57a330a2a8c8fce284f971b8ab52',
                            'profile_ref': 'post-execution-support-set.v1'},
 'reference_posture': {'posture': 'parent_bound_or_no_standalone_ref'},
 'digest_posture': {'posture': 'parent_bound_or_no_standalone_self_digest'}},
        nested={},
        meta={},
    ),
)


PostExecutionSupportSetV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionSupportSetV1', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V13',
 'schema_id': 'governed-execution.nwp-post-execution-support-set.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-support-set.v1',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'entries',
                     'nullable': False,
                     'rule': {'count_equality': 'length_equals_owner_inventory_by_consumer_entry_count_for_profile_ref',
                              'duplicates': 'reject_repeated_role_rank_ordinal_or_unapproved_repeated_source_pair',
                              'item_type': 'PostExecutionSupportEntryV1',
                              'maximum': 16,
                              'minimum': 1,
                              'ordering': 'exact_owner_inventory_by_consumer_order',
                              'value_equality': 'equals_literal_owner_inventory_by_consumer_for_profile_ref'},
                     'type': 'exact_builtin_list'},
                    {'name': 'support_set_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'support_set_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': 'dc2428d307d9ebb5bcff78fa494a70339a7a57a330a2a8c8fce284f971b8ab52',
                            'profile_ref': 'post-execution-support-set.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-post-execution-support-set.v1.key',
                       'field': 'support_set_ref',
                       'posture': 'generated',
                       'prefix': 'post-support-set.',
                       'preimage_fields': ['profile_ref', 'profile_digest', 'entries']},
 'digest_posture': {'domain': 'governed-execution.nwp-post-execution-support-set.v1.identity',
                    'field': 'support_set_digest',
                    'self_exclusion': ['support_set_digest']}},
        nested={'entries': PostExecutionSupportEntryV1},
        meta={},
    ),
)


ValidationDispositionV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'ValidationDispositionV1', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V14',
 'schema_id': 'governed-execution.nwp-validation-disposition.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-validation-disposition.v1',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'disposition_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_observation_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'source_observation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_observation_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'delivery_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_kind',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_invocation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'observation_kind',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_outcome', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'source_reason_code', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'source_evidence_refs',
                     'nullable': False,
                     'rule': {'duplicates': 'reject',
                              'item_type': 'exact_builtin_str_safe_ref',
                              'maximum': 32,
                              'minimum': 0,
                              'ordering': 'strict_lexicographic',
                              'value_equality': 'equals_exact_current_source_observation_source_evidence_refs'},
                     'type': 'exact_builtin_list'},
                    {'name': 'source_observed_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_role', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'program_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'program_version_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'accepted_intent_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'semantic_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'semantic_attempt_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_number',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'candidate_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'capsule_manifest_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'portable_capsule_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'command_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'command_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_intent_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_class',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'validation_tool_profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'validation_tool_profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'validation_tool_qualification_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'validation_tool_qualification_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'validation_tool_qualification_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'validation_requirement_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'validation_requirement_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'validation_requirement_safe_evidence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'validation_requirement_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'validation_requirement_work_spec_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'validation_requirement_work_spec_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'validation_result_set_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'validation_result_set_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'validation_result_set_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'result',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'reason',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'repairability', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'evaluated_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'expires_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'support_set_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'support_set_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'disposition_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': '65a2af00efe0fd6d83cafe5c713536c12e71814544c342d907ef62a2f3cb4048',
                            'profile_ref': 'validation-disposition.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-validation-disposition.v1.key',
                       'field': 'disposition_ref',
                       'posture': 'generated',
                       'prefix': 'validation-disposition.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'source_observation_schema_id',
                                           'source_observation_ref',
                                           'source_observation_digest',
                                           'delivery_attempt_ref',
                                           'source_kind',
                                           'source_ref',
                                           'source_invocation_ref',
                                           'observation_kind',
                                           'source_outcome',
                                           'source_reason_code',
                                           'source_evidence_refs',
                                           'source_observed_at',
                                           'author_role',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'semantic_attempt_digest',
                                           'attempt_number',
                                           'candidate_ref',
                                           'capsule_manifest_ref',
                                           'portable_capsule_digest',
                                           'command_ref',
                                           'command_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'effect_intent_ref',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'effect_class',
                                           'validation_tool_profile_ref',
                                           'validation_tool_profile_digest',
                                           'validation_tool_qualification_schema_id',
                                           'validation_tool_qualification_ref',
                                           'validation_tool_qualification_digest',
                                           'validation_requirement_schema_id',
                                           'validation_requirement_ref',
                                           'validation_requirement_safe_evidence_digest',
                                           'validation_requirement_digest',
                                           'validation_requirement_work_spec_ref',
                                           'validation_requirement_work_spec_digest',
                                           'validation_result_set_schema_id',
                                           'validation_result_set_ref',
                                           'validation_result_set_digest',
                                           'result',
                                           'reason',
                                           'repairability',
                                           'evaluated_at',
                                           'expires_at',
                                           'support_set_ref',
                                           'support_set_digest']},
 'digest_posture': {'domain': 'governed-execution.nwp-validation-disposition.v1.identity',
                    'field': 'disposition_digest',
                    'self_exclusion': ['disposition_digest']}},
        nested={},
        meta={},
    ),
)


IndependentReviewDispositionV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'IndependentReviewDispositionV1', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V15',
 'schema_id': 'governed-execution.nwp-independent-review-disposition.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-independent-review-disposition.v1',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'disposition_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_observation_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'source_observation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_observation_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'delivery_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_kind',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_invocation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'observation_kind',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_outcome', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'source_reason_code', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'source_evidence_refs',
                     'nullable': False,
                     'rule': {'duplicates': 'reject',
                              'item_type': 'exact_builtin_str_safe_ref',
                              'maximum': 32,
                              'minimum': 0,
                              'ordering': 'strict_lexicographic',
                              'value_equality': 'equals_exact_current_source_observation_source_evidence_refs'},
                     'type': 'exact_builtin_list'},
                    {'name': 'source_observed_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_role', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'program_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'program_version_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'accepted_intent_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'semantic_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'semantic_attempt_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_number',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'candidate_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'capsule_manifest_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'portable_capsule_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'command_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'command_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_intent_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_class',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_tool_profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_tool_profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_tool_qualification_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'review_tool_qualification_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_tool_qualification_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_requirement_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'review_requirement_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_requirement_safe_evidence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_requirement_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_requirement_work_spec_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_requirement_work_spec_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_result_set_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'review_result_set_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_result_set_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'reviewer_separation_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'reviewer_separation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'reviewer_separation_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'separation_status', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'result',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'reason',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'evaluated_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'expires_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'support_set_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'support_set_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'disposition_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': 'c5a87ab332790e95f4cd0fb4790149115e8b15a5e4cd0786272cc535b1b23a78',
                            'profile_ref': 'independent-review-disposition.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-independent-review-disposition.v1.key',
                       'field': 'disposition_ref',
                       'posture': 'generated',
                       'prefix': 'independent-review-disposition.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'source_observation_schema_id',
                                           'source_observation_ref',
                                           'source_observation_digest',
                                           'delivery_attempt_ref',
                                           'source_kind',
                                           'source_ref',
                                           'source_invocation_ref',
                                           'observation_kind',
                                           'source_outcome',
                                           'source_reason_code',
                                           'source_evidence_refs',
                                           'source_observed_at',
                                           'author_role',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'semantic_attempt_digest',
                                           'attempt_number',
                                           'candidate_ref',
                                           'capsule_manifest_ref',
                                           'portable_capsule_digest',
                                           'command_ref',
                                           'command_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'effect_intent_ref',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'effect_class',
                                           'review_tool_profile_ref',
                                           'review_tool_profile_digest',
                                           'review_tool_qualification_schema_id',
                                           'review_tool_qualification_ref',
                                           'review_tool_qualification_digest',
                                           'review_requirement_schema_id',
                                           'review_requirement_ref',
                                           'review_requirement_safe_evidence_digest',
                                           'review_requirement_digest',
                                           'review_requirement_work_spec_ref',
                                           'review_requirement_work_spec_digest',
                                           'review_result_set_schema_id',
                                           'review_result_set_ref',
                                           'review_result_set_digest',
                                           'reviewer_separation_schema_id',
                                           'reviewer_separation_ref',
                                           'reviewer_separation_digest',
                                           'separation_status',
                                           'result',
                                           'reason',
                                           'evaluated_at',
                                           'expires_at',
                                           'support_set_ref',
                                           'support_set_digest']},
 'digest_posture': {'domain': 'governed-execution.nwp-independent-review-disposition.v1.identity',
                    'field': 'disposition_digest',
                    'self_exclusion': ['disposition_digest']}},
        nested={},
        meta={},
    ),
)


PostExecutionGlobalStopSnapshotV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionGlobalStopSnapshotV1', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V20',
 'schema_id': 'governed-execution.nwp-post-execution-global-stop-snapshot.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-global-stop-snapshot.v1',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'global_stop_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'global_stop_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'global_stop_version',
                     'nullable': False,
                     'rule': 'bounded_by_governing_profile;bool_rejected',
                     'type': 'exact_builtin_int_bool_rejected'},
                    {'name': 'global_stop_state', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'branch_rule': 'null_only_in_the_literal_profile_branch_exhibited_by_the_golden_value',
                     'name': 'global_stop_stop_id',
                     'nullable': True,
                     'type': 'exact_null'},
                    {'branch_rule': 'null_only_in_the_literal_profile_branch_exhibited_by_the_golden_value',
                     'name': 'global_stop_reason_class',
                     'nullable': True,
                     'type': 'exact_null'},
                    {'branch_rule': 'null_only_in_the_literal_profile_branch_exhibited_by_the_golden_value',
                     'name': 'global_stop_issuer_ref',
                     'nullable': True,
                     'type': 'exact_null'},
                    {'branch_rule': 'null_only_in_the_literal_profile_branch_exhibited_by_the_golden_value',
                     'name': 'global_stop_issued_at',
                     'nullable': True,
                     'type': 'exact_null'},
                    {'branch_rule': 'null_only_in_the_literal_profile_branch_exhibited_by_the_golden_value',
                     'name': 'global_stop_operator_decision_ref',
                     'nullable': True,
                     'type': 'exact_null'},
                    {'name': 'global_stop_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'global_stop_updated_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'evaluated_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'support_set_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'support_set_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'snapshot_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'snapshot_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': '5f2be30f5f081f5c159596375ba872bc08e012e389706b084a79b21baaab9142',
                            'profile_ref': 'post-execution-global-stop.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-post-execution-global-stop-snapshot.v1.key',
                       'field': 'snapshot_ref',
                       'posture': 'generated',
                       'prefix': 'post-global-stop-snapshot.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'global_stop_schema_id',
                                           'global_stop_ref',
                                           'global_stop_version',
                                           'global_stop_state',
                                           'global_stop_stop_id',
                                           'global_stop_reason_class',
                                           'global_stop_issuer_ref',
                                           'global_stop_issued_at',
                                           'global_stop_operator_decision_ref',
                                           'global_stop_digest',
                                           'global_stop_updated_at',
                                           'evaluated_at',
                                           'support_set_ref',
                                           'support_set_digest']},
 'digest_posture': {'domain': 'governed-execution.nwp-post-execution-global-stop-snapshot.v1.identity',
                    'field': 'snapshot_digest',
                    'self_exclusion': ['snapshot_digest']}},
        nested={},
        meta={},
    ),
)


PostExecutionSourceEffectCeilingEvidenceV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionSourceEffectCeilingEvidenceV1', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V21',
 'schema_id': 'governed-execution.nwp-post-execution-source-effect-ceiling-evidence.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-source-effect-ceiling-evidence.v1',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'proposal_phase', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'program_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'program_version_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'accepted_intent_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'semantic_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'candidate_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_intent_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'repository_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'base_git_object_format',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'base_git_oid', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'source_effect_class', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'source_effect_ceilings',
                     'nullable': False,
                     'type': 'exact_builtin_dict',
                     'unknown_nested_fields': 'reject'},
                    {'name': 'path_scope_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_allowed_effect_classes',
                     'nullable': False,
                     'rule': {'duplicates': 'reject',
                              'item_type': 'exact_builtin_str_enum',
                              'maximum': 5,
                              'minimum': 1,
                              'ordering': 'strict_lexicographic_current_effect_class_order',
                              'subset_of': 'current_effect_classes'},
                     'type': 'exact_builtin_list'},
                    {'name': 'attempt_ceilings',
                     'nullable': False,
                     'type': 'exact_builtin_dict',
                     'unknown_nested_fields': 'reject'},
                    {'name': 'attempt_fence_expires_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_class', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'effect_ceilings',
                     'nullable': False,
                     'type': 'exact_builtin_dict',
                     'unknown_nested_fields': 'reject'},
                    {'name': 'effect_fence_expires_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'authority_schema_id', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'authority_observation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'authority_observation_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'authority_status', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'authority_family_status',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'authority_revocation_status',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'authority_allowed_effect_classes',
                     'nullable': False,
                     'rule': {'duplicates': 'reject',
                              'item_type': 'exact_builtin_str_enum',
                              'maximum': 5,
                              'minimum': 1,
                              'ordering': 'strict_lexicographic_current_effect_class_order',
                              'subset_of': 'current_effect_classes'},
                     'type': 'exact_builtin_list'},
                    {'name': 'authority_ceilings',
                     'nullable': False,
                     'type': 'exact_builtin_dict',
                     'unknown_nested_fields': 'reject'},
                    {'name': 'authority_grant_expires_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'authority_observation_expires_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'evaluated_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'result',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'reason',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'support_set_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'support_set_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'evidence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'evidence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': '6aa721b81b9b341e0e5b3ce3bc10590641dd4d4f50c056ae65e8dc4b605eff1a',
                            'profile_ref': 'post-execution-source-effect-ceiling.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-post-execution-source-effect-ceiling-evidence.v1.key',
                       'field': 'evidence_ref',
                       'posture': 'generated',
                       'prefix': 'post-source-effect-ceiling.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'proposal_phase',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'candidate_ref',
                                           'effect_intent_ref',
                                           'repository_ref',
                                           'base_git_object_format',
                                           'base_git_oid',
                                           'source_effect_class',
                                           'source_effect_ceilings',
                                           'path_scope_digest',
                                           'attempt_fence_schema_id',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'attempt_allowed_effect_classes',
                                           'attempt_ceilings',
                                           'attempt_fence_expires_at',
                                           'effect_fence_schema_id',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'effect_fence_class',
                                           'effect_ceilings',
                                           'effect_fence_expires_at',
                                           'authority_schema_id',
                                           'authority_observation_ref',
                                           'authority_observation_digest',
                                           'authority_status',
                                           'authority_family_status',
                                           'authority_revocation_status',
                                           'authority_allowed_effect_classes',
                                           'authority_ceilings',
                                           'authority_grant_expires_at',
                                           'authority_observation_expires_at',
                                           'evaluated_at',
                                           'result',
                                           'reason',
                                           'support_set_ref',
                                           'support_set_digest']},
 'digest_posture': {'domain': 'governed-execution.nwp-post-execution-source-effect-ceiling-evidence.v1.identity',
                    'field': 'evidence_digest',
                    'self_exclusion': ['evidence_digest']}},
        nested={},
        meta={},
    ),
)


PostExecutionValidationResultSetV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionValidationResultSetV1', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V38',
 'schema_id': 'governed-execution.nwp-post-execution-validation-result-set.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-validation-result-set.v1',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'result_set_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_observation_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'source_observation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_observation_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_kind',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_invocation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'delivery_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'observation_kind',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_outcome', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'source_reason_code', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'source_evidence_refs',
                     'nullable': False,
                     'rule': {'duplicates': 'reject',
                              'item_type': 'exact_builtin_str_safe_ref',
                              'maximum': 32,
                              'minimum': 0,
                              'ordering': 'strict_lexicographic',
                              'value_equality': 'equals_exact_current_source_observation_source_evidence_refs'},
                     'type': 'exact_builtin_list'},
                    {'name': 'source_observed_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'program_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'program_version_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'accepted_intent_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'semantic_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_intent_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'command_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'command_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_class',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'candidate_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'capsule_manifest_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'portable_capsule_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'tool_profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'tool_profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'tool_qualification_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'tool_qualification_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'tool_qualification_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'requirement_evidence_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'requirement_evidence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'requirement_evidence_safe_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'requirement_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'requirement_work_spec_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'requirement_work_spec_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'result_author_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'result_author_invocation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'result_set_evidence_refs',
                     'nullable': False,
                     'rule': {'duplicates': 'reject',
                              'item_type': 'exact_builtin_str_safe_ref',
                              'maximum': 32,
                              'minimum': 0,
                              'ordering': 'strict_lexicographic',
                              'value_equality': 'independently_exact_under_governing_result_set_profile'},
                     'type': 'exact_builtin_list'},
                    {'name': 'result',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'repairability', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'reason',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'evaluated_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'expires_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'result_set_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': 'cff49323050cd70855d7fda9b8bcc2666da18a7a3f30f8d8e030a9d60b087d58',
                            'profile_ref': 'post-execution-validation-result-set.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-post-execution-validation-result-set.v1.key',
                       'field': 'result_set_ref',
                       'posture': 'generated_and_owner_supplied_for_revalidation',
                       'prefix': 'post-validation-result-set.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'source_observation_schema_id',
                                           'source_observation_ref',
                                           'source_observation_digest',
                                           'source_kind',
                                           'source_ref',
                                           'source_invocation_ref',
                                           'delivery_attempt_ref',
                                           'observation_kind',
                                           'source_outcome',
                                           'source_reason_code',
                                           'source_evidence_refs',
                                           'source_observed_at',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'effect_intent_ref',
                                           'command_ref',
                                           'command_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'effect_class',
                                           'candidate_ref',
                                           'capsule_manifest_ref',
                                           'portable_capsule_digest',
                                           'tool_profile_ref',
                                           'tool_profile_digest',
                                           'tool_qualification_schema_id',
                                           'tool_qualification_ref',
                                           'tool_qualification_digest',
                                           'requirement_evidence_schema_id',
                                           'requirement_evidence_ref',
                                           'requirement_evidence_safe_digest',
                                           'requirement_digest',
                                           'requirement_work_spec_ref',
                                           'requirement_work_spec_digest',
                                           'result_author_ref',
                                           'result_author_invocation_ref',
                                           'result_set_evidence_refs',
                                           'result',
                                           'repairability',
                                           'reason',
                                           'evaluated_at',
                                           'expires_at']},
 'digest_posture': {'algorithm': 'sha256',
                    'domain': 'governed-execution.nwp-post-execution-validation-result-set.v1.identity',
                    'domain_separator': 'NUL',
                    'field': 'result_set_digest',
                    'self_exclusion': ['result_set_digest']}},
        nested={},
        meta={},
    ),
)


PostExecutionReviewResultSetV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionReviewResultSetV1', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V39',
 'schema_id': 'governed-execution.nwp-post-execution-review-result-set.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-review-result-set.v1',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'result_set_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_observation_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'source_observation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_observation_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_kind',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_invocation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'delivery_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'observation_kind',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_outcome', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'source_reason_code', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'source_evidence_refs',
                     'nullable': False,
                     'rule': {'duplicates': 'reject',
                              'item_type': 'exact_builtin_str_safe_ref',
                              'maximum': 32,
                              'minimum': 0,
                              'ordering': 'strict_lexicographic',
                              'value_equality': 'equals_exact_current_source_observation_source_evidence_refs'},
                     'type': 'exact_builtin_list'},
                    {'name': 'source_observed_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'program_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'program_version_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'accepted_intent_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'semantic_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_intent_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'command_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'command_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_class',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'candidate_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'capsule_manifest_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'portable_capsule_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'tool_profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'tool_profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'tool_qualification_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'tool_qualification_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'tool_qualification_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'requirement_evidence_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'requirement_evidence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'requirement_evidence_safe_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'requirement_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'requirement_work_spec_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'requirement_work_spec_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'result_author_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'result_author_invocation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'result_set_evidence_refs',
                     'nullable': False,
                     'rule': {'duplicates': 'reject',
                              'item_type': 'exact_builtin_str_safe_ref',
                              'maximum': 32,
                              'minimum': 0,
                              'ordering': 'strict_lexicographic',
                              'value_equality': 'independently_exact_under_governing_result_set_profile'},
                     'type': 'exact_builtin_list'},
                    {'name': 'result',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'reason',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'evaluated_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'expires_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'result_set_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': '2dd40a8e0c3628f9e0e3860acc29c0ee908111ce14c7e8dccf944e4b1e9d9730',
                            'profile_ref': 'post-execution-review-result-set.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-post-execution-review-result-set.v1.key',
                       'field': 'result_set_ref',
                       'posture': 'generated_and_owner_supplied_for_revalidation',
                       'prefix': 'post-review-result-set.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'source_observation_schema_id',
                                           'source_observation_ref',
                                           'source_observation_digest',
                                           'source_kind',
                                           'source_ref',
                                           'source_invocation_ref',
                                           'delivery_attempt_ref',
                                           'observation_kind',
                                           'source_outcome',
                                           'source_reason_code',
                                           'source_evidence_refs',
                                           'source_observed_at',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'effect_intent_ref',
                                           'command_ref',
                                           'command_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'effect_fence_ref',
                                           'effect_fence_digest',
                                           'effect_class',
                                           'candidate_ref',
                                           'capsule_manifest_ref',
                                           'portable_capsule_digest',
                                           'tool_profile_ref',
                                           'tool_profile_digest',
                                           'tool_qualification_schema_id',
                                           'tool_qualification_ref',
                                           'tool_qualification_digest',
                                           'requirement_evidence_schema_id',
                                           'requirement_evidence_ref',
                                           'requirement_evidence_safe_digest',
                                           'requirement_digest',
                                           'requirement_work_spec_ref',
                                           'requirement_work_spec_digest',
                                           'result_author_ref',
                                           'result_author_invocation_ref',
                                           'result_set_evidence_refs',
                                           'result',
                                           'reason',
                                           'evaluated_at',
                                           'expires_at']},
 'digest_posture': {'algorithm': 'sha256',
                    'domain': 'governed-execution.nwp-post-execution-review-result-set.v1.identity',
                    'domain_separator': 'NUL',
                    'field': 'result_set_digest',
                    'self_exclusion': ['result_set_digest']}},
        nested={},
        meta={},
    ),
)


PostExecutionReviewerSeparationAuthorObservationLocatorV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionReviewerSeparationAuthorObservationLocatorV1', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V40.n01',
 'schema_id': 'governed-execution.nwp-post-execution-reviewer-separation-author-observation-locator.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-reviewer-separation-author-observation-locator.v1',
                     'name': 'schema_id',
                     'nullable': False,
                     'rule': 'exact_builtin_str;displayed_literal',
                     'type': 'exact_builtin_str'},
                    {'name': 'ordinal',
                     'nullable': False,
                     'rule': '0..2;tuple_order;bool_rejected',
                     'type': 'exact_builtin_int'},
                    {'constant': 'governed-execution.nwp-rw0-c1-evidence-membership.v1',
                     'name': 'membership_schema_id',
                     'nullable': False,
                     'rule': 'exact_builtin_str;displayed_literal',
                     'type': 'exact_builtin_str'},
                    {'name': 'membership_ref',
                     'nullable': False,
                     'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
                     'type': 'exact_builtin_str'},
                    {'name': 'membership_digest',
                     'nullable': False,
                     'rule': 'exact_builtin_str;64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'constant': 'governed-execution.nwp-worker-observation.v1',
                     'name': 'value_schema_id',
                     'nullable': False,
                     'rule': 'exact_builtin_str;displayed_literal',
                     'type': 'exact_builtin_str'},
                    {'name': 'value_ref',
                     'nullable': False,
                     'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
                     'type': 'exact_builtin_str'},
                    {'name': 'value_digest',
                     'nullable': False,
                     'rule': 'exact_builtin_str;64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'constant': 'governed-execution.nwp-rw0-c1-relation-binding.v1',
                     'name': 'relation_row_schema_id',
                     'nullable': False,
                     'rule': 'exact_builtin_str;displayed_literal',
                     'type': 'exact_builtin_str'},
                    {'name': 'relation_ref',
                     'nullable': False,
                     'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
                     'type': 'exact_builtin_str'},
                    {'name': 'relation_digest',
                     'nullable': False,
                     'rule': 'exact_builtin_str;64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'relation_row_digest',
                     'nullable': False,
                     'rule': 'exact_builtin_str;64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'constant': 'governed-execution.nwp-rw0-c1-c2a-worker-observation-relation.v1',
                     'name': 'relation_schema_id',
                     'nullable': False,
                     'rule': 'exact_builtin_str;displayed_literal',
                     'type': 'exact_builtin_str'},
                    {'enum': ['worker'],
                     'name': 'source_kind',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'source_ref',
                     'nullable': False,
                     'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
                     'type': 'exact_builtin_str'},
                    {'name': 'source_invocation_ref',
                     'nullable': False,
                     'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
                     'type': 'exact_builtin_str'},
                    {'enum': ['worker_started', 'candidate_captured', 'worker_completed'],
                     'name': 'observation_kind',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_intent_ref',
                     'nullable': False,
                     'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_ref',
                     'nullable': False,
                     'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
                     'type': 'exact_builtin_str'},
                    {'name': 'effect_fence_digest',
                     'nullable': False,
                     'rule': 'exact_builtin_str;64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'delivery_attempt_ref',
                     'nullable': False,
                     'rule': 'exact_builtin_str;1..96_ASCII_bytes;first_alphanumeric;remaining_[0-9A-Za-z.-];reserved_private_prefixes_rejected',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': '477867ca6eecb36bd77629452489637ef43af2d79c97ffb72b5cce0969d80a2f',
                            'profile_ref': 'post-execution-reviewer-separation-evaluation.v1'},
 'reference_posture': {'posture': 'parent_bound_no_standalone_ref'},
 'digest_posture': {'posture': 'parent_bound_no_standalone_self_digest'}},
        nested={},
        meta={},
    ),
)


PostExecutionReviewerSeparationEvaluationV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'PostExecutionReviewerSeparationEvaluationV1', 'ge_nwp_coordinator._post_execution_evidence_values',
        {'v_number': 'V40',
 'schema_id': 'governed-execution.nwp-post-execution-reviewer-separation-evaluation.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-post-execution-reviewer-separation-evaluation.v1',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'evaluation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'profile_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'phase_basis_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'phase_basis_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_membership_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'review_membership_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_membership_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_value_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'review_value_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_value_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_relation_row_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'review_relation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_relation_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_relation_row_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_relation_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'author_result_membership_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'author_result_membership_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_result_membership_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_result_value_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'author_result_value_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_result_value_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_result_relation_row_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'author_result_relation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_result_relation_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_result_relation_row_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_result_relation_schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'author_observation_locators',
                     'nullable': False,
                     'rule': {'count_equality': 'length_equals_exact_rank13_observation_membership_count',
                              'duplicates': 'reject',
                              'item_type': 'PostExecutionReviewerSeparationAuthorObservationLocatorV1',
                              'maximum': 3,
                              'minimum': 2,
                              'ordering': 'exact_rank13_worker_result_tuple_order'},
                     'type': 'exact_builtin_list'},
                    {'name': 'review_source_kind', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'review_source_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_source_invocation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_source_kind', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'author_source_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_source_invocation_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_effect_intent_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_effect_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_effect_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'review_delivery_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_effect_intent_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_effect_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_effect_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_delivery_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_command_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'author_command_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'attempt_fence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'program_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'program_version_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'accepted_intent_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'work_item_revision_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'semantic_attempt_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'candidate_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'capsule_manifest_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'portable_capsule_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'support_set_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'support_set_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'status',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'reason',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'evaluated_at',
                     'nullable': False,
                     'rule': 'whole_second_UTC_YYYY-MM-DDThh:mm:ssZ',
                     'type': 'exact_builtin_str'},
                    {'name': 'evaluation_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': '477867ca6eecb36bd77629452489637ef43af2d79c97ffb72b5cce0969d80a2f',
                            'profile_ref': 'post-execution-reviewer-separation-evaluation.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-post-execution-reviewer-separation-evaluation.v1.key',
                       'field': 'evaluation_ref',
                       'posture': 'generated',
                       'prefix': 'post-reviewer-separation-evaluation.',
                       'preimage_fields': ['profile_ref',
                                           'profile_digest',
                                           'phase_basis_ref',
                                           'phase_basis_digest',
                                           'review_membership_schema_id',
                                           'review_membership_ref',
                                           'review_membership_digest',
                                           'review_value_schema_id',
                                           'review_value_ref',
                                           'review_value_digest',
                                           'review_relation_row_schema_id',
                                           'review_relation_ref',
                                           'review_relation_digest',
                                           'review_relation_row_digest',
                                           'review_relation_schema_id',
                                           'author_result_membership_schema_id',
                                           'author_result_membership_ref',
                                           'author_result_membership_digest',
                                           'author_result_value_schema_id',
                                           'author_result_value_ref',
                                           'author_result_value_digest',
                                           'author_result_relation_row_schema_id',
                                           'author_result_relation_ref',
                                           'author_result_relation_digest',
                                           'author_result_relation_row_digest',
                                           'author_result_relation_schema_id',
                                           'author_observation_locators',
                                           'review_source_kind',
                                           'review_source_ref',
                                           'review_source_invocation_ref',
                                           'author_source_kind',
                                           'author_source_ref',
                                           'author_source_invocation_ref',
                                           'review_effect_intent_ref',
                                           'review_effect_fence_ref',
                                           'review_effect_fence_digest',
                                           'review_delivery_attempt_ref',
                                           'author_effect_intent_ref',
                                           'author_effect_fence_ref',
                                           'author_effect_fence_digest',
                                           'author_delivery_attempt_ref',
                                           'author_command_ref',
                                           'author_command_digest',
                                           'attempt_fence_ref',
                                           'attempt_fence_digest',
                                           'program_ref',
                                           'program_version_ref',
                                           'accepted_intent_revision_ref',
                                           'work_item_ref',
                                           'work_item_revision_ref',
                                           'semantic_attempt_ref',
                                           'candidate_ref',
                                           'capsule_manifest_ref',
                                           'portable_capsule_digest',
                                           'support_set_ref',
                                           'support_set_digest',
                                           'status',
                                           'reason',
                                           'evaluated_at']},
 'digest_posture': {'algorithm': 'sha256',
                    'domain': 'governed-execution.nwp-post-execution-reviewer-separation-evaluation.v1.identity',
                    'domain_separator': 'NUL',
                    'field': 'evaluation_digest',
                    'self_exclusion': ['evaluation_digest']}},
        nested={'author_observation_locators': PostExecutionReviewerSeparationAuthorObservationLocatorV1},
        meta={},
    ),
)


def _require_action_fields(
    target: _PostExecutionValue,
    source: object,
    pairs: tuple[tuple[str, str], ...],
) -> None:
    if any(
        not _exact_equal(getattr(target, target_name), getattr(source, source_name))
        for target_name, source_name in pairs
    ):
        _fail("source_owner_mismatch")


_OBSERVATION_RESULT_PAIRS = (
    ("source_observation_schema_id", "schema_id"),
    ("source_observation_ref", "observation_ref"),
    ("source_observation_digest", "observation_digest"),
    ("source_kind", "source_kind"), ("source_ref", "source_ref"),
    ("source_invocation_ref", "source_invocation_ref"),
    ("delivery_attempt_ref", "delivery_attempt_ref"),
    ("observation_kind", "observation_kind"), ("source_outcome", "outcome"),
    ("source_reason_code", "reason_code"), ("source_evidence_refs", "evidence_refs"),
    ("source_observed_at", "observed_at"), ("program_ref", "program_ref"),
    ("program_version_ref", "program_version_ref"),
    ("accepted_intent_revision_ref", "accepted_intent_revision_ref"),
    ("work_item_ref", "work_item_ref"), ("work_item_revision_ref", "work_item_revision_ref"),
    ("semantic_attempt_ref", "semantic_attempt_ref"), ("effect_intent_ref", "effect_intent_ref"),
    ("command_ref", "command_ref"), ("command_digest", "command_digest"),
    ("attempt_fence_ref", "attempt_fence_ref"), ("attempt_fence_digest", "attempt_fence_digest"),
    ("effect_fence_ref", "effect_fence_ref"), ("effect_fence_digest", "effect_fence_digest"),
    ("candidate_ref", "candidate_ref"), ("capsule_manifest_ref", "capsule_manifest_ref"),
    ("portable_capsule_digest", "portable_capsule_digest"),
)


def validate_independent_review_disposition(
    value: object,
    *,
    review_result_set: object,
    reviewer_separation: object,
) -> IndependentReviewDispositionV1:
    """Verify the expected disposition against its two derived evidence owners."""

    candidate = typing.cast(
        IndependentReviewDispositionV1,
        IndependentReviewDispositionV1.from_supplied(value),
    )
    result_set = typing.cast(
        PostExecutionReviewResultSetV1,
        PostExecutionReviewResultSetV1.from_supplied(review_result_set),
    )
    separation = typing.cast(
        PostExecutionReviewerSeparationEvaluationV1,
        PostExecutionReviewerSeparationEvaluationV1.from_supplied(reviewer_separation),
    )
    _require_action_fields(candidate, result_set, (
        ("source_observation_schema_id", "source_observation_schema_id"),
        ("source_observation_ref", "source_observation_ref"),
        ("source_observation_digest", "source_observation_digest"),
        ("source_kind", "source_kind"), ("source_ref", "source_ref"),
        ("source_invocation_ref", "source_invocation_ref"),
        ("source_outcome", "source_outcome"), ("source_reason_code", "source_reason_code"),
        ("source_evidence_refs", "source_evidence_refs"), ("source_observed_at", "source_observed_at"),
        ("review_result_set_schema_id", "schema_id"), ("review_result_set_ref", "result_set_ref"),
        ("review_result_set_digest", "result_set_digest"), ("result", "result"),
        ("reason", "reason"), ("evaluated_at", "evaluated_at"), ("expires_at", "expires_at"),
    ))
    _require_action_fields(candidate, separation, (
        ("reviewer_separation_schema_id", "schema_id"),
        ("reviewer_separation_ref", "evaluation_ref"),
        ("reviewer_separation_digest", "evaluation_digest"),
        ("separation_status", "status"),
    ))
    return candidate


def _supplied_owner_mapping(value: object) -> dict[str, object]:
    if isinstance(value, _PostExecutionValue):
        value._validate_value()
        return value.to_mapping()
    if type(value) in {
        _worker_values.CandidateCapsuleManifestV1,
        _worker_values.WorkerObservationV1,
        _worker_values.AttemptFenceV1,
        _worker_values.EffectFenceV1,
        _phase_values.RW0AuthorityVerificationObservationV1,
        _phase_values.RW0EffectHostQualificationV1,
    }:
        return value.to_mapping()
    if type(value) in {
        _c1_values.RW0C1WireProcessResultClassificationBindingV1,
        _c1_values.RW0C1WireWorkerResultBindingV1,
    }:
        return value.to_mapping()
    if type(value) in {
        _requirement_values.DevelopmentValidationRequirementEvidenceV1,
        _requirement_values.DevelopmentReviewRequirementEvidenceV1,
    }:
        return {
            name: getattr(value, name)
            for name in (
                "schema_id", "requirement_ref", "requirement_digest",
                "work_spec_ref", "work_spec_digest", "safe_evidence_digest",
            )
        }
    if type(value) is _GlobalStopState:
        return value.to_dict()
    if type(value) is dict:
        mapping = _require_exact_mapping(value)
        schema_id = mapping.get("schema_id")
        if type(schema_id) is not str or not schema_id.endswith("-profile.v1"):
            _fail("source_owner_mismatch")
        return mapping
    _fail("source_owner_mismatch")


def _validate_role_supply_source_canonicals(
    supply_mapping: dict[str, object],
    index: int,
) -> None:
    """Validate the profile/binding bytes carried by one frozen role branch."""

    typed = typing.cast(dict[str, object], supply_mapping["typed_canonical_value"])
    profile = supply_mapping["source_profile_canonical_value"]
    binding = supply_mapping["source_binding_canonical_value"]
    if profile is None:
        if binding is not None:
            _fail("source_owner_mismatch")
        return
    if type(profile) is not dict or type(binding) is not dict:
        _fail("invalid_nested_value")
    profile_mapping = typing.cast(dict[str, object], profile)
    binding_mapping = typing.cast(dict[str, object], binding)
    expected_profile_schema = _ROLE_SOURCE_PROFILE_SCHEMAS[index]
    expected_binding_schema = _ROLE_SOURCE_BINDING_SCHEMAS[index]
    if (
        profile_mapping.get("schema_id") != expected_profile_schema
        or binding_mapping.get("schema_id") != expected_binding_schema
    ):
        _fail("source_owner_mismatch")

    if index == 5:
        profile_fields = {
            "schema_id", "source_profile_ref", "source_family",
            "source_system_schema_id", "adapter_profile_ref",
            "adapter_profile_digest", "profile_version",
            "external_authority_claim", "source_profile_digest",
        }
        if set(profile_mapping) != profile_fields:
            _fail("invalid_nested_value")
        if (
            profile_mapping["source_family"] != "versioned_external_risk_source"
            or profile_mapping["source_system_schema_id"]
            != "governed-execution.nwp-finite-backlog-risk-source-binding.v1"
            or profile_mapping["adapter_profile_ref"] != "finite_backlog_risk_source.v1"
            or profile_mapping["adapter_profile_digest"]
            != "2ea8aa75234deb0901d3ca0a32d19877da072378e1acd438c901ce5cf1e489bc"
            or profile_mapping["profile_version"] != 1
            or profile_mapping["external_authority_claim"] is not False
        ):
            _fail("source_owner_mismatch")
        expected_profile_ref = _generated_ref(
            "post-risk-source-profile.",
            "governed-execution.nwp-post-execution-risk-source-profile.v1.key",
            {
                name: profile_mapping[name]
                for name in (
                    "source_family", "source_system_schema_id",
                    "adapter_profile_ref", "adapter_profile_digest",
                    "profile_version", "external_authority_claim",
                )
            },
        )
        expected_profile_digest = _domain_separated_digest(
            "governed-execution.nwp-post-execution-risk-source-profile.v1.identity",
            {
                name: value for name, value in profile_mapping.items()
                if name != "source_profile_digest"
            },
        )
        profile_ref_field = "source_profile_ref"
        profile_digest_field = "source_profile_digest"
    else:
        profile_pair = _ROLE_SOURCE_PROFILE_PAIRS[index]
        if profile_pair is None:
            _fail("invalid_profile_pair")
        profile_ref_field = "profile_ref"
        profile_digest_field = "profile_digest"
        expected_profile_ref, expected_profile_digest = profile_pair
        profile_preimage = (
            {
                name: value for name, value in profile_mapping.items()
                if name != "profile_digest"
            }
            if index == 1
            else profile_mapping
        )
        if _domain_separated_digest(
            typing.cast(str, expected_profile_schema) + ".identity",
            profile_preimage,
        ) != expected_profile_digest:
            _fail("invalid_profile_pair")

    if (
        profile_mapping.get(profile_ref_field) != expected_profile_ref
        or profile_mapping.get(profile_digest_field, expected_profile_digest)
        != expected_profile_digest
        or supply_mapping["source_profile_ref"] != expected_profile_ref
        or supply_mapping["source_profile_digest"] != expected_profile_digest
    ):
        _fail("invalid_profile_pair")

    binding_ref: object
    binding_digest: object
    if index == 1:
        relation_fields = {
            "schema_id", "phase_basis_ref", "phase_basis_digest",
            "relation_ref", "subject_type", "subject_membership_ref",
            "subject_membership_digest", "subject_kind_rank",
            "subject_value_ref", "subject_value_digest",
            "subject_value_schema_id", "relation_rank", "relation_schema_id",
            "relation_version", "proof_mode", "profile_ref", "profile_digest",
            "evaluated_at", "operand_count", "operand_set_digest",
            "relation_digest", "relation_row_digest",
        }
        if set(binding_mapping) != relation_fields:
            _fail("invalid_nested_value")
        try:
            expected_relation_ref = _c1_contracts.relation_reference(
                phase_basis_ref=typing.cast(str, binding_mapping["phase_basis_ref"]),
                subject_type=typing.cast(str, binding_mapping["subject_type"]),
                subject_membership_ref=typing.cast(
                    str, binding_mapping["subject_membership_ref"]
                ),
                relation_rank=typing.cast(int, binding_mapping["relation_rank"]),
                phase_basis_digest=typing.cast(
                    str, binding_mapping["phase_basis_digest"]
                ),
            )
        except (TypeError, ValueError, KeyError, OverflowError):
            _fail("source_owner_mismatch")
        if (
            binding_mapping["relation_ref"] != expected_relation_ref
            or binding_mapping["subject_type"] != "evidence_membership"
            or binding_mapping["subject_kind_rank"] != 14
            or binding_mapping["subject_value_schema_id"] != typed["schema_id"]
            or binding_mapping["subject_value_ref"] != typed["value_ref"]
            or binding_mapping["subject_value_digest"] != typed["value_digest"]
            or binding_mapping["relation_rank"] != 0
            or binding_mapping["relation_schema_id"]
            != "governed-execution.nwp-rw0-c1-wire-process-result-classifier-relation.v1"
            or binding_mapping["relation_version"] != 1
            or binding_mapping["proof_mode"] != "derived_wrapper_recomputable"
            or binding_mapping["profile_ref"] != expected_profile_ref
            or binding_mapping["profile_digest"] != expected_profile_digest
        ):
            _fail("source_owner_mismatch")
        binding_ref = binding_mapping["relation_ref"]
        binding_digest = binding_mapping["relation_digest"]
    elif index in {2, 3}:
        try:
            observation = _worker_values.WorkerObservationV1.from_mapping(
                binding_mapping
            )
        except (TypeError, ValueError, KeyError, OverflowError):
            _fail("source_owner_mismatch")
        expected_source = (
            ("validator", "validation_completed")
            if index == 2
            else ("independent_reviewer", "independent_review_completed")
        )
        if (
            (observation.source_kind, observation.observation_kind)
            != expected_source
            or typed["source_observation_schema_id"] != observation.schema_id
            or typed["source_observation_ref"] != observation.observation_ref
            or typed["source_observation_digest"] != observation.observation_digest
        ):
            _fail("source_owner_mismatch")
        binding_ref = observation.observation_ref
        binding_digest = observation.observation_digest
    elif index == 4:
        binding_ref = binding_mapping.get("attestation_ref")
        binding_digest = binding_mapping.get("attestation_digest")
        if (
            _domain_separated_digest(
                "governed-execution.nwp-post-execution-standing-policy-source-attestation.v1.identity",
                {
                    name: value for name, value in binding_mapping.items()
                    if name != "attestation_digest"
                },
            ) != binding_digest
            or typed["policy_source_schema_id"] != binding_mapping["schema_id"]
            or typed["policy_source_ref"] != binding_ref
            or typed["policy_source_digest"] != binding_digest
        ):
            _fail("source_owner_mismatch")
    elif index == 5:
        binding_fields = {
            "schema_id", "source_binding_ref", "source_profile_schema_id",
            "source_profile_ref", "source_profile_digest",
            "development_work_item_ref", "risk_lane", "source_value_schema_id",
            "source_value_ref", "source_value_digest", "mapping_evidence_ref",
            "mapping_evidence_digest", "evaluated_at", "expires_at",
            "source_binding_digest",
        }
        if set(binding_mapping) != binding_fields:
            _fail("invalid_nested_value")
        _require_safe_ref(binding_mapping["development_work_item_ref"])
        _require_safe_ref(binding_mapping["risk_lane"])
        _require_safe_ref(binding_mapping["source_value_ref"])
        _require_sha256(binding_mapping["source_value_digest"])
        _require_safe_ref(binding_mapping["mapping_evidence_ref"])
        _require_sha256(binding_mapping["mapping_evidence_digest"])
        evaluated_at = _require_whole_second_utc(binding_mapping["evaluated_at"])
        expires_at = _require_whole_second_utc(binding_mapping["expires_at"])
        expected_binding_ref = _generated_ref(
            "post-risk-source-binding.",
            "governed-execution.nwp-post-execution-risk-source-binding.v1.key",
            {
                name: binding_mapping[name]
                for name in (
                    "source_profile_schema_id", "source_profile_ref",
                    "source_profile_digest", "development_work_item_ref",
                    "risk_lane", "source_value_schema_id", "source_value_ref",
                    "source_value_digest", "mapping_evidence_ref",
                    "mapping_evidence_digest", "evaluated_at", "expires_at",
                )
            },
        )
        expected_binding_digest = _domain_separated_digest(
            "governed-execution.nwp-post-execution-risk-source-binding.v1.identity",
            {
                name: value for name, value in binding_mapping.items()
                if name != "source_binding_digest"
            },
        )
        if (
            evaluated_at >= expires_at
            or binding_mapping["source_binding_ref"] != expected_binding_ref
            or binding_mapping["source_binding_digest"] != expected_binding_digest
            or binding_mapping["source_profile_schema_id"] != expected_profile_schema
            or binding_mapping["source_profile_ref"] != expected_profile_ref
            or binding_mapping["source_profile_digest"] != expected_profile_digest
            or typed["source_profile_schema_id"] != expected_profile_schema
            or typed["source_profile_ref"] != expected_profile_ref
            or typed["source_profile_digest"] != expected_profile_digest
            or typed["source_binding_schema_id"] != binding_mapping["schema_id"]
            or typed["source_binding_ref"] != expected_binding_ref
            or typed["source_binding_digest"] != expected_binding_digest
        ):
            _fail("source_owner_mismatch")
        binding_ref = expected_binding_ref
        binding_digest = expected_binding_digest
    elif index == 7:
        try:
            state = _GlobalStopState.from_dict(binding_mapping)
        except (TypeError, ValueError, KeyError, OverflowError):
            _fail("source_owner_mismatch")
        binding_ref = state.stop_ref
        binding_digest = state.canonical_digest()
        if (
            typed["global_stop_schema_id"] != state.schema_id
            or typed["global_stop_ref"] != state.stop_ref
            or typed["global_stop_digest"] != binding_digest
            or typed["global_stop_version"] != state.version
            or typed["global_stop_state"]
            != ("active" if state.active else "clear")
        ):
            _fail("source_owner_mismatch")
    elif index == 8:
        try:
            fence = _worker_values.EffectFenceV1.from_mapping(binding_mapping)
        except (TypeError, ValueError, KeyError, OverflowError):
            _fail("source_owner_mismatch")
        binding_ref = fence.effect_fence_ref
        binding_digest = fence.effect_fence_digest
        if (
            typed["effect_fence_schema_id"] != fence.schema_id
            or typed["effect_fence_ref"] != binding_ref
            or typed["effect_fence_digest"] != binding_digest
        ):
            _fail("source_owner_mismatch")
    else:
        _fail("source_owner_mismatch")

    if (
        supply_mapping["source_binding_schema_id"] != expected_binding_schema
        or supply_mapping["source_binding_ref"] != binding_ref
        or supply_mapping["source_binding_digest"] != binding_digest
    ):
        _fail("source_owner_mismatch")


def validate_post_execution_evidence_supply(
    value: object,
    *,
    role_values: tuple[object, ...],
    support_values: tuple[tuple[object, ...], ...],
) -> PostExecutionEvidenceSupplyV2:
    """Verify the exact nine-role private supply against independent owners."""

    candidate = typing.cast(
        PostExecutionEvidenceSupplyV2,
        PostExecutionEvidenceSupplyV2.from_supplied(value),
    )
    role_entries = candidate.input_context.role_entries
    if (
        type(role_values) is not tuple
        or len(role_values) != 9
        or type(support_values) is not tuple
        or len(support_values) != 9
        or any(type(group) is not tuple for group in support_values)
        or len(candidate.role_supplies) != 9
        or len(role_entries) != 9
    ):
        _fail("invalid_cardinality")
    expected_role_types = (
        (_worker_values.__name__, "CandidateCapsuleManifestV1"),
        (_c1_values.__name__, "RW0C1WireProcessResultClassificationBindingV1"),
        (__name__, "ValidationDispositionV1"),
        (__name__, "IndependentReviewDispositionV1"),
        ("ge_nwp_coordinator._post_execution_policy_values", "PostExecutionStandingPolicyBranchMatrixV1"),
        ("ge_nwp_coordinator._post_execution_policy_values", "PostExecutionRiskLaneBranchMatrixV1"),
        (_phase_values.__name__, "RW0AuthorityVerificationObservationV1"),
        (__name__, "PostExecutionGlobalStopSnapshotV1"),
        (__name__, "PostExecutionSourceEffectCeilingEvidenceV1"),
    )
    for index, (entry, supply, owner, support_group) in enumerate(zip(
        role_entries,
        candidate.role_supplies,
        role_values,
        support_values,
        strict=True,
    )):
        for field in ("role", "role_rank", "ordinal", "typed_schema_id", "typed_value_ref", "typed_value_digest", "model_input_posture"):
            if not _exact_equal(getattr(entry, field), getattr(supply, field)):
                _fail("relation_mismatch")
        owner_type = type(owner)
        if (owner_type.__module__, owner_type.__name__) != expected_role_types[index]:
            _fail("source_owner_mismatch")
        supply_mapping = supply.to_mapping()
        typed_value = typing.cast(dict[str, object], supply_mapping["typed_canonical_value"])
        _validate_role_supply_source_canonicals(supply_mapping, index)
        owner_mapping = _supplied_owner_mapping(owner)
        if (
            not _exact_equal(typed_value, owner_mapping)
            or typed_value.get("schema_id") != supply.typed_schema_id
            or supply.typed_value_ref not in owner_mapping.values()
            or supply.typed_value_digest not in owner_mapping.values()
            or len(support_group) != supply.support_value_count
        ):
            _fail("invalid_nested_value")
        supplied_support = typing.cast(
            list[dict[str, object]],
            supply_mapping["support_canonical_values"],
        )
        if len(supplied_support) != len(support_group):
            _fail("invalid_cardinality")
        raw_support_set = supply_mapping["support_set_canonical_value"]
        if raw_support_set is None:
            if support_group:
                _fail("source_owner_mismatch")
            continue
        support_set = PostExecutionSupportSetV1.from_mapping({
            name: (
                [
                    {field: raw[field] for field in PostExecutionSupportEntryV1._FIELDS}
                    for raw in typing.cast(
                        list[dict[str, object]],
                        typing.cast(dict[str, object], raw_support_set)["entries"],
                    )
                ]
                if name == "entries"
                else typing.cast(dict[str, object], raw_support_set)[name]
            )
            for name in PostExecutionSupportSetV1._FIELDS
        })
        for support_entry, supplied_mapping, support_owner in zip(
            support_set.entries,
            supplied_support,
            support_group,
            strict=True,
        ):
            support_mapping = _supplied_owner_mapping(support_owner)
            if (
                not _exact_equal(supplied_mapping, support_mapping)
                or support_mapping.get("schema_id") != support_entry.source_schema_id
            ):
                _fail("source_owner_mismatch")
            if type(support_owner) is dict:
                if _domain_separated_digest(
                    typing.cast(str, support_mapping["schema_id"]) + ".identity",
                    support_mapping,
                ) != support_entry.source_digest:
                    _fail("source_owner_mismatch")
            elif type(support_owner) is _GlobalStopState:
                if support_owner.canonical_digest() != support_entry.source_digest:
                    _fail("source_owner_mismatch")
            elif support_entry.source_digest not in support_mapping.values():
                _fail("source_owner_mismatch")
            if (
                support_entry.source_ref not in support_mapping.values()
                and not (
                    type(support_owner) is _GlobalStopState
                    and support_entry.source_ref == support_owner.stop_ref
                )
            ):
                _fail("source_owner_mismatch")
    return candidate


def post_execution_global_stop_snapshot(
    value: object,
    *,
    current_state: _GlobalStopState,
    updated_at: str,
    support_set: PostExecutionSupportSetV1,
) -> PostExecutionGlobalStopSnapshotV1:
    """Derive the snapshot fields from one exact current global-stop value."""

    if type(current_state) is not _GlobalStopState or type(support_set) is not PostExecutionSupportSetV1:
        _fail("source_owner_mismatch")
    candidate = typing.cast(
        PostExecutionGlobalStopSnapshotV1,
        PostExecutionGlobalStopSnapshotV1.from_supplied(value),
    )
    source = current_state.to_dict()
    support_set._validate_value()
    expected_support = (
        (
            "global_stop_current", 1, source["schema_id"], current_state.stop_ref,
            current_state.canonical_digest(),
        ),
        (
            "stop_profile", 2,
            "governed-execution.nwp-post-execution-global-stop-profile.v1",
            _POST_EXECUTION_GLOBAL_STOP_PROFILE_REF,
            _POST_EXECUTION_GLOBAL_STOP_PROFILE_DIGEST,
        ),
    )
    if tuple(
        (entry.role, entry.rank, entry.source_schema_id, entry.source_ref, entry.source_digest)
        for entry in support_set.entries
    ) != expected_support:
        _fail("source_owner_mismatch")
    reason = source["reason_class"]
    expected = {
        "global_stop_schema_id": source["schema_id"],
        "global_stop_ref": current_state.stop_ref,
        "global_stop_version": source["version"],
        "global_stop_state": current_state.status.value,
        "global_stop_stop_id": source["stop_id"],
        "global_stop_reason_class": reason,
        "global_stop_issuer_ref": source["issuer_ref"],
        "global_stop_issued_at": source["issued_at"],
        "global_stop_operator_decision_ref": source["operator_decision_ref"],
        "global_stop_digest": current_state.canonical_digest(),
        "global_stop_updated_at": _require_whole_second_utc(updated_at),
        "support_set_ref": support_set.support_set_ref,
        "support_set_digest": support_set.support_set_digest,
    }
    if any(not _exact_equal(getattr(candidate, field), expected_value) for field, expected_value in expected.items()):
        _fail("source_owner_mismatch")
    return candidate


def validate_post_execution_model_input_binding(
    value: object,
    *,
    input_context: object,
    safe_projection: object,
    private_manifest: object,
) -> PostExecutionModelInputBindingV2:
    """Verify a model-input binding against its exact three input owners."""

    candidate = typing.cast(
        PostExecutionModelInputBindingV2,
        PostExecutionModelInputBindingV2.from_supplied(value),
    )
    context = PostExecutionSemanticReviewInputContextV1.from_supplied(input_context)
    safe = PostExecutionModelInputSafeProjectionV2.from_supplied(safe_projection)
    private = PostExecutionPrivateInputManifestV2.from_supplied(private_manifest)
    _require_action_fields(candidate, context, (
        ("input_context_schema_id", "schema_id"), ("input_context_ref", "input_context_ref"),
        ("input_context_digest", "input_context_digest"), ("lineage_context_schema_id", "lineage_context_schema_id"),
        ("lineage_context_ref", "lineage_context_ref"), ("lineage_context_digest", "lineage_context_digest"),
    ))
    _require_action_fields(candidate, safe, (
        ("model_input_safe_projection_schema_id", "schema_id"),
        ("model_input_safe_projection_ref", "projection_ref"),
        ("model_input_safe_projection_digest", "projection_digest"),
    ))
    _require_action_fields(candidate, private, (
        ("private_input_manifest_schema_id", "schema_id"),
        ("private_input_manifest_ref", "manifest_ref"),
        ("private_input_manifest_digest", "manifest_digest"),
    ))
    return candidate


def validate_post_execution_review_result_set(
    value: object,
    *,
    source_observation: _worker_values.WorkerObservationV1,
    requirement_evidence: _requirement_values.DevelopmentReviewRequirementEvidenceV1,
    tool_qualification: _phase_values.RW0EffectHostQualificationV1,
) -> PostExecutionReviewResultSetV1:
    """Derive and verify review-result fields from one current observation."""

    if (
        type(source_observation) is not _worker_values.WorkerObservationV1
        or type(requirement_evidence)
        is not _requirement_values.DevelopmentReviewRequirementEvidenceV1
        or type(tool_qualification) is not _phase_values.RW0EffectHostQualificationV1
        or tool_qualification.result != "qualified"
    ):
        _fail("source_owner_mismatch")
    candidate = typing.cast(
        PostExecutionReviewResultSetV1,
        PostExecutionReviewResultSetV1.from_supplied(value),
    )
    _require_action_fields(candidate, source_observation, _OBSERVATION_RESULT_PAIRS)
    _require_action_fields(candidate, requirement_evidence, (
        ("requirement_evidence_schema_id", "schema_id"),
        ("requirement_evidence_ref", "requirement_ref"),
        ("requirement_evidence_safe_digest", "safe_evidence_digest"),
        ("requirement_digest", "requirement_digest"),
        ("requirement_work_spec_ref", "work_spec_ref"),
        ("requirement_work_spec_digest", "work_spec_digest"),
    ))
    _require_action_fields(candidate, tool_qualification, (
        ("tool_profile_ref", "required_review_tool_profile_ref"),
        ("tool_profile_digest", "required_review_tool_profile_digest"),
        ("tool_qualification_schema_id", "schema_id"),
        ("tool_qualification_ref", "qualification_ref"),
        ("tool_qualification_digest", "qualification_digest"),
    ))
    return candidate


def _require_c1_row(
    value: object,
    *,
    table_name: str,
    kind_rank: int,
) -> dict[str, object]:
    if (
        type(value) is not _c1_contracts.RW0C1RowValue
        or value.table_name != table_name
    ):
        _fail("source_owner_mismatch")
    mapping = value.to_mapping()
    rank_field = "kind_rank" if table_name == "rw0_evidence_memberships" else "subject_kind_rank"
    if mapping[rank_field] != kind_rank:
        _fail("source_owner_mismatch")
    return mapping


def evaluate_post_execution_reviewer_separation(
    value: object,
    *,
    review_membership_row: object,
    review_observation: _worker_values.WorkerObservationV1,
    review_relation_row: object,
    author_result_membership_row: object,
    author_result_value: _c1_values.RW0C1WireWorkerResultBindingV1,
    author_result_relation_row: object,
    author_observation_membership_rows: tuple[object, ...],
    author_observations: tuple[_worker_values.WorkerObservationV1, ...],
    author_observation_relation_rows: tuple[object, ...],
    candidate_capsule: _worker_values.CandidateCapsuleManifestV1,
    support_set: PostExecutionSupportSetV1,
) -> PostExecutionReviewerSeparationEvaluationV1:
    """Verify an expected V40 result against the exact current C1 owner graph.

    The current-owner values are already reconstructed by their existing
    private owners.  This function performs no lookup: it binds their exact
    membership/value/relation coordinates, derives the operational-separation
    outcome, and treats ``value`` only as the expected output assertion.
    """

    if (
        type(review_observation) is not _worker_values.WorkerObservationV1
        or type(author_result_value)
        is not _c1_values.RW0C1WireWorkerResultBindingV1
        or type(author_observation_membership_rows) is not tuple
        or type(author_observations) is not tuple
        or type(author_observation_relation_rows) is not tuple
        or type(candidate_capsule) is not _worker_values.CandidateCapsuleManifestV1
        or type(support_set) is not PostExecutionSupportSetV1
    ):
        _fail("source_owner_mismatch")
    support_set._validate_value()
    review_membership = _require_c1_row(
        review_membership_row,
        table_name="rw0_evidence_memberships",
        kind_rank=12,
    )
    review_relation = _require_c1_row(
        review_relation_row,
        table_name="rw0_relation_bindings",
        kind_rank=12,
    )
    author_result_membership = _require_c1_row(
        author_result_membership_row,
        table_name="rw0_evidence_memberships",
        kind_rank=13,
    )
    author_result_relation = _require_c1_row(
        author_result_relation_row,
        table_name="rw0_relation_bindings",
        kind_rank=13,
    )
    count = len(author_result_value.observation_memberships)
    if (
        count not in {2, 3}
        or len(author_observation_membership_rows) != count
        or len(author_observations) != count
        or len(author_observation_relation_rows) != count
        or any(type(item) is not _worker_values.WorkerObservationV1 for item in author_observations)
    ):
        _fail("source_owner_mismatch")
    author_memberships = tuple(
        _require_c1_row(row, table_name="rw0_evidence_memberships", kind_rank=12)
        for row in author_observation_membership_rows
    )
    author_relations = tuple(
        _require_c1_row(row, table_name="rw0_relation_bindings", kind_rank=12)
        for row in author_observation_relation_rows
    )

    def require_membership_relation(
        membership: dict[str, object],
        relation: dict[str, object],
        *,
        value_schema_id: str,
        value_ref: str,
        value_digest: str,
    ) -> None:
        if (
            membership["value_schema_id"] != value_schema_id
            or membership["value_ref"] != value_ref
            or membership["value_digest"] != value_digest
            or relation["phase_basis_ref"] != membership["phase_basis_ref"]
            or relation["phase_basis_digest"] != membership["phase_basis_digest"]
            or relation["subject_membership_ref"] != membership["membership_ref"]
            or relation["subject_membership_digest"] != membership["membership_digest"]
            or relation["subject_value_schema_id"] != value_schema_id
            or relation["subject_value_ref"] != value_ref
            or relation["subject_value_digest"] != value_digest
        ):
            _fail("source_owner_mismatch")

    require_membership_relation(
        review_membership,
        review_relation,
        value_schema_id=review_observation.schema_id,
        value_ref=review_observation.observation_ref,
        value_digest=review_observation.observation_digest,
    )
    require_membership_relation(
        author_result_membership,
        author_result_relation,
        value_schema_id=author_result_value.schema_id,
        value_ref=author_result_value.value_ref,
        value_digest=author_result_value.value_digest,
    )

    expected_kinds = (
        ("worker_started", "worker_completed")
        if count == 2
        else ("worker_started", "candidate_captured", "worker_completed")
    )
    locators: list[dict[str, object]] = []
    for ordinal, (locator, membership, observation, relation) in enumerate(zip(
        author_result_value.observation_memberships,
        author_memberships,
        author_observations,
        author_relations,
        strict=True,
    )):
        require_membership_relation(
            membership,
            relation,
            value_schema_id=observation.schema_id,
            value_ref=observation.observation_ref,
            value_digest=observation.observation_digest,
        )
        if (
            locator.role != f"worker_observation:{ordinal:03d}"
            or locator.kind_rank != 12
            or locator.membership_ref != membership["membership_ref"]
            or locator.membership_digest != membership["membership_digest"]
            or locator.value_ref != observation.observation_ref
            or locator.value_digest != observation.observation_digest
            or observation.observation_kind != expected_kinds[ordinal]
        ):
            _fail("source_owner_mismatch")
        locators.append({
            "schema_id": PostExecutionReviewerSeparationAuthorObservationLocatorV1._SCHEMA_ID,
            "ordinal": ordinal,
            "membership_schema_id": membership["schema_id"],
            "membership_ref": membership["membership_ref"],
            "membership_digest": membership["membership_digest"],
            "value_schema_id": observation.schema_id,
            "value_ref": observation.observation_ref,
            "value_digest": observation.observation_digest,
            "relation_row_schema_id": relation["schema_id"],
            "relation_ref": relation["relation_ref"],
            "relation_digest": relation["relation_digest"],
            "relation_row_digest": relation["relation_row_digest"],
            "relation_schema_id": relation["relation_schema_id"],
            "source_kind": observation.source_kind,
            "source_ref": observation.source_ref,
            "source_invocation_ref": observation.source_invocation_ref,
            "observation_kind": observation.observation_kind,
            "effect_intent_ref": observation.effect_intent_ref,
            "effect_fence_ref": observation.effect_fence_ref,
            "effect_fence_digest": observation.effect_fence_digest,
            "delivery_attempt_ref": observation.delivery_attempt_ref,
        })

    author = author_observations[-1]
    phase_pair = (
        review_membership["phase_basis_ref"],
        review_membership["phase_basis_digest"],
    )
    phase_pairs = {
        phase_pair,
        (review_relation["phase_basis_ref"], review_relation["phase_basis_digest"]),
        (author_result_value.phase_basis_ref, author_result_value.phase_basis_digest),
        (author_result_membership["phase_basis_ref"], author_result_membership["phase_basis_digest"]),
        (author_result_relation["phase_basis_ref"], author_result_relation["phase_basis_digest"]),
        *((row["phase_basis_ref"], row["phase_basis_digest"]) for row in author_memberships),
        *((row["phase_basis_ref"], row["phase_basis_digest"]) for row in author_relations),
    }
    common_lineage_fields = (
        "program_ref", "program_version_ref", "accepted_intent_revision_ref",
        "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
    )
    author_lineage = tuple(getattr(author, name) for name in common_lineage_fields)
    if (
        len(phase_pairs) != 1
        or any(
            tuple(getattr(item, name) for name in common_lineage_fields) != author_lineage
            for item in author_observations
        )
        or tuple(getattr(review_observation, name) for name in common_lineage_fields)
        != author_lineage
        or (count == 3 and author_observations[1].candidate_ref != candidate_capsule.candidate_ref)
        or review_observation.candidate_ref != candidate_capsule.candidate_ref
        or review_observation.capsule_manifest_ref != candidate_capsule.capsule_manifest_ref
        or review_observation.portable_capsule_digest != candidate_capsule.portable_capsule_digest
        or tuple(getattr(candidate_capsule, name) for name in common_lineage_fields)
        != author_lineage
        or author_result_value.program_ref != author.program_ref
        or author_result_value.semantic_attempt_ref != author.semantic_attempt_ref
        or author_result_value.candidate_ref != candidate_capsule.candidate_ref
        or author_result_value.effect_intent_ref != author.effect_intent_ref
        or author_result_value.author_command_ref != author.command_ref
        or author_result_value.attempt_fence_ref != author.attempt_fence_ref
        or author_result_value.effect_fence_ref != author.effect_fence_ref
        or author_result_value.delivery_attempt_ref != author.delivery_attempt_ref
        or any(
            (
                item.source_ref,
                item.source_invocation_ref,
                item.effect_intent_ref,
                item.effect_fence_ref,
                item.effect_fence_digest,
                item.delivery_attempt_ref,
                item.command_ref,
                item.command_digest,
                item.attempt_fence_ref,
                item.attempt_fence_digest,
            )
            != (
                author.source_ref,
                author.source_invocation_ref,
                author.effect_intent_ref,
                author.effect_fence_ref,
                author.effect_fence_digest,
                author.delivery_attempt_ref,
                author.command_ref,
                author.command_digest,
                author.attempt_fence_ref,
                author.attempt_fence_digest,
            )
            for item in author_observations
        )
    ):
        _fail("source_owner_mismatch")

    expected_support = (
        (
            "review_observation_membership", 1, 0,
            review_membership["schema_id"], review_membership["membership_ref"],
            review_membership["membership_digest"],
        ),
        (
            "author_worker_result_membership", 2, 0,
            author_result_membership["schema_id"], author_result_membership["membership_ref"],
            author_result_membership["membership_digest"],
        ),
    )
    if tuple(
        (entry.role, entry.rank, entry.ordinal, entry.source_schema_id, entry.source_ref, entry.source_digest)
        for entry in support_set.entries
    ) != expected_support:
        _fail("source_owner_mismatch")

    candidate = typing.cast(
        PostExecutionReviewerSeparationEvaluationV1,
        PostExecutionReviewerSeparationEvaluationV1.from_supplied(value),
    )
    if review_observation.source_kind != "independent_reviewer" or author.source_kind != "worker":
        expected_result = ("conflict", "source_role_conflict")
    elif review_observation.source_invocation_ref == author.source_invocation_ref:
        expected_result = ("not_separate", "review_source_invocation_reused")
    elif (
        review_observation.effect_intent_ref == author.effect_intent_ref
        or review_observation.effect_fence_ref == author.effect_fence_ref
        or review_observation.effect_fence_digest == author.effect_fence_digest
    ):
        expected_result = ("not_separate", "review_effect_identity_reused")
    elif review_observation.delivery_attempt_ref == author.delivery_attempt_ref:
        expected_result = ("not_separate", "review_delivery_identity_reused")
    else:
        expected_result = ("separate", "governed_review_graph_separate")

    expected = {
        "phase_basis_ref": phase_pair[0],
        "phase_basis_digest": phase_pair[1],
        "review_membership_schema_id": review_membership["schema_id"],
        "review_membership_ref": review_membership["membership_ref"],
        "review_membership_digest": review_membership["membership_digest"],
        "review_value_schema_id": review_observation.schema_id,
        "review_value_ref": review_observation.observation_ref,
        "review_value_digest": review_observation.observation_digest,
        "review_relation_row_schema_id": review_relation["schema_id"],
        "review_relation_ref": review_relation["relation_ref"],
        "review_relation_digest": review_relation["relation_digest"],
        "review_relation_row_digest": review_relation["relation_row_digest"],
        "review_relation_schema_id": review_relation["relation_schema_id"],
        "author_result_membership_schema_id": author_result_membership["schema_id"],
        "author_result_membership_ref": author_result_membership["membership_ref"],
        "author_result_membership_digest": author_result_membership["membership_digest"],
        "author_result_value_schema_id": author_result_value.schema_id,
        "author_result_value_ref": author_result_value.value_ref,
        "author_result_value_digest": author_result_value.value_digest,
        "author_result_relation_row_schema_id": author_result_relation["schema_id"],
        "author_result_relation_ref": author_result_relation["relation_ref"],
        "author_result_relation_digest": author_result_relation["relation_digest"],
        "author_result_relation_row_digest": author_result_relation["relation_row_digest"],
        "author_result_relation_schema_id": author_result_relation["relation_schema_id"],
        "author_observation_locators": locators,
        "review_source_kind": review_observation.source_kind,
        "review_source_ref": review_observation.source_ref,
        "review_source_invocation_ref": review_observation.source_invocation_ref,
        "author_source_kind": author.source_kind,
        "author_source_ref": author.source_ref,
        "author_source_invocation_ref": author.source_invocation_ref,
        "review_effect_intent_ref": review_observation.effect_intent_ref,
        "review_effect_fence_ref": review_observation.effect_fence_ref,
        "review_effect_fence_digest": review_observation.effect_fence_digest,
        "review_delivery_attempt_ref": review_observation.delivery_attempt_ref,
        "author_effect_intent_ref": author.effect_intent_ref,
        "author_effect_fence_ref": author.effect_fence_ref,
        "author_effect_fence_digest": author.effect_fence_digest,
        "author_delivery_attempt_ref": author.delivery_attempt_ref,
        "author_command_ref": author.command_ref,
        "author_command_digest": author.command_digest,
        "attempt_fence_ref": author.attempt_fence_ref,
        "attempt_fence_digest": author.attempt_fence_digest,
        "program_ref": author.program_ref,
        "program_version_ref": author.program_version_ref,
        "accepted_intent_revision_ref": author.accepted_intent_revision_ref,
        "work_item_ref": author.work_item_ref,
        "work_item_revision_ref": author.work_item_revision_ref,
        "semantic_attempt_ref": author.semantic_attempt_ref,
        "candidate_ref": candidate_capsule.candidate_ref,
        "capsule_manifest_ref": candidate_capsule.capsule_manifest_ref,
        "portable_capsule_digest": candidate_capsule.portable_capsule_digest,
        "support_set_ref": support_set.support_set_ref,
        "support_set_digest": support_set.support_set_digest,
        "status": expected_result[0],
        "reason": expected_result[1],
        "evaluated_at": review_observation.observed_at,
    }
    candidate_mapping = candidate.to_mapping()
    if any(not _exact_equal(candidate_mapping[name], member) for name, member in expected.items()):
        _fail("source_owner_mismatch")
    return candidate


def construct_post_execution_semantic_review_input(
    value: object,
    *,
    lineage_context: object,
    role_entries: tuple[PostExecutionSemanticReviewRoleEntryV2, ...],
    safe_projection: object,
    private_manifest: object,
) -> PostExecutionSemanticReviewInputContextV1:
    """Construct-check the exact T1 context from its independently typed inputs."""

    if type(role_entries) is not tuple or len(role_entries) != 9:
        _fail("invalid_cardinality")
    lineage = Section41PostExecutionSemanticReviewLineageContextV1.from_supplied(lineage_context)
    safe = PostExecutionModelInputSafeProjectionV2.from_supplied(safe_projection)
    private = PostExecutionPrivateInputManifestV2.from_supplied(private_manifest)
    candidate = typing.cast(
        PostExecutionSemanticReviewInputContextV1,
        PostExecutionSemanticReviewInputContextV1.from_supplied(value),
    )
    if tuple(candidate.role_entries) != role_entries:
        _fail("relation_mismatch")
    if (
        candidate.lineage_context_schema_id != lineage.schema_id
        or candidate.lineage_context_ref != lineage.lineage_context_ref
        or candidate.lineage_context_digest != lineage.lineage_context_digest
        or candidate.model_input_safe_projection_schema_id != safe.schema_id
        or candidate.model_input_safe_projection_ref != safe.projection_ref
        or candidate.model_input_safe_projection_digest != safe.projection_digest
        or candidate.private_input_manifest_schema_id != private.schema_id
        or candidate.private_input_manifest_ref != private.manifest_ref
        or candidate.private_input_manifest_digest != private.manifest_digest
    ):
        _fail("relation_mismatch")
    return candidate


def evaluate_post_execution_source_effect_ceiling(
    value: object,
    *,
    attempt_fence: _worker_values.AttemptFenceV1,
    effect_fence: _worker_values.EffectFenceV1,
    authority_observation: _phase_values.RW0AuthorityVerificationObservationV1,
    standing_policy_matrix: _PostExecutionValue,
    support_set: PostExecutionSupportSetV1,
) -> PostExecutionSourceEffectCeilingEvidenceV1:
    """Derive the ceiling assertion from the exact five-owner support set."""

    if (
        type(attempt_fence) is not _worker_values.AttemptFenceV1
        or type(effect_fence) is not _worker_values.EffectFenceV1
        or type(authority_observation)
        is not _phase_values.RW0AuthorityVerificationObservationV1
        or not isinstance(standing_policy_matrix, _PostExecutionValue)
        or standing_policy_matrix._V_NUMBER != "V17"
        or type(support_set) is not PostExecutionSupportSetV1
    ):
        _fail("source_owner_mismatch")
    candidate = typing.cast(
        PostExecutionSourceEffectCeilingEvidenceV1,
        PostExecutionSourceEffectCeilingEvidenceV1.from_supplied(value),
    )
    standing_policy_matrix._validate_value()
    support_set._validate_value()
    attempt_mapping = attempt_fence.to_mapping()
    effect_mapping = effect_fence.to_mapping()
    authority_mapping = authority_observation.to_mapping()
    expected_support = (
        ("attempt_fence", 1, attempt_mapping["schema_id"], attempt_mapping["attempt_fence_ref"], attempt_mapping["attempt_fence_digest"]),
        ("effect_fence", 2, effect_mapping["schema_id"], effect_mapping["effect_fence_ref"], effect_mapping["effect_fence_digest"]),
        ("authority_observation", 3, authority_mapping["schema_id"], authority_mapping["observation_ref"], authority_mapping["observation_digest"]),
        ("standing_policy_matrix", 4, standing_policy_matrix.schema_id, standing_policy_matrix.matrix_ref, standing_policy_matrix.matrix_digest),
        (
            "ceiling_profile", 5,
            "governed-execution.nwp-post-execution-source-effect-ceiling-profile.v1",
            _POST_EXECUTION_SOURCE_EFFECT_CEILING_PROFILE_REF,
            _POST_EXECUTION_SOURCE_EFFECT_CEILING_PROFILE_DIGEST,
        ),
    )
    observed_support = tuple(
        (entry.role, entry.rank, entry.source_schema_id, entry.source_ref, entry.source_digest)
        for entry in support_set.entries
    )
    if observed_support != expected_support:
        _fail("source_owner_mismatch")
    expected = {
        "program_ref": attempt_mapping["program_ref"],
        "program_version_ref": attempt_mapping["program_version_ref"],
        "accepted_intent_revision_ref": attempt_mapping["accepted_intent_revision_ref"],
        "work_item_ref": attempt_mapping["work_item_ref"],
        "work_item_revision_ref": attempt_mapping["work_item_revision_ref"],
        "semantic_attempt_ref": attempt_mapping["semantic_attempt_ref"],
        "candidate_ref": effect_mapping["candidate_ref"],
        "effect_intent_ref": effect_mapping["effect_intent_ref"],
        "repository_ref": effect_mapping["repository_ref"],
        "base_git_object_format": effect_mapping["base_git_object_format"],
        "base_git_oid": effect_mapping["base_git_oid"],
        "source_effect_class": effect_mapping["effect_class"],
        "source_effect_ceilings": effect_mapping["effect_ceilings"],
        "path_scope_digest": authority_mapping["path_scope_digest"],
        "attempt_fence_schema_id": attempt_mapping["schema_id"],
        "attempt_fence_ref": attempt_mapping["attempt_fence_ref"],
        "attempt_fence_digest": attempt_mapping["attempt_fence_digest"],
        "attempt_allowed_effect_classes": attempt_mapping["allowed_effect_classes"],
        "attempt_ceilings": attempt_mapping["aggregate_ceilings"],
        "attempt_fence_expires_at": attempt_mapping["expires_at"],
        "effect_fence_schema_id": effect_mapping["schema_id"],
        "effect_fence_ref": effect_mapping["effect_fence_ref"],
        "effect_fence_digest": effect_mapping["effect_fence_digest"],
        "effect_fence_class": effect_mapping["effect_class"],
        "effect_ceilings": effect_mapping["effect_ceilings"],
        "effect_fence_expires_at": effect_mapping["expires_at"],
        "authority_schema_id": authority_mapping["schema_id"],
        "authority_observation_ref": authority_mapping["observation_ref"],
        "authority_observation_digest": authority_mapping["observation_digest"],
        "authority_status": authority_mapping["status"],
        "authority_family_status": authority_mapping["family_status"],
        "authority_revocation_status": authority_mapping["revocation_status"],
        "authority_allowed_effect_classes": authority_mapping["allowed_effect_classes"],
        "authority_ceilings": authority_mapping["parent_ceilings"],
        "authority_grant_expires_at": authority_mapping["grant_expires_at"],
        "authority_observation_expires_at": authority_mapping["observation_expires_at"],
        "support_set_ref": support_set.support_set_ref,
        "support_set_digest": support_set.support_set_digest,
    }
    if any(
        not _exact_equal(candidate.to_mapping()[field], expected_value)
        for field, expected_value in expected.items()
    ):
        _fail("source_owner_mismatch")
    if any(
        not _exact_equal(effect_mapping[field], attempt_mapping[field])
        for field in (
            "program_ref", "program_version_ref", "accepted_intent_revision_ref",
            "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
            "repository_ref", "base_git_object_format", "base_git_oid",
            "attempt_fence_ref", "attempt_fence_digest", "parent_standing_grant_ref",
            "parent_standing_grant_digest", "path_ceiling", "global_stop_ref",
            "global_stop_version",
        )
    ):
        _fail("source_owner_mismatch")
    authority_pairs = (
        ("parent_grant_ref", attempt_mapping["parent_standing_grant_ref"]),
        ("parent_grant_digest", attempt_mapping["parent_standing_grant_digest"]),
        ("attempt_basis_ref", attempt_mapping["attempt_authorization_ref"]),
        ("attempt_basis_digest", attempt_mapping["attempt_authorization_digest"]),
        ("effect_basis_ref", effect_mapping["effect_authorization_ref"]),
        ("effect_basis_digest", effect_mapping["effect_authorization_digest"]),
        ("attempt_fence_ref", attempt_mapping["attempt_fence_ref"]),
        ("attempt_fence_digest", attempt_mapping["attempt_fence_digest"]),
        ("effect_fence_ref", effect_mapping["effect_fence_ref"]),
        ("effect_fence_digest", effect_mapping["effect_fence_digest"]),
        ("repository_ref", attempt_mapping["repository_ref"]),
        ("base_git_object_format", attempt_mapping["base_git_object_format"]),
        ("base_git_oid", attempt_mapping["base_git_oid"]),
        ("effect_class", effect_mapping["effect_class"]),
        ("global_stop_ref", attempt_mapping["global_stop_ref"]),
        ("global_stop_version", attempt_mapping["global_stop_version"]),
    )
    if any(
        not _exact_equal(authority_mapping[name], expected_value)
        for name, expected_value in authority_pairs
    ):
        _fail("source_owner_mismatch")
    policy_pairs = (
        ("program_ref", attempt_mapping["program_ref"]),
        ("program_version_ref", attempt_mapping["program_version_ref"]),
        ("accepted_intent_revision_ref", attempt_mapping["accepted_intent_revision_ref"]),
        ("work_item_ref", attempt_mapping["work_item_ref"]),
        ("work_item_revision_ref", attempt_mapping["work_item_revision_ref"]),
        ("semantic_attempt_ref", attempt_mapping["semantic_attempt_ref"]),
        ("candidate_ref", effect_mapping["candidate_ref"]),
        ("effect_intent_ref", effect_mapping["effect_intent_ref"]),
        ("author_command_ref", effect_mapping["command_ref"]),
        ("source_effect_fence_ref", effect_mapping["effect_fence_ref"]),
        ("source_effect_fence_digest", effect_mapping["effect_fence_digest"]),
        ("source_effect_class", effect_mapping["effect_class"]),
        ("parent_grant_ref", authority_mapping["parent_grant_ref"]),
        ("parent_grant_digest", authority_mapping["parent_grant_digest"]),
        ("grant_family_ref", authority_mapping["grant_family_ref"]),
        ("grant_family_digest", authority_mapping["grant_family_digest"]),
        ("audience_ref", authority_mapping["audience_ref"]),
        ("repository_ref", authority_mapping["repository_ref"]),
        ("path_scope_digest", authority_mapping["path_scope_digest"]),
    )
    if any(
        not _exact_equal(getattr(standing_policy_matrix, name), expected_value)
        for name, expected_value in policy_pairs
    ) or standing_policy_matrix.to_mapping()["policy_ceilings"] != authority_mapping[
        "parent_ceilings"
    ]:
        _fail("source_owner_mismatch")
    return candidate


def construct_post_execution_support_set(
    value: object,
    *,
    entries: tuple[PostExecutionSupportEntryV1, ...],
) -> PostExecutionSupportSetV1:
    """Construct-check a support set from its exact ordered owner inventory."""

    if type(entries) is not tuple or not 1 <= len(entries) <= 16:
        _fail("invalid_cardinality")
    if any(type(entry) is not PostExecutionSupportEntryV1 for entry in entries):
        _fail("invalid_nested_value")
    candidate = typing.cast(
        PostExecutionSupportSetV1,
        PostExecutionSupportSetV1.from_supplied(value),
    )
    if tuple(candidate.entries) != entries:
        _fail("relation_mismatch")
    return candidate


def validate_post_execution_validation_result_set(
    value: object,
    *,
    source_observation: _worker_values.WorkerObservationV1,
    requirement_evidence: _requirement_values.DevelopmentValidationRequirementEvidenceV1,
    tool_qualification: _phase_values.RW0EffectHostQualificationV1,
) -> PostExecutionValidationResultSetV1:
    """Derive and verify validation-result fields from one current observation."""

    if (
        type(source_observation) is not _worker_values.WorkerObservationV1
        or type(requirement_evidence)
        is not _requirement_values.DevelopmentValidationRequirementEvidenceV1
        or type(tool_qualification) is not _phase_values.RW0EffectHostQualificationV1
        or tool_qualification.result != "qualified"
    ):
        _fail("source_owner_mismatch")
    candidate = typing.cast(
        PostExecutionValidationResultSetV1,
        PostExecutionValidationResultSetV1.from_supplied(value),
    )
    _require_action_fields(candidate, source_observation, _OBSERVATION_RESULT_PAIRS)
    _require_action_fields(candidate, requirement_evidence, (
        ("requirement_evidence_schema_id", "schema_id"),
        ("requirement_evidence_ref", "requirement_ref"),
        ("requirement_evidence_safe_digest", "safe_evidence_digest"),
        ("requirement_digest", "requirement_digest"),
        ("requirement_work_spec_ref", "work_spec_ref"),
        ("requirement_work_spec_digest", "work_spec_digest"),
    ))
    _require_action_fields(candidate, tool_qualification, (
        ("tool_profile_ref", "required_validation_tool_profile_ref"),
        ("tool_profile_digest", "required_validation_tool_profile_digest"),
        ("tool_qualification_schema_id", "schema_id"),
        ("tool_qualification_ref", "qualification_ref"),
        ("tool_qualification_digest", "qualification_digest"),
    ))
    return candidate


def validate_validation_disposition(
    value: object,
    *,
    validation_result_set: object,
) -> ValidationDispositionV1:
    """Verify the expected disposition against the independently derived result set."""

    candidate = typing.cast(
        ValidationDispositionV1,
        ValidationDispositionV1.from_supplied(value),
    )
    result_set = typing.cast(
        PostExecutionValidationResultSetV1,
        PostExecutionValidationResultSetV1.from_supplied(validation_result_set),
    )
    _require_action_fields(candidate, result_set, (
        ("source_observation_schema_id", "source_observation_schema_id"),
        ("source_observation_ref", "source_observation_ref"),
        ("source_observation_digest", "source_observation_digest"),
        ("source_kind", "source_kind"), ("source_ref", "source_ref"),
        ("source_invocation_ref", "source_invocation_ref"),
        ("source_outcome", "source_outcome"), ("source_reason_code", "source_reason_code"),
        ("source_evidence_refs", "source_evidence_refs"), ("source_observed_at", "source_observed_at"),
        ("validation_result_set_schema_id", "schema_id"),
        ("validation_result_set_ref", "result_set_ref"),
        ("validation_result_set_digest", "result_set_digest"),
        ("result", "result"), ("repairability", "repairability"),
        ("reason", "reason"), ("evaluated_at", "evaluated_at"), ("expires_at", "expires_at"),
    ))
    return candidate
