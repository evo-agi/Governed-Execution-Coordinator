"""Literal, test-owned vectors for the three private Capability schemas."""

from __future__ import annotations

import hashlib

import ge_nwp_coordinator._rw0_worker_mechanism_capability_values as capability
from ge_nwp_coordinator._rw0_worker_mechanism_capability_values import (
    RW0WorkerMechanismCapabilityDeclarationV1,
    RW0WorkerMechanismCapabilityObservationV1,
    RW0WorkerMechanismCapabilityQualificationV1,
)


DECLARATION_FIELDS = (
    "schema_id", "capability_declaration_ref", "declaration_source_kind",
    "declaration_source_ref", "worker_artifact_ref", "worker_artifact_digest",
    "wire_profile_ref", "wire_profile_digest", "noninteractive_operation",
    "wire_command_input_only", "wire_result_output_only", "protocol_stdout_only",
    "private_bounded_diagnostic_stderr", "external_cancellation_control_supported",
    "external_deadline_control_supported", "invocation_bound_logical_context",
    "private_history_non_authority", "isolated_credential_use",
    "private_interaction_material", "zero_git_effects", "restricted_network_access",
    "external_session_non_authority", "capability_declaration_digest",
)
OBSERVATION_FIELDS = (
    "schema_id", "capability_observation_ref", "observation_source_kind",
    "observation_source_ref", "observation_source_invocation_ref", "evidence_ref",
    "evidence_digest", "capability_declaration_ref", "capability_declaration_digest",
    "worker_artifact_ref", "worker_artifact_digest", "wire_profile_ref",
    "wire_profile_digest", "noninteractive_operation", "wire_command_input_only",
    "wire_result_output_only", "protocol_stdout_only",
    "private_bounded_diagnostic_stderr", "external_cancellation_control_supported",
    "external_deadline_control_supported", "invocation_bound_logical_context",
    "private_history_non_authority", "isolated_credential_use",
    "private_interaction_material", "zero_git_effects", "restricted_network_access",
    "external_session_non_authority", "observed_at", "expires_at",
    "capability_observation_digest",
)
QUALIFICATION_FIELDS = (
    "schema_id", "capability_qualification_ref", "capability_declaration_ref",
    "capability_declaration_digest", "capability_observation_ref",
    "capability_observation_digest", "worker_artifact_ref", "worker_artifact_digest",
    "wire_profile_ref", "wire_profile_digest", "phase_basis_ref", "phase_basis_digest",
    "authority_observation_ref", "authority_observation_digest",
    "readiness_observation_ref", "readiness_observation_digest",
    "host_qualification_ref", "host_qualification_digest", "effect_intent_ref",
    "effect_fence_ref", "effect_fence_digest", "result", "reason", "evaluated_at",
    "capability_qualification_digest",
)
DIMENSIONS = (
    "noninteractive_operation", "wire_command_input_only", "wire_result_output_only",
    "protocol_stdout_only", "private_bounded_diagnostic_stderr",
    "external_cancellation_control_supported", "external_deadline_control_supported",
    "invocation_bound_logical_context", "private_history_non_authority",
    "isolated_credential_use", "private_interaction_material", "zero_git_effects",
    "restricted_network_access", "external_session_non_authority",
)

DECLARATION_SCHEMA = "governed-execution.nwp-rw0-worker-mechanism-capability-declaration.v1"
OBSERVATION_SCHEMA = "governed-execution.nwp-rw0-worker-mechanism-capability-observation.v1"
QUALIFICATION_SCHEMA = "governed-execution.nwp-rw0-worker-mechanism-capability-qualification.v1"
DECLARATION_DOMAIN = DECLARATION_SCHEMA + ".identity"
OBSERVATION_DOMAIN = OBSERVATION_SCHEMA + ".identity"
QUALIFICATION_DOMAIN = QUALIFICATION_SCHEMA + ".identity"
WIRE_REF = "rw0-wire-nwpf-v1"
WIRE_DIGEST = "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454"


