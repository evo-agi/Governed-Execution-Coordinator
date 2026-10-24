"""Actual D2 process continuation through native A, C1 B, and pure V22."""

from __future__ import annotations

import base64
from dataclasses import fields, replace
import json
import sqlite3

import pytest

import ge_nwp_coordinator._rw0_d2_handback as d2_handback
import ge_nwp_coordinator._rw0_d1_offline as d1_offline
import ge_nwp_coordinator._cognitive_proposal_row_values as common_rows
import ge_nwp_coordinator._sqlite_section41_post_execution_proposal as post_store
import ge_nwp_coordinator.sqlite_transition_transaction as transaction
from ge_nwp_coordinator._cognitive_proposal_value_support import _domain_separated_digest
from ge_nwp_coordinator._rw0_c1_semantic_values import (
    RW0C1ConflictReasonV1, RW0C1ConflictV1,
)
from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture
from ge_nwp_coordinator._rw0_d1_process_frames import decode_worker_launch
from ge_nwp_coordinator._rw0_d2_offline import run_rw0_d2_offline
from ge_nwp_coordinator._rw0_d2_post_execution_continuation import (
    _rank15_command, continue_open_rw0_d2_run, prepare_record_command,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator._rw0_wire_protocol_values import (
    RW0WireWorkerResultV1, decode_wire_command_frame,
    decode_wire_result_frame, encode_wire_result_frame,
)
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1, EffectFenceV1,
)
from test_rw0_d1_offline_integration import work_spec


def _counts(run: object, proposal_ref: str) -> tuple[int, int, int, int, int]:
    # Read-only observation of this test's disposable artificial database.
    with sqlite3.connect(run._d1_run.location.database_path) as db:
        return (
            db.execute("SELECT count(*) FROM development_model_source_invocations "
                       "WHERE proposal_phase='post_execution_semantic_review'").fetchone()[0],
            db.execute("SELECT count(*) FROM development_model_proposals "
                       "WHERE proposal_ref=?", (proposal_ref,)).fetchone()[0],
            db.execute("SELECT count(*) FROM development_model_proposal_evidence_bindings "
                       "WHERE proposal_ref=?", (proposal_ref,)).fetchone()[0],
            db.execute("SELECT count(*) FROM development_post_execution_proposal_contexts "
                       "WHERE proposal_ref=?", (proposal_ref,)).fetchone()[0],
            db.execute("SELECT count(*) FROM development_post_execution_proposal_receipts "
                       "WHERE proposal_ref=?", (proposal_ref,)).fetchone()[0],
        )


def _record_and_read(run: object) -> tuple[object, object, object]:
    command, safe = prepare_record_command(run)
    with acquire_sqlite_writer_session(run._d1_run.location) as writer:
        result = writer._record_post_execution_proposal(command, run, safe)
    with acquire_sqlite_writer_session(run._d1_run.location) as writer:
        checked = writer._read_post_execution_proposal(command)
    return command, result, checked


