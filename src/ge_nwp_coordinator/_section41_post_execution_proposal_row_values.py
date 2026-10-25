"""Exact private immutable rows for the two Section 41 post proposal tables."""

from __future__ import annotations

from dataclasses import make_dataclass
from datetime import datetime, timezone
import typing

from ._cognitive_proposal_value_support import _require_safe_ref, _require_sha256
from ._post_execution_evidence_values import _domain_separated_digest
from ._section41_post_execution_proposal_mutation_contracts import (
    _PHASE, _RECEIPT_DOMAIN, checked_safe_basis_bytes, safe_basis_digest,
)

__all__: tuple[str, ...] = ()

_CONTEXT_TABLE = "development_post_execution_proposal_contexts"
_RECEIPT_TABLE = "development_post_execution_proposal_receipts"
_CONTEXT_SCHEMA = "governed-execution.nwp-section41-post-execution-proposal-context-row.v1"
_RECEIPT_SCHEMA = "governed-execution.nwp-section41-post-execution-proposal-receipt-row.v1"
_CONTEXT_DOMAIN = _CONTEXT_SCHEMA + ".identity"
_CONTEXT_COLUMNS = (
    "schema_id", "proposal_phase", "context_ref", "context_digest",
    "proposal_ref", "proposal_digest", "phase_basis_ref", "phase_basis_digest",
    "safe_basis_bytes", "safe_basis_digest", "context_row_digest",
)
_RECEIPT_COLUMNS = (
    "schema_id", "mutation_ref", "mutation_command_digest", "proposal_phase",
    "context_ref", "context_digest", "proposal_ref", "proposal_digest",
    "phase_basis_ref", "phase_basis_digest", "source_invocation_ref",
    "source_invocation_digest", "artifact_ref", "artifact_digest",
    "artifact_binding_digest", "evidence_set_ref", "evidence_set_digest",
    "safe_basis_digest", "c1_mutation_ref", "c1_membership_ref",
    "mutation_graph_digest", "committed_result_digest", "committed_outcome",
    "committed_at", "receipt_digest",
)
_COLUMNS = {_CONTEXT_TABLE: _CONTEXT_COLUMNS, _RECEIPT_TABLE: _RECEIPT_COLUMNS}
_REFS = frozenset((
    "context_ref", "proposal_ref", "phase_basis_ref", "mutation_ref",
    "source_invocation_ref", "artifact_ref", "evidence_set_ref",
    "c1_mutation_ref", "c1_membership_ref",
))


def _invalid() -> typing.NoReturn:
    raise ValueError("invalid_post_execution_proposal_row") from None


def _validate_row(table: str, value: object) -> None:
    cols = _COLUMNS[table]
    raw = {name: getattr(value, name) for name in cols}
    if (type(raw["schema_id"]) is not str
            or raw["schema_id"] != (_CONTEXT_SCHEMA if table == _CONTEXT_TABLE else _RECEIPT_SCHEMA)
            or type(raw["proposal_phase"]) is not str
            or raw["proposal_phase"] != _PHASE):
        _invalid()
    try:
        for name, member in raw.items():
            if name in _REFS:
                _require_safe_ref(member)
            elif name.endswith("_digest"):
                _require_sha256(member)
        if table == _CONTEXT_TABLE:
            if type(raw["safe_basis_bytes"]) is not bytes:
                _invalid()
            if checked_safe_basis_bytes(raw["safe_basis_bytes"]) != raw["safe_basis_bytes"]:
                _invalid()
            if raw["safe_basis_digest"] != safe_basis_digest(raw["safe_basis_bytes"]):
                _invalid()
        else:
            if (type(raw["committed_outcome"]) is not str
                    or raw["committed_outcome"] != "proposal_recorded"):
                _invalid()
            time = raw["committed_at"]
            if (type(time) is not str or len(time) != 20
                    or datetime.fromisoformat(time.replace("Z", "+00:00")).astimezone(
                        timezone.utc
                    ).strftime("%Y-%m-%dT%H:%M:%SZ") != time):
                _invalid()
        digest_field = cols[-1]
        identity = {name: raw[name] for name in cols if name != digest_field}
        # Canonical JSON cannot carry bytes; the context digest commits to
        # the separately domain-hashed canonical safe basis, not a second
        # serialization of its BLOB.
        if table == _CONTEXT_TABLE:
            identity.pop("safe_basis_bytes")
        expected = _domain_separated_digest(
            _CONTEXT_DOMAIN if table == _CONTEXT_TABLE else _RECEIPT_DOMAIN,
            identity,
        )
        if raw[digest_field] != expected:
            _invalid()
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        _invalid()


def _make_row(name: str, table: str) -> type:
    columns = _COLUMNS[table]
    def post_init(self: object) -> None:
        _validate_row(table, self)
    def to_mapping(self: object) -> dict[str, object]:
        _validate_row(table, self)
        return {column: getattr(self, column) for column in columns}
    def as_tuple(self: object) -> tuple[object, ...]:
        _validate_row(table, self)
        return tuple(getattr(self, column) for column in columns)
    return make_dataclass(
        name, [(column, object) for column in columns],
        frozen=True, slots=True, repr=False,
        namespace={"__post_init__": post_init, "to_mapping": to_mapping,
                   "as_tuple": as_tuple, "__reduce__": lambda self: _invalid()},
    )


PostExecutionProposalContextRowV1 = _make_row(
    "PostExecutionProposalContextRowV1", _CONTEXT_TABLE,
)
PostExecutionProposalReceiptRowV1 = _make_row(
    "PostExecutionProposalReceiptRowV1", _RECEIPT_TABLE,
)


def row_from_mapping(table: str, mapping: object) -> object:
    if table not in _COLUMNS or type(mapping) is not dict:
        _invalid()
    columns = _COLUMNS[table]
    if frozenset(mapping) != frozenset(columns):
        _invalid()
    cls = (PostExecutionProposalContextRowV1
           if table == _CONTEXT_TABLE else PostExecutionProposalReceiptRowV1)
    return cls(**{name: mapping[name] for name in columns})


def row_from_tuple(table: str, raw: object) -> object:
    if (table not in _COLUMNS or type(raw) is not tuple
            or len(raw) != len(_COLUMNS[table])):
        _invalid()
    return row_from_mapping(table, dict(zip(_COLUMNS[table], raw, strict=True)))


def seal_row(table: str, identity: dict[str, object]) -> object:
    if table not in _COLUMNS or type(identity) is not dict:
        _invalid()
    columns = _COLUMNS[table]
    digest_field = columns[-1]
    if frozenset(identity) != frozenset(columns[:-1]):
        _invalid()
    preimage = {name: identity[name] for name in columns[:-1]}
    if table == _CONTEXT_TABLE:
        preimage.pop("safe_basis_bytes")
    digest = _domain_separated_digest(
        _CONTEXT_DOMAIN if table == _CONTEXT_TABLE else _RECEIPT_DOMAIN,
        preimage,
    )
    return row_from_mapping(table, {**identity, digest_field: digest})
