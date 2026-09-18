"""Pure B1 relations over exact supplied C2A and B1 values."""

from __future__ import annotations

import pytest

import ge_nwp_coordinator._rw0_phase_entry_semantic_values as b1
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1, EffectFenceV1, WorkSpecV1, WorkerCommandV1,
)
from tests.c2a_contract_support import (
    _effect_fence_for_vector, _full_record, _reseal_single_digest_record,
)
from test_rw0_b1_vectors import mapping_for

NOW = "2029-01-01T00:00:00Z"
EFFECT_CLASSES = (
    "author_candidate", "cancel_effect", "local_git_commit",
    "review_candidate", "validate_candidate",
)


def value(cls: type, **changes: object):
    return cls.from_mapping(mapping_for(cls, **changes))


def graph():
    work = WorkSpecV1.from_mapping(_full_record("WorkSpecV1"))
    attempt = AttemptFenceV1.from_mapping(_full_record("AttemptFenceV1"))
    effect = EffectFenceV1.from_mapping(_effect_fence_for_vector("author"))
    command = WorkerCommandV1.from_mapping(_full_record("WorkerCommandV1"))
    return work, attempt, effect, command


def claims():
    work, attempt, effect, command = graph()
    lineage = mapping_for(b1.RW0PhaseEntryBasisV1)["c2b3d_lineage"]
    for owner in (work, attempt, effect, command):
        record = owner.to_mapping()
        for name in b1._L34_FIELDS:
            if name in record:
                lineage[name] = record[name]
    lineage["author_command_ref"] = command.command_ref
    lineage["author_command_digest"] = command.command_digest
    lineage["effect_intent_ref"] = effect.effect_intent_ref
    lineage["semantic_attempt_ref"] = attempt.semantic_attempt_ref
    key = [[field, lineage[field]] for field in b1._K8_FIELDS]
    path = b1._path_scope_binding_digest(work.authorized_paths)
    basis = value(b1.RW0PhaseEntryBasisV1, c2b3d_lineage=lineage,
                  selection_key=key, path_scope_digest=path,
                  global_stop_ref=attempt.global_stop_ref,
                  global_stop_version=attempt.global_stop_version)
    observation = value(
        b1.RW0AuthorityVerificationObservationV1,
        phase_basis_ref=basis.basis_ref, phase_basis_digest=basis.basis_digest,
        parent_grant_ref=attempt.parent_standing_grant_ref,
        parent_grant_digest=attempt.parent_standing_grant_digest,
        attempt_basis_ref=attempt.attempt_authorization_ref,
        attempt_basis_digest=attempt.attempt_authorization_digest,
        effect_basis_ref=effect.effect_authorization_ref,
        effect_basis_digest=effect.effect_authorization_digest,
        attempt_fence_ref=attempt.attempt_fence_ref,
        attempt_fence_digest=attempt.attempt_fence_digest,
        effect_fence_ref=effect.effect_fence_ref,
        effect_fence_digest=effect.effect_fence_digest,
        audience_ref=attempt.program_ref,
        repository_ref=attempt.repository_ref,
        base_git_object_format=attempt.base_git_object_format,
        base_git_oid=attempt.base_git_oid,
        path_scope_digest=path,
        allowed_effect_classes=list(EFFECT_CLASSES),
        parent_ceilings=attempt.aggregate_ceilings.to_mapping(),
        effect_class=effect.effect_class,
        grant_expires_at="2030-01-01T00:00:00Z",
        observed_at="2028-01-01T00:00:00Z",
        observation_expires_at="2030-01-01T00:00:00Z",
        current_effect_head_digest=basis.current_effect_head_digest,
        current_delivery_head_digest=basis.current_delivery_head_digest,
        global_stop_ref=basis.global_stop_ref,
        global_stop_version=basis.global_stop_version,
        global_stop_state=basis.global_stop_state,
    )
    proposal = value(
        b1.RW0SubordinateAuthorizationProposalV1,
        phase_basis_ref=basis.basis_ref, phase_basis_digest=basis.basis_digest,
        verification_ref=observation.observation_ref,
        verification_digest=observation.observation_digest,
        parent_grant_ref=observation.parent_grant_ref,
        parent_grant_digest=observation.parent_grant_digest,
        grant_family_ref=observation.grant_family_ref,
        grant_family_digest=observation.grant_family_digest,
        attempt_basis_ref=observation.attempt_basis_ref,
        attempt_basis_digest=observation.attempt_basis_digest,
        effect_basis_ref=observation.effect_basis_ref,
        effect_basis_digest=observation.effect_basis_digest,
        attempt_fence_ref=attempt.attempt_fence_ref,
        attempt_fence_digest=attempt.attempt_fence_digest,
        effect_fence_ref=effect.effect_fence_ref,
        effect_fence_digest=effect.effect_fence_digest,
        audience_ref=attempt.program_ref,
        repository_ref=attempt.repository_ref,
        base_git_object_format=attempt.base_git_object_format,
        base_git_oid=attempt.base_git_oid,
        path_scope_digest=path,
        effect_class=effect.effect_class,
        ceilings=effect.effect_ceilings.to_mapping(),
        expires_at="2029-12-01T00:00:00Z",
        global_stop_ref=basis.global_stop_ref,
        global_stop_version=basis.global_stop_version,
    )
    return basis, observation, proposal, work, attempt, effect, command


def error(expected: str, action) -> None:
    with pytest.raises(b1.RW0PhaseValueError) as caught:
        action()
    assert caught.value.reason == expected
    assert caught.value.__cause__ is None


def exact_relation_budget(monkeypatch: pytest.MonkeyPatch, limit: int, action) -> None:
    original = b1._WorkBudget
    instances = []
    class Measured(original):
        def __init__(self, given: int) -> None:
            assert given == limit
            super().__init__(given)
            instances.append(self)
    monkeypatch.setattr(b1, "_WorkBudget", Measured)
    try:
        assert action() is None
        assert len(instances) == 1
        assert instances[0].remaining == 0
        class OneLess(original):
            def __init__(self, given: int) -> None:
                assert given == limit
                super().__init__(given - 1)
        monkeypatch.setattr(b1, "_WorkBudget", OneLess)
        error("cumulative_work_exhausted", action)
    finally:
        monkeypatch.setattr(b1, "_WorkBudget", original)


def test_all_thirteen_relations_are_present() -> None:
    names = (
        "validate_phase_entry_basis", "validate_authority_observation",
        "validate_per_fence_basis", "validate_external_common_family_claim",
        "validate_subordinate_narrowing", "validate_custody_binding",
        "validate_retrieval_event_sequence", "validate_host_qualification",
        "validate_terminal_outcome_binding", "validate_normal_outcome_shape",
        "validate_reconciled_cancel_outcome_shape",
        "validate_unresolved_cancel_outcome_shape",
        "validate_unusable_cancel_basis_outcome_shape",
    )
    assert all(callable(getattr(b1, name)) for name in names)


def test_per_fence_and_family_claim_positive_and_mutants(monkeypatch: pytest.MonkeyPatch) -> None:
    basis, obs, proposal, _, attempt, effect, _ = claims()
    assert b1.validate_per_fence_basis(observation=obs, proposal=proposal,
                                       attempt_fence=attempt, current_effect_fence=effect) is None
    assert b1.validate_external_common_family_claim(
        observation=obs, proposal=proposal, attempt_fence=attempt,
        current_effect_fence=effect) is None
    exact_relation_budget(monkeypatch, 110, lambda: b1.validate_per_fence_basis(
        observation=obs, proposal=proposal, attempt_fence=attempt,
        current_effect_fence=effect))
    exact_relation_budget(monkeypatch, 110, lambda: b1.validate_external_common_family_claim(
        observation=obs, proposal=proposal, attempt_fence=attempt,
        current_effect_fence=effect))
    bad = value(b1.RW0SubordinateAuthorizationProposalV1,
                **{**proposal.identity_mapping(), "effect_basis_digest": "a" * 64})
    error("per_fence_basis_mismatch", lambda: b1.validate_per_fence_basis(
        observation=obs, proposal=bad, attempt_fence=attempt, current_effect_fence=effect))
    family = value(b1.RW0SubordinateAuthorizationProposalV1,
                   **{**proposal.identity_mapping(), "grant_family_digest": "a" * 64})
    error("common_family_unverified", lambda: b1.validate_external_common_family_claim(
        observation=obs, proposal=family, attempt_fence=attempt,
        current_effect_fence=effect))
    assert obs.attempt_basis_ref != obs.effect_basis_ref


def test_authority_current_freshness_and_narrowing(monkeypatch: pytest.MonkeyPatch) -> None:
    basis, obs, proposal, _, attempt, effect, command = claims()
    assert b1.validate_authority_observation(
        basis=basis, observation=obs, attempt_fence=attempt,
        author_effect_fence=effect, current_effect_fence=effect,
        author_command=command, capsule_manifest=None, cancellation_target=None,
        now_utc=NOW) is None
    assert b1.validate_subordinate_narrowing(
        basis=basis, observation=obs, proposal=proposal,
        attempt_fence=attempt, current_effect_fence=effect, now_utc=NOW) is None
    exact_relation_budget(monkeypatch, 196, lambda: b1.validate_authority_observation(
        basis=basis, observation=obs, attempt_fence=attempt,
        author_effect_fence=effect, current_effect_fence=effect,
        author_command=command, capsule_manifest=None, cancellation_target=None,
        now_utc=NOW))
    exact_relation_budget(monkeypatch, 242, lambda: b1.validate_subordinate_narrowing(
        basis=basis, observation=obs, proposal=proposal,
        attempt_fence=attempt, current_effect_fence=effect, now_utc=NOW))
    error("observation_stale_or_expired", lambda: b1.validate_authority_observation(
        basis=basis, observation=obs, attempt_fence=attempt,
        author_effect_fence=effect, current_effect_fence=effect,
        author_command=command, capsule_manifest=None, cancellation_target=None,
        now_utc="2030-01-01T00:00:00Z"))
    denied = value(b1.RW0AuthorityVerificationObservationV1,
                   **{**obs.identity_mapping(), "status": "denied"})
    error("authority_denied_or_revoked", lambda: b1.validate_subordinate_narrowing(
        basis=basis, observation=denied, proposal=proposal,
        attempt_fence=attempt, current_effect_fence=effect, now_utc=NOW))


