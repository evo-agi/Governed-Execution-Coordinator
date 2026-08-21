"""Private immutable C2B2 development-reader query and result contracts."""

from __future__ import annotations

import typing

from . import _development_decision_row_values as _decision_rows
from . import _development_effect_row_values as _effect_rows
from . import _development_program_row_values as _program_rows
from . import _development_row_value_support as _row_support


_DEVELOPMENT_DECISION_COLUMNS = _decision_rows._DEVELOPMENT_DECISION_COLUMNS
_DEVELOPMENT_MUTATION_RECEIPT_COLUMNS = (
    _decision_rows._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS
)
DevelopmentDecisionRowValue = _decision_rows.DevelopmentDecisionRowValue

_DEVELOPMENT_ATTEMPT_FENCE_COLUMNS = _effect_rows._DEVELOPMENT_ATTEMPT_FENCE_COLUMNS
_DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS = (
    _effect_rows._DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS
)
_DEVELOPMENT_AUTHOR_COMMAND_COLUMNS = _effect_rows._DEVELOPMENT_AUTHOR_COMMAND_COLUMNS
_DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS = (
    _effect_rows._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS
)
_DEVELOPMENT_DELIVERY_HEAD_COLUMNS = _effect_rows._DEVELOPMENT_DELIVERY_HEAD_COLUMNS
_DEVELOPMENT_EFFECT_FENCE_COLUMNS = _effect_rows._DEVELOPMENT_EFFECT_FENCE_COLUMNS
_DEVELOPMENT_EFFECT_HEAD_COLUMNS = _effect_rows._DEVELOPMENT_EFFECT_HEAD_COLUMNS
_DEVELOPMENT_EFFECT_INTENT_COLUMNS = _effect_rows._DEVELOPMENT_EFFECT_INTENT_COLUMNS
DevelopmentAttemptFenceRowValue = _effect_rows.DevelopmentAttemptFenceRowValue
DevelopmentAuthorCommandRowValue = _effect_rows.DevelopmentAuthorCommandRowValue
DevelopmentDeliveryAttemptRowValue = _effect_rows.DevelopmentDeliveryAttemptRowValue
DevelopmentDeliveryHeadRowValue = _effect_rows.DevelopmentDeliveryHeadRowValue
DevelopmentEffectFenceRowValue = _effect_rows.DevelopmentEffectFenceRowValue
DevelopmentEffectIntentRowValue = _effect_rows.DevelopmentEffectIntentRowValue

_DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS = (
    _program_rows._DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS
)
_DEVELOPMENT_PROGRAM_HEAD_COLUMNS = _program_rows._DEVELOPMENT_PROGRAM_HEAD_COLUMNS
_DEVELOPMENT_PROGRAM_VERSION_COLUMNS = _program_rows._DEVELOPMENT_PROGRAM_VERSION_COLUMNS
_DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS = (
    _program_rows._DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS
)
_DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS = (
    _program_rows._DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS
)
_DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS = _program_rows._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS
_DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS = (
    _program_rows._DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS
)
_DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS = (
    _program_rows._DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS
)
DevelopmentProgramHeadRowValue = _program_rows.DevelopmentProgramHeadRowValue
DevelopmentProgramVersionRowValue = _program_rows.DevelopmentProgramVersionRowValue
DevelopmentProgramVersionWorkItemRowValue = (
    _program_rows.DevelopmentProgramVersionWorkItemRowValue
)
DevelopmentSemanticAttemptRowValue = _program_rows.DevelopmentSemanticAttemptRowValue
DevelopmentWorkItemHeadRowValue = _program_rows.DevelopmentWorkItemHeadRowValue
DevelopmentWorkItemRevisionRowValue = _program_rows.DevelopmentWorkItemRevisionRowValue

_ImmutableValue = _row_support._ImmutableValue


__all__: tuple[str, ...] = ()


