"""Private pure RW0-B2 Wire values and framing; no I/O, authority, or acceptance."""

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
    WorkerCommandV1,
    WorkerExecutionValueError,
    WorkerObservationV1,
    _MISSING as _C2A_MISSING,
    _reconstruct_exact_worker_execution_value,
    validate_delivery_relation,
    validate_observation_relation,
)

__all__: tuple[str, ...] = ()

_REQUEST_SCHEMA = "governed-execution.nwp-rw0-wire-cancellation-request-observation.v1"
_PROCESS_SCHEMA = "governed-execution.nwp-rw0-wire-process-observation.v1"
_PROFILE_SCHEMA = "governed-execution.nwp-rw0-wire-protocol-profile.v1"
_PROFILE_REF = "rw0-wire-nwpf-v1"
_PROFILE_DIGEST = "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454"
_MAGIC = b"NWPF"
_VERSION = 1
_COMMAND_KIND = 1
_RESULT_KIND = 2
_MAX_INT = 9_223_372_036_854_775_807
_CAPS = {1: (5898, 3, 5, 71, 70, 23746), 2: (16627, 4, 8, 77, 169, 66770)}
_PRIVATE_FRAGMENTS = (
    "hostname", "host_key", "ip_address", "endpoint", "username", "bearer",
    "token", "secret", "signature", "trust_root", "prompt", "transcript",
    "stdout", "stderr", "provider", "environment_value", "absolute_path",
    "workspace_path", "store_path",
)
_REF_PREFIXES = ("connector-", "tunnel-", "workspace-", "org-", "organization-", "user-")
_REQUEST_FIELDS = (
    "schema_id", "request_observation_ref", "source_kind", "source_ref",
    "source_invocation_ref", "evidence_ref", "evidence_digest", "program_ref",
    "program_version_ref", "accepted_intent_revision_ref", "work_item_ref",
    "work_item_revision_ref", "semantic_attempt_ref", "candidate_ref",
    "command_ref", "command_digest", "attempt_fence_ref", "attempt_fence_digest",
    "cancellation_effect_intent_ref", "cancellation_effect_fence_ref",
    "cancellation_effect_fence_digest", "cancellation_delivery_attempt_ref",
    "cancellation_delivery_envelope_digest", "target_effect_intent_ref",
    "target_effect_fence_ref", "target_effect_fence_digest",
    "target_delivery_attempt_ref", "target_delivery_envelope_digest",
    "observed_at", "request_observation_digest",
)
_PROCESS_FIELDS = (
    "schema_id", "process_observation_ref", "source_kind", "source_ref",
    "source_invocation_ref", "evidence_ref", "evidence_digest", "event_kind",
    "program_ref", "program_version_ref", "accepted_intent_revision_ref",
    "work_item_ref", "work_item_revision_ref", "semantic_attempt_ref",
    "candidate_ref", "command_ref", "command_digest", "attempt_fence_ref",
    "attempt_fence_digest", "effect_intent_ref", "effect_fence_ref",
    "effect_fence_digest", "delivery_attempt_ref",
    "delivery_envelope_digest", "observed_at", "process_observation_digest",
)
_REQUEST_SOURCES = ("supervisor", "execution_substrate")
_PROCESS_SOURCES = ("supervisor", "operating_system")
_PROCESS_EVENTS = ("resource_limit_exceeded", "signal_delivered")
_RESULT_SEQUENCES = (
    ("worker_started", "worker_completed"),
    ("worker_started", "candidate_captured", "worker_completed"),
)
_ADAPTER_FACTS = (
    "cancellation_acknowledged", "cancellation_rejected",
    "deadline_elapsed", "process_exited",
)
_CLASSIFICATIONS = ("usable", "unusable", "invalid")
_REASONS = (
    "usable", "invalid_input", "unrelated_fact", "duplicate_fact",
    "conflicting_fact", "cancellation_graph_mismatch",
    "resource_limit_exceeded", "deadline_elapsed", "signal_delivered",
    "cancellation_request_pending", "cancellation_acknowledged",
    "cancellation_rejected", "process_result_contradiction", "process_failed",
    "result_missing", "result_invalid", "process_evidence_incomplete",
)
_MATRIX = {
    "usable": ("usable",),
    "invalid": (
        "invalid_input", "unrelated_fact", "duplicate_fact", "conflicting_fact",
        "cancellation_graph_mismatch",
    ),
    "unusable": tuple(reason for reason in _REASONS if reason not in (
        "usable", "invalid_input", "unrelated_fact", "duplicate_fact",
        "conflicting_fact", "cancellation_graph_mismatch",
    )),
}
_DECODER_REASONS = (
    "invalid_outer_type", "short_header", "bad_magic", "unsupported_version",
    "unsupported_kind", "declared_length_over_cap", "truncated_payload",
    "trailing_data", "invalid_utf8", "bom_forbidden", "json_token_invalid",
    "duplicate_key", "invalid_root_or_scalar", "unknown_field",
    "missing_field", "nested_record_invalid", "noncanonical_payload",
    "relation_mismatch", "work_limit_exceeded",
)
_CONSTRUCTION_REASONS = (
    "invalid_field_type", "invalid_field_value", "unknown_field",
    "missing_field", "invalid_length_or_cardinality", "digest_mismatch",
    "privacy_forbidden_material", "relation_mismatch",
)
_ERROR_TOKEN = object()
_WORK_TEST_EXTRA_UNITS = 0
_MAX_SOURCE_MAPPING_KEY_CHARS = 37
_MAX_FRAME_KEY_CHARS = 29
_C2A_FIELD_INVENTORIES = {
    CeilingsV1: (
        "max_active_invocations", "max_candidate_bytes", "max_changed_files",
        "max_cost_microusd", "max_cpu_seconds", "max_deliveries",
        "max_deployments", "max_local_commits", "max_memory_bytes",
        "max_merges", "max_model_input_tokens", "max_model_output_tokens",
        "max_pull_requests", "max_pushes", "max_wall_seconds",
    ),
    AttemptFenceV1: (
        "schema_id", "attempt_fence_ref", "parent_standing_grant_ref",
        "parent_standing_grant_digest", "attempt_authorization_ref",
        "attempt_authorization_digest", "program_ref", "program_version_ref",
        "accepted_intent_revision_ref", "work_item_ref",
        "work_item_revision_ref", "semantic_attempt_ref", "repository_ref",
        "base_git_object_format", "base_git_oid", "path_ceiling",
        "allowed_effect_classes", "aggregate_ceilings", "expires_at",
        "global_stop_ref", "global_stop_version", "attempt_fence_digest",
    ),
    EffectFenceV1: (
        "schema_id", "effect_fence_ref", "parent_standing_grant_ref",
        "parent_standing_grant_digest", "effect_authorization_ref",
        "effect_authorization_digest", "attempt_fence_ref",
        "attempt_fence_digest", "program_ref", "program_version_ref",
        "accepted_intent_revision_ref", "work_item_ref",
        "work_item_revision_ref", "semantic_attempt_ref", "effect_intent_ref",
        "effect_class", "command_ref", "command_digest", "candidate_ref",
        "repository_ref", "base_git_object_format", "base_git_oid",
        "path_ceiling", "effect_ceilings", "expires_at", "global_stop_ref",
        "global_stop_version", "portable_capsule_digest",
        "cancellation_target_effect_intent_ref",
        "cancellation_target_effect_fence_ref",
        "cancellation_target_effect_fence_digest", "effect_fence_digest",
    ),
    WorkerCommandV1: (
        "schema_id", "command_ref", "program_ref", "program_version_ref",
        "accepted_intent_revision_ref", "work_item_ref",
        "work_item_revision_ref", "semantic_attempt_ref", "effect_intent_ref",
        "effect_class", "candidate_ref", "repository_ref",
        "base_git_object_format", "base_git_oid", "path_ceiling",
        "work_spec_ref", "work_spec_digest", "standing_grant_ref",
        "standing_grant_digest", "attempt_authorization_ref",
        "attempt_authorization_digest", "effect_authorization_ref",
        "effect_authorization_digest", "attempt_fence_ref",
        "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest",
        "global_stop_ref", "global_stop_version", "validation_requirement_ref",
        "validation_requirement_digest", "review_requirement_ref",
        "review_requirement_digest", "capsule_schema_id",
        "capsule_profile_ref", "effect_ceilings", "privacy_classification",
        "redaction_profile_ref", "command_digest",
    ),
    DeliveryEnvelopeV1: (
        "schema_id", "delivery_attempt_ref", "program_ref",
        "program_version_ref", "command_ref", "command_digest",
        "semantic_attempt_ref", "effect_intent_ref", "attempt_fence_ref",
        "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest",
        "adapter_kind", "adapter_safe_correlation_ref",
        "delivery_envelope_digest",
    ),
    WorkerObservationV1: (
        "schema_id", "observation_ref", "source_kind", "source_ref",
        "source_invocation_ref", "delivery_attempt_ref", "program_ref",
        "program_version_ref", "accepted_intent_revision_ref", "work_item_ref",
        "work_item_revision_ref", "semantic_attempt_ref", "effect_intent_ref",
        "command_ref", "command_digest", "attempt_fence_ref",
        "attempt_fence_digest", "effect_fence_ref", "effect_fence_digest",
        "observation_kind", "outcome", "reason_code", "evidence_refs",
        "observed_at", "candidate_ref", "capsule_manifest_ref",
        "portable_capsule_digest", "process_exit_code", "observation_digest",
    ),
}


class RW0WireProtocolError(ValueError):
    """Closed, content-free Wire failure."""

    __slots__ = ("_reason",)

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled") from None

    def __init__(self, token: object, reason: str) -> None:
        if token is not _ERROR_TOKEN or reason not in _DECODER_REASONS + _CONSTRUCTION_REASONS:
            raise TypeError("sealed error") from None
        object.__setattr__(self, "_reason", reason)
        ValueError.__init__(self, "RW0WireProtocolError")

    @property
    def reason(self) -> str:
        return self._reason

    def __str__(self) -> str:
        return "RW0WireProtocolError"

    def __repr__(self) -> str:
        return "RW0WireProtocolError"

    def __setattr__(self, name: str, value: object) -> typing.NoReturn:
        raise AttributeError("immutable") from None

    def __reduce_ex__(self, protocol: int) -> typing.NoReturn:
        raise TypeError("non-pickleable") from None


class _WireFailure(Exception):
    """Internal-only reason carrier; never crosses a public Wire boundary."""

    __slots__ = ("reason",)

    def __init__(self, reason: str) -> None:
        self.reason = reason
        Exception.__init__(self)


class _BoundaryFailure:
    __slots__ = ("reason",)

    def __init__(self, reason: str) -> None:
        self.reason = reason


def _fail(reason: str) -> typing.NoReturn:
    raise _WireFailure(reason)


def _capture(
    call: typing.Callable[..., object], fallback: str, *arguments: object,
) -> object:
    try:
        return call(*arguments)
    except _WireFailure as caught:
        reason = caught.reason
    except Exception:
        reason = fallback
    return _BoundaryFailure(reason)


def _raise_public(reason: str) -> typing.NoReturn:
    raise RW0WireProtocolError(_ERROR_TOKEN, reason) from None


def _unwrap(outcome: object) -> object:
    if type(outcome) is _BoundaryFailure:
        reason = typing.cast(_BoundaryFailure, outcome).reason
        outcome = None
        _raise_public(reason)
    return outcome


def _relation(condition: bool) -> None:
    if not condition:
        _fail("relation_mismatch")


def _closed_mapping(value: object, fields: tuple[str, ...]) -> dict[str, object]:
    if type(value) is not dict:
        _fail("invalid_field_type")
    mapping = typing.cast(dict[object, object], value)
    if len(mapping) > len(fields) + 1:
        _fail("invalid_length_or_cardinality")
    for key in mapping:
        if type(key) is not str:
            _fail("invalid_field_type")
        if len(key) > _MAX_SOURCE_MAPPING_KEY_CHARS:
            _fail("invalid_length_or_cardinality")
        if not key.isascii():
            _fail("unknown_field")
        if key not in fields:
            lowered = key.lower()
            if any(part in lowered for part in _PRIVATE_FRAGMENTS):
                _fail("privacy_forbidden_material")
            _fail("unknown_field")
    if any(field not in mapping for field in fields):
        _fail("missing_field")
    return typing.cast(dict[str, object], mapping)


def _safe_ref(value: object) -> str:
    if type(value) is not str:
        _fail("invalid_field_type")
    result = typing.cast(str, value)
    if (not 1 <= len(result) <= 96
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", result) is None
        or result.lower().startswith(_REF_PREFIXES)):
        _fail("invalid_field_value")
    if re.fullmatch(r"[0-9]{1,3}(?:\.[0-9]{1,3}){3}", result) is not None:
        _fail("privacy_forbidden_material")
    return result


def _digest(value: object) -> str:
    if type(value) is not str:
        _fail("invalid_field_type")
    if re.fullmatch(r"[0-9a-f]{64}", typing.cast(str, value)) is None:
        _fail("invalid_field_value")
    return typing.cast(str, value)


def _timestamp(value: object) -> str:
    if type(value) is not str:
        _fail("invalid_field_type")
    result = typing.cast(str, value)
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", result) is None:
        _fail("invalid_field_value")
    failed = False
    try:
        parsed = datetime.datetime.strptime(result, "%Y-%m-%dT%H:%M:%SZ")
        if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != result:
            failed = True
    except ValueError:
        failed = True
    if failed:
        _fail("invalid_field_value")
    return result


def _canonical(payload: object) -> bytes:
    failed = False
    encoded = b""
    try:
        encoded = json.dumps(
            payload, ensure_ascii=False, allow_nan=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, OverflowError):
        failed = True
    if failed:
        _fail("invalid_field_value")
    return encoded


def _self_digest(domain: str, identity: dict[str, object]) -> str:
    return hashlib.sha256(domain.encode("utf-8") + b"\0" + _canonical(identity)).hexdigest()


class _ImmutableValue:
    __slots__ = ()
    _FIELDS: tuple[str, ...] = ()

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("construction disabled")

    def __setattr__(self, name: str, value: object) -> typing.NoReturn:
        raise AttributeError("immutable") from None

    def __delattr__(self, name: str) -> typing.NoReturn:
        raise AttributeError("immutable") from None

    def __getattr__(self, name: str) -> object:
        if name in type(self)._FIELDS:
            return object.__getattribute__(self, "_" + name)
        raise AttributeError("unknown attribute") from None

    def __repr__(self) -> str:
        return type(self).__name__

    __str__ = __repr__

    def __reduce_ex__(self, protocol: int) -> typing.NoReturn:
        raise TypeError("non-pickleable") from None

    def to_mapping(self) -> dict[str, object]:
        outcome = _capture(_wire_value_mapping_impl, "invalid_field_value", self)
        self = None
        return typing.cast(dict[str, object], _unwrap(outcome))


def _construct(cls: type[_ImmutableValue], fields: tuple[str, ...], mapping: dict[str, object]) -> _ImmutableValue:
    result = object.__new__(cls)
    for field in fields:
        object.__setattr__(result, "_" + field, mapping[field])
    return result


