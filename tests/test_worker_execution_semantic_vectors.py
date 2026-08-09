from __future__ import annotations

from copy import deepcopy
import hashlib
import json

import pytest

from ge_nwp_coordinator._worker_execution_semantic_values import (
    AttemptFenceV1,
    CandidateCapsuleManifestV1,
    DeliveryEnvelopeV1,
    EffectFenceV1,
    WorkerCommandV1,
    WorkerExecutionValueError,
    WorkerObservationV1,
    WorkSpecV1,
)


WORK_SPEC_BYTES = b'{"accepted_intent_revision_ref":"intent-revision.0001","authorized_paths":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","exclusions":["Do not push, create a pull request, merge, or deploy.","Do not modify Execution Substrate runtime source."],"objective":"Document the bounded direct-local bootstrap proof while preserving Execution Substrate migration gates.","privacy_classification":"private_work_spec","program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","requirements":["Modify only the three authorized repository-relative paths.","Preserve Execution Substrate reliable-submit ownership and current P0.","Produce no runtime, schema, or service change."],"review_requirement_ref":"review.es-docs.0001","schema_id":"governed-execution.nwp-work-spec.v1","validation_requirement_ref":"validation.es-docs.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001","work_spec_ref":"work-spec.es-docs.0001"}'

ATTEMPT_FENCE_BYTES = b'{"accepted_intent_revision_ref":"intent-revision.0001","aggregate_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":10000000,"max_cpu_seconds":3600,"max_deliveries":2,"max_deployments":0,"max_local_commits":1,"max_memory_bytes":4294967296,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":3600},"allowed_effect_classes":["author_candidate","cancel_effect","local_git_commit","review_candidate","validate_candidate"],"attempt_authorization_digest":"2222222222222222222222222222222222222222222222222222222222222222","attempt_authorization_ref":"attempt-authorization.0001","attempt_fence_ref":"attempt-fence.0001","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","expires_at":"2030-01-01T00:00:00Z","global_stop_ref":"global-stop.current","global_stop_version":7,"parent_standing_grant_digest":"1111111111111111111111111111111111111111111111111111111111111111","parent_standing_grant_ref":"standing-grant.0001","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","schema_id":"governed-execution.nwp-attempt-fence.v1","semantic_attempt_ref":"semantic-attempt.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}'

EFFECT_FENCE_BYTES = b'{"accepted_intent_revision_ref":"intent-revision.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","cancellation_target_effect_fence_digest":null,"cancellation_target_effect_fence_ref":null,"cancellation_target_effect_intent_ref":null,"candidate_ref":"candidate.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","effect_authorization_digest":"3333333333333333333333333333333333333333333333333333333333333333","effect_authorization_ref":"effect-authorization.0001","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":10000000,"max_cpu_seconds":3600,"max_deliveries":2,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":4294967296,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":3600},"effect_class":"author_candidate","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","expires_at":"2030-01-01T00:00:00Z","global_stop_ref":"global-stop.current","global_stop_version":7,"parent_standing_grant_digest":"1111111111111111111111111111111111111111111111111111111111111111","parent_standing_grant_ref":"standing-grant.0001","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"portable_capsule_digest":null,"program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","schema_id":"governed-execution.nwp-effect-fence.v1","semantic_attempt_ref":"semantic-attempt.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}'

