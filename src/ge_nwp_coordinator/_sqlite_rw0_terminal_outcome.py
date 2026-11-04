"""Private fenced normal RW0 terminal family; no connection or lease ownership."""
from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import cast

from . import _cognitive_proposal_row_values as _cognitive
from . import _development_decision_row_values as _decision
from . import _development_program_row_values as _program
from ._rw0_c2_progression_contracts import ArtificialDecisionGuardSourceV1
from ._rw0_c2_progression_rows import _P1Row, _RELATION, _RESULT, _ACCEPTANCE
from ._rw0_terminal_outcome_contracts import (
    EVIDENCE_ROLES, HEAD_ROLES, NORMAL_PAIRS, PROFILE,
    RecordRW0TerminalOutcomeCommandV1, TerminalCommittedV1,
    TerminalConflictV1, TerminalRecoveryV1, _canonical, _strict_bytes,
)
from ._rw0_terminal_outcome_plan import (
    TerminalFacts, TerminalPlan, build_terminal_plan, snapshot_compatible,
)
from ._rw0_terminal_head_witness import (
    TerminalHeadWitness, witness_from_bytes, witness_from_typed,
)
from ._rw0_terminal_anchor_rows import TerminalAnchorRow, expected_normal_anchor
from ._rw0_terminal_outcome_rows import (
    CONTEXT, OUTCOME, RESULT, RECEIPT, COLUMNS, PRIMARY, TABLES,
    TerminalRow, checked_row,
)
from ._sqlite_rw0_terminal_anchor import read_terminal_anchor
from ._sqlite_development_pre_execution_plan_disposition import _read_exact_row
from ._sqlite_rw0_c1 import (
    _read_rw0_c1_checked_family_after_fencing, _verify_phase_family_rows,
)
from ._sqlite_rw0_c1_readers import (
    _read_phase_by_pair, _read_relation_set, _read_receipt,
)
from ._sqlite_rw0_c2_progression import (
    _historical_exact as _p1_historical_exact, _one as _p1_one,
)
from ._sqlite_section41_post_execution_proposal import read_checked_family_after_fencing
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from .sqlite_transition_read_scope import _read_global_stop_current
from .sqlite_transition_select_support import (
    _MutationReadCapability, _execute_select_fetch_bounded,
)

__all__: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FreshTerminal:
    committed: TerminalCommittedV1


class ProtectedPostureUnavailable(Exception):
    """No protected row or occupancy detail may escape this boundary."""


def _integrity() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def _failed() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)


def _one(capability: object, table: str, column: str, value: object) -> TerminalRow | None:
    if table not in TABLES or column not in COLUMNS[table]:
        raise _integrity() from None
    sql = (f"SELECT {', '.join(COLUMNS[table])} FROM {table} "
           f"WHERE {column} = ? LIMIT 2")
    try:
        rows = _execute_select_fetch_bounded(
            capability=cast(_MutationReadCapability, capability),
            sql=sql, parameters=(value,), limit=2,
        )
        if len(rows) > 1:
            raise _integrity()
        return checked_row(table, rows[0]) if rows else None
    except SQLiteMutationStoreError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None


def _insert(connection: sqlite3.Connection, row: TerminalRow) -> None:
    if type(connection) is not sqlite3.Connection or type(row) is not TerminalRow:
        raise _failed() from None
    columns = COLUMNS[row.table]
    sql = (f"INSERT INTO {row.table} ({', '.join(columns)}) "
           f"VALUES ({', '.join('?' for _ in columns)})")
    cursor: sqlite3.Cursor | None = None
    failure: SQLiteMutationStoreError | None = None
    try:
        cursor = connection.execute(sql, row.values)
        if cursor.rowcount != 1:
            failure = _integrity()
    except sqlite3.IntegrityError:
        failure = _integrity()
    except sqlite3.Error:
        failure = _failed()
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        failure = _failed()
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except sqlite3.Error:
                failure = failure or _failed()
    if failure is not None:
        raise failure from None


