from __future__ import annotations

import copy
import hashlib
import json
import pickle

import pytest

import ge_nwp_coordinator._rw0_wire_protocol_values as wire
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1,
    CandidateCapsuleManifestV1,
    DeliveryEnvelopeV1,
    EffectFenceV1,
    WorkerCommandV1,
    WorkerObservationV1,
)
from tests.c2a_contract_support import (
    _delivery_for_vector,
    _effect_fence_for_vector,
    _full_record,
    _reseal_single_digest_record,
)
from tests.test_rw0_b2_wire_values import (
    PROCESS_SCHEMA,
    PROFILE_DIGEST,
    PROFILE_SCHEMA,
    REQUEST_SCHEMA,
    canonical,
    graph as nwpf_graph,
    process_mapping,
    request_mapping,
    seal,
    worker_observation,
)


PROFILE_SCHEMA_V1 = "governed-execution.nwp-rw0-wire-cancellation-control-profile.v1"
PROFILE_REF_V1 = "rw0-wire-cancellation-control-v1"
PROFILE_DOMAIN_V1 = PROFILE_SCHEMA_V1 + ".identity"
PROFILE_DIGEST_V1 = "4d6f84552b852a4c4073b4238591afd271072f648424eca9e744def436165288"
EXPECTED_MANIFEST_JSON = r'''{"authority":{"acceptance":false,"authentication":false,"c1_evidence_member":false,"current_selection":false,"durable":false,"durable_truth":false,"effect_authority":false,"external_contact":false,"io":false,"mechanism_neutral":true,"permission":false,"persistence":false,"process_control":false,"production_caller":false,"profile_in_frame":false,"provider_neutral":true,"public_export":false,"reconciliation":false,"review_result":false,"runtime":false,"semantic_cancellation":false,"source_authenticity":false,"target_result":false,"teardown":false,"terminality":false,"transport":false,"validation_result":false,"worker_result":false},"capsule":{"author_candidate":{"argument":"omitted","cancellation_portable_capsule_digest":"null","target_portable_capsule_digest":"null"},"entries":{"maximum":3,"minimum":3},"review_candidate":{"argument":"exact_CandidateCapsuleManifestV1","cancellation_portable_capsule_digest":"manifest","target_portable_capsule_digest":"manifest"},"validate_candidate":{"argument":"exact_CandidateCapsuleManifestV1","cancellation_portable_capsule_digest":"manifest","target_portable_capsule_digest":"manifest"}},"classifier":{"acknowledgement_rejection_exclusive":true,"classifications":["invalid","incomplete","finite"],"decision_order":[["invalid_input","invalid","invalid_input"],["duplicate_fact","invalid","duplicate_fact"],["unrelated_fact","invalid","unrelated_fact"],["conflicting_fact","invalid","conflicting_fact"],["cancellation_graph_mismatch","invalid","cancellation_graph_mismatch"],["request_absent","incomplete","process_evidence_incomplete"],["cancellation_rejected","finite","cancellation_rejected"],["target_process_exited","finite","target_process_exited"],["resource_limit_exceeded","incomplete","resource_limit_exceeded"],["deadline_elapsed","incomplete","deadline_elapsed"],["signal_delivered","incomplete","signal_delivered"],["cancellation_acknowledged","incomplete","cancellation_acknowledged"],["request_present","incomplete","cancellation_request_pending"]],"exit_code":{"maximum":255,"minimum":-255,"zero_special":false},"matrix":{"finite":["cancellation_rejected","target_process_exited"],"incomplete":["process_evidence_incomplete","resource_limit_exceeded","deadline_elapsed","signal_delivered","cancellation_acknowledged","cancellation_request_pending"],"invalid":["invalid_input","duplicate_fact","unrelated_fact","conflicting_fact","cancellation_graph_mismatch"]},"reasons":["invalid_input","duplicate_fact","unrelated_fact","conflicting_fact","cancellation_graph_mismatch","process_evidence_incomplete","resource_limit_exceeded","deadline_elapsed","signal_delivered","cancellation_acknowledged","cancellation_request_pending","cancellation_rejected","target_process_exited"],"response_requires_request":true,"return_type":"exact_RW0WireCancellationControlClassificationV1","timestamp_ordering":false},"facts":{"absence":"None","adapter_observations":{"maximum":4,"minimum":0,"roles":["cancellation_acknowledged","cancellation_rejected","deadline_elapsed","process_exited"]},"duplicate_detection":{"after_reconstruction":true,"keys":["original_object_identity","safe_fact_ref","safe_fact_digest"],"scope":"all_supplied_facts"},"item_types":{"adapter_observations":"exact_WorkerObservationV1","process_observations":"exact_RW0WireProcessObservationV1"},"observation_items_nullable":false,"outer_types":{"adapter_observations":"exact_builtin_tuple","process_observations":"exact_builtin_tuple","request":"exact_RW0WireCancellationRequestObservationV1_or_None"},"process_observations":{"maximum":2,"minimum":0,"roles":["resource_limit_exceeded","signal_delivered"]},"request":{"maximum":1,"minimum":0},"request_absence":"None","request_bindings":["target_effect_fence","target_delivery","cancellation_effect_fence","cancellation_delivery"],"role_bindings":{"cancellation_acknowledged":["cancellation_effect_fence","cancellation_delivery"],"cancellation_rejected":["cancellation_effect_fence","cancellation_delivery"],"deadline_elapsed":["target_effect_fence","target_delivery"],"process_exited":["target_effect_fence","target_delivery"],"resource_limit_exceeded":["target_effect_fence","target_delivery"],"signal_delivered":["target_effect_fence","target_delivery"]},"role_validation":{"cancellation_acknowledged":["cancellation_response"],"cancellation_rejected":["cancellation_response"],"deadline_elapsed":["target_observation"],"process_exited":["target_observation"],"request":["target_delivery","cancellation_delivery"],"resource_limit_exceeded":["target_delivery"],"signal_delivered":["target_delivery"]},"singleton_maximum":1,"singleton_roles":["request","cancellation_acknowledged","cancellation_rejected","deadline_elapsed","process_exited","resource_limit_exceeded","signal_delivered"],"total_maximum":7},"identity":{"canonical_json":{"allow_nan":false,"ensure_ascii":false,"normalization":"none","separators":[",",":"],"sort_keys":true},"digest":"sha256","domain_separator":"NUL","encoding":"UTF-8"},"relations":{"c2a_call_profiles":{"cancellation_delivery":{"arguments":[["delivery","cancellation_delivery"],["author_command","author_command"],["attempt_fence","attempt_fence"],["author_effect_fence","author_effect_fence"],["effect_fence","cancellation_effect_fence"],["capsule_manifest","target_capsule_manifest_by_target_class"],["cancellation_target","target_effect_fence"]],"call":"validate_delivery_relation"},"cancellation_response":{"arguments":[["observation","response"],["delivery","cancellation_delivery"],["author_command","author_command"],["attempt_fence","attempt_fence"],["author_effect_fence","author_effect_fence"],["effect_fence","cancellation_effect_fence"],["capsule_manifest","target_capsule_manifest_by_target_class"],["before_blobs","omitted"],["after_blobs","omitted"],["cancellation_target","target_effect_fence"]],"call":"validate_observation_relation"},"target_delivery":{"arguments":[["delivery","target_delivery"],["author_command","author_command"],["attempt_fence","attempt_fence"],["author_effect_fence","author_effect_fence"],["effect_fence","target_effect_fence"],["capsule_manifest","target_capsule_manifest_by_target_class"],["cancellation_target","omitted"]],"call":"validate_delivery_relation"},"target_observation":{"arguments":[["observation","adapter_observation"],["delivery","target_delivery"],["author_command","author_command"],["attempt_fence","attempt_fence"],["author_effect_fence","author_effect_fence"],["effect_fence","target_effect_fence"],["capsule_manifest","target_capsule_manifest_by_target_class"],["before_blobs","omitted"],["after_blobs","omitted"],["cancellation_target","omitted"]],"call":"validate_observation_relation"}},"c2a_owner_relations":["validate_delivery_relation","validate_observation_relation"],"classifier":{"name":"classify_wire_exact_current_cancellation_control","operands":["author_command","attempt_fence","author_effect_fence","target_effect_fence","target_delivery","cancellation_effect_fence","cancellation_delivery","request","adapter_observations","process_observations","target_capsule_manifest"],"return_type":"exact_RW0WireCancellationControlClassificationV1"},"ordered_direct_c2a_calls":{"classifier_base":["target_delivery","cancellation_delivery"],"process":["target_delivery"],"request":["target_delivery","cancellation_delivery"],"response":["target_delivery","cancellation_delivery","cancellation_response"]},"process":{"name":"validate_wire_exact_current_process_observation_relation","operands":["observation","author_command","attempt_fence","author_effect_fence","target_effect_fence","target_delivery","target_capsule_manifest"],"return_type":"None"},"request":{"name":"validate_wire_exact_current_cancellation_request_relation","operands":["request","author_command","attempt_fence","author_effect_fence","target_effect_fence","target_delivery","cancellation_effect_fence","cancellation_delivery","target_capsule_manifest"],"return_type":"None"},"response":{"name":"validate_wire_exact_current_cancellation_response_relation","operands":["response","request","author_command","attempt_fence","author_effect_fence","target_effect_fence","target_delivery","cancellation_effect_fence","cancellation_delivery","target_capsule_manifest"],"return_type":"None"},"response_prerequisite":"validate_wire_exact_current_cancellation_request_relation"},"routes":{"adapter_observation_orientation":{"cancellation_acknowledged":{"cancellation_target":"target_effect_fence","delivery":"cancellation_delivery","effect":"cancellation_effect_fence","source_basis":"bound_delivery.adapter_kind"},"cancellation_rejected":{"cancellation_target":"target_effect_fence","delivery":"cancellation_delivery","effect":"cancellation_effect_fence","source_basis":"bound_delivery.adapter_kind"},"deadline_elapsed":{"cancellation_target":"omitted","delivery":"target_delivery","effect":"target_effect_fence","source_basis":"bound_delivery.adapter_kind"},"process_exited":{"cancellation_target":"omitted","delivery":"target_delivery","effect":"target_effect_fence","source_basis":"bound_delivery.adapter_kind"}},"adapter_observation_sources":{"direct_local_bootstrap":"direct_local_adapter","execution_substrate":"es_adapter"},"process_observation_orientation":{"resource_limit_exceeded":{"delivery":"target_delivery","effect":"target_effect_fence","source_basis":"closed_process_source_kind"},"signal_delivered":{"delivery":"target_delivery","effect":"target_effect_fence","source_basis":"closed_process_source_kind"}},"process_sources":["supervisor","operating_system"],"request_orientation":{"cancellation_delivery":"cancellation_delivery","cancellation_effect":"cancellation_effect_fence","source_basis":"cancellation_delivery.adapter_kind","target_delivery":"target_delivery","target_effect":"target_effect_fence"},"request_sources":{"direct_local_bootstrap":"supervisor","execution_substrate":"execution_substrate"}},"targets":["author_candidate","validate_candidate","review_candidate"],"values":{"classification":{"c1_evidence_member":false,"c2_binding":"profile_pair_plus_exact_operand_closure","durable_identity":false,"fields":["classification","reason"],"identity":false,"name":"RW0WireCancellationControlClassificationV1"},"process":{"digest_domain":"governed-execution.nwp-rw0-wire-process-observation.v1.identity","name":"RW0WireProcessObservationV1","schema_id":"governed-execution.nwp-rw0-wire-process-observation.v1"},"request":{"digest_domain":"governed-execution.nwp-rw0-wire-cancellation-request-observation.v1.identity","name":"RW0WireCancellationRequestObservationV1","schema_id":"governed-execution.nwp-rw0-wire-cancellation-request-observation.v1"}},"work":{"alias_accounting":"per_occurrence","duplicate_detection_after_reconstruction":true,"fixed_closed_relations":"unmetered","limit_outcomes":{"maximum":"evaluate_normally","one_under_classifier":["invalid","invalid_input"],"one_under_relation_error":"work_limit_exceeded"},"maximum_local_work_units":{"classifier":{"author_candidate":1244,"review_candidate":1342,"validate_candidate":1342},"process_relation":{"author_candidate":498,"review_candidate":596,"validate_candidate":596},"request_relation":{"author_candidate":640,"review_candidate":738,"validate_candidate":738},"response_relation":{"author_candidate":764,"review_candidate":862,"validate_candidate":862}},"one_under_local_work_units":{"classifier":{"author_candidate":1243,"review_candidate":1341,"validate_candidate":1341},"process_relation":{"author_candidate":497,"review_candidate":595,"validate_candidate":595},"request_relation":{"author_candidate":639,"review_candidate":737,"validate_candidate":737},"response_relation":{"author_candidate":763,"review_candidate":861,"validate_candidate":861}},"operand_reconstruction_units":{"AttemptFenceV1":92,"CandidateCapsuleManifestV1":98,"DeliveryEnvelopeV1":32,"EffectFenceV1":102,"RW0WireCancellationRequestObservationV1":62,"RW0WireProcessObservationV1":54,"WorkerCommandV1":116,"WorkerObservationV1":124},"tariff":"two_pass_occurrence_work_including_root_and_owner_revalidation"}}'''
EXPECTED_MANIFEST_BYTES = EXPECTED_MANIFEST_JSON.encode("utf-8")


