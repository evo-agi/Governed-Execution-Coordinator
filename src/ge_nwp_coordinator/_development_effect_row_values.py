"""Pure private C2B2 row values for development effects and delivery."""

from __future__ import annotations

import typing

from ._development_row_value_support import (
    _ImmutableValue,
    _RowValueValidationError,
    _canonical_identity_bytes,
    _decode_effect_class_mask,
    _decode_fixed_paths_json,
    _domain_separated_digest,
    _encode_effect_class_mask,
    _encode_fixed_paths,
    _new_database_integrity_error,
    _require_constant_string,
    _require_enum,
    _require_matching_digest,
    _require_nonnegative_integer,
    _require_optional_nonnegative_integer,
    _require_optional_safe_ref,
    _require_optional_sha256,
    _require_optional_utc_timestamp,
    _require_positive_integer,
    _require_reason_code,
    _require_safe_ref,
    _require_sha256,
    _require_utc_timestamp,
    _row_tuple_to_private_mapping,
)
from ._worker_execution_semantic_values import (
    AttemptFenceV1,
    DeliveryEnvelopeV1,
    EffectFenceV1,
    WorkerCommandV1,
    WorkerExecutionValueError,
)


__all__: tuple[str, ...] = ()


_DEVELOPMENT_ATTEMPT_FENCE_COLUMNS = (
    "schema_id", "attempt_fence_ref", "parent_standing_grant_ref",
    "parent_standing_grant_digest", "attempt_authorization_ref",
    "attempt_authorization_digest", "program_ref", "program_version_ref",
    "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref",
    "semantic_attempt_ref", "repository_ref", "base_git_object_format",
    "base_git_oid", "path_ceiling_json", "allowed_effect_class_mask",
    "aggregate_max_active_invocations", "aggregate_max_candidate_bytes",
    "aggregate_max_changed_files", "aggregate_max_cost_microusd",
    "aggregate_max_cpu_seconds", "aggregate_max_deliveries",
    "aggregate_max_deployments", "aggregate_max_local_commits",
    "aggregate_max_memory_bytes", "aggregate_max_merges",
    "aggregate_max_model_input_tokens", "aggregate_max_model_output_tokens",
    "aggregate_max_pull_requests", "aggregate_max_pushes",
    "aggregate_max_wall_seconds", "expires_at", "global_stop_ref",
    "global_stop_version", "attempt_fence_digest", "recorded_at",
)
_DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS = (
    "schema_id", "authority_evaluation_ref", "program_ref", "evaluation_scope",
    "evaluation_subject_ref", "semantic_attempt_ref", "effect_intent_ref",
    "authority_ref", "authority_digest", "authority_state", "reason_code",
    "expires_at", "evaluated_at", "authority_evaluation_digest",
)
_DEVELOPMENT_EFFECT_INTENT_COLUMNS = (
    "schema_id", "effect_intent_ref", "program_ref", "program_version_ref",
    "semantic_attempt_ref", "effect_class", "candidate_ref", "command_ref",
    "basis_decision_ref", "cancellation_target_effect_intent_ref",
    "expected_target_effect_head_revision", "portable_capsule_digest",
    "created_at", "effect_intent_digest",
)
_DEVELOPMENT_EFFECT_FENCE_COLUMNS = (
    "schema_id", "effect_fence_ref", "parent_standing_grant_ref",
    "parent_standing_grant_digest", "effect_authorization_ref",
    "effect_authorization_digest", "attempt_fence_ref", "attempt_fence_digest",
    "program_ref", "program_version_ref", "accepted_intent_revision_ref",
    "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
    "effect_intent_ref", "effect_class", "command_ref", "command_digest",
    "candidate_ref", "repository_ref", "base_git_object_format", "base_git_oid",
    "path_ceiling_json", "effect_max_active_invocations",
    "effect_max_candidate_bytes", "effect_max_changed_files",
    "effect_max_cost_microusd", "effect_max_cpu_seconds", "effect_max_deliveries",
    "effect_max_deployments", "effect_max_local_commits",
    "effect_max_memory_bytes", "effect_max_merges", "effect_max_model_input_tokens",
    "effect_max_model_output_tokens", "effect_max_pull_requests",
    "effect_max_pushes", "effect_max_wall_seconds", "expires_at",
    "global_stop_ref", "global_stop_version", "portable_capsule_digest",
    "cancellation_target_effect_intent_ref", "cancellation_target_effect_fence_ref",
    "cancellation_target_effect_fence_digest", "effect_fence_digest", "recorded_at",
)
_DEVELOPMENT_AUTHOR_COMMAND_COLUMNS = (
    "schema_id", "command_ref", "program_ref", "program_version_ref",
    "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref",
    "semantic_attempt_ref", "effect_intent_ref", "effect_class", "candidate_ref",
    "repository_ref", "base_git_object_format", "base_git_oid", "path_ceiling_json",
    "work_spec_ref", "work_spec_digest", "standing_grant_ref",
    "standing_grant_digest", "attempt_authorization_ref",
    "attempt_authorization_digest", "effect_authorization_ref",
    "effect_authorization_digest", "attempt_fence_ref", "attempt_fence_digest",
    "effect_fence_ref", "effect_fence_digest", "global_stop_ref",
    "global_stop_version", "validation_requirement_ref",
    "validation_requirement_digest", "review_requirement_ref",
    "review_requirement_digest", "capsule_schema_id", "capsule_profile_ref",
    "effect_max_active_invocations", "effect_max_candidate_bytes",
    "effect_max_changed_files", "effect_max_cost_microusd", "effect_max_cpu_seconds",
    "effect_max_deliveries", "effect_max_deployments", "effect_max_local_commits",
    "effect_max_memory_bytes", "effect_max_merges", "effect_max_model_input_tokens",
    "effect_max_model_output_tokens", "effect_max_pull_requests", "effect_max_pushes",
    "effect_max_wall_seconds", "privacy_classification", "redaction_profile_ref",
    "command_digest", "recorded_at",
)
_DEVELOPMENT_EFFECT_HEAD_COLUMNS = (
    "schema_id", "effect_intent_ref", "program_ref", "current_effect_fence_ref",
    "head_revision", "effect_state", "cancellation_effect_intent_ref", "updated_at",
    "head_digest",
)
_DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS = (
    "schema_id", "delivery_attempt_ref", "program_ref", "program_version_ref",
    "command_ref", "command_digest", "semantic_attempt_ref", "effect_intent_ref",
    "attempt_fence_ref", "attempt_fence_digest", "effect_fence_ref",
    "effect_fence_digest", "adapter_kind", "adapter_safe_correlation_ref",
    "delivery_envelope_digest", "delivery_kind", "delivery_number",
    "predecessor_delivery_attempt_ref", "basis_decision_ref", "recorded_at",
    "delivery_attempt_digest",
)
_DEVELOPMENT_DELIVERY_HEAD_COLUMNS = (
    "schema_id", "effect_intent_ref", "program_ref", "current_delivery_attempt_ref",
    "head_revision", "delivery_state", "updated_at", "head_digest",
)

