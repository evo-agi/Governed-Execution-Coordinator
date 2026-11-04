"""Cancel-bound block transaction, historical replay, and recovery."""
from __future__ import annotations

from dataclasses import replace
import sqlite3

import pytest

from ge_nwp_coordinator import _development_effect_row_values as effect_values
from ge_nwp_coordinator import _sqlite_rw0_cancel_pre_effect_terminal as terminal_runtime
from ge_nwp_coordinator import sqlite_transition_transaction as transaction
from ge_nwp_coordinator._rw0_cancel_pre_effect_terminal_plan import build_cancel_terminal_plan
from ge_nwp_coordinator._rw0_cancel_pre_effect_terminal_rows import COLUMNS, CONTEXT
from ge_nwp_coordinator._sqlite_rw0_terminal_anchor_migration_invariants_0010 import verify_terminal_anchor_families_0010
from ge_nwp_coordinator._rw0_cancel_pre_effect_terminal_contracts import RecordRW0CancelPreEffectTerminalCommandV1
from ge_nwp_coordinator._rw0_terminal_outcome_contracts import _canonical
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_sqlite_rw0_active_cancel_connected import prepared_cancel_case
from test_sqlite_rw0_active_cancel_verification import _shift_head, _restore_head


def _ready(location, command):
    with acquire_sqlite_writer_session(location) as writer:
        decision = writer._record_active_cancel_decision(command)
    with sqlite3.connect(location.database_path) as db:
        before = _shift_head(db, "development_effect_heads",
                             effect_values._EFFECT_HEAD_DOMAIN,
                             effect_values._DEVELOPMENT_EFFECT_HEAD_COLUMNS)
    with acquire_sqlite_writer_session(location) as writer:
        current = writer._verify_active_cancel_currentness(command)
    assert current.classification == "proven_coordinator_mismatch"
    terminal = RecordRW0CancelPreEffectTerminalCommandV1.prepare(
        mutation_ref="mutation.cancel.block.offline", decision_command=command,
        committed=decision, verification=current)
    return decision, current, terminal, before


def _variation(command, decision, current, *, mutation_ref="mutation.cancel.block.offline",
               mismatch_digest=None):
    if mismatch_digest is not None:
        current = replace(current, mismatch_digest=mismatch_digest,
            verification_safe_bytes=_canonical({
                "classification": "proven_coordinator_mismatch",
                "mismatch_class": current.mismatch_class,
                "mismatch_ref": current.mismatch_ref,
                "mismatch_digest": mismatch_digest}))
    return RecordRW0CancelPreEffectTerminalCommandV1.prepare(
        mutation_ref=mutation_ref, decision_command=command,
        committed=decision, verification=current)


def test_fresh_block_exact_replay_changed_command_and_competing_normal_route(monkeypatch):
    with prepared_cancel_case(monkeypatch, with_normal=True) as (
        location, command, normal_command, normal_source
    ):
        decision, current, terminal, _ = _ready(location, command)
        with acquire_sqlite_writer_session(location) as writer:
            first = writer._record_cancel_pre_effect_block(terminal)
        changed = _variation(command, decision, current, mismatch_digest="0" * 64)
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._record_cancel_pre_effect_block(terminal) == first
            assert writer._record_cancel_pre_effect_block(changed).reason == "command_reuse"
            assert writer._record_terminal_outcome(normal_command, normal_source).reason == "route_collision"
        with sqlite3.connect(location.database_path) as db:
            assert db.execute("SELECT COUNT(*) FROM rw0_terminal_anchors").fetchone() == (1,)
            assert db.execute("SELECT COUNT(*) FROM rw0_cancel_pre_effect_receipts").fetchone() == (1,)
            assert db.execute("SELECT COUNT(*) FROM development_decisions WHERE decision_kind='block'").fetchone() == (0,)
            assert db.execute("SELECT COUNT(*) FROM development_effect_intents WHERE effect_class='cancel_effect'").fetchone() == (0,)
            assert db.execute("SELECT COUNT(*) FROM rw0_wire_cancellation_request_observations").fetchone() == (0,)