CLASSIFICATION_MATRIX = {
    "invalid": (
        "invalid_input",
        "duplicate_fact",
        "unrelated_fact",
        "conflicting_fact",
        "cancellation_graph_mismatch",
    ),
    "incomplete": (
        "process_evidence_incomplete",
        "resource_limit_exceeded",
        "deadline_elapsed",
        "signal_delivered",
        "cancellation_acknowledged",
        "cancellation_request_pending",
    ),
    "finite": ("cancellation_rejected", "target_process_exited"),
}


class ControlGraph:
    __slots__ = (
        "command",
        "attempt",
        "author",
        "target",
        "target_delivery",
        "cancel",
        "cancel_delivery",
        "manifest",
    )

    def __init__(
        self,
        command: WorkerCommandV1,
        attempt: AttemptFenceV1,
        author: EffectFenceV1,
        target: EffectFenceV1,
        target_delivery: DeliveryEnvelopeV1,
        cancel: EffectFenceV1,
        cancel_delivery: DeliveryEnvelopeV1,
        manifest: CandidateCapsuleManifestV1,
    ) -> None:
        self.command = command
        self.attempt = attempt
        self.author = author
        self.target = target
        self.target_delivery = target_delivery
        self.cancel = cancel
        self.cancel_delivery = cancel_delivery
        self.manifest = manifest


