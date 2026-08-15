"""Pure private C2B2 row values for development program state."""

from __future__ import annotations

import typing

from ._development_row_value_support import (
    _ImmutableValue,
    _RowValueValidationError,
    _canonical_identity_bytes,
    _decode_fixed_paths_json,
    _domain_separated_digest,
    _encode_fixed_paths,
    _new_database_integrity_error,
    _require_constant_string,
    _require_enum,
    _require_fixed_paths,
    _require_git_object_format,
    _require_git_oid,
    _require_matching_digest,
    _require_nonnegative_integer,
    _require_optional_safe_ref,
    _require_positive_integer,
    _require_safe_ref,
    _require_sha256,
    _require_utc_timestamp,
    _row_tuple_to_private_mapping,
)
from ._worker_execution_semantic_values import WorkSpecV1


__all__: tuple[str, ...] = ()


_DEVELOPMENT_PROGRAM_HEAD_COLUMNS = (
    "schema_id",
    "program_ref",
    "current_program_version_ref",
    "current_program_version_number",
    "head_revision",
    "program_state",
    "updated_at",
    "head_digest",
)
_DEVELOPMENT_PROGRAM_VERSION_COLUMNS = (
    "schema_id",
    "program_version_ref",
    "program_ref",
    "program_version_number",
    "program_version_kind",
    "creating_decision_ref",
    "accepted_intent_revision_ref",
    "created_at",
    "program_version_digest",
)
_DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS = (
    "schema_id",
    "accepted_intent_revision_ref",
    "program_ref",
    "accepted_intent_revision_number",
    "prior_accepted_intent_revision_ref",
    "source_intent_ref",
    "source_intent_digest",
    "safe_projection_digest",
    "created_at",
    "accepted_intent_revision_digest",
)
_DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS = (
    "schema_id",
    "work_item_ref",
    "program_ref",
    "current_work_item_revision_ref",
    "current_work_item_revision_number",
    "head_revision",
    "work_state",
    "updated_at",
    "head_digest",
)
_DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS = (
    "schema_id",
    "work_item_revision_ref",
    "program_ref",
    "work_item_ref",
    "work_item_revision_number",
    "work_item_revision_kind",
    "prior_work_item_revision_ref",
    "accepted_intent_revision_ref",
    "created_at",
    "work_item_revision_digest",
)
_DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS = (
    "schema_id",
    "program_ref",
    "program_version_ref",
    "work_item_ref",
    "work_item_revision_ref",
    "membership_ordinal",
    "created_at",
    "membership_digest",
)
_DEVELOPMENT_REVISION_EDGE_COLUMNS = (
    "schema_id",
    "revision_edge_ref",
    "relation_key_digest",
    "program_ref",
    "revision_edge_kind",
    "from_accepted_intent_revision_ref",
    "to_accepted_intent_revision_ref",
    "from_work_item_revision_ref",
    "to_work_item_revision_ref",
    "created_at",
    "revision_edge_digest",
)
_DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS = (
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
    "authorized_paths_json",
    "validation_requirement_ref",
    "review_requirement_ref",
    "privacy_classification",
    "work_spec_digest",
    "safe_projection_digest",
    "recorded_at",
    "work_spec_binding_digest",
)
_DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS = (
    "schema_id",
    "semantic_attempt_ref",
    "program_ref",
    "program_version_ref",
    "accepted_intent_revision_ref",
    "work_item_ref",
    "work_item_revision_ref",
    "attempt_number",
    "candidate_ref",
    "attempt_phase",
    "selection_decision_ref",
    "created_at",
    "semantic_attempt_digest",
)

_DEVELOPMENT_PROGRAM_HEAD_SCHEMA = "governed-execution.nwp-development-program-head.v1"
_DEVELOPMENT_PROGRAM_VERSION_SCHEMA = (
    "governed-execution.nwp-development-program-version.v1"
)
_DEVELOPMENT_ACCEPTED_INTENT_REVISION_SCHEMA = (
    "governed-execution.nwp-development-accepted-intent-revision.v1"
)
_DEVELOPMENT_WORK_ITEM_HEAD_SCHEMA = (
    "governed-execution.nwp-development-work-item-head.v1"
)
_DEVELOPMENT_WORK_ITEM_REVISION_SCHEMA = (
    "governed-execution.nwp-development-work-item-revision.v1"
)
_DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_SCHEMA = (
    "governed-execution.nwp-development-program-version-work-item.v1"
)
_DEVELOPMENT_REVISION_EDGE_SCHEMA = (
    "governed-execution.nwp-development-revision-edge.v1"
)
_DEVELOPMENT_WORK_SPEC_BINDING_SCHEMA = (
    "governed-execution.nwp-development-work-spec-binding.v1"
)
_DEVELOPMENT_SEMANTIC_ATTEMPT_SCHEMA = (
    "governed-execution.nwp-development-semantic-attempt.v1"
)
_DEVELOPMENT_WORK_SPEC_SAFE_PROJECTION_SCHEMA = (
    "governed-execution.nwp-development-work-spec-safe-projection.v1"
)

_DEVELOPMENT_PROGRAM_HEAD_DOMAIN = _DEVELOPMENT_PROGRAM_HEAD_SCHEMA + ".identity"
_DEVELOPMENT_PROGRAM_VERSION_DOMAIN = _DEVELOPMENT_PROGRAM_VERSION_SCHEMA + ".identity"
_DEVELOPMENT_ACCEPTED_INTENT_REVISION_DOMAIN = (
    _DEVELOPMENT_ACCEPTED_INTENT_REVISION_SCHEMA + ".identity"
)
_DEVELOPMENT_WORK_ITEM_HEAD_DOMAIN = _DEVELOPMENT_WORK_ITEM_HEAD_SCHEMA + ".identity"
_DEVELOPMENT_WORK_ITEM_REVISION_DOMAIN = (
    _DEVELOPMENT_WORK_ITEM_REVISION_SCHEMA + ".identity"
)
_DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_DOMAIN = (
    _DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_SCHEMA + ".identity"
)
_DEVELOPMENT_REVISION_EDGE_DOMAIN = _DEVELOPMENT_REVISION_EDGE_SCHEMA + ".identity"
_DEVELOPMENT_WORK_SPEC_BINDING_DOMAIN = (
    _DEVELOPMENT_WORK_SPEC_BINDING_SCHEMA + ".identity"
)
_DEVELOPMENT_SEMANTIC_ATTEMPT_DOMAIN = (
    _DEVELOPMENT_SEMANTIC_ATTEMPT_SCHEMA + ".identity"
)
_DEVELOPMENT_WORK_SPEC_SAFE_PROJECTION_DOMAIN = (
    _DEVELOPMENT_WORK_SPEC_SAFE_PROJECTION_SCHEMA + ".identity"
)

