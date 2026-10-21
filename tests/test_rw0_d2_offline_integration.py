"""Single-input D2 proof: real A admissions, three D2 children, one typed handback."""

from __future__ import annotations

from dataclasses import fields, replace
import hashlib
import json
from pathlib import Path
import pickle
import sqlite3
import pytest

import ge_nwp_coordinator._rw0_d2_handback as d2_handback
import ge_nwp_coordinator._rw0_d2_offline as d2_offline
import ge_nwp_coordinator._rw0_d1_process_supervisor as supervisor
from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture
from ge_nwp_coordinator._rw0_d1_offline import run_rw0_d1_offline
from ge_nwp_coordinator._rw0_d2_offline import run_rw0_d2_offline
from ge_nwp_coordinator._rw0_phase_entry_semantic_values import (
    RW0AuthorityVerificationObservationV1, validate_authority_observation,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError
from test_rw0_d1_offline_integration import work_spec


def _forge_exact_value(value: object, **changes: object) -> object:
    """Test only: reach a consumer with one altered exact frozen wrapper."""
    forged = object.__new__(type(value))
    for member in fields(value):
        object.__setattr__(forged, member.name,
                           changes.get(member.name, getattr(value, member.name)))
    return forged


def _reject_reason_only(handback: object, reason: str) -> None:
    """Both construction and direct consumption must reject the same false reason."""
    with pytest.raises(ValueError, match="^invalid_d2_preadmission_handback$"):
        replace(handback, reason=reason)
    forged = _forge_exact_value(handback, reason=reason)
    with pytest.raises(ValueError, match="^invalid_d2_preadmission_handback$"):
        forged.validate()


# Fixed producer prefixes: D1 non-continuation has no D2 facts; A establishment
# has 0..1 effects, A admission has two effects and an ordered 0..13 checked
# prefix, A checking has one or two actual child outcomes, and completed A has
# 2/14/2 plus a checkpoint. B may stop before input, after paired input, or
# after its model child. These are assertions about retained producer facts,
# not a new durable history or a new public reason grammar.


def _alternate_same_role_authority(
    source: RW0AuthorityVerificationObservationV1,
) -> RW0AuthorityVerificationObservationV1:
    """Reseal an individually valid observation without changing its role fence."""
    mapping = source.to_mapping()
    mapping["observation_ref"] = "authority-observation.d2.validation.alternate"
    mapping["evidence_ref"] = "authority-evidence.d2.validation.alternate"
    mapping["evidence_digest"] = hashlib.sha256(
        mapping["evidence_ref"].encode("utf-8")
    ).hexdigest()
    identity = {name: value for name, value in mapping.items()
                if name != "observation_digest"}
    schema = "governed-execution.nwp-rw0-authority-verification-observation.v1"
    mapping["observation_digest"] = hashlib.sha256(
        (schema + ".identity").encode("utf-8") + b"\0"
        + json.dumps(identity, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()
    return RW0AuthorityVerificationObservationV1.from_mapping(mapping)


def test_single_input_ready_handback_and_owned_close() -> None:
    work = work_spec()
    run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        handback.validate()
        assert handback.status == "preadmission_ready"
        assert handback.reason == "complete"
        assert len(handback.committed_bound_effects) == 2
        assert len(handback.checked_admissions) == 14
        assert len(handback.child_outcomes) == 3
        assert len({item.pid for item in handback.child_outcomes}) == 3
        assert handback.model_process is handback.child_outcomes[2]
        assert handback.proposal.recommendation == "accept_candidate"
        assert handback.evidence_checkpoint.d1_handback is handback.d1_handback
        assert "_d1_run" not in repr(handback)
    finally:
        run.close()
        run.close()
    with pytest.raises(RuntimeError, match="d2_run_closed"):
        _ = run.handback


def test_d1_stopped_has_no_invented_a_or_model_evidence() -> None:
    work = work_spec()
    run = run_rw0_d2_offline(work, artificial_fixture(work, planner_behavior="defer"))
    try:
        handback = run.handback
        assert handback.status == "stopped"
        assert handback.reason == "d1_stopped"
        assert handback.d1_handback.reason == "nonselection"
        assert handback.committed_bound_effects == ()
        assert handback.checked_admissions == ()
        assert handback.child_outcomes == ()
        assert handback.proposal is None
        handback.validate()
        _reject_reason_only(handback, "model_input_or_normalization_failed")
    finally:
        run.close()


def test_resource_free_handback_rejects_live_or_incoherent_nested_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        handback = run.handback
        checkpoint = handback.evidence_checkpoint
        assert checkpoint is not None
        for field_name, bad in (
            ("evidence_checkpoint", run),
            ("committed_bound_effects", [*handback.committed_bound_effects]),
            ("checked_admissions", handback.checked_admissions[:-1]),
            ("child_outcomes", (*handback.child_outcomes[:2], Path("state.db"))),
            ("evidence_bindings", [*handback.evidence_bindings]),
        ):
            with pytest.raises(ValueError, match="^invalid_d2_preadmission_handback$"):
                replace(handback, **{field_name: bad})
        for field_name, bad in (
            ("capture", run),
            ("policy_sources", (*checkpoint.policy_sources[:-1], object())),
            ("admitted_families", checkpoint.admitted_families[:-1]),
        ):
            with pytest.raises(ValueError, match="^invalid_d2_evidence_checkpoint$"):
                replace(checkpoint, **{field_name: bad})
        assert handback.proposal is not None and handback.evidence_set is not None
        with pytest.raises(ValueError):
            replace(handback.proposal, proposal_phase="pre_execution_plan")
        with pytest.raises(ValueError):
            replace(handback.proposal, recommendation="defer")
        with pytest.raises(ValueError):
            replace(handback.evidence_set, entries=handback.evidence_bindings[:-1])
        with pytest.raises(TypeError, match="serialization disabled"):
            pickle.dumps(handback)
        pid = d2_handback.os.getpid()
        with monkeypatch.context() as patch:
            patch.setattr(d2_handback.os, "getpid", lambda: pid + 1)
            with pytest.raises(RuntimeError, match="^d2_run_wrong_process$"):
                _ = run.handback
            with pytest.raises(RuntimeError, match="^d2_run_wrong_process$"):
                run.close()


def test_authority_roles_match_actual_checked_families_and_reconstruction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launched: list[object] = []
    original_popen = supervisor.subprocess.Popen

    def observe(*args: object, **kwargs: object) -> object:
        process = original_popen(*args, **kwargs)
        launched.append(process)
        return process

    with monkeypatch.context() as patch:
        patch.setattr(supervisor.subprocess, "Popen", observe)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
        try:
            handback = run.handback
            checkpoint = handback.evidence_checkpoint
            assert handback.status == "preadmission_ready" and checkpoint is not None
            assert len(checkpoint.admitted_families) == 14
            assert len(handback.child_outcomes) == 3
            assert len(launched) == 5
            assert all(process.poll() is not None for process in launched)
            source_slots = checkpoint.authority_sources
            family_slots = (6, 7, 13)
            assert tuple(f.admission_result.kind_rank for f in checkpoint.admitted_families) == (
                12, 12, 12, 12, 13, 14, 1, 1, 5, 6, 12, 6, 12, 1,
            )
            assert tuple(f.admission_result.membership_ref
                         for f in (checkpoint.admitted_families[i] for i in family_slots)) == (
                "membership.d2.validation-authority",
                "membership.d2.review-authority",
                "membership.d2.author-authority",
            )
            assert tuple(source.observation_ref for source in source_slots) == (
                "authority-observation.d2.validation",
                "authority-observation.d2.review",
                "authority-observation.d2.author",
            )
            assert tuple(source.effect_class for source in source_slots) == (
                "validate_candidate", "review_candidate", "author_candidate",
            )
            for source, family_index in zip(source_slots, family_slots, strict=True):
                family = checkpoint.admitted_families[family_index]
                family.validate()
                assert source.to_mapping() == family.evidence_value.to_mapping()
                assert source.observation_ref == family.admission_result.value_ref
                assert source.observation_digest == family.admission_result.value_digest
                assert source.phase_basis_ref == handback.d1_handback.phase_basis.basis_ref
                assert source.phase_basis_digest == handback.d1_handback.phase_basis.basis_digest
            for index, fence in enumerate((
                checkpoint.bound_effects[0].current_fence,
                checkpoint.bound_effects[1].current_fence,
            )):
                assert source_slots[index].effect_fence_ref == fence.effect_fence_ref
                assert checkpoint.qualifications[index].verification_ref == source_slots[index].observation_ref
                assert checkpoint.qualifications[index].verification_digest == source_slots[index].observation_digest
            author_fence = handback.d1_handback.author_command.effect_fence
            assert source_slots[2].effect_fence_ref == author_fence.effect_fence_ref
            assert source_slots[2].effect_fence_digest == author_fence.effect_fence_digest
            reconstructed = RW0AuthorityVerificationObservationV1.from_mapping(
                source_slots[0].to_mapping(),
            )
            assert reconstructed is not source_slots[0]
            assert reconstructed.to_mapping() == source_slots[0].to_mapping()
            equivalent = replace(checkpoint, authority_sources=(
                reconstructed, source_slots[1], source_slots[2],
            ))
            equivalent.validate()
            replace(handback, evidence_checkpoint=equivalent).validate()
            assert run.handback is handback
        finally:
            run.close()
            run.close()
    assert all(process.poll() is not None for process in launched)


@pytest.mark.parametrize("case_name", (
    "validation_review_sources",
    "validation_author_sources",
    "review_author_sources",
    "duplicate_source",
    "validation_review_families",
    "source_family_pairs",
    "same_role_alternate",
))
def test_authority_role_transpositions_and_alternate_source_fail_exact_join(
    case_name: str,
) -> None:
    work = work_spec()
    run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        checkpoint = handback.evidence_checkpoint
        assert checkpoint is not None and handback.status == "preadmission_ready"
        sources = checkpoint.authority_sources
        families = checkpoint.admitted_families
        assert len({source.observation_digest for source in sources}) == 3
        for source in sources:
            RW0AuthorityVerificationObservationV1.from_mapping(source.to_mapping())
        for index in (6, 7, 13):
            families[index].validate()
        alternate = _alternate_same_role_authority(sources[0])
        assert alternate.to_mapping() != sources[0].to_mapping()
        assert (alternate.effect_class, alternate.effect_fence_ref,
                alternate.effect_fence_digest) == (
                    sources[0].effect_class, sources[0].effect_fence_ref,
                    sources[0].effect_fence_digest,
                )
        author = handback.d1_handback.author_command
        validate_authority_observation(
            basis=handback.d1_handback.phase_basis, observation=alternate,
            attempt_fence=author.attempt_fence,
            author_effect_fence=author.effect_fence,
            current_effect_fence=checkpoint.bound_effects[0].current_fence,
            author_command=author.worker_command,
            capsule_manifest=checkpoint.capsule_manifest,
            cancellation_target=None, now_utc=alternate.observed_at,
        )
        def swapped(items: tuple[object, ...], left: int, right: int) -> tuple[object, ...]:
            out = list(items)
            out[left], out[right] = out[right], out[left]
            return tuple(out)
        cases = {
            "validation_review_sources": {
                "authority_sources": swapped(sources, 0, 1),
            },
            "validation_author_sources": {
                "authority_sources": swapped(sources, 0, 2),
            },
            "review_author_sources": {
                "authority_sources": swapped(sources, 1, 2),
            },
            "duplicate_source": {
                "authority_sources": (sources[0], sources[0], sources[2]),
            },
            "validation_review_families": {
                "admitted_families": swapped(families, 6, 7),
            },
            "source_family_pairs": {
                "authority_sources": swapped(sources, 0, 1),
                "admitted_families": swapped(families, 6, 7),
            },
            "same_role_alternate": {
                "authority_sources": (alternate, sources[1], sources[2]),
            },
        }
        changes = cases[case_name]
        database = Path(run._d1_run.location.database_path)
        database_before = hashlib.sha256(database.read_bytes()).hexdigest()
        child_ids = tuple(item.pid for item in handback.child_outcomes)
        with pytest.raises(ValueError, match="^invalid_d2_evidence_checkpoint$"):
            replace(checkpoint, **changes)
        forged = _forge_exact_value(checkpoint, **changes)
        with pytest.raises(ValueError, match="^invalid_d2_evidence_checkpoint$"):
            forged.validate()
        assert run.handback is handback
        assert hashlib.sha256(database.read_bytes()).hexdigest() == database_before
        assert tuple(item.pid for item in run.handback.child_outcomes) == child_ids
        if case_name == "same_role_alternate":
            with pytest.raises(SQLiteMutationStoreError):
                replace(families[6], evidence_value=sources[1])
    finally:
        run.close()
        run.close()


def test_final_ready_consumer_revalidates_forged_authority_checkpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
        handback = run.handback
        checkpoint = handback.evidence_checkpoint
        assert checkpoint is not None and handback.status == "preadmission_ready"
        sources = checkpoint.authority_sources
        forged_checkpoint = _forge_exact_value(
            checkpoint, authority_sources=(sources[1], sources[0], sources[2]),
        )
        forged_handback = _forge_exact_value(
            handback, evidence_checkpoint=forged_checkpoint,
        )
        calls: list[object] = []
        original_validate = type(checkpoint).validate

        def observe(value: object) -> None:
            calls.append(value)
            original_validate(value)

        with monkeypatch.context() as patch:
            patch.setattr(type(checkpoint), "validate", observe)
            with pytest.raises(ValueError, match="^invalid_d2_preadmission_handback$"):
                forged_handback.validate()
        assert calls == [forged_checkpoint]
        assert run.handback is handback
        handback.validate()


def test_final_stopped_consumer_revalidates_complete_a_checkpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decoded: list[object] = []
    original_decode = d2_offline.decode_model_response

    def stop_after_real_decode(frame: bytes) -> object:
        decoded.append(original_decode(frame))
        raise ValueError("test_only_after_model_decode")

    with monkeypatch.context() as patch:
        patch.setattr(d2_offline, "decode_model_response", stop_after_real_decode)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        checkpoint = handback.evidence_checkpoint
        assert decoded and checkpoint is not None
        assert handback.status == "stopped"
        assert handback.reason == "model_input_or_normalization_failed"
        assert len(handback.checked_admissions) == 14
        assert len(handback.child_outcomes) == 3
        handback.validate()
        # The real response was decoded before the fault. A new explanation
        # cannot erase the reached D1/A/B facts or cause another durable effect.
        database = Path(run._d1_run.location.database_path)
        database_before = hashlib.sha256(database.read_bytes()).hexdigest()
        child_ids = tuple(item.pid for item in handback.child_outcomes)
        _reject_reason_only(handback, "d1_stopped")
        _reject_reason_only(handback, "unknown_reason")
        with pytest.raises(ValueError, match="^invalid_d2_preadmission_handback$"):
            replace(handback, reason=1)
        assert hashlib.sha256(database.read_bytes()).hexdigest() == database_before
        assert tuple(item.pid for item in handback.child_outcomes) == child_ids
        sources = checkpoint.authority_sources
        forged_checkpoint = _forge_exact_value(
            checkpoint, authority_sources=(sources[1], sources[0], sources[2]),
        )
        forged_handback = _forge_exact_value(
            handback, evidence_checkpoint=forged_checkpoint,
        )
        with pytest.raises(ValueError, match="^invalid_d2_preadmission_handback$"):
            forged_handback.validate()
        assert run.handback is handback
    finally:
        run.close()
        run.close()


def test_late_reason_only_forged_wrapper_fails_explicit_consumption(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = d2_offline.decode_model_response
    decoded: list[object] = []

    def fault_after_decode(frame: bytes) -> object:
        decoded.append(original(frame))
        raise ValueError("test_only_after_real_model_decode")

    with monkeypatch.context() as patch:
        patch.setattr(d2_offline, "decode_model_response", fault_after_decode)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        assert len(decoded) == 1
        assert (handback.status, handback.reason) == (
            "stopped", "model_input_or_normalization_failed",
        )
        assert handback.d1_handback.status == "capsule_ready"
        assert handback.evidence_checkpoint is not None
        assert len(handback.committed_bound_effects) == 2
        assert len(handback.checked_admissions) == 14
        assert len(handback.child_outcomes) == 3
        database = Path(run._d1_run.location.database_path)
        database_before = hashlib.sha256(database.read_bytes()).hexdigest()
        child_ids = tuple(item.pid for item in handback.child_outcomes)
        forged = _forge_exact_value(handback, reason="d1_stopped")
        with pytest.raises(ValueError, match="^invalid_d2_preadmission_handback$"):
            forged.validate()
        assert hashlib.sha256(database.read_bytes()).hexdigest() == database_before
        assert tuple(item.pid for item in handback.child_outcomes) == child_ids
        handback.validate()
    finally:
        run.close()
        run.close()


def test_ready_d1_with_empty_d2_is_not_a_d1_stop() -> None:
    """Pure consumer specimen: this empty D2 tuple was not produced by D2."""
    work = work_spec()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as ready_d1:
        assert ready_d1.handback.status == "capsule_ready"
        with run_rw0_d2_offline(
            work, artificial_fixture(work, planner_behavior="defer"),
        ) as stopped_run:
            early = stopped_run.handback
            assert early.reason == "d1_stopped" and early.child_outcomes == ()
            with pytest.raises(ValueError, match="^invalid_d2_preadmission_handback$"):
                replace(early, d1_handback=ready_d1.handback)
            forged = _forge_exact_value(early, d1_handback=ready_d1.handback)
            with pytest.raises(ValueError, match="^invalid_d2_preadmission_handback$"):
                forged.validate()


def test_d1_cleanup_unresolved_still_propagates_without_d2_facts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ge_nwp_coordinator._rw0_d1_offline as d1_offline

    original = d1_offline.tempfile.TemporaryDirectory

    class CleanupFault:
        def __init__(self, inner: object) -> None:
            self.inner = inner
            self.name = inner.name

        def cleanup(self) -> None:
            self.inner.cleanup()
            raise OSError("test_only_d1_planner_cleanup_failure")

    def planner_only(*args: object, **kwargs: object) -> object:
        inner = original(*args, **kwargs)
        if kwargs.get("prefix") == "rw0-d1-planner-":
            return CleanupFault(inner)
        return inner

    with monkeypatch.context() as patch:
        patch.setattr(d1_offline.tempfile, "TemporaryDirectory", planner_only)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        assert (handback.status, handback.reason) == ("stopped", "d1_stopped")
        assert (handback.d1_handback.status, handback.d1_handback.reason) == (
            "cleanup_unresolved", "process_cleanup_unresolved",
        )
        assert handback.committed_bound_effects == ()
        assert handback.checked_admissions == () and handback.child_outcomes == ()
        handback.validate()
        _reject_reason_only(handback, "writer_cleanup_unresolved")
    finally:
        run.close()


def test_pre_effect_a_failure_has_ready_d1_but_no_d2_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ge_nwp_coordinator._rw0_d2a_offline as d2a

    reached: list[object] = []

    def fail_preimages(*args: object, **_kwargs: object) -> object:
        reached.append(args)
        raise d2a._D2AStop("d1_genesis_mismatch")

    with monkeypatch.context() as patch:
        patch.setattr(d2a, "_preimages", fail_preimages)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        assert len(reached) == 1 and handback.d1_handback.status == "capsule_ready"
        assert (handback.status, handback.reason) == ("stopped", "d1_genesis_mismatch")
        assert handback.committed_bound_effects == ()
        assert handback.checked_admissions == () and handback.child_outcomes == ()
        handback.validate()
        _reject_reason_only(handback, "d1_stopped")
    finally:
        run.close()


@pytest.mark.parametrize(("failed_close", "effects", "checked", "children"), (
    (1, 0, 0, 0),  # first bound effect
    (2, 1, 0, 0),  # second bound effect, after one confirmed proof
    (3, 2, 0, 0),  # first C1 admission, before its checked readback is retained
    (13, 2, 10, 1),  # first admission after the real validator child
    (15, 2, 12, 2),  # first admission after the real reviewer child
))
def test_writer_cleanup_failure_preserves_only_confirmed_a_prefix(
    monkeypatch: pytest.MonkeyPatch, failed_close: int, effects: int,
    checked: int, children: int,
) -> None:
    import ge_nwp_coordinator._rw0_d2a_offline as d2a

    original = d2a.acquire_sqlite_writer_session
    close_calls = 0

    class CloseFault:
        def __init__(self, inner: object) -> None:
            self.inner = inner

        def __getattr__(self, name: str) -> object:
            return getattr(self.inner, name)

        def close(self) -> None:
            nonlocal close_calls
            self.inner.close()
            close_calls += 1
            if close_calls == failed_close:
                raise OSError("test_only_writer_close_failure")

    def acquire(location: object) -> object:
        return CloseFault(original(location))

    with monkeypatch.context() as patch:
        patch.setattr(d2a, "acquire_sqlite_writer_session", acquire)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        assert close_calls == failed_close
        assert (handback.status, handback.reason) == (
            "cleanup_unresolved", "writer_cleanup_unresolved",
        )
        assert handback.d1_handback.status == "capsule_ready"
        assert (len(handback.committed_bound_effects), len(handback.checked_admissions),
                len(handback.child_outcomes)) == (effects, checked, children)
        assert handback.evidence_checkpoint is None
        assert all(child.clean_success and child.cleanup_complete
                   for child in handback.child_outcomes)
        handback.validate()
        _reject_reason_only(handback, "d1_stopped")
    finally:
        run.close()


@pytest.mark.parametrize(("role", "checked", "children"), (
    ("validator", 10, 1), ("reviewer", 12, 2),
))
def test_validator_start_failure_retains_process_cleanup_fact(
    monkeypatch: pytest.MonkeyPatch, role: str, checked: int, children: int,
) -> None:
    original = supervisor.subprocess.Popen

    def refuse_checker(args: object, **kwargs: object) -> object:
        if type(args) is tuple and args[3].endswith("_fake_" + role):
            raise OSError("test_only_checker_start_failure")
        return original(args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(supervisor.subprocess, "Popen", refuse_checker)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        assert (handback.status, handback.reason) == (
            "cleanup_unresolved", "process_cleanup_unresolved",
        )
        assert (len(handback.committed_bound_effects), len(handback.checked_admissions),
                len(handback.child_outcomes)) == (2, checked, children)
        assert handback.child_outcomes[-1].reason == "start_failed"
        assert not handback.child_outcomes[-1].cleanup_complete
        assert all(child.clean_success and child.cleanup_complete
                   for child in handback.child_outcomes[:-1])
        handback.validate()
        _reject_reason_only(handback, "validator_process_failed")
    finally:
        run.close()


@pytest.mark.parametrize("failed_establishment", (1, 2))
def test_partial_bound_effect_failure_keeps_one_real_commit(
    monkeypatch: pytest.MonkeyPatch, failed_establishment: int,
) -> None:
    import ge_nwp_coordinator._rw0_d2a_offline as d2a

    original = d2a._establish_bound
    calls = 0

    def fail_selected(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        if calls == failed_establishment:
            raise d2a._D2AStop("bound_effect_conflict")
        return original(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(d2a, "_establish_bound", fail_selected)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        assert calls == failed_establishment
        assert (handback.status, handback.reason) == ("stopped", "bound_effect_conflict")
        assert (len(handback.committed_bound_effects), len(handback.checked_admissions),
                len(handback.child_outcomes)) == (failed_establishment - 1, 0, 0)
        handback.validate()
        _reject_reason_only(handback, "c1_admission_failed")
        _reject_reason_only(handback, "d1_stopped")
    finally:
        run.close()


@pytest.mark.parametrize(("fail_at", "checked", "children", "wrong_reason"), (
    (0, 0, 0, "bound_effect_conflict"),
    (10, 10, 1, "validator_process_failed"),
    (12, 12, 2, "reviewer_process_failed"),
    (13, 13, 2, "evidence_mismatch"),
))
def test_c1_admission_failure_preserves_exact_reached_prefix(
    monkeypatch: pytest.MonkeyPatch, fail_at: int, checked: int,
    children: int, wrong_reason: str,
) -> None:
    import ge_nwp_coordinator._rw0_d2a_offline as d2a

    original = d2a._admit_and_check
    calls = 0

    def fail_selected(*args: object, **kwargs: object) -> object:
        nonlocal calls
        ordinal = calls
        calls += 1
        if ordinal == fail_at:
            raise d2a._D2AStop("c1_admission_failed")
        return original(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(d2a, "_admit_and_check", fail_selected)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        assert calls == fail_at + 1
        assert (handback.status, handback.reason) == ("stopped", "c1_admission_failed")
        assert (len(handback.committed_bound_effects), len(handback.checked_admissions),
                len(handback.child_outcomes)) == (2, checked, children)
        assert handback.evidence_checkpoint is None
        handback.validate()
        _reject_reason_only(handback, wrong_reason)
    finally:
        run.close()


@pytest.mark.parametrize(("role", "checked", "children", "reason"), (
    ("validator", 10, 1, "validator_process_failed"),
    ("reviewer", 12, 2, "reviewer_process_failed"),
))
def test_real_cancelled_checker_is_a_process_failure(
    monkeypatch: pytest.MonkeyPatch, role: str, checked: int,
    children: int, reason: str,
) -> None:
    import ge_nwp_coordinator._rw0_d2a_offline as d2a

    original = d2a.run_fake_module

    def cancel_target(module: str, request: bytes, **kwargs: object) -> object:
        if module.endswith("_fake_" + role):
            kwargs["cancelled"] = lambda: True
        return original(module, request, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(d2a, "run_fake_module", cancel_target)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        assert (handback.status, handback.reason) == ("stopped", reason)
        assert (len(handback.checked_admissions), len(handback.child_outcomes)) == (
            checked, children,
        )
        assert handback.child_outcomes[-1].reason == "cancelled"
        assert handback.child_outcomes[-1].cleanup_complete
        handback.validate()
        _reject_reason_only(handback, "c1_admission_failed")
        _reject_reason_only(handback, "process_cleanup_unresolved")
    finally:
        run.close()


def test_reconstruction_separation_failure_retains_two_real_children(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ge_nwp_coordinator._rw0_d2a_offline as d2a

    original = d2a._run_checker
    first_root: str | None = None

    def repeat_root(*args: object, **kwargs: object) -> tuple[object, str]:
        nonlocal first_root
        evidence, root = original(*args, **kwargs)
        if kwargs["role"] == "validator":
            first_root = root
            return evidence, root
        assert first_root is not None
        return evidence, first_root

    with monkeypatch.context() as patch:
        patch.setattr(d2a, "_run_checker", repeat_root)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        assert (handback.status, handback.reason) == (
            "stopped", "reconstruction_not_independent",
        )
        assert (len(handback.checked_admissions), len(handback.child_outcomes)) == (13, 2)
        assert all(child.clean_success for child in handback.child_outcomes)
        handback.validate()
        _reject_reason_only(handback, "evidence_mismatch")
    finally:
        run.close()


@pytest.mark.parametrize("stop_reason", ("evidence_incomplete", "evidence_mismatch"))
def test_incomplete_bundle_retains_complete_checked_prefix_without_checkpoint(
    monkeypatch: pytest.MonkeyPatch, stop_reason: str,
) -> None:
    import ge_nwp_coordinator._rw0_d2a_offline as d2a

    original = d2a._RW0D2AAdmittedBundle.validate
    reached: list[object] = []

    def fault_after_validation(bundle: object) -> None:
        original(bundle)
        reached.append(bundle)
        raise d2a._D2AStop(stop_reason)

    with monkeypatch.context() as patch:
        patch.setattr(d2a._RW0D2AAdmittedBundle, "validate", fault_after_validation)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        assert len(reached) == 1
        assert (handback.status, handback.reason) == ("stopped", stop_reason)
        assert (len(handback.committed_bound_effects), len(handback.checked_admissions),
                len(handback.child_outcomes)) == (2, 14, 2)
        assert handback.evidence_checkpoint is None
        handback.validate()
        _reject_reason_only(handback, "model_input_or_normalization_failed")
    finally:
        run.close()


@pytest.mark.parametrize("point", ("before_context", "after_supply"))
def test_model_input_failure_retains_actual_prelaunch_prefix(
    monkeypatch: pytest.MonkeyPatch, point: str,
) -> None:
    target = "current_stop_and_ceiling" if point == "before_context" else "encode_model_request"

    def fail(*_args: object, **_kwargs: object) -> object:
        raise ValueError("test_only_model_input_fault")

    with monkeypatch.context() as patch:
        patch.setattr(d2_offline, target, fail)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        assert (handback.status, handback.reason) == (
            "stopped", "model_input_or_normalization_failed",
        )
        assert handback.evidence_checkpoint is not None
        assert (len(handback.committed_bound_effects), len(handback.checked_admissions),
                len(handback.child_outcomes)) == (2, 14, 2)
        assert (handback.input_context is None) == (point == "before_context")
        assert (handback.evidence_supply is None) == (point == "before_context")
        handback.validate()
        _reject_reason_only(handback, "evidence_mismatch")
        _reject_reason_only(handback, "d1_stopped")
    finally:
        run.close()


def test_real_cancelled_model_is_process_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = d2_offline.run_fake_module

    def cancel_model(module: str, request: bytes, **kwargs: object) -> object:
        assert module.endswith("_fake_review_model")
        kwargs["cancelled"] = lambda: True
        return original(module, request, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(d2_offline, "run_fake_module", cancel_model)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        assert (handback.status, handback.reason) == ("stopped", "model_process_failed")
        assert len(handback.child_outcomes) == 3
        assert handback.model_process.reason == "cancelled"
        assert handback.model_process.cleanup_complete
        handback.validate()
        _reject_reason_only(handback, "model_input_or_normalization_failed")
        _reject_reason_only(handback, "model_process_cleanup_unresolved")
    finally:
        run.close()


def test_model_start_failure_is_cleanup_unresolved_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = supervisor.subprocess.Popen

    def refuse_model(args: object, **kwargs: object) -> object:
        if type(args) is tuple and args[3].endswith("_fake_review_model"):
            raise OSError("test_only_model_start_failure")
        return original(args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(supervisor.subprocess, "Popen", refuse_model)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        assert (handback.status, handback.reason) == (
            "cleanup_unresolved", "model_process_cleanup_unresolved",
        )
        assert len(handback.child_outcomes) == 3
        assert handback.model_process.reason == "start_failed"
        assert not handback.model_process.cleanup_complete
        handback.validate()
        _reject_reason_only(handback, "model_process_failed")
    finally:
        run.close()


def test_model_workspace_cleanup_failure_retains_model_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = d2_offline.tempfile.TemporaryDirectory
    reached: list[object] = []

    class CleanupFault:
        def __init__(self, inner: object) -> None:
            self.inner = inner
            self.name = inner.name

        def cleanup(self) -> None:
            self.inner.cleanup()
            raise OSError("test_only_model_workspace_cleanup_failure")

    def model_only(*args: object, **kwargs: object) -> object:
        inner = original(*args, **kwargs)
        if kwargs.get("prefix") == "rw0-d2-model-":
            reached.append(inner)
            return CleanupFault(inner)
        return inner

    with monkeypatch.context() as patch:
        patch.setattr(d2_offline.tempfile, "TemporaryDirectory", model_only)
        work = work_spec()
        run = run_rw0_d2_offline(work, artificial_fixture(work))
    try:
        handback = run.handback
        assert len(reached) == 1
        assert (handback.status, handback.reason) == (
            "cleanup_unresolved", "model_workspace_cleanup_unresolved",
        )
        assert len(handback.child_outcomes) == 3
        assert handback.model_process.clean_success
        handback.validate()
        _reject_reason_only(handback, "model_process_cleanup_unresolved")
    finally:
        run.close()


def test_five_real_children_have_bounded_lower_process_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launched: list[tuple[tuple[str, ...], dict[str, object]]] = []
    original = supervisor.subprocess.Popen

    def observe(args: object, **kwargs: object) -> object:
        assert type(args) is tuple
        launched.append((args, kwargs.copy()))
        return original(args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(supervisor.subprocess, "Popen", observe)
        work = work_spec()
        with run_rw0_d2_offline(work, artificial_fixture(work)) as run:
            root = str(run._d1_run.location.state_root)
            assert run.handback.status == "preadmission_ready"
    assert tuple(args[3] for args, _ in launched) == (
        "ge_nwp_coordinator._rw0_d1_fake_planner",
        "ge_nwp_coordinator._rw0_d1_fake_worker",
        "ge_nwp_coordinator._rw0_d2a_fake_validator",
        "ge_nwp_coordinator._rw0_d2a_fake_reviewer",
        "ge_nwp_coordinator._rw0_d2b_fake_review_model",
    )
    assert len(launched) == 5
    for args, kwargs in launched:
        assert args[1:3] == ("-B", "-m")
        assert kwargs["shell"] is False
        assert kwargs["start_new_session"] is True
        assert kwargs["close_fds"] is True and kwargs["pass_fds"] == ()
        assert root not in str(args) and root not in str(kwargs["cwd"])
        env = kwargs["env"]
        assert type(env) is dict
        assert set(env) == {
            "PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "PYTHONIOENCODING",
            "LANG", "LC_ALL", "__CF_USER_TEXT_ENCODING", "TMPDIR",
        }
        assert root not in str(tuple(env.values()))


@pytest.mark.parametrize(("contract", "recommendation"), (
    (b"package contracts\n\nfunc TestContract() {}\n", "accept_candidate"),
    (b"package contracts\n\nfunc TestContract() {}\n// UNSAFE-CHANGE\n", "repair_candidate"),
    (b"package contracts\n\nfunc TestContract() {}\n// VALIDATION-REPLAN\n", "replan"),
    (b"package contracts\n\nfunc TestContract() {}\n// VALIDATION-TERMINAL\n", "terminal_reject"),
    (b"package contracts\n\nfunc TestContract() {}\n// VALIDATION-UNCLASSIFIED\n", "block"),
))
def test_five_recommendations_come_from_actual_candidate_bytes(
    contract: bytes, recommendation: str,
) -> None:
    work = work_spec()
    fixture = artificial_fixture(work)
    fixture = replace(fixture, base_entries=(
        fixture.base_entries[0], fixture.base_entries[1],
        (fixture.base_entries[2][0], contract, "100644"),
    ))
    with run_rw0_d2_offline(work, fixture) as run:
        handback = run.handback
        handback.validate()
        assert handback.status == "preadmission_ready", handback.reason
        assert handback.proposal.recommendation == recommendation
        assert handback.private_artifact.recommendation == recommendation


def _repair_candidate_fixture(work: object) -> object:
    fixture = artificial_fixture(work)
    return replace(fixture, base_entries=(
        fixture.base_entries[0], fixture.base_entries[1],
        (fixture.base_entries[2][0],
         b"package contracts\n\nfunc TestContract() {}\n// UNSAFE-CHANGE\n", "100644"),
    ))


def _full_b_transplant(recipient: object, donor: object) -> dict[str, object]:
    changes = {name: getattr(donor, name) for name in d2_handback._B_ORDER}
    changes["child_outcomes"] = (
        *recipient.child_outcomes[:2], donor.child_outcomes[2],
    )
    return changes


def _assert_pure_rejection(
    monkeypatch: pytest.MonkeyPatch, recipient: object,
    changes: dict[str, object], runs: tuple[object, ...],
) -> None:
    before = tuple(hashlib.sha256(Path(run._d1_run.location.database_path).read_bytes())
                   .hexdigest() for run in runs)
    child_ids = tuple(tuple(child.pid for child in run.handback.child_outcomes)
                      for run in runs)
    def unexpected(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("validation_attempted_external_effect")
    with monkeypatch.context() as patch:
        patch.setattr(sqlite3, "connect", unexpected)
        patch.setattr(supervisor.subprocess, "Popen", unexpected)
        patch.setattr(d2_offline, "acquire_sqlite_writer_session", unexpected)
        with pytest.raises(ValueError, match="^invalid_d2_preadmission_handback$"):
            replace(recipient, **changes)
        with pytest.raises(ValueError, match="^invalid_d2_preadmission_handback$"):
            _forge_exact_value(recipient, **changes).validate()
    assert before == tuple(
        hashlib.sha256(Path(run._d1_run.location.database_path).read_bytes())
        .hexdigest() for run in runs
    )
    assert child_ids == tuple(tuple(child.pid for child in run.handback.child_outcomes)
                              for run in runs)
    for run in runs:
        run.handback.validate()


def test_final_consumer_binds_full_ready_b_graph_to_retained_a(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    runs = []
    try:
        alpha = run_rw0_d2_offline(work, artificial_fixture(work))
        runs.append(alpha)
        beta = run_rw0_d2_offline(work, _repair_candidate_fixture(work))
        runs.append(beta)
        a, b = alpha.handback, beta.handback
        assert a.proposal.recommendation == "accept_candidate"
        assert b.proposal.recommendation == "repair_candidate"
        assert a.evidence_checkpoint.capsule_manifest.to_mapping() != (
            b.evidence_checkpoint.capsule_manifest.to_mapping()
        )
        assert a.d1_handback is a.evidence_checkpoint.d1_handback
        a.validate()
        b.validate()
        # Every donor role is an actual, individually valid B owner. Its
        # different canonical values and supports are measured independently
        # of the new consuming predicate.
        role_names = (
            "candidate_capsule", "worker_result", "validation_result",
            "independent_review", "standing_policy", "risk_lane",
            "authority_currentness_attestation", "global_stop", "effect_ceiling",
        )
        assert tuple(item.role for item in b.input_context.role_entries) == role_names
        assert tuple(item.support_value_count for item in b.evidence_supply.role_supplies) == (
            0, 0, 6, 7, 4, 4, 0, 2, 5,
        )
        assert all(
            a.evidence_supply.role_supplies[index].to_mapping()["typed_canonical_value"]
            != b.evidence_supply.role_supplies[index].to_mapping()["typed_canonical_value"]
            for index in range(9)
        )
        assert (
            a.input_context.role_entries[1].direct_c1_membership_digest
            != b.input_context.role_entries[1].direct_c1_membership_digest
        )
        assert (
            a.evidence_supply.role_supplies[3].to_mapping()["support_canonical_values"]
            != b.evidence_supply.role_supplies[3].to_mapping()["support_canonical_values"]
        )
        _assert_pure_rejection(monkeypatch, a, _full_b_transplant(a, b), tuple(runs))

        # This source is checked inside the A checkpoint and does not appear
        # in the nine B roles. It isolates the final checkpoint revalidation
        # from the new A-to-B relation in the J02 omission control.
        assert a.evidence_checkpoint.readiness_source.to_mapping() != (
            b.evidence_checkpoint.readiness_source.to_mapping()
        )
        forged_checkpoint = _forge_exact_value(
            a.evidence_checkpoint,
            readiness_source=b.evidence_checkpoint.readiness_source,
        )
        with pytest.raises(ValueError, match="^invalid_d2_preadmission_handback$"):
            _forge_exact_value(a, evidence_checkpoint=forged_checkpoint).validate()

        # Independently allocated, canonically identical B values remain
        # valid. The handback is not bound to Python object addresses.
        rebuilt_context = type(a.input_context).from_mapping(a.input_context.to_mapping())
        rebuilt_supply = type(a.evidence_supply).from_mapping(a.evidence_supply.to_mapping())
        assert rebuilt_context is not a.input_context
        assert rebuilt_supply is not a.evidence_supply
        rebuilt = replace(
            a, input_context=rebuilt_context, evidence_supply=rebuilt_supply,
            model_input_binding=replace(a.model_input_binding),
            model_source_invocation=replace(a.model_source_invocation),
            private_artifact=replace(a.private_artifact),
            artifact_binding=replace(a.artifact_binding),
            safe_projection=replace(a.safe_projection),
            evidence_bindings=tuple(replace(item) for item in a.evidence_bindings),
            evidence_set=replace(a.evidence_set), proposal=replace(a.proposal),
        )
        rebuilt.validate()
        assert rebuilt.proposal.recommendation == a.proposal.recommendation
    finally:
        for run in reversed(runs):
            run.close()


def test_final_consumer_binds_paired_input_in_stopped_and_cleanup_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    runs = []
    original_encode = d2_offline.encode_model_request
    original_temp = d2_offline.tempfile.TemporaryDirectory

    def stop_after_pair(*_args: object, **_kwargs: object) -> object:
        raise ValueError("test_only_after_pair")

    class CleanupFault:
        def __init__(self, inner: object) -> None:
            self.inner = inner
            self.name = inner.name

        def cleanup(self) -> None:
            self.inner.cleanup()
            raise OSError("test_only_model_workspace_cleanup_failure")

    def cleanup_model(*args: object, **kwargs: object) -> object:
        inner = original_temp(*args, **kwargs)
        return CleanupFault(inner) if kwargs.get("prefix") == "rw0-d2-model-" else inner

    try:
        donor = run_rw0_d2_offline(work, _repair_candidate_fixture(work))
        runs.append(donor)
        with monkeypatch.context() as patch:
            patch.setattr(d2_offline, "encode_model_request", stop_after_pair)
            stopped = run_rw0_d2_offline(work, artificial_fixture(work))
        runs.append(stopped)
        with monkeypatch.context() as patch:
            patch.setattr(d2_offline.tempfile, "TemporaryDirectory", cleanup_model)
            cleanup = run_rw0_d2_offline(work, artificial_fixture(work))
        runs.append(cleanup)
        b = donor.handback
        for run, expected in (
            (stopped, ("stopped", "model_input_or_normalization_failed")),
            (cleanup, ("cleanup_unresolved", "model_workspace_cleanup_unresolved")),
        ):
            recipient = run.handback
            assert (recipient.status, recipient.reason) == expected
            assert recipient.evidence_checkpoint is not None
            assert recipient.input_context is not None
            assert recipient.evidence_supply is not None
            assert len(recipient.child_outcomes) == (2 if run is stopped else 3)
            recipient.validate()
            _assert_pure_rejection(monkeypatch, recipient, {
                "input_context": b.input_context,
                "evidence_supply": b.evidence_supply,
            }, tuple(runs))
    finally:
        for run in reversed(runs):
            run.close()


def test_final_consumer_rejects_same_capsule_non_capsule_b_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    runs = []
    try:
        first = run_rw0_d2_offline(work, artificial_fixture(work))
        runs.append(first)
        second = run_rw0_d2_offline(work, artificial_fixture(work))
        runs.append(second)
        a, b = first.handback, second.handback
        assert a.evidence_checkpoint.capsule_manifest.to_mapping() == (
            b.evidence_checkpoint.capsule_manifest.to_mapping()
        )
        assert a.input_context.role_entries[0].typed_value_digest == (
            b.input_context.role_entries[0].typed_value_digest
        )
        assert a.proposal.recommendation == b.proposal.recommendation
        # Actual distinct checked classification and review producer evidence,
        # with the same capsule, make the noncapsule relation observable.
        assert a.checked_admissions[5].admission_result.value_digest != (
            b.checked_admissions[5].admission_result.value_digest
        )
        assert a.evidence_checkpoint.review_source.observation.to_mapping() != (
            b.evidence_checkpoint.review_source.observation.to_mapping()
        )
        assert a.evidence_supply.role_supplies[3].to_mapping()["support_canonical_values"] != (
            b.evidence_supply.role_supplies[3].to_mapping()["support_canonical_values"]
        )
        a.validate()
        b.validate()
        _assert_pure_rejection(monkeypatch, a, _full_b_transplant(a, b), tuple(runs))
    finally:
        for run in reversed(runs):
            run.close()
