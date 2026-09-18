"""Independent canonical vectors for the eight private B1 schemas."""

from __future__ import annotations

import hashlib
import json

import pytest

import ge_nwp_coordinator._rw0_phase_entry_semantic_values as b1


SCHEMAS = (
    (b1.RW0PhaseEntryBasisV1, "governed-execution.nwp-rw0-phase-entry-basis.v1", 26, 174),
    (b1.RW0AuthorityVerificationObservationV1, "governed-execution.nwp-rw0-authority-verification-observation.v1", 39, 124),
    (b1.RW0SubordinateAuthorizationProposalV1, "governed-execution.nwp-rw0-subordinate-authorization-proposal.v1", 29, 92),
    (b1.RW0CustodyAvailabilityObservationV1, "governed-execution.nwp-rw0-custody-availability-observation.v1", 16, 34),
    (b1.RW0RetrievalCapabilityEventObservationV1, "governed-execution.nwp-rw0-retrieval-capability-event-observation.v1", 37, 76),
    (b1.RW0RemoteHostReadinessObservationV1, "governed-execution.nwp-rw0-remote-host-readiness-observation.v1", 39, 80),
    (b1.RW0EffectHostQualificationV1, "governed-execution.nwp-rw0-effect-host-qualification.v1", 45, 92),
    (b1.RW0TerminalOutcomeV1, "governed-execution.nwp-rw0-terminal-outcome-value.v1", 31, 64),
)


# Literal test-owned schema and nested-field inventories.
EXPECTED_FIELDS = {
    b1.RW0PhaseEntryBasisV1: (
        'schema_id',
        'basis_ref',
        'c2b3d_lineage',
        'selection_key',
        'selected_proposal_ref',
        'selected_proposal_digest',
        'selected_artifact_ref',
        'selected_artifact_digest',
        'selected_artifact_binding_digest',
        'selected_plan_safe_projection_digest',
        'disposition_ref',
        'disposition_digest',
        'disposition',
        'selection_head_revision',
        'selection_head_digest',
        'current_effect_head_revision',
        'current_effect_head_state',
        'current_effect_head_digest',
        'current_delivery_head_revision',
        'current_delivery_head_state',
        'current_delivery_head_digest',
        'global_stop_ref',
        'global_stop_version',
        'global_stop_state',
        'path_scope_digest',
        'basis_digest',
    ),
    b1.RW0AuthorityVerificationObservationV1: (
        'schema_id',
        'observation_ref',
        'source_ref',
        'evidence_ref',
        'evidence_digest',
        'phase_basis_ref',
        'phase_basis_digest',
        'parent_grant_ref',
        'parent_grant_digest',
        'grant_family_ref',
        'grant_family_digest',
        'attempt_basis_ref',
        'attempt_basis_digest',
        'effect_basis_ref',
        'effect_basis_digest',
        'attempt_fence_ref',
        'attempt_fence_digest',
        'effect_fence_ref',
        'effect_fence_digest',
        'audience_ref',
        'repository_ref',
        'base_git_object_format',
        'base_git_oid',
        'path_scope_digest',
        'allowed_effect_classes',
        'effect_class',
        'parent_ceilings',
        'status',
        'family_status',
        'revocation_status',
        'grant_expires_at',
        'observed_at',
        'observation_expires_at',
        'current_effect_head_digest',
        'current_delivery_head_digest',
        'global_stop_ref',
        'global_stop_version',
        'global_stop_state',
        'observation_digest',
    ),
    b1.RW0SubordinateAuthorizationProposalV1: (
        'schema_id',
        'proposal_ref',
        'phase_basis_ref',
        'phase_basis_digest',
        'verification_ref',
        'verification_digest',
        'parent_grant_ref',
        'parent_grant_digest',
        'grant_family_ref',
        'grant_family_digest',
        'attempt_basis_ref',
        'attempt_basis_digest',
        'effect_basis_ref',
        'effect_basis_digest',
        'attempt_fence_ref',
        'attempt_fence_digest',
        'effect_fence_ref',
        'effect_fence_digest',
        'audience_ref',
        'repository_ref',
        'base_git_object_format',
        'base_git_oid',
        'path_scope_digest',
        'effect_class',
        'ceilings',
        'expires_at',
        'global_stop_ref',
        'global_stop_version',
        'proposal_digest',
    ),
    b1.RW0CustodyAvailabilityObservationV1: (
        'schema_id',
        'observation_ref',
        'source_ref',
        'evidence_ref',
        'evidence_digest',
        'phase_basis_ref',
        'phase_basis_digest',
        'subject_kind',
        'subject_ref',
        'subject_semantic_digest',
        'content_sha256',
        'byte_length',
        'availability',
        'observed_at',
        'expires_at',
        'observation_digest',
    ),
    b1.RW0RetrievalCapabilityEventObservationV1: (
        'schema_id',
        'event_ref',
        'source_ref',
        'evidence_ref',
        'evidence_digest',
        'phase_basis_ref',
        'phase_basis_digest',
        'safe_correlation_ref',
        'subject_kind',
        'subject_ref',
        'subject_semantic_digest',
        'content_sha256',
        'byte_length',
        'semantic_attempt_ref',
        'attempt_fence_ref',
        'attempt_fence_digest',
        'effect_intent_ref',
        'effect_fence_ref',
        'effect_fence_digest',
        'audience_ref',
        'repository_ref',
        'base_git_object_format',
        'base_git_oid',
        'path_scope_digest',
        'authority_observation_ref',
        'authority_observation_digest',
        'subordinate_proposal_ref',
        'subordinate_proposal_digest',
        'custody_observation_ref',
        'custody_observation_digest',
        'event_kind',
        'predecessor_event_ref',
        'predecessor_event_digest',
        'sequence_number',
        'occurred_at',
        'expires_at',
        'event_digest',
    ),
    b1.RW0RemoteHostReadinessObservationV1: (
        'schema_id',
        'observation_ref',
        'source_ref',
        'evidence_ref',
        'evidence_digest',
        'safe_host_correlation_ref',
        'status',
        'platform',
        'platform_profile_ref',
        'platform_profile_digest',
        'architecture_profile_ref',
        'architecture_profile_digest',
        'worker_artifact_ref',
        'worker_artifact_digest',
        'worker_protocol_ref',
        'worker_protocol_digest',
        'execution_identity_profile_ref',
        'execution_identity_profile_digest',
        'process_profile_ref',
        'process_profile_digest',
        'isolation_profile_ref',
        'isolation_profile_digest',
        'resource_profile_ref',
        'resource_profile_digest',
        'cancellation_profile_ref',
        'cancellation_profile_digest',
        'credential_handoff_profile_ref',
        'credential_handoff_profile_digest',
        'capsule_store_profile_ref',
        'capsule_store_profile_digest',
        'validation_tool_profile_ref',
        'validation_tool_profile_digest',
        'review_tool_profile_ref',
        'review_tool_profile_digest',
        'cleanup_profile_ref',
        'cleanup_profile_digest',
        'observed_at',
        'expires_at',
        'observation_digest',
    ),
    b1.RW0EffectHostQualificationV1: (
        'schema_id',
        'qualification_ref',
        'phase_basis_ref',
        'phase_basis_digest',
        'effect_intent_ref',
        'effect_fence_ref',
        'effect_fence_digest',
        'verification_ref',
        'verification_digest',
        'readiness_ref',
        'readiness_digest',
        'required_scenario_profile_ref',
        'required_scenario_profile_digest',
        'required_platform_profile_ref',
        'required_platform_profile_digest',
        'required_architecture_profile_ref',
        'required_architecture_profile_digest',
        'required_worker_artifact_ref',
        'required_worker_artifact_digest',
        'required_worker_protocol_ref',
        'required_worker_protocol_digest',
        'required_execution_identity_profile_ref',
        'required_execution_identity_profile_digest',
        'required_process_profile_ref',
        'required_process_profile_digest',
        'required_isolation_profile_ref',
        'required_isolation_profile_digest',
        'required_resource_profile_ref',
        'required_resource_profile_digest',
        'required_cancellation_profile_ref',
        'required_cancellation_profile_digest',
        'required_credential_handoff_profile_ref',
        'required_credential_handoff_profile_digest',
        'required_capsule_store_profile_ref',
        'required_capsule_store_profile_digest',
        'required_validation_tool_profile_ref',
        'required_validation_tool_profile_digest',
        'required_review_tool_profile_ref',
        'required_review_tool_profile_digest',
        'required_cleanup_profile_ref',
        'required_cleanup_profile_digest',
        'result',
        'reason',
        'evaluated_at',
        'qualification_digest',
    ),
    b1.RW0TerminalOutcomeV1: (
        'schema_id',
        'outcome_value_ref',
        'phase_basis_ref',
        'phase_basis_digest',
        'branch',
        'outcome',
        'decision_ref',
        'decision_digest',
        'decision_kind',
        'program_head_revision',
        'program_head_digest',
        'work_item_head_revision',
        'work_item_head_digest',
        'selection_head_revision',
        'selection_head_digest',
        'effect_head_revision',
        'effect_head_digest',
        'delivery_head_revision',
        'delivery_head_digest',
        'global_stop_ref',
        'global_stop_version',
        'global_stop_state',
        'evidence_set_ref',
        'evidence_set_digest',
        'latch_postimage_ref',
        'latch_postimage_digest',
        'reconciliation_ref',
        'reconciliation_digest',
        'mismatch_ref',
        'mismatch_digest',
        'outcome_value_digest',
    ),
}

