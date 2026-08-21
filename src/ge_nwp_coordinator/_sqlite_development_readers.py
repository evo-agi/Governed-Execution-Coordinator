"""Private, production-unintegrated C2B2 development-state SELECT readers."""

from __future__ import annotations

import typing

from . import _development_decision_row_values as _decision_rows
from . import _development_effect_row_values as _effect_rows
from . import _development_program_row_values as _program_rows
from . import _development_row_value_support as _row_support
from ._sqlite_development_reader_contracts import (
    _ACCEPTED_INTENT_REVISION_SELECT,
    _ATTEMPT_FENCE_SELECT,
    _AUTHORITY_EVALUATION_SELECT,
    _AUTHOR_COMMAND_SELECT,
    _AUTHOR_EFFECT_FENCE_SELECT,
    _CURRENT_DELIVERY_ATTEMPT_SELECT,
    _CURRENT_EFFECT_FENCE_SELECT,
    _CURRENT_PROGRAM_VERSION_SELECT,
    _DECISION_SELECT,
    _DELIVERY_HEAD_SELECT,
    _EFFECT_HEAD_SELECT,
    _EFFECT_INTENT_ROOT_SELECT,
    _INITIALIZE_DECISION_SELECT,
    _MEMBERSHIP_CONTINUATION_PAGE_SELECT,
    _MEMBERSHIP_FIRST_PAGE_SELECT,
    _MEMBERSHIP_WORK_ITEM_REVISION_SELECT,
    _MUTATION_RECEIPT_SELECT,
    _PROGRAM_HEAD_SELECT,
    _PROGRAM_VERSION_ROOT_SELECT,
    _RESULTING_PROGRAM_VERSION_SELECT,
    _SEMANTIC_ATTEMPT_SELECT,
    _WORK_ITEM_HEAD_SELECT,
    _WORK_ITEM_REVISION_SELECT,
    _WORK_SPEC_SAFE_BINDING_SELECT,
    DevelopmentAttemptFenceCommandEffectRead,
    DevelopmentDeliveryHeadAndCurrentAttemptRead,
    DevelopmentInitializeDecisionAndResultingVersionRead,
    DevelopmentProgramHeadAndCurrentVersionRead,
    DevelopmentProgramVersionMembershipEntry,
    DevelopmentProgramVersionMembershipRead,
    DevelopmentWorkItemHeadAndRevisionRead,
)
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from .sqlite_transition_select_support import (
    _MutationReadCapabilityError,
    _MutationReadCapabilityFailureReason,
    _database_integrity_failure,
    _execute_select_fetch_bounded,
    _mutation_failed,
)


DevelopmentDecisionRowValue = _decision_rows.DevelopmentDecisionRowValue
DevelopmentMutationReceiptRowValue = _decision_rows.DevelopmentMutationReceiptRowValue
development_decision_row_value_from_row_tuple = (
    _decision_rows.development_decision_row_value_from_row_tuple
)
development_mutation_receipt_row_value_from_row_tuple = (
    _decision_rows.development_mutation_receipt_row_value_from_row_tuple
)

DevelopmentAttemptFenceRowValue = _effect_rows.DevelopmentAttemptFenceRowValue
DevelopmentAuthorityEvaluationRowValue = (
    _effect_rows.DevelopmentAuthorityEvaluationRowValue
)
DevelopmentAuthorCommandRowValue = _effect_rows.DevelopmentAuthorCommandRowValue
DevelopmentDeliveryAttemptRowValue = _effect_rows.DevelopmentDeliveryAttemptRowValue
DevelopmentDeliveryHeadRowValue = _effect_rows.DevelopmentDeliveryHeadRowValue
DevelopmentEffectFenceRowValue = _effect_rows.DevelopmentEffectFenceRowValue
DevelopmentEffectHeadRowValue = _effect_rows.DevelopmentEffectHeadRowValue
DevelopmentEffectIntentRowValue = _effect_rows.DevelopmentEffectIntentRowValue
development_attempt_fence_row_value_from_row_tuple = (
    _effect_rows.development_attempt_fence_row_value_from_row_tuple
)
development_author_command_row_value_from_row_tuple = (
    _effect_rows.development_author_command_row_value_from_row_tuple
)
development_authority_evaluation_row_value_from_row_tuple = (
    _effect_rows.development_authority_evaluation_row_value_from_row_tuple
)
development_delivery_attempt_row_value_from_row_tuple = (
    _effect_rows.development_delivery_attempt_row_value_from_row_tuple
)
development_delivery_head_row_value_from_row_tuple = (
    _effect_rows.development_delivery_head_row_value_from_row_tuple
)
development_effect_fence_row_value_from_row_tuple = (
    _effect_rows.development_effect_fence_row_value_from_row_tuple
)
development_effect_head_row_value_from_row_tuple = (
    _effect_rows.development_effect_head_row_value_from_row_tuple
)
development_effect_intent_row_value_from_row_tuple = (
    _effect_rows.development_effect_intent_row_value_from_row_tuple
)

DevelopmentAcceptedIntentRevisionRowValue = (
    _program_rows.DevelopmentAcceptedIntentRevisionRowValue
)
DevelopmentProgramHeadRowValue = _program_rows.DevelopmentProgramHeadRowValue
DevelopmentProgramVersionRowValue = _program_rows.DevelopmentProgramVersionRowValue
DevelopmentProgramVersionWorkItemRowValue = (
    _program_rows.DevelopmentProgramVersionWorkItemRowValue
)
DevelopmentSemanticAttemptRowValue = _program_rows.DevelopmentSemanticAttemptRowValue
DevelopmentWorkItemHeadRowValue = _program_rows.DevelopmentWorkItemHeadRowValue
DevelopmentWorkItemRevisionRowValue = _program_rows.DevelopmentWorkItemRevisionRowValue
DevelopmentWorkSpecBindingRowValue = _program_rows.DevelopmentWorkSpecBindingRowValue
development_accepted_intent_revision_row_value_from_row_tuple = (
    _program_rows.development_accepted_intent_revision_row_value_from_row_tuple
)
development_program_head_row_value_from_row_tuple = (
    _program_rows.development_program_head_row_value_from_row_tuple
)
development_program_version_row_value_from_row_tuple = (
    _program_rows.development_program_version_row_value_from_row_tuple
)
development_program_version_work_item_row_value_from_row_tuple = (
    _program_rows.development_program_version_work_item_row_value_from_row_tuple
)
development_semantic_attempt_row_value_from_row_tuple = (
    _program_rows.development_semantic_attempt_row_value_from_row_tuple
)
development_work_item_head_row_value_from_row_tuple = (
    _program_rows.development_work_item_head_row_value_from_row_tuple
)
development_work_item_revision_row_value_from_row_tuple = (
    _program_rows.development_work_item_revision_row_value_from_row_tuple
)
development_work_spec_binding_row_value_from_row_tuple = (
    _program_rows.development_work_spec_binding_row_value_from_row_tuple
)

