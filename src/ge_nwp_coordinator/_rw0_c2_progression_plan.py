"""Private pure P1 write-plan construction over already checked owner rows."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import cast

from . import _development_decision_row_values as _decision
from . import _development_program_row_values as _program
from ._development_program_initialization_contracts import _accepted_intent_safe_projection
from ._development_row_value_support import _domain_separated_digest
from ._rw0_c2_progression_contracts import (
    _PREFIX, _canonical, _self_digest, _safe_evidence, _time,
    RecordProgressionDecisionCommandV1, ProgressionDecisionReductionV1,
    _require_bound_replan_work_spec, bind_replan_work_spec, derive_replan_durable_refs,
    derive_successor_selection_refs,
)
from ._rw0_c2_progression_rows import (
    _P1Row, _CONTINUITY, _SOLE, _BASIS, _RELATION, _RESULT, _ACCEPTANCE,
    _TABLE_FIELDS, _checked_p1_row,
)

__all__: tuple[str, ...] = ()

_BRANCH_KIND = {
    "candidate_acceptance": ("accept", "candidate_acceptance", "accepted"),
    "candidate_repair": ("repair", "candidate_repair", "active"),
    "attempt_selecting_replan": ("replan", "attempt_selecting_replan", "active"),
    "program_terminal_reject": ("terminal_reject", "program_terminal_reject", "terminal_rejected"),
    "post_execution_program_block": ("block", "program_block", "blocked"),
}
_VERSION_KIND = {
    "candidate_acceptance": "accepted", "candidate_repair": "repair",
    "attempt_selecting_replan": "replan", "program_terminal_reject": "terminal_rejected",
    "post_execution_program_block": "blocked",
}
_PROGRESSION_RESULT_SCHEMA = "governed-execution.nwp-record-development-progression-decision-result.v1"
_RECEIPT_GRAPH_PROFILE = _PREFIX + "receipt-graph-profile.v2"


@dataclass(frozen=True, slots=True, repr=False)
class _P1CurrentRows:
    program_head: _program.DevelopmentProgramHeadRowValue
    program_version: _program.DevelopmentProgramVersionRowValue
    accepted_intent: _program.DevelopmentAcceptedIntentRevisionRowValue
    work_head: _program.DevelopmentWorkItemHeadRowValue
    work_revision: _program.DevelopmentWorkItemRevisionRowValue
    basis_decision: _decision.DevelopmentDecisionRowValue
    membership: tuple[_program.DevelopmentProgramVersionWorkItemRowValue, ...]
    coding_global_stop_ref: str
    coding_global_stop_version: int


@dataclass(frozen=True, slots=True, repr=False)
class _P1WritePlan:
    rows: tuple[tuple[str, object], ...]
    head_postimage: _program.DevelopmentProgramHeadRowValue
    work_head_postimage: _program.DevelopmentWorkItemHeadRowValue | None
    generic_receipt: _decision.DevelopmentMutationReceiptRowValue
    graph_entries: tuple[_decision.DevelopmentMutationGraphEntry, ...]
    branch: str
    decided_at: str
    guarded_result_digest: str


def _row(
    *, table: str, fields: dict[str, object], columns: tuple[str, ...],
    digest_field: str, adapter: object,
) -> object:
    value = dict(fields)
    if tuple(value) != columns[:-1] or columns[-1] != digest_field:
        raise ValueError("invalid P1 generic row order")
    schema = cast(str, value["schema_id"])
    value[digest_field] = _domain_separated_digest(schema + ".identity", value)
    return adapter(tuple(value[name] for name in columns))  # type: ignore[operator]


def _p1_row(table: str, logical: dict[str, object], **wrappers: object) -> _P1Row:
    value = dict(logical)
    value.update(wrappers)
    if set(value) != set(_TABLE_FIELDS[table]):
        raise ValueError("invalid P1 supplemental plan")
    return _checked_p1_row(table, tuple(value[name] for name in _TABLE_FIELDS[table]))


def _edge(
    *, command_digest: str, program_ref: str, kind: str,
    from_ref: str, to_ref: str, timestamp: str,
) -> _program.DevelopmentRevisionEdgeRowValue:
    is_intent = kind == "accepted_intent_supersedes"
    relation = {
        "schema_id": _PREFIX + "revision-edge-relation-key.v1",
        "command_digest": command_digest, "program_ref": program_ref,
        "kind": kind, "from_ref": from_ref, "to_ref": to_ref,
    }
    relation_digest = _domain_separated_digest(
        _PREFIX + "revision-edge-relation-key.v1.identity", relation)
    edge_ref = _domain_separated_digest(_PREFIX + "revision-edge-ref.v1", relation)
    fields = {
        "schema_id": _program._DEVELOPMENT_REVISION_EDGE_SCHEMA,
        "revision_edge_ref": edge_ref, "relation_key_digest": relation_digest,
        "program_ref": program_ref, "revision_edge_kind": kind,
        "from_accepted_intent_revision_ref": from_ref if is_intent else None,
        "to_accepted_intent_revision_ref": to_ref if is_intent else None,
        "from_work_item_revision_ref": None if is_intent else from_ref,
        "to_work_item_revision_ref": None if is_intent else to_ref,
        "created_at": timestamp,
    }
    return cast(_program.DevelopmentRevisionEdgeRowValue, _row(
        table="development_revision_edges", fields=fields,
        columns=_program._DEVELOPMENT_REVISION_EDGE_COLUMNS,
        digest_field="revision_edge_digest",
        adapter=_program.development_revision_edge_row_value_from_row_tuple,
    ))


def build_p1_write_plan(
    *, command: RecordProgressionDecisionCommandV1,
    reduction: ProgressionDecisionReductionV1,
    current: _P1CurrentRows,
    continuity: dict[str, object], sole: dict[str, object],
    timestamp: str,
) -> _P1WritePlan:
    if (type(command) is not RecordProgressionDecisionCommandV1
        or type(reduction) is not ProgressionDecisionReductionV1
        or type(current) is not _P1CurrentRows or not _time(timestamp)):
        raise ValueError("invalid P1 write-plan input")
    relation = command.relation.to_mapping()
    basis = command.basis.to_mapping()
    snapshot = cast(dict[str, object], basis["decision_current_snapshot"])
    act = cast(dict[str, object], basis["verified_admission_act"])
    fact = cast(dict[str, object], basis["scope_admission_fact"])
    branch = reduction.branch
    program_ref = cast(str, relation["program_ref"])
    mutation_ref = cast(str, relation["mutation_ref"])
    decision_ref = cast(str, relation["preassigned_decision_ref"])
    version_ref = cast(str, relation["preassigned_version_ref"])
    command_digest = command.command_digest
    if (program_ref != current.program_head.program_ref
        or current.program_version.program_version_ref != current.program_head.current_program_version_ref
        or current.program_version.program_ref != program_ref
        or current.program_head.current_program_version_ref != relation["expected_head_ref"]
        or current.program_head.head_revision != relation["expected_head_revision"]
        or current.program_head.head_digest != relation["expected_head_digest"]
        or current.program_version.program_version_ref != snapshot["program_version_ref"]
        or current.accepted_intent.accepted_intent_revision_ref != snapshot["accepted_intent_revision_ref"]
        or current.work_head.work_item_ref != snapshot["work_item_ref"]
        or current.work_revision.work_item_revision_ref != snapshot["work_item_revision_ref"]
        or current.basis_decision.decision_ref != current.program_version.creating_decision_ref):
        raise ValueError("stale P1 current family")
    continuity = _safe_evidence(continuity, sole=False)
    sole = _safe_evidence(sole, sole=True)
    if (continuity["basis_ref"] != relation["continuity_basis_ref"]
        or continuity["projection_digest"] != relation["continuity_basis_digest"]
        or continuity["source_ref"] != relation["continuity_source_ref"]
        or continuity["source_digest"] != relation["continuity_source_digest"]
        or sole["basis_ref"] != relation["sole_active_basis_ref"]
        or sole["projection_digest"] != relation["sole_active_basis_digest"]
        or sole["source_ref"] != relation["sole_active_source_ref"]
        or sole["source_digest"] != relation["sole_active_source_digest"]):
        raise ValueError("foreign P1 historical evidence")
    for item in current.membership:
        if type(item) is not _program.DevelopmentProgramVersionWorkItemRowValue:
            raise ValueError("invalid P1 membership")
    if (not current.membership
        or tuple(item.membership_ordinal for item in current.membership)
           != tuple(range(len(current.membership)))
        or len({item.work_item_ref for item in current.membership}) != len(current.membership)
        or any(item.program_ref != program_ref
               or item.program_version_ref != current.program_version.program_version_ref
               for item in current.membership)
        or sum(item.work_item_ref == snapshot["work_item_ref"]
               and item.work_item_revision_ref == snapshot["work_item_revision_ref"]
               for item in current.membership) != 1):
        raise ValueError("invalid P1 membership closure")
    version_number = current.program_version.program_version_number + 1
    head_revision = current.program_head.head_revision + 1
    head_state = _BRANCH_KIND[branch][2]
    is_replan = branch == "attempt_selecting_replan"
    new_intent_ref = None
    new_work_revision_ref = None
    next_attempt = None
    next_candidate = None
    final_work_spec = None
    replan_rows: list[tuple[str, object]] = []
    if branch in {"candidate_repair", "attempt_selecting_replan"}:
        next_attempt, next_candidate = derive_successor_selection_refs(
            command_digest=command_digest, program_ref=program_ref,
            selected_attempt_ref=cast(str, snapshot["semantic_attempt_ref"]),
            selected_candidate_ref=cast(str, snapshot["candidate_ref"]),
            branch=branch,
        )
    if is_replan:
        proposal = command.replan_proposal
        if proposal is None:
            raise ValueError("missing P1 replan source")
        template = proposal.work_spec_template.to_mapping()
        if (template["program_ref"] != program_ref
            or template["work_item_ref"] != snapshot["work_item_ref"]):
            raise ValueError("invalid P1 replan adoption")
        new_intent_ref, new_work_revision_ref, new_work_spec_ref = derive_replan_durable_refs(
            command_digest=command_digest, program_ref=program_ref,
            current_program_version_ref=current.program_version.program_version_ref,
            current_accepted_intent_revision_ref=current.accepted_intent.accepted_intent_revision_ref,
            work_item_ref=current.work_head.work_item_ref,
            current_work_item_revision_ref=current.work_revision.work_item_revision_ref,
            source_intent_ref=proposal.source_intent_ref,
            source_intent_digest=proposal.source_intent_digest,
            work_spec_template_digest=proposal.work_spec_template.digest,
            preassigned_version_ref=version_ref,
        )
        if (new_intent_ref == current.accepted_intent.accepted_intent_revision_ref
            or new_work_revision_ref == current.work_revision.work_item_revision_ref):
            raise ValueError("reused P1 replan revision")
        final_work_spec = bind_replan_work_spec(
            proposal.work_spec_template, work_spec_ref=new_work_spec_ref,
            program_version_ref=version_ref,
            accepted_intent_revision_ref=new_intent_ref,
            work_item_revision_ref=new_work_revision_ref,
        )
        _require_bound_replan_work_spec(
            proposal.work_spec_template, candidate=final_work_spec,
            work_spec_ref=new_work_spec_ref, program_version_ref=version_ref,
            accepted_intent_revision_ref=new_intent_ref,
            work_item_revision_ref=new_work_revision_ref,
        )
        work_projection = _program.development_work_spec_safe_projection_from_work_spec(
            work_spec=final_work_spec)
        accepted_projection = _accepted_intent_safe_projection(
            source_intent_ref=proposal.source_intent_ref,
            source_intent_digest=proposal.source_intent_digest,
            work_spec_safe_projection=work_projection,
        )
        intent_row = _row(table="development_accepted_intent_revisions", fields={
            "schema_id": _program._DEVELOPMENT_ACCEPTED_INTENT_REVISION_SCHEMA,
            "accepted_intent_revision_ref": new_intent_ref,
            "program_ref": program_ref,
            "accepted_intent_revision_number": current.accepted_intent.accepted_intent_revision_number + 1,
            "prior_accepted_intent_revision_ref": current.accepted_intent.accepted_intent_revision_ref,
            "source_intent_ref": proposal.source_intent_ref,
            "source_intent_digest": proposal.source_intent_digest,
            "safe_projection_digest": accepted_projection.safe_projection_digest,
            "created_at": timestamp,
        }, columns=_program._DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS,
            digest_field="accepted_intent_revision_digest",
            adapter=_program.development_accepted_intent_revision_row_value_from_row_tuple)
        work_row = _row(table="development_work_item_revisions", fields={
            "schema_id": _program._DEVELOPMENT_WORK_ITEM_REVISION_SCHEMA,
            "work_item_revision_ref": new_work_revision_ref,
            "program_ref": program_ref,
            "work_item_ref": current.work_head.work_item_ref,
            "work_item_revision_number": current.work_revision.work_item_revision_number + 1,
            "work_item_revision_kind": "replan",
            "prior_work_item_revision_ref": current.work_revision.work_item_revision_ref,
            "accepted_intent_revision_ref": new_intent_ref,
            "created_at": timestamp,
        }, columns=_program._DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS,
            digest_field="work_item_revision_digest",
            adapter=_program.development_work_item_revision_row_value_from_row_tuple)
        replan_rows.extend((
            ("development_accepted_intent_revisions", intent_row),
            ("development_work_item_revisions", work_row),
            ("development_revision_edges", _edge(
                command_digest=command_digest, program_ref=program_ref,
                kind="accepted_intent_supersedes",
                from_ref=current.accepted_intent.accepted_intent_revision_ref,
                to_ref=new_intent_ref, timestamp=timestamp)),
            ("development_revision_edges", _edge(
                command_digest=command_digest, program_ref=program_ref,
                kind="work_item_supersedes",
                from_ref=current.work_revision.work_item_revision_ref,
                to_ref=new_work_revision_ref, timestamp=timestamp)),
        ))
    resulting_intent = new_intent_ref or current.accepted_intent.accepted_intent_revision_ref
    selected = branch != "post_execution_program_block"
    decision_values = {
        "schema_id": _decision._DEVELOPMENT_DECISION_SCHEMA,
        "mutation_ref": mutation_ref, "decision_ref": decision_ref,
        "program_ref": program_ref,
        "decision_kind": _BRANCH_KIND[branch][0],
        "decision_variant": _BRANCH_KIND[branch][1],
        "basis_decision_ref": current.basis_decision.decision_ref,
        "basis_program_version_ref": current.program_version.program_version_ref,
        "basis_program_version_number": current.program_version.program_version_number,
        "expected_program_head_revision": current.program_head.head_revision,
        "resulting_program_version_ref": version_ref,
        "resulting_program_version_number": version_number,
        "selected_semantic_attempt_ref": snapshot["semantic_attempt_ref"] if selected else None,
        "selected_candidate_ref": snapshot["candidate_ref"] if selected else None,
        "selected_attempt_fence_ref": snapshot["attempt_fence_ref"] if selected else None,
        "selected_attempt_fence_digest": snapshot["attempt_fence_digest"] if selected else None,
        "target_effect_intent_ref": None, "target_effect_class": None,
        "target_effect_fence_ref": None, "target_effect_fence_digest": None,
        "expected_target_effect_head_revision": None,
        "target_delivery_attempt_ref": None,
        "originating_command_ref": None, "originating_command_digest": None,
        "target_capsule_manifest_ref": None, "target_portable_capsule_digest": None,
        "coding_global_stop_ref": current.coding_global_stop_ref,
        "coding_global_stop_version": current.coding_global_stop_version,
        "source_directive_ref": None, "source_directive_digest": None,
        "source_evidence_ref": None, "source_evidence_digest": None,
        "preassigned_semantic_attempt_ref": next_attempt,
        "preassigned_candidate_ref": next_candidate,
        "preassigned_effect_intent_ref": None, "preassigned_effect_fence_ref": None,
        "preassigned_delivery_attempt_ref": None,
        "resulting_accepted_intent_revision_ref": new_intent_ref,
        "resulting_work_item_ref": current.work_head.work_item_ref if is_replan else None,
        "resulting_work_item_revision_ref": new_work_revision_ref,
        "reason_code": reduction.reason_code,
        "decided_at": timestamp,
    }
    decision = cast(_decision.DevelopmentDecisionRowValue, _row(
        table="development_decisions", fields=decision_values,
        columns=_decision._DEVELOPMENT_DECISION_COLUMNS,
        digest_field="decision_digest",
        adapter=_decision.development_decision_row_value_from_row_tuple,
    ))
    version = cast(_program.DevelopmentProgramVersionRowValue, _row(
        table="development_program_versions", fields={
            "schema_id": _program._DEVELOPMENT_PROGRAM_VERSION_SCHEMA,
            "program_version_ref": version_ref, "program_ref": program_ref,
            "program_version_number": version_number,
            "program_version_kind": _VERSION_KIND[branch],
            "creating_decision_ref": decision_ref,
            "accepted_intent_revision_ref": resulting_intent,
            "created_at": timestamp,
        }, columns=_program._DEVELOPMENT_PROGRAM_VERSION_COLUMNS,
        digest_field="program_version_digest",
        adapter=_program.development_program_version_row_value_from_row_tuple,
    ))
    head = cast(_program.DevelopmentProgramHeadRowValue, _row(
        table="development_program_heads", fields={
            "schema_id": _program._DEVELOPMENT_PROGRAM_HEAD_SCHEMA,
            "program_ref": program_ref,
            "current_program_version_ref": version_ref,
            "current_program_version_number": version_number,
            "head_revision": head_revision,
            "program_state": head_state,
            "updated_at": timestamp,
        }, columns=_program._DEVELOPMENT_PROGRAM_HEAD_COLUMNS,
        digest_field="head_digest",
        adapter=_program.development_program_head_row_value_from_row_tuple,
    ))
    work_head: _program.DevelopmentWorkItemHeadRowValue | None = None
    if is_replan:
        work_head = cast(_program.DevelopmentWorkItemHeadRowValue, _row(
            table="development_work_item_heads", fields={
                "schema_id": _program._DEVELOPMENT_WORK_ITEM_HEAD_SCHEMA,
                "work_item_ref": current.work_head.work_item_ref,
                "program_ref": program_ref,
                "current_work_item_revision_ref": new_work_revision_ref,
                "current_work_item_revision_number": current.work_head.current_work_item_revision_number + 1,
                "head_revision": current.work_head.head_revision + 1,
                "work_state": "active", "updated_at": timestamp,
            }, columns=_program._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS,
            digest_field="head_digest",
            adapter=_program.development_work_item_head_row_value_from_row_tuple,
        ))
    memberships: list[tuple[str, object]] = []
    for member in current.membership:
        new_revision = (new_work_revision_ref if is_replan and
                        member.work_item_ref == current.work_head.work_item_ref
                        else member.work_item_revision_ref)
        memberships.append(("development_program_version_work_items", _row(
            table="development_program_version_work_items", fields={
                "schema_id": _program._DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_SCHEMA,
                "program_ref": program_ref, "program_version_ref": version_ref,
                "work_item_ref": member.work_item_ref,
                "work_item_revision_ref": new_revision,
                "membership_ordinal": member.membership_ordinal,
                "created_at": timestamp,
            }, columns=_program._DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS,
            digest_field="membership_digest",
            adapter=_program.development_program_version_work_item_row_value_from_row_tuple,
        )))
    if is_replan:
        assert final_work_spec is not None
        safe = _program.development_work_spec_safe_projection_from_work_spec(
            work_spec=final_work_spec)
        binding_fields = {
            "schema_id": _program._DEVELOPMENT_WORK_SPEC_BINDING_SCHEMA,
            "work_spec_ref": safe.work_spec_ref, "program_ref": program_ref,
            "program_version_ref": version_ref,
            "accepted_intent_revision_ref": resulting_intent,
            "work_item_ref": safe.work_item_ref,
            "work_item_revision_ref": safe.work_item_revision_ref,
            "repository_ref": safe.repository_ref,
            "base_git_object_format": safe.base_git_object_format,
            "base_git_oid": safe.base_git_oid,
            "authorized_paths_json": json.dumps(list(safe.authorized_paths),
                ensure_ascii=False, separators=(",", ":")),
            "validation_requirement_ref": safe.validation_requirement_ref,
            "review_requirement_ref": safe.review_requirement_ref,
            "privacy_classification": safe.privacy_classification,
            "work_spec_digest": safe.work_spec_digest,
            "safe_projection_digest": safe.safe_projection_digest,
            "recorded_at": timestamp,
        }
        replan_rows.append(("development_work_spec_bindings", _row(
            table="development_work_spec_bindings", fields=binding_fields,
            columns=_program._DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS,
            digest_field="work_spec_binding_digest",
            adapter=_program.development_work_spec_binding_row_value_from_row_tuple,
        )))
    continuity_row = _p1_row(_CONTINUITY, continuity,
        program_ref=program_ref, admission_fact_ref=fact["admission_fact_ref"],
        captured_at=timestamp)
    sole_row = _p1_row(_SOLE, sole,
        program_ref=program_ref, admission_fact_ref=fact["admission_fact_ref"],
        captured_at=timestamp)
    basis_row = _p1_row(_BASIS, {
        "schema_id": _PREFIX + "decision-basis.v2",
        "basis_ref": basis["basis_ref"], "mutation_ref": mutation_ref,
        "program_ref": program_ref,
        "admission_fact_ref": fact["admission_fact_ref"],
        "admission_fact_digest": fact["admission_fact_digest"],
        "continuity_basis_ref": continuity["basis_ref"],
        "continuity_basis_digest": continuity["projection_digest"],
        "sole_active_basis_ref": sole["basis_ref"],
        "sole_active_basis_digest": sole["projection_digest"],
        "current_program_version_ref": current.program_version.program_version_ref,
        "selected_attempt_ref": snapshot["semantic_attempt_ref"],
        "selected_candidate_ref": snapshot["candidate_ref"],
        "selected_fence_ref": snapshot["attempt_fence_ref"],
        "selected_fence_digest": snapshot["attempt_fence_digest"],
        "branch": branch, "basis_bytes": command.basis.canonical_bytes,
        "basis_digest": basis["basis_digest"], "captured_at": basis["captured_at"],
    })
    generic_projection = {
        "schema_id": _PROGRESSION_RESULT_SCHEMA,
        "program_ref": program_ref, "decision_ref": decision_ref,
        "result_program_version_ref": version_ref,
        "result_decision_ref": decision_ref,
    }
    generic_projection_digest = _domain_separated_digest(
        _PROGRESSION_RESULT_SCHEMA + ".identity", generic_projection)
    acceptance: _P1Row | None = None
    if branch == "candidate_acceptance":
        fact_logical = {
            "schema_id": _PREFIX + "bootstrap-acceptance-fact.v1",
            "acceptance_fact_ref": relation["preassigned_acceptance_fact_ref"],
            "lineage_ref": fact["lineage_ref"], "scope_ref": fact["scope_ref"],
            "admission_fact_ref": fact["admission_fact_ref"],
            "admission_fact_digest": fact["admission_fact_digest"],
            "mutation_ref": mutation_ref, "command_digest": command_digest,
            "decision_ref": decision_ref, "decision_digest": decision.decision_digest,
            "version_ref": version_ref, "version_digest": version.program_version_digest,
            "historical_head_ref": head.program_ref,
            "historical_head_revision": head.head_revision,
            "historical_head_digest": head.head_digest,
            "selected_attempt_ref": snapshot["semantic_attempt_ref"],
            "selected_candidate_ref": snapshot["candidate_ref"],
            "basis_ref": basis["basis_ref"], "basis_digest": basis["basis_digest"],
            "family_route": relation["family_route"], "accepted_at": timestamp,
        }
        fact_logical["acceptance_fact_digest"] = _self_digest(
            fact_logical, "acceptance_fact_digest")
        acceptance = _p1_row(_ACCEPTANCE, fact_logical, program_ref=program_ref)
    head_mapping = head._identity_mapping() | {"head_digest": head.head_digest}
    work_head_mapping = (work_head._identity_mapping() | {"head_digest": work_head.head_digest}
                         if work_head is not None else None)
    relation_logical = {
        "schema_id": _PREFIX + "guarded-family-relation.v2",
        "relation_ref": relation["preassigned_relation_ref"], "branch": branch,
        "lineage_ref": fact["lineage_ref"], "scope_ref": fact["scope_ref"],
        "command_digest": command_digest,
        "admission_act_ref": act["act_ref"], "admission_act_digest": act["act_digest"],
        "admission_fact_ref": fact["admission_fact_ref"],
        "admission_fact_digest": fact["admission_fact_digest"],
        "continuity_basis_ref": continuity["basis_ref"],
        "continuity_basis_digest": continuity["projection_digest"],
        "sole_active_basis_ref": sole["basis_ref"],
        "sole_active_basis_digest": sole["projection_digest"],
        "decision_ref": decision_ref, "decision_digest": decision.decision_digest,
        "version_ref": version_ref, "version_digest": version.program_version_digest,
        "historical_head_ref": head.program_ref,
        "historical_head_revision": head.head_revision,
        "historical_head_digest": head.head_digest,
        "historical_head_postimage": head_mapping,
        "historical_work_head_ref": work_head.work_item_ref if work_head is not None else None,
        "historical_work_head_revision": work_head.head_revision if work_head is not None else None,
        "historical_work_head_digest": work_head.head_digest if work_head is not None else None,
        "historical_work_head_postimage": work_head_mapping,
        "acceptance_fact_ref": acceptance.mapping["acceptance_fact_ref"] if acceptance else None,
        "acceptance_fact_digest": acceptance.mapping["acceptance_fact_digest"] if acceptance else None,
        "generic_result_projection_digest": generic_projection_digest,
        "family_route": relation["family_route"],
    }
    relation_logical["relation_digest"] = _self_digest(relation_logical, "relation_digest")
    relation_row = _p1_row(_RELATION, {
        **relation_logical,
        "historical_head_postimage": _canonical(head_mapping),
        "historical_work_head_postimage": (_canonical(work_head_mapping)
                                            if work_head_mapping is not None else None),
    }, mutation_ref=mutation_ref, program_ref=program_ref,
       basis_ref=basis["basis_ref"], basis_digest=basis["basis_digest"])
    result_logical = {
        "schema_id": _PREFIX + "guarded-progression-result.v2",
        "guarded_result_ref": relation["preassigned_guarded_result_ref"],
        "branch": branch,
        "generic_v1_result_schema_id": _PROGRESSION_RESULT_SCHEMA,
        "generic_v1_result_digest": generic_projection_digest,
        "family_relation_ref": relation["preassigned_relation_ref"],
        "family_relation_digest": relation_logical["relation_digest"],
        "receipt_graph_profile_id": _RECEIPT_GRAPH_PROFILE,
    }
    result_logical["guarded_result_digest"] = _self_digest(
        result_logical, "guarded_result_digest")
    result_row = _p1_row(_RESULT, result_logical, mutation_ref=mutation_ref,
        program_ref=program_ref, decision_ref=decision_ref,
        version_ref=version_ref, decided_at=timestamp)
    receipt_values = (
        _decision._DEVELOPMENT_MUTATION_RECEIPT_SCHEMA,
        mutation_ref, "record_development_progression_decision",
        "governed-execution.nwp-record-development-progression-decision-command.v1",
        command_digest, program_ref, decision_ref, version_ref,
        None, None, None, None, None, decision_ref,
        "development_progression_decision_recorded",
        generic_projection_digest, "0" * 64, "committed", timestamp,
    )
    proto = _decision.development_mutation_receipt_row_value_from_row_tuple(receipt_values)
    members = (
        ("verified_admission_act", act["act_ref"], act["act_digest"]),
        ("scope_admission_fact", fact["admission_fact_ref"], fact["admission_fact_digest"]),
        ("historical_continuity_basis", continuity["basis_ref"], continuity["projection_digest"]),
        ("historical_sole_active_basis", sole["basis_ref"], sole["projection_digest"]),
        ("decision", decision_ref, decision.decision_digest),
        ("program_version", version_ref, version.program_version_digest),
        ("historical_head_postimage", head.program_ref, head.head_digest),
        ("generic_v1_result_projection", decision_ref, generic_projection_digest),
        ("guarded_family_relation", relation["preassigned_relation_ref"], relation_logical["relation_digest"]),
        ("guarded_result_composite", relation["preassigned_guarded_result_ref"], result_logical["guarded_result_digest"]),
    ) + ((("acceptance_fact", relation["preassigned_acceptance_fact_ref"], acceptance.mapping["acceptance_fact_digest"]),)
         if acceptance is not None else
         (("historical_work_head_postimage", work_head.work_item_ref, work_head.head_digest),)
         if work_head is not None else ())
    graph_entries = tuple(_decision.development_mutation_graph_entry(
        role=role, ordinal=0, record_ref=ref, record_digest=digest)
        for role, ref, digest in members)
    graph_digest = _decision.compute_development_mutation_graph_digest(
        receipt=proto, graph_entries=graph_entries)
    receipt = _decision.development_mutation_receipt_row_value_from_row_tuple(
        receipt_values[:16] + (graph_digest,) + receipt_values[17:])
    rows: list[tuple[str, object]] = [
        *replan_rows[:4],
        ("development_decisions", decision),
        ("development_program_versions", version),
        *memberships,
        *replan_rows[4:],
        (_CONTINUITY, continuity_row), (_SOLE, sole_row),
        (_BASIS, basis_row), (_RELATION, relation_row),
        (_RESULT, result_row),
    ]
    if acceptance is not None:
        rows.append((_ACCEPTANCE, acceptance))
    rows.append(("development_mutation_receipts", receipt))
    return _P1WritePlan(tuple(rows), head, work_head, receipt,
        graph_entries, branch, timestamp, cast(str, result_logical["guarded_result_digest"]))


def verify_p1_plan_coherence(
    plan: _P1WritePlan, command: RecordProgressionDecisionCommandV1,
    current: _P1CurrentRows,
) -> None:
    """Check cross-row postimages independently of the plan construction path."""
    if (type(plan) is not _P1WritePlan
        or type(command) is not RecordProgressionDecisionCommandV1
        or type(current) is not _P1CurrentRows):
        raise ValueError("invalid P1 plan coherence input")
    rows: dict[str, list[object]] = {}
    for table, row in plan.rows:
        rows.setdefault(table, []).append(row)
    def one(table: str) -> object:
        matches = rows.get(table, [])
        if len(matches) != 1:
            raise ValueError("invalid P1 family cardinality")
        return matches[0]
    relation = one(_RELATION)
    result = one(_RESULT)
    decision = one("development_decisions")
    version = one("development_program_versions")
    receipt = one("development_mutation_receipts")
    if (type(relation) is not _P1Row or type(result) is not _P1Row
        or type(decision) is not _decision.DevelopmentDecisionRowValue
        or type(version) is not _program.DevelopmentProgramVersionRowValue
        or type(receipt) is not _decision.DevelopmentMutationReceiptRowValue):
        raise ValueError("invalid P1 family row type")
    rel = relation.mapping
    common_roles = (
        "verified_admission_act", "scope_admission_fact",
        "historical_continuity_basis", "historical_sole_active_basis",
        "decision", "program_version", "historical_head_postimage",
        "generic_v1_result_projection", "guarded_family_relation",
        "guarded_result_composite",
    )
    branch_role = (("acceptance_fact",) if plan.branch == "candidate_acceptance"
                   else ("historical_work_head_postimage",)
                   if plan.branch == "attempt_selecting_replan" else ())
    if (tuple(entry.role for entry in plan.graph_entries) != common_roles + branch_role
        or any(entry.ordinal != 0 for entry in plan.graph_entries)
        or result.mapping["receipt_graph_profile_id"] != _RECEIPT_GRAPH_PROFILE):
        raise ValueError("invalid P1 receipt graph profile")
    selected = command.basis.to_mapping()["decision_current_snapshot"]
    command_relation = command.relation.to_mapping()
    head = plan.head_postimage
    if (type(head) is not _program.DevelopmentProgramHeadRowValue
        or head.program_ref != command_relation["program_ref"]
        or head.current_program_version_ref != version.program_version_ref
        or head.current_program_version_number != version.program_version_number
        or head.head_revision != current.program_head.head_revision + 1
        or head.updated_at != plan.decided_at
        or rel["historical_head_ref"] != head.program_ref
        or rel["historical_head_revision"] != head.head_revision
        or rel["historical_head_digest"] != head.head_digest
        or rel["historical_head_postimage"] != _canonical(
            head._identity_mapping() | {"head_digest": head.head_digest})
        or decision.resulting_program_version_ref != version.program_version_ref
        or decision.decision_ref != version.creating_decision_ref
        or version.accepted_intent_revision_ref != current.accepted_intent.accepted_intent_revision_ref
           and plan.branch != "attempt_selecting_replan"
        or result.mapping["family_relation_digest"] != rel["relation_digest"]
        or receipt != plan.generic_receipt
        or _decision.compute_development_mutation_graph_digest(
            receipt=receipt, graph_entries=plan.graph_entries)
           != receipt.mutation_graph_digest):
        raise ValueError("incoherent P1 program postimage")
    is_replan = plan.branch == "attempt_selecting_replan"
    witness_fields = ("historical_work_head_ref", "historical_work_head_revision",
                      "historical_work_head_digest", "historical_work_head_postimage")
    if not is_replan:
        if (plan.work_head_postimage is not None
            or any(rel[name] is not None for name in witness_fields)
            or any(rows.get(table) for table in (
                "development_accepted_intent_revisions",
                "development_work_item_revisions", "development_revision_edges",
                "development_work_spec_bindings"))
            or any(entry.role == "historical_work_head_postimage"
                   for entry in plan.graph_entries)):
            raise ValueError("foreign P1 replan witness")
        return
    work_head = plan.work_head_postimage
    intent = one("development_accepted_intent_revisions")
    revision = one("development_work_item_revisions")
    binding = one("development_work_spec_bindings")
    memberships = rows.get("development_program_version_work_items", [])
    edges = rows.get("development_revision_edges", [])
    if (type(work_head) is not _program.DevelopmentWorkItemHeadRowValue
        or type(intent) is not _program.DevelopmentAcceptedIntentRevisionRowValue
        or type(revision) is not _program.DevelopmentWorkItemRevisionRowValue
        or type(binding) is not _program.DevelopmentWorkSpecBindingRowValue
        or len(edges) != 2 or len(memberships) != len(current.membership)):
        raise ValueError("incomplete P1 replan family")
    work_mapping = work_head._identity_mapping() | {"head_digest": work_head.head_digest}
    selected_member = [member for member in memberships
                       if type(member) is _program.DevelopmentProgramVersionWorkItemRowValue
                       and member.work_item_ref == selected["work_item_ref"]]
    role = [entry for entry in plan.graph_entries
            if entry.role == "historical_work_head_postimage"]
    if (work_head.program_ref != command_relation["program_ref"]
        or work_head.work_item_ref != selected["work_item_ref"]
        or work_head.current_work_item_revision_ref != revision.work_item_revision_ref
        or work_head.current_work_item_revision_number != revision.work_item_revision_number
        or work_head.current_work_item_revision_number != current.work_head.current_work_item_revision_number + 1
        or work_head.head_revision != current.work_head.head_revision + 1
        or work_head.work_state != "active" or work_head.updated_at != plan.decided_at
        or revision.program_ref != work_head.program_ref
        or revision.work_item_ref != work_head.work_item_ref
        or revision.prior_work_item_revision_ref != current.work_revision.work_item_revision_ref
        or revision.accepted_intent_revision_ref != intent.accepted_intent_revision_ref
        or revision.work_item_revision_kind != "replan"
        or intent.prior_accepted_intent_revision_ref != current.accepted_intent.accepted_intent_revision_ref
        or intent.accepted_intent_revision_ref != version.accepted_intent_revision_ref
        or binding.program_ref != work_head.program_ref
        or binding.program_version_ref != version.program_version_ref
        or binding.accepted_intent_revision_ref != intent.accepted_intent_revision_ref
        or binding.work_item_ref != work_head.work_item_ref
        or binding.work_item_revision_ref != revision.work_item_revision_ref
        or binding.recorded_at != plan.decided_at
        or len(selected_member) != 1
        or selected_member[0].work_item_revision_ref != revision.work_item_revision_ref
        or rel["historical_work_head_ref"] != work_head.work_item_ref
        or rel["historical_work_head_revision"] != work_head.head_revision
        or rel["historical_work_head_digest"] != work_head.head_digest
        or rel["historical_work_head_postimage"] != _canonical(work_mapping)
        or len(role) != 1 or role[0].record_ref != work_head.work_item_ref
        or role[0].record_digest != work_head.head_digest):
        raise ValueError("incoherent P1 replan witness")