_PROGRAM_STATES = ("active", "accepted", "terminal_rejected", "blocked")
_PROGRAM_VERSION_KINDS = (
    "initial",
    "accepted",
    "repair",
    "replan",
    "terminal_rejected",
    "blocked",
)
_WORK_STATES = (
    "planned",
    "active",
    "accepted",
    "repair_required",
    "terminal_rejected",
    "blocked",
)
_WORK_ITEM_REVISION_KINDS = ("initial", "replan")
_REVISION_EDGE_KINDS = (
    "accepted_intent_supersedes",
    "work_item_supersedes",
    "work_item_split",
    "work_item_merge",
)
_ATTEMPT_PHASES = ("established",)


class _DigestBackedValue(_ImmutableValue):
    __slots__ = ()
    _DOMAIN = ""

    def identity_mapping(self) -> dict[str, object]:
        return self._identity_mapping()

    def canonical_identity_bytes(self) -> bytes:
        return _canonical_identity_bytes(self._identity_mapping())

    def computed_digest(self) -> str:
        return _domain_separated_digest(self._DOMAIN, self._identity_mapping())


class DevelopmentProgramHeadRowValue(_DigestBackedValue):
    __slots__ = ("_values",)
    _DOMAIN = _DEVELOPMENT_PROGRAM_HEAD_DOMAIN

    @property
    def schema_id(self) -> str: return typing.cast(str, self._values[0])
    @property
    def program_ref(self) -> str: return typing.cast(str, self._values[1])
    @property
    def current_program_version_ref(self) -> str: return typing.cast(str, self._values[2])
    @property
    def current_program_version_number(self) -> int: return typing.cast(int, self._values[3])
    @property
    def head_revision(self) -> int: return typing.cast(int, self._values[4])
    @property
    def program_state(self) -> str: return typing.cast(str, self._values[5])
    @property
    def updated_at(self) -> str: return typing.cast(str, self._values[6])
    @property
    def head_digest(self) -> str: return typing.cast(str, self._values[7])

    def _identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "program_ref": self.program_ref,
            "current_program_version_ref": self.current_program_version_ref,
            "current_program_version_number": self.current_program_version_number,
            "head_revision": self.head_revision,
            "program_state": self.program_state,
            "updated_at": self.updated_at,
        }

    @classmethod
    def _from_validated(cls, values: tuple[object, ...]) -> DevelopmentProgramHeadRowValue:
        result = object.__new__(cls)
        object.__setattr__(result, "_values", values)
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentProgramVersionRowValue(_DigestBackedValue):
    __slots__ = ("_values",)
    _DOMAIN = _DEVELOPMENT_PROGRAM_VERSION_DOMAIN

    @property
    def schema_id(self) -> str: return typing.cast(str, self._values[0])
    @property
    def program_version_ref(self) -> str: return typing.cast(str, self._values[1])
    @property
    def program_ref(self) -> str: return typing.cast(str, self._values[2])
    @property
    def program_version_number(self) -> int: return typing.cast(int, self._values[3])
    @property
    def program_version_kind(self) -> str: return typing.cast(str, self._values[4])
    @property
    def creating_decision_ref(self) -> str: return typing.cast(str, self._values[5])
    @property
    def accepted_intent_revision_ref(self) -> str: return typing.cast(str, self._values[6])
    @property
    def created_at(self) -> str: return typing.cast(str, self._values[7])
    @property
    def program_version_digest(self) -> str: return typing.cast(str, self._values[8])

    def _identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "program_version_ref": self.program_version_ref,
            "program_ref": self.program_ref,
            "program_version_number": self.program_version_number,
            "program_version_kind": self.program_version_kind,
            "creating_decision_ref": self.creating_decision_ref,
            "accepted_intent_revision_ref": self.accepted_intent_revision_ref,
            "created_at": self.created_at,
        }

    @classmethod
    def _from_validated(cls, values: tuple[object, ...]) -> DevelopmentProgramVersionRowValue:
        result = object.__new__(cls)
        object.__setattr__(result, "_values", values)
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentAcceptedIntentRevisionRowValue(_DigestBackedValue):
    __slots__ = ("_values",)
    _DOMAIN = _DEVELOPMENT_ACCEPTED_INTENT_REVISION_DOMAIN

    @property
    def schema_id(self) -> str: return typing.cast(str, self._values[0])
    @property
    def accepted_intent_revision_ref(self) -> str: return typing.cast(str, self._values[1])
    @property
    def program_ref(self) -> str: return typing.cast(str, self._values[2])
    @property
    def accepted_intent_revision_number(self) -> int: return typing.cast(int, self._values[3])
    @property
    def prior_accepted_intent_revision_ref(self) -> str | None: return typing.cast(str | None, self._values[4])
    @property
    def source_intent_ref(self) -> str: return typing.cast(str, self._values[5])
    @property
    def source_intent_digest(self) -> str: return typing.cast(str, self._values[6])
    @property
    def safe_projection_digest(self) -> str: return typing.cast(str, self._values[7])
    @property
    def created_at(self) -> str: return typing.cast(str, self._values[8])
    @property
    def accepted_intent_revision_digest(self) -> str: return typing.cast(str, self._values[9])

    def _identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "accepted_intent_revision_ref": self.accepted_intent_revision_ref,
            "program_ref": self.program_ref,
            "accepted_intent_revision_number": self.accepted_intent_revision_number,
            "prior_accepted_intent_revision_ref": self.prior_accepted_intent_revision_ref,
            "source_intent_ref": self.source_intent_ref,
            "source_intent_digest": self.source_intent_digest,
            "safe_projection_digest": self.safe_projection_digest,
            "created_at": self.created_at,
        }

    @classmethod
    def _from_validated(cls, values: tuple[object, ...]) -> DevelopmentAcceptedIntentRevisionRowValue:
        result = object.__new__(cls)
        object.__setattr__(result, "_values", values)
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentWorkItemHeadRowValue(_DigestBackedValue):
    __slots__ = ("_values",)
    _DOMAIN = _DEVELOPMENT_WORK_ITEM_HEAD_DOMAIN

    @property
    def schema_id(self) -> str: return typing.cast(str, self._values[0])
    @property
    def work_item_ref(self) -> str: return typing.cast(str, self._values[1])
    @property
    def program_ref(self) -> str: return typing.cast(str, self._values[2])
    @property
    def current_work_item_revision_ref(self) -> str: return typing.cast(str, self._values[3])
    @property
    def current_work_item_revision_number(self) -> int: return typing.cast(int, self._values[4])
    @property
    def head_revision(self) -> int: return typing.cast(int, self._values[5])
    @property
    def work_state(self) -> str: return typing.cast(str, self._values[6])
    @property
    def updated_at(self) -> str: return typing.cast(str, self._values[7])
    @property
    def head_digest(self) -> str: return typing.cast(str, self._values[8])

    def _identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "work_item_ref": self.work_item_ref,
            "program_ref": self.program_ref,
            "current_work_item_revision_ref": self.current_work_item_revision_ref,
            "current_work_item_revision_number": self.current_work_item_revision_number,
            "head_revision": self.head_revision,
            "work_state": self.work_state,
            "updated_at": self.updated_at,
        }

    @classmethod
    def _from_validated(cls, values: tuple[object, ...]) -> DevelopmentWorkItemHeadRowValue:
        result = object.__new__(cls)
        object.__setattr__(result, "_values", values)
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentWorkItemRevisionRowValue(_DigestBackedValue):
    __slots__ = ("_values",)
    _DOMAIN = _DEVELOPMENT_WORK_ITEM_REVISION_DOMAIN

    @property
    def schema_id(self) -> str: return typing.cast(str, self._values[0])
    @property
    def work_item_revision_ref(self) -> str: return typing.cast(str, self._values[1])
    @property
    def program_ref(self) -> str: return typing.cast(str, self._values[2])
    @property
    def work_item_ref(self) -> str: return typing.cast(str, self._values[3])
    @property
    def work_item_revision_number(self) -> int: return typing.cast(int, self._values[4])
    @property
    def work_item_revision_kind(self) -> str: return typing.cast(str, self._values[5])
    @property
    def prior_work_item_revision_ref(self) -> str | None: return typing.cast(str | None, self._values[6])
    @property
    def accepted_intent_revision_ref(self) -> str: return typing.cast(str, self._values[7])
    @property
    def created_at(self) -> str: return typing.cast(str, self._values[8])
    @property
    def work_item_revision_digest(self) -> str: return typing.cast(str, self._values[9])

    def _identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "work_item_revision_ref": self.work_item_revision_ref,
            "program_ref": self.program_ref,
            "work_item_ref": self.work_item_ref,
            "work_item_revision_number": self.work_item_revision_number,
            "work_item_revision_kind": self.work_item_revision_kind,
            "prior_work_item_revision_ref": self.prior_work_item_revision_ref,
            "accepted_intent_revision_ref": self.accepted_intent_revision_ref,
            "created_at": self.created_at,
        }

    @classmethod
    def _from_validated(cls, values: tuple[object, ...]) -> DevelopmentWorkItemRevisionRowValue:
        result = object.__new__(cls)
        object.__setattr__(result, "_values", values)
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentProgramVersionWorkItemRowValue(_DigestBackedValue):
    __slots__ = ("_values",)
    _DOMAIN = _DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_DOMAIN

    @property
    def schema_id(self) -> str: return typing.cast(str, self._values[0])
    @property
    def program_ref(self) -> str: return typing.cast(str, self._values[1])
    @property
    def program_version_ref(self) -> str: return typing.cast(str, self._values[2])
    @property
    def work_item_ref(self) -> str: return typing.cast(str, self._values[3])
    @property
    def work_item_revision_ref(self) -> str: return typing.cast(str, self._values[4])
    @property
    def membership_ordinal(self) -> int: return typing.cast(int, self._values[5])
    @property
    def created_at(self) -> str: return typing.cast(str, self._values[6])
    @property
    def membership_digest(self) -> str: return typing.cast(str, self._values[7])

    def _identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "program_ref": self.program_ref,
            "program_version_ref": self.program_version_ref,
            "work_item_ref": self.work_item_ref,
            "work_item_revision_ref": self.work_item_revision_ref,
            "membership_ordinal": self.membership_ordinal,
            "created_at": self.created_at,
        }

    @classmethod
    def _from_validated(cls, values: tuple[object, ...]) -> DevelopmentProgramVersionWorkItemRowValue:
        result = object.__new__(cls)
        object.__setattr__(result, "_values", values)
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentRevisionEdgeRowValue(_DigestBackedValue):
    __slots__ = ("_values",)
    _DOMAIN = _DEVELOPMENT_REVISION_EDGE_DOMAIN

    @property
    def schema_id(self) -> str: return typing.cast(str, self._values[0])
    @property
    def revision_edge_ref(self) -> str: return typing.cast(str, self._values[1])
    @property
    def relation_key_digest(self) -> str: return typing.cast(str, self._values[2])
    @property
    def program_ref(self) -> str: return typing.cast(str, self._values[3])
    @property
    def revision_edge_kind(self) -> str: return typing.cast(str, self._values[4])
    @property
    def from_accepted_intent_revision_ref(self) -> str | None: return typing.cast(str | None, self._values[5])
    @property
    def to_accepted_intent_revision_ref(self) -> str | None: return typing.cast(str | None, self._values[6])
    @property
    def from_work_item_revision_ref(self) -> str | None: return typing.cast(str | None, self._values[7])
    @property
    def to_work_item_revision_ref(self) -> str | None: return typing.cast(str | None, self._values[8])
    @property
    def created_at(self) -> str: return typing.cast(str, self._values[9])
    @property
    def revision_edge_digest(self) -> str: return typing.cast(str, self._values[10])

    def _identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "revision_edge_ref": self.revision_edge_ref,
            "relation_key_digest": self.relation_key_digest,
            "program_ref": self.program_ref,
            "revision_edge_kind": self.revision_edge_kind,
            "from_accepted_intent_revision_ref": self.from_accepted_intent_revision_ref,
            "to_accepted_intent_revision_ref": self.to_accepted_intent_revision_ref,
            "from_work_item_revision_ref": self.from_work_item_revision_ref,
            "to_work_item_revision_ref": self.to_work_item_revision_ref,
            "created_at": self.created_at,
        }

    @classmethod
    def _from_validated(cls, values: tuple[object, ...]) -> DevelopmentRevisionEdgeRowValue:
        result = object.__new__(cls)
        object.__setattr__(result, "_values", values)
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentWorkSpecSafeProjection(_DigestBackedValue):
    __slots__ = ("_values",)
    _DOMAIN = _DEVELOPMENT_WORK_SPEC_SAFE_PROJECTION_DOMAIN

    @property
    def schema_id(self) -> str: return typing.cast(str, self._values[0])
    @property
    def work_spec_ref(self) -> str: return typing.cast(str, self._values[1])
    @property
    def program_ref(self) -> str: return typing.cast(str, self._values[2])
    @property
    def program_version_ref(self) -> str: return typing.cast(str, self._values[3])
    @property
    def accepted_intent_revision_ref(self) -> str: return typing.cast(str, self._values[4])
    @property
    def work_item_ref(self) -> str: return typing.cast(str, self._values[5])
    @property
    def work_item_revision_ref(self) -> str: return typing.cast(str, self._values[6])
    @property
    def repository_ref(self) -> str: return typing.cast(str, self._values[7])
    @property
    def base_git_object_format(self) -> str: return typing.cast(str, self._values[8])
    @property
    def base_git_oid(self) -> str: return typing.cast(str, self._values[9])
    @property
    def authorized_paths(self) -> tuple[str, ...]: return typing.cast(tuple[str, ...], self._values[10])
    @property
    def validation_requirement_ref(self) -> str: return typing.cast(str, self._values[11])
    @property
    def review_requirement_ref(self) -> str: return typing.cast(str, self._values[12])
    @property
    def privacy_classification(self) -> str: return typing.cast(str, self._values[13])
    @property
    def work_spec_digest(self) -> str: return typing.cast(str, self._values[14])
    @property
    def safe_projection_digest(self) -> str: return typing.cast(str, self._values[15])

    def _identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "work_spec_ref": self.work_spec_ref,
            "program_ref": self.program_ref,
            "program_version_ref": self.program_version_ref,
            "accepted_intent_revision_ref": self.accepted_intent_revision_ref,
            "work_item_ref": self.work_item_ref,
            "work_item_revision_ref": self.work_item_revision_ref,
            "repository_ref": self.repository_ref,
            "base_git_object_format": self.base_git_object_format,
            "base_git_oid": self.base_git_oid,
            "authorized_paths": self.authorized_paths,
            "validation_requirement_ref": self.validation_requirement_ref,
            "review_requirement_ref": self.review_requirement_ref,
            "privacy_classification": self.privacy_classification,
            "work_spec_digest": self.work_spec_digest,
        }

    @classmethod
    def _from_validated(cls, values: tuple[object, ...]) -> DevelopmentWorkSpecSafeProjection:
        result = object.__new__(cls)
        object.__setattr__(result, "_values", values)
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentWorkSpecBindingRowValue(_DigestBackedValue):
    __slots__ = ("_values",)
    _DOMAIN = _DEVELOPMENT_WORK_SPEC_BINDING_DOMAIN

    @property
    def safe_projection(self) -> DevelopmentWorkSpecSafeProjection:
        return typing.cast(DevelopmentWorkSpecSafeProjection, self._values[0])
    @property
    def schema_id(self) -> str: return _DEVELOPMENT_WORK_SPEC_BINDING_SCHEMA
    @property
    def work_spec_ref(self) -> str: return self.safe_projection.work_spec_ref
    @property
    def program_ref(self) -> str: return self.safe_projection.program_ref
    @property
    def program_version_ref(self) -> str: return self.safe_projection.program_version_ref
    @property
    def accepted_intent_revision_ref(self) -> str: return self.safe_projection.accepted_intent_revision_ref
    @property
    def work_item_ref(self) -> str: return self.safe_projection.work_item_ref
    @property
    def work_item_revision_ref(self) -> str: return self.safe_projection.work_item_revision_ref
    @property
    def repository_ref(self) -> str: return self.safe_projection.repository_ref
    @property
    def base_git_object_format(self) -> str: return self.safe_projection.base_git_object_format
    @property
    def base_git_oid(self) -> str: return self.safe_projection.base_git_oid
    @property
    def authorized_paths_json(self) -> str: return _encode_fixed_paths(self.safe_projection.authorized_paths)
    @property
    def validation_requirement_ref(self) -> str: return self.safe_projection.validation_requirement_ref
    @property
    def review_requirement_ref(self) -> str: return self.safe_projection.review_requirement_ref
    @property
    def privacy_classification(self) -> str: return self.safe_projection.privacy_classification
    @property
    def work_spec_digest(self) -> str: return self.safe_projection.work_spec_digest
    @property
    def safe_projection_digest(self) -> str: return self.safe_projection.safe_projection_digest
    @property
    def recorded_at(self) -> str: return typing.cast(str, self._values[1])
    @property
    def work_spec_binding_digest(self) -> str: return typing.cast(str, self._values[2])

    def _identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "work_spec_ref": self.work_spec_ref,
            "program_ref": self.program_ref,
            "program_version_ref": self.program_version_ref,
            "accepted_intent_revision_ref": self.accepted_intent_revision_ref,
            "work_item_ref": self.work_item_ref,
            "work_item_revision_ref": self.work_item_revision_ref,
            "repository_ref": self.repository_ref,
            "base_git_object_format": self.base_git_object_format,
            "base_git_oid": self.base_git_oid,
            "authorized_paths_json": self.authorized_paths_json,
            "validation_requirement_ref": self.validation_requirement_ref,
            "review_requirement_ref": self.review_requirement_ref,
            "privacy_classification": self.privacy_classification,
            "work_spec_digest": self.work_spec_digest,
            "safe_projection_digest": self.safe_projection_digest,
            "recorded_at": self.recorded_at,
        }

    @classmethod
    def _from_validated(cls, values: tuple[object, ...]) -> DevelopmentWorkSpecBindingRowValue:
        result = object.__new__(cls)
        object.__setattr__(result, "_values", values)
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


