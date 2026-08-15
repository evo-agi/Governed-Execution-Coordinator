"""Shared pure mechanics for private C2B2 durable row values.

This module deliberately performs no I/O and confers no durable, execution,
or external authority.  Its helpers are implementation details of the three
private row-family owner modules.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import typing

from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode


__all__: tuple[str, ...] = ()


_SAFE_REF_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]*\Z")
_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_GIT_SHA1_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
_REASON_CODE_PATTERN = re.compile(r"[a-z][a-z0-9_.-]*\Z")
_RESERVED_SAFE_REF_PREFIXES = (
    "connector-",
    "tunnel-",
    "workspace-",
    "org-",
    "organization-",
    "user-",
)
_FIXED_SAFE_PATHS = (
    ".docs/system_overview/hybrid_integration_architecture_adr.md",
    "PLANS.md",
    "docs_contract_test.go",
)
_FIXED_SAFE_PATHS_JSON = (
    '[".docs/system_overview/hybrid_integration_architecture_adr.md",'
    '"PLANS.md","docs_contract_test.go"]'
)
_EFFECT_CLASSES = (
    "author_candidate",
    "cancel_effect",
    "local_git_commit",
    "review_candidate",
    "validate_candidate",
)


class _RowValueValidationError(ValueError):
    """Content-free internal marker for expected pure validation failures."""

    __slots__ = ()


def _fail_validation() -> typing.NoReturn:
    raise _RowValueValidationError() from None


def _new_database_integrity_error() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(
        SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
    )


def _require_exact_string(value: object) -> str:
    if type(value) is not str:
        _fail_validation()
    return typing.cast(str, value)


def _require_nonempty_string(value: object) -> str:
    result = _require_exact_string(value)
    if not result:
        _fail_validation()
    return result


def _require_constant_string(value: object, expected: str) -> str:
    result = _require_exact_string(value)
    if result != expected:
        _fail_validation()
    return result


def _require_safe_ref(value: object) -> str:
    result = _require_exact_string(value)
    if not 1 <= len(result) <= 96:
        _fail_validation()
    if _SAFE_REF_PATTERN.fullmatch(result) is None:
        _fail_validation()
    if result.lower().startswith(_RESERVED_SAFE_REF_PREFIXES):
        _fail_validation()
    return result


def _require_optional_safe_ref(value: object) -> str | None:
    if value is None:
        return None
    return _require_safe_ref(value)


def _require_sha256(value: object) -> str:
    result = _require_exact_string(value)
    if _DIGEST_PATTERN.fullmatch(result) is None:
        _fail_validation()
    return result


def _require_optional_sha256(value: object) -> str | None:
    if value is None:
        return None
    return _require_sha256(value)


def _require_git_object_format(value: object) -> str:
    return _require_constant_string(value, "sha1")


def _require_git_oid(value: object) -> str:
    result = _require_exact_string(value)
    if _GIT_SHA1_PATTERN.fullmatch(result) is None:
        _fail_validation()
    return result


def _require_nonnegative_integer(value: object) -> int:
    if type(value) is not int:
        _fail_validation()
    result = typing.cast(int, value)
    if result < 0:
        _fail_validation()
    return result


def _require_optional_nonnegative_integer(value: object) -> int | None:
    if value is None:
        return None
    return _require_nonnegative_integer(value)


def _require_positive_integer(value: object) -> int:
    if type(value) is not int:
        _fail_validation()
    result = typing.cast(int, value)
    if result < 1:
        _fail_validation()
    return result


def _require_optional_positive_integer(value: object) -> int | None:
    if value is None:
        return None
    return _require_positive_integer(value)


def _require_enum(value: object, allowed: tuple[str, ...]) -> str:
    result = _require_exact_string(value)
    if result not in allowed:
        _fail_validation()
    return result


def _require_optional_enum(
    value: object,
    allowed: tuple[str, ...],
) -> str | None:
    if value is None:
        return None
    return _require_enum(value, allowed)


def _require_reason_code(value: object) -> str:
    result = _require_exact_string(value)
    if not 1 <= len(result) <= 96:
        _fail_validation()
    if _REASON_CODE_PATTERN.fullmatch(result) is None:
        _fail_validation()
    return result


def _require_utc_timestamp(value: object) -> str:
    result = _require_exact_string(value)
    if len(result) != 20:
        _fail_validation()
    if (
        result[4] != "-"
        or result[7] != "-"
        or result[10] != "T"
        or result[13] != ":"
        or result[16] != ":"
        or result[19] != "Z"
        or not (
            result[0:4]
            + result[5:7]
            + result[8:10]
            + result[11:13]
            + result[14:16]
            + result[17:19]
        ).isdigit()
    ):
        _fail_validation()
    try:
        parsed = datetime.datetime(
            int(result[0:4]),
            int(result[5:7]),
            int(result[8:10]),
            int(result[11:13]),
            int(result[14:16]),
            int(result[17:19]),
            tzinfo=datetime.timezone.utc,
        )
    except ValueError:
        _fail_validation()
    rendered = (
        f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}T"
        f"{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}Z"
    )
    if rendered != result:
        _fail_validation()
    return result


def _require_optional_utc_timestamp(value: object) -> str | None:
    if value is None:
        return None
    return _require_utc_timestamp(value)


def _decode_fixed_paths_json(value: object) -> tuple[str, ...]:
    result = _require_exact_string(value)
    if result != _FIXED_SAFE_PATHS_JSON:
        _fail_validation()
    return _FIXED_SAFE_PATHS


def _require_fixed_paths(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        _fail_validation()
    result = typing.cast(tuple[object, ...], value)
    if result != _FIXED_SAFE_PATHS or any(type(item) is not str for item in result):
        _fail_validation()
    return _FIXED_SAFE_PATHS


def _encode_fixed_paths(value: tuple[str, ...]) -> str:
    if type(value) is not tuple or value != _FIXED_SAFE_PATHS:
        _fail_validation()
    return _FIXED_SAFE_PATHS_JSON


def _decode_effect_class_mask(value: object) -> tuple[str, ...]:
    mask = _require_positive_integer(value)
    if mask > 31:
        _fail_validation()
    return tuple(
        effect_class
        for bit, effect_class in enumerate(_EFFECT_CLASSES)
        if mask & (1 << bit)
    )


def _encode_effect_class_mask(value: tuple[str, ...]) -> int:
    if type(value) is not tuple or not value:
        _fail_validation()
    if any(type(item) is not str for item in value):
        _fail_validation()
    expected = tuple(item for item in _EFFECT_CLASSES if item in value)
    if value != expected or len(set(value)) != len(value):
        _fail_validation()
    mask = 0
    for bit, effect_class in enumerate(_EFFECT_CLASSES):
        if effect_class in value:
            mask |= 1 << bit
    return mask


def _canonical_identity_bytes(identity: dict[str, object]) -> bytes:
    if type(identity) is not dict or any(type(key) is not str for key in identity):
        _fail_validation()
    try:
        return json.dumps(
            identity,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeError):
        _fail_validation()


def _domain_separated_digest(domain: str, identity: dict[str, object]) -> str:
    if type(domain) is not str or not domain:
        _fail_validation()
    try:
        prefix = domain.encode("utf-8", errors="strict")
    except UnicodeError:
        _fail_validation()
    return hashlib.sha256(prefix + b"\x00" + _canonical_identity_bytes(identity)).hexdigest()


def _require_matching_digest(
    *,
    domain: str,
    identity: dict[str, object],
    stored_digest: object,
) -> str:
    result = _require_sha256(stored_digest)
    if result != _domain_separated_digest(domain, identity):
        _fail_validation()
    return result


def _row_tuple_to_private_mapping(
    *,
    columns: tuple[str, ...],
    row: object,
) -> dict[str, object]:
    if type(columns) is not tuple:
        _fail_validation()
    if type(row) is not tuple:
        _fail_validation()
    values = typing.cast(tuple[object, ...], row)
    if len(values) != len(columns):
        _fail_validation()
    if any(type(column) is not str for column in columns):
        _fail_validation()
    if len(set(columns)) != len(columns):
        _fail_validation()
    return dict(zip(columns, values, strict=True))


class _ImmutableValue:
    """Mechanics-only base for manually defined private immutable values."""

    __slots__ = ()
    __hash__ = None

    def __new__(cls, *args: object, **kwargs: object) -> typing.NoReturn:
        raise TypeError("construction disabled")

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("construction disabled")

    def __setattr__(self, name: str, value: object) -> typing.NoReturn:
        raise AttributeError("immutable")

    def __delattr__(self, name: str) -> typing.NoReturn:
        raise AttributeError("immutable")

    def __repr__(self) -> str:
        return f"<{type(self).__name__}>"

    __str__ = __repr__

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return object.__getattribute__(self, "_values") == object.__getattribute__(
            other, "_values"
        )

    def __copy__(self) -> _ImmutableValue:
        return self

    def __deepcopy__(self, memo: object) -> _ImmutableValue:
        return self

    def __reduce__(self) -> typing.NoReturn:
        raise TypeError("pickling disabled")

    def __reduce_ex__(self, protocol: int) -> typing.NoReturn:
        raise TypeError("pickling disabled")
