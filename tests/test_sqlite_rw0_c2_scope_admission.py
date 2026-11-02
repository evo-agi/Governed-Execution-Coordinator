"""Causal artificial-offline P0 persistence tests through the guarded writer."""
from __future__ import annotations

from dataclasses import replace
import sqlite3

import pytest

from ge_nwp_coordinator._rw0_c2_scope_admission_contracts import (
    ArtificialAdmissionSourceV1, ScopeAdmissionCommandV1,
    ScopeAdmissionCommittedV1, ScopeAdmissionConflictV1, ScopeAdmissionRecoveryV1,
    _canonical, _self_digest, _build_family, _TABLE_FIELDS,
)
from ge_nwp_coordinator.sqlite_location import CoordinatorStateLocation
from ge_nwp_coordinator.sqlite_migration import initialize_database
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator import sqlite_transition_transaction as txn

P = "governed-execution.nwp-rw0-c2-"


def _command(letter: str = "A", *, operation_ref: str | None = None,
             fact_ref: str | None = None, lineage_ref: str | None = None,
             scope_ref: str | None = None) -> tuple[ScopeAdmissionCommandV1, ArtificialAdmissionSourceV1]:
    # Candidate construction and the fixed source observation are separate.
    act = {
        "schema_id": P + "verified-admission-act.v1", "act_ref": "act-" + letter,
        "act_digest": ("ac" if letter == "A" else "bc") * 32,
        "lineage_ref": lineage_ref or "lineage-" + letter,
        "scope_ref": scope_ref or "scope-" + letter,
        "guard_profile": "rw0-c2-guard-v1",
        "applicability": "admitted_direct_local_bootstrap",
        "provenance_ref": "policy-proof-" + letter,
        "provenance_digest": ("b1" if letter == "A" else "b2") * 32,
    }
    act["projection_digest"] = _self_digest(act, "projection_digest")
    fact = {
        "schema_id": P + "scope-admission-fact.v1",
        "admission_fact_ref": fact_ref or "admission-" + letter,
        **{name: act[name] for name in ("act_ref", "act_digest", "lineage_ref", "scope_ref", "guard_profile", "applicability", "provenance_ref", "provenance_digest")},
        "one_shot_ceiling": 1,
    }
    fact["admission_fact_digest"] = _self_digest(fact, "admission_fact_digest")
    payload = {
        "schema_id": P + "record-scope-admission-command.v1",
        "operation_ref": operation_ref or "admission-operation-" + letter,
        "verified_admission_act": act,
        "expected_admission_fact": fact,
        "enrollment_ref": "enrollment-" + letter,
        "incarnation_ref": "incarnation-" + letter,
        "authority_process_ref": "process-binding-" + letter,
        "storage_custody_ref": "storage-binding-" + letter,
        "proof_profile_id": "rw0-c2-single-realization-proof-v1",
    }
    payload["command_digest"] = _self_digest(payload, "command_digest")
    # This fixture-authored source subject is built independently of the
    # candidate command, including its own policy projection. The deliberate
    # mismatch test below proves the writer compares the two.
    fixed_policy = {
        "schema_id": P + "verified-admission-act.v1",
        "act_ref": "act-" + letter,
        "act_digest": ("ac" if letter == "A" else "bc") * 32,
        "lineage_ref": lineage_ref or "lineage-" + letter,
        "scope_ref": scope_ref or "scope-" + letter,
        "guard_profile": "rw0-c2-guard-v1",
        "applicability": "admitted_direct_local_bootstrap",
        "provenance_ref": "policy-proof-" + letter,
        "provenance_digest": ("b1" if letter == "A" else "b2") * 32,
    }
    fixed_policy["projection_digest"] = _self_digest(fixed_policy, "projection_digest")
    source = ArtificialAdmissionSourceV1(
        _canonical(fixed_policy), "ge-nwp-coordinator", "enrollment-" + letter,
        "incarnation-" + letter, "process-binding-" + letter,
        "storage-binding-" + letter, "enrollment-proof-" + letter,
        "11" * 32, "recording-proof-" + letter, "22" * 32,
        "custody-proof-" + letter, "33" * 32, True, True, True, True,
    )
    return ScopeAdmissionCommandV1.from_mapping(payload), source


