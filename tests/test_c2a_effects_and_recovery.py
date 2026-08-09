"""Direct effect, reconciliation, privacy, and Git-contract tests for C2A."""

from __future__ import annotations

from copy import deepcopy
import pytest
import re

from c2a_contract_support import (
    ADAPTER_AUTHORED_OBSERVATIONS,
    AUTHORITY_DOC,
    CLAUSES,
    DOC,
    EFFECT_RELATION_ROWS,
    GIT_PROHIBITION_ROWS,
    GIT_REQUIREMENT_ROWS,
    GOLDEN_META,
    INGEST_ROWS,
    OBSERVATION_ROWS,
    OWNER_AUTHOR_ROWS,
    PLACEMENT_ALLOWED,
    PLACEMENT_ROWS,
    REJECTED_MATERIAL_CLASSES,
    RELATION_DIGESTS,
    SOURCE_KINDS,
    _delivery_for_vector,
    _effect_class_permitted,
    _effect_fence_for_vector,
    _effect_fence_record_valid_with_canonical_relations,
    _field_names,
    _full_record,
    _git_contract_valid,
    _ingest_disposition,
    _local_git_effect_fence,
    _observation_for_kind,
    _observation_for_vector,
    _observation_valid_with_canonical_relations,
    _ordered_items,
    _placement_allows,
    _reseal_observation,
    _reseal_single_digest_record,
    _retargeted_cancellation,
    _section,
    _table,
    _unknown_outcome_redelivery_allowed,
    _unknown_outcome_rejection_ingest_disposition,
    _unknown_outcome_relation_fixture,
    _without_fences,
)

def test_source_observation_ingest_and_placement_matrices_are_exact() -> None:
    source_clause = _section(DOC, f"{CLAUSES[5][0]} — {CLAUSES[5][1]}", 2)
    assert tuple(item.strip("`") for item in _ordered_items(source_clause)) == SOURCE_KINDS
    assert _table(DOC, "Source/observation-kind matrix") == OBSERVATION_ROWS
    assert _table(DOC, "Observation fact-owner and authorship matrix") == OWNER_AUTHOR_ROWS
    assert _table(DOC, "Observation current-effect relation matrix") == EFFECT_RELATION_ROWS
    assert _table(DOC, "Ingest-disposition precedence matrix") == INGEST_ROWS
    assert _table(DOC, "Placement matrix") == PLACEMENT_ROWS
    ingest = " ".join(_section(DOC, f"{CLAUSES[6][0]} — {CLAUSES[6][1]}", 2).split())
    for phrase in (
        "Before any disposition is assigned, schema, canonical digest, exact field types, finite enums, source-kind/observation-kind/outcome relation, current-effect relation, and conditional fields must all pass.",
        "A malformed record receives no ingest disposition.",
        "source-owner evidence cannot distinguish late from stale",
        "Local receipt time or an unauthoritative source timestamp cannot decide late versus stale.",
        "No disposition creates semantic acceptance, repair, replan, retry authorization, program completion, or publication.",
    ):
        assert phrase in ingest


def test_fact_owner_observation_author_carrier_and_recorder_roles_match_both_authorities() -> None:
    assert _table(DOC, "Observation fact-owner and authorship matrix") == OWNER_AUTHOR_ROWS
    assert _table(AUTHORITY_DOC, "First-slice observation fact-owner and authorship matrix") == OWNER_AUTHOR_ROWS
    for text in (DOC, AUTHORITY_DOC):
        normalized = " ".join(_without_fences(text).split())
        for role in ("underlying fact owner", "canonical observation author", "adapter/carrier", "Coordinator recorder"):
            assert role in normalized
        for statement in (
            "ES remains the fact owner for ES admission/runtime/lifecycle facts even when",
            "A direct-local adapter does not become the OS-process fact owner merely because it authors an observation",
            "Coordinator does not become the fact owner merely because it records",
            "Carrier identity is route",
        ):
            assert statement in normalized
        assert "`source_kind`" in normalized
        assert "`source_ref`" in normalized
        assert "`evidence_refs`" in normalized


def test_current_effect_and_originating_author_roles_are_normatively_separate() -> None:
    clause = " ".join(_section(DOC, f"{CLAUSES[3][0]} — {CLAUSES[3][1]}", 2).split())
    for phrase in (
        "`WorkerCommandV1` is only the originating candidate-authoring semantic command.",
        "Its sole effect class is `author_candidate`",
        "represents the **current effect delivery**",
        "`author_candidate`, `validate_candidate`, `review_candidate`, or `cancel_effect`",
        "it never carries `local_git_commit`",
        "`command_ref` and digest bind the originating author-candidate command lineage",
        "The v1 field names are unchanged.",
        "A route change between `direct_local_bootstrap` and `execution_substrate` is not redelivery",
    ):
        assert phrase in clause


