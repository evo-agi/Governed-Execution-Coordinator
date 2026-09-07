"""Private pure contracts for route-neutral development-program genesis.

This module owns only privacy-safe values and deterministic row planning.  It
does not import SQLite, acquire authority, perform I/O, select a route, or
retain a complete WorkSpec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
import typing

from . import _development_decision_row_values as _decision_rows
from . import _development_program_row_values as _program_rows
from ._development_row_value_support import (
    _RowValueValidationError,
    _domain_separated_digest,
    _require_constant_string,
    _require_nonnegative_integer,
    _require_safe_ref,
    _require_sha256,
    _require_utc_timestamp,
)
from .sqlite_errors import SQLiteMutationStoreError, SQLiteMutationStoreErrorCode


__all__: tuple[str, ...] = ()


_ACCEPTED_INTENT_SAFE_PROJECTION_SCHEMA = (
    "governed-execution.nwp-development-accepted-intent-safe-projection.v1"
)
_ACCEPTED_INTENT_SAFE_PROJECTION_DOMAIN = (
    _ACCEPTED_INTENT_SAFE_PROJECTION_SCHEMA + ".identity"
)
_INITIALIZATION_COMMAND_SCHEMA = (
    "governed-execution.nwp-initialize-development-program-command.v1"
)
_INITIALIZATION_COMMAND_DOMAIN = _INITIALIZATION_COMMAND_SCHEMA + ".identity"
_INITIALIZATION_RESULT_SCHEMA = (
    "governed-execution.nwp-initialize-development-program-result.v1"
)
_INITIALIZATION_RESULT_DOMAIN = _INITIALIZATION_RESULT_SCHEMA + ".identity"


class DevelopmentProgramInitializationConflictReasonV1(str, Enum):
    MUTATION_REF_REUSE_CONFLICT = "mutation_ref_reuse_conflict"
    GLOBAL_STOP_VERSION_CONFLICT = "global_stop_version_conflict"
    CODING_GLOBAL_STOP_ACTIVE = "coding_global_stop_active"
    SEMANTIC_IDENTITY_CONFLICT = "semantic_identity_conflict"


class DevelopmentProgramInitializationRecoveryDispositionV1(str, Enum):
    COMMITTED_EXACT = "committed_exact"
    DEFINITELY_NOT_COMMITTED = "definitely_not_committed"
    UNRESOLVED = "unresolved"


def _constant_repr(value: object) -> str:
    return f"<{type(value).__name__}>"


def _disable_pickle(self: object, protocol: object = None) -> typing.NoReturn:
    raise TypeError("pickling disabled")


def _safe_projection_mapping(
    value: _program_rows.DevelopmentWorkSpecSafeProjection,
) -> dict[str, object]:
    return {
        "schema_id": value.schema_id,
        "work_spec_ref": value.work_spec_ref,
        "program_ref": value.program_ref,
        "program_version_ref": value.program_version_ref,
        "accepted_intent_revision_ref": value.accepted_intent_revision_ref,
        "work_item_ref": value.work_item_ref,
        "work_item_revision_ref": value.work_item_revision_ref,
        "repository_ref": value.repository_ref,
        "base_git_object_format": value.base_git_object_format,
        "base_git_oid": value.base_git_oid,
        "authorized_paths": value.authorized_paths,
        "validation_requirement_ref": value.validation_requirement_ref,
        "review_requirement_ref": value.review_requirement_ref,
        "privacy_classification": value.privacy_classification,
        "work_spec_digest": value.work_spec_digest,
        "safe_projection_digest": value.safe_projection_digest,
    }


def _require_exact_work_spec_safe_projection(
    value: object,
) -> _program_rows.DevelopmentWorkSpecSafeProjection:
    try:
        if type(value) is not _program_rows.DevelopmentWorkSpecSafeProjection:
            raise _RowValueValidationError() from None
        raw = object.__getattribute__(value, "_values")
        if type(raw) is not tuple or len(raw) != 16:
            raise _RowValueValidationError() from None
        result = _program_rows._persisted_safe_projection_from_fields(
            work_spec_ref=raw[1],
            program_ref=raw[2],
            program_version_ref=raw[3],
            accepted_intent_revision_ref=raw[4],
            work_item_ref=raw[5],
            work_item_revision_ref=raw[6],
            repository_ref=raw[7],
            base_git_object_format=raw[8],
            base_git_oid=raw[9],
            authorized_paths=raw[10],
            validation_requirement_ref=raw[11],
            review_requirement_ref=raw[12],
            privacy_classification=raw[13],
            work_spec_digest=raw[14],
            persisted_safe_projection_digest=raw[15],
        )
    except _RowValueValidationError:
        raise _database_integrity_failure() from None
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        value = None
        raw = None
    return result


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentAcceptedIntentSafeProjectionV1:
    schema_id: str
    source_intent_ref: str
    source_intent_digest: str
    initial_work_spec_safe_projection: _program_rows.DevelopmentWorkSpecSafeProjection = field(
        repr=False
    )
    safe_projection_digest: str

    def __post_init__(self) -> None:
        try:
            schema_id = _require_constant_string(
                self.schema_id, _ACCEPTED_INTENT_SAFE_PROJECTION_SCHEMA
            )
            source_ref = _require_safe_ref(self.source_intent_ref)
            source_digest = _require_sha256(self.source_intent_digest)
            projection = _require_exact_work_spec_safe_projection(
                self.initial_work_spec_safe_projection
            )
            stored_digest = _require_sha256(self.safe_projection_digest)
            expected_digest = _domain_separated_digest(
                _ACCEPTED_INTENT_SAFE_PROJECTION_DOMAIN,
                {
                    "schema_id": schema_id,
                    "source_intent_ref": source_ref,
                    "source_intent_digest": source_digest,
                    "initial_work_spec_safe_projection": _safe_projection_mapping(
                        projection
                    ),
                },
            )
            if stored_digest != expected_digest:
                raise _RowValueValidationError() from None
        except _RowValueValidationError:
            raise _database_integrity_failure() from None
        object.__setattr__(self, "schema_id", schema_id)
        object.__setattr__(self, "source_intent_ref", source_ref)
        object.__setattr__(self, "source_intent_digest", source_digest)
        object.__setattr__(self, "initial_work_spec_safe_projection", projection)
        object.__setattr__(self, "safe_projection_digest", stored_digest)

    def identity_mapping(self) -> dict[str, object]:
        return {
            "schema_id": self.schema_id,
            "source_intent_ref": self.source_intent_ref,
            "source_intent_digest": self.source_intent_digest,
            "initial_work_spec_safe_projection": _safe_projection_mapping(
                self.initial_work_spec_safe_projection
            ),
        }

    def computed_digest(self) -> str:
        return _domain_separated_digest(
            _ACCEPTED_INTENT_SAFE_PROJECTION_DOMAIN, self.identity_mapping()
        )

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


def _accepted_intent_safe_projection(
    *,
    source_intent_ref: object,
    source_intent_digest: object,
    work_spec_safe_projection: object,
) -> DevelopmentAcceptedIntentSafeProjectionV1:
    try:
        source_ref = _require_safe_ref(source_intent_ref)
        source_digest = _require_sha256(source_intent_digest)
        projection = _require_exact_work_spec_safe_projection(work_spec_safe_projection)
        identity = {
            "schema_id": _ACCEPTED_INTENT_SAFE_PROJECTION_SCHEMA,
            "source_intent_ref": source_ref,
            "source_intent_digest": source_digest,
            "initial_work_spec_safe_projection": _safe_projection_mapping(projection),
        }
        digest = _domain_separated_digest(
            _ACCEPTED_INTENT_SAFE_PROJECTION_DOMAIN, identity
        )
        return DevelopmentAcceptedIntentSafeProjectionV1(
            schema_id=_ACCEPTED_INTENT_SAFE_PROJECTION_SCHEMA,
            source_intent_ref=source_ref,
            source_intent_digest=source_digest,
            initial_work_spec_safe_projection=projection,
            safe_projection_digest=digest,
        )
    except _RowValueValidationError:
        raise _database_integrity_failure() from None
    finally:
        source_intent_ref = None
        source_intent_digest = None
        work_spec_safe_projection = None


def _accepted_intent_mapping(
    value: DevelopmentAcceptedIntentSafeProjectionV1,
) -> dict[str, object]:
    return {
        **value.identity_mapping(),
        "safe_projection_digest": value.safe_projection_digest,
    }


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentProgramInitializationCommandV1:
    schema_id: str
    mutation_ref: str
    program_ref: str
    program_version_ref: str
    accepted_intent_revision_ref: str
    decision_ref: str
    preassigned_semantic_attempt_ref: str
    preassigned_candidate_ref: str
    coding_global_stop_ref: str
    coding_global_stop_version: int
    reason_code: str
    work_spec_safe_projection: _program_rows.DevelopmentWorkSpecSafeProjection = field(
        repr=False
    )
    accepted_intent_safe_projection: DevelopmentAcceptedIntentSafeProjectionV1 = field(
        repr=False
    )
    command_digest: str

    def __post_init__(self) -> None:
        try:
            schema_id = _require_constant_string(
                self.schema_id, _INITIALIZATION_COMMAND_SCHEMA
            )
            refs = tuple(
                _require_safe_ref(value)
                for value in (
                    self.mutation_ref,
                    self.program_ref,
                    self.program_version_ref,
                    self.accepted_intent_revision_ref,
                    self.decision_ref,
                    self.preassigned_semantic_attempt_ref,
                    self.preassigned_candidate_ref,
                    self.coding_global_stop_ref,
                )
            )
            stop_version = _require_nonnegative_integer(
                self.coding_global_stop_version
            )
            reason_code = _require_constant_string(self.reason_code, "program_genesis")
            work_projection = _require_exact_work_spec_safe_projection(
                self.work_spec_safe_projection
            )
            accepted_projection = _require_exact_accepted_intent_safe_projection(
                self.accepted_intent_safe_projection
            )
            stored_digest = _require_sha256(self.command_digest)
            if (
                work_projection.program_ref != refs[1]
                or work_projection.program_version_ref != refs[2]
                or work_projection.accepted_intent_revision_ref != refs[3]
                or accepted_projection.initial_work_spec_safe_projection
                != work_projection
            ):
                raise _RowValueValidationError() from None
            identity = _initialization_command_identity(
                schema_id=schema_id,
                refs=refs,
                coding_global_stop_version=stop_version,
                reason_code=reason_code,
                work_spec_safe_projection=work_projection,
                accepted_intent_safe_projection=accepted_projection,
            )
            if stored_digest != _domain_separated_digest(
                _INITIALIZATION_COMMAND_DOMAIN, identity
            ):
                raise _RowValueValidationError() from None
        except _RowValueValidationError:
            raise _database_integrity_failure() from None
        object.__setattr__(self, "schema_id", schema_id)
        for name, value in zip(
            (
                "mutation_ref",
                "program_ref",
                "program_version_ref",
                "accepted_intent_revision_ref",
                "decision_ref",
                "preassigned_semantic_attempt_ref",
                "preassigned_candidate_ref",
                "coding_global_stop_ref",
            ),
            refs,
            strict=True,
        ):
            object.__setattr__(self, name, value)
        object.__setattr__(self, "coding_global_stop_version", stop_version)
        object.__setattr__(self, "reason_code", reason_code)
        object.__setattr__(self, "work_spec_safe_projection", work_projection)
        object.__setattr__(
            self, "accepted_intent_safe_projection", accepted_projection
        )
        object.__setattr__(self, "command_digest", stored_digest)

    def identity_mapping(self) -> dict[str, object]:
        return _initialization_command_identity(
            schema_id=self.schema_id,
            refs=(
                self.mutation_ref,
                self.program_ref,
                self.program_version_ref,
                self.accepted_intent_revision_ref,
                self.decision_ref,
                self.preassigned_semantic_attempt_ref,
                self.preassigned_candidate_ref,
                self.coding_global_stop_ref,
            ),
            coding_global_stop_version=self.coding_global_stop_version,
            reason_code=self.reason_code,
            work_spec_safe_projection=self.work_spec_safe_projection,
            accepted_intent_safe_projection=self.accepted_intent_safe_projection,
        )

    def computed_digest(self) -> str:
        return _domain_separated_digest(
            _INITIALIZATION_COMMAND_DOMAIN, self.identity_mapping()
        )

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


def _initialization_command_identity(
    *,
    schema_id: str,
    refs: tuple[str, ...],
    coding_global_stop_version: int,
    reason_code: str,
    work_spec_safe_projection: _program_rows.DevelopmentWorkSpecSafeProjection,
    accepted_intent_safe_projection: DevelopmentAcceptedIntentSafeProjectionV1,
) -> dict[str, object]:
    return {
        "schema_id": schema_id,
        "mutation_ref": refs[0],
        "program_ref": refs[1],
        "program_version_ref": refs[2],
        "accepted_intent_revision_ref": refs[3],
        "decision_ref": refs[4],
        "preassigned_semantic_attempt_ref": refs[5],
        "preassigned_candidate_ref": refs[6],
        "coding_global_stop_ref": refs[7],
        "coding_global_stop_version": coding_global_stop_version,
        "reason_code": reason_code,
        "work_spec_safe_projection": _safe_projection_mapping(
            work_spec_safe_projection
        ),
        "accepted_intent_safe_projection": _accepted_intent_mapping(
            accepted_intent_safe_projection
        ),
    }


def _development_program_initialization_command(
    *,
    mutation_ref: object,
    program_ref: object,
    program_version_ref: object,
    accepted_intent_revision_ref: object,
    decision_ref: object,
    preassigned_semantic_attempt_ref: object,
    preassigned_candidate_ref: object,
    coding_global_stop_ref: object,
    coding_global_stop_version: object,
    reason_code: object,
    work_spec_safe_projection: object,
    accepted_intent_safe_projection: object,
) -> DevelopmentProgramInitializationCommandV1:
    try:
        refs = tuple(
            _require_safe_ref(value)
            for value in (
                mutation_ref,
                program_ref,
                program_version_ref,
                accepted_intent_revision_ref,
                decision_ref,
                preassigned_semantic_attempt_ref,
                preassigned_candidate_ref,
                coding_global_stop_ref,
            )
        )
        stop_version = _require_nonnegative_integer(coding_global_stop_version)
        reason = _require_constant_string(reason_code, "program_genesis")
        work_projection = _require_exact_work_spec_safe_projection(
            work_spec_safe_projection
        )
        accepted_projection = _require_exact_accepted_intent_safe_projection(
            accepted_intent_safe_projection
        )
        identity = _initialization_command_identity(
            schema_id=_INITIALIZATION_COMMAND_SCHEMA,
            refs=refs,
            coding_global_stop_version=stop_version,
            reason_code=reason,
            work_spec_safe_projection=work_projection,
            accepted_intent_safe_projection=accepted_projection,
        )
        digest = _domain_separated_digest(_INITIALIZATION_COMMAND_DOMAIN, identity)
        return DevelopmentProgramInitializationCommandV1(
            schema_id=_INITIALIZATION_COMMAND_SCHEMA,
            mutation_ref=refs[0],
            program_ref=refs[1],
            program_version_ref=refs[2],
            accepted_intent_revision_ref=refs[3],
            decision_ref=refs[4],
            preassigned_semantic_attempt_ref=refs[5],
            preassigned_candidate_ref=refs[6],
            coding_global_stop_ref=refs[7],
            coding_global_stop_version=stop_version,
            reason_code=reason,
            work_spec_safe_projection=work_projection,
            accepted_intent_safe_projection=accepted_projection,
            command_digest=digest,
        )
    except _RowValueValidationError:
        raise _database_integrity_failure() from None
    finally:
        mutation_ref = None
        program_ref = None
        program_version_ref = None
        accepted_intent_revision_ref = None
        decision_ref = None
        preassigned_semantic_attempt_ref = None
        preassigned_candidate_ref = None
        coding_global_stop_ref = None
        coding_global_stop_version = None
        reason_code = None
        work_spec_safe_projection = None
        accepted_intent_safe_projection = None


def _require_exact_accepted_intent_safe_projection(
    value: object,
) -> DevelopmentAcceptedIntentSafeProjectionV1:
    try:
        if type(value) is not DevelopmentAcceptedIntentSafeProjectionV1:
            raise _RowValueValidationError() from None
        return DevelopmentAcceptedIntentSafeProjectionV1(
            schema_id=object.__getattribute__(value, "schema_id"),
            source_intent_ref=object.__getattribute__(value, "source_intent_ref"),
            source_intent_digest=object.__getattribute__(
                value, "source_intent_digest"
            ),
            initial_work_spec_safe_projection=object.__getattribute__(
                value, "initial_work_spec_safe_projection"
            ),
            safe_projection_digest=object.__getattribute__(
                value, "safe_projection_digest"
            ),
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        value = None


def _require_exact_development_program_initialization_command(
    value: object,
) -> DevelopmentProgramInitializationCommandV1:
    try:
        if type(value) is not DevelopmentProgramInitializationCommandV1:
            raise _RowValueValidationError() from None
        return DevelopmentProgramInitializationCommandV1(
            schema_id=object.__getattribute__(value, "schema_id"),
            mutation_ref=object.__getattribute__(value, "mutation_ref"),
            program_ref=object.__getattribute__(value, "program_ref"),
            program_version_ref=object.__getattribute__(value, "program_version_ref"),
            accepted_intent_revision_ref=object.__getattribute__(
                value, "accepted_intent_revision_ref"
            ),
            decision_ref=object.__getattribute__(value, "decision_ref"),
            preassigned_semantic_attempt_ref=object.__getattribute__(
                value, "preassigned_semantic_attempt_ref"
            ),
            preassigned_candidate_ref=object.__getattribute__(
                value, "preassigned_candidate_ref"
            ),
            coding_global_stop_ref=object.__getattribute__(
                value, "coding_global_stop_ref"
            ),
            coding_global_stop_version=object.__getattribute__(
                value, "coding_global_stop_version"
            ),
            reason_code=object.__getattribute__(value, "reason_code"),
            work_spec_safe_projection=object.__getattribute__(
                value, "work_spec_safe_projection"
            ),
            accepted_intent_safe_projection=object.__getattribute__(
                value, "accepted_intent_safe_projection"
            ),
            command_digest=object.__getattribute__(value, "command_digest"),
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        value = None


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentProgramInitializationResultV1:
    disposition: str
    mutation_ref: str
    command_digest: str
    program_ref: str
    program_version_ref: str
    accepted_intent_revision_ref: str
    decision_ref: str
    work_item_ref: str
    work_item_revision_ref: str
    work_spec_ref: str
    preassigned_semantic_attempt_ref: str
    preassigned_candidate_ref: str
    transaction_timestamp: str

    def __post_init__(self) -> None:
        try:
            if type(self.disposition) is not str or self.disposition not in (
                "committed",
                "exact_replay",
            ):
                raise _RowValueValidationError() from None
            refs = tuple(
                _require_safe_ref(value)
                for value in (
                    self.mutation_ref,
                    self.program_ref,
                    self.program_version_ref,
                    self.accepted_intent_revision_ref,
                    self.decision_ref,
                    self.work_item_ref,
                    self.work_item_revision_ref,
                    self.work_spec_ref,
                    self.preassigned_semantic_attempt_ref,
                    self.preassigned_candidate_ref,
                )
            )
            digest = _require_sha256(self.command_digest)
            timestamp = _require_utc_timestamp(self.transaction_timestamp)
        except _RowValueValidationError:
            raise _database_integrity_failure() from None
        object.__setattr__(self, "command_digest", digest)
        object.__setattr__(self, "transaction_timestamp", timestamp)
        for name, value in zip(
            (
                "mutation_ref",
                "program_ref",
                "program_version_ref",
                "accepted_intent_revision_ref",
                "decision_ref",
                "work_item_ref",
                "work_item_revision_ref",
                "work_spec_ref",
                "preassigned_semantic_attempt_ref",
                "preassigned_candidate_ref",
            ),
            refs,
            strict=True,
        ):
            object.__setattr__(self, name, value)

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentProgramInitializationConflictV1:
    reason: DevelopmentProgramInitializationConflictReasonV1
    mutation_ref: str
    command_digest: str
    program_ref: str

    def __post_init__(self) -> None:
        try:
            if type(self.reason) is not DevelopmentProgramInitializationConflictReasonV1:
                raise _RowValueValidationError() from None
            mutation_ref = _require_safe_ref(self.mutation_ref)
            command_digest = _require_sha256(self.command_digest)
            program_ref = _require_safe_ref(self.program_ref)
        except _RowValueValidationError:
            raise _database_integrity_failure() from None
        object.__setattr__(self, "mutation_ref", mutation_ref)
        object.__setattr__(self, "command_digest", command_digest)
        object.__setattr__(self, "program_ref", program_ref)

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


@dataclass(frozen=True, slots=True, repr=False)
class DevelopmentProgramInitializationRecoveryResultV1:
    disposition: DevelopmentProgramInitializationRecoveryDispositionV1
    committed_result: DevelopmentProgramInitializationResultV1 | None = field(
        default=None, repr=False
    )

    def __post_init__(self) -> None:
        if type(self.disposition) is not DevelopmentProgramInitializationRecoveryDispositionV1:
            raise _database_integrity_failure() from None
        if self.disposition is DevelopmentProgramInitializationRecoveryDispositionV1.COMMITTED_EXACT:
            if (
                type(self.committed_result)
                is not DevelopmentProgramInitializationResultV1
                or self.committed_result.disposition != "exact_replay"
            ):
                raise _database_integrity_failure() from None
        elif self.committed_result is not None:
            raise _database_integrity_failure() from None

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle

    def __init_subclass__(cls, **kwargs: object) -> typing.NoReturn:
        raise TypeError("subclassing disabled")


@dataclass(frozen=True, slots=True, repr=False)
class _DevelopmentProgramInitializationWritePlan:
    program_head: _program_rows.DevelopmentProgramHeadRowValue
    accepted_intent_revision: _program_rows.DevelopmentAcceptedIntentRevisionRowValue
    work_item_head: _program_rows.DevelopmentWorkItemHeadRowValue
    work_item_revision: _program_rows.DevelopmentWorkItemRevisionRowValue
    initialize_decision: _decision_rows.DevelopmentDecisionRowValue
    program_version: _program_rows.DevelopmentProgramVersionRowValue
    program_version_work_item: _program_rows.DevelopmentProgramVersionWorkItemRowValue
    work_spec_binding: _program_rows.DevelopmentWorkSpecBindingRowValue
    mutation_receipt: _decision_rows.DevelopmentMutationReceiptRowValue
    graph_entries: tuple[_decision_rows.DevelopmentMutationGraphEntry, ...]
    planned_result: DevelopmentProgramInitializationResultV1

    __repr__ = _constant_repr
    __str__ = _constant_repr
    __reduce__ = _disable_pickle
    __reduce_ex__ = _disable_pickle


def _development_program_initialization_write_plan(
    command: object,
    transaction_timestamp: object,
) -> _DevelopmentProgramInitializationWritePlan:
    command = _require_exact_development_program_initialization_command(command)
    try:
        timestamp = _require_utc_timestamp(transaction_timestamp)
        work = command.work_spec_safe_projection
        accepted = command.accepted_intent_safe_projection

        program_head = _program_row(
            adapter=_program_rows.development_program_head_row_value_from_row_tuple,
            domain="governed-execution.nwp-development-program-head.v1.identity",
            digest_field="head_digest",
            fields={
                "schema_id": "governed-execution.nwp-development-program-head.v1",
                "program_ref": command.program_ref,
                "current_program_version_ref": command.program_version_ref,
                "current_program_version_number": 1,
                "head_revision": 0,
                "program_state": "active",
                "updated_at": timestamp,
            },
        )
        accepted_intent_revision = _program_row(
            adapter=_program_rows.development_accepted_intent_revision_row_value_from_row_tuple,
            domain="governed-execution.nwp-development-accepted-intent-revision.v1.identity",
            digest_field="accepted_intent_revision_digest",
            fields={
                "schema_id": "governed-execution.nwp-development-accepted-intent-revision.v1",
                "accepted_intent_revision_ref": command.accepted_intent_revision_ref,
                "program_ref": command.program_ref,
                "accepted_intent_revision_number": 1,
                "prior_accepted_intent_revision_ref": None,
                "source_intent_ref": accepted.source_intent_ref,
                "source_intent_digest": accepted.source_intent_digest,
                "safe_projection_digest": accepted.safe_projection_digest,
                "created_at": timestamp,
            },
        )
        work_item_head = _program_row(
            adapter=_program_rows.development_work_item_head_row_value_from_row_tuple,
            domain="governed-execution.nwp-development-work-item-head.v1.identity",
            digest_field="head_digest",
            fields={
                "schema_id": "governed-execution.nwp-development-work-item-head.v1",
                "work_item_ref": work.work_item_ref,
                "program_ref": command.program_ref,
                "current_work_item_revision_ref": work.work_item_revision_ref,
                "current_work_item_revision_number": 1,
                "head_revision": 0,
                "work_state": "planned",
                "updated_at": timestamp,
            },
        )
        work_item_revision = _program_row(
            adapter=_program_rows.development_work_item_revision_row_value_from_row_tuple,
            domain="governed-execution.nwp-development-work-item-revision.v1.identity",
            digest_field="work_item_revision_digest",
            fields={
                "schema_id": "governed-execution.nwp-development-work-item-revision.v1",
                "work_item_revision_ref": work.work_item_revision_ref,
                "program_ref": command.program_ref,
                "work_item_ref": work.work_item_ref,
                "work_item_revision_number": 1,
                "work_item_revision_kind": "initial",
                "prior_work_item_revision_ref": None,
                "accepted_intent_revision_ref": command.accepted_intent_revision_ref,
                "created_at": timestamp,
            },
        )
        initialize_decision = _decision_row(command, timestamp)
        program_version = _program_row(
            adapter=_program_rows.development_program_version_row_value_from_row_tuple,
            domain="governed-execution.nwp-development-program-version.v1.identity",
            digest_field="program_version_digest",
            fields={
                "schema_id": "governed-execution.nwp-development-program-version.v1",
                "program_version_ref": command.program_version_ref,
                "program_ref": command.program_ref,
                "program_version_number": 1,
                "program_version_kind": "initial",
                "creating_decision_ref": command.decision_ref,
                "accepted_intent_revision_ref": command.accepted_intent_revision_ref,
                "created_at": timestamp,
            },
        )
        membership = _program_row(
            adapter=_program_rows.development_program_version_work_item_row_value_from_row_tuple,
            domain="governed-execution.nwp-development-program-version-work-item.v1.identity",
            digest_field="membership_digest",
            fields={
                "schema_id": "governed-execution.nwp-development-program-version-work-item.v1",
                "program_ref": command.program_ref,
                "program_version_ref": command.program_version_ref,
                "work_item_ref": work.work_item_ref,
                "work_item_revision_ref": work.work_item_revision_ref,
                "membership_ordinal": 0,
                "created_at": timestamp,
            },
        )
        binding = _work_spec_binding_row(work, timestamp)
        result_projection_digest = _domain_separated_digest(
            _INITIALIZATION_RESULT_DOMAIN,
            {
                "schema_id": _INITIALIZATION_RESULT_SCHEMA,
                "program_ref": command.program_ref,
                "decision_ref": command.decision_ref,
                "result_program_version_ref": command.program_version_ref,
                "result_decision_ref": command.decision_ref,
            },
        )
        provisional_receipt = _receipt_row(
            command,
            timestamp,
            result_projection_digest=result_projection_digest,
            mutation_graph_digest="0" * 64,
        )
        graph_entries = (
            _decision_rows.development_mutation_graph_entry(
                role="program_head_postimage", ordinal=0,
                record_ref=command.program_ref, record_digest=program_head.head_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="accepted_intent_revision", ordinal=0,
                record_ref=command.accepted_intent_revision_ref,
                record_digest=accepted_intent_revision.accepted_intent_revision_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="initialize_decision", ordinal=0,
                record_ref=command.decision_ref,
                record_digest=initialize_decision.decision_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="program_version", ordinal=0,
                record_ref=command.program_version_ref,
                record_digest=program_version.program_version_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="work_item_head_postimage", ordinal=0,
                record_ref=work.work_item_ref, record_digest=work_item_head.head_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="work_item_revision", ordinal=0,
                record_ref=work.work_item_revision_ref,
                record_digest=work_item_revision.work_item_revision_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="program_version_work_item", ordinal=0,
                record_ref=work.work_item_ref, record_digest=membership.membership_digest,
            ),
            _decision_rows.development_mutation_graph_entry(
                role="work_spec_binding", ordinal=0,
                record_ref=work.work_spec_ref,
                record_digest=binding.work_spec_binding_digest,
            ),
        )
        graph_digest = _decision_rows.compute_development_mutation_graph_digest(
            receipt=provisional_receipt, graph_entries=graph_entries
        )
        receipt = _receipt_row(
            command,
            timestamp,
            result_projection_digest=result_projection_digest,
            mutation_graph_digest=graph_digest,
        )
        _decision_rows.require_development_mutation_graph_digest_matches_supplied_entries(
            receipt=receipt, graph_entries=graph_entries
        )
        result = _initialization_result(command, timestamp, "committed")
        return _DevelopmentProgramInitializationWritePlan(
            program_head=program_head,
            accepted_intent_revision=accepted_intent_revision,
            work_item_head=work_item_head,
            work_item_revision=work_item_revision,
            initialize_decision=initialize_decision,
            program_version=program_version,
            program_version_work_item=membership,
            work_spec_binding=binding,
            mutation_receipt=receipt,
            graph_entries=graph_entries,
            planned_result=result,
        )
    except SQLiteMutationStoreError:
        raise
    except Exception:
        raise _database_integrity_failure() from None
    finally:
        command = None
        transaction_timestamp = None


def _program_row(
    *, adapter: typing.Callable[[object], object], domain: str,
    digest_field: str, fields: dict[str, object],
) -> typing.Any:
    identity = dict(fields)
    fields[digest_field] = _domain_separated_digest(domain, identity)
    return adapter(tuple(fields.values()))


def _decision_row(
    command: DevelopmentProgramInitializationCommandV1,
    timestamp: str,
) -> _decision_rows.DevelopmentDecisionRowValue:
    values: dict[str, object] = {
        "schema_id": "governed-execution.nwp-development-decision.v1",
        "mutation_ref": command.mutation_ref,
        "decision_ref": command.decision_ref,
        "program_ref": command.program_ref,
        "decision_kind": "initialize",
        "decision_variant": "program_genesis",
        "basis_decision_ref": None,
        "basis_program_version_ref": None,
        "basis_program_version_number": None,
        "expected_program_head_revision": 0,
        "resulting_program_version_ref": command.program_version_ref,
        "resulting_program_version_number": 1,
        "selected_semantic_attempt_ref": None,
        "selected_candidate_ref": None,
        "selected_attempt_fence_ref": None,
        "selected_attempt_fence_digest": None,
        "target_effect_intent_ref": None,
        "target_effect_class": None,
        "target_effect_fence_ref": None,
        "target_effect_fence_digest": None,
        "expected_target_effect_head_revision": None,
        "target_delivery_attempt_ref": None,
        "originating_command_ref": None,
        "originating_command_digest": None,
        "target_capsule_manifest_ref": None,
        "target_portable_capsule_digest": None,
        "coding_global_stop_ref": command.coding_global_stop_ref,
        "coding_global_stop_version": command.coding_global_stop_version,
        "source_directive_ref": None,
        "source_directive_digest": None,
        "source_evidence_ref": None,
        "source_evidence_digest": None,
        "preassigned_semantic_attempt_ref": command.preassigned_semantic_attempt_ref,
        "preassigned_candidate_ref": command.preassigned_candidate_ref,
        "preassigned_effect_intent_ref": None,
        "preassigned_effect_fence_ref": None,
        "preassigned_delivery_attempt_ref": None,
        "resulting_accepted_intent_revision_ref": None,
        "resulting_work_item_ref": None,
        "resulting_work_item_revision_ref": None,
        "reason_code": "program_genesis",
        "decided_at": timestamp,
    }
    values["decision_digest"] = _domain_separated_digest(
        "governed-execution.nwp-development-decision.v1.identity", dict(values)
    )
    return _decision_rows.development_decision_row_value_from_row_tuple(
        tuple(values.values())
    )


def _work_spec_binding_row(
    work: _program_rows.DevelopmentWorkSpecSafeProjection,
    timestamp: str,
) -> _program_rows.DevelopmentWorkSpecBindingRowValue:
    values: dict[str, object] = {
        "schema_id": "governed-execution.nwp-development-work-spec-binding.v1",
        "work_spec_ref": work.work_spec_ref,
        "program_ref": work.program_ref,
        "program_version_ref": work.program_version_ref,
        "accepted_intent_revision_ref": work.accepted_intent_revision_ref,
        "work_item_ref": work.work_item_ref,
        "work_item_revision_ref": work.work_item_revision_ref,
        "repository_ref": work.repository_ref,
        "base_git_object_format": work.base_git_object_format,
        "base_git_oid": work.base_git_oid,
        "authorized_paths_json": json.dumps(
            list(work.authorized_paths), ensure_ascii=False, separators=(",", ":")
        ),
        "validation_requirement_ref": work.validation_requirement_ref,
        "review_requirement_ref": work.review_requirement_ref,
        "privacy_classification": work.privacy_classification,
        "work_spec_digest": work.work_spec_digest,
        "safe_projection_digest": work.safe_projection_digest,
        "recorded_at": timestamp,
    }
    values["work_spec_binding_digest"] = _domain_separated_digest(
        "governed-execution.nwp-development-work-spec-binding.v1.identity",
        dict(values),
    )
    return _program_rows.development_work_spec_binding_row_value_from_row_tuple(
        tuple(values.values())
    )


def _receipt_row(
    command: DevelopmentProgramInitializationCommandV1,
    timestamp: str,
    *,
    result_projection_digest: str,
    mutation_graph_digest: str,
) -> _decision_rows.DevelopmentMutationReceiptRowValue:
    return _decision_rows.development_mutation_receipt_row_value_from_row_tuple(
        (
            "governed-execution.nwp-development-mutation-receipt.v1",
            command.mutation_ref,
            "initialize_development_program",
            command.schema_id,
            command.command_digest,
            command.program_ref,
            command.decision_ref,
            command.program_version_ref,
            None,
            None,
            None,
            None,
            None,
            command.decision_ref,
            "development_program_initialized",
            result_projection_digest,
            mutation_graph_digest,
            "committed",
            timestamp,
        )
    )


def _initialization_result(
    command: DevelopmentProgramInitializationCommandV1,
    timestamp: str,
    disposition: str,
) -> DevelopmentProgramInitializationResultV1:
    work = command.work_spec_safe_projection
    return DevelopmentProgramInitializationResultV1(
        disposition=disposition,
        mutation_ref=command.mutation_ref,
        command_digest=command.command_digest,
        program_ref=command.program_ref,
        program_version_ref=command.program_version_ref,
        accepted_intent_revision_ref=command.accepted_intent_revision_ref,
        decision_ref=command.decision_ref,
        work_item_ref=work.work_item_ref,
        work_item_revision_ref=work.work_item_revision_ref,
        work_spec_ref=work.work_spec_ref,
        preassigned_semantic_attempt_ref=command.preassigned_semantic_attempt_ref,
        preassigned_candidate_ref=command.preassigned_candidate_ref,
        transaction_timestamp=timestamp,
    )


def _initialization_conflict(
    command: DevelopmentProgramInitializationCommandV1,
    reason: DevelopmentProgramInitializationConflictReasonV1,
) -> DevelopmentProgramInitializationConflictV1:
    return DevelopmentProgramInitializationConflictV1(
        reason=reason,
        mutation_ref=command.mutation_ref,
        command_digest=command.command_digest,
        program_ref=command.program_ref,
    )


def _database_integrity_failure() -> SQLiteMutationStoreError:
    return SQLiteMutationStoreError(
        SQLiteMutationStoreErrorCode.DATABASE_INTEGRITY_FAILURE
    )
