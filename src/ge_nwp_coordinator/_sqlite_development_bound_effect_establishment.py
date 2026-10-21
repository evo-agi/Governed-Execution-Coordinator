"""Private fenced family mechanics for the two D2 capsule-bound effects.

This module neither opens connections nor owns a writer.  All SELECTs borrow the
single nominal Coordinator mutation capability after writer fencing.
"""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
import typing

from . import _development_decision_row_values as _decision_rows
from . import _development_effect_row_values as _effect_rows
from . import _development_program_row_values as _program_rows
from ._development_bound_effect_establishment_contracts import (
    DevelopmentBoundEffectEstablishmentCommandV1,
    DevelopmentBoundEffectEstablishmentConflictReasonV1,
    DevelopmentBoundEffectEstablishmentConflictV1,
    DevelopmentBoundEffectEstablishmentRecoveryDispositionV1,
    DevelopmentBoundEffectEstablishmentRecoveryResultV1,
    DevelopmentBoundEffectEstablishmentResultV1,
    _DevelopmentBoundEffectEstablishmentWritePlan,
    _bound_effect_conflict,
    _bound_effect_result,
    _development_bound_effect_establishment_write_plan,
    _require_exact_bound_effect_authorization_safe_binding,
    _require_exact_development_bound_effect_command,
)
from ._development_row_value_support import _require_utc_timestamp
from ._sqlite_development_pre_execution_plan_disposition import _read_disposition_by_ref
from ._sqlite_development_reader_contracts import (
    DevelopmentAttemptFenceCommandEffectRead,
    DevelopmentDeliveryHeadAndCurrentAttemptRead,
    DevelopmentProgramHeadAndCurrentVersionRead,
    DevelopmentWorkItemHeadAndRevisionRead,
)
from ._sqlite_development_readers import (
    _read_development_attempt_fence_command_effect_aggregate,
    _read_development_authority_evaluation_by_exact_ref,
    _read_development_decision_by_decision_ref,
    _read_development_delivery_head,
    _read_development_effect_head,
    _read_development_mutation_receipt_by_mutation_ref,
    _read_development_program_head_and_current_version,
    _read_development_work_item_head_and_revision_by_exact_ref,
    _read_development_work_spec_safe_binding,
)
from ._sqlite_rw0_c1_readers import _read_phase_by_pair
from ._worker_execution_semantic_values import (
    create_effect_fence,
    validate_capsule_manifest_relation,
    validate_delivery_relation,
)
from .persistence_contracts import GlobalStopCurrentRecordEnvelope
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from .sqlite_transition_read_scope import _read_global_stop_current
from .sqlite_transition_select_support import (
    _execute_select_fetch_bounded, _execute_select_fetch_two,
)

__all__: tuple[str, ...] = ()

