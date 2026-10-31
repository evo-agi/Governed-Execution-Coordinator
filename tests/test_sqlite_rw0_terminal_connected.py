"""Source-coherent artificial D1/D2 to normal terminal closure."""
from __future__ import annotations

from copy import deepcopy
from contextlib import contextmanager
from dataclasses import replace
import sqlite3

import pytest

from ge_nwp_coordinator import _development_program_row_values as pr
from ge_nwp_coordinator import _development_effect_row_values as er
from ge_nwp_coordinator import _cognitive_proposal_row_values as cr
from ge_nwp_coordinator._rw0_terminal_head_witness import (
    WITNESS_BYTE_CEILING, WITNESS_SCHEMA, witness_from_bytes,
)
from ge_nwp_coordinator._development_row_value_support import _domain_separated_digest
from ge_nwp_coordinator import _rw0_d1_offline as d1
from ge_nwp_coordinator._rw0_c2_progression_contracts import (
    ArtificialDecisionGuardSourceV1, _canonical, _self_digest,
)
from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture
from ge_nwp_coordinator._rw0_d2_offline import run_rw0_d2_offline
from ge_nwp_coordinator._rw0_d2_post_execution_continuation import continue_open_rw0_d2_run
from ge_nwp_coordinator._rw0_terminal_outcome_contracts import (
    NORMAL_PAIRS, RecordRW0TerminalOutcomeCommandV1, TerminalCommittedV1,
    TerminalConflictV1,
)
from ge_nwp_coordinator import _rw0_terminal_outcome_rows as terminal_rows
from ge_nwp_coordinator._section41_post_execution_proposal_mutation_contracts import (
    prepare_record_command,
)
from ge_nwp_coordinator.global_stop import GLOBAL_STOP_CLEAR_REF
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from test_post_execution_pure_owner_values import _seal
from test_rw0_c2_progression_contracts import _basis, _replan_proposal
from test_rw0_c2_progression_plan import _command, _history
from test_sqlite_rw0_c2_connected import _connected_basis, _golden_spec
from test_sqlite_rw0_c2_scope_admission import _command as _p0_command
from test_sqlite_rw0_c2_progression import STAMP


CASES = (
    ("candidate_acceptance", b"package contracts\n\nfunc TestContract() {}\n"),
    ("candidate_repair", b"package contracts\n\nfunc TestContract() {}\n// UNSAFE-CHANGE\n"),
    ("attempt_selecting_replan", b"package contracts\n\nfunc TestContract() {}\n// VALIDATION-REPLAN\n"),
    ("program_terminal_reject", b"package contracts\n\nfunc TestContract() {}\n// VALIDATION-TERMINAL\n"),
    ("post_execution_program_block", b"package contracts\n\nfunc TestContract() {}\n// VALIDATION-UNCLASSIFIED\n"),
)
RECOMMENDATION_BRANCH = {
    "accept_candidate": "candidate_acceptance",
    "repair_candidate": "candidate_repair",
    "replan": "attempt_selecting_replan",
    "terminal_reject": "program_terminal_reject",
    "block": "post_execution_program_block",
}


