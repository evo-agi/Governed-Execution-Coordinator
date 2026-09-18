"""Private pure RW0-B1 phase-entry values and supplied-fact relations.

No value in this module is executable authority, durable state, source
authenticity, physical custody, or a terminal-outcome receipt.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import typing

from ._worker_execution_semantic_values import (
    AttemptFenceV1,
    CandidateCapsuleManifestV1,
    CeilingsV1,
    DeliveryEnvelopeV1,
    EffectFenceV1,
    WorkSpecV1,
    WorkerCommandV1,
    _CEILING_FIELDS,
    _DELIVERABLE_EFFECT_CLASSES,
    _EFFECT_CLASSES,
    _ceilings_at_most,
    _local_git_effect_ceilings,
    _non_git_effect_ceilings,
    validate_authoring_relation,
    validate_delivery_relation,
    validate_effect_relation,
)
from ._development_pre_execution_plan_disposition_contracts import (
    CanonicalC2B3DLineage,
    PreExecutionPlanDispositionResultProjectionV1,
    _K8_FIELDS,
    _L34_FIELDS,
)
from ._cognitive_proposal_row_values import (
    DevelopmentModelProposalRowValue,
    DevelopmentPrivateProposalArtifactBindingRowValue,
    DevelopmentPreExecutionSelectionHeadRowValue,
)
from ._development_effect_row_values import (
    DevelopmentDeliveryHeadRowValue,
    DevelopmentEffectHeadRowValue,
)
from ._development_program_row_values import (
    DevelopmentProgramHeadRowValue,
    DevelopmentWorkItemHeadRowValue,
)
from ._development_decision_row_values import DevelopmentDecisionRowValue
from .persistence_contracts import GlobalStopCurrentRecordEnvelope


__all__: tuple[str, ...] = ()


_PATH_SCOPE_BINDING_DOMAIN = (
    "governed-execution.nwp-rw0-current-path-scope-binding.v1.identity"
)
_ERROR_REASONS = (
    "invalid_field_type", "missing_field", "unknown_field", "duplicate_field",
    "invalid_enum", "malformed_ref", "malformed_digest",
    "invalid_timestamp_window", "invalid_length_or_cardinality",
    "graph_cycle", "cumulative_work_exhausted", "relation_mismatch",
    "observation_stale_or_expired", "authority_denied_or_revoked",
    "per_fence_basis_mismatch", "common_family_unverified",
    "scope_or_ceiling_mismatch", "path_scope_binding_mismatch",
    "current_head_or_global_stop_mismatch", "custody_subject_mismatch",
    "retrieval_transition_invalid", "readiness_profile_mismatch",
    "qualification_reason_mismatch", "terminal_branch_mismatch",
    "privacy_forbidden_material",
)
_ERROR_TOKEN = object()
_SAFE_REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]*\Z", re.ASCII)
_IPV4_SHAPED_REF_RE = re.compile(r"[0-9]{1,3}(?:\.[0-9]{1,3}){3}\Z", re.ASCII)
_DIGEST_RE = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_OID_RE = re.compile(r"[0-9a-f]{40}\Z", re.ASCII)
_TIME_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z",
    re.ASCII,
)
_FORBIDDEN_REF_PREFIXES = (
    "connector-", "tunnel-", "workspace-", "org-", "organization-", "user-",
)
_PRIVATE_KEY_PARTS = (
    "hostname", "host_key", "ip_address", "endpoint", "username",
    "bearer", "token", "secret", "signature", "trust_root", "prompt",
    "transcript", "stdout", "stderr", "provider", "environment_value",
    "absolute_path", "workspace_path", "store_path",
)
_EFFECT_HEAD_STATES = (
    "ready_for_delivery", "delivery_pending", "delivery_outcome_unknown",
    "observed", "cancellation_effect_established", "terminal",
)
_DELIVERY_HEAD_STATES = (
    "planned", "submitted", "outcome_unknown", "acknowledged", "rejected",
    "completed",
)
_STOP_STATES = ("clear", "active")
_SUBJECT_KINDS = ("work_spec", "selected_plan")
_QUALIFICATION_REASONS = (
    "qualified", "readiness_unready", "readiness_unknown",
    "readiness_expired", "authority_not_verified",
    "authority_denied_or_revoked", "authority_expired",
    "phase_or_effect_mismatch", "worker_artifact_mismatch",
    "worker_protocol_mismatch", "platform_or_architecture_mismatch",
    "profile_mismatch", "global_stop_active", "unknown",
)
_QUALIFICATION_BLOCKING_REASONS = tuple(
    reason for reason in _QUALIFICATION_REASONS
    if reason not in ("qualified", "unknown")
)
_TERMINAL_OUTCOMES = (
    "accept", "repair", "replan", "terminal_reject", "block", "cancel",
)
_TERMINAL_BRANCHES = (
    "normal", "active_cancel_reconciled", "active_cancel_unresolved",
    "pre_effect_cancel_basis_unusable",
)
_RETRIEVAL_EVENTS = (
    "issued", "redeemed", "consumed", "expired", "revoked", "failed",
    "unknown",
)
_MAX_CANONICAL_INTEGER = 2**63 - 1


class RW0PhaseValueError(ValueError):
    """Sealed, content-free failure of a B1 value or relation."""

    __slots__ = ("_reason", "_field_path")

    def __init__(self, token: object, reason: str, field_path: str) -> None:
        if token is not _ERROR_TOKEN or reason not in _ERROR_REASONS:
            raise TypeError("RW0PhaseValueError cannot be constructed directly")
        self._reason = reason
        self._field_path = field_path
        super().__init__(f"{reason}:{field_path}")

    @property
    def reason(self) -> str:
        return self._reason

    @property
    def field_path(self) -> str:
        return self._field_path

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


def _fail(reason: str, label: str) -> typing.NoReturn:
    raise RW0PhaseValueError(_ERROR_TOKEN, reason, label)


def _require(condition: bool, reason: str, label: str) -> None:
    if not condition:
        _fail(reason, label)


class _WorkBudget:
    __slots__ = ("remaining", "active")

    def __init__(self, limit: int) -> None:
        self.remaining = limit
        self.active: set[int] = set()

    def charge(self, amount: int = 1) -> None:
        if amount > self.remaining:
            _fail("cumulative_work_exhausted", "work_budget")
        self.remaining -= amount

    def walk(self, value: object) -> None:
        if type(value) in (bytes, bytearray, memoryview):
            _fail("privacy_forbidden_material", "value")
        if type(value) in (dict, list, tuple):
            identity = id(value)
            if identity in self.active:
                _fail("graph_cycle", "value_graph")
            self.charge()
            self.active.add(identity)
            try:
                if type(value) is dict:
                    mapping = typing.cast(dict[object, object], value)
                    for member in mapping.values():
                        self.charge()
                        if type(member) in (dict, list, tuple):
                            self.walk(member)
                        elif type(member) in (bytes, bytearray, memoryview):
                            _fail("privacy_forbidden_material", "value")
                else:
                    for member in typing.cast(list[object] | tuple[object, ...], value):
                        self.walk(member)
            finally:
                self.active.remove(identity)
        else:
            self.charge()


def _closed_mapping(payload: object, fields: tuple[str, ...], label: str) -> dict[str, object]:
    if type(payload) is not dict:
        _fail("invalid_field_type", label)
    if len(payload) > len(fields):
        _fail("unknown_field", label)
    mapping = typing.cast(dict[object, object], payload)
    # This fixed-field-count pass belongs to the validation half of 2V.
    # Defer closure rejection so any non-exact key retains type precedence.
    unknown_reason: str | None = None
    for key in mapping:
        if type(key) is not str:
            _fail("invalid_field_type", label)
        if key not in fields and unknown_reason is None:
            unknown_reason = (
                "privacy_forbidden_material"
                if any(part in key.lower() for part in _PRIVATE_KEY_PARTS)
                else "unknown_field"
            )
    if unknown_reason is not None:
        _fail(unknown_reason, label)
    if len(mapping) < len(fields):
        _fail("missing_field", label)
    return typing.cast(dict[str, object], mapping)


def _string(value: object, label: str) -> str:
    if type(value) is not str:
        _fail("invalid_field_type", label)
    return typing.cast(str, value)


def _ref(value: object, label: str) -> str:
    item = _string(value, label)
    if (
        not 1 <= len(item) <= 96
        or _SAFE_REF_RE.fullmatch(item) is None
        or item.lower().startswith(_FORBIDDEN_REF_PREFIXES)
    ):
        _fail("malformed_ref", label)
    if _IPV4_SHAPED_REF_RE.fullmatch(item) is not None:
        _fail("privacy_forbidden_material", label)
    return item


def _digest(value: object, label: str) -> str:
    item = _string(value, label)
    if _DIGEST_RE.fullmatch(item) is None:
        _fail("malformed_digest", label)
    return item


def _oid(value: object, label: str) -> str:
    item = _string(value, label)
    if _OID_RE.fullmatch(item) is None:
        _fail("malformed_digest", label)
    return item


def _timestamp(value: object, label: str) -> str:
    item = _string(value, label)
    if len(item) != 20 or _TIME_RE.fullmatch(item) is None or item[:4] == "0000":
        _fail("invalid_timestamp_window", label)
    try:
        parsed = datetime.datetime.strptime(item, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        parsed = None
    if parsed is None or parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != item:
        _fail("invalid_timestamp_window", label)
    return item


def _integer(value: object, label: str, *, minimum: int = 0,
             maximum: int = _MAX_CANONICAL_INTEGER) -> int:
    if type(value) is not int:
        _fail("invalid_field_type", label)
    item = typing.cast(int, value)
    if item < minimum or item > maximum:
        _fail("invalid_length_or_cardinality", label)
    return item


def _enum(value: object, options: tuple[str, ...], label: str) -> str:
    item = _string(value, label)
    if item not in options:
        _fail("invalid_enum", label)
    return item


def _canonical_bytes(payload: object) -> bytes:
    failed = False
    result = b""
    try:
        result = json.dumps(
            payload, ensure_ascii=False, allow_nan=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8", "strict")
    except (TypeError, ValueError, UnicodeEncodeError):
        failed = True
    if failed:
        _fail("invalid_length_or_cardinality", "canonical_identity")
    return result


def _domain_digest(domain: str, payload: object) -> str:
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + _canonical_bytes(payload)).hexdigest()


def _path_scope_binding_digest(paths: tuple[str, ...]) -> str:
    if type(paths) is not tuple or any(type(item) is not str for item in paths):
        _fail("invalid_field_type", "path_scope")
    return _domain_digest(_PATH_SCOPE_BINDING_DOMAIN, list(paths))


def _lineage(value: object) -> CanonicalC2B3DLineage:
    mapping = _closed_mapping(value, _L34_FIELDS, "c2b3d_lineage")
    for name in _L34_FIELDS:
        if name.endswith("_ref"):
            _ref(mapping[name], f"c2b3d_lineage.{name}")
    for name in ("program_version_number", "attempt_number"):
        _integer(mapping[name], f"c2b3d_lineage.{name}")
    failed = False
    result: CanonicalC2B3DLineage | None = None
    try:
        result = CanonicalC2B3DLineage(**mapping)
    except (TypeError, ValueError):
        failed = True
    if failed or result is None:
        _fail("relation_mismatch", "c2b3d_lineage")
    return result


def _selection_key(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) is not list:
        _fail("invalid_field_type", "selection_key")
    members = typing.cast(list[object], value)
    if len(members) != 8:
        _fail("invalid_length_or_cardinality", "selection_key")
    checked: list[tuple[str, str]] = []
    for index, member in enumerate(members):
        if type(member) is not list:
            _fail("invalid_field_type", "selection_key")
        pair = typing.cast(list[object], member)
        if len(pair) != 2:
            _fail("invalid_length_or_cardinality", "selection_key")
        if type(pair[0]) is not str or pair[0] != _K8_FIELDS[index]:
            _fail("relation_mismatch", "selection_key")
        checked.append((_K8_FIELDS[index], _ref(pair[1], "selection_key")))
    return tuple(checked)


def _ceilings(value: object) -> CeilingsV1:
    mapping = _closed_mapping(value, _CEILING_FIELDS, "ceilings")
    for name in _CEILING_FIELDS:
        _integer(mapping[name], "ceilings")
    failed = False
    result: CeilingsV1 | None = None
    try:
        result = CeilingsV1.from_mapping(mapping)
    except (TypeError, ValueError):
        failed = True
    if failed or result is None:
        _fail("relation_mismatch", "ceilings")
    return result


def _effects(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        _fail("invalid_field_type", "allowed_effect_classes")
    members = typing.cast(list[object], value)
    if not 1 <= len(members) <= 5:
        _fail("invalid_length_or_cardinality", "allowed_effect_classes")
    checked = tuple(_enum(item, _EFFECT_CLASSES, "allowed_effect_classes") for item in members)
    if checked != tuple(sorted(set(checked))):
        _fail("invalid_length_or_cardinality", "allowed_effect_classes")
    return checked


def _external(member: object) -> object:
    if type(member) is CanonicalC2B3DLineage:
        return typing.cast(CanonicalC2B3DLineage, member).to_mapping()
    if type(member) is CeilingsV1:
        return typing.cast(CeilingsV1, member).to_mapping()
    if type(member) is tuple:
        return [_external(item) for item in typing.cast(tuple[object, ...], member)]
    return member


def _reject_subclass(cls: type[object], **kwargs: object) -> typing.NoReturn:
    raise TypeError("subclassing disabled")


class _B1Value:
    __slots__ = ("_values",)
    __hash__ = None
    _FIELDS: tuple[str, ...] = ()
    _SCHEMA = ""
    _LIMIT = 0

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("construction disabled")

    def __setattr__(self, name: str, value: object) -> typing.NoReturn:
        raise AttributeError("immutable")

    def __delattr__(self, name: str) -> typing.NoReturn:
        raise AttributeError("immutable")

    def __getattr__(self, name: str) -> object:
        if name in type(self)._FIELDS:
            return object.__getattribute__(self, "_values")[type(self)._FIELDS.index(name)]
        raise AttributeError(name)

    def __repr__(self) -> str:
        return f"<{type(self).__name__}>"

    __str__ = __repr__

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other) and self._values == typing.cast(_B1Value, other)._values

    def __copy__(self) -> _B1Value:
        return self

    def __deepcopy__(self, memo: object) -> _B1Value:
        return self

    def __reduce__(self) -> typing.NoReturn:
        raise TypeError("pickling disabled")

    def __reduce_ex__(self, protocol: int) -> typing.NoReturn:
        raise TypeError("pickling disabled")

    @classmethod
    def from_mapping(cls, payload: dict[str, object]) -> _B1Value:
        mapping = _closed_mapping(payload, cls._FIELDS, cls.__name__)
        budget = _WorkBudget(cls._LIMIT)
        budget.walk(mapping)
        values = tuple(_validate_member(cls, name, mapping[name], mapping) for name in cls._FIELDS)
        _validate_cross_fields(cls, mapping)
        result = object.__new__(cls)
        object.__setattr__(result, "_values", values)
        if result.computed_digest() != object.__getattribute__(result, "_values")[-1]:
            _fail("relation_mismatch", cls.__name__)
        budget.walk(result.to_mapping())
        return result

    def to_mapping(self) -> dict[str, object]:
        return {
            name: _external(member)
            for name, member in zip(type(self)._FIELDS, self._values)
        }

    def identity_mapping(self) -> dict[str, object]:
        mapping = self.to_mapping()
        mapping.pop(type(self)._FIELDS[-1])
        return mapping

    def canonical_identity_bytes(self) -> bytes:
        return _canonical_bytes(self.identity_mapping())

    def computed_digest(self) -> str:
        return _domain_digest(type(self)._SCHEMA + ".identity", self.identity_mapping())


class RW0PhaseEntryBasisV1(_B1Value):
    _SCHEMA = "governed-execution.nwp-rw0-phase-entry-basis.v1"
    _FIELDS = (
        "schema_id", "basis_ref", "c2b3d_lineage", "selection_key",
        "selected_proposal_ref", "selected_proposal_digest",
        "selected_artifact_ref", "selected_artifact_digest",
        "selected_artifact_binding_digest", "selected_plan_safe_projection_digest",
        "disposition_ref", "disposition_digest", "disposition",
        "selection_head_revision", "selection_head_digest",
        "current_effect_head_revision", "current_effect_head_state",
        "current_effect_head_digest", "current_delivery_head_revision",
        "current_delivery_head_state", "current_delivery_head_digest",
        "global_stop_ref", "global_stop_version", "global_stop_state",
        "path_scope_digest", "basis_digest",
    )
    _LIMIT = 174
    __slots__ = ()
    __init_subclass__ = _reject_subclass


class RW0AuthorityVerificationObservationV1(_B1Value):
    _SCHEMA = "governed-execution.nwp-rw0-authority-verification-observation.v1"
    _FIELDS = (
        "schema_id", "observation_ref", "source_ref", "evidence_ref",
        "evidence_digest", "phase_basis_ref", "phase_basis_digest",
        "parent_grant_ref", "parent_grant_digest", "grant_family_ref",
        "grant_family_digest", "attempt_basis_ref", "attempt_basis_digest",
        "effect_basis_ref", "effect_basis_digest", "attempt_fence_ref",
        "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest",
        "audience_ref", "repository_ref", "base_git_object_format",
        "base_git_oid", "path_scope_digest", "allowed_effect_classes",
        "effect_class", "parent_ceilings", "status", "family_status",
        "revocation_status", "grant_expires_at", "observed_at",
        "observation_expires_at", "current_effect_head_digest",
        "current_delivery_head_digest", "global_stop_ref",
        "global_stop_version", "global_stop_state", "observation_digest",
    )
    _LIMIT = 124
    __slots__ = ()
    __init_subclass__ = _reject_subclass


class RW0SubordinateAuthorizationProposalV1(_B1Value):
    _SCHEMA = "governed-execution.nwp-rw0-subordinate-authorization-proposal.v1"
    _FIELDS = (
        "schema_id", "proposal_ref", "phase_basis_ref", "phase_basis_digest",
        "verification_ref", "verification_digest", "parent_grant_ref",
        "parent_grant_digest", "grant_family_ref", "grant_family_digest",
        "attempt_basis_ref", "attempt_basis_digest", "effect_basis_ref",
        "effect_basis_digest", "attempt_fence_ref", "attempt_fence_digest",
        "effect_fence_ref", "effect_fence_digest", "audience_ref",
        "repository_ref", "base_git_object_format", "base_git_oid",
        "path_scope_digest", "effect_class", "ceilings", "expires_at",
        "global_stop_ref", "global_stop_version", "proposal_digest",
    )
    _LIMIT = 92
    __slots__ = ()
    __init_subclass__ = _reject_subclass


class RW0CustodyAvailabilityObservationV1(_B1Value):
    _SCHEMA = "governed-execution.nwp-rw0-custody-availability-observation.v1"
    _FIELDS = (
        "schema_id", "observation_ref", "source_ref", "evidence_ref",
        "evidence_digest", "phase_basis_ref", "phase_basis_digest",
        "subject_kind", "subject_ref", "subject_semantic_digest",
        "content_sha256", "byte_length", "availability", "observed_at",
        "expires_at", "observation_digest",
    )
    _LIMIT = 34
    __slots__ = ()
    __init_subclass__ = _reject_subclass


class RW0RetrievalCapabilityEventObservationV1(_B1Value):
    _SCHEMA = "governed-execution.nwp-rw0-retrieval-capability-event-observation.v1"
    _FIELDS = (
        "schema_id", "event_ref", "source_ref", "evidence_ref",
        "evidence_digest", "phase_basis_ref", "phase_basis_digest",
        "safe_correlation_ref", "subject_kind", "subject_ref",
        "subject_semantic_digest", "content_sha256", "byte_length",
        "semantic_attempt_ref", "attempt_fence_ref", "attempt_fence_digest",
        "effect_intent_ref", "effect_fence_ref", "effect_fence_digest",
        "audience_ref", "repository_ref", "base_git_object_format",
        "base_git_oid", "path_scope_digest", "authority_observation_ref",
        "authority_observation_digest", "subordinate_proposal_ref",
        "subordinate_proposal_digest", "custody_observation_ref",
        "custody_observation_digest", "event_kind", "predecessor_event_ref",
        "predecessor_event_digest", "sequence_number", "occurred_at",
        "expires_at", "event_digest",
    )
    _LIMIT = 76
    __slots__ = ()
    __init_subclass__ = _reject_subclass


class RW0RemoteHostReadinessObservationV1(_B1Value):
    _SCHEMA = "governed-execution.nwp-rw0-remote-host-readiness-observation.v1"
    _FIELDS = (
        "schema_id", "observation_ref", "source_ref", "evidence_ref",
        "evidence_digest", "safe_host_correlation_ref", "status", "platform",
        "platform_profile_ref", "platform_profile_digest",
        "architecture_profile_ref", "architecture_profile_digest",
        "worker_artifact_ref", "worker_artifact_digest",
        "worker_protocol_ref", "worker_protocol_digest",
        "execution_identity_profile_ref", "execution_identity_profile_digest",
        "process_profile_ref", "process_profile_digest", "isolation_profile_ref",
        "isolation_profile_digest", "resource_profile_ref",
        "resource_profile_digest", "cancellation_profile_ref",
        "cancellation_profile_digest", "credential_handoff_profile_ref",
        "credential_handoff_profile_digest", "capsule_store_profile_ref",
        "capsule_store_profile_digest", "validation_tool_profile_ref",
        "validation_tool_profile_digest", "review_tool_profile_ref",
        "review_tool_profile_digest", "cleanup_profile_ref",
        "cleanup_profile_digest", "observed_at", "expires_at",
        "observation_digest",
    )
    _LIMIT = 80
    __slots__ = ()
    __init_subclass__ = _reject_subclass


class RW0EffectHostQualificationV1(_B1Value):
    _SCHEMA = "governed-execution.nwp-rw0-effect-host-qualification.v1"
    _FIELDS = (
        "schema_id", "qualification_ref", "phase_basis_ref",
        "phase_basis_digest", "effect_intent_ref", "effect_fence_ref",
        "effect_fence_digest", "verification_ref", "verification_digest",
        "readiness_ref", "readiness_digest", "required_scenario_profile_ref",
        "required_scenario_profile_digest", "required_platform_profile_ref",
        "required_platform_profile_digest", "required_architecture_profile_ref",
        "required_architecture_profile_digest", "required_worker_artifact_ref",
        "required_worker_artifact_digest", "required_worker_protocol_ref",
        "required_worker_protocol_digest",
        "required_execution_identity_profile_ref",
        "required_execution_identity_profile_digest",
        "required_process_profile_ref", "required_process_profile_digest",
        "required_isolation_profile_ref", "required_isolation_profile_digest",
        "required_resource_profile_ref", "required_resource_profile_digest",
        "required_cancellation_profile_ref",
        "required_cancellation_profile_digest",
        "required_credential_handoff_profile_ref",
        "required_credential_handoff_profile_digest",
        "required_capsule_store_profile_ref",
        "required_capsule_store_profile_digest",
        "required_validation_tool_profile_ref",
        "required_validation_tool_profile_digest",
        "required_review_tool_profile_ref", "required_review_tool_profile_digest",
        "required_cleanup_profile_ref", "required_cleanup_profile_digest",
        "result", "reason", "evaluated_at", "qualification_digest",
    )
    _LIMIT = 92
    __slots__ = ()
    __init_subclass__ = _reject_subclass


class RW0TerminalOutcomeV1(_B1Value):
    _SCHEMA = "governed-execution.nwp-rw0-terminal-outcome-value.v1"
    _FIELDS = (
        "schema_id", "outcome_value_ref", "phase_basis_ref",
        "phase_basis_digest", "branch", "outcome", "decision_ref",
        "decision_digest", "decision_kind", "program_head_revision",
        "program_head_digest", "work_item_head_revision", "work_item_head_digest",
        "selection_head_revision", "selection_head_digest",
        "effect_head_revision", "effect_head_digest", "delivery_head_revision",
        "delivery_head_digest", "global_stop_ref", "global_stop_version",
        "global_stop_state", "evidence_set_ref", "evidence_set_digest",
        "latch_postimage_ref", "latch_postimage_digest",
        "reconciliation_ref", "reconciliation_digest", "mismatch_ref",
        "mismatch_digest", "outcome_value_digest",
    )
    _LIMIT = 64
    __slots__ = ()
    __init_subclass__ = _reject_subclass


_B1_CLASSES = (
    RW0PhaseEntryBasisV1, RW0AuthorityVerificationObservationV1,
    RW0SubordinateAuthorizationProposalV1, RW0CustodyAvailabilityObservationV1,
    RW0RetrievalCapabilityEventObservationV1,
    RW0RemoteHostReadinessObservationV1, RW0EffectHostQualificationV1,
    RW0TerminalOutcomeV1,
)


def _validate_member(cls: type[_B1Value], name: str, value: object,
                     mapping: dict[str, object]) -> object:
    label = f"{cls.__name__}.{name}"
    if name == "schema_id":
        return _enum(value, (cls._SCHEMA,), label)
    if name == "c2b3d_lineage":
        return _lineage(value)
    if name == "selection_key":
        return _selection_key(value)
    if name in ("parent_ceilings", "ceilings"):
        return _ceilings(value)
    if name == "allowed_effect_classes":
        return _effects(value)
    if name in (
        "predecessor_event_ref", "latch_postimage_ref", "reconciliation_ref",
        "mismatch_ref",
    ):
        return None if value is None else _ref(value, label)
    if name in (
        "predecessor_event_digest", "latch_postimage_digest",
        "reconciliation_digest", "mismatch_digest",
    ):
        return None if value is None else _digest(value, label)
    if name == "base_git_object_format":
        return _enum(value, ("sha1",), label)
    if name == "base_git_oid":
        return _oid(value, label)
    if name == "disposition":
        return _enum(value, ("selected_for_dispatch_gates",), label)
    if name == "current_effect_head_state":
        return _enum(value, _EFFECT_HEAD_STATES, label)
    if name == "current_delivery_head_state":
        return _enum(value, _DELIVERY_HEAD_STATES, label)
    if name == "global_stop_state":
        return _enum(value, _STOP_STATES, label)
    if name == "subject_kind":
        return _enum(value, _SUBJECT_KINDS, label)
    if name == "availability":
        return _enum(value, ("available", "unavailable", "unknown"), label)
    if name == "event_kind":
        return _enum(value, _RETRIEVAL_EVENTS, label)
    if name == "platform":
        return _enum(value, ("linux",), label)
    if name == "status":
        options = (("verified", "denied", "unknown") if cls is RW0AuthorityVerificationObservationV1
                   else ("ready", "unready", "unknown"))
        return _enum(value, options, label)
    if name == "family_status":
        return _enum(value, ("compatible", "incompatible", "unknown"), label)
    if name == "revocation_status":
        return _enum(value, ("unrevoked", "revoked", "unknown"), label)
    if name == "effect_class":
        return _enum(value, _DELIVERABLE_EFFECT_CLASSES, label)
    if name == "result":
        return _enum(value, ("qualified", "blocked", "unknown"), label)
    if name == "reason":
        return _enum(value, _QUALIFICATION_REASONS, label)
    if name == "branch":
        return _enum(value, _TERMINAL_BRANCHES, label)
    if name in ("outcome", "decision_kind"):
        return _enum(value, _TERMINAL_OUTCOMES, label)
    if name == "byte_length":
        maximum = 65_536 if mapping["subject_kind"] == "selected_plan" else 2**63 - 1
        return _integer(value, label, minimum=1, maximum=maximum)
    if name == "sequence_number":
        return _integer(value, label, maximum=2)
    if name == "selection_head_revision":
        return _integer(value, label, maximum=2**63 - 1)
    if name.endswith("_revision") or name.endswith("_version"):
        return _integer(value, label)
    if name.endswith("_at"):
        return _timestamp(value, label)
    if name.endswith("_digest") or name == "content_sha256":
        return _digest(value, label)
    if name.endswith("_ref"):
        return _ref(value, label)
    _fail("invalid_field_type", label)


def _pair(mapping: dict[str, object], prefix: str) -> bool:
    return mapping[prefix + "_ref"] is not None and mapping[prefix + "_digest"] is not None


def _validate_cross_fields(cls: type[_B1Value], mapping: dict[str, object]) -> None:
    if cls is RW0PhaseEntryBasisV1:
        lineage = typing.cast(dict[str, object], mapping["c2b3d_lineage"])
        key = typing.cast(list[list[str]], mapping["selection_key"])
        if tuple((name, lineage[name]) for name in _K8_FIELDS) != tuple(tuple(item) for item in key):
            _fail("relation_mismatch", "selection_key")
    if cls is RW0AuthorityVerificationObservationV1:
        if not mapping["observed_at"] < mapping["observation_expires_at"]:
            _fail("invalid_timestamp_window", "authority_window")
    if cls in (RW0CustodyAvailabilityObservationV1, RW0RemoteHostReadinessObservationV1):
        if not mapping["observed_at"] < mapping["expires_at"]:
            _fail("invalid_timestamp_window", "observation_window")
    if cls is RW0RetrievalCapabilityEventObservationV1:
        predecessor = _pair(mapping, "predecessor_event")
        if (mapping["predecessor_event_ref"] is None) != (mapping["predecessor_event_digest"] is None):
            _fail("invalid_length_or_cardinality", "predecessor_event")
        if (mapping["sequence_number"] == 0) == predecessor:
            _fail("invalid_length_or_cardinality", "predecessor_event")
        if mapping["event_kind"] in ("issued", "redeemed", "consumed") and not mapping["occurred_at"] < mapping["expires_at"]:
            _fail("invalid_timestamp_window", "retrieval_window")
    if cls is RW0EffectHostQualificationV1:
        result = mapping["result"]
        reason = mapping["reason"]
        if not (
            (result == "qualified" and reason == "qualified")
            or (result == "unknown" and reason == "unknown")
            or (result == "blocked" and reason in _QUALIFICATION_BLOCKING_REASONS)
        ):
            _fail("qualification_reason_mismatch", "qualification_result")
    if cls is RW0TerminalOutcomeV1:
        for prefix in ("latch_postimage", "reconciliation", "mismatch"):
            if (mapping[prefix + "_ref"] is None) != (mapping[prefix + "_digest"] is None):
                _fail("invalid_length_or_cardinality", "terminal_pair")
        _terminal_shape_mapping(mapping)


def _terminal_shape_mapping(mapping: dict[str, object]) -> None:
    branch, outcome, decision = (
        mapping["branch"], mapping["outcome"], mapping["decision_kind"]
    )
    latch = _pair(mapping, "latch_postimage")
    recon = _pair(mapping, "reconciliation")
    mismatch = _pair(mapping, "mismatch")
    valid = (
        (branch == "normal" and outcome == decision and outcome != "cancel"
         and latch == (outcome == "accept") and not recon and not mismatch)
        or (branch == "active_cancel_reconciled" and decision == "cancel"
            and outcome == "cancel" and recon and not latch and not mismatch)
        or (branch == "active_cancel_unresolved" and decision == "cancel"
            and outcome == "block" and recon and not latch and not mismatch)
        or (branch == "pre_effect_cancel_basis_unusable" and decision == "cancel"
            and outcome == "block" and mismatch and not latch and not recon)
    )
    if not valid:
        _fail("terminal_branch_mismatch", "terminal_branch")


def _value(budget: _WorkBudget, value: object, expected: type[_B1Value]) -> _B1Value:
    if type(value) is not expected:
        _fail("invalid_field_type", expected.__name__)
    checked = typing.cast(_B1Value, value)
    budget.walk(checked.to_mapping())
    _require(checked.computed_digest() == checked._values[-1], "relation_mismatch", expected.__name__)
    return checked


def _leaf(budget: _WorkBudget, value: object, expected: type[object], label: str) -> None:
    budget.charge()
    if type(value) is not expected:
        _fail("invalid_field_type", label)


def _time_leaf(budget: _WorkBudget, value: object) -> str:
    budget.charge()
    return _timestamp(value, "now_utc")


def _path_leaf(budget: _WorkBudget, paths: object) -> str:
    budget.walk(paths)
    return _path_scope_binding_digest(typing.cast(tuple[str, ...], paths))


def _owner_relation(function: typing.Callable[..., None], **kwargs: object) -> None:
    failed = False
    try:
        function(**kwargs)
    except Exception:
        failed = True
    if failed:
        _fail("relation_mismatch", "owner_relation")


def _pair_equals(value: object, prefix: str, ref: str, digest: str,
                 reason: str) -> None:
    if getattr(value, prefix + "_ref") != ref or getattr(value, prefix + "_digest") != digest:
        _fail(reason, prefix)


def _stop_matches(value: object, global_stop: GlobalStopCurrentRecordEnvelope,
                  reason: str = "current_head_or_global_stop_mismatch") -> None:
    state = global_stop.state
    if (value.global_stop_ref, value.global_stop_version, value.global_stop_state) != (
        state.stop_ref, state.version, "active" if state.active else "clear"
    ):
        _fail(reason, "global_stop")


def _basis_pair(value: object, basis: RW0PhaseEntryBasisV1,
                reason: str = "relation_mismatch") -> None:
    _pair_equals(value, "phase_basis", basis.basis_ref, basis.basis_digest, reason)


def _basis_lineage_matches(basis: RW0PhaseEntryBasisV1, *objects: object) -> None:
    lineage = basis.c2b3d_lineage
    for obj in objects:
        mapping = obj.to_mapping()
        for name in _L34_FIELDS:
            if name in mapping and name not in ("schema_id",):
                if mapping[name] != getattr(lineage, name):
                    _fail("relation_mismatch", "lineage")


def _stable_current_origin(basis: RW0PhaseEntryBasisV1,
                           current_effect_fence: EffectFenceV1) -> bool:
    lineage = basis.c2b3d_lineage
    return (current_effect_fence.candidate_ref,
            current_effect_fence.command_ref,
            current_effect_fence.command_digest) == (
                lineage.candidate_ref, lineage.author_command_ref,
                lineage.author_command_digest)


def _attempt_effect_lineage(basis: RW0PhaseEntryBasisV1,
                            attempt_fence: AttemptFenceV1,
                            current_effect_fence: EffectFenceV1) -> None:
    lineage = basis.c2b3d_lineage
    _require(
        (attempt_fence.attempt_fence_ref, attempt_fence.attempt_fence_digest,
         attempt_fence.semantic_attempt_ref) ==
        (lineage.attempt_fence_ref, lineage.attempt_fence_digest,
         lineage.semantic_attempt_ref),
        "per_fence_basis_mismatch", "attempt_lineage",
    )
    _require(
        (current_effect_fence.attempt_fence_ref,
         current_effect_fence.attempt_fence_digest,
         current_effect_fence.semantic_attempt_ref) ==
        (attempt_fence.attempt_fence_ref, attempt_fence.attempt_fence_digest,
         attempt_fence.semantic_attempt_ref),
        "per_fence_basis_mismatch", "current_effect_origin",
    )
    _require(
        (current_effect_fence.program_ref, current_effect_fence.program_version_ref,
         current_effect_fence.accepted_intent_revision_ref,
         current_effect_fence.work_item_ref, current_effect_fence.work_item_revision_ref) ==
        (attempt_fence.program_ref, attempt_fence.program_version_ref,
         attempt_fence.accepted_intent_revision_ref,
         attempt_fence.work_item_ref, attempt_fence.work_item_revision_ref),
        "per_fence_basis_mismatch", "current_effect_origin",
    )
    _require(_stable_current_origin(basis, current_effect_fence),
             "relation_mismatch", "current_effect_command_or_candidate")


def _current_effect_within_attempt(basis: RW0PhaseEntryBasisV1,
                                   attempt_fence: AttemptFenceV1,
                                   current_effect_fence: EffectFenceV1) -> None:
    # External leaves were charged by the caller's single shared B1 budget.
    # Reconstruct through the owner to validate fields and stored self-digests.
    _owner_relation(AttemptFenceV1.from_mapping, payload=attempt_fence.to_mapping())
    _owner_relation(EffectFenceV1.from_mapping, payload=current_effect_fence.to_mapping())
    _attempt_effect_lineage(basis, attempt_fence, current_effect_fence)
    _require(attempt_fence.allowed_effect_classes.count(current_effect_fence.effect_class) == 1,
             "scope_or_ceiling_mismatch", "current_effect_class")
    _require(_ceilings_at_most(current_effect_fence.effect_ceilings,
                               attempt_fence.aggregate_ceilings) and
             current_effect_fence.expires_at <= attempt_fence.expires_at,
             "scope_or_ceiling_mismatch", "current_effect_attempt_bounds")
    ceilings_valid = (
        _local_git_effect_ceilings(current_effect_fence.effect_ceilings)
        if current_effect_fence.effect_class == "local_git_commit"
        else _non_git_effect_ceilings(current_effect_fence.effect_ceilings)
    )
    _require(ceilings_valid, "scope_or_ceiling_mismatch", "current_effect_ceilings")


def _verified_parent_contains(
    observation: RW0AuthorityVerificationObservationV1,
    attempt_fence: AttemptFenceV1, *effect_fences: EffectFenceV1,
    parent_reason: str,
) -> None:
    parent_pair = (observation.parent_grant_ref, observation.parent_grant_digest)
    _require(
        parent_pair == (attempt_fence.parent_standing_grant_ref,
                        attempt_fence.parent_standing_grant_digest) and
        all(parent_pair == (fence.parent_standing_grant_ref,
                            fence.parent_standing_grant_digest)
            for fence in effect_fences),
        parent_reason, "parent_grant",
    )
    allowed = set(observation.allowed_effect_classes)
    _require(set(attempt_fence.allowed_effect_classes) <= allowed,
             "scope_or_ceiling_mismatch", "attempt_effect_set")
    parent = observation.parent_ceilings.to_mapping()
    attempt = attempt_fence.aggregate_ceilings.to_mapping()
    _require(all(attempt[name] <= parent[name] for name in _CEILING_FIELDS) and
             attempt_fence.expires_at <= observation.grant_expires_at,
             "scope_or_ceiling_mismatch", "attempt_parent")
    for fence in effect_fences:
        ceilings = fence.effect_ceilings.to_mapping()
        _require(fence.effect_class in allowed and
                 fence.effect_class in attempt_fence.allowed_effect_classes and
                 all(ceilings[name] <= parent[name] for name in _CEILING_FIELDS) and
                 fence.expires_at <= observation.grant_expires_at,
                 "scope_or_ceiling_mismatch", "effect_parent")


def validate_phase_entry_basis(*, basis: RW0PhaseEntryBasisV1,
                               lineage: CanonicalC2B3DLineage,
                               selection_result: PreExecutionPlanDispositionResultProjectionV1,
                               selection_head: DevelopmentPreExecutionSelectionHeadRowValue,
                               selected_proposal: DevelopmentModelProposalRowValue,
                               selected_artifact: DevelopmentPrivateProposalArtifactBindingRowValue,
                               work_spec: WorkSpecV1, attempt_fence: AttemptFenceV1,
                               author_effect_fence: EffectFenceV1,
                               author_command: WorkerCommandV1,
                               author_delivery: DeliveryEnvelopeV1,
                               effect_head: DevelopmentEffectHeadRowValue,
                               delivery_head: DevelopmentDeliveryHeadRowValue,
                               global_stop: GlobalStopCurrentRecordEnvelope) -> None:
    budget = _WorkBudget(104)
    _value(budget, basis, RW0PhaseEntryBasisV1)
    for label, obj, kind in (
        ("lineage", lineage, CanonicalC2B3DLineage),
        ("selection_result", selection_result, PreExecutionPlanDispositionResultProjectionV1),
        ("selection_head", selection_head, DevelopmentPreExecutionSelectionHeadRowValue),
        ("selected_proposal", selected_proposal, DevelopmentModelProposalRowValue),
        ("selected_artifact", selected_artifact, DevelopmentPrivateProposalArtifactBindingRowValue),
        ("work_spec", work_spec, WorkSpecV1),
        ("attempt_fence", attempt_fence, AttemptFenceV1),
        ("author_effect_fence", author_effect_fence, EffectFenceV1),
        ("author_command", author_command, WorkerCommandV1),
        ("author_delivery", author_delivery, DeliveryEnvelopeV1),
        ("effect_head", effect_head, DevelopmentEffectHeadRowValue),
        ("delivery_head", delivery_head, DevelopmentDeliveryHeadRowValue),
        ("global_stop", global_stop, GlobalStopCurrentRecordEnvelope),
    ):
        _leaf(budget, obj, kind, label)
    _require(basis.c2b3d_lineage == lineage, "relation_mismatch", "lineage")
    _require(basis.selection_key == tuple((name, getattr(lineage, name)) for name in _K8_FIELDS),
             "relation_mismatch", "selection_key")
    _require((basis.selected_proposal_ref, basis.selected_proposal_digest) ==
             (selected_proposal.proposal_ref, selected_proposal.proposal_digest),
             "relation_mismatch", "selected_proposal")
    _require((basis.selected_artifact_ref, basis.selected_artifact_digest,
              basis.selected_artifact_binding_digest, basis.selected_plan_safe_projection_digest) ==
             (selected_artifact.artifact_ref, selected_artifact.artifact_digest,
              selected_artifact.artifact_binding_digest, selected_artifact.safe_projection_digest),
             "relation_mismatch", "selected_artifact")
    _require((selected_proposal.artifact_ref, selected_proposal.artifact_digest,
              selected_proposal.safe_projection_digest) ==
             (selected_artifact.artifact_ref, selected_artifact.artifact_digest,
              selected_artifact.safe_projection_digest), "relation_mismatch", "selected_artifact")
    _require((basis.disposition_ref, basis.disposition_digest, basis.disposition,
              basis.selection_head_revision, basis.selection_head_digest) ==
             (selection_result.disposition_ref, selection_result.disposition_digest,
              selection_result.disposition, selection_result.selection_head_revision,
              selection_result.selection_head_digest), "relation_mismatch", "selection_result")
    _require((selection_result.proposal_ref, selection_result.selection_head_revision,
              selection_result.selection_head_digest) ==
             (selected_proposal.proposal_ref, selection_head.head_revision,
              selection_head.head_digest), "relation_mismatch", "selection_head")
    _require((selection_head.current_proposal_ref, selection_head.current_disposition_ref,
              selection_head.current_disposition) ==
             (selected_proposal.proposal_ref, selection_result.disposition_ref,
              "selected_for_dispatch_gates"), "relation_mismatch", "selection_head")
    _require((work_spec.work_spec_ref, work_spec.work_spec_digest) ==
             (lineage.work_spec_ref, lineage.work_spec_digest), "relation_mismatch", "work_spec")
    _basis_lineage_matches(basis, selection_head, selection_result, work_spec,
                           attempt_fence, author_effect_fence, author_command, author_delivery)
    _owner_relation(validate_authoring_relation, work_spec=work_spec,
                    attempt_fence=attempt_fence, author_command=author_command,
                    author_effect_fence=author_effect_fence)
    _owner_relation(validate_delivery_relation, delivery=author_delivery,
                    author_command=author_command, attempt_fence=attempt_fence,
                    author_effect_fence=author_effect_fence, effect_fence=author_effect_fence)
    _require((basis.current_effect_head_revision, basis.current_effect_head_state,
              basis.current_effect_head_digest) ==
             (effect_head.head_revision, effect_head.effect_state, effect_head.head_digest),
             "current_head_or_global_stop_mismatch", "effect_head")
    _require((basis.current_delivery_head_revision, basis.current_delivery_head_state,
              basis.current_delivery_head_digest) ==
             (delivery_head.head_revision, delivery_head.delivery_state, delivery_head.head_digest),
             "current_head_or_global_stop_mismatch", "delivery_head")
    _require((effect_head.effect_intent_ref, delivery_head.effect_intent_ref,
              effect_head.program_ref, delivery_head.program_ref) ==
             (lineage.effect_intent_ref, lineage.effect_intent_ref,
              lineage.program_ref, lineage.program_ref),
             "current_head_or_global_stop_mismatch", "heads")
    _stop_matches(basis, global_stop)
    _require(basis.path_scope_digest == _path_leaf(budget, work_spec.authorized_paths),
             "path_scope_binding_mismatch", "path_scope")
    _require(work_spec.authorized_paths == attempt_fence.path_ceiling ==
             author_effect_fence.path_ceiling == author_command.path_ceiling,
             "path_scope_binding_mismatch", "path_scope")


def validate_authority_observation(*, basis: RW0PhaseEntryBasisV1,
                                   observation: RW0AuthorityVerificationObservationV1,
                                   attempt_fence: AttemptFenceV1,
                                   author_effect_fence: EffectFenceV1,
                                   current_effect_fence: EffectFenceV1,
                                   author_command: WorkerCommandV1,
                                   capsule_manifest: CandidateCapsuleManifestV1 | None,
                                   cancellation_target: EffectFenceV1 | None,
                                   now_utc: str) -> None:
    budget = _WorkBudget(196)
    _value(budget, basis, RW0PhaseEntryBasisV1)
    _value(budget, observation, RW0AuthorityVerificationObservationV1)
    for label, obj, kind in (
        ("attempt_fence", attempt_fence, AttemptFenceV1),
        ("author_effect_fence", author_effect_fence, EffectFenceV1),
        ("current_effect_fence", current_effect_fence, EffectFenceV1),
        ("author_command", author_command, WorkerCommandV1),
        ("capsule_manifest", capsule_manifest, CandidateCapsuleManifestV1),
        ("cancellation_target", cancellation_target, EffectFenceV1),
    ):
        budget.charge()
        if obj is not None and type(obj) is not kind:
            _fail("invalid_field_type", label)
    now = _time_leaf(budget, now_utc)
    budget.charge(30 + 6)
    _basis_pair(observation, basis)
    _basis_lineage_matches(basis, attempt_fence, author_effect_fence,
                           author_command)
    _attempt_effect_lineage(basis, attempt_fence, current_effect_fence)
    _require(basis.global_stop_state == observation.global_stop_state == "clear" and
             (attempt_fence.global_stop_ref, attempt_fence.global_stop_version) ==
             (basis.global_stop_ref, basis.global_stop_version) and
             (author_effect_fence.global_stop_ref,
              author_effect_fence.global_stop_version) ==
             (basis.global_stop_ref, basis.global_stop_version) and
             (current_effect_fence.global_stop_ref,
              current_effect_fence.global_stop_version) ==
             (basis.global_stop_ref, basis.global_stop_version),
             "current_head_or_global_stop_mismatch", "global_stop")
    if observation.status != "verified" or observation.revocation_status != "unrevoked":
        _fail("authority_denied_or_revoked", "authority")
    if observation.family_status != "compatible":
        _fail("common_family_unverified", "grant_family")
    if not (observation.observed_at <= now < observation.observation_expires_at
            and now < observation.grant_expires_at
            and now < attempt_fence.expires_at
            and now < author_effect_fence.expires_at
            and now < current_effect_fence.expires_at):
        _fail("observation_stale_or_expired", "authority_window")
    _verified_parent_contains(observation, attempt_fence,
                              author_effect_fence, current_effect_fence,
                              parent_reason="relation_mismatch")
    _pair_equals(observation, "attempt_fence", attempt_fence.attempt_fence_ref,
                 attempt_fence.attempt_fence_digest, "relation_mismatch")
    _pair_equals(observation, "effect_fence", current_effect_fence.effect_fence_ref,
                 current_effect_fence.effect_fence_digest, "relation_mismatch")
    _require((observation.attempt_basis_ref, observation.attempt_basis_digest) ==
             (attempt_fence.attempt_authorization_ref,
              attempt_fence.attempt_authorization_digest),
             "per_fence_basis_mismatch", "attempt_basis")
    _require((observation.effect_basis_ref, observation.effect_basis_digest) ==
             (current_effect_fence.effect_authorization_ref,
              current_effect_fence.effect_authorization_digest),
             "per_fence_basis_mismatch", "effect_basis")
    _require((observation.audience_ref, observation.repository_ref,
              observation.base_git_object_format, observation.base_git_oid,
              observation.effect_class) ==
             (author_command.program_ref, author_command.repository_ref,
              author_command.base_git_object_format, author_command.base_git_oid,
              current_effect_fence.effect_class), "relation_mismatch", "scope")
    _require(observation.effect_class in observation.allowed_effect_classes,
             "scope_or_ceiling_mismatch", "effect_class")
    _require((observation.current_effect_head_digest,
              observation.current_delivery_head_digest,
              observation.global_stop_ref, observation.global_stop_version,
              observation.global_stop_state) ==
             (basis.current_effect_head_digest, basis.current_delivery_head_digest,
              basis.global_stop_ref, basis.global_stop_version,
              basis.global_stop_state),
             "current_head_or_global_stop_mismatch", "current_state")
    _require(observation.path_scope_digest == basis.path_scope_digest ==
             _path_leaf(budget, attempt_fence.path_ceiling),
             "path_scope_binding_mismatch", "path_scope")
    kwargs: dict[str, object] = dict(attempt_fence=attempt_fence,
        author_command=author_command, author_effect_fence=author_effect_fence,
        effect_fence=current_effect_fence)
    if capsule_manifest is not None:
        kwargs["capsule_manifest"] = capsule_manifest
    if cancellation_target is not None:
        kwargs["cancellation_target"] = cancellation_target
    _owner_relation(validate_effect_relation, **kwargs)
    _require(current_effect_fence.path_ceiling == attempt_fence.path_ceiling,
             "path_scope_binding_mismatch", "path_scope")


def validate_per_fence_basis(*, observation: RW0AuthorityVerificationObservationV1,
                             proposal: RW0SubordinateAuthorizationProposalV1,
                             attempt_fence: AttemptFenceV1,
                             current_effect_fence: EffectFenceV1) -> None:
    budget = _WorkBudget(110)
    _value(budget, observation, RW0AuthorityVerificationObservationV1)
    _value(budget, proposal, RW0SubordinateAuthorizationProposalV1)
    _leaf(budget, attempt_fence, AttemptFenceV1, "attempt_fence")
    _leaf(budget, current_effect_fence, EffectFenceV1, "current_effect_fence")
    for value in (observation, proposal):
        _pair_equals(value, "attempt_fence", attempt_fence.attempt_fence_ref,
                     attempt_fence.attempt_fence_digest, "per_fence_basis_mismatch")
        _pair_equals(value, "effect_fence", current_effect_fence.effect_fence_ref,
                     current_effect_fence.effect_fence_digest, "per_fence_basis_mismatch")
        _require((value.attempt_basis_ref, value.attempt_basis_digest) ==
                 (attempt_fence.attempt_authorization_ref,
                  attempt_fence.attempt_authorization_digest),
                 "per_fence_basis_mismatch", "attempt_basis")
        _require((value.effect_basis_ref, value.effect_basis_digest) ==
                 (current_effect_fence.effect_authorization_ref,
                  current_effect_fence.effect_authorization_digest),
                 "per_fence_basis_mismatch", "effect_basis")


def validate_external_common_family_claim(*,
    observation: RW0AuthorityVerificationObservationV1,
    proposal: RW0SubordinateAuthorizationProposalV1,
    attempt_fence: AttemptFenceV1,
    current_effect_fence: EffectFenceV1) -> None:
    budget = _WorkBudget(110)
    _value(budget, observation, RW0AuthorityVerificationObservationV1)
    _value(budget, proposal, RW0SubordinateAuthorizationProposalV1)
    _leaf(budget, attempt_fence, AttemptFenceV1, "attempt_fence")
    _leaf(budget, current_effect_fence, EffectFenceV1, "current_effect_fence")
    _require(observation.family_status == "compatible", "common_family_unverified", "family_status")
    _require((observation.grant_family_ref, observation.grant_family_digest) ==
             (proposal.grant_family_ref, proposal.grant_family_digest),
             "common_family_unverified", "grant_family")
    _require((observation.parent_grant_ref, observation.parent_grant_digest) ==
             (proposal.parent_grant_ref, proposal.parent_grant_digest) ==
             (attempt_fence.parent_standing_grant_ref,
              attempt_fence.parent_standing_grant_digest) ==
             (current_effect_fence.parent_standing_grant_ref,
              current_effect_fence.parent_standing_grant_digest),
             "common_family_unverified", "parent_grant")
    for value in (observation, proposal):
        _require((value.attempt_basis_ref, value.attempt_basis_digest) ==
                 (attempt_fence.attempt_authorization_ref,
                  attempt_fence.attempt_authorization_digest),
                 "per_fence_basis_mismatch", "attempt_basis")
        _require((value.effect_basis_ref, value.effect_basis_digest) ==
                 (current_effect_fence.effect_authorization_ref,
                  current_effect_fence.effect_authorization_digest),
                 "per_fence_basis_mismatch", "effect_basis")


def _narrowing_core(basis: RW0PhaseEntryBasisV1,
                    observation: RW0AuthorityVerificationObservationV1,
                    proposal: RW0SubordinateAuthorizationProposalV1,
                    attempt_fence: AttemptFenceV1,
                    current_effect_fence: EffectFenceV1, now: str,
                    budget: _WorkBudget, *, paths_already_charged: bool = False) -> None:
    _basis_pair(observation, basis)
    _basis_pair(proposal, basis)
    _basis_lineage_matches(basis, attempt_fence)
    _current_effect_within_attempt(basis, attempt_fence, current_effect_fence)
    _require(basis.global_stop_state == observation.global_stop_state == "clear" and
             (attempt_fence.global_stop_ref, attempt_fence.global_stop_version) ==
             (basis.global_stop_ref, basis.global_stop_version) and
             (current_effect_fence.global_stop_ref,
              current_effect_fence.global_stop_version) ==
             (basis.global_stop_ref, basis.global_stop_version) and
             (proposal.global_stop_ref, proposal.global_stop_version) ==
             (basis.global_stop_ref, basis.global_stop_version),
             "current_head_or_global_stop_mismatch", "global_stop")
    _require((observation.current_effect_head_digest,
              observation.current_delivery_head_digest) ==
             (basis.current_effect_head_digest, basis.current_delivery_head_digest),
             "current_head_or_global_stop_mismatch", "current_heads")
    if observation.status != "verified" or observation.revocation_status != "unrevoked":
        _fail("authority_denied_or_revoked", "authority")
    if not (observation.observed_at <= now < observation.observation_expires_at
            and now < observation.grant_expires_at
            and now < attempt_fence.expires_at
            and now < current_effect_fence.expires_at):
        _fail("observation_stale_or_expired", "authority_window")
    _require(observation.family_status == "compatible" and
             (observation.grant_family_ref, observation.grant_family_digest) ==
             (proposal.grant_family_ref, proposal.grant_family_digest),
             "common_family_unverified", "grant_family")
    _require((observation.parent_grant_ref, observation.parent_grant_digest) ==
             (proposal.parent_grant_ref, proposal.parent_grant_digest) ==
             (attempt_fence.parent_standing_grant_ref,
              attempt_fence.parent_standing_grant_digest) ==
             (current_effect_fence.parent_standing_grant_ref,
              current_effect_fence.parent_standing_grant_digest),
             "common_family_unverified", "parent_grant")
    for value in (observation, proposal):
        _require((value.attempt_basis_ref, value.attempt_basis_digest) ==
                 (attempt_fence.attempt_authorization_ref,
                  attempt_fence.attempt_authorization_digest) and
                 (value.effect_basis_ref, value.effect_basis_digest) ==
                 (current_effect_fence.effect_authorization_ref,
                  current_effect_fence.effect_authorization_digest) and
                 (value.attempt_fence_ref, value.attempt_fence_digest) ==
                 (attempt_fence.attempt_fence_ref, attempt_fence.attempt_fence_digest) and
                 (value.effect_fence_ref, value.effect_fence_digest) ==
                 (current_effect_fence.effect_fence_ref,
                  current_effect_fence.effect_fence_digest),
                 "per_fence_basis_mismatch", "fence_basis")
    _require((proposal.verification_ref, proposal.verification_digest) ==
             (observation.observation_ref, observation.observation_digest),
             "relation_mismatch", "verification")
    for value in (observation, proposal):
        _require((value.audience_ref, value.repository_ref,
                  value.base_git_object_format, value.base_git_oid,
                  value.global_stop_ref, value.global_stop_version) ==
                 (attempt_fence.program_ref, attempt_fence.repository_ref,
                  attempt_fence.base_git_object_format, attempt_fence.base_git_oid,
                  basis.global_stop_ref, basis.global_stop_version),
                 "scope_or_ceiling_mismatch", "scope")
        _require(value.path_scope_digest == basis.path_scope_digest,
                 "path_scope_binding_mismatch", "path_scope")
    _require((current_effect_fence.program_ref,
              current_effect_fence.repository_ref,
              current_effect_fence.base_git_object_format,
              current_effect_fence.base_git_oid,
              current_effect_fence.attempt_fence_ref,
              current_effect_fence.attempt_fence_digest) ==
             (attempt_fence.program_ref, attempt_fence.repository_ref,
              attempt_fence.base_git_object_format, attempt_fence.base_git_oid,
              attempt_fence.attempt_fence_ref, attempt_fence.attempt_fence_digest),
             "scope_or_ceiling_mismatch", "current_fence_scope")
    _require((proposal.effect_class, observation.effect_class) ==
             (current_effect_fence.effect_class, current_effect_fence.effect_class),
             "scope_or_ceiling_mismatch", "effect_class")
    _require(attempt_fence.path_ceiling == current_effect_fence.path_ceiling,
             "path_scope_binding_mismatch", "path_scope")
    for paths in (attempt_fence.path_ceiling, current_effect_fence.path_ceiling):
        digest = (_path_scope_binding_digest(paths) if paths_already_charged
                  else _path_leaf(budget, paths))
        _require(digest == basis.path_scope_digest,
                 "path_scope_binding_mismatch", "path_scope")
    budget.charge(30 + 6)
    _verified_parent_contains(observation, attempt_fence,
                              current_effect_fence,
                              parent_reason="common_family_unverified")
    allowed = observation.allowed_effect_classes
    _require(proposal.effect_class in allowed and
             proposal.effect_class in attempt_fence.allowed_effect_classes,
             "scope_or_ceiling_mismatch", "effect_set")
    parent = observation.parent_ceilings.to_mapping()
    attempt = attempt_fence.aggregate_ceilings.to_mapping()
    effect = current_effect_fence.effect_ceilings.to_mapping()
    proposed = proposal.ceilings.to_mapping()
    _require(all(proposed[name] <= parent[name] and proposed[name] <= attempt[name]
                 and proposed[name] <= effect[name] for name in _CEILING_FIELDS),
             "scope_or_ceiling_mismatch", "ceilings")
    _require(proposal.expires_at <= observation.grant_expires_at and
             proposal.expires_at <= attempt_fence.expires_at and
             proposal.expires_at <= current_effect_fence.expires_at and
             now < proposal.expires_at,
             "scope_or_ceiling_mismatch", "expires_at")
    strict = (len(allowed) > 1 or
              any(proposed[name] < parent[name] for name in _CEILING_FIELDS) or
              proposal.expires_at < observation.grant_expires_at)
    _require(strict, "scope_or_ceiling_mismatch", "strict_narrowing")


def validate_subordinate_narrowing(*, basis: RW0PhaseEntryBasisV1,
    observation: RW0AuthorityVerificationObservationV1,
    proposal: RW0SubordinateAuthorizationProposalV1,
    attempt_fence: AttemptFenceV1,
    current_effect_fence: EffectFenceV1, now_utc: str) -> None:
    budget = _WorkBudget(242)
    _value(budget, basis, RW0PhaseEntryBasisV1)
    _value(budget, observation, RW0AuthorityVerificationObservationV1)
    _value(budget, proposal, RW0SubordinateAuthorizationProposalV1)
    _leaf(budget, attempt_fence, AttemptFenceV1, "attempt_fence")
    _leaf(budget, current_effect_fence, EffectFenceV1, "current_effect_fence")
    now = _time_leaf(budget, now_utc)
    _narrowing_core(basis, observation, proposal, attempt_fence,
                    current_effect_fence, now, budget)


def validate_custody_binding(*, basis: RW0PhaseEntryBasisV1,
    availability: RW0CustodyAvailabilityObservationV1,
    subject: WorkSpecV1 | DevelopmentPrivateProposalArtifactBindingRowValue,
    now_utc: str) -> None:
    budget = _WorkBudget(106)
    _value(budget, basis, RW0PhaseEntryBasisV1)
    _value(budget, availability, RW0CustodyAvailabilityObservationV1)
    budget.charge()
    now = _time_leaf(budget, now_utc)
    _basis_pair(availability, basis, "custody_subject_mismatch")
    if availability.subject_kind == "work_spec":
        _require(type(subject) is WorkSpecV1, "invalid_field_type", "subject")
        checked = typing.cast(WorkSpecV1, subject)
        expected = (basis.c2b3d_lineage.work_spec_ref,
                    basis.c2b3d_lineage.work_spec_digest)
        actual = (checked.work_spec_ref, checked.work_spec_digest)
    else:
        _require(type(subject) is DevelopmentPrivateProposalArtifactBindingRowValue,
                 "invalid_field_type", "subject")
        artifact = typing.cast(DevelopmentPrivateProposalArtifactBindingRowValue, subject)
        expected = (basis.selected_artifact_ref, basis.selected_artifact_digest)
        actual = (artifact.artifact_ref, artifact.artifact_digest)
        _require(availability.byte_length == artifact.artifact_canonical_byte_length,
                 "custody_subject_mismatch", "byte_length")
    _require((availability.subject_ref, availability.subject_semantic_digest) ==
             expected == actual, "custody_subject_mismatch", "subject")
    _require(availability.availability == "available" and
             availability.observed_at <= now < availability.expires_at,
             "observation_stale_or_expired", "custody_window")


def validate_retrieval_event_sequence(*, basis: RW0PhaseEntryBasisV1,
    availability: RW0CustodyAvailabilityObservationV1,
    observation: RW0AuthorityVerificationObservationV1,
    proposal: RW0SubordinateAuthorizationProposalV1,
    events: tuple[RW0RetrievalCapabilityEventObservationV1, ...],
    attempt_fence: AttemptFenceV1, current_effect_fence: EffectFenceV1,
    now_utc: str) -> None:
    budget = _WorkBudget(374)
    _value(budget, basis, RW0PhaseEntryBasisV1)
    _value(budget, availability, RW0CustodyAvailabilityObservationV1)
    _value(budget, observation, RW0AuthorityVerificationObservationV1)
    _value(budget, proposal, RW0SubordinateAuthorizationProposalV1)
    if type(events) is not tuple or not 1 <= len(events) <= 3:
        _fail("invalid_length_or_cardinality", "events")
    budget.charge()
    for event in events:
        _value(budget, event, RW0RetrievalCapabilityEventObservationV1)
    _leaf(budget, attempt_fence, AttemptFenceV1, "attempt_fence")
    _leaf(budget, current_effect_fence, EffectFenceV1, "current_effect_fence")
    now = _time_leaf(budget, now_utc)
    for paths in (attempt_fence.path_ceiling, current_effect_fence.path_ceiling):
        _require(_path_leaf(budget, paths) == basis.path_scope_digest,
                 "path_scope_binding_mismatch", "path_scope")
    _narrowing_core(basis, observation, proposal, attempt_fence,
                    current_effect_fence, now, budget,
                    paths_already_charged=True)
    _basis_pair(availability, basis, "custody_subject_mismatch")
    _basis_pair(observation, basis)
    _basis_pair(proposal, basis)
    expected_subject = (
        (basis.c2b3d_lineage.work_spec_ref, basis.c2b3d_lineage.work_spec_digest)
        if availability.subject_kind == "work_spec" else
        (basis.selected_artifact_ref, basis.selected_artifact_digest)
    )
    _require((availability.subject_ref, availability.subject_semantic_digest) ==
             expected_subject, "custody_subject_mismatch", "subject")
    _require(availability.availability == "available" and
             availability.observed_at <= now < availability.expires_at,
             "observation_stale_or_expired", "custody_window")
    _require((proposal.verification_ref, proposal.verification_digest) ==
             (observation.observation_ref, observation.observation_digest),
             "relation_mismatch", "proposal")
    for claim in (observation, proposal):
        _require((claim.attempt_fence_ref, claim.attempt_fence_digest,
                  claim.effect_fence_ref, claim.effect_fence_digest,
                  claim.attempt_basis_ref, claim.attempt_basis_digest,
                  claim.effect_basis_ref, claim.effect_basis_digest) ==
                 (attempt_fence.attempt_fence_ref, attempt_fence.attempt_fence_digest,
                  current_effect_fence.effect_fence_ref,
                  current_effect_fence.effect_fence_digest,
                  attempt_fence.attempt_authorization_ref,
                  attempt_fence.attempt_authorization_digest,
                  current_effect_fence.effect_authorization_ref,
                  current_effect_fence.effect_authorization_digest),
                 "per_fence_basis_mismatch", "fences")
    _require(availability.subject_kind in _SUBJECT_KINDS, "custody_subject_mismatch", "subject")
    previous: RW0RetrievalCapabilityEventObservationV1 | None = None
    event_refs: set[str] = set()
    capability_expires_at = events[0].expires_at
    for index, event in enumerate(events):
        _require(event.event_ref not in event_refs and
                 event.predecessor_event_ref != event.event_ref and
                 event.expires_at == capability_expires_at,
                 "retrieval_transition_invalid", "event_identity")
        event_refs.add(event.event_ref)
        _basis_pair(event, basis, "retrieval_transition_invalid")
        _require((event.subject_kind, event.subject_ref, event.subject_semantic_digest,
                  event.content_sha256, event.byte_length) ==
                 (availability.subject_kind, availability.subject_ref,
                  availability.subject_semantic_digest, availability.content_sha256,
                  availability.byte_length), "custody_subject_mismatch", "subject")
        _require((event.semantic_attempt_ref, event.effect_intent_ref,
                  event.attempt_fence_ref, event.attempt_fence_digest,
                  event.effect_fence_ref, event.effect_fence_digest) ==
                 (basis.c2b3d_lineage.semantic_attempt_ref,
                  current_effect_fence.effect_intent_ref,
                  attempt_fence.attempt_fence_ref, attempt_fence.attempt_fence_digest,
                  current_effect_fence.effect_fence_ref,
                  current_effect_fence.effect_fence_digest),
                 "retrieval_transition_invalid", "fences")
        _require((event.audience_ref, event.repository_ref,
                  event.base_git_object_format, event.base_git_oid) ==
                 (attempt_fence.program_ref, attempt_fence.repository_ref,
                  attempt_fence.base_git_object_format, attempt_fence.base_git_oid),
                 "retrieval_transition_invalid", "scope")
        _require((event.authority_observation_ref, event.authority_observation_digest,
                  event.subordinate_proposal_ref, event.subordinate_proposal_digest,
                  event.custody_observation_ref, event.custody_observation_digest) ==
                 (observation.observation_ref, observation.observation_digest,
                  proposal.proposal_ref, proposal.proposal_digest,
                  availability.observation_ref, availability.observation_digest),
                 "retrieval_transition_invalid", "claim_bindings")
        _require(event.sequence_number == index, "retrieval_transition_invalid", "sequence_number")
        if previous is None:
            _require(event.predecessor_event_ref is None and
                     event.predecessor_event_digest is None,
                     "retrieval_transition_invalid", "predecessor")
        else:
            _require((event.predecessor_event_ref, event.predecessor_event_digest) ==
                     (previous.event_ref, previous.event_digest) and
                     previous.occurred_at <= event.occurred_at,
                     "retrieval_transition_invalid", "predecessor")
        _require(event.safe_correlation_ref == events[0].safe_correlation_ref,
                 "retrieval_transition_invalid", "correlation")
        _require(event.path_scope_digest == basis.path_scope_digest,
                 "path_scope_binding_mismatch", "path_scope")
        if event.event_kind in ("issued", "redeemed", "consumed"):
            _require(availability.availability == "available" and
                     availability.observed_at <= event.occurred_at < availability.expires_at,
                     "observation_stale_or_expired", "custody_window")
            _require(observation.status == "verified" and
                     observation.revocation_status == "unrevoked" and
                     observation.family_status == "compatible",
                     "authority_denied_or_revoked", "authority")
            _require(observation.observed_at <= event.occurred_at <
                     observation.observation_expires_at and
                     event.occurred_at < observation.grant_expires_at and
                     event.occurred_at < proposal.expires_at and
                     event.occurred_at < attempt_fence.expires_at and
                     event.occurred_at < current_effect_fence.expires_at and
                     event.occurred_at < event.expires_at,
                     "observation_stale_or_expired", "retrieval_window")
        if event.event_kind == "expired":
            _require(event.occurred_at >= event.expires_at,
                     "retrieval_transition_invalid", "expires_at")
        previous = event
    kinds = tuple(event.event_kind for event in events)
    legal = (kinds in (("issued",), ("issued", "redeemed"),
                       ("issued", "redeemed", "consumed"),
                       ("failed",), ("unknown",)) or
             (len(kinds) in (2, 3) and kinds[-1] in
              ("expired", "revoked", "failed", "unknown") and
              kinds[:-1] in (("issued",), ("issued", "redeemed"))))
    _require(legal, "retrieval_transition_invalid", "sequence")
    _require(events[-1].occurred_at <= now, "retrieval_transition_invalid", "future_event")


def validate_host_qualification(*, basis: RW0PhaseEntryBasisV1,
    authority: RW0AuthorityVerificationObservationV1,
    readiness: RW0RemoteHostReadinessObservationV1,
    qualification: RW0EffectHostQualificationV1,
    current_effect_fence: EffectFenceV1, now_utc: str) -> None:
    budget = _WorkBudget(241)
    _value(budget, basis, RW0PhaseEntryBasisV1)
    _value(budget, authority, RW0AuthorityVerificationObservationV1)
    _value(budget, readiness, RW0RemoteHostReadinessObservationV1)
    _value(budget, qualification, RW0EffectHostQualificationV1)
    _leaf(budget, current_effect_fence, EffectFenceV1, "current_effect_fence")
    now = _time_leaf(budget, now_utc)
    path_digest = _path_leaf(budget, current_effect_fence.path_ceiling)
    lineage = basis.c2b3d_lineage
    _owner_relation(EffectFenceV1.from_mapping, payload=current_effect_fence.to_mapping())
    phase_match = (
        _stable_current_origin(basis, current_effect_fence) and
        path_digest == basis.path_scope_digest == authority.path_scope_digest and
        (qualification.phase_basis_ref, qualification.phase_basis_digest) ==
        (basis.basis_ref, basis.basis_digest) and
        (authority.phase_basis_ref, authority.phase_basis_digest) ==
        (basis.basis_ref, basis.basis_digest) and
        (qualification.effect_intent_ref, qualification.effect_fence_ref,
         qualification.effect_fence_digest) ==
        (current_effect_fence.effect_intent_ref, current_effect_fence.effect_fence_ref,
         current_effect_fence.effect_fence_digest) and
        (authority.effect_fence_ref, authority.effect_fence_digest) ==
        (current_effect_fence.effect_fence_ref, current_effect_fence.effect_fence_digest) and
        (authority.attempt_fence_ref, authority.attempt_fence_digest) ==
        (lineage.attempt_fence_ref, lineage.attempt_fence_digest) ==
        (current_effect_fence.attempt_fence_ref,
         current_effect_fence.attempt_fence_digest) and
        (authority.attempt_basis_ref, authority.attempt_basis_digest) ==
        (lineage.attempt_authorization_ref,
         lineage.attempt_authorization_digest) and
        current_effect_fence.semantic_attempt_ref == lineage.semantic_attempt_ref and
        (current_effect_fence.program_ref, current_effect_fence.program_version_ref,
         current_effect_fence.accepted_intent_revision_ref,
         current_effect_fence.work_item_ref,
         current_effect_fence.work_item_revision_ref) ==
        (lineage.program_ref, lineage.program_version_ref,
         lineage.accepted_intent_revision_ref,
         lineage.work_item_ref, lineage.work_item_revision_ref) and
        authority.effect_class == current_effect_fence.effect_class and
        authority.audience_ref == current_effect_fence.program_ref and
        authority.repository_ref == current_effect_fence.repository_ref and
        (authority.base_git_object_format, authority.base_git_oid) ==
        (current_effect_fence.base_git_object_format,
         current_effect_fence.base_git_oid) and
        current_effect_fence.program_ref == lineage.program_ref and
        (authority.current_effect_head_digest,
         authority.current_delivery_head_digest) ==
        (basis.current_effect_head_digest, basis.current_delivery_head_digest) and
        (qualification.verification_ref, qualification.verification_digest) ==
        (authority.observation_ref, authority.observation_digest) and
        (qualification.readiness_ref, qualification.readiness_digest) ==
        (readiness.observation_ref, readiness.observation_digest) and
        (authority.global_stop_ref, authority.global_stop_version,
         authority.global_stop_state) ==
        (basis.global_stop_ref, basis.global_stop_version,
         basis.global_stop_state) and
        (current_effect_fence.global_stop_ref,
         current_effect_fence.global_stop_version) ==
        (basis.global_stop_ref, basis.global_stop_version)
    )
    if not phase_match:
        result = ("blocked", "phase_or_effect_mismatch")
    elif basis.global_stop_state == "active" or authority.global_stop_state == "active":
        result = ("blocked", "global_stop_active")
    elif authority.status == "denied" or authority.revocation_status == "revoked":
        result = ("blocked", "authority_denied_or_revoked")
    elif not (authority.observed_at <= now < authority.observation_expires_at and
              now < authority.grant_expires_at and now < current_effect_fence.expires_at):
        result = ("blocked", "authority_expired")
    elif authority.status == "unknown" or authority.revocation_status == "unknown":
        result = ("unknown", "unknown")
    elif authority.family_status != "compatible" or (
        authority.parent_grant_ref, authority.parent_grant_digest) != (
            current_effect_fence.parent_standing_grant_ref,
            current_effect_fence.parent_standing_grant_digest
        ) or (
        authority.effect_basis_ref, authority.effect_basis_digest
        ) != (
            current_effect_fence.effect_authorization_ref,
            current_effect_fence.effect_authorization_digest
        ) or current_effect_fence.effect_class not in authority.allowed_effect_classes or (
        any(current_effect_fence.effect_ceilings.to_mapping()[name] >
            authority.parent_ceilings.to_mapping()[name] for name in _CEILING_FIELDS)
        ) or current_effect_fence.expires_at > authority.grant_expires_at:
        result = ("blocked", "authority_not_verified")
    elif not readiness.observed_at <= now < readiness.expires_at:
        result = ("blocked", "readiness_expired")
    elif readiness.status == "unready":
        result = ("blocked", "readiness_unready")
    elif readiness.status == "unknown":
        result = ("blocked", "readiness_unknown")
    elif (qualification.required_worker_artifact_ref,
          qualification.required_worker_artifact_digest) != (
              readiness.worker_artifact_ref, readiness.worker_artifact_digest):
        result = ("blocked", "worker_artifact_mismatch")
    elif (qualification.required_worker_protocol_ref,
          qualification.required_worker_protocol_digest) != (
              readiness.worker_protocol_ref, readiness.worker_protocol_digest):
        result = ("blocked", "worker_protocol_mismatch")
    elif (readiness.platform != "linux" or
          (qualification.required_platform_profile_ref,
           qualification.required_platform_profile_digest) != (
              readiness.platform_profile_ref, readiness.platform_profile_digest) or
          (qualification.required_architecture_profile_ref,
           qualification.required_architecture_profile_digest) != (
              readiness.architecture_profile_ref, readiness.architecture_profile_digest)):
        result = ("blocked", "platform_or_architecture_mismatch")
    elif any(
        (getattr(qualification, "required_" + stem + suffix) !=
         getattr(readiness, stem + suffix))
        for stem in (
            "execution_identity_profile", "process_profile", "isolation_profile",
            "resource_profile", "cancellation_profile", "credential_handoff_profile",
            "capsule_store_profile", "validation_tool_profile",
            "review_tool_profile", "cleanup_profile",
        ) for suffix in ("_ref", "_digest")
    ):
        result = ("blocked", "profile_mismatch")
    else:
        result = ("qualified", "qualified")
    _require((qualification.result, qualification.reason) == result,
             "qualification_reason_mismatch", "qualification_result")
    _require(qualification.evaluated_at == now, "qualification_reason_mismatch", "evaluated_at")


def _terminal_shape(outcome: RW0TerminalOutcomeV1, decision: DevelopmentDecisionRowValue,
                    branch: str, budget: _WorkBudget) -> None:
    _value(budget, outcome, RW0TerminalOutcomeV1)
    _leaf(budget, decision, DevelopmentDecisionRowValue, "decision")
    _require(outcome.branch == branch and outcome.decision_kind == decision.decision_kind,
             "terminal_branch_mismatch", "terminal_branch")
    _terminal_shape_mapping(outcome.to_mapping())


def validate_normal_outcome_shape(*, outcome: RW0TerminalOutcomeV1,
                                  decision: DevelopmentDecisionRowValue) -> None:
    _terminal_shape(outcome, decision, "normal", _WorkBudget(33))


def validate_reconciled_cancel_outcome_shape(*, outcome: RW0TerminalOutcomeV1,
                                             decision: DevelopmentDecisionRowValue) -> None:
    _terminal_shape(outcome, decision, "active_cancel_reconciled", _WorkBudget(33))


def validate_unresolved_cancel_outcome_shape(*, outcome: RW0TerminalOutcomeV1,
                                             decision: DevelopmentDecisionRowValue) -> None:
    _terminal_shape(outcome, decision, "active_cancel_unresolved", _WorkBudget(33))


def validate_unusable_cancel_basis_outcome_shape(*, outcome: RW0TerminalOutcomeV1,
                                                  decision: DevelopmentDecisionRowValue) -> None:
    _terminal_shape(outcome, decision, "pre_effect_cancel_basis_unusable", _WorkBudget(33))


def validate_terminal_outcome_binding(*, basis: RW0PhaseEntryBasisV1,
    outcome: RW0TerminalOutcomeV1, decision: DevelopmentDecisionRowValue,
    program_head: DevelopmentProgramHeadRowValue,
    work_head: DevelopmentWorkItemHeadRowValue,
    selection_head: DevelopmentPreExecutionSelectionHeadRowValue,
    effect_head: DevelopmentEffectHeadRowValue,
    delivery_head: DevelopmentDeliveryHeadRowValue,
    global_stop: GlobalStopCurrentRecordEnvelope) -> None:
    budget = _WorkBudget(159)
    _value(budget, basis, RW0PhaseEntryBasisV1)
    _value(budget, outcome, RW0TerminalOutcomeV1)
    for label, obj, kind in (
        ("decision", decision, DevelopmentDecisionRowValue),
        ("program_head", program_head, DevelopmentProgramHeadRowValue),
        ("work_head", work_head, DevelopmentWorkItemHeadRowValue),
        ("selection_head", selection_head, DevelopmentPreExecutionSelectionHeadRowValue),
        ("effect_head", effect_head, DevelopmentEffectHeadRowValue),
        ("delivery_head", delivery_head, DevelopmentDeliveryHeadRowValue),
        ("global_stop", global_stop, GlobalStopCurrentRecordEnvelope),
    ):
        _leaf(budget, obj, kind, label)
    _basis_pair(outcome, basis)
    _require((outcome.decision_ref, outcome.decision_digest,
              outcome.decision_kind) ==
             (decision.decision_ref, decision.decision_digest,
              decision.decision_kind), "relation_mismatch", "decision")
    for prefix, head in (
        ("program_head", program_head), ("work_item_head", work_head),
        ("selection_head", selection_head), ("effect_head", effect_head),
        ("delivery_head", delivery_head),
    ):
        _require((getattr(outcome, prefix + "_revision"),
                  getattr(outcome, prefix + "_digest")) ==
                 (head.head_revision, head.head_digest),
                 "current_head_or_global_stop_mismatch", prefix)
    _require((basis.selection_head_revision, basis.selection_head_digest,
              basis.current_effect_head_revision, basis.current_effect_head_digest,
              basis.current_delivery_head_revision, basis.current_delivery_head_digest) ==
             (selection_head.head_revision, selection_head.head_digest,
              effect_head.head_revision, effect_head.head_digest,
              delivery_head.head_revision, delivery_head.head_digest),
             "current_head_or_global_stop_mismatch", "basis_heads")
    _stop_matches(outcome, global_stop)
    _stop_matches(basis, global_stop)
    _terminal_shape(outcome, decision, outcome.branch, budget)
