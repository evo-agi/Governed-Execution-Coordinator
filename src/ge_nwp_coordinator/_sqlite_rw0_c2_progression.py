"""Private artificial P1 family under the fenced Coordinator mutation controller.

The supplied connection is write-only. Every SELECT borrows the nominal
transaction capability. This module has no public package or StateStore route.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Literal, cast

from . import _development_decision_row_values as _decision
from . import _development_program_row_values as _program
from . import _development_effect_row_values as _effect
from ._rw0_c2_progression_contracts import (
    AdmittedCommandRelationV1, ArtificialDecisionGuardSourceV1,
    DecisionBasisV2, ProgressionDecisionCommittedV1,
    ProgressionDecisionConflictV1, ProgressionDecisionRecoveryV1,
    ProgressionDecisionReductionV1, RecordProgressionDecisionCommandV1,
    _RELATION_SCHEMA, _PREASSIGNMENT_FIELDS, _SIBLINGS,
    _canonical, _digest, _self_digest,
    derive_progression_branch, derive_replan_durable_refs,
)
from ._rw0_c2_progression_plan import (
    _P1CurrentRows, _P1WritePlan, _edge, _row, build_p1_write_plan,
    verify_p1_plan_coherence,
)
from ._rw0_c2_progression_rows import (
    _ACCEPTANCE, _BASIS, _CONTINUITY, _RELATION, _RESULT, _SOLE,
    _P1Row, _TABLE_FIELDS, _checked_p1_row,
)
from ._sqlite_rw0_c2_scope_admission import (
    _ACT_TABLE as _P0_ACT, _FACT_TABLE as _P0_FACT,
    _one as _p0_one, _complete_winner_for_act,
)
from ._post_execution_evidence_values import (
    ValidationDispositionV1, IndependentReviewDispositionV1,
)
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from .sqlite_transition_select_support import (
    _MutationReadCapability, _execute_select_fetch_bounded,
)
from .sqlite_transition_read_scope import _read_global_stop_current

__all__: tuple[str, ...] = ()

_GENERIC: dict[str, tuple[tuple[str, ...], object]] = {
    "development_program_heads": (_program._DEVELOPMENT_PROGRAM_HEAD_COLUMNS,
        _program.development_program_head_row_value_from_row_tuple),
    "development_program_versions": (_program._DEVELOPMENT_PROGRAM_VERSION_COLUMNS,
        _program.development_program_version_row_value_from_row_tuple),
    "development_accepted_intent_revisions": (_program._DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS,
        _program.development_accepted_intent_revision_row_value_from_row_tuple),
    "development_work_item_heads": (_program._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS,
        _program.development_work_item_head_row_value_from_row_tuple),
    "development_work_item_revisions": (_program._DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS,
        _program.development_work_item_revision_row_value_from_row_tuple),
    "development_program_version_work_items": (_program._DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS,
        _program.development_program_version_work_item_row_value_from_row_tuple),
    "development_revision_edges": (_program._DEVELOPMENT_REVISION_EDGE_COLUMNS,
        _program.development_revision_edge_row_value_from_row_tuple),
    "development_work_spec_bindings": (_program._DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS,
        _program.development_work_spec_binding_row_value_from_row_tuple),
    "development_decisions": (_decision._DEVELOPMENT_DECISION_COLUMNS,
        _decision.development_decision_row_value_from_row_tuple),
    "development_mutation_receipts": (_decision._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS,
        _decision.development_mutation_receipt_row_value_from_row_tuple),
    "development_semantic_attempts": (_program._DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS,
        _program.development_semantic_attempt_row_value_from_row_tuple),
    "development_attempt_fences": (_effect._DEVELOPMENT_ATTEMPT_FENCE_COLUMNS,
        _effect.development_attempt_fence_row_value_from_row_tuple),
}
_TABLES = frozenset(_GENERIC) | frozenset(_TABLE_FIELDS)
_PRIMARY = {
    "development_decisions": "decision_ref",
    "development_program_versions": "program_version_ref",
    "development_accepted_intent_revisions": "accepted_intent_revision_ref",
    "development_work_item_revisions": "work_item_revision_ref",
    "development_revision_edges": "revision_edge_ref",
    "development_work_spec_bindings": "work_spec_ref",
    "development_mutation_receipts": "mutation_ref",
    _CONTINUITY: "basis_ref", _SOLE: "basis_ref", _BASIS: "basis_ref",
    _RELATION: "relation_ref", _RESULT: "guarded_result_ref",
    _ACCEPTANCE: "acceptance_fact_ref",
}


@dataclass(frozen=True, slots=True)
class _FreshProgression:
    committed: ProgressionDecisionCommittedV1


class _ProtectedPostureUnavailable(Exception):
    """Current source rejected disclosure or recording before family access."""


def _integrity() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def _failed() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)


def _columns(table: str) -> tuple[str, ...]:
    if table in _GENERIC:
        return _GENERIC[table][0]
    if table in _TABLE_FIELDS:
        return _TABLE_FIELDS[table]
    raise _integrity() from None


def _one(capability: object, table: str, where: str,
         parameters: tuple[object, ...]) -> object | None:
    if table not in _TABLES or type(where) is not str or type(parameters) is not tuple:
        raise _integrity() from None
    columns = _columns(table)
    sql = f"SELECT {', '.join(columns)} FROM {table} WHERE {where} LIMIT 2"
    try:
        rows = _execute_select_fetch_bounded(
            capability=cast(_MutationReadCapability, capability),
            sql=sql, parameters=parameters, limit=2)
        if len(rows) > 1:
            raise _integrity()
        if not rows:
            return None
        row = rows[0]
        if type(row) is not tuple or len(row) != len(columns):
            raise _integrity()
        if table in _TABLE_FIELDS:
            return _checked_p1_row(table, row)
        return _GENERIC[table][1](row)  # type: ignore[operator]
    except SQLiteMutationStoreError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None


def _members(capability: object, program_ref: str, version_ref: str,
             *, allow_empty: bool = False) -> tuple[_program.DevelopmentProgramVersionWorkItemRowValue, ...]:
    columns = _columns("development_program_version_work_items")
    sql = (f"SELECT {', '.join(columns)} FROM development_program_version_work_items "
           "WHERE program_ref = ? AND program_version_ref = ? "
           "ORDER BY membership_ordinal LIMIT 257")
    try:
        rows = _execute_select_fetch_bounded(
            capability=cast(_MutationReadCapability, capability), sql=sql,
            parameters=(program_ref, version_ref), limit=257)
        if len(rows) > 256 or not rows and not allow_empty:
            raise _integrity()
        values = tuple(_program.development_program_version_work_item_row_value_from_row_tuple(row)
                       for row in rows)
        if (tuple(item.membership_ordinal for item in values) != tuple(range(len(values)))
            or len({item.work_item_ref for item in values}) != len(values)):
            raise _integrity()
        return values
    except SQLiteMutationStoreError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None


def _checked_p0(capability: object, command: RecordProgressionDecisionCommandV1) -> None:
    basis = command.basis.to_mapping()
    act = cast(dict[str, object], basis["verified_admission_act"])
    fact = cast(dict[str, object], basis["scope_admission_fact"])
    persisted_act = _p0_one(capability, _P0_ACT, "act_ref = ?", (act["act_ref"],))
    persisted_fact = _p0_one(capability, _P0_FACT, "admission_fact_ref = ?",
                             (fact["admission_fact_ref"],))
    if (persisted_act != act or persisted_fact != fact
        or not _complete_winner_for_act(capability, act["act_ref"])):
        raise _integrity() from None


def _require_current(capability: object,
                     command: RecordProgressionDecisionCommandV1) -> _P1CurrentRows:
    relation = command.relation.to_mapping()
    basis = command.basis.to_mapping()
    snapshot = cast(dict[str, object], basis["decision_current_snapshot"])
    program_ref = cast(str, relation["program_ref"])
    head = _one(capability, "development_program_heads", "program_ref = ?", (program_ref,))
    if type(head) is not _program.DevelopmentProgramHeadRowValue:
        raise _integrity() from None
    version = _one(capability, "development_program_versions",
        "program_ref = ? AND program_version_ref = ?",
        (program_ref, head.current_program_version_ref))
    if type(version) is not _program.DevelopmentProgramVersionRowValue:
        raise _integrity() from None
    intent = _one(capability, "development_accepted_intent_revisions",
        "program_ref = ? AND accepted_intent_revision_ref = ?",
        (program_ref, version.accepted_intent_revision_ref))
    work_head = _one(capability, "development_work_item_heads",
        "program_ref = ? AND work_item_ref = ?", (program_ref, snapshot["work_item_ref"]))
    if type(work_head) is not _program.DevelopmentWorkItemHeadRowValue:
        raise _integrity() from None
    work_revision = _one(capability, "development_work_item_revisions",
        "program_ref = ? AND work_item_ref = ? AND work_item_revision_ref = ?",
        (program_ref, work_head.work_item_ref, work_head.current_work_item_revision_ref))
    decision = _one(capability, "development_decisions", "program_ref = ? AND decision_ref = ?",
        (program_ref, version.creating_decision_ref))
    if (type(intent) is not _program.DevelopmentAcceptedIntentRevisionRowValue
        or type(work_revision) is not _program.DevelopmentWorkItemRevisionRowValue
        or type(decision) is not _decision.DevelopmentDecisionRowValue):
        raise _integrity() from None
    members = _members(capability, program_ref, version.program_version_ref)
    attempt = _one(capability, "development_semantic_attempts",
        "program_ref = ? AND semantic_attempt_ref = ?",
        (program_ref, snapshot["semantic_attempt_ref"]))
    fence = _one(capability, "development_attempt_fences",
        "program_ref = ? AND attempt_fence_ref = ?",
        (program_ref, snapshot["attempt_fence_ref"]))
    if (type(attempt) is not _program.DevelopmentSemanticAttemptRowValue
        or type(fence) is not _effect.DevelopmentAttemptFenceRowValue
        or attempt.candidate_ref != snapshot["candidate_ref"]
        or attempt.accepted_intent_revision_ref != intent.accepted_intent_revision_ref
        or attempt.work_item_ref != work_head.work_item_ref
        or attempt.program_version_ref != version.program_version_ref
        or attempt.work_item_revision_ref != work_revision.work_item_revision_ref
        or work_head.current_work_item_revision_number != work_revision.work_item_revision_number
        or work_revision.accepted_intent_revision_ref != intent.accepted_intent_revision_ref
        or fence.attempt_fence_digest != snapshot["attempt_fence_digest"]
        or fence.semantic_attempt_ref != attempt.semantic_attempt_ref
        or fence.program_version_ref != version.program_version_ref
        or fence.accepted_intent_revision_ref != intent.accepted_intent_revision_ref
        or fence.work_item_ref != work_head.work_item_ref
        or fence.work_item_revision_ref != work_revision.work_item_revision_ref):
        raise _integrity() from None
    stop = _read_global_stop_current(capability)
    if (stop.state.stop_ref != snapshot["global_stop_ref"]
        or stop.state.active):
        raise _integrity() from None
    return _P1CurrentRows(head, version, intent, work_head, work_revision,
                          decision, members, stop.state.stop_ref, stop.state.version)


def _insert(connection: sqlite3.Connection, table: str, row: object) -> None:
    if type(connection) is not sqlite3.Connection:
        raise _failed() from None
    columns = _columns(table)
    if table in _TABLE_FIELDS:
        if type(row) is not _P1Row or row.table != table:
            raise _integrity() from None
        values = row.columns
    else:
        if table not in _PRIMARY and table != "development_program_version_work_items":
            raise _integrity() from None
        values = tuple(getattr(row, name) for name in columns)
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})"
    cursor: sqlite3.Cursor | None = None
    try:
        cursor = connection.execute(sql, values)
        if cursor.rowcount != 1:
            raise _integrity()
    except SQLiteMutationStoreError:
        raise
    except sqlite3.Error:
        raise _failed() from None
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except sqlite3.Error:
                raise _failed() from None


def _cas_head(connection: sqlite3.Connection, table: str, before: object,
              after: object) -> None:
    if table not in {"development_program_heads", "development_work_item_heads"}:
        raise _integrity() from None
    columns = _columns(table)
    identity = "program_ref" if table == "development_program_heads" else "work_item_ref"
    set_columns = tuple(column for column in columns if column not in ("schema_id", identity))
    sql = (f"UPDATE {table} SET {', '.join(column + ' = ?' for column in set_columns)} "
           f"WHERE {identity} = ? AND head_revision = ? AND head_digest = ?")
    params = tuple(getattr(after, name) for name in set_columns) + (
        getattr(before, identity), before.head_revision, before.head_digest)
    cursor: sqlite3.Cursor | None = None
    try:
        cursor = connection.execute(sql, params)
        if cursor.rowcount != 1:
            raise _integrity()
    except SQLiteMutationStoreError:
        raise
    except sqlite3.Error:
        raise _failed() from None
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except sqlite3.Error:
                raise _failed() from None


def _plan_rows_exact(capability: object, plan: _P1WritePlan,
                     *, receipt: bool) -> None:
    expected_members = tuple(value for table, value in plan.rows
                             if table == "development_program_version_work_items")
    if not expected_members:
        raise _integrity() from None
    first = expected_members[0]
    observed_members = _members(capability, first.program_ref, first.program_version_ref)
    if observed_members != expected_members:
        raise _integrity() from None
    for table, value in plan.rows:
        if table == "development_program_version_work_items":
            continue
        if table == "development_mutation_receipts" and not receipt:
            continue
        key = _PRIMARY[table]
        expected_ref = value.mapping[key] if type(value) is _P1Row else getattr(value, key)
        if _one(capability, table, key + " = ?", (expected_ref,)) != value:
            raise _integrity() from None


def _historical_current(
    capability: object, command: RecordProgressionDecisionCommandV1,
    recorded_decision: _decision.DevelopmentDecisionRowValue,
) -> _P1CurrentRows:
    """Reconstruct the prior 0002 preimages; the retained v2 witnesses prove postimages."""
    relation = command.relation.to_mapping()
    basis = command.basis.to_mapping()
    snapshot = cast(dict[str, object], basis["decision_current_snapshot"])
    program_ref = cast(str, relation["program_ref"])
    old_version = _one(capability, "development_program_versions",
        "program_ref = ? AND program_version_ref = ?",
        (program_ref, relation["expected_head_ref"]))
    if type(old_version) is not _program.DevelopmentProgramVersionRowValue:
        raise _integrity() from None
    old_decision = _one(capability, "development_decisions",
        "program_ref = ? AND decision_ref = ?",
        (program_ref, old_version.creating_decision_ref))
    old_intent = _one(capability, "development_accepted_intent_revisions",
        "program_ref = ? AND accepted_intent_revision_ref = ?",
        (program_ref, old_version.accepted_intent_revision_ref))
    old_work = _one(capability, "development_work_item_revisions",
        "program_ref = ? AND work_item_ref = ? AND work_item_revision_ref = ?",
        (program_ref, snapshot["work_item_ref"], snapshot["work_item_revision_ref"]))
    if (type(old_decision) is not _decision.DevelopmentDecisionRowValue
        or type(old_intent) is not _program.DevelopmentAcceptedIntentRevisionRowValue
        or type(old_work) is not _program.DevelopmentWorkItemRevisionRowValue):
        raise _integrity() from None
    state = {
        "initial": "active", "repair": "active", "replan": "active",
        "accepted": "accepted", "terminal_rejected": "terminal_rejected",
        "blocked": "blocked",
    }.get(old_version.program_version_kind)
    if state is None:
        raise _integrity() from None
    old_head = _row(table="development_program_heads", fields={
        "schema_id": _program._DEVELOPMENT_PROGRAM_HEAD_SCHEMA,
        "program_ref": program_ref,
        "current_program_version_ref": old_version.program_version_ref,
        "current_program_version_number": old_version.program_version_number,
        "head_revision": relation["expected_head_revision"],
        "program_state": state, "updated_at": old_decision.decided_at,
    }, columns=_program._DEVELOPMENT_PROGRAM_HEAD_COLUMNS,
        digest_field="head_digest",
        adapter=_program.development_program_head_row_value_from_row_tuple)
    old_work_head = _row(table="development_work_item_heads", fields={
        "schema_id": _program._DEVELOPMENT_WORK_ITEM_HEAD_SCHEMA,
        "work_item_ref": old_work.work_item_ref,
        "program_ref": program_ref,
        "current_work_item_revision_ref": old_work.work_item_revision_ref,
        "current_work_item_revision_number": old_work.work_item_revision_number,
        "head_revision": old_work.work_item_revision_number - 1,
        "work_state": "active", "updated_at": old_work.created_at,
    }, columns=_program._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS,
        digest_field="head_digest",
        adapter=_program.development_work_item_head_row_value_from_row_tuple)
    if (old_head.head_digest != relation["expected_head_digest"]
        or old_version.program_version_ref != snapshot["program_version_ref"]
        or old_intent.accepted_intent_revision_ref != snapshot["accepted_intent_revision_ref"]
        or old_decision.decision_ref != old_version.creating_decision_ref
        or recorded_decision.coding_global_stop_ref != snapshot["global_stop_ref"]):
        raise _integrity() from None
    members = _members(capability, program_ref, old_version.program_version_ref)
    return _P1CurrentRows(old_head, old_version, old_intent, old_work_head,
                          old_work, old_decision, members,
                          recorded_decision.coding_global_stop_ref,
                          recorded_decision.coding_global_stop_version)


def _committed_from_plan(command: RecordProgressionDecisionCommandV1,
                         plan: _P1WritePlan) -> ProgressionDecisionCommittedV1:
    relation = command.relation.to_mapping()
    return ProgressionDecisionCommittedV1(
        cast(str, relation["mutation_ref"]), command.command_digest,
        cast(str, relation["preassigned_decision_ref"]),
        cast(str, relation["preassigned_version_ref"]), plan.branch,
        plan.guarded_result_digest, plan.generic_receipt.mutation_graph_digest,
        plan.decided_at,
    )


def _historical_exact(capability: object,
                      command: RecordProgressionDecisionCommandV1,
                      receipt: _decision.DevelopmentMutationReceiptRowValue,
                      ) -> ProgressionDecisionCommittedV1:
    relation = command.relation.to_mapping()
    basis = command.basis.to_mapping()
    if receipt.command_digest != command.command_digest:
        raise ValueError("P1 mutation reference reused")
    _checked_p0(capability, command)
    decision = _one(capability, "development_decisions", "decision_ref = ?",
                    (relation["preassigned_decision_ref"],))
    relation_row = _one(capability, _RELATION, "relation_ref = ?",
                        (relation["preassigned_relation_ref"],))
    continuity_row = _one(capability, _CONTINUITY, "basis_ref = ?",
                          (relation["continuity_basis_ref"],))
    sole_row = _one(capability, _SOLE, "basis_ref = ?",
                    (relation["sole_active_basis_ref"],))
    if (type(decision) is not _decision.DevelopmentDecisionRowValue
        or type(relation_row) is not _P1Row or type(continuity_row) is not _P1Row
        or type(sole_row) is not _P1Row):
        raise _integrity() from None
    if (relation_row.mapping["branch"] not in (
        "candidate_acceptance", "candidate_repair", "attempt_selecting_replan",
        "program_terminal_reject", "post_execution_program_block")
        or relation_row.mapping["mutation_ref"] != relation["mutation_ref"]):
        raise _integrity() from None
    basis_row = _one(capability, _BASIS, "basis_ref = ?", (basis["basis_ref"],))
    if type(basis_row) is not _P1Row:
        raise _integrity() from None
    persisted_basis = DecisionBasisV2.from_json(
        cast(bytes, basis_row.mapping["basis_bytes"]))
    if persisted_basis.canonical_bytes != command.basis.canonical_bytes:
        raise _integrity() from None
    embedded_validation, embedded_review = persisted_basis.typed_dispositions()
    reduction = derive_progression_branch(
        persisted_basis, embedded_validation, embedded_review,
        expected_branch=None, replan_proposal=command.replan_proposal)
    if (type(reduction) is not ProgressionDecisionReductionV1
        or reduction.branch != relation_row.mapping["branch"]
        or reduction.reason_code != decision.reason_code):
        raise _integrity() from None
    current = _historical_current(capability, command, decision)
    continuity = {key: continuity_row.mapping[key] for key in (
        "schema_id", "basis_ref", "source_ref", "source_digest", "lineage_ref",
        "scope_ref", "authority_epoch_ref", "currentness_ref",
        "currentness_digest", "provenance_ref", "provenance_digest",
        "projection_digest")}
    sole = {key: sole_row.mapping[key] for key in (
        "schema_id", "basis_ref", "source_ref", "source_digest", "lineage_ref",
        "scope_ref", "authority_epoch_ref", "currentness_ref",
        "currentness_digest", "active_authority_ref", "sole_active_assertion_ref",
        "sole_active_assertion_digest", "provenance_ref", "provenance_digest",
        "projection_digest")}
    try:
        plan = build_p1_write_plan(command=command, reduction=reduction,
            current=current, continuity=continuity, sole=sole,
            timestamp=receipt.committed_at)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None
    if (plan.generic_receipt != receipt
        or plan.branch != relation_row.mapping["branch"]):
        raise _integrity() from None
    try:
        verify_p1_plan_coherence(plan, command, current)
    except Exception:
        raise _integrity() from None
    _plan_rows_exact(capability, plan, receipt=True)
    return _committed_from_plan(command, plan)


def _read_with_posture(capability: object,
                       command: RecordProgressionDecisionCommandV1,
                       source: ArtificialDecisionGuardSourceV1,
                       timestamp: str, *, write_on_absence: bool,
                       ) -> tuple[ProgressionDecisionCommittedV1 | None,
                                  tuple[dict[str, object], dict[str, object]] | None]:
    relation = command.relation.to_mapping()
    receipt = _one(capability, "development_mutation_receipts",
                   "mutation_ref = ?", (relation["mutation_ref"],))
    if receipt is None:
        try:
            evidence = source.checked_for(command.basis, now=timestamp,
                                          write=write_on_absence)
        except ValueError:
            raise _ProtectedPostureUnavailable() from None
        return None, evidence if write_on_absence else None
    if type(receipt) is not _decision.DevelopmentMutationReceiptRowValue:
        raise _integrity() from None
    try:
        source.checked_for(command.basis, now=timestamp, write=False)
    except ValueError:
        raise _ProtectedPostureUnavailable() from None
    return _historical_exact(capability, command, receipt), None


def read_after_fencing(capability: object,
                       command: RecordProgressionDecisionCommandV1,
                       source: ArtificialDecisionGuardSourceV1,
                       timestamp: str,
                       ) -> ProgressionDecisionCommittedV1 | None:
    return _read_with_posture(capability, command, source, timestamp,
                              write_on_absence=False)[0]


def _route_occupied(capability: object,
                    command: RecordProgressionDecisionCommandV1,
                    *, acceptance_aliases: bool = True) -> bool:
    """Probe every command-derived creation route, including replan successors."""
    relation = command.relation.to_mapping()
    basis = command.basis.to_mapping()
    fact = cast(dict[str, object], basis["scope_admission_fact"])
    snapshot = cast(dict[str, object], basis["decision_current_snapshot"])
    probes: list[tuple[str, str, object]] = [
        ("development_decisions", "decision_ref", relation["preassigned_decision_ref"]),
        ("development_decisions", "mutation_ref", relation["mutation_ref"]),
        ("development_program_versions", "program_version_ref", relation["preassigned_version_ref"]),
        ("development_mutation_receipts", "mutation_ref", relation["mutation_ref"]),
        (_CONTINUITY, "basis_ref", relation["continuity_basis_ref"]),
        (_SOLE, "basis_ref", relation["sole_active_basis_ref"]),
        (_BASIS, "basis_ref", basis["basis_ref"]),
        (_BASIS, "mutation_ref", relation["mutation_ref"]),
        (_RELATION, "relation_ref", relation["preassigned_relation_ref"]),
        (_RELATION, "mutation_ref", relation["mutation_ref"]),
        (_RELATION, "family_route", relation["family_route"]),
        (_RESULT, "guarded_result_ref", relation["preassigned_guarded_result_ref"]),
        (_RESULT, "mutation_ref", relation["mutation_ref"]),
        (_ACCEPTANCE, "acceptance_fact_ref", relation["preassigned_acceptance_fact_ref"]),
    ]
    if acceptance_aliases:
        probes.extend((
            (_ACCEPTANCE, "admission_fact_ref", fact["admission_fact_ref"]),
            (_ACCEPTANCE, "lineage_ref", fact["lineage_ref"]),
            (_ACCEPTANCE, "scope_ref", fact["scope_ref"]),
        ))
    if command.replan_proposal is not None:
        proposal = command.replan_proposal
        intent_ref, work_ref, work_spec_ref = derive_replan_durable_refs(
            command_digest=command.command_digest,
            program_ref=cast(str, relation["program_ref"]),
            current_program_version_ref=cast(str, snapshot["program_version_ref"]),
            current_accepted_intent_revision_ref=cast(str, snapshot["accepted_intent_revision_ref"]),
            work_item_ref=cast(str, snapshot["work_item_ref"]),
            current_work_item_revision_ref=cast(str, snapshot["work_item_revision_ref"]),
            source_intent_ref=proposal.source_intent_ref,
            source_intent_digest=proposal.source_intent_digest,
            work_spec_template_digest=proposal.work_spec_template.digest,
            preassigned_version_ref=cast(str, relation["preassigned_version_ref"]),
        )
        probes.extend((
            ("development_accepted_intent_revisions", "accepted_intent_revision_ref", intent_ref),
            ("development_work_item_revisions", "work_item_revision_ref", work_ref),
            ("development_work_spec_bindings", "work_spec_ref", work_spec_ref),
        ))
        for kind, from_ref, to_ref in (
            ("accepted_intent_supersedes", snapshot["accepted_intent_revision_ref"], intent_ref),
            ("work_item_supersedes", snapshot["work_item_revision_ref"], work_ref),
        ):
            edge = _edge(command_digest=command.command_digest,
                         program_ref=cast(str, relation["program_ref"]),
                         kind=kind, from_ref=cast(str, from_ref), to_ref=to_ref,
                         timestamp="2000-01-01T00:00:00Z")
            probes.append(("development_revision_edges", "revision_edge_ref",
                           edge.revision_edge_ref))
    if any(_one(capability, table, key + " = ?", (value,)) is not None
           for table, key, value in probes):
        return True
    return bool(_members(capability, cast(str, relation["program_ref"]),
                         cast(str, relation["preassigned_version_ref"]),
                         allow_empty=True))


def _competing_acceptance_proof(
    capability: object, command: RecordProgressionDecisionCommandV1,
) -> Literal["absent", "complete", "unresolved"]:
    """Classify local scope claim without exposing a competing winner."""
    fact = cast(dict[str, object], command.basis.to_mapping()["scope_admission_fact"])
    aliases = tuple(_one(capability, _ACCEPTANCE, key + " = ?", (fact[key],))
                    for key in ("admission_fact_ref", "lineage_ref", "scope_ref"))
    present = tuple(row for row in aliases if row is not None)
    if not present:
        return "absent"
    if (any(type(row) is not _P1Row for row in present)
        or len({row.mapping["acceptance_fact_ref"] for row in present}) != 1):
        return "unresolved"
    winner = cast(_P1Row, present[0]).mapping
    mutation_ref = cast(str, winner["mutation_ref"])
    basis_row = _one(capability, _BASIS, "mutation_ref = ?", (mutation_ref,))
    decision = _one(capability, "development_decisions", "mutation_ref = ?", (mutation_ref,))
    continuity = _one(capability, _CONTINUITY, "basis_ref = ?",
                      (basis_row.mapping["continuity_basis_ref"],)) if type(basis_row) is _P1Row else None
    sole = _one(capability, _SOLE, "basis_ref = ?",
                (basis_row.mapping["sole_active_basis_ref"],)) if type(basis_row) is _P1Row else None
    if (type(basis_row) is not _P1Row or type(decision) is not _decision.DevelopmentDecisionRowValue
        or type(continuity) is not _P1Row or type(sole) is not _P1Row):
        return "unresolved"
    basis = DecisionBasisV2.from_json(cast(bytes, basis_row.mapping["basis_bytes"]))
    b = basis.to_mapping()
    a = cast(dict[str, object], b["verified_admission_act"])
    f = cast(dict[str, object], b["scope_admission_fact"])
    old_version = _one(capability, "development_program_versions",
                       "program_version_ref = ?", (decision.basis_program_version_ref,))
    if type(old_version) is not _program.DevelopmentProgramVersionRowValue:
        return "unresolved"
    old_decision = _one(capability, "development_decisions", "decision_ref = ?",
                        (old_version.creating_decision_ref,))
    if type(old_decision) is not _decision.DevelopmentDecisionRowValue:
        return "unresolved"
    old_state = {
        "initial": "active", "repair": "active", "replan": "active",
        "accepted": "accepted", "terminal_rejected": "terminal_rejected",
        "blocked": "blocked",
    }.get(old_version.program_version_kind)
    if old_state is None:
        return "unresolved"
    old_head = _row(table="development_program_heads", fields={
        "schema_id": _program._DEVELOPMENT_PROGRAM_HEAD_SCHEMA,
        "program_ref": decision.program_ref,
        "current_program_version_ref": old_version.program_version_ref,
        "current_program_version_number": old_version.program_version_number,
        "head_revision": decision.expected_program_head_revision,
        "program_state": old_state, "updated_at": old_decision.decided_at,
    }, columns=_program._DEVELOPMENT_PROGRAM_HEAD_COLUMNS,
        digest_field="head_digest",
        adapter=_program.development_program_head_row_value_from_row_tuple)
    c = continuity.mapping
    s = sole.mapping
    relation = {
        "schema_id": _RELATION_SCHEMA,
        "lineage_ref": f["lineage_ref"], "scope_ref": f["scope_ref"],
        "admission_fact_ref": f["admission_fact_ref"],
        "admission_fact_digest": f["admission_fact_digest"],
        "guard_profile": f["guard_profile"], "applicability": f["applicability"],
        "admission_act_ref": a["act_ref"], "admission_act_digest": a["act_digest"],
        "continuity_basis_ref": c["basis_ref"],
        "continuity_basis_digest": c["projection_digest"],
        "continuity_source_ref": c["source_ref"],
        "continuity_source_digest": c["source_digest"],
        "sole_active_basis_ref": s["basis_ref"],
        "sole_active_basis_digest": s["projection_digest"],
        "sole_active_source_ref": s["source_ref"],
        "sole_active_source_digest": s["source_digest"],
        "mutation_ref": mutation_ref, "program_ref": decision.program_ref,
        "decision_basis_ref": b["basis_ref"],
        "decision_basis_digest": b["basis_digest"],
        "expected_head_ref": old_version.program_version_ref,
        "expected_head_revision": old_head.head_revision,
        "expected_head_digest": old_head.head_digest,
    }
    transcript = [(name, _RELATION_SCHEMA if name == "command_profile" else relation[name])
                  for name in _PREASSIGNMENT_FIELDS]
    for name, domain in _SIBLINGS:
        relation[name] = _digest(domain, transcript, ordered=True)
    relation["relation_digest"] = _self_digest(relation, "relation_digest")
    receipt = _one(capability, "development_mutation_receipts",
                   "mutation_ref = ?", (mutation_ref,))
    if type(receipt) is not _decision.DevelopmentMutationReceiptRowValue:
        return "unresolved"
    admitted_relation = AdmittedCommandRelationV1.from_mapping(relation)
    candidates = tuple(RecordProgressionDecisionCommandV1(
        admitted_relation, basis, assertion, None)
        for assertion in (None, "candidate_acceptance"))
    matches = tuple(candidate for candidate in candidates
                    if candidate.command_digest == receipt.command_digest)
    if len(matches) != 1:
        return "unresolved"
    # Internal completeness verification only: no caller-visible result leaves here.
    checked = _historical_exact(capability, matches[0], receipt)
    if (checked.branch == "candidate_acceptance"
        and checked.decision_ref == winner["decision_ref"]
        and checked.mutation_ref != command.relation.to_mapping()["mutation_ref"]):
        return "complete"
    return "unresolved"


def write_fresh_after_fencing(
    capability: object, connection: sqlite3.Connection,
    command: RecordProgressionDecisionCommandV1,
    source: ArtificialDecisionGuardSourceV1,
    validation: ValidationDispositionV1,
    review: IndependentReviewDispositionV1,
    timestamp: str,
) -> _FreshProgression | ProgressionDecisionCommittedV1 | ProgressionDecisionConflictV1:
    """Resolve receipt first, then admit and atomically write one fresh family."""
    if type(connection) is not sqlite3.Connection:
        raise _failed() from None
    embedded_validation, embedded_review = command.basis.typed_dispositions()
    if (validation.to_mapping() != embedded_validation.to_mapping()
        or review.to_mapping() != embedded_review.to_mapping()):
        return ProgressionDecisionConflictV1(
            "basis_identity_lineage_profile_provenance_conflict")
    relation = command.relation.to_mapping()
    try:
        historical, evidence = _read_with_posture(
            capability, command, source, timestamp, write_on_absence=True)
    except _ProtectedPostureUnavailable:
        return ProgressionDecisionConflictV1(
            "basis_identity_lineage_profile_provenance_conflict")
    except ValueError as error:
        if str(error) == "P1 mutation reference reused":
            return ProgressionDecisionConflictV1("mutation_ref_reuse_conflict")
        raise _integrity() from None
    if historical is not None:
        return historical
    if evidence is None:
        raise _integrity() from None
    continuity, sole = evidence
    if _route_occupied(capability, command):
        return ProgressionDecisionConflictV1("preassigned_identity_or_family_route_collision")
    _checked_p0(capability, command)
    current = _require_current(capability, command)
    if (current.program_head.current_program_version_ref != relation["expected_head_ref"]
        or current.program_head.head_revision != relation["expected_head_revision"]
        or current.program_head.head_digest != relation["expected_head_digest"]):
        return ProgressionDecisionConflictV1("stale_caller_expectation")
    reduction = derive_progression_branch(command.basis, embedded_validation, embedded_review,
        expected_branch=command.expected_branch,
        replan_proposal=command.replan_proposal)
    if type(reduction) is ProgressionDecisionConflictV1:
        return reduction
    if type(reduction) is not ProgressionDecisionReductionV1:
        raise _integrity() from None
    if reduction.branch == "candidate_acceptance":
        try:
            source.checked_acceptance_eligibility_for(command.basis)
        except ValueError:
            return ProgressionDecisionConflictV1("bootstrap_acceptance_guard_conflict")
    try:
        plan = build_p1_write_plan(command=command, reduction=reduction,
            current=current, continuity=continuity, sole=sole,
            timestamp=timestamp)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return ProgressionDecisionConflictV1("required_fact_invalid")
    try:
        verify_p1_plan_coherence(plan, command, current)
    except Exception:
        raise _integrity() from None
    for table, row in plan.rows[:-1]:
        _insert(connection, table, row)
    _cas_head(connection, "development_program_heads",
              current.program_head, plan.head_postimage)
    if plan.work_head_postimage is not None:
        _cas_head(connection, "development_work_item_heads",
                  current.work_head, plan.work_head_postimage)
    actual_program = _one(capability, "development_program_heads",
                          "program_ref = ?", (relation["program_ref"],))
    if actual_program != plan.head_postimage:
        raise _integrity() from None
    if plan.work_head_postimage is not None:
        actual_work = _one(capability, "development_work_item_heads",
                           "program_ref = ? AND work_item_ref = ?",
                           (relation["program_ref"], plan.work_head_postimage.work_item_ref))
        if actual_work != plan.work_head_postimage:
            raise _integrity() from None
    _plan_rows_exact(capability, plan, receipt=False)
    _insert(connection, "development_mutation_receipts", plan.generic_receipt)
    return _FreshProgression(_committed_from_plan(command, plan))


def recover_after_fencing(
    capability: object, command: RecordProgressionDecisionCommandV1,
    source: ArtificialDecisionGuardSourceV1,
    timestamp: str,
) -> ProgressionDecisionRecoveryV1:
    try:
        historical = read_after_fencing(capability, command, source, timestamp)
        if historical is not None:
            return ProgressionDecisionRecoveryV1("committed_exact", historical)
        if not source.old_execution_excluded:
            return ProgressionDecisionRecoveryV1("unresolved")
        _checked_p0(capability, command)
        if _route_occupied(capability, command, acceptance_aliases=False):
            return ProgressionDecisionRecoveryV1("unresolved")
        competing = _competing_acceptance_proof(capability, command)
        if (competing == "unresolved"
            or (source.acceptance_exhaustively_unclaimed is False
                and competing != "complete")):
            return ProgressionDecisionRecoveryV1("unresolved")
        return ProgressionDecisionRecoveryV1("definitely_not_committed")
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return ProgressionDecisionRecoveryV1("unresolved")
