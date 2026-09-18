"""Direct constructor, immutability, privacy and finite-budget contracts."""

from __future__ import annotations

from copy import deepcopy
import pickle
import ast
import inspect

import pytest

import ge_nwp_coordinator._rw0_phase_entry_semantic_values as b1
from test_rw0_b1_vectors import SCHEMAS, mapping_for, _digest


EFFECT_CLASSES = (
    "author_candidate", "cancel_effect", "local_git_commit",
    "review_candidate", "validate_candidate",
)
BLOCKING_REASONS = (
    "readiness_unready", "readiness_unknown", "readiness_expired",
    "authority_not_verified", "authority_denied_or_revoked",
    "authority_expired", "phase_or_effect_mismatch",
    "worker_artifact_mismatch", "worker_protocol_mismatch",
    "platform_or_architecture_mismatch", "profile_mismatch",
    "global_stop_active",
)


def test_retrieval_budget_literal_matches_complete_occurrence_formula() -> None:
    expected = 87 + 17 + 62 + 46 + 3 * 38 + 1 + 2 + 1 + 8 + 30 + 6
    assert expected == 374
    function = ast.parse(inspect.getsource(b1.validate_retrieval_event_sequence)).body[0]
    limits = [node.args[0].value for node in ast.walk(function)
              if isinstance(node, ast.Call)
              and isinstance(node.func, ast.Name)
              and node.func.id == "_WorkBudget"
              and len(node.args) == 1 and isinstance(node.args[0], ast.Constant)]
    assert limits == [374]


def reseal(cls: type, mapping: dict[str, object]) -> dict[str, object]:
    mapping[cls._FIELDS[-1]] = _digest(
        cls._SCHEMA + ".identity",
        {key: value for key, value in mapping.items() if key != cls._FIELDS[-1]},
    )
    return mapping


def reason(cls: type, mapping: dict[str, object]) -> str:
    with pytest.raises(b1.RW0PhaseValueError) as caught:
        cls.from_mapping(mapping)
    assert caught.value.__cause__ is None
    assert str(caught.value) == f"{caught.value.reason}:{caught.value.field_path}"
    return caught.value.reason


def test_eight_private_values_are_present() -> None:
    assert tuple(cls for cls, _, _, _ in SCHEMAS) == b1._B1_CLASSES
    assert b1.__all__ == ()
    assert set(b1._ERROR_REASONS) == {
        "invalid_field_type", "missing_field", "unknown_field", "duplicate_field",
        "invalid_enum", "malformed_ref", "malformed_digest",
        "invalid_timestamp_window", "invalid_length_or_cardinality", "graph_cycle",
        "cumulative_work_exhausted", "relation_mismatch",
        "observation_stale_or_expired", "authority_denied_or_revoked",
        "per_fence_basis_mismatch", "common_family_unverified",
        "scope_or_ceiling_mismatch", "path_scope_binding_mismatch",
        "current_head_or_global_stop_mismatch", "custody_subject_mismatch",
        "retrieval_transition_invalid", "readiness_profile_mismatch",
        "qualification_reason_mismatch", "terminal_branch_mismatch",
        "privacy_forbidden_material",
    }


@pytest.mark.parametrize("cls,schema,count,limit", SCHEMAS)
def test_closed_type_and_digest_failures(cls: type, schema: str, count: int, limit: int) -> None:
    original = mapping_for(cls)
    assert reason(cls, {**original, "unknown": "anything", cls._FIELDS[1]: None}) == "unknown_field"
    missing = dict(original)
    missing.pop(cls._FIELDS[1])
    assert reason(cls, missing) == "missing_field"
    assert reason(cls, {**original, "schema_id": "other"}) == "invalid_enum"
    assert reason(cls, {**original, cls._FIELDS[-1]: "0" * 64}) == "relation_mismatch"
    assert reason(cls, {**original, cls._FIELDS[-1]: "A" * 64}) == "malformed_digest"
    assert reason(cls, {**original, cls._FIELDS[1]: "user-private"}) == "malformed_ref"
    private_key = dict(original)
    private_key.pop(cls._FIELDS[1])
    private_key["bearer_token"] = "secret"
    assert reason(cls, private_key) == "privacy_forbidden_material"
    assert reason(cls, []) == "invalid_field_type"
    assert reason(cls, dict(original, **{cls._FIELDS[1]: b"private"})) == "privacy_forbidden_material"


