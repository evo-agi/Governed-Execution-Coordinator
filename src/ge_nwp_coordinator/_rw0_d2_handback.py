"""Resource-free D2 result and separate parent-owned D1 disposal wrapper."""

from __future__ import annotations

from dataclasses import dataclass, field
import os

from ._cognitive_proposal_semantic_values import (
    ModelProposalEvidenceBindingV1, ModelProposalEvidenceSetV1,
    ModelSourceInvocationV1, PreExecutionModelProposalV1,
    PrivateProposalArtifactBindingV1,
    _validate_semantic_value,
)
from ._post_execution_evidence_values import (
    CandidateCapsuleSafeProjectionV1, PostExecutionEvidenceSupplyV2,
    PostExecutionGlobalStopSnapshotV1, PostExecutionModelInputBindingV2,
    PostExecutionSemanticReviewInputContextV1,
    PostExecutionSourceEffectCeilingEvidenceV1, PostExecutionSupportEntryV1,
    PostExecutionSupportSetV1,
    Section41PostExecutionSemanticReviewLineageContextV1, _canonical_bytes,
    construct_post_execution_semantic_review_input,
    evaluate_post_execution_source_effect_ceiling,
    post_execution_global_stop_snapshot, validate_post_execution_evidence_supply,
)
from ._rw0_d2a_evidence import _seal_post_value
from .global_stop import GlobalStopState
from ._rw0_d1_handback import RW0D1HandbackV1, RW0D1OfflineRun
from ._rw0_d1_process_supervisor import D1ProcessOutcome
from ._rw0_d2a_handback import RW0D2BoundEffectProofV1, RW0D2EvidenceCheckpointV1
from ._rw0_d2b_proposal import (
    PostExecutionSemanticReviewArtifactV1,
    PostExecutionSemanticReviewSafeProjectionV1,
)
from ._sqlite_rw0_c1 import RW0C1CheckedEvidenceFamilyV1

__all__: tuple[str, ...] = ()

_B_ORDER = (
    "input_context", "evidence_supply", "model_input_binding",
    "model_source_invocation", "private_artifact", "artifact_binding",
    "safe_projection", "evidence_bindings", "evidence_set", "proposal",
    "model_process",
)
_A_RANK_PREFIX = (12, 12, 12, 12, 13, 14, 1, 1, 5, 6, 12, 6, 12, 1)
_NORMALIZED_NAMES = (
    "model_input_binding", "model_source_invocation", "private_artifact",
    "artifact_binding", "safe_projection", "evidence_set", "proposal",
)


def _fail() -> None:
    raise ValueError("invalid_d2_preadmission_handback") from None