_AUTHOR_COMMAND_BY_REF = (
    f"SELECT {', '.join(_effect_rows._DEVELOPMENT_AUTHOR_COMMAND_COLUMNS)} "
    "FROM development_author_commands WHERE program_ref = ? AND command_ref = ? LIMIT 2"
)
_EFFECT_INTENT_BY_REF = (
    f"SELECT {', '.join(_effect_rows._DEVELOPMENT_EFFECT_INTENT_COLUMNS)} "
    "FROM development_effect_intents WHERE program_ref = ? AND effect_intent_ref = ? LIMIT 2"
)
_EFFECT_FENCE_BY_REF = (
    f"SELECT {', '.join(_effect_rows._DEVELOPMENT_EFFECT_FENCE_COLUMNS)} "
    "FROM development_effect_fences WHERE program_ref = ? AND effect_fence_ref = ? LIMIT 2"
)
_DELIVERY_BY_REF = (
    f"SELECT {', '.join(_effect_rows._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS)} "
    "FROM development_delivery_attempts WHERE program_ref = ? AND delivery_attempt_ref = ? LIMIT 2"
)
_EFFECTS_FOR_ATTEMPT = (
    "SELECT effect_intent_ref, effect_class FROM development_effect_intents "
    "WHERE program_ref = ? AND semantic_attempt_ref = ? LIMIT 15"
)
_COLLISION_QUERIES = (
    ("SELECT 1 FROM development_effect_intents WHERE effect_intent_ref = ? LIMIT 2", "effect_intent_ref"),
    ("SELECT 1 FROM development_effect_fences WHERE effect_fence_ref = ? LIMIT 2", "effect_fence_ref"),
    ("SELECT 1 FROM development_authority_evaluations WHERE authority_evaluation_ref = ? LIMIT 2", "authority_evaluation_ref"),
    ("SELECT 1 FROM development_delivery_attempts WHERE delivery_attempt_ref = ? LIMIT 2", "delivery_attempt_ref"),
    ("SELECT 1 FROM development_effect_heads WHERE effect_intent_ref = ? LIMIT 2", "effect_intent_ref"),
    ("SELECT 1 FROM development_delivery_heads WHERE effect_intent_ref = ? LIMIT 2", "effect_intent_ref"),
)
_INSERTS = (
    ("development_effect_intents", _effect_rows._DEVELOPMENT_EFFECT_INTENT_COLUMNS),
    ("development_effect_fences", _effect_rows._DEVELOPMENT_EFFECT_FENCE_COLUMNS),
    ("development_authority_evaluations", _effect_rows._DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS),
    ("development_delivery_attempts", _effect_rows._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS),
    ("development_effect_heads", _effect_rows._DEVELOPMENT_EFFECT_HEAD_COLUMNS),
    ("development_delivery_heads", _effect_rows._DEVELOPMENT_DELIVERY_HEAD_COLUMNS),
    ("development_mutation_receipts", _decision_rows._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS),
)
_INSERT_SQL = tuple(
    f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})"
    for table, columns in _INSERTS
)


def _integrity() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def _failed() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)


def _exact_row(capability: object, sql: str, parameters: tuple[str, str], adapter: typing.Callable[[object], object]) -> object | None:
    if type(sql) is not str or not any(sql is allowed for allowed in (
        _AUTHOR_COMMAND_BY_REF, _EFFECT_INTENT_BY_REF, _EFFECT_FENCE_BY_REF,
        _DELIVERY_BY_REF,
    )):
        raise _integrity() from None
    rows = _execute_select_fetch_two(capability=capability, sql=sql, parameters=parameters)
    if len(rows) > 1:
        raise _integrity() from None
    if not rows:
        return None
    row = rows[0]
    if type(row) is not tuple:
        raise _integrity() from None
    try:
        return adapter(row)
    except Exception:
        raise _integrity() from None


def _collisions(capability: object, command: DevelopmentBoundEffectEstablishmentCommandV1) -> bool:
    for sql, field in _COLLISION_QUERIES:
        rows = _execute_select_fetch_two(
            capability=capability, sql=sql,
            parameters=(getattr(command, field),),
        )
        if rows:
            return True
    return False


def _attempt_effects(capability: object, command: DevelopmentBoundEffectEstablishmentCommandV1) -> tuple[tuple[str, str], ...]:
    rows = _execute_select_fetch_bounded(
        capability=capability, sql=_EFFECTS_FOR_ATTEMPT,
        parameters=(command.program_ref, command.semantic_attempt_ref), limit=15,
    )
    if not 1 <= len(rows) <= 3 or any(
        type(row) is not tuple or len(row) != 2
        or type(row[0]) is not str or type(row[1]) is not str
        for row in rows
    ):
        raise _integrity() from None
    observed = typing.cast(tuple[tuple[str, str], ...], tuple(rows))
    if len({x[0] for x in observed}) != len(observed):
        raise _integrity() from None
    return observed


