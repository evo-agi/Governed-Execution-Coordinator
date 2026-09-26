from __future__ import annotations

import hashlib
import json

import pytest

import ge_nwp_coordinator._rw0_phase_entry_semantic_values as b1
import ge_nwp_coordinator._rw0_worker_mechanism_capability_values as capability
from ge_nwp_coordinator._rw0_worker_mechanism_capability_values import (
    RW0WorkerMechanismCapabilityDeclarationV1,
    RW0WorkerMechanismCapabilityError,
    RW0WorkerMechanismCapabilityObservationV1,
    RW0WorkerMechanismCapabilityQualificationV1,
    validate_worker_mechanism_capability_qualification,
)
from test_rw0_b1_relations import NOW, claims, value
from test_rw0_b2_capability_values import (
    DIMENSIONS, QUALIFICATION_SCHEMA, WIRE_DIGEST, WIRE_REF,
    declaration_mapping, observation_mapping, qualification_mapping, seal,
)


BLOCKING_B1_REASONS = (
    "authority_denied_or_revoked", "authority_expired", "authority_not_verified",
    "global_stop_active", "phase_or_effect_mismatch", "platform_or_architecture_mismatch",
    "profile_mismatch", "readiness_expired", "readiness_unknown", "readiness_unready",
    "worker_artifact_mismatch", "worker_protocol_mismatch",
)


