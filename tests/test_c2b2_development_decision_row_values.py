from __future__ import annotations

import hashlib
import json

import pytest

from ge_nwp_coordinator import _development_decision_row_values as rows
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError


NOW = "2026-08-15T12:34:56Z"
SHA = "a" * 64


DECISION_COLUMNS = (
    "schema_id","mutation_ref","decision_ref","program_ref","decision_kind",
    "decision_variant","basis_decision_ref","basis_program_version_ref",
    "basis_program_version_number","expected_program_head_revision",
    "resulting_program_version_ref","resulting_program_version_number",
    "selected_semantic_attempt_ref","selected_candidate_ref","selected_attempt_fence_ref",
    "selected_attempt_fence_digest","target_effect_intent_ref","target_effect_class",
    "target_effect_fence_ref","target_effect_fence_digest",
    "expected_target_effect_head_revision","target_delivery_attempt_ref",
    "originating_command_ref","originating_command_digest","target_capsule_manifest_ref",
    "target_portable_capsule_digest","coding_global_stop_ref","coding_global_stop_version",
    "source_directive_ref","source_directive_digest","source_evidence_ref",
    "source_evidence_digest","preassigned_semantic_attempt_ref",
    "preassigned_candidate_ref","preassigned_effect_intent_ref",
    "preassigned_effect_fence_ref","preassigned_delivery_attempt_ref",
    "resulting_accepted_intent_revision_ref","resulting_work_item_ref",
    "resulting_work_item_revision_ref","reason_code","decided_at","decision_digest",
)
RECEIPT_COLUMNS = (
    "schema_id","mutation_ref","mutation_family","command_schema_id","command_digest",
    "program_ref","decision_ref","result_program_version_ref",
    "result_semantic_attempt_ref","result_effect_intent_ref","result_effect_fence_ref",
    "result_delivery_attempt_ref","result_observation_ref","result_decision_ref",
    "result_class","result_projection_digest","mutation_graph_digest","outcome",
    "committed_at",
)

DECISION_KINDS = (
    "initialize", "accept", "repair", "replan", "terminal_reject", "block",
    "redeliver", "cancel",
)
DECISION_VARIANTS = (
    "program_genesis", "candidate_acceptance", "candidate_repair", "program_replan",
    "attempt_selecting_replan", "program_terminal_reject", "program_block",
    "productive_redelivery", "cancellation_redelivery", "effect_cancellation",
)
GRAPH_DOMAIN = "governed-execution.nwp-development-mutation-receipt.v1.identity"
GRAPH_ENTRY_KEYS = ("role", "ordinal", "record_ref", "record_digest")


def _digest(domain: str, identity: dict[str, object]) -> str:
    canonical=json.dumps(identity,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(",",":")).encode("utf-8",errors="strict")
    return hashlib.sha256(domain.encode("utf-8")+b"\0"+canonical).hexdigest()


def test_decision_and_receipt_columns_are_exact_independent_literals() -> None:
    assert rows._DEVELOPMENT_DECISION_COLUMNS == DECISION_COLUMNS
    assert rows._DEVELOPMENT_MUTATION_RECEIPT_COLUMNS == RECEIPT_COLUMNS
    assert len(DECISION_COLUMNS)==43
    assert len(RECEIPT_COLUMNS)==19


def test_decision_receipt_schema_domains_and_closed_vocabularies_are_literal() -> None:
    assert rows._DEVELOPMENT_DECISION_SCHEMA == "governed-execution.nwp-development-decision.v1"
    assert rows._DEVELOPMENT_DECISION_DOMAIN == "governed-execution.nwp-development-decision.v1.identity"
    assert rows._DEVELOPMENT_MUTATION_RECEIPT_SCHEMA == "governed-execution.nwp-development-mutation-receipt.v1"
    assert rows._DEVELOPMENT_MUTATION_RECEIPT_DOMAIN == GRAPH_DOMAIN
    assert rows._DECISION_KINDS == DECISION_KINDS
    assert rows._DECISION_VARIANTS == DECISION_VARIANTS
    assert rows._TARGET_EFFECT_CLASSES == ("author_candidate", "cancel_effect", "local_git_commit", "review_candidate", "validate_candidate")