def test_effect_fence_cancellation_target_fields_and_attempt_ceiling_are_exact() -> None:
    fields = _field_names("EffectFenceV1")
    target_fields = (
        "cancellation_target_effect_intent_ref",
        "cancellation_target_effect_fence_ref",
        "cancellation_target_effect_fence_digest",
    )
    assert len(fields) == 32
    assert len(set(fields) - {"effect_fence_digest"}) == 31
    assert tuple(field for field in fields if field.startswith("cancellation_target_")) == target_fields
    attempt = _full_record("AttemptFenceV1")
    command = _full_record("WorkerCommandV1")
    assert attempt["allowed_effect_classes"] == [
        "author_candidate",
        "cancel_effect",
        "local_git_commit",
        "review_candidate",
        "validate_candidate",
    ]
    effects = {
        "author_candidate": _effect_fence_for_vector("author"),
        "validate_candidate": _effect_fence_for_vector("validation"),
        "review_candidate": _effect_fence_for_vector("review"),
        "cancel_effect": _effect_fence_for_vector("cancellation"),
        "local_git_commit": _local_git_effect_fence(),
    }
    for effect_class, effect in effects.items():
        assert _effect_class_permitted(effect, attempt), effect_class
        assert _effect_fence_record_valid_with_canonical_relations(
            effect,
            attempt_fence=attempt,
            author_command=command,
        ), effect_class
    omitted = deepcopy(attempt)
    omitted["allowed_effect_classes"].remove("cancel_effect")
    omitted = _reseal_single_digest_record("AttemptFenceV1", omitted)
    assert not _effect_class_permitted(effects["cancel_effect"], omitted)


def test_cancellation_target_relations_and_capsule_consuming_control_close() -> None:
    attempt = _full_record("AttemptFenceV1")
    command = _full_record("WorkerCommandV1")
    author = _effect_fence_for_vector("author")
    validation = _effect_fence_for_vector("validation")
    review = _effect_fence_for_vector("review")
    cancel_author = _effect_fence_for_vector("cancellation")
    cancel_validation = _effect_fence_for_vector("cancellation_validation")
    assert _effect_fence_record_valid_with_canonical_relations(
        cancel_author,
        attempt_fence=attempt,
        author_command=command,
        cancellation_target=author,
    )
    assert _effect_fence_record_valid_with_canonical_relations(
        cancel_validation,
        attempt_fence=attempt,
        author_command=command,
        cancellation_target=validation,
    )
    assert cancel_validation["portable_capsule_digest"] == GOLDEN_META["CandidateCapsuleManifestV1"][3]
    assert RELATION_DIGESTS["cancellation_validation"] == (
        cancel_validation["effect_fence_digest"],
        _delivery_for_vector("cancellation_validation")["delivery_envelope_digest"],
        _observation_for_vector("cancellation_validation")["observation_digest"],
    )

    mixed = deepcopy(cancel_validation)
    mixed["cancellation_target_effect_intent_ref"] = review["effect_intent_ref"]
    mixed["cancellation_target_effect_fence_ref"] = review["effect_fence_ref"]
    mixed = _reseal_single_digest_record("EffectFenceV1", mixed)
    assert not _effect_fence_record_valid_with_canonical_relations(mixed, attempt_fence=attempt, author_command=command, cancellation_target=review)

    wrong_digest = deepcopy(cancel_validation)
    wrong_digest["cancellation_target_effect_fence_digest"] = review["effect_fence_digest"]
    wrong_digest = _reseal_single_digest_record("EffectFenceV1", wrong_digest)
    assert not _effect_fence_record_valid_with_canonical_relations(wrong_digest, attempt_fence=attempt, author_command=command, cancellation_target=validation)

    wrong_ref = deepcopy(cancel_validation)
    wrong_ref["cancellation_target_effect_fence_ref"] = review["effect_fence_ref"]
    wrong_ref = _reseal_single_digest_record("EffectFenceV1", wrong_ref)
    assert not _effect_fence_record_valid_with_canonical_relations(wrong_ref, attempt_fence=attempt, author_command=command, cancellation_target=validation)

    self_target = deepcopy(cancel_author)
    self_target["cancellation_target_effect_intent_ref"] = self_target["effect_intent_ref"]
    self_target["cancellation_target_effect_fence_ref"] = self_target["effect_fence_ref"]
    self_target["cancellation_target_effect_fence_digest"] = "b" * 64
    self_target = _reseal_single_digest_record("EffectFenceV1", self_target)
    assert not _effect_fence_record_valid_with_canonical_relations(self_target, attempt_fence=attempt, author_command=command, cancellation_target=self_target)

    for field, wrong in (
        ("semantic_attempt_ref", "semantic-attempt.other"),
        ("program_ref", "program.other"),
        ("work_item_revision_ref", "work-revision.other"),
        ("repository_ref", "repository.other"),
        ("base_git_oid", "0" * 40),
    ):
        target = deepcopy(validation)
        target[field] = wrong
        target = _reseal_single_digest_record("EffectFenceV1", target)
        current = _retargeted_cancellation(cancel_validation, target)
        assert not _effect_fence_record_valid_with_canonical_relations(current, attempt_fence=attempt, author_command=command, cancellation_target=target), field

    unrelated_author_capsule = deepcopy(cancel_author)
    unrelated_author_capsule["portable_capsule_digest"] = "c" * 64
    unrelated_author_capsule = _reseal_single_digest_record("EffectFenceV1", unrelated_author_capsule)
    assert not _effect_fence_record_valid_with_canonical_relations(unrelated_author_capsule, attempt_fence=attempt, author_command=command, cancellation_target=author)

    for capsule in (None, "d" * 64):
        changed = deepcopy(cancel_validation)
        changed["portable_capsule_digest"] = capsule
        changed = _reseal_single_digest_record("EffectFenceV1", changed)
        assert not _effect_fence_record_valid_with_canonical_relations(changed, attempt_fence=attempt, author_command=command, cancellation_target=validation)

    for field in (
        "cancellation_target_effect_intent_ref",
        "cancellation_target_effect_fence_ref",
        "cancellation_target_effect_fence_digest",
    ):
        changed = deepcopy(cancel_author)
        changed[field] = None
        changed = _reseal_single_digest_record("EffectFenceV1", changed)
        assert not _effect_fence_record_valid_with_canonical_relations(changed, attempt_fence=attempt, author_command=command, cancellation_target=author), field

    local_git = _local_git_effect_fence()
    current = _retargeted_cancellation(cancel_validation, local_git)
    current["portable_capsule_digest"] = local_git["portable_capsule_digest"]
    current = _reseal_single_digest_record("EffectFenceV1", current)
    assert not _effect_fence_record_valid_with_canonical_relations(current, attempt_fence=attempt, author_command=command, cancellation_target=local_git)


