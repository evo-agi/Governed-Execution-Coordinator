"""Read-only sequence-10 proof of both admitted terminal families."""
from __future__ import annotations

from ._rw0_terminal_anchor_rows import COLUMNS as ANCHOR_COLUMNS, checked_anchor_row, expected_normal_anchor, expected_cancel_anchor
from ._rw0_terminal_outcome_rows import COLUMNS as NORMAL_COLUMNS, CONTEXT as NC, OUTCOME as NO, RESULT as NX, RECEIPT as NR, checked_row as normal_row
from ._rw0_cancel_pre_effect_terminal_rows import COLUMNS as CANCEL_COLUMNS, CONTEXT as CC, OUTCOME as CO, RESULT as CX, RECEIPT as CR, checked_row as cancel_row
from ._rw0_cancel_pre_effect_terminal_contracts import RecordRW0CancelPreEffectTerminalCommandV1
from ._rw0_cancel_pre_effect_terminal_plan import build_cancel_terminal_plan
from ._rw0_cancel_decision_contracts import RecordRW0ActiveCancelDecisionCommandV1
from ._rw0_cancel_decision_rows import (
    COLUMNS as DECISION_COLUMNS, BINDING as DB, RECEIPT as DR,
    checked_row as decision_row, required_roles,
)
from ._rw0_cancel_decision_plan import build_cancel_decision_plan

__all__: tuple[str, ...] = ()


def _one(connection: object, table: str, columns: tuple[str, ...], key: str,
         value: object, checker: object) -> object:
    rows = connection.execute(  # type: ignore[attr-defined]
        f"SELECT {', '.join(columns)} FROM {table} WHERE {key}=? LIMIT 2", (value,)
    ).fetchmany(2)
    if type(rows) is not list or len(rows) != 1:
        raise ValueError("incomplete terminal family")
    return checker(table, rows[0])  # type: ignore[operator]


def _checked_cancel_terminal_witness(connection: object, context: object,
                                     rows: tuple[object, object, object, object],
                                     anchor: object) -> None:
    """Read saved immutable witnesses; present heads and stop are not rechecked."""
    c = context.mapping  # type: ignore[attr-defined]
    command = RecordRW0CancelPreEffectTerminalCommandV1(c["command_safe_bytes"])
    terminal_plan = build_cancel_terminal_plan(command, c["recorded_at"])
    if terminal_plan.rows != rows or terminal_plan.anchor != anchor:
        raise ValueError("contradictory cancel terminal command")
    terminal = command.to_mapping()
    receipt = _one(connection, DR, DECISION_COLUMNS[DR], "receipt_ref",
                   terminal["decision_receipt_ref"], decision_row)
    r = receipt.mapping
    original = RecordRW0ActiveCancelDecisionCommandV1(r["command_safe_bytes"])
    decision_plan = build_cancel_decision_plan(original, r["recorded_at"])
    if decision_plan.receipt != receipt:
        raise ValueError("contradictory cancel decision receipt")
    saved = original.to_mapping()
    committed = decision_plan.committed
    if (terminal["decision_ref"] != committed.decision_ref
        or terminal["decision_digest"] != committed.decision_digest
        or terminal["decision_receipt_ref"] != committed.receipt_ref
        or terminal["decision_receipt_digest"] != committed.receipt_digest
        or terminal["decision_command_digest"] != original.command_digest
        or terminal["phase_basis_ref"] != saved["phase_basis_ref"]
        or terminal["phase_basis_digest"] != saved["phase_basis_digest"]
        or terminal["program_ref"] != saved["program"]["program_ref"]
        or terminal["target_effect_intent_ref"] != saved["target"]["effect_intent_ref"]):
        raise ValueError("contradictory original cancel witness")
    expected_decision = decision_plan.decision.identity_mapping()
    expected_decision["decision_digest"] = decision_plan.decision.decision_digest
    decision_columns = tuple(expected_decision)
    decision_rows = connection.execute(  # type: ignore[attr-defined]
        f"SELECT {', '.join(decision_columns)} FROM development_decisions "
        "WHERE decision_ref=? LIMIT 2", (r["decision_ref"],)
    ).fetchmany(2)
    if (type(decision_rows) is not list or len(decision_rows) != 1
        or type(decision_rows[0]) is not tuple
        or len(decision_rows[0]) != len(decision_columns)
        or any(type(actual) is not type(expected_decision[name])
               or actual != expected_decision[name]
               for name, actual in zip(decision_columns, decision_rows[0], strict=True))):
        raise ValueError("contradictory original cancel decision")
    found = connection.execute(  # type: ignore[attr-defined]
        f"SELECT {', '.join(DECISION_COLUMNS[DB])} FROM {DB} "
        "WHERE decision_ref=? ORDER BY role LIMIT 15", (r["decision_ref"],)
    ).fetchmany(15)
    if (type(found) is not list or len(found) != len(required_roles(original.to_mapping()["target"]["effect_class"]))
        or {row.mapping["role"]: row for row in (decision_row(DB, item) for item in found)}
            != {row.mapping["role"]: row for row in decision_plan.bindings}):
        raise ValueError("contradictory cancel decision bindings")