DECLARATION_VECTOR: dict[str, str] = {
    "schema_id": DECLARATION_SCHEMA,
    "capability_declaration_ref": "capability-declaration.vector.0001",
    "declaration_source_kind": "worker_artifact_owner",
    "declaration_source_ref": "artifact-owner.vector.0001",
    "worker_artifact_ref": "worker-artifact.vector.0001",
    "worker_artifact_digest": "1111111111111111111111111111111111111111111111111111111111111111",
    "wire_profile_ref": WIRE_REF,
    "wire_profile_digest": WIRE_DIGEST,
    "noninteractive_operation": "supported",
    "wire_command_input_only": "supported",
    "wire_result_output_only": "supported",
    "protocol_stdout_only": "supported",
    "private_bounded_diagnostic_stderr": "supported",
    "external_cancellation_control_supported": "supported",
    "external_deadline_control_supported": "supported",
    "invocation_bound_logical_context": "supported",
    "private_history_non_authority": "supported",
    "isolated_credential_use": "supported",
    "private_interaction_material": "supported",
    "zero_git_effects": "supported",
    "restricted_network_access": "supported",
    "external_session_non_authority": "supported",
    "capability_declaration_digest": "3f539b5a40b3f74316779eef78fe462e4df78961ebf611b017772f767df26423",
}

OBSERVATION_VECTOR: dict[str, str] = {
    "schema_id": OBSERVATION_SCHEMA,
    "capability_observation_ref": "capability-observation.vector.0001",
    "observation_source_kind": "independent_worker_mechanism_observer",
    "observation_source_ref": "independent-observer.vector.0001",
    "observation_source_invocation_ref": "observer-invocation.vector.0001",
    "evidence_ref": "capability-evidence.vector.0001",
    "evidence_digest": "2222222222222222222222222222222222222222222222222222222222222222",
    "capability_declaration_ref": "capability-declaration.vector.0001",
    "capability_declaration_digest": "3f539b5a40b3f74316779eef78fe462e4df78961ebf611b017772f767df26423",
    "worker_artifact_ref": "worker-artifact.vector.0001",
    "worker_artifact_digest": "1111111111111111111111111111111111111111111111111111111111111111",
    "wire_profile_ref": WIRE_REF,
    "wire_profile_digest": WIRE_DIGEST,
    "noninteractive_operation": "confirmed",
    "wire_command_input_only": "confirmed",
    "wire_result_output_only": "confirmed",
    "protocol_stdout_only": "confirmed",
    "private_bounded_diagnostic_stderr": "confirmed",
    "external_cancellation_control_supported": "confirmed",
    "external_deadline_control_supported": "confirmed",
    "invocation_bound_logical_context": "confirmed",
    "private_history_non_authority": "confirmed",
    "isolated_credential_use": "confirmed",
    "private_interaction_material": "confirmed",
    "zero_git_effects": "confirmed",
    "restricted_network_access": "confirmed",
    "external_session_non_authority": "confirmed",
    "observed_at": "2028-02-29T12:34:56Z",
    "expires_at": "2030-01-02T03:04:05Z",
    "capability_observation_digest": "4c0c3dca3d3978f466ff2b20e07931cae248750a9a794fb1c2737b6ae73dfa9c",
}

QUALIFICATION_VECTOR: dict[str, str] = {
    "schema_id": QUALIFICATION_SCHEMA,
    "capability_qualification_ref": "capability-qualification.vector.0001",
    "capability_declaration_ref": "capability-declaration.vector.0001",
    "capability_declaration_digest": "3f539b5a40b3f74316779eef78fe462e4df78961ebf611b017772f767df26423",
    "capability_observation_ref": "capability-observation.vector.0001",
    "capability_observation_digest": "4c0c3dca3d3978f466ff2b20e07931cae248750a9a794fb1c2737b6ae73dfa9c",
    "worker_artifact_ref": "worker-artifact.vector.0001",
    "worker_artifact_digest": "1111111111111111111111111111111111111111111111111111111111111111",
    "wire_profile_ref": WIRE_REF,
    "wire_profile_digest": WIRE_DIGEST,
    "phase_basis_ref": "phase-basis.vector.0001",
    "phase_basis_digest": "3333333333333333333333333333333333333333333333333333333333333333",
    "authority_observation_ref": "authority-observation.vector.0001",
    "authority_observation_digest": "4444444444444444444444444444444444444444444444444444444444444444",
    "readiness_observation_ref": "readiness-observation.vector.0001",
    "readiness_observation_digest": "5555555555555555555555555555555555555555555555555555555555555555",
    "host_qualification_ref": "host-qualification.vector.0001",
    "host_qualification_digest": "6666666666666666666666666666666666666666666666666666666666666666",
    "effect_intent_ref": "effect-intent.vector.0001",
    "effect_fence_ref": "effect-fence.vector.0001",
    "effect_fence_digest": "7777777777777777777777777777777777777777777777777777777777777777",
    "result": "qualified",
    "reason": "qualified",
    "evaluated_at": "2029-01-01T00:00:00Z",
    "capability_qualification_digest": "7da4eaca3f6c1d05c1be487a89de602170a423aa5b92e839d97267cf69a05fad",
}

