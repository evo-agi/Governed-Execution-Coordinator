"""Closed frames for the two artificial D2 checking children."""

from __future__ import annotations

import hashlib
import json
import re
import struct

__all__: tuple[str, ...] = ()

_MAGICS = {"validator": b"D2V1", "reviewer": b"D2R1"}
_REQUEST_LIMIT = 256 * 1024
_RESPONSE_LIMIT = 64 * 1024
_PATHS = (
    ".docs/system_overview/hybrid_integration_architecture_adr.md",
    "PLANS.md",
    "docs_contract_test.go",
)
_REF = re.compile(r"[0-9A-Za-z][0-9A-Za-z.-]{0,95}\Z", re.ASCII)
_REASON = re.compile(r"[a-z][a-z0-9_]{0,95}\Z", re.ASCII)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_TIME = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z", re.ASCII)
_REQUEST_FIELDS = (
    "schema_id", "role", "invocation_ref", "command_digest",
    "effect_intent_ref", "effect_fence_ref", "effect_fence_digest",
    "delivery_attempt_ref", "capsule_manifest_ref", "portable_capsule_digest",
    "requirement_ref", "requirement_safe_digest", "files",
)
_RESPONSE_FIELDS = (
    "schema_id", "role", "invocation_ref", "command_digest",
    "effect_fence_ref", "effect_fence_digest", "delivery_attempt_ref",
    "capsule_manifest_ref", "portable_capsule_digest", "outcome",
    "reason_code", "source_ref", "evidence_ref", "observed_at",
    "file_digests", "record_digest",
)


class D2CheckingFrameError(ValueError):
    """Content-free closed-frame refusal."""


def _fail() -> None:
    raise D2CheckingFrameError("invalid_d2_checking_frame")


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if type(key) is not str or key in result:
            _fail()
        result[key] = value
    return result


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        _fail()


def _digest(value: dict[str, object]) -> str:
    return hashlib.sha256(
        b"governed-execution.nwp-d2-checking-source-record.v1.identity\0"
        + _canonical(value)
    ).hexdigest()


def _safe_ref(value: object) -> bool:
    return type(value) is str and _REF.fullmatch(value) is not None


def _sha(value: object) -> bool:
    return type(value) is str and _DIGEST.fullmatch(value) is not None


def _shape(role: str, kind: str, value: object) -> dict[str, object]:
    if role not in _MAGICS or type(value) is not dict:
        _fail()
    fields = _REQUEST_FIELDS if kind == "request" else _RESPONSE_FIELDS
    if set(value) != set(fields) or any(type(key) is not str for key in value):
        _fail()
    if (value["schema_id"] != f"governed-execution.nwp-d2-{role}-{kind}.v1"
            or value["role"] != role or not _safe_ref(value["invocation_ref"])
            or not _sha(value["command_digest"])
            or not _safe_ref(value["effect_fence_ref"])
            or not _sha(value["effect_fence_digest"])
            or not _safe_ref(value["delivery_attempt_ref"])
            or not _safe_ref(value["capsule_manifest_ref"])
            or not _sha(value["portable_capsule_digest"])):
        _fail()
    if kind == "request":
        if (not _safe_ref(value["effect_intent_ref"])
                or not _safe_ref(value["requirement_ref"])
                or not _sha(value["requirement_safe_digest"])):
            _fail()
        files = value["files"]
        if type(files) is not list or len(files) != 3:
            _fail()
        for expected, entry in zip(_PATHS, files, strict=True):
            if (type(entry) is not dict or set(entry) != {"path", "length", "sha256"}
                    or entry["path"] != expected or type(entry["length"]) is not int
                    or not 0 <= entry["length"] <= 1_048_576
                    or not _sha(entry["sha256"])):
                _fail()
    else:
        if (value["outcome"] not in ("passed", "failed", "inconclusive")
                or type(value["reason_code"]) is not str
                or _REASON.fullmatch(value["reason_code"]) is None
                or not _safe_ref(value["source_ref"])
                or not _safe_ref(value["evidence_ref"])
                or type(value["observed_at"]) is not str
                or _TIME.fullmatch(value["observed_at"]) is None
                or type(value["file_digests"]) is not list
                or len(value["file_digests"]) != 3
                or any(not _sha(item) for item in value["file_digests"])
                or not _sha(value["record_digest"])):
            _fail()
        unsigned = {key: item for key, item in value.items() if key != "record_digest"}
        if value["record_digest"] != _digest(unsigned):
            _fail()
    return value


def _encode(role: str, kind: str, value: dict[str, object]) -> bytes:
    shaped = _shape(role, kind, value)
    payload = _canonical(shaped)
    if len(payload) > (_REQUEST_LIMIT if kind == "request" else _RESPONSE_LIMIT):
        _fail()
    return _MAGICS[role] + struct.pack(">I", len(payload)) + payload


def _decode(role: str, kind: str, frame: object) -> dict[str, object]:
    limit = _REQUEST_LIMIT if kind == "request" else _RESPONSE_LIMIT
    if type(frame) is not bytes or len(frame) < 8 or frame[:4] != _MAGICS[role]:
        _fail()
    length = struct.unpack(">I", frame[4:8])[0]
    if length > limit or len(frame) != 8 + length:
        _fail()
    payload = frame[8:]
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=lambda _ignored: _fail())
    except (ValueError, UnicodeError, TypeError):
        _fail()
    shaped = _shape(role, kind, value)
    if _canonical(shaped) != payload:
        _fail()
    return shaped


def encode_checking_request(role: str, value: dict[str, object]) -> bytes:
    return _encode(role, "request", value)


def decode_checking_request(role: str, frame: bytes) -> dict[str, object]:
    return _decode(role, "request", frame)


def encode_checking_response(role: str, value: dict[str, object]) -> bytes:
    unsigned = {key: item for key, item in value.items() if key != "record_digest"}
    return _encode(role, "response", {**unsigned, "record_digest": _digest(unsigned)})


def decode_checking_response(role: str, frame: bytes) -> dict[str, object]:
    return _decode(role, "response", frame)
