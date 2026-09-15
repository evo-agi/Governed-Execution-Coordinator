"""Hostile-safe pure support for private Section 41 cognitive values.

This module performs no I/O and confers no authority.  It deliberately accepts
only exact built-in values before canonicalization or comparison.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
import typing
import unicodedata


__all__ = ()


SQLITE_INTEGER_MIN = -(2**63)
SQLITE_INTEGER_MAX = 2**63 - 1

_SAFE_REF_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z.-]{0,95}\Z", re.ASCII)
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z", re.ASCII)
_REASON_RE = re.compile(r"[a-z][a-z0-9_.-]{0,95}\Z", re.ASCII)
_UTC_SECOND_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z",
    re.ASCII,
)
_FORBIDDEN_REF_PREFIXES = (
    "connector-",
    "tunnel-",
    "workspace-",
    "org-",
    "organization-",
    "user-",
)
_EFFECT_CLASS_ORDER = (
    "author_candidate",
    "cancel_effect",
    "local_git_commit",
    "review_candidate",
    "validate_candidate",
)
_EFFECT_CLASS_JSON_MAX_BYTES = len(
    json.dumps(
        _EFFECT_CLASS_ORDER,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
)

_VIOLATION_REASONS = frozenset(
    {
        "cognitive_mutation_identity_invalid",
        "authority_observation_shape_invalid",
        "authority_observation_binding_mismatch",
        "authority_observation_version_invalid",
        "authority_observation_state_ineligible",
        "authority_observation_window_invalid",
        "preselection_timestamp_record_invalid",
        "preselection_timestamp_digest_mismatch",
        "preselection_chronology_invalid",
        "proposal_disposition_identity_collapse",
        "post_common_mapping_invalid",
        "authority_observation_expired",
        "attempt_fence_expired",
        "effect_fence_expired",
        "private_plan_narrative_invalid",
        "private_plan_nested_collection_invalid",
        "private_plan_closed_vocabulary_invalid",
        "private_plan_artifact_size_invalid",
        "private_plan_prerequisite_order_invalid",
        "private_plan_prerequisite_unreferenced",
        "private_plan_stop_unreferenced",
        "private_plan_validation_link_asymmetric",
        "private_plan_forward_dependency",
        "safe_projection_derivation_mismatch",
        "phase_algebra_mismatch",
        "canonical_value_invalid",
        "physical_family_missing_row",
        "physical_family_extra_row",
        "physical_family_row_digest_mismatch",
        "physical_family_graph_without_row",
        "physical_family_row_without_graph",
        "physical_family_receipt_in_graph",
        "physical_family_graph_digest_mismatch",
        "physical_family_order_mismatch",
        "physical_family_receipt_binding_mismatch",
        "physical_family_readiness_mismatch",
        "recovery_unresolved",
        "invalid_field_type",
        "invalid_field_value",
        "missing_field",
        "unknown_field",
        "relation_mismatch",
        "digest_mismatch",
    }
)
_VIOLATION_TOKEN = object()


class _CognitiveProposalContractViolation(ValueError):
    """Finite private contract failure with no hostile value in its payload."""

    __slots__ = ("_reason",)

    def __init__(self, *args: object, **kwargs: object) -> None:
        if (
            len(args) != 2
            or kwargs
            or args[0] is not _VIOLATION_TOKEN
            or type(args[1]) is not str
            or args[1] not in _VIOLATION_REASONS
        ):
            raise TypeError("construction disabled") from None
        object.__setattr__(self, "_reason", args[1])
        ValueError.__init__(self, args[1])

    @property
    def reason(self) -> str:
        return self._reason

    def __setattr__(self, name: str, value: object) -> typing.NoReturn:
        raise AttributeError("immutable")

    def __delattr__(self, name: str) -> typing.NoReturn:
        raise AttributeError("immutable")


def _violate(reason: str) -> typing.NoReturn:
    if type(reason) is not str or reason not in _VIOLATION_REASONS:
        reason = "canonical_value_invalid"
    raise _CognitiveProposalContractViolation(_VIOLATION_TOKEN, reason)


def _require_exact_mapping(
    value: object,
    fields: tuple[str, ...],
    reason: str = "invalid_field_type",
) -> dict[str, object]:
    if (
        type(fields) is not tuple
        or any(type(field) is not str for field in fields)
        or len(fields) != len(set(fields))
        or type(value) is not dict
    ):
        _violate(reason)
    mapping = typing.cast(dict[object, object], value)
    if any(type(key) is not str for key in mapping) or tuple(mapping) != fields:
        _violate(reason)
    return typing.cast(dict[str, object], mapping)


def _require_exact_tuple(
    value: object,
    *,
    minimum: int = 0,
    maximum: int = SQLITE_INTEGER_MAX,
    reason: str = "invalid_field_type",
) -> tuple[object, ...]:
    if type(value) is not tuple or not minimum <= len(value) <= maximum:
        _violate(reason)
    return typing.cast(tuple[object, ...], value)


def _require_exact_list(
    value: object,
    *,
    minimum: int = 0,
    maximum: int = SQLITE_INTEGER_MAX,
    reason: str = "invalid_field_type",
) -> list[object]:
    if type(value) is not list or not minimum <= len(value) <= maximum:
        _violate(reason)
    return typing.cast(list[object], value)


def _require_canonical_string(
    value: object,
    *,
    reason: str = "invalid_field_type",
    nfc: bool = True,
) -> str:
    if type(value) is not str:
        _violate(reason)
    result = typing.cast(str, value)
    if any(0xD800 <= ord(character) <= 0xDFFF for character in result):
        _violate(reason)
    if nfc and unicodedata.normalize("NFC", result) != result:
        _violate(reason)
    if any(ord(character) < 32 or ord(character) == 127 for character in result):
        _violate(reason)
    return result


def _require_safe_ref(value: object, reason: str = "invalid_field_value") -> str:
    result = _require_canonical_string(value, reason=reason)
    if _SAFE_REF_RE.fullmatch(result) is None or result.lower().startswith(
        _FORBIDDEN_REF_PREFIXES
    ):
        _violate(reason)
    return result


def _require_optional_safe_ref(
    value: object, reason: str = "invalid_field_value"
) -> str | None:
    if value is None:
        return None
    return _require_safe_ref(value, reason)


def _require_sha256(value: object, reason: str = "invalid_field_value") -> str:
    result = _require_canonical_string(value, reason=reason)
    if _SHA256_RE.fullmatch(result) is None:
        _violate(reason)
    return result


def _require_optional_sha256(
    value: object, reason: str = "invalid_field_value"
) -> str | None:
    if value is None:
        return None
    return _require_sha256(value, reason)


def _require_sha1(value: object, reason: str = "invalid_field_value") -> str:
    result = _require_canonical_string(value, reason=reason)
    if _SHA1_RE.fullmatch(result) is None:
        _violate(reason)
    return result


def _require_sqlite_integer(value: object, reason: str = "invalid_field_type") -> int:
    if type(value) is not int or not SQLITE_INTEGER_MIN <= value <= SQLITE_INTEGER_MAX:
        _violate(reason)
    return typing.cast(int, value)


def _require_nonnegative_integer(
    value: object, reason: str = "invalid_field_value"
) -> int:
    result = _require_sqlite_integer(value, reason)
    if result < 0:
        _violate(reason)
    return result


def _require_positive_integer(
    value: object, reason: str = "invalid_field_value"
) -> int:
    result = _require_sqlite_integer(value, reason)
    if result <= 0:
        _violate(reason)
    return result


def _require_utc_second(value: object, reason: str = "invalid_field_value") -> str:
    result = _require_canonical_string(value, reason=reason)
    if _UTC_SECOND_RE.fullmatch(result) is None or result[:4] == "0000":
        _violate(reason)
    parsed: datetime | None = None
    try:
        parsed = datetime.strptime(result, "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError, OverflowError):
        pass
    if parsed is None or parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != result:
        _violate(reason)
    return result


def _require_reason_code(value: object, reason: str = "invalid_field_value") -> str:
    result = _require_canonical_string(value, reason=reason)
    if _REASON_RE.fullmatch(result) is None:
        _violate(reason)
    return result


def _require_enum(
    value: object,
    vocabulary: tuple[str, ...],
    reason: str = "invalid_field_value",
) -> str:
    result = _require_canonical_string(value, reason=reason)
    if (
        type(vocabulary) is not tuple
        or any(type(item) is not str for item in vocabulary)
        or result not in vocabulary
    ):
        _violate(reason)
    return result


def _select_exact_type(
    candidate_type: object,
    trusted_types: tuple[type[object], ...],
) -> type[object] | None:
    """Select a trusted class without hashing or comparing the candidate."""

    for trusted_type in trusted_types:
        if candidate_type is trusted_type:
            return trusted_type
    return None


def _require_canonical_effect_class_json(
    value: object,
    reason: str = "invalid_field_value",
) -> tuple[str, ...]:
    """Reconstruct the closed, canonically encoded C2A effect-class list."""

    text = _require_canonical_string(value, reason=reason)
    if not text or len(text.encode("utf-8", errors="strict")) > _EFFECT_CLASS_JSON_MAX_BYTES:
        _violate(reason)

    decoded: object = None
    parse_failed = False
    try:
        decoded = json.loads(text)
    except (ValueError, RecursionError):
        parse_failed = True
    if parse_failed or type(decoded) is not list:
        _violate(reason)

    raw_members = typing.cast(list[object], decoded)
    if not raw_members:
        _violate(reason)
    checked_members = tuple(
        _require_canonical_string(member, reason=reason) for member in raw_members
    )
    if len(checked_members) != len(set(checked_members)):
        _violate(reason)

    canonical_members = tuple(
        effect_class
        for effect_class in _EFFECT_CLASS_ORDER
        if effect_class in checked_members
    )
    if checked_members != canonical_members:
        _violate(reason)
    canonical_text = json.dumps(
        checked_members,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    if text != canonical_text:
        _violate(reason)
    return checked_members


def _validate_canonical_value(value: object) -> None:
    active: set[int] = set()

    def visit(item: object) -> None:
        kind = type(item)
        if kind is str:
            _require_canonical_string(item, reason="canonical_value_invalid")
            return
        if kind is int:
            _require_sqlite_integer(item, "canonical_value_invalid")
            return
        if kind is bool or kind is type(None):
            return
        if kind is not dict and kind is not tuple:
            _violate("canonical_value_invalid")
        identity = id(item)
        if identity in active:
            _violate("canonical_value_invalid")
        active.add(identity)
        try:
            if kind is dict:
                mapping = typing.cast(dict[object, object], item)
                if any(type(key) is not str for key in mapping):
                    _violate("canonical_value_invalid")
                for key, member in mapping.items():
                    _require_canonical_string(key, reason="canonical_value_invalid")
                    visit(member)
            else:
                for member in typing.cast(tuple[object, ...], item):
                    visit(member)
        finally:
            active.discard(identity)

    visit(value)


def _canonical_bytes(value: object) -> bytes:
    result: bytes | None = None
    try:
        _validate_canonical_value(value)
        result = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8", errors="strict")
    except _CognitiveProposalContractViolation:
        raise
    except (Exception, RecursionError):
        pass
    if result is None:
        _violate("canonical_value_invalid")
    return result


def _domain_separated_digest(domain: str, value: object) -> str:
    checked = _require_canonical_string(domain, reason="canonical_value_invalid")
    if not checked:
        _violate("canonical_value_invalid")
    return hashlib.sha256(
        checked.encode("utf-8") + b"\x00" + _canonical_bytes(value)
    ).hexdigest()


def _without_field(mapping: dict[str, object], field: str) -> dict[str, object]:
    if type(mapping) is not dict or type(field) is not str or field not in mapping:
        _violate("canonical_value_invalid")
    return {name: value for name, value in mapping.items() if name != field}


def _exact_equal(left: object, right: object) -> bool:
    active: set[tuple[int, int]] = set()

    def compare(first: object, second: object) -> bool:
        if type(first) is not type(second):
            return False
        kind = type(second)
        if kind is dict or kind is tuple:
            pair = (id(first), id(second))
            if pair in active:
                return False
            active.add(pair)
            try:
                if kind is dict:
                    left_mapping = typing.cast(dict[object, object], first)
                    right_mapping = typing.cast(dict[object, object], second)
                    if (
                        any(type(key) is not str for key in left_mapping)
                        or any(type(key) is not str for key in right_mapping)
                        or tuple(left_mapping) != tuple(right_mapping)
                    ):
                        return False
                    return all(
                        compare(left_mapping[key], right_mapping[key])
                        for key in right_mapping
                    )
                left_tuple = typing.cast(tuple[object, ...], first)
                right_tuple = typing.cast(tuple[object, ...], second)
                return len(left_tuple) == len(right_tuple) and all(
                    compare(a, b) for a, b in zip(left_tuple, right_tuple, strict=True)
                )
            finally:
                active.discard(pair)
        if (
            kind is not str
            and kind is not int
            and kind is not bool
            and kind is not type(None)
        ):
            return False
        if kind is str:
            return str.__eq__(
                typing.cast(str, first), typing.cast(str, second)
            ) is True
        if kind is int:
            return int.__eq__(
                typing.cast(int, first), typing.cast(int, second)
            ) is True
        return first is second

    try:
        return compare(left, right)
    except (Exception, RecursionError):
        return False


def _constant_repr(value: object) -> str:
    return f"<{type(value).__name__}>"


def _disable_pickle(self: object, protocol: object = None) -> typing.NoReturn:
    raise TypeError("pickling disabled")
