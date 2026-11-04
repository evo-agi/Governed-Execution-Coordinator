"""Fenced cancel-bound pre-effect block through the shared terminal registry."""
from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from ._rw0_cancel_pre_effect_terminal_contracts import (
    RecordRW0CancelPreEffectTerminalCommandV1, CancelTerminalCommittedV1,
    CancelTerminalConflictV1, CancelTerminalRecoveryV1,
)
from ._rw0_cancel_pre_effect_terminal_plan import build_cancel_terminal_plan, CancelTerminalPlan
from ._rw0_cancel_pre_effect_terminal_rows import (
    CONTEXT, OUTCOME, RESULT, RECEIPT, COLUMNS, PRIMARY, PROFILE,
    CancelTerminalRow, checked_row,
)
from ._rw0_terminal_anchor_rows import TerminalAnchorRow, expected_cancel_anchor
from ._sqlite_rw0_terminal_anchor import read_terminal_anchor
from ._rw0_cancel_decision_rows import RECEIPT as DECISION_RECEIPT
from ._sqlite_rw0_cancel_decision import _one as _decision_one, _family_exact as _decision_family
from ._rw0_cancel_decision_contracts import RecordRW0ActiveCancelDecisionCommandV1
from ._sqlite_rw0_cancel_currentness import check_coordinator_facts
from ._rw0_terminal_outcome_contracts import _canonical
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from .sqlite_transition_select_support import _MutationReadCapability, _execute_select_fetch_bounded

__all__: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FreshCancelTerminal:
    committed: CancelTerminalCommittedV1


def unresolved_recovery() -> CancelTerminalRecoveryV1:
    return CancelTerminalRecoveryV1("unresolved")


def _integrity() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def _one(capability: object, table: str, key: str, value: object) -> CancelTerminalRow | None:
    if table not in COLUMNS or key not in COLUMNS[table]:
        raise _integrity() from None
    try:
        rows = _execute_select_fetch_bounded(
            capability=cast(_MutationReadCapability, capability),
            sql=f"SELECT {', '.join(COLUMNS[table])} FROM {table} WHERE {key}=? LIMIT 2",
            parameters=(value,), limit=2)
        if len(rows) > 1:
            raise _integrity()
        return checked_row(table, rows[0]) if rows else None
    except SQLiteMutationStoreError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None


def check_phase_route_rows(capability: object, phase_basis_ref: str,
                           anchor: TerminalAnchorRow | None) -> None:
    """Bounded phase aliases must be exactly the rows selected by the anchor."""
    from ._rw0_terminal_outcome_rows import CONTEXT as NC, OUTCOME as NO, RECEIPT as NR
    from ._rw0_terminal_outcome_contracts import PROFILE as NORMAL_PROFILE
    for table, primary, profile in (
        (NC, "context_ref", NORMAL_PROFILE), (NO, "outcome_value_ref", NORMAL_PROFILE),
        (NR, "receipt_ref", NORMAL_PROFILE), (CONTEXT, "context_ref", PROFILE),
        (OUTCOME, "outcome_value_ref", PROFILE), (RECEIPT, "receipt_ref", PROFILE),
    ):
        try:
            rows = _execute_select_fetch_bounded(
                capability=cast(_MutationReadCapability, capability),
                sql=f"SELECT {primary} FROM {table} WHERE phase_basis_ref=? LIMIT 2",
                parameters=(phase_basis_ref,), limit=2)
            if (len(rows) > 1 or any(type(row) is not tuple or len(row) != 1
                                     or type(row[0]) is not str for row in rows)):
                raise _integrity()
            actual = rows[0][0] if rows else None
            expected = (anchor.mapping[primary] if anchor is not None
                        and anchor.mapping["family_profile"] == profile else None)
            if actual != expected:
                raise _integrity()
        except SQLiteMutationStoreError:
            raise
        except (KeyboardInterrupt, SystemExit, GeneratorExit):
            raise
        except Exception:
            raise _integrity() from None


