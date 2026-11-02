"""Guarded normal terminal routing through the immutable registry."""
from __future__ import annotations

import sqlite3
from copy import deepcopy
from contextlib import closing
from dataclasses import replace

import pytest

from ge_nwp_coordinator import sqlite_migration as migration
from ge_nwp_coordinator._rw0_c1_row_values import (
    PHASE_COLUMNS, build_row_mapping, rw0_c1_row_value_from_tuple,
)
from ge_nwp_coordinator._rw0_terminal_anchor_rows import COLUMNS as ANCHOR_COLUMNS, expected_normal_anchor
from ge_nwp_coordinator._rw0_terminal_outcome_contracts import RecordRW0TerminalOutcomeCommandV1
from ge_nwp_coordinator._rw0_terminal_outcome_rows import COLUMNS, CONTEXT, OUTCOME, RESULT, RECEIPT, checked_row
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode
from ge_nwp_coordinator import _sqlite_rw0_terminal_outcome as terminal_store
from test_sqlite_rw0_terminal_connected import prepared_normal_case


def _family(connection: sqlite3.Connection):
    return tuple(checked_row(table, connection.execute(
        f"SELECT {', '.join(COLUMNS[table])} FROM {table}").fetchone())
        for table in (CONTEXT, OUTCOME, RESULT, RECEIPT))


def _different_mutation(command):
    safe = command.to_mapping()
    return RecordRW0TerminalOutcomeCommandV1.prepare(
        mutation_ref="terminal.repair.alternative",
        p1_command=command.p1_command,
        section41_command=command.section41_command,
        c1_rank15=command.c1_rank15,
        heads=tuple(safe["heads"]), stop=safe["stop"],
        prior_decision_digest=safe["reached_owners"][15]["digest"],
        prior_guarded_result_digest=safe["reached_owners"][16]["digest"],
        prior_receipt_graph_digest=safe["reached_owners"][17]["digest"],
        expected_branch=safe["expected_branch"],
        expected_outcome=safe["expected_outcome"],
    )


class _TestSelectCapability:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def _borrow_connection_for_select(self) -> sqlite3.Connection:
        return self.connection


class _DecisionAliasSelector:
    """Isolate a decision alias distinct from the valid phase winner.

    A real same-P1 alternative command necessarily shares the winner's
    decision_ref, which is UNIQUE in the registry. This private seam varies
    only the safe lookup projection to exercise that otherwise unreachable
    alias collision while retaining the original transient owner operands.
    """

    def __init__(self, command, decision_ref):
        self.safe_bytes = command.safe_bytes
        self.command_digest = command.command_digest
        self.p1_command = command.p1_command
        self.section41_command = command.section41_command
        self.c1_rank15 = command.c1_rank15
        self._safe = deepcopy(command.to_mapping())
        self._safe["p1"]["relation"]["preassigned_decision_ref"] = decision_ref

    def to_mapping(self):
        return deepcopy(self._safe)


def _second_phase_parent(connection: sqlite3.Connection) -> tuple[str, str]:
    original = connection.execute(
        f"SELECT {', '.join(PHASE_COLUMNS)} FROM rw0_phase_instances"
    ).fetchone()
    assert original is not None
    phase = dict(zip(PHASE_COLUMNS, original, strict=True))
    phase["phase_basis_ref"] = "basis.repair.orphan"
    phase["phase_basis_digest"] = "a" * 64
    phase["k8_digest"] = "b" * 64
    phase["establishment_mutation_ref"] = "c1.repair.orphan"
    alternate_effect = connection.execute(
        "SELECT effect_intent_ref, effect_intent_digest "
        "FROM development_effect_intents WHERE program_ref=? "
        "AND effect_intent_ref<>? LIMIT 1",
        (phase["program_ref"], phase["effect_intent_ref"]),
    ).fetchone()
    assert alternate_effect is not None
    phase["effect_intent_ref"], phase["effect_intent_digest"] = alternate_effect
    phase = build_row_mapping(
        "rw0_phase_instances",
        {name: phase[name] for name in PHASE_COLUMNS if name != "phase_row_digest"},
    )
    connection.execute(
        f"INSERT INTO rw0_phase_instances ({', '.join(PHASE_COLUMNS)}) "
        f"VALUES ({', '.join('?' for _ in PHASE_COLUMNS)})",
        tuple(phase[name] for name in PHASE_COLUMNS),
    )
    inserted = connection.execute(
        f"SELECT {', '.join(PHASE_COLUMNS)} FROM rw0_phase_instances WHERE phase_basis_ref=?",
        (phase["phase_basis_ref"],),
    ).fetchone()
    assert rw0_c1_row_value_from_tuple("rw0_phase_instances", inserted).to_mapping() == phase
    return phase["phase_basis_ref"], phase["phase_basis_digest"]


