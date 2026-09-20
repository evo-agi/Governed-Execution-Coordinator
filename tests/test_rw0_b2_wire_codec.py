from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

import ge_nwp_coordinator._rw0_wire_protocol_values as wire
import ge_nwp_coordinator._worker_execution_semantic_values as semantic
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1, CeilingsV1, DeliveryEnvelopeV1, EffectFenceV1,
    WorkerCommandV1, WorkerObservationV1,
)
from ge_nwp_coordinator._rw0_wire_protocol_values import (
    RW0WireProtocolError, RW0WireWorkerResultV1,
    decode_wire_command_frame, decode_wire_result_frame,
    encode_wire_command_frame, encode_wire_result_frame,
)
from tests.c2a_contract_support import (
    _reseal_author_command, _reseal_single_digest_record,
)
from tests.test_rw0_b2_wire_values import graph, worker_observation

MAGIC = b"NWPF"
VERSION = 1
COMMAND_KIND = 1
RESULT_KIND = 2
COMMAND_CAP = 5898
RESULT_CAP = 16627
COMMAND_WORK = 23746
RESULT_WORK = 66770
MAX_INTEGER = 9_223_372_036_854_775_807
MAX_FRAME_KEY_CHARS = 29
COMMAND_FIELDS = (
    "schema_id", "command_ref", "program_ref", "program_version_ref",
    "accepted_intent_revision_ref", "work_item_ref", "work_item_revision_ref",
    "semantic_attempt_ref", "effect_intent_ref", "effect_class", "candidate_ref",
    "repository_ref", "base_git_object_format", "base_git_oid", "path_ceiling",
    "work_spec_ref", "work_spec_digest", "standing_grant_ref",
    "standing_grant_digest", "attempt_authorization_ref",
    "attempt_authorization_digest", "effect_authorization_ref",
    "effect_authorization_digest", "attempt_fence_ref", "attempt_fence_digest",
    "effect_fence_ref", "effect_fence_digest", "global_stop_ref",
    "global_stop_version", "validation_requirement_ref",
    "validation_requirement_digest", "review_requirement_ref",
    "review_requirement_digest", "capsule_schema_id", "capsule_profile_ref",
    "effect_ceilings", "privacy_classification", "redaction_profile_ref",
    "command_digest",
)
DELIVERY_FIELDS = (
    "schema_id", "delivery_attempt_ref", "program_ref", "program_version_ref",
    "command_ref", "command_digest", "semantic_attempt_ref", "effect_intent_ref",
    "attempt_fence_ref", "attempt_fence_digest", "effect_fence_ref",
    "effect_fence_digest", "adapter_kind", "adapter_safe_correlation_ref",
    "delivery_envelope_digest",
)
OBSERVATION_FIELDS = (
    "schema_id", "observation_ref", "source_kind", "source_ref",
    "source_invocation_ref", "delivery_attempt_ref", "program_ref",
    "program_version_ref", "accepted_intent_revision_ref", "work_item_ref",
    "work_item_revision_ref", "semantic_attempt_ref", "effect_intent_ref",
    "command_ref", "command_digest", "attempt_fence_ref", "attempt_fence_digest",
    "effect_fence_ref", "effect_fence_digest", "observation_kind", "outcome",
    "reason_code", "evidence_refs", "observed_at", "observation_digest",
)
CEILING_FIELDS = (
    "max_active_invocations", "max_candidate_bytes", "max_changed_files",
    "max_cost_microusd", "max_cpu_seconds", "max_deliveries", "max_deployments",
    "max_local_commits", "max_memory_bytes", "max_merges",
    "max_model_input_tokens", "max_model_output_tokens", "max_pull_requests",
    "max_pushes", "max_wall_seconds",
)
GIT_ZERO_FIELDS = {
    "max_deployments", "max_local_commits", "max_merges", "max_pull_requests",
    "max_pushes",
}


def command_frame() -> bytes:
    command, attempt, author, delivery, _, _ = graph()
    return encode_wire_command_frame(
        command=command, delivery=delivery,
        attempt_fence=attempt, author_effect_fence=author)


def result_frame() -> bytes:
    command, attempt, author, delivery, _, _ = graph()
    result = RW0WireWorkerResultV1._create((
        worker_observation("worker_started", "observation.started.0001"),
        worker_observation("candidate_captured", "observation.captured.0001"),
        worker_observation("worker_completed", "observation.completed.0001"),
    ))
    return encode_wire_result_frame(
        result=result, command=command, delivery=delivery,
        attempt_fence=attempt, author_effect_fence=author)