def _delivery(
    effect: EffectFenceV1, token: str, adapter_kind: str,
) -> DeliveryEnvelopeV1:
    mapping = _delivery_for_vector("author")
    mapping.update(
        delivery_attempt_ref=f"delivery-attempt.{token}.0001",
        effect_intent_ref=effect.effect_intent_ref,
        effect_fence_ref=effect.effect_fence_ref,
        effect_fence_digest=effect.effect_fence_digest,
    )
    mapping["adapter_kind"] = adapter_kind
    safe_adapter_kind = adapter_kind.replace("_", "-")
    mapping["adapter_safe_correlation_ref"] = (
        f"adapter-correlation.{token}.{safe_adapter_kind}.0001"
    )
    return DeliveryEnvelopeV1.from_mapping(
        _reseal_single_digest_record("DeliveryEnvelopeV1", mapping)
    )


def control_graph(
    target_class: str = "author_candidate",
    adapter_kind: str = "direct_local_bootstrap",
) -> ControlGraph:
    target_vectors = {
        "author_candidate": "author",
        "validate_candidate": "validation",
        "review_candidate": "review",
    }
    target_vector = target_vectors[target_class]
    target = EffectFenceV1.from_mapping(_effect_fence_for_vector(target_vector))
    if target_class == "author_candidate":
        cancel_mapping = _effect_fence_for_vector("cancellation")
    elif target_class == "validate_candidate":
        cancel_mapping = _effect_fence_for_vector("cancellation_validation")
    else:
        cancel_mapping = _effect_fence_for_vector("cancellation_validation")
        cancel_mapping.update(
            effect_intent_ref="effect-intent.cancel-review.0001",
            effect_fence_ref="effect-fence.cancel-review.0001",
            effect_authorization_ref="effect-authorization.cancel-review.0001",
            effect_authorization_digest="a" * 64,
            cancellation_target_effect_intent_ref=target.effect_intent_ref,
            cancellation_target_effect_fence_ref=target.effect_fence_ref,
            cancellation_target_effect_fence_digest=target.effect_fence_digest,
        )
        cancel_mapping = _reseal_single_digest_record(
            "EffectFenceV1", cancel_mapping
        )
    cancel = EffectFenceV1.from_mapping(cancel_mapping)
    return ControlGraph(
        WorkerCommandV1.from_mapping(_full_record("WorkerCommandV1")),
        AttemptFenceV1.from_mapping(_full_record("AttemptFenceV1")),
        EffectFenceV1.from_mapping(_effect_fence_for_vector("author")),
        target,
        _delivery(target, target_vector, adapter_kind),
        cancel,
        _delivery(cancel, "cancel-" + target_vector, adapter_kind),
        CandidateCapsuleManifestV1.from_mapping(
            _full_record("CandidateCapsuleManifestV1")
        ),
    )