def _source_basis(run, projection, branch: str):
    checkpoint = run.handback.evidence_checkpoint
    assert checkpoint is not None
    actual_validation = checkpoint.validation_disposition.to_mapping()
    actual_review = checkpoint.review_disposition.to_mapping()
    basis = deepcopy(_basis())
    snapshot = basis["decision_current_snapshot"]
    for name in (
        "program_ref", "program_version_ref", "accepted_intent_revision_ref",
        "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
        "candidate_ref", "attempt_fence_ref", "attempt_fence_digest",
    ):
        snapshot[name] = actual_validation[name]
    snapshot["captured_at"] = STAMP
    for entry in snapshot["external_sources"]:
        if entry["role"] in ("validation", "review"):
            actual = actual_validation if entry["role"] == "validation" else actual_review
            entry["source_ref"] = actual["source_observation_ref"]
            entry["source_digest"] = actual["source_observation_digest"]
    basis["decision_current_snapshot"] = _seal("V27", snapshot)
    basis["proposal_family_projection"] = projection.to_mapping()
    currentness = basis["proposal_evidence_currentness"]
    currentness["proposal_ref"] = projection.proposal_ref
    currentness["proposal_digest"] = projection.proposal_digest
    currentness["snapshot_ref"] = snapshot["snapshot_ref"]
    currentness["snapshot_digest"] = snapshot["snapshot_digest"]
    currentness["evaluated_at"] = STAMP
    for component in currentness["components"]:
        component["evaluated_at"] = STAMP
        component["source_expires_at"] = "2099-01-01T00:00:00Z"
    basis["proposal_evidence_currentness"] = _seal("V29", currentness)
    for name, version in (("standing_policy_branch_matrix", "V17"),
                          ("risk_lane_branch_matrix", "V18")):
        matrix = basis[name]
        for field in (
            "program_ref", "program_version_ref", "accepted_intent_revision_ref",
            "work_item_revision_ref", "semantic_attempt_ref", "candidate_ref",
        ):
            matrix[field] = snapshot[field]
        matrix["work_item_ref" if version == "V17" else "development_work_item_ref"] = snapshot["work_item_ref"]
        basis[name] = _seal(version, matrix)
    for name, version in (("decision_time_authority_branch_matrix", "V31"),
                          ("decision_time_global_stop_branch_matrix", "V32"),
                          ("decision_time_source_effect_ceiling_branch_matrix", "V33")):
        matrix = basis[name]
        matrix["snapshot_ref"] = snapshot["snapshot_ref"]
        matrix["snapshot_digest"] = snapshot["snapshot_digest"]
        matrix["evaluated_at"] = STAMP
        if version == "V31":
            matrix["proposal_ref"] = projection.proposal_ref
            matrix["proposal_digest"] = projection.proposal_digest
        basis[name] = _seal(version, matrix)
    model = basis["recommendation_consistency_evaluation"]
    mapped = RECOMMENDATION_BRANCH[projection.recommendation]
    model.update(
        proposal_ref=projection.proposal_ref,
        proposal_digest=projection.proposal_digest,
        snapshot_ref=snapshot["snapshot_ref"],
        snapshot_digest=snapshot["snapshot_digest"],
        proposal_currentness_ref=currentness["currentness_ref"],
        proposal_currentness_digest=currentness["currentness_digest"],
        model_recommendation=projection.recommendation,
        mapped_branch=mapped, authoritative_branch=branch, evaluated_at=STAMP,
    )
    model["result"] = "consistent" if mapped == branch else "inconsistent"
    model["reason"] = ("mapped_branch_equals_authoritative_branch" if mapped == branch
                       else "mapped_branch_differs_from_authoritative_branch")
    basis["recommendation_consistency_evaluation"] = _seal("V34", model)
    proposal = _replan_proposal(basis) if branch == "attempt_selecting_replan" else None
    if proposal is not None:
        basis["replan_proposal_safe_projection"] = proposal.safe_projection()
    continuity = _history(basis, False)
    sole = _history(basis, True)
    basis["bootstrap_guard_evidence"]["guard_digest"] = _self_digest(
        basis["bootstrap_guard_evidence"], "guard_digest")
    basis["captured_at"] = STAMP
    basis["validation_disposition"] = checkpoint.validation_disposition.to_mapping()
    basis["independent_review_disposition"] = checkpoint.review_disposition.to_mapping()
    basis["basis_digest"] = _self_digest(basis, "basis_digest")
    return basis, continuity, sole, proposal, checkpoint.validation_disposition, checkpoint.review_disposition


