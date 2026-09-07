"""Private SQLite mechanics for one route-neutral program-genesis family."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
import typing

from . import _development_decision_row_values as _decision_rows
from . import _development_program_row_values as _program_rows
from ._development_program_initialization_contracts import (
    DevelopmentProgramInitializationCommandV1,
    DevelopmentProgramInitializationConflictReasonV1,
    DevelopmentProgramInitializationConflictV1,
    DevelopmentProgramInitializationRecoveryDispositionV1,
    DevelopmentProgramInitializationRecoveryResultV1,
    DevelopmentProgramInitializationResultV1,
    _DevelopmentProgramInitializationWritePlan,
    _accepted_intent_safe_projection,
    _development_program_initialization_command,
    _development_program_initialization_write_plan,
    _initialization_conflict,
    _initialization_result,
    _require_exact_development_program_initialization_command,
)
from ._development_row_value_support import (
    _RowValueValidationError,
    _require_constant_string,
    _require_nonnegative_integer,
    _require_safe_ref,
    _require_sha256,
)
from ._sqlite_development_readers import (
    _read_development_mutation_receipt_by_mutation_ref,
)
from ._worker_execution_semantic_values import WorkSpecV1
from .persistence_contracts import GlobalStopCurrentRecordEnvelope
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from .sqlite_transition_read_scope import _read_global_stop_current
from .sqlite_transition_select_support import _execute_select_fetch_two


__all__: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, repr=False)
class _FreshDevelopmentProgramInitialization:
    command: DevelopmentProgramInitializationCommandV1

    def __repr__(self) -> str:
        return "<_FreshDevelopmentProgramInitialization>"


def _reduce_development_program_initialization_command(
    *,
    mutation_ref: object,
    program_ref: object,
    program_version_ref: object,
    accepted_intent_revision_ref: object,
    decision_ref: object,
    preassigned_semantic_attempt_ref: object,
    preassigned_candidate_ref: object,
    coding_global_stop_ref: object,
    coding_global_stop_version: object,
    source_intent_ref: object,
    source_intent_digest: object,
    work_spec: object,
    reason_code: object = "program_genesis",
) -> DevelopmentProgramInitializationCommandV1:
    """Reduce one exact transient WorkSpec to a closed safe command."""

    raw_mapping: dict[str, object] | None = None
    checked_work_spec: WorkSpecV1 | None = None
    checked_mutation_ref: str | None = None
    checked_program_ref: str | None = None
    checked_program_version_ref: str | None = None
    checked_accepted_intent_revision_ref: str | None = None
    checked_decision_ref: str | None = None
    checked_semantic_attempt_ref: str | None = None
    checked_candidate_ref: str | None = None
    checked_global_stop_ref: str | None = None
    checked_global_stop_version: int | None = None
    checked_source_intent_ref: str | None = None
    checked_source_intent_digest: str | None = None
    checked_reason_code: str | None = None
    work_projection: _program_rows.DevelopmentWorkSpecSafeProjection | None = None
    accepted_projection = None
    result: DevelopmentProgramInitializationCommandV1 | None = None
    ordinary_failure = False
    try:
        checked_mutation_ref = _require_safe_ref(mutation_ref)
        checked_program_ref = _require_safe_ref(program_ref)
        checked_program_version_ref = _require_safe_ref(program_version_ref)
        checked_accepted_intent_revision_ref = _require_safe_ref(
            accepted_intent_revision_ref
        )
        checked_decision_ref = _require_safe_ref(decision_ref)
        checked_semantic_attempt_ref = _require_safe_ref(
            preassigned_semantic_attempt_ref
        )
        checked_candidate_ref = _require_safe_ref(preassigned_candidate_ref)
        checked_global_stop_ref = _require_safe_ref(coding_global_stop_ref)
        checked_global_stop_version = _require_nonnegative_integer(
            coding_global_stop_version
        )
        checked_source_intent_ref = _require_safe_ref(source_intent_ref)
        checked_source_intent_digest = _require_sha256(source_intent_digest)
        checked_reason_code = _require_constant_string(reason_code, "program_genesis")
        if type(work_spec) is not WorkSpecV1:
            ordinary_failure = True
        else:
            raw_mapping = work_spec.to_mapping()
            if type(raw_mapping) is not dict:
                ordinary_failure = True
            else:
                checked_work_spec = WorkSpecV1.from_mapping(raw_mapping)
                if (
                    checked_work_spec.program_ref != checked_program_ref
                    or checked_work_spec.program_version_ref
                    != checked_program_version_ref
                    or checked_work_spec.accepted_intent_revision_ref
                    != checked_accepted_intent_revision_ref
                ):
                    ordinary_failure = True
                else:
                    work_projection = (
                        _program_rows.development_work_spec_safe_projection_from_work_spec(
                            work_spec=checked_work_spec
                        )
                    )
                    accepted_projection = _accepted_intent_safe_projection(
                        source_intent_ref=checked_source_intent_ref,
                        source_intent_digest=checked_source_intent_digest,
                        work_spec_safe_projection=work_projection,
                    )
                    result = _development_program_initialization_command(
                        mutation_ref=checked_mutation_ref,
                        program_ref=checked_program_ref,
                        program_version_ref=checked_program_version_ref,
                        accepted_intent_revision_ref=(
                            checked_accepted_intent_revision_ref
                        ),
                        decision_ref=checked_decision_ref,
                        preassigned_semantic_attempt_ref=(
                            checked_semantic_attempt_ref
                        ),
                        preassigned_candidate_ref=checked_candidate_ref,
                        coding_global_stop_ref=checked_global_stop_ref,
                        coding_global_stop_version=checked_global_stop_version,
                        reason_code=checked_reason_code,
                        work_spec_safe_projection=work_projection,
                        accepted_intent_safe_projection=accepted_projection,
                    )
    except SQLiteMutationStoreError:
        ordinary_failure = True
    except Exception:
        ordinary_failure = True
    finally:
        if type(raw_mapping) is dict:
            raw_mapping.clear()
        raw_mapping = None
        checked_work_spec = None
        checked_mutation_ref = None
        checked_program_ref = None
        checked_program_version_ref = None
        checked_accepted_intent_revision_ref = None
        checked_decision_ref = None
        checked_semantic_attempt_ref = None
        checked_candidate_ref = None
        checked_global_stop_ref = None
        checked_global_stop_version = None
        checked_source_intent_ref = None
        checked_source_intent_digest = None
        checked_reason_code = None
        work_projection = None
        accepted_projection = None
        work_spec = None
        mutation_ref = None
        program_ref = None
        program_version_ref = None
        accepted_intent_revision_ref = None
        decision_ref = None
        preassigned_semantic_attempt_ref = None
        preassigned_candidate_ref = None
        coding_global_stop_ref = None
        coding_global_stop_version = None
        source_intent_ref = None
        source_intent_digest = None
        reason_code = None
    if ordinary_failure or type(result) is not DevelopmentProgramInitializationCommandV1:
        result = None
        raise _database_integrity_failure() from None
    return result


def _resolve_development_program_initialization_apply_after_fencing(
    *,
    capability: object,
    command: object,
) -> (
    DevelopmentProgramInitializationResultV1
    | DevelopmentProgramInitializationConflictV1
    | _FreshDevelopmentProgramInitialization
):
    checked = _require_exact_development_program_initialization_command(command)

    receipt_digest = _read_receipt_command_digest(
        capability, checked.mutation_ref
    )
    if receipt_digest is not None:
        if receipt_digest != checked.command_digest:
            return _initialization_conflict(
                checked,
                DevelopmentProgramInitializationConflictReasonV1.MUTATION_REF_REUSE_CONFLICT,
            )
        return _read_and_verify_exact_initialization(capability, checked)

    stop_envelope = _read_global_stop_current(capability)
    if type(stop_envelope) is not GlobalStopCurrentRecordEnvelope:
        raise _database_integrity_failure() from None
    stop = stop_envelope.state
    if (
        stop.stop_ref != checked.coding_global_stop_ref
        or stop.version != checked.coding_global_stop_version
    ):
        return _initialization_conflict(
            checked,
            DevelopmentProgramInitializationConflictReasonV1.GLOBAL_STOP_VERSION_CONFLICT,
        )
    if stop.active:
        return _initialization_conflict(
            checked,
            DevelopmentProgramInitializationConflictReasonV1.CODING_GLOBAL_STOP_ACTIVE,
        )

    if _selected_family_identity_exists(capability, checked):
        return _initialization_conflict(
            checked,
            DevelopmentProgramInitializationConflictReasonV1.SEMANTIC_IDENTITY_CONFLICT,
        )
    return _FreshDevelopmentProgramInitialization(checked)


def _recover_development_program_initialization_after_fencing(
    *,
    capability: object,
    command: object,
) -> DevelopmentProgramInitializationRecoveryResultV1:
    checked = _require_exact_development_program_initialization_command(command)
    try:
        receipt_digest = _read_receipt_command_digest(
            capability, checked.mutation_ref
        )
        if receipt_digest is not None:
            if receipt_digest != checked.command_digest:
                return _unresolved_recovery()
            try:
                replay = _read_and_verify_exact_initialization(capability, checked)
            except SQLiteMutationStoreError:
                return _unresolved_recovery()
            if type(replay) is not DevelopmentProgramInitializationResultV1:
                return _unresolved_recovery()
            return DevelopmentProgramInitializationRecoveryResultV1(
                disposition=DevelopmentProgramInitializationRecoveryDispositionV1.COMMITTED_EXACT,
                committed_result=replay,
            )
        if _selected_family_identity_exists(capability, checked):
            return _unresolved_recovery()
        return DevelopmentProgramInitializationRecoveryResultV1(
            disposition=DevelopmentProgramInitializationRecoveryDispositionV1.DEFINITELY_NOT_COMMITTED
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return _unresolved_recovery()
    finally:
        command = None
        checked = None


def _unresolved_recovery() -> DevelopmentProgramInitializationRecoveryResultV1:
    return DevelopmentProgramInitializationRecoveryResultV1(
        disposition=DevelopmentProgramInitializationRecoveryDispositionV1.UNRESOLVED
    )


def _read_receipt_command_digest(
    capability: object,
    mutation_ref: str,
) -> str | None:
    rows = _execute_select_fetch_two(
        capability=capability,
        sql=(
            "SELECT command_digest FROM development_mutation_receipts "
            "WHERE mutation_ref = ? LIMIT 2"
        ),
        parameters=(mutation_ref,),
    )
    if len(rows) == 0:
        return None
    if len(rows) != 1 or type(rows[0]) is not tuple or len(rows[0]) != 1:
        raise _database_integrity_failure() from None
    try:
        return _require_sha256(rows[0][0])
    except _RowValueValidationError:
        raise _database_integrity_failure() from None
    finally:
        rows = []


def _selected_family_identity_exists(
    capability: object,
    command: DevelopmentProgramInitializationCommandV1,
) -> bool:
    work = command.work_spec_safe_projection
    probes = (
        (
            "SELECT 1 FROM development_program_heads WHERE program_ref = ? LIMIT 2",
            (command.program_ref,),
        ),
        (
            "SELECT 1 FROM development_program_versions "
            "WHERE program_version_ref = ? OR (program_ref = ? AND program_version_number = 1) LIMIT 2",
            (command.program_version_ref, command.program_ref),
        ),
        (
            "SELECT 1 FROM development_accepted_intent_revisions "
            "WHERE accepted_intent_revision_ref = ? OR (program_ref = ? AND accepted_intent_revision_number = 1) LIMIT 2",
            (command.accepted_intent_revision_ref, command.program_ref),
        ),
        (
            "SELECT 1 FROM development_decisions "
            "WHERE decision_ref = ? OR mutation_ref = ? LIMIT 2",
            (command.decision_ref, command.mutation_ref),
        ),
        (
            "SELECT 1 FROM development_work_item_heads WHERE work_item_ref = ? LIMIT 2",
            (work.work_item_ref,),
        ),
        (
            "SELECT 1 FROM development_work_item_revisions "
            "WHERE work_item_revision_ref = ? OR "
            "(program_ref = ? AND work_item_ref = ? AND work_item_revision_number = 1) LIMIT 2",
            (work.work_item_revision_ref, command.program_ref, work.work_item_ref),
        ),
        (
            "SELECT 1 FROM development_program_version_work_items "
            "WHERE program_ref = ? AND program_version_ref = ? LIMIT 2",
            (command.program_ref, command.program_version_ref),
        ),
        (
            "SELECT 1 FROM development_work_spec_bindings "
            "WHERE work_spec_ref = ? OR "
            "(program_ref = ? AND program_version_ref = ? AND work_item_ref = ? "
            "AND work_item_revision_ref = ?) LIMIT 2",
            (
                work.work_spec_ref,
                command.program_ref,
                command.program_version_ref,
                work.work_item_ref,
                work.work_item_revision_ref,
            ),
        ),
    )
    for sql, parameters in probes:
        rows = _execute_select_fetch_two(
            capability=capability, sql=sql, parameters=parameters
        )
        if rows:
            rows = []
            return True
    return False


def _read_and_verify_exact_initialization(
    capability: object,
    command: DevelopmentProgramInitializationCommandV1,
) -> DevelopmentProgramInitializationResultV1:
    receipt = _read_development_mutation_receipt_by_mutation_ref(
        capability, command.mutation_ref
    )
    if receipt is None:
        raise _database_integrity_failure() from None
    expected = _development_program_initialization_write_plan(
        command, receipt.committed_at
    )
    if receipt != expected.mutation_receipt:
        raise _database_integrity_failure() from None

    actual_program_head = _read_one_row(
        capability,
        table="development_program_heads",
        columns=_program_rows._DEVELOPMENT_PROGRAM_HEAD_COLUMNS,
        where="program_ref = ?",
        parameters=(command.program_ref,),
        adapter=_program_rows.development_program_head_row_value_from_row_tuple,
    )
    actual_intent = _read_one_row(
        capability,
        table="development_accepted_intent_revisions",
        columns=_program_rows._DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS,
        where="program_ref = ? AND accepted_intent_revision_ref = ?",
        parameters=(command.program_ref, command.accepted_intent_revision_ref),
        adapter=_program_rows.development_accepted_intent_revision_row_value_from_row_tuple,
    )
    actual_work_head = _read_one_row(
        capability,
        table="development_work_item_heads",
        columns=_program_rows._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS,
        where="program_ref = ? AND work_item_ref = ?",
        parameters=(command.program_ref, command.work_spec_safe_projection.work_item_ref),
        adapter=_program_rows.development_work_item_head_row_value_from_row_tuple,
    )
    actual_work_revision = _read_one_row(
        capability,
        table="development_work_item_revisions",
        columns=_program_rows._DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS,
        where="program_ref = ? AND work_item_ref = ? AND work_item_revision_ref = ?",
        parameters=(
            command.program_ref,
            command.work_spec_safe_projection.work_item_ref,
            command.work_spec_safe_projection.work_item_revision_ref,
        ),
        adapter=_program_rows.development_work_item_revision_row_value_from_row_tuple,
    )
    actual_decision = _read_one_row(
        capability,
        table="development_decisions",
        columns=_decision_rows._DEVELOPMENT_DECISION_COLUMNS,
        where="program_ref = ? AND decision_ref = ?",
        parameters=(command.program_ref, command.decision_ref),
        adapter=_decision_rows.development_decision_row_value_from_row_tuple,
    )
    actual_version = _read_one_row(
        capability,
        table="development_program_versions",
        columns=_program_rows._DEVELOPMENT_PROGRAM_VERSION_COLUMNS,
        where="program_ref = ? AND program_version_ref = ?",
        parameters=(command.program_ref, command.program_version_ref),
        adapter=_program_rows.development_program_version_row_value_from_row_tuple,
    )
    actual_membership = _read_one_row(
        capability,
        table="development_program_version_work_items",
        columns=_program_rows._DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS,
        where="program_ref = ? AND program_version_ref = ?",
        parameters=(command.program_ref, command.program_version_ref),
        adapter=_program_rows.development_program_version_work_item_row_value_from_row_tuple,
    )
    actual_binding = _read_one_row(
        capability,
        table="development_work_spec_bindings",
        columns=_program_rows._DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS,
        where=(
            "program_ref = ? AND program_version_ref = ? AND work_item_ref = ? "
            "AND work_item_revision_ref = ?"
        ),
        parameters=(
            command.program_ref,
            command.program_version_ref,
            command.work_spec_safe_projection.work_item_ref,
            command.work_spec_safe_projection.work_item_revision_ref,
        ),
        adapter=_program_rows.development_work_spec_binding_row_value_from_row_tuple,
    )

    if (
        actual_intent != expected.accepted_intent_revision
        or actual_work_revision != expected.work_item_revision
        or actual_decision != expected.initialize_decision
        or actual_version != expected.program_version
        or actual_membership != expected.program_version_work_item
        or actual_binding != expected.work_spec_binding
    ):
        raise _database_integrity_failure() from None
    if not _program_head_and_current_version_are_coherent(
        capability=capability,
        command=command,
        actual_head=actual_program_head,
        genesis_head=expected.program_head,
        genesis_version=actual_version,
        committed_at=receipt.committed_at,
    ):
        raise _database_integrity_failure() from None
    if not _work_head_and_current_revision_are_coherent(
        capability=capability,
        command=command,
        actual_head=actual_work_head,
        genesis_head=expected.work_item_head,
        genesis_revision=actual_work_revision,
        committed_at=receipt.committed_at,
    ):
        raise _database_integrity_failure() from None
    return _initialization_result(command, receipt.committed_at, "exact_replay")


def _read_one_row(
    capability: object,
    *,
    table: str,
    columns: tuple[str, ...],
    where: str,
    parameters: tuple[object, ...],
    adapter: typing.Callable[[object], object],
) -> object:
    sql = f"SELECT {', '.join(columns)} FROM {table} WHERE {where} LIMIT 2"
    rows = _execute_select_fetch_two(
        capability=capability, sql=sql, parameters=parameters
    )
    if len(rows) != 1:
        raise _database_integrity_failure() from None
    row = rows[0]
    rows = []
    return adapter(row)


def _program_head_is_genesis_or_valid_later(
    actual: object,
    genesis: _program_rows.DevelopmentProgramHeadRowValue,
    committed_at: str,
) -> bool:
    if type(actual) is not _program_rows.DevelopmentProgramHeadRowValue:
        return False
    if actual == genesis:
        return True
    return bool(
        actual.program_ref == genesis.program_ref
        and actual.head_revision > genesis.head_revision
        and actual.current_program_version_number >= genesis.current_program_version_number
        and actual.updated_at >= committed_at
    )


def _work_head_is_genesis_or_valid_later(
    actual: object,
    genesis: _program_rows.DevelopmentWorkItemHeadRowValue,
    committed_at: str,
) -> bool:
    if type(actual) is not _program_rows.DevelopmentWorkItemHeadRowValue:
        return False
    if actual == genesis:
        return True
    return bool(
        actual.program_ref == genesis.program_ref
        and actual.work_item_ref == genesis.work_item_ref
        and actual.head_revision > genesis.head_revision
        and actual.current_work_item_revision_number
        >= genesis.current_work_item_revision_number
        and actual.updated_at >= committed_at
    )


def _program_head_and_current_version_are_coherent(
    *,
    capability: object,
    command: DevelopmentProgramInitializationCommandV1,
    actual_head: object,
    genesis_head: _program_rows.DevelopmentProgramHeadRowValue,
    genesis_version: object,
    committed_at: str,
) -> bool:
    if not _program_head_is_genesis_or_valid_later(
        actual_head, genesis_head, committed_at
    ):
        return False
    if (
        type(actual_head) is not _program_rows.DevelopmentProgramHeadRowValue
        or type(genesis_version) is not _program_rows.DevelopmentProgramVersionRowValue
    ):
        return False
    if actual_head.current_program_version_ref == genesis_version.program_version_ref:
        referenced_version = genesis_version
    else:
        referenced_version = _read_one_row(
            capability,
            table="development_program_versions",
            columns=_program_rows._DEVELOPMENT_PROGRAM_VERSION_COLUMNS,
            where="program_ref = ? AND program_version_ref = ?",
            parameters=(
                actual_head.program_ref,
                actual_head.current_program_version_ref,
            ),
            adapter=_program_rows.development_program_version_row_value_from_row_tuple,
        )
    return bool(
        type(referenced_version) is _program_rows.DevelopmentProgramVersionRowValue
        and referenced_version.program_ref
        == actual_head.program_ref
        == command.program_ref
        and referenced_version.program_version_ref
        == actual_head.current_program_version_ref
        and referenced_version.program_version_number
        == actual_head.current_program_version_number
    )


def _work_head_and_current_revision_are_coherent(
    *,
    capability: object,
    command: DevelopmentProgramInitializationCommandV1,
    actual_head: object,
    genesis_head: _program_rows.DevelopmentWorkItemHeadRowValue,
    genesis_revision: object,
    committed_at: str,
) -> bool:
    if not _work_head_is_genesis_or_valid_later(
        actual_head, genesis_head, committed_at
    ):
        return False
    if (
        type(actual_head) is not _program_rows.DevelopmentWorkItemHeadRowValue
        or type(genesis_revision)
        is not _program_rows.DevelopmentWorkItemRevisionRowValue
    ):
        return False
    if (
        actual_head.current_work_item_revision_ref
        == genesis_revision.work_item_revision_ref
    ):
        referenced_revision = genesis_revision
    else:
        referenced_revision = _read_one_row(
            capability,
            table="development_work_item_revisions",
            columns=_program_rows._DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS,
            where=(
                "program_ref = ? AND work_item_ref = ? "
                "AND work_item_revision_ref = ?"
            ),
            parameters=(
                actual_head.program_ref,
                actual_head.work_item_ref,
                actual_head.current_work_item_revision_ref,
            ),
            adapter=_program_rows.development_work_item_revision_row_value_from_row_tuple,
        )
    work = command.work_spec_safe_projection
    return bool(
        type(referenced_revision)
        is _program_rows.DevelopmentWorkItemRevisionRowValue
        and referenced_revision.program_ref
        == actual_head.program_ref
        == command.program_ref
        and referenced_revision.work_item_ref
        == actual_head.work_item_ref
        == work.work_item_ref
        and referenced_revision.work_item_revision_ref
        == actual_head.current_work_item_revision_ref
        and referenced_revision.work_item_revision_number
        == actual_head.current_work_item_revision_number
    )


def _execute_development_program_initialization_writes(
    connection: object,
    plan: object,
) -> None:
    if type(connection) is not sqlite3.Connection:
        raise _mutation_failed() from None
    if type(plan) is not _DevelopmentProgramInitializationWritePlan:
        raise _database_integrity_failure() from None
    ordered = (
        (
            "development_program_heads",
            _program_rows._DEVELOPMENT_PROGRAM_HEAD_COLUMNS,
            _program_head_parameters(plan.program_head),
        ),
        (
            "development_accepted_intent_revisions",
            _program_rows._DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS,
            _accepted_intent_parameters(plan.accepted_intent_revision),
        ),
        (
            "development_work_item_heads",
            _program_rows._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS,
            _work_head_parameters(plan.work_item_head),
        ),
        (
            "development_work_item_revisions",
            _program_rows._DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS,
            _work_revision_parameters(plan.work_item_revision),
        ),
        (
            "development_decisions",
            _decision_rows._DEVELOPMENT_DECISION_COLUMNS,
            _decision_parameters(plan.initialize_decision),
        ),
        (
            "development_program_versions",
            _program_rows._DEVELOPMENT_PROGRAM_VERSION_COLUMNS,
            _program_version_parameters(plan.program_version),
        ),
        (
            "development_program_version_work_items",
            _program_rows._DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS,
            _membership_parameters(plan.program_version_work_item),
        ),
        (
            "development_work_spec_bindings",
            _program_rows._DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS,
            _binding_parameters(plan.work_spec_binding),
        ),
        (
            "development_mutation_receipts",
            _decision_rows._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS,
            _receipt_parameters(plan.mutation_receipt),
        ),
    )
    for table, columns, parameters in ordered:
        _execute_insert(connection, table, columns, parameters)


def _execute_insert(
    connection: sqlite3.Connection,
    table: str,
    columns: tuple[str, ...],
    parameters: tuple[object, ...],
) -> None:
    sql = (
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES "
        f"({', '.join('?' for _ in columns)})"
    )
    cursor = None
    failure: SQLiteMutationStoreError | None = None
    rowcount: object = None
    try:
        cursor = connection.execute(sql, parameters)
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


def _program_head_parameters(row: object) -> tuple[object, ...]:
    if type(row) is not _program_rows.DevelopmentProgramHeadRowValue:
        raise _database_integrity_failure() from None
    return tuple(row._values)


def _accepted_intent_parameters(row: object) -> tuple[object, ...]:
    if type(row) is not _program_rows.DevelopmentAcceptedIntentRevisionRowValue:
        raise _database_integrity_failure() from None
    return tuple(row._values)


def _work_head_parameters(row: object) -> tuple[object, ...]:
    if type(row) is not _program_rows.DevelopmentWorkItemHeadRowValue:
        raise _database_integrity_failure() from None
    return tuple(row._values)


def _work_revision_parameters(row: object) -> tuple[object, ...]:
    if type(row) is not _program_rows.DevelopmentWorkItemRevisionRowValue:
        raise _database_integrity_failure() from None
    return tuple(row._values)


def _program_version_parameters(row: object) -> tuple[object, ...]:
    if type(row) is not _program_rows.DevelopmentProgramVersionRowValue:
        raise _database_integrity_failure() from None
    return tuple(row._values)


def _membership_parameters(row: object) -> tuple[object, ...]:
    if type(row) is not _program_rows.DevelopmentProgramVersionWorkItemRowValue:
        raise _database_integrity_failure() from None
    return tuple(row._values)


def _binding_parameters(row: object) -> tuple[object, ...]:
    if type(row) is not _program_rows.DevelopmentWorkSpecBindingRowValue:
        raise _database_integrity_failure() from None
    safe = row.safe_projection
    return (
        row.schema_id,
        row.work_spec_ref,
        row.program_ref,
        row.program_version_ref,
        row.accepted_intent_revision_ref,
        row.work_item_ref,
        row.work_item_revision_ref,
        row.repository_ref,
        row.base_git_object_format,
        row.base_git_oid,
        row.authorized_paths_json,
        row.validation_requirement_ref,
        row.review_requirement_ref,
        row.privacy_classification,
        row.work_spec_digest,
        safe.safe_projection_digest,
        row.recorded_at,
        row.work_spec_binding_digest,
    )


def _decision_parameters(row: object) -> tuple[object, ...]:
    if type(row) is not _decision_rows.DevelopmentDecisionRowValue:
        raise _database_integrity_failure() from None
    return tuple(row.decision._values) + (row.decision_digest,)


def _receipt_parameters(row: object) -> tuple[object, ...]:
    if type(row) is not _decision_rows.DevelopmentMutationReceiptRowValue:
        raise _database_integrity_failure() from None
    return tuple(row._values[:19])


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
