from __future__ import annotations

import hashlib
import json

import pytest

from ge_nwp_coordinator import _development_effect_row_values as rows
from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1,
    DeliveryEnvelopeV1,
    EffectFenceV1,
    WorkerCommandV1,
)
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError


NOW = "2026-08-15T12:34:56Z"
EXPIRES = "2026-08-16T12:34:56Z"
OID = "a" * 40
SHA = "b" * 64
PATHS = [
    ".docs/system_overview/hybrid_integration_architecture_adr.md",
    "PLANS.md",
    "docs_contract_test.go",
]
PATHS_JSON = '[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"]'
CEILINGS = {
    "max_active_invocations": 1,
    "max_candidate_bytes": 2,
    "max_changed_files": 3,
    "max_cost_microusd": 4,
    "max_cpu_seconds": 5,
    "max_deliveries": 6,
    "max_deployments": 0,
    "max_local_commits": 0,
    "max_memory_bytes": 9,
    "max_merges": 0,
    "max_model_input_tokens": 11,
    "max_model_output_tokens": 12,
    "max_pull_requests": 0,
    "max_pushes": 0,
    "max_wall_seconds": 15,
}

EFFECT_SCHEMA_DOMAIN_LEDGER = (
    ("_ATTEMPT_FENCE_SCHEMA", "governed-execution.nwp-attempt-fence.v1", "_ATTEMPT_FENCE_DOMAIN", "governed-execution.nwp-attempt-fence.v1.identity"),
    ("_AUTHORITY_EVALUATION_SCHEMA", "governed-execution.nwp-development-authority-evaluation.v1", "_AUTHORITY_EVALUATION_DOMAIN", "governed-execution.nwp-development-authority-evaluation.v1.identity"),
    ("_EFFECT_INTENT_SCHEMA", "governed-execution.nwp-development-effect-intent.v1", "_EFFECT_INTENT_DOMAIN", "governed-execution.nwp-development-effect-intent.v1.identity"),
    ("_EFFECT_FENCE_SCHEMA", "governed-execution.nwp-effect-fence.v1", "_EFFECT_FENCE_DOMAIN", "governed-execution.nwp-effect-fence.v1.identity"),
    ("_AUTHOR_COMMAND_SCHEMA", "governed-execution.nwp-worker-command.v1", "_AUTHOR_COMMAND_DOMAIN", "governed-execution.nwp-worker-command.v1.identity"),
    ("_EFFECT_HEAD_SCHEMA", "governed-execution.nwp-development-effect-head.v1", "_EFFECT_HEAD_DOMAIN", "governed-execution.nwp-development-effect-head.v1.identity"),
    ("_DELIVERY_ENVELOPE_SCHEMA", "governed-execution.nwp-delivery-envelope.v1", "_DELIVERY_ATTEMPT_DOMAIN", "governed-execution.nwp-development-delivery-attempt.v1.identity"),
    ("_DELIVERY_HEAD_SCHEMA", "governed-execution.nwp-development-delivery-head.v1", "_DELIVERY_HEAD_DOMAIN", "governed-execution.nwp-development-delivery-head.v1.identity"),
)

EFFECT_VOCABULARIES = {
    "_EVALUATION_SCOPES": ("attempt", "effect"),
    "_AUTHORITY_STATES": ("pending", "verified", "blocked", "stale", "revoked", "expired"),
    "_EFFECT_CLASSES": ("author_candidate", "cancel_effect", "local_git_commit", "review_candidate", "validate_candidate"),
    "_EFFECT_STATES": ("ready_for_delivery", "delivery_pending", "delivery_outcome_unknown", "observed", "cancellation_effect_established", "terminal"),
    "_DELIVERY_KINDS": ("initial", "redelivery"),
    "_DELIVERY_STATES": ("planned", "submitted", "outcome_unknown", "acknowledged", "rejected", "completed"),
}