_RowValueValidationError = _row_support._RowValueValidationError
_new_database_integrity_error = _row_support._new_database_integrity_error
_require_safe_ref = _row_support._require_safe_ref


__all__: tuple[str, ...] = ()


def _validated_safe_ref(value: object) -> str:
    result: str | None = None
    error: SQLiteMutationStoreError | None = None
    try:
        result = _require_safe_ref(value)
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        value = None
    if error is not None:
        raise error from None
    return typing.cast(str, result)


def _validated_maximum_members(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise _database_integrity_failure() from None
    return value


def _require_nominal_capability(capability: object) -> object:
    from .sqlite_transition_transaction import _SQLiteMutationReadCapability

    if type(capability) is not _SQLiteMutationReadCapability:
        raise _MutationReadCapabilityError(
            _MutationReadCapabilityFailureReason.CAPABILITY_UNAVAILABLE
        ) from None
    return capability


def _optional_single_row(rows: list[object]) -> object | None:
    if len(rows) == 0:
        return None
    if len(rows) != 1:
        raise _database_integrity_failure() from None
    return rows[0]


def _required_single_row(rows: list[object]) -> object:
    if len(rows) != 1:
        raise _database_integrity_failure() from None
    return rows[0]


def _require_relation(condition: bool) -> None:
    if type(condition) is not bool or not condition:
        raise _database_integrity_failure() from None


def _ceilings_are_no_wider(child: object, parent: object) -> bool:
    return bool(
        child.max_active_invocations <= parent.max_active_invocations
        and child.max_candidate_bytes <= parent.max_candidate_bytes
        and child.max_changed_files <= parent.max_changed_files
        and child.max_cost_microusd <= parent.max_cost_microusd
        and child.max_cpu_seconds <= parent.max_cpu_seconds
        and child.max_deliveries <= parent.max_deliveries
        and child.max_deployments <= parent.max_deployments
        and child.max_local_commits <= parent.max_local_commits
        and child.max_memory_bytes <= parent.max_memory_bytes
        and child.max_merges <= parent.max_merges
        and child.max_model_input_tokens <= parent.max_model_input_tokens
        and child.max_model_output_tokens <= parent.max_model_output_tokens
        and child.max_pull_requests <= parent.max_pull_requests
        and child.max_pushes <= parent.max_pushes
        and child.max_wall_seconds <= parent.max_wall_seconds
    )


def _load_development_mutation_receipt_by_mutation_ref(
    capability: object,
    mutation_ref: object,
) -> DevelopmentMutationReceiptRowValue | None:
    mutation_ref = _validated_safe_ref(mutation_ref)
    capability = _require_nominal_capability(capability)
    rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_MUTATION_RECEIPT_SELECT.sql,
        parameters=(mutation_ref,),
        limit=_MUTATION_RECEIPT_SELECT.fetch_limit,
    )
    row = _optional_single_row(rows)
    rows = []
    if row is None:
        return None
    result = development_mutation_receipt_row_value_from_row_tuple(row)
    row = None
    _require_relation(result.mutation_ref == mutation_ref)
    return result


def _load_development_decision_by_decision_ref(
    capability: object,
    decision_ref: object,
) -> DevelopmentDecisionRowValue | None:
    decision_ref = _validated_safe_ref(decision_ref)
    capability = _require_nominal_capability(capability)
    rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_DECISION_SELECT.sql,
        parameters=(decision_ref,),
        limit=_DECISION_SELECT.fetch_limit,
    )
    row = _optional_single_row(rows)
    rows = []
    if row is None:
        return None
    result = development_decision_row_value_from_row_tuple(row)
    row = None
    _require_relation(result.decision_ref == decision_ref)
    return result


def _load_development_program_head_and_current_version(
    capability: object,
    program_ref: object,
) -> DevelopmentProgramHeadAndCurrentVersionRead | None:
    program_ref = _validated_safe_ref(program_ref)
    capability = _require_nominal_capability(capability)
    root_rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_PROGRAM_HEAD_SELECT.sql,
        parameters=(program_ref,),
        limit=_PROGRAM_HEAD_SELECT.fetch_limit,
    )
    root_row = _optional_single_row(root_rows)
    root_rows = []
    if root_row is None:
        return None
    program_head = development_program_head_row_value_from_row_tuple(root_row)
    root_row = None
    _require_relation(program_head.program_ref == program_ref)
    child_rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_CURRENT_PROGRAM_VERSION_SELECT.sql,
        parameters=(
            program_ref,
            program_head.current_program_version_ref,
            program_head.current_program_version_number,
        ),
        limit=_CURRENT_PROGRAM_VERSION_SELECT.fetch_limit,
    )
    child_row = _required_single_row(child_rows)
    child_rows = []
    current_program_version = development_program_version_row_value_from_row_tuple(child_row)
    child_row = None
    _require_relation(
        current_program_version.program_ref == program_ref
        and current_program_version.program_version_ref
        == program_head.current_program_version_ref
        and current_program_version.program_version_number
        == program_head.current_program_version_number
    )
    return DevelopmentProgramHeadAndCurrentVersionRead._from_validated(
        program_head,
        current_program_version,
    )