def _terminal_selector(db: sqlite3.Connection, p1_command, post_command, rank15, committed):
    relation = p1_command.relation.to_mapping()
    program_ref = relation["program_ref"]
    work_ref = p1_command.basis.to_mapping()["decision_current_snapshot"]["work_item_ref"]
    phase_ref = post_command.phase_basis_ref
    effect_ref = db.execute(
        "SELECT effect_intent_ref FROM rw0_phase_instances WHERE phase_basis_ref=?",
        (phase_ref,)).fetchone()[0]
    rows = (
        ("program", program_ref, "development_program_heads", "program_ref", program_ref),
        ("work", work_ref, "development_work_item_heads", "work_item_ref", work_ref),
        ("selection", effect_ref, "development_pre_execution_selection_heads", "effect_intent_ref", effect_ref),
        ("effect", effect_ref, "development_effect_heads", "effect_intent_ref", effect_ref),
        ("delivery", effect_ref, "development_delivery_heads", "effect_intent_ref", effect_ref),
    )
    heads = []
    for role, owner_ref, table, key, value in rows:
        revision, digest = db.execute(
            f"SELECT head_revision, head_digest FROM {table} WHERE {key}=?",
            (value,)).fetchone()
        heads.append({"role": role, "owner_ref": owner_ref,
                      "revision": revision, "digest": digest})
    version, active, stop_id, updated_at = db.execute(
        "SELECT version, active, stop_id, updated_at FROM global_stop_current"
    ).fetchone()
    stop = {"ref": stop_id if active else GLOBAL_STOP_CLEAR_REF,
            "version": version, "state": "active" if active else "clear",
            "updated_at": updated_at}
    decision_digest = db.execute(
        "SELECT decision_digest FROM development_decisions WHERE decision_ref=?",
        (committed.decision_ref,)).fetchone()[0]
    return RecordRW0TerminalOutcomeCommandV1.prepare(
        mutation_ref="terminal." + committed.decision_ref[:70],
        p1_command=p1_command, section41_command=post_command,
        c1_rank15=rank15, heads=tuple(heads), stop=stop,
        prior_decision_digest=decision_digest,
        prior_guarded_result_digest=committed.result_digest,
        prior_receipt_graph_digest=committed.receipt_graph_digest,
        expected_branch=committed.branch,
        expected_outcome=NORMAL_PAIRS[committed.branch],
    )


def _changed_assertion(command: RecordRW0TerminalOutcomeCommandV1):
    safe = command.to_mapping()
    return RecordRW0TerminalOutcomeCommandV1.prepare(
        mutation_ref=safe["mutation_ref"],
        p1_command=command.p1_command,
        section41_command=command.section41_command,
        c1_rank15=command.c1_rank15,
        heads=tuple(safe["heads"]), stop=safe["stop"],
        prior_decision_digest=safe["reached_owners"][15]["digest"],
        prior_guarded_result_digest=safe["reached_owners"][16]["digest"],
        prior_receipt_graph_digest=safe["reached_owners"][17]["digest"],
        expected_branch=None,
        expected_outcome=safe["expected_outcome"],
    )


def _advance_program_head(db: sqlite3.Connection) -> None:
    columns = pr._DEVELOPMENT_PROGRAM_HEAD_COLUMNS
    row = dict(zip(columns, db.execute(
        "SELECT " + ", ".join(columns) + " FROM development_program_heads").fetchone(), strict=True))
    row["head_revision"] += 1
    row["updated_at"] = "2098-01-01T00:00:00Z"
    identity = {key: row[key] for key in columns if key != "head_digest"}
    row["head_digest"] = _domain_separated_digest(pr._DEVELOPMENT_PROGRAM_HEAD_DOMAIN, identity)
    db.execute("UPDATE development_program_heads SET head_revision=?, updated_at=?, head_digest=? WHERE program_ref=?",
               (row["head_revision"], row["updated_at"], row["head_digest"], row["program_ref"]))