def _location(tmp_path):
    location = CoordinatorStateLocation.from_trusted_root(tmp_path / "state")
    initialize_database(location)
    return location


def _count(location, table):
    connection = sqlite3.connect(location.database_path)
    try:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        connection.close()


def test_p0_preprogram_commit_replay_and_readback(tmp_path):
    location = _location(tmp_path)
    command, source = _command()
    with acquire_sqlite_writer_session(location) as writer:
        committed = writer._record_scope_admission(command, source)
        replay = writer._record_scope_admission(command, source)
        checked = writer._read_scope_admission(command, source)
        recovered = writer._recover_scope_admission(command, source)
    assert type(committed) is ScopeAdmissionCommittedV1
    assert replay == checked == committed
    assert type(recovered) is ScopeAdmissionRecoveryV1
    assert recovered.classification == "committed_exact"
    assert recovered.committed == committed
    for table in ("rw0_c2_verified_admission_acts", "rw0_c2_scope_admission_facts",
                  "rw0_c2_scope_admission_recording_bases", "rw0_c2_scope_admission_recording_receipts"):
        assert _count(location, table) == 1
    for table in ("development_program_heads", "development_decisions",
                  "development_mutation_receipts"):
        assert _count(location, table) == 0
    for table in (
        "rw0_c2_historical_continuity_bases",
        "rw0_c2_historical_sole_active_bases",
        "rw0_c2_decision_bases",
        "rw0_c2_guarded_family_relations",
        "rw0_c2_guarded_progression_results",
        "rw0_c2_bootstrap_acceptance_facts",
    ):
        assert _count(location, table) == 0
    # P0 admission alone must leave the later terminal family unpopulated.
    for table in (
        "rw0_terminal_contexts",
        "rw0_terminal_outcomes",
        "rw0_terminal_results",
        "rw0_terminal_receipts",
        "rw0_terminal_anchors",
    ):
        assert _count(location, table) == 0


def test_p0_exact_replay_requires_disclosure_but_not_renewed_recording(tmp_path):
    location = _location(tmp_path)
    command, source = _command()
    with acquire_sqlite_writer_session(location) as writer:
        original = writer._record_scope_admission(command, source)
        disclosure_only = replace(source, recording_permitted=False)
        assert writer._record_scope_admission(command, disclosure_only) == original
        assert writer._read_scope_admission(command, disclosure_only) == original
        with pytest.raises(SQLiteMutationStoreError):
            writer._record_scope_admission(
                command, replace(source, disclosure_permitted=False)
            )
    assert _count(location, "rw0_c2_scope_admission_recording_receipts") == 1


def test_p0_same_operation_different_command_is_no_write(tmp_path):
    location = _location(tmp_path)
    original, source = _command()
    changed, changed_source = _command("B", operation_ref="admission-operation-A")
    with acquire_sqlite_writer_session(location) as writer:
        writer._record_scope_admission(original, source)
        conflict = writer._record_scope_admission(changed, changed_source)
    assert type(conflict) is ScopeAdmissionConflictV1
    assert conflict.reason_code == "scope_admission_provisioning.operation_identity_conflict"
    assert _count(location, "rw0_c2_scope_admission_recording_receipts") == 1


def test_p0_same_act_new_operation_does_not_replenish(tmp_path):
    location = _location(tmp_path)
    original, source = _command()
    alternate, _ = _command(operation_ref="admission-operation-alternate",
                           fact_ref="admission-alternate")
    with acquire_sqlite_writer_session(location) as writer:
        writer._record_scope_admission(original, source)
        conflict = writer._record_scope_admission(alternate, source)
    assert type(conflict) is ScopeAdmissionConflictV1
    assert conflict.reason_code == "scope_admission_provisioning.already_recorded_under_other_operation"
    assert _count(location, "rw0_c2_scope_admission_facts") == 1


def test_p0_empty_original_readback_is_proven_noncommit(tmp_path):
    location = _location(tmp_path)
    command, source = _command()
    with acquire_sqlite_writer_session(location) as writer:
        result = writer._recover_scope_admission(command, source)
    assert result.classification == "definitely_not_committed"


