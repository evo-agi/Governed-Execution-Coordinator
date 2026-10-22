"""Private no-I/O command and result for one candidate-bound checking effect.

The command retains immutable transient capsule bytes for exact revalidation.
Its digest contains only canonical byte bindings. Neither the command nor its
result confers executable external authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
import hashlib
import typing

from ._development_author_effect_establishment_contracts import (
    DevelopmentAuthorEffectEstablishmentCommandV1,
    DevelopmentReviewRequirementEvidenceV1,
    DevelopmentValidationRequirementEvidenceV1,
    _delivery_attempt_parameters,
    _effect_fence_parameters,
    _require_exact_review_evidence,
    _require_exact_validation_evidence,
    _row_with_digest,
)
from . import _development_decision_row_values as _decision_rows
from . import _development_effect_row_values as _effect_rows
from . import _development_program_row_values as _program_rows
from ._development_pre_execution_plan_disposition_contracts import (
    PreExecutionPlanDispositionResultV1,
)
from ._development_row_value_support import (
    _RowValueValidationError,
    _domain_separated_digest,
    _require_fixed_paths,
    _require_nonnegative_integer,
    _require_safe_ref,
    _require_sha256,
    _require_utc_timestamp,
)
from ._worker_execution_semantic_values import (
    CandidateCapsuleManifestV1, CeilingsV1, DeliveryEnvelopeV1, EffectFenceV1,
    WorkSpecV1, WorkerExecutionValueError, create_effect_fence,
    validate_capsule_manifest_relation, validate_delivery_relation,
)
from ._rw0_d1_workspace import D1CandidateCapture
from ._rw0_phase_entry_semantic_values import RW0PhaseEntryBasisV1


__all__: tuple[str, ...] = ()

_COMMAND_SCHEMA = "governed-execution.nwp-establish-development-bound-effect-intent-command.v1"
_COMMAND_DOMAIN = _COMMAND_SCHEMA + ".identity"
_RESULT_SCHEMA = "governed-execution.nwp-development-bound-effect-establishment-result.v1"
_RESULT_DOMAIN = _RESULT_SCHEMA + ".identity"
_RECEIPT_RESULT_SCHEMA = "governed-execution.nwp-establish-development-bound-effect-intent-result.v1"
_RECEIPT_RESULT_DOMAIN = _RECEIPT_RESULT_SCHEMA + ".identity"
_EFFECT_CLASSES = frozenset({"validate_candidate", "review_candidate"})
_BOUND_BINDING_SCHEMA = (
    "governed-execution.nwp-development-bound-effect-authorization-safe-binding.v1"
)
_BOUND_BINDING_DOMAIN = _BOUND_BINDING_SCHEMA + ".identity"
_BOUND_BINDING_FIELDS = (
    "schema_id", "parent_standing_grant_ref", "parent_standing_grant_digest",
    "effect_authorization_ref", "effect_authorization_digest",
    "attempt_fence_ref", "attempt_fence_digest", "semantic_attempt_ref",
    "effect_intent_ref", "effect_class", "path_ceiling", "effect_ceilings",
    "expires_at", "global_stop_ref", "global_stop_version",
    "safe_binding_digest",
)
_SCALAR_REFS = (
    "mutation_ref", "program_ref", "program_version_ref",
    "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref",
    "basis_decision_ref", "semantic_attempt_ref", "candidate_ref",
    "attempt_fence_ref", "originating_command_ref", "author_effect_fence_ref",
    "selected_disposition_ref", "phase_basis_ref", "capsule_manifest_ref",
    "requirement_ref", "effect_intent_ref", "effect_fence_ref",
    "authority_evaluation_ref", "delivery_attempt_ref",
    "adapter_safe_correlation_ref",
)
_SCALAR_DIGESTS = (
    "basis_decision_digest", "attempt_fence_digest",
    "originating_command_digest", "author_effect_fence_digest",
    "selected_disposition_digest", "phase_basis_digest",
    "portable_capsule_digest", "requirement_safe_digest",
)


def _invalid() -> typing.NoReturn:
    raise ValueError("invalid_development_bound_effect_command")


def _safe_display(self: object) -> str:
    return f"<{type(self).__name__}>"


def _no_pickle(self: object, protocol: object = None) -> typing.NoReturn:
    raise TypeError("serialization disabled")


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentBoundEffectAuthorizationSafeBindingV1:
    """A local canonical assertion for one artificial checking-effect source."""

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
        self.validate()

    def validate(self) -> None:
        if type(self) is not DevelopmentBoundEffectAuthorizationSafeBindingV1:
            _invalid()
        identity = self.identity_mapping()
        try:
            if _require_sha256(self.safe_binding_digest) != _domain_separated_digest(
                _BOUND_BINDING_DOMAIN, identity
            ):
                _invalid()
        except (_RowValueValidationError, ValueError, TypeError, AttributeError):
            _invalid()

    def identity_mapping(self) -> dict[str, object]:
        if type(self) is not DevelopmentBoundEffectAuthorizationSafeBindingV1:
            _invalid()
        try:
            if type(self.schema_id) is not str or self.schema_id != _BOUND_BINDING_SCHEMA:
                _invalid()
            if type(self.effect_class) is not str or self.effect_class not in _EFFECT_CLASSES:
                _invalid()
            if type(self.effect_ceilings) is not CeilingsV1:
                _invalid()
            ceilings = CeilingsV1.from_mapping(self.effect_ceilings.to_mapping())
            return {
                "schema_id": self.schema_id,
                "parent_standing_grant_ref": _require_safe_ref(self.parent_standing_grant_ref),
                "parent_standing_grant_digest": _require_sha256(self.parent_standing_grant_digest),
                "effect_authorization_ref": _require_safe_ref(self.effect_authorization_ref),
                "effect_authorization_digest": _require_sha256(self.effect_authorization_digest),
                "attempt_fence_ref": _require_safe_ref(self.attempt_fence_ref),
                "attempt_fence_digest": _require_sha256(self.attempt_fence_digest),
                "semantic_attempt_ref": _require_safe_ref(self.semantic_attempt_ref),
                "effect_intent_ref": _require_safe_ref(self.effect_intent_ref),
                "effect_class": self.effect_class,
                "path_ceiling": _require_fixed_paths(self.path_ceiling),
                "effect_ceilings": ceilings.to_mapping(),
                "expires_at": _require_utc_timestamp(self.expires_at),
                "global_stop_ref": _require_safe_ref(self.global_stop_ref),
                "global_stop_version": _require_nonnegative_integer(self.global_stop_version),
            }
        except (_RowValueValidationError, WorkerExecutionValueError,
                ValueError, TypeError, AttributeError):
            _invalid()

    def computed_digest(self) -> str:
        return _domain_separated_digest(_BOUND_BINDING_DOMAIN, self.identity_mapping())

    __repr__ = _safe_display
    __str__ = _safe_display
    __reduce__ = _no_pickle
    __reduce_ex__ = _no_pickle

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


def _development_bound_effect_authorization_safe_binding(
    *, parent_standing_grant_ref: object, parent_standing_grant_digest: object,
    effect_authorization_ref: object, effect_authorization_digest: object,
    attempt_fence_ref: object, attempt_fence_digest: object,
    semantic_attempt_ref: object, effect_intent_ref: object, effect_class: object,
    path_ceiling: object, effect_ceilings: object, expires_at: object,
    global_stop_ref: object, global_stop_version: object,
) -> DevelopmentBoundEffectAuthorizationSafeBindingV1:
    values = dict(zip(_BOUND_BINDING_FIELDS[:-1], (
        _BOUND_BINDING_SCHEMA, parent_standing_grant_ref, parent_standing_grant_digest,
        effect_authorization_ref, effect_authorization_digest, attempt_fence_ref,
        attempt_fence_digest, semantic_attempt_ref, effect_intent_ref, effect_class,
        path_ceiling, effect_ceilings, expires_at, global_stop_ref,
        global_stop_version,
    ), strict=True))
    provisional = object.__new__(DevelopmentBoundEffectAuthorizationSafeBindingV1)
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    identity = provisional.identity_mapping()
    values["effect_ceilings"] = CeilingsV1.from_mapping(identity["effect_ceilings"])
    return DevelopmentBoundEffectAuthorizationSafeBindingV1(
        **values, safe_binding_digest=_domain_separated_digest(
            _BOUND_BINDING_DOMAIN, identity
        ),
    )


def _require_exact_bound_effect_authorization_safe_binding(
    value: object,
) -> DevelopmentBoundEffectAuthorizationSafeBindingV1:
    if type(value) is not DevelopmentBoundEffectAuthorizationSafeBindingV1:
        _invalid()
    try:
        return DevelopmentBoundEffectAuthorizationSafeBindingV1(**{
            name: object.__getattribute__(value, name) for name in _BOUND_BINDING_FIELDS
        })
    except (ValueError, TypeError, AttributeError, _RowValueValidationError,
            WorkerExecutionValueError):
        _invalid()


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentBoundEffectEstablishmentCommandV1:
    schema_id: str
    mutation_ref: str
    effect_class: str
    program_ref: str
    program_version_ref: str
    accepted_intent_revision_ref: str
    work_item_ref: str
    work_item_revision_ref: str
    basis_decision_ref: str
    basis_decision_digest: str
    semantic_attempt_ref: str
    candidate_ref: str
    attempt_fence_ref: str
    attempt_fence_digest: str
    originating_command_ref: str
    originating_command_digest: str
    author_effect_fence_ref: str
    author_effect_fence_digest: str
    selected_disposition_ref: str
    selected_disposition_digest: str
    phase_basis_ref: str
    phase_basis_digest: str
    capsule_manifest_ref: str
    portable_capsule_digest: str
    requirement_ref: str
    requirement_safe_digest: str
    effect_intent_ref: str
    effect_fence_ref: str
    authority_evaluation_ref: str
    delivery_attempt_ref: str
    adapter_safe_correlation_ref: str
    effect_authorization_safe_binding: DevelopmentBoundEffectAuthorizationSafeBindingV1 = field(repr=False)
    capsule_manifest: CandidateCapsuleManifestV1 = field(repr=False)
    requirement_evidence: DevelopmentValidationRequirementEvidenceV1 | DevelopmentReviewRequirementEvidenceV1 = field(repr=False)
    before_blob_entries: tuple[tuple[str, bytes], ...] = field(repr=False)
    after_blob_entries: tuple[tuple[str, bytes], ...] = field(repr=False)
    effect_fence: EffectFenceV1 = field(repr=False)
    delivery_envelope: DeliveryEnvelopeV1 = field(repr=False)
    command_digest: str

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if type(self) is not DevelopmentBoundEffectEstablishmentCommandV1:
            _invalid()
        try:
            identity = self.identity_mapping()
            if (_require_sha256(self.command_digest)
                    != _domain_separated_digest(_COMMAND_DOMAIN, identity)):
                _invalid()
        except (ValueError, TypeError, AttributeError, _RowValueValidationError,
                WorkerExecutionValueError):
            _invalid()

    def identity_mapping(self) -> dict[str, object]:
        if type(self.schema_id) is not str or self.schema_id != _COMMAND_SCHEMA:
            _invalid()
        if type(self.effect_class) is not str or self.effect_class not in _EFFECT_CLASSES:
            _invalid()
        try:
            for name in _SCALAR_REFS:
                _require_safe_ref(object.__getattribute__(self, name))
            for name in _SCALAR_DIGESTS:
                _require_sha256(object.__getattribute__(self, name))
            binding = _require_exact_bound_effect_authorization_safe_binding(
                self.effect_authorization_safe_binding
            )
            requirement = (
                _require_exact_validation_evidence(self.requirement_evidence)
                if self.effect_class == "validate_candidate"
                else _require_exact_review_evidence(self.requirement_evidence)
            )
            manifest = self.capsule_manifest
            fence = self.effect_fence
            delivery = self.delivery_envelope
            if (type(manifest) is not CandidateCapsuleManifestV1
                    or type(fence) is not EffectFenceV1
                    or type(delivery) is not DeliveryEnvelopeV1):
                _invalid()
            manifest = CandidateCapsuleManifestV1.from_mapping(manifest.to_mapping())
            fence = EffectFenceV1.from_mapping(fence.to_mapping())
            delivery = DeliveryEnvelopeV1.from_mapping(delivery.to_mapping())
            if (manifest.capsule_manifest_ref != self.capsule_manifest_ref
                    or manifest.portable_capsule_digest != self.portable_capsule_digest
                    or manifest.program_ref != self.program_ref
                    or manifest.program_version_ref != self.program_version_ref
                    or manifest.accepted_intent_revision_ref != self.accepted_intent_revision_ref
                    or manifest.work_item_ref != self.work_item_ref
                    or manifest.work_item_revision_ref != self.work_item_revision_ref
                    or manifest.semantic_attempt_ref != self.semantic_attempt_ref
                    or manifest.candidate_ref != self.candidate_ref
                    or manifest.command_ref != self.originating_command_ref
                    or manifest.command_digest != self.originating_command_digest
                    or manifest.attempt_fence_ref != self.attempt_fence_ref
                    or manifest.attempt_fence_digest != self.attempt_fence_digest
                    or manifest.effect_fence_ref != self.author_effect_fence_ref
                    or manifest.effect_fence_digest != self.author_effect_fence_digest
                    or requirement.requirement_ref != self.requirement_ref
                    or requirement.safe_evidence_digest != self.requirement_safe_digest
                    or binding.effect_class != self.effect_class
                    or binding.effect_intent_ref != self.effect_intent_ref
                    or binding.semantic_attempt_ref != self.semantic_attempt_ref
                    or binding.global_stop_ref != fence.global_stop_ref
                    or binding.global_stop_version != fence.global_stop_version
                    or binding.parent_standing_grant_ref != fence.parent_standing_grant_ref
                    or binding.parent_standing_grant_digest != fence.parent_standing_grant_digest
                    or binding.path_ceiling != fence.path_ceiling
                    or binding.effect_ceilings.to_mapping() != fence.effect_ceilings.to_mapping()
                    or binding.expires_at != fence.expires_at
                    or binding.attempt_fence_ref != self.attempt_fence_ref
                    or binding.attempt_fence_digest != self.attempt_fence_digest
                    or fence.effect_class != self.effect_class
                    or fence.effect_intent_ref != self.effect_intent_ref
                    or fence.effect_fence_ref != self.effect_fence_ref
                    or fence.effect_authorization_ref != binding.effect_authorization_ref
                    or fence.effect_authorization_digest != binding.effect_authorization_digest
                    or fence.portable_capsule_digest != self.portable_capsule_digest
                    or fence.attempt_fence_ref != self.attempt_fence_ref
                    or fence.attempt_fence_digest != self.attempt_fence_digest
                    or fence.command_ref != self.originating_command_ref
                    or fence.command_digest != self.originating_command_digest
                    or delivery.effect_intent_ref != self.effect_intent_ref
                    or delivery.effect_fence_ref != self.effect_fence_ref
                    or delivery.effect_fence_digest != fence.effect_fence_digest
                    or delivery.delivery_attempt_ref != self.delivery_attempt_ref
                    or delivery.adapter_safe_correlation_ref != self.adapter_safe_correlation_ref):
                _invalid()
            before = _blob_bindings(self.before_blob_entries, manifest, after=False)
            after = _blob_bindings(self.after_blob_entries, manifest, after=True)
            if (len(before) != 3 or len(after) != 3
                    or tuple(item["path"] for item in before)
                    != tuple(item["path"] for item in after)
                    or sum(x[1] != y[1] for x, y in zip(
                        self.before_blob_entries, self.after_blob_entries, strict=True
                    )) != 1):
                _invalid()
            identity = {
                field.name: object.__getattribute__(self, field.name)
                for field in fields(type(self))
                if field.name not in {
                    "effect_authorization_safe_binding", "capsule_manifest",
                    "requirement_evidence", "before_blob_entries", "after_blob_entries",
                    "effect_fence", "delivery_envelope", "command_digest",
                }
            }
            identity.update({
                "effect_authorization_safe_binding": {
                    **binding.identity_mapping(),
                    "safe_binding_digest": binding.safe_binding_digest,
                },
                "capsule_manifest": manifest.to_mapping(),
                "requirement_evidence": {
                    **requirement.identity_mapping(),
                    "safe_evidence_digest": requirement.safe_evidence_digest,
                },
                "before_blob_entries": before,
                "after_blob_entries": after,
                "effect_fence": fence.to_mapping(),
                "delivery_envelope": delivery.to_mapping(),
            })
            return identity
        except (ValueError, TypeError, AttributeError, _RowValueValidationError,
                WorkerExecutionValueError):
            _invalid()

    def computed_digest(self) -> str:
        return _domain_separated_digest(_COMMAND_DOMAIN, self.identity_mapping())

    __repr__ = _safe_display
    __str__ = _safe_display
    __reduce__ = _no_pickle
    __reduce_ex__ = _no_pickle

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


def _blob_bindings(
    entries: object, manifest: CandidateCapsuleManifestV1, *, after: bool,
) -> tuple[dict[str, object], ...]:
    if type(entries) is not tuple or len(entries) != len(manifest.entries):
        _invalid()
    out: list[dict[str, object]] = []
    for supplied, recorded in zip(entries, manifest.entries, strict=True):
        if (type(supplied) is not tuple or len(supplied) != 2
                or type(supplied[0]) is not str or type(supplied[1]) is not bytes
                or supplied[0] != recorded.path or len(supplied[1]) > 1_048_576):
            _invalid()
        length = len(supplied[1])
        digest = hashlib.sha256(supplied[1]).hexdigest()
        if after:
            if length != recorded.after_byte_length or digest != recorded.after_blob_sha256:
                _invalid()
        elif length != recorded.before_byte_length or digest != recorded.before_blob_sha256:
            _invalid()
        out.append({"path": supplied[0], "byte_length": length, "sha256": digest})
    return tuple(out)


def _require_exact_development_bound_effect_command(
    value: object,
) -> DevelopmentBoundEffectEstablishmentCommandV1:
    if type(value) is not DevelopmentBoundEffectEstablishmentCommandV1:
        _invalid()
    value.validate()
    return value


def _reduce_development_bound_effect_establishment_command(
    *,
    mutation_ref: str,
    effect_class: str,
    effect_intent_ref: str,
    effect_fence_ref: str,
    authority_evaluation_ref: str,
    delivery_attempt_ref: str,
    adapter_safe_correlation_ref: str,
    author_command: DevelopmentAuthorEffectEstablishmentCommandV1,
    selected_disposition: PreExecutionPlanDispositionResultV1,
    phase_basis: RW0PhaseEntryBasisV1,
    work_spec: WorkSpecV1,
    capture: D1CandidateCapture,
    capsule_manifest: CandidateCapsuleManifestV1,
    requirement_evidence: DevelopmentValidationRequirementEvidenceV1 | DevelopmentReviewRequirementEvidenceV1,
    effect_authorization_safe_binding: DevelopmentBoundEffectAuthorizationSafeBindingV1,
) -> DevelopmentBoundEffectEstablishmentCommandV1:
    """Reduce one actual D1 capsule and selected owner lineage to a closed command."""
    try:
        if (type(author_command) is not DevelopmentAuthorEffectEstablishmentCommandV1
                or type(selected_disposition) is not PreExecutionPlanDispositionResultV1
                or type(phase_basis) is not RW0PhaseEntryBasisV1
                or type(work_spec) is not WorkSpecV1
                or type(capture) is not D1CandidateCapture
                or type(capsule_manifest) is not CandidateCapsuleManifestV1
                or type(effect_class) is not str or effect_class not in _EFFECT_CLASSES):
            _invalid()
        capture.validate()
        checked_author = DevelopmentAuthorEffectEstablishmentCommandV1(
            **{name: object.__getattribute__(author_command, name)
               for name in author_command.__dataclass_fields__}
        )
        checked_work = WorkSpecV1.from_mapping(work_spec.to_mapping())
        checked_projection = _program_rows.development_work_spec_safe_projection_from_work_spec(
            work_spec=checked_work
        )
        if (checked_projection != checked_author.work_spec_safe_projection
                or selected_disposition.disposition != "selected_for_dispatch_gates"
                or phase_basis.disposition_ref != selected_disposition.disposition_ref
                or phase_basis.disposition_digest != selected_disposition.disposition_digest
                or phase_basis.global_stop_state != "clear"
                or phase_basis.global_stop_ref != checked_author.coding_global_stop_ref
                or phase_basis.global_stop_version != checked_author.coding_global_stop_version):
            _invalid()
        requirement = (
            _require_exact_validation_evidence(requirement_evidence)
            if effect_class == "validate_candidate"
            else _require_exact_review_evidence(requirement_evidence)
        )
        expected_requirement = (
            checked_author.validation_requirement_evidence
            if effect_class == "validate_candidate"
            else checked_author.review_requirement_evidence
        )
        if requirement != expected_requirement:
            _invalid()
        manifest = CandidateCapsuleManifestV1.from_mapping(capsule_manifest.to_mapping())
        before = tuple((entry.path, entry.before) for entry in capture.entries)
        after = tuple((entry.path, entry.after) for entry in capture.entries)
        before_map = {path: blob for path, blob in before}
        after_map = {path: blob for path, blob in after}
        validate_capsule_manifest_relation(
            capsule_manifest=manifest,
            author_command=checked_author.worker_command,
            attempt_fence=checked_author.attempt_fence,
            author_effect_fence=checked_author.effect_fence,
            before_blobs=before_map, after_blobs=after_map,
        )
        binding = _require_exact_bound_effect_authorization_safe_binding(
            effect_authorization_safe_binding
        )
        if (binding.effect_class != effect_class
                or binding.effect_intent_ref != effect_intent_ref
                or binding.semantic_attempt_ref != checked_author.semantic_attempt_ref
                or binding.parent_standing_grant_ref
                != checked_author.attempt_fence.parent_standing_grant_ref
                or binding.parent_standing_grant_digest
                != checked_author.attempt_fence.parent_standing_grant_digest
                or binding.attempt_fence_ref != checked_author.attempt_fence_ref
                or binding.attempt_fence_digest != checked_author.attempt_fence.attempt_fence_digest
                or binding.global_stop_ref != checked_author.coding_global_stop_ref
                or binding.global_stop_version != checked_author.coding_global_stop_version
                or binding.expires_at > checked_author.attempt_fence.expires_at
                or binding.path_ceiling != checked_author.attempt_fence.path_ceiling
                or binding.effect_ceilings.max_deliveries > 1):
            _invalid()
        fence = create_effect_fence(
            attempt_fence=checked_author.attempt_fence,
            author_command=checked_author.worker_command,
            author_effect_fence=checked_author.effect_fence,
            effect_fence_ref=effect_fence_ref,
            effect_intent_ref=effect_intent_ref,
            effect_class=effect_class,
            effect_authorization_ref=binding.effect_authorization_ref,
            effect_authorization_digest=binding.effect_authorization_digest,
            effect_ceilings=binding.effect_ceilings,
            expires_at=binding.expires_at,
            capsule_manifest=manifest,
        )
        delivery = DeliveryEnvelopeV1.create(
            delivery_attempt_ref=delivery_attempt_ref,
            adapter_kind="direct_local_bootstrap",
            adapter_safe_correlation_ref=adapter_safe_correlation_ref,
            author_command=checked_author.worker_command,
            attempt_fence=checked_author.attempt_fence,
            author_effect_fence=checked_author.effect_fence,
            effect_fence=fence,
            capsule_manifest=manifest,
        )
        validate_delivery_relation(
            delivery=delivery,
            author_command=checked_author.worker_command,
            attempt_fence=checked_author.attempt_fence,
            author_effect_fence=checked_author.effect_fence,
            effect_fence=fence,
            capsule_manifest=manifest,
        )
        values = {
            "schema_id": _COMMAND_SCHEMA,
            "mutation_ref": mutation_ref,
            "effect_class": effect_class,
            "program_ref": checked_author.program_ref,
            "program_version_ref": checked_author.program_version_ref,
            "accepted_intent_revision_ref": checked_author.accepted_intent_revision_ref,
            "work_item_ref": checked_author.work_item_ref,
            "work_item_revision_ref": checked_author.work_item_revision_ref,
            "basis_decision_ref": checked_author.basis_decision_ref,
            "basis_decision_digest": checked_author.basis_decision_digest,
            "semantic_attempt_ref": checked_author.semantic_attempt_ref,
            "candidate_ref": checked_author.candidate_ref,
            "attempt_fence_ref": checked_author.attempt_fence_ref,
            "attempt_fence_digest": checked_author.attempt_fence.attempt_fence_digest,
            "originating_command_ref": checked_author.command_ref,
            "originating_command_digest": checked_author.worker_command.command_digest,
            "author_effect_fence_ref": checked_author.effect_fence_ref,
            "author_effect_fence_digest": checked_author.effect_fence.effect_fence_digest,
            "selected_disposition_ref": selected_disposition.disposition_ref,
            "selected_disposition_digest": selected_disposition.disposition_digest,
            "phase_basis_ref": phase_basis.basis_ref,
            "phase_basis_digest": phase_basis.basis_digest,
            "capsule_manifest_ref": manifest.capsule_manifest_ref,
            "portable_capsule_digest": manifest.portable_capsule_digest,
            "requirement_ref": requirement.requirement_ref,
            "requirement_safe_digest": requirement.safe_evidence_digest,
            "effect_intent_ref": effect_intent_ref,
            "effect_fence_ref": effect_fence_ref,
            "authority_evaluation_ref": authority_evaluation_ref,
            "delivery_attempt_ref": delivery_attempt_ref,
            "adapter_safe_correlation_ref": adapter_safe_correlation_ref,
            "effect_authorization_safe_binding": binding,
            "capsule_manifest": manifest,
            "requirement_evidence": requirement,
            "before_blob_entries": before,
            "after_blob_entries": after,
            "effect_fence": fence,
            "delivery_envelope": delivery,
        }
        provisional = object.__new__(DevelopmentBoundEffectEstablishmentCommandV1)
        for name, value in values.items():
            object.__setattr__(provisional, name, value)
        digest = _domain_separated_digest(_COMMAND_DOMAIN, provisional.identity_mapping())
        return DevelopmentBoundEffectEstablishmentCommandV1(**values, command_digest=digest)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        _invalid()


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentBoundEffectEstablishmentResultV1:
    disposition: str
    mutation_ref: str
    command_digest: str
    program_ref: str
    decision_ref: str
    program_version_ref: str
    semantic_attempt_ref: str
    candidate_ref: str
    effect_class: str
    effect_intent_ref: str
    effect_fence_ref: str
    delivery_attempt_ref: str
    transaction_timestamp: str

    def __post_init__(self) -> None:
        if type(self) is not DevelopmentBoundEffectEstablishmentResultV1:
            _invalid()
        try:
            if type(self.disposition) is not str or self.disposition not in {
                "committed", "exact_replay",
            }:
                _invalid()
            for name in (
                "mutation_ref", "program_ref", "decision_ref", "program_version_ref",
                "semantic_attempt_ref", "candidate_ref", "effect_intent_ref",
                "effect_fence_ref", "delivery_attempt_ref",
            ):
                _require_safe_ref(object.__getattribute__(self, name))
            _require_sha256(self.command_digest)
            _require_utc_timestamp(self.transaction_timestamp)
            if type(self.effect_class) is not str or self.effect_class not in _EFFECT_CLASSES:
                _invalid()
        except (ValueError, TypeError, AttributeError, _RowValueValidationError):
            _invalid()

    def identity_mapping(self) -> dict[str, object]:
        return {item.name: object.__getattribute__(self, item.name)
                for item in fields(type(self))}

    def computed_digest(self) -> str:
        return _domain_separated_digest(_RESULT_DOMAIN, self.identity_mapping())

    __repr__ = _safe_display
    __str__ = _safe_display
    __reduce__ = _no_pickle
    __reduce_ex__ = _no_pickle


class DevelopmentBoundEffectEstablishmentConflictReasonV1(str, Enum):
    MUTATION_REF_REUSE_CONFLICT = "mutation_ref_reuse_conflict"
    GLOBAL_STOP_VERSION_CONFLICT = "global_stop_version_conflict"
    CODING_GLOBAL_STOP_ACTIVE = "coding_global_stop_active"
    SEMANTIC_IDENTITY_CONFLICT = "semantic_identity_conflict"
    CURRENT_STATE_CONFLICT = "current_state_conflict"


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentBoundEffectEstablishmentConflictV1:
    reason: DevelopmentBoundEffectEstablishmentConflictReasonV1
    mutation_ref: str
    command_digest: str
    program_ref: str

    def __post_init__(self) -> None:
        if type(self.reason) is not DevelopmentBoundEffectEstablishmentConflictReasonV1:
            _invalid()
        try:
            _require_safe_ref(self.mutation_ref)
            _require_sha256(self.command_digest)
            _require_safe_ref(self.program_ref)
        except _RowValueValidationError:
            _invalid()

    __repr__ = _safe_display
    __str__ = _safe_display


class DevelopmentBoundEffectEstablishmentRecoveryDispositionV1(str, Enum):
    COMMITTED_EXACT = "committed_exact"
    DEFINITELY_NOT_COMMITTED = "definitely_not_committed"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentBoundEffectEstablishmentRecoveryResultV1:
    disposition: DevelopmentBoundEffectEstablishmentRecoveryDispositionV1
    committed_result: DevelopmentBoundEffectEstablishmentResultV1 | None = field(
        default=None, repr=False
    )

    def __post_init__(self) -> None:
        if type(self.disposition) is not DevelopmentBoundEffectEstablishmentRecoveryDispositionV1:
            _invalid()
        if self.disposition is DevelopmentBoundEffectEstablishmentRecoveryDispositionV1.COMMITTED_EXACT:
            if (type(self.committed_result) is not DevelopmentBoundEffectEstablishmentResultV1
                    or self.committed_result.disposition != "exact_replay"):
                _invalid()
        elif self.committed_result is not None:
            _invalid()

    __repr__ = _safe_display
    __str__ = _safe_display


@dataclass(frozen=True, slots=True, repr=False)
class _DevelopmentBoundEffectEstablishmentWritePlan:
    effect_intent: _effect_rows.DevelopmentEffectIntentRowValue
    effect_fence: _effect_rows.DevelopmentEffectFenceRowValue
    authority_evaluation: _effect_rows.DevelopmentAuthorityEvaluationRowValue
    delivery_attempt: _effect_rows.DevelopmentDeliveryAttemptRowValue
    effect_head: _effect_rows.DevelopmentEffectHeadRowValue
    delivery_head: _effect_rows.DevelopmentDeliveryHeadRowValue
    mutation_receipt: _decision_rows.DevelopmentMutationReceiptRowValue
    graph_entries: tuple[_decision_rows.DevelopmentMutationGraphEntry, ...]
    planned_result: DevelopmentBoundEffectEstablishmentResultV1

    __repr__ = _safe_display
    __str__ = _safe_display
    __reduce__ = _no_pickle
    __reduce_ex__ = _no_pickle


def _bound_effect_result(
    command: DevelopmentBoundEffectEstablishmentCommandV1,
    timestamp: str,
    disposition: str,
) -> DevelopmentBoundEffectEstablishmentResultV1:
    return DevelopmentBoundEffectEstablishmentResultV1(
        disposition, command.mutation_ref, command.command_digest,
        command.program_ref, command.basis_decision_ref,
        command.program_version_ref, command.semantic_attempt_ref,
        command.candidate_ref, command.effect_class, command.effect_intent_ref,
        command.effect_fence_ref, command.delivery_attempt_ref, timestamp,
    )


def _bound_effect_conflict(
    command: DevelopmentBoundEffectEstablishmentCommandV1,
    reason: DevelopmentBoundEffectEstablishmentConflictReasonV1,
) -> DevelopmentBoundEffectEstablishmentConflictV1:
    return DevelopmentBoundEffectEstablishmentConflictV1(
        reason, command.mutation_ref, command.command_digest, command.program_ref,
    )


def _bound_receipt_row(
    command: DevelopmentBoundEffectEstablishmentCommandV1,
    timestamp: str,
    projection_digest: str,
    graph_digest: str,
) -> _decision_rows.DevelopmentMutationReceiptRowValue:
    return _decision_rows.development_mutation_receipt_row_value_from_row_tuple((
        "governed-execution.nwp-development-mutation-receipt.v1",
        command.mutation_ref, "establish_development_bound_effect_intent",
        _COMMAND_SCHEMA, command.command_digest, command.program_ref,
        command.basis_decision_ref, command.program_version_ref,
        command.semantic_attempt_ref, command.effect_intent_ref,
        command.effect_fence_ref, command.delivery_attempt_ref, None, None,
        "development_bound_effect_intent_established", projection_digest,
        graph_digest, "committed", timestamp,
    ))


def _development_bound_effect_establishment_write_plan(
    command: object,
    transaction_timestamp: object,
) -> _DevelopmentBoundEffectEstablishmentWritePlan:
    checked = _require_exact_development_bound_effect_command(command)
    try:
        timestamp = _require_utc_timestamp(transaction_timestamp)
        binding = _require_exact_bound_effect_authorization_safe_binding(
            checked.effect_authorization_safe_binding
        )
        effect_intent = _row_with_digest(
            fields={
                "schema_id": "governed-execution.nwp-development-effect-intent.v1",
                "effect_intent_ref": checked.effect_intent_ref,
                "program_ref": checked.program_ref,
                "program_version_ref": checked.program_version_ref,
                "semantic_attempt_ref": checked.semantic_attempt_ref,
                "effect_class": checked.effect_class,
                "candidate_ref": checked.candidate_ref,
                "command_ref": checked.originating_command_ref,
                "basis_decision_ref": checked.basis_decision_ref,
                "cancellation_target_effect_intent_ref": None,
                "expected_target_effect_head_revision": None,
                "portable_capsule_digest": checked.portable_capsule_digest,
                "created_at": timestamp,
            },
            domain="governed-execution.nwp-development-effect-intent.v1.identity",
            digest_field="effect_intent_digest",
            adapter=_effect_rows.development_effect_intent_row_value_from_row_tuple,
        )
        effect_fence = _effect_rows.development_effect_fence_row_value_from_row_tuple(
            _effect_fence_parameters(checked.effect_fence, timestamp)
        )
        authority = _row_with_digest(
            fields={
                "schema_id": "governed-execution.nwp-development-authority-evaluation.v1",
                "authority_evaluation_ref": checked.authority_evaluation_ref,
                "program_ref": checked.program_ref,
                "evaluation_scope": "effect",
                "evaluation_subject_ref": checked.effect_intent_ref,
                "semantic_attempt_ref": None,
                "effect_intent_ref": checked.effect_intent_ref,
                "authority_ref": binding.effect_authorization_ref,
                "authority_digest": binding.effect_authorization_digest,
                "authority_state": "pending",
                "reason_code": "external_verification_pending",
                "expires_at": None,
                "evaluated_at": timestamp,
            },
            domain="governed-execution.nwp-development-authority-evaluation.v1.identity",
            digest_field="authority_evaluation_digest",
            adapter=_effect_rows.development_authority_evaluation_row_value_from_row_tuple,
        )
        delivery = _effect_rows.development_delivery_attempt_row_value_from_row_tuple(
            _delivery_attempt_parameters(
                checked.delivery_envelope,
                basis_decision_ref=checked.basis_decision_ref,
                timestamp=timestamp,
            )
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
        projection = {
            "schema_id": _RECEIPT_RESULT_SCHEMA,
            "program_ref": checked.program_ref,
            "decision_ref": checked.basis_decision_ref,
            "result_program_version_ref": checked.program_version_ref,
            "result_semantic_attempt_ref": checked.semantic_attempt_ref,
            "result_effect_intent_ref": checked.effect_intent_ref,
            "result_effect_fence_ref": checked.effect_fence_ref,
            "result_delivery_attempt_ref": checked.delivery_attempt_ref,
        }
        projection_digest = _domain_separated_digest(_RECEIPT_RESULT_DOMAIN, projection)
        provisional = _bound_receipt_row(checked, timestamp, projection_digest, "0" * 64)
        graph_entries = tuple(
            _decision_rows.development_mutation_graph_entry(
                role=role, ordinal=0, record_ref=ref, record_digest=digest
            )
            for role, ref, digest in (
                ("bound_effect_intent", effect_intent.effect_intent_ref,
                 effect_intent.effect_intent_digest),
                ("bound_effect_fence", effect_fence.effect_fence_ref,
                 effect_fence.effect_fence_digest),
                ("authority_evaluation", authority.authority_evaluation_ref,
                 authority.authority_evaluation_digest),
                ("initial_delivery_attempt", delivery.delivery_attempt_ref,
                 delivery.delivery_attempt_digest),
                ("effect_head_postimage", effect_head.effect_intent_ref,
                 effect_head.head_digest),
                ("delivery_head_postimage", delivery_head.effect_intent_ref,
                 delivery_head.head_digest),
            )
        )
        graph_digest = _decision_rows.compute_development_mutation_graph_digest(
            receipt=provisional, graph_entries=graph_entries
        )
        receipt = _bound_receipt_row(checked, timestamp, projection_digest, graph_digest)
        _decision_rows.require_development_mutation_graph_digest_matches_supplied_entries(
            receipt=receipt, graph_entries=graph_entries
        )
        return _DevelopmentBoundEffectEstablishmentWritePlan(
            effect_intent, effect_fence, authority, delivery, effect_head,
            delivery_head, receipt, graph_entries,
            _bound_effect_result(checked, timestamp, "committed"),
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        _invalid()