def _decision_identity(variant: str) -> dict[str, object]:
    identity={
        "schema_id":"governed-execution.nwp-development-decision.v1",
        "mutation_ref":"mutation-1","decision_ref":"decision-1","program_ref":"program-1",
        "decision_kind":"initialize","decision_variant":variant,
        "basis_decision_ref":None,"basis_program_version_ref":None,
        "basis_program_version_number":None,"expected_program_head_revision":2,
        "resulting_program_version_ref":None,"resulting_program_version_number":None,
        "selected_semantic_attempt_ref":None,"selected_candidate_ref":None,
        "selected_attempt_fence_ref":None,"selected_attempt_fence_digest":None,
        "target_effect_intent_ref":None,"target_effect_class":None,
        "target_effect_fence_ref":None,"target_effect_fence_digest":None,
        "expected_target_effect_head_revision":None,"target_delivery_attempt_ref":None,
        "originating_command_ref":None,"originating_command_digest":None,
        "target_capsule_manifest_ref":None,"target_portable_capsule_digest":None,
        "coding_global_stop_ref":"stop-1","coding_global_stop_version":0,
        "source_directive_ref":None,"source_directive_digest":None,
        "source_evidence_ref":None,"source_evidence_digest":None,
        "preassigned_semantic_attempt_ref":None,"preassigned_candidate_ref":None,
        "preassigned_effect_intent_ref":None,"preassigned_effect_fence_ref":None,
        "preassigned_delivery_attempt_ref":None,
        "resulting_accepted_intent_revision_ref":None,"resulting_work_item_ref":None,
        "resulting_work_item_revision_ref":None,"reason_code":"decision.recorded","decided_at":NOW,
    }
    basis={"basis_decision_ref":"decision-0","basis_program_version_ref":"version-1","basis_program_version_number":1}
    result={"resulting_program_version_ref":"version-2","resulting_program_version_number":2}
    selection={"selected_semantic_attempt_ref":"attempt-1","selected_candidate_ref":"candidate-1","selected_attempt_fence_ref":"attempt-fence-1","selected_attempt_fence_digest":"1"*64}
    target={"target_effect_intent_ref":"effect-1","target_effect_class":"author_candidate","target_effect_fence_ref":"effect-fence-1","target_effect_fence_digest":"2"*64,"expected_target_effect_head_revision":0}
    command={"originating_command_ref":"command-1","originating_command_digest":"3"*64}
    pre_attempt={"preassigned_semantic_attempt_ref":"attempt-2","preassigned_candidate_ref":"candidate-2"}
    if variant=="program_genesis":
        identity.update({"decision_kind":"initialize","expected_program_head_revision":0,"resulting_program_version_ref":"version-1","resulting_program_version_number":1,**pre_attempt})
    elif variant=="candidate_acceptance":
        identity.update({"decision_kind":"accept",**basis,**result,**selection})
    elif variant=="candidate_repair":
        identity.update({"decision_kind":"repair",**basis,**result,**selection,**pre_attempt})
    elif variant=="program_replan":
        identity.update({"decision_kind":"replan",**basis,**result,"resulting_accepted_intent_revision_ref":"intent-2"})
    elif variant=="attempt_selecting_replan":
        identity.update({"decision_kind":"replan",**basis,**result,**selection,**pre_attempt,"resulting_accepted_intent_revision_ref":"intent-2","resulting_work_item_ref":"work-2","resulting_work_item_revision_ref":"work-revision-2"})
    elif variant=="program_terminal_reject":
        identity.update({"decision_kind":"terminal_reject",**basis,**result,**selection})
    elif variant=="program_block":
        identity.update({"decision_kind":"block",**basis,**result})
    elif variant=="productive_redelivery":
        identity.update({"decision_kind":"redeliver",**basis,**selection,**target,**command,"target_delivery_attempt_ref":"delivery-1","preassigned_delivery_attempt_ref":"delivery-2"})
    elif variant=="cancellation_redelivery":
        target["target_effect_class"]="cancel_effect"
        identity.update({"decision_kind":"redeliver",**basis,**selection,**target,**command,"target_delivery_attempt_ref":"delivery-1","preassigned_delivery_attempt_ref":"delivery-2"})
    elif variant=="effect_cancellation":
        identity.update({"decision_kind":"cancel",**basis,**selection,**target,**command,
            "source_directive_ref":"directive-1","source_directive_digest":"4"*64,
            "source_evidence_ref":"evidence-1","source_evidence_digest":"5"*64,
            "preassigned_effect_intent_ref":"effect-cancel-1",
            "preassigned_effect_fence_ref":"effect-fence-cancel-1",
            "preassigned_delivery_attempt_ref":"delivery-cancel-1"})
    else: raise AssertionError(variant)
    return identity