def _disclosure(
    command: RecordRW0TerminalOutcomeCommandV1,
    source: ArtificialDecisionGuardSourceV1, timestamp: str,
    *, recording: bool,
) -> None:
    try:
        source.checked_for(command.p1_command.basis, now=timestamp, write=False)
        if recording:
            source.checked_for(command.p1_command.basis, now=timestamp, write=True)
    except ValueError:
        raise ProtectedPostureUnavailable() from None


def _phase_checked(capability: object, command: RecordRW0TerminalOutcomeCommandV1) -> None:
    selector = command.to_mapping()
    phase = _read_phase_by_pair(
        capability, selector["phase_basis_ref"], selector["phase_basis_digest"])
    if phase is None:
        raise _integrity() from None
    receipt = _read_receipt(capability, phase.value("establishment_mutation_ref"))
    relation = _read_relation_set(
        capability, phase_basis_ref=selector["phase_basis_ref"],
        membership_ref=None)
    if receipt is None:
        raise _integrity() from None
    _verify_phase_family_rows(phase, relation, receipt, capability=capability)


def _predecessors(
    capability: object, command: RecordRW0TerminalOutcomeCommandV1,
) -> TerminalFacts:
    """Read every historical owner with the current operation's nominal capability."""
    try:
        _phase_checked(capability, command)
        post = read_checked_family_after_fencing(capability, command.section41_command)
        if post is None:
            raise _integrity()
        c1 = _read_rw0_c1_checked_family_after_fencing(
            capability=capability, selector=command.c1_rank15)
        if (c1.admission_result.kind_rank != 15
            or c1.admission_result.phase_basis_ref != post.command.phase_basis_ref
            or c1.admission_result.phase_basis_digest != post.command.phase_basis_digest
            or c1.evidence_value.proposal_ref != post.proposal.proposal_ref
            or c1.evidence_value.proposal_digest != post.proposal.proposal_digest):
            raise _integrity()
        # The existing owner projection reconstructs the full checked V22
        # graph, including the rank-15 relation, from these same-capability
        # checked families. The import is local to avoid a module import cycle.
        from ._rw0_d2_post_execution_continuation import _project
        projection = _project(post, c1)
        basis = command.p1_command.basis.to_mapping()
        if basis["proposal_family_projection"] != projection.to_mapping():
            raise _integrity()
        validation, review = command.p1_command.basis.typed_dispositions()
        for index, disposition in ((2, validation), (3, review)):
            evidence = post.evidence[index]
            if (evidence.evidence_role != EVIDENCE_ROLES[index]
                or evidence.evidence_ref != disposition.disposition_ref
                or evidence.evidence_digest != disposition.disposition_digest):
                raise _integrity()
        relation = command.p1_command.relation.to_mapping()
        p1_receipt = _p1_one(
            capability, "development_mutation_receipts", "mutation_ref = ?",
            (relation["mutation_ref"],))
        if type(p1_receipt) is not _decision.DevelopmentMutationReceiptRowValue:
            raise _integrity()
        prior = _p1_historical_exact(capability, command.p1_command, p1_receipt)
        decision = _p1_one(capability, "development_decisions", "decision_ref = ?",
                           (prior.decision_ref,))
        p1_relation = _p1_one(capability, _RELATION, "relation_ref = ?",
                              (relation["preassigned_relation_ref"],))
        p1_result = _p1_one(capability, _RESULT, "guarded_result_ref = ?",
                            (relation["preassigned_guarded_result_ref"],))
        if (type(decision) is not _decision.DevelopmentDecisionRowValue
            or type(p1_relation) is not _P1Row or type(p1_result) is not _P1Row
            or prior.branch not in NORMAL_PAIRS):
            raise _integrity()
        acceptance = None
        if prior.branch == "candidate_acceptance":
            acceptance = _p1_one(
                capability, _ACCEPTANCE, "acceptance_fact_ref = ?",
                (relation["preassigned_acceptance_fact_ref"],))
            if type(acceptance) is not _P1Row:
                raise _integrity()
        manifest = command.to_mapping()["reached_owners"]
        if (manifest[15]["digest"] != decision.decision_digest
            or manifest[16]["digest"] != prior.result_digest
            or manifest[17]["digest"] != p1_receipt.mutation_graph_digest):
            raise _integrity()
        facts = TerminalFacts(prior, decision, p1_relation, p1_result,
                              p1_receipt, acceptance, post, c1)
        return facts
    except SQLiteMutationStoreError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None