L34_FIELDS = (
    'program_ref',
    'program_version_ref',
    'program_version_number',
    'accepted_intent_revision_ref',
    'work_item_ref',
    'work_item_revision_ref',
    'semantic_attempt_ref',
    'semantic_attempt_digest',
    'attempt_number',
    'candidate_ref',
    'basis_decision_ref',
    'basis_decision_digest',
    'work_spec_ref',
    'work_spec_digest',
    'work_spec_safe_projection_digest',
    'effect_intent_ref',
    'effect_intent_digest',
    'author_command_ref',
    'author_command_digest',
    'standing_grant_ref',
    'standing_grant_digest',
    'attempt_authorization_ref',
    'attempt_authorization_digest',
    'effect_authorization_ref',
    'effect_authorization_digest',
    'attempt_fence_ref',
    'attempt_fence_digest',
    'effect_fence_ref',
    'effect_fence_digest',
    'delivery_attempt_ref',
    'delivery_envelope_digest',
    'delivery_attempt_digest',
    'authority_evaluation_ref',
    'authority_evaluation_digest',
)

K8_FIELDS = (
    'program_ref',
    'semantic_attempt_ref',
    'candidate_ref',
    'effect_intent_ref',
    'author_command_ref',
    'attempt_fence_ref',
    'effect_fence_ref',
    'delivery_attempt_ref',
)

CEILING_FIELDS = (
    'max_active_invocations',
    'max_candidate_bytes',
    'max_changed_files',
    'max_cost_microusd',
    'max_cpu_seconds',
    'max_deliveries',
    'max_deployments',
    'max_local_commits',
    'max_memory_bytes',
    'max_merges',
    'max_model_input_tokens',
    'max_model_output_tokens',
    'max_pull_requests',
    'max_pushes',
    'max_wall_seconds',
)