class DevelopmentSemanticAttemptRowValue(_DigestBackedValue):
    __slots__ = ("_values",)
    _DOMAIN = _DEVELOPMENT_SEMANTIC_ATTEMPT_DOMAIN

    @property
    def schema_id(self) -> str: return typing.cast(str, self._values[0])
    @property
    def semantic_attempt_ref(self) -> str: return typing.cast(str, self._values[1])
    @property
    def program_ref(self) -> str: return typing.cast(str, self._values[2])
    @property
    def program_version_ref(self) -> str: return typing.cast(str, self._values[3])
    @property
    def accepted_intent_revision_ref(self) -> str: return typing.cast(str, self._values[4])
    @property
    def work_item_ref(self) -> str: return typing.cast(str, self._values[5])
    @property
    def work_item_revision_ref(self) -> str: return typing.cast(str, self._values[6])
    @property
    def attempt_number(self) -> int: return typing.cast(int, self._values[7])
    @property
    def candidate_ref(self) -> str: return typing.cast(str, self._values[8])
    @property
    def attempt_phase(self) -> str: return typing.cast(str, self._values[9])
    @property
    def selection_decision_ref(self) -> str: return typing.cast(str, self._values[10])
    @property
    def created_at(self) -> str: return typing.cast(str, self._values[11])
    @property
    def semantic_attempt_digest(self) -> str: return typing.cast(str, self._values[12])

    def _identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "semantic_attempt_ref": self.semantic_attempt_ref,
            "program_ref": self.program_ref,
            "program_version_ref": self.program_version_ref,
            "accepted_intent_revision_ref": self.accepted_intent_revision_ref,
            "work_item_ref": self.work_item_ref,
            "work_item_revision_ref": self.work_item_revision_ref,
            "attempt_number": self.attempt_number,
            "candidate_ref": self.candidate_ref,
            "attempt_phase": self.attempt_phase,
            "selection_decision_ref": self.selection_decision_ref,
            "created_at": self.created_at,
        }

    @classmethod
    def _from_validated(cls, values: tuple[object, ...]) -> DevelopmentSemanticAttemptRowValue:
        result = object.__new__(cls)
        object.__setattr__(result, "_values", values)
        return result

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