def _validate_reason_reached_facts(handback: RW0D2PreadmissionHandbackV1) -> None:
    """Check the producer's closed explanations against the retained D2 prefix."""
    effects = len(handback.committed_bound_effects)
    admitted = len(handback.checked_admissions)
    children = len(handback.child_outcomes)
    a_only = (handback.evidence_checkpoint is None
              and not handback.evidence_bindings
              and all(getattr(handback, name) is None for name in _B_ORDER
                      if name != "evidence_bindings"))

    if handback.reason == "d1_stopped":
        if (handback.status != "stopped"
                or handback.d1_handback.status == "capsule_ready"
                or effects or admitted or children or not a_only):
            _fail()
        return
    if (handback.d1_handback.status != "capsule_ready"
            or not handback.d1_handback.workspace_cleaned):
        _fail()
    if handback.reason == "complete":
        if handback.status != "preadmission_ready":
            _fail()
        return
    if handback.status == "preadmission_ready":
        _fail()

    def checked_child_prefix() -> bool:
        return children == (0 if admitted <= 9 else 1 if admitted <= 11 else 2)

    def prior_children_clean() -> bool:
        return all(child.clean_success and child.cleanup_complete
                   for child in handback.child_outcomes)

    if handback.reason in ("invalid_d1_input", "d1_genesis_mismatch"):
        valid = (handback.status == "stopped" and a_only
                 and (effects, admitted, children) == (0, 0, 0))
    elif handback.reason in ("bound_effect_conflict", "bound_effect_commit_unresolved"):
        valid = (handback.status == "stopped" and a_only
                 and effects < 2 and admitted == children == 0)
    elif handback.reason in (
        "c1_admission_failed", "c1_readback_failed", "c1_commit_unresolved",
    ):
        valid = (handback.status == "stopped" and a_only and effects == 2
                 and admitted <= 13 and checked_child_prefix()
                 and prior_children_clean())
    elif handback.reason == "writer_cleanup_unresolved":
        valid = (handback.status == "cleanup_unresolved" and a_only
                 and ((effects < 2 and admitted == children == 0)
                      or (effects == 2 and admitted <= 13
                          and checked_child_prefix() and prior_children_clean())))
    elif handback.reason == "process_cleanup_unresolved":
        valid = (handback.status == "cleanup_unresolved" and a_only and effects == 2
                 and (admitted, children) in ((10, 1), (12, 2))
                 and all(child.clean_success and child.cleanup_complete
                         for child in handback.child_outcomes[:-1])
                 and not handback.child_outcomes[-1].cleanup_complete)
    elif handback.reason in ("validator_process_failed", "reviewer_process_failed"):
        expected = (10, 1) if handback.reason == "validator_process_failed" else (12, 2)
        valid = (handback.status == "stopped" and a_only and effects == 2
                 and (admitted, children) == expected
                 and all(child.clean_success and child.cleanup_complete
                         for child in handback.child_outcomes[:-1])
                 and handback.child_outcomes[-1].cleanup_complete
                 and not handback.child_outcomes[-1].clean_success)
    elif handback.reason == "reconstruction_not_independent":
        valid = (handback.status == "stopped" and a_only and effects == 2
                 and (admitted, children) == (13, 2) and prior_children_clean())
    elif handback.reason in ("evidence_incomplete", "evidence_mismatch"):
        valid = (handback.status == "stopped" and a_only and effects == 2
                 and (admitted, children) == (14, 2) and prior_children_clean())
    elif handback.reason in (
        "model_input_or_normalization_failed", "model_process_failed",
        "model_process_cleanup_unresolved", "model_workspace_cleanup_unresolved",
    ):
        paired_input = ((handback.input_context is None)
                        == (handback.evidence_supply is None))
        model_present = children == 3 and handback.model_process is not None
        complete_a = (handback.evidence_checkpoint is not None and effects == 2
                      and admitted == 14 and children in (2, 3) and paired_input)
        if handback.reason == "model_input_or_normalization_failed":
            valid = (handback.status == "stopped" and complete_a
                     and ((children == 2 and handback.model_process is None)
                          or (model_present and handback.input_context is not None
                              and handback.model_process.clean_success
                              and handback.model_process.cleanup_complete)))
        elif handback.reason == "model_process_failed":
            valid = (handback.status == "stopped" and complete_a and model_present
                     and handback.input_context is not None
                     and handback.model_process.cleanup_complete
                     and not handback.model_process.clean_success)
        elif handback.reason == "model_process_cleanup_unresolved":
            valid = (handback.status == "cleanup_unresolved" and complete_a
                     and model_present and handback.input_context is not None
                     and not handback.model_process.cleanup_complete)
        else:
            valid = (handback.status == "cleanup_unresolved" and complete_a
                     and model_present and handback.input_context is not None)
    else:
        valid = False
    if not valid:
        _fail()