def _digest(domain: str, identity: dict[str, object]) -> str:
    encoded = json.dumps(identity, ensure_ascii=False, allow_nan=False,
                         sort_keys=True, separators=(",", ":")).encode("utf-8", "strict")
    return hashlib.sha256(domain.encode() + b"\x00" + encoded).hexdigest()


def _h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def _ref(name: str) -> str:
    return "ref-" + name.replace("_", "-")


def _lineage() -> dict[str, object]:
    result: dict[str, object] = {}
    for name in L34_FIELDS:
        if name in ("program_version_number", "attempt_number"):
            result[name] = 1
        elif name.endswith("_digest"):
            result[name] = _h("lineage-" + name)
        else:
            result[name] = _ref("lineage-" + name)
    return result


def mapping_for(cls: type, **changes: object) -> dict[str, object]:
    result: dict[str, object] = {}
    fields = EXPECTED_FIELDS[cls]
    schema = next(item[1] for item in SCHEMAS if item[0] is cls)
    for name in fields:
        if name == "schema_id":
            value: object = schema
        elif name == "c2b3d_lineage":
            value = _lineage()
        elif name == "selection_key":
            lineage = result["c2b3d_lineage"]
            value = [[field, lineage[field]] for field in K8_FIELDS]
        elif name in ("parent_ceilings", "ceilings"):
            value = {field: 1 for field in CEILING_FIELDS}
        elif name == "allowed_effect_classes":
            value = ["author_candidate"]
        elif name in ("predecessor_event_ref", "predecessor_event_digest",
                      "latch_postimage_ref", "latch_postimage_digest",
                      "reconciliation_ref", "reconciliation_digest",
                      "mismatch_ref", "mismatch_digest"):
            value = None
        elif name == "base_git_object_format":
            value = "sha1"
        elif name == "base_git_oid":
            value = "a" * 40
        elif name == "disposition":
            value = "selected_for_dispatch_gates"
        elif name == "current_effect_head_state":
            value = "ready_for_delivery"
        elif name == "current_delivery_head_state":
            value = "planned"
        elif name == "global_stop_state":
            value = "clear"
        elif name == "subject_kind":
            value = "work_spec"
        elif name == "availability":
            value = "available"
        elif name == "event_kind":
            value = "issued"
        elif name == "platform":
            value = "linux"
        elif name == "status":
            value = "verified" if cls is b1.RW0AuthorityVerificationObservationV1 else "ready"
        elif name == "family_status":
            value = "compatible"
        elif name == "revocation_status":
            value = "unrevoked"
        elif name == "effect_class":
            value = "author_candidate"
        elif name == "result" or name == "reason":
            value = "qualified"
        elif name == "branch":
            value = "normal"
        elif name == "outcome" or name == "decision_kind":
            value = "block"
        elif name == "byte_length":
            value = 1
        elif name == "sequence_number":
            value = 0
        elif name.endswith("_revision") or name.endswith("_version"):
            value = 0
        elif name.endswith("_at"):
            value = "2030-01-01T00:00:00Z" if name in ("observed_at", "occurred_at") else "2031-01-01T00:00:00Z"
        elif name.endswith("_digest") or name == "content_sha256":
            value = _h(name)
        elif name.endswith("_ref"):
            value = _ref(name)
        else:
            raise AssertionError(name)
        result[name] = value
    result.update(changes)
    result[fields[-1]] = _digest(schema + ".identity",
                                {k: v for k, v in result.items() if k != fields[-1]})
    return result


@pytest.mark.parametrize("cls,schema,count,limit", SCHEMAS)
def test_independent_canonical_vector(cls: type, schema: str, count: int, limit: int) -> None:
    payload = mapping_for(cls)
    value = cls.from_mapping(payload)
    fields = EXPECTED_FIELDS[cls]
    identity = {k: v for k, v in payload.items() if k != fields[-1]}
    expected_bytes = json.dumps(identity, ensure_ascii=False, allow_nan=False,
                                sort_keys=True, separators=(",", ":")).encode()
    assert cls._FIELDS == fields
    assert len(fields) == count
    assert cls._SCHEMA == schema
    assert cls._LIMIT == limit
    assert value.identity_mapping() == identity
    assert value.canonical_identity_bytes() == expected_bytes
    assert value.computed_digest() == payload[fields[-1]]
    assert value.to_mapping() == payload
    assert cls.from_mapping(value.to_mapping()) == value
    assert repr(value) == f"<{cls.__name__}>" == str(value)


def test_domain_separation_and_path_vector() -> None:
    paths = (".docs/system_overview/hybrid_integration_architecture_adr.md",
             "PLANS.md", "docs_contract_test.go")
    expected = hashlib.sha256(
        b"governed-execution.nwp-rw0-current-path-scope-binding.v1.identity\x00"
        + json.dumps(paths, separators=(",", ":")).encode()
    ).hexdigest()
    assert b1._path_scope_binding_digest(paths) == expected
    assert _digest(SCHEMAS[0][1] + ".identity", {"x": "e\u0301"}) != _digest(
        SCHEMAS[0][1] + ".identity", {"x": "\u00e9"})