def _advance_program_head_in_test_database(run: object) -> None:
    # Test-only coherent head movement after A, with the same immutable
    # program version. This deliberately makes C1's frozen CAS preimage stale.
    with sqlite3.connect(run._d1_run.location.database_path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        row = db.execute(
            "SELECT schema_id, program_ref, current_program_version_ref, "
            "current_program_version_number, head_revision, program_state, "
            "updated_at, head_digest FROM development_program_heads"
        ).fetchone()
        assert row is not None
        names = (
            "schema_id", "program_ref", "current_program_version_ref",
            "current_program_version_number", "head_revision", "program_state",
            "updated_at", "head_digest",
        )
        mapping = dict(zip(names, row, strict=True))
        mapping["head_revision"] += 1
        mapping["updated_at"] = "2029-01-01T00:00:00Z"
        identity = {name: mapping[name] for name in names if name != "head_digest"}
        mapping["head_digest"] = _domain_separated_digest(
            "governed-execution.nwp-development-program-head.v1.identity",
            identity,
        )
        db.execute(
            "UPDATE development_program_heads SET head_revision=?, updated_at=?, "
            "head_digest=? WHERE program_ref=?",
            (mapping["head_revision"], mapping["updated_at"],
             mapping["head_digest"], mapping["program_ref"]),
        )


def test_actual_d2_a_b_and_unchanged_v22_connected_positive() -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        handback = run.handback
        assert handback.status == "preadmission_ready"
        assert len(handback.child_outcomes) == 3
        assert all(child.clean_success and child.cleanup_complete
                   for child in handback.child_outcomes)
        result = continue_open_rw0_d2_run(run)
        assert (result.status, result.reason) == ("projected", "complete")
        assert result.cleanup_complete is None
        assert result.proposal_result.disposition == "fresh_committed"
        assert result.admission_result.kind_rank == 15
        assert result.admission_result.disposition == "fresh_committed"
        assert result.projection.proposal_ref == handback.proposal.proposal_ref
        assert _counts(run, handback.proposal.proposal_ref) == (1, 1, 9, 1, 1)
        with sqlite3.connect(run._d1_run.location.database_path) as db:
            assert db.execute(
                "SELECT count(*) FROM rw0_evidence_memberships WHERE kind_rank=15"
            ).fetchone()[0] == 1


def _omit_optional_capture_observation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise the Wire owner's legal two-observation result from a real D1 child."""
    original = d1_offline.run_fake_module

    def legal_two_observation_result(module: str, request: bytes, **kwargs: object) -> object:
        process = original(module, request, **kwargs)
        if module != "ge_nwp_coordinator._rw0_d1_fake_worker" or not process.clean_success:
            return process
        launch = decode_worker_launch(request)
        attempt = AttemptFenceV1.from_mapping(launch["attempt_fence"])
        effect = EffectFenceV1.from_mapping(launch["effect_fence"])
        command, delivery = decode_wire_command_frame(
            base64.b64decode(launch["command_frame_b64"]),
            attempt_fence=attempt, author_effect_fence=effect,
        )
        result = decode_wire_result_frame(
            process.stdout, command=command, delivery=delivery,
            attempt_fence=attempt, author_effect_fence=effect,
        )
        assert tuple(item.observation_kind for item in result.observations) == (
            "worker_started", "candidate_captured", "worker_completed",
        )
        two = RW0WireWorkerResultV1._create((
            result.observations[0], result.observations[2],
        ))
        return replace(process, stdout=encode_wire_result_frame(
            result=two, command=command, delivery=delivery,
            attempt_fence=attempt, author_effect_fence=effect,
        ))

    monkeypatch.setattr(d1_offline, "run_fake_module", legal_two_observation_result)


def test_two_observation_actual_d1_through_native_a_b_and_v22(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _omit_optional_capture_observation(monkeypatch)
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        handback = run.handback
        assert handback.status == "preadmission_ready"
        assert tuple(item.observation_kind for item in handback.d1_handback.wire_result.observations) == (
            "worker_started", "worker_completed",
        )
        assert "candidate_ref" not in handback.d1_handback.wire_result.observations[1].to_mapping()
        assert len(handback.checked_admissions) == 13
        assert tuple(item.admission_result.kind_rank for item in handback.checked_admissions) == (
            12, 12, 12, 13, 14, 1, 1, 5, 6, 12, 6, 12, 1,
        )
        assert len(handback.evidence_checkpoint.reviewer_separation.author_observation_locators) == 2
        result = continue_open_rw0_d2_run(run)
        assert (result.status, result.reason) == ("projected", "complete")
        assert result.proposal_result.disposition == "fresh_committed"
        assert result.admission_result.kind_rank == 15
        assert result.admission_result.disposition == "fresh_committed"
        assert result.projection.proposal_ref == handback.proposal.proposal_ref
        assert _counts(run, handback.proposal.proposal_ref) == (1, 1, 9, 1, 1)


def test_same_capsule_donor_b_refused_at_final_record_consumer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    recipient = run_rw0_d2_offline(work, artificial_fixture(work))
    donor = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        original = recipient.handback
        assert original.evidence_checkpoint.capsule_manifest.to_mapping() == (
            donor.handback.evidence_checkpoint.capsule_manifest.to_mapping()
        )
        command, safe = prepare_record_command(recipient)
        changes = {name: getattr(donor.handback, name) for name in d2_handback._B_ORDER}
        changes["child_outcomes"] = (
            *original.child_outcomes[:2], donor.handback.child_outcomes[2],
        )
        forged = object.__new__(type(original))
        for member in fields(original):
            object.__setattr__(
                forged, member.name, changes.get(member.name, getattr(original, member.name)),
            )
        recipient._handback = forged
        reached = []
        original_relation = d2_handback._validate_a_to_b_input_binding
        def observed(value: object) -> None:
            reached.append(True)
            return original_relation(value)
        monkeypatch.setattr(d2_handback, "_validate_a_to_b_input_binding", observed)
        with acquire_sqlite_writer_session(recipient._d1_run.location) as writer:
            with pytest.raises(SQLiteMutationStoreError):
                writer._record_post_execution_proposal(command, recipient, safe)
        assert reached
        assert _counts(recipient, command.proposal_ref) == (0, 0, 0, 0, 0)
    finally:
        donor.close()
        recipient.close()


def test_fresh_writer_refuses_valid_donor_command_and_basis_before_target_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    donor_fixture = artificial_fixture(work)
    donor_fixture = replace(donor_fixture, base_entries=(
        donor_fixture.base_entries[0], donor_fixture.base_entries[1],
        (donor_fixture.base_entries[2][0],
         b"package contracts\n\nfunc TestDonor() {}\n", "100644"),
    ))
    with run_rw0_d2_offline(work, artificial_fixture(work)) as recipient:
        with run_rw0_d2_offline(work, donor_fixture) as donor:
            own_command, own_basis = prepare_record_command(recipient)
            donor_command, donor_basis = prepare_record_command(donor)
            assert donor_command.command_digest != own_command.command_digest
            assert donor_command.safe_basis_digest != own_command.safe_basis_digest
            assert donor_basis != own_basis
            reached = []
            currentness_reads = []
            original = post_store.prepare_record_command
            original_currentness = post_store._read_rw0_d2_current_owner_snapshot_after_fencing

            def observed_run_derivation(run: object) -> tuple[object, bytes]:
                reached.append(run)
                return original(run)

            def observed_currentness(*args: object, **kwargs: object) -> object:
                currentness_reads.append(True)
                return original_currentness(*args, **kwargs)

            monkeypatch.setattr(post_store, "prepare_record_command", observed_run_derivation)
            monkeypatch.setattr(
                post_store, "_read_rw0_d2_current_owner_snapshot_after_fencing",
                observed_currentness,
            )
            with acquire_sqlite_writer_session(recipient._d1_run.location) as writer:
                with pytest.raises(SQLiteMutationStoreError):
                    writer._record_post_execution_proposal(
                        donor_command, recipient, donor_basis,
                    )
            assert reached == [recipient]
            assert currentness_reads == []
            assert _counts(recipient, donor_command.proposal_ref) == (0, 0, 0, 0, 0)
            assert _counts(recipient, own_command.proposal_ref) == (0, 0, 0, 0, 0)
            with acquire_sqlite_writer_session(recipient._d1_run.location) as writer:
                committed = writer._record_post_execution_proposal(
                    own_command, recipient, own_basis,
                )
            assert committed.disposition == "fresh_committed"
            assert currentness_reads == [True]
            assert _counts(recipient, own_command.proposal_ref) == (1, 1, 9, 1, 1)


@pytest.mark.parametrize("worker_count", (2, 3))
def test_both_layouts_historical_a_replay_and_checked_readback_without_child_rerun(
    monkeypatch: pytest.MonkeyPatch, worker_count: int,
) -> None:
    import ge_nwp_coordinator._rw0_d2a_offline as d2a_offline
    import ge_nwp_coordinator._rw0_d2_offline as d2_offline

    with monkeypatch.context() as patch:
        if worker_count == 2:
            _omit_optional_capture_observation(patch)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        command, basis = prepare_record_command(run)
        assert len(json.loads(basis)["d2_checkpoint_witness"]["checked_memberships"]) == (
            worker_count + 11
        )
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            first = writer._record_post_execution_proposal(command, run, basis)
        assert first.disposition == "fresh_committed"

        def child_forbidden(*_args: object, **_kwargs: object) -> object:
            raise AssertionError("historical_a_replay_reran_child")

        monkeypatch.setattr(d1_offline, "run_fake_module", child_forbidden)
        monkeypatch.setattr(d2a_offline, "run_fake_module", child_forbidden)
        monkeypatch.setattr(d2_offline, "run_fake_module", child_forbidden)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            replay = writer._record_post_execution_proposal(command, run, basis)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            checked = writer._read_post_execution_proposal(command)
        assert replay.disposition == "exact_replay"
        assert replay.receipt_digest == first.receipt_digest
        assert checked.receipt.receipt_digest == first.receipt_digest
        assert _counts(run, command.proposal_ref) == (1, 1, 9, 1, 1)
    finally:
        run.close()


@pytest.mark.parametrize("missing_insert_position", range(1, 10))
def test_each_missing_actual_evidence_role_is_rejected_at_transaction_gate(
    monkeypatch: pytest.MonkeyPatch, missing_insert_position: int,
) -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, safe = prepare_record_command(run)
        original = post_store._insert
        observed = []
        def omit_selected(connection: object, table: str, columns: tuple[str, ...],
                       values: tuple[object, ...]) -> None:
            if table == "development_model_proposal_evidence_bindings":
                observed.append(True)
                if len(observed) == missing_insert_position:
                    return
            original(connection, table, columns, values)
        monkeypatch.setattr(post_store, "_insert", omit_selected)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            with pytest.raises(SQLiteMutationStoreError):
                writer._record_post_execution_proposal(command, run, safe)
        assert len(observed) == 9
        assert _counts(run, command.proposal_ref) == (0, 0, 0, 0, 0)


@pytest.mark.parametrize("fault", (
    "extra", "duplicate", "reordered", "wrong_role", "phase",
    "source", "set", "digest", "ref",
))
def test_same_transaction_gate_rejects_faulted_actual_evidence_observation(
    monkeypatch: pytest.MonkeyPatch, fault: str,
) -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, safe = prepare_record_command(run)
        original = post_store._select
        original_evidence = post_store._evidence
        reached = []
        parsed = []

        def observed_evidence(capability: object, proposal_ref: str) -> object:
            value = original_evidence(capability, proposal_ref)
            parsed.append(True)
            return value

        def faulted_select(capability: object, table: str, columns: tuple[str, ...],
                           where: str, params: tuple[object, ...], *,
                           limit: int, order: str = "") -> tuple[tuple[object, ...], ...]:
            rows = original(capability, table, columns, where, params,
                            limit=limit, order=order)
            if table != common_rows._TABLE_ORDER[5] or limit != 10:
                return rows
            reached.append(True)
            assert len(rows) == 9
            if fault == "extra":
                return (*rows, rows[0])
            if fault == "duplicate":
                return (rows[0], *rows[:-1])
            if fault == "reordered":
                return tuple(reversed(rows))
            first = dict(zip(columns, rows[0], strict=True))
            field, replacement = {
                "wrong_role": ("evidence_role", "worker_result"),
                "phase": ("proposal_phase", "pre_execution_plan"),
                "source": ("proposal_ref", "alien.proposal"),
                "set": ("evidence_set_ref", "alien.evidence-set"),
                "digest": ("evidence_digest", "0" * 64),
                "ref": ("evidence_ref", "alien.evidence"),
            }[fault]
            first[field] = replacement
            first["evidence_binding_digest"] = _domain_separated_digest(
                common_rows._DOMAINS[table],
                {name: first[name] for name in columns
                 if name != "evidence_binding_digest"},
            )
            return (tuple(first[name] for name in columns), *rows[1:])

        monkeypatch.setattr(post_store, "_select", faulted_select)
        monkeypatch.setattr(post_store, "_evidence", observed_evidence)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            with pytest.raises(SQLiteMutationStoreError):
                writer._record_post_execution_proposal(command, run, safe)
        assert reached == [True]
        assert parsed == ([True] if fault in {"source", "set", "digest", "ref"} else [])
        assert _counts(run, command.proposal_ref) == (0, 0, 0, 0, 0)


def test_a_retained_when_b_fresh_cas_conflicts() -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, a_result, checked = _record_and_read(run)
        assert a_result.disposition == "fresh_committed"
        b_command = _rank15_command(checked, run.handback.checked_admissions[0].phase)
        _advance_program_head_in_test_database(run)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            b_result = writer._admit_rw0_evidence(b_command)
        assert type(b_result) is RW0C1ConflictV1
        assert b_result.reason is RW0C1ConflictReasonV1.CURRENT_STATE_CONFLICT
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            historical = writer._read_post_execution_proposal(command)
        assert historical.receipt.receipt_digest == a_result.receipt_digest
        assert _counts(run, command.proposal_ref) == (1, 1, 9, 1, 1)
        with sqlite3.connect(run._d1_run.location.database_path) as db:
            assert db.execute(
                "SELECT count(*) FROM rw0_c1_mutation_receipts WHERE mutation_ref=?",
                (b_command.mutation_ref,),
            ).fetchone()[0] == 0


def test_a_historical_replay_after_head_change_uses_no_clock_or_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        command, first, _checked = _record_and_read(run)
        _advance_program_head_in_test_database(run)
        def forbidden() -> str:
            raise AssertionError("historical_replay_sampled_fresh_clock")
        monkeypatch.setattr(transaction, "_capture_transaction_timestamp", forbidden)
        with acquire_sqlite_writer_session(run._d1_run.location) as writer:
            replay = writer._record_post_execution_proposal(
                command, run, prepare_record_command(run)[1],
            )
        assert replay.disposition == "exact_replay"
        assert (replay.receipt_digest, replay.committed_at) == (
            first.receipt_digest, first.committed_at,
        )
        assert _counts(run, command.proposal_ref) == (1, 1, 9, 1, 1)


@pytest.mark.parametrize(("contract", "recommendation"), (
    (b"package contracts\n\nfunc TestContract() {}\n", "accept_candidate"),
    (b"package contracts\n\nfunc TestContract() {}\n// UNSAFE-CHANGE\n", "repair_candidate"),
    (b"package contracts\n\nfunc TestContract() {}\n// VALIDATION-REPLAN\n", "replan"),
    (b"package contracts\n\nfunc TestContract() {}\n// VALIDATION-TERMINAL\n", "terminal_reject"),
    (b"package contracts\n\nfunc TestContract() {}\n// VALIDATION-UNCLASSIFIED\n", "block"),
))
def test_all_five_model_recommendations_remain_admitted_proposal_evidence(
    contract: bytes, recommendation: str,
) -> None:
    work = work_spec()
    fixture = artificial_fixture(work)
    fixture = replace(fixture, base_entries=(
        fixture.base_entries[0], fixture.base_entries[1],
        (fixture.base_entries[2][0], contract, "100644"),
    ))
    with run_rw0_d2_offline(work, fixture) as run:
        assert run.handback.proposal.recommendation == recommendation
        with sqlite3.connect(run._d1_run.location.database_path) as db:
            decisions_before = db.execute(
                "SELECT count(*) FROM development_decisions"
            ).fetchone()[0]
        result = continue_open_rw0_d2_run(run)
        assert result.status == "projected"
        assert result.proposal_result.disposition == "fresh_committed"
        assert result.admission_result.kind_rank == 15
        assert result.projection.recommendation == recommendation
        with sqlite3.connect(run._d1_run.location.database_path) as db:
            assert db.execute(
                "SELECT count(*) FROM development_decisions"
            ).fetchone()[0] == decisions_before