def test_custody_subject_and_freshness(monkeypatch: pytest.MonkeyPatch) -> None:
    basis, _, _, work, _, _, _ = claims()
    availability = value(b1.RW0CustodyAvailabilityObservationV1,
                         phase_basis_ref=basis.basis_ref,
                         phase_basis_digest=basis.basis_digest,
                         subject_ref=work.work_spec_ref,
                         subject_semantic_digest=work.work_spec_digest,
                         observed_at="2028-01-01T00:00:00Z",
                         expires_at="2030-01-01T00:00:00Z")
    assert b1.validate_custody_binding(basis=basis, availability=availability,
                                       subject=work, now_utc=NOW) is None
    exact_relation_budget(monkeypatch, 106, lambda: b1.validate_custody_binding(
        basis=basis, availability=availability, subject=work, now_utc=NOW))
    error("observation_stale_or_expired", lambda: b1.validate_custody_binding(
        basis=basis, availability=availability, subject=work,
        now_utc="2030-01-01T00:00:00Z"))
    wrong = value(b1.RW0CustodyAvailabilityObservationV1,
                  **{**availability.identity_mapping(), "subject_semantic_digest": "a" * 64})
    error("custody_subject_mismatch", lambda: b1.validate_custody_binding(
        basis=basis, availability=wrong, subject=work, now_utc=NOW))


def test_retrieval_sequence_success_diagnostic_and_illegal_transition(monkeypatch: pytest.MonkeyPatch) -> None:
    basis, obs, proposal, work, attempt, effect, _ = claims()
    custody = value(b1.RW0CustodyAvailabilityObservationV1,
                    phase_basis_ref=basis.basis_ref,
                    phase_basis_digest=basis.basis_digest,
                    subject_ref=work.work_spec_ref,
                    subject_semantic_digest=work.work_spec_digest,
                    observed_at="2028-01-01T00:00:00Z",
                    expires_at="2030-01-01T00:00:00Z")
    def event(kind: str, number: int, prior=None):
        return value(
            b1.RW0RetrievalCapabilityEventObservationV1,
            event_ref=f"retrieval-event-{number}",
            phase_basis_ref=basis.basis_ref, phase_basis_digest=basis.basis_digest,
            subject_kind=custody.subject_kind, subject_ref=custody.subject_ref,
            subject_semantic_digest=custody.subject_semantic_digest,
            content_sha256=custody.content_sha256, byte_length=custody.byte_length,
            semantic_attempt_ref=attempt.semantic_attempt_ref,
            attempt_fence_ref=attempt.attempt_fence_ref,
            attempt_fence_digest=attempt.attempt_fence_digest,
            effect_intent_ref=effect.effect_intent_ref,
            effect_fence_ref=effect.effect_fence_ref,
            effect_fence_digest=effect.effect_fence_digest,
            audience_ref=attempt.program_ref, repository_ref=attempt.repository_ref,
            base_git_object_format=attempt.base_git_object_format,
            base_git_oid=attempt.base_git_oid,
            path_scope_digest=basis.path_scope_digest,
            authority_observation_ref=obs.observation_ref,
            authority_observation_digest=obs.observation_digest,
            subordinate_proposal_ref=proposal.proposal_ref,
            subordinate_proposal_digest=proposal.proposal_digest,
            custody_observation_ref=custody.observation_ref,
            custody_observation_digest=custody.observation_digest,
            event_kind=kind, sequence_number=number,
            predecessor_event_ref=None if prior is None else prior.event_ref,
            predecessor_event_digest=None if prior is None else prior.event_digest,
            occurred_at=f"2029-01-0{number + 1}T00:00:00Z",
            expires_at="2030-01-01T00:00:00Z",
        )
    issued = event("issued", 0)
    redeemed = event("redeemed", 1, issued)
    consumed = event("consumed", 2, redeemed)
    base = dict(basis=basis, availability=custody, observation=obs,
                proposal=proposal, attempt_fence=attempt,
                current_effect_fence=effect, now_utc="2029-01-04T00:00:00Z")
    for sequence in ((issued,), (issued, redeemed),
                     (issued, redeemed, consumed), (event("unknown", 0),)):
        assert b1.validate_retrieval_event_sequence(events=sequence, **base) is None
    exact_relation_budget(monkeypatch, 374, lambda: b1.validate_retrieval_event_sequence(
        events=(issued, redeemed, consumed), **base))
    failed = event("failed", 1, issued)
    assert b1.validate_retrieval_event_sequence(events=(issued, failed), **base) is None
    error("retrieval_transition_invalid", lambda: b1.validate_retrieval_event_sequence(
        events=(issued, consumed), **base))
    reversed_time = value(b1.RW0RetrievalCapabilityEventObservationV1,
                          **{**redeemed.identity_mapping(),
                             "occurred_at": "2028-01-01T00:00:00Z"})
    error("retrieval_transition_invalid", lambda: b1.validate_retrieval_event_sequence(
        events=(issued, reversed_time), **base))


def test_host_qualification_precedence_and_profile_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    basis, authority, _, _, _, effect, _ = claims()
    readiness = value(b1.RW0RemoteHostReadinessObservationV1,
                      observed_at="2028-01-01T00:00:00Z",
                      expires_at="2030-01-01T00:00:00Z")
    matching = {
        "phase_basis_ref": basis.basis_ref,
        "phase_basis_digest": basis.basis_digest,
        "effect_intent_ref": effect.effect_intent_ref,
        "effect_fence_ref": effect.effect_fence_ref,
        "effect_fence_digest": effect.effect_fence_digest,
        "verification_ref": authority.observation_ref,
        "verification_digest": authority.observation_digest,
        "readiness_ref": readiness.observation_ref,
        "readiness_digest": readiness.observation_digest,
        "evaluated_at": NOW,
    }
    for stem in ("platform_profile", "architecture_profile", "worker_artifact",
                 "worker_protocol", "execution_identity_profile", "process_profile",
                 "isolation_profile", "resource_profile", "cancellation_profile",
                 "credential_handoff_profile", "capsule_store_profile",
                 "validation_tool_profile", "review_tool_profile", "cleanup_profile"):
        for suffix in ("_ref", "_digest"):
            matching["required_" + stem + suffix] = getattr(readiness, stem + suffix)
    qualification = value(b1.RW0EffectHostQualificationV1, **matching)
    args = dict(basis=basis, authority=authority, readiness=readiness,
                current_effect_fence=effect, now_utc=NOW)
    assert b1.validate_host_qualification(qualification=qualification, **args) is None
    exact_relation_budget(monkeypatch, 241, lambda: b1.validate_host_qualification(
        qualification=qualification, **args))
    denied = value(b1.RW0AuthorityVerificationObservationV1,
                   **{**authority.identity_mapping(), "status": "denied"})
    blocked = value(b1.RW0EffectHostQualificationV1,
                    **{**qualification.identity_mapping(),
                       "verification_digest": denied.observation_digest,
                       "result": "blocked", "reason": "authority_denied_or_revoked"})
    assert b1.validate_host_qualification(
        qualification=blocked, **{**args, "authority": denied}) is None
    error("qualification_reason_mismatch", lambda: b1.validate_host_qualification(
        qualification=qualification, **{**args, "authority": denied}))
    bad_profile = value(b1.RW0EffectHostQualificationV1,
                        **{**qualification.identity_mapping(),
                           "required_worker_artifact_digest": "a" * 64,
                           "result": "blocked", "reason": "worker_artifact_mismatch"})
    assert b1.validate_host_qualification(qualification=bad_profile, **args) is None


def test_normal_terminal_shape_binds_real_block_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    from ge_nwp_coordinator import _development_decision_row_values as owner
    from tests.test_c2b2_private_development_readers import _decision_row
    from test_rw0_b1_vectors import _digest
    identity = dict(zip(owner._DEVELOPMENT_DECISION_COLUMNS, _decision_row(), strict=True))
    identity.update(
        decision_kind="block", decision_variant="program_block",
        basis_decision_ref="ref-basis-decision",
        basis_program_version_ref="ref-basis-version",
        basis_program_version_number=1,
        preassigned_semantic_attempt_ref=None,
        preassigned_candidate_ref=None,
    )
    identity["decision_digest"] = _digest(
        "governed-execution.nwp-development-decision.v1.identity",
        {k: v for k, v in identity.items() if k != "decision_digest"},
    )
    decision = owner.development_decision_row_value_from_row_tuple(
        tuple(identity[name] for name in owner._DEVELOPMENT_DECISION_COLUMNS))
    outcome = value(b1.RW0TerminalOutcomeV1,
                    decision_ref=decision.decision_ref,
                    decision_digest=decision.decision_digest,
                    decision_kind="block", outcome="block", branch="normal")
    assert b1.validate_normal_outcome_shape(outcome=outcome, decision=decision) is None
    exact_relation_budget(monkeypatch, 33, lambda: b1.validate_normal_outcome_shape(
        outcome=outcome, decision=decision))
    error("terminal_branch_mismatch", lambda: b1.validate_reconciled_cancel_outcome_shape(
        outcome=outcome, decision=decision))