def _current(
    capability: object, command: RecordRW0TerminalOutcomeCommandV1,
) -> tuple[TerminalHeadWitness, dict[str, object]]:
    relation = command.p1_command.relation.to_mapping()
    basis = command.p1_command.basis.to_mapping()
    snapshot = cast(dict[str, object], basis["decision_current_snapshot"])
    program_ref = cast(str, relation["program_ref"])
    phase = _read_phase_by_pair(capability, command.section41_command.phase_basis_ref,
                                command.section41_command.phase_basis_digest)
    if phase is None:
        raise _integrity() from None
    effect_ref = cast(str, phase.value("effect_intent_ref"))
    program = _p1_one(capability, "development_program_heads",
                      "program_ref = ?", (program_ref,))
    work = _p1_one(capability, "development_work_item_heads",
                   "program_ref = ? AND work_item_ref = ?",
                   (program_ref, snapshot["work_item_ref"]))
    selection = _read_exact_row(
        capability, table="development_pre_execution_selection_heads",
        where="program_ref = ? AND effect_intent_ref = ?",
        parameters=(program_ref, effect_ref))
    from ._sqlite_development_readers import (
        _read_development_effect_head, _read_development_delivery_head,
    )
    effect = _read_development_effect_head(capability, program_ref, effect_ref)
    delivery_aggregate = _read_development_delivery_head(capability, program_ref, effect_ref)
    stop_envelope = _read_global_stop_current(capability)
    if (type(program) is not _program.DevelopmentProgramHeadRowValue
        or type(work) is not _program.DevelopmentWorkItemHeadRowValue
        or type(selection) is not _cognitive.DevelopmentPreExecutionSelectionHeadRowValue
        or effect is None or delivery_aggregate is None):
        raise _integrity() from None
    delivery = delivery_aggregate.delivery_head
    try:
        witness = witness_from_typed((program, work, selection, effect, delivery))
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None
    state = stop_envelope.state
    stop = {"ref": state.stop_ref, "version": state.version,
            "state": "active" if state.active else "clear",
            "updated_at": stop_envelope.updated_at}
    return witness, stop


def _route_occupied(
    capability: object, command: RecordRW0TerminalOutcomeCommandV1,
    checked_anchors: tuple[TerminalAnchorRow, ...],
) -> bool:
    """Reject any normal-family alias outside the checked registered families."""
    safe = command.to_mapping()
    probes = (
        (CONTEXT, "context_ref", safe["context_ref"]),
        (CONTEXT, "mutation_ref", safe["mutation_ref"]),
        (CONTEXT, "phase_basis_ref", safe["phase_basis_ref"]),
        (CONTEXT, "p1_decision_ref", safe["p1"]["relation"]["preassigned_decision_ref"]),
        (OUTCOME, "outcome_value_ref", safe["outcome_value_ref"]),
        (OUTCOME, "phase_basis_ref", safe["phase_basis_ref"]),
        (OUTCOME, "decision_ref", safe["p1"]["relation"]["preassigned_decision_ref"]),
        (RESULT, "result_ref", safe["result_ref"]),
        (RESULT, "outcome_value_ref", safe["outcome_value_ref"]),
        (RECEIPT, "receipt_ref", safe["receipt_ref"]),
        (RECEIPT, "mutation_ref", safe["mutation_ref"]),
        (RECEIPT, "family_route", safe["family_route"]),
        (RECEIPT, "phase_basis_ref", safe["phase_basis_ref"]),
        (RECEIPT, "p1_decision_ref", safe["p1"]["relation"]["preassigned_decision_ref"]),
        (RECEIPT, "context_ref", safe["context_ref"]),
        (RECEIPT, "outcome_value_ref", safe["outcome_value_ref"]),
        (RECEIPT, "result_ref", safe["result_ref"]),
    )
    registered = {
        table: {anchor.mapping[PRIMARY[table]] for anchor in checked_anchors}
        for table in TABLES
    }
    occupied = False
    for table, column, value in probes:
        row = _one(capability, table, column, value)
        if row is not None:
            if row.mapping[PRIMARY[table]] not in registered[table]:
                raise _integrity() from None
            occupied = True
    return occupied


