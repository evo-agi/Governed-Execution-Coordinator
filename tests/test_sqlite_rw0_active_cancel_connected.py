"""Connected artificial-offline active-cancel decision and block fixture."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import sqlite3

import pytest

from ge_nwp_coordinator._rw0_cancel_decision_contracts import RecordRW0ActiveCancelDecisionCommandV1
from ge_nwp_coordinator._rw0_cancel_pre_effect_terminal_contracts import RecordRW0CancelPreEffectTerminalCommandV1
from ge_nwp_coordinator._development_row_value_support import _domain_separated_digest
from ge_nwp_coordinator import _development_effect_row_values as effect_values
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_sqlite_rw0_terminal_connected import prepared_normal_case


def _row(db: sqlite3.Connection, table: str, where: str = "1=1", args: tuple[object, ...] = ()) -> dict[str, object]:
    columns = tuple(item[1] for item in db.execute(f"PRAGMA table_info({table})"))
    row = db.execute(f"SELECT {', '.join(columns)} FROM {table} WHERE {where} LIMIT 1", args).fetchone()
    assert row is not None
    return dict(zip(columns, row, strict=True))


@contextmanager
def prepared_cancel_case(monkeypatch: pytest.MonkeyPatch, *, close_normal: bool = False,
                         with_normal: bool = False, branch: str = "candidate_acceptance"):
    with prepared_normal_case(monkeypatch, branch=branch) as (location, normal_command, normal_source, _):
        with sqlite3.connect(location.database_path) as db:
            phase = _row(db, "rw0_phase_instances")
            head = _row(db, "development_program_heads")
            version = _row(db, "development_program_versions", "program_version_ref=?",
                           (head["current_program_version_ref"],))
            attempt = _row(db, "development_semantic_attempts",
                           "semantic_attempt_ref=?", (phase["semantic_attempt_ref"],))
            attempt_fence = _row(db, "development_attempt_fences",
                                 "attempt_fence_ref=?", (phase["attempt_fence_ref"],))
            effect = _row(db, "development_effect_intents",
                          "effect_intent_ref=?", (phase["effect_intent_ref"],))
            fence = _row(db, "development_effect_fences",
                         "effect_intent_ref=?", (effect["effect_intent_ref"],))
            effect_head = _row(db, "development_effect_heads",
                               "effect_intent_ref=?", (effect["effect_intent_ref"],))
            delivery_head = _row(db, "development_delivery_heads",
                                 "effect_intent_ref=?", (effect["effect_intent_ref"],))
            author = _row(db, "development_author_commands",
                          "command_ref=?", (effect["command_ref"],))
            stop_row = _row(db, "global_stop_current")
        source = {"directive_ref": "cancel-directive.offline", "directive_digest": "1" * 64,
                  "evidence_ref": "cancel-evidence.offline", "evidence_digest": "2" * 64}
        evidence = [
            {"role": "cancel_target_effect", "ref": effect["effect_intent_ref"], "digest": effect_head["head_digest"]},
            {"role": "cancel_target_effect_fence", "ref": fence["effect_fence_ref"], "digest": fence["effect_fence_digest"]},
            {"role": "cancel_source_directive", "ref": source["directive_ref"], "digest": source["directive_digest"]},
            {"role": "cancel_source_evidence", "ref": source["evidence_ref"], "digest": source["evidence_digest"]},
        ]
        command = RecordRW0ActiveCancelDecisionCommandV1.prepare(
            mutation_ref="mutation.cancel.offline", phase_basis_ref=phase["phase_basis_ref"],
            phase_basis_digest=phase["phase_basis_digest"],
            program={"program_ref": head["program_ref"],
                     "program_version_ref": head["current_program_version_ref"],
                     "program_version_number": head["current_program_version_number"],
                     "basis_decision_ref": version["creating_decision_ref"],
                     "head_revision": head["head_revision"], "head_digest": head["head_digest"],
                     "semantic_attempt_ref": attempt["semantic_attempt_ref"],
                     "candidate_ref": attempt["candidate_ref"],
                     "attempt_fence_ref": attempt_fence["attempt_fence_ref"],
                     "attempt_fence_digest": attempt_fence["attempt_fence_digest"]},
            target={"effect_intent_ref": effect["effect_intent_ref"],
                    "effect_class": effect["effect_class"],
                    "effect_fence_ref": fence["effect_fence_ref"],
                    "effect_fence_digest": fence["effect_fence_digest"],
                    "effect_head": effect_head,
                    "delivery_attempt_ref": delivery_head["current_delivery_attempt_ref"],
                    "delivery_head": delivery_head,
                    "originating_command_ref": author["command_ref"],
                    "originating_command_digest": author["command_digest"],
                    "capsule_manifest_ref": None, "capsule_digest": None},
            stop={"ref": phase["global_stop_ref"], "version": stop_row["version"],
                  "state": "active" if stop_row["active"] else "clear",
                  "updated_at": stop_row["updated_at"]},
            source=source,
            basis={"repository_ref": fence["repository_ref"],
                   "base_git_object_format": fence["base_git_object_format"],
                   "base_git_oid": fence["base_git_oid"],
                   "path_ceiling_digest": hashlib.sha256(fence["path_ceiling_json"].encode()).hexdigest(),
                   "audience_ref": "audience.offline", "audience_digest": "3" * 64},
            evidence=evidence)
        if close_normal:
            with acquire_sqlite_writer_session(location) as writer:
                writer._record_terminal_outcome(normal_command, normal_source)
        if with_normal:
            yield location, command, normal_command, normal_source
        else:
            yield location, command


def test_connected_cancel_decision_and_source_unverified(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        with acquire_sqlite_writer_session(location) as writer:
            first = writer._record_active_cancel_decision(command)
        with acquire_sqlite_writer_session(location) as writer:
            again = writer._record_active_cancel_decision(command)
        assert again == first
        with acquire_sqlite_writer_session(location) as writer:
            current = writer._verify_active_cancel_currentness(command)
        assert current.classification == "locally_current_source_unverified"
        with sqlite3.connect(location.database_path) as db:
            assert db.execute("SELECT COUNT(*) FROM rw0_cancel_decision_receipts").fetchone() == (1,)
            assert db.execute("SELECT COUNT(*) FROM rw0_terminal_anchors").fetchone() == (0,)


def test_connected_proven_effect_head_mismatch_closes_one_cancel_bound_block(monkeypatch):
    with prepared_cancel_case(monkeypatch) as (location, command):
        with acquire_sqlite_writer_session(location) as writer:
            decision = writer._record_active_cancel_decision(command)
        with sqlite3.connect(location.database_path) as db:
            head = _row(db, "development_effect_heads")
            head["head_revision"] += 1
            head["updated_at"] = "2098-01-01T00:00:00Z"
            head["head_digest"] = _domain_separated_digest(
                effect_values._EFFECT_HEAD_DOMAIN,
                {k: head[k] for k in effect_values._DEVELOPMENT_EFFECT_HEAD_COLUMNS
                 if k != "head_digest"})
            db.execute("UPDATE development_effect_heads SET head_revision=?, updated_at=?, head_digest=? WHERE effect_intent_ref=?",
                       (head["head_revision"], head["updated_at"], head["head_digest"], head["effect_intent_ref"]))
        with acquire_sqlite_writer_session(location) as writer:
            current = writer._verify_active_cancel_currentness(command)
        assert current.classification == "proven_coordinator_mismatch"
        assert current.mismatch_class == "effect_head"
        terminal = RecordRW0CancelPreEffectTerminalCommandV1.prepare(
            mutation_ref="mutation.cancel.block.offline", decision_command=command,
            committed=decision, verification=current)
        with acquire_sqlite_writer_session(location) as writer:
            first = writer._record_cancel_pre_effect_block(terminal)
        with acquire_sqlite_writer_session(location) as writer:
            again = writer._record_cancel_pre_effect_block(terminal)
        assert again == first
        with sqlite3.connect(location.database_path) as db:
            assert db.execute("SELECT COUNT(*) FROM rw0_terminal_anchors").fetchone() == (1,)
            assert db.execute("SELECT decision_kind FROM development_decisions WHERE decision_ref=?",
                              (decision.decision_ref,)).fetchone() == ("cancel",)
            assert db.execute("SELECT COUNT(*) FROM development_decisions WHERE decision_kind='block'").fetchone() == (0,)