class _DevelopmentSelectSpecification(_ImmutableValue):
    __slots__ = ("_values",)

    @property
    def query_id(self) -> str:
        return typing.cast(str, self._values[0])

    @property
    def sql(self) -> str:
        return typing.cast(str, self._values[1])

    @property
    def row_columns(self) -> tuple[str, ...]:
        return typing.cast(tuple[str, ...], self._values[2])

    @property
    def parameter_order(self) -> tuple[str, ...]:
        return typing.cast(tuple[str, ...], self._values[3])

    @property
    def fetch_limit(self) -> int:
        return typing.cast(int, self._values[4])

    @classmethod
    def _from_literal(
        cls,
        query_id: str,
        sql: str,
        row_columns: tuple[str, ...],
        parameter_order: tuple[str, ...],
        fetch_limit: int,
    ) -> _DevelopmentSelectSpecification:
        if (
            type(query_id) is not str
            or not query_id
            or type(sql) is not str
            or not sql
            or type(row_columns) is not tuple
            or not row_columns
            or any(type(column) is not str or not column for column in row_columns)
            or type(parameter_order) is not tuple
            or any(type(parameter) is not str or not parameter for parameter in parameter_order)
            or type(fetch_limit) is not int
            or fetch_limit not in (2, 257)
        ):
            raise TypeError("invalid literal query specification")
        result = object.__new__(cls)
        object.__setattr__(
            result,
            "_values",
            (query_id, sql, row_columns, parameter_order, fetch_limit),
        )
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentProgramHeadAndCurrentVersionRead(_ImmutableValue):
    __slots__ = ("_values",)

    @property
    def program_head(self) -> DevelopmentProgramHeadRowValue:
        return typing.cast(DevelopmentProgramHeadRowValue, self._values[0])

    @property
    def current_program_version(self) -> DevelopmentProgramVersionRowValue:
        return typing.cast(DevelopmentProgramVersionRowValue, self._values[1])

    @classmethod
    def _from_validated(
        cls,
        program_head: DevelopmentProgramHeadRowValue,
        current_program_version: DevelopmentProgramVersionRowValue,
    ) -> DevelopmentProgramHeadAndCurrentVersionRead:
        if (
            type(program_head) is not DevelopmentProgramHeadRowValue
            or type(current_program_version) is not DevelopmentProgramVersionRowValue
        ):
            raise TypeError("invalid aggregate value")
        result = object.__new__(cls)
        object.__setattr__(result, "_values", (program_head, current_program_version))
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentInitializeDecisionAndResultingVersionRead(_ImmutableValue):
    __slots__ = ("_values",)

    @property
    def initialize_decision(self) -> DevelopmentDecisionRowValue:
        return typing.cast(DevelopmentDecisionRowValue, self._values[0])

    @property
    def resulting_program_version(self) -> DevelopmentProgramVersionRowValue:
        return typing.cast(DevelopmentProgramVersionRowValue, self._values[1])

    @classmethod
    def _from_validated(
        cls,
        initialize_decision: DevelopmentDecisionRowValue,
        resulting_program_version: DevelopmentProgramVersionRowValue,
    ) -> DevelopmentInitializeDecisionAndResultingVersionRead:
        if (
            type(initialize_decision) is not DevelopmentDecisionRowValue
            or type(resulting_program_version) is not DevelopmentProgramVersionRowValue
        ):
            raise TypeError("invalid aggregate value")
        result = object.__new__(cls)
        object.__setattr__(result, "_values", (initialize_decision, resulting_program_version))
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentWorkItemHeadAndRevisionRead(_ImmutableValue):
    __slots__ = ("_values",)

    @property
    def work_item_head(self) -> DevelopmentWorkItemHeadRowValue:
        return typing.cast(DevelopmentWorkItemHeadRowValue, self._values[0])

    @property
    def work_item_revision(self) -> DevelopmentWorkItemRevisionRowValue:
        return typing.cast(DevelopmentWorkItemRevisionRowValue, self._values[1])

    @property
    def is_current(self) -> bool:
        return typing.cast(bool, self._values[2])

    @classmethod
    def _from_validated(
        cls,
        work_item_head: DevelopmentWorkItemHeadRowValue,
        work_item_revision: DevelopmentWorkItemRevisionRowValue,
        is_current: bool,
    ) -> DevelopmentWorkItemHeadAndRevisionRead:
        if (
            type(work_item_head) is not DevelopmentWorkItemHeadRowValue
            or type(work_item_revision) is not DevelopmentWorkItemRevisionRowValue
            or type(is_current) is not bool
        ):
            raise TypeError("invalid aggregate value")
        result = object.__new__(cls)
        object.__setattr__(result, "_values", (work_item_head, work_item_revision, is_current))
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentProgramVersionMembershipEntry(_ImmutableValue):
    __slots__ = ("_values",)

    @property
    def membership(self) -> DevelopmentProgramVersionWorkItemRowValue:
        return typing.cast(DevelopmentProgramVersionWorkItemRowValue, self._values[0])

    @property
    def work_item_revision(self) -> DevelopmentWorkItemRevisionRowValue:
        return typing.cast(DevelopmentWorkItemRevisionRowValue, self._values[1])

    @classmethod
    def _from_validated(
        cls,
        membership: DevelopmentProgramVersionWorkItemRowValue,
        work_item_revision: DevelopmentWorkItemRevisionRowValue,
    ) -> DevelopmentProgramVersionMembershipEntry:
        if (
            type(membership) is not DevelopmentProgramVersionWorkItemRowValue
            or type(work_item_revision) is not DevelopmentWorkItemRevisionRowValue
        ):
            raise TypeError("invalid aggregate value")
        result = object.__new__(cls)
        object.__setattr__(result, "_values", (membership, work_item_revision))
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentProgramVersionMembershipRead(_ImmutableValue):
    __slots__ = ("_values",)

    @property
    def program_version(self) -> DevelopmentProgramVersionRowValue:
        return typing.cast(DevelopmentProgramVersionRowValue, self._values[0])

    @property
    def entries(self) -> tuple[DevelopmentProgramVersionMembershipEntry, ...]:
        return typing.cast(tuple[DevelopmentProgramVersionMembershipEntry, ...], self._values[1])

    @classmethod
    def _from_validated(
        cls,
        program_version: DevelopmentProgramVersionRowValue,
        entries: tuple[DevelopmentProgramVersionMembershipEntry, ...],
    ) -> DevelopmentProgramVersionMembershipRead:
        if (
            type(program_version) is not DevelopmentProgramVersionRowValue
            or type(entries) is not tuple
            or not entries
            or any(type(entry) is not DevelopmentProgramVersionMembershipEntry for entry in entries)
        ):
            raise TypeError("invalid aggregate value")
        result = object.__new__(cls)
        object.__setattr__(result, "_values", (program_version, entries))
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentAttemptFenceCommandEffectRead(_ImmutableValue):
    __slots__ = ("_values",)

    @property
    def semantic_attempt(self) -> DevelopmentSemanticAttemptRowValue:
        return typing.cast(DevelopmentSemanticAttemptRowValue, self._values[0])

    @property
    def effect_intent(self) -> DevelopmentEffectIntentRowValue:
        return typing.cast(DevelopmentEffectIntentRowValue, self._values[1])

    @property
    def author_command(self) -> DevelopmentAuthorCommandRowValue:
        return typing.cast(DevelopmentAuthorCommandRowValue, self._values[2])

    @property
    def attempt_fence(self) -> DevelopmentAttemptFenceRowValue:
        return typing.cast(DevelopmentAttemptFenceRowValue, self._values[3])

    @property
    def current_effect_fence(self) -> DevelopmentEffectFenceRowValue:
        return typing.cast(DevelopmentEffectFenceRowValue, self._values[4])

    @property
    def author_effect_fence(self) -> DevelopmentEffectFenceRowValue:
        return typing.cast(DevelopmentEffectFenceRowValue, self._values[5])

    @classmethod
    def _from_validated(
        cls,
        semantic_attempt: DevelopmentSemanticAttemptRowValue,
        effect_intent: DevelopmentEffectIntentRowValue,
        author_command: DevelopmentAuthorCommandRowValue,
        attempt_fence: DevelopmentAttemptFenceRowValue,
        current_effect_fence: DevelopmentEffectFenceRowValue,
        author_effect_fence: DevelopmentEffectFenceRowValue,
    ) -> DevelopmentAttemptFenceCommandEffectRead:
        if (
            type(semantic_attempt) is not DevelopmentSemanticAttemptRowValue
            or type(effect_intent) is not DevelopmentEffectIntentRowValue
            or type(author_command) is not DevelopmentAuthorCommandRowValue
            or type(attempt_fence) is not DevelopmentAttemptFenceRowValue
            or type(current_effect_fence) is not DevelopmentEffectFenceRowValue
            or type(author_effect_fence) is not DevelopmentEffectFenceRowValue
        ):
            raise TypeError("invalid aggregate value")
        result = object.__new__(cls)
        object.__setattr__(
            result,
            "_values",
            (
                semantic_attempt,
                effect_intent,
                author_command,
                attempt_fence,
                current_effect_fence,
                author_effect_fence,
            ),
        )
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentDeliveryHeadAndCurrentAttemptRead(_ImmutableValue):
    __slots__ = ("_values",)

    @property
    def delivery_head(self) -> DevelopmentDeliveryHeadRowValue:
        return typing.cast(DevelopmentDeliveryHeadRowValue, self._values[0])

    @property
    def current_delivery_attempt(self) -> DevelopmentDeliveryAttemptRowValue:
        return typing.cast(DevelopmentDeliveryAttemptRowValue, self._values[1])

    @classmethod
    def _from_validated(
        cls,
        delivery_head: DevelopmentDeliveryHeadRowValue,
        current_delivery_attempt: DevelopmentDeliveryAttemptRowValue,
    ) -> DevelopmentDeliveryHeadAndCurrentAttemptRead:
        if (
            type(delivery_head) is not DevelopmentDeliveryHeadRowValue
            or type(current_delivery_attempt) is not DevelopmentDeliveryAttemptRowValue
        ):
            raise TypeError("invalid aggregate value")
        result = object.__new__(cls)
        object.__setattr__(result, "_values", (delivery_head, current_delivery_attempt))
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


