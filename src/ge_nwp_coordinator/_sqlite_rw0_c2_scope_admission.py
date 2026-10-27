"""Private RW0-C2 P0 SQLite family, used only under the fenced controller."""
from __future__ import annotations

import sqlite3
from typing import cast

from ge_nwp_coordinator._rw0_c2_scope_admission_contracts import (
    ArtificialAdmissionSourceV1, ScopeAdmissionCommandV1,
    ScopeAdmissionCommittedV1, ScopeAdmissionConflictV1, ScopeAdmissionRecoveryV1,
    _ACT, _BASIS, _FACT, _RECEIPT, _TABLE_FIELDS,
    _PROFILE, _build_family, _digest_value, _exact, _ref, _self_digest, _time,
)
from ge_nwp_coordinator.sqlite_transition_select_support import (
    _MutationReadCapability, _execute_select_fetch_bounded,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode

_ACT_TABLE = "rw0_c2_verified_admission_acts"
_FACT_TABLE = "rw0_c2_scope_admission_facts"
_BASIS_TABLE = "rw0_c2_scope_admission_recording_bases"
_RECEIPT_TABLE = "rw0_c2_scope_admission_recording_receipts"
_TABLES = (_ACT_TABLE, _FACT_TABLE, _BASIS_TABLE, _RECEIPT_TABLE)


def _integrity() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE)


def _failed() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(SQLiteMutationStoreErrorCode.MUTATION_FAILED)