def _original_alias_occupied_excluding_phase(
    capability: object, command: RecordRW0TerminalOutcomeCommandV1,
) -> bool:
    safe = command.to_mapping()
    probes = (
        (CONTEXT, "context_ref", safe["context_ref"]),
        (CONTEXT, "mutation_ref", safe["mutation_ref"]),
        (OUTCOME, "outcome_value_ref", safe["outcome_value_ref"]),
        (RESULT, "result_ref", safe["result_ref"]),
        (RESULT, "outcome_value_ref", safe["outcome_value_ref"]),
        (RECEIPT, "receipt_ref", safe["receipt_ref"]),
        (RECEIPT, "mutation_ref", safe["mutation_ref"]),
        (RECEIPT, "family_route", safe["family_route"]),
        (RECEIPT, "context_ref", safe["context_ref"]),
        (RECEIPT, "outcome_value_ref", safe["outcome_value_ref"]),
        (RECEIPT, "result_ref", safe["result_ref"]),
    )
    return any(_one(capability, table, column, value) is not None
               for table, column, value in probes)


def _plan_exact(capability: object, plan: TerminalPlan, *, receipt: bool) -> None:
    for row in plan.rows:
        if row.table == RECEIPT and not receipt:
            continue
        actual = _one(capability, row.table, PRIMARY[row.table],
                      row.mapping[PRIMARY[row.table]])
        if actual != row:
            raise _integrity() from None


def _anchor_family_exact(capability: object, anchor: TerminalAnchorRow) -> object:
    """Check the selected persisted family before interpreting its receipt."""
    a = anchor.mapping
    if a["family_profile"] != PROFILE:
        from ._rw0_cancel_pre_effect_terminal_rows import PROFILE as CANCEL_PROFILE
        if a["family_profile"] != CANCEL_PROFILE:
            raise _integrity() from None
        from ._sqlite_rw0_cancel_pre_effect_terminal import family_from_anchor
        return family_from_anchor(capability, anchor)
    context = _one(capability, CONTEXT, "context_ref", a["context_ref"])
    outcome = _one(capability, OUTCOME, "outcome_value_ref", a["outcome_value_ref"])
    result = _one(capability, RESULT, "result_ref", a["result_ref"])
    receipt = _one(capability, RECEIPT, "receipt_ref", a["receipt_ref"])
    if any(row is None for row in (context, outcome, result, receipt)):
        raise _integrity() from None
    try:
        expected = expected_normal_anchor(
            cast(TerminalRow, context), cast(TerminalRow, outcome),
            cast(TerminalRow, result), cast(TerminalRow, receipt),
        )
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None
    if expected != anchor:
        raise _integrity() from None
    return cast(TerminalRow, receipt)


def _checked_anchor_aliases(
    capability: object, command: RecordRW0TerminalOutcomeCommandV1,
) -> tuple[TerminalAnchorRow, ...]:
    """Probe all seven unique aliases and verify each selected family once."""
    safe = command.to_mapping()
    probes = (
        ("family_route", safe["family_route"]),
        ("mutation_ref", safe["mutation_ref"]),
        ("decision_ref", safe["p1"]["relation"]["preassigned_decision_ref"]),
        ("context_ref", safe["context_ref"]),
        ("outcome_value_ref", safe["outcome_value_ref"]),
        ("result_ref", safe["result_ref"]),
        ("receipt_ref", safe["receipt_ref"]),
    )
    checked: dict[str, TerminalAnchorRow] = {}
    for column, value in probes:
        anchor = read_terminal_anchor(capability, column, value)
        if anchor is None:
            continue
        phase_ref = cast(str, anchor.mapping["phase_basis_ref"])
        prior = checked.get(phase_ref)
        if prior is not None:
            if prior != anchor:
                raise _integrity() from None
            continue
        _anchor_family_exact(capability, anchor)
        checked[phase_ref] = anchor
    return tuple(checked.values())


