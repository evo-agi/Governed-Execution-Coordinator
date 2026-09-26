from __future__ import annotations

import gc
import hashlib
import json
import pickle
import weakref
from copy import copy, deepcopy

import pytest

import ge_nwp_coordinator._rw0_worker_mechanism_capability_values as capability
from ge_nwp_coordinator._rw0_worker_mechanism_capability_values import (
    RW0WorkerMechanismCapabilityDeclarationV1,
    RW0WorkerMechanismCapabilityError,
    RW0WorkerMechanismCapabilityObservationV1,
    RW0WorkerMechanismCapabilityQualificationV1,
)


DECLARATION_FIELDS = (
    "schema_id", "capability_declaration_ref", "declaration_source_kind",
    "declaration_source_ref", "worker_artifact_ref", "worker_artifact_digest",
    "wire_profile_ref", "wire_profile_digest", "noninteractive_operation",
    "wire_command_input_only", "wire_result_output_only", "protocol_stdout_only",
    "private_bounded_diagnostic_stderr", "external_cancellation_control_supported",
    "external_deadline_control_supported", "invocation_bound_logical_context",
    "private_history_non_authority", "isolated_credential_use",
    "private_interaction_material", "zero_git_effects", "restricted_network_access",
    "external_session_non_authority", "capability_declaration_digest",
)
OBSERVATION_FIELDS = (
    "schema_id", "capability_observation_ref", "observation_source_kind",
    "observation_source_ref", "observation_source_invocation_ref", "evidence_ref",
    "evidence_digest", "capability_declaration_ref", "capability_declaration_digest",
    "worker_artifact_ref", "worker_artifact_digest", "wire_profile_ref",
    "wire_profile_digest", "noninteractive_operation", "wire_command_input_only",
    "wire_result_output_only", "protocol_stdout_only",
    "private_bounded_diagnostic_stderr", "external_cancellation_control_supported",
    "external_deadline_control_supported", "invocation_bound_logical_context",
    "private_history_non_authority", "isolated_credential_use",
    "private_interaction_material", "zero_git_effects", "restricted_network_access",
    "external_session_non_authority", "observed_at", "expires_at",
    "capability_observation_digest",
)
QUALIFICATION_FIELDS = (
    "schema_id", "capability_qualification_ref", "capability_declaration_ref",
    "capability_declaration_digest", "capability_observation_ref",
    "capability_observation_digest", "worker_artifact_ref", "worker_artifact_digest",
    "wire_profile_ref", "wire_profile_digest", "phase_basis_ref", "phase_basis_digest",
    "authority_observation_ref", "authority_observation_digest",
    "readiness_observation_ref", "readiness_observation_digest",
    "host_qualification_ref", "host_qualification_digest", "effect_intent_ref",
    "effect_fence_ref", "effect_fence_digest", "result", "reason", "evaluated_at",
    "capability_qualification_digest",
)
DIMENSIONS = (
    "noninteractive_operation", "wire_command_input_only", "wire_result_output_only",
    "protocol_stdout_only", "private_bounded_diagnostic_stderr",
    "external_cancellation_control_supported", "external_deadline_control_supported",
    "invocation_bound_logical_context", "private_history_non_authority",
    "isolated_credential_use", "private_interaction_material", "zero_git_effects",
    "restricted_network_access", "external_session_non_authority",
)
DECLARATION_SCHEMA = (
    "governed-execution.nwp-rw0-worker-mechanism-capability-declaration.v1"
)
OBSERVATION_SCHEMA = (
    "governed-execution.nwp-rw0-worker-mechanism-capability-observation.v1"
)
QUALIFICATION_SCHEMA = (
    "governed-execution.nwp-rw0-worker-mechanism-capability-qualification.v1"
)
WIRE_REF = "rw0-wire-nwpf-v1"
WIRE_DIGEST = "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454"


