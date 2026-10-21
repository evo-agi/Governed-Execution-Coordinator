"""One real D1-to-D2A evidence sequence in a disposable owner database."""

from __future__ import annotations

from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture, run_rw0_d1_offline
from ge_nwp_coordinator._rw0_d2a_offline import run_d2a_checked_evidence
from ge_nwp_coordinator._sqlite_rw0_c1 import RW0D2CurrentOwnerSnapshotV1
from ge_nwp_coordinator.sqlite_writer_session import acquire_sqlite_writer_session
from ge_nwp_coordinator._rw0_d2a_evidence import (
    checked_reviewer_separation, checking_disposition, checking_result_set,
)
from ge_nwp_coordinator._development_author_effect_establishment_contracts import (
    _development_author_effect_establishment_write_plan,
)
from test_rw0_d1_offline_integration import work_spec


def test_fourteen_checked_members_and_two_independent_children() -> None:
    work = work_spec()
    fixture = artificial_fixture(work)
    with run_rw0_d1_offline(work, fixture) as run:
        bundle = run_d2a_checked_evidence(run, work, fixture)
        bundle.validate()
        with acquire_sqlite_writer_session(run.location) as writer:
            current = writer._read_rw0_d2_current_owner_snapshot(
                run.handback.phase_basis,
            )
        assert type(current) is RW0D2CurrentOwnerSnapshotV1
        current.validate()
        assert current.global_stop.status.value == "clear"
        checkpoint = bundle.checkpoint
        checkpoint.validate()
        assert len(checkpoint.bound_effects) == 2
        assert len(checkpoint.policy_sources) == 5
        assert len(checkpoint.policy_matrices) == 2
        assert tuple(len(source.entries) for source in checkpoint.support_sets) == (2, 2, 3, 4, 4)
        assert len(bundle.checked_families) == 14
        assert sorted(family.admission_result.kind_rank for family in bundle.checked_families) == (
            [1] * 3 + [5] + [6] * 2 + [12] * 6 + [13] + [14]
        )
        validation, review = bundle.checking_evidence
        assert validation.role == "validator" and review.role == "reviewer"
        assert validation.process.pid != review.process.pid
        assert validation.observation.outcome == "passed"
        assert review.observation.outcome == "passed"
        separation, separation_support = checked_reviewer_separation(
            checked_families=bundle.checked_families,
            capsule_manifest=run.handback.capsule_manifest,
        )
        assert separation.status == "separate"
        assert len(separation_support.entries) == 2
        author_plan = _development_author_effect_establishment_write_plan(
            run.handback.author_command,
            run.handback.author_result.transaction_timestamp,
        )
        for evidence, qualifier in zip(
            bundle.checking_evidence,
            (bundle.checked_families[9].evidence_value,
             bundle.checked_families[11].evidence_value), strict=True,
        ):
            result_set = checking_result_set(
                evidence=evidence, qualification=qualifier,
                expires_at="2099-01-01T00:00:00Z",
            )
            disposition, support = checking_disposition(
                evidence=evidence, result_set=result_set, qualification=qualifier,
                semantic_attempt_digest=author_plan.semantic_attempt.semantic_attempt_digest,
                attempt_number=1,
                reviewer_separation=separation if evidence.role == "reviewer" else None,
            )
            assert result_set.result == "passed"
            assert disposition.result == "passed"
            assert len(support.entries) == (2 if evidence.role == "validator" else 3)