def _raw_slots(value: _ImmutableValue, fields: tuple[str, ...]) -> dict[str, object]:
    failed = False
    mapping: dict[str, object] = {}
    try:
        for field in fields:
            mapping[field] = object.__getattribute__(value, "_" + field)
    except AttributeError:
        failed = True
    if failed:
        _fail("invalid_field_value")
    return mapping


def _request_from_mapping_impl(
    value: object,
) -> RW0WireCancellationRequestObservationV1:
    mapping = _closed_mapping(value, _REQUEST_FIELDS)
    safe: dict[str, object] = {}
    for field in _REQUEST_FIELDS:
        item = mapping[field]
        if field == "schema_id":
            if type(item) is not str:
                _fail("invalid_field_type")
            if item != _REQUEST_SCHEMA:
                _fail("invalid_field_value")
            safe[field] = item
        elif field == "source_kind":
            if type(item) is not str:
                _fail("invalid_field_type")
            if item not in _REQUEST_SOURCES:
                _fail("invalid_field_value")
            safe[field] = item
        elif field.endswith("_digest"):
            safe[field] = _digest(item)
        elif field == "observed_at":
            safe[field] = _timestamp(item)
        else:
            safe[field] = _safe_ref(item)
    identity = {field: safe[field] for field in _REQUEST_FIELDS[:-1]}
    if safe["request_observation_digest"] != _self_digest(
        _REQUEST_SCHEMA + ".identity", identity,
    ):
        _fail("digest_mismatch")
    return typing.cast(
        RW0WireCancellationRequestObservationV1,
        _construct(RW0WireCancellationRequestObservationV1, _REQUEST_FIELDS, safe),
    )


def _process_from_mapping_impl(value: object) -> RW0WireProcessObservationV1:
    mapping = _closed_mapping(value, _PROCESS_FIELDS)
    safe: dict[str, object] = {}
    for field in _PROCESS_FIELDS:
        item = mapping[field]
        if field == "schema_id":
            if type(item) is not str:
                _fail("invalid_field_type")
            if item != _PROCESS_SCHEMA:
                _fail("invalid_field_value")
            safe[field] = item
        elif field == "source_kind":
            if type(item) is not str:
                _fail("invalid_field_type")
            if item not in _PROCESS_SOURCES:
                _fail("invalid_field_value")
            safe[field] = item
        elif field == "event_kind":
            if type(item) is not str:
                _fail("invalid_field_type")
            if item not in _PROCESS_EVENTS:
                _fail("invalid_field_value")
            safe[field] = item
        elif field.endswith("_digest"):
            safe[field] = _digest(item)
        elif field == "observed_at":
            safe[field] = _timestamp(item)
        else:
            safe[field] = _safe_ref(item)
    identity = {field: safe[field] for field in _PROCESS_FIELDS[:-1]}
    if safe["process_observation_digest"] != _self_digest(
        _PROCESS_SCHEMA + ".identity", identity,
    ):
        _fail("digest_mismatch")
    return typing.cast(
        RW0WireProcessObservationV1,
        _construct(RW0WireProcessObservationV1, _PROCESS_FIELDS, safe),
    )


class RW0WireCancellationRequestObservationV1(_ImmutableValue):
    _FIELDS = _REQUEST_FIELDS
    __slots__ = tuple("_" + field for field in _FIELDS)
    _DOMAIN = _REQUEST_SCHEMA + ".identity"

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled") from None

    @classmethod
    def from_mapping(cls, value: object) -> RW0WireCancellationRequestObservationV1:
        outcome = _capture(_request_from_mapping_impl, "invalid_field_value", value)
        value = None
        return typing.cast(RW0WireCancellationRequestObservationV1, _unwrap(outcome))

    def identity_mapping(self) -> dict[str, object]:
        outcome = _capture(_request_identity_impl, "invalid_field_value", self)
        self = None
        return typing.cast(dict[str, object], _unwrap(outcome))

    def canonical_identity_bytes(self) -> bytes:
        outcome = _capture(_request_canonical_impl, "invalid_field_value", self)
        self = None
        return typing.cast(bytes, _unwrap(outcome))

    def computed_digest(self) -> str:
        outcome = _capture(_request_digest_impl, "invalid_field_value", self)
        self = None
        return typing.cast(str, _unwrap(outcome))


class RW0WireProcessObservationV1(_ImmutableValue):
    _FIELDS = _PROCESS_FIELDS
    __slots__ = tuple("_" + field for field in _FIELDS)
    _DOMAIN = _PROCESS_SCHEMA + ".identity"

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled") from None

    @classmethod
    def from_mapping(cls, value: object) -> RW0WireProcessObservationV1:
        outcome = _capture(_process_from_mapping_impl, "invalid_field_value", value)
        value = None
        return typing.cast(RW0WireProcessObservationV1, _unwrap(outcome))

    def identity_mapping(self) -> dict[str, object]:
        outcome = _capture(_process_identity_impl, "invalid_field_value", self)
        self = None
        return typing.cast(dict[str, object], _unwrap(outcome))

    def canonical_identity_bytes(self) -> bytes:
        outcome = _capture(_process_canonical_impl, "invalid_field_value", self)
        self = None
        return typing.cast(bytes, _unwrap(outcome))

    def computed_digest(self) -> str:
        outcome = _capture(_process_digest_impl, "invalid_field_value", self)
        self = None
        return typing.cast(str, _unwrap(outcome))


class RW0WireWorkerResultV1(_ImmutableValue):
    _FIELDS = ("observations",)
    __slots__ = ("_observations",)

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled") from None

    @classmethod
    def _create(
        cls, observations: tuple[WorkerObservationV1, ...],
    ) -> RW0WireWorkerResultV1:
        outcome = _capture(_worker_result_create_impl, "invalid_field_value", observations)
        observations = None
        return typing.cast(RW0WireWorkerResultV1, _unwrap(outcome))

    def to_mapping(self) -> dict[str, object]:
        outcome = _capture(_wire_value_mapping_impl, "invalid_field_value", self)
        self = None
        return typing.cast(dict[str, object], _unwrap(outcome))


class RW0WireProcessResultClassificationV1(_ImmutableValue):
    _FIELDS = ("classification", "reason")
    __slots__ = ("_classification", "_reason")

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled") from None

    @classmethod
    def _create(
        cls, classification: str, reason: str,
    ) -> RW0WireProcessResultClassificationV1:
        outcome = _capture(
            _classification_create_impl, "invalid_field_value", classification, reason,
        )
        classification = None
        reason = None
        return typing.cast(RW0WireProcessResultClassificationV1, _unwrap(outcome))


class _SafeC2AExtraction:
    __slots__ = ("mapping", "inspections")

    def __init__(self, mapping: dict[str, object], inspections: int) -> None:
        self.mapping = mapping
        self.inspections = inspections


def _safe_c2a_integer(value: object) -> int:
    if type(value) is not int or value > _MAX_INT:
        _fail("invalid_field_value")
    return typing.cast(int, value)


def _safe_c2a_extract(
    value: object, expected: type[object],
) -> _SafeC2AExtraction:
    inventory = _C2A_FIELD_INVENTORIES.get(expected)
    if inventory is None:
        _fail("invalid_field_value")
    if type(value) is not expected:
        _fail("invalid_field_type")
    fields = expected._FIELDS  # type: ignore[attr-defined]
    if type(fields) is not tuple or fields != inventory:
        _fail("invalid_field_value")

    mapping: dict[str, object] = {}
    inspections = 0
    for field in inventory:
        try:
            item = object.__getattribute__(value, "_" + field)
        except AttributeError:
            _fail("invalid_field_value")
        inspections += 1

        if expected is CeilingsV1:
            mapping[field] = _safe_c2a_integer(item)
            continue

        if field == "path_ceiling":
            if type(item) is not tuple or len(item) != 3:
                _fail("invalid_field_value")
            paths: list[str] = []
            for index in range(3):
                member = item[index]
                inspections += 1
                if type(member) is not str:
                    _fail("invalid_field_value")
                paths.append(member)
            mapping[field] = paths
            continue

        if field == "allowed_effect_classes":
            if type(item) is not tuple or not 1 <= len(item) <= 5:
                _fail("invalid_field_value")
            effect_classes: list[str] = []
            for index in range(len(item)):
                member = item[index]
                inspections += 1
                if type(member) is not str:
                    _fail("invalid_field_value")
                effect_classes.append(member)
            mapping[field] = effect_classes
            continue

        if field == "evidence_refs":
            if type(item) is not tuple or len(item) > 32:
                _fail("invalid_field_value")
            evidence_refs: list[str] = []
            for index in range(len(item)):
                member = item[index]
                inspections += 1
                if type(member) is not str:
                    _fail("invalid_field_value")
                evidence_refs.append(member)
            mapping[field] = evidence_refs
            continue

        if field in ("aggregate_ceilings", "effect_ceilings"):
            nested = _safe_c2a_extract(item, CeilingsV1)
            inspections += nested.inspections
            mapping[field] = nested.mapping
            continue

        if expected is WorkerObservationV1 and field in (
            "candidate_ref", "capsule_manifest_ref", "portable_capsule_digest",
            "process_exit_code",
        ):
            if item is _C2A_MISSING:
                continue
            if field == "process_exit_code":
                item = _safe_c2a_integer(item)
            elif type(item) is not str:
                _fail("invalid_field_value")
            mapping[field] = item
            continue

        if expected is EffectFenceV1 and field in (
            "portable_capsule_digest",
            "cancellation_target_effect_intent_ref",
            "cancellation_target_effect_fence_ref",
            "cancellation_target_effect_fence_digest",
        ):
            if item is not None and type(item) is not str:
                _fail("invalid_field_value")
            mapping[field] = item
            continue

        if field == "global_stop_version":
            mapping[field] = _safe_c2a_integer(item)
            continue

        if type(item) is not str:
            _fail("invalid_field_value")
        mapping[field] = item

    return _SafeC2AExtraction(mapping, inspections)


def _rebuild_safe_c2a(
    extracted: _SafeC2AExtraction, expected: type[object],
) -> object:
    failed = False
    rebuilt: object | None = None
    try:
        rebuilt = expected.from_mapping(extracted.mapping)  # type: ignore[attr-defined]
    except Exception:
        failed = True
    extracted.mapping = {}
    if failed or type(rebuilt) is not expected:
        _fail("invalid_field_value")
    return rebuilt


def _rebuild_c2a(value: object, expected: type[object]) -> object:
    extracted = _safe_c2a_extract(value, expected)
    value = None
    return _rebuild_safe_c2a(extracted, expected)


def _validated_request(
    value: object,
) -> RW0WireCancellationRequestObservationV1:
    if type(value) is not RW0WireCancellationRequestObservationV1:
        _fail("invalid_field_type")
    mapping = _raw_slots(typing.cast(_ImmutableValue, value), _REQUEST_FIELDS)
    failed = False
    rebuilt: RW0WireCancellationRequestObservationV1 | None = None
    try:
        rebuilt = _request_from_mapping_impl(mapping)
    except _WireFailure:
        failed = True
    value = None
    mapping = {}
    if failed or rebuilt is None:
        _fail("invalid_field_value")
    return rebuilt


def _validated_process(value: object) -> RW0WireProcessObservationV1:
    if type(value) is not RW0WireProcessObservationV1:
        _fail("invalid_field_type")
    mapping = _raw_slots(typing.cast(_ImmutableValue, value), _PROCESS_FIELDS)
    failed = False
    rebuilt: RW0WireProcessObservationV1 | None = None
    try:
        rebuilt = _process_from_mapping_impl(mapping)
    except _WireFailure:
        failed = True
    value = None
    mapping = {}
    if failed or rebuilt is None:
        _fail("invalid_field_value")
    return rebuilt


def _worker_result_create_impl(observations: object) -> RW0WireWorkerResultV1:
    if type(observations) is not tuple or len(observations) not in (2, 3):
        _fail("invalid_length_or_cardinality")
    raw = typing.cast(tuple[object, ...], observations)
    if any(type(item) is not WorkerObservationV1 for item in raw):
        _fail("invalid_field_type")
    extracted = tuple(
        _safe_c2a_extract(item, WorkerObservationV1) for item in raw
    )
    rebuilt = tuple(
        typing.cast(
            WorkerObservationV1,
            _rebuild_safe_c2a(item, WorkerObservationV1),
        )
        for item in extracted
    )
    if tuple(item.observation_kind for item in rebuilt) not in _RESULT_SEQUENCES:
        _fail("invalid_field_value")
    return typing.cast(
        RW0WireWorkerResultV1,
        _construct(RW0WireWorkerResultV1, ("observations",), {"observations": rebuilt}),
    )


def _validated_result(value: object) -> RW0WireWorkerResultV1:
    if type(value) is not RW0WireWorkerResultV1:
        _fail("invalid_field_type")
    failed = False
    observations: object = None
    try:
        observations = object.__getattribute__(value, "_observations")
    except AttributeError:
        failed = True
    value = None
    if failed:
        _fail("invalid_field_value")
    try:
        return _worker_result_create_impl(observations)
    except _WireFailure:
        failed = True
    observations = None
    if failed:
        _fail("invalid_field_value")
    raise AssertionError("unreachable")


def _classification_create_impl(
    classification: object, reason: object,
) -> RW0WireProcessResultClassificationV1:
    if type(classification) is not str or type(reason) is not str:
        _fail("invalid_field_type")
    if classification not in _CLASSIFICATIONS or reason not in _MATRIX[classification]:
        _fail("invalid_field_value")
    return typing.cast(
        RW0WireProcessResultClassificationV1,
        _construct(
            RW0WireProcessResultClassificationV1,
            ("classification", "reason"),
            {"classification": classification, "reason": reason},
        ),
    )


def _validated_classification(
    value: object,
) -> RW0WireProcessResultClassificationV1:
    if type(value) is not RW0WireProcessResultClassificationV1:
        _fail("invalid_field_type")
    mapping = _raw_slots(
        typing.cast(_ImmutableValue, value), ("classification", "reason"),
    )
    failed = False
    rebuilt: RW0WireProcessResultClassificationV1 | None = None
    try:
        rebuilt = _classification_create_impl(
            mapping["classification"], mapping["reason"],
        )
    except _WireFailure:
        failed = True
    value = None
    mapping = {}
    if failed or rebuilt is None:
        _fail("invalid_field_value")
    return rebuilt


def _wire_value_mapping_impl(value: object) -> dict[str, object]:
    if type(value) is RW0WireCancellationRequestObservationV1:
        rebuilt = _validated_request(value)
        return _raw_slots(rebuilt, _REQUEST_FIELDS)
    if type(value) is RW0WireProcessObservationV1:
        rebuilt = _validated_process(value)
        return _raw_slots(rebuilt, _PROCESS_FIELDS)
    if type(value) is RW0WireWorkerResultV1:
        rebuilt_result = _validated_result(value)
        return {
            "observations": [
                item.to_mapping() for item in rebuilt_result.observations
            ],
        }
    if type(value) is RW0WireProcessResultClassificationV1:
        rebuilt_classification = _validated_classification(value)
        return _raw_slots(
            rebuilt_classification, ("classification", "reason"),
        )
    _fail("invalid_field_type")