def _original_family(capability: object, command: RecordRW0CancelPreEffectTerminalCommandV1) -> RecordRW0ActiveCancelDecisionCommandV1:
    m = command.to_mapping()
    receipt = _decision_one(capability, DECISION_RECEIPT, "receipt_ref", m["decision_receipt_ref"])
    if receipt is None:
        raise _integrity() from None
    plan = _decision_family(capability, receipt)
    d = plan.committed
    if (d.decision_ref != m["decision_ref"] or d.decision_digest != m["decision_digest"]
        or d.receipt_digest != m["decision_receipt_digest"]
        or receipt.mapping["command_digest"] != m["decision_command_digest"]):
        raise _integrity() from None
    original = RecordRW0ActiveCancelDecisionCommandV1(cast(bytes, receipt.mapping["command_safe_bytes"]))
    if (original.to_mapping()["phase_basis_ref"] != m["phase_basis_ref"]
        or original.to_mapping()["phase_basis_digest"] != m["phase_basis_digest"]
        or original.to_mapping()["target"]["effect_intent_ref"] != m["target_effect_intent_ref"]):
        raise _integrity() from None
    return original


def family_from_anchor(capability: object, anchor: TerminalAnchorRow) -> CancelTerminalRow:
    """Validate the selected four-row family and its original decision."""
    if type(anchor) is not TerminalAnchorRow or anchor.mapping["family_profile"] != PROFILE:
        raise _integrity() from None
    a = anchor.mapping
    rows = tuple(_one(capability, table, PRIMARY[table], a[PRIMARY[table]])
                 for table in (CONTEXT, OUTCOME, RESULT, RECEIPT))
    if any(row is None for row in rows):
        raise _integrity() from None
    c, o, x, r = cast(tuple[CancelTerminalRow, CancelTerminalRow, CancelTerminalRow, CancelTerminalRow], rows)
    try:
        expected = expected_cancel_anchor(c, o, x, r)
        if expected != anchor:
            raise _integrity()
        command = RecordRW0CancelPreEffectTerminalCommandV1(cast(bytes, c.mapping["command_safe_bytes"]))
        plan = build_cancel_terminal_plan(command, cast(str, r.mapping["recorded_at"]))
        if plan.rows != rows or plan.anchor != anchor:
            raise _integrity()
        _original_family(capability, command)
        return r
    except SQLiteMutationStoreError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None


def _validated_alias_anchors(capability: object,
                             command: RecordRW0CancelPreEffectTerminalCommandV1) -> set[str]:
    """Inspect every declared family and registry alias before classification."""
    m = command.to_mapping()
    probes = (
        (CONTEXT, "context_ref", m["context_ref"]),
        (CONTEXT, "mutation_ref", m["mutation_ref"]),
        (CONTEXT, "decision_ref", m["decision_ref"]),
        (CONTEXT, "decision_receipt_ref", m["decision_receipt_ref"]),
        (OUTCOME, "outcome_value_ref", m["outcome_value_ref"]),
        (OUTCOME, "context_ref", m["context_ref"]),
        (OUTCOME, "decision_ref", m["decision_ref"]),
        (RESULT, "result_ref", m["result_ref"]),
        (RESULT, "outcome_value_ref", m["outcome_value_ref"]),
        (RESULT, "context_ref", m["context_ref"]),
        (RECEIPT, "receipt_ref", m["receipt_ref"]),
        (RECEIPT, "mutation_ref", m["mutation_ref"]),
        (RECEIPT, "family_route", m["family_route"]),
        (RECEIPT, "decision_ref", m["decision_ref"]),
        (RECEIPT, "context_ref", m["context_ref"]),
        (RECEIPT, "outcome_value_ref", m["outcome_value_ref"]),
        (RECEIPT, "result_ref", m["result_ref"]),
    )
    anchors: dict[str, TerminalAnchorRow] = {}
    from ._sqlite_rw0_terminal_outcome import _anchor_family_exact
    for table, key, value in probes:
        row = _one(capability, table, key, value)
        if row is None:
            continue
        primary = PRIMARY[table]
        anchor = read_terminal_anchor(capability, primary, row.mapping[primary])
        if (anchor is None or anchor.mapping["family_profile"] != PROFILE
            or anchor.mapping[primary] != row.mapping[primary]):
            raise _integrity() from None
        anchors[cast(str, anchor.mapping["phase_basis_ref"])] = anchor
    for column in ("family_route", "mutation_ref", "decision_ref", "context_ref",
                   "outcome_value_ref", "result_ref", "receipt_ref"):
        anchor = read_terminal_anchor(capability, column, m[column])
        if anchor is not None:
            anchors[cast(str, anchor.mapping["phase_basis_ref"])] = anchor
    for anchor in anchors.values():
        check_phase_route_rows(capability, cast(str, anchor.mapping["phase_basis_ref"]), anchor)
        _anchor_family_exact(capability, anchor)
    return set(anchors)