def test_p0_unqualified_custody_cannot_recover_as_absent(tmp_path):
    location = _location(tmp_path)
    command, source = _command()
    with acquire_sqlite_writer_session(location) as writer:
        result = writer._recover_scope_admission(
            command, replace(source, old_execution_excluded=False)
        )
    assert result.classification == "unresolved"


def test_p0_candidate_cannot_substitute_for_independent_policy_source(tmp_path):
    location = _location(tmp_path)
    command, _ = _command()
    _, foreign_source = _command("B")
    with acquire_sqlite_writer_session(location) as writer:
        with pytest.raises(SQLiteMutationStoreError):
            writer._record_scope_admission(command, foreign_source)
    assert _count(location, "rw0_c2_scope_admission_recording_receipts") == 0


@pytest.mark.parametrize("route", ("lineage_ref", "scope_ref"))
def test_p0_lineage_or_scope_alias_is_no_write(tmp_path, route):
    location = _location(tmp_path)
    original, original_source = _command()
    kwargs = {route: "lineage-A" if route == "lineage_ref" else "scope-A"}
    alternate, alternate_source = _command("B", **kwargs)
    with acquire_sqlite_writer_session(location) as writer:
        writer._record_scope_admission(original, original_source)
        conflict = writer._record_scope_admission(alternate, alternate_source)
    assert type(conflict) is ScopeAdmissionConflictV1
    assert conflict.reason_code == "scope_admission_provisioning.admission_identity_conflict"
    assert _count(location, "rw0_c2_scope_admission_facts") == 1


def test_p0_partial_act_row_is_unverifiable_and_never_completed(tmp_path):
    location = _location(tmp_path)
    command, source = _command()
    act = command.to_mapping()["verified_admission_act"]
    assert type(act) is dict
    fields = tuple(act)
    with sqlite3.connect(location.database_path) as connection:
        connection.execute(
            "INSERT INTO rw0_c2_verified_admission_acts (" + ", ".join(fields)
            + ") VALUES (" + ", ".join("?" for _ in fields) + ")",
            tuple(act[field] for field in fields),
        )
    with acquire_sqlite_writer_session(location) as writer:
        conflict = writer._record_scope_admission(command, source)
        recovery = writer._recover_scope_admission(command, source)
    assert type(conflict) is ScopeAdmissionConflictV1
    assert conflict.reason_code == "scope_admission_provisioning.family_unverifiable"
    assert recovery.classification == "unresolved"
    assert _count(location, "rw0_c2_scope_admission_recording_receipts") == 0


def test_p0_orphan_fact_and_malformed_complete_family_are_unresolved(tmp_path):
    command, source = _command()
    act, fact, basis, _, receipt = _build_family(command, source, "2026-10-24T00:00:00Z")
    for variant in ("orphan", "malformed"):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as directory:
            location = _location(Path(directory))
            with sqlite3.connect(location.database_path) as connection:
                for table, row in (("rw0_c2_verified_admission_acts", act),
                                   ("rw0_c2_scope_admission_facts", fact)):
                    fields = _TABLE_FIELDS[table]
                    connection.execute(
                        f"INSERT INTO {table} ({', '.join(fields)}) VALUES "
                        f"({', '.join('?' for _ in fields)})",
                        tuple(row[field] for field in fields),
                    )
                if variant == "malformed":
                    wrong_basis = dict(basis, basis_digest="f" * 64)
                    wrong_receipt = dict(receipt, basis_digest="f" * 64)
                    for table, row in (("rw0_c2_scope_admission_recording_bases", wrong_basis),
                                       ("rw0_c2_scope_admission_recording_receipts", wrong_receipt)):
                        fields = _TABLE_FIELDS[table]
                        connection.execute(
                            f"INSERT INTO {table} ({', '.join(fields)}) VALUES "
                            f"({', '.join('?' for _ in fields)})",
                            tuple(row[field] for field in fields),
                        )
            with acquire_sqlite_writer_session(location) as writer:
                assert writer._recover_scope_admission(command, source).classification == "unresolved"
                if variant == "orphan":
                    conflict = writer._record_scope_admission(command, source)
                    assert type(conflict) is ScopeAdmissionConflictV1
                    assert conflict.reason_code == "scope_admission_provisioning.family_unverifiable"