# These literal byte strings and digests are frozen test vectors. They are
# independent of production constants and compared byte-for-byte.
DECLARATION_CANONICAL = b'{"capability_declaration_ref":"capability-declaration.vector.0001","declaration_source_kind":"worker_artifact_owner","declaration_source_ref":"artifact-owner.vector.0001","external_cancellation_control_supported":"supported","external_deadline_control_supported":"supported","external_session_non_authority":"supported","invocation_bound_logical_context":"supported","isolated_credential_use":"supported","noninteractive_operation":"supported","private_bounded_diagnostic_stderr":"supported","private_history_non_authority":"supported","private_interaction_material":"supported","protocol_stdout_only":"supported","restricted_network_access":"supported","schema_id":"governed-execution.nwp-rw0-worker-mechanism-capability-declaration.v1","wire_command_input_only":"supported","wire_profile_digest":"470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454","wire_profile_ref":"rw0-wire-nwpf-v1","wire_result_output_only":"supported","worker_artifact_digest":"1111111111111111111111111111111111111111111111111111111111111111","worker_artifact_ref":"worker-artifact.vector.0001","zero_git_effects":"supported"}'
OBSERVATION_CANONICAL = b'{"capability_declaration_digest":"3f539b5a40b3f74316779eef78fe462e4df78961ebf611b017772f767df26423","capability_declaration_ref":"capability-declaration.vector.0001","capability_observation_ref":"capability-observation.vector.0001","evidence_digest":"2222222222222222222222222222222222222222222222222222222222222222","evidence_ref":"capability-evidence.vector.0001","expires_at":"2030-01-02T03:04:05Z","external_cancellation_control_supported":"confirmed","external_deadline_control_supported":"confirmed","external_session_non_authority":"confirmed","invocation_bound_logical_context":"confirmed","isolated_credential_use":"confirmed","noninteractive_operation":"confirmed","observation_source_invocation_ref":"observer-invocation.vector.0001","observation_source_kind":"independent_worker_mechanism_observer","observation_source_ref":"independent-observer.vector.0001","observed_at":"2028-02-29T12:34:56Z","private_bounded_diagnostic_stderr":"confirmed","private_history_non_authority":"confirmed","private_interaction_material":"confirmed","protocol_stdout_only":"confirmed","restricted_network_access":"confirmed","schema_id":"governed-execution.nwp-rw0-worker-mechanism-capability-observation.v1","wire_command_input_only":"confirmed","wire_profile_digest":"470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454","wire_profile_ref":"rw0-wire-nwpf-v1","wire_result_output_only":"confirmed","worker_artifact_digest":"1111111111111111111111111111111111111111111111111111111111111111","worker_artifact_ref":"worker-artifact.vector.0001","zero_git_effects":"confirmed"}'
QUALIFICATION_CANONICAL = b'{"authority_observation_digest":"4444444444444444444444444444444444444444444444444444444444444444","authority_observation_ref":"authority-observation.vector.0001","capability_declaration_digest":"3f539b5a40b3f74316779eef78fe462e4df78961ebf611b017772f767df26423","capability_declaration_ref":"capability-declaration.vector.0001","capability_observation_digest":"4c0c3dca3d3978f466ff2b20e07931cae248750a9a794fb1c2737b6ae73dfa9c","capability_observation_ref":"capability-observation.vector.0001","capability_qualification_ref":"capability-qualification.vector.0001","effect_fence_digest":"7777777777777777777777777777777777777777777777777777777777777777","effect_fence_ref":"effect-fence.vector.0001","effect_intent_ref":"effect-intent.vector.0001","evaluated_at":"2029-01-01T00:00:00Z","host_qualification_digest":"6666666666666666666666666666666666666666666666666666666666666666","host_qualification_ref":"host-qualification.vector.0001","phase_basis_digest":"3333333333333333333333333333333333333333333333333333333333333333","phase_basis_ref":"phase-basis.vector.0001","readiness_observation_digest":"5555555555555555555555555555555555555555555555555555555555555555","readiness_observation_ref":"readiness-observation.vector.0001","reason":"qualified","result":"qualified","schema_id":"governed-execution.nwp-rw0-worker-mechanism-capability-qualification.v1","wire_profile_digest":"470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454","wire_profile_ref":"rw0-wire-nwpf-v1","worker_artifact_digest":"1111111111111111111111111111111111111111111111111111111111111111","worker_artifact_ref":"worker-artifact.vector.0001"}'
DECLARATION_DIGEST = "3f539b5a40b3f74316779eef78fe462e4df78961ebf611b017772f767df26423"
OBSERVATION_DIGEST = "4c0c3dca3d3978f466ff2b20e07931cae248750a9a794fb1c2737b6ae73dfa9c"
QUALIFICATION_DIGEST = "7da4eaca3f6c1d05c1be487a89de602170a423aa5b92e839d97267cf69a05fad"