def canonical(mapping: dict[str, object]) -> bytes:
    return json.dumps(
        mapping, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8", "strict")


def seal(mapping: dict[str, object], schema: str, final: str) -> dict[str, object]:
    result = dict(mapping)
    identity = {key: value for key, value in result.items() if key != final}
    result[final] = hashlib.sha256(
        (schema + ".identity").encode("utf-8") + b"\0" + canonical(identity)
    ).hexdigest()
    return result


def declaration_mapping(**changes: object) -> dict[str, object]:
    identity: dict[str, object] = {
        "schema_id": DECLARATION_SCHEMA,
        "capability_declaration_ref": "capability-declaration.safe.0001",
        "declaration_source_kind": "worker_artifact_owner",
        "declaration_source_ref": "artifact-owner.safe.0001",
        "worker_artifact_ref": "worker-artifact.safe.0001",
        "worker_artifact_digest": "a" * 64,
        "wire_profile_ref": WIRE_REF,
        "wire_profile_digest": WIRE_DIGEST,
    }
    identity.update({name: "supported" for name in DIMENSIONS})
    identity.update(changes)
    return seal(identity, DECLARATION_SCHEMA, "capability_declaration_digest")


def observation_mapping(declaration: dict[str, object] | None = None,
                        **changes: object) -> dict[str, object]:
    owner = declaration_mapping() if declaration is None else declaration
    identity: dict[str, object] = {
        "schema_id": OBSERVATION_SCHEMA,
        "capability_observation_ref": "capability-observation.safe.0001",
        "observation_source_kind": "independent_worker_mechanism_observer",
        "observation_source_ref": "independent-observer.safe.0001",
        "observation_source_invocation_ref": "observer-invocation.safe.0001",
        "evidence_ref": "capability-evidence.safe.0001",
        "evidence_digest": "b" * 64,
        "capability_declaration_ref": owner["capability_declaration_ref"],
        "capability_declaration_digest": owner["capability_declaration_digest"],
        "worker_artifact_ref": owner["worker_artifact_ref"],
        "worker_artifact_digest": owner["worker_artifact_digest"],
        "wire_profile_ref": owner["wire_profile_ref"],
        "wire_profile_digest": owner["wire_profile_digest"],
        "observed_at": "2028-01-01T00:00:00Z",
        "expires_at": "2030-01-01T00:00:00Z",
    }
    identity.update({name: "confirmed" for name in DIMENSIONS})
    identity.update(changes)
    return seal(identity, OBSERVATION_SCHEMA, "capability_observation_digest")


def qualification_mapping(
    declaration: dict[str, object] | None = None,
    observation: dict[str, object] | None = None,
    **changes: object,
) -> dict[str, object]:
    owner = declaration_mapping() if declaration is None else declaration
    observed = observation_mapping(owner) if observation is None else observation
    identity: dict[str, object] = {
        "schema_id": QUALIFICATION_SCHEMA,
        "capability_qualification_ref": "capability-qualification.safe.0001",
        "capability_declaration_ref": owner["capability_declaration_ref"],
        "capability_declaration_digest": owner["capability_declaration_digest"],
        "capability_observation_ref": observed["capability_observation_ref"],
        "capability_observation_digest": observed["capability_observation_digest"],
        "worker_artifact_ref": owner["worker_artifact_ref"],
        "worker_artifact_digest": owner["worker_artifact_digest"],
        "wire_profile_ref": owner["wire_profile_ref"],
        "wire_profile_digest": owner["wire_profile_digest"],
        "phase_basis_ref": "phase-basis.safe.0001",
        "phase_basis_digest": "c" * 64,
        "authority_observation_ref": "authority-observation.safe.0001",
        "authority_observation_digest": "d" * 64,
        "readiness_observation_ref": "readiness-observation.safe.0001",
        "readiness_observation_digest": "e" * 64,
        "host_qualification_ref": "host-qualification.safe.0001",
        "host_qualification_digest": "f" * 64,
        "effect_intent_ref": "effect-intent.safe.0001",
        "effect_fence_ref": "effect-fence.safe.0001",
        "effect_fence_digest": "1" * 64,
        "result": "qualified",
        "reason": "qualified",
        "evaluated_at": "2029-01-01T00:00:00Z",
    }
    identity.update(changes)
    return seal(identity, QUALIFICATION_SCHEMA, "capability_qualification_digest")


CASES = (
    (RW0WorkerMechanismCapabilityDeclarationV1, declaration_mapping,
     DECLARATION_FIELDS, DECLARATION_SCHEMA, 48, 72, 144),
    (RW0WorkerMechanismCapabilityObservationV1, observation_mapping,
     OBSERVATION_FIELDS, OBSERVATION_SCHEMA, 62, 93, 186),
    (RW0WorkerMechanismCapabilityQualificationV1, qualification_mapping,
     QUALIFICATION_FIELDS, QUALIFICATION_SCHEMA, 52, 78, 156),
)


def capability_error(reason: str, action) -> RW0WorkerMechanismCapabilityError:
    with pytest.raises(RW0WorkerMechanismCapabilityError) as caught:
        action()
    assert type(caught.value) is RW0WorkerMechanismCapabilityError
    assert caught.value.reason == reason
    assert type(caught.value.reason) is str
    assert caught.value.args == ()
    assert BaseException.args.__get__(caught.value) == ()
    assert str(caught.value) == repr(caught.value) == "RW0WorkerMechanismCapabilityError"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert BaseException.__cause__.__get__(caught.value) is None
    assert BaseException.__context__.__get__(caught.value) is None
    return caught.value


def test_exact_classes_fields_and_construction_posture() -> None:
    for cls, factory, fields, schema, _, _, _ in CASES:
        mapping = factory()
        assert cls._FIELDS == fields
        assert cls._SCHEMA == schema
        value = cls.from_mapping(mapping)
        assert type(value) is cls
        assert value.to_mapping() == mapping
        assert tuple(value.to_mapping()) == fields
        assert value.to_mapping() is not value.to_mapping()
        assert value.identity_mapping() == {
            name: mapping[name] for name in fields[:-1]
        }
        assert value.canonical_identity_bytes() == canonical(value.identity_mapping())
        assert value.computed_digest() == mapping[fields[-1]]
        assert copy(value) is value
        assert deepcopy(value) is value
        assert str(value) == repr(value) == cls.__name__
        assert value.__hash__ is None
        with pytest.raises(TypeError):
            hash(value)
        with pytest.raises(TypeError):
            cls()
        with pytest.raises(TypeError):
            type("ForbiddenSubclass", (cls,), {})
        with pytest.raises((TypeError, pickle.PicklingError)):
            pickle.dumps(value)
        assert not hasattr(value, "__dict__")
        with pytest.raises(AttributeError):
            value.schema_id = schema
        with pytest.raises(AttributeError):
            del value.schema_id
        with pytest.raises(AttributeError) as missing:
            getattr(value, "private.sentinel.attribute")
        assert "private.sentinel.attribute" not in str(missing.value)

    declaration = RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(
        declaration_mapping())
    observation = RW0WorkerMechanismCapabilityObservationV1.from_mapping(
        observation_mapping())
    assert (declaration == observation) is False
    assert (observation == declaration) is False


def test_public_surfaces_and_equality_always_safely_reconstruct() -> None:
    for cls, factory, fields, _, _, _, _ in CASES:
        mapping = factory()
        left = cls.from_mapping(mapping)
        right = cls.from_mapping(mapping)
        assert left == right
        assert left is not right
        for name in fields:
            assert getattr(left, name) == mapping[name]
        for operation in (
            left.to_mapping, left.identity_mapping, left.canonical_identity_bytes,
            left.computed_digest,
        ):
            assert operation() is not None

        missing = object.__new__(cls)
        for operation in (
            missing.to_mapping, missing.identity_mapping,
            missing.canonical_identity_bytes, missing.computed_digest,
            lambda: getattr(missing, fields[0]), lambda: missing == right,
        ):
            capability_error("invalid_field_type", operation)

        wrong_tuple = object.__new__(cls)
        object.__setattr__(wrong_tuple, "_values", tuple(mapping[name] for name in fields[:-1]))
        capability_error("invalid_length_or_cardinality", wrong_tuple.to_mapping)

        bad_member = object.__new__(cls)
        members = [mapping[name] for name in fields]
        members[1] = True
        object.__setattr__(bad_member, "_values", tuple(members))
        capability_error("invalid_field_type", bad_member.to_mapping)

        resealed = factory(schema_id="not-the-schema")
        invalid = object.__new__(cls)
        object.__setattr__(invalid, "_values", tuple(resealed[name] for name in fields))
        capability_error("invalid_enum", invalid.to_mapping)

        tampered = object.__new__(cls)
        members = [mapping[name] for name in fields]
        members[-1] = "0" * 64
        object.__setattr__(tampered, "_values", tuple(members))
        capability_error("digest_mismatch", tampered.to_mapping)


def test_exact_types_enums_refs_digests_and_time_windows() -> None:
    class StringSubclass(str):
        pass

    class DictSubclass(dict):
        pass

    capability_error(
        "invalid_field_type",
        lambda: RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(
            DictSubclass(declaration_mapping())),
    )
    for replacement in (True, StringSubclass("supported")):
        changed = declaration_mapping(noninteractive_operation=replacement)
        capability_error(
            "invalid_field_type",
            lambda changed=changed: RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(changed),
        )
    for changed in (
        declaration_mapping(declaration_source_kind="observer"),
        declaration_mapping(noninteractive_operation="confirmed"),
    ):
        capability_error(
            "invalid_enum",
            lambda changed=changed: RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(changed),
        )
    for changed in (
        observation_mapping(observation_source_kind="worker_artifact_owner"),
        observation_mapping(noninteractive_operation="supported"),
    ):
        capability_error(
            "invalid_enum",
            lambda changed=changed: RW0WorkerMechanismCapabilityObservationV1.from_mapping(changed),
        )

    valid_pairs = {
        ("qualified", "qualified"),
        ("unknown", "b1_host_qualification_unknown"),
        ("unknown", "capability_unknown"),
        *{
            ("blocked", reason)
            for reason in (
                "b1_binding_mismatch", "b1_host_qualification_blocked",
                "declaration_observation_mismatch", "self_observation",
                "observation_expired", "worker_artifact_mismatch",
                "wire_profile_mismatch", "declaration_unsupported",
                "observation_nonconformant",
            )
        },
    }
    for result, reason in valid_pairs:
        assert RW0WorkerMechanismCapabilityQualificationV1.from_mapping(
            qualification_mapping(result=result, reason=reason))
    for result, reason in (
        ("qualified", "capability_unknown"), ("blocked", "qualified"),
        ("unknown", "observation_expired"),
    ):
        changed = qualification_mapping(result=result, reason=reason)
        capability_error(
            "qualification_reason_mismatch",
            lambda changed=changed: RW0WorkerMechanismCapabilityQualificationV1.from_mapping(changed),
        )
    for changes, expected in (
        ({"result": "maybe", "reason": "qualified"}, "invalid_enum"),
        ({"result": "qualified", "reason": "maybe"}, "invalid_enum"),
    ):
        changed = qualification_mapping(**changes)
        capability_error(
            expected,
            lambda changed=changed: RW0WorkerMechanismCapabilityQualificationV1.from_mapping(changed),
        )

    for timestamp in (
        "2029-01-01T00:00:00", "2029-01-01T00:00:00.0Z",
        "2029-02-29T00:00:00Z", "0000-01-01T00:00:00Z", True,
    ):
        changed = observation_mapping(observed_at=timestamp)
        expected = "invalid_field_type" if timestamp is True else "invalid_timestamp_window"
        capability_error(
            expected,
            lambda changed=changed: RW0WorkerMechanismCapabilityObservationV1.from_mapping(changed),
        )
    for start, end in (
        ("2029-01-01T00:00:00Z", "2029-01-01T00:00:00Z"),
        ("2029-01-02T00:00:00Z", "2029-01-01T00:00:00Z"),
    ):
        changed = observation_mapping(observed_at=start, expires_at=end)
        capability_error(
            "invalid_timestamp_window",
            lambda changed=changed: RW0WorkerMechanismCapabilityObservationV1.from_mapping(changed),
        )

    for cls, factory, fields, _, _, _, _ in CASES:
        for name in fields:
            if name.endswith("_ref"):
                for bad, expected in (
                    ("", "malformed_ref"), ("x" * 97, "malformed_ref"),
                    ("bad_value", "malformed_ref"), ("USER-private", "malformed_ref"),
                    ("192.168.1.1", "privacy_forbidden_material"),
                ):
                    changed = factory(**{name: bad})
                    capability_error(
                        expected,
                        lambda cls=cls, changed=changed: cls.from_mapping(changed),
                    )
            if name.endswith("_digest"):
                for bad in ("A" * 64, "a" * 63, "g" * 64):
                    changed = factory()
                    changed[name] = bad
                    capability_error(
                        "malformed_digest",
                        lambda cls=cls, changed=changed: cls.from_mapping(changed),
                    )


def test_mapping_closure_precedence_is_bounded_and_order_independent() -> None:
    base = declaration_mapping()
    missing = dict(base)
    missing.pop("capability_declaration_ref")
    capability_error(
        "missing_field",
        lambda: RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(missing),
    )
    for key, expected in (
        ("ordinary", "unknown_field"),
        ("hostname_hint", "privacy_forbidden_material"),
        ("", "invalid_length_or_cardinality"),
        ("x" * 40, "invalid_length_or_cardinality"),
        ("é", "invalid_length_or_cardinality"),
    ):
        changed = dict(base)
        changed[key] = "sentinel-private-value"
        capability_error(
            expected,
            lambda changed=changed: RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(changed),
        )

    overlaps = []
    for ordered in (("ordinary", "credential_hint"),
                    ("credential_hint", "ordinary")):
        changed = dict(base)
        changed.pop("capability_declaration_ref")
        for key in ordered:
            changed[key] = "sentinel-private-value"
        overlaps.append(changed)
    for changed in overlaps:
        capability_error(
            "privacy_forbidden_material",
            lambda changed=changed: RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(changed),
        )

    oversized = dict(base)
    oversized[object()] = "never-traversed"
    oversized["secret"] = "never-traversed"
    capability_error(
        "invalid_length_or_cardinality",
        lambda: RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(oversized),
    )
    non_string = dict(base)
    non_string.pop("capability_declaration_ref")
    non_string[1] = "bad"
    capability_error(
        "invalid_field_type",
        lambda: RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(non_string),
    )
    # Accepted names are recognized before their stdout/stderr/credential/session fragments.
    assert RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(base)


def _budget_case(monkeypatch: pytest.MonkeyPatch, expected: int, action) -> None:
    original = capability._WorkBudget
    instances = []

    class Measured(original):
        def __init__(self, limit: int) -> None:
            assert limit == expected
            super().__init__(limit)
            instances.append(self)

    monkeypatch.setattr(capability, "_WorkBudget", Measured)
    try:
        assert action() is not None
        assert len(instances) == 1
        assert instances[0].remaining == 0

        class OneUnder(original):
            def __init__(self, limit: int) -> None:
                assert limit == expected
                super().__init__(limit - 1)

        monkeypatch.setattr(capability, "_WorkBudget", OneUnder)
        capability_error("cumulative_work_exhausted", action)
    finally:
        monkeypatch.setattr(capability, "_WorkBudget", original)


def test_exact_work_budgets_cycles_private_bytes_and_repeated_aliases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for cls, factory, _, _, construction, reconstruction, equality in CASES:
        mapping = factory()
        _budget_case(monkeypatch, construction, lambda cls=cls, mapping=mapping: cls.from_mapping(mapping))
        value = cls.from_mapping(mapping)
        _budget_case(monkeypatch, reconstruction, value.to_mapping)
        peer = cls.from_mapping(mapping)
        _budget_case(monkeypatch, equality, lambda value=value, peer=peer: value == peer)

    cycle: list[object] = []
    cycle.append(cycle)
    changed = declaration_mapping()
    changed["noninteractive_operation"] = cycle
    capability_error(
        "graph_cycle",
        lambda: RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(changed),
    )
    for private in (b"secret", bytearray(b"secret"), memoryview(b"secret")):
        changed = declaration_mapping()
        changed["noninteractive_operation"] = private
        capability_error(
            "privacy_forbidden_material",
            lambda changed=changed: RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(changed),
        )
    shared = ["supported"]
    changed = declaration_mapping()
    changed["noninteractive_operation"] = shared
    changed["wire_command_input_only"] = shared
    capability_error(
        "invalid_field_type",
        lambda: RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(changed),
    )


def test_error_is_sealed_content_free_and_drops_hostile_traceback_locals() -> None:
    sentinel = "SENTINEL-HOSTILE-CAPABILITY-PAYLOAD"
    payload = declaration_mapping(capability_declaration_ref=sentinel + "_")
    error = capability_error(
        "malformed_ref",
        lambda: RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(payload),
    )
    assert not hasattr(error, "field_path")
    with pytest.raises(AttributeError):
        error.reason = "unknown_field"
    with pytest.raises(AttributeError):
        error.extra = sentinel
    with pytest.raises(TypeError):
        type("ForbiddenCapabilityError", (RW0WorkerMechanismCapabilityError,), {})
    with pytest.raises(TypeError):
        RW0WorkerMechanismCapabilityError(object(), "malformed_ref")
    with pytest.raises((TypeError, pickle.PicklingError)):
        pickle.dumps(error)
    frame = error.__traceback__
    while frame is not None:
        if frame.tb_frame.f_code.co_filename.endswith(
            "_rw0_worker_mechanism_capability_values.py"
        ):
            assert sentinel not in repr(frame.tb_frame.f_locals)
        frame = frame.tb_next


def test_error_hides_ordinary_instance_dictionary_and_ignores_reflective_state() -> None:
    error = capability_error(
        "malformed_ref",
        lambda: RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(
            declaration_mapping(capability_declaration_ref="not/a/ref")
        ),
    )
    with pytest.raises(AttributeError):
        error.__dict__
    with pytest.raises(AttributeError):
        object.__getattribute__(error, "__dict__")

    expected = (
        "malformed_ref",
        "malformed_ref",
        (),
        None,
        None,
    )
    ordinary_mutations = (
        ("reason", "unknown_field"),
        ("_reason", "unknown_field"),
        ("args", ("hostile-payload",)),
        ("__cause__", RuntimeError("hostile-payload")),
        ("__context__", RuntimeError("hostile-payload")),
    )
    for name, value in ordinary_mutations:
        with pytest.raises(AttributeError):
            setattr(error, name, value)
        assert (
            error.reason,
            error._reason,
            error.args,
            error.__cause__,
            error.__context__,
        ) == expected

    reference = weakref.ref(error)
    assert reference() is error
    registry = capability._CAPABILITY_ERROR_REASON_BY_INSTANCE
    assert isinstance(registry, weakref.WeakKeyDictionary)
    assert registry[error] == "malformed_ref"
    assert str(error) == repr(error) == "RW0WorkerMechanismCapabilityError"

    reflected = capability_error(
        "invalid_enum",
        lambda: capability._raise_public("invalid_enum"),
    )
    BaseException.args.__set__(reflected, ("externally-written",))
    assert BaseException.args.__get__(reflected) == ("externally-written",)
    assert reflected.args == ("externally-written",)
    assert reflected.reason == reflected._reason == "invalid_enum"
    BaseException.args.__set__(reflected, ())

    gc.collect()
    initial = len(registry)
    ephemeral = RW0WorkerMechanismCapabilityError(
        capability._ERROR_TOKEN, "invalid_enum"
    )
    ephemeral_ref = weakref.ref(ephemeral)
    assert registry[ephemeral] == "invalid_enum"
    assert len(registry) == initial + 1
    del ephemeral
    gc.collect()
    assert ephemeral_ref() is None
    assert len(registry) == initial


@pytest.mark.parametrize("canonical_reason", capability._ERROR_REASONS)
def test_every_finite_error_reason_has_canonical_empty_inherited_state(
    canonical_reason: str,
) -> None:
    assert tuple(capability._ERROR_REASON_BY_TEXT) == capability._ERROR_REASONS
    module_canonical_reason = capability._ERROR_REASON_BY_TEXT[canonical_reason]
    assert module_canonical_reason is canonical_reason
    caller_reason = "".join((canonical_reason[:-1], canonical_reason[-1:]))
    assert type(caller_reason) is str
    assert caller_reason == canonical_reason
    assert caller_reason is not module_canonical_reason

    error = capability_error(
        canonical_reason,
        lambda: capability._raise_public(caller_reason),
    )
    registry = capability._CAPABILITY_ERROR_REASON_BY_INSTANCE
    assert error.reason is module_canonical_reason
    assert error._reason is module_canonical_reason
    assert registry[error] is module_canonical_reason
    assert registry[error] is not caller_reason
    assert BaseException.args.__get__(error) == ()
    assert BaseException.__cause__.__get__(error) is None
    assert BaseException.__context__.__get__(error) is None


def test_caller_value_retention_mutant_is_rejected_by_finite_reason_oracle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = capability._canonical_error_reason

    def retain_caller_value(reason: object) -> str:
        original(reason)
        assert type(reason) is str
        return reason

    monkeypatch.setattr(
        capability, "_canonical_error_reason", retain_caller_value
    )
    with pytest.raises(AssertionError):
        test_every_finite_error_reason_has_canonical_empty_inherited_state(
            "invalid_enum"
        )


def test_error_factory_rejects_nonexact_reasons_before_registry_use() -> None:
    registry = capability._CAPABILITY_ERROR_REASON_BY_INSTANCE
    before = tuple(registry.values())

    class EqualReason:
        def __init__(self) -> None:
            self.equality_calls = 0
            self.hash_calls = 0

        def __eq__(self, other: object) -> bool:
            self.equality_calls += 1
            return other == "invalid_enum"

        def __hash__(self) -> int:
            self.hash_calls += 1
            return hash("invalid_enum")

    class ReasonSubclass(str):
        pass

    hostile = EqualReason()
    with pytest.raises(TypeError, match="sealed error"):
        capability._raise_public(hostile)  # type: ignore[arg-type]
    assert hostile.equality_calls == hostile.hash_calls == 0
    assert tuple(registry.values()) == before

    with pytest.raises(TypeError, match="sealed error"):
        capability._raise_public(ReasonSubclass("invalid_enum"))
    assert tuple(registry.values()) == before

    with pytest.raises(TypeError, match="sealed error"):
        capability._raise_public("not-a-capability-error-reason")
    assert tuple(registry.values()) == before


def test_direct_error_emission_has_actual_empty_base_exception_state() -> None:
    try:
        capability._raise_public("malformed_ref")
    except RW0WorkerMechanismCapabilityError as error:
        assert type(error) is RW0WorkerMechanismCapabilityError
        assert BaseException.args.__get__(error) == ()
        assert BaseException.__cause__.__get__(error) is None
        assert BaseException.__context__.__get__(error) is None
        assert error.__suppress_context__ is True
    else:
        raise AssertionError("Capability error was not emitted")


def test_active_exception_context_is_interpreter_owned_and_not_masked() -> None:
    try:
        raise LookupError("outside-capability")
    except LookupError as active:
        try:
            capability._raise_public("invalid_enum")
        except RW0WorkerMechanismCapabilityError as invoked:
            assert BaseException.__cause__.__get__(invoked) is None
            assert BaseException.__context__.__get__(invoked) is active
            assert invoked.__context__ is active
            assert invoked.__suppress_context__ is True

    direct = capability_error(
        "malformed_ref", lambda: capability._raise_public("malformed_ref")
    )
    try:
        raise RuntimeError("outside-capability")
    except RuntimeError as active:
        try:
            raise direct
        except RW0WorkerMechanismCapabilityError as reraised:
            assert reraised is direct
            assert BaseException.__context__.__get__(reraised) is active
            assert reraised.__context__ is active
            assert reraised.reason == "malformed_ref"


def test_error_registry_is_identity_based_weak_and_payload_free() -> None:
    registry = capability._CAPABILITY_ERROR_REASON_BY_INSTANCE
    first = capability_error(
        "invalid_enum", lambda: capability._raise_public("invalid_enum")
    )
    second = capability_error(
        "malformed_ref", lambda: capability._raise_public("malformed_ref")
    )
    assert first is not second
    assert first != second
    assert hash(first) == object.__hash__(first)
    assert hash(second) == object.__hash__(second)
    assert len({first, second}) == 2
    assert registry[first] == "invalid_enum"
    assert registry[second] == "malformed_ref"
    assert all(
        type(stored) is str and stored in capability._ERROR_REASONS
        for stored in registry.values()
    )
    for error in (first, second):
        with pytest.raises(TypeError):
            copy(error)
        with pytest.raises(TypeError):
            deepcopy(error)
        with pytest.raises((TypeError, pickle.PicklingError)):
            pickle.dumps(error)


@pytest.mark.parametrize("field", ("session", "session_handle"))
def test_generic_session_unknown_fields_are_private(field: str) -> None:
    mapping = declaration_mapping()
    mapping[field] = "private-session-material"
    capability_error(
        "privacy_forbidden_material",
        lambda: RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(mapping),
    )
    assert RW0WorkerMechanismCapabilityDeclarationV1.from_mapping(
        declaration_mapping(external_session_non_authority="supported")
    )