def capsule_operand(graph: ControlGraph) -> dict[str, object]:
    if graph.target.effect_class == "author_candidate":
        return {}
    return {"target_capsule_manifest": graph.manifest}


def make_request(
    graph: ControlGraph,
    *,
    ref: str = "request.observation.control.0001",
    observed_at: str = "2026-08-08T18:00:01Z",
    source_kind: str | None = None,
    overrides: dict[str, object] | None = None,
) -> wire.RW0WireCancellationRequestObservationV1:
    expected_source = (
        "supervisor"
        if graph.cancel_delivery.adapter_kind == "direct_local_bootstrap"
        else "execution_substrate"
    )
    identity: dict[str, object] = {
        "schema_id": REQUEST_SCHEMA,
        "request_observation_ref": ref,
        "source_kind": expected_source if source_kind is None else source_kind,
        "source_ref": "cancellation.request.source.0001",
        "source_invocation_ref": "cancellation.request.invocation.0001",
        "evidence_ref": "cancellation.request.evidence.0001",
        "evidence_digest": "a" * 64,
        "program_ref": graph.command.program_ref,
        "program_version_ref": graph.command.program_version_ref,
        "accepted_intent_revision_ref": graph.command.accepted_intent_revision_ref,
        "work_item_ref": graph.command.work_item_ref,
        "work_item_revision_ref": graph.command.work_item_revision_ref,
        "semantic_attempt_ref": graph.command.semantic_attempt_ref,
        "candidate_ref": graph.command.candidate_ref,
        "command_ref": graph.command.command_ref,
        "command_digest": graph.command.command_digest,
        "attempt_fence_ref": graph.attempt.attempt_fence_ref,
        "attempt_fence_digest": graph.attempt.attempt_fence_digest,
        "cancellation_effect_intent_ref": graph.cancel.effect_intent_ref,
        "cancellation_effect_fence_ref": graph.cancel.effect_fence_ref,
        "cancellation_effect_fence_digest": graph.cancel.effect_fence_digest,
        "cancellation_delivery_attempt_ref": graph.cancel_delivery.delivery_attempt_ref,
        "cancellation_delivery_envelope_digest": (
            graph.cancel_delivery.delivery_envelope_digest
        ),
        "target_effect_intent_ref": graph.target.effect_intent_ref,
        "target_effect_fence_ref": graph.target.effect_fence_ref,
        "target_effect_fence_digest": graph.target.effect_fence_digest,
        "target_delivery_attempt_ref": graph.target_delivery.delivery_attempt_ref,
        "target_delivery_envelope_digest": (
            graph.target_delivery.delivery_envelope_digest
        ),
        "observed_at": observed_at,
    }
    if overrides:
        identity.update(overrides)
    mapping = seal(
        identity,
        REQUEST_SCHEMA + ".identity",
        "request_observation_digest",
    )
    return wire.RW0WireCancellationRequestObservationV1.from_mapping(mapping)


