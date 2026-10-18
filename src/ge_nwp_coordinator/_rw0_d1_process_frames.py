"""Closed, private frames for the artificial RW0-D1 child processes."""

from __future__ import annotations

import json
import struct


_PLANNER_MAGIC = b"D1O1"
_WORKER_MAGIC = b"D1W1"
_PLANNER_REQUEST_LIMIT = 256 * 1024
_PLANNER_RESPONSE_LIMIT = 64 * 1024
_WORKER_REQUEST_LIMIT = 256 * 1024
_ACTIONS = frozenset({"modify_authorized_path"})
_BEHAVIORS = frozenset({
    "normal", "malformed", "oversized", "trailing", "nonzero", "timeout",
    "stderr_limit", "missing_candidate", "extra_path", "unsafe_path", "defer",
})


class D1FrameError(ValueError):
    """Content-free private frame failure."""


def _fail() -> None:
    raise D1FrameError("invalid_d1_frame")


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if type(key) is not str or key in result:
            _fail()
        result[key] = value
    return result


def _shape(kind: str, value: object) -> dict[str, object]:
    if type(value) is not dict or any(type(k) is not str for k in value):
        _fail()
    fields: dict[str, tuple[str, ...]] = {
        "planner_request": (
            "objective", "requirements", "exclusions", "path_ordinals",
            "action", "behavior",
        ),
        "planner_response": (
            "strategy", "target_ordinal", "action", "recommendation",
            "reason", "plan",
        ),
        "worker_launch": (
            "command_frame_b64", "attempt_fence", "effect_fence",
            "target_ordinal", "action", "behavior",
        ),
    }
    if set(value) != set(fields[kind]):
        _fail()
    result = value
    if kind == "planner_request":
        if (type(result["objective"]) is not str
                or not 1 <= len(result["objective"]) <= 4096):
            _fail()
        for name in ("requirements", "exclusions"):
            items = result[name]
            if (type(items) is not list or not 1 <= len(items) <= 16
                    or any(type(item) is not str or not 1 <= len(item) <= 1024
                           for item in items)):
                _fail()
        if (type(result["path_ordinals"]) is not list
                or result["path_ordinals"] != [0, 1, 2]
                or any(type(item) is not int for item in result["path_ordinals"])):
            _fail()
    elif kind == "planner_response":
        for name, bound in (("strategy", 512), ("reason", 256), ("plan", 4096)):
            if type(result[name]) is not str or not 1 <= len(result[name]) <= bound:
                _fail()
        if (type(result["recommendation"]) is not str
                or result["recommendation"] not in ("select_for_dispatch_gates", "defer")):
            _fail()
    else:
        if (type(result["command_frame_b64"]) is not str
                or not 1 <= len(result["command_frame_b64"]) <= 180_000):
            _fail()
        for name in ("attempt_fence", "effect_fence"):
            if type(result[name]) is not dict:
                _fail()
    if kind != "planner_request":
        if type(result["target_ordinal"]) is not int or result["target_ordinal"] not in (0, 1, 2):
            _fail()
    if type(result["action"]) is not str or result["action"] not in _ACTIONS:
        _fail()
    if kind != "planner_response":
        if type(result["behavior"]) is not str or result["behavior"] not in _BEHAVIORS:
            _fail()
    return result


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        _fail()


def _encode(value: object, kind: str, magic: bytes, limit: int) -> bytes:
    shaped = _shape(kind, value)
    payload = _canonical(shaped)
    if len(payload) > limit:
        _fail()
    return magic + struct.pack(">I", len(payload)) + payload


def _decode(frame: object, kind: str, magic: bytes, limit: int) -> dict[str, object]:
    if type(frame) is not bytes or len(frame) < 8 or frame[:4] != magic:
        _fail()
    length = struct.unpack(">I", frame[4:8])[0]
    if length > limit or len(frame) != 8 + length:
        _fail()
    payload = frame[8:]
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=lambda _value: _fail())
    except (ValueError, UnicodeError, TypeError):
        _fail()
    shaped = _shape(kind, value)
    if _canonical(shaped) != payload:
        _fail()
    return shaped


def encode_planner_request(value: dict[str, object]) -> bytes:
    return _encode(value, "planner_request", _PLANNER_MAGIC, _PLANNER_REQUEST_LIMIT)


def decode_planner_request(frame: bytes) -> dict[str, object]:
    return _decode(frame, "planner_request", _PLANNER_MAGIC, _PLANNER_REQUEST_LIMIT)


def encode_planner_response(value: dict[str, object]) -> bytes:
    return _encode(value, "planner_response", _PLANNER_MAGIC, _PLANNER_RESPONSE_LIMIT)


def decode_planner_response(frame: bytes) -> dict[str, object]:
    return _decode(frame, "planner_response", _PLANNER_MAGIC, _PLANNER_RESPONSE_LIMIT)


def encode_worker_launch(value: dict[str, object]) -> bytes:
    return _encode(value, "worker_launch", _WORKER_MAGIC, _WORKER_REQUEST_LIMIT)


def decode_worker_launch(frame: bytes) -> dict[str, object]:
    return _decode(frame, "worker_launch", _WORKER_MAGIC, _WORKER_REQUEST_LIMIT)