def _validate_a_to_b_input_binding(handback: RW0D2PreadmissionHandbackV1) -> None:
    """Consume the retained A owners against every reached B input role."""
    if handback.input_context is None and handback.evidence_supply is None:
        return
    checkpoint = handback.evidence_checkpoint
    context = handback.input_context
    supply = handback.evidence_supply
    if checkpoint is None or context is None or supply is None:
        _fail()
    basis = checkpoint.d1_handback.phase_basis
    author = checkpoint.d1_handback.author_command
    capsule = checkpoint.capsule_manifest
    worker_family = checkpoint.admitted_families[5]
    authority_family = checkpoint.admitted_families[13]

    # V01 is derived from the retained phase lineage. B's clock is retained,
    # not resampled or compared with A's earlier observation time.
    lineage_cls = Section41PostExecutionSemanticReviewLineageContextV1
    lineage = _seal_post_value(lineage_cls, {
        "schema_id": lineage_cls._SCHEMA_ID,
        "proposal_phase": "post_execution_semantic_review",
        **basis.c2b3d_lineage.to_mapping(),
    })
    safe = supply.model_input_safe_projection
    private = supply.private_input_manifest
    construct_post_execution_semantic_review_input(
        context, lineage_context=lineage, role_entries=context.role_entries,
        safe_projection=safe, private_manifest=private,
    )
    if ((context.phase_basis_ref, context.phase_basis_digest)
            != (basis.basis_ref, basis.basis_digest)
            or supply.supply_created_at != context.constructed_at):
        _fail()

    # The stop state and the observation clock are B-time facts. Reconstruct
    # their existing pure relation, then bind the retained stop identity to A.
    supplies = supply.role_supplies
    stop_supply = supplies[7].to_mapping()
    ceiling_supply = supplies[8].to_mapping()
    current_stop = GlobalStopState.from_dict(
        stop_supply["source_binding_canonical_value"]
    )
    stop_raw = stop_supply["typed_canonical_value"]
    ceiling_raw = ceiling_supply["typed_canonical_value"]
    stop_support_raw = stop_supply["support_set_canonical_value"]
    ceiling_support_raw = ceiling_supply["support_set_canonical_value"]
    stop = PostExecutionGlobalStopSnapshotV1.from_mapping({
        name: stop_raw[name] for name in PostExecutionGlobalStopSnapshotV1._FIELDS
    })
    ceiling = PostExecutionSourceEffectCeilingEvidenceV1.from_mapping({
        name: ceiling_raw[name]
        for name in PostExecutionSourceEffectCeilingEvidenceV1._FIELDS
    })
    def support_set(raw: dict[str, object]) -> PostExecutionSupportSetV1:
        return PostExecutionSupportSetV1.from_mapping({
            name: ([
                {field: entry[field] for field in PostExecutionSupportEntryV1._FIELDS}
                for entry in raw["entries"]
            ] if name == "entries" else raw[name])
            for name in PostExecutionSupportSetV1._FIELDS
        })

    stop_support = support_set(stop_support_raw)
    ceiling_support = support_set(ceiling_support_raw)
    post_execution_global_stop_snapshot(
        stop, current_state=current_stop, updated_at=stop.global_stop_updated_at,
        support_set=stop_support,
    )
    evaluate_post_execution_source_effect_ceiling(
        ceiling, attempt_fence=author.attempt_fence,
        effect_fence=author.effect_fence,
        authority_observation=checkpoint.authority_sources[2],
        standing_policy_matrix=checkpoint.policy_matrices[0],
        support_set=ceiling_support,
    )
    if ((current_stop.stop_ref, current_stop.version, current_stop.status.value)
            != (basis.global_stop_ref, basis.global_stop_version,
                basis.global_stop_state)
            or stop.evaluated_at != context.constructed_at
            or ceiling.evaluated_at != context.constructed_at):
        _fail()

    owners = (
        capsule, worker_family.evidence_value,
        checkpoint.validation_disposition, checkpoint.review_disposition,
        checkpoint.policy_matrices[0], checkpoint.policy_matrices[1],
        authority_family.evidence_value, stop, ceiling,
    )
    supports = (
        (), (),
        (
            checkpoint.validation_source.observation,
            checkpoint.bound_effects[0].requirement,
            checkpoint.qualifications[0], checkpoint.validation_result_set,
            checkpoint.authority_sources[0], checkpoint.support_sets[1],
        ),
        (
            checkpoint.review_source.observation,
            checkpoint.bound_effects[1].requirement,
            checkpoint.qualifications[1], checkpoint.review_result_set,
            checkpoint.reviewer_separation, checkpoint.authority_sources[1],
            checkpoint.support_sets[2],
        ),
        (
            checkpoint.policy_sources[0], checkpoint.authority_sources[2],
            author.attempt_fence, author.effect_fence,
        ),
        (
            checkpoint.policy_sources[2], checkpoint.policy_sources[3],
            checkpoint.policy_sources[4], checkpoint.policy_sources[1],
        ),
        (),
        (current_stop, stop_supply["source_profile_canonical_value"]),
        (
            author.attempt_fence, author.effect_fence,
            checkpoint.authority_sources[2], checkpoint.policy_matrices[0],
            ceiling_supply["source_profile_canonical_value"],
        ),
    )
    validate_post_execution_evidence_supply(
        supply, role_values=owners, support_values=supports,
    )

    # The two direct C1 roles use this checkpoint's checked memberships. The
    # other seven roles have no direct C1 membership in the frozen grammar.
    for role_index, family in ((1, worker_family), (6, authority_family)):
        entry = context.role_entries[role_index]
        result = family.admission_result
        if ((entry.direct_c1_kind_rank, entry.direct_c1_membership_ref,
             entry.direct_c1_membership_digest)
                != (result.kind_rank, result.membership_ref,
                    result.membership_digest)):
            _fail()

    expected_bindings = (
        None, worker_family.relations.relations[0].binding.to_mapping(),
        checkpoint.validation_source.observation.to_mapping(),
        checkpoint.review_source.observation.to_mapping(),
        checkpoint.policy_sources[0].to_mapping(),
        checkpoint.policy_sources[4].to_mapping(), None,
        current_stop.to_dict(), author.effect_fence.to_mapping(),
    )
    for entry, supplied, expected in zip(
        context.role_entries, supplies, expected_bindings, strict=True,
    ):
        mapping = supplied.to_mapping()
        if (mapping["source_binding_canonical_value"] != expected
                or (entry.source_binding_schema_id, entry.source_binding_ref,
                    entry.source_binding_digest)
                != (supplied.source_binding_schema_id,
                    supplied.source_binding_ref, supplied.source_binding_digest)
                or (entry.source_profile_ref, entry.source_profile_digest)
                != (supplied.source_profile_ref,
                    supplied.source_profile_digest)):
            _fail()
    if (supplies[5].to_mapping()["source_profile_canonical_value"]
            != checkpoint.policy_sources[3].to_mapping()):
        _fail()

    # The private capsule carries the full A manifest, while the model's
    # first projection carries only its existing safe fields.
    capsule_cls = CandidateCapsuleSafeProjectionV1
    capsule_mapping = capsule.to_mapping()
    capsule_safe = _seal_post_value(capsule_cls, {
        "schema_id": capsule_cls._SCHEMA_ID,
        **{name: capsule_mapping[name] for name in capsule_cls._FIELDS
           if name in capsule_mapping
           and name not in ("schema_id", "projection_ref", "projection_digest")},
    })
    private_entry = private.entries[0]
    first_projection = safe.entries[0]
    if ((private_entry.typed_schema_id, private_entry.typed_value_ref,
         private_entry.typed_value_digest, private_entry.canonical_byte_length)
            != (capsule.schema_id, capsule.capsule_manifest_ref,
                capsule.portable_capsule_digest,
                len(_canonical_bytes(capsule_mapping)))
            or (first_projection.model_value_schema_id,
                first_projection.model_value_ref, first_projection.model_value_digest)
            != (capsule_safe.schema_id, capsule_safe.projection_ref,
                capsule_safe.projection_digest)):
        _fail()
    for entry, projection in zip(context.role_entries, safe.entries, strict=True):
        if ((entry.role, entry.role_rank, entry.ordinal,
             entry.typed_schema_id, entry.typed_value_ref, entry.typed_value_digest)
            != (projection.role, projection.role_rank, projection.ordinal,
                projection.typed_schema_id, projection.typed_value_ref,
                projection.typed_value_digest)):
            _fail()
        if entry.role_rank != 5 and (
            projection.model_value_schema_id, projection.model_value_ref,
            projection.model_value_digest,
        ) != (entry.typed_schema_id, entry.typed_value_ref,
              entry.typed_value_digest):
            _fail()