def make_process(
    graph: ControlGraph,
    event_kind: str,
    *,
    ref: str | None = None,
    source_kind: str = "supervisor",
    observed_at: str = "2026-08-08T18:00:02Z",
    overrides: dict[str, object] | None = None,
) -> wire.RW0WireProcessObservationV1:
    identity: dict[str, object] = {
        "schema_id": PROCESS_SCHEMA,
        "process_observation_ref": (
            ref or f"process.observation.{event_kind.replace('_', '-')}.0001"
        ),
        "source_kind": source_kind,
        "source_ref": "process.source.0001",
        "source_invocation_ref": "process.invocation.0001",
        "evidence_ref": "process.evidence.0001",
        "evidence_digest": "b" * 64,
        "event_kind": event_kind,
        "program_ref": graph.command.program_ref,
        "program_version_ref": graph.command.program_version_ref,
        "accepted_intent_revision_ref": graph.command.accepted_intent_revision_ref,
        "work_item_ref": graph.command.work_item_ref,
        "work_item_revision_ref": graph.command.work_item_revision_ref,
        "semantic_attempt_ref": graph.command.semantic_attempt_ref,
        "candidate_ref": graph.command.candidate_ref,
        "command_ref": graph.command.command_ref,
        "command_digest": graph.command.command_digest,
        "attempt_fence_ref": graph.attempt.attempt_fence_ref,
        "attempt_fence_digest": graph.attempt.attempt_fence_digest,
        "effect_intent_ref": graph.target.effect_intent_ref,
        "effect_fence_ref": graph.target.effect_fence_ref,
        "effect_fence_digest": graph.target.effect_fence_digest,
        "delivery_attempt_ref": graph.target_delivery.delivery_attempt_ref,
        "delivery_envelope_digest": graph.target_delivery.delivery_envelope_digest,
        "observed_at": observed_at,
    }
    if overrides:
        identity.update(overrides)
    mapping = seal(
        identity,
        PROCESS_SCHEMA + ".identity",
        "process_observation_digest",
    )
    return wire.RW0WireProcessObservationV1.from_mapping(mapping)


