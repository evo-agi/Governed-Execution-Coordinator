"""Pure/static RW0-C1 identities, dependency grammar, and SQLite write plans.

This module performs no I/O.  It does not decide evidence completeness,
permission, acceptance, terminality, source authenticity, or runtime truth.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import typing

from ._rw0_c1_row_values import (
    ROW_SPECS,
    RW0C1RowValue,
    build_row_mapping,
    rw0_c1_row_value_from_mapping,
)
from ._rw0_c1_semantic_values import (
    RW0C1AdmitEvidenceCommandV1,
    RW0C1AdmissionSnapshotBindingV1,
    RW0C1EstablishPhaseCommandV1,
    RW0C1MemberLocatorV1,
    RW0C1PreflightError,
    RW0C1RecoveryDispositionV1,
    RW0C1RecoveryResultV1,
    RW0C1Section41PostExecutionProposalFamilyMemberV1,
    RW0C1TransientPrivateBindingV1,
    RW0C1WireProcessResultClassificationBindingV1,
    RW0C1WireWorkerResultBindingV1,
    evidence_identity,
    relation_evaluation_time,
)


__all__: tuple[str, ...] = ()


_MAX_INT = 9_223_372_036_854_775_807
_SAFE_REF_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]*\Z")
_RESERVED_SAFE_REF_PREFIXES = (
    "connector-",
    "tunnel-",
    "workspace-",
    "org-",
    "organization-",
    "user-",
)
_NWPF_PROFILE = (
    "rw0-wire-nwpf-v1",
    "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454",
)
_CANCELLATION_PROFILE = (
    "rw0-wire-cancellation-control-v1",
    "4d6f84552b852a4c4073b4238591afd271072f648424eca9e744def436165288",
)


class _RW0C1CommitCloseWitness:
    """One-operation in-memory witness for the complete C1 commit close."""

    __slots__ = ("_commit_attempted", "_controller_claimed", "_state")

    def __init__(self) -> None:
        self._commit_attempted = False
        self._controller_claimed = False
        self._state = "precommit"

    @property
    def state(self) -> str:
        return self._state

    @property
    def ordinary_failure_is_commit_uncertain(self) -> bool:
        return self._commit_attempted

    def _claim_controller(self) -> None:
        if self._controller_claimed or self._state != "precommit":
            raise ValueError("invalid C1 commit-close witness")
        self._controller_claimed = True

    def _mark_commit_attempt_started(self) -> None:
        if not self._controller_claimed or self._state != "precommit":
            raise ValueError("invalid C1 commit-close transition")
        self._commit_attempted = True
        self._state = "commit_attempt_started"

    def _mark_commit_returned_success(self) -> None:
        if self._state != "commit_attempt_started":
            raise ValueError("invalid C1 commit-close transition")
        self._state = "commit_returned_success"

    def _mark_close_proof_complete(self) -> None:
        if self._state not in {"precommit", "commit_returned_success"}:
            raise ValueError("invalid C1 commit-close transition")
        self._state = "close_proof_complete"

    def __repr__(self) -> str:
        return "<_RW0C1CommitCloseWitness>"


class _RW0C1RecoveryCloseWitness:
    """One-operation in-memory witness for recovery-result close proof."""

    __slots__ = ("_controller_claimed", "_result", "_state")

    def __init__(self) -> None:
        self._controller_claimed = False
        self._result: RW0C1RecoveryResultV1 | None = None
        self._state = "pre_result"

    @property
    def result_computed(self) -> bool:
        return self._state in {"result_computed", "close_proof_complete"}

    def _claim_controller(self) -> None:
        if self._controller_claimed or self._state != "pre_result":
            raise ValueError("invalid C1 recovery-close witness")
        self._controller_claimed = True

    def _mark_result_computed(self, result: RW0C1RecoveryResultV1) -> None:
        if (
            not self._controller_claimed
            or self._state != "pre_result"
            or type(result) is not RW0C1RecoveryResultV1
        ):
            raise ValueError("invalid C1 recovery-close transition")
        self._result = result
        self._state = "result_computed"

    def _unresolved_result(self) -> RW0C1RecoveryResultV1:
        result = self._result
        if not self.result_computed or type(result) is not RW0C1RecoveryResultV1:
            raise ValueError("invalid C1 recovery-close transition")
        return RW0C1RecoveryResultV1(
            result.mutation_family,
            result.mutation_ref,
            result.command_digest,
            RW0C1RecoveryDispositionV1.UNRESOLVED,
        )

    def _mark_close_proof_complete(self) -> None:
        if self._state != "result_computed":
            raise ValueError("invalid C1 recovery-close transition")
        self._state = "close_proof_complete"

    def __repr__(self) -> str:
        return "<_RW0C1RecoveryCloseWitness>"

_OWNER_SCHEMA_BY_ROLE = {
    "development_work_spec_binding": (
        "governed-execution.nwp-development-work-spec-binding.v1"
    ),
    "development_attempt_fence": "governed-execution.nwp-attempt-fence.v1",
    "development_effect_fence": "governed-execution.nwp-effect-fence.v1",
    "development_author_command": "governed-execution.nwp-worker-command.v1",
    "development_delivery_attempt": (
        "governed-execution.nwp-development-delivery-attempt.v1"
    ),
    "development_model_source_invocation": (
        "governed-execution.nwp-model-source-invocation.v1"
    ),
    "development_pre_execution_planning_context": (
        "governed-execution.nwp-pre-execution-planning-context.v1"
    ),
    "development_private_proposal_artifact_binding": (
        "governed-execution.nwp-private-proposal-artifact-binding.v1"
    ),
    "development_model_proposal": (
        "governed-execution.nwp-model-proposal-envelope.v1"
    ),
    "development_pre_execution_plan_projection": (
        "governed-execution.nwp-pre-execution-plan-safe-projection.v1"
    ),
    "development_model_proposal_evidence_binding": (
        "governed-execution.nwp-model-proposal-evidence-binding.v1"
    ),
    "development_pre_execution_disposition": (
        "governed-execution.nwp-pre-execution-coordinator-disposition.v1"
    ),
    "development_cognitive_mutation_receipt": (
        "governed-execution.nwp-cognitive-mutation-receipt.v1"
    ),
}

_TRANSIENT_SCHEMA_BY_KIND = {
    "work_spec": "governed-execution.nwp-rw0-c1-transient-work-spec-binding.v1",
    "candidate_capsule_manifest": (
        "governed-execution.nwp-candidate-capsule-manifest.v1"
    ),
    "before_blob_set": (
        "governed-execution.nwp-rw0-c1-transient-before-blob-set-binding.v1"
    ),
    "after_blob_set": (
        "governed-execution.nwp-rw0-c1-transient-after-blob-set-binding.v1"
    ),
    "wire_protocol_error": (
        "governed-execution.nwp-rw0-c1-transient-wire-protocol-error-binding.v1"
    ),
}

_SNAPSHOT_SCHEMA_AND_COMPONENT_BY_KIND = {
    "selection_head_snapshot": (
        "governed-execution.nwp-rw0-c1-selection-head-admission-snapshot-binding.v1",
        "selection",
    ),
    "effect_head_snapshot": (
        "governed-execution.nwp-rw0-c1-effect-head-admission-snapshot-binding.v1",
        "effect",
    ),
    "delivery_head_snapshot": (
        "governed-execution.nwp-rw0-c1-delivery-head-admission-snapshot-binding.v1",
        "delivery",
    ),
    "global_stop_snapshot": (
        "governed-execution.nwp-rw0-c1-global-stop-admission-snapshot-binding.v1",
        "global-stop",
    ),
}

_WIRE_ERROR_REASONS = frozenset(
    {
        "invalid_outer_type", "short_header", "bad_magic", "unsupported_version",
        "unsupported_kind", "declared_length_over_cap", "truncated_payload",
        "trailing_data", "invalid_utf8", "bom_forbidden", "json_token_invalid",
        "duplicate_key", "invalid_root_or_scalar", "unknown_field", "missing_field",
        "nested_record_invalid", "noncanonical_payload", "relation_mismatch",
        "work_limit_exceeded", "invalid_field_type", "invalid_field_value",
        "invalid_length_or_cardinality", "digest_mismatch",
        "privacy_forbidden_material",
    }
)

_SECTION41_EVIDENCE_ROLES = (
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

_ROW_SCHEMAS = {
    "rw0_phase_instances": "governed-execution.nwp-rw0-c1-phase-instance-row.v1",
    "rw0_evidence_values": "governed-execution.nwp-rw0-c1-evidence-value-row.v1",
    "rw0_evidence_memberships": "governed-execution.nwp-rw0-c1-evidence-membership.v1",
    "rw0_relation_bindings": "governed-execution.nwp-rw0-c1-relation-binding.v1",
    "rw0_relation_operands": "governed-execution.nwp-rw0-c1-relation-operand.v1",
    "rw0_c1_mutation_receipts": "governed-execution.nwp-rw0-c1-mutation-receipt.v1",
    "rw0_authority_observation_effect_classes": "governed-execution.nwp-rw0-c1-authority-effect-class-row.v1",
    "rw0_c2a_worker_observation_evidence_refs": "governed-execution.nwp-rw0-c1-worker-observation-evidence-ref-row.v1",
}

_TYPED_TABLES = (
    "rw0_authority_verification_observations",
    "rw0_subordinate_authorization_proposals",
    "rw0_custody_availability_observations",
    "rw0_retrieval_capability_event_observations",
    "rw0_remote_host_readiness_observations",
    "rw0_effect_host_qualifications",
    "rw0_worker_mechanism_capability_declarations",
    "rw0_worker_mechanism_capability_observations",
    "rw0_worker_mechanism_capability_qualifications",
    "rw0_wire_cancellation_request_observations",
    "rw0_wire_process_observations",
    "rw0_c2a_worker_observations",
    "rw0_wire_worker_result_bindings",
    "rw0_wire_process_result_classification_bindings",
    "rw0_section41_post_execution_proposal_family_members",
)
for _typed_rank, _typed_table in enumerate(_TYPED_TABLES, 1):
    _ROW_SCHEMAS[_typed_table] = (
        "governed-execution.nwp-rw0-c1-"
        + _typed_table.removeprefix("rw0_").replace("_", "-")
        + "-payload-row.v1"
    )
del _typed_rank, _typed_table


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeError):
        raise RW0C1PreflightError("invalid_value") from None


def _digest(domain: str, value: object) -> str:
    if type(domain) is not str or not domain:
        raise RW0C1PreflightError("invalid_value") from None
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + _canonical_bytes(value)).hexdigest()


def _require_digest(value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise RW0C1PreflightError("invalid_value") from None
    return value


def _require_safe_ref(value: object) -> str:
    if (
        type(value) is not str
        or not 1 <= len(value) <= 96
        or _SAFE_REF_PATTERN.fullmatch(value) is None
        or value.lower().startswith(_RESERVED_SAFE_REF_PREFIXES)
    ):
        raise RW0C1PreflightError("invalid_value") from None
    return value


def _require_role(value: object) -> str:
    if (
        type(value) is not str
        or re.fullmatch(r"[a-z][a-z0-9_.:-]{0,95}", value) is None
    ):
        raise RW0C1PreflightError("invalid_value") from None
    return value


_PROOF_MODES = frozenset(
    {
        "relation_recomputable",
        "relation_attested_at_admission",
        "derived_wrapper_recomputable",
        "existing_owner_row_reconstructed",
    }
)


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1RelationSpecification:
    kind_rank: int
    relation_rank: int
    relation_schema_id: str
    proof_mode: str
    profile_ref: str | None = None
    profile_digest: str | None = None

    def __post_init__(self) -> None:
        if (
            type(self.kind_rank) is not int
            or not 0 <= self.kind_rank <= 15
            or type(self.relation_rank) is not int
            or self.relation_rank not in {0, 1}
            or type(self.relation_schema_id) is not str
            or not self.relation_schema_id.startswith("governed-execution.nwp-rw0-c1-")
            or self.proof_mode not in _PROOF_MODES
        ):
            raise RW0C1PreflightError("invalid_value") from None
        pair = (self.profile_ref, self.profile_digest)
        if pair not in {(None, None), _NWPF_PROFILE, _CANCELLATION_PROFILE}:
            raise RW0C1PreflightError("invalid_value") from None

    def __repr__(self) -> str:
        return "<RW0C1RelationSpecification>"


_RELATION_SPECS: dict[int, tuple[RW0C1RelationSpecification, ...]] = {
    1: (RW0C1RelationSpecification(1, 0, "governed-execution.nwp-rw0-c1-authority-verification-observation-relation.v1", "relation_recomputable"),),
    2: (RW0C1RelationSpecification(2, 0, "governed-execution.nwp-rw0-c1-subordinate-narrowing-relation.v1", "relation_recomputable"),),
    3: (RW0C1RelationSpecification(3, 0, "governed-execution.nwp-rw0-c1-custody-binding-relation.v1", "existing_owner_row_reconstructed"),),
    4: (RW0C1RelationSpecification(4, 0, "governed-execution.nwp-rw0-c1-retrieval-event-sequence-relation.v1", "relation_recomputable"),),
    5: (),
    6: (RW0C1RelationSpecification(6, 0, "governed-execution.nwp-rw0-c1-host-qualification-relation.v1", "derived_wrapper_recomputable"),),
    7: (),
    8: (RW0C1RelationSpecification(8, 0, "governed-execution.nwp-rw0-c1-capability-observation-declaration-binding-relation.v1", "relation_recomputable", *_NWPF_PROFILE),),
    9: (RW0C1RelationSpecification(9, 0, "governed-execution.nwp-rw0-c1-worker-mechanism-capability-qualification-relation.v1", "derived_wrapper_recomputable", *_NWPF_PROFILE),),
    10: (RW0C1RelationSpecification(10, 0, "governed-execution.nwp-rw0-c1-wire-exact-current-cancellation-request-relation.v1", "relation_attested_at_admission", *_CANCELLATION_PROFILE),),
    11: (RW0C1RelationSpecification(11, 0, "governed-execution.nwp-rw0-c1-wire-exact-current-process-observation-relation.v1", "relation_attested_at_admission", *_CANCELLATION_PROFILE),),
    12: (RW0C1RelationSpecification(12, 0, "governed-execution.nwp-rw0-c1-c2a-worker-observation-relation.v1", "relation_recomputable"),),
    13: (RW0C1RelationSpecification(13, 0, "governed-execution.nwp-rw0-c1-wire-worker-result-relation.v1", "derived_wrapper_recomputable", *_NWPF_PROFILE),),
    14: (RW0C1RelationSpecification(14, 0, "governed-execution.nwp-rw0-c1-wire-process-result-classifier-relation.v1", "derived_wrapper_recomputable", *_NWPF_PROFILE),),
    15: (RW0C1RelationSpecification(15, 0, "governed-execution.nwp-rw0-c1-section41-post-execution-proposal-family-relation.v1", "existing_owner_row_reconstructed"),),
}

_CANCELLATION_RESPONSE_SPEC = RW0C1RelationSpecification(
    12,
    1,
    "governed-execution.nwp-rw0-c1-wire-exact-current-cancellation-response-relation.v1",
    "relation_attested_at_admission",
    *_CANCELLATION_PROFILE,
)

_REQUIRED_DEPENDENCIES: dict[int, frozenset[int]] = {
    1: frozenset(),
    2: frozenset({1}),
    3: frozenset(),
    4: frozenset({1, 2, 3}),
    5: frozenset(),
    6: frozenset({1, 5}),
    7: frozenset(),
    8: frozenset({7}),
    9: frozenset({1, 5, 6, 7, 8}),
    10: frozenset(),
    11: frozenset(),
    12: frozenset(),
    13: frozenset({12}),
    14: frozenset(),
    15: frozenset(),
}


def relation_specifications(
    *, kind_rank: int, cancellation_response: bool = False,
    transient_binding_kinds: tuple[str, ...] = (),
    rank14_result_state: str | None = None,
) -> tuple[RW0C1RelationSpecification, ...]:
    if type(kind_rank) is not int or kind_rank not in _RELATION_SPECS:
        raise RW0C1PreflightError("invalid_value") from None
    if type(cancellation_response) is not bool or type(transient_binding_kinds) is not tuple:
        raise RW0C1PreflightError("invalid_value") from None
    specs = list(_RELATION_SPECS[kind_rank])
    if kind_rank == 12 and cancellation_response:
        specs.append(_CANCELLATION_RESPONSE_SPEC)
    elif cancellation_response:
        raise RW0C1PreflightError("invalid_value") from None
    if kind_rank == 1 and "candidate_capsule_manifest" in transient_binding_kinds:
        specs[0] = _replace_proof(specs[0], "relation_attested_at_admission")
    if kind_rank == 3 and "work_spec" in transient_binding_kinds:
        specs[0] = _replace_proof(specs[0], "relation_attested_at_admission")
    if kind_rank == 12 and transient_binding_kinds:
        specs[0] = _replace_proof(specs[0], "relation_attested_at_admission")
    if kind_rank == 14:
        if rank14_result_state not in {"present", "finite_failure", "absent"}:
            raise RW0C1PreflightError("invalid_value") from None
        if rank14_result_state == "finite_failure":
            specs[0] = _replace_proof(specs[0], "relation_attested_at_admission")
    return tuple(specs)


def _replace_proof(
    spec: RW0C1RelationSpecification, proof_mode: str,
) -> RW0C1RelationSpecification:
    return RW0C1RelationSpecification(
        spec.kind_rank,
        spec.relation_rank,
        spec.relation_schema_id,
        proof_mode,
        spec.profile_ref,
        spec.profile_digest,
    )


def validate_dependency_locators(
    *, kind_rank: int, evidence_value: object,
    locators: tuple[RW0C1MemberLocatorV1, ...],
) -> None:
    if type(kind_rank) is not int or kind_rank not in _REQUIRED_DEPENDENCIES:
        raise RW0C1PreflightError("invalid_command") from None
    if type(locators) is not tuple or any(type(item) is not RW0C1MemberLocatorV1 for item in locators):
        raise RW0C1PreflightError("invalid_command") from None
    expected: tuple[tuple[str, int], ...]
    if kind_rank == 2:
        expected = (("authority_observation", 1),)
    elif kind_rank == 4:
        if len(locators) not in {3, 4, 5}:
            raise RW0C1PreflightError("invalid_command") from None
        prefix_count = len(locators) - 3
        expected = (
            ("authority_observation", 1),
            ("subordinate_proposal", 2),
            ("custody_observation", 3),
            *tuple((f"retrieval_event:{ordinal:03d}", 4) for ordinal in range(prefix_count)),
        )
    elif kind_rank == 6:
        expected = (
            ("authority_observation", 1),
            ("remote_host_readiness", 5),
        )
    elif kind_rank == 8:
        expected = (("capability_declaration", 7),)
    elif kind_rank == 9:
        expected = (
            ("authority_observation", 1),
            ("remote_host_readiness", 5),
            ("host_qualification", 6),
            ("capability_declaration", 7),
            ("capability_observation", 8),
        )
    elif kind_rank == 12:
        try:
            response = evidence_value.observation_kind in {
                "cancellation_acknowledged",
                "cancellation_rejected",
            }
        except Exception:
            raise RW0C1PreflightError("invalid_command") from None
        expected = (("cancellation_request", 10),) if response else ()
    elif kind_rank == 13:
        value = typing.cast(RW0C1WireWorkerResultBindingV1, evidence_value)
        if type(value) is not RW0C1WireWorkerResultBindingV1:
            raise RW0C1PreflightError("invalid_command") from None
        expected = tuple(
            (f"worker_observation:{ordinal:03d}", 12)
            for ordinal in range(len(value.observation_memberships))
        )
        if tuple(item.to_mapping() for item in locators) != tuple(
            {
                **item.to_mapping(),
                "role": f"worker_observation:{ordinal:03d}",
            }
            for ordinal, item in enumerate(value.observation_memberships)
        ):
            raise RW0C1PreflightError("invalid_command") from None
    elif kind_rank == 14:
        value = typing.cast(
            RW0C1WireProcessResultClassificationBindingV1,
            evidence_value,
        )
        if type(value) is not RW0C1WireProcessResultClassificationBindingV1:
            raise RW0C1PreflightError("invalid_command") from None
        wrapped: list[tuple[str, RW0C1MemberLocatorV1]] = []
        if value.result_membership is not None:
            wrapped.append(("worker_result_binding", value.result_membership))
        wrapped.extend(
            (f"adapter_observation:{ordinal:03d}", item)
            for ordinal, item in enumerate(value.adapter_observations)
        )
        if value.request_membership is not None:
            wrapped.append(("cancellation_request", value.request_membership))
        wrapped.extend(
            (f"process_observation:{ordinal:03d}", item)
            for ordinal, item in enumerate(value.process_observations)
        )
        expected = tuple((role, item.kind_rank) for role, item in wrapped)
        if tuple(item.to_mapping() for item in locators) != tuple(
            {**item.to_mapping(), "role": role} for role, item in wrapped
        ):
            raise RW0C1PreflightError("invalid_command") from None
    else:
        expected = ()
    if tuple((item.role, item.kind_rank) for item in locators) != expected:
        raise RW0C1PreflightError("invalid_command") from None


_OWNER_OPERAND_GRAMMAR: dict[int, tuple[tuple[str, str], ...]] = {
    1: (
        ("attempt_fence", "development_attempt_fence"),
        ("author_effect_fence", "development_effect_fence"),
        ("current_effect_fence", "development_effect_fence"),
        ("author_command", "development_author_command"),
    ),
    2: (
        ("attempt_fence", "development_attempt_fence"),
        ("current_effect_fence", "development_effect_fence"),
    ),
    4: (
        ("attempt_fence", "development_attempt_fence"),
        ("current_effect_fence", "development_effect_fence"),
    ),
    6: (("current_effect_fence", "development_effect_fence"),),
    9: (("current_effect_fence", "development_effect_fence"),),
    10: (
        ("author_command", "development_author_command"),
        ("attempt_fence", "development_attempt_fence"),
        ("author_effect_fence", "development_effect_fence"),
        ("target_effect_fence", "development_effect_fence"),
        ("target_delivery", "development_delivery_attempt"),
        ("cancellation_effect_fence", "development_effect_fence"),
        ("cancellation_delivery", "development_delivery_attempt"),
    ),
    11: (
        ("author_command", "development_author_command"),
        ("attempt_fence", "development_attempt_fence"),
        ("author_effect_fence", "development_effect_fence"),
        ("target_effect_fence", "development_effect_fence"),
        ("target_delivery", "development_delivery_attempt"),
    ),
    12: (
        ("target_delivery", "development_delivery_attempt"),
        ("author_command", "development_author_command"),
        ("attempt_fence", "development_attempt_fence"),
        ("author_effect_fence", "development_effect_fence"),
        ("target_effect_fence", "development_effect_fence"),
    ),
    13: (
        ("author_command", "development_author_command"),
        ("author_delivery", "development_delivery_attempt"),
        ("attempt_fence", "development_attempt_fence"),
        ("author_effect_fence", "development_effect_fence"),
    ),
    14: (
        ("author_command", "development_author_command"),
        ("author_delivery", "development_delivery_attempt"),
        ("attempt_fence", "development_attempt_fence"),
        ("author_effect_fence", "development_effect_fence"),
    ),
    15: (
        ("source_invocation", "development_model_source_invocation"),
        ("artifact_binding", "development_private_proposal_artifact_binding"),
        ("model_proposal", "development_model_proposal"),
    ),
}


def validate_admission_operand_grammar(
    command: RW0C1AdmitEvidenceCommandV1,
) -> None:
    """Require the exact closed member/owner/transient operand grammar."""

    if type(command) is not RW0C1AdmitEvidenceCommandV1:
        raise RW0C1PreflightError("invalid_command") from None
    validate_dependency_locators(
        kind_rank=command.kind_rank,
        evidence_value=command.evidence_value,
        locators=command.prerequisite_member_locators,
    )
    owners = list(_OWNER_OPERAND_GRAMMAR.get(command.kind_rank, ()))
    transients: list[tuple[str, str]] = []
    if command.kind_rank == 1:
        if any(item.role == "cancellation_target_effect_fence" for item in command.owner_row_locators):
            owners.append(
                ("cancellation_target_effect_fence", "development_effect_fence")
            )
        if command.transient_bindings:
            transients.append(("target_capsule_manifest", "candidate_capsule_manifest"))
    elif command.kind_rank == 3:
        if command.owner_row_locators:
            owners = [
                ("custody_subject", "development_private_proposal_artifact_binding")
            ]
        else:
            transients = [("custody_subject", "work_spec")]
    elif command.kind_rank in {10, 11} and command.transient_bindings:
        transients = [("target_capsule_manifest", "candidate_capsule_manifest")]
    elif command.kind_rank == 12:
        try:
            response = command.evidence_value.observation_kind in {
                "cancellation_acknowledged",
                "cancellation_rejected",
            }
        except Exception:
            raise RW0C1PreflightError("invalid_command") from None
        if response:
            owners.extend(
                (
                    ("cancellation_effect_fence", "development_effect_fence"),
                    ("cancellation_delivery", "development_delivery_attempt"),
                )
            )
        allowed = {
            "target_capsule_manifest": "candidate_capsule_manifest",
            "before_blob_set": "before_blob_set",
            "after_blob_set": "after_blob_set",
        }
        transients = [
            (role, allowed[role])
            for role in (
                "target_capsule_manifest",
                "before_blob_set",
                "after_blob_set",
            )
            if any(item.role == role for item in command.transient_bindings)
        ]
    elif command.kind_rank == 14:
        value = typing.cast(
            RW0C1WireProcessResultClassificationBindingV1,
            command.evidence_value,
        )
        cancellation_fields = any(
            item.role in {
                "cancellation_effect_fence",
                "cancellation_delivery",
            }
            for item in command.owner_row_locators
        )
        if cancellation_fields:
            owners.extend(
                (
                    ("cancellation_effect_fence", "development_effect_fence"),
                    ("cancellation_delivery", "development_delivery_attempt"),
                )
            )
        if value.result_state == "finite_failure":
            transients = [("worker_result_failure", "wire_protocol_error")]
    elif command.kind_rank == 15:
        value = typing.cast(
            RW0C1Section41PostExecutionProposalFamilyMemberV1,
            command.evidence_value,
        )
        if type(value) is not RW0C1Section41PostExecutionProposalFamilyMemberV1:
            raise RW0C1PreflightError("invalid_command") from None
        if value.evidence_binding_count == 9:
            owners.extend(
                (role, "development_model_proposal_evidence_binding")
                for role in _SECTION41_EVIDENCE_ROLES
            )
    observed_owners = tuple(
        (item.role, item.owner_role) for item in command.owner_row_locators
    )
    observed_transients = tuple(
        (item.role, item.binding_kind) for item in command.transient_bindings
    )
    if observed_owners != tuple(owners) or observed_transients != tuple(transients):
        raise RW0C1PreflightError("invalid_command") from None
    if command.kind_rank == 15:
        for item in command.owner_row_locators[3:]:
            if item.subrole != item.role or item.ordinal != 0:
                raise RW0C1PreflightError("invalid_command") from None
        value = typing.cast(
            RW0C1Section41PostExecutionProposalFamilyMemberV1,
            command.evidence_value,
        )
        if value.owner_family_graph_digest != section41_owner_family_graph_digest(
            command.owner_row_locators
        ):
            raise RW0C1PreflightError("invalid_command") from None
    roles = (
        *(item.role for item in command.prerequisite_member_locators),
        *(item.role for item in command.owner_row_locators),
        *(item.role for item in command.transient_bindings),
    )
    if len(roles) != len(set(roles)) or len(roles) > 14:
        raise RW0C1PreflightError("invalid_command") from None


def k8_mapping_from_phase_basis(phase_basis: object) -> dict[str, object]:
    try:
        selection_key = phase_basis.selection_key
    except Exception:
        raise RW0C1PreflightError("invalid_value") from None
    if type(selection_key) is not tuple or len(selection_key) != 8:
        raise RW0C1PreflightError("invalid_value") from None
    expected = (
        "program_ref", "semantic_attempt_ref", "candidate_ref", "effect_intent_ref",
        "author_command_ref", "attempt_fence_ref", "effect_fence_ref",
        "delivery_attempt_ref",
    )
    if tuple(item[0] for item in selection_key if type(item) is tuple and len(item) == 2) != expected:
        raise RW0C1PreflightError("invalid_value") from None
    return {name: value for name, value in selection_key}


def k8_digest_from_phase_basis(phase_basis: object) -> str:
    return _digest(
        "governed-execution.nwp-rw0-c1-k8.v1.identity",
        {"schema_id": "governed-execution.nwp-rw0-c1-k8.v1", **k8_mapping_from_phase_basis(phase_basis)},
    )


def global_scope_binding_digest(kind_rank: int, value_schema_id: str) -> str:
    if kind_rank not in {5, 7, 8} or type(value_schema_id) is not str:
        raise RW0C1PreflightError("invalid_value") from None
    return _digest(
        "governed-execution.nwp-rw0-c1-global-evidence-scope.v1.identity",
        {"kind_rank": kind_rank, "value_schema_id": value_schema_id},
    )


def relation_reference(
    *, phase_basis_ref: str, subject_type: str,
    subject_membership_ref: str | None, relation_rank: int,
    phase_basis_digest: str,
) -> str:
    if subject_type == "phase_establishment":
        if subject_membership_ref is not None or relation_rank != 0:
            raise RW0C1PreflightError("invalid_value") from None
        return "rw0-c1-phase-relation." + _require_digest(phase_basis_digest)
    if subject_type != "evidence_membership" or type(subject_membership_ref) is not str:
        raise RW0C1PreflightError("invalid_value") from None
    digest = _digest(
        "governed-execution.nwp-rw0-c1-relation-reference.v1.identity",
        {
            "phase_basis_ref": phase_basis_ref,
            "subject_type": subject_type,
            "subject_membership_ref": subject_membership_ref,
            "relation_rank": relation_rank,
        },
    )
    return "rw0-c1-relation." + digest


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1OperandIdentity:
    operand_ordinal: int
    operand_role: str
    operand_source: str
    source_membership_ref: str | None
    source_membership_digest: str | None
    source_kind_rank: int | None
    owner_role: str | None
    owner_locator_ref: str | None
    owner_locator_revision: int | None
    owner_locator_subrole: str | None
    owner_locator_ordinal: int | None
    transient_binding_kind: str | None
    transient_error_reason: str | None
    snapshot_binding_kind: str | None
    operand_schema_id: str
    operand_ref: str
    operand_digest: str
    operand_scope_digest: str | None

    def __post_init__(self) -> None:
        if type(self.operand_ordinal) is not int or not 0 <= self.operand_ordinal <= 13:
            raise RW0C1PreflightError("invalid_value") from None
        _require_role(self.operand_role)
        if self.operand_source not in {
            "c1_evidence", "existing_owner_row", "transient_private_binding",
            "admission_snapshot_binding",
        }:
            raise RW0C1PreflightError("invalid_value") from None
        _require_safe_ref(self.operand_ref)
        _require_digest(self.operand_digest)
        if self.operand_scope_digest is not None:
            _require_digest(self.operand_scope_digest)
        membership_fields = (
            self.source_membership_ref,
            self.source_membership_digest,
            self.source_kind_rank,
        )
        owner_fields = (
            self.owner_role,
            self.owner_locator_ref,
            self.owner_locator_revision,
            self.owner_locator_subrole,
            self.owner_locator_ordinal,
        )
        transient_fields = (
            self.transient_binding_kind,
            self.transient_error_reason,
        )
        if self.operand_source == "c1_evidence":
            if (
                self.source_membership_ref is None
                or self.source_membership_digest is None
                or type(self.source_kind_rank) is not int
                or not 1 <= self.source_kind_rank <= 15
                or any(item is not None for item in owner_fields)
                or any(item is not None for item in transient_fields)
                or self.snapshot_binding_kind is not None
                or self.operand_scope_digest is None
            ):
                raise RW0C1PreflightError("invalid_value") from None
            _require_safe_ref(self.source_membership_ref)
            _require_digest(self.source_membership_digest)
        elif self.operand_source == "existing_owner_row":
            if (
                any(item is not None for item in membership_fields)
                or self.owner_role not in _OWNER_SCHEMA_BY_ROLE
                or self.owner_locator_ref is None
                or any(item is not None for item in transient_fields)
                or self.snapshot_binding_kind is not None
                or self.operand_scope_digest is not None
                or self.operand_schema_id != _OWNER_SCHEMA_BY_ROLE[self.owner_role]
            ):
                raise RW0C1PreflightError("invalid_value") from None
            _require_safe_ref(self.owner_locator_ref)
            if self.owner_role == "development_model_proposal_evidence_binding":
                if (
                    self.owner_locator_revision is not None
                    or self.owner_locator_subrole not in _SECTION41_EVIDENCE_ROLES
                    and self.owner_locator_subrole
                    not in {
                        "repository_binding",
                        "base_binding",
                        "authorized_path_scope",
                        "cost_ceiling",
                        "token_ceiling",
                        "time_ceiling",
                        "delivery_ceiling",
                        "validation_requirement",
                        "review_requirement",
                        "qualified_remote_host_readiness",
                    }
                    or self.owner_locator_ordinal != 0
                ):
                    raise RW0C1PreflightError("invalid_value") from None
            elif any(
                item is not None
                for item in (
                    self.owner_locator_revision,
                    self.owner_locator_subrole,
                    self.owner_locator_ordinal,
                )
            ):
                raise RW0C1PreflightError("invalid_value") from None
        elif self.operand_source == "transient_private_binding":
            if (
                any(item is not None for item in membership_fields)
                or any(item is not None for item in owner_fields)
                or self.transient_binding_kind not in _TRANSIENT_SCHEMA_BY_KIND
                or self.snapshot_binding_kind is not None
                or self.operand_scope_digest is None
                or self.operand_schema_id
                != _TRANSIENT_SCHEMA_BY_KIND[self.transient_binding_kind]
            ):
                raise RW0C1PreflightError("invalid_value") from None
            if self.transient_binding_kind == "wire_protocol_error":
                if self.transient_error_reason not in _WIRE_ERROR_REASONS:
                    raise RW0C1PreflightError("invalid_value") from None
            elif self.transient_error_reason is not None:
                raise RW0C1PreflightError("invalid_value") from None
        else:
            if (
                any(item is not None for item in membership_fields)
                or any(item is not None for item in owner_fields)
                or any(item is not None for item in transient_fields)
                or self.snapshot_binding_kind
                not in _SNAPSHOT_SCHEMA_AND_COMPONENT_BY_KIND
                or self.operand_scope_digest is None
            ):
                raise RW0C1PreflightError("invalid_value") from None
            schema_id, component = _SNAPSHOT_SCHEMA_AND_COMPONENT_BY_KIND[
                self.snapshot_binding_kind
            ]
            if (
                self.operand_schema_id != schema_id
                or self.operand_ref
                != f"rw0-c1-snapshot.{component}.{self.operand_scope_digest}"
            ):
                raise RW0C1PreflightError("invalid_value") from None
        if type(self.operand_schema_id) is not str or not self.operand_schema_id.startswith(
            "governed-execution.nwp-"
        ):
            raise RW0C1PreflightError("invalid_value") from None

    def to_mapping(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in self.__slots__}

    def __repr__(self) -> str:
        return "<RW0C1OperandIdentity>"


def operand_set_digest(
    *, phase_basis_ref: str, relation_ref: str,
    operands: tuple[RW0C1OperandIdentity, ...],
) -> str:
    if (
        type(operands) is not tuple
        or len(operands) > 14
        or tuple(item.operand_ordinal for item in operands) != tuple(range(len(operands)))
        or len({item.operand_role for item in operands}) != len(operands)
    ):
        raise RW0C1PreflightError("invalid_value") from None
    return _digest(
        "governed-execution.nwp-rw0-c1-relation-operand-set.v1.identity",
        {
            "schema_id": "governed-execution.nwp-rw0-c1-relation-operand-set.v1",
            "phase_basis_ref": phase_basis_ref,
            "relation_ref": relation_ref,
            "operands": [item.to_mapping() for item in operands],
        },
    )


def relation_digest(
    *, phase_basis_ref: str, phase_basis_digest: str, relation_ref: str,
    subject_type: str, subject_membership_ref: str | None,
    subject_kind_rank: int | None, subject_value_ref: str | None,
    subject_value_digest: str | None, subject_value_schema_id: str | None,
    specification: RW0C1RelationSpecification, evaluated_at: str | None,
    operands: tuple[RW0C1OperandIdentity, ...],
) -> tuple[str, str]:
    operand_digest = operand_set_digest(
        phase_basis_ref=phase_basis_ref, relation_ref=relation_ref, operands=operands
    )
    identity = {
        "schema_id": "governed-execution.nwp-rw0-c1-relation.v1",
        "phase_basis_ref": phase_basis_ref,
        "phase_basis_digest": phase_basis_digest,
        "relation_ref": relation_ref,
        "subject_type": subject_type,
        "subject_membership_ref": subject_membership_ref,
        "subject_kind_rank": subject_kind_rank,
        "subject_value_ref": subject_value_ref,
        "subject_value_digest": subject_value_digest,
        "subject_value_schema_id": subject_value_schema_id,
        "relation_rank": specification.relation_rank,
        "relation_schema_id": specification.relation_schema_id,
        "relation_version": 1,
        "proof_mode": specification.proof_mode,
        "profile_ref": specification.profile_ref,
        "profile_digest": specification.profile_digest,
        "evaluated_at": evaluated_at,
        "operand_count": len(operands),
        "operand_set_digest": operand_digest,
    }
    return _digest(specification.relation_schema_id + ".identity", identity), operand_digest


def relation_set_digest(
    *, phase_basis_ref: str, subject_type: str, subject_ref: str,
    relations: tuple[tuple[int, str, str], ...],
) -> str:
    if (
        type(relations) is not tuple
        or len(relations) > 2
        or tuple(item[0] for item in relations) != tuple(range(len(relations)))
        or len({item[1] for item in relations}) != len(relations)
        or len({item[2] for item in relations}) != len(relations)
    ):
        raise RW0C1PreflightError("invalid_value") from None
    return _digest(
        "governed-execution.nwp-rw0-c1-relation-set.v1.identity",
        {
            "schema_id": "governed-execution.nwp-rw0-c1-relation-set.v1",
            "phase_basis_ref": phase_basis_ref,
            "subject_type": subject_type,
            "subject_ref": subject_ref,
            "relations": [
                {"relation_rank": rank, "relation_ref": ref, "relation_digest": digest}
                for rank, ref, digest in relations
            ],
        },
    )


def membership_digest(identity: dict[str, object]) -> str:
    expected = (
        "schema_id", "membership_ref", "phase_basis_ref", "phase_basis_digest",
        "kind_rank", "value_ref", "value_digest", "value_schema_id",
        "scope_binding_digest", "relation_set_digest", "admitted_by_mutation_ref",
        "admitted_at", "admission_graph_digest",
    )
    if type(identity) is not dict or tuple(identity) != expected:
        raise RW0C1PreflightError("invalid_value") from None
    return _digest("governed-execution.nwp-rw0-c1-evidence-membership.v1.identity", identity)


def admission_graph_digest(identity: dict[str, object]) -> str:
    return _digest("governed-execution.nwp-rw0-c1-evidence-admission-graph.v1.identity", identity)


def phase_graph_digest(identity: dict[str, object]) -> str:
    return _digest("governed-execution.nwp-rw0-c1-phase-graph.v1.identity", identity)


def section41_owner_family_graph_digest(
    locators: tuple[RW0C1OwnerRowLocatorV1, ...],
) -> str:
    """Return the exact owner-family binding digest for the rank-15 wrapper."""

    if type(locators) is not tuple or len(locators) not in {3, 12}:
        raise RW0C1PreflightError("invalid_value") from None
    expected = list(_OWNER_OPERAND_GRAMMAR[15])
    if len(locators) == 12:
        expected.extend(
            (role, "development_model_proposal_evidence_binding")
            for role in _SECTION41_EVIDENCE_ROLES
        )
    if tuple((item.role, item.owner_role) for item in locators) != tuple(expected):
        raise RW0C1PreflightError("invalid_value") from None
    return _digest(
        "governed-execution.nwp-rw0-c1-section41-owner-family-graph.v1.identity",
        {
            "schema_id": (
                "governed-execution.nwp-rw0-c1-section41-owner-family-graph.v1"
            ),
            "owners": [item.to_mapping() for item in locators],
        },
    )


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1InsertSpecification:
    table_name: str
    columns: tuple[str, ...]
    sql: str

    def __repr__(self) -> str:
        return "<RW0C1InsertSpecification>"


INSERT_SPECIFICATIONS: tuple[RW0C1InsertSpecification, ...] = tuple(
    RW0C1InsertSpecification(
        spec.table_name,
        spec.columns,
        f"INSERT INTO {spec.table_name} ({', '.join(spec.columns)}) "
        f"VALUES ({', '.join('?' for _ in spec.columns)})",
    )
    for spec in ROW_SPECS
)
INSERT_SPEC_BY_TABLE = {spec.table_name: spec for spec in INSERT_SPECIFICATIONS}


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1WritePlan:
    mutation_family: str
    rows: tuple[RW0C1RowValue, ...]
    operation_timestamp: str
    result: object

    def __post_init__(self) -> None:
        if self.mutation_family not in {"establish_rw0_phase", "admit_rw0_evidence"}:
            raise RW0C1PreflightError("invalid_value") from None
        if type(self.rows) is not tuple or not self.rows:
            raise RW0C1PreflightError("invalid_value") from None
        if self.rows[-1].table_name != "rw0_c1_mutation_receipts":
            raise RW0C1PreflightError("invalid_value") from None

    def __repr__(self) -> str:
        return "<RW0C1WritePlan>"


def row_value(table_name: str, mapping: dict[str, object]) -> RW0C1RowValue:
    return rw0_c1_row_value_from_mapping(table_name, mapping)


def build_row(table_name: str, values_without_digest: dict[str, object]) -> RW0C1RowValue:
    return rw0_c1_row_value_from_mapping(
        table_name, build_row_mapping(table_name, values_without_digest)
    )


def row_schema_id(table_name: str) -> str:
    try:
        return _ROW_SCHEMAS[table_name]
    except KeyError:
        raise RW0C1PreflightError("invalid_value") from None


def typed_payload_table(kind_rank: int) -> str:
    if type(kind_rank) is not int or not 1 <= kind_rank <= 15:
        raise RW0C1PreflightError("invalid_value") from None
    return _TYPED_TABLES[kind_rank - 1]


def normalized_owner_mapping(value: object, kind_rank: int) -> dict[str, object]:
    _ref, _value_digest, _schema, _scope, mapping = evidence_identity(value, kind_rank)
    result = dict(mapping)
    ceilings = result.pop("parent_ceilings", None)
    if ceilings is None:
        ceilings = result.pop("ceilings", None)
    if ceilings is not None:
        if type(ceilings) is not dict:
            raise RW0C1PreflightError("invalid_value") from None
        result.update(ceilings)
    effect_classes = result.pop("allowed_effect_classes", None)
    if effect_classes is not None:
        if type(effect_classes) not in {list, tuple}:
            raise RW0C1PreflightError("invalid_value") from None
        result["allowed_effect_class_count"] = len(effect_classes)
    evidence_refs = result.pop("evidence_refs", None)
    if evidence_refs is not None:
        if type(evidence_refs) is not list:
            raise RW0C1PreflightError("invalid_value") from None
        result["evidence_ref_count"] = len(evidence_refs)
    return result


def temporal_evaluation_for_command(
    *, command: RW0C1AdmitEvidenceCommandV1, relation_schema_id: str,
    operation_timestamp: str, host_qualification: object | None = None,
) -> str | None:
    if type(command) is not RW0C1AdmitEvidenceCommandV1:
        raise RW0C1PreflightError("invalid_command") from None
    return relation_evaluation_time(
        relation_schema_id=relation_schema_id,
        evidence_value=command.evidence_value,
        operation_timestamp=operation_timestamp,
        host_qualification=host_qualification,
    )


def phase_command_identity(command: RW0C1EstablishPhaseCommandV1) -> tuple[str, str, str]:
    if type(command) is not RW0C1EstablishPhaseCommandV1:
        raise RW0C1PreflightError("invalid_command") from None
    return command.phase_basis.basis_ref, command.phase_basis.basis_digest, k8_digest_from_phase_basis(command.phase_basis)