_ATTEMPT_FENCE_SCHEMA = "governed-execution.nwp-attempt-fence.v1"
_AUTHORITY_EVALUATION_SCHEMA = (
    "governed-execution.nwp-development-authority-evaluation.v1"
)
_EFFECT_INTENT_SCHEMA = "governed-execution.nwp-development-effect-intent.v1"
_EFFECT_FENCE_SCHEMA = "governed-execution.nwp-effect-fence.v1"
_AUTHOR_COMMAND_SCHEMA = "governed-execution.nwp-worker-command.v1"
_EFFECT_HEAD_SCHEMA = "governed-execution.nwp-development-effect-head.v1"
_DELIVERY_ENVELOPE_SCHEMA = "governed-execution.nwp-delivery-envelope.v1"
_DELIVERY_ATTEMPT_WRAPPER_SCHEMA = (
    "governed-execution.nwp-development-delivery-attempt.v1"
)
_DELIVERY_HEAD_SCHEMA = "governed-execution.nwp-development-delivery-head.v1"

_ATTEMPT_FENCE_DOMAIN = _ATTEMPT_FENCE_SCHEMA + ".identity"
_AUTHORITY_EVALUATION_DOMAIN = _AUTHORITY_EVALUATION_SCHEMA + ".identity"
_EFFECT_INTENT_DOMAIN = _EFFECT_INTENT_SCHEMA + ".identity"
_EFFECT_FENCE_DOMAIN = _EFFECT_FENCE_SCHEMA + ".identity"
_AUTHOR_COMMAND_DOMAIN = _AUTHOR_COMMAND_SCHEMA + ".identity"
_EFFECT_HEAD_DOMAIN = _EFFECT_HEAD_SCHEMA + ".identity"
_DELIVERY_ATTEMPT_DOMAIN = _DELIVERY_ATTEMPT_WRAPPER_SCHEMA + ".identity"
_DELIVERY_HEAD_DOMAIN = _DELIVERY_HEAD_SCHEMA + ".identity"

_EVALUATION_SCOPES = ("attempt", "effect")
_AUTHORITY_STATES = ("pending", "verified", "blocked", "stale", "revoked", "expired")
_EFFECT_CLASSES = (
    "author_candidate", "cancel_effect", "local_git_commit", "review_candidate",
    "validate_candidate",
)
_EFFECT_STATES = (
    "ready_for_delivery", "delivery_pending", "delivery_outcome_unknown", "observed",
    "cancellation_effect_established", "terminal",
)
_DELIVERY_KINDS = ("initial", "redelivery")
_DELIVERY_STATES = (
    "planned", "submitted", "outcome_unknown", "acknowledged", "rejected", "completed",
)


class _DigestBackedValue(_ImmutableValue):
    __slots__ = ()
    _DOMAIN = ""

    def identity_mapping(self) -> dict[str, object]:
        return self._identity_mapping()

    def canonical_identity_bytes(self) -> bytes:
        return _canonical_identity_bytes(self._identity_mapping())

    def computed_digest(self) -> str:
        return _domain_separated_digest(self._DOMAIN, self._identity_mapping())


class DevelopmentAttemptFenceRowValue(_ImmutableValue):
    __slots__ = ("_values",)

    @property
    def attempt_fence(self) -> AttemptFenceV1: return typing.cast(AttemptFenceV1, self._values[0])
    @property
    def recorded_at(self) -> str: return typing.cast(str, self._values[1])
    @property
    def schema_id(self) -> str: return self.attempt_fence.schema_id
    @property
    def attempt_fence_ref(self) -> str: return self.attempt_fence.attempt_fence_ref
    @property
    def parent_standing_grant_ref(self) -> str: return self.attempt_fence.parent_standing_grant_ref
    @property
    def parent_standing_grant_digest(self) -> str: return self.attempt_fence.parent_standing_grant_digest
    @property
    def attempt_authorization_ref(self) -> str: return self.attempt_fence.attempt_authorization_ref
    @property
    def attempt_authorization_digest(self) -> str: return self.attempt_fence.attempt_authorization_digest
    @property
    def program_ref(self) -> str: return self.attempt_fence.program_ref
    @property
    def program_version_ref(self) -> str: return self.attempt_fence.program_version_ref
    @property
    def accepted_intent_revision_ref(self) -> str: return self.attempt_fence.accepted_intent_revision_ref
    @property
    def work_item_ref(self) -> str: return self.attempt_fence.work_item_ref
    @property
    def work_item_revision_ref(self) -> str: return self.attempt_fence.work_item_revision_ref
    @property
    def semantic_attempt_ref(self) -> str: return self.attempt_fence.semantic_attempt_ref
    @property
    def repository_ref(self) -> str: return self.attempt_fence.repository_ref
    @property
    def base_git_object_format(self) -> str: return self.attempt_fence.base_git_object_format
    @property
    def base_git_oid(self) -> str: return self.attempt_fence.base_git_oid
    @property
    def path_ceiling_json(self) -> str: return _encode_fixed_paths(self.attempt_fence.path_ceiling)
    @property
    def allowed_effect_class_mask(self) -> int: return _encode_effect_class_mask(self.attempt_fence.allowed_effect_classes)
    @property
    def aggregate_max_active_invocations(self) -> int: return self.attempt_fence.aggregate_ceilings.max_active_invocations
    @property
    def aggregate_max_candidate_bytes(self) -> int: return self.attempt_fence.aggregate_ceilings.max_candidate_bytes
    @property
    def aggregate_max_changed_files(self) -> int: return self.attempt_fence.aggregate_ceilings.max_changed_files
    @property
    def aggregate_max_cost_microusd(self) -> int: return self.attempt_fence.aggregate_ceilings.max_cost_microusd
    @property
    def aggregate_max_cpu_seconds(self) -> int: return self.attempt_fence.aggregate_ceilings.max_cpu_seconds
    @property
    def aggregate_max_deliveries(self) -> int: return self.attempt_fence.aggregate_ceilings.max_deliveries
    @property
    def aggregate_max_deployments(self) -> int: return self.attempt_fence.aggregate_ceilings.max_deployments
    @property
    def aggregate_max_local_commits(self) -> int: return self.attempt_fence.aggregate_ceilings.max_local_commits
    @property
    def aggregate_max_memory_bytes(self) -> int: return self.attempt_fence.aggregate_ceilings.max_memory_bytes
    @property
    def aggregate_max_merges(self) -> int: return self.attempt_fence.aggregate_ceilings.max_merges
    @property
    def aggregate_max_model_input_tokens(self) -> int: return self.attempt_fence.aggregate_ceilings.max_model_input_tokens
    @property
    def aggregate_max_model_output_tokens(self) -> int: return self.attempt_fence.aggregate_ceilings.max_model_output_tokens
    @property
    def aggregate_max_pull_requests(self) -> int: return self.attempt_fence.aggregate_ceilings.max_pull_requests
    @property
    def aggregate_max_pushes(self) -> int: return self.attempt_fence.aggregate_ceilings.max_pushes
    @property
    def aggregate_max_wall_seconds(self) -> int: return self.attempt_fence.aggregate_ceilings.max_wall_seconds
    @property
    def expires_at(self) -> str: return self.attempt_fence.expires_at
    @property
    def global_stop_ref(self) -> str: return self.attempt_fence.global_stop_ref
    @property
    def global_stop_version(self) -> int: return self.attempt_fence.global_stop_version
    @property
    def attempt_fence_digest(self) -> str: return self.attempt_fence.attempt_fence_digest

    def identity_mapping(self) -> dict[str, object]: return self.attempt_fence.identity_mapping()
    def canonical_identity_bytes(self) -> bytes: return self.attempt_fence.canonical_identity_bytes()
    def computed_digest(self) -> str: return self.attempt_fence.computed_digest()

    @classmethod
    def _from_validated(cls, attempt_fence: AttemptFenceV1, recorded_at: str) -> DevelopmentAttemptFenceRowValue:
        result = object.__new__(cls); object.__setattr__(result, "_values", (attempt_fence, recorded_at)); return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn: raise TypeError("subclassing disabled")


