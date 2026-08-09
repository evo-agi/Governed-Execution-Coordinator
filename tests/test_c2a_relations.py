"""Direct identity, authority, observation, and capsule relation tests for C2A."""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import inspect
from pathlib import Path
import pytest

from c2a_contract_support import (
    AUTHORIZED_PATHS,
    BLOB_EXPECTATIONS,
    BLOB_FIXTURES,
    CLAUSES,
    CONDITIONAL_FIELDS,
    DOC,
    EFFECT_CLASSES_BY_OBSERVATION,
    GOLDEN_BYTES,
    GOLDEN_META,
    IDENTITIES,
    IDENTITY_PAIRS,
    MANIFEST_CANONICALIZATION_PROFILE,
    MANIFEST_DIGEST_DOMAIN,
    MANIFEST_SCHEMA_ID,
    OBSERVATION_DIGEST_FIELDS,
    OBSERVATION_ROWS,
    OBSERVATION_SPEC,
    RELATION_DIGESTS,
    RETRIEVAL_INVERSIONS,
    RETRIEVAL_NON_AUTHORITY_RULES,
    SAFE_REF_FIELDS,
    _RelatedRecordDictSubclass,
    _RelatedRecordListSubclass,
    _RelatedRecordMappingLike,
    _attempt_fence_record_valid,
    _author_command_record_valid,
    _authorized_path_scope_digest,
    _base_git_oid_valid,
    _canonical,
    _command_replay,
    _complete_authority,
    _delivery_for_vector,
    _delivery_record_valid,
    _delivery_record_valid_with_canonical_relations,
    _digest,
    _effect_fence_for_vector,
    _effect_fence_record_valid,
    _effect_fence_record_valid_with_canonical_relations,
    _field_names,
    _full_record,
    _identity_bytes_are_valid,
    _identity_noncollapse,
    _identity_object,
    _identity_values,
    _local_git_effect_fence,
    _manifest_valid,
    _manifest_valid_with_canonical_relations,
    _manifest_with_entry_mutation,
    _nominal_identity_binding_valid,
    _observation_for_kind,
    _observation_for_vector,
    _observation_relation,
    _observation_relation_with_canonical_relations,
    _observation_valid,
    _observation_valid_with_canonical_relations,
    _path_set_valid,
    _redelivery_valid,
    _redelivery_valid_with_canonical_relations,
    _reseal_author_command,
    _reseal_manifest,
    _reseal_observation,
    _reseal_single_digest_record,
    _retargeted_cancellation,
    _retrieval_contract_valid,
    _sealed_record,
    _section,
    _source_timestamp,
    _unknown_outcome_redelivery_allowed,
    _unknown_outcome_relation_fixture,
    _valid_redelivery_candidate,
)


class _BaseGitOidStringSubclass(str):
    pass


class _BaseGitOidStringableObject:
    def __str__(self) -> str:
        return "1" * 40

@pytest.mark.parametrize("left,right", IDENTITY_PAIRS)
def test_identity_collapse_mutations_are_rejected(left: str, right: str) -> None:
    values = _identity_values()
    assert _identity_noncollapse(values)
    values[right] = values[left]
    assert not _identity_noncollapse(values)


def test_nominal_identity_swaps_and_general_collapses_are_rejected() -> None:
    control = _identity_values()
    assert _nominal_identity_binding_valid(control)
    for index, name in enumerate(IDENTITIES):
        other = IDENTITIES[(index + 1) % len(IDENTITIES)]
        collapsed = dict(control)
        collapsed[name] = collapsed[other]
        assert not _nominal_identity_binding_valid(collapsed), (name, other, "collapse")
        swapped = dict(control)
        swapped[name], swapped[other] = swapped[other], swapped[name]
        assert not _nominal_identity_binding_valid(swapped), (name, other, "swap")


def test_legacy_transition_and_counter_identities_are_not_reused() -> None:
    clause = " ".join(_section(DOC, f"{CLAUSES[1][0]} — {CLAUSES[1][1]}", 2).split())
    for legacy in (
        "`TransitionCommand.command_ref`",
        "`TransitionEvent.event_ref`",
        "transition idempotency keys",
        "`FiniteBacklog.backlog_id`",
        "current `attempt_count`",
        "current `repair_count`",
        "standing-lease digest",
    ):
        assert legacy in clause
    assert "must not be reused as any identity above" in clause


def test_command_bindings_ceilings_and_replay_mutations_are_exact() -> None:
    command = _full_record("WorkerCommandV1")
    identity = _identity_object("WorkerCommandV1")
    domain = GOLDEN_META["WorkerCommandV1"][1]
    expected_digest = GOLDEN_META["WorkerCommandV1"][3]
    mutations = {
        "widen path ceiling": lambda value: value["path_ceiling"].append("fourth.txt"),
        "change base OID": lambda value: value.__setitem__("base_git_oid", "0" * 40),
        "change WorkSpec ref": lambda value: value.__setitem__("work_spec_ref", "work-spec.other"),
        "change WorkSpec digest": lambda value: value.__setitem__("work_spec_digest", "0" * 64),
        "change validation requirement": lambda value: value.__setitem__("validation_requirement_ref", "validation.other"),
        "change review requirement": lambda value: value.__setitem__("review_requirement_ref", "review.other"),
        "change ceiling": lambda value: value["effect_ceilings"].__setitem__("max_changed_files", 4),
    }
    for name, mutate in mutations.items():
        changed = deepcopy(identity)
        mutate(changed)
        assert _digest(domain, _canonical(changed)) != expected_digest, name

    with_route = deepcopy(identity)
    with_route["adapter_kind"] = "direct_local_bootstrap"
    assert set(with_route) != set(identity)
    assert not _identity_bytes_are_valid("WorkerCommandV1", _canonical(with_route))

    assert command["effect_ceilings"]["max_local_commits"] == 0
    for field in ("max_pushes", "max_pull_requests", "max_merges", "max_deployments"):
        assert command["effect_ceilings"][field] == 0
    assert _command_replay(command, deepcopy(command)) == "exact_replay"
    changed_digest = deepcopy(command)
    changed_digest["command_digest"] = "0" * 64
    assert _command_replay(command, changed_digest) == "conflict"


def test_command_effect_fence_digest_graph_is_acyclic_and_coherent() -> None:
    command_identity = _identity_object("WorkerCommandV1")
    effect_fence = _full_record("EffectFenceV1")
    command = _full_record("WorkerCommandV1")
    assert "effect_fence_ref" in command_identity
    assert "effect_fence_digest" not in command_identity
    assert "command_digest" not in command_identity
    assert effect_fence["command_digest"] == command["command_digest"]
    assert command["effect_fence_digest"] == effect_fence["effect_fence_digest"]


def test_authority_and_fence_mutations_fail_complete_relation() -> None:
    valid = {
        "structural_valid": True,
        "parent_grant_valid": True,
        "subordinate_authorization_valid": True,
        "fence_valid": True,
        "not_expired": True,
        "not_revoked": True,
        "repository_base_path_match": True,
        "current_global_stop_match": True,
    }
    assert _complete_authority(**valid)
    for field in valid:
        mutated = dict(valid)
        mutated[field] = False
        assert not _complete_authority(**mutated), field
    assert not _complete_authority(structural_valid=True)

    for model, fields in (
        ("AttemptFenceV1", ("parent_standing_grant_ref", "attempt_authorization_ref", "expires_at", "global_stop_version", "repository_ref", "base_git_oid", "path_ceiling", "allowed_effect_classes")),
        ("EffectFenceV1", ("parent_standing_grant_ref", "effect_authorization_ref", "expires_at", "global_stop_version", "repository_ref", "base_git_oid", "path_ceiling", "effect_class")),
    ):
        domain = GOLDEN_META[model][1]
        expected = GOLDEN_META[model][3]
        for field in fields:
            mutated = _identity_object(model)
            if isinstance(mutated[field], list):
                mutated[field] = list(mutated[field]) + ["mutated"]
            elif isinstance(mutated[field], int):
                mutated[field] += 1
            else:
                mutated[field] = "mutated.value"
            assert _digest(domain, _canonical(mutated)) != expected, (model, field)