def test_adapter_authored_route_source_pairing_is_exact() -> None:
    command = _full_record("WorkerCommandV1")
    assert ADAPTER_AUTHORED_OBSERVATIONS == {
        "delivery_acknowledged",
        "delivery_rejected",
        "delivery_outcome_unknown",
        "cancellation_acknowledged",
        "cancellation_rejected",
        "process_exited",
        "deadline_elapsed",
    }
    for kind in sorted(ADAPTER_AUTHORED_OBSERVATIONS):
        direct_record, fence, direct_delivery = _observation_for_kind(kind)
        assert _observation_valid_with_canonical_relations(direct_record, effect_fence=fence, delivery=direct_delivery, author_command=command), kind

        es_delivery = deepcopy(direct_delivery)
        es_delivery["adapter_kind"] = "execution_substrate"
        es_delivery = _reseal_single_digest_record("DeliveryEnvelopeV1", es_delivery)
        assert not _observation_valid_with_canonical_relations(direct_record, effect_fence=fence, delivery=es_delivery, author_command=command), (kind, "direct-source-on-es")

        es_record = deepcopy(direct_record)
        es_record["source_kind"] = "es_adapter"
        es_record["source_ref"] = "source.es-adapter.0001"
        es_record = _reseal_observation(es_record)
        assert _observation_valid_with_canonical_relations(es_record, effect_fence=fence, delivery=es_delivery, author_command=command), kind
        assert not _observation_valid_with_canonical_relations(es_record, effect_fence=fence, delivery=direct_delivery, author_command=command), (kind, "es-source-on-direct")


def test_ingest_duplicate_late_stale_ambiguous_and_unknown_outcomes_are_distinct() -> None:
    cases = {
        "recorded": {},
        "duplicate_exact": {"same_ref": True, "same_digest": True},
        "conflict_quarantined": {"same_ref": True, "same_digest": False},
        "late_retained": {"late": True},
        "stale_retained": {"stale": True},
        "ambiguous_unbound": {"bound": False},
        "ambiguous_contradictory": {"contradictory": True},
        "ambiguous_late_stale": {"late": True, "stale": True},
    }
    expected = {
        "recorded": "recorded",
        "duplicate_exact": "duplicate_exact",
        "conflict_quarantined": "conflict_quarantined",
        "late_retained": "late_retained",
        "stale_retained": "stale_retained",
        "ambiguous_unbound": "ambiguous_quarantined",
        "ambiguous_contradictory": "ambiguous_quarantined",
        "ambiguous_late_stale": "ambiguous_quarantined",
    }
    assert {name: _ingest_disposition(**values) for name, values in cases.items()} == expected
    assert _ingest_disposition(valid=False) is None
    assert _ingest_disposition(same_ref=True, same_digest=True, late=True) == "duplicate_exact"
    assert _ingest_disposition(same_ref=True, same_digest=False, stale=True) == "conflict_quarantined"
    assert not _unknown_outcome_redelivery_allowed(
        outcome_unknown=True, generic_reconciled=True
    )
    complete_relation = _unknown_outcome_relation_fixture()
    assert _unknown_outcome_redelivery_allowed(**complete_relation)
    for field in tuple(complete_relation):
        changed = deepcopy(complete_relation)
        changed[field] = None
        assert not _unknown_outcome_redelivery_allowed(**changed), field