def test_literal_schema_field_domain_and_wire_vectors() -> None:
    assert RW0WorkerMechanismCapabilityDeclarationV1._FIELDS == DECLARATION_FIELDS
    assert RW0WorkerMechanismCapabilityObservationV1._FIELDS == OBSERVATION_FIELDS
    assert RW0WorkerMechanismCapabilityQualificationV1._FIELDS == QUALIFICATION_FIELDS
    assert RW0WorkerMechanismCapabilityDeclarationV1._SCHEMA == DECLARATION_SCHEMA
    assert RW0WorkerMechanismCapabilityObservationV1._SCHEMA == OBSERVATION_SCHEMA
    assert RW0WorkerMechanismCapabilityQualificationV1._SCHEMA == QUALIFICATION_SCHEMA
    assert RW0WorkerMechanismCapabilityDeclarationV1._DIGEST_DOMAIN == DECLARATION_DOMAIN
    assert RW0WorkerMechanismCapabilityObservationV1._DIGEST_DOMAIN == OBSERVATION_DOMAIN
    assert RW0WorkerMechanismCapabilityQualificationV1._DIGEST_DOMAIN == QUALIFICATION_DOMAIN
    assert capability._WIRE_PROFILE_REF == WIRE_REF
    assert capability._WIRE_PROFILE_DIGEST == WIRE_DIGEST


def test_literal_complete_canonical_and_digest_vectors() -> None:
    cases = (
        (RW0WorkerMechanismCapabilityDeclarationV1, DECLARATION_VECTOR,
         "capability_declaration_digest", DECLARATION_CANONICAL, DECLARATION_DIGEST,
         DECLARATION_DOMAIN),
        (RW0WorkerMechanismCapabilityObservationV1, OBSERVATION_VECTOR,
         "capability_observation_digest", OBSERVATION_CANONICAL, OBSERVATION_DIGEST,
         OBSERVATION_DOMAIN),
        (RW0WorkerMechanismCapabilityQualificationV1, QUALIFICATION_VECTOR,
         "capability_qualification_digest", QUALIFICATION_CANONICAL,
         QUALIFICATION_DIGEST, QUALIFICATION_DOMAIN),
    )
    for cls, literal, final, expected_bytes, expected_digest, domain in cases:
        assert literal[final] == expected_digest
        value = cls.from_mapping(dict(literal))
        assert value.canonical_identity_bytes() == expected_bytes
        assert value.computed_digest() == expected_digest
        assert hashlib.sha256(domain.encode("utf-8") + b"\0" + expected_bytes).hexdigest() == expected_digest
        first = value.to_mapping()
        second = value.to_mapping()
        assert first == literal == second
        assert first is not second
        assert tuple(first) == cls._FIELDS


def test_canonical_encoding_does_not_normalize_unicode() -> None:
    composed = {"z": "é", "a": "é"}
    decomposed = {"z": "e\u0301", "a": "e\u0301"}
    assert capability._raw_canonical_bytes(composed) == b'{"a":"\xc3\xa9","z":"\xc3\xa9"}'
    assert capability._raw_canonical_bytes(decomposed) == b'{"a":"e\xcc\x81","z":"e\xcc\x81"}'
    assert capability._raw_canonical_bytes(composed) != capability._raw_canonical_bytes(decomposed)
