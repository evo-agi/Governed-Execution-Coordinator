"""Private pure RW0-B2 worker-mechanism capability semantics.

These values are supplied claims and a Coordinator qualification projection.
They perform no I/O and confer no source authenticity or runtime authority.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import typing
import weakref

from ._worker_execution_semantic_values import EffectFenceV1
from ._rw0_phase_entry_semantic_values import (
    RW0AuthorityVerificationObservationV1,
    RW0EffectHostQualificationV1,
    RW0PhaseEntryBasisV1,
    RW0RemoteHostReadinessObservationV1,
    _validate_host_qualification_with_snapshots,
)
from ._rw0_wire_protocol_values import (
    wire_profile_mapping as _wire_profile_mapping_owner,
)


__all__: tuple[str, ...] = ()


_DECLARATION_FIELDS = (
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
_OBSERVATION_FIELDS = (
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
_QUALIFICATION_FIELDS = (
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
_DIMENSIONS = (
    "noninteractive_operation", "wire_command_input_only", "wire_result_output_only",
    "protocol_stdout_only", "private_bounded_diagnostic_stderr",
    "external_cancellation_control_supported", "external_deadline_control_supported",
    "invocation_bound_logical_context", "private_history_non_authority",
    "isolated_credential_use", "private_interaction_material", "zero_git_effects",
    "restricted_network_access", "external_session_non_authority",
)
_DECLARATION_SCHEMA = (
    "governed-execution.nwp-rw0-worker-mechanism-capability-declaration.v1"
)
_OBSERVATION_SCHEMA = (
    "governed-execution.nwp-rw0-worker-mechanism-capability-observation.v1"
)
_QUALIFICATION_SCHEMA = (
    "governed-execution.nwp-rw0-worker-mechanism-capability-qualification.v1"
)
_DECLARATION_STATES = ("supported", "unsupported", "unknown")
_OBSERVATION_STATES = ("confirmed", "contradicted", "unknown")
_QUALIFICATION_RESULTS = ("qualified", "blocked", "unknown")
_QUALIFICATION_REASONS = (
    "b1_binding_mismatch", "b1_host_qualification_blocked",
    "b1_host_qualification_unknown", "declaration_observation_mismatch",
    "self_observation", "observation_expired", "worker_artifact_mismatch",
    "wire_profile_mismatch", "declaration_unsupported",
    "observation_nonconformant", "capability_unknown", "qualified",
)
_QUALIFICATION_BLOCKING_REASONS = (
    "b1_binding_mismatch", "b1_host_qualification_blocked",
    "declaration_observation_mismatch", "self_observation",
    "observation_expired", "worker_artifact_mismatch", "wire_profile_mismatch",
    "declaration_unsupported", "observation_nonconformant",
)
_ERROR_REASONS = (
    "invalid_field_type", "missing_field", "unknown_field", "invalid_enum",
    "malformed_ref", "malformed_digest", "invalid_timestamp_window",
    "invalid_length_or_cardinality", "digest_mismatch", "graph_cycle",
    "cumulative_work_exhausted", "privacy_forbidden_material",
    "relation_mismatch", "qualification_reason_mismatch",
)
_ERROR_REASON_BY_TEXT = {reason: reason for reason in _ERROR_REASONS}
_PRIVATE_FRAGMENTS = (
    "hostname", "host_key", "ip_address", "endpoint", "username", "bearer",
    "token", "secret", "signature", "trust_root", "prompt", "transcript",
    "stdout", "stderr", "provider", "environment_value", "absolute_path",
    "workspace_path", "store_path", "credential", "account", "model",
    "session", "jsonl", "pid", "process_handle",
)
_FORBIDDEN_REF_PREFIXES = (
    "connector-", "tunnel-", "workspace-", "org-", "organization-", "user-",
)
_SAFE_REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]*\Z", re.ASCII)
_IPV4_SHAPED_REF_RE = re.compile(r"[0-9]{1,3}(?:\.[0-9]{1,3}){3}\Z", re.ASCII)
_DIGEST_RE = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_TIME_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z",
    re.ASCII,
)
_ERROR_TOKEN = object()


def _capture_wire_owner_pair(
    owner_call: typing.Callable[[], object],
) -> tuple[str, tuple[str, str] | None]:
    status = "invalid"
    pair: tuple[str, str] | None = None
    owner: object = None
    manifest: object = None
    owner_mapping: dict[str, object] | None = None
    ordered_keys: list[str] | None = None
    key: object = None
    schema_id: object = None
    profile_ref: object = None
    profile_digest: object = None
    try:
        owner = owner_call()
        valid = type(owner) is dict and len(owner) == 4
        if valid:
            ordered_keys = []
            for key in typing.cast(dict[object, object], owner):
                if type(key) is not str:
                    valid = False
                    break
                ordered_keys.append(key)
        if valid and tuple(typing.cast(list[str], ordered_keys)) != (
            "schema_id", "profile_ref", "manifest", "profile_digest"
        ):
            valid = False
        if valid:
            owner_mapping = typing.cast(dict[str, object], owner)
            schema_id = owner_mapping["schema_id"]
            profile_ref = owner_mapping["profile_ref"]
            manifest = owner_mapping["manifest"]
            profile_digest = owner_mapping["profile_digest"]
            valid = (
                type(schema_id) is str
                and schema_id
                == "governed-execution.nwp-rw0-wire-protocol-profile.v1"
                and type(profile_ref) is str
                and profile_ref == "rw0-wire-nwpf-v1"
                and type(manifest) is dict
                and type(profile_digest) is str
                and profile_digest
                == "470cb5bf96acd3163cea4e60b8fb6fdb2844ebb18db871d014eceae5fd596454"
            )
            if valid:
                pair = (
                    typing.cast(str, profile_ref),
                    typing.cast(str, profile_digest),
                )
                status = "valid"
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        status = "invalid"
        pair = None
    finally:
        owner = None
        owner_mapping = None
        manifest = None
        ordered_keys = None
        key = None
        schema_id = None
        profile_ref = None
        profile_digest = None
        owner_call = None
    return status, pair


def _raise_wire_owner_invariant() -> typing.NoReturn:
    raise RuntimeError("RW0WorkerMechanismCapabilityWireOwnerInvariant") from None


try:
    _wire_owner_status, _wire_owner_pair = _capture_wire_owner_pair(
        _wire_profile_mapping_owner
    )
finally:
    del _wire_profile_mapping_owner
if _wire_owner_status != "valid" or _wire_owner_pair is None:
    del _wire_owner_status, _wire_owner_pair
    _raise_wire_owner_invariant()
_WIRE_PROFILE_REF, _WIRE_PROFILE_DIGEST = _wire_owner_pair
del _wire_owner_status, _wire_owner_pair


class RW0WorkerMechanismCapabilityError(ValueError):
    """Sealed, content-free Capability value or relation failure."""

    __slots__ = ("__weakref__",)

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled") from None

    def __new__(
        cls, token: object, reason: object,
    ) -> RW0WorkerMechanismCapabilityError:
        if cls is not RW0WorkerMechanismCapabilityError or token is not _ERROR_TOKEN:
            raise TypeError("sealed error") from None
        _canonical_error_reason(reason)
        error = BaseException.__new__(cls)
        BaseException.__init__(error)
        return error

    def __init__(self, token: object, reason: object) -> None:
        if token is not _ERROR_TOKEN:
            raise TypeError("sealed error") from None
        canonical_reason = _canonical_error_reason(reason)
        BaseException.__init__(self)
        _CAPABILITY_ERROR_REASON_BY_INSTANCE[self] = canonical_reason

    def __getattribute__(self, name: str) -> object:
        if name == "__dict__":
            raise AttributeError(name) from None
        return object.__getattribute__(self, name)

    @property
    def __dict__(self) -> typing.NoReturn:
        raise AttributeError("__dict__") from None

    @property
    def reason(self) -> str:
        return _CAPABILITY_ERROR_REASON_BY_INSTANCE[self]

    @property
    def _reason(self) -> str:
        return _CAPABILITY_ERROR_REASON_BY_INSTANCE[self]

    def __str__(self) -> str:
        return "RW0WorkerMechanismCapabilityError"

    def __repr__(self) -> str:
        return "RW0WorkerMechanismCapabilityError"

    def __setattr__(self, name: str, value: object) -> typing.NoReturn:
        raise AttributeError("immutable") from None

    def __delattr__(self, name: str) -> typing.NoReturn:
        raise AttributeError("immutable") from None

    def __reduce__(self) -> typing.NoReturn:
        raise TypeError("non-pickleable") from None

    def __reduce_ex__(self, protocol: int) -> typing.NoReturn:
        raise TypeError("non-pickleable") from None


_CAPABILITY_ERROR_REASON_BY_INSTANCE: weakref.WeakKeyDictionary[
    RW0WorkerMechanismCapabilityError, str
] = weakref.WeakKeyDictionary()


def _canonical_error_reason(reason: object) -> str:
    if type(reason) is not str:
        raise TypeError("sealed error") from None
    try:
        return _ERROR_REASON_BY_TEXT[typing.cast(str, reason)]
    except KeyError:
        raise TypeError("sealed error") from None


class _CapabilityFailure(Exception):
    __slots__ = ("reason",)

    def __init__(self, reason: object) -> None:
        self.reason = _canonical_error_reason(reason)
        Exception.__init__(self)


class _BoundaryFailure:
    __slots__ = ("reason",)

    def __init__(self, reason: object) -> None:
        self.reason = _canonical_error_reason(reason)


def _fail(reason: object) -> typing.NoReturn:
    raise _CapabilityFailure(_canonical_error_reason(reason))


def _capture_boundary(
    call: typing.Callable[..., object], fallback: str, *arguments: object,
) -> object:
    try:
        return call(*arguments)
    except _CapabilityFailure as caught:
        reason = caught.reason
    except Exception:
        reason = fallback
    return _BoundaryFailure(reason)


def _raise_public(reason: object) -> typing.NoReturn:
    canonical_reason = _canonical_error_reason(reason)
    error = RW0WorkerMechanismCapabilityError(_ERROR_TOKEN, canonical_reason)
    raise error from None


def _unwrap_boundary(outcome: object) -> object:
    if type(outcome) is _BoundaryFailure:
        reason = typing.cast(_BoundaryFailure, outcome).reason
        outcome = None
        _raise_public(reason)
    return outcome


class _WorkBudget:
    __slots__ = ("remaining", "active")

    def __init__(self, limit: int) -> None:
        self.remaining = limit
        self.active: set[int] = set()

    def charge(self, amount: int = 1) -> None:
        if amount > self.remaining:
            _fail("cumulative_work_exhausted")
        self.remaining -= amount

    def walk(self, value: object) -> None:
        if type(value) in (bytes, bytearray, memoryview):
            _fail("privacy_forbidden_material")
        if type(value) in (dict, list, tuple):
            identity = id(value)
            if identity in self.active:
                _fail("graph_cycle")
            self.charge()
            self.active.add(identity)
            try:
                if type(value) is dict:
                    for member in typing.cast(dict[object, object], value).values():
                        self.charge()
                        if type(member) in (dict, list, tuple):
                            self.walk(member)
                        elif type(member) in (bytes, bytearray, memoryview):
                            _fail("privacy_forbidden_material")
                else:
                    for member in typing.cast(list[object] | tuple[object, ...], value):
                        self.walk(member)
            finally:
                self.active.remove(identity)
        else:
            self.charge()


def _closed_capability_mapping(
    payload: object, fields: tuple[str, ...],
) -> dict[str, object]:
    if type(payload) is not dict:
        _fail("invalid_field_type")
    mapping = typing.cast(dict[object, object], payload)
    if len(mapping) > len(fields) + 1:
        _fail("invalid_length_or_cardinality")
    for key in mapping:
        if type(key) is not str:
            _fail("invalid_field_type")
    for key in typing.cast(dict[str, object], mapping):
        if not 1 <= len(key) <= 39:
            _fail("invalid_length_or_cardinality")
    for key in typing.cast(dict[str, object], mapping):
        if not key.isascii():
            _fail("invalid_length_or_cardinality")
    private_unknown = False
    ordinary_unknown = False
    for key in typing.cast(dict[str, object], mapping):
        if key in fields:
            continue
        if any(fragment in key.lower() for fragment in _PRIVATE_FRAGMENTS):
            private_unknown = True
        else:
            ordinary_unknown = True
    if private_unknown:
        _fail("privacy_forbidden_material")
    if ordinary_unknown:
        _fail("unknown_field")
    if any(field not in mapping for field in fields):
        _fail("missing_field")
    return typing.cast(dict[str, object], mapping)


def _exact_string(value: object) -> str:
    if type(value) is not str:
        _fail("invalid_field_type")
    return typing.cast(str, value)


def _safe_ref(value: object) -> str:
    item = _exact_string(value)
    if (
        not 1 <= len(item) <= 96
        or _SAFE_REF_RE.fullmatch(item) is None
        or item.lower().startswith(_FORBIDDEN_REF_PREFIXES)
    ):
        _fail("malformed_ref")
    if _IPV4_SHAPED_REF_RE.fullmatch(item) is not None:
        _fail("privacy_forbidden_material")
    return item


def _digest(value: object) -> str:
    item = _exact_string(value)
    if _DIGEST_RE.fullmatch(item) is None:
        _fail("malformed_digest")
    return item


def _timestamp(value: object) -> str:
    item = _exact_string(value)
    if len(item) != 20 or _TIME_RE.fullmatch(item) is None or item[:4] == "0000":
        _fail("invalid_timestamp_window")
    failed = False
    try:
        parsed = datetime.datetime.strptime(item, "%Y-%m-%dT%H:%M:%SZ")
        if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != item:
            failed = True
    except ValueError:
        failed = True
    if failed:
        _fail("invalid_timestamp_window")
    return item


def _enum(value: object, options: tuple[str, ...]) -> str:
    item = _exact_string(value)
    if item not in options:
        _fail("invalid_enum")
    return item


def _raw_identity_mapping(
    cls: type[_CapabilityValue], mapping: dict[str, str],
) -> dict[str, str]:
    return {name: mapping[name] for name in cls._FIELDS[:-1]}


def _raw_canonical_bytes(payload: object) -> bytes:
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
        _fail("invalid_length_or_cardinality")
    return result


def _raw_identity_digest(
    cls: type[_CapabilityValue], identity: dict[str, str],
) -> str:
    return hashlib.sha256(
        cls._DIGEST_DOMAIN.encode("utf-8") + b"\0" + _raw_canonical_bytes(identity)
    ).hexdigest()


def _validate_member(
    cls: type[_CapabilityValue], name: str, value: object,
    mapping: dict[str, object],
) -> str:
    if name == "schema_id":
        return _enum(value, (cls._SCHEMA,))
    if name == "declaration_source_kind":
        return _enum(value, ("worker_artifact_owner",))
    if name == "observation_source_kind":
        return _enum(value, ("independent_worker_mechanism_observer",))
    if name in _DIMENSIONS:
        options = (
            _DECLARATION_STATES
            if cls is RW0WorkerMechanismCapabilityDeclarationV1
            else _OBSERVATION_STATES
        )
        return _enum(value, options)
    if name == "result":
        return _enum(value, _QUALIFICATION_RESULTS)
    if name == "reason":
        return _enum(value, _QUALIFICATION_REASONS)
    if name in ("observed_at", "expires_at", "evaluated_at"):
        return _timestamp(value)
    if name.endswith("_digest"):
        return _digest(value)
    if name.endswith("_ref"):
        return _safe_ref(value)
    return _exact_string(value)


def _validate_cross_fields(
    cls: type[_CapabilityValue], mapping: dict[str, str],
) -> None:
    if cls is RW0WorkerMechanismCapabilityObservationV1:
        if not mapping["observed_at"] < mapping["expires_at"]:
            _fail("invalid_timestamp_window")
    if cls is RW0WorkerMechanismCapabilityQualificationV1:
        pair = (mapping["result"], mapping["reason"])
        valid = (
            pair == ("qualified", "qualified")
            or pair in (
                ("unknown", "b1_host_qualification_unknown"),
                ("unknown", "capability_unknown"),
            )
            or (pair[0] == "blocked" and pair[1] in _QUALIFICATION_BLOCKING_REASONS)
        )
        if not valid:
            _fail("qualification_reason_mismatch")


def _from_mapping_impl(
    cls: type[_CapabilityValue], payload: object, budget: _WorkBudget,
) -> tuple[_CapabilityValue, dict[str, str]]:
    mapping = _closed_capability_mapping(payload, cls._FIELDS)
    budget.walk(mapping)
    checked = {
        name: _validate_member(cls, name, mapping[name], mapping)
        for name in cls._FIELDS
    }
    _validate_cross_fields(cls, checked)
    identity = _raw_identity_mapping(cls, checked)
    if _raw_identity_digest(cls, identity) != checked[cls._FIELDS[-1]]:
        _fail("digest_mismatch")
    rebuilt = object.__new__(cls)
    object.__setattr__(rebuilt, "_values", tuple(checked[name] for name in cls._FIELDS))
    projection = {name: checked[name] for name in cls._FIELDS}
    budget.walk(projection)
    return rebuilt, projection


def _extract_stored_mapping(
    value: object, expected: type[_CapabilityValue], budget: _WorkBudget,
) -> dict[str, object]:
    if type(value) is not expected:
        _fail("invalid_field_type")
    budget.charge()
    failed = False
    values: object = None
    try:
        values = object.__getattribute__(value, "_values")
    except AttributeError:
        failed = True
    if failed or type(values) is not tuple:
        _fail("invalid_field_type")
    members = typing.cast(tuple[object, ...], values)
    if len(members) != len(expected._FIELDS):
        _fail("invalid_length_or_cardinality")
    for member in members:
        budget.charge()
        if type(member) is not str:
            _fail("invalid_field_type")
    return dict(zip(expected._FIELDS, members, strict=True))


def _safe_reconstruct_impl(
    value: object, expected: type[_CapabilityValue], budget: _WorkBudget,
) -> _CapabilityValue:
    stored = _extract_stored_mapping(value, expected, budget)
    rebuilt, projection = _from_mapping_impl(expected, stored, budget)
    stored = {}
    projection = {}
    return rebuilt


def _raw_stored_mapping(value: _CapabilityValue) -> dict[str, str]:
    values = typing.cast(tuple[str, ...], object.__getattribute__(value, "_values"))
    return dict(zip(type(value)._FIELDS, values, strict=True))


def _reject_subclass(cls: type[object], **kwargs: object) -> typing.NoReturn:
    raise TypeError("subclassing disabled") from None


class _CapabilityValue:
    __slots__ = ("_values",)
    __hash__ = None
    _FIELDS: tuple[str, ...] = ()
    _SCHEMA = ""
    _DIGEST_DOMAIN = ""
    _CONSTRUCTION_LIMIT = 0
    _RECONSTRUCTION_LIMIT = 0
    _EQUALITY_LIMIT = 0

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("construction disabled") from None

    def __setattr__(self, name: str, value: object) -> typing.NoReturn:
        raise AttributeError("immutable") from None

    def __delattr__(self, name: str) -> typing.NoReturn:
        raise AttributeError("immutable") from None

    def __getattr__(self, name: str) -> object:
        expected = type(self)
        if name not in expected._FIELDS:
            self = None
            name = ""
            raise AttributeError(expected.__name__) from None
        index = expected._FIELDS.index(name)
        budget = _WorkBudget(expected._RECONSTRUCTION_LIMIT)
        outcome = _capture_boundary(_safe_reconstruct_impl, "relation_mismatch",
                                    self, expected, budget)
        self = None
        name = ""
        budget = None
        rebuilt = typing.cast(_CapabilityValue, _unwrap_boundary(outcome))
        return object.__getattribute__(rebuilt, "_values")[index]

    def __repr__(self) -> str:
        return type(self).__name__

    __str__ = __repr__

    def __eq__(self, other: object) -> bool:
        expected = type(self)
        if type(other) is not expected:
            return False
        budget = _WorkBudget(expected._EQUALITY_LIMIT)
        outcome = _capture_boundary(_same_class_equality_impl, "relation_mismatch",
                                    self, other, expected, budget)
        self = None
        other = None
        budget = None
        return typing.cast(bool, _unwrap_boundary(outcome))

    def __copy__(self) -> _CapabilityValue:
        return self

    def __deepcopy__(self, memo: object) -> _CapabilityValue:
        return self

    def __reduce__(self) -> typing.NoReturn:
        raise TypeError("pickling disabled") from None

    def __reduce_ex__(self, protocol: int) -> typing.NoReturn:
        raise TypeError("pickling disabled") from None

    @classmethod
    def from_mapping(cls, payload: object) -> _CapabilityValue:
        budget = _WorkBudget(cls._CONSTRUCTION_LIMIT)
        outcome = _capture_boundary(_from_mapping_impl, "relation_mismatch",
                                    cls, payload, budget)
        payload = None
        budget = None
        rebuilt, projection = typing.cast(
            tuple[_CapabilityValue, dict[str, str]], _unwrap_boundary(outcome))
        projection = {}
        return rebuilt

    def to_mapping(self) -> dict[str, str]:
        expected = type(self)
        budget = _WorkBudget(expected._RECONSTRUCTION_LIMIT)
        outcome = _capture_boundary(_safe_reconstruct_impl, "relation_mismatch",
                                    self, expected, budget)
        self = None
        budget = None
        rebuilt = typing.cast(_CapabilityValue, _unwrap_boundary(outcome))
        return _raw_stored_mapping(rebuilt)

    def identity_mapping(self) -> dict[str, str]:
        expected = type(self)
        budget = _WorkBudget(expected._RECONSTRUCTION_LIMIT)
        outcome = _capture_boundary(_safe_reconstruct_impl, "relation_mismatch",
                                    self, expected, budget)
        self = None
        budget = None
        rebuilt = typing.cast(_CapabilityValue, _unwrap_boundary(outcome))
        mapping = _raw_stored_mapping(rebuilt)
        return _raw_identity_mapping(expected, mapping)

    def canonical_identity_bytes(self) -> bytes:
        expected = type(self)
        budget = _WorkBudget(expected._RECONSTRUCTION_LIMIT)
        outcome = _capture_boundary(_safe_reconstruct_impl, "relation_mismatch",
                                    self, expected, budget)
        self = None
        budget = None
        rebuilt = typing.cast(_CapabilityValue, _unwrap_boundary(outcome))
        mapping = _raw_stored_mapping(rebuilt)
        return _raw_canonical_bytes(_raw_identity_mapping(expected, mapping))

    def computed_digest(self) -> str:
        expected = type(self)
        budget = _WorkBudget(expected._RECONSTRUCTION_LIMIT)
        outcome = _capture_boundary(_safe_reconstruct_impl, "relation_mismatch",
                                    self, expected, budget)
        self = None
        budget = None
        rebuilt = typing.cast(_CapabilityValue, _unwrap_boundary(outcome))
        mapping = _raw_stored_mapping(rebuilt)
        return _raw_identity_digest(expected, _raw_identity_mapping(expected, mapping))


def _same_class_equality_impl(
    left: object, right: object, expected: type[_CapabilityValue], budget: _WorkBudget,
) -> bool:
    rebuilt_left = _safe_reconstruct_impl(left, expected, budget)
    rebuilt_right = _safe_reconstruct_impl(right, expected, budget)
    return (
        object.__getattribute__(rebuilt_left, "_values")
        == object.__getattribute__(rebuilt_right, "_values")
    )


class RW0WorkerMechanismCapabilityDeclarationV1(_CapabilityValue):
    _FIELDS = _DECLARATION_FIELDS
    _SCHEMA = _DECLARATION_SCHEMA
    _DIGEST_DOMAIN = _DECLARATION_SCHEMA + ".identity"
    _CONSTRUCTION_LIMIT = 48
    _RECONSTRUCTION_LIMIT = 72
    _EQUALITY_LIMIT = 144
    __slots__ = ()
    __init_subclass__ = _reject_subclass


class RW0WorkerMechanismCapabilityObservationV1(_CapabilityValue):
    _FIELDS = _OBSERVATION_FIELDS
    _SCHEMA = _OBSERVATION_SCHEMA
    _DIGEST_DOMAIN = _OBSERVATION_SCHEMA + ".identity"
    _CONSTRUCTION_LIMIT = 62
    _RECONSTRUCTION_LIMIT = 93
    _EQUALITY_LIMIT = 186
    __slots__ = ()
    __init_subclass__ = _reject_subclass


class RW0WorkerMechanismCapabilityQualificationV1(_CapabilityValue):
    _FIELDS = _QUALIFICATION_FIELDS
    _SCHEMA = _QUALIFICATION_SCHEMA
    _DIGEST_DOMAIN = _QUALIFICATION_SCHEMA + ".identity"
    _CONSTRUCTION_LIMIT = 52
    _RECONSTRUCTION_LIMIT = 78
    _EQUALITY_LIMIT = 156
    __slots__ = ()
    __init_subclass__ = _reject_subclass


def _relation_leaf(budget: _WorkBudget, value: object, expected: type[object]) -> None:
    budget.charge()
    if type(value) is not expected:
        _fail("relation_mismatch")


def _expected_qualification_pair(
    declaration: RW0WorkerMechanismCapabilityDeclarationV1,
    observation: RW0WorkerMechanismCapabilityObservationV1,
    qualification: RW0WorkerMechanismCapabilityQualificationV1,
    phase_basis: dict[str, object],
    authority_observation: dict[str, object],
    readiness_observation: dict[str, object],
    host_qualification: dict[str, object],
    current_effect_fence: dict[str, object],
    now_utc: str,
    wire_profile_pair: tuple[str, str],
) -> tuple[str, str]:
    declaration_values = _raw_stored_mapping(declaration)
    observation_values = _raw_stored_mapping(observation)
    qualification_values = _raw_stored_mapping(qualification)
    coordinates_match = (
        (qualification_values["phase_basis_ref"],
         qualification_values["phase_basis_digest"])
        == (phase_basis["basis_ref"], phase_basis["basis_digest"])
        and (qualification_values["authority_observation_ref"],
             qualification_values["authority_observation_digest"])
        == (authority_observation["observation_ref"],
            authority_observation["observation_digest"])
        and (qualification_values["readiness_observation_ref"],
             qualification_values["readiness_observation_digest"])
        == (readiness_observation["observation_ref"],
            readiness_observation["observation_digest"])
        and (qualification_values["host_qualification_ref"],
             qualification_values["host_qualification_digest"])
        == (host_qualification["qualification_ref"],
            host_qualification["qualification_digest"])
        and (qualification_values["effect_intent_ref"],
             qualification_values["effect_fence_ref"],
             qualification_values["effect_fence_digest"])
        == (current_effect_fence["effect_intent_ref"],
            current_effect_fence["effect_fence_ref"],
            current_effect_fence["effect_fence_digest"])
        and qualification_values["evaluated_at"]
        == host_qualification["evaluated_at"] == now_utc
    )
    if not coordinates_match:
        return "blocked", "b1_binding_mismatch"
    if host_qualification["result"] == "blocked":
        return "blocked", "b1_host_qualification_blocked"
    if (
        host_qualification["result"] == "unknown"
        and host_qualification["reason"] == "unknown"
    ):
        return "unknown", "b1_host_qualification_unknown"
    if (
        observation_values["capability_declaration_ref"],
        observation_values["capability_declaration_digest"],
    ) != (
        declaration_values["capability_declaration_ref"],
        declaration_values["capability_declaration_digest"],
    ):
        return "blocked", "declaration_observation_mismatch"
    if (
        declaration_values["declaration_source_ref"]
        == observation_values["observation_source_ref"]
    ):
        return "blocked", "self_observation"
    if not (
        observation_values["observed_at"] <= now_utc
        < observation_values["expires_at"]
    ):
        return "blocked", "observation_expired"
    artifact_pair = (
        declaration_values["worker_artifact_ref"],
        declaration_values["worker_artifact_digest"],
    )
    if any(
        pair != artifact_pair
        for pair in (
            (observation_values["worker_artifact_ref"],
             observation_values["worker_artifact_digest"]),
            (qualification_values["worker_artifact_ref"],
             qualification_values["worker_artifact_digest"]),
            (readiness_observation["worker_artifact_ref"],
             readiness_observation["worker_artifact_digest"]),
            (host_qualification["required_worker_artifact_ref"],
             host_qualification["required_worker_artifact_digest"]),
        )
    ):
        return "blocked", "worker_artifact_mismatch"
    wire_pair = (
        declaration_values["wire_profile_ref"],
        declaration_values["wire_profile_digest"],
    )
    if any(
        pair != wire_pair
        for pair in (
            (observation_values["wire_profile_ref"],
             observation_values["wire_profile_digest"]),
            (qualification_values["wire_profile_ref"],
             qualification_values["wire_profile_digest"]),
            wire_profile_pair,
            (readiness_observation["worker_protocol_ref"],
             readiness_observation["worker_protocol_digest"]),
            (host_qualification["required_worker_protocol_ref"],
             host_qualification["required_worker_protocol_digest"]),
        )
    ):
        return "blocked", "wire_profile_mismatch"
    if any(declaration_values[name] == "unsupported" for name in _DIMENSIONS):
        return "blocked", "declaration_unsupported"
    if any(observation_values[name] == "contradicted" for name in _DIMENSIONS):
        return "blocked", "observation_nonconformant"
    if (
        any(declaration_values[name] == "unknown" for name in _DIMENSIONS)
        or any(observation_values[name] == "unknown" for name in _DIMENSIONS)
    ):
        return "unknown", "capability_unknown"
    return "qualified", "qualified"


def _validate_qualification_impl(
    declaration: object,
    observation: object,
    qualification: object,
    phase_basis: object,
    authority_observation: object,
    readiness_observation: object,
    host_qualification: object,
    current_effect_fence: object,
    now_utc: object,
) -> None:
    wire_profile_pair = (_WIRE_PROFILE_REF, _WIRE_PROFILE_DIGEST)
    (
        phase_basis_snapshot,
        authority_snapshot,
        readiness_snapshot,
        host_qualification_snapshot,
        current_effect_snapshot,
    ) = _validate_host_qualification_with_snapshots(
        basis=typing.cast(RW0PhaseEntryBasisV1, phase_basis),
        authority=typing.cast(
            RW0AuthorityVerificationObservationV1, authority_observation
        ),
        readiness=typing.cast(
            RW0RemoteHostReadinessObservationV1, readiness_observation
        ),
        qualification=typing.cast(
            RW0EffectHostQualificationV1, host_qualification
        ),
        current_effect_fence=typing.cast(EffectFenceV1, current_effect_fence),
        now_utc=typing.cast(str, now_utc),
    )
    phase_basis = None
    authority_observation = None
    readiness_observation = None
    host_qualification = None
    current_effect_fence = None
    budget = _WorkBudget(249)
    rebuilt_declaration = typing.cast(
        RW0WorkerMechanismCapabilityDeclarationV1,
        _safe_reconstruct_impl(
            declaration, RW0WorkerMechanismCapabilityDeclarationV1, budget),
    )
    rebuilt_observation = typing.cast(
        RW0WorkerMechanismCapabilityObservationV1,
        _safe_reconstruct_impl(
            observation, RW0WorkerMechanismCapabilityObservationV1, budget),
    )
    rebuilt_qualification = typing.cast(
        RW0WorkerMechanismCapabilityQualificationV1,
        _safe_reconstruct_impl(
            qualification, RW0WorkerMechanismCapabilityQualificationV1, budget),
    )
    for snapshot in (
        phase_basis_snapshot,
        authority_snapshot,
        readiness_snapshot,
        host_qualification_snapshot,
        current_effect_snapshot,
    ):
        _relation_leaf(budget, snapshot, dict)
    budget.charge()
    checked_now = _timestamp(now_utc)
    declaration_values = _raw_stored_mapping(rebuilt_declaration)
    observation_values = _raw_stored_mapping(rebuilt_observation)
    qualification_values = _raw_stored_mapping(rebuilt_qualification)
    if (
        qualification_values["capability_declaration_ref"],
        qualification_values["capability_declaration_digest"],
    ) != (
        declaration_values["capability_declaration_ref"],
        declaration_values["capability_declaration_digest"],
    ):
        _fail("relation_mismatch")
    if (
        qualification_values["capability_observation_ref"],
        qualification_values["capability_observation_digest"],
    ) != (
        observation_values["capability_observation_ref"],
        observation_values["capability_observation_digest"],
    ):
        _fail("relation_mismatch")
    expected = _expected_qualification_pair(
        rebuilt_declaration,
        rebuilt_observation,
        rebuilt_qualification,
        phase_basis_snapshot,
        authority_snapshot,
        readiness_snapshot,
        host_qualification_snapshot,
        current_effect_snapshot,
        checked_now,
        wire_profile_pair,
    )
    if (
        qualification_values["result"], qualification_values["reason"]
    ) != expected:
        _fail("qualification_reason_mismatch")


def validate_worker_mechanism_capability_qualification(
    *,
    declaration: RW0WorkerMechanismCapabilityDeclarationV1,
    observation: RW0WorkerMechanismCapabilityObservationV1,
    qualification: RW0WorkerMechanismCapabilityQualificationV1,
    phase_basis: RW0PhaseEntryBasisV1,
    authority_observation: RW0AuthorityVerificationObservationV1,
    readiness_observation: RW0RemoteHostReadinessObservationV1,
    host_qualification: RW0EffectHostQualificationV1,
    current_effect_fence: EffectFenceV1,
    now_utc: str,
) -> None:
    outcome = _capture_boundary(
        _validate_qualification_impl,
        "relation_mismatch",
        declaration,
        observation,
        qualification,
        phase_basis,
        authority_observation,
        readiness_observation,
        host_qualification,
        current_effect_fence,
        now_utc,
    )
    declaration = None
    observation = None
    qualification = None
    phase_basis = None
    authority_observation = None
    readiness_observation = None
    host_qualification = None
    current_effect_fence = None
    now_utc = None
    _unwrap_boundary(outcome)