class DevelopmentAuthorityEvaluationRowValue(_DigestBackedValue):
    __slots__ = ("_values",)
    _DOMAIN = _AUTHORITY_EVALUATION_DOMAIN

    @property
    def schema_id(self) -> str: return typing.cast(str, self._values[0])
    @property
    def authority_evaluation_ref(self) -> str: return typing.cast(str, self._values[1])
    @property
    def program_ref(self) -> str: return typing.cast(str, self._values[2])
    @property
    def evaluation_scope(self) -> str: return typing.cast(str, self._values[3])
    @property
    def evaluation_subject_ref(self) -> str: return typing.cast(str, self._values[4])
    @property
    def semantic_attempt_ref(self) -> str | None: return typing.cast(str | None, self._values[5])
    @property
    def effect_intent_ref(self) -> str | None: return typing.cast(str | None, self._values[6])
    @property
    def authority_ref(self) -> str: return typing.cast(str, self._values[7])
    @property
    def authority_digest(self) -> str: return typing.cast(str, self._values[8])
    @property
    def authority_state(self) -> str: return typing.cast(str, self._values[9])
    @property
    def reason_code(self) -> str: return typing.cast(str, self._values[10])
    @property
    def expires_at(self) -> str | None: return typing.cast(str | None, self._values[11])
    @property
    def evaluated_at(self) -> str: return typing.cast(str, self._values[12])
    @property
    def authority_evaluation_digest(self) -> str: return typing.cast(str, self._values[13])

    def _identity_mapping(self) -> dict[str, object]:
        return {"schema_id":self.schema_id,"authority_evaluation_ref":self.authority_evaluation_ref,
            "program_ref":self.program_ref,"evaluation_scope":self.evaluation_scope,
            "evaluation_subject_ref":self.evaluation_subject_ref,"semantic_attempt_ref":self.semantic_attempt_ref,
            "effect_intent_ref":self.effect_intent_ref,"authority_ref":self.authority_ref,
            "authority_digest":self.authority_digest,"authority_state":self.authority_state,
            "reason_code":self.reason_code,"expires_at":self.expires_at,"evaluated_at":self.evaluated_at}

    @classmethod
    def _from_validated(cls, values: tuple[object, ...]) -> DevelopmentAuthorityEvaluationRowValue:
        result=object.__new__(cls); object.__setattr__(result,"_values",values); return result
    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn: raise TypeError("subclassing disabled")


class DevelopmentEffectIntentRowValue(_DigestBackedValue):
    __slots__ = ("_values",)
    _DOMAIN = _EFFECT_INTENT_DOMAIN

    @property
    def schema_id(self) -> str: return typing.cast(str,self._values[0])
    @property
    def effect_intent_ref(self) -> str: return typing.cast(str,self._values[1])
    @property
    def program_ref(self) -> str: return typing.cast(str,self._values[2])
    @property
    def program_version_ref(self) -> str: return typing.cast(str,self._values[3])
    @property
    def semantic_attempt_ref(self) -> str: return typing.cast(str,self._values[4])
    @property
    def effect_class(self) -> str: return typing.cast(str,self._values[5])
    @property
    def candidate_ref(self) -> str: return typing.cast(str,self._values[6])
    @property
    def command_ref(self) -> str: return typing.cast(str,self._values[7])
    @property
    def basis_decision_ref(self) -> str: return typing.cast(str,self._values[8])
    @property
    def cancellation_target_effect_intent_ref(self) -> str | None: return typing.cast(str|None,self._values[9])
    @property
    def expected_target_effect_head_revision(self) -> int | None: return typing.cast(int|None,self._values[10])
    @property
    def portable_capsule_digest(self) -> str | None: return typing.cast(str|None,self._values[11])
    @property
    def created_at(self) -> str: return typing.cast(str,self._values[12])
    @property
    def effect_intent_digest(self) -> str: return typing.cast(str,self._values[13])

    def _identity_mapping(self) -> dict[str, object]:
        return {"schema_id":self.schema_id,"effect_intent_ref":self.effect_intent_ref,
            "program_ref":self.program_ref,"program_version_ref":self.program_version_ref,
            "semantic_attempt_ref":self.semantic_attempt_ref,"effect_class":self.effect_class,
            "candidate_ref":self.candidate_ref,"command_ref":self.command_ref,
            "basis_decision_ref":self.basis_decision_ref,
            "cancellation_target_effect_intent_ref":self.cancellation_target_effect_intent_ref,
            "expected_target_effect_head_revision":self.expected_target_effect_head_revision,
            "portable_capsule_digest":self.portable_capsule_digest,"created_at":self.created_at}

    @classmethod
    def _from_validated(cls, values: tuple[object,...]) -> DevelopmentEffectIntentRowValue:
        result=object.__new__(cls); object.__setattr__(result,"_values",values); return result
    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn: raise TypeError("subclassing disabled")