def _request_identity_impl(value: object) -> dict[str, object]:
    rebuilt = _validated_request(value)
    mapping = _raw_slots(rebuilt, _REQUEST_FIELDS)
    return {field: mapping[field] for field in _REQUEST_FIELDS[:-1]}


def _request_canonical_impl(value: object) -> bytes:
    return _canonical(_request_identity_impl(value))


def _request_digest_impl(value: object) -> str:
    return _self_digest(
        _REQUEST_SCHEMA + ".identity", _request_identity_impl(value),
    )


def _process_identity_impl(value: object) -> dict[str, object]:
    rebuilt = _validated_process(value)
    mapping = _raw_slots(rebuilt, _PROCESS_FIELDS)
    return {field: mapping[field] for field in _PROCESS_FIELDS[:-1]}


def _process_canonical_impl(value: object) -> bytes:
    return _canonical(_process_identity_impl(value))


def _process_digest_impl(value: object) -> str:
    return _self_digest(
        _PROCESS_SCHEMA + ".identity", _process_identity_impl(value),
    )


_PROFILE_IDENTITY_JSON = '{"manifest":{"authority":{"acceptance":false,"mechanism_neutral":true,"permission":false,"profile_in_frame":false,"provider_neutral":true},"classifier":{"ack_reject_exclusive":true,"adapter_kinds":["cancellation_acknowledged","cancellation_rejected","deadline_elapsed","process_exited"],"classifications":["usable","unusable","invalid"],"exit_success_code":0,"max_adapter_facts":4,"max_process_facts":2,"max_request_facts":1,"max_total_facts":10,"max_worker_result_facts":3,"precedence":[["invalid_input","duplicate_fact","unrelated_fact","conflicting_fact","cancellation_graph_mismatch"],["resource_limit_exceeded"],["deadline_elapsed"],["signal_delivered"],["cancellation_acknowledged","cancellation_rejected","cancellation_request_pending"],["process_result_contradiction","process_failed"],["result_missing","result_invalid"],["process_evidence_incomplete"],["usable"]],"reasons":["usable","invalid_input","unrelated_fact","duplicate_fact","conflicting_fact","cancellation_graph_mismatch","resource_limit_exceeded","deadline_elapsed","signal_delivered","cancellation_request_pending","cancellation_acknowledged","cancellation_rejected","process_result_contradiction","process_failed","result_missing","result_invalid","process_evidence_incomplete"],"response_requires_request":true},"decoder_errors":["invalid_outer_type","short_header","bad_magic","unsupported_version","unsupported_kind","declared_length_over_cap","truncated_payload","trailing_data","invalid_utf8","bom_forbidden","json_token_invalid","duplicate_key","invalid_root_or_scalar","unknown_field","missing_field","nested_record_invalid","noncanonical_payload","relation_mismatch","work_limit_exceeded"],"frame":{"header":[["magic",0,4],["version",4,1],["kind",5,1],["payload_length",6,2]],"kinds":{"command":1,"worker_result":2},"length_encoding":"uint16-big-endian","magic":"NWPF","one_frame":true,"semantic_identity":false,"version":1},"integer":{"json":"unsigned_decimal_no_sign_or_leading_zero","lower_bound":"owning_field","maximum":9223372036854775807,"preconversion_bounded":true,"type":"exact_builtin_int"},"json":{"allow_nan":false,"bom":false,"canonical_reencode_equals_payload":true,"constants":false,"duplicate_keys":false,"ensure_ascii":false,"floats":false,"normalization":"none","separators":[",",":"],"sort_keys":true,"utf8":"strict"},"payloads":{"command":{"max_bytes":5898,"max_containers":5,"max_depth":3,"max_hostile_units":23746,"max_key_pairs":71,"max_scalar_leaves":70,"records":["WorkerCommandV1","DeliveryEnvelopeV1"],"root_keys":["command","delivery"]},"worker_result":{"max_bytes":16627,"max_containers":8,"max_depth":4,"max_hostile_units":66770,"max_key_pairs":77,"max_scalar_leaves":169,"records":["WorkerObservationV1"],"root_keys":["observations"]}},"process":{"digest_domain":"governed-execution.nwp-rw0-wire-process-observation.v1.identity","event_kinds":["resource_limit_exceeded","signal_delivered"],"schema_id":"governed-execution.nwp-rw0-wire-process-observation.v1","source_authenticity":false,"source_kinds":["supervisor","operating_system"]},"request":{"digest_domain":"governed-execution.nwp-rw0-wire-cancellation-request-observation.v1.identity","schema_id":"governed-execution.nwp-rw0-wire-cancellation-request-observation.v1","source_authenticity":false,"source_kinds":["supervisor","execution_substrate"],"target":"author_candidate"},"result":{"graph":"supplied_exact_fences","order":"tuple","same_source_invocation_ref":true,"same_source_ref":true,"sequences":[["worker_started","worker_completed"],["worker_started","candidate_captured","worker_completed"]],"source_kind":"worker","unique_digests":true,"unique_refs":true},"work":{"classifier_fact":1,"container":1,"container_list_member":"container_only","fixed_closed_relations":"unmetered","header_byte":1,"key_pair":1,"payload_byte_per_pass":1,"payload_passes":["utf8_decode","json_tokenize","canonical_reencode","canonical_compare"],"scalar_leaf":1}},"profile_ref":"rw0-wire-nwpf-v1","schema_id":"governed-execution.nwp-rw0-wire-protocol-profile.v1"}'

def wire_profile_mapping() -> dict[str, object]:
    identity = json.loads(_PROFILE_IDENTITY_JSON)
    return {"schema_id": identity["schema_id"], "profile_ref": identity["profile_ref"],
            "manifest": identity["manifest"], "profile_digest": _PROFILE_DIGEST}


def _c2a_relation(call: typing.Callable[[], None]) -> None:
    failed = False
    try:
        call()
    except WorkerExecutionValueError:
        failed = True
    if failed:
        _fail("relation_mismatch")


def _author_delivery_impl(
    command: object, delivery: object, attempt_fence: object,
    author_effect_fence: object,
) -> tuple[WorkerCommandV1, DeliveryEnvelopeV1, AttemptFenceV1, EffectFenceV1]:
    command_extraction = _safe_c2a_extract(command, WorkerCommandV1)
    delivery_extraction = _safe_c2a_extract(delivery, DeliveryEnvelopeV1)
    attempt_extraction = _safe_c2a_extract(attempt_fence, AttemptFenceV1)
    author_extraction = _safe_c2a_extract(author_effect_fence, EffectFenceV1)
    command = delivery = attempt_fence = author_effect_fence = None
    safe_command = typing.cast(
        WorkerCommandV1,
        _rebuild_safe_c2a(command_extraction, WorkerCommandV1),
    )
    safe_delivery = typing.cast(
        DeliveryEnvelopeV1,
        _rebuild_safe_c2a(delivery_extraction, DeliveryEnvelopeV1),
    )
    safe_attempt = typing.cast(
        AttemptFenceV1,
        _rebuild_safe_c2a(attempt_extraction, AttemptFenceV1),
    )
    safe_author = typing.cast(
        EffectFenceV1,
        _rebuild_safe_c2a(author_extraction, EffectFenceV1),
    )
    _c2a_relation(lambda: validate_delivery_relation(
        delivery=safe_delivery, author_command=safe_command,
        attempt_fence=safe_attempt, author_effect_fence=safe_author,
        effect_fence=safe_author,
    ))
    return safe_command, safe_delivery, safe_attempt, safe_author


def _validate_wire_cancellation_request_relation_impl(
    request: object, author_command: object, attempt_fence: object,
    author_effect_fence: object, target_effect_fence: object,
    target_delivery: object, cancellation_effect_fence: object,
    cancellation_delivery: object,
) -> None:
    safe_request = _validated_request(request)
    safe_command = typing.cast(
        WorkerCommandV1, _rebuild_c2a(author_command, WorkerCommandV1),
    )
    safe_attempt = typing.cast(
        AttemptFenceV1, _rebuild_c2a(attempt_fence, AttemptFenceV1),
    )
    safe_author = typing.cast(
        EffectFenceV1, _rebuild_c2a(author_effect_fence, EffectFenceV1),
    )
    safe_target = typing.cast(
        EffectFenceV1, _rebuild_c2a(target_effect_fence, EffectFenceV1),
    )
    safe_target_delivery = typing.cast(
        DeliveryEnvelopeV1, _rebuild_c2a(target_delivery, DeliveryEnvelopeV1),
    )
    safe_cancel = typing.cast(
        EffectFenceV1, _rebuild_c2a(cancellation_effect_fence, EffectFenceV1),
    )
    safe_cancel_delivery = typing.cast(
        DeliveryEnvelopeV1,
        _rebuild_c2a(cancellation_delivery, DeliveryEnvelopeV1),
    )
    _relation(safe_target.effect_class == "author_candidate")
    _relation(safe_cancel.effect_class == "cancel_effect")
    _c2a_relation(lambda: validate_delivery_relation(
        delivery=safe_target_delivery, author_command=safe_command,
        attempt_fence=safe_attempt, author_effect_fence=safe_author,
        effect_fence=safe_target,
    ))
    _c2a_relation(lambda: validate_delivery_relation(
        delivery=safe_cancel_delivery, author_command=safe_command,
        attempt_fence=safe_attempt, author_effect_fence=safe_author,
        effect_fence=safe_cancel, cancellation_target=safe_target,
    ))
    _relation((
        safe_cancel.cancellation_target_effect_intent_ref,
        safe_cancel.cancellation_target_effect_fence_ref,
        safe_cancel.cancellation_target_effect_fence_digest,
    ) == (
        safe_target.effect_intent_ref,
        safe_target.effect_fence_ref,
        safe_target.effect_fence_digest,
    ))
    bindings = (
        ("program_ref", safe_command.program_ref),
        ("program_version_ref", safe_command.program_version_ref),
        ("accepted_intent_revision_ref", safe_command.accepted_intent_revision_ref),
        ("work_item_ref", safe_command.work_item_ref),
        ("work_item_revision_ref", safe_command.work_item_revision_ref),
        ("semantic_attempt_ref", safe_command.semantic_attempt_ref),
        ("candidate_ref", safe_command.candidate_ref),
        ("command_ref", safe_command.command_ref),
        ("command_digest", safe_command.command_digest),
        ("attempt_fence_ref", safe_attempt.attempt_fence_ref),
        ("attempt_fence_digest", safe_attempt.attempt_fence_digest),
        ("cancellation_effect_intent_ref", safe_cancel.effect_intent_ref),
        ("cancellation_effect_fence_ref", safe_cancel.effect_fence_ref),
        ("cancellation_effect_fence_digest", safe_cancel.effect_fence_digest),
        ("cancellation_delivery_attempt_ref", safe_cancel_delivery.delivery_attempt_ref),
        ("cancellation_delivery_envelope_digest", safe_cancel_delivery.delivery_envelope_digest),
        ("target_effect_intent_ref", safe_target.effect_intent_ref),
        ("target_effect_fence_ref", safe_target.effect_fence_ref),
        ("target_effect_fence_digest", safe_target.effect_fence_digest),
        ("target_delivery_attempt_ref", safe_target_delivery.delivery_attempt_ref),
        ("target_delivery_envelope_digest", safe_target_delivery.delivery_envelope_digest),
    )
    _relation(all(getattr(safe_request, field) == value for field, value in bindings))
    expected_source = (
        "supervisor"
        if safe_cancel_delivery.adapter_kind == "direct_local_bootstrap"
        else "execution_substrate"
    )
    _relation(safe_request.source_kind == expected_source)


def validate_wire_cancellation_request_relation(
    *, request: RW0WireCancellationRequestObservationV1,
    author_command: WorkerCommandV1, attempt_fence: AttemptFenceV1,
    author_effect_fence: EffectFenceV1, target_effect_fence: EffectFenceV1,
    target_delivery: DeliveryEnvelopeV1, cancellation_effect_fence: EffectFenceV1,
    cancellation_delivery: DeliveryEnvelopeV1,
) -> None:
    outcome = _capture(
        _validate_wire_cancellation_request_relation_impl,
        "invalid_field_value", request, author_command, attempt_fence,
        author_effect_fence, target_effect_fence, target_delivery,
        cancellation_effect_fence, cancellation_delivery,
    )
    request = author_command = attempt_fence = author_effect_fence = None
    target_effect_fence = target_delivery = None
    cancellation_effect_fence = cancellation_delivery = None
    _unwrap(outcome)


def _validate_wire_process_observation_relation_impl(
    observation: object, author_command: object, attempt_fence: object,
    author_effect_fence: object, target_effect_fence: object,
    target_delivery: object,
) -> None:
    safe_observation = _validated_process(observation)
    safe_command = typing.cast(
        WorkerCommandV1, _rebuild_c2a(author_command, WorkerCommandV1),
    )
    safe_attempt = typing.cast(
        AttemptFenceV1, _rebuild_c2a(attempt_fence, AttemptFenceV1),
    )
    safe_author = typing.cast(
        EffectFenceV1, _rebuild_c2a(author_effect_fence, EffectFenceV1),
    )
    safe_target = typing.cast(
        EffectFenceV1, _rebuild_c2a(target_effect_fence, EffectFenceV1),
    )
    safe_delivery = typing.cast(
        DeliveryEnvelopeV1, _rebuild_c2a(target_delivery, DeliveryEnvelopeV1),
    )
    _relation(safe_target.effect_class == "author_candidate")
    _c2a_relation(lambda: validate_delivery_relation(
        delivery=safe_delivery, author_command=safe_command,
        attempt_fence=safe_attempt, author_effect_fence=safe_author,
        effect_fence=safe_target,
    ))
    bindings = (
        ("program_ref", safe_command.program_ref),
        ("program_version_ref", safe_command.program_version_ref),
        ("accepted_intent_revision_ref", safe_command.accepted_intent_revision_ref),
        ("work_item_ref", safe_command.work_item_ref),
        ("work_item_revision_ref", safe_command.work_item_revision_ref),
        ("semantic_attempt_ref", safe_command.semantic_attempt_ref),
        ("candidate_ref", safe_command.candidate_ref),
        ("command_ref", safe_command.command_ref),
        ("command_digest", safe_command.command_digest),
        ("attempt_fence_ref", safe_attempt.attempt_fence_ref),
        ("attempt_fence_digest", safe_attempt.attempt_fence_digest),
        ("effect_intent_ref", safe_target.effect_intent_ref),
        ("effect_fence_ref", safe_target.effect_fence_ref),
        ("effect_fence_digest", safe_target.effect_fence_digest),
        ("delivery_attempt_ref", safe_delivery.delivery_attempt_ref),
        ("delivery_envelope_digest", safe_delivery.delivery_envelope_digest),
    )
    _relation(all(
        getattr(safe_observation, field) == value for field, value in bindings
    ))


