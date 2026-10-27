"""Pure P1 family construction over exact existing v1 row validators."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from ge_nwp_coordinator import _development_program_row_values as pr
from ge_nwp_coordinator import _development_decision_row_values as dr
from ge_nwp_coordinator._development_row_value_support import _domain_separated_digest
from ge_nwp_coordinator._rw0_c2_progression_contracts import (
    _RELATION_SCHEMA, _PREASSIGNMENT_FIELDS, _COMMAND_DIGEST_FIELDS,
    _SIBLINGS, _canonical, _digest, _self_digest,
    AdmittedCommandRelationV1, DecisionBasisV2, RecordProgressionDecisionCommandV1,
    CognitiveReplanProposalV1, CognitiveReplanWorkSpecTemplateV1,
    _require_bound_replan_work_spec, bind_replan_work_spec,
    derive_progression_branch, derive_replan_durable_refs,
)
from ge_nwp_coordinator._worker_execution_semantic_values import WorkSpecV1
from ge_nwp_coordinator._rw0_c2_progression_plan import (
    _P1CurrentRows, _row, build_p1_write_plan, verify_p1_plan_coherence,
)
from ge_nwp_coordinator._rw0_c2_progression_rows import (
    _P1Row, _ACCEPTANCE, _RELATION, _RESULT, _RELATION_LOGICAL,
    _TABLE_FIELDS, _checked_p1_row,
)
from test_c2b2_development_decision_row_values import _decision_identity
from test_post_execution_pure_owner_values import _sample, _seal, CLASS_BY_V
from test_rw0_c2_progression_contracts import _basis, _validation_for, _replan_proposal

NOW = "2029-01-01T00:00:00Z"


def test_command_digest_v2_six_assertions_bind_after_unchanged_siblings() -> None:
    command, _proposal, _refs, _work_spec, _plan = _replan_case()
    relation = command.relation.to_mapping()
    siblings = tuple(relation[name] for name, _domain in _SIBLINGS)
    assert len(_PREASSIGNMENT_FIELDS) == 24
    assert len(_COMMAND_DIGEST_FIELDS) == 30
    assert command.relation.command_digest == (
        "70a186fd5429da5b53e465f50755863e14e6875bd009f318e16cfee3e0facc10")
    vectors = {
        None: "06a2a03e8bf9b5f77a254e45fb18739670220ae4c412e87747851bfcb230d7a0",
        "candidate_acceptance": "ddd68b7d79c9752aff7bebdf0bddf1b8249aba8ce9d6a42932296106574e05e0",
        "candidate_repair": "9973b5df2070b546f0a76f5f4a9103b43a6f922c4a49fd27ea9854a63c1253d0",
        "attempt_selecting_replan": "7c80a9eee614e071876602b91a8fc2d1108f58b7fb8974785a47a03bd8ff43c6",
        "program_terminal_reject": "0a4389513551c446fd31e22530bafcb26dc8dc7d6c271b39751f4b3df808b6f2",
        "post_execution_program_block": "8eb827359c963f0a0040ab1b73c3cc39cd1bc3fed59e9284ef4e03e5a03674f6",
    }
    assert len(set(vectors.values())) == 6
    for assertion, digest in vectors.items():
        changed = replace(command, expected_branch=assertion)
        same_relation = changed.relation.to_mapping()
        assert tuple(same_relation[name] for name, _domain in _SIBLINGS) == siblings
        assert changed.relation.command_digest == command.relation.command_digest
        assert changed.command_digest == digest
        pairs = [(name, _RELATION_SCHEMA if name == "command_profile" else relation[name])
                 for name in _COMMAND_DIGEST_FIELDS]
        assert _digest("governed-execution.nwp-rw0-c2-guarded-command-digest.v2.identity",
                       pairs + [("expected_branch", assertion)], ordered=True) == digest
    for invalid in (1, False, "foreign", type("BranchSubclass", (str,), {})("candidate_acceptance")):
        with pytest.raises(ValueError):
            replace(command, expected_branch=invalid)


def _g(fields, columns, digest, adapter):
    return _row(table="fixture", fields=fields, columns=columns,
                digest_field=digest, adapter=adapter)


def _current(basis):
    snap = basis["decision_current_snapshot"]
    p, v, i, w, r = (snap[name] for name in (
        "program_ref", "program_version_ref", "accepted_intent_revision_ref",
        "work_item_ref", "work_item_revision_ref"))
    d = "genesis-decision-A"
    head = _g(dict(schema_id=pr._DEVELOPMENT_PROGRAM_HEAD_SCHEMA,
        program_ref=p, current_program_version_ref=v,
        current_program_version_number=1, head_revision=0,
        program_state="active", updated_at=NOW),
        pr._DEVELOPMENT_PROGRAM_HEAD_COLUMNS, "head_digest",
        pr.development_program_head_row_value_from_row_tuple)
    version = _g(dict(schema_id=pr._DEVELOPMENT_PROGRAM_VERSION_SCHEMA,
        program_version_ref=v, program_ref=p, program_version_number=1,
        program_version_kind="initial", creating_decision_ref=d,
        accepted_intent_revision_ref=i, created_at=NOW),
        pr._DEVELOPMENT_PROGRAM_VERSION_COLUMNS, "program_version_digest",
        pr.development_program_version_row_value_from_row_tuple)
    intent = _g(dict(schema_id=pr._DEVELOPMENT_ACCEPTED_INTENT_REVISION_SCHEMA,
        accepted_intent_revision_ref=i, program_ref=p,
        accepted_intent_revision_number=1, prior_accepted_intent_revision_ref=None,
        source_intent_ref="source-intent-A", source_intent_digest="11" * 32,
        safe_projection_digest="22" * 32, created_at=NOW),
        pr._DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS,
        "accepted_intent_revision_digest",
        pr.development_accepted_intent_revision_row_value_from_row_tuple)
    work_head = _g(dict(schema_id=pr._DEVELOPMENT_WORK_ITEM_HEAD_SCHEMA,
        work_item_ref=w, program_ref=p, current_work_item_revision_ref=r,
        current_work_item_revision_number=1, head_revision=0,
        work_state="active", updated_at=NOW),
        pr._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS, "head_digest",
        pr.development_work_item_head_row_value_from_row_tuple)
    work_revision = _g(dict(schema_id=pr._DEVELOPMENT_WORK_ITEM_REVISION_SCHEMA,
        work_item_revision_ref=r, program_ref=p, work_item_ref=w,
        work_item_revision_number=1, work_item_revision_kind="initial",
        prior_work_item_revision_ref=None, accepted_intent_revision_ref=i,
        created_at=NOW), pr._DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS,
        "work_item_revision_digest", pr.development_work_item_revision_row_value_from_row_tuple)
    member = _g(dict(schema_id=pr._DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_SCHEMA,
        program_ref=p, program_version_ref=v, work_item_ref=w,
        work_item_revision_ref=r, membership_ordinal=0, created_at=NOW),
        pr._DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS,
        "membership_digest", pr.development_program_version_work_item_row_value_from_row_tuple)
    genesis = _decision_identity("program_genesis")
    genesis.update(program_ref=p, mutation_ref="genesis-mutation-A", decision_ref=d,
        resulting_program_version_ref=v, coding_global_stop_ref=snap["global_stop_ref"],
        decided_at=NOW)
    genesis["decision_digest"] = _domain_separated_digest(dr._DEVELOPMENT_DECISION_DOMAIN, genesis)
    decision = dr.development_decision_row_value_from_row_tuple(
        tuple(genesis[name] for name in dr._DEVELOPMENT_DECISION_COLUMNS))
    return _P1CurrentRows(head, version, intent, work_head, work_revision,
                          decision, (member,), snap["global_stop_ref"], 0)


def _history(basis, sole, *, suffix="A"):
    fact = basis["scope_admission_fact"]
    value = dict(
        schema_id="governed-execution.nwp-rw0-c2-verified-sole-active.v1"
            if sole else "governed-execution.nwp-rw0-c2-verified-lineage-continuity.v1",
        basis_ref="sole-" + suffix if sole else "continuity-" + suffix,
        source_ref="sole-source-" + suffix if sole else "continuity-source-" + suffix,
        source_digest="33" * 32 if sole else "44" * 32,
        lineage_ref=fact["lineage_ref"], scope_ref=fact["scope_ref"],
        authority_epoch_ref="epoch-A", currentness_ref="currentness-A",
        currentness_digest="55" * 32,
    )
    if sole:
        value.update(active_authority_ref="authority-A",
                     sole_active_assertion_ref="assertion-A",
                     sole_active_assertion_digest="66" * 32)
    value.update(provenance_ref="provenance-A", provenance_digest="77" * 32)
    value["projection_digest"] = _self_digest(value, "projection_digest")
    key = "sole_active" if sole else "continuity"
    basis[f"historical_{key}_basis_ref"] = value["basis_ref"]
    basis[f"historical_{key}_basis_digest"] = value["projection_digest"]
    basis["bootstrap_guard_evidence"][f"{key}_basis_ref"] = value["basis_ref"]
    basis["bootstrap_guard_evidence"][f"{key}_basis_digest"] = value["projection_digest"]
    return value


def _command(basis, head, continuity, sole, *, expected_branch="candidate_acceptance", proposal=None,
             mutation_ref="p1-mutation-A"):
    fact, act, snap = (basis[name] for name in (
        "scope_admission_fact", "verified_admission_act", "decision_current_snapshot"))
    rel = dict(schema_id=_RELATION_SCHEMA,
        lineage_ref=fact["lineage_ref"], scope_ref=fact["scope_ref"],
        admission_fact_ref=fact["admission_fact_ref"],
        admission_fact_digest=fact["admission_fact_digest"],
        guard_profile=fact["guard_profile"], applicability=fact["applicability"],
        admission_act_ref=act["act_ref"], admission_act_digest=act["act_digest"],
        continuity_basis_ref=continuity["basis_ref"],
        continuity_basis_digest=continuity["projection_digest"],
        continuity_source_ref=continuity["source_ref"],
        continuity_source_digest=continuity["source_digest"],
        sole_active_basis_ref=sole["basis_ref"],
        sole_active_basis_digest=sole["projection_digest"],
        sole_active_source_ref=sole["source_ref"],
        sole_active_source_digest=sole["source_digest"],
        mutation_ref=mutation_ref, program_ref=snap["program_ref"],
        decision_basis_ref=basis["basis_ref"],
        decision_basis_digest=basis["basis_digest"],
        expected_head_ref=head.current_program_version_ref,
        expected_head_revision=head.head_revision,
        expected_head_digest=head.head_digest)
    preimage = [(name, _RELATION_SCHEMA if name == "command_profile" else rel[name])
                for name in _PREASSIGNMENT_FIELDS]
    for name, domain in _SIBLINGS:
        rel[name] = _digest(domain, preimage, ordered=True)
    rel["relation_digest"] = _self_digest(rel, "relation_digest")
    return RecordProgressionDecisionCommandV1(
        AdmittedCommandRelationV1.from_mapping(rel),
        DecisionBasisV2.from_mapping(basis), expected_branch, proposal)


def test_acceptance_plan_has_one_fact_and_one_generic_receipt() -> None:
    basis = deepcopy(_basis())
    continuity = _history(basis, False)
    sole = _history(basis, True)
    guard = basis["bootstrap_guard_evidence"]
    guard["guard_digest"] = _self_digest(guard, "guard_digest")
    basis["basis_digest"] = _self_digest(basis, "basis_digest")
    current = _current(basis)
    command = _command(basis, current.program_head, continuity, sole)
    reduction = derive_progression_branch(
        command.basis, _validation_for("accept"),
        CLASS_BY_V["V15"].from_mapping(_sample("V15")),
        expected_branch="candidate_acceptance", replan_proposal=None)
    plan = build_p1_write_plan(command=command, reduction=reduction,
        current=current, continuity=continuity, sole=sole, timestamp=NOW)
    tables = [table for table, _ in plan.rows]
    assert plan.branch == "candidate_acceptance"
    assert tables.count(_ACCEPTANCE) == 1
    assert tables.count("development_mutation_receipts") == 1
    assert tables.count("development_program_version_work_items") == 1
    assert len(plan.graph_entries) == 11
    assert all(type(row) is _P1Row for table, row in plan.rows if table.startswith("rw0_c2_"))


def _replan_case(*, objective: str = "Artificial replan only.",
                 requirements: list[str] | None = None,
                 exclusions: list[str] | None = None):
    basis = deepcopy(_basis())
    basis["validation_disposition"] = _validation_for("replan").to_mapping()
    model = basis["recommendation_consistency_evaluation"]
    assert type(model) is dict
    model["authoritative_branch"] = "attempt_selecting_replan"
    model["result"] = "inconsistent"
    model["reason"] = "mapped_branch_differs_from_authoritative_branch"
    basis["recommendation_consistency_evaluation"] = _seal("V34", model)
    proposal = _replan_proposal(basis)
    template = proposal.work_spec_template.to_mapping()
    template["objective"] = objective
    if requirements is not None:
        template["requirements"] = requirements
    if exclusions is not None:
        template["exclusions"] = exclusions
    template["template_digest"] = _self_digest(template, "template_digest")
    proposal = CognitiveReplanProposalV1(
        proposal.source_intent_ref, proposal.source_intent_digest,
        CognitiveReplanWorkSpecTemplateV1.from_mapping(template))
    basis["replan_proposal_safe_projection"] = proposal.safe_projection()
    continuity = _history(basis, False)
    sole = _history(basis, True)
    basis["bootstrap_guard_evidence"]["guard_digest"] = _self_digest(
        basis["bootstrap_guard_evidence"], "guard_digest")
    basis["basis_digest"] = _self_digest(basis, "basis_digest")
    current = _current(basis)
    command = _command(basis, current.program_head, continuity, sole,
        expected_branch="attempt_selecting_replan", proposal=proposal)
    reduction = derive_progression_branch(
        command.basis, _validation_for("replan"),
        CLASS_BY_V["V15"].from_mapping(_sample("V15")),
        expected_branch="attempt_selecting_replan", replan_proposal=proposal)
    assert reduction.branch == "attempt_selecting_replan"
    relation = command.relation.to_mapping()
    snap = basis["decision_current_snapshot"]
    refs = derive_replan_durable_refs(
        command_digest=command.command_digest,
        program_ref=relation["program_ref"],
        current_program_version_ref=snap["program_version_ref"],
        current_accepted_intent_revision_ref=snap["accepted_intent_revision_ref"],
        work_item_ref=snap["work_item_ref"],
        current_work_item_revision_ref=snap["work_item_revision_ref"],
        source_intent_ref=proposal.source_intent_ref,
        source_intent_digest=proposal.source_intent_digest,
        work_spec_template_digest=proposal.work_spec_template.digest,
        preassigned_version_ref=relation["preassigned_version_ref"],
    )
    work_spec = bind_replan_work_spec(
        proposal.work_spec_template, work_spec_ref=refs[2],
        program_version_ref=relation["preassigned_version_ref"],
        accepted_intent_revision_ref=refs[0], work_item_revision_ref=refs[1])
    plan = build_p1_write_plan(command=command, reduction=reduction,
        current=current, continuity=continuity, sole=sole, timestamp=NOW)
    return command, proposal, refs, work_spec, plan


def test_replan_identity_order_and_existing_0002_family_are_deterministic() -> None:
    first = _replan_case()
    second = _replan_case()
    command, proposal, refs, work_spec, plan = first
    assert type(work_spec) is WorkSpecV1
    assert command.basis.canonical_bytes == second[0].basis.canonical_bytes
    assert command.relation.canonical_bytes == second[0].relation.canonical_bytes
    assert refs == second[2]
    assert work_spec.to_mapping() == second[3].to_mapping()
    assert tuple((table, row.mapping if type(row) is _P1Row else row)
                 for table, row in plan.rows) == tuple(
                     (table, row.mapping if type(row) is _P1Row else row)
                     for table, row in second[4].rows)
    relation = command.relation.to_mapping()
    assert work_spec.program_version_ref == relation["preassigned_version_ref"]
    assert (work_spec.accepted_intent_revision_ref,
            work_spec.work_item_revision_ref, work_spec.work_spec_ref) == refs
    assert set(proposal.work_spec_template.safe_projection()).isdisjoint({
        "program_version_ref", "accepted_intent_revision_ref", "work_item_revision_ref",
        "work_spec_ref", "work_spec_digest", "objective", "requirements", "exclusions"})
    tables = [table for table, _ in plan.rows]
    for table in ("development_accepted_intent_revisions",
                  "development_work_item_revisions", "development_work_spec_bindings"):
        assert tables.count(table) == 1
    assert tables.count("development_revision_edges") == 2
    assert tables.count("development_program_version_work_items") == 1
    assert tables.count("development_mutation_receipts") == 1
    assert tables.count("rw0_c2_bootstrap_acceptance_facts") == 0
    assert len(plan.graph_entries) == 11
    assert tuple(entry.role for entry in plan.graph_entries)[-1] == "historical_work_head_postimage"
    relation_row = next(row for table, row in plan.rows if table == _RELATION)
    result_row = next(row for table, row in plan.rows if table == _RESULT)
    assert relation_row.mapping["schema_id"] == "governed-execution.nwp-rw0-c2-guarded-family-relation.v2"
    assert result_row.mapping["schema_id"] == "governed-execution.nwp-rw0-c2-guarded-progression-result.v2"
    assert result_row.mapping["receipt_graph_profile_id"] == "governed-execution.nwp-rw0-c2-receipt-graph-profile.v2"
    assert plan.work_head_postimage is not None
    witness = relation_row.mapping
    work_head = plan.work_head_postimage
    assert witness["historical_work_head_ref"] == work_head.work_item_ref
    assert witness["historical_work_head_revision"] == work_head.head_revision
    assert witness["historical_work_head_digest"] == work_head.head_digest
    assert witness["historical_work_head_postimage"] == _canonical(
        work_head._identity_mapping() | {"head_digest": work_head.head_digest})
    assert plan.graph_entries[-1].record_ref == work_head.work_item_ref
    assert plan.graph_entries[-1].record_digest == work_head.head_digest
    assert len(_RELATION_LOGICAL) == 31
    assert _RELATION_LOGICAL[22:26] == (
        "historical_work_head_ref", "historical_work_head_revision",
        "historical_work_head_digest", "historical_work_head_postimage")
    assert len(_TABLE_FIELDS[_RELATION]) == 35
    assert plan.generic_receipt.mutation_graph_digest == second[4].generic_receipt.mutation_graph_digest
    assert proposal.work_spec_template.digest == "61dc84e3b4fdc2cc2a43291d65945c041b9b74dbf5b5a2234258b0164802dcce"
    assert proposal.work_spec_template.safe_projection()["safe_projection_digest"] == "70240825c9165e43289b8e6468089f2d6e91a370f521c7b747fe64f837d3891b"
    assert proposal.safe_projection()["proposal_digest"] == "c8bc73fd8957634173eaa889b13d926c3532d16ceaf0f6e5cd42766886277e68"
    assert command.basis.digest == "3dcd3729b90e18b045d447420894261d05187f4342dc3af2634192d2bc50827d"
    assert command.relation.command_digest == "70a186fd5429da5b53e465f50755863e14e6875bd009f318e16cfee3e0facc10"
    assert command.command_digest == "7c80a9eee614e071876602b91a8fc2d1108f58b7fb8974785a47a03bd8ff43c6"
    assert relation["preassigned_version_ref"] == "de16c32f21a01bb2c062c63cd024857c041a4c5984446047a8df0481efd4f84c"
    assert refs == (
        "9d05a865af7f525530d3a33f74393734162340cabeece693cf1cc8017504fab8",
        "8f454c0c381e8d7093125be0ea26e6b6797c040ae28fd03c81caeeee572d2144",
        "66e14a94c24b97119c77a03374bced3081a069315d6864a511398d9206dff2b7",
    )
    assert work_spec.work_spec_digest == "96181b95bad1f0cd06444d7d32602619318e10631d3c963dabd8fa7e462b756e"


def test_replan_plan_cross_record_witness_cannot_detach_revision_membership_or_work_spec() -> None:
    command, _proposal, _refs, _spec, plan = _replan_case()
    current = _current(command.basis.to_mapping())
    verify_p1_plan_coherence(plan, command, current)
    wrong_work = _row(table="development_work_item_heads", fields={
        **plan.work_head_postimage._identity_mapping(),
        "current_work_item_revision_ref": current.work_revision.work_item_revision_ref,
    }, columns=pr._DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS,
        digest_field="head_digest", adapter=pr.development_work_item_head_row_value_from_row_tuple)
    with pytest.raises(ValueError):
        verify_p1_plan_coherence(replace(plan, work_head_postimage=wrong_work), command, current)
    rows = list(plan.rows)
    index = next(i for i, (table, _row_value) in enumerate(rows)
                 if table == "development_program_version_work_items")
    member = rows[index][1]
    wrong_member = _row(table="development_program_version_work_items", fields={
        **member._identity_mapping(),
        "work_item_revision_ref": current.work_revision.work_item_revision_ref,
    }, columns=pr._DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS,
        digest_field="membership_digest",
        adapter=pr.development_program_version_work_item_row_value_from_row_tuple)
    rows[index] = (rows[index][0], wrong_member)
    with pytest.raises(ValueError):
        verify_p1_plan_coherence(replace(plan, rows=tuple(rows)), command, current)
    donor = _replan_case(objective="Another bound WorkSpec.")[4]
    donor_binding = next(row for table, row in donor.rows
                         if table == "development_work_spec_bindings")
    rows = tuple((table, donor_binding if table == "development_work_spec_bindings" else row)
                 for table, row in plan.rows)
    with pytest.raises(ValueError):
        verify_p1_plan_coherence(replace(plan, rows=rows), command, current)


@pytest.mark.parametrize("fault", (
    "missing", "duplicate", "extra", "wrong_branch", "wrong_ref", "wrong_digest",
))
def test_replan_graph_role_mutants_reject_before_write(fault: str) -> None:
    command, _proposal, _refs, _spec, plan = _replan_case()
    current = _current(command.basis.to_mapping())
    entries = list(plan.graph_entries)
    role = entries[-1]
    if fault == "missing":
        entries.pop()
    elif fault == "duplicate":
        entries.append(role)
    elif fault == "extra":
        entries.append(dr.development_mutation_graph_entry(
            role="acceptance_fact", ordinal=0, record_ref="foreign-fact",
            record_digest="0" * 64))
    else:
        entries[-1] = dr.development_mutation_graph_entry(
            role="acceptance_fact" if fault == "wrong_branch" else role.role,
            ordinal=0,
            record_ref="foreign-work" if fault == "wrong_ref" else role.record_ref,
            record_digest="0" * 64 if fault == "wrong_digest" else role.record_digest)
    with pytest.raises(ValueError):
        verify_p1_plan_coherence(replace(plan, graph_entries=tuple(entries)), command, current)


@pytest.mark.parametrize("changed", [
    {"objective": "A distinct artificial replan objective."},
    {"requirements": ["A distinct scoped requirement."]},
    {"exclusions": ["A distinct excluded effect."]},
])
def test_private_replan_content_changes_every_downstream_identity(changed) -> None:
    first = _replan_case()
    changed = _replan_case(**changed)
    for left, right in (
        (first[1].work_spec_template.digest, changed[1].work_spec_template.digest),
        (first[1].safe_projection()["proposal_digest"], changed[1].safe_projection()["proposal_digest"]),
        (first[0].basis.digest, changed[0].basis.digest),
        (first[0].relation.to_mapping()["preassigned_version_ref"],
         changed[0].relation.to_mapping()["preassigned_version_ref"]),
        (first[0].command_digest, changed[0].command_digest),
        (first[3].work_spec_digest, changed[3].work_spec_digest),
    ):
        assert left != right
    assert all(left != right for left, right in zip(first[2], changed[2], strict=True))


def test_replan_proposal_rejects_detached_template_and_final_work_spec_input() -> None:
    command, proposal, refs, work_spec, _ = _replan_case()
    basis = command.basis.to_mapping()
    donor = _replan_case(objective="Different donor content.")[1]
    with pytest.raises(ValueError):
        RecordProgressionDecisionCommandV1(
            command.relation, command.basis, "attempt_selecting_replan", donor)
    bad = proposal.work_spec_template.to_mapping()
    bad["work_spec_ref"] = "caller-picked"
    bad["template_digest"] = _self_digest(bad, "template_digest")
    with pytest.raises(ValueError):
        CognitiveReplanWorkSpecTemplateV1.from_mapping(bad)
    with pytest.raises(TypeError):
        CognitiveReplanProposalV1(proposal.source_intent_ref,
            proposal.source_intent_digest, proposal.work_spec_template,
            work_spec=work_spec)
    assert "program_version_ref" not in basis["replan_proposal_safe_projection"]
    relation = command.relation.to_mapping()
    with pytest.raises(ValueError):
        _require_bound_replan_work_spec(
            proposal.work_spec_template, candidate=work_spec,
            work_spec_ref=refs[2], program_version_ref="wrong-version-A",
            accepted_intent_revision_ref=refs[0], work_item_revision_ref=refs[1])
    with pytest.raises(ValueError):
        _require_bound_replan_work_spec(
            proposal.work_spec_template, candidate=work_spec,
            work_spec_ref="wrong-work-spec-A",
            program_version_ref=relation["preassigned_version_ref"],
            accepted_intent_revision_ref=refs[0], work_item_revision_ref=refs[1])
    with pytest.raises(ValueError):
        _require_bound_replan_work_spec(
            proposal.work_spec_template, candidate=work_spec,
            work_spec_ref=refs[2], program_version_ref=relation["preassigned_version_ref"],
            accepted_intent_revision_ref="wrong-intent-A", work_item_revision_ref=refs[1])


def test_template_rejects_future_coordinates_unknown_duplicate_and_bad_paths() -> None:
    template = _replan_case()[1].work_spec_template
    raw = template.canonical_bytes
    with pytest.raises(ValueError):
        CognitiveReplanWorkSpecTemplateV1.from_json(raw + b" ")
    with pytest.raises(ValueError):
        CognitiveReplanWorkSpecTemplateV1.from_json(
            raw[:-1] + b',"program_version_ref":"placeholder"}')
    changed = template.to_mapping()
    changed["program_version_ref"] = "placeholder"
    changed["template_digest"] = _self_digest(changed, "template_digest")
    with pytest.raises(ValueError):
        CognitiveReplanWorkSpecTemplateV1.from_mapping(changed)
    changed = template.to_mapping()
    changed["authorized_paths"] = ["../escape"]
    changed["template_digest"] = _self_digest(changed, "template_digest")
    with pytest.raises(ValueError):
        CognitiveReplanWorkSpecTemplateV1.from_mapping(changed)
    changed = template.to_mapping()
    changed["requirements"] = [True]
    changed["template_digest"] = _self_digest(changed, "template_digest")
    with pytest.raises(ValueError):
        CognitiveReplanWorkSpecTemplateV1.from_mapping(changed)


def test_replan_dependency_order_is_acyclic_and_version_neutral() -> None:
    stages = (
        "private_template", "template_safe_projection", "proposal_safe_projection",
        "decision_basis", "six_preassignments", "command_digest",
        "three_replan_refs", "final_work_spec", "existing_0002_rows",
        "receipt_graph", "commit",
    )
    edges = tuple(zip(stages, stages[1:], strict=False))
    order = {node: index for index, node in enumerate(stages)}
    assert len(order) == len(stages)
    assert all(order[before] < order[after] for before, after in edges)
    command, proposal, refs, final, _ = _replan_case()
    early = command.basis.to_mapping()["replan_proposal_safe_projection"]
    assert "program_version_ref" not in proposal.work_spec_template.to_mapping()
    assert "program_version_ref" not in early["work_spec_template_safe_projection"]
    assert "work_spec_digest" not in early["work_spec_template_safe_projection"]
    assert final.program_version_ref == command.relation.to_mapping()["preassigned_version_ref"]


@pytest.mark.parametrize("changed", [
    {"historical_work_head_ref": None},
    {"historical_work_head_revision": None},
    {"historical_work_head_digest": None},
    {"historical_work_head_postimage": None},
    {"historical_work_head_ref": "foreign-work-A"},
    {"historical_work_head_revision": 999},
    {"historical_work_head_digest": "0" * 64},
    {"historical_work_head_postimage": b"{}"},
])
def test_replan_work_head_witness_rejects_missing_mixed_or_foreign_value(changed) -> None:
    row = next(row for table, row in _replan_case()[4].rows if table == _RELATION)
    mapping = row.mapping | changed
    with pytest.raises(ValueError):
        _checked_p1_row(_RELATION, tuple(mapping[name] for name in _TABLE_FIELDS[_RELATION]))


@pytest.mark.parametrize("normal,branch,roles", [
    ("accept", "candidate_acceptance", ("acceptance_fact",)),
    ("repair", "candidate_repair", ()),
    ("terminal", "program_terminal_reject", ()),
    ("nonconclusive", "post_execution_program_block", ()),
])
def test_v2_nonreplan_role_sets_and_null_work_head_witness(normal, branch, roles) -> None:
    basis = deepcopy(_basis())
    basis["validation_disposition"] = _validation_for(normal).to_mapping()
    model = basis["recommendation_consistency_evaluation"]
    model["authoritative_branch"] = branch
    if branch != "candidate_acceptance":
        model["result"] = "inconsistent"
        model["reason"] = "mapped_branch_differs_from_authoritative_branch"
    basis["recommendation_consistency_evaluation"] = _seal("V34", model)
    continuity = _history(basis, False)
    sole = _history(basis, True)
    basis["bootstrap_guard_evidence"]["guard_digest"] = _self_digest(
        basis["bootstrap_guard_evidence"], "guard_digest")
    basis["basis_digest"] = _self_digest(basis, "basis_digest")
    current = _current(basis)
    command = _command(basis, current.program_head, continuity, sole,
                       expected_branch=branch)
    reduction = derive_progression_branch(command.basis, _validation_for(normal),
        CLASS_BY_V["V15"].from_mapping(_sample("V15")),
        expected_branch=branch, replan_proposal=None)
    assert reduction.branch == branch
    plan = build_p1_write_plan(command=command, reduction=reduction,
        current=current, continuity=continuity, sole=sole, timestamp=NOW)
    relation = next(row for table, row in plan.rows if table == _RELATION)
    assert plan.work_head_postimage is None
    assert all(relation.mapping[name] is None for name in (
        "historical_work_head_ref", "historical_work_head_revision",
        "historical_work_head_digest", "historical_work_head_postimage"))
    if roles:
        assert tuple(entry.role for entry in plan.graph_entries[-len(roles):]) == roles
    assert len(plan.graph_entries) == 10 + len(roles)
    if branch == "candidate_acceptance":
        assert sum(table == _ACCEPTANCE for table, _ in plan.rows) == 1
    else:
        assert sum(table == _ACCEPTANCE for table, _ in plan.rows) == 0