def _historical_exact(
    capability: object, command: RecordRW0TerminalOutcomeCommandV1,
    receipt: TerminalRow,
) -> TerminalCommittedV1:
    context = _one(capability, CONTEXT, "context_ref", receipt.mapping["context_ref"])
    if context is None:
        raise _integrity() from None
    try:
        recorded = RecordRW0TerminalOutcomeCommandV1(
            context.mapping["command_safe_bytes"], command.p1_command,
            command.section41_command, command.c1_rank15)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None
    witness = witness_from_bytes(context.mapping["closure_heads_bytes"])
    stop = _strict_bytes(context.mapping["closure_stop_bytes"], limit=1024)["stop"]
    facts = _predecessors(capability, recorded)
    if not snapshot_compatible(recorded, facts, witness):
        raise _integrity() from None
    plan = build_terminal_plan(recorded, facts, witness, stop, context.mapping["recorded_at"])
    if plan.rows[3] != receipt:
        raise _integrity() from None
    _plan_exact(capability, plan, receipt=True)
    if recorded.safe_bytes != command.safe_bytes or recorded.command_digest != command.command_digest:
        raise ValueError("terminal_command_reused") from None
    return plan.committed


def read_after_fencing(
    capability: object, command: RecordRW0TerminalOutcomeCommandV1,
    source: ArtificialDecisionGuardSourceV1, timestamp: str,
) -> TerminalCommittedV1 | None:
    _disclosure(command, source, timestamp, recording=False)
    safe = command.to_mapping()
    anchor = read_terminal_anchor(capability, "phase_basis_ref", safe["phase_basis_ref"])
    from ._sqlite_rw0_cancel_pre_effect_terminal import check_phase_route_rows
    check_phase_route_rows(capability, cast(str, safe["phase_basis_ref"]), anchor)
    if anchor is None:
        aliases = _checked_anchor_aliases(capability, command)
        _route_occupied(capability, command, aliases)
        if aliases:
            raise _integrity() from None
        return None
    receipt = _anchor_family_exact(capability, anchor)
    if anchor.mapping["family_profile"] != PROFILE:
        aliases = _checked_anchor_aliases(capability, command)
        _route_occupied(capability, command, (anchor, *aliases))
        return None
    if anchor.mapping["mutation_ref"] != safe["mutation_ref"]:
        aliases = _checked_anchor_aliases(capability, command)
        _route_occupied(capability, command, (anchor, *aliases))
        return None
    return _historical_exact(capability, command, receipt)


