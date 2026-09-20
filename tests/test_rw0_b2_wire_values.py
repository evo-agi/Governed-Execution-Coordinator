from __future__ import annotations

import hashlib
import json
import pickle
from copy import deepcopy

import pytest

import ge_nwp_coordinator._rw0_wire_protocol_values as wire
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1, CeilingsV1, DeliveryEnvelopeV1, EffectFenceV1,
    WorkerCommandV1, WorkerObservationV1,
)
from ge_nwp_coordinator._rw0_wire_protocol_values import (
    RW0WireCancellationRequestObservationV1, RW0WireProcessObservationV1,
    RW0WireProcessResultClassificationV1, RW0WireProtocolError,
    RW0WireWorkerResultV1, wire_profile_mapping,
)
from tests.c2a_contract_support import _delivery_for_vector, _effect_fence_for_vector, _full_record

REQUEST_FIELDS = (
    "schema_id", "request_observation_ref", "source_kind", "source_ref",
    "source_invocation_ref", "evidence_ref", "evidence_digest", "program_ref",
    "program_version_ref", "accepted_intent_revision_ref", "work_item_ref",
    "work_item_revision_ref", "semantic_attempt_ref", "candidate_ref",
    "command_ref", "command_digest", "attempt_fence_ref", "attempt_fence_digest",
    "cancellation_effect_intent_ref", "cancellation_effect_fence_ref",
    "cancellation_effect_fence_digest", "cancellation_delivery_attempt_ref",
    "cancellation_delivery_envelope_digest", "target_effect_intent_ref",
    "target_effect_fence_ref", "target_effect_fence_digest",
    "target_delivery_attempt_ref", "target_delivery_envelope_digest",
    "observed_at", "request_observation_digest",
)
PROCESS_FIELDS = (
    "schema_id", "process_observation_ref", "source_kind", "source_ref",
    "source_invocation_ref", "evidence_ref", "evidence_digest", "event_kind",
    "program_ref", "program_version_ref", "accepted_intent_revision_ref",
    "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
    "candidate_ref", "command_ref", "command_digest", "attempt_fence_ref",
    "attempt_fence_digest", "effect_intent_ref", "effect_fence_ref",
    "effect_fence_digest", "delivery_attempt_ref", "delivery_envelope_digest",
    "observed_at", "process_observation_digest",
)
REQUEST_SCHEMA = "governed-execution.nwp-rw0-wire-cancellation-request-observation.v1"
PROCESS_SCHEMA = "governed-execution.nwp-rw0-wire-process-observation.v1"
PROFILE_SCHEMA = "governed-execution.nwp-rw0-wire-protocol-profile.v1"
PROFILE_DIGEST = "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454"
MAX_SOURCE_MAPPING_KEY_CHARS = 37
PRIVATE_FRAGMENTS = (
    "hostname", "host_key", "ip_address", "endpoint", "username", "bearer",
    "token", "secret", "signature", "trust_root", "prompt", "transcript",
    "stdout", "stderr", "provider", "environment_value", "absolute_path",
    "workspace_path", "store_path",
)
C2A_FIELD_INVENTORIES = {
    CeilingsV1: (
        "max_active_invocations", "max_candidate_bytes", "max_changed_files",
        "max_cost_microusd", "max_cpu_seconds", "max_deliveries",
        "max_deployments", "max_local_commits", "max_memory_bytes",
        "max_merges", "max_model_input_tokens", "max_model_output_tokens",
        "max_pull_requests", "max_pushes", "max_wall_seconds",
    ),
    AttemptFenceV1: (
        "schema_id", "attempt_fence_ref", "parent_standing_grant_ref",
        "parent_standing_grant_digest", "attempt_authorization_ref",
        "attempt_authorization_digest", "program_ref", "program_version_ref",
        "accepted_intent_revision_ref", "work_item_ref",
        "work_item_revision_ref", "semantic_attempt_ref", "repository_ref",
        "base_git_object_format", "base_git_oid", "path_ceiling",
        "allowed_effect_classes", "aggregate_ceilings", "expires_at",
        "global_stop_ref", "global_stop_version", "attempt_fence_digest",
    ),
    EffectFenceV1: (
        "schema_id", "effect_fence_ref", "parent_standing_grant_ref",
        "parent_standing_grant_digest", "effect_authorization_ref",
        "effect_authorization_digest", "attempt_fence_ref",
        "attempt_fence_digest", "program_ref", "program_version_ref",
        "accepted_intent_revision_ref", "work_item_ref",
        "work_item_revision_ref", "semantic_attempt_ref", "effect_intent_ref",
        "effect_class", "command_ref", "command_digest", "candidate_ref",
        "repository_ref", "base_git_object_format", "base_git_oid",
        "path_ceiling", "effect_ceilings", "expires_at", "global_stop_ref",
        "global_stop_version", "portable_capsule_digest",
        "cancellation_target_effect_intent_ref",
        "cancellation_target_effect_fence_ref",
        "cancellation_target_effect_fence_digest", "effect_fence_digest",
    ),
    WorkerCommandV1: (
        "schema_id", "command_ref", "program_ref", "program_version_ref",
        "accepted_intent_revision_ref", "work_item_ref",
        "work_item_revision_ref", "semantic_attempt_ref", "effect_intent_ref",
        "effect_class", "candidate_ref", "repository_ref",
        "base_git_object_format", "base_git_oid", "path_ceiling",
        "work_spec_ref", "work_spec_digest", "standing_grant_ref",
        "standing_grant_digest", "attempt_authorization_ref",
        "attempt_authorization_digest", "effect_authorization_ref",
        "effect_authorization_digest", "attempt_fence_ref",
        "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest",
        "global_stop_ref", "global_stop_version", "validation_requirement_ref",
        "validation_requirement_digest", "review_requirement_ref",
        "review_requirement_digest", "capsule_schema_id",
        "capsule_profile_ref", "effect_ceilings", "privacy_classification",
        "redaction_profile_ref", "command_digest",
    ),
    DeliveryEnvelopeV1: (
        "schema_id", "delivery_attempt_ref", "program_ref",
        "program_version_ref", "command_ref", "command_digest",
        "semantic_attempt_ref", "effect_intent_ref", "attempt_fence_ref",
        "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest",
        "adapter_kind", "adapter_safe_correlation_ref",
        "delivery_envelope_digest",
    ),
    WorkerObservationV1: (
        "schema_id", "observation_ref", "source_kind", "source_ref",
        "source_invocation_ref", "delivery_attempt_ref", "program_ref",
        "program_version_ref", "accepted_intent_revision_ref", "work_item_ref",
        "work_item_revision_ref", "semantic_attempt_ref", "effect_intent_ref",
        "command_ref", "command_digest", "attempt_fence_ref",
        "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest",
        "observation_kind", "outcome", "reason_code", "evidence_refs",
        "observed_at", "candidate_ref", "capsule_manifest_ref",
        "portable_capsule_digest", "process_exit_code", "observation_digest",
    ),
}


