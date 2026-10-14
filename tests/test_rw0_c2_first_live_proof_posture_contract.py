"""Finite causal checks for the unimplemented first-live support profile.

These hand-authored snapshots test contract logic, not a platform supplier or
the existing C2 reducer. No event interpreter or production source is imported.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / ".docs/rw0-c2-first-live-proof-posture.md"


@dataclass(frozen=True)
class _Proof:
    policy_admitted: bool = False
    enrollment: str | None = None
    incarnation: str | None = None
    activation_attempted: bool = False
    admission_recorded: bool = False
    original_state: bool = False
    supervisor_live: bool = False
    current_source: bool = False
    continuity_lost: bool = False
    closed: bool = False
    acceptances: int = 0


def _may_first_activate(proof: _Proof, requested: str) -> bool:
    return (
        proof.policy_admitted
        and proof.enrollment == requested
        and not proof.activation_attempted
        and proof.original_state
        and proof.supervisor_live
        and proof.current_source
        and not proof.continuity_lost
        and not proof.closed
    )


def _may_command(proof: _Proof) -> bool:
    return (
        proof.policy_admitted
        and proof.enrollment is not None
        and proof.incarnation == proof.enrollment
        and proof.activation_attempted
        and proof.admission_recorded
        and proof.original_state
        and proof.supervisor_live
        and proof.current_source
        and not proof.continuity_lost
        and not proof.closed
    )


def _may_accept(proof: _Proof, *, exhaustive_unclaimed: bool) -> bool:
    return _may_command(proof) and exhaustive_unclaimed and proof.acceptances == 0


def _active() -> _Proof:
    return _Proof(
        policy_admitted=True,
        enrollment="incarnation-1",
        incarnation="incarnation-1",
        activation_attempted=True,
        admission_recorded=True,
        original_state=True,
        supervisor_live=True,
        current_source=True,
    )


def test_owner_scope_and_finite_history_anchors() -> None:
    owner = OWNER.read_text(encoding="utf-8")
    assert owner.count("rw0-c2-single-realization-proof-v1") >= 1
    assert owner.count("Classification: `ACCEPTED TARGET / FIRST-LIVE SUPPORT PROFILE`; unimplemented.") == 1
    assert "The eleven private schemas and receipt-graph profile" in owner
    assert "No per-admission-write or\nper-acceptance-write external arm is selected." in owner
    assert "no\ngeneral external checkpoint" in owner
    assert "A fixture cannot satisfy this platform gate." in owner
    for history in (
        "D-repeat", "Enroll-before-program", "Lost-activation-response",
        "Copied-state", "Late-response", "Nonaccept-four", "First-then-second",
        "Lost-commit-response", "Restored-preaccept", "Restart",
        "In-place-restore", "Fence-request", "Preaccept-failure",
        "Normal-close", "ES-later",
    ):
        assert owner.count(f"| {history} | ") == 1


def test_repeatable_offline_runs_are_not_live_enrollment() -> None:
    history = (
        ("offline fake run 1", _Proof()),
        ("offline reset and fake run 2", _Proof()),
    )
    assert [name for name, _ in history] == [
        "offline fake run 1", "offline reset and fake run 2"
    ]
    assert all(proof.enrollment is None and not _may_command(proof) for _, proof in history)


def test_authenticated_enrollment_and_separate_admission_precede_program() -> None:
    policy = _Proof(policy_admitted=True)
    enrolled = replace(
        policy, enrollment="incarnation-1", original_state=True,
        supervisor_live=True, current_source=True,
    )
    activated = replace(enrolled, incarnation="incarnation-1", activation_attempted=True)
    admission = replace(activated, admission_recorded=True)
    history = (
        ("standing-policy admission", policy),
        ("independent non-reissuable enrollment", enrolled),
        ("first activation", activated),
        ("program-independent admission fact", admission),
        ("program created later", admission),
    )
    assert _may_first_activate(history[1][1], "incarnation-1")
    assert not _may_command(history[2][1])
    assert _may_command(history[3][1])
    assert history[3][0] == "program-independent admission fact"
    assert history[4][0] == "program created later"


def test_lost_activation_response_cannot_trigger_second_launch() -> None:
    uncertain = replace(_active(), admission_recorded=False, current_source=False)
    history = ("enrollment persisted", "activation may have started", "response lost")
    assert history[-1] == "response lost"
    assert not _may_first_activate(uncertain, "incarnation-1")
    assert not _may_first_activate(uncertain, "incarnation-2")
    assert not _may_command(uncertain)


def test_copied_database_and_late_old_response_have_no_authority() -> None:
    original = _active()
    copied = replace(original, original_state=False, current_source=False)
    late = replace(original, incarnation="incarnation-2", current_source=False)
    history = (
        ("original guarded process", original),
        ("same bytes on another host", copied),
        ("old response presented to new process", late),
    )
    assert _may_command(history[0][1])
    assert not _may_command(history[1][1])
    assert not _may_command(history[2][1])


def test_four_nonaccept_branches_need_no_checkpoint_or_unclaimed_claim() -> None:
    history = (
        ("candidate_repair", _active()),
        ("attempt_selecting_replan", _active()),
        ("program_terminal_reject", _active()),
        ("post_execution_program_block", _active()),
    )
    external_writes = ("one preactivation incarnation enrollment",)
    assert len(history) == 4
    assert all(_may_command(proof) and proof.acceptances == 0 for _, proof in history)
    assert external_writes == ("one preactivation incarnation enrollment",)


def test_first_acceptance_commits_once_across_programs() -> None:
    before = _active()
    after = replace(before, acceptances=1)
    history = (("program A acceptance candidate", before), ("program B candidate", after))
    assert _may_accept(history[0][1], exhaustive_unclaimed=True)
    assert not _may_accept(history[1][1], exhaustive_unclaimed=True)
    assert not _may_accept(history[0][1], exhaustive_unclaimed=False)


def test_lost_commit_response_uses_original_custody_readback() -> None:
    before = _active()
    committed = replace(before, acceptances=1)
    history = (("commit attempted", before), ("response lost", committed))
    assert _may_command(history[1][1])
    assert history[1][1].acceptances == 1
    assert not _may_accept(history[1][1], exhaustive_unclaimed=True)
    assert history[1][0] == "response lost"
    assert history[1][1].original_state and history[1][1].current_source


def test_identical_preaccept_bytes_after_restore_do_not_restore_custody() -> None:
    preaccept = _active()
    restored = replace(preaccept, original_state=False, current_source=False,
                       continuity_lost=True)
    history = (("preaccept original bytes", preaccept),
               ("identical bytes restored later", restored))
    assert history[0][1].acceptances == history[1][1].acceptances == 0
    assert _may_accept(preaccept, exhaustive_unclaimed=True)
    assert not _may_command(restored)
    assert not _may_accept(restored, exhaustive_unclaimed=True)


def test_process_and_supervisor_restart_retire_without_synthetic_outcome() -> None:
    process_restart = replace(_active(), current_source=False, continuity_lost=True)
    supervisor_restart = replace(_active(), supervisor_live=False, continuity_lost=True)
    history = (("process restarted", process_restart),
               ("supervisor identity lost", supervisor_restart))
    assert all(not _may_command(proof) for _, proof in history)
    assert all(not _may_first_activate(proof, "incarnation-1") for _, proof in history)
    assert all(proof.acceptances == 0 for _, proof in history)


def test_in_place_and_memory_restore_invalidate_live_custody() -> None:
    in_place = replace(_active(), current_source=False, continuity_lost=True)
    memory = replace(_active(), current_source=False, continuity_lost=True)
    history = (("SQLite in-place rollback", in_place),
               ("VM memory checkpoint restored", memory))
    assert all(not _may_command(proof) for _, proof in history)


def test_fence_request_without_completion_cannot_authorize_successor() -> None:
    history = ("fence requested", "old subtree may still run", "storage exclusion unproved")
    subtree_exit_observed = False
    storage_exclusion_observed = False
    fence_complete = subtree_exit_observed and storage_exclusion_observed
    assert history[-1] == "storage exclusion unproved"
    assert not fence_complete
    assert not _may_first_activate(_active(), "incarnation-2")
    assert not _may_first_activate(_active(), "incarnation-1")


def test_preaccept_failure_retires_availability_not_allowance_fact() -> None:
    failed = replace(_active(), current_source=False, continuity_lost=True)
    history = (("enrolled and active", _active()),
               ("custody failed before acceptance", failed))
    assert not _may_command(history[1][1])
    assert history[1][1].acceptances == 0
    assert not _may_first_activate(history[1][1], "incarnation-1")


def test_normal_terminal_close_and_later_es_do_not_renew() -> None:
    accepted = replace(_active(), acceptances=1)
    closed = replace(accepted, closed=True)
    history = (("direct-local acceptance", accepted),
               ("terminal close", closed),
               ("later separately governed ES route", closed))
    assert not _may_first_activate(history[1][1], "incarnation-1")
    assert not _may_accept(history[2][1], exhaustive_unclaimed=True)
    assert history[2][1].enrollment == "incarnation-1"
    assert history[2][1].acceptances == 1


def test_six_direct_causal_counterexamples() -> None:
    # Each intentionally broken rule changes an independently expected denial.
    absent = replace(_active(), enrollment=None)
    assert not _may_command(absent)
    bad_without_enrollment = absent.policy_admitted and absent.activation_attempted
    assert bad_without_enrollment  # incorrectly admits an unenrolled lineage

    copied = replace(_active(), original_state=False, current_source=False)
    assert not _may_command(copied)
    bad_copied_session = copied.incarnation == copied.enrollment
    assert bad_copied_session  # incorrectly treats a copied identity as live custody

    missing = replace(_active(), current_source=False)
    assert not _may_command(missing)
    bad_default_positive = missing.original_state and (missing.current_source or True)
    assert bad_default_positive  # incorrectly defaults missing posture to positive

    restarted = replace(_active(), continuity_lost=True)
    assert not _may_command(restarted)
    bad_restart = (
        restarted.enrollment == restarted.incarnation
        and restarted.supervisor_live and restarted.current_source
    )
    assert bad_restart  # incorrectly ignores irreversible loss

    commit_attempt_with_timeout = ("commit attempted", "response timed out")
    observed_whole_family_absence = False
    bad_noncommit_inference = commit_attempt_with_timeout[-1] == "response timed out"
    assert bad_noncommit_inference and not observed_whole_family_absence

    coordinator_branch = "candidate_repair"
    enforcer_claim = "candidate_acceptance"
    bad_enforcer_branch = enforcer_claim
    assert bad_enforcer_branch != coordinator_branch
    assert _active().acceptances == 0  # an enforcer claim writes no acceptance fact


def test_owner_routing_and_compatibility_are_explicit() -> None:
    guard = (ROOT / ".docs/rw0-c2-bootstrap-acceptance-guard-semantic-contract.md").read_text()
    value = (ROOT / ".docs/rw0-c2-private-value-versioning.md").read_text()
    operating = (ROOT / ".docs/autonomous-software-development-operating-model.md").read_text()
    recovery = (ROOT / ".docs/sqlite-operations-and-recovery.md").read_text()
    phase = (ROOT / ".docs/rw0-remote-worker-contact-phase-entry.md").read_text()
    assert "rw0-c2-single-realization-proof-v1" in guard
    assert "the separate provisioner owns its creation and repair" not in value
    assert "with no replacement, renewal, orphan repair, or implicit\nretry" in value
    assert "single-realization custody posture" in operating
    assert "Ordinary B1 administration is unaffected." in recovery
    assert "| offline process/custody mechanics and fake capability behavior | RW0-D |" in phase
    assert "| first-live independent enrollment supplier, continuous original process/storage custody, and complete fencing conformance | RW0-E |" in phase