def test_changed_mismatch_before_terminal_write_fails_closed(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        _, _, terminal, before = _ready(location, command)
        with sqlite3.connect(location.database_path) as db:
            _restore_head(db, "development_effect_heads", before)
        with acquire_sqlite_writer_session(location) as writer:
            result = writer._record_cancel_pre_effect_block(terminal)
        assert result.reason == "mismatch_not_current"
        with sqlite3.connect(location.database_path) as db:
            assert db.execute("SELECT COUNT(*) FROM rw0_terminal_anchors").fetchone() == (0,)
            assert db.execute("SELECT COUNT(*) FROM rw0_cancel_pre_effect_receipts").fetchone() == (0,)


def test_terminal_lost_commit_response_three_way_recovery_and_historical_replay(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        decision, current, terminal, _ = _ready(location, command)
        original = transaction._CoordinatorMutationTransactionController._commit_after_fresh_writes
        def lost(self, result, **kwargs):
            original(self, result, **kwargs)
            raise transaction._commit_outcome_unknown()
        with monkeypatch.context() as patch:
            patch.setattr(transaction._CoordinatorMutationTransactionController,
                          "_commit_after_fresh_writes", lost)
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as error:
                    writer._record_cancel_pre_effect_block(terminal)
                assert error.value.error_class == "commit_outcome_unknown"
        with sqlite3.connect(location.database_path) as db:
            _shift_head(db, "development_effect_heads",
                        effect_values._EFFECT_HEAD_DOMAIN,
                        effect_values._DEVELOPMENT_EFFECT_HEAD_COLUMNS)
        with acquire_sqlite_writer_session(location) as writer:
            exact = writer._recover_cancel_pre_effect_block(terminal)
            replay = writer._record_cancel_pre_effect_block(terminal)
        assert exact.status == "committed_exact"
        assert replay == exact.committed
        other = _variation(command, decision, current, mutation_ref="mutation.cancel.block.other")
        with acquire_sqlite_writer_session(location) as writer:
            absent = writer._recover_cancel_pre_effect_block(other)
        assert absent.status == "definitely_not_committed"
        with monkeypatch.context() as patch:
            patch.setattr(terminal_runtime, "_original_family",
                          lambda *args: (_ for _ in ()).throw(terminal_runtime._integrity()))
            with acquire_sqlite_writer_session(location) as writer:
                unresolved = writer._recover_cancel_pre_effect_block(terminal)
        assert unresolved.status == "unresolved"


def _change_immutable(db: sqlite3.Connection, trigger_name: str, sql: str) -> None:
    trigger = db.execute("SELECT sql FROM sqlite_schema WHERE name=?", (trigger_name,)).fetchone()[0]
    db.execute(f"DROP TRIGGER {trigger_name}")
    db.execute(sql)
    db.execute(trigger)


@pytest.mark.parametrize("damage", ("family_only", "anchor_only", "wrong_profile", "malformed_graph"))
def test_cancel_route_corruption_is_never_replay_or_clean_collision(monkeypatch, damage):
    with prepared_cancel_case(monkeypatch) as (location, command):
        _, _, terminal, _ = _ready(location, command)
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_cancel_pre_effect_block(terminal)
        with sqlite3.connect(location.database_path) as db:
            db.execute("PRAGMA foreign_keys=OFF")
            if damage == "family_only":
                _change_immutable(db, "rw0_terminal_anchors_no_delete",
                                  "DELETE FROM rw0_terminal_anchors")
            elif damage == "anchor_only":
                _change_immutable(db, "rw0_cancel_pre_effect_receipts_no_delete",
                                  "DELETE FROM rw0_cancel_pre_effect_receipts")
            elif damage == "wrong_profile":
                _change_immutable(db, "rw0_terminal_anchors_no_update",
                                  "UPDATE rw0_terminal_anchors SET family_profile='unknown.v1'")
            else:
                _change_immutable(db, "rw0_cancel_pre_effect_receipts_no_update",
                                  "UPDATE rw0_cancel_pre_effect_receipts SET graph_digest="
                                  "(CASE WHEN substr(graph_digest,1,1)='0' THEN '1' ELSE '0' END) || substr(graph_digest,2)")
            with pytest.raises((ValueError, SQLiteMutationStoreError)):
                verify_terminal_anchor_families_0010(db)
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as error:
                writer._record_cancel_pre_effect_block(terminal)
            assert error.value.error_class == "database_integrity_failure"
            assert writer._recover_cancel_pre_effect_block(terminal).status == "unresolved"
            assert writer._verify_active_cancel_currentness(command).classification == "integrity_failure"
            with pytest.raises(SQLiteMutationStoreError) as decision_error:
                writer._record_active_cancel_decision(command)
            assert decision_error.value.error_class == "database_integrity_failure"


def test_partial_context_alias_without_anchor_is_integrity_failure(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        _, _, terminal, _ = _ready(location, command)
        context = build_cancel_terminal_plan(terminal, "2098-01-01T00:00:00Z").rows[0]
        with sqlite3.connect(location.database_path) as db:
            columns = COLUMNS[CONTEXT]
            db.execute(f"INSERT INTO {CONTEXT} ({', '.join(columns)}) "
                       f"VALUES ({', '.join('?' for _ in columns)})", context.values)
            with pytest.raises(ValueError):
                verify_terminal_anchor_families_0010(db)
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as error:
                writer._record_cancel_pre_effect_block(terminal)
            assert error.value.error_class == "database_integrity_failure"
            assert writer._recover_cancel_pre_effect_block(terminal).status == "unresolved"
            assert writer._verify_active_cancel_currentness(command).classification == "integrity_failure"
            with pytest.raises(SQLiteMutationStoreError) as decision_error:
                writer._record_active_cancel_decision(command)
            assert decision_error.value.error_class == "database_integrity_failure"