def retrieval_case():
    basis, obs, proposal, work, attempt, effect, _ = claims()
    custody = value(
        b1.RW0CustodyAvailabilityObservationV1,
        phase_basis_ref=basis.basis_ref, phase_basis_digest=basis.basis_digest,
        subject_ref=work.work_spec_ref, subject_semantic_digest=work.work_spec_digest,
        observed_at="2028-01-01T00:00:00Z", expires_at="2030-01-01T00:00:00Z",
    )
    def make_event(kind: str, number: int, prior=None, **changes: object):
        return value(
            b1.RW0RetrievalCapabilityEventObservationV1,
            event_ref=f"retrieval-event-{number}",
            phase_basis_ref=basis.basis_ref, phase_basis_digest=basis.basis_digest,
            subject_kind=custody.subject_kind, subject_ref=custody.subject_ref,
            subject_semantic_digest=custody.subject_semantic_digest,
            content_sha256=custody.content_sha256, byte_length=custody.byte_length,
            semantic_attempt_ref=attempt.semantic_attempt_ref,
            attempt_fence_ref=attempt.attempt_fence_ref,
            attempt_fence_digest=attempt.attempt_fence_digest,
            effect_intent_ref=effect.effect_intent_ref,
            effect_fence_ref=effect.effect_fence_ref,
            effect_fence_digest=effect.effect_fence_digest,
            audience_ref=attempt.program_ref, repository_ref=attempt.repository_ref,
            base_git_object_format=attempt.base_git_object_format,
            base_git_oid=attempt.base_git_oid, path_scope_digest=basis.path_scope_digest,
            authority_observation_ref=obs.observation_ref,
            authority_observation_digest=obs.observation_digest,
            subordinate_proposal_ref=proposal.proposal_ref,
            subordinate_proposal_digest=proposal.proposal_digest,
            custody_observation_ref=custody.observation_ref,
            custody_observation_digest=custody.observation_digest,
            event_kind=kind, sequence_number=number,
            predecessor_event_ref=None if prior is None else prior.event_ref,
            predecessor_event_digest=None if prior is None else prior.event_digest,
            occurred_at=f"2029-01-0{number + 1}T00:00:00Z",
            expires_at="2030-01-01T00:00:00Z", **changes,
        )
    args = dict(basis=basis, availability=custody, observation=obs,
                proposal=proposal, attempt_fence=attempt,
                current_effect_fence=effect, now_utc="2029-01-04T00:00:00Z")
    return args, make_event


def test_audit_f1_parent_is_strict_reference_and_fences_cannot_exceed_it() -> None:
    basis, obs, proposal, _, attempt, effect, _ = claims()
    parent = effect.effect_ceilings.to_mapping()
    observed = value(b1.RW0AuthorityVerificationObservationV1,
                     **{**obs.identity_mapping(),
                        "allowed_effect_classes": ["author_candidate"],
                        "parent_ceilings": parent,
                        "grant_expires_at": proposal.expires_at})
    equal_parent = value(b1.RW0SubordinateAuthorizationProposalV1,
                         **{**proposal.identity_mapping(),
                            "verification_digest": observed.observation_digest,
                            "ceilings": parent})
    assert equal_parent.ceilings == observed.parent_ceilings
    assert attempt.aggregate_ceilings.max_local_commits > parent["max_local_commits"]
    error("scope_or_ceiling_mismatch", lambda: b1.validate_subordinate_narrowing(
        basis=basis, observation=observed, proposal=equal_parent,
        attempt_fence=attempt, current_effect_fence=effect, now_utc=NOW))


def test_audit_f2_fence_stop_and_head_drift_are_rejected() -> None:
    basis, obs, proposal, _, attempt, effect, command = claims()
    basis8 = value(b1.RW0PhaseEntryBasisV1,
                   **{**basis.identity_mapping(), "global_stop_version": 8})
    obs8 = value(b1.RW0AuthorityVerificationObservationV1,
                 **{**obs.identity_mapping(), "phase_basis_digest": basis8.basis_digest,
                    "global_stop_version": 8})
    proposal8 = value(b1.RW0SubordinateAuthorizationProposalV1,
                      **{**proposal.identity_mapping(), "phase_basis_digest": basis8.basis_digest,
                         "verification_digest": obs8.observation_digest,
                         "global_stop_version": 8})
    assert (basis8.global_stop_version, obs8.global_stop_version,
            proposal8.global_stop_version, attempt.global_stop_version,
            effect.global_stop_version) == (8, 8, 8, 7, 7)
    error("current_head_or_global_stop_mismatch", lambda: b1.validate_authority_observation(
        basis=basis8, observation=obs8, attempt_fence=attempt,
        author_effect_fence=effect, current_effect_fence=effect,
        author_command=command, capsule_manifest=None,
        cancellation_target=None, now_utc=NOW))
    error("current_head_or_global_stop_mismatch", lambda: b1.validate_subordinate_narrowing(
        basis=basis8, observation=obs8, proposal=proposal8,
        attempt_fence=attempt, current_effect_fence=effect, now_utc=NOW))
    different_head = value(b1.RW0AuthorityVerificationObservationV1,
                           **{**obs.identity_mapping(),
                              "current_effect_head_digest": "a" * 64})
    error("current_head_or_global_stop_mismatch", lambda: b1.validate_subordinate_narrowing(
        basis=basis, observation=different_head, proposal=proposal,
        attempt_fence=attempt, current_effect_fence=effect, now_utc=NOW))


def test_audit_f2_later_fence_cannot_pose_as_author_even_by_identity() -> None:
    from tests.c2a_contract_support import _effect_fence_for_vector
    basis, obs, _, _, attempt, _, command = claims()
    later = EffectFenceV1.from_mapping(_effect_fence_for_vector("validation"))
    later_obs = value(b1.RW0AuthorityVerificationObservationV1,
                      **{**obs.identity_mapping(),
                         "effect_basis_ref": later.effect_authorization_ref,
                         "effect_basis_digest": later.effect_authorization_digest,
                         "effect_fence_ref": later.effect_fence_ref,
                         "effect_fence_digest": later.effect_fence_digest,
                         "effect_class": later.effect_class})
    error("relation_mismatch", lambda: b1.validate_authority_observation(
        basis=basis, observation=later_obs, attempt_fence=attempt,
        author_effect_fence=later, current_effect_fence=later,
        author_command=command, capsule_manifest=None,
        cancellation_target=None, now_utc=NOW))


def test_audit_f3_retrieval_requires_current_narrowing_and_live_custody() -> None:
    args, make_event = retrieval_case()
    issued = make_event("issued", 0)
    wrong_effect = value(b1.RW0SubordinateAuthorizationProposalV1,
                         **{**args["proposal"].identity_mapping(),
                            "effect_class": "validate_candidate"})
    wrong_event = value(b1.RW0RetrievalCapabilityEventObservationV1,
                        **{**issued.identity_mapping(),
                           "subordinate_proposal_digest": wrong_effect.proposal_digest})
    error("scope_or_ceiling_mismatch", lambda: b1.validate_retrieval_event_sequence(
        events=(wrong_event,), **{**args, "proposal": wrong_effect}))
    unavailable = value(b1.RW0CustodyAvailabilityObservationV1,
                        **{**args["availability"].identity_mapping(),
                           "availability": "unavailable"})
    stale_event = value(b1.RW0RetrievalCapabilityEventObservationV1,
                        **{**issued.identity_mapping(),
                           "custody_observation_digest": unavailable.observation_digest,
                           "event_kind": "failed"})
    error("observation_stale_or_expired", lambda: b1.validate_retrieval_event_sequence(
        events=(stale_event,), **{**args, "availability": unavailable}))


def test_audit_f3_qualified_requires_allowed_effect_and_parent_compatible_fence() -> None:
    basis, authority, _, _, _, effect, _ = claims()
    readiness = value(b1.RW0RemoteHostReadinessObservationV1,
                      observed_at="2028-01-01T00:00:00Z",
                      expires_at="2030-01-01T00:00:00Z")
    matching = dict(phase_basis_ref=basis.basis_ref,
                    phase_basis_digest=basis.basis_digest,
                    effect_intent_ref=effect.effect_intent_ref,
                    effect_fence_ref=effect.effect_fence_ref,
                    effect_fence_digest=effect.effect_fence_digest,
                    verification_ref=authority.observation_ref,
                    verification_digest=authority.observation_digest,
                    readiness_ref=readiness.observation_ref,
                    readiness_digest=readiness.observation_digest,
                    evaluated_at=NOW)
    for stem in ("platform_profile", "architecture_profile", "worker_artifact",
                 "worker_protocol", "execution_identity_profile", "process_profile",
                 "isolation_profile", "resource_profile", "cancellation_profile",
                 "credential_handoff_profile", "capsule_store_profile",
                 "validation_tool_profile", "review_tool_profile", "cleanup_profile"):
        for suffix in ("_ref", "_digest"):
            matching["required_" + stem + suffix] = getattr(readiness, stem + suffix)
    excluded = value(b1.RW0AuthorityVerificationObservationV1,
                     **{**authority.identity_mapping(),
                        "allowed_effect_classes": ["validate_candidate"]})
    qualified = value(b1.RW0EffectHostQualificationV1,
                      **{**matching, "verification_digest": excluded.observation_digest})
    error("qualification_reason_mismatch", lambda: b1.validate_host_qualification(
        basis=basis, authority=excluded, readiness=readiness,
        qualification=qualified, current_effect_fence=effect, now_utc=NOW))
    blocked = value(b1.RW0EffectHostQualificationV1,
                    **{**qualified.identity_mapping(),
                       "result": "blocked", "reason": "authority_not_verified"})
    assert b1.validate_host_qualification(
        basis=basis, authority=excluded, readiness=readiness,
        qualification=blocked, current_effect_fence=effect, now_utc=NOW) is None


def test_audit_f7_retrieval_refs_are_unique_and_expiry_is_immutable() -> None:
    args, make_event = retrieval_case()
    issued = make_event("issued", 0)
    redeemed = make_event("redeemed", 1, issued)
    assert b1.validate_retrieval_event_sequence(events=(issued, redeemed), **args) is None
    repeated = value(b1.RW0RetrievalCapabilityEventObservationV1,
                     **{**redeemed.identity_mapping(), "event_ref": issued.event_ref})
    assert repeated.predecessor_event_ref == repeated.event_ref
    error("retrieval_transition_invalid", lambda: b1.validate_retrieval_event_sequence(
        events=(issued, repeated), **args))
    extended = value(b1.RW0RetrievalCapabilityEventObservationV1,
                     **{**redeemed.identity_mapping(),
                        "expires_at": "2031-01-01T00:00:00Z"})
    error("retrieval_transition_invalid", lambda: b1.validate_retrieval_event_sequence(
        events=(issued, extended), **args))