def validate_wire_process_observation_relation(
    *, observation: RW0WireProcessObservationV1,
    author_command: WorkerCommandV1, attempt_fence: AttemptFenceV1,
    author_effect_fence: EffectFenceV1, target_effect_fence: EffectFenceV1,
    target_delivery: DeliveryEnvelopeV1,
) -> None:
    outcome = _capture(
        _validate_wire_process_observation_relation_impl,
        "invalid_field_value", observation, author_command, attempt_fence,
        author_effect_fence, target_effect_fence, target_delivery,
    )
    observation = author_command = attempt_fence = author_effect_fence = None
    target_effect_fence = target_delivery = None
    _unwrap(outcome)


def _validate_wire_result_relation_impl(
    result: object, command: object, delivery: object, attempt_fence: object,
    author_effect_fence: object,
) -> None:
    safe_result = _validated_result(result)
    safe_command, safe_delivery, safe_attempt, safe_author = _author_delivery_impl(
        command, delivery, attempt_fence, author_effect_fence,
    )
    observations = safe_result.observations
    _relation(tuple(item.observation_kind for item in observations) in _RESULT_SEQUENCES)
    _relation(all(item.source_kind == "worker" for item in observations))
    _relation(len({item.source_ref for item in observations}) == 1)
    _relation(len({item.source_invocation_ref for item in observations}) == 1)
    _relation(len({item.observation_ref for item in observations}) == len(observations))
    _relation(len({item.observation_digest for item in observations}) == len(observations))
    for observation in observations:
        _c2a_relation(lambda item=observation: validate_observation_relation(
            observation=item, delivery=safe_delivery,
            author_command=safe_command, attempt_fence=safe_attempt,
            author_effect_fence=safe_author, effect_fence=safe_author,
        ))
        _relation(observation.delivery_attempt_ref == safe_delivery.delivery_attempt_ref)
        _relation(observation.effect_intent_ref == safe_author.effect_intent_ref)
    if len(observations) == 3:
        _relation(observations[1].candidate_ref == safe_command.candidate_ref)


def validate_wire_result_relation(
    *, result: RW0WireWorkerResultV1, command: WorkerCommandV1,
    delivery: DeliveryEnvelopeV1, attempt_fence: AttemptFenceV1,
    author_effect_fence: EffectFenceV1,
) -> None:
    outcome = _capture(
        _validate_wire_result_relation_impl, "invalid_field_value",
        result, command, delivery, attempt_fence, author_effect_fence,
    )
    result = command = delivery = attempt_fence = author_effect_fence = None
    _unwrap(outcome)


class _JSONTokenFailure(Exception):
    pass


class _JSONObjectPairs:
    __slots__ = ("pairs",)

    def __init__(self, pairs: list[tuple[str, object]]) -> None:
        self.pairs = tuple(pairs)


class _JSONParseAccounting:
    __slots__ = ("raw_pair_count", "duplicate_seen", "key_shape_invalid")

    def __init__(self) -> None:
        self.raw_pair_count = 0
        self.duplicate_seen = False
        self.key_shape_invalid = False

    def object_pairs(
        self, pairs: list[tuple[str, object]],
    ) -> _JSONObjectPairs:
        self.raw_pair_count += len(pairs)
        seen: set[str] = set()
        for key, _ in pairs:
            if type(key) is not str:
                self.key_shape_invalid = True
            else:
                if key in seen:
                    self.duplicate_seen = True
                else:
                    seen.add(key)
                if len(key) > _MAX_FRAME_KEY_CHARS:
                    self.key_shape_invalid = True
        return _JSONObjectPairs(pairs)


def _parse_integer(token: str) -> int:
    if len(token) > 19 or token.startswith("-") or (
        len(token) == 19 and token > str(_MAX_INT)
    ):
        raise _JSONTokenFailure from None
    return int(token)


def _parse_forbidden(token: str) -> typing.NoReturn:
    raise _JSONTokenFailure from None


def _decode_json(payload: bytes) -> tuple[object, _JSONParseAccounting]:
    failed = False
    text = ""
    try:
        text = payload.decode("utf-8", "strict")
    except UnicodeDecodeError:
        failed = True
    if failed:
        _fail("invalid_utf8")
    if text.startswith("\ufeff"):
        _fail("bom_forbidden")
    tree: object = None
    accounting = _JSONParseAccounting()
    failed = False
    try:
        tree = json.loads(
            text, object_pairs_hook=accounting.object_pairs,
            parse_int=_parse_integer,
            parse_float=_parse_forbidden, parse_constant=_parse_forbidden,
        )
    except (json.JSONDecodeError, _JSONTokenFailure, ValueError, RecursionError):
        failed = True
    text = ""
    if failed:
        _fail("json_token_invalid")
    return tree, accounting


def _assign_reconstructed(parent: object, locator: object, value: object) -> None:
    if type(parent) is dict:
        mapping = typing.cast(dict[object, object], parent)
        mapping[locator] = value
    else:
        items = typing.cast(list[object], parent)
        index = typing.cast(int, locator)
        if index != len(items):
            _fail("invalid_root_or_scalar")
        items.append(value)


class _ShapeFrame:
    __slots__ = (
        "container", "iterator", "depth", "output", "object_frame", "seen",
    )

    def __init__(
        self, container: object, iterator: object, depth: int, output: object,
        object_frame: bool, seen: set[str] | None,
    ) -> None:
        self.container = container
        self.iterator = iterator
        self.depth = depth
        self.output = output
        self.object_frame = object_frame
        self.seen = seen


class _ShapeWorkResult:
    __slots__ = (
        "tree", "units", "structural", "duplicate", "max_pending_frames",
    )

    def __init__(
        self, tree: object, units: int, structural: bool, duplicate: bool,
        max_pending_frames: int,
    ) -> None:
        self.tree = tree
        self.units = units
        self.structural = structural
        self.duplicate = duplicate
        self.max_pending_frames = max_pending_frames


def _shape_work(
    tree: object, kind: int, payload_length: int,
    accounting: _JSONParseAccounting | None = None,
) -> _ShapeWorkResult:
    _, max_depth, max_containers, max_keys, max_scalars, _ = _CAPS[kind]
    containers = scalars = 0
    keys = 0 if accounting is None else accounting.raw_pair_count
    duplicate = False
    structural = (
        accounting is not None
        and (accounting.key_shape_invalid or keys > max_keys)
    )
    root: dict[str, object] = {}
    stack: list[_ShapeFrame] = []
    pending: tuple[object, int, object, object] | None = (
        tree, 1, root, "value",
    )
    max_pending_frames = 0

    while not structural and (pending is not None or stack):
        if pending is None:
            frame = stack[-1]
            try:
                next_item = next(frame.iterator)  # type: ignore[arg-type]
            except StopIteration:
                stack.pop()
                continue
            if frame.object_frame:
                key, item = typing.cast(tuple[object, object], next_item)
                if type(key) is not str or len(key) > _MAX_FRAME_KEY_CHARS:
                    structural = True
                    break
                if frame.seen is not None:
                    if key in frame.seen:
                        duplicate = True
                        break
                    frame.seen.add(key)
                pending = (item, frame.depth + 1, frame.output, key)
            else:
                items = typing.cast(list[object], frame.output)
                pending = (
                    next_item, frame.depth + 1, items, len(items),
                )
            continue

        value, depth, parent, locator = pending
        pending = None
        if type(value) in (_JSONObjectPairs, dict):
            containers += 1
            if containers > max_containers or depth > max_depth:
                structural = True
                break
            pair_count = (
                len(typing.cast(_JSONObjectPairs, value).pairs)
                if type(value) is _JSONObjectPairs
                else len(typing.cast(dict[object, object], value))
            )
            if accounting is None:
                if keys + pair_count > max_keys:
                    structural = True
                    break
                keys += pair_count
            reconstructed: dict[object, object] = {}
            _assign_reconstructed(parent, locator, reconstructed)
            iterator = iter(
                typing.cast(_JSONObjectPairs, value).pairs
                if type(value) is _JSONObjectPairs
                else typing.cast(dict[object, object], value).items()
            )
            seen = (
                set()
                if accounting is None and type(value) is _JSONObjectPairs
                else None
            )
            stack.append(
                _ShapeFrame(value, iterator, depth, reconstructed, True, seen),
            )
            max_pending_frames = max(max_pending_frames, len(stack))
        elif type(value) is list:
            containers += 1
            if containers > max_containers or depth > max_depth:
                structural = True
                break
            items = typing.cast(list[object], value)
            if len(items) > max_containers + max_scalars:
                structural = True
                break
            reconstructed_list: list[object] = []
            _assign_reconstructed(parent, locator, reconstructed_list)
            stack.append(
                _ShapeFrame(
                    value, iter(items), depth, reconstructed_list, False, None,
                ),
            )
            max_pending_frames = max(max_pending_frames, len(stack))
        elif type(value) in (str, int) or value is None:
            if type(value) is int and (value < 0 or value > _MAX_INT):
                structural = True
                break
            scalars += 1
            if scalars > max_scalars:
                structural = True
                break
            _assign_reconstructed(parent, locator, value)
        else:
            structural = True
            break
    units = 8 + 4 * payload_length + keys + containers + scalars
    return _ShapeWorkResult(
        root.get("value"), units, structural, duplicate, max_pending_frames,
    )


def _complete_work(units: int, kind: int) -> None:
    if units + _WORK_TEST_EXTRA_UNITS > _CAPS[kind][5]:
        _fail("work_limit_exceeded")


def _decode_frame(frame: object, kind: int) -> tuple[object, int, bytes]:
    if type(frame) is not bytes:
        _fail("invalid_outer_type")
    safe_frame = typing.cast(bytes, frame)
    if len(safe_frame) < 8:
        _fail("short_header")
    if safe_frame[:4] != _MAGIC:
        _fail("bad_magic")
    if safe_frame[4] != _VERSION:
        _fail("unsupported_version")
    if safe_frame[5] not in (_COMMAND_KIND, _RESULT_KIND) or safe_frame[5] != kind:
        _fail("unsupported_kind")
    length = int.from_bytes(safe_frame[6:8], "big")
    if length > _CAPS[kind][0]:
        _fail("declared_length_over_cap")
    if len(safe_frame) < 8 + length:
        _fail("truncated_payload")
    if len(safe_frame) > 8 + length:
        _fail("trailing_data")
    payload = safe_frame[8:]
    parsed, accounting = _decode_json(payload)
    if accounting.duplicate_seen:
        parsed = accounting = None
        _fail("duplicate_key")
    scan = _shape_work(parsed, kind, length, accounting)
    parsed = accounting = None
    if scan.duplicate:
        _fail("duplicate_key")
    if scan.structural:
        _fail("invalid_root_or_scalar")
    tree = scan.tree
    if type(tree) is not dict:
        _fail("invalid_root_or_scalar")
    return tree, scan.units, payload


def _root(tree: object, fields: tuple[str, ...]) -> dict[str, object]:
    if type(tree) is not dict: _fail("invalid_root_or_scalar")
    mapping = typing.cast(dict[object, object], tree)
    if any(type(key) is not str or key not in fields for key in mapping):
        _fail("unknown_field")
    if any(field not in mapping for field in fields): _fail("missing_field")
    return typing.cast(dict[str, object], mapping)


def _canonical_payload(tree: object, original: bytes) -> None:
    actual = _canonical(tree)
    if actual != original:
        _fail("noncanonical_payload")


def _frame(kind: int, tree: dict[str, object]) -> bytes:
    payload = _canonical(tree)
    if len(payload) > _CAPS[kind][0]:
        _fail("invalid_length_or_cardinality")
    scan = _shape_work(tree, kind, len(payload))
    if scan.duplicate:
        _fail("duplicate_key")
    if scan.structural:
        _fail("invalid_root_or_scalar")
    _complete_work(scan.units, kind)
    return _MAGIC + bytes((_VERSION, kind)) + len(payload).to_bytes(2, "big") + payload


def _encode_wire_command_frame_impl(
    command: object, delivery: object, attempt_fence: object,
    author_effect_fence: object,
) -> bytes:
    safe_command, safe_delivery, _, _ = _author_delivery_impl(
        command, delivery, attempt_fence, author_effect_fence,
    )
    return _frame(
        _COMMAND_KIND,
        {"command": safe_command.to_mapping(),
         "delivery": safe_delivery.to_mapping()},
    )


def encode_wire_command_frame(
    *, command: WorkerCommandV1, delivery: DeliveryEnvelopeV1,
    attempt_fence: AttemptFenceV1, author_effect_fence: EffectFenceV1,
) -> bytes:
    outcome = _capture(
        _encode_wire_command_frame_impl, "invalid_field_value",
        command, delivery, attempt_fence, author_effect_fence,
    )
    command = delivery = attempt_fence = author_effect_fence = None
    return typing.cast(bytes, _unwrap(outcome))


def _decode_wire_command_frame_impl(
    frame: object, attempt_fence: object, author_effect_fence: object,
) -> tuple[WorkerCommandV1, DeliveryEnvelopeV1]:
    tree, units, payload = _decode_frame(frame, _COMMAND_KIND)
    root = _root(tree, ("command", "delivery"))
    if type(root["command"]) is not dict or type(root["delivery"]) is not dict:
        _fail("nested_record_invalid")
    failed = False
    command: WorkerCommandV1 | None = None
    delivery: DeliveryEnvelopeV1 | None = None
    try:
        command = WorkerCommandV1.from_mapping(root["command"])
        delivery = DeliveryEnvelopeV1.from_mapping(root["delivery"])
    except WorkerExecutionValueError:
        failed = True
    if failed or command is None or delivery is None:
        _fail("nested_record_invalid")
    _canonical_payload(tree, payload)
    safe_command, safe_delivery, _, _ = _author_delivery_impl(
        command, delivery, attempt_fence, author_effect_fence,
    )
    _complete_work(units, _COMMAND_KIND)
    return safe_command, safe_delivery


def decode_wire_command_frame(
    frame: bytes, *, attempt_fence: AttemptFenceV1,
    author_effect_fence: EffectFenceV1,
) -> tuple[WorkerCommandV1, DeliveryEnvelopeV1]:
    outcome = _capture(
        _decode_wire_command_frame_impl, "invalid_field_value",
        frame, attempt_fence, author_effect_fence,
    )
    frame = attempt_fence = author_effect_fence = None
    return typing.cast(
        tuple[WorkerCommandV1, DeliveryEnvelopeV1], _unwrap(outcome),
    )


def _encode_wire_result_frame_impl(
    result: object, command: object, delivery: object, attempt_fence: object,
    author_effect_fence: object,
) -> bytes:
    safe_result = _validated_result(result)
    _validate_wire_result_relation_impl(
        safe_result, command, delivery, attempt_fence, author_effect_fence,
    )
    return _frame(_RESULT_KIND, _wire_value_mapping_impl(safe_result))


def encode_wire_result_frame(
    *, result: RW0WireWorkerResultV1, command: WorkerCommandV1,
    delivery: DeliveryEnvelopeV1, attempt_fence: AttemptFenceV1,
    author_effect_fence: EffectFenceV1,
) -> bytes:
    outcome = _capture(
        _encode_wire_result_frame_impl, "invalid_field_value",
        result, command, delivery, attempt_fence, author_effect_fence,
    )
    result = command = delivery = attempt_fence = author_effect_fence = None
    return typing.cast(bytes, _unwrap(outcome))