WORKER_COMMAND_BYTES = b'{"accepted_intent_revision_ref":"intent-revision.0001","attempt_authorization_digest":"2222222222222222222222222222222222222222222222222222222222222222","attempt_authorization_ref":"attempt-authorization.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","candidate_ref":"candidate.0001","capsule_profile_ref":"capsule-profile.regular-replace-v1","capsule_schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1","command_ref":"worker-command.0001","effect_authorization_digest":"3333333333333333333333333333333333333333333333333333333333333333","effect_authorization_ref":"effect-authorization.0001","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":10000000,"max_cpu_seconds":3600,"max_deliveries":2,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":4294967296,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":3600},"effect_class":"author_candidate","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","global_stop_ref":"global-stop.current","global_stop_version":7,"path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"privacy_classification":"private_source_change","program_ref":"program.es-docs","program_version_ref":"program-version.0001","redaction_profile_ref":"redaction.source-private-v1","repository_ref":"repository.execution-substrate","review_requirement_digest":"5555555555555555555555555555555555555555555555555555555555555555","review_requirement_ref":"review.es-docs.0001","schema_id":"governed-execution.nwp-worker-command.v1","semantic_attempt_ref":"semantic-attempt.0001","standing_grant_digest":"1111111111111111111111111111111111111111111111111111111111111111","standing_grant_ref":"standing-grant.0001","validation_requirement_digest":"4444444444444444444444444444444444444444444444444444444444444444","validation_requirement_ref":"validation.es-docs.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001","work_spec_digest":"5ae0add98fb3b6a233b778fe165dfa7ef8d1f3c43e824dddbdb6827958360ade","work_spec_ref":"work-spec.es-docs.0001"}'

DELIVERY_ENVELOPE_BYTES = b'{"adapter_kind":"direct_local_bootstrap","adapter_safe_correlation_ref":"adapter-correlation.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","delivery_attempt_ref":"delivery-attempt.0001","effect_fence_digest":"71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","program_ref":"program.es-docs","program_version_ref":"program-version.0001","schema_id":"governed-execution.nwp-delivery-envelope.v1","semantic_attempt_ref":"semantic-attempt.0001"}'

WORKER_OBSERVATION_BYTES = b'{"accepted_intent_revision_ref":"intent-revision.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","candidate_ref":"candidate.0001","capsule_manifest_ref":"capsule-manifest.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","delivery_attempt_ref":"delivery-attempt.0001","effect_fence_digest":"71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","evidence_refs":["evidence.capsule-seal.0001"],"observation_kind":"capsule_sealed","observation_ref":"observation.capsule-sealed.0001","observed_at":"2026-08-08T18:00:00Z","outcome":"sealed","portable_capsule_digest":"b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c","program_ref":"program.es-docs","program_version_ref":"program-version.0001","reason_code":"reason.none","schema_id":"governed-execution.nwp-worker-observation.v1","semantic_attempt_ref":"semantic-attempt.0001","source_invocation_ref":"source-invocation.capsule-builder.0001","source_kind":"capsule_builder","source_ref":"capsule-builder.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}'

CAPSULE_MANIFEST_BYTES = b'{"accepted_intent_revision_ref":"intent-revision.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","authorized_path_scope_digest":"881d8190e95accffbce9d463a68910703595e5106ce81ba00a8433404b6c8116","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","candidate_ref":"candidate.0001","canonicalization_profile":"canonical-json.sorted-keys.utf8.v1","capsule_manifest_ref":"capsule-manifest.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","digest_domain":"governed-execution.nwp-candidate-capsule-manifest.v1.identity","effect_fence_digest":"71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","entries":[{"after_blob_sha256":"7c1525eca0dfcccb6dcda32fe7f7f58281aa82be220018b1f69f4b529503ea8a","after_byte_length":52,"before_blob_sha256":"1ac70a99e7e54c57641ba8c0cb1e49ae7d0e6e5a7b1acaa0443e5afc1782f73a","before_byte_length":53,"mode":"100644","operation":"replace_regular_file","path":".docs/system_overview/hybrid_integration_architecture_adr.md"},{"after_blob_sha256":"3b80b40624b6a3834873b32839e8e7e73644def7437389a5eaea12abe480f180","after_byte_length":45,"before_blob_sha256":"d0cc82b8b8733e1b4ee2aba05aad19d474ed16e746bcac709b083d5ce2d848d9","before_byte_length":46,"mode":"100644","operation":"replace_regular_file","path":"PLANS.md"},{"after_blob_sha256":"267a3924b2a2ce1260c9d2532bf75db970eda7c76c40042d192e6cdece8202c2","after_byte_length":53,"before_blob_sha256":"47fc7108400e128ad4deade38d14c9c410b3f4dd23d3e022b008ac279d96ef90","before_byte_length":54,"mode":"100644","operation":"replace_regular_file","path":"docs_contract_test.go"}],"program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1","semantic_attempt_ref":"semantic-attempt.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}'


