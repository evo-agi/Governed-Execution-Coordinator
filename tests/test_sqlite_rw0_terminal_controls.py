"""Fenced terminal rejection, rollback and uncertainty controls on real owners."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import sqlite3

import pytest

from ge_nwp_coordinator import _sqlite_rw0_terminal_outcome as terminal
from ge_nwp_coordinator._rw0_terminal_outcome_contracts import (
    RecordRW0TerminalOutcomeCommandV1, TerminalCommittedV1, TerminalConflictV1,
    _time,
)
from ge_nwp_coordinator._rw0_terminal_outcome_rows import checked_row, seal_row
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_sqlite_rw0_terminal_connected import (
    _advance_program_head, _terminal_selector, prepared_normal_case,
)


def _counts(location):
    with sqlite3.connect(location.database_path) as db:
        return tuple(db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                     for table in terminal.TABLES)


def _test_reseal_terminal_row(table, mapping):
    """Test-owned canonical preimage; no production sealer in negative setup."""
    own = {terminal.CONTEXT: "context_digest", terminal.RESULT: "result_digest",
           terminal.RECEIPT: "receipt_digest"}[table]
    preimage = {key: (value.hex() if table == terminal.CONTEXT
                      and type(value) is bytes else value)
                for key, value in mapping.items() if key != own}
    payload = json.dumps(preimage, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256((mapping["schema_id"] + ".identity").encode("utf-8")
                          + b"\0" + payload).hexdigest()


def _variation(command, *, mutation_ref=None, heads=None, stop=None,
               p1_command=None, section41_command=None, c1_rank15=None,
               expected_branch="candidate_acceptance", expected_outcome="accept"):
    safe = command.to_mapping()
    return RecordRW0TerminalOutcomeCommandV1.prepare(
        mutation_ref=mutation_ref or safe["mutation_ref"],
        p1_command=p1_command or command.p1_command,
        section41_command=section41_command or command.section41_command,
        c1_rank15=c1_rank15 or command.c1_rank15,
        heads=tuple(heads if heads is not None else safe["heads"]),
        stop=stop if stop is not None else safe["stop"],
        prior_decision_digest=safe["reached_owners"][15]["digest"],
        prior_guarded_result_digest=safe["reached_owners"][16]["digest"],
        prior_receipt_graph_digest=safe["reached_owners"][17]["digest"],
        expected_branch=expected_branch,
        expected_outcome=expected_outcome)


def test_cancel_shaped_commands_and_unsupported_profile_are_prewrite_rejected(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        for branch in ("active_cancel_reconciled", "active_cancel_unresolved",
                       "pre_effect_cancel_basis_unusable"):
            with pytest.raises(ValueError):
                _variation(command, expected_branch=branch)
            assert _counts(location) == (0, 0, 0, 0)
        safe = command.to_mapping()
        safe["profile"] = "live.v1"
        from ge_nwp_coordinator._rw0_terminal_outcome_contracts import _canonical
        with pytest.raises(ValueError):
            RecordRW0TerminalOutcomeCommandV1(
                _canonical(safe), command.p1_command,
                command.section41_command, command.c1_rank15)
        assert _counts(location) == (0, 0, 0, 0)


def test_five_head_expectations_stop_expectation_and_actual_program_drift(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        original = command.to_mapping()
        for index in range(5):
            heads = [dict(item) for item in original["heads"]]
            heads[index]["revision"] += 1
            changed = _variation(command, heads=heads)
            with acquire_sqlite_writer_session(location) as writer:
                assert writer._record_terminal_outcome(changed, source) == TerminalConflictV1("stale_currentness")
            assert _counts(location) == (0, 0, 0, 0)
        stop = dict(original["stop"])
        stop["version"] += 1
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._record_terminal_outcome(
                _variation(command, stop=stop), source) == TerminalConflictV1("stale_currentness")
        with sqlite3.connect(location.database_path) as db:
            _advance_program_head(db)
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._record_terminal_outcome(command, source) == TerminalConflictV1("stale_currentness")
        assert _counts(location) == (0, 0, 0, 0)


def test_changed_matched_active_stop_records_fact_without_new_effect(monkeypatch):
    from ge_nwp_coordinator.global_stop import GlobalStopOperatorDecision
    from ge_nwp_coordinator.persistence_contracts import (
        global_stop_operator_decision_canonical_json,
        global_stop_operator_decision_canonical_digest,
    )
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        with sqlite3.connect(location.database_path) as db:
            effects_before = db.execute("SELECT count(*) FROM development_effect_intents").fetchone()[0]
            decision = GlobalStopOperatorDecision(
                decision_ref="terminal-test-stop-decision", authorized=True, reason="accepted")
            db.execute(
                "INSERT INTO global_stop_operator_decision_receipts "
                "(decision_ref, authorized, reason, schema_id, canonical_json, canonical_digest, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (decision.decision_ref, 1, decision.reason, decision.schema_id,
                 global_stop_operator_decision_canonical_json(decision),
                 global_stop_operator_decision_canonical_digest(decision),
                 "2098-01-01T00:00:00Z"))
            db.execute(
                "UPDATE global_stop_current SET version=version+1, active=1, "
                "stop_id='terminal-test-stop', reason_class='operator_stop', "
                "issuer_ref='operator-policy', issued_at='2098-01-01T00:00:00Z', "
                "operator_decision_ref=?, updated_at='2098-01-01T00:00:00Z'",
                (decision.decision_ref,))
            changed = _terminal_selector(
                db, command.p1_command, command.section41_command, command.c1_rank15, p1)
        with acquire_sqlite_writer_session(location) as writer:
            committed = writer._record_terminal_outcome(changed, source)
            assert committed.outcome == "accept"
        with sqlite3.connect(location.database_path) as db:
            assert db.execute("SELECT count(*) FROM development_effect_intents").fetchone()[0] == effects_before
            assert db.execute("SELECT count(*) FROM rw0_c2_bootstrap_acceptance_facts").fetchone()[0] == 1
            assert _counts(location) == (1, 1, 1, 1)


def test_insert_readback_select_and_process_control_faults_rollback(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        original_insert = terminal._insert
        for fault_ordinal in range(1, 5):
            seen = []
            def fault(connection, row):
                seen.append(row.table)
                if len(seen) == fault_ordinal:
                    if row.table == terminal.RECEIPT:
                        assert tuple(connection.execute(
                            f"SELECT count(*) FROM {table}").fetchone()[0]
                            for table in terminal.TABLES) == (1, 1, 1, 0)
                    raise terminal._failed()
                return original_insert(connection, row)
            with monkeypatch.context() as patch:
                patch.setattr(terminal, "_insert", fault)
                with acquire_sqlite_writer_session(location) as writer:
                    with pytest.raises(SQLiteMutationStoreError) as error:
                        writer._record_terminal_outcome(command, source)
                    assert error.value.error_class == "mutation_failed"
            assert _counts(location) == (0, 0, 0, 0)
        original_exact = terminal._plan_exact
        def bad_readback(*args, **kwargs):
            raise terminal._integrity()
        with monkeypatch.context() as patch:
            patch.setattr(terminal, "_plan_exact", bad_readback)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as error:
                    writer._record_terminal_outcome(command, source)
                assert error.value.error_class == "database_integrity_failure"
        assert _counts(location) == (0, 0, 0, 0)
        with monkeypatch.context() as patch:
            patch.setattr(terminal, "_one", lambda *args: (_ for _ in ()).throw(terminal._integrity()))
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as error:
                    writer._record_terminal_outcome(command, source)
                assert error.value.error_class == "database_integrity_failure"
        assert _counts(location) == (0, 0, 0, 0)
        for control in (KeyboardInterrupt, SystemExit, GeneratorExit):
            with monkeypatch.context() as patch:
                patch.setattr(terminal, "_insert", lambda *args: (_ for _ in ()).throw(control()))
                with acquire_sqlite_writer_session(location) as writer:
                    with pytest.raises(control):
                        writer._record_terminal_outcome(command, source)
            assert _counts(location) == (0, 0, 0, 0)
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._record_terminal_outcome(command, source).outcome == "accept"


def test_missing_existing_acceptance_fact_is_not_synthesized(monkeypatch):
    from ge_nwp_coordinator import _rw0_c2_progression_rows as p1_rows
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        original = terminal._p1_one
        def missing(capability, table, where, parameters):
            if table == terminal._ACCEPTANCE:
                return None
            return original(capability, table, where, parameters)
        with monkeypatch.context() as patch:
            patch.setattr(terminal, "_p1_one", missing)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as error:
                    writer._record_terminal_outcome(command, source)
                assert error.value.error_class == "database_integrity_failure"
        assert _counts(location) == (0, 0, 0, 0)
        for field, replacement in (
            ("acceptance_fact_ref", "foreign-acceptance-fact"),
            ("lineage_ref", "foreign-lineage"),
            ("acceptance_fact_digest", "f" * 64),
        ):
            def substituted(capability, table, where, parameters):
                row = original(capability, table, where, parameters)
                if table != terminal._ACCEPTANCE:
                    return row
                assert type(row) is terminal._P1Row
                mapping = row.mapping
                mapping[field] = replacement
                return p1_rows._P1Row(
                    table, tuple(mapping[name] for name in p1_rows._TABLE_FIELDS[table]))
            with monkeypatch.context() as patch:
                patch.setattr(terminal, "_p1_one", substituted)
                with acquire_sqlite_writer_session(location) as writer:
                    with pytest.raises(SQLiteMutationStoreError) as error:
                        writer._record_terminal_outcome(command, source)
                    assert error.value.error_class == "database_integrity_failure", field
            assert _counts(location) == (0, 0, 0, 0), field


def test_foreign_p0_c1_section41_and_v22_bindings_fail_before_terminal_write(monkeypatch):
    from types import SimpleNamespace
    from ge_nwp_coordinator import _sqlite_rw0_c2_progression as p1_owner
    from ge_nwp_coordinator import _rw0_d2_post_execution_continuation as v22_owner
    from ge_nwp_coordinator._rw0_c2_scope_admission_contracts import ScopeAdmissionCommittedV1
    from test_sqlite_rw0_c2_scope_admission import _command as p0_command
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        foreign_command, foreign_source = p0_command("B")
        with acquire_sqlite_writer_session(location) as writer:
            assert type(writer._record_scope_admission(
                foreign_command, foreign_source)) is ScopeAdmissionCommittedV1
        original_p0 = p1_owner._p0_one
        def foreign_p0(capability, table, where, parameters):
            if table == p1_owner._P0_ACT:
                return original_p0(capability, table, "act_ref = ?", ("act-B",))
            if table == p1_owner._P0_FACT:
                return original_p0(capability, table, "admission_fact_ref = ?", ("admission-B",))
            return original_p0(capability, table, where, parameters)
        with monkeypatch.context() as patch:
            patch.setattr(p1_owner, "_p0_one", foreign_p0)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as error:
                    writer._record_terminal_outcome(command, source)
                assert error.value.error_class == "database_integrity_failure"
        assert _counts(location) == (0, 0, 0, 0)
        changed_c1 = replace(command.c1_rank15,
                             membership_digest="f" * 64, result_digest="")
        changed_section41 = replace(command.section41_command,
                                    evidence_set_digest="f" * 64,
                                    command_digest="")
        for label, candidate in (
            ("c1_membership", _variation(command, c1_rank15=changed_c1)),
            ("section41_evidence_set", _variation(
                command, section41_command=changed_section41)),
        ):
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as error:
                    writer._record_terminal_outcome(candidate, source)
                assert error.value.error_class == "database_integrity_failure", label
            assert _counts(location) == (0, 0, 0, 0), label
        original_project = v22_owner._project
        def inconsistent_projection(post, c1):
            projection = original_project(post, c1)
            mapping = projection.to_mapping()
            mapping["proposal_digest"] = "f" * 64
            return SimpleNamespace(to_mapping=lambda: mapping)
        with monkeypatch.context() as patch:
            patch.setattr(v22_owner, "_project", inconsistent_projection)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as error:
                    writer._record_terminal_outcome(command, source)
                assert error.value.error_class == "database_integrity_failure"
        assert _counts(location) == (0, 0, 0, 0)


def test_unavailable_original_replan_operand_has_safe_failure_and_unresolved_recovery(monkeypatch):
    with prepared_normal_case(monkeypatch, "attempt_selecting_replan") as (location, command, source, p1):
        forged = object.__new__(RecordRW0TerminalOutcomeCommandV1)
        for name in ("safe_bytes", "section41_command", "c1_rank15"):
            object.__setattr__(forged, name, getattr(command, name))
        object.__setattr__(forged, "p1_command", None)
        with acquire_sqlite_writer_session(location) as writer:
            for method in (writer._record_terminal_outcome, writer._read_terminal_outcome):
                with pytest.raises(SQLiteMutationStoreError) as error:
                    method(forged, source)
                assert error.value.error_class == "database_integrity_failure"
            assert writer._recover_terminal_outcome(
                forged, source).classification == "unresolved"
        mismatched_p1 = replace(command.p1_command, expected_branch=None)
        safe = command.to_mapping()
        mismatched = RecordRW0TerminalOutcomeCommandV1.prepare(
            mutation_ref=safe["mutation_ref"], p1_command=mismatched_p1,
            section41_command=command.section41_command,
            c1_rank15=command.c1_rank15, heads=tuple(safe["heads"]),
            stop=safe["stop"],
            prior_decision_digest=safe["reached_owners"][15]["digest"],
            prior_guarded_result_digest=safe["reached_owners"][16]["digest"],
            prior_receipt_graph_digest=safe["reached_owners"][17]["digest"],
            expected_branch=safe["expected_branch"],
            expected_outcome=safe["expected_outcome"])
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as error:
                writer._record_terminal_outcome(mismatched, source)
            assert error.value.error_class == "database_integrity_failure"
            assert writer._recover_terminal_outcome(
                mismatched, source).classification == "unresolved"
        assert _counts(location) == (0, 0, 0, 0)


def test_recovery_original_absence_and_unverifiable_competing_winner(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._recover_terminal_outcome(
                command, source).classification == "definitely_not_committed"
            assert writer._recover_terminal_outcome(
                command, replace(source, old_execution_excluded=False)
            ).classification == "unresolved"
            assert writer._record_terminal_outcome(command, source).outcome == "accept"
        competitor = _variation(command, mutation_ref="terminal.competing.2")
        with monkeypatch.context() as patch:
            patch.setattr(terminal, "_historical_exact",
                          lambda *args: (_ for _ in ()).throw(terminal._integrity()))
            with acquire_sqlite_writer_session(location) as writer:
                assert writer._recover_terminal_outcome(
                    competitor, source).classification == "unresolved"
        assert _counts(location) == (1, 1, 1, 1)


def test_applied_commit_lost_return_recovers_exact(monkeypatch):
    from ge_nwp_coordinator import sqlite_transition_transaction as tx
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        original = tx._CoordinatorMutationTransactionController._commit_after_fresh_writes
        calls = []
        def lost_return(self, result, **kwargs):
            calls.append("commit")
            original(self, result, **kwargs)
            raise tx._commit_outcome_unknown()
        with monkeypatch.context() as patch:
            patch.setattr(tx._CoordinatorMutationTransactionController,
                          "_commit_after_fresh_writes", lost_return)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as error:
                    writer._record_terminal_outcome(command, source)
                assert error.value.error_class == "commit_outcome_unknown"
        assert calls == ["commit"]
        assert _counts(location) == (1, 1, 1, 1)
        with acquire_sqlite_writer_session(location) as writer:
            recovery = writer._recover_terminal_outcome(command, source)
            assert recovery.classification == "committed_exact"
            assert writer._read_terminal_outcome(command, source) == recovery.committed


def test_partial_phase_family_and_alias_probe_remain_unresolved(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        captured = []
        original_insert = terminal._insert
        def capture_then_fail(connection, row):
            captured.append(row)
            if row.table == terminal.RECEIPT:
                raise terminal._failed()
            original_insert(connection, row)
        with monkeypatch.context() as patch:
            patch.setattr(terminal, "_insert", capture_then_fail)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError):
                    writer._record_terminal_outcome(command, source)
        assert [row.table for row in captured] == list(terminal.TABLES)
        assert _counts(location) == (0, 0, 0, 0)
        original_one = terminal._one
        def alias(capability, table, column, value):
            if table == terminal.RESULT and column == "result_ref" and value == command.to_mapping()["result_ref"]:
                return captured[2]
            return original_one(capability, table, column, value)
        with monkeypatch.context() as patch:
            patch.setattr(terminal, "_one", alias)
            with acquire_sqlite_writer_session(location) as writer:
                assert writer._recover_terminal_outcome(command, source).classification == "unresolved"
        assert _counts(location) == (0, 0, 0, 0)
        context = captured[0]
        with sqlite3.connect(location.database_path) as db:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute(
                f"INSERT INTO {context.table} ({', '.join(terminal.COLUMNS[context.table])}) "
                f"VALUES ({', '.join('?' for _ in context.values)})", context.values)
        assert _counts(location) == (1, 0, 0, 0)
        competitor = _variation(command, mutation_ref="terminal.competing.partial")
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._recover_terminal_outcome(command, source).classification == "unresolved"
            assert writer._recover_terminal_outcome(competitor, source).classification == "unresolved"
        assert _counts(location) == (1, 0, 0, 0)
        with sqlite3.connect(location.database_path) as db:
            db.execute("PRAGMA foreign_keys=ON")
            registration = db.execute(
                "SELECT sql FROM sqlite_schema WHERE name='rw0_terminal_receipts_register_anchor'"
            ).fetchone()[0]
            db.execute("DROP TRIGGER rw0_terminal_receipts_register_anchor")
            for row in captured[1:]:
                values = list(row.values)
                if row.table == terminal.RECEIPT:
                    values[terminal.COLUMNS[row.table].index("receipt_digest")] = "f" * 64
                db.execute(
                    f"INSERT INTO {row.table} ({', '.join(terminal.COLUMNS[row.table])}) "
                    f"VALUES ({', '.join('?' for _ in values)})", values)
            db.execute(registration)
        assert _counts(location) == (1, 1, 1, 1)
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._recover_terminal_outcome(command, source).classification == "unresolved"
            assert writer._recover_terminal_outcome(competitor, source).classification == "unresolved"


def test_before_commit_and_post_commit_cleanup_faults(monkeypatch):
    from ge_nwp_coordinator import sqlite_transition_transaction as tx
    from ge_nwp_coordinator import sqlite_writer_session as writer_module
    with prepared_normal_case(monkeypatch) as (location, command, source, p1):
        calls = []
        def before_commit(self, result, **kwargs):
            calls.append("planned_commit")
            raise terminal._failed()
        with monkeypatch.context() as patch:
            patch.setattr(tx._CoordinatorMutationTransactionController,
                          "_commit_after_fresh_writes", before_commit)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as error:
                    writer._record_terminal_outcome(command, source)
                assert error.value.error_class == "mutation_failed"
        assert calls == ["planned_commit"]
        assert _counts(location) == (0, 0, 0, 0)
        def cleanup_fault(**kwargs):
            raise RuntimeError("simulated cleanup fault")
        with monkeypatch.context() as patch:
            patch.setattr(writer_module, "_complete_rw0_c1_writer_post_operation", cleanup_fault)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as error:
                    writer._record_terminal_outcome(command, source)
                assert error.value.error_class == "commit_outcome_unknown"
        assert _counts(location) == (1, 1, 1, 1)
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._recover_terminal_outcome(command, source).classification == "committed_exact"


def test_recorded_at_checked_rows_and_sealers_use_exact_time_owner(monkeypatch):
    valid = ("0001-01-01T00:00:00Z", "9999-12-31T23:59:59Z",
             "2000-02-29T12:00:00Z", "2024-02-29T12:00:00Z",
             "2026-12-31T23:59:59Z")
    invalid = ("2026-13-27T12:00:00Z", "2026-02-29T12:00:00Z",
               "2024-02-30T12:00:00Z", "1900-02-29T12:00:00Z",
               "2100-02-29T12:00:00Z", "2026-04-31T12:00:00Z",
               "0000-01-01T00:00:00Z", "2026-01-01T24:00:00Z",
               "2026-01-01T12:60:00Z", "2026-01-01T12:00:60Z",
               "2026-01-01T12:00:00.0Z", "2026-01-01T12:00:00Z\x00",
               None, 20260101120000, True, b"2026-01-01T12:00:00Z")

    class StringSubclass(str):
        def __eq__(self, other):
            raise AssertionError("timestamp subclass equality invoked")

    invalid += (StringSubclass("2026-01-01T12:00:00Z"),)
    with prepared_normal_case(monkeypatch) as (location, command, source, _):
        with acquire_sqlite_writer_session(location) as writer:
            committed = writer._record_terminal_outcome(command, source)
            assert type(committed) is TerminalCommittedV1
        with sqlite3.connect(location.database_path) as db:
            base = {table: dict(zip(terminal.COLUMNS[table], db.execute(
                f"SELECT * FROM {table}").fetchone(), strict=True))
                for table in (terminal.CONTEXT, terminal.RESULT, terminal.RECEIPT)}
        for table, original in base.items():
            digest_name = {terminal.CONTEXT: "context_digest",
                           terminal.RESULT: "result_digest",
                           terminal.RECEIPT: "receipt_digest"}[table]
            for timestamp in valid:
                assert _time(timestamp) == timestamp
                candidate = {**original, "recorded_at": timestamp}
                candidate[digest_name] = _test_reseal_terminal_row(table, candidate)
                ordered = tuple(candidate[name] for name in terminal.COLUMNS[table])
                assert checked_row(table, ordered).mapping == candidate
                assert seal_row(table, {**candidate, digest_name: ""}).mapping == candidate
                assert seal_row(table, dict(candidate)).mapping == candidate
                assert TerminalCommittedV1(
                    "mutation.1", "a" * 64, "receipt.1", "outcome.1",
                    "accept", "a" * 64, timestamp).recorded_at == timestamp
            for timestamp in invalid:
                candidate = {**original, "recorded_at": timestamp}
                if type(timestamp) is not bytes:
                    candidate[digest_name] = _test_reseal_terminal_row(table, candidate)
                ordered = tuple(candidate[name] for name in terminal.COLUMNS[table])
                with pytest.raises(ValueError, match="invalid terminal time"):
                    checked_row(table, ordered)
                with pytest.raises(ValueError, match="invalid terminal time"):
                    seal_row(table, {**candidate, digest_name: ""})
                with pytest.raises(ValueError, match="invalid terminal time"):
                    seal_row(table, dict(candidate))
                with pytest.raises(ValueError, match="invalid terminal time"):
                    TerminalCommittedV1(
                        "mutation.1", "a" * 64, "receipt.1", "outcome.1",
                        "accept", "a" * 64, timestamp)


def test_invalid_captured_recording_time_cannot_write_terminal_family(monkeypatch):
    from ge_nwp_coordinator import sqlite_transition_transaction as tx
    with prepared_normal_case(monkeypatch) as (location, command, source, _):
        # Fault injection reaches the controller's captured-time argument.
        # Disclosure is held positive only for this writer probe so the plan
        # and row grammar, rather than a prior posture check, decide rejection.
        with monkeypatch.context() as patch:
            patch.setattr(tx, "_capture_transaction_timestamp",
                          lambda: "2026-13-27T12:00:00Z")
            patch.setattr(terminal, "_disclosure", lambda *args, **kwargs: None)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as error:
                    writer._record_terminal_outcome(command, source)
                assert error.value.error_class == "database_integrity_failure"
        assert _counts(location) == (0, 0, 0, 0)
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._record_terminal_outcome(command, source).outcome == "accept"


def test_invalid_selected_terminal_row_refuses_read_replay_and_recovery(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, _):
        with acquire_sqlite_writer_session(location) as writer:
            valid = writer._record_terminal_outcome(command, source)
            assert writer._read_terminal_outcome(command, source) == valid
        competitor = _variation(command, mutation_ref="terminal.corrupt-competitor")
        original_select = terminal._execute_select_fetch_bounded
        for table in (terminal.RESULT, terminal.RECEIPT):
            digest_name = "result_digest" if table == terminal.RESULT else "receipt_digest"
            def corrupt_selected(*args, **kwargs):
                rows = original_select(*args, **kwargs)
                if rows and f"FROM {table} " in kwargs["sql"]:
                    columns = terminal.COLUMNS[table]
                    mapping = dict(zip(columns, rows[0], strict=True))
                    mapping["recorded_at"] = "2026-13-27T12:00:00Z"
                    mapping[digest_name] = _test_reseal_terminal_row(table, mapping)
                    return [tuple(mapping[name] for name in columns)]
                return rows
            with monkeypatch.context() as patch:
                patch.setattr(terminal, "_execute_select_fetch_bounded", corrupt_selected)
                with acquire_sqlite_writer_session(location) as writer:
                    with pytest.raises(SQLiteMutationStoreError) as error:
                        writer._read_terminal_outcome(command, source)
                    assert error.value.error_class == "database_integrity_failure"
                    with pytest.raises(SQLiteMutationStoreError) as error:
                        writer._record_terminal_outcome(command, source)
                    assert error.value.error_class == "database_integrity_failure"
                    assert writer._recover_terminal_outcome(
                        command, source).classification == "unresolved"
                    assert writer._recover_terminal_outcome(
                        competitor, source).classification == "unresolved"
            assert _counts(location) == (1, 1, 1, 1)
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._read_terminal_outcome(command, source) == valid
            assert writer._recover_terminal_outcome(
                competitor, source).classification == "definitely_not_committed"