def decode_command(frame: bytes) -> object:
    _, attempt, author, _, _, _ = graph()
    return decode_wire_command_frame(frame, attempt_fence=attempt,
                                     author_effect_fence=author)


def decode_result(frame: bytes) -> object:
    command, attempt, author, delivery, _, _ = graph()
    return decode_wire_result_frame(
        frame, command=command, delivery=delivery,
        attempt_fence=attempt, author_effect_fence=author)


def framed(kind: int, payload: bytes) -> bytes:
    return MAGIC + bytes((VERSION, kind)) + len(payload).to_bytes(2, "big") + payload


def rejected(call, frame: bytes, reason: str) -> None:
    with pytest.raises(RW0WireProtocolError) as caught:
        call(frame)
    assert caught.value.reason == reason
    assert str(caught.value) == repr(caught.value) == "RW0WireProtocolError"


def _contains_sentinel(value: object, sentinels: tuple[bytes | str, ...],
                       seen: set[int] | None = None) -> bool:
    if seen is None:
        seen = set()
    marker = id(value)
    if marker in seen:
        return False
    seen.add(marker)
    if type(value) is bytes:
        return any(
            (item in value if type(item) is bytes else item.encode() in value)
            for item in sentinels
        )
    if type(value) is str:
        return any(
            (item in value if type(item) is str else item.decode("utf-8", "ignore") in value)
            for item in sentinels
        )
    if type(value) in (tuple, list, set, frozenset):
        return any(_contains_sentinel(item, sentinels, seen) for item in value)
    if type(value) is dict:
        return any(
            _contains_sentinel(key, sentinels, seen)
            or _contains_sentinel(item, sentinels, seen)
            for key, item in value.items()
        )
    if isinstance(value, BaseException):
        return _contains_sentinel(value.args, sentinels, seen)
    if type(value).__module__.startswith("ge_nwp_coordinator"):
        for cls in type(value).__mro__:
            slots = cls.__dict__.get("__slots__", ())
            if type(slots) is str:
                slots = (slots,)
            for slot in slots:
                try:
                    item = object.__getattribute__(value, slot)
                except AttributeError:
                    continue
                if _contains_sentinel(item, sentinels, seen):
                    return True
    return False


def assert_sealed_failure(call, reason: str, *sentinels: bytes | str) -> None:
    with pytest.raises(RW0WireProtocolError) as caught:
        call()
    error = caught.value
    assert error.reason == reason
    assert error.args == ("RW0WireProtocolError",)
    assert str(error) == repr(error) == "RW0WireProtocolError"
    assert error.__cause__ is None
    assert error.__context__ is None
    assert not _contains_sentinel(error, tuple(sentinels))
    traceback = error.__traceback__
    while traceback is not None:
        frame = traceback.tb_frame
        if Path(frame.f_code.co_filename).name == "_rw0_wire_protocol_values.py":
            assert not any(
                _contains_sentinel(value, tuple(sentinels))
                for value in frame.f_locals.values()
            )
        traceback = traceback.tb_next


def _maximum_graph(*, command_decrement: int = 0) -> tuple[
    WorkerCommandV1, AttemptFenceV1, EffectFenceV1, DeliveryEnvelopeV1,
]:
    base_command, base_attempt, base_author, base_delivery, _, _ = graph()
    padded_refs: dict[str, str] = {}

    def padded_ref(value: str) -> str:
        if value not in padded_refs:
            prefix = f"r{len(padded_refs):03d}."
            size = 96
            if value == base_delivery.adapter_safe_correlation_ref:
                size -= command_decrement
            padded_refs[value] = prefix + "x" * (size - len(prefix))
        return padded_refs[value]

    def maximize(mapping: dict[str, object]) -> dict[str, object]:
        result = deepcopy(mapping)
        for key, value in tuple(result.items()):
            if key.endswith("_ref") and type(value) is str:
                result[key] = padded_ref(value)
            elif key == "global_stop_version":
                result[key] = MAX_INTEGER
            elif key in ("aggregate_ceilings", "effect_ceilings"):
                assert type(value) is dict and tuple(value) == CEILING_FIELDS
                result[key] = {
                    name: 0 if name in GIT_ZERO_FIELDS else MAX_INTEGER
                    for name in CEILING_FIELDS
                }
        return result

    attempt_mapping = _reseal_single_digest_record(
        "AttemptFenceV1", maximize(base_attempt.to_mapping()))
    attempt = AttemptFenceV1.from_mapping(attempt_mapping)

    command_mapping = maximize(base_command.to_mapping())
    assert tuple(command_mapping) == COMMAND_FIELDS
    command_mapping["attempt_fence_digest"] = attempt.attempt_fence_digest
    command_mapping["effect_fence_digest"] = "0" * 64
    command_mapping = _reseal_author_command(command_mapping)
    preliminary_command = WorkerCommandV1.from_mapping(command_mapping)

    author_mapping = maximize(base_author.to_mapping())
    author_mapping["attempt_fence_digest"] = attempt.attempt_fence_digest
    author_mapping["command_digest"] = preliminary_command.command_digest
    author_mapping = _reseal_single_digest_record("EffectFenceV1", author_mapping)
    author = EffectFenceV1.from_mapping(author_mapping)

    command_mapping["effect_fence_digest"] = author.effect_fence_digest
    command = WorkerCommandV1.from_mapping(command_mapping)

    delivery_mapping = maximize(base_delivery.to_mapping())
    assert tuple(delivery_mapping) == DELIVERY_FIELDS
    delivery_mapping.update(
        attempt_fence_digest=attempt.attempt_fence_digest,
        command_digest=command.command_digest,
        effect_fence_digest=author.effect_fence_digest,
    )
    delivery = DeliveryEnvelopeV1.from_mapping(
        _reseal_single_digest_record("DeliveryEnvelopeV1", delivery_mapping))
    return command, attempt, author, delivery