def make_adapter(
    graph: ControlGraph,
    observation_kind: str,
    *,
    ref: str | None = None,
    source_kind: str | None = None,
    observed_at: str = "2026-08-08T18:00:03Z",
    exit_code: int | None = None,
) -> WorkerObservationV1:
    responses = ("cancellation_acknowledged", "cancellation_rejected")
    is_response = observation_kind in responses
    outcomes = {
        "cancellation_acknowledged": "acknowledged",
        "cancellation_rejected": "rejected",
        "deadline_elapsed": "elapsed",
        "process_exited": "exited",
        "delivery_acknowledged": "acknowledged",
    }
    delivery = graph.cancel_delivery if is_response else graph.target_delivery
    effect = graph.cancel if is_response else graph.target
    expected_source = (
        "direct_local_adapter"
        if delivery.adapter_kind == "direct_local_bootstrap"
        else "es_adapter"
    )
    extras: dict[str, object] = {}
    if graph.target.effect_class != "author_candidate":
        extras["capsule_manifest"] = graph.manifest
    if is_response:
        extras["cancellation_target"] = graph.target
    if exit_code is not None:
        extras["process_exit_code"] = exit_code
    return WorkerObservationV1.create(
        observation_ref=(
            ref or f"observation.control.{observation_kind.replace('_', '-')}.0001"
        ),
        source_kind=expected_source if source_kind is None else source_kind,
        source_ref="adapter.control.source.0001",
        source_invocation_ref="adapter.control.invocation.0001",
        observation_kind=observation_kind,
        outcome=outcomes[observation_kind],
        reason_code="reason.none",
        evidence_refs=["adapter.control.evidence.0001"],
        observed_at=observed_at,
        delivery=delivery,
        author_command=graph.command,
        attempt_fence=graph.attempt,
        author_effect_fence=graph.author,
        effect_fence=effect,
        **extras,
    )


def classifier_kwargs(graph: ControlGraph) -> dict[str, object]:
    result: dict[str, object] = {
        "author_command": graph.command,
        "attempt_fence": graph.attempt,
        "author_effect_fence": graph.author,
        "target_effect_fence": graph.target,
        "target_delivery": graph.target_delivery,
        "cancellation_effect_fence": graph.cancel,
        "cancellation_delivery": graph.cancel_delivery,
    }
    result.update(capsule_operand(graph))
    return result