def _original_author_aggregate(capability: object, command: DevelopmentBoundEffectEstablishmentCommandV1) -> DevelopmentAttemptFenceCommandEffectRead:
    original = _exact_row(
        capability, _AUTHOR_COMMAND_BY_REF,
        (command.program_ref, command.originating_command_ref),
        _effect_rows.development_author_command_row_value_from_row_tuple,
    )
    if type(original) is not _effect_rows.DevelopmentAuthorCommandRowValue:
        raise _integrity() from None
    aggregate = _read_development_attempt_fence_command_effect_aggregate(
        capability, command.program_ref, command.semantic_attempt_ref,
        original.effect_intent_ref,
    )
    if type(aggregate) is not DevelopmentAttemptFenceCommandEffectRead:
        raise _integrity() from None
    if (aggregate.author_command != original
            or aggregate.effect_intent.effect_class != "author_candidate"
            or aggregate.author_effect_fence.effect_fence_ref != command.author_effect_fence_ref
            or aggregate.author_effect_fence.effect_fence_digest != command.author_effect_fence_digest
            or aggregate.author_command.command_digest != command.originating_command_digest
            or aggregate.attempt_fence.attempt_fence_digest != command.attempt_fence_digest
            or aggregate.semantic_attempt.candidate_ref != command.candidate_ref):
        raise _integrity() from None
    return aggregate