def test_audit_f2_active_stop_never_authorizes_progression() -> None:
    basis, obs, proposal, _, attempt, effect, command = claims()
    active_basis = value(b1.RW0PhaseEntryBasisV1,
                         **{**basis.identity_mapping(), "global_stop_state": "active"})
    active_obs = value(b1.RW0AuthorityVerificationObservationV1,
                       **{**obs.identity_mapping(),
                          "phase_basis_digest": active_basis.basis_digest,
                          "global_stop_state": "active"})
    active_proposal = value(b1.RW0SubordinateAuthorizationProposalV1,
                            **{**proposal.identity_mapping(),
                               "phase_basis_digest": active_basis.basis_digest,
                               "verification_digest": active_obs.observation_digest})
    error("current_head_or_global_stop_mismatch", lambda: b1.validate_authority_observation(
        basis=active_basis, observation=active_obs, attempt_fence=attempt,
        author_effect_fence=effect, current_effect_fence=effect,
        author_command=command, capsule_manifest=None,
        cancellation_target=None, now_utc=NOW))
    error("current_head_or_global_stop_mismatch", lambda: b1.validate_subordinate_narrowing(
        basis=active_basis, observation=active_obs, proposal=active_proposal,
        attempt_fence=attempt, current_effect_fence=effect, now_utc=NOW))
    args, make_event = retrieval_case()
    event = make_event("issued", 0)
    error("current_head_or_global_stop_mismatch", lambda: b1.validate_retrieval_event_sequence(
        events=(event,), **{**args, "basis": active_basis,
                            "observation": active_obs,
                            "proposal": active_proposal}))


def test_relation_budget_largest_valid_one_over_alias_and_cycle(monkeypatch: pytest.MonkeyPatch) -> None:
    basis, obs, proposal, _, attempt, effect, _ = claims()
    original = b1._WorkBudget
    instances = []
    class Measured(original):
        def __init__(self, limit: int) -> None:
            super().__init__(limit)
            self.original_limit = limit
            instances.append(self)
    monkeypatch.setattr(b1, "_WorkBudget", Measured)
    kwargs = dict(basis=basis, observation=obs, proposal=proposal,
                  attempt_fence=attempt, current_effect_fence=effect, now_utc=NOW)
    assert b1.validate_subordinate_narrowing(**kwargs) is None
    assert instances[-1].original_limit == 242 and instances[-1].remaining == 0
    args, make_event = retrieval_case()
    issued = make_event("issued", 0)
    redeemed = make_event("redeemed", 1, issued)
    consumed = make_event("consumed", 2, redeemed)
    assert b1.validate_retrieval_event_sequence(events=(issued, redeemed, consumed), **args) is None
    assert instances[-1].original_limit == 374 and instances[-1].remaining == 0
    error("retrieval_transition_invalid", lambda: b1.validate_retrieval_event_sequence(
        events=(consumed, consumed, consumed), **args))
    assert instances[-1].original_limit == 374 and instances[-1].remaining == 0
    class OneLess(original):
        def __init__(self, limit: int) -> None:
            super().__init__(limit - 1)
    monkeypatch.setattr(b1, "_WorkBudget", OneLess)
    error("cumulative_work_exhausted", lambda: b1.validate_subordinate_narrowing(**kwargs))
    error("cumulative_work_exhausted", lambda: b1.validate_retrieval_event_sequence(
        events=(issued, redeemed, consumed), **args))
    monkeypatch.setattr(b1, "_WorkBudget", original)
    cyclic: list[object] = []
    cyclic.append(cyclic)
    damaged = value(b1.RW0PhaseEntryBasisV1, **basis.identity_mapping())
    fields = type(damaged)._FIELDS
    members = list(damaged._values)
    members[fields.index("selection_key")] = cyclic
    object.__setattr__(damaged, "_values", tuple(members))
    error("graph_cycle", lambda: b1.validate_subordinate_narrowing(
        **{**kwargs, "basis": damaged}))


def phase_bundle(tmp_path):
    """Build exact owner values through test-only local fixtures, then close the writer."""
    import sqlite3
    from unittest.mock import patch
    import ge_nwp_coordinator.sqlite_transition_transaction as transaction
    import ge_nwp_coordinator._cognitive_proposal_row_values as cognitive_rows
    import ge_nwp_coordinator._development_effect_row_values as effect_rows
    import ge_nwp_coordinator._development_program_row_values as program_rows
    from ge_nwp_coordinator._development_pre_execution_plan_disposition_contracts import (
        CanonicalC2B3DLineage, _L34_FIELDS, _K8_FIELDS,
    )
    from ge_nwp_coordinator.global_stop import GlobalStopState
    from ge_nwp_coordinator.persistence_contracts import GlobalStopCurrentRecordEnvelope
    from test_section41_private_atomic_pre_execution_plan_disposition import (
        make_section41_fixture, DECISION_TIME,
    )
    fixture = make_section41_fixture(tmp_path, suffix="b1-phase")
    try:
        with patch.object(transaction, "_capture_transaction_timestamp", return_value=DECISION_TIME):
            recorded = fixture.author.writer._record_pre_execution_plan_disposition(
                fixture.mutation_ref, fixture.command_digest, fixture.bundle,
                fixture.identity, fixture.recovery_probe,
            )
        connection = sqlite3.connect(fixture.author.location.database_path)
        try:
            def row(table: str, columns: tuple[str, ...]):
                found = connection.execute(
                    "SELECT " + ", ".join(columns) + " FROM " + table
                ).fetchone()
                assert type(found) is tuple
                return found
            selection_head = cognitive_rows._row_value_from_tuple(
                "development_pre_execution_selection_heads",
                row("development_pre_execution_selection_heads",
                    cognitive_rows._TABLE_COLUMNS["development_pre_execution_selection_heads"]),
            )
            selected_proposal = cognitive_rows._row_value_from_tuple(
                "development_model_proposals",
                row("development_model_proposals",
                    cognitive_rows._TABLE_COLUMNS["development_model_proposals"]),
            )
            selected_artifact = cognitive_rows._row_value_from_tuple(
                "development_private_proposal_artifact_bindings",
                row("development_private_proposal_artifact_bindings",
                    cognitive_rows._TABLE_COLUMNS["development_private_proposal_artifact_bindings"]),
            )
            effect_head = effect_rows.development_effect_head_row_value_from_row_tuple(
                row("development_effect_heads", effect_rows._DEVELOPMENT_EFFECT_HEAD_COLUMNS)
            )
            delivery_head = effect_rows.development_delivery_head_row_value_from_row_tuple(
                row("development_delivery_heads", effect_rows._DEVELOPMENT_DELIVERY_HEAD_COLUMNS)
            )
            program_head = program_rows.development_program_head_row_value_from_row_tuple(
                row("development_program_heads", program_rows._DEVELOPMENT_PROGRAM_HEAD_COLUMNS)
            )
            work_head = program_rows.development_work_item_head_row_value_from_row_tuple(
                row("development_work_item_heads", program_rows._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS)
            )
        finally:
            connection.close()
        lineage = CanonicalC2B3DLineage(
            **{name: getattr(selection_head, name) for name in _L34_FIELDS}
        )
        stop = GlobalStopCurrentRecordEnvelope(
            state=GlobalStopState(version=fixture.author.command.coding_global_stop_version),
            updated_at=DECISION_TIME,
        )
        command = fixture.author.command
        work = fixture.author.work_spec
        basis = value(
            b1.RW0PhaseEntryBasisV1,
            c2b3d_lineage=lineage.to_mapping(),
            selection_key=[[name, getattr(lineage, name)] for name in _K8_FIELDS],
            selected_proposal_ref=selected_proposal.proposal_ref,
            selected_proposal_digest=selected_proposal.proposal_digest,
            selected_artifact_ref=selected_artifact.artifact_ref,
            selected_artifact_digest=selected_artifact.artifact_digest,
            selected_artifact_binding_digest=selected_artifact.artifact_binding_digest,
            selected_plan_safe_projection_digest=selected_artifact.safe_projection_digest,
            disposition_ref=recorded.disposition_ref,
            disposition_digest=recorded.disposition_digest,
            disposition=recorded.disposition,
            selection_head_revision=selection_head.head_revision,
            selection_head_digest=selection_head.head_digest,
            current_effect_head_revision=effect_head.head_revision,
            current_effect_head_state=effect_head.effect_state,
            current_effect_head_digest=effect_head.head_digest,
            current_delivery_head_revision=delivery_head.head_revision,
            current_delivery_head_state=delivery_head.delivery_state,
            current_delivery_head_digest=delivery_head.head_digest,
            global_stop_ref=stop.state.stop_ref,
            global_stop_version=stop.state.version,
            global_stop_state="clear",
            path_scope_digest=b1._path_scope_binding_digest(work.authorized_paths),
        )
        return dict(
            basis=basis, lineage=lineage, selection_result=recorded.projection,
            selection_head=selection_head, selected_proposal=selected_proposal,
            selected_artifact=selected_artifact, work_spec=work,
            attempt_fence=command.attempt_fence,
            author_effect_fence=command.effect_fence,
            author_command=command.worker_command,
            author_delivery=command.delivery_envelope,
            effect_head=effect_head, delivery_head=delivery_head,
            global_stop=stop, program_head=program_head, work_head=work_head,
            author_fixture=fixture.author,
        )
    finally:
        fixture.author.writer.close()