def _maximum_result(*, result_decrement: int = 0) -> tuple[
    RW0WireWorkerResultV1, WorkerCommandV1, AttemptFenceV1,
    EffectFenceV1, DeliveryEnvelopeV1,
]:
    command, attempt, author, delivery = _maximum_graph()
    observations: list[WorkerObservationV1] = []
    for index, (kind, reference) in enumerate((
        ("worker_started", "observation.maximum.started.0001"),
        ("candidate_captured", "observation.maximum.captured.0001"),
        ("worker_completed", "observation.maximum.completed.0001"),
    )):
        mapping = worker_observation(kind, reference).to_mapping()
        expected = (
            OBSERVATION_FIELDS[:-1]
            + (("candidate_ref",) if kind == "candidate_captured" else ())
            + (OBSERVATION_FIELDS[-1],)
        )
        assert tuple(mapping) == expected
        for key, value in tuple(mapping.items()):
            if key.endswith("_ref") and type(value) is str:
                prefix = f"o{index:01d}{len(key):02d}."
                mapping[key] = prefix + "x" * (96 - len(prefix))
        shared = {
            "source_ref": "worker." + "s" * 89,
            "source_invocation_ref": "invocation." + "i" * 85,
            "delivery_attempt_ref": delivery.delivery_attempt_ref,
            "program_ref": command.program_ref,
            "program_version_ref": command.program_version_ref,
            "accepted_intent_revision_ref": command.accepted_intent_revision_ref,
            "work_item_ref": command.work_item_ref,
            "work_item_revision_ref": command.work_item_revision_ref,
            "semantic_attempt_ref": command.semantic_attempt_ref,
            "effect_intent_ref": author.effect_intent_ref,
            "command_ref": command.command_ref,
            "command_digest": command.command_digest,
            "attempt_fence_ref": attempt.attempt_fence_ref,
            "attempt_fence_digest": attempt.attempt_fence_digest,
            "effect_fence_ref": author.effect_fence_ref,
            "effect_fence_digest": author.effect_fence_digest,
        }
        mapping.update(shared)
        if kind == "candidate_captured":
            mapping["candidate_ref"] = command.candidate_ref
        mapping["reason_code"] = "reason." + "z" * (
            89 - (result_decrement if index == 0 else 0)
        )
        mapping["evidence_refs"] = [
            f"e{item:02d}." + "y" * 92 for item in range(32)
        ]
        mapping = _reseal_single_digest_record("WorkerObservationV1", mapping)
        observations.append(WorkerObservationV1.from_mapping(mapping))
    return (
        RW0WireWorkerResultV1._create(tuple(observations)),
        command, attempt, author, delivery
    )


def test_round_trip_exact_header_payload_roots_and_work_formula() -> None:
    command = command_frame()
    result = result_frame()
    assert command[:6] == b"NWPF\x01\x01"
    assert result[:6] == b"NWPF\x01\x02"
    assert int.from_bytes(command[6:8], "big") == len(command) - 8
    assert int.from_bytes(result[6:8], "big") == len(result) - 8
    assert len(command) <= COMMAND_CAP + 8
    assert len(result) <= RESULT_CAP + 8
    assert tuple(json.loads(command[8:])) == ("command", "delivery")
    assert tuple(json.loads(result[8:])) == ("observations",)
    assert decode_command(command)[0].command_ref == graph()[0].command_ref
    assert len(decode_result(result).observations) == 3
    assert 8 + 4 * COMMAND_CAP + 71 + 5 + 70 == COMMAND_WORK
    assert 8 + 4 * RESULT_CAP + 77 + 8 + 169 == RESULT_WORK