def verify_terminal_anchor_families_0010(connection: object) -> None:
    counts = {}
    for table in (NC, NO, NX, NR, CC, CO, CX, CR, "rw0_terminal_anchors"):
        row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()  # type: ignore[attr-defined]
        if type(row) is not tuple or len(row) != 1 or type(row[0]) is not int or row[0] < 0:
            raise ValueError("invalid terminal family count")
        counts[table] = row[0]
    if (len({counts[t] for t in (NC, NO, NX, NR)}) != 1
        or len({counts[t] for t in (CC, CO, CX, CR)}) != 1
        or counts["rw0_terminal_anchors"] != counts[NR] + counts[CR]):
        raise ValueError("incomplete mixed terminal family")
    seen: set[str] = set()
    for receipt_table, context_table, outcome_table, result_table, columns, checker, expected in (
        (NR, NC, NO, NX, NORMAL_COLUMNS, normal_row, expected_normal_anchor),
        (CR, CC, CO, CX, CANCEL_COLUMNS, cancel_row, expected_cancel_anchor),
    ):
        locator = connection.execute(f"SELECT receipt_ref FROM {receipt_table} ORDER BY receipt_ref")  # type: ignore[attr-defined]
        try:
            for page in iter(lambda: locator.fetchmany(257), []):
                if type(page) is not list or len(page) > 257:
                    raise ValueError("invalid terminal family page")
                for item in page:
                    if type(item) is not tuple or len(item) != 1 or type(item[0]) is not str:
                        raise ValueError("invalid terminal family locator")
                    receipt = _one(connection, receipt_table, columns[receipt_table], "receipt_ref", item[0], checker)
                    r = receipt.mapping  # type: ignore[attr-defined]
                    context = _one(connection, context_table, columns[context_table], "context_ref", r["context_ref"], checker)
                    outcome = _one(connection, outcome_table, columns[outcome_table], "outcome_value_ref", r["outcome_value_ref"], checker)
                    result = _one(connection, result_table, columns[result_table], "result_ref", r["result_ref"], checker)
                    anchor = expected(context, outcome, result, receipt)
                    a = anchor.mapping
                    if a["phase_basis_ref"] in seen:
                        raise ValueError("duplicate terminal phase")
                    seen.add(a["phase_basis_ref"])
                    persisted = connection.execute(  # type: ignore[attr-defined]
                        f"SELECT {', '.join(ANCHOR_COLUMNS)} FROM rw0_terminal_anchors WHERE phase_basis_ref=? LIMIT 2",
                        (a["phase_basis_ref"],),
                    ).fetchmany(2)
                    if type(persisted) is not list or len(persisted) != 1 or checked_anchor_row(persisted[0]) != anchor:
                        raise ValueError("contradictory terminal anchor")
                    if receipt_table == CR:
                        _checked_cancel_terminal_witness(
                            connection, context, (context, outcome, result, receipt), anchor)
        finally:
            locator.close()
    if len(seen) != counts["rw0_terminal_anchors"]:
        raise ValueError("orphan terminal anchor")