def _canonical(mapping: dict[str, object]) -> bytes:
    return json.dumps(
        mapping,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8", errors="strict")


def _digest(domain: str, payload: bytes) -> str:
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + payload).hexdigest()


def _different(value: object) -> object:
    if value is None:
        return "changed"
    if type(value) is str:
        return f"{value}x"
    if type(value) is int:
        return value + 1
    if type(value) is list:
        changed = deepcopy(value)
        if changed and type(changed[0]) is dict:
            changed[0] = dict(changed[0])
            changed[0][next(iter(changed[0]))] = "changed"
        else:
            changed.append("changed")
        return changed
    if type(value) is dict:
        changed = dict(value)
        first = next(iter(changed))
        changed[first] = _different(changed[first])
        return changed
    raise AssertionError("unexpected literal vector value")


@pytest.mark.parametrize(
    "value_type,canonical_bytes,schema_id,domain,length,digest,excluded",
    (
        (
            WorkSpecV1,
            WORK_SPEC_BYTES,
            "governed-execution.nwp-work-spec.v1",
            "governed-execution.nwp-work-spec.v1.identity",
            1158,
            "5ae0add98fb3b6a233b778fe165dfa7ef8d1f3c43e824dddbdb6827958360ade",
            ("work_spec_digest",),
        ),
        (
            AttemptFenceV1,
            ATTEMPT_FENCE_BYTES,
            "governed-execution.nwp-attempt-fence.v1",
            "governed-execution.nwp-attempt-fence.v1.identity",
            1525,
            "7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e",
            ("attempt_fence_digest",),
        ),
        (
            EffectFenceV1,
            EFFECT_FENCE_BYTES,
            "governed-execution.nwp-effect-fence.v1",
            "governed-execution.nwp-effect-fence.v1.identity",
            1928,
            "71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3",
            ("effect_fence_digest",),
        ),
        (
            WorkerCommandV1,
            WORKER_COMMAND_BYTES,
            "governed-execution.nwp-worker-command.v1",
            "governed-execution.nwp-worker-command.v1.identity",
            2444,
            "6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927",
            ("effect_fence_digest", "command_digest"),
        ),
        (
            DeliveryEnvelopeV1,
            DELIVERY_ENVELOPE_BYTES,
            "governed-execution.nwp-delivery-envelope.v1",
            "governed-execution.nwp-delivery-envelope.v1.identity",
            755,
            "83e68b50759dc21746ef7b521edb8f7b61cf5446d819c8c7aa47bee048841f0e",
            ("delivery_envelope_digest",),
        ),
        (
            WorkerObservationV1,
            WORKER_OBSERVATION_BYTES,
            "governed-execution.nwp-worker-observation.v1",
            "governed-execution.nwp-worker-observation.v1.identity",
            1324,
            "b605b2779fa5b46ebff2d23d7026c643debde509c015e840608b0991f1c52a6f",
            ("observation_digest",),
        ),
        (
            CandidateCapsuleManifestV1,
            CAPSULE_MANIFEST_BYTES,
            "governed-execution.nwp-candidate-capsule-manifest.v1",
            "governed-execution.nwp-candidate-capsule-manifest.v1.identity",
            2178,
            "b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c",
            ("portable_capsule_digest",),
        ),
    ),
)
def test_seven_literal_canonical_vectors_and_every_identity_field_mutation(
    value_type: type[object],
    canonical_bytes: bytes,
    schema_id: str,
    domain: str,
    length: int,
    digest: str,
    excluded: tuple[str, ...],
) -> None:
    identity = json.loads(canonical_bytes.decode("utf-8", errors="strict"))
    assert type(identity) is dict
    record = dict(identity)
    for field in excluded:
        record[field] = digest
    if value_type is WorkerCommandV1:
        record["effect_fence_digest"] = (
            "71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3"
        )
    value = value_type.from_mapping(record)

    assert identity["schema_id"] == schema_id
    assert len(canonical_bytes) == length
    assert value.identity_mapping() == identity
    assert value.canonical_identity_bytes() == canonical_bytes
    assert value.computed_digest() == digest
    assert _digest(domain, canonical_bytes) == digest
    assert not set(excluded) & set(value.identity_mapping())

    for field in identity:
        changed = deepcopy(identity)
        changed[field] = _different(changed[field])
        changed_bytes = _canonical(changed)
        assert changed_bytes != canonical_bytes
        assert _digest(domain, changed_bytes) != digest