def _load_development_initialize_decision_and_resulting_version(
    capability: object,
    program_ref: object,
    decision_ref: object,
) -> DevelopmentInitializeDecisionAndResultingVersionRead | None:
    program_ref = _validated_safe_ref(program_ref)
    decision_ref = _validated_safe_ref(decision_ref)
    capability = _require_nominal_capability(capability)
    root_rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_INITIALIZE_DECISION_SELECT.sql,
        parameters=(program_ref, decision_ref),
        limit=_INITIALIZE_DECISION_SELECT.fetch_limit,
    )
    root_row = _optional_single_row(root_rows)
    root_rows = []
    if root_row is None:
        return None
    initialize_decision = development_decision_row_value_from_row_tuple(root_row)
    root_row = None
    _require_relation(
        initialize_decision.program_ref == program_ref
        and initialize_decision.decision_ref == decision_ref
        and initialize_decision.decision_kind == "initialize"
        and initialize_decision.decision_variant == "program_genesis"
        and initialize_decision.basis_decision_ref is None
        and initialize_decision.basis_program_version_ref is None
        and initialize_decision.basis_program_version_number is None
        and initialize_decision.resulting_program_version_ref is not None
        and initialize_decision.resulting_program_version_number is not None
    )
    child_rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_RESULTING_PROGRAM_VERSION_SELECT.sql,
        parameters=(
            program_ref,
            initialize_decision.resulting_program_version_ref,
            initialize_decision.resulting_program_version_number,
        ),
        limit=_RESULTING_PROGRAM_VERSION_SELECT.fetch_limit,
    )
    child_row = _required_single_row(child_rows)
    child_rows = []
    resulting_program_version = development_program_version_row_value_from_row_tuple(child_row)
    child_row = None
    _require_relation(
        resulting_program_version.program_ref == program_ref
        and resulting_program_version.program_version_ref
        == initialize_decision.resulting_program_version_ref
        and resulting_program_version.program_version_number
        == initialize_decision.resulting_program_version_number
        and resulting_program_version.program_version_kind == "initial"
        and resulting_program_version.program_version_number == 1
        and resulting_program_version.creating_decision_ref == decision_ref
    )
    return DevelopmentInitializeDecisionAndResultingVersionRead._from_validated(
        initialize_decision,
        resulting_program_version,
    )


def _load_development_accepted_intent_revision_by_exact_ref(
    capability: object,
    program_ref: object,
    accepted_intent_revision_ref: object,
) -> DevelopmentAcceptedIntentRevisionRowValue | None:
    program_ref = _validated_safe_ref(program_ref)
    accepted_intent_revision_ref = _validated_safe_ref(accepted_intent_revision_ref)
    capability = _require_nominal_capability(capability)
    rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_ACCEPTED_INTENT_REVISION_SELECT.sql,
        parameters=(program_ref, accepted_intent_revision_ref),
        limit=_ACCEPTED_INTENT_REVISION_SELECT.fetch_limit,
    )
    row = _optional_single_row(rows)
    rows = []
    if row is None:
        return None
    result = development_accepted_intent_revision_row_value_from_row_tuple(row)
    row = None
    _require_relation(
        result.program_ref == program_ref
        and result.accepted_intent_revision_ref == accepted_intent_revision_ref
    )
    return result


def _load_development_work_item_head_and_revision_by_exact_ref(
    capability: object,
    program_ref: object,
    work_item_ref: object,
    work_item_revision_ref: object,
) -> DevelopmentWorkItemHeadAndRevisionRead | None:
    program_ref = _validated_safe_ref(program_ref)
    work_item_ref = _validated_safe_ref(work_item_ref)
    work_item_revision_ref = _validated_safe_ref(work_item_revision_ref)
    capability = _require_nominal_capability(capability)
    root_rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_WORK_ITEM_HEAD_SELECT.sql,
        parameters=(program_ref, work_item_ref),
        limit=_WORK_ITEM_HEAD_SELECT.fetch_limit,
    )
    root_row = _optional_single_row(root_rows)
    root_rows = []
    if root_row is None:
        return None
    work_item_head = development_work_item_head_row_value_from_row_tuple(root_row)
    root_row = None
    _require_relation(
        work_item_head.program_ref == program_ref
        and work_item_head.work_item_ref == work_item_ref
    )
    child_rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_WORK_ITEM_REVISION_SELECT.sql,
        parameters=(program_ref, work_item_ref, work_item_revision_ref),
        limit=_WORK_ITEM_REVISION_SELECT.fetch_limit,
    )
    child_row = _required_single_row(child_rows)
    child_rows = []
    work_item_revision = development_work_item_revision_row_value_from_row_tuple(child_row)
    child_row = None
    _require_relation(
        work_item_revision.program_ref == program_ref
        and work_item_revision.work_item_ref == work_item_ref
        and work_item_revision.work_item_revision_ref == work_item_revision_ref
    )
    reference_matches = (
        work_item_head.current_work_item_revision_ref
        == work_item_revision.work_item_revision_ref
    )
    number_matches = (
        work_item_head.current_work_item_revision_number
        == work_item_revision.work_item_revision_number
    )
    _require_relation(reference_matches == number_matches)
    return DevelopmentWorkItemHeadAndRevisionRead._from_validated(
        work_item_head,
        work_item_revision,
        reference_matches and number_matches,
    )


