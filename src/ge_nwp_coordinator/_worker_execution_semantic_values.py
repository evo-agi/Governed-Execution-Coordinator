"""Pure internal C2A1 worker-execution semantic values.

This module deliberately owns no transport, authority verification, durable
state, process, filesystem, network, clock, capsule custody, or effect runtime.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import typing


__all__: tuple[str, ...] = ()


_MISSING = object()

_WORK_SPEC_SCHEMA = "governed-execution.nwp-work-spec.v1"
_WORK_SPEC_DOMAIN = "governed-execution.nwp-work-spec.v1.identity"
_ATTEMPT_FENCE_SCHEMA = "governed-execution.nwp-attempt-fence.v1"
_ATTEMPT_FENCE_DOMAIN = "governed-execution.nwp-attempt-fence.v1.identity"
_EFFECT_FENCE_SCHEMA = "governed-execution.nwp-effect-fence.v1"
_EFFECT_FENCE_DOMAIN = "governed-execution.nwp-effect-fence.v1.identity"
_WORKER_COMMAND_SCHEMA = "governed-execution.nwp-worker-command.v1"
_WORKER_COMMAND_DOMAIN = "governed-execution.nwp-worker-command.v1.identity"
_DELIVERY_ENVELOPE_SCHEMA = "governed-execution.nwp-delivery-envelope.v1"
_DELIVERY_ENVELOPE_DOMAIN = "governed-execution.nwp-delivery-envelope.v1.identity"
_WORKER_OBSERVATION_SCHEMA = "governed-execution.nwp-worker-observation.v1"
_WORKER_OBSERVATION_DOMAIN = "governed-execution.nwp-worker-observation.v1.identity"
_CAPSULE_MANIFEST_SCHEMA = "governed-execution.nwp-candidate-capsule-manifest.v1"
_CAPSULE_MANIFEST_DOMAIN = "governed-execution.nwp-candidate-capsule-manifest.v1.identity"
_AUTHORIZED_PATH_SCOPE_DOMAIN = "governed-execution.nwp-authorized-path-scope.v1.identity"
_CAPSULE_CANONICALIZATION_PROFILE = "canonical-json.sorted-keys.utf8.v1"

_AUTHORIZED_PATHS = (
    ".docs/system_overview/hybrid_integration_architecture_adr.md",
    "PLANS.md",
    "docs_contract_test.go",
)
_EFFECT_CLASSES = (
    "author_candidate",
    "cancel_effect",
    "local_git_commit",
    "review_candidate",
    "validate_candidate",
)
_DELIVERABLE_EFFECT_CLASSES = (
    "author_candidate",
    "cancel_effect",
    "review_candidate",
    "validate_candidate",
)
_CANCELLATION_TARGET_CLASSES = (
    "author_candidate",
    "review_candidate",
    "validate_candidate",
)
_ADAPTER_KINDS = ("direct_local_bootstrap", "execution_substrate")
_SOURCE_KINDS = (
    "capsule_builder",
    "capsule_store",
    "direct_local_adapter",
    "es_adapter",
    "independent_reviewer",
    "validator",
    "worker",
    "workspace_custodian",
)
_ADAPTER_AUTHORED_OBSERVATIONS = (
    "cancellation_acknowledged",
    "cancellation_rejected",
    "deadline_elapsed",
    "delivery_acknowledged",
    "delivery_outcome_unknown",
    "delivery_rejected",
    "process_exited",
)
_CAPSULE_OBSERVATIONS = (
    "capsule_retrieval_failed",
    "capsule_retrieval_succeeded",
    "capsule_sealed",
    "independent_review_completed",
    "validation_completed",
    "workspace_teardown_failed",
    "workspace_teardown_succeeded",
)
_CANDIDATE_OBSERVATIONS = ("candidate_captured", "capsule_seal_failed")

_CEILING_FIELDS = (
    "max_active_invocations",
    "max_candidate_bytes",
    "max_changed_files",
    "max_cost_microusd",
    "max_cpu_seconds",
    "max_deliveries",
    "max_deployments",
    "max_local_commits",
    "max_memory_bytes",
    "max_merges",
    "max_model_input_tokens",
    "max_model_output_tokens",
    "max_pull_requests",
    "max_pushes",
    "max_wall_seconds",
)
_GIT_EFFECT_CEILING_FIELDS = (
    "max_deployments",
    "max_local_commits",
    "max_merges",
    "max_pull_requests",
    "max_pushes",
)

_ERROR_REASONS = (
    "digest_mismatch",
    "invalid_field_type",
    "invalid_field_value",
    "missing_field",
    "relation_mismatch",
    "unknown_field",
)
_WORKER_EXECUTION_VALUE_ERROR_TOKEN = object()


class WorkerExecutionValueError(ValueError):
    """Bounded C2A1 value or relation failure."""

    __slots__ = ("_field_path", "_reason")

    def __init__(self, *args: object, **kwargs: object) -> None:
        if (
            len(args) != 3
            or kwargs
            or args[0] is not _WORKER_EXECUTION_VALUE_ERROR_TOKEN
        ):
            raise TypeError(
                "WorkerExecutionValueError cannot be constructed directly"
            ) from None
        reason = typing.cast(str, args[1])
        field_path = typing.cast(str, args[2])
        object.__setattr__(self, "_reason", reason)
        object.__setattr__(self, "_field_path", field_path)
        ValueError.__init__(self, f"{reason}:{field_path}")

    @property
    def reason(self) -> str:
        return self._reason

    @property
    def field_path(self) -> str:
        return self._field_path

    def __setattr__(self, name: str, value: object) -> typing.NoReturn:
        raise AttributeError("immutable")

    def __delattr__(self, name: str) -> typing.NoReturn:
        raise AttributeError("immutable")


def _make_worker_execution_value_error(
    reason: str, field_path: str
) -> WorkerExecutionValueError:
    if type(reason) is not str or type(field_path) is not str:
        raise TypeError(
            "WorkerExecutionValueError cannot be constructed directly"
        ) from None
    if reason not in _ERROR_REASONS:
        raise TypeError(
            "WorkerExecutionValueError cannot be constructed directly"
        ) from None
    return WorkerExecutionValueError(
        _WORKER_EXECUTION_VALUE_ERROR_TOKEN, reason, field_path
    )


def _fail(reason: str, field_path: str) -> typing.NoReturn:
    raise _make_worker_execution_value_error(reason, field_path)


def _relation(condition: bool, field_path: str) -> None:
    if not condition:
        _fail("relation_mismatch", field_path)


def _closed_mapping(
    payload: object,
    fields: tuple[str, ...],
    field_path: str,
    *,
    required_fields: tuple[str, ...] | None = None,
) -> dict[str, object]:
    if type(payload) is not dict:
        _fail("invalid_field_type", field_path)
    mapping = typing.cast(dict[object, object], payload)
    if any(type(key) is not str for key in mapping):
        _fail("invalid_field_type", field_path)
    if any(key not in fields for key in typing.cast(dict[str, object], mapping)):
        _fail("unknown_field", field_path)
    required = fields if required_fields is None else required_fields
    if any(field not in mapping for field in required):
        _fail("missing_field", field_path)
    return typing.cast(dict[str, object], mapping)


def _require_exact_string(value: object, field_path: str) -> str:
    if type(value) is not str:
        _fail("invalid_field_type", field_path)
    return typing.cast(str, value)


def _require_exact_integer_type(value: object, field_path: str) -> int:
    if type(value) is not int:
        _fail("invalid_field_type", field_path)
    return typing.cast(int, value)


def _require_exact_string_list_type(value: object, field_path: str) -> list[str]:
    if type(value) is not list:
        _fail("invalid_field_type", field_path)
    items = typing.cast(list[object], value)
    if any(type(item) is not str for item in items):
        _fail("invalid_field_type", field_path)
    return typing.cast(list[str], items)


def _require_nullable_exact_string_type(value: object, field_path: str) -> None:
    if value is not None and type(value) is not str:
        _fail("invalid_field_type", field_path)


def _require_factory_exact_value(
    value: object,
    value_type: type[typing.Any],
    field_path: str,
) -> None:
    if type(value) is not value_type:
        _fail("invalid_field_type", field_path)


def _require_optional_factory_exact_value(
    value: object,
    value_type: type[typing.Any],
    field_path: str,
) -> None:
    if value is not _MISSING:
        _require_factory_exact_value(value, value_type, field_path)


def _require_optional_relation_exact_value(
    value: object,
    value_type: type[typing.Any],
    field_path: str,
) -> None:
    if value is not _MISSING:
        _require_exact_value(value, value_type, field_path)


def _require_blob_map_types(payload: object, field_path: str) -> dict[str, bytes]:
    if type(payload) is not dict:
        _fail("invalid_field_type", field_path)
    mapping = typing.cast(dict[object, object], payload)
    if any(type(key) is not str for key in mapping):
        _fail("invalid_field_type", field_path)
    if any(type(value) is not bytes for value in mapping.values()):
        _fail("invalid_field_type", field_path)
    return typing.cast(dict[str, bytes], mapping)


def _require_mode_map_types(payload: object, field_path: str) -> dict[str, str]:
    if type(payload) is not dict:
        _fail("invalid_field_type", field_path)
    mapping = typing.cast(dict[object, object], payload)
    if any(type(key) is not str for key in mapping):
        _fail("invalid_field_type", field_path)
    if any(type(value) is not str for value in mapping.values()):
        _fail("invalid_field_type", field_path)
    return typing.cast(dict[str, str], mapping)


def _require_optional_blob_map_types(payload: object, field_path: str) -> None:
    if payload is not _MISSING:
        _require_blob_map_types(payload, field_path)


def _require_constant(value: object, expected: str, field_path: str) -> str:
    result = _require_exact_string(value, field_path)
    if result != expected:
        _fail("invalid_field_value", field_path)
    return result


def _require_safe_ref(value: object, field_path: str) -> str:
    result = _require_exact_string(value, field_path)
    if not 1 <= len(result) <= 96:
        _fail("invalid_field_value", field_path)
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", result) is None:
        _fail("invalid_field_value", field_path)
    if result.lower().startswith(
        ("connector-", "tunnel-", "workspace-", "org-", "organization-", "user-")
    ):
        _fail("invalid_field_value", field_path)
    return result


def _require_digest(value: object, field_path: str) -> str:
    result = _require_exact_string(value, field_path)
    if re.fullmatch(r"[0-9a-f]{64}", result) is None:
        _fail("invalid_field_value", field_path)
    return result


def _require_base_oid(value: object, field_path: str) -> str:
    result = _require_exact_string(value, field_path)
    if re.fullmatch(r"[0-9a-f]{40}", result) is None:
        _fail("invalid_field_value", field_path)
    return result


def _require_non_negative_integer(value: object, field_path: str) -> int:
    if type(value) is not int:
        _fail("invalid_field_type", field_path)
    result = typing.cast(int, value)
    if result < 0:
        _fail("invalid_field_value", field_path)
    return result


def _require_exit_code(value: object, field_path: str) -> int:
    if type(value) is not int:
        _fail("invalid_field_type", field_path)
    result = typing.cast(int, value)
    if not -255 <= result <= 255:
        _fail("invalid_field_value", field_path)
    return result


def _require_timestamp(value: object, field_path: str) -> str:
    result = _require_exact_string(value, field_path)
    valid = (
        len(result) == 20
        and result.isascii()
        and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", result)
        is not None
    )
    if not valid:
        _fail("invalid_field_value", field_path)
    parse_failed = False
    try:
        parsed = datetime.datetime.strptime(result, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        parse_failed = True
        parsed = None
    if parse_failed or parsed is None or parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != result:
        _fail("invalid_field_value", field_path)
    return result


def _require_private_string(value: object, field_path: str) -> str:
    result = _require_exact_string(value, field_path)
    if not 1 <= len(result) <= 512:
        _fail("invalid_field_value", field_path)
    if any(ord(character) < 32 or ord(character) == 127 for character in result):
        _fail("invalid_field_value", field_path)
    return result


def _require_paths(value: object, field_path: str) -> tuple[str, ...]:
    if type(value) is not list:
        _fail("invalid_field_type", field_path)
    items = typing.cast(list[object], value)
    if any(type(item) is not str for item in items):
        _fail("invalid_field_type", field_path)
    paths = tuple(typing.cast(list[str], items))
    if paths != _AUTHORIZED_PATHS:
        _fail("invalid_field_value", field_path)
    return paths


def _require_private_string_array(value: object, field_path: str) -> tuple[str, ...]:
    if type(value) is not list:
        _fail("invalid_field_type", field_path)
    items = typing.cast(list[object], value)
    if not 1 <= len(items) <= 32:
        _fail("invalid_field_value", field_path)
    strings = tuple(_require_private_string(item, field_path) for item in items)
    if len(strings) != len(set(strings)):
        _fail("invalid_field_value", field_path)
    return strings


def _require_allowed_effect_classes(value: object, field_path: str) -> tuple[str, ...]:
    if type(value) is not list:
        _fail("invalid_field_type", field_path)
    items = typing.cast(list[object], value)
    if not items or any(type(item) is not str for item in items):
        if any(type(item) is not str for item in items):
            _fail("invalid_field_type", field_path)
        _fail("invalid_field_value", field_path)
    classes = tuple(typing.cast(list[str], items))
    if classes != tuple(sorted(classes)) or len(classes) != len(set(classes)):
        _fail("invalid_field_value", field_path)
    if any(item not in _EFFECT_CLASSES for item in classes):
        _fail("invalid_field_value", field_path)
    return classes


def _require_evidence_refs(value: object, field_path: str) -> tuple[str, ...]:
    if type(value) is not list:
        _fail("invalid_field_type", field_path)
    items = typing.cast(list[object], value)
    if len(items) > 32:
        _fail("invalid_field_value", field_path)
    refs = tuple(_require_safe_ref(item, field_path) for item in items)
    if refs != tuple(sorted(refs)) or len(refs) != len(set(refs)):
        _fail("invalid_field_value", field_path)
    return refs


def _require_reason_code(value: object, observation_kind: str, field_path: str) -> str:
    result = _require_exact_string(value, field_path)
    if re.fullmatch(r"[a-z][a-z0-9_.-]{0,95}", result) is None:
        _fail("invalid_field_value", field_path)
    if result == "provably_not_accepted" and observation_kind != "delivery_rejected":
        _fail("invalid_field_value", field_path)
    return result


def _canonical_bytes(payload: object, field_path: str) -> bytes:
    failed = False
    encoded = b""
    try:
        text = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        encoded = text.encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeEncodeError):
        failed = True
    if failed:
        _fail("invalid_field_value", field_path)
    return encoded


def _domain_digest(domain: str, canonical_bytes: bytes) -> str:
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + canonical_bytes).hexdigest()


def _authorized_path_scope_digest(paths: tuple[str, ...]) -> str:
    return _domain_digest(
        _AUTHORIZED_PATH_SCOPE_DOMAIN,
        _canonical_bytes(list(paths), "CandidateCapsuleManifestV1.authorized_path_scope_digest"),
    )


def _read_only_property(private_name: str) -> property:
    def get_value(instance: object) -> object:
        return object.__getattribute__(instance, private_name)

    return property(get_value)


def _external_value(value: object) -> object:
    if type(value) is tuple:
        return [_external_value(item) for item in typing.cast(tuple[object, ...], value)]
    if type(value) is CeilingsV1:
        return typing.cast(CeilingsV1, value).to_mapping()
    if type(value) is CapsuleEntryV1:
        return typing.cast(CapsuleEntryV1, value).to_mapping()
    return value


def _construct(
    value_type: type[typing.Any],
    fields: tuple[str, ...],
    values: tuple[object, ...],
) -> typing.Any:
    instance = object.__new__(value_type)
    for field, value in zip(fields, values, strict=True):
        object.__setattr__(instance, f"_{field}", value)
    return instance


class _ImmutableValue:
    __slots__ = ()
    __hash__ = None
    _FIELDS: tuple[str, ...] = ()

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("construction disabled")

    def __setattr__(self, name: str, value: object) -> typing.NoReturn:
        raise AttributeError("immutable")

    def __delattr__(self, name: str) -> typing.NoReturn:
        raise AttributeError("immutable")

    def __repr__(self) -> str:
        return f"<{type(self).__name__}>"

    __str__ = __repr__

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return all(
            object.__getattribute__(self, f"_{field}")
            == object.__getattribute__(other, f"_{field}")
            for field in self._FIELDS
        )

    def __copy__(self) -> _ImmutableValue:
        return self

    def __deepcopy__(self, memo: object) -> _ImmutableValue:
        return self

    def __reduce__(self) -> typing.NoReturn:
        raise TypeError("pickling disabled")

    def __reduce_ex__(self, protocol: int) -> typing.NoReturn:
        raise TypeError("pickling disabled")

    def _to_mapping(self) -> dict[str, object]:
        return {
            field: _external_value(object.__getattribute__(self, f"_{field}"))
            for field in self._FIELDS
        }


class _TopLevelValue(_ImmutableValue):
    __slots__ = ()
    _DOMAIN = ""
    _IDENTITY_EXCLUSIONS: tuple[str, ...] = ()

    def identity_mapping(self) -> dict[str, object]:
        result = self._to_mapping()
        for field in self._IDENTITY_EXCLUSIONS:
            result.pop(field)
        return result

    def canonical_identity_bytes(self) -> bytes:
        return _canonical_bytes(
            self.identity_mapping(), f"{type(self).__name__}.canonical_identity"
        )

    def computed_digest(self) -> str:
        return _domain_digest(self._DOMAIN, self.canonical_identity_bytes())


def _prevalidate_ceilings_mapping_types(mapping: dict[str, object]) -> None:
    for field in _CEILING_FIELDS:
        _require_exact_integer_type(mapping[field], f"CeilingsV1.{field}")


class CeilingsV1(_ImmutableValue):
    __slots__ = (
        "_max_active_invocations",
        "_max_candidate_bytes",
        "_max_changed_files",
        "_max_cost_microusd",
        "_max_cpu_seconds",
        "_max_deliveries",
        "_max_deployments",
        "_max_local_commits",
        "_max_memory_bytes",
        "_max_merges",
        "_max_model_input_tokens",
        "_max_model_output_tokens",
        "_max_pull_requests",
        "_max_pushes",
        "_max_wall_seconds",
    )
    _FIELDS = _CEILING_FIELDS

    max_active_invocations = _read_only_property("_max_active_invocations")
    max_candidate_bytes = _read_only_property("_max_candidate_bytes")
    max_changed_files = _read_only_property("_max_changed_files")
    max_cost_microusd = _read_only_property("_max_cost_microusd")
    max_cpu_seconds = _read_only_property("_max_cpu_seconds")
    max_deliveries = _read_only_property("_max_deliveries")
    max_deployments = _read_only_property("_max_deployments")
    max_local_commits = _read_only_property("_max_local_commits")
    max_memory_bytes = _read_only_property("_max_memory_bytes")
    max_merges = _read_only_property("_max_merges")
    max_model_input_tokens = _read_only_property("_max_model_input_tokens")
    max_model_output_tokens = _read_only_property("_max_model_output_tokens")

    @property
    def max_pull_requests(self) -> int:
        return self._max_pull_requests

    max_pushes = _read_only_property("_max_pushes")
    max_wall_seconds = _read_only_property("_max_wall_seconds")

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")

    @classmethod
    def create(
        cls,
        **fields: object,
    ) -> CeilingsV1:
        return cls.from_mapping(fields)

    @classmethod
    def from_mapping(cls, payload: object) -> CeilingsV1:
        mapping = _closed_mapping(payload, cls._FIELDS, "CeilingsV1.fields")
        _prevalidate_ceilings_mapping_types(mapping)
        values = tuple(
            _require_non_negative_integer(mapping[field], f"CeilingsV1.{field}")
            for field in cls._FIELDS
        )
        return typing.cast(CeilingsV1, _construct(cls, cls._FIELDS, values))

    def to_mapping(self) -> dict[str, object]:
        return self._to_mapping()


def _prevalidate_capsule_entry_mapping_types(mapping: dict[str, object]) -> None:
    for field in (
        "path",
        "operation",
        "mode",
        "before_blob_sha256",
        "after_blob_sha256",
    ):
        _require_exact_string(mapping[field], f"CapsuleEntryV1.{field}")
    for field in ("before_byte_length", "after_byte_length"):
        _require_exact_integer_type(mapping[field], f"CapsuleEntryV1.{field}")


class CapsuleEntryV1(_ImmutableValue):
    _FIELDS = (
        "path",
        "operation",
        "mode",
        "before_blob_sha256",
        "before_byte_length",
        "after_blob_sha256",
        "after_byte_length",
    )
    __slots__ = tuple(f"_{field}" for field in _FIELDS)

    path = _read_only_property("_path")
    operation = _read_only_property("_operation")
    mode = _read_only_property("_mode")
    before_blob_sha256 = _read_only_property("_before_blob_sha256")
    before_byte_length = _read_only_property("_before_byte_length")
    after_blob_sha256 = _read_only_property("_after_blob_sha256")
    after_byte_length = _read_only_property("_after_byte_length")

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")

    @classmethod
    def create(
        cls,
        *,
        path: str,
        mode: str,
        before_blob: bytes,
        after_blob: bytes,
    ) -> CapsuleEntryV1:
        _require_exact_string(path, "CapsuleEntryV1.path")
        _require_exact_string(mode, "CapsuleEntryV1.mode")
        if type(before_blob) is not bytes:
            _fail("invalid_field_type", "CapsuleEntryV1.before_blob")
        if type(after_blob) is not bytes:
            _fail("invalid_field_type", "CapsuleEntryV1.after_blob")
        return cls.from_mapping(
            {
                "path": path,
                "operation": "replace_regular_file",
                "mode": mode,
                "before_blob_sha256": hashlib.sha256(before_blob).hexdigest(),
                "before_byte_length": len(before_blob),
                "after_blob_sha256": hashlib.sha256(after_blob).hexdigest(),
                "after_byte_length": len(after_blob),
            }
        )

    @classmethod
    def from_mapping(cls, payload: object) -> CapsuleEntryV1:
        mapping = _closed_mapping(payload, cls._FIELDS, "CapsuleEntryV1.fields")
        _prevalidate_capsule_entry_mapping_types(mapping)
        path = _require_exact_string(mapping["path"], "CapsuleEntryV1.path")
        if path not in _AUTHORIZED_PATHS:
            _fail("invalid_field_value", "CapsuleEntryV1.path")
        operation = _require_constant(
            mapping["operation"], "replace_regular_file", "CapsuleEntryV1.operation"
        )
        mode = _require_exact_string(mapping["mode"], "CapsuleEntryV1.mode")
        if mode not in ("100644", "100755"):
            _fail("invalid_field_value", "CapsuleEntryV1.mode")
        values = (
            path,
            operation,
            mode,
            _require_digest(
                mapping["before_blob_sha256"], "CapsuleEntryV1.before_blob_sha256"
            ),
            _require_non_negative_integer(
                mapping["before_byte_length"], "CapsuleEntryV1.before_byte_length"
            ),
            _require_digest(
                mapping["after_blob_sha256"], "CapsuleEntryV1.after_blob_sha256"
            ),
            _require_non_negative_integer(
                mapping["after_byte_length"], "CapsuleEntryV1.after_byte_length"
            ),
        )
        return typing.cast(CapsuleEntryV1, _construct(cls, cls._FIELDS, values))

    def to_mapping(self) -> dict[str, object]:
        return self._to_mapping()


def _prevalidate_work_spec_mapping_types(mapping: dict[str, object]) -> None:
    for field in (
        "schema_id",
        "work_spec_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "objective",
        "validation_requirement_ref",
        "review_requirement_ref",
        "privacy_classification",
        "work_spec_digest",
    ):
        _require_exact_string(mapping[field], f"WorkSpecV1.{field}")
    for field in ("authorized_paths", "requirements", "exclusions"):
        _require_exact_string_list_type(mapping[field], f"WorkSpecV1.{field}")


class WorkSpecV1(_TopLevelValue):
    _FIELDS = (
        "schema_id",
        "work_spec_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "authorized_paths",
        "objective",
        "requirements",
        "exclusions",
        "validation_requirement_ref",
        "review_requirement_ref",
        "privacy_classification",
        "work_spec_digest",
    )
    __slots__ = tuple(f"_{field}" for field in _FIELDS)
    _DOMAIN = _WORK_SPEC_DOMAIN
    _IDENTITY_EXCLUSIONS = ("work_spec_digest",)

    schema_id = _read_only_property("_schema_id")
    work_spec_ref = _read_only_property("_work_spec_ref")
    program_ref = _read_only_property("_program_ref")
    program_version_ref = _read_only_property("_program_version_ref")
    accepted_intent_revision_ref = _read_only_property("_accepted_intent_revision_ref")
    work_item_ref = _read_only_property("_work_item_ref")
    work_item_revision_ref = _read_only_property("_work_item_revision_ref")
    repository_ref = _read_only_property("_repository_ref")
    base_git_object_format = _read_only_property("_base_git_object_format")
    base_git_oid = _read_only_property("_base_git_oid")
    authorized_paths = _read_only_property("_authorized_paths")
    objective = _read_only_property("_objective")
    requirements = _read_only_property("_requirements")
    exclusions = _read_only_property("_exclusions")
    validation_requirement_ref = _read_only_property("_validation_requirement_ref")
    review_requirement_ref = _read_only_property("_review_requirement_ref")
    privacy_classification = _read_only_property("_privacy_classification")
    work_spec_digest = _read_only_property("_work_spec_digest")

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")

    @classmethod
    def create(
        cls,
        *,
        work_spec_ref: str,
        program_ref: str,
        program_version_ref: str,
        accepted_intent_revision_ref: str,
        work_item_ref: str,
        work_item_revision_ref: str,
        repository_ref: str,
        base_git_oid: str,
        authorized_paths: list[str],
        objective: str,
        requirements: list[str],
        exclusions: list[str],
        validation_requirement_ref: str,
        review_requirement_ref: str,
    ) -> WorkSpecV1:
        for field_path, value in (
            ("WorkSpecV1.work_spec_ref", work_spec_ref),
            ("WorkSpecV1.program_ref", program_ref),
            ("WorkSpecV1.program_version_ref", program_version_ref),
            (
                "WorkSpecV1.accepted_intent_revision_ref",
                accepted_intent_revision_ref,
            ),
            ("WorkSpecV1.work_item_ref", work_item_ref),
            ("WorkSpecV1.work_item_revision_ref", work_item_revision_ref),
            ("WorkSpecV1.repository_ref", repository_ref),
            ("WorkSpecV1.base_git_oid", base_git_oid),
            ("WorkSpecV1.objective", objective),
            (
                "WorkSpecV1.validation_requirement_ref",
                validation_requirement_ref,
            ),
            ("WorkSpecV1.review_requirement_ref", review_requirement_ref),
        ):
            _require_exact_string(value, field_path)
        _require_exact_string_list_type(
            authorized_paths, "WorkSpecV1.authorized_paths"
        )
        _require_exact_string_list_type(requirements, "WorkSpecV1.requirements")
        _require_exact_string_list_type(exclusions, "WorkSpecV1.exclusions")
        identity: dict[str, object] = {
            "schema_id": _WORK_SPEC_SCHEMA,
            "work_spec_ref": work_spec_ref,
            "program_ref": program_ref,
            "program_version_ref": program_version_ref,
            "accepted_intent_revision_ref": accepted_intent_revision_ref,
            "work_item_ref": work_item_ref,
            "work_item_revision_ref": work_item_revision_ref,
            "repository_ref": repository_ref,
            "base_git_object_format": "sha1",
            "base_git_oid": base_git_oid,
            "authorized_paths": authorized_paths,
            "objective": objective,
            "requirements": requirements,
            "exclusions": exclusions,
            "validation_requirement_ref": validation_requirement_ref,
            "review_requirement_ref": review_requirement_ref,
            "privacy_classification": "private_work_spec",
        }
        identity["work_spec_digest"] = _domain_digest(
            cls._DOMAIN, _canonical_bytes(identity, "WorkSpecV1.canonical_identity")
        )
        return cls.from_mapping(identity)

    @classmethod
    def from_mapping(cls, payload: object) -> WorkSpecV1:
        mapping = _closed_mapping(payload, cls._FIELDS, "WorkSpecV1.fields")
        _prevalidate_work_spec_mapping_types(mapping)
        values = (
            _require_constant(mapping["schema_id"], _WORK_SPEC_SCHEMA, "WorkSpecV1.schema_id"),
            _require_safe_ref(mapping["work_spec_ref"], "WorkSpecV1.work_spec_ref"),
            _require_safe_ref(mapping["program_ref"], "WorkSpecV1.program_ref"),
            _require_safe_ref(
                mapping["program_version_ref"], "WorkSpecV1.program_version_ref"
            ),
            _require_safe_ref(
                mapping["accepted_intent_revision_ref"],
                "WorkSpecV1.accepted_intent_revision_ref",
            ),
            _require_safe_ref(mapping["work_item_ref"], "WorkSpecV1.work_item_ref"),
            _require_safe_ref(
                mapping["work_item_revision_ref"], "WorkSpecV1.work_item_revision_ref"
            ),
            _require_safe_ref(mapping["repository_ref"], "WorkSpecV1.repository_ref"),
            _require_constant(
                mapping["base_git_object_format"],
                "sha1",
                "WorkSpecV1.base_git_object_format",
            ),
            _require_base_oid(mapping["base_git_oid"], "WorkSpecV1.base_git_oid"),
            _require_paths(mapping["authorized_paths"], "WorkSpecV1.authorized_paths"),
            _require_private_string(mapping["objective"], "WorkSpecV1.objective"),
            _require_private_string_array(mapping["requirements"], "WorkSpecV1.requirements"),
            _require_private_string_array(mapping["exclusions"], "WorkSpecV1.exclusions"),
            _require_safe_ref(
                mapping["validation_requirement_ref"],
                "WorkSpecV1.validation_requirement_ref",
            ),
            _require_safe_ref(
                mapping["review_requirement_ref"], "WorkSpecV1.review_requirement_ref"
            ),
            _require_constant(
                mapping["privacy_classification"],
                "private_work_spec",
                "WorkSpecV1.privacy_classification",
            ),
            _require_digest(mapping["work_spec_digest"], "WorkSpecV1.work_spec_digest"),
        )
        result = typing.cast(WorkSpecV1, _construct(cls, cls._FIELDS, values))
        if result.work_spec_digest != result.computed_digest():
            _fail("digest_mismatch", "WorkSpecV1.work_spec_digest")
        return result

    def to_mapping(self) -> dict[str, object]:
        return self._to_mapping()


def _prevalidate_attempt_fence_mapping_types(mapping: dict[str, object]) -> None:
    for field in (
        "schema_id",
        "attempt_fence_ref",
        "parent_standing_grant_ref",
        "parent_standing_grant_digest",
        "attempt_authorization_ref",
        "attempt_authorization_digest",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "expires_at",
        "global_stop_ref",
        "attempt_fence_digest",
    ):
        _require_exact_string(mapping[field], f"AttemptFenceV1.{field}")
    _require_exact_string_list_type(
        mapping["path_ceiling"], "AttemptFenceV1.path_ceiling"
    )
    _require_exact_string_list_type(
        mapping["allowed_effect_classes"],
        "AttemptFenceV1.allowed_effect_classes",
    )
    _require_exact_integer_type(
        mapping["global_stop_version"], "AttemptFenceV1.global_stop_version"
    )
    aggregate_mapping = _closed_mapping(
        mapping["aggregate_ceilings"],
        _CEILING_FIELDS,
        "AttemptFenceV1.aggregate_ceilings",
    )
    _prevalidate_ceilings_mapping_types(aggregate_mapping)


class AttemptFenceV1(_TopLevelValue):
    _FIELDS = (
        "schema_id",
        "attempt_fence_ref",
        "parent_standing_grant_ref",
        "parent_standing_grant_digest",
        "attempt_authorization_ref",
        "attempt_authorization_digest",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "path_ceiling",
        "allowed_effect_classes",
        "aggregate_ceilings",
        "expires_at",
        "global_stop_ref",
        "global_stop_version",
        "attempt_fence_digest",
    )
    __slots__ = tuple(f"_{field}" for field in _FIELDS)
    _DOMAIN = _ATTEMPT_FENCE_DOMAIN
    _IDENTITY_EXCLUSIONS = ("attempt_fence_digest",)

    schema_id = _read_only_property("_schema_id")
    attempt_fence_ref = _read_only_property("_attempt_fence_ref")
    parent_standing_grant_ref = _read_only_property("_parent_standing_grant_ref")
    parent_standing_grant_digest = _read_only_property("_parent_standing_grant_digest")
    attempt_authorization_ref = _read_only_property("_attempt_authorization_ref")
    attempt_authorization_digest = _read_only_property("_attempt_authorization_digest")
    program_ref = _read_only_property("_program_ref")
    program_version_ref = _read_only_property("_program_version_ref")
    accepted_intent_revision_ref = _read_only_property("_accepted_intent_revision_ref")
    work_item_ref = _read_only_property("_work_item_ref")
    work_item_revision_ref = _read_only_property("_work_item_revision_ref")
    semantic_attempt_ref = _read_only_property("_semantic_attempt_ref")
    repository_ref = _read_only_property("_repository_ref")
    base_git_object_format = _read_only_property("_base_git_object_format")
    base_git_oid = _read_only_property("_base_git_oid")
    path_ceiling = _read_only_property("_path_ceiling")
    allowed_effect_classes = _read_only_property("_allowed_effect_classes")
    aggregate_ceilings = _read_only_property("_aggregate_ceilings")
    expires_at = _read_only_property("_expires_at")
    global_stop_ref = _read_only_property("_global_stop_ref")
    global_stop_version = _read_only_property("_global_stop_version")
    attempt_fence_digest = _read_only_property("_attempt_fence_digest")

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")

    @classmethod
    def create(
        cls,
        *,
        attempt_fence_ref: str,
        parent_standing_grant_ref: str,
        parent_standing_grant_digest: str,
        attempt_authorization_ref: str,
        attempt_authorization_digest: str,
        program_ref: str,
        program_version_ref: str,
        accepted_intent_revision_ref: str,
        work_item_ref: str,
        work_item_revision_ref: str,
        semantic_attempt_ref: str,
        repository_ref: str,
        base_git_oid: str,
        path_ceiling: list[str],
        allowed_effect_classes: list[str],
        aggregate_ceilings: CeilingsV1,
        expires_at: str,
        global_stop_ref: str,
        global_stop_version: int,
    ) -> AttemptFenceV1:
        for field_path, value in (
            ("AttemptFenceV1.attempt_fence_ref", attempt_fence_ref),
            (
                "AttemptFenceV1.parent_standing_grant_ref",
                parent_standing_grant_ref,
            ),
            (
                "AttemptFenceV1.parent_standing_grant_digest",
                parent_standing_grant_digest,
            ),
            (
                "AttemptFenceV1.attempt_authorization_ref",
                attempt_authorization_ref,
            ),
            (
                "AttemptFenceV1.attempt_authorization_digest",
                attempt_authorization_digest,
            ),
            ("AttemptFenceV1.program_ref", program_ref),
            ("AttemptFenceV1.program_version_ref", program_version_ref),
            (
                "AttemptFenceV1.accepted_intent_revision_ref",
                accepted_intent_revision_ref,
            ),
            ("AttemptFenceV1.work_item_ref", work_item_ref),
            ("AttemptFenceV1.work_item_revision_ref", work_item_revision_ref),
            ("AttemptFenceV1.semantic_attempt_ref", semantic_attempt_ref),
            ("AttemptFenceV1.repository_ref", repository_ref),
            ("AttemptFenceV1.base_git_oid", base_git_oid),
            ("AttemptFenceV1.expires_at", expires_at),
            ("AttemptFenceV1.global_stop_ref", global_stop_ref),
        ):
            _require_exact_string(value, field_path)
        _require_exact_string_list_type(
            path_ceiling, "AttemptFenceV1.path_ceiling"
        )
        _require_exact_string_list_type(
            allowed_effect_classes,
            "AttemptFenceV1.allowed_effect_classes",
        )
        _require_factory_exact_value(
            aggregate_ceilings,
            CeilingsV1,
            "AttemptFenceV1.aggregate_ceilings",
        )
        _require_exact_integer_type(
            global_stop_version, "AttemptFenceV1.global_stop_version"
        )
        identity: dict[str, object] = {
            "schema_id": _ATTEMPT_FENCE_SCHEMA,
            "attempt_fence_ref": attempt_fence_ref,
            "parent_standing_grant_ref": parent_standing_grant_ref,
            "parent_standing_grant_digest": parent_standing_grant_digest,
            "attempt_authorization_ref": attempt_authorization_ref,
            "attempt_authorization_digest": attempt_authorization_digest,
            "program_ref": program_ref,
            "program_version_ref": program_version_ref,
            "accepted_intent_revision_ref": accepted_intent_revision_ref,
            "work_item_ref": work_item_ref,
            "work_item_revision_ref": work_item_revision_ref,
            "semantic_attempt_ref": semantic_attempt_ref,
            "repository_ref": repository_ref,
            "base_git_object_format": "sha1",
            "base_git_oid": base_git_oid,
            "path_ceiling": path_ceiling,
            "allowed_effect_classes": allowed_effect_classes,
            "aggregate_ceilings": aggregate_ceilings.to_mapping(),
            "expires_at": expires_at,
            "global_stop_ref": global_stop_ref,
            "global_stop_version": global_stop_version,
        }
        identity["attempt_fence_digest"] = _domain_digest(
            cls._DOMAIN, _canonical_bytes(identity, "AttemptFenceV1.canonical_identity")
        )
        return cls.from_mapping(identity)

    @classmethod
    def from_mapping(cls, payload: object) -> AttemptFenceV1:
        mapping = _closed_mapping(payload, cls._FIELDS, "AttemptFenceV1.fields")
        _prevalidate_attempt_fence_mapping_types(mapping)
        values = (
            _require_constant(
                mapping["schema_id"], _ATTEMPT_FENCE_SCHEMA, "AttemptFenceV1.schema_id"
            ),
            _require_safe_ref(mapping["attempt_fence_ref"], "AttemptFenceV1.attempt_fence_ref"),
            _require_safe_ref(
                mapping["parent_standing_grant_ref"],
                "AttemptFenceV1.parent_standing_grant_ref",
            ),
            _require_digest(
                mapping["parent_standing_grant_digest"],
                "AttemptFenceV1.parent_standing_grant_digest",
            ),
            _require_safe_ref(
                mapping["attempt_authorization_ref"],
                "AttemptFenceV1.attempt_authorization_ref",
            ),
            _require_digest(
                mapping["attempt_authorization_digest"],
                "AttemptFenceV1.attempt_authorization_digest",
            ),
            _require_safe_ref(mapping["program_ref"], "AttemptFenceV1.program_ref"),
            _require_safe_ref(
                mapping["program_version_ref"], "AttemptFenceV1.program_version_ref"
            ),
            _require_safe_ref(
                mapping["accepted_intent_revision_ref"],
                "AttemptFenceV1.accepted_intent_revision_ref",
            ),
            _require_safe_ref(mapping["work_item_ref"], "AttemptFenceV1.work_item_ref"),
            _require_safe_ref(
                mapping["work_item_revision_ref"],
                "AttemptFenceV1.work_item_revision_ref",
            ),
            _require_safe_ref(
                mapping["semantic_attempt_ref"], "AttemptFenceV1.semantic_attempt_ref"
            ),
            _require_safe_ref(mapping["repository_ref"], "AttemptFenceV1.repository_ref"),
            _require_constant(
                mapping["base_git_object_format"],
                "sha1",
                "AttemptFenceV1.base_git_object_format",
            ),
            _require_base_oid(mapping["base_git_oid"], "AttemptFenceV1.base_git_oid"),
            _require_paths(mapping["path_ceiling"], "AttemptFenceV1.path_ceiling"),
            _require_allowed_effect_classes(
                mapping["allowed_effect_classes"],
                "AttemptFenceV1.allowed_effect_classes",
            ),
            CeilingsV1.from_mapping(mapping["aggregate_ceilings"]),
            _require_timestamp(mapping["expires_at"], "AttemptFenceV1.expires_at"),
            _require_safe_ref(mapping["global_stop_ref"], "AttemptFenceV1.global_stop_ref"),
            _require_non_negative_integer(
                mapping["global_stop_version"], "AttemptFenceV1.global_stop_version"
            ),
            _require_digest(
                mapping["attempt_fence_digest"], "AttemptFenceV1.attempt_fence_digest"
            ),
        )
        result = typing.cast(AttemptFenceV1, _construct(cls, cls._FIELDS, values))
        if result.attempt_fence_digest != result.computed_digest():
            _fail("digest_mismatch", "AttemptFenceV1.attempt_fence_digest")
        return result

    def to_mapping(self) -> dict[str, object]:
        return self._to_mapping()


def _prevalidate_effect_fence_mapping_types(mapping: dict[str, object]) -> None:
    for field in (
        "schema_id",
        "effect_fence_ref",
        "parent_standing_grant_ref",
        "parent_standing_grant_digest",
        "effect_authorization_ref",
        "effect_authorization_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "effect_class",
        "command_ref",
        "command_digest",
        "candidate_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "expires_at",
        "global_stop_ref",
        "effect_fence_digest",
    ):
        _require_exact_string(mapping[field], f"EffectFenceV1.{field}")
    _require_exact_string_list_type(
        mapping["path_ceiling"], "EffectFenceV1.path_ceiling"
    )
    _require_exact_integer_type(
        mapping["global_stop_version"], "EffectFenceV1.global_stop_version"
    )
    for field in (
        "portable_capsule_digest",
        "cancellation_target_effect_intent_ref",
        "cancellation_target_effect_fence_ref",
        "cancellation_target_effect_fence_digest",
    ):
        _require_nullable_exact_string_type(
            mapping[field], f"EffectFenceV1.{field}"
        )
    ceilings_mapping = _closed_mapping(
        mapping["effect_ceilings"],
        _CEILING_FIELDS,
        "EffectFenceV1.effect_ceilings",
    )
    _prevalidate_ceilings_mapping_types(ceilings_mapping)


class EffectFenceV1(_TopLevelValue):
    _FIELDS = (
        "schema_id",
        "effect_fence_ref",
        "parent_standing_grant_ref",
        "parent_standing_grant_digest",
        "effect_authorization_ref",
        "effect_authorization_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "effect_class",
        "command_ref",
        "command_digest",
        "candidate_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "path_ceiling",
        "effect_ceilings",
        "expires_at",
        "global_stop_ref",
        "global_stop_version",
        "portable_capsule_digest",
        "cancellation_target_effect_intent_ref",
        "cancellation_target_effect_fence_ref",
        "cancellation_target_effect_fence_digest",
        "effect_fence_digest",
    )
    __slots__ = tuple(f"_{field}" for field in _FIELDS)
    _DOMAIN = _EFFECT_FENCE_DOMAIN
    _IDENTITY_EXCLUSIONS = ("effect_fence_digest",)

    schema_id = _read_only_property("_schema_id")
    effect_fence_ref = _read_only_property("_effect_fence_ref")
    parent_standing_grant_ref = _read_only_property("_parent_standing_grant_ref")
    parent_standing_grant_digest = _read_only_property("_parent_standing_grant_digest")
    effect_authorization_ref = _read_only_property("_effect_authorization_ref")
    effect_authorization_digest = _read_only_property("_effect_authorization_digest")
    attempt_fence_ref = _read_only_property("_attempt_fence_ref")
    attempt_fence_digest = _read_only_property("_attempt_fence_digest")
    program_ref = _read_only_property("_program_ref")
    program_version_ref = _read_only_property("_program_version_ref")
    accepted_intent_revision_ref = _read_only_property("_accepted_intent_revision_ref")
    work_item_ref = _read_only_property("_work_item_ref")
    work_item_revision_ref = _read_only_property("_work_item_revision_ref")
    semantic_attempt_ref = _read_only_property("_semantic_attempt_ref")
    effect_intent_ref = _read_only_property("_effect_intent_ref")
    effect_class = _read_only_property("_effect_class")
    command_ref = _read_only_property("_command_ref")
    command_digest = _read_only_property("_command_digest")
    candidate_ref = _read_only_property("_candidate_ref")
    repository_ref = _read_only_property("_repository_ref")
    base_git_object_format = _read_only_property("_base_git_object_format")
    base_git_oid = _read_only_property("_base_git_oid")
    path_ceiling = _read_only_property("_path_ceiling")
    effect_ceilings = _read_only_property("_effect_ceilings")
    expires_at = _read_only_property("_expires_at")
    global_stop_ref = _read_only_property("_global_stop_ref")
    global_stop_version = _read_only_property("_global_stop_version")
    portable_capsule_digest = _read_only_property("_portable_capsule_digest")
    cancellation_target_effect_intent_ref = _read_only_property(
        "_cancellation_target_effect_intent_ref"
    )
    cancellation_target_effect_fence_ref = _read_only_property(
        "_cancellation_target_effect_fence_ref"
    )
    cancellation_target_effect_fence_digest = _read_only_property(
        "_cancellation_target_effect_fence_digest"
    )
    effect_fence_digest = _read_only_property("_effect_fence_digest")

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")

    @classmethod
    def from_mapping(cls, payload: object) -> EffectFenceV1:
        mapping = _closed_mapping(payload, cls._FIELDS, "EffectFenceV1.fields")
        _prevalidate_effect_fence_mapping_types(mapping)
        nullable_ref_fields = (
            "cancellation_target_effect_intent_ref",
            "cancellation_target_effect_fence_ref",
        )
        nullable_refs: list[str | None] = []
        for field in nullable_ref_fields:
            value = mapping[field]
            nullable_refs.append(
                None
                if value is None
                else _require_safe_ref(value, f"EffectFenceV1.{field}")
            )
        target_digest_value = mapping["cancellation_target_effect_fence_digest"]
        target_digest = (
            None
            if target_digest_value is None
            else _require_digest(
                target_digest_value,
                "EffectFenceV1.cancellation_target_effect_fence_digest",
            )
        )
        capsule_value = mapping["portable_capsule_digest"]
        capsule_digest = (
            None
            if capsule_value is None
            else _require_digest(capsule_value, "EffectFenceV1.portable_capsule_digest")
        )
        effect_class = _require_exact_string(mapping["effect_class"], "EffectFenceV1.effect_class")
        if effect_class not in _EFFECT_CLASSES:
            _fail("invalid_field_value", "EffectFenceV1.effect_class")
        target_tuple = (nullable_refs[0], nullable_refs[1], target_digest)
        if effect_class == "cancel_effect":
            if any(value is None for value in target_tuple):
                _fail("invalid_field_value", "EffectFenceV1.cancellation_target")
        elif target_tuple != (None, None, None):
            _fail("invalid_field_value", "EffectFenceV1.cancellation_target")
        if effect_class == "author_candidate" and capsule_digest is not None:
            _fail("invalid_field_value", "EffectFenceV1.portable_capsule_digest")
        if effect_class in ("validate_candidate", "review_candidate", "local_git_commit"):
            if capsule_digest is None:
                _fail("invalid_field_value", "EffectFenceV1.portable_capsule_digest")
        values = (
            _require_constant(
                mapping["schema_id"], _EFFECT_FENCE_SCHEMA, "EffectFenceV1.schema_id"
            ),
            _require_safe_ref(mapping["effect_fence_ref"], "EffectFenceV1.effect_fence_ref"),
            _require_safe_ref(
                mapping["parent_standing_grant_ref"],
                "EffectFenceV1.parent_standing_grant_ref",
            ),
            _require_digest(
                mapping["parent_standing_grant_digest"],
                "EffectFenceV1.parent_standing_grant_digest",
            ),
            _require_safe_ref(
                mapping["effect_authorization_ref"],
                "EffectFenceV1.effect_authorization_ref",
            ),
            _require_digest(
                mapping["effect_authorization_digest"],
                "EffectFenceV1.effect_authorization_digest",
            ),
            _require_safe_ref(mapping["attempt_fence_ref"], "EffectFenceV1.attempt_fence_ref"),
            _require_digest(
                mapping["attempt_fence_digest"], "EffectFenceV1.attempt_fence_digest"
            ),
            _require_safe_ref(mapping["program_ref"], "EffectFenceV1.program_ref"),
            _require_safe_ref(
                mapping["program_version_ref"], "EffectFenceV1.program_version_ref"
            ),
            _require_safe_ref(
                mapping["accepted_intent_revision_ref"],
                "EffectFenceV1.accepted_intent_revision_ref",
            ),
            _require_safe_ref(mapping["work_item_ref"], "EffectFenceV1.work_item_ref"),
            _require_safe_ref(
                mapping["work_item_revision_ref"], "EffectFenceV1.work_item_revision_ref"
            ),
            _require_safe_ref(
                mapping["semantic_attempt_ref"], "EffectFenceV1.semantic_attempt_ref"
            ),
            _require_safe_ref(mapping["effect_intent_ref"], "EffectFenceV1.effect_intent_ref"),
            effect_class,
            _require_safe_ref(mapping["command_ref"], "EffectFenceV1.command_ref"),
            _require_digest(mapping["command_digest"], "EffectFenceV1.command_digest"),
            _require_safe_ref(mapping["candidate_ref"], "EffectFenceV1.candidate_ref"),
            _require_safe_ref(mapping["repository_ref"], "EffectFenceV1.repository_ref"),
            _require_constant(
                mapping["base_git_object_format"],
                "sha1",
                "EffectFenceV1.base_git_object_format",
            ),
            _require_base_oid(mapping["base_git_oid"], "EffectFenceV1.base_git_oid"),
            _require_paths(mapping["path_ceiling"], "EffectFenceV1.path_ceiling"),
            CeilingsV1.from_mapping(mapping["effect_ceilings"]),
            _require_timestamp(mapping["expires_at"], "EffectFenceV1.expires_at"),
            _require_safe_ref(mapping["global_stop_ref"], "EffectFenceV1.global_stop_ref"),
            _require_non_negative_integer(
                mapping["global_stop_version"], "EffectFenceV1.global_stop_version"
            ),
            capsule_digest,
            nullable_refs[0],
            nullable_refs[1],
            target_digest,
            _require_digest(mapping["effect_fence_digest"], "EffectFenceV1.effect_fence_digest"),
        )
        result = typing.cast(EffectFenceV1, _construct(cls, cls._FIELDS, values))
        if result.effect_fence_digest != result.computed_digest():
            _fail("digest_mismatch", "EffectFenceV1.effect_fence_digest")
        return result

    def to_mapping(self) -> dict[str, object]:
        return self._to_mapping()


def _prevalidate_worker_command_mapping_types(mapping: dict[str, object]) -> None:
    for field in (
        "schema_id",
        "command_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "effect_class",
        "candidate_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "work_spec_ref",
        "work_spec_digest",
        "standing_grant_ref",
        "standing_grant_digest",
        "attempt_authorization_ref",
        "attempt_authorization_digest",
        "effect_authorization_ref",
        "effect_authorization_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
        "global_stop_ref",
        "validation_requirement_ref",
        "validation_requirement_digest",
        "review_requirement_ref",
        "review_requirement_digest",
        "capsule_schema_id",
        "capsule_profile_ref",
        "privacy_classification",
        "redaction_profile_ref",
        "command_digest",
    ):
        _require_exact_string(mapping[field], f"WorkerCommandV1.{field}")
    _require_exact_string_list_type(
        mapping["path_ceiling"], "WorkerCommandV1.path_ceiling"
    )
    _require_exact_integer_type(
        mapping["global_stop_version"], "WorkerCommandV1.global_stop_version"
    )
    ceilings_mapping = _closed_mapping(
        mapping["effect_ceilings"],
        _CEILING_FIELDS,
        "WorkerCommandV1.effect_ceilings",
    )
    _prevalidate_ceilings_mapping_types(ceilings_mapping)


class WorkerCommandV1(_TopLevelValue):
    _FIELDS = (
        "schema_id",
        "command_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "effect_class",
        "candidate_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "path_ceiling",
        "work_spec_ref",
        "work_spec_digest",
        "standing_grant_ref",
        "standing_grant_digest",
        "attempt_authorization_ref",
        "attempt_authorization_digest",
        "effect_authorization_ref",
        "effect_authorization_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
        "global_stop_ref",
        "global_stop_version",
        "validation_requirement_ref",
        "validation_requirement_digest",
        "review_requirement_ref",
        "review_requirement_digest",
        "capsule_schema_id",
        "capsule_profile_ref",
        "effect_ceilings",
        "privacy_classification",
        "redaction_profile_ref",
        "command_digest",
    )
    __slots__ = tuple(f"_{field}" for field in _FIELDS)
    _DOMAIN = _WORKER_COMMAND_DOMAIN
    _IDENTITY_EXCLUSIONS = ("effect_fence_digest", "command_digest")

    schema_id = _read_only_property("_schema_id")
    command_ref = _read_only_property("_command_ref")
    program_ref = _read_only_property("_program_ref")
    program_version_ref = _read_only_property("_program_version_ref")
    accepted_intent_revision_ref = _read_only_property("_accepted_intent_revision_ref")
    work_item_ref = _read_only_property("_work_item_ref")
    work_item_revision_ref = _read_only_property("_work_item_revision_ref")
    semantic_attempt_ref = _read_only_property("_semantic_attempt_ref")
    effect_intent_ref = _read_only_property("_effect_intent_ref")
    effect_class = _read_only_property("_effect_class")
    candidate_ref = _read_only_property("_candidate_ref")
    repository_ref = _read_only_property("_repository_ref")
    base_git_object_format = _read_only_property("_base_git_object_format")
    base_git_oid = _read_only_property("_base_git_oid")
    path_ceiling = _read_only_property("_path_ceiling")
    work_spec_ref = _read_only_property("_work_spec_ref")
    work_spec_digest = _read_only_property("_work_spec_digest")
    standing_grant_ref = _read_only_property("_standing_grant_ref")
    standing_grant_digest = _read_only_property("_standing_grant_digest")
    attempt_authorization_ref = _read_only_property("_attempt_authorization_ref")
    attempt_authorization_digest = _read_only_property("_attempt_authorization_digest")
    effect_authorization_ref = _read_only_property("_effect_authorization_ref")
    effect_authorization_digest = _read_only_property("_effect_authorization_digest")
    attempt_fence_ref = _read_only_property("_attempt_fence_ref")
    attempt_fence_digest = _read_only_property("_attempt_fence_digest")
    effect_fence_ref = _read_only_property("_effect_fence_ref")
    effect_fence_digest = _read_only_property("_effect_fence_digest")
    global_stop_ref = _read_only_property("_global_stop_ref")
    global_stop_version = _read_only_property("_global_stop_version")
    validation_requirement_ref = _read_only_property("_validation_requirement_ref")
    validation_requirement_digest = _read_only_property("_validation_requirement_digest")
    review_requirement_ref = _read_only_property("_review_requirement_ref")
    review_requirement_digest = _read_only_property("_review_requirement_digest")
    capsule_schema_id = _read_only_property("_capsule_schema_id")
    capsule_profile_ref = _read_only_property("_capsule_profile_ref")
    effect_ceilings = _read_only_property("_effect_ceilings")
    privacy_classification = _read_only_property("_privacy_classification")
    redaction_profile_ref = _read_only_property("_redaction_profile_ref")
    command_digest = _read_only_property("_command_digest")

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")

    @classmethod
    def from_mapping(cls, payload: object) -> WorkerCommandV1:
        mapping = _closed_mapping(payload, cls._FIELDS, "WorkerCommandV1.fields")
        _prevalidate_worker_command_mapping_types(mapping)
        ceilings = CeilingsV1.from_mapping(mapping["effect_ceilings"])
        if not _non_git_effect_ceilings(ceilings):
            _fail("invalid_field_value", "WorkerCommandV1.effect_ceilings")
        ref_fields = (
            "command_ref",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "work_item_ref",
            "work_item_revision_ref",
            "semantic_attempt_ref",
            "effect_intent_ref",
            "candidate_ref",
            "repository_ref",
            "work_spec_ref",
            "standing_grant_ref",
            "attempt_authorization_ref",
            "effect_authorization_ref",
            "attempt_fence_ref",
            "effect_fence_ref",
            "global_stop_ref",
            "validation_requirement_ref",
            "review_requirement_ref",
            "capsule_profile_ref",
            "redaction_profile_ref",
        )
        refs = {
            field: _require_safe_ref(mapping[field], f"WorkerCommandV1.{field}")
            for field in ref_fields
        }
        digest_fields = (
            "work_spec_digest",
            "standing_grant_digest",
            "attempt_authorization_digest",
            "effect_authorization_digest",
            "attempt_fence_digest",
            "effect_fence_digest",
            "validation_requirement_digest",
            "review_requirement_digest",
            "command_digest",
        )
        digests = {
            field: _require_digest(mapping[field], f"WorkerCommandV1.{field}")
            for field in digest_fields
        }
        values = (
            _require_constant(
                mapping["schema_id"], _WORKER_COMMAND_SCHEMA, "WorkerCommandV1.schema_id"
            ),
            refs["command_ref"],
            refs["program_ref"],
            refs["program_version_ref"],
            refs["accepted_intent_revision_ref"],
            refs["work_item_ref"],
            refs["work_item_revision_ref"],
            refs["semantic_attempt_ref"],
            refs["effect_intent_ref"],
            _require_constant(
                mapping["effect_class"], "author_candidate", "WorkerCommandV1.effect_class"
            ),
            refs["candidate_ref"],
            refs["repository_ref"],
            _require_constant(
                mapping["base_git_object_format"],
                "sha1",
                "WorkerCommandV1.base_git_object_format",
            ),
            _require_base_oid(mapping["base_git_oid"], "WorkerCommandV1.base_git_oid"),
            _require_paths(mapping["path_ceiling"], "WorkerCommandV1.path_ceiling"),
            refs["work_spec_ref"],
            digests["work_spec_digest"],
            refs["standing_grant_ref"],
            digests["standing_grant_digest"],
            refs["attempt_authorization_ref"],
            digests["attempt_authorization_digest"],
            refs["effect_authorization_ref"],
            digests["effect_authorization_digest"],
            refs["attempt_fence_ref"],
            digests["attempt_fence_digest"],
            refs["effect_fence_ref"],
            digests["effect_fence_digest"],
            refs["global_stop_ref"],
            _require_non_negative_integer(
                mapping["global_stop_version"], "WorkerCommandV1.global_stop_version"
            ),
            refs["validation_requirement_ref"],
            digests["validation_requirement_digest"],
            refs["review_requirement_ref"],
            digests["review_requirement_digest"],
            _require_constant(
                mapping["capsule_schema_id"],
                _CAPSULE_MANIFEST_SCHEMA,
                "WorkerCommandV1.capsule_schema_id",
            ),
            refs["capsule_profile_ref"],
            ceilings,
            _require_constant(
                mapping["privacy_classification"],
                "private_source_change",
                "WorkerCommandV1.privacy_classification",
            ),
            refs["redaction_profile_ref"],
            digests["command_digest"],
        )
        result = typing.cast(WorkerCommandV1, _construct(cls, cls._FIELDS, values))
        if result.command_digest != result.computed_digest():
            _fail("digest_mismatch", "WorkerCommandV1.command_digest")
        return result

    def to_mapping(self) -> dict[str, object]:
        return self._to_mapping()


def _prevalidate_delivery_envelope_mapping_types(
    mapping: dict[str, object],
) -> None:
    for field in DeliveryEnvelopeV1._FIELDS:
        _require_exact_string(mapping[field], f"DeliveryEnvelopeV1.{field}")


class DeliveryEnvelopeV1(_TopLevelValue):
    _FIELDS = (
        "schema_id",
        "delivery_attempt_ref",
        "program_ref",
        "program_version_ref",
        "command_ref",
        "command_digest",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
        "adapter_kind",
        "adapter_safe_correlation_ref",
        "delivery_envelope_digest",
    )
    __slots__ = tuple(f"_{field}" for field in _FIELDS)
    _DOMAIN = _DELIVERY_ENVELOPE_DOMAIN
    _IDENTITY_EXCLUSIONS = ("delivery_envelope_digest",)

    schema_id = _read_only_property("_schema_id")
    delivery_attempt_ref = _read_only_property("_delivery_attempt_ref")
    program_ref = _read_only_property("_program_ref")
    program_version_ref = _read_only_property("_program_version_ref")
    command_ref = _read_only_property("_command_ref")
    command_digest = _read_only_property("_command_digest")
    semantic_attempt_ref = _read_only_property("_semantic_attempt_ref")
    effect_intent_ref = _read_only_property("_effect_intent_ref")
    attempt_fence_ref = _read_only_property("_attempt_fence_ref")
    attempt_fence_digest = _read_only_property("_attempt_fence_digest")
    effect_fence_ref = _read_only_property("_effect_fence_ref")
    effect_fence_digest = _read_only_property("_effect_fence_digest")
    adapter_kind = _read_only_property("_adapter_kind")
    adapter_safe_correlation_ref = _read_only_property("_adapter_safe_correlation_ref")
    delivery_envelope_digest = _read_only_property("_delivery_envelope_digest")

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")

    @classmethod
    def create(
        cls,
        *,
        delivery_attempt_ref: str,
        adapter_kind: str,
        adapter_safe_correlation_ref: str,
        author_command: WorkerCommandV1,
        attempt_fence: AttemptFenceV1,
        author_effect_fence: EffectFenceV1,
        effect_fence: EffectFenceV1,
        capsule_manifest: object = _MISSING,
        cancellation_target: object = _MISSING,
    ) -> DeliveryEnvelopeV1:
        _require_exact_string(
            delivery_attempt_ref, "DeliveryEnvelopeV1.delivery_attempt_ref"
        )
        _require_exact_string(adapter_kind, "DeliveryEnvelopeV1.adapter_kind")
        _require_exact_string(
            adapter_safe_correlation_ref,
            "DeliveryEnvelopeV1.adapter_safe_correlation_ref",
        )
        _require_factory_exact_value(
            author_command, WorkerCommandV1, "DeliveryEnvelopeV1.author_command"
        )
        _require_factory_exact_value(
            attempt_fence, AttemptFenceV1, "DeliveryEnvelopeV1.attempt_fence"
        )
        _require_factory_exact_value(
            author_effect_fence,
            EffectFenceV1,
            "DeliveryEnvelopeV1.author_effect_fence",
        )
        _require_factory_exact_value(
            effect_fence, EffectFenceV1, "DeliveryEnvelopeV1.effect_fence"
        )
        _require_optional_factory_exact_value(
            capsule_manifest,
            CandidateCapsuleManifestV1,
            "DeliveryEnvelopeV1.capsule_manifest",
        )
        _require_optional_factory_exact_value(
            cancellation_target,
            EffectFenceV1,
            "DeliveryEnvelopeV1.cancellation_target",
        )
        validate_effect_relation(
            attempt_fence=attempt_fence,
            author_command=author_command,
            author_effect_fence=author_effect_fence,
            effect_fence=effect_fence,
            capsule_manifest=capsule_manifest,
            cancellation_target=cancellation_target,
        )
        identity: dict[str, object] = {
            "schema_id": _DELIVERY_ENVELOPE_SCHEMA,
            "delivery_attempt_ref": delivery_attempt_ref,
            "program_ref": effect_fence.program_ref,
            "program_version_ref": effect_fence.program_version_ref,
            "command_ref": author_command.command_ref,
            "command_digest": author_command.command_digest,
            "semantic_attempt_ref": effect_fence.semantic_attempt_ref,
            "effect_intent_ref": effect_fence.effect_intent_ref,
            "attempt_fence_ref": attempt_fence.attempt_fence_ref,
            "attempt_fence_digest": attempt_fence.attempt_fence_digest,
            "effect_fence_ref": effect_fence.effect_fence_ref,
            "effect_fence_digest": effect_fence.effect_fence_digest,
            "adapter_kind": adapter_kind,
            "adapter_safe_correlation_ref": adapter_safe_correlation_ref,
        }
        identity["delivery_envelope_digest"] = _domain_digest(
            cls._DOMAIN,
            _canonical_bytes(identity, "DeliveryEnvelopeV1.canonical_identity"),
        )
        result = cls.from_mapping(identity)
        validate_delivery_relation(
            delivery=result,
            author_command=author_command,
            attempt_fence=attempt_fence,
            author_effect_fence=author_effect_fence,
            effect_fence=effect_fence,
            capsule_manifest=capsule_manifest,
            cancellation_target=cancellation_target,
        )
        return result

    @classmethod
    def from_mapping(cls, payload: object) -> DeliveryEnvelopeV1:
        mapping = _closed_mapping(payload, cls._FIELDS, "DeliveryEnvelopeV1.fields")
        _prevalidate_delivery_envelope_mapping_types(mapping)
        adapter_kind = _require_exact_string(
            mapping["adapter_kind"], "DeliveryEnvelopeV1.adapter_kind"
        )
        if adapter_kind not in _ADAPTER_KINDS:
            _fail("invalid_field_value", "DeliveryEnvelopeV1.adapter_kind")
        values = (
            _require_constant(
                mapping["schema_id"],
                _DELIVERY_ENVELOPE_SCHEMA,
                "DeliveryEnvelopeV1.schema_id",
            ),
            _require_safe_ref(
                mapping["delivery_attempt_ref"], "DeliveryEnvelopeV1.delivery_attempt_ref"
            ),
            _require_safe_ref(mapping["program_ref"], "DeliveryEnvelopeV1.program_ref"),
            _require_safe_ref(
                mapping["program_version_ref"], "DeliveryEnvelopeV1.program_version_ref"
            ),
            _require_safe_ref(mapping["command_ref"], "DeliveryEnvelopeV1.command_ref"),
            _require_digest(mapping["command_digest"], "DeliveryEnvelopeV1.command_digest"),
            _require_safe_ref(
                mapping["semantic_attempt_ref"], "DeliveryEnvelopeV1.semantic_attempt_ref"
            ),
            _require_safe_ref(
                mapping["effect_intent_ref"], "DeliveryEnvelopeV1.effect_intent_ref"
            ),
            _require_safe_ref(
                mapping["attempt_fence_ref"], "DeliveryEnvelopeV1.attempt_fence_ref"
            ),
            _require_digest(
                mapping["attempt_fence_digest"], "DeliveryEnvelopeV1.attempt_fence_digest"
            ),
            _require_safe_ref(
                mapping["effect_fence_ref"], "DeliveryEnvelopeV1.effect_fence_ref"
            ),
            _require_digest(
                mapping["effect_fence_digest"], "DeliveryEnvelopeV1.effect_fence_digest"
            ),
            adapter_kind,
            _require_safe_ref(
                mapping["adapter_safe_correlation_ref"],
                "DeliveryEnvelopeV1.adapter_safe_correlation_ref",
            ),
            _require_digest(
                mapping["delivery_envelope_digest"],
                "DeliveryEnvelopeV1.delivery_envelope_digest",
            ),
        )
        result = typing.cast(DeliveryEnvelopeV1, _construct(cls, cls._FIELDS, values))
        if result.delivery_envelope_digest != result.computed_digest():
            _fail("digest_mismatch", "DeliveryEnvelopeV1.delivery_envelope_digest")
        return result

    def to_mapping(self) -> dict[str, object]:
        return self._to_mapping()


def _prevalidate_capsule_manifest_mapping_types(
    mapping: dict[str, object],
) -> None:
    for field in (
        "schema_id",
        "canonicalization_profile",
        "digest_domain",
        "candidate_ref",
        "capsule_manifest_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "command_ref",
        "command_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "authorized_path_scope_digest",
        "portable_capsule_digest",
    ):
        _require_exact_string(
            mapping[field], f"CandidateCapsuleManifestV1.{field}"
        )
    entries_value = mapping["entries"]
    if type(entries_value) is not list:
        _fail("invalid_field_type", "CandidateCapsuleManifestV1.entries")
    entry_payloads = typing.cast(list[object], entries_value)
    if any(type(entry) is not dict for entry in entry_payloads):
        _fail("invalid_field_type", "CandidateCapsuleManifestV1.entries")
    for entry in typing.cast(list[dict[str, object]], entry_payloads):
        entry_mapping = _closed_mapping(
            entry,
            CapsuleEntryV1._FIELDS,
            "CandidateCapsuleManifestV1.entries",
        )
        _prevalidate_capsule_entry_mapping_types(entry_mapping)


class CandidateCapsuleManifestV1(_TopLevelValue):
    _FIELDS = (
        "schema_id",
        "canonicalization_profile",
        "digest_domain",
        "candidate_ref",
        "capsule_manifest_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "command_ref",
        "command_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "authorized_path_scope_digest",
        "entries",
        "portable_capsule_digest",
    )
    __slots__ = tuple(f"_{field}" for field in _FIELDS)
    _DOMAIN = _CAPSULE_MANIFEST_DOMAIN
    _IDENTITY_EXCLUSIONS = ("portable_capsule_digest",)

    schema_id = _read_only_property("_schema_id")
    canonicalization_profile = _read_only_property("_canonicalization_profile")
    digest_domain = _read_only_property("_digest_domain")
    candidate_ref = _read_only_property("_candidate_ref")
    capsule_manifest_ref = _read_only_property("_capsule_manifest_ref")
    program_ref = _read_only_property("_program_ref")
    program_version_ref = _read_only_property("_program_version_ref")
    accepted_intent_revision_ref = _read_only_property("_accepted_intent_revision_ref")
    work_item_ref = _read_only_property("_work_item_ref")
    work_item_revision_ref = _read_only_property("_work_item_revision_ref")
    semantic_attempt_ref = _read_only_property("_semantic_attempt_ref")
    effect_intent_ref = _read_only_property("_effect_intent_ref")
    command_ref = _read_only_property("_command_ref")
    command_digest = _read_only_property("_command_digest")
    attempt_fence_ref = _read_only_property("_attempt_fence_ref")
    attempt_fence_digest = _read_only_property("_attempt_fence_digest")
    effect_fence_ref = _read_only_property("_effect_fence_ref")
    effect_fence_digest = _read_only_property("_effect_fence_digest")
    repository_ref = _read_only_property("_repository_ref")
    base_git_object_format = _read_only_property("_base_git_object_format")
    base_git_oid = _read_only_property("_base_git_oid")
    authorized_path_scope_digest = _read_only_property("_authorized_path_scope_digest")
    entries = _read_only_property("_entries")
    portable_capsule_digest = _read_only_property("_portable_capsule_digest")

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")

    @classmethod
    def create(
        cls,
        *,
        before_blobs: dict[str, bytes],
        after_blobs: dict[str, bytes],
        modes: dict[str, str],
        author_command: WorkerCommandV1,
        attempt_fence: AttemptFenceV1,
        author_effect_fence: EffectFenceV1,
        capsule_manifest_ref: str,
    ) -> CandidateCapsuleManifestV1:
        _require_factory_exact_value(
            before_blobs, dict, "CandidateCapsuleManifestV1.before_blobs"
        )
        _require_factory_exact_value(
            after_blobs, dict, "CandidateCapsuleManifestV1.after_blobs"
        )
        _require_factory_exact_value(
            modes, dict, "CandidateCapsuleManifestV1.modes"
        )
        _require_factory_exact_value(
            author_command,
            WorkerCommandV1,
            "CandidateCapsuleManifestV1.author_command",
        )
        _require_factory_exact_value(
            attempt_fence,
            AttemptFenceV1,
            "CandidateCapsuleManifestV1.attempt_fence",
        )
        _require_factory_exact_value(
            author_effect_fence,
            EffectFenceV1,
            "CandidateCapsuleManifestV1.author_effect_fence",
        )
        _require_exact_string(
            capsule_manifest_ref,
            "CandidateCapsuleManifestV1.capsule_manifest_ref",
        )
        _require_blob_map_types(
            before_blobs, "CandidateCapsuleManifestV1.before_blobs"
        )
        _require_blob_map_types(
            after_blobs, "CandidateCapsuleManifestV1.after_blobs"
        )
        _require_mode_map_types(modes, "CandidateCapsuleManifestV1.modes")
        before = _require_blob_map(before_blobs, "CandidateCapsuleManifestV1.before_blobs")
        after = _require_blob_map(after_blobs, "CandidateCapsuleManifestV1.after_blobs")
        mode_map = _require_mode_map(modes, "CandidateCapsuleManifestV1.modes")
        _validate_author_pair_without_work_spec(
            attempt_fence=attempt_fence,
            author_command=author_command,
            author_effect_fence=author_effect_fence,
        )
        entries = [
            CapsuleEntryV1.create(
                path=path,
                mode=mode_map[path],
                before_blob=before[path],
                after_blob=after[path],
            ).to_mapping()
            for path in _AUTHORIZED_PATHS
        ]
        identity: dict[str, object] = {
            "schema_id": _CAPSULE_MANIFEST_SCHEMA,
            "canonicalization_profile": _CAPSULE_CANONICALIZATION_PROFILE,
            "digest_domain": _CAPSULE_MANIFEST_DOMAIN,
            "candidate_ref": author_command.candidate_ref,
            "capsule_manifest_ref": capsule_manifest_ref,
            "program_ref": author_command.program_ref,
            "program_version_ref": author_command.program_version_ref,
            "accepted_intent_revision_ref": author_command.accepted_intent_revision_ref,
            "work_item_ref": author_command.work_item_ref,
            "work_item_revision_ref": author_command.work_item_revision_ref,
            "semantic_attempt_ref": author_command.semantic_attempt_ref,
            "effect_intent_ref": author_command.effect_intent_ref,
            "command_ref": author_command.command_ref,
            "command_digest": author_command.command_digest,
            "attempt_fence_ref": attempt_fence.attempt_fence_ref,
            "attempt_fence_digest": attempt_fence.attempt_fence_digest,
            "effect_fence_ref": author_effect_fence.effect_fence_ref,
            "effect_fence_digest": author_effect_fence.effect_fence_digest,
            "repository_ref": author_command.repository_ref,
            "base_git_object_format": author_command.base_git_object_format,
            "base_git_oid": author_command.base_git_oid,
            "authorized_path_scope_digest": _authorized_path_scope_digest(
                author_command.path_ceiling
            ),
            "entries": entries,
        }
        identity["portable_capsule_digest"] = _domain_digest(
            cls._DOMAIN,
            _canonical_bytes(identity, "CandidateCapsuleManifestV1.canonical_identity"),
        )
        result = cls.from_mapping(identity)
        validate_capsule_manifest_relation(
            capsule_manifest=result,
            author_command=author_command,
            attempt_fence=attempt_fence,
            author_effect_fence=author_effect_fence,
            before_blobs=before_blobs,
            after_blobs=after_blobs,
        )
        return result

    @classmethod
    def from_mapping(cls, payload: object) -> CandidateCapsuleManifestV1:
        mapping = _closed_mapping(
            payload, cls._FIELDS, "CandidateCapsuleManifestV1.fields"
        )
        _prevalidate_capsule_manifest_mapping_types(mapping)
        entries_value = mapping["entries"]
        entry_payloads = typing.cast(list[object], entries_value)
        if not entry_payloads:
            _fail("invalid_field_value", "CandidateCapsuleManifestV1.entries")
        entries = tuple(CapsuleEntryV1.from_mapping(entry) for entry in entry_payloads)
        if tuple(entry.path for entry in entries) != _AUTHORIZED_PATHS:
            _fail("invalid_field_value", "CandidateCapsuleManifestV1.entries")
        ref_fields = (
            "candidate_ref",
            "capsule_manifest_ref",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "work_item_ref",
            "work_item_revision_ref",
            "semantic_attempt_ref",
            "effect_intent_ref",
            "command_ref",
            "attempt_fence_ref",
            "effect_fence_ref",
            "repository_ref",
        )
        refs = {
            field: _require_safe_ref(
                mapping[field], f"CandidateCapsuleManifestV1.{field}"
            )
            for field in ref_fields
        }
        digest_fields = (
            "command_digest",
            "attempt_fence_digest",
            "effect_fence_digest",
            "authorized_path_scope_digest",
            "portable_capsule_digest",
        )
        digests = {
            field: _require_digest(
                mapping[field], f"CandidateCapsuleManifestV1.{field}"
            )
            for field in digest_fields
        }
        values = (
            _require_constant(
                mapping["schema_id"],
                _CAPSULE_MANIFEST_SCHEMA,
                "CandidateCapsuleManifestV1.schema_id",
            ),
            _require_constant(
                mapping["canonicalization_profile"],
                _CAPSULE_CANONICALIZATION_PROFILE,
                "CandidateCapsuleManifestV1.canonicalization_profile",
            ),
            _require_constant(
                mapping["digest_domain"],
                _CAPSULE_MANIFEST_DOMAIN,
                "CandidateCapsuleManifestV1.digest_domain",
            ),
            refs["candidate_ref"],
            refs["capsule_manifest_ref"],
            refs["program_ref"],
            refs["program_version_ref"],
            refs["accepted_intent_revision_ref"],
            refs["work_item_ref"],
            refs["work_item_revision_ref"],
            refs["semantic_attempt_ref"],
            refs["effect_intent_ref"],
            refs["command_ref"],
            digests["command_digest"],
            refs["attempt_fence_ref"],
            digests["attempt_fence_digest"],
            refs["effect_fence_ref"],
            digests["effect_fence_digest"],
            refs["repository_ref"],
            _require_constant(
                mapping["base_git_object_format"],
                "sha1",
                "CandidateCapsuleManifestV1.base_git_object_format",
            ),
            _require_base_oid(
                mapping["base_git_oid"], "CandidateCapsuleManifestV1.base_git_oid"
            ),
            digests["authorized_path_scope_digest"],
            entries,
            digests["portable_capsule_digest"],
        )
        result = typing.cast(
            CandidateCapsuleManifestV1, _construct(cls, cls._FIELDS, values)
        )
        if result.portable_capsule_digest != result.computed_digest():
            _fail(
                "digest_mismatch", "CandidateCapsuleManifestV1.portable_capsule_digest"
            )
        return result

    def to_mapping(self) -> dict[str, object]:
        return self._to_mapping()


class _WorkerExecutionReconstructionFailure(Exception):
    """Private control-flow sentinel for exact owner reconstruction."""

    __slots__ = ()


class _WorkerExecutionReconstructionBudget:
    """Occurrence-work meter for one C2A owner reconstruction."""

    __slots__ = ("remaining",)

    def __init__(self, limit: int) -> None:
        if type(limit) is not int or limit < 0:
            raise _WorkerExecutionReconstructionFailure
        self.remaining = limit

    def consume(self, amount: int = 1) -> None:
        if (
            type(amount) is not int
            or amount < 0
            or amount > self.remaining
        ):
            raise _WorkerExecutionReconstructionFailure
        self.remaining -= amount


_EXACT_WORKER_EXECUTION_RECONSTRUCTION_GRAPHS = (
    (CeilingsV1, 16),
    (CapsuleEntryV1, 8),
    (WorkSpecV1, 86),
    (AttemptFenceV1, 46),
    (EffectFenceV1, 51),
    (WorkerCommandV1, 58),
    (DeliveryEnvelopeV1, 16),
    (CandidateCapsuleManifestV1, 49),
)


def _exact_worker_execution_reconstruction_work(
    expected: type[object],
) -> int:
    for candidate, graph_work in _EXACT_WORKER_EXECUTION_RECONSTRUCTION_GRAPHS:
        if expected is candidate:
            return graph_work * 2
    _fail("relation_mismatch", "_exact_worker_execution_reconstruction_work")


def _worker_execution_tuple_field_limit(
    owner: type[object], field: str,
) -> int | None:
    if owner is WorkSpecV1:
        return {
            "authorized_paths": 3,
            "requirements": 32,
            "exclusions": 32,
        }.get(field)
    if owner is AttemptFenceV1:
        return {"path_ceiling": 3, "allowed_effect_classes": 5}.get(field)
    if owner is EffectFenceV1 or owner is WorkerCommandV1:
        return 3 if field == "path_ceiling" else None
    if owner is CandidateCapsuleManifestV1:
        return 3 if field == "entries" else None
    return None


def _worker_execution_nested_owner(
    owner: type[object], field: str,
) -> type[_ImmutableValue] | None:
    if owner is AttemptFenceV1 and field == "aggregate_ceilings":
        return CeilingsV1
    if (
        (owner is EffectFenceV1 or owner is WorkerCommandV1)
        and field == "effect_ceilings"
    ):
        return CeilingsV1
    return None


def _raw_worker_execution_projection(
    value: object,
    expected: type[_ImmutableValue],
    budget: _WorkerExecutionReconstructionBudget,
) -> tuple[dict[str, object], int]:
    """Snapshot one exact owner graph without invoking supplied behavior."""

    starting = budget.remaining
    active: set[int] = set()
    projection: dict[str, object] = {}
    events: list[tuple[object, ...]] = []

    budget.consume()
    if type(value) is not expected:
        raise _WorkerExecutionReconstructionFailure
    active.add(id(value))
    events.append(("leave", value))
    for field in reversed(expected._FIELDS):
        events.append(("field", value, expected, field, projection))

    while events:
        event = events.pop()
        kind = typing.cast(str, event[0])
        if kind == "leave":
            active.discard(id(event[1]))
            continue

        if kind == "field":
            owner_value = event[1]
            owner_type = typing.cast(type[_ImmutableValue], event[2])
            field = typing.cast(str, event[3])
            target = typing.cast(dict[str, object], event[4])
            budget.consume()
            try:
                member = object.__getattribute__(owner_value, f"_{field}")
            except (KeyboardInterrupt, SystemExit, GeneratorExit):
                raise
            except Exception as error:
                raise _WorkerExecutionReconstructionFailure from error

            tuple_limit = _worker_execution_tuple_field_limit(owner_type, field)
            nested_owner = _worker_execution_nested_owner(owner_type, field)
            if tuple_limit is not None:
                if type(member) is not tuple:
                    raise _WorkerExecutionReconstructionFailure
                sequence = typing.cast(tuple[object, ...], member)
                if len(sequence) > tuple_limit:
                    raise _WorkerExecutionReconstructionFailure
                identity = id(sequence)
                if identity in active:
                    raise _WorkerExecutionReconstructionFailure
                result: list[object] = []
                target[field] = result
                active.add(identity)
                events.append(("leave", sequence))
                item_owner = (
                    CapsuleEntryV1
                    if owner_type is CandidateCapsuleManifestV1
                    and field == "entries"
                    else None
                )
                if sequence:
                    events.append(
                        ("item", sequence, item_owner, result, 0)
                    )
                continue
            if nested_owner is not None:
                if type(member) is not nested_owner:
                    raise _WorkerExecutionReconstructionFailure
                identity = id(member)
                if identity in active:
                    raise _WorkerExecutionReconstructionFailure
                nested_projection: dict[str, object] = {}
                target[field] = nested_projection
                active.add(identity)
                events.append(("leave", member))
                for nested_field in reversed(nested_owner._FIELDS):
                    events.append(
                        (
                            "field",
                            member,
                            nested_owner,
                            nested_field,
                            nested_projection,
                        )
                    )
                continue
            if type(member) not in (str, int, type(None)):
                raise _WorkerExecutionReconstructionFailure
            target[field] = member
            continue

        if kind == "item":
            sequence = typing.cast(tuple[object, ...], event[1])
            item_owner = typing.cast(type[_ImmutableValue] | None, event[2])
            target_list = typing.cast(list[object], event[3])
            index = typing.cast(int, event[4])
            budget.consume()
            member = sequence[index]
            if index + 1 < len(sequence):
                events.append(
                    ("item", sequence, item_owner, target_list, index + 1)
                )
            if item_owner is None:
                if type(member) is not str:
                    raise _WorkerExecutionReconstructionFailure
                target_list.insert(index, member)
                continue
            if type(member) is not item_owner:
                raise _WorkerExecutionReconstructionFailure
            identity = id(member)
            if identity in active:
                raise _WorkerExecutionReconstructionFailure
            nested_projection = {}
            target_list.insert(index, nested_projection)
            active.add(identity)
            events.append(("leave", member))
            for nested_field in reversed(item_owner._FIELDS):
                events.append(
                    (
                        "field",
                        member,
                        item_owner,
                        nested_field,
                        nested_projection,
                    )
                )
            continue

        raise _WorkerExecutionReconstructionFailure

    return projection, starting - budget.remaining


def _reconstruct_exact_worker_execution_value(
    value: object,
    expected: type[object],
    budget: _WorkerExecutionReconstructionBudget | None = None,
) -> tuple[_ImmutableValue, dict[str, object]]:
    """Return a fresh exact C2A value and its validated plain projection."""

    failed = False
    reconstructed: object = None
    projection: dict[str, object] = {}
    try:
        maximum = _exact_worker_execution_reconstruction_work(expected)
        if budget is None:
            exact_budget = _WorkerExecutionReconstructionBudget(maximum)
        elif type(budget) is _WorkerExecutionReconstructionBudget:
            exact_budget = budget
        else:
            raise _WorkerExecutionReconstructionFailure
        exact_expected = typing.cast(type[_ImmutableValue], expected)
        projection, raw_work = _raw_worker_execution_projection(
            value, exact_expected, exact_budget
        )
        exact_budget.consume(raw_work)
        reconstructed = exact_expected.from_mapping(projection)
        if type(reconstructed) is not exact_expected:
            raise _WorkerExecutionReconstructionFailure
    except (KeyboardInterrupt, SystemExit, GeneratorExit):
        raise
    except Exception:
        failed = True
    if failed:
        _fail("relation_mismatch", "_reconstruct_exact_worker_execution_value")
    return typing.cast(_ImmutableValue, reconstructed), projection


def _prevalidate_worker_observation_mapping_types(
    mapping: dict[str, object],
) -> None:
    for field in (
        "schema_id",
        "observation_ref",
        "source_kind",
        "source_ref",
        "source_invocation_ref",
        "delivery_attempt_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "command_ref",
        "command_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
        "observation_kind",
        "outcome",
        "reason_code",
        "observed_at",
        "observation_digest",
    ):
        _require_exact_string(mapping[field], f"WorkerObservationV1.{field}")
    _require_exact_string_list_type(
        mapping["evidence_refs"], "WorkerObservationV1.evidence_refs"
    )
    for field in (
        "candidate_ref",
        "capsule_manifest_ref",
        "portable_capsule_digest",
    ):
        if field in mapping:
            _require_exact_string(mapping[field], f"WorkerObservationV1.{field}")
    if "process_exit_code" in mapping:
        _require_exact_integer_type(
            mapping["process_exit_code"],
            "WorkerObservationV1.process_exit_code",
        )


class WorkerObservationV1(_TopLevelValue):
    _REQUIRED_FIELDS = (
        "schema_id",
        "observation_ref",
        "source_kind",
        "source_ref",
        "source_invocation_ref",
        "delivery_attempt_ref",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "command_ref",
        "command_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
        "observation_kind",
        "outcome",
        "reason_code",
        "evidence_refs",
        "observed_at",
        "observation_digest",
    )
    _OPTIONAL_FIELDS = (
        "candidate_ref",
        "capsule_manifest_ref",
        "portable_capsule_digest",
        "process_exit_code",
    )
    _FIELDS = _REQUIRED_FIELDS[:-1] + _OPTIONAL_FIELDS + ("observation_digest",)
    __slots__ = tuple(f"_{field}" for field in _FIELDS)
    _DOMAIN = _WORKER_OBSERVATION_DOMAIN
    _IDENTITY_EXCLUSIONS = ("observation_digest",)

    schema_id = _read_only_property("_schema_id")
    observation_ref = _read_only_property("_observation_ref")
    source_kind = _read_only_property("_source_kind")
    source_ref = _read_only_property("_source_ref")
    source_invocation_ref = _read_only_property("_source_invocation_ref")
    delivery_attempt_ref = _read_only_property("_delivery_attempt_ref")
    program_ref = _read_only_property("_program_ref")
    program_version_ref = _read_only_property("_program_version_ref")
    accepted_intent_revision_ref = _read_only_property("_accepted_intent_revision_ref")
    work_item_ref = _read_only_property("_work_item_ref")
    work_item_revision_ref = _read_only_property("_work_item_revision_ref")
    semantic_attempt_ref = _read_only_property("_semantic_attempt_ref")
    effect_intent_ref = _read_only_property("_effect_intent_ref")
    command_ref = _read_only_property("_command_ref")
    command_digest = _read_only_property("_command_digest")
    attempt_fence_ref = _read_only_property("_attempt_fence_ref")
    attempt_fence_digest = _read_only_property("_attempt_fence_digest")
    effect_fence_ref = _read_only_property("_effect_fence_ref")
    effect_fence_digest = _read_only_property("_effect_fence_digest")
    observation_kind = _read_only_property("_observation_kind")
    outcome = _read_only_property("_outcome")
    reason_code = _read_only_property("_reason_code")
    evidence_refs = _read_only_property("_evidence_refs")
    observed_at = _read_only_property("_observed_at")
    candidate_ref = _read_only_property("_candidate_ref")
    capsule_manifest_ref = _read_only_property("_capsule_manifest_ref")
    portable_capsule_digest = _read_only_property("_portable_capsule_digest")
    process_exit_code = _read_only_property("_process_exit_code")
    observation_digest = _read_only_property("_observation_digest")

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")

    @classmethod
    def create(
        cls,
        *,
        observation_ref: str,
        source_kind: str,
        source_ref: str,
        source_invocation_ref: str,
        observation_kind: str,
        outcome: str,
        reason_code: str,
        evidence_refs: list[str],
        observed_at: str,
        delivery: DeliveryEnvelopeV1,
        author_command: WorkerCommandV1,
        attempt_fence: AttemptFenceV1,
        author_effect_fence: EffectFenceV1,
        effect_fence: EffectFenceV1,
        capsule_manifest: object = _MISSING,
        before_blobs: object = _MISSING,
        after_blobs: object = _MISSING,
        process_exit_code: object = _MISSING,
        cancellation_target: object = _MISSING,
    ) -> WorkerObservationV1:
        for field_path, value in (
            ("WorkerObservationV1.observation_ref", observation_ref),
            ("WorkerObservationV1.source_kind", source_kind),
            ("WorkerObservationV1.source_ref", source_ref),
            (
                "WorkerObservationV1.source_invocation_ref",
                source_invocation_ref,
            ),
            ("WorkerObservationV1.observation_kind", observation_kind),
            ("WorkerObservationV1.outcome", outcome),
            ("WorkerObservationV1.reason_code", reason_code),
            ("WorkerObservationV1.observed_at", observed_at),
        ):
            _require_exact_string(value, field_path)
        _require_factory_exact_value(
            evidence_refs, list, "WorkerObservationV1.evidence_refs"
        )
        _require_factory_exact_value(
            delivery, DeliveryEnvelopeV1, "WorkerObservationV1.delivery"
        )
        _require_factory_exact_value(
            author_command,
            WorkerCommandV1,
            "WorkerObservationV1.author_command",
        )
        _require_factory_exact_value(
            attempt_fence, AttemptFenceV1, "WorkerObservationV1.attempt_fence"
        )
        _require_factory_exact_value(
            author_effect_fence,
            EffectFenceV1,
            "WorkerObservationV1.author_effect_fence",
        )
        _require_factory_exact_value(
            effect_fence, EffectFenceV1, "WorkerObservationV1.effect_fence"
        )
        _require_optional_factory_exact_value(
            capsule_manifest,
            CandidateCapsuleManifestV1,
            "WorkerObservationV1.capsule_manifest",
        )
        _require_optional_factory_exact_value(
            before_blobs, dict, "WorkerObservationV1.before_blobs"
        )
        _require_optional_factory_exact_value(
            after_blobs, dict, "WorkerObservationV1.after_blobs"
        )
        if process_exit_code is not _MISSING:
            _require_exact_integer_type(
                process_exit_code, "WorkerObservationV1.process_exit_code"
            )
        _require_optional_factory_exact_value(
            cancellation_target,
            EffectFenceV1,
            "WorkerObservationV1.cancellation_target",
        )
        _require_exact_string_list_type(
            evidence_refs, "WorkerObservationV1.evidence_refs"
        )
        _require_optional_blob_map_types(
            before_blobs, "WorkerObservationV1.before_blobs"
        )
        _require_optional_blob_map_types(
            after_blobs, "WorkerObservationV1.after_blobs"
        )
        conditional = _observation_conditional(observation_kind)
        graph_manifest_required = _effect_graph_requires_capsule_manifest(
            effect_fence=effect_fence,
            cancellation_target=cancellation_target,
        )
        identity: dict[str, object] = {
            "schema_id": _WORKER_OBSERVATION_SCHEMA,
            "observation_ref": observation_ref,
            "source_kind": source_kind,
            "source_ref": source_ref,
            "source_invocation_ref": source_invocation_ref,
            "delivery_attempt_ref": delivery.delivery_attempt_ref,
            "program_ref": author_command.program_ref,
            "program_version_ref": author_command.program_version_ref,
            "accepted_intent_revision_ref": author_command.accepted_intent_revision_ref,
            "work_item_ref": author_command.work_item_ref,
            "work_item_revision_ref": author_command.work_item_revision_ref,
            "semantic_attempt_ref": author_command.semantic_attempt_ref,
            "effect_intent_ref": effect_fence.effect_intent_ref,
            "command_ref": author_command.command_ref,
            "command_digest": author_command.command_digest,
            "attempt_fence_ref": attempt_fence.attempt_fence_ref,
            "attempt_fence_digest": attempt_fence.attempt_fence_digest,
            "effect_fence_ref": effect_fence.effect_fence_ref,
            "effect_fence_digest": effect_fence.effect_fence_digest,
            "observation_kind": observation_kind,
            "outcome": outcome,
            "reason_code": reason_code,
            "evidence_refs": evidence_refs,
            "observed_at": observed_at,
        }
        if conditional == "candidate":
            if (
                capsule_manifest is not _MISSING
                or before_blobs is not _MISSING
                or after_blobs is not _MISSING
                or process_exit_code is not _MISSING
            ):
                _fail("invalid_field_value", "WorkerObservationV1.conditional_fields")
            identity["candidate_ref"] = author_command.candidate_ref
        elif conditional == "capsule":
            if type(capsule_manifest) is not CandidateCapsuleManifestV1:
                _fail("invalid_field_type", "WorkerObservationV1.capsule_manifest")
            if process_exit_code is not _MISSING:
                _fail("invalid_field_value", "WorkerObservationV1.conditional_fields")
            manifest = typing.cast(CandidateCapsuleManifestV1, capsule_manifest)
            identity.update(
                candidate_ref=manifest.candidate_ref,
                capsule_manifest_ref=manifest.capsule_manifest_ref,
                portable_capsule_digest=manifest.portable_capsule_digest,
            )
        elif conditional == "exit":
            if (
                before_blobs is not _MISSING
                or after_blobs is not _MISSING
                or process_exit_code is _MISSING
            ):
                _fail("invalid_field_value", "WorkerObservationV1.conditional_fields")
            if graph_manifest_required:
                if capsule_manifest is _MISSING:
                    _fail("invalid_field_type", "WorkerObservationV1.capsule_manifest")
            elif capsule_manifest is not _MISSING:
                _fail("invalid_field_value", "WorkerObservationV1.conditional_fields")
            identity["process_exit_code"] = process_exit_code
        else:
            if (
                before_blobs is not _MISSING
                or after_blobs is not _MISSING
                or process_exit_code is not _MISSING
            ):
                _fail("invalid_field_value", "WorkerObservationV1.conditional_fields")
            if graph_manifest_required:
                if capsule_manifest is _MISSING:
                    _fail("invalid_field_type", "WorkerObservationV1.capsule_manifest")
            elif capsule_manifest is not _MISSING:
                _fail("invalid_field_value", "WorkerObservationV1.conditional_fields")
        identity["observation_digest"] = _domain_digest(
            cls._DOMAIN,
            _canonical_bytes(identity, "WorkerObservationV1.canonical_identity"),
        )
        result = cls.from_mapping(identity)
        validate_observation_relation(
            observation=result,
            delivery=delivery,
            author_command=author_command,
            attempt_fence=attempt_fence,
            author_effect_fence=author_effect_fence,
            effect_fence=effect_fence,
            capsule_manifest=capsule_manifest,
            before_blobs=before_blobs,
            after_blobs=after_blobs,
            cancellation_target=cancellation_target,
        )
        return result

    @classmethod
    def from_mapping(cls, payload: object) -> WorkerObservationV1:
        mapping = _closed_mapping(
            payload,
            cls._FIELDS,
            "WorkerObservationV1.fields",
            required_fields=cls._REQUIRED_FIELDS,
        )
        _prevalidate_worker_observation_mapping_types(mapping)
        kind = _require_exact_string(
            mapping["observation_kind"], "WorkerObservationV1.observation_kind"
        )
        sources, outcomes, conditional = _observation_spec(kind)
        expected_optional = _conditional_field_names(conditional)
        present_optional = tuple(
            field for field in cls._OPTIONAL_FIELDS if field in mapping
        )
        if any(field not in present_optional for field in expected_optional):
            _fail("missing_field", "WorkerObservationV1.conditional_fields")
        if set(present_optional) != set(expected_optional):
            _fail("invalid_field_value", "WorkerObservationV1.conditional_fields")
        source_kind = _require_exact_string(
            mapping["source_kind"], "WorkerObservationV1.source_kind"
        )
        if source_kind not in _SOURCE_KINDS or source_kind not in sources:
            _fail("invalid_field_value", "WorkerObservationV1.source_kind")
        outcome = _require_exact_string(mapping["outcome"], "WorkerObservationV1.outcome")
        if outcome not in outcomes:
            _fail("invalid_field_value", "WorkerObservationV1.outcome")
        common_refs = (
            "observation_ref",
            "source_ref",
            "source_invocation_ref",
            "delivery_attempt_ref",
            "program_ref",
            "program_version_ref",
            "accepted_intent_revision_ref",
            "work_item_ref",
            "work_item_revision_ref",
            "semantic_attempt_ref",
            "effect_intent_ref",
            "command_ref",
            "attempt_fence_ref",
            "effect_fence_ref",
        )
        refs = {
            field: _require_safe_ref(mapping[field], f"WorkerObservationV1.{field}")
            for field in common_refs
        }
        common_digests = (
            "command_digest",
            "attempt_fence_digest",
            "effect_fence_digest",
            "observation_digest",
        )
        digests = {
            field: _require_digest(mapping[field], f"WorkerObservationV1.{field}")
            for field in common_digests
        }
        candidate_ref = (
            _require_safe_ref(mapping["candidate_ref"], "WorkerObservationV1.candidate_ref")
            if "candidate_ref" in mapping
            else _MISSING
        )
        capsule_manifest_ref = (
            _require_safe_ref(
                mapping["capsule_manifest_ref"],
                "WorkerObservationV1.capsule_manifest_ref",
            )
            if "capsule_manifest_ref" in mapping
            else _MISSING
        )
        portable_capsule_digest = (
            _require_digest(
                mapping["portable_capsule_digest"],
                "WorkerObservationV1.portable_capsule_digest",
            )
            if "portable_capsule_digest" in mapping
            else _MISSING
        )
        exit_code = (
            _require_exit_code(mapping["process_exit_code"], "WorkerObservationV1.process_exit_code")
            if "process_exit_code" in mapping
            else _MISSING
        )
        values_by_field: dict[str, object] = {
            "schema_id": _require_constant(
                mapping["schema_id"],
                _WORKER_OBSERVATION_SCHEMA,
                "WorkerObservationV1.schema_id",
            ),
            "observation_ref": refs["observation_ref"],
            "source_kind": source_kind,
            "source_ref": refs["source_ref"],
            "source_invocation_ref": refs["source_invocation_ref"],
            "delivery_attempt_ref": refs["delivery_attempt_ref"],
            "program_ref": refs["program_ref"],
            "program_version_ref": refs["program_version_ref"],
            "accepted_intent_revision_ref": refs["accepted_intent_revision_ref"],
            "work_item_ref": refs["work_item_ref"],
            "work_item_revision_ref": refs["work_item_revision_ref"],
            "semantic_attempt_ref": refs["semantic_attempt_ref"],
            "effect_intent_ref": refs["effect_intent_ref"],
            "command_ref": refs["command_ref"],
            "command_digest": digests["command_digest"],
            "attempt_fence_ref": refs["attempt_fence_ref"],
            "attempt_fence_digest": digests["attempt_fence_digest"],
            "effect_fence_ref": refs["effect_fence_ref"],
            "effect_fence_digest": digests["effect_fence_digest"],
            "observation_kind": kind,
            "outcome": outcome,
            "reason_code": _require_reason_code(
                mapping["reason_code"], kind, "WorkerObservationV1.reason_code"
            ),
            "evidence_refs": _require_evidence_refs(
                mapping["evidence_refs"], "WorkerObservationV1.evidence_refs"
            ),
            "observed_at": _require_timestamp(
                mapping["observed_at"], "WorkerObservationV1.observed_at"
            ),
            "candidate_ref": candidate_ref,
            "capsule_manifest_ref": capsule_manifest_ref,
            "portable_capsule_digest": portable_capsule_digest,
            "process_exit_code": exit_code,
            "observation_digest": digests["observation_digest"],
        }
        result = typing.cast(
            WorkerObservationV1,
            _construct(
                cls,
                cls._FIELDS,
                tuple(values_by_field[field] for field in cls._FIELDS),
            ),
        )
        if result.observation_digest != result.computed_digest():
            _fail("digest_mismatch", "WorkerObservationV1.observation_digest")
        return result

    def to_mapping(self) -> dict[str, object]:
        result = self._to_mapping()
        for field in self._OPTIONAL_FIELDS:
            if result[field] is _MISSING:
                result.pop(field)
        return result

    def identity_mapping(self) -> dict[str, object]:
        result = self.to_mapping()
        result.pop("observation_digest")
        return result


def _require_blob_map(payload: object, field_path: str) -> dict[str, bytes]:
    mapping = _closed_mapping(payload, _AUTHORIZED_PATHS, field_path)
    if any(type(mapping[path]) is not bytes for path in _AUTHORIZED_PATHS):
        _fail("invalid_field_type", field_path)
    return typing.cast(dict[str, bytes], mapping)


def _require_mode_map(payload: object, field_path: str) -> dict[str, str]:
    mapping = _closed_mapping(payload, _AUTHORIZED_PATHS, field_path)
    modes: dict[str, str] = {}
    for path in _AUTHORIZED_PATHS:
        mode = _require_exact_string(mapping[path], field_path)
        if mode not in ("100644", "100755"):
            _fail("invalid_field_value", field_path)
        modes[path] = mode
    return modes


def _observation_spec(kind: str) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    if kind == "delivery_acknowledged":
        return ("direct_local_adapter", "es_adapter"), ("acknowledged",), "none"
    if kind == "delivery_rejected":
        return ("direct_local_adapter", "es_adapter"), ("rejected",), "none"
    if kind == "worker_started":
        return ("worker",), ("started",), "none"
    if kind == "worker_completed":
        return ("worker",), ("completed",), "none"
    if kind == "candidate_captured":
        return ("worker",), ("captured",), "candidate"
    if kind == "capsule_sealed":
        return ("capsule_builder",), ("sealed",), "capsule"
    if kind == "capsule_seal_failed":
        return ("capsule_builder",), ("failed",), "candidate"
    if kind == "validation_completed":
        return ("validator",), ("passed", "failed", "inconclusive", "not_run"), "capsule"
    if kind == "independent_review_completed":
        return ("independent_reviewer",), ("passed", "failed", "inconclusive"), "capsule"
    if kind == "cancellation_acknowledged":
        return ("direct_local_adapter", "es_adapter"), ("acknowledged",), "none"
    if kind == "cancellation_rejected":
        return ("direct_local_adapter", "es_adapter"), ("rejected",), "none"
    if kind == "process_exited":
        return ("direct_local_adapter", "es_adapter"), ("exited",), "exit"
    if kind == "deadline_elapsed":
        return ("direct_local_adapter", "es_adapter"), ("elapsed",), "none"
    if kind == "delivery_outcome_unknown":
        return ("direct_local_adapter", "es_adapter"), ("unknown",), "none"
    if kind == "workspace_teardown_succeeded":
        return ("workspace_custodian",), ("succeeded",), "capsule"
    if kind == "workspace_teardown_failed":
        return ("workspace_custodian",), ("failed",), "capsule"
    if kind == "capsule_retrieval_succeeded":
        return ("capsule_store",), ("succeeded",), "capsule"
    if kind == "capsule_retrieval_failed":
        return ("capsule_store",), ("failed",), "capsule"
    _fail("invalid_field_value", "WorkerObservationV1.observation_kind")


def _observation_conditional(kind: object) -> str:
    exact_kind = _require_exact_string(kind, "WorkerObservationV1.observation_kind")
    return _observation_spec(exact_kind)[2]


def _conditional_field_names(conditional: str) -> tuple[str, ...]:
    if conditional == "candidate":
        return ("candidate_ref",)
    if conditional == "capsule":
        return ("candidate_ref", "capsule_manifest_ref", "portable_capsule_digest")
    if conditional == "exit":
        return ("process_exit_code",)
    return ()


def _effect_classes_for_observation(kind: str) -> tuple[str, ...]:
    if kind in (
        "delivery_acknowledged",
        "delivery_rejected",
        "process_exited",
        "deadline_elapsed",
        "delivery_outcome_unknown",
    ):
        return _DELIVERABLE_EFFECT_CLASSES
    if kind in (
        "worker_started",
        "worker_completed",
        "candidate_captured",
        "capsule_sealed",
        "capsule_seal_failed",
    ):
        return ("author_candidate",)
    if kind == "validation_completed":
        return ("validate_candidate",)
    if kind == "independent_review_completed":
        return ("review_candidate",)
    if kind in ("cancellation_acknowledged", "cancellation_rejected"):
        return ("cancel_effect",)
    if kind in ("workspace_teardown_succeeded", "workspace_teardown_failed"):
        return ("author_candidate", "cancel_effect")
    if kind in ("capsule_retrieval_succeeded", "capsule_retrieval_failed"):
        return ("validate_candidate", "review_candidate")
    _fail("invalid_field_value", "WorkerObservationV1.observation_kind")


def _effect_graph_requires_capsule_manifest(
    *,
    effect_fence: EffectFenceV1,
    cancellation_target: object,
) -> bool:
    if effect_fence.effect_class in (
        "validate_candidate",
        "review_candidate",
        "local_git_commit",
    ):
        return True
    if (
        effect_fence.effect_class == "cancel_effect"
        and type(cancellation_target) is EffectFenceV1
    ):
        target = typing.cast(EffectFenceV1, cancellation_target)
        return target.effect_class in (
            "validate_candidate",
            "review_candidate",
            "local_git_commit",
        )
    return False


def _require_exact_value(value: object, value_type: type[typing.Any], field_path: str) -> None:
    if type(value) is not value_type:
        _fail("relation_mismatch", field_path)


def _ceilings_at_most(child: CeilingsV1, parent: CeilingsV1) -> bool:
    return (
        child.max_pull_requests <= parent.max_pull_requests
        and all(
            getattr(child, field) <= getattr(parent, field)
            for field in _CEILING_FIELDS
            if field != "max_pull_requests"
        )
    )


def _non_git_effect_ceilings(ceilings: CeilingsV1) -> bool:
    return (
        ceilings.max_deployments == 0
        and ceilings.max_local_commits == 0
        and ceilings.max_merges == 0
        and ceilings.max_pull_requests == 0
        and ceilings.max_pushes == 0
    )


def _local_git_effect_ceilings(ceilings: CeilingsV1) -> bool:
    return (
        ceilings.max_local_commits == 1
        and ceilings.max_pushes == 0
        and ceilings.max_pull_requests == 0
        and ceilings.max_merges == 0
        and ceilings.max_deployments == 0
    )


def _validate_work_spec_attempt_relation(
    *, work_spec: WorkSpecV1, attempt_fence: AttemptFenceV1
) -> None:
    _require_exact_value(work_spec, WorkSpecV1, "validate_authoring_relation.work_spec")
    _require_exact_value(
        attempt_fence, AttemptFenceV1, "validate_authoring_relation.attempt_fence"
    )
    for field in (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
    ):
        _relation(
            getattr(work_spec, field) == getattr(attempt_fence, field),
            f"validate_authoring_relation.{field}",
        )
    _relation(
        work_spec.authorized_paths == attempt_fence.path_ceiling,
        "validate_authoring_relation.path_ceiling",
    )


def _validate_author_pair_without_work_spec(
    *,
    attempt_fence: AttemptFenceV1,
    author_command: WorkerCommandV1,
    author_effect_fence: EffectFenceV1,
) -> None:
    _require_exact_value(
        attempt_fence, AttemptFenceV1, "validate_authoring_relation.attempt_fence"
    )
    _require_exact_value(
        author_command, WorkerCommandV1, "validate_authoring_relation.author_command"
    )
    _require_exact_value(
        author_effect_fence,
        EffectFenceV1,
        "validate_authoring_relation.author_effect_fence",
    )
    _relation(
        author_command.command_digest == author_command.computed_digest(),
        "validate_authoring_relation.command_digest",
    )
    _relation(
        author_effect_fence.effect_fence_digest == author_effect_fence.computed_digest(),
        "validate_authoring_relation.effect_fence_digest",
    )
    _relation(
        attempt_fence.attempt_fence_digest == attempt_fence.computed_digest(),
        "validate_authoring_relation.attempt_fence_digest",
    )
    for field in (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "attempt_authorization_ref",
        "attempt_authorization_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "global_stop_ref",
        "global_stop_version",
    ):
        _relation(
            getattr(author_command, field) == getattr(attempt_fence, field),
            f"validate_authoring_relation.{field}",
        )
    _relation(
        author_command.standing_grant_ref == attempt_fence.parent_standing_grant_ref,
        "validate_authoring_relation.standing_grant_ref",
    )
    _relation(
        author_command.standing_grant_digest == attempt_fence.parent_standing_grant_digest,
        "validate_authoring_relation.standing_grant_digest",
    )
    _relation(
        author_command.path_ceiling == attempt_fence.path_ceiling,
        "validate_authoring_relation.path_ceiling",
    )
    _relation(
        _ceilings_at_most(author_command.effect_ceilings, attempt_fence.aggregate_ceilings),
        "validate_authoring_relation.effect_ceilings",
    )
    _relation(
        _non_git_effect_ceilings(author_command.effect_ceilings),
        "validate_authoring_relation.git_effect_ceilings",
    )
    _relation(
        attempt_fence.allowed_effect_classes.count("author_candidate") == 1,
        "validate_authoring_relation.allowed_effect_classes",
    )
    for field in (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "effect_class",
        "command_ref",
        "command_digest",
        "candidate_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "path_ceiling",
        "effect_authorization_ref",
        "effect_authorization_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_ceilings",
        "global_stop_ref",
        "global_stop_version",
    ):
        _relation(
            getattr(author_effect_fence, field) == getattr(author_command, field),
            f"validate_authoring_relation.{field}",
        )
    _relation(
        author_effect_fence.parent_standing_grant_ref == author_command.standing_grant_ref,
        "validate_authoring_relation.parent_standing_grant_ref",
    )
    _relation(
        author_effect_fence.parent_standing_grant_digest
        == author_command.standing_grant_digest,
        "validate_authoring_relation.parent_standing_grant_digest",
    )
    _relation(
        author_effect_fence.effect_fence_ref == author_command.effect_fence_ref,
        "validate_authoring_relation.effect_fence_ref",
    )
    _relation(
        author_effect_fence.effect_fence_digest == author_command.effect_fence_digest,
        "validate_authoring_relation.effect_fence_digest",
    )
    _relation(
        author_effect_fence.effect_class == "author_candidate",
        "validate_authoring_relation.effect_class",
    )
    _relation(
        author_effect_fence.portable_capsule_digest is None,
        "validate_authoring_relation.portable_capsule_digest",
    )
    _relation(
        (
            author_effect_fence.cancellation_target_effect_intent_ref,
            author_effect_fence.cancellation_target_effect_fence_ref,
            author_effect_fence.cancellation_target_effect_fence_digest,
        )
        == (None, None, None),
        "validate_authoring_relation.cancellation_target",
    )
    _relation(
        author_effect_fence.expires_at <= attempt_fence.expires_at,
        "validate_authoring_relation.expires_at",
    )


def create_author_command_and_effect_fence(
    *,
    work_spec: WorkSpecV1,
    attempt_fence: AttemptFenceV1,
    command_ref: str,
    effect_intent_ref: str,
    effect_fence_ref: str,
    candidate_ref: str,
    effect_authorization_ref: str,
    effect_authorization_digest: str,
    expires_at: str,
    validation_requirement_digest: str,
    review_requirement_digest: str,
    capsule_profile_ref: str,
    redaction_profile_ref: str,
    effect_ceilings: CeilingsV1,
) -> tuple[WorkerCommandV1, EffectFenceV1]:
    _require_factory_exact_value(
        work_spec,
        WorkSpecV1,
        "create_author_command_and_effect_fence.work_spec",
    )
    _require_factory_exact_value(
        attempt_fence,
        AttemptFenceV1,
        "create_author_command_and_effect_fence.attempt_fence",
    )
    _require_factory_exact_value(
        effect_ceilings,
        CeilingsV1,
        "create_author_command_and_effect_fence.effect_ceilings",
    )
    for field_path, value in (
        ("create_author_command_and_effect_fence.command_ref", command_ref),
        (
            "create_author_command_and_effect_fence.effect_intent_ref",
            effect_intent_ref,
        ),
        (
            "create_author_command_and_effect_fence.effect_fence_ref",
            effect_fence_ref,
        ),
        (
            "create_author_command_and_effect_fence.candidate_ref",
            candidate_ref,
        ),
        (
            "create_author_command_and_effect_fence.effect_authorization_ref",
            effect_authorization_ref,
        ),
        (
            "create_author_command_and_effect_fence.effect_authorization_digest",
            effect_authorization_digest,
        ),
        ("create_author_command_and_effect_fence.expires_at", expires_at),
        (
            "create_author_command_and_effect_fence.validation_requirement_digest",
            validation_requirement_digest,
        ),
        (
            "create_author_command_and_effect_fence.review_requirement_digest",
            review_requirement_digest,
        ),
        (
            "create_author_command_and_effect_fence.capsule_profile_ref",
            capsule_profile_ref,
        ),
        (
            "create_author_command_and_effect_fence.redaction_profile_ref",
            redaction_profile_ref,
        ),
    ):
        _require_exact_string(value, field_path)
    _validate_work_spec_attempt_relation(
        work_spec=work_spec, attempt_fence=attempt_fence
    )
    _relation(
        _ceilings_at_most(effect_ceilings, attempt_fence.aggregate_ceilings),
        "create_author_command_and_effect_fence.effect_ceilings",
    )
    _relation(
        _non_git_effect_ceilings(effect_ceilings),
        "create_author_command_and_effect_fence.git_effect_ceilings",
    )
    command_identity: dict[str, object] = {
        "schema_id": _WORKER_COMMAND_SCHEMA,
        "command_ref": command_ref,
        "program_ref": work_spec.program_ref,
        "program_version_ref": work_spec.program_version_ref,
        "accepted_intent_revision_ref": work_spec.accepted_intent_revision_ref,
        "work_item_ref": work_spec.work_item_ref,
        "work_item_revision_ref": work_spec.work_item_revision_ref,
        "semantic_attempt_ref": attempt_fence.semantic_attempt_ref,
        "effect_intent_ref": effect_intent_ref,
        "effect_class": "author_candidate",
        "candidate_ref": candidate_ref,
        "repository_ref": work_spec.repository_ref,
        "base_git_object_format": work_spec.base_git_object_format,
        "base_git_oid": work_spec.base_git_oid,
        "path_ceiling": list(work_spec.authorized_paths),
        "work_spec_ref": work_spec.work_spec_ref,
        "work_spec_digest": work_spec.work_spec_digest,
        "standing_grant_ref": attempt_fence.parent_standing_grant_ref,
        "standing_grant_digest": attempt_fence.parent_standing_grant_digest,
        "attempt_authorization_ref": attempt_fence.attempt_authorization_ref,
        "attempt_authorization_digest": attempt_fence.attempt_authorization_digest,
        "effect_authorization_ref": effect_authorization_ref,
        "effect_authorization_digest": effect_authorization_digest,
        "attempt_fence_ref": attempt_fence.attempt_fence_ref,
        "attempt_fence_digest": attempt_fence.attempt_fence_digest,
        "effect_fence_ref": effect_fence_ref,
        "global_stop_ref": attempt_fence.global_stop_ref,
        "global_stop_version": attempt_fence.global_stop_version,
        "validation_requirement_ref": work_spec.validation_requirement_ref,
        "validation_requirement_digest": validation_requirement_digest,
        "review_requirement_ref": work_spec.review_requirement_ref,
        "review_requirement_digest": review_requirement_digest,
        "capsule_schema_id": _CAPSULE_MANIFEST_SCHEMA,
        "capsule_profile_ref": capsule_profile_ref,
        "effect_ceilings": effect_ceilings.to_mapping(),
        "privacy_classification": "private_source_change",
        "redaction_profile_ref": redaction_profile_ref,
    }
    command_digest = _domain_digest(
        _WORKER_COMMAND_DOMAIN,
        _canonical_bytes(
            command_identity, "create_author_command_and_effect_fence.command_identity"
        ),
    )
    effect_identity: dict[str, object] = {
        "schema_id": _EFFECT_FENCE_SCHEMA,
        "effect_fence_ref": effect_fence_ref,
        "parent_standing_grant_ref": attempt_fence.parent_standing_grant_ref,
        "parent_standing_grant_digest": attempt_fence.parent_standing_grant_digest,
        "effect_authorization_ref": effect_authorization_ref,
        "effect_authorization_digest": effect_authorization_digest,
        "attempt_fence_ref": attempt_fence.attempt_fence_ref,
        "attempt_fence_digest": attempt_fence.attempt_fence_digest,
        "program_ref": attempt_fence.program_ref,
        "program_version_ref": attempt_fence.program_version_ref,
        "accepted_intent_revision_ref": attempt_fence.accepted_intent_revision_ref,
        "work_item_ref": attempt_fence.work_item_ref,
        "work_item_revision_ref": attempt_fence.work_item_revision_ref,
        "semantic_attempt_ref": attempt_fence.semantic_attempt_ref,
        "effect_intent_ref": effect_intent_ref,
        "effect_class": "author_candidate",
        "command_ref": command_ref,
        "command_digest": command_digest,
        "candidate_ref": candidate_ref,
        "repository_ref": attempt_fence.repository_ref,
        "base_git_object_format": attempt_fence.base_git_object_format,
        "base_git_oid": attempt_fence.base_git_oid,
        "path_ceiling": list(attempt_fence.path_ceiling),
        "effect_ceilings": effect_ceilings.to_mapping(),
        "expires_at": expires_at,
        "global_stop_ref": attempt_fence.global_stop_ref,
        "global_stop_version": attempt_fence.global_stop_version,
        "portable_capsule_digest": None,
        "cancellation_target_effect_intent_ref": None,
        "cancellation_target_effect_fence_ref": None,
        "cancellation_target_effect_fence_digest": None,
    }
    effect_identity["effect_fence_digest"] = _domain_digest(
        _EFFECT_FENCE_DOMAIN,
        _canonical_bytes(
            effect_identity, "create_author_command_and_effect_fence.effect_identity"
        ),
    )
    author_effect_fence = EffectFenceV1.from_mapping(effect_identity)
    complete_command = dict(command_identity)
    complete_command["effect_fence_digest"] = author_effect_fence.effect_fence_digest
    complete_command["command_digest"] = command_digest
    author_command = WorkerCommandV1.from_mapping(complete_command)
    validate_authoring_relation(
        work_spec=work_spec,
        attempt_fence=attempt_fence,
        author_command=author_command,
        author_effect_fence=author_effect_fence,
    )
    return author_command, author_effect_fence


def create_effect_fence(
    *,
    attempt_fence: AttemptFenceV1,
    author_command: WorkerCommandV1,
    author_effect_fence: EffectFenceV1,
    effect_fence_ref: str,
    effect_intent_ref: str,
    effect_class: str,
    effect_authorization_ref: str,
    effect_authorization_digest: str,
    effect_ceilings: CeilingsV1,
    expires_at: str,
    capsule_manifest: object = _MISSING,
    cancellation_target: object = _MISSING,
) -> EffectFenceV1:
    _require_factory_exact_value(
        attempt_fence, AttemptFenceV1, "create_effect_fence.attempt_fence"
    )
    _require_factory_exact_value(
        author_command, WorkerCommandV1, "create_effect_fence.author_command"
    )
    _require_factory_exact_value(
        author_effect_fence,
        EffectFenceV1,
        "create_effect_fence.author_effect_fence",
    )
    _require_factory_exact_value(
        effect_ceilings, CeilingsV1, "create_effect_fence.effect_ceilings"
    )
    _require_optional_factory_exact_value(
        capsule_manifest,
        CandidateCapsuleManifestV1,
        "create_effect_fence.capsule_manifest",
    )
    _require_optional_factory_exact_value(
        cancellation_target,
        EffectFenceV1,
        "create_effect_fence.cancellation_target",
    )
    for field_path, value in (
        ("create_effect_fence.effect_fence_ref", effect_fence_ref),
        ("create_effect_fence.effect_intent_ref", effect_intent_ref),
        ("create_effect_fence.effect_class", effect_class),
        (
            "create_effect_fence.effect_authorization_ref",
            effect_authorization_ref,
        ),
        (
            "create_effect_fence.effect_authorization_digest",
            effect_authorization_digest,
        ),
        ("create_effect_fence.expires_at", expires_at),
    ):
        _require_exact_string(value, field_path)
    _validate_author_pair_without_work_spec(
        attempt_fence=attempt_fence,
        author_command=author_command,
        author_effect_fence=author_effect_fence,
    )
    exact_effect_class = _require_exact_string(effect_class, "create_effect_fence.effect_class")
    if exact_effect_class == "author_candidate":
        _fail("invalid_field_value", "create_effect_fence.effect_class")
    if exact_effect_class not in _EFFECT_CLASSES:
        _fail("invalid_field_value", "create_effect_fence.effect_class")
    portable_capsule_digest: str | None
    target_intent: str | None
    target_ref: str | None
    target_digest: str | None
    if exact_effect_class in ("validate_candidate", "review_candidate", "local_git_commit"):
        if type(capsule_manifest) is not CandidateCapsuleManifestV1:
            _fail("invalid_field_type", "create_effect_fence.capsule_manifest")
        if cancellation_target is not _MISSING:
            _fail("invalid_field_value", "create_effect_fence.cancellation_target")
        manifest = typing.cast(CandidateCapsuleManifestV1, capsule_manifest)
        _validate_manifest_graph(
            capsule_manifest=manifest,
            author_command=author_command,
            attempt_fence=attempt_fence,
            author_effect_fence=author_effect_fence,
        )
        portable_capsule_digest = manifest.portable_capsule_digest
        target_intent = target_ref = target_digest = None
    elif exact_effect_class == "cancel_effect":
        if type(cancellation_target) is not EffectFenceV1:
            _fail("invalid_field_type", "create_effect_fence.cancellation_target")
        target = typing.cast(EffectFenceV1, cancellation_target)
        if target.effect_class == "author_candidate":
            if capsule_manifest is not _MISSING:
                _fail("invalid_field_value", "create_effect_fence.capsule_manifest")
            portable_capsule_digest = None
        else:
            if type(capsule_manifest) is not CandidateCapsuleManifestV1:
                _fail("invalid_field_type", "create_effect_fence.capsule_manifest")
            manifest = typing.cast(CandidateCapsuleManifestV1, capsule_manifest)
            _validate_manifest_graph(
                capsule_manifest=manifest,
                author_command=author_command,
                attempt_fence=attempt_fence,
                author_effect_fence=author_effect_fence,
            )
            portable_capsule_digest = manifest.portable_capsule_digest
        target_intent = target.effect_intent_ref
        target_ref = target.effect_fence_ref
        target_digest = target.effect_fence_digest
    else:
        _fail("invalid_field_value", "create_effect_fence.effect_class")
    identity: dict[str, object] = {
        "schema_id": _EFFECT_FENCE_SCHEMA,
        "effect_fence_ref": effect_fence_ref,
        "parent_standing_grant_ref": attempt_fence.parent_standing_grant_ref,
        "parent_standing_grant_digest": attempt_fence.parent_standing_grant_digest,
        "effect_authorization_ref": effect_authorization_ref,
        "effect_authorization_digest": effect_authorization_digest,
        "attempt_fence_ref": attempt_fence.attempt_fence_ref,
        "attempt_fence_digest": attempt_fence.attempt_fence_digest,
        "program_ref": attempt_fence.program_ref,
        "program_version_ref": attempt_fence.program_version_ref,
        "accepted_intent_revision_ref": attempt_fence.accepted_intent_revision_ref,
        "work_item_ref": attempt_fence.work_item_ref,
        "work_item_revision_ref": attempt_fence.work_item_revision_ref,
        "semantic_attempt_ref": attempt_fence.semantic_attempt_ref,
        "effect_intent_ref": effect_intent_ref,
        "effect_class": exact_effect_class,
        "command_ref": author_command.command_ref,
        "command_digest": author_command.command_digest,
        "candidate_ref": author_command.candidate_ref,
        "repository_ref": attempt_fence.repository_ref,
        "base_git_object_format": attempt_fence.base_git_object_format,
        "base_git_oid": attempt_fence.base_git_oid,
        "path_ceiling": list(attempt_fence.path_ceiling),
        "effect_ceilings": effect_ceilings.to_mapping(),
        "expires_at": expires_at,
        "global_stop_ref": attempt_fence.global_stop_ref,
        "global_stop_version": attempt_fence.global_stop_version,
        "portable_capsule_digest": portable_capsule_digest,
        "cancellation_target_effect_intent_ref": target_intent,
        "cancellation_target_effect_fence_ref": target_ref,
        "cancellation_target_effect_fence_digest": target_digest,
    }
    identity["effect_fence_digest"] = _domain_digest(
        _EFFECT_FENCE_DOMAIN,
        _canonical_bytes(identity, "create_effect_fence.effect_identity"),
    )
    result = EffectFenceV1.from_mapping(identity)
    validate_effect_relation(
        attempt_fence=attempt_fence,
        author_command=author_command,
        author_effect_fence=author_effect_fence,
        effect_fence=result,
        capsule_manifest=capsule_manifest,
        cancellation_target=cancellation_target,
    )
    return result


def validate_authoring_relation(
    *,
    work_spec: WorkSpecV1,
    attempt_fence: AttemptFenceV1,
    author_command: WorkerCommandV1,
    author_effect_fence: EffectFenceV1,
) -> None:
    _require_exact_value(
        work_spec, WorkSpecV1, "validate_authoring_relation.work_spec"
    )
    _require_exact_value(
        attempt_fence, AttemptFenceV1, "validate_authoring_relation.attempt_fence"
    )
    _require_exact_value(
        author_command,
        WorkerCommandV1,
        "validate_authoring_relation.author_command",
    )
    _require_exact_value(
        author_effect_fence,
        EffectFenceV1,
        "validate_authoring_relation.author_effect_fence",
    )
    _validate_work_spec_attempt_relation(
        work_spec=work_spec, attempt_fence=attempt_fence
    )
    _validate_author_pair_without_work_spec(
        attempt_fence=attempt_fence,
        author_command=author_command,
        author_effect_fence=author_effect_fence,
    )
    _relation(
        work_spec.work_spec_digest == work_spec.computed_digest(),
        "validate_authoring_relation.work_spec_digest",
    )
    for field in (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
    ):
        _relation(
            getattr(author_command, field) == getattr(work_spec, field),
            f"validate_authoring_relation.work_spec.{field}",
        )
    _relation(
        author_command.work_spec_ref == work_spec.work_spec_ref,
        "validate_authoring_relation.work_spec_ref",
    )
    _relation(
        author_command.work_spec_digest == work_spec.work_spec_digest,
        "validate_authoring_relation.work_spec_digest",
    )
    _relation(
        author_command.path_ceiling == work_spec.authorized_paths,
        "validate_authoring_relation.authorized_paths",
    )
    _relation(
        author_command.validation_requirement_ref
        == work_spec.validation_requirement_ref,
        "validate_authoring_relation.validation_requirement_ref",
    )
    _relation(
        author_command.review_requirement_ref == work_spec.review_requirement_ref,
        "validate_authoring_relation.review_requirement_ref",
    )


def _validate_manifest_graph(
    *,
    capsule_manifest: CandidateCapsuleManifestV1,
    author_command: WorkerCommandV1,
    attempt_fence: AttemptFenceV1,
    author_effect_fence: EffectFenceV1,
) -> None:
    _require_exact_value(
        capsule_manifest,
        CandidateCapsuleManifestV1,
        "validate_capsule_manifest_relation.capsule_manifest",
    )
    _validate_author_pair_without_work_spec(
        attempt_fence=attempt_fence,
        author_command=author_command,
        author_effect_fence=author_effect_fence,
    )
    for field in (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "command_ref",
        "command_digest",
        "candidate_ref",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
    ):
        _relation(
            getattr(capsule_manifest, field) == getattr(author_command, field),
            f"validate_capsule_manifest_relation.{field}",
        )
    for field in (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
    ):
        _relation(
            getattr(capsule_manifest, field) == getattr(attempt_fence, field),
            f"validate_capsule_manifest_relation.attempt_fence.{field}",
        )
    for field in (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "command_ref",
        "command_digest",
        "candidate_ref",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
    ):
        _relation(
            getattr(capsule_manifest, field) == getattr(author_effect_fence, field),
            f"validate_capsule_manifest_relation.author_effect_fence.{field}",
        )
    paths = tuple(entry.path for entry in capsule_manifest.entries)
    _relation(
        paths == _AUTHORIZED_PATHS,
        "validate_capsule_manifest_relation.entries",
    )
    _relation(
        capsule_manifest.authorized_path_scope_digest
        == _authorized_path_scope_digest(paths),
        "validate_capsule_manifest_relation.authorized_path_scope_digest",
    )
    _relation(
        capsule_manifest.authorized_path_scope_digest
        == _authorized_path_scope_digest(author_command.path_ceiling),
        "validate_capsule_manifest_relation.path_ceiling",
    )
    _relation(
        capsule_manifest.portable_capsule_digest
        == capsule_manifest.computed_digest(),
        "validate_capsule_manifest_relation.portable_capsule_digest",
    )


def validate_effect_relation(
    *,
    attempt_fence: AttemptFenceV1,
    author_command: WorkerCommandV1,
    author_effect_fence: EffectFenceV1,
    effect_fence: EffectFenceV1,
    capsule_manifest: object = _MISSING,
    cancellation_target: object = _MISSING,
) -> None:
    _require_exact_value(
        attempt_fence, AttemptFenceV1, "validate_effect_relation.attempt_fence"
    )
    _require_exact_value(
        author_command,
        WorkerCommandV1,
        "validate_effect_relation.author_command",
    )
    _require_exact_value(
        author_effect_fence,
        EffectFenceV1,
        "validate_effect_relation.author_effect_fence",
    )
    _require_exact_value(
        effect_fence, EffectFenceV1, "validate_effect_relation.effect_fence"
    )
    _require_optional_relation_exact_value(
        capsule_manifest,
        CandidateCapsuleManifestV1,
        "validate_effect_relation.capsule_manifest",
    )
    _require_optional_relation_exact_value(
        cancellation_target,
        EffectFenceV1,
        "validate_effect_relation.cancellation_target",
    )
    _validate_author_pair_without_work_spec(
        attempt_fence=attempt_fence,
        author_command=author_command,
        author_effect_fence=author_effect_fence,
    )
    _require_exact_value(
        effect_fence, EffectFenceV1, "validate_effect_relation.effect_fence"
    )
    _relation(
        effect_fence.effect_fence_digest == effect_fence.computed_digest(),
        "validate_effect_relation.effect_fence_digest",
    )
    _relation(
        attempt_fence.allowed_effect_classes.count(effect_fence.effect_class) == 1,
        "validate_effect_relation.allowed_effect_classes",
    )
    for field in (
        "parent_standing_grant_ref",
        "parent_standing_grant_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "path_ceiling",
        "global_stop_ref",
        "global_stop_version",
    ):
        _relation(
            getattr(effect_fence, field) == getattr(attempt_fence, field),
            f"validate_effect_relation.{field}",
        )
    for field in (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "command_ref",
        "command_digest",
        "candidate_ref",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "global_stop_ref",
        "global_stop_version",
    ):
        _relation(
            getattr(effect_fence, field) == getattr(author_command, field),
            f"validate_effect_relation.author_command.{field}",
        )
    _relation(
        effect_fence.expires_at <= attempt_fence.expires_at,
        "validate_effect_relation.expires_at",
    )
    _relation(
        _ceilings_at_most(effect_fence.effect_ceilings, attempt_fence.aggregate_ceilings),
        "validate_effect_relation.effect_ceilings",
    )
    if effect_fence.effect_class == "local_git_commit":
        _relation(
            _local_git_effect_ceilings(effect_fence.effect_ceilings),
            "validate_effect_relation.git_effect_ceilings",
        )
    else:
        _relation(
            _non_git_effect_ceilings(effect_fence.effect_ceilings),
            "validate_effect_relation.git_effect_ceilings",
        )
    if effect_fence.effect_class == "author_candidate":
        _relation(
            effect_fence == author_effect_fence,
            "validate_effect_relation.author_effect_fence",
        )
        _relation(
            capsule_manifest is _MISSING,
            "validate_effect_relation.capsule_manifest",
        )
        _relation(
            cancellation_target is _MISSING,
            "validate_effect_relation.cancellation_target",
        )
        return
    if effect_fence.effect_class in (
        "validate_candidate",
        "review_candidate",
        "local_git_commit",
    ):
        _require_exact_value(
            capsule_manifest,
            CandidateCapsuleManifestV1,
            "validate_effect_relation.capsule_manifest",
        )
        manifest = typing.cast(CandidateCapsuleManifestV1, capsule_manifest)
        _validate_manifest_graph(
            capsule_manifest=manifest,
            author_command=author_command,
            attempt_fence=attempt_fence,
            author_effect_fence=author_effect_fence,
        )
        _relation(
            effect_fence.portable_capsule_digest
            == manifest.portable_capsule_digest,
            "validate_effect_relation.portable_capsule_digest",
        )
        _relation(
            cancellation_target is _MISSING,
            "validate_effect_relation.cancellation_target",
        )
        return
    _relation(
        effect_fence.effect_class == "cancel_effect",
        "validate_effect_relation.effect_class",
    )
    _require_exact_value(
        cancellation_target,
        EffectFenceV1,
        "validate_effect_relation.cancellation_target",
    )
    target = typing.cast(EffectFenceV1, cancellation_target)
    _relation(
        target.effect_class in _CANCELLATION_TARGET_CLASSES,
        "validate_effect_relation.cancellation_target.effect_class",
    )
    target_manifest: object = (
        _MISSING if target.effect_class == "author_candidate" else capsule_manifest
    )
    validate_effect_relation(
        attempt_fence=attempt_fence,
        author_command=author_command,
        author_effect_fence=author_effect_fence,
        effect_fence=target,
        capsule_manifest=target_manifest,
        cancellation_target=_MISSING,
    )
    _relation(
        target != effect_fence,
        "validate_effect_relation.cancellation_target.self",
    )
    _relation(
        effect_fence.effect_intent_ref != target.effect_intent_ref,
        "validate_effect_relation.cancellation_target.effect_intent_ref_collision",
    )
    _relation(
        effect_fence.effect_fence_ref != target.effect_fence_ref,
        "validate_effect_relation.cancellation_target.effect_fence_ref_collision",
    )
    _relation(
        effect_fence.effect_fence_digest != target.effect_fence_digest,
        "validate_effect_relation.cancellation_target.effect_fence_digest_collision",
    )
    _relation(
        effect_fence.cancellation_target_effect_intent_ref == target.effect_intent_ref
        and effect_fence.cancellation_target_effect_fence_ref == target.effect_fence_ref
        and effect_fence.cancellation_target_effect_fence_digest
        == target.effect_fence_digest,
        "validate_effect_relation.cancellation_target.tuple",
    )
    for field in (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "repository_ref",
        "base_git_object_format",
        "base_git_oid",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "command_ref",
        "command_digest",
        "candidate_ref",
    ):
        _relation(
            getattr(effect_fence, field) == getattr(target, field),
            f"validate_effect_relation.cancellation_target.{field}",
        )
    if target.effect_class == "author_candidate":
        _relation(
            capsule_manifest is _MISSING,
            "validate_effect_relation.capsule_manifest",
        )
        _relation(
            target.portable_capsule_digest is None
            and effect_fence.portable_capsule_digest is None,
            "validate_effect_relation.portable_capsule_digest",
        )
    else:
        _require_exact_value(
            capsule_manifest,
            CandidateCapsuleManifestV1,
            "validate_effect_relation.capsule_manifest",
        )
        _relation(
            target.portable_capsule_digest is not None
            and effect_fence.portable_capsule_digest
            == target.portable_capsule_digest,
            "validate_effect_relation.portable_capsule_digest",
        )


def validate_delivery_relation(
    *,
    delivery: DeliveryEnvelopeV1,
    author_command: WorkerCommandV1,
    attempt_fence: AttemptFenceV1,
    author_effect_fence: EffectFenceV1,
    effect_fence: EffectFenceV1,
    capsule_manifest: object = _MISSING,
    cancellation_target: object = _MISSING,
) -> None:
    _require_exact_value(
        delivery, DeliveryEnvelopeV1, "validate_delivery_relation.delivery"
    )
    _require_exact_value(
        author_command,
        WorkerCommandV1,
        "validate_delivery_relation.author_command",
    )
    _require_exact_value(
        attempt_fence,
        AttemptFenceV1,
        "validate_delivery_relation.attempt_fence",
    )
    _require_exact_value(
        author_effect_fence,
        EffectFenceV1,
        "validate_delivery_relation.author_effect_fence",
    )
    _require_exact_value(
        effect_fence, EffectFenceV1, "validate_delivery_relation.effect_fence"
    )
    _require_optional_relation_exact_value(
        capsule_manifest,
        CandidateCapsuleManifestV1,
        "validate_delivery_relation.capsule_manifest",
    )
    _require_optional_relation_exact_value(
        cancellation_target,
        EffectFenceV1,
        "validate_delivery_relation.cancellation_target",
    )
    validate_effect_relation(
        attempt_fence=attempt_fence,
        author_command=author_command,
        author_effect_fence=author_effect_fence,
        effect_fence=effect_fence,
        capsule_manifest=capsule_manifest,
        cancellation_target=cancellation_target,
    )
    _relation(
        effect_fence.effect_class in _DELIVERABLE_EFFECT_CLASSES,
        "validate_delivery_relation.effect_class",
    )
    _relation(
        delivery.delivery_envelope_digest == delivery.computed_digest(),
        "validate_delivery_relation.delivery_envelope_digest",
    )
    for field in (
        "program_ref",
        "program_version_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "command_ref",
        "command_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
    ):
        _relation(
            getattr(delivery, field) == getattr(effect_fence, field),
            f"validate_delivery_relation.{field}",
        )
    for field in (
        "program_ref",
        "program_version_ref",
        "semantic_attempt_ref",
        "command_ref",
        "command_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
    ):
        _relation(
            getattr(delivery, field) == getattr(author_command, field),
            f"validate_delivery_relation.author_command.{field}",
        )


def validate_redelivery_relation(
    *,
    original_delivery: DeliveryEnvelopeV1,
    candidate_delivery: DeliveryEnvelopeV1,
    author_command: WorkerCommandV1,
    attempt_fence: AttemptFenceV1,
    author_effect_fence: EffectFenceV1,
    effect_fence: EffectFenceV1,
    capsule_manifest: object = _MISSING,
    cancellation_target: object = _MISSING,
) -> None:
    _require_exact_value(
        original_delivery,
        DeliveryEnvelopeV1,
        "validate_redelivery_relation.original_delivery",
    )
    _require_exact_value(
        candidate_delivery,
        DeliveryEnvelopeV1,
        "validate_redelivery_relation.candidate_delivery",
    )
    _require_exact_value(
        author_command,
        WorkerCommandV1,
        "validate_redelivery_relation.author_command",
    )
    _require_exact_value(
        attempt_fence,
        AttemptFenceV1,
        "validate_redelivery_relation.attempt_fence",
    )
    _require_exact_value(
        author_effect_fence,
        EffectFenceV1,
        "validate_redelivery_relation.author_effect_fence",
    )
    _require_exact_value(
        effect_fence, EffectFenceV1, "validate_redelivery_relation.effect_fence"
    )
    _require_optional_relation_exact_value(
        capsule_manifest,
        CandidateCapsuleManifestV1,
        "validate_redelivery_relation.capsule_manifest",
    )
    _require_optional_relation_exact_value(
        cancellation_target,
        EffectFenceV1,
        "validate_redelivery_relation.cancellation_target",
    )
    validate_delivery_relation(
        delivery=original_delivery,
        author_command=author_command,
        attempt_fence=attempt_fence,
        author_effect_fence=author_effect_fence,
        effect_fence=effect_fence,
        capsule_manifest=capsule_manifest,
        cancellation_target=cancellation_target,
    )
    validate_delivery_relation(
        delivery=candidate_delivery,
        author_command=author_command,
        attempt_fence=attempt_fence,
        author_effect_fence=author_effect_fence,
        effect_fence=effect_fence,
        capsule_manifest=capsule_manifest,
        cancellation_target=cancellation_target,
    )
    original_identity = original_delivery.identity_mapping()
    candidate_identity = candidate_delivery.identity_mapping()
    changed = tuple(
        field
        for field in DeliveryEnvelopeV1._FIELDS
        if field != "delivery_envelope_digest"
        and original_identity[field] != candidate_identity[field]
    )
    _relation(
        set(changed)
        == {"delivery_attempt_ref", "adapter_safe_correlation_ref"},
        "validate_redelivery_relation.delta",
    )
    _relation(
        original_delivery.delivery_envelope_digest
        != candidate_delivery.delivery_envelope_digest,
        "validate_redelivery_relation.delivery_envelope_digest",
    )


def validate_capsule_manifest_relation(
    *,
    capsule_manifest: CandidateCapsuleManifestV1,
    author_command: WorkerCommandV1,
    attempt_fence: AttemptFenceV1,
    author_effect_fence: EffectFenceV1,
    before_blobs: dict[str, bytes],
    after_blobs: dict[str, bytes],
) -> None:
    _require_exact_value(
        capsule_manifest,
        CandidateCapsuleManifestV1,
        "validate_capsule_manifest_relation.capsule_manifest",
    )
    _require_exact_value(
        author_command,
        WorkerCommandV1,
        "validate_capsule_manifest_relation.author_command",
    )
    _require_exact_value(
        attempt_fence,
        AttemptFenceV1,
        "validate_capsule_manifest_relation.attempt_fence",
    )
    _require_exact_value(
        author_effect_fence,
        EffectFenceV1,
        "validate_capsule_manifest_relation.author_effect_fence",
    )
    if type(before_blobs) is not dict:
        _fail("invalid_field_type", "validate_capsule_manifest_relation.before_blobs")
    if type(after_blobs) is not dict:
        _fail("invalid_field_type", "validate_capsule_manifest_relation.after_blobs")
    _require_blob_map_types(
        before_blobs, "validate_capsule_manifest_relation.before_blobs"
    )
    _require_blob_map_types(
        after_blobs, "validate_capsule_manifest_relation.after_blobs"
    )
    before = _require_blob_map(
        before_blobs, "validate_capsule_manifest_relation.before_blobs"
    )
    after = _require_blob_map(
        after_blobs, "validate_capsule_manifest_relation.after_blobs"
    )
    _validate_manifest_graph(
        capsule_manifest=capsule_manifest,
        author_command=author_command,
        attempt_fence=attempt_fence,
        author_effect_fence=author_effect_fence,
    )
    for entry in capsule_manifest.entries:
        _relation(
            entry.before_byte_length == len(before[entry.path]),
            "validate_capsule_manifest_relation.before_byte_length",
        )
        _relation(
            entry.after_byte_length == len(after[entry.path]),
            "validate_capsule_manifest_relation.after_byte_length",
        )
        _relation(
            entry.before_blob_sha256
            == hashlib.sha256(before[entry.path]).hexdigest(),
            "validate_capsule_manifest_relation.before_blob_sha256",
        )
        _relation(
            entry.after_blob_sha256 == hashlib.sha256(after[entry.path]).hexdigest(),
            "validate_capsule_manifest_relation.after_blob_sha256",
        )


def validate_observation_relation(
    *,
    observation: WorkerObservationV1,
    delivery: DeliveryEnvelopeV1,
    author_command: WorkerCommandV1,
    attempt_fence: AttemptFenceV1,
    author_effect_fence: EffectFenceV1,
    effect_fence: EffectFenceV1,
    capsule_manifest: object = _MISSING,
    before_blobs: object = _MISSING,
    after_blobs: object = _MISSING,
    cancellation_target: object = _MISSING,
) -> None:
    _require_exact_value(
        observation, WorkerObservationV1, "validate_observation_relation.observation"
    )
    _require_exact_value(
        delivery,
        DeliveryEnvelopeV1,
        "validate_observation_relation.delivery",
    )
    _require_exact_value(
        author_command,
        WorkerCommandV1,
        "validate_observation_relation.author_command",
    )
    _require_exact_value(
        attempt_fence,
        AttemptFenceV1,
        "validate_observation_relation.attempt_fence",
    )
    _require_exact_value(
        author_effect_fence,
        EffectFenceV1,
        "validate_observation_relation.author_effect_fence",
    )
    _require_exact_value(
        effect_fence,
        EffectFenceV1,
        "validate_observation_relation.effect_fence",
    )
    _require_optional_relation_exact_value(
        capsule_manifest,
        CandidateCapsuleManifestV1,
        "validate_observation_relation.capsule_manifest",
    )
    _require_optional_relation_exact_value(
        before_blobs, dict, "validate_observation_relation.before_blobs"
    )
    _require_optional_relation_exact_value(
        after_blobs, dict, "validate_observation_relation.after_blobs"
    )
    _require_optional_relation_exact_value(
        cancellation_target,
        EffectFenceV1,
        "validate_observation_relation.cancellation_target",
    )
    _require_optional_blob_map_types(
        before_blobs, "validate_observation_relation.before_blobs"
    )
    _require_optional_blob_map_types(
        after_blobs, "validate_observation_relation.after_blobs"
    )
    effect_capsule: object = _MISSING
    if effect_fence.effect_class in ("validate_candidate", "review_candidate"):
        effect_capsule = capsule_manifest
    elif effect_fence.effect_class == "cancel_effect" and type(cancellation_target) is EffectFenceV1:
        target = typing.cast(EffectFenceV1, cancellation_target)
        if target.effect_class in ("validate_candidate", "review_candidate"):
            effect_capsule = capsule_manifest
    validate_delivery_relation(
        delivery=delivery,
        author_command=author_command,
        attempt_fence=attempt_fence,
        author_effect_fence=author_effect_fence,
        effect_fence=effect_fence,
        capsule_manifest=effect_capsule,
        cancellation_target=cancellation_target,
    )
    _relation(
        observation.observation_digest == observation.computed_digest(),
        "validate_observation_relation.observation_digest",
    )
    _relation(
        effect_fence.effect_class
        in _effect_classes_for_observation(observation.observation_kind),
        "validate_observation_relation.effect_class",
    )
    for field in (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "command_ref",
        "command_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
    ):
        _relation(
            getattr(observation, field) == getattr(effect_fence, field),
            f"validate_observation_relation.effect_fence.{field}",
        )
    for field in (
        "program_ref",
        "program_version_ref",
        "semantic_attempt_ref",
        "effect_intent_ref",
        "command_ref",
        "command_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
        "effect_fence_ref",
        "effect_fence_digest",
        "delivery_attempt_ref",
    ):
        _relation(
            getattr(observation, field) == getattr(delivery, field),
            f"validate_observation_relation.delivery.{field}",
        )
    for field in (
        "program_ref",
        "program_version_ref",
        "accepted_intent_revision_ref",
        "work_item_ref",
        "work_item_revision_ref",
        "semantic_attempt_ref",
        "command_ref",
        "command_digest",
        "attempt_fence_ref",
        "attempt_fence_digest",
    ):
        _relation(
            getattr(observation, field) == getattr(author_command, field),
            f"validate_observation_relation.author_command.{field}",
        )
    if observation.observation_kind in _ADAPTER_AUTHORED_OBSERVATIONS:
        expected_source = (
            "direct_local_adapter"
            if delivery.adapter_kind == "direct_local_bootstrap"
            else "es_adapter"
        )
        _relation(
            observation.source_kind == expected_source,
            "validate_observation_relation.route_source",
        )
    conditional = _observation_conditional(observation.observation_kind)
    if conditional == "candidate":
        _relation(
            observation.candidate_ref
            == effect_fence.candidate_ref
            == author_command.candidate_ref,
            "validate_observation_relation.candidate_ref",
        )
        _relation(
            capsule_manifest is _MISSING
            and before_blobs is _MISSING
            and after_blobs is _MISSING,
            "validate_observation_relation.capsule_manifest",
        )
        return
    if conditional == "capsule":
        _require_exact_value(
            capsule_manifest,
            CandidateCapsuleManifestV1,
            "validate_observation_relation.capsule_manifest",
        )
        if type(before_blobs) is not dict:
            _fail("relation_mismatch", "validate_observation_relation.before_blobs")
        if type(after_blobs) is not dict:
            _fail("relation_mismatch", "validate_observation_relation.after_blobs")
        manifest = typing.cast(CandidateCapsuleManifestV1, capsule_manifest)
        validate_capsule_manifest_relation(
            capsule_manifest=manifest,
            author_command=author_command,
            attempt_fence=attempt_fence,
            author_effect_fence=author_effect_fence,
            before_blobs=typing.cast(dict[str, bytes], before_blobs),
            after_blobs=typing.cast(dict[str, bytes], after_blobs),
        )
        _relation(
            observation.candidate_ref == manifest.candidate_ref
            and observation.capsule_manifest_ref == manifest.capsule_manifest_ref
            and observation.portable_capsule_digest
            == manifest.portable_capsule_digest,
            "validate_observation_relation.capsule_binding",
        )
        _relation(
            observation.candidate_ref == effect_fence.candidate_ref,
            "validate_observation_relation.candidate_ref",
        )
        if effect_fence.effect_class in ("validate_candidate", "review_candidate"):
            _relation(
                effect_fence.portable_capsule_digest
                == manifest.portable_capsule_digest,
                "validate_observation_relation.portable_capsule_digest",
            )
        return
    _relation(
        before_blobs is _MISSING and after_blobs is _MISSING,
        "validate_observation_relation.capsule_blobs",
    )
    _relation(
        (effect_capsule is _MISSING and capsule_manifest is _MISSING)
        or (
            effect_capsule is capsule_manifest
            and type(capsule_manifest) is CandidateCapsuleManifestV1
        ),
        "validate_observation_relation.capsule_manifest",
    )
    if observation.observation_kind in (
        "cancellation_acknowledged",
        "cancellation_rejected",
    ):
        _relation(
            effect_fence.effect_class == "cancel_effect"
            and type(cancellation_target) is EffectFenceV1,
            "validate_observation_relation.cancellation_target",
        )