@pytest.mark.parametrize(
    ("variant","type_name"),
    (
        ("program_genesis","_ProgramGenesisDecision"),
        ("candidate_acceptance","_CandidateAcceptanceDecision"),
        ("candidate_repair","_CandidateRepairDecision"),
        ("program_replan","_ProgramReplanDecision"),
        ("attempt_selecting_replan","_AttemptSelectingReplanDecision"),
        ("program_terminal_reject","_ProgramTerminalRejectDecision"),
        ("program_block","_ProgramBlockDecision"),
        ("productive_redelivery","_ProductiveRedeliveryDecision"),
        ("cancellation_redelivery","_CancellationRedeliveryDecision"),
        ("effect_cancellation","_EffectCancellationDecision"),
    ),
)
def test_ten_decision_variants_verify_exact_closed_envelopes(variant: str,type_name: str)->None:
    identity=_decision_identity(variant)
    digest=_digest("governed-execution.nwp-development-decision.v1.identity",identity)
    physical=dict(identity);physical["decision_digest"]=digest
    value=rows.development_decision_row_value_from_row_tuple(tuple(physical[column] for column in DECISION_COLUMNS))
    assert value.identity_mapping()==identity
    assert value.computed_digest()==digest
    assert value.decision_variant==variant
    assert type(value.decision).__name__==type_name


def test_decision_counterfactual_null_and_capsule_algebra_fails_closed() -> None:
    identity=_decision_identity("effect_cancellation")
    identity["target_capsule_manifest_ref"]="capsule-1"
    identity["target_portable_capsule_digest"]="6"*64
    physical=dict(identity);physical["decision_digest"]=_digest("governed-execution.nwp-development-decision.v1.identity",identity)
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.development_decision_row_value_from_row_tuple(tuple(physical[column] for column in DECISION_COLUMNS))


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("decision_kind", "repair"),
        ("decision_variant", "unknown_variant"),
        ("selected_candidate_ref", None),
        ("target_capsule_manifest_ref", "capsule-1"),
    ),
)
def test_decision_kind_variant_required_and_forbidden_field_counterfactuals(
    field: str,
    replacement: object,
) -> None:
    identity=_decision_identity("candidate_acceptance")
    identity[field]=replacement
    physical=dict(identity);physical["decision_digest"]=_digest("governed-execution.nwp-development-decision.v1.identity",identity)
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.development_decision_row_value_from_row_tuple(tuple(physical[column] for column in DECISION_COLUMNS))


FAMILIES = (
    ("initialize_development_program","governed-execution.nwp-initialize-development-program-command.v1","development_program_initialized","governed-execution.nwp-initialize-development-program-result.v1","governed-execution.nwp-initialize-development-program-result.v1.identity"),
    ("establish_development_author_effect_intent","governed-execution.nwp-establish-development-author-effect-intent-command.v1","development_author_effect_intent_established","governed-execution.nwp-establish-development-author-effect-intent-result.v1","governed-execution.nwp-establish-development-author-effect-intent-result.v1.identity"),
    ("establish_development_bound_effect_intent","governed-execution.nwp-establish-development-bound-effect-intent-command.v1","development_bound_effect_intent_established","governed-execution.nwp-establish-development-bound-effect-intent-result.v1","governed-execution.nwp-establish-development-bound-effect-intent-result.v1.identity"),
    ("ingest_development_source_observation","governed-execution.nwp-ingest-development-source-observation-command.v1","development_source_observation_ingested","governed-execution.nwp-ingest-development-source-observation-result.v1","governed-execution.nwp-ingest-development-source-observation-result.v1.identity"),
    ("record_development_progression_decision","governed-execution.nwp-record-development-progression-decision-command.v1","development_progression_decision_recorded","governed-execution.nwp-record-development-progression-decision-result.v1","governed-execution.nwp-record-development-progression-decision-result.v1.identity"),
)


def _receipt(family_index: int,graph_digest: str="f"*64)->tuple[object,...]:
    family,command_schema,result_class,result_schema,result_domain=FAMILIES[family_index]
    values={"schema_id":"governed-execution.nwp-development-mutation-receipt.v1",
        "mutation_ref":"mutation-1","mutation_family":family,"command_schema_id":command_schema,
        "command_digest":SHA,"program_ref":"program-1","decision_ref":None,
        "result_program_version_ref":None,"result_semantic_attempt_ref":None,
        "result_effect_intent_ref":None,"result_effect_fence_ref":None,
        "result_delivery_attempt_ref":None,"result_observation_ref":None,
        "result_decision_ref":None,"result_class":result_class,
        "mutation_graph_digest":graph_digest,"outcome":"committed","committed_at":NOW}
    if family_index in (0,4):
        values.update({"decision_ref":"decision-1","result_program_version_ref":"version-1","result_decision_ref":"decision-1"})
        projection={"schema_id":result_schema,"program_ref":"program-1","decision_ref":"decision-1","result_program_version_ref":"version-1","result_decision_ref":"decision-1"}
    elif family_index in (1,2):
        values.update({"decision_ref":"decision-1","result_program_version_ref":"version-1","result_semantic_attempt_ref":"attempt-1","result_effect_intent_ref":"effect-1","result_effect_fence_ref":"effect-fence-1","result_delivery_attempt_ref":"delivery-1"})
        projection={"schema_id":result_schema,"program_ref":"program-1","decision_ref":"decision-1","result_program_version_ref":"version-1","result_semantic_attempt_ref":"attempt-1","result_effect_intent_ref":"effect-1","result_effect_fence_ref":"effect-fence-1","result_delivery_attempt_ref":"delivery-1"}
    else:
        values["result_observation_ref"]="observation-1"
        projection={"schema_id":result_schema,"program_ref":"program-1","result_observation_ref":"observation-1"}
    values["result_projection_digest"]=_digest(result_domain,projection)
    return tuple(values[column] for column in RECEIPT_COLUMNS)