def _fresh_basis_is_exact(capability: object, command: DevelopmentBoundEffectEstablishmentCommandV1, now: str) -> bool:
    program = _read_development_program_head_and_current_version(capability, command.program_ref)
    work = _read_development_work_item_head_and_revision_by_exact_ref(
        capability, command.program_ref, command.work_item_ref,
        command.work_item_revision_ref,
    )
    work_spec = _read_development_work_spec_safe_binding(
        capability, command.program_ref, command.program_version_ref,
        command.work_item_ref, command.work_item_revision_ref,
    )
    decision = _read_development_decision_by_decision_ref(capability, command.basis_decision_ref)
    disposition = _read_disposition_by_ref(capability, command.selected_disposition_ref)
    phase = _read_phase_by_pair(capability, command.phase_basis_ref, command.phase_basis_digest)
    original = _original_author_aggregate(capability, command)
    author_head = _read_development_effect_head(capability, command.program_ref, original.effect_intent.effect_intent_ref)
    author_delivery = _read_development_delivery_head(capability, command.program_ref, original.effect_intent.effect_intent_ref)
    if (type(program) is not DevelopmentProgramHeadAndCurrentVersionRead
            or type(work) is not DevelopmentWorkItemHeadAndRevisionRead
            or type(work_spec) is not _program_rows.DevelopmentWorkSpecBindingRowValue
            or type(decision) is not _decision_rows.DevelopmentDecisionRowValue
            or disposition is None or phase is None
            or type(author_head) is not _effect_rows.DevelopmentEffectHeadRowValue
            or type(author_delivery) is not DevelopmentDeliveryHeadAndCurrentAttemptRead):
        raise _integrity() from None
    binding = _require_exact_bound_effect_authorization_safe_binding(command.effect_authorization_safe_binding)
    attempt = original.attempt_fence.attempt_fence
    author_command = original.author_command.author_command
    author_fence = original.author_effect_fence.effect_fence
    before = dict(command.before_blob_entries)
    after = dict(command.after_blob_entries)
    validate_capsule_manifest_relation(
        capsule_manifest=command.capsule_manifest,
        author_command=author_command,
        attempt_fence=attempt,
        author_effect_fence=author_fence,
        before_blobs=before, after_blobs=after,
    )
    created_fence = create_effect_fence(
        attempt_fence=attempt, author_command=author_command,
        author_effect_fence=author_fence,
        effect_fence_ref=command.effect_fence_ref,
        effect_intent_ref=command.effect_intent_ref,
        effect_class=command.effect_class,
        effect_authorization_ref=binding.effect_authorization_ref,
        effect_authorization_digest=binding.effect_authorization_digest,
        effect_ceilings=binding.effect_ceilings,
        expires_at=binding.expires_at,
        capsule_manifest=command.capsule_manifest,
    )
    validate_delivery_relation(
        delivery=command.delivery_envelope,
        author_command=author_command, attempt_fence=attempt,
        author_effect_fence=author_fence, effect_fence=created_fence,
        capsule_manifest=command.capsule_manifest,
    )
    requirement = command.requirement_evidence
    return bool(
        created_fence.to_mapping() == command.effect_fence.to_mapping()
        and program.program_head.program_state == "active"
        and program.program_head.current_program_version_ref == command.program_version_ref
        and program.current_program_version.program_version_ref == command.program_version_ref
        and work.is_current
        and work.work_item_head.current_work_item_revision_ref == command.work_item_revision_ref
        and work_spec.work_spec_ref == requirement.work_spec_ref
        and work_spec.work_spec_digest == requirement.work_spec_digest
        and work_spec.safe_projection.work_spec_digest == original.author_command.author_command.work_spec_digest
        and (work_spec.validation_requirement_ref if command.effect_class == "validate_candidate" else work_spec.review_requirement_ref) == requirement.requirement_ref
        and decision.decision_ref == command.basis_decision_ref
        and decision.decision_digest == command.basis_decision_digest
        and decision.decision_kind == "initialize"
        and disposition.disposition_ref == command.selected_disposition_ref
        and disposition.disposition_digest == command.selected_disposition_digest
        and disposition.disposition == "selected_for_dispatch_gates"
        and disposition.author_command_ref == command.originating_command_ref
        and disposition.effect_fence_ref == command.author_effect_fence_ref
        and phase.value("phase_basis_ref") == command.phase_basis_ref
        and phase.value("phase_basis_digest") == command.phase_basis_digest
        and binding.parent_standing_grant_ref == attempt.parent_standing_grant_ref
        and binding.parent_standing_grant_digest == attempt.parent_standing_grant_digest
        and binding.attempt_fence_ref == attempt.attempt_fence_ref
        and binding.attempt_fence_digest == attempt.attempt_fence_digest
        and binding.global_stop_ref == attempt.global_stop_ref
        and binding.global_stop_version == attempt.global_stop_version
        and binding.expires_at <= attempt.expires_at
        and binding.expires_at > now
        and attempt.expires_at > now
        and binding.path_ceiling == attempt.path_ceiling
        and binding.effect_ceilings.max_deliveries <= 1
        and attempt.aggregate_ceilings.max_deliveries >= 3
        and author_head.current_effect_fence_ref == author_fence.effect_fence_ref
        and author_delivery.current_delivery_attempt.delivery_number == 1
        and author_delivery.current_delivery_attempt.basis_decision_ref == command.basis_decision_ref
    )


@dataclass(frozen=True, slots=True, repr=False)
class _FreshDevelopmentBoundEffectEstablishment:
    command: DevelopmentBoundEffectEstablishmentCommandV1
    transaction_timestamp: str

    def __repr__(self) -> str:
        return "<_FreshDevelopmentBoundEffectEstablishment>"


