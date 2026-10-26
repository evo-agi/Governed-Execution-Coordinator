"""Artificial P1 physical family through the fenced private writer session."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import sqlite3
from unittest.mock import patch

import pytest

import ge_nwp_coordinator._sqlite_rw0_c2_progression as p1
from ge_nwp_coordinator import _development_program_row_values as pr
from ge_nwp_coordinator import _development_effect_row_values as er
from ge_nwp_coordinator._rw0_c2_progression_contracts import (
    ArtificialDecisionGuardSourceV1, ProgressionDecisionCommittedV1,
    ProgressionDecisionRecoveryV1, DecisionBasisV2, _canonical, _self_digest,
    derive_replan_durable_refs, derive_successor_selection_refs,
    derive_candidate_evidence_reason, RecordProgressionDecisionCommandV1,
)
from ge_nwp_coordinator._rw0_c2_progression_plan import _row
from ge_nwp_coordinator._rw0_c2_progression_rows import _P1Row, _TABLE_FIELDS
from ge_nwp_coordinator._development_author_effect_establishment_contracts import (
    _attempt_fence_parameters,
)
from ge_nwp_coordinator._worker_execution_semantic_values import AttemptFenceV1
from ge_nwp_coordinator import sqlite_transition_transaction as txn
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from test_c2b3d_private_atomic_author_effect_establishment import make_author_effect_fixture
from test_sqlite_rw0_c2_scope_admission import _command as _p0_command
from test_rw0_c2_progression_contracts import _basis, _replan_proposal, _validation_for
from test_rw0_c2_progression_plan import _command, _history
from test_post_execution_pure_owner_values import _sample, _seal, CLASS_BY_V

STAMP = "2029-01-01T00:00:00Z"
BRANCH_CLASS = (
    ("candidate_acceptance", "accept"),
    ("candidate_repair", "repair"),
    ("attempt_selecting_replan", "replan"),
    ("program_terminal_reject", "terminal"),
    ("post_execution_program_block", "nonconclusive"),
)


def _case(tmp_path, branch: str, normal: str, *, block_mode: str | None = None):
    fixture = make_author_effect_fixture(tmp_path, suffix="golden.0001")
    fixture.writer._establish_development_author_effect_intent(**fixture.ingress)
    p0_command, p0_source = _p0_command()
    fixture.writer._record_scope_admission(p0_command, p0_source)
    basis = deepcopy(_basis())
    snapshot = basis["decision_current_snapshot"]
    snapshot["attempt_fence_digest"] = fixture.ingress["attempt_fence"].attempt_fence_digest
    snapshot["captured_at"] = STAMP
    snapshot = _seal("V27", snapshot)
    basis["decision_current_snapshot"] = snapshot
    currentness = basis["proposal_evidence_currentness"]
    for component in currentness["components"]:
        component["evaluated_at"] = STAMP
        component["source_expires_at"] = "2099-01-01T00:00:00Z"
    currentness["evaluated_at"] = STAMP
    currentness["snapshot_ref"] = snapshot["snapshot_ref"]
    currentness["snapshot_digest"] = snapshot["snapshot_digest"]
    if block_mode == "stale":
        component = currentness["components"][0]
        component["source_expires_at"] = STAMP
        component["result"] = "stale"
        component["reason"] = "exact_source_expired_at_evaluation"
        currentness["result"] = "stale"
        currentness["reason"] = "component_source_stale"
    basis["proposal_evidence_currentness"] = _seal("V29", currentness)
    if block_mode == "productive":
        matrix = basis["standing_policy_branch_matrix"]
        entry = next(item for item in matrix["entries"]
                     if item["branch"] == "candidate_acceptance")
        entry["result"] = "deny"
        entry["reason"] = "branch_not_allowed"
        basis["standing_policy_branch_matrix"] = _seal("V17", matrix)
    for key, version in (
        ("decision_time_authority_branch_matrix", "V31"),
        ("decision_time_global_stop_branch_matrix", "V32"),
        ("decision_time_source_effect_ceiling_branch_matrix", "V33"),
    ):
        matrix = basis[key]
        matrix["snapshot_ref"] = snapshot["snapshot_ref"]
        matrix["snapshot_digest"] = snapshot["snapshot_digest"]
        matrix["evaluated_at"] = STAMP
        basis[key] = _seal(version, matrix)
    model = basis["recommendation_consistency_evaluation"]
    model["snapshot_ref"] = snapshot["snapshot_ref"]
    model["snapshot_digest"] = snapshot["snapshot_digest"]
    model["proposal_currentness_ref"] = basis["proposal_evidence_currentness"]["currentness_ref"]
    model["proposal_currentness_digest"] = basis["proposal_evidence_currentness"]["currentness_digest"]
    model["authoritative_branch"] = branch
    model["evaluated_at"] = STAMP
    if branch != "candidate_acceptance":
        model["result"] = "inconsistent"
        model["reason"] = "mapped_branch_differs_from_authoritative_branch"
    basis["recommendation_consistency_evaluation"] = _seal("V34", model)
    proposal = _replan_proposal(basis) if branch == "attempt_selecting_replan" else None
    if proposal is not None:
        basis["replan_proposal_safe_projection"] = proposal.safe_projection()
    continuity = _history(basis, False)
    sole = _history(basis, True)
    basis["bootstrap_guard_evidence"]["guard_digest"] = _self_digest(
        basis["bootstrap_guard_evidence"], "guard_digest")
    basis["captured_at"] = STAMP
    validation_map = _validation_for(normal).to_mapping()
    review_map = _sample("V15")
    for value, version in ((validation_map, "V14"), (review_map, "V15")):
        value["attempt_fence_digest"] = snapshot["attempt_fence_digest"]
        _seal(version, value)
    validation = CLASS_BY_V["V14"].from_mapping(validation_map)
    review = CLASS_BY_V["V15"].from_mapping(review_map)
    basis["validation_disposition"] = validation.to_mapping()
    basis["independent_review_disposition"] = review.to_mapping()
    basis["basis_digest"] = _self_digest(basis, "basis_digest")
    with sqlite3.connect(fixture.location.database_path) as database:
        columns = pr._DEVELOPMENT_PROGRAM_HEAD_COLUMNS
        observed = database.execute(
            "SELECT " + ", ".join(columns) + " FROM development_program_heads"
        ).fetchone()
    head = pr.development_program_head_row_value_from_row_tuple(observed)
    command = _command(basis, head, continuity, sole,
                       expected_branch=branch, proposal=proposal)
    source = ArtificialDecisionGuardSourceV1(
        _canonical(continuity), _canonical(sole),
        "2020-01-01T00:00:00Z", "2099-01-01T00:00:00Z",
        True, True, True, True, True, True, True,
    )
    return fixture, command, source, validation, review, head


def _counts(location):
    with sqlite3.connect(location.database_path) as database:
        return {table: database.execute("SELECT count(*) FROM " + table).fetchone()[0]
                for table in (
                    "rw0_c2_guarded_family_relations",
                    "rw0_c2_guarded_progression_results",
                    "rw0_c2_bootstrap_acceptance_facts",
                    "development_program_versions",
                    "development_work_item_revisions",
                    "development_mutation_receipts",
                )}


def _durable_snapshot(location):
    """Capture every user table, including receipts and both mutable heads."""
    with sqlite3.connect(location.database_path) as database:
        tables = tuple(row[0] for row in database.execute(
            "SELECT name FROM sqlite_schema WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"))
        return {table: tuple(database.execute(f'SELECT * FROM "{table}"'))
                for table in tables}


@pytest.mark.parametrize("branch,normal", BRANCH_CLASS)
def test_five_physical_branches_commit_replay_read_and_recover(tmp_path, branch, normal):
    fixture, command, source, validation, review, old_head = _case(tmp_path, branch, normal)
    try:
        committed = fixture.writer._record_progression_decision(
            command, source, validation, review)
        assert type(committed) is ProgressionDecisionCommittedV1
        assert committed.branch == branch
        assert fixture.writer._record_progression_decision(
            command, source, validation, review) == committed
        assert fixture.writer._read_progression_decision(command, source) == committed
        recovery = fixture.writer._recover_progression_decision(command, source)
        assert type(recovery) is ProgressionDecisionRecoveryV1
        assert recovery.classification == "committed_exact"
        assert recovery.committed == committed
        counts = _counts(fixture.location)
        assert counts["rw0_c2_guarded_family_relations"] == 1
        assert counts["rw0_c2_guarded_progression_results"] == 1
        assert counts["rw0_c2_bootstrap_acceptance_facts"] == (branch == "candidate_acceptance")
        assert counts["development_program_versions"] == 2
        assert counts["development_mutation_receipts"] == 3
        assert counts["development_work_item_revisions"] == (2 if branch == "attempt_selecting_replan" else 1)
    finally:
        fixture.writer.close()


@pytest.mark.parametrize("normal,candidate_reason", (
    ("accept", "candidate_evidence_conclusively_accepted"),
    ("repair", "candidate_evidence_requires_repair"),
    ("replan", "candidate_evidence_requires_replan"),
    ("terminal", "candidate_evidence_terminally_rejected"),
    ("nonconclusive", "candidate_evidence_nonconclusive"),
))
def test_stale_basis_v2_block_preserves_distinct_candidate_reason_and_exact_family(
    tmp_path, normal, candidate_reason,
):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "post_execution_program_block", normal, block_mode="stale")
    try:
        embedded_validation, embedded_review = command.basis.typed_dispositions()
        assert derive_candidate_evidence_reason(
            embedded_validation, embedded_review) == candidate_reason
        with patch.object(txn, "_capture_transaction_timestamp", lambda: STAMP):
            fresh = fixture.writer._record_progression_decision(
                command, source, validation, review)
        assert type(fresh) is ProgressionDecisionCommittedV1
        assert fresh.branch == "post_execution_program_block"
        with sqlite3.connect(fixture.location.database_path) as database:
            assert database.execute(
                "SELECT reason_code FROM development_decisions WHERE decision_ref = ?",
                (fresh.decision_ref,)).fetchone() == ("decision_basis_not_current",)
            persisted_basis = database.execute(
                "SELECT basis_bytes FROM rw0_c2_decision_bases WHERE basis_ref = ?",
                (command.basis.to_mapping()["basis_ref"],)).fetchone()[0]
        assert DecisionBasisV2.from_json(persisted_basis).canonical_bytes == command.basis.canonical_bytes
        after_fresh = _durable_snapshot(fixture.location)
        assert fixture.writer._record_progression_decision(
            command, source, validation, review) == fresh
        assert fixture.writer._read_progression_decision(command, source) == fresh
        recovery = fixture.writer._recover_progression_decision(command, source)
        assert recovery.classification == "committed_exact"
        assert recovery.committed == fresh
        assert _durable_snapshot(fixture.location) == after_fresh
    finally:
        fixture.writer.close()


def test_basis_v2_disposition_variants_change_command_identity_under_shared_coordinates(
    tmp_path,
):
    observed = []
    for normal in ("accept", "repair", "replan", "terminal", "nonconclusive"):
        fixture, command, _source, _validation, _review, _ = _case(
            tmp_path / normal, "post_execution_program_block", normal,
            block_mode="stale")
        try:
            snapshot = command.basis.to_mapping()["decision_current_snapshot"]
            observed.append((snapshot["external_sources"], command.basis.digest,
                             command.command_digest,
                             command.relation.to_mapping()["preassigned_version_ref"]))
        finally:
            fixture.writer.close()
    assert all(item[0] == observed[0][0] for item in observed)
    for index in (1, 2, 3):
        assert len({item[index] for item in observed}) == 5


@pytest.mark.parametrize("block_mode,normal,final_reason,candidate_reason", (
    ("productive", "accept", "productive_branch_not_permitted",
     "candidate_evidence_conclusively_accepted"),
    (None, "nonconclusive", "candidate_evidence_nonconclusive",
     "candidate_evidence_nonconclusive"),
))
def test_other_block_reasons_replay_from_basis_v2(
    tmp_path, block_mode, normal, final_reason, candidate_reason,
):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "post_execution_program_block", normal, block_mode=block_mode)
    try:
        assert derive_candidate_evidence_reason(
            *command.basis.typed_dispositions()) == candidate_reason
        with patch.object(txn, "_capture_transaction_timestamp", lambda: STAMP):
            fresh = fixture.writer._record_progression_decision(
                command, source, validation, review)
        assert fresh.branch == "post_execution_program_block"
        with sqlite3.connect(fixture.location.database_path) as database:
            assert database.execute(
                "SELECT reason_code FROM development_decisions WHERE decision_ref = ?",
                (fresh.decision_ref,)).fetchone() == (final_reason,)
        after_fresh = _durable_snapshot(fixture.location)
        assert fixture.writer._record_progression_decision(
            command, source, validation, review) == fresh
        assert fixture.writer._read_progression_decision(command, source) == fresh
        recovery = fixture.writer._recover_progression_decision(command, source)
        assert recovery.classification == "committed_exact"
        assert recovery.committed == fresh
        assert _durable_snapshot(fixture.location) == after_fresh
    finally:
        fixture.writer.close()


def test_detached_disposition_is_rejected_before_p1_route_probe(tmp_path, monkeypatch):
    fixture, command, source, _validation, review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    before = _durable_snapshot(fixture.location)
    reached = []
    def forbidden_probe(*args, **kwargs):
        reached.append(True)
        raise AssertionError("detached evidence reached route probe")
    try:
        monkeypatch.setattr(p1, "_route_occupied", forbidden_probe)
        conflict = fixture.writer._record_progression_decision(
            command, source, _validation_for("repair"), review)
        assert conflict.reason_code == "basis_identity_lineage_profile_provenance_conflict"
        assert reached == []
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


@pytest.mark.parametrize("field", (
    "validation_disposition", "independent_review_disposition",
))
def test_persisted_basis_disposition_tamper_without_basis_reseal_is_not_replay(
    tmp_path, monkeypatch, field,
):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    try:
        fixture.writer._record_progression_decision(command, source, validation, review)
        before = _durable_snapshot(fixture.location)
        changed = command.basis.to_mapping()
        if field == "validation_disposition":
            alternate = _validation_for("repair").to_mapping()
            alternate["attempt_fence_digest"] = changed[
                "decision_current_snapshot"]["attempt_fence_digest"]
            changed[field] = _seal("V14", alternate)
        else:
            alternate = changed[field]
            alternate["expires_at"] = "2099-01-02T00:00:00Z"
            changed[field] = _seal("V15", alternate)
        assert changed["basis_digest"] == command.basis.digest
        with pytest.raises(ValueError):
            DecisionBasisV2.from_json(_canonical(changed))
        original = p1._one
        def tampered(capability, table, where, parameters):
            row = original(capability, table, where, parameters)
            if table == p1._BASIS:
                assert type(row) is _P1Row
                mapping = row.mapping
                mapping["basis_bytes"] = _canonical(changed)
                return _P1Row(table, tuple(mapping[name] for name in _TABLE_FIELDS[table]))
            return row
        with monkeypatch.context() as patch:
            patch.setattr(p1, "_one", tampered)
            with pytest.raises(SQLiteMutationStoreError):
                fixture.writer._read_progression_decision(command, source)
            assert fixture.writer._recover_progression_decision(
                command, source).classification == "unresolved"
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


def test_foreign_resealed_basis_disposition_on_occupied_route_conflicts(tmp_path):
    fixture, command, source, validation, review, head = _case(
        tmp_path, "candidate_acceptance", "accept")
    try:
        committed = fixture.writer._record_progression_decision(
            command, source, validation, review)
        changed = command.basis.to_mapping()
        alternate = _validation_for("repair").to_mapping()
        alternate["attempt_fence_digest"] = changed[
            "decision_current_snapshot"]["attempt_fence_digest"]
        changed["validation_disposition"] = _seal("V14", alternate)
        changed["basis_digest"] = _self_digest(changed, "basis_digest")
        assert DecisionBasisV2.from_mapping(changed).digest != command.basis.digest
        continuity = _history(changed, False)
        sole = _history(changed, True)
        changed["bootstrap_guard_evidence"]["guard_digest"] = _self_digest(
            changed["bootstrap_guard_evidence"], "guard_digest")
        changed["basis_digest"] = _self_digest(changed, "basis_digest")
        foreign = _command(changed, head, continuity, sole,
                           mutation_ref=command.relation.to_mapping()["mutation_ref"])
        before = _durable_snapshot(fixture.location)
        conflict = fixture.writer._record_progression_decision(
            foreign, source,
            CLASS_BY_V["V14"].from_mapping(changed["validation_disposition"]),
            review)
        assert conflict.reason_code == "mutation_ref_reuse_conflict"
        assert fixture.writer._read_progression_decision(command, source) == committed
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


def test_invalid_expected_branch_cannot_enter_private_writer(tmp_path):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    class EqualBranch(str):
        def __eq__(self, other):
            raise AssertionError("subclass equality must not run")
    forged = object.__new__(RecordProgressionDecisionCommandV1)
    for name in ("relation", "basis", "replan_proposal"):
        object.__setattr__(forged, name, getattr(command, name))
    object.__setattr__(forged, "expected_branch", EqualBranch("foreign"))
    before = _durable_snapshot(fixture.location)
    try:
        with pytest.raises(SQLiteMutationStoreError):
            fixture.writer._record_progression_decision(
                forged, source, validation, review)
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


@pytest.mark.parametrize("fault", ("work_cas_noop", "work_readback_mismatch"))
def test_replan_work_head_faults_roll_back_every_target_row(tmp_path, monkeypatch, fault):
    fixture, command, source, validation, review, old_head = _case(
        tmp_path, "attempt_selecting_replan", "replan")
    before = _counts(fixture.location)
    reached: list[str] = []
    original_cas = p1._cas_head
    original_one = p1._one
    def cas(connection, table, before_row, after_row):
        if table == "development_work_item_heads":
            reached.append("work_cas")
            if fault == "work_cas_noop":
                return None
        return original_cas(connection, table, before_row, after_row)
    def one(capability, table, where, parameters):
        if (fault == "work_readback_mismatch" and "work_cas" in reached
            and table == "development_work_item_heads"):
            reached.append("work_readback")
            return None
        return original_one(capability, table, where, parameters)
    monkeypatch.setattr(p1, "_cas_head", cas)
    monkeypatch.setattr(p1, "_one", one)
    try:
        with pytest.raises(SQLiteMutationStoreError):
            fixture.writer._record_progression_decision(
                command, source, validation, review)
        assert "work_cas" in reached
        if fault == "work_readback_mismatch":
            assert "work_readback" in reached
        assert _counts(fixture.location) == before
        with sqlite3.connect(fixture.location.database_path) as database:
            current = database.execute(
                "SELECT head_digest FROM development_program_heads"
            ).fetchone()[0]
            assert current == old_head.head_digest
    finally:
        fixture.writer.close()


def test_second_replan_preserves_first_historical_work_head_replay(tmp_path):
    fixture, first_command, first_source, first_validation, first_review, _ = _case(
        tmp_path, "attempt_selecting_replan", "replan")
    try:
        with patch.object(txn, "_capture_transaction_timestamp", lambda: STAMP):
            first = fixture.writer._record_progression_decision(
                first_command, first_source, first_validation, first_review)
        original = first_command.relation.to_mapping()
        snapshot = first_command.basis.to_mapping()["decision_current_snapshot"]
        proposal = first_command.replan_proposal
        assert proposal is not None
        intent_ref, work_revision_ref, work_spec_ref = derive_replan_durable_refs(
            command_digest=first_command.command_digest,
            program_ref=original["program_ref"],
            current_program_version_ref=snapshot["program_version_ref"],
            current_accepted_intent_revision_ref=snapshot["accepted_intent_revision_ref"],
            work_item_ref=snapshot["work_item_ref"],
            current_work_item_revision_ref=snapshot["work_item_revision_ref"],
            source_intent_ref=proposal.source_intent_ref,
            source_intent_digest=proposal.source_intent_digest,
            work_spec_template_digest=proposal.work_spec_template.digest,
            preassigned_version_ref=original["preassigned_version_ref"],
        )
        next_attempt, next_candidate = derive_successor_selection_refs(
            command_digest=first_command.command_digest,
            program_ref=original["program_ref"],
            selected_attempt_ref=snapshot["semantic_attempt_ref"],
            selected_candidate_ref=snapshot["candidate_ref"],
            branch="attempt_selecting_replan",
        )
        old_fence = fixture.ingress["attempt_fence"]
        new_fence = AttemptFenceV1.create(
            attempt_fence_ref="attempt-fence-second",
            parent_standing_grant_ref=old_fence.parent_standing_grant_ref,
            parent_standing_grant_digest=old_fence.parent_standing_grant_digest,
            attempt_authorization_ref="attempt-authorization-second",
            attempt_authorization_digest="8" * 64,
            program_ref=original["program_ref"],
            program_version_ref=original["preassigned_version_ref"],
            accepted_intent_revision_ref=intent_ref,
            work_item_ref=snapshot["work_item_ref"],
            work_item_revision_ref=work_revision_ref,
            semantic_attempt_ref=next_attempt,
            repository_ref=proposal.work_spec_template.to_mapping()["repository_ref"],
            base_git_oid=proposal.work_spec_template.to_mapping()["base_git_oid"],
            path_ceiling=list(old_fence.path_ceiling),
            allowed_effect_classes=list(old_fence.allowed_effect_classes),
            aggregate_ceilings=old_fence.aggregate_ceilings,
            expires_at="2099-01-01T00:00:00Z",
            global_stop_ref="global-stop-clear", global_stop_version=0,
        )
        second_attempt = _row(table="development_semantic_attempts", fields={
            "schema_id": pr._DEVELOPMENT_SEMANTIC_ATTEMPT_SCHEMA,
            "semantic_attempt_ref": next_attempt,
            "program_ref": original["program_ref"],
            "program_version_ref": original["preassigned_version_ref"],
            "accepted_intent_revision_ref": intent_ref,
            "work_item_ref": snapshot["work_item_ref"],
            "work_item_revision_ref": work_revision_ref,
            "attempt_number": 2, "candidate_ref": next_candidate,
            "attempt_phase": "established", "selection_decision_ref": first.decision_ref,
            "created_at": "2029-01-01T00:00:01Z",
        }, columns=pr._DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS,
            digest_field="semantic_attempt_digest",
            adapter=pr.development_semantic_attempt_row_value_from_row_tuple)
        second_fence = er.development_attempt_fence_row_value_from_row_tuple(
            _attempt_fence_parameters(new_fence, "2029-01-01T00:00:01Z"))
        # The existing author-effect entry admits only generation-1 attempt one.
        # This task-owned test fixture inserts exactly two typed 0002 preimages;
        # it is no product provisioner and performs no P1 family mutation.
        with sqlite3.connect(fixture.location.database_path) as database:
            database.execute("PRAGMA foreign_keys=ON")
            for table, row, columns in (
                ("development_semantic_attempts", second_attempt,
                 pr._DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS),
                ("development_attempt_fences", second_fence,
                 er._DEVELOPMENT_ATTEMPT_FENCE_COLUMNS),
            ):
                database.execute(
                    "INSERT INTO " + table + " (" + ", ".join(columns) + ") VALUES ("
                    + ", ".join("?" for _ in columns) + ")",
                    tuple(getattr(row, column) for column in columns),
                )
            assert database.execute("PRAGMA foreign_key_check").fetchall() == []
        basis = first_command.basis.to_mapping()
        basis["basis_ref"] = "basis-B"
        current = basis["decision_current_snapshot"]
        current.update(
            program_version_ref=original["preassigned_version_ref"],
            accepted_intent_revision_ref=intent_ref,
            work_item_revision_ref=work_revision_ref,
            semantic_attempt_ref=next_attempt, candidate_ref=next_candidate,
            attempt_fence_ref=new_fence.attempt_fence_ref,
            attempt_fence_digest=new_fence.attempt_fence_digest,
            captured_at="2029-01-01T00:00:02Z",
        )
        current = _seal("V27", current)
        basis["decision_current_snapshot"] = current
        for key, version in (
            ("proposal_evidence_currentness", "V29"),
            ("decision_time_authority_branch_matrix", "V31"),
            ("decision_time_global_stop_branch_matrix", "V32"),
            ("decision_time_source_effect_ceiling_branch_matrix", "V33"),
        ):
            value = basis[key]
            value["snapshot_ref"] = current["snapshot_ref"]
            value["snapshot_digest"] = current["snapshot_digest"]
            value["evaluated_at"] = "2029-01-01T00:00:02Z"
            basis[key] = _seal(version, value)
        model = basis["recommendation_consistency_evaluation"]
        model["snapshot_ref"] = current["snapshot_ref"]
        model["snapshot_digest"] = current["snapshot_digest"]
        model["proposal_currentness_ref"] = basis["proposal_evidence_currentness"]["currentness_ref"]
        model["proposal_currentness_digest"] = basis["proposal_evidence_currentness"]["currentness_digest"]
        model["evaluated_at"] = "2029-01-01T00:00:02Z"
        basis["recommendation_consistency_evaluation"] = _seal("V34", model)
        second_proposal = _replan_proposal(basis)
        basis["replan_proposal_safe_projection"] = second_proposal.safe_projection()
        continuity = _history(basis, False, suffix="B")
        sole = _history(basis, True, suffix="B")
        basis["bootstrap_guard_evidence"]["guard_digest"] = _self_digest(
            basis["bootstrap_guard_evidence"], "guard_digest")
        basis["captured_at"] = "2029-01-01T00:00:02Z"
        validation = _validation_for("replan").to_mapping()
        review = CLASS_BY_V["V15"].from_mapping(_sample("V15")).to_mapping()
        for value, version in ((validation, "V14"), (review, "V15")):
            value.update(
                program_version_ref=original["preassigned_version_ref"],
                accepted_intent_revision_ref=intent_ref,
                work_item_revision_ref=work_revision_ref,
                semantic_attempt_ref=next_attempt,
                candidate_ref=next_candidate,
                attempt_fence_ref=new_fence.attempt_fence_ref,
                attempt_fence_digest=new_fence.attempt_fence_digest,
                semantic_attempt_digest="0" * 64,
            )
            _seal(version, value)
        basis["validation_disposition"] = validation
        basis["independent_review_disposition"] = review
        basis["basis_digest"] = _self_digest(basis, "basis_digest")
        DecisionBasisV2.from_mapping(basis)
        with sqlite3.connect(fixture.location.database_path) as database:
            columns = pr._DEVELOPMENT_PROGRAM_HEAD_COLUMNS
            head = pr.development_program_head_row_value_from_row_tuple(
                database.execute("SELECT " + ", ".join(columns)
                                 + " FROM development_program_heads").fetchone())
        second_command = _command(
            basis, head, continuity, sole,
            expected_branch="attempt_selecting_replan",
            proposal=second_proposal, mutation_ref="p1-mutation-B",
        )
        second_source = ArtificialDecisionGuardSourceV1(
            _canonical(continuity), _canonical(sole),
            "2020-01-01T00:00:00Z", "2099-01-01T00:00:00Z",
            True, True, True, True, True, True, True,
        )
        with patch.object(txn, "_capture_transaction_timestamp",
                          lambda: "2029-01-01T00:00:02Z"):
            second = fixture.writer._record_progression_decision(
                second_command, second_source,
                CLASS_BY_V["V14"].from_mapping(validation),
                CLASS_BY_V["V15"].from_mapping(review),
            )
        assert second.branch == "attempt_selecting_replan"
        assert second.decision_ref != first.decision_ref
        assert fixture.writer._read_progression_decision(first_command, first_source) == first
        assert fixture.writer._recover_progression_decision(
            first_command, first_source).classification == "committed_exact"
        with sqlite3.connect(fixture.location.database_path) as database:
            assert database.execute(
                "SELECT count(*) FROM rw0_c2_guarded_family_relations"
            ).fetchone()[0] == 2
            assert database.execute(
                "SELECT head_revision FROM development_work_item_heads"
            ).fetchone()[0] == 2
    finally:
        fixture.writer.close()


@pytest.mark.parametrize("field,value", (
    ("historical_work_head_ref", None),
    ("historical_work_head_revision", None),
    ("historical_work_head_digest", None),
    ("historical_work_head_postimage", None),
    ("historical_work_head_ref", "foreign-work"),
    ("historical_work_head_revision", 999),
    ("historical_work_head_digest", "0" * 64),
    ("historical_work_head_postimage", b"{bad"),
))
def test_replan_relation_readback_mutant_rolls_back(tmp_path, monkeypatch, field, value):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "attempt_selecting_replan", "replan")
    before = _counts(fixture.location)
    original = p1._one
    reached = []
    def mutant(capability, table, where, parameters):
        row = original(capability, table, where, parameters)
        if table == p1._RELATION:
            reached.append(field)
            assert type(row) is _P1Row
            altered = row.mapping
            altered[field] = value
            return _P1Row(table, tuple(altered[name] for name in _TABLE_FIELDS[table]))
        return row
    try:
        with monkeypatch.context() as patch:
            patch.setattr(p1, "_one", mutant)
            with pytest.raises(SQLiteMutationStoreError):
                fixture.writer._record_progression_decision(
                    command, source, validation, review)
        assert reached == [field]
        assert _counts(fixture.location) == before
        assert fixture.writer._recover_progression_decision(
            command, source).classification == "definitely_not_committed"
    finally:
        fixture.writer.close()


def test_p0_complete_with_p1_absent_is_truthful(tmp_path):
    fixture, command, source, _validation, _review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    try:
        p0_command, p0_source = _p0_command()
        assert fixture.writer._read_scope_admission(p0_command, p0_source)
        assert fixture.writer._recover_progression_decision(
            command, source).classification == "definitely_not_committed"
        assert _counts(fixture.location)["rw0_c2_guarded_family_relations"] == 0
    finally:
        fixture.writer.close()


@pytest.mark.parametrize("phase,expected", (
    ("before", "definitely_not_committed"),
    ("after", "committed_exact"),
))
def test_p1_commit_response_loss_has_three_way_readback(tmp_path, monkeypatch, phase, expected):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    original = txn._ControllerConnectionScope.commit
    reached = []
    def lost_response(self):
        reached.append(phase)
        if phase == "after":
            original(self)
        raise RuntimeError("synthetic P1 commit response loss")
    try:
        with monkeypatch.context() as patch:
            patch.setattr(txn._ControllerConnectionScope, "commit", lost_response)
            with pytest.raises(SQLiteMutationStoreError) as failure:
                fixture.writer._record_progression_decision(
                    command, source, validation, review)
        assert reached == [phase]
        assert failure.value.error_class == "commit_outcome_unknown"
        fixture.writer.close()
        with acquire_sqlite_writer_session(fixture.location) as writer:
            assert writer._recover_progression_decision(
                command, source).classification == expected
    finally:
        fixture.writer.close()


def test_p1_same_mutation_ref_different_digest_is_no_write(tmp_path):
    fixture, command, source, validation, review, head = _case(
        tmp_path, "candidate_acceptance", "accept")
    try:
        committed = fixture.writer._record_progression_decision(
            command, source, validation, review)
        changed = command.basis.to_mapping()
        changed["basis_ref"] = "basis-collision"
        changed["basis_digest"] = _self_digest(changed, "basis_digest")
        continuity = _history(changed, False)
        sole = _history(changed, True)
        changed["bootstrap_guard_evidence"]["guard_digest"] = _self_digest(
            changed["bootstrap_guard_evidence"], "guard_digest")
        changed["basis_digest"] = _self_digest(changed, "basis_digest")
        other = _command(changed, head, continuity, sole,
                         mutation_ref=command.relation.to_mapping()["mutation_ref"])
        before = _counts(fixture.location)
        conflict = fixture.writer._record_progression_decision(
            other, source, validation, review)
        assert conflict.reason_code == "mutation_ref_reuse_conflict"
        assert _counts(fixture.location) == before
        assert fixture.writer._read_progression_decision(command, source) == committed
    finally:
        fixture.writer.close()


@pytest.mark.parametrize("original_assertion", (None, "candidate_acceptance"))
def test_expected_branch_v2_exact_replay_with_original_assertion(
    tmp_path, original_assertion,
):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    command = replace(command, expected_branch=original_assertion)
    try:
        committed = fixture.writer._record_progression_decision(
            command, source, validation, review)
        before = _durable_snapshot(fixture.location)
        assert committed.command_digest == command.command_digest
        assert fixture.writer._record_progression_decision(
            command, source, validation, review) == committed
        assert fixture.writer._read_progression_decision(command, source) == committed
        recovery = fixture.writer._recover_progression_decision(command, source)
        assert recovery.classification == "committed_exact"
        assert recovery.committed == committed
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


@pytest.mark.parametrize("wrong_assertion", (
    "candidate_repair", "program_terminal_reject"))
def test_changed_expected_branch_after_commit_is_never_exact_replay(
    tmp_path, wrong_assertion,
):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    original = replace(command, expected_branch=None)
    changed = replace(original, expected_branch=wrong_assertion)
    assert original.relation == changed.relation
    assert original.relation.command_digest == changed.relation.command_digest
    assert original.command_digest != changed.command_digest
    try:
        committed = fixture.writer._record_progression_decision(
            original, source, validation, review)
        before = _durable_snapshot(fixture.location)
        assert committed.command_digest == original.command_digest
        conflict = fixture.writer._record_progression_decision(
            changed, source, validation, review)
        assert conflict.reason_code == "mutation_ref_reuse_conflict"
        with pytest.raises(SQLiteMutationStoreError):
            fixture.writer._read_progression_decision(changed, source)
        recovery = fixture.writer._recover_progression_decision(changed, source)
        assert recovery.classification == "unresolved"
        assert recovery.committed is None
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


def test_fresh_wrong_expected_branch_conflicts_before_any_write(tmp_path):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    wrong = replace(command, expected_branch="candidate_repair")
    before = _durable_snapshot(fixture.location)
    try:
        conflict = fixture.writer._record_progression_decision(
            wrong, source, validation, review)
        assert conflict.reason_code == "expected_branch_mismatch"
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


def test_protected_replay_uses_disclosure_when_recording_is_denied(tmp_path):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    try:
        committed = fixture.writer._record_progression_decision(
            command, source, validation, review)
        before = _durable_snapshot(fixture.location)
        disclosure_only = replace(source, recording_permitted=False,
                                  disclosure_permitted=True)
        assert fixture.writer._record_progression_decision(
            command, disclosure_only, validation, review) == committed
        assert fixture.writer._read_progression_decision(
            command, disclosure_only) == committed
        recovery = fixture.writer._recover_progression_decision(
            command, disclosure_only)
        assert recovery.classification == "committed_exact"
        assert recovery.committed == committed
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


def test_truthful_post_acceptance_claim_preserves_exact_protected_replay(tmp_path):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    try:
        fresh = fixture.writer._record_progression_decision(
            command, source, validation, review)
        before = _durable_snapshot(fixture.location)
        claimed = replace(source, recording_permitted=False,
                          acceptance_exhaustively_unclaimed=False)
        assert fixture.writer._record_progression_decision(
            command, claimed, validation, review) == fresh
        assert fixture.writer._read_progression_decision(command, claimed) == fresh
        recovery = fixture.writer._recover_progression_decision(command, claimed)
        assert recovery.classification == "committed_exact"
        assert recovery.committed == fresh
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


def test_truthful_post_claim_nonaccept_replay_keeps_original_family(tmp_path):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_repair", "repair")
    try:
        fresh = fixture.writer._record_progression_decision(
            command, source, validation, review)
        before = _durable_snapshot(fixture.location)
        claimed = replace(source, recording_permitted=False,
                          acceptance_exhaustively_unclaimed=False)
        assert fixture.writer._record_progression_decision(
            command, claimed, validation, review) == fresh
        assert fixture.writer._read_progression_decision(command, claimed) == fresh
        recovery = fixture.writer._recover_progression_decision(command, claimed)
        assert recovery.classification == "committed_exact"
        assert recovery.committed == fresh
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


@pytest.mark.parametrize("current_unclaimed", (False, None))
def test_fresh_acceptance_requires_current_unclaimed_scope_after_branch(
    tmp_path, monkeypatch, current_unclaimed,
):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    source = replace(source, acceptance_exhaustively_unclaimed=current_unclaimed)
    before = _durable_snapshot(fixture.location)
    reached = []
    original_one = p1._one
    original_checked = ArtificialDecisionGuardSourceV1.checked_for
    original_route = p1._route_occupied
    original_current = p1._require_current
    original_reduce = p1.derive_progression_branch
    original_acceptance = ArtificialDecisionGuardSourceV1.checked_acceptance_eligibility_for
    def receipt_first(capability, table, where, parameters):
        if (table == "development_mutation_receipts" and where == "mutation_ref = ?"
            and "receipt" not in reached):
            reached.append("receipt")
        return original_one(capability, table, where, parameters)
    def universal(self, basis, *, now, write):
        reached.append("recording")
        return original_checked(self, basis, now=now, write=write)
    def route(*args, **kwargs):
        reached.append("route")
        return original_route(*args, **kwargs)
    def current(*args, **kwargs):
        reached.append("current")
        return original_current(*args, **kwargs)
    def reduce(*args, **kwargs):
        reached.append("branch")
        return original_reduce(*args, **kwargs)
    def acceptance(self, basis):
        reached.append("acceptance")
        return original_acceptance(self, basis)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(p1, "_one", receipt_first)
            patch.setattr(ArtificialDecisionGuardSourceV1, "checked_for", universal)
            patch.setattr(p1, "_route_occupied", route)
            patch.setattr(p1, "_require_current", current)
            patch.setattr(p1, "derive_progression_branch", reduce)
            patch.setattr(ArtificialDecisionGuardSourceV1,
                          "checked_acceptance_eligibility_for", acceptance)
            conflict = fixture.writer._record_progression_decision(
                command, source, validation, review)
        assert conflict.reason_code == "bootstrap_acceptance_guard_conflict"
        assert reached == ["receipt", "recording", "route", "current",
                           "branch", "acceptance"]
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


def test_fresh_nonaccept_under_claimed_scope_uses_derived_branch(tmp_path):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_repair", "repair")
    source = replace(source, acceptance_exhaustively_unclaimed=False)
    try:
        fresh = fixture.writer._record_progression_decision(
            command, source, validation, review)
        assert type(fresh) is ProgressionDecisionCommittedV1
        assert fresh.branch == "candidate_repair"
        assert _counts(fixture.location)["rw0_c2_bootstrap_acceptance_facts"] == 0
        before = _durable_snapshot(fixture.location)
        assert fixture.writer._read_progression_decision(command, source) == fresh
        assert fixture.writer._recover_progression_decision(
            command, source).classification == "committed_exact"
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


@pytest.mark.parametrize("posture", (
    "disclosure_denied", "expired", "continuity_negative",
    "sole_active_negative", "continuity_source_mismatch",
    "sole_active_source_mismatch", "malformed_source", "malformed_claim_type",
))
def test_protected_result_requires_fresh_positive_disclosure(
    tmp_path, monkeypatch, posture,
):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    try:
        fixture.writer._record_progression_decision(command, source, validation, review)
        before = _durable_snapshot(fixture.location)
        if posture == "disclosure_denied":
            denied = replace(source, disclosure_permitted=False)
        elif posture == "expired":
            denied = replace(source, expires_at="2021-01-01T00:00:00Z")
        elif posture == "continuity_negative":
            denied = replace(source, continuity_positive=False)
        elif posture == "sole_active_negative":
            denied = replace(source, sole_active_positive=False)
        elif posture == "continuity_source_mismatch":
            basis = deepcopy(command.basis.to_mapping())
            denied = replace(source, continuity_bytes=_canonical(
                _history(basis, False, suffix="mismatch")))
        elif posture == "sole_active_source_mismatch":
            basis = deepcopy(command.basis.to_mapping())
            denied = replace(source, sole_active_bytes=_canonical(
                _history(basis, True, suffix="mismatch")))
        elif posture == "malformed_claim_type":
            denied = replace(source, acceptance_exhaustively_unclaimed=1)
        else:
            denied = replace(source, continuity_bytes=b"{}")
        reached = []
        checked_for = ArtificialDecisionGuardSourceV1.checked_for
        def observed(self, basis, *, now, write):
            reached.append(write)
            return checked_for(self, basis, now=now, write=write)
        with monkeypatch.context() as patch:
            patch.setattr(ArtificialDecisionGuardSourceV1, "checked_for", observed)
            with pytest.raises(ValueError):
                denied.checked_for(command.basis, now=STAMP, write=False)
            record = fixture.writer._record_progression_decision(
                command, denied, validation, review)
            assert type(record) is not ProgressionDecisionCommittedV1
            with pytest.raises(SQLiteMutationStoreError):
                fixture.writer._read_progression_decision(command, denied)
            recovery = fixture.writer._recover_progression_decision(command, denied)
        assert reached == [False, False, False, False]
        assert recovery.classification == "unresolved"
        assert recovery.committed is None
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


def test_fresh_recording_and_absence_disclosure_are_distinct(tmp_path):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    before = _durable_snapshot(fixture.location)
    try:
        disclosure_only = replace(source, recording_permitted=False,
                                  disclosure_permitted=True)
        conflict = fixture.writer._record_progression_decision(
            command, disclosure_only, validation, review)
        assert conflict.reason_code == "basis_identity_lineage_profile_provenance_conflict"
        no_disclosure = replace(source, disclosure_permitted=False)
        with pytest.raises(SQLiteMutationStoreError):
            fixture.writer._read_progression_decision(command, no_disclosure)
        recovery = fixture.writer._recover_progression_decision(
            command, no_disclosure)
        assert recovery.classification == "unresolved"
        assert recovery.committed is None
        assert _durable_snapshot(fixture.location) == before
        committed = fixture.writer._record_progression_decision(
            command, no_disclosure, validation, review)
        assert type(committed) is ProgressionDecisionCommittedV1
        assert committed.command_digest == command.command_digest
    finally:
        fixture.writer.close()


@pytest.mark.parametrize("exception", (KeyboardInterrupt, SystemExit, GeneratorExit))
def test_disclosure_process_control_exceptions_are_unsuppressed(
    tmp_path, monkeypatch, exception,
):
    fixture, command, source, _validation, _review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    before = _durable_snapshot(fixture.location)
    def interrupted(self, basis, *, now, write):
        raise exception("synthetic disclosure interruption")
    try:
        with monkeypatch.context() as patch:
            patch.setattr(ArtificialDecisionGuardSourceV1, "checked_for", interrupted)
            with pytest.raises(exception):
                fixture.writer._read_progression_decision(command, source)
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


def test_p1_missing_family_member_never_gets_receipt_only_credit(tmp_path, monkeypatch):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "attempt_selecting_replan", "replan")
    try:
        fixture.writer._record_progression_decision(command, source, validation, review)
        original = p1._one
        reached = []
        def hidden(capability, table, where, parameters):
            if table == p1._RELATION:
                reached.append(True)
                return None
            return original(capability, table, where, parameters)
        with monkeypatch.context() as patch:
            patch.setattr(p1, "_one", hidden)
            with pytest.raises(SQLiteMutationStoreError):
                fixture.writer._read_progression_decision(command, source)
            assert fixture.writer._recover_progression_decision(
                command, source).classification == "unresolved"
        assert reached == [True, True]
    finally:
        fixture.writer.close()


def test_malformed_persisted_basis_is_integrity_not_posture_conflict(tmp_path):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    try:
        fixture.writer._record_progression_decision(command, source, validation, review)
        before = _durable_snapshot(fixture.location)
        with patch.object(p1, "_historical_exact",
                          side_effect=ValueError("synthetic malformed persisted basis")):
            with pytest.raises(SQLiteMutationStoreError) as record_failure:
                fixture.writer._record_progression_decision(
                    command, source, validation, review)
            assert record_failure.value.error_class == "database_integrity_failure"
            with pytest.raises(SQLiteMutationStoreError):
                fixture.writer._read_progression_decision(command, source)
            recovery = fixture.writer._recover_progression_decision(command, source)
            assert recovery.classification == "unresolved"
            assert recovery.committed is None
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


@pytest.mark.parametrize("winner_assertion", (None, "candidate_acceptance"))
@pytest.mark.parametrize("current_unclaimed", (True, False))
def test_different_complete_acceptance_winner_proves_original_absence(
    tmp_path, monkeypatch, winner_assertion, current_unclaimed,
):
    fixture, original_command, original_source, validation, review, head = _case(
        tmp_path, "candidate_acceptance", "accept")
    changed = original_command.basis.to_mapping()
    changed["basis_ref"] = "basis-competitor"
    continuity = _history(changed, False, suffix="competitor")
    sole = _history(changed, True, suffix="competitor")
    changed["bootstrap_guard_evidence"]["guard_digest"] = _self_digest(
        changed["bootstrap_guard_evidence"], "guard_digest")
    changed["basis_digest"] = _self_digest(changed, "basis_digest")
    competitor = _command(changed, head, continuity, sole,
                          mutation_ref="p1-competitor")
    competitor = replace(competitor, expected_branch=winner_assertion)
    competitor_source = ArtificialDecisionGuardSourceV1(
        _canonical(continuity), _canonical(sole),
        "2020-01-01T00:00:00Z", "2099-01-01T00:00:00Z",
        True, True, True, True, True, True, True,
    )
    original_source = replace(
        original_source, acceptance_exhaustively_unclaimed=current_unclaimed)
    try:
        winner = fixture.writer._record_progression_decision(
            competitor, competitor_source, validation, review)
        assert winner.branch == "candidate_acceptance"
        assert winner.command_digest == competitor.command_digest
        before = _durable_snapshot(fixture.location)
        recovered = fixture.writer._recover_progression_decision(
            original_command, original_source)
        assert recovered.classification == "definitely_not_committed"
        assert recovered.committed is None
        assert _durable_snapshot(fixture.location) == before
        reached = []
        original = p1._one
        def hidden(capability, table, where, parameters):
            if table == p1._RELATION:
                reached.append(True)
                return None
            return original(capability, table, where, parameters)
        with monkeypatch.context() as patch:
            patch.setattr(p1, "_one", hidden)
            assert fixture.writer._recover_progression_decision(
                original_command, original_source).classification == "unresolved"
        assert reached
    finally:
        fixture.writer.close()


@pytest.mark.parametrize("current_unclaimed,classification", (
    (False, "unresolved"), (None, "definitely_not_committed"),
))
def test_claim_without_complete_local_winner_cannot_prove_absence(
    tmp_path, current_unclaimed, classification,
):
    fixture, command, source, _validation, _review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    source = replace(source, acceptance_exhaustively_unclaimed=current_unclaimed)
    before = _durable_snapshot(fixture.location)
    try:
        assert _counts(fixture.location)["rw0_c2_bootstrap_acceptance_facts"] == 0
        recovery = fixture.writer._recover_progression_decision(command, source)
        assert recovery.classification == classification
        assert recovery.committed is None
        assert _durable_snapshot(fixture.location) == before
    finally:
        fixture.writer.close()


def test_p1_cleanup_acknowledgment_loss_quarantines_writer(tmp_path, monkeypatch):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "candidate_acceptance", "accept")
    original = txn._RetainedSQLiteConnection._close_with_proof
    reached = []
    def lost_close(self):
        result = original(self)
        reached.append(result)
        raise RuntimeError("synthetic close acknowledgment loss")
    try:
        with monkeypatch.context() as patch:
            patch.setattr(txn._RetainedSQLiteConnection, "_close_with_proof", lost_close)
            with pytest.raises(SQLiteMutationStoreError) as failure:
                fixture.writer._record_progression_decision(
                    command, source, validation, review)
        assert reached and failure.value.error_class == "commit_outcome_unknown"
        with pytest.raises(Exception, match="state_authority_lock_busy"):
            acquire_sqlite_writer_session(fixture.location)
    finally:
        fixture.writer.close()


@pytest.mark.parametrize("table,key,occurrence", (
    ("development_decisions", "decision_ref", 1),
    ("development_decisions", "mutation_ref", 1),
    ("development_program_versions", "program_version_ref", 1),
    ("development_mutation_receipts", "mutation_ref", 2),
    (p1._CONTINUITY, "basis_ref", 1),
    (p1._SOLE, "basis_ref", 1),
    (p1._BASIS, "basis_ref", 1),
    (p1._BASIS, "mutation_ref", 1),
    (p1._RELATION, "relation_ref", 1),
    (p1._RELATION, "mutation_ref", 1),
    (p1._RELATION, "family_route", 1),
    (p1._RESULT, "guarded_result_ref", 1),
    (p1._RESULT, "mutation_ref", 1),
    (p1._ACCEPTANCE, "acceptance_fact_ref", 1),
    (p1._ACCEPTANCE, "admission_fact_ref", 1),
    (p1._ACCEPTANCE, "lineage_ref", 1),
    (p1._ACCEPTANCE, "scope_ref", 1),
    ("development_accepted_intent_revisions", "accepted_intent_revision_ref", 1),
    ("development_work_item_revisions", "work_item_revision_ref", 1),
    ("development_work_spec_bindings", "work_spec_ref", 1),
    ("development_revision_edges", "revision_edge_ref", 1),
    ("development_revision_edges", "revision_edge_ref", 2),
))
def test_each_original_creation_or_alias_probe_stops_fresh_write(
    tmp_path, monkeypatch, table, key, occurrence,
):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "attempt_selecting_replan", "replan")
    before = _counts(fixture.location)
    original = p1._one
    seen = []
    def occupied(capability, observed_table, where, parameters):
        if observed_table == table and where == key + " = ?":
            seen.append(parameters)
            if len(seen) == occurrence:
                return object()
        return original(capability, observed_table, where, parameters)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(p1, "_one", occupied)
            result = fixture.writer._record_progression_decision(
                command, source, validation, review)
        assert len(seen) == occurrence
        assert result.reason_code == "preassigned_identity_or_family_route_collision"
        assert _counts(fixture.location) == before
    finally:
        fixture.writer.close()


def test_resulting_membership_route_collision_stops_fresh_write(tmp_path, monkeypatch):
    fixture, command, source, validation, review, _ = _case(
        tmp_path, "attempt_selecting_replan", "replan")
    before = _counts(fixture.location)
    original = p1._members
    reached = []
    def occupied(capability, program_ref, version_ref, *, allow_empty=False):
        if allow_empty:
            reached.append(version_ref)
            return (object(),)
        return original(capability, program_ref, version_ref, allow_empty=allow_empty)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(p1, "_members", occupied)
            result = fixture.writer._record_progression_decision(
                command, source, validation, review)
        assert reached == [command.relation.to_mapping()["preassigned_version_ref"]]
        assert result.reason_code == "preassigned_identity_or_family_route_collision"
        assert _counts(fixture.location) == before
    finally:
        fixture.writer.close()