def _validated_safe_projection_fields(
    *,
    work_spec_ref: object,
    program_ref: object,
    program_version_ref: object,
    accepted_intent_revision_ref: object,
    work_item_ref: object,
    work_item_revision_ref: object,
    repository_ref: object,
    base_git_object_format: object,
    base_git_oid: object,
    authorized_paths: object,
    validation_requirement_ref: object,
    review_requirement_ref: object,
    privacy_classification: object,
    work_spec_digest: object,
) -> tuple[tuple[object, ...], dict[str, object]]:
    validated = (
        _DEVELOPMENT_WORK_SPEC_SAFE_PROJECTION_SCHEMA,
        _require_safe_ref(work_spec_ref),
        _require_safe_ref(program_ref),
        _require_safe_ref(program_version_ref),
        _require_safe_ref(accepted_intent_revision_ref),
        _require_safe_ref(work_item_ref),
        _require_safe_ref(work_item_revision_ref),
        _require_safe_ref(repository_ref),
        _require_git_object_format(base_git_object_format),
        _require_git_oid(base_git_oid),
        _require_fixed_paths(authorized_paths),
        _require_safe_ref(validation_requirement_ref),
        _require_safe_ref(review_requirement_ref),
        _require_constant_string(privacy_classification, "private_work_spec"),
        _require_sha256(work_spec_digest),
    )
    identity = {
        "schema_id": validated[0],
        "work_spec_ref": validated[1],
        "program_ref": validated[2],
        "program_version_ref": validated[3],
        "accepted_intent_revision_ref": validated[4],
        "work_item_ref": validated[5],
        "work_item_revision_ref": validated[6],
        "repository_ref": validated[7],
        "base_git_object_format": validated[8],
        "base_git_oid": validated[9],
        "authorized_paths": validated[10],
        "validation_requirement_ref": validated[11],
        "review_requirement_ref": validated[12],
        "privacy_classification": validated[13],
        "work_spec_digest": validated[14],
    }
    return validated, identity