def test_provably_not_accepted_reason_is_delivery_rejection_only_and_exactly_bound() -> None:
    command = _full_record("WorkerCommandV1")
    record, fence, delivery = _observation_for_kind("delivery_rejected")
    record["reason_code"] = "provably_not_accepted"
    record = _reseal_observation(record)
    assert _observation_valid_with_canonical_relations(record, effect_fence=fence, delivery=delivery, author_command=command)

    wrong_kind, wrong_fence, wrong_delivery = _observation_for_kind("delivery_acknowledged")
    wrong_kind["reason_code"] = "provably_not_accepted"
    wrong_kind = _reseal_observation(wrong_kind)
    assert not _observation_valid_with_canonical_relations(wrong_kind, effect_fence=wrong_fence, delivery=wrong_delivery, author_command=command)

    wrong_binding = deepcopy(record)
    wrong_binding["delivery_attempt_ref"] = "delivery-attempt.other.0001"
    wrong_binding = _reseal_observation(wrong_binding)
    assert not _observation_valid_with_canonical_relations(wrong_binding, effect_fence=fence, delivery=delivery, author_command=command)


def test_unknown_outcome_redelivery_requires_complete_five_condition_graph() -> None:
    canonical = _unknown_outcome_relation_fixture()
    assert _unknown_outcome_redelivery_allowed(**canonical)
    assert not _unknown_outcome_redelivery_allowed(
        outcome_unknown=True,
        source_native_rejection_proven=True,
        canonical_observation_authored=True,
        safe_owner_evidence_bound=True,
        route_source_paired=True,
        canonical_observation_kind="delivery_rejected",
        reason_code="provably_not_accepted",
        exact_binding=True,
        coordinator_decision=True,
        valid_authority=True,
        current_global_stop=True,
    )

    for missing in (
        "unknown_observation",
        "rejection_observation",
        "owner_evidence_ref",
        "coordinator_decision",
        "authority_global_stop",
    ):
        changed = deepcopy(canonical)
        changed.pop(missing)
        assert not _unknown_outcome_redelivery_allowed(**changed), missing

    no_owner_proof = deepcopy(canonical)
    no_owner_proof["rejection_observation"]["evidence_refs"] = []
    no_owner_proof["rejection_observation"] = _reseal_observation(
        no_owner_proof["rejection_observation"]
    )
    assert not _unknown_outcome_redelivery_allowed(**no_owner_proof)

    wrong_reason = deepcopy(canonical)
    wrong_reason["rejection_observation"]["reason_code"] = "reason.other"
    wrong_reason["rejection_observation"] = _reseal_observation(
        wrong_reason["rejection_observation"]
    )
    assert not _unknown_outcome_redelivery_allowed(**wrong_reason)

    wrong_evidence = deepcopy(canonical)
    wrong_evidence["rejection_observation"]["evidence_refs"] = [
        "evidence.delivery-owner-rejection.other"
    ]
    wrong_evidence["rejection_observation"] = _reseal_observation(
        wrong_evidence["rejection_observation"]
    )
    assert not _unknown_outcome_redelivery_allowed(**wrong_evidence)

    wrong_route = deepcopy(canonical)
    wrong_route["selected_adapter_route"] = "execution_substrate"
    wrong_route["canonical_observation_author"] = "es_adapter"
    assert not _unknown_outcome_redelivery_allowed(**wrong_route)

    decision_mutations = (
        ("delivery_attempt_ref", "delivery-attempt.other"),
        ("effect_intent_ref", "effect-intent.other"),
        ("effect_fence_ref", "effect-fence.other"),
        ("effect_fence_digest", "8" * 64),
        ("command_ref", "worker-command.other"),
        ("command_digest", "8" * 64),
        ("attempt_fence_ref", "attempt-fence.other"),
        ("attempt_fence_digest", "8" * 64),
        ("program_ref", "program.other"),
        ("program_version_ref", "program-version.other"),
        ("owner_evidence_ref", "evidence.other"),
    )
    for field_name, wrong in decision_mutations:
        changed = deepcopy(canonical)
        changed["coordinator_decision"][field_name] = wrong
        assert not _unknown_outcome_redelivery_allowed(**changed), field_name

    stale = deepcopy(canonical)
    stale["authority_global_stop"]["evaluated_at"] = "2031-01-01T00:00:00Z"
    assert not _unknown_outcome_redelivery_allowed(**stale)
    revoked = deepcopy(canonical)
    revoked["authority_global_stop"]["revocation_status"] = "revoked"
    assert not _unknown_outcome_redelivery_allowed(**revoked)
    non_current_stop = deepcopy(canonical)
    non_current_stop["authority_global_stop"]["current_global_stop_version"] += 1
    assert not _unknown_outcome_redelivery_allowed(**non_current_stop)

    for related_record in (
        "unknown_observation",
        "rejection_observation",
        "delivery",
        "current_effect_fence",
        "attempt_fence",
        "author_command",
        "author_effect_fence",
        "coordinator_decision",
        "authority_global_stop",
    ):
        changed = deepcopy(canonical)
        changed[related_record] = {}
        assert not _unknown_outcome_redelivery_allowed(**changed), related_record