def write_fresh_after_fencing(
    capability: object, connection: sqlite3.Connection,
    command: RecordRW0TerminalOutcomeCommandV1,
    source: ArtificialDecisionGuardSourceV1, timestamp: str,
) -> FreshTerminal | TerminalCommittedV1 | TerminalConflictV1:
    try:
        _disclosure(command, source, timestamp, recording=False)
    except ProtectedPostureUnavailable:
        return TerminalConflictV1("protected_posture_unavailable")
    safe = command.to_mapping()
    anchor = read_terminal_anchor(capability, "phase_basis_ref", safe["phase_basis_ref"])
    from ._sqlite_rw0_cancel_pre_effect_terminal import check_phase_route_rows
    check_phase_route_rows(capability, cast(str, safe["phase_basis_ref"]), anchor)
    if anchor is not None and anchor.mapping["mutation_ref"] == safe["mutation_ref"]:
        receipt = _anchor_family_exact(capability, anchor)
        if anchor.mapping["family_profile"] != PROFILE:
            _route_occupied(capability, command, (anchor,))
            return TerminalConflictV1("route_collision")
        try:
            return _historical_exact(capability, command, receipt)
        except ValueError as exc:
            if str(exc) == "terminal_command_reused":
                aliases = _checked_anchor_aliases(capability, command)
                _route_occupied(capability, command, (anchor, *aliases))
                return TerminalConflictV1("command_reuse")
            raise
    if anchor is not None:
        _anchor_family_exact(capability, anchor)
        aliases = _checked_anchor_aliases(capability, command)
        _route_occupied(capability, command, (anchor, *aliases))
        return TerminalConflictV1("route_collision")
    try:
        _disclosure(command, source, timestamp, recording=True)
    except ProtectedPostureUnavailable:
        return TerminalConflictV1("protected_posture_unavailable")
    aliases = _checked_anchor_aliases(capability, command)
    _route_occupied(capability, command, aliases)
    if aliases:
        return TerminalConflictV1("route_collision")
    facts = _predecessors(capability, command)
    witness, stop = _current(capability, command)
    if witness.coordinates != tuple(safe["heads"]) or stop != safe["stop"]:
        return TerminalConflictV1("stale_currentness")
    if not snapshot_compatible(command, facts, witness):
        return TerminalConflictV1("stale_currentness")
    if (safe["expected_branch"] is not None and safe["expected_branch"] != facts.prior.branch
        or safe["expected_outcome"] is not None
           and safe["expected_outcome"] != NORMAL_PAIRS[facts.prior.branch]):
        return TerminalConflictV1("predecessor_mismatch")
    try:
        plan = build_terminal_plan(command, facts, witness, stop, timestamp)
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None
    for row in plan.rows[:3]:
        _insert(connection, row)
    _plan_exact(capability, plan, receipt=False)
    _insert(connection, plan.rows[3])
    _plan_exact(capability, plan, receipt=True)
    inserted_anchor = read_terminal_anchor(capability, "phase_basis_ref", safe["phase_basis_ref"])
    if inserted_anchor is None:
        raise _integrity() from None
    _anchor_family_exact(capability, inserted_anchor)
    return FreshTerminal(plan.committed)


def recover_after_fencing(
    capability: object, command: RecordRW0TerminalOutcomeCommandV1,
    source: ArtificialDecisionGuardSourceV1, timestamp: str,
) -> TerminalRecoveryV1:
    try:
        exact = read_after_fencing(capability, command, source, timestamp)
        if exact is not None:
            return TerminalRecoveryV1("committed_exact", exact)
        # A different transient P1 operand cannot prove the original operation
        # absent. Reauthenticate it under this same fenced capability first.
        _predecessors(capability, command)
        winner = read_terminal_anchor(
            capability, "phase_basis_ref", command.to_mapping()["phase_basis_ref"])
        if winner is not None:
            if winner.mapping["mutation_ref"] == command.to_mapping()["mutation_ref"]:
                return TerminalRecoveryV1("unresolved")
            other_receipt = _anchor_family_exact(capability, winner)
            try:
                _historical_exact(capability, command, other_receipt)
            except ValueError as exc:
                if str(exc) != "terminal_command_reused":
                    return TerminalRecoveryV1("unresolved")
            except Exception:
                return TerminalRecoveryV1("unresolved")
            aliases = _checked_anchor_aliases(capability, command)
            if (any(alias != winner for alias in aliases)
                or _original_alias_occupied_excluding_phase(capability, command)):
                return TerminalRecoveryV1("unresolved")
            return TerminalRecoveryV1("definitely_not_committed")
        aliases = _checked_anchor_aliases(capability, command)
        if aliases:
            return TerminalRecoveryV1("unresolved")
        if _route_occupied(capability, command, aliases):
            return TerminalRecoveryV1("unresolved")
        if not source.old_execution_excluded:
            return TerminalRecoveryV1("unresolved")
        # The original phase route is unique. An absent route with positive
        # old-execution exclusion is a complete negative only after protected
        # predecessor disclosure and the exhaustive route probe above.
        return TerminalRecoveryV1("definitely_not_committed")
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return TerminalRecoveryV1("unresolved")