def test_worker_command_excludes_both_postcomputed_fields_only() -> None:
    identity = json.loads(WORKER_COMMAND_BYTES.decode("utf-8"))
    first = dict(identity)
    first["effect_fence_digest"] = "1" * 64
    first["command_digest"] = (
        "6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927"
    )
    second = dict(first)
    second["effect_fence_digest"] = "2" * 64
    first_value = WorkerCommandV1.from_mapping(first)
    second_value = WorkerCommandV1.from_mapping(second)
    assert first_value.canonical_identity_bytes() == WORKER_COMMAND_BYTES
    assert second_value.canonical_identity_bytes() == WORKER_COMMAND_BYTES
    assert first_value.command_digest == second_value.command_digest
    assert first_value.effect_fence_digest != second_value.effect_fence_digest


def test_cross_domain_raw_hash_schema_and_stored_digest_mismatches_reject() -> None:
    expected = "5ae0add98fb3b6a233b778fe165dfa7ef8d1f3c43e824dddbdb6827958360ade"
    raw_hash = hashlib.sha256(WORK_SPEC_BYTES).hexdigest()
    cross_domain = _digest(
        "governed-execution.nwp-attempt-fence.v1.identity", WORK_SPEC_BYTES
    )
    assert raw_hash != expected
    assert cross_domain != expected

    identity = json.loads(WORK_SPEC_BYTES.decode("utf-8"))
    wrong_schema = dict(identity)
    wrong_schema["schema_id"] = "governed-execution.nwp-work-spec.v2"
    wrong_schema["work_spec_digest"] = _digest(
        "governed-execution.nwp-work-spec.v1.identity", _canonical(wrong_schema)
    )
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkSpecV1.from_mapping(wrong_schema)
    assert caught.value.field_path == "WorkSpecV1.schema_id"

    wrong_digest = dict(identity)
    wrong_digest["work_spec_digest"] = "0" * 64
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkSpecV1.from_mapping(wrong_digest)
    assert caught.value.reason == "digest_mismatch"


def test_unicode_is_preserved_without_normalization_and_strict_utf8_fails_closed() -> None:
    identity = json.loads(WORK_SPEC_BYTES.decode("utf-8"))
    composed = dict(identity)
    composed["objective"] = "Caf\u00e9"
    composed["work_spec_digest"] = _digest(
        "governed-execution.nwp-work-spec.v1.identity",
        _canonical({key: value for key, value in composed.items() if key != "work_spec_digest"}),
    )
    decomposed = dict(identity)
    decomposed["objective"] = "Cafe\u0301"
    decomposed["work_spec_digest"] = _digest(
        "governed-execution.nwp-work-spec.v1.identity",
        _canonical({key: value for key, value in decomposed.items() if key != "work_spec_digest"}),
    )
    composed_value = WorkSpecV1.from_mapping(composed)
    decomposed_value = WorkSpecV1.from_mapping(decomposed)
    assert composed_value.objective != decomposed_value.objective
    assert composed_value.canonical_identity_bytes() != decomposed_value.canonical_identity_bytes()
    assert composed_value.computed_digest() != decomposed_value.computed_digest()

    surrogate = dict(identity)
    surrogate["objective"] = "private\ud800value"
    surrogate["work_spec_digest"] = "0" * 64
    with pytest.raises(WorkerExecutionValueError) as caught:
        WorkSpecV1.from_mapping(surrogate)
    assert caught.value.reason == "invalid_field_value"
    assert caught.value.field_path == "WorkSpecV1.canonical_identity"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
