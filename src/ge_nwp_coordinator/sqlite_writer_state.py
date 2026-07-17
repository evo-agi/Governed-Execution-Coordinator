"""Internal SQLite writer-ownership row validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any

from ge_nwp_coordinator.models import require_contract_ref
from ge_nwp_coordinator.state_store import MAX_WRITER_GENERATION

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_RFC3339_UTC_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


@dataclass(frozen=True, repr=False)
class _DurableWriterIssuance:
    writer_ref: str
    generation: int
    issued_ref: str
    issuance_nonce_digest: str
    acquired_at: str

    def __repr__(self) -> str:
        return "<_DurableWriterIssuance>"


def _parse_writer_ownership_rows(rows: Any) -> _DurableWriterIssuance | None:
    if not isinstance(rows, list | tuple):
        raise ValueError("malformed writer ownership")
    if len(rows) > 1:
        raise ValueError("malformed writer ownership")
    if not rows:
        return None
    try:
        row = tuple(rows[0])
    except TypeError:
        raise ValueError("malformed writer ownership") from None
    if len(row) != 6:
        raise ValueError("malformed writer ownership")
    singleton_id, writer_ref, generation, issued_ref, issuance_nonce_digest, acquired_at = row
    if singleton_id != 1 or isinstance(singleton_id, bool):
        raise ValueError("malformed writer ownership")
    return _DurableWriterIssuance(
        writer_ref=_require_writer_ref(writer_ref),
        generation=_require_generation(generation),
        issued_ref=_require_issued_ref(issued_ref),
        issuance_nonce_digest=_require_sha256_digest(issuance_nonce_digest),
        acquired_at=_require_utc_timestamp(acquired_at),
    )


def _require_writer_ref(value: Any) -> str:
    return require_contract_ref(value, "writer_ref")


def _require_issued_ref(value: Any) -> str:
    return require_contract_ref(value, "issued_ref")


def _require_generation(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1 or value > MAX_WRITER_GENERATION:
        raise ValueError("invalid writer generation")
    return value


def _require_sha256_digest(value: Any) -> str:
    if not isinstance(value, str) or _SHA256_HEX_RE.fullmatch(value) is None:
        raise ValueError("invalid writer input")
    return value


def _require_utc_timestamp(value: Any) -> str:
    if not isinstance(value, str) or _RFC3339_UTC_Z_RE.fullmatch(value) is None:
        raise ValueError("invalid writer timestamp")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ValueError("invalid writer timestamp") from None
    return value