def _digest(domain: str, identity: dict[str, object]) -> str:
    canonical = json.dumps(
        identity,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8", errors="strict")
    return hashlib.sha256(domain.encode("utf-8") + b"\0" + canonical).hexdigest()


EXPECTED_COLUMNS = {
    "_DEVELOPMENT_ATTEMPT_FENCE_COLUMNS": (
        "schema_id","attempt_fence_ref","parent_standing_grant_ref","parent_standing_grant_digest","attempt_authorization_ref","attempt_authorization_digest","program_ref","program_version_ref","accepted_intent_revision_ref","work_item_ref","work_item_revision_ref","semantic_attempt_ref","repository_ref","base_git_object_format","base_git_oid","path_ceiling_json","allowed_effect_class_mask","aggregate_max_active_invocations","aggregate_max_candidate_bytes","aggregate_max_changed_files","aggregate_max_cost_microusd","aggregate_max_cpu_seconds","aggregate_max_deliveries","aggregate_max_deployments","aggregate_max_local_commits","aggregate_max_memory_bytes","aggregate_max_merges","aggregate_max_model_input_tokens","aggregate_max_model_output_tokens","aggregate_max_pull_requests","aggregate_max_pushes","aggregate_max_wall_seconds","expires_at","global_stop_ref","global_stop_version","attempt_fence_digest","recorded_at",
    ),
    "_DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS": (
        "schema_id","authority_evaluation_ref","program_ref","evaluation_scope","evaluation_subject_ref","semantic_attempt_ref","effect_intent_ref","authority_ref","authority_digest","authority_state","reason_code","expires_at","evaluated_at","authority_evaluation_digest",
    ),
    "_DEVELOPMENT_EFFECT_INTENT_COLUMNS": (
        "schema_id","effect_intent_ref","program_ref","program_version_ref","semantic_attempt_ref","effect_class","candidate_ref","command_ref","basis_decision_ref","cancellation_target_effect_intent_ref","expected_target_effect_head_revision","portable_capsule_digest","created_at","effect_intent_digest",
    ),
    "_DEVELOPMENT_EFFECT_FENCE_COLUMNS": (
        "schema_id","effect_fence_ref","parent_standing_grant_ref","parent_standing_grant_digest","effect_authorization_ref","effect_authorization_digest","attempt_fence_ref","attempt_fence_digest","program_ref","program_version_ref","accepted_intent_revision_ref","work_item_ref","work_item_revision_ref","semantic_attempt_ref","effect_intent_ref","effect_class","command_ref","command_digest","candidate_ref","repository_ref","base_git_object_format","base_git_oid","path_ceiling_json","effect_max_active_invocations","effect_max_candidate_bytes","effect_max_changed_files","effect_max_cost_microusd","effect_max_cpu_seconds","effect_max_deliveries","effect_max_deployments","effect_max_local_commits","effect_max_memory_bytes","effect_max_merges","effect_max_model_input_tokens","effect_max_model_output_tokens","effect_max_pull_requests","effect_max_pushes","effect_max_wall_seconds","expires_at","global_stop_ref","global_stop_version","portable_capsule_digest","cancellation_target_effect_intent_ref","cancellation_target_effect_fence_ref","cancellation_target_effect_fence_digest","effect_fence_digest","recorded_at",
    ),
    "_DEVELOPMENT_AUTHOR_COMMAND_COLUMNS": (
        "schema_id","command_ref","program_ref","program_version_ref","accepted_intent_revision_ref","work_item_ref","work_item_revision_ref","semantic_attempt_ref","effect_intent_ref","effect_class","candidate_ref","repository_ref","base_git_object_format","base_git_oid","path_ceiling_json","work_spec_ref","work_spec_digest","standing_grant_ref","standing_grant_digest","attempt_authorization_ref","attempt_authorization_digest","effect_authorization_ref","effect_authorization_digest","attempt_fence_ref","attempt_fence_digest","effect_fence_ref","effect_fence_digest","global_stop_ref","global_stop_version","validation_requirement_ref","validation_requirement_digest","review_requirement_ref","review_requirement_digest","capsule_schema_id","capsule_profile_ref","effect_max_active_invocations","effect_max_candidate_bytes","effect_max_changed_files","effect_max_cost_microusd","effect_max_cpu_seconds","effect_max_deliveries","effect_max_deployments","effect_max_local_commits","effect_max_memory_bytes","effect_max_merges","effect_max_model_input_tokens","effect_max_model_output_tokens","effect_max_pull_requests","effect_max_pushes","effect_max_wall_seconds","privacy_classification","redaction_profile_ref","command_digest","recorded_at",
    ),
    "_DEVELOPMENT_EFFECT_HEAD_COLUMNS": (
        "schema_id","effect_intent_ref","program_ref","current_effect_fence_ref","head_revision","effect_state","cancellation_effect_intent_ref","updated_at","head_digest",
    ),
    "_DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS": (
        "schema_id","delivery_attempt_ref","program_ref","program_version_ref","command_ref","command_digest","semantic_attempt_ref","effect_intent_ref","attempt_fence_ref","attempt_fence_digest","effect_fence_ref","effect_fence_digest","adapter_kind","adapter_safe_correlation_ref","delivery_envelope_digest","delivery_kind","delivery_number","predecessor_delivery_attempt_ref","basis_decision_ref","recorded_at","delivery_attempt_digest",
    ),
    "_DEVELOPMENT_DELIVERY_HEAD_COLUMNS": (
        "schema_id","effect_intent_ref","program_ref","current_delivery_attempt_ref","head_revision","delivery_state","updated_at","head_digest",
    ),
}


def test_effect_owner_column_tuples_are_independent_literals() -> None:
    assert {name: getattr(rows, name) for name in EXPECTED_COLUMNS} == EXPECTED_COLUMNS
    assert sum(len(columns) for columns in EXPECTED_COLUMNS.values()) == 204


def test_effect_schema_domain_and_vocabulary_ledgers_are_independent_literals() -> None:
    for schema_name, schema, domain_name, domain in EFFECT_SCHEMA_DOMAIN_LEDGER:
        assert getattr(rows, schema_name) == schema
        assert getattr(rows, domain_name) == domain
    assert rows._DELIVERY_ATTEMPT_WRAPPER_SCHEMA == "governed-execution.nwp-development-delivery-attempt.v1"
    assert {name: getattr(rows, name) for name in EFFECT_VOCABULARIES} == EFFECT_VOCABULARIES


def _attempt_fence_row(recorded_at: str = NOW) -> tuple[object, ...]:
    identity = {
        "schema_id":"governed-execution.nwp-attempt-fence.v1",
        "attempt_fence_ref":"attempt-fence-1","parent_standing_grant_ref":"grant-1",
        "parent_standing_grant_digest":"1"*64,"attempt_authorization_ref":"attempt-auth-1",
        "attempt_authorization_digest":"2"*64,"program_ref":"program-1",
        "program_version_ref":"version-1","accepted_intent_revision_ref":"intent-1",
        "work_item_ref":"work-1","work_item_revision_ref":"work-revision-1",
        "semantic_attempt_ref":"attempt-1","repository_ref":"repository-1",
        "base_git_object_format":"sha1","base_git_oid":OID,"path_ceiling":PATHS,
        "allowed_effect_classes":["author_candidate","cancel_effect","local_git_commit","review_candidate","validate_candidate"],
        "aggregate_ceilings":CEILINGS,"expires_at":EXPIRES,"global_stop_ref":"stop-1",
        "global_stop_version":0,
    }
    digest = _digest("governed-execution.nwp-attempt-fence.v1.identity", identity)
    physical = {key:value for key,value in identity.items() if key not in ("path_ceiling","allowed_effect_classes","aggregate_ceilings")}
    physical["path_ceiling_json"] = PATHS_JSON
    physical["allowed_effect_class_mask"] = 31
    for name, value in CEILINGS.items(): physical["aggregate_" + name] = value
    physical["attempt_fence_digest"] = digest
    physical["recorded_at"] = recorded_at
    return tuple(physical[column] for column in EXPECTED_COLUMNS["_DEVELOPMENT_ATTEMPT_FENCE_COLUMNS"])


def _effect_fence_row(recorded_at: str = NOW) -> tuple[object, ...]:
    identity = {
        "schema_id":"governed-execution.nwp-effect-fence.v1","effect_fence_ref":"effect-fence-1",
        "parent_standing_grant_ref":"grant-1","parent_standing_grant_digest":"1"*64,
        "effect_authorization_ref":"effect-auth-1","effect_authorization_digest":"3"*64,
        "attempt_fence_ref":"attempt-fence-1","attempt_fence_digest":"4"*64,
        "program_ref":"program-1","program_version_ref":"version-1",
        "accepted_intent_revision_ref":"intent-1","work_item_ref":"work-1",
        "work_item_revision_ref":"work-revision-1","semantic_attempt_ref":"attempt-1",
        "effect_intent_ref":"effect-1","effect_class":"author_candidate",
        "command_ref":"command-1","command_digest":"5"*64,"candidate_ref":"candidate-1",
        "repository_ref":"repository-1","base_git_object_format":"sha1","base_git_oid":OID,
        "path_ceiling":PATHS,"effect_ceilings":CEILINGS,"expires_at":EXPIRES,
        "global_stop_ref":"stop-1","global_stop_version":0,"portable_capsule_digest":None,
        "cancellation_target_effect_intent_ref":None,"cancellation_target_effect_fence_ref":None,
        "cancellation_target_effect_fence_digest":None,
    }
    digest=_digest("governed-execution.nwp-effect-fence.v1.identity",identity)
    physical={key:value for key,value in identity.items() if key not in ("path_ceiling","effect_ceilings")}
    physical["path_ceiling_json"]=PATHS_JSON
    for name,value in CEILINGS.items():physical["effect_"+name]=value
    physical["effect_fence_digest"]=digest;physical["recorded_at"]=recorded_at
    return tuple(physical[column] for column in EXPECTED_COLUMNS["_DEVELOPMENT_EFFECT_FENCE_COLUMNS"])


def _command_row(recorded_at: str = NOW) -> tuple[object, ...]:
    identity={
        "schema_id":"governed-execution.nwp-worker-command.v1","command_ref":"command-1",
        "program_ref":"program-1","program_version_ref":"version-1",
        "accepted_intent_revision_ref":"intent-1","work_item_ref":"work-1",
        "work_item_revision_ref":"work-revision-1","semantic_attempt_ref":"attempt-1",
        "effect_intent_ref":"effect-1","effect_class":"author_candidate","candidate_ref":"candidate-1",
        "repository_ref":"repository-1","base_git_object_format":"sha1","base_git_oid":OID,
        "path_ceiling":PATHS,"work_spec_ref":"work-spec-1","work_spec_digest":"6"*64,
        "standing_grant_ref":"grant-1","standing_grant_digest":"1"*64,
        "attempt_authorization_ref":"attempt-auth-1","attempt_authorization_digest":"2"*64,
        "effect_authorization_ref":"effect-auth-1","effect_authorization_digest":"3"*64,
        "attempt_fence_ref":"attempt-fence-1","attempt_fence_digest":"4"*64,
        "effect_fence_ref":"effect-fence-1","global_stop_ref":"stop-1","global_stop_version":0,
        "validation_requirement_ref":"validation-1","validation_requirement_digest":"7"*64,
        "review_requirement_ref":"review-1","review_requirement_digest":"8"*64,
        "capsule_schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1",
        "capsule_profile_ref":"capsule-profile-1","effect_ceilings":CEILINGS,
        "privacy_classification":"private_source_change","redaction_profile_ref":"redaction-1",
    }
    digest=_digest("governed-execution.nwp-worker-command.v1.identity",identity)
    physical={key:value for key,value in identity.items() if key not in ("path_ceiling","effect_ceilings")}
    physical["path_ceiling_json"]=PATHS_JSON;physical["effect_fence_digest"]="9"*64
    for name,value in CEILINGS.items():physical["effect_"+name]=value
    physical["command_digest"]=digest;physical["recorded_at"]=recorded_at
    return tuple(physical[column] for column in EXPECTED_COLUMNS["_DEVELOPMENT_AUTHOR_COMMAND_COLUMNS"])


def _delivery_row(recorded_at: str = NOW) -> tuple[object, ...]:
    envelope_identity={
        "schema_id":"governed-execution.nwp-delivery-envelope.v1",
        "delivery_attempt_ref":"delivery-1","program_ref":"program-1",
        "program_version_ref":"version-1","command_ref":"command-1",
        "command_digest":"a"*64,"semantic_attempt_ref":"attempt-1",
        "effect_intent_ref":"effect-1","attempt_fence_ref":"attempt-fence-1",
        "attempt_fence_digest":"4"*64,"effect_fence_ref":"effect-fence-1",
        "effect_fence_digest":"9"*64,"adapter_kind":"direct_local_bootstrap",
        "adapter_safe_correlation_ref":"correlation-1",
    }
    envelope_digest=_digest("governed-execution.nwp-delivery-envelope.v1.identity",envelope_identity)
    wrapper_identity={
        "schema_id":"governed-execution.nwp-development-delivery-attempt.v1",
        "delivery_envelope_digest":envelope_digest,"delivery_kind":"initial",
        "delivery_number":1,"predecessor_delivery_attempt_ref":None,
        "basis_decision_ref":"decision-1","recorded_at":recorded_at,
    }
    physical=dict(envelope_identity);physical["delivery_envelope_digest"]=envelope_digest
    physical.update({"delivery_kind":"initial","delivery_number":1,
        "predecessor_delivery_attempt_ref":None,"basis_decision_ref":"decision-1",
        "recorded_at":recorded_at,"delivery_attempt_digest":_digest(
            "governed-execution.nwp-development-delivery-attempt.v1.identity",wrapper_identity)})
    return tuple(physical[column] for column in EXPECTED_COLUMNS["_DEVELOPMENT_DELIVERY_ATTEMPT_COLUMNS"])


def test_four_c2a_rows_reconstruct_nested_values_and_timestamp_boundaries() -> None:
    attempt=rows.development_attempt_fence_row_value_from_row_tuple(_attempt_fence_row())
    effect=rows.development_effect_fence_row_value_from_row_tuple(_effect_fence_row())
    command=rows.development_author_command_row_value_from_row_tuple(_command_row())
    delivery=rows.development_delivery_attempt_row_value_from_row_tuple(_delivery_row())
    assert type(attempt.attempt_fence) is AttemptFenceV1
    assert type(effect.effect_fence) is EffectFenceV1
    assert type(command.author_command) is WorkerCommandV1
    assert type(delivery.delivery_envelope) is DeliveryEnvelopeV1
    assert attempt.computed_digest()==attempt.attempt_fence_digest
    assert effect.computed_digest()==effect.effect_fence_digest
    assert command.computed_digest()==command.command_digest
    assert delivery.computed_digest()==delivery.delivery_attempt_digest
    assert delivery.schema_id=="governed-execution.nwp-delivery-envelope.v1"
    assert delivery.wrapper_schema_id=="governed-execution.nwp-development-delivery-attempt.v1"
    assert attempt != rows.development_attempt_fence_row_value_from_row_tuple(_attempt_fence_row("2026-08-15T12:35:56Z"))
    assert attempt.computed_digest()==rows.development_attempt_fence_row_value_from_row_tuple(_attempt_fence_row("2026-08-15T12:35:56Z")).computed_digest()


@pytest.mark.parametrize(
    ("columns_name","factory","domain","digest_name","identity"),
    (
        ("_DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS",rows.development_authority_evaluation_row_value_from_row_tuple,"governed-execution.nwp-development-authority-evaluation.v1.identity","authority_evaluation_digest",{"schema_id":"governed-execution.nwp-development-authority-evaluation.v1","authority_evaluation_ref":"evaluation-1","program_ref":"program-1","evaluation_scope":"attempt","evaluation_subject_ref":"attempt-1","semantic_attempt_ref":"attempt-1","effect_intent_ref":None,"authority_ref":"authority-1","authority_digest":SHA,"authority_state":"verified","reason_code":"authority.verified","expires_at":EXPIRES,"evaluated_at":NOW}),
        ("_DEVELOPMENT_EFFECT_INTENT_COLUMNS",rows.development_effect_intent_row_value_from_row_tuple,"governed-execution.nwp-development-effect-intent.v1.identity","effect_intent_digest",{"schema_id":"governed-execution.nwp-development-effect-intent.v1","effect_intent_ref":"effect-1","program_ref":"program-1","program_version_ref":"version-1","semantic_attempt_ref":"attempt-1","effect_class":"author_candidate","candidate_ref":"candidate-1","command_ref":"command-1","basis_decision_ref":"decision-1","cancellation_target_effect_intent_ref":None,"expected_target_effect_head_revision":None,"portable_capsule_digest":None,"created_at":NOW}),
        ("_DEVELOPMENT_EFFECT_HEAD_COLUMNS",rows.development_effect_head_row_value_from_row_tuple,"governed-execution.nwp-development-effect-head.v1.identity","head_digest",{"schema_id":"governed-execution.nwp-development-effect-head.v1","effect_intent_ref":"effect-1","program_ref":"program-1","current_effect_fence_ref":"effect-fence-1","head_revision":0,"effect_state":"ready_for_delivery","cancellation_effect_intent_ref":None,"updated_at":NOW}),
        ("_DEVELOPMENT_DELIVERY_HEAD_COLUMNS",rows.development_delivery_head_row_value_from_row_tuple,"governed-execution.nwp-development-delivery-head.v1.identity","head_digest",{"schema_id":"governed-execution.nwp-development-delivery-head.v1","effect_intent_ref":"effect-1","program_ref":"program-1","current_delivery_attempt_ref":"delivery-1","head_revision":0,"delivery_state":"planned","updated_at":NOW}),
    ),
)
def test_four_c2b_effect_rows_verify_literal_vectors(columns_name: str,factory: object,domain: str,digest_name: str,identity: dict[str,object])->None:
    physical=dict(identity);physical[digest_name]=_digest(domain,identity)
    value=factory(tuple(physical[column] for column in EXPECTED_COLUMNS[columns_name]))
    assert value.identity_mapping()==identity
    assert value.computed_digest()==physical[digest_name]


def test_nested_and_outer_delivery_digest_corruption_are_independently_rejected() -> None:
    row=list(_delivery_row())
    row[14]="0"*64
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.development_delivery_attempt_row_value_from_row_tuple(tuple(row))
    row=list(_delivery_row());row[-1]="0"*64
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.development_delivery_attempt_row_value_from_row_tuple(tuple(row))


@pytest.mark.parametrize(
    ("factory", "row_builder", "digest_index"),
    (
        (rows.development_attempt_fence_row_value_from_row_tuple, _attempt_fence_row, 35),
        (rows.development_effect_fence_row_value_from_row_tuple, _effect_fence_row, 45),
        (rows.development_author_command_row_value_from_row_tuple, _command_row, 52),
    ),
)
def test_each_embedded_c2a_self_digest_is_verified(
    factory: object,
    row_builder: object,
    digest_index: int,
) -> None:
    row=list(row_builder());row[digest_index]="0"*64
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        factory(tuple(row))


@pytest.mark.parametrize(
    ("factory", "row_builder"),
    (
        (rows.development_attempt_fence_row_value_from_row_tuple, _attempt_fence_row),
        (rows.development_effect_fence_row_value_from_row_tuple, _effect_fence_row),
        (rows.development_author_command_row_value_from_row_tuple, _command_row),
    ),
)
def test_three_c2a_outer_recorded_timestamps_are_equality_only(
    factory: object,
    row_builder: object,
) -> None:
    first=factory(row_builder(NOW))
    second=factory(row_builder("2026-08-15T12:35:56Z"))
    assert first != second
    assert first.computed_digest() == second.computed_digest()


def test_authority_evaluation_is_evidence_only_and_enforces_expiry_algebra() -> None:
    identity={"schema_id":"governed-execution.nwp-development-authority-evaluation.v1","authority_evaluation_ref":"evaluation-1","program_ref":"program-1","evaluation_scope":"attempt","evaluation_subject_ref":"attempt-1","semantic_attempt_ref":"attempt-1","effect_intent_ref":None,"authority_ref":"authority-1","authority_digest":SHA,"authority_state":"pending","reason_code":"authority.pending","expires_at":None,"evaluated_at":NOW}
    physical=dict(identity);physical["authority_evaluation_digest"]=_digest("governed-execution.nwp-development-authority-evaluation.v1.identity",identity)
    value=rows.development_authority_evaluation_row_value_from_row_tuple(tuple(physical[column] for column in EXPECTED_COLUMNS["_DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS"]))
    assert value.authority_state=="pending"
    assert not hasattr(value,"authorized")
    bad=dict(physical);bad["expires_at"]=EXPIRES
    with pytest.raises(SQLiteMutationStoreError):
        rows.development_authority_evaluation_row_value_from_row_tuple(tuple(bad[column] for column in EXPECTED_COLUMNS["_DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS"]))

    reverse=dict(identity);reverse.update({"authority_state":"verified","reason_code":"authority.verified","expires_at":None})
    reverse["authority_evaluation_digest"]=_digest("governed-execution.nwp-development-authority-evaluation.v1.identity",{key:value for key,value in reverse.items() if key != "authority_evaluation_digest"})
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.development_authority_evaluation_row_value_from_row_tuple(tuple(reverse[column] for column in EXPECTED_COLUMNS["_DEVELOPMENT_AUTHORITY_EVALUATION_COLUMNS"]))


@pytest.mark.parametrize(
    ("effect_class", "target", "expected_revision"),
    (("author_candidate", "effect-0", 0), ("cancel_effect", None, None)),
)
def test_effect_intent_cancellation_nullability_rejects_both_directions(
    effect_class: str,
    target: object,
    expected_revision: object,
) -> None:
    identity={"schema_id":"governed-execution.nwp-development-effect-intent.v1","effect_intent_ref":"effect-1","program_ref":"program-1","program_version_ref":"version-1","semantic_attempt_ref":"attempt-1","effect_class":effect_class,"candidate_ref":"candidate-1","command_ref":"command-1","basis_decision_ref":"decision-1","cancellation_target_effect_intent_ref":target,"expected_target_effect_head_revision":expected_revision,"portable_capsule_digest":None,"created_at":NOW}
    physical=dict(identity);physical["effect_intent_digest"]=_digest("governed-execution.nwp-development-effect-intent.v1.identity",identity)
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.development_effect_intent_row_value_from_row_tuple(tuple(physical[column] for column in EXPECTED_COLUMNS["_DEVELOPMENT_EFFECT_INTENT_COLUMNS"]))


@pytest.mark.parametrize(
    ("delivery_kind", "delivery_number", "predecessor"),
    (("initial", 1, "delivery-0"), ("redelivery", 2, None)),
)
def test_delivery_lineage_nullability_rejects_both_directions(
    delivery_kind: str,
    delivery_number: int,
    predecessor: object,
) -> None:
    row=list(_delivery_row())
    row[15]=delivery_kind;row[16]=delivery_number;row[17]=predecessor
    wrapper={"schema_id":"governed-execution.nwp-development-delivery-attempt.v1","delivery_envelope_digest":row[14],"delivery_kind":delivery_kind,"delivery_number":delivery_number,"predecessor_delivery_attempt_ref":predecessor,"basis_decision_ref":row[18],"recorded_at":row[19]}
    row[20]=_digest("governed-execution.nwp-development-delivery-attempt.v1.identity",wrapper)
    with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
        rows.development_delivery_attempt_row_value_from_row_tuple(tuple(row))
