"""Connected guarded cancel decision replay, conflict, and recovery."""
from __future__ import annotations

import sqlite3

import pytest

from ge_nwp_coordinator import _sqlite_rw0_cancel_decision as decision_runtime
from ge_nwp_coordinator import sqlite_transition_transaction as transaction
from ge_nwp_coordinator._rw0_cancel_decision_contracts import (
    RecordRW0ActiveCancelDecisionCommandV1, CancelDecisionCommittedV1,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_sqlite_rw0_active_cancel_connected import prepared_cancel_case


def _variation(command: RecordRW0ActiveCancelDecisionCommandV1, *,
               mutation_ref: str | None = None, source_digest: str | None = None):
    m = command.to_mapping()
    source = m["source"]
    evidence = m["evidence"]
    if source_digest is not None:
        source["evidence_digest"] = source_digest
        evidence[3]["digest"] = source_digest
    return RecordRW0ActiveCancelDecisionCommandV1.prepare(
        mutation_ref=mutation_ref or m["mutation_ref"],
        phase_basis_ref=m["phase_basis_ref"], phase_basis_digest=m["phase_basis_digest"],
        program=m["program"], target=m["target"], stop=m["stop"],
        source=source, basis=m["basis"], evidence=evidence)


def test_fresh_receipt_first_replay_changed_command_and_zero_effect_rows(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        with acquire_sqlite_writer_session(location) as writer:
            fresh = writer._record_active_cancel_decision(command)
        assert type(fresh) is CancelDecisionCommittedV1
        changed = _variation(command, source_digest="9" * 64)
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._record_active_cancel_decision(command) == fresh
            assert writer._record_active_cancel_decision(changed).reason == "command_reused"
        with sqlite3.connect(location.database_path) as db:
            assert db.execute("SELECT COUNT(*) FROM rw0_cancel_decision_receipts").fetchone() == (1,)
            assert db.execute("SELECT COUNT(*) FROM development_effect_intents WHERE effect_class='cancel_effect'").fetchone() == (0,)
            assert db.execute("SELECT COUNT(*) FROM development_delivery_attempts WHERE basis_decision_ref=?",
                              (fresh.decision_ref,)).fetchone() == (0,)
            assert db.execute("SELECT COUNT(*) FROM rw0_terminal_anchors").fetchone() == (0,)


def test_decision_response_loss_and_three_way_recovery(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        original = transaction._CoordinatorMutationTransactionController._commit_after_fresh_writes
        def lost(self, result, **kwargs):
            original(self, result, **kwargs)
            raise transaction._commit_outcome_unknown()
        with monkeypatch.context() as patch:
            patch.setattr(transaction._CoordinatorMutationTransactionController,
                          "_commit_after_fresh_writes", lost)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as error:
                    writer._record_active_cancel_decision(command)
                assert error.value.error_class == "commit_outcome_unknown"
        with acquire_sqlite_writer_session(location) as writer:
            exact = writer._recover_active_cancel_decision(command)
        assert exact.status == "committed_exact"
        other = _variation(command, mutation_ref="mutation.other.offline")
        with acquire_sqlite_writer_session(location) as writer:
            absent = writer._recover_active_cancel_decision(other)
        assert absent.status == "definitely_not_committed"
        with monkeypatch.context() as patch:
            patch.setattr(decision_runtime, "_family_exact",
                          lambda *args: (_ for _ in ()).throw(decision_runtime._integrity()))
            with acquire_sqlite_writer_session(location) as writer:
                unresolved = writer._recover_active_cancel_decision(command)
        assert unresolved.status == "unresolved"


def test_terminal_phase_excludes_fresh_cancel_decision(monkeypatch):
    with prepared_cancel_case(monkeypatch, close_normal=True) as (location, command):
        with acquire_sqlite_writer_session(location) as writer:
            result = writer._record_active_cancel_decision(command)
        assert result.reason == "terminal_phase_occupied"
        with sqlite3.connect(location.database_path) as db:
            assert db.execute("SELECT COUNT(*) FROM rw0_cancel_decision_receipts").fetchone() == (0,)
            assert db.execute("SELECT COUNT(*) FROM development_decisions WHERE decision_kind='cancel'").fetchone() == (0,)