def test_header_priority_and_single_frame() -> None:
    valid = command_frame()
    rejected(decode_command, bytearray(valid), "invalid_outer_type")
    for count in range(8):
        rejected(decode_command, valid[:count], "short_header")
    for offset in range(4):
        changed = bytearray(valid); changed[offset] ^= 1
        rejected(decode_command, bytes(changed), "bad_magic")
    changed = bytearray(valid); changed[4] = 2
    rejected(decode_command, bytes(changed), "unsupported_version")
    for kind in (0, 2, 3, 255):
        changed = bytearray(valid); changed[5] = kind
        rejected(decode_command, bytes(changed), "unsupported_kind")
    changed = bytearray(valid); changed[6:8] = (COMMAND_CAP + 1).to_bytes(2, "big")
    rejected(decode_command, bytes(changed), "declared_length_over_cap")
    changed[6:8] = (65535).to_bytes(2, "big")
    rejected(decode_command, bytes(changed), "declared_length_over_cap")
    rejected(decode_command, valid[:-1], "truncated_payload")
    rejected(decode_command, valid + b"x", "trailing_data")
    rejected(decode_command, valid + valid, "trailing_data")


def test_utf8_bom_json_token_and_duplicate_priority() -> None:
    rejected(decode_command, framed(COMMAND_KIND, b"\xff"), "invalid_utf8")
    rejected(decode_command, framed(COMMAND_KIND, b"\xef\xbb\xbf{}"), "bom_forbidden")
    for payload in (b"{", b'{"x":01}', b'{"x":1.0}', b'{"x":1e2}',
                    b'{"x":NaN}', b'{"x":9223372036854775808}'):
        rejected(decode_command, framed(COMMAND_KIND, payload), "json_token_invalid")
    rejected(decode_command, framed(COMMAND_KIND, b'{"x":1,"x":2'), "json_token_invalid")
    rejected(decode_command, framed(COMMAND_KIND, b'{"x":1,"x":2}'), "duplicate_key")
    rejected(decode_command, framed(COMMAND_KIND, b'{"command":{"x":1,"x":2},"delivery":{}}'),
             "duplicate_key")
    overlength = b"x" * 30
    rejected(
        decode_command,
        framed(COMMAND_KIND, b'{"' + overlength + b'":0}'),
        "invalid_root_or_scalar",
    )
    rejected(
        decode_command,
        framed(
            COMMAND_KIND,
            b'{"' + overlength + b'":0,"' + overlength + b'":1}',
        ),
        "duplicate_key",
    )
    rejected(
        decode_command,
        framed(
            COMMAND_KIND,
            b'{"nested":{"' + overlength + b'":0,"'
            + overlength + b'":1},"later":',
        ),
        "json_token_invalid",
    )
    for payload in (b"[]", b"true", b"null", b'{"command":true,"delivery":{}}'):
        rejected(decode_command, framed(COMMAND_KIND, payload), "invalid_root_or_scalar")


def test_closed_root_and_canonical_payload() -> None:
    valid = command_frame()
    root = json.loads(valid[8:])
    rejected(decode_command, framed(COMMAND_KIND, b'{"unexpected":0}'), "unknown_field")
    rejected(decode_command, framed(COMMAND_KIND, b'{"command":{}}'), "missing_field")
    payload = json.dumps(root, sort_keys=True, separators=(", ", ":")).encode()
    rejected(decode_command, framed(COMMAND_KIND, payload), "noncanonical_payload")
    payload = json.dumps({"delivery": root["delivery"], "command": root["command"]},
                         sort_keys=False, separators=(",", ":")).encode()
    rejected(decode_command, framed(COMMAND_KIND, payload), "noncanonical_payload")
    nested = json.loads(valid[8:])
    nested["command"]["command_ref"] = "not a safe ref"
    rejected(decode_command, framed(COMMAND_KIND, json.dumps(nested, sort_keys=True,
              separators=(",", ":")).encode()), "nested_record_invalid")


def test_result_frame_rejects_wrong_kind_and_shape() -> None:
    valid = result_frame()
    rejected(decode_result, valid[:-1], "truncated_payload")
    rejected(decode_result, command_frame(), "unsupported_kind")
    rejected(decode_result, framed(RESULT_KIND, b'{"observations":[]}'), "nested_record_invalid")
    rejected(decode_result, framed(RESULT_KIND, b'{"observations":[1,2]}'), "nested_record_invalid")
    changed = bytearray(valid); changed[6:8] = (RESULT_CAP + 1).to_bytes(2, "big")
    rejected(decode_result, bytes(changed), "declared_length_over_cap")