@contextmanager
def prepared_normal_case(monkeypatch, branch: str = "candidate_acceptance"):
    """Test-only source-coherent predecessor chain; caller owns terminal step."""
    contract = dict(CASES)[branch]
    spec = _golden_spec()
    fixture = artificial_fixture(spec)
    fixture = replace(fixture, base_entries=(
        fixture.base_entries[0], fixture.base_entries[1],
        (fixture.base_entries[2][0], contract, "100644")))
    p0_command, p0_source = _p0_command()
    original_initialize = d1.initialize_database
    def initialize_with_p0(location):
        result = original_initialize(location)
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_scope_admission(p0_command, p0_source)
        return result
    with monkeypatch.context() as patch:
        patch.setattr(d1, "initialize_database", initialize_with_p0)
        with run_rw0_d2_offline(spec, fixture) as run:
            assert run.handback.status == "preadmission_ready"
            post_command, _ = prepare_record_command(run)
            continuation = continue_open_rw0_d2_run(run)
            assert continuation.status == "projected"
            basis, continuity, sole, proposal, validation, review = _source_basis(
                run, continuation.projection, branch)
            location = run._d1_run.location
            with sqlite3.connect(location.database_path) as db:
                columns = pr._DEVELOPMENT_PROGRAM_HEAD_COLUMNS
                head = pr.development_program_head_row_value_from_row_tuple(
                    db.execute("SELECT " + ", ".join(columns)
                               + " FROM development_program_heads").fetchone())
            p1_command = _command(basis, head, continuity, sole,
                                  expected_branch=branch, proposal=proposal)
            source = ArtificialDecisionGuardSourceV1(
                _canonical(continuity), _canonical(sole),
                "2020-01-01T00:00:00Z", "2099-01-01T00:00:00Z",
                True, True, True, True, True, True, True)
            with acquire_sqlite_writer_session(location) as writer:
                p1 = writer._record_progression_decision(p1_command, source, validation, review)
                assert p1.branch == branch
            with sqlite3.connect(location.database_path) as db:
                terminal_command = _terminal_selector(
                    db, p1_command, post_command, continuation.admission_result, p1)
            yield location, terminal_command, source, p1