@dataclass(frozen=True, slots=True, repr=False)
class RW0D2PreadmissionHandbackV1:
    status: str
    reason: str
    d1_handback: RW0D1HandbackV1 = field(repr=False)
    committed_bound_effects: tuple[RW0D2BoundEffectProofV1, ...] = field(default=(), repr=False)
    checked_admissions: tuple[RW0C1CheckedEvidenceFamilyV1, ...] = field(default=(), repr=False)
    child_outcomes: tuple[D1ProcessOutcome, ...] = field(default=(), repr=False)
    evidence_checkpoint: RW0D2EvidenceCheckpointV1 | None = field(default=None, repr=False)
    input_context: PostExecutionSemanticReviewInputContextV1 | None = field(default=None, repr=False)
    evidence_supply: PostExecutionEvidenceSupplyV2 | None = field(default=None, repr=False)
    model_input_binding: PostExecutionModelInputBindingV2 | None = field(default=None, repr=False)
    model_source_invocation: ModelSourceInvocationV1 | None = field(default=None, repr=False)
    private_artifact: PostExecutionSemanticReviewArtifactV1 | None = field(default=None, repr=False)
    artifact_binding: PrivateProposalArtifactBindingV1 | None = field(default=None, repr=False)
    safe_projection: PostExecutionSemanticReviewSafeProjectionV1 | None = field(default=None, repr=False)
    evidence_bindings: tuple[ModelProposalEvidenceBindingV1, ...] = field(default=(), repr=False)
    evidence_set: ModelProposalEvidenceSetV1 | None = field(default=None, repr=False)
    proposal: PreExecutionModelProposalV1 | None = field(default=None, repr=False)
    model_process: D1ProcessOutcome | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if (type(self) is not RW0D2PreadmissionHandbackV1
                or type(self.status) is not str
                or self.status not in ("preadmission_ready", "stopped", "cleanup_unresolved")
                or type(self.reason) is not str or not self.reason
                or len(self.reason) > 96 or not self.reason.replace("_", "").isalnum()
                or type(self.d1_handback) is not RW0D1HandbackV1
                or type(self.committed_bound_effects) is not tuple
                or len(self.committed_bound_effects) > 2
                or type(self.checked_admissions) is not tuple
                or len(self.checked_admissions) > 14
                or type(self.child_outcomes) is not tuple
                or len(self.child_outcomes) > 3
                or type(self.evidence_bindings) is not tuple
                or len(self.evidence_bindings) not in (0, 9)):
            _fail()
        try:
            self.d1_handback.validate()
            for proof in self.committed_bound_effects:
                if type(proof) is not RW0D2BoundEffectProofV1:
                    _fail()
                proof.validate()
            if tuple(proof.command.effect_class for proof in self.committed_bound_effects) != (
                "validate_candidate", "review_candidate"
            )[:len(self.committed_bound_effects)]:
                _fail()
            for family in self.checked_admissions:
                if type(family) is not RW0C1CheckedEvidenceFamilyV1:
                    _fail()
                family.validate()
            if tuple(family.admission_result.kind_rank for family in self.checked_admissions) != (
                _A_RANK_PREFIX[:len(self.checked_admissions)]
            ):
                _fail()
            for process in self.child_outcomes:
                if type(process) is not D1ProcessOutcome:
                    _fail()
                process.validate()
            if (len(self.checked_admissions) and len(self.committed_bound_effects) != 2):
                _fail()
            if self.evidence_checkpoint is not None:
                if (type(self.evidence_checkpoint) is not RW0D2EvidenceCheckpointV1
                        or len(self.committed_bound_effects) != 2
                        or len(self.checked_admissions) != 14
                        or len(self.child_outcomes) < 2):
                    _fail()
                self.evidence_checkpoint.validate()
                if (self.evidence_checkpoint.d1_handback is not self.d1_handback
                        or self.evidence_checkpoint.bound_effects != self.committed_bound_effects
                        or self.evidence_checkpoint.admitted_families != self.checked_admissions
                        or self.child_outcomes[0] is not self.evidence_checkpoint.validator_process
                        or self.child_outcomes[1] is not self.evidence_checkpoint.reviewer_process):
                    _fail()
            elif len(self.child_outcomes) > 2:
                _fail()
            types = (
                (self.input_context, PostExecutionSemanticReviewInputContextV1),
                (self.evidence_supply, PostExecutionEvidenceSupplyV2),
                (self.model_input_binding, PostExecutionModelInputBindingV2),
                (self.model_source_invocation, ModelSourceInvocationV1),
                (self.private_artifact, PostExecutionSemanticReviewArtifactV1),
                (self.artifact_binding, PrivateProposalArtifactBindingV1),
                (self.safe_projection, PostExecutionSemanticReviewSafeProjectionV1),
                (self.evidence_set, ModelProposalEvidenceSetV1),
                (self.proposal, PreExecutionModelProposalV1),
                (self.model_process, D1ProcessOutcome),
            )
            if any(value is not None and type(value) is not expected
                   for value, expected in types):
                _fail()
            if any(type(item) is not ModelProposalEvidenceBindingV1
                   for item in self.evidence_bindings):
                _fail()
            if self.model_process is not None and (
                len(self.child_outcomes) != 3
                or self.model_process is not self.child_outcomes[2]
            ):
                _fail()
            if self.evidence_checkpoint is None and any(
                getattr(self, name) is not None
                for name in _B_ORDER if name not in ("evidence_bindings", "model_process")
            ):
                _fail()
            if (self.d1_handback.status != "capsule_ready"
                    and (self.committed_bound_effects or self.checked_admissions
                         or self.child_outcomes or self.evidence_checkpoint is not None)):
                _fail()
            if (self.evidence_supply is not None and self.input_context is None
                    or self.input_context is not None and self.evidence_checkpoint is None
                    or self.model_process is not None and self.evidence_supply is None
                    or len(self.child_outcomes) >= 1 and len(self.checked_admissions) < 10
                    or len(self.child_outcomes) >= 2 and len(self.checked_admissions) < 12):
                _fail()
            if self.input_context is not None:
                self.input_context._validate_value()
            if self.evidence_supply is not None:
                self.evidence_supply._validate_value()
                if self.evidence_supply.input_context != self.input_context:
                    _fail()
            if (self.status != "preadmission_ready" and (
                    any(getattr(self, name) is not None for name in _NORMALIZED_NAMES)
                    or self.evidence_bindings)):
                _fail()
            if (self.status == "stopped" and any(
                    not item.cleanup_complete for item in self.child_outcomes
            )):
                _fail()
            if (self.status == "cleanup_unresolved"
                    and not self.reason.endswith("cleanup_unresolved")):
                _fail()
            _validate_reason_reached_facts(self)
            _validate_a_to_b_input_binding(self)
            if self.status == "preadmission_ready":
                if (self.reason != "complete"
                        or self.d1_handback.status != "capsule_ready"
                        or not self.d1_handback.workspace_cleaned
                        or self.evidence_checkpoint is None
                        or len(self.child_outcomes) != 3
                        or any(not item.clean_success or not item.cleanup_complete
                               for item in self.child_outcomes)
                        or any(getattr(self, name) is None for name in _B_ORDER
                               if name != "evidence_bindings")):
                    _fail()
                self.input_context._validate_value()
                self.evidence_supply._validate_value()
                self.model_input_binding._validate_value()
                _validate_semantic_value(self.model_source_invocation)
                self.private_artifact.validate()
                _validate_semantic_value(self.artifact_binding)
                self.safe_projection.validate()
                for binding in self.evidence_bindings:
                    _validate_semantic_value(binding)
                _validate_semantic_value(self.evidence_set)
                _validate_semantic_value(self.proposal)
                if (self.evidence_supply.input_context != self.input_context
                        or self.model_source_invocation.source_invocation_ref
                        != self.model_input_binding.source_invocation_ref
                        or self.private_artifact.artifact_digest
                        != self.model_source_invocation.artifact_digest
                        or self.proposal.proposal_digest
                        != self.model_input_binding.proposal_digest
                        or self.proposal.evidence_set_digest
                        != self.evidence_set.evidence_set_digest
                        or self.evidence_set.entries != self.evidence_bindings):
                    _fail()
            elif self.reason == "complete":
                _fail()
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception:
            _fail()

    def __reduce__(self) -> object:
        raise TypeError("serialization disabled")