def _load_development_paged_program_version_membership(
    capability: object,
    program_ref: object,
    program_version_ref: object,
    maximum_members: object,
) -> DevelopmentProgramVersionMembershipRead | None:
    program_ref = _validated_safe_ref(program_ref)
    program_version_ref = _validated_safe_ref(program_version_ref)
    maximum_members = _validated_maximum_members(maximum_members)
    capability = _require_nominal_capability(capability)
    root_rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_PROGRAM_VERSION_ROOT_SELECT.sql,
        parameters=(program_ref, program_version_ref),
        limit=_PROGRAM_VERSION_ROOT_SELECT.fetch_limit,
    )
    root_row = _optional_single_row(root_rows)
    root_rows = []
    if root_row is None:
        return None
    program_version = development_program_version_row_value_from_row_tuple(root_row)
    root_row = None
    _require_relation(
        program_version.program_ref == program_ref
        and program_version.program_version_ref == program_version_ref
    )

    memberships: list[DevelopmentProgramVersionWorkItemRowValue] = []
    seen_pairs: set[tuple[int, str]] = set()
    seen_ordinals: set[int] = set()
    seen_work_item_refs: set[str] = set()
    after_ordinal: int | None = None
    after_work_item_ref: str | None = None
    expected_evidence: DevelopmentProgramVersionWorkItemRowValue | None = None
    while after_ordinal is None or expected_evidence is not None:
        if after_ordinal is None:
            page_rows = _execute_select_fetch_bounded(
                capability=capability,
                sql=_MEMBERSHIP_FIRST_PAGE_SELECT.sql,
                parameters=(program_ref, program_version_ref),
                limit=_MEMBERSHIP_FIRST_PAGE_SELECT.fetch_limit,
            )
        else:
            page_rows = _execute_select_fetch_bounded(
                capability=capability,
                sql=_MEMBERSHIP_CONTINUATION_PAGE_SELECT.sql,
                parameters=(
                    program_ref,
                    program_version_ref,
                    after_ordinal,
                    after_ordinal,
                    after_work_item_ref,
                ),
                limit=_MEMBERSHIP_CONTINUATION_PAGE_SELECT.fetch_limit,
            )
        if len(page_rows) > 257:
            raise _database_integrity_failure() from None
        page_values: list[DevelopmentProgramVersionWorkItemRowValue] = []
        for page_row in page_rows:
            page_values.append(
                development_program_version_work_item_row_value_from_row_tuple(page_row)
            )
        page_rows = []
        if expected_evidence is not None:
            _require_relation(bool(page_values) and page_values[0] == expected_evidence)
            expected_evidence = None
        has_more = len(page_values) == 257
        logical_values = page_values[:256] if has_more else page_values
        for membership in logical_values:
            if len(memberships) >= maximum_members:
                raise _mutation_failed() from None
            pair = (membership.membership_ordinal, membership.work_item_ref)
            _require_relation(
                membership.program_ref == program_ref
                and membership.program_version_ref == program_version_ref
                and pair not in seen_pairs
                and membership.membership_ordinal not in seen_ordinals
                and membership.work_item_ref not in seen_work_item_refs
                and membership.membership_ordinal == len(memberships)
                and (not memberships or pair > (
                    memberships[-1].membership_ordinal,
                    memberships[-1].work_item_ref,
                ))
            )
            seen_pairs.add(pair)
            seen_ordinals.add(membership.membership_ordinal)
            seen_work_item_refs.add(membership.work_item_ref)
            memberships.append(membership)
        if not has_more:
            break
        _require_relation(bool(logical_values))
        expected_evidence = page_values[256]
        after_ordinal = logical_values[-1].membership_ordinal
        after_work_item_ref = logical_values[-1].work_item_ref
        page_values = []
    _require_relation(bool(memberships) and expected_evidence is None)

    entries: list[DevelopmentProgramVersionMembershipEntry] = []
    for membership in memberships:
        child_rows = _execute_select_fetch_bounded(
            capability=capability,
            sql=_MEMBERSHIP_WORK_ITEM_REVISION_SELECT.sql,
            parameters=(
                program_ref,
                membership.work_item_ref,
                membership.work_item_revision_ref,
            ),
            limit=_MEMBERSHIP_WORK_ITEM_REVISION_SELECT.fetch_limit,
        )
        child_row = _required_single_row(child_rows)
        child_rows = []
        work_item_revision = development_work_item_revision_row_value_from_row_tuple(
            child_row
        )
        child_row = None
        _require_relation(
            work_item_revision.program_ref == program_ref
            and work_item_revision.work_item_ref == membership.work_item_ref
            and work_item_revision.work_item_revision_ref
            == membership.work_item_revision_ref
        )
        entries.append(
            DevelopmentProgramVersionMembershipEntry._from_validated(
                membership,
                work_item_revision,
            )
        )
    return DevelopmentProgramVersionMembershipRead._from_validated(
        program_version,
        tuple(entries),
    )


def _load_development_work_spec_safe_binding(
    capability: object,
    program_ref: object,
    program_version_ref: object,
    work_item_ref: object,
    work_item_revision_ref: object,
) -> DevelopmentWorkSpecBindingRowValue | None:
    program_ref = _validated_safe_ref(program_ref)
    program_version_ref = _validated_safe_ref(program_version_ref)
    work_item_ref = _validated_safe_ref(work_item_ref)
    work_item_revision_ref = _validated_safe_ref(work_item_revision_ref)
    capability = _require_nominal_capability(capability)
    rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_WORK_SPEC_SAFE_BINDING_SELECT.sql,
        parameters=(program_ref, program_version_ref, work_item_ref, work_item_revision_ref),
        limit=_WORK_SPEC_SAFE_BINDING_SELECT.fetch_limit,
    )
    row = _optional_single_row(rows)
    rows = []
    if row is None:
        return None
    result = development_work_spec_binding_row_value_from_row_tuple(row)
    row = None
    _require_relation(
        result.program_ref == program_ref
        and result.program_version_ref == program_version_ref
        and result.work_item_ref == work_item_ref
        and result.work_item_revision_ref == work_item_revision_ref
    )
    return result