def test_unknown_outcome_contract_says_all_five_conditions() -> None:
    clause = _without_fences(
        _section(DOC, f"{CLAUSES[6][0]} — {CLAUSES[6][1]}", 2)
    )
    assert clause.count("all five\nconditions hold:") == 1
    assert "all four\nconditions hold:" not in clause
    numbered = re.findall(r"^([1-5])\. ", clause, re.MULTILINE)
    assert numbered[-5:] == ["1", "2", "3", "4", "5"]
    required = (
        "a valid original `delivery_outcome_unknown` observation",
        "source-native proof of rejection",
        "a valid exact\n   `delivery_rejected` WorkerObservationV1",
        "Coordinator separately records a closed redelivery decision relation",
        "parent and subordinate authority relation remains valid",
    )
    assert all(statement in clause for statement in required)


def test_closed_privacy_placement_table_cells_match_independent_grammar() -> None:
    assert tuple(PLACEMENT_ALLOWED) == tuple(row[0] for row in PLACEMENT_ROWS)
    for row in PLACEMENT_ROWS:
        location, permitted, prohibited, _ = row
        parsed = frozenset(re.findall(r"`([^`]+)`", permitted))
        assert parsed == PLACEMENT_ALLOWED[location]
        assert prohibited == "every unlisted material class (closed-world)"
    privacy = " ".join(_section(DOC, f"{CLAUSES[12][0]} — {CLAUSES[12][1]}", 2).split())
    for material_class in REJECTED_MATERIAL_CLASSES:
        assert f"`{material_class}`" in privacy


@pytest.mark.parametrize(
    "location,material_class",
    tuple((location, material_class) for location, allowed in PLACEMENT_ALLOWED.items() for material_class in sorted(allowed)),
)
def test_every_permitted_material_class_has_a_positive_control(location: str, material_class: str) -> None:
    assert _placement_allows(location, material_class)


@pytest.mark.parametrize("location", tuple(PLACEMENT_ALLOWED))
@pytest.mark.parametrize("material_class", tuple(sorted(REJECTED_MATERIAL_CLASSES)))
def test_every_sensitive_or_unlisted_material_class_is_rejected_at_every_location(location: str, material_class: str) -> None:
    assert material_class not in PLACEMENT_ALLOWED[location]
    assert not _placement_allows(location, material_class)


@pytest.mark.parametrize("location", tuple(PLACEMENT_ALLOWED))
def test_arbitrary_unlisted_material_class_is_rejected_per_location(location: str) -> None:
    assert not _placement_allows(location, "synthetic_unlisted_material_class")


def test_validation_review_model_decision_and_git_effect_separation_is_explicit() -> None:
    decision = " ".join(_section(DOC, f"{CLAUSES[8][0]} — {CLAUSES[8][1]}", 2).split())
    for statement in (
        "Successful validation does not create acceptance.",
        "`inconclusive` or `not_run` does not satisfy required validation.",
        "A byte-changing repair normally creates a new semantic attempt and candidate.",
        "Replan changes the governing program or work revision",
        "stale proposals cannot advance that revision.",
        "It has no direct requirement-profile, tool-version, raw-tool-output, detailed-count, unrestricted-validation-record, or review-narrative field.",
        "Detailed requirement, tool, profile, count, and private-output material remains behind a bounded safe evidence reference",
        "No raw validation or review output enters Coordinator SQLite or a public report.",
    ):
        assert statement in decision

    fields = set(_field_names("WorkerObservationV1"))
    assert fields.isdisjoint(
        {
            "requirement_profile_ref",
            "tool_version_ref",
            "raw_tool_output",
            "detailed_counts",
            "validation_record",
            "review_narrative",
        }
    )

    git = " ".join(_section(DOC, f"{CLAUSES[9][0]} — {CLAUSES[9][1]}", 2).split())
    for binding in (
        "`git_effect_intent_ref`",
        "accepted Coordinator decision",
        "semantic attempt",
        "candidate",
        "capsule manifest",
        "portable capsule digest",
        "ES repository identity",
        "exact base OID",
        "exact three-path ceiling",
        "designated local feature ref",
        "expected current ref and base",
        "one intended commit content or tree",
    ):
        assert binding in git
    for blocker in (
        "stale base",
        "unexpected ref",
        "unexpected tree",
        "dirty unrelated content",
        "capsule mismatch",
        "candidate mismatch",
        "missing acceptance",
        "missing fence",
        "ambiguous authority",
    ):
        assert blocker in git