@pytest.mark.parametrize("cls,schema,count,limit", SCHEMAS)
def test_immutable_slots_and_pickle(cls: type, schema: str, count: int, limit: int) -> None:
    payload = mapping_for(cls)
    value = cls.from_mapping(payload)
    assert not hasattr(value, "__dict__")
    with pytest.raises(AttributeError):
        value._values = ()
    with pytest.raises(TypeError):
        pickle.dumps(value)
    with pytest.raises(TypeError):
        type("Evil", (cls,), {})
    with pytest.raises(TypeError):
        b1.RW0PhaseValueError(object(), "relation_mismatch", "private")
    saved = value.to_mapping()
    if cls is b1.RW0PhaseEntryBasisV1:
        payload["c2b3d_lineage"]["program_ref"] = "altered"
        payload["selection_key"][0][1] = "altered"
    if cls in (b1.RW0AuthorityVerificationObservationV1,
               b1.RW0SubordinateAuthorizationProposalV1):
        payload["parent_ceilings" if cls is b1.RW0AuthorityVerificationObservationV1 else "ceilings"]["max_cpu_seconds"] = 999
    assert value.to_mapping() == saved
    projected = value.to_mapping()
    if cls is b1.RW0PhaseEntryBasisV1:
        projected["c2b3d_lineage"]["program_ref"] = "altered"
    assert value.to_mapping() == saved


def test_bool_integer_subclass_optional_pairs_and_windows() -> None:
    class IntChild(int):
        pass
    cls = b1.RW0PhaseEntryBasisV1
    assert reason(cls, reseal(cls, {**mapping_for(cls), "global_stop_version": True})) == "invalid_field_type"
    assert reason(cls, reseal(cls, {**mapping_for(cls), "global_stop_version": IntChild(1)})) == "invalid_field_type"
    cls = b1.RW0TerminalOutcomeV1
    assert reason(cls, reseal(cls, {**mapping_for(cls), "latch_postimage_ref": "ref-latch"})) == "invalid_length_or_cardinality"
    cls = b1.RW0AuthorityVerificationObservationV1
    assert reason(cls, reseal(cls, {**mapping_for(cls), "observation_expires_at": "2030-01-01T00:00:00Z"})) == "invalid_timestamp_window"


def test_enum_representation_is_separate_from_progression() -> None:
    authority = b1.RW0AuthorityVerificationObservationV1
    for status in ("verified", "denied", "unknown"):
        assert authority.from_mapping(mapping_for(authority, status=status)).status == status
    custody = b1.RW0CustodyAvailabilityObservationV1
    for status in ("available", "unavailable", "unknown"):
        assert custody.from_mapping(mapping_for(custody, availability=status)).availability == status
    event = b1.RW0RetrievalCapabilityEventObservationV1
    for kind in ("issued", "redeemed", "consumed", "expired", "revoked", "failed", "unknown"):
        assert event.from_mapping(mapping_for(event, event_kind=kind)).event_kind == kind
    qual = b1.RW0EffectHostQualificationV1
    for result, why in (("qualified", "qualified"), ("unknown", "unknown"),
                        *(("blocked", why) for why in BLOCKING_REASONS)):
        assert qual.from_mapping(mapping_for(qual, result=result, reason=why)).reason == why
    assert reason(qual, mapping_for(qual, result="qualified", reason="unknown")) == "qualification_reason_mismatch"