def test_foreign_error_graphs_drop_json_utf8_nested_and_relation_payloads() -> None:
    json_sentinel = "AUDIT-JSON-SENTINEL"
    json_payload = ('{"command":"' + json_sentinel + '"').encode()
    assert_sealed_failure(
        lambda: decode_command(framed(COMMAND_KIND, json_payload)),
        "json_token_invalid", json_sentinel, json_payload,
    )

    utf8_sentinel = b"AUDIT-UTF8-SENTINEL"
    utf8_payload = b"\xff" + utf8_sentinel
    assert_sealed_failure(
        lambda: decode_command(framed(COMMAND_KIND, utf8_payload)),
        "invalid_utf8", utf8_sentinel, utf8_payload,
    )

    nested_sentinel = "AUDIT-NESTED-SENTINEL!"
    nested = json.loads(command_frame()[8:])
    nested["command"]["command_ref"] = nested_sentinel
    nested_payload = json.dumps(
        nested, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ).encode()
    assert_sealed_failure(
        lambda: decode_command(framed(COMMAND_KIND, nested_payload)),
        "nested_record_invalid", nested_sentinel, nested_payload,
    )

    relation_sentinel = "audit-relation-sentinel"
    command, attempt, author, delivery, _, _ = graph()
    delivery_mapping = delivery.to_mapping()
    delivery_mapping["program_ref"] = relation_sentinel
    unrelated_delivery = DeliveryEnvelopeV1.from_mapping(
        _reseal_single_digest_record("DeliveryEnvelopeV1", delivery_mapping))
    assert_sealed_failure(
        lambda: encode_wire_command_frame(
            command=command, delivery=unrelated_delivery,
            attempt_fence=attempt, author_effect_fence=author),
        "relation_mismatch", relation_sentinel,
    )


def test_exact_maximum_command_and_one_semantic_decrement() -> None:
    command, attempt, author, delivery = _maximum_graph()
    assert command.global_stop_version == MAX_INTEGER
    assert command.effect_ceilings.max_cpu_seconds == MAX_INTEGER
    maximum = encode_wire_command_frame(
        command=command, delivery=delivery,
        attempt_fence=attempt, author_effect_fence=author)
    assert len(maximum[8:]) == 5898
    assert len(maximum) == 5906
    decoded_command, decoded_delivery = decode_wire_command_frame(
        maximum, attempt_fence=attempt, author_effect_fence=author)
    assert decoded_command.to_mapping() == command.to_mapping()
    assert decoded_delivery.to_mapping() == delivery.to_mapping()

    below_command, below_attempt, below_author, below_delivery = _maximum_graph(
        command_decrement=1)
    below = encode_wire_command_frame(
        command=below_command, delivery=below_delivery,
        attempt_fence=below_attempt, author_effect_fence=below_author)
    assert len(below[8:]) == 5897
    assert len(below) == 5905
    decode_wire_command_frame(
        below, attempt_fence=below_attempt, author_effect_fence=below_author)


def test_exact_maximum_result_and_one_semantic_decrement() -> None:
    result, command, attempt, author, delivery = _maximum_result()
    maximum = encode_wire_result_frame(
        result=result, command=command, delivery=delivery,
        attempt_fence=attempt, author_effect_fence=author)
    assert len(maximum[8:]) == 16627
    assert len(maximum) == 16635
    decoded = decode_wire_result_frame(
        maximum, command=command, delivery=delivery,
        attempt_fence=attempt, author_effect_fence=author)
    assert decoded.to_mapping() == result.to_mapping()

    below_result, below_command, below_attempt, below_author, below_delivery = (
        _maximum_result(result_decrement=1)
    )
    below = encode_wire_result_frame(
        result=below_result, command=below_command, delivery=below_delivery,
        attempt_fence=below_attempt, author_effect_fence=below_author)
    assert len(below[8:]) == 16626
    assert len(below) == 16634
    decode_wire_result_frame(
        below, command=below_command, delivery=below_delivery,
        attempt_fence=below_attempt, author_effect_fence=below_author)


def test_declared_cap_plus_one_precedes_payload_access_and_exact_frames_are_single() -> None:
    for kind, cap, decoder in (
        (COMMAND_KIND, COMMAND_CAP, decode_command),
        (RESULT_KIND, RESULT_CAP, decode_result),
    ):
        header_only = MAGIC + bytes((VERSION, kind)) + (cap + 1).to_bytes(2, "big")
        rejected(decoder, header_only, "declared_length_over_cap")
    command = command_frame()
    rejected(decode_command, command + b"x", "trailing_data")
    rejected(decode_command, command + command, "trailing_data")