def _decode_wire_result_frame_impl(
    frame: object, command: object, delivery: object, attempt_fence: object,
    author_effect_fence: object,
) -> RW0WireWorkerResultV1:
    tree, units, payload = _decode_frame(frame, _RESULT_KIND)
    root = _root(tree, ("observations",))
    items = root["observations"]
    if type(items) is not list or len(items) not in (2, 3):
        _fail("nested_record_invalid")
    observations: list[WorkerObservationV1] = []
    failed = False
    for item in items:
        if type(item) is not dict:
            failed = True
            break
        try:
            observation = WorkerObservationV1.from_mapping(item)
        except WorkerExecutionValueError:
            failed = True
        else:
            observations.append(observation)
        if failed:
            break
    if failed:
        _fail("nested_record_invalid")
    try:
        result = _worker_result_create_impl(tuple(observations))
    except _WireFailure:
        failed = True
    if failed:
        _fail("nested_record_invalid")
    _canonical_payload(tree, payload)
    _validate_wire_result_relation_impl(
        result, command, delivery, attempt_fence, author_effect_fence,
    )
    _complete_work(units, _RESULT_KIND)
    return result


def decode_wire_result_frame(
    frame: bytes, *, command: WorkerCommandV1, delivery: DeliveryEnvelopeV1,
    attempt_fence: AttemptFenceV1, author_effect_fence: EffectFenceV1,
) -> RW0WireWorkerResultV1:
    outcome = _capture(
        _decode_wire_result_frame_impl, "invalid_field_value",
        frame, command, delivery, attempt_fence, author_effect_fence,
    )
    frame = command = delivery = attempt_fence = author_effect_fence = None
    return typing.cast(RW0WireWorkerResultV1, _unwrap(outcome))


def _classified(classification: str, reason: str) -> RW0WireProcessResultClassificationV1:
    return _classification_create_impl(classification, reason)


def _raw_result_observations(value: object) -> tuple[WorkerObservationV1, ...]:
    if type(value) is not RW0WireWorkerResultV1:
        _fail("invalid_field_type")
    failed = False
    raw: object = None
    try:
        raw = object.__getattribute__(value, "_observations")
    except AttributeError:
        failed = True
    if failed or type(raw) is not tuple or len(raw) not in (2, 3):
        _fail("invalid_field_value")
    items = typing.cast(tuple[object, ...], raw)
    if any(type(item) is not WorkerObservationV1 for item in items):
        _fail("invalid_field_value")
    return typing.cast(tuple[WorkerObservationV1, ...], items)


def _valid_result_failure(value: object) -> bool:
    if type(value) is not RW0WireProtocolError:
        return False
    failed = False
    reason: object = None
    try:
        reason = object.__getattribute__(value, "_reason")
        arguments = BaseException.args.__get__(value, RW0WireProtocolError)
    except Exception:
        failed = True
        arguments = ()
    return (
        not failed
        and type(reason) is str
        and reason in _DECODER_REASONS + _CONSTRUCTION_REASONS
        and arguments == ("RW0WireProtocolError",)
    )


def _classify_wire_process_result_impl(
    command: object, delivery: object, attempt_fence: object,
    author_effect_fence: object, result: object, result_failure: object,
    adapter_observations: object, request: object,
    process_observations: object, cancellation_effect_fence: object,
    cancellation_delivery: object,
) -> RW0WireProcessResultClassificationV1:
    if (
        (result is not None and type(result) is not RW0WireWorkerResultV1)
        or (result_failure is not None and not _valid_result_failure(result_failure))
        or (result is not None and result_failure is not None)
        or type(adapter_observations) is not tuple
        or type(process_observations) is not tuple
        or (request is not None
            and type(request) is not RW0WireCancellationRequestObservationV1)
        or (cancellation_effect_fence is not None
            and type(cancellation_effect_fence) is not EffectFenceV1)
        or (cancellation_delivery is not None
            and type(cancellation_delivery) is not DeliveryEnvelopeV1)
        or (cancellation_effect_fence is None) != (cancellation_delivery is None)
    ):
        return _classified("invalid", "invalid_input")
    adapters = typing.cast(tuple[object, ...], adapter_observations)
    processes = typing.cast(tuple[object, ...], process_observations)
    if (
        len(adapters) > 4
        or len(processes) > 2
        or any(type(item) is not WorkerObservationV1 for item in adapters)
        or any(type(item) is not RW0WireProcessObservationV1 for item in processes)
    ):
        return _classified("invalid", "invalid_input")
    try:
        result_items = () if result is None else _raw_result_observations(result)
    except _WireFailure:
        return _classified("invalid", "invalid_input")
    if (
        len(result_items) + len(adapters) + len(processes)
        + int(request is not None) > 10
    ):
        return _classified("invalid", "invalid_input")
    facts: tuple[object, ...] = (
        result_items + adapters + (() if request is None else (request,)) + processes
    )
    original_markers = tuple(id(item) for item in facts)

    try:
        safe_command, safe_delivery, safe_attempt, safe_author = (
            _author_delivery_impl(
                command, delivery, attempt_fence, author_effect_fence,
            )
        )
        safe_result = None if result is None else _validated_result(result)
        safe_adapters = tuple(
            typing.cast(
                WorkerObservationV1,
                _rebuild_c2a(item, WorkerObservationV1),
            )
            for item in adapters
        )
        safe_request = None if request is None else _validated_request(request)
        safe_processes = tuple(_validated_process(item) for item in processes)
        safe_cancel = (
            None if cancellation_effect_fence is None
            else typing.cast(
                EffectFenceV1,
                _rebuild_c2a(cancellation_effect_fence, EffectFenceV1),
            )
        )
        safe_cancel_delivery = (
            None if cancellation_delivery is None
            else typing.cast(
                DeliveryEnvelopeV1,
                _rebuild_c2a(cancellation_delivery, DeliveryEnvelopeV1),
            )
        )
    except _WireFailure:
        return _classified("invalid", "invalid_input")

    safe_result_items = (
        () if safe_result is None else safe_result.observations
    )
    safe_facts: tuple[object, ...] = (
        safe_result_items
        + safe_adapters
        + (() if safe_request is None else (safe_request,))
        + safe_processes
    )
    seen_objects: set[int] = set()
    seen_refs: set[str] = set()
    seen_digests: set[str] = set()
    duplicate = False
    adapter_kinds_list: list[str] = []
    process_kinds_list: list[str] = []
    for marker in original_markers:
        if marker in seen_objects:
            duplicate = True
        seen_objects.add(marker)
    for item in safe_facts:
        if type(item) is WorkerObservationV1:
            observation = typing.cast(WorkerObservationV1, item)
            reference = observation.observation_ref
            digest = observation.observation_digest
        elif type(item) is RW0WireCancellationRequestObservationV1:
            request_fact = typing.cast(
                RW0WireCancellationRequestObservationV1, item,
            )
            reference = request_fact.request_observation_ref
            digest = request_fact.request_observation_digest
        else:
            process_fact = typing.cast(RW0WireProcessObservationV1, item)
            reference = process_fact.process_observation_ref
            digest = process_fact.process_observation_digest
        if reference in seen_refs or digest in seen_digests:
            duplicate = True
        seen_refs.add(reference)
        seen_digests.add(digest)
    for item in safe_adapters:
        adapter_kinds_list.append(item.observation_kind)
    for item in safe_processes:
        process_kinds_list.append(item.event_kind)
    if duplicate:
        return _classified("invalid", "duplicate_fact")

    adapter_kinds = tuple(adapter_kinds_list)
    process_kinds = tuple(process_kinds_list)
    conflict = (
        len(adapter_kinds) != len(set(adapter_kinds))
        or len(process_kinds) != len(set(process_kinds))
        or (
            "cancellation_acknowledged" in adapter_kinds
            and "cancellation_rejected" in adapter_kinds
        )
    )

    for observation in safe_adapters:
        if observation.observation_kind not in _ADAPTER_FACTS:
            return _classified("invalid", "unrelated_fact")
        if observation.observation_kind in (
            "cancellation_acknowledged", "cancellation_rejected",
        ):
            continue
        failed = False
        try:
            _c2a_relation(lambda item=observation: validate_observation_relation(
                observation=item, delivery=safe_delivery,
                author_command=safe_command, attempt_fence=safe_attempt,
                author_effect_fence=safe_author, effect_fence=safe_author,
            ))
        except _WireFailure:
            failed = True
        if failed:
            return _classified("invalid", "unrelated_fact")
    for observation in safe_processes:
        failed = False
        try:
            _validate_wire_process_observation_relation_impl(
                observation, safe_command, safe_attempt, safe_author,
                safe_author, safe_delivery,
            )
        except _WireFailure:
            failed = True
        if failed:
            return _classified("invalid", "unrelated_fact")

    if conflict:
        return _classified("invalid", "conflicting_fact")

    responses = tuple(
        item for item in safe_adapters
        if item.observation_kind in (
            "cancellation_acknowledged", "cancellation_rejected",
        )
    )
    graph_mismatch = False
    if safe_cancel is not None and safe_cancel_delivery is not None:
        try:
            _relation(safe_cancel.effect_class == "cancel_effect")
            _c2a_relation(lambda: validate_delivery_relation(
                delivery=safe_cancel_delivery,
                author_command=safe_command, attempt_fence=safe_attempt,
                author_effect_fence=safe_author, effect_fence=safe_cancel,
                cancellation_target=safe_author,
            ))
        except _WireFailure:
            graph_mismatch = True
    elif safe_request is not None or responses:
        graph_mismatch = True
    if not graph_mismatch and safe_request is not None:
        try:
            _validate_wire_cancellation_request_relation_impl(
                safe_request, safe_command, safe_attempt, safe_author,
                safe_author, safe_delivery, safe_cancel,
                safe_cancel_delivery,
            )
        except _WireFailure:
            graph_mismatch = True
    if not graph_mismatch:
        for response in responses:
            try:
                _c2a_relation(lambda item=response: validate_observation_relation(
                    observation=item, delivery=safe_cancel_delivery,
                    author_command=safe_command, attempt_fence=safe_attempt,
                    author_effect_fence=safe_author,
                    effect_fence=safe_cancel,
                    cancellation_target=safe_author,
                ))
            except _WireFailure:
                graph_mismatch = True
                break
    if graph_mismatch or (responses and safe_request is None):
        return _classified("invalid", "cancellation_graph_mismatch")

    valid_result = False
    if safe_result is not None:
        try:
            _validate_wire_result_relation_impl(
                safe_result, safe_command, safe_delivery,
                safe_attempt, safe_author,
            )
        except _WireFailure:
            pass
        else:
            valid_result = True

    has_ack = "cancellation_acknowledged" in adapter_kinds
    has_reject = "cancellation_rejected" in adapter_kinds
    if "resource_limit_exceeded" in process_kinds:
        return _classified("unusable", "resource_limit_exceeded")
    if "deadline_elapsed" in adapter_kinds:
        return _classified("unusable", "deadline_elapsed")
    if "signal_delivered" in process_kinds:
        return _classified("unusable", "signal_delivered")
    if safe_request is not None:
        if has_ack:
            return _classified("unusable", "cancellation_acknowledged")
        if has_reject:
            return _classified("unusable", "cancellation_rejected")
        return _classified("unusable", "cancellation_request_pending")
    exits = [
        item for item in safe_adapters
        if item.observation_kind == "process_exited"
    ]
    if exits:
        exit_code = exits[0].process_exit_code
        if exit_code != 0:
            if valid_result:
                return _classified("unusable", "process_result_contradiction")
            return _classified("unusable", "process_failed")
        if safe_result is None and result_failure is None:
            return _classified("unusable", "result_missing")
    if result_failure is not None or (safe_result is not None and not valid_result):
        return _classified("unusable", "result_invalid")
    if not exits:
        return _classified("unusable", "process_evidence_incomplete")
    if not valid_result:
        return _classified("unusable", "result_missing")
    return _classified("usable", "usable")


def classify_wire_process_result(
    *, command: WorkerCommandV1, delivery: DeliveryEnvelopeV1,
    attempt_fence: AttemptFenceV1, author_effect_fence: EffectFenceV1,
    result: RW0WireWorkerResultV1 | None,
    result_failure: RW0WireProtocolError | None,
    adapter_observations: tuple[WorkerObservationV1, ...],
    request: RW0WireCancellationRequestObservationV1 | None,
    process_observations: tuple[RW0WireProcessObservationV1, ...],
    cancellation_effect_fence: EffectFenceV1 | None,
    cancellation_delivery: DeliveryEnvelopeV1 | None,
) -> RW0WireProcessResultClassificationV1:
    outcome = _capture(
        _classify_wire_process_result_impl, "invalid_field_value",
        command, delivery, attempt_fence, author_effect_fence, result,
        result_failure, adapter_observations, request, process_observations,
        cancellation_effect_fence, cancellation_delivery,
    )
    command = delivery = attempt_fence = author_effect_fence = None
    result = result_failure = adapter_observations = request = None
    process_observations = cancellation_effect_fence = cancellation_delivery = None
    if type(outcome) is _BoundaryFailure:
        return _classified("invalid", "invalid_input")
    return typing.cast(RW0WireProcessResultClassificationV1, outcome)