@pytest.mark.parametrize("branch,decision,outcome,pair", (
    ("normal", "accept", "accept", "latch_postimage"),
    ("normal", "repair", "repair", None),
    ("normal", "replan", "replan", None),
    ("normal", "terminal_reject", "terminal_reject", None),
    ("normal", "block", "block", None),
    ("active_cancel_reconciled", "cancel", "cancel", "reconciliation"),
    ("active_cancel_unresolved", "cancel", "block", "reconciliation"),
    ("pre_effect_cancel_basis_unusable", "cancel", "block", "mismatch"),
))
def test_terminal_matrix(branch: str, decision: str, outcome: str,
                         pair: str | None) -> None:
    cls = b1.RW0TerminalOutcomeV1
    fields: dict[str, object] = {"branch": branch, "decision_kind": decision,
                                 "outcome": outcome}
    if pair:
        fields[pair + "_ref"] = "ref-" + pair.replace("_", "-")
        fields[pair + "_digest"] = "a" * 64
    assert cls.from_mapping(mapping_for(cls, **fields)).branch == branch
    wrong = dict(fields)
    wrong["outcome"] = "cancel" if outcome != "cancel" else "accept"
    assert reason(cls, mapping_for(cls, **wrong)) == "terminal_branch_mismatch"


def test_budget_formula_exact_and_one_over_with_alias_and_cycle() -> None:
    for cls, _, _, limit in SCHEMAS:
        source = mapping_for(cls)
        if cls is b1.RW0AuthorityVerificationObservationV1:
            source = reseal(cls, {**source, "allowed_effect_classes": list(EFFECT_CLASSES)})
        budget = b1._WorkBudget(limit)
        budget.walk(source)
        budget.walk(deepcopy(source))
        assert budget.remaining == 0
        over = b1._WorkBudget(limit - 1)
        over.walk(source)
        with pytest.raises(b1.RW0PhaseValueError) as caught:
            over.walk(deepcopy(source))
        assert caught.value.reason == "cumulative_work_exhausted"
    shared: list[object] = ["x"]
    alias = [shared, shared]
    budget = b1._WorkBudget(5)
    budget.walk(alias)
    assert budget.remaining == 0
    cycle: list[object] = []
    cycle.append(cycle)
    with pytest.raises(b1.RW0PhaseValueError) as caught:
        b1._WorkBudget(100).walk(cycle)
    assert caught.value.reason == "graph_cycle"


def test_audit_f4_canonical_integer_bound_direct_and_nested() -> None:
    maximum = 2**63 - 1
    for cls, field in ((b1.RW0PhaseEntryBasisV1, "global_stop_version"),
                       (b1.RW0TerminalOutcomeV1, "program_head_revision")):
        payload = mapping_for(cls)
        payload[field] = maximum
        assert cls.from_mapping(reseal(cls, payload)).to_mapping()[field] == maximum
        payload[field] = maximum + 1
        assert reason(cls, payload) == "invalid_length_or_cardinality"
    basis = mapping_for(b1.RW0PhaseEntryBasisV1)
    basis["c2b3d_lineage"]["program_version_number"] = maximum + 1
    assert reason(b1.RW0PhaseEntryBasisV1, basis) == "invalid_length_or_cardinality"
    authority = mapping_for(b1.RW0AuthorityVerificationObservationV1)
    for field in ("max_active_invocations", "max_wall_seconds"):
        over = deepcopy(authority)
        over["parent_ceilings"][field] = maximum + 1
        assert reason(b1.RW0AuthorityVerificationObservationV1, over) == "invalid_length_or_cardinality"