def test_depth_container_key_and_scalar_maximum_plus_one_are_isolated(
    monkeypatch,
) -> None:
    assert max(map(len, COMMAND_FIELDS + DELIVERY_FIELDS + OBSERVATION_FIELDS)) == (
        MAX_FRAME_KEY_CHARS
    )

    def payload(value: object) -> bytes:
        return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()

    command_shapes = (
        {"command": {"x": [[0]]}, "delivery": {}},
        {"command": {}, "delivery": {}, "a": {}, "b": {}, "c": {}},
        {"x": list(range(71))},
        {"x" * (MAX_FRAME_KEY_CHARS + 1): 0},
    )
    result_shapes = (
        {"observations": [[[[0]]]]},
        {"observations": [[] for _ in range(7)]},
        {"observations": [{f"k{index:02d}": 0 for index in range(77)}]},
        {"observations": list(range(170))},
        {"x" * (MAX_FRAME_KEY_CHARS + 1): 0},
    )
    for value in command_shapes:
        rejected(
            decode_command, framed(COMMAND_KIND, payload(value)),
            "invalid_root_or_scalar")
    for value in result_shapes:
        rejected(
            decode_result, framed(RESULT_KIND, payload(value)),
            "invalid_root_or_scalar")

    pair_tree = {f"k{index:02d}": 0 for index in range(70)}
    pair_tree.update(container_a={}, container_b={})
    pair_payload = payload(pair_tree)
    assert wire._CAPS[COMMAND_KIND] == (5898, 3, 5, 71, 70, 23746)
    assert len(pair_tree) == 72
    assert sum(type(value) is int for value in pair_tree.values()) == 70
    assert sum(type(value) is dict for value in pair_tree.values()) == 2
    assert max(map(len, pair_tree)) <= 29
    assert len(pair_payload) < 5898
    production = wire._shape_work(pair_tree, COMMAND_KIND, len(pair_payload))
    assert production.structural is True
    rejected(
        decode_command,
        framed(COMMAND_KIND, pair_payload),
        "invalid_root_or_scalar",
    )

    monkeypatch.setattr(
        wire,
        "_CAPS",
        {
            COMMAND_KIND: (5898, 3, 5, 72, 70, 23746),
            RESULT_KIND: (16627, 4, 8, 77, 169, 66770),
        },
    )
    broken = wire._shape_work(pair_tree, COMMAND_KIND, len(pair_payload))
    assert broken.structural is False
    assert broken.duplicate is False
    assert broken.units <= 23746
    with pytest.raises(RW0WireProtocolError) as caught:
        decode_command(framed(COMMAND_KIND, pair_payload))
    assert caught.value.reason == "unknown_field"


def test_duplicate_raw_pairs_are_accounted_and_shape_is_traversed_once(monkeypatch) -> None:
    valid = command_frame()
    calls: list[tuple[object, ...]] = []
    original = wire._shape_work

    def counted(*args):
        calls.append(args)
        return original(*args)

    monkeypatch.setattr(wire, "_shape_work", counted)
    decode_command(valid)
    assert len(calls) == 1
    assert type(calls[0][0]) is wire._JSONObjectPairs
    assert len(calls[0][0].pairs) == 2

    calls.clear()
    duplicate = framed(
        COMMAND_KIND,
        b'{"command":{"x":1,"x":2},"delivery":{}}',
    )
    rejected(decode_command, duplicate, "duplicate_key")
    assert calls == []
    raw_root, accounting = wire._decode_json(duplicate[8:])
    assert accounting.raw_pair_count == 4
    assert accounting.duplicate_seen is True
    assert type(raw_root) is wire._JSONObjectPairs
    raw_command = dict(raw_root.pairs)["command"]
    assert type(raw_command) is wire._JSONObjectPairs
    assert raw_command.pairs == (("x", 1), ("x", 2))

    calls.clear()
    rejected(
        decode_command,
        framed(COMMAND_KIND, b'{"command":{"x":1,"x":2},"delivery":{}'),
        "json_token_invalid",
    )
    assert calls == []


def test_injected_work_maximum_plus_one_is_exact(monkeypatch) -> None:
    command, attempt, author, delivery = _maximum_graph()
    command_maximum = encode_wire_command_frame(
        command=command, delivery=delivery,
        attempt_fence=attempt, author_effect_fence=author)
    result, result_command, result_attempt, result_author, result_delivery = (
        _maximum_result()
    )
    result_maximum = encode_wire_result_frame(
        result=result, command=result_command, delivery=result_delivery,
        attempt_fence=result_attempt, author_effect_fence=result_author)
    monkeypatch.setattr(wire, "_WORK_TEST_EXTRA_UNITS", 1)
    rejected(
        lambda value: decode_wire_command_frame(
            value, attempt_fence=attempt, author_effect_fence=author),
        command_maximum, "work_limit_exceeded")
    rejected(
        lambda value: decode_wire_result_frame(
            value, command=result_command, delivery=result_delivery,
            attempt_fence=result_attempt, author_effect_fence=result_author),
        result_maximum, "work_limit_exceeded")