_CANCELLATION_CONTROL_PROFILE_SCHEMA = (
    "governed-execution.nwp-rw0-wire-cancellation-control-profile.v1"
)
_CANCELLATION_CONTROL_PROFILE_REF = "rw0-wire-cancellation-control-v1"
_CANCELLATION_CONTROL_PROFILE_DIGEST = (
    "4d6f84552b852a4c4073b4238591afd271072f648424eca9e744def436165288"
)
_CANCELLATION_CONTROL_MANIFEST_JSON = r'''{"authority":{"acceptance":false,"authentication":false,"c1_evidence_member":false,"current_selection":false,"durable":false,"durable_truth":false,"effect_authority":false,"external_contact":false,"io":false,"mechanism_neutral":true,"permission":false,"persistence":false,"process_control":false,"production_caller":false,"profile_in_frame":false,"provider_neutral":true,"public_export":false,"reconciliation":false,"review_result":false,"runtime":false,"semantic_cancellation":false,"source_authenticity":false,"target_result":false,"teardown":false,"terminality":false,"transport":false,"validation_result":false,"worker_result":false},"capsule":{"author_candidate":{"argument":"omitted","cancellation_portable_capsule_digest":"null","target_portable_capsule_digest":"null"},"entries":{"maximum":3,"minimum":3},"review_candidate":{"argument":"exact_CandidateCapsuleManifestV1","cancellation_portable_capsule_digest":"manifest","target_portable_capsule_digest":"manifest"},"validate_candidate":{"argument":"exact_CandidateCapsuleManifestV1","cancellation_portable_capsule_digest":"manifest","target_portable_capsule_digest":"manifest"}},"classifier":{"acknowledgement_rejection_exclusive":true,"classifications":["invalid","incomplete","finite"],"decision_order":[["invalid_input","invalid","invalid_input"],["duplicate_fact","invalid","duplicate_fact"],["unrelated_fact","invalid","unrelated_fact"],["conflicting_fact","invalid","conflicting_fact"],["cancellation_graph_mismatch","invalid","cancellation_graph_mismatch"],["request_absent","incomplete","process_evidence_incomplete"],["cancellation_rejected","finite","cancellation_rejected"],["target_process_exited","finite","target_process_exited"],["resource_limit_exceeded","incomplete","resource_limit_exceeded"],["deadline_elapsed","incomplete","deadline_elapsed"],["signal_delivered","incomplete","signal_delivered"],["cancellation_acknowledged","incomplete","cancellation_acknowledged"],["request_present","incomplete","cancellation_request_pending"]],"exit_code":{"maximum":255,"minimum":-255,"zero_special":false},"matrix":{"finite":["cancellation_rejected","target_process_exited"],"incomplete":["process_evidence_incomplete","resource_limit_exceeded","deadline_elapsed","signal_delivered","cancellation_acknowledged","cancellation_request_pending"],"invalid":["invalid_input","duplicate_fact","unrelated_fact","conflicting_fact","cancellation_graph_mismatch"]},"reasons":["invalid_input","duplicate_fact","unrelated_fact","conflicting_fact","cancellation_graph_mismatch","process_evidence_incomplete","resource_limit_exceeded","deadline_elapsed","signal_delivered","cancellation_acknowledged","cancellation_request_pending","cancellation_rejected","target_process_exited"],"response_requires_request":true,"return_type":"exact_RW0WireCancellationControlClassificationV1","timestamp_ordering":false},"facts":{"absence":"None","adapter_observations":{"maximum":4,"minimum":0,"roles":["cancellation_acknowledged","cancellation_rejected","deadline_elapsed","process_exited"]},"duplicate_detection":{"after_reconstruction":true,"keys":["original_object_identity","safe_fact_ref","safe_fact_digest"],"scope":"all_supplied_facts"},"item_types":{"adapter_observations":"exact_WorkerObservationV1","process_observations":"exact_RW0WireProcessObservationV1"},"observation_items_nullable":false,"outer_types":{"adapter_observations":"exact_builtin_tuple","process_observations":"exact_builtin_tuple","request":"exact_RW0WireCancellationRequestObservationV1_or_None"},"process_observations":{"maximum":2,"minimum":0,"roles":["resource_limit_exceeded","signal_delivered"]},"request":{"maximum":1,"minimum":0},"request_absence":"None","request_bindings":["target_effect_fence","target_delivery","cancellation_effect_fence","cancellation_delivery"],"role_bindings":{"cancellation_acknowledged":["cancellation_effect_fence","cancellation_delivery"],"cancellation_rejected":["cancellation_effect_fence","cancellation_delivery"],"deadline_elapsed":["target_effect_fence","target_delivery"],"process_exited":["target_effect_fence","target_delivery"],"resource_limit_exceeded":["target_effect_fence","target_delivery"],"signal_delivered":["target_effect_fence","target_delivery"]},"role_validation":{"cancellation_acknowledged":["cancellation_response"],"cancellation_rejected":["cancellation_response"],"deadline_elapsed":["target_observation"],"process_exited":["target_observation"],"request":["target_delivery","cancellation_delivery"],"resource_limit_exceeded":["target_delivery"],"signal_delivered":["target_delivery"]},"singleton_maximum":1,"singleton_roles":["request","cancellation_acknowledged","cancellation_rejected","deadline_elapsed","process_exited","resource_limit_exceeded","signal_delivered"],"total_maximum":7},"identity":{"canonical_json":{"allow_nan":false,"ensure_ascii":false,"normalization":"none","separators":[",",":"],"sort_keys":true},"digest":"sha256","domain_separator":"NUL","encoding":"UTF-8"},"relations":{"c2a_call_profiles":{"cancellation_delivery":{"arguments":[["delivery","cancellation_delivery"],["author_command","author_command"],["attempt_fence","attempt_fence"],["author_effect_fence","author_effect_fence"],["effect_fence","cancellation_effect_fence"],["capsule_manifest","target_capsule_manifest_by_target_class"],["cancellation_target","target_effect_fence"]],"call":"validate_delivery_relation"},"cancellation_response":{"arguments":[["observation","response"],["delivery","cancellation_delivery"],["author_command","author_command"],["attempt_fence","attempt_fence"],["author_effect_fence","author_effect_fence"],["effect_fence","cancellation_effect_fence"],["capsule_manifest","target_capsule_manifest_by_target_class"],["before_blobs","omitted"],["after_blobs","omitted"],["cancellation_target","target_effect_fence"]],"call":"validate_observation_relation"},"target_delivery":{"arguments":[["delivery","target_delivery"],["author_command","author_command"],["attempt_fence","attempt_fence"],["author_effect_fence","author_effect_fence"],["effect_fence","target_effect_fence"],["capsule_manifest","target_capsule_manifest_by_target_class"],["cancellation_target","omitted"]],"call":"validate_delivery_relation"},"target_observation":{"arguments":[["observation","adapter_observation"],["delivery","target_delivery"],["author_command","author_command"],["attempt_fence","attempt_fence"],["author_effect_fence","author_effect_fence"],["effect_fence","target_effect_fence"],["capsule_manifest","target_capsule_manifest_by_target_class"],["before_blobs","omitted"],["after_blobs","omitted"],["cancellation_target","omitted"]],"call":"validate_observation_relation"}},"c2a_owner_relations":["validate_delivery_relation","validate_observation_relation"],"classifier":{"name":"classify_wire_exact_current_cancellation_control","operands":["author_command","attempt_fence","author_effect_fence","target_effect_fence","target_delivery","cancellation_effect_fence","cancellation_delivery","request","adapter_observations","process_observations","target_capsule_manifest"],"return_type":"exact_RW0WireCancellationControlClassificationV1"},"ordered_direct_c2a_calls":{"classifier_base":["target_delivery","cancellation_delivery"],"process":["target_delivery"],"request":["target_delivery","cancellation_delivery"],"response":["target_delivery","cancellation_delivery","cancellation_response"]},"process":{"name":"validate_wire_exact_current_process_observation_relation","operands":["observation","author_command","attempt_fence","author_effect_fence","target_effect_fence","target_delivery","target_capsule_manifest"],"return_type":"None"},"request":{"name":"validate_wire_exact_current_cancellation_request_relation","operands":["request","author_command","attempt_fence","author_effect_fence","target_effect_fence","target_delivery","cancellation_effect_fence","cancellation_delivery","target_capsule_manifest"],"return_type":"None"},"response":{"name":"validate_wire_exact_current_cancellation_response_relation","operands":["response","request","author_command","attempt_fence","author_effect_fence","target_effect_fence","target_delivery","cancellation_effect_fence","cancellation_delivery","target_capsule_manifest"],"return_type":"None"},"response_prerequisite":"validate_wire_exact_current_cancellation_request_relation"},"routes":{"adapter_observation_orientation":{"cancellation_acknowledged":{"cancellation_target":"target_effect_fence","delivery":"cancellation_delivery","effect":"cancellation_effect_fence","source_basis":"bound_delivery.adapter_kind"},"cancellation_rejected":{"cancellation_target":"target_effect_fence","delivery":"cancellation_delivery","effect":"cancellation_effect_fence","source_basis":"bound_delivery.adapter_kind"},"deadline_elapsed":{"cancellation_target":"omitted","delivery":"target_delivery","effect":"target_effect_fence","source_basis":"bound_delivery.adapter_kind"},"process_exited":{"cancellation_target":"omitted","delivery":"target_delivery","effect":"target_effect_fence","source_basis":"bound_delivery.adapter_kind"}},"adapter_observation_sources":{"direct_local_bootstrap":"direct_local_adapter","execution_substrate":"es_adapter"},"process_observation_orientation":{"resource_limit_exceeded":{"delivery":"target_delivery","effect":"target_effect_fence","source_basis":"closed_process_source_kind"},"signal_delivered":{"delivery":"target_delivery","effect":"target_effect_fence","source_basis":"closed_process_source_kind"}},"process_sources":["supervisor","operating_system"],"request_orientation":{"cancellation_delivery":"cancellation_delivery","cancellation_effect":"cancellation_effect_fence","source_basis":"cancellation_delivery.adapter_kind","target_delivery":"target_delivery","target_effect":"target_effect_fence"},"request_sources":{"direct_local_bootstrap":"supervisor","execution_substrate":"execution_substrate"}},"targets":["author_candidate","validate_candidate","review_candidate"],"values":{"classification":{"c1_evidence_member":false,"c2_binding":"profile_pair_plus_exact_operand_closure","durable_identity":false,"fields":["classification","reason"],"identity":false,"name":"RW0WireCancellationControlClassificationV1"},"process":{"digest_domain":"governed-execution.nwp-rw0-wire-process-observation.v1.identity","name":"RW0WireProcessObservationV1","schema_id":"governed-execution.nwp-rw0-wire-process-observation.v1"},"request":{"digest_domain":"governed-execution.nwp-rw0-wire-cancellation-request-observation.v1.identity","name":"RW0WireCancellationRequestObservationV1","schema_id":"governed-execution.nwp-rw0-wire-cancellation-request-observation.v1"}},"work":{"alias_accounting":"per_occurrence","duplicate_detection_after_reconstruction":true,"fixed_closed_relations":"unmetered","limit_outcomes":{"maximum":"evaluate_normally","one_under_classifier":["invalid","invalid_input"],"one_under_relation_error":"work_limit_exceeded"},"maximum_local_work_units":{"classifier":{"author_candidate":1244,"review_candidate":1342,"validate_candidate":1342},"process_relation":{"author_candidate":498,"review_candidate":596,"validate_candidate":596},"request_relation":{"author_candidate":640,"review_candidate":738,"validate_candidate":738},"response_relation":{"author_candidate":764,"review_candidate":862,"validate_candidate":862}},"one_under_local_work_units":{"classifier":{"author_candidate":1243,"review_candidate":1341,"validate_candidate":1341},"process_relation":{"author_candidate":497,"review_candidate":595,"validate_candidate":595},"request_relation":{"author_candidate":639,"review_candidate":737,"validate_candidate":737},"response_relation":{"author_candidate":763,"review_candidate":861,"validate_candidate":861}},"operand_reconstruction_units":{"AttemptFenceV1":92,"CandidateCapsuleManifestV1":98,"DeliveryEnvelopeV1":32,"EffectFenceV1":102,"RW0WireCancellationRequestObservationV1":62,"RW0WireProcessObservationV1":54,"WorkerCommandV1":116,"WorkerObservationV1":124},"tariff":"two_pass_occurrence_work_including_root_and_owner_revalidation"}}'''
_CANCELLATION_CONTROL_WORK_TEST_EXTRA_UNITS = 0
_CANCELLATION_CONTROL_TARIFFS = {
    RW0WireCancellationRequestObservationV1: 62,
    RW0WireProcessObservationV1: 54,
    WorkerCommandV1: 116,
    AttemptFenceV1: 92,
    EffectFenceV1: 102,
    DeliveryEnvelopeV1: 32,
    WorkerObservationV1: 124,
    CandidateCapsuleManifestV1: 98,
}
_CANCELLATION_CONTROL_MATRIX = {
    "invalid": (
        "invalid_input", "duplicate_fact", "unrelated_fact",
        "conflicting_fact", "cancellation_graph_mismatch",
    ),
    "incomplete": (
        "process_evidence_incomplete", "resource_limit_exceeded",
        "deadline_elapsed", "signal_delivered",
        "cancellation_acknowledged", "cancellation_request_pending",
    ),
    "finite": ("cancellation_rejected", "target_process_exited"),
}
_CANCELLATION_CONTROL_ADAPTER_ROLES = (
    "cancellation_acknowledged", "cancellation_rejected",
    "deadline_elapsed", "process_exited",
)
_CANCELLATION_CONTROL_RESPONSE_ROLES = (
    "cancellation_acknowledged", "cancellation_rejected",
)
_CANCELLATION_CONTROL_TARGET_ROLES = ("deadline_elapsed", "process_exited")


class RW0WireCancellationControlClassificationV1(_ImmutableValue):
    _FIELDS = ("classification", "reason")
    __slots__ = ("_classification", "_reason")

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled") from None

    @classmethod
    def _create(
        cls, classification: str, reason: str,
    ) -> RW0WireCancellationControlClassificationV1:
        outcome = _capture(
            _cancellation_control_classification_create_impl,
            "invalid_field_value", classification, reason,
        )
        classification = reason = None
        return typing.cast(
            RW0WireCancellationControlClassificationV1, _unwrap(outcome),
        )

    def to_mapping(self) -> dict[str, object]:
        outcome = _capture(
            _cancellation_control_classification_mapping_impl,
            "invalid_field_value", self,
        )
        self = None
        return typing.cast(dict[str, object], _unwrap(outcome))


def _cancellation_control_classification_create_impl(
    classification: object, reason: object,
) -> RW0WireCancellationControlClassificationV1:
    if type(classification) is not str or type(reason) is not str:
        _fail("invalid_field_type")
    if (
        classification not in _CANCELLATION_CONTROL_MATRIX
        or reason not in _CANCELLATION_CONTROL_MATRIX[classification]
    ):
        _fail("invalid_field_value")
    return typing.cast(
        RW0WireCancellationControlClassificationV1,
        _construct(
            RW0WireCancellationControlClassificationV1,
            ("classification", "reason"),
            {"classification": classification, "reason": reason},
        ),
    )


def _validated_cancellation_control_classification(
    value: object,
) -> RW0WireCancellationControlClassificationV1:
    if type(value) is not RW0WireCancellationControlClassificationV1:
        _fail("invalid_field_type")
    mapping = _raw_slots(
        typing.cast(_ImmutableValue, value), ("classification", "reason"),
    )
    failed = False
    rebuilt: RW0WireCancellationControlClassificationV1 | None = None
    try:
        rebuilt = _cancellation_control_classification_create_impl(
            mapping["classification"], mapping["reason"],
        )
    except _WireFailure:
        failed = True
    value = None
    mapping = {}
    if failed or rebuilt is None:
        _fail("invalid_field_value")
    return rebuilt


def _cancellation_control_classification_mapping_impl(
    value: object,
) -> dict[str, object]:
    rebuilt = _validated_cancellation_control_classification(value)
    return _raw_slots(rebuilt, ("classification", "reason"))


def cancellation_control_profile_mapping() -> dict[str, object]:
    manifest = json.loads(_CANCELLATION_CONTROL_MANIFEST_JSON)
    return {
        "schema_id": _CANCELLATION_CONTROL_PROFILE_SCHEMA,
        "profile_ref": _CANCELLATION_CONTROL_PROFILE_REF,
        "manifest": manifest,
        "profile_digest": _CANCELLATION_CONTROL_PROFILE_DIGEST,
    }


class _CancellationControlWorkBudget:
    __slots__ = ("remaining",)

    def __init__(self, maximum: int) -> None:
        extra = _CANCELLATION_CONTROL_WORK_TEST_EXTRA_UNITS
        if type(maximum) is not int or type(extra) is not int:
            _fail("work_limit_exceeded")
        self.remaining = maximum + extra

    def charge(self, units: int) -> None:
        if type(units) is not int or units < 0 or self.remaining < units:
            _fail("work_limit_exceeded")
        self.remaining -= units