def _one(capability: object, table: str, where: str, params: tuple[object, ...]) -> dict[str, object] | None:
    if table not in _TABLES:
        raise _integrity() from None
    cols = _TABLE_FIELDS[table]
    sql = f"SELECT {', '.join(cols)} FROM {table} WHERE {where} LIMIT 2"
    try:
        rows = _execute_select_fetch_bounded(
            capability=cast(_MutationReadCapability, capability),
            sql=sql, parameters=params, limit=2,
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _failed() from None
    if len(rows) > 1:
        raise _integrity() from None
    if not rows:
        return None
    row = rows[0]
    if type(row) is not tuple or len(row) != len(cols):
        raise _integrity() from None
    return dict(zip(cols, row, strict=True))


def _observed(capability: object, command: ScopeAdmissionCommandV1) -> tuple[dict[str, object] | None, ...]:
    value = command.to_mapping()
    act = cast(dict[str, object], value["verified_admission_act"])
    fact = cast(dict[str, object], value["expected_admission_fact"])
    receipt = _one(capability, _RECEIPT_TABLE, "operation_ref = ?", (value["operation_ref"],))
    basis = _one(capability, _BASIS_TABLE, "operation_ref = ?", (value["operation_ref"],))
    fact_row = _one(capability, _FACT_TABLE, "admission_fact_ref = ?", (fact["admission_fact_ref"],))
    act_row = _one(capability, _ACT_TABLE, "act_ref = ?", (act["act_ref"],))
    return act_row, fact_row, basis, receipt


def _result_from_basis(command: ScopeAdmissionCommandV1, basis: dict[str, object]) -> dict[str, object]:
    value = command.to_mapping()
    fact = cast(dict[str, object], value["expected_admission_fact"])
    result: dict[str, object] = {
        "schema_id": "governed-execution.nwp-rw0-c2-scope-admission-recording-result.v1",
        "operation_ref": value["operation_ref"], "command_digest": value["command_digest"],
        "admission_fact_ref": fact["admission_fact_ref"], "admission_fact_digest": fact["admission_fact_digest"],
        "basis_digest": basis["basis_digest"], "recorded_at": basis["recorded_at"],
        "result_class": "scope_admission_recorded",
    }
    result["result_digest"] = _self_digest(result, "result_digest")
    return result


def _verify_exact(command: ScopeAdmissionCommandV1, rows: tuple[dict[str, object] | None, ...]) -> ScopeAdmissionCommittedV1:
    act, fact, basis, receipt = rows
    if any(type(row) is not dict for row in rows):
        raise _integrity() from None
    assert act is not None and fact is not None and basis is not None and receipt is not None
    value = command.to_mapping()
    expected_act = value["verified_admission_act"]
    expected_fact = value["expected_admission_fact"]
    try:
        _exact(act, _ACT)
        _exact(fact, _FACT, int_fields=("one_shot_ceiling",))
        _exact(basis, _BASIS)
        _exact(receipt, _RECEIPT)
        if (act != expected_act or fact != expected_fact
            or basis["operation_ref"] != value["operation_ref"]
            or basis["command_digest"] != value["command_digest"]
            or basis["act_projection_digest"] != act["projection_digest"]
            or basis["admission_fact_ref"] != fact["admission_fact_ref"]
            or basis["admission_fact_digest"] != fact["admission_fact_digest"]
            or any(basis[name] != value[name] for name in ("enrollment_ref", "incarnation_ref", "authority_process_ref", "storage_custody_ref"))
            or any(not _ref(basis[name]) for name in ("enrollment_evidence_ref", "recording_permission_evidence_ref", "custody_evidence_ref"))
            or any(not _digest_value(basis[name]) for name in ("enrollment_evidence_digest", "recording_permission_evidence_digest", "custody_evidence_digest"))
            or not _time(basis["recorded_at"])
            or _self_digest(basis, "basis_digest") != basis["basis_digest"]):
            raise ValueError("invalid basis")
        result = _result_from_basis(command, basis)
        expected_receipt = {
            "schema_id": "governed-execution.nwp-rw0-c2-scope-admission-recording-receipt.v1",
            "operation_ref": value["operation_ref"], "command_digest": value["command_digest"],
            "act_ref": act["act_ref"], "act_digest": act["act_digest"],
            "act_projection_digest": act["projection_digest"],
            "admission_fact_ref": fact["admission_fact_ref"], "admission_fact_digest": fact["admission_fact_digest"],
            "basis_digest": basis["basis_digest"], "result_digest": result["result_digest"],
            "recorded_at": basis["recorded_at"], "outcome": "committed",
        }
        expected_receipt["receipt_digest"] = _self_digest(expected_receipt, "receipt_digest")
        if receipt != expected_receipt:
            raise ValueError("invalid receipt")
    except (ValueError, KeyError, TypeError):
        raise _integrity() from None
    return ScopeAdmissionCommittedV1(result, receipt)


def _route_rows(capability: object, command: ScopeAdmissionCommandV1) -> tuple[dict[str, object] | None, ...]:
    value = command.to_mapping()
    act = cast(dict[str, object], value["verified_admission_act"])
    fact = cast(dict[str, object], value["expected_admission_fact"])
    return (
        _one(capability, _ACT_TABLE, "lineage_ref = ?", (fact["lineage_ref"],)),
        _one(capability, _ACT_TABLE, "scope_ref = ?", (fact["scope_ref"],)),
        _one(capability, _FACT_TABLE, "act_ref = ?", (act["act_ref"],)),
        _one(capability, _FACT_TABLE, "lineage_ref = ?", (fact["lineage_ref"],)),
        _one(capability, _FACT_TABLE, "scope_ref = ?", (fact["scope_ref"],)),
        _one(capability, _BASIS_TABLE, "admission_fact_ref = ?", (fact["admission_fact_ref"],)),
        _one(capability, _RECEIPT_TABLE, "act_ref = ?", (act["act_ref"],)),
        _one(capability, _RECEIPT_TABLE, "admission_fact_ref = ?", (fact["admission_fact_ref"],)),
    )


def _complete_winner_for_act(capability: object, act_ref: object) -> bool:
    if not _ref(act_ref):
        return False
    try:
        act = _one(capability, _ACT_TABLE, "act_ref = ?", (act_ref,))
        fact = _one(capability, _FACT_TABLE, "act_ref = ?", (act_ref,))
        receipt = _one(capability, _RECEIPT_TABLE, "act_ref = ?", (act_ref,))
        if act is None or fact is None or receipt is None:
            return False
        basis = _one(capability, _BASIS_TABLE, "operation_ref = ?", (receipt["operation_ref"],))
        if basis is None:
            return False
        value: dict[str, object] = {
            "schema_id": "governed-execution.nwp-rw0-c2-record-scope-admission-command.v1",
            "operation_ref": receipt["operation_ref"],
            "verified_admission_act": act,
            "expected_admission_fact": fact,
            **{name: basis[name] for name in ("enrollment_ref", "incarnation_ref", "authority_process_ref", "storage_custody_ref")},
            "proof_profile_id": _PROFILE,
        }
        value["command_digest"] = _self_digest(value, "command_digest")
        candidate = ScopeAdmissionCommandV1.from_mapping(value)
        _verify_exact(candidate, (act, fact, basis, receipt))
        return True
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return False


def read_after_fencing(capability: object, command: ScopeAdmissionCommandV1,
                       source: ArtificialAdmissionSourceV1, *, disclosure: bool = True) -> ScopeAdmissionCommittedV1 | None:
    if disclosure:
        source.checked_for(command, disclosure=True)
    else:
        # The protected receipt probe admits either current recording or
        # disclosure permission. Historical replay then requires disclosure;
        # a fresh write still requires current recording permission.
        try:
            source.checked_for(command, disclosure=False)
        except ValueError:
            source.checked_for(command, disclosure=True)
    rows = _observed(capability, command)
    receipt = rows[3]
    if receipt is None:
        if not disclosure:
            source.checked_for(command, disclosure=False)
        if disclosure and (any(row is not None for row in rows) or any(row is not None for row in _route_rows(capability, command))):
            raise _integrity() from None
        return None
    source.checked_for(command, disclosure=True)
    if receipt["command_digest"] != command.to_mapping()["command_digest"]:
        raise ValueError("scope_admission_operation_identity_conflict")
    committed = _verify_exact(command, rows)
    route_rows = _route_rows(capability, command)
    if any(row is not None and row not in rows for row in route_rows):
        raise _integrity() from None
    return committed


def classify_fresh_collision(capability: object, command: ScopeAdmissionCommandV1) -> ScopeAdmissionConflictV1 | None:
    rows = _observed(capability, command)
    route = _route_rows(capability, command)
    if rows[2] is not None or rows[3] is not None:
        return ScopeAdmissionConflictV1("scope_admission_provisioning.family_unverifiable")
    occupied = tuple(row for row in (*rows[:2], *route) if row is not None)
    for row in occupied:
        act_ref = row.get("act_ref")
        if act_ref is None and "admission_fact_ref" in row:
            related = _one(capability, _FACT_TABLE, "admission_fact_ref = ?", (row["admission_fact_ref"],))
            act_ref = related.get("act_ref") if related is not None else None
        if not _complete_winner_for_act(capability, act_ref):
            return ScopeAdmissionConflictV1("scope_admission_provisioning.family_unverifiable")
    if any(row is not None for row in route[6:]):
        return ScopeAdmissionConflictV1("scope_admission_provisioning.already_recorded_under_other_operation")
    if occupied:
        return ScopeAdmissionConflictV1("scope_admission_provisioning.admission_identity_conflict")
    return None


def write_fresh_after_fencing(capability: object, connection: sqlite3.Connection,
                              command: ScopeAdmissionCommandV1, source: ArtificialAdmissionSourceV1,
                              recorded_at: str) -> ScopeAdmissionCommittedV1 | ScopeAdmissionConflictV1:
    if type(connection) is not sqlite3.Connection:
        raise _failed() from None
    source.checked_for(command, disclosure=False)
    conflict = classify_fresh_collision(capability, command)
    if conflict is not None:
        return conflict
    act, fact, basis, result, receipt = _build_family(command, source, recorded_at)
    for table, row in zip(_TABLES, (act, fact, basis, receipt), strict=True):
        columns = _TABLE_FIELDS[table]
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})"
        cursor: sqlite3.Cursor | None = None
        try:
            cursor = connection.execute(sql, tuple(row[name] for name in columns))
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
    return ScopeAdmissionCommittedV1(result, receipt)


def recover_after_fencing(capability: object, command: ScopeAdmissionCommandV1,
                          source: ArtificialAdmissionSourceV1) -> ScopeAdmissionRecoveryV1:
    try:
        checked = read_after_fencing(capability, command, source)
        if checked is not None:
            return ScopeAdmissionRecoveryV1("committed_exact", checked)
        if not source.old_execution_excluded:
            return ScopeAdmissionRecoveryV1("unresolved")
        return ScopeAdmissionRecoveryV1("definitely_not_committed")
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        return ScopeAdmissionRecoveryV1("unresolved")