class DevelopmentEffectFenceRowValue(_ImmutableValue):
    __slots__ = ("_values",)

    @property
    def effect_fence(self) -> EffectFenceV1: return typing.cast(EffectFenceV1,self._values[0])
    @property
    def recorded_at(self) -> str: return typing.cast(str,self._values[1])
    @property
    def schema_id(self) -> str: return self.effect_fence.schema_id
    @property
    def effect_fence_ref(self) -> str: return self.effect_fence.effect_fence_ref
    @property
    def parent_standing_grant_ref(self) -> str: return self.effect_fence.parent_standing_grant_ref
    @property
    def parent_standing_grant_digest(self) -> str: return self.effect_fence.parent_standing_grant_digest
    @property
    def effect_authorization_ref(self) -> str: return self.effect_fence.effect_authorization_ref
    @property
    def effect_authorization_digest(self) -> str: return self.effect_fence.effect_authorization_digest
    @property
    def attempt_fence_ref(self) -> str: return self.effect_fence.attempt_fence_ref
    @property
    def attempt_fence_digest(self) -> str: return self.effect_fence.attempt_fence_digest
    @property
    def program_ref(self) -> str: return self.effect_fence.program_ref
    @property
    def program_version_ref(self) -> str: return self.effect_fence.program_version_ref
    @property
    def accepted_intent_revision_ref(self) -> str: return self.effect_fence.accepted_intent_revision_ref
    @property
    def work_item_ref(self) -> str: return self.effect_fence.work_item_ref
    @property
    def work_item_revision_ref(self) -> str: return self.effect_fence.work_item_revision_ref
    @property
    def semantic_attempt_ref(self) -> str: return self.effect_fence.semantic_attempt_ref
    @property
    def effect_intent_ref(self) -> str: return self.effect_fence.effect_intent_ref
    @property
    def effect_class(self) -> str: return self.effect_fence.effect_class
    @property
    def command_ref(self) -> str: return self.effect_fence.command_ref
    @property
    def command_digest(self) -> str: return self.effect_fence.command_digest
    @property
    def candidate_ref(self) -> str: return self.effect_fence.candidate_ref
    @property
    def repository_ref(self) -> str: return self.effect_fence.repository_ref
    @property
    def base_git_object_format(self) -> str: return self.effect_fence.base_git_object_format
    @property
    def base_git_oid(self) -> str: return self.effect_fence.base_git_oid
    @property
    def path_ceiling_json(self) -> str: return _encode_fixed_paths(self.effect_fence.path_ceiling)
    @property
    def effect_max_active_invocations(self) -> int: return self.effect_fence.effect_ceilings.max_active_invocations
    @property
    def effect_max_candidate_bytes(self) -> int: return self.effect_fence.effect_ceilings.max_candidate_bytes
    @property
    def effect_max_changed_files(self) -> int: return self.effect_fence.effect_ceilings.max_changed_files
    @property
    def effect_max_cost_microusd(self) -> int: return self.effect_fence.effect_ceilings.max_cost_microusd
    @property
    def effect_max_cpu_seconds(self) -> int: return self.effect_fence.effect_ceilings.max_cpu_seconds
    @property
    def effect_max_deliveries(self) -> int: return self.effect_fence.effect_ceilings.max_deliveries
    @property
    def effect_max_deployments(self) -> int: return self.effect_fence.effect_ceilings.max_deployments
    @property
    def effect_max_local_commits(self) -> int: return self.effect_fence.effect_ceilings.max_local_commits
    @property
    def effect_max_memory_bytes(self) -> int: return self.effect_fence.effect_ceilings.max_memory_bytes
    @property
    def effect_max_merges(self) -> int: return self.effect_fence.effect_ceilings.max_merges
    @property
    def effect_max_model_input_tokens(self) -> int: return self.effect_fence.effect_ceilings.max_model_input_tokens
    @property
    def effect_max_model_output_tokens(self) -> int: return self.effect_fence.effect_ceilings.max_model_output_tokens
    @property
    def effect_max_pull_requests(self) -> int: return self.effect_fence.effect_ceilings.max_pull_requests
    @property
    def effect_max_pushes(self) -> int: return self.effect_fence.effect_ceilings.max_pushes
    @property
    def effect_max_wall_seconds(self) -> int: return self.effect_fence.effect_ceilings.max_wall_seconds
    @property
    def expires_at(self) -> str: return self.effect_fence.expires_at
    @property
    def global_stop_ref(self) -> str: return self.effect_fence.global_stop_ref
    @property
    def global_stop_version(self) -> int: return self.effect_fence.global_stop_version
    @property
    def portable_capsule_digest(self) -> str | None: return self.effect_fence.portable_capsule_digest
    @property
    def cancellation_target_effect_intent_ref(self) -> str | None: return self.effect_fence.cancellation_target_effect_intent_ref
    @property
    def cancellation_target_effect_fence_ref(self) -> str | None: return self.effect_fence.cancellation_target_effect_fence_ref
    @property
    def cancellation_target_effect_fence_digest(self) -> str | None: return self.effect_fence.cancellation_target_effect_fence_digest
    @property
    def effect_fence_digest(self) -> str: return self.effect_fence.effect_fence_digest

    def identity_mapping(self) -> dict[str,object]: return self.effect_fence.identity_mapping()
    def canonical_identity_bytes(self) -> bytes: return self.effect_fence.canonical_identity_bytes()
    def computed_digest(self) -> str: return self.effect_fence.computed_digest()

    @classmethod
    def _from_validated(cls,effect_fence:EffectFenceV1,recorded_at:str)->DevelopmentEffectFenceRowValue:
        result=object.__new__(cls); object.__setattr__(result,"_values",(effect_fence,recorded_at)); return result
    def __init_subclass__(cls,**kwargs:object)->typing.NoReturn: raise TypeError("subclassing disabled")


class DevelopmentAuthorCommandRowValue(_ImmutableValue):
    __slots__ = ("_values",)

    @property
    def author_command(self) -> WorkerCommandV1: return typing.cast(WorkerCommandV1,self._values[0])
    @property
    def worker_command(self) -> WorkerCommandV1: return self.author_command
    @property
    def recorded_at(self) -> str: return typing.cast(str,self._values[1])
    @property
    def schema_id(self) -> str: return self.author_command.schema_id
    @property
    def command_ref(self) -> str: return self.author_command.command_ref
    @property
    def program_ref(self) -> str: return self.author_command.program_ref
    @property
    def program_version_ref(self) -> str: return self.author_command.program_version_ref
    @property
    def accepted_intent_revision_ref(self) -> str: return self.author_command.accepted_intent_revision_ref
    @property
    def work_item_ref(self) -> str: return self.author_command.work_item_ref
    @property
    def work_item_revision_ref(self) -> str: return self.author_command.work_item_revision_ref
    @property
    def semantic_attempt_ref(self) -> str: return self.author_command.semantic_attempt_ref
    @property
    def effect_intent_ref(self) -> str: return self.author_command.effect_intent_ref
    @property
    def effect_class(self) -> str: return self.author_command.effect_class
    @property
    def candidate_ref(self) -> str: return self.author_command.candidate_ref
    @property
    def repository_ref(self) -> str: return self.author_command.repository_ref
    @property
    def base_git_object_format(self) -> str: return self.author_command.base_git_object_format
    @property
    def base_git_oid(self) -> str: return self.author_command.base_git_oid
    @property
    def path_ceiling_json(self) -> str: return _encode_fixed_paths(self.author_command.path_ceiling)
    @property
    def work_spec_ref(self) -> str: return self.author_command.work_spec_ref
    @property
    def work_spec_digest(self) -> str: return self.author_command.work_spec_digest
    @property
    def standing_grant_ref(self) -> str: return self.author_command.standing_grant_ref
    @property
    def standing_grant_digest(self) -> str: return self.author_command.standing_grant_digest
    @property
    def attempt_authorization_ref(self) -> str: return self.author_command.attempt_authorization_ref
    @property
    def attempt_authorization_digest(self) -> str: return self.author_command.attempt_authorization_digest
    @property
    def effect_authorization_ref(self) -> str: return self.author_command.effect_authorization_ref
    @property
    def effect_authorization_digest(self) -> str: return self.author_command.effect_authorization_digest
    @property
    def attempt_fence_ref(self) -> str: return self.author_command.attempt_fence_ref
    @property
    def attempt_fence_digest(self) -> str: return self.author_command.attempt_fence_digest
    @property
    def effect_fence_ref(self) -> str: return self.author_command.effect_fence_ref
    @property
    def effect_fence_digest(self) -> str: return self.author_command.effect_fence_digest
    @property
    def global_stop_ref(self) -> str: return self.author_command.global_stop_ref
    @property
    def global_stop_version(self) -> int: return self.author_command.global_stop_version
    @property
    def validation_requirement_ref(self) -> str: return self.author_command.validation_requirement_ref
    @property
    def validation_requirement_digest(self) -> str: return self.author_command.validation_requirement_digest
    @property
    def review_requirement_ref(self) -> str: return self.author_command.review_requirement_ref
    @property
    def review_requirement_digest(self) -> str: return self.author_command.review_requirement_digest
    @property
    def capsule_schema_id(self) -> str: return self.author_command.capsule_schema_id
    @property
    def capsule_profile_ref(self) -> str: return self.author_command.capsule_profile_ref
    @property
    def effect_max_active_invocations(self) -> int: return self.author_command.effect_ceilings.max_active_invocations
    @property
    def effect_max_candidate_bytes(self) -> int: return self.author_command.effect_ceilings.max_candidate_bytes
    @property
    def effect_max_changed_files(self) -> int: return self.author_command.effect_ceilings.max_changed_files
    @property
    def effect_max_cost_microusd(self) -> int: return self.author_command.effect_ceilings.max_cost_microusd
    @property
    def effect_max_cpu_seconds(self) -> int: return self.author_command.effect_ceilings.max_cpu_seconds
    @property
    def effect_max_deliveries(self) -> int: return self.author_command.effect_ceilings.max_deliveries
    @property
    def effect_max_deployments(self) -> int: return self.author_command.effect_ceilings.max_deployments
    @property
    def effect_max_local_commits(self) -> int: return self.author_command.effect_ceilings.max_local_commits
    @property
    def effect_max_memory_bytes(self) -> int: return self.author_command.effect_ceilings.max_memory_bytes
    @property
    def effect_max_merges(self) -> int: return self.author_command.effect_ceilings.max_merges
    @property
    def effect_max_model_input_tokens(self) -> int: return self.author_command.effect_ceilings.max_model_input_tokens
    @property
    def effect_max_model_output_tokens(self) -> int: return self.author_command.effect_ceilings.max_model_output_tokens
    @property
    def effect_max_pull_requests(self) -> int: return self.author_command.effect_ceilings.max_pull_requests
    @property
    def effect_max_pushes(self) -> int: return self.author_command.effect_ceilings.max_pushes
    @property
    def effect_max_wall_seconds(self) -> int: return self.author_command.effect_ceilings.max_wall_seconds
    @property
    def privacy_classification(self) -> str: return self.author_command.privacy_classification
    @property
    def redaction_profile_ref(self) -> str: return self.author_command.redaction_profile_ref
    @property
    def command_digest(self) -> str: return self.author_command.command_digest

    def identity_mapping(self)->dict[str,object]: return self.author_command.identity_mapping()
    def canonical_identity_bytes(self)->bytes: return self.author_command.canonical_identity_bytes()
    def computed_digest(self)->str: return self.author_command.computed_digest()

    @classmethod
    def _from_validated(cls,command:WorkerCommandV1,recorded_at:str)->DevelopmentAuthorCommandRowValue:
        result=object.__new__(cls); object.__setattr__(result,"_values",(command,recorded_at)); return result
    def __init_subclass__(cls,**kwargs:object)->typing.NoReturn: raise TypeError("subclassing disabled")