def _assert_builtin_graph(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            assert type(key) is str
            _assert_builtin_graph(item)
        return
    if type(value) is list:
        for item in value:
            _assert_builtin_graph(item)
        return
    assert type(value) in (str, int, bool)


def test_profile_literal_canonical_bytes_length_and_digest_are_exact() -> None:
    profile = wire.cancellation_control_profile_mapping()
    manifest_bytes = json.dumps(
        profile["manifest"],
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert manifest_bytes == EXPECTED_MANIFEST_BYTES
    assert len(manifest_bytes) == 12_014
    identity = {
        "schema_id": PROFILE_SCHEMA_V1,
        "profile_ref": PROFILE_REF_V1,
        "manifest": json.loads(EXPECTED_MANIFEST_JSON),
    }
    canonical_identity = json.dumps(
        identity,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert len(canonical_identity) == 12_154
    assert hashlib.sha256(
        PROFILE_DOMAIN_V1.encode("utf-8") + b"\0" + canonical_identity
    ).hexdigest() == PROFILE_DIGEST_V1
    assert profile["profile_digest"] == PROFILE_DIGEST_V1


def test_profile_mapping_has_exact_order_and_returns_fresh_builtin_dicts() -> None:
    first = wire.cancellation_control_profile_mapping()
    second = wire.cancellation_control_profile_mapping()
    assert type(first) is type(second) is dict
    assert tuple(first) == ("schema_id", "profile_ref", "manifest", "profile_digest")
    assert tuple(first["manifest"]) == (
        "authority",
        "capsule",
        "classifier",
        "facts",
        "identity",
        "relations",
        "routes",
        "targets",
        "values",
        "work",
    )
    assert first == second
    assert first is not second and first["manifest"] is not second["manifest"]
    _assert_builtin_graph(first)
    first["manifest"]["authority"]["io"] = True
    assert second["manifest"]["authority"]["io"] is False


def test_classification_value_has_exact_fields_and_result_reason_matrix() -> None:
    cls = wire.RW0WireCancellationControlClassificationV1
    assert cls._FIELDS == ("classification", "reason")
    for classification, reasons in CLASSIFICATION_MATRIX.items():
        for reason in reasons:
            value = cls._create(classification, reason)
            assert type(value) is cls
            assert tuple(value.to_mapping()) == ("classification", "reason")
            assert value.to_mapping() == {
                "classification": classification,
                "reason": reason,
            }
            assert value.to_mapping() is not value.to_mapping()
            assert str(value) == repr(value) == cls.__name__
    with pytest.raises(wire.RW0WireProtocolError) as caught:
        cls._create("finite", "cancellation_request_pending")
    assert caught.value.reason == "invalid_field_value"
    with pytest.raises(wire.RW0WireProtocolError) as caught:
        cls._create("finite", 0)
    assert caught.value.reason == "invalid_field_type"


def test_classification_value_is_final_slotted_immutable_noncopyable_and_nonpickleable() -> None:
    cls = wire.RW0WireCancellationControlClassificationV1
    value = cls._create("finite", "target_process_exited")
    assert not hasattr(value, "__dict__")
    assert not hasattr(cls, "from_mapping")
    assert not hasattr(value, "identity_mapping")
    assert not hasattr(value, "canonical_identity_bytes")
    assert not hasattr(value, "computed_digest")
    with pytest.raises(TypeError, match="construction disabled"):
        cls()
    with pytest.raises(TypeError, match="subclassing disabled"):
        type("ForbiddenCancellationClassification", (cls,), {})
    with pytest.raises(AttributeError, match="immutable"):
        value.reason = "cancellation_rejected"
    with pytest.raises(AttributeError, match="immutable"):
        del value.reason
    for operation in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError, match="non-pickleable"):
            operation(value)


def test_existing_request_and_process_values_remain_golden_compatible() -> None:
    request = wire.RW0WireCancellationRequestObservationV1.from_mapping(
        request_mapping()
    )
    process = wire.RW0WireProcessObservationV1.from_mapping(process_mapping())
    assert request.to_mapping() == request_mapping()
    assert process.to_mapping() == process_mapping()
    assert request.computed_digest() == request.request_observation_digest
    assert process.computed_digest() == process.process_observation_digest


def test_existing_nwpf_profile_and_frame_vectors_are_unchanged() -> None:
    profile = wire.wire_profile_mapping()
    assert profile["schema_id"] == PROFILE_SCHEMA
    assert profile["profile_ref"] == "rw0-wire-nwpf-v1"
    assert profile["profile_digest"] == PROFILE_DIGEST
    command, attempt, author, delivery, _, _ = nwpf_graph()
    command_frame = wire.encode_wire_command_frame(
        command=command,
        delivery=delivery,
        attempt_fence=attempt,
        author_effect_fence=author,
    )
    started = worker_observation(
        "worker_started", "observation.golden.started.0001"
    )
    completed = worker_observation(
        "worker_completed", "observation.golden.completed.0001"
    )
    result = wire.RW0WireWorkerResultV1._create((started, completed))
    result_frame = wire.encode_wire_result_frame(
        result=result,
        command=command,
        delivery=delivery,
        attempt_fence=attempt,
        author_effect_fence=author,
    )
    assert (len(command_frame), hashlib.sha256(command_frame).hexdigest()) == (
        3512,
        "cd75e668cc06fa67f39e3670d1867c134606491887112d10de8bd28c9d8e481e",
    )
    assert (len(result_frame), hashlib.sha256(result_frame).hexdigest()) == (
        2450,
        "f8b8e3af49a88351607c85ab3e74bfc55e8f32c6ff0499edca6920bf6526dee1",
    )
    assert PROFILE_REF_V1.encode("utf-8") not in command_frame + result_frame


def test_profile_declares_exact_fact_cardinality_and_work_tariffs() -> None:
    manifest = json.loads(EXPECTED_MANIFEST_JSON)
    assert manifest["facts"] == {
        "absence": "None",
        "adapter_observations": {
            "maximum": 4,
            "minimum": 0,
            "roles": [
                "cancellation_acknowledged",
                "cancellation_rejected",
                "deadline_elapsed",
                "process_exited",
            ],
        },
        "duplicate_detection": {
            "after_reconstruction": True,
            "keys": [
                "original_object_identity",
                "safe_fact_ref",
                "safe_fact_digest",
            ],
            "scope": "all_supplied_facts",
        },
        "item_types": {
            "adapter_observations": "exact_WorkerObservationV1",
            "process_observations": "exact_RW0WireProcessObservationV1",
        },
        "observation_items_nullable": False,
        "outer_types": {
            "adapter_observations": "exact_builtin_tuple",
            "process_observations": "exact_builtin_tuple",
            "request": "exact_RW0WireCancellationRequestObservationV1_or_None",
        },
        "process_observations": {
            "maximum": 2,
            "minimum": 0,
            "roles": ["resource_limit_exceeded", "signal_delivered"],
        },
        "request": {"maximum": 1, "minimum": 0},
        "request_absence": "None",
        "request_bindings": [
            "target_effect_fence",
            "target_delivery",
            "cancellation_effect_fence",
            "cancellation_delivery",
        ],
        "role_bindings": manifest["facts"]["role_bindings"],
        "role_validation": manifest["facts"]["role_validation"],
        "singleton_maximum": 1,
        "singleton_roles": [
            "request",
            "cancellation_acknowledged",
            "cancellation_rejected",
            "deadline_elapsed",
            "process_exited",
            "resource_limit_exceeded",
            "signal_delivered",
        ],
        "total_maximum": 7,
    }
    assert manifest["work"] == {
        "alias_accounting": "per_occurrence",
        "duplicate_detection_after_reconstruction": True,
        "fixed_closed_relations": "unmetered",
        "limit_outcomes": {
            "maximum": "evaluate_normally",
            "one_under_classifier": ["invalid", "invalid_input"],
            "one_under_relation_error": "work_limit_exceeded",
        },
        "maximum_local_work_units": {
            "classifier": {
                "author_candidate": 1244,
                "review_candidate": 1342,
                "validate_candidate": 1342,
            },
            "process_relation": {
                "author_candidate": 498,
                "review_candidate": 596,
                "validate_candidate": 596,
            },
            "request_relation": {
                "author_candidate": 640,
                "review_candidate": 738,
                "validate_candidate": 738,
            },
            "response_relation": {
                "author_candidate": 764,
                "review_candidate": 862,
                "validate_candidate": 862,
            },
        },
        "one_under_local_work_units": {
            "classifier": {
                "author_candidate": 1243,
                "review_candidate": 1341,
                "validate_candidate": 1341,
            },
            "process_relation": {
                "author_candidate": 497,
                "review_candidate": 595,
                "validate_candidate": 595,
            },
            "request_relation": {
                "author_candidate": 639,
                "review_candidate": 737,
                "validate_candidate": 737,
            },
            "response_relation": {
                "author_candidate": 763,
                "review_candidate": 861,
                "validate_candidate": 861,
            },
        },
        "operand_reconstruction_units": {
            "AttemptFenceV1": 92,
            "CandidateCapsuleManifestV1": 98,
            "DeliveryEnvelopeV1": 32,
            "EffectFenceV1": 102,
            "RW0WireCancellationRequestObservationV1": 62,
            "RW0WireProcessObservationV1": 54,
            "WorkerCommandV1": 116,
            "WorkerObservationV1": 124,
        },
        "tariff": "two_pass_occurrence_work_including_root_and_owner_revalidation",
    }