def test_delivery_identity_and_redelivery_are_separate_from_command_identity() -> None:
    delivery = _full_record("DeliveryEnvelopeV1")
    command = _full_record("WorkerCommandV1")
    redelivery = deepcopy(delivery)
    redelivery["delivery_attempt_ref"] = "delivery-attempt.0002"
    redelivery["adapter_safe_correlation_ref"] = "adapter-correlation.0002"
    identity = {key: value for key, value in redelivery.items() if key != "delivery_envelope_digest"}
    redelivery["delivery_envelope_digest"] = _digest(GOLDEN_META["DeliveryEnvelopeV1"][1], _canonical(identity))
    assert _redelivery_valid_with_canonical_relations(delivery, redelivery)
    assert len(delivery) == 15
    assert len(identity) == 14
    assert set(delivery) == set(_field_names("DeliveryEnvelopeV1"))
    assert delivery["program_ref"] == command["program_ref"]
    assert delivery["program_version_ref"] == command["program_version_ref"]
    assert redelivery["semantic_attempt_ref"] == delivery["semantic_attempt_ref"]
    assert redelivery["effect_intent_ref"] == delivery["effect_intent_ref"]
    assert redelivery["command_ref"] == delivery["command_ref"]
    assert redelivery["command_digest"] == delivery["command_digest"] == command["command_digest"]

    missing = deepcopy(delivery)
    missing.pop("delivery_attempt_ref")
    assert set(missing) != set(_field_names("DeliveryEnvelopeV1"))
    command_with_delivery = _identity_object("WorkerCommandV1")
    command_with_delivery["delivery_attempt_ref"] = redelivery["delivery_attempt_ref"]
    assert not _identity_bytes_are_valid("WorkerCommandV1", _canonical(command_with_delivery))

    forbidden_changes = {
        "attempt-fence ref": ("attempt_fence_ref", "attempt-fence.0002"),
        "attempt-fence digest": ("attempt_fence_digest", "0" * 64),
        "effect-fence ref": ("effect_fence_ref", "effect-fence.0002"),
        "effect-fence digest": ("effect_fence_digest", "1" * 64),
        "adapter kind": ("adapter_kind", "execution_substrate"),
        "program": ("program_ref", "program.other"),
        "program version": ("program_version_ref", "program-version.other"),
        "semantic attempt": ("semantic_attempt_ref", "semantic-attempt.0002"),
        "effect intent": ("effect_intent_ref", "effect-intent.other"),
        "command ref": ("command_ref", "worker-command.other"),
        "command digest": ("command_digest", "2" * 64),
    }
    for name, (field, value) in forbidden_changes.items():
        changed = deepcopy(redelivery)
        changed[field] = value
        changed_identity = {key: item for key, item in changed.items() if key != "delivery_envelope_digest"}
        changed["delivery_envelope_digest"] = _digest(GOLDEN_META["DeliveryEnvelopeV1"][1], _canonical(changed_identity))
        assert not _redelivery_valid_with_canonical_relations(delivery, changed), name

    extra = deepcopy(redelivery)
    extra["extra"] = "not-allowed"
    assert not _redelivery_valid_with_canonical_relations(delivery, extra)
    missing = deepcopy(redelivery)
    missing.pop("effect_fence_ref")
    assert not _redelivery_valid_with_canonical_relations(delivery, missing)

    unchanged_correlation = deepcopy(redelivery)
    unchanged_correlation["adapter_safe_correlation_ref"] = delivery["adapter_safe_correlation_ref"]
    unchanged_identity = {key: item for key, item in unchanged_correlation.items() if key != "delivery_envelope_digest"}
    unchanged_correlation["delivery_envelope_digest"] = _digest(GOLDEN_META["DeliveryEnvelopeV1"][1], _canonical(unchanged_identity))
    assert not _redelivery_valid_with_canonical_relations(delivery, unchanged_correlation)


def test_complete_delivery_validation_precedes_redelivery_delta() -> None:
    original = _full_record("DeliveryEnvelopeV1")
    valid = _valid_redelivery_candidate(original)
    assert _redelivery_valid_with_canonical_relations(original, valid)
    mutations: tuple[tuple[str, str, object, bool], ...] = (
        ("object attempt", "delivery_attempt_ref", {"ref": "delivery-attempt.0002"}, True),
        ("array attempt", "delivery_attempt_ref", ["delivery-attempt.0002"], True),
        ("boolean attempt", "delivery_attempt_ref", True, True),
        ("reserved correlation", "adapter_safe_correlation_ref", "connector-secret.0001", True),
        ("absolute correlation", "adapter_safe_correlation_ref", "/private/tmp/correlation", True),
        ("invalid digest", "delivery_envelope_digest", "0" * 63, False),
        ("wrong schema", "schema_id", "governed-execution.nwp-delivery-envelope.v2", True),
        ("invalid adapter", "adapter_kind", "bridge", True),
    )
    for name, field, wrong, reseal in mutations:
        changed = deepcopy(valid)
        changed[field] = wrong
        if reseal:
            changed = _reseal_single_digest_record("DeliveryEnvelopeV1", changed)
        assert not _redelivery_valid_with_canonical_relations(original, changed), name
    unknown = deepcopy(valid)
    unknown["metadata"] = "forbidden"
    assert not _redelivery_valid_with_canonical_relations(original, unknown)
    missing = deepcopy(valid)
    missing.pop("effect_fence_ref")
    assert not _redelivery_valid_with_canonical_relations(original, missing)
    route = deepcopy(valid)
    route["adapter_kind"] = "execution_substrate"
    route = _reseal_single_digest_record("DeliveryEnvelopeV1", route)
    assert not _redelivery_valid_with_canonical_relations(original, route)
    malformed_original = deepcopy(original)
    malformed_original["adapter_safe_correlation_ref"] = "workspace-secret.0001"
    malformed_original = _reseal_single_digest_record("DeliveryEnvelopeV1", malformed_original)
    assert not _redelivery_valid_with_canonical_relations(malformed_original, valid)