def _orphan_alias_anchor(connection: sqlite3.Connection, alias: str, value: str):
    original = dict(zip(ANCHOR_COLUMNS, connection.execute(
        f"SELECT {', '.join(ANCHOR_COLUMNS)} FROM rw0_terminal_anchors"
    ).fetchone(), strict=True))
    phase_ref, phase_digest = _second_phase_parent(connection)
    other_decision = connection.execute(
        "SELECT decision_ref FROM development_decisions "
        "WHERE program_ref=? AND decision_ref<>? LIMIT 1",
        (original["program_ref"], original["decision_ref"]),
    ).fetchone()
    assert other_decision is not None
    orphan = dict(original)
    orphan.update(
        phase_basis_ref=phase_ref, phase_basis_digest=phase_digest,
        family_route="orphan.family-route", mutation_ref="orphan.mutation",
        decision_ref=other_decision[0], context_ref="orphan.context",
        outcome_value_ref="orphan.outcome", result_ref="orphan.result",
        receipt_ref="orphan.receipt",
    )
    orphan[alias] = value
    guard = connection.execute(
        "SELECT sql FROM sqlite_schema "
        "WHERE name='rw0_terminal_anchors_require_registered_family'"
    ).fetchone()[0]
    connection.execute("DROP TRIGGER rw0_terminal_anchors_require_registered_family")
    connection.execute(
        f"INSERT INTO rw0_terminal_anchors ({', '.join(ANCHOR_COLUMNS)}) "
        f"VALUES ({', '.join('?' for _ in ANCHOR_COLUMNS)})",
        tuple(orphan[name] for name in ANCHOR_COLUMNS),
    )
    connection.execute(guard)
    assert connection.execute(
        "SELECT sql FROM sqlite_schema "
        "WHERE name='rw0_terminal_anchors_require_registered_family'"
    ).fetchone()[0] == guard
    assert connection.execute(
        "SELECT COUNT(*) FROM rw0_terminal_receipts WHERE phase_basis_ref=?",
        (phase_ref,),
    ).fetchone()[0] == 0
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    return orphan


def test_record_replay_and_recovery_require_exact_anchor(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, _):
        with acquire_sqlite_writer_session(location) as writer:
            committed = writer._record_terminal_outcome(command, source)
            assert writer._read_terminal_outcome(command, source) == committed
            assert writer._record_terminal_outcome(command, source) == committed
            recovery = writer._recover_terminal_outcome(command, source)
            assert recovery.classification == "committed_exact"
            assert recovery.committed == committed
        with sqlite3.connect(location.database_path) as connection:
            family = _family(connection)
            expected = expected_normal_anchor(*family)
            anchors = connection.execute(
                f"SELECT {', '.join(ANCHOR_COLUMNS)} FROM rw0_terminal_anchors").fetchall()
            assert anchors == [expected.values]
            assert connection.execute("SELECT COUNT(*) FROM rw0_terminal_anchors").fetchone()[0] == 1


def test_clean_alternative_winner_keeps_collision_and_definite_absence(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, _):
        alternative = _different_mutation(command)
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_terminal_outcome(command, source)
        with closing(sqlite3.connect(location.database_path)) as connection:
            capability = _TestSelectCapability(connection)
            assert terminal_store.read_after_fencing(
                capability, alternative, source, "2029-01-01T00:00:00Z") is None
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._record_terminal_outcome(
                alternative, source).reason == "route_collision"
            assert writer._recover_terminal_outcome(
                alternative, source).classification == "definitely_not_committed"