class _CancellationControlTargetGraph:
    __slots__ = (
        "command", "attempt", "author", "target", "target_delivery",
        "manifest", "manifest_present",
    )

    def __init__(
        self, command: WorkerCommandV1, attempt: AttemptFenceV1,
        author: EffectFenceV1, target: EffectFenceV1,
        target_delivery: DeliveryEnvelopeV1,
        manifest: CandidateCapsuleManifestV1 | None,
        manifest_present: bool,
    ) -> None:
        self.command = command
        self.attempt = attempt
        self.author = author
        self.target = target
        self.target_delivery = target_delivery
        self.manifest = manifest
        self.manifest_present = manifest_present


class _CancellationControlGraph(_CancellationControlTargetGraph):
    __slots__ = ("cancel", "cancel_delivery")

    def __init__(
        self, command: WorkerCommandV1, attempt: AttemptFenceV1,
        author: EffectFenceV1, target: EffectFenceV1,
        target_delivery: DeliveryEnvelopeV1,
        cancel: EffectFenceV1, cancel_delivery: DeliveryEnvelopeV1,
        manifest: CandidateCapsuleManifestV1 | None,
        manifest_present: bool,
    ) -> None:
        _CancellationControlTargetGraph.__init__(
            self, command, attempt, author, target, target_delivery,
            manifest, manifest_present,
        )
        self.cancel = cancel
        self.cancel_delivery = cancel_delivery


def _cancellation_control_classified(
    classification: str, reason: str,
) -> RW0WireCancellationControlClassificationV1:
    return _cancellation_control_classification_create_impl(classification, reason)


def _cancellation_control_capsule_present(value: object) -> bool:
    if value is _C2A_MISSING:
        return False
    if type(value) is not CandidateCapsuleManifestV1:
        _fail("invalid_field_type")
    return True


def _cancellation_control_budget(
    author_maximum: int, capsule_present: bool,
) -> _CancellationControlWorkBudget:
    return _CancellationControlWorkBudget(
        author_maximum + (98 if capsule_present else 0)
    )


def _cancellation_control_rebuild_c2a(
    value: object, expected: type[object], budget: _CancellationControlWorkBudget,
) -> object:
    tariff = _CANCELLATION_CONTROL_TARIFFS.get(expected)
    if type(tariff) is not int:
        _fail("invalid_field_value")
    budget.charge(tariff)
    return _rebuild_c2a(value, expected)


def _cancellation_control_rebuild_manifest(
    value: object, budget: _CancellationControlWorkBudget,
) -> CandidateCapsuleManifestV1:
    budget.charge(_CANCELLATION_CONTROL_TARIFFS[CandidateCapsuleManifestV1])
    failed = False
    rebuilt: object = None
    try:
        rebuilt, projection = _reconstruct_exact_worker_execution_value(
            value, CandidateCapsuleManifestV1,
        )
        projection = {}
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        failed = True
    value = None
    if failed or type(rebuilt) is not CandidateCapsuleManifestV1:
        _fail("invalid_field_value")
    return typing.cast(CandidateCapsuleManifestV1, rebuilt)


def _cancellation_control_rebuild_request(
    value: object, budget: _CancellationControlWorkBudget,
) -> RW0WireCancellationRequestObservationV1:
    budget.charge(
        _CANCELLATION_CONTROL_TARIFFS[
            RW0WireCancellationRequestObservationV1
        ]
    )
    return _validated_request(value)


def _cancellation_control_rebuild_process(
    value: object, budget: _CancellationControlWorkBudget,
) -> RW0WireProcessObservationV1:
    budget.charge(
        _CANCELLATION_CONTROL_TARIFFS[RW0WireProcessObservationV1]
    )
    return _validated_process(value)


def _cancellation_control_reconstruct_target_graph(
    author_command: object, attempt_fence: object,
    author_effect_fence: object, target_effect_fence: object,
    target_delivery: object, target_capsule_manifest: object,
    capsule_present: bool, budget: _CancellationControlWorkBudget,
) -> _CancellationControlTargetGraph:
    safe_command = typing.cast(
        WorkerCommandV1,
        _cancellation_control_rebuild_c2a(
            author_command, WorkerCommandV1, budget,
        ),
    )
    safe_attempt = typing.cast(
        AttemptFenceV1,
        _cancellation_control_rebuild_c2a(
            attempt_fence, AttemptFenceV1, budget,
        ),
    )
    safe_author = typing.cast(
        EffectFenceV1,
        _cancellation_control_rebuild_c2a(
            author_effect_fence, EffectFenceV1, budget,
        ),
    )
    safe_target = typing.cast(
        EffectFenceV1,
        _cancellation_control_rebuild_c2a(
            target_effect_fence, EffectFenceV1, budget,
        ),
    )
    safe_delivery = typing.cast(
        DeliveryEnvelopeV1,
        _cancellation_control_rebuild_c2a(
            target_delivery, DeliveryEnvelopeV1, budget,
        ),
    )
    safe_manifest = (
        _cancellation_control_rebuild_manifest(
            target_capsule_manifest, budget,
        )
        if capsule_present
        else None
    )
    return _CancellationControlTargetGraph(
        safe_command, safe_attempt, safe_author, safe_target, safe_delivery,
        safe_manifest, capsule_present,
    )


def _cancellation_control_reconstruct_graph(
    author_command: object, attempt_fence: object,
    author_effect_fence: object, target_effect_fence: object,
    target_delivery: object, cancellation_effect_fence: object,
    cancellation_delivery: object, target_capsule_manifest: object,
    capsule_present: bool, budget: _CancellationControlWorkBudget,
) -> _CancellationControlGraph:
    target_graph = _cancellation_control_reconstruct_target_graph(
        author_command, attempt_fence, author_effect_fence,
        target_effect_fence, target_delivery, target_capsule_manifest,
        capsule_present, budget,
    )
    safe_cancel = typing.cast(
        EffectFenceV1,
        _cancellation_control_rebuild_c2a(
            cancellation_effect_fence, EffectFenceV1, budget,
        ),
    )
    safe_cancel_delivery = typing.cast(
        DeliveryEnvelopeV1,
        _cancellation_control_rebuild_c2a(
            cancellation_delivery, DeliveryEnvelopeV1, budget,
        ),
    )
    return _CancellationControlGraph(
        target_graph.command, target_graph.attempt, target_graph.author,
        target_graph.target, target_graph.target_delivery, safe_cancel,
        safe_cancel_delivery, target_graph.manifest,
        target_graph.manifest_present,
    )


def _cancellation_control_capsule_argument(
    graph: _CancellationControlTargetGraph,
) -> object:
    return graph.manifest if graph.manifest_present else _C2A_MISSING


def _validate_cancellation_control_capsule_branch(
    graph: _CancellationControlTargetGraph,
) -> None:
    if graph.target.effect_class == "author_candidate":
        _relation(not graph.manifest_present)
        _relation(graph.target.portable_capsule_digest is None)
        return
    _relation(
        graph.target.effect_class in ("validate_candidate", "review_candidate")
    )
    _relation(
        graph.manifest_present
        and type(graph.manifest) is CandidateCapsuleManifestV1
    )
    manifest = typing.cast(CandidateCapsuleManifestV1, graph.manifest)
    _relation(
        graph.target.portable_capsule_digest == manifest.portable_capsule_digest
    )


def _validate_cancellation_control_target_owner(
    graph: _CancellationControlTargetGraph,
) -> None:
    _validate_cancellation_control_capsule_branch(graph)
    capsule = _cancellation_control_capsule_argument(graph)
    _c2a_relation(lambda: validate_delivery_relation(
        delivery=graph.target_delivery,
        author_command=graph.command,
        attempt_fence=graph.attempt,
        author_effect_fence=graph.author,
        effect_fence=graph.target,
        capsule_manifest=capsule,
    ))


def _validate_cancellation_control_graph(
    graph: _CancellationControlGraph,
) -> None:
    _validate_cancellation_control_capsule_branch(graph)
    _relation(graph.cancel.effect_class == "cancel_effect")
    _relation((
        graph.cancel.cancellation_target_effect_intent_ref,
        graph.cancel.cancellation_target_effect_fence_ref,
        graph.cancel.cancellation_target_effect_fence_digest,
    ) == (
        graph.target.effect_intent_ref,
        graph.target.effect_fence_ref,
        graph.target.effect_fence_digest,
    ))
    if graph.manifest_present:
        manifest = typing.cast(CandidateCapsuleManifestV1, graph.manifest)
        _relation(
            graph.cancel.portable_capsule_digest
            == graph.target.portable_capsule_digest
            == manifest.portable_capsule_digest
        )
    else:
        _relation(
            graph.cancel.portable_capsule_digest is None
            and graph.target.portable_capsule_digest is None
        )
    capsule = _cancellation_control_capsule_argument(graph)
    _c2a_relation(lambda: validate_delivery_relation(
        delivery=graph.target_delivery,
        author_command=graph.command,
        attempt_fence=graph.attempt,
        author_effect_fence=graph.author,
        effect_fence=graph.target,
        capsule_manifest=capsule,
    ))
    _c2a_relation(lambda: validate_delivery_relation(
        delivery=graph.cancel_delivery,
        author_command=graph.command,
        attempt_fence=graph.attempt,
        author_effect_fence=graph.author,
        effect_fence=graph.cancel,
        capsule_manifest=capsule,
        cancellation_target=graph.target,
    ))


def _validate_cancellation_control_request_bindings(
    request: RW0WireCancellationRequestObservationV1,
    graph: _CancellationControlGraph,
) -> None:
    bindings = (
        ("program_ref", graph.command.program_ref),
        ("program_version_ref", graph.command.program_version_ref),
        (
            "accepted_intent_revision_ref",
            graph.command.accepted_intent_revision_ref,
        ),
        ("work_item_ref", graph.command.work_item_ref),
        ("work_item_revision_ref", graph.command.work_item_revision_ref),
        ("semantic_attempt_ref", graph.command.semantic_attempt_ref),
        ("candidate_ref", graph.command.candidate_ref),
        ("command_ref", graph.command.command_ref),
        ("command_digest", graph.command.command_digest),
        ("attempt_fence_ref", graph.attempt.attempt_fence_ref),
        ("attempt_fence_digest", graph.attempt.attempt_fence_digest),
        ("cancellation_effect_intent_ref", graph.cancel.effect_intent_ref),
        ("cancellation_effect_fence_ref", graph.cancel.effect_fence_ref),
        (
            "cancellation_effect_fence_digest",
            graph.cancel.effect_fence_digest,
        ),
        (
            "cancellation_delivery_attempt_ref",
            graph.cancel_delivery.delivery_attempt_ref,
        ),
        (
            "cancellation_delivery_envelope_digest",
            graph.cancel_delivery.delivery_envelope_digest,
        ),
        ("target_effect_intent_ref", graph.target.effect_intent_ref),
        ("target_effect_fence_ref", graph.target.effect_fence_ref),
        ("target_effect_fence_digest", graph.target.effect_fence_digest),
        (
            "target_delivery_attempt_ref",
            graph.target_delivery.delivery_attempt_ref,
        ),
        (
            "target_delivery_envelope_digest",
            graph.target_delivery.delivery_envelope_digest,
        ),
    )
    _relation(all(getattr(request, field) == value for field, value in bindings))
    expected_source = (
        "supervisor"
        if graph.cancel_delivery.adapter_kind == "direct_local_bootstrap"
        else "execution_substrate"
    )
    _relation(request.source_kind == expected_source)


def _validate_cancellation_control_process_bindings(
    observation: RW0WireProcessObservationV1,
    graph: _CancellationControlTargetGraph,
) -> None:
    bindings = (
        ("program_ref", graph.command.program_ref),
        ("program_version_ref", graph.command.program_version_ref),
        (
            "accepted_intent_revision_ref",
            graph.command.accepted_intent_revision_ref,
        ),
        ("work_item_ref", graph.command.work_item_ref),
        ("work_item_revision_ref", graph.command.work_item_revision_ref),
        ("semantic_attempt_ref", graph.command.semantic_attempt_ref),
        ("candidate_ref", graph.command.candidate_ref),
        ("command_ref", graph.command.command_ref),
        ("command_digest", graph.command.command_digest),
        ("attempt_fence_ref", graph.attempt.attempt_fence_ref),
        ("attempt_fence_digest", graph.attempt.attempt_fence_digest),
        ("effect_intent_ref", graph.target.effect_intent_ref),
        ("effect_fence_ref", graph.target.effect_fence_ref),
        ("effect_fence_digest", graph.target.effect_fence_digest),
        ("delivery_attempt_ref", graph.target_delivery.delivery_attempt_ref),
        (
            "delivery_envelope_digest",
            graph.target_delivery.delivery_envelope_digest,
        ),
    )
    _relation(all(
        getattr(observation, field) == value for field, value in bindings
    ))


def _validate_cancellation_control_target_observation(
    observation: WorkerObservationV1,
    graph: _CancellationControlTargetGraph,
) -> None:
    _relation(observation.observation_kind in _CANCELLATION_CONTROL_TARGET_ROLES)
    capsule = _cancellation_control_capsule_argument(graph)
    _c2a_relation(lambda: validate_observation_relation(
        observation=observation,
        delivery=graph.target_delivery,
        author_command=graph.command,
        attempt_fence=graph.attempt,
        author_effect_fence=graph.author,
        effect_fence=graph.target,
        capsule_manifest=capsule,
    ))


def _validate_cancellation_control_response(
    response: WorkerObservationV1,
    graph: _CancellationControlGraph,
) -> None:
    _relation(
        response.observation_kind in _CANCELLATION_CONTROL_RESPONSE_ROLES
    )
    capsule = _cancellation_control_capsule_argument(graph)
    _c2a_relation(lambda: validate_observation_relation(
        observation=response,
        delivery=graph.cancel_delivery,
        author_command=graph.command,
        attempt_fence=graph.attempt,
        author_effect_fence=graph.author,
        effect_fence=graph.cancel,
        capsule_manifest=capsule,
        cancellation_target=graph.target,
    ))


def _validate_wire_exact_current_cancellation_request_relation_impl(
    request: object, author_command: object, attempt_fence: object,
    author_effect_fence: object, target_effect_fence: object,
    target_delivery: object, cancellation_effect_fence: object,
    cancellation_delivery: object, target_capsule_manifest: object,
) -> None:
    if (
        type(request) is not RW0WireCancellationRequestObservationV1
        or type(author_command) is not WorkerCommandV1
        or type(attempt_fence) is not AttemptFenceV1
        or type(author_effect_fence) is not EffectFenceV1
        or type(target_effect_fence) is not EffectFenceV1
        or type(target_delivery) is not DeliveryEnvelopeV1
        or type(cancellation_effect_fence) is not EffectFenceV1
        or type(cancellation_delivery) is not DeliveryEnvelopeV1
    ):
        _fail("invalid_field_type")
    capsule_present = _cancellation_control_capsule_present(
        target_capsule_manifest
    )
    budget = _cancellation_control_budget(640, capsule_present)
    safe_request = _cancellation_control_rebuild_request(request, budget)
    graph = _cancellation_control_reconstruct_graph(
        author_command, attempt_fence, author_effect_fence,
        target_effect_fence, target_delivery, cancellation_effect_fence,
        cancellation_delivery, target_capsule_manifest, capsule_present,
        budget,
    )
    _validate_cancellation_control_graph(graph)
    _validate_cancellation_control_request_bindings(safe_request, graph)