def _load_development_attempt_fence_command_effect_aggregate(
    capability: object,
    program_ref: object,
    semantic_attempt_ref: object,
    effect_intent_ref: object,
) -> DevelopmentAttemptFenceCommandEffectRead | None:
    program_ref = _validated_safe_ref(program_ref)
    semantic_attempt_ref = _validated_safe_ref(semantic_attempt_ref)
    effect_intent_ref = _validated_safe_ref(effect_intent_ref)
    capability = _require_nominal_capability(capability)
    root_rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_EFFECT_INTENT_ROOT_SELECT.sql,
        parameters=(program_ref, effect_intent_ref),
        limit=_EFFECT_INTENT_ROOT_SELECT.fetch_limit,
    )
    root_row = _optional_single_row(root_rows)
    root_rows = []
    if root_row is None:
        return None
    effect_intent = development_effect_intent_row_value_from_row_tuple(root_row)
    root_row = None
    _require_relation(
        effect_intent.program_ref == program_ref
        and effect_intent.effect_intent_ref == effect_intent_ref
        and effect_intent.semantic_attempt_ref == semantic_attempt_ref
    )

    attempt_rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_SEMANTIC_ATTEMPT_SELECT.sql,
        parameters=(program_ref, semantic_attempt_ref),
        limit=_SEMANTIC_ATTEMPT_SELECT.fetch_limit,
    )
    attempt_row = _required_single_row(attempt_rows)
    attempt_rows = []
    semantic_attempt = development_semantic_attempt_row_value_from_row_tuple(attempt_row)
    attempt_row = None

    command_rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_AUTHOR_COMMAND_SELECT.sql,
        parameters=(program_ref, effect_intent.command_ref),
        limit=_AUTHOR_COMMAND_SELECT.fetch_limit,
    )
    command_row = _required_single_row(command_rows)
    command_rows = []
    author_command = development_author_command_row_value_from_row_tuple(command_row)
    command_row = None

    fence_rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_ATTEMPT_FENCE_SELECT.sql,
        parameters=(program_ref, author_command.attempt_fence_ref),
        limit=_ATTEMPT_FENCE_SELECT.fetch_limit,
    )
    fence_row = _required_single_row(fence_rows)
    fence_rows = []
    attempt_fence = development_attempt_fence_row_value_from_row_tuple(fence_row)
    fence_row = None

    current_rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_CURRENT_EFFECT_FENCE_SELECT.sql,
        parameters=(program_ref, effect_intent_ref),
        limit=_CURRENT_EFFECT_FENCE_SELECT.fetch_limit,
    )
    current_row = _required_single_row(current_rows)
    current_rows = []
    current_effect_fence = development_effect_fence_row_value_from_row_tuple(current_row)
    current_row = None

    if author_command.effect_fence_ref == current_effect_fence.effect_fence_ref:
        author_effect_fence = current_effect_fence
    else:
        author_rows = _execute_select_fetch_bounded(
            capability=capability,
            sql=_AUTHOR_EFFECT_FENCE_SELECT.sql,
            parameters=(program_ref, author_command.effect_fence_ref),
            limit=_AUTHOR_EFFECT_FENCE_SELECT.fetch_limit,
        )
        author_row = _required_single_row(author_rows)
        author_rows = []
        author_effect_fence = development_effect_fence_row_value_from_row_tuple(author_row)
        author_row = None

    _require_relation(
        semantic_attempt.program_ref == program_ref
        and semantic_attempt.semantic_attempt_ref == semantic_attempt_ref
        and effect_intent.program_version_ref == semantic_attempt.program_version_ref
        and effect_intent.candidate_ref == semantic_attempt.candidate_ref
        and author_command.program_ref == program_ref
        and author_command.command_ref == effect_intent.command_ref
        and author_command.program_version_ref == semantic_attempt.program_version_ref
        and author_command.accepted_intent_revision_ref
        == semantic_attempt.accepted_intent_revision_ref
        and author_command.work_item_ref == semantic_attempt.work_item_ref
        and author_command.work_item_revision_ref == semantic_attempt.work_item_revision_ref
        and author_command.semantic_attempt_ref == semantic_attempt_ref
        and author_command.candidate_ref == semantic_attempt.candidate_ref
        and attempt_fence.program_ref == program_ref
        and attempt_fence.program_version_ref == semantic_attempt.program_version_ref
        and attempt_fence.accepted_intent_revision_ref
        == semantic_attempt.accepted_intent_revision_ref
        and attempt_fence.work_item_ref == semantic_attempt.work_item_ref
        and attempt_fence.work_item_revision_ref == semantic_attempt.work_item_revision_ref
        and attempt_fence.semantic_attempt_ref == semantic_attempt_ref
        and author_command.repository_ref == attempt_fence.repository_ref
        and author_command.base_git_object_format == attempt_fence.base_git_object_format
        and author_command.base_git_oid == attempt_fence.base_git_oid
        and author_command.author_command.path_ceiling
        == attempt_fence.attempt_fence.path_ceiling
        and author_command.standing_grant_ref == attempt_fence.parent_standing_grant_ref
        and author_command.standing_grant_digest
        == attempt_fence.parent_standing_grant_digest
        and author_command.attempt_authorization_ref
        == attempt_fence.attempt_authorization_ref
        and author_command.attempt_authorization_digest
        == attempt_fence.attempt_authorization_digest
        and author_command.attempt_fence_ref == attempt_fence.attempt_fence_ref
        and author_command.attempt_fence_digest == attempt_fence.attempt_fence_digest
        and author_command.global_stop_ref == attempt_fence.global_stop_ref
        and author_command.global_stop_version == attempt_fence.global_stop_version
        and _ceilings_are_no_wider(
            author_command.author_command.effect_ceilings,
            attempt_fence.attempt_fence.aggregate_ceilings,
        )
    )
    _require_relation(
        current_effect_fence.program_ref == program_ref
        and current_effect_fence.program_version_ref == semantic_attempt.program_version_ref
        and current_effect_fence.accepted_intent_revision_ref
        == semantic_attempt.accepted_intent_revision_ref
        and current_effect_fence.work_item_ref == semantic_attempt.work_item_ref
        and current_effect_fence.work_item_revision_ref
        == semantic_attempt.work_item_revision_ref
        and current_effect_fence.semantic_attempt_ref == semantic_attempt_ref
        and current_effect_fence.effect_intent_ref == effect_intent_ref
        and current_effect_fence.effect_class == effect_intent.effect_class
        and current_effect_fence.command_ref == author_command.command_ref
        and current_effect_fence.command_digest == author_command.command_digest
        and current_effect_fence.candidate_ref == semantic_attempt.candidate_ref
        and current_effect_fence.repository_ref == attempt_fence.repository_ref
        and current_effect_fence.base_git_object_format
        == attempt_fence.base_git_object_format
        and current_effect_fence.base_git_oid == attempt_fence.base_git_oid
        and current_effect_fence.effect_fence.path_ceiling
        == attempt_fence.attempt_fence.path_ceiling
        and current_effect_fence.parent_standing_grant_ref
        == attempt_fence.parent_standing_grant_ref
        and current_effect_fence.parent_standing_grant_digest
        == attempt_fence.parent_standing_grant_digest
        and current_effect_fence.attempt_fence_ref == attempt_fence.attempt_fence_ref
        and current_effect_fence.attempt_fence_digest
        == attempt_fence.attempt_fence_digest
        and current_effect_fence.global_stop_ref == attempt_fence.global_stop_ref
        and current_effect_fence.global_stop_version == attempt_fence.global_stop_version
        and _ceilings_are_no_wider(
            current_effect_fence.effect_fence.effect_ceilings,
            attempt_fence.attempt_fence.aggregate_ceilings,
        )
        and current_effect_fence.effect_class
        in attempt_fence.attempt_fence.allowed_effect_classes
        and current_effect_fence.expires_at <= attempt_fence.expires_at
    )
    _require_relation(
        author_effect_fence.program_ref == program_ref
        and author_effect_fence.program_version_ref == author_command.program_version_ref
        and author_effect_fence.accepted_intent_revision_ref
        == author_command.accepted_intent_revision_ref
        and author_effect_fence.work_item_ref == author_command.work_item_ref
        and author_effect_fence.work_item_revision_ref == author_command.work_item_revision_ref
        and author_effect_fence.semantic_attempt_ref == author_command.semantic_attempt_ref
        and author_effect_fence.effect_intent_ref == author_command.effect_intent_ref
        and author_effect_fence.effect_class == "author_candidate"
        and author_effect_fence.command_ref == author_command.command_ref
        and author_effect_fence.command_digest == author_command.command_digest
        and author_effect_fence.candidate_ref == author_command.candidate_ref
        and author_effect_fence.repository_ref == author_command.repository_ref
        and author_effect_fence.base_git_object_format
        == author_command.base_git_object_format
        and author_effect_fence.base_git_oid == author_command.base_git_oid
        and author_effect_fence.effect_fence.path_ceiling
        == author_command.author_command.path_ceiling
        and author_effect_fence.effect_authorization_ref
        == author_command.effect_authorization_ref
        and author_effect_fence.effect_authorization_digest
        == author_command.effect_authorization_digest
        and author_effect_fence.attempt_fence_ref == author_command.attempt_fence_ref
        and author_effect_fence.attempt_fence_digest == author_command.attempt_fence_digest
        and author_effect_fence.effect_fence_ref == author_command.effect_fence_ref
        and author_effect_fence.effect_fence_digest == author_command.effect_fence_digest
        and author_effect_fence.effect_fence.effect_ceilings
        == author_command.author_command.effect_ceilings
        and author_effect_fence.global_stop_ref == author_command.global_stop_ref
        and author_effect_fence.global_stop_version == author_command.global_stop_version
        and author_effect_fence.parent_standing_grant_ref
        == author_command.standing_grant_ref
        and author_effect_fence.parent_standing_grant_digest
        == author_command.standing_grant_digest
        and _ceilings_are_no_wider(
            author_effect_fence.effect_fence.effect_ceilings,
            attempt_fence.attempt_fence.aggregate_ceilings,
        )
        and author_effect_fence.effect_class
        in attempt_fence.attempt_fence.allowed_effect_classes
        and author_effect_fence.expires_at <= attempt_fence.expires_at
    )
    if effect_intent.effect_class == "author_candidate":
        _require_relation(current_effect_fence is author_effect_fence)
    return DevelopmentAttemptFenceCommandEffectRead._from_validated(
        semantic_attempt,
        effect_intent,
        author_command,
        attempt_fence,
        current_effect_fence,
        author_effect_fence,
    )