def canonical(mapping: dict[str, object]) -> bytes:
    return json.dumps(mapping, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode()


def seal(mapping: dict[str, object], domain: str, final: str) -> dict[str, object]:
    result = deepcopy(mapping)
    identity = {key: value for key, value in result.items() if key != final}
    result[final] = hashlib.sha256(domain.encode() + b"\0" + canonical(identity)).hexdigest()
    return result


def graph() -> tuple[WorkerCommandV1, AttemptFenceV1, EffectFenceV1, DeliveryEnvelopeV1,
                     EffectFenceV1, DeliveryEnvelopeV1]:
    command = WorkerCommandV1.from_mapping(_full_record("WorkerCommandV1"))
    attempt = AttemptFenceV1.from_mapping(_full_record("AttemptFenceV1"))
    author = EffectFenceV1.from_mapping(_effect_fence_for_vector("author"))
    delivery = DeliveryEnvelopeV1.from_mapping(_delivery_for_vector("author"))
    cancel = EffectFenceV1.from_mapping(_effect_fence_for_vector("cancellation"))
    cancel_delivery = DeliveryEnvelopeV1.from_mapping(_delivery_for_vector("cancellation"))
    return command, attempt, author, delivery, cancel, cancel_delivery


def worker_observation(kind: str, ref: str) -> WorkerObservationV1:
    command, attempt, author, delivery, _, _ = graph()
    outcomes = {"worker_started": "started", "candidate_captured": "captured",
                "worker_completed": "completed"}
    return WorkerObservationV1.create(
        observation_ref=ref, source_kind="worker", source_ref="worker.safe.0001",
        source_invocation_ref="invocation.safe.0001", observation_kind=kind,
        outcome=outcomes[kind], reason_code="reason.none",
        evidence_refs=["evidence.safe.0001"], observed_at="2026-08-08T18:00:00Z",
        delivery=delivery, author_command=command, attempt_fence=attempt,
        author_effect_fence=author, effect_fence=author)


def adapter_observation(kind: str, ref: str, exit_code: int | None = None) -> WorkerObservationV1:
    command, attempt, author, delivery, cancel, cancel_delivery = graph()
    response = kind in ("cancellation_acknowledged", "cancellation_rejected")
    outcomes = {"cancellation_acknowledged": "acknowledged",
                "cancellation_rejected": "rejected", "deadline_elapsed": "elapsed",
                "process_exited": "exited"}
    extra: dict[str, object] = {"cancellation_target": author} if response else {}
    if exit_code is not None:
        extra["process_exit_code"] = exit_code
    return WorkerObservationV1.create(
        observation_ref=ref, source_kind="direct_local_adapter",
        source_ref="adapter.safe.0001", source_invocation_ref="adapter.invocation.safe.0001",
        observation_kind=kind, outcome=outcomes[kind], reason_code="reason.none",
        evidence_refs=["evidence.safe.0002"], observed_at="2026-08-08T18:00:01Z",
        delivery=cancel_delivery if response else delivery,
        author_command=command, attempt_fence=attempt,
        author_effect_fence=author, effect_fence=cancel if response else author,
        **extra)


def request_mapping(source_kind: str = "supervisor") -> dict[str, object]:
    command, attempt, author, delivery, cancel, cancel_delivery = graph()
    identity: dict[str, object] = {
        "schema_id": REQUEST_SCHEMA,
        "request_observation_ref": "request.observation.safe.0001",
        "source_kind": source_kind, "source_ref": "supervisor.safe.0001",
        "source_invocation_ref": "supervisor.invocation.safe.0001",
        "evidence_ref": "evidence.request.safe.0001", "evidence_digest": "a" * 64,
        "program_ref": command.program_ref,
        "program_version_ref": command.program_version_ref,
        "accepted_intent_revision_ref": command.accepted_intent_revision_ref,
        "work_item_ref": command.work_item_ref,
        "work_item_revision_ref": command.work_item_revision_ref,
        "semantic_attempt_ref": command.semantic_attempt_ref,
        "candidate_ref": command.candidate_ref, "command_ref": command.command_ref,
        "command_digest": command.command_digest,
        "attempt_fence_ref": attempt.attempt_fence_ref,
        "attempt_fence_digest": attempt.attempt_fence_digest,
        "cancellation_effect_intent_ref": cancel.effect_intent_ref,
        "cancellation_effect_fence_ref": cancel.effect_fence_ref,
        "cancellation_effect_fence_digest": cancel.effect_fence_digest,
        "cancellation_delivery_attempt_ref": cancel_delivery.delivery_attempt_ref,
        "cancellation_delivery_envelope_digest": cancel_delivery.delivery_envelope_digest,
        "target_effect_intent_ref": author.effect_intent_ref,
        "target_effect_fence_ref": author.effect_fence_ref,
        "target_effect_fence_digest": author.effect_fence_digest,
        "target_delivery_attempt_ref": delivery.delivery_attempt_ref,
        "target_delivery_envelope_digest": delivery.delivery_envelope_digest,
        "observed_at": "2026-08-08T18:00:01Z",
    }
    return seal(identity, REQUEST_SCHEMA + ".identity", "request_observation_digest")


def process_mapping(kind: str = "signal_delivered", source: str = "supervisor") -> dict[str, object]:
    command, attempt, author, delivery, _, _ = graph()
    identity: dict[str, object] = {
        "schema_id": PROCESS_SCHEMA,
        "process_observation_ref": "process.observation.safe.0001",
        "source_kind": source, "source_ref": "supervisor.safe.0001",
        "source_invocation_ref": "supervisor.invocation.safe.0001",
        "evidence_ref": "evidence.process.safe.0001", "evidence_digest": "b" * 64,
        "event_kind": kind,
        "program_ref": command.program_ref,
        "program_version_ref": command.program_version_ref,
        "accepted_intent_revision_ref": command.accepted_intent_revision_ref,
        "work_item_ref": command.work_item_ref,
        "work_item_revision_ref": command.work_item_revision_ref,
        "semantic_attempt_ref": command.semantic_attempt_ref,
        "candidate_ref": command.candidate_ref, "command_ref": command.command_ref,
        "command_digest": command.command_digest,
        "attempt_fence_ref": attempt.attempt_fence_ref,
        "attempt_fence_digest": attempt.attempt_fence_digest,
        "effect_intent_ref": author.effect_intent_ref,
        "effect_fence_ref": author.effect_fence_ref,
        "effect_fence_digest": author.effect_fence_digest,
        "delivery_attempt_ref": delivery.delivery_attempt_ref,
        "delivery_envelope_digest": delivery.delivery_envelope_digest,
        "observed_at": "2026-08-08T18:00:01Z",
    }
    return seal(identity, PROCESS_SCHEMA + ".identity", "process_observation_digest")


def test_value_fields_digests_and_safe_projection() -> None:
    assert RW0WireCancellationRequestObservationV1._FIELDS == REQUEST_FIELDS
    assert RW0WireProcessObservationV1._FIELDS == PROCESS_FIELDS
    for cls, mapping, final in (
        (RW0WireCancellationRequestObservationV1, request_mapping(), "request_observation_digest"),
        (RW0WireProcessObservationV1, process_mapping(), "process_observation_digest"),
    ):
        value = cls.from_mapping(mapping)
        assert value.to_mapping() == mapping
        assert value.to_mapping() is not value.to_mapping()
        assert value.identity_mapping() == {key: item for key, item in mapping.items() if key != final}
        assert value.canonical_identity_bytes() == canonical(value.identity_mapping())
        assert value.computed_digest() == mapping[final]
        assert str(value) == repr(value) == cls.__name__
        with pytest.raises(AttributeError):
            value.source_ref = "changed"
        with pytest.raises((TypeError, pickle.PicklingError)):
            pickle.dumps(value)


@pytest.mark.parametrize("cls,mapping,final,domain", (
    (RW0WireCancellationRequestObservationV1, request_mapping, "request_observation_digest", REQUEST_SCHEMA + ".identity"),
    (RW0WireProcessObservationV1, process_mapping, "process_observation_digest", PROCESS_SCHEMA + ".identity"),
))
def test_private_unknown_missing_digest_ipv4_and_types(cls, mapping, final, domain) -> None:
    valid = mapping()
    for key, reason in (("hostname", "privacy_forbidden_material"),
                        ("host_key_hint", "privacy_forbidden_material"),
                        ("unexpected", "unknown_field")):
        changed = dict(valid); changed[key] = "safe"
        with pytest.raises(RW0WireProtocolError) as caught:
            cls.from_mapping(changed)
        assert caught.value.reason == reason
        assert str(caught.value) == "RW0WireProtocolError"
    changed = dict(valid); changed.pop("source_ref")
    with pytest.raises(RW0WireProtocolError) as caught:
        cls.from_mapping(changed)
    assert caught.value.reason == "missing_field"
    changed = dict(valid); changed[final] = "0" * 64
    with pytest.raises(RW0WireProtocolError) as caught:
        cls.from_mapping(changed)
    assert caught.value.reason == "digest_mismatch"
    for ref_field in ("source_ref", "source_invocation_ref", "evidence_ref"):
        changed = seal({**valid, ref_field: "192.168.1.1"}, domain, final)
        with pytest.raises(RW0WireProtocolError) as caught:
            cls.from_mapping(changed)
        assert caught.value.reason == "privacy_forbidden_material"
    with pytest.raises(RW0WireProtocolError) as caught:
        cls.from_mapping({**valid, **{f"x{i}": i for i in range(len(cls._FIELDS) + 2)}})
    assert caught.value.reason == "invalid_length_or_cardinality"


def test_worker_result_and_classification_closed_values() -> None:
    started = worker_observation("worker_started", "observation.worker.started.0001")
    captured = worker_observation("candidate_captured", "observation.worker.captured.0001")
    completed = worker_observation("worker_completed", "observation.worker.completed.0001")
    value = RW0WireWorkerResultV1._create((started, captured, completed))
    assert value.observations == (started, captured, completed)
    assert [x["observation_kind"] for x in value.to_mapping()["observations"]] == [
        "worker_started", "candidate_captured", "worker_completed"]
    assert RW0WireWorkerResultV1._create((started, completed)).observations == (
        started, completed)
    with pytest.raises(RW0WireProtocolError):
        RW0WireWorkerResultV1._create((completed, started))
    with pytest.raises(RW0WireProtocolError):
        RW0WireWorkerResultV1._create([started, completed])
    usable = RW0WireProcessResultClassificationV1._create("usable", "usable")
    assert usable.to_mapping() == {"classification": "usable", "reason": "usable"}
    for closed in (value, usable):
        with pytest.raises((TypeError, pickle.PicklingError)):
            pickle.dumps(closed)
    with pytest.raises(RW0WireProtocolError):
        RW0WireProcessResultClassificationV1._create("usable", "process_failed")


def test_all_wire_values_disable_ordinary_construction_and_bypass_fails_closed() -> None:
    started = worker_observation("worker_started", "observation.construct.started.0001")
    completed = worker_observation("worker_completed", "observation.construct.completed.0001")
    ordinary_calls = (
        lambda: RW0WireCancellationRequestObservationV1(),
        lambda: RW0WireProcessObservationV1(),
        lambda: RW0WireWorkerResultV1((started, completed)),
        lambda: RW0WireProcessResultClassificationV1("usable", "usable"),
    )
    for call in ordinary_calls:
        with pytest.raises(TypeError, match="construction disabled"):
            call()

    for cls in (
        RW0WireCancellationRequestObservationV1,
        RW0WireProcessObservationV1,
        RW0WireWorkerResultV1,
        RW0WireProcessResultClassificationV1,
    ):
        with pytest.raises(TypeError, match="subclassing disabled"):
            type("ForbiddenWireSubclass", (cls,), {})
        bypass = object.__new__(cls)
        with pytest.raises(RW0WireProtocolError) as caught:
            bypass.to_mapping()
        assert caught.value.reason == "invalid_field_value"
        assert caught.value.__cause__ is None
        assert caught.value.__context__ is None
        assert str(caught.value) == repr(caught.value) == "RW0WireProtocolError"


def test_safe_c2a_extractor_inventories_and_valid_values_are_literal_and_bounded() -> None:
    command, attempt, author, delivery, _, _ = graph()
    observation = worker_observation(
        "worker_completed", "observation.extractor.completed.0001")
    examples = {
        CeilingsV1: command.effect_ceilings,
        AttemptFenceV1: attempt,
        EffectFenceV1: author,
        WorkerCommandV1: command,
        DeliveryEnvelopeV1: delivery,
        WorkerObservationV1: observation,
    }
    maximum_inspections = {
        CeilingsV1: 15,
        AttemptFenceV1: 45,
        EffectFenceV1: 50,
        WorkerCommandV1: 57,
        DeliveryEnvelopeV1: 15,
        WorkerObservationV1: 61,
    }
    assert wire._C2A_FIELD_INVENTORIES == C2A_FIELD_INVENTORIES
    for cls, fields in C2A_FIELD_INVENTORIES.items():
        assert tuple(cls._FIELDS) == fields
        with pytest.raises(TypeError, match="subclassing disabled"):
            type("ForbiddenC2ASubclass", (cls,), {})
        extracted = wire._safe_c2a_extract(examples[cls], cls)
        assert extracted.mapping == examples[cls].to_mapping()
        assert extracted.inspections <= maximum_inspections[cls]


def test_self_digest_public_methods_revalidate_incomplete_and_tampered_state() -> None:
    methods = (
        "to_mapping", "identity_mapping", "canonical_identity_bytes",
        "computed_digest",
    )
    for cls, factory, digest_slot in (
        (RW0WireCancellationRequestObservationV1, request_mapping,
         "_request_observation_digest"),
        (RW0WireProcessObservationV1, process_mapping,
         "_process_observation_digest"),
    ):
        incomplete = object.__new__(cls)
        valid = cls.from_mapping(factory())
        object.__setattr__(valid, digest_slot, "0" * 64)
        for value in (incomplete, valid):
            for method in methods:
                with pytest.raises(RW0WireProtocolError) as caught:
                    getattr(value, method)()
                assert caught.value.reason == "invalid_field_value"
                assert caught.value.args == ("RW0WireProtocolError",)
                assert caught.value.__cause__ is None
                assert caught.value.__context__ is None
                assert str(caught.value) == repr(caught.value) == (
                    "RW0WireProtocolError"
                )


@pytest.mark.parametrize("cls,mapping", (
    (RW0WireCancellationRequestObservationV1, request_mapping),
    (RW0WireProcessObservationV1, process_mapping),
))
def test_source_mapping_key_bound_and_privacy_precedence(cls, mapping) -> None:
    assert max(map(len, REQUEST_FIELDS + PROCESS_FIELDS + PRIVATE_FRAGMENTS)) == (
        MAX_SOURCE_MAPPING_KEY_CHARS
    )
    valid = mapping()
    bounded_unknown = "x" * MAX_SOURCE_MAPPING_KEY_CHARS
    changed = dict(valid); changed[bounded_unknown] = "safe"
    with pytest.raises(RW0WireProtocolError) as caught:
        cls.from_mapping(changed)
    assert caught.value.reason == "unknown_field"

    oversized_unknown = "x" * (MAX_SOURCE_MAPPING_KEY_CHARS + 1)
    changed = dict(valid); changed[oversized_unknown] = "safe"
    with pytest.raises(RW0WireProtocolError) as caught:
        cls.from_mapping(changed)
    assert caught.value.reason == "invalid_length_or_cardinality"

    bounded_private = "hostname" + "x" * (
        MAX_SOURCE_MAPPING_KEY_CHARS - len("hostname")
    )
    changed = dict(valid); changed[bounded_private] = "safe"
    with pytest.raises(RW0WireProtocolError) as caught:
        cls.from_mapping(changed)
    assert caught.value.reason == "privacy_forbidden_material"

    oversized_private = bounded_private + "x"
    changed = dict(valid); changed[oversized_private] = "safe"
    with pytest.raises(RW0WireProtocolError) as caught:
        cls.from_mapping(changed)
    assert caught.value.reason == "invalid_length_or_cardinality"


def test_every_private_fragment_and_b2_ref_field_is_owned_by_tests() -> None:
    for cls, factory, fields, final, domain in (
        (RW0WireCancellationRequestObservationV1, request_mapping, REQUEST_FIELDS,
         "request_observation_digest", REQUEST_SCHEMA + ".identity"),
        (RW0WireProcessObservationV1, process_mapping, PROCESS_FIELDS,
         "process_observation_digest", PROCESS_SCHEMA + ".identity"),
    ):
        valid = factory()
        for fragment in PRIVATE_FRAGMENTS:
            changed = dict(valid); changed[fragment] = "safe"
            with pytest.raises(RW0WireProtocolError) as caught:
                cls.from_mapping(changed)
            assert caught.value.reason == "privacy_forbidden_material"
        for field in (name for name in fields if name.endswith("_ref")):
            changed = seal({**valid, field: "192.168.1.1"}, domain, final)
            with pytest.raises(RW0WireProtocolError) as caught:
                cls.from_mapping(changed)
            assert caught.value.reason == "privacy_forbidden_material"


def test_fixed_profile_identity_and_freshness() -> None:
    profile = wire_profile_mapping()
    assert tuple(profile) == ("schema_id", "profile_ref", "manifest", "profile_digest")
    assert profile["schema_id"] == PROFILE_SCHEMA
    assert profile["profile_ref"] == "rw0-wire-nwpf-v1"
    assert profile["profile_digest"] == PROFILE_DIGEST
    identity = {key: value for key, value in profile.items() if key != "profile_digest"}
    assert identity == EXPECTED_PROFILE_IDENTITY
    payload = canonical(identity)
    assert len(payload) == 4021
    assert hashlib.sha256((PROFILE_SCHEMA + ".identity").encode() + b"\0" + payload).hexdigest() == PROFILE_DIGEST
    profile["manifest"]["request"]["source_kinds"].append("adapter")
    assert wire_profile_mapping()["manifest"]["request"]["source_kinds"] == ["supervisor", "execution_substrate"]


EXPECTED_PROFILE_IDENTITY = json.loads('{"manifest":{"authority":{"acceptance":false,"mechanism_neutral":true,"permission":false,"profile_in_frame":false,"provider_neutral":true},"classifier":{"ack_reject_exclusive":true,"adapter_kinds":["cancellation_acknowledged","cancellation_rejected","deadline_elapsed","process_exited"],"classifications":["usable","unusable","invalid"],"exit_success_code":0,"max_adapter_facts":4,"max_process_facts":2,"max_request_facts":1,"max_total_facts":10,"max_worker_result_facts":3,"precedence":[["invalid_input","duplicate_fact","unrelated_fact","conflicting_fact","cancellation_graph_mismatch"],["resource_limit_exceeded"],["deadline_elapsed"],["signal_delivered"],["cancellation_acknowledged","cancellation_rejected","cancellation_request_pending"],["process_result_contradiction","process_failed"],["result_missing","result_invalid"],["process_evidence_incomplete"],["usable"]],"reasons":["usable","invalid_input","unrelated_fact","duplicate_fact","conflicting_fact","cancellation_graph_mismatch","resource_limit_exceeded","deadline_elapsed","signal_delivered","cancellation_request_pending","cancellation_acknowledged","cancellation_rejected","process_result_contradiction","process_failed","result_missing","result_invalid","process_evidence_incomplete"],"response_requires_request":true},"decoder_errors":["invalid_outer_type","short_header","bad_magic","unsupported_version","unsupported_kind","declared_length_over_cap","truncated_payload","trailing_data","invalid_utf8","bom_forbidden","json_token_invalid","duplicate_key","invalid_root_or_scalar","unknown_field","missing_field","nested_record_invalid","noncanonical_payload","relation_mismatch","work_limit_exceeded"],"frame":{"header":[["magic",0,4],["version",4,1],["kind",5,1],["payload_length",6,2]],"kinds":{"command":1,"worker_result":2},"length_encoding":"uint16-big-endian","magic":"NWPF","one_frame":true,"semantic_identity":false,"version":1},"integer":{"json":"unsigned_decimal_no_sign_or_leading_zero","lower_bound":"owning_field","maximum":9223372036854775807,"preconversion_bounded":true,"type":"exact_builtin_int"},"json":{"allow_nan":false,"bom":false,"canonical_reencode_equals_payload":true,"constants":false,"duplicate_keys":false,"ensure_ascii":false,"floats":false,"normalization":"none","separators":[",",":"],"sort_keys":true,"utf8":"strict"},"payloads":{"command":{"max_bytes":5898,"max_containers":5,"max_depth":3,"max_hostile_units":23746,"max_key_pairs":71,"max_scalar_leaves":70,"records":["WorkerCommandV1","DeliveryEnvelopeV1"],"root_keys":["command","delivery"]},"worker_result":{"max_bytes":16627,"max_containers":8,"max_depth":4,"max_hostile_units":66770,"max_key_pairs":77,"max_scalar_leaves":169,"records":["WorkerObservationV1"],"root_keys":["observations"]}},"process":{"digest_domain":"governed-execution.nwp-rw0-wire-process-observation.v1.identity","event_kinds":["resource_limit_exceeded","signal_delivered"],"schema_id":"governed-execution.nwp-rw0-wire-process-observation.v1","source_authenticity":false,"source_kinds":["supervisor","operating_system"]},"request":{"digest_domain":"governed-execution.nwp-rw0-wire-cancellation-request-observation.v1.identity","schema_id":"governed-execution.nwp-rw0-wire-cancellation-request-observation.v1","source_authenticity":false,"source_kinds":["supervisor","execution_substrate"],"target":"author_candidate"},"result":{"graph":"supplied_exact_fences","order":"tuple","same_source_invocation_ref":true,"same_source_ref":true,"sequences":[["worker_started","worker_completed"],["worker_started","candidate_captured","worker_completed"]],"source_kind":"worker","unique_digests":true,"unique_refs":true},"work":{"classifier_fact":1,"container":1,"container_list_member":"container_only","fixed_closed_relations":"unmetered","header_byte":1,"key_pair":1,"payload_byte_per_pass":1,"payload_passes":["utf8_decode","json_tokenize","canonical_reencode","canonical_compare"],"scalar_leaf":1}},"profile_ref":"rw0-wire-nwpf-v1","schema_id":"governed-execution.nwp-rw0-wire-protocol-profile.v1"}')