class DevelopmentEffectHeadRowValue(_DigestBackedValue):
    __slots__=("_values",)
    _DOMAIN=_EFFECT_HEAD_DOMAIN
    @property
    def schema_id(self)->str:return typing.cast(str,self._values[0])
    @property
    def effect_intent_ref(self)->str:return typing.cast(str,self._values[1])
    @property
    def program_ref(self)->str:return typing.cast(str,self._values[2])
    @property
    def current_effect_fence_ref(self)->str:return typing.cast(str,self._values[3])
    @property
    def head_revision(self)->int:return typing.cast(int,self._values[4])
    @property
    def effect_state(self)->str:return typing.cast(str,self._values[5])
    @property
    def cancellation_effect_intent_ref(self)->str|None:return typing.cast(str|None,self._values[6])
    @property
    def updated_at(self)->str:return typing.cast(str,self._values[7])
    @property
    def head_digest(self)->str:return typing.cast(str,self._values[8])
    def _identity_mapping(self)->dict[str,object]:
        return {"schema_id":self.schema_id,"effect_intent_ref":self.effect_intent_ref,
            "program_ref":self.program_ref,"current_effect_fence_ref":self.current_effect_fence_ref,
            "head_revision":self.head_revision,"effect_state":self.effect_state,
            "cancellation_effect_intent_ref":self.cancellation_effect_intent_ref,"updated_at":self.updated_at}
    @classmethod
    def _from_validated(cls,values:tuple[object,...])->DevelopmentEffectHeadRowValue:
        result=object.__new__(cls);object.__setattr__(result,"_values",values);return result
    def __init_subclass__(cls,**kwargs:object)->typing.NoReturn:raise TypeError("subclassing disabled")


class DevelopmentDeliveryAttemptRowValue(_DigestBackedValue):
    __slots__=("_values",)
    _DOMAIN=_DELIVERY_ATTEMPT_DOMAIN
    @property
    def delivery_envelope(self)->DeliveryEnvelopeV1:return typing.cast(DeliveryEnvelopeV1,self._values[0])
    @property
    def schema_id(self)->str:return self.delivery_envelope.schema_id
    @property
    def wrapper_schema_id(self)->str:return _DELIVERY_ATTEMPT_WRAPPER_SCHEMA
    @property
    def delivery_attempt_ref(self)->str:return self.delivery_envelope.delivery_attempt_ref
    @property
    def program_ref(self)->str:return self.delivery_envelope.program_ref
    @property
    def program_version_ref(self)->str:return self.delivery_envelope.program_version_ref
    @property
    def command_ref(self)->str:return self.delivery_envelope.command_ref
    @property
    def command_digest(self)->str:return self.delivery_envelope.command_digest
    @property
    def semantic_attempt_ref(self)->str:return self.delivery_envelope.semantic_attempt_ref
    @property
    def effect_intent_ref(self)->str:return self.delivery_envelope.effect_intent_ref
    @property
    def attempt_fence_ref(self)->str:return self.delivery_envelope.attempt_fence_ref
    @property
    def attempt_fence_digest(self)->str:return self.delivery_envelope.attempt_fence_digest
    @property
    def effect_fence_ref(self)->str:return self.delivery_envelope.effect_fence_ref
    @property
    def effect_fence_digest(self)->str:return self.delivery_envelope.effect_fence_digest
    @property
    def adapter_kind(self)->str:return self.delivery_envelope.adapter_kind
    @property
    def adapter_safe_correlation_ref(self)->str:return self.delivery_envelope.adapter_safe_correlation_ref
    @property
    def delivery_envelope_digest(self)->str:return self.delivery_envelope.delivery_envelope_digest
    @property
    def delivery_kind(self)->str:return typing.cast(str,self._values[1])
    @property
    def delivery_number(self)->int:return typing.cast(int,self._values[2])
    @property
    def predecessor_delivery_attempt_ref(self)->str|None:return typing.cast(str|None,self._values[3])
    @property
    def basis_decision_ref(self)->str:return typing.cast(str,self._values[4])
    @property
    def recorded_at(self)->str:return typing.cast(str,self._values[5])
    @property
    def delivery_attempt_digest(self)->str:return typing.cast(str,self._values[6])
    def _identity_mapping(self)->dict[str,object]:
        return {"schema_id":self.wrapper_schema_id,"delivery_envelope_digest":self.delivery_envelope_digest,
            "delivery_kind":self.delivery_kind,"delivery_number":self.delivery_number,
            "predecessor_delivery_attempt_ref":self.predecessor_delivery_attempt_ref,
            "basis_decision_ref":self.basis_decision_ref,"recorded_at":self.recorded_at}
    @classmethod
    def _from_validated(cls,values:tuple[object,...])->DevelopmentDeliveryAttemptRowValue:
        result=object.__new__(cls);object.__setattr__(result,"_values",values);return result
    def __init_subclass__(cls,**kwargs:object)->typing.NoReturn:raise TypeError("subclassing disabled")


class DevelopmentDeliveryHeadRowValue(_DigestBackedValue):
    __slots__=("_values",)
    _DOMAIN=_DELIVERY_HEAD_DOMAIN
    @property
    def schema_id(self)->str:return typing.cast(str,self._values[0])
    @property
    def effect_intent_ref(self)->str:return typing.cast(str,self._values[1])
    @property
    def program_ref(self)->str:return typing.cast(str,self._values[2])
    @property
    def current_delivery_attempt_ref(self)->str:return typing.cast(str,self._values[3])
    @property
    def head_revision(self)->int:return typing.cast(int,self._values[4])
    @property
    def delivery_state(self)->str:return typing.cast(str,self._values[5])
    @property
    def updated_at(self)->str:return typing.cast(str,self._values[6])
    @property
    def head_digest(self)->str:return typing.cast(str,self._values[7])
    def _identity_mapping(self)->dict[str,object]:
        return {"schema_id":self.schema_id,"effect_intent_ref":self.effect_intent_ref,
            "program_ref":self.program_ref,"current_delivery_attempt_ref":self.current_delivery_attempt_ref,
            "head_revision":self.head_revision,"delivery_state":self.delivery_state,"updated_at":self.updated_at}
    @classmethod
    def _from_validated(cls,values:tuple[object,...])->DevelopmentDeliveryHeadRowValue:
        result=object.__new__(cls);object.__setattr__(result,"_values",values);return result
    def __init_subclass__(cls,**kwargs:object)->typing.NoReturn:raise TypeError("subclassing disabled")