def _historical_exact(capability: object, command: RecordRW0CancelPreEffectTerminalCommandV1,
                      receipt: CancelTerminalRow) -> CancelTerminalCommittedV1 | CancelTerminalConflictV1:
    r = receipt.mapping
    context = _one(capability, CONTEXT, "context_ref", r["context_ref"])
    if context is None:
        raise _integrity() from None
    saved = RecordRW0CancelPreEffectTerminalCommandV1(cast(bytes, context.mapping["command_safe_bytes"]))
    plan = build_cancel_terminal_plan(saved, cast(str, r["recorded_at"]))
    if plan.rows[3] != receipt:
        raise _integrity() from None
    for row in plan.rows:
        if _one(capability, row.table, PRIMARY[row.table], row.mapping[PRIMARY[row.table]]) != row:
            raise _integrity() from None
    _original_family(capability, saved)
    if saved.safe_bytes != command.safe_bytes:
        return CancelTerminalConflictV1("command_reuse")
    return plan.committed


def read_after_fencing(capability: object,
                       command: RecordRW0CancelPreEffectTerminalCommandV1) -> CancelTerminalCommittedV1 | CancelTerminalConflictV1 | None:
    m = command.to_mapping()
    anchor = read_terminal_anchor(capability, "phase_basis_ref", m["phase_basis_ref"])
    check_phase_route_rows(capability, cast(str, m["phase_basis_ref"]), anchor)
    aliases = _validated_alias_anchors(capability, command)
    if anchor is None:
        return CancelTerminalConflictV1("command_reuse") if aliases else None
    from ._sqlite_rw0_terminal_outcome import _anchor_family_exact
    selected = _anchor_family_exact(capability, anchor)
    if anchor.mapping["family_profile"] != PROFILE or anchor.mapping["mutation_ref"] != m["mutation_ref"]:
        return CancelTerminalConflictV1("occupied_phase")
    if type(selected) is not CancelTerminalRow:
        raise _integrity() from None
    return _historical_exact(capability, command, selected)


def _insert(connection: object, row: CancelTerminalRow) -> None:
    columns = COLUMNS[row.table]
    from .sqlite_transition_transaction import _insert_cancel_sqlite_row
    _insert_cancel_sqlite_row(connection, row.table, columns, row.values)


def write_after_fencing(capability: object, connection: object,
                        command: RecordRW0CancelPreEffectTerminalCommandV1,
                        timestamp: str) -> FreshCancelTerminal | CancelTerminalCommittedV1 | CancelTerminalConflictV1:
    prior = read_after_fencing(capability, command)
    if prior is not None:
        return prior
    original = _original_family(capability, command)
    current = check_coordinator_facts(capability, original)
    m = command.to_mapping()
    if current.classification == "integrity_failure":
        raise _integrity() from None
    if (current.classification != "proven_coordinator_mismatch"
        or (current.mismatch_class, current.mismatch_ref, current.mismatch_digest)
            != (m["mismatch_class"], m["mismatch_ref"], m["mismatch_digest"])
        or current.heads_bytes != _canonical(m["heads"])
        or current.stop_bytes != _canonical(m["stop"])
        or current.verification_safe_bytes != _canonical(m["verification"])):
        return CancelTerminalConflictV1("mismatch_not_current")
    plan = build_cancel_terminal_plan(command, timestamp)
    for row in plan.rows:
        _insert(connection, row)
    anchor = read_terminal_anchor(capability, "phase_basis_ref", m["phase_basis_ref"])
    if anchor != plan.anchor or family_from_anchor(capability, plan.anchor) != plan.rows[3]:
        raise _integrity() from None
    return FreshCancelTerminal(plan.committed)


def recover_after_fencing(capability: object,
                          command: RecordRW0CancelPreEffectTerminalCommandV1) -> CancelTerminalRecoveryV1:
    try:
        exact = read_after_fencing(capability, command)
        if type(exact) is CancelTerminalCommittedV1:
            return CancelTerminalRecoveryV1("committed_exact", exact)
        _original_family(capability, command)
        if exact is None or type(exact) is CancelTerminalConflictV1:
            return CancelTerminalRecoveryV1("definitely_not_committed")
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        pass
    return CancelTerminalRecoveryV1("unresolved")