def _resolve_development_bound_effect_establishment_apply_after_fencing(
    *, capability: object, command: object, transaction_timestamp: object,
) -> DevelopmentBoundEffectEstablishmentResultV1 | DevelopmentBoundEffectEstablishmentConflictV1 | _FreshDevelopmentBoundEffectEstablishment:
    checked = _require_exact_development_bound_effect_command(command)
    timestamp = _require_utc_timestamp(transaction_timestamp)
    receipt = _read_development_mutation_receipt_by_mutation_ref(capability, checked.mutation_ref)
    if receipt is not None:
        if receipt.command_digest != checked.command_digest:
            return _bound_effect_conflict(
                checked, DevelopmentBoundEffectEstablishmentConflictReasonV1.MUTATION_REF_REUSE_CONFLICT
            )
        return _read_and_verify_exact_bound_effect_family(
            capability=capability, command=checked, receipt=receipt,
        )
    stop_envelope = _read_global_stop_current(capability)
    if type(stop_envelope) is not GlobalStopCurrentRecordEnvelope:
        raise _integrity() from None
    stop = stop_envelope.state
    if (stop.stop_ref != checked.effect_authorization_safe_binding.global_stop_ref
            or stop.version != checked.effect_authorization_safe_binding.global_stop_version):
        return _bound_effect_conflict(
            checked, DevelopmentBoundEffectEstablishmentConflictReasonV1.GLOBAL_STOP_VERSION_CONFLICT
        )
    if stop.active:
        return _bound_effect_conflict(
            checked, DevelopmentBoundEffectEstablishmentConflictReasonV1.CODING_GLOBAL_STOP_ACTIVE
        )
    if not _fresh_basis_is_exact(capability, checked, timestamp):
        return _bound_effect_conflict(
            checked, DevelopmentBoundEffectEstablishmentConflictReasonV1.CURRENT_STATE_CONFLICT
        )
    effects = _attempt_effects(capability, checked)
    if any(effect_class == checked.effect_class for _ref, effect_class in effects):
        return _bound_effect_conflict(
            checked, DevelopmentBoundEffectEstablishmentConflictReasonV1.SEMANTIC_IDENTITY_CONFLICT
        )
    if _collisions(capability, checked):
        return _bound_effect_conflict(
            checked, DevelopmentBoundEffectEstablishmentConflictReasonV1.SEMANTIC_IDENTITY_CONFLICT
        )
    if len(effects) >= 3 or any(effect_class not in {"author_candidate", "validate_candidate", "review_candidate"} for _, effect_class in effects):
        raise _integrity() from None
    if sum(1 for _, effect_class in effects if effect_class == "author_candidate") != 1:
        raise _integrity() from None
    committed_delivery_ceiling = 0
    for effect_ref, effect_class in effects:
        head = _read_development_delivery_head(capability, checked.program_ref, effect_ref)
        if type(head) is not DevelopmentDeliveryHeadAndCurrentAttemptRead or head.current_delivery_attempt.delivery_number != 1:
            raise _integrity() from None
        aggregate = _read_development_attempt_fence_command_effect_aggregate(
            capability, checked.program_ref, checked.semantic_attempt_ref,
            effect_ref,
        )
        if type(aggregate) is not DevelopmentAttemptFenceCommandEffectRead:
            raise _integrity() from None
        if aggregate.effect_intent.effect_class != effect_class:
            raise _integrity() from None
        ceiling = aggregate.current_effect_fence.effect_fence.effect_ceilings.max_deliveries
        if type(ceiling) is not int or ceiling > 1:
            raise _integrity() from None
        committed_delivery_ceiling += ceiling
    if committed_delivery_ceiling + checked.effect_fence.effect_ceilings.max_deliveries > 3:
        raise _integrity() from None
    return _FreshDevelopmentBoundEffectEstablishment(checked, timestamp)


