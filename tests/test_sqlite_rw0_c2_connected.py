"""Disposable connected D1/D2, Section 41/C1, P0, and five P1 branches."""
from __future__ import annotations

from copy import deepcopy
import sqlite3

import pytest

from ge_nwp_coordinator import _development_program_row_values as pr
from ge_nwp_coordinator import _rw0_d1_offline as d1
from ge_nwp_coordinator._rw0_c2_progression_contracts import (
    ArtificialDecisionGuardSourceV1, ProgressionDecisionCommittedV1,
    _canonical, _self_digest,
)
from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture
from ge_nwp_coordinator._rw0_d2_offline import run_rw0_d2_offline
from ge_nwp_coordinator._rw0_d2_post_execution_continuation import continue_open_rw0_d2_run
from ge_nwp_coordinator._worker_execution_semantic_values import WorkSpecV1
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_post_execution_pure_owner_values import _seal, CLASS_BY_V
from test_rw0_d1_offline_integration import work_spec
from test_rw0_c2_progression_contracts import _basis, _replan_proposal, _validation_for
from test_rw0_c2_progression_plan import _command, _history
from test_sqlite_rw0_c2_scope_admission import _command as _p0_command
from test_sqlite_rw0_c2_progression import BRANCH_CLASS, STAMP


def _golden_spec() -> WorkSpecV1:
    fields = work_spec().to_mapping()
    fields.update(
        work_spec_ref="work-spec-golden.0001",
        program_ref="program-golden.0001",
        program_version_ref="program-version-golden.0001",
        accepted_intent_revision_ref="accepted-intent-golden.0001",
        work_item_ref="work-item-golden.0001",
        work_item_revision_ref="work-item-revision-golden.0001",
    )
    fields.pop("work_spec_digest")
    return WorkSpecV1.create(**{key: value for key, value in fields.items()
                                 if key not in ("schema_id", "base_git_object_format",
                                                "privacy_classification")})


def _connected_basis(run, projection, branch: str, normal: str):
    checkpoint = run.handback.evidence_checkpoint
    assert checkpoint is not None
    actual_validation = checkpoint.validation_disposition.to_mapping()
    actual_review = checkpoint.review_disposition.to_mapping()
    basis = deepcopy(_basis())
    snapshot = basis["decision_current_snapshot"]
    for name in ("program_ref", "program_version_ref", "accepted_intent_revision_ref",
                 "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
                 "candidate_ref", "attempt_fence_ref", "attempt_fence_digest"):
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
        for field in ("program_ref", "program_version_ref",
                      "accepted_intent_revision_ref", "work_item_revision_ref",
                      "semantic_attempt_ref", "candidate_ref"):
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
    model.update(proposal_ref=projection.proposal_ref,
                 proposal_digest=projection.proposal_digest,
                 snapshot_ref=snapshot["snapshot_ref"],
                 snapshot_digest=snapshot["snapshot_digest"],
                 proposal_currentness_ref=currentness["currentness_ref"],
                 proposal_currentness_digest=currentness["currentness_digest"],
                 model_recommendation=projection.recommendation,
                 mapped_branch="candidate_acceptance",
                 authoritative_branch=branch, evaluated_at=STAMP)
    model["result"] = "consistent" if branch == "candidate_acceptance" else "inconsistent"
    model["reason"] = ("mapped_branch_equals_authoritative_branch" if branch == "candidate_acceptance"
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
    if normal == "accept":
        validation = checkpoint.validation_disposition
    else:
        alternate = _validation_for(normal).to_mapping()
        for name in ("source_outcome", "source_reason_code", "result",
                     "repairability", "reason", "validation_result_set_ref",
                     "validation_result_set_digest"):
            actual_validation[name] = alternate[name]
        validation = CLASS_BY_V["V14"].from_mapping(_seal("V14", actual_validation))
    basis["validation_disposition"] = validation.to_mapping()
    basis["independent_review_disposition"] = checkpoint.review_disposition.to_mapping()
    basis["basis_digest"] = _self_digest(basis, "basis_digest")
    return basis, continuity, sole, proposal, validation, checkpoint.review_disposition


@pytest.mark.parametrize("branch,normal", BRANCH_CLASS)
def test_connected_actual_offline_owner_state_reaches_p1(tmp_path, monkeypatch, branch, normal):
    spec = _golden_spec()
    p0_command, p0_source = _p0_command()
    reached = []
    original_initialize = d1.initialize_database
    def initialize_with_prior_p0(location):
        result = original_initialize(location)
        with acquire_sqlite_writer_session(location) as writer:
            p0 = writer._record_scope_admission(p0_command, p0_source)
            assert writer._read_scope_admission(p0_command, p0_source) == p0
        reached.append(location.database_path)
        return result
    monkeypatch.setattr(d1, "initialize_database", initialize_with_prior_p0)
    with run_rw0_d2_offline(spec, artificial_fixture(spec)) as run:
        assert reached == [run._d1_run.location.database_path]
        assert run.handback.status == "preadmission_ready"
        continuation = continue_open_rw0_d2_run(run)
        assert continuation.status == "projected"
        assert continuation.projection is not None
        assert continuation.admission_result is not None
        assert continuation.projection.proposal_ref == "proposal.d2.post-review"
        location = run._d1_run.location
        with acquire_sqlite_writer_session(location) as writer:
            assert writer._recover_scope_admission(
                p0_command, p0_source).classification == "committed_exact"
        basis, continuity, sole, proposal, validation, review = _connected_basis(
            run, continuation.projection, branch, normal)
        with sqlite3.connect(location.database_path) as connection:
            columns = pr._DEVELOPMENT_PROGRAM_HEAD_COLUMNS
            head = pr.development_program_head_row_value_from_row_tuple(
                connection.execute("SELECT " + ", ".join(columns)
                                   + " FROM development_program_heads").fetchone())
        command = _command(basis, head, continuity, sole,
                           expected_branch=branch, proposal=proposal)
        source = ArtificialDecisionGuardSourceV1(
            _canonical(continuity), _canonical(sole),
            "2020-01-01T00:00:00Z", "2099-01-01T00:00:00Z",
            True, True, True, True, True, True, True,
        )
        with acquire_sqlite_writer_session(location) as writer:
            committed = writer._record_progression_decision(
                command, source, validation, review)
            assert type(committed) is ProgressionDecisionCommittedV1
            assert committed.branch == branch
            assert committed.command_digest == command.command_digest
            assert writer._read_progression_decision(command, source) == committed
            assert writer._recover_progression_decision(
                command, source).classification == "committed_exact"
        with sqlite3.connect(location.database_path) as connection:
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