def _load_development_authority_evaluation_by_exact_ref(
    capability: object,
    program_ref: object,
    authority_evaluation_ref: object,
) -> DevelopmentAuthorityEvaluationRowValue | None:
    program_ref = _validated_safe_ref(program_ref)
    authority_evaluation_ref = _validated_safe_ref(authority_evaluation_ref)
    capability = _require_nominal_capability(capability)
    rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_AUTHORITY_EVALUATION_SELECT.sql,
        parameters=(program_ref, authority_evaluation_ref),
        limit=_AUTHORITY_EVALUATION_SELECT.fetch_limit,
    )
    row = _optional_single_row(rows)
    rows = []
    if row is None:
        return None
    result = development_authority_evaluation_row_value_from_row_tuple(row)
    row = None
    _require_relation(
        result.program_ref == program_ref
        and result.authority_evaluation_ref == authority_evaluation_ref
    )
    return result


def _load_development_effect_head(
    capability: object,
    program_ref: object,
    effect_intent_ref: object,
) -> DevelopmentEffectHeadRowValue | None:
    program_ref = _validated_safe_ref(program_ref)
    effect_intent_ref = _validated_safe_ref(effect_intent_ref)
    capability = _require_nominal_capability(capability)
    rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_EFFECT_HEAD_SELECT.sql,
        parameters=(program_ref, effect_intent_ref),
        limit=_EFFECT_HEAD_SELECT.fetch_limit,
    )
    row = _optional_single_row(rows)
    rows = []
    if row is None:
        return None
    result = development_effect_head_row_value_from_row_tuple(row)
    row = None
    _require_relation(
        result.program_ref == program_ref
        and result.effect_intent_ref == effect_intent_ref
    )
    return result


def _load_development_delivery_head(
    capability: object,
    program_ref: object,
    effect_intent_ref: object,
) -> DevelopmentDeliveryHeadAndCurrentAttemptRead | None:
    program_ref = _validated_safe_ref(program_ref)
    effect_intent_ref = _validated_safe_ref(effect_intent_ref)
    capability = _require_nominal_capability(capability)
    root_rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_DELIVERY_HEAD_SELECT.sql,
        parameters=(program_ref, effect_intent_ref),
        limit=_DELIVERY_HEAD_SELECT.fetch_limit,
    )
    root_row = _optional_single_row(root_rows)
    root_rows = []
    if root_row is None:
        return None
    delivery_head = development_delivery_head_row_value_from_row_tuple(root_row)
    root_row = None
    _require_relation(
        delivery_head.program_ref == program_ref
        and delivery_head.effect_intent_ref == effect_intent_ref
    )
    child_rows = _execute_select_fetch_bounded(
        capability=capability,
        sql=_CURRENT_DELIVERY_ATTEMPT_SELECT.sql,
        parameters=(
            program_ref,
            effect_intent_ref,
            delivery_head.current_delivery_attempt_ref,
        ),
        limit=_CURRENT_DELIVERY_ATTEMPT_SELECT.fetch_limit,
    )
    child_row = _required_single_row(child_rows)
    child_rows = []
    current_delivery_attempt = development_delivery_attempt_row_value_from_row_tuple(
        child_row
    )
    child_row = None
    _require_relation(
        current_delivery_attempt.program_ref == program_ref
        and current_delivery_attempt.effect_intent_ref == effect_intent_ref
        and current_delivery_attempt.delivery_attempt_ref
        == delivery_head.current_delivery_attempt_ref
    )
    return DevelopmentDeliveryHeadAndCurrentAttemptRead._from_validated(
        delivery_head,
        current_delivery_attempt,
    )


_ReaderFailure: typing.TypeAlias = (
    SQLiteMutationStoreErrorCode | _MutationReadCapabilityFailureReason
)


def _complete_reader_outcome(outcome: object | None | _ReaderFailure) -> object | None:
    if type(outcome) is SQLiteMutationStoreErrorCode:
        failure = outcome
        outcome = None
        _raise_reader_failure(failure)
    if type(outcome) is _MutationReadCapabilityFailureReason:
        capability_failure = outcome
        outcome = None
        _raise_reader_failure(capability_failure)
    return outcome


