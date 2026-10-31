"""Exact private row tuples for the four immutable terminal tables."""
from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from ._rw0_terminal_outcome_contracts import (
    CONTEXT_SCHEMA, OUTCOME_SCHEMA, RESULT_SCHEMA, RECEIPT_SCHEMA,
    GRAPH_PROFILE, PROFILE, RW0TerminalOutcomeV2, _canonical, _digest,
    _exact, _head, _identity_digest, _safe_ref, _sha, _stop, _strict_bytes,
    _time, HEAD_ROLES, NORMAL_PAIRS,
)
from ._rw0_terminal_head_witness import (
    WITNESS_BYTE_CEILING, witness_from_bytes,
)

__all__: tuple[str, ...] = ()

CONTEXT = "rw0_terminal_contexts"
OUTCOME = "rw0_terminal_outcomes"
RESULT = "rw0_terminal_results"
RECEIPT = "rw0_terminal_receipts"
TABLES = (CONTEXT, OUTCOME, RESULT, RECEIPT)
COLUMNS = {
    CONTEXT: (
        "schema_id", "context_ref", "profile", "mutation_ref",
        "phase_basis_ref", "phase_basis_digest", "program_ref", "lineage_ref",
        "scope_ref", "p0_act_ref", "p0_act_digest", "p0_fact_ref",
        "p0_fact_digest", "section41_context_ref", "section41_context_digest",
        "section41_proposal_ref", "section41_proposal_digest",
        "section41_receipt_mutation_ref", "section41_receipt_digest",
        "evidence_set_ref", "evidence_set_digest", "c1_membership_ref",
        "c1_membership_digest", "c1_receipt_digest", "p1_basis_ref",
        "p1_basis_digest", "p1_decision_ref", "p1_decision_digest",
        "p1_decision_kind", "p1_result_ref", "p1_result_digest",
        "p1_receipt_mutation_ref", "p1_receipt_graph_digest",
        "p1_receipt_digest_anchor", "acceptance_fact_ref",
        "acceptance_fact_digest", "command_safe_bytes",
        "reached_owner_manifest_bytes", "closure_heads_bytes",
        "closure_stop_bytes", "recorded_at", "context_digest",
    ),
    OUTCOME: (
        "schema_id", "outcome_value_ref", "context_ref", "context_digest",
        "phase_basis_ref", "phase_basis_digest", "branch", "outcome",
        "decision_ref", "decision_digest", "decision_kind",
        "guarded_result_ref", "guarded_result_digest",
        "p1_receipt_mutation_ref", "p1_receipt_graph_digest",
        "closure_heads_bytes", "closure_stop_bytes", "evidence_set_ref",
        "evidence_set_digest", "acceptance_fact_ref", "acceptance_fact_digest",
        "reconciliation_ref", "reconciliation_digest", "mismatch_ref",
        "mismatch_digest", "outcome_value_digest",
    ),
    RESULT: (
        "schema_id", "result_ref", "outcome_value_ref", "outcome_value_digest",
        "context_ref", "context_digest", "branch", "outcome", "recorded_at",
        "result_digest",
    ),
    RECEIPT: (
        "schema_id", "receipt_ref", "mutation_ref", "command_digest",
        "profile", "family_route", "phase_basis_ref", "phase_basis_digest",
        "p1_decision_ref", "context_ref", "context_digest",
        "outcome_value_ref", "outcome_value_digest", "result_ref",
        "result_digest", "graph_profile", "graph_digest",
        "committed_result_digest", "recorded_at", "receipt_digest",
    ),
}
SCHEMAS = {CONTEXT: CONTEXT_SCHEMA, OUTCOME: OUTCOME_SCHEMA,
           RESULT: RESULT_SCHEMA, RECEIPT: RECEIPT_SCHEMA}
OWN_DIGEST = {CONTEXT: "context_digest", OUTCOME: "outcome_value_digest",
              RESULT: "result_digest", RECEIPT: "receipt_digest"}
PRIMARY = {CONTEXT: "context_ref", OUTCOME: "outcome_value_ref",
           RESULT: "result_ref", RECEIPT: "receipt_ref"}
_BLOBS = {"command_safe_bytes", "reached_owner_manifest_bytes",
          "closure_heads_bytes", "closure_stop_bytes"}
_OPTIONAL_PAIRS = {"acceptance_fact_ref", "acceptance_fact_digest",
                   "reconciliation_ref", "reconciliation_digest",
                   "mismatch_ref", "mismatch_digest"}


@dataclass(frozen=True, slots=True, repr=False)
class TerminalRow:
    table: str
    values: tuple[object, ...]

    @property
    def mapping(self) -> dict[str, object]:
        return dict(zip(COLUMNS[self.table], self.values, strict=True))