def _aggregate_ceilings_from_row(mapping: dict[str, object]) -> dict[str, object]:
    return {
        "max_active_invocations": mapping["aggregate_max_active_invocations"],
        "max_candidate_bytes": mapping["aggregate_max_candidate_bytes"],
        "max_changed_files": mapping["aggregate_max_changed_files"],
        "max_cost_microusd": mapping["aggregate_max_cost_microusd"],
        "max_cpu_seconds": mapping["aggregate_max_cpu_seconds"],
        "max_deliveries": mapping["aggregate_max_deliveries"],
        "max_deployments": mapping["aggregate_max_deployments"],
        "max_local_commits": mapping["aggregate_max_local_commits"],
        "max_memory_bytes": mapping["aggregate_max_memory_bytes"],
        "max_merges": mapping["aggregate_max_merges"],
        "max_model_input_tokens": mapping["aggregate_max_model_input_tokens"],
        "max_model_output_tokens": mapping["aggregate_max_model_output_tokens"],
        "max_pull_requests": mapping["aggregate_max_pull_requests"],
        "max_pushes": mapping["aggregate_max_pushes"],
        "max_wall_seconds": mapping["aggregate_max_wall_seconds"],
    }


def _effect_ceilings_from_row(mapping: dict[str, object]) -> dict[str, object]:
    return {
        "max_active_invocations": mapping["effect_max_active_invocations"],
        "max_candidate_bytes": mapping["effect_max_candidate_bytes"],
        "max_changed_files": mapping["effect_max_changed_files"],
        "max_cost_microusd": mapping["effect_max_cost_microusd"],
        "max_cpu_seconds": mapping["effect_max_cpu_seconds"],
        "max_deliveries": mapping["effect_max_deliveries"],
        "max_deployments": mapping["effect_max_deployments"],
        "max_local_commits": mapping["effect_max_local_commits"],
        "max_memory_bytes": mapping["effect_max_memory_bytes"],
        "max_merges": mapping["effect_max_merges"],
        "max_model_input_tokens": mapping["effect_max_model_input_tokens"],
        "max_model_output_tokens": mapping["effect_max_model_output_tokens"],
        "max_pull_requests": mapping["effect_max_pull_requests"],
        "max_pushes": mapping["effect_max_pushes"],
        "max_wall_seconds": mapping["effect_max_wall_seconds"],
    }


def _attempt_attempt_fence(
    row: object,
) -> tuple[DevelopmentAttemptFenceRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentAttemptFenceRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_ATTEMPT_FENCE_COLUMNS,
            row=row,
        )
        path_ceiling = _decode_fixed_paths_json(mapping["path_ceiling_json"])
        effect_classes = _decode_effect_class_mask(mapping["allowed_effect_class_mask"])
        attempt_fence = AttemptFenceV1.from_mapping(
            {
                "schema_id": mapping["schema_id"],
                "attempt_fence_ref": mapping["attempt_fence_ref"],
                "parent_standing_grant_ref": mapping["parent_standing_grant_ref"],
                "parent_standing_grant_digest": mapping["parent_standing_grant_digest"],
                "attempt_authorization_ref": mapping["attempt_authorization_ref"],
                "attempt_authorization_digest": mapping["attempt_authorization_digest"],
                "program_ref": mapping["program_ref"],
                "program_version_ref": mapping["program_version_ref"],
                "accepted_intent_revision_ref": mapping["accepted_intent_revision_ref"],
                "work_item_ref": mapping["work_item_ref"],
                "work_item_revision_ref": mapping["work_item_revision_ref"],
                "semantic_attempt_ref": mapping["semantic_attempt_ref"],
                "repository_ref": mapping["repository_ref"],
                "base_git_object_format": mapping["base_git_object_format"],
                "base_git_oid": mapping["base_git_oid"],
                "path_ceiling": list(path_ceiling),
                "allowed_effect_classes": list(effect_classes),
                "aggregate_ceilings": _aggregate_ceilings_from_row(mapping),
                "expires_at": mapping["expires_at"],
                "global_stop_ref": mapping["global_stop_ref"],
                "global_stop_version": mapping["global_stop_version"],
                "attempt_fence_digest": mapping["attempt_fence_digest"],
            }
        )
        recorded_at = _require_utc_timestamp(mapping["recorded_at"])
        result = DevelopmentAttemptFenceRowValue._from_validated(
            attempt_fence,
            recorded_at,
        )
    except (_RowValueValidationError, WorkerExecutionValueError):
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_attempt_fence_row_value_from_row_tuple(
    row: object,
) -> DevelopmentAttemptFenceRowValue:
    result, error = _attempt_attempt_fence(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentAttemptFenceRowValue, result)


def _attempt_authority_evaluation(
    row: object,
) -> tuple[DevelopmentAuthorityEvaluationRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentAuthorityEvaluationRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS,
            row=row,
        )
        scope = _require_enum(mapping["evaluation_scope"], _EVALUATION_SCOPES)
        subject = _require_safe_ref(mapping["evaluation_subject_ref"])
        attempt_ref = _require_optional_safe_ref(mapping["semantic_attempt_ref"])
        effect_ref = _require_optional_safe_ref(mapping["effect_intent_ref"])
        if not (
            (scope == "attempt" and attempt_ref == subject and effect_ref is None)
            or (scope == "effect" and effect_ref == subject and attempt_ref is None)
        ):
            raise _RowValueValidationError() from None
        state = _require_enum(mapping["authority_state"], _AUTHORITY_STATES)
        expires_at = _require_optional_utc_timestamp(mapping["expires_at"])
        if (state in ("verified", "expired")) != (expires_at is not None):
            raise _RowValueValidationError() from None
        validated = (
            _require_constant_string(mapping["schema_id"], _AUTHORITY_EVALUATION_SCHEMA),
            _require_safe_ref(mapping["authority_evaluation_ref"]),
            _require_safe_ref(mapping["program_ref"]),
            scope,
            subject,
            attempt_ref,
            effect_ref,
            _require_safe_ref(mapping["authority_ref"]),
            _require_sha256(mapping["authority_digest"]),
            state,
            _require_reason_code(mapping["reason_code"]),
            expires_at,
            _require_utc_timestamp(mapping["evaluated_at"]),
        )
        identity = {
            "schema_id": validated[0], "authority_evaluation_ref": validated[1],
            "program_ref": validated[2], "evaluation_scope": validated[3],
            "evaluation_subject_ref": validated[4], "semantic_attempt_ref": validated[5],
            "effect_intent_ref": validated[6], "authority_ref": validated[7],
            "authority_digest": validated[8], "authority_state": validated[9],
            "reason_code": validated[10], "expires_at": validated[11],
            "evaluated_at": validated[12],
        }
        digest = _require_matching_digest(
            domain=_AUTHORITY_EVALUATION_DOMAIN,
            identity=identity,
            stored_digest=mapping["authority_evaluation_digest"],
        )
        result = DevelopmentAuthorityEvaluationRowValue._from_validated(
            validated + (digest,)
        )
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_authority_evaluation_row_value_from_row_tuple(
    row: object,
) -> DevelopmentAuthorityEvaluationRowValue:
    result, error = _attempt_authority_evaluation(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentAuthorityEvaluationRowValue, result)


def _attempt_effect_intent(
    row: object,
) -> tuple[DevelopmentEffectIntentRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentEffectIntentRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_EFFECT_INTENT_COLUMNS,
            row=row,
        )
        effect_class = _require_enum(mapping["effect_class"], _EFFECT_CLASSES)
        target = _require_optional_safe_ref(mapping["cancellation_target_effect_intent_ref"])
        expected_revision = _require_optional_nonnegative_integer(
            mapping["expected_target_effect_head_revision"]
        )
        capsule_digest = _require_optional_sha256(mapping["portable_capsule_digest"])
        if effect_class == "cancel_effect":
            if target is None or expected_revision is None:
                raise _RowValueValidationError() from None
        elif target is not None or expected_revision is not None:
            raise _RowValueValidationError() from None
        if effect_class == "author_candidate" and capsule_digest is not None:
            raise _RowValueValidationError() from None
        if effect_class in ("validate_candidate", "review_candidate", "local_git_commit") and capsule_digest is None:
            raise _RowValueValidationError() from None
        validated = (
            _require_constant_string(mapping["schema_id"], _EFFECT_INTENT_SCHEMA),
            _require_safe_ref(mapping["effect_intent_ref"]),
            _require_safe_ref(mapping["program_ref"]),
            _require_safe_ref(mapping["program_version_ref"]),
            _require_safe_ref(mapping["semantic_attempt_ref"]),
            effect_class,
            _require_safe_ref(mapping["candidate_ref"]),
            _require_safe_ref(mapping["command_ref"]),
            _require_safe_ref(mapping["basis_decision_ref"]),
            target,
            expected_revision,
            capsule_digest,
            _require_utc_timestamp(mapping["created_at"]),
        )
        identity = {
            "schema_id":validated[0],"effect_intent_ref":validated[1],
            "program_ref":validated[2],"program_version_ref":validated[3],
            "semantic_attempt_ref":validated[4],"effect_class":validated[5],
            "candidate_ref":validated[6],"command_ref":validated[7],
            "basis_decision_ref":validated[8],"cancellation_target_effect_intent_ref":validated[9],
            "expected_target_effect_head_revision":validated[10],
            "portable_capsule_digest":validated[11],"created_at":validated[12],
        }
        digest = _require_matching_digest(
            domain=_EFFECT_INTENT_DOMAIN,
            identity=identity,
            stored_digest=mapping["effect_intent_digest"],
        )
        result = DevelopmentEffectIntentRowValue._from_validated(validated + (digest,))
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_effect_intent_row_value_from_row_tuple(
    row: object,
) -> DevelopmentEffectIntentRowValue:
    result, error = _attempt_effect_intent(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentEffectIntentRowValue, result)


def _attempt_effect_fence(
    row: object,
) -> tuple[DevelopmentEffectFenceRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentEffectFenceRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_EFFECT_FENCE_COLUMNS,
            row=row,
        )
        effect_fence = EffectFenceV1.from_mapping(
            {
                "schema_id": mapping["schema_id"],
                "effect_fence_ref": mapping["effect_fence_ref"],
                "parent_standing_grant_ref": mapping["parent_standing_grant_ref"],
                "parent_standing_grant_digest": mapping["parent_standing_grant_digest"],
                "effect_authorization_ref": mapping["effect_authorization_ref"],
                "effect_authorization_digest": mapping["effect_authorization_digest"],
                "attempt_fence_ref": mapping["attempt_fence_ref"],
                "attempt_fence_digest": mapping["attempt_fence_digest"],
                "program_ref": mapping["program_ref"],
                "program_version_ref": mapping["program_version_ref"],
                "accepted_intent_revision_ref": mapping["accepted_intent_revision_ref"],
                "work_item_ref": mapping["work_item_ref"],
                "work_item_revision_ref": mapping["work_item_revision_ref"],
                "semantic_attempt_ref": mapping["semantic_attempt_ref"],
                "effect_intent_ref": mapping["effect_intent_ref"],
                "effect_class": mapping["effect_class"],
                "command_ref": mapping["command_ref"],
                "command_digest": mapping["command_digest"],
                "candidate_ref": mapping["candidate_ref"],
                "repository_ref": mapping["repository_ref"],
                "base_git_object_format": mapping["base_git_object_format"],
                "base_git_oid": mapping["base_git_oid"],
                "path_ceiling": list(_decode_fixed_paths_json(mapping["path_ceiling_json"])),
                "effect_ceilings": _effect_ceilings_from_row(mapping),
                "expires_at": mapping["expires_at"],
                "global_stop_ref": mapping["global_stop_ref"],
                "global_stop_version": mapping["global_stop_version"],
                "portable_capsule_digest": mapping["portable_capsule_digest"],
                "cancellation_target_effect_intent_ref": mapping["cancellation_target_effect_intent_ref"],
                "cancellation_target_effect_fence_ref": mapping["cancellation_target_effect_fence_ref"],
                "cancellation_target_effect_fence_digest": mapping["cancellation_target_effect_fence_digest"],
                "effect_fence_digest": mapping["effect_fence_digest"],
            }
        )
        recorded_at = _require_utc_timestamp(mapping["recorded_at"])
        result = DevelopmentEffectFenceRowValue._from_validated(effect_fence, recorded_at)
    except (_RowValueValidationError, WorkerExecutionValueError):
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_effect_fence_row_value_from_row_tuple(
    row: object,
) -> DevelopmentEffectFenceRowValue:
    result, error = _attempt_effect_fence(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentEffectFenceRowValue, result)


def _attempt_author_command(
    row: object,
) -> tuple[DevelopmentAuthorCommandRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentAuthorCommandRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_AUTHOR_COMMAND_COLUMNS,
            row=row,
        )
        command = WorkerCommandV1.from_mapping(
            {
                "schema_id": mapping["schema_id"],
                "command_ref": mapping["command_ref"],
                "program_ref": mapping["program_ref"],
                "program_version_ref": mapping["program_version_ref"],
                "accepted_intent_revision_ref": mapping["accepted_intent_revision_ref"],
                "work_item_ref": mapping["work_item_ref"],
                "work_item_revision_ref": mapping["work_item_revision_ref"],
                "semantic_attempt_ref": mapping["semantic_attempt_ref"],
                "effect_intent_ref": mapping["effect_intent_ref"],
                "effect_class": mapping["effect_class"],
                "candidate_ref": mapping["candidate_ref"],
                "repository_ref": mapping["repository_ref"],
                "base_git_object_format": mapping["base_git_object_format"],
                "base_git_oid": mapping["base_git_oid"],
                "path_ceiling": list(_decode_fixed_paths_json(mapping["path_ceiling_json"])),
                "work_spec_ref": mapping["work_spec_ref"],
                "work_spec_digest": mapping["work_spec_digest"],
                "standing_grant_ref": mapping["standing_grant_ref"],
                "standing_grant_digest": mapping["standing_grant_digest"],
                "attempt_authorization_ref": mapping["attempt_authorization_ref"],
                "attempt_authorization_digest": mapping["attempt_authorization_digest"],
                "effect_authorization_ref": mapping["effect_authorization_ref"],
                "effect_authorization_digest": mapping["effect_authorization_digest"],
                "attempt_fence_ref": mapping["attempt_fence_ref"],
                "attempt_fence_digest": mapping["attempt_fence_digest"],
                "effect_fence_ref": mapping["effect_fence_ref"],
                "effect_fence_digest": mapping["effect_fence_digest"],
                "global_stop_ref": mapping["global_stop_ref"],
                "global_stop_version": mapping["global_stop_version"],
                "validation_requirement_ref": mapping["validation_requirement_ref"],
                "validation_requirement_digest": mapping["validation_requirement_digest"],
                "review_requirement_ref": mapping["review_requirement_ref"],
                "review_requirement_digest": mapping["review_requirement_digest"],
                "capsule_schema_id": mapping["capsule_schema_id"],
                "capsule_profile_ref": mapping["capsule_profile_ref"],
                "effect_ceilings": _effect_ceilings_from_row(mapping),
                "privacy_classification": mapping["privacy_classification"],
                "redaction_profile_ref": mapping["redaction_profile_ref"],
                "command_digest": mapping["command_digest"],
            }
        )
        recorded_at = _require_utc_timestamp(mapping["recorded_at"])
        result = DevelopmentAuthorCommandRowValue._from_validated(command, recorded_at)
    except (_RowValueValidationError, WorkerExecutionValueError):
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_author_command_row_value_from_row_tuple(
    row: object,
) -> DevelopmentAuthorCommandRowValue:
    result, error = _attempt_author_command(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentAuthorCommandRowValue, result)