class RW0D2OfflineRun:
    __slots__ = ("_d1_run", "_handback", "_creator_pid", "_closed")

    def __init__(self, d1_run: RW0D1OfflineRun,
                 handback: RW0D2PreadmissionHandbackV1) -> None:
        if type(d1_run) is not RW0D1OfflineRun or type(handback) is not RW0D2PreadmissionHandbackV1:
            raise TypeError("invalid_d2_run")
        handback.validate()
        if d1_run.handback is not handback.d1_handback:
            raise ValueError("invalid_d2_run")
        self._d1_run = d1_run
        self._handback = handback
        self._creator_pid = os.getpid()
        self._closed = False

    def _require_open_owner(self) -> None:
        if os.getpid() != self._creator_pid:
            raise RuntimeError("d2_run_wrong_process")
        if self._closed or self._d1_run.closed:
            raise RuntimeError("d2_run_closed")

    @property
    def handback(self) -> RW0D2PreadmissionHandbackV1:
        self._require_open_owner()
        return self._handback

    @property
    def closed(self) -> bool:
        if os.getpid() != self._creator_pid:
            raise RuntimeError("d2_run_wrong_process")
        return self._closed

    def close(self) -> None:
        if os.getpid() != self._creator_pid:
            raise RuntimeError("d2_run_wrong_process")
        if self._closed:
            return
        self._d1_run.close()
        self._closed = True

    def __enter__(self) -> RW0D2OfflineRun:
        self._require_open_owner()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return "RW0D2OfflineRun"

    __str__ = __repr__

    def __reduce__(self) -> object:
        raise TypeError("serialization disabled")
