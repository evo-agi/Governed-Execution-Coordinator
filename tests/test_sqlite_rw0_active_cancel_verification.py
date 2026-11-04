"""Fresh local currentness versus missing source, mismatch, and corruption."""
from __future__ import annotations

import sqlite3

import pytest

from ge_nwp_coordinator import _development_effect_row_values as effect_values
from ge_nwp_coordinator._development_row_value_support import _domain_separated_digest
from ge_nwp_coordinator._rw0_cancel_decision_contracts import RecordRW0ActiveCancelDecisionCommandV1
from ge_nwp_coordinator._worker_execution_semantic_values import DeliveryEnvelopeV1
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from test_sqlite_rw0_active_cancel_connected import prepared_cancel_case, _row


def _shift_head(db: sqlite3.Connection, table: str, domain: str, columns: tuple[str, ...]) -> dict[str, object]:
    before = _row(db, table)
    after = dict(before)
    after["head_revision"] += 1
    after["updated_at"] = "2098-01-01T00:00:00Z"
    after["head_digest"] = _domain_separated_digest(
        domain, {k: after[k] for k in columns if k != "head_digest"})
    db.execute(f"UPDATE {table} SET head_revision=?, updated_at=?, head_digest=? WHERE effect_intent_ref=?",
               (after["head_revision"], after["updated_at"], after["head_digest"], after["effect_intent_ref"]))
    return before


def _restore_head(db: sqlite3.Connection, table: str, before: dict[str, object]) -> None:
    db.execute(f"UPDATE {table} SET head_revision=?, updated_at=?, head_digest=? WHERE effect_intent_ref=?",
               (before["head_revision"], before["updated_at"], before["head_digest"], before["effect_intent_ref"]))


def _verify(location, command, *, source=True):
    with acquire_sqlite_writer_session(location) as writer:
        return writer._verify_active_cancel_currentness(command, source)


def _reprepare(command, *, target=None, program=None, evidence=None):
    m = command.to_mapping()
    return RecordRW0ActiveCancelDecisionCommandV1.prepare(
        mutation_ref=m["mutation_ref"], phase_basis_ref=m["phase_basis_ref"],
        phase_basis_digest=m["phase_basis_digest"],
        program=m["program"] if program is None else program,
        target=m["target"] if target is None else target,
        stop=m["stop"], source=m["source"], basis=m["basis"],
        evidence=m["evidence"] if evidence is None else evidence)