# Fixed valid identity bytes are a test-owned independent vector corpus.
LITERAL_IDENTITY_JSON = {
    b1.RW0PhaseEntryBasisV1: (
        '{"basis_ref":"ref-basis-ref","c2b3d_lineage":{"accepted_intent_revision_ref":"ref-lineage-accept'
        'ed-intent-revision-ref","attempt_authorization_digest":"789c63e0f1878cd405df2dcbee38278a0b224f99'
        'd7987c89454122f8bdbad98b","attempt_authorization_ref":"ref-lineage-attempt-authorization-ref","a'
        'ttempt_fence_digest":"d459ebf8abb9661a2c027a06e0aa2cc5a750f8f8d167af8a32e1294ecf7cd93d","attempt'
        '_fence_ref":"ref-lineage-attempt-fence-ref","attempt_number":1,"author_command_digest":"b85c3181'
        'cde63168f9a9e87a8620c452830e5358bb190025d84f51d76972c980","author_command_ref":"ref-lineage-auth'
        'or-command-ref","authority_evaluation_digest":"d406b4f6d25c0bef7d112da80142645890674d164288a0df1'
        '5da567386fb356e","authority_evaluation_ref":"ref-lineage-authority-evaluation-ref","basis_decisi'
        'on_digest":"68951c7d4f3fd24241dba145511bed7173398b190eb115eb0a7aa273fbdfa026","basis_decision_re'
        'f":"ref-lineage-basis-decision-ref","candidate_ref":"ref-lineage-candidate-ref","delivery_attemp'
        't_digest":"c30efeae2fc1c0d27d19200972407e5ba56f3fb3eb8e32689d54e08af18eb5f1","delivery_attempt_r'
        'ef":"ref-lineage-delivery-attempt-ref","delivery_envelope_digest":"0ba258a06fda11de81060ce26a7ad'
        'ccdaeebc3c01e8ee7fd7c45b7ceb7ebda02","effect_authorization_digest":"b7d5604008a7d070e3c0f8015de2'
        'c893a9ff02d9ac3aacff64921e30c5dd4e45","effect_authorization_ref":"ref-lineage-effect-authorizati'
        'on-ref","effect_fence_digest":"0cf0b3077d91b5146c4e8eee255de54ec0984504028b9678c3a64504c79fc389"'
        ',"effect_fence_ref":"ref-lineage-effect-fence-ref","effect_intent_digest":"e9b7993b61f61984a4279'
        'c0bc6430ca6877223cb55d7500474594b01fb51f44d","effect_intent_ref":"ref-lineage-effect-intent-ref"'
        ',"program_ref":"ref-lineage-program-ref","program_version_number":1,"program_version_ref":"ref-l'
        'ineage-program-version-ref","semantic_attempt_digest":"8280eca26285163540f55c2e60f2e6bd2c4abf84d'
        '9eff4b5661353f5d06491d9","semantic_attempt_ref":"ref-lineage-semantic-attempt-ref","standing_gra'
        'nt_digest":"891b91640bfbe2f369135626ac272c4d305e5a5fe9f9886cd3a64323a7e34283","standing_grant_re'
        'f":"ref-lineage-standing-grant-ref","work_item_ref":"ref-lineage-work-item-ref","work_item_revis'
        'ion_ref":"ref-lineage-work-item-revision-ref","work_spec_digest":"15f1861bdfe90c412759f707a5c5c9'
        'a9990d572f41c75f470de961657bba245b","work_spec_ref":"ref-lineage-work-spec-ref","work_spec_safe_'
        'projection_digest":"81319cd00c65d90b139692391cf81b90c0b642aac03e637ba666550f4525ef74"},"current_'
        'delivery_head_digest":"d4a89e1416d00acc38c7ccba594a234f381b79e0144a2796d0c3646ac2f84262","curren'
        't_delivery_head_revision":0,"current_delivery_head_state":"planned","current_effect_head_digest"'
        ':"3e316a9e4916978db3afbefcc2d7507fe95e5c78c1d0ec9b1c8e8e8f4336f669","current_effect_head_revisio'
        'n":0,"current_effect_head_state":"ready_for_delivery","disposition":"selected_for_dispatch_gates'
        '","disposition_digest":"cb9c62cff61e13aac3681002b11eeeee0d42c8ed8d5ae10218fe37654029d9ea","dispo'
        'sition_ref":"ref-disposition-ref","global_stop_ref":"ref-global-stop-ref","global_stop_state":"c'
        'lear","global_stop_version":0,"path_scope_digest":"a07f66361352760c306129ca0cd93317c84dedc11488c'
        '14e23293edfa2ed02a6","schema_id":"governed-execution.nwp-rw0-phase-entry-basis.v1","selected_art'
        'ifact_binding_digest":"9ac8e87656c4b7294096342763238a55a2216ccc15449c1be2f66014ab8de216","select'
        'ed_artifact_digest":"8cfd0eae74aae5adf82527b031b510520d0ce26bd755728f5bcb2a34ca5d101c","selected'
        '_artifact_ref":"ref-selected-artifact-ref","selected_plan_safe_projection_digest":"8cffe8551298d'
        '3bbb65541dd9c4fcd15cf91dab3da657cc18d4fc29c3ed3d807","selected_proposal_digest":"3d07dabe7229bb3'
        '0776d62f0705c5f04cafe4a311aebf89a9d4555c18ae55725","selected_proposal_ref":"ref-selected-proposa'
        'l-ref","selection_head_digest":"d2c9d75dd0e2fa779ededcffadb18737b4ac894c6c80969197032f85dc61ee21'
        '","selection_head_revision":0,"selection_key":[["program_ref","ref-lineage-program-ref"],["seman'
        'tic_attempt_ref","ref-lineage-semantic-attempt-ref"],["candidate_ref","ref-lineage-candidate-ref'
        '"],["effect_intent_ref","ref-lineage-effect-intent-ref"],["author_command_ref","ref-lineage-auth'
        'or-command-ref"],["attempt_fence_ref","ref-lineage-attempt-fence-ref"],["effect_fence_ref","ref-'
        'lineage-effect-fence-ref"],["delivery_attempt_ref","ref-lineage-delivery-attempt-ref"]]}'
    ),
    b1.RW0AuthorityVerificationObservationV1: (
        '{"allowed_effect_classes":["author_candidate"],"attempt_basis_digest":"d45bc3556aed677eb112bc5f9'
        'cee8751ccbcc1919715cb9dab00ccd6aaf25636","attempt_basis_ref":"ref-attempt-basis-ref","attempt_fe'
        'nce_digest":"e1710d64b86b80041206bef5bb9a787618484c2a1d3418ed7ed4e57832c1a3cd","attempt_fence_re'
        'f":"ref-attempt-fence-ref","audience_ref":"ref-audience-ref","base_git_object_format":"sha1","ba'
        'se_git_oid":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","current_delivery_head_digest":"d4a89e141'
        '6d00acc38c7ccba594a234f381b79e0144a2796d0c3646ac2f84262","current_effect_head_digest":"3e316a9e4'
        '916978db3afbefcc2d7507fe95e5c78c1d0ec9b1c8e8e8f4336f669","effect_basis_digest":"79ff111a9bc91b58'
        '80aea2339f047fd4ff85571362a473c61bb02271b351ea9d","effect_basis_ref":"ref-effect-basis-ref","eff'
        'ect_class":"author_candidate","effect_fence_digest":"ac090f5ef3ac4a0222692ace8ba7bd6888743e4e91e'
        '36137241309a87d2a7fec","effect_fence_ref":"ref-effect-fence-ref","evidence_digest":"dc4dc97f2265'
        '7838fc8382d1511537101048947d38a39a3558181851296c018c","evidence_ref":"ref-evidence-ref","family_'
        'status":"compatible","global_stop_ref":"ref-global-stop-ref","global_stop_state":"clear","global'
        '_stop_version":0,"grant_expires_at":"2031-01-01T00:00:00Z","grant_family_digest":"880f70b091f0c3'
        '1685b1279f7633f15a0373a75c8c80fed50f733b70548693d2","grant_family_ref":"ref-grant-family-ref","o'
        'bservation_expires_at":"2031-01-01T00:00:00Z","observation_ref":"ref-observation-ref","observed_'
        'at":"2030-01-01T00:00:00Z","parent_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1'
        ',"max_changed_files":1,"max_cost_microusd":1,"max_cpu_seconds":1,"max_deliveries":1,"max_deploym'
        'ents":1,"max_local_commits":1,"max_memory_bytes":1,"max_merges":1,"max_model_input_tokens":1,"ma'
        'x_model_output_tokens":1,"max_pull_requests":1,"max_pushes":1,"max_wall_seconds":1},"parent_gran'
        't_digest":"fa30616958ce95c7aa600da013a23766594b44a0dd22291d9fe1659f468b8514","parent_grant_ref":'
        '"ref-parent-grant-ref","path_scope_digest":"a07f66361352760c306129ca0cd93317c84dedc11488c14e2329'
        '3edfa2ed02a6","phase_basis_digest":"90a8ccc0d0566b54608668649d61a0a41b427fbbea84d2a19cb09b8e50d4'
        '9b11","phase_basis_ref":"ref-phase-basis-ref","repository_ref":"ref-repository-ref","revocation_'
        'status":"unrevoked","schema_id":"governed-execution.nwp-rw0-authority-verification-observation.v'
        '1","source_ref":"ref-source-ref","status":"verified"}'
    ),
    b1.RW0SubordinateAuthorizationProposalV1: (
        '{"attempt_basis_digest":"d45bc3556aed677eb112bc5f9cee8751ccbcc1919715cb9dab00ccd6aaf25636","atte'
        'mpt_basis_ref":"ref-attempt-basis-ref","attempt_fence_digest":"e1710d64b86b80041206bef5bb9a78761'
        '8484c2a1d3418ed7ed4e57832c1a3cd","attempt_fence_ref":"ref-attempt-fence-ref","audience_ref":"ref'
        '-audience-ref","base_git_object_format":"sha1","base_git_oid":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        'aaaaaaa","ceilings":{"max_active_invocations":1,"max_candidate_bytes":1,"max_changed_files":1,"m'
        'ax_cost_microusd":1,"max_cpu_seconds":1,"max_deliveries":1,"max_deployments":1,"max_local_commit'
        's":1,"max_memory_bytes":1,"max_merges":1,"max_model_input_tokens":1,"max_model_output_tokens":1,'
        '"max_pull_requests":1,"max_pushes":1,"max_wall_seconds":1},"effect_basis_digest":"79ff111a9bc91b'
        '5880aea2339f047fd4ff85571362a473c61bb02271b351ea9d","effect_basis_ref":"ref-effect-basis-ref","e'
        'ffect_class":"author_candidate","effect_fence_digest":"ac090f5ef3ac4a0222692ace8ba7bd6888743e4e9'
        '1e36137241309a87d2a7fec","effect_fence_ref":"ref-effect-fence-ref","expires_at":"2031-01-01T00:0'
        '0:00Z","global_stop_ref":"ref-global-stop-ref","global_stop_version":0,"grant_family_digest":"88'
        '0f70b091f0c31685b1279f7633f15a0373a75c8c80fed50f733b70548693d2","grant_family_ref":"ref-grant-fa'
        'mily-ref","parent_grant_digest":"fa30616958ce95c7aa600da013a23766594b44a0dd22291d9fe1659f468b851'
        '4","parent_grant_ref":"ref-parent-grant-ref","path_scope_digest":"a07f66361352760c306129ca0cd933'
        '17c84dedc11488c14e23293edfa2ed02a6","phase_basis_digest":"90a8ccc0d0566b54608668649d61a0a41b427f'
        'bbea84d2a19cb09b8e50d49b11","phase_basis_ref":"ref-phase-basis-ref","proposal_ref":"ref-proposal'
        '-ref","repository_ref":"ref-repository-ref","schema_id":"governed-execution.nwp-rw0-subordinate-'
        'authorization-proposal.v1","verification_digest":"8866ec18b2ab885932ed3c73495880696d7f49ddc140ef'
        '0b8d848577713c8065","verification_ref":"ref-verification-ref"}'
    ),
    b1.RW0CustodyAvailabilityObservationV1: (
        '{"availability":"available","byte_length":1,"content_sha256":"656484a17acd7aee553f2b603e3353fcda'
        '2a2e7dd87175ed7178e0ae7b4ddcd4","evidence_digest":"dc4dc97f22657838fc8382d1511537101048947d38a39'
        'a3558181851296c018c","evidence_ref":"ref-evidence-ref","expires_at":"2031-01-01T00:00:00Z","obse'
        'rvation_ref":"ref-observation-ref","observed_at":"2030-01-01T00:00:00Z","phase_basis_digest":"90'
        'a8ccc0d0566b54608668649d61a0a41b427fbbea84d2a19cb09b8e50d49b11","phase_basis_ref":"ref-phase-bas'
        'is-ref","schema_id":"governed-execution.nwp-rw0-custody-availability-observation.v1","source_ref'
        '":"ref-source-ref","subject_kind":"work_spec","subject_ref":"ref-subject-ref","subject_semantic_'
        'digest":"8fb6da23246c16477cc80413db5a3266723d3ab72510d3d0d0a32a2388022e49"}'
    ),
    b1.RW0RetrievalCapabilityEventObservationV1: (
        '{"attempt_fence_digest":"e1710d64b86b80041206bef5bb9a787618484c2a1d3418ed7ed4e57832c1a3cd","atte'
        'mpt_fence_ref":"ref-attempt-fence-ref","audience_ref":"ref-audience-ref","authority_observation_'
        'digest":"43ef81bf2cd791c6b8a20c1ca3884d4cbc8da7115011b0a2a3d08daf083accdc","authority_observatio'
        'n_ref":"ref-authority-observation-ref","base_git_object_format":"sha1","base_git_oid":"aaaaaaaaa'
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","byte_length":1,"content_sha256":"656484a17acd7aee553f2b603e335'
        '3fcda2a2e7dd87175ed7178e0ae7b4ddcd4","custody_observation_digest":"ede37b391c656cc19ab9f0b6d58d5'
        '5dd5e881e089fd6da188f2876c3d9c63851","custody_observation_ref":"ref-custody-observation-ref","ef'
        'fect_fence_digest":"ac090f5ef3ac4a0222692ace8ba7bd6888743e4e91e36137241309a87d2a7fec","effect_fe'
        'nce_ref":"ref-effect-fence-ref","effect_intent_ref":"ref-effect-intent-ref","event_kind":"issued'
        '","event_ref":"ref-event-ref","evidence_digest":"dc4dc97f22657838fc8382d1511537101048947d38a39a3'
        '558181851296c018c","evidence_ref":"ref-evidence-ref","expires_at":"2031-01-01T00:00:00Z","occurr'
        'ed_at":"2030-01-01T00:00:00Z","path_scope_digest":"a07f66361352760c306129ca0cd93317c84dedc11488c'
        '14e23293edfa2ed02a6","phase_basis_digest":"90a8ccc0d0566b54608668649d61a0a41b427fbbea84d2a19cb09'
        'b8e50d49b11","phase_basis_ref":"ref-phase-basis-ref","predecessor_event_digest":null,"predecesso'
        'r_event_ref":null,"repository_ref":"ref-repository-ref","safe_correlation_ref":"ref-safe-correla'
        'tion-ref","schema_id":"governed-execution.nwp-rw0-retrieval-capability-event-observation.v1","se'
        'mantic_attempt_ref":"ref-semantic-attempt-ref","sequence_number":0,"source_ref":"ref-source-ref"'
        ',"subject_kind":"work_spec","subject_ref":"ref-subject-ref","subject_semantic_digest":"8fb6da232'
        '46c16477cc80413db5a3266723d3ab72510d3d0d0a32a2388022e49","subordinate_proposal_digest":"69f29044'
        '1ab2d4473fdfe61f72caab32c089c5b149ab9fc573537de286902e6d","subordinate_proposal_ref":"ref-subord'
        'inate-proposal-ref"}'
    ),
    b1.RW0RemoteHostReadinessObservationV1: (
        '{"architecture_profile_digest":"35ace60b14345eaeacbd683bde0e1a595ed9abee899baa9727372b68969c6420'
        '","architecture_profile_ref":"ref-architecture-profile-ref","cancellation_profile_digest":"b24b5'
        '38f5258c22e20519039ab0cdecbbf333ff2c707ac5d77da86cb430afb16","cancellation_profile_ref":"ref-can'
        'cellation-profile-ref","capsule_store_profile_digest":"47feb759be584fb467c58910653087970caceef76'
        '3621aa0a588b88ff04ddf14","capsule_store_profile_ref":"ref-capsule-store-profile-ref","cleanup_pr'
        'ofile_digest":"3f2712c488d26b36eec75c1febe2837be32ef9c325e55a332115c14deb6b9cf6","cleanup_profil'
        'e_ref":"ref-cleanup-profile-ref","credential_handoff_profile_digest":"0300376f46291fb27eec3da74b'
        '36c732fbd96e8b39174687b5234c4d740c631b","credential_handoff_profile_ref":"ref-credential-handoff'
        '-profile-ref","evidence_digest":"dc4dc97f22657838fc8382d1511537101048947d38a39a3558181851296c018'
        'c","evidence_ref":"ref-evidence-ref","execution_identity_profile_digest":"e83b0e28f388da60a71a95'
        '7c1e0b51da9abf308a742358e0fd08fbf86439043d","execution_identity_profile_ref":"ref-execution-iden'
        'tity-profile-ref","expires_at":"2031-01-01T00:00:00Z","isolation_profile_digest":"29ed6b4cb0ad95'
        '8b1bc97b12294693a97dd5a75eec734f90950b8b9014558213","isolation_profile_ref":"ref-isolation-profi'
        'le-ref","observation_ref":"ref-observation-ref","observed_at":"2030-01-01T00:00:00Z","platform":'
        '"linux","platform_profile_digest":"6756c6ea25a2be459bd82168bc94ef8a7357318991c0505355181b96a5fc8'
        '715","platform_profile_ref":"ref-platform-profile-ref","process_profile_digest":"863b5d5eba3a263'
        'bcbd1d59ff1daa3e776575dd0490acc33637dd413a51ea9b7","process_profile_ref":"ref-process-profile-re'
        'f","resource_profile_digest":"08103f2f0f43f1b465c344258382a9d37346bd9bd3d36cfb63e31711e5e8c344",'
        '"resource_profile_ref":"ref-resource-profile-ref","review_tool_profile_digest":"ee617eefd1467196'
        '46535081591db4a8525380f5dccbaa8c3ee2a3eae00a2361","review_tool_profile_ref":"ref-review-tool-pro'
        'file-ref","safe_host_correlation_ref":"ref-safe-host-correlation-ref","schema_id":"governed-exec'
        'ution.nwp-rw0-remote-host-readiness-observation.v1","source_ref":"ref-source-ref","status":"read'
        'y","validation_tool_profile_digest":"ba5cbcc5387ce4544b375045607f40eff8d88805a6676a62807f9952385'
        '05904","validation_tool_profile_ref":"ref-validation-tool-profile-ref","worker_artifact_digest":'
        '"7b2fb3b2535d91a55f49784d46604aaa1c438c18bb508def7c0c3e8c407f6554","worker_artifact_ref":"ref-wo'
        'rker-artifact-ref","worker_protocol_digest":"79077d77f57d69a8694768f3cb23f1d30cbd4d2951055f1c36e'
        '36d2d7e1ebf5e","worker_protocol_ref":"ref-worker-protocol-ref"}'
    ),
    b1.RW0EffectHostQualificationV1: (
        '{"effect_fence_digest":"ac090f5ef3ac4a0222692ace8ba7bd6888743e4e91e36137241309a87d2a7fec","effec'
        't_fence_ref":"ref-effect-fence-ref","effect_intent_ref":"ref-effect-intent-ref","evaluated_at":"'
        '2031-01-01T00:00:00Z","phase_basis_digest":"90a8ccc0d0566b54608668649d61a0a41b427fbbea84d2a19cb0'
        '9b8e50d49b11","phase_basis_ref":"ref-phase-basis-ref","qualification_ref":"ref-qualification-ref'
        '","readiness_digest":"18e040e6ffb0bad072d8acc014ae3dd6bb10cbfbbf3b94f7c488d72784534029","readine'
        'ss_ref":"ref-readiness-ref","reason":"qualified","required_architecture_profile_digest":"58864cf'
        'e45bc15ad2cb1c61056a81da003912e841a03ede48a258db9a07f38fb","required_architecture_profile_ref":"'
        'ref-required-architecture-profile-ref","required_cancellation_profile_digest":"c45f842c15886113e'
        '27e0f469f60cdf82786a4d50dc283405d2010ec1ba22421","required_cancellation_profile_ref":"ref-requir'
        'ed-cancellation-profile-ref","required_capsule_store_profile_digest":"897eab8ed0085642b60fac9c18'
        '0c16ecace4b4f078cb3eeff670732823eb8c4b","required_capsule_store_profile_ref":"ref-required-capsu'
        'le-store-profile-ref","required_cleanup_profile_digest":"0f709e01473c2c3335a43e531a7640ca77d0f36'
        '8f150ca44af38b2b44db6f308","required_cleanup_profile_ref":"ref-required-cleanup-profile-ref","re'
        'quired_credential_handoff_profile_digest":"6cbe38aaf1d44f4b8a649f3ba3b22cc8fdda4a4dfda4b290f3f59'
        '5be7045c4b2","required_credential_handoff_profile_ref":"ref-required-credential-handoff-profile-'
        'ref","required_execution_identity_profile_digest":"9e8a7bacc07ad33836d609b12f957fc109bf696f3cd83'
        'cd1aaccc4da01381db0","required_execution_identity_profile_ref":"ref-required-execution-identity-'
        'profile-ref","required_isolation_profile_digest":"8fdaf8e1db513342cd0e36b05ab29b53a46196f526a770'
        '7a33d5930336ca38a4","required_isolation_profile_ref":"ref-required-isolation-profile-ref","requi'
        'red_platform_profile_digest":"552e7faae866a496f4cac63710f8ca3121376b2276ad689e0f0a3e74df5e30ba",'
        '"required_platform_profile_ref":"ref-required-platform-profile-ref","required_process_profile_di'
        'gest":"614cb80511a8dd2654dc4aa96ed43274b8367333e5149ce7cf997c82b0f23cff","required_process_profi'
        'le_ref":"ref-required-process-profile-ref","required_resource_profile_digest":"e43ca6678f62f6891'
        '0b402ac322a6054f1001dd01c7532e5aad88623b8a7e47e","required_resource_profile_ref":"ref-required-r'
        'esource-profile-ref","required_review_tool_profile_digest":"bb6688a6c9f9e5c2ae66db638124f6039440'
        '79c431683c641f4e5e22eb4c5a44","required_review_tool_profile_ref":"ref-required-review-tool-profi'
        'le-ref","required_scenario_profile_digest":"449c0d02fd3139ef47687fcbc173db0a81e23e6c1f4464dfbc38'
        '5c34382e3645","required_scenario_profile_ref":"ref-required-scenario-profile-ref","required_vali'
        'dation_tool_profile_digest":"49eb16808a63c72cf682e4c5b1e570a49de795ffc48b8384b614510b8a4f1019","'
        'required_validation_tool_profile_ref":"ref-required-validation-tool-profile-ref","required_worke'
        'r_artifact_digest":"3e9df5dc82da6b38b15ee6ed02078663db43c45a18aaf2f952ac7a7f2a293a8a","required_'
        'worker_artifact_ref":"ref-required-worker-artifact-ref","required_worker_protocol_digest":"fa936'
        '0406f70221dbfc2b643881f2d6c00bff65e504fac9244c77ac3b8501e9c","required_worker_protocol_ref":"ref'
        '-required-worker-protocol-ref","result":"qualified","schema_id":"governed-execution.nwp-rw0-effe'
        'ct-host-qualification.v1","verification_digest":"8866ec18b2ab885932ed3c73495880696d7f49ddc140ef0'
        'b8d848577713c8065","verification_ref":"ref-verification-ref"}'
    ),
    b1.RW0TerminalOutcomeV1: (
        '{"branch":"normal","decision_digest":"7959ca91e1653558a1ae94b36ba33703f3c69eb75219a30d02d95931a4'
        '42a2c3","decision_kind":"block","decision_ref":"ref-decision-ref","delivery_head_digest":"bde031'
        'bbcecf639b15ee43e7929daab9b3a90b72f6b776b2abd3b0071de510c0","delivery_head_revision":0,"effect_h'
        'ead_digest":"03fb2092de9ec3bfedcdd13376672dfd7188b6cafc5508868532907dd524e8c2","effect_head_revi'
        'sion":0,"evidence_set_digest":"747baa37c74d69ecccdc770d57dabccfc8454530da994bf6d2a4f14bc1a74669"'
        ',"evidence_set_ref":"ref-evidence-set-ref","global_stop_ref":"ref-global-stop-ref","global_stop_'
        'state":"clear","global_stop_version":0,"latch_postimage_digest":null,"latch_postimage_ref":null,'
        '"mismatch_digest":null,"mismatch_ref":null,"outcome":"block","outcome_value_ref":"ref-outcome-va'
        'lue-ref","phase_basis_digest":"90a8ccc0d0566b54608668649d61a0a41b427fbbea84d2a19cb09b8e50d49b11"'
        ',"phase_basis_ref":"ref-phase-basis-ref","program_head_digest":"df3f749f35567ceacf535f88308f87a4'
        'e919d27777e24709cfe3e5ca114cd6de","program_head_revision":0,"reconciliation_digest":null,"reconc'
        'iliation_ref":null,"schema_id":"governed-execution.nwp-rw0-terminal-outcome-value.v1","selection'
        '_head_digest":"d2c9d75dd0e2fa779ededcffadb18737b4ac894c6c80969197032f85dc61ee21","selection_head'
        '_revision":0,"work_item_head_digest":"040f7245dc08a721ac07f9e9c03ebb143f0cb70ac035c089a17ff93761'
        'a998c7","work_item_head_revision":0}'
    ),
}


