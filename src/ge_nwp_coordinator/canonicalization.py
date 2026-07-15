"""Deterministic JSON canonicalization helpers.

Canonical arrays preserve caller order unless a schema field is explicitly
documented as set-like. Set-like string arrays use this duplicate rule: values
must be strings, duplicates are rejected before sorting, and canonical order is
lexicographic by the exact string value.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping


class CanonicalizationError(ValueError):
    """Raised when a value cannot be represented in the Coordinator canonical form."""


def to_primitive(value: Any) -> Any:
    """Convert supported Python objects to deterministic JSON primitives."""

    if is_dataclass(value):
        return to_primitive(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        converted: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError("canonical object keys must be strings")
            converted[key] = to_primitive(item)
        return converted
    if isinstance(value, tuple | list):
        return [to_primitive(item) for item in value]
    if isinstance(value, str | int | bool) or value is None:
        return value
    raise CanonicalizationError(f"unsupported canonical primitive: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Return UTF-8 encoded, sorted-key, compact JSON canonical bytes."""

    primitive = to_primitive(value)
    return json.dumps(
        primitive,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return the SHA-256 hex digest over canonical JSON bytes."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def require_string(value: Any, field_name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must be non-empty")
    return value


def require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def require_non_negative_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def require_positive_int(value: Any, field_name: str) -> int:
    value = require_non_negative_int(value, field_name)
    if value < 1:
        raise ValueError(f"{field_name} must be greater than zero")
    return value


def require_string_tuple(value: Any, field_name: str, *, ordered: bool = True) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        raise ValueError(f"{field_name} must be an array")
    items = tuple(require_string(item, f"{field_name}[]") for item in value)
    if ordered:
        return items
    return normalize_set_like_strings(items, field_name)


def normalize_set_like_strings(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        require_string(value, field_name)
        if value in seen:
            raise ValueError(f"{field_name} contains duplicate value {value!r}")
        seen.add(value)
        result.append(value)
    return tuple(sorted(result))


def require_object(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    for key in value:
        if not isinstance(key, str):
            raise ValueError(f"{field_name} keys must be strings")
    return dict(value)