@pytest.mark.parametrize("alias", (
    "family_route", "mutation_ref", "decision_ref", "context_ref",
    "outcome_value_ref", "result_ref", "receipt_ref",
))
def test_occupied_phase_checks_each_orphaned_registry_alias(monkeypatch, alias):
    with prepared_normal_case(monkeypatch) as (location, command, source, _):
        alternative = _different_mutation(command)
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_terminal_outcome(command, source)
        with closing(sqlite3.connect(location.database_path)) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            if alias == "decision_ref":
                # A valid same-P1 command necessarily proposes the winner's
                # UNIQUE decision_ref. Isolate the distinct lookup coordinate
                # at the private post-fence seam without relaxing that key.
                winner = connection.execute(
                    "SELECT program_ref, decision_ref FROM rw0_terminal_anchors"
                ).fetchone()
                other = connection.execute(
                    "SELECT decision_ref FROM development_decisions "
                    "WHERE program_ref=? AND decision_ref<>? LIMIT 1", winner
                ).fetchone()
                assert other is not None
                selector = _DecisionAliasSelector(alternative, other[0])
            else:
                selector = alternative
            safe = selector.to_mapping()
            value = (safe["p1"]["relation"]["preassigned_decision_ref"]
                     if alias == "decision_ref" else safe[alias])
            orphan = _orphan_alias_anchor(connection, alias, value)
            assert orphan[alias] == value
            connection.commit()
        assert migration.validate_database(location).classification is migration.DatabaseClassification.MANAGED
        with closing(sqlite3.connect(location.database_path)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            capability = _TestSelectCapability(connection)
            with pytest.raises(SQLiteMutationStoreError) as read_error:
                terminal_store.read_after_fencing(
                    capability, selector, source, "2029-01-01T00:00:00Z")
            assert read_error.value.error_class == SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value
            with pytest.raises(SQLiteMutationStoreError) as record_error:
                terminal_store.write_fresh_after_fencing(
                    capability, connection, selector, source, "2029-01-01T00:00:00Z")
            assert record_error.value.error_class == SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value
            assert terminal_store.recover_after_fencing(
                capability, selector, source,
                "2029-01-01T00:00:00Z").classification == "unresolved"
            connection.rollback()
        if alias != "decision_ref":
            with acquire_sqlite_writer_session(location) as writer:
                with pytest.raises(SQLiteMutationStoreError) as record_error:
                    writer._record_terminal_outcome(alternative, source)
                assert record_error.value.error_class == SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value
                assert writer._recover_terminal_outcome(
                    alternative, source).classification == "unresolved"


def test_anchor_is_immutable_and_missing_anchor_is_unresolved(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, _):
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_terminal_outcome(command, source)
        with sqlite3.connect(location.database_path) as connection:
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute("UPDATE rw0_terminal_anchors SET family_route='changed' ")
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute("DELETE FROM rw0_terminal_anchors")
            guard = connection.execute(
                "SELECT sql FROM sqlite_schema WHERE name='rw0_terminal_anchors_no_delete'"
            ).fetchone()[0]
            connection.execute("DROP TRIGGER rw0_terminal_anchors_no_delete")
            connection.execute("DELETE FROM rw0_terminal_anchors")
            connection.execute(guard)
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError):
                writer._read_terminal_outcome(command, source)
            with pytest.raises(SQLiteMutationStoreError):
                writer._record_terminal_outcome(command, source)
            assert writer._recover_terminal_outcome(command, source).classification == "unresolved"


def test_receipt_zero_row_registration_aborts_the_receipt_statement(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, _):
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_terminal_outcome(command, source)
        with closing(sqlite3.connect(location.database_path)) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            receipt = _family(connection)[3].mapping
            anchor_guard = connection.execute(
                "SELECT sql FROM sqlite_schema WHERE name='rw0_terminal_anchors_no_delete'"
            ).fetchone()[0]
            receipt_guard = connection.execute(
                "SELECT sql FROM sqlite_schema WHERE name='rw0_terminal_receipts_no_delete'"
            ).fetchone()[0]
            connection.execute("DROP TRIGGER rw0_terminal_anchors_no_delete")
            connection.execute("DELETE FROM rw0_terminal_anchors")
            connection.execute(anchor_guard)
            connection.execute("DROP TRIGGER rw0_terminal_receipts_no_delete")
            connection.execute("DELETE FROM rw0_terminal_receipts")
            connection.execute(receipt_guard)
            connection.commit()
        assert migration.validate_database(location).classification is migration.DatabaseClassification.MANAGED
        with closing(sqlite3.connect(location.database_path)) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            assert [connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    for table in (CONTEXT, OUTCOME, RESULT, RECEIPT)] == [1, 1, 1, 0]
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
            # The receipt's own CHECK and FK constraints admit this coordinate;
            # the registration SELECT must reject its cross-family mismatch.
            receipt["p1_decision_ref"] = "decision.repair.mismatch"
            with pytest.raises(sqlite3.IntegrityError, match="missing_rw0_terminal_anchor"):
                connection.execute(
                    f"INSERT INTO {RECEIPT} ({', '.join(COLUMNS[RECEIPT])}) "
                    f"VALUES ({', '.join('?' for _ in COLUMNS[RECEIPT])})",
                    tuple(receipt[name] for name in COLUMNS[RECEIPT]),
                )
            assert connection.execute(f"SELECT COUNT(*) FROM {RECEIPT}").fetchone()[0] == 0
            assert connection.execute("SELECT COUNT(*) FROM rw0_terminal_anchors").fetchone()[0] == 0