def checked_row(table: str, raw: object) -> TerminalRow:
    if type(table) is not str or table not in TABLES or type(raw) is not tuple or len(raw) != len(COLUMNS[table]):
        raise ValueError("invalid terminal row tuple")
    value = dict(zip(COLUMNS[table], raw, strict=True))
    if type(value["schema_id"]) is not str or value["schema_id"] != SCHEMAS[table]:
        raise ValueError("invalid terminal row schema")
    if table in (CONTEXT, RESULT, RECEIPT):
        _time(value["recorded_at"])
    for name, item in value.items():
        if name in _BLOBS:
            ceiling = (49152 if name == "command_safe_bytes" else
                       WITNESS_BYTE_CEILING if table == CONTEXT and name == "closure_heads_bytes"
                       else 1024 if name == "closure_stop_bytes" else 8192)
            if type(item) is not bytes or not 1 <= len(item) <= ceiling:
                raise ValueError("invalid terminal row blob")
        elif name.endswith("_ref") or name in ("family_route", "mutation_ref"):
            if name not in _OPTIONAL_PAIRS or item is not None:
                _safe_ref(item)
        elif name.endswith("_digest") or name in ("command_digest", "p1_receipt_digest_anchor"):
            if name not in _OPTIONAL_PAIRS or item is not None:
                _sha(item)
    if table == CONTEXT:
        if (type(value["profile"]) is not str or value["profile"] != PROFILE
            or type(value["p1_decision_kind"]) is not str
            or value["p1_decision_kind"] not in NORMAL_PAIRS.values()):
            raise ValueError("invalid terminal context")
        safe = _strict_bytes(cast(bytes, value["command_safe_bytes"]))
        witness = witness_from_bytes(value["closure_heads_bytes"])
        stop = _strict_bytes(cast(bytes, value["closure_stop_bytes"]), limit=1024)
        manifest = _strict_bytes(cast(bytes, value["reached_owner_manifest_bytes"]), limit=8192)
        if (safe["context_ref"] != value["context_ref"]
            or safe["mutation_ref"] != value["mutation_ref"]
            or safe["phase_basis_ref"] != value["phase_basis_ref"]
            or safe["phase_basis_digest"] != value["phase_basis_digest"]
            or safe["reached_owners"] != manifest["roles"]
            or list(witness.coordinates) != safe["heads"]
            or stop["stop"] != safe["stop"]):
            raise ValueError("invalid terminal context binding")
        _stop(stop["stop"])
        expected = _identity_digest(CONTEXT_SCHEMA, {
            k: (v.hex() if type(v) is bytes else v)
            for k, v in value.items()}, "context_digest")
        if value["context_digest"] != expected:
            raise ValueError("invalid terminal context digest")
    elif table == OUTCOME:
        heads = _strict_bytes(cast(bytes, value["closure_heads_bytes"]), limit=4096)
        stop = _strict_bytes(cast(bytes, value["closure_stop_bytes"]), limit=1024)
        logical = {
            **{name: value[name] for name in COLUMNS[OUTCOME]
               if name not in ("closure_heads_bytes", "closure_stop_bytes")},
            "closure_heads": heads["heads"], "closure_stop": stop["stop"],
        }
        RW0TerminalOutcomeV2.from_mapping(logical)
    elif table == RESULT:
        if (type(value["branch"]) is not str or value["branch"] != "normal"
            or type(value["outcome"]) is not str
            or value["outcome"] not in NORMAL_PAIRS.values()):
            raise ValueError("invalid terminal result")
        if value["result_digest"] != _identity_digest(RESULT_SCHEMA, value, "result_digest"):
            raise ValueError("invalid terminal result digest")
    else:
        if (type(value["profile"]) is not str or value["profile"] != PROFILE
            or type(value["graph_profile"]) is not str
            or value["graph_profile"] != GRAPH_PROFILE):
            raise ValueError("invalid terminal receipt")
        if value["receipt_digest"] != _identity_digest(RECEIPT_SCHEMA, value, "receipt_digest"):
            raise ValueError("invalid terminal receipt digest")
    return TerminalRow(table, cast(tuple[object, ...], raw))


def seal_row(table: str, value: dict[str, object]) -> TerminalRow:
    if type(table) is not str or table not in TABLES or type(value) is not dict or set(value) != set(COLUMNS[table]):
        raise ValueError("invalid terminal row fields")
    if table in (CONTEXT, RESULT, RECEIPT):
        _time(value["recorded_at"])
    field = OWN_DIGEST[table]
    if value[field] in ("", None):
        if table == CONTEXT:
            value[field] = _identity_digest(CONTEXT_SCHEMA, {
                k: (v.hex() if type(v) is bytes else v) for k, v in value.items()
            }, field)
        elif table == OUTCOME:
            heads = _strict_bytes(cast(bytes, value["closure_heads_bytes"]), limit=4096)
            stop = _strict_bytes(cast(bytes, value["closure_stop_bytes"]), limit=1024)
            logical = {**{name: value[name] for name in COLUMNS[OUTCOME]
                          if name not in ("closure_heads_bytes", "closure_stop_bytes")},
                       "closure_heads": heads["heads"], "closure_stop": stop["stop"]}
            value[field] = _identity_digest(OUTCOME_SCHEMA, logical, field)
        else:
            value[field] = _identity_digest(SCHEMAS[table], value, field)
    return checked_row(table, tuple(value[name] for name in COLUMNS[table]))
