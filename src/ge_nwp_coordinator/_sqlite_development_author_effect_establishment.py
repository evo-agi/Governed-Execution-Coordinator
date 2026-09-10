"""Private SQLite mechanics for one author-effect establishment family."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
import typing

from . import _development_decision_row_values as _decision_rows
from . import _development_effect_row_values as _effect_rows
from . import _development_program_row_values as _program_rows
from ._development_author_effect_establishment_contracts import (
    DevelopmentAuthorEffectEstablishmentCommandV1,
    DevelopmentAuthorEffectEstablishmentConflictReasonV1,
    DevelopmentAuthorEffectEstablishmentConflictV1,
    DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1,
    DevelopmentAuthorEffectEstablishmentRecoveryResultV1,
    DevelopmentAuthorEffectEstablishmentResultV1,
    DevelopmentEffectAuthorizationSafeBindingV1,
    DevelopmentReviewRequirementEvidenceV1,
    DevelopmentValidationRequirementEvidenceV1,
    _DevelopmentAuthorEffectEstablishmentWritePlan,
    _author_effect_conflict,
    _author_effect_result,
    _development_author_effect_establishment_command,
    _development_author_effect_establishment_write_plan,
    _require_exact_attempt_fence,
    _require_exact_development_author_effect_establishment_command,
    _require_exact_effect_authorization_safe_binding,
    _require_exact_review_evidence,
    _require_exact_validation_evidence,
)
from ._development_row_value_support import (
    _RowValueValidationError,
    _require_nonnegative_integer,
    _require_positive_integer,
    _require_safe_ref,
    _require_sha256,
)
from ._sqlite_development_reader_contracts import (
    DevelopmentAttemptFenceCommandEffectRead,
    DevelopmentDeliveryHeadAndCurrentAttemptRead,
    DevelopmentInitializeDecisionAndResultingVersionRead,
    DevelopmentProgramHeadAndCurrentVersionRead,
    DevelopmentProgramVersionMembershipRead,
    DevelopmentWorkItemHeadAndRevisionRead,
)
from ._sqlite_development_readers import (
    _read_development_accepted_intent_revision_by_exact_ref,
    _read_development_attempt_fence_command_effect_aggregate,
    _read_development_authority_evaluation_by_exact_ref,
    _read_development_decision_by_decision_ref,
    _read_development_delivery_head,
    _read_development_effect_head,
    _read_development_initialize_decision_and_resulting_version,
    _read_development_mutation_receipt_by_mutation_ref,
    _read_development_paged_program_version_membership,
    _read_development_program_head_and_current_version,
    _read_development_work_item_head_and_revision_by_exact_ref,
    _read_development_work_spec_safe_binding,
)
from ._worker_execution_semantic_values import (
    AttemptFenceV1,
    DeliveryEnvelopeV1,
    EffectFenceV1,
    WorkSpecV1,
    WorkerExecutionValueError,
    create_author_command_and_effect_fence,
    validate_authoring_relation,
    validate_delivery_relation,
    validate_effect_relation,
    validate_redelivery_relation,
)
from .persistence_contracts import GlobalStopCurrentRecordEnvelope
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from .sqlite_transition_read_scope import _read_global_stop_current
from .sqlite_transition_select_support import _execute_select_fetch_two


__all__: tuple[str, ...] = ()


_EFFECT_INTENT_BY_EXACT_REF_SELECT = (
    f"SELECT {', '.join(_effect_rows._DEVELOPMENT_EFFECT_INTENT_COLUMNS)} "
    "FROM development_effect_intents "
    "WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2"
)
_EFFECT_FENCE_BY_EFFECT_INTENT_REF_SELECT = (
    f"SELECT {', '.join(_effect_rows._DEVELOPMENT_EFFECT_FENCE_COLUMNS)} "
    "FROM development_effect_fences "
    "WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2"
)
_DELIVERY_ATTEMPT_BY_EXACT_REF_SELECT = (
    f"SELECT {', '.join(_effect_rows._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS)} "
    "FROM development_delivery_attempts "
    "WHERE program_ref = ? AND delivery_attempt_ref = ? LIMIT 2"
)

_SEMANTIC_ATTEMPT_INSERT = (
    f"INSERT INTO development_semantic_attempts "
    f"({', '.join(_program_rows._DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS)}) VALUES "
    f"({', '.join('?' for _ in _program_rows._DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS)})"
)
_ATTEMPT_FENCE_INSERT = (
    f"INSERT INTO development_attempt_fences "
    f"({', '.join(_effect_rows._DEVELOPMENT_ATTEMPT_FENCE_COLUMNS)}) VALUES "
    f"({', '.join('?' for _ in _effect_rows._DEVELOPMENT_ATTEMPT_FENCE_COLUMNS)})"
)
_EFFECT_INTENT_INSERT = (
    f"INSERT INTO development_effect_intents "
    f"({', '.join(_effect_rows._DEVELOPMENT_EFFECT_INTENT_COLUMNS)}) VALUES "
    f"({', '.join('?' for _ in _effect_rows._DEVELOPMENT_EFFECT_INTENT_COLUMNS)})"
)
_EFFECT_FENCE_INSERT = (
    f"INSERT INTO development_effect_fences "
    f"({', '.join(_effect_rows._DEVELOPMENT_EFFECT_FENCE_COLUMNS)}) VALUES "
    f"({', '.join('?' for _ in _effect_rows._DEVELOPMENT_EFFECT_FENCE_COLUMNS)})"
)
_AUTHOR_COMMAND_INSERT = (
    f"INSERT INTO development_author_commands "
    f"({', '.join(_effect_rows._DEVELOPMENT_AUTHOR_COMMAND_COLUMNS)}) VALUES "
    f"({', '.join('?' for _ in _effect_rows._DEVELOPMENT_AUTHOR_COMMAND_COLUMNS)})"
)
_AUTHORITY_EVALUATION_INSERT = (
    f"INSERT INTO development_authority_evaluations "
    f"({', '.join(_effect_rows._DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS)}) VALUES "
    f"({', '.join('?' for _ in _effect_rows._DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS)})"
)
_EFFECT_HEAD_INSERT = (
    f"INSERT INTO development_effect_heads "
    f"({', '.join(_effect_rows._DEVELOPMENT_EFFECT_HEAD_COLUMNS)}) VALUES "
    f"({', '.join('?' for _ in _effect_rows._DEVELOPMENT_EFFECT_HEAD_COLUMNS)})"
)
_DELIVERY_ATTEMPT_INSERT = (
    f"INSERT INTO development_delivery_attempts "
    f"({', '.join(_effect_rows._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS)}) VALUES "
    f"({', '.join('?' for _ in _effect_rows._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS)})"
)
_DELIVERY_HEAD_INSERT = (
    f"INSERT INTO development_delivery_heads "
    f"({', '.join(_effect_rows._DEVELOPMENT_DELIVERY_HEAD_COLUMNS)}) VALUES "
    f"({', '.join('?' for _ in _effect_rows._DEVELOPMENT_DELIVERY_HEAD_COLUMNS)})"
)
_MUTATION_RECEIPT_INSERT = (
    f"INSERT INTO development_mutation_receipts "
    f"({', '.join(_decision_rows._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS)}) VALUES "
    f"({', '.join('?' for _ in _decision_rows._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS)})"
)
_AUTHOR_EFFECT_INSERT_STATEMENTS = (
    _SEMANTIC_ATTEMPT_INSERT,
    _ATTEMPT_FENCE_INSERT,
    _EFFECT_INTENT_INSERT,
    _EFFECT_FENCE_INSERT,
    _AUTHOR_COMMAND_INSERT,
    _AUTHORITY_EVALUATION_INSERT,
    _EFFECT_HEAD_INSERT,
    _DELIVERY_ATTEMPT_INSERT,
    _DELIVERY_HEAD_INSERT,
    _MUTATION_RECEIPT_INSERT,
)

_SEMANTIC_ATTEMPT_COLLISION_SELECT = (
    "SELECT 1 FROM development_semantic_attempts WHERE "
    "semantic_attempt_ref = ? OR (program_ref = ? AND candidate_ref = ?) "
    "OR (program_ref = ? AND work_item_ref = ? AND attempt_number = ?) LIMIT 2"
)
_ATTEMPT_FENCE_COLLISION_SELECT = (
    "SELECT 1 FROM development_attempt_fences WHERE attempt_fence_ref = ? "
    "OR (program_ref = ? AND semantic_attempt_ref = ?) LIMIT 2"
)
_EFFECT_INTENT_COLLISION_SELECT = (
    "SELECT 1 FROM development_effect_intents WHERE effect_intent_ref = ? "
    "OR (effect_class = 'author_candidate' AND command_ref = ?) LIMIT 2"
)
_EFFECT_FENCE_COLLISION_SELECT = (
    "SELECT 1 FROM development_effect_fences WHERE effect_fence_ref = ? "
    "OR (program_ref = ? AND effect_intent_ref = ?) LIMIT 2"
)
_AUTHOR_COMMAND_COLLISION_SELECT = (
    "SELECT 1 FROM development_author_commands WHERE command_ref = ? "
    "OR effect_intent_ref = ? OR candidate_ref = ? LIMIT 2"
)
_AUTHORITY_EVALUATION_COLLISION_SELECT = (
    "SELECT 1 FROM development_authority_evaluations WHERE "
    "authority_evaluation_ref = ? LIMIT 2"
)
_EFFECT_HEAD_COLLISION_SELECT = (
    "SELECT 1 FROM development_effect_heads WHERE effect_intent_ref = ? LIMIT 2"
)
_DELIVERY_ATTEMPT_COLLISION_SELECT = (
    "SELECT 1 FROM development_delivery_attempts WHERE delivery_attempt_ref = ? "
    "OR (program_ref = ? AND effect_intent_ref = ? AND delivery_number = 1) LIMIT 2"
)
_DELIVERY_HEAD_COLLISION_SELECT = (
    "SELECT 1 FROM development_delivery_heads WHERE effect_intent_ref = ? LIMIT 2"
)


@dataclass(frozen=True, slots=True, repr=False)
class _FreshDevelopmentAuthorEffectEstablishment:
    command: DevelopmentAuthorEffectEstablishmentCommandV1

    def __repr__(self) -> str:
        return "<_FreshDevelopmentAuthorEffectEstablishment>"


def _reduce_development_author_effect_establishment_command(
    *,
    mutation_ref: object,
    program_ref: object,
    program_version_ref: object,
    program_version_number: object,
    accepted_intent_revision_ref: object,
    work_item_ref: object,
    work_item_revision_ref: object,
    basis_decision_ref: object,
    basis_decision_digest: object,
    semantic_attempt_ref: object,
    candidate_ref: object,
    attempt_number: object,
    attempt_fence_ref: object,
    effect_intent_ref: object,
    effect_fence_ref: object,
    command_ref: object,
    authority_evaluation_ref: object,
    delivery_attempt_ref: object,
    adapter_safe_correlation_ref: object,
    coding_global_stop_ref: object,
    coding_global_stop_version: object,
    work_spec: object,
    validation_requirement_evidence: object,
    review_requirement_evidence: object,
    attempt_fence: object,
    effect_authorization_safe_binding: object,
) -> DevelopmentAuthorEffectEstablishmentCommandV1:
    """Reduce transient private material to the closed safe family command."""

    raw_mapping: dict[str, object] | None = None
    result: DevelopmentAuthorEffectEstablishmentCommandV1 | None = None
    ordinary_failure = False
    checked_work_spec: WorkSpecV1 | None = None
    safe_projection: _program_rows.DevelopmentWorkSpecSafeProjection | None = None
    validation: DevelopmentValidationRequirementEvidenceV1 | None = None
    review: DevelopmentReviewRequirementEvidenceV1 | None = None
    checked_attempt_fence: AttemptFenceV1 | None = None
    binding: DevelopmentEffectAuthorizationSafeBindingV1 | None = None
    author_command = None
    author_fence = None
    delivery = None
    checked: dict[str, object] = {}
    try:
        for name, value in (
            ("mutation_ref", mutation_ref),
            ("program_ref", program_ref),
            ("program_version_ref", program_version_ref),
            ("accepted_intent_revision_ref", accepted_intent_revision_ref),
            ("work_item_ref", work_item_ref),
            ("work_item_revision_ref", work_item_revision_ref),
            ("basis_decision_ref", basis_decision_ref),
            ("semantic_attempt_ref", semantic_attempt_ref),
            ("candidate_ref", candidate_ref),
            ("attempt_fence_ref", attempt_fence_ref),
            ("effect_intent_ref", effect_intent_ref),
            ("effect_fence_ref", effect_fence_ref),
            ("command_ref", command_ref),
            ("authority_evaluation_ref", authority_evaluation_ref),
            ("delivery_attempt_ref", delivery_attempt_ref),
            ("adapter_safe_correlation_ref", adapter_safe_correlation_ref),
            ("coding_global_stop_ref", coding_global_stop_ref),
        ):
            checked[name] = _require_safe_ref(value)
        checked["program_version_number"] = _require_positive_integer(
            program_version_number
        )
        checked["attempt_number"] = _require_positive_integer(attempt_number)
        checked["coding_global_stop_version"] = _require_nonnegative_integer(
            coding_global_stop_version
        )
        checked["basis_decision_digest"] = _require_sha256(basis_decision_digest)
        if (
            checked["program_version_number"] != 1
            or checked["attempt_number"] != 1
            or type(work_spec) is not WorkSpecV1
        ):
            ordinary_failure = True
        else:
            raw_mapping = work_spec.to_mapping()
            if type(raw_mapping) is not dict:
                ordinary_failure = True
            else:
                checked_work_spec = WorkSpecV1.from_mapping(raw_mapping)
                safe_projection = (
                    _program_rows.development_work_spec_safe_projection_from_work_spec(
                        work_spec=checked_work_spec
                    )
                )
                validation = _require_exact_validation_evidence(
                    validation_requirement_evidence
                )
                review = _require_exact_review_evidence(review_requirement_evidence)
                checked_attempt_fence = _require_exact_attempt_fence(attempt_fence)
                binding = _require_exact_effect_authorization_safe_binding(
                    effect_authorization_safe_binding
                )
                if not _raw_inputs_are_coherent(
                    checked=checked,
                    work_spec=checked_work_spec,
                    validation=validation,
                    review=review,
                    attempt_fence=checked_attempt_fence,
                    binding=binding,
                ):
                    ordinary_failure = True
                else:
                    author_command, author_fence = (
                        create_author_command_and_effect_fence(
                            work_spec=checked_work_spec,
                            attempt_fence=checked_attempt_fence,
                            command_ref=typing.cast(str, checked["command_ref"]),
                            effect_intent_ref=typing.cast(
                                str, checked["effect_intent_ref"]
                            ),
                            effect_fence_ref=typing.cast(
                                str, checked["effect_fence_ref"]
                            ),
                            candidate_ref=typing.cast(str, checked["candidate_ref"]),
                            effect_authorization_ref=binding.effect_authorization_ref,
                            effect_authorization_digest=(
                                binding.effect_authorization_digest
                            ),
                            expires_at=binding.expires_at,
                            validation_requirement_digest=(
                                validation.requirement_digest
                            ),
                            review_requirement_digest=review.requirement_digest,
                            capsule_profile_ref=("capsule-profile.regular-replace-v1"),
                            redaction_profile_ref="redaction.source-private-v1",
                            effect_ceilings=binding.effect_ceilings,
                        )
                    )
                    validate_authoring_relation(
                        work_spec=checked_work_spec,
                        attempt_fence=checked_attempt_fence,
                        author_command=author_command,
                        author_effect_fence=author_fence,
                    )
                    delivery = DeliveryEnvelopeV1.create(
                        delivery_attempt_ref=typing.cast(
                            str, checked["delivery_attempt_ref"]
                        ),
                        adapter_kind="direct_local_bootstrap",
                        adapter_safe_correlation_ref=typing.cast(
                            str, checked["adapter_safe_correlation_ref"]
                        ),
                        author_command=author_command,
                        attempt_fence=checked_attempt_fence,
                        author_effect_fence=author_fence,
                        effect_fence=author_fence,
                    )
                    result = _development_author_effect_establishment_command(
                        schema_id=(
                            "governed-execution.nwp-establish-development-"
                            "author-effect-intent-command.v1"
                        ),
                        mutation_ref=checked["mutation_ref"],
                        program_ref=checked["program_ref"],
                        program_version_ref=checked["program_version_ref"],
                        program_version_number=checked["program_version_number"],
                        accepted_intent_revision_ref=(
                            checked["accepted_intent_revision_ref"]
                        ),
                        work_item_ref=checked["work_item_ref"],
                        work_item_revision_ref=checked["work_item_revision_ref"],
                        basis_decision_ref=checked["basis_decision_ref"],
                        basis_decision_digest=checked["basis_decision_digest"],
                        semantic_attempt_ref=checked["semantic_attempt_ref"],
                        candidate_ref=checked["candidate_ref"],
                        attempt_number=checked["attempt_number"],
                        attempt_fence_ref=checked["attempt_fence_ref"],
                        effect_intent_ref=checked["effect_intent_ref"],
                        effect_fence_ref=checked["effect_fence_ref"],
                        command_ref=checked["command_ref"],
                        authority_evaluation_ref=(checked["authority_evaluation_ref"]),
                        delivery_attempt_ref=checked["delivery_attempt_ref"],
                        adapter_safe_correlation_ref=(
                            checked["adapter_safe_correlation_ref"]
                        ),
                        coding_global_stop_ref=checked["coding_global_stop_ref"],
                        coding_global_stop_version=(
                            checked["coding_global_stop_version"]
                        ),
                        capsule_schema_id=(
                            "governed-execution.nwp-candidate-capsule-manifest.v1"
                        ),
                        capsule_profile_ref="capsule-profile.regular-replace-v1",
                        privacy_classification="private_source_change",
                        redaction_profile_ref="redaction.source-private-v1",
                        work_spec_safe_projection=safe_projection,
                        validation_requirement_evidence=validation,
                        review_requirement_evidence=review,
                        attempt_fence=checked_attempt_fence,
                        effect_authorization_safe_binding=binding,
                        worker_command=author_command,
                        effect_fence=author_fence,
                        delivery_envelope=delivery,
                    )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        ordinary_failure = True
    finally:
        if type(raw_mapping) is dict:
            raw_mapping.clear()
        checked.clear()
        raw_mapping = None
        checked_work_spec = None
        safe_projection = None
        validation = None
        review = None
        checked_attempt_fence = None
        binding = None
        author_command = None
        author_fence = None
        delivery = None
        work_spec = None
        validation_requirement_evidence = None
        review_requirement_evidence = None
        attempt_fence = None
        effect_authorization_safe_binding = None
    if (
        ordinary_failure
        or type(result) is not DevelopmentAuthorEffectEstablishmentCommandV1
    ):
        result = None
        raise _database_integrity_failure() from None
    return result


def _raw_inputs_are_coherent(
    *,
    checked: dict[str, object],
    work_spec: WorkSpecV1,
    validation: DevelopmentValidationRequirementEvidenceV1,
    review: DevelopmentReviewRequirementEvidenceV1,
    attempt_fence: AttemptFenceV1,
    binding: DevelopmentEffectAuthorizationSafeBindingV1,
) -> bool:
    return bool(
        work_spec.program_ref == checked["program_ref"]
        and work_spec.program_version_ref == checked["program_version_ref"]
        and work_spec.accepted_intent_revision_ref
        == checked["accepted_intent_revision_ref"]
        and work_spec.work_item_ref == checked["work_item_ref"]
        and work_spec.work_item_revision_ref == checked["work_item_revision_ref"]
        and validation.requirement_ref == work_spec.validation_requirement_ref
        and review.requirement_ref == work_spec.review_requirement_ref
        and validation.work_spec_ref == review.work_spec_ref == work_spec.work_spec_ref
        and validation.work_spec_digest
        == review.work_spec_digest
        == work_spec.work_spec_digest
        and attempt_fence.attempt_fence_ref == checked["attempt_fence_ref"]
        and attempt_fence.program_ref == checked["program_ref"]
        and attempt_fence.program_version_ref == checked["program_version_ref"]
        and attempt_fence.accepted_intent_revision_ref
        == checked["accepted_intent_revision_ref"]
        and attempt_fence.work_item_ref == checked["work_item_ref"]
        and attempt_fence.work_item_revision_ref == checked["work_item_revision_ref"]
        and attempt_fence.semantic_attempt_ref == checked["semantic_attempt_ref"]
        and attempt_fence.global_stop_ref == checked["coding_global_stop_ref"]
        and attempt_fence.global_stop_version == checked["coding_global_stop_version"]
        and binding.parent_standing_grant_ref == attempt_fence.parent_standing_grant_ref
        and binding.parent_standing_grant_digest
        == attempt_fence.parent_standing_grant_digest
        and binding.attempt_fence_ref == attempt_fence.attempt_fence_ref
        and binding.attempt_fence_digest == attempt_fence.attempt_fence_digest
        and binding.semantic_attempt_ref == checked["semantic_attempt_ref"]
        and binding.effect_intent_ref == checked["effect_intent_ref"]
        and binding.effect_class == "author_candidate"
        and binding.path_ceiling == attempt_fence.path_ceiling
        and binding.expires_at <= attempt_fence.expires_at
        and binding.global_stop_ref == checked["coding_global_stop_ref"]
        and binding.global_stop_version == checked["coding_global_stop_version"]
    )


def _resolve_development_author_effect_establishment_apply_after_fencing(
    *,
    capability: object,
    command: object,
) -> (
    DevelopmentAuthorEffectEstablishmentResultV1
    | DevelopmentAuthorEffectEstablishmentConflictV1
    | _FreshDevelopmentAuthorEffectEstablishment
):
    checked = _require_exact_development_author_effect_establishment_command(command)

    receipt = _read_development_mutation_receipt_by_mutation_ref(
        capability, checked.mutation_ref
    )
    if receipt is not None:
        if receipt.command_digest != checked.command_digest:
            return _author_effect_conflict(
                checked,
                DevelopmentAuthorEffectEstablishmentConflictReasonV1.MUTATION_REF_REUSE_CONFLICT,
            )
        return _read_and_verify_exact_author_effect_family(
            capability=capability,
            command=checked,
            receipt=receipt,
        )

    stop_envelope = _read_global_stop_current(capability)
    if type(stop_envelope) is not GlobalStopCurrentRecordEnvelope:
        raise _database_integrity_failure() from None
    stop = stop_envelope.state
    if (
        stop.stop_ref != checked.coding_global_stop_ref
        or stop.version != checked.coding_global_stop_version
    ):
        return _author_effect_conflict(
            checked,
            DevelopmentAuthorEffectEstablishmentConflictReasonV1.GLOBAL_STOP_VERSION_CONFLICT,
        )
    if stop.active:
        return _author_effect_conflict(
            checked,
            DevelopmentAuthorEffectEstablishmentConflictReasonV1.CODING_GLOBAL_STOP_ACTIVE,
        )
    if not _genesis_basis_is_current_and_exact(capability, checked):
        raise _database_integrity_failure() from None
    if _selected_author_effect_identity_exists(capability, checked):
        return _author_effect_conflict(
            checked,
            DevelopmentAuthorEffectEstablishmentConflictReasonV1.SEMANTIC_IDENTITY_CONFLICT,
        )
    return _FreshDevelopmentAuthorEffectEstablishment(checked)


def _recover_development_author_effect_establishment_after_fencing(
    *,
    capability: object,
    command: object,
) -> DevelopmentAuthorEffectEstablishmentRecoveryResultV1:
    checked = _require_exact_development_author_effect_establishment_command(command)
    try:
        receipt = _read_development_mutation_receipt_by_mutation_ref(
            capability, checked.mutation_ref
        )
        if receipt is not None:
            if receipt.command_digest != checked.command_digest:
                return _unresolved_recovery()
            try:
                replay = _read_and_verify_exact_author_effect_family(
                    capability=capability,
                    command=checked,
                    receipt=receipt,
                )
            except SQLiteMutationStoreError:
                return _unresolved_recovery()
            if type(replay) is not DevelopmentAuthorEffectEstablishmentResultV1:
                return _unresolved_recovery()
            return DevelopmentAuthorEffectEstablishmentRecoveryResultV1(
                disposition=(
                    DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1.COMMITTED_EXACT
                ),
                committed_result=replay,
            )
        if _selected_author_effect_identity_exists(capability, checked):
            return _unresolved_recovery()
        return DevelopmentAuthorEffectEstablishmentRecoveryResultV1(
            disposition=(
                DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1.DEFINITELY_NOT_COMMITTED
            )
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return _unresolved_recovery()
    finally:
        command = None
        checked = None


def _unresolved_recovery() -> DevelopmentAuthorEffectEstablishmentRecoveryResultV1:
    return DevelopmentAuthorEffectEstablishmentRecoveryResultV1(
        disposition=DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1.UNRESOLVED
    )


def _genesis_basis_is_current_and_exact(
    capability: object,
    command: DevelopmentAuthorEffectEstablishmentCommandV1,
) -> bool:
    try:
        program = _read_development_program_head_and_current_version(
            capability, command.program_ref
        )
        initialization = _read_development_initialize_decision_and_resulting_version(
            capability,
            command.program_ref,
            command.basis_decision_ref,
        )
        intent = _read_development_accepted_intent_revision_by_exact_ref(
            capability,
            command.program_ref,
            command.accepted_intent_revision_ref,
        )
        work = _read_development_work_item_head_and_revision_by_exact_ref(
            capability,
            command.program_ref,
            command.work_item_ref,
            command.work_item_revision_ref,
        )
        membership = _read_development_paged_program_version_membership(
            capability,
            command.program_ref,
            command.program_version_ref,
            1,
        )
        binding = _read_development_work_spec_safe_binding(
            capability,
            command.program_ref,
            command.program_version_ref,
            command.work_item_ref,
            command.work_item_revision_ref,
        )
        if (
            type(program) is not DevelopmentProgramHeadAndCurrentVersionRead
            or type(initialization)
            is not DevelopmentInitializeDecisionAndResultingVersionRead
            or type(intent)
            is not _program_rows.DevelopmentAcceptedIntentRevisionRowValue
            or type(work) is not DevelopmentWorkItemHeadAndRevisionRead
            or type(membership) is not DevelopmentProgramVersionMembershipRead
            or type(binding) is not _program_rows.DevelopmentWorkSpecBindingRowValue
        ):
            return False
        head = program.program_head
        version = program.current_program_version
        decision = initialization.initialize_decision
        resulting = initialization.resulting_program_version
        revision = work.work_item_revision
        entries = membership.entries
        projection = command.work_spec_safe_projection
        return bool(
            head.program_ref == command.program_ref
            and head.current_program_version_ref == command.program_version_ref
            and head.current_program_version_number
            == command.program_version_number
            == 1
            and head.program_state == "active"
            and version == resulting == membership.program_version
            and version.program_ref == command.program_ref
            and version.program_version_ref == command.program_version_ref
            and version.program_version_number == 1
            and version.program_version_kind == "initial"
            and version.creating_decision_ref == command.basis_decision_ref
            and version.accepted_intent_revision_ref
            == command.accepted_intent_revision_ref
            and decision.program_ref == command.program_ref
            and decision.decision_ref == command.basis_decision_ref
            and decision.decision_digest == command.basis_decision_digest
            and decision.decision_kind == "initialize"
            and decision.decision_variant == "program_genesis"
            and decision.expected_program_head_revision == 0
            and decision.resulting_program_version_ref == command.program_version_ref
            and decision.resulting_program_version_number == 1
            and decision.preassigned_semantic_attempt_ref
            == command.semantic_attempt_ref
            and decision.preassigned_candidate_ref == command.candidate_ref
            and decision.coding_global_stop_ref == command.coding_global_stop_ref
            and decision.coding_global_stop_version
            == command.coding_global_stop_version
            and intent.program_ref == command.program_ref
            and intent.accepted_intent_revision_ref
            == command.accepted_intent_revision_ref
            and intent.accepted_intent_revision_number == 1
            and intent.prior_accepted_intent_revision_ref is None
            and work.is_current
            and work.work_item_head.work_item_ref == command.work_item_ref
            and work.work_item_head.current_work_item_revision_ref
            == command.work_item_revision_ref
            and work.work_item_head.current_work_item_revision_number == 1
            and work.work_item_head.work_state == "planned"
            and revision.work_item_revision_number == 1
            and revision.accepted_intent_revision_ref
            == command.accepted_intent_revision_ref
            and len(entries) == 1
            and entries[0].membership.work_item_ref == command.work_item_ref
            and entries[0].membership.work_item_revision_ref
            == command.work_item_revision_ref
            and entries[0].membership.membership_ordinal == 0
            and entries[0].work_item_revision == revision
            and binding.safe_projection == projection
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return False


def _selected_author_effect_identity_exists(
    capability: object,
    command: DevelopmentAuthorEffectEstablishmentCommandV1,
) -> bool:
    probes = (
        (
            _SEMANTIC_ATTEMPT_COLLISION_SELECT,
            (
                command.semantic_attempt_ref,
                command.program_ref,
                command.candidate_ref,
                command.program_ref,
                command.work_item_ref,
                command.attempt_number,
            ),
        ),
        (
            _ATTEMPT_FENCE_COLLISION_SELECT,
            (
                command.attempt_fence_ref,
                command.program_ref,
                command.semantic_attempt_ref,
            ),
        ),
        (
            _EFFECT_INTENT_COLLISION_SELECT,
            (command.effect_intent_ref, command.command_ref),
        ),
        (
            _EFFECT_FENCE_COLLISION_SELECT,
            (
                command.effect_fence_ref,
                command.program_ref,
                command.effect_intent_ref,
            ),
        ),
        (
            _AUTHOR_COMMAND_COLLISION_SELECT,
            (command.command_ref, command.effect_intent_ref, command.candidate_ref),
        ),
        (
            _AUTHORITY_EVALUATION_COLLISION_SELECT,
            (command.authority_evaluation_ref,),
        ),
        (
            _EFFECT_HEAD_COLLISION_SELECT,
            (command.effect_intent_ref,),
        ),
        (
            _DELIVERY_ATTEMPT_COLLISION_SELECT,
            (
                command.delivery_attempt_ref,
                command.program_ref,
                command.effect_intent_ref,
            ),
        ),
        (
            _DELIVERY_HEAD_COLLISION_SELECT,
            (command.effect_intent_ref,),
        ),
    )
    for sql, parameters in probes:
        rows = _execute_select_fetch_two(
            capability=capability,
            sql=sql,
            parameters=parameters,
        )
        if rows:
            rows = []
            return True
    return False


def _read_and_verify_exact_author_effect_family(
    *,
    capability: object,
    command: DevelopmentAuthorEffectEstablishmentCommandV1,
    receipt: object,
) -> DevelopmentAuthorEffectEstablishmentResultV1:
    if type(receipt) is not _decision_rows.DevelopmentMutationReceiptRowValue:
        raise _database_integrity_failure() from None
    expected = _development_author_effect_establishment_write_plan(
        command, receipt.committed_at
    )
    if receipt != expected.mutation_receipt:
        raise _database_integrity_failure() from None

    aggregate = _read_development_attempt_fence_command_effect_aggregate(
        capability,
        command.program_ref,
        command.semantic_attempt_ref,
        command.effect_intent_ref,
    )
    authority = _read_development_authority_evaluation_by_exact_ref(
        capability,
        command.program_ref,
        command.authority_evaluation_ref,
    )
    effect_head = _read_development_effect_head(
        capability,
        command.program_ref,
        command.effect_intent_ref,
    )
    delivery_head = _read_development_delivery_head(
        capability,
        command.program_ref,
        command.effect_intent_ref,
    )
    original_delivery = _read_delivery_attempt_by_exact_ref(
        capability,
        command.program_ref,
        command.delivery_attempt_ref,
    )
    if (
        type(aggregate) is not DevelopmentAttemptFenceCommandEffectRead
        or type(authority) is not _effect_rows.DevelopmentAuthorityEvaluationRowValue
        or type(effect_head) is not _effect_rows.DevelopmentEffectHeadRowValue
        or type(delivery_head) is not DevelopmentDeliveryHeadAndCurrentAttemptRead
        or type(original_delivery)
        is not _effect_rows.DevelopmentDeliveryAttemptRowValue
    ):
        raise _database_integrity_failure() from None
    if (
        aggregate.semantic_attempt != expected.semantic_attempt
        or aggregate.effect_intent != expected.effect_intent
        or aggregate.author_command != expected.author_command
        or aggregate.attempt_fence != expected.attempt_fence
        or aggregate.author_effect_fence != expected.effect_fence
        or aggregate.current_effect_fence != expected.effect_fence
        or authority != expected.authority_evaluation
        or original_delivery != expected.delivery_attempt
    ):
        raise _database_integrity_failure() from None
    if not _effect_head_is_coherent(
        capability=capability,
        command=command,
        actual=effect_head,
        original=expected.effect_head,
        author_fence=expected.effect_fence,
        author_command=expected.author_command,
        attempt_fence=expected.attempt_fence,
        established_at=receipt.committed_at,
    ):
        raise _database_integrity_failure() from None
    if not _delivery_head_is_coherent(
        capability=capability,
        command=command,
        actual=delivery_head,
        original_head=expected.delivery_head,
        original_delivery=expected.delivery_attempt,
        author_fence=expected.effect_fence,
        author_command=expected.author_command,
        attempt_fence=expected.attempt_fence,
        established_at=receipt.committed_at,
    ):
        raise _database_integrity_failure() from None
    return _author_effect_result(command, receipt.committed_at, "exact_replay")


def _effect_head_is_coherent(
    *,
    capability: object,
    command: DevelopmentAuthorEffectEstablishmentCommandV1,
    actual: _effect_rows.DevelopmentEffectHeadRowValue,
    original: _effect_rows.DevelopmentEffectHeadRowValue,
    author_fence: _effect_rows.DevelopmentEffectFenceRowValue,
    author_command: _effect_rows.DevelopmentAuthorCommandRowValue,
    attempt_fence: _effect_rows.DevelopmentAttemptFenceRowValue,
    established_at: str,
) -> bool:
    if actual == original:
        return True
    if not (
        actual.program_ref == command.program_ref
        and actual.effect_intent_ref == command.effect_intent_ref
        and actual.current_effect_fence_ref == command.effect_fence_ref
        and actual.head_revision > original.head_revision
        and actual.updated_at >= established_at
    ):
        return False
    cancellation_ref = actual.cancellation_effect_intent_ref
    if cancellation_ref is None:
        return True
    try:
        cancellation_intent = _read_effect_intent_by_exact_ref(
            capability, command.program_ref, cancellation_ref
        )
        cancellation_fence = _read_effect_fence_by_effect_intent_ref(
            capability, command.program_ref, cancellation_ref
        )
        if (
            type(cancellation_intent)
            is not _effect_rows.DevelopmentEffectIntentRowValue
            or type(cancellation_fence)
            is not _effect_rows.DevelopmentEffectFenceRowValue
        ):
            return False
        if not _cancellation_decision_owns_records(
            capability=capability,
            command=command,
            intent=cancellation_intent,
            fence=cancellation_fence,
        ):
            return False
        validate_effect_relation(
            attempt_fence=attempt_fence.attempt_fence,
            author_command=author_command.worker_command,
            author_effect_fence=author_fence.effect_fence,
            effect_fence=cancellation_fence.effect_fence,
            cancellation_target=author_fence.effect_fence,
        )
        return bool(
            cancellation_intent.program_ref == command.program_ref
            and cancellation_intent.program_version_ref == command.program_version_ref
            and cancellation_intent.semantic_attempt_ref == command.semantic_attempt_ref
            and cancellation_intent.effect_intent_ref == cancellation_ref
            and cancellation_intent.effect_class == "cancel_effect"
            and cancellation_intent.candidate_ref == command.candidate_ref
            and cancellation_intent.command_ref == command.command_ref
            and cancellation_intent.cancellation_target_effect_intent_ref
            == command.effect_intent_ref
            and cancellation_intent.expected_target_effect_head_revision is not None
            and cancellation_intent.expected_target_effect_head_revision
            < actual.head_revision
            and cancellation_intent.portable_capsule_digest is None
            and cancellation_fence.effect_intent_ref == cancellation_ref
            and cancellation_fence.effect_class == "cancel_effect"
            and cancellation_fence.cancellation_target_effect_intent_ref
            == command.effect_intent_ref
            and cancellation_fence.cancellation_target_effect_fence_ref
            == command.effect_fence_ref
            and cancellation_fence.cancellation_target_effect_fence_digest
            == author_fence.effect_fence_digest
            and cancellation_intent.created_at == cancellation_fence.recorded_at
            and established_at <= cancellation_intent.created_at <= actual.updated_at
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return False


def _cancellation_decision_owns_records(
    *,
    capability: object,
    command: DevelopmentAuthorEffectEstablishmentCommandV1,
    intent: _effect_rows.DevelopmentEffectIntentRowValue,
    fence: _effect_rows.DevelopmentEffectFenceRowValue,
) -> bool:
    decision = _read_development_decision_by_decision_ref(
        capability, intent.basis_decision_ref
    )
    return bool(
        type(decision) is _decision_rows.DevelopmentDecisionRowValue
        and decision.program_ref == command.program_ref
        and decision.decision_kind == "cancel"
        and decision.decision_variant == "effect_cancellation"
        and decision.basis_program_version_ref == command.program_version_ref
        and decision.basis_program_version_number == command.program_version_number
        and decision.selected_semantic_attempt_ref == command.semantic_attempt_ref
        and decision.selected_candidate_ref == command.candidate_ref
        and decision.selected_attempt_fence_ref == command.attempt_fence_ref
        and decision.selected_attempt_fence_digest
        == command.attempt_fence.attempt_fence_digest
        and decision.target_effect_intent_ref == command.effect_intent_ref
        and decision.target_effect_class == "author_candidate"
        and decision.target_effect_fence_ref == command.effect_fence_ref
        and decision.target_effect_fence_digest
        == command.effect_fence.effect_fence_digest
        and decision.expected_target_effect_head_revision
        == intent.expected_target_effect_head_revision
        and decision.originating_command_ref == command.command_ref
        and decision.originating_command_digest == command.worker_command.command_digest
        and decision.preassigned_effect_intent_ref == intent.effect_intent_ref
        and decision.preassigned_effect_fence_ref == fence.effect_fence_ref
    )


def _delivery_head_is_coherent(
    *,
    capability: object,
    command: DevelopmentAuthorEffectEstablishmentCommandV1,
    actual: DevelopmentDeliveryHeadAndCurrentAttemptRead,
    original_head: _effect_rows.DevelopmentDeliveryHeadRowValue,
    original_delivery: _effect_rows.DevelopmentDeliveryAttemptRowValue,
    author_fence: _effect_rows.DevelopmentEffectFenceRowValue,
    author_command: _effect_rows.DevelopmentAuthorCommandRowValue,
    attempt_fence: _effect_rows.DevelopmentAttemptFenceRowValue,
    established_at: str,
) -> bool:
    head = actual.delivery_head
    current = actual.current_delivery_attempt
    if head == original_head:
        return current == original_delivery
    if not (
        head.program_ref == command.program_ref
        and head.effect_intent_ref == command.effect_intent_ref
        and head.head_revision > original_head.head_revision
        and head.updated_at >= established_at
        and current.program_ref == command.program_ref
        and current.effect_intent_ref == command.effect_intent_ref
        and current.delivery_attempt_ref == head.current_delivery_attempt_ref
    ):
        return False
    if current.delivery_attempt_ref == original_delivery.delivery_attempt_ref:
        return current == original_delivery
    try:
        if not _redelivery_row_is_coherent(
            capability=capability,
            command=command,
            row=current,
            predecessor_ref=current.predecessor_delivery_attempt_ref,
            original_delivery=original_delivery,
            author_fence=author_fence,
            author_command=author_command,
            attempt_fence=attempt_fence,
        ):
            return False
        predecessor_ref = current.predecessor_delivery_attempt_ref
        if predecessor_ref is None or predecessor_ref == current.delivery_attempt_ref:
            return False
        predecessor = _read_delivery_attempt_by_exact_ref(
            capability, command.program_ref, predecessor_ref
        )
        if type(predecessor) is not _effect_rows.DevelopmentDeliveryAttemptRowValue:
            return False
        if predecessor.delivery_attempt_ref == original_delivery.delivery_attempt_ref:
            predecessor_valid = predecessor == original_delivery
        else:
            predecessor_valid = _redelivery_row_is_coherent(
                capability=capability,
                command=command,
                row=predecessor,
                predecessor_ref=predecessor.predecessor_delivery_attempt_ref,
                original_delivery=original_delivery,
                author_fence=author_fence,
                author_command=author_command,
                attempt_fence=attempt_fence,
            )
        return bool(
            predecessor_valid
            and predecessor.delivery_number == current.delivery_number - 1
            and established_at <= predecessor.recorded_at <= current.recorded_at
            and established_at <= current.recorded_at <= head.updated_at
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return False


def _redelivery_row_is_coherent(
    *,
    capability: object,
    command: DevelopmentAuthorEffectEstablishmentCommandV1,
    row: _effect_rows.DevelopmentDeliveryAttemptRowValue,
    predecessor_ref: str | None,
    original_delivery: _effect_rows.DevelopmentDeliveryAttemptRowValue,
    author_fence: _effect_rows.DevelopmentEffectFenceRowValue,
    author_command: _effect_rows.DevelopmentAuthorCommandRowValue,
    attempt_fence: _effect_rows.DevelopmentAttemptFenceRowValue,
) -> bool:
    if row.delivery_kind != "redelivery" or predecessor_ref is None:
        return False
    validate_delivery_relation(
        delivery=row.delivery_envelope,
        author_command=author_command.worker_command,
        attempt_fence=attempt_fence.attempt_fence,
        author_effect_fence=author_fence.effect_fence,
        effect_fence=author_fence.effect_fence,
    )
    validate_redelivery_relation(
        original_delivery=original_delivery.delivery_envelope,
        candidate_delivery=row.delivery_envelope,
        author_command=author_command.worker_command,
        attempt_fence=attempt_fence.attempt_fence,
        author_effect_fence=author_fence.effect_fence,
        effect_fence=author_fence.effect_fence,
    )
    decision = _read_development_decision_by_decision_ref(
        capability, row.basis_decision_ref
    )
    return bool(
        row.delivery_number > 1
        and type(decision) is _decision_rows.DevelopmentDecisionRowValue
        and decision.program_ref == command.program_ref
        and decision.decision_kind == "redeliver"
        and decision.decision_variant == "productive_redelivery"
        and decision.basis_program_version_ref == command.program_version_ref
        and decision.basis_program_version_number == command.program_version_number
        and decision.selected_semantic_attempt_ref == command.semantic_attempt_ref
        and decision.selected_candidate_ref == command.candidate_ref
        and decision.selected_attempt_fence_ref == command.attempt_fence_ref
        and decision.selected_attempt_fence_digest
        == command.attempt_fence.attempt_fence_digest
        and decision.target_effect_intent_ref == command.effect_intent_ref
        and decision.target_effect_class == "author_candidate"
        and decision.target_effect_fence_ref == command.effect_fence_ref
        and decision.target_effect_fence_digest
        == command.effect_fence.effect_fence_digest
        and decision.target_delivery_attempt_ref == predecessor_ref
        and decision.originating_command_ref == command.command_ref
        and decision.originating_command_digest == command.worker_command.command_digest
        and decision.preassigned_delivery_attempt_ref == row.delivery_attempt_ref
    )


def _read_effect_intent_by_exact_ref(
    capability: object,
    program_ref: str,
    effect_intent_ref: str,
) -> _effect_rows.DevelopmentEffectIntentRowValue | None:
    return typing.cast(
        _effect_rows.DevelopmentEffectIntentRowValue | None,
        _read_optional_family_row(
            capability=capability,
            sql=_EFFECT_INTENT_BY_EXACT_REF_SELECT,
            parameters=(program_ref, effect_intent_ref),
            adapter=_effect_rows.development_effect_intent_row_value_from_row_tuple,
        ),
    )


def _read_effect_fence_by_effect_intent_ref(
    capability: object,
    program_ref: str,
    effect_intent_ref: str,
) -> _effect_rows.DevelopmentEffectFenceRowValue | None:
    return typing.cast(
        _effect_rows.DevelopmentEffectFenceRowValue | None,
        _read_optional_family_row(
            capability=capability,
            sql=_EFFECT_FENCE_BY_EFFECT_INTENT_REF_SELECT,
            parameters=(program_ref, effect_intent_ref),
            adapter=_effect_rows.development_effect_fence_row_value_from_row_tuple,
        ),
    )


def _read_delivery_attempt_by_exact_ref(
    capability: object,
    program_ref: str,
    delivery_attempt_ref: str,
) -> _effect_rows.DevelopmentDeliveryAttemptRowValue | None:
    return typing.cast(
        _effect_rows.DevelopmentDeliveryAttemptRowValue | None,
        _read_optional_family_row(
            capability=capability,
            sql=_DELIVERY_ATTEMPT_BY_EXACT_REF_SELECT,
            parameters=(program_ref, delivery_attempt_ref),
            adapter=_effect_rows.development_delivery_attempt_row_value_from_row_tuple,
        ),
    )


def _read_optional_family_row(
    *,
    capability: object,
    sql: str,
    parameters: tuple[object, ...],
    adapter: typing.Callable[[object], object],
) -> object | None:
    rows = _execute_select_fetch_two(
        capability=capability,
        sql=sql,
        parameters=parameters,
    )
    if len(rows) == 0:
        return None
    if len(rows) != 1:
        raise _database_integrity_failure() from None
    row = rows[0]
    rows = []
    try:
        return adapter(row)
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None


def _execute_development_author_effect_establishment_writes(
    connection: object,
    plan: object,
) -> None:
    if type(connection) is not sqlite3.Connection:
        raise _mutation_failed() from None
    if type(plan) is not _DevelopmentAuthorEffectEstablishmentWritePlan:
        raise _database_integrity_failure() from None
    ordered = (
        (
            _SEMANTIC_ATTEMPT_INSERT,
            _exact_row_parameters(
                plan.semantic_attempt,
                _program_rows.DevelopmentSemanticAttemptRowValue,
            ),
        ),
        (
            _ATTEMPT_FENCE_INSERT,
            _attempt_fence_parameters(plan.attempt_fence),
        ),
        (
            _EFFECT_INTENT_INSERT,
            _exact_row_parameters(
                plan.effect_intent,
                _effect_rows.DevelopmentEffectIntentRowValue,
            ),
        ),
        (
            _EFFECT_FENCE_INSERT,
            _effect_fence_parameters(plan.effect_fence),
        ),
        (
            _AUTHOR_COMMAND_INSERT,
            _author_command_parameters(plan.author_command),
        ),
        (
            _AUTHORITY_EVALUATION_INSERT,
            _exact_row_parameters(
                plan.authority_evaluation,
                _effect_rows.DevelopmentAuthorityEvaluationRowValue,
            ),
        ),
        (
            _EFFECT_HEAD_INSERT,
            _exact_row_parameters(
                plan.effect_head,
                _effect_rows.DevelopmentEffectHeadRowValue,
            ),
        ),
        (
            _DELIVERY_ATTEMPT_INSERT,
            _delivery_attempt_parameters(plan.delivery_attempt),
        ),
        (
            _DELIVERY_HEAD_INSERT,
            _exact_row_parameters(
                plan.delivery_head,
                _effect_rows.DevelopmentDeliveryHeadRowValue,
            ),
        ),
        (
            _MUTATION_RECEIPT_INSERT,
            _receipt_parameters(plan.mutation_receipt),
        ),
    )
    for statement, parameters in ordered:
        _execute_author_effect_insert(connection, statement, parameters)


def _exact_row_parameters(row: object, exact_type: type[object]) -> tuple[object, ...]:
    if type(row) is not exact_type:
        raise _database_integrity_failure() from None
    values = object.__getattribute__(row, "_values")
    if type(values) is not tuple:
        raise _database_integrity_failure() from None
    return tuple(values)


def _attempt_fence_parameters(row: object) -> tuple[object, ...]:
    if type(row) is not _effect_rows.DevelopmentAttemptFenceRowValue:
        raise _database_integrity_failure() from None
    return _row_to_columns(row, _effect_rows._DEVELOPMENT_ATTEMPT_FENCE_COLUMNS)


def _effect_fence_parameters(row: object) -> tuple[object, ...]:
    if type(row) is not _effect_rows.DevelopmentEffectFenceRowValue:
        raise _database_integrity_failure() from None
    return _row_to_columns(row, _effect_rows._DEVELOPMENT_EFFECT_FENCE_COLUMNS)


def _author_command_parameters(row: object) -> tuple[object, ...]:
    if type(row) is not _effect_rows.DevelopmentAuthorCommandRowValue:
        raise _database_integrity_failure() from None
    return _row_to_columns(row, _effect_rows._DEVELOPMENT_AUTHOR_COMMAND_COLUMNS)


def _delivery_attempt_parameters(row: object) -> tuple[object, ...]:
    if type(row) is not _effect_rows.DevelopmentDeliveryAttemptRowValue:
        raise _database_integrity_failure() from None
    return _row_to_columns(row, _effect_rows._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS)


def _row_to_columns(row: object, columns: tuple[str, ...]) -> tuple[object, ...]:
    return tuple(getattr(row, column) for column in columns)


def _receipt_parameters(row: object) -> tuple[object, ...]:
    if type(row) is not _decision_rows.DevelopmentMutationReceiptRowValue:
        raise _database_integrity_failure() from None
    return tuple(row._values[:19])


def _execute_author_effect_insert(
    connection: sqlite3.Connection,
    statement: str,
    parameters: tuple[object, ...],
) -> None:
    if type(statement) is not str or not any(
        statement is allowed for allowed in _AUTHOR_EFFECT_INSERT_STATEMENTS
    ):
        raise _database_integrity_failure() from None
    if type(parameters) is not tuple:
        raise _database_integrity_failure() from None
    cursor = None
    failure: SQLiteMutationStoreError | None = None
    rowcount: object = None
    try:
        cursor = connection.execute(statement, parameters)
        rowcount = cursor.rowcount
    except sqlite3.Error as error:
        failure = _classify_sqlite_write_error(error)
    except Exception:
        failure = _mutation_failed()
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                if failure is None:
                    failure = _mutation_failed()
    if failure is not None:
        raise failure from None
    if type(rowcount) is not int or rowcount != 1:
        raise _database_integrity_failure() from None


_SQLITE_INTEGRITY_PRIMARY_CODES = frozenset(
    code
    for code in (
        getattr(sqlite3, "SQLITE_ERROR", None),
        getattr(sqlite3, "SQLITE_SCHEMA", None),
        getattr(sqlite3, "SQLITE_CORRUPT", None),
        getattr(sqlite3, "SQLITE_NOTADB", None),
        getattr(sqlite3, "SQLITE_MISMATCH", None),
        getattr(sqlite3, "SQLITE_CONSTRAINT", None),
    )
    if type(code) is int
)


def _classify_sqlite_write_error(error: sqlite3.Error) -> SQLiteMutationStoreError:
    code = getattr(error, "sqlite_errorcode", None)
    primary = code & 0xFF if type(code) is int else None
    if primary in _SQLITE_INTEGRITY_PRIMARY_CODES:
        return _database_integrity_failure()
    return _mutation_failed()


def _database_integrity_failure() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(
        SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
    )


def _mutation_failed() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)