def _read_and_verify_exact_bound_effect_family(
    *, capability: object, command: DevelopmentBoundEffectEstablishmentCommandV1,
    receipt: object,
) -> DevelopmentBoundEffectEstablishmentResultV1:
    if type(receipt) is not _decision_rows.DevelopmentMutationReceiptRowValue:
        raise _integrity() from None
    plan = _development_bound_effect_establishment_write_plan(command, receipt.committed_at)
    if receipt != plan.mutation_receipt:
        raise _integrity() from None
    intent = _exact_row(capability, _EFFECT_INTENT_BY_REF,
                        (command.program_ref, command.effect_intent_ref),
                        _effect_rows.development_effect_intent_row_value_from_row_tuple)
    fence = _exact_row(capability, _EFFECT_FENCE_BY_REF,
                       (command.program_ref, command.effect_fence_ref),
                       _effect_rows.development_effect_fence_row_value_from_row_tuple)
    delivery = _exact_row(capability, _DELIVERY_BY_REF,
                          (command.program_ref, command.delivery_attempt_ref),
                          _effect_rows.development_delivery_attempt_row_value_from_row_tuple)
    authority = _read_development_authority_evaluation_by_exact_ref(
        capability, command.program_ref, command.authority_evaluation_ref
    )
    effect_head = _read_development_effect_head(capability, command.program_ref, command.effect_intent_ref)
    delivery_head = _read_development_delivery_head(capability, command.program_ref, command.effect_intent_ref)
    if (intent != plan.effect_intent or fence != plan.effect_fence
            or authority != plan.authority_evaluation or delivery != plan.delivery_attempt
            or effect_head != plan.effect_head
            or type(delivery_head) is not DevelopmentDeliveryHeadAndCurrentAttemptRead
            or delivery_head.delivery_head != plan.delivery_head
            or delivery_head.current_delivery_attempt != plan.delivery_attempt):
        raise _integrity() from None
    return _bound_effect_result(command, receipt.committed_at, "exact_replay")


def _recover_development_bound_effect_establishment_after_fencing(
    *, capability: object, command: object,
) -> DevelopmentBoundEffectEstablishmentRecoveryResultV1:
    checked = _require_exact_development_bound_effect_command(command)
    try:
        receipt = _read_development_mutation_receipt_by_mutation_ref(capability, checked.mutation_ref)
        if receipt is not None:
            if receipt.command_digest != checked.command_digest:
                raise _integrity()
            replay = _read_and_verify_exact_bound_effect_family(
                capability=capability, command=checked, receipt=receipt,
            )
            return DevelopmentBoundEffectEstablishmentRecoveryResultV1(
                DevelopmentBoundEffectEstablishmentRecoveryDispositionV1.COMMITTED_EXACT,
                replay,
            )
        if _collisions(capability, checked):
            raise _integrity()
        return DevelopmentBoundEffectEstablishmentRecoveryResultV1(
            DevelopmentBoundEffectEstablishmentRecoveryDispositionV1.DEFINITELY_NOT_COMMITTED
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return DevelopmentBoundEffectEstablishmentRecoveryResultV1(
            DevelopmentBoundEffectEstablishmentRecoveryDispositionV1.UNRESOLVED
        )


def _execute_development_bound_effect_establishment_writes(
    connection: object, plan: object,
) -> None:
    if type(connection) is not sqlite3.Connection:
        raise _failed() from None
    if type(plan) is not _DevelopmentBoundEffectEstablishmentWritePlan:
        raise _integrity() from None
    rows = (
        plan.effect_intent, plan.effect_fence, plan.authority_evaluation,
        plan.delivery_attempt, plan.effect_head, plan.delivery_head,
        plan.mutation_receipt,
    )
    for statement, (_table, columns), row in zip(_INSERT_SQL, _INSERTS, rows, strict=True):
        if row is plan.mutation_receipt:
            values = tuple(row._values[:19])
        else:
            values = tuple(getattr(row, column) for column in columns)
        cursor = None
        failure: SQLiteMutationStoreError | None = None
        count: object = None
        try:
            cursor = connection.execute(statement, values)
            count = cursor.rowcount
        except sqlite3.Error as error:
            code = getattr(error, "sqlite_errorcode", None)
            if type(code) is int and (code & 0xff) in {
                sqlite3.SQLITE_CONSTRAINT, sqlite3.SQLITE_ERROR,
                sqlite3.SQLITE_SCHEMA, sqlite3.SQLITE_CORRUPT,
            }:
                failure = _integrity()
            else:
                failure = _failed()
        except Exception:
            failure = _failed()
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    if failure is None:
                        failure = _failed()
        if failure is not None:
            raise failure from None
        if type(count) is not int or count != 1:
            raise _integrity() from None