def test_anchor_without_selected_receipt_is_integrity_and_unresolved(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, _):
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_terminal_outcome(command, source)
        with closing(sqlite3.connect(location.database_path)) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            guard = connection.execute(
                "SELECT sql FROM sqlite_schema WHERE name='rw0_terminal_receipts_no_delete'"
            ).fetchone()[0]
            connection.execute("DROP TRIGGER rw0_terminal_receipts_no_delete")
            connection.execute("DELETE FROM rw0_terminal_receipts")
            connection.execute(guard)
            connection.commit()
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
            assert connection.execute("SELECT COUNT(*) FROM rw0_terminal_anchors").fetchone()[0] == 1
            assert connection.execute(f"SELECT COUNT(*) FROM {RECEIPT}").fetchone()[0] == 0
        assert migration.validate_database(location).classification is migration.DatabaseClassification.MANAGED
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as read_error:
                writer._read_terminal_outcome(command, source)
            assert read_error.value.error_class == SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE.value
            assert writer._recover_terminal_outcome(command, source).classification == "unresolved"


def test_protected_disclosure_precedes_anchor_lookup(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, _):
        calls = []
        real_read = terminal_store.read_terminal_anchor

        def read_after_disclosure(*args, **kwargs):
            calls.append(1)
            return real_read(*args, **kwargs)

        monkeypatch.setattr(terminal_store, "read_terminal_anchor", read_after_disclosure)
        denied = replace(source, disclosure_permitted=False)
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError):
                writer._read_terminal_outcome(command, denied)
            assert writer._recover_terminal_outcome(command, denied).classification == "unresolved"
            assert calls == []
            assert writer._record_terminal_outcome(command, denied).reason == "protected_posture_unavailable"
            assert calls == []


@pytest.mark.parametrize("column,value", (
    ("family_profile", "unsupported.v1"),
    ("graph_profile", "governed-execution.nwp-rw0-terminal-other-graph.v1"),
))
def test_direct_anchor_wrong_profile_rejected_even_with_complete_family(
    monkeypatch, column, value,
):
    with prepared_normal_case(monkeypatch) as (location, command, source, _):
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_terminal_outcome(command, source)
        with sqlite3.connect(location.database_path) as connection:
            row = connection.execute(
                f"SELECT {', '.join(ANCHOR_COLUMNS)} FROM rw0_terminal_anchors"
            ).fetchone()
            guard = connection.execute(
                "SELECT sql FROM sqlite_schema WHERE name='rw0_terminal_anchors_no_delete'"
            ).fetchone()[0]
            connection.execute("DROP TRIGGER rw0_terminal_anchors_no_delete")
            connection.execute("DELETE FROM rw0_terminal_anchors")
            connection.execute(guard)
            changed = list(row)
            changed[ANCHOR_COLUMNS.index(column)] = value
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(
                    f"INSERT INTO rw0_terminal_anchors ({', '.join(ANCHOR_COLUMNS)}) "
                    f"VALUES ({', '.join('?' for _ in ANCHOR_COLUMNS)})", changed)
            assert connection.execute("SELECT COUNT(*) FROM rw0_terminal_anchors").fetchone()[0] == 0


def test_phase_and_route_uniqueness_are_independent_constraints(monkeypatch):
    with prepared_normal_case(monkeypatch) as (location, command, source, _):
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_terminal_outcome(command, source)
        with sqlite3.connect(location.database_path, isolation_level=None) as connection:
            connection.execute("PRAGMA foreign_keys=OFF")
            original = dict(zip(ANCHOR_COLUMNS, connection.execute(
                f"SELECT {', '.join(ANCHOR_COLUMNS)} FROM rw0_terminal_anchors"
            ).fetchone(), strict=True))
            # Isolate the physical UNIQUE constraints from the family guard
            # in this temporary test database only.
            connection.execute("DROP TRIGGER rw0_terminal_anchors_require_registered_family")
            unique_names = ("family_route", "mutation_ref", "decision_ref",
                            "context_ref", "outcome_value_ref", "result_ref", "receipt_ref")
            candidate = {**original, **{
                name: f"other.{name.replace('_', '-')}" for name in unique_names
            }}
            insert = (f"INSERT INTO rw0_terminal_anchors ({', '.join(ANCHOR_COLUMNS)}) "
                      f"VALUES ({', '.join('?' for _ in ANCHOR_COLUMNS)})")
            with pytest.raises(sqlite3.IntegrityError) as phase_collision:
                connection.execute(insert, tuple(candidate[name] for name in ANCHOR_COLUMNS))
            assert "rw0_terminal_anchors.phase_basis_ref" in str(phase_collision.value)
            candidate["phase_basis_ref"] = "other.phase"
            candidate["family_route"] = original["family_route"]
            with pytest.raises(sqlite3.IntegrityError) as route_collision:
                connection.execute(insert, tuple(candidate[name] for name in ANCHOR_COLUMNS))
            assert "rw0_terminal_anchors.family_route" in str(route_collision.value)
            assert connection.execute("SELECT COUNT(*) FROM rw0_terminal_anchors").fetchone()[0] == 1