@pytest.mark.parametrize("branch,contract", CASES)
def test_connected_source_coherent_normal_terminal(tmp_path, monkeypatch, branch, contract):
    spec = _golden_spec()
    fixture = artificial_fixture(spec)
    fixture = replace(fixture, base_entries=(
        fixture.base_entries[0], fixture.base_entries[1],
        (fixture.base_entries[2][0], contract, "100644"),
    ))
    p0_command, p0_source = _p0_command()
    original_initialize = d1.initialize_database
    def initialize_with_p0(location):
        result = original_initialize(location)
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_scope_admission(p0_command, p0_source)
        return result
    monkeypatch.setattr(d1, "initialize_database", initialize_with_p0)
    with run_rw0_d2_offline(spec, fixture) as run:
        assert run.handback.status == "preadmission_ready"
        post_command, _ = prepare_record_command(run)
        continuation = continue_open_rw0_d2_run(run)
        assert continuation.status == "projected", continuation.reason
        assert RECOMMENDATION_BRANCH[continuation.projection.recommendation] == branch
        basis, continuity, sole, proposal, validation, review = _source_basis(
            run, continuation.projection, branch)
        location = run._d1_run.location
        with sqlite3.connect(location.database_path) as db:
            columns = pr._DEVELOPMENT_PROGRAM_HEAD_COLUMNS
            head = pr.development_program_head_row_value_from_row_tuple(
                db.execute("SELECT " + ", ".join(columns)
                           + " FROM development_program_heads").fetchone())
        p1_command = _command(basis, head, continuity, sole,
                              expected_branch=branch, proposal=proposal)
        source = ArtificialDecisionGuardSourceV1(
            _canonical(continuity), _canonical(sole),
            "2020-01-01T00:00:00Z", "2099-01-01T00:00:00Z",
            True, True, True, True, True, True, True,
        )
        with acquire_sqlite_writer_session(location) as writer:
            p1 = writer._record_progression_decision(p1_command, source, validation, review)
            assert p1.branch == branch
        with sqlite3.connect(location.database_path) as db:
            terminal_command = _terminal_selector(
                db, p1_command, post_command, continuation.admission_result, p1)
            acceptance_before = db.execute(
                "SELECT * FROM rw0_c2_bootstrap_acceptance_facts ORDER BY acceptance_fact_ref"
            ).fetchall()
            unchanged_tables = (
                "development_program_heads", "development_work_item_heads",
                "development_pre_execution_selection_heads",
                "development_effect_heads", "development_delivery_heads",
                "global_stop_current", "development_decisions",
                "development_program_versions", "development_effect_intents",
            )
            owner_rows_before = {
                table: db.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
                for table in unchanged_tables
            }
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._record_terminal_outcome(
                terminal_command, replace(source, disclosure_permitted=False)
            ) == TerminalConflictV1("protected_posture_unavailable")
            assert writer._record_terminal_outcome(
                terminal_command, replace(source, recording_permitted=False)
            ) == TerminalConflictV1("protected_posture_unavailable")
            terminal = writer._record_terminal_outcome(terminal_command, source)
            assert type(terminal) is TerminalCommittedV1
            assert terminal.outcome == NORMAL_PAIRS[branch]
            assert writer._read_terminal_outcome(terminal_command, source) == terminal
            assert writer._record_terminal_outcome(terminal_command, source) == terminal
            recovery = writer._recover_terminal_outcome(terminal_command, source)
            assert recovery.classification == "committed_exact"
            assert recovery.committed == terminal
            changed_assertion = _changed_assertion(terminal_command)
            assert changed_assertion.command_digest != terminal_command.command_digest
            assert writer._record_terminal_outcome(changed_assertion, source) == TerminalConflictV1("command_reuse")
            for claimed in (False, None):
                disclosure_only = replace(
                    source, recording_permitted=False,
                    acceptance_exhaustively_unclaimed=claimed)
                assert writer._record_terminal_outcome(terminal_command, disclosure_only) == terminal
                assert writer._read_terminal_outcome(terminal_command, disclosure_only) == terminal
                assert writer._recover_terminal_outcome(
                    terminal_command, disclosure_only).classification == "committed_exact"
            denied = replace(source, disclosure_permitted=False)
            with pytest.raises(SQLiteMutationStoreError):
                writer._read_terminal_outcome(terminal_command, denied)
            assert writer._recover_terminal_outcome(
                terminal_command, denied).classification == "unresolved"
            if branch == "candidate_acceptance":
                other = RecordRW0TerminalOutcomeCommandV1.prepare(
                    mutation_ref="terminal.competing.1",
                    p1_command=p1_command, section41_command=post_command,
                    c1_rank15=continuation.admission_result,
                    heads=tuple(terminal_command.to_mapping()["heads"]),
                    stop=terminal_command.to_mapping()["stop"],
                    prior_decision_digest=terminal_command.to_mapping()["reached_owners"][15]["digest"],
                    prior_guarded_result_digest=p1.result_digest,
                    prior_receipt_graph_digest=p1.receipt_graph_digest,
                    expected_branch=branch, expected_outcome="accept")
                assert writer._recover_terminal_outcome(
                    other, source).classification == "definitely_not_committed"
                assert writer._recover_terminal_outcome(
                    other, replace(source, old_execution_excluded=False)
                ).classification == "definitely_not_committed"
                assert writer._record_terminal_outcome(
                    other, source) == TerminalConflictV1("route_collision")
        with sqlite3.connect(location.database_path) as db:
            assert db.execute("PRAGMA foreign_key_check").fetchall() == []
            raw_witness = db.execute(
                "SELECT closure_heads_bytes FROM rw0_terminal_contexts"
            ).fetchone()[0]
            witness = witness_from_bytes(raw_witness)
            assert witness.canonical_bytes == raw_witness
            assert 1 <= len(raw_witness) <= WITNESS_BYTE_CEILING
            assert WITNESS_SCHEMA.encode() in raw_witness
            owner_columns = (
                pr._DEVELOPMENT_PROGRAM_HEAD_COLUMNS,
                pr._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS,
                cr._TABLE_COLUMNS["development_pre_execution_selection_heads"],
                er._DEVELOPMENT_EFFECT_HEAD_COLUMNS,
                er._DEVELOPMENT_DELIVERY_HEAD_COLUMNS,
            )
            for image, table, columns in zip(witness.postimages,
                    unchanged_tables[:5], owner_columns, strict=True):
                actual = db.execute("SELECT " + ", ".join(columns) + " FROM " + table).fetchone()
                assert image == dict(zip(columns, actual, strict=True))
            assert witness.coordinates == tuple(terminal_command.to_mapping()["heads"])
            assert db.execute("SELECT * FROM rw0_c2_bootstrap_acceptance_facts ORDER BY acceptance_fact_ref").fetchall() == acceptance_before
            assert {table: db.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
                    for table in unchanged_tables} == owner_rows_before
            assert [db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                    for table in ("rw0_terminal_contexts", "rw0_terminal_outcomes",
                                  "rw0_terminal_results", "rw0_terminal_receipts")] == [1, 1, 1, 1]
            for table in terminal_rows.TABLES:
                row = db.execute(
                    f"SELECT {', '.join(terminal_rows.COLUMNS[table])} FROM {table}"
                ).fetchone()
                assert terminal_rows.checked_row(table, row).values == row
                if branch == "candidate_acceptance":
                    key = terminal_rows.PRIMARY[table]
                    with pytest.raises(sqlite3.IntegrityError):
                        db.execute(f"UPDATE {table} SET {key}={key}")
                    with pytest.raises(sqlite3.IntegrityError):
                        db.execute(f"DELETE FROM {table}")
            if branch == "attempt_selecting_replan":
                private = p1_command.replan_proposal.work_spec_template.to_mapping()
                terminal_bytes = b"".join(
                    (item.encode("utf-8") if type(item) is str else item)
                    for table in ("rw0_terminal_contexts", "rw0_terminal_outcomes",
                                  "rw0_terminal_results", "rw0_terminal_receipts")
                    for row in db.execute(f"SELECT * FROM {table}")
                    for item in row if type(item) in (bytes, str)
                )
                assert private["objective"].encode("utf-8") not in terminal_bytes
                for field in ("requirements", "exclusions"):
                    for phrase in private[field]:
                        assert phrase.encode("utf-8") not in terminal_bytes
        if branch in ("candidate_acceptance", "attempt_selecting_replan"):
            with sqlite3.connect(location.database_path) as db:
                _advance_program_head(db)
                db.execute("UPDATE global_stop_current SET version=version+1, updated_at='2098-01-01T00:00:00Z'")
            with acquire_sqlite_writer_session(location) as writer:
                assert writer._read_terminal_outcome(terminal_command, source) == terminal
                assert writer._record_terminal_outcome(terminal_command, source) == terminal
                assert writer._recover_terminal_outcome(
                    terminal_command, source).classification == "committed_exact"


