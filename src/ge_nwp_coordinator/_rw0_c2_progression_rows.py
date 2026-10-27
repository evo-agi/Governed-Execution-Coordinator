"""Private closed row reconstruction for the six immutable P1 supplements.

The catalog is physical authority for column order. These literal tuples pin the
0007 member shape at the application boundary; each row is reconstructed under
the same nominal mutation read capability used by existing C2B readers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from ._rw0_c2_progression_contracts import (
    _PREFIX, _BRANCHES, _safe_evidence, _self_digest, _strict_json,
    DecisionBasisV2,
)
from ._rw0_c2_scope_admission_contracts import _ref, _digest_value, _time
from . import _development_program_row_values as _program_rows

__all__: tuple[str, ...] = ()

_CONTINUITY = "rw0_c2_historical_continuity_bases"
_SOLE = "rw0_c2_historical_sole_active_bases"
_BASIS = "rw0_c2_decision_bases"
_RELATION = "rw0_c2_guarded_family_relations"
_RESULT = "rw0_c2_guarded_progression_results"
_ACCEPTANCE = "rw0_c2_bootstrap_acceptance_facts"
_TABLES = (_CONTINUITY, _SOLE, _BASIS, _RELATION, _RESULT, _ACCEPTANCE)
_CONTINUITY_LOGICAL = (
    "schema_id", "basis_ref", "source_ref", "source_digest", "lineage_ref",
    "scope_ref", "authority_epoch_ref", "currentness_ref",
    "currentness_digest", "provenance_ref", "provenance_digest",
    "projection_digest",
)
_SOLE_LOGICAL = _CONTINUITY_LOGICAL[:9] + (
    "active_authority_ref", "sole_active_assertion_ref",
    "sole_active_assertion_digest",
) + _CONTINUITY_LOGICAL[9:]
_RELATION_LOGICAL = (
    "schema_id", "relation_ref", "branch", "lineage_ref", "scope_ref",
    "command_digest", "admission_act_ref", "admission_act_digest",
    "admission_fact_ref", "admission_fact_digest", "continuity_basis_ref",
    "continuity_basis_digest", "sole_active_basis_ref", "sole_active_basis_digest",
    "decision_ref", "decision_digest", "version_ref", "version_digest",
    "historical_head_ref", "historical_head_revision", "historical_head_digest",
    "historical_head_postimage", "historical_work_head_ref",
    "historical_work_head_revision", "historical_work_head_digest",
    "historical_work_head_postimage", "acceptance_fact_ref", "acceptance_fact_digest",
    "generic_result_projection_digest", "family_route", "relation_digest",
)
_RESULT_LOGICAL = (
    "schema_id", "guarded_result_ref", "branch", "generic_v1_result_schema_id",
    "generic_v1_result_digest", "family_relation_ref", "family_relation_digest",
    "receipt_graph_profile_id", "guarded_result_digest",
)
_ACCEPTANCE_LOGICAL = (
    "schema_id", "acceptance_fact_ref", "lineage_ref", "scope_ref",
    "admission_fact_ref", "admission_fact_digest", "mutation_ref",
    "command_digest", "decision_ref", "decision_digest", "version_ref",
    "version_digest", "historical_head_ref", "historical_head_revision",
    "historical_head_digest", "selected_attempt_ref", "selected_candidate_ref",
    "basis_ref", "basis_digest", "family_route", "accepted_at",
    "acceptance_fact_digest",
)
_TABLE_FIELDS = {
    _CONTINUITY: _CONTINUITY_LOGICAL + ("program_ref", "admission_fact_ref", "captured_at"),
    _SOLE: _SOLE_LOGICAL + ("program_ref", "admission_fact_ref", "captured_at"),
    _BASIS: (
        "schema_id", "basis_ref", "mutation_ref", "program_ref",
        "admission_fact_ref", "admission_fact_digest", "continuity_basis_ref",
        "continuity_basis_digest", "sole_active_basis_ref", "sole_active_basis_digest",
        "current_program_version_ref", "selected_attempt_ref", "selected_candidate_ref",
        "selected_fence_ref", "selected_fence_digest", "branch", "basis_bytes",
        "basis_digest", "captured_at",
    ),
    _RELATION: _RELATION_LOGICAL + ("mutation_ref", "program_ref", "basis_ref", "basis_digest"),
    _RESULT: _RESULT_LOGICAL + ("mutation_ref", "program_ref", "decision_ref", "version_ref", "decided_at"),
    _ACCEPTANCE: _ACCEPTANCE_LOGICAL + ("program_ref",),
}
_LOGICAL = {
    _CONTINUITY: _CONTINUITY_LOGICAL, _SOLE: _SOLE_LOGICAL,
    _RELATION: _RELATION_LOGICAL, _RESULT: _RESULT_LOGICAL,
    _ACCEPTANCE: _ACCEPTANCE_LOGICAL,
}
_SCHEMAS = {
    _CONTINUITY: _PREFIX + "verified-lineage-continuity.v1",
    _SOLE: _PREFIX + "verified-sole-active.v1",
    _BASIS: _PREFIX + "decision-basis.v2",
    _RELATION: _PREFIX + "guarded-family-relation.v2",
    _RESULT: _PREFIX + "guarded-progression-result.v2",
    _ACCEPTANCE: _PREFIX + "bootstrap-acceptance-fact.v1",
}
_DIGEST_FIELDS = {
    _CONTINUITY: "projection_digest", _SOLE: "projection_digest",
    _RELATION: "relation_digest", _RESULT: "guarded_result_digest",
    _ACCEPTANCE: "acceptance_fact_digest",
}


@dataclass(frozen=True, slots=True, repr=False)
class _P1Row:
    table: str
    columns: tuple[object, ...]

    @property
    def mapping(self) -> dict[str, object]:
        return dict(zip(_TABLE_FIELDS[self.table], self.columns, strict=True))


def _checked_p1_row(table: str, row: object) -> _P1Row:
    if (table not in _TABLES or type(row) is not tuple
        or len(row) != len(_TABLE_FIELDS[table])):
        raise ValueError("invalid P1 row shape")
    mapping = dict(zip(_TABLE_FIELDS[table], row, strict=True))
    if mapping["schema_id"] != _SCHEMAS[table]:
        raise ValueError("invalid P1 row schema")
    if table in (_CONTINUITY, _SOLE):
        logical = {name: mapping[name] for name in _LOGICAL[table]}
        _safe_evidence(logical, sole=table == _SOLE)
        if (any(not _ref(mapping[name]) for name in ("program_ref", "admission_fact_ref"))
            or not _time(mapping["captured_at"])):
            raise ValueError("invalid P1 historical binding")
    elif table == _BASIS:
        raw = mapping["basis_bytes"]
        basis = DecisionBasisV2.from_json(raw)
        value = basis.to_mapping()
        fact = cast(dict[str, object], value["scope_admission_fact"])
        snapshot = cast(dict[str, object], value["decision_current_snapshot"])
        if (mapping["basis_ref"] != value["basis_ref"]
            or mapping["basis_digest"] != value["basis_digest"]
            or mapping["admission_fact_ref"] != fact["admission_fact_ref"]
            or mapping["admission_fact_digest"] != fact["admission_fact_digest"]
            or mapping["continuity_basis_ref"] != value["historical_continuity_basis_ref"]
            or mapping["continuity_basis_digest"] != value["historical_continuity_basis_digest"]
            or mapping["sole_active_basis_ref"] != value["historical_sole_active_basis_ref"]
            or mapping["sole_active_basis_digest"] != value["historical_sole_active_basis_digest"]
            or mapping["program_ref"] != snapshot["program_ref"]
            or mapping["current_program_version_ref"] != snapshot["program_version_ref"]
            or mapping["selected_attempt_ref"] != snapshot["semantic_attempt_ref"]
            or mapping["selected_candidate_ref"] != snapshot["candidate_ref"]
            or mapping["selected_fence_ref"] != snapshot["attempt_fence_ref"]
            or mapping["selected_fence_digest"] != snapshot["attempt_fence_digest"]
            or mapping["branch"] not in _BRANCHES
            or mapping["captured_at"] != value["captured_at"]
            or not _ref(mapping["mutation_ref"])):
            raise ValueError("invalid P1 basis row binding")
    else:
        logical = {name: mapping[name] for name in _LOGICAL[table]}
        if table == _RELATION:
            head = logical["historical_head_postimage"]
            if type(head) is not bytes:
                raise ValueError("invalid P1 head postimage bytes")
            parsed = _strict_json(head, ceiling=4096)
            columns = _program_rows._DEVELOPMENT_PROGRAM_HEAD_COLUMNS
            if set(parsed) != set(columns):
                raise ValueError("invalid P1 head postimage shape")
            _program_rows.development_program_head_row_value_from_row_tuple(
                tuple(parsed[name] for name in columns))
            if (parsed["program_ref"] != mapping["program_ref"]
                or parsed["head_digest"] != mapping["historical_head_digest"]
                or parsed["head_revision"] != mapping["historical_head_revision"]
                or parsed["program_ref"] != mapping["historical_head_ref"]):
                raise ValueError("invalid P1 head postimage relation")
            logical["historical_head_postimage"] = parsed
            work_names = (
                "historical_work_head_ref", "historical_work_head_revision",
                "historical_work_head_digest", "historical_work_head_postimage",
            )
            work_values = tuple(logical[name] for name in work_names)
            if logical["branch"] == "attempt_selecting_replan":
                if any(value is None for value in work_values):
                    raise ValueError("missing P1 replan work-head witness")
                raw_work = logical["historical_work_head_postimage"]
                if type(raw_work) is not bytes:
                    raise ValueError("invalid P1 work-head bytes")
                work = _strict_json(raw_work, ceiling=4096)
                work_columns = _program_rows._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS
                if set(work) != set(work_columns):
                    raise ValueError("invalid P1 work-head shape")
                _program_rows.development_work_item_head_row_value_from_row_tuple(
                    tuple(work[name] for name in work_columns))
                if (work["program_ref"] != mapping["program_ref"]
                    or work["work_item_ref"] != logical["historical_work_head_ref"]
                    or work["head_revision"] != logical["historical_work_head_revision"]
                    or work["head_digest"] != logical["historical_work_head_digest"]
                    or work["work_state"] != "active"
                    or not _ref(logical["historical_work_head_ref"])
                    or type(logical["historical_work_head_revision"]) is not int
                    or logical["historical_work_head_revision"] < 1
                    or not _digest_value(logical["historical_work_head_digest"])):
                    raise ValueError("invalid P1 replan work-head witness")
                logical["historical_work_head_postimage"] = work
            elif any(value is not None for value in work_values):
                raise ValueError("foreign P1 work-head witness")
            if (logical["branch"] == "candidate_acceptance") != (
                logical["acceptance_fact_ref"] is not None
                and logical["acceptance_fact_digest"] is not None):
                raise ValueError("invalid P1 acceptance relation")
        digest_field = _DIGEST_FIELDS[table]
        if _self_digest(logical, digest_field) != logical[digest_field]:
            raise ValueError("invalid P1 logical row digest")
        if table in (_RELATION, _RESULT):
            if (mapping["branch"] not in _BRANCHES
                or any(not _ref(mapping[name]) for name in ("mutation_ref", "program_ref"))):
                raise ValueError("invalid P1 supplemental binding")
        if table == _RESULT and (not _ref(mapping["decision_ref"])
                                 or not _ref(mapping["version_ref"])
                                 or not _time(mapping["decided_at"])):
            raise ValueError("invalid P1 result binding")
        if table == _ACCEPTANCE and (not _ref(mapping["program_ref"])
                                     or not _time(mapping["accepted_at"])):
            raise ValueError("invalid P1 acceptance binding")
    return _P1Row(table, cast(tuple[object, ...], row))