def _raise_reader_failure(failure: _ReaderFailure) -> typing.NoReturn:
    if type(failure) is _MutationReadCapabilityFailureReason:
        raise _MutationReadCapabilityError(failure) from None
    raise SQLiteMutationStoreError(failure) from None


def _perform_development_mutation_receipt_by_mutation_ref(
    capability: object,
    mutation_ref: object,
) -> DevelopmentMutationReceiptRowValue | None | _ReaderFailure:
    try:
        return _load_development_mutation_receipt_by_mutation_ref(
            capability,
            mutation_ref,
        )
    except SQLiteMutationStoreError as error:
        return SQLiteMutationStoreErrorCode(error.error_class)
    except _MutationReadCapabilityError as error:
        return error.reason


def _read_development_mutation_receipt_by_mutation_ref(
    capability: object,
    mutation_ref: object,
) -> DevelopmentMutationReceiptRowValue | None:
    outcome = _perform_development_mutation_receipt_by_mutation_ref(
        capability,
        mutation_ref,
    )
    del capability, mutation_ref
    return typing.cast(
        DevelopmentMutationReceiptRowValue | None,
        _complete_reader_outcome(outcome),
    )


def _perform_development_decision_by_decision_ref(
    capability: object,
    decision_ref: object,
) -> DevelopmentDecisionRowValue | None | _ReaderFailure:
    try:
        return _load_development_decision_by_decision_ref(capability, decision_ref)
    except SQLiteMutationStoreError as error:
        return SQLiteMutationStoreErrorCode(error.error_class)
    except _MutationReadCapabilityError as error:
        return error.reason


def _read_development_decision_by_decision_ref(
    capability: object,
    decision_ref: object,
) -> DevelopmentDecisionRowValue | None:
    outcome = _perform_development_decision_by_decision_ref(
        capability,
        decision_ref,
    )
    del capability, decision_ref
    return typing.cast(
        DevelopmentDecisionRowValue | None,
        _complete_reader_outcome(outcome),
    )


def _perform_development_program_head_and_current_version(
    capability: object,
    program_ref: object,
) -> DevelopmentProgramHeadAndCurrentVersionRead | None | _ReaderFailure:
    try:
        return _load_development_program_head_and_current_version(
            capability,
            program_ref,
        )
    except SQLiteMutationStoreError as error:
        return SQLiteMutationStoreErrorCode(error.error_class)
    except _MutationReadCapabilityError as error:
        return error.reason


def _read_development_program_head_and_current_version(
    capability: object,
    program_ref: object,
) -> DevelopmentProgramHeadAndCurrentVersionRead | None:
    outcome = _perform_development_program_head_and_current_version(
        capability,
        program_ref,
    )
    del capability, program_ref
    return typing.cast(
        DevelopmentProgramHeadAndCurrentVersionRead | None,
        _complete_reader_outcome(outcome),
    )


def _perform_development_initialize_decision_and_resulting_version(
    capability: object,
    program_ref: object,
    decision_ref: object,
) -> DevelopmentInitializeDecisionAndResultingVersionRead | None | _ReaderFailure:
    try:
        return _load_development_initialize_decision_and_resulting_version(
            capability,
            program_ref,
            decision_ref,
        )
    except SQLiteMutationStoreError as error:
        return SQLiteMutationStoreErrorCode(error.error_class)
    except _MutationReadCapabilityError as error:
        return error.reason


def _read_development_initialize_decision_and_resulting_version(
    capability: object,
    program_ref: object,
    decision_ref: object,
) -> DevelopmentInitializeDecisionAndResultingVersionRead | None:
    outcome = _perform_development_initialize_decision_and_resulting_version(
        capability,
        program_ref,
        decision_ref,
    )
    del capability, program_ref, decision_ref
    return typing.cast(
        DevelopmentInitializeDecisionAndResultingVersionRead | None,
        _complete_reader_outcome(outcome),
    )


def _perform_development_accepted_intent_revision_by_exact_ref(
    capability: object,
    program_ref: object,
    accepted_intent_revision_ref: object,
) -> DevelopmentAcceptedIntentRevisionRowValue | None | _ReaderFailure:
    try:
        return _load_development_accepted_intent_revision_by_exact_ref(
            capability,
            program_ref,
            accepted_intent_revision_ref,
        )
    except SQLiteMutationStoreError as error:
        return SQLiteMutationStoreErrorCode(error.error_class)
    except _MutationReadCapabilityError as error:
        return error.reason


def _read_development_accepted_intent_revision_by_exact_ref(
    capability: object,
    program_ref: object,
    accepted_intent_revision_ref: object,
) -> DevelopmentAcceptedIntentRevisionRowValue | None:
    outcome = _perform_development_accepted_intent_revision_by_exact_ref(
        capability,
        program_ref,
        accepted_intent_revision_ref,
    )
    del capability, program_ref, accepted_intent_revision_ref
    return typing.cast(
        DevelopmentAcceptedIntentRevisionRowValue | None,
        _complete_reader_outcome(outcome),
    )


def _perform_development_work_item_head_and_revision_by_exact_ref(
    capability: object,
    program_ref: object,
    work_item_ref: object,
    work_item_revision_ref: object,
) -> DevelopmentWorkItemHeadAndRevisionRead | None | _ReaderFailure:
    try:
        return _load_development_work_item_head_and_revision_by_exact_ref(
            capability,
            program_ref,
            work_item_ref,
            work_item_revision_ref,
        )
    except SQLiteMutationStoreError as error:
        return SQLiteMutationStoreErrorCode(error.error_class)
    except _MutationReadCapabilityError as error:
        return error.reason


def _read_development_work_item_head_and_revision_by_exact_ref(
    capability: object,
    program_ref: object,
    work_item_ref: object,
    work_item_revision_ref: object,
) -> DevelopmentWorkItemHeadAndRevisionRead | None:
    outcome = _perform_development_work_item_head_and_revision_by_exact_ref(
        capability,
        program_ref,
        work_item_ref,
        work_item_revision_ref,
    )
    del capability, program_ref, work_item_ref, work_item_revision_ref
    return typing.cast(
        DevelopmentWorkItemHeadAndRevisionRead | None,
        _complete_reader_outcome(outcome),
    )


