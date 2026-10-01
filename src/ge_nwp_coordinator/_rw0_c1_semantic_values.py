"""Private pure RW0-C1 commands, identities, results, and recovery values.

The module performs no I/O and grants no execution, source-authenticity,
completeness, custody, or acceptance authority.  Raw WorkSpec, capsule, blob,
and sealed Wire-error objects are retained only by private in-memory commands;
their representations and errors are content free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import datetime
from enum import Enum
import hashlib
import json
import re
import struct
import typing

from ._rw0_phase_entry_semantic_values import (
    RW0AuthorityVerificationObservationV1,
    RW0CustodyAvailabilityObservationV1,
    RW0EffectHostQualificationV1,
    RW0PhaseEntryBasisV1,
    RW0RemoteHostReadinessObservationV1,
    RW0RetrievalCapabilityEventObservationV1,
    RW0SubordinateAuthorizationProposalV1,
)
from ._rw0_wire_protocol_values import (
    RW0WireCancellationRequestObservationV1,
    RW0WireProcessObservationV1,
    RW0WireProtocolError,
)
from ._rw0_worker_mechanism_capability_values import (
    RW0WorkerMechanismCapabilityDeclarationV1,
    RW0WorkerMechanismCapabilityObservationV1,
    RW0WorkerMechanismCapabilityQualificationV1,
)
from ._worker_execution_semantic_values import (
    CandidateCapsuleManifestV1,
    WorkSpecV1,
    WorkerObservationV1,
)


__all__: tuple[str, ...] = ()


_MAX_INT = 9_223_372_036_854_775_807
_SAFE_REF_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]*\Z")
_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_RESERVED_SAFE_REF_PREFIXES = (
    "connector-",
    "tunnel-",
    "workspace-",
    "org-",
    "organization-",
    "user-",
)
_NWPF_REF = "rw0-wire-nwpf-v1"
_NWPF_DIGEST = "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454"

_ESTABLISH_COMMAND_SCHEMA = "governed-execution.nwp-rw0-c1-establish-phase-command.v1"
_ADMIT_COMMAND_SCHEMA = "governed-execution.nwp-rw0-c1-admit-evidence-command.v1"
_ESTABLISH_RESULT_SCHEMA = "governed-execution.nwp-rw0-c1-establish-phase-result.v1"
_ADMIT_RESULT_SCHEMA = "governed-execution.nwp-rw0-c1-admit-evidence-result.v1"
_RECEIPT_SCHEMA = "governed-execution.nwp-rw0-c1-mutation-receipt.v1"
_RECOVERY_SCHEMA = "governed-execution.nwp-rw0-c1-recovery-result.v1"
_EVIDENCE_RECOVERY_SELECTOR_SCHEMA = (
    "governed-execution.nwp-rw0-c1-evidence-admission-recovery-selector.v1"
)
_MEMBERSHIP_SCHEMA = "governed-execution.nwp-rw0-c1-evidence-membership.v1"
_SNAPSHOT_SCHEMAS = {
    "selection_head_snapshot": (
        "governed-execution.nwp-rw0-c1-selection-head-admission-snapshot-binding.v1",
        "selection",
    ),
    "effect_head_snapshot": (
        "governed-execution.nwp-rw0-c1-effect-head-admission-snapshot-binding.v1",
        "effect",
    ),
    "delivery_head_snapshot": (
        "governed-execution.nwp-rw0-c1-delivery-head-admission-snapshot-binding.v1",
        "delivery",
    ),
    "global_stop_snapshot": (
        "governed-execution.nwp-rw0-c1-global-stop-admission-snapshot-binding.v1",
        "global-stop",
    ),
}
_WORKER_RESULT_BINDING_SCHEMA = (
    "governed-execution.nwp-rw0-c1-wire-worker-result-binding.v1"
)
_PROCESS_RESULT_BINDING_SCHEMA = (
    "governed-execution.nwp-rw0-c1-wire-process-result-classification-binding.v1"
)
_SECTION41_MEMBER_SCHEMA = (
    "governed-execution.nwp-rw0-c1-section41-post-execution-proposal-family-member.v1"
)

_OPERATION_TIME_RELATION_SCHEMAS = frozenset(
    {
        "governed-execution.nwp-rw0-c1-authority-verification-observation-relation.v1",
        "governed-execution.nwp-rw0-c1-subordinate-narrowing-relation.v1",
        "governed-execution.nwp-rw0-c1-custody-binding-relation.v1",
        "governed-execution.nwp-rw0-c1-retrieval-event-sequence-relation.v1",
    }
)
_SUBJECT_TIME_HOST_RELATION_SCHEMA = (
    "governed-execution.nwp-rw0-c1-host-qualification-relation.v1"
)
_SUBJECT_TIME_CAPABILITY_RELATION_SCHEMA = (
    "governed-execution.nwp-rw0-c1-worker-mechanism-capability-qualification-relation.v1"
)
_NON_TEMPORAL_RELATION_SCHEMAS = frozenset(
    {
        "governed-execution.nwp-rw0-c1-capability-observation-declaration-binding-relation.v1",
        "governed-execution.nwp-rw0-c1-wire-exact-current-cancellation-request-relation.v1",
        "governed-execution.nwp-rw0-c1-wire-exact-current-process-observation-relation.v1",
        "governed-execution.nwp-rw0-c1-c2a-worker-observation-relation.v1",
        "governed-execution.nwp-rw0-c1-wire-exact-current-cancellation-response-relation.v1",
        "governed-execution.nwp-rw0-c1-wire-worker-result-relation.v1",
        "governed-execution.nwp-rw0-c1-wire-process-result-classifier-relation.v1",
        "governed-execution.nwp-rw0-c1-section41-post-execution-proposal-family-relation.v1",
    }
)


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeError):
        raise RW0C1PreflightError("invalid_value") from None


def _digest(domain: str, value: object) -> str:
    if type(domain) is not str or not domain:
        raise RW0C1PreflightError("invalid_value") from None
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + _canonical_bytes(value)).hexdigest()


def _safe_ref(value: object) -> str:
    if (
        type(value) is not str
        or not 1 <= len(value) <= 96
        or _SAFE_REF_PATTERN.fullmatch(value) is None
        or value.lower().startswith(_RESERVED_SAFE_REF_PREFIXES)
    ):
        raise RW0C1PreflightError("invalid_value") from None
    return value


def _role(value: object) -> str:
    if (
        type(value) is not str
        or re.fullmatch(r"[a-z][a-z0-9_.:-]{0,95}", value) is None
    ):
        raise RW0C1PreflightError("invalid_value") from None
    return value


def _sha256(value: object) -> str:
    if type(value) is not str or _DIGEST_PATTERN.fullmatch(value) is None:
        raise RW0C1PreflightError("invalid_value") from None
    return value


def _timestamp(value: object) -> str:
    try:
        if (
            type(value) is not str
            or len(value) != 20
            or value[4] != "-"
            or value[7] != "-"
            or value[10] != "T"
            or value[13] != ":"
            or value[16] != ":"
            or value[19] != "Z"
            or not (
                value[0:4]
                + value[5:7]
                + value[8:10]
                + value[11:13]
                + value[14:16]
                + value[17:19]
            ).isdigit()
        ):
            raise ValueError
        parsed = datetime.datetime(
            int(value[0:4]),
            int(value[5:7]),
            int(value[8:10]),
            int(value[11:13]),
            int(value[14:16]),
            int(value[17:19]),
            tzinfo=datetime.timezone.utc,
        )
        rendered = (
            f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}T"
            f"{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}Z"
        )
        if rendered != value:
            raise ValueError
    except (TypeError, ValueError, OverflowError):
        raise RW0C1PreflightError("invalid_value") from None
    return value


def _nonnegative(value: object) -> int:
    if type(value) is not int or not 0 <= value <= _MAX_INT:
        raise RW0C1PreflightError("invalid_value") from None
    return value


def _tuple(value: object, *, maximum: int) -> tuple[object, ...]:
    if type(value) is not tuple or len(value) > maximum:
        raise RW0C1PreflightError("invalid_value") from None
    return value


class RW0C1PreflightError(ValueError):
    """Content-free private command/value preflight failure."""

    __slots__ = ("reason",)

    def __init__(self, reason: str) -> None:
        if reason not in {"invalid_command", "invalid_value", "invalid_recovery_probe"}:
            reason = "invalid_value"
        object.__setattr__(self, "reason", reason)
        ValueError.__init__(self, reason)

    def __repr__(self) -> str:
        return "<RW0C1PreflightError>"


class _PrivateValue:
    __slots__ = ()

    def __repr__(self) -> str:
        return f"<{type(self).__name__}>"

    def __copy__(self) -> typing.NoReturn:
        raise TypeError("copy disabled") from None

    def __deepcopy__(self, memo: object) -> typing.NoReturn:
        raise TypeError("copy disabled") from None

    def __reduce__(self) -> typing.NoReturn:
        raise TypeError("pickling disabled") from None

    def __reduce_ex__(self, protocol: int) -> typing.NoReturn:
        raise TypeError("pickling disabled") from None


class RW0C1ConflictReasonV1(str, Enum):
    STALE_WRITER_TOKEN = "stale_writer_token"
    MUTATION_REF_REUSE = "mutation_ref_reuse"
    PHASE_IDENTITY_COLLISION = "phase_identity_collision"
    K8_COLLISION = "k8_collision"
    CURRENT_STATE_CONFLICT = "current_state_conflict"
    MEMBER_IDENTITY_COLLISION = "member_identity_collision"
    MEMBER_ALREADY_ADMITTED = "member_already_admitted"
    MISSING_PREREQUISITE_MEMBER = "missing_prerequisite_member"
    RELATION_FAILURE = "relation_failure"
    RELATION_IDENTITY_COLLISION = "relation_identity_collision"
    OWNER_ROW_MISSING = "owner_row_missing"


class RW0C1RecoveryDispositionV1(str, Enum):
    COMMITTED_EXACT = "committed_exact"
    DEFINITELY_NOT_COMMITTED = "definitely_not_committed"
    UNRESOLVED = "unresolved"


class RW0C1EvidenceKindV1(str, Enum):
    AUTHORITY_VERIFICATION_OBSERVATION = "authority_verification_observation"
    SUBORDINATE_AUTHORIZATION_PROPOSAL = "subordinate_authorization_proposal"
    CUSTODY_AVAILABILITY_OBSERVATION = "custody_availability_observation"
    RETRIEVAL_CAPABILITY_EVENT_OBSERVATION = "retrieval_capability_event_observation"
    REMOTE_HOST_READINESS_OBSERVATION = "remote_host_readiness_observation"
    EFFECT_HOST_QUALIFICATION = "effect_host_qualification"
    WORKER_MECHANISM_CAPABILITY_DECLARATION = "worker_mechanism_capability_declaration"
    WORKER_MECHANISM_CAPABILITY_OBSERVATION = "worker_mechanism_capability_observation"
    WORKER_MECHANISM_CAPABILITY_QUALIFICATION = "worker_mechanism_capability_qualification"
    WIRE_CANCELLATION_REQUEST_OBSERVATION = "wire_cancellation_request_observation"
    WIRE_PROCESS_OBSERVATION = "wire_process_observation"
    C2A_WORKER_OBSERVATION = "c2a_worker_observation"
    WIRE_WORKER_RESULT_BINDING = "wire_worker_result_binding"
    WIRE_PROCESS_RESULT_CLASSIFICATION_BINDING = (
        "wire_process_result_classification_binding"
    )
    SECTION41_POST_EXECUTION_PROPOSAL_FAMILY_MEMBER = (
        "section41_post_execution_proposal_family_member"
    )


_KIND_BY_RANK = tuple(RW0C1EvidenceKindV1)
RW0_C1_KIND_RANKS: tuple[tuple[int, str], ...] = tuple(
    (rank, member.value) for rank, member in enumerate(_KIND_BY_RANK, 1)
)


@dataclass(frozen=True, slots=True, repr=False)
class _KindSpec:
    rank: int
    kind: RW0C1EvidenceKindV1
    value_type: type[object]
    schema_id: str
    ref_field: str
    digest_field: str
    scope_class: str


_OWNER_KIND_SPECS = (
    _KindSpec(1, _KIND_BY_RANK[0], RW0AuthorityVerificationObservationV1,
              "governed-execution.nwp-rw0-authority-verification-observation.v1",
              "observation_ref", "observation_digest", "phase_bound"),
    _KindSpec(2, _KIND_BY_RANK[1], RW0SubordinateAuthorizationProposalV1,
              "governed-execution.nwp-rw0-subordinate-authorization-proposal.v1",
              "proposal_ref", "proposal_digest", "phase_bound"),
    _KindSpec(3, _KIND_BY_RANK[2], RW0CustodyAvailabilityObservationV1,
              "governed-execution.nwp-rw0-custody-availability-observation.v1",
              "observation_ref", "observation_digest", "phase_bound"),
    _KindSpec(4, _KIND_BY_RANK[3], RW0RetrievalCapabilityEventObservationV1,
              "governed-execution.nwp-rw0-retrieval-capability-event-observation.v1",
              "event_ref", "event_digest", "phase_bound"),
    _KindSpec(5, _KIND_BY_RANK[4], RW0RemoteHostReadinessObservationV1,
              "governed-execution.nwp-rw0-remote-host-readiness-observation.v1",
              "observation_ref", "observation_digest", "global_reusable"),
    _KindSpec(6, _KIND_BY_RANK[5], RW0EffectHostQualificationV1,
              "governed-execution.nwp-rw0-effect-host-qualification.v1",
              "qualification_ref", "qualification_digest", "phase_bound"),
    _KindSpec(7, _KIND_BY_RANK[6], RW0WorkerMechanismCapabilityDeclarationV1,
              "governed-execution.nwp-rw0-worker-mechanism-capability-declaration.v1",
              "capability_declaration_ref", "capability_declaration_digest",
              "global_reusable"),
    _KindSpec(8, _KIND_BY_RANK[7], RW0WorkerMechanismCapabilityObservationV1,
              "governed-execution.nwp-rw0-worker-mechanism-capability-observation.v1",
              "capability_observation_ref", "capability_observation_digest",
              "global_reusable"),
    _KindSpec(9, _KIND_BY_RANK[8], RW0WorkerMechanismCapabilityQualificationV1,
              "governed-execution.nwp-rw0-worker-mechanism-capability-qualification.v1",
              "capability_qualification_ref", "capability_qualification_digest",
              "phase_bound"),
    _KindSpec(10, _KIND_BY_RANK[9], RW0WireCancellationRequestObservationV1,
              "governed-execution.nwp-rw0-wire-cancellation-request-observation.v1",
              "request_observation_ref", "request_observation_digest", "k8_bound"),
    _KindSpec(11, _KIND_BY_RANK[10], RW0WireProcessObservationV1,
              "governed-execution.nwp-rw0-wire-process-observation.v1",
              "process_observation_ref", "process_observation_digest", "k8_bound"),
    _KindSpec(12, _KIND_BY_RANK[11], WorkerObservationV1,
              "governed-execution.nwp-worker-observation.v1",
              "observation_ref", "observation_digest", "k8_bound"),
)


def _owner_mapping(value: object, spec: _KindSpec) -> dict[str, object]:
    if type(value) is not spec.value_type:
        raise RW0C1PreflightError("invalid_value") from None
    mapping_method = getattr(value, "to_mapping", None)
    if callable(mapping_method):
        mapping = mapping_method()
    else:
        mapping = value.identity_mapping()
        mapping[spec.digest_field] = getattr(value, spec.digest_field)
    if type(mapping) is not dict or mapping.get("schema_id") != spec.schema_id:
        raise RW0C1PreflightError("invalid_value") from None
    if getattr(value, spec.ref_field) != mapping.get(spec.ref_field):
        raise RW0C1PreflightError("invalid_value") from None
    if getattr(value, spec.digest_field) != mapping.get(spec.digest_field):
        raise RW0C1PreflightError("invalid_value") from None
    return typing.cast(dict[str, object], mapping)


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1MemberLocatorV1(_PrivateValue):
    role: str
    kind_rank: int
    membership_ref: str
    membership_digest: str
    value_ref: str
    value_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _role(self.role))
        if type(self.kind_rank) is not int or not 1 <= self.kind_rank <= 15:
            raise RW0C1PreflightError("invalid_value") from None
        object.__setattr__(self, "membership_ref", _safe_ref(self.membership_ref))
        object.__setattr__(self, "membership_digest", _sha256(self.membership_digest))
        object.__setattr__(self, "value_ref", _safe_ref(self.value_ref))
        object.__setattr__(self, "value_digest", _sha256(self.value_digest))

    def to_mapping(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in self.__slots__}


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1OwnerRowLocatorV1(_PrivateValue):
    role: str
    owner_role: str
    row_ref: str
    row_digest: str
    revision: int | None = None
    subrole: str | None = None
    ordinal: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _role(self.role))
        object.__setattr__(self, "owner_role", _role(self.owner_role))
        if self.owner_role not in {
            "development_work_spec_binding",
            "development_attempt_fence",
            "development_effect_fence",
            "development_author_command",
            "development_delivery_attempt",
            "development_model_source_invocation",
            "development_pre_execution_planning_context",
            "development_private_proposal_artifact_binding",
            "development_model_proposal",
            "development_pre_execution_plan_projection",
            "development_model_proposal_evidence_binding",
            "development_pre_execution_disposition",
            "development_cognitive_mutation_receipt",
        }:
            raise RW0C1PreflightError("invalid_value") from None
        object.__setattr__(self, "row_ref", _safe_ref(self.row_ref))
        object.__setattr__(self, "row_digest", _sha256(self.row_digest))
        if self.revision is not None:
            object.__setattr__(self, "revision", _nonnegative(self.revision))
        if self.subrole is not None:
            object.__setattr__(self, "subrole", _role(self.subrole))
        if self.ordinal is not None:
            object.__setattr__(self, "ordinal", _nonnegative(self.ordinal))
        if self.owner_role == "development_model_proposal_evidence_binding":
            if (
                self.revision is not None
                or self.ordinal != 0
                or self.subrole not in {
                    "standing_policy",
                    "risk_lane",
                    "repository_binding",
                    "base_binding",
                    "authorized_path_scope",
                    "cost_ceiling",
                    "token_ceiling",
                    "time_ceiling",
                    "delivery_ceiling",
                    "effect_ceiling",
                    "authority_currentness_attestation",
                    "authority_selection_observation",
                    "global_stop",
                    "validation_requirement",
                    "review_requirement",
                    "qualified_remote_host_readiness",
                    "candidate_capsule",
                    "worker_result",
                    "validation_result",
                    "independent_review",
                }
            ):
                raise RW0C1PreflightError("invalid_value") from None
        elif any(
            member is not None
            for member in (self.revision, self.subrole, self.ordinal)
        ):
            raise RW0C1PreflightError("invalid_value") from None

    def to_mapping(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in self.__slots__}


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1AdmissionSnapshotBindingV1(_PrivateValue):
    """Privacy-safe immutable admission snapshot reconstructed from a phase row."""

    role: str
    snapshot_kind: str
    phase_basis_ref: str
    phase_basis_digest: str
    identity_fields: tuple[tuple[str, object], ...]
    operand_schema_id: str = field(init=False)
    operand_ref: str = field(init=False)
    operand_digest: str = field(init=False)
    operand_scope_digest: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _role(self.role))
        if self.snapshot_kind not in _SNAPSHOT_SCHEMAS:
            raise RW0C1PreflightError("invalid_value") from None
        object.__setattr__(self, "phase_basis_ref", _safe_ref(self.phase_basis_ref))
        phase_digest = _sha256(self.phase_basis_digest)
        object.__setattr__(self, "phase_basis_digest", phase_digest)
        if type(self.identity_fields) is not tuple or not self.identity_fields:
            raise RW0C1PreflightError("invalid_value") from None
        names: list[str] = []
        identity: dict[str, object] = {}
        for item in self.identity_fields:
            if (
                type(item) is not tuple
                or len(item) != 2
                or type(item[0]) is not str
                or not item[0]
                or type(item[1]) not in {str, int, type(None)}
            ):
                raise RW0C1PreflightError("invalid_value") from None
            names.append(item[0])
            identity[item[0]] = item[1]
        if len(names) != len(set(names)) or "snapshot_digest" in identity:
            raise RW0C1PreflightError("invalid_value") from None
        schema_id, ref_component = _SNAPSHOT_SCHEMAS[self.snapshot_kind]
        snapshot_ref = f"rw0-c1-snapshot.{ref_component}.{phase_digest}"
        prefix = {
            "schema_id": schema_id,
            "snapshot_ref": snapshot_ref,
            "phase_basis_ref": self.phase_basis_ref,
            "phase_basis_digest": phase_digest,
        }
        overlap = set(prefix).intersection(identity)
        if overlap:
            raise RW0C1PreflightError("invalid_value") from None
        digest = _digest(schema_id + ".identity", {**prefix, **identity})
        object.__setattr__(self, "operand_schema_id", schema_id)
        object.__setattr__(self, "operand_ref", snapshot_ref)
        object.__setattr__(self, "operand_digest", digest)
        object.__setattr__(self, "operand_scope_digest", phase_digest)

    def safe_mapping(self) -> dict[str, object]:
        return {
            "role": self.role,
            "snapshot_kind": self.snapshot_kind,
            "operand_schema_id": self.operand_schema_id,
            "operand_ref": self.operand_ref,
            "operand_digest": self.operand_digest,
            "operand_scope_digest": self.operand_scope_digest,
        }


_TRANSIENT_SCHEMAS = {
    "work_spec": "governed-execution.nwp-rw0-c1-transient-work-spec-binding.v1",
    "candidate_capsule_manifest": "governed-execution.nwp-candidate-capsule-manifest.v1",
    "before_blob_set": "governed-execution.nwp-rw0-c1-transient-before-blob-set-binding.v1",
    "after_blob_set": "governed-execution.nwp-rw0-c1-transient-after-blob-set-binding.v1",
    "wire_protocol_error": "governed-execution.nwp-rw0-c1-transient-wire-protocol-error-binding.v1",
}


_WIRE_ERROR_REASONS = (
    "invalid_outer_type", "short_header", "bad_magic", "unsupported_version",
    "unsupported_kind", "declared_length_over_cap", "truncated_payload",
    "trailing_data", "invalid_utf8", "bom_forbidden", "json_token_invalid",
    "duplicate_key", "invalid_root_or_scalar", "unknown_field", "missing_field",
    "nested_record_invalid", "noncanonical_payload", "relation_mismatch",
    "work_limit_exceeded", "invalid_field_type", "invalid_field_value",
    "invalid_length_or_cardinality", "digest_mismatch", "privacy_forbidden_material",
)


def _blob_set_digest(kind: str, scope_digest: str, blobs: dict[str, bytes]) -> str:
    if type(blobs) is not dict or len(blobs) != 3:
        raise RW0C1PreflightError("invalid_value") from None
    encoded: list[tuple[bytes, bytes]] = []
    for key, blob in blobs.items():
        if type(key) is not str or type(blob) is not bytes:
            raise RW0C1PreflightError("invalid_value") from None
        key_bytes = key.encode("utf-8", errors="strict")
        encoded.append((key_bytes, blob))
    encoded.sort(key=lambda item: item[0])
    payload = bytearray(scope_digest.encode("utf-8") + b"\x00" + struct.pack(">I", len(encoded)))
    for key_bytes, blob in encoded:
        payload.extend(struct.pack(">I", len(key_bytes)))
        payload.extend(key_bytes)
        payload.extend(struct.pack(">Q", len(blob)))
        payload.extend(blob)
    domain = _TRANSIENT_SCHEMAS[kind] + ".identity"
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + bytes(payload)).hexdigest()


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1TransientPrivateBindingV1(_PrivateValue):
    role: str
    binding_kind: str
    operand_schema_id: str
    operand_ref: str
    operand_digest: str
    operand_scope_digest: str
    error_reason: str | None = None
    _private_value: object = field(default=None, compare=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", _role(self.role))
        if self.binding_kind not in _TRANSIENT_SCHEMAS:
            raise RW0C1PreflightError("invalid_value") from None
        if self.operand_schema_id != _TRANSIENT_SCHEMAS[self.binding_kind]:
            raise RW0C1PreflightError("invalid_value") from None
        object.__setattr__(self, "operand_ref", _safe_ref(self.operand_ref))
        object.__setattr__(self, "operand_digest", _sha256(self.operand_digest))
        object.__setattr__(self, "operand_scope_digest", _sha256(self.operand_scope_digest))
        if self.binding_kind == "wire_protocol_error":
            if type(self._private_value) is not RW0WireProtocolError:
                raise RW0C1PreflightError("invalid_value") from None
            if self.error_reason not in _WIRE_ERROR_REASONS:
                raise RW0C1PreflightError("invalid_value") from None
            if self._private_value.reason != self.error_reason:
                raise RW0C1PreflightError("invalid_value") from None
        elif self.error_reason is not None:
            raise RW0C1PreflightError("invalid_value") from None

    @classmethod
    def work_spec(
        cls, *, role: str, value: WorkSpecV1, safe_projection_digest: str,
    ) -> "RW0C1TransientPrivateBindingV1":
        if type(value) is not WorkSpecV1:
            raise RW0C1PreflightError("invalid_value") from None
        return cls(role, "work_spec", _TRANSIENT_SCHEMAS["work_spec"],
                   value.work_spec_ref, value.work_spec_digest,
                   safe_projection_digest, None, value)

    @classmethod
    def candidate_capsule_manifest(
        cls, *, role: str, value: CandidateCapsuleManifestV1,
    ) -> "RW0C1TransientPrivateBindingV1":
        if type(value) is not CandidateCapsuleManifestV1:
            raise RW0C1PreflightError("invalid_value") from None
        return cls(role, "candidate_capsule_manifest",
                   _TRANSIENT_SCHEMAS["candidate_capsule_manifest"],
                   value.capsule_manifest_ref, value.portable_capsule_digest,
                   value.authorized_path_scope_digest, None, value)

    @classmethod
    def blob_set(
        cls, *, role: str, binding_kind: str, blobs: dict[str, bytes],
        authorized_path_scope_digest: str,
    ) -> "RW0C1TransientPrivateBindingV1":
        if binding_kind not in {"before_blob_set", "after_blob_set"}:
            raise RW0C1PreflightError("invalid_value") from None
        scope = _sha256(authorized_path_scope_digest)
        digest = _blob_set_digest(binding_kind, scope, blobs)
        prefix = "before" if binding_kind == "before_blob_set" else "after"
        return cls(role, binding_kind, _TRANSIENT_SCHEMAS[binding_kind],
                   f"rw0-c1-{prefix}-blob-set.{digest}", digest, scope, None, blobs)

    @classmethod
    def wire_protocol_error(
        cls, *, role: str, value: RW0WireProtocolError,
    ) -> "RW0C1TransientPrivateBindingV1":
        if type(value) is not RW0WireProtocolError or value.reason not in _WIRE_ERROR_REASONS:
            raise RW0C1PreflightError("invalid_value") from None
        payload = {
            "schema_id": _TRANSIENT_SCHEMAS["wire_protocol_error"],
            "wire_profile_ref": _NWPF_REF,
            "wire_profile_digest": _NWPF_DIGEST,
            "reason": value.reason,
        }
        digest = _digest(_TRANSIENT_SCHEMAS["wire_protocol_error"] + ".identity", payload)
        return cls(role, "wire_protocol_error", _TRANSIENT_SCHEMAS["wire_protocol_error"],
                   f"rw0-c1-wire-error.{digest}", digest, _NWPF_DIGEST,
                   value.reason, value)

    def safe_mapping(self) -> dict[str, object]:
        return {
            "role": self.role,
            "binding_kind": self.binding_kind,
            "operand_schema_id": self.operand_schema_id,
            "operand_ref": self.operand_ref,
            "operand_digest": self.operand_digest,
            "operand_scope_digest": self.operand_scope_digest,
            "error_reason": self.error_reason,
        }

    def command_mapping(self) -> dict[str, object]:
        result = self.safe_mapping()
        if self.binding_kind in {"work_spec", "candidate_capsule_manifest"}:
            result["private_identity"] = self._private_value.to_mapping()
        return result


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1WireWorkerResultBindingV1(_PrivateValue):
    value_ref: str
    phase_basis_ref: str
    phase_basis_digest: str
    program_ref: str
    semantic_attempt_ref: str
    candidate_ref: str
    effect_intent_ref: str
    author_command_ref: str
    attempt_fence_ref: str
    effect_fence_ref: str
    delivery_attempt_ref: str
    observation_memberships: tuple[RW0C1MemberLocatorV1, ...]
    value_digest: str = ""
    schema_id: str = field(default=_WORKER_RESULT_BINDING_SCHEMA, init=False)

    def __post_init__(self) -> None:
        for name in (
            "value_ref", "phase_basis_ref", "program_ref", "semantic_attempt_ref",
            "candidate_ref", "effect_intent_ref", "author_command_ref",
            "attempt_fence_ref", "effect_fence_ref", "delivery_attempt_ref",
        ):
            object.__setattr__(self, name, _safe_ref(getattr(self, name)))
        object.__setattr__(self, "phase_basis_digest", _sha256(self.phase_basis_digest))
        members = _tuple(self.observation_memberships, maximum=3)
        if len(members) not in {2, 3} or any(type(item) is not RW0C1MemberLocatorV1 for item in members):
            raise RW0C1PreflightError("invalid_value") from None
        if any(item.kind_rank != 12 for item in typing.cast(tuple[RW0C1MemberLocatorV1, ...], members)):
            raise RW0C1PreflightError("invalid_value") from None
        if tuple(item.role for item in self.observation_memberships) != tuple(
            f"worker_observation:{ordinal:03d}"
            for ordinal in range(len(self.observation_memberships))
        ):
            raise RW0C1PreflightError("invalid_value") from None
        computed = _digest(self.schema_id + ".identity", self.identity_mapping())
        if self.value_digest:
            if _sha256(self.value_digest) != computed:
                raise RW0C1PreflightError("invalid_value") from None
        else:
            object.__setattr__(self, "value_digest", computed)

    def identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "value_ref": self.value_ref,
            "phase_basis_ref": self.phase_basis_ref,
            "phase_basis_digest": self.phase_basis_digest,
            "program_ref": self.program_ref,
            "semantic_attempt_ref": self.semantic_attempt_ref,
            "candidate_ref": self.candidate_ref,
            "effect_intent_ref": self.effect_intent_ref,
            "author_command_ref": self.author_command_ref,
            "attempt_fence_ref": self.attempt_fence_ref,
            "effect_fence_ref": self.effect_fence_ref,
            "delivery_attempt_ref": self.delivery_attempt_ref,
            "wire_profile_ref": _NWPF_REF,
            "wire_profile_digest": _NWPF_DIGEST,
            "observation_memberships": [item.to_mapping() for item in self.observation_memberships],
        }

    def to_mapping(self) -> dict[str, object]:
        result = self.identity_mapping()
        result["value_digest"] = self.value_digest
        return result


_PROCESS_CLASSIFICATION_REASONS = {
    "usable": {"usable"},
    "invalid": {"invalid_input", "unrelated_fact", "duplicate_fact",
                "conflicting_fact", "cancellation_graph_mismatch"},
    "unusable": {"resource_limit_exceeded", "deadline_elapsed", "signal_delivered",
                  "cancellation_request_pending", "cancellation_acknowledged",
                  "cancellation_rejected", "process_result_contradiction",
                  "process_failed", "result_missing", "result_invalid",
                  "process_evidence_incomplete"},
}


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1WireProcessResultClassificationBindingV1(_PrivateValue):
    value_ref: str
    phase_basis_ref: str
    phase_basis_digest: str
    program_ref: str
    semantic_attempt_ref: str
    candidate_ref: str
    effect_intent_ref: str
    author_command_ref: str
    attempt_fence_ref: str
    effect_fence_ref: str
    delivery_attempt_ref: str
    result_state: str
    result_membership: RW0C1MemberLocatorV1 | None
    result_failure_reason: str | None
    adapter_observations: tuple[RW0C1MemberLocatorV1, ...]
    request_membership: RW0C1MemberLocatorV1 | None
    process_observations: tuple[RW0C1MemberLocatorV1, ...]
    classification: str
    reason: str
    value_digest: str = ""
    schema_id: str = field(default=_PROCESS_RESULT_BINDING_SCHEMA, init=False)

    def __post_init__(self) -> None:
        for name in (
            "value_ref", "phase_basis_ref", "program_ref", "semantic_attempt_ref",
            "candidate_ref", "effect_intent_ref", "author_command_ref",
            "attempt_fence_ref", "effect_fence_ref", "delivery_attempt_ref",
        ):
            object.__setattr__(self, name, _safe_ref(getattr(self, name)))
        object.__setattr__(self, "phase_basis_digest", _sha256(self.phase_basis_digest))
        if self.result_state not in {"present", "finite_failure", "absent"}:
            raise RW0C1PreflightError("invalid_value") from None
        if self.result_state == "present":
            valid_result = type(self.result_membership) is RW0C1MemberLocatorV1 and self.result_failure_reason is None
            if valid_result and self.result_membership.kind_rank != 13:
                valid_result = False
        elif self.result_state == "finite_failure":
            valid_result = self.result_membership is None and self.result_failure_reason in _WIRE_ERROR_REASONS
        else:
            valid_result = self.result_membership is None and self.result_failure_reason is None
        if not valid_result:
            raise RW0C1PreflightError("invalid_value") from None
        adapters = _tuple(self.adapter_observations, maximum=4)
        processes = _tuple(self.process_observations, maximum=2)
        if any(type(item) is not RW0C1MemberLocatorV1 or item.kind_rank != 12 for item in adapters):
            raise RW0C1PreflightError("invalid_value") from None
        if any(type(item) is not RW0C1MemberLocatorV1 or item.kind_rank != 11 for item in processes):
            raise RW0C1PreflightError("invalid_value") from None
        if tuple(item.role for item in self.adapter_observations) != tuple(
            f"adapter_observation:{ordinal:03d}"
            for ordinal in range(len(self.adapter_observations))
        ) or tuple(item.role for item in self.process_observations) != tuple(
            f"process_observation:{ordinal:03d}"
            for ordinal in range(len(self.process_observations))
        ):
            raise RW0C1PreflightError("invalid_value") from None
        if self.request_membership is not None and (
            type(self.request_membership) is not RW0C1MemberLocatorV1
            or self.request_membership.kind_rank != 10
            or self.request_membership.role != "cancellation_request"
        ):
            raise RW0C1PreflightError("invalid_value") from None
        if self.result_membership is not None and (
            self.result_membership.role != "worker_result_binding"
        ):
            raise RW0C1PreflightError("invalid_value") from None
        if self.classification not in _PROCESS_CLASSIFICATION_REASONS or self.reason not in _PROCESS_CLASSIFICATION_REASONS[self.classification]:
            raise RW0C1PreflightError("invalid_value") from None
        computed = _digest(self.schema_id + ".identity", self.identity_mapping())
        if self.value_digest:
            if _sha256(self.value_digest) != computed:
                raise RW0C1PreflightError("invalid_value") from None
        else:
            object.__setattr__(self, "value_digest", computed)

    def identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "value_ref": self.value_ref,
            "phase_basis_ref": self.phase_basis_ref,
            "phase_basis_digest": self.phase_basis_digest,
            "program_ref": self.program_ref,
            "semantic_attempt_ref": self.semantic_attempt_ref,
            "candidate_ref": self.candidate_ref,
            "effect_intent_ref": self.effect_intent_ref,
            "author_command_ref": self.author_command_ref,
            "attempt_fence_ref": self.attempt_fence_ref,
            "effect_fence_ref": self.effect_fence_ref,
            "delivery_attempt_ref": self.delivery_attempt_ref,
            "wire_profile_ref": _NWPF_REF,
            "wire_profile_digest": _NWPF_DIGEST,
            "result_state": self.result_state,
            "result_membership": None if self.result_membership is None else self.result_membership.to_mapping(),
            "result_failure_reason": self.result_failure_reason,
            "adapter_observations": [item.to_mapping() for item in self.adapter_observations],
            "request_membership": None if self.request_membership is None else self.request_membership.to_mapping(),
            "process_observations": [item.to_mapping() for item in self.process_observations],
            "classification": self.classification,
            "reason": self.reason,
        }

    def to_mapping(self) -> dict[str, object]:
        result = self.identity_mapping()
        result["value_digest"] = self.value_digest
        return result


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1Section41PostExecutionProposalFamilyMemberV1(_PrivateValue):
    value_ref: str
    phase_basis_ref: str
    phase_basis_digest: str
    source_invocation_ref: str
    source_invocation_digest: str
    artifact_ref: str
    artifact_digest: str
    artifact_binding_digest: str
    proposal_ref: str
    proposal_digest: str
    model_contract_ref: str
    model_contract_digest: str
    model_configuration_ref: str
    model_configuration_digest: str
    context_schema_id: str
    context_ref: str
    context_digest: str
    safe_projection_schema_id: str
    safe_projection_digest: str
    evidence_set_ref: str
    evidence_set_digest: str
    evidence_binding_count: int
    recommendation: str
    reason_code: str
    proposal_created_at: str
    owner_family_graph_digest: str
    value_digest: str = ""
    schema_id: str = field(default=_SECTION41_MEMBER_SCHEMA, init=False)

    def __post_init__(self) -> None:
        for name in (
            "value_ref", "phase_basis_ref", "source_invocation_ref", "artifact_ref",
            "proposal_ref", "model_contract_ref", "model_configuration_ref",
            "context_ref", "evidence_set_ref",
        ):
            object.__setattr__(self, name, _safe_ref(getattr(self, name)))
        for name in (
            "phase_basis_digest", "source_invocation_digest", "artifact_digest",
            "artifact_binding_digest", "proposal_digest", "model_contract_digest",
            "model_configuration_digest", "context_digest", "safe_projection_digest",
            "evidence_set_digest", "owner_family_graph_digest",
        ):
            object.__setattr__(self, name, _sha256(getattr(self, name)))
        if self.context_schema_id != (
            "governed-execution.nwp-post-execution-semantic-review-context.v1"
        ) or self.safe_projection_schema_id != (
            "governed-execution.nwp-post-execution-semantic-review-safe-projection.v1"
        ):
            raise RW0C1PreflightError("invalid_value") from None
        if self.evidence_binding_count not in {0, 9}:
            raise RW0C1PreflightError("invalid_value") from None
        if self.recommendation not in {
            "accept_candidate",
            "repair_candidate",
            "replan",
            "terminal_reject",
            "block",
        }:
            raise RW0C1PreflightError("invalid_value") from None
        object.__setattr__(self, "reason_code", _role(self.reason_code))
        object.__setattr__(self, "proposal_created_at", _timestamp(self.proposal_created_at))
        computed = _digest(self.schema_id + ".identity", self.identity_mapping())
        if self.value_digest:
            if _sha256(self.value_digest) != computed:
                raise RW0C1PreflightError("invalid_value") from None
        else:
            object.__setattr__(self, "value_digest", computed)

    def identity_mapping(self) -> dict[str, object]:
        return {
            name: getattr(self, name)
            for name in (
                "schema_id", "value_ref", "phase_basis_ref", "phase_basis_digest",
                "source_invocation_ref", "source_invocation_digest", "artifact_ref",
                "artifact_digest", "artifact_binding_digest", "proposal_ref",
                "proposal_digest", "model_contract_ref", "model_contract_digest",
                "model_configuration_ref", "model_configuration_digest",
                "context_schema_id", "context_ref", "context_digest",
                "safe_projection_schema_id", "safe_projection_digest",
                "evidence_set_ref", "evidence_set_digest", "evidence_binding_count",
                "recommendation", "reason_code", "proposal_created_at",
                "owner_family_graph_digest",
            )
        }

    def to_mapping(self) -> dict[str, object]:
        result = self.identity_mapping()
        result["value_digest"] = self.value_digest
        return result


_C1_KIND_SPECS = _OWNER_KIND_SPECS + (
    _KindSpec(13, _KIND_BY_RANK[12], RW0C1WireWorkerResultBindingV1,
              _WORKER_RESULT_BINDING_SCHEMA, "value_ref", "value_digest", "k8_bound"),
    _KindSpec(14, _KIND_BY_RANK[13], RW0C1WireProcessResultClassificationBindingV1,
              _PROCESS_RESULT_BINDING_SCHEMA, "value_ref", "value_digest", "k8_bound"),
    _KindSpec(15, _KIND_BY_RANK[14], RW0C1Section41PostExecutionProposalFamilyMemberV1,
              _SECTION41_MEMBER_SCHEMA, "value_ref", "value_digest",
              "existing_owner_row_bound"),
)
RW0_C1_KIND_SPECS: tuple[_KindSpec, ...] = _C1_KIND_SPECS


def evidence_identity(value: object, kind_rank: int) -> tuple[str, str, str, str, dict[str, object]]:
    if type(kind_rank) is not int or not 1 <= kind_rank <= 15:
        raise RW0C1PreflightError("invalid_value") from None
    spec = _C1_KIND_SPECS[kind_rank - 1]
    if kind_rank <= 12:
        mapping = _owner_mapping(value, spec)
    else:
        if type(value) is not spec.value_type:
            raise RW0C1PreflightError("invalid_value") from None
        mapping = value.to_mapping()
    ref = _safe_ref(getattr(value, spec.ref_field))
    digest = _sha256(getattr(value, spec.digest_field))
    return ref, digest, spec.schema_id, spec.scope_class, mapping


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1EstablishPhaseCommandV1(_PrivateValue):
    mutation_ref: str
    phase_basis: RW0PhaseEntryBasisV1 = field(repr=False, compare=False)
    work_spec: WorkSpecV1 = field(repr=False, compare=False)
    work_spec_safe_projection_digest: str
    expected_program_head_revision: int
    expected_program_head_digest: str
    expected_work_item_head_revision: int
    expected_work_item_head_digest: str
    command_digest: str = ""
    schema_id: str = field(default=_ESTABLISH_COMMAND_SCHEMA, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "mutation_ref", _safe_ref(self.mutation_ref))
        if type(self.phase_basis) is not RW0PhaseEntryBasisV1 or type(self.work_spec) is not WorkSpecV1:
            raise RW0C1PreflightError("invalid_command") from None
        object.__setattr__(self, "work_spec_safe_projection_digest", _sha256(self.work_spec_safe_projection_digest))
        object.__setattr__(self, "expected_program_head_revision", _nonnegative(self.expected_program_head_revision))
        object.__setattr__(self, "expected_program_head_digest", _sha256(self.expected_program_head_digest))
        object.__setattr__(self, "expected_work_item_head_revision", _nonnegative(self.expected_work_item_head_revision))
        object.__setattr__(self, "expected_work_item_head_digest", _sha256(self.expected_work_item_head_digest))
        computed = _digest(self.schema_id + ".identity", self.identity_mapping())
        if self.command_digest:
            if _sha256(self.command_digest) != computed:
                raise RW0C1PreflightError("invalid_command") from None
        else:
            object.__setattr__(self, "command_digest", computed)

    def identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "mutation_ref": self.mutation_ref,
            "phase_basis": self.phase_basis.to_mapping(),
            "work_spec": self.work_spec.to_mapping(),
            "work_spec_safe_projection_digest": self.work_spec_safe_projection_digest,
            "expected_program_head_revision": self.expected_program_head_revision,
            "expected_program_head_digest": self.expected_program_head_digest,
            "expected_work_item_head_revision": self.expected_work_item_head_revision,
            "expected_work_item_head_digest": self.expected_work_item_head_digest,
        }


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1AdmitEvidenceCommandV1(_PrivateValue):
    mutation_ref: str
    phase_basis_ref: str
    phase_basis_digest: str
    expected_program_head_revision: int
    expected_program_head_digest: str
    expected_work_item_head_revision: int
    expected_work_item_head_digest: str
    preassigned_membership_ref: str
    kind_rank: int
    evidence_value: object = field(repr=False, compare=False)
    prerequisite_member_locators: tuple[RW0C1MemberLocatorV1, ...] = ()
    owner_row_locators: tuple[RW0C1OwnerRowLocatorV1, ...] = ()
    transient_bindings: tuple[RW0C1TransientPrivateBindingV1, ...] = ()
    command_digest: str = ""
    schema_id: str = field(default=_ADMIT_COMMAND_SCHEMA, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "mutation_ref", _safe_ref(self.mutation_ref))
        object.__setattr__(self, "phase_basis_ref", _safe_ref(self.phase_basis_ref))
        object.__setattr__(self, "phase_basis_digest", _sha256(self.phase_basis_digest))
        object.__setattr__(self, "preassigned_membership_ref", _safe_ref(self.preassigned_membership_ref))
        object.__setattr__(self, "expected_program_head_revision", _nonnegative(self.expected_program_head_revision))
        object.__setattr__(self, "expected_program_head_digest", _sha256(self.expected_program_head_digest))
        object.__setattr__(self, "expected_work_item_head_revision", _nonnegative(self.expected_work_item_head_revision))
        object.__setattr__(self, "expected_work_item_head_digest", _sha256(self.expected_work_item_head_digest))
        evidence_identity(self.evidence_value, self.kind_rank)
        members = _tuple(self.prerequisite_member_locators, maximum=14)
        owners = _tuple(self.owner_row_locators, maximum=14)
        transients = _tuple(self.transient_bindings, maximum=5)
        if any(type(item) is not RW0C1MemberLocatorV1 for item in members):
            raise RW0C1PreflightError("invalid_command") from None
        if any(type(item) is not RW0C1OwnerRowLocatorV1 for item in owners):
            raise RW0C1PreflightError("invalid_command") from None
        if any(type(item) is not RW0C1TransientPrivateBindingV1 for item in transients):
            raise RW0C1PreflightError("invalid_command") from None
        for sequence in (members, owners, transients):
            roles = [getattr(item, "role") for item in sequence]
            if len(roles) != len(set(roles)):
                raise RW0C1PreflightError("invalid_command") from None
        all_roles = tuple(
            getattr(item, "role")
            for sequence in (members, owners, transients)
            for item in sequence
        )
        if (
            len(all_roles) != len(set(all_roles))
            or len(members) + len(owners) + len(transients) > 14
        ):
            raise RW0C1PreflightError("invalid_command") from None
        computed = _digest(self.schema_id + ".identity", self.identity_mapping())
        if self.command_digest:
            if _sha256(self.command_digest) != computed:
                raise RW0C1PreflightError("invalid_command") from None
        else:
            object.__setattr__(self, "command_digest", computed)

    def identity_mapping(self) -> dict[str, object]:
        _ref, _digest_value, _schema, _scope, value_mapping = evidence_identity(
            self.evidence_value, self.kind_rank
        )
        return {
            "schema_id": self.schema_id,
            "mutation_ref": self.mutation_ref,
            "phase_basis_ref": self.phase_basis_ref,
            "phase_basis_digest": self.phase_basis_digest,
            "expected_program_head_revision": self.expected_program_head_revision,
            "expected_program_head_digest": self.expected_program_head_digest,
            "expected_work_item_head_revision": self.expected_work_item_head_revision,
            "expected_work_item_head_digest": self.expected_work_item_head_digest,
            "preassigned_membership_ref": self.preassigned_membership_ref,
            "kind_rank": self.kind_rank,
            "evidence_value": value_mapping,
            "prerequisite_member_locators": [item.to_mapping() for item in self.prerequisite_member_locators],
            "owner_row_locators": [item.to_mapping() for item in self.owner_row_locators],
            "transient_bindings": [item.command_mapping() for item in self.transient_bindings],
        }


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1ConflictV1(_PrivateValue):
    reason: RW0C1ConflictReasonV1

    def __post_init__(self) -> None:
        if type(self.reason) is not RW0C1ConflictReasonV1:
            raise RW0C1PreflightError("invalid_value") from None

    def safe_projection(self) -> dict[str, str]:
        return {"reason": self.reason.value}


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1EstablishPhaseResultV1(_PrivateValue):
    mutation_ref: str
    command_digest: str
    disposition: str
    phase_basis_ref: str
    phase_basis_digest: str
    k8_digest: str
    phase_graph_digest: str
    receipt_digest: str
    committed_at: str
    result_digest: str = ""
    schema_id: str = field(default=_ESTABLISH_RESULT_SCHEMA, init=False)

    def __post_init__(self) -> None:
        for name in ("mutation_ref", "phase_basis_ref"):
            object.__setattr__(self, name, _safe_ref(getattr(self, name)))
        for name in ("command_digest", "phase_basis_digest", "k8_digest", "phase_graph_digest", "receipt_digest"):
            object.__setattr__(self, name, _sha256(getattr(self, name)))
        if self.disposition not in {"fresh_committed", "exact_replay"}:
            raise RW0C1PreflightError("invalid_value") from None
        object.__setattr__(self, "committed_at", _timestamp(self.committed_at))
        computed = _digest(self.schema_id + ".identity", self.identity_mapping())
        if self.result_digest:
            if _sha256(self.result_digest) != computed:
                raise RW0C1PreflightError("invalid_value") from None
        else:
            object.__setattr__(self, "result_digest", computed)

    def identity_mapping(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in (
            "schema_id", "mutation_ref", "command_digest", "disposition",
            "phase_basis_ref", "phase_basis_digest", "k8_digest",
            "phase_graph_digest", "receipt_digest", "committed_at",
        )}

    def safe_projection(self) -> dict[str, object]:
        result = self.identity_mapping()
        result["result_digest"] = self.result_digest
        return result

    def committed_projection_digest(self) -> str:
        return _digest(
            self.schema_id + ".committed-projection",
            {
                "schema_id": self.schema_id,
                "mutation_ref": self.mutation_ref,
                "command_digest": self.command_digest,
                "phase_basis_ref": self.phase_basis_ref,
                "phase_basis_digest": self.phase_basis_digest,
                "k8_digest": self.k8_digest,
                "phase_graph_digest": self.phase_graph_digest,
                "committed_at": self.committed_at,
            },
        )


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1AdmitEvidenceResultV1(_PrivateValue):
    mutation_ref: str
    command_digest: str
    disposition: str
    phase_basis_ref: str
    phase_basis_digest: str
    membership_ref: str
    membership_digest: str
    kind_rank: int
    value_ref: str
    value_digest: str
    value_schema_id: str
    relation_set_digest: str
    admission_graph_digest: str
    receipt_digest: str
    committed_at: str
    result_digest: str = ""
    schema_id: str = field(default=_ADMIT_RESULT_SCHEMA, init=False)

    def __post_init__(self) -> None:
        for name in ("mutation_ref", "phase_basis_ref", "membership_ref", "value_ref"):
            object.__setattr__(self, name, _safe_ref(getattr(self, name)))
        for name in ("command_digest", "phase_basis_digest", "membership_digest", "value_digest", "relation_set_digest", "admission_graph_digest", "receipt_digest"):
            object.__setattr__(self, name, _sha256(getattr(self, name)))
        if self.disposition not in {"fresh_committed", "exact_replay"} or type(self.kind_rank) is not int or not 1 <= self.kind_rank <= 15:
            raise RW0C1PreflightError("invalid_value") from None
        if self.value_schema_id != _C1_KIND_SPECS[self.kind_rank - 1].schema_id:
            raise RW0C1PreflightError("invalid_value") from None
        object.__setattr__(self, "committed_at", _timestamp(self.committed_at))
        computed = _digest(self.schema_id + ".identity", self.identity_mapping())
        if self.result_digest:
            if _sha256(self.result_digest) != computed:
                raise RW0C1PreflightError("invalid_value") from None
        else:
            object.__setattr__(self, "result_digest", computed)

    def identity_mapping(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in (
            "schema_id", "mutation_ref", "command_digest", "disposition",
            "phase_basis_ref", "phase_basis_digest", "membership_ref",
            "membership_digest", "kind_rank", "value_ref", "value_digest",
            "value_schema_id", "relation_set_digest", "admission_graph_digest",
            "receipt_digest", "committed_at",
        )}

    def safe_projection(self) -> dict[str, object]:
        result = self.identity_mapping()
        result["result_digest"] = self.result_digest
        return result

    def committed_projection_digest(self) -> str:
        return _digest(
            self.schema_id + ".committed-projection",
            {
                "schema_id": self.schema_id,
                "mutation_ref": self.mutation_ref,
                "command_digest": self.command_digest,
                "phase_basis_ref": self.phase_basis_ref,
                "phase_basis_digest": self.phase_basis_digest,
                "membership_ref": self.membership_ref,
                "membership_digest": self.membership_digest,
                "kind_rank": self.kind_rank,
                "value_ref": self.value_ref,
                "value_digest": self.value_digest,
                "value_schema_id": self.value_schema_id,
                "relation_set_digest": self.relation_set_digest,
                "admission_graph_digest": self.admission_graph_digest,
                "committed_at": self.committed_at,
            },
        )


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1MutationReceiptV1(_PrivateValue):
    mutation_ref: str
    mutation_family: str
    command_schema_id: str
    command_digest: str
    phase_basis_ref: str
    phase_basis_digest: str
    membership_ref: str | None
    membership_digest: str | None
    kind_rank: int | None
    value_ref: str | None
    value_digest: str | None
    value_schema_id: str | None
    result_class: str
    result_projection_digest: str
    admission_graph_digest: str
    outcome: str
    committed_at: str
    receipt_digest: str = ""
    schema_id: str = field(default=_RECEIPT_SCHEMA, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "mutation_ref", _safe_ref(self.mutation_ref))
        object.__setattr__(self, "phase_basis_ref", _safe_ref(self.phase_basis_ref))
        for name in (
            "command_digest", "phase_basis_digest", "result_projection_digest",
            "admission_graph_digest",
        ):
            object.__setattr__(self, name, _sha256(getattr(self, name)))
        if self.outcome != "committed":
            raise RW0C1PreflightError("invalid_value") from None
        if self.mutation_family == "establish_rw0_phase":
            if (
                self.command_schema_id != _ESTABLISH_COMMAND_SCHEMA
                or self.result_class != "rw0_phase_established"
                or any(
                    value is not None
                    for value in (
                        self.membership_ref, self.membership_digest, self.kind_rank,
                        self.value_ref, self.value_digest, self.value_schema_id,
                    )
                )
            ):
                raise RW0C1PreflightError("invalid_value") from None
        elif self.mutation_family == "admit_rw0_evidence":
            if (
                self.command_schema_id != _ADMIT_COMMAND_SCHEMA
                or self.result_class != "rw0_evidence_admitted"
                or type(self.kind_rank) is not int
                or not 1 <= self.kind_rank <= 15
                or None in (
                    self.membership_ref, self.membership_digest, self.value_ref,
                    self.value_digest, self.value_schema_id,
                )
            ):
                raise RW0C1PreflightError("invalid_value") from None
            object.__setattr__(self, "membership_ref", _safe_ref(self.membership_ref))
            object.__setattr__(self, "membership_digest", _sha256(self.membership_digest))
            object.__setattr__(self, "value_ref", _safe_ref(self.value_ref))
            object.__setattr__(self, "value_digest", _sha256(self.value_digest))
            if self.value_schema_id != _C1_KIND_SPECS[self.kind_rank - 1].schema_id:
                raise RW0C1PreflightError("invalid_value") from None
        else:
            raise RW0C1PreflightError("invalid_value") from None
        object.__setattr__(self, "committed_at", _timestamp(self.committed_at))
        computed = _digest(self.schema_id + ".identity", self.identity_mapping())
        if self.receipt_digest:
            if _sha256(self.receipt_digest) != computed:
                raise RW0C1PreflightError("invalid_value") from None
        else:
            object.__setattr__(self, "receipt_digest", computed)

    def identity_mapping(self) -> dict[str, object]:
        return {
            name: getattr(self, name)
            for name in (
                "schema_id", "mutation_ref", "mutation_family", "command_schema_id",
                "command_digest", "phase_basis_ref", "phase_basis_digest",
                "membership_ref", "membership_digest", "kind_rank", "value_ref",
                "value_digest", "value_schema_id", "result_class",
                "result_projection_digest", "admission_graph_digest", "outcome",
                "committed_at",
            )
        }

    def safe_projection(self) -> dict[str, object]:
        result = self.identity_mapping()
        result["receipt_digest"] = self.receipt_digest
        return result


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1EvidenceAdmissionRecoverySelectorV1(_PrivateValue):
    """Stable pre-apply identity needed to resolve one uncertain admission."""

    mutation_ref: str
    command_digest: str
    phase_basis_ref: str
    phase_basis_digest: str
    preassigned_membership_ref: str
    kind_rank: int
    value_ref: str
    value_digest: str
    value_schema_id: str
    prerequisite_member_locators: tuple[RW0C1MemberLocatorV1, ...]
    owner_row_locators: tuple[RW0C1OwnerRowLocatorV1, ...]
    selector_digest: str = ""
    schema_id: str = field(
        default=_EVIDENCE_RECOVERY_SELECTOR_SCHEMA,
        init=False,
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "mutation_ref", _safe_ref(self.mutation_ref))
        object.__setattr__(self, "command_digest", _sha256(self.command_digest))
        object.__setattr__(self, "phase_basis_ref", _safe_ref(self.phase_basis_ref))
        object.__setattr__(self, "phase_basis_digest", _sha256(self.phase_basis_digest))
        object.__setattr__(
            self,
            "preassigned_membership_ref",
            _safe_ref(self.preassigned_membership_ref),
        )
        if type(self.kind_rank) is not int or not 1 <= self.kind_rank <= 15:
            raise RW0C1PreflightError("invalid_recovery_probe") from None
        object.__setattr__(self, "value_ref", _safe_ref(self.value_ref))
        object.__setattr__(self, "value_digest", _sha256(self.value_digest))
        if self.value_schema_id != _C1_KIND_SPECS[self.kind_rank - 1].schema_id:
            raise RW0C1PreflightError("invalid_recovery_probe") from None
        members = _tuple(self.prerequisite_member_locators, maximum=14)
        owners = _tuple(self.owner_row_locators, maximum=14)
        if (
            any(type(item) is not RW0C1MemberLocatorV1 for item in members)
            or any(type(item) is not RW0C1OwnerRowLocatorV1 for item in owners)
            or len(members) + len(owners) > 14
        ):
            raise RW0C1PreflightError("invalid_recovery_probe") from None
        roles = tuple(item.role for item in (*members, *owners))
        if len(roles) != len(set(roles)):
            raise RW0C1PreflightError("invalid_recovery_probe") from None
        computed = _digest(self.schema_id + ".identity", self.identity_mapping())
        if self.selector_digest:
            if _sha256(self.selector_digest) != computed:
                raise RW0C1PreflightError("invalid_recovery_probe") from None
        else:
            object.__setattr__(self, "selector_digest", computed)

    @property
    def mutation_family(self) -> str:
        return "admit_rw0_evidence"

    def identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "mutation_ref": self.mutation_ref,
            "command_digest": self.command_digest,
            "phase_basis_ref": self.phase_basis_ref,
            "phase_basis_digest": self.phase_basis_digest,
            "preassigned_membership_ref": self.preassigned_membership_ref,
            "kind_rank": self.kind_rank,
            "value_ref": self.value_ref,
            "value_digest": self.value_digest,
            "value_schema_id": self.value_schema_id,
            "prerequisite_member_locators": [
                item.to_mapping() for item in self.prerequisite_member_locators
            ],
            "owner_row_locators": [
                item.to_mapping() for item in self.owner_row_locators
            ],
        }


def evidence_admission_recovery_selector(
    command: RW0C1AdmitEvidenceCommandV1,
) -> RW0C1EvidenceAdmissionRecoverySelectorV1:
    """Derive a caller-retainable selector without I/O, clocks, or authority."""

    if type(command) is not RW0C1AdmitEvidenceCommandV1:
        raise RW0C1PreflightError("invalid_recovery_probe") from None
    value_ref, value_digest, value_schema_id, _scope, _mapping = evidence_identity(
        command.evidence_value,
        command.kind_rank,
    )
    return RW0C1EvidenceAdmissionRecoverySelectorV1(
        mutation_ref=command.mutation_ref,
        command_digest=command.command_digest,
        phase_basis_ref=command.phase_basis_ref,
        phase_basis_digest=command.phase_basis_digest,
        preassigned_membership_ref=command.preassigned_membership_ref,
        kind_rank=command.kind_rank,
        value_ref=value_ref,
        value_digest=value_digest,
        value_schema_id=value_schema_id,
        prerequisite_member_locators=command.prerequisite_member_locators,
        owner_row_locators=command.owner_row_locators,
    )


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1RecoveryProbeV1(_PrivateValue):
    mutation_family: str
    mutation_ref: str
    command_digest: str
    phase_basis_ref: str
    phase_basis_digest: str
    membership_ref: str | None = None
    membership_digest: str | None = None
    k8: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.mutation_family not in {"establish_rw0_phase", "admit_rw0_evidence"}:
            raise RW0C1PreflightError("invalid_recovery_probe") from None
        object.__setattr__(self, "mutation_ref", _safe_ref(self.mutation_ref))
        object.__setattr__(self, "command_digest", _sha256(self.command_digest))
        object.__setattr__(self, "phase_basis_ref", _safe_ref(self.phase_basis_ref))
        object.__setattr__(self, "phase_basis_digest", _sha256(self.phase_basis_digest))
        if self.mutation_family == "establish_rw0_phase":
            if (
                self.membership_ref is not None
                or self.membership_digest is not None
                or type(self.k8) is not tuple
                or len(self.k8) != 8
            ):
                raise RW0C1PreflightError("invalid_recovery_probe") from None
            object.__setattr__(self, "k8", tuple(_safe_ref(item) for item in self.k8))
        else:
            if (
                self.membership_ref is None
                or self.membership_digest is None
                or self.k8 is not None
            ):
                raise RW0C1PreflightError("invalid_recovery_probe") from None
            object.__setattr__(self, "membership_ref", _safe_ref(self.membership_ref))
            object.__setattr__(self, "membership_digest", _sha256(self.membership_digest))


@dataclass(frozen=True, slots=True, repr=False)
class RW0C1RecoveryResultV1(_PrivateValue):
    mutation_family: str
    mutation_ref: str
    command_digest: str
    disposition: RW0C1RecoveryDispositionV1
    receipt_digest: str | None = None
    result_projection_digest: str | None = None
    operation_graph_digest: str | None = None
    recovery_digest: str = ""
    schema_id: str = field(default=_RECOVERY_SCHEMA, init=False)

    def __post_init__(self) -> None:
        if self.mutation_family not in {"establish_rw0_phase", "admit_rw0_evidence"}:
            raise RW0C1PreflightError("invalid_value") from None
        object.__setattr__(self, "mutation_ref", _safe_ref(self.mutation_ref))
        object.__setattr__(self, "command_digest", _sha256(self.command_digest))
        if type(self.disposition) is not RW0C1RecoveryDispositionV1:
            raise RW0C1PreflightError("invalid_value") from None
        trio = (self.receipt_digest, self.result_projection_digest, self.operation_graph_digest)
        if self.disposition is RW0C1RecoveryDispositionV1.COMMITTED_EXACT:
            if any(item is None for item in trio):
                raise RW0C1PreflightError("invalid_value") from None
            for name in ("receipt_digest", "result_projection_digest", "operation_graph_digest"):
                object.__setattr__(self, name, _sha256(getattr(self, name)))
        elif any(item is not None for item in trio):
            raise RW0C1PreflightError("invalid_value") from None
        computed = _digest(self.schema_id + ".identity", self.identity_mapping())
        if self.recovery_digest:
            if _sha256(self.recovery_digest) != computed:
                raise RW0C1PreflightError("invalid_value") from None
        else:
            object.__setattr__(self, "recovery_digest", computed)

    def identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "mutation_family": self.mutation_family,
            "mutation_ref": self.mutation_ref,
            "command_digest": self.command_digest,
            "disposition": self.disposition.value,
            "receipt_digest": self.receipt_digest,
            "result_projection_digest": self.result_projection_digest,
            "operation_graph_digest": self.operation_graph_digest,
        }

    def safe_projection(self) -> dict[str, object]:
        result = self.identity_mapping()
        result["recovery_digest"] = self.recovery_digest
        return result


def relation_evaluation_time(
    *, relation_schema_id: str, evidence_value: object,
    operation_timestamp: str, host_qualification: object | None = None,
) -> str | None:
    """Return the closed owner semantic instant and reject future evidence."""

    operation_timestamp = _timestamp(operation_timestamp)
    if relation_schema_id in _OPERATION_TIME_RELATION_SCHEMAS:
        return operation_timestamp
    if relation_schema_id == _SUBJECT_TIME_HOST_RELATION_SCHEMA:
        if type(evidence_value) is not RW0EffectHostQualificationV1:
            raise RW0C1PreflightError("invalid_value") from None
        evaluated_at = _timestamp(evidence_value.evaluated_at)
    elif relation_schema_id == _SUBJECT_TIME_CAPABILITY_RELATION_SCHEMA:
        if type(evidence_value) is not RW0WorkerMechanismCapabilityQualificationV1 or type(host_qualification) is not RW0EffectHostQualificationV1:
            raise RW0C1PreflightError("invalid_value") from None
        evaluated_at = _timestamp(evidence_value.evaluated_at)
        if evaluated_at != _timestamp(host_qualification.evaluated_at):
            raise RW0C1PreflightError("invalid_value") from None
    elif relation_schema_id in _NON_TEMPORAL_RELATION_SCHEMAS:
        return None
    else:
        raise RW0C1PreflightError("invalid_value") from None
    if evaluated_at > operation_timestamp:
        raise RW0C1PreflightError("invalid_value") from None
    return evaluated_at


def membership_schema_id() -> str:
    return _MEMBERSHIP_SCHEMA


def _reject_private_subclass(cls: type[object], **kwargs: object) -> typing.NoReturn:
    del cls, kwargs
    raise TypeError("subclassing disabled") from None


for _final_value_type in (
    RW0C1MemberLocatorV1,
    RW0C1OwnerRowLocatorV1,
    RW0C1AdmissionSnapshotBindingV1,
    RW0C1TransientPrivateBindingV1,
    RW0C1WireWorkerResultBindingV1,
    RW0C1WireProcessResultClassificationBindingV1,
    RW0C1Section41PostExecutionProposalFamilyMemberV1,
    RW0C1EstablishPhaseCommandV1,
    RW0C1AdmitEvidenceCommandV1,
    RW0C1ConflictV1,
    RW0C1EstablishPhaseResultV1,
    RW0C1AdmitEvidenceResultV1,
    RW0C1MutationReceiptV1,
    RW0C1EvidenceAdmissionRecoverySelectorV1,
    RW0C1RecoveryProbeV1,
    RW0C1RecoveryResultV1,
):
    setattr(_final_value_type, "__init_subclass__", classmethod(_reject_private_subclass))
del _final_value_type