def test_phase_entry_basis_relation_positive_and_causal_head_drift(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = phase_bundle(tmp_path)
    names = ("basis", "lineage", "selection_result", "selection_head",
             "selected_proposal", "selected_artifact", "work_spec",
             "attempt_fence", "author_effect_fence", "author_command",
             "author_delivery", "effect_head", "delivery_head", "global_stop")
    args = {name: bundle[name] for name in names}
    assert b1.validate_phase_entry_basis(**args) is None
    exact_relation_budget(monkeypatch, 104, lambda: b1.validate_phase_entry_basis(**args))
    drifted = value(b1.RW0PhaseEntryBasisV1,
                    **{**bundle["basis"].identity_mapping(),
                       "current_effect_head_digest": "a" * 64})
    error("current_head_or_global_stop_mismatch", lambda: b1.validate_phase_entry_basis(
        **{**args, "basis": drifted}))


def test_terminal_outcome_binding_positive_and_causal_head_drift(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    import ge_nwp_coordinator._development_decision_row_values as decision_rows
    from tests.test_c2b2_private_development_readers import _decision_row
    from test_rw0_b1_vectors import _digest
    bundle = phase_bundle(tmp_path)
    identity = dict(zip(decision_rows._DEVELOPMENT_DECISION_COLUMNS, _decision_row(), strict=True))
    identity.update(
        decision_kind="block", decision_variant="program_block",
        basis_decision_ref="ref-basis-decision",
        basis_program_version_ref="ref-basis-version",
        basis_program_version_number=1,
        preassigned_semantic_attempt_ref=None,
        preassigned_candidate_ref=None,
    )
    identity["decision_digest"] = _digest(
        "governed-execution.nwp-development-decision.v1.identity",
        {k: v for k, v in identity.items() if k != "decision_digest"},
    )
    decision = decision_rows.development_decision_row_value_from_row_tuple(
        tuple(identity[name] for name in decision_rows._DEVELOPMENT_DECISION_COLUMNS)
    )
    basis = bundle["basis"]
    outcome = value(
        b1.RW0TerminalOutcomeV1,
        phase_basis_ref=basis.basis_ref, phase_basis_digest=basis.basis_digest,
        decision_ref=decision.decision_ref, decision_digest=decision.decision_digest,
        branch="normal", outcome="block", decision_kind="block",
        program_head_revision=bundle["program_head"].head_revision,
        program_head_digest=bundle["program_head"].head_digest,
        work_item_head_revision=bundle["work_head"].head_revision,
        work_item_head_digest=bundle["work_head"].head_digest,
        selection_head_revision=bundle["selection_head"].head_revision,
        selection_head_digest=bundle["selection_head"].head_digest,
        effect_head_revision=bundle["effect_head"].head_revision,
        effect_head_digest=bundle["effect_head"].head_digest,
        delivery_head_revision=bundle["delivery_head"].head_revision,
        delivery_head_digest=bundle["delivery_head"].head_digest,
        global_stop_ref=bundle["global_stop"].state.stop_ref,
        global_stop_version=bundle["global_stop"].state.version,
        global_stop_state="clear",
    )
    args = dict(basis=basis, outcome=outcome, decision=decision,
                program_head=bundle["program_head"], work_head=bundle["work_head"],
                selection_head=bundle["selection_head"],
                effect_head=bundle["effect_head"],
                delivery_head=bundle["delivery_head"],
                global_stop=bundle["global_stop"])
    assert b1.validate_terminal_outcome_binding(**args) is None
    exact_relation_budget(monkeypatch, 159, lambda: b1.validate_terminal_outcome_binding(**args))
    drifted = value(b1.RW0TerminalOutcomeV1,
                    **{**outcome.identity_mapping(), "effect_head_digest": "a" * 64})
    error("current_head_or_global_stop_mismatch", lambda: b1.validate_terminal_outcome_binding(
        **{**args, "outcome": drifted}))


def test_all_cancel_terminal_shape_relations_positive_and_causal_negative(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from test_c2b3d_author_effect_establishment_recovery import _decision_row
    bundle = phase_bundle(tmp_path)
    decision = _decision_row(
        bundle["author_fixture"], decision_ref="decision-b1-cancel",
        mutation_ref="mutation-b1-cancel", variant="effect_cancellation",
        target_delivery_attempt_ref=None,
        preassigned_delivery_attempt_ref="delivery-b1-cancel",
        timestamp="2098-01-01T00:00:09Z",
    )
    assert decision.decision_kind == "cancel"
    cases = (
        ("active_cancel_reconciled", "cancel", "reconciliation",
         b1.validate_reconciled_cancel_outcome_shape),
        ("active_cancel_unresolved", "block", "reconciliation",
         b1.validate_unresolved_cancel_outcome_shape),
        ("pre_effect_cancel_basis_unusable", "block", "mismatch",
         b1.validate_unusable_cancel_basis_outcome_shape),
    )
    for branch, outcome_kind, pair, validator in cases:
        outcome = value(
            b1.RW0TerminalOutcomeV1,
            branch=branch, outcome=outcome_kind, decision_kind="cancel",
            decision_ref=decision.decision_ref,
            decision_digest=decision.decision_digest,
            **{pair + "_ref": "ref-" + pair.replace("_", "-"),
               pair + "_digest": "a" * 64},
        )
        assert validator(outcome=outcome, decision=decision) is None
        exact_relation_budget(monkeypatch, 33, lambda: validator(
            outcome=outcome, decision=decision))
        error("terminal_branch_mismatch", lambda: b1.validate_normal_outcome_shape(
            outcome=outcome, decision=decision))


def test_audit_f7_expired_and_terminal_events_keep_issued_expiry() -> None:
    args, make_event = retrieval_case()
    issued = make_event("issued", 0)
    short = value(b1.RW0RetrievalCapabilityEventObservationV1,
                  **{**issued.identity_mapping(),
                     "expires_at": "2029-01-02T00:00:00Z"})
    terminal = make_event("expired", 1, short)
    expired = value(b1.RW0RetrievalCapabilityEventObservationV1,
                    **{**terminal.identity_mapping(),
                       "expires_at": short.expires_at,
                       "occurred_at": "2029-01-02T00:00:00Z"})
    assert b1.validate_retrieval_event_sequence(events=(short, expired), **args) is None
    for kind in ("revoked", "failed", "unknown"):
        observed = make_event(kind, 1, short)
        after = value(b1.RW0RetrievalCapabilityEventObservationV1,
                      **{**observed.identity_mapping(),
                         "expires_at": short.expires_at,
                         "occurred_at": "2029-01-03T00:00:00Z"})
        assert b1.validate_retrieval_event_sequence(events=(short, after), **args) is None
    later = make_event("consumed", 2, expired)
    error("retrieval_transition_invalid", lambda: b1.validate_retrieval_event_sequence(
        events=(short, expired, later), **args))


def test_audit_f2_single_field_delivery_head_and_proposal_fence_drift() -> None:
    basis, obs, proposal, _, attempt, effect, command = claims()
    other_delivery_head = value(b1.RW0AuthorityVerificationObservationV1,
                                **{**obs.identity_mapping(),
                                   "current_delivery_head_digest": "a" * 64})
    error("current_head_or_global_stop_mismatch", lambda: b1.validate_authority_observation(
        basis=basis, observation=other_delivery_head, attempt_fence=attempt,
        author_effect_fence=effect, current_effect_fence=effect,
        author_command=command, capsule_manifest=None,
        cancellation_target=None, now_utc=NOW))
    error("current_head_or_global_stop_mismatch", lambda: b1.validate_subordinate_narrowing(
        basis=basis, observation=other_delivery_head, proposal=proposal,
        attempt_fence=attempt, current_effect_fence=effect, now_utc=NOW))
    other_fence = value(b1.RW0SubordinateAuthorizationProposalV1,
                        **{**proposal.identity_mapping(),
                           "effect_fence_digest": "a" * 64})
    error("per_fence_basis_mismatch", lambda: b1.validate_subordinate_narrowing(
        basis=basis, observation=obs, proposal=other_fence,
        attempt_fence=attempt, current_effect_fence=effect, now_utc=NOW))


def test_audit_f3_host_parent_ceiling_and_expiry_must_cover_current_fence() -> None:
    basis, authority, _, _, _, effect, _ = claims()
    readiness = value(b1.RW0RemoteHostReadinessObservationV1,
                      observed_at="2028-01-01T00:00:00Z",
                      expires_at="2030-01-01T00:00:00Z")
    fields = dict(phase_basis_ref=basis.basis_ref,
                  phase_basis_digest=basis.basis_digest,
                  effect_intent_ref=effect.effect_intent_ref,
                  effect_fence_ref=effect.effect_fence_ref,
                  effect_fence_digest=effect.effect_fence_digest,
                  readiness_ref=readiness.observation_ref,
                  readiness_digest=readiness.observation_digest,
                  evaluated_at=NOW)
    for stem in ("platform_profile", "architecture_profile", "worker_artifact",
                 "worker_protocol", "execution_identity_profile", "process_profile",
                 "isolation_profile", "resource_profile", "cancellation_profile",
                 "credential_handoff_profile", "capsule_store_profile",
                 "validation_tool_profile", "review_tool_profile", "cleanup_profile"):
        for suffix in ("_ref", "_digest"):
            fields["required_" + stem + suffix] = getattr(readiness, stem + suffix)
    narrower_parent = authority.parent_ceilings.to_mapping()
    narrower_parent["max_active_invocations"] = 0
    for changes in ({"parent_ceilings": narrower_parent},
                    {"grant_expires_at": "2029-12-01T00:00:00Z"}):
        altered = value(b1.RW0AuthorityVerificationObservationV1,
                        **{**authority.identity_mapping(), **changes})
        claim = value(b1.RW0EffectHostQualificationV1,
                      **{**fields, "verification_ref": altered.observation_ref,
                         "verification_digest": altered.observation_digest})
        error("qualification_reason_mismatch", lambda: b1.validate_host_qualification(
            basis=basis, authority=altered, readiness=readiness,
            qualification=claim, current_effect_fence=effect, now_utc=NOW))
        blocked = value(b1.RW0EffectHostQualificationV1,
                        **{**claim.identity_mapping(),
                           "result": "blocked", "reason": "authority_not_verified"})
        assert b1.validate_host_qualification(
            basis=basis, authority=altered, readiness=readiness,
            qualification=blocked, current_effect_fence=effect, now_utc=NOW) is None


def test_audit_f1_equal_parent_rejected_with_compatible_fences() -> None:
    from tests.c2a_contract_support import _reseal_single_digest_record
    basis, obs, proposal, _, attempt, effect, _ = claims()
    attempt_fields = attempt.to_mapping()
    attempt_fields.update(aggregate_ceilings=effect.effect_ceilings.to_mapping(),
                          allowed_effect_classes=["author_candidate"],
                          expires_at=proposal.expires_at)
    narrow_attempt = AttemptFenceV1.from_mapping(
        _reseal_single_digest_record("AttemptFenceV1", attempt_fields)
    )
    effect_fields = effect.to_mapping()
    effect_fields.update(attempt_fence_digest=narrow_attempt.attempt_fence_digest,
                         expires_at=proposal.expires_at)
    narrow_effect = EffectFenceV1.from_mapping(
        _reseal_single_digest_record("EffectFenceV1", effect_fields)
    )
    lineage = basis.c2b3d_lineage.to_mapping()
    lineage.update(attempt_fence_digest=narrow_attempt.attempt_fence_digest,
                   effect_fence_digest=narrow_effect.effect_fence_digest)
    current_basis = value(b1.RW0PhaseEntryBasisV1,
                          **{**basis.identity_mapping(), "c2b3d_lineage": lineage})
    parent = narrow_effect.effect_ceilings.to_mapping()
    current_obs = value(b1.RW0AuthorityVerificationObservationV1,
                        **{**obs.identity_mapping(),
                           "phase_basis_digest": current_basis.basis_digest,
                           "attempt_fence_digest": narrow_attempt.attempt_fence_digest,
                           "effect_fence_digest": narrow_effect.effect_fence_digest,
                           "parent_ceilings": parent,
                           "allowed_effect_classes": ["author_candidate"],
                           "grant_expires_at": proposal.expires_at})
    equal = value(b1.RW0SubordinateAuthorizationProposalV1,
                  **{**proposal.identity_mapping(),
                     "phase_basis_digest": current_basis.basis_digest,
                     "verification_digest": current_obs.observation_digest,
                     "attempt_fence_digest": narrow_attempt.attempt_fence_digest,
                     "effect_fence_digest": narrow_effect.effect_fence_digest,
                     "ceilings": parent})
    args = dict(basis=current_basis, observation=current_obs, proposal=equal,
                attempt_fence=narrow_attempt, current_effect_fence=narrow_effect,
                now_utc=NOW)
    error("scope_or_ceiling_mismatch", lambda: b1.validate_subordinate_narrowing(**args))
    lower = dict(parent)
    lower["max_cpu_seconds"] -= 1
    narrowed = value(b1.RW0SubordinateAuthorizationProposalV1,
                     **{**equal.identity_mapping(), "ceilings": lower})
    assert b1.validate_subordinate_narrowing(**{**args, "proposal": narrowed}) is None


def test_audit_f3_active_stop_blocks_matching_host_claim() -> None:
    basis, authority, _, _, _, effect, _ = claims()
    active_basis = value(b1.RW0PhaseEntryBasisV1,
                         **{**basis.identity_mapping(), "global_stop_state": "active"})
    active_authority = value(b1.RW0AuthorityVerificationObservationV1,
                             **{**authority.identity_mapping(),
                                "phase_basis_digest": active_basis.basis_digest,
                                "global_stop_state": "active"})
    readiness = value(b1.RW0RemoteHostReadinessObservationV1,
                      observed_at="2028-01-01T00:00:00Z",
                      expires_at="2030-01-01T00:00:00Z")
    fields = dict(phase_basis_ref=active_basis.basis_ref,
                  phase_basis_digest=active_basis.basis_digest,
                  effect_intent_ref=effect.effect_intent_ref,
                  effect_fence_ref=effect.effect_fence_ref,
                  effect_fence_digest=effect.effect_fence_digest,
                  verification_ref=active_authority.observation_ref,
                  verification_digest=active_authority.observation_digest,
                  readiness_ref=readiness.observation_ref,
                  readiness_digest=readiness.observation_digest,
                  evaluated_at=NOW)
    for stem in ("platform_profile", "architecture_profile", "worker_artifact",
                 "worker_protocol", "execution_identity_profile", "process_profile",
                 "isolation_profile", "resource_profile", "cancellation_profile",
                 "credential_handoff_profile", "capsule_store_profile",
                 "validation_tool_profile", "review_tool_profile", "cleanup_profile"):
        for suffix in ("_ref", "_digest"):
            fields["required_" + stem + suffix] = getattr(readiness, stem + suffix)
    blocked = value(b1.RW0EffectHostQualificationV1,
                    **{**fields, "result": "blocked", "reason": "global_stop_active"})
    assert b1.validate_host_qualification(
        basis=active_basis, authority=active_authority, readiness=readiness,
        qualification=blocked, current_effect_fence=effect, now_utc=NOW) is None
    qualified = value(b1.RW0EffectHostQualificationV1,
                      **{**blocked.identity_mapping(),
                         "result": "qualified", "reason": "qualified"})
    error("qualification_reason_mismatch", lambda: b1.validate_host_qualification(
        basis=active_basis, authority=active_authority, readiness=readiness,
        qualification=qualified, current_effect_fence=effect, now_utc=NOW))


def _owner_change(owner, **changes: object):
    fields = owner.to_mapping()
    fields.update(changes)
    return type(owner).from_mapping(
        _reseal_single_digest_record(type(owner).__name__, fields)
    )


def _narrowing_with_effect(effect_changes: dict[str, object]):
    basis, observation, proposal, _, attempt, effect, _ = claims()
    changed_effect = _owner_change(effect, **effect_changes)
    changed_observation = value(
        b1.RW0AuthorityVerificationObservationV1,
        **{**observation.identity_mapping(),
           "effect_fence_digest": changed_effect.effect_fence_digest},
    )
    changed_proposal = value(
        b1.RW0SubordinateAuthorizationProposalV1,
        **{**proposal.identity_mapping(),
           "effect_fence_digest": changed_effect.effect_fence_digest,
           "verification_digest": changed_observation.observation_digest},
    )
    return dict(basis=basis, observation=changed_observation,
                proposal=changed_proposal, attempt_fence=attempt,
                current_effect_fence=changed_effect, now_utc=NOW)


def _host_case(issues: tuple[str, ...] = (), *, claimed: tuple[str, str] =
               ("qualified", "qualified"), effect_changes: dict[str, object] | None = None,
               authority_changes: dict[str, object] | None = None):
    basis, authority, _, _, _, effect, _ = claims()
    if effect_changes:
        effect = _owner_change(effect, **effect_changes)
    basis_changes = {}
    authority_fields = dict(authority.identity_mapping())
    readiness_fields = {
        "observed_at": "2028-01-01T00:00:00Z",
        "expires_at": "2030-01-01T00:00:00Z",
    }
    qualification_changes = {}
    for issue in issues:
        if issue == "phase_mismatch":
            qualification_changes["effect_intent_ref"] = "other-effect-intent"
        elif issue == "active_stop":
            basis_changes["global_stop_state"] = "active"
            authority_fields["global_stop_state"] = "active"
        elif issue == "denied":
            authority_fields["status"] = "denied"
        elif issue == "authority_expired":
            authority_fields["grant_expires_at"] = "2028-12-31T00:00:00Z"
        elif issue == "authority_unknown":
            authority_fields["revocation_status"] = "unknown"
        elif issue == "family_invalid":
            authority_fields["family_status"] = "incompatible"
        elif issue == "readiness_expired":
            readiness_fields["expires_at"] = "2028-12-31T00:00:00Z"
        elif issue == "readiness_unready":
            readiness_fields["status"] = "unready"
        elif issue == "readiness_unknown":
            readiness_fields["status"] = "unknown"
        elif issue == "artifact_mismatch":
            qualification_changes["required_worker_artifact_digest"] = "a" * 64
        elif issue == "protocol_mismatch":
            qualification_changes["required_worker_protocol_digest"] = "a" * 64
        elif issue == "platform_mismatch":
            qualification_changes["required_platform_profile_digest"] = "a" * 64
        elif issue == "profile_mismatch":
            qualification_changes["required_process_profile_digest"] = "a" * 64
        else:
            raise AssertionError(issue)
    if basis_changes:
        basis = value(b1.RW0PhaseEntryBasisV1,
                      **{**basis.identity_mapping(), **basis_changes})
    authority_fields.update(
        phase_basis_digest=basis.basis_digest,
        effect_fence_digest=effect.effect_fence_digest,
    )
    if authority_changes:
        authority_fields.update(authority_changes)
    authority = value(b1.RW0AuthorityVerificationObservationV1,
                      **authority_fields)
    readiness = value(b1.RW0RemoteHostReadinessObservationV1, **readiness_fields)
    matching = dict(
        phase_basis_ref=basis.basis_ref,
        phase_basis_digest=basis.basis_digest,
        effect_intent_ref=effect.effect_intent_ref,
        effect_fence_ref=effect.effect_fence_ref,
        effect_fence_digest=effect.effect_fence_digest,
        verification_ref=authority.observation_ref,
        verification_digest=authority.observation_digest,
        readiness_ref=readiness.observation_ref,
        readiness_digest=readiness.observation_digest,
        evaluated_at=NOW, result=claimed[0], reason=claimed[1],
    )
    for stem in (
        "platform_profile", "architecture_profile", "worker_artifact",
        "worker_protocol", "execution_identity_profile", "process_profile",
        "isolation_profile", "resource_profile", "cancellation_profile",
        "credential_handoff_profile", "capsule_store_profile",
        "validation_tool_profile", "review_tool_profile", "cleanup_profile",
    ):
        for suffix in ("_ref", "_digest"):
            matching["required_" + stem + suffix] = getattr(readiness, stem + suffix)
    matching.update(qualification_changes)
    qualification = value(b1.RW0EffectHostQualificationV1, **matching)
    return dict(basis=basis, authority=authority, readiness=readiness,
                qualification=qualification, current_effect_fence=effect,
                now_utc=NOW)


def test_reaudit_host_attempt_pair_and_effect_origin_are_causal() -> None:
    basis, authority, _, _, attempt, effect, _ = claims()
    assert (authority.attempt_fence_ref, authority.attempt_fence_digest) == (
        basis.c2b3d_lineage.attempt_fence_ref,
        basis.c2b3d_lineage.attempt_fence_digest,
    ) == (effect.attempt_fence_ref, effect.attempt_fence_digest)
    for changes in (
        {"attempt_fence_ref": "other-attempt-fence"},
        {"attempt_fence_digest": "a" * 64},
    ):
        qualified = _host_case(authority_changes=changes)
        error("qualification_reason_mismatch", lambda: b1.validate_host_qualification(**qualified))
        blocked = value(b1.RW0EffectHostQualificationV1,
                        **{**qualified["qualification"].identity_mapping(),
                           "result": "blocked", "reason": "phase_or_effect_mismatch"})
        assert b1.validate_host_qualification(
            **{**qualified, "qualification": blocked}) is None
    for changes in (
        {"semantic_attempt_ref": "other-semantic-attempt"},
        {"attempt_fence_ref": "other-attempt-fence"},
        {"attempt_fence_digest": "a" * 64},
    ):
        qualified = _host_case(effect_changes=changes)
        error("qualification_reason_mismatch", lambda: b1.validate_host_qualification(**qualified))
        blocked = value(b1.RW0EffectHostQualificationV1,
                        **{**qualified["qualification"].identity_mapping(),
                           "result": "blocked", "reason": "phase_or_effect_mismatch"})
        assert b1.validate_host_qualification(
            **{**qualified, "qualification": blocked}) is None


def test_reaudit_narrowing_current_semantic_attempt_and_origin() -> None:
    for changes in (
        {"semantic_attempt_ref": "other-semantic-attempt"},
        {"attempt_fence_ref": "other-attempt-fence"},
        {"attempt_fence_digest": "a" * 64},
    ):
        args = _narrowing_with_effect(changes)
        error("per_fence_basis_mismatch", lambda: b1.validate_subordinate_narrowing(**args))


def test_reaudit_verified_parent_contains_entire_attempt_effect_set_and_expiries() -> None:
    basis, observation, proposal, _, attempt, effect, command = claims()
    narrower_parent = value(
        b1.RW0AuthorityVerificationObservationV1,
        **{**observation.identity_mapping(),
           "allowed_effect_classes": ["author_candidate"]},
    )
    narrower_proposal = value(
        b1.RW0SubordinateAuthorizationProposalV1,
        **{**proposal.identity_mapping(),
           "verification_digest": narrower_parent.observation_digest},
    )
    error("scope_or_ceiling_mismatch", lambda: b1.validate_subordinate_narrowing(
        basis=basis, observation=narrower_parent, proposal=narrower_proposal,
        attempt_fence=attempt, current_effect_fence=effect, now_utc=NOW))
    error("scope_or_ceiling_mismatch", lambda: b1.validate_authority_observation(
        basis=basis, observation=narrower_parent, attempt_fence=attempt,
        author_effect_fence=effect, current_effect_fence=effect,
        author_command=command, capsule_manifest=None,
        cancellation_target=None, now_utc=NOW))
    short_grant = value(
        b1.RW0AuthorityVerificationObservationV1,
        **{**observation.identity_mapping(),
           "grant_expires_at": "2029-06-01T00:00:00Z"},
    )
    error("scope_or_ceiling_mismatch", lambda: b1.validate_authority_observation(
        basis=basis, observation=short_grant, attempt_fence=attempt,
        author_effect_fence=effect, current_effect_fence=effect,
        author_command=command, capsule_manifest=None,
        cancellation_target=None, now_utc=NOW))


def test_reaudit_narrower_attempt_set_and_role_specific_basis_pairs_are_valid() -> None:
    basis, observation, proposal, _, attempt, effect, _ = claims()
    narrow_attempt = _owner_change(
        attempt, allowed_effect_classes=["author_candidate"])
    narrow_effect = _owner_change(
        effect, attempt_fence_digest=narrow_attempt.attempt_fence_digest)
    lineage = basis.c2b3d_lineage.to_mapping()
    lineage.update(attempt_fence_digest=narrow_attempt.attempt_fence_digest,
                   effect_fence_digest=narrow_effect.effect_fence_digest)
    narrow_basis = value(b1.RW0PhaseEntryBasisV1,
                         **{**basis.identity_mapping(), "c2b3d_lineage": lineage})
    narrow_observation = value(
        b1.RW0AuthorityVerificationObservationV1,
        **{**observation.identity_mapping(),
           "phase_basis_digest": narrow_basis.basis_digest,
           "attempt_fence_digest": narrow_attempt.attempt_fence_digest,
           "effect_fence_digest": narrow_effect.effect_fence_digest},
    )
    narrow_proposal = value(
        b1.RW0SubordinateAuthorizationProposalV1,
        **{**proposal.identity_mapping(),
           "phase_basis_digest": narrow_basis.basis_digest,
           "verification_digest": narrow_observation.observation_digest,
           "attempt_fence_digest": narrow_attempt.attempt_fence_digest,
           "effect_fence_digest": narrow_effect.effect_fence_digest},
    )
    assert set(narrow_attempt.allowed_effect_classes) < set(narrow_observation.allowed_effect_classes)
    assert b1.validate_subordinate_narrowing(
        basis=narrow_basis, observation=narrow_observation, proposal=narrow_proposal,
        attempt_fence=narrow_attempt, current_effect_fence=narrow_effect,
        now_utc=NOW) is None
    assert observation.attempt_basis_ref != observation.effect_basis_ref
    assert b1.validate_subordinate_narrowing(
        basis=basis, observation=observation, proposal=proposal,
        attempt_fence=attempt, current_effect_fence=effect, now_utc=NOW) is None
    equal_basis_effect = _owner_change(
        effect,
        effect_authorization_ref=attempt.attempt_authorization_ref,
        effect_authorization_digest=attempt.attempt_authorization_digest,
    )
    equal_observation = value(
        b1.RW0AuthorityVerificationObservationV1,
        **{**observation.identity_mapping(),
           "effect_basis_ref": equal_basis_effect.effect_authorization_ref,
           "effect_basis_digest": equal_basis_effect.effect_authorization_digest,
           "effect_fence_digest": equal_basis_effect.effect_fence_digest},
    )
    equal_proposal = value(
        b1.RW0SubordinateAuthorizationProposalV1,
        **{**proposal.identity_mapping(),
           "verification_digest": equal_observation.observation_digest,
           "effect_basis_ref": equal_basis_effect.effect_authorization_ref,
           "effect_basis_digest": equal_basis_effect.effect_authorization_digest,
           "effect_fence_digest": equal_basis_effect.effect_fence_digest},
    )
    assert equal_observation.attempt_basis_ref == equal_observation.effect_basis_ref
    assert b1.validate_subordinate_narrowing(
        basis=basis, observation=equal_observation, proposal=equal_proposal,
        attempt_fence=attempt, current_effect_fence=equal_basis_effect,
        now_utc=NOW) is None


def test_reaudit_each_applicable_fence_is_independently_inside_parent() -> None:
    _, observation, _, _, attempt, effect, _ = claims()
    def contained(candidate_attempt, author, current):
        return b1._verified_parent_contains(
            observation, candidate_attempt, author, current,
            parent_reason="relation_mismatch")
    assert contained(attempt, effect, effect) is None
    late_attempt = _owner_change(attempt, expires_at="2031-01-01T00:00:00Z")
    late_author = _owner_change(effect, expires_at="2031-01-01T00:00:00Z")
    late_current = _owner_change(effect, expires_at="2031-02-01T00:00:00Z")
    for candidate in ((late_attempt, effect, effect),
                      (attempt, late_author, effect),
                      (attempt, effect, late_current)):
        error("scope_or_ceiling_mismatch", lambda c=candidate: contained(*c))
    high_attempt = attempt.aggregate_ceilings.to_mapping()
    high_attempt["max_cpu_seconds"] = observation.parent_ceilings.max_cpu_seconds + 1
    error("scope_or_ceiling_mismatch", lambda: contained(
        _owner_change(attempt, aggregate_ceilings=high_attempt), effect, effect))
    high_effect = effect.effect_ceilings.to_mapping()
    high_effect["max_cpu_seconds"] = observation.parent_ceilings.max_cpu_seconds + 1
    error("scope_or_ceiling_mismatch", lambda: contained(
        attempt, effect, _owner_change(effect, effect_ceilings=high_effect)))


def test_reaudit_retrieval_shared_path_alias_is_charged_twice(monkeypatch: pytest.MonkeyPatch) -> None:
    args, make_event = retrieval_case()
    attempt = args["attempt_fence"]
    effect = args["current_effect_fence"]
    assert attempt.path_ceiling == effect.path_ceiling
    object.__setattr__(effect, "_path_ceiling", attempt.path_ceiling)
    assert attempt.path_ceiling is effect.path_ceiling
    issued = make_event("issued", 0)
    redeemed = make_event("redeemed", 1, issued)
    consumed = make_event("consumed", 2, redeemed)
    exact_relation_budget(monkeypatch, 374, lambda: b1.validate_retrieval_event_sequence(
        events=(issued, redeemed, consumed), **args))


def test_reaudit_host_complete_result_table_and_adjacent_precedence() -> None:
    # Literal expected outcomes are independent of production reason constants.
    ordered = (
        ("phase_mismatch", ("blocked", "phase_or_effect_mismatch")),
        ("active_stop", ("blocked", "global_stop_active")),
        ("denied", ("blocked", "authority_denied_or_revoked")),
        ("authority_expired", ("blocked", "authority_expired")),
        ("authority_unknown", ("unknown", "unknown")),
        ("family_invalid", ("blocked", "authority_not_verified")),
        ("readiness_expired", ("blocked", "readiness_expired")),
        ("readiness_unready", ("blocked", "readiness_unready")),
        ("readiness_unknown", ("blocked", "readiness_unknown")),
        ("artifact_mismatch", ("blocked", "worker_artifact_mismatch")),
        ("protocol_mismatch", ("blocked", "worker_protocol_mismatch")),
        ("platform_mismatch", ("blocked", "platform_or_architecture_mismatch")),
        ("profile_mismatch", ("blocked", "profile_mismatch")),
    )
    assert b1.validate_host_qualification(**_host_case()) is None
    for issue, expected in ordered:
        assert b1.validate_host_qualification(
            **_host_case((issue,), claimed=expected)) is None, issue
    for (higher, expected), (lower, _) in zip(ordered, ordered[1:]):
        if (higher, lower) == ("readiness_unready", "readiness_unknown"):
            continue  # One readiness status cannot be both values.
        assert b1.validate_host_qualification(
            **_host_case((higher, lower), claimed=expected)) is None, (higher, lower)
    assert b1.validate_host_qualification(**_host_case(
        ("readiness_unready", "artifact_mismatch"),
        claimed=("blocked", "readiness_unready"))) is None


def test_reaudit_retrieval_duplicate_ref_and_self_predecessor_are_independent() -> None:
    args, make_event = retrieval_case()
    issued = make_event("issued", 0)
    redeemed = make_event("redeemed", 1, issued)
    consumed = make_event("consumed", 2, redeemed)
    duplicate = value(
        b1.RW0RetrievalCapabilityEventObservationV1,
        **{**consumed.identity_mapping(), "event_ref": issued.event_ref},
    )
    assert duplicate.predecessor_event_ref == redeemed.event_ref != duplicate.event_ref
    error("retrieval_transition_invalid", lambda: b1.validate_retrieval_event_sequence(
        events=(issued, redeemed, duplicate), **args))
    self_predecessor = value(
        b1.RW0RetrievalCapabilityEventObservationV1,
        **{**consumed.identity_mapping(), "predecessor_event_ref": consumed.event_ref},
    )
    assert len({issued.event_ref, redeemed.event_ref, self_predecessor.event_ref}) == 3
    error("retrieval_transition_invalid", lambda: b1.validate_retrieval_event_sequence(
        events=(issued, redeemed, self_predecessor), **args))


def test_reaudit_retrieval_external_members_charge_once(monkeypatch: pytest.MonkeyPatch) -> None:
    args, make_event = retrieval_case()
    issued = make_event("issued", 0)
    redeemed = make_event("redeemed", 1, issued)
    consumed = make_event("consumed", 2, redeemed)
    original = b1._WorkBudget
    observed = []
    class Measured(original):
        def __init__(self, limit: int) -> None:
            assert limit == 374
            super().__init__(limit)
            self.charges = []
            observed.append(self)
        def charge(self, amount: int = 1) -> None:
            self.charges.append(amount)
            super().charge(amount)
    monkeypatch.setattr(b1, "_WorkBudget", Measured)
    assert b1.validate_retrieval_event_sequence(
        events=(issued, redeemed, consumed), **args) is None
    assert len(observed) == 1
    assert observed[0].charges.count(30 + 6) == 1
    assert sum(observed[0].charges) == 374
    assert observed[0].remaining == 0


# Third-audit fixtures retain all unrelated facts and rebind only digest links.
def _third_current_case(changes: dict[str, object]):
    args, make_event = retrieval_case()
    attempt = args["attempt_fence"]
    effect = _owner_change(args["current_effect_fence"], **changes)
    parent = attempt.aggregate_ceilings.to_mapping()
    parent["max_cpu_seconds"] += 2
    obs = value(b1.RW0AuthorityVerificationObservationV1,
                **{**args["observation"].identity_mapping(),
                   "effect_fence_ref": effect.effect_fence_ref,
                   "effect_fence_digest": effect.effect_fence_digest,
                   "effect_class": effect.effect_class,
                   "effect_basis_ref": effect.effect_authorization_ref,
                   "effect_basis_digest": effect.effect_authorization_digest,
                   "parent_ceilings": parent,
                   "grant_expires_at": "2031-01-01T00:00:00Z"})
    proposed = effect.effect_ceilings.to_mapping()
    proposed["max_cpu_seconds"] = attempt.aggregate_ceilings.max_cpu_seconds - 2
    proposal = value(b1.RW0SubordinateAuthorizationProposalV1,
                     **{**args["proposal"].identity_mapping(),
                        "verification_digest": obs.observation_digest,
                        "effect_fence_ref": effect.effect_fence_ref,
                        "effect_fence_digest": effect.effect_fence_digest,
                        "effect_class": effect.effect_class,
                        "effect_basis_ref": effect.effect_authorization_ref,
                        "effect_basis_digest": effect.effect_authorization_digest,
                        "ceilings": proposed})
    event = value(b1.RW0RetrievalCapabilityEventObservationV1,
                  **{**make_event("issued", 0).identity_mapping(),
                     "effect_intent_ref": effect.effect_intent_ref,
                     "effect_fence_ref": effect.effect_fence_ref,
                     "effect_fence_digest": effect.effect_fence_digest,
                     "authority_observation_digest": obs.observation_digest,
                     "subordinate_proposal_digest": proposal.proposal_digest})
    args.update(observation=obs, proposal=proposal, current_effect_fence=effect)
    narrow = {k: v for k, v in args.items() if k != "availability"}
    return narrow, dict(args, events=(event,))


@pytest.mark.parametrize("bound", ("ceiling", "expiry"))
@pytest.mark.parametrize("relation", ("narrowing", "retrieval"))
def test_third_current_fence_attempt_bounds(bound: str, relation: str) -> None:
    _, attempt, effect, _ = graph()
    if bound == "ceiling":
        def changes(offset):
            ceilings = effect.effect_ceilings.to_mapping()
            ceilings["max_cpu_seconds"] = attempt.aggregate_ceilings.max_cpu_seconds + offset
            return {"effect_ceilings": ceilings}
        variants = (changes(0), changes(-1), changes(1))
    else:
        variants = tuple({"expires_at": stamp} for stamp in (
            attempt.expires_at, "2029-12-15T00:00:00Z", "2030-06-01T00:00:00Z"))
    function = (b1.validate_subordinate_narrowing if relation == "narrowing"
                else b1.validate_retrieval_event_sequence)
    index = 0 if relation == "narrowing" else 1
    for changes in variants[:2]:
        assert function(**_third_current_case(changes)[index]) is None
    error("scope_or_ceiling_mismatch",
          lambda: function(**_third_current_case(variants[2])[index]))


@pytest.mark.parametrize("field,changed", (
    ("candidate_ref", "other-candidate"),
    ("command_ref", "other-author-command"),
    ("command_digest", "a" * 64),
))
@pytest.mark.parametrize("relation", ("narrowing", "retrieval", "qualification"))
def test_third_stable_origin_lineage(field: str, changed: str, relation: str) -> None:
    changes = {field: changed}
    _, _, original, _ = graph()
    mutant = _owner_change(original, **changes)
    assert mutant.effect_fence_digest == mutant.computed_digest()
    assert {k for k in original.identity_mapping()
            if original.identity_mapping()[k] != mutant.identity_mapping()[k]} == {field}
    if relation == "qualification":
        args = _host_case(effect_changes=changes)
        error("qualification_reason_mismatch", lambda: b1.validate_host_qualification(**args))
        blocked = value(b1.RW0EffectHostQualificationV1,
                        **{**args["qualification"].identity_mapping(),
                           "result": "blocked", "reason": "phase_or_effect_mismatch"})
        assert b1.validate_host_qualification(**{**args, "qualification": blocked}) is None
    else:
        narrow, retrieval = _third_current_case(changes)
        function, args = ((b1.validate_subordinate_narrowing, narrow)
                          if relation == "narrowing" else
                          (b1.validate_retrieval_event_sequence, retrieval))
        error("relation_mismatch", lambda: function(**args))


def test_third_later_current_effect_keeps_stable_origin() -> None:
    from ge_nwp_coordinator._worker_execution_semantic_values import (
        CandidateCapsuleManifestV1, validate_effect_relation,
    )
    _, attempt, author, command = graph()
    later = EffectFenceV1.from_mapping(_effect_fence_for_vector("validation"))
    capsule = CandidateCapsuleManifestV1.from_mapping(_full_record("CandidateCapsuleManifestV1"))
    assert validate_effect_relation(attempt_fence=attempt, author_command=command,
                                   author_effect_fence=author, effect_fence=later,
                                   capsule_manifest=capsule) is None
    assert later.effect_intent_ref != author.effect_intent_ref
    assert later.effect_fence_ref != author.effect_fence_ref
    changes = {k: v for k, v in later.identity_mapping().items()
               if v != author.identity_mapping()[k]}
    narrow, retrieval = _third_current_case(changes)
    assert b1.validate_subordinate_narrowing(**narrow) is None
    assert b1.validate_retrieval_event_sequence(**retrieval) is None
    assert b1.validate_host_qualification(**_host_case(
        effect_changes=changes, authority_changes={
            "effect_fence_ref": later.effect_fence_ref,
            "effect_class": later.effect_class,
            "effect_basis_ref": later.effect_authorization_ref,
            "effect_basis_digest": later.effect_authorization_digest})) is None
