"""Closed, bounded wire values for the one artificial D2 review-model child."""

from __future__ import annotations

import hashlib
import json
import re
import struct

__all__: tuple[str, ...] = ()

_MAGIC = b"D2M1"
_REQUEST_LIMIT = 256 * 1024 - 8
_RESPONSE_LIMIT = 64 * 1024
_REF = re.compile(r"[0-9A-Za-z][0-9A-Za-z.-]{0,95}\Z", re.ASCII)
_REASON = re.compile(r"[a-z][a-z0-9_]{0,95}\Z", re.ASCII)
_SHA = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_TIME = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z", re.ASCII)
_RECOMMENDATIONS = (
    "accept_candidate", "repair_candidate", "replan", "terminal_reject", "block",
)
_ROLES = (
    "candidate_capsule", "worker_result", "validation_result",
    "independent_review", "standing_policy", "risk_lane",
    "authority_currentness_attestation", "global_stop", "effect_ceiling",
)
_REQUEST_FIELDS = (
    "schema_id", "invocation_ref", "input_context", "evidence_supply",
    "input_digest",
)
_RESPONSE_FIELDS = (
    "schema_id", "invocation_ref", "input_digest", "input_context_ref",
    "input_context_digest", "supply_ref", "supply_digest", "recommendation",
    "reason_code", "findings", "completed_at", "record_digest",
)
_FINDING_FIELDS = (
    "finding_ref", "source_role", "source_value_ref", "source_value_digest",
    "reason_code",
)


class D2ReviewModelFrameError(ValueError):
    pass


def _fail() -> None:
    raise D2ReviewModelFrameError("invalid_d2_review_model_frame") from None


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in items:
        if type(name) is not str or name in result:
            _fail()
        result[name] = value
    return result


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        _fail()


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _ref(value: object) -> bool:
    return type(value) is str and _REF.fullmatch(value) is not None


def _reason(value: object) -> bool:
    return type(value) is str and _REASON.fullmatch(value) is not None


def _identity(domain: bytes, mapping: dict[str, object]) -> str:
    return hashlib.sha256(domain + b"\0" + _canonical(mapping)).hexdigest()


def _shape(kind: str, value: object) -> dict[str, object]:
    fields = _REQUEST_FIELDS if kind == "request" else _RESPONSE_FIELDS
    if type(value) is not dict or tuple(value) != fields:
        _fail()
    if (value["schema_id"] != f"governed-execution.nwp-d2-review-model-{kind}.v1"
            or not _ref(value["invocation_ref"]) or not _sha(value["input_digest"])):
        _fail()
    if kind == "request":
        context = value["input_context"]
        supply = value["evidence_supply"]
        if (type(context) is not dict or type(supply) is not dict
                or context.get("schema_id") != "governed-execution.nwp-post-execution-semantic-review-context.v1"
                or supply.get("schema_id") != "governed-execution.nwp-post-execution-evidence-supply.v2"
                or supply.get("input_context") != context
                or not _ref(context.get("input_context_ref"))
                or not _sha(context.get("input_context_digest"))
                or not _ref(supply.get("supply_ref"))
                or not _sha(supply.get("supply_digest"))
                or type(supply.get("role_supplies")) is not list
                or len(supply["role_supplies"]) != 9
                or tuple(entry.get("role") for entry in supply["role_supplies"]
                         if type(entry) is dict) != _ROLES
                or value["input_digest"] != _identity(
                    b"governed-execution.nwp-d2-review-model-input.v1.identity",
                    {"input_context": context, "evidence_supply": supply,
                     "invocation_ref": value["invocation_ref"]},
                )):
            _fail()
    else:
        if (not _ref(value["input_context_ref"])
                or not _sha(value["input_context_digest"])
                or not _ref(value["supply_ref"]) or not _sha(value["supply_digest"])
                or value["recommendation"] not in _RECOMMENDATIONS
                or not _reason(value["reason_code"])
                or type(value["findings"]) is not list
                or len(value["findings"]) > 8
                or type(value["completed_at"]) is not str
                or _TIME.fullmatch(value["completed_at"]) is None
                or not _sha(value["record_digest"])):
            _fail()
        seen: set[str] = set()
        ranks: list[int] = []
        for item in value["findings"]:
            if (type(item) is not dict or set(item) != set(_FINDING_FIELDS)
                    or not _ref(item["finding_ref"])
                    or item["finding_ref"] in seen
                    or item["source_role"] not in _ROLES
                    or not _ref(item["source_value_ref"])
                    or not _sha(item["source_value_digest"])
                    or not _reason(item["reason_code"])):
                _fail()
            seen.add(item["finding_ref"])
            ranks.append(_ROLES.index(item["source_role"]))
        if ranks != sorted(ranks):
            _fail()
        unsigned = {name: item for name, item in value.items()
                    if name != "record_digest"}
        if value["record_digest"] != _identity(
            b"governed-execution.nwp-d2-review-model-response.v1.identity", unsigned,
        ):
            _fail()
    return value


def _encode(kind: str, value: dict[str, object]) -> bytes:
    shaped = _shape(kind, value)
    payload = _canonical(shaped)
    if len(payload) > (_REQUEST_LIMIT if kind == "request" else _RESPONSE_LIMIT):
        _fail()
    return _MAGIC + struct.pack(">I", len(payload)) + payload


def _decode(kind: str, frame: object) -> dict[str, object]:
    limit = _REQUEST_LIMIT if kind == "request" else _RESPONSE_LIMIT
    if type(frame) is not bytes or len(frame) < 8 or frame[:4] != _MAGIC:
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
    # Canonical wire order is the frozen field order, not sorted JSON order.
    if type(value) is not dict or set(value) != set(_REQUEST_FIELDS if kind == "request" else _RESPONSE_FIELDS):
        _fail()
    value = {name: value[name] for name in
             (_REQUEST_FIELDS if kind == "request" else _RESPONSE_FIELDS)}
    shaped = _shape(kind, value)
    if _canonical(shaped) != payload:
        _fail()
    return shaped


def encode_model_request(value: dict[str, object]) -> bytes:
    return _encode("request", value)


def decode_model_request(frame: bytes) -> dict[str, object]:
    return _decode("request", frame)


def encode_model_response(value: dict[str, object]) -> bytes:
    if type(value) is not dict or set(value) != set(_RESPONSE_FIELDS[:-1]):
        _fail()
    unsigned = {name: value[name] for name in _RESPONSE_FIELDS if name != "record_digest"}
    return _encode("response", {**unsigned, "record_digest": _identity(
        b"governed-execution.nwp-d2-review-model-response.v1.identity", unsigned,
    )})


def decode_model_response(frame: bytes) -> dict[str, object]:
    return _decode("response", frame)


def model_input_digest(invocation_ref: str, context: dict[str, object],
                       supply: dict[str, object]) -> str:
    return _identity(
        b"governed-execution.nwp-d2-review-model-input.v1.identity",
        {"input_context": context, "evidence_supply": supply,
         "invocation_ref": invocation_ref},
    )