def _constructed_safe_projection_from_fields(
    *,
    work_spec_ref: object,
    program_ref: object,
    program_version_ref: object,
    accepted_intent_revision_ref: object,
    work_item_ref: object,
    work_item_revision_ref: object,
    repository_ref: object,
    base_git_object_format: object,
    base_git_oid: object,
    authorized_paths: object,
    validation_requirement_ref: object,
    review_requirement_ref: object,
    privacy_classification: object,
    work_spec_digest: object,
) -> DevelopmentWorkSpecSafeProjection:
    validated, identity = _validated_safe_projection_fields(
        work_spec_ref=work_spec_ref,
        program_ref=program_ref,
        program_version_ref=program_version_ref,
        accepted_intent_revision_ref=accepted_intent_revision_ref,
        work_item_ref=work_item_ref,
        work_item_revision_ref=work_item_revision_ref,
        repository_ref=repository_ref,
        base_git_object_format=base_git_object_format,
        base_git_oid=base_git_oid,
        authorized_paths=authorized_paths,
        validation_requirement_ref=validation_requirement_ref,
        review_requirement_ref=review_requirement_ref,
        privacy_classification=privacy_classification,
        work_spec_digest=work_spec_digest,
    )
    digest = _domain_separated_digest(
        _DEVELOPMENT_WORK_SPEC_SAFE_PROJECTION_DOMAIN,
        identity,
    )
    return DevelopmentWorkSpecSafeProjection._from_validated(validated + (digest,))


def _persisted_safe_projection_from_fields(
    *,
    work_spec_ref: object,
    program_ref: object,
    program_version_ref: object,
    accepted_intent_revision_ref: object,
    work_item_ref: object,
    work_item_revision_ref: object,
    repository_ref: object,
    base_git_object_format: object,
    base_git_oid: object,
    authorized_paths: object,
    validation_requirement_ref: object,
    review_requirement_ref: object,
    privacy_classification: object,
    work_spec_digest: object,
    persisted_safe_projection_digest: str,
) -> DevelopmentWorkSpecSafeProjection:
    validated, identity = _validated_safe_projection_fields(
        work_spec_ref=work_spec_ref,
        program_ref=program_ref,
        program_version_ref=program_version_ref,
        accepted_intent_revision_ref=accepted_intent_revision_ref,
        work_item_ref=work_item_ref,
        work_item_revision_ref=work_item_revision_ref,
        repository_ref=repository_ref,
        base_git_object_format=base_git_object_format,
        base_git_oid=base_git_oid,
        authorized_paths=authorized_paths,
        validation_requirement_ref=validation_requirement_ref,
        review_requirement_ref=review_requirement_ref,
        privacy_classification=privacy_classification,
        work_spec_digest=work_spec_digest,
    )
    expected_safe_projection_digest = _domain_separated_digest(
        _DEVELOPMENT_WORK_SPEC_SAFE_PROJECTION_DOMAIN,
        identity,
    )
    if persisted_safe_projection_digest != expected_safe_projection_digest:
        raise _RowValueValidationError() from None
    return DevelopmentWorkSpecSafeProjection._from_validated(
        validated + (persisted_safe_projection_digest,)
    )