def test_literal_field_oracle_detects_same_count_reorder_and_rename() -> None:
    assert tuple(EXPECTED_FIELDS) == tuple(cls for cls, _, _, _ in SCHEMAS)
    for cls, schema, count, limit in SCHEMAS:
        expected = EXPECTED_FIELDS[cls]
        assert cls._FIELDS == expected
        assert len(expected) == count
        assert cls._SCHEMA == schema
        assert cls._LIMIT == limit
        swapped = (expected[1], expected[0], *expected[2:])
        renamed = (*expected[:-2], "same_count_mutant", expected[-1])
        assert len(swapped) == len(renamed) == count
        assert swapped != expected and renamed != expected
        with pytest.raises(AssertionError):
            assert swapped == expected
        with pytest.raises(AssertionError):
            assert renamed == expected


@pytest.mark.parametrize("cls,schema,count,limit", SCHEMAS)
def test_fixed_literal_canonical_identity_vectors(cls: type, schema: str,
        count: int, limit: int) -> None:
    literal = LITERAL_IDENTITY_JSON[cls]
    identity = json.loads(literal)
    assert type(identity) is dict
    assert tuple(identity) != EXPECTED_FIELDS[cls][:-1]  # canonical keys are sorted
    digest = hashlib.sha256(
        (schema + ".identity").encode("utf-8") + b"\x00" + literal.encode("utf-8")
    ).hexdigest()
    record = {**identity, EXPECTED_FIELDS[cls][-1]: digest}
    value = cls.from_mapping(record)
    assert value.canonical_identity_bytes() == literal.encode("utf-8")
    assert value.computed_digest() == digest
    assert value.to_mapping() == record
    assert cls._FIELDS == EXPECTED_FIELDS[cls] and len(cls._FIELDS) == count
    assert cls._SCHEMA == schema and cls._LIMIT == limit