def test_resealed_detached_p1_disposition_is_not_terminal_source_evidence(
    tmp_path, monkeypatch,
):
    spec = _golden_spec()
    p0_command, p0_source = _p0_command()
    original_initialize = d1.initialize_database
    def initialize_with_p0(location):
        result = original_initialize(location)
        with acquire_sqlite_writer_session(location) as writer:
            writer._record_scope_admission(p0_command, p0_source)
        return result
    monkeypatch.setattr(d1, "initialize_database", initialize_with_p0)
    with run_rw0_d2_offline(spec, artificial_fixture(spec)) as run:
        assert run.handback.status == "preadmission_ready"
        post_command, _ = prepare_record_command(run)
        continuation = continue_open_rw0_d2_run(run)
        assert continuation.status == "projected"
        assert continuation.projection.recommendation == "accept_candidate"
        location = run._d1_run.location
        basis, continuity, sole, proposal, validation, review = _connected_basis(
            run, continuation.projection, "candidate_repair", "repair")
        assert validation.disposition_digest != run.handback.evidence_checkpoint.validation_disposition.disposition_digest
        with sqlite3.connect(location.database_path) as db:
            columns = pr._DEVELOPMENT_PROGRAM_HEAD_COLUMNS
            head = pr.development_program_head_row_value_from_row_tuple(
                db.execute("SELECT " + ", ".join(columns)
                           + " FROM development_program_heads").fetchone())
        p1_command = _command(basis, head, continuity, sole,
                              expected_branch="candidate_repair", proposal=proposal)
        source = ArtificialDecisionGuardSourceV1(
            _canonical(continuity), _canonical(sole),
            "2020-01-01T00:00:00Z", "2099-01-01T00:00:00Z",
            True, True, True, True, True, True, True)
        with acquire_sqlite_writer_session(location) as writer:
            p1 = writer._record_progression_decision(
                p1_command, source, validation, review)
            assert p1.branch == "candidate_repair"
        with sqlite3.connect(location.database_path) as db:
            terminal_command = _terminal_selector(
                db, p1_command, post_command, continuation.admission_result, p1)
        with acquire_sqlite_writer_session(location) as writer:
            with pytest.raises(SQLiteMutationStoreError):
                writer._record_terminal_outcome(terminal_command, source)
        with sqlite3.connect(location.database_path) as db:
            assert [db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                    for table in ("rw0_terminal_contexts", "rw0_terminal_outcomes",
                                  "rw0_terminal_results", "rw0_terminal_receipts")] == [0, 0, 0, 0]