@pytest.mark.parametrize("row", GIT_PROHIBITION_ROWS, ids=lambda row: row[1].replace(" ", "-"))
@pytest.mark.parametrize("mutation", ("removed", "inverted", "moved"))
def test_each_git_effect_prohibition_is_independently_owner_local(row: tuple[str, ...], mutation: str) -> None:
    line = "| " + " | ".join(row) + " |\n"
    assert DOC.count(line) == 1
    if mutation == "removed":
        changed = DOC.replace(line, "", 1)
    elif mutation == "inverted":
        changed = DOC.replace(line, line.replace("| prohibited |", "| permitted |"), 1)
    else:
        changed = DOC.replace(line, "", 1) + "\n" + line
    assert _git_contract_valid(DOC)
    assert not _git_contract_valid(changed)


def test_unknown_outcome_reconciliation_and_commit_noncompletion_are_mandatory() -> None:
    for row in GIT_REQUIREMENT_ROWS:
        line = "| " + " | ".join(row) + " |\n"
        assert DOC.count(line) == 1
        assert not _git_contract_valid(DOC.replace(line, "", 1)), row[0]


def test_direct_local_es_process_release_terminal_receipt_and_credentials_remain_gated() -> None:
    conformance = " ".join(_section(DOC, f"{CLAUSES[10][0]} — {CLAUSES[10][1]}", 2).split())
    for phrase in (
        "Only transport wrapping may differ.",
        "No route may translate semantic identities into a route-specific dialect.",
        "ES owns admission, reliable submit, response-loss recovery, runtime lifecycle, cancellation correlation, retained results, and ES-side ambiguity resolution.",
        "Bridge and Bridge Core are not part of conformance.",
        "Bridge Core remains unused.",
    ):
        assert phrase in conformance

    process = " ".join(_section(DOC, f"{CLAUSES[11][0]} — {CLAUSES[11][1]}", 2).split())
    for phrase in (
        "one one-shot subprocess",
        "one semantic command on standard input",
        "one bounded protocol-only result on standard output",
        "no listener, and no daemon",
        "named Unix-domain listener and filesystem mailbox control transport are rejected",
        "not current implementation",
        "Exact framing, executable identity, artifact versioning, packaging, release and rollback, containment, terminal receipt, size limits, exit and error precedence, and credential delivery must be separately frozen",
        "No worker-side component receives Coordinator durable-write authority.",
        "A durable effect intent must precede every external process I/O attempt.",
    ):
        assert phrase in process


def test_unknown_outcome_redelivery_applies_observation_conflict_precedence() -> None:
    canonical = _unknown_outcome_relation_fixture()
    unknown = canonical["unknown_observation"]
    rejection = canonical["rejection_observation"]

    def disposition(relation: dict[str, object]) -> str | None:
        return _unknown_outcome_rejection_ingest_disposition(
            relation["unknown_observation"],
            relation["rejection_observation"],
            owner_evidence_ref=relation["owner_evidence_ref"],
            effect_lifecycle_relation=relation["effect_lifecycle_relation"],
        )

    assert disposition(canonical) == "recorded"
    assert _unknown_outcome_redelivery_allowed(**canonical)

    duplicate = deepcopy(canonical)
    duplicate["rejection_observation"] = deepcopy(unknown)
    assert disposition(duplicate) == "duplicate_exact"
    assert not _unknown_outcome_redelivery_allowed(**duplicate)

    conflict = deepcopy(canonical)
    conflict["rejection_observation"]["observation_ref"] = unknown[
        "observation_ref"
    ]
    conflict["rejection_observation"] = _reseal_observation(
        conflict["rejection_observation"]
    )
    assert disposition(conflict) == "conflict_quarantined"
    assert not _unknown_outcome_redelivery_allowed(**conflict)

    unbound = deepcopy(canonical)
    unbound["rejection_observation"]["delivery_attempt_ref"] = (
        "delivery-attempt.other.0001"
    )
    unbound["rejection_observation"] = _reseal_observation(
        unbound["rejection_observation"]
    )
    assert disposition(unbound) == "ambiguous_quarantined"
    assert not _unknown_outcome_redelivery_allowed(**unbound)

    stale = deepcopy(canonical)
    stale["effect_lifecycle_relation"]["source_owner_relation"] = "stale"
    assert disposition(stale) == "stale_retained"
    assert not _unknown_outcome_redelivery_allowed(**stale)

    late = deepcopy(canonical)
    late["effect_lifecycle_relation"]["source_owner_relation"] = "late"
    assert disposition(late) == "late_retained"
    assert not _unknown_outcome_redelivery_allowed(**late)