def test_redelivery_core_signature_has_only_original_and_candidate_effect_fences() -> None:
    signature = inspect.signature(_redelivery_valid)
    parameters = signature.parameters
    assert tuple(parameters)[:2] == ("original", "candidate")
    assert parameters["original_effect_fence"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["candidate_effect_fence"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["original_effect_fence"].default is inspect.Parameter.empty
    assert parameters["candidate_effect_fence"].default is inspect.Parameter.empty
    assert "effect_fence" not in parameters
    assert "later_effect_fence" not in parameters


def test_redelivery_core_rejects_missing_or_contradictory_split_fences() -> None:
    original = _delivery_for_vector("author")
    candidate = _valid_redelivery_candidate(original)
    attempt = _full_record("AttemptFenceV1")
    command = _full_record("WorkerCommandV1")
    author = _effect_fence_for_vector("author")
    assert _redelivery_valid(
        original,
        candidate,
        original_effect_fence=author,
        candidate_effect_fence=author,
        attempt_fence=attempt,
        author_command=command,
        author_effect_fence=author,
    )

    for contradictory in (
        _effect_fence_for_vector("validation"),
        _effect_fence_for_vector("review"),
    ):
        assert not _redelivery_valid(
            original,
            candidate,
            original_effect_fence=author,
            candidate_effect_fence=contradictory,
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=author,
        )

    with pytest.raises(TypeError):
        _redelivery_valid(
            original,
            candidate,
            candidate_effect_fence=author,
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=author,
        )
    with pytest.raises(TypeError):
        _redelivery_valid(
            original,
            candidate,
            original_effect_fence=author,
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=author,
        )

    for malformed in (
        None,
        {},
        {"effect_fence_ref": "effect-fence.incomplete"},
        _RelatedRecordDictSubclass(author),
    ):
        assert not _redelivery_valid(
            original,
            candidate,
            original_effect_fence=author,
            candidate_effect_fence=malformed,
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=author,
        )

    with pytest.raises(TypeError):
        _redelivery_valid(
            original,
            candidate,
            original_effect_fence=author,
            candidate_effect_fence=author,
            effect_fence=author,
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=author,
        )


def test_redelivery_wrapper_defaults_both_fences_only_for_exact_unset() -> None:
    original = _delivery_for_vector("author")
    candidate = _valid_redelivery_candidate(original)
    author = _effect_fence_for_vector("author")
    assert _redelivery_valid_with_canonical_relations(original, candidate)
    assert _redelivery_valid_with_canonical_relations(
        original,
        candidate,
        original_effect_fence=author,
        candidate_effect_fence=author,
    )
    assert not _redelivery_valid_with_canonical_relations(
        original, candidate, original_effect_fence=author
    )
    assert not _redelivery_valid_with_canonical_relations(
        original, candidate, candidate_effect_fence=author
    )
    for malformed in (
        None,
        {},
        {"effect_fence_ref": "effect-fence.incomplete"},
        _RelatedRecordDictSubclass(author),
    ):
        assert not _redelivery_valid_with_canonical_relations(
            original,
            candidate,
            original_effect_fence=malformed,
            candidate_effect_fence=author,
        )

    with pytest.raises(TypeError):
        _redelivery_valid_with_canonical_relations(
            original, candidate, effect_fence=author
        )


def test_author_effect_fence_is_exactly_post_bound_to_worker_command() -> None:
    attempt_fence = _full_record("AttemptFenceV1")
    author_command = _full_record("WorkerCommandV1")
    author_effect_fence = _effect_fence_for_vector("author")
    validation_effect_fence = _effect_fence_for_vector("validation")

    assert _effect_fence_record_valid_with_canonical_relations(
        author_effect_fence,
        attempt_fence=attempt_fence,
        author_command=author_command,
        author_effect_fence=author_effect_fence,
    )
    assert _effect_fence_record_valid_with_canonical_relations(
        validation_effect_fence,
        attempt_fence=attempt_fence,
        author_command=author_command,
        author_effect_fence=author_effect_fence,
    )

    sibling_mutations = (
        ("expires_at", "2029-12-31T23:59:59Z"),
        ("effect_authorization_ref", "effect-authorization.sibling"),
        ("effect_authorization_digest", "8" * 64),
        ("effect_ceilings", {**author_effect_fence["effect_ceilings"], "max_wall_seconds": 3599}),
    )
    for field_name, wrong in sibling_mutations:
        sibling = deepcopy(author_effect_fence)
        sibling[field_name] = wrong
        sibling = _reseal_single_digest_record("EffectFenceV1", sibling)
        assert not _effect_fence_record_valid_with_canonical_relations(
            sibling,
            attempt_fence=attempt_fence,
            author_command=author_command,
            author_effect_fence=sibling,
        ), field_name
        assert not _effect_fence_record_valid_with_canonical_relations(
            validation_effect_fence,
            attempt_fence=attempt_fence,
            author_command=author_command,
            author_effect_fence=sibling,
        ), field_name


def test_observation_matrix_rejects_wrong_sources_payloads_and_decision_fields() -> None:
    record = _observation_for_vector("author")
    fence = _effect_fence_for_vector("author")
    delivery = _delivery_for_vector("author")
    command = _full_record("WorkerCommandV1")
    assert _observation_valid_with_canonical_relations(
        record,
        effect_fence=fence,
        delivery=delivery,
        author_command=command,
    )
    mutations = {
        "invalid source/kind pair": ("source_kind", "worker"),
        "arbitrary payload": ("payload", {"anything": True}),
        "missing binding": ("command_ref", None),
        "acceptance field": ("accepted", True),
        "repair field": ("repair", True),
        "replan field": ("replan", True),
        "retry authorization field": ("retry_authorized", True),
        "publication field": ("published", True),
    }
    for name, (field, value) in mutations.items():
        changed = deepcopy(record)
        if value is None:
            changed.pop(field)
        else:
            changed[field] = value
        if "observation_digest" in changed:
            changed = _reseal_observation(changed)
        assert not _observation_valid_with_canonical_relations(changed, effect_fence=fence, delivery=delivery, author_command=command), name

    for row in OBSERVATION_ROWS:
        kind = row[1].strip("`")
        sources, outcomes, conditional_key = OBSERVATION_SPEC[kind]
        assert sources
        assert outcomes
        assert conditional_key in CONDITIONAL_FIELDS


def test_four_current_effect_originating_author_relation_vectors_are_exact() -> None:
    command = _full_record("WorkerCommandV1")
    observed: dict[str, tuple[dict[str, object], dict[str, object], dict[str, object]]] = {}
    for vector in ("author", "validation", "review", "cancellation"):
        fence = _effect_fence_for_vector(vector)
        delivery = _delivery_for_vector(vector)
        observation = _observation_for_vector(vector)
        expected_fence, expected_delivery, expected_observation = RELATION_DIGESTS[vector]
        assert fence["effect_fence_digest"] == expected_fence
        assert delivery["delivery_envelope_digest"] == expected_delivery
        assert observation["observation_digest"] == expected_observation
        assert _observation_valid_with_canonical_relations(
            observation,
            effect_fence=fence,
            delivery=delivery,
            author_command=command,
        )
        observed[vector] = observation, fence, delivery

    assert {items[0]["command_ref"] for items in observed.values()} == {"worker-command.0001"}
    assert {items[0]["command_digest"] for items in observed.values()} == {GOLDEN_META["WorkerCommandV1"][3]}
    assert {items[0]["semantic_attempt_ref"] for items in observed.values()} == {"semantic-attempt.0001"}
    assert len({items[0]["effect_intent_ref"] for items in observed.values()}) == 4
    assert len({items[0]["effect_fence_ref"] for items in observed.values()}) == 4
    assert len({items[0]["delivery_attempt_ref"] for items in observed.values()}) == 4
    assert len({items[0]["source_invocation_ref"] for items in observed.values()}) == 4
    assert observed["validation"][1]["portable_capsule_digest"] == GOLDEN_META["CandidateCapsuleManifestV1"][3]
    assert observed["review"][1]["portable_capsule_digest"] == GOLDEN_META["CandidateCapsuleManifestV1"][3]
    assert observed["cancellation"][1]["portable_capsule_digest"] is None
    author_target = _effect_fence_for_vector("author")
    cancellation = observed["cancellation"][1]
    assert cancellation["cancellation_target_effect_intent_ref"] == author_target["effect_intent_ref"]
    assert cancellation["cancellation_target_effect_fence_ref"] == author_target["effect_fence_ref"]
    assert cancellation["cancellation_target_effect_fence_digest"] == author_target["effect_fence_digest"]


@pytest.mark.parametrize("kind", tuple(OBSERVATION_SPEC))
def test_every_observation_kind_enforces_current_effect_relation(kind: str) -> None:
    command = _full_record("WorkerCommandV1")
    record, fence, delivery = _observation_for_kind(kind)
    assert _observation_valid_with_canonical_relations(
        record,
        effect_fence=fence,
        delivery=delivery,
        author_command=command,
    )
    wrong = next(effect for effect in ("author_candidate", "validate_candidate", "review_candidate", "cancel_effect", "local_git_commit") if effect not in EFFECT_CLASSES_BY_OBSERVATION[kind])
    if wrong == "local_git_commit":
        wrong_record, wrong_fence, wrong_delivery = _observation_for_kind(kind)
        fence_identity = {field: value for field, value in wrong_fence.items() if field != "effect_fence_digest"}
        fence_identity["effect_class"] = wrong
        wrong_fence = _sealed_record("EffectFenceV1", fence_identity)
        delivery_identity = {field: value for field, value in wrong_delivery.items() if field != "delivery_envelope_digest"}
        delivery_identity["effect_fence_digest"] = wrong_fence["effect_fence_digest"]
        wrong_delivery = _sealed_record("DeliveryEnvelopeV1", delivery_identity)
        wrong_record["effect_fence_digest"] = wrong_fence["effect_fence_digest"]
        wrong_record = _reseal_observation(wrong_record)
    else:
        wrong_record, wrong_fence, wrong_delivery = _observation_for_kind(kind, wrong)
    assert not _observation_valid_with_canonical_relations(
        wrong_record,
        effect_fence=wrong_fence,
        delivery=wrong_delivery,
        author_command=command,
    )


@pytest.mark.parametrize("vector", ("validation", "review", "cancellation"))
def test_non_authoring_observation_rejects_retained_author_effect_fence(vector: str) -> None:
    command = _full_record("WorkerCommandV1")
    observation = _observation_for_vector(vector)
    author_fence = _effect_fence_for_vector("author")
    author_delivery = _delivery_for_vector("author")
    changed = deepcopy(observation)
    for field in ("effect_intent_ref", "effect_fence_ref", "effect_fence_digest", "delivery_attempt_ref"):
        changed[field] = author_delivery[field]
    changed = _reseal_observation(changed)
    assert not _observation_valid_with_canonical_relations(changed, effect_fence=author_fence, delivery=author_delivery, author_command=command)


def test_observation_candidate_capsule_and_cancellation_relations_close() -> None:
    command = _full_record("WorkerCommandV1")
    manifest = _full_record("CandidateCapsuleManifestV1")
    author_effect = _effect_fence_for_vector("author")
    validation = _observation_for_vector("validation")
    validation_fence = _effect_fence_for_vector("validation")
    validation_delivery = _delivery_for_vector("validation")
    assert _observation_valid_with_canonical_relations(
        validation,
        effect_fence=validation_fence,
        delivery=validation_delivery,
        author_command=command,
        author_effect_fence=author_effect,
        capsule_manifest=manifest,
    )
    for field, wrong in (
        ("candidate_ref", "candidate.other"),
        ("capsule_manifest_ref", "capsule-manifest.other"),
        ("portable_capsule_digest", "e" * 64),
    ):
        changed = deepcopy(validation)
        changed[field] = wrong
        changed = _reseal_observation(changed)
        assert not _observation_valid_with_canonical_relations(
            changed,
            effect_fence=validation_fence,
            delivery=validation_delivery,
            author_command=command,
            author_effect_fence=author_effect,
            capsule_manifest=manifest,
        ), field

    for vector in ("validation", "review"):
        observation = _observation_for_vector(vector)
        fence = _effect_fence_for_vector(vector)
        delivery = _delivery_for_vector(vector)
        fence["portable_capsule_digest"] = None
        fence = _reseal_single_digest_record("EffectFenceV1", fence)
        delivery["effect_fence_digest"] = fence["effect_fence_digest"]
        delivery = _reseal_single_digest_record("DeliveryEnvelopeV1", delivery)
        observation["effect_fence_digest"] = fence["effect_fence_digest"]
        observation = _reseal_observation(observation)
        assert not _observation_valid_with_canonical_relations(
            observation,
            effect_fence=fence,
            delivery=delivery,
            author_command=command,
            author_effect_fence=author_effect,
            capsule_manifest=manifest,
        ), vector

    capsule_mutations = (
        ("semantic_attempt_ref", "semantic-attempt.other"),
        ("effect_intent_ref", "effect-intent.validate.0001"),
        ("command_ref", "worker-command.other"),
    )
    for field, wrong in capsule_mutations:
        other = deepcopy(manifest)
        other[field] = wrong
        other = _reseal_manifest(other)
        changed = deepcopy(validation)
        changed["portable_capsule_digest"] = other["portable_capsule_digest"]
        changed = _reseal_observation(changed)
        assert not _observation_valid_with_canonical_relations(
            changed,
            effect_fence=validation_fence,
            delivery=validation_delivery,
            author_command=command,
            author_effect_fence=author_effect,
            capsule_manifest=other,
        ), field

    cancellation = _observation_for_vector("cancellation")
    cancellation_fence = _effect_fence_for_vector("cancellation")
    cancellation_delivery = _delivery_for_vector("cancellation")
    bad_fence = deepcopy(cancellation_fence)
    bad_fence["cancellation_target_effect_fence_digest"] = "f" * 64
    bad_fence = _reseal_single_digest_record("EffectFenceV1", bad_fence)
    bad_delivery = deepcopy(cancellation_delivery)
    bad_delivery["effect_fence_digest"] = bad_fence["effect_fence_digest"]
    bad_delivery = _reseal_single_digest_record("DeliveryEnvelopeV1", bad_delivery)
    bad_observation = deepcopy(cancellation)
    bad_observation["effect_fence_digest"] = bad_fence["effect_fence_digest"]
    bad_observation = _reseal_observation(bad_observation)
    assert not _observation_valid_with_canonical_relations(
        bad_observation,
        effect_fence=bad_fence,
        delivery=bad_delivery,
        author_command=command,
        cancellation_target=author_effect,
    )


def test_cancellation_target_relations_and_capsule_consuming_control_close() -> None:
    attempt = _full_record("AttemptFenceV1")
    command = _full_record("WorkerCommandV1")
    author = _effect_fence_for_vector("author")
    validation = _effect_fence_for_vector("validation")
    review = _effect_fence_for_vector("review")
    cancellation = _effect_fence_for_vector("cancellation_validation")

    for field, wrong in (
        ("program_version_ref", "program-version.other"),
        ("accepted_intent_revision_ref", "intent-revision.other"),
        ("work_item_ref", "work-item.other"),
        ("attempt_fence_ref", "attempt-fence.other"),
    ):
        target = deepcopy(validation)
        target[field] = wrong
        target = _reseal_single_digest_record("EffectFenceV1", target)
        current = _retargeted_cancellation(cancellation, target)
        assert not _effect_fence_record_valid_with_canonical_relations(
            current,
            attempt_fence=attempt,
            author_command=command,
            cancellation_target=target,
        ), field

    intent_disagreement = deepcopy(cancellation)
    intent_disagreement["cancellation_target_effect_intent_ref"] = review[
        "effect_intent_ref"
    ]
    intent_disagreement = _reseal_single_digest_record(
        "EffectFenceV1", intent_disagreement
    )
    assert not _effect_fence_record_valid_with_canonical_relations(
        intent_disagreement,
        attempt_fence=attempt,
        author_command=command,
        cancellation_target=validation,
    )

    for field, wrong in (
        ("cancellation_target_effect_intent_ref", validation["effect_intent_ref"]),
        ("cancellation_target_effect_fence_ref", validation["effect_fence_ref"]),
        (
            "cancellation_target_effect_fence_digest",
            validation["effect_fence_digest"],
        ),
    ):
        noncancellation = deepcopy(author)
        noncancellation[field] = wrong
        noncancellation = _reseal_single_digest_record(
            "EffectFenceV1", noncancellation
        )
        assert not _effect_fence_record_valid_with_canonical_relations(
            noncancellation,
            attempt_fence=attempt,
            author_command=command,
            cancellation_target=None,
            author_effect_fence=author,
        ), field

    cancellation_target = _effect_fence_for_vector("cancellation")
    nested_cancellation = _retargeted_cancellation(
        cancellation, cancellation_target
    )
    nested_cancellation["portable_capsule_digest"] = None
    nested_cancellation = _reseal_single_digest_record(
        "EffectFenceV1", nested_cancellation
    )
    assert not _effect_fence_record_valid_with_canonical_relations(
        nested_cancellation,
        attempt_fence=attempt,
        author_command=command,
        cancellation_target=cancellation_target,
    )

    local_git = _local_git_effect_fence()
    git_target = _retargeted_cancellation(cancellation, local_git)
    git_target["portable_capsule_digest"] = local_git[
        "portable_capsule_digest"
    ]
    git_target = _reseal_single_digest_record("EffectFenceV1", git_target)
    assert not _effect_fence_record_valid_with_canonical_relations(
        git_target,
        attempt_fence=attempt,
        author_command=command,
        cancellation_target=local_git,
    )


@pytest.mark.parametrize("field", tuple(sorted(SAFE_REF_FIELDS)))
@pytest.mark.parametrize("wrong", ({"object": "value"}, ["array"], True, 7))
def test_observation_rejects_every_wrong_reference_field_type(field: str, wrong: object) -> None:
    command = _full_record("WorkerCommandV1")
    record = _observation_for_vector("author")
    fence = _effect_fence_for_vector("author")
    delivery = _delivery_for_vector("author")
    assert field in record
    changed = deepcopy(record)
    changed[field] = wrong
    changed = _reseal_observation(changed)
    assert not _observation_valid_with_canonical_relations(changed, effect_fence=fence, delivery=delivery, author_command=command)


@pytest.mark.parametrize("field", tuple(sorted(OBSERVATION_DIGEST_FIELDS - {"observation_digest"})))
@pytest.mark.parametrize("wrong", ("A" * 64, "0" * 63, True, {"digest": "0" * 64}))
def test_observation_rejects_every_wrong_digest_field_type_or_shape(field: str, wrong: object) -> None:
    command = _full_record("WorkerCommandV1")
    record = _observation_for_vector("author")
    fence = _effect_fence_for_vector("author")
    delivery = _delivery_for_vector("author")
    assert field in record
    changed = deepcopy(record)
    changed[field] = wrong
    changed = _reseal_observation(changed)
    assert not _observation_valid_with_canonical_relations(changed, effect_fence=fence, delivery=delivery, author_command=command)


@pytest.mark.parametrize("wrong", (True, -256, 256, 1.0, "0", None))
def test_process_exit_code_requires_exact_bounded_integer(wrong: object) -> None:
    command = _full_record("WorkerCommandV1")
    record, fence, delivery = _observation_for_kind("process_exited")
    changed = deepcopy(record)
    changed["process_exit_code"] = wrong
    changed = _reseal_observation(changed)
    assert not _observation_valid_with_canonical_relations(changed, effect_fence=fence, delivery=delivery, author_command=command)


def test_observation_rejects_wrong_source_kind_and_source_timestamp_types() -> None:
    command = _full_record("WorkerCommandV1")
    record = _observation_for_vector("validation")
    fence = _effect_fence_for_vector("validation")
    delivery = _delivery_for_vector("validation")
    for field, wrong in (("source_kind", "worker"), ("observed_at", 7), ("observed_at", "2026-08-08T18:01:00.000Z")):
        changed = deepcopy(record)
        changed[field] = wrong
        changed = _reseal_observation(changed)
        assert not _observation_valid_with_canonical_relations(changed, effect_fence=fence, delivery=delivery, author_command=command)


def test_whole_second_utc_is_calendar_aware_and_exact() -> None:
    accepted = (
        "2024-02-29T23:59:59Z",
        "2026-01-01T00:00:00Z",
    )
    rejected = (
        "2026-00-01T00:00:00Z",
        "2026-13-01T00:00:00Z",
        "2026-02-29T00:00:00Z",
        "2024-02-30T00:00:00Z",
        "2026-12-31T24:00:00Z",
        "2026-12-31T23:60:00Z",
        "2026-12-31T23:59:60Z",
        "2026-99-99T99:99:99Z",
        "2026-12-31T23:59:59.000Z",
        "2026-12-31T23:59:59+00:00",
        "2026-12-31T23:59:59z",
        " 2026-12-31T23:59:59Z",
        "2026-12-31T23:59:59Z ",
    )
    assert all(_source_timestamp(value) for value in accepted)
    assert not any(_source_timestamp(value) for value in rejected)

    command = _full_record("WorkerCommandV1")
    record = _observation_for_vector("validation")
    fence = _effect_fence_for_vector("validation")
    delivery = _delivery_for_vector("validation")
    for value in rejected:
        changed = deepcopy(record)
        changed["observed_at"] = value
        changed = _reseal_observation(changed)
        assert not _observation_valid_with_canonical_relations(changed, effect_fence=fence, delivery=delivery, author_command=command), value
    leap = deepcopy(record)
    leap["observed_at"] = accepted[0]
    leap = _reseal_observation(leap)
    assert _observation_valid_with_canonical_relations(leap, effect_fence=fence, delivery=delivery, author_command=command)


@pytest.mark.parametrize(
    "field,wrong",
    (
        ("schema_id", True),
        ("source_kind", {"kind": "validator"}),
        ("observation_kind", ["validation_completed"]),
        ("outcome", 1),
        ("reason_code", True),
        ("reason_code", "_invalid-leading-underscore"),
        ("reason_code", "r" * 97),
        ("observed_at", False),
        ("observed_at", "2026-08-08T18:01:00+00:00"),
    ),
)
def test_observation_rejects_every_other_scalar_field_type_or_shape(field: str, wrong: object) -> None:
    command = _full_record("WorkerCommandV1")
    record = _observation_for_vector("validation")
    fence = _effect_fence_for_vector("validation")
    delivery = _delivery_for_vector("validation")
    record[field] = wrong
    record = _reseal_observation(record)
    assert not _observation_valid_with_canonical_relations(record, effect_fence=fence, delivery=delivery, author_command=command)


@pytest.mark.parametrize(
    "wrong",
    (
        "not-an-array",
        ["evidence.valid.0001", "evidence.valid.0001"],
        ["evidence.z.0001", "evidence.a.0001"],
        [True],
        [{"ref": "evidence.valid.0001"}],
        [f"evidence.{index:02d}" for index in range(33)],
    ),
)
def test_observation_evidence_refs_are_exact_bounded_sorted_safe_array(wrong: object) -> None:
    command = _full_record("WorkerCommandV1")
    record = _observation_for_vector("validation")
    fence = _effect_fence_for_vector("validation")
    delivery = _delivery_for_vector("validation")
    record["evidence_refs"] = wrong
    record = _reseal_observation(record)
    assert not _observation_valid_with_canonical_relations(record, effect_fence=fence, delivery=delivery, author_command=command)


@pytest.mark.parametrize("kind", tuple(OBSERVATION_SPEC))
def test_every_observation_kind_enforces_exact_conditional_keyset(kind: str) -> None:
    command = _full_record("WorkerCommandV1")
    record, fence, delivery = _observation_for_kind(kind)
    expected = CONDITIONAL_FIELDS[OBSERVATION_SPEC[kind][2]]
    if expected:
        changed = deepcopy(record)
        changed.pop(next(iter(expected)))
    else:
        changed = deepcopy(record)
        changed["candidate_ref"] = "candidate.0001"
    changed = _reseal_observation(changed)
    assert not _observation_valid_with_canonical_relations(changed, effect_fence=fence, delivery=delivery, author_command=command)


def test_observation_digest_and_unknown_key_are_independently_rejected() -> None:
    command = _full_record("WorkerCommandV1")
    record = _observation_for_vector("author")
    fence = _effect_fence_for_vector("author")
    delivery = _delivery_for_vector("author")
    wrong_digest = deepcopy(record)
    wrong_digest["observation_digest"] = True
    assert not _observation_valid_with_canonical_relations(wrong_digest, effect_fence=fence, delivery=delivery, author_command=command)
    unknown = deepcopy(record)
    unknown["metadata"] = "forbidden"
    unknown = _reseal_observation(unknown)
    assert not _observation_valid_with_canonical_relations(unknown, effect_fence=fence, delivery=delivery, author_command=command)


def test_base_git_oid_requires_exact_builtin_string_across_relation_graph() -> None:
    numeric_oid = int("1" * 40)
    assert str(numeric_oid) == "1" * 40
    assert _base_git_oid_valid("sha1", "1" * 40)
    assert not _base_git_oid_valid("sha1", numeric_oid)
    assert not _base_git_oid_valid(
        "sha1", _BaseGitOidStringSubclass("1" * 40)
    )
    assert not _base_git_oid_valid("sha1", _BaseGitOidStringableObject())

    work_spec = _identity_object("WorkSpecV1")
    work_spec["base_git_oid"] = numeric_oid
    assert not _identity_bytes_are_valid("WorkSpecV1", _canonical(work_spec))

    attempt_fence = _full_record("AttemptFenceV1")
    attempt_fence["base_git_oid"] = numeric_oid
    attempt_fence = _reseal_single_digest_record("AttemptFenceV1", attempt_fence)
    assert not _attempt_fence_record_valid(attempt_fence)

    command = _full_record("WorkerCommandV1")
    command["base_git_oid"] = numeric_oid
    command = _reseal_author_command(command)
    assert not _author_command_record_valid(command)

    effect_fence = _effect_fence_for_vector("author")
    effect_fence["base_git_oid"] = numeric_oid
    effect_fence = _reseal_single_digest_record("EffectFenceV1", effect_fence)
    assert not _effect_fence_record_valid_with_canonical_relations(
        effect_fence,
        attempt_fence=_full_record("AttemptFenceV1"),
        author_command=_full_record("WorkerCommandV1"),
        author_effect_fence=effect_fence,
    )

    manifest = _full_record("CandidateCapsuleManifestV1")
    manifest["base_git_oid"] = numeric_oid
    assert not _manifest_valid_with_canonical_relations(_reseal_manifest(manifest))


def test_explicit_malformed_related_records_are_never_defaulted() -> None:
    command = _full_record("WorkerCommandV1")
    attempt_fence = _full_record("AttemptFenceV1")
    author_effect_fence = _effect_fence_for_vector("author")
    delivery = _full_record("DeliveryEnvelopeV1")
    redelivery = _valid_redelivery_candidate(delivery)
    observation = _full_record("WorkerObservationV1")
    manifest = _full_record("CandidateCapsuleManifestV1")

    for malformed in (None, {}, [], "", 0, False):
        assert not _redelivery_valid_with_canonical_relations(
            delivery, redelivery, original_effect_fence=malformed
        )
        assert not _redelivery_valid_with_canonical_relations(
            delivery, redelivery, candidate_effect_fence=malformed
        )
        assert not _redelivery_valid_with_canonical_relations(delivery, redelivery, attempt_fence=malformed)
        assert not _redelivery_valid_with_canonical_relations(delivery, redelivery, author_command=malformed)
        assert not _delivery_record_valid_with_canonical_relations(delivery, effect_fence=malformed)
        assert not _delivery_record_valid_with_canonical_relations(delivery, attempt_fence=malformed)
        assert not _delivery_record_valid_with_canonical_relations(delivery, author_command=malformed)
        assert not _delivery_record_valid_with_canonical_relations(
            delivery, author_effect_fence=malformed
        )
        assert not _observation_valid_with_canonical_relations(
            observation,
            effect_fence=author_effect_fence,
            delivery=delivery,
            author_command=command,
            attempt_fence=malformed,
        )
        assert not _observation_valid_with_canonical_relations(
            observation,
            effect_fence=author_effect_fence,
            delivery=delivery,
            author_command=command,
            author_effect_fence=malformed,
        )
        assert not _observation_valid_with_canonical_relations(
            observation,
            effect_fence=author_effect_fence,
            delivery=delivery,
            author_command=command,
            capsule_manifest=malformed,
        )
        assert not _observation_valid_with_canonical_relations(
            observation,
            effect_fence=author_effect_fence,
            delivery=malformed,
            author_command=command,
        )
        assert not _observation_valid_with_canonical_relations(
            observation,
            effect_fence=author_effect_fence,
            delivery=delivery,
            author_command=malformed,
        )
        assert not _manifest_valid_with_canonical_relations(manifest, command=malformed)
        assert not _manifest_valid_with_canonical_relations(manifest, attempt_fence=malformed)
        assert not _manifest_valid_with_canonical_relations(manifest, effect_fence=malformed)

    cancellation = _effect_fence_for_vector("cancellation")
    assert not _effect_fence_record_valid_with_canonical_relations(
        cancellation,
        attempt_fence=attempt_fence,
        author_command=command,
        cancellation_target={},
        author_effect_fence=author_effect_fence,
    )

    tree = ast.parse(
        Path(__file__).with_name("c2a_contract_support.py").read_text(
            encoding="utf-8"
        )
    )
    targets = {
        "_effect_fence_record_valid",
        "_redelivery_valid",
        "_delivery_record_valid",
        "_observation_valid",
        "_manifest_valid",
        "_unknown_outcome_redelivery_allowed",
    }
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in targets
    }
    assert set(functions) == targets
    default_factories = {"_full_record", "_effect_fence_for_vector"}
    for name, function in functions.items():
        for node in ast.walk(function):
            if not isinstance(node, ast.BoolOp) or not isinstance(node.op, ast.Or):
                continue
            calls = {
                nested.func.id
                for value in node.values
                for nested in ast.walk(value)
                if isinstance(nested, ast.Call) and isinstance(nested.func, ast.Name)
            }
            assert not calls & default_factories, name


@pytest.mark.parametrize(
    "name,manifest",
    (
        ("absolute path", _manifest_with_entry_mutation("path", "/PLANS.md")),
        ("traversal", _manifest_with_entry_mutation("path", "../PLANS.md")),
        ("URI", _manifest_with_entry_mutation("path", "file:PLANS.md")),
        ("backslash", _manifest_with_entry_mutation("path", "dir\\PLANS.md")),
        ("NUL", _manifest_with_entry_mutation("path", "PLANS.md\x00")),
        ("add", _manifest_with_entry_mutation("operation", "add")),
        ("delete", _manifest_with_entry_mutation("operation", "delete")),
        ("rename", _manifest_with_entry_mutation("operation", "rename")),
        ("symlink", _manifest_with_entry_mutation("operation", "symlink")),
        ("submodule", _manifest_with_entry_mutation("operation", "submodule")),
        ("special type", _manifest_with_entry_mutation("operation", "fifo")),
        ("unsupported mode", _manifest_with_entry_mutation("mode", "100600")),
        ("blob digest", _manifest_with_entry_mutation("after_blob_sha256", "x" * 64)),
        ("blob length", _manifest_with_entry_mutation("after_byte_length", True)),
    ),
)
def test_capsule_entry_mutations_fail_closed(name: str, manifest: dict[str, object]) -> None:
    assert _manifest_valid_with_canonical_relations(_full_record("CandidateCapsuleManifestV1"))
    assert not _manifest_valid_with_canonical_relations(manifest), name


def test_capsule_path_set_collisions_and_fourth_path_fail_closed() -> None:
    manifest = _full_record("CandidateCapsuleManifestV1")
    assert _manifest_valid_with_canonical_relations(manifest)
    cases: dict[str, list[str]] = {
        "duplicate": ["PLANS.md", "PLANS.md"],
        "case equivalent": ["PLANS.md", "plans.md"],
        "normalization equivalent": ["caf\u00e9.md", "cafe\u0301.md"],
        "fourth ES path": list(AUTHORIZED_PATHS) + ["fourth.md"],
    }
    for name, paths in cases.items():
        assert not _path_set_valid(sorted(paths), exact_first_slice=name == "fourth ES path"), name

    duplicate_manifest = deepcopy(manifest)
    duplicate_manifest["entries"].append(deepcopy(duplicate_manifest["entries"][0]))
    assert not _manifest_valid_with_canonical_relations(duplicate_manifest)
    case_manifest = deepcopy(manifest)
    case_manifest["entries"][1]["path"] = "plans.md"
    assert not _manifest_valid_with_canonical_relations(case_manifest)
    fourth_manifest = deepcopy(manifest)
    extra = deepcopy(fourth_manifest["entries"][-1])
    extra["path"] = "fourth.md"
    fourth_manifest["entries"].append(extra)
    fourth_manifest["entries"].sort(key=lambda entry: entry["path"])
    assert not _manifest_valid_with_canonical_relations(fourth_manifest)


def test_synthetic_blob_fixture_independently_reconstructs_manifest_and_dependents() -> None:
    assert tuple(BLOB_FIXTURES) == AUTHORIZED_PATHS
    assert tuple(BLOB_EXPECTATIONS) == AUTHORIZED_PATHS
    for path in AUTHORIZED_PATHS:
        fixture = BLOB_FIXTURES[path]
        before_length, before_digest, after_length, after_digest = BLOB_EXPECTATIONS[path]
        assert fixture["before"].endswith(b"\n") and fixture["after"].endswith(b"\n")
        fixture["before"].decode("utf-8", errors="strict")
        fixture["after"].decode("utf-8", errors="strict")
        assert (len(fixture["before"]), hashlib.sha256(fixture["before"]).hexdigest()) == (before_length, before_digest)
        assert (len(fixture["after"]), hashlib.sha256(fixture["after"]).hexdigest()) == (after_length, after_digest)

    manifest = _full_record("CandidateCapsuleManifestV1")
    assert _authorized_path_scope_digest(AUTHORIZED_PATHS) == "881d8190e95accffbce9d463a68910703595e5106ce81ba00a8433404b6c8116"
    assert _manifest_valid_with_canonical_relations(manifest)
    assert manifest["portable_capsule_digest"] == "b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c"
    assert _canonical({field: value for field, value in manifest.items() if field != "portable_capsule_digest"}) == GOLDEN_BYTES["CandidateCapsuleManifestV1"]
    assert _full_record("WorkerObservationV1")["portable_capsule_digest"] == manifest["portable_capsule_digest"]
    assert _effect_fence_for_vector("validation")["portable_capsule_digest"] == manifest["portable_capsule_digest"]
    assert _effect_fence_for_vector("review")["portable_capsule_digest"] == manifest["portable_capsule_digest"]


def _alternate_capsule_observation_graph() -> tuple[object, ...]:
    blobs = {
        path: {
            "before": f"Synthetic alternate before {index}.\n".encode("utf-8"),
            "after": f"Synthetic alternate after {index}.\n".encode("utf-8"),
        }
        for index, path in enumerate(AUTHORIZED_PATHS, start=1)
    }
    manifest = deepcopy(_full_record("CandidateCapsuleManifestV1"))
    entries_by_path = {entry["path"]: entry for entry in manifest["entries"]}
    for path, phases in blobs.items():
        entry = entries_by_path[path]
        for phase, raw in phases.items():
            entry[f"{phase}_byte_length"] = len(raw)
            entry[f"{phase}_blob_sha256"] = hashlib.sha256(raw).hexdigest()
    manifest = _reseal_manifest(manifest)

    author_observation = deepcopy(_full_record("WorkerObservationV1"))
    author_observation["portable_capsule_digest"] = manifest[
        "portable_capsule_digest"
    ]
    author_observation = _reseal_observation(author_observation)

    observation = _observation_for_vector("validation")
    effect_fence = _effect_fence_for_vector("validation")
    effect_fence["portable_capsule_digest"] = manifest[
        "portable_capsule_digest"
    ]
    effect_fence = _reseal_single_digest_record("EffectFenceV1", effect_fence)
    delivery = _delivery_for_vector("validation")
    delivery["effect_fence_digest"] = effect_fence["effect_fence_digest"]
    delivery = _reseal_single_digest_record("DeliveryEnvelopeV1", delivery)
    observation["effect_fence_digest"] = effect_fence["effect_fence_digest"]
    observation["portable_capsule_digest"] = manifest[
        "portable_capsule_digest"
    ]
    observation = _reseal_observation(observation)
    return (
        observation,
        effect_fence,
        delivery,
        manifest,
        blobs,
        author_observation,
        _full_record("AttemptFenceV1"),
        _full_record("WorkerCommandV1"),
        _effect_fence_for_vector("author"),
    )


def test_observation_capsule_relation_accepts_actual_alternate_blob_graph() -> None:
    (
        observation,
        effect_fence,
        delivery,
        manifest,
        blobs,
        author_observation,
        attempt,
        command,
        author_effect_fence,
    ) = _alternate_capsule_observation_graph()
    assert _observation_relation(
        observation,
        effect_fence,
        delivery,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author_effect_fence,
        capsule_manifest=manifest,
        capsule_blobs=blobs,
        author_observation=author_observation,
    )


def test_observation_capsule_relation_rejects_missing_or_mismatched_blob_graph() -> None:
    (
        observation,
        effect_fence,
        delivery,
        manifest,
        blobs,
        author_observation,
        attempt,
        command,
        author_effect_fence,
    ) = _alternate_capsule_observation_graph()
    relation = dict(
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author_effect_fence,
        capsule_manifest=manifest,
        author_observation=author_observation,
    )
    assert not _observation_relation(
        observation, effect_fence, delivery, **relation
    )
    assert not _observation_relation(
        observation,
        effect_fence,
        delivery,
        capsule_blobs=BLOB_FIXTURES,
        **relation,
    )
    mismatched = deepcopy(blobs)
    mismatched[AUTHORIZED_PATHS[0]]["after"] = (
        b"Synthetic alternate mismatched after bytes.\n"
    )
    assert not _observation_relation(
        observation,
        effect_fence,
        delivery,
        capsule_blobs=mismatched,
        **relation,
    )
    malformed = deepcopy(blobs)
    malformed.pop(AUTHORIZED_PATHS[-1])
    assert not _observation_relation(
        observation,
        effect_fence,
        delivery,
        capsule_blobs=malformed,
        **relation,
    )


def test_observation_capsule_core_rejects_omitted_none_empty_and_subclass_blob_maps() -> None:
    (
        observation,
        effect_fence,
        delivery,
        manifest,
        blobs,
        author_observation,
        attempt,
        command,
        author_effect_fence,
    ) = _alternate_capsule_observation_graph()
    relation = dict(
        effect_fence=effect_fence,
        delivery=delivery,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author_effect_fence,
        capsule_manifest=manifest,
        author_observation=author_observation,
    )
    assert not _observation_valid(observation, **relation)
    for explicit in (
        None,
        {},
        _RelatedRecordDictSubclass(blobs),
    ):
        assert not _observation_valid(
            observation, capsule_blobs=explicit, **relation
        )


def test_noncapsule_observation_rejects_explicit_blob_graph() -> None:
    explicit_blob_values = (
        None,
        {},
        BLOB_FIXTURES,
        _RelatedRecordDictSubclass(BLOB_FIXTURES),
        _RelatedRecordMappingLike(),
        [],
        "blob-map",
        1,
        True,
    )
    for kind, spec in OBSERVATION_SPEC.items():
        if spec[2] == "capsule":
            continue
        observation, effect_fence, delivery = _observation_for_kind(kind)
        assert _observation_valid_with_canonical_relations(
            observation,
            effect_fence=effect_fence,
            delivery=delivery,
        ), kind
        for explicit in explicit_blob_values:
            assert not _observation_valid_with_canonical_relations(
                observation,
                effect_fence=effect_fence,
                delivery=delivery,
                capsule_blobs=explicit,
            ), (kind, explicit)


@pytest.mark.parametrize("phase", ("before", "after"))
@pytest.mark.parametrize("mutation", ("content", "digest", "length"))
def test_blob_content_digest_and_length_mutations_fail_closed(phase: str, mutation: str) -> None:
    manifest = _full_record("CandidateCapsuleManifestV1")
    blobs = deepcopy(BLOB_FIXTURES)
    if mutation == "content":
        blobs[AUTHORIZED_PATHS[0]][phase] += b"synthetic changed byte\n"
    elif mutation == "digest":
        manifest["entries"][0][f"{phase}_blob_sha256"] = "0" * 64
        manifest = _reseal_manifest(manifest)
    else:
        manifest["entries"][0][f"{phase}_byte_length"] += 1
        manifest = _reseal_manifest(manifest)
    assert not _manifest_valid_with_canonical_relations(manifest, blobs=blobs)


@pytest.mark.parametrize(
    "field,wrong",
    (
        ("schema_id", "governed-execution.nwp-candidate-capsule-manifest.v2"),
        ("canonicalization_profile", "canonical-json.sorted-keys.utf8.v2"),
        ("digest_domain", "governed-execution.nwp-candidate-capsule-manifest.v2.identity"),
        ("program_ref", "program.other"),
        ("program_version_ref", "program-version.other"),
        ("accepted_intent_revision_ref", "intent-revision.other"),
        ("work_item_ref", "work-item.other"),
        ("work_item_revision_ref", "work-revision.other"),
        ("semantic_attempt_ref", "semantic-attempt.other"),
        ("effect_intent_ref", "effect-intent.other"),
        ("command_ref", "worker-command.other"),
        ("command_digest", "0" * 64),
        ("candidate_ref", "candidate.other"),
        ("attempt_fence_ref", "attempt-fence.other"),
        ("attempt_fence_digest", "1" * 64),
        ("effect_fence_ref", "effect-fence.other"),
        ("effect_fence_digest", "2" * 64),
        ("repository_ref", "repository.other"),
        ("base_git_object_format", "sha256"),
        ("base_git_oid", "0" * 40),
        ("authorized_path_scope_digest", "3" * 64),
        ("capsule_manifest_ref", "capsule-manifest.other"),
    ),
)
def test_valid_format_wrong_manifest_cross_record_bindings_fail(field: str, wrong: object) -> None:
    manifest = _full_record("CandidateCapsuleManifestV1")
    manifest[field] = wrong
    assert not _manifest_valid_with_canonical_relations(_reseal_manifest(manifest)), field


def test_manifest_root_constants_and_false_coherent_graph_fail_closed() -> None:
    manifest = _full_record("CandidateCapsuleManifestV1")
    assert manifest["schema_id"] == MANIFEST_SCHEMA_ID
    assert manifest["canonicalization_profile"] == MANIFEST_CANONICALIZATION_PROFILE
    assert manifest["digest_domain"] == MANIFEST_DIGEST_DOMAIN
    assert _manifest_valid_with_canonical_relations(manifest)

    wrong_portable = deepcopy(manifest)
    wrong_portable["portable_capsule_digest"] = "5" * 64
    assert not _manifest_valid_with_canonical_relations(wrong_portable)

    false_attempt_digest = "6" * 64
    command = _full_record("WorkerCommandV1")
    command["attempt_fence_digest"] = false_attempt_digest
    command_identity = {
        field: value
        for field, value in command.items()
        if field not in {"effect_fence_digest", "command_digest"}
    }
    command["command_digest"] = _digest(GOLDEN_META["WorkerCommandV1"][1], _canonical(command_identity))

    author_effect = _effect_fence_for_vector("author")
    author_effect["attempt_fence_digest"] = false_attempt_digest
    author_effect["command_digest"] = command["command_digest"]
    author_effect = _reseal_single_digest_record("EffectFenceV1", author_effect)
    command["effect_fence_digest"] = author_effect["effect_fence_digest"]

    false_manifest = deepcopy(manifest)
    false_manifest["attempt_fence_digest"] = false_attempt_digest
    false_manifest["command_digest"] = command["command_digest"]
    false_manifest["effect_fence_digest"] = author_effect["effect_fence_digest"]
    false_manifest = _reseal_manifest(false_manifest)

    observation = _full_record("WorkerObservationV1")
    observation["attempt_fence_digest"] = false_attempt_digest
    observation["command_digest"] = command["command_digest"]
    observation["effect_fence_digest"] = author_effect["effect_fence_digest"]
    observation["portable_capsule_digest"] = false_manifest["portable_capsule_digest"]
    observation = _reseal_observation(observation)
    assert not _manifest_valid_with_canonical_relations(
        false_manifest,
        command=command,
        attempt_fence=_full_record("AttemptFenceV1"),
        effect_fence=author_effect,
        observation=observation,
    )


@pytest.mark.parametrize("field,wrong", (("capsule_manifest_ref", "capsule-manifest.other"), ("portable_capsule_digest", "4" * 64)))
def test_valid_format_wrong_observation_capsule_bindings_fail(field: str, wrong: object) -> None:
    observation = _full_record("WorkerObservationV1")
    observation[field] = wrong
    observation = _reseal_observation(observation)
    assert not _manifest_valid_with_canonical_relations(_full_record("CandidateCapsuleManifestV1"), observation=observation)


def test_safe_reference_retrieval_non_authority_is_owner_local() -> None:
    assert _retrieval_contract_valid(DOC)
    for rule in RETRIEVAL_NON_AUTHORITY_RULES:
        line = f"- {rule}\n"
        assert DOC.count(line) == 1
        assert not _retrieval_contract_valid(DOC.replace(line, "", 1)), (rule, "removed")
        inversion = line.replace(" is not ", " is ")
        assert not _retrieval_contract_valid(DOC.replace(line, inversion, 1)), (rule, "inverted")
        moved = DOC.replace(line, "", 1) + "\n" + line
        assert not _retrieval_contract_valid(moved), (rule, "moved")
    clause_heading = f"## {CLAUSES[7][0]} — {CLAUSES[7][1]}"
    for inversion in RETRIEVAL_INVERSIONS:
        changed = DOC.replace(clause_heading, clause_heading + "\n\n" + inversion, 1)
        assert not _retrieval_contract_valid(changed), inversion


def test_exact_retrieval_authority_affirmative_contradictions_reject() -> None:
    clause_heading = f"## {CLAUSES[7][0]} — {CLAUSES[7][1]}"
    affirmatives = (
        "`capsule_manifest_ref` is retrieval authority.",
        "`portable_capsule_digest` is retrieval authority.",
        "Safe-reference possession is retrieval authority.",
        "Digest possession is authorization.",
    )
    assert set(affirmatives) <= set(RETRIEVAL_INVERSIONS)
    for contradiction in affirmatives:
        changed = DOC.replace(
            clause_heading, clause_heading + "\n\n" + contradiction, 1
        )
        assert not _retrieval_contract_valid(changed), contradiction


def test_related_record_arguments_distinguish_omitted_from_explicit_values() -> None:
    attempt = _full_record("AttemptFenceV1")
    command = _full_record("WorkerCommandV1")
    author = _effect_fence_for_vector("author")
    cancellation = _effect_fence_for_vector("cancellation")
    delivery = _delivery_for_vector("cancellation")
    later = _valid_redelivery_candidate(delivery)
    observation = _observation_for_vector("cancellation")

    assert not _effect_fence_record_valid(
        cancellation,
        attempt_fence=attempt,
        author_command=command,
    )
    assert _effect_fence_record_valid_with_canonical_relations(
        cancellation,
        attempt_fence=attempt,
        author_command=command,
    )
    assert not _delivery_record_valid(delivery, effect_fence=cancellation)
    assert _delivery_record_valid_with_canonical_relations(
        delivery, effect_fence=cancellation
    )
    assert not _redelivery_valid(
        delivery,
        later,
        original_effect_fence=cancellation,
        candidate_effect_fence=cancellation,
    )
    assert _redelivery_valid_with_canonical_relations(
        delivery,
        later,
        original_effect_fence=cancellation,
        candidate_effect_fence=cancellation,
    )
    assert not _redelivery_valid(
        delivery,
        later,
        original_effect_fence=cancellation,
        candidate_effect_fence=cancellation,
        attempt_fence=attempt,
        author_command=command,
        author_effect_fence=author,
        original_cancellation_target=None,
        later_cancellation_target=author,
    )
    assert not _redelivery_valid(
        delivery,
        later,
        original_effect_fence=cancellation,
        candidate_effect_fence=cancellation,
        attempt_fence=attempt,
        author_command=command,
        author_effect_fence=author,
        original_cancellation_target=author,
        later_cancellation_target=None,
    )
    assert not _observation_valid(
        observation,
        effect_fence=cancellation,
        delivery=delivery,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author,
    )
    assert _observation_valid_with_canonical_relations(
        observation,
        effect_fence=cancellation,
        delivery=delivery,
        author_command=command,
    )
    assert not _observation_relation(
        observation,
        cancellation,
        delivery,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author,
    )
    assert _observation_relation_with_canonical_relations(
        observation, cancellation, delivery
    )

    assert _effect_fence_record_valid(
        author,
        attempt_fence=attempt,
        author_command=command,
        author_effect_fence=author,
    )
    for explicit in (None, {}, author):
        assert not _effect_fence_record_valid(
            author,
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=author,
            cancellation_target=explicit,
        )
        assert not _delivery_record_valid(
            _delivery_for_vector("author"),
            effect_fence=author,
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=author,
            cancellation_target=explicit,
        )


def test_malformed_related_records_reject_without_uncontrolled_exceptions() -> None:
    attempt = _full_record("AttemptFenceV1")
    command = _full_record("WorkerCommandV1")
    author = _effect_fence_for_vector("author")
    cancellation = _effect_fence_for_vector("cancellation")
    delivery = _delivery_for_vector("cancellation")
    later = _valid_redelivery_candidate(delivery)
    observation = _observation_for_vector("cancellation")
    relation = _unknown_outcome_relation_fixture("cancellation")
    malformed_values = (
        None,
        {},
        [],
        "",
        0,
        False,
        _RelatedRecordDictSubclass(author),
        _RelatedRecordMappingLike(),
    )

    for malformed in malformed_values:
        assert not _effect_fence_record_valid_with_canonical_relations(
            cancellation,
            attempt_fence=attempt,
            author_command=command,
            cancellation_target=malformed,
        )
        assert not _delivery_record_valid_with_canonical_relations(
            delivery,
            effect_fence=cancellation,
            cancellation_target=malformed,
        )
        assert not _redelivery_valid_with_canonical_relations(
            delivery,
            later,
            original_effect_fence=cancellation,
            candidate_effect_fence=cancellation,
            cancellation_target=malformed,
        )
        assert not _observation_valid_with_canonical_relations(
            observation,
            effect_fence=cancellation,
            delivery=delivery,
            author_command=command,
            cancellation_target=malformed,
        )
        assert not _observation_relation_with_canonical_relations(
            observation,
            cancellation,
            delivery,
            cancellation_target=malformed,
        )
        changed = deepcopy(relation)
        changed["cancellation_target"] = malformed
        assert not _unknown_outcome_redelivery_allowed(**changed)


def test_core_relation_validators_require_actual_records() -> None:
    attempt = _full_record("AttemptFenceV1")
    command = _full_record("WorkerCommandV1")
    author = _effect_fence_for_vector("author")
    delivery = _delivery_for_vector("author")
    redelivery = _valid_redelivery_candidate(delivery)
    observation, _, observation_delivery = _observation_for_kind(
        "worker_started"
    )
    manifest = _full_record("CandidateCapsuleManifestV1")
    author_observation = _full_record("WorkerObservationV1")

    assert not _effect_fence_record_valid(
        author,
        attempt_fence=attempt,
        author_command=command,
    )
    assert _effect_fence_record_valid_with_canonical_relations(
        author,
        attempt_fence=attempt,
        author_command=command,
    )
    assert not _delivery_record_valid(
        delivery,
        attempt_fence=attempt,
        author_command=command,
        author_effect_fence=author,
    )
    assert _delivery_record_valid_with_canonical_relations(delivery)
    with pytest.raises(TypeError):
        _redelivery_valid(
            delivery,
            redelivery,
            attempt_fence=attempt,
            author_command=command,
            author_effect_fence=author,
        )
    assert _redelivery_valid_with_canonical_relations(delivery, redelivery)
    assert not _observation_valid(
        observation,
        effect_fence=author,
        delivery=observation_delivery,
        author_command=command,
        author_effect_fence=author,
    )
    assert _observation_valid_with_canonical_relations(
        observation,
        effect_fence=author,
        delivery=observation_delivery,
        author_command=command,
    )
    assert not _manifest_valid(
        manifest,
        blobs=BLOB_FIXTURES,
        attempt_fence=attempt,
        effect_fence=author,
        observation=author_observation,
    )
    assert not _manifest_valid(
        manifest,
        blobs=BLOB_FIXTURES,
        command=command,
        attempt_fence=attempt,
        effect_fence=author,
        observation=None,
    )
    assert _manifest_valid_with_canonical_relations(manifest)
    assert not _observation_relation(
        observation,
        author,
        observation_delivery,
        attempt_fence=attempt,
        author_effect_fence=author,
    )
    assert _observation_relation_with_canonical_relations(
        observation, author, observation_delivery
    )

    core_names = {
        "_redelivery_valid",
        "_effect_fence_record_valid",
        "_delivery_record_valid",
        "_observation_valid",
        "_manifest_valid",
        "_observation_relation",
    }
    tree = ast.parse(
        Path(__file__).with_name("c2a_contract_support.py").read_text(
            encoding="utf-8"
        )
    )
    cores = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in core_names
    }
    assert set(cores) == core_names
    for name, function in cores.items():
        calls = {
            node.func.id
            for node in ast.walk(function)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert not {"_full_record", "_effect_fence_for_vector"} & calls, name
        if name in {"_observation_valid", "_observation_relation"}:
            names = {
                node.id for node in ast.walk(function) if isinstance(node, ast.Name)
            }
            assert not {
                "BLOB_FIXTURES",
                "_full_record",
                "_effect_fence_for_vector",
            } & names, name


def test_related_record_exact_types_reject_boundedly() -> None:
    attempt = _full_record("AttemptFenceV1")
    command = _full_record("WorkerCommandV1")
    author = _effect_fence_for_vector("author")
    observation, _, delivery = _observation_for_kind("worker_started")
    manifest = _full_record("CandidateCapsuleManifestV1")
    author_observation = _full_record("WorkerObservationV1")
    malformed_relations = (
        None,
        {},
        [],
        "",
        0,
        False,
        _RelatedRecordDictSubclass(author),
        _RelatedRecordMappingLike(),
    )
    for malformed in malformed_relations:
        assert not _observation_valid(
            observation,
            effect_fence=malformed,
            delivery=delivery,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author,
        )

    malformed_blob_maps = (
        None,
        0,
        False,
        _RelatedRecordMappingLike(),
        _RelatedRecordDictSubclass(BLOB_FIXTURES),
    )
    for malformed in malformed_blob_maps:
        assert not _manifest_valid(
            manifest,
            blobs=malformed,
            command=command,
            attempt_fence=attempt,
            effect_fence=author,
            observation=author_observation,
        )

    subclass_entry = deepcopy(manifest)
    subclass_entry["entries"][0] = _RelatedRecordDictSubclass(
        subclass_entry["entries"][0]
    )
    subclass_entry = _reseal_manifest(subclass_entry)
    assert not _manifest_valid(
        subclass_entry,
        blobs=BLOB_FIXTURES,
        command=command,
        attempt_fence=attempt,
        effect_fence=author,
        observation=author_observation,
    )
    list_subclass_entries = deepcopy(manifest)
    list_subclass_entries["entries"] = _RelatedRecordListSubclass(
        list_subclass_entries["entries"]
    )
    list_subclass_entries = _reseal_manifest(list_subclass_entries)
    assert not _manifest_valid(
        list_subclass_entries,
        blobs=BLOB_FIXTURES,
        command=command,
        attempt_fence=attempt,
        effect_fence=author,
        observation=author_observation,
    )

    relation = _unknown_outcome_relation_fixture()
    relation["coordinator_decision"] = _RelatedRecordDictSubclass(
        relation["coordinator_decision"]
    )
    assert not _unknown_outcome_redelivery_allowed(**relation)


def test_noncapsule_observations_reject_explicit_manifest_arguments() -> None:
    attempt = _full_record("AttemptFenceV1")
    command = _full_record("WorkerCommandV1")
    author = _effect_fence_for_vector("author")
    observation, _, delivery = _observation_for_kind("worker_started")
    assert _observation_valid(
        observation,
        effect_fence=author,
        delivery=delivery,
        author_command=command,
        attempt_fence=attempt,
        author_effect_fence=author,
    )
    for explicit in (
        None,
        _full_record("CandidateCapsuleManifestV1"),
        [],
        "",
        0,
        False,
        _RelatedRecordDictSubclass(
            _full_record("CandidateCapsuleManifestV1")
        ),
        _RelatedRecordMappingLike(),
    ):
        assert not _observation_valid(
            observation,
            effect_fence=author,
            delivery=delivery,
            author_command=command,
            attempt_fence=attempt,
            author_effect_fence=author,
            capsule_manifest=explicit,
        )
