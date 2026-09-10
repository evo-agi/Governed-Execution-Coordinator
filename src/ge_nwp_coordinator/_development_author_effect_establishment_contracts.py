"""Private pure contracts for one author-effect establishment family.

The values and planner in this module are route-neutral and perform no I/O.
They retain only the privacy-safe C2A/C2B2 projections needed by the durable
family; a complete WorkSpec is never stored here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
import typing

from . import _development_decision_row_values as _decision_rows
from . import _development_effect_row_values as _effect_rows
from . import _development_program_row_values as _program_rows
from ._development_row_value_support import (
    _RowValueValidationError,
    _domain_separated_digest,
    _encode_effect_class_mask,
    _require_constant_string,
    _require_nonnegative_integer,
    _require_positive_integer,
    _require_safe_ref,
    _require_sha256,
    _require_utc_timestamp,
)
from ._worker_execution_semantic_values import (
    AttemptFenceV1,
    CeilingsV1,
    DeliveryEnvelopeV1,
    EffectFenceV1,
    WorkerCommandV1,
    WorkerExecutionValueError,
    validate_delivery_relation,
)
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode


__all__: tuple[str, ...] = ()


_VALIDATION_EVIDENCE_SCHEMA = (
    "governed-execution.nwp-development-validation-requirement-evidence.v1"
)
_REVIEW_EVIDENCE_SCHEMA = (
    "governed-execution.nwp-development-review-requirement-evidence.v1"
)
_EFFECT_AUTHORIZATION_BINDING_SCHEMA = (
    "governed-execution.nwp-development-effect-authorization-safe-binding.v1"
)
_COMMAND_SCHEMA = (
    "governed-execution.nwp-establish-development-author-effect-intent-command.v1"
)
_RESULT_SCHEMA = (
    "governed-execution.nwp-development-author-effect-establishment-result.v1"
)
_RECEIPT_RESULT_SCHEMA = (
    "governed-execution.nwp-establish-development-author-effect-intent-result.v1"
)

_VALIDATION_EVIDENCE_DOMAIN = _VALIDATION_EVIDENCE_SCHEMA + ".identity"
_REVIEW_EVIDENCE_DOMAIN = _REVIEW_EVIDENCE_SCHEMA + ".identity"
_EFFECT_AUTHORIZATION_BINDING_DOMAIN = (
    _EFFECT_AUTHORIZATION_BINDING_SCHEMA + ".identity"
)
_COMMAND_DOMAIN = _COMMAND_SCHEMA + ".identity"
_RESULT_DOMAIN = _RESULT_SCHEMA + ".identity"
_RECEIPT_RESULT_DOMAIN = _RECEIPT_RESULT_SCHEMA + ".identity"

_CAPSULE_SCHEMA = "governed-execution.nwp-candidate-capsule-manifest.v1"
_CAPSULE_PROFILE = "capsule-profile.regular-replace-v1"
_PRIVACY_CLASSIFICATION = "private_source_change"
_REDACTION_PROFILE = "redaction.source-private-v1"
_MUTATION_FAMILY = "establish_development_author_effect_intent"


class DevelopmentAuthorEffectEstablishmentConflictReasonV1(str, Enum):
    MUTATION_REF_REUSE_CONFLICT = "mutation_ref_reuse_conflict"
    GLOBAL_STOP_VERSION_CONFLICT = "global_stop_version_conflict"
    CODING_GLOBAL_STOP_ACTIVE = "coding_global_stop_active"
    SEMANTIC_IDENTITY_CONFLICT = "semantic_identity_conflict"


class DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1(str, Enum):
    COMMITTED_EXACT = "committed_exact"
    DEFINITELY_NOT_COMMITTED = "definitely_not_committed"
    UNRESOLVED = "unresolved"


def _constant_repr(value: object) -> str:
    return f"<{type(value).__name__}>"


def _disable_pickle(self: object, protocol: object = None) -> typing.NoReturn:
    raise TypeError("pickling disabled")


def _safe_projection_mapping(
    value: _program_rows.DevelopmentWorkSpecSafeProjection,
) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "work_spec_ref": value.work_spec_ref,
        "program_ref": value.program_ref,
        "program_version_ref": value.program_version_ref,
        "accepted_intent_revision_ref": value.accepted_intent_revision_ref,
        "work_item_ref": value.work_item_ref,
        "work_item_revision_ref": value.work_item_revision_ref,
        "repository_ref": value.repository_ref,
        "base_git_object_format": value.base_git_object_format,
        "base_git_oid": value.base_git_oid,
        "authorized_paths": value.authorized_paths,
        "validation_requirement_ref": value.validation_requirement_ref,
        "review_requirement_ref": value.review_requirement_ref,
        "privacy_classification": value.privacy_classification,
        "work_spec_digest": value.work_spec_digest,
        "safe_projection_digest": value.safe_projection_digest,
    }


def _require_exact_work_spec_safe_projection(
    value: object,
) -> _program_rows.DevelopmentWorkSpecSafeProjection:
    raw: object = None
    try:
        if type(value) is not _program_rows.DevelopmentWorkSpecSafeProjection:
            raise _RowValueValidationError() from None
        raw = object.__getattribute__(value, "_values")
        if type(raw) is not tuple or len(raw) != 16:
            raise _RowValueValidationError() from None
        values = typing.cast(tuple[object, ...], raw)
        return _program_rows._persisted_safe_projection_from_fields(
            work_spec_ref=values[1],
            program_ref=values[2],
            program_version_ref=values[3],
            accepted_intent_revision_ref=values[4],
            work_item_ref=values[5],
            work_item_revision_ref=values[6],
            repository_ref=values[7],
            base_git_object_format=values[8],
            base_git_oid=values[9],
            authorized_paths=values[10],
            validation_requirement_ref=values[11],
            review_requirement_ref=values[12],
            privacy_classification=values[13],
            work_spec_digest=values[14],
            persisted_safe_projection_digest=values[15],
        )
    except _RowValueValidationError:
        raise _database_integrity_failure() from None
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        value = None
        raw = None


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentValidationRequirementEvidenceV1:
    schema_id: str
    requirement_ref: str
    requirement_digest: str
    work_spec_ref: str
    work_spec_digest: str
    safe_evidence_digest: str

    def __post_init__(self) -> None:
        _validate_requirement_evidence(self, validation=True)

    def identity_mapping(self) -> dict[str, object]:
        return _requirement_evidence_identity(self, validation=True)

    def computed_digest(self) -> str:
        return _domain_separated_digest(
            _VALIDATION_EVIDENCE_DOMAIN, self.identity_mapping()
        )

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentReviewRequirementEvidenceV1:
    schema_id: str
    requirement_ref: str
    requirement_digest: str
    work_spec_ref: str
    work_spec_digest: str
    safe_evidence_digest: str

    def __post_init__(self) -> None:
        _validate_requirement_evidence(self, validation=False)

    def identity_mapping(self) -> dict[str, object]:
        return _requirement_evidence_identity(self, validation=False)

    def computed_digest(self) -> str:
        return _domain_separated_digest(
            _REVIEW_EVIDENCE_DOMAIN, self.identity_mapping()
        )

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


def _requirement_evidence_identity(
    value: (
        DevelopmentValidationRequirementEvidenceV1
        | DevelopmentReviewRequirementEvidenceV1
    ),
    *,
    validation: bool,
) -> dict[str, object]:
    schema = _VALIDATION_EVIDENCE_SCHEMA if validation else _REVIEW_EVIDENCE_SCHEMA
    try:
        return {
            "schema_id": _require_constant_string(value.schema_id, schema),
            "requirement_ref": _require_safe_ref(value.requirement_ref),
            "requirement_digest": _require_sha256(value.requirement_digest),
            "work_spec_ref": _require_safe_ref(value.work_spec_ref),
            "work_spec_digest": _require_sha256(value.work_spec_digest),
        }
    except _RowValueValidationError:
        raise _database_integrity_failure() from None


def _validate_requirement_evidence(
    value: (
        DevelopmentValidationRequirementEvidenceV1
        | DevelopmentReviewRequirementEvidenceV1
    ),
    *,
    validation: bool,
) -> None:
    identity = _requirement_evidence_identity(value, validation=validation)
    domain = _VALIDATION_EVIDENCE_DOMAIN if validation else _REVIEW_EVIDENCE_DOMAIN
    try:
        stored = _require_sha256(value.safe_evidence_digest)
    except _RowValueValidationError:
        raise _database_integrity_failure() from None
    if stored != _domain_separated_digest(domain, identity):
        raise _database_integrity_failure() from None


def _development_validation_requirement_evidence(
    *,
    requirement_ref: object,
    requirement_digest: object,
    work_spec_ref: object,
    work_spec_digest: object,
) -> DevelopmentValidationRequirementEvidenceV1:
    return typing.cast(
        DevelopmentValidationRequirementEvidenceV1,
        _new_requirement_evidence(
            validation=True,
            requirement_ref=requirement_ref,
            requirement_digest=requirement_digest,
            work_spec_ref=work_spec_ref,
            work_spec_digest=work_spec_digest,
        ),
    )


def _development_review_requirement_evidence(
    *,
    requirement_ref: object,
    requirement_digest: object,
    work_spec_ref: object,
    work_spec_digest: object,
) -> DevelopmentReviewRequirementEvidenceV1:
    return typing.cast(
        DevelopmentReviewRequirementEvidenceV1,
        _new_requirement_evidence(
            validation=False,
            requirement_ref=requirement_ref,
            requirement_digest=requirement_digest,
            work_spec_ref=work_spec_ref,
            work_spec_digest=work_spec_digest,
        ),
    )


def _new_requirement_evidence(
    *,
    validation: bool,
    requirement_ref: object,
    requirement_digest: object,
    work_spec_ref: object,
    work_spec_digest: object,
) -> object:
    try:
        schema = _VALIDATION_EVIDENCE_SCHEMA if validation else _REVIEW_EVIDENCE_SCHEMA
        domain = _VALIDATION_EVIDENCE_DOMAIN if validation else _REVIEW_EVIDENCE_DOMAIN
        identity = {
            "schema_id": schema,
            "requirement_ref": _require_safe_ref(requirement_ref),
            "requirement_digest": _require_sha256(requirement_digest),
            "work_spec_ref": _require_safe_ref(work_spec_ref),
            "work_spec_digest": _require_sha256(work_spec_digest),
        }
        fields = {
            **identity,
            "safe_evidence_digest": _domain_separated_digest(domain, identity),
        }
        value_type = (
            DevelopmentValidationRequirementEvidenceV1
            if validation
            else DevelopmentReviewRequirementEvidenceV1
        )
        return value_type(**fields)
    except _RowValueValidationError:
        raise _database_integrity_failure() from None
    finally:
        requirement_ref = None
        requirement_digest = None
        work_spec_ref = None
        work_spec_digest = None


def _require_exact_validation_evidence(
    value: object,
) -> DevelopmentValidationRequirementEvidenceV1:
    if type(value) is not DevelopmentValidationRequirementEvidenceV1:
        raise _database_integrity_failure() from None
    try:
        return DevelopmentValidationRequirementEvidenceV1(
            schema_id=object.__getattribute__(value, "schema_id"),
            requirement_ref=object.__getattribute__(value, "requirement_ref"),
            requirement_digest=object.__getattribute__(value, "requirement_digest"),
            work_spec_ref=object.__getattribute__(value, "work_spec_ref"),
            work_spec_digest=object.__getattribute__(value, "work_spec_digest"),
            safe_evidence_digest=object.__getattribute__(value, "safe_evidence_digest"),
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        value = None


def _require_exact_review_evidence(
    value: object,
) -> DevelopmentReviewRequirementEvidenceV1:
    if type(value) is not DevelopmentReviewRequirementEvidenceV1:
        raise _database_integrity_failure() from None
    try:
        return DevelopmentReviewRequirementEvidenceV1(
            schema_id=object.__getattribute__(value, "schema_id"),
            requirement_ref=object.__getattribute__(value, "requirement_ref"),
            requirement_digest=object.__getattribute__(value, "requirement_digest"),
            work_spec_ref=object.__getattribute__(value, "work_spec_ref"),
            work_spec_digest=object.__getattribute__(value, "work_spec_digest"),
            safe_evidence_digest=object.__getattribute__(value, "safe_evidence_digest"),
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        value = None


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentEffectAuthorizationSafeBindingV1:
    schema_id: str
    parent_standing_grant_ref: str
    parent_standing_grant_digest: str
    effect_authorization_ref: str
    effect_authorization_digest: str
    attempt_fence_ref: str
    attempt_fence_digest: str
    semantic_attempt_ref: str
    effect_intent_ref: str
    effect_class: str
    path_ceiling: tuple[str, ...]
    effect_ceilings: CeilingsV1 = field(repr=False)
    expires_at: str
    global_stop_ref: str
    global_stop_version: int
    safe_binding_digest: str

    def __post_init__(self) -> None:
        identity = _effect_authorization_binding_identity(self)
        try:
            stored = _require_sha256(self.safe_binding_digest)
        except _RowValueValidationError:
            raise _database_integrity_failure() from None
        if stored != _domain_separated_digest(
            _EFFECT_AUTHORIZATION_BINDING_DOMAIN, identity
        ):
            raise _database_integrity_failure() from None

    def identity_mapping(self) -> dict[str, object]:
        return _effect_authorization_binding_identity(self)

    def computed_digest(self) -> str:
        return _domain_separated_digest(
            _EFFECT_AUTHORIZATION_BINDING_DOMAIN, self.identity_mapping()
        )

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


def _effect_authorization_binding_identity(
    value: DevelopmentEffectAuthorizationSafeBindingV1,
) -> dict[str, object]:
    try:
        if type(value.path_ceiling) is not tuple or any(
            type(path) is not str for path in value.path_ceiling
        ):
            raise _RowValueValidationError() from None
        if type(value.effect_ceilings) is not CeilingsV1:
            raise _RowValueValidationError() from None
        ceilings = CeilingsV1.from_mapping(value.effect_ceilings.to_mapping())
        return {
            "schema_id": _require_constant_string(
                value.schema_id, _EFFECT_AUTHORIZATION_BINDING_SCHEMA
            ),
            "parent_standing_grant_ref": _require_safe_ref(
                value.parent_standing_grant_ref
            ),
            "parent_standing_grant_digest": _require_sha256(
                value.parent_standing_grant_digest
            ),
            "effect_authorization_ref": _require_safe_ref(
                value.effect_authorization_ref
            ),
            "effect_authorization_digest": _require_sha256(
                value.effect_authorization_digest
            ),
            "attempt_fence_ref": _require_safe_ref(value.attempt_fence_ref),
            "attempt_fence_digest": _require_sha256(value.attempt_fence_digest),
            "semantic_attempt_ref": _require_safe_ref(value.semantic_attempt_ref),
            "effect_intent_ref": _require_safe_ref(value.effect_intent_ref),
            "effect_class": _require_constant_string(
                value.effect_class, "author_candidate"
            ),
            "path_ceiling": tuple(value.path_ceiling),
            "effect_ceilings": ceilings.to_mapping(),
            "expires_at": _require_utc_timestamp(value.expires_at),
            "global_stop_ref": _require_safe_ref(value.global_stop_ref),
            "global_stop_version": _require_nonnegative_integer(
                value.global_stop_version
            ),
        }
    except (_RowValueValidationError, WorkerExecutionValueError):
        raise _database_integrity_failure() from None


def _development_effect_authorization_safe_binding(
    *,
    parent_standing_grant_ref: object,
    parent_standing_grant_digest: object,
    effect_authorization_ref: object,
    effect_authorization_digest: object,
    attempt_fence_ref: object,
    attempt_fence_digest: object,
    semantic_attempt_ref: object,
    effect_intent_ref: object,
    effect_class: object,
    path_ceiling: object,
    effect_ceilings: object,
    expires_at: object,
    global_stop_ref: object,
    global_stop_version: object,
) -> DevelopmentEffectAuthorizationSafeBindingV1:
    provisional = object.__new__(DevelopmentEffectAuthorizationSafeBindingV1)
    inputs = (
        (_EFFECT_AUTHORIZATION_BINDING_SCHEMA, "schema_id"),
        (parent_standing_grant_ref, "parent_standing_grant_ref"),
        (parent_standing_grant_digest, "parent_standing_grant_digest"),
        (effect_authorization_ref, "effect_authorization_ref"),
        (effect_authorization_digest, "effect_authorization_digest"),
        (attempt_fence_ref, "attempt_fence_ref"),
        (attempt_fence_digest, "attempt_fence_digest"),
        (semantic_attempt_ref, "semantic_attempt_ref"),
        (effect_intent_ref, "effect_intent_ref"),
        (effect_class, "effect_class"),
        (path_ceiling, "path_ceiling"),
        (effect_ceilings, "effect_ceilings"),
        (expires_at, "expires_at"),
        (global_stop_ref, "global_stop_ref"),
        (global_stop_version, "global_stop_version"),
    )
    try:
        for value, name in inputs:
            object.__setattr__(provisional, name, value)
        identity = _effect_authorization_binding_identity(provisional)
        construction = dict(identity)
        construction["effect_ceilings"] = CeilingsV1.from_mapping(
            identity["effect_ceilings"]
        )
        return DevelopmentEffectAuthorizationSafeBindingV1(
            **construction,
            safe_binding_digest=_domain_separated_digest(
                _EFFECT_AUTHORIZATION_BINDING_DOMAIN, identity
            ),
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        construction = None
        provisional = None
        parent_standing_grant_ref = None
        parent_standing_grant_digest = None
        effect_authorization_ref = None
        effect_authorization_digest = None
        attempt_fence_ref = None
        attempt_fence_digest = None
        semantic_attempt_ref = None
        effect_intent_ref = None
        effect_class = None
        path_ceiling = None
        effect_ceilings = None
        expires_at = None
        global_stop_ref = None
        global_stop_version = None


def _require_exact_effect_authorization_safe_binding(
    value: object,
) -> DevelopmentEffectAuthorizationSafeBindingV1:
    if type(value) is not DevelopmentEffectAuthorizationSafeBindingV1:
        raise _database_integrity_failure() from None
    try:
        return DevelopmentEffectAuthorizationSafeBindingV1(
            schema_id=object.__getattribute__(value, "schema_id"),
            parent_standing_grant_ref=object.__getattribute__(
                value, "parent_standing_grant_ref"
            ),
            parent_standing_grant_digest=object.__getattribute__(
                value, "parent_standing_grant_digest"
            ),
            effect_authorization_ref=object.__getattribute__(
                value, "effect_authorization_ref"
            ),
            effect_authorization_digest=object.__getattribute__(
                value, "effect_authorization_digest"
            ),
            attempt_fence_ref=object.__getattribute__(value, "attempt_fence_ref"),
            attempt_fence_digest=object.__getattribute__(value, "attempt_fence_digest"),
            semantic_attempt_ref=object.__getattribute__(value, "semantic_attempt_ref"),
            effect_intent_ref=object.__getattribute__(value, "effect_intent_ref"),
            effect_class=object.__getattribute__(value, "effect_class"),
            path_ceiling=object.__getattribute__(value, "path_ceiling"),
            effect_ceilings=object.__getattribute__(value, "effect_ceilings"),
            expires_at=object.__getattribute__(value, "expires_at"),
            global_stop_ref=object.__getattribute__(value, "global_stop_ref"),
            global_stop_version=object.__getattribute__(value, "global_stop_version"),
            safe_binding_digest=object.__getattribute__(value, "safe_binding_digest"),
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        value = None


def _require_exact_attempt_fence(value: object) -> AttemptFenceV1:
    try:
        if type(value) is not AttemptFenceV1:
            raise WorkerExecutionValueError("invalid_type", "attempt_fence")
        return AttemptFenceV1.from_mapping(value.to_mapping())
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        value = None


def _require_exact_worker_command(value: object) -> WorkerCommandV1:
    try:
        if type(value) is not WorkerCommandV1:
            raise WorkerExecutionValueError("invalid_type", "worker_command")
        return WorkerCommandV1.from_mapping(value.to_mapping())
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        value = None


def _require_exact_effect_fence(value: object) -> EffectFenceV1:
    try:
        if type(value) is not EffectFenceV1:
            raise WorkerExecutionValueError("invalid_type", "effect_fence")
        return EffectFenceV1.from_mapping(value.to_mapping())
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        value = None


def _require_exact_delivery_envelope(value: object) -> DeliveryEnvelopeV1:
    try:
        if type(value) is not DeliveryEnvelopeV1:
            raise WorkerExecutionValueError("invalid_type", "delivery_envelope")
        return DeliveryEnvelopeV1.from_mapping(value.to_mapping())
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        value = None


def _requirement_mapping(
    value: (
        DevelopmentValidationRequirementEvidenceV1
        | DevelopmentReviewRequirementEvidenceV1
    ),
) -> dict[str, object]:
    return {
        **value.identity_mapping(),
        "safe_evidence_digest": value.safe_evidence_digest,
    }


def _binding_mapping(
    value: DevelopmentEffectAuthorizationSafeBindingV1,
) -> dict[str, object]:
    return {
        **value.identity_mapping(),
        "safe_binding_digest": value.safe_binding_digest,
    }


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentAuthorEffectEstablishmentCommandV1:
    schema_id: str
    mutation_ref: str
    program_ref: str
    program_version_ref: str
    program_version_number: int
    accepted_intent_revision_ref: str
    work_item_ref: str
    work_item_revision_ref: str
    basis_decision_ref: str
    basis_decision_digest: str
    semantic_attempt_ref: str
    candidate_ref: str
    attempt_number: int
    attempt_fence_ref: str
    effect_intent_ref: str
    effect_fence_ref: str
    command_ref: str
    authority_evaluation_ref: str
    delivery_attempt_ref: str
    adapter_safe_correlation_ref: str
    coding_global_stop_ref: str
    coding_global_stop_version: int
    capsule_schema_id: str
    capsule_profile_ref: str
    privacy_classification: str
    redaction_profile_ref: str
    work_spec_safe_projection: _program_rows.DevelopmentWorkSpecSafeProjection = field(
        repr=False
    )
    validation_requirement_evidence: DevelopmentValidationRequirementEvidenceV1 = field(
        repr=False
    )
    review_requirement_evidence: DevelopmentReviewRequirementEvidenceV1 = field(
        repr=False
    )
    attempt_fence: AttemptFenceV1 = field(repr=False)
    effect_authorization_safe_binding: DevelopmentEffectAuthorizationSafeBindingV1 = (
        field(repr=False)
    )
    worker_command: WorkerCommandV1 = field(repr=False)
    effect_fence: EffectFenceV1 = field(repr=False)
    delivery_envelope: DeliveryEnvelopeV1 = field(repr=False)
    command_digest: str

    def __post_init__(self) -> None:
        identity = _author_effect_command_identity(self)
        try:
            stored = _require_sha256(self.command_digest)
        except _RowValueValidationError:
            raise _database_integrity_failure() from None
        if stored != _domain_separated_digest(_COMMAND_DOMAIN, identity):
            raise _database_integrity_failure() from None

    def identity_mapping(self) -> dict[str, object]:
        return _author_effect_command_identity(self)

    def computed_digest(self) -> str:
        return _domain_separated_digest(_COMMAND_DOMAIN, self.identity_mapping())

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


def _author_effect_command_identity(
    value: DevelopmentAuthorEffectEstablishmentCommandV1,
) -> dict[str, object]:
    try:
        refs = tuple(
            _require_safe_ref(item)
            for item in (
                value.mutation_ref,
                value.program_ref,
                value.program_version_ref,
                value.accepted_intent_revision_ref,
                value.work_item_ref,
                value.work_item_revision_ref,
                value.basis_decision_ref,
                value.semantic_attempt_ref,
                value.candidate_ref,
                value.attempt_fence_ref,
                value.effect_intent_ref,
                value.effect_fence_ref,
                value.command_ref,
                value.authority_evaluation_ref,
                value.delivery_attempt_ref,
                value.adapter_safe_correlation_ref,
                value.coding_global_stop_ref,
                value.capsule_profile_ref,
                value.redaction_profile_ref,
            )
        )
        version_number = _require_positive_integer(value.program_version_number)
        attempt_number = _require_positive_integer(value.attempt_number)
        if version_number != 1 or attempt_number != 1:
            raise _RowValueValidationError() from None
        basis_digest = _require_sha256(value.basis_decision_digest)
        stop_version = _require_nonnegative_integer(value.coding_global_stop_version)
        projection = _require_exact_work_spec_safe_projection(
            value.work_spec_safe_projection
        )
        validation = _require_exact_validation_evidence(
            value.validation_requirement_evidence
        )
        review = _require_exact_review_evidence(value.review_requirement_evidence)
        attempt_fence = _require_exact_attempt_fence(value.attempt_fence)
        binding = _require_exact_effect_authorization_safe_binding(
            value.effect_authorization_safe_binding
        )
        worker_command = _require_exact_worker_command(value.worker_command)
        effect_fence = _require_exact_effect_fence(value.effect_fence)
        delivery = _require_exact_delivery_envelope(value.delivery_envelope)
        _require_constant_string(value.schema_id, _COMMAND_SCHEMA)
        _require_constant_string(value.capsule_schema_id, _CAPSULE_SCHEMA)
        _require_constant_string(value.capsule_profile_ref, _CAPSULE_PROFILE)
        _require_constant_string(value.privacy_classification, _PRIVACY_CLASSIFICATION)
        _require_constant_string(value.redaction_profile_ref, _REDACTION_PROFILE)
        if not (
            projection.program_ref == refs[1]
            and projection.program_version_ref == refs[2]
            and projection.accepted_intent_revision_ref == refs[3]
            and projection.work_item_ref == refs[4]
            and projection.work_item_revision_ref == refs[5]
            and validation.requirement_ref == projection.validation_requirement_ref
            and review.requirement_ref == projection.review_requirement_ref
            and validation.work_spec_ref
            == review.work_spec_ref
            == projection.work_spec_ref
            and validation.work_spec_digest
            == review.work_spec_digest
            == projection.work_spec_digest
            and attempt_fence.attempt_fence_ref == refs[9]
            and attempt_fence.program_ref == refs[1]
            and attempt_fence.program_version_ref == refs[2]
            and attempt_fence.accepted_intent_revision_ref == refs[3]
            and attempt_fence.work_item_ref == refs[4]
            and attempt_fence.work_item_revision_ref == refs[5]
            and attempt_fence.semantic_attempt_ref == refs[7]
            and attempt_fence.global_stop_ref == refs[16]
            and attempt_fence.global_stop_version == stop_version
            and binding.parent_standing_grant_ref
            == attempt_fence.parent_standing_grant_ref
            and binding.parent_standing_grant_digest
            == attempt_fence.parent_standing_grant_digest
            and binding.attempt_fence_ref == refs[9]
            and binding.attempt_fence_digest == attempt_fence.attempt_fence_digest
            and binding.semantic_attempt_ref == refs[7]
            and binding.effect_intent_ref == refs[10]
            and binding.effect_class == "author_candidate"
            and binding.path_ceiling == attempt_fence.path_ceiling
            and binding.global_stop_ref == refs[16]
            and binding.global_stop_version == stop_version
            and binding.expires_at <= attempt_fence.expires_at
            and worker_command.command_ref == refs[12]
            and worker_command.effect_intent_ref == refs[10]
            and worker_command.effect_fence_ref == refs[11]
            and worker_command.candidate_ref == refs[8]
            and worker_command.capsule_profile_ref == refs[17]
            and worker_command.redaction_profile_ref == refs[18]
            and effect_fence.effect_fence_ref == refs[11]
            and delivery.delivery_attempt_ref == refs[14]
            and delivery.adapter_safe_correlation_ref == refs[15]
            and delivery.adapter_kind == "direct_local_bootstrap"
        ):
            raise _RowValueValidationError() from None
    except (_RowValueValidationError, WorkerExecutionValueError):
        raise _database_integrity_failure() from None
    if not (
        worker_command.program_ref == refs[1]
        and worker_command.program_version_ref == refs[2]
        and worker_command.accepted_intent_revision_ref == refs[3]
        and worker_command.work_item_ref == refs[4]
        and worker_command.work_item_revision_ref == refs[5]
        and worker_command.semantic_attempt_ref == refs[7]
        and worker_command.work_spec_ref == projection.work_spec_ref
        and worker_command.work_spec_digest == projection.work_spec_digest
        and worker_command.validation_requirement_ref == validation.requirement_ref
        and worker_command.validation_requirement_digest
        == validation.requirement_digest
        and worker_command.review_requirement_ref == review.requirement_ref
        and worker_command.review_requirement_digest == review.requirement_digest
        and worker_command.attempt_fence_digest == attempt_fence.attempt_fence_digest
        and worker_command.effect_authorization_ref == binding.effect_authorization_ref
        and worker_command.effect_authorization_digest
        == binding.effect_authorization_digest
        and worker_command.effect_ceilings == binding.effect_ceilings
        and effect_fence.effect_fence_digest == worker_command.effect_fence_digest
        and effect_fence.effect_authorization_ref == binding.effect_authorization_ref
        and effect_fence.effect_authorization_digest
        == binding.effect_authorization_digest
        and effect_fence.effect_ceilings == binding.effect_ceilings
        and effect_fence.expires_at == binding.expires_at
        and effect_fence.path_ceiling == binding.path_ceiling
    ):
        raise _database_integrity_failure() from None
    validate_delivery_relation(
        delivery=delivery,
        author_command=worker_command,
        attempt_fence=attempt_fence,
        author_effect_fence=effect_fence,
        effect_fence=effect_fence,
    )
    return {
        "schema_id": _COMMAND_SCHEMA,
        "mutation_ref": refs[0],
        "program_ref": refs[1],
        "program_version_ref": refs[2],
        "program_version_number": version_number,
        "accepted_intent_revision_ref": refs[3],
        "work_item_ref": refs[4],
        "work_item_revision_ref": refs[5],
        "basis_decision_ref": refs[6],
        "basis_decision_digest": basis_digest,
        "semantic_attempt_ref": refs[7],
        "candidate_ref": refs[8],
        "attempt_number": attempt_number,
        "attempt_fence_ref": refs[9],
        "effect_intent_ref": refs[10],
        "effect_fence_ref": refs[11],
        "command_ref": refs[12],
        "authority_evaluation_ref": refs[13],
        "delivery_attempt_ref": refs[14],
        "adapter_safe_correlation_ref": refs[15],
        "coding_global_stop_ref": refs[16],
        "coding_global_stop_version": stop_version,
        "capsule_schema_id": _CAPSULE_SCHEMA,
        "capsule_profile_ref": _CAPSULE_PROFILE,
        "privacy_classification": _PRIVACY_CLASSIFICATION,
        "redaction_profile_ref": _REDACTION_PROFILE,
        "work_spec_safe_projection": _safe_projection_mapping(projection),
        "validation_requirement_evidence": _requirement_mapping(validation),
        "review_requirement_evidence": _requirement_mapping(review),
        "attempt_fence": attempt_fence.to_mapping(),
        "effect_authorization_safe_binding": _binding_mapping(binding),
        "worker_command": worker_command.to_mapping(),
        "effect_fence": effect_fence.to_mapping(),
        "delivery_envelope": delivery.to_mapping(),
    }


def _development_author_effect_establishment_command(
    **fields: object,
) -> DevelopmentAuthorEffectEstablishmentCommandV1:
    provisional = object.__new__(DevelopmentAuthorEffectEstablishmentCommandV1)
    try:
        expected = tuple(
            name
            for name in DevelopmentAuthorEffectEstablishmentCommandV1.__dataclass_fields__
            if name != "command_digest"
        )
        if tuple(fields) != expected:
            raise _database_integrity_failure() from None
        for name in expected:
            object.__setattr__(provisional, name, fields[name])
        object.__setattr__(provisional, "command_digest", "0" * 64)
        identity = _author_effect_command_identity(provisional)
        return DevelopmentAuthorEffectEstablishmentCommandV1(
            **fields,
            command_digest=_domain_separated_digest(_COMMAND_DOMAIN, identity),
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        fields.clear()
        provisional = None


def _require_exact_development_author_effect_establishment_command(
    value: object,
) -> DevelopmentAuthorEffectEstablishmentCommandV1:
    if type(value) is not DevelopmentAuthorEffectEstablishmentCommandV1:
        raise _database_integrity_failure() from None
    fields: dict[str, object] = {}
    try:
        for name in DevelopmentAuthorEffectEstablishmentCommandV1.__dataclass_fields__:
            fields[name] = object.__getattribute__(value, name)
        return DevelopmentAuthorEffectEstablishmentCommandV1(**fields)
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        fields.clear()
        value = None


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentAuthorEffectEstablishmentResultV1:
    disposition: str
    mutation_ref: str
    command_digest: str
    program_ref: str
    program_version_ref: str
    accepted_intent_revision_ref: str
    decision_ref: str
    work_item_ref: str
    work_item_revision_ref: str
    work_spec_ref: str
    semantic_attempt_ref: str
    candidate_ref: str
    effect_intent_ref: str
    effect_fence_ref: str
    delivery_attempt_ref: str
    transaction_timestamp: str

    def __post_init__(self) -> None:
        try:
            if type(self.disposition) is not str or self.disposition not in (
                "committed",
                "exact_replay",
            ):
                raise _RowValueValidationError() from None
            for name in (
                "mutation_ref",
                "program_ref",
                "program_version_ref",
                "accepted_intent_revision_ref",
                "decision_ref",
                "work_item_ref",
                "work_item_revision_ref",
                "work_spec_ref",
                "semantic_attempt_ref",
                "candidate_ref",
                "effect_intent_ref",
                "effect_fence_ref",
                "delivery_attempt_ref",
            ):
                _require_safe_ref(getattr(self, name))
            _require_sha256(self.command_digest)
            _require_utc_timestamp(self.transaction_timestamp)
        except _RowValueValidationError:
            raise _database_integrity_failure() from None

    def identity_mapping(self) -> dict[str, object]:
        return {
            "disposition": self.disposition,
            "mutation_ref": self.mutation_ref,
            "command_digest": self.command_digest,
            "program_ref": self.program_ref,
            "program_version_ref": self.program_version_ref,
            "accepted_intent_revision_ref": self.accepted_intent_revision_ref,
            "decision_ref": self.decision_ref,
            "work_item_ref": self.work_item_ref,
            "work_item_revision_ref": self.work_item_revision_ref,
            "work_spec_ref": self.work_spec_ref,
            "semantic_attempt_ref": self.semantic_attempt_ref,
            "candidate_ref": self.candidate_ref,
            "effect_intent_ref": self.effect_intent_ref,
            "effect_fence_ref": self.effect_fence_ref,
            "delivery_attempt_ref": self.delivery_attempt_ref,
            "transaction_timestamp": self.transaction_timestamp,
        }

    def computed_digest(self) -> str:
        return _domain_separated_digest(_RESULT_DOMAIN, self.identity_mapping())

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentAuthorEffectEstablishmentConflictV1:
    reason: DevelopmentAuthorEffectEstablishmentConflictReasonV1
    mutation_ref: str
    command_digest: str
    program_ref: str

    def __post_init__(self) -> None:
        try:
            if (
                type(self.reason)
                is not DevelopmentAuthorEffectEstablishmentConflictReasonV1
            ):
                raise _RowValueValidationError() from None
            _require_safe_ref(self.mutation_ref)
            _require_sha256(self.command_digest)
            _require_safe_ref(self.program_ref)
        except _RowValueValidationError:
            raise _database_integrity_failure() from None

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentAuthorEffectEstablishmentRecoveryResultV1:
    disposition: DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1
    committed_result: DevelopmentAuthorEffectEstablishmentResultV1 | None = field(
        default=None, repr=False
    )

    def __post_init__(self) -> None:
        if (
            type(self.disposition)
            is not DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1
        ):
            raise _database_integrity_failure() from None
        if (
            self.disposition
            is DevelopmentAuthorEffectEstablishmentRecoveryDispositionV1.COMMITTED_EXACT
        ):
            if (
                type(self.committed_result)
                is not DevelopmentAuthorEffectEstablishmentResultV1
                or self.committed_result.disposition != "exact_replay"
            ):
                raise _database_integrity_failure() from None
        elif self.committed_result is not None:
            raise _database_integrity_failure() from None

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


@dataclass(frozen=True, slots=True, repr=False)
class _DevelopmentAuthorEffectEstablishmentWritePlan:
    semantic_attempt: _program_rows.DevelopmentSemanticAttemptRowValue
    attempt_fence: _effect_rows.DevelopmentAttemptFenceRowValue
    effect_intent: _effect_rows.DevelopmentEffectIntentRowValue
    effect_fence: _effect_rows.DevelopmentEffectFenceRowValue
    author_command: _effect_rows.DevelopmentAuthorCommandRowValue
    authority_evaluation: _effect_rows.DevelopmentAuthorityEvaluationRowValue
    effect_head: _effect_rows.DevelopmentEffectHeadRowValue
    delivery_attempt: _effect_rows.DevelopmentDeliveryAttemptRowValue
    delivery_head: _effect_rows.DevelopmentDeliveryHeadRowValue
    mutation_receipt: _decision_rows.DevelopmentMutationReceiptRowValue
    graph_entries: tuple[_decision_rows.DevelopmentMutationGraphEntry, ...]
    planned_result: DevelopmentAuthorEffectEstablishmentResultV1

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle


def _row_with_digest(
    *,
    fields: dict[str, object],
    domain: str,
    digest_field: str,
    adapter: typing.Callable[[object], object],
) -> typing.Any:
    identity = dict(fields)
    fields[digest_field] = _domain_separated_digest(domain, identity)
    return adapter(tuple(fields.values()))


def _development_author_effect_establishment_write_plan(
    command: object,
    transaction_timestamp: object,
) -> _DevelopmentAuthorEffectEstablishmentWritePlan:
    checked = _require_exact_development_author_effect_establishment_command(command)
    try:
        timestamp = _require_utc_timestamp(transaction_timestamp)
        semantic_attempt = _row_with_digest(
            fields={
                "schema_id": "governed-execution.nwp-development-semantic-attempt.v1",
                "semantic_attempt_ref": checked.semantic_attempt_ref,
                "program_ref": checked.program_ref,
                "program_version_ref": checked.program_version_ref,
                "accepted_intent_revision_ref": checked.accepted_intent_revision_ref,
                "work_item_ref": checked.work_item_ref,
                "work_item_revision_ref": checked.work_item_revision_ref,
                "attempt_number": checked.attempt_number,
                "candidate_ref": checked.candidate_ref,
                "attempt_phase": "established",
                "selection_decision_ref": checked.basis_decision_ref,
                "created_at": timestamp,
            },
            domain="governed-execution.nwp-development-semantic-attempt.v1.identity",
            digest_field="semantic_attempt_digest",
            adapter=_program_rows.development_semantic_attempt_row_value_from_row_tuple,
        )
        attempt_fence = _effect_rows.development_attempt_fence_row_value_from_row_tuple(
            _attempt_fence_parameters(checked.attempt_fence, timestamp)
        )
        effect_intent = _row_with_digest(
            fields={
                "schema_id": "governed-execution.nwp-development-effect-intent.v1",
                "effect_intent_ref": checked.effect_intent_ref,
                "program_ref": checked.program_ref,
                "program_version_ref": checked.program_version_ref,
                "semantic_attempt_ref": checked.semantic_attempt_ref,
                "effect_class": "author_candidate",
                "candidate_ref": checked.candidate_ref,
                "command_ref": checked.command_ref,
                "basis_decision_ref": checked.basis_decision_ref,
                "cancellation_target_effect_intent_ref": None,
                "expected_target_effect_head_revision": None,
                "portable_capsule_digest": None,
                "created_at": timestamp,
            },
            domain="governed-execution.nwp-development-effect-intent.v1.identity",
            digest_field="effect_intent_digest",
            adapter=_effect_rows.development_effect_intent_row_value_from_row_tuple,
        )
        effect_fence = _effect_rows.development_effect_fence_row_value_from_row_tuple(
            _effect_fence_parameters(checked.effect_fence, timestamp)
        )
        author_command = (
            _effect_rows.development_author_command_row_value_from_row_tuple(
                _author_command_parameters(checked.worker_command, timestamp)
            )
        )
        authority_evaluation = _row_with_digest(
            fields={
                "schema_id": "governed-execution.nwp-development-authority-evaluation.v1",
                "authority_evaluation_ref": checked.authority_evaluation_ref,
                "program_ref": checked.program_ref,
                "evaluation_scope": "effect",
                "evaluation_subject_ref": checked.effect_intent_ref,
                "semantic_attempt_ref": None,
                "effect_intent_ref": checked.effect_intent_ref,
                "authority_ref": checked.effect_authorization_safe_binding.effect_authorization_ref,
                "authority_digest": checked.effect_authorization_safe_binding.effect_authorization_digest,
                "authority_state": "pending",
                "reason_code": "external_verification_pending",
                "expires_at": None,
                "evaluated_at": timestamp,
            },
            domain="governed-execution.nwp-development-authority-evaluation.v1.identity",
            digest_field="authority_evaluation_digest",
            adapter=_effect_rows.development_authority_evaluation_row_value_from_row_tuple,
        )
        effect_head = _row_with_digest(
            fields={
                "schema_id": "governed-execution.nwp-development-effect-head.v1",
                "effect_intent_ref": checked.effect_intent_ref,
                "program_ref": checked.program_ref,
                "current_effect_fence_ref": checked.effect_fence_ref,
                "head_revision": 0,
                "effect_state": "ready_for_delivery",
                "cancellation_effect_intent_ref": None,
                "updated_at": timestamp,
            },
            domain="governed-execution.nwp-development-effect-head.v1.identity",
            digest_field="head_digest",
            adapter=_effect_rows.development_effect_head_row_value_from_row_tuple,
        )
        delivery_attempt = (
            _effect_rows.development_delivery_attempt_row_value_from_row_tuple(
                _delivery_attempt_parameters(
                    checked.delivery_envelope,
                    basis_decision_ref=checked.basis_decision_ref,
                    timestamp=timestamp,
                )
            )
        )
        delivery_head = _row_with_digest(
            fields={
                "schema_id": "governed-execution.nwp-development-delivery-head.v1",
                "effect_intent_ref": checked.effect_intent_ref,
                "program_ref": checked.program_ref,
                "current_delivery_attempt_ref": checked.delivery_attempt_ref,
                "head_revision": 0,
                "delivery_state": "planned",
                "updated_at": timestamp,
            },
            domain="governed-execution.nwp-development-delivery-head.v1.identity",
            digest_field="head_digest",
            adapter=_effect_rows.development_delivery_head_row_value_from_row_tuple,
        )
        projection_identity = {
            "schema_id": _RECEIPT_RESULT_SCHEMA,
            "program_ref": checked.program_ref,
            "decision_ref": checked.basis_decision_ref,
            "result_program_version_ref": checked.program_version_ref,
            "result_semantic_attempt_ref": checked.semantic_attempt_ref,
            "result_effect_intent_ref": checked.effect_intent_ref,
            "result_effect_fence_ref": checked.effect_fence_ref,
            "result_delivery_attempt_ref": checked.delivery_attempt_ref,
        }
        projection_digest = _domain_separated_digest(
            _RECEIPT_RESULT_DOMAIN, projection_identity
        )
        provisional_receipt = _receipt_row(
            checked,
            timestamp,
            result_projection_digest=projection_digest,
            mutation_graph_digest="0" * 64,
        )
        graph_entries = (
            _decision_rows.development_mutation_graph_entry(
                role="semantic_attempt",
                ordinal=0,
                record_ref=semantic_attempt.semantic_attempt_ref,
                record_digest=semantic_attempt.semantic_attempt_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="attempt_fence",
                ordinal=0,
                record_ref=attempt_fence.attempt_fence_ref,
                record_digest=attempt_fence.attempt_fence_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="author_effect_intent",
                ordinal=0,
                record_ref=effect_intent.effect_intent_ref,
                record_digest=effect_intent.effect_intent_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="author_effect_fence",
                ordinal=0,
                record_ref=effect_fence.effect_fence_ref,
                record_digest=effect_fence.effect_fence_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="author_command",
                ordinal=0,
                record_ref=author_command.command_ref,
                record_digest=author_command.command_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="authority_evaluation",
                ordinal=0,
                record_ref=authority_evaluation.authority_evaluation_ref,
                record_digest=authority_evaluation.authority_evaluation_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="initial_delivery_attempt",
                ordinal=0,
                record_ref=delivery_attempt.delivery_attempt_ref,
                record_digest=delivery_attempt.delivery_attempt_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="effect_head_postimage",
                ordinal=0,
                record_ref=effect_head.effect_intent_ref,
                record_digest=effect_head.head_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="delivery_head_postimage",
                ordinal=0,
                record_ref=delivery_head.effect_intent_ref,
                record_digest=delivery_head.head_digest,
            ),
        )
        graph_digest = _decision_rows.compute_development_mutation_graph_digest(
            receipt=provisional_receipt, graph_entries=graph_entries
        )
        receipt = _receipt_row(
            checked,
            timestamp,
            result_projection_digest=projection_digest,
            mutation_graph_digest=graph_digest,
        )
        _decision_rows.require_development_mutation_graph_digest_matches_supplied_entries(
            receipt=receipt, graph_entries=graph_entries
        )
        result = _author_effect_result(checked, timestamp, "committed")
        return _DevelopmentAuthorEffectEstablishmentWritePlan(
            semantic_attempt=semantic_attempt,
            attempt_fence=attempt_fence,
            effect_intent=effect_intent,
            effect_fence=effect_fence,
            author_command=author_command,
            authority_evaluation=authority_evaluation,
            effect_head=effect_head,
            delivery_attempt=delivery_attempt,
            delivery_head=delivery_head,
            mutation_receipt=receipt,
            graph_entries=graph_entries,
            planned_result=result,
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        command = None
        checked = None
        transaction_timestamp = None


def _attempt_fence_parameters(
    value: AttemptFenceV1, timestamp: str
) -> tuple[object, ...]:
    mapping = value.to_mapping()
    ceilings = value.aggregate_ceilings
    return (
        value.schema_id,
        value.attempt_fence_ref,
        value.parent_standing_grant_ref,
        value.parent_standing_grant_digest,
        value.attempt_authorization_ref,
        value.attempt_authorization_digest,
        value.program_ref,
        value.program_version_ref,
        value.accepted_intent_revision_ref,
        value.work_item_ref,
        value.work_item_revision_ref,
        value.semantic_attempt_ref,
        value.repository_ref,
        value.base_git_object_format,
        value.base_git_oid,
        json.dumps(mapping["path_ceiling"], separators=(",", ":")),
        _encode_effect_class_mask(value.allowed_effect_classes),
        *(
            getattr(ceilings, name)
            for name in (
                "max_active_invocations",
                "max_candidate_bytes",
                "max_changed_files",
                "max_cost_microusd",
                "max_cpu_seconds",
                "max_deliveries",
                "max_deployments",
                "max_local_commits",
                "max_memory_bytes",
                "max_merges",
                "max_model_input_tokens",
                "max_model_output_tokens",
                "max_pull_requests",
                "max_pushes",
                "max_wall_seconds",
            )
        ),
        value.expires_at,
        value.global_stop_ref,
        value.global_stop_version,
        value.attempt_fence_digest,
        timestamp,
    )


def _effect_fence_parameters(
    value: EffectFenceV1, timestamp: str
) -> tuple[object, ...]:
    ceilings = value.effect_ceilings
    return (
        value.schema_id,
        value.effect_fence_ref,
        value.parent_standing_grant_ref,
        value.parent_standing_grant_digest,
        value.effect_authorization_ref,
        value.effect_authorization_digest,
        value.attempt_fence_ref,
        value.attempt_fence_digest,
        value.program_ref,
        value.program_version_ref,
        value.accepted_intent_revision_ref,
        value.work_item_ref,
        value.work_item_revision_ref,
        value.semantic_attempt_ref,
        value.effect_intent_ref,
        value.effect_class,
        value.command_ref,
        value.command_digest,
        value.candidate_ref,
        value.repository_ref,
        value.base_git_object_format,
        value.base_git_oid,
        json.dumps(list(value.path_ceiling), separators=(",", ":")),
        *(
            getattr(ceilings, name)
            for name in (
                "max_active_invocations",
                "max_candidate_bytes",
                "max_changed_files",
                "max_cost_microusd",
                "max_cpu_seconds",
                "max_deliveries",
                "max_deployments",
                "max_local_commits",
                "max_memory_bytes",
                "max_merges",
                "max_model_input_tokens",
                "max_model_output_tokens",
                "max_pull_requests",
                "max_pushes",
                "max_wall_seconds",
            )
        ),
        value.expires_at,
        value.global_stop_ref,
        value.global_stop_version,
        value.portable_capsule_digest,
        value.cancellation_target_effect_intent_ref,
        value.cancellation_target_effect_fence_ref,
        value.cancellation_target_effect_fence_digest,
        value.effect_fence_digest,
        timestamp,
    )


def _author_command_parameters(
    value: WorkerCommandV1, timestamp: str
) -> tuple[object, ...]:
    ceilings = value.effect_ceilings
    return (
        value.schema_id,
        value.command_ref,
        value.program_ref,
        value.program_version_ref,
        value.accepted_intent_revision_ref,
        value.work_item_ref,
        value.work_item_revision_ref,
        value.semantic_attempt_ref,
        value.effect_intent_ref,
        value.effect_class,
        value.candidate_ref,
        value.repository_ref,
        value.base_git_object_format,
        value.base_git_oid,
        json.dumps(list(value.path_ceiling), separators=(",", ":")),
        value.work_spec_ref,
        value.work_spec_digest,
        value.standing_grant_ref,
        value.standing_grant_digest,
        value.attempt_authorization_ref,
        value.attempt_authorization_digest,
        value.effect_authorization_ref,
        value.effect_authorization_digest,
        value.attempt_fence_ref,
        value.attempt_fence_digest,
        value.effect_fence_ref,
        value.effect_fence_digest,
        value.global_stop_ref,
        value.global_stop_version,
        value.validation_requirement_ref,
        value.validation_requirement_digest,
        value.review_requirement_ref,
        value.review_requirement_digest,
        value.capsule_schema_id,
        value.capsule_profile_ref,
        *(
            getattr(ceilings, name)
            for name in (
                "max_active_invocations",
                "max_candidate_bytes",
                "max_changed_files",
                "max_cost_microusd",
                "max_cpu_seconds",
                "max_deliveries",
                "max_deployments",
                "max_local_commits",
                "max_memory_bytes",
                "max_merges",
                "max_model_input_tokens",
                "max_model_output_tokens",
                "max_pull_requests",
                "max_pushes",
                "max_wall_seconds",
            )
        ),
        value.privacy_classification,
        value.redaction_profile_ref,
        value.command_digest,
        timestamp,
    )


def _delivery_attempt_parameters(
    value: DeliveryEnvelopeV1,
    *,
    basis_decision_ref: str,
    timestamp: str,
) -> tuple[object, ...]:
    identity = {
        "schema_id": "governed-execution.nwp-development-delivery-attempt.v1",
        "delivery_envelope_digest": value.delivery_envelope_digest,
        "delivery_kind": "initial",
        "delivery_number": 1,
        "predecessor_delivery_attempt_ref": None,
        "basis_decision_ref": basis_decision_ref,
        "recorded_at": timestamp,
    }
    wrapper_digest = _domain_separated_digest(
        "governed-execution.nwp-development-delivery-attempt.v1.identity",
        identity,
    )
    return tuple(value.to_mapping().values()) + (
        "initial",
        1,
        None,
        basis_decision_ref,
        timestamp,
        wrapper_digest,
    )


def _receipt_row(
    command: DevelopmentAuthorEffectEstablishmentCommandV1,
    timestamp: str,
    *,
    result_projection_digest: str,
    mutation_graph_digest: str,
) -> _decision_rows.DevelopmentMutationReceiptRowValue:
    return _decision_rows.development_mutation_receipt_row_value_from_row_tuple(
        (
            "governed-execution.nwp-development-mutation-receipt.v1",
            command.mutation_ref,
            _MUTATION_FAMILY,
            _COMMAND_SCHEMA,
            command.command_digest,
            command.program_ref,
            command.basis_decision_ref,
            command.program_version_ref,
            command.semantic_attempt_ref,
            command.effect_intent_ref,
            command.effect_fence_ref,
            command.delivery_attempt_ref,
            None,
            None,
            "development_author_effect_intent_established",
            result_projection_digest,
            mutation_graph_digest,
            "committed",
            timestamp,
        )
    )


def _author_effect_result(
    command: DevelopmentAuthorEffectEstablishmentCommandV1,
    timestamp: str,
    disposition: str,
) -> DevelopmentAuthorEffectEstablishmentResultV1:
    return DevelopmentAuthorEffectEstablishmentResultV1(
        disposition=disposition,
        mutation_ref=command.mutation_ref,
        command_digest=command.command_digest,
        program_ref=command.program_ref,
        program_version_ref=command.program_version_ref,
        accepted_intent_revision_ref=command.accepted_intent_revision_ref,
        decision_ref=command.basis_decision_ref,
        work_item_ref=command.work_item_ref,
        work_item_revision_ref=command.work_item_revision_ref,
        work_spec_ref=command.work_spec_safe_projection.work_spec_ref,
        semantic_attempt_ref=command.semantic_attempt_ref,
        candidate_ref=command.candidate_ref,
        effect_intent_ref=command.effect_intent_ref,
        effect_fence_ref=command.effect_fence_ref,
        delivery_attempt_ref=command.delivery_attempt_ref,
        transaction_timestamp=timestamp,
    )


def _author_effect_conflict(
    command: DevelopmentAuthorEffectEstablishmentCommandV1,
    reason: DevelopmentAuthorEffectEstablishmentConflictReasonV1,
) -> DevelopmentAuthorEffectEstablishmentConflictV1:
    return DevelopmentAuthorEffectEstablishmentConflictV1(
        reason=reason,
        mutation_ref=command.mutation_ref,
        command_digest=command.command_digest,
        program_ref=command.program_ref,
    )


def _database_integrity_failure() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(
        SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
    )