def test_unknown_outcome_redelivery_composes_exact_cancellation_target() -> None:
    author = _unknown_outcome_relation_fixture()
    cancel_author = _unknown_outcome_relation_fixture("cancellation")
    cancel_validation = _unknown_outcome_relation_fixture(
        "cancellation_validation"
    )
    assert _unknown_outcome_redelivery_allowed(**author)
    assert _unknown_outcome_redelivery_allowed(**cancel_author)
    assert _unknown_outcome_redelivery_allowed(**cancel_validation)
    assert cancel_author["cancellation_target"] == _effect_fence_for_vector(
        "author"
    )
    assert cancel_validation[
        "cancellation_target"
    ] == _effect_fence_for_vector("validation")
    assert cancel_validation["current_effect_fence"][
        "portable_capsule_digest"
    ] == cancel_validation["cancellation_target"][
        "portable_capsule_digest"
    ]

    missing = deepcopy(cancel_author)
    missing.pop("cancellation_target")
    assert not _unknown_outcome_redelivery_allowed(**missing)
    for malformed in (None, {}, [], "", 0, False):
        changed = deepcopy(cancel_author)
        changed["cancellation_target"] = malformed
        assert not _unknown_outcome_redelivery_allowed(**changed)

    wrong_target = deepcopy(cancel_author)
    wrong_target["cancellation_target"] = _effect_fence_for_vector("review")
    assert not _unknown_outcome_redelivery_allowed(**wrong_target)
    wrong_capsule = deepcopy(cancel_validation)
    target = deepcopy(wrong_capsule["cancellation_target"])
    target["portable_capsule_digest"] = "d" * 64
    wrong_capsule["cancellation_target"] = _reseal_single_digest_record(
        "EffectFenceV1", target
    )
    assert not _unknown_outcome_redelivery_allowed(**wrong_capsule)