@pytest.mark.parametrize("family_index",range(5))
def test_five_receipt_result_projections_verify_independent_domains(family_index:int)->None:
    value=rows.development_mutation_receipt_row_value_from_row_tuple(_receipt(family_index))
    assert value.mutation_family==FAMILIES[family_index][0]
    assert value.result_projection.computed_digest()==value.result_projection_digest
    assert not hasattr(value,"computed_digest")
    assert not hasattr(value,"identity_mapping")
    assert not hasattr(value,"graph_verified")


@pytest.mark.parametrize(
    ("index", "replacement"),
    (
        (2, "establish_development_author_effect_intent"),
        (14, "development_author_effect_intent_established"),
        (15, "0" * 64),
    ),
)
def test_receipt_family_result_and_projection_digest_counterfactuals(
    index: int,
    replacement: object,
) -> None:
    row=list(_receipt(0));row[index]=replacement
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.development_mutation_receipt_row_value_from_row_tuple(tuple(row))


def test_supplied_entry_graph_digest_is_ordered_and_rejects_only_common_duplicates() -> None:
    placeholder=rows.development_mutation_receipt_row_value_from_row_tuple(_receipt(0))
    first=rows.development_mutation_graph_entry(role="program",ordinal=0,record_ref="record-1",record_digest="1"*64)
    second=rows.development_mutation_graph_entry(role="decision",ordinal=0,record_ref="record-1",record_digest="2"*64)
    digest=rows.compute_development_mutation_graph_digest(receipt=placeholder,graph_entries=(first,second))
    graph_identity={
        "schema_id":"governed-execution.nwp-development-mutation-receipt.v1",
        "mutation_ref":"mutation-1","mutation_family":"initialize_development_program",
        "command_schema_id":"governed-execution.nwp-initialize-development-program-command.v1",
        "command_digest":SHA,"program_ref":"program-1","decision_ref":"decision-1",
        "result_program_version_ref":"version-1","result_semantic_attempt_ref":None,
        "result_effect_intent_ref":None,"result_effect_fence_ref":None,
        "result_delivery_attempt_ref":None,"result_observation_ref":None,
        "result_decision_ref":"decision-1","result_class":"development_program_initialized",
        "result_projection_digest":placeholder.result_projection_digest,
        "outcome":"committed","committed_at":NOW,
        "graph_entries":(
            {"role":"program","ordinal":0,"record_ref":"record-1","record_digest":"1"*64},
            {"role":"decision","ordinal":0,"record_ref":"record-1","record_digest":"2"*64},
        ),
    }
    assert tuple(graph_identity["graph_entries"][0]) == GRAPH_ENTRY_KEYS
    assert digest == _digest(GRAPH_DOMAIN,graph_identity)
    assert digest!=rows.compute_development_mutation_graph_digest(receipt=placeholder,graph_entries=(second,first))
    receipt=rows.development_mutation_receipt_row_value_from_row_tuple(_receipt(0,digest))
    assert rows.require_development_mutation_graph_digest_matches_supplied_entries(receipt=receipt,graph_entries=(first,second)) is None
    empty_digest=rows.compute_development_mutation_graph_digest(receipt=placeholder,graph_entries=())
    assert len(empty_digest)==64
    duplicate_ordinal=rows.development_mutation_graph_entry(role="program",ordinal=0,record_ref="record-2",record_digest="3"*64)
    duplicate_ref=rows.development_mutation_graph_entry(role="program",ordinal=1,record_ref="record-1",record_digest="3"*64)
    for entries in ((first,duplicate_ordinal),(first,duplicate_ref)):
        with pytest.raises(SQLiteMutationStoreError):
            rows.compute_development_mutation_graph_digest(receipt=placeholder,graph_entries=entries)


def test_receipt_never_defaults_to_an_empty_graph() -> None:
    receipt=rows.development_mutation_receipt_row_value_from_row_tuple(_receipt(0))
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.require_development_mutation_graph_digest_matches_supplied_entries(receipt=receipt,graph_entries=())