def test_verifier_distinguishes_unresolved_source_and_three_owned_heads(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        assert _verify(location, command).classification == "commit_or_readback_unresolved"
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_active_cancel_decision(command)
        assert _verify(location, command).classification == "locally_current_source_unverified"
        assert _verify(location, command, source=False).classification == "external_source_unresolved"
        for table, domain, columns, expected in (
            ("development_effect_heads", effect_values._EFFECT_HEAD_DOMAIN,
             effect_values._DEVELOPMENT_EFFECT_HEAD_COLUMNS, "effect_head"),
            ("development_delivery_heads", effect_values._DELIVERY_HEAD_DOMAIN,
             effect_values._DEVELOPMENT_DELIVERY_HEAD_COLUMNS, "delivery_head"),
        ):
            with sqlite3.connect(location.database_path) as db:
                before = _shift_head(db, table, domain, columns)
            assert _verify(location, command).mismatch_class == expected
            with sqlite3.connect(location.database_path) as db:
                _restore_head(db, table, before)
        with sqlite3.connect(location.database_path) as db:
            before_time = db.execute("SELECT updated_at FROM global_stop_current").fetchone()[0]
            db.execute("UPDATE global_stop_current SET updated_at=?", ("2098-01-01T00:00:00Z",))
        assert _verify(location, command).mismatch_class == "global_stop"
        with sqlite3.connect(location.database_path) as db:
            db.execute("UPDATE global_stop_current SET updated_at=?", (before_time,))
        assert _verify(location, command).classification == "locally_current_source_unverified"


def test_missing_immutable_predecessor_is_corruption(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_active_cancel_decision(command)
        with sqlite3.connect(location.database_path) as db:
            db.execute("PRAGMA foreign_keys=OFF")
            guard = db.execute("SELECT sql FROM sqlite_schema WHERE name='development_effect_intents_no_delete'").fetchone()[0]
            db.execute("DROP TRIGGER development_effect_intents_no_delete")
            db.execute("DELETE FROM development_effect_intents WHERE effect_intent_ref=?",
                       (command.to_mapping()["target"]["effect_intent_ref"],))
            db.execute(guard)
        assert _verify(location, command).classification == "integrity_failure"


def test_terminal_winner_after_decision_occupies_phase(monkeypatch):
    with prepared_cancel_case(monkeypatch, with_normal=True) as (
        location, command, normal_command, normal_source
    ):
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_active_cancel_decision(command)
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_terminal_outcome(normal_command, normal_source)
        assert _verify(location, command).classification == "occupied_terminal_phase"


def test_stale_persisted_fence_and_version_basis_are_guarded_before_record(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        m = command.to_mapping()
        target = m["target"]
        target["effect_fence_digest"] = "f" * 64
        evidence = m["evidence"]
        evidence[1]["digest"] = "f" * 64
        stale_fence = _reprepare(command, target=target, evidence=evidence)
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as raised:
                writer._record_active_cancel_decision(stale_fence)
            assert raised.value.error_class == "database_integrity_failure"
        with sqlite3.connect(location.database_path) as db:
            assert db.execute("SELECT COUNT(*) FROM rw0_cancel_decision_receipts").fetchone() == (0,)
        program = m["program"]
        program["basis_decision_ref"] = "decision.stale.version"
        stale_version = _reprepare(command, program=program)
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._record_active_cancel_decision(stale_version).reason == "basis_changed"


def test_persisted_preassignment_is_proven_mismatch(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_active_cancel_decision(command)
        with sqlite3.connect(location.database_path) as db:
            existing = _row(db, "development_delivery_attempts")
            assert _domain_separated_digest(effect_values._DELIVERY_ATTEMPT_DOMAIN,
                {**{k: existing[k] for k in ("delivery_envelope_digest", "delivery_kind",
                                              "delivery_number", "predecessor_delivery_attempt_ref",
                                              "basis_decision_ref", "recorded_at")},
                 "schema_id": effect_values._DELIVERY_ATTEMPT_WRAPPER_SCHEMA}) == existing["delivery_attempt_digest"]
            preassigned = dict(existing)
            preassigned["delivery_attempt_ref"] = command.to_mapping()["preassigned_delivery_attempt_ref"]
            preassigned["delivery_kind"] = "redelivery"
            preassigned["delivery_number"] = existing["delivery_number"] + 1
            preassigned["predecessor_delivery_attempt_ref"] = existing["delivery_attempt_ref"]
            envelope = {k: preassigned[k] for k in (
                "delivery_attempt_ref", "program_ref", "program_version_ref", "command_ref",
                "command_digest", "semantic_attempt_ref", "effect_intent_ref",
                "attempt_fence_ref", "attempt_fence_digest", "effect_fence_ref",
                "effect_fence_digest", "adapter_kind", "adapter_safe_correlation_ref")}
            envelope["schema_id"] = "governed-execution.nwp-delivery-envelope.v1"
            preassigned["delivery_envelope_digest"] = _domain_separated_digest(
                "governed-execution.nwp-delivery-envelope.v1.identity", envelope)
            DeliveryEnvelopeV1.from_mapping({**envelope, "delivery_envelope_digest": preassigned["delivery_envelope_digest"]})
            preassigned["delivery_attempt_digest"] = _domain_separated_digest(
                effect_values._DELIVERY_ATTEMPT_DOMAIN,
                {**{k: preassigned[k] for k in ("delivery_envelope_digest", "delivery_kind",
                                                 "delivery_number", "predecessor_delivery_attempt_ref",
                                                 "basis_decision_ref", "recorded_at")},
                 "schema_id": effect_values._DELIVERY_ATTEMPT_WRAPPER_SCHEMA})
            columns = effect_values._DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS
            effect_values.development_delivery_attempt_row_value_from_row_tuple(
                tuple(preassigned[k] for k in columns))
            db.execute(f"INSERT INTO development_delivery_attempts ({', '.join(columns)}) "
                       f"VALUES ({', '.join('?' for _ in columns)})",
                       tuple(preassigned[k] for k in columns))
        result = _verify(location, command)
        assert result.classification == "proven_coordinator_mismatch"
        assert result.mismatch_class == "preassignment"
        assert result.mismatch_ref == preassigned["delivery_attempt_ref"]
