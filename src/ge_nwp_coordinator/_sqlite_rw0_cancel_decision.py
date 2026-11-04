"""Fenced private durable active-cancel decision; no external effects."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast
from . import _development_decision_row_values as generic
from ._rw0_cancel_decision_contracts import (
    RecordRW0ActiveCancelDecisionCommandV1, CancelDecisionCommittedV1,
    CancelDecisionConflictV1, CancelDecisionRecoveryV1,
)
from ._rw0_cancel_decision_plan import build_cancel_decision_plan, CancelDecisionPlan
from ._rw0_cancel_decision_rows import BINDING, RECEIPT, COLUMNS, PRIMARY, CancelDecisionRow, checked_row, required_roles
from ._sqlite_rw0_c2_progression import _one as _generic_one
from ._sqlite_rw0_cancel_currentness import check_coordinator_facts, checked_immutable_cancel_lineage
from ._sqlite_rw0_terminal_anchor import read_terminal_anchor
from ._sqlite_rw0_terminal_outcome import _anchor_family_exact
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from .sqlite_transition_select_support import _MutationReadCapability, _execute_select_fetch_bounded

__all__: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FreshCancelDecision:
    committed: CancelDecisionCommittedV1


def unresolved_recovery() -> CancelDecisionRecoveryV1:
    return CancelDecisionRecoveryV1("unresolved")


def _integrity() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def _failed() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)


def _one(capability: object, table: str, key: str, value: object) -> CancelDecisionRow | None:
    if table not in (BINDING, RECEIPT) or key not in COLUMNS[table]:
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


def _bindings(capability: object, decision_ref: str, target_class: str) -> tuple[CancelDecisionRow, ...]:
    columns = COLUMNS[BINDING]
    try:
        rows = _execute_select_fetch_bounded(
            capability=cast(_MutationReadCapability, capability),
            sql=f"SELECT {', '.join(columns)} FROM {BINDING} WHERE decision_ref=? ORDER BY role LIMIT 15",
            parameters=(decision_ref,), limit=15)
        if len(rows) != len(required_roles(target_class)):
            raise _integrity()
        typed = tuple(checked_row(BINDING, row) for row in rows)
        if {row.mapping["role"] for row in typed} != set(required_roles(target_class)):
            raise _integrity()
        return typed
    except SQLiteMutationStoreError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None


def _family_exact(capability: object, receipt: CancelDecisionRow) -> CancelDecisionPlan:
    if type(receipt) is not CancelDecisionRow or receipt.table != RECEIPT:
        raise _integrity() from None
    r = receipt.mapping
    try:
        command = RecordRW0ActiveCancelDecisionCommandV1(cast(bytes, r["command_safe_bytes"]))
        plan = build_cancel_decision_plan(command, cast(str, r["recorded_at"]))
        decision = _generic_one(capability, "development_decisions", "decision_ref = ?", (r["decision_ref"],))
        if (plan.receipt != receipt or type(decision) is not generic.DevelopmentDecisionRowValue
            or decision.identity_mapping() != plan.decision.identity_mapping()
            or decision.decision_digest != plan.decision.decision_digest):
            raise _integrity()
        persisted = _bindings(capability, cast(str, r["decision_ref"]), cast(str, command.to_mapping()["target"]["effect_class"]))
        if {row.mapping["role"]: row for row in persisted} != {row.mapping["role"]: row for row in plan.bindings}:
            raise _integrity()
        if checked_immutable_cancel_lineage(capability, command) is None:
            raise _integrity()
        return plan
    except SQLiteMutationStoreError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None


def _binding_rows(capability: object, key: str, value: object) -> tuple[CancelDecisionRow, ...]:
    if key not in ("phase_basis_ref", "decision_ref", "mutation_ref"):
        raise _integrity() from None
    try:
        rows = _execute_select_fetch_bounded(
            capability=cast(_MutationReadCapability, capability),
            sql=f"SELECT {', '.join(COLUMNS[BINDING])} FROM {BINDING} WHERE {key}=? ORDER BY role LIMIT 15",
            parameters=(value,), limit=15)
        if len(rows) > 5:
            raise _integrity()
        return tuple(checked_row(BINDING, row) for row in rows)
    except SQLiteMutationStoreError:
        raise
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        raise _integrity() from None


def _validated_alias_receipts(capability: object,
                              command: RecordRW0ActiveCancelDecisionCommandV1) -> set[str]:
    """All bounded receipt, binding, phase, and generic aliases must be complete."""
    m = command.to_mapping()
    receipts: dict[str, CancelDecisionRow] = {}
    for table, key, value in (
        (RECEIPT, "receipt_ref", m["receipt_ref"]),
        (RECEIPT, "mutation_ref", m["mutation_ref"]),
        (RECEIPT, "decision_ref", m["decision_ref"]),
        (RECEIPT, "phase_basis_ref", m["phase_basis_ref"]),
    ):
        row = _one(capability, table, key, value)
        if row is not None:
            receipts[cast(str, row.mapping["receipt_ref"])] = row
    plan = build_cancel_decision_plan(command, "2020-01-01T00:00:00Z")
    bindings: dict[str, CancelDecisionRow] = {}
    for row in plan.bindings:
        found = _one(capability, BINDING, "binding_ref", row.mapping["binding_ref"])
        if found is not None:
            bindings[cast(str, found.mapping["binding_ref"])] = found
    for key in ("phase_basis_ref", "decision_ref", "mutation_ref"):
        for found in _binding_rows(capability, key, m[key]):
            bindings[cast(str, found.mapping["binding_ref"])] = found
    for binding in bindings.values():
        receipt = _one(capability, RECEIPT, "decision_ref", binding.mapping["decision_ref"])
        if receipt is None:
            raise _integrity() from None
        receipts[cast(str, receipt.mapping["receipt_ref"])] = receipt
    for key in ("decision_ref", "mutation_ref"):
        generic = _generic_one(capability, "development_decisions", f"{key} = ?", (m[key],))
        if generic is not None:
            receipt = _one(capability, RECEIPT, "decision_ref", generic.decision_ref)
            if receipt is None:
                raise _integrity() from None
            receipts[cast(str, receipt.mapping["receipt_ref"])] = receipt
    for receipt in receipts.values():
        _family_exact(capability, receipt)
    return set(receipts)


def read_after_fencing(capability: object,
                       command: RecordRW0ActiveCancelDecisionCommandV1) -> CancelDecisionCommittedV1 | CancelDecisionConflictV1 | None:
    m = command.to_mapping()
    receipt = _one(capability, RECEIPT, "mutation_ref", m["mutation_ref"])
    anchor = read_terminal_anchor(capability, "phase_basis_ref", m["phase_basis_ref"])
    from ._sqlite_rw0_cancel_pre_effect_terminal import check_phase_route_rows
    check_phase_route_rows(capability, cast(str, m["phase_basis_ref"]), anchor)
    if anchor is not None:
        _anchor_family_exact(capability, anchor)
    aliases = _validated_alias_receipts(capability, command)
    if receipt is not None:
        if aliases != {receipt.mapping["receipt_ref"]}:
            raise _integrity() from None
        plan = _family_exact(capability, receipt)
        if receipt.mapping["command_digest"] != command.command_digest or receipt.mapping["command_safe_bytes"] != command.safe_bytes:
            return CancelDecisionConflictV1("command_reused")
        return plan.committed
    phase_receipt = _one(capability, RECEIPT, "phase_basis_ref", m["phase_basis_ref"])
    if phase_receipt is not None:
        if aliases != {phase_receipt.mapping["receipt_ref"]}:
            raise _integrity() from None
        return CancelDecisionConflictV1("phase_already_decided")
    if anchor is not None:
        if aliases:
            raise _integrity() from None
        return CancelDecisionConflictV1("terminal_phase_occupied")
    if aliases:
        raise _integrity() from None
    return None


def _insert_cancel_sqlite_row(
    connection: object, table: str, columns: tuple[str, ...],
    values: tuple[object, ...], *, sqlite_api: Any,
) -> None:
    """Execute one closed cancel-family insert inside its private SQLite owner."""
    allowed = {
        "development_decisions", "rw0_cancel_decision_evidence_bindings",
        "rw0_cancel_decision_receipts", "rw0_cancel_pre_effect_contexts",
        "rw0_cancel_pre_effect_outcomes", "rw0_cancel_pre_effect_results",
        "rw0_cancel_pre_effect_receipts",
    }
    if (type(connection) is not sqlite_api.Connection or table not in allowed
        or type(columns) is not tuple or type(values) is not tuple
        or not columns or len(columns) != len(values)):
        raise _failed()
    cursor: Any = None
    failure: SQLiteMutationStoreError | None = None
    try:
        cursor = connection.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) "
            f"VALUES ({', '.join('?' for _ in columns)})", values)
        if cursor.rowcount != 1:
            failure = _integrity()
    except sqlite_api.IntegrityError:
        failure = _integrity()
    except sqlite_api.Error:
        failure = _failed()
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        failure = _failed()
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except sqlite_api.Error:
                failure = failure or _failed()
    if failure is not None:
        raise failure from None


def _insert(connection: object, table: str, values: tuple[object, ...]) -> None:
    columns = generic._DEVELOPMENT_DECISION_COLUMNS if table == "development_decisions" else COLUMNS[table]
    from .sqlite_transition_transaction import _insert_cancel_sqlite_row
    _insert_cancel_sqlite_row(connection, table, columns, values)


def write_after_fencing(capability: object, connection: object,
                        command: RecordRW0ActiveCancelDecisionCommandV1,
                        timestamp: str) -> FreshCancelDecision | CancelDecisionCommittedV1 | CancelDecisionConflictV1:
    existing = read_after_fencing(capability, command)
    if existing is not None:
        return existing
    current = check_coordinator_facts(capability, command)
    if current.classification == "integrity_failure":
        raise _integrity() from None
    if current.classification != "locally_current_source_unverified":
        return CancelDecisionConflictV1("basis_changed")
    plan = build_cancel_decision_plan(command, timestamp)
    d = plan.decision.identity_mapping()
    d["decision_digest"] = plan.decision.decision_digest
    _insert(connection, "development_decisions", tuple(d[k] for k in generic._DEVELOPMENT_DECISION_COLUMNS))
    for binding in plan.bindings:
        _insert(connection, BINDING, binding.values)
    _insert(connection, RECEIPT, plan.receipt.values)
    if _family_exact(capability, plan.receipt).committed != plan.committed:
        raise _integrity() from None
    return FreshCancelDecision(plan.committed)


def recover_after_fencing(capability: object,
                          command: RecordRW0ActiveCancelDecisionCommandV1) -> CancelDecisionRecoveryV1:
    try:
        exact = read_after_fencing(capability, command)
        if type(exact) is CancelDecisionCommittedV1:
            return CancelDecisionRecoveryV1("committed_exact", exact)
        if exact is None or type(exact) is CancelDecisionConflictV1:
            return CancelDecisionRecoveryV1("definitely_not_committed")
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        pass
    return CancelDecisionRecoveryV1("unresolved")