def _attempt_effect_head(
    row: object,
) -> tuple[DevelopmentEffectHeadRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentEffectHeadRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_EFFECT_HEAD_COLUMNS,
            row=row,
        )
        state = _require_enum(mapping["effect_state"], _EFFECT_STATES)
        cancellation_ref = _require_optional_safe_ref(
            mapping["cancellation_effect_intent_ref"]
        )
        if (state == "cancellation_effect_established") != (cancellation_ref is not None):
            raise _RowValueValidationError() from None
        validated = (
            _require_constant_string(mapping["schema_id"], _EFFECT_HEAD_SCHEMA),
            _require_safe_ref(mapping["effect_intent_ref"]),
            _require_safe_ref(mapping["program_ref"]),
            _require_safe_ref(mapping["current_effect_fence_ref"]),
            _require_nonnegative_integer(mapping["head_revision"]),
            state,
            cancellation_ref,
            _require_utc_timestamp(mapping["updated_at"]),
        )
        identity = {
            "schema_id": validated[0], "effect_intent_ref": validated[1],
            "program_ref": validated[2], "current_effect_fence_ref": validated[3],
            "head_revision": validated[4], "effect_state": validated[5],
            "cancellation_effect_intent_ref": validated[6], "updated_at": validated[7],
        }
        digest = _require_matching_digest(
            domain=_EFFECT_HEAD_DOMAIN,
            identity=identity,
            stored_digest=mapping["head_digest"],
        )
        result = DevelopmentEffectHeadRowValue._from_validated(validated + (digest,))
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_effect_head_row_value_from_row_tuple(
    row: object,
) -> DevelopmentEffectHeadRowValue:
    result, error = _attempt_effect_head(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentEffectHeadRowValue, result)


def _attempt_delivery_attempt(
    row: object,
) -> tuple[DevelopmentDeliveryAttemptRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentDeliveryAttemptRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS,
            row=row,
        )
        delivery_envelope = DeliveryEnvelopeV1.from_mapping(
            {
                "schema_id": mapping["schema_id"],
                "delivery_attempt_ref": mapping["delivery_attempt_ref"],
                "program_ref": mapping["program_ref"],
                "program_version_ref": mapping["program_version_ref"],
                "command_ref": mapping["command_ref"],
                "command_digest": mapping["command_digest"],
                "semantic_attempt_ref": mapping["semantic_attempt_ref"],
                "effect_intent_ref": mapping["effect_intent_ref"],
                "attempt_fence_ref": mapping["attempt_fence_ref"],
                "attempt_fence_digest": mapping["attempt_fence_digest"],
                "effect_fence_ref": mapping["effect_fence_ref"],
                "effect_fence_digest": mapping["effect_fence_digest"],
                "adapter_kind": mapping["adapter_kind"],
                "adapter_safe_correlation_ref": mapping["adapter_safe_correlation_ref"],
                "delivery_envelope_digest": mapping["delivery_envelope_digest"],
            }
        )
        delivery_kind = _require_enum(mapping["delivery_kind"], _DELIVERY_KINDS)
        delivery_number = _require_positive_integer(mapping["delivery_number"])
        predecessor = _require_optional_safe_ref(
            mapping["predecessor_delivery_attempt_ref"]
        )
        if not (
            (delivery_kind == "initial" and delivery_number == 1 and predecessor is None)
            or (delivery_kind == "redelivery" and delivery_number >= 2 and predecessor is not None)
        ):
            raise _RowValueValidationError() from None
        basis_decision_ref = _require_safe_ref(mapping["basis_decision_ref"])
        recorded_at = _require_utc_timestamp(mapping["recorded_at"])
        identity = {
            "schema_id": _DELIVERY_ATTEMPT_WRAPPER_SCHEMA,
            "delivery_envelope_digest": delivery_envelope.delivery_envelope_digest,
            "delivery_kind": delivery_kind,
            "delivery_number": delivery_number,
            "predecessor_delivery_attempt_ref": predecessor,
            "basis_decision_ref": basis_decision_ref,
            "recorded_at": recorded_at,
        }
        digest = _require_matching_digest(
            domain=_DELIVERY_ATTEMPT_DOMAIN,
            identity=identity,
            stored_digest=mapping["delivery_attempt_digest"],
        )
        result = DevelopmentDeliveryAttemptRowValue._from_validated(
            (
                delivery_envelope,
                delivery_kind,
                delivery_number,
                predecessor,
                basis_decision_ref,
                recorded_at,
                digest,
            )
        )
    except (_RowValueValidationError, WorkerExecutionValueError):
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_delivery_attempt_row_value_from_row_tuple(
    row: object,
) -> DevelopmentDeliveryAttemptRowValue:
    result, error = _attempt_delivery_attempt(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentDeliveryAttemptRowValue, result)


def _attempt_delivery_head(
    row: object,
) -> tuple[DevelopmentDeliveryHeadRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentDeliveryHeadRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_DELIVERY_HEAD_COLUMNS,
            row=row,
        )
        validated = (
            _require_constant_string(mapping["schema_id"], _DELIVERY_HEAD_SCHEMA),
            _require_safe_ref(mapping["effect_intent_ref"]),
            _require_safe_ref(mapping["program_ref"]),
            _require_safe_ref(mapping["current_delivery_attempt_ref"]),
            _require_nonnegative_integer(mapping["head_revision"]),
            _require_enum(mapping["delivery_state"], _DELIVERY_STATES),
            _require_utc_timestamp(mapping["updated_at"]),
        )
        identity = {
            "schema_id":validated[0],"effect_intent_ref":validated[1],
            "program_ref":validated[2],"current_delivery_attempt_ref":validated[3],
            "head_revision":validated[4],"delivery_state":validated[5],"updated_at":validated[6],
        }
        digest = _require_matching_digest(
            domain=_DELIVERY_HEAD_DOMAIN,
            identity=identity,
            stored_digest=mapping["head_digest"],
        )
        result = DevelopmentDeliveryHeadRowValue._from_validated(validated + (digest,))
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_delivery_head_row_value_from_row_tuple(
    row: object,
) -> DevelopmentDeliveryHeadRowValue:
    result, error = _attempt_delivery_head(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentDeliveryHeadRowValue, result)
