"""Closed, private value contracts for one native post-D2 proposal record."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import typing

from ._cognitive_proposal_value_support import _require_safe_ref, _require_sha256
from ._development_bound_effect_establishment_contracts import (
    _development_bound_effect_establishment_write_plan,
)
from ._post_execution_evidence_values import (
    CandidateCapsuleSafeProjectionV1,
    PostExecutionModelInputBindingV2,
    PostExecutionModelInputSafeProjectionV2,
    PostExecutionPrivateInputManifestV2,
    PostExecutionSemanticReviewInputContextV1,
    Section41PostExecutionSemanticReviewLineageContextV1,
    _canonical_bytes,
    _domain_separated_digest,
)
from ._rw0_d2_handback import RW0D2OfflineRun
from ._rw0_d2b_proposal import PostExecutionSemanticReviewSafeProjectionV1
from ._rw0_d2a_evidence import _D2_LEGAL_RANKS, _seal_post_value

__all__: tuple[str, ...] = ()

_PHASE = "post_execution_semantic_review"
_COMMAND_SCHEMA = "governed-execution.nwp-section41-record-post-execution-proposal-command.v1"
_RESULT_SCHEMA = "governed-execution.nwp-section41-record-post-execution-proposal-result.v1"
_BASIS_DOMAIN = "governed-execution.nwp-section41-post-execution-safe-basis.v1.identity"
_GRAPH_DOMAIN = "governed-execution.nwp-section41-post-execution-mutation-graph.v1.identity"
_COMMITTED_DOMAIN = "governed-execution.nwp-section41-post-execution-committed-result.v1.identity"
_RECEIPT_DOMAIN = "governed-execution.nwp-section41-post-execution-proposal-receipt-row.v1.identity"
_COMMAND_DOMAIN = _COMMAND_SCHEMA + ".identity"
_RESULT_DOMAIN = _RESULT_SCHEMA + ".identity"
_SAFE_KEYS = frozenset((
    "lineage_v01", "context_v02", "capsule_safe_projection_v04",
    "model_safe_projection_v05", "private_input_manifest_v07",
    "model_input_binding_v09", "artifact_safe_projection",
    "d2_checkpoint_witness",
))
_ROLE_ORDER = (
    "candidate_capsule", "worker_result", "validation_result",
    "independent_review", "standing_policy", "risk_lane",
    "authority_currentness_attestation", "global_stop", "effect_ceiling",
)
_WITNESS_KEYS = frozenset(("checked_memberships", "bound_effects", "child_attestations"))


def _invalid() -> typing.NoReturn:
    raise ValueError("invalid_post_execution_proposal_contract") from None


def _digest(domain: str, value: object) -> str:
    return _domain_separated_digest(domain, value)


def _safe_ref(value: object) -> str:
    try:
        return _require_safe_ref(value)
    except ValueError:
        _invalid()


def _sha(value: object) -> str:
    try:
        return _require_sha256(value)
    except ValueError:
        _invalid()


def _exact_json(value: object) -> bytes:
    if type(value) not in (dict, list, str, int, bool, type(None)):
        _invalid()
    def walk(item: object, depth: int) -> None:
        if depth > 24:
            _invalid()
        if type(item) is dict:
            if any(type(key) is not str for key in item):
                _invalid()
            for child in item.values():
                walk(child, depth + 1)
        elif type(item) is list:
            for child in item:
                walk(child, depth + 1)
        elif type(item) not in (str, int, bool, type(None)):
            _invalid()
    walk(value, 0)
    result = _canonical_bytes(value)
    if not 1 <= len(result) <= 131072:
        _invalid()
    return result


def _pairs_unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _invalid()
        result[key] = value
    return result


def _ordered_typed_mapping(cls: type, mapping: object) -> dict[str, object]:
    if type(mapping) is not dict or frozenset(mapping) != frozenset(cls._FIELDS):
        _invalid()
    result: dict[str, object] = {}
    for name in cls._FIELDS:
        member = mapping[name]
        nested = cls._NESTED.get(name)
        if nested is not None and type(member) is dict:
            member = _ordered_typed_mapping(nested, member)
        elif nested is not None and type(member) is list:
            member = [_ordered_typed_mapping(nested, entry) for entry in member]
        result[name] = member
    return result


def checked_safe_basis_bytes(value: object) -> bytes:
    """Validate the exact nested retention grammar before custody in SQLite."""
    if type(value) is bytes:
        if not 1 <= len(value) <= 131072:
            _invalid()
        try:
            decoded = json.loads(value.decode("utf-8"), object_pairs_hook=_pairs_unique)
        except (UnicodeError, ValueError, TypeError):
            _invalid()
        if _exact_json(decoded) != value:
            _invalid()
        value = decoded
    if type(value) is not dict or frozenset(value) != _SAFE_KEYS:
        _invalid()
    basis = typing.cast(dict[str, object], value)
    try:
        typed = (
            (Section41PostExecutionSemanticReviewLineageContextV1, "lineage_v01"),
            (PostExecutionSemanticReviewInputContextV1, "context_v02"),
            (CandidateCapsuleSafeProjectionV1, "capsule_safe_projection_v04"),
            (PostExecutionModelInputSafeProjectionV2, "model_safe_projection_v05"),
            (PostExecutionPrivateInputManifestV2, "private_input_manifest_v07"),
            (PostExecutionModelInputBindingV2, "model_input_binding_v09"),
        )
        for cls, key in typed:
            mapping = basis[key]
            if (type(mapping) is not dict
                    or cls.from_mapping(_ordered_typed_mapping(cls, mapping)).to_mapping()
                    != mapping):
                _invalid()
        artifact = basis["artifact_safe_projection"]
        if type(artifact) is not dict:
            _invalid()
        if PostExecutionSemanticReviewSafeProjectionV1(**artifact).to_mapping() != artifact:
            _invalid()
        witness = basis["d2_checkpoint_witness"]
        if type(witness) is not dict or frozenset(witness) != _WITNESS_KEYS:
            _invalid()
        members = witness["checked_memberships"]
        effects = witness["bound_effects"]
        children = witness["child_attestations"]
        if (type(members) is not list or len(members) not in (13, 14)
                or type(effects) is not list or len(effects) != 2
                or type(children) is not list or len(children) != 3):
            _invalid()
        if tuple(member.get("kind_rank") if type(member) is dict else None
                 for member in members) not in _D2_LEGAL_RANKS:
            _invalid()
        for member in members:
            if type(member) is not dict or frozenset(member) != frozenset((
                "kind_rank", "membership_ref", "membership_digest",
                "mutation_ref", "admission_graph_digest",
            )):
                _invalid()
            if type(member["kind_rank"]) is not int or not 1 <= member["kind_rank"] <= 15:
                _invalid()
            for name in ("membership_ref", "mutation_ref"):
                _safe_ref(member[name])
            for name in ("membership_digest", "admission_graph_digest"):
                _sha(member[name])
        for effect, expected in zip(effects, ("validate_candidate", "review_candidate"), strict=True):
            if (type(effect) is not dict or frozenset(effect) != frozenset((
                "effect_class", "mutation_ref", "receipt_graph_digest",
            )) or effect["effect_class"] != expected):
                _invalid()
            _safe_ref(effect["mutation_ref"])
            _sha(effect["receipt_graph_digest"])
        for child, expected in zip(children, ("validator", "reviewer", "model"), strict=True):
            if (type(child) is not dict or frozenset(child) != frozenset((
                "role", "safe_outcome_digest", "clean_success", "cleanup_complete",
            )) or child["role"] != expected or child["clean_success"] is not True
                    or child["cleanup_complete"] is not True):
                _invalid()
            _sha(child["safe_outcome_digest"])
        context = basis["context_v02"]
        if (context["lineage_context_ref"] != basis["lineage_v01"]["lineage_context_ref"]
                or context["lineage_context_digest"] != basis["lineage_v01"]["lineage_context_digest"]
                or context["model_input_safe_projection_digest"] != basis["model_safe_projection_v05"]["projection_digest"]
                or context["private_input_manifest_digest"] != basis["private_input_manifest_v07"]["manifest_digest"]
                or basis["model_input_binding_v09"]["input_context_digest"] != context["input_context_digest"]
                or basis["artifact_safe_projection"]["input_context_digest"] != context["input_context_digest"]):
            _invalid()
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        _invalid()
    return _exact_json(basis)


def safe_basis_digest(value: bytes) -> str:
    checked_safe_basis_bytes(value)
    return hashlib.sha256(_BASIS_DOMAIN.encode("utf-8") + b"\0" + value).hexdigest()


@dataclass(frozen=True, slots=True, repr=False)
class PostExecutionEvidenceSelectorV1:
    role: str
    rank: int
    ordinal: int
    schema_id: str
    ref: str
    digest: str

    def __post_init__(self) -> None:
        if (type(self.role) is not str or self.role not in _ROLE_ORDER
                or type(self.rank) is not int or self.rank != _ROLE_ORDER.index(self.role) + 5
                or type(self.ordinal) is not int or self.ordinal != 0
                or type(self.schema_id) is not str or not self.schema_id.startswith("governed-execution.")):
            _invalid()
        _safe_ref(self.ref)
        _sha(self.digest)

    def to_mapping(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in self.__slots__}


@dataclass(frozen=True, slots=True, repr=False)
class RecordPostExecutionProposalCommandV1:
    mutation_ref: str
    phase_basis_ref: str
    phase_basis_digest: str
    context_ref: str
    context_digest: str
    source_invocation_ref: str
    source_invocation_digest: str
    artifact_ref: str
    artifact_digest: str
    artifact_binding_digest: str
    proposal_ref: str
    proposal_digest: str
    evidence_set_ref: str
    evidence_set_digest: str
    evidence_selectors: tuple[PostExecutionEvidenceSelectorV1, ...]
    safe_basis_digest: str
    c1_mutation_ref: str
    c1_membership_ref: str
    command_digest: str = ""
    schema_id: str = field(default=_COMMAND_SCHEMA, init=False)

    def __post_init__(self) -> None:
        for name in (
            "mutation_ref", "phase_basis_ref", "context_ref", "source_invocation_ref",
            "artifact_ref", "proposal_ref", "evidence_set_ref", "c1_mutation_ref",
            "c1_membership_ref",
        ):
            _safe_ref(getattr(self, name))
        for name in (
            "phase_basis_digest", "context_digest", "source_invocation_digest",
            "artifact_digest", "artifact_binding_digest", "proposal_digest",
            "evidence_set_digest", "safe_basis_digest",
        ):
            _sha(getattr(self, name))
        if (type(self.evidence_selectors) is not tuple
                or len(self.evidence_selectors) != 9
                or any(type(item) is not PostExecutionEvidenceSelectorV1
                       for item in self.evidence_selectors)
                or tuple(item.role for item in self.evidence_selectors) != _ROLE_ORDER):
            _invalid()
        expected = _digest(_COMMAND_DOMAIN, self.identity_mapping())
        if self.command_digest and self.command_digest != expected:
            _invalid()
        object.__setattr__(self, "command_digest", expected)

    def identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            **{name: getattr(self, name) for name in self.__slots__
               if name not in ("schema_id", "command_digest", "evidence_selectors")},
            "evidence_selectors": [item.to_mapping() for item in self.evidence_selectors],
        }


@dataclass(frozen=True, slots=True, repr=False)
class RecordPostExecutionProposalResultV1:
    mutation_ref: str
    command_digest: str
    disposition: str
    proposal_ref: str
    context_ref: str
    context_row_digest: str
    mutation_graph_digest: str
    committed_result_digest: str
    receipt_digest: str
    committed_at: str
    result_digest: str = ""
    schema_id: str = field(default=_RESULT_SCHEMA, init=False)

    def __post_init__(self) -> None:
        for name in ("mutation_ref", "proposal_ref", "context_ref"):
            _safe_ref(getattr(self, name))
        for name in ("command_digest", "context_row_digest", "mutation_graph_digest",
                     "committed_result_digest", "receipt_digest"):
            _sha(getattr(self, name))
        if self.disposition not in ("fresh_committed", "exact_replay"):
            _invalid()
        if type(self.committed_at) is not str or len(self.committed_at) != 20:
            _invalid()
        identity = {name: getattr(self, name) for name in self.__slots__
                    if name != "result_digest"}
        expected = _digest(_RESULT_DOMAIN, identity)
        if self.result_digest and self.result_digest != expected:
            _invalid()
        object.__setattr__(self, "result_digest", expected)


@dataclass(frozen=True, slots=True, repr=False)
class PostExecutionProposalConflictV1:
    reason: str
    mutation_ref: str
    command_digest: str

    def __post_init__(self) -> None:
        if self.reason not in ("identity_conflict", "currentness_conflict", "route_conflict"):
            _invalid()
        _safe_ref(self.mutation_ref)
        _sha(self.command_digest)


@dataclass(frozen=True, slots=True, repr=False)
class PostExecutionProposalRecoveryV1:
    classification: str
    result: RecordPostExecutionProposalResultV1 | None = None

    def __post_init__(self) -> None:
        if self.classification not in (
            "committed_exact", "definitely_not_committed", "unresolved",
        ) or (self.classification == "committed_exact") != (
            type(self.result) is RecordPostExecutionProposalResultV1
        ):
            _invalid()


def _safe_child_digest(role: str, outcome: object) -> str:
    return _domain_separated_digest(
        "governed-execution.nwp-d2-child-safe-outcome-witness.v1.identity",
        {
            "role": role,
            "reason": outcome.reason,
            "exit_code": outcome.exit_code,
            "clean_success": outcome.clean_success,
            "cleanup_complete": outcome.cleanup_complete,
        },
    )


def prepare_record_command(
    run: RW0D2OfflineRun,
) -> tuple[RecordPostExecutionProposalCommandV1, bytes]:
    """Bind the exact original open run to one closed safe command and basis."""
    if type(run) is not RW0D2OfflineRun:
        raise ValueError("invalid_post_execution_run")
    run._require_open_owner()
    handback = run.handback
    handback.validate()
    if handback.status != "preadmission_ready":
        raise ValueError("post_execution_preadmission_unavailable")
    basis = handback.d1_handback.phase_basis
    lineage_cls = Section41PostExecutionSemanticReviewLineageContextV1
    lineage = _seal_post_value(lineage_cls, {
        "schema_id": lineage_cls._SCHEMA_ID,
        "proposal_phase": "post_execution_semantic_review",
        **basis.c2b3d_lineage.to_mapping(),
    })
    capsule = handback.evidence_checkpoint.capsule_manifest
    capsule_mapping = capsule.to_mapping()
    capsule_cls = CandidateCapsuleSafeProjectionV1
    capsule_safe = _seal_post_value(capsule_cls, {
        "schema_id": capsule_cls._SCHEMA_ID,
        **{name: capsule_mapping[name] for name in capsule_cls._FIELDS
           if name in capsule_mapping and name not in (
               "schema_id", "projection_ref", "projection_digest",
           )},
    })
    membership_witness = [{
        "kind_rank": family.admission_result.kind_rank,
        "membership_ref": family.admission_result.membership_ref,
        "membership_digest": family.admission_result.membership_digest,
        "mutation_ref": family.admission_result.mutation_ref,
        "admission_graph_digest": family.admission_result.admission_graph_digest,
    } for family in handback.checked_admissions]
    effect_witness = []
    for proof in handback.committed_bound_effects:
        plan = _development_bound_effect_establishment_write_plan(
            proof.command, proof.confirmed_result.transaction_timestamp,
        )
        effect_witness.append({
            "effect_class": proof.command.effect_class,
            "mutation_ref": proof.command.mutation_ref,
            "receipt_graph_digest": plan.mutation_receipt.mutation_graph_digest,
        })
    child_witness = [{
        "role": role,
        "safe_outcome_digest": _safe_child_digest(role, outcome),
        "clean_success": outcome.clean_success,
        "cleanup_complete": outcome.cleanup_complete,
    } for role, outcome in zip(
        ("validator", "reviewer", "model"), handback.child_outcomes, strict=True,
    )]
    safe_basis = {
        "lineage_v01": lineage.to_mapping(),
        "context_v02": handback.input_context.to_mapping(),
        "capsule_safe_projection_v04": capsule_safe.to_mapping(),
        "model_safe_projection_v05": (
            handback.evidence_supply.model_input_safe_projection.to_mapping()
        ),
        "private_input_manifest_v07": (
            handback.evidence_supply.private_input_manifest.to_mapping()
        ),
        "model_input_binding_v09": handback.model_input_binding.to_mapping(),
        "artifact_safe_projection": handback.safe_projection.to_mapping(),
        "d2_checkpoint_witness": {
            "checked_memberships": membership_witness,
            "bound_effects": effect_witness,
            "child_attestations": child_witness,
        },
    }
    encoded = checked_safe_basis_bytes(safe_basis)
    proposal = handback.proposal
    route_basis = {
        "phase_basis_ref": basis.basis_ref,
        "phase_basis_digest": basis.basis_digest,
        "proposal_ref": proposal.proposal_ref,
        "proposal_digest": proposal.proposal_digest,
    }
    route_digest = _domain_separated_digest(
        "governed-execution.nwp-section41-post-proposal-route.v1.identity",
        route_basis,
    )
    selectors = tuple(
        PostExecutionEvidenceSelectorV1(
            role=row.evidence_role, rank=row.role_rank, ordinal=row.ordinal,
            schema_id=entry.typed_schema_id,
            ref=row.evidence_ref, digest=row.evidence_digest,
        )
        for row, entry in zip(
            handback.evidence_bindings, handback.input_context.role_entries,
            strict=True,
        )
    )
    command = RecordPostExecutionProposalCommandV1(
        mutation_ref="section41-post-proposal." + route_digest[:32],
        phase_basis_ref=basis.basis_ref,
        phase_basis_digest=basis.basis_digest,
        context_ref=handback.input_context.input_context_ref,
        context_digest=handback.input_context.input_context_digest,
        source_invocation_ref=handback.model_source_invocation.source_invocation_ref,
        source_invocation_digest=handback.model_source_invocation.source_invocation_digest,
        artifact_ref=handback.artifact_binding.artifact_ref,
        artifact_digest=handback.artifact_binding.artifact_digest,
        artifact_binding_digest=handback.artifact_binding.artifact_binding_digest,
        proposal_ref=proposal.proposal_ref,
        proposal_digest=proposal.proposal_digest,
        evidence_set_ref=handback.evidence_set.evidence_set_ref,
        evidence_set_digest=handback.evidence_set.evidence_set_digest,
        evidence_selectors=selectors,
        safe_basis_digest=safe_basis_digest(encoded),
        c1_mutation_ref="rw0-post-proposal-admit." + route_digest[:32],
        c1_membership_ref="rw0-post-proposal-member." + route_digest[:32],
    )
    return command, encoded