def test_parse_accounting_charges_duplicates_before_shape() -> None:
    tree, accounting = wire._decode_json(b'{"x":1,"x":2}')
    assert type(tree) is wire._JSONObjectPairs
    assert accounting.raw_pair_count == 2
    assert accounting.duplicate_seen is True
    assert accounting.key_shape_invalid is False


def test_over_cap_siblings_use_depth_bounded_frames_and_keep_error_priority(
    monkeypatch,
) -> None:
    literal_result_caps = (16_627, 4, 8, 77, 169, 66_770)
    profile_result = wire.wire_profile_mapping()["manifest"]["payloads"][
        "worker_result"
    ]
    assert literal_result_caps == (16_627, 4, 8, 77, 169, 66_770)
    assert literal_result_caps == (
        profile_result["max_bytes"],
        profile_result["max_depth"],
        profile_result["max_containers"],
        profile_result["max_key_pairs"],
        profile_result["max_scalar_leaves"],
        profile_result["max_hostile_units"],
    )
    assert wire._CAPS[RESULT_KIND] == literal_result_caps
    literal_pending_frame_limit = 5
    payload = json.dumps(
        {"observations": [0] * 5000}, separators=(",", ":"),
    ).encode()
    assert len(payload) < RESULT_CAP
    pending: list[int] = []
    original = wire._shape_work

    def observed(*args):
        scan = original(*args)
        pending.append(scan.max_pending_frames)
        return scan

    monkeypatch.setattr(wire, "_shape_work", observed)
    rejected(decode_result, framed(RESULT_KIND, payload), "invalid_root_or_scalar")
    assert len(pending) == 1
    assert pending[0] <= literal_pending_frame_limit

    duplicate_and_shape = (
        b'{"observations":[0,0,0],"observations":['
        + b','.join([b'0'] * 5000)
        + b']}'
    )
    rejected(
        decode_result, framed(RESULT_KIND, duplicate_and_shape), "duplicate_key")
    monkeypatch.setattr(wire, "_WORK_TEST_EXTRA_UNITS", RESULT_WORK + 1)
    rejected(decode_result, framed(RESULT_KIND, payload), "invalid_root_or_scalar")

    inflated = dict(wire._CAPS)
    inflated[RESULT_KIND] = (16_627, 99, 8, 77, 169, 66_770)
    monkeypatch.setattr(wire, "_CAPS", inflated)
    production_derived_oracle = wire._CAPS[RESULT_KIND][1] + 1
    assert production_derived_oracle == 100
    assert literal_pending_frame_limit == 5


def test_hostile_c2a_alias_cycle_and_custom_iterable_fail_before_expansion(
    monkeypatch,
) -> None:
    hostile: list[tuple[WorkerCommandV1, AttemptFenceV1, EffectFenceV1,
                        DeliveryEnvelopeV1]] = []
    for depth in (8, 12, 16):
        command, attempt, author, delivery, _, _ = graph()
        node: object = ("safe",)
        for _ in range(depth):
            node = (node, node)
        object.__setattr__(command, "_path_ceiling", node)
        hostile.append((command, attempt, author, delivery))

    cycle_command, cycle_attempt, cycle_author, cycle_delivery, _, _ = graph()
    ceilings = cycle_command.effect_ceilings
    object.__setattr__(ceilings, "_max_active_invocations", ceilings)
    hostile.append((cycle_command, cycle_attempt, cycle_author, cycle_delivery))

    iterations = 0

    class ExplosiveIterable:
        def __iter__(self):
            nonlocal iterations
            iterations += 1
            raise AssertionError("custom iteration is forbidden")

    iterable_command, iterable_attempt, iterable_author, iterable_delivery, _, _ = graph()
    object.__setattr__(iterable_command, "_path_ceiling", ExplosiveIterable())
    hostile.append((
        iterable_command, iterable_attempt, iterable_author, iterable_delivery,
    ))

    external_calls = 0
    mapping_calls = 0
    original_external = semantic._external_value
    original_mapping = WorkerCommandV1.to_mapping

    def counted_external(value):
        nonlocal external_calls
        external_calls += 1
        return original_external(value)

    def counted_mapping(value):
        nonlocal mapping_calls
        mapping_calls += 1
        return original_mapping(value)

    monkeypatch.setattr(semantic, "_external_value", counted_external)
    monkeypatch.setattr(WorkerCommandV1, "to_mapping", counted_mapping)
    snapshots = []
    for command, attempt, author, delivery in hostile:
        before = (mapping_calls, external_calls)
        assert_sealed_failure(
            lambda: encode_wire_command_frame(
                command=command, delivery=delivery,
                attempt_fence=attempt, author_effect_fence=author,
            ),
            "invalid_field_value",
        )
        snapshots.append((mapping_calls - before[0], external_calls - before[1]))
    assert snapshots == [(0, 0)] * len(hostile)
    assert iterations == 0


def test_each_c2a_class_missing_and_wrong_slots_fail_before_generic_mapping(
    monkeypatch,
) -> None:
    consumed = (
        CeilingsV1, AttemptFenceV1, EffectFenceV1, WorkerCommandV1,
        DeliveryEnvelopeV1, WorkerObservationV1,
    )
    cases = []

    def copies(value, cls, *, missing: bool):
        result = object.__new__(cls)
        fields = cls._FIELDS[:-1] if missing else cls._FIELDS
        for field in fields:
            object.__setattr__(
                result, "_" + field,
                object.__getattribute__(value, "_" + field),
            )
        if not missing:
            object.__setattr__(result, "_" + cls._FIELDS[0], object())
        return result

    for missing in (True, False):
        command, attempt, author, delivery, _, _ = graph()
        bad = copies(command.effect_ceilings, CeilingsV1, missing=missing)
        object.__setattr__(command, "_effect_ceilings", bad)
        cases.append(lambda command=command, attempt=attempt, author=author,
                     delivery=delivery: encode_wire_command_frame(
            command=command, delivery=delivery, attempt_fence=attempt,
            author_effect_fence=author))

        command, attempt, author, delivery, _, _ = graph()
        bad = copies(attempt, AttemptFenceV1, missing=missing)
        cases.append(lambda command=command, bad=bad, author=author,
                     delivery=delivery: encode_wire_command_frame(
            command=command, delivery=delivery, attempt_fence=bad,
            author_effect_fence=author))

        command, attempt, author, delivery, _, _ = graph()
        bad = copies(author, EffectFenceV1, missing=missing)
        cases.append(lambda command=command, attempt=attempt, bad=bad,
                     delivery=delivery: encode_wire_command_frame(
            command=command, delivery=delivery, attempt_fence=attempt,
            author_effect_fence=bad))

        command, attempt, author, delivery, _, _ = graph()
        bad = copies(command, WorkerCommandV1, missing=missing)
        cases.append(lambda bad=bad, attempt=attempt, author=author,
                     delivery=delivery: encode_wire_command_frame(
            command=bad, delivery=delivery, attempt_fence=attempt,
            author_effect_fence=author))

        command, attempt, author, delivery, _, _ = graph()
        bad = copies(delivery, DeliveryEnvelopeV1, missing=missing)
        cases.append(lambda command=command, attempt=attempt, author=author,
                     bad=bad: encode_wire_command_frame(
            command=command, delivery=bad, attempt_fence=attempt,
            author_effect_fence=author))

        command, attempt, author, delivery, _, _ = graph()
        started = worker_observation(
            "worker_started", "observation.extract-matrix.started.0001")
        completed = worker_observation(
            "worker_completed", "observation.extract-matrix.completed.0001")
        bad = copies(started, WorkerObservationV1, missing=missing)
        result = object.__new__(RW0WireWorkerResultV1)
        object.__setattr__(result, "_observations", (bad, completed))
        cases.append(lambda result=result, command=command, delivery=delivery,
                     attempt=attempt, author=author: encode_wire_result_frame(
            result=result, command=command, delivery=delivery,
            attempt_fence=attempt, author_effect_fence=author))

    mapping_calls = 0
    external_calls = 0
    original_external = semantic._external_value

    def counted_external(value):
        nonlocal external_calls
        external_calls += 1
        return original_external(value)

    monkeypatch.setattr(semantic, "_external_value", counted_external)
    for cls in consumed:
        original = cls.to_mapping

        def counted_mapping(value, _original=original):
            nonlocal mapping_calls
            mapping_calls += 1
            return _original(value)

        monkeypatch.setattr(cls, "to_mapping", counted_mapping)

    snapshots = []
    for call in cases:
        before = (mapping_calls, external_calls)
        assert_sealed_failure(call, "invalid_field_value")
        snapshots.append((mapping_calls - before[0], external_calls - before[1]))
    assert snapshots == [(0, 0)] * len(cases)
