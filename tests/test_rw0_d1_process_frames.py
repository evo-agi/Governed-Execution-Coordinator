from __future__ import annotations

import json
import struct

import pytest

from ge_nwp_coordinator._rw0_d1_process_frames import (
    D1FrameError, decode_planner_request, decode_planner_response,
    decode_worker_launch, encode_planner_request, encode_planner_response,
    encode_worker_launch,
)


REQUEST = {
    "objective": "Make one artificial change.",
    "requirements": ["Stay in scope."],
    "exclusions": ["No network."],
    "path_ordinals": [0, 1, 2],
    "action": "modify_authorized_path", "behavior": "normal",
}
RESPONSE = {
    "strategy": "Change one file.", "target_ordinal": 2,
    "action": "modify_authorized_path",
    "recommendation": "select_for_dispatch_gates",
    "reason": "plan.bounded_contract_change", "plan": "Change one contract test.",
}
LAUNCH = {
    "command_frame_b64": "QUJD", "attempt_fence": {}, "effect_fence": {},
    "target_ordinal": 2, "action": "modify_authorized_path",
    "behavior": "normal",
}


@pytest.mark.parametrize("value,encode,decode,magic", (
    (REQUEST, encode_planner_request, decode_planner_request, b"D1O1"),
    (RESPONSE, encode_planner_response, decode_planner_response, b"D1O1"),
    (LAUNCH, encode_worker_launch, decode_worker_launch, b"D1W1"),
))
def test_exact_canonical_frames(value, encode, decode, magic) -> None:
    frame = encode(value)
    assert frame[:4] == magic
    assert len(frame) == 8 + struct.unpack(">I", frame[4:8])[0]
    assert decode(frame) == value
    assert encode(decode(frame)) == frame
    for changed in (
        frame[:4] + frame[4:8] + frame[8:] + b"x",
        frame[:-1], b"BAD!" + frame[4:], frame + frame,
        frame[:4] + struct.pack(">I", 256 * 1024 + 1) + frame[8:],
    ):
        with pytest.raises(D1FrameError):
            decode(changed)


def test_duplicate_unknown_and_noncanonical_planner_keys_fail() -> None:
    raw = json.dumps(REQUEST, sort_keys=True, separators=(",", ":")).encode()
    duplicate = raw[:-1] + b',"objective":"again"}'
    unknown = raw[:-1] + b',"program_ref":"shadow"}'
    pretty = json.dumps(REQUEST).encode()
    for payload in (duplicate, unknown, pretty, b"{", b"\xef\xbb\xbf" + raw):
        frame = b"D1O1" + struct.pack(">I", len(payload)) + payload
        with pytest.raises(D1FrameError):
            decode_planner_request(frame)


def test_wrong_exact_types_and_oversize_fail_before_frame() -> None:
    for changed in (
        {**REQUEST, "path_ordinals": [False, 1, 2]},
        {**REQUEST, "requirements": ("Stay in scope.",)},
        {**REQUEST, "objective": "x" * 5000},
        {**REQUEST, "behavior": "unknown"},
    ):
        with pytest.raises(D1FrameError):
            encode_planner_request(changed)
    with pytest.raises(D1FrameError):
        encode_planner_response({**RESPONSE, "plan": "x" * 70000})
    with pytest.raises(D1FrameError):
        encode_worker_launch({**LAUNCH, "command_frame_b64": "x" * 190000})


@pytest.mark.parametrize("value,encode,decode,magic,field", (
    (REQUEST, encode_planner_request, decode_planner_request, b"D1O1", "action"),
    (REQUEST, encode_planner_request, decode_planner_request, b"D1O1", "behavior"),
    (RESPONSE, encode_planner_response, decode_planner_response, b"D1O1", "action"),
    (RESPONSE, encode_planner_response, decode_planner_response, b"D1O1", "recommendation"),
    (RESPONSE, encode_planner_response, decode_planner_response, b"D1O1", "target_ordinal"),
    (LAUNCH, encode_worker_launch, decode_worker_launch, b"D1W1", "action"),
    (LAUNCH, encode_worker_launch, decode_worker_launch, b"D1W1", "behavior"),
    (LAUNCH, encode_worker_launch, decode_worker_launch, b"D1W1", "target_ordinal"),
))
@pytest.mark.parametrize("wrong", ([], {}, False))
def test_canonical_wrong_enum_types_raise_only_frame_error(
    value, encode, decode, magic: bytes, field: str, wrong: object,
) -> None:
    changed = {**value, field: wrong}
    with pytest.raises(D1FrameError, match="^invalid_d1_frame$"):
        encode(changed)
    payload = json.dumps(changed, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode()
    frame = magic + struct.pack(">I", len(payload)) + payload
    with pytest.raises(D1FrameError, match="^invalid_d1_frame$"):
        decode(frame)