def test_unknown_outcome_ingest_classification_precedes_eligibility() -> None:
    class EligibilityMustNotRun:
        def __eq__(self, other: object) -> bool:
            raise AssertionError("later eligibility validation was reached")

        def __ne__(self, other: object) -> bool:
            raise AssertionError("later eligibility validation was reached")

    recorded = _unknown_outcome_relation_fixture()
    assert _ingest_disposition() == "recorded"
    assert (
        _unknown_outcome_rejection_ingest_disposition(
            recorded["unknown_observation"],
            recorded["rejection_observation"],
            owner_evidence_ref=recorded["owner_evidence_ref"],
            effect_lifecycle_relation=recorded["effect_lifecycle_relation"],
        )
        == "recorded"
    )
    assert _unknown_outcome_redelivery_allowed(**recorded)
    recorded_later_eligibility = deepcopy(recorded)
    recorded_later_eligibility["attempt_fence"]["schema_id"] = (
        EligibilityMustNotRun()
    )
    with pytest.raises(
        AssertionError, match="later eligibility validation was reached"
    ):
        _unknown_outcome_redelivery_allowed(**recorded_later_eligibility)

    duplicate = _unknown_outcome_relation_fixture()
    duplicate["rejection_observation"] = deepcopy(
        duplicate["unknown_observation"]
    )
    assert (
        _ingest_disposition(same_ref=True, same_digest=True)
        == "duplicate_exact"
    )
    assert (
        _unknown_outcome_rejection_ingest_disposition(
            duplicate["unknown_observation"],
            duplicate["rejection_observation"],
            owner_evidence_ref=duplicate["owner_evidence_ref"],
            effect_lifecycle_relation=duplicate["effect_lifecycle_relation"],
        )
        == "duplicate_exact"
    )
    assert not _unknown_outcome_redelivery_allowed(**duplicate)
    duplicate_short_circuit = deepcopy(duplicate)
    duplicate_short_circuit["attempt_fence"]["schema_id"] = (
        EligibilityMustNotRun()
    )
    assert not _unknown_outcome_redelivery_allowed(**duplicate_short_circuit)

    conflict = _unknown_outcome_relation_fixture()
    conflict["rejection_observation"]["observation_ref"] = conflict[
        "unknown_observation"
    ]["observation_ref"]
    conflict["rejection_observation"] = _reseal_observation(
        conflict["rejection_observation"]
    )
    assert (
        _ingest_disposition(same_ref=True, same_digest=False)
        == "conflict_quarantined"
    )
    assert (
        _unknown_outcome_rejection_ingest_disposition(
            conflict["unknown_observation"],
            conflict["rejection_observation"],
            owner_evidence_ref=conflict["owner_evidence_ref"],
            effect_lifecycle_relation=conflict["effect_lifecycle_relation"],
        )
        == "conflict_quarantined"
    )
    assert not _unknown_outcome_redelivery_allowed(**conflict)
    conflict_short_circuit = deepcopy(conflict)
    conflict_short_circuit["attempt_fence"]["schema_id"] = (
        EligibilityMustNotRun()
    )
    assert not _unknown_outcome_redelivery_allowed(**conflict_short_circuit)

    ambiguous = _unknown_outcome_relation_fixture()
    ambiguous["rejection_observation"]["delivery_attempt_ref"] = (
        "delivery-attempt.unbound.0001"
    )
    ambiguous["rejection_observation"] = _reseal_observation(
        ambiguous["rejection_observation"]
    )
    assert _ingest_disposition(bound=False) == "ambiguous_quarantined"
    assert (
        _unknown_outcome_rejection_ingest_disposition(
            ambiguous["unknown_observation"],
            ambiguous["rejection_observation"],
            owner_evidence_ref=ambiguous["owner_evidence_ref"],
            effect_lifecycle_relation=ambiguous["effect_lifecycle_relation"],
        )
        == "ambiguous_quarantined"
    )
    assert not _unknown_outcome_redelivery_allowed(**ambiguous)
    ambiguous_short_circuit = deepcopy(ambiguous)
    ambiguous_short_circuit["attempt_fence"]["schema_id"] = (
        EligibilityMustNotRun()
    )
    assert not _unknown_outcome_redelivery_allowed(**ambiguous_short_circuit)

    stale = _unknown_outcome_relation_fixture()
    stale["effect_lifecycle_relation"]["source_owner_relation"] = "stale"
    assert _ingest_disposition(stale=True) == "stale_retained"
    assert (
        _unknown_outcome_rejection_ingest_disposition(
            stale["unknown_observation"],
            stale["rejection_observation"],
            owner_evidence_ref=stale["owner_evidence_ref"],
            effect_lifecycle_relation=stale["effect_lifecycle_relation"],
        )
        == "stale_retained"
    )
    assert not _unknown_outcome_redelivery_allowed(**stale)
    stale_short_circuit = deepcopy(stale)
    stale_short_circuit["attempt_fence"]["schema_id"] = EligibilityMustNotRun()
    assert not _unknown_outcome_redelivery_allowed(**stale_short_circuit)

    late = _unknown_outcome_relation_fixture()
    late["effect_lifecycle_relation"]["source_owner_relation"] = "late"
    assert _ingest_disposition(late=True) == "late_retained"
    assert (
        _unknown_outcome_rejection_ingest_disposition(
            late["unknown_observation"],
            late["rejection_observation"],
            owner_evidence_ref=late["owner_evidence_ref"],
            effect_lifecycle_relation=late["effect_lifecycle_relation"],
        )
        == "late_retained"
    )
    assert not _unknown_outcome_redelivery_allowed(**late)
    late_short_circuit = deepcopy(late)
    late_short_circuit["attempt_fence"]["schema_id"] = EligibilityMustNotRun()
    assert not _unknown_outcome_redelivery_allowed(**late_short_circuit)

    route_mismatch = _unknown_outcome_relation_fixture()
    route_mismatch["selected_adapter_route"] = "execution_substrate"
    route_mismatch["canonical_observation_author"] = "es_adapter"
    assert _ingest_disposition() == "recorded"
    assert (
        _unknown_outcome_rejection_ingest_disposition(
            route_mismatch["unknown_observation"],
            route_mismatch["rejection_observation"],
            owner_evidence_ref=route_mismatch["owner_evidence_ref"],
            effect_lifecycle_relation=route_mismatch[
                "effect_lifecycle_relation"
            ],
        )
        == "recorded"
    )
    assert not _unknown_outcome_redelivery_allowed(**route_mismatch)

    current_effect_mismatch = _unknown_outcome_relation_fixture()
    current_effect_mismatch["current_effect_fence"] = _effect_fence_for_vector(
        "validation"
    )
    assert _ingest_disposition() == "recorded"
    assert (
        _unknown_outcome_rejection_ingest_disposition(
            current_effect_mismatch["unknown_observation"],
            current_effect_mismatch["rejection_observation"],
            owner_evidence_ref=current_effect_mismatch["owner_evidence_ref"],
            effect_lifecycle_relation=current_effect_mismatch[
                "effect_lifecycle_relation"
            ],
        )
        == "recorded"
    )
    assert not _unknown_outcome_redelivery_allowed(**current_effect_mismatch)