_MUTATION_RECEIPT_SELECT = _DevelopmentSelectSpecification._from_literal(
    "mutation_receipt",
    "SELECT schema_id, mutation_ref, mutation_family, command_schema_id, command_digest, program_ref, decision_ref, result_program_version_ref, result_semantic_attempt_ref, result_effect_intent_ref, result_effect_fence_ref, result_delivery_attempt_ref, result_observation_ref, result_decision_ref, result_class, result_projection_digest, mutation_graph_digest, outcome, committed_at FROM development_mutation_receipts WHERE mutation_ref = ? LIMIT 2",
    _DEVELOPMENT_MUTATION_RECEIPT_COLUMNS,
    ("mutation_ref",),
    2,
)
_DECISION_SELECT = _DevelopmentSelectSpecification._from_literal(
    "decision",
    "SELECT schema_id, mutation_ref, decision_ref, program_ref, decision_kind, decision_variant, basis_decision_ref, basis_program_version_ref, basis_program_version_number, expected_program_head_revision, resulting_program_version_ref, resulting_program_version_number, selected_semantic_attempt_ref, selected_candidate_ref, selected_attempt_fence_ref, selected_attempt_fence_digest, target_effect_intent_ref, target_effect_class, target_effect_fence_ref, target_effect_fence_digest, expected_target_effect_head_revision, target_delivery_attempt_ref, originating_command_ref, originating_command_digest, target_capsule_manifest_ref, target_portable_capsule_digest, coding_global_stop_ref, coding_global_stop_version, source_directive_ref, source_directive_digest, source_evidence_ref, source_evidence_digest, preassigned_semantic_attempt_ref, preassigned_candidate_ref, preassigned_effect_intent_ref, preassigned_effect_fence_ref, preassigned_delivery_attempt_ref, resulting_accepted_intent_revision_ref, resulting_work_item_ref, resulting_work_item_revision_ref, reason_code, decided_at, decision_digest FROM development_decisions WHERE decision_ref = ? LIMIT 2",
    _DEVELOPMENT_DECISION_COLUMNS,
    ("decision_ref",),
    2,
)
_PROGRAM_HEAD_SELECT = _DevelopmentSelectSpecification._from_literal(
    "program_head",
    "SELECT schema_id, program_ref, current_program_version_ref, current_program_version_number, head_revision, program_state, updated_at, head_digest FROM development_program_heads WHERE program_ref = ? LIMIT 2",
    _DEVELOPMENT_PROGRAM_HEAD_COLUMNS,
    ("program_ref",),
    2,
)
_CURRENT_PROGRAM_VERSION_SELECT = _DevelopmentSelectSpecification._from_literal(
    "current_program_version",
    "SELECT schema_id, program_version_ref, program_ref, program_version_number, program_version_kind, creating_decision_ref, accepted_intent_revision_ref, created_at, program_version_digest FROM development_program_versions WHERE program_ref = ? AND program_version_ref = ? AND program_version_number = ? LIMIT 2",
    _DEVELOPMENT_PROGRAM_VERSION_COLUMNS,
    ("program_ref", "program_head.current_program_version_ref", "program_head.current_program_version_number"),
    2,
)
_INITIALIZE_DECISION_SELECT = _DevelopmentSelectSpecification._from_literal(
    "initialize_decision",
    "SELECT schema_id, mutation_ref, decision_ref, program_ref, decision_kind, decision_variant, basis_decision_ref, basis_program_version_ref, basis_program_version_number, expected_program_head_revision, resulting_program_version_ref, resulting_program_version_number, selected_semantic_attempt_ref, selected_candidate_ref, selected_attempt_fence_ref, selected_attempt_fence_digest, target_effect_intent_ref, target_effect_class, target_effect_fence_ref, target_effect_fence_digest, expected_target_effect_head_revision, target_delivery_attempt_ref, originating_command_ref, originating_command_digest, target_capsule_manifest_ref, target_portable_capsule_digest, coding_global_stop_ref, coding_global_stop_version, source_directive_ref, source_directive_digest, source_evidence_ref, source_evidence_digest, preassigned_semantic_attempt_ref, preassigned_candidate_ref, preassigned_effect_intent_ref, preassigned_effect_fence_ref, preassigned_delivery_attempt_ref, resulting_accepted_intent_revision_ref, resulting_work_item_ref, resulting_work_item_revision_ref, reason_code, decided_at, decision_digest FROM development_decisions WHERE program_ref = ? AND decision_ref = ? LIMIT 2",
    _DEVELOPMENT_DECISION_COLUMNS,
    ("program_ref", "decision_ref"),
    2,
)
_RESULTING_PROGRAM_VERSION_SELECT = _DevelopmentSelectSpecification._from_literal(
    "resulting_program_version",
    "SELECT schema_id, program_version_ref, program_ref, program_version_number, program_version_kind, creating_decision_ref, accepted_intent_revision_ref, created_at, program_version_digest FROM development_program_versions WHERE program_ref = ? AND program_version_ref = ? AND program_version_number = ? LIMIT 2",
    _DEVELOPMENT_PROGRAM_VERSION_COLUMNS,
    ("program_ref", "initialize_decision.resulting_program_version_ref", "initialize_decision.resulting_program_version_number"),
    2,
)
_ACCEPTED_INTENT_REVISION_SELECT = _DevelopmentSelectSpecification._from_literal(
    "accepted_intent_revision",
    "SELECT schema_id, accepted_intent_revision_ref, program_ref, accepted_intent_revision_number, prior_accepted_intent_revision_ref, source_intent_ref, source_intent_digest, safe_projection_digest, created_at, accepted_intent_revision_digest FROM development_accepted_intent_revisions WHERE program_ref = ? AND accepted_intent_revision_ref = ? LIMIT 2",
    _DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS,
    ("program_ref", "accepted_intent_revision_ref"),
    2,
)
_WORK_ITEM_HEAD_SELECT = _DevelopmentSelectSpecification._from_literal(
    "work_item_head",
    "SELECT schema_id, work_item_ref, program_ref, current_work_item_revision_ref, current_work_item_revision_number, head_revision, work_state, updated_at, head_digest FROM development_work_item_heads WHERE program_ref = ? AND work_item_ref = ? LIMIT 2",
    _DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS,
    ("program_ref", "work_item_ref"),
    2,
)
_WORK_ITEM_REVISION_SELECT = _DevelopmentSelectSpecification._from_literal(
    "work_item_revision",
    "SELECT schema_id, work_item_revision_ref, program_ref, work_item_ref, work_item_revision_number, work_item_revision_kind, prior_work_item_revision_ref, accepted_intent_revision_ref, created_at, work_item_revision_digest FROM development_work_item_revisions WHERE program_ref = ? AND work_item_ref = ? AND work_item_revision_ref = ? LIMIT 2",
    _DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS,
    ("program_ref", "work_item_ref", "work_item_revision_ref"),
    2,
)
_PROGRAM_VERSION_ROOT_SELECT = _DevelopmentSelectSpecification._from_literal(
    "program_version_root",
    "SELECT schema_id, program_version_ref, program_ref, program_version_number, program_version_kind, creating_decision_ref, accepted_intent_revision_ref, created_at, program_version_digest FROM development_program_versions WHERE program_ref = ? AND program_version_ref = ? LIMIT 2",
    _DEVELOPMENT_PROGRAM_VERSION_COLUMNS,
    ("program_ref", "program_version_ref"),
    2,
)
_MEMBERSHIP_FIRST_PAGE_SELECT = _DevelopmentSelectSpecification._from_literal(
    "membership_first_page",
    "SELECT schema_id, program_ref, program_version_ref, work_item_ref, work_item_revision_ref, membership_ordinal, created_at, membership_digest FROM development_program_version_work_items WHERE program_ref = ? AND program_version_ref = ? ORDER BY membership_ordinal ASC, work_item_ref ASC LIMIT 257",
    _DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS,
    ("program_ref", "program_version_ref"),
    257,
)
_MEMBERSHIP_CONTINUATION_PAGE_SELECT = _DevelopmentSelectSpecification._from_literal(
    "membership_continuation_page",
    "SELECT schema_id, program_ref, program_version_ref, work_item_ref, work_item_revision_ref, membership_ordinal, created_at, membership_digest FROM development_program_version_work_items WHERE program_ref = ? AND program_version_ref = ? AND (membership_ordinal > ? OR (membership_ordinal = ? AND work_item_ref > ?)) ORDER BY membership_ordinal ASC, work_item_ref ASC LIMIT 257",
    _DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS,
    ("program_ref", "program_version_ref", "after_membership_ordinal", "after_membership_ordinal", "after_work_item_ref"),
    257,
)
_MEMBERSHIP_WORK_ITEM_REVISION_SELECT = _DevelopmentSelectSpecification._from_literal(
    "membership_work_item_revision",
    "SELECT schema_id, work_item_revision_ref, program_ref, work_item_ref, work_item_revision_number, work_item_revision_kind, prior_work_item_revision_ref, accepted_intent_revision_ref, created_at, work_item_revision_digest FROM development_work_item_revisions WHERE program_ref = ? AND work_item_ref = ? AND work_item_revision_ref = ? LIMIT 2",
    _DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS,
    ("program_ref", "membership.work_item_ref", "membership.work_item_revision_ref"),
    2,
)
_WORK_SPEC_SAFE_BINDING_SELECT = _DevelopmentSelectSpecification._from_literal(
    "work_spec_safe_binding",
    "SELECT schema_id, work_spec_ref, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, repository_ref, base_git_object_format, base_git_oid, authorized_paths_json, validation_requirement_ref, review_requirement_ref, privacy_classification, work_spec_digest, safe_projection_digest, recorded_at, work_spec_binding_digest FROM development_work_spec_bindings WHERE program_ref = ? AND program_version_ref = ? AND work_item_ref = ? AND work_item_revision_ref = ? LIMIT 2",
    _DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS,
    ("program_ref", "program_version_ref", "work_item_ref", "work_item_revision_ref"),
    2,
)
_EFFECT_INTENT_ROOT_SELECT = _DevelopmentSelectSpecification._from_literal(
    "effect_intent_root",
    "SELECT schema_id, effect_intent_ref, program_ref, program_version_ref, semantic_attempt_ref, effect_class, candidate_ref, command_ref, basis_decision_ref, cancellation_target_effect_intent_ref, expected_target_effect_head_revision, portable_capsule_digest, created_at, effect_intent_digest FROM development_effect_intents WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2",
    _DEVELOPMENT_EFFECT_INTENT_COLUMNS,
    ("program_ref", "effect_intent_ref"),
    2,
)
_SEMANTIC_ATTEMPT_SELECT = _DevelopmentSelectSpecification._from_literal(
    "semantic_attempt",
    "SELECT schema_id, semantic_attempt_ref, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, attempt_number, candidate_ref, attempt_phase, selection_decision_ref, created_at, semantic_attempt_digest FROM development_semantic_attempts WHERE program_ref = ? AND semantic_attempt_ref = ? LIMIT 2",
    _DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS,
    ("program_ref", "semantic_attempt_ref"),
    2,
)
_AUTHOR_COMMAND_SELECT = _DevelopmentSelectSpecification._from_literal(
    "author_command",
    "SELECT schema_id, command_ref, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, semantic_attempt_ref, effect_intent_ref, effect_class, candidate_ref, repository_ref, base_git_object_format, base_git_oid, path_ceiling_json, work_spec_ref, work_spec_digest, standing_grant_ref, standing_grant_digest, attempt_authorization_ref, attempt_authorization_digest, effect_authorization_ref, effect_authorization_digest, attempt_fence_ref, attempt_fence_digest, effect_fence_ref, effect_fence_digest, global_stop_ref, global_stop_version, validation_requirement_ref, validation_requirement_digest, review_requirement_ref, review_requirement_digest, capsule_schema_id, capsule_profile_ref, effect_max_active_invocations, effect_max_candidate_bytes, effect_max_changed_files, effect_max_cost_microusd, effect_max_cpu_seconds, effect_max_deliveries, effect_max_deployments, effect_max_local_commits, effect_max_memory_bytes, effect_max_merges, effect_max_model_input_tokens, effect_max_model_output_tokens, effect_max_pull_requests, effect_max_pushes, effect_max_wall_seconds, privacy_classification, redaction_profile_ref, command_digest, recorded_at FROM development_author_commands WHERE program_ref = ? AND command_ref = ? LIMIT 2",
    _DEVELOPMENT_AUTHOR_COMMAND_COLUMNS,
    ("program_ref", "effect_intent.command_ref"),
    2,
)
_ATTEMPT_FENCE_SELECT = _DevelopmentSelectSpecification._from_literal(
    "attempt_fence",
    "SELECT schema_id, attempt_fence_ref, parent_standing_grant_ref, parent_standing_grant_digest, attempt_authorization_ref, attempt_authorization_digest, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, semantic_attempt_ref, repository_ref, base_git_object_format, base_git_oid, path_ceiling_json, allowed_effect_class_mask, aggregate_max_active_invocations, aggregate_max_candidate_bytes, aggregate_max_changed_files, aggregate_max_cost_microusd, aggregate_max_cpu_seconds, aggregate_max_deliveries, aggregate_max_deployments, aggregate_max_local_commits, aggregate_max_memory_bytes, aggregate_max_merges, aggregate_max_model_input_tokens, aggregate_max_model_output_tokens, aggregate_max_pull_requests, aggregate_max_pushes, aggregate_max_wall_seconds, expires_at, global_stop_ref, global_stop_version, attempt_fence_digest, recorded_at FROM development_attempt_fences WHERE program_ref = ? AND attempt_fence_ref = ? LIMIT 2",
    _DEVELOPMENT_ATTEMPT_FENCE_COLUMNS,
    ("program_ref", "author_command.attempt_fence_ref"),
    2,
)
_CURRENT_EFFECT_FENCE_SELECT = _DevelopmentSelectSpecification._from_literal(
    "current_effect_fence",
    "SELECT schema_id, effect_fence_ref, parent_standing_grant_ref, parent_standing_grant_digest, effect_authorization_ref, effect_authorization_digest, attempt_fence_ref, attempt_fence_digest, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, semantic_attempt_ref, effect_intent_ref, effect_class, command_ref, command_digest, candidate_ref, repository_ref, base_git_object_format, base_git_oid, path_ceiling_json, effect_max_active_invocations, effect_max_candidate_bytes, effect_max_changed_files, effect_max_cost_microusd, effect_max_cpu_seconds, effect_max_deliveries, effect_max_deployments, effect_max_local_commits, effect_max_memory_bytes, effect_max_merges, effect_max_model_input_tokens, effect_max_model_output_tokens, effect_max_pull_requests, effect_max_pushes, effect_max_wall_seconds, expires_at, global_stop_ref, global_stop_version, portable_capsule_digest, cancellation_target_effect_intent_ref, cancellation_target_effect_fence_ref, cancellation_target_effect_fence_digest, effect_fence_digest, recorded_at FROM development_effect_fences WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2",
    _DEVELOPMENT_EFFECT_FENCE_COLUMNS,
    ("program_ref", "effect_intent_ref"),
    2,
)
_AUTHOR_EFFECT_FENCE_SELECT = _DevelopmentSelectSpecification._from_literal(
    "author_effect_fence",
    "SELECT schema_id, effect_fence_ref, parent_standing_grant_ref, parent_standing_grant_digest, effect_authorization_ref, effect_authorization_digest, attempt_fence_ref, attempt_fence_digest, program_ref, program_version_ref, accepted_intent_revision_ref, work_item_ref, work_item_revision_ref, semantic_attempt_ref, effect_intent_ref, effect_class, command_ref, command_digest, candidate_ref, repository_ref, base_git_object_format, base_git_oid, path_ceiling_json, effect_max_active_invocations, effect_max_candidate_bytes, effect_max_changed_files, effect_max_cost_microusd, effect_max_cpu_seconds, effect_max_deliveries, effect_max_deployments, effect_max_local_commits, effect_max_memory_bytes, effect_max_merges, effect_max_model_input_tokens, effect_max_model_output_tokens, effect_max_pull_requests, effect_max_pushes, effect_max_wall_seconds, expires_at, global_stop_ref, global_stop_version, portable_capsule_digest, cancellation_target_effect_intent_ref, cancellation_target_effect_fence_ref, cancellation_target_effect_fence_digest, effect_fence_digest, recorded_at FROM development_effect_fences WHERE program_ref = ? AND effect_fence_ref = ? LIMIT 2",
    _DEVELOPMENT_EFFECT_FENCE_COLUMNS,
    ("program_ref", "author_command.effect_fence_ref"),
    2,
)
_AUTHORITY_EVALUATION_SELECT = _DevelopmentSelectSpecification._from_literal(
    "authority_evaluation",
    "SELECT schema_id, authority_evaluation_ref, program_ref, evaluation_scope, evaluation_subject_ref, semantic_attempt_ref, effect_intent_ref, authority_ref, authority_digest, authority_state, reason_code, expires_at, evaluated_at, authority_evaluation_digest FROM development_authority_evaluations WHERE program_ref = ? AND authority_evaluation_ref = ? LIMIT 2",
    _DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS,
    ("program_ref", "authority_evaluation_ref"),
    2,
)
_EFFECT_HEAD_SELECT = _DevelopmentSelectSpecification._from_literal(
    "effect_head",
    "SELECT schema_id, effect_intent_ref, program_ref, current_effect_fence_ref, head_revision, effect_state, cancellation_effect_intent_ref, updated_at, head_digest FROM development_effect_heads WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2",
    _DEVELOPMENT_EFFECT_HEAD_COLUMNS,
    ("program_ref", "effect_intent_ref"),
    2,
)
_DELIVERY_HEAD_SELECT = _DevelopmentSelectSpecification._from_literal(
    "delivery_head",
    "SELECT schema_id, effect_intent_ref, program_ref, current_delivery_attempt_ref, head_revision, delivery_state, updated_at, head_digest FROM development_delivery_heads WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2",
    _DEVELOPMENT_DELIVERY_HEAD_COLUMNS,
    ("program_ref", "effect_intent_ref"),
    2,
)
_CURRENT_DELIVERY_ATTEMPT_SELECT = _DevelopmentSelectSpecification._from_literal(
    "current_delivery_attempt",
    "SELECT schema_id, delivery_attempt_ref, program_ref, program_version_ref, command_ref, command_digest, semantic_attempt_ref, effect_intent_ref, attempt_fence_ref, attempt_fence_digest, effect_fence_ref, effect_fence_digest, adapter_kind, adapter_safe_correlation_ref, delivery_envelope_digest, delivery_kind, delivery_number, predecessor_delivery_attempt_ref, basis_decision_ref, recorded_at, delivery_attempt_digest FROM development_delivery_attempts WHERE program_ref = ? AND effect_intent_ref = ? AND delivery_attempt_ref = ? LIMIT 2",
    _DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS,
    ("program_ref", "effect_intent_ref", "delivery_head.current_delivery_attempt_ref"),
    2,
)