def _forge_b1_value(
    cls: type, identity: dict[str, object],
) -> tuple[object, str]:
    mapping = dict(identity)
    final = cls._FIELDS[-1]
    mapping.pop(final, None)
    canonical = json.dumps(
        mapping, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8", "strict")
    digest = hashlib.sha256(
        (cls._SCHEMA + ".identity").encode("utf-8") + b"\0" + canonical
    ).hexdigest()
    mapping[final] = digest
    forged = object.__new__(cls)
    object.__setattr__(
        forged, "_values", tuple(mapping[name] for name in cls._FIELDS)
    )
    return forged, digest


def host_graph(
    *,
    mode: str = "qualified",
    worker_artifact_ref: str = "worker-artifact.safe.0001",
    worker_artifact_digest: str = "a" * 64,
    wire_profile_ref: str = WIRE_REF,
    wire_profile_digest: str = WIRE_DIGEST,
):
    basis, authority, _, _, _, effect, _ = claims()
    if mode == "unknown":
        authority = value(
            b1.RW0AuthorityVerificationObservationV1,
            **{**authority.identity_mapping(), "status": "unknown"},
        )
    readiness_changes: dict[str, object] = {
        "worker_artifact_ref": worker_artifact_ref,
        "worker_artifact_digest": worker_artifact_digest,
        "worker_protocol_ref": wire_profile_ref,
        "worker_protocol_digest": wire_profile_digest,
        "observed_at": "2028-01-01T00:00:00Z",
        "expires_at": "2030-01-01T00:00:00Z",
    }
    if mode == "blocked":
        readiness_changes["status"] = "unready"
    readiness = value(b1.RW0RemoteHostReadinessObservationV1, **readiness_changes)
    matching: dict[str, object] = {
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
    for stem in (
        "platform_profile", "architecture_profile", "worker_artifact",
        "worker_protocol", "execution_identity_profile", "process_profile",
        "isolation_profile", "resource_profile", "cancellation_profile",
        "credential_handoff_profile", "capsule_store_profile",
        "validation_tool_profile", "review_tool_profile", "cleanup_profile",
    ):
        for suffix in ("_ref", "_digest"):
            matching["required_" + stem + suffix] = getattr(readiness, stem + suffix)
    if mode == "blocked":
        matching.update(result="blocked", reason="readiness_unready")
    elif mode == "unknown":
        matching.update(result="unknown", reason="unknown")
    host = value(b1.RW0EffectHostQualificationV1, **matching)
    return basis, authority, readiness, host, effect


def capability_graph(
    *,
    expected: tuple[str, str] = ("qualified", "qualified"),
    declaration_changes: dict[str, object] | None = None,
    observation_changes: dict[str, object] | None = None,
    qualification_changes: dict[str, object] | None = None,
    b1_mode: str = "qualified",
    b1_artifact: tuple[str, str] | None = None,
    b1_wire: tuple[str, str] | None = None,
):
    declaration_record = declaration_mapping(**(declaration_changes or {}))
    observation_record = observation_mapping(
        declaration_record, **(observation_changes or {}))
    artifact = b1_artifact or (
        declaration_record["worker_artifact_ref"],
        declaration_record["worker_artifact_digest"],
    )
    wire = b1_wire or (
        declaration_record["wire_profile_ref"],
        declaration_record["wire_profile_digest"],
    )
    basis, authority, readiness, host, effect = host_graph(
        mode=b1_mode,
        worker_artifact_ref=artifact[0], worker_artifact_digest=artifact[1],
        wire_profile_ref=wire[0], wire_profile_digest=wire[1],
    )
    qualification_coordinates: dict[str, object] = {
        "phase_basis_ref": basis.basis_ref,
        "phase_basis_digest": basis.basis_digest,
        "authority_observation_ref": authority.observation_ref,
        "authority_observation_digest": authority.observation_digest,
        "readiness_observation_ref": readiness.observation_ref,
        "readiness_observation_digest": readiness.observation_digest,
        "host_qualification_ref": host.qualification_ref,
        "host_qualification_digest": host.qualification_digest,
        "effect_intent_ref": effect.effect_intent_ref,
        "effect_fence_ref": effect.effect_fence_ref,
        "effect_fence_digest": effect.effect_fence_digest,
        "evaluated_at": NOW,
        "result": expected[0],
        "reason": expected[1],
    }
    qualification_coordinates.update(qualification_changes or {})
    qualification_record = qualification_mapping(
        declaration_record, observation_record, **qualification_coordinates)
    declaration = RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(
        declaration_record)
    observation = RW0WorkerMechanismCapabilityObservationV1.from_mapping(
        observation_record)
    qualification = RW0WorkerMechanismCapabilityQualificationV1.from_mapping(
        qualification_record)
    arguments = {
        "declaration": declaration,
        "observation": observation,
        "qualification": qualification,
        "phase_basis": basis,
        "authority_observation": authority,
        "readiness_observation": readiness,
        "host_qualification": host,
        "current_effect_fence": effect,
        "now_utc": NOW,
    }
    return arguments


def test_correctly_resealed_constructor_invalid_readiness_fails_before_precedence() -> None:
    case = capability_graph()
    readiness_identity = case["readiness_observation"].identity_mapping()
    readiness_identity["status"] = "constructor-invalid-status"
    readiness, readiness_digest = _forge_b1_value(
        b1.RW0RemoteHostReadinessObservationV1, readiness_identity
    )

    host_identity = case["host_qualification"].identity_mapping()
    host_identity["readiness_digest"] = readiness_digest
    host, host_digest = _forge_b1_value(
        b1.RW0EffectHostQualificationV1, host_identity
    )

    qualification_mapping_value = case["qualification"].identity_mapping()
    qualification_mapping_value["readiness_observation_digest"] = readiness_digest
    qualification_mapping_value["host_qualification_digest"] = host_digest
    case["qualification"] = (
        RW0WorkerMechanismCapabilityQualificationV1.from_mapping(
            seal(
                qualification_mapping_value,
                QUALIFICATION_SCHEMA,
                "capability_qualification_digest",
            )
        )
    )
    case["readiness_observation"] = readiness
    case["host_qualification"] = host

    relation_error("relation_mismatch", case)


def expected_result(arguments: dict[str, object]) -> tuple[str, str]:
    """Literal test-owned oracle; it deliberately uses no production helper."""
    declaration = arguments["declaration"]
    observation = arguments["observation"]
    qualification = arguments["qualification"]
    basis = arguments["phase_basis"]
    authority = arguments["authority_observation"]
    readiness = arguments["readiness_observation"]
    host = arguments["host_qualification"]
    effect = arguments["current_effect_fence"]
    now = arguments["now_utc"]
    coordinate_match = (
        (qualification.phase_basis_ref, qualification.phase_basis_digest)
        == (basis.basis_ref, basis.basis_digest)
        and (qualification.authority_observation_ref,
             qualification.authority_observation_digest)
        == (authority.observation_ref, authority.observation_digest)
        and (qualification.readiness_observation_ref,
             qualification.readiness_observation_digest)
        == (readiness.observation_ref, readiness.observation_digest)
        and (qualification.host_qualification_ref,
             qualification.host_qualification_digest)
        == (host.qualification_ref, host.qualification_digest)
        and (qualification.effect_intent_ref, qualification.effect_fence_ref,
             qualification.effect_fence_digest)
        == (effect.effect_intent_ref, effect.effect_fence_ref,
            effect.effect_fence_digest)
        and qualification.evaluated_at == host.evaluated_at == now
    )
    if not coordinate_match:
        return "blocked", "b1_binding_mismatch"
    if host.result == "blocked":
        assert host.reason in BLOCKING_B1_REASONS
        return "blocked", "b1_host_qualification_blocked"
    if host.result == "unknown" and host.reason == "unknown":
        return "unknown", "b1_host_qualification_unknown"
    if (observation.capability_declaration_ref,
        observation.capability_declaration_digest) != (
            declaration.capability_declaration_ref,
            declaration.capability_declaration_digest):
        return "blocked", "declaration_observation_mismatch"
    if declaration.declaration_source_ref == observation.observation_source_ref:
        return "blocked", "self_observation"
    if not observation.observed_at <= now < observation.expires_at:
        return "blocked", "observation_expired"
    artifacts = {
        (declaration.worker_artifact_ref, declaration.worker_artifact_digest),
        (observation.worker_artifact_ref, observation.worker_artifact_digest),
        (qualification.worker_artifact_ref, qualification.worker_artifact_digest),
        (readiness.worker_artifact_ref, readiness.worker_artifact_digest),
        (host.required_worker_artifact_ref, host.required_worker_artifact_digest),
    }
    if len(artifacts) != 1:
        return "blocked", "worker_artifact_mismatch"
    profiles = {
        (declaration.wire_profile_ref, declaration.wire_profile_digest),
        (observation.wire_profile_ref, observation.wire_profile_digest),
        (qualification.wire_profile_ref, qualification.wire_profile_digest),
        (WIRE_REF, WIRE_DIGEST),
        (readiness.worker_protocol_ref, readiness.worker_protocol_digest),
        (host.required_worker_protocol_ref, host.required_worker_protocol_digest),
    }
    if len(profiles) != 1:
        return "blocked", "wire_profile_mismatch"
    if any(getattr(declaration, name) == "unsupported" for name in DIMENSIONS):
        return "blocked", "declaration_unsupported"
    if any(getattr(observation, name) == "contradicted" for name in DIMENSIONS):
        return "blocked", "observation_nonconformant"
    if (any(getattr(declaration, name) == "unknown" for name in DIMENSIONS)
            or any(getattr(observation, name) == "unknown" for name in DIMENSIONS)):
        return "unknown", "capability_unknown"
    return "qualified", "qualified"


def invoke(arguments: dict[str, object]) -> None:
    assert validate_worker_mechanism_capability_qualification(**arguments) is None


def relation_error(reason: str, arguments: dict[str, object]) -> None:
    with pytest.raises(RW0WorkerMechanismCapabilityError) as caught:
        validate_worker_mechanism_capability_qualification(**arguments)
    assert caught.value.reason == reason
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_all_results_reasons_dimensions_freshness_and_precedence() -> None:
    cases = [
        capability_graph(),
        capability_graph(
            expected=("blocked", "b1_binding_mismatch"),
            qualification_changes={"phase_basis_ref": "other-phase-basis.safe.0001"},
        ),
        capability_graph(expected=("blocked", "b1_host_qualification_blocked"),
                         b1_mode="blocked"),
        capability_graph(expected=("unknown", "b1_host_qualification_unknown"),
                         b1_mode="unknown"),
        capability_graph(
            expected=("blocked", "declaration_observation_mismatch"),
            observation_changes={"capability_declaration_ref": "other-declaration.safe.0001"},
        ),
        capability_graph(
            expected=("blocked", "self_observation"),
            declaration_changes={"declaration_source_ref": "independent-observer.safe.0001"},
        ),
        capability_graph(
            expected=("blocked", "observation_expired"),
            observation_changes={"expires_at": NOW},
        ),
        capability_graph(
            expected=("blocked", "worker_artifact_mismatch"),
            observation_changes={"worker_artifact_ref": "other-artifact.safe.0001"},
        ),
        capability_graph(
            expected=("blocked", "wire_profile_mismatch"),
            observation_changes={"wire_profile_ref": "other-wire.safe.0001"},
        ),
        capability_graph(
            expected=("blocked", "declaration_unsupported"),
            declaration_changes={"zero_git_effects": "unsupported"},
        ),
        capability_graph(
            expected=("blocked", "observation_nonconformant"),
            observation_changes={"zero_git_effects": "contradicted"},
        ),
        capability_graph(
            expected=("unknown", "capability_unknown"),
            observation_changes={"zero_git_effects": "unknown"},
        ),
    ]
    assert [expected_result(case) for case in cases] == [
        (case["qualification"].result, case["qualification"].reason) for case in cases
    ]
    for case in cases:
        invoke(case)

    # Equal-time observation is fresh, while equal-time expiry above is blocked.
    equal_time = capability_graph(observation_changes={"observed_at": NOW})
    assert expected_result(equal_time) == ("qualified", "qualified")
    invoke(equal_time)

    # Every individual dimension state is owned by this oracle and relation.
    for dimension in DIMENSIONS:
        unsupported = capability_graph(
            expected=("blocked", "declaration_unsupported"),
            declaration_changes={dimension: "unsupported"},
        )
        contradicted = capability_graph(
            expected=("blocked", "observation_nonconformant"),
            observation_changes={dimension: "contradicted"},
        )
        unknown_declaration = capability_graph(
            expected=("unknown", "capability_unknown"),
            declaration_changes={dimension: "unknown"},
        )
        unknown_observation = capability_graph(
            expected=("unknown", "capability_unknown"),
            observation_changes={dimension: "unknown"},
        )
        for case in (unsupported, contradicted, unknown_declaration, unknown_observation):
            assert expected_result(case) == (
                case["qualification"].result, case["qualification"].reason)
            invoke(case)

    # Pairwise conflicts pin that every earlier predicate wins every later one.
    precedence_mutations = (
        ({"phase_basis_ref": "other-phase.safe.0001"},
         {"wire_profile_ref": "other-wire.safe.0001"},
         ("blocked", "b1_binding_mismatch")),
        ({}, {"capability_declaration_ref": "other-declaration.safe.0001",
              "wire_profile_ref": "other-wire.safe.0001"},
         ("blocked", "declaration_observation_mismatch")),
        ({}, {"expires_at": NOW, "zero_git_effects": "contradicted"},
         ("blocked", "observation_expired")),
        ({}, {"worker_artifact_ref": "other-artifact.safe.0001",
              "wire_profile_ref": "other-wire.safe.0001"},
         ("blocked", "worker_artifact_mismatch")),
    )
    for qualification_changes, observation_changes, expected in precedence_mutations:
        case = capability_graph(
            expected=expected, qualification_changes=qualification_changes,
            observation_changes=observation_changes,
        )
        assert expected_result(case) == expected
        invoke(case)


def test_b1_call_once_complete_coordinates_and_bare_qualified_false_positive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = capability_graph()
    original = capability._validate_host_qualification_with_snapshots
    calls = []

    def measured(**kwargs: object):
        calls.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(
        capability, "_validate_host_qualification_with_snapshots", measured
    )
    invoke(case)
    assert len(calls) == 1
    assert calls[0] == {
        "basis": case["phase_basis"],
        "authority": case["authority_observation"],
        "readiness": case["readiness_observation"],
        "qualification": case["host_qualification"],
        "current_effect_fence": case["current_effect_fence"],
        "now_utc": NOW,
    }

    retained_wire_pair = (
        capability._WIRE_PROFILE_REF, capability._WIRE_PROFILE_DIGEST)

    def mutate_after_relation_snapshot(**kwargs: object):
        capability._WIRE_PROFILE_REF = "mutated-wire.safe.0001"
        capability._WIRE_PROFILE_DIGEST = "0" * 64
        return original(**kwargs)

    monkeypatch.setattr(
        capability,
        "_validate_host_qualification_with_snapshots",
        mutate_after_relation_snapshot,
    )
    try:
        invoke(capability_graph())
    finally:
        capability._WIRE_PROFILE_REF, capability._WIRE_PROFILE_DIGEST = retained_wire_pair
        monkeypatch.setattr(
            capability, "_validate_host_qualification_with_snapshots", measured
        )

    for field in (
        "phase_basis_ref", "phase_basis_digest", "authority_observation_ref",
        "authority_observation_digest", "readiness_observation_ref",
        "readiness_observation_digest", "host_qualification_ref",
        "host_qualification_digest", "effect_intent_ref", "effect_fence_ref",
        "effect_fence_digest", "evaluated_at",
    ):
        replacement = "0" * 64 if field.endswith("_digest") else (
            "2029-01-01T00:00:01Z" if field == "evaluated_at" else "other.safe.0001")
        changed = capability_graph(
            expected=("blocked", "b1_binding_mismatch"),
            qualification_changes={field: replacement},
        )
        invoke(changed)

    # A constructor-valid bare B1 qualified pair cannot bypass its owning relation.
    broken = capability_graph()
    readiness = value(
        b1.RW0RemoteHostReadinessObservationV1,
        **{**broken["readiness_observation"].identity_mapping(),
           "worker_artifact_ref": "different-artifact.safe.0001"},
    )
    broken["readiness_observation"] = readiness
    qualification_map = broken["qualification"].identity_mapping()
    qualification_map["readiness_observation_ref"] = readiness.observation_ref
    qualification_map["readiness_observation_digest"] = readiness.observation_digest
    qualification_map["result"] = "blocked"
    qualification_map["reason"] = "b1_host_qualification_blocked"
    broken["qualification"] = RW0WorkerMechanismCapabilityQualificationV1.from_mapping(
        seal(qualification_map, QUALIFICATION_SCHEMA,
             "capability_qualification_digest"))
    relation_error("relation_mismatch", broken)


def test_subject_identity_artifact_wire_and_b1_graph_matrices() -> None:
    for field in (
        "capability_declaration_ref", "capability_declaration_digest",
        "capability_observation_ref", "capability_observation_digest",
    ):
        case = capability_graph()
        identity = case["qualification"].identity_mapping()
        identity[field] = "0" * 64 if field.endswith("_digest") else "other.safe.0001"
        case["qualification"] = RW0WorkerMechanismCapabilityQualificationV1.from_mapping(
            seal(identity, QUALIFICATION_SCHEMA,
                 "capability_qualification_digest"))
        relation_error("relation_mismatch", case)

    for location in ("declaration", "observation", "qualification", "b1"):
        if location == "declaration":
            case = capability_graph(
                expected=("blocked", "worker_artifact_mismatch"),
                declaration_changes={"worker_artifact_ref": "artifact-other.safe.0001"},
                b1_artifact=("worker-artifact.safe.0001", "a" * 64),
            )
        elif location == "observation":
            case = capability_graph(
                expected=("blocked", "worker_artifact_mismatch"),
                observation_changes={"worker_artifact_digest": "2" * 64},
            )
        elif location == "qualification":
            case = capability_graph(
                expected=("blocked", "worker_artifact_mismatch"),
                qualification_changes={"worker_artifact_ref": "artifact-other.safe.0001"},
            )
        else:
            case = capability_graph(
                expected=("blocked", "worker_artifact_mismatch"),
                b1_artifact=("artifact-other.safe.0001", "2" * 64),
            )
        assert expected_result(case) == ("blocked", "worker_artifact_mismatch")
        invoke(case)

    for location in ("declaration", "observation", "qualification", "b1"):
        if location == "declaration":
            case = capability_graph(
                expected=("blocked", "wire_profile_mismatch"),
                declaration_changes={"wire_profile_ref": "wire-other.safe.0001"},
                b1_wire=(WIRE_REF, WIRE_DIGEST),
            )
        elif location == "observation":
            case = capability_graph(
                expected=("blocked", "wire_profile_mismatch"),
                observation_changes={"wire_profile_digest": "2" * 64},
            )
        elif location == "qualification":
            case = capability_graph(
                expected=("blocked", "wire_profile_mismatch"),
                qualification_changes={"wire_profile_ref": "wire-other.safe.0001"},
            )
        else:
            case = capability_graph(
                expected=("blocked", "wire_profile_mismatch"),
                b1_wire=("wire-other.safe.0001", "2" * 64),
            )
        assert expected_result(case) == ("blocked", "wire_profile_mismatch")
        invoke(case)


def test_relation_local_b1_and_composed_work_accounting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = capability_graph()
    original_capability_budget = capability._WorkBudget
    capability_instances = []

    class MeasuredCapability(original_capability_budget):
        def __init__(self, limit: int) -> None:
            assert limit == 249
            super().__init__(limit)
            capability_instances.append(self)

    monkeypatch.setattr(capability, "_WorkBudget", MeasuredCapability)
    invoke(case)
    assert len(capability_instances) == 1
    assert capability_instances[0].remaining == 0

    class OneUnderCapability(original_capability_budget):
        def __init__(self, limit: int) -> None:
            assert limit == 249
            super().__init__(248)

    monkeypatch.setattr(capability, "_WorkBudget", OneUnderCapability)
    relation_error("cumulative_work_exhausted", case)
    monkeypatch.setattr(capability, "_WorkBudget", original_capability_budget)

    original_b1_budget = b1._WorkBudget
    b1_instances = []

    class MeasuredB1(original_b1_budget):
        def __init__(self, limit: int) -> None:
            super().__init__(limit)
            if limit == 863:
                b1_instances.append(self)

    monkeypatch.setattr(b1, "_WorkBudget", MeasuredB1)
    invoke(case)
    assert len(b1_instances) == 1
    assert b1_instances[0].remaining == 0

    class OneUnderB1(original_b1_budget):
        def __init__(self, limit: int) -> None:
            super().__init__(862 if limit == 863 else limit)

    monkeypatch.setattr(b1, "_WorkBudget", OneUnderB1)
    relation_error("relation_mismatch", case)
    assert 863 + 249 == 1112


def test_safe_reconstruction_mutants_and_originals_are_never_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = capability_graph()
    original = capability._safe_reconstruct_impl
    seen = []

    def rebuild_then_poison(value: object, expected: type, budget: object):
        rebuilt = original(value, expected, budget)
        seen.append(expected)
        members = list(object.__getattribute__(value, "_values"))
        members[0] = "POISONED-ORIGINAL"
        object.__setattr__(value, "_values", tuple(members))
        return rebuilt

    monkeypatch.setattr(capability, "_safe_reconstruct_impl", rebuild_then_poison)
    invoke(case)
    assert seen == [
        RW0WorkerMechanismCapabilityDeclarationV1,
        RW0WorkerMechanismCapabilityObservationV1,
        RW0WorkerMechanismCapabilityQualificationV1,
    ]

    # A missing reconstruction cannot be hidden by a later result mismatch.
    monkeypatch.setattr(capability, "_safe_reconstruct_impl", original)
    bad_case = capability_graph()
    bad_declaration = bad_case["declaration"]
    members = list(object.__getattribute__(bad_declaration, "_values"))
    members[0] = "invalid-but-otherwise-unused-schema"
    object.__setattr__(bad_declaration, "_values", tuple(members))
    relation_error("invalid_enum", bad_case)

    def rejected() -> bool:
        try:
            validate_worker_mechanism_capability_qualification(**bad_case)
        except RW0WorkerMechanismCapabilityError:
            return True
        return False

    assert rejected()

    def selective_bypass(value: object, expected: type, budget: object):
        if expected is RW0WorkerMechanismCapabilityDeclarationV1:
            return value
        return original(value, expected, budget)

    monkeypatch.setattr(capability, "_safe_reconstruct_impl", selective_bypass)
    assert not rejected()

    monkeypatch.setattr(
        capability, "_safe_reconstruct_impl",
        lambda value, expected, budget: value,
    )
    assert not rejected()