def test_audit_f4_huge_exact_integer_rejects_before_json_conversion(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = mapping_for(b1.RW0PhaseEntryBasisV1)
    payload["global_stop_version"] = 10**4300
    def forbidden_json(*args: object, **kwargs: object) -> None:
        raise AssertionError("canonical JSON must not see an out-of-range integer")
    monkeypatch.setattr(b1.json, "dumps", forbidden_json)
    assert reason(b1.RW0PhaseEntryBasisV1, payload) == "invalid_length_or_cardinality"


@pytest.mark.parametrize("cls,member", (
    (b1.RW0AuthorityVerificationObservationV1, "parent_ceilings"),
    (b1.RW0SubordinateAuthorizationProposalV1, "ceilings"),
))
@pytest.mark.parametrize("field", (
    "max_active_invocations", "max_candidate_bytes", "max_changed_files",
    "max_cost_microusd", "max_cpu_seconds", "max_deliveries",
    "max_deployments", "max_local_commits", "max_memory_bytes",
    "max_merges", "max_model_input_tokens", "max_model_output_tokens",
    "max_pull_requests", "max_pushes", "max_wall_seconds",
))
def test_all_fifteen_nested_ceiling_integer_leaves_are_bounded(cls: type,
        member: str, field: str) -> None:
    maximum = 2**63 - 1
    at_max = mapping_for(cls)
    at_max[member][field] = maximum
    assert cls.from_mapping(reseal(cls, at_max)).to_mapping()[member][field] == maximum
    too_large = mapping_for(cls)
    too_large[member][field] = maximum + 1
    assert reason(cls, too_large) == "invalid_length_or_cardinality"


@pytest.mark.parametrize("field", ("program_version_number", "attempt_number"))
def test_both_l34_integer_leaves_are_bounded(field: str) -> None:
    maximum = 2**63 - 1
    at_max = mapping_for(b1.RW0PhaseEntryBasisV1)
    at_max["c2b3d_lineage"][field] = maximum
    at_max["selection_key"] = [
        [name, at_max["c2b3d_lineage"][name]]
        for name in ("program_ref", "semantic_attempt_ref", "candidate_ref",
                     "effect_intent_ref", "author_command_ref",
                     "attempt_fence_ref", "effect_fence_ref", "delivery_attempt_ref")
    ]
    assert b1.RW0PhaseEntryBasisV1.from_mapping(reseal(b1.RW0PhaseEntryBasisV1, at_max))
    too_large = mapping_for(b1.RW0PhaseEntryBasisV1)
    too_large["c2b3d_lineage"][field] = maximum + 1
    assert reason(b1.RW0PhaseEntryBasisV1, too_large) == "invalid_length_or_cardinality"


def test_literal_enum_oracles_are_independent_of_production_sets() -> None:
    expected = {
        "_EFFECT_HEAD_STATES": (
            "ready_for_delivery", "delivery_pending", "delivery_outcome_unknown",
            "observed", "cancellation_effect_established", "terminal",
        ),
        "_DELIVERY_HEAD_STATES": (
            "planned", "submitted", "outcome_unknown", "acknowledged",
            "rejected", "completed",
        ),
        "_STOP_STATES": ("clear", "active"),
        "_SUBJECT_KINDS": ("work_spec", "selected_plan"),
        "_QUALIFICATION_REASONS": (
            "qualified", "readiness_unready", "readiness_unknown",
            "readiness_expired", "authority_not_verified",
            "authority_denied_or_revoked", "authority_expired",
            "phase_or_effect_mismatch", "worker_artifact_mismatch",
            "worker_protocol_mismatch", "platform_or_architecture_mismatch",
            "profile_mismatch", "global_stop_active", "unknown",
        ),
        "_TERMINAL_OUTCOMES": (
            "accept", "repair", "replan", "terminal_reject", "block", "cancel",
        ),
        "_TERMINAL_BRANCHES": (
            "normal", "active_cancel_reconciled", "active_cancel_unresolved",
            "pre_effect_cancel_basis_unusable",
        ),
        "_RETRIEVAL_EVENTS": (
            "issued", "redeemed", "consumed", "expired", "revoked",
            "failed", "unknown",
        ),
    }
    for name, literal in expected.items():
        assert getattr(b1, name) == literal
    assert b1._EFFECT_CLASSES == EFFECT_CLASSES
    assert b1._QUALIFICATION_BLOCKING_REASONS == BLOCKING_REASONS


# Literal test-owned R inventories; never generated from production metadata.
_THIRD_R_FIELDS = {
    b1.RW0PhaseEntryBasisV1: "basis_ref selected_proposal_ref selected_artifact_ref disposition_ref global_stop_ref".split(),
    b1.RW0AuthorityVerificationObservationV1: "observation_ref source_ref evidence_ref phase_basis_ref parent_grant_ref grant_family_ref attempt_basis_ref effect_basis_ref attempt_fence_ref effect_fence_ref audience_ref repository_ref global_stop_ref".split(),
    b1.RW0SubordinateAuthorizationProposalV1: "proposal_ref phase_basis_ref verification_ref parent_grant_ref grant_family_ref attempt_basis_ref effect_basis_ref attempt_fence_ref effect_fence_ref audience_ref repository_ref global_stop_ref".split(),
    b1.RW0CustodyAvailabilityObservationV1: "observation_ref source_ref evidence_ref phase_basis_ref subject_ref".split(),
    b1.RW0RetrievalCapabilityEventObservationV1: "event_ref source_ref evidence_ref phase_basis_ref safe_correlation_ref subject_ref semantic_attempt_ref attempt_fence_ref effect_intent_ref effect_fence_ref audience_ref repository_ref authority_observation_ref subordinate_proposal_ref custody_observation_ref predecessor_event_ref".split(),
    b1.RW0RemoteHostReadinessObservationV1: "observation_ref source_ref evidence_ref safe_host_correlation_ref platform_profile_ref architecture_profile_ref worker_artifact_ref worker_protocol_ref execution_identity_profile_ref process_profile_ref isolation_profile_ref resource_profile_ref cancellation_profile_ref credential_handoff_profile_ref capsule_store_profile_ref validation_tool_profile_ref review_tool_profile_ref cleanup_profile_ref".split(),
    b1.RW0EffectHostQualificationV1: "qualification_ref phase_basis_ref effect_intent_ref effect_fence_ref verification_ref readiness_ref required_scenario_profile_ref required_platform_profile_ref required_architecture_profile_ref required_worker_artifact_ref required_worker_protocol_ref required_execution_identity_profile_ref required_process_profile_ref required_isolation_profile_ref required_resource_profile_ref required_cancellation_profile_ref required_credential_handoff_profile_ref required_capsule_store_profile_ref required_validation_tool_profile_ref required_review_tool_profile_ref required_cleanup_profile_ref".split(),
    b1.RW0TerminalOutcomeV1: "outcome_value_ref phase_basis_ref decision_ref global_stop_ref evidence_set_ref latch_postimage_ref reconciliation_ref mismatch_ref".split(),
}
_THIRD_L34_REFS = "program_ref program_version_ref accepted_intent_revision_ref work_item_ref work_item_revision_ref semantic_attempt_ref candidate_ref basis_decision_ref work_spec_ref effect_intent_ref author_command_ref standing_grant_ref attempt_authorization_ref effect_authorization_ref attempt_fence_ref effect_fence_ref delivery_attempt_ref authority_evaluation_ref".split()
_THIRD_K8_REFS = "program_ref semantic_attempt_ref candidate_ref effect_intent_ref author_command_ref attempt_fence_ref effect_fence_ref delivery_attempt_ref".split()


def _third_private_rejection(cls, payload, raw):
    with pytest.raises(b1.RW0PhaseValueError) as caught:
        cls.from_mapping(reseal(cls, payload))
    assert caught.value.reason == "privacy_forbidden_material"
    assert raw not in str(caught.value) and raw not in repr(caught.value)
    assert caught.value.__cause__ is None and caught.value.__context__ is None


@pytest.mark.parametrize("cls,field", [(cls, field) for cls, fields in _THIRD_R_FIELDS.items()
                                       for field in fields])
def test_third_ipv4_shaped_every_r_field(cls, field) -> None:
    payload = mapping_for(cls)
    if field == "predecessor_event_ref":
        payload.update(predecessor_event_digest="a" * 64, sequence_number=1, event_kind="redeemed")
    elif field == "latch_postimage_ref":
        payload.update(latch_postimage_digest="a" * 64, outcome="accept", decision_kind="accept")
    elif field == "reconciliation_ref":
        payload.update(reconciliation_digest="a" * 64, branch="active_cancel_reconciled",
                       outcome="cancel", decision_kind="cancel")
    elif field == "mismatch_ref":
        payload.update(mismatch_digest="a" * 64, branch="pre_effect_cancel_basis_unusable",
                       decision_kind="cancel")
    payload[field] = "safe-ref"
    assert cls.from_mapping(reseal(cls, payload)) is not None
    payload[field] = "192.0.2.1"
    _third_private_rejection(cls, payload, "192.0.2.1")


def _fourth_nested_mutant(field: str, surface: str):
    cls = b1.RW0PhaseEntryBasisV1
    original = mapping_for(cls)
    assert cls.from_mapping(original) is not None
    payload = deepcopy(original)
    if surface == "c2b3d_lineage":
        payload[surface][field] = "192.0.2.1"
    else:
        index = _THIRD_K8_REFS.index(field)
        assert payload[surface][index][0] == field
        payload[surface][index][1] = "192.0.2.1"
    reseal(cls, payload)
    assert {key for key in original if original[key] != payload[key]} == {surface, "basis_digest"}
    if surface == "c2b3d_lineage":
        assert payload["selection_key"] == original["selection_key"]
        assert {key for key in original[surface]
                if original[surface][key] != payload[surface][key]} == {field}
        for key, member in original[surface].items():
            if key != field:
                assert payload[surface][key] == member
        # L34 is a coordinate value without a lineage-level self-digest.
        lineage = b1.CanonicalC2B3DLineage(**original[surface])
        assert not hasattr(lineage, "computed_digest")
        assert lineage.to_mapping() == original[surface]
    else:
        assert payload["c2b3d_lineage"] == original["c2b3d_lineage"]
        assert [i for i, pair in enumerate(original[surface])
                if pair != payload[surface][i]] == [index]
        assert payload[surface][index] == [field, "192.0.2.1"]
    return payload


@pytest.mark.parametrize("field", _THIRD_L34_REFS)
def test_third_ipv4_shaped_nested_lineage(field) -> None:
    payload = _fourth_nested_mutant(field, "c2b3d_lineage")
    _third_private_rejection(b1.RW0PhaseEntryBasisV1, payload, "192.0.2.1")


@pytest.mark.parametrize("field", _THIRD_K8_REFS)
def test_third_ipv4_shaped_selection_key(field) -> None:
    payload = _fourth_nested_mutant(field, "selection_key")
    _third_private_rejection(b1.RW0PhaseEntryBasisV1, payload, "192.0.2.1")


@pytest.mark.parametrize("raw", ("10.0.0.1", "001.002.003.004", "999.999.999.999"))
def test_third_ipv4_shaped_representative_literals(raw) -> None:
    cls = b1.RW0RemoteHostReadinessObservationV1
    _third_private_rejection(cls, mapping_for(cls, safe_host_correlation_ref=raw), raw)


def test_third_ref_inventory_and_positive_syntax_controls() -> None:
    assert set(_THIRD_R_FIELDS) == {row[0] for row in SCHEMAS}
    for cls, fields in _THIRD_R_FIELDS.items():
        assert set(fields) == {name for name in cls._FIELDS if name.endswith("_ref")}
    assert set(_THIRD_L34_REFS) == {name for name in b1._L34_FIELDS if name.endswith("_ref")}
    assert tuple(_THIRD_K8_REFS) == b1._K8_FIELDS
    cls = b1.RW0RemoteHostReadinessObservationV1
    for safe in ("host.profile.v1", "artifact.ref.1", "192.0.2.ref"):
        assert cls.from_mapping(mapping_for(cls, safe_host_correlation_ref=safe)).safe_host_correlation_ref == safe
    for malformed in ("２００.0.2.1", "2001:db8::1", "https://host"):
        assert reason(cls, mapping_for(cls, safe_host_correlation_ref=malformed)) == "malformed_ref"
    class StringChild(str):
        pass
    assert reason(cls, mapping_for(cls, safe_host_correlation_ref=StringChild("192.0.2.1"))) == "invalid_field_type"


@pytest.mark.parametrize("cls,schema,count,limit", SCHEMAS)
def test_fourth_oversize_closed_mapping_is_content_free(cls, schema, count, limit) -> None:
    payload = mapping_for(cls)
    for index in range(1000 - count):
        payload[f"unknown-sentinel-{index}"] = "VALUE-SENTINEL"
    assert len(payload) == 1000
    with pytest.raises(b1.RW0PhaseValueError) as caught:
        cls.from_mapping(payload)
    assert caught.value.reason == "unknown_field"
    assert caught.value.field_path == cls.__name__
    assert str(caught.value) == "unknown_field:" + cls.__name__
    assert "sentinel" not in (str(caught.value) + repr(caught.value)).lower()
    assert caught.value.__cause__ is None and caught.value.__context__ is None


@pytest.mark.parametrize("cls", (b1.RW0CustodyAvailabilityObservationV1,
                                b1.RW0EffectHostQualificationV1))
def test_fourth_exact_cardinality_unknown_precedes_missing(cls) -> None:
    payload = mapping_for(cls)
    field = "observation_ref" if cls is b1.RW0CustodyAvailabilityObservationV1 else "qualification_ref"
    del payload[field]
    assert reason(cls, payload) == "missing_field"
    payload["unknown-sentinel"] = "VALUE-SENTINEL"
    assert reason(cls, payload) == "unknown_field"
    del payload["unknown-sentinel"]
    payload[7] = "VALUE-SENTINEL"
    assert reason(cls, payload) == "invalid_field_type"


@pytest.mark.parametrize("cls,schema,count,limit", SCHEMAS)
def test_fourth_actual_constructor_maximum_and_one_over_budget(monkeypatch, cls, schema, count, limit) -> None:
    payload = mapping_for(cls)
    if cls is b1.RW0AuthorityVerificationObservationV1:
        payload = reseal(cls, {**payload, "allowed_effect_classes": list(EFFECT_CLASSES)})
    original = b1._WorkBudget
    instances = []
    class Measured(original):
        def __init__(self, given):
            assert given == limit
            super().__init__(given)
            instances.append(self)
    monkeypatch.setattr(b1, "_WorkBudget", Measured)
    assert cls.from_mapping(payload).to_mapping() == payload
    assert len(instances) == 1 and instances[0].remaining == 0
    class OneLess(original):
        def __init__(self, given):
            assert given == limit
            super().__init__(given - 1)
    monkeypatch.setattr(b1, "_WorkBudget", OneLess)
    assert reason(cls, payload) == "cumulative_work_exhausted"


def test_fourth_k8_oracle_detects_only_k8_privacy_regression(monkeypatch) -> None:
    original = b1._ref
    def without_k8_ipv4(value, label):
        if label == "selection_key" and value == "192.0.2.1":
            return value
        return original(value, label)
    monkeypatch.setattr(b1, "_ref", without_k8_ipv4)
    for field in _THIRD_K8_REFS:
        # The actual K8 oracle must fail if only its rejection is removed.
        with pytest.raises(AssertionError):
            test_third_ipv4_shaped_selection_key(field)
        test_third_ipv4_shaped_nested_lineage(field)