def _attempt_work_spec_safe_projection(
    work_spec: object,
) -> tuple[
    DevelopmentWorkSpecSafeProjection | None,
    BaseException | None,
]:
    result: DevelopmentWorkSpecSafeProjection | None = None
    error: BaseException | None = None
    try:
        if type(work_spec) is not WorkSpecV1:
            raise _RowValueValidationError() from None
        source = typing.cast(WorkSpecV1, work_spec)
        result = _constructed_safe_projection_from_fields(
            work_spec_ref=source.work_spec_ref,
            program_ref=source.program_ref,
            program_version_ref=source.program_version_ref,
            accepted_intent_revision_ref=source.accepted_intent_revision_ref,
            work_item_ref=source.work_item_ref,
            work_item_revision_ref=source.work_item_revision_ref,
            repository_ref=source.repository_ref,
            base_git_object_format=source.base_git_object_format,
            base_git_oid=source.base_git_oid,
            authorized_paths=source.authorized_paths,
            validation_requirement_ref=source.validation_requirement_ref,
            review_requirement_ref=source.review_requirement_ref,
            privacy_classification=source.privacy_classification,
            work_spec_digest=source.work_spec_digest,
        )
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        source = None
        work_spec = None
    return result, error


def development_work_spec_safe_projection_from_work_spec(
    *,
    work_spec: object,
) -> DevelopmentWorkSpecSafeProjection:
    result, error = _attempt_work_spec_safe_projection(work_spec)
    work_spec = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentWorkSpecSafeProjection, result)


def _attempt_program_head(
    row: object,
) -> tuple[DevelopmentProgramHeadRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentProgramHeadRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_PROGRAM_HEAD_COLUMNS,
            row=row,
        )
        validated = (
            _require_constant_string(mapping["schema_id"], _DEVELOPMENT_PROGRAM_HEAD_SCHEMA),
            _require_safe_ref(mapping["program_ref"]),
            _require_safe_ref(mapping["current_program_version_ref"]),
            _require_positive_integer(mapping["current_program_version_number"]),
            _require_nonnegative_integer(mapping["head_revision"]),
            _require_enum(mapping["program_state"], _PROGRAM_STATES),
            _require_utc_timestamp(mapping["updated_at"]),
        )
        identity = {
            "schema_id": validated[0],
            "program_ref": validated[1],
            "current_program_version_ref": validated[2],
            "current_program_version_number": validated[3],
            "head_revision": validated[4],
            "program_state": validated[5],
            "updated_at": validated[6],
        }
        digest = _require_matching_digest(
            domain=_DEVELOPMENT_PROGRAM_HEAD_DOMAIN,
            identity=identity,
            stored_digest=mapping["head_digest"],
        )
        result = DevelopmentProgramHeadRowValue._from_validated(validated + (digest,))
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_program_head_row_value_from_row_tuple(
    row: object,
) -> DevelopmentProgramHeadRowValue:
    result, error = _attempt_program_head(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentProgramHeadRowValue, result)


def _attempt_program_version(
    row: object,
) -> tuple[DevelopmentProgramVersionRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentProgramVersionRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_PROGRAM_VERSION_COLUMNS,
            row=row,
        )
        number = _require_positive_integer(mapping["program_version_number"])
        kind = _require_enum(mapping["program_version_kind"], _PROGRAM_VERSION_KINDS)
        if (kind == "initial") != (number == 1):
            raise _RowValueValidationError() from None
        validated = (
            _require_constant_string(mapping["schema_id"], _DEVELOPMENT_PROGRAM_VERSION_SCHEMA),
            _require_safe_ref(mapping["program_version_ref"]),
            _require_safe_ref(mapping["program_ref"]),
            number,
            kind,
            _require_safe_ref(mapping["creating_decision_ref"]),
            _require_safe_ref(mapping["accepted_intent_revision_ref"]),
            _require_utc_timestamp(mapping["created_at"]),
        )
        identity = {
            "schema_id": validated[0],
            "program_version_ref": validated[1],
            "program_ref": validated[2],
            "program_version_number": validated[3],
            "program_version_kind": validated[4],
            "creating_decision_ref": validated[5],
            "accepted_intent_revision_ref": validated[6],
            "created_at": validated[7],
        }
        digest = _require_matching_digest(
            domain=_DEVELOPMENT_PROGRAM_VERSION_DOMAIN,
            identity=identity,
            stored_digest=mapping["program_version_digest"],
        )
        result = DevelopmentProgramVersionRowValue._from_validated(validated + (digest,))
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_program_version_row_value_from_row_tuple(
    row: object,
) -> DevelopmentProgramVersionRowValue:
    result, error = _attempt_program_version(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentProgramVersionRowValue, result)


def _attempt_accepted_intent_revision(
    row: object,
) -> tuple[DevelopmentAcceptedIntentRevisionRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentAcceptedIntentRevisionRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_ACCEPTED_INTENT_REVISION_COLUMNS,
            row=row,
        )
        number = _require_positive_integer(mapping["accepted_intent_revision_number"])
        prior = _require_optional_safe_ref(mapping["prior_accepted_intent_revision_ref"])
        if (number == 1 and prior is not None) or (number >= 2 and prior is None):
            raise _RowValueValidationError() from None
        validated = (
            _require_constant_string(
                mapping["schema_id"],
                _DEVELOPMENT_ACCEPTED_INTENT_REVISION_SCHEMA,
            ),
            _require_safe_ref(mapping["accepted_intent_revision_ref"]),
            _require_safe_ref(mapping["program_ref"]),
            number,
            prior,
            _require_safe_ref(mapping["source_intent_ref"]),
            _require_sha256(mapping["source_intent_digest"]),
            _require_sha256(mapping["safe_projection_digest"]),
            _require_utc_timestamp(mapping["created_at"]),
        )
        identity = {
            "schema_id": validated[0],
            "accepted_intent_revision_ref": validated[1],
            "program_ref": validated[2],
            "accepted_intent_revision_number": validated[3],
            "prior_accepted_intent_revision_ref": validated[4],
            "source_intent_ref": validated[5],
            "source_intent_digest": validated[6],
            "safe_projection_digest": validated[7],
            "created_at": validated[8],
        }
        digest = _require_matching_digest(
            domain=_DEVELOPMENT_ACCEPTED_INTENT_REVISION_DOMAIN,
            identity=identity,
            stored_digest=mapping["accepted_intent_revision_digest"],
        )
        result = DevelopmentAcceptedIntentRevisionRowValue._from_validated(
            validated + (digest,)
        )
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_accepted_intent_revision_row_value_from_row_tuple(
    row: object,
) -> DevelopmentAcceptedIntentRevisionRowValue:
    result, error = _attempt_accepted_intent_revision(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentAcceptedIntentRevisionRowValue, result)