def validate_wire_exact_current_cancellation_request_relation(
    *,
    request: RW0WireCancellationRequestObservationV1,
    author_command: WorkerCommandV1,
    attempt_fence: AttemptFenceV1,
    author_effect_fence: EffectFenceV1,
    target_effect_fence: EffectFenceV1,
    target_delivery: DeliveryEnvelopeV1,
    cancellation_effect_fence: EffectFenceV1,
    cancellation_delivery: DeliveryEnvelopeV1,
    target_capsule_manifest: object = _C2A_MISSING,
) -> None:
    outcome = _capture(
        _validate_wire_exact_current_cancellation_request_relation_impl,
        "invalid_field_value", request, author_command, attempt_fence,
        author_effect_fence, target_effect_fence, target_delivery,
        cancellation_effect_fence, cancellation_delivery,
        target_capsule_manifest,
    )
    request = author_command = attempt_fence = author_effect_fence = None
    target_effect_fence = target_delivery = None
    cancellation_effect_fence = cancellation_delivery = None
    target_capsule_manifest = None
    _unwrap(outcome)


def _validate_wire_exact_current_process_observation_relation_impl(
    observation: object, author_command: object, attempt_fence: object,
    author_effect_fence: object, target_effect_fence: object,
    target_delivery: object, target_capsule_manifest: object,
) -> None:
    if (
        type(observation) is not RW0WireProcessObservationV1
        or type(author_command) is not WorkerCommandV1
        or type(attempt_fence) is not AttemptFenceV1
        or type(author_effect_fence) is not EffectFenceV1
        or type(target_effect_fence) is not EffectFenceV1
        or type(target_delivery) is not DeliveryEnvelopeV1
    ):
        _fail("invalid_field_type")
    capsule_present = _cancellation_control_capsule_present(
        target_capsule_manifest
    )
    budget = _cancellation_control_budget(498, capsule_present)
    safe_observation = _cancellation_control_rebuild_process(
        observation, budget,
    )
    graph = _cancellation_control_reconstruct_target_graph(
        author_command, attempt_fence, author_effect_fence,
        target_effect_fence, target_delivery, target_capsule_manifest,
        capsule_present, budget,
    )
    _validate_cancellation_control_target_owner(graph)
    _validate_cancellation_control_process_bindings(safe_observation, graph)


def validate_wire_exact_current_process_observation_relation(
    *,
    observation: RW0WireProcessObservationV1,
    author_command: WorkerCommandV1,
    attempt_fence: AttemptFenceV1,
    author_effect_fence: EffectFenceV1,
    target_effect_fence: EffectFenceV1,
    target_delivery: DeliveryEnvelopeV1,
    target_capsule_manifest: object = _C2A_MISSING,
) -> None:
    outcome = _capture(
        _validate_wire_exact_current_process_observation_relation_impl,
        "invalid_field_value", observation, author_command, attempt_fence,
        author_effect_fence, target_effect_fence, target_delivery,
        target_capsule_manifest,
    )
    observation = author_command = attempt_fence = author_effect_fence = None
    target_effect_fence = target_delivery = target_capsule_manifest = None
    _unwrap(outcome)


def _validate_wire_exact_current_cancellation_response_relation_impl(
    response: object, request: object, author_command: object,
    attempt_fence: object, author_effect_fence: object,
    target_effect_fence: object, target_delivery: object,
    cancellation_effect_fence: object, cancellation_delivery: object,
    target_capsule_manifest: object,
) -> None:
    if (
        type(response) is not WorkerObservationV1
        or type(request) is not RW0WireCancellationRequestObservationV1
        or type(author_command) is not WorkerCommandV1
        or type(attempt_fence) is not AttemptFenceV1
        or type(author_effect_fence) is not EffectFenceV1
        or type(target_effect_fence) is not EffectFenceV1
        or type(target_delivery) is not DeliveryEnvelopeV1
        or type(cancellation_effect_fence) is not EffectFenceV1
        or type(cancellation_delivery) is not DeliveryEnvelopeV1
    ):
        _fail("invalid_field_type")
    capsule_present = _cancellation_control_capsule_present(
        target_capsule_manifest
    )
    budget = _cancellation_control_budget(764, capsule_present)
    safe_response = typing.cast(
        WorkerObservationV1,
        _cancellation_control_rebuild_c2a(
            response, WorkerObservationV1, budget,
        ),
    )
    safe_request = _cancellation_control_rebuild_request(request, budget)
    graph = _cancellation_control_reconstruct_graph(
        author_command, attempt_fence, author_effect_fence,
        target_effect_fence, target_delivery, cancellation_effect_fence,
        cancellation_delivery, target_capsule_manifest, capsule_present,
        budget,
    )
    _validate_cancellation_control_graph(graph)
    _validate_cancellation_control_request_bindings(safe_request, graph)
    _validate_cancellation_control_response(safe_response, graph)


def validate_wire_exact_current_cancellation_response_relation(
    *,
    response: WorkerObservationV1,
    request: RW0WireCancellationRequestObservationV1,
    author_command: WorkerCommandV1,
    attempt_fence: AttemptFenceV1,
    author_effect_fence: EffectFenceV1,
    target_effect_fence: EffectFenceV1,
    target_delivery: DeliveryEnvelopeV1,
    cancellation_effect_fence: EffectFenceV1,
    cancellation_delivery: DeliveryEnvelopeV1,
    target_capsule_manifest: object = _C2A_MISSING,
) -> None:
    outcome = _capture(
        _validate_wire_exact_current_cancellation_response_relation_impl,
        "invalid_field_value", response, request, author_command,
        attempt_fence, author_effect_fence, target_effect_fence,
        target_delivery, cancellation_effect_fence, cancellation_delivery,
        target_capsule_manifest,
    )
    response = request = author_command = attempt_fence = None
    author_effect_fence = target_effect_fence = target_delivery = None
    cancellation_effect_fence = cancellation_delivery = None
    target_capsule_manifest = None
    _unwrap(outcome)


def _cancellation_control_fact_identity(
    value: object,
) -> tuple[str, str]:
    if type(value) is RW0WireCancellationRequestObservationV1:
        request = typing.cast(
            RW0WireCancellationRequestObservationV1, value,
        )
        return request.request_observation_ref, request.request_observation_digest
    if type(value) is WorkerObservationV1:
        observation = typing.cast(WorkerObservationV1, value)
        return observation.observation_ref, observation.observation_digest
    process = typing.cast(RW0WireProcessObservationV1, value)
    return process.process_observation_ref, process.process_observation_digest


def _classify_wire_exact_current_cancellation_control_impl(
    author_command: object, attempt_fence: object,
    author_effect_fence: object, target_effect_fence: object,
    target_delivery: object, cancellation_effect_fence: object,
    cancellation_delivery: object, request: object,
    adapter_observations: object, process_observations: object,
    target_capsule_manifest: object,
) -> RW0WireCancellationControlClassificationV1:
    if (
        type(author_command) is not WorkerCommandV1
        or type(attempt_fence) is not AttemptFenceV1
        or type(author_effect_fence) is not EffectFenceV1
        or type(target_effect_fence) is not EffectFenceV1
        or type(target_delivery) is not DeliveryEnvelopeV1
        or type(cancellation_effect_fence) is not EffectFenceV1
        or type(cancellation_delivery) is not DeliveryEnvelopeV1
        or (request is not None
            and type(request) is not RW0WireCancellationRequestObservationV1)
        or type(adapter_observations) is not tuple
        or type(process_observations) is not tuple
        or (
            target_capsule_manifest is not _C2A_MISSING
            and type(target_capsule_manifest) is not CandidateCapsuleManifestV1
        )
    ):
        return _cancellation_control_classified("invalid", "invalid_input")
    adapters = typing.cast(tuple[object, ...], adapter_observations)
    processes = typing.cast(tuple[object, ...], process_observations)
    if (
        len(adapters) > 4
        or len(processes) > 2
        or len(adapters) + len(processes) + int(request is not None) > 7
        or any(type(item) is not WorkerObservationV1 for item in adapters)
        or any(
            type(item) is not RW0WireProcessObservationV1
            for item in processes
        )
    ):
        return _cancellation_control_classified("invalid", "invalid_input")
    raw_facts: tuple[object, ...] = (
        (() if request is None else (request,)) + adapters + processes
    )
    original_markers = tuple(id(item) for item in raw_facts)
    capsule_present = target_capsule_manifest is not _C2A_MISSING
    budget = _cancellation_control_budget(1244, capsule_present)
    try:
        graph = _cancellation_control_reconstruct_graph(
            author_command, attempt_fence, author_effect_fence,
            target_effect_fence, target_delivery, cancellation_effect_fence,
            cancellation_delivery, target_capsule_manifest, capsule_present,
            budget,
        )
        safe_request = (
            None
            if request is None
            else _cancellation_control_rebuild_request(request, budget)
        )
        safe_adapters = tuple(
            typing.cast(
                WorkerObservationV1,
                _cancellation_control_rebuild_c2a(
                    item, WorkerObservationV1, budget,
                ),
            )
            for item in adapters
        )
        safe_processes = tuple(
            _cancellation_control_rebuild_process(item, budget)
            for item in processes
        )
    except _WireFailure:
        return _cancellation_control_classified("invalid", "invalid_input")

    if (
        graph.target.effect_class not in (
            "author_candidate", "validate_candidate", "review_candidate",
        )
        or graph.cancel.effect_class != "cancel_effect"
    ):
        return _cancellation_control_classified("invalid", "invalid_input")

    safe_facts: tuple[object, ...] = (
        (() if safe_request is None else (safe_request,))
        + safe_adapters
        + safe_processes
    )
    duplicate = False
    seen_objects: set[int] = set()
    seen_refs: set[str] = set()
    seen_digests: set[str] = set()
    for marker in original_markers:
        if marker in seen_objects:
            duplicate = True
        seen_objects.add(marker)
    for fact in safe_facts:
        reference, digest = _cancellation_control_fact_identity(fact)
        if reference in seen_refs or digest in seen_digests:
            duplicate = True
        seen_refs.add(reference)
        seen_digests.add(digest)
    if duplicate:
        return _cancellation_control_classified("invalid", "duplicate_fact")

    adapter_roles = tuple(item.observation_kind for item in safe_adapters)
    process_roles = tuple(item.event_kind for item in safe_processes)
    for observation in safe_adapters:
        if observation.observation_kind not in _CANCELLATION_CONTROL_ADAPTER_ROLES:
            return _cancellation_control_classified("invalid", "unrelated_fact")
        if observation.observation_kind in _CANCELLATION_CONTROL_TARGET_ROLES:
            unrelated = False
            try:
                _validate_cancellation_control_target_observation(
                    observation, graph,
                )
            except _WireFailure:
                unrelated = True
            if unrelated:
                return _cancellation_control_classified(
                    "invalid", "unrelated_fact",
                )
    for observation in safe_processes:
        unrelated = False
        try:
            _validate_cancellation_control_process_bindings(observation, graph)
        except _WireFailure:
            unrelated = True
        if unrelated:
            return _cancellation_control_classified("invalid", "unrelated_fact")

    conflict = (
        len(adapter_roles) != len(set(adapter_roles))
        or len(process_roles) != len(set(process_roles))
        or (
            "cancellation_acknowledged" in adapter_roles
            and "cancellation_rejected" in adapter_roles
        )
    )
    if conflict:
        return _cancellation_control_classified("invalid", "conflicting_fact")

    graph_mismatch = False
    try:
        _validate_cancellation_control_graph(graph)
    except _WireFailure:
        graph_mismatch = True
    if safe_request is not None:
        try:
            _validate_cancellation_control_request_bindings(
                safe_request, graph,
            )
        except _WireFailure:
            graph_mismatch = True
    responses = tuple(
        item for item in safe_adapters
        if item.observation_kind in _CANCELLATION_CONTROL_RESPONSE_ROLES
    )
    if responses and safe_request is None:
        graph_mismatch = True
    if safe_request is not None:
        for response in responses:
            try:
                _validate_cancellation_control_response(response, graph)
            except _WireFailure:
                graph_mismatch = True
                break
    if graph_mismatch:
        return _cancellation_control_classified(
            "invalid", "cancellation_graph_mismatch",
        )
    if safe_request is None:
        return _cancellation_control_classified(
            "incomplete", "process_evidence_incomplete",
        )
    if "cancellation_rejected" in adapter_roles:
        return _cancellation_control_classified(
            "finite", "cancellation_rejected",
        )
    if "process_exited" in adapter_roles:
        return _cancellation_control_classified(
            "finite", "target_process_exited",
        )
    if "resource_limit_exceeded" in process_roles:
        return _cancellation_control_classified(
            "incomplete", "resource_limit_exceeded",
        )
    if "deadline_elapsed" in adapter_roles:
        return _cancellation_control_classified("incomplete", "deadline_elapsed")
    if "signal_delivered" in process_roles:
        return _cancellation_control_classified("incomplete", "signal_delivered")
    if "cancellation_acknowledged" in adapter_roles:
        return _cancellation_control_classified(
            "incomplete", "cancellation_acknowledged",
        )
    return _cancellation_control_classified(
        "incomplete", "cancellation_request_pending",
    )


def classify_wire_exact_current_cancellation_control(
    *,
    author_command: WorkerCommandV1,
    attempt_fence: AttemptFenceV1,
    author_effect_fence: EffectFenceV1,
    target_effect_fence: EffectFenceV1,
    target_delivery: DeliveryEnvelopeV1,
    cancellation_effect_fence: EffectFenceV1,
    cancellation_delivery: DeliveryEnvelopeV1,
    request: RW0WireCancellationRequestObservationV1 | None,
    adapter_observations: tuple[WorkerObservationV1, ...],
    process_observations: tuple[RW0WireProcessObservationV1, ...],
    target_capsule_manifest: object = _C2A_MISSING,
) -> RW0WireCancellationControlClassificationV1:
    outcome = _capture(
        _classify_wire_exact_current_cancellation_control_impl,
        "invalid_field_value", author_command, attempt_fence,
        author_effect_fence, target_effect_fence, target_delivery,
        cancellation_effect_fence, cancellation_delivery, request,
        adapter_observations, process_observations,
        target_capsule_manifest,
    )
    author_command = attempt_fence = author_effect_fence = None
    target_effect_fence = target_delivery = None
    cancellation_effect_fence = cancellation_delivery = request = None
    adapter_observations = process_observations = None
    target_capsule_manifest = None
    if type(outcome) is _BoundaryFailure:
        return _cancellation_control_classified("invalid", "invalid_input")
    return typing.cast(
        RW0WireCancellationControlClassificationV1, outcome,
    )