def _perform_development_paged_program_version_membership(
    capability: object,
    program_ref: object,
    program_version_ref: object,
    maximum_members: object,
) -> DevelopmentProgramVersionMembershipRead | None | _ReaderFailure:
    try:
        return _load_development_paged_program_version_membership(
            capability,
            program_ref,
            program_version_ref,
            maximum_members,
        )
    except SQLiteMutationStoreError as error:
        return SQLiteMutationStoreErrorCode(error.error_class)
    except _MutationReadCapabilityError as error:
        return error.reason


def _read_development_paged_program_version_membership(
    capability: object,
    program_ref: object,
    program_version_ref: object,
    maximum_members: object,
) -> DevelopmentProgramVersionMembershipRead | None:
    outcome = _perform_development_paged_program_version_membership(
        capability,
        program_ref,
        program_version_ref,
        maximum_members,
    )
    del capability, program_ref, program_version_ref, maximum_members
    return typing.cast(
        DevelopmentProgramVersionMembershipRead | None,
        _complete_reader_outcome(outcome),
    )


def _perform_development_work_spec_safe_binding(
    capability: object,
    program_ref: object,
    program_version_ref: object,
    work_item_ref: object,
    work_item_revision_ref: object,
) -> DevelopmentWorkSpecBindingRowValue | None | _ReaderFailure:
    try:
        return _load_development_work_spec_safe_binding(
            capability,
            program_ref,
            program_version_ref,
            work_item_ref,
            work_item_revision_ref,
        )
    except SQLiteMutationStoreError as error:
        return SQLiteMutationStoreErrorCode(error.error_class)
    except _MutationReadCapabilityError as error:
        return error.reason


def _read_development_work_spec_safe_binding(
    capability: object,
    program_ref: object,
    program_version_ref: object,
    work_item_ref: object,
    work_item_revision_ref: object,
) -> DevelopmentWorkSpecBindingRowValue | None:
    outcome = _perform_development_work_spec_safe_binding(
        capability,
        program_ref,
        program_version_ref,
        work_item_ref,
        work_item_revision_ref,
    )
    del capability, program_ref, program_version_ref, work_item_ref, work_item_revision_ref
    return typing.cast(
        DevelopmentWorkSpecBindingRowValue | None,
        _complete_reader_outcome(outcome),
    )


def _perform_development_attempt_fence_command_effect_aggregate(
    capability: object,
    program_ref: object,
    semantic_attempt_ref: object,
    effect_intent_ref: object,
) -> DevelopmentAttemptFenceCommandEffectRead | None | _ReaderFailure:
    try:
        return _load_development_attempt_fence_command_effect_aggregate(
            capability,
            program_ref,
            semantic_attempt_ref,
            effect_intent_ref,
        )
    except SQLiteMutationStoreError as error:
        return SQLiteMutationStoreErrorCode(error.error_class)
    except _MutationReadCapabilityError as error:
        return error.reason


def _read_development_attempt_fence_command_effect_aggregate(
    capability: object,
    program_ref: object,
    semantic_attempt_ref: object,
    effect_intent_ref: object,
) -> DevelopmentAttemptFenceCommandEffectRead | None:
    outcome = _perform_development_attempt_fence_command_effect_aggregate(
        capability,
        program_ref,
        semantic_attempt_ref,
        effect_intent_ref,
    )
    del capability, program_ref, semantic_attempt_ref, effect_intent_ref
    return typing.cast(
        DevelopmentAttemptFenceCommandEffectRead | None,
        _complete_reader_outcome(outcome),
    )


def _perform_development_authority_evaluation_by_exact_ref(
    capability: object,
    program_ref: object,
    authority_evaluation_ref: object,
) -> DevelopmentAuthorityEvaluationRowValue | None | _ReaderFailure:
    try:
        return _load_development_authority_evaluation_by_exact_ref(
            capability,
            program_ref,
            authority_evaluation_ref,
        )
    except SQLiteMutationStoreError as error:
        return SQLiteMutationStoreErrorCode(error.error_class)
    except _MutationReadCapabilityError as error:
        return error.reason


def _read_development_authority_evaluation_by_exact_ref(
    capability: object,
    program_ref: object,
    authority_evaluation_ref: object,
) -> DevelopmentAuthorityEvaluationRowValue | None:
    outcome = _perform_development_authority_evaluation_by_exact_ref(
        capability,
        program_ref,
        authority_evaluation_ref,
    )
    del capability, program_ref, authority_evaluation_ref
    return typing.cast(
        DevelopmentAuthorityEvaluationRowValue | None,
        _complete_reader_outcome(outcome),
    )


def _perform_development_effect_head(
    capability: object,
    program_ref: object,
    effect_intent_ref: object,
) -> DevelopmentEffectHeadRowValue | None | _ReaderFailure:
    try:
        return _load_development_effect_head(
            capability,
            program_ref,
            effect_intent_ref,
        )
    except SQLiteMutationStoreError as error:
        return SQLiteMutationStoreErrorCode(error.error_class)
    except _MutationReadCapabilityError as error:
        return error.reason


def _read_development_effect_head(
    capability: object,
    program_ref: object,
    effect_intent_ref: object,
) -> DevelopmentEffectHeadRowValue | None:
    outcome = _perform_development_effect_head(
        capability,
        program_ref,
        effect_intent_ref,
    )
    del capability, program_ref, effect_intent_ref
    return typing.cast(
        DevelopmentEffectHeadRowValue | None,
        _complete_reader_outcome(outcome),
    )


def _perform_development_delivery_head(
    capability: object,
    program_ref: object,
    effect_intent_ref: object,
) -> DevelopmentDeliveryHeadAndCurrentAttemptRead | None | _ReaderFailure:
    try:
        return _load_development_delivery_head(
            capability,
            program_ref,
            effect_intent_ref,
        )
    except SQLiteMutationStoreError as error:
        return SQLiteMutationStoreErrorCode(error.error_class)
    except _MutationReadCapabilityError as error:
        return error.reason


def _read_development_delivery_head(
    capability: object,
    program_ref: object,
    effect_intent_ref: object,
) -> DevelopmentDeliveryHeadAndCurrentAttemptRead | None:
    outcome = _perform_development_delivery_head(
        capability,
        program_ref,
        effect_intent_ref,
    )
    del capability, program_ref, effect_intent_ref
    return typing.cast(
        DevelopmentDeliveryHeadAndCurrentAttemptRead | None,
        _complete_reader_outcome(outcome),
    )