def _attempt_work_item_head(
    row: object,
) -> tuple[DevelopmentWorkItemHeadRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentWorkItemHeadRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_WORK_ITEM_HEAD_COLUMNS,
            row=row,
        )
        validated = (
            _require_constant_string(mapping["schema_id"], _DEVELOPMENT_WORK_ITEM_HEAD_SCHEMA),
            _require_safe_ref(mapping["work_item_ref"]),
            _require_safe_ref(mapping["program_ref"]),
            _require_safe_ref(mapping["current_work_item_revision_ref"]),
            _require_positive_integer(mapping["current_work_item_revision_number"]),
            _require_nonnegative_integer(mapping["head_revision"]),
            _require_enum(mapping["work_state"], _WORK_STATES),
            _require_utc_timestamp(mapping["updated_at"]),
        )
        identity = {
            "schema_id": validated[0],
            "work_item_ref": validated[1],
            "program_ref": validated[2],
            "current_work_item_revision_ref": validated[3],
            "current_work_item_revision_number": validated[4],
            "head_revision": validated[5],
            "work_state": validated[6],
            "updated_at": validated[7],
        }
        digest = _require_matching_digest(
            domain=_DEVELOPMENT_WORK_ITEM_HEAD_DOMAIN,
            identity=identity,
            stored_digest=mapping["head_digest"],
        )
        result = DevelopmentWorkItemHeadRowValue._from_validated(validated + (digest,))
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_work_item_head_row_value_from_row_tuple(
    row: object,
) -> DevelopmentWorkItemHeadRowValue:
    result, error = _attempt_work_item_head(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentWorkItemHeadRowValue, result)


def _attempt_work_item_revision(
    row: object,
) -> tuple[DevelopmentWorkItemRevisionRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentWorkItemRevisionRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_WORK_ITEM_REVISION_COLUMNS,
            row=row,
        )
        number = _require_positive_integer(mapping["work_item_revision_number"])
        kind = _require_enum(mapping["work_item_revision_kind"], _WORK_ITEM_REVISION_KINDS)
        prior = _require_optional_safe_ref(mapping["prior_work_item_revision_ref"])
        if not (
            (kind == "initial" and number == 1 and prior is None)
            or (kind == "replan" and number >= 2 and prior is not None)
        ):
            raise _RowValueValidationError() from None
        validated = (
            _require_constant_string(
                mapping["schema_id"],
                _DEVELOPMENT_WORK_ITEM_REVISION_SCHEMA,
            ),
            _require_safe_ref(mapping["work_item_revision_ref"]),
            _require_safe_ref(mapping["program_ref"]),
            _require_safe_ref(mapping["work_item_ref"]),
            number,
            kind,
            prior,
            _require_safe_ref(mapping["accepted_intent_revision_ref"]),
            _require_utc_timestamp(mapping["created_at"]),
        )
        identity = {
            "schema_id": validated[0],
            "work_item_revision_ref": validated[1],
            "program_ref": validated[2],
            "work_item_ref": validated[3],
            "work_item_revision_number": validated[4],
            "work_item_revision_kind": validated[5],
            "prior_work_item_revision_ref": validated[6],
            "accepted_intent_revision_ref": validated[7],
            "created_at": validated[8],
        }
        digest = _require_matching_digest(
            domain=_DEVELOPMENT_WORK_ITEM_REVISION_DOMAIN,
            identity=identity,
            stored_digest=mapping["work_item_revision_digest"],
        )
        result = DevelopmentWorkItemRevisionRowValue._from_validated(
            validated + (digest,)
        )
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_work_item_revision_row_value_from_row_tuple(
    row: object,
) -> DevelopmentWorkItemRevisionRowValue:
    result, error = _attempt_work_item_revision(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentWorkItemRevisionRowValue, result)


def _attempt_program_version_work_item(
    row: object,
) -> tuple[DevelopmentProgramVersionWorkItemRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentProgramVersionWorkItemRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_COLUMNS,
            row=row,
        )
        validated = (
            _require_constant_string(
                mapping["schema_id"],
                _DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_SCHEMA,
            ),
            _require_safe_ref(mapping["program_ref"]),
            _require_safe_ref(mapping["program_version_ref"]),
            _require_safe_ref(mapping["work_item_ref"]),
            _require_safe_ref(mapping["work_item_revision_ref"]),
            _require_nonnegative_integer(mapping["membership_ordinal"]),
            _require_utc_timestamp(mapping["created_at"]),
        )
        identity = {
            "schema_id": validated[0],
            "program_ref": validated[1],
            "program_version_ref": validated[2],
            "work_item_ref": validated[3],
            "work_item_revision_ref": validated[4],
            "membership_ordinal": validated[5],
            "created_at": validated[6],
        }
        digest = _require_matching_digest(
            domain=_DEVELOPMENT_PROGRAM_VERSION_WORK_ITEM_DOMAIN,
            identity=identity,
            stored_digest=mapping["membership_digest"],
        )
        result = DevelopmentProgramVersionWorkItemRowValue._from_validated(
            validated + (digest,)
        )
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_program_version_work_item_row_value_from_row_tuple(
    row: object,
) -> DevelopmentProgramVersionWorkItemRowValue:
    result, error = _attempt_program_version_work_item(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentProgramVersionWorkItemRowValue, result)


def _attempt_revision_edge(
    row: object,
) -> tuple[DevelopmentRevisionEdgeRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentRevisionEdgeRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_REVISION_EDGE_COLUMNS,
            row=row,
        )
        kind = _require_enum(mapping["revision_edge_kind"], _REVISION_EDGE_KINDS)
        from_intent = _require_optional_safe_ref(
            mapping["from_accepted_intent_revision_ref"]
        )
        to_intent = _require_optional_safe_ref(mapping["to_accepted_intent_revision_ref"])
        from_work = _require_optional_safe_ref(mapping["from_work_item_revision_ref"])
        to_work = _require_optional_safe_ref(mapping["to_work_item_revision_ref"])
        if kind == "accepted_intent_supersedes":
            if from_intent is None or to_intent is None or from_work is not None or to_work is not None:
                raise _RowValueValidationError() from None
        elif from_intent is not None or to_intent is not None or from_work is None or to_work is None:
            raise _RowValueValidationError() from None
        validated = (
            _require_constant_string(mapping["schema_id"], _DEVELOPMENT_REVISION_EDGE_SCHEMA),
            _require_safe_ref(mapping["revision_edge_ref"]),
            _require_sha256(mapping["relation_key_digest"]),
            _require_safe_ref(mapping["program_ref"]),
            kind,
            from_intent,
            to_intent,
            from_work,
            to_work,
            _require_utc_timestamp(mapping["created_at"]),
        )
        identity = {
            "schema_id": validated[0],
            "revision_edge_ref": validated[1],
            "relation_key_digest": validated[2],
            "program_ref": validated[3],
            "revision_edge_kind": validated[4],
            "from_accepted_intent_revision_ref": validated[5],
            "to_accepted_intent_revision_ref": validated[6],
            "from_work_item_revision_ref": validated[7],
            "to_work_item_revision_ref": validated[8],
            "created_at": validated[9],
        }
        digest = _require_matching_digest(
            domain=_DEVELOPMENT_REVISION_EDGE_DOMAIN,
            identity=identity,
            stored_digest=mapping["revision_edge_digest"],
        )
        result = DevelopmentRevisionEdgeRowValue._from_validated(validated + (digest,))
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_revision_edge_row_value_from_row_tuple(
    row: object,
) -> DevelopmentRevisionEdgeRowValue:
    result, error = _attempt_revision_edge(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentRevisionEdgeRowValue, result)


def _attempt_work_spec_binding(
    row: object,
) -> tuple[DevelopmentWorkSpecBindingRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    paths: tuple[str, ...] | None = None
    persisted_safe_projection_digest: str | None = None
    projection: DevelopmentWorkSpecSafeProjection | None = None
    result: DevelopmentWorkSpecBindingRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_WORK_SPEC_BINDING_COLUMNS,
            row=row,
        )
        persisted_safe_projection_digest = _require_sha256(
            mapping["safe_projection_digest"]
        )
        _require_constant_string(mapping["schema_id"], _DEVELOPMENT_WORK_SPEC_BINDING_SCHEMA)
        paths = _decode_fixed_paths_json(mapping["authorized_paths_json"])
        projection = _persisted_safe_projection_from_fields(
            work_spec_ref=mapping["work_spec_ref"],
            program_ref=mapping["program_ref"],
            program_version_ref=mapping["program_version_ref"],
            accepted_intent_revision_ref=mapping["accepted_intent_revision_ref"],
            work_item_ref=mapping["work_item_ref"],
            work_item_revision_ref=mapping["work_item_revision_ref"],
            repository_ref=mapping["repository_ref"],
            base_git_object_format=mapping["base_git_object_format"],
            base_git_oid=mapping["base_git_oid"],
            authorized_paths=paths,
            validation_requirement_ref=mapping["validation_requirement_ref"],
            review_requirement_ref=mapping["review_requirement_ref"],
            privacy_classification=mapping["privacy_classification"],
            work_spec_digest=mapping["work_spec_digest"],
            persisted_safe_projection_digest=persisted_safe_projection_digest,
        )
        recorded_at = _require_utc_timestamp(mapping["recorded_at"])
        identity = {
            "schema_id": _DEVELOPMENT_WORK_SPEC_BINDING_SCHEMA,
            "work_spec_ref": projection.work_spec_ref,
            "program_ref": projection.program_ref,
            "program_version_ref": projection.program_version_ref,
            "accepted_intent_revision_ref": projection.accepted_intent_revision_ref,
            "work_item_ref": projection.work_item_ref,
            "work_item_revision_ref": projection.work_item_revision_ref,
            "repository_ref": projection.repository_ref,
            "base_git_object_format": projection.base_git_object_format,
            "base_git_oid": projection.base_git_oid,
            "authorized_paths_json": _encode_fixed_paths(projection.authorized_paths),
            "validation_requirement_ref": projection.validation_requirement_ref,
            "review_requirement_ref": projection.review_requirement_ref,
            "privacy_classification": projection.privacy_classification,
            "work_spec_digest": projection.work_spec_digest,
            "safe_projection_digest": projection.safe_projection_digest,
            "recorded_at": recorded_at,
        }
        digest = _require_matching_digest(
            domain=_DEVELOPMENT_WORK_SPEC_BINDING_DOMAIN,
            identity=identity,
            stored_digest=mapping["work_spec_binding_digest"],
        )
        result = DevelopmentWorkSpecBindingRowValue._from_validated(
            (projection, recorded_at, digest)
        )
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        projection = None
        persisted_safe_projection_digest = None
        paths = None
        mapping = None
        row = None
    return result, error


def development_work_spec_binding_row_value_from_row_tuple(
    row: object,
) -> DevelopmentWorkSpecBindingRowValue:
    result, error = _attempt_work_spec_binding(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentWorkSpecBindingRowValue, result)


def _attempt_semantic_attempt(
    row: object,
) -> tuple[DevelopmentSemanticAttemptRowValue | None, BaseException | None]:
    mapping: dict[str, object] | None = None
    result: DevelopmentSemanticAttemptRowValue | None = None
    error: BaseException | None = None
    try:
        mapping = _row_tuple_to_private_mapping(
            columns=_DEVELOPMENT_SEMANTIC_ATTEMPT_COLUMNS,
            row=row,
        )
        validated = (
            _require_constant_string(mapping["schema_id"], _DEVELOPMENT_SEMANTIC_ATTEMPT_SCHEMA),
            _require_safe_ref(mapping["semantic_attempt_ref"]),
            _require_safe_ref(mapping["program_ref"]),
            _require_safe_ref(mapping["program_version_ref"]),
            _require_safe_ref(mapping["accepted_intent_revision_ref"]),
            _require_safe_ref(mapping["work_item_ref"]),
            _require_safe_ref(mapping["work_item_revision_ref"]),
            _require_positive_integer(mapping["attempt_number"]),
            _require_safe_ref(mapping["candidate_ref"]),
            _require_enum(mapping["attempt_phase"], _ATTEMPT_PHASES),
            _require_safe_ref(mapping["selection_decision_ref"]),
            _require_utc_timestamp(mapping["created_at"]),
        )
        identity = {
            "schema_id": validated[0],
            "semantic_attempt_ref": validated[1],
            "program_ref": validated[2],
            "program_version_ref": validated[3],
            "accepted_intent_revision_ref": validated[4],
            "work_item_ref": validated[5],
            "work_item_revision_ref": validated[6],
            "attempt_number": validated[7],
            "candidate_ref": validated[8],
            "attempt_phase": validated[9],
            "selection_decision_ref": validated[10],
            "created_at": validated[11],
        }
        digest = _require_matching_digest(
            domain=_DEVELOPMENT_SEMANTIC_ATTEMPT_DOMAIN,
            identity=identity,
            stored_digest=mapping["semantic_attempt_digest"],
        )
        result = DevelopmentSemanticAttemptRowValue._from_validated(validated + (digest,))
    except _RowValueValidationError:
        error = _new_database_integrity_error()
    finally:
        mapping = None
        row = None
    return result, error


def development_semantic_attempt_row_value_from_row_tuple(
    row: object,
) -> DevelopmentSemanticAttemptRowValue:
    result, error = _attempt_semantic_attempt(row)
    row = None
    if error is not None:
        raise error from None
    return typing.cast(DevelopmentSemanticAttemptRowValue, result)