def test_p0_unreadable_family_is_unresolved(tmp_path, monkeypatch):
    location = _location(tmp_path)
    command, source = _command()
    with acquire_sqlite_writer_session(location) as writer:
        writer._record_scope_admission(command, source)
    from ge_nwp_coordinator import _sqlite_rw0_c2_scope_admission as owner
    reached = []
    def unreadable(**kwargs):
        reached.append(kwargs["sql"])
        raise sqlite3.OperationalError("synthetic unreadable")
    with monkeypatch.context() as patch:
        patch.setattr(owner, "_execute_select_fetch_bounded", unreadable)
        with acquire_sqlite_writer_session(location) as writer:
            result = writer._recover_scope_admission(command, source)
    assert reached and result.classification == "unresolved"


def test_p0_rollback_after_partial_writes_leaves_definite_absence(tmp_path, monkeypatch):
    location = _location(tmp_path)
    command, source = _command()
    original = txn._write_scope_admission_after_fencing
    reached = []
    def fail_after_writes(*args):
        result = original(*args)
        reached.append(result)
        raise RuntimeError("synthetic failure before commit")
    with monkeypatch.context() as patch:
        patch.setattr(txn, "_write_scope_admission_after_fencing", fail_after_writes)
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError):
                writer._record_scope_admission(command, source)
    assert reached
    with acquire_sqlite_writer_session(location) as writer:
        assert writer._recover_scope_admission(command, source).classification == "definitely_not_committed"
    assert _count(location, "rw0_c2_verified_admission_acts") == 0


def test_p0_before_commit_response_loss_preserves_uncertainty(tmp_path, monkeypatch):
    location = _location(tmp_path)
    command, source = _command()
    reached = []
    def fail_before_commit(self):
        reached.append(True)
        raise RuntimeError("synthetic failure before underlying commit")
    with monkeypatch.context() as patch:
        patch.setattr(txn._ControllerConnectionScope, "commit", fail_before_commit)
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as error:
                writer._record_scope_admission(command, source)
    assert reached and error.value.error_class == "commit_outcome_unknown"
    with acquire_sqlite_writer_session(location) as writer:
        assert writer._recover_scope_admission(command, source).classification == "definitely_not_committed"


def test_p0_cleanup_uncertainty_quarantines_authority(tmp_path, monkeypatch):
    location = _location(tmp_path)
    command, source = _command()
    original = txn._RetainedSQLiteConnection._close_with_proof
    reached = []
    def lose_close_proof(self):
        result = original(self)
        reached.append(result)
        raise RuntimeError("synthetic close acknowledgment loss")
    with monkeypatch.context() as patch:
        patch.setattr(txn._RetainedSQLiteConnection, "_close_with_proof", lose_close_proof)
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError) as error:
                writer._record_scope_admission(command, source)
    assert reached and error.value.error_class == "commit_outcome_unknown"
    # An unproved close retains the live-process authority lock. Recovery must
    # wait for that authority to be safely released; no second writer is minted.
    with pytest.raises(Exception, match="state_authority_lock_busy"):
        acquire_sqlite_writer_session(location)
    assert _count(location, "rw0_c2_scope_admission_recording_receipts") == 1


def test_p0_commit_response_loss_after_underlying_commit_is_recoverable(tmp_path, monkeypatch):
    location = _location(tmp_path)
    command, source = _command()
    original = txn._ControllerConnectionScope.commit
    reached = []

    def lost_response(self):
        reached.append(True)
        original(self)
        raise RuntimeError("injected response loss after commit")

    with acquire_sqlite_writer_session(location) as writer:
        with monkeypatch.context() as patch:
            patch.setattr(txn._ControllerConnectionScope, "commit", lost_response)
            with pytest.raises(SQLiteMutationStoreError) as error:
                writer._record_scope_admission(command, source)
    assert reached
    assert error.value.error_class == "commit_outcome_unknown"
    with acquire_sqlite_writer_session(location) as writer:
        outcome = writer._recover_scope_admission(command, source)
    assert outcome.classification == "committed_exact"
