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
from ._rw0_terminal_outcome_rows import (
    CONTEXT, OUTCOME, RESULT, RECEIPT, COLUMNS, PRIMARY, TABLES,
    TerminalRow, checked_row,
)
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


def _route_occupied(capability: object, command: RecordRW0TerminalOutcomeCommandV1) -> bool:
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
    return any(_one(capability, table, column, value) is not None
               for table, column, value in probes)


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
    receipt = _one(capability, RECEIPT, "mutation_ref",
                   command.to_mapping()["mutation_ref"])
    _disclosure(command, source, timestamp, recording=False)
    if receipt is None:
        return None
    return _historical_exact(capability, command, receipt)


def write_fresh_after_fencing(
    capability: object, connection: sqlite3.Connection,
    command: RecordRW0TerminalOutcomeCommandV1,
    source: ArtificialDecisionGuardSourceV1, timestamp: str,
) -> FreshTerminal | TerminalCommittedV1 | TerminalConflictV1:
    receipt = _one(capability, RECEIPT, "mutation_ref",
                   command.to_mapping()["mutation_ref"])
    try:
        _disclosure(command, source, timestamp, recording=receipt is None)
    except ProtectedPostureUnavailable:
        return TerminalConflictV1("protected_posture_unavailable")
    if receipt is not None:
        try:
            return _historical_exact(capability, command, receipt)
        except ValueError as exc:
            if str(exc) == "terminal_command_reused":
                return TerminalConflictV1("command_reuse")
            raise
    safe = command.to_mapping()
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
    if _route_occupied(capability, command):
        return TerminalConflictV1("route_collision")
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
        winner = _one(capability, CONTEXT, "phase_basis_ref",
                      command.to_mapping()["phase_basis_ref"])
        if winner is not None:
            if winner.mapping["mutation_ref"] == command.to_mapping()["mutation_ref"]:
                return TerminalRecoveryV1("unresolved")
            other_receipt = _one(capability, RECEIPT, "mutation_ref",
                                 winner.mapping["mutation_ref"])
            if other_receipt is None:
                return TerminalRecoveryV1("unresolved")
            try:
                _historical_exact(capability, command, other_receipt)
            except ValueError as exc:
                if str(exc) != "terminal_command_reused":
                    return TerminalRecoveryV1("unresolved")
            except Exception:
                return TerminalRecoveryV1("unresolved")
            if _original_alias_occupied_excluding_phase(capability, command):
                return TerminalRecoveryV1("unresolved")
            return TerminalRecoveryV1("definitely_not_committed")
        if _route_occupied(capability, command):
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
